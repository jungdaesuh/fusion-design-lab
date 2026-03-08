from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from fusion_lab.models import RotatingEllipseParams

ASPECT_RATIO_MAX: Final[float] = 4.0
AVERAGE_TRIANGULARITY_MAX: Final[float] = -0.5
EDGE_IOTA_OVER_NFP_MIN: Final[float] = 0.3
FEASIBILITY_TOLERANCE: Final[float] = 0.01


@dataclass(frozen=True)
class EvaluationMetrics:
    max_elongation: float
    aspect_ratio: float
    average_triangularity: float
    edge_iota_over_nfp: float
    p1_score: float
    p1_feasibility: float
    constraints_satisfied: bool
    vacuum_well: float


def _normalized_violation(value: float, *, limit: float, direction: str) -> float:
    if direction == "max":
        return max((value - limit) / max(abs(limit), 1e-6), 0.0)
    return max((limit - value) / max(abs(limit), 1e-6), 0.0)


def evaluate_params(params: RotatingEllipseParams) -> EvaluationMetrics:
    aspect_ratio = round(params.aspect_ratio, 4)
    average_triangularity = round(
        -0.2
        - 0.35 * (params.elongation - 1.0)
        - 0.2 * max(0.0, 0.35 - params.rotational_transform),
        4,
    )
    edge_iota_over_nfp = round(
        params.rotational_transform
        - 0.05 * max(0.0, params.aspect_ratio - ASPECT_RATIO_MAX)
        + 0.03 * (params.elongation - 1.5),
        4,
    )
    max_elongation = round(
        params.elongation
        + 0.18 * (params.aspect_ratio - 3.4) ** 2
        + 0.8 * abs(params.rotational_transform - 0.42)
        + 0.2,
        4,
    )
    vacuum_well = round(
        0.03
        + 0.02 * (4.0 - min(params.aspect_ratio, 4.0))
        + 0.015 * (params.rotational_transform - 0.3)
        - 0.01 * abs(params.elongation - 1.7),
        4,
    )

    aspect_ratio_violation = _normalized_violation(
        aspect_ratio,
        limit=ASPECT_RATIO_MAX,
        direction="max",
    )
    triangularity_violation = _normalized_violation(
        average_triangularity,
        limit=AVERAGE_TRIANGULARITY_MAX,
        direction="max",
    )
    iota_violation = _normalized_violation(
        edge_iota_over_nfp,
        limit=EDGE_IOTA_OVER_NFP_MIN,
        direction="min",
    )

    p1_feasibility = round(
        max(aspect_ratio_violation, triangularity_violation, iota_violation),
        6,
    )
    constraints_satisfied = p1_feasibility <= FEASIBILITY_TOLERANCE
    p1_score = (
        round(1.0 - min(max((max_elongation - 1.0) / 9.0, 0.0), 1.0), 6)
        if constraints_satisfied
        else 0.0
    )

    return EvaluationMetrics(
        max_elongation=max_elongation,
        aspect_ratio=aspect_ratio,
        average_triangularity=average_triangularity,
        edge_iota_over_nfp=edge_iota_over_nfp,
        p1_score=p1_score,
        p1_feasibility=p1_feasibility,
        constraints_satisfied=constraints_satisfied,
        vacuum_well=vacuum_well,
    )
