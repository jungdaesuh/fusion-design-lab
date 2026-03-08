from __future__ import annotations

from typing import Literal

from openenv.core import Action, Observation, State
from pydantic import BaseModel, Field

ActionIntent = Literal["run", "submit", "restore_best"]
ConstraintName = Literal[
    "none",
    "aspect_ratio",
    "average_triangularity",
    "edge_iota_over_nfp",
]
ParameterName = Literal[
    "aspect_ratio",
    "elongation",
    "rotational_transform",
    "triangularity_scale",
]
DirectionName = Literal["increase", "decrease"]
MagnitudeName = Literal["small", "medium", "large"]
EvaluationFidelityName = Literal["low", "high"]


class LowDimBoundaryParams(BaseModel):
    aspect_ratio: float
    elongation: float
    rotational_transform: float
    triangularity_scale: float


def default_low_dim_boundary_params() -> LowDimBoundaryParams:
    return LowDimBoundaryParams(
        aspect_ratio=3.6,
        elongation=1.4,
        rotational_transform=1.5,
        triangularity_scale=0.55,
    )


class RewardBreakdown(BaseModel):
    intent: ActionIntent = "run"
    total: float = 0.0
    evaluation_failed: bool = False
    recovered_from_failure: bool = False
    reference_constraints_satisfied: bool = False
    reference_score: float | None = None
    reference_feasibility: float | None = None
    reference_max_elongation: float | None = None
    initial_reference_score: float | None = None
    terminal_score_ratio: float | None = None
    invalid_action_penalty: float = 0.0
    failure_penalty: float = 0.0
    failure_submit_penalty: float = 0.0
    failure_budget_penalty: float = 0.0
    feasibility_crossing_bonus: float = 0.0
    feasibility_regression_penalty: float = 0.0
    feasibility_delta_reward: float = 0.0
    aspect_ratio_repair_reward: float = 0.0
    triangularity_repair_reward: float = 0.0
    iota_repair_reward: float = 0.0
    objective_delta_reward: float = 0.0
    step_cost: float = 0.0
    recovery_bonus: float = 0.0
    terminal_improvement_bonus: float = 0.0
    terminal_budget_bonus: float = 0.0
    terminal_no_improvement_penalty: float = 0.0


def default_reward_breakdown() -> RewardBreakdown:
    return RewardBreakdown()


class ActionMonitor(BaseModel):
    intent: ActionIntent = "run"
    parameter: ParameterName | None = None
    direction: DirectionName | None = None
    magnitude: MagnitudeName | None = None
    params_before: LowDimBoundaryParams = Field(default_factory=default_low_dim_boundary_params)
    params_after: LowDimBoundaryParams = Field(default_factory=default_low_dim_boundary_params)
    clamped: bool = False
    no_op: bool = False
    used_best_params: bool = False


def default_action_monitor() -> ActionMonitor:
    params = default_low_dim_boundary_params()
    return ActionMonitor(params_before=params, params_after=params)


class StellaratorAction(Action):
    intent: ActionIntent
    parameter: ParameterName | None = None
    direction: DirectionName | None = None
    magnitude: MagnitudeName | None = None
    reasoning: str = ""


class StellaratorObservation(Observation):
    diagnostics_text: str = ""
    max_elongation: float = 0.0
    aspect_ratio: float = 0.0
    average_triangularity: float = 0.0
    edge_iota_over_nfp: float = 0.0
    aspect_ratio_violation: float = 0.0
    triangularity_violation: float = 0.0
    iota_violation: float = 0.0
    dominant_constraint: ConstraintName = "none"
    p1_score: float = 0.0
    p1_feasibility: float = 0.0
    vacuum_well: float = 0.0
    evaluation_fidelity: EvaluationFidelityName = "low"
    evaluation_failed: bool = False
    failure_reason: str = ""
    step_number: int = 0
    budget_remaining: int = 6
    best_low_fidelity_score: float = 0.0
    best_low_fidelity_feasibility: float = float("inf")
    best_high_fidelity_score: float | None = None
    best_high_fidelity_feasibility: float | None = None
    constraints_satisfied: bool = True
    target_spec: str = ""
    reward_breakdown: RewardBreakdown = Field(default_factory=default_reward_breakdown)
    action_monitor: ActionMonitor = Field(default_factory=default_action_monitor)
    episode_total_reward: float = 0.0
    trajectory_summary: str = ""


class StellaratorState(State):
    initial_params: LowDimBoundaryParams = Field(default_factory=default_low_dim_boundary_params)
    current_params: LowDimBoundaryParams = Field(default_factory=default_low_dim_boundary_params)
    best_params: LowDimBoundaryParams = Field(default_factory=default_low_dim_boundary_params)
    initial_low_fidelity_score: float = 0.0
    initial_high_fidelity_score: float | None = None
    best_low_fidelity_score: float = 0.0
    best_low_fidelity_feasibility: float = float("inf")
    best_high_fidelity_score: float | None = None
    best_high_fidelity_feasibility: float | None = None
    budget_total: int = 6
    budget_remaining: int = 6
    episode_done: bool = False
    constraints_satisfied: bool = True
    total_reward: float = 0.0
    history: list[str] = Field(default_factory=list)
