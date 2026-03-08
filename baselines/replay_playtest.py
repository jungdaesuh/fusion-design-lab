"""Fixed-action replay playtest for reward branch coverage.

Runs 5 scripted episodes against StellaratorEnvironment directly.
Each episode targets specific untested reward branches.

Episodes:
  1. Seed 0 — repair + feasible-side objective shaping + budget exhaustion
  2. Seed 1 — repair from different seed (ar=3.4, rt=1.6)
  3. Seed 2 — boundary clamping (ar=3.8 = upper bound)
  4. Seed 0 — push rt into crash zone + restore_best
  5. Seed 0 — repair + objective move + explicit submit
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from typing import Sequence

from fusion_lab.models import StellaratorAction, StellaratorObservation
from server.environment import StellaratorEnvironment


@dataclass(frozen=True)
class StepRecord:
    step: int
    intent: str
    action_label: str
    score: float
    feasibility: float
    constraints_satisfied: bool
    evaluation_fidelity: str
    evaluation_failed: bool
    max_elongation: float
    reward: float
    budget_remaining: int
    done: bool


def _action_label(action: StellaratorAction) -> str:
    if action.intent != "run":
        return action.intent
    return f"{action.parameter} {action.direction} {action.magnitude}"


def _record(obs: StellaratorObservation, step: int, action: StellaratorAction) -> StepRecord:
    return StepRecord(
        step=step,
        intent=action.intent,
        action_label=_action_label(action),
        score=obs.p1_score,
        feasibility=obs.p1_feasibility,
        constraints_satisfied=obs.constraints_satisfied,
        evaluation_fidelity=obs.evaluation_fidelity,
        evaluation_failed=obs.evaluation_failed,
        max_elongation=obs.max_elongation,
        reward=obs.reward or 0.0,
        budget_remaining=obs.budget_remaining,
        done=obs.done,
    )


def _run_episode(
    env: StellaratorEnvironment,
    seed: int,
    actions: Sequence[StellaratorAction],
    label: str,
) -> list[StepRecord]:
    obs = env.reset(seed=seed)
    print(f"\n{'=' * 72}")
    print(f"Episode: {label}")
    print(f"Seed: {seed}")
    print(
        f"  reset  score={obs.p1_score:.6f}  feasibility={obs.p1_feasibility:.6f}  "
        f"constraints={'yes' if obs.constraints_satisfied else 'no'}  "
        f"elongation={obs.max_elongation:.4f}  budget={obs.budget_remaining}"
    )

    records: list[StepRecord] = []
    for i, action in enumerate(actions, start=1):
        if obs.done:
            print(f"  (episode ended before step {i})")
            break
        obs = env.step(action)
        rec = _record(obs, i, action)
        records.append(rec)

        status = (
            "FAIL" if rec.evaluation_failed else ("OK" if rec.constraints_satisfied else "viol")
        )
        print(
            f"  step {i:2d}  {rec.action_label:<42s}  "
            f"reward={rec.reward:+8.4f}  score={rec.score:.6f}  "
            f"feas={rec.feasibility:.6f}  elong={rec.max_elongation:.4f}  "
            f"status={status}  budget={rec.budget_remaining}  "
            f"{'DONE' if rec.done else ''}"
        )

    total_reward = sum(r.reward for r in records)
    print(f"  total_reward={total_reward:+.4f}")
    return records


def _run(action: str, param: str, direction: str, magnitude: str) -> StellaratorAction:
    return StellaratorAction(
        intent="run",
        parameter=param,
        direction=direction,
        magnitude=magnitude,
    )


def _submit() -> StellaratorAction:
    return StellaratorAction(intent="submit")


def _restore() -> StellaratorAction:
    return StellaratorAction(intent="restore_best")


# ── Episode definitions ──────────────────────────────────────────────────

EPISODE_1 = (
    "seed0_repair_objective_exhaustion",
    0,
    [
        _run("run", "triangularity_scale", "increase", "medium"),  # cross feasibility
        _run("run", "elongation", "decrease", "small"),  # feasible-side shaping
        _run("run", "elongation", "decrease", "small"),  # more shaping
        _run("run", "elongation", "decrease", "small"),  # more shaping
        _run("run", "elongation", "decrease", "small"),  # more shaping
        _run("run", "elongation", "decrease", "small"),  # budget=0 → done bonus
    ],
)

EPISODE_2 = (
    "seed1_repair_different_seed",
    1,
    [
        _run(
            "run", "triangularity_scale", "increase", "medium"
        ),  # cross feasibility from ar=3.4,rt=1.6
        _run("run", "elongation", "decrease", "small"),  # feasible-side shaping
        _run("run", "elongation", "decrease", "small"),  # more shaping
        _run("run", "triangularity_scale", "increase", "small"),  # push tri further
        _run("run", "elongation", "decrease", "small"),  # more shaping
        _run("run", "elongation", "decrease", "small"),  # budget exhaustion
    ],
)

EPISODE_3 = (
    "seed2_boundary_clamping",
    2,
    [
        _run("run", "aspect_ratio", "increase", "large"),  # ar=3.8 + 0.2 → clamped at 3.8
        _run("run", "triangularity_scale", "increase", "medium"),  # repair toward feasibility
        _run("run", "triangularity_scale", "increase", "medium"),  # push further
        _run("run", "elongation", "decrease", "small"),  # shaping if feasible
        _run("run", "aspect_ratio", "decrease", "large"),  # move ar down
        _run("run", "elongation", "decrease", "small"),  # budget exhaustion
    ],
)

EPISODE_4 = (
    "seed0_crash_recovery_restore",
    0,
    [
        _run("run", "triangularity_scale", "increase", "medium"),  # cross feasibility first
        _run("run", "rotational_transform", "increase", "large"),  # rt 1.5→1.7
        _run("run", "rotational_transform", "increase", "large"),  # rt 1.7→1.9 (crash zone)
        _restore(),  # recover best state
        _run("run", "elongation", "decrease", "small"),  # continue from best
        _run("run", "elongation", "decrease", "small"),  # budget exhaustion
    ],
)

EPISODE_5 = (
    "seed0_repair_objective_submit",
    0,
    [
        _run("run", "triangularity_scale", "increase", "medium"),  # cross feasibility
        _run("run", "elongation", "decrease", "small"),  # feasible-side objective
        _submit(),  # explicit high-fidelity submit
    ],
)

ALL_EPISODES = [EPISODE_1, EPISODE_2, EPISODE_3, EPISODE_4, EPISODE_5]


def main(output_json: str | None = None) -> None:
    env = StellaratorEnvironment()
    all_results: dict[str, list[dict[str, object]]] = {}

    for label, seed, actions in ALL_EPISODES:
        records = _run_episode(env, seed, actions, label)
        all_results[label] = [asdict(r) for r in records]

    if output_json:
        with open(output_json, "w") as f:
            json.dump(all_results, f, indent=2)
        print(f"\nResults written to {output_json}")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else None
    main(output_json=out)
