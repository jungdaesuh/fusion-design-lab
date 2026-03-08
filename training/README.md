Training and evaluation notebooks belong here.

This repository treats notebooks and trained-policy runs as supporting evidence for the environment, not the primary product.

Training policy:

- train on the live low-fidelity environment surface, including explicit `submit`
- keep the standard `training/llm_rollout.py` monitor/evaluate workflow on the same live contract as the notebook
- keep high-fidelity validation in offline tooling such as `baselines/high_fidelity_validation.py`

## Status

- [ ] Northflank notebook artifacts saved
- [x] repository GRPO notebook saved
- [ ] Colab mirror or public notebook link saved if required by the submission surface
- [x] tiny low-fi PPO smoke artifact saved
- [ ] fixed-seed untrained baseline artifact saved
- [ ] before/after trained-policy evidence saved

## Runnable paths

- install the training dependencies: `uv sync --extra training`
- tiny low-fi PPO smoke run: `uv run --extra training python training/ppo_smoke.py`
- generate an LLM-ready prompt payload: `uv run python training/llm_rollout.py prompt --seed 0`
- replay an LLM completion or action plan: `uv run python training/llm_rollout.py replay --seed 0 --completion-file <path>`
- monitor reward terms, action clamping, and verifier outcomes across seeds:
  `uv run python training/llm_rollout.py monitor --completion-file <path> --seeds 0,1,2`
- generate fresh model completions per seed and save aggregate reward/outcome metrics:
  `uv run python training/llm_rollout.py evaluate --completion-command 'python path/to/model_cli.py' --seeds 0,1,2`

Use `monitor` when you already have one completion or one action plan and want a fixed replay across seeds.
Use `evaluate` for before/after policy comparison because it generates a fresh completion per seed.

## Current validation target

- save one untrained fixed-seed baseline with `evaluate`
- run one short GRPO pass on Northflank H100 with the repository notebook
- rerun the same seeds and compare reward plus low-fidelity feasibility before versus after

## Shared LLM Contract

The prompt/action/replay contract for LLM training lives in:

- `fusion_lab/llm_agent.py`

Use that module as the source of truth for:

- prompt formatting
- action-plan parsing
- local rollout replay
- rollout telemetry structure used by the monitor command

For `prompt`, `monitor`, `evaluate`, and the notebook, the shared helper contract now includes the live `submit` action.
Use offline validation scripts when you explicitly want high-fidelity checks outside the environment loop.

For `evaluate`, the completion command reads the prompt from `stdin` and writes a raw completion to `stdout`.
The current seed is exposed as the `FUSION_LAB_SEED` environment variable so the same command can be used
for fixed-seed before/after comparisons of untrained and trained checkpoints.
