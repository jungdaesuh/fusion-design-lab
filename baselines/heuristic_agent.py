"""Heuristic baseline agent for the stellarator design environment."""

from __future__ import annotations

import sys

from fusion_lab.models import StellaratorAction, StellaratorObservation
from server.environment import StellaratorEnvironment

FEASIBLE_SUBMIT_ELONGATION_MAX = 7.45
TRIANGULARITY_TARGET_MAX = -0.5
LOW_IOTA_RESET_THRESHOLD = 0.305
IOTA_RECOVERY_THRESHOLD = 0.3
ASPECT_RATIO_TARGET_MAX = 4.0


def heuristic_episode(
    env: StellaratorEnvironment, seed: int | None = None
) -> tuple[float, list[dict[str, object]]]:
    obs = env.reset(seed=seed)
    total_reward = 0.0
    trace: list[dict[str, object]] = [
        {
            "step": 0,
            "score": obs.p1_score,
            "evaluation_fidelity": obs.evaluation_fidelity,
            "constraints_satisfied": obs.constraints_satisfied,
            "feasibility": obs.p1_feasibility,
            "max_elongation": obs.max_elongation,
            "average_triangularity": obs.average_triangularity,
            "edge_iota_over_nfp": obs.edge_iota_over_nfp,
        }
    ]

    while not obs.done:
        action = (
            StellaratorAction(intent="submit") if obs.budget_remaining <= 1 else _choose_action(obs)
        )
        obs = env.step(action)
        total_reward += obs.reward or 0.0
        trace.append(
            {
                "step": len(trace),
                "action": _action_label(action),
                "score": obs.p1_score,
                "evaluation_fidelity": obs.evaluation_fidelity,
                "constraints_satisfied": obs.constraints_satisfied,
                "feasibility": obs.p1_feasibility,
                "max_elongation": obs.max_elongation,
                "average_triangularity": obs.average_triangularity,
                "edge_iota_over_nfp": obs.edge_iota_over_nfp,
                "reward": obs.reward,
                "evaluation_failed": obs.evaluation_failed,
            }
        )

    return total_reward, trace


def _choose_action(obs: StellaratorObservation) -> StellaratorAction:
    if obs.evaluation_failed:
        return StellaratorAction(intent="restore_best")

    if obs.constraints_satisfied:
        if (
            obs.max_elongation <= FEASIBLE_SUBMIT_ELONGATION_MAX
            or obs.budget_remaining <= 2
            or obs.step_number >= 3
        ):
            return StellaratorAction(intent="submit")
        return StellaratorAction(
            intent="run",
            parameter="elongation",
            direction="decrease",
            magnitude="small",
        )

    if obs.average_triangularity > TRIANGULARITY_TARGET_MAX:
        if obs.step_number == 0 and obs.edge_iota_over_nfp < LOW_IOTA_RESET_THRESHOLD:
            return StellaratorAction(
                intent="run",
                parameter="rotational_transform",
                direction="increase",
                magnitude="medium",
            )
        return StellaratorAction(
            intent="run",
            parameter="triangularity_scale",
            direction="increase",
            magnitude="medium",
        )

    if obs.edge_iota_over_nfp < IOTA_RECOVERY_THRESHOLD:
        return StellaratorAction(
            intent="run",
            parameter="rotational_transform",
            direction="increase",
            magnitude="small",
        )

    if obs.aspect_ratio > ASPECT_RATIO_TARGET_MAX:
        return StellaratorAction(
            intent="run",
            parameter="aspect_ratio",
            direction="decrease",
            magnitude="small",
        )

    return StellaratorAction(
        intent="run",
        parameter="elongation",
        direction="decrease",
        magnitude="small",
    )


def _action_label(action: StellaratorAction) -> str:
    if action.intent != "run":
        return action.intent
    return f"{action.parameter} {action.direction} {action.magnitude}"


def main(n_episodes: int = 20) -> None:
    env = StellaratorEnvironment()
    rewards: list[float] = []

    for i in range(n_episodes):
        total_reward, trace = heuristic_episode(env, seed=i)
        final = trace[-1]
        rewards.append(total_reward)
        print(
            f"Episode {i:3d}: steps={len(trace) - 1}  "
            f"final_score={final['score']:.6f}  fidelity={final['evaluation_fidelity']}  "
            f"constraints={'yes' if final['constraints_satisfied'] else 'no'}  "
            f"reward={total_reward:+.4f}"
        )

    mean_reward = sum(rewards) / len(rewards)
    print(f"\nHeuristic baseline ({n_episodes} episodes): mean_reward={mean_reward:+.4f}")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    main(n)
