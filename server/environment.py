from __future__ import annotations

from typing import Any, Final, Optional

from openenv.core import Environment as BaseEnvironment

from fusion_lab.models import (
    StellaratorAction,
    StellaratorObservation,
    StellaratorState,
)
from server.physics import Diagnostics, PhysicsEngine

BUDGET: Final[int] = 6

ASPECT_RATIO_RANGE: Final[tuple[float, float]] = (4.5, 7.0)
IOTA_EDGE_RANGE: Final[tuple[float, float]] = (0.3, 0.6)
VOLUME_MIN: Final[float] = 0.5

TARGET_SPEC: Final[str] = (
    "Minimize quasi-symmetry residual for a 2-period quasi-helical stellarator. "
    "Constraints: aspect ratio in [4.5, 7.0], edge iota in [0.3, 0.6], volume > 0.5 m³. "
    "Budget: 6 evaluations."
)


def check_constraints(diag: Diagnostics) -> bool:
    ar_lo, ar_hi = ASPECT_RATIO_RANGE
    iota_lo, iota_hi = IOTA_EDGE_RANGE
    return (
        ar_lo <= diag.aspect_ratio <= ar_hi
        and iota_lo <= diag.iota_edge <= iota_hi
        and diag.volume >= VOLUME_MIN
    )


class StellaratorEnvironment(
    BaseEnvironment[StellaratorAction, StellaratorObservation, StellaratorState]
):
    def __init__(self) -> None:
        super().__init__()
        self._engine = PhysicsEngine()
        self._state = StellaratorState()
        self._last_diag: Diagnostics | None = None

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        **kwargs: Any,
    ) -> StellaratorObservation:
        diag = self._engine.reset(seed)
        satisfied = check_constraints(diag)
        self._state = StellaratorState(
            episode_id=episode_id,
            step_count=0,
            initial_qs=diag.qs_residual,
            current_qs=diag.qs_residual,
            prev_qs=diag.qs_residual,
            best_qs=diag.qs_residual,
            budget_total=BUDGET,
            budget_remaining=BUDGET,
            constraints_satisfied=satisfied,
        )
        self._last_diag = diag
        return self._build_observation(
            diag, satisfied, action_summary="Episode started. Baseline design loaded."
        )

    def step(
        self,
        action: StellaratorAction,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> StellaratorObservation:
        self._state.prev_qs = self._state.current_qs
        self._state.step_count += 1

        if action.intent == "submit":
            return self._handle_submit()
        if action.intent == "restore_best":
            return self._handle_restore()
        return self._handle_run(action)

    @property
    def state(self) -> StellaratorState:
        return self._state

    # ------------------------------------------------------------------
    # Action handlers
    # ------------------------------------------------------------------

    def _handle_run(self, action: StellaratorAction) -> StellaratorObservation:
        if not all([action.operator, action.direction, action.magnitude]):
            return self._handle_invalid_run()

        self._state.budget_remaining -= 1

        diag = self._engine.modify_and_run(
            operator=action.operator,
            direction=action.direction,
            magnitude=action.magnitude,
            restart=action.restart or "hot",
        )

        satisfied = check_constraints(diag) if diag.converged else self._state.constraints_satisfied

        if diag.converged:
            self._state.current_qs = diag.qs_residual
            if diag.qs_residual < self._state.best_qs:
                self._state.best_qs = diag.qs_residual
            self._state.constraints_satisfied = satisfied

        done = self._state.budget_remaining <= 0
        reward = self._compute_reward(diag, action.intent, done)
        summary = self._summary_run(action, diag)
        self._state.history.append(summary)
        self._last_diag = diag

        return self._build_observation(
            diag, satisfied, action_summary=summary, reward=reward, done=done
        )

    def _handle_submit(self) -> StellaratorObservation:
        diag = self._last_diag or self._engine.restore_best()
        satisfied = check_constraints(diag)
        reward = self._compute_reward(diag, "submit", done=True)
        summary = self._summary_submit(satisfied)
        self._state.history.append(summary)

        return self._build_observation(
            diag, satisfied, action_summary=summary, reward=reward, done=True
        )

    def _handle_restore(self) -> StellaratorObservation:
        self._state.budget_remaining -= 1

        diag = self._engine.restore_best()
        self._state.current_qs = diag.qs_residual
        satisfied = check_constraints(diag)
        self._state.constraints_satisfied = satisfied

        done = self._state.budget_remaining <= 0
        reward = self._compute_reward(diag, "restore_best", done)
        summary = f"Restored best design. QS residual: {diag.qs_residual:.6f}."
        self._state.history.append(summary)
        self._last_diag = diag

        return self._build_observation(
            diag, satisfied, action_summary=summary, reward=reward, done=done
        )

    def _handle_invalid_run(self) -> StellaratorObservation:
        self._state.budget_remaining -= 1
        diag = self._last_diag or self._engine.restore_best()
        satisfied = check_constraints(diag)
        done = self._state.budget_remaining <= 0
        summary = "Invalid run action: operator, direction, and magnitude are required."
        self._state.history.append(summary)
        return self._build_observation(
            diag, satisfied, action_summary=summary, reward=-1.0, done=done
        )

    # ------------------------------------------------------------------
    # Reward V0
    # ------------------------------------------------------------------

    def _compute_reward(self, diag: Diagnostics, intent: str, done: bool) -> float:
        reward = 0.0

        if diag.converged and self._state.prev_qs < float("inf"):
            improvement = self._state.prev_qs - diag.qs_residual
            reward += improvement * 500.0

        if diag.converged and not check_constraints(diag):
            reward -= 2.0

        if not diag.converged:
            reward -= 1.5

        if intent != "submit":
            reward -= 0.1

        if intent == "submit":
            if self._state.best_qs < self._state.initial_qs:
                ratio = 1.0 - (self._state.best_qs / max(self._state.initial_qs, 1e-9))
                reward += 5.0 * ratio
                reward += 1.0 * (self._state.budget_remaining / self._state.budget_total)
            else:
                reward -= 1.0

        if done and intent != "submit":
            if self._state.best_qs < self._state.initial_qs:
                ratio = 1.0 - (self._state.best_qs / max(self._state.initial_qs, 1e-9))
                reward += 2.0 * ratio

        return round(reward, 4)

    # ------------------------------------------------------------------
    # Observation builders
    # ------------------------------------------------------------------

    def _build_observation(
        self,
        diag: Diagnostics,
        satisfied: bool,
        action_summary: str,
        reward: float | None = None,
        done: bool = False,
    ) -> StellaratorObservation:
        text_lines = [
            action_summary,
            "",
            f"QS Residual: {diag.qs_residual:.6f}  |  Best: {self._state.best_qs:.6f}",
            f"Aspect Ratio: {diag.aspect_ratio:.4f}  [4.5, 7.0]",
            f"Edge Iota: {diag.iota_edge:.4f}  [0.3, 0.6]",
            f"Volume: {diag.volume:.4f} m³  (min 0.5)",
            f"Magnetic Well: {diag.magnetic_well_depth:.4f}",
            f"VMEC Converged: {diag.converged}",
            f"Constraints: {'SATISFIED' if satisfied else 'VIOLATED'}",
            f"Step: {self._state.step_count}  |  Budget: {self._state.budget_remaining}/{self._state.budget_total}",
        ]

        return StellaratorObservation(
            diagnostics_text="\n".join(text_lines),
            quasi_symmetry_residual=diag.qs_residual,
            aspect_ratio=diag.aspect_ratio,
            rotational_transform_axis=diag.iota_axis,
            rotational_transform_edge=diag.iota_edge,
            magnetic_well_depth=diag.magnetic_well_depth,
            volume=diag.volume,
            vmec_converged=diag.converged,
            step_number=self._state.step_count,
            budget_remaining=self._state.budget_remaining,
            best_qs_residual=self._state.best_qs,
            constraints_satisfied=satisfied,
            target_spec=TARGET_SPEC,
            reward=reward,
            done=done,
        )

    # ------------------------------------------------------------------
    # Action summaries
    # ------------------------------------------------------------------

    def _summary_run(self, action: StellaratorAction, diag: Diagnostics) -> str:
        restart_note = f" ({action.restart} restart)" if action.restart else ""
        header = f"Applied {action.operator} {action.direction} {action.magnitude}{restart_note}."

        if diag.converged:
            delta = self._state.prev_qs - diag.qs_residual
            direction = "improved" if delta > 0 else "worsened" if delta < 0 else "unchanged"
            return f"{header} VMEC converged. QS {direction}: {self._state.prev_qs:.6f} -> {diag.qs_residual:.6f}."
        return f"{header} VMEC failed to converge. Change reverted."

    def _summary_submit(self, satisfied: bool) -> str:
        status = "Constraints satisfied." if satisfied else "Constraints VIOLATED."
        improvement = self._state.initial_qs - self._state.best_qs
        return (
            f"Design submitted. Best QS residual: {self._state.best_qs:.6f} "
            f"(improved by {improvement:.6f} from initial). {status}"
        )
