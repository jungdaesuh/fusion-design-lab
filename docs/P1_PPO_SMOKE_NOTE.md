# P1 PPO Smoke Note

This note records the first tiny low-fidelity PPO smoke pass on the repaired 4-knob `P1` environment.

## Purpose

This run is diagnostic-only.

It exists to answer:

- can a small PPO policy interact with the low-fidelity environment without code-path failures
- does the reward surface produce a readable early failure mode
- what is the first obvious behavior problem before any broader training push

It does **not** validate the high-fidelity `submit` contract.

## Command

```bash
uv sync --extra training
uv run --extra training python training/ppo_smoke.py --eval-episodes 1
```

## Artifact

- ignored runtime artifact: `training/artifacts/ppo_smoke/ppo_smoke_20260308T062412Z.json`

## Configuration

- training mode: low-fidelity only
- action space: 24 `run` actions + `restore_best`
- `submit`: intentionally excluded from the smoke loop
- total timesteps: `64`
- evaluation episodes: `1`
- device: `cpu`

## Result

- the smoke path executed successfully and wrote a trajectory artifact
- the trained policy did **not** reach feasibility in the evaluation episode
- summary metrics:
  - `mean_eval_reward = -1.1`
  - `constraint_satisfaction_rate = 0.0`

## First failure mode

The policy collapsed to a repeated low-fidelity action:

- `aspect_ratio increase medium`

Observed behavior:

- the same action repeated for the full 6-step budget
- feasibility stayed near `0.050653`
- final reward was negative because the agent burned the budget without finding a repair path

This is useful smoke evidence because it shows:

- the PPO training path is wired correctly enough to produce trajectories
- the current low-fidelity surface still permits an obvious local-behavior failure
- the next step should remain paired high-fidelity fixture checks plus at least one submit-side manual trace, not a broader training push
