# P1 reward transfer for fusion-design-lab

## Core conclusion
Use `scadena` as the main repair prior and `CreativeEngineer` as the top-score exploitation prior.

## Reward schedule
1. Infeasible phase: reduce official feasibility violation first.
2. Within infeasible candidates, prioritize average triangularity repair first.
3. After triangularity starts to clear, prefer aspect-ratio and edge-iota cleanup.
4. Crossing the official feasibility threshold should receive a large bonus.
5. Once feasible, optimize the official P1 score, which in practice tracks lower max elongation.

## Practical priors
- `scadena_seed.json`: best repair anchor. Raw near-P1 HF seeds crossed official feasibility by moving toward this family.
- `creative_seed.json` and `creative_best.json`: best endpoint family. Use these for exploitation after feasibility is stable.
- `samet_seed.json`: exact-feasible distinct family. Useful for diversity and non-scadena exploration.
- `egodos_seed.json`: best near-feasible non-scadena source.
- `egodos_sparse_rgroup_best.json`: proof that a sparse low-order `r_cos` move can create a new feasible non-scadena design.

## Operators that worked
- Coordinated move toward the `scadena` manifold for repairing raw near-P1 seeds.
- Sparse low-order `r_cos` move from `egodos` toward `Samet`.
- Small local `Samet` continuation on low-order modes.

## Operators that did not work well
- Whole-boundary interpolation between distant families.
- Random full-space coefficient noise.
- Sparse top-k replacement toward `scadena` without coordinated movement.

## Suggested usage in fusion-design-lab
- During repair-heavy exploration, add reward telemetry for:
  - official feasibility
  - average triangularity
  - aspect ratio
  - edge rotational transform over field periods
  - max elongation
- Bias mutation proposals toward:
  - `scadena` direction for feasibility repair
  - `CreativeEngineer` neighborhood for high-score exploitation
  - `Samet` and `egodos` seeds for diversity maintenance
