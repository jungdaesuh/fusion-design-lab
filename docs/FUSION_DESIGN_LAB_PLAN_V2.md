# Fusion Design Lab — Plan V2

**Hackathon:** OpenEnv Hackathon, March 7-8, 2026
**Track:** Statement 3.1 (World Modeling — Professional Tasks)
**Status:** Judge-aligned rewrite of the main plan

## 1. Submission Thesis

We are not primarily submitting "a trained model for fusion."

We are submitting a clear, reproducible training environment for a constrained scientific design task:

- a junior plasma-scientist-style agent
- a small VMEC budget
- a narrow action space
- real simulator feedback
- explicit constraints
- a reward function that is understandable and iteratively improved

Training is supporting evidence. The environment is the product.

## 2. What Changed From V1

This version changes the center of gravity:

- `environment quality > training effort`
- `reward shaping story > polished final reward formula`
- `manual playtesting > training-first iteration`
- `clarity and reproducibility > broad unsupported transfer claims`

This version also separates:

- what is already decided
- what is a working hypothesis
- what must be validated before it becomes part of the final pitch

## 3. Judge-Aligned Priorities

The judging signal now implies four priorities:

1. The environment itself must be strong.
2. The reward function must be explainable and visibly iterated.
3. A human should be able to act in the environment coherently before we invest heavily in training.
4. The final story should emphasize a clear, reproducible environment, not just a reward curve.

## 4. Final Artifacts

The four visible artifacts remain:

1. HF Space environment
2. Colab notebook for evaluation or training
3. 1-minute demo video
4. Public repo and README

But the evidence order is:

1. environment contract
2. manual playtest log
3. reward iteration note
4. stable local and remote episodes
5. random and heuristic baselines
6. training or eval notebook evidence
7. demo and repo polish

## 5. Non-Negotiables

- One stable task only.
- No broad cross-science claims unless evidence exists.
- No training-first drift.
- No dependence on reward curves alone.
- No repo/video polish before environment and baselines are real.

## 6. Single Stable Task

We intentionally narrow the scope to one environment family:

- fixed-boundary, low-resolution, 2-period quasi-helical stellarator
- one baseline input
- small seed perturbation for episode variety
- budget of 6 VMEC runs per episode

The task is:

> improve quasi-symmetry under explicit constraints with limited simulation budget

### Constraints

- aspect ratio in `[4.5, 7.0]`
- edge iota in `[0.3, 0.6]`
- volume `> 0.5 m^3`

### Objective

- minimize quasi-symmetry residual

## 7. Environment Contract

The environment contract must be frozen before meaningful evaluation.

### Observation

The observation should expose:

- current quasi-symmetry residual
- best residual so far
- improvement from initial
- aspect ratio
- axis and edge iota
- volume
- magnetic well
- VMEC convergence status
- step number
- budget remaining
- target description
- concise textual summary of the last action outcome

The observation must be interpretable by a human without additional hidden state.

### Action Space

The action space stays intentionally small and discrete:

- `run`
- `submit`
- `restore_best`

For `run`, the controllable fields are:

- operator: one of a small fixed set of coefficients
- direction: increase or decrease
- magnitude: small, medium, large
- restart mode: hot or cold

This is not trying to expose the full plasma design space. The goal is a legible environment, not maximal realism.

### Episode Flow

1. Reset from baseline plus optional small seed perturbation.
2. Agent chooses one action.
3. Simulator or verifier runs.
4. Environment returns diagnostics and reward.
5. Episode ends on:
   - `submit`
   - exhausted budget

### Terminal Contract

The episode should end cleanly and deterministically.

At termination, the environment should provide:

- final best design metrics
- whether constraints were satisfied
- total reward
- short human-readable summary of the trajectory

## 8. Reward V0

The reward in this document is not the final reward. It is `Reward V0`.

The initial scoring idea remains:

- improvement in quasi-symmetry should help
- constraint violations should hurt
- VMEC non-convergence should hurt
- wasting budget should have some cost
- successful early submission may deserve a small bonus

### Reward V0 Design Goals

- easy to explain
- sensitive to genuine progress
- hostile to obvious degenerate behavior
- simple enough to debug from trajectories

### Reward V0 Failure Modes To Test

We should expect at least some of these:

- the agent spams large perturbations
- the agent oscillates between equivalent moves
- the agent overuses `restore_best`
- the agent never submits
- the agent submits too early
- the agent learns to preserve safety but not improve objective

The reward is only acceptable after we test for those behaviors.

## 9. What Is Hypothesis vs Validated

These are still hypotheses until manually or empirically checked:

- `large` perturbations are risky enough to make restart choice meaningful
- six runs are enough to create non-trivial decision pressure
- the chosen coefficients create a task that is neither trivial nor impossible
- `restore_best` is useful without becoming an exploit
- heuristic should beat random on mean episode reward

These should not be narrated as facts in the final demo until validated.

## 10. Manual Playtest Plan

Before heavy training, we should act as the agent ourselves.

### Protocol

Run 5 to 10 episodes manually and log for each step:

- observation seen
- action chosen
- reason for the action
- simulator outcome
- reward returned
- whether the reward matched intuitive quality

### Questions The Playtest Must Answer

- can a human understand what to do from the observation?
- do action labels map to meaningful decisions?
- is six-run budgeting interesting or arbitrary?
- which actions are high leverage?
- do obvious bad actions get punished?
- do obviously good actions get rewarded?
- does `restore_best` help recovery or encourage stalling?

### Expected Output

- short manual playtest log
- one paragraph on what a good episode looks like
- one paragraph on what broke or felt ambiguous

## 11. Reward Iteration Story

The reward iteration story is not a side note. It is likely part of the pitch.

We should aim to document at least one concrete sequence:

1. initial reward version
2. observed bad behavior
3. reward or penalty change
4. changed behavior afterward

Examples of acceptable story structure:

- "The agent kept making risky large moves, so we increased the non-convergence penalty."
- "The agent kept deferring commitment, so we adjusted terminal incentives."
- "The agent overused restore-best, so we changed the reward/step logic to make stalling unprofitable."

This is stronger than saying only "reward improved after training."

## 12. Evidence Plan

### HF Space

Must prove:

- remote `reset` works
- remote `step` works
- one stable episode runs end-to-end
- the remote behavior matches the local contract

### Colab Notebook

Primary job:

- connect to the live environment
- run multi-turn episodes
- export traces and baseline comparisons

Secondary job:

- show training or policy improvement if the signal is credible

If training is weak but the environment and eval traces are strong, the notebook still ships.

### Demo Video

The video should show:

1. the task
2. the environment observation and action space
3. one manual or agent trajectory
4. one reward pathology and fix
5. one baseline comparison

Reward curves are optional supporting visuals, not the center of the story.

### Public Repo

The repo should make the environment easy to understand:

- what the task is
- what the agent sees
- what the agent can do
- how reward works
- how to run one episode
- where the demo evidence lives

## 13. Success Gates

### Gate 1: Environment Contract Locked

- task frozen
- observation schema frozen
- action schema frozen
- terminal conditions frozen

### Gate 2: Manual Playtest Pass

- human can act coherently
- at least one trajectory feels sensible
- at least one pathology identified or ruled out

### Gate 3: Stable Local Episode

- local modify -> solve -> observe loop works
- at least one end-to-end episode is stable

### Gate 4: Reward V1

- at least one reward revision completed
- story is documented with before/after behavior

### Gate 5: Baselines

- random baseline complete
- heuristic baseline complete
- heuristic is at least competitive and preferably better than random

### Gate 6: Remote Environment

- HF Space live
- remote client runs one clean episode

### Gate 7: Notebook Evidence

- notebook runs end-to-end
- traces exported
- training evidence included only if it adds signal

## 14. Timeline

### Phase 0

Lock the environment contract and validate the minimal toolchain needed to play the game.

Deliverables:

- frozen task definition
- frozen action and observation schema
- proof that one VMEC modify -> run -> diagnose loop works

### Phase 1

Manual-playtest the environment.

Deliverables:

- 5 to 10 episode logs
- notes on leverage, ambiguity, and pathologies

### Phase 2

Implement or refine Reward V0 into Reward V1 based on real behavior.

Deliverables:

- documented exploit
- documented fix
- updated reward logic

### Phase 3

Stabilize one local task and run baselines.

Deliverables:

- stable local trajectory
- random baseline
- heuristic baseline

### Phase 4

Deploy HF Space and validate remote parity.

Deliverables:

- live environment
- one stable remote episode

### Phase 5

Produce notebook evidence.

Deliverables:

- Colab notebook
- traces
- baseline comparison
- training outputs only if persuasive

### Phase 6

Record the demo and make the repo readable.

Deliverables:

- 1-minute video
- public README
- linked artifacts

## 15. Fallback Rules

If something goes wrong, the fallback should preserve the environment story.

### If training signal is weak

Do not force a training-centric pitch.

Ship:

- strong environment
- manual playtest evidence
- reward iteration story
- baseline traces
- one stable remote demo

### If reward is unstable

Reduce ambition:

- keep only the terms we can explain
- remove fragile shaping
- prefer legible trajectories over complex reward composition

### If the task is too hard

Do not broaden scope.

Instead:

- simplify the starting configuration
- tighten the action set
- make the task more learnable within six runs

### If the task is too easy

Do not add more domains.

Instead:

- adjust budget
- adjust magnitudes
- adjust reward to discourage trivial submission

## 16. Demo Story

The recommended demo structure is:

### Part 1: Problem

"The agent gets a small VMEC budget to improve a stellarator design while staying within constraints."

### Part 2: Environment

"Here is what the agent sees, what it can change, and what counts as success."

### Part 3: Reward Iteration

"Our first reward version produced a bad behavior. We changed the penalty or incentive, and the behavior improved."

### Part 4: Evidence

"Here is one stable trajectory, plus random and heuristic baselines."

### Part 5: Why It Matters

"This is a clear, reproducible simulation environment for budget-constrained scientific decision-making."

That last line is intentionally conservative. It is strong enough without claiming universal scientific transfer.

## 17. Immediate Next Actions

1. Freeze the environment contract in code and docs.
2. Run manual playtests before heavy training work.
3. Mark the current reward as `V0`.
4. Log the first real pathology and reward revision.
5. Do not let notebook or video work outrun the environment evidence.
