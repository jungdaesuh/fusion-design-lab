from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

from server.contract import N_FIELD_PERIODS, SMOKE_TEST_PARAMS
from server.physics import EvaluationMetrics, build_boundary_from_params, evaluate_boundary


DEFAULT_OUTPUT_DIR = Path("training/notebooks/artifacts")


@dataclass(frozen=True)
class SmokeArtifact:
    created_at_utc: str
    constellaration_version: str
    boundary_type: str
    n_field_periods: int
    params: dict[str, float]
    metrics: dict[str, str | float | bool]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the Fusion Design Lab Northflank smoke check: generate one "
            "rotating-ellipse-derived low-dimensional boundary, run one "
            "low-fidelity verifier call, and write a JSON artifact."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=(
            "Directory where the smoke artifact should be written. On Northflank, "
            "point this at the mounted persistent storage path."
        ),
    )
    return parser.parse_args()


def build_artifact() -> SmokeArtifact:
    boundary = build_boundary_from_params(
        SMOKE_TEST_PARAMS,
        n_field_periods=N_FIELD_PERIODS,
    )
    metrics = evaluate_boundary(boundary, fidelity="low")
    return SmokeArtifact(
        created_at_utc=datetime.now(UTC).isoformat(),
        constellaration_version=version("constellaration"),
        boundary_type=type(boundary).__name__,
        n_field_periods=N_FIELD_PERIODS,
        params=SMOKE_TEST_PARAMS.model_dump(),
        metrics=_metrics_payload(metrics),
    )


def write_artifact(output_dir: Path, artifact: SmokeArtifact) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output_path = output_dir / f"northflank_smoke_{timestamp}.json"
    output_path.write_text(json.dumps(asdict(artifact), indent=2, sort_keys=True) + "\n")
    return output_path


def _metrics_payload(metrics: EvaluationMetrics) -> dict[str, str | float | bool]:
    return {
        "evaluation_fidelity": metrics.evaluation_fidelity,
        "evaluation_failed": metrics.evaluation_failed,
        "failure_reason": metrics.failure_reason,
        "max_elongation": metrics.max_elongation,
        "aspect_ratio": metrics.aspect_ratio,
        "average_triangularity": metrics.average_triangularity,
        "edge_iota_over_nfp": metrics.edge_iota_over_nfp,
        "p1_score": metrics.p1_score,
        "p1_feasibility": metrics.p1_feasibility,
        "constraints_satisfied": metrics.constraints_satisfied,
        "vacuum_well": metrics.vacuum_well,
    }


def main() -> None:
    args = parse_args()
    artifact = build_artifact()
    output_path = write_artifact(args.output_dir, artifact)
    print(output_path)


if __name__ == "__main__":
    main()
