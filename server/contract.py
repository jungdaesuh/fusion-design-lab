from __future__ import annotations

from typing import Final

from fusion_lab.models import LowDimBoundaryParams, default_low_dim_boundary_params

N_FIELD_PERIODS: Final[int] = 3
DEFAULT_RESET_SEED: Final[LowDimBoundaryParams] = default_low_dim_boundary_params()

RESET_SEEDS: Final[tuple[LowDimBoundaryParams, ...]] = (
    DEFAULT_RESET_SEED,
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

SMOKE_TEST_PARAMS: Final[LowDimBoundaryParams] = DEFAULT_RESET_SEED
