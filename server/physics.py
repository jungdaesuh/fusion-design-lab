from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

from constellaration.forward_model import (
    ConstellarationMetrics,
    ConstellarationSettings,
    forward_model,
)
from constellaration.initial_guess import generate_rotating_ellipse
from constellaration.problems import GeometricalProblem

from fusion_lab.models import RotatingEllipseParams

ASPECT_RATIO_MAX: Final[float] = 4.0
AVERAGE_TRIANGULARITY_MAX: Final[float] = -0.5
EDGE_IOTA_OVER_NFP_MIN: Final[float] = 0.3
FEASIBILITY_TOLERANCE: Final[float] = 0.01

EvaluationFidelity = Literal["low", "high"]


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


def evaluate_params(
    params: RotatingEllipseParams,
    *,
    n_field_periods: int = 3,
    fidelity: EvaluationFidelity = "low",
) -> EvaluationMetrics:
    boundary = generate_rotating_ellipse(
        aspect_ratio=params.aspect_ratio,
        elongation=params.elongation,
        rotational_transform=params.rotational_transform,
        n_field_periods=n_field_periods,
    )
    settings = _settings_for_fidelity(fidelity)
    metrics, _ = forward_model(boundary, settings=settings)
    return _to_evaluation_metrics(metrics)


def _settings_for_fidelity(fidelity: EvaluationFidelity) -> ConstellarationSettings:
    if fidelity == "high":
        return ConstellarationSettings(
            vmec_preset_settings=ConstellarationSettings.default_high_fidelity_skip_qi().vmec_preset_settings,
            boozer_preset_settings=None,
            qi_settings=None,
            turbulent_settings=None,
        )
    return ConstellarationSettings(
        boozer_preset_settings=None,
        qi_settings=None,
        turbulent_settings=None,
    )


def _to_evaluation_metrics(metrics: ConstellarationMetrics) -> EvaluationMetrics:
    problem = GeometricalProblem()
    constraints_satisfied = problem.is_feasible(metrics)
    p1_feasibility = float(problem.compute_feasibility(metrics))
    objective, minimize_objective = problem.get_objective(metrics)
    if not minimize_objective:
        raise ValueError("P1 objective is expected to be minimize-only.")
    p1_score = _score_from_objective(float(objective)) if constraints_satisfied else 0.0

    return EvaluationMetrics(
        max_elongation=float(objective),
        aspect_ratio=float(metrics.aspect_ratio),
        average_triangularity=float(metrics.average_triangularity),
        edge_iota_over_nfp=float(metrics.edge_rotational_transform_over_n_field_periods),
        p1_score=p1_score,
        p1_feasibility=p1_feasibility,
        constraints_satisfied=constraints_satisfied,
        vacuum_well=float(metrics.vacuum_well),
    )


def _score_from_objective(objective: float) -> float:
    normalized = min(max((objective - 1.0) / 9.0, 0.0), 1.0)
    return 1.0 - normalized
