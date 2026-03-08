from __future__ import annotations

from typing import Any, Final, Optional

from openenv.core import Environment as BaseEnvironment

from fusion_lab.models import (
    ActionMonitor,
    ActionIntent,
    LowDimBoundaryParams,
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
    "triangularity <= -0.5, edge rotational transform / n_field_periods >= 0.3. "
    "Run actions use low-fidelity verification. Submit uses high-fidelity verification. "
    "Budget: 6 evaluations."
)

FAILURE_PENALTY: Final[float] = -2.0


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
        action_monitor = self._build_action_monitor(
            action=action,
            params_before=params_before,
            params_after=params,
            clamped=clamped,
            no_op=no_op,
        )
        metrics = self._evaluate_params(params, fidelity="low")
        self._state.current_params = params
        self._state.constraints_satisfied = metrics.constraints_satisfied
        self._update_best(params, metrics)

        done = self._state.budget_remaining <= 0
        reward_breakdown = self._compute_reward_breakdown(metrics, action.intent, done)
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
        action = StellaratorAction(intent="submit")
        action_monitor = self._build_action_monitor(
            action=action,
            params_before=self._state.current_params,
            params_after=self._state.current_params,
        )
        metrics = self._evaluate_params(self._state.current_params, fidelity="high")
        initial_submit_score = self._initial_high_fidelity_score()
        best_submit_metrics = self._refresh_best_high_fidelity_metrics(metrics)
        reward_breakdown = self._compute_reward_breakdown(
            metrics,
            "submit",
            done=True,
            initial_reference_score=initial_submit_score,
        )
        reward = reward_breakdown.total
        summary = self._summary_submit(metrics, best_submit_metrics)
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
        action = StellaratorAction(intent="restore_best")
        action_monitor = self._build_action_monitor(
            action=action,
            params_before=params_before,
            params_after=self._state.current_params,
            no_op=params_before == self._state.current_params,
            used_best_params=True,
        )
        metrics = self._evaluate_params(self._state.current_params, fidelity="low")
        self._state.constraints_satisfied = metrics.constraints_satisfied

        done = self._state.budget_remaining <= 0
        reward_breakdown = self._compute_reward_breakdown(metrics, "restore_best", done)
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
        initial_reference_score: float | None = None,
    ) -> RewardBreakdown:
        recovered_from_failure = self._recovered_from_failed_evaluation(metrics)
        previous_metrics = self._reference_metrics(metrics)
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
        if metrics.evaluation_failed:
            breakdown.failure_penalty = FAILURE_PENALTY
            if intent != "submit":
                breakdown.step_cost = -0.1
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

        if metrics.constraints_satisfied and previous_metrics.constraints_satisfied:
            breakdown.objective_delta_reward = (
                previous_metrics.max_elongation - metrics.max_elongation
            ) * 10.0
        else:
            breakdown.feasibility_delta_reward = (
                previous_metrics.p1_feasibility - metrics.p1_feasibility
            ) * 5.0

        if intent != "submit":
            breakdown.step_cost = -0.1

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
        best_high_fidelity_score = self._state.best_high_fidelity_score
        best_high_fidelity_feasibility = self._state.best_high_fidelity_feasibility
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
                f"edge_iota_over_nfp={metrics.edge_iota_over_nfp:.4f}  (>= {EDGE_IOTA_OVER_NFP_MIN:.1f})",
                f"feasibility={metrics.p1_feasibility:.6f}",
                f"best_low_fidelity_score={best_low_fidelity_score:.6f}",
                f"best_low_fidelity_feasibility={best_low_fidelity_feasibility:.6f}",
                (
                    "best_high_fidelity_score="
                    f"{self._format_optional_metric(best_high_fidelity_score)}"
                ),
                (
                    "best_high_fidelity_feasibility="
                    f"{self._format_optional_metric(best_high_fidelity_feasibility)}"
                ),
                f"vacuum_well={metrics.vacuum_well:.4f}",
                f"constraints={'SATISFIED' if metrics.constraints_satisfied else 'VIOLATED'}",
                f"step={self._state.step_count}  |  budget={self._state.budget_remaining}/{self._state.budget_total}",
                f"reward_total={reward_breakdown.total:+.4f}",
                f"reward_terms={self._reward_terms_text(reward_breakdown)}",
                f"action_clamped={action_monitor.clamped}",
                f"action_no_op={action_monitor.no_op}",
                f"episode_total_reward={self._state.total_reward:+.4f}",
            ]
        )

        return StellaratorObservation(
            diagnostics_text="\n".join(text_lines),
            max_elongation=metrics.max_elongation,
            aspect_ratio=metrics.aspect_ratio,
            average_triangularity=metrics.average_triangularity,
            edge_iota_over_nfp=metrics.edge_iota_over_nfp,
            p1_score=metrics.p1_score,
            p1_feasibility=metrics.p1_feasibility,
            vacuum_well=metrics.vacuum_well,
            evaluation_fidelity=metrics.evaluation_fidelity,
            evaluation_failed=metrics.evaluation_failed,
            failure_reason=metrics.failure_reason,
            step_number=self._state.step_count,
            budget_remaining=self._state.budget_remaining,
            best_low_fidelity_score=best_low_fidelity_score,
            best_low_fidelity_feasibility=best_low_fidelity_feasibility,
            best_high_fidelity_score=best_high_fidelity_score,
            best_high_fidelity_feasibility=best_high_fidelity_feasibility,
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
                f"feasibility changed by {delta:+.6f} to {metrics.p1_feasibility:.6f}."
            )
        return (
            f"Applied {action.parameter} {action.direction} {action.magnitude}. "
            f"{action_note}"
            f"Low-fidelity evaluation. {objective_summary}"
        )

    def _summary_submit(
        self,
        metrics: EvaluationMetrics,
        best_submit_metrics: EvaluationMetrics,
    ) -> str:
        if metrics.evaluation_failed:
            return f"Submit failed during high-fidelity evaluation: {metrics.failure_reason}"
        return (
            f"Submitted current_high_fidelity_score={metrics.p1_score:.6f}, "
            f"best_high_fidelity_score={best_submit_metrics.p1_score:.6f}, "
            f"best_high_fidelity_feasibility={best_submit_metrics.p1_feasibility:.6f}, "
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

    def _recovered_from_failed_evaluation(self, metrics: EvaluationMetrics) -> bool:
        return (
            not metrics.evaluation_failed
            and self._last_metrics is not None
            and self._last_metrics.evaluation_failed
        )

    def _initial_high_fidelity_score(self) -> float:
        if self._state.initial_high_fidelity_score is not None:
            return self._state.initial_high_fidelity_score
        metrics = self._evaluate_params(self._state.initial_params, fidelity="high")
        self._state.initial_high_fidelity_score = metrics.p1_score
        return metrics.p1_score

    def _refresh_best_high_fidelity_metrics(
        self,
        current_submit_metrics: EvaluationMetrics,
    ) -> EvaluationMetrics:
        best_metrics = current_submit_metrics
        if self._state.best_params != self._state.current_params:
            best_metrics = self._evaluate_params(self._state.best_params, fidelity="high")

        self._state.best_high_fidelity_score = best_metrics.p1_score
        self._state.best_high_fidelity_feasibility = best_metrics.p1_feasibility
        return best_metrics

    def _format_optional_metric(self, value: float | None) -> str:
        if value is None:
            return "n/a"
        return f"{value:.6f}"

    def _build_action_monitor(
        self,
        *,
        action: StellaratorAction,
        params_before: LowDimBoundaryParams,
        params_after: LowDimBoundaryParams,
        clamped: bool = False,
        no_op: bool = False,
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

    def _reward_total(self, breakdown: RewardBreakdown) -> float:
        total = (
            breakdown.invalid_action_penalty
            + breakdown.failure_penalty
            + breakdown.failure_submit_penalty
            + breakdown.failure_budget_penalty
            + breakdown.feasibility_crossing_bonus
            + breakdown.feasibility_regression_penalty
            + breakdown.feasibility_delta_reward
            + breakdown.objective_delta_reward
            + breakdown.step_cost
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
            ("objective_delta_reward", breakdown.objective_delta_reward),
            ("step_cost", breakdown.step_cost),
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

        current = (
            (1, metrics.p1_score) if metrics.constraints_satisfied else (0, -metrics.p1_feasibility)
        )
        best = (
            (1, self._state.best_low_fidelity_score)
            if self._state.best_low_fidelity_feasibility <= FEASIBILITY_TOLERANCE
            else (0, -self._state.best_low_fidelity_feasibility)
        )
        if current > best:
            self._state.best_params = params
            self._state.best_low_fidelity_score = metrics.p1_score
            self._state.best_low_fidelity_feasibility = metrics.p1_feasibility
