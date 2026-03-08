# P1 Parameterization Deep-Dive

**Date:** 2026-03-07
**Status:** Findings complete. Parameterization repair is implemented; measured sweep follow-up is pending.

This document records the investigation into why the current 3-knob rotating-ellipse
environment cannot produce P1-feasible designs, what the original winning session
actually did, and the validated plan for fixing it.

---

## 1. The Structural Blocker

### Symptom

The environment's 3-parameter action space (`aspect_ratio`, `elongation`,
`rotational_transform`) cannot satisfy the P1 constraints regardless of parameter
values.

### Evidence

A 125-point grid sweep over the full 3-knob range with the real `constellaration`
verifier:

```
aspect_ratio    ∈ [2.0, 8.0]   (5 values)
elongation      ∈ [1.0, 5.0]   (5 values)
rot_transform   ∈ [0.1, 1.0]   (5 values)
n_field_periods = 3
```

**Result: 0/125 feasible.** Every configuration produced:

- `average_triangularity ≈ +0.005` (constraint requires `≤ -0.5`, gap of ~0.505)
- `edge_iota_over_nfp ≈ 0.05-0.22` (constraint requires `≥ 0.3`)

Varying `n_field_periods` (3, 4, 5) did not change the result. The
`generate_rotating_ellipse` function structurally produces near-zero triangularity
regardless of its input parameters.

### Root cause

`generate_rotating_ellipse(aspect_ratio, elongation, rotational_transform,
n_field_periods)` sets Fourier coefficients that define the boundary shape. The
`m=2, n=0` mode (which controls triangularity) is not meaningfully set by any of the
three input parameters. Triangularity is structurally fixed near zero.

The `rotational_transform` range `[0.1, 1.0]` is also too low. Even with injected
triangularity, `edge_iota_over_nfp` doesn't reach 0.3 until `rotational_transform ≈ 1.5+`.

---

## 2. The Original Winning Session

### Source

The original session that found P1-feasible designs is documented in:

```
ai-sci-feasible-designs/docs/harness/raw-session.md
```

Session: `rollout-2026-01-05T10-43-45-019b8bd3-14d6-7253-8235-f732ee43d683.jsonl`
(25,012 lines, 200 agent messages, Jan 5-9 2026)

### What the agent actually did for P1

1. Built `scripts/search_p1_lowdim.py` — a rotating-ellipse sweep with a **4th knob**
2. Found 3 feasible designs (feasibility 0.0) within ~20 minutes
3. Refined with trust-region local optimizer around those seeds
4. Downloaded scadena-pf leaderboard seed from HuggingFace as anchor
5. Ran `scripts/p1_alm_ngopt_multifidelity.py` (ALM + NGOpt multi-fidelity)
6. Final result: score 0.970141, beating leaderboard 0.969457

### The 4th knob: `tri_scale`

The script `search_p1_lowdim.py` (recovered from git at commit `300c191`) does NOT
use the raw `generate_rotating_ellipse` output. After generating the base shape, it:

1. Expands Fourier resolution: `set_max_mode_numbers(surface, max_poloidal_mode=3, max_toroidal_mode=3)`
2. Injects triangularity: `r_cos[2, center] = -tri_scale * minor_radius`
3. Cleans auxiliary modes: `r_cos[0, :center] = 0.0`, `z_sin[0, :center+1] = 0.0`
4. Returns the modified `SurfaceRZFourier`

The `tri_scale` knob directly controls the `m=2, n=0` Fourier mode, which is what
drives `average_triangularity` in the physics evaluation. This is the missing piece.

### Parameter ranges from the original script

```python
aspect_ratio:          [3.0, 3.6]
elongation:            [1.4, 2.2]
rotational_transform:  [1.5, 2.2]   # NOTE: much higher than our [0.1, 1.0]
tri_scale:             [0.55, 0.8]
```

---

## 3. The Harness Campaign Results

### All campaigns found zero feasible designs

Queried SQLite databases across all P1 runs in `ai-sci-feasible-designs/runs/`:

| Run | Candidates | Feasible | Best feasibility |
|-----|-----------|----------|-----------------|
| p1_campaign | 58 | 0 | 0.615 |
| p1_campaign_v2 | 50 | 0 | 0.416 |
| p1_e2e_validate | 7 | 0 | 0.639 |
| p1_live | 23 | 0 | 0.569 |

The campaign candidates used full Fourier boundaries (`5x9` arrays, `n_field_periods=5`),
not the low-dimensional rotating-ellipse family.

### Postmortem diagnosis (from P1_CAMPAIGN_POSTMORTEM.md)

The campaign's `_COLD_START_GUIDANCE` told the LLM "Do NOT generate from scratch" and
"Start with small perturbations (0.01-0.05)." The winning raw-session agent did the
exact opposite: broad sweeps, large parameter variations, rotating-ellipse seeds. The
guidance actively prohibited the winning strategy.

---

## 4. Live Sweep Validation

### 4-knob sweep with `tri_scale` injection

A 256-point grid sweep using the same boundary construction as `search_p1_lowdim.py`:

```
aspect_ratio    ∈ [3.2, 3.8]   step 0.2  (4 values)
elongation      ∈ [1.2, 1.8]   step 0.2  (4 values)
rot_transform   ∈ [1.2, 1.8]   step 0.2  (4 values)
tri_scale       ∈ [0.4, 0.7]   step 0.1  (4 values)
n_field_periods = 3
mpol = 3, ntor = 3
```

**Result from the recorded sweep:**

```
Total configs: 256
Evaluated:     228  (VMEC succeeded)
Crashed:        28  (VMEC solver failed)
Feasible:       10
Crash rate:    10.9%
Feasibility rate (of evaluated): 4.4%
```

### Top feasible results

| AR | elong | rot_t | tri_s | AR_out | tri | iota/nfp | elong_out | feas | ok |
|----|-------|-------|-------|--------|-----|----------|-----------|------|----|
| 3.6 | 1.4 | 1.6 | 0.60 | 3.287 | -0.5003 | 0.3005 | 7.3751 | 0.0000 | YES |
| 3.6 | 1.4 | 1.8 | 0.60 | 3.287 | -0.5003 | 0.3481 | 8.9318 | 0.0000 | YES |
| 3.8 | 1.4 | 1.6 | 0.60 | 3.487 | -0.5003 | 0.3256 | 7.9202 | 0.0000 | YES |
| 3.8 | 1.6 | 1.6 | 0.60 | 3.474 | -0.5037 | 0.3168 | 8.0626 | 0.0000 | YES |
| 3.8 | 1.8 | 1.6 | 0.60 | 3.459 | -0.5075 | 0.3097 | 8.2033 | 0.0000 | YES |
| 3.4 | 1.2 | 1.8 | 0.60 | 3.096 | -0.4977 | 0.3276 | 8.0849 | 0.0046 | YES |
| 3.8 | 1.2 | 1.6 | 0.60 | 3.496 | -0.4977 | 0.3345 | 7.7908 | 0.0046 | YES |
| 3.6 | 1.2 | 1.8 | 0.60 | 3.296 | -0.4977 | 0.3535 | 8.8140 | 0.0046 | YES |
| 3.2 | 1.2 | 1.8 | 0.60 | 2.896 | -0.4977 | 0.2995 | 7.4314 | 0.0046 | YES |
| 3.6 | 1.2 | 1.6 | 0.60 | 3.296 | -0.4977 | 0.3105 | 7.2363 | 0.0046 | YES |

**Key observations:**

- All feasible designs have `tri_scale = 0.60`
- `rot_transform ∈ {1.6, 1.8}` only — lower values never reach feasibility
- `average_triangularity` clusters at `-0.500` to `-0.508` (right at the constraint)
- Triangularity is always the binding constraint (within the 1% tolerance)
- `max_elongation` ranges from 7.2 to 8.9 (score ~0.31 to ~0.12). Significant room
  for optimization compared to the winning score of 0.970 (elongation 1.27)

### Crash rate by `rotational_transform`

| rot_transform | crash rate | feasible |
|---------------|-----------|----------|
| 1.2 | 0% (0/64) | 0 |
| 1.4 | 0% (0/64) | 0 |
| 1.6 | 0% (0/64) | 6 |
| 1.8 | 44% (28/64) | 4 |

**`rot_transform = 1.6` is the sweet spot:** zero crashes, highest feasible count.

### VMEC crash zone

Tested the extreme region (`rot_transform ∈ [2.0, 2.4]`, `tri_scale ∈ [0.7, 0.9]`):

```
600/600 crashed (100%)
```

VMEC solver fails universally when the boundary is too distorted. The crash boundary
is approximately `rot_transform ≥ 2.0` combined with `tri_scale ≥ 0.7`.

---

## 5. Verifier Analysis

### What's correct in the current verifier (`server/physics.py`)

1. **`_to_evaluation_metrics`** uses `GeometricalProblem` public API:
   - `problem.is_feasible(metrics)` — applies the 1% tolerance internally
   - `problem.compute_feasibility(metrics)` — infinity-norm of normalized violations
   - `problem.get_objective(metrics)` — returns `(max_elongation, minimize=True)`

2. **`_score_from_objective`** matches the official formula:
   `score = 1 - clip((max_elongation - 1) / 9, 0, 1)`

3. **Multi-fidelity split** is correct:
   - `run` actions use low-fidelity VMEC (~0.6s per eval)
   - `submit` uses high-fidelity VMEC (~24s per eval)

4. **Constraint constants** match the official P1 definition:
   - `aspect_ratio ≤ 4.0`
   - `average_triangularity ≤ -0.5`
   - `edge_rotational_transform / n_field_periods ≥ 0.3`

### What needs to change

- `evaluate_params` currently takes `RotatingEllipseParams` and calls
  `generate_rotating_ellipse` directly. It should be split into:
  - `build_boundary_from_params(...)` → `SurfaceRZFourier` (handles mode expansion + tri_scale injection)
  - `evaluate_boundary(boundary, fidelity)` → `EvaluationMetrics` (pure evaluation, no parameterization knowledge)

---

## 6. Reward Analysis

### Reward V0 structure (current, in `server/environment.py`)

```
Feasibility transition:      ±3.0 on crossing the feasible/infeasible boundary
Dual-track step shaping:
  feasible + feasible     →  (prev_elongation - curr_elongation) * 10.0
  otherwise               →  (prev_feasibility - curr_feasibility) * 5.0
Per-step cost:               -0.1 for non-submit actions
Terminal bonus (submit):      5.0 * improvement_ratio + budget_efficiency
Terminal bonus (exhaust):     2.0 * improvement_ratio
Not improved penalty:        -1.0 (submit) / -0.5 (exhaust)
```

### Assessment

**The reward is well-designed and should stay unchanged.** It only uses two scalars
from the verifier: `feasibility` and `objective (max_elongation)`. These are
problem-agnostic quantities that `GeometricalProblem` provides for any problem variant.

Things the reward correctly avoids:
- Per-constraint shaping (would overfit to P1's specific constraint structure)
- Tolerance-exploit bonus (would overfit to the 1% evaluator quirk)
- Mode-specific or parameter-specific weighting
- Any knowledge of which knob controls which metric

**One thing to monitor during playtesting:** the `5.0` multiplier on feasibility shaping
may need tuning once the action space changes. Mode perturbations produce different
feasibility deltas per step than the old 3-knob steps. But tune from playtest data,
not from theory.

---

## 7. Findings from the P1 Score Chase Notes

From `ai-sci-feasible-designs/docs/P1_SCORE_CHASE_NOTES.md`:

### Best submission metrics (high-fidelity)

```
max_elongation        = 1.266744   →  score = 0.970362
aspect_ratio          = 3.999377   (tight, but feasible)
average_triangularity = -0.495236  (normalized violation ≈ 0.009529)
iota/nfp              = 0.298946   (normalized violation ≈ 0.003515)
feasibility           = 0.009529   (feasible due to 1% tolerance)
```

### Key patterns

- The winning region is "thin": improving elongation pushes triangularity and/or iota
  over the constraint cliff
- The **1% feasibility tolerance** is a first-order effect: the best scores come from
  intentionally pushing constraints to the edge of tolerance to squeeze more elongation
  reduction
- Triangularity is usually the binding constraint near the best scores; iota is second
- The best submission used a full Fourier boundary (`mpol=8, ntor=8`, `n_field_periods=3`)
  refined through multiple optimization stages, not the low-dimensional parameterization

### What this means for our environment

Our feasible designs from the 4-knob sweep have `max_elongation ≈ 7.2-8.9`
(score ≈ 0.12-0.31). The winning submission has `max_elongation = 1.27` (score 0.97).
The gap is large — the 4-knob family can reach feasibility but cannot reach competitive
scores. This is expected: the environment is a stepping stone for learning
constraint-satisfaction and basic optimization, not a path to the leaderboard.

---

## 8. Anti-Overfitting Design

### What constitutes overfitting in this context

- Per-constraint reward weighting (e.g., "triangularity progress is worth 2x")
- Reward bonuses for exploiting the 1% tolerance
- Action-space design that hardcodes which modes matter
- Single fixed starting state that agents memorize

### Agreed anti-overfitting levers

1. **Multiple frozen reset seeds first** (start with exact seeds; add bounded jitter only
   if memorization becomes a real problem)
2. **Held-out evaluation seeds** (test generalization, not memorization)
3. **Reward based on official scalars only** (feasibility + objective, not per-constraint)
4. **Domain knowledge in initial state, not reward** (good baseline params in `reset()`,
   not constraint-specific shaping in `_compute_reward`)
5. **Known winners as calibration fixtures only**, not optimization targets

---

## 9. Agreed Plan

### What everyone agrees on

1. **4-knob low-dimensional action space**: `aspect_ratio`, `elongation`,
   `rotational_transform`, `triangularity_scale`
2. **Boundary-based verifier**: `build_boundary_from_params(...)` + `evaluate_boundary(...)`
3. **Explicit VMEC crash handling**: treat solver failures as bad-but-not-fatal
4. **Reward V0 unchanged in spirit**: feasibility-first, scalar-only, no P1-specific shaping
5. **Fidelity labeling in observation**: distinguish low-fi vs high-fi metrics

### What is deferred until after build + playtest

- Exact `rotational_transform` range bounds (data suggests ~[1.2, 1.9] is useful)
- Exact `triangularity_scale` delta values
- Seed pool construction (need empirical sweep in the repaired parameterization)
- Whether budget should be 6 or 8
- Any Reward V1 changes

### Implementation order

1. `server/physics.py` — boundary-based verifier interface
2. `fusion_lab/models.py` — action/observation/state for 4 knobs
3. `server/environment.py` — reset with seed pool, discrete knob perturbations, VMEC crash handling
4. `server/app.py` — expose new action schema
5. `baselines/` — random + heuristic (repair feasibility first, then reduce elongation)
6. Manual playtest — verify budget is sufficient, tune ranges/deltas/seeds empirically

---

## 10. Cross-Validation Record

This plan was cross-validated with an independent agent that:

- Independently confirmed the 3-knob blocker
- Independently confirmed the historical `tri_scale` implementation detail
- Reproduced VMEC crash failures
- Validated the layer decomposition (verifier / environment / parameterization)

### Pushbacks from the cross-validation agent and resolution

| Pushback | Verdict | Resolution |
|----------|---------|------------|
| "10/228 feasible is unverified" | **Partially addressed.** The recorded sweep found feasible points in the repaired 4-knob family, but this exact count should be treated as an artifact-backed result, not a free-floating fact. | Keep the sweep note, and link or preserve the underlying artifact if this exact count will be cited elsewhere. |
| "rt=1.8 comfortably feasible is too strong" | **Partially valid.** 44% crash rate at 1.8. | rt=1.6 is the true sweet spot: 0% crashes, 6 feasible. |
| "Delta values are design proposals, not facts" | **Valid.** | Defer to post-build playtesting. |
| "Seed pool not empirically validated" | **Valid.** | Methodology sound, execution pending. |
| "Budget change to 8-10 is speculative" | **Valid.** | Keep 6 until playtest proves otherwise. |

---

## Appendix A: Key File Locations

### Fusion Design Lab (this repo)

```
server/physics.py       — verifier (needs boundary-based refactor)
server/environment.py   — environment loop + reward V0
fusion_lab/models.py    — action/observation/state schemas
server/app.py           — FastAPI endpoints
baselines/              — random + heuristic agents
```

### ai-sci-feasible-designs (reference repo)

```
docs/harness/raw-session.md                — original winning session narrative
docs/harness/P1_CAMPAIGN_POSTMORTEM.md     — why campaigns found 0 feasible
docs/P1_SCORE_CHASE_NOTES.md               — best P1 score details + approach
scripts/search_p1_lowdim.py                — the 4-knob sweep script (git: 300c191)
scripts/p1_alm_ngopt_multifidelity.py      — ALM+NGOpt optimizer (git: aba75b7)
runs/p1_campaign*/world.sqlite             — campaign evaluation databases
```

## Appendix B: Boundary Construction Reference

The 4-knob boundary construction, as implemented in the original
`search_p1_lowdim.py`:

```python
from constellaration.initial_guess import generate_rotating_ellipse
from constellaration.geometry import surface_rz_fourier
from constellaration.geometry.surface_rz_fourier import SurfaceRZFourier
import numpy as np

def build_boundary(aspect_ratio, elongation, rotational_transform, tri_scale, nfp=3):
    # 1. Generate base rotating-ellipse shape
    surface = generate_rotating_ellipse(
        aspect_ratio=aspect_ratio,
        elongation=elongation,
        rotational_transform=rotational_transform,
        n_field_periods=nfp,
    )

    # 2. Expand to higher Fourier modes
    surface = surface_rz_fourier.set_max_mode_numbers(
        surface, max_poloidal_mode=3, max_toroidal_mode=3,
    )

    # 3. Inject triangularity via the m=2, n=0 Fourier mode
    r_cos = np.asarray(surface.r_cos, dtype=float).copy()
    z_sin = np.asarray(surface.z_sin, dtype=float).copy()
    center = r_cos.shape[1] // 2
    minor = float(r_cos[1, center])

    r_cos[2, center] = -tri_scale * minor

    # 4. Clean auxiliary modes
    r_cos[0, :center] = 0.0
    z_sin[0, :center + 1] = 0.0

    return SurfaceRZFourier(
        r_cos=r_cos.tolist(),
        z_sin=z_sin.tolist(),
        n_field_periods=nfp,
        is_stellarator_symmetric=True,
    )
```

Key details:
- `r_cos[1, center]` is the minor radius of the base shape
- `r_cos[2, center]` is the `m=2, n=0` Fourier coefficient (controls triangularity)
- Setting it to `-tri_scale * minor` produces negative triangularity proportional to `tri_scale`
- The auxiliary mode cleanup ensures the boundary is well-conditioned for VMEC
