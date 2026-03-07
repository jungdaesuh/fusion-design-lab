# Fusion Design Lab Deliverables Map

This is the output-first map for the hackathon. It is aligned to Plan V2: environment-first, reward-iteration-driven, and conservative about training claims. Everything branches from the four final artifacts the judges and submission flow will actually see.

## Deliverables Tree

```mermaid
flowchart TD
    A["Fusion Design Lab Submission"] --> B["HF Space Environment"]
    A --> C["Colab Eval / Training Notebook"]
    A --> D["1-Minute Demo"]
    A --> E["Public Repo + README"]

    B --> B0["Environment contract frozen"]
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

    B0 --> F["Observation + action schema frozen"]
    B3 --> G["Standalone physics loop proven"]
    B2 --> H["Exploit observed -> penalty added"]
    B4 --> I0["Deterministic action schema"]
    D2 --> I["Human can act coherently in env"]
    C3 --> J["Random baseline"]
    C3 --> K["Heuristic baseline"]
```

## Reverse Timeline

```mermaid
flowchart LR
    S["Submit by Sun 1:00 PM"] --> V["Video finalized"]
    S --> R["Repo public and readable"]
    S --> T["Training / eval evidence exported"]
    S --> H["HF Space live"]

    V --> V1["Recorded clean demo trajectory"]
    V --> V2["Scripted 60-second story"]

    T --> T1["Behavior trace image"]
    T --> T2["Baseline comparison numbers"]
    T --> T3["Colab notebook runs end-to-end"]

    H --> H1["OpenEnv environment packaged"]
    H --> H2["Remote client can reset and step"]
    H --> H3["Verifier and reward stable"]
    H --> H4["Rules are clear and reproducible"]

    H4 --> P["Environment contract locked first"]
    P --> Q["Manual playtest completed first"]
    H3 --> M["Local physics loop proven first"]
    T2 --> B["Random + heuristic baselines done"]
    T3 --> X["Training included only if persuasive"]
    V1 --> Y["One stable task only"]
    V2 --> Z["Explain reward fix, not just reward gain"]
```

## Priority Order

1. Prove the local physics loop.
2. Freeze the environment contract and mark the initial reward as `V0`.
3. Manual-playtest the environment and fix obvious reward/pathology issues.
4. Make one stable OpenEnv task work remotely with clear, reproducible rules.
5. Get random and heuristic baselines.
6. Use the notebook to show traces and comparisons; include training only if it adds signal.
7. Record the demo around environment clarity, reward shaping, and one stable trajectory.
8. Polish the repo only after the artifacts are real.
