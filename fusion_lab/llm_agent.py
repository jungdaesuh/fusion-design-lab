from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Final, Sequence

from fusion_lab.models import (
    DirectionName,
    MagnitudeName,
    ParameterName,
    StellaratorAction,
    StellaratorObservation,
)
from server.environment import BUDGET, StellaratorEnvironment

RUN_PARAMETERS: Final[tuple[ParameterName, ...]] = (
    "aspect_ratio",
    "elongation",
    "rotational_transform",
    "triangularity_scale",
)
RUN_DIRECTIONS: Final[tuple[DirectionName, ...]] = ("increase", "decrease")
RUN_MAGNITUDES: Final[tuple[MagnitudeName, ...]] = ("small", "medium", "large")

SYSTEM_PROMPT: Final[str] = """You are an expert stellarator designer.

Goal:
- satisfy the P1 physics constraints
- then improve the design score by lowering max elongation

You control a 4-knob low-dimensional design:
- aspect_ratio
- elongation
- rotational_transform
- triangularity_scale

Action rules:
- output a JSON array
- each item must be either:
  - {"intent":"run","parameter":"<parameter>","direction":"increase|decrease","magnitude":"small|medium|large"}
  - {"intent":"restore_best"}
  - {"intent":"submit"}
- keep the plan short and within the remaining budget
- use "submit" only when the design looks ready

Constraint directions:
- aspect_ratio <= 4.0
- average_triangularity <= -0.5
- edge_iota_over_nfp >= 0.3"""

ACTION_ARRAY_PATTERN: Final[re.Pattern[str]] = re.compile(r"\[[\s\S]*\]")


@dataclass(frozen=True)
class LLMStepTrace:
    step: int
    action_label: str
    reward: float
    p1_score: float
    p1_feasibility: float
    constraints_satisfied: bool
    evaluation_fidelity: str
    evaluation_failed: bool
    budget_remaining: int
    diagnostics_text: str


@dataclass(frozen=True)
class LLMEpisodeTrace:
    seed: int
    total_reward: float
    final_score: float
    final_feasibility: float
    constraints_satisfied: bool
    evaluation_failed: bool
    steps: list[LLMStepTrace]

    def asdict(self) -> dict[str, object]:
        return asdict(self)


def action_label(action: StellaratorAction) -> str:
    if action.intent != "run":
        return action.intent
    return f"{action.intent} {action.parameter} {action.direction} {action.magnitude}"


def format_observation(observation: StellaratorObservation) -> str:
    return (
        "Current stellarator state:\n"
        f"- max_elongation: {observation.max_elongation:.4f}\n"
        f"- aspect_ratio: {observation.aspect_ratio:.4f} (must stay <= 4.0)\n"
        f"- average_triangularity: {observation.average_triangularity:.6f} "
        "(must stay <= -0.5)\n"
        f"- edge_iota_over_nfp: {observation.edge_iota_over_nfp:.4f} "
        "(must stay >= 0.3)\n"
        f"- p1_score: {observation.p1_score:.4f}\n"
        f"- p1_feasibility: {observation.p1_feasibility:.6f}\n"
        f"- constraints_satisfied: {observation.constraints_satisfied}\n"
        f"- evaluation_fidelity: {observation.evaluation_fidelity}\n"
        f"- evaluation_failed: {observation.evaluation_failed}\n"
        f"- budget_remaining: {observation.budget_remaining}\n"
        f"- best_low_fidelity_score: {observation.best_low_fidelity_score:.4f}\n"
        f"- best_low_fidelity_feasibility: {observation.best_low_fidelity_feasibility:.6f}\n"
        f"- diagnostics: {observation.diagnostics_text}\n"
    )


def build_prompt(observation: StellaratorObservation) -> str:
    return (
        f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n"
        f"<|im_start|>user\n{format_observation(observation)}<|im_end|>\n"
        "<|im_start|>assistant\n"
    )


def extract_json_plan(text: str) -> str | None:
    match = ACTION_ARRAY_PATTERN.search(text)
    if match is None:
        return None
    return match.group()


def _parse_action_item(item: object) -> StellaratorAction | None:
    if not isinstance(item, dict):
        return None

    intent = item.get("intent")
    if intent == "submit":
        return StellaratorAction(intent="submit")
    if intent == "restore_best":
        return StellaratorAction(intent="restore_best")
    if intent != "run":
        return None

    parameter = item.get("parameter")
    direction = item.get("direction")
    magnitude = item.get("magnitude", "small")
    if parameter not in RUN_PARAMETERS:
        return None
    if direction not in RUN_DIRECTIONS:
        return None
    if magnitude not in RUN_MAGNITUDES:
        return None

    return StellaratorAction(
        intent="run",
        parameter=parameter,
        direction=direction,
        magnitude=magnitude,
    )


def parse_action_plan(text: str) -> list[StellaratorAction]:
    raw_plan = extract_json_plan(text)
    if raw_plan is None:
        return []
    try:
        decoded = json.loads(raw_plan)
    except json.JSONDecodeError:
        return []
    if not isinstance(decoded, list):
        return []

    parsed: list[StellaratorAction] = []
    for item in decoded:
        action = _parse_action_item(item)
        if action is None:
            continue
        parsed.append(action)
        if action.intent == "submit":
            break
    return parsed


def run_episode_with_actions(
    actions: Sequence[StellaratorAction],
    *,
    seed_idx: int,
) -> LLMEpisodeTrace:
    environment = StellaratorEnvironment()
    observation = environment.reset(seed=seed_idx)
    step_traces: list[LLMStepTrace] = []
    total_reward = 0.0

    for step_index, action in enumerate(actions[:BUDGET], start=1):
        observation = environment.step(action)
        reward = float(observation.reward or 0.0)
        total_reward += reward
        step_traces.append(
            LLMStepTrace(
                step=step_index,
                action_label=action_label(action),
                reward=reward,
                p1_score=observation.p1_score,
                p1_feasibility=observation.p1_feasibility,
                constraints_satisfied=observation.constraints_satisfied,
                evaluation_fidelity=observation.evaluation_fidelity,
                evaluation_failed=observation.evaluation_failed,
                budget_remaining=observation.budget_remaining,
                diagnostics_text=observation.diagnostics_text,
            )
        )
        if observation.done:
            break

    return LLMEpisodeTrace(
        seed=seed_idx,
        total_reward=round(total_reward, 4),
        final_score=observation.p1_score,
        final_feasibility=observation.p1_feasibility,
        constraints_satisfied=observation.constraints_satisfied,
        evaluation_failed=observation.evaluation_failed,
        steps=step_traces,
    )
