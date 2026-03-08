Random and heuristic baselines will live here.

## Status

- [x] random baseline exists
- [x] heuristic baseline exists
- [x] baseline comparison script exists
- [x] baseline comparison rerun completed on the real verifier path
- [x] verified that the current 3-knob family is blocked on P1 triangularity under the real verifier path
- [x] repair the low-dimensional parameterization before further heuristic work
- [x] use the measured repaired-family evidence and current frozen seed set before retuning the heuristic
- [x] heuristic refreshed after the real-verifier rerun
- [ ] near-boundary fixture-backed baseline start chosen for manual playtesting
- [ ] presentation-ready comparison trace exported

## Current Heuristic

The refreshed heuristic now follows the measured repaired-family transition pattern:

- if a low-fidelity evaluation fails, `restore_best`
- if a reset starts with low `edge_iota_over_nfp`, push `rotational_transform increase medium` first
- once `average_triangularity` is close enough, push `triangularity_scale increase medium`
- once feasible, take at most a small amount of `elongation decrease small`
- submit as soon as the design is feasible and the elongation is in the safe band

This keeps the baseline on the real verifier path instead of relying on the older threshold-only policy that over-pushed triangularity and missed the feasible sequence.

## Latest Rerun

`uv run python baselines/compare.py 5`

- random mean reward: `-2.2438`
- heuristic mean reward: `+5.2825`
- random mean final `P1` score: `0.000000`
- heuristic mean final `P1` score: `0.291951`
- feasible high-fidelity finals: `0/5` random vs `5/5` heuristic
- heuristic wins: `5/5`

The first baseline milestone is:

- one random agent
- one simple heuristic agent
- one short comparison run on the frozen task
