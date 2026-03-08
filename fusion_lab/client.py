from __future__ import annotations

from openenv.core.client_types import StepResult
from openenv.core.env_client import EnvClient

from fusion_lab.models import StellaratorAction, StellaratorObservation, StellaratorState


class FusionLabClient(EnvClient[StellaratorAction, StellaratorObservation, StellaratorState]):
    """Typed client wrapper for the remote Fusion Design Lab environment."""

    def _step_payload(self, action: StellaratorAction) -> dict[str, object]:
        return action.model_dump(exclude_none=True)

    def _parse_result(self, payload: dict[str, object]) -> StepResult[StellaratorObservation]:
        observation_payload = dict(payload.get("observation", {}))
        observation_payload["reward"] = payload.get("reward")
        observation_payload["done"] = payload.get("done", False)
        observation = StellaratorObservation.model_validate(observation_payload)
        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: dict[str, object]) -> StellaratorState:
        return StellaratorState.model_validate(payload)
