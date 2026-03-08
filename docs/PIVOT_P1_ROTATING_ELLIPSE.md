# Pivot: P1 Rotating-Ellipse Environment

**Date:** 2026-03-07
**Status:** Supporting decision record, superseded as planning SSOT by `FUSION_DESIGN_LAB_PLAN_V2.md`
**Supersedes:** Synthetic physics model in current `server/physics.py`

Use this file as rationale for the pivot, not as a fresh planning queue. Once the pivot is accepted, implementation should follow the SSOT plan docs.

## Current Branch Status

- [x] pivot accepted
- [x] rotating-ellipse `P1` contract is implemented
- [x] `constellaration` verifier path is wired
- [ ] tracked fixtures are added
- [ ] manual playtest evidence is recorded
- [ ] heuristic baseline is refreshed for the real verifier path

Current caution:

- the default rotating-ellipse baseline params are currently useful as an infeasible reference, not as a near-feasible anchor, so the fixture set still needs a better boundary-region map

## Decision

Pivot the OpenEnv environment to use the official ConStellaration P1 benchmark with real VMEC physics, scoped to the rotating-ellipse low-dimensional parameter space.

This borrows the strongest low-dimensional entry point from the proven winning approach documented in `raw-session.md`, not the full approach.

## What Was Validated

| Claim | Status | Source |
|---|---|---|
| P1 is the cleanest benchmark task | Verified | `problems.py:113` — minimize max_elongation, 3 constraints, no QI |
| P1 skips QI | Verified | `problems.py:145` — `_does_it_require_qi = False` |
| Low-fidelity eval is fast enough | Measured | 0.63s per eval on local machine; postmortem says ~1s/eval |
| High-fidelity eval is expensive | Measured | 24s per eval; only viable for final validation |
| Rotating-ellipse can find P1-feasible designs | Verified | `raw-session.md`: sweeps found 3 feasible designs in ~20 min |
| vmecpp installs from wheels | Verified | `uv pip install vmecpp==0.4.7` resolves cleanly, no compilation |
| constellaration Dockerfile is not bloated | Verified | `python:3.10-slim` + `pip install constellaration` |
| Current seed logic is too loose for P1 | Verified | `seeds.py:42`: triangularity override 0.05 vs constraint -0.5 |
| Full harness should not be ported | Verified | Postmortem: prescriptive harness produced 0 feasible candidates |

## What Is Hypothesis (Not Yet Validated)

1. **6 actions is enough** to reach or improve P1 feasibility from a rotating-ellipse starting point. Must validate by manual playtest immediately.
2. **Discretized rotating-ellipse perturbations** create non-trivial decision pressure (not too easy, not impossible).
3. **Low-fidelity metrics** are close enough to high-fidelity P1 scoring that low-fi reward signal is meaningful.
4. **The Docker image** builds and deploys on HF Spaces within reasonable time/size limits.

## Environment Design

### Single Task

Improve a stellarator boundary's P1 score using the rotating-ellipse parameterization under the official ConStellaration P1 constraints.

### P1 Constraints (from `GeometricalProblem`)

- aspect_ratio <= 4.0
- average_triangularity <= -0.5
- edge_rotational_transform / n_field_periods >= 0.3

### P1 Objective

Minimize `max_elongation`. Score = `1 - clip((max_elongation - 1) / 9, 0, 1)`.

Feasibility tolerance: normalized constraint violations <= 1% (0.01).

### Parameter Space

The rotating-ellipse generator takes 3 continuous parameters + 1 discrete:

| Parameter | Role | Typical range |
|---|---|---|
| `aspect_ratio` | Width-to-height ratio of the boundary | 2.0 - 8.0 |
| `elongation` | Vertical stretching of cross-section | 1.0 - 5.0 |
| `rotational_transform` | Magnetic field line winding | 0.1 - 1.0 |
| `n_field_periods` | Fixed at 3 (not an action) | 3 |

These map to `constellaration.initial_guess.generate_rotating_ellipse(aspect_ratio, elongation, rotational_transform, n_field_periods)` which returns a `SurfaceRZFourier` boundary in ~4ms.

### Action Space

Discrete perturbations on the 3 rotating-ellipse parameters:

```
intent: "run" | "submit" | "restore_best"
operator: "aspect_ratio" | "elongation" | "rotational_transform"
direction: "increase" | "decrease"
magnitude: "small" | "medium" | "large"
```

Magnitude deltas (to be tuned by playtest):

| Parameter | small | medium | large |
|---|---|---|---|
| aspect_ratio | 0.1 | 0.3 | 0.8 |
| elongation | 0.1 | 0.3 | 0.8 |
| rotational_transform | 0.02 | 0.05 | 0.15 |

### Episode Flow

1. Reset: generate initial boundary from baseline rotating-ellipse parameters (+ optional seed perturbation). Run low-fi forward_model. Return initial observation.
2. Agent chooses action.
3. If `run`: modify parameter, regenerate boundary, run low-fi forward_model (~0.6s). Return diagnostics + reward.
4. If `restore_best`: revert to best-known parameters. No VMEC cost, but costs a budget step.
5. If `submit`: end episode. Optionally run high-fi for final score.
6. Episode ends on `submit` or budget exhaustion.

### Budget

6 evaluations per episode. All non-submit actions cost 1 budget.

### Observation

```
diagnostics_text: str          # human-readable summary
max_elongation: float          # P1 objective (minimize)
aspect_ratio: float            # constraint: <= 4.0
average_triangularity: float   # constraint: <= -0.5
edge_iota_over_nfp: float     # constraint: >= 0.3
p1_score: float                # official P1 score (0 if infeasible)
p1_feasibility: float          # max normalized constraint violation
constraints_satisfied: bool    # feasibility <= 0.01
vacuum_well: float             # stability indicator
step_number: int
budget_remaining: int
best_score: float
target_spec: str
```

### Reward V0

Feasibility-first, then objective improvement:

```
if constraints newly satisfied:
    +3.0
if constraints newly violated:
    -3.0

if feasible:
    reward += (prev_elongation - curr_elongation) * 10.0  # improvement in objective
else:
    reward += (prev_feasibility - curr_feasibility) * 5.0  # progress toward feasibility

per-step cost: -0.1

submit bonus (if feasible and improved):
    +5.0 * improvement_ratio + 1.0 * budget_efficiency
submit penalty (if infeasible or no improvement):
    -1.0
```

This puts feasibility first. An agent that achieves feasibility then minimizes elongation gets rewarded. An agent that never reaches feasibility gets penalized.

### State

```
step_count: int
current_params: {aspect_ratio, elongation, rotational_transform}
best_params: {aspect_ratio, elongation, rotational_transform}
initial_score: float
best_score: float
best_feasibility: float
history: list[str]
```

## Two Designs That Were Considered

| | Rotating-ellipse env | Curated-seed Fourier-repair env |
|---|---|---|
| Action space | 3 parameters (AR, elongation, iota) | N Fourier modes |
| Starting point | Generated from parameters | Frozen from HF dataset |
| Interpretability | High — parameters map to physical shape | Lower — mode perturbations are abstract |
| Dataset dependency | None at runtime | Requires offline curation |
| Search space coverage | Low-dimensional subfamily | Full boundary space |
| Hackathon viability | High | Medium (needs pre-work) |

**Decision:** Rotating-ellipse for the hackathon. It is self-contained, human-playable, and proven as a viable entry point for P1.

**What it does NOT claim:** Full coverage of the P1 boundary design space. This is a tradeoff accepted for hackathon scope.

## Implementation Order

### Phase 1: Physics Backend (~1 hour)

Status: done.

Rewrite `server/physics.py` to wrap:
- `constellaration.initial_guess.generate_rotating_ellipse` for boundary generation
- `constellaration.forward_model.forward_model` with low-fi settings for evaluation
- `constellaration.problems.GeometricalProblem` for official P1 scoring on every evaluation

### Phase 2: Environment Contract (~1 hour)

Status: done.

Update `server/environment.py`:
- New observation schema with P1 metrics
- New action schema for rotating-ellipse perturbations
- Reward V0 with feasibility-first logic
- Terminal conditions

Update `fusion_lab/models.py` for new schemas.

### Phase 3: Manual Playtest (~30 min)

Status: open.

Validate hypothesis: "6 actions is enough."
- Play 5-10 episodes manually
- Log: can a human reach feasibility? Improve elongation?
- Tune magnitude deltas if needed
- Document at least one pathology or adjustment

### Phase 4: Baselines (~30 min)

Status: partial. Baselines exist, but the heuristic needs refresh on the real verifier path.

- Random agent
- Heuristic agent (greedy toward known-good parameter region)
- Comparison table

### Phase 5: Deploy + Evidence (~2 hours)

Status: open.

- Update Dockerfile/deps for constellaration
- `openenv validate` + `openenv push`
- Colab notebook connecting to live environment
- 1-minute demo video

This section exists to justify the pivot with an implementation path. It should not trigger another strategy pass when the same work is already covered by the SSOT plan and checklist.

## Fallback

If full high-fidelity `constellaration` deployment fails (Docker build, HF Spaces issues):
- Keep the low-fidelity `constellaration` run path working
- Fall back to a low-fidelity-only hosted environment and document the limitation clearly
- Do not spend more than 1 hour debugging deployment before falling back

## Known-Good Fixtures

Start with 1-2 rotating-ellipse configurations for sanity checks and expand only if the implementation needs more coverage:

1. **Repairable baseline anchor:** aspect_ratio=3.5, elongation=1.5, rotational_transform=0.4 — intentionally infeasible at reset but close enough to support short repair/improvement episodes
1. **Current default baseline reference:** aspect_ratio=3.5, elongation=1.5, rotational_transform=0.4 — currently deeply infeasible on the real verifier path; keep as a negative or repair reference only
2. **Infeasible reference:** aspect_ratio=5.0, elongation=3.0, rotational_transform=0.2 — expected to violate constraints
3. **Near-boundary anchor:** still needs to be found from real verifier probing before manual playtesting

These are for verifier/reward sanity, not a prerequisite seed-mining project.

## What Not To Do

- Do not port the full ai-sci-feasible-designs harness or governor stack.
- Do not make the task "agent writes arbitrary optimization scripts."
- Do not stream the full HF dataset at runtime.
- Do not mix rotating-ellipse and Fourier-repair action spaces.
- Do not use high-fidelity eval for interactive steps (24s is too slow).
- Do not narrate "6 actions is enough" as validated until manually playtested.
- Do not claim full P1 boundary space coverage. The env uses a low-dim subfamily.
- Do not reopen the task-selection debate after the pivot is already accepted unless a blocker forces it.
