# Fusion Design Lab — Plan V2

**Hackathon:** OpenEnv Hackathon, March 7-8, 2026
**Track:** Statement 3.1 (World Modeling — Professional Tasks)
**Status:** Judge-aligned plan with `P1` locked

## 1. Submission Thesis

We are not primarily submitting "a trained model for fusion."

We are submitting a clear, reproducible training environment for a constrained scientific design task:

- official `P1` benchmark semantics
- a narrow, human-playable action space
- real verifier feedback from `constellaration`
- explicit constraints
- a reward function that is understandable and iteratively improved

Training is supporting evidence. The environment is the product.

## 2. Locked Decisions

These decisions are now fixed unless a hard blocker appears:

- benchmark task: `P1`
- submission framing: `Statement 3.1`
- verifier of record: `constellaration.problems.GeometricalProblem`
- implementation strategy: fresh wiring in this repo
- reuse policy: do not port the old `ai-sci-feasible-designs` harness; only reuse selected JSON artifacts or boundaries when useful

Execution rule after lock:

- do not reopen these decisions in new planning passes unless a real blocker appears
- once a decision is locked, translate it into code, fixtures, baselines, or deployment work

## 3. What Changed From V1

This version changes the center of gravity:

- `environment quality > training effort`
- `reward shaping story > polished final reward formula`
- `manual playtesting > training-first iteration`
- `clarity and reproducibility > broad unsupported transfer claims`
- `fresh, minimal environment wiring > transplanting legacy orchestration`

This version also separates:

- what is already decided
- what is a working hypothesis
- what must be validated before it becomes part of the final pitch

## 4. Judge-Aligned Priorities

The judging signal now implies four priorities:

1. The environment itself must be strong.
2. The reward function must be explainable and visibly iterated.
3. A human should be able to act in the environment coherently before we invest heavily in training.
4. The final story should emphasize a clear, reproducible environment, not just a reward curve.

## 5. Final Artifacts

The four visible artifacts remain:

1. HF Space environment
2. Colab notebook for evaluation or training
3. 1-minute demo video
4. Public repo and README

The primary compute workspace should be Northflank:

- Northflank Jupyter Notebook with PyTorch on the team H100 for development, verifier integration, baselines, and training/debugging
- HF Space as the hosted environment surface
- Colab as the minimal required public notebook artifact

But the evidence order is:

1. environment contract
2. manual playtest log
3. reward iteration note
4. stable local and remote episodes
5. random and heuristic baselines
6. training or eval notebook evidence
7. demo and repo polish

## 6. Non-Negotiables

- One stable task only.
- No broad cross-science claims unless evidence exists.
- No training-first drift.
- No dependence on reward curves alone.
- No repo/video polish before environment and baselines are real.
- No harness transplant from `ai-sci-feasible-designs`.
- No new strategy churn after `P1` + rotating-ellipse is locked unless a blocker forces it.

## 7. Single Stable Task

We intentionally narrow the scope to one environment family:

- `P1` geometrical benchmark
- rotating-ellipse, low-dimensional design space
- official `constellaration` verifier
- low-fidelity evaluation for ordinary interaction
- optional high-fidelity verification for final checks or `submit`

The task is:

> improve a stellarator boundary on the `P1` benchmark under explicit constraints and limited evaluation budget

### Constraints

Use the official `P1` constraints:

- aspect ratio `<= 4.0`
- average triangularity `<= -0.5`
- edge rotational transform over field periods `>= 0.3`

### Objective

Use the official `P1` objective:

- minimize `max_elongation`

### Why This Task

- it is official rather than invented
- it is cheaper than `P2` and `P3` because `P1` skips QI
- it maps cleanly to a tool-using scientific workflow
- it is easier to explain than a broader fusion-design claim

## 8. Fresh Wiring Rule

This repo should implement a minimal environment directly for the hackathon.

That means:

- define our own environment contract
- define our own reward logic on top of the official verifier
- define our own baselines
- define our own HF Space interface

That does not mean:

- importing the old governor
- importing the old planner
- importing the old experiment harness
- recreating the old agent-as-coder stack

Allowed reuse:

- official `constellaration` library behavior
- selected JSON artifacts or seed boundaries
- problem notes as human reference

Implementation handoff:

- the remaining work is now wiring, smoke validation, manual playtesting, baselines, and deployment
- do not treat supporting decision notes as a new planning backlog

## 8.1 Compute Surfaces

Use each surface for one clear purpose:

- Northflank Jupyter Notebook with PyTorch:
  - main development and compute workspace
  - verifier sanity checks
  - manual playtesting
  - baseline runs
  - optional RL fine-tuning
- HF Space:
  - public OpenEnv environment surface
  - remote `reset` and `step` endpoint for the final demo path
- Colab:
  - minimal reproducible evaluation or training notebook required by the hackathon

Northflank-specific constraint:

- containers are ephemeral, so persistent storage must be attached before relying on saved models, caches, or fixture downloads

Deployment path:

- develop and verify in Northflank or local
- commit and push changes to the public GitHub repo
- have HF Space build and serve from that repo path
- do not rely on manual copy-paste deployment as the default path

Auth stance:

- prefer a public HF Space for the hackathon to keep the Colab artifact simple
- if the Space must be private, the notebook must explicitly document token-based access

## 9. Environment Contract

The environment contract must be frozen before meaningful evaluation.

### Observation

The observation should expose:

- current `max_elongation`
- current aspect ratio
- current average triangularity
- current edge rotational transform over field periods
- current feasibility score or normalized violation summary
- best-so-far feasible score
- best-so-far least-violating design summary
- step number
- budget remaining
- concise textual summary of the last action outcome

The observation must be interpretable by a human without additional hidden state.

### Action Space

The action space stays intentionally small and discrete:

- `run`
- `submit`
- `restore_best`

For `run`, the controllable fields are:

- parameter: one of
  - `aspect_ratio`
  - `elongation`
  - `rotational_transform`
- direction: increase or decrease
- magnitude: small, medium, large

This is not trying to expose the full Fourier-boundary space. The goal is a legible environment, not maximal realism.

### Episode Flow

1. Reset from one rotating-ellipse initial state or a small frozen set of initial states.
2. Agent chooses one action.
3. Low-fidelity verifier runs for normal interaction.
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

## 10. Verifier Contract

The verifier of record is `constellaration.problems.GeometricalProblem`.

The environment must preserve:

- objective direction
- constraint direction
- feasibility semantics
- score ordering

The environment may add reward shaping, but it must not redefine what `P1` means.

## 11. Reward V0

The reward in this document is not the final reward. It is `Reward V0`.

The initial scoring idea should be feasibility-first:

- reducing normalized constraint violation should help
- becoming feasible should give a meaningful bonus
- once feasible, lower `max_elongation` should help
- wasting budget should have some cost
- successful submission may deserve a small bonus

### Reward V0 Design Goals

- easy to explain
- sensitive to genuine progress
- hostile to obvious degenerate behavior
- simple enough to debug from trajectories
- aligned with official `P1` semantics

### Reward V0 Failure Modes To Test

We should expect at least some of these:

- the agent oscillates between equivalent moves
- the agent submits too early
- the agent never submits
- the agent learns to improve objective before it learns feasibility
- the agent camps near one constraint while breaking another
- the agent overuses `restore_best`

The reward is only acceptable after we test for those behaviors.

## 12. Verifier and Reward Fixture Checks

Before training, we should validate environment wiring with a few fixed fixtures.

Use:

- one known-good design or near-winning design
- a few near-boundary designs
- a few clearly infeasible designs

Purpose:

- verify the verifier is wired correctly
- verify the reward ordering makes sense
- verify feasible designs outrank clearly infeasible ones

This is calibration, not training.

## 13. What Is Hypothesis vs Validated

These are still hypotheses until manually or empirically checked:

- six steps are enough to create non-trivial decision pressure
- the rotating-ellipse action space is expressive enough for a meaningful `P1` task
- `restore_best` is useful without becoming an exploit
- heuristic should beat random on mean episode reward
- low-fidelity interaction is predictive enough for useful policy learning

These should not be narrated as facts in the final demo until validated.

## 14. Manual Playtest Plan

Before heavy training, we should act as the agent ourselves.

### Protocol

Run 5 to 10 episodes manually and log for each step:

- observation seen
- action chosen
- reason for the action
- verifier outcome
- reward returned
- whether the reward matched intuitive quality

### Questions The Playtest Must Answer

- can a human understand what to do from the observation?
- do action labels map to meaningful decisions?
- is the step budget interesting or arbitrary?
- which actions are high leverage?
- do obvious bad actions get punished?
- do obviously good actions get rewarded?
- does `restore_best` help recovery or encourage stalling?

### Expected Output

- short manual playtest log
- one paragraph on what a good episode looks like
- one paragraph on what broke or felt ambiguous

## 15. Reward Iteration Story

The reward iteration story is not a side note. It is likely part of the pitch.

We should aim to document at least one concrete sequence:

1. initial reward version
2. observed bad behavior
3. reward or penalty change
4. changed behavior afterward

Examples of acceptable story structure:

- "The agent improved elongation while staying deeply infeasible, so we increased feasibility-first shaping."
- "The agent hovered near one constraint and ignored another, so we changed the violation shaping."
- "The agent overused restore-best, so we changed the reward or step logic to make stalling unprofitable."

This is stronger than saying only "reward improved after training."

## 16. Evidence Plan

### HF Space

Must prove:

- remote `reset` works
- remote `step` works
- one stable episode runs end-to-end
- the remote behavior matches the local contract

HF Space is the serving surface, not the main heavy-compute workspace.

### Northflank Notebook

Must prove:

- Jupyter Notebook with PyTorch is live on the team H100
- persistent storage is attached
- verifier and baseline work runs there without local-machine dependency
- environment/debug/training work can proceed there even if local runtime is inconvenient
- one smoke check passes:
  - import `constellaration`
  - generate one rotating-ellipse boundary
  - run one low-fidelity verifier call
  - write a result artifact to persistent storage

### Colab Notebook

Primary job:

- connect to the live environment
- run multi-turn episodes
- export traces and baseline comparisons

Secondary job:

- show training or policy improvement if the signal is credible

If training is weak but the environment and eval traces are strong, the notebook still ships.

Colab is a required artifact, but it is not the preferred main compute surface.

Connectivity rule:

- if HF Space is public, the notebook uses direct HTTP calls with no extra auth flow
- if HF Space is private, the notebook must state the required token path and setup explicitly

### Demo Video

The video should show:

1. the `P1` task
2. the environment observation and action space
3. one manual or agent trajectory
4. one reward pathology and fix
5. one baseline comparison

Reward curves are optional supporting visuals, not the center of the story.

### Public Repo

The repo should make the environment easy to understand:

- what `P1` is
- what the agent sees
- what the agent can do
- how reward works
- how to run one episode
- where the demo evidence lives
- why the repo is freshly wired rather than copied from the old project

## 17. Success Gates

### Prerequisite: Northflank Compute Ready

- notebook starts on the team H100
- persistent storage mount is usable
- smoke test artifact is written successfully

### Gate 1: Environment Contract Locked

- task frozen
- observation schema frozen
- action schema frozen
- terminal conditions frozen

### Gate 2: Verifier Wiring Pass

- official `P1` verifier returns expected outputs
- fixture ordering is sensible
- objective direction is correct

### Gate 3: Manual Playtest Pass

- human can act coherently
- at least one trajectory feels sensible
- at least one pathology identified or ruled out

### Gate 4: Stable Local Episode

- local modify -> verify -> observe loop works
- at least one end-to-end episode is stable

### Gate 5: Reward V1

- at least one reward revision completed
- story is documented with before/after behavior

### Gate 6: Baselines

- random baseline complete
- heuristic baseline complete
- heuristic is at least competitive and preferably better than random

### Gate 7: Remote Environment

- HF Space live
- remote client runs one clean episode

### Gate 8: Notebook Evidence

- notebook runs end-to-end
- traces exported
- training evidence included only if it adds signal

## 18. Timeline

### Phase 0

Run two parallel tracks:

- Track A: Northflank compute setup and smoke validation
- Track B: lock the `P1` environment contract

Deliverables:

- frozen task definition
- frozen action and observation schema
- proof that one local `P1` loop works
- Northflank smoke test pass

### Phase 1

Wire the official verifier and run fixture checks.

Deliverables:

- one good fixture
- near-boundary fixtures
- bad fixtures
- confidence that reward/verifier ordering is sane

### Phase 2

Manual-playtest the environment.

Deliverables:

- 5 to 10 episode logs
- notes on leverage, ambiguity, and pathologies

### Phase 3

Implement or refine Reward V0 into Reward V1 based on real behavior.

Deliverables:

- documented exploit
- documented fix
- updated reward logic

### Phase 4

Stabilize one local task and run baselines.

Deliverables:

- stable local trajectory
- random baseline
- heuristic baseline

### Phase 5

Deploy HF Space and validate remote parity.

Deliverables:

- live environment
- one stable remote episode

### Phase 6

Produce notebook evidence.

Deliverables:

- Colab notebook
- Northflank traces or run exports
- traces
- baseline comparison
- training outputs only if persuasive

### Phase 7

Record the demo and make the repo readable.

Deliverables:

- 1-minute video
- public README
- linked artifacts

## 19. Fallback Rules

If something goes wrong, the fallback should preserve the environment story.

### If training signal is weak

Do not force a training-centric pitch.

Ship:

- strong environment
- verifier and fixture evidence
- manual playtest evidence
- reward iteration story
- baseline traces
- one stable remote demo

### If Northflank is delayed or unavailable

Do not block environment design on it.

Fallback:

- continue contract definition, reward design, and basic wiring locally
- use local CPU or Colab for limited verifier/debug work
- keep Northflank as the preferred compute target, but do not stall the whole plan waiting for it

### If reward is unstable

Reduce ambition:

- keep only the terms we can explain
- remove fragile shaping
- prefer legible trajectories over complex reward composition

### If the task is too hard

Do not broaden scope.

Instead:

- simplify the initial states
- tighten the action set
- reduce magnitude choices
- keep the environment more learnable within the fixed budget

### If the task is too easy

Do not add more domains.

Instead:

- adjust budget
- adjust magnitudes
- adjust reward to discourage trivial submission

## 20. Demo Story

The recommended demo structure is:

### Part 1: Problem

"The agent interacts with the official `P1` stellarator-design benchmark and must improve a design under strict geometric constraints."

### Part 2: Environment

"Here is what the agent sees, what it can change, and what counts as success."

### Part 3: Reward Iteration

"Our first reward version produced a bad behavior. We changed the penalty or incentive, and the behavior improved."

### Part 4: Evidence

"Here is one stable trajectory, plus random and heuristic baselines."

### Part 5: Why It Matters

"This is a clear, reproducible scientific workflow environment built around a real verifier, not a shortcut task."

That last line is intentionally conservative. It is strong enough without claiming universal scientific transfer.

## 21. Immediate Next Actions

1. Freeze the `P1` environment contract in code and docs.
2. Implement fresh verifier wiring in this repo.
3. Run fixture checks before heavy training work.
4. Run manual playtests before heavy training work.
5. Mark the current reward as `V0`.
6. Log the first real pathology and reward revision.
7. Do not let notebook or video work outrun the environment evidence.
