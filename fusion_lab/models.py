from __future__ import annotations

from typing import Literal

from openenv.core import Action, Observation, State
from pydantic import Field

ActionIntent = Literal["run", "submit", "restore_best"]
OperatorName = Literal["tune_rc10", "tune_rc11", "tune_zs11", "tune_zs12"]
DirectionName = Literal["increase", "decrease"]
MagnitudeName = Literal["small", "medium", "large"]
RestartMode = Literal["hot", "cold"]


class StellaratorAction(Action):
    intent: ActionIntent
    operator: OperatorName | None = None
    direction: DirectionName | None = None
    magnitude: MagnitudeName | None = None
    restart: RestartMode | None = None
    reasoning: str = ""


class StellaratorObservation(Observation):
    diagnostics_text: str = ""
    quasi_symmetry_residual: float = 0.0
    aspect_ratio: float = 0.0
    rotational_transform_axis: float = 0.0
    rotational_transform_edge: float = 0.0
    magnetic_well_depth: float = 0.0
    volume: float = 0.0
    vmec_converged: bool = True
    step_number: int = 0
    budget_remaining: int = 6
    best_qs_residual: float = float("inf")
    constraints_satisfied: bool = True
    target_spec: str = ""


class StellaratorState(State):
    initial_qs: float = 0.0
    current_qs: float = 0.0
    prev_qs: float = 0.0
    best_qs: float = Field(default=float("inf"))
    budget_total: int = 6
    budget_remaining: int = 6
    constraints_satisfied: bool = True
    history: list[str] = Field(default_factory=list)
