from __future__ import annotations

from typing import Literal

from openenv.core import Action, Observation, State
from pydantic import BaseModel, Field

ActionIntent = Literal["run", "submit", "restore_best"]
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
    p1_score: float = 0.0
    p1_feasibility: float = 0.0
    vacuum_well: float = 0.0
    evaluation_fidelity: EvaluationFidelityName = "low"
    evaluation_failed: bool = False
    failure_reason: str = ""
    step_number: int = 0
    budget_remaining: int = 6
    best_score: float = 0.0
    best_feasibility: float = float("inf")
    constraints_satisfied: bool = True
    target_spec: str = ""


class StellaratorState(State):
    current_params: LowDimBoundaryParams = Field(
        default_factory=lambda: LowDimBoundaryParams(
            aspect_ratio=3.6,
            elongation=1.4,
            rotational_transform=1.6,
            triangularity_scale=0.55,
        )
    )
    best_params: LowDimBoundaryParams = Field(
        default_factory=lambda: LowDimBoundaryParams(
            aspect_ratio=3.6,
            elongation=1.4,
            rotational_transform=1.6,
            triangularity_scale=0.55,
        )
    )
    initial_score: float = 0.0
    best_score: float = 0.0
    best_feasibility: float = float("inf")
    budget_total: int = 6
    budget_remaining: int = 6
    episode_done: bool = False
    constraints_satisfied: bool = True
    history: list[str] = Field(default_factory=list)
