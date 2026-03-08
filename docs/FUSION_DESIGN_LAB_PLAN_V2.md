# Fusion Design Lab — Plan V2

**Hackathon:** OpenEnv Hackathon, March 7-8, 2026
**Track:** Statement 3.1 (World Modeling — Professional Tasks)
**Role:** Planning and execution SSOT for this repo
**Updated:** March 8, 2026

## 1. Submission Thesis

Fusion Design Lab is not only a "trained model for fusion" submission.

It is a clear, reproducible environment for one constrained scientific design task:

- official `P1` benchmark semantics
- narrow, human-playable action space
- real verifier feedback from `constellaration`
- explicit constraints and failure semantics
- reward logic that can be explained and iterated

The environment is the product. A trained policy is required supporting evidence because it demonstrates that the environment is learnable in practice rather than only manually playable.

## 2. Current State

Completed:

- `P1` is locked as the single benchmark task
- the repaired 4-knob low-dimensional runtime is live in code
- the official `constellaration` verifier path is wired
- low-fidelity `run` and high-fidelity `submit` are separated clearly
- terminal scoring and reporting are fidelity-consistent
- explicit VMEC failure semantics are implemented
- the Northflank smoke workflow is committed
- the Northflank smoke test passed on the team H100
- baseline comparison has been rerun on the real verifier path
- a coarse measured sweep note now exists
- the first tracked low-fidelity fixtures now exist
- an initial low-fidelity manual playtest note now exists

Still open:

- tiny low-fidelity PPO smoke evidence
- paired high-fidelity checks for the tracked fixtures
- submit-side manual playtest evidence
- heuristic baseline refresh on the repaired real-verifier path
- HF Space deployment evidence
- Colab artifact wiring
- demo and README polish after the artifacts are real

Current caution:

- do not present repaired-family ranges, deltas, or budget choices as settled defaults until the measured sweep is recorded
- do not narrate low-fidelity rollout metrics as final submission truth

## 3. Locked Decisions

These decisions are fixed unless a hard blocker appears:

- benchmark task: `P1`
- submission framing: `Statement 3.1`
- verifier of record: `constellaration.problems.GeometricalProblem`
- repo strategy: fresh wiring in this repo
- reuse policy: do not port the old `ai-sci-feasible-designs` harness
- scope rule: one stable task only

Execution rule:

- do not reopen strategy unless a real blocker appears
- convert decisions into code, fixtures, traces, baselines, or deployment work

## 4. Non-Negotiables

- Keep scope to one stable task.
- Keep claims conservative and evidence-backed.
- Do not let training-first work outrun environment stability.
- Do not rely on reward curves alone; keep trajectory evidence.
- Do not use reward complexity to hide a blocked action family.
- Do not polish repo or video before the environment and baselines are real.

Practical fail-fast rule:

- allow a tiny low-fidelity PPO smoke run before full submit-side validation
- use it only to surface obvious learnability bugs, reward exploits, or action-space problems
- do not use low-fidelity training alone as proof that the terminal `submit` contract is trustworthy

## 5. Document Roles

Use the docs like this:

- this file defines planning order, status, gates, and fallback rules
- [`P1_ENV_CONTRACT_V1.md`](P1_ENV_CONTRACT_V1.md) defines the live technical contract
- [`P1_PARAMETERIZATION_DEEPDIVE.md`](P1_PARAMETERIZATION_DEEPDIVE.md) keeps blocker evidence, sweep evidence, and supporting rationale
- archived legacy planning docs live under [`archive/`](archive/) and are not active SSOT surfaces

## 6. Artifact Plan

Visible artifacts:

- [ ] HF Space environment
- [ ] Required Colab notebook
- [ ] 1-minute demo video
- [x] Public repo and README

Compute surfaces:

- Northflank is the main compute workspace for verifier-heavy work
- HF Space is the hosted environment surface
- Colab is the required public artifact and should show trained-policy behavior against the live environment

Evidence order:

- [x] measured sweep note
- [ ] fixture checks
- [x] manual playtest log
- [ ] tiny low-fi PPO smoke trace
- [ ] reward iteration note
- [ ] stable local and remote episodes
- [x] random and heuristic baselines
- [ ] notebook evidence
- [ ] demo and repo polish

## 7. Environment Summary

The environment contract must stay narrow and legible:

- one repaired low-dimensional boundary family derived from a rotating-ellipse seed
- discrete `run | submit | restore_best` interaction
- low-fidelity verifier for normal steps
- high-fidelity verifier for `submit`
- readable observation surface with explicit fidelity labeling
- `Reward V0` kept simple and feasibility-first until playtesting proves a real pathology

The live technical details belong in [`P1_ENV_CONTRACT_V1.md`](P1_ENV_CONTRACT_V1.md), not here.

## 8. Execution Order

- [ ] Run a tiny low-fidelity PPO smoke pass and inspect a few trajectories for obvious learnability failures or reward exploits.
- [ ] Pair the tracked low-fidelity fixtures with high-fidelity submit checks.
- [ ] Decide whether the reset pool should change based on the measured sweep plus those paired checks.
- [ ] Run at least one submit-side manual trace, then expand to 5 to 10 episodes and record the first real confusion point, exploit, or reward pathology.
- [ ] Adjust reward or penalties only if playtesting exposes a concrete problem.
- [ ] Refresh the heuristic baseline using the repaired-family evidence.
- [ ] Prove a stable local episode path.
- [ ] Deploy the same task contract to HF Space and prove one clean remote episode.
- [ ] Wire the Colab artifact to the live environment.
- [ ] Record the demo around environment clarity, reward iteration, and baseline evidence.
- [ ] Polish the public repo only after the artifacts above exist.

## 9. Success Gates

Gate 1: measured sweep exists

- repaired-family ranges, deltas, and reset seeds are justified by recorded evidence

Gate 2: fixture checks pass

- good, boundary, and bad references behave as expected

Gate 3: tiny PPO smoke is sane

- a small low-fidelity policy can improve or at least reveal a concrete failure mode quickly
- trajectories are readable enough to debug

Gate 4: manual playtest passes

- a human can read the observation
- a human can choose a plausible next action
- a human can explain the reward change

Gate 5: local episode is stable

- one clean trajectory is reproducible enough for demo use

Gate 6: baseline story is credible

- heuristic behavior is at least interpretable and preferable to random on the repaired task

Gate 7: remote surface is real

- HF Space preserves the same task contract as local

Gate 8: submission artifacts exist

- Colab, demo, and README all reflect the actual environment rather than a hypothetical future one

## 10. Fallback Rules

If training evidence is weak:

- keep claims conservative about policy quality
- still ship a trained-policy demonstration and document its limitations plainly
- do not skip the paired high-fidelity checks or submit-side manual trace

If HF Space deployment is delayed:

- keep local and Northflank evidence first
- document the deployment blocker plainly
- do not invent remote claims without a real run

If reward behavior is confusing:

- fix observation clarity, step magnitudes, seed choice, or terminal semantics before adding reward complexity

If the repaired family is too hard:

- adjust ranges, deltas, or seeds from measured evidence
- do not expand into a broad Fourier action space just to rescue the hackathon scope

If the repaired family is too easy:

- prefer fixture and seed adjustments before broadening the action schema

## 11. Immediate Next Actions

- [x] Record the measured sweep and choose provisional defaults from evidence.
- [x] Check in tracked fixtures.
- [x] Record the first manual playtest log.
- [ ] Run a tiny low-fidelity PPO smoke pass and save a few trajectories.
- [ ] Pair the tracked fixtures with high-fidelity submit checks.
- [ ] Record one submit-side manual trace.
- [ ] Refresh the heuristic baseline from that playtest evidence.
- [ ] Verify one clean HF Space episode with the same contract.
