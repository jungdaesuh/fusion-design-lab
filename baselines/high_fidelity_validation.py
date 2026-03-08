"""Validation utilities for high-fidelity fixture pairing and submit-side traces."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from pprint import pformat
from time import perf_counter
from typing import Any

from fusion_lab.models import LowDimBoundaryParams, StellaratorAction
from server.contract import N_FIELD_PERIODS
from server.environment import StellaratorEnvironment
from server.physics import EvaluationMetrics, build_boundary_from_params, evaluate_boundary


LOW_FIDELITY_TOLERANCE = 1.0e-6


def _float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class FixturePairResult:
    name: str
    file: str
    status: str
    low_fidelity: dict[str, Any]
    high_fidelity: dict[str, Any]
    comparison: dict[str, Any]


@dataclass(frozen=True)
class TraceStep:
    step: int
    intent: str
    action: str
    reward: float
    score: float
    feasibility: float
    constraints_satisfied: bool
    feasibility_delta: float | None
    score_delta: float | None
    max_elongation: float
    p1_feasibility: float
    budget_remaining: int
    evaluation_fidelity: str
    done: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run paired high-fidelity fixture checks and a submit-side manual trace "
            "for the repaired P1 contract."
        )
    )
    parser.add_argument(
        "--fixture-dir",
        type=Path,
        default=Path("server/data/p1"),
        help="Directory containing tracked P1 fixture JSON files.",
    )
    parser.add_argument(
        "--fixture-output",
        type=Path,
        default=Path("baselines/fixture_high_fidelity_pairs.json"),
        help="Output path for paired fixture summary JSON.",
    )
    parser.add_argument(
        "--trace-output",
        type=Path,
        default=Path("baselines/submit_side_trace.json"),
        help="Output path for one submit-side manual trace JSON.",
    )
    parser.add_argument(
        "--no-write-fixture-updates",
        action="store_true",
        help="Do not write paired high-fidelity results back into fixture files.",
    )
    parser.add_argument(
        "--skip-submit-trace",
        action="store_true",
        help="Only run paired fixture checks.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Seed for the submit-side manual trace reset state.",
    )
    parser.add_argument(
        "--submit-action-sequence",
        type=str,
        default=(
            "run:rotational_transform:increase:medium,"
            "run:triangularity_scale:increase:medium,"
            "run:elongation:decrease:small,"
            "submit"
        ),
        help=(
            "Comma-separated submit trace sequence. "
            "Run actions are `run:parameter:direction:magnitude`; include `submit` as the last token."
        ),
    )
    return parser.parse_args()


def _fixture_files(fixture_dir: Path) -> list[Path]:
    return sorted(path for path in fixture_dir.glob("*.json") if path.is_file())


def _load_fixture(path: Path) -> dict[str, Any]:
    with path.open("r") as file:
        return json.load(file)


def _metrics_payload(metrics: EvaluationMetrics) -> dict[str, Any]:
    return {
        "evaluation_failed": metrics.evaluation_failed,
        "constraints_satisfied": metrics.constraints_satisfied,
        "p1_score": metrics.p1_score,
        "p1_feasibility": metrics.p1_feasibility,
        "max_elongation": metrics.max_elongation,
        "aspect_ratio": metrics.aspect_ratio,
        "average_triangularity": metrics.average_triangularity,
        "edge_iota_over_nfp": metrics.edge_iota_over_nfp,
        "vacuum_well": metrics.vacuum_well,
        "evaluation_fidelity": metrics.evaluation_fidelity,
        "failure_reason": metrics.failure_reason,
    }


def _parse_submit_sequence(raw: str) -> list[StellaratorAction]:
    actions: list[StellaratorAction] = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue

        if token == "submit":
            actions.append(StellaratorAction(intent="submit"))
            continue

        parts = token.split(":")
        if len(parts) != 4 or parts[0] != "run":
            raise ValueError(
                "Expected token format `run:parameter:direction:magnitude` or `submit`."
            )
        _, parameter, direction, magnitude = parts
        actions.append(
            StellaratorAction(
                intent="run",
                parameter=parameter,
                direction=direction,
                magnitude=magnitude,
            )
        )

    if not actions:
        raise ValueError("submit-action-sequence must include at least one action.")
    if actions[-1].intent != "submit":
        raise ValueError("submit-action-sequence must end with submit.")
    return actions


def _compare_low_snapshot(
    stored: dict[str, Any],
    current: dict[str, Any],
) -> tuple[bool, dict[str, Any]]:
    numeric_keys = [
        "p1_feasibility",
        "p1_score",
        "max_elongation",
        "aspect_ratio",
        "average_triangularity",
        "edge_iota_over_nfp",
        "vacuum_well",
    ]
    exact_keys = [
        "constraints_satisfied",
        "evaluation_fidelity",
        "evaluation_failed",
        "failure_reason",
    ]
    missing_fields: list[str] = []
    drift_fields: dict[str, dict[str, float]] = {}
    mismatches: list[dict[str, Any]] = []
    max_abs_drift = 0.0

    for key in numeric_keys:
        if key not in stored:
            missing_fields.append(key)
            continue

        expected = _float(stored.get(key))
        actual = _float(current.get(key))
        if expected is None or actual is None:
            mismatches.append(
                {
                    "field": key,
                    "expected": stored.get(key),
                    "actual": current.get(key),
                    "reason": "non-numeric",
                }
            )
            continue

        drift = abs(expected - actual)
        max_abs_drift = max(max_abs_drift, drift)
        if drift > LOW_FIDELITY_TOLERANCE:
            drift_fields[key] = {
                "expected": expected,
                "actual": actual,
                "abs_drift": drift,
            }
            mismatches.append(
                {
                    "field": key,
                    "expected": expected,
                    "actual": actual,
                    "abs_drift": drift,
                }
            )

    for key in exact_keys:
        if key not in stored:
            missing_fields.append(key)
            continue

        expected = stored.get(key)
        actual = current.get(key)
        if expected != actual:
            mismatches.append(
                {
                    "field": key,
                    "expected": expected,
                    "actual": actual,
                    "reason": "exact-mismatch",
                }
            )

    return (
        not missing_fields and not mismatches,
        {
            "missing_fields": missing_fields,
            "drift_fields": drift_fields,
            "mismatches": mismatches,
            "max_abs_drift": max_abs_drift,
        },
    )


def _pair_fixture(path: Path) -> FixturePairResult:
    data = _load_fixture(path)
    params = LowDimBoundaryParams.model_validate(data["params"])
    boundary = build_boundary_from_params(params, n_field_periods=N_FIELD_PERIODS)

    low = evaluate_boundary(boundary, fidelity="low")
    high = evaluate_boundary(boundary, fidelity="high")

    low_payload = _metrics_payload(low)
    high_payload = _metrics_payload(high)
    low_snapshot_ok, low_snapshot = _compare_low_snapshot(
        data.get("low_fidelity", {}),
        low_payload,
    )
    feasible_match = low.constraints_satisfied == high.constraints_satisfied
    ranking_compat = (
        "ambiguous"
        if low.evaluation_failed or high.evaluation_failed
        else "match"
        if feasible_match
        else "mismatch"
    )

    comparison: dict[str, Any] = {
        "low_high_feasibility_match": feasible_match,
        "feasibility_delta": high.p1_feasibility - low.p1_feasibility,
        "score_delta": high.p1_score - low.p1_score,
        "ranking_compatibility": ranking_compat,
        "low_fidelity_stored_p1_score": data.get("low_fidelity", {}).get("p1_score"),
        "low_fidelity_stored_p1_feasibility": data.get("low_fidelity", {}).get("p1_feasibility"),
        "low_fidelity_snapshot": low_snapshot,
    }

    status = "pass"
    if low.evaluation_failed or high.evaluation_failed or not feasible_match or not low_snapshot_ok:
        status = "fail"
        if not low_snapshot_ok:
            print(f"  low-fidelity snapshot mismatch:\n{pformat(low_snapshot)}")

    return FixturePairResult(
        name=str(data.get("name", path.stem)),
        file=str(path),
        status=status,
        low_fidelity=low_payload,
        high_fidelity=high_payload,
        comparison=comparison,
    )


def _write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as file:
        json.dump(payload, file, indent=2)


def _run_fixture_checks(
    *,
    fixture_dir: Path,
    fixture_output: Path,
    write_fixture_updates: bool,
) -> tuple[list[FixturePairResult], int]:
    results: list[FixturePairResult] = []
    fail_count = 0

    for path in _fixture_files(fixture_dir):
        print(f"Evaluating fixture: {path.name}")
        fixture_start = perf_counter()
        result = _pair_fixture(path)
        if result.status != "pass":
            fail_count += 1
        results.append(result)

        if write_fixture_updates:
            fixture = _load_fixture(path)
            fixture["high_fidelity"] = result.high_fidelity
            fixture["paired_high_fidelity_timestamp_utc"] = datetime.now(tz=UTC).isoformat()
            with path.open("w") as file:
                json.dump(fixture, file, indent=2)

        elapsed = perf_counter() - fixture_start
        print(
            "  done in "
            f"{elapsed:0.1f}s | low_feasible={result.low_fidelity['constraints_satisfied']} "
            f"| high_feasible={result.high_fidelity['constraints_satisfied']} "
            f"| status={result.status}"
        )

    pass_count = len(results) - fail_count
    payload = {
        "timestamp_utc": datetime.now(tz=UTC).isoformat(),
        "n_field_periods": N_FIELD_PERIODS,
        "fixture_count": len(results),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "results": [asdict(result) for result in results],
    }
    _write_json(payload, fixture_output)
    return results, fail_count


def _run_submit_trace(
    trace_output: Path,
    *,
    seed: int,
    action_sequence: str,
) -> dict[str, Any]:
    env = StellaratorEnvironment()
    obs = env.reset(seed=seed)
    reset_params = env.state.current_params.model_dump()
    actions = _parse_submit_sequence(action_sequence)

    trace: list[dict[str, Any]] = [
        {
            "step": 0,
            "intent": "reset",
            "action": f"reset(seed={seed})",
            "reward": 0.0,
            "score": obs.p1_score,
            "feasibility": obs.p1_feasibility,
            "feasibility_delta": None,
            "score_delta": None,
            "constraints_satisfied": obs.constraints_satisfied,
            "max_elongation": obs.max_elongation,
            "p1_feasibility": obs.p1_feasibility,
            "budget_remaining": obs.budget_remaining,
            "evaluation_fidelity": obs.evaluation_fidelity,
            "done": obs.done,
            "params": reset_params,
        }
    ]

    previous_feasibility = obs.p1_feasibility
    previous_score = obs.p1_score

    for idx, action in enumerate(actions, start=1):
        obs = env.step(action)
        trace.append(
            asdict(
                TraceStep(
                    step=idx,
                    intent=action.intent,
                    action=(
                        f"{action.parameter} {action.direction} {action.magnitude}"
                        if action.intent == "run"
                        else action.intent
                    ),
                    reward=float(obs.reward or 0.0),
                    score=obs.p1_score,
                    feasibility=obs.p1_feasibility,
                    constraints_satisfied=obs.constraints_satisfied,
                    feasibility_delta=obs.p1_feasibility - previous_feasibility,
                    score_delta=obs.p1_score - previous_score,
                    max_elongation=obs.max_elongation,
                    p1_feasibility=obs.p1_feasibility,
                    budget_remaining=obs.budget_remaining,
                    evaluation_fidelity=obs.evaluation_fidelity,
                    done=obs.done,
                )
            )
        )

        previous_feasibility = obs.p1_feasibility
        previous_score = obs.p1_score
        if obs.done:
            break

    total_reward = sum(step["reward"] for step in trace)
    payload = {
        "trace_label": "submit_side_manual",
        "trace_profile": action_sequence,
        "timestamp_utc": datetime.now(tz=UTC).isoformat(),
        "n_field_periods": N_FIELD_PERIODS,
        "seed": seed,
        "total_reward": total_reward,
        "final_score": obs.p1_score,
        "final_feasibility": obs.p1_feasibility,
        "final_constraints_satisfied": obs.constraints_satisfied,
        "final_evaluation_fidelity": obs.evaluation_fidelity,
        "final_evaluation_failed": obs.evaluation_failed,
        "steps": trace,
        "final_best_low_fidelity_score": obs.best_low_fidelity_score,
        "final_best_low_fidelity_feasibility": obs.best_low_fidelity_feasibility,
        "final_diagnostics_text": obs.diagnostics_text,
    }
    _write_json(payload, trace_output)
    return payload


def main() -> int:
    args = parse_args()
    results, fail_count = _run_fixture_checks(
        fixture_dir=args.fixture_dir,
        fixture_output=args.fixture_output,
        write_fixture_updates=not args.no_write_fixture_updates,
    )

    print(
        f"Paired fixtures: {len(results)} total, {len(results) - fail_count} pass, {fail_count} fail"
    )
    for result in results:
        print(
            f"  - {result.name}: {result.status} "
            f"(low={result.low_fidelity['constraints_satisfied']} "
            f"high={result.high_fidelity['constraints_satisfied']})"
        )

    if not args.skip_submit_trace:
        trace = _run_submit_trace(
            args.trace_output,
            seed=args.seed,
            action_sequence=args.submit_action_sequence,
        )
        print(
            f"Manual submit trace written to {args.trace_output} | "
            f"sequence='{trace['trace_profile']}' | "
            f"final_feasibility={trace['final_feasibility']:.6f} | "
            f"fidelity={trace['final_evaluation_fidelity']}"
        )

    return 1 if fail_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
