from __future__ import annotations

from openenv.core.client_types import StepResult
from openenv.core.env_client import EnvClient

from fusion_lab.models import StellaratorAction, StellaratorObservation, StellaratorState


class FusionLabClient(
    EnvClient[StellaratorAction, StellaratorObservation, StellaratorState]
):
    """Thin typed client wrapper for the remote OpenEnv environment."""

    def _step_payload(self, action: StellaratorAction) -> dict[str, object]:
        return action.model_dump(exclude_none=True)

    def _parse_result(self, payload: dict[str, object]) -> StepResult[StellaratorObservation]:
        observation = StellaratorObservation(**payload)
        return StepResult(
            observation=observation,
            reward=observation.reward,
            done=observation.done,
        )

    def _parse_state(self, payload: dict[str, object]) -> StellaratorState:
        return StellaratorState(**payload)

