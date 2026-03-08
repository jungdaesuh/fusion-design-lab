# P1 curated seed selection

## Included seeds
- `creative_best.json`: best overall official P1 design found. Use as the score ceiling reference.
- `creative_seed.json`: original CreativeEngineer leaderboard anchor. Use as the exploitation parent.
- `scadena_seed.json`: strongest repair anchor found. Use when a candidate is close but still infeasible.
- `scadena_repaired_best.json`: repaired raw-HF survivor showing that the scadena corridor generalizes.
- `samet_seed.json`: exact-feasible distinct family. Use to prevent collapse into only the creative/scadena basin.
- `egodos_seed.json`: near-feasible non-scadena target. Use as a repair-source seed.
- `egodos_sparse_rgroup_best.json`: best new non-scadena feasible design found from a sparse grouped repair.

## Family roles
- `creative`: best objective region.
- `scadena`: best feasibility-repair corridor.
- `samet`: stable distinct feasible basin.
- `egodos`: useful near-feasible source for non-scadena exploration.

## Search pattern extracted
- `CreativeEngineer` is the better endpoint family.
- `scadena` is the better repair corridor.
- `Samet` supports local feasible continuation.
- `egodos` can be repaired into feasibility with a very small sparse low-order `r_cos` move toward `Samet`.

## Recommended initialization mix
- 40% from `scadena_seed.json` and `scadena_repaired_best.json`
- 30% from `creative_seed.json` and `creative_best.json`
- 20% from `samet_seed.json`
- 10% from `egodos_seed.json` and `egodos_sparse_rgroup_best.json`

## Why this is minimal
This pack gives one strong exploitation family, one strong repair family, and one genuinely distinct non-scadena frontier, without dragging over the entire search archive.
