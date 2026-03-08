# Notebooks

Use this directory for the notebooks that support the hackathon submission.

Expected contents:

- one Colab-friendly notebook that connects to the deployed HF Space
- one Northflank-friendly notebook path for verifier sanity checks, manual reward iteration, baselines, or training/debugging

Recommended split:

- Northflank notebook: main compute workspace on the team H100
- Colab notebook: thin public artifact required by the hackathon

## Status

- [x] Northflank smoke notebook note saved
- [x] runnable Northflank smoke script saved
- [ ] manual-playtest notebook or trace notebook saved
- [ ] thin public Colab notebook saved

Operational defaults:

- use the same Python dependency set as the repo runtime
- keep heavy verifier and training work on Northflank
- keep the Colab notebook focused on connecting to the deployed HF Space and exporting visible traces
- prefer a public HF Space for the hackathon; if private, document the token setup directly in the notebook

Northflank smoke gate:

- import `constellaration`
- generate one rotating-ellipse boundary
- run one low-fidelity verifier call
- write one artifact to persistent storage

Runnable repo path:

- `uv run python training/notebooks/northflank_smoke.py --output-dir <mounted-persistent-storage-path>`
- note: `training/notebooks/NORTHFLANK_SMOKE_NOTE.md`

The notebooks are supporting evidence for the environment, not the primary product.
