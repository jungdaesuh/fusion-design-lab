# Fusion Design Lab: Next 12 Hours Checklist

This checklist turns the updated deliverables map and Plan V2 into concrete execution order. The goal is to produce real evidence for the four submission artifacts, with environment clarity and reproducibility driving the sequence.

## Core Rule

Do not expand scope beyond one stable task. Training is supporting evidence, not the main story.

## Plan V2 Inheritance

Carry these rules through the whole checklist:

- Freeze the environment contract before heavy iteration.
- Treat the current reward as `Reward V0`, not final reward.
- Distinguish validated facts from working hypotheses.
- Prefer behavior traces and baseline comparisons over generic reward-curve storytelling.
- If training is weak, ship the environment story anyway.

## Hour 0-2: Lock the Environment Contract

1. Write the exact environment spec.
2. Freeze one task only.
3. Define:
   - observation schema
   - action schema
   - episode loop
   - terminal conditions
   - reward V0 terms
   - initial penalties
4. Update the main diagram so it emphasizes:
   - environment
   - verifier
   - reward shaping
   - manual playtesting
5. Mark open assumptions explicitly:
   - risky action magnitudes
   - whether 6 runs is enough
   - whether `restore_best` is useful without becoming an exploit

Exit condition: a human can read the spec and understand how to act in the environment.

Artifacts:
- short environment spec
- revised mermaid diagram
- short hypothesis list

## Hour 2-4: Manual Playtest and Fix Reward Pathologies

1. Manually play 5 to 10 episodes.
2. Log for each step:
   - observation
   - chosen action
   - expected effect
   - returned reward
   - confusion or exploit if observed
3. Identify at least one bad incentive or exploit.
4. Patch reward or penalty logic immediately.
5. Write the reward shaping story:
   - initial reward V0
   - bad behavior
   - refinement to reward V1
   - improved behavior

Exit condition: you can explain why the environment now rewards the intended behavior.

Artifacts:
- manual playtest log
- reward shaping note
- reward V1 delta note

## Hour 4-6: Stabilize the Local Task

1. Prove the local physics or verifier loop.
2. Run one stable end-to-end task repeatedly.
3. Confirm the action schema is deterministic enough for reproducible episodes.
4. Save one clean local trajectory.
5. Do not proceed to remote deployment until this gate is real.

Exit condition: the same setup yields the same type of behavior reliably enough for a demo.

Artifacts:
- stable local run
- saved trajectory

## Hour 6-8: Make the HF Space Real

1. Package the OpenEnv environment for remote use.
2. Verify remote `reset` and `step`.
3. Run one clean remote episode end-to-end.
4. Confirm the remote environment preserves the same task contract as local.

Exit condition: the environment is runnable in the actual submission surface, not only locally.

Artifacts:
- live HF Space environment
- remote episode proof

## Hour 8-10: Add Baselines

1. Implement the random baseline.
2. Implement the heuristic baseline.
3. Run short comparisons on the same stable task.
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
3. Draft the 60-second demo script.
4. Record the demo around:
   - what the environment is
   - how reward was refined
   - what manual playtesting revealed
   - one stable trajectory
   - baseline comparison
5. If training evidence is weak, keep the notebook eval-first and do not force a training-centric claim.
6. Make the repo public-facing and readable only after the artifacts are real.

Exit condition: all four visible artifacts exist in usable form.

Artifacts:
- Colab training or eval script
- demo script
- draft or final video
- updated repo README
- explicit fallback note if training is not persuasive

## Artifact Order

1. Environment spec
2. Manual playtest log
3. Reward revision note
4. Stable task run
5. Random baseline
6. Heuristic baseline
7. Colab training or eval evidence
8. Demo recording
9. Repo polish

## Non-Negotiables

- Do not widen scope beyond one stable task.
- Do not optimize training before manual playtesting.
- Do not rely on reward curves alone; keep trajectory evidence.
- Do not narrate hypotheses as facts before they are checked.
- Do not polish the repo or video before the environment and baselines are real.
- Treat judge comments as pressure toward clarity and reproducibility, not broader unsupported claims.
- Do not force a training-centric story if the strongest evidence is environment quality plus baselines.
