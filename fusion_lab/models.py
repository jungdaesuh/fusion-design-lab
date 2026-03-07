from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


ActionIntent = Literal["run", "submit", "restore_best"]
OperatorName = Literal["tune_rc10", "tune_rc11", "tune_zs11", "tune_zs12"]
DirectionName = Literal["increase", "decrease"]
MagnitudeName = Literal["small", "medium", "large"]
RestartMode = Literal["hot", "cold"]


class StellaratorAction(BaseModel):
    intent: ActionIntent
    operator: OperatorName | None = None
    direction: DirectionName | None = None
    magnitude: MagnitudeName | None = None
    restart: RestartMode | None = None
    reasoning: str = ""


class StellaratorObservation(BaseModel):
    diagnostics_text: str
    quasi_symmetry_residual: float
    aspect_ratio: float
    rotational_transform_axis: float
    rotational_transform_edge: float
    magnetic_well_depth: float
    volume: float
    vmec_converged: bool
    step_number: int
    budget_remaining: int
    best_qs_residual: float
    constraints_satisfied: bool
    target_spec: str
    reward: float | None = None
    done: bool = False


class StellaratorState(BaseModel):
    step_count: int = 0
    initial_qs: float = 0.0
    current_qs: float = 0.0
    prev_qs: float = 0.0
    best_qs: float = Field(default=float("inf"))
    budget_total: int = 6
    budget_remaining: int = 6
    constraints_satisfied: bool = True
    history: list[str] = Field(default_factory=list)

