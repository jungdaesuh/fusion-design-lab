# Fusion Design Lab TODO

This is the execution tracker for the hackathon repo.

Use this file for day-of build progress. Use the linked docs for rationale, sequencing, and submission framing:

- [Plan V2](docs/FUSION_DESIGN_LAB_PLAN_V2.md)
- [Deliverables Map](docs/FUSION_DELIVERABLES_MAP.md)
- [Next 12 Hours Checklist](docs/FUSION_NEXT_12_HOURS_CHECKLIST.md)
- [P1 Environment Contract](docs/P1_ENV_CONTRACT_V1.md)
- [P1 Pivot Record](docs/PIVOT_P1_ROTATING_ELLIPSE.md)
- [Repo Guardrails](AGENTS.md)

Priority source:

- [Plan V2](docs/FUSION_DESIGN_LAB_PLAN_V2.md) is the planning SSOT
- [Next 12 Hours Checklist](docs/FUSION_NEXT_12_HOURS_CHECKLIST.md) is the execution order SSOT
- this file should track execution progress only

## Current State

- [x] `P1` strategy is locked
- [x] shared models reflect the rotating-ellipse `P1` contract
- [x] environment loop reflects the rotating-ellipse `P1` contract
- [x] API/task surface reflects `P1`
- [x] baselines reflect the `P1` contract
- [x] repo docs call out the low-fi/high-fi `constellaration` split honestly
- [x] post-terminal guard in `step()`
- [x] `constellaration` verifier wiring
- [x] verify the current 3-knob family against the real low-fidelity verifier
- [ ] repair the low-dimensional parameterization so triangularity is controllable
- [ ] split boundary building from boundary evaluation
- [ ] update the action schema from 3 knobs to the repaired low-dimensional family
- [ ] add explicit VMEC failure semantics
- [ ] label low-fi vs high-fi truth in the observation/task surface
- [ ] tracked `P1` fixtures
- [ ] manual playtest log
- [x] settle the non-submit terminal reward policy
- [x] baseline comparison has been re-run on the `constellaration` branch state
- [ ] refresh the heuristic baseline for the real verifier path

## Execution Graph

```mermaid
flowchart TD
    A["Northflank Smoke Test"] --> E["Fixture Checks"]
    B["P1 Contract Lock"] --> D["P1 Models + Environment"]
    C["constellaration Physics Wiring"] --> D
    D --> P["Parameterization Repair"]
    P --> E["Fixture Checks"]
    E --> F["Manual Playtest"]
    F --> G["Reward V1"]
    G --> H["Baselines"]
    H --> I["HF Space Deploy"]
    I --> J["Colab Notebook"]
    J --> K["Demo + README"]
```

## Hour 0-2

- [x] Lock the exact `P1` environment contract
  Goal:
  freeze observation schema, action schema, episode loop, terminal conditions, and `Reward V0`
  Related:
  [Plan V2](docs/FUSION_DESIGN_LAB_PLAN_V2.md),
  [Next 12 Hours Checklist](docs/FUSION_NEXT_12_HOURS_CHECKLIST.md)

- [x] Pass the Northflank smoke test
  Related:
  [Plan V2](docs/FUSION_DESIGN_LAB_PLAN_V2.md),
  [Next 12 Hours Checklist](docs/FUSION_NEXT_12_HOURS_CHECKLIST.md),
  [training/notebooks/README.md](training/notebooks/README.md)

- [x] Verify that the current 3-knob family can or cannot approach P1 feasibility
  Goal:
  decide whether parameterization repair is a blocker before more reward work
  Related:
  [P1 Environment Contract](docs/P1_ENV_CONTRACT_V1.md),
  [P1 Pivot Record](docs/PIVOT_P1_ROTATING_ELLIPSE.md)

## Fresh Wiring

- [x] Rewrite the shared models to the locked `P1` contract
  Files:
  [fusion_lab/models.py](fusion_lab/models.py),
  [Plan V2](docs/FUSION_DESIGN_LAB_PLAN_V2.md)

- [x] Rewrite the environment loop to the locked `P1` contract
  Files:
  [server/environment.py](server/environment.py),
  [Plan V2](docs/FUSION_DESIGN_LAB_PLAN_V2.md),
  [P1 Pivot Record](docs/PIVOT_P1_ROTATING_ELLIPSE.md)

- [x] Add a post-terminal guard to the environment loop
  Files:
  [server/environment.py](server/environment.py)
  Goal:
  reject or no-op any `step()` call after terminal state so budget and step count do not drift past episode end

- [x] Replace the synthetic physics path with `constellaration` wiring
  Files:
  [server/physics.py](server/physics.py),
  [server/Dockerfile](server/Dockerfile),
  [pyproject.toml](pyproject.toml)

- [x] Update the API/task surface to match `P1`
  Files:
  [server/app.py](server/app.py),
  [README.md](README.md)

- [ ] Repair the low-dimensional boundary family
  Goal:
  add an explicit triangularity control knob or equivalent low-dimensional control so the environment can actually approach P1 feasibility
  Files:
  [server/physics.py](server/physics.py),
  [fusion_lab/models.py](fusion_lab/models.py),
  [server/environment.py](server/environment.py),
  [server/app.py](server/app.py)
  Related:
  [P1 Environment Contract](docs/P1_ENV_CONTRACT_V1.md)

- [ ] Split boundary construction from boundary evaluation
  Goal:
  make the verifier boundary-based and keep parameterization-specific logic in the environment adapter layer
  Files:
  [server/physics.py](server/physics.py)
  Related:
  [P1 Environment Contract](docs/P1_ENV_CONTRACT_V1.md)

- [ ] Add explicit VMEC failure semantics
  Goal:
  failed evaluations must cost budget, return a visible failure observation, and apply a documented penalty without silent fallback
  Files:
  [server/physics.py](server/physics.py),
  [server/environment.py](server/environment.py)
  Related:
  [P1 Environment Contract](docs/P1_ENV_CONTRACT_V1.md)

- [ ] Label low-fi vs high-fi truth in the observation/task surface
  Goal:
  make it obvious whether a metric came from a low-fidelity `run` step or a high-fidelity `submit`
  Files:
  [fusion_lab/models.py](fusion_lab/models.py),
  [server/environment.py](server/environment.py),
  [server/app.py](server/app.py)
  Related:
  [P1 Environment Contract](docs/P1_ENV_CONTRACT_V1.md)

## Validation and Reward

- [ ] Run a small measured sweep on the repaired low-dimensional family
  Goal:
  choose useful parameter ranges, step deltas, and reset seeds from the repaired action family instead of guessing them from prose
  Related:
  [P1 Environment Contract](docs/P1_ENV_CONTRACT_V1.md)

- [ ] Add 1-2 tracked `P1` fixtures
  Files:
  [server/data/p1/README.md](server/data/p1/README.md),
  [P1 Pivot Record](docs/PIVOT_P1_ROTATING_ELLIPSE.md)
  Note:
  add fixtures only after the parameterization repair produces a meaningful near-boundary region

- [ ] Run fixture sanity checks
  Goal:
  confirm verifier outputs, objective direction, and reward ordering
  Related:
  [Plan V2](docs/FUSION_DESIGN_LAB_PLAN_V2.md),
  [Next 12 Hours Checklist](docs/FUSION_NEXT_12_HOURS_CHECKLIST.md)

- [ ] Manual-playtest 5-10 episodes
  Goal:
  verify a human can act coherently and surface at least one pathology or ambiguity
  Related:
  [Plan V2](docs/FUSION_DESIGN_LAB_PLAN_V2.md),
  [Deliverables Map](docs/FUSION_DELIVERABLES_MAP.md)

- [ ] Update reward from `V0` to `V1` if playtesting reveals a real pathology
  Goal:
  keep a short exploit -> fix -> behavior improvement story
  Related:
  [AGENTS.md](AGENTS.md),
  [Plan V2](docs/FUSION_DESIGN_LAB_PLAN_V2.md)

- [ ] Write down whether `Reward V0` survives unchanged
  Goal:
  if playtesting does not reveal a real pathology, record that outcome explicitly instead of forcing a `V1`
  Related:
  [README.md](README.md),
  [Plan V2](docs/FUSION_DESIGN_LAB_PLAN_V2.md)

- [x] Decide the non-submit terminal reward policy
  Goal:
  budget exhaustion now yields a smaller end-of-episode reward than `submit`, so non-submitting agents still get terminal feedback without outranking explicit submit behavior
  Files:
  [server/environment.py](server/environment.py),
  [README.md](README.md)

## Baselines

- [x] Implement the random baseline
  Files:
  [baselines/random_agent.py](baselines/random_agent.py),
  [baselines/compare.py](baselines/compare.py)

- [x] Implement the heuristic baseline
  Files:
  [baselines/heuristic_agent.py](baselines/heuristic_agent.py),
  [baselines/compare.py](baselines/compare.py)

- [x] Run the baseline comparison on the current `constellaration` branch state
  Files:
  [baselines/compare.py](baselines/compare.py)

- [ ] Refresh the heuristic baseline after the `constellaration` rerun
  Goal:
  the old synthetic-path heuristic no longer gives a useful anchor on the real verifier path; redesign it after manual playtesting

- [ ] Save one comparison trace that is presentation-ready
  Goal:
  show at least one stable trajectory and one heuristic-vs-random comparison

## Submission Surfaces

- [ ] Deploy the environment to HF Space
  Related:
  [Deliverables Map](docs/FUSION_DELIVERABLES_MAP.md),
  [README.md](README.md)

- [ ] Create the thin public Colab notebook
  Files:
  [training/notebooks/README.md](training/notebooks/README.md)

- [ ] Record the 1-minute demo
  Goal:
  explain `P1`, show one trajectory, show reward iteration, show baseline evidence

- [ ] Finalize the public README
  Files:
  [README.md](README.md)

- [ ] Only add training evidence if it is actually persuasive
  Related:
  [Plan V2](docs/FUSION_DESIGN_LAB_PLAN_V2.md),
  [Next 12 Hours Checklist](docs/FUSION_NEXT_12_HOURS_CHECKLIST.md)

## Guardrails

- [ ] Do not reopen `P1 + rotating-ellipse` strategy without a real blocker
- [ ] Do not pretend the current 3-knob family is sufficient for P1 after the verified triangularity blocker
- [ ] Do not guess repaired-family ranges, deltas, or budget changes without measurement
- [ ] Do not port the old `ai-sci-feasible-designs` harness
- [ ] Do not let notebook or demo work outrun environment evidence
- [ ] Do not add training-first complexity before manual playtesting
- [ ] Do not describe low-fidelity `run` metrics as equivalent to high-fidelity `submit` results
- [ ] Do not describe the current baseline reset state as feasible or near-feasible
- [ ] Do not force a `Reward V1` story if `Reward V0` survives manual playtesting
