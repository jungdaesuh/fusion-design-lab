# P1 Fixture Sanity

This folder now contains three paired low-fidelity/high-fidelity `P1` fixtures:

- `boundary_default_reset.json`
- `bad_low_iota.json`
- `lowfi_feasible_local.json`

Calibration source:

- coarse measured sweep artifact: `baselines/sweep_results/measured_sweep_20260308T050043Z.json`
- targeted local probes around the default reset seed

Current interpretation:

- `boundary_default_reset.json`
  - near-boundary reset reference
  - infeasible, but close enough that short repair episodes are realistic
- `bad_low_iota.json`
  - clearly bad infeasible case
  - demonstrates that edge iota can be the blocking constraint even when triangularity is already acceptable
- `lowfi_feasible_local.json`
  - low-fidelity feasible local target
  - reachable from the default reset band with two intuitive knob increases

Observed from paired run:

- low-fi vs high-fi feasibility alignment and metric deltas are documented in `baselines/fixture_high_fidelity_pairs.json`.
- decision on whether any reset seed should be changed from the current default

Current paired summary (`baselines/fixture_high_fidelity_pairs.json`):

- `bad_low_iota.json`:
  - both fidelities infeasible
  - low/high feasibility match: `true`
  - low/high score match: both `0.0`

- `boundary_default_reset.json`:
  - both fidelities infeasible
  - low/high feasibility match: `true`
  - low/high score match: both `0.0`

- `lowfi_feasible_local.json`:
  - both fidelities feasible
  - low/high feasibility match: `true`
  - high-fidelity score improved slightly: `0.29165951078327634` → `0.2920325118884466`
