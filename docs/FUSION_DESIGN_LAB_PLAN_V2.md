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
- the live environment is now unified onto one low-fidelity reward and verifier surface
- `submit` remains an explicit terminal action on that same live contract
- explicit VMEC failure semantics are implemented
- the Northflank smoke workflow is committed
- the Northflank smoke test passed on the team H100
- baseline comparison has been rerun on the real verifier path
- a coarse measured sweep note now exists
- the first tracked low-fidelity fixtures now exist
- an initial low-fidelity manual playtest note now exists
- paired high-fidelity fixture checks for those tracked fixtures now exist
- one submit-side manual playtest trace exists
- the repository GRPO notebook is checked in and aligned to the shared `fusion_lab/llm_agent.py` helper contract
- model-driven fixed-seed low-fidelity `monitor` / `evaluate` tooling exists for LLM baselines

Still open:

- decision on whether reset-seed pool should change from paired checks
- HF Space deployment evidence
- public Colab mirror or notebook submission link, if the submission surface still requires it
- before/after trained-policy evidence on the current unified low-fidelity workflow
- demo and README polish after the artifacts are real

Current caution:

- do not present repaired-family ranges, deltas, or budget choices as settled defaults until the measured sweep is recorded
- do not narrate low-fidelity rollout metrics as final submission truth
- the standard notebook and `training/llm_rollout.py` paths should stay on the same live low-fidelity contract as the environment, including explicit `submit`
- reserve higher-fidelity validation for paired fixture checks, offline validation scripts, and final evidence

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
- stop after a few readable trajectories or one clear failure mode
- run paired high-fidelity fixture checks and one real submit-side trace immediately after the smoke run
- do not use low-fidelity training alone as proof that the terminal `submit` contract is trustworthy
- keep any checkpoint high-fidelity evaluation sparse enough that it does not replace the low-fidelity inner loop

## 5. Document Roles

Use the docs like this:

- this file defines planning order, status, gates, and fallback rules
- [`P1_ENV_CONTRACT_V1.md`](P1_ENV_CONTRACT_V1.md) defines the live technical contract
- [`P1_PARAMETERIZATION_DEEPDIVE.md`](P1_PARAMETERIZATION_DEEPDIVE.md) keeps blocker evidence, sweep evidence, and supporting rationale
- archived legacy planning docs live under [`archive/`](archive/) and are not active SSOT surfaces

## 6. Artifact Plan

Visible artifacts:

- [x] HF Space environment
- [x] Repository training notebook
- [ ] Public Colab mirror or submission notebook link if required
- [ ] 1-minute demo video
- [x] Public repo and README

Compute surfaces:

- Northflank is the main compute workspace for verifier-heavy work
- HF Space is the hosted environment surface
- the public notebook artifact should show trained-policy behavior against the live environment and can be mirrored to Colab if the submission form still requires it
- trained-policy work should iterate on the same live low-fidelity environment contract that will be demoed publicly

Evidence order:

- [x] measured sweep note
- [x] fixture checks
- [x] manual playtest log
- [x] tiny low-fi PPO smoke trace
- [x] shared-helper notebook alignment
- [x] model-driven low-fi LLM evaluation tooling
- [ ] reward iteration note
- [ ] stable local and remote episodes
- [x] random and heuristic baselines
- [ ] before/after trained-policy evidence
- [ ] demo and repo polish

## 7. Environment Summary

The environment contract must stay narrow and legible:

- one repaired low-dimensional boundary family derived from a rotating-ellipse seed
- discrete `run | submit | restore_best` interaction
- one low-fidelity verifier surface for all live environment actions
- readable observation surface with explicit fidelity labeling
- `Reward V2` keeps the verifier-native `Reward V1` core and adds small best-so-far / anti-stagnation shaping for the low-fi repair loop

The live technical details belong in [`P1_ENV_CONTRACT_V1.md`](P1_ENV_CONTRACT_V1.md), not here.

## 8. Execution Order

- [x] Run a tiny low-fidelity PPO smoke pass and stop after a few trajectories once it reveals either readable behavior or one clear failure mode.
- [x] Pair the tracked low-fidelity fixtures with higher-fidelity validation checks immediately after the PPO smoke pass.
- [ ] Decide whether the reset pool should change based on the measured sweep plus those paired checks.
- [x] Run at least one submit-side manual trace, then expand to 5 to 10 episodes and record the first real confusion point, exploit, or reward pathology.
- [ ] Save one fixed-seed untrained baseline with the unified live `training/llm_rollout.py evaluate` workflow.
- [ ] Run one short H100 GRPO pass with the repository notebook on that same unified low-fidelity workflow.
- [ ] Re-run the same seeds after training and save one before/after artifact.
- [ ] Adjust reward or penalties only if playtesting exposes a concrete problem.
- [x] Refresh the heuristic baseline using the repaired-family evidence.
- [ ] Prove a stable local episode path.
- [ ] Deploy the same task contract to HF Space and prove one clean remote episode.
- [ ] Publish or mirror the notebook artifact only after the live before/after path is real.
- [ ] Record the demo around environment clarity, reward iteration, and baseline evidence.
- [ ] Polish the public repo only after the artifacts above exist.

## 9. Success Gates

Gate 1: measured sweep exists

- repaired-family ranges, deltas, and reset seeds are justified by recorded evidence

Gate 2: tiny PPO smoke is sane

- a small low-fidelity policy can improve or at least reveal a concrete failure mode quickly
- trajectories are readable enough to debug
- the smoke run stops at that diagnostic threshold instead of turning into a broader training phase
- current status: passed as a plumbing/debugging gate, with the first exposed failure mode recorded in [`P1_PPO_SMOKE_NOTE.md`](P1_PPO_SMOKE_NOTE.md)

Gate 3: fixture checks pass

- good, boundary, and bad references behave as expected
- the paired high-fidelity checks happen immediately after the PPO smoke run, not as optional later work

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

- the public notebook artifact, demo, and README all reflect the actual environment rather than a hypothetical future one

Gate 9: trained-policy evidence is real

- one fixed-seed untrained baseline exists
- one short low-fidelity training pass exists on the same workflow
- the repo can show a before/after comparison on the same seeds using the live environment contract, including `submit`

## 10. Fallback Rules

If training evidence is weak:

- keep claims conservative about policy quality
- still ship a trained-policy demonstration and document its limitations plainly
- do not skip the paired higher-fidelity validation artifacts
- do not split the notebook back onto a different submit contract than the live environment

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
- [x] Run a tiny low-fidelity PPO smoke pass and save a few trajectories.
- [x] Pair the tracked fixtures with higher-fidelity validation checks.
- [x] Record one submit-side manual trace.
- [x] Refresh the heuristic baseline from that playtest evidence.
- [ ] Save one fixed-seed untrained baseline with `training/llm_rollout.py evaluate`.
- [ ] Run one short H100 GRPO pass with `training/notebooks/fusion_design_lab_training.ipynb`.
- [ ] Re-run the same seeds and save a before/after artifact.
- [ ] Verify one clean HF Space episode with the same contract.
