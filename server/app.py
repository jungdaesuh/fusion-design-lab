from __future__ import annotations

from fastapi import FastAPI

from server.environment import TASK, environment_status

app = FastAPI(title="Fusion Design Lab")


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "environment": environment_status()}


@app.get("/task")
def task_summary() -> dict[str, object]:
    return TASK

