# Submission Plan — 14 Hours Remaining

Date: 2026-03-07

Status: late-stage submission checklist, not a planning SSOT. The planning
SSOT is `FUSION_DESIGN_LAB_PLAN_V2.md`. This file captures time allocation
and cut priorities for the final push.

## Current state (aligned to SSOT)

Done:

- environment contract locked and stable
- official constellaration verifier wired (low-fi run, high-fi submit)
- 3 frozen reset seeds validated by measured sweep
- reward V0 replay playtest committed (see `P1_REPLAY_PLAYTEST_REPORT.md` for branch-level detail)
- random and heuristic baselines committed
- paired high-fidelity fixture checks complete (all 3 fixtures)
- one successful submit-side manual trace recorded (Episode C in playtest log)
- PPO smoke completed as a plumbing/debugging gate (exposed repeated-action collapse, not training success)
- replay playtest script committed with full trace output

Not done (per SSOT execution order):

- [ ] reset-seed pool decision from paired checks
- [ ] heuristic baseline refresh on repaired-family evidence
- [ ] trained policy with non-degenerate trajectories (current smoke collapses to a single repeated action)
- [ ] if non-degenerate: push toward demo-quality trajectories showing feasibility crossing
- [ ] HF Space deployment
- [ ] Colab notebook
- [ ] 1-minute demo video
- [ ] README polish

## Cross-fidelity status

The cross-fidelity picture is nuanced, not a blanket failure:

- `lowfi_feasible_local.json` shows a successful paired high-fi evaluation at
  `(ar=3.6, elong=1.4, rt=1.6, tri=0.60)` — constraints satisfied, score=0.292
- Episode C manual trace shows a successful high-fi submit from seed 0 with
  score=0.296, constraints satisfied
- the replay playtest episode 5 crashed at high-fi from
  `(ar=3.6, elong=1.35, rt=1.6, tri=0.60)` — one elongation decrease away

So: high-fi works for some feasible states but not all. The gap is
**path-dependent**, not universal. States closer to the original params
(elong=1.4) survive high-fi; states with decreased elongation (elong=1.35)
may not. This is a real multi-fidelity challenge, not a total blocker.

Decision: do not spend time trying to map the full high-fi-safe region.
Use the known-good submit path for the demo. Document the path-dependent
gap honestly.

## Time allocation

| Task | Hours | Notes |
|------|-------|-------|
| Heuristic refresh + reset-seed decision | 1 | Per SSOT, this is the next execution step. Quick because the sweep and fixture evidence already exist. |
| Train low-fi PPO | 2-3 | Smoke passed as plumbing only. 25 discrete actions (24 run + restore_best), 6-step budget. The repeated-action collapse needs more timesteps or reward tuning. Convergence risk is real — the smoke exposed a failure mode, not success. |
| HF Space deployment | 2-3 | Hard requirement. Deploy FastAPI server, prove one clean remote episode. |
| Colab notebook | 1-2 | Connect to HF Space, run trained policy, show trajectory. Minimal but working. |
| Demo video | 1 | Script around: environment clarity, human playability, trained agent, reward story. |
| README and repo polish | 1 | Last step. Only after artifacts exist. |
| Buffer | 2-3 | Deployment issues, training tuning, unexpected blockers. |
| **Total** | **~11-14** | |

## Execution order (aligned to SSOT)

1. **Heuristic refresh + reset-seed decision** — per SSOT, this comes before
   broader training. The measured sweep and paired fixture evidence already
   exist. Decide whether any seed should move, refresh the heuristic to use
   the repair path from the playtest log, and save one comparison trace.

2. **Training** — start after the heuristic is refreshed so training runs
   against a confirmed environment configuration. Use `training/ppo_smoke.py`
   as the base but increase timesteps significantly. The smoke ran 64
   timesteps and collapsed to a single repeated action — this is the expected
   outcome of a plumbing gate, not evidence that training will converge
   easily. First milestone: non-degenerate trajectories (varied actions,
   not single-action collapse). Second milestone: feasibility crossing in
   at least one evaluation episode. Do not assume demo-quality trajectories
   are reachable without tuning. Can run on Northflank H100 in the background.
   **Do not block HF Space, notebook, or video on training success.**

3. **HF Space** — deploy while training runs. The server is in `server/app.py`.
   Verify dependencies, prove one clean remote episode.

4. **Colab notebook** — wire to the live HF Space endpoint. Load trained
   checkpoint if available; otherwise show the heuristic or manual
   trajectory as evidence.

5. **Demo video** — 1 minute. Structure:
   - the problem (stellarator design is hard)
   - the environment (narrow, human-playable, real verifier)
   - the evidence (successful submit trace, replay playtest coverage)
   - trained agent if available (trajectory with visible improvement)
   - honest findings (path-dependent cross-fidelity gap)

6. **README polish** — update with links to HF Space, Colab, and video.
   Keep claims conservative. Reference the evidence docs.

## What to cut if time runs short

Priority order (cut from the bottom):

1. Colab polish — minimal working notebook is enough
2. Training length — a few readable trajectories over a long run
3. README depth — link to docs, keep top-level short
4. Reset-seed decision — keep current seeds if evidence is ambiguous
5. Do NOT cut HF Space — hard requirement
6. Do NOT cut demo video — primary judge-facing artifact

If training remains weak or degenerate:

- still ship the trained-policy demonstration, even if it only shows collapse or weak behavior
- supplement with the heuristic baseline or manual playtest Episode C as the primary evidence of environment usability
- document the training limitations plainly in the video and README
- per SSOT fallback rules (`FUSION_DESIGN_LAB_PLAN_V2.md` section 10): "keep claims conservative about policy quality" and "still ship a trained-policy demonstration and document its limitations plainly"
- do NOT wait for strong PPO before shipping HF Space, notebook, and video

## Submission narrative

The story is:

1. we built a clear, narrow environment for one constrained design task
2. we tested it thoroughly (sweep, baselines, replay playtest with broad reward branch coverage)
3. the environment has a known-good submit path (Episode C: successful high-fi, score=0.296)
4. we discovered a path-dependent cross-fidelity gap (some low-fi feasible states crash at high-fi)
5. the environment is the product; the policy is evidence that it works

## Risk assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Training does not converge | Medium — smoke exposed collapse, not success | Show the heuristic trajectory or manual playtest as fallback evidence. Document what was tried. Keep claims conservative per SSOT fallback rules. |
| HF Space dependency issues | Medium | Start deployment early. Have a local-only fallback with screen recording. |
| Run out of time | Medium | Follow cut order above. Prioritize video and HF Space over polish. |
