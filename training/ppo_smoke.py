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
DEFAULT_TOTAL_TIMESTEPS: Final[int] = 128
DEFAULT_EVAL_EPISODES: Final[int] = 3

RUN_ACTION_SPECS: Final[tuple[tuple[str, str, str], ...]] = (
    ("aspect_ratio", "increase", "small"),
    ("aspect_ratio", "increase", "medium"),
    ("aspect_ratio", "increase", "large"),
    ("aspect_ratio", "decrease", "small"),
    ("aspect_ratio", "decrease", "medium"),
    ("aspect_ratio", "decrease", "large"),
    ("elongation", "increase", "small"),
    ("elongation", "increase", "medium"),
    ("elongation", "increase", "large"),
    ("elongation", "decrease", "small"),
    ("elongation", "decrease", "medium"),
    ("elongation", "decrease", "large"),
    ("rotational_transform", "increase", "small"),
    ("rotational_transform", "increase", "medium"),
    ("rotational_transform", "increase", "large"),
    ("rotational_transform", "decrease", "small"),
    ("rotational_transform", "decrease", "medium"),
    ("rotational_transform", "decrease", "large"),
    ("triangularity_scale", "increase", "small"),
    ("triangularity_scale", "increase", "medium"),
    ("triangularity_scale", "increase", "large"),
    ("triangularity_scale", "decrease", "small"),
    ("triangularity_scale", "decrease", "medium"),
    ("triangularity_scale", "decrease", "large"),
)
LOW_FI_ACTION_COUNT: Final[int] = len(RUN_ACTION_SPECS) + 1
LOW_FI_RESTORE_ACTION_INDEX: Final[int] = len(RUN_ACTION_SPECS)


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
    steps: list[TraceStep]


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
            shape=(12,),
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
        next_seed = self._episode_index % len(RESET_SEEDS)
        self._episode_index += 1
        return next_seed

    def step(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, object]]:
        obs = self._env.step(self._decode_action(action))
        return (
            self._encode_observation(obs),
            float(obs.reward or 0.0),
            bool(obs.done),
            False,
            self._info(obs),
        )

    def _decode_action(self, action: int) -> StellaratorAction:
        if action == LOW_FI_RESTORE_ACTION_INDEX:
            return StellaratorAction(intent="restore_best")
        parameter, direction, magnitude = RUN_ACTION_SPECS[action]
        return StellaratorAction(
            intent="run",
            parameter=parameter,
            direction=direction,
            magnitude=magnitude,
        )

    def action_label(self, action: int) -> str:
        if action == LOW_FI_RESTORE_ACTION_INDEX:
            return "restore_best"
        parameter, direction, magnitude = RUN_ACTION_SPECS[action]
        return f"{parameter} {direction} {magnitude}"

    def _encode_observation(self, obs: StellaratorObservation) -> np.ndarray:
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
                budget_fraction,
                step_fraction,
                obs.best_low_fidelity_score,
                obs.best_low_fidelity_feasibility,
                float(obs.constraints_satisfied) - float(obs.evaluation_failed),
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
        }


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
        n_steps=32,
        batch_size=32,
        n_epochs=4,
        gamma=0.98,
        learning_rate=3e-4,
        ent_coef=0.01,
    )


def evaluate_policy(model: PPO, *, eval_episodes: int, base_seed: int) -> list[EpisodeTrace]:
    traces: list[EpisodeTrace] = []
    for episode in range(eval_episodes):
        env = LowFiSmokeEnv()
        seed = base_seed + episode
        obs, _ = env.reset(seed=seed)
        done = False
        total_reward = 0.0
        steps: list[TraceStep] = []
        step_index = 0
        final_info: dict[str, object] = {}

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
                    max_elongation=float(obs[0]),
                    average_triangularity=float(obs[2]),
                    edge_iota_over_nfp=float(obs[3]),
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
                steps=steps,
            )
        )
    return traces


def artifact_payload(
    *,
    total_timesteps: int,
    eval_episodes: int,
    seed: int,
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
        "train_reset_seed_indices": list(range(len(RESET_SEEDS))),
        "action_space_size": LOW_FI_ACTION_COUNT,
        "notes": (
            "Diagnostic-only PPO smoke run. Submit is intentionally excluded here so the "
            "smoke loop stays low-fidelity and fast. Training resets cycle through the "
            "frozen low-fidelity reset seeds to surface positive repair signal sooner."
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
    traces = evaluate_policy(
        model,
        eval_episodes=args.eval_episodes,
        base_seed=args.seed,
    )
    payload = artifact_payload(
        total_timesteps=args.total_timesteps,
        eval_episodes=args.eval_episodes,
        seed=args.seed,
        traces=traces,
    )
    output_path = write_artifact(args.output_dir, payload)
    print(output_path)


if __name__ == "__main__":
    main()
