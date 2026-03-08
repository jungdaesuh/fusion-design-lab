# P1 PPO Smoke Note

This note records the current tiny low-fidelity PPO smoke pass on the repaired 4-knob `P1` environment.

## Purpose

This run is diagnostic-only.

It exists to answer:

- can a small PPO policy interact with the low-fidelity environment without code-path failures
- can the smoke trainer discover any real positive repair signal quickly
- what is the first obvious remaining behavior problem before any broader training push

It does **not** validate the high-fidelity `submit` contract.

## Command

```bash
uv sync --extra training
uv run --extra training python training/ppo_smoke.py --eval-episodes 3 --seed 0
```

## Artifact

- ignored runtime artifact: `training/artifacts/ppo_smoke/ppo_smoke_20260308T090723Z.json`

## Configuration

- training mode: low-fidelity only
- training reset seeds: easy-seed curriculum (`seed 2` only)
- evaluation reset seeds: frozen seeds `0`, `1`, and `2`
- action space: 2 diagnostic repair actions
  - `rotational_transform increase medium`
  - `triangularity_scale increase medium`
- `submit`: intentionally excluded from the smoke loop
- total timesteps: `32`
- evaluation episodes: `3`
- device: `cpu`

## Result

- the smoke path executed successfully and wrote a trajectory artifact
- the trained policy discovered a real positive repair move and reached feasibility on the easy evaluation seed
- the trained policy did **not** generalize across all frozen evaluation seeds yet
- summary metrics:
  - `mean_eval_reward = -0.1204`
  - `constraint_satisfaction_rate = 0.3333`

## What Changed

The original smoke trainer was asking PPO to solve too much at once:

- a 25-action search space
- mixed one-step and two-step repair behavior across seeds
- no direct access to current control parameters in the observation
- no early stop on first success or first failure

The current smoke trainer is now intentionally narrower:

- observation includes current control parameters and explicit low-fidelity state fields
- episodes stop on first feasible crossing or first failed evaluation
- the action space is narrowed to the two known repair actions
- training uses the easiest frozen seed so the smoke question stays diagnostic

## Current Behavior

Deterministic evaluation now repeats a repair-seeking action instead of the older crashing loop:

- policy action: `triangularity_scale increase medium`
- seed `2`: reaches feasibility in one step with reward `+3.1533`
- seeds `0` and `1`: keeps pushing triangularity in the same direction, improves nothing after the first few steps, and times out with negative reward

This is useful smoke evidence because it shows:

- the PPO training path is wired correctly enough to produce trajectories
- the smoke trainer can now discover a real positive repair signal instead of only collapsing into a bad local action
- the next remaining issue is not plumbing; it is limited cross-seed generalization even inside the smoke action subset

## Current Conclusion

The smoke pass is now doing the right job:

- it is still diagnostic-only
- it proves the low-fidelity PPO path can find at least one real repair action
- it still leaves broader training work open, because the policy does not yet solve all frozen seeds
