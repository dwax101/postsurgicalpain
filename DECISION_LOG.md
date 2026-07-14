# Decision Log

## Entry #1 — 2026-07-13
Repo initialized: postsurgicalpain

## Entry #2 — 2026-07-13 — Phase 1: PROTOCOL.md drafted
Replaced the PROTOCOL.md stub with the full study protocol (Sections 1–7:
Background, Objectives, Inclusion/Exclusion, Data sources, Key design decisions,
Planned analysis, Limitations). Criteria were made concrete by reading
`config/topic_config.yaml` and `config/search.txt`.

Key decisions recorded:
- Cohort = whatever `search.txt` retrieves, spanning BOTH acute (root 1) and
  chronic (root 2) postsurgical pain, despite the "Acute Postsurgical Pain"
  topic label. Flagged as an assumption to confirm with the study lead.
- Section 5 states the four required properties: dictionary is empirically
  derived, curated, endorsement-flagged, and frozen; detection uses only the
  frozen list; cohort reconciled against the hand-vetted NCT list (≥90% overlap
  gate); detection accuracy checked by two-reviewer dual coding.
- No date filter; FDA guidance (2006-10-11) and PROMPT endorsement (2025-03-14,
  VERIFY) used only as over-time reference anchors.
- Endorsed set and classification flips (NRS/VAS = endorsed PRO; clinician-
  reported not endorsed) recorded from config; all `# VERIFY` items and any
  domain facts absent from the repo were marked `[TO ENRICH: ...]` rather than
  invented.

Open items flagged in-protocol as [TO ENRICH]: verify consensus citation and
endorsement date; verify endorsed-instrument names; fix missing commas in
`endorsement_milestones.instruments` YAML list; confirm cohort scope
(acute-only vs. all postsurgical pain); confirm `vetted_ncts.csv` header vs.
configured "NCT Number" column; choose the date field for the time axis.

Not committed.

## Entry #3 — 2026-07-13 — Phase 2: working branch confirmed
Confirmed the working branch is `analysis/postsurgicalpain` (created during
setup; also present on origin as `remotes/origin/analysis/postsurgicalpain`).
`git branch --show-current` → `analysis/postsurgicalpain`. All Phase-1 work
(PROTOCOL.md, DECISION_LOG.md) proceeds on this branch, not `main`.

Convention reaffirmed: DECISION_LOG.md is append-only — new entries are added at
the end; prior entries are never edited, reordered, or deleted.

Not committed.

## Entry #4 — 2026-07-14 — Alignment endorsed-set reconciled to frozen dictionary canonicals
Resolved the discrepancy logged in DISCREPANCY_LOG (2026-07-14): `is_aligned()` in
`scripts/04_detect.py` matches `alignment.endorsed_instruments` strings against the
frozen dictionary's canonical names, which previously did not match. Updated ONLY the
`endorsed_instruments` list in `config/topic_config.yaml` to the EXACT canonical strings
of the 5 `endorsed=True` entries in the frozen `config/dictionary.py` (which was NOT
modified). The 7 provisional labels reconcile to 5 tools per user direction:
- "Numerical Rating Scale" + "NRS"        -> "Numeric Rating Scale (NRS)" (same tool, collapsed)
- "Procedure-specific pain intensity scale" -> "Visual Analog Scale (VAS)" (folded into VAS; VAS stays endorsed)
- "Pain interference"                     -> "Pain Interference (PROMIS/BPI domain)"
- "ASES IMI PROMPT adaptation"            -> "ASES (Amer. Shoulder & Elbow Surgeons)"
- "OR-SDS IMI PROMPT adaptation"          -> "Opioid-Related Symptom Distress Scale (ORSDS)"
- "Procedure-specific physical function scale" -> DROPPED (no endorsed=True canonical;
  abstract surgery-specific category, unresolved [TO ENRICH]).
`# VERIFY` markers left in place. Verified with a 3-line check: config's endorsed_instruments
== the 5 frozen endorsed=True canonicals, character-for-character, count 5 = 5 (PASS).

Also fixed a PRE-EXISTING, unrelated YAML syntax error found during verification:
`time_anchors.endorsement_milestones[0].instruments` was a space-separated list with no
commas, which made the ENTIRE config unparseable by `yaml.safe_load` (so the pipeline
could not load it at all). Added the missing commas (syntax only). The names in that list
are a stale parallel copy of the endorsement set and were NOT reconciled (out of scope) —
flagged inline and here for a separate follow-up.

Not committed.

## Entry #5 — 2026-07-14 — Stale endorsement-name copy reconciled
Completed the follow-up from Entry #4: reconciled the second copy of the endorsement
names in `time_anchors.endorsement_milestones[0].instruments` to the SAME 5 frozen
dictionary `endorsed=True` canonicals (VAS, NRS, Pain Interference, ASES, ORSDS); the old
7 provisional names are gone and "Procedure-specific physical function scale" stays
excluded (DECISION_LOG #4). Verified: `time_anchors...instruments` ==
`alignment.endorsed_instruments` == the frozen endorsed=True canonicals, all three sets
equal, 5 = 5 = 5, character-for-character (PASS). `# VERIFY` markers left in place; frozen
`config/dictionary.py` not modified.

Not committed.

## Entry #6 — 2026-07-14
Extraction (`scripts/01_extract.py`, mode=bins, interventional=True). 2 search string(s); cross-search dupes removed 412; final 6130 trials to `data/raw_export.csv`. Pagination asserted == totalCount per string before write.

## Entry #7 — 2026-07-14
Screening (`scripts/02_screen.py`, mode=bins). Loaded 6130; dropped 0 non-interventional, 27 bin-3 title exclusion; final kept 6103 to `data/screened_kept.csv`.

## Entry #8 — 2026-07-14
Volume gate PASSED (`run_all.py`). Screened cohort 6103; expected 948 (-543.8% short). Recorded so the gate's decision is on disk, not only in the terminal.

## Entry #9 — 2026-07-14
Extraction (`scripts/01_extract.py`, mode=bins, interventional=True). 2 search string(s); cross-search dupes removed 412; final 6130 trials to `data/raw_export.csv`. Pagination asserted == totalCount per string before write.

## Entry #10 — 2026-07-14
Screening (`scripts/02_screen.py`, mode=bins). Loaded 6130; dropped 0 non-interventional, 27 bin-3 title exclusion; final kept 6103 to `data/screened_kept.csv`.

## Entry #11 — 2026-07-14
Volume gate PASSED (`run_all.py`). Screened cohort 6103; expected 948 (-543.8% short). Recorded so the gate's decision is on disk, not only in the terminal.

## Entry #12 — 2026-07-14
Cohort reconciliation (`scripts/03_reconcile.py`). Code 6103 vs vetted 948. Both 948, code-only 5155, vetted-only 0. Overlap 15.53% (min 90%). Report: `data/reconciliation_report.csv`.

## Entry #13 — 2026-07-14
Overlap gate FAILED: 15.5% < 90% (both 948, code-only 5155, vetted-only 0).

## Entry #14 — 2026-07-14
Extraction (`scripts/01_extract.py`, mode=bins, interventional=True). 0 search string(s); cross-search dupes removed 0; final 948 trials to `data/raw_export.csv`. Pagination asserted == totalCount per string before write.

## Entry #15 — 2026-07-14
Screening (`scripts/02_screen.py`, mode=bins). Loaded 948; dropped 0 non-interventional, 0 bin-3 title exclusion; final kept 948 to `data/screened_kept.csv`.

## Entry #16 — 2026-07-14
Volume gate PASSED (`run_all.py`). Screened cohort 948; expected 948 (0.0% short). Recorded so the gate's decision is on disk, not only in the terminal.

## Entry #17 — 2026-07-14
Cohort reconciliation (`scripts/03_reconcile.py`). Code 948 vs vetted 948. Both 948, code-only 0, vetted-only 0. Overlap 100.00% (min 90%). Report: `data/reconciliation_report.csv`.

## Entry #18 — 2026-07-14
Overlap gate PASSED (`run_all.py`). Overlap 100.0% ≥ 90% (both 948, code-only 0, vetted-only 0). This is the gate's own pass/fail record, distinct from 03_reconcile.py's log.

## Entry #19 — 2026-07-14
PRO detection (`scripts/04_detect.py`, config-driven). Dictionary: `config/dictionary.py` (58 instruments, read-only). Alignment mode: any_of. Input: 948 trials. Completeness 737 (77.74%); alignment 662 (69.83%).

## Entry #20 — 2026-07-14
Built detection-validation sample (`scripts/05_build_validation_sample.py`). Strata over 948-trial cohort: RANDOM_100 (seed=42), ENDORSED_CENSUS (662), VARIANT_SCAN (0). Combined 692 unique (70 multi-stratum). Two blinded reviewer files + lead KEY + recognition_list.md written.

## Entry #21 — 2026-07-14
Standard figure set (`scripts/07_figures.py`). Wrote 7 figures + epoch table to `figures/` for postsurgical-pain (948 trials). Time anchors: FDA 2006 + 1 endorsement milestone(s).

## Entry #22 — 2026-07-14
Reviewer reference table (`scripts/08_reference_table.py`). Wrote reference_table.csv: 58 instruments (46 PRO, 5 endorsed). The 'What it measures' column is [VERIFY] — the team fills it from each instrument's source before handing the sheet to reviewers.

## Entry #23 — 2026-07-14 — Phase 4: interpretive notebook
Created `notebooks/analysis.ipynb` (paired with jupytext to `notebooks/analysis.py`
via `py:percent`; committed with all cell outputs/execution counts stripped —
nbstripout-clean). The notebook READS `data/detection_results.csv` (n=948) and
INTERPRETS the standard figure set already produced by `scripts/07_figures.py`; it
references the PNGs in `figures/` and does NOT regenerate them. Four interpretive
markdown sections, each framed as exploratory-descriptive (endorsed set = one
heterogeneity example, never adherence/quality; 2006 FDA and 2025 PROMPT dates are
reference lines, not filters):
  1. Category split (named 737/77.7%, no-PRO 181/19.1%) + fragmentation (52 instruments,
     NRS+VAS ~48% of 1404 uses, top-3 = 54%, 3 instruments reach 50%).
  2. Over-time category trend (2000–2026; named-PRO share ~60%->~85%), referencing the
     FDA-2006 and PROMPT-2025 lines — a secular drift, no step change at either anchor.
  3. Endorsed uptake 662 (69.8%/89.8% of named-PRO), framed descriptively: composition is
     almost entirely NRS/VAS; PROMPT-specific tools rare (Pain Interference 42, OR-SDS 3,
     ASES 0) — endorsed-set-is-a-floor makes ASES=0 a real finding, not a detection gap.
  4. Epoch table (`figures/epoch_table.csv`): pre-2025 88.8% vs post-2025 94.0% — modest,
     driven by pre-existing NRS/VAS use; descriptive split, not a causal before/after.
Also declared the toolchain: added matplotlib/jupyterlab/jupytext/nbstripout to
`environment.yml` and added `.pre-commit-config.yaml` (jupytext --sync + nbstripout).
Verified: notebook code executes end-to-end against the data; .ipynb is valid nbformat
v4, paired, and output-stripped. Not committed.

## Entry #24 — 2026-07-14 — Phase 6: reproducibility handoff
Confirmed `reproducibility/run_all.py` drives the full pipeline from
`config/topic_config.yaml`: `--dry-run` prints the config-driven plan
(01_extract → 02_screen → [VOLUME GATE] → 03_reconcile → [OVERLAP GATE] →
04_detect → 05_build_validation_sample → 07_figures → 08_reference_table), all step
scripts exist, and the config loads. Did NOT trigger a fresh live full re-run to avoid
re-hitting the CTG API and appending duplicate gate/step entries to this append-only log;
the recorded end-to-end run (Entries #14–#22, all 948) plus the complete `qc_logs/` set
are the reproducibility evidence. 06_validation_stats is intentionally excluded (human
dual-coding gate).

Wrote `reproducibility/README.md`: the one-command run (`python
reproducibility/run_all.py`, plus --dry-run/--from), the environment
(`environment.yml`, conda env pro-workflow, Python 3.11), the random seed
(validation.random_seed=42, n=100 — the only stochastic step), and a data-availability
statement (data/ is gitignored and re-created by re-running; cohort pulled by NCT ID from
the vetted list, so deterministic).

Generated `DRAFT_VALIDATION.md`: a reproducibility worksheet with the ANALYST column
filled from logs/config/Decision Log (cohort 948 through extract→screen→reconcile→detect;
volume & overlap gates PASSED; completeness 737/77.74%; alignment 662/69.83%; endorsed
detections NRS 343 / VAS 327 / Pain Interference 42 / OR-SDS 3 / ASES 0; validation sample
RANDOM_100 seed 42, census 662, combined 692; epoch 88.8%/94.0%; 58 instruments/5
endorsed). REVIEWER and MATCH columns left blank for the independent reviewer's fresh run.
Distinct from `VALIDATION.md` (detection dual-coding, filled later by 06). Not committed.
