from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from fusion_lab.llm_agent import (
    build_prompt,
    parse_action_plan,
    run_episode_with_actions,
    LLMEpisodeTrace,
)
from fusion_lab.models import StellaratorAction
from server.environment import StellaratorEnvironment

DEFAULT_OUTPUT_DIR: Final[Path] = Path("training/artifacts/llm_rollout")
DEFAULT_MONITOR_OUTPUT_DIR: Final[Path] = Path("training/artifacts/llm_monitor")
DEFAULT_EVALUATE_OUTPUT_DIR: Final[Path] = Path("training/artifacts/llm_evaluate")


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

    evaluate_parser = subparsers.add_parser(
        "evaluate",
        help=(
            "Generate fresh completions per seed with a model command, replay them, "
            "and save aggregate reward/outcome metrics."
        ),
    )
    evaluate_parser.add_argument(
        "--completion-command",
        type=str,
        required=True,
        help=(
            "Shell command that reads the prompt from stdin and writes a completion to stdout. "
            "The current seed is exposed as FUSION_LAB_SEED."
        ),
    )
    evaluate_parser.add_argument(
        "--seeds",
        type=str,
        default="0,1,2",
        help="Comma-separated reset seed indices to evaluate.",
    )
    evaluate_parser.add_argument(
        "--label",
        type=str,
        default="model",
        help="Short label stored in the evaluation artifact.",
    )
    evaluate_parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_EVALUATE_OUTPUT_DIR,
        help="Directory for evaluation artifacts.",
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


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _round_metric(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 4)


def _format_metric(value: object, precision: int = 4, signed: bool = False) -> str:
    if not isinstance(value, (int, float)):
        return "n/a"
    if signed:
        return f"{float(value):+.{precision}f}"
    return f"{float(value):.{precision}f}"


def _pearson_correlation(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    centered_x = [value - mean_x for value in xs]
    centered_y = [value - mean_y for value in ys]
    variance_x = sum(value * value for value in centered_x)
    variance_y = sum(value * value for value in centered_y)
    if math.isclose(variance_x, 0.0) or math.isclose(variance_y, 0.0):
        return None
    covariance = sum(x_value * y_value for x_value, y_value in zip(centered_x, centered_y))
    return covariance / math.sqrt(variance_x * variance_y)


def summarize_traces(traces: list[LLMEpisodeTrace]) -> dict[str, object]:
    feasible_count = sum(1 for trace in traces if trace.constraints_satisfied)
    high_fidelity_traces = [trace for trace in traces if trace.final_evaluation_fidelity == "high"]
    high_fidelity_count = len(high_fidelity_traces)
    failed_count = sum(1 for trace in traces if trace.evaluation_failed)
    total_rewards = [trace.total_reward for trace in traces]
    final_scores = [trace.final_score for trace in traces]
    final_feasibilities = [trace.final_feasibility for trace in traces]
    high_fidelity_scores = [trace.final_score for trace in high_fidelity_traces]
    high_fidelity_feasibilities = [trace.final_feasibility for trace in high_fidelity_traces]
    feasible_flags = [1.0 if trace.constraints_satisfied else 0.0 for trace in traces]
    episode_count = len(traces)

    return {
        "episode_count": episode_count,
        "feasible_episode_count": feasible_count,
        "high_fidelity_episode_count": high_fidelity_count,
        "evaluation_failed_episode_count": failed_count,
        "feasible_rate": _round_metric(feasible_count / episode_count),
        "high_fidelity_rate": _round_metric(high_fidelity_count / episode_count),
        "evaluation_failed_rate": _round_metric(failed_count / episode_count),
        "mean_total_reward": _round_metric(_mean(total_rewards)),
        "mean_final_score": _round_metric(_mean(final_scores)),
        "mean_final_feasibility": _round_metric(_mean(final_feasibilities)),
        "mean_high_fidelity_score": _round_metric(_mean(high_fidelity_scores)),
        "mean_high_fidelity_feasibility": _round_metric(_mean(high_fidelity_feasibilities)),
        "reward_final_score_correlation": _round_metric(
            _pearson_correlation(total_rewards, final_scores)
        ),
        "reward_feasible_correlation": _round_metric(
            _pearson_correlation(total_rewards, feasible_flags)
        ),
    }


def monitor_payload(
    *,
    source: str,
    actions: list[StellaratorAction],
    seeds: list[int],
) -> dict[str, object]:
    traces = [run_episode_with_actions(actions, seed_idx=seed) for seed in seeds]
    return {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "source": source,
        "parsed_action_count": len(actions),
        "actions": [action.model_dump(exclude_none=True) for action in actions],
        "seeds": seeds,
        "summary": summarize_traces(traces),
        "episodes": [trace.asdict() for trace in traces],
    }


def _run_completion_command(*, prompt: str, seed: int, command: str) -> str:
    env = os.environ.copy()
    env["FUSION_LAB_SEED"] = str(seed)
    shell_path = env.get("SHELL", "/bin/sh")
    completed = subprocess.run(
        [shell_path, "-lc", command],
        input=prompt,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "completion command failed "
            f"(seed={seed}, exit_code={completed.returncode}): {completed.stderr.strip()}"
        )
    return completed.stdout


def evaluate_payload(
    *,
    completion_command: str,
    label: str,
    seeds: list[int],
) -> dict[str, object]:
    evaluations: list[dict[str, object]] = []
    traces: list[LLMEpisodeTrace] = []

    for seed in seeds:
        observation = StellaratorEnvironment().reset(seed=seed)
        prompt = build_prompt(observation)
        completion = _run_completion_command(
            prompt=prompt,
            seed=seed,
            command=completion_command,
        )
        actions = parse_action_plan(completion)
        trace = run_episode_with_actions(actions, seed_idx=seed)
        traces.append(trace)
        evaluations.append(
            {
                "seed": seed,
                "prompt": prompt,
                "completion": completion,
                "parsed_action_count": len(actions),
                "actions": [action.model_dump(exclude_none=True) for action in actions],
                "trace": trace.asdict(),
            }
        )

    return {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "label": label,
        "completion_command": completion_command,
        "seeds": seeds,
        "summary": summarize_traces(traces),
        "episodes": evaluations,
    }


def write_monitor_summary(payload: dict[str, object]) -> None:
    summary = payload["summary"]
    print(
        "episodes="
        f"{summary['episode_count']} feasible={summary['feasible_episode_count']} "
        f"high_fidelity={summary['high_fidelity_episode_count']} "
        f"failed={summary['evaluation_failed_episode_count']} "
        f"mean_total_reward={_format_metric(summary['mean_total_reward'], signed=True)} "
        f"mean_high_fidelity_score={_format_metric(summary['mean_high_fidelity_score'], signed=True)} "
        f"reward_score_corr={summary['reward_final_score_correlation']}"
    )
    for episode in payload["episodes"]:
        trace = episode.get("trace", episode)
        print(
            "seed="
            f"{trace['seed']} total_reward={trace['total_reward']:+.4f} "
            f"final_fidelity={trace['final_evaluation_fidelity']} "
            f"feasible={trace['constraints_satisfied']} "
            f"score={trace['final_score']:.6f} "
            f"feasibility={trace['final_feasibility']:.6f}"
        )
        if "parsed_action_count" in episode:
            print(f"  parsed_actions={episode['parsed_action_count']}")
        for step in trace["steps"]:
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


def run_evaluate(args: argparse.Namespace) -> None:
    seeds = parse_seed_list(args.seeds)
    payload = evaluate_payload(
        completion_command=args.completion_command,
        label=args.label,
        seeds=seeds,
    )
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output_path = args.output_dir / f"llm_evaluate_{timestamp}.json"
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
    if args.command == "evaluate":
        run_evaluate(args)
        return
    run_monitor(args)


if __name__ == "__main__":
    main()
