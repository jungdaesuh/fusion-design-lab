"""Random baseline agent for the stellarator design environment."""

from __future__ import annotations

import random
import sys

from fusion_lab.models import StellaratorAction
from server.environment import StellaratorEnvironment

PARAMETERS = [
    "aspect_ratio",
    "elongation",
    "rotational_transform",
    "triangularity_scale",
]
DIRECTIONS = ["increase", "decrease"]
MAGNITUDES = ["small", "medium", "large"]


def random_episode(
    env: StellaratorEnvironment, seed: int | None = None
) -> tuple[float, list[dict[str, object]]]:
    rng = random.Random(seed)
    obs = env.reset(seed=seed)
    total_reward = 0.0
    trace: list[dict[str, object]] = [
        {
            "step": 0,
            "score": obs.p1_score,
            "evaluation_fidelity": obs.evaluation_fidelity,
            "constraints_satisfied": obs.constraints_satisfied,
        }
    ]

    while not obs.done:
        if obs.budget_remaining <= 1:
            action = StellaratorAction(intent="submit")
        else:
            action = StellaratorAction(
                intent="run",
                parameter=rng.choice(PARAMETERS),
                direction=rng.choice(DIRECTIONS),
                magnitude=rng.choice(MAGNITUDES),
            )
        obs = env.step(action)
        total_reward += obs.reward or 0.0
        trace.append(
            {
                "step": len(trace),
                "action": action.intent,
                "score": obs.p1_score,
                "evaluation_fidelity": obs.evaluation_fidelity,
                "constraints_satisfied": obs.constraints_satisfied,
                "evaluation_failed": obs.evaluation_failed,
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
            f"final_score={final['score']:.6f}  fidelity={final['evaluation_fidelity']}  "
            f"constraints={'yes' if final['constraints_satisfied'] else 'no'}  "
            f"reward={total_reward:+.4f}"
        )

    mean_reward = sum(rewards) / len(rewards)
    print(f"\nRandom baseline ({n_episodes} episodes): mean_reward={mean_reward:+.4f}")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    main(n)
