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
    replay_parser.add_argument(
        "--completion-file",
        type=Path,
        default=None,
        help="Path to a raw LLM completion containing a JSON action array.",
    )
    replay_parser.add_argument(
        "--action-plan-file",
        type=Path,
        default=None,
        help="Path to a JSON array of actions.",
    )
    replay_parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for rollout artifacts.",
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
        raise ValueError("replay requires --completion-file or --action-plan-file")

    return source, parse_action_plan(text)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


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


def main() -> None:
    args = parse_args()
    if args.command == "prompt":
        run_prompt(args)
        return
    run_replay(args)


if __name__ == "__main__":
    main()
