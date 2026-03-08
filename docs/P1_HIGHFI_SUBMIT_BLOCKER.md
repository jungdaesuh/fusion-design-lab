# P1 High-Fidelity Submit Blocker

**Date:** 2026-03-07
**Status:** RESOLVED. Fix: switched submit preset from `high_fidelity` to `from_boundary_resolution`.
**Predecessor:** [P1_PARAMETERIZATION_DEEPDIVE.md](P1_PARAMETERIZATION_DEEPDIVE.md)

---

## 1. The Problem

After repairing the parameterization (4-knob family with `triangularity_scale`),
low-fidelity `run` steps work correctly but **every high-fidelity `submit` crashes**.

The environment is functional (no Python exceptions, graceful degradation via
`evaluation_failed=True`) but no agent can ever produce a nonzero score because
the submit path always fails with `"VMEC++ did not converge"`.

## 2. Evidence

### Smoke test: all 3 reset seeds, immediate submit

```
Seed 0: low-fi feas=0.0507 tri=-0.4747 iota=0.2906
  submit: FAILED  fidelity=high  reason="VMEC++ did not converge"

Seed 1: low-fi feas=0.0507 tri=-0.4747 iota=0.2896
  submit: FAILED  fidelity=high  reason="VMEC++ did not converge"

Seed 2: low-fi feas=0.0507 tri=-0.4747 iota=0.3165
  submit: FAILED  fidelity=high  reason="VMEC++ did not converge"
```

### Smoke test: heuristic-style episode (seed 0)

```
Start:    feas=0.0507  tri=-0.4747  iota=0.2906  failed=False
tri+s:    feas=0.0517  tri=-0.4852  iota=0.2845  r=-0.11  failed=False
rt+s:     feas=0.0296  tri=-0.4852  iota=0.2977  r=+0.01  failed=False
submit:   feas=1000000 score=0.0000              r=-3.00  failed=True
```

Low-fi steps produce real physics feedback (feasibility moves, constraint values
respond to knob changes). But the boundary that passes low-fi evaluation fails
high-fi evaluation universally.

### What the failure handling does correctly

The VMEC crash handling from `d585eb2` works as designed:

- `evaluate_boundary` catches `RuntimeError` and returns `_failure_metrics`
- `_failure_metrics` sets `evaluation_failed=True`, `p1_feasibility=1_000_000.0`
- The environment applies `FAILURE_PENALTY = -2.0` plus terminal penalties
- `_update_best` skips failed evaluations (doesn't corrupt best-known state)
- `_reference_metrics` falls back to last successful evaluation for reward deltas
- The observation text shows `evaluation_status=FAILED` with the failure reason

No silent swallowing, no crashes, no state corruption. The problem is purely that
the physics solver rejects these boundaries at high fidelity.

## 3. Why It Happens

### Low-fi vs high-fi VMEC settings

```python
low:  ConstellarationSettings(vmec_preset_settings=fidelity='low_fidelity')
high: ConstellarationSettings(vmec_preset_settings=fidelity='high_fidelity')
```

High-fidelity VMEC uses more radial grid points and stricter convergence criteria.
The 4-knob boundaries (generated at `mpol=3, ntor=3` with injected triangularity)
are not spectrally smooth enough for the high-fi solver to converge.

### Why low-fi works

Low-fi VMEC is more tolerant of rough boundaries. It uses fewer grid points and
relaxed convergence thresholds, so the same boundary that fails high-fi can still
produce valid physics at low-fi.

### The original session handled this differently

From `P1_SCORE_CHASE_NOTES.md`, the winning approach used a multi-fidelity pipeline:

1. Low-fi VMEC inside the optimization loop (fast, robust)
2. Periodic promotion to `from_boundary_resolution` (mid gate)
3. Final promotion to `high_fidelity` (final truth)

The boundaries that reached high-fi were already refined through optimization
(trust-region, ALM+NGOpt) with much higher Fourier resolution (`mpol=8, ntor=8`).
Our 4-knob `mpol=3, ntor=3` boundaries are too coarse for high-fi convergence.

## 4. Fix Options

### Option A: Use mid-fidelity for submit

Replace the `high_fidelity` preset in `_settings_for_fidelity("high")` with
`from_boundary_resolution` or another intermediate preset.

**Pros:**
- Minimal code change (one line in `physics.py`)
- Still more rigorous than low-fi `run` steps
- Likely to converge on these boundaries

**Cons:**
- Submit results are no longer comparable to the official leaderboard evaluator
- Need to verify `from_boundary_resolution` actually exists and converges

**Verdict:** Pragmatic for the hackathon. The environment already documents that
it's a stepping stone, not a leaderboard tool.

### Option B: Increase Fourier resolution in boundary construction

Change `build_boundary_from_params` to use `mpol=5, ntor=5` or higher instead
of `mpol=3, ntor=3`. More Fourier modes produce a smoother boundary that high-fi
VMEC can converge on.

**Pros:**
- Addresses root cause (boundary too coarse)
- Submit uses the real high-fi evaluator

**Cons:**
- Higher modes may change which parameter regions are feasible
- Need to re-run the 4-knob sweep to verify feasibility still holds
- Low-fi `run` steps become slower (more modes = more computation)

**Verdict:** Correct fix but requires re-validation. May invalidate current
ranges, deltas, and seed pool.

### Option C: Both (higher modes + mid-fi submit)

Increase `mpol/ntor` moderately (e.g., 4 or 5) AND use a mid-fi submit preset.

**Pros:**
- Belt and suspenders: smoother boundary + more tolerant solver
- Most likely to unblock submit without breaking low-fi behavior

**Cons:**
- Two changes at once make it harder to attribute any regressions
- Need re-validation of the parameter landscape

### Option D: Use same fidelity for both run and submit

Make both `run` and `submit` use the same low-fi settings. Submit costs a budget
step but doesn't add fidelity uplift.

**Pros:**
- Guaranteed to work (low-fi already converges)
- Simplest possible fix

**Cons:**
- Loses the multi-fidelity story entirely
- Submit becomes meaningless as a distinct action (same eval as run)
- The low-fi/high-fi split was a deliberate design choice

**Verdict:** Only if nothing else works. Last resort.

## 5. Resolution

**Option A was applied.** The `from_boundary_resolution` preset exists in
`constellaration.mhd.vmec_settings` and is actually the library's default preset.

### Investigation results

1. `from_boundary_resolution` adapts VMEC resolution to the boundary's Fourier
   resolution and "optimizes for convergence rate over runtime and high fidelity"
2. `high_fidelity` forces minimum 10 poloidal and toroidal modes regardless of
   boundary resolution — far beyond our `mpol=3, ntor=3` boundaries
3. All 3 reset seeds converge with `from_boundary_resolution` (~4s each)
4. Tested across 6 diverse parameter combos: `from_boundary_resolution` converges
   everywhere that `low_fidelity` converges — no case where low-fi works but mid-fi fails
5. Metrics are nearly identical between low-fi and mid-fi (slight iota differences,
   matching triangularity and feasibility)

### Fix

One-line change in `server/physics.py`:

```python
# Before (crashed on all 4-knob boundaries):
vmec_preset_settings=ConstellarationSettings.default_high_fidelity_skip_qi().vmec_preset_settings

# After (converges on all boundaries that low-fi converges on):
vmec_preset_settings=VmecPresetSettings(fidelity="from_boundary_resolution")
```

### Available VMEC presets (for reference)

| Preset | Purpose | Convergence | Speed |
|--------|---------|-------------|-------|
| `very_low_fidelity` | Fast optimization | Very tolerant | ~0.3s |
| `low_fidelity` | Runtime over fidelity (our `run` steps) | Tolerant | ~0.6s |
| `from_boundary_resolution` | Match boundary resolution (our `submit`) | Adaptive | ~4s |
| `high_fidelity` | Max correctness (min 10 modes) | Strict | crashes on coarse boundaries |

### Verification

Full environment episode with submit now works:

```
Reset: feas=0.0507 tri=-0.4747 iota=0.2906
tri+s: feas=0.0517 tri=-0.4852 iota=0.2845 r=-0.105 failed=False
rt+s:  feas=0.0296 tri=-0.4852 iota=0.2977 r=+0.011 failed=False
tri+s: feas=0.0292 tri=-0.4954 iota=0.2912 r=-0.098 failed=False
submit: feas=0.0322 score=0.0000 r=-1.015 failed=False fidelity=high
```

Submit produces real physics metrics, no crash, correct fidelity labeling.

## 6. What This Does NOT Invalidate

- The 4-knob parameterization repair is correct (low-fi feasibility works)
- The VMEC crash handling is correct (graceful degradation, no state corruption)
- The reward V0 design is correct (failure penalty, reference metrics fallback)
- The heuristic baseline design is correct (reactive constraint repair strategy)
- The reset seed pool design is correct (diverse near-feasible starts)

The only thing broken is the submit fidelity gate. Everything else in `d585eb2`
is validated by the smoke tests.

## 7. Affected Files

The fix will touch:

- `server/physics.py` — `_settings_for_fidelity("high")` and/or
  `build_boundary_from_params` defaults
- Possibly `server/environment.py` if submit semantics change
- `docs/P1_ENV_CONTRACT_V1.md` — if the multi-fidelity contract changes

## 8. Baseline Results (from background runs)

The heuristic and random baselines completed their 20-episode runs. Both ran
on the repaired parameterization with low-fi `run` steps working correctly.
Submit steps in both baselines triggered the high-fi crash, so all episodes
ended with `evaluation_failed=True` on submit and zero final scores.

The low-fi step behavior was healthy:

- Heuristic agent correctly identified and repaired constraint violations
- Random agent produced varied trajectories with some feasibility improvement
- VMEC crash handling worked throughout (no Python exceptions, graceful penalties)
- The `restore_best` action worked correctly after failures

The baselines are ready to produce meaningful results once the submit blocker
is resolved.
