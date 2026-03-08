from __future__ import annotations

from typing import Literal

from openenv.core import Action, Observation, State
from pydantic import BaseModel, Field

ActionIntent = Literal["run", "submit", "restore_best"]
ParameterName = Literal["aspect_ratio", "elongation", "rotational_transform"]
DirectionName = Literal["increase", "decrease"]
MagnitudeName = Literal["small", "medium", "large"]


class RotatingEllipseParams(BaseModel):
    aspect_ratio: float
    elongation: float
    rotational_transform: float


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
    step_number: int = 0
    budget_remaining: int = 6
    best_score: float = 0.0
    best_feasibility: float = float("inf")
    constraints_satisfied: bool = True
    target_spec: str = ""


class StellaratorState(State):
    current_params: RotatingEllipseParams = Field(
        default_factory=lambda: RotatingEllipseParams(
            aspect_ratio=3.5,
            elongation=1.5,
            rotational_transform=0.4,
        )
    )
    best_params: RotatingEllipseParams = Field(
        default_factory=lambda: RotatingEllipseParams(
            aspect_ratio=3.5,
            elongation=1.5,
            rotational_transform=0.4,
        )
    )
    initial_score: float = 0.0
    best_score: float = 0.0
    current_feasibility: float = float("inf")
    best_feasibility: float = float("inf")
    budget_total: int = 6
    budget_remaining: int = 6
    episode_done: bool = False
    constraints_satisfied: bool = True
    history: list[str] = Field(default_factory=list)
