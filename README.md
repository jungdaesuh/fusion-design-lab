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

This repository is the clean hackathon workspace. The detailed planning docs live in [docs/FUSION_DESIGN_LAB_PLAN_V2.md](/Users/suhjungdae/code/fusion-design-lab/docs/FUSION_DESIGN_LAB_PLAN_V2.md), [docs/FUSION_DELIVERABLES_MAP.md](/Users/suhjungdae/code/fusion-design-lab/docs/FUSION_DELIVERABLES_MAP.md), and [docs/FUSION_NEXT_12_HOURS_CHECKLIST.md](/Users/suhjungdae/code/fusion-design-lab/docs/FUSION_NEXT_12_HOURS_CHECKLIST.md).

Implementation status:

- `P1` is locked as the benchmark task
- docs are aligned to fresh `P1` wiring in this repo
- shared models and server/client entry points exist
- the runtime environment still needs to be rewired from the old toy scaffold to the real `P1` contract

Current mode:

- strategic task choice is already locked
- the next work is implementation, smoke validation, and manual playtesting
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

1. Set up the Northflank Jupyter Notebook with PyTorch and attach persistent storage.
2. Pass a Northflank smoke test:
   - import `constellaration`
   - run one rotating-ellipse generation plus one low-fidelity verifier call
   - write an artifact to persistent storage
3. Rewrite [server/environment.py](/Users/suhjungdae/code/fusion-design-lab/server/environment.py) to the locked `P1` contract.
4. Rewrite [server/physics.py](/Users/suhjungdae/code/fusion-design-lab/server/physics.py) to use `constellaration`-based `P1` verification.
5. Add tracked `P1` fixtures under [server/data/p1](/Users/suhjungdae/code/fusion-design-lab/server/data/p1).
6. Add the Colab notebook under [training/notebooks](/Users/suhjungdae/code/fusion-design-lab/training/notebooks).
7. Run manual playtest episodes before heavy training work.

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
