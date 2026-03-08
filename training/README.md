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
