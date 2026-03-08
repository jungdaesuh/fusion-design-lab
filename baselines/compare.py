"""Run both baselines and print a comparison summary."""

from __future__ import annotations

import sys

from baselines.heuristic_agent import heuristic_episode
from baselines.random_agent import random_episode
from server.environment import StellaratorEnvironment


def main(n_episodes: int = 20) -> None:
    env = StellaratorEnvironment()

    random_rewards: list[float] = []
    heuristic_rewards: list[float] = []
    random_best_scores: list[float] = []
    heuristic_best_scores: list[float] = []

    for i in range(n_episodes):
        rr, rt = random_episode(env, seed=i)
        random_rewards.append(rr)
        random_best_scores.append(rt[-1]["best_score"])

        hr, ht = heuristic_episode(env, seed=i)
        heuristic_rewards.append(hr)
        heuristic_best_scores.append(ht[-1]["best_score"])

    r_mean = sum(random_rewards) / len(random_rewards)
    h_mean = sum(heuristic_rewards) / len(heuristic_rewards)
    r_score = sum(random_best_scores) / len(random_best_scores)
    h_score = sum(heuristic_best_scores) / len(heuristic_best_scores)

    print(f"{'Metric':<25} {'Random':>12} {'Heuristic':>12}")
    print("-" * 51)
    print(f"{'Mean reward':<25} {r_mean:>+12.4f} {h_mean:>+12.4f}")
    print(f"{'Mean best P1 score':<25} {r_score:>12.6f} {h_score:>12.6f}")
    print(f"{'Episodes':<25} {n_episodes:>12d} {n_episodes:>12d}")
    print()

    wins = sum(1 for h, r in zip(heuristic_rewards, random_rewards) if h > r)
    print(f"Heuristic wins: {wins}/{n_episodes} episodes ({100 * wins / n_episodes:.0f}%)")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    main(n)
