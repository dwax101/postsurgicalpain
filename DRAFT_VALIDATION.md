# DRAFT VALIDATION — Reproducibility Worksheet (postsurgical-pain)

**Purpose.** Independent-reviewer reproducibility check. The **ANALYST** column below is
filled with every result from the analyst's committed run (read from `qc_logs/*.log`,
`config/topic_config.yaml`, `figures/`, and `DECISION_LOG.md`). On a **fresh clone**, the
Independent Reviewer runs `python reproducibility/run_all.py` and records their observed
values in **REVIEWER**, then marks **MATCH** (`Y`/`N`). Leave REVIEWER/MATCH blank until
the reviewer's run.

> This worksheet validates that the **pipeline reproduces**. It is distinct from
> `VALIDATION.md`, which `06_validation_stats.py` fills with the **detection dual-coding**
> (two-reviewer) results after the manual review step.

**Analyst run:** 2026-07-14 · cohort n = 948 · frozen dictionary = 58 instruments
(5 endorsed) · consensus body = IMI-PainCare PROMPT.

---

## 1. Cohort assembly

| # | Metric | ANALYST | REVIEWER | MATCH |
|---|---|---|---|---|
| 1.1 | Extract — retrieval mode | bins (by NCT ID; 948 IDs) |  |  |
| 1.2 | Extract — unique trials pulled | 948 |  |  |
| 1.3 | Extract — rows written `data/raw_export.csv` | 948 |  |  |
| 1.4 | Screen — rows loaded | 948 |  |  |
| 1.5 | Screen — dropped (Rule 1, non-interventional) | 0 |  |  |
| 1.6 | Screen — dropped (Rule 2, bin-3 title exclusion) | 0 |  |  |
| 1.7 | Screen — final kept `data/screened_kept.csv` | 948 |  |  |

## 2. Gates (go/no-go)

| # | Metric | ANALYST | REVIEWER | MATCH |
|---|---|---|---|---|
| 2.1 | Volume gate — screened cohort size | 948 |  |  |
| 2.2 | Volume gate — expected size (config) | 948 |  |  |
| 2.3 | Volume gate — shortfall vs expected | 0.0% |  |  |
| 2.4 | Volume gate — outcome | **PASSED** |  |  |
| 2.5 | Reconcile — code cohort vs vetted list | 948 vs 948 |  |  |
| 2.6 | Reconcile — BOTH | 948 |  |  |
| 2.7 | Reconcile — CODE_ONLY | 0 |  |  |
| 2.8 | Reconcile — VETTED_ONLY | 0 |  |  |
| 2.9 | Reconcile — overlap % (min 90%) | 100.00% |  |  |
| 2.10 | Overlap gate — outcome | **PASSED** |  |  |

## 3. Detection (`04_detect.py`, frozen dictionary)

| # | Metric | ANALYST | REVIEWER | MATCH |
|---|---|---|---|---|
| 3.1 | Instruments loaded (read-only) | 58 |  |  |
| 3.2 | Alignment mode | any_of |  |  |
| 3.3 | Trials scored | 948 |  |  |
| 3.4 | **Completeness** (has_any_named_pro) | 737 (77.74%) |  |  |
| 3.5 | **Alignment** (uses_endorsed) | 662 (69.83%) |  |  |
| 3.6 | Distinct instruments detected | 52 |  |  |
| 3.7 | Concentration — instruments to 50% of uses | 3 |  |  |
| 3.8 | Endorsed detections — NRS | 343 |  |  |
| 3.9 | Endorsed detections — VAS | 327 |  |  |
| 3.10 | Endorsed detections — Pain Interference | 42 |  |  |
| 3.11 | Endorsed detections — OR-SDS | 3 |  |  |
| 3.12 | Endorsed detections — ASES | 0 |  |  |

## 4. Validation sample (`05_build_validation_sample.py`)

| # | Metric | ANALYST | REVIEWER | MATCH |
|---|---|---|---|---|
| 4.1 | RANDOM_N size (seed) | 100 (seed=42) |  |  |
| 4.2 | ENDORSED_CENSUS | 662 |  |  |
| 4.3 | VARIANT_SCAN | 0 |  |  |
| 4.4 | Combined unique sample | 692 |  |  |
| 4.5 | In >1 stratum | 70 |  |  |

## 5. Figures & epoch table (`07_figures.py`)

| # | Metric | ANALYST | REVIEWER | MATCH |
|---|---|---|---|---|
| 5.1 | Category split — Named PRO | 737 |  |  |
| 5.2 | Category split — NRS/VAS-only (matched non-PRO only) | 30 |  |  |
| 5.3 | Category split — Vague only | 0 |  |  |
| 5.4 | Category split — No PRO | 181 |  |  |
| 5.5 | Registration window (first-posted year) | 2000–2026 |  |  |
| 5.6 | Epoch pre-PROMPT (<2025) — named / aligned / % | 587 / 521 / 88.8% |  |  |
| 5.7 | Epoch post-PROMPT (≥2025) — named / aligned / % | 150 / 141 / 94.0% |  |  |
| 5.8 | Figures written | 7 + epoch_table.csv |  |  |

## 6. Reviewer reference table (`08_reference_table.py`)

| # | Metric | ANALYST | REVIEWER | MATCH |
|---|---|---|---|---|
| 6.1 | `reference_table.csv` — instruments / PRO / endorsed | 58 / 46 / 5 |  |  |

## 7. Config invariants (source of truth — must be identical, not re-derived)

| # | Metric | ANALYST | REVIEWER | MATCH |
|---|---|---|---|---|
| 7.1 | Frozen dictionary — total instruments | 58 |  |  |
| 7.2 | Frozen dictionary — endorsed=True | 5 |  |  |
| 7.3 | Frequency floor | 3 |  |  |
| 7.4 | classification.nrs_vas_is_pro / nrs_vas_endorsed | True / True |  |  |
| 7.5 | classification.clinician_reported_endorsed | False |  |  |
| 7.6 | reconciliation.min_overlap_pct | 90 |  |  |
| 7.7 | volume_gate expected / min | 948 / 150 |  |  |
| 7.8 | Time anchor — FDA PRO guidance | 2006-10-11 |  |  |
| 7.9 | Time anchor — IMI-PainCare PROMPT endorsement | 2025-03-14 |  |  |

---

**Reviewer sign-off:** ______________________  **Date:** __________
All MATCH = `Y` ⇒ pipeline reproduces from committed inputs. Any `N` ⇒ investigate before
sign-off (note: ClinicalTrials.gov is a live source; small count drift from post-run
registry edits should be annotated, not silently accepted).
