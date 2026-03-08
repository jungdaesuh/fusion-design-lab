# P1 Parameterization Deep-Dive

**Date:** March 7, 2026
**Role:** Evidence and rationale record
**Status:** Supporting doc, not a live planning or contract SSOT

This document keeps the durable evidence behind the repaired low-dimensional `P1` environment:

- why the historical 3-knob family failed
- what the original winning session actually did
- what the recorded 4-knob sweep proved
- why the current environment is intentionally a playable stepping stone rather than a leaderboard-matching optimizer

## 1. Structural Blocker

### Symptom

The old 3-parameter action space:

- `aspect_ratio`
- `elongation`
- `rotational_transform`

could not satisfy the `P1` constraints under the real `constellaration` verifier path.

### Evidence

A 125-point grid sweep over the historical 3-knob range produced `0/125` feasible designs.

Observed behavior:

- `average_triangularity` stayed near `+0.005`
- `p1_feasibility` stayed near `1.00995`
- varying `n_field_periods` did not resolve the blocker

### Root Cause

`generate_rotating_ellipse(aspect_ratio, elongation, rotational_transform, n_field_periods)` does not meaningfully expose the Fourier mode that controls triangularity.

The historical `rotational_transform` range was also too low to reach the `abs(edge_iota_over_nfp) >= 0.3` requirement reliably.

## 2. Original Winning Session

The original successful `P1` path in `ai-sci-feasible-designs` did not rely on the raw 3-knob family alone.

The winning session:

1. built a low-dimensional sweep with a fourth knob
2. found feasible seeds quickly
3. refined around those seeds with stronger optimizers
4. used leaderboard-quality anchors later in the pipeline

### Missing Fourth Knob

The historical script added `tri_scale` by injecting the `m=2, n=0` Fourier mode after generating the base rotating-ellipse shape.

That missing triangularity control is the key reason the raw 3-knob family was structurally blocked.

### Recovered Useful Ranges

The original script used substantially different useful ranges than the blocked runtime:

```text
aspect_ratio:         [3.0, 3.6]
elongation:           [1.4, 2.2]
rotational_transform: [1.5, 2.2]
tri_scale:            [0.55, 0.8]
```

## 3. Harness Campaign Comparison

Recorded `P1` campaign runs in `ai-sci-feasible-designs` also found zero feasible candidates.

That failure does not disprove the repaired low-dimensional path. It mostly shows that the campaign guidance and search style diverged from the winning approach:

- the campaigns pushed the agent away from broad low-dimensional exploration
- the winning session did broad sweeps and large early moves
- the campaign path used richer Fourier candidates, but not the same successful cold-start behavior

## 4. Recorded 4-Knob Sweep

A recorded 4-knob sweep using explicit triangularity injection showed that the repaired family can reach `P1` feasibility.

Recorded sweep family:

```text
aspect_ratio:         [3.2, 3.8]
elongation:           [1.2, 1.8]
rotational_transform: [1.2, 1.8]
tri_scale:            [0.4, 0.7]
n_field_periods:      3
mpol / ntor:          3 / 3
```

What that sweep established:

- explicit triangularity control fixes the structural blocker
- repaired-family feasibility is reachable in principle
- repaired-family defaults still need measured calibration before they should be narrated as stable

## 5. Verifier Alignment Evidence

The current runtime verifier alignment is sound:

- the official `GeometricalProblem` API is used for feasibility and objective semantics
- score conversion matches the official `P1` objective direction
- the runtime split is boundary-based: build boundary first, then evaluate boundary
- low-fidelity `run` and high-fidelity `submit` are treated as separate truth surfaces

This matters because the repair belongs in the boundary family, not in redefined verifier semantics.

## 6. Reward Implications

The repaired family changes what is possible, but it does not justify a complicated reward.

The main reward conclusions remain:

- keep reward tied to official verifier scalars
- keep feasibility-first behavior
- do not add per-constraint or knob-specific shaping
- tune from playtest evidence, not from theory alone

## 7. Why The Environment Is Still Valid

The repaired 4-knob family is not a leaderboard-matching optimizer. That is acceptable for this repo.

The purpose of the environment is:

- teach and evaluate constrained design behavior
- keep the observation/action/reward loop legible
- preserve an explainable path from action to verifier feedback

The winning high-fidelity score chase used a much richer downstream optimization story. This repo does not need to reproduce that full pipeline to be a valid hackathon environment artifact.

## 8. Design Implications Kept From This Analysis

- keep multiple frozen reset seeds rather than one memorized starting state
- keep reward based on official scalars rather than hand-coded constraint bonuses
- keep known winners as calibration fixtures, not direct reward targets
- keep domain knowledge in seeds and fixtures, not in opaque reward tricks

## 9. Primary References

Fusion Design Lab:

- [`server/physics.py`](../server/physics.py)
- [`server/environment.py`](../server/environment.py)
- [`fusion_lab/models.py`](../fusion_lab/models.py)
- [`docs/P1_ENV_CONTRACT_V1.md`](P1_ENV_CONTRACT_V1.md)

Reference repo:

- `ai-sci-feasible-designs/docs/harness/raw-session.md`
- historical `scripts/search_p1_lowdim.py`
- `ai-sci-feasible-designs/docs/P1_SCORE_CHASE_NOTES.md`
- `P1_CAMPAIGN_POSTMORTEM.md`
