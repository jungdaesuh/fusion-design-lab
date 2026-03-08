from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from fusion_lab.llm_agent import (
    build_prompt,
    parse_action_plan,
    run_episode_with_actions,
)
from fusion_lab.models import StellaratorAction
from server.environment import StellaratorEnvironment

DEFAULT_OUTPUT_DIR: Final[Path] = Path("training/artifacts/llm_rollout")
DEFAULT_MONITOR_OUTPUT_DIR: Final[Path] = Path("training/artifacts/llm_monitor")


def add_action_source_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--completion-file",
        type=Path,
        default=None,
        help="Path to a raw LLM completion containing a JSON action array.",
    )
    parser.add_argument(
        "--action-plan-file",
        type=Path,
        default=None,
        help="Path to a JSON array of actions.",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate an LLM-ready prompt or replay an LLM completion against the live "
            "Fusion Design Lab environment."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    prompt_parser = subparsers.add_parser("prompt", help="Print or save an LLM prompt.")
    prompt_parser.add_argument("--seed", type=int, default=0, help="Reset seed index.")
    prompt_parser.add_argument(
        "--output-file",
        type=Path,
        default=None,
        help="Optional JSON file path for the prompt payload.",
    )

    replay_parser = subparsers.add_parser(
        "replay",
        help="Replay a completion or action-plan file and save a rollout artifact.",
    )
    replay_parser.add_argument("--seed", type=int, default=0, help="Reset seed index.")
    add_action_source_args(replay_parser)
    replay_parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for rollout artifacts.",
    )

    monitor_parser = subparsers.add_parser(
        "monitor",
        help="Replay a completion or action-plan across multiple seeds and print telemetry.",
    )
    add_action_source_args(monitor_parser)
    monitor_parser.add_argument(
        "--seeds",
        type=str,
        default="0,1,2",
        help="Comma-separated reset seed indices to replay.",
    )
    monitor_parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_MONITOR_OUTPUT_DIR,
        help="Directory for monitoring artifacts.",
    )
    return parser.parse_args()


def prompt_payload(seed: int) -> dict[str, object]:
    environment = StellaratorEnvironment()
    observation = environment.reset(seed=seed)
    return {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "seed": seed,
        "prompt": build_prompt(observation),
        "target_spec": observation.target_spec,
        "budget_remaining": observation.budget_remaining,
        "diagnostics_text": observation.diagnostics_text,
    }


def parse_actions(args: argparse.Namespace) -> tuple[str, list[StellaratorAction]]:
    if args.action_plan_file is not None:
        text = args.action_plan_file.read_text()
        source = str(args.action_plan_file)
    elif args.completion_file is not None:
        text = args.completion_file.read_text()
        source = str(args.completion_file)
    else:
        raise ValueError("replay/monitor requires --completion-file or --action-plan-file")

    return source, parse_action_plan(text)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def parse_seed_list(raw: str) -> list[int]:
    seeds: list[int] = []
    for token in raw.split(","):
        stripped = token.strip()
        if not stripped:
            continue
        seeds.append(int(stripped))
    if not seeds:
        raise ValueError("monitor requires at least one seed in --seeds")
    return seeds


def run_prompt(args: argparse.Namespace) -> None:
    payload = prompt_payload(args.seed)
    if args.output_file is not None:
        write_json(args.output_file, payload)
        print(args.output_file)
        return
    print(json.dumps(payload, indent=2))


def run_replay(args: argparse.Namespace) -> None:
    source, actions = parse_actions(args)
    trace = run_episode_with_actions(actions, seed_idx=args.seed)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output_path = args.output_dir / f"llm_rollout_{timestamp}.json"
    payload = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "seed": args.seed,
        "source": source,
        "parsed_action_count": len(actions),
        "actions": [action.model_dump(exclude_none=True) for action in actions],
        "trace": trace.asdict(),
    }
    write_json(output_path, payload)
    print(output_path)


def _reward_terms_summary(reward_breakdown: dict[str, object]) -> str:
    non_zero_terms: list[str] = []
    for key, value in reward_breakdown.items():
        if key in {
            "intent",
            "total",
            "evaluation_failed",
            "recovered_from_failure",
            "reference_constraints_satisfied",
            "reference_score",
            "reference_feasibility",
            "reference_max_elongation",
            "initial_reference_score",
            "terminal_score_ratio",
        }:
            continue
        if isinstance(value, (int, float)) and float(value) != 0.0:
            non_zero_terms.append(f"{key}={float(value):+.4f}")
    return ", ".join(non_zero_terms) if non_zero_terms else "none"


def monitor_payload(
    *,
    source: str,
    actions: list[StellaratorAction],
    seeds: list[int],
) -> dict[str, object]:
    traces = [run_episode_with_actions(actions, seed_idx=seed) for seed in seeds]
    feasible_count = sum(1 for trace in traces if trace.constraints_satisfied)
    high_fidelity_count = sum(1 for trace in traces if trace.final_evaluation_fidelity == "high")
    mean_reward = sum(trace.total_reward for trace in traces) / len(traces)
    return {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "source": source,
        "parsed_action_count": len(actions),
        "actions": [action.model_dump(exclude_none=True) for action in actions],
        "seeds": seeds,
        "summary": {
            "episode_count": len(traces),
            "feasible_episode_count": feasible_count,
            "high_fidelity_episode_count": high_fidelity_count,
            "mean_total_reward": round(mean_reward, 4),
        },
        "episodes": [trace.asdict() for trace in traces],
    }


def write_monitor_summary(payload: dict[str, object]) -> None:
    summary = payload["summary"]
    print(
        "episodes="
        f"{summary['episode_count']} feasible={summary['feasible_episode_count']} "
        f"high_fidelity={summary['high_fidelity_episode_count']} "
        f"mean_total_reward={summary['mean_total_reward']:+.4f}"
    )
    for episode in payload["episodes"]:
        print(
            "seed="
            f"{episode['seed']} total_reward={episode['total_reward']:+.4f} "
            f"final_fidelity={episode['final_evaluation_fidelity']} "
            f"feasible={episode['constraints_satisfied']} "
            f"score={episode['final_score']:.6f} "
            f"feasibility={episode['final_feasibility']:.6f}"
        )
        for step in episode["steps"]:
            action_monitor = step["action_monitor"]
            print(
                "  step="
                f"{step['step']} action={step['action_label']} reward={step['reward']:+.4f} "
                f"fidelity={step['evaluation_fidelity']} feasible={step['constraints_satisfied']} "
                f"score={step['p1_score']:.6f} feasibility={step['p1_feasibility']:.6f} "
                f"clamped={action_monitor['clamped']} no_op={action_monitor['no_op']}"
            )
            print(f"    reward_terms={_reward_terms_summary(step['reward_breakdown'])}")


def run_monitor(args: argparse.Namespace) -> None:
    source, actions = parse_actions(args)
    seeds = parse_seed_list(args.seeds)
    payload = monitor_payload(source=source, actions=actions, seeds=seeds)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output_path = args.output_dir / f"llm_monitor_{timestamp}.json"
    write_json(output_path, payload)
    print(output_path)
    write_monitor_summary(payload)


def main() -> None:
    args = parse_args()
    if args.command == "prompt":
        run_prompt(args)
        return
    if args.command == "replay":
        run_replay(args)
        return
    run_monitor(args)


if __name__ == "__main__":
    main()
