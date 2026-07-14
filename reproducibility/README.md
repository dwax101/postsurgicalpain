# Reproducibility & Handoff — postsurgical-pain

This topic's entire analysis is driven by committed inputs and one command. An
Independent Reviewer, on a **fresh clone**, runs the same command and must reproduce the
same numbers recorded in `DRAFT_VALIDATION.md`.

## One-command run

```bash
python reproducibility/run_all.py
```

Run it from the repository root. It executes the pipeline in order and **halts hard at
each go/no-go gate**:

```
01_extract → 02_screen → [VOLUME GATE] → 03_reconcile → [OVERLAP GATE]
           → 04_detect → 05_build_validation_sample → 07_figures → 08_reference_table
```

Every parameter comes from `config/topic_config.yaml` (the single source of truth) —
nothing is hardcoded per topic, so the reviewer's run and the analyst's run are driven by
identical committed inputs. Each step writes a `qc_logs/*.log` and a `DECISION_LOG.md`
entry; both gates write their own log + Decision Log entry.

Useful flags:

```bash
python reproducibility/run_all.py --dry-run     # print the plan, run nothing
python reproducibility/run_all.py --from 03     # resume from a step (01/02/03/04/05)
```

**Not run by `run_all.py`:** `06_validation_stats.py`. It requires the two **completed
human-reviewer** dual-coding workbooks, which do not exist until the manual review step is
done. That human step is the wall between the analyst's pipeline and the reviewer's
sign-off. `05_build_validation_sample.py` is also **safe to re-run**: if the reviewer
`.xlsx` files already exist it preserves them and only refreshes its log.

## Environment

Dependencies are pinned in [`../environment.yml`](../environment.yml) (conda env
`pro-workflow`, Python 3.11):

```bash
conda env create -f environment.yml
conda activate pro-workflow
```

Core: `pandas`, `requests`, `pyyaml`, `numpy`, `scipy`, `openpyxl`, `matplotlib`. Notebook
tooling: `jupyterlab`, `jupytext`, `nbstripout` (the interpretive notebook
`notebooks/analysis.ipynb` is paired to `analysis.py` and committed output-stripped).

## Random seed

The only stochastic step is the detection-validation **random sample**
(`05_build_validation_sample.py`). It is fully reproducible: `validation.random_seed: 42`
and `validation.random_sample_n: 100` in `config/topic_config.yaml`, applied via
`random.seed(seed)` before `random.sample(...)`. Same config → identical `RANDOM_100`
sample on any machine. No other step uses randomness.

## Data-availability statement

**Raw and derived data are NOT committed — they are re-created by re-running the
pipeline.** `.gitignore` excludes `data/*` (only `data/.gitkeep` is tracked). What *is*
committed is everything needed to regenerate that data deterministically:

- `config/topic_config.yaml` — all retrieval, screening, gate, classification, and
  validation parameters.
- `config/search.txt` and `config/vetted_ncts.csv` — the cohort definition (the analytic
  cohort is pulled **by NCT ID** from the hand-vetted list, so the pull is deterministic).
- `config/dictionary.py` — the **frozen** PRO-instrument dictionary (58 instruments), with
  `config/dictionary_derivation.md` recording how it was built.

Running `python reproducibility/run_all.py` rebuilds `data/` (raw export, screened cohort,
reconciliation report, detection results) and `figures/` from ClinicalTrials.gov via the
v2 API. The source registry is a live external resource; trial records added or edited
after the recorded run may cause small differences, which is why the reviewer records
observed counts in `DRAFT_VALIDATION.md` against the analyst's committed values.

## Handoff artifacts

| File | Purpose |
|---|---|
| `DRAFT_VALIDATION.md` | Analyst's recorded results; reviewer fills REVIEWER/MATCH on a fresh run. |
| `VALIDATION.md` | Detection dual-coding results (written by `06_validation_stats.py` after human review). |
| `DECISION_LOG.md` | Append-only audit trail of every step, gate, and decision. |
| `qc_logs/*.log` | Per-step record counts and gate outcomes. |
| `DISCREPANCY_LOG.md` | Reconciliation / config discrepancies and their resolution. |
