# Fusion Design Lab

Fusion Design Lab is an environment-first OpenEnv hackathon project for the `P1` stellarator benchmark.

The repo is organized around one clear submission thesis:

- an official `P1` task with `constellaration` as the verifier of record
- a narrow, reproducible action space
- real verifier feedback
- explicit constraints and feasibility semantics
- a reward function that is iteratively improved through observed behavior

Training is supporting evidence. The environment is the product.

A trained model is optional for this repo's submission story. A public Colab notebook artifact is still required by the hackathon, and that notebook can stay evaluation-first if training evidence is weak.

## Current Status

This repository is the clean hackathon workspace. The detailed planning docs live in `docs/FUSION_DESIGN_LAB_PLAN_V2.md`, `docs/FUSION_DELIVERABLES_MAP.md`, and `docs/FUSION_NEXT_12_HOURS_CHECKLIST.md`.

Implementation status:

- `P1` is locked as the benchmark task
- docs are aligned to fresh `P1` wiring in this repo
- shared models, baselines, and server/client entry points now reflect the locked `P1` contract
- the current environment uses `constellaration` for low-fidelity `run` steps and high-fidelity `submit` evaluation
- the repaired 4-knob low-dimensional family is now wired into the runtime path
- the next runtime work is measured sweep validation, fixtures, manual playtesting, heuristic refresh, and deployment evidence

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
- [x] Pass the Northflank smoke test on the H100 workspace
- [x] Verify the current 3-knob family against the real low-fidelity verifier
- [x] Add a custom low-dimensional boundary builder with an explicit triangularity control knob
- [x] Split boundary construction from boundary evaluation in `server/physics.py`
- [x] Update the action contract from 3 knobs to the repaired low-dimensional family
- [x] Add explicit VMEC failure semantics to the environment contract
- [x] Label low-fi `run` truth vs high-fi `submit` truth in observations and task docs
- [x] Separate high-fidelity submit scoring/reporting from low-fidelity rollout score state
- [ ] Add tracked `P1` fixtures under `server/data/p1/`
- [ ] Run manual playtesting and record the first reward pathology
- [ ] Refresh the heuristic baseline for the real verifier path
- [ ] Deploy the real environment to HF Space

## Known Gaps

- Historical blocker note: the old 3-knob family was structurally blocked on P1 triangularity with the real verifier path. A sampled low-fidelity sweep kept `average_triangularity` at roughly `+0.004975` and `p1_feasibility` at roughly `1.00995`, with zero feasible samples. That blocker motivated the repaired 4-knob runtime that is now live.
- The repaired family now uses frozen exact seeds with explicit triangularity control. Those seeds are near-boundary references, not yet tracked fixtures.
- The repaired low-dimensional family still needs measured ranges and deltas. Do not narrate guessed `rotational_transform` bounds, `triangularity_scale` deltas, or a larger budget as validated facts until they are measured on the repaired environment.
- `run` uses low-fidelity `constellaration` metrics, while `submit` re-evaluates the current design with high-fidelity `skip_qi`; do not present step-time metrics as final submission metrics.
- VMEC failure semantics are now explicit in the runtime path. Failed evaluations cost budget, produce a visible failure observation, and apply a penalty.
- Terminal reward/reporting now uses a fidelity-consistent basis: `submit` compares against high-fidelity reference state instead of low-fidelity rollout score state.
- `best_score` and `best_feasibility` are currently context-dependent in observations: run-time views reflect low-fidelity rollout state, while submit-time views can reflect high-fidelity best state. Keep that distinction explicit in docs, traces, and baseline interpretation until the contract is simplified further.
- Budget exhaustion now returns a smaller terminal reward than explicit `submit`; keep that asymmetry when tuning reward so agents still prefer deliberate submission.
- The real-verifier baseline rerun showed the old heuristic is no longer useful as-is: over 5 seeded episodes, both agents stayed at `0.0` mean best score and the heuristic underperformed random on reward. The heuristic needs redesign after the repaired parameterization and manual playtesting.

Current mode:

- strategic task choice is already locked
- the next work is measured sweep validation, then fixtures, manual playtesting, heuristic refresh, smoke validation, and deployment
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
- Required notebook artifact: one public Colab notebook, even if it only demonstrates evaluation traces rather than a trained policy
- Verifier of record: `constellaration.problems.GeometricalProblem`
- Environment style: fresh wiring in this repo, not a port of the old `ai-sci-feasible-designs` harness
- Northflank containers are ephemeral, so persistent storage should be attached before relying on saved models, caches, or fixture data
- Preferred deployment path: push this GitHub repo and let HF Space build from the repo/Docker configuration rather than copying code manually
- Preferred Colab/HF Space connectivity: make the HF Space public for the hackathon unless privacy becomes necessary; if private, document and use an explicit access token in the notebook

## Immediate Next Steps

1. Run a small measured sweep on the repaired family to choose useful ranges, deltas, and reset seeds.
2. Add tracked `P1` fixtures under `server/data/p1`.
3. Run manual playtest episodes and record the first real reward pathology, if any.
4. Refresh the heuristic baseline using manual playtest evidence, then save one comparison trace.
5. Use the passing Northflank H100 setup to produce remote traces and comparisons from the real verifier path.
6. Deploy the environment to HF Space.
7. Add the Colab notebook under `training/notebooks`.

These are implementation steps, not another planning phase.

## Fixture Policy

This repo may reuse selected JSON artifacts or boundaries as fixed calibration fixtures.

Allowed examples:

- a known-good or near-winning `P1` boundary
- near-boundary cases
- clearly bad cases

Disallowed:

- porting the old planner, governor, or experiment harness into this repo

## Technical Spec

The focused technical plan for the repaired `P1` environment lives in [docs/P1_ENV_CONTRACT_V1.md](docs/P1_ENV_CONTRACT_V1.md).

## Hackathon Working Note

This repo is intentionally biased toward executable demos, manual playtesting, and clear environment behavior over building out test coverage during the hackathon.
