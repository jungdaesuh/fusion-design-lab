# Fusion Design Lab

Fusion Design Lab is an environment-first OpenEnv hackathon project for the `P1` stellarator benchmark.

The repo is organized around one clear submission thesis:

- an official `P1` task with `constellaration` as the verifier of record
- a narrow, reproducible action space
- real verifier feedback
- explicit constraints and feasibility semantics
- a reward function that is iteratively improved through observed behavior

Training is supporting evidence. The environment is the product.

## Current Status

This repository is the clean hackathon workspace. The detailed planning docs live in `docs/FUSION_DESIGN_LAB_PLAN_V2.md`, `docs/FUSION_DELIVERABLES_MAP.md`, and `docs/FUSION_NEXT_12_HOURS_CHECKLIST.md`.

Implementation status:

- `P1` is locked as the benchmark task
- docs are aligned to fresh `P1` wiring in this repo
- shared models, baselines, and server/client entry points now reflect the locked `P1` contract
- the current environment uses `constellaration` for low-fidelity `run` steps and high-fidelity `submit` evaluation
- the remaining runtime work is fixture coverage, manual playtesting, heuristic refresh, and deployment evidence

## Execution Status

- [x] Lock the `P1` contract in code
- [x] Rewrite shared models to the rotating-ellipse `P1` schema
- [x] Rewrite the environment loop to the rotating-ellipse `P1` schema
- [x] Update the API/task surface to match `P1`
- [x] Update baseline agents to the `P1` contract
- [x] Add a post-terminal guard so `step()` is a no-op after `done=True`
- [x] Re-run the baseline comparison on the `constellaration`-backed branch state
- [x] Replace the synthetic evaluator with `constellaration`
- [x] Add a runnable Northflank smoke workflow and note
- [ ] Add tracked `P1` fixtures under `server/data/p1/`
- [ ] Run manual playtesting and record the first reward pathology
- [ ] Refresh the heuristic baseline for the real verifier path
- [ ] Pass the Northflank smoke test on the H100 workspace
- [ ] Deploy the real environment to HF Space

## Known Gaps

- `BASELINE_PARAMS` is not a near-feasible anchor on the real verifier path. The current low-fidelity measurement is roughly `p1_feasibility=1.01`, `average_triangularity=+0.005`, and `edge_iota_over_nfp=0.059`, so fixture discovery has to happen before meaningful manual playtesting.
- `run` uses low-fidelity `constellaration` metrics, while `submit` re-evaluates the current design with high-fidelity `skip_qi`; do not present step-time metrics as final submission metrics.
- Budget exhaustion now returns a smaller terminal reward than explicit `submit`; keep that asymmetry when tuning reward so agents still prefer deliberate submission.
- The real-verifier baseline rerun showed the old heuristic is no longer useful as-is: over 5 seeded episodes, both agents stayed at `0.0` mean best score and the heuristic underperformed random on reward. The heuristic needs redesign after manual playtesting.

Current mode:

- strategic task choice is already locked
- the next work is fixtures, manual playtesting, heuristic refresh, smoke validation, and deployment
- new planning text should only appear when a real blocker forces a decision change

## Planned Repository Layout

```text
fusion-design-lab/
├── baselines/
├── demo/
├── docs/
├── fusion_lab/
├── server/
├── server/data/p1/
├── training/
├── openenv.yaml
├── pyproject.toml
└── README.md
```

## Setup

Base runtime:

```bash
uv sync
```

Development tooling:

```bash
uv sync --extra dev
pre-commit install
```

Optional local notebook tooling:

```bash
uv sync --extra notebooks
```

## Runtime Assumptions

- Recommended compute workspace: Northflank Jupyter Notebook with PyTorch on the team H100
- OpenEnv deployment target: Hugging Face Spaces
- Minimal submission notebook target: Colab
- Verifier of record: `constellaration.problems.GeometricalProblem`
- Environment style: fresh wiring in this repo, not a port of the old `ai-sci-feasible-designs` harness
- Northflank containers are ephemeral, so persistent storage should be attached before relying on saved models, caches, or fixture data
- Preferred deployment path: push this GitHub repo and let HF Space build from the repo/Docker configuration rather than copying code manually
- Preferred Colab/HF Space connectivity: make the HF Space public for the hackathon unless privacy becomes necessary; if private, document and use an explicit access token in the notebook

## Immediate Next Steps

1. Add tracked `P1` fixtures under `server/data/p1`.
2. Run manual playtest episodes and record the first real reward pathology, if any.
3. Refresh the heuristic baseline using manual playtest evidence, then save one comparison trace.
4. Pass a Northflank smoke test:
   - import `constellaration`
   - run one rotating-ellipse generation plus one low-fidelity verifier call
   - write an artifact to persistent storage
5. Deploy the environment to HF Space.
6. Add the Colab notebook under `training/notebooks`.

These are implementation steps, not another planning phase.

## Fixture Policy

This repo may reuse selected JSON artifacts or boundaries as fixed calibration fixtures.

Allowed examples:

- a known-good or near-winning `P1` boundary
- near-boundary cases
- clearly bad cases

Disallowed:

- porting the old planner, governor, or experiment harness into this repo

## Hackathon Working Note

This repo is intentionally biased toward executable demos, manual playtesting, and clear environment behavior over building out test coverage during the hackathon.
