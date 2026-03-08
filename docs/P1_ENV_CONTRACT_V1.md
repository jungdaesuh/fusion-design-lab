# P1 Environment Contract V1

**Role:** Live technical contract SSOT for the current implementation phase
**Planning dependency:** [`FUSION_DESIGN_LAB_PLAN_V2.md`](FUSION_DESIGN_LAB_PLAN_V2.md)
**Evidence dependency:** [`P1_PARAMETERIZATION_DEEPDIVE.md`](P1_PARAMETERIZATION_DEEPDIVE.md)

## 1. Scope

This document defines the live technical contract for:

- [`server/physics.py`](../server/physics.py)
- [`fusion_lab/models.py`](../fusion_lab/models.py)
- [`server/environment.py`](../server/environment.py)
- [`server/app.py`](../server/app.py)

If the observation schema, action schema, episode flow, terminal conditions, or reward semantics change, update this file in the same task.

## 2. Design Split

Keep three layers separate:

1. boundary builder
2. official verifier
3. environment

Boundary builder owns:

- the repaired low-dimensional family
- rotating-ellipse seed generation
- explicit triangularity control injection

Official verifier owns:

- boundary in, metrics out
- official `P1` feasibility semantics
- objective direction and score ordering
- low-fidelity and high-fidelity evaluation modes
- explicit failure results when VMEC or forward-model evaluation fails

Environment owns:

- reset pool
- discrete actions
- episode budget
- best-state tracking
- reward shaping

## 3. Boundary Family

The historical 3-knob upstream rotating-ellipse family is not the live contract.

The live controllable knobs are:

- `aspect_ratio`
- `elongation`
- `rotational_transform`
- `triangularity_scale`

Rules:

- stay low-dimensional and human-playable
- treat the current family as rotating-ellipse-derived, not plain upstream rotating ellipse
- the coarse measured sweep is now recorded, but reset-seed changes and any budget changes should still wait for paired high-fidelity fixture checks

## 4. Action Contract

`intent` is one of:

- `run`
- `submit`
- `restore_best`

For `run`, the action also includes:

- `parameter`: one of `aspect_ratio | elongation | rotational_transform | triangularity_scale`
- `direction`: `increase | decrease`
- `magnitude`: `small | medium | large`

Constraints:

- keep the discrete interaction style
- do not expose the full Fourier action space as the primary environment
- do not use action complexity to compensate for missing clarity elsewhere

## 5. Observation Contract

The observation must stay metric-centered and human-readable.

Required fields:

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
- `reward_breakdown`
- `action_monitor`
- `episode_total_reward`
- `trajectory_summary`

Interpretation rules:

- low-fidelity `run` metrics must be labeled as low-fidelity
- high-fidelity `submit` metrics must be labeled as high-fidelity
- low-fidelity and high-fidelity best-state reporting must stay separate
- the observation must be understandable without hidden state
- reward telemetry must expose which bonuses, penalties, and shaping terms contributed to the scalar reward
- action telemetry must expose parameter values before and after the action, including clamped and no-op moves

## 6. Episode Flow

1. Reset from one frozen repaired-family seed or a small frozen seed set.
2. Evaluate the initial state with low fidelity and return the first observation.
3. On `run`, perturb one controllable parameter and re-evaluate with low fidelity.
4. On `restore_best`, revert to the best known low-fidelity state, re-evaluate, and consume budget.
5. On `submit`, end the episode and run the high-fidelity submit evaluation.
6. End the episode on `submit` or budget exhaustion.

Failure semantics:

- failed evaluations still consume budget
- failed evaluations produce visible failure observations
- failed evaluations apply a documented penalty
- the environment must not silently convert failures into success paths

## 7. Terminal Contract

At termination, the environment must provide:

- final best design metrics
- final feasibility status
- total reward
- a short human-readable trajectory summary
- the final reward breakdown and action telemetry for the terminal step

Terminal reporting rules:

- keep submit-time reporting fidelity-consistent
- do not compare high-fidelity submit results against low-fidelity baseline state as if they were the same truth surface

## 8. Verifier Contract

The verifier of record is `constellaration.problems.GeometricalProblem`.

The implementation must preserve:

- objective direction
- constraint direction
- feasibility semantics
- score ordering

The verifier should stay boundary-based:

- `build_boundary_from_params(...) -> SurfaceRZFourier`
- `evaluate_boundary(boundary, fidelity) -> EvaluationMetrics`

Do not treat parameterization-specific logic as verifier truth.

VMEC preset mapping:

- `run` steps use the `low_fidelity` VMEC preset (~0.6s, tolerant convergence)
- `submit` uses the `from_boundary_resolution` VMEC preset (~4s, adaptive convergence matching boundary Fourier resolution)
- the `high_fidelity` VMEC preset (minimum 10 modes, strict convergence) is not used because it does not converge on the current `mpol=3, ntor=3` boundaries

Training and evaluation rule:

- use low-fidelity `run` as the RL inner-loop surface
- keep higher-fidelity `submit` for terminal truth, paired fixture checks, submit-side manual traces, and sparse checkpoint evaluation
- do not move VMEC-backed submit evaluation into every training step unless the contract is deliberately redefined

## 9. Reward V0

`Reward V0` is the live reward contract until playtesting proves a concrete pathology.

Target behavior:

- infeasible to feasible crossing gets a clear positive bonus
- feasible to infeasible regression gets a clear penalty
- when both states are infeasible, reduced official feasibility violation should help
- when both states are feasible, lower `max_elongation` should help
- non-submit actions pay a small step cost
- `submit` should be better than passive exhaustion when the design is genuinely improved
- recovery after a failed evaluation may receive a modest bounded bonus

Rules:

- keep reward scalar and verifier-driven
- do not add mode-specific or parameter-specific reward shaping
- do not use reward complexity to compensate for blocked parameterization, poor seeds, or unclear observations

## 10. Reset and Fixture Policy

Reset policy:

- start with exact frozen seeds
- keep `n_field_periods = 3`
- prefer a small reproducible seed set

Each seed should be:

- reproducible
- near enough to the feasible boundary to make the budget meaningful
- not already solved

Fixture policy:

- track good, boundary, and clearly bad references
- use fixtures for verifier and reward sanity checks
- do not turn fixture mining into a separate broad project

## 11. Open Measurements

These items remain open until measured on the repaired family:

- exact repaired-family range bounds
- exact `triangularity_scale` deltas
- exact `rotational_transform` bounds
- exact reset seed pool
- whether the budget should stay at 6 or change

## 12. Out of Scope

- porting the old `ai-sci-feasible-designs` harness
- broad Fourier-mode action space as the main environment
- complicated reward shaping before playtest evidence
- a wider task family than the single stellarator environment
