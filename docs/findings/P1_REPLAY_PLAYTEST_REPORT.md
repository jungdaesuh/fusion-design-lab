# P1 Replay Playtest Report

Date: 2026-03-07

## Purpose

Expand reward branch coverage beyond the initial manual playtest (Episodes A-B in
`P1_MANUAL_PLAYTEST_LOG.md`). That log covered 1 seed, 2 episodes, 3 steps.
This replay covers all 3 seeds, 5 episodes, 27 steps, and exercises every
reward branch in `server/environment.py:_compute_reward`.

## Method

Script: `baselines/replay_playtest.py`

- direct `StellaratorEnvironment` instantiation (no server)
- fixed action sequences for reproducibility
- same pattern as `baselines/random_agent.py` and `baselines/heuristic_agent.py`

## Episode results

### Episode 1: seed 0 — repair + objective shaping + budget exhaustion

Start: `ar=3.6, elong=1.4, rt=1.5, tri=0.55`, feasibility=0.050653, score=0.0

| Step | Action | Reward | Score | Feasibility | Elongation | Status | Budget |
|------|--------|--------|-------|-------------|------------|--------|--------|
| 1 | rt increase medium | -0.1000 | 0.000000 | 0.050653 | 6.7295 | viol | 5 |
| 2 | tri increase medium | +3.1533 | 0.291660 | 0.000000 | 7.3751 | OK | 4 |
| 3 | elong decrease small | +0.2665 | 0.295731 | 0.000865 | 7.3384 | OK | 3 |
| 4 | elong decrease small | -2.1000 | 0.000000 | 1000000 | 10.0000 | FAIL | 2 |
| 5 | elong decrease small | -2.1000 | 0.000000 | 1000000 | 10.0000 | FAIL | 1 |
| 6 | elong decrease small | +2.5350 | 0.307074 | 0.004561 | 7.2363 | OK | 0 |

Total reward: +1.6548

Branches exercised:
- feasibility crossing bonus (+3.0, step 2)
- feasible-side elongation shaping (step 3)
- VMEC failure penalty (-2.1, steps 4-5)
- recovery bonus (+1.0, step 6)
- budget exhaustion done-time improvement bonus (step 6)

Finding: **elongation crash pocket at elong ~1.30-1.25**. Steps 4-5 crashed
during low-fi evaluation after decreasing elongation from 1.35 to 1.30 and 1.25.
Recovery occurred at elong=1.20 (step 6). This crash zone is within the
documented parameter range `(1.2, 1.8)` and is not mapped in the measured sweep.

### Episode 2: seed 1 — repair from different seed

Start: `ar=3.4, elong=1.4, rt=1.6, tri=0.55`, feasibility=0.050653, score=0.0

| Step | Action | Reward | Score | Feasibility | Elongation | Status | Budget |
|------|--------|--------|-------|-------------|------------|--------|--------|
| 1 | rt increase medium | -0.1000 | 0.000000 | 0.050653 | 6.8493 | viol | 5 |
| 2 | tri increase medium | +3.1042 | 0.276209 | 0.009819 | 7.5141 | OK | 4 |
| 3 | elong decrease small | +0.2824 | 0.280458 | 0.001415 | 7.4759 | OK | 3 |
| 4 | elong decrease small | +0.2724 | 0.284596 | 0.002252 | 7.4386 | OK | 2 |
| 5 | elong decrease small | +0.2557 | 0.288548 | 0.003499 | 7.4031 | OK | 1 |
| 6 | elong decrease small | +0.8212 | 0.292289 | 0.004561 | 7.3694 | OK | 0 |

Total reward: +4.6359

Branches exercised:
- feasibility crossing from a non-default seed (step 2)
- sustained feasible-side elongation shaping (steps 3-6)
- budget exhaustion done-time improvement bonus (step 6)

Finding: **cleanest full-episode success**. Six consecutive successful
evaluations, monotonic score improvement, positive reward every step after
crossing. Confirms that the repair+optimize arc is legible across a full episode
from seed 1.

### Episode 3: seed 2 — boundary clamping + feasibility regression

Start: `ar=3.8, elong=1.4, rt=1.5, tri=0.55`, feasibility=0.050653, score=0.0

| Step | Action | Reward | Score | Feasibility | Elongation | Status | Budget |
|------|--------|--------|-------|-------------|------------|--------|--------|
| 1 | ar increase large | -0.1000 | 0.000000 | 0.050653 | 6.5502 | viol | 5 |
| 2 | tri increase medium | +3.1533 | 0.314255 | 0.000000 | 7.1717 | OK | 4 |
| 3 | tri increase medium | -3.3598 | 0.000000 | 0.051950 | 7.8596 | viol | 3 |
| 4 | elong decrease small | -0.0715 | 0.000000 | 0.046243 | 7.8309 | viol | 2 |
| 5 | ar decrease large | -0.4932 | 0.000000 | 0.124880 | 7.3386 | viol | 1 |
| 6 | elong decrease small | -0.5650 | 0.000000 | 0.117873 | 7.3091 | viol | 0 |

Total reward: -1.4362

Branches exercised:
- boundary clamping (step 1: ar=3.8 + 0.2 clamped at 3.8, no physics change, reward = step cost only)
- feasibility crossing bonus (+3.0, step 2)
- **feasibility regression penalty** (-3.0, step 3: pushed tri too far, lost feasibility)
- infeasible feasibility shaping (steps 4-6)
- budget exhaustion done-time penalty (step 6: not improved)

Finding: **feasibility is non-monotonic in triangularity_scale**. Crossing at
tri=0.60 (score=0.314), but tri=0.65 breaks feasibility (feas=0.052). The
feasible zone is a narrow band, not an open region. The regression penalty
(-3.36 total) is clearly legible.

### Episode 4: seed 0 — crash recovery + restore_best

Start: `ar=3.6, elong=1.4, rt=1.5, tri=0.55`, feasibility=0.050653, score=0.0

| Step | Action | Reward | Score | Feasibility | Elongation | Status | Budget |
|------|--------|--------|-------|-------------|------------|--------|--------|
| 1 | tri increase medium | -0.2593 | 0.000000 | 0.082515 | 6.7218 | viol | 5 |
| 2 | rt increase large | +3.3126 | 0.210239 | 0.000000 | 8.1079 | OK | 4 |
| 3 | rt increase large | -2.1000 | 0.000000 | 1000000 | 10.0000 | FAIL | 3 |
| 4 | restore_best | +0.9000 | 0.210239 | 0.000000 | 8.1079 | OK | 2 |
| 5 | elong decrease small | +0.2541 | 0.214174 | 0.000865 | 8.0724 | OK | 1 |
| 6 | elong decrease small | +0.6821 | 0.218018 | 0.002252 | 8.0378 | OK | 0 |

Total reward: +2.7895

Branches exercised:
- infeasible feasibility shaping (step 1: tri alone worsened feasibility)
- feasibility crossing via large rt jump (step 2)
- **VMEC failure at rt=1.9** (-2.1, step 3: crash zone as documented in sweep report)
- **restore_best + recovery bonus** (+0.9, step 4: reverts to best-known state, +1.0 recovery -0.1 step cost)
- feasible-side elongation shaping (steps 5-6)
- budget exhaustion done-time improvement bonus (step 6)

Finding: **restore_best works correctly** and the recovery bonus (+1.0) is
legible. After reverting from a VMEC crash, the agent can continue improving
from its saved best state.

Note: step 1 reveals that `triangularity_scale increase medium` alone (without
a preceding rt increase) **worsens** feasibility for seed 0. The feasibility
boundary is a multi-parameter surface, not a single-knob threshold.

### Episode 5: seed 0 — repair + objective move + explicit submit

Start: `ar=3.6, elong=1.4, rt=1.5, tri=0.55`, feasibility=0.050653, score=0.0

| Step | Action | Reward | Score | Feasibility | Elongation | Status | Budget |
|------|--------|--------|-------|-------------|------------|--------|--------|
| 1 | rt increase medium | -0.1000 | 0.000000 | 0.050653 | 6.7295 | viol | 5 |
| 2 | tri increase medium | +3.1533 | 0.291660 | 0.000000 | 7.3751 | OK | 4 |
| 3 | elong decrease small | +0.2665 | 0.295731 | 0.000865 | 7.3384 | OK | 3 |
| 4 | submit | -3.0000 | 0.000000 | 1000000 | 10.0000 | FAIL | 3 |

Total reward: +0.3198

Branches exercised:
- feasibility crossing (step 2)
- feasible-side elongation shaping (step 3)
- **submit high-fidelity evaluation** (step 4)
- **submit failure penalty** (-3.0, step 4: VMEC crash at high fidelity)

Finding: **cross-fidelity gap confirmed**. The state at
`(ar=3.6, elong=1.35, rt=1.6, tri=0.60)` passes low-fidelity evaluation
(step 3: score=0.296, constraints satisfied) but **crashes at high-fidelity
evaluation** (step 4: VMEC failure). The low-fi repair story does not survive
the real final check for this particular path.

## Reward branch coverage summary

| Branch | Code reference | First run | This replay |
|--------|---------------|-----------|-------------|
| Feasibility crossing bonus (+3.0) | `environment.py:235-236` | Ep A step 2 | Ep 1-4 |
| Feasibility regression penalty (-3.0) | `environment.py:237-238` | not tested | Ep 3 step 3 |
| Feasible-side elongation shaping | `environment.py:240-241` | not tested | Ep 1-2, Ep 4 |
| Infeasible feasibility shaping | `environment.py:242-243` | Ep A step 1 | Ep 3 steps 4-6 |
| Step cost (-0.1) | `environment.py:245-246` | Ep A step 1 | all run steps |
| VMEC failure penalty (-2.1) | `environment.py:223-226` | not tested | Ep 1 steps 4-5, Ep 4 step 3 |
| Submit failure penalty (-3.0) | `environment.py:227-228` | not tested | Ep 5 step 4 |
| Budget exhaustion done-penalty | `environment.py:264-265` | not tested | Ep 3 step 6 |
| Recovery bonus (+1.0) | `environment.py:248-249` | not tested | Ep 1 step 6, Ep 4 step 4 |
| Budget exhaustion done-bonus | `environment.py:258-263` | not tested | Ep 1 step 6, Ep 2 step 6, Ep 4 step 6 |
| Submit improvement bonus | `environment.py:260-261` | not tested | not triggered (submit crashed) |
| Clamping (no physics change) | `environment.py:412-414` | not tested | Ep 3 step 1 |
| restore_best | `environment.py:175-195` | not tested | Ep 4 step 4 |

Coverage: 12 of 13 branches exercised. The only untested branch is the
**submit improvement bonus** (submit from a state that is feasible at high
fidelity). This requires finding a repair path that survives high-fi first.

## Critical findings

### 1. Cross-fidelity gap is real (Episode 5)

The canonical repair path from seed 0 (increase rt medium, increase tri medium,
decrease elong small) produces a low-fi feasible state that crashes at high
fidelity. This confirms the concern documented in `P1_MANUAL_PLAYTEST_LOG.md`
line 53 and `FUSION_DESIGN_LAB_PLAN_V2.md` open items.

Implication: no currently tested repair path from seed 0 has a known-good
high-fidelity submit. The submit improvement bonus branch cannot be exercised
until a cross-fidelity-safe path is found.

### 2. Elongation crash pocket (Episode 1)

VMEC crashes at `elongation ~1.25-1.30` during low-fi evaluation, with recovery
at `elongation=1.20`. This crash zone is inside the documented parameter range
`(1.2, 1.8)` and was not discovered by the measured sweep (which only varied
`rotational_transform` and `triangularity_scale` in the targeted grid).

Implication: the elongation dimension has internal crash pockets that the
current sweep does not map. Agents that decrease elongation aggressively will
hit unexpected crashes.

### 3. Feasibility boundary is multi-parametric (Episode 4 step 1)

`triangularity_scale increase medium` alone worsens feasibility for seed 0
(0.051 to 0.083). The original manual playtest crossed feasibility only because
`rotational_transform` was already increased to 1.6 first. The feasibility
boundary is a surface in 4D parameter space, not a threshold on a single knob.

### 4. Feasibility is non-monotonic in triangularity (Episode 3 steps 2-3)

`triangularity_scale=0.60` is feasible but `0.65` is not (from seed 2). The
feasible zone is a narrow band. Pushing a single knob further does not
monotonically improve the design.

## Comparison with initial manual playtest

| Property | Initial (Ep A-B) | This replay |
|----------|------------------|-------------|
| Seeds tested | 1 (seed 0) | 3 (seeds 0, 1, 2) |
| Episodes | 2 | 5 |
| Total steps | 3 | 27 |
| Reward branches covered | 3 of 13 | 12 of 13 |
| Feasible-side shaping | not tested | confirmed legible |
| VMEC crash handling | not tested | confirmed legible |
| restore_best | not tested | confirmed working |
| Submit tested | no | yes (crashed at high-fi) |
| Cross-fidelity evidence | none | gap confirmed |

## Open items

1. **Find a high-fi-safe repair path** to exercise the submit improvement bonus
   (the last uncovered branch) and provide positive submit-side evidence.
2. **Map the elongation crash pocket** with a targeted sweep over the elongation
   dimension at feasible parameter combinations.
3. **Update the measured sweep report** to document the elongation crash zone.
4. **Consider narrowing `elongation` range** or documenting the crash pocket as
   a known hazard in the environment contract.
