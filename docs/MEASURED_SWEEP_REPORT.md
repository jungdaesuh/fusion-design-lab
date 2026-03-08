# Measured Sweep Report

**Date:** 2026-03-08
**Status:** Complete. One range change recommended.

This report validates the current parameter ranges, deltas, and reset seeds
against measured low-fidelity evaluations on the repaired 4-knob boundary family.

---

## 0. What Was Done

### Goal

Validate the current `PARAMETER_RANGES`, `PARAMETER_DELTAS`, and `RESET_SEEDS`
before treating them as stable defaults. This is the "measured sweep" step from
Plan V2 §21 and Deliverables Map priority #1.

### Procedure

1. **Timed a single evaluation** on local CPU to establish approximate per-eval
   cost. Observed ~2.5s per low-fidelity evaluation (timing metadata is now
   saved to the JSON artifact by the sweep script for future runs).

2. **Ran a broad 3-point grid sweep** (`baselines/measured_sweep.py --grid-points 3`)
   over the full `PARAMETER_RANGES` to check crash zones, feasibility coverage,
   and per-parameter trends. 81 configurations.

3. **Ran a targeted fine-grid sweep** (`baselines/measured_sweep.py --targeted`)
   over the known feasible zone (`rot_transform ∈ [1.50, 1.80]`,
   `tri_scale ∈ [0.55, 0.65]`) to map the exact feasibility boundary, crash
   gradient, and candidate reset seeds. 315 configurations.

4. **Validated the 3 current reset seeds** individually against the live
   `build_boundary_from_params` + `evaluate_boundary` code path.

5. **Checked delta reachability**: whether 6 steps at maximum delta can traverse
   each parameter range end-to-end.

6. **Cross-referenced** results against the prior recorded 4-knob sweep
   documented in `docs/P1_PARAMETERIZATION_DEEPDIVE.md` §4.

### Tools

- Script: `baselines/measured_sweep.py`
  - broad grid: `--grid-points N` (evenly spaced across `PARAMETER_RANGES`)
  - targeted: `--targeted` (pre-defined value set around the known feasible zone)
- Code path: `server.physics.build_boundary_from_params` →
  `server.physics.evaluate_boundary` (low-fidelity)
- Runtime: local CPU (Darwin), `uv run python`

---

## 1. Sweep Configuration

Two sweeps were run on local CPU using the live `build_boundary_from_params` +
`evaluate_boundary` code path (low-fidelity VMEC).

### Broad sweep (3-point grid)

```
aspect_ratio           ∈ [3.2, 3.8]  3 values: 3.2, 3.5, 3.8
elongation             ∈ [1.2, 1.8]  3 values: 1.2, 1.5, 1.8
rotational_transform   ∈ [1.2, 1.9]  3 values: 1.2, 1.55, 1.9
triangularity_scale    ∈ [0.4, 0.7]  3 values: 0.4, 0.55, 0.7
Total: 81 configurations
```

### Targeted sweep (fine grid around feasible zone)

```
aspect_ratio           ∈ {3.4, 3.6, 3.8}
elongation             ∈ {1.2, 1.4, 1.6}
rotational_transform   ∈ {1.50, 1.55, 1.60, 1.65, 1.70, 1.75, 1.80}
triangularity_scale    ∈ {0.55, 0.58, 0.60, 0.62, 0.65}
Total: 315 configurations
```

---

## 2. Broad Sweep Results

```
Total:     81
Evaluated: 63 (77.8%)
Crashed:   18 (22.2%)
Feasible:   0 (0.0%)
```

The 3-point grid missed the narrow feasible zone entirely (`tri_scale=0.60`,
`rot_transform≈1.6` were not sampled). All 18 crashes occurred at
`rot_transform=1.9` (67% crash rate at that value).

### Per-parameter summary

| Parameter | Value | Crash rate | Avg feasibility |
|-----------|-------|------------|-----------------|
| aspect_ratio | 3.20 | 6/27 (22%) | 0.3335 |
| aspect_ratio | 3.50 | 6/27 (22%) | 0.2568 |
| aspect_ratio | 3.80 | 6/27 (22%) | 0.2011 |
| elongation | 1.20 | 6/27 (22%) | 0.2443 |
| elongation | 1.50 | 6/27 (22%) | 0.2661 |
| elongation | 1.80 | 6/27 (22%) | 0.2811 |
| rot_transform | 1.20 | 0/27 (0%) | 0.3641 |
| rot_transform | 1.55 | 0/27 (0%) | 0.1738 |
| rot_transform | 1.90 | 18/27 (67%) | 0.2332 |
| tri_scale | 0.40 | 0/27 (0%) | 0.2519 |
| tri_scale | 0.55 | 9/27 (33%) | 0.2309 |
| tri_scale | 0.70 | 9/27 (33%) | 0.3146 |

Key observation: crash rate is driven entirely by `rotational_transform`.
Higher `tri_scale` also contributes when combined with high `rot_transform`.

---

## 3. Targeted Sweep Results

```
Total:     315
Evaluated: 273 (86.7%)
Crashed:    42 (13.3%)
Feasible:   77 (28.2% of evaluated)
```

### Crash rate by `rotational_transform`

| rot_transform | crash rate | feasible count |
|---------------|------------|----------------|
| 1.50 | 0/45 (0%) | 3 |
| 1.55 | 1/45 (2%) | 8 |
| 1.60 | 1/45 (2%) | 12 |
| 1.65 | 1/45 (2%) | 15 |
| 1.70 | 4/45 (9%) | 17 |
| 1.75 | 9/45 (20%) | 17 |
| 1.80 | 26/45 (58%) | 5 |

**Feasible count peaks at rt=1.70-1.75.** Beyond 1.75, crash rate rises sharply
while feasible count drops. The useful range is [1.50, 1.75].

### Feasibility by `triangularity_scale`

| tri_scale | feasible count |
|-----------|----------------|
| 0.55 | 0 |
| 0.58 | 0 |
| 0.60 | 35 |
| 0.62 | 25 |
| 0.65 | 17 |

**The feasibility boundary is between ts=0.58 and ts=0.60.** No configurations
with `tri_scale < 0.60` are feasible. The binding constraint is always
`average_triangularity` (requires `≤ -0.5`).

### Top feasible designs (by score)

Note: the `P1` verifier uses a 1% feasibility tolerance (`FEASIBILITY_TOLERANCE = 0.01`
in `server/physics.py`). Designs with `feas ≤ 0.01` are considered feasible by
`GeometricalProblem.is_feasible()`. Rows below showing `feas=0.0046` are feasible
under this tolerance even though their raw feasibility is nonzero.

| AR | elong | rt | ts | score | feas | elong_out | tri | iota |
|----|-------|------|------|---------|---------|-----------|---------|--------|
| 3.6 | 1.2 | 1.55 | 0.60 | 0.3446 | 0.0046 | 6.8985 | -0.4977 | 0.2989 |
| 3.8 | 1.2 | 1.50 | 0.60 | 0.3292 | 0.0046 | 7.0375 | -0.4977 | 0.3106 |
| 3.8 | 1.4 | 1.50 | 0.60 | 0.3143 | 0.0000 | 7.1717 | -0.5003 | 0.3002 |
| 3.6 | 1.2 | 1.60 | 0.60 | 0.3071 | 0.0046 | 7.2363 | -0.4977 | 0.3105 |
| 3.8 | 1.2 | 1.50 | 0.62 | 0.2982 | 0.0000 | 7.3165 | -0.5074 | 0.3027 |

All top scores have `elongation=1.2` (lowest tested). Lower input elongation →
lower output `max_elongation` → higher score. The best achievable score in the
4-knob family is ~0.34, far below the winning 0.97 (as expected — the
environment is a stepping stone, not a leaderboard path).

---

## 4. Reset Seed Validation

Current seeds from `server/contract.py`:

| Seed | AR | elong | rt | ts | feas | tri | iota | elong_out |
|------|-----|-------|------|------|---------|---------|--------|-----------|
| 0 | 3.6 | 1.4 | 1.5 | 0.55 | 0.0507 | -0.4747 | 0.2906 | 6.1368 |
| 1 | 3.4 | 1.4 | 1.6 | 0.55 | 0.0507 | -0.4747 | 0.2896 | 6.2744 |
| 2 | 3.8 | 1.4 | 1.5 | 0.55 | 0.0507 | -0.4747 | 0.3165 | 6.5502 |

**Assessment:**

- All three have identical feasibility (0.0507) because they share `ts=0.55`
  and the binding constraint is `triangularity`
- All are infeasible but near the boundary — exactly 1 medium `tri_scale` step
  (delta 0.05) from crossing into feasibility at `ts=0.60`
- Seed 2 already satisfies the iota constraint (0.3165 ≥ 0.3); seeds 0 and 1
  are just below (0.29), adding a secondary challenge
- Diversity is limited: all share `elongation=1.4` and `ts=0.55`

**Verdict:** The seeds are functional. They create a meaningful 6-step task
where the agent must first cross the feasibility boundary (1-2 steps), then
optimize elongation (remaining steps). The limited diversity is acceptable for
a hackathon environment — memorization risk is low because the task is about
constraint navigation, not seed-specific tricks.

---

## 5. Delta Reachability

Can an agent traverse the parameter space within 6 steps?

| Parameter | Range | Span | Large delta | 6 large steps | Coverage |
|-----------|-------|------|-------------|---------------|----------|
| aspect_ratio | [3.2, 3.8] | 0.60 | 0.20 | 1.20 | 200% |
| elongation | [1.2, 1.8] | 0.60 | 0.20 | 1.20 | 200% |
| rotational_transform | [1.2, 1.9] | 0.70 | 0.20 | 1.20 | 171% |
| triangularity_scale | [0.4, 0.7] | 0.30 | 0.10 | 0.60 | 200% |

All parameters have >100% coverage. The agent can reach any point in the range
from any starting point within 6 large steps. In practice, agents will use a mix
of magnitudes, so effective coverage is tighter — but the feasibility crossing
only requires 1 medium `tri_scale` step.

---

## 6. Crash Zone Summary

Combining both sweeps and the prior deep-dive data:

| Zone | rot_transform | tri_scale | Crash rate | Notes |
|------|---------------|-----------|------------|-------|
| Safe | ≤ 1.65 | any | 0-2% | All feasible exploration happens here |
| Moderate | 1.70 | any | ~9% | Still useful, some feasible designs |
| Risky | 1.75 | any | ~20% | Feasible count plateaus, crash rate rising |
| Dangerous | 1.80 | any | ~58% | Few feasible, mostly crashes |
| Dead | ≥ 1.90 | ≥ 0.55 | 67-100% | No feasible, universal crashes |

The crash penalty (`-2.1` net) already discourages exploration into crash zones.
The agent should learn to avoid `rot_transform > 1.75` naturally.

### Known gap: elongation crash pocket

The replay playtest (`docs/P1_REPLAY_PLAYTEST_REPORT.md`, Episode 1 steps 4-5)
discovered VMEC crashes at `elongation ~1.25-1.30` during low-fidelity evaluation,
with recovery at `elongation=1.20`. This crash pocket is inside the documented
range `(1.2, 1.8)` and was **not mapped** by either sweep, because the targeted
grid did not vary elongation aggressively at feasible parameter combinations.

This means the crash zone table above is incomplete — it only maps the
`rotational_transform` dimension. The elongation dimension has internal crash
pockets that agents exploring lower elongation values will encounter.

### Scope note: low-fidelity only

Both sweeps used low-fidelity VMEC evaluation. The high-fidelity submit path
has its own convergence behavior documented in `docs/P1_HIGHFI_SUBMIT_BLOCKER.md`.
After that blocker was resolved (switching from `high_fidelity` to
`from_boundary_resolution` VMEC preset), the submit path converges on all
boundaries that low-fi converges on, but the cross-fidelity gap is
path-dependent — some low-fi feasible states crash at high-fi (see replay
playtest Episode 5).

---

## 7. Recommendation

### Change: tighten `rotational_transform` upper bound

```
rotational_transform: (1.2, 1.9) → (1.2, 1.8)
```

**Rationale:** `rot_transform=1.9` is a dead zone — 67% crash, 0 feasible.
Keeping 1.8 preserves the risky-but-learnable edge (58% crash, 5 feasible)
while eliminating a region that only wastes budget. The agent can still learn
crash avoidance from the 1.75-1.80 boundary.

### Keep: everything else

- **Ranges** for `aspect_ratio`, `elongation`, `triangularity_scale` are well-sized
- **Deltas** allow feasibility crossing in 1 step and full range traversal in 6
- **Reset seeds** are near-feasible, functional, and create a meaningful task
- **Budget of 6** is appropriate: 1-2 steps for feasibility, 3-4 for optimization, 1 for submit

### Not recommended yet

- Changing reset seeds (current ones work, diversity is adequate for hackathon)
- Changing deltas (reachability is good, tune from playtest data)
- Changing budget (verify in manual playtest first)

---

## 8. Artifacts

- `baselines/sweep_results/measured_sweep_20260308T050043Z.json` — broad 81-point sweep
  (produced by `baselines/measured_sweep.py --grid-points 3`)
- `baselines/sweep_results/targeted_sweep.json` — targeted 315-point sweep
  (produced during the initial investigation session before the `--targeted`
  mode was committed; running `baselines/measured_sweep.py --targeted` now
  reproduces equivalent sweep coverage/results under a timestamped
  `measured_sweep_*.json` filename, but with a different JSON schema)
- Prior recorded 4-knob sweep data referenced in `docs/P1_PARAMETERIZATION_DEEPDIVE.md` §4

Provenance note: the committed JSON artifacts predate the `metadata` block added
to the sweep script. Future runs include `metadata.elapsed_seconds` and
`metadata.seconds_per_eval`. The existing broad sweep artifact contains only
`analysis` and `results`; the existing targeted sweep artifact is a raw list of
rows without a `metadata` or `analysis` wrapper.
