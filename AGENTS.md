# AGENTS.md

This repository is for the Fusion Design Lab hackathon submission. Treat it as a clean, public-facing artifact repository, not a general research sandbox.

## Mission

Build and ship one clear, reproducible OpenEnv environment for budget-constrained stellarator design.

The core product is the environment:

- narrow task
- legible observation space
- discrete action space
- explicit constraints
- reward function that can be explained and iterated

Training is supporting evidence. Do not let the repo drift into training-first work.

## Source of Truth

Use these docs as the planning SSOT:

- `docs/FUSION_DESIGN_LAB_PLAN_V2.md`
- `docs/FUSION_DELIVERABLES_MAP.md`
- `docs/FUSION_NEXT_12_HOURS_CHECKLIST.md`

If code and docs disagree, either:

1. update code to match the docs, or
2. deliberately update the docs in the same change

Do not leave silent divergence.

## Project Priorities

1. Freeze the environment contract before heavy iteration.
2. Keep scope to one stable task.
3. Treat reward as iterative: `Reward V0`, then `Reward V1`, etc.
4. Manual-playtest before investing heavily in training.
5. Prefer behavior traces and baselines over reward-curve-only storytelling.
6. Keep claims conservative and evidence-backed.

## Working Rules

- Do not broaden the task family beyond the single stellarator environment unless explicitly requested.
- Do not add broad “other sciences” claims to docs or demo copy unless there is real supporting evidence.
- Do not narrate hypotheses as validated facts.
- Do not add complicated reward shaping until the simpler version has been tested against actual trajectories.
- Do not optimize notebook/training work ahead of local environment stability, remote environment stability, and baseline comparisons.

## Environment Contract Rules

Any change to the environment should preserve or deliberately update:

- observation schema
- action schema
- episode flow
- terminal conditions
- reward semantics

If you change one of these, update the corresponding documentation and tests in the same task.

## Reward Design Rules

When changing reward logic:

- document the previous behavior
- identify the pathology or exploit
- describe the change in plain language
- preserve a readable mapping from behavior to incentive

Avoid opaque reward changes that improve a metric without making the environment easier to reason about.

## Manual Playtesting

Before calling a reward design “good,” verify that a human can:

- read the observation
- choose a plausible next action
- understand why the reward changed

If a human cannot act coherently from the observation, fix the environment contract before doing more training work.

## Repo Layout

- `fusion_lab/`: shared typed models and client code
- `server/`: environment server, task contract, physics loop
- `baselines/`: random and heuristic baselines
- `training/`: evaluation or training notebooks
- `demo/`: demo assets and scripts
- `tests/`: focused tests for environment contract and repo behavior
- `docs/`: public-facing planning and submission docs

## Validation

For scoped changes, prefer the smallest relevant checks first.

Current useful commands:

```bash
python3 -m py_compile fusion_lab/models.py fusion_lab/client.py server/environment.py server/app.py server/physics.py
python3 -m pytest -q tests/test_repo_scaffold.py
```

As the repo grows, add more targeted tests instead of depending only on broad end-to-end runs.

## Git and Change Discipline

- Keep commits scoped to the task.
- Do not mix environment-contract edits with unrelated cleanup.
- Prefer small, reviewable increments.
- Branch names created for new work should use the `codex/` prefix.

## What Good Looks Like

A strong change in this repo usually does at least one of these:

- makes the environment contract clearer
- improves reproducibility
- adds or fixes a meaningful baseline
- strengthens the reward-iteration story
- makes the demo evidence easier to trust

If a change does not help one of those, question whether it belongs in this hackathon repo.
