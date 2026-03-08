# P1 Fixture Sanity

This folder now contains three low-fidelity-calibrated `P1` fixtures:

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

What is still pending:

- paired high-fidelity submit measurements for each tracked fixture
- low-fi vs high-fi ranking comparison note
- decision on whether any reset seed should be changed from the current default
