# Verifier And Reward Review

Date: 2026-03-08

## Scope

This note reviews how well the current verifier path and reward function serve the repo's stated goal:

- ship one clear, reproducible OpenEnv environment for budget-constrained stellarator design
- keep the verifier official
- keep the task human-playable
- keep reward explainable and iteratively improved

Primary review targets:

- [FUSION_DESIGN_LAB_PLAN_V2.md](./FUSION_DESIGN_LAB_PLAN_V2.md)
- [P1_ENV_CONTRACT_V1.md](./P1_ENV_CONTRACT_V1.md)
- [server/physics.py](../server/physics.py)
- [server/environment.py](../server/environment.py)
- recent history from `d58c100` through `6deaccc`

## Executive Summary

The verifier implementation is directionally strong and mostly correct now. The major March 7, 2026 commit sequence fixed the important correctness problems:

- replaced the synthetic evaluator with real `constellaration` / `GeometricalProblem`
- repaired the blocked 3-knob family by adding explicit triangularity control
- separated low-fidelity `run` truth from high-fidelity `submit` truth
- fixed the post-VMEC-failure recovery reward bug

The reward is also directionally good. `Reward V0` remains simple, mostly verifier-driven, and aligned with the repo docs.

The main gap is no longer basic verifier wiring. The main gap is that the repo still lacks the validation evidence that its own docs require before calling the environment "good":

- no tracked fixtures
- no manual playtest log
- no documented reward pathology/fix or explicit "Reward V0 survived playtest" note

## Validated Findings

### 1. Missing validation artifacts are still the biggest repo-level gap

The planning docs explicitly say the environment artifact is the product, not just the code. Current repo state still lacks:

- tracked `P1` fixtures
- manual playtest evidence
- a documented `Reward V0 -> V1` change, or an explicit record that `Reward V0` survived playtesting unchanged

Relevant references:

- [FUSION_DESIGN_LAB_PLAN_V2.md](./FUSION_DESIGN_LAB_PLAN_V2.md)
- [FUSION_DELIVERABLES_MAP.md](./FUSION_DELIVERABLES_MAP.md)
- [server/data/p1/README.md](../server/data/p1/README.md)

### 2. Observation legibility still conflicts with the official tolerance semantics

The env prints hard constraint thresholds in diagnostics, but actual feasibility is decided by `GeometricalProblem.is_feasible()` using the official 1% tolerance.

That means a human can see:

- a printed bound like `edge_iota_over_nfp >= 0.3`
- a reported value slightly below `0.3`
- `constraints=SATISFIED`

This is a direct usability problem for a repo whose goal is a legible, human-playable environment.

Relevant references:

- [server/environment.py](../server/environment.py) in `_build_observation(...)`
- [server/physics.py](../server/physics.py) in `_to_evaluation_metrics(...)`
- [P1_PARAMETERIZATION_DEEPDIVE.md](./P1_PARAMETERIZATION_DEEPDIVE.md)

### 3. High-fidelity best-state bookkeeping is still not trustworthy

`best_high_fidelity_score` and `best_high_fidelity_feasibility` are not true best high-fidelity values. On submit, the env can overwrite them by reevaluating `best_params`, even if the current submit is the best actual high-fidelity result.

The worst failure mode is sharper than simple bookkeeping drift: if reevaluating `best_params` crashes VMEC, the env can store failure-sentinel data under `best_high_fidelity_*`, including `p1_score=0.0`, while still labeling that state as "best."

This weakens the clean low-fi/high-fi split the contract calls for.

Relevant references:

- [server/environment.py](../server/environment.py) in `_refresh_best_high_fidelity_metrics(...)`
- [server/environment.py](../server/environment.py) in `_summary_submit(...)`
- [P1_ENV_CONTRACT_V1.md](./P1_ENV_CONTRACT_V1.md)

### 4. Submit is operationally expensive

One `submit` can trigger up to three high-fidelity evaluations:

1. current design
2. initial high-fidelity reference
3. reevaluated `best_params`

The initial high-fidelity reference cache is only per episode because it lives on `State`, which is recreated on every `reset()`. In practice, repeated episodes still repay that cost.

That makes baseline comparison and manual validation much slower than the task surface implies.

Relevant references:

- [server/environment.py](../server/environment.py) in `_handle_submit(...)`
- [server/environment.py](../server/environment.py) in `_initial_high_fidelity_score(...)`

### 5. Heuristic baseline evidence is stale and currently unconvincing

The current heuristic is not validated on the repaired 4-knob family and is already documented in repo status notes as underperforming random on the real verifier path.

This is not a verifier bug, but it is a serious artifact-quality problem for a repo that needs credible baseline evidence.

Relevant references:

- [README.md](../README.md)
- [TODO.md](../TODO.md)

### 6. Baseline comparison does not reject failed high-fidelity submits

[baselines/compare.py](../baselines/compare.py) in `_require_submit_fidelity(...)` only checks that the final step used high-fidelity evaluation. It does not check whether that high-fidelity submit succeeded.

That means a failed submit can still count as a terminal high-fi result in comparison output.

### 7. Verifier failure normalization is incomplete

[server/physics.py](../server/physics.py) in `evaluate_boundary(...)` converts `RuntimeError` into explicit failure metrics, but other exception types can still crash the env instead of producing documented failure observations.

### 8. Submit budget reporting is inconsistent

`submit` does not decrement `budget_remaining`, so the terminal observation shows pre-submit budget. Since `submit` is terminal, this is not a serious episode-flow bug, but it is a contract/reporting inconsistency.

Relevant reference:

- [server/environment.py](../server/environment.py) in `_handle_submit(...)`

### 9. Minor maintenance smells

- [server/app.py](../server/app.py) imports `N_FIELD_PERIODS` indirectly via `server.environment` instead of directly from `server.contract`
- [fusion_lab/models.py](../fusion_lab/models.py) has misleading defaults if used outside the environment

## Findings From The Quoted External Review

### Confirmed

- submit cost is real
- heuristic baseline is stale
- `compare.py` should check failed submits explicitly
- `app.py` re-export dependency is fragile
- observation defaults are mildly misleading

### Partially Confirmed

- submit budget reporting is inconsistent, but it does not allow the agent to exceed the episode budget because submit is terminal

### Fragile Coupling, Not A Reproduced Live Bug

The quoted review's highest-severity claim was an `_update_best` feasibility mismatch between:

- `constraints_satisfied`
- `p1_feasibility <= FEASIBILITY_TOLERANCE`

I did not reproduce that as a current live bug. I sampled 30 low-fidelity evaluations across the current parameter ranges and found zero mismatches between those two criteria.

But the current code still represents a fragile coupling: `_update_best(...)` uses one concept through `constraints_satisfied` for `current`, and a separate hardcoded `FEASIBILITY_TOLERANCE` comparison for `best`. Those happen to agree today because current `constellaration` semantics line up with `compute_feasibility() <= 0.01`.

That means this is best described as:

- not a reproduced live bug on current `HEAD`
- still a maintainability risk if upstream tolerance semantics ever drift

Relevant reference:

- [server/environment.py](../server/environment.py) in `_update_best(...)`

## Validation Performed

### Compile smoke

Passed:

```bash
uv run python -m py_compile fusion_lab/models.py fusion_lab/client.py server/environment.py server/app.py server/physics.py
```

### Reset-seed sanity check

All three current reset seeds start low-fidelity infeasible at about:

- `p1_feasibility ~= 0.05065`

So the task is not trivially solved at reset.

### Sampled low-fidelity trajectory

For seed `0`, the following low-fidelity sequence reached feasibility within 5 steps:

1. `triangularity_scale increase small`
2. `triangularity_scale increase small`
3. `triangularity_scale increase small`
4. `rotational_transform increase small`
5. `rotational_transform increase small`

The feasibility-crossing step received a strong positive reward (`+3.1054`).

This is a good sign for current `Reward V0` ordering, but it is not a substitute for the fixture/manual-playtest loop the docs require.

One additional playtest note: reward stacking should be checked explicitly. A single step can combine:

- recovery bonus `+1.0`
- feasibility transition bonus `+3.0`
- shaping delta
- non-submit step cost `-0.1`

That is not obviously wrong, but it can produce a `+4.0+` step and should be verified during manual playtesting.

### Current workspace state at review time

The workspace was dirty during review:

- modified [training/notebooks/northflank_smoke.py](../training/notebooks/northflank_smoke.py)
- untracked [baselines/measured_sweep.py](../baselines/measured_sweep.py)
- untracked `baselines/sweep_results/`

These were treated as workspace observations, not committed `HEAD` findings.

## Commit-History Update

Recent history is directionally good and mostly coherent:

- `d58c100` made the verifier real by switching to `constellaration`
- `fe3a41d` repaired the parameterization and added explicit VMEC failure semantics
- `88d9b78` fixed submit-time mixed-fidelity reward/reporting
- `eb446cf` fixed the post-failure recovery reward bug
- `6deaccc` cleaned up contract naming and tightened baseline reporting

The current issues are mostly:

- clarity
- bookkeeping
- operational cost
- missing validation artifacts

not a fundamental verifier-wiring failure

## Current Assessment

### Verifier

Status: mostly implemented correctly, not fully productized

Strengths:

- official `GeometricalProblem` semantics
- boundary-based evaluation
- low-fi/high-fi split
- explicit VMEC failure metrics for common runtime failures

Weaknesses:

- hidden tolerance semantics in diagnostics
- incomplete exception normalization
- high-fidelity best-state tracking ambiguity

### Reward

Status: directionally good, still pre-validation

Strengths:

- scalar and verifier-driven
- feasibility-first
- objective shaping only after feasibility
- explicit failure penalty
- recovery reward no longer relies on failure sentinels
- explicit submit remains better than passive exhaustion

Weaknesses:

- not yet validated by the playtest/fixture loop the repo requires
- some reward/reporting details still depend on unclear high-fi bookkeeping
- reward stacking is still under-documented and should be checked during playtesting

## TODOs

### Highest Priority

1. Fix diagnostics so humans can understand official tolerance-based feasibility.
2. Fix true high-fidelity best-state bookkeeping.
3. Update [baselines/compare.py](../baselines/compare.py) to reject or explicitly flag failed high-fidelity submits.
4. Reduce submit-time high-fidelity reevaluation cost.

### Validation Priority

5. Add tracked `P1` fixtures under [server/data/p1/](../server/data/p1/).
6. Run fixture sanity checks for:
   - good or near-boundary cases
   - clearly bad cases
   - reward ordering
7. Run manual playtesting and record:
   - observation seen
   - action chosen
   - verifier outcome
   - reward returned
   - whether reward matched intuition
8. Either:
   - document the first real `Reward V0 -> V1` pathology/fix
   - or explicitly record that `Reward V0` survived playtesting unchanged
9. Refresh or replace the heuristic baseline after measured sweep, fixtures, and manual playtesting so the repo has credible baseline evidence on the repaired family.
   Success bar: the heuristic should at least be competitive with, and preferably beat, random on the repaired-family task.

### Secondary Cleanup

10. Decide whether submit should decrement `budget_remaining` for contract clarity.
11. Import `N_FIELD_PERIODS` in [server/app.py](../server/app.py) directly from `server.contract`.
12. Clean up or intentionally commit the current workspace-only baseline and notebook artifacts.

## Bottom Line

The verifier is no longer the main blocker. The repo has crossed the line from "not wired" to "mostly wired and mostly correct."

The next blocker is proving that the environment is actually a clear, reproducible, human-legible artifact through:

- fixtures
- playtesting
- reward-validation evidence

Until those exist, the verifier and reward should be described as strong `HEAD` implementations with remaining validation debt, not finished hackathon evidence.
