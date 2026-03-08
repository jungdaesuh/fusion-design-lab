"""Heuristic baseline agent for the stellarator design environment.

Strategy: guided perturbations informed by domain knowledge.
1. Push elongation upward to improve triangularity.
2. Nudge rotational transform upward to stay on the iota side of feasibility.
3. Use restore_best to recover from any worsening.
4. Submit before exhausting budget.
"""

from __future__ import annotations

import sys

from fusion_lab.models import StellaratorAction
from server.environment import StellaratorEnvironment

STRATEGY: list[tuple[str, str, str]] = [
    ("elongation", "increase", "medium"),
    ("elongation", "increase", "small"),
    ("rotational_transform", "increase", "small"),
    ("aspect_ratio", "decrease", "small"),
    ("rotational_transform", "increase", "small"),
]


def heuristic_episode(
    env: StellaratorEnvironment, seed: int | None = None
) -> tuple[float, list[dict[str, object]]]:
    obs = env.reset(seed=seed)
    total_reward = 0.0
    trace: list[dict[str, object]] = [{"step": 0, "score": obs.p1_score}]
    prev_best = (
        int(obs.best_feasibility <= 0.01),
        obs.best_score if obs.best_feasibility <= 0.01 else -obs.best_feasibility,
    )

    for parameter, direction, magnitude in STRATEGY:
        if obs.done or obs.budget_remaining <= 1:
            break

        action = StellaratorAction(
            intent="run",
            parameter=parameter,
            direction=direction,
            magnitude=magnitude,
        )
        obs = env.step(action)
        total_reward += obs.reward or 0.0
        trace.append(
            {
                "step": len(trace),
                "action": f"{parameter} {direction} {magnitude}",
                "score": obs.p1_score,
                "best_score": obs.best_score,
                "reward": obs.reward,
            }
        )

        current_best = (
            int(obs.best_feasibility <= 0.01),
            obs.best_score if obs.best_feasibility <= 0.01 else -obs.best_feasibility,
        )

        if current_best < prev_best and obs.budget_remaining > 1:
            restore = StellaratorAction(intent="restore_best")
            obs = env.step(restore)
            total_reward += obs.reward or 0.0
            trace.append(
                {
                    "step": len(trace),
                    "action": "restore_best",
                    "score": obs.p1_score,
                    "best_score": obs.best_score,
                    "reward": obs.reward,
                }
            )

        prev_best = current_best

    if not obs.done:
        submit = StellaratorAction(intent="submit")
        obs = env.step(submit)
        total_reward += obs.reward or 0.0
        trace.append(
            {
                "step": len(trace),
                "action": "submit",
                "score": obs.p1_score,
                "best_score": obs.best_score,
                "reward": obs.reward,
            }
        )

    return total_reward, trace


def main(n_episodes: int = 20) -> None:
    env = StellaratorEnvironment()
    rewards: list[float] = []

    for i in range(n_episodes):
        total_reward, trace = heuristic_episode(env, seed=i)
        final = trace[-1]
        rewards.append(total_reward)
        print(
            f"Episode {i:3d}: steps={len(trace) - 1}  "
            f"final_score={final['score']:.6f}  best_score={final['best_score']:.6f}  "
            f"reward={total_reward:+.4f}"
        )

    mean_reward = sum(rewards) / len(rewards)
    print(f"\nHeuristic baseline ({n_episodes} episodes): mean_reward={mean_reward:+.4f}")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    main(n)
