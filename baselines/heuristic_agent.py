"""Heuristic baseline agent for the stellarator design environment.

Strategy: guided perturbations informed by domain knowledge.
1. Probe the most sensitive coefficient (zs12) first with a small move.
2. Apply medium perturbations in directions that typically improve QS.
3. Use restore_best to recover from any worsening.
4. Submit before exhausting budget.
"""

from __future__ import annotations

import sys

from fusion_lab.models import StellaratorAction
from server.environment import StellaratorEnvironment

STRATEGY: list[tuple[str, str, str, str]] = [
    ("tune_zs12", "decrease", "small", "hot"),
    ("tune_zs12", "decrease", "medium", "hot"),
    ("tune_rc11", "increase", "small", "hot"),
    ("tune_rc10", "increase", "medium", "hot"),
    ("tune_zs11", "decrease", "small", "hot"),
]


def heuristic_episode(
    env: StellaratorEnvironment, seed: int | None = None
) -> tuple[float, list[dict[str, object]]]:
    obs = env.reset(seed=seed)
    total_reward = 0.0
    trace: list[dict[str, object]] = [{"step": 0, "qs": obs.quasi_symmetry_residual}]
    prev_best = obs.best_qs_residual

    for operator, direction, magnitude, restart in STRATEGY:
        if obs.done or obs.budget_remaining <= 1:
            break

        action = StellaratorAction(
            intent="run",
            operator=operator,
            direction=direction,
            magnitude=magnitude,
            restart=restart,
        )
        obs = env.step(action)
        total_reward += obs.reward or 0.0
        trace.append(
            {
                "step": len(trace),
                "action": f"{operator} {direction} {magnitude}",
                "qs": obs.quasi_symmetry_residual,
                "best_qs": obs.best_qs_residual,
                "reward": obs.reward,
            }
        )

        if obs.best_qs_residual > prev_best and obs.budget_remaining > 1:
            restore = StellaratorAction(intent="restore_best")
            obs = env.step(restore)
            total_reward += obs.reward or 0.0
            trace.append(
                {
                    "step": len(trace),
                    "action": "restore_best",
                    "qs": obs.quasi_symmetry_residual,
                    "best_qs": obs.best_qs_residual,
                    "reward": obs.reward,
                }
            )

        prev_best = obs.best_qs_residual

    if not obs.done:
        submit = StellaratorAction(intent="submit")
        obs = env.step(submit)
        total_reward += obs.reward or 0.0
        trace.append(
            {
                "step": len(trace),
                "action": "submit",
                "qs": obs.quasi_symmetry_residual,
                "best_qs": obs.best_qs_residual,
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
            f"final_qs={final['qs']:.6f}  best_qs={final['best_qs']:.6f}  "
            f"reward={total_reward:+.4f}"
        )

    mean_reward = sum(rewards) / len(rewards)
    print(f"\nHeuristic baseline ({n_episodes} episodes): mean_reward={mean_reward:+.4f}")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    main(n)
