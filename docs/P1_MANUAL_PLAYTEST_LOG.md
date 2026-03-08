# P1 Manual Playtest Log

Scope:

- initial low-fidelity manual sanity check from the current default reset seed
- focus: can a human read the observation, choose a plausible move, and see a legible reward change?

Episode A: repair toward feasibility

Start state:

- seed: `0`
- params: `aspect_ratio=3.6`, `elongation=1.4`, `rotational_transform=1.5`, `triangularity_scale=0.55`
- low-fidelity feasibility: `0.050653`
- low-fidelity score: `0.0`
- constraints satisfied: `false`

Step 1:

- action: increase `rotational_transform` by `medium`
- expectation: improve iota without changing triangularity much
- result: feasibility stayed effectively flat at `0.050653`
- reward: `-0.1`
- interpretation: legible but weak; this move alone does not solve the boundary issue

Step 2:

- action: increase `triangularity_scale` by `medium`
- expectation: push the boundary over the triangularity threshold
- result: low-fidelity feasibility moved to `0.0`
- result: low-fidelity score moved to `0.291660`
- constraints satisfied: `true`
- reward: `+3.1533`
- interpretation: good reward behavior; the feasibility crossing was clearly positive and easy to understand

Episode B: move the wrong way

Start state:

- same default reset seed

Step 1:

- action: decrease `triangularity_scale` by `medium`
- expectation: worsen triangularity and move away from feasibility
- result: feasibility worsened to `0.107113`
- reward: `-0.3823`
- interpretation: good negative signal; the environment penalized an obviously bad move without needing a complicated reward term

Current conclusion:

- At the time of this initial playtest, Reward V0 was legible on the low-fidelity repair path around the default reset seed
- a real `submit` trace is now recorded; next manual validation is to extend beyond the initial 5-10 episode path and look for one clear exploit or ambiguity

Episode C: submit-side manual trace

Scope:

- same seed-0 start state as episode A
- actions: `rotational_transform increase medium`, `triangularity_scale increase medium`, `elongation decrease small`, `submit`

Step sequence:

- Step 1: `rotational_transform increase medium`
  - low-fidelity feasibility changed by `0.000000` (still infeasible)
  - reward: `-0.1000`
- Step 2: `triangularity_scale increase medium`
  - crossed feasibility boundary
  - low-fidelity feasibility moved from `0.050653` to `0.000000`
  - reward: `+3.1533`
- Step 3: `elongation decrease small`
  - low-fidelity feasibility moved to `0.000865`
  - reward: `+0.2665`
- Step 4: `submit` (high-fidelity)
  - final feasibility: `0.000865`
  - final high-fidelity score: `0.296059`
  - final reward: `+2.0098`
  - final diagnostics `evaluation_fidelity`=`high`, `constraints`=`SATISFIED`, `best_high_fidelity_score`=`0.296059`

Artifact:

- [manual submit trace JSON](../baselines/submit_side_trace.json)
  Note:
  this is a historical submit-side artifact from the earlier Reward V0 / pre-telemetry contract surface. Keep it as supporting evidence for the old submit path, not as the current Reward V1 observation-format example.
