from __future__ import annotations

from typing import Any, Final, Optional

from openenv.core import Environment as BaseEnvironment

from fusion_lab.models import (
    LowDimBoundaryParams,
    StellaratorAction,
    StellaratorObservation,
    StellaratorState,
)
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
N_FIELD_PERIODS: Final[int] = 3

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

RESET_SEEDS: Final[tuple[LowDimBoundaryParams, ...]] = (
    LowDimBoundaryParams(
        aspect_ratio=3.6,
        elongation=1.4,
        rotational_transform=1.5,
        triangularity_scale=0.55,
    ),
    LowDimBoundaryParams(
        aspect_ratio=3.4,
        elongation=1.4,
        rotational_transform=1.6,
        triangularity_scale=0.55,
    ),
    LowDimBoundaryParams(
        aspect_ratio=3.8,
        elongation=1.4,
        rotational_transform=1.5,
        triangularity_scale=0.55,
    ),
)

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
            current_params=params,
            best_params=params,
            initial_score=metrics.p1_score,
            best_score=metrics.p1_score,
            best_feasibility=metrics.p1_feasibility,
            budget_total=BUDGET,
            budget_remaining=BUDGET,
            episode_done=False,
            constraints_satisfied=metrics.constraints_satisfied,
        )
        self._last_metrics = metrics
        self._last_successful_metrics = None if metrics.evaluation_failed else metrics
        return self._build_observation(
            metrics,
            action_summary="Episode started from a frozen low-dimensional seed.",
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
            return self._build_observation(
                metrics,
                action_summary="Episode already ended. Call reset() before sending more actions.",
                reward=0.0,
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
        params = self._apply_action(
            params=self._state.current_params,
            parameter=action.parameter,
            direction=action.direction,
            magnitude=action.magnitude,
        )
        metrics = self._evaluate_params(params, fidelity="low")
        self._state.current_params = params
        self._state.constraints_satisfied = metrics.constraints_satisfied
        self._update_best(params, metrics)

        done = self._state.budget_remaining <= 0
        reward = self._compute_reward(metrics, action.intent, done)
        summary = self._summary_run(action, metrics)
        self._state.history.append(summary)
        self._last_metrics = metrics
        if not metrics.evaluation_failed:
            self._last_successful_metrics = metrics
        self._state.episode_done = done

        return self._build_observation(
            metrics,
            action_summary=summary,
            reward=reward,
            done=done,
        )

    def _handle_submit(self) -> StellaratorObservation:
        metrics = self._evaluate_params(self._state.current_params, fidelity="high")
        reward = self._compute_reward(metrics, "submit", done=True)
        summary = self._summary_submit(metrics)
        self._state.history.append(summary)
        self._state.episode_done = True
        self._last_metrics = metrics
        if not metrics.evaluation_failed:
            self._last_successful_metrics = metrics

        return self._build_observation(
            metrics,
            action_summary=summary,
            reward=reward,
            done=True,
        )

    def _handle_restore(self) -> StellaratorObservation:
        self._state.budget_remaining -= 1
        self._state.current_params = self._state.best_params
        metrics = self._evaluate_params(self._state.current_params, fidelity="low")
        self._state.constraints_satisfied = metrics.constraints_satisfied

        done = self._state.budget_remaining <= 0
        reward = self._compute_reward(metrics, "restore_best", done)
        summary = self._summary_restore(metrics)
        self._state.history.append(summary)
        self._last_metrics = metrics
        if not metrics.evaluation_failed:
            self._last_successful_metrics = metrics
        self._state.episode_done = done

        return self._build_observation(
            metrics,
            action_summary=summary,
            reward=reward,
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
        self._state.episode_done = done
        return self._build_observation(
            metrics,
            action_summary=summary,
            reward=-1.0,
            done=done,
        )

    def _compute_reward(
        self,
        metrics: EvaluationMetrics,
        intent: str,
        done: bool,
    ) -> float:
        previous_metrics = self._reference_metrics(metrics)
        if metrics.evaluation_failed:
            reward = FAILURE_PENALTY
            if intent != "submit":
                reward -= 0.1
            if intent == "submit":
                reward -= 1.0
            elif done:
                reward -= 0.5
            return round(reward, 4)

        reward = 0.0

        if metrics.constraints_satisfied and not previous_metrics.constraints_satisfied:
            reward += 3.0
        if previous_metrics.constraints_satisfied and not metrics.constraints_satisfied:
            reward -= 3.0

        if metrics.constraints_satisfied and previous_metrics.constraints_satisfied:
            reward += (previous_metrics.max_elongation - metrics.max_elongation) * 10.0
        else:
            reward += (previous_metrics.p1_feasibility - metrics.p1_feasibility) * 5.0

        if intent != "submit":
            reward -= 0.1

        if intent == "submit" or done:
            improved = (
                metrics.constraints_satisfied and metrics.p1_score > self._state.initial_score
            )
            if improved:
                ratio = (metrics.p1_score - self._state.initial_score) / max(
                    1.0 - self._state.initial_score, 1e-6
                )
                if intent == "submit":
                    reward += 5.0 * ratio + self._state.budget_remaining / self._state.budget_total
                else:
                    reward += 2.0 * ratio
            else:
                reward -= 1.0 if intent == "submit" else 0.5

        return round(reward, 4)

    def _build_observation(
        self,
        metrics: EvaluationMetrics,
        action_summary: str,
        reward: float | None = None,
        done: bool = False,
    ) -> StellaratorObservation:
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
                f"max_elongation={metrics.max_elongation:.4f}  |  best_score={self._state.best_score:.6f}",
                f"aspect_ratio={metrics.aspect_ratio:.4f}  (<= {ASPECT_RATIO_MAX:.1f})",
                f"average_triangularity={metrics.average_triangularity:.4f}  (<= {AVERAGE_TRIANGULARITY_MAX:.1f})",
                f"edge_iota_over_nfp={metrics.edge_iota_over_nfp:.4f}  (>= {EDGE_IOTA_OVER_NFP_MIN:.1f})",
                f"feasibility={metrics.p1_feasibility:.6f}  |  best_feasibility={self._state.best_feasibility:.6f}",
                f"vacuum_well={metrics.vacuum_well:.4f}",
                f"constraints={'SATISFIED' if metrics.constraints_satisfied else 'VIOLATED'}",
                f"step={self._state.step_count}  |  budget={self._state.budget_remaining}/{self._state.budget_total}",
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
            best_score=self._state.best_score,
            best_feasibility=self._state.best_feasibility,
            constraints_satisfied=metrics.constraints_satisfied,
            target_spec=TARGET_SPEC,
            reward=reward,
            done=done,
        )

    def _summary_run(self, action: StellaratorAction, metrics: EvaluationMetrics) -> str:
        assert action.parameter is not None
        assert action.direction is not None
        assert action.magnitude is not None
        if metrics.evaluation_failed:
            return (
                f"Applied {action.parameter} {action.direction} {action.magnitude}. "
                f"Low-fidelity evaluation failed: {metrics.failure_reason}"
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
            f"Low-fidelity evaluation. {objective_summary}"
        )

    def _summary_submit(self, metrics: EvaluationMetrics) -> str:
        if metrics.evaluation_failed:
            return f"Submit failed during high-fidelity evaluation: {metrics.failure_reason}"
        return (
            f"Submitted current_score={metrics.p1_score:.6f}, "
            f"best_seen_score={self._state.best_score:.6f}, "
            f"best_feasibility={self._state.best_feasibility:.6f}, "
            f"constraints={'SATISFIED' if metrics.constraints_satisfied else 'VIOLATED'}."
        )

    def _summary_restore(self, metrics: EvaluationMetrics) -> str:
        if metrics.evaluation_failed:
            return f"Restore-best failed during low-fidelity evaluation: {metrics.failure_reason}"
        return (
            "Restored the best-known design. "
            f"Score={metrics.p1_score:.6f}, feasibility={metrics.p1_feasibility:.6f}."
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
    ) -> LowDimBoundaryParams:
        delta = PARAMETER_DELTAS[parameter][magnitude]
        signed_delta = delta if direction == "increase" else -delta

        next_values = params.model_dump()
        next_values[parameter] = self._clamp(
            next_values[parameter] + signed_delta,
            parameter=parameter,
        )
        return LowDimBoundaryParams.model_validate(next_values)

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

    def _update_best(self, params: LowDimBoundaryParams, metrics: EvaluationMetrics) -> None:
        if metrics.evaluation_failed:
            return

        current = (
            (1, metrics.p1_score) if metrics.constraints_satisfied else (0, -metrics.p1_feasibility)
        )
        best = (
            (1, self._state.best_score)
            if self._state.best_feasibility <= FEASIBILITY_TOLERANCE
            else (0, -self._state.best_feasibility)
        )
        if current > best:
            self._state.best_params = params
            self._state.best_score = metrics.p1_score
            self._state.best_feasibility = metrics.p1_feasibility
