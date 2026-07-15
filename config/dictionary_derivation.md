# Dictionary Derivation — Acute/Chronic Postsurgical Pain (v1, FROZEN)

**Frozen:** 2026-07-14
**Operative file:** `config/dictionary.py` (frozen copy of `config/DRAFT_dictionary.py`)
**Topic:** postsurgical-pain (slate #1) · **Consensus body:** IMI-PainCare PROMPT
**Instruments:** 58 (46 `is_pro=True`, 12 `is_pro=False`; 5 `endorsed=True`, 53 `endorsed=False`)

This file records how the frozen dictionary was empirically derived, curated, and
endorsement-flagged, per the study protocol (Section 5). The dictionary is READ-ONLY
downstream; any change is a new versioned freeze, not an in-place edit.

---

## 1. Date & provenance
- Discovery pull run: 2026-07-13 (`scripts/dict_01_pull.py` → `data/dict_raw.csv`).
- Tally / seed + open-ended scan: `scripts/dict_02_tally.py` → `data/dict_candidates.csv`.
- Dead-pattern check: `scripts/dict_03_check.py` (0 dead is_pro, 0 dead endorsed,
  1 benign acronym-gap — HHS, see §7).
- Curated draft: `config/DRAFT_dictionary.py`; frozen to `config/dictionary.py` 2026-07-14.

## 2. Search string(s) (from `config/search.txt`, run as `query.term`, AREA[...] honored)
- **Root 1 — acute postsurgical pain:** `AREA[ConditionSearch] ("acute post surgical pain"
  OR "Acute Postoperative Pain" OR "Post-operative Pain" OR "Postoperative Pain Management"
  OR … )` (33 condition synonyms).
- **Root 2 — chronic postsurgical pain:** `AREA[ConditionSearch] ("chronic post surgical
  pain" OR "Chronic Post-surgical Pain" OR "Persistent Postsurgical Pain" OR … )` (21 synonyms).
- **Bin-2:** 350 vetted trials pulled directly by NCT ID (`NCTIDS:` line).
- **Discovery scope:** NO interventional filter (observational included) — deliberately
  broader than the analytic cohort, to mine the widest instrument vocabulary.

## 3. Reported vs retrieved counts (pagination asserted `fetched == totalCount` per string)
| Source | Reported total | Retrieved | Notes |
|---|---:|---:|---|
| Root 1 (acute) | 6833 | 6833 | 7 pages, 0 within-string dupes |
| Root 2 (chronic) | 286 | 286 | 1 page |
| Bin-2 by NCT ID | 350 req | 350 | 0 missing |
| **Combined (deduped)** | — | **6944** | 525 cross-string/list dupes removed |

`data/dict_raw.csv` = 6944 trials × {nct_id, outcome_measures, outcome_descriptions}.

## 4. Seed (the a-priori "known instruments" prior, read from `scripts/dict_02_tally.py` → `SEED`)
42 seed instruments (canonical names + abbreviations only; no generic words). Verbatim
from the script:

Numeric Rating Scale (NRS) · Visual Analog Scale (VAS) · Verbal Rating Scale (VRS) ·
Faces Pain Scale (FPS) · FLACC scale · Defense & Veterans Pain Rating Scale ·
CAPA (Clinically Aligned Pain Assess.) · SPID (sum pain intensity difference) ·
TOTPAR (total pain relief) · PID / PAR (pain intensity diff/relief) ·
Brief Pain Inventory (BPI) · McGill Pain Questionnaire (MPQ) ·
Pain Catastrophizing Scale (PCS) · Pain Disability Index (PDI) ·
Central Sensitization Inventory (CSI) · painDETECT · DN4 · LANSS ·
Neuropathic Pain Symptom Inv. (NPSI) · Quality of Recovery (QoR-15/40) · EQ-5D ·
SF-36 / SF-12 (Short Form) · PROMIS · WHOQOL · Oswestry Disability Index (ODI) ·
Roland-Morris Disability Q. (RMDQ) · WOMAC · KOOS / HOOS · DASH / QuickDASH ·
Oxford Knee/Hip Score (OKS/OHS) · ASES (Shoulder & Elbow Surgeons) ·
Constant-Murley score · Lysholm score · Harris Hip Score (HHS) ·
Hospital Anxiety & Depression (HADS) · State-Trait Anxiety Inventory (STAI) ·
Patient Health Questionnaire (PHQ) · GAD-7 (anxiety) ·
Pittsburgh Sleep Quality Index (PSQI) · Patient Global Impression (PGIC) ·
Overall Benefit of Analgesia (OBAS) · Opioid-Related Symptom Distress (ORSDS).

The open-ended scan (capitalized `…Scale/Score/Index/Questionnaire/Inventory/Survey`
phrases + acronym-shaped tokens, minus generic phrases and a non-PRO acronym stoplist)
surfaced additional real instruments promoted into the dictionary during curation:
CHEOPS, CPOT, Behavioral Pain Scale, PPPM, Neuropathic Pain Scale, EORTC QLQ-C30,
Knee Society Score, SANE, Beck Depression Inventory, Insomnia Severity Index,
Richards-Campbell Sleep Questionnaire, Tampa Scale of Kinesiophobia, APAIS,
Yale/mYPAS, APS-POQ-R, OHIP-14, POSAS, Ramsay Sedation Scale, RASS.

## 5. Frequency floor
- `config/topic_config.yaml → dictionary.frequency_floor: 3`.
- Empirically-derived candidates below 3 trials were not promoted into the dictionary.
- **Exception (see §6):** endorsed instruments bypass the floor.

## 6. Endorsement policy — the endorsed set is a FLOOR
- Endorsement is applied from `config/topic_config.yaml` (`alignment.endorsed_instruments`
  + `classification.nrs_vas_endorsed: true`), NOT invented. All config names are `# VERIFY`
  pending confirmation against the PROMPT publication (Pogatzki-Zahn et al., Br J Anaesth 2025).
- **Every endorsed instrument enters the dictionary regardless of frequency**, so alignment
  can never read zero by construction. If an endorsed instrument then turns out to be rare
  in the data, THAT low usage is the real finding.
- `endorsed=True` (5): **NRS** (config "NRS"/"Numerical Rating Scale"), **VAS**
  (`nrs_vas_endorsed: true`; also serves "Procedure-specific pain intensity scale"),
  **Pain Interference (PROMIS/BPI domain)** (config "Pain interference" — added as a floor
  entry), **ASES** (config "ASES IMI PROMPT adaptation"), **ORSDS** (config
  "OR-SDS IMI PROMPT adaptation").
- `endorsed=False`: all other 53 instruments (clinician-/observer-reported tools are not
  endorsed for this body: `clinician_reported_endorsed: false`).
- Post-freeze check: `scripts/dict_03_check.py` → 0 dead endorsed (all 5 match ≥1 trial:
  VAS 2751, NRS 2179, Pain Interference 152, ORSDS 27, ASES 13).

### Endorsement decisions and remaining verification
1. **"Procedure-specific physical function scale" — EXCLUDED by decision (2026-07-14,
   DECISION_LOG #4).** An abstract, surgery-type-specific category, not one instrument
   (realized by the procedure's function PRO: WOMAC/KOOS/HOOS/ODI/DASH/Oxford/ASES/…). Per
   user direction it is NOT in the endorsed set — dropped, not deferred. Would only be
   revisited if verification against the PROMPT publication shows a physical-function
   measure is a core endorsed instrument, which would require a new dictionary freeze.
2. **Alignment name mismatch — RESOLVED (2026-07-14, DECISION_LOG #4).**
   `config/topic_config.yaml → alignment.endorsed_instruments` was reconciled to the exact 5
   frozen `endorsed=True` canonicals, so `scripts/04_detect.py → is_aligned()` matches on
   canonical names. Verified 5 = 5, character-for-character.
3. **Still `# VERIFY`:** all config endorsement values (`nrs_vas_endorsed`, the endorsed
   set, endorsement date 2025-03-14) remain to be confirmed against the PROMPT publication.
   The second copy of the endorsement names in
   `time_anchors.endorsement_milestones[0].instruments` was reconciled to the same 5 frozen
   canonicals (DECISION_LOG #5); all three sets now equal (5 = 5 = 5).

## 7. Cut log
### 7a. Consolidations (fragments merged into one entry)
Representative merges (full provenance in `CURATION` inside `config/dictionary.py`):
- **VAS** ← Visual Analog/Analogue/Analogic Scale, "Visual Analog Pain Scale/Score", EVA.
- **NRS** ← NPRS, VNRS, NRSr, NRSm, "Numeric(al) Pain Rating Scale".
- **QoR** ← bare QoR, QoR-15, QoR-40; **SF Health Survey** ← SF-36/12/8, VR-12, RAND-36, "Health Survey".
- **HADS** ← "Hospital Anxiety and Depression"; **STAI** ← "State Anxiety Inventory".
- **WOMAC** ← "McMaster Universities Osteoarthritis Index"; **KOOS/HOOS** ← "Osteoarthritis Outcome Score".
- **MPQ** ← SF-MPQ, PRI; **Faces** ← FACES, Wong-Baker; **APAIS** ← "Information Scale".
- **EORTC QLQ-C30** and **WHOQOL** given spelled-out name patterns (robustness fix).

### 7b. Discarded as non-instruments (from `DISCARDED` in `config/dictionary.py`)
- **lab/biomarker:** CRP, ESR, IL-6/8/10/2, TNF-a, WBC, NLR, PLR, MMP-9, COX-2, DNA, CFU(s), ELISA, PCR, ABG
- **pharmacokinetics/units:** AUC, AUC0-72, AUC0-t, Cmax, Tmax, MME(s), MED, MEDD, HCl, mg/kg
- **physiologic/vitals/imaging:** MAP, MBP, HR, BP, SpO2, EtCO2, HRV, ANI, NOL, fMRI, CBCT, FEV1, FVC, PEF, MEP, MVIC
- **care-setting/adverse/regulatory:** PACU, ICU, POD1/2/3, AEs, SAEs, TEAEs, CTCAE, CDC, FDA, LOS
- **interventions/blocks/routes:** PCA, IV-PCA, TENS, TAP, ESPB, PENG, QLB, PECS, NSAID(s)
- **conditions/constructs:** CPSP, PPSP, PLP (phantom limb pain), POCD, POI, ADL
- **performance/quant-sensory (non-PRO):** QST, CPM, PPT, TUG, MRC, PPI
- **cognitive/delirium (off-topic):** MMSE, MoCA, CAM, CAM-ICU, PAED
- **generic/fragments/noise:** PAIN, SCALE, WORST, Likert Scale, Pain Score, Analgesia Score, Information Scale, Depression Scale, Health Questionnaire, II, III, LAST, YES, AND, USA, WHO
- **usability/other (out of scope):** SUS / System Usability Scale, PGA (physician/patient global — ambiguous), Aldrete Score, Bromage Scale

### 7c. Notable classification decisions
- **SPID/TOTPAR/PID/SPRID** kept for detection but `is_pro=False` (PRO-derived summary
  endpoints, not instruments; the underlying VAS/NRS is counted separately).
- 12 observer-/clinician-/proxy-reported scales `is_pro=False`: FLACC, CHEOPS, CPOT, BPS,
  PPPM, Constant-Murley, HHS, KSS, mYPAS, Ramsay/RSS, RASS (+ the SPID group).
