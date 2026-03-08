# Fusion Design Lab: Next 12 Hours Checklist

This checklist turns the updated deliverables map and Plan V2 into concrete execution order. The goal is to produce real evidence for the four submission artifacts, with `P1`, fresh wiring, and environment clarity driving the sequence.

## Core Rule

Do not expand scope beyond one stable task. Training is supporting evidence, not the main story.

## Current Branch Status

- [x] `P1` task is locked
- [x] rotating-ellipse `P1` contract is implemented in the working tree
- [x] baselines and API surface have been moved to the `P1` contract
- [x] add a post-terminal guard in `step()`
- [x] replace the synthetic evaluator with `constellaration`
- [x] re-run baselines on the real verifier path
- [x] commit the Northflank smoke workflow and note
- [ ] add tracked fixtures and manual playtest evidence
- [ ] refresh the heuristic baseline after the real-verifier rerun

Current caution:

- do not assume the default baseline params are a near-feasible playtest start; on the current real verifier path they are still deeply infeasible, so fixture discovery comes first

## Plan V2 Inheritance

Carry these rules through the whole checklist:

- Freeze the environment contract before heavy iteration.
- Keep the repo freshly wired; do not port the old harness.
- Treat the current reward as `Reward V0`, not final reward.
- Distinguish validated facts from working hypotheses.
- Prefer behavior traces and baseline comparisons over generic reward-curve storytelling.
- If training is weak, ship the environment story anyway.
- Use Northflank as the main compute workspace; keep HF Space and Colab as the submission surfaces.
- Do not open another strategy loop unless a real blocker appears.

## Hour 0-2: Parallelize Compute Bring-Up and Contract Lock

### Track A: Northflank Compute

1. Bring up the Northflank Jupyter Notebook with PyTorch on the team H100.
2. Attach persistent storage before relying on saved models, caches, or fixture downloads.
3. Pass a concrete smoke test:
   - import `constellaration`
   - generate one rotating-ellipse boundary
   - run one low-fidelity verifier call
   - write one artifact to persistent storage

Exit condition: the notebook is not just open; the verifier path works and persistent storage is usable.

Artifacts:
- Northflank notebook live
- smoke test note
- one persisted smoke artifact

### Track B: Environment Contract

1. Write the exact `P1` environment spec.
2. Freeze one task only.
3. Define:
   - observation schema
   - action schema
   - episode loop
   - terminal conditions
   - reward V0 terms
   - initial penalties
4. Update the main diagram so it emphasizes:
   - `P1`
   - official verifier
   - reward shaping
   - manual playtesting
5. Mark open assumptions explicitly:
   - whether the rotating-ellipse action set is expressive enough
   - whether the fixed step budget is enough
   - whether `restore_best` is useful without becoming an exploit

Exit condition: a human can read the spec and understand how to act in the environment.

Artifacts:
- short environment spec
- revised mermaid diagram
- short hypothesis list

Transition rule:

- once Track B exits, stop rewriting the strategy and move straight into wiring and verifier checks

## Hour 2-4: Verify Wiring, Then Manual Playtest

1. Run fixture checks:
   - known-good or near-winning design
   - near-boundary designs
   - clearly bad designs
   - do not rely on the default baseline params as the only starting point
2. Confirm:
   - verifier outputs are sane
   - reward ordering is sane
   - objective direction is correct
3. Manually play 5 to 10 episodes.
4. Log for each step:
   - observation
   - chosen action
   - expected effect
   - returned reward
   - confusion or exploit if observed
5. Identify at least one bad incentive or exploit.
6. Patch reward or penalty logic immediately.
7. Write the reward shaping story:
   - initial reward V0
   - bad behavior
   - refinement to reward V1
   - improved behavior
8. If no real pathology appears, record that `Reward V0` survived playtesting and move on.

Exit condition: you can explain why the environment now rewards the intended behavior.

Artifacts:
- fixture check note
- manual playtest log
- reward shaping note
- reward V1 delta note

## Hour 4-6: Stabilize the Local Task

1. Prove the fresh local `P1` verifier loop.
2. Run one stable end-to-end task repeatedly.
3. Confirm the action schema is deterministic enough for reproducible episodes.
4. Save one clean local trajectory.
5. Do not proceed to remote deployment until this gate is real.

Exit condition: the same setup yields the same type of behavior reliably enough for a demo.

Artifacts:
- stable local run
- saved trajectory

## Hour 6-8: Make the HF Space Real

1. Package the OpenEnv `P1` environment for remote use.
2. Use the explicit deployment path:
   - commit changes in this repo
   - push to GitHub
   - let HF Space build from the repo
3. Decide and document the access mode:
   - preferred: public HF Space for the hackathon
   - if private: token-based notebook access documented
4. Verify remote `reset` and `step`.
5. Run one clean remote episode end-to-end.
6. Confirm the remote environment preserves the same task contract as local.

Exit condition: the environment is runnable in the actual submission surface, not only locally.

Artifacts:
- live HF Space environment
- remote episode proof

## Hour 8-10: Add Baselines

1. Implement the random baseline.
2. Implement the heuristic baseline.
3. Run short comparisons on the same stable `P1` task.
4. Save:
   - comparison numbers
   - behavior traces
   - one example where heuristic beats random

Exit condition: there is a credible baseline anchor for the judges.

Artifacts:
- random baseline
- heuristic baseline
- comparison table or figure

## Hour 10-12: Produce the Submission Evidence

1. Wire the Colab training or eval script to the live environment.
2. Ensure it produces:
   - multi-turn episodes
   - behavior traces
   - reward or behavior comparison outputs
3. Keep heavy verifier and training work on Northflank; use Colab as the thin public artifact.
4. Draft the 60-second demo script.
5. Record the demo around:
   - what `P1` is
   - how reward was refined
   - what manual playtesting revealed
   - one stable trajectory
   - baseline comparison
6. If training evidence is weak, keep the notebook eval-first and do not force a training-centric claim.
7. Make the repo public-facing and readable only after the artifacts are real.

Exit condition: all four visible artifacts exist in usable form.

Artifacts:
- Colab training or eval script
- Northflank run notes or exported traces
- demo script
- draft or final video
- updated repo README
- explicit fallback note if training is not persuasive

## Artifact Order

1. Environment spec
2. Fixture check note
3. Manual playtest log
4. Reward revision note
5. Stable task run
6. Random baseline
7. Heuristic baseline
8. Northflank traces or training evidence
9. Colab training or eval evidence
10. Demo recording
11. Repo polish

## Non-Negotiables

- Do not widen scope beyond one stable task.
- Do not port the old `ai-sci-feasible-designs` harness into this repo.
- Do not optimize training before manual playtesting.
- Do not rely on reward curves alone; keep trajectory evidence.
- Do not narrate hypotheses as facts before they are checked.
- Do not polish the repo or video before the environment and baselines are real.
- Treat judge comments as pressure toward clarity and reproducibility, not broader unsupported claims.
- Do not force a training-centric story if the strongest evidence is environment quality plus baselines.
- Do not rely on Northflank container-local state without persistent storage.
- Do not block contract design work on Northflank provisioning friction.
