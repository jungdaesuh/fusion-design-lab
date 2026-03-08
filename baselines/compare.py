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
    random_final_scores: list[float] = []
    heuristic_final_scores: list[float] = []
    random_feasible: list[int] = []
    heuristic_feasible: list[int] = []

    for i in range(n_episodes):
        rr, rt = random_episode(env, seed=i)
        _require_submit_fidelity(rt[-1], baseline_name="random")
        random_rewards.append(rr)
        random_final_scores.append(rt[-1]["score"])
        random_feasible.append(1 if rt[-1]["constraints_satisfied"] else 0)

        hr, ht = heuristic_episode(env, seed=i)
        _require_submit_fidelity(ht[-1], baseline_name="heuristic")
        heuristic_rewards.append(hr)
        heuristic_final_scores.append(ht[-1]["score"])
        heuristic_feasible.append(1 if ht[-1]["constraints_satisfied"] else 0)

    r_mean = sum(random_rewards) / len(random_rewards)
    h_mean = sum(heuristic_rewards) / len(heuristic_rewards)
    r_score = sum(random_final_scores) / len(random_final_scores)
    h_score = sum(heuristic_final_scores) / len(heuristic_final_scores)
    r_feasible = sum(random_feasible)
    h_feasible = sum(heuristic_feasible)

    print(f"{'Metric':<25} {'Random':>12} {'Heuristic':>12}")
    print("-" * 51)
    print(f"{'Mean reward':<25} {r_mean:>+12.4f} {h_mean:>+12.4f}")
    print(f"{'Mean final P1 score':<25} {r_score:>12.6f} {h_score:>12.6f}")
    print(f"{'Feasible finals':<25} {r_feasible:>12d} {h_feasible:>12d}")
    print(f"{'Episodes':<25} {n_episodes:>12d} {n_episodes:>12d}")
    print()

    wins = sum(1 for h, r in zip(heuristic_rewards, random_rewards) if h > r)
    print(f"Heuristic wins: {wins}/{n_episodes} episodes ({100 * wins / n_episodes:.0f}%)")


def _require_submit_fidelity(final_step: dict[str, object], *, baseline_name: str) -> None:
    fidelity = final_step["evaluation_fidelity"]
    if fidelity != "high":
        raise ValueError(
            f"{baseline_name} baseline ended on {fidelity!r} instead of high-fidelity submit."
        )


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    main(n)
