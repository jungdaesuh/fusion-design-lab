# Submission Plan — 14 Hours Remaining

Date: 2026-03-07

## Current state

Done:

- environment contract locked and stable
- official constellaration verifier wired (low-fi run, high-fi submit)
- 3 frozen reset seeds validated by measured sweep
- reward V0 tested across 12 of 13 branches (replay playtest report)
- random and heuristic baselines committed
- PPO smoke passed on Northflank H100 (plumbing gate)
- replay playtest script committed with full trace output

Not done:

- [ ] trained policy with demo-quality trajectories
- [ ] HF Space deployment
- [ ] Colab notebook
- [ ] 1-minute demo video
- [ ] README polish
- [ ] paired high-fidelity fixture checks
- [ ] submit-side manual playtest with successful high-fi outcome

## Key finding: cross-fidelity gap

The replay playtest (episode 5) confirmed that the canonical low-fi repair
path from seed 0 crashes at high-fidelity evaluation. The state
`(ar=3.6, elong=1.35, rt=1.6, tri=0.60)` is low-fi feasible but high-fi
VMEC failure.

Decision: **do not attempt to fix this in the remaining time**. Reasons:

1. finding a high-fi-safe path requires sweep work with no time guarantee
2. the plan doc already frames the trained policy as supporting evidence, not the product
3. the gap itself is a strong honest finding for the submission narrative

## Time allocation

| Task | Hours | Notes |
|------|-------|-------|
| Train low-fi PPO | 2-3 | PPO smoke already passed. 24 discrete actions, 6-step budget. Target: visible score improvement across seeds. Run on Northflank H100. |
| HF Space deployment | 2-3 | Hard requirement. Deploy FastAPI server, prove one clean remote episode. Debug dependency issues. |
| Colab notebook | 1-2 | Connect to HF Space, run trained policy, show trajectory. Minimal but working. |
| Demo video | 1 | Script around: environment clarity, human playability, trained agent, reward story. |
| README and repo polish | 1 | Last step. Only after artifacts exist. |
| Buffer | 2-3 | Deployment issues, training bugs, unexpected blockers. |
| **Total** | **~11-14** | |

## Execution order

1. **Training** — start first because it can run while doing other work.
   Use the existing `training/ppo_smoke.py` as the base. Train on all 3 seeds.
   Stop when a few trajectories show clear repair-arc behavior (cross
   feasibility, improve score). Do not overfit to one seed.

2. **HF Space** — deploy while training runs or immediately after. The server
   is already in `server/app.py`. Need to verify dependencies resolve on HF
   infra and that one reset-step-submit cycle completes cleanly.

3. **Colab notebook** — wire to the live HF Space endpoint. Load the trained
   checkpoint. Run a short episode. Add minimal narrative connecting the
   environment design to the trajectory evidence.

4. **Demo video** — 1 minute. Structure:
   - the problem (stellarator design is hard)
   - the environment (narrow, human-playable, real verifier)
   - human playtest (replay output showing legible reward)
   - trained agent (trajectory with visible improvement)
   - honest findings (cross-fidelity gap as a real insight)

5. **README polish** — update with links to HF Space, Colab, and video.
   Keep claims conservative. Reference the evidence docs.

## What to cut if time runs short

Priority order (cut from the bottom):

1. Colab polish — minimal working notebook is enough
2. Training length — a few readable improving trajectories over a long run
3. README depth — link to docs, keep top-level short
4. Do NOT cut HF Space — hard requirement
5. Do NOT cut demo video — primary judge-facing artifact

## Submission narrative

Frame the cross-fidelity gap as a strength, not a failure:

> The environment is instrumented well enough to reveal that low-fidelity
> feasibility does not guarantee high-fidelity success. This is a real
> challenge in multi-fidelity scientific design and exactly the kind of
> insight a well-built environment should surface.

The story is:

1. we built a clear, narrow environment for one constrained design task
2. we tested it thoroughly (sweep, baselines, replay playtest, 12/13 reward branches)
3. we trained a policy that learns the low-fi repair arc
4. we discovered and documented an honest cross-fidelity gap
5. the environment is the product; the policy is evidence that it works

## Risk assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Training does not converge | Low — smoke already passed | Show the smoke trajectories as evidence. Document what was tried. |
| HF Space dependency issues | Medium | Start deployment early. Have a local-only fallback with screen recording. |
| High-fi submit never works | Already confirmed | Frame as documented finding. Do not promise high-fi results. |
| Run out of time | Medium | Follow cut order above. Prioritize video and HF Space over polish. |
