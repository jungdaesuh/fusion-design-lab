# Northflank Smoke Note

This is the concrete smoke path for the repo's Northflank compute gate.

## Goal

Prove all four required conditions in the Northflank Jupyter workspace:

1. `constellaration` imports
2. one rotating-ellipse boundary is generated
3. one low-fidelity verifier call succeeds
4. one JSON artifact is written to persistent storage

## Repo Entry Point

Use [northflank_smoke.py](/Users/suhjungdae/code/fusion-design-lab/training/notebooks/northflank_smoke.py).

It uses the repo SSOT values from:

- [server/environment.py](/Users/suhjungdae/code/fusion-design-lab/server/environment.py)
- [server/physics.py](/Users/suhjungdae/code/fusion-design-lab/server/physics.py)

## Northflank Run

Run from the repo root after the notebook container is up and the persistent volume is mounted:

```bash
uv sync --extra notebooks
uv run python training/notebooks/northflank_smoke.py \
  --output-dir /path/to/northflank/persistent-storage/fusion-design-lab/smoke
```

Replace `/path/to/northflank/persistent-storage/...` with the real mounted path in the workspace.

## Expected Output

The command prints the artifact path it wrote, for example:

```text
/path/to/northflank/persistent-storage/fusion-design-lab/smoke/northflank_smoke_20260308T000000Z.json
```

The JSON artifact records:

- UTC timestamp
- `constellaration` version
- generated boundary type
- rotating-ellipse baseline parameters
- low-fidelity verifier metrics

## Local Dry Run

The same script can be exercised locally with:

```bash
uv run python training/notebooks/northflank_smoke.py
```

That writes a small artifact under `training/notebooks/artifacts/`.
