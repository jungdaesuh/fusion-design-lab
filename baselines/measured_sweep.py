"""Measured sweep over the 4-knob parameter space.

Validates ranges, crash zones, feasibility regions, and identifies
candidate reset seeds for the repaired low-dimensional family.

Usage:
    # Broad evenly spaced grid (default 3 points per parameter)
    uv run python baselines/measured_sweep.py --grid-points 5

    # Targeted sweep around the known feasible zone
    uv run python baselines/measured_sweep.py --targeted
"""

from __future__ import annotations

import argparse
import json
import time
from itertools import product
from pathlib import Path

import numpy as np

from fusion_lab.models import LowDimBoundaryParams
from server.contract import N_FIELD_PERIODS
from server.environment import PARAMETER_DELTAS, PARAMETER_RANGES
from server.physics import build_boundary_from_params, evaluate_boundary

SWEEP_RANGES: dict[str, tuple[float, float]] = PARAMETER_RANGES


def linspace_inclusive(low: float, high: float, n: int) -> list[float]:
    return [round(float(v), 4) for v in np.linspace(low, high, n)]


TARGETED_VALUES: dict[str, list[float]] = {
    "aspect_ratio": [3.4, 3.6, 3.8],
    "elongation": [1.2, 1.4, 1.6],
    "rotational_transform": [1.50, 1.55, 1.60, 1.65, 1.70, 1.75, 1.80],
    "triangularity_scale": [0.55, 0.58, 0.60, 0.62, 0.65],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a measured low-fidelity sweep over the repaired 4-knob family."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--grid-points",
        type=int,
        default=3,
        help="Number of evenly spaced points per parameter range (default: 3).",
    )
    mode.add_argument(
        "--targeted",
        action="store_true",
        help="Use the pre-defined targeted value set around the known feasible zone.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("baselines/sweep_results"),
        help="Directory where the JSON artifact should be written.",
    )
    return parser.parse_args()


def run_sweep(*, grid_points: int, targeted: bool = False) -> tuple[list[dict], float]:
    if targeted:
        grids = TARGETED_VALUES
    else:
        if grid_points < 2:
            raise ValueError("--grid-points must be at least 2.")
        grids = {
            name: linspace_inclusive(lo, hi, grid_points) for name, (lo, hi) in SWEEP_RANGES.items()
        }

    configs = list(
        product(
            grids["aspect_ratio"],
            grids["elongation"],
            grids["rotational_transform"],
            grids["triangularity_scale"],
        )
    )
    total = len(configs)
    print(f"Sweep: {total} configurations, estimated {total * 0.6:.0f}s")

    results: list[dict] = []
    t0 = time.monotonic()

    for i, (ar, elong, rt, ts) in enumerate(configs):
        params = LowDimBoundaryParams(
            aspect_ratio=ar,
            elongation=elong,
            rotational_transform=rt,
            triangularity_scale=ts,
        )
        boundary = build_boundary_from_params(params, n_field_periods=N_FIELD_PERIODS)
        metrics = evaluate_boundary(boundary, fidelity="low")

        results.append(
            {
                "aspect_ratio": ar,
                "elongation": elong,
                "rotational_transform": rt,
                "triangularity_scale": ts,
                "crashed": metrics.evaluation_failed,
                "failure_reason": metrics.failure_reason,
                "feasible": metrics.constraints_satisfied,
                "p1_feasibility": metrics.p1_feasibility,
                "p1_score": metrics.p1_score,
                "max_elongation": metrics.max_elongation,
                "aspect_ratio_out": metrics.aspect_ratio,
                "average_triangularity": metrics.average_triangularity,
                "edge_iota_over_nfp": metrics.edge_iota_over_nfp,
                "vacuum_well": metrics.vacuum_well,
            }
        )

        if (i + 1) % 50 == 0 or i + 1 == total:
            elapsed = time.monotonic() - t0
            rate = (i + 1) / elapsed
            eta = (total - i - 1) / rate
            print(
                f"  [{i + 1}/{total}] "
                f"{elapsed:.1f}s elapsed, {eta:.1f}s remaining, "
                f"{rate:.1f} eval/s"
            )

    total_elapsed = time.monotonic() - t0
    return results, total_elapsed


def analyze(results: list[dict]) -> dict:
    total = len(results)
    crashed = [r for r in results if r["crashed"]]
    evaluated = [r for r in results if not r["crashed"]]
    feasible = [r for r in evaluated if r["feasible"]]

    print(f"\n{'=' * 60}")
    print("SWEEP SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total:     {total}")
    print(f"Evaluated: {len(evaluated)} ({len(evaluated) / total * 100:.1f}%)")
    print(f"Crashed:   {len(crashed)} ({len(crashed) / total * 100:.1f}%)")
    print(f"Feasible:  {len(feasible)} ({len(feasible) / total * 100:.1f}% of evaluated)")

    # Per-parameter breakdown
    for param in ["aspect_ratio", "elongation", "rotational_transform", "triangularity_scale"]:
        print(f"\n--- {param} ---")
        values = sorted(set(r[param] for r in results))
        for v in values:
            subset = [r for r in results if r[param] == v]
            n_crash = sum(1 for r in subset if r["crashed"])
            n_feas = sum(1 for r in subset if not r["crashed"] and r["feasible"])
            n_eval = sum(1 for r in subset if not r["crashed"])
            avg_feas = (
                np.mean([r["p1_feasibility"] for r in subset if not r["crashed"]])
                if n_eval > 0
                else float("nan")
            )
            print(
                f"  {v:.4f}: crash={n_crash}/{len(subset)} "
                f"feasible={n_feas}/{n_eval} "
                f"avg_feasibility={avg_feas:.4f}"
            )

    # Top feasible results
    if feasible:
        print("\n--- TOP FEASIBLE (by score) ---")
        by_score = sorted(feasible, key=lambda r: r["p1_score"], reverse=True)
        for r in by_score[:10]:
            print(
                f"  AR={r['aspect_ratio']:.2f} elong={r['elongation']:.2f} "
                f"rt={r['rotational_transform']:.2f} ts={r['triangularity_scale']:.2f} | "
                f"score={r['p1_score']:.6f} feas={r['p1_feasibility']:.6f} "
                f"elong_out={r['max_elongation']:.4f} tri={r['average_triangularity']:.4f}"
            )

    # Candidate reset seeds: near-feasible but not yet feasible
    near_feasible = sorted(
        [r for r in evaluated if not r["feasible"] and r["p1_feasibility"] < 0.5],
        key=lambda r: r["p1_feasibility"],
    )
    print("\n--- CANDIDATE RESET SEEDS (near-feasible, not yet feasible) ---")
    for r in near_feasible[:10]:
        print(
            f"  AR={r['aspect_ratio']:.2f} elong={r['elongation']:.2f} "
            f"rt={r['rotational_transform']:.2f} ts={r['triangularity_scale']:.2f} | "
            f"feas={r['p1_feasibility']:.6f} "
            f"tri={r['average_triangularity']:.4f} iota={r['edge_iota_over_nfp']:.4f}"
        )

    # Delta reachability: from each near-feasible seed, can 6 steps reach feasibility?
    print("\n--- DELTA REACHABILITY ---")
    for param, deltas in PARAMETER_DELTAS.items():
        lo, hi = PARAMETER_RANGES[param]
        span = hi - lo
        max_reach = deltas["large"] * 6
        print(
            f"  {param}: range=[{lo}, {hi}] span={span:.2f} "
            f"max_6_steps={max_reach:.2f} "
            f"coverage={max_reach / span * 100:.0f}%"
        )

    analysis = {
        "total": total,
        "evaluated": len(evaluated),
        "crashed": len(crashed),
        "feasible": len(feasible),
        "crash_rate": len(crashed) / total,
        "feasibility_rate": len(feasible) / max(len(evaluated), 1),
    }
    return analysis


def main() -> None:
    args = parse_args()
    results, elapsed_s = run_sweep(
        grid_points=args.grid_points,
        targeted=args.targeted,
    )

    out_dir = args.output_dir
    out_dir.mkdir(exist_ok=True)
    mode_label = "targeted" if args.targeted else f"grid{args.grid_points}"
    timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out_path = out_dir / f"measured_sweep_{timestamp}.json"

    analysis = analyze(results)

    metadata = {
        "mode": mode_label,
        "timestamp": timestamp,
        "elapsed_seconds": round(elapsed_s, 1),
        "seconds_per_eval": round(elapsed_s / max(len(results), 1), 2),
    }

    with open(out_path, "w") as f:
        json.dump({"metadata": metadata, "analysis": analysis, "results": results}, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
