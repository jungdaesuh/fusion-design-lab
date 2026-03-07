# Fusion Design Lab

Fusion Design Lab is an environment-first OpenEnv hackathon project for budget-constrained stellarator design.

The repo is organized around one clear submission thesis:

- a narrow, reproducible stellarator design task
- a small discrete action space
- real simulator feedback
- explicit constraints
- a reward function that is iteratively improved through observed behavior

Training is supporting evidence. The environment is the product.

## Current Status

This repository is the clean hackathon workspace. The detailed planning docs live in [docs/FUSION_DESIGN_LAB_PLAN_V2.md](/Users/suhjungdae/code/fusion-design-lab/docs/FUSION_DESIGN_LAB_PLAN_V2.md), [docs/FUSION_DELIVERABLES_MAP.md](/Users/suhjungdae/code/fusion-design-lab/docs/FUSION_DELIVERABLES_MAP.md), and [docs/FUSION_NEXT_12_HOURS_CHECKLIST.md](/Users/suhjungdae/code/fusion-design-lab/docs/FUSION_NEXT_12_HOURS_CHECKLIST.md).

Implementation status:

- repo scaffolded
- shared models defined
- server and client entry points stubbed
- environment contract ready to be implemented next

## Planned Repository Layout

```text
fusion-design-lab/
├── baselines/
├── demo/
├── docs/
├── fusion_lab/
├── server/
├── tests/
├── training/
├── openenv.yaml
├── pyproject.toml
└── README.md
```

## Immediate Next Steps

1. Implement the environment contract in `server/environment.py`.
2. Implement the VMEC-backed physics loop in `server/physics.py`.
3. Add one stable local episode test.
4. Run manual-playtest episodes before heavy training work.

