from __future__ import annotations

from random import Random
from typing import Any, Final, Optional

from openenv.core import Environment as BaseEnvironment

from fusion_lab.models import (
    RotatingEllipseParams,
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
    evaluate_params,
)

BUDGET: Final[int] = 6
N_FIELD_PERIODS: Final[int] = 3

PARAMETER_RANGES: Final[dict[str, tuple[float, float]]] = {
    "aspect_ratio": (2.0, 8.0),
    "elongation": (1.0, 5.0),
    "rotational_transform": (0.1, 1.0),
}

PARAMETER_DELTAS: Final[dict[str, dict[str, float]]] = {
    "aspect_ratio": {"small": 0.1, "medium": 0.3, "large": 0.8},
    "elongation": {"small": 0.1, "medium": 0.3, "large": 0.8},
    "rotational_transform": {"small": 0.02, "medium": 0.05, "large": 0.15},
}

BASELINE_PARAMS: Final[RotatingEllipseParams] = RotatingEllipseParams(
    aspect_ratio=3.5,
    elongation=1.5,
    rotational_transform=0.4,
)

TARGET_SPEC: Final[str] = (
    "Optimize the P1 benchmark using a rotating-ellipse parameterization. "
    "Constraints: aspect ratio <= 4.0, average triangularity <= -0.5, "
    "edge rotational transform / n_field_periods >= 0.3. "
    "Budget: 6 evaluations."
)


class StellaratorEnvironment(
    BaseEnvironment[StellaratorAction, StellaratorObservation, StellaratorState]
):
    def __init__(self) -> None:
        super().__init__()
        self._state = StellaratorState()
        self._last_metrics: EvaluationMetrics | None = None
        self._rng = Random()

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        **kwargs: Any,
    ) -> StellaratorObservation:
        self._rng = Random(seed)
        params = self._initial_params(seed)
        metrics = evaluate_params(params)
        self._state = StellaratorState(
            episode_id=episode_id,
            step_count=0,
            current_params=params,
            best_params=params,
            initial_score=metrics.p1_score,
            best_score=metrics.p1_score,
            current_feasibility=metrics.p1_feasibility,
            best_feasibility=metrics.p1_feasibility,
            budget_total=BUDGET,
            budget_remaining=BUDGET,
            episode_done=False,
            constraints_satisfied=metrics.constraints_satisfied,
        )
        self._last_metrics = metrics
        return self._build_observation(
            metrics,
            action_summary="Episode started from the rotating-ellipse baseline.",
        )

    def step(
        self,
        action: StellaratorAction,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> StellaratorObservation:
        if self._state.episode_done or self._state.budget_remaining <= 0:
            metrics = self._last_metrics or evaluate_params(self._state.current_params)
            return self._build_observation(
                metrics,
                action_summary=("Episode already ended. Call reset() before sending more actions."),
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

    # ------------------------------------------------------------------
    # Action handlers
    # ------------------------------------------------------------------

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
        metrics = evaluate_params(params)
        self._state.current_params = params
        self._state.current_feasibility = metrics.p1_feasibility
        self._state.constraints_satisfied = metrics.constraints_satisfied
        self._update_best(params, metrics)

        done = self._state.budget_remaining <= 0
        reward = self._compute_reward(metrics, action.intent, done)
        summary = self._summary_run(action, metrics)
        self._state.history.append(summary)
        self._last_metrics = metrics
        self._state.episode_done = done

        return self._build_observation(
            metrics,
            action_summary=summary,
            reward=reward,
            done=done,
        )

    def _handle_submit(self) -> StellaratorObservation:
        metrics = self._last_metrics or evaluate_params(self._state.current_params)
        reward = self._compute_reward(metrics, "submit", done=True)
        summary = self._summary_submit(metrics)
        self._state.history.append(summary)
        self._state.episode_done = True

        return self._build_observation(
            metrics,
            action_summary=summary,
            reward=reward,
            done=True,
        )

    def _handle_restore(self) -> StellaratorObservation:
        self._state.budget_remaining -= 1
        self._state.current_params = self._state.best_params
        metrics = evaluate_params(self._state.current_params)
        self._state.current_feasibility = metrics.p1_feasibility
        self._state.constraints_satisfied = metrics.constraints_satisfied

        done = self._state.budget_remaining <= 0
        reward = self._compute_reward(metrics, "restore_best", done)
        summary = (
            "Restored the best-known design. "
            f"Score={metrics.p1_score:.6f}, feasibility={metrics.p1_feasibility:.6f}."
        )
        self._state.history.append(summary)
        self._last_metrics = metrics
        self._state.episode_done = done

        return self._build_observation(
            metrics,
            action_summary=summary,
            reward=reward,
            done=done,
        )

    def _handle_invalid_run(self) -> StellaratorObservation:
        self._state.budget_remaining -= 1
        metrics = self._last_metrics or evaluate_params(self._state.current_params)
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

    # ------------------------------------------------------------------
    # Reward V0
    # ------------------------------------------------------------------

    def _compute_reward(
        self,
        metrics: EvaluationMetrics,
        intent: str,
        done: bool,
    ) -> float:
        previous_metrics = self._last_metrics or metrics
        reward = 0.0

        if metrics.constraints_satisfied and not previous_metrics.constraints_satisfied:
            reward += 3.0
        if previous_metrics.constraints_satisfied and not metrics.constraints_satisfied:
            reward -= 3.0

        if metrics.constraints_satisfied:
            reward += (previous_metrics.max_elongation - metrics.max_elongation) * 10.0
        else:
            reward += (previous_metrics.p1_feasibility - metrics.p1_feasibility) * 5.0

        if intent != "submit":
            reward -= 0.1

        if intent == "submit":
            if metrics.constraints_satisfied and self._state.best_score > self._state.initial_score:
                improvement_ratio = (self._state.best_score - self._state.initial_score) / max(
                    1.0 - self._state.initial_score, 1e-6
                )
                budget_efficiency = self._state.budget_remaining / self._state.budget_total
                reward += 5.0 * improvement_ratio + budget_efficiency
            else:
                reward -= 1.0
        elif done:
            if metrics.constraints_satisfied and self._state.best_score > self._state.initial_score:
                improvement_ratio = (self._state.best_score - self._state.initial_score) / max(
                    1.0 - self._state.initial_score, 1e-6
                )
                reward += 2.0 * improvement_ratio
            else:
                reward -= 0.5

        return round(reward, 4)

    # ------------------------------------------------------------------
    # Observation builders
    # ------------------------------------------------------------------

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
            f"max_elongation={metrics.max_elongation:.4f}  |  best_score={self._state.best_score:.6f}",
            f"aspect_ratio={metrics.aspect_ratio:.4f}  (<= {ASPECT_RATIO_MAX:.1f})",
            f"average_triangularity={metrics.average_triangularity:.4f}  (<= {AVERAGE_TRIANGULARITY_MAX:.1f})",
            f"edge_iota_over_nfp={metrics.edge_iota_over_nfp:.4f}  (>= {EDGE_IOTA_OVER_NFP_MIN:.1f})",
            f"feasibility={metrics.p1_feasibility:.6f}  |  best_feasibility={self._state.best_feasibility:.6f}",
            f"vacuum_well={metrics.vacuum_well:.4f}",
            f"constraints={'SATISFIED' if metrics.constraints_satisfied else 'VIOLATED'}",
            f"step={self._state.step_count}  |  budget={self._state.budget_remaining}/{self._state.budget_total}",
        ]

        return StellaratorObservation(
            diagnostics_text="\n".join(text_lines),
            max_elongation=metrics.max_elongation,
            aspect_ratio=metrics.aspect_ratio,
            average_triangularity=metrics.average_triangularity,
            edge_iota_over_nfp=metrics.edge_iota_over_nfp,
            p1_score=metrics.p1_score,
            p1_feasibility=metrics.p1_feasibility,
            vacuum_well=metrics.vacuum_well,
            step_number=self._state.step_count,
            budget_remaining=self._state.budget_remaining,
            best_score=self._state.best_score,
            best_feasibility=self._state.best_feasibility,
            constraints_satisfied=metrics.constraints_satisfied,
            target_spec=TARGET_SPEC,
            reward=reward,
            done=done,
        )

    # ------------------------------------------------------------------
    # Action summaries
    # ------------------------------------------------------------------

    def _summary_run(self, action: StellaratorAction, metrics: EvaluationMetrics) -> str:
        assert action.parameter is not None
        assert action.direction is not None
        assert action.magnitude is not None
        previous_metrics = self._last_metrics or metrics
        if metrics.constraints_satisfied:
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
            f"Applied {action.parameter} {action.direction} {action.magnitude}. {objective_summary}"
        )

    def _summary_submit(self, metrics: EvaluationMetrics) -> str:
        return (
            f"Submitted design with best_score={self._state.best_score:.6f}, "
            f"best_feasibility={self._state.best_feasibility:.6f}, "
            f"constraints={'SATISFIED' if metrics.constraints_satisfied else 'VIOLATED'}."
        )

    def _initial_params(self, seed: int | None) -> RotatingEllipseParams:
        if seed is None:
            return BASELINE_PARAMS
        rng = Random(seed)
        return RotatingEllipseParams(
            aspect_ratio=self._clamp(
                BASELINE_PARAMS.aspect_ratio + rng.uniform(-0.1, 0.1),
                parameter="aspect_ratio",
            ),
            elongation=self._clamp(
                BASELINE_PARAMS.elongation + rng.uniform(-0.1, 0.1),
                parameter="elongation",
            ),
            rotational_transform=self._clamp(
                BASELINE_PARAMS.rotational_transform + rng.uniform(-0.015, 0.015),
                parameter="rotational_transform",
            ),
        )

    def _apply_action(
        self,
        params: RotatingEllipseParams,
        parameter: str,
        direction: str,
        magnitude: str,
    ) -> RotatingEllipseParams:
        delta = PARAMETER_DELTAS[parameter][magnitude]
        signed_delta = delta if direction == "increase" else -delta

        next_values = params.model_dump()
        next_values[parameter] = self._clamp(
            next_values[parameter] + signed_delta,
            parameter=parameter,
        )
        return RotatingEllipseParams.model_validate(next_values)

    def _clamp(self, value: float, *, parameter: str) -> float:
        lower, upper = PARAMETER_RANGES[parameter]
        return min(max(value, lower), upper)

    def _update_best(self, params: RotatingEllipseParams, metrics: EvaluationMetrics) -> None:
        current_rank = self._candidate_rank(metrics)
        best_rank = (
            (1, self._state.best_score)
            if self._state.best_feasibility <= FEASIBILITY_TOLERANCE
            else (0, -self._state.best_feasibility)
        )
        if current_rank > best_rank:
            self._state.best_params = params
            self._state.best_score = metrics.p1_score
            self._state.best_feasibility = metrics.p1_feasibility

    def _candidate_rank(self, metrics: EvaluationMetrics) -> tuple[int, float]:
        if metrics.constraints_satisfied:
            return (1, metrics.p1_score)
        return (0, -metrics.p1_feasibility)
