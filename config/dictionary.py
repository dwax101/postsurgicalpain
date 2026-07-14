#!/usr/bin/env python3
"""
config/dictionary.py  —  FROZEN PRO-instrument dictionary v1 (Stage A output).

FROZEN 2026-07-14 from config/DRAFT_dictionary.py. This is the operative dictionary
read by scripts/04_detect.py. It MUST NOT change after this freeze; any revision is a
new versioned freeze with a DECISION_LOG entry, not an in-place edit. Derivation and
cut log: config/dictionary_derivation.md.

Hand-curated from data/dict_candidates.csv (+ data/dict_raw.csv). Fragments of the
same instrument are consolidated into ONE entry; every entry carries BOTH the
spelled-out name AND the acronym. Non-instruments (lab/biomarker acronyms,
anthropometrics, care-setting acronyms, generic phrase fragments) are discarded.

RULES honored here:
  - Every acronym pattern is \\b-anchored so short forms cannot match inside longer
    words (e.g. \\bASES\\b will not fire inside "phases" or "assess").
  - is_pro is set per config/topic_config.yaml -> classification.nrs_vas_is_pro
    (TRUE for this topic, so single-item NRS/VAS count as PROs). Observer- or
    clinician-reported scales are is_pro=False.
  - endorsed is set per config/topic_config.yaml (alignment.endorsed_instruments +
    classification.nrs_vas_endorsed), applied as the endorsement policy: endorsed=True
    for NRS, VAS, ASES, ORSDS, and Pain Interference; endorsed=False for all others.
    Every flag is now True/False (no None). See config/dictionary_derivation.md.

Schema matches scripts/04_detect.py
(load_instruments -> INSTRUMENTS; compile_instruments reads canonical/patterns/
is_pro/endorsed). Curation provenance is in CURATION below (printed by __main__).
"""

INSTRUMENTS = [
    # ---------------- pain intensity, patient-reported (is_pro True) ----------------
    {"canonical": "Visual Analog Scale (VAS)", "is_pro": True, "endorsed": True,
     "patterns": [r"visual\s+analog(?:ue|ic)?\s+(?:pain\s+)?scale",
                  r"visual\s+analog(?:ue|ic)?\s+(?:pain\s+)?score",
                  r"\bVAS\b", r"\bEVA\b"]},
    {"canonical": "Numeric Rating Scale (NRS)", "is_pro": True, "endorsed": True,
     "patterns": [r"numeric(?:al)?\s+(?:pain\s+)?rating\s+scale",
                  r"\bNRS\b", r"\bNPRS\b", r"\bVNRS\b", r"\bNRSr\b", r"\bNRSm\b"]},
    {"canonical": "Verbal Rating Scale (VRS)", "is_pro": True, "endorsed": False,
     "patterns": [r"verbal\s+rating\s+scale", r"verbal\s+descriptor\s+scale", r"\bVRS\b"]},
    {"canonical": "Faces Pain Scale / Wong-Baker (FPS)", "is_pro": True, "endorsed": False,
     "patterns": [r"faces\s+pain\s+scale(?:[-\s]revised)?", r"wong[-\s]?baker",
                  r"\bFPS(?:-R)?\b", r"\bFACES\b"]},

    # ---------------- pain intensity, observer-reported (is_pro False) ----------------
    {"canonical": "FLACC scale", "is_pro": False, "endorsed": False,
     "patterns": [r"\bFLACC\b", r"face,?\s*legs,?\s*activity,?\s*cry"]},
    {"canonical": "CHEOPS (Children's Hosp. Eastern Ontario Pain Scale)", "is_pro": False, "endorsed": False,
     "patterns": [r"\bCHEOPS\b", r"children'?s\s+hospital\s+of\s+eastern\s+ontario\s+pain\s+scale",
                  r"eastern\s+ontario\s+pain\s+scale"]},
    {"canonical": "CPOT (Critical-Care Pain Observation Tool)", "is_pro": False, "endorsed": False,
     "patterns": [r"\bCPOT\b", r"critical[-\s]care\s+pain\s+observation\s+tool"]},
    {"canonical": "Behavioral Pain Scale (BPS)", "is_pro": False, "endorsed": False,
     "patterns": [r"behavio(?:u)?ral\s+pain\s+scale", r"\bBPS\b"]},
    {"canonical": "PPPM (Parents' Postoperative Pain Measure)", "is_pro": False, "endorsed": False,
     "patterns": [r"\bPPPM\b", r"parents'?\s+postoperative\s+pain\s+measure"]},

    # ---------------- multidimensional / other pain, patient-reported ----------------
    {"canonical": "Brief Pain Inventory (BPI)", "is_pro": True, "endorsed": False,
     "patterns": [r"brief\s+pain\s+inventory", r"\bBPI(?:-SF)?\b"]},
    # Endorsed floor entry: config alignment.endorsed_instruments lists "Pain interference"
    # (a PROMIS / BPI domain). Enters the dictionary regardless of frequency so alignment
    # cannot read zero by construction (endorsed-set-is-a-floor rule).
    {"canonical": "Pain Interference (PROMIS/BPI domain)", "is_pro": True, "endorsed": True,
     "patterns": [r"pain\s+interference"]},
    {"canonical": "McGill Pain Questionnaire (MPQ)", "is_pro": True, "endorsed": False,
     "patterns": [r"mcgill\s+pain\s+questionnaire", r"\bMPQ\b", r"\bSF-?MPQ\b",
                  r"pain\s+rating\s+index", r"\bPRI\b"]},
    {"canonical": "Pain Catastrophizing Scale (PCS)", "is_pro": True, "endorsed": False,
     "patterns": [r"pain\s+catastroph\w+\s+scale", r"\bPCS\b"]},
    {"canonical": "Neuropathic Pain Scale (NPS)", "is_pro": True, "endorsed": False,
     "patterns": [r"neuropathic\s+pain\s+scale", r"\bNPS\b"]},
    {"canonical": "Central Sensitization Inventory (CSI)", "is_pro": True, "endorsed": False,
     "patterns": [r"central\s+sensiti[sz]ation\s+inventory", r"\bCSI\b"]},
    {"canonical": "Pain Disability Index (PDI)", "is_pro": True, "endorsed": False,
     "patterns": [r"pain\s+disability\s+index", r"\bPDI\b"]},

    # ---------------- neuropathic-pain screening (patient / mixed) ----------------
    {"canonical": "painDETECT", "is_pro": True, "endorsed": False,
     "patterns": [r"pain\s?detect", r"\bPD-?Q\b"]},
    {"canonical": "DN4", "is_pro": True, "endorsed": False,
     "patterns": [r"\bDN-?4\b", r"douleur\s+neuropathique"]},
    {"canonical": "LANSS", "is_pro": True, "endorsed": False,
     "patterns": [r"\bLANSS\b", r"leeds\s+assessment\s+of\s+neuropathic"]},
    {"canonical": "Neuropathic Pain Symptom Inventory (NPSI)", "is_pro": True, "endorsed": False,
     "patterns": [r"\bNPSI\b", r"neuropathic\s+pain\s+symptom\s+inventory"]},

    # ---------------- analgesic PRO-derived summary endpoints ----------------
    {"canonical": "SPID / TOTPAR / PID / SPRID (analgesic endpoints)", "is_pro": False, "endorsed": False,
     "patterns": [r"\bSPID\d*\b", r"\bSPIDs\b", r"\bTOTPAR\b", r"\bSPRID\b", r"\bPRID\b", r"\bPID\b",
                  r"sum(?:med)?\s+of\s+pain\s+intensity\s+difference", r"total\s+pain\s+relief",
                  r"pain\s+intensity\s+difference"]},

    # ---------------- recovery / HRQoL, patient-reported ----------------
    {"canonical": "Quality of Recovery (QoR-15/40)", "is_pro": True, "endorsed": False,
     "patterns": [r"quality\s+of\s+recovery", r"\bQoR-?\d+\b", r"\bQOR-?\d+\b", r"\bQoR\b"]},
    {"canonical": "EQ-5D", "is_pro": True, "endorsed": False,
     "patterns": [r"\bEQ-?5D(?:-?[35]L)?\b", r"euroqol"]},
    {"canonical": "Short Form Health Survey (SF-36/12/VR-12)", "is_pro": True, "endorsed": False,
     "patterns": [r"\bSF-?36\b", r"\bSF-?12\b", r"\bSF-?8\b", r"\bVR-?12\b", r"\bRAND-?36\b",
                  r"short[-\s]form\s+(?:36|12|health\s+survey)"]},
    {"canonical": "PROMIS", "is_pro": True, "endorsed": False,
     "patterns": [r"\bPROMIS\b", r"patient[-\s]reported\s+outcomes?\s+measurement\s+information"]},
    {"canonical": "WHOQOL", "is_pro": True, "endorsed": False,
     "patterns": [r"\bWHOQOL(?:-?BREF)?\b",
                  r"world\s+health\s+organi[sz]ation\s+quality\s+of\s+life"]},
    {"canonical": "EORTC QLQ-C30", "is_pro": True, "endorsed": False,
     "patterns": [r"\bQLQ-?C?30\b", r"\bEORTC\b",
                  r"european\s+organi[sz]ation\s+for\s+research\s+and\s+treatment\s+of\s+cancer"]},

    # ---------------- function / disability, patient-reported (surgery-specific) ----------------
    {"canonical": "Oswestry Disability Index (ODI)", "is_pro": True, "endorsed": False,
     "patterns": [r"oswestry", r"\bODI\b"]},
    {"canonical": "Roland-Morris Disability Questionnaire (RMDQ)", "is_pro": True, "endorsed": False,
     "patterns": [r"roland[-\s]morris", r"\bRMDQ\b", r"\bRDQ\b"]},
    {"canonical": "WOMAC", "is_pro": True, "endorsed": False,
     "patterns": [r"\bWOMAC\b", r"western\s+ontario\s+and\s+mcmaster",
                  r"mcmaster\s+universities\s+osteoarthritis\s+index"]},
    {"canonical": "KOOS / HOOS", "is_pro": True, "endorsed": False,
     "patterns": [r"\bKOOS\b", r"\bHOOS\b", r"knee\s+injury\s+and\s+osteoarthritis\s+outcome",
                  r"hip\s+disability\s+and\s+osteoarthritis\s+outcome", r"osteoarthritis\s+outcome\s+score"]},
    {"canonical": "DASH / QuickDASH", "is_pro": True, "endorsed": False,
     "patterns": [r"\bquick-?\s?DASH\b", r"\bDASH\b", r"disabilities\s+of\s+the\s+arm,?\s+shoulder"]},
    {"canonical": "Oxford Knee/Hip Score (OKS/OHS)", "is_pro": True, "endorsed": False,
     "patterns": [r"oxford\s+knee\s+score", r"oxford\s+hip\s+score", r"\bOKS\b", r"\bOHS\b"]},
    {"canonical": "ASES (Amer. Shoulder & Elbow Surgeons)", "is_pro": True, "endorsed": True,
     "patterns": [r"american\s+shoulder\s+and\s+elbow\s+surgeons", r"\bASES\b"]},
    {"canonical": "Constant-Murley score", "is_pro": False, "endorsed": False,
     "patterns": [r"constant[-\s]murley", r"constant\s+score"]},
    {"canonical": "Lysholm score", "is_pro": True, "endorsed": False,
     "patterns": [r"lysholm"]},
    {"canonical": "Harris Hip Score (HHS)", "is_pro": False, "endorsed": False,
     "patterns": [r"harris\s+hip\s+score", r"\bHHS\b"]},
    {"canonical": "Knee Society Score (KSS)", "is_pro": False, "endorsed": False,
     "patterns": [r"knee\s+society\s+score", r"\bKSS\b"]},
    {"canonical": "SANE (Single Assessment Numeric Eval.)", "is_pro": True, "endorsed": False,
     "patterns": [r"single\s+assessment\s+numeric\s+evaluation", r"\bSANE\b"]},

    # ---------------- psych / sleep / global / other PRO ----------------
    {"canonical": "Hospital Anxiety & Depression Scale (HADS)", "is_pro": True, "endorsed": False,
     "patterns": [r"hospital\s+anxiety\s+and\s+depression", r"\bHADS\b"]},
    {"canonical": "State-Trait Anxiety Inventory (STAI)", "is_pro": True, "endorsed": False,
     "patterns": [r"state[-\s]trait\s+anxiety", r"state\s+anxiety\s+inventory", r"\bSTAI\b"]},
    {"canonical": "Patient Health Questionnaire (PHQ)", "is_pro": True, "endorsed": False,
     "patterns": [r"patient\s+health\s+questionnaire", r"\bPHQ-?\d*\b"]},
    {"canonical": "GAD-7 (anxiety)", "is_pro": True, "endorsed": False,
     "patterns": [r"generali[sz]ed\s+anxiety\s+disorder", r"\bGAD-?7\b"]},
    {"canonical": "Beck Depression Inventory (BDI)", "is_pro": True, "endorsed": False,
     "patterns": [r"beck\s+depression\s+inventory", r"\bBDI(?:-II)?\b"]},
    {"canonical": "Pittsburgh Sleep Quality Index (PSQI)", "is_pro": True, "endorsed": False,
     "patterns": [r"pittsburgh\s+sleep\s+quality", r"\bPSQI\b"]},
    {"canonical": "Insomnia Severity Index (ISI)", "is_pro": True, "endorsed": False,
     "patterns": [r"insomnia\s+severity\s+index", r"\bISI\b"]},
    {"canonical": "Richards-Campbell Sleep Questionnaire (RCSQ)", "is_pro": True, "endorsed": False,
     "patterns": [r"richards[-\s]campbell", r"\bRCSQ\b"]},
    {"canonical": "Tampa Scale of Kinesiophobia (TSK)", "is_pro": True, "endorsed": False,
     "patterns": [r"tampa\s+scale", r"kinesiophobia", r"\bTSK\b"]},
    {"canonical": "APAIS (Amsterdam Preop Anxiety & Info Scale)", "is_pro": True, "endorsed": False,
     "patterns": [r"amsterdam\s+preoperative\s+anxiety", r"\bAPAIS\b"]},
    {"canonical": "Yale Preoperative Anxiety Scale (mYPAS)", "is_pro": False, "endorsed": False,
     "patterns": [r"yale\s+preoperative\s+anxiety", r"\bm?YPAS\b"]},
    {"canonical": "Patient Global Impression of Change (PGIC)", "is_pro": True, "endorsed": False,
     "patterns": [r"patient\s+global\s+impression", r"\bPGIC\b", r"\bPGI-?C\b"]},
    {"canonical": "Overall Benefit of Analgesia Score (OBAS)", "is_pro": True, "endorsed": False,
     "patterns": [r"overall\s+benefit\s+of\s+analgesia", r"\bOBAS\b"]},
    {"canonical": "Opioid-Related Symptom Distress Scale (ORSDS)", "is_pro": True, "endorsed": True,
     "patterns": [r"opioid[-\s]related\s+symptom\s+distress", r"\bORSDS\b", r"\bOR-?SDS\b"]},
    {"canonical": "APS-POQ-R (Amer. Pain Society Patient Outcome Q.)", "is_pro": True, "endorsed": False,
     "patterns": [r"american\s+pain\s+society\s+patient\s+outcome", r"\bAPS-?POQ(?:-R)?\b"]},
    {"canonical": "Oral Health Impact Profile (OHIP-14)", "is_pro": True, "endorsed": False,
     "patterns": [r"oral\s+health\s+impact\s+profile", r"\bOHIP-?\d*\b"]},
    {"canonical": "POSAS (Patient & Observer Scar Assessment)", "is_pro": True, "endorsed": False,
     "patterns": [r"patient\s+and\s+observer\s+scar\s+assessment", r"\bPOSAS\b",
                  r"observer\s+scar\s+assessment\s+scale"]},

    # ---------------- sedation, observer-reported (is_pro False) ----------------
    {"canonical": "Ramsay Sedation Scale (RSS)", "is_pro": False, "endorsed": False,
     "patterns": [r"ramsay\s+sedation\s+(?:scale|score)", r"ramsay", r"\bRSS\b"]},
    {"canonical": "Richmond Agitation-Sedation Scale (RASS)", "is_pro": False, "endorsed": False,
     "patterns": [r"richmond\s+agitation[-\s]sedation", r"\bRASS\b"]},
]

# --------------------------------------------------------------------------
# CURATION PROVENANCE — (canonical, [fragments/spellings merged in], unsure note)
# Printed by __main__. Not read by the detection engine.
# --------------------------------------------------------------------------
CURATION = [
    ("Visual Analog Scale (VAS)", ["VAS", "Visual Analog/Analogue Scale", "Visual Analog Pain Scale/Score",
        "Visual Analogic Scale", "Visual Analogue Pain Scale", "EVA (Spanish)"],
        "EVA (Escala Visual Analogica) added for Spanish-language trials — \\bEVA\\b could in principle hit the name 'Eva'; low risk in outcome text."),
    ("Numeric Rating Scale (NRS)", ["NRS", "NPRS", "Numeric/Numerical (Pain) Rating Scale", "VNRS", "NRSr", "NRSm"],
        "VNRS folded into NRS (verbal-numeric variant)."),
    ("Verbal Rating Scale (VRS)", ["VRS", "Verbal Rating/Descriptor Scale"], ""),
    ("Faces Pain Scale / Wong-Baker (FPS)", ["FACES", "FPS", "FPS-R", "Wong-Baker"],
        "\\bFACES\\b assumed to be the faces pain scale in this cohort."),
    ("FLACC scale", ["FLACC"], "Observer-reported -> is_pro=False."),
    ("CHEOPS", ["CHEOPS", "Eastern Ontario Pain Scale"], "Observer-reported pediatric scale -> is_pro=False."),
    ("CPOT", ["CPOT"], "Observer-reported -> is_pro=False."),
    ("Behavioral Pain Scale (BPS)", ["BPS", "Behavioral/Behavioural Pain Scale"], "Observer-reported -> is_pro=False."),
    ("PPPM", ["PPPM"], "Parent-proxy report -> is_pro=False."),
    ("Brief Pain Inventory (BPI)", ["BPI", "BPI-SF"], ""),
    ("McGill Pain Questionnaire (MPQ)", ["MPQ", "SF-MPQ", "Pain Rating Index / PRI"],
        "PRI (Pain Rating Index) merged as an MPQ component; \\bPRI\\b is a low-frequency risk token."),
    ("Pain Catastrophizing Scale (PCS)", ["PCS"], "\\bPCS\\b can also mean SF-36 Physical Component Summary — in this cohort PCS is overwhelmingly Pain Catastrophizing; flag for validation."),
    ("Neuropathic Pain Scale (NPS)", ["NPS"], "\\bNPS\\b could rarely be 'Net Promoter Score'; pain context assumed."),
    ("Central Sensitization Inventory (CSI)", ["CSI"], ""),
    ("Pain Disability Index (PDI)", ["PDI"], ""),
    ("painDETECT", ["painDETECT", "PD-Q"], ""),
    ("DN4", ["DN4"], "Has a clinician-exam component; kept is_pro=True as a screening PRO — flag."),
    ("LANSS", ["LANSS"], "Has a clinician-exam component; flag."),
    ("Neuropathic Pain Symptom Inventory (NPSI)", ["NPSI"], ""),
    ("SPID / TOTPAR / PID / SPRID", ["SPID", "SPID6/12/24/48", "SPIDs", "TOTPAR", "SPRID", "PRID", "PID"],
        "PRO-DERIVED summary endpoints, NOT instruments themselves -> is_pro=False (the underlying VAS/NRS is counted on its own line; this must not double-credit a trial's PRO-ness). Still detected for record-keeping. Dropped bare \\bPAR\\b (too generic). \\bPID\\b could rarely mean pelvic inflammatory disease — flag."),
    ("Quality of Recovery (QoR-15/40)", ["QoR", "QoR-15", "QoR-40"], "Bare 'QoR' fragment merged in."),
    ("EQ-5D", ["EQ-5D", "EQ-5D-3L/5L", "EuroQol"], ""),
    ("Short Form Health Survey", ["SF-36", "SF-12", "SF-8", "VR-12", "RAND-36", "Health Survey"],
        "Dropped bare \\bRAND\\b (kept RAND-36). 'Health Survey' fragment covered by full pattern."),
    ("PROMIS", ["PROMIS"], "Umbrella family (Pain Interference, Physical Function, etc.); not split by domain in this draft."),
    ("WHOQOL", ["WHOQOL", "WHOQOL-BREF", "World Health Organization Quality of Life"],
        "Added spelled-out name for robustness. Did not add bare 'BREF' token (too risky)."),
    ("EORTC QLQ-C30", ["EORTC", "QLQ-C30", "European Organisation for Research and Treatment of Cancer"],
        "Added spelled-out name for robustness."),
    ("Oswestry Disability Index (ODI)", ["Oswestry", "ODI"], ""),
    ("Roland-Morris Disability Questionnaire (RMDQ)", ["RMDQ", "RDQ", "Roland-Morris"], ""),
    ("WOMAC", ["WOMAC", "McMaster Universities Osteoarthritis Index"], ""),
    ("KOOS / HOOS", ["KOOS", "HOOS", "Osteoarthritis Outcome Score"], "KOOS and HOOS grouped; split later if a surgery-type breakdown is needed."),
    ("DASH / QuickDASH", ["DASH", "QuickDASH"], ""),
    ("Oxford Knee/Hip Score (OKS/OHS)", ["OKS", "OHS"], ""),
    ("ASES", ["ASES", "American Shoulder and Elbow Surgeons"], "Has clinician-scored portion historically; kept is_pro=True (patient-reported section) — flag. endorsed=True per config 'ASES IMI PROMPT adaptation' (# VERIFY)."),
    ("Constant-Murley score", ["Constant-Murley", "Constant score"], "Mixed clinician+patient+objective -> is_pro=False (conservative); flag."),
    ("Lysholm score", ["Lysholm"], ""),
    ("Harris Hip Score (HHS)", ["HHS", "Harris Hip Score"], "Clinician-administered -> is_pro=False; flag."),
    ("Knee Society Score (KSS)", ["KSS", "Knee Society Score"], "Clinician+objective (modern versions add patient part) -> is_pro=False; flag."),
    ("SANE", ["SANE", "Single Assessment Numeric Evaluation"], "\\bSANE\\b also an English word; low risk in outcome text — flag."),
    ("Hospital Anxiety & Depression Scale (HADS)", ["HADS", "Hospital Anxiety and Depression"],
        "Bare fragments 'Depression Scale' (n=67) NOT merged — ambiguous with BDI/CES-D/others; only full name + HADS matched."),
    ("State-Trait Anxiety Inventory (STAI)", ["STAI", "State Anxiety Inventory"], ""),
    ("Patient Health Questionnaire (PHQ)", ["PHQ", "PHQ-9", "PHQ-8"], "Bare 'Health Questionnaire' fragment not merged (ambiguous)."),
    ("GAD-7", ["GAD-7", "Generalized Anxiety Disorder"], ""),
    ("Beck Depression Inventory (BDI)", ["BDI", "BDI-II"], ""),
    ("Pittsburgh Sleep Quality Index (PSQI)", ["PSQI"], ""),
    ("Insomnia Severity Index (ISI)", ["ISI"], ""),
    ("Richards-Campbell Sleep Questionnaire (RCSQ)", ["RCSQ", "Richards-Campbell"], ""),
    ("Tampa Scale of Kinesiophobia (TSK)", ["TSK", "Tampa Scale", "kinesiophobia"], ""),
    ("APAIS", ["APAIS", "Amsterdam Preoperative Anxiety", "Information Scale"], "'Information Scale' fragment covered by full name."),
    ("Yale Preoperative Anxiety Scale (mYPAS)", ["YPAS", "mYPAS", "Yale Preoperative Anxiety"], "Observer-rated -> is_pro=False."),
    ("Patient Global Impression of Change (PGIC)", ["PGIC", "PGI-C"], ""),
    ("Overall Benefit of Analgesia Score (OBAS)", ["OBAS"], ""),
    ("Opioid-Related Symptom Distress Scale (ORSDS)", ["ORSDS", "OR-SDS"],
        "endorsed=True per config 'OR-SDS IMI PROMPT adaptation' (# VERIFY)."),
    ("APS-POQ-R", ["APS-POQ-R", "American Pain Society Patient Outcome Questionnaire"], ""),
    ("Oral Health Impact Profile (OHIP-14)", ["OHIP-14", "Oral Health Impact Profile"], ""),
    ("POSAS", ["POSAS", "Observer Scar Assessment Scale", "Patient and Observer Scar Assessment"],
        "Has patient + observer components -> is_pro=True (patient part); flag."),
    ("Ramsay Sedation Scale (RSS)", ["Ramsay Sedation Scale/Score", "RSS"], "Observer-reported -> is_pro=False."),
    ("Richmond Agitation-Sedation Scale (RASS)", ["RASS"], "Observer-reported -> is_pro=False."),
]

# Candidates deliberately DISCARDED as non-instruments (for the record):
DISCARDED = {
    "lab/biomarker": ["CRP", "ESR", "IL-6/8/10/2", "TNF-a", "WBC", "NLR", "PLR", "MMP-9", "COX-2", "DNA", "CFU(s)", "ELISA", "PCR", "ABG"],
    "pharmacokinetics/units": ["AUC", "AUC0-72", "AUC0-t", "Cmax", "Tmax", "MME(s)", "MED", "MEDD", "HCl", "mg/kg"],
    "physiologic/vitals/imaging": ["MAP", "MBP", "HR", "BP", "SpO2", "EtCO2", "HRV", "ANI", "NOL", "fMRI", "CBCT", "FEV1", "FVC", "PEF", "MEP", "MVIC"],
    "care-setting/adverse/regulatory": ["PACU", "ICU", "POD1/2/3", "AEs", "SAEs", "TEAEs", "CTCAE", "CDC", "FDA", "LOS"],
    "interventions/blocks/routes": ["PCA", "IV-PCA", "TENS", "TAP", "ESPB", "PENG", "QLB", "PECS", "NSAID(s)"],
    "conditions/constructs": ["CPSP", "PPSP", "PLP (phantom limb pain)", "POCD", "POI", "ADL"],
    "performance/quant-sensory (non-PRO)": ["QST", "CPM", "PPT", "TUG", "MRC", "PPI"],
    "cognitive/delirium (off-topic)": ["MMSE", "MoCA", "CAM", "CAM-ICU", "PAED"],
    "generic/fragments/noise": ["PAIN", "SCALE", "WORST", "Likert Scale", "Pain Score", "Analgesia Score",
        "Information Scale", "Depression Scale", "Health Questionnaire", "II", "III", "LAST", "YES", "AND", "USA", "WHO"],
    "usability/other (out of scope)": ["SUS / System Usability Scale", "PGA (physician/patient global — ambiguous)", "Aldrete Score", "Bromage Scale"],
}


def _lookup(canon):
    """Tolerant match: CURATION keys may use a short form of the INSTRUMENTS
    canonical (which carries a parenthetical gloss), so match on shared prefix."""
    for i in INSTRUMENTS:
        c = i["canonical"]
        if c == canon or c.startswith(canon) or canon.startswith(c) or canon.split(" (")[0] == c.split(" (")[0]:
            return i
    return None


def _print_table():
    print(f"FROZEN dictionary v1 — {len(INSTRUMENTS)} instruments "
          f"({sum(i['is_pro'] for i in INSTRUMENTS)} is_pro=True, "
          f"{sum(not i['is_pro'] for i in INSTRUMENTS)} is_pro=False; "
          f"{sum(i['endorsed'] for i in INSTRUMENTS)} endorsed=True).\n")
    for canon, frags, unsure in CURATION:
        inst = _lookup(canon)
        pro = inst["is_pro"] if inst else "?"
        print(f"• {canon}   [is_pro={pro}]")
        print(f"    merged: {', '.join(frags)}")
        if unsure:
            print(f"    UNSURE: {unsure}")
    print("\nDISCARDED as non-instruments:")
    for cat, items in DISCARDED.items():
        print(f"  [{cat}] {', '.join(items)}")


if __name__ == "__main__":
    _print_table()
