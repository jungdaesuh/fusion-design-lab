"""Random baseline agent for the stellarator design environment."""

from __future__ import annotations

import random
import sys

from fusion_lab.models import StellaratorAction
from server.environment import StellaratorEnvironment

OPERATORS = ["tune_rc10", "tune_rc11", "tune_zs11", "tune_zs12"]
DIRECTIONS = ["increase", "decrease"]
MAGNITUDES = ["small", "medium", "large"]
RESTARTS = ["hot", "cold"]


def random_episode(
    env: StellaratorEnvironment, seed: int | None = None
) -> tuple[float, list[dict[str, object]]]:
    rng = random.Random(seed)
    obs = env.reset(seed=seed)
    total_reward = 0.0
    trace: list[dict[str, object]] = [{"step": 0, "qs": obs.quasi_symmetry_residual}]

    while not obs.done:
        if obs.budget_remaining <= 0:
            action = StellaratorAction(intent="submit")
        else:
            action = StellaratorAction(
                intent="run",
                operator=rng.choice(OPERATORS),
                direction=rng.choice(DIRECTIONS),
                magnitude=rng.choice(MAGNITUDES),
                restart=rng.choice(RESTARTS),
            )
        obs = env.step(action)
        total_reward += obs.reward or 0.0
        trace.append(
            {
                "step": len(trace),
                "action": action.intent,
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
        total_reward, trace = random_episode(env, seed=i)
        final = trace[-1]
        rewards.append(total_reward)
        print(
            f"Episode {i:3d}: steps={len(trace) - 1}  "
            f"final_qs={final['qs']:.6f}  best_qs={final['best_qs']:.6f}  "
            f"reward={total_reward:+.4f}"
        )

    mean_reward = sum(rewards) / len(rewards)
    print(f"\nRandom baseline ({n_episodes} episodes): mean_reward={mean_reward:+.4f}")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    main(n)
