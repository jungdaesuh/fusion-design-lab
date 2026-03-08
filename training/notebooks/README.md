# Notebooks

Use this directory for the notebooks that support the hackathon submission.

Expected contents:

- one public notebook artifact that connects to the deployed HF Space; mirror it to Colab if the submission surface requires Colab specifically
- one Northflank-friendly notebook path for verifier sanity checks, manual reward iteration, baselines, or training/debugging

Recommended split:

- Northflank notebook: main compute workspace on the team H100
- public notebook artifact: thin submission surface, mirrored to Colab only if the submission form still requires it
- trained model: required; the public notebook should include a trained-policy demonstration even if performance is modest

## Status

- [x] Northflank smoke notebook note saved
- [x] runnable Northflank smoke script saved
- [x] Northflank smoke test passed on the team H100
- [x] repository GRPO notebook saved
- [ ] manual-playtest notebook or trace notebook saved
- [ ] public Colab mirror or submission notebook link saved if still required

Operational defaults:

- use the same Python dependency set as the repo runtime
- keep heavy verifier and training work on Northflank
- keep low-fidelity `run` as the training inner loop; do not put high-fidelity `submit` in every RL step
- use high-fidelity `submit` only for sparse checkpoint evaluation, paired fixture checks, manual traces, and final evidence
- keep the repository GRPO notebook aligned to the shared helper contract in `fusion_lab/llm_agent.py`
- the standard notebook reward/eval path is low-fidelity-only and ignores `submit` by default
- keep the public submission notebook focused on connecting to the deployed HF Space and exporting visible traces
- prefer a public HF Space for the hackathon; if private, document the token setup directly in the notebook

Northflank smoke gate:

- import `constellaration`
- generate one rotating-ellipse boundary
- run one low-fidelity verifier call
- write one artifact to persistent storage

Runnable repo path:

- `uv run python training/notebooks/northflank_smoke.py --output-dir <mounted-persistent-storage-path>`
- note: `training/notebooks/NORTHFLANK_SMOKE_NOTE.md`
- latest passing artifact example: `/home/jovyan/fusion-design-lab/smoke/northflank_smoke_20260308T023646Z.json`

LLM notebook helpers should use the packaged prompt/action contract in:

- `fusion_lab/llm_agent.py`

Current repository notebook:

- `training/notebooks/fusion_design_lab_training.ipynb`

The notebooks are supporting evidence for the environment, not the primary product. The required artifact is the notebook plus trained-policy evidence; a standalone checkpoint file is optional only if the notebook can still demonstrate the trained behavior.
