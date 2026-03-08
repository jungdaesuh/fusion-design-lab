from __future__ import annotations

from openenv.core import create_fastapi_app

from fusion_lab.models import StellaratorAction, StellaratorObservation
from server.environment import (
    ASPECT_RATIO_RANGE,
    BUDGET,
    IOTA_EDGE_RANGE,
    VOLUME_MIN,
    StellaratorEnvironment,
)

app = create_fastapi_app(
    env=StellaratorEnvironment,
    action_cls=StellaratorAction,
    observation_cls=StellaratorObservation,
)


@app.get("/task")
def task_summary() -> dict[str, object]:
    return {
        "description": "Minimize quasi-symmetry error for a 2-period quasi-helical stellarator.",
        "constraints": {
            "aspect_ratio": list(ASPECT_RATIO_RANGE),
            "rotational_transform_edge": list(IOTA_EDGE_RANGE),
            "volume_min": VOLUME_MIN,
        },
        "budget": BUDGET,
        "actions": ["run", "submit", "restore_best"],
        "operators": ["tune_rc10", "tune_rc11", "tune_zs11", "tune_zs12"],
        "directions": ["increase", "decrease"],
        "magnitudes": ["small", "medium", "large"],
        "restart_modes": ["hot", "cold"],
    }


def main() -> None:
    import uvicorn

    uvicorn.run("server.app:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
