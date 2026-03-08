from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

import gymnasium as gym
import numpy as np
from gymnasium import spaces
from stable_baselines3 import PPO

from fusion_lab.models import StellaratorAction, StellaratorObservation
from server.contract import RESET_SEEDS
from server.environment import BUDGET, StellaratorEnvironment

DEFAULT_OUTPUT_DIR: Final[Path] = Path("training/artifacts/ppo_smoke")
DEFAULT_TOTAL_TIMESTEPS: Final[int] = 32
DEFAULT_EVAL_EPISODES: Final[int] = 3
ENCODED_OBSERVATION_DIM: Final[int] = 17

DIAGNOSTIC_RUN_ACTION_SPECS: Final[tuple[tuple[str, str, str], ...]] = (
    ("rotational_transform", "increase", "medium"),
    ("triangularity_scale", "increase", "medium"),
)
TRAIN_RESET_SEED_INDICES: Final[tuple[int, ...]] = (2,)
LOW_FI_ACTION_COUNT: Final[int] = len(DIAGNOSTIC_RUN_ACTION_SPECS)


@dataclass(frozen=True)
class TraceStep:
    step: int
    action_index: int
    action_label: str
    reward: float
    score: float
    feasibility: float
    constraints_satisfied: bool
    evaluation_failed: bool
    budget_remaining: int
    termination_reason: str
    max_elongation: float
    average_triangularity: float
    edge_iota_over_nfp: float


@dataclass(frozen=True)
class EpisodeTrace:
    episode: int
    seed: int
    total_reward: float
    final_score: float
    final_feasibility: float
    constraints_satisfied: bool
    evaluation_failed: bool
    termination_reason: str
    steps: list[TraceStep]


def diagnostic_action(action_index: int) -> StellaratorAction:
    parameter, direction, magnitude = DIAGNOSTIC_RUN_ACTION_SPECS[action_index]
    return StellaratorAction(
        intent="run",
        parameter=parameter,
        direction=direction,
        magnitude=magnitude,
    )


def diagnostic_action_label(action_index: int) -> str:
    action = diagnostic_action(action_index)
    return f"{action.parameter} {action.direction} {action.magnitude}"


class LowFiSmokeEnv(gym.Env[np.ndarray, int]):
    metadata = {"render_modes": []}

    def __init__(self) -> None:
        super().__init__()
        self._env = StellaratorEnvironment()
        self._seed = 0
        self._episode_index = 0
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            # Keep this aligned with _encode_observation feature count.
            shape=(ENCODED_OBSERVATION_DIM,),
            dtype=np.float32,
        )
        self.action_space = spaces.Discrete(LOW_FI_ACTION_COUNT)

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, object] | None = None,
    ) -> tuple[np.ndarray, dict[str, object]]:
        super().reset(seed=seed)
        self._seed = self._next_seed(seed)
        obs = self._env.reset(seed=self._seed)
        return self._encode_observation(obs), self._info(obs)

    def _next_seed(self, seed: int | None) -> int:
        if seed is not None:
            self._episode_index = 0
            return seed % len(RESET_SEEDS)
        if not TRAIN_RESET_SEED_INDICES:
            raise ValueError("TRAIN_RESET_SEED_INDICES must define at least one seed index.")
        next_seed = TRAIN_RESET_SEED_INDICES[self._episode_index % len(TRAIN_RESET_SEED_INDICES)]
        self._episode_index += 1
        return next_seed

    def step(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, object]]:
        obs = self._env.step(self._decode_action(action))
        return (
            self._encode_observation(obs),
            float(obs.reward if obs.reward is not None else 0.0),
            bool(obs.done),
            False,
            self._info(obs),
        )

    def _decode_action(self, action: int) -> StellaratorAction:
        return diagnostic_action(action)

    def action_label(self, action: int) -> str:
        return diagnostic_action_label(action)

    def _encode_observation(self, obs: StellaratorObservation) -> np.ndarray:
        params = self._env.state.current_params
        budget_fraction = obs.budget_remaining / BUDGET
        step_fraction = obs.step_number / BUDGET
        return np.array(
            [
                obs.max_elongation,
                obs.aspect_ratio,
                obs.average_triangularity,
                obs.edge_iota_over_nfp,
                obs.p1_score,
                obs.p1_feasibility,
                obs.vacuum_well,
                params.aspect_ratio,
                params.elongation,
                params.rotational_transform,
                params.triangularity_scale,
                budget_fraction,
                step_fraction,
                obs.best_low_fidelity_score,
                obs.best_low_fidelity_feasibility,
                float(obs.constraints_satisfied),
                float(obs.evaluation_failed),
            ],
            dtype=np.float32,
        )

    def _info(self, obs: StellaratorObservation) -> dict[str, object]:
        return {
            "diagnostics_text": obs.diagnostics_text,
            "budget_remaining": obs.budget_remaining,
            "constraints_satisfied": obs.constraints_satisfied,
            "evaluation_failed": obs.evaluation_failed,
            "p1_score": obs.p1_score,
            "p1_feasibility": obs.p1_feasibility,
            "max_elongation": obs.max_elongation,
            "average_triangularity": obs.average_triangularity,
            "edge_iota_over_nfp": obs.edge_iota_over_nfp,
            "termination_reason": self._termination_reason(obs),
            "current_seed": self._seed,
        }

    def _termination_reason(self, obs: StellaratorObservation) -> str:
        if obs.evaluation_failed:
            return "evaluation_failed"
        if obs.constraints_satisfied:
            return "constraints_satisfied"
        if obs.done:
            return "budget_exhausted"
        return "in_progress"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a tiny low-fidelity PPO smoke pass against the repaired Fusion Design Lab "
            "environment and save a small trajectory artifact."
        )
    )
    parser.add_argument(
        "--total-timesteps",
        type=int,
        default=DEFAULT_TOTAL_TIMESTEPS,
        help=f"Total PPO timesteps for the smoke run (default: {DEFAULT_TOTAL_TIMESTEPS}).",
    )
    parser.add_argument(
        "--eval-episodes",
        type=int,
        default=DEFAULT_EVAL_EPISODES,
        help=f"Number of deterministic evaluation episodes to record (default: {DEFAULT_EVAL_EPISODES}).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Base seed for training and evaluation.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where the JSON artifact should be written.",
    )
    return parser.parse_args()


def build_model(env: LowFiSmokeEnv, seed: int) -> PPO:
    return PPO(
        policy="MlpPolicy",
        env=env,
        seed=seed,
        verbose=0,
        device="cpu",
        n_steps=16,
        batch_size=16,
        n_epochs=8,
        gamma=0.995,
        learning_rate=3e-4,
        ent_coef=0.01,
    )


def evaluate_policy(
    model: PPO, *, eval_episodes: int, base_seed: int
) -> tuple[list[EpisodeTrace], list[int]]:
    traces: list[EpisodeTrace] = []
    eval_reset_seed_indices: list[int] = []
    env = LowFiSmokeEnv()
    for episode in range(eval_episodes):
        seed = base_seed + episode
        eval_reset_seed_indices.append(seed % len(RESET_SEEDS))
        obs, info = env.reset(seed=seed)
        done = False
        total_reward = 0.0
        steps: list[TraceStep] = []
        step_index = 0
        final_info = dict[str, object](info)

        while not done:
            action, _ = model.predict(obs, deterministic=True)
            action_index = int(action)
            obs, reward, terminated, truncated, info = env.step(action_index)
            done = terminated or truncated
            total_reward += reward
            step_index += 1
            final_info = info
            steps.append(
                TraceStep(
                    step=step_index,
                    action_index=action_index,
                    action_label=env.action_label(action_index),
                    reward=reward,
                    score=float(info["p1_score"]),
                    feasibility=float(info["p1_feasibility"]),
                    constraints_satisfied=bool(info["constraints_satisfied"]),
                    evaluation_failed=bool(info["evaluation_failed"]),
                    budget_remaining=int(info["budget_remaining"]),
                    termination_reason=str(info["termination_reason"]),
                    max_elongation=float(info["max_elongation"]),
                    average_triangularity=float(info["average_triangularity"]),
                    edge_iota_over_nfp=float(info["edge_iota_over_nfp"]),
                )
            )

        traces.append(
            EpisodeTrace(
                episode=episode,
                seed=seed,
                total_reward=round(total_reward, 4),
                final_score=float(final_info["p1_score"]),
                final_feasibility=float(final_info["p1_feasibility"]),
                constraints_satisfied=bool(final_info["constraints_satisfied"]),
                evaluation_failed=bool(final_info["evaluation_failed"]),
                termination_reason=str(final_info["termination_reason"]),
                steps=steps,
            )
        )
    return traces, eval_reset_seed_indices


def artifact_payload(
    *,
    total_timesteps: int,
    eval_episodes: int,
    seed: int,
    eval_reset_seed_indices: list[int],
    traces: list[EpisodeTrace],
) -> dict[str, object]:
    mean_reward = sum(trace.total_reward for trace in traces) / max(len(traces), 1)
    success_rate = sum(1 for trace in traces if trace.constraints_satisfied) / max(len(traces), 1)
    return {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "mode": "low_fidelity_ppo_smoke",
        "total_timesteps": total_timesteps,
        "eval_episodes": eval_episodes,
        "seed": seed,
        "train_reset_seed_indices": list(TRAIN_RESET_SEED_INDICES),
        "eval_reset_seed_indices": eval_reset_seed_indices,
        "action_space_size": LOW_FI_ACTION_COUNT,
        "diagnostic_run_actions": [
            diagnostic_action_label(action_index) for action_index in range(LOW_FI_ACTION_COUNT)
        ],
        "notes": (
            "Diagnostics-only low-fidelity PPO smoke; submit is excluded and the action "
            "space is narrowed to a two-step repair arc. Evaluation runs across "
            "frozen seeds and records full low-fi traces."
        ),
        "summary": {
            "mean_eval_reward": round(mean_reward, 4),
            "constraint_satisfaction_rate": round(success_rate, 4),
        },
        "episodes": [asdict(trace) for trace in traces],
    }


def write_artifact(output_dir: Path, payload: dict[str, object]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output_path = output_dir / f"ppo_smoke_{timestamp}.json"
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return output_path


def main() -> None:
    args = parse_args()
    env = LowFiSmokeEnv()
    model = build_model(env, seed=args.seed)
    model.learn(total_timesteps=args.total_timesteps, progress_bar=False)
    traces, eval_reset_seed_indices = evaluate_policy(
        model,
        eval_episodes=args.eval_episodes,
        base_seed=args.seed,
    )
    payload = artifact_payload(
        total_timesteps=args.total_timesteps,
        eval_episodes=args.eval_episodes,
        seed=args.seed,
        eval_reset_seed_indices=eval_reset_seed_indices,
        traces=traces,
    )
    output_path = write_artifact(args.output_dir, payload)
    summary = payload["summary"]
    print(output_path)
    print(f"constraint_satisfaction_rate={summary['constraint_satisfaction_rate']}")
    print(f"mean_eval_reward={summary['mean_eval_reward']}")


if __name__ == "__main__":
    main()
