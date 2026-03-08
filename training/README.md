Training and evaluation notebooks belong here.

This repository treats notebooks and trained-policy runs as supporting evidence for the environment, not the primary product.

Training policy:

- train on the low-fidelity `run` surface for the normal RL inner loop
- use high-fidelity `submit` only for sparse checkpoint evaluation, paired fixture checks, submit-side traces, and final evidence
- if low-fidelity gains do not survive high-fidelity `submit`, stop training and fix the environment or reward before pushing further

## Status

- [ ] Northflank notebook artifacts saved
- [ ] Colab notebook saved
- [x] tiny low-fi PPO smoke artifact saved
- [ ] trained-policy evidence saved

## Runnable paths

- install the training dependencies: `uv sync --extra training`
- tiny low-fi PPO smoke run: `uv run --extra training python training/ppo_smoke.py`
- generate an LLM-ready prompt payload: `uv run python training/llm_rollout.py prompt --seed 0`
- replay an LLM completion or action plan: `uv run python training/llm_rollout.py replay --seed 0 --completion-file <path>`
- monitor reward terms, action clamping, and verifier outcomes across seeds:
  `uv run python training/llm_rollout.py monitor --completion-file <path> --seeds 0,1,2`
- generate fresh model completions per seed and save aggregate reward/outcome metrics:
  `uv run python training/llm_rollout.py evaluate --completion-command 'python path/to/model_cli.py' --seeds 0,1,2`

## Shared LLM Contract

The prompt/action/replay contract for LLM training lives in:

- `fusion_lab/llm_agent.py`

Use that module as the source of truth for:

- prompt formatting
- action-plan parsing
- local rollout replay
- rollout telemetry structure used by the monitor command

For `evaluate`, the completion command reads the prompt from `stdin` and writes a raw completion to `stdout`.
The current seed is exposed as the `FUSION_LAB_SEED` environment variable so the same command can be used
for fixed-seed before/after comparisons of untrained and trained checkpoints.
