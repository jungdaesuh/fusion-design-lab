# P1 Environment Contract V1

**Status:** Technical contract with partial implementation now landed
**Role:** Supporting spec for the `P1` environment contract
**SSOT relationship:** This file refines [FUSION_DESIGN_LAB_PLAN_V2.md](FUSION_DESIGN_LAB_PLAN_V2.md). If this file conflicts with the planning SSOT, update both in the same task.

## Purpose

This file captures the technical contract that should drive the next code changes in:

- [server/physics.py](../server/physics.py)
- [fusion_lab/models.py](../fusion_lab/models.py)
- [server/environment.py](../server/environment.py)
- [server/app.py](../server/app.py)

The central change is now explicit:

- the historical upstream 3-knob rotating-ellipse family is blocked on P1 triangularity under the real verifier path
- that blocker drove the repair to the current 4-knob low-dimensional runtime
- the runtime now exposes the repaired 4-knob target, but measured sweep validation and fixture calibration are still pending

## Historical Blocker

This section records the resolved upstream blocker that motivated the current repair. It is not the live runtime state.

Current verified facts:

- upstream `generate_rotating_ellipse(aspect_ratio, elongation, rotational_transform, n_field_periods)` has no triangularity control
- the historical 3-knob environment directly exposed only:
  - `aspect_ratio`
  - `elongation`
  - `rotational_transform`
- real low-fidelity samples on the current verifier path kept:
  - `average_triangularity` at roughly `+0.004975`
  - `p1_feasibility` at roughly `1.00995`
  - feasible count at `0`

Conclusion:

- the historical 3-knob family was not a meaningful playtest or baseline environment for `P1`
- the live runtime therefore moved to a repaired boundary family before further reward iteration

## Design Split

Keep three layers separate:

1. **Boundary builder**
   - low-dimensional parameterization
   - rotating-ellipse seed generation
   - optional triangularity control injection
2. **Official verifier**
   - boundary in
   - metrics out
   - feasibility, objective, and score semantics from `GeometricalProblem`
3. **Environment**
   - reset pool
   - discrete actions
   - episode flow
   - reward shaping

## Verifier Plan

`server/physics.py` should expose a boundary-based verifier surface.

Current repo state:

- the live code now exposes a boundary builder plus boundary-based evaluator
- explicit failure results are returned when VMEC evaluation fails
- measured sweep validation is still pending

Current live functions:

- `build_boundary_from_params(...) -> SurfaceRZFourier`
- `evaluate_boundary(boundary, fidelity) -> EvaluationMetrics`

Current layering note:

- discrete perturbation application lives in `server/environment.py`
- there is no separate `apply_low_dim_perturbation(...)` helper in the live code

The verifier layer should own:

- low-fidelity step-time evaluation
- high-fidelity submit-time evaluation
- official `P1` feasibility semantics
- official `P1` objective direction
- score ordering
- explicit failure results when VMEC or forward-model evaluation fails

The verifier layer should not own:

- episode budget
- action semantics
- reward shaping
- “best so far” state

## Low-Dimensional Boundary Plan

Stay low-dimensional, not Fourier-first.

Target controllable knobs:

- `aspect_ratio`
- `elongation`
- `rotational_transform`
- `triangularity_scale`

Current measurement rule:

- do not lock exact repaired-family ranges or deltas from prose alone
- measure them on the repaired boundary family before presenting them as defaults
- especially treat `rotational_transform` bounds, `triangularity_scale` deltas, and budget changes as open until measured

Important naming rule:

- once triangularity is injected explicitly, stop describing the family as plain upstream “rotating ellipse”
- it becomes a custom low-dimensional boundary family derived from a rotating-ellipse seed

## Action Contract

Keep the discrete interaction style:

- `intent`: `run | submit | restore_best`
- `direction`: `increase | decrease`
- `magnitude`: `small | medium | large`

For `run`, the controllable parameter should be one of:

- `aspect_ratio`
- `elongation`
- `rotational_transform`
- `triangularity_scale`

This keeps the environment human-playable and aligned with the historical low-dimensional P1 path.

Current repo state:

- the live action schema now exposes:
  - `aspect_ratio`
  - `elongation`
  - `rotational_transform`
  - `triangularity_scale`

## Observation Contract

The observation should stay metric-centered and human-readable.

Keep:

- `max_elongation`
- `aspect_ratio`
- `average_triangularity`
- `edge_iota_over_nfp`
- `p1_feasibility`
- `p1_score`
- `constraints_satisfied`
- `vacuum_well`
- `evaluation_fidelity`
- `evaluation_failed`
- `failure_reason`
- `step_number`
- `budget_remaining`
- `best_low_fidelity_score`
- `best_low_fidelity_feasibility`
- `best_high_fidelity_score`
- `best_high_fidelity_feasibility`
- `target_spec`
- `diagnostics_text`

Add clarity about fidelity:

- low-fidelity step-time metrics should be labeled as such
- high-fidelity submit-time metrics should be labeled as such
- do not expose them as if they are the same truth surface
- the live runtime should expose separate low-fidelity and high-fidelity best-state fields instead of overloading one generic best-state metric

This can be done either by:

- separate observation fields, or
- explicit fidelity labels in `diagnostics_text`

The minimum requirement is that a reader can tell whether a metric came from low-fi `run` or high-fi `submit`.

Current repo state:

- the live observation surface now exposes evaluation fidelity and failure state
- the live observation surface now exposes separate low-fidelity and high-fidelity best-state fields
- terminal reward/reporting is now fidelity-consistent: `submit` compares against high-fi reference state instead of low-fi rollout score state

## Reward V0

Keep reward mostly scalar and verifier-driven.

Target structure:

- infeasible to feasible crossing:
  - clear positive bonus
- feasible to infeasible regression:
  - clear negative penalty
- both infeasible:
  - reward reduction in official feasibility scalar
- both feasible:
  - reward lower `max_elongation`
- non-submit step:
  - small step cost
- recovery after a failed evaluation:
  - modest positive signal for returning to a valid verifier result
  - do not compute this from the failed sentinel feasibility value
- explicit `submit`:
  - better than passive budget exhaustion when the design is improved

Do not add:

- reward terms tied to specific Fourier modes
- bonuses for matching a known winner
- hand-coded constraint tricks to hide a blocked action family

Do not use reward complexity to compensate for missing action expressivity or missing crash semantics.

Additional fidelity rule:

- do not compare a high-fidelity submit score against low-fidelity baseline state
- terminal reward and submit summaries should use a fidelity-consistent basis

## Reset Strategy

Start with frozen exact seeds, not jitter.

Reset pool policy:

- `n_field_periods = 3`
- small frozen seed set
- each seed must be:
  - reproducible
  - near enough to the feasible boundary that 6 steps is worth testing
  - not already solved

Add bounded jitter only if memorization becomes a real problem.

## Manual Playtest Gate

Do not move to heuristic redesign or reward tuning until this gate is passed.

Manual playtest questions:

- can a human tell which constraint is currently blocking progress?
- can a human choose a plausible next action?
- can a human reach or approach feasibility within the budget?
- does `submit` feel meaningfully different from passive exhaustion?

If the answer is no, fix:

- the boundary family
- the step magnitudes
- the seed pool
- the observation semantics around low-fi vs high-fi best-state reporting

before tuning reward further

## Implementation Order

1. Repair the low-dimensional boundary builder in [server/physics.py](../server/physics.py).
2. Split boundary construction from official boundary evaluation in [server/physics.py](../server/physics.py).
3. Update the action and state schema in [fusion_lab/models.py](../fusion_lab/models.py).
4. Update the episode loop and observation labeling in [server/environment.py](../server/environment.py).
5. Update the task summary and public action description in [server/app.py](../server/app.py).
6. Add explicit VMEC failure semantics in [server/environment.py](../server/environment.py).
7. Run a small measured sweep to choose ranges, deltas, and reset seeds.
8. Verify that observation semantics are human-readable and that low-fi versus high-fi best-state reporting is explicit.
9. Freeze 1-2 repaired low-dimensional fixtures.
10. Run manual playtesting.
11. Refresh the heuristic baseline only after that evidence exists.

## Out of Scope

- full Fourier-mode action space as the primary environment
- porting the old `ai-sci-feasible-designs` harness
- making reward more complex before the repaired low-dimensional family exists
- building a full benchmark split protocol before the environment is even playable
