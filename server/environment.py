from __future__ import annotations

from typing import Final

TASK: Final[dict[str, object]] = {
    "description": "Minimize quasi-symmetry error for a 2-period quasi-helical stellarator.",
    "constraints": {
        "aspect_ratio": [4.5, 7.0],
        "rotational_transform_edge": [0.3, 0.6],
        "volume_min": 0.5,
    },
    "budget": 6,
    "baseline_input": "server/data/input.QH_baseline",
}


def environment_status() -> str:
    """Return a simple status string until the full environment is implemented."""
    return "scaffolded"

