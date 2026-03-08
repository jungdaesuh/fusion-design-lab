from __future__ import annotations

from fastapi.responses import HTMLResponse
from openenv.core import create_fastapi_app

from fusion_lab.models import StellaratorAction, StellaratorObservation
from server.environment import BUDGET, N_FIELD_PERIODS, StellaratorEnvironment
from server.physics import ASPECT_RATIO_MAX, AVERAGE_TRIANGULARITY_MAX, EDGE_IOTA_OVER_NFP_MIN

app = create_fastapi_app(
    env=StellaratorEnvironment,
    action_cls=StellaratorAction,
    observation_cls=StellaratorObservation,
)


@app.get("/", response_class=HTMLResponse)
def landing_page() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Fusion Design Lab</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: system-ui, -apple-system, sans-serif; background: #0a0e1a; color: #e0e0e0; min-height: 100vh; display: flex; align-items: center; justify-content: center; }
  .container { max-width: 720px; padding: 3rem 2rem; }
  h1 { font-size: 2.2rem; font-weight: 700; margin-bottom: 0.5rem; background: linear-gradient(135deg, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  .subtitle { color: #94a3b8; font-size: 1.1rem; margin-bottom: 2rem; }
  .card { background: #141926; border: 1px solid #1e293b; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.2rem; }
  .card h2 { font-size: 1rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.8rem; }
  .constraint { display: flex; justify-content: space-between; padding: 0.3rem 0; border-bottom: 1px solid #1e293b; }
  .constraint:last-child { border: none; }
  .constraint .name { color: #60a5fa; font-family: monospace; }
  .constraint .bound { color: #e0e0e0; font-family: monospace; }
  .endpoints { list-style: none; }
  .endpoints li { padding: 0.4rem 0; }
  .endpoints code { background: #1e293b; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.9rem; color: #a78bfa; }
  .endpoints .method { color: #4ade80; font-weight: 600; font-family: monospace; margin-right: 0.3rem; }
  .meta { display: flex; gap: 2rem; flex-wrap: wrap; }
  .meta-item { flex: 1; min-width: 140px; }
  .meta-item .value { font-size: 1.8rem; font-weight: 700; color: #60a5fa; }
  .meta-item .label { color: #64748b; font-size: 0.85rem; }
  a { color: #a78bfa; text-decoration: none; }
  a:hover { text-decoration: underline; }
  .footer { margin-top: 2rem; color: #475569; font-size: 0.85rem; text-align: center; }
</style>
</head>
<body>
<div class="container">
  <h1>Fusion Design Lab</h1>
  <p class="subtitle">OpenEnv P1 stellarator optimization environment powered by <code>constellaration</code></p>

  <div class="card">
    <h2>Task</h2>
    <p style="margin-bottom:1rem;">Minimize <strong>max elongation</strong> of a stellarator boundary using 4 geometric knobs, subject to physics constraints.</p>
    <div class="meta">
      <div class="meta-item"><div class="value">6</div><div class="label">evaluation budget</div></div>
      <div class="meta-item"><div class="value">26</div><div class="label">discrete actions</div></div>
      <div class="meta-item"><div class="value">3</div><div class="label">field periods</div></div>
    </div>
  </div>

  <div class="card">
    <h2>Constraints</h2>
    <div class="constraint"><span class="name">aspect_ratio</span><span class="bound">&le; 4.0</span></div>
    <div class="constraint"><span class="name">average_triangularity</span><span class="bound">&le; &minus;0.5</span></div>
    <div class="constraint"><span class="name">abs(edge_iota_over_nfp)</span><span class="bound">&ge; 0.3</span></div>
  </div>

  <div class="card">
    <h2>API Endpoints</h2>
    <ul class="endpoints">
      <li><span class="method">GET</span> <code>/health</code> &mdash; liveness check</li>
      <li><span class="method">GET</span> <code>/task</code> &mdash; task specification</li>
      <li><span class="method">POST</span> <code>/reset</code> &mdash; start a new episode</li>
      <li><span class="method">POST</span> <code>/step</code> &mdash; execute an action</li>
    </ul>
  </div>

  <div class="footer">
    <a href="https://github.com/jungdaesuh/fusion-design-lab">GitHub</a>
    &middot; OpenEnv Hackathon 2026
  </div>
</div>
</body>
</html>"""


@app.get("/task")
def task_summary() -> dict[str, object]:
    return {
        "description": (
            "Optimize the P1 benchmark with a custom low-dimensional boundary family "
            "derived from a rotating-ellipse seed."
        ),
        "constraints": {
            "aspect_ratio_max": ASPECT_RATIO_MAX,
            "average_triangularity_max": AVERAGE_TRIANGULARITY_MAX,
            "abs_edge_iota_over_nfp_min": EDGE_IOTA_OVER_NFP_MIN,
        },
        "n_field_periods": N_FIELD_PERIODS,
        "budget": BUDGET,
        "actions": ["run", "submit", "restore_best"],
        "parameters": [
            "aspect_ratio",
            "elongation",
            "rotational_transform",
            "triangularity_scale",
        ],
        "directions": ["increase", "decrease"],
        "magnitudes": ["small", "medium", "large"],
        "evaluation_modes": {
            "run": "low-fidelity constellaration evaluation",
            "submit": "high-fidelity constellaration evaluation",
        },
    }


def main() -> None:
    import uvicorn

    uvicorn.run("server.app:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
