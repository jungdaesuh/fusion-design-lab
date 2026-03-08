# Fusion Design Lab Deliverables Map

This is the output-first map for the hackathon. It is aligned to Plan V2: `P1` is locked, the environment is built fresh in this repo, the old harness is not ported, and training claims stay conservative. Everything branches from the four final artifacts the judges and submission flow will actually see.

Northflank is the recommended compute workspace behind those artifacts. HF Space and Colab remain the actual submission surfaces.

Use this map to sequence execution, not to reopen already-locked task choices.

## Current Branch Status

- [x] `P1` contract is frozen in code
- [x] official `constellaration` verifier loop is wired
- [x] baseline comparison has been rerun on the real verifier path
- [x] Northflank smoke workflow and note are committed
- [ ] tracked fixtures are checked in
- [ ] manual playtest evidence exists
- [ ] heuristic baseline has been refreshed for the real verifier path
- [ ] HF Space deployment is live

## Deliverables Tree

```mermaid
flowchart TD
    A["Fusion Design Lab Submission"] --> B["HF Space Environment"]
    A --> C["Colab Eval / Training Notebook"]
    A --> D["1-Minute Demo"]
    A --> E["Public Repo + README"]
    A --> N["Northflank H100 Workspace"]

    B --> B0["P1 environment contract frozen"]
    B --> B1["Remote reset/step works"]
    B --> B2["Reward V0 -> V1 documented"]
    B --> B3["One stable task runs end-to-end"]
    B --> B4["Clear rules + reproducible episodes"]

    C --> C1["Connects to HF Space"]
    C --> C2["Runs multi-turn episodes"]
    C --> C3["Logs behavior + reward traces"]

    D --> D1["Clear problem statement"]
    D --> D2["Manual playtest + agent trajectory"]
    D --> D3["Reward shaping story"]

    E --> E1["Readable project summary"]
    E --> E2["Setup + run instructions"]
    E --> E3["Submission links and artifacts"]

    N --> N1["Jupyter Notebook with PyTorch live"]
    N --> N2["Persistent storage attached"]
    N --> N3["Verifier + baseline runs happen here"]
    N --> N4["Northflank smoke test passes"]

    B0 --> F["Observation + action schema frozen"]
    B3 --> G["Fresh P1 verifier loop proven"]
    B2 --> H["Exploit observed -> penalty added"]
    B4 --> I0["Deterministic action schema"]
    D2 --> I["Human can act coherently in env"]
    C3 --> J["Random baseline"]
    C3 --> K["Heuristic baseline"]
    G --> L["Official constellaration P1 verifier wired correctly"]
    L --> M["Good / boundary / bad fixture checks pass"]
    N4 --> N3
    N3 --> G
```

## Reverse Timeline

```mermaid
flowchart LR
    S["Submit by Sun 1:00 PM"] --> V["Video finalized"]
    S --> R["Repo public and readable"]
    S --> T["Training / eval evidence exported"]
    S --> H["HF Space live"]
    S --> N1["Northflank compute ready"]

    V --> V1["Recorded clean demo trajectory"]
    V --> V2["Scripted 60-second story"]

    T --> T1["Behavior trace image"]
    T --> T2["Baseline comparison numbers"]
    T --> T3["Colab notebook runs end-to-end"]

    H --> H1["OpenEnv P1 environment packaged"]
    H --> H2["Remote client can reset and step"]
    H --> H3["Verifier and reward stable"]
    H --> H4["Rules are clear and reproducible"]

    H4 --> P["Environment contract locked first"]
    N1 --> N2["Jupyter with PyTorch up first"]
    N2 --> N3["Persistent storage attached"]
    N3 --> N4["Import + low-fi verifier smoke passes"]
    N4 --> M0
    P --> Q["Manual playtest completed first"]
    H3 --> M0["Local verifier loop proven first"]
    T2 --> B["Random + heuristic baselines done"]
    T3 --> X["Training included only if persuasive"]
    V1 --> Y["One stable task only"]
    V2 --> Z["Explain reward fix, not just reward gain"]
    M0 --> N["Fresh wiring, not legacy harness port"]
```

## Priority Order

1. Add tracked fixtures and run fixture sanity checks.
2. Manual-playtest the environment and record the first real pathology, if any.
3. Refresh the heuristic baseline from that evidence.
4. Bring up the Northflank H100 workspace with persistent storage.
5. Pass the Northflank smoke test.
6. Make one stable OpenEnv `P1` task work remotely with clear, reproducible rules.
7. Use the notebook to show traces and comparisons; include training only if it adds signal.
8. Record the demo around environment clarity, verifier fidelity, reward shaping, and one stable trajectory.
9. Polish the repo only after the artifacts are real.
