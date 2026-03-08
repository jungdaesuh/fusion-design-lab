from __future__ import annotations

from typing import Any, Final, Optional

from openenv.core import Environment as BaseEnvironment

from fusion_lab.models import (
    ActionMonitor,
    ActionIntent,
    LowDimBoundaryParams,
    MagnitudeName,
    RewardBreakdown,
    StellaratorAction,
    StellaratorObservation,
    StellaratorState,
)
from server.contract import N_FIELD_PERIODS, RESET_SEEDS
from server.physics import (
    ASPECT_RATIO_MAX,
    AVERAGE_TRIANGULARITY_MAX,
    EDGE_IOTA_OVER_NFP_MIN,
    FEASIBILITY_TOLERANCE,
    EvaluationMetrics,
    build_boundary_from_params,
    evaluate_boundary,
)

BUDGET: Final[int] = 6

PARAMETER_RANGES: Final[dict[str, tuple[float, float]]] = {
    "aspect_ratio": (3.2, 3.8),
    "elongation": (1.2, 1.8),
    "rotational_transform": (1.2, 1.9),
    "triangularity_scale": (0.4, 0.7),
}

PARAMETER_DELTAS: Final[dict[str, dict[str, float]]] = {
    "aspect_ratio": {"small": 0.05, "medium": 0.1, "large": 0.2},
    "elongation": {"small": 0.05, "medium": 0.1, "large": 0.2},
    "rotational_transform": {"small": 0.05, "medium": 0.1, "large": 0.2},
    "triangularity_scale": {"small": 0.02, "medium": 0.05, "large": 0.1},
}

TARGET_SPEC: Final[str] = (
    "Optimize the P1 benchmark using a custom low-dimensional boundary family derived "
    "from a rotating-ellipse seed. Constraints: aspect ratio <= 4.0, average "
    "triangularity <= -0.5, abs(edge rotational transform / n_field_periods) >= 0.3. "
    "All actions use low-fidelity verification. Submit ends the episode with an explicit "
    "terminal evaluation and reward bonus. Budget: 6 evaluations including submit."
)

FAILURE_PENALTY: Final[float] = -2.0
FEASIBILITY_DELTA_WEIGHT: Final[float] = 2.0
TRIANGULARITY_REPAIR_WEIGHT: Final[float] = 2.0
ASPECT_RATIO_REPAIR_WEIGHT: Final[float] = 1.0
IOTA_REPAIR_WEIGHT: Final[float] = 1.0
BEST_FEASIBILITY_BONUS_WEIGHT: Final[float] = 1.5
BEST_SCORE_BONUS_WEIGHT: Final[float] = 0.75
NEAR_FEASIBILITY_THRESHOLD: Final[float] = 0.02
NEAR_FEASIBILITY_BONUS: Final[float] = 1.0
NO_PROGRESS_STEP_THRESHOLD: Final[int] = 3
NO_PROGRESS_PENALTY: Final[float] = -0.2
REPEAT_STATE_PENALTY: Final[float] = -0.15
STEP_COST_BY_MAGNITUDE: Final[dict[MagnitudeName, float]] = {
    "small": -0.05,
    "medium": -0.1,
    "large": -0.2,
}
RESTORE_STEP_COST: Final[float] = -0.1


class StellaratorEnvironment(
    BaseEnvironment[StellaratorAction, StellaratorObservation, StellaratorState]
):
    def __init__(self) -> None:
        super().__init__()
        self._state = StellaratorState()
        self._last_metrics: EvaluationMetrics | None = None
        self._last_successful_metrics: EvaluationMetrics | None = None

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        **kwargs: Any,
    ) -> StellaratorObservation:
        params = self._initial_params(seed)
        metrics = self._evaluate_params(params, fidelity="low")
        self._state = StellaratorState(
            episode_id=episode_id,
            step_count=0,
            initial_params=params,
            current_params=params,
            best_params=params,
            initial_low_fidelity_score=metrics.p1_score,
            best_low_fidelity_score=metrics.p1_score,
            best_low_fidelity_feasibility=metrics.p1_feasibility,
            budget_total=BUDGET,
            budget_remaining=BUDGET,
            episode_done=False,
            constraints_satisfied=metrics.constraints_satisfied,
            total_reward=0.0,
        )
        self._state.visited_state_keys = [self._state_key(params)]
        self._last_metrics = metrics
        self._last_successful_metrics = None if metrics.evaluation_failed else metrics
        return self._build_observation(
            metrics,
            action_summary="Episode started from a frozen low-dimensional seed.",
            reward_breakdown=RewardBreakdown(intent="run"),
            action_monitor=self._action_monitor_for_no_op(StellaratorAction(intent="run")),
        )

    def step(
        self,
        action: StellaratorAction,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> StellaratorObservation:
        if self._state.episode_done or self._state.budget_remaining <= 0:
            metrics = self._last_metrics or self._evaluate_params(
                self._state.current_params,
                fidelity="low",
            )
            reward_breakdown = RewardBreakdown(intent=action.intent)
            return self._build_observation(
                metrics,
                action_summary="Episode already ended. Call reset() before sending more actions.",
                reward=0.0,
                reward_breakdown=reward_breakdown,
                action_monitor=self._action_monitor_for_no_op(action),
                done=True,
            )

        self._state.step_count += 1

        if action.intent == "submit":
            return self._handle_submit()
        if action.intent == "restore_best":
            return self._handle_restore()
        return self._handle_run(action)

    @property
    def state(self) -> StellaratorState:
        return self._state

    def _handle_run(self, action: StellaratorAction) -> StellaratorObservation:
        if not all([action.parameter, action.direction, action.magnitude]):
            return self._handle_invalid_run()

        self._state.budget_remaining -= 1
        params_before = self._state.current_params
        params, clamped, no_op = self._apply_action(
            params=self._state.current_params,
            parameter=action.parameter,
            direction=action.direction,
            magnitude=action.magnitude,
        )
        repeat_state = self._is_repeat_state(params)
        action_monitor = self._build_action_monitor(
            action=action,
            params_before=params_before,
            params_after=params,
            clamped=clamped,
            no_op=no_op,
            repeat_state=repeat_state,
        )
        metrics = self._evaluate_params(params, fidelity="low")
        self._state.current_params = params
        self._state.constraints_satisfied = metrics.constraints_satisfied
        (
            best_low_fidelity_feasibility_before,
            best_low_fidelity_score_before,
            step_improved,
            no_progress_steps,
        ) = self._advance_low_fidelity_progress(params, metrics)

        done = self._state.budget_remaining <= 0
        reward_breakdown = self._compute_reward_breakdown(
            metrics,
            action.intent,
            done,
            magnitude=action.magnitude,
            best_low_fidelity_feasibility_before=best_low_fidelity_feasibility_before,
            best_low_fidelity_score_before=best_low_fidelity_score_before,
            step_improved=step_improved,
            no_progress_steps=no_progress_steps,
            repeat_state=repeat_state,
        )
        reward = reward_breakdown.total
        summary = self._summary_run(action, metrics, action_monitor)
        self._state.history.append(summary)
        self._state.total_reward = round(self._state.total_reward + reward, 4)
        self._last_metrics = metrics
        if not metrics.evaluation_failed:
            self._last_successful_metrics = metrics
        self._state.episode_done = done

        return self._build_observation(
            metrics,
            action_summary=summary,
            reward=reward,
            reward_breakdown=reward_breakdown,
            action_monitor=action_monitor,
            done=done,
        )

    def _handle_submit(self) -> StellaratorObservation:
        self._state.budget_remaining -= 1
        action = StellaratorAction(intent="submit")
        action_monitor = self._build_action_monitor(
            action=action,
            params_before=self._state.current_params,
            params_after=self._state.current_params,
        )
        metrics = self._evaluate_params(self._state.current_params, fidelity="low")
        self._state.constraints_satisfied = metrics.constraints_satisfied
        reward_breakdown = self._compute_reward_breakdown(
            metrics,
            "submit",
            done=True,
        )
        reward = reward_breakdown.total
        summary = self._summary_submit(metrics)
        self._state.history.append(summary)
        self._state.total_reward = round(self._state.total_reward + reward, 4)
        self._state.episode_done = True
        self._last_metrics = metrics
        if not metrics.evaluation_failed:
            self._last_successful_metrics = metrics

        return self._build_observation(
            metrics,
            action_summary=summary,
            reward=reward,
            reward_breakdown=reward_breakdown,
            action_monitor=action_monitor,
            done=True,
        )

    def _handle_restore(self) -> StellaratorObservation:
        self._state.budget_remaining -= 1
        params_before = self._state.current_params
        self._state.current_params = self._state.best_params
        repeat_state = self._is_repeat_state(self._state.current_params)
        action = StellaratorAction(intent="restore_best")
        action_monitor = self._build_action_monitor(
            action=action,
            params_before=params_before,
            params_after=self._state.current_params,
            no_op=params_before == self._state.current_params,
            repeat_state=repeat_state,
            used_best_params=True,
        )
        metrics = self._evaluate_params(self._state.current_params, fidelity="low")
        self._state.constraints_satisfied = metrics.constraints_satisfied
        (
            best_low_fidelity_feasibility_before,
            best_low_fidelity_score_before,
            step_improved,
            no_progress_steps,
        ) = self._advance_low_fidelity_progress(self._state.current_params, metrics)

        done = self._state.budget_remaining <= 0
        reward_breakdown = self._compute_reward_breakdown(
            metrics,
            "restore_best",
            done,
            best_low_fidelity_feasibility_before=best_low_fidelity_feasibility_before,
            best_low_fidelity_score_before=best_low_fidelity_score_before,
            step_improved=step_improved,
            no_progress_steps=no_progress_steps,
            repeat_state=repeat_state,
        )
        reward = reward_breakdown.total
        summary = self._summary_restore(metrics, action_monitor)
        self._state.history.append(summary)
        self._state.total_reward = round(self._state.total_reward + reward, 4)
        self._last_metrics = metrics
        if not metrics.evaluation_failed:
            self._last_successful_metrics = metrics
        self._state.episode_done = done

        return self._build_observation(
            metrics,
            action_summary=summary,
            reward=reward,
            reward_breakdown=reward_breakdown,
            action_monitor=action_monitor,
            done=done,
        )

    def _handle_invalid_run(self) -> StellaratorObservation:
        self._state.budget_remaining -= 1
        metrics = self._last_metrics or self._evaluate_params(
            self._state.current_params,
            fidelity="low",
        )
        done = self._state.budget_remaining <= 0
        summary = "Invalid run action: parameter, direction, and magnitude are required."
        self._state.history.append(summary)
        reward_breakdown = RewardBreakdown(intent="run", invalid_action_penalty=-1.0, total=-1.0)
        action_monitor = self._action_monitor_for_no_op(StellaratorAction(intent="run"))
        self._state.total_reward = round(self._state.total_reward - 1.0, 4)
        self._state.episode_done = done
        return self._build_observation(
            metrics,
            action_summary=summary,
            reward=-1.0,
            reward_breakdown=reward_breakdown,
            action_monitor=action_monitor,
            done=done,
        )

    def _compute_reward_breakdown(
        self,
        metrics: EvaluationMetrics,
        intent: ActionIntent,
        done: bool,
        magnitude: MagnitudeName | None = None,
        initial_reference_score: float | None = None,
        reference_metrics: EvaluationMetrics | None = None,
        best_low_fidelity_feasibility_before: float | None = None,
        best_low_fidelity_score_before: float | None = None,
        step_improved: bool = False,
        no_progress_steps: int = 0,
        repeat_state: bool = False,
    ) -> RewardBreakdown:
        recovered_from_failure = self._recovered_from_failed_evaluation(metrics)
        previous_metrics = reference_metrics or self._reference_metrics(metrics)
        best_low_fidelity_feasibility_before = (
            self._state.best_low_fidelity_feasibility
            if best_low_fidelity_feasibility_before is None
            else best_low_fidelity_feasibility_before
        )
        best_low_fidelity_score_before = (
            self._state.best_low_fidelity_score
            if best_low_fidelity_score_before is None
            else best_low_fidelity_score_before
        )
        breakdown = RewardBreakdown(
            intent=intent,
            evaluation_failed=metrics.evaluation_failed,
            recovered_from_failure=recovered_from_failure,
            reference_constraints_satisfied=previous_metrics.constraints_satisfied,
            reference_score=previous_metrics.p1_score,
            reference_feasibility=previous_metrics.p1_feasibility,
            reference_max_elongation=previous_metrics.max_elongation,
            initial_reference_score=initial_reference_score,
        )
        self._apply_step_penalties(
            breakdown,
            intent=intent,
            magnitude=magnitude,
            no_progress_steps=no_progress_steps,
            repeat_state=repeat_state,
            step_improved=step_improved,
        )

        if metrics.evaluation_failed:
            breakdown.failure_penalty = FAILURE_PENALTY
            if intent == "submit":
                breakdown.failure_submit_penalty = -1.0
            elif done:
                breakdown.failure_budget_penalty = -0.5
            breakdown.total = self._reward_total(breakdown)
            return breakdown

        if metrics.constraints_satisfied and not previous_metrics.constraints_satisfied:
            breakdown.feasibility_crossing_bonus = 3.0
        if previous_metrics.constraints_satisfied and not metrics.constraints_satisfied:
            breakdown.feasibility_regression_penalty = -3.0

        if (
            previous_metrics.p1_feasibility > NEAR_FEASIBILITY_THRESHOLD
            and metrics.p1_feasibility <= NEAR_FEASIBILITY_THRESHOLD
        ):
            breakdown.near_feasible_bonus = NEAR_FEASIBILITY_BONUS

        if metrics.constraints_satisfied and previous_metrics.constraints_satisfied:
            breakdown.objective_delta_reward = (
                previous_metrics.max_elongation - metrics.max_elongation
            ) * 10.0
            if intent != "submit" and best_low_fidelity_feasibility_before <= FEASIBILITY_TOLERANCE:
                breakdown.best_score_bonus = (
                    max(
                        0.0,
                        metrics.p1_score - best_low_fidelity_score_before,
                    )
                    * BEST_SCORE_BONUS_WEIGHT
                )
        else:
            breakdown.feasibility_delta_reward = (
                previous_metrics.p1_feasibility - metrics.p1_feasibility
            ) * FEASIBILITY_DELTA_WEIGHT
            if (
                intent != "submit"
                and not metrics.constraints_satisfied
                and best_low_fidelity_feasibility_before > FEASIBILITY_TOLERANCE
            ):
                breakdown.best_feasibility_bonus = (
                    max(
                        0.0,
                        best_low_fidelity_feasibility_before - metrics.p1_feasibility,
                    )
                    * BEST_FEASIBILITY_BONUS_WEIGHT
                )
            breakdown.triangularity_repair_reward = (
                previous_metrics.triangularity_violation - metrics.triangularity_violation
            ) * TRIANGULARITY_REPAIR_WEIGHT
            breakdown.aspect_ratio_repair_reward = (
                previous_metrics.aspect_ratio_violation - metrics.aspect_ratio_violation
            ) * ASPECT_RATIO_REPAIR_WEIGHT
            breakdown.iota_repair_reward = (
                previous_metrics.iota_violation - metrics.iota_violation
            ) * IOTA_REPAIR_WEIGHT

        if recovered_from_failure:
            breakdown.recovery_bonus = 1.0

        if intent == "submit" or done:
            base_score = (
                initial_reference_score
                if initial_reference_score is not None
                else self._state.initial_low_fidelity_score
            )
            breakdown.initial_reference_score = base_score
            improved = metrics.constraints_satisfied and metrics.p1_score > base_score
            if improved:
                ratio = (metrics.p1_score - base_score) / max(1.0 - base_score, 1e-6)
                breakdown.terminal_score_ratio = ratio
                if intent == "submit":
                    breakdown.terminal_improvement_bonus = 5.0 * ratio
                    breakdown.terminal_budget_bonus = (
                        self._state.budget_remaining / self._state.budget_total
                    )
                else:
                    breakdown.terminal_improvement_bonus = 2.0 * ratio
            else:
                breakdown.terminal_no_improvement_penalty = -1.0 if intent == "submit" else -0.5

        breakdown.total = self._reward_total(breakdown)
        return breakdown

    def _build_observation(
        self,
        metrics: EvaluationMetrics,
        action_summary: str,
        reward: float | None = None,
        reward_breakdown: RewardBreakdown | None = None,
        action_monitor: ActionMonitor | None = None,
        done: bool = False,
    ) -> StellaratorObservation:
        reward_breakdown = reward_breakdown or RewardBreakdown()
        action_monitor = action_monitor or self._action_monitor_for_no_op(
            StellaratorAction(intent="run")
        )
        best_low_fidelity_score = self._state.best_low_fidelity_score
        best_low_fidelity_feasibility = self._state.best_low_fidelity_feasibility
        trajectory_summary = self._trajectory_summary()
        text_lines = [
            action_summary,
            "",
            f"evaluation_fidelity={metrics.evaluation_fidelity}",
            f"evaluation_status={'FAILED' if metrics.evaluation_failed else 'OK'}",
        ]
        if metrics.evaluation_failed:
            text_lines.append(f"failure_reason={metrics.failure_reason}")
        text_lines.extend(
            [
                f"max_elongation={metrics.max_elongation:.4f}",
                f"aspect_ratio={metrics.aspect_ratio:.4f}  (<= {ASPECT_RATIO_MAX:.1f})",
                f"average_triangularity={metrics.average_triangularity:.4f}  (<= {AVERAGE_TRIANGULARITY_MAX:.1f})",
                (
                    "edge_iota_over_nfp="
                    f"{metrics.edge_iota_over_nfp:.4f}  (abs(.) >= {EDGE_IOTA_OVER_NFP_MIN:.1f})"
                ),
                f"feasibility={metrics.p1_feasibility:.6f}",
                f"aspect_ratio_violation={metrics.aspect_ratio_violation:.6f}",
                f"triangularity_violation={metrics.triangularity_violation:.6f}",
                f"iota_violation={metrics.iota_violation:.6f}",
                f"dominant_constraint={metrics.dominant_constraint}",
                f"best_low_fidelity_score={best_low_fidelity_score:.6f}",
                f"best_low_fidelity_feasibility={best_low_fidelity_feasibility:.6f}",
                f"no_progress_steps={self._state.no_progress_steps}",
                f"vacuum_well={metrics.vacuum_well:.4f}",
                f"constraints={'SATISFIED' if metrics.constraints_satisfied else 'VIOLATED'}",
                f"step={self._state.step_count}  |  budget={self._state.budget_remaining}/{self._state.budget_total}",
                f"reward_total={reward_breakdown.total:+.4f}",
                f"reward_terms={self._reward_terms_text(reward_breakdown)}",
                f"action_clamped={action_monitor.clamped}",
                f"action_no_op={action_monitor.no_op}",
                f"action_repeat_state={action_monitor.repeat_state}",
                f"episode_total_reward={self._state.total_reward:+.4f}",
            ]
        )

        return StellaratorObservation(
            diagnostics_text="\n".join(text_lines),
            max_elongation=metrics.max_elongation,
            aspect_ratio=metrics.aspect_ratio,
            average_triangularity=metrics.average_triangularity,
            edge_iota_over_nfp=metrics.edge_iota_over_nfp,
            aspect_ratio_violation=metrics.aspect_ratio_violation,
            triangularity_violation=metrics.triangularity_violation,
            iota_violation=metrics.iota_violation,
            dominant_constraint=metrics.dominant_constraint,
            p1_score=metrics.p1_score,
            p1_feasibility=metrics.p1_feasibility,
            vacuum_well=metrics.vacuum_well,
            evaluation_fidelity=metrics.evaluation_fidelity,
            evaluation_failed=metrics.evaluation_failed,
            failure_reason=metrics.failure_reason,
            step_number=self._state.step_count,
            budget_remaining=self._state.budget_remaining,
            no_progress_steps=self._state.no_progress_steps,
            best_low_fidelity_score=best_low_fidelity_score,
            best_low_fidelity_feasibility=best_low_fidelity_feasibility,
            constraints_satisfied=metrics.constraints_satisfied,
            target_spec=TARGET_SPEC,
            reward=reward,
            reward_breakdown=reward_breakdown,
            action_monitor=action_monitor,
            episode_total_reward=self._state.total_reward,
            trajectory_summary=trajectory_summary,
            done=done,
        )

    def _summary_run(
        self,
        action: StellaratorAction,
        metrics: EvaluationMetrics,
        action_monitor: ActionMonitor,
    ) -> str:
        assert action.parameter is not None
        assert action.direction is not None
        assert action.magnitude is not None
        action_note = self._action_monitor_note(action_monitor)
        if metrics.evaluation_failed:
            return (
                f"Applied {action.parameter} {action.direction} {action.magnitude}. "
                f"{action_note}"
                f"Low-fidelity evaluation failed: {metrics.failure_reason}"
            )

        if self._recovered_from_failed_evaluation(metrics):
            return (
                f"Applied {action.parameter} {action.direction} {action.magnitude}. "
                f"{action_note}"
                "Low-fidelity evaluation recovered from the previous failed evaluation. "
                f"feasibility={metrics.p1_feasibility:.6f}."
            )

        previous_metrics = self._reference_metrics(metrics)
        if metrics.constraints_satisfied and previous_metrics.constraints_satisfied:
            delta = previous_metrics.max_elongation - metrics.max_elongation
            objective_summary = (
                f"max_elongation changed by {delta:+.4f} to {metrics.max_elongation:.4f}."
            )
        else:
            delta = previous_metrics.p1_feasibility - metrics.p1_feasibility
            objective_summary = (
                f"feasibility changed by {delta:+.6f} to {metrics.p1_feasibility:.6f}; "
                f"dominant_constraint={metrics.dominant_constraint}."
            )
        return (
            f"Applied {action.parameter} {action.direction} {action.magnitude}. "
            f"{action_note}"
            f"Low-fidelity evaluation. {objective_summary}"
        )

    def _summary_submit(
        self,
        metrics: EvaluationMetrics,
    ) -> str:
        if metrics.evaluation_failed:
            return f"Submit failed during low-fidelity evaluation: {metrics.failure_reason}"
        return (
            f"Submitted current_score={metrics.p1_score:.6f}, "
            f"best_score={self._state.best_low_fidelity_score:.6f}, "
            f"best_feasibility={self._state.best_low_fidelity_feasibility:.6f}, "
            f"constraints={'SATISFIED' if metrics.constraints_satisfied else 'VIOLATED'}."
        )

    def _summary_restore(self, metrics: EvaluationMetrics, action_monitor: ActionMonitor) -> str:
        action_note = self._action_monitor_note(action_monitor)
        if metrics.evaluation_failed:
            return (
                f"Restore-best failed during low-fidelity evaluation: {metrics.failure_reason}. "
                f"{action_note}"
            )
        return (
            "Restored the best-known design. "
            f"{action_note}"
            f"Low-fidelity score={metrics.p1_score:.6f}, feasibility={metrics.p1_feasibility:.6f}."
        )

    def _initial_params(self, seed: int | None) -> LowDimBoundaryParams:
        if seed is None:
            return RESET_SEEDS[0]
        return RESET_SEEDS[seed % len(RESET_SEEDS)]

    def _apply_action(
        self,
        params: LowDimBoundaryParams,
        parameter: str,
        direction: str,
        magnitude: str,
    ) -> tuple[LowDimBoundaryParams, bool, bool]:
        delta = PARAMETER_DELTAS[parameter][magnitude]
        signed_delta = delta if direction == "increase" else -delta

        current_value = getattr(params, parameter)
        requested_value = current_value + signed_delta
        next_value = self._clamp(
            requested_value,
            parameter=parameter,
        )
        next_values = params.model_dump()
        next_values[parameter] = next_value
        clamped = next_value != requested_value
        no_op = next_value == current_value
        return LowDimBoundaryParams.model_validate(next_values), clamped, no_op

    def _clamp(self, value: float, *, parameter: str) -> float:
        lower, upper = PARAMETER_RANGES[parameter]
        return min(max(value, lower), upper)

    def _evaluate_params(
        self,
        params: LowDimBoundaryParams,
        *,
        fidelity: str,
    ) -> EvaluationMetrics:
        boundary = build_boundary_from_params(
            params,
            n_field_periods=N_FIELD_PERIODS,
        )
        return evaluate_boundary(boundary, fidelity=fidelity)

    def _reference_metrics(self, fallback: EvaluationMetrics) -> EvaluationMetrics:
        if self._last_metrics is not None and not self._last_metrics.evaluation_failed:
            return self._last_metrics
        if self._last_successful_metrics is not None:
            return self._last_successful_metrics
        return fallback

    def _best_low_fidelity_snapshot(self) -> tuple[float, float]:
        return (
            self._state.best_low_fidelity_feasibility,
            self._state.best_low_fidelity_score,
        )

    def _advance_low_fidelity_progress(
        self,
        params: LowDimBoundaryParams,
        metrics: EvaluationMetrics,
    ) -> tuple[float, float, bool, int]:
        best_low_fidelity_feasibility_before, best_low_fidelity_score_before = (
            self._best_low_fidelity_snapshot()
        )
        step_improved = self._is_better_than_reference(
            metrics,
            self._previous_step_metrics(metrics),
        )
        self._update_best(params, metrics)
        no_progress_steps = self._advance_no_progress(step_improved=step_improved)
        self._record_visited_state(params)
        return (
            best_low_fidelity_feasibility_before,
            best_low_fidelity_score_before,
            step_improved,
            no_progress_steps,
        )

    def _previous_step_metrics(self, fallback: EvaluationMetrics) -> EvaluationMetrics:
        if self._last_metrics is not None:
            return self._last_metrics
        return fallback

    def _recovered_from_failed_evaluation(self, metrics: EvaluationMetrics) -> bool:
        return (
            not metrics.evaluation_failed
            and self._last_metrics is not None
            and self._last_metrics.evaluation_failed
        )

    def _build_action_monitor(
        self,
        *,
        action: StellaratorAction,
        params_before: LowDimBoundaryParams,
        params_after: LowDimBoundaryParams,
        clamped: bool = False,
        no_op: bool = False,
        repeat_state: bool = False,
        used_best_params: bool = False,
    ) -> ActionMonitor:
        return ActionMonitor(
            intent=action.intent,
            parameter=action.parameter,
            direction=action.direction,
            magnitude=action.magnitude,
            params_before=params_before,
            params_after=params_after,
            clamped=clamped,
            no_op=no_op,
            repeat_state=repeat_state,
            used_best_params=used_best_params,
        )

    def _action_monitor_for_no_op(self, action: StellaratorAction) -> ActionMonitor:
        params = self._state.current_params
        return self._build_action_monitor(
            action=action,
            params_before=params,
            params_after=params,
            no_op=True,
        )

    def _action_monitor_note(self, action_monitor: ActionMonitor) -> str:
        if action_monitor.used_best_params and action_monitor.no_op:
            return "Already at the best-known design. "
        if action_monitor.no_op:
            return "The requested move hit a parameter bound and produced no state change. "
        if action_monitor.clamped:
            return "The requested move was clipped to stay inside the allowed parameter range. "
        return ""

    def _apply_step_penalties(
        self,
        breakdown: RewardBreakdown,
        *,
        intent: ActionIntent,
        magnitude: MagnitudeName | None,
        no_progress_steps: int,
        repeat_state: bool,
        step_improved: bool,
    ) -> None:
        if intent == "submit":
            return
        breakdown.step_cost = self._step_cost(intent=intent, magnitude=magnitude)
        if intent == "run" and no_progress_steps >= NO_PROGRESS_STEP_THRESHOLD:
            breakdown.no_progress_penalty = NO_PROGRESS_PENALTY
        if intent == "run" and repeat_state and not step_improved:
            breakdown.repeat_state_penalty = REPEAT_STATE_PENALTY

    def _step_cost(self, *, intent: ActionIntent, magnitude: MagnitudeName | None) -> float:
        if intent == "restore_best":
            return RESTORE_STEP_COST
        if magnitude is None:
            return STEP_COST_BY_MAGNITUDE["medium"]
        return STEP_COST_BY_MAGNITUDE[magnitude]

    def _reward_total(self, breakdown: RewardBreakdown) -> float:
        total = (
            breakdown.invalid_action_penalty
            + breakdown.failure_penalty
            + breakdown.failure_submit_penalty
            + breakdown.failure_budget_penalty
            + breakdown.feasibility_crossing_bonus
            + breakdown.feasibility_regression_penalty
            + breakdown.feasibility_delta_reward
            + breakdown.best_feasibility_bonus
            + breakdown.near_feasible_bonus
            + breakdown.aspect_ratio_repair_reward
            + breakdown.triangularity_repair_reward
            + breakdown.iota_repair_reward
            + breakdown.objective_delta_reward
            + breakdown.best_score_bonus
            + breakdown.step_cost
            + breakdown.no_progress_penalty
            + breakdown.repeat_state_penalty
            + breakdown.recovery_bonus
            + breakdown.terminal_improvement_bonus
            + breakdown.terminal_budget_bonus
            + breakdown.terminal_no_improvement_penalty
        )
        return round(total, 4)

    def _reward_terms_text(self, breakdown: RewardBreakdown) -> str:
        terms = [
            ("invalid_action_penalty", breakdown.invalid_action_penalty),
            ("failure_penalty", breakdown.failure_penalty),
            ("failure_submit_penalty", breakdown.failure_submit_penalty),
            ("failure_budget_penalty", breakdown.failure_budget_penalty),
            ("feasibility_crossing_bonus", breakdown.feasibility_crossing_bonus),
            ("feasibility_regression_penalty", breakdown.feasibility_regression_penalty),
            ("feasibility_delta_reward", breakdown.feasibility_delta_reward),
            ("best_feasibility_bonus", breakdown.best_feasibility_bonus),
            ("near_feasible_bonus", breakdown.near_feasible_bonus),
            ("aspect_ratio_repair_reward", breakdown.aspect_ratio_repair_reward),
            ("triangularity_repair_reward", breakdown.triangularity_repair_reward),
            ("iota_repair_reward", breakdown.iota_repair_reward),
            ("objective_delta_reward", breakdown.objective_delta_reward),
            ("best_score_bonus", breakdown.best_score_bonus),
            ("step_cost", breakdown.step_cost),
            ("no_progress_penalty", breakdown.no_progress_penalty),
            ("repeat_state_penalty", breakdown.repeat_state_penalty),
            ("recovery_bonus", breakdown.recovery_bonus),
            ("terminal_improvement_bonus", breakdown.terminal_improvement_bonus),
            ("terminal_budget_bonus", breakdown.terminal_budget_bonus),
            ("terminal_no_improvement_penalty", breakdown.terminal_no_improvement_penalty),
        ]
        non_zero_terms = [f"{name}={value:+.4f}" for name, value in terms if value != 0.0]
        if not non_zero_terms:
            return "none"
        return ", ".join(non_zero_terms)

    def _trajectory_summary(self) -> str:
        if not self._state.history:
            return "No actions taken yet."
        return " | ".join(self._state.history)

    def _update_best(self, params: LowDimBoundaryParams, metrics: EvaluationMetrics) -> None:
        if metrics.evaluation_failed:
            return

        if self._is_better_than_best(
            metrics,
            best_low_fidelity_feasibility=self._state.best_low_fidelity_feasibility,
            best_low_fidelity_score=self._state.best_low_fidelity_score,
        ):
            self._state.best_params = params
            self._state.best_low_fidelity_score = metrics.p1_score
            self._state.best_low_fidelity_feasibility = metrics.p1_feasibility

    def _is_better_than_best(
        self,
        metrics: EvaluationMetrics,
        *,
        best_low_fidelity_feasibility: float,
        best_low_fidelity_score: float,
    ) -> bool:
        current = (
            (1, metrics.p1_score) if metrics.constraints_satisfied else (0, -metrics.p1_feasibility)
        )
        best = (
            (1, best_low_fidelity_score)
            if best_low_fidelity_feasibility <= FEASIBILITY_TOLERANCE
            else (0, -best_low_fidelity_feasibility)
        )
        return current > best

    def _is_better_than_reference(
        self,
        metrics: EvaluationMetrics,
        reference_metrics: EvaluationMetrics,
    ) -> bool:
        return self._metrics_rank(metrics) > self._metrics_rank(reference_metrics)

    def _metrics_rank(self, metrics: EvaluationMetrics) -> tuple[int, float]:
        if metrics.evaluation_failed:
            return (-1, float("-inf"))
        if metrics.constraints_satisfied:
            return (1, metrics.p1_score)
        return (0, -metrics.p1_feasibility)

    def _advance_no_progress(self, *, step_improved: bool) -> int:
        if step_improved:
            self._state.no_progress_steps = 0
        else:
            self._state.no_progress_steps += 1
        return self._state.no_progress_steps

    def _is_repeat_state(self, params: LowDimBoundaryParams) -> bool:
        return self._state_key(params) in self._state.visited_state_keys

    def _record_visited_state(self, params: LowDimBoundaryParams) -> None:
        self._state.visited_state_keys.append(self._state_key(params))

    def _state_key(self, params: LowDimBoundaryParams) -> str:
        return (
            f"{params.aspect_ratio:.6f}|{params.elongation:.6f}|"
            f"{params.rotational_transform:.6f}|{params.triangularity_scale:.6f}"
        )
