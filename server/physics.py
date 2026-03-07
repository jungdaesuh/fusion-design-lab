from __future__ import annotations


class PhysicsEngine:
    """Placeholder for the VMEC-backed physics loop.

    The next implementation step should make this the single place that:
    - loads the baseline input
    - applies discrete coefficient updates
    - runs the solver
    - computes diagnostics
    - tracks best-known designs
    """

    def __init__(self) -> None:
        self._status = "unimplemented"

    @property
    def status(self) -> str:
        return self._status
