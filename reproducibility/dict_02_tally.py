#!/usr/bin/env python3
"""
scripts/dict_02_tally.py  —  Dictionary discovery: tally (Stage A, step 2).

Reads data/dict_raw.csv, concatenates each trial's outcome NAME + DESCRIPTION into
one text blob, and tallies instrument mentions two ways:

  1. SEED TALLY — a proposed list of KNOWN PRO instruments for this topic (acute /
     chronic postsurgical pain), each as canonical name + abbreviation variants only.
     No generic words ('pain', 'function', 'score') are ever a seed. Counts the number
     of TRIALS mentioning each instrument (each trial counted once per instrument).

  2. OPEN-ENDED SCAN — a token / n-gram scan for instrument-SHAPED names the seed
     missed: capitalized phrases ending in Scale/Score/Index/Questionnaire/Inventory/
     Survey/Profile, and acronym-shaped tokens (VAS, QoR-15, EQ-5D, DN4, ...). Generic
     phrases and non-instrument acronyms (PACU, PONV, MME, CRP, ...) are filtered out.

Endorsement is NOT assigned to anything here — this is pure frequency discovery. All
candidates (seed + discovered) are ranked together by trial count and written to
data/dict_candidates.csv; the top of the list is printed.
"""
import csv, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IN = ROOT / "data" / "dict_raw.csv"
OUT = ROOT / "data" / "dict_candidates.csv"
csv.field_size_limit(sys.maxsize)

# --------------------------------------------------------------------------
# SEED — proposed known PRO instruments for postsurgical pain. Each entry is a
# canonical display name -> list of case-insensitive, word-boundaried patterns
# (full names + abbreviations). Abbreviations chosen to be distinctive (avoid
# 2-letter ambiguous tokens like PI / VR / SF used alone). NEVER a generic word.
# --------------------------------------------------------------------------
SEED = {
    # --- pain intensity (single-item) ---
    "Numeric Rating Scale (NRS)":            [r"numeric(?:al)? rating scale", r"numeric(?:al)? pain rating scale", r"\bNRS\b", r"\bNPRS\b"],
    "Visual Analog Scale (VAS)":             [r"visual analog(?:ue)? scale", r"visual analog(?:ue)? score", r"\bVAS\b"],
    "Verbal Rating Scale (VRS)":             [r"verbal rating scale", r"verbal descriptor scale", r"\bVRS\b"],
    "Faces Pain Scale (FPS)":                [r"faces pain scale(?:[- ]revised)?", r"wong[- ]baker", r"\bFPS(?:-R)?\b"],
    "FLACC scale":                           [r"\bFLACC\b", r"face,? legs,? activity,? cry"],
    "Defense & Veterans Pain Rating Scale":  [r"defense and veterans pain rating scale", r"\bDVPRS\b"],
    "CAPA (Clinically Aligned Pain Assess.)":[r"clinically aligned pain assessment", r"\bCAPA\b"],
    # --- analgesic PRO-derived endpoints ---
    "SPID (sum pain intensity difference)":  [r"\bSPID\b", r"sum(?:med)? of pain intensity difference"],
    "TOTPAR (total pain relief)":            [r"\bTOTPAR\b", r"total pain relief"],
    "PID / PAR (pain intensity diff/relief)":[r"\bPID\b", r"\bTOTPAR\b", r"pain intensity difference", r"pain relief score"],
    # --- multidimensional pain ---
    "Brief Pain Inventory (BPI)":            [r"brief pain inventory", r"\bBPI(?:-SF)?\b"],
    "McGill Pain Questionnaire (MPQ)":       [r"mcgill pain questionnaire", r"\bMPQ\b", r"\bSF-MPQ\b"],
    "Pain Catastrophizing Scale (PCS)":      [r"pain catastroph\w+ scale", r"\bPCS\b"],
    "Pain Disability Index (PDI)":           [r"pain disability index", r"\bPDI\b"],
    "Central Sensitization Inventory (CSI)": [r"central senssit\w+ inventory", r"central sensitization inventory", r"\bCSI\b"],
    # --- neuropathic pain ---
    "painDETECT":                            [r"pain\s?detect", r"\bPDQ\b"],
    "DN4":                                   [r"\bDN4\b", r"douleur neuropathique"],
    "LANSS":                                 [r"\bLANSS\b", r"leeds assessment of neuropathic"],
    "Neuropathic Pain Symptom Inv. (NPSI)":  [r"neuropathic pain symptom inventory", r"\bNPSI\b"],
    # --- recovery / HRQoL ---
    "Quality of Recovery (QoR-15/40)":       [r"quality of recovery", r"\bQoR-?\d+\b", r"\bQOR-?\d+\b"],
    "EQ-5D":                                 [r"\bEQ-?5D(?:-?[35]L)?\b", r"euroqol"],
    "SF-36 / SF-12 (Short Form)":            [r"\bSF-?36\b", r"\bSF-?12\b", r"\bSF-?8\b", r"\bVR-?12\b", r"short form(?:-| )?(?:36|12|health survey)"],
    "PROMIS":                                [r"\bPROMIS\b", r"patient[- ]reported outcomes measurement information"],
    "WHOQOL":                                [r"\bWHOQOL(?:-BREF)?\b"],
    # --- function / disability (surgery-specific) ---
    "Oswestry Disability Index (ODI)":       [r"oswestry", r"\bODI\b"],
    "Roland-Morris Disability Q. (RMDQ)":    [r"roland[- ]morris", r"\bRMDQ\b", r"\bRDQ\b"],
    "WOMAC":                                 [r"\bWOMAC\b", r"western ontario and mcmaster"],
    "KOOS / HOOS":                           [r"\bKOOS\b", r"\bHOOS\b", r"knee injury and osteoarthritis outcome", r"hip disability and osteoarthritis outcome"],
    "DASH / QuickDASH":                      [r"\bquick ?DASH\b", r"\bDASH\b", r"disabilities of the arm,? shoulder"],
    "Oxford Knee/Hip Score (OKS/OHS)":       [r"oxford knee score", r"oxford hip score", r"\bOKS\b", r"\bOHS\b"],
    "ASES (Shoulder & Elbow Surgeons)":      [r"american shoulder and elbow surgeons", r"\bASES\b"],
    "Constant-Murley score":                 [r"constant[- ]murley", r"constant score"],
    "Lysholm score":                         [r"lysholm"],
    "Harris Hip Score (HHS)":                [r"harris hip score", r"\bHHS\b"],
    # --- psych / sleep / global ---
    "Hospital Anxiety & Depression (HADS)":  [r"hospital anxiety and depression", r"\bHADS\b"],
    "State-Trait Anxiety Inventory (STAI)":  [r"state[- ]trait anxiety", r"\bSTAI\b"],
    "Patient Health Questionnaire (PHQ)":    [r"patient health questionnaire", r"\bPHQ-?\d*\b"],
    "GAD-7 (anxiety)":                       [r"generali[sz]ed anxiety disorder", r"\bGAD-?7\b"],
    "Pittsburgh Sleep Quality Index (PSQI)": [r"pittsburgh sleep quality", r"\bPSQI\b"],
    "Patient Global Impression (PGIC)":      [r"patient global impression", r"\bPGIC\b", r"\bPGI-?C?\b"],
    "Overall Benefit of Analgesia (OBAS)":   [r"overall benefit of analgesia", r"\bOBAS\b"],
    "Opioid-Related Symptom Distress (ORSDS)":[r"opioid[- ]related symptom distress", r"\bORSDS\b", r"\bOR-?SDS\b"],
}

SEED_COMPILED = {name: [re.compile(p, re.IGNORECASE) for p in pats] for name, pats in SEED.items()}
SEED_ALL = [rx for pats in SEED_COMPILED.values() for rx in pats]

# --------------------------------------------------------------------------
# OPEN-ENDED SCAN patterns and filters
# --------------------------------------------------------------------------
SUFFIX = r"(?:Scale|Score|Index|Questionnaire|Inventory|Survey|Profile)"
PHRASE_RX = re.compile(r"((?:[A-Z][A-Za-z0-9''\-]*\s+){1,5}" + SUFFIX + r")")
ACRO_RX = re.compile(r"\b[A-Za-z][A-Za-z0-9\-]{1,9}\b")

LEAD_STRIP = re.compile(r"^(?:the|mean|total|average|change in|change from baseline in|"
                        r"measured (?:with|by|using)(?: the)?|assessed (?:with|by|using)(?: the)?|"
                        r"modified|patient'?s?)\s+", re.IGNORECASE)

# words that, if they are the ONLY non-suffix content, make a phrase too generic to be an instrument
GENERIC = {"pain", "postoperative", "post-operative", "post", "operative", "post-op", "postop",
           "intensity", "acute", "chronic", "overall", "worst", "least", "average", "mean",
           "rest", "resting", "movement", "moving", "dynamic", "static", "activity", "cough",
           "patient", "satisfaction", "sedation", "function", "physical", "functional", "recovery",
           "comfort", "nausea", "vomiting", "quality", "life", "opioid", "analgesic", "numeric",
           "numerical", "verbal", "visual", "rating", "pain-related", "global", "composite", "total"}

# acronym-shaped tokens that are NOT PRO instruments (devices, labs, units, care settings, endpoints)
ACRO_STOP = {
    "PACU", "PONV", "PDNV", "ICU", "PICU", "NICU", "IV", "IM", "PO", "SC", "PCA", "PCEA", "PCIA",
    "TAP", "ESP", "QLB", "PECS", "ERAS", "LOS", "POD", "POM", "MME", "OME", "MEDD", "MELD",
    "CRP", "ESR", "IL", "IL-6", "TNF", "WBC", "ELISA", "PCR", "PK", "PD", "AUC", "CMAX", "TMAX",
    "MAP", "HR", "BP", "SBP", "DBP", "SPO2", "ETCO2", "RR", "BMI", "ASA", "BIS", "SPI", "SPI-",
    "TKA", "THA", "TKR", "THR", "ACL", "ORIF", "VATS", "CABG", "LSG", "RYGB", "TEP", "TAPP",
    "US", "CT", "MRI", "EEG", "ECG", "EKG", "EMG", "ROM", "CI", "SD", "SE", "SEM", "OR", "RR",
    "AE", "SAE", "TEAE", "DVT", "PE", "AKI", "SSI", "GI", "CNS", "FDA", "RCT", "ITT", "PP",
    "MG", "ML", "MCG", "KG", "MMHG", "MIN", "MG/KG", "NRS-", "VAS-", "QOL", "HRQOL", "HRQL",
    "PROM", "PROMS", "PRO", "COA", "CLINRO", "OBSRO", "MID", "MCID", "NNT", "NNH", "ABG",
    "VR", "PI", "SF", "EQ", "GAD", "PHQ",  # bare short forms handled by seed's hyphenated variants
    "POI", "PONV", "DGE", "SIRS", "PONV-", "PACU-", "TIVA", "GA", "SA", "EA", "CSE",
}


def norm_phrase(p):
    p = re.sub(r"\s+", " ", p).strip().strip(".,;:")
    prev = None
    while prev != p:
        prev = p
        p = LEAD_STRIP.sub("", p).strip()
    return p


def is_generic_phrase(p):
    words = re.split(r"\s+", p)
    core = [w for w in words[:-1] if re.sub(r"[^A-Za-z-]", "", w)]  # drop the suffix word
    if not core:
        return True
    return all(w.lower().strip("-") in GENERIC for w in core)


def acronymish(tok):
    """True if tok looks like an instrument acronym (>=2 letters, mostly uppercase),
    e.g. VAS, QoR, EQ-5D, PHQ-9, DN4, FLACC, WOMAC."""
    letters = re.sub(r"[^A-Za-z]", "", tok)
    if len(letters) < 2:
        return False
    up = sum(c.isupper() for c in letters)
    return up >= 2 and up >= len(letters) - 1  # allow at most one lowercase letter (e.g. QoR)


def matched_by_seed(text_or_token):
    return any(rx.search(text_or_token) for rx in SEED_ALL)


def main():
    rows = list(csv.DictReader(IN.open()))
    n_trials = len(rows)
    seed_hits = Counter()
    disc_hits = Counter()
    disc_display = {}  # normalized-key -> representative original

    for r in rows:
        meas = json.loads(r["outcome_measures"] or "[]")
        desc = json.loads(r["outcome_descriptions"] or "[]")
        text = "  ".join(meas) + "  " + "  ".join(desc)

        # 1) seed: one increment per instrument per trial
        for name, rxs in SEED_COMPILED.items():
            if any(rx.search(text) for rx in rxs):
                seed_hits[name] += 1

        # 2) open-ended: collect distinct candidates in this trial, then increment once each
        cands = set()
        for m in PHRASE_RX.finditer(text):
            cand = norm_phrase(m.group(1))
            if len(cand) < 6 or is_generic_phrase(cand):
                continue
            if matched_by_seed(cand):
                continue
            key = cand.lower()
            cands.add(key)
            disc_display.setdefault(key, cand)
        for tok in ACRO_RX.findall(text):
            if not acronymish(tok):
                continue
            up = tok.upper()
            if up in ACRO_STOP or matched_by_seed(tok):
                continue
            key = up
            cands.add(key)
            disc_display.setdefault(key, tok)
        for key in cands:
            disc_hits[key] += 1

    # combine into one ranked table (endorsement NOT assigned)
    combined = []
    for name, c in seed_hits.items():
        combined.append((name, "seed", c))
    for key, c in disc_hits.items():
        combined.append((disc_display[key], "discovered", c))
    combined.sort(key=lambda t: (-t[2], t[0].lower()))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rank", "candidate", "source", "n_trials", "pct_trials"])
        for i, (name, src, c) in enumerate(combined, 1):
            w.writerow([i, name, src, c, f"{100*c/n_trials:.1f}"])

    print(f"Trials scanned: {n_trials}")
    print(f"Seed instruments proposed: {len(SEED)}  |  discovered candidates: {len(disc_hits)}")
    print(f"Wrote {len(combined)} ranked candidates -> {OUT.relative_to(ROOT)}\n")
    print(f"{'rank':>4}  {'n':>5}  {'pct':>5}  source       candidate")
    for i, (name, src, c) in enumerate(combined[:40], 1):
        print(f"{i:>4}  {c:>5}  {100*c/n_trials:>4.1f}%  {src:<11}  {name}")


if __name__ == "__main__":
    main()
