# PROTOCOL — PRO Instrument Use Across Postsurgical Pain Clinical Trials

**Topic:** Acute Postsurgical Pain (`topic.slate_number: 1`)
**Consensus body:** IMI-PainCare PROMPT — Pogatzki-Zahn et al., *Br J Anaesth* 2025 `[TO ENRICH: verify citation and full reference; flagged # VERIFY in config]`
**Repository:** `postsurgicalpain` (SAFE Lab PRO meta-research run)
**Date drafted:** 2026-07-13

---

## 1. Background

Patient-reported outcome (PRO) instruments are central to how postsurgical pain is
measured in interventional clinical trials, but their use across the trial landscape
is heterogeneous: many instruments exist, they are adopted unevenly, and only a
subset are endorsed by any consensus body. Two reference events frame the timeline:
the FDA PRO guidance (2006-10-11, a global anchor used across all topics in this
program) and, for this topic, the IMI-PainCare PROMPT core-outcome-set endorsement
(`time_anchors.endorsement_milestones`, dated 2025-03-14 `[TO ENRICH: confirm
endorsement date and scope against the PROMPT publication; flagged # VERIFY]`).

This study is one topic (slate #1) in a standardized, multi-topic meta-research
program that applies an identical detection-and-validation engine to each clinical
area, varying only the per-topic configuration and the frozen instrument dictionary.
The postsurgical pain topic is distinctive in that a bare Numerical Rating Scale /
Visual Analog Scale (NRS/VAS) is treated as a named, endorsed PRO here
(`classification.nrs_vas_is_pro: true`), unlike some other topics in the program.

`[TO ENRICH: substantive clinical/scientific background on postsurgical pain PRO
measurement and the IMI-PainCare PROMPT core outcome set — instruments, domains,
and rationale — with citations. Not present in repo.]`

## 2. Objectives

**Primary objective.** Describe how PRO instruments are used across the landscape of
postsurgical pain interventional trials: which instruments appear, how prevalent each
is, and how the mix is distributed across the cohort.

**Secondary objectives.**
1. **Endorsement alignment.** Quantify the share of trials that use at least one
   IMI-PainCare PROMPT–endorsed instrument (`alignment.mode: any_of`; a trial is
   "aligned" if it uses ANY endorsed instrument).
2. **Change over time.** Examine instrument use and alignment over calendar time,
   using the FDA guidance date (2006-10-11) and the PROMPT endorsement milestone
   (2025-03-14, VERIFY) as **reference anchors, not inclusion filters** (no date
   filter is applied to the cohort — `retrieval` has no date cutoff).
3. **Detection accuracy.** Establish that algorithmic instrument detection is
   accurate via two-reviewer dual coding on a structured validation sample.

## 3. Inclusion / Exclusion criteria

**Source population.** Interventional studies registered on ClinicalTrials.gov,
retrieved in `bins` mode (`retrieval.mode: bins`, `interventional_only: true`,
`root_term_count: 2`). No registration- or start-date filter is applied; pre-2006
trials are retained so the FDA guidance can serve as an over-time reference point.

**Inclusion (retrieval / Bin-1 + Bin-2), from `config/search.txt`:**
- **Root term 1 — acute postsurgical pain:** condition-field search over the acute
  postsurgical-pain synonym set (e.g., "Acute Postoperative Pain", "Post-operative
  Pain", "post surgical pain", "Postoperative Pain Management", …).
- **Root term 2 — chronic postsurgical pain:** condition-field search over the
  chronic/persistent postsurgical-pain synonym set (e.g., "Chronic Post-surgical
  Pain", "Persistent Postsurgical Pain", …).
- **Bin-2:** a fixed supplemental list of ~330 NCT IDs (`NCTIDS:` line in
  `search.txt`), shared across both roots.

> **Scope note (assumption).** Although the topic display name is "Acute Postsurgical
> Pain," the retrieval pulls BOTH acute (root 1) and chronic (root 2) postsurgical
> pain. This protocol treats the analytic cohort as *whatever `search.txt` retrieves*
> (acute + chronic postsurgical pain), with "acute" as the topic label rather than a
> filter. `[TO ENRICH: confirm intended cohort scope — acute-only vs. all
> postsurgical pain — with study lead.]`

**Exclusion (screening / Bin-3 title exclusion), from
`topic_config.yaml → screening.title_exclude`:** a trial is dropped if its title
contains any listed phrase. The ~45 exclusion titles cover off-topic themes:
chronic neuropathic / central pain drug trials, neuromodulation and stimulation
devices (SCS, DRG, DBS), dental/endodontic procedures, healthy-volunteer PK/PD
studies, and other non-postsurgical-pain contexts. The interventional-only filter is
re-checked independently at screening (`scripts/02_screen.py`, Rule 1).

**Volume gate (`volume_gate`).** Expected vetted cohort ≈ **948** NCTs; hard minimum
150. A retrieved cohort below the minimum halts the run.

## 4. Data sources

- **ClinicalTrials.gov** — primary trial records, retrieved via `scripts/01_extract.py`
  (config-driven; full pagination with a `fetched == totalCount` assertion before any
  write; one row per trial → `data/raw_export.csv`).
- **`config/search.txt`** — the two root-term condition queries and the Bin-2 NCT-ID
  supplement.
- **`config/topic_config.yaml`** — screening terms, classification flips, endorsed
  instrument set, time anchors, reconciliation and validation settings.
- **`config/vetted_ncts.csv`** — hand-vetted NCT list (~947 rows) used for cohort
  reconciliation (`reconciliation.vetted_nct_column: "NCT Number"`;
  `min_overlap_pct: 90`). `[TO ENRICH: file currently appears headerless / first row
  is an NCT ID; confirm the "NCT Number" column header matches the file.]`
- **`config/dictionary.py`** (operative) and **`config/dictionary_v1_frozen.py`**
  (audit) — the frozen instrument dictionary from Stage A; `frequency_floor: 3`.
  Currently a stub (`INSTRUMENTS = []`) — to be populated by Stage A before detection.
- **Pipeline scripts:** `01_extract` → `02_screen` → `03_reconcile` → `04_detect` →
  `05_build_validation_sample` → `06_validation_stats`.

## 5. Key design decisions

1. **The dictionary is empirically derived, curated, endorsement-flagged, and frozen.**
   The instrument dictionary is built in Stage A by empirically mining instrument
   mentions from the cohort's trial text (subject to `dictionary.frequency_floor: 3`),
   then curated by hand, flagged for which entries are endorsed by the consensus body,
   and **frozen** as an audit artifact (`config/dictionary_v1_frozen.py`) alongside the
   operative copy (`config/dictionary.py`).

2. **Detection uses only the frozen list.** PRO-instrument detection
   (`scripts/04_detect.py`) classifies each trial using **only** the frozen dictionary
   — no ad hoc, on-the-fly, or reviewer-time additions to the instrument list. The
   engine is identical across all topics in the program; only the config and the frozen
   dictionary change.

3. **The cohort is reconciled against a hand-vetted NCT list.** The algorithmically
   screened cohort is reconciled against `config/vetted_ncts.csv`
   (`scripts/03_reconcile.py`), producing BOTH / CODE_ONLY / VETTED_ONLY labels and an
   overlap percentage; the run halts if overlap falls below `min_overlap_pct: 90`.

4. **Detection accuracy is checked by two-reviewer dual coding.** A structured
   validation sample (`scripts/05_build_validation_sample.py`) is issued as **two
   separately-blinded reviewer copies** plus a lead-only answer key. Two reviewers
   independently classify each sampled trial; `scripts/06_validation_stats.py` computes
   inter-reviewer percent agreement and Cohen's kappa, reviewer-vs-algorithm agreement,
   the false-negative rate (a named PRO the algorithm missed), and any dictionary
   leakage ("(unlisted)" instruments reviewers flagged).

5. **NRS/VAS counts as an endorsed PRO for this topic.**
   `classification.nrs_vas_is_pro: true` and `nrs_vas_endorsed: true`; clinician-
   reported tools are NOT endorsed (`clinician_reported_endorsed: false`). These flips
   are marked `# VERIFY` in config. `[TO ENRICH: confirm NRS/VAS and clinician-reported
   endorsement status against the IMI-PainCare PROMPT publication.]`

6. **Endorsed instrument set (`alignment.any_of`).** Numerical Rating Scale; NRS; Pain
   interference; Procedure-specific physical function scale; ASES IMI PROMPT adaptation;
   OR-SDS IMI PROMPT adaptation; Procedure-specific pain intensity scale. `[TO ENRICH:
   verify every instrument name against the PROMPT publication — all flagged # VERIFY;
   note the endorsement_milestones.instruments list in config is missing commas
   (likely YAML typo) and should be corrected before it is parsed.]`

7. **No date filter; anchors are references only.** All trials, including pre-2006, are
   retained. The FDA guidance date (2006-10-11) and PROMPT endorsement date
   (2025-03-14, VERIFY) are used only to interpret the over-time analysis.

## 6. Planned analysis

1. **Cohort assembly & QC.** Extract → screen → reconcile. Report retrieved N,
   screened-kept N, reconciliation overlap %, and pass/fail against the volume gate
   (min 150; expected ≈ 948).
2. **Instrument prevalence (primary).** Using `04_detect.py` over the frozen
   dictionary, report the count and percentage of trials using each PRO instrument,
   ranked; report the distribution of instruments-per-trial.
3. **Endorsement alignment (secondary).** Report the share of trials aligned under
   `any_of` (≥1 endorsed instrument), and prevalence of each endorsed instrument. NRS/
   VAS included as endorsed per the classification flips.
4. **Over-time analysis (secondary).** Plot instrument use and alignment share by
   calendar year, annotated with the FDA-guidance and PROMPT-endorsement anchors.
   `[TO ENRICH: choose the trial date field for the time axis — e.g., start date vs.
   first-posted date.]`
5. **Detection validation.** Build the validation sample (random n=100, seed=42;
   endorsed census; variant scan), run two-reviewer dual coding, and report percent
   agreement, Cohen's kappa, reviewer-vs-algorithm agreement, false-negative rate, and
   dictionary leakage → written to `VALIDATION.md`.
6. **Reporting.** Descriptive throughout (counts, percentages, distributions, trends);
   no inferential hypothesis test is planned unless added later. `[TO ENRICH: specify
   any subgroup cuts of interest, e.g., by surgery type — the physical-function scale
   is surgery-type specific per the config note.]`

## 7. Limitations

- **Registry-only measurement.** Detection relies on ClinicalTrials.gov record text
  (outcome-measure fields, descriptions), not full protocols or publications;
  instruments described vaguely or only in linked publications may be missed.
- **Dictionary boundedness.** Detection is limited to the frozen dictionary; an
  instrument absent from Stage A mining (or below the frequency floor of 3) will not be
  detected. Dual-coding's false-negative and leakage checks bound but do not eliminate
  this.
- **Unverified config values.** The consensus citation, endorsement date, endorsed-
  instrument names, and classification flips are all `# VERIFY` in config and are
  carried as provisional (`[TO ENRICH]`) rather than asserted.
- **Scope ambiguity.** The cohort spans acute and chronic postsurgical pain despite the
  "acute" topic label; conclusions apply to the retrieved cohort as defined.
- **Reconciliation dependence.** Cohort validity leans on the hand-vetted NCT list;
  systematic gaps in that list would propagate. A possible header mismatch in
  `vetted_ncts.csv` should be resolved before reconciliation.
- **Free-text and synonym drift.** Instrument naming varies across records; the variant
  scan mitigates but cannot guarantee complete capture of spelling variants.
- **No causal claims.** The over-time analysis is descriptive; anchors mark context and
  do not support causal inference about guidance or endorsement effects.
