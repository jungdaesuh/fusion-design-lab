from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

import numpy as np
from constellaration.forward_model import (
    ConstellarationMetrics,
    ConstellarationSettings,
    forward_model,
)
from constellaration.mhd.vmec_settings import VmecPresetSettings
from constellaration.geometry import surface_rz_fourier
from constellaration.geometry.surface_rz_fourier import SurfaceRZFourier
from constellaration.initial_guess import generate_rotating_ellipse
from constellaration.problems import GeometricalProblem

from fusion_lab.models import ConstraintName, LowDimBoundaryParams

ASPECT_RATIO_MAX: Final[float] = 4.0
AVERAGE_TRIANGULARITY_MAX: Final[float] = -0.5
EDGE_IOTA_OVER_NFP_MIN: Final[float] = 0.3
FEASIBILITY_TOLERANCE: Final[float] = 0.01
MAX_POLOIDAL_MODE: Final[int] = 3
MAX_TOROIDAL_MODE: Final[int] = 3
FAILED_FEASIBILITY: Final[float] = 1_000_000.0
FAILED_ELONGATION: Final[float] = 10.0

EvaluationFidelity = Literal["low", "high"]


@dataclass(frozen=True)
class EvaluationMetrics:
    max_elongation: float
    aspect_ratio: float
    average_triangularity: float
    edge_iota_over_nfp: float
    aspect_ratio_violation: float
    triangularity_violation: float
    iota_violation: float
    dominant_constraint: ConstraintName
    p1_score: float
    p1_feasibility: float
    constraints_satisfied: bool
    vacuum_well: float
    evaluation_fidelity: EvaluationFidelity
    evaluation_failed: bool
    failure_reason: str


def build_boundary_from_params(
    params: LowDimBoundaryParams,
    *,
    n_field_periods: int = 3,
    max_poloidal_mode: int = MAX_POLOIDAL_MODE,
    max_toroidal_mode: int = MAX_TOROIDAL_MODE,
) -> SurfaceRZFourier:
    surface = generate_rotating_ellipse(
        aspect_ratio=params.aspect_ratio,
        elongation=params.elongation,
        rotational_transform=params.rotational_transform,
        n_field_periods=n_field_periods,
    )
    expanded_surface = surface_rz_fourier.set_max_mode_numbers(
        surface,
        max_poloidal_mode=max_poloidal_mode,
        max_toroidal_mode=max_toroidal_mode,
    )
    r_cos = np.asarray(expanded_surface.r_cos, dtype=float).copy()
    z_sin = np.asarray(expanded_surface.z_sin, dtype=float).copy()
    center = r_cos.shape[1] // 2
    minor_radius = float(r_cos[1, center])

    r_cos[2, center] = -params.triangularity_scale * minor_radius
    r_cos[0, :center] = 0.0
    z_sin[0, : center + 1] = 0.0

    return SurfaceRZFourier(
        r_cos=r_cos,
        z_sin=z_sin,
        n_field_periods=n_field_periods,
        is_stellarator_symmetric=True,
    )


def evaluate_boundary(
    boundary: SurfaceRZFourier,
    *,
    fidelity: EvaluationFidelity = "low",
) -> EvaluationMetrics:
    settings = _settings_for_fidelity(fidelity)
    try:
        metrics, _ = forward_model(boundary, settings=settings)
    except RuntimeError as error:
        return _failure_metrics(fidelity=fidelity, failure_reason=str(error))
    return _to_evaluation_metrics(metrics, fidelity=fidelity)


def _settings_for_fidelity(fidelity: EvaluationFidelity) -> ConstellarationSettings:
    if fidelity == "high":
        return ConstellarationSettings(
            vmec_preset_settings=VmecPresetSettings(fidelity="from_boundary_resolution"),
            boozer_preset_settings=None,
            qi_settings=None,
            turbulent_settings=None,
        )
    return ConstellarationSettings(
        boozer_preset_settings=None,
        qi_settings=None,
        turbulent_settings=None,
    )


def _to_evaluation_metrics(
    metrics: ConstellarationMetrics,
    *,
    fidelity: EvaluationFidelity,
) -> EvaluationMetrics:
    problem = GeometricalProblem()
    constraints_satisfied = problem.is_feasible(metrics)
    p1_feasibility = float(problem.compute_feasibility(metrics))
    objective, minimize_objective = problem.get_objective(metrics)
    if not minimize_objective:
        raise ValueError("P1 objective is expected to be minimize-only.")
    p1_score = _score_from_objective(float(objective)) if constraints_satisfied else 0.0
    aspect_ratio_violation, triangularity_violation, iota_violation, dominant_constraint = (
        _constraint_violation_metrics(metrics)
    )

    return EvaluationMetrics(
        max_elongation=float(objective),
        aspect_ratio=float(metrics.aspect_ratio),
        average_triangularity=float(metrics.average_triangularity),
        edge_iota_over_nfp=float(metrics.edge_rotational_transform_over_n_field_periods),
        aspect_ratio_violation=aspect_ratio_violation,
        triangularity_violation=triangularity_violation,
        iota_violation=iota_violation,
        dominant_constraint=dominant_constraint,
        p1_score=p1_score,
        p1_feasibility=p1_feasibility,
        constraints_satisfied=constraints_satisfied,
        vacuum_well=float(metrics.vacuum_well),
        evaluation_fidelity=fidelity,
        evaluation_failed=False,
        failure_reason="",
    )


def _failure_metrics(
    *,
    fidelity: EvaluationFidelity,
    failure_reason: str,
) -> EvaluationMetrics:
    return EvaluationMetrics(
        max_elongation=FAILED_ELONGATION,
        aspect_ratio=0.0,
        average_triangularity=0.0,
        edge_iota_over_nfp=0.0,
        aspect_ratio_violation=0.0,
        triangularity_violation=0.0,
        iota_violation=0.0,
        dominant_constraint="none",
        p1_score=0.0,
        p1_feasibility=FAILED_FEASIBILITY,
        constraints_satisfied=False,
        vacuum_well=0.0,
        evaluation_fidelity=fidelity,
        evaluation_failed=True,
        failure_reason=failure_reason,
    )


def _score_from_objective(objective: float) -> float:
    normalized = min(max((objective - 1.0) / 9.0, 0.0), 1.0)
    return 1.0 - normalized


def _constraint_violation_metrics(
    metrics: ConstellarationMetrics,
) -> tuple[float, float, float, ConstraintName]:
    aspect_ratio_violation = max(float(metrics.aspect_ratio) - ASPECT_RATIO_MAX, 0.0) / (
        ASPECT_RATIO_MAX
    )
    triangularity_violation = max(
        float(metrics.average_triangularity) - AVERAGE_TRIANGULARITY_MAX,
        0.0,
    ) / abs(AVERAGE_TRIANGULARITY_MAX)
    iota_violation = (
        max(
            EDGE_IOTA_OVER_NFP_MIN
            - abs(float(metrics.edge_rotational_transform_over_n_field_periods)),
            0.0,
        )
        / EDGE_IOTA_OVER_NFP_MIN
    )

    dominant_constraint: ConstraintName = "none"
    dominant_violation = 0.0
    constraint_violations: tuple[tuple[ConstraintName, float], ...] = (
        ("aspect_ratio", aspect_ratio_violation),
        ("average_triangularity", triangularity_violation),
        ("edge_iota_over_nfp", iota_violation),
    )
    for constraint_name, violation in constraint_violations:
        if violation > dominant_violation:
            dominant_constraint = constraint_name
            dominant_violation = violation

    return (
        aspect_ratio_violation,
        triangularity_violation,
        iota_violation,
        dominant_constraint,
    )
