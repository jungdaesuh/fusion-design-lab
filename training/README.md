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

## Shared LLM Contract

The prompt/action/replay contract for LLM training lives in:

- `fusion_lab/llm_agent.py`

Use that module as the source of truth for:

- prompt formatting
- action-plan parsing
- local rollout replay
