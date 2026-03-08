---
title: Fusion Design Lab
sdk: docker
app_port: 8000
short_description: OpenEnv P1 stellarator design environment for the OpenEnv hackathon.
---

# Fusion Design Lab

Fusion Design Lab is an environment-first [OpenEnv](https://openenv.dev) hackathon project for the `P1` stellarator benchmark.

**Live Environment**: [HF Space](https://huggingface.co/spaces/CreativeEngineer/fusion-design-lab)
**Training Notebook**: [Repository Notebook (GRPO + HF TRL)](training/notebooks/fusion_design_lab_training.ipynb)

## What It Does

An RL environment where agents optimize stellarator fusion reactor designs by adjusting 4 geometric knobs of a low-dimensional boundary family, aiming to **minimize max elongation** while satisfying 3 hard physics constraints:

| Constraint | Bound |
|---|---|
| `aspect_ratio` | ≤ 4.0 |
| `average_triangularity` | ≤ -0.5 |
| `abs(edge_iota_over_nfp)` | ≥ 0.3 |

The environment uses [`constellaration`](https://pypi.org/project/constellaration/) as the live low-fidelity physics verifier (~0.6s) for every in-environment evaluation. The live environment still exposes **26 discrete actions** (4 parameters × 2 directions × 3 magnitudes + restore_best + submit), and `submit` remains an explicit terminal action on that same reward surface rather than a separate high-fidelity mode.

## Architecture

- **Environment server** (`server/`): FastAPI app with `/reset`, `/step`, `/health`, `/task` endpoints
- **Physics engine** (`server/physics.py`): `constellaration` VMEC-backed boundary evaluation
- **Models** (`fusion_lab/models.py`): Pydantic schemas for actions, observations, state
- **Client** (`fusion_lab/client.py`): Typed OpenEnv client for remote interaction
- **Training** (`training/`): GRPO notebook (HF TRL) and PPO smoke test

## Current Status

- `P1` is locked as the benchmark task with `constellaration` as verifier of record
- The repaired 4-knob low-dimensional boundary family is wired into the runtime path
- Environment deployed to HF Spaces and verified (health, reset, step all operational)
- GRPO training notebook is checked into the repo and aligned with the shared `fusion_lab/llm_agent.py` contract
- LLM rollout tooling can now generate fresh model completions per seed and save fixed-seed reward/outcome summaries
- Low-fidelity PPO smoke artifacts and paired high-fidelity fixture checks exist
- The live low-fidelity reward is now `Reward V2`: verifier-native repair shaping plus bounded best-so-far / anti-stagnation terms
- Before/after trained-policy evidence on the current unified low-fidelity workflow is still open

## Execution Status

- [x] Lock the `P1` contract in code
- [x] Rewrite shared models to the repaired low-dimensional `P1` schema
- [x] Rewrite the environment loop to the repaired low-dimensional `P1` schema
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
- [x] Collapse the live environment to one low-fidelity truth surface while keeping explicit `submit`
- [x] Add tracked `P1` fixtures under `server/data/p1/`
- [x] Run a tiny low-fi PPO smoke run as a diagnostic-only check and save one trajectory artifact
- [x] Complete paired high-fidelity validation artifacts outside the live environment path
- [x] Refresh the heuristic baseline for the real verifier path
- [x] Deploy the real environment to HF Space
- [x] Add the public training notebook under `training/notebooks`

## Known Gaps

- Historical blocker note: the old 3-knob family was structurally blocked on P1 triangularity with the real verifier path. A sampled low-fidelity sweep kept `average_triangularity` at roughly `+0.004975` and `p1_feasibility` at roughly `1.00995`, with zero feasible samples. That blocker motivated the repaired 4-knob runtime that is now live.
- The repaired family now has a first coarse measured sweep note in [docs/P1_MEASURED_SWEEP_NOTE.md](docs/P1_MEASURED_SWEEP_NOTE.md), but reset-seed changes and any budget changes should still wait for paired high-fidelity validation checks.
- The paired low-fi/high-fi fixture snapshots are now written into each fixture JSON and summarized in `baselines/fixture_high_fidelity_pairs.json`.
- The live environment now uses one low-fidelity verifier surface for `run`, `restore_best`, and `submit`. Keep high-fidelity checks in `baselines/high_fidelity_validation.py` and other offline validation artifacts rather than mixing them back into the environment reward loop.
- VMEC failure semantics are now explicit in the runtime path. Failed evaluations cost budget, produce a visible failure observation, and apply a penalty.
- Budget exhaustion now returns a smaller terminal reward than explicit `submit`; keep that asymmetry when tuning reward so agents still prefer deliberate submission.
- The refreshed real-verifier heuristic now follows the measured feasible sequence instead of the older threshold-only policy: on a fresh `uv run python baselines/compare.py 5` rerun, it finished with `5/5` feasible submitted finals, mean final `P1` score `0.291951`, and `5/5` wins over random.
- The first low-fidelity manual playtest note is in [docs/P1_MANUAL_PLAYTEST_LOG.md](docs/P1_MANUAL_PLAYTEST_LOG.md). The next fail-fast step is now reset-seed confirmation and one presentation-ready comparison trace backed by the paired offline high-fidelity evidence.
- The first tiny PPO smoke note is in [docs/P1_PPO_SMOKE_NOTE.md](docs/P1_PPO_SMOKE_NOTE.md). The repaired smoke trainer now finds a real positive repair signal on the easy seed, but it still does not generalize across all frozen seeds, which is the right diagnostic boundary for this stage.

Current mode:

- strategic task choice is already locked
- the next work is reset-seed confirmation, trace export, and deployment
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
- Submission notebook surface: one public notebook artifact; mirror it to Colab if the submission form still requires Colab specifically
- Required notebook artifact: one public notebook that demonstrates trained-policy behavior against the environment
- Verifier of record: `constellaration.problems.GeometricalProblem`
- Environment style: fresh wiring in this repo, not a port of the old `ai-sci-feasible-designs` harness
- Northflank containers are ephemeral, so persistent storage should be attached before relying on saved models, caches, or fixture data
- Preferred deployment path: push this GitHub repo and let HF Space build from the repo/Docker configuration rather than copying code manually
- Preferred notebook/HF Space connectivity: make the HF Space public for the hackathon unless privacy becomes necessary; if private, document and use an explicit access token in the notebook

## Immediate Next Steps

- [x] Run a tiny low-fidelity PPO smoke run and stop after a few readable trajectories or one clear failure mode.
- [x] Pair the tracked low-fidelity fixtures with high-fidelity validation spot checks immediately after the PPO smoke run.
- [x] Run at least one explicit-submit manual trace before any broader training push, then record the first real reward pathology, if any.
- [ ] Decide whether any reset seed should move based on the measured sweep plus those paired checks.
- [ ] Save one fixed-seed untrained baseline with `training/llm_rollout.py evaluate`.
- [ ] Run one short H100 GRPO pass with the repository notebook on the same unified low-fidelity workflow.
- [ ] Re-run the same seeds after training and save one before/after artifact.
- [ ] Save one presentation-ready comparison trace from the refreshed heuristic baseline.
- [ ] Use the passing Northflank H100 setup to produce remote traces and comparisons from the real verifier path.
- [x] Deploy the environment to HF Space.
- [x] Add the public training notebook under `training/notebooks`.

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
