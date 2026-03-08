from __future__ import annotations

from openenv.core import create_fastapi_app

from fusion_lab.models import StellaratorAction, StellaratorObservation
from server.environment import BUDGET, N_FIELD_PERIODS, StellaratorEnvironment
from server.physics import ASPECT_RATIO_MAX, AVERAGE_TRIANGULARITY_MAX, EDGE_IOTA_OVER_NFP_MIN

app = create_fastapi_app(
    env=StellaratorEnvironment,
    action_cls=StellaratorAction,
    observation_cls=StellaratorObservation,
)


@app.get("/task")
def task_summary() -> dict[str, object]:
    return {
        "description": "Optimize the P1 benchmark with a rotating-ellipse parameterization.",
        "constraints": {
            "aspect_ratio_max": ASPECT_RATIO_MAX,
            "average_triangularity_max": AVERAGE_TRIANGULARITY_MAX,
            "edge_iota_over_nfp_min": EDGE_IOTA_OVER_NFP_MIN,
        },
        "n_field_periods": N_FIELD_PERIODS,
        "budget": BUDGET,
        "actions": ["run", "submit", "restore_best"],
        "parameters": ["aspect_ratio", "elongation", "rotational_transform"],
        "directions": ["increase", "decrease"],
        "magnitudes": ["small", "medium", "large"],
    }


def main() -> None:
    import uvicorn

    uvicorn.run("server.app:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
