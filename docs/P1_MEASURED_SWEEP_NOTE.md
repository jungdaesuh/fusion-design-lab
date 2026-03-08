# P1 Measured Sweep Note

Artifact:

- `baselines/sweep_results/measured_sweep_20260308T050043Z.json`

Run shape:

- repaired 4-knob family
- low-fidelity verifier only
- `3 x 3 x 3 x 3 = 81` configurations

Summary:

- total configurations: `81`
- evaluated successfully: `63`
- crashed: `18`
- feasible: `0`
- crash rate: `22.2%`

Most useful result:

- the best coarse near-boundary point was:
  - `aspect_ratio=3.8`
  - `elongation=1.8`
  - `rotational_transform=1.55`
  - `triangularity_scale=0.55`
  - `p1_feasibility=0.035208`

What the sweep tells us:

- the repaired family does have a usable near-boundary band
- coarse global resolution is still too blunt to capture the small low-fidelity feasible pocket seen in targeted local probes
- `rotational_transform=1.55` performed better than `1.2`, while `1.9` produced a concentrated crash zone
- `triangularity_scale=0.55` was the best coarse setting overall; `0.7` improved triangularity but also increased crash rate

Actionable conclusion:

- keep the current ranges and deltas for now
- do not freeze a new default reset seed from the coarse sweep alone
- use the coarse sweep plus local probes to drive the first tracked fixtures and manual playtesting
