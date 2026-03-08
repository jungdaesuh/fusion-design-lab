from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Final

NFP: Final[int] = 2

BASELINE_COEFFS: Final[dict[str, float]] = {
    "rc10": 1.0,
    "rc11": 0.12,
    "zs11": 0.12,
    "zs12": -0.02,
}

OPTIMAL_COEFFS: Final[dict[str, float]] = {
    "rc10": 1.02,
    "rc11": 0.135,
    "zs11": 0.115,
    "zs12": -0.035,
}

MAGNITUDE_DELTAS: Final[dict[str, float]] = {
    "small": 0.005,
    "medium": 0.02,
    "large": 0.05,
}


@dataclass(frozen=True)
class Diagnostics:
    qs_residual: float
    aspect_ratio: float
    iota_axis: float
    iota_edge: float
    volume: float
    magnetic_well_depth: float
    converged: bool


@dataclass
class PhysicsEngine:
    coeffs: dict[str, float] = field(default_factory=lambda: dict(BASELINE_COEFFS))
    best_coeffs: dict[str, float] = field(default_factory=lambda: dict(BASELINE_COEFFS))
    best_qs: float = float("inf")
    _rng: random.Random = field(default_factory=random.Random)

    def reset(self, seed: int | None = None) -> Diagnostics:
        self.coeffs = dict(BASELINE_COEFFS)
        self._rng = random.Random(seed)
        if seed is not None:
            for key in self.coeffs:
                self.coeffs[key] += self._rng.gauss(0, 0.002)
        self.best_coeffs = dict(self.coeffs)
        diag = self._compute_diagnostics(converged=True)
        self.best_qs = diag.qs_residual
        return diag

    def modify_and_run(
        self,
        operator: str,
        direction: str,
        magnitude: str,
        restart: str,
    ) -> Diagnostics:
        coeff_key = operator.removeprefix("tune_")
        delta = MAGNITUDE_DELTAS[magnitude]
        if direction == "decrease":
            delta = -delta

        prev_value = self.coeffs[coeff_key]
        self.coeffs[coeff_key] = prev_value + delta

        converged = self._simulate_convergence(magnitude, restart)
        if not converged:
            self.coeffs[coeff_key] = prev_value
            return self._compute_diagnostics(converged=False)

        diag = self._compute_diagnostics(converged=True)
        if diag.qs_residual < self.best_qs:
            self.best_qs = diag.qs_residual
            self.best_coeffs = dict(self.coeffs)
        return diag

    def restore_best(self) -> Diagnostics:
        self.coeffs = dict(self.best_coeffs)
        return self._compute_diagnostics(converged=True)

    def _compute_diagnostics(self, *, converged: bool) -> Diagnostics:
        rc10 = self.coeffs["rc10"]
        rc11 = self.coeffs["rc11"]
        zs11 = self.coeffs["zs11"]
        zs12 = self.coeffs["zs12"]

        r_minor = math.sqrt(rc11**2 + zs11**2)
        aspect_ratio = rc10 / max(r_minor, 1e-6)
        volume = 2.0 * math.pi**2 * rc10 * r_minor**2

        helical_excursion = abs(zs11 / max(abs(rc11), 1e-6))
        iota_axis = 0.35 + 0.15 * helical_excursion + 0.5 * abs(zs12)
        shear = 0.04 + 0.02 * abs(rc10 - 1.0)
        iota_edge = iota_axis + shear

        magnetic_well = 0.02 + 0.01 * (rc11 / max(abs(zs11), 1e-6) - 1.0)

        qs_residual = self._compute_qs_residual() if converged else float("inf")

        return Diagnostics(
            qs_residual=round(qs_residual, 6),
            aspect_ratio=round(aspect_ratio, 4),
            iota_axis=round(iota_axis, 4),
            iota_edge=round(iota_edge, 4),
            volume=round(volume, 4),
            magnetic_well_depth=round(magnetic_well, 4),
            converged=converged,
        )

    def _compute_qs_residual(self) -> float:
        d = {k: self.coeffs[k] - OPTIMAL_COEFFS[k] for k in OPTIMAL_COEFFS}
        quadratic = (
            2.0 * d["rc10"] ** 2
            + 8.0 * d["rc11"] ** 2
            + 8.0 * d["zs11"] ** 2
            + 15.0 * d["zs12"] ** 2
        )
        cross = 4.0 * d["rc11"] * d["zs11"] - 3.0 * d["rc10"] * d["zs12"]
        noise = self._rng.gauss(0, 0.0003)
        return max(quadratic + cross + 0.002 + noise, 0.001)

    def _simulate_convergence(self, magnitude: str, restart: str) -> bool:
        fail_prob = {"small": 0.02, "medium": 0.08, "large": 0.20}[magnitude]
        if restart == "hot":
            fail_prob *= 0.5
        for key, val in self.coeffs.items():
            deviation = abs(val - BASELINE_COEFFS[key])
            if deviation > 0.1:
                fail_prob += 0.15
            elif deviation > 0.05:
                fail_prob += 0.05
        return self._rng.random() > min(fail_prob, 0.8)
