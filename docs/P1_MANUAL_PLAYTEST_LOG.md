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

- Reward V0 is legible on the low-fidelity repair path around the default reset seed
- the most useful next manual check is still a real `submit` trace, but low-fidelity shaping is already understandable by a human
