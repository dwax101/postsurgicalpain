#!/usr/bin/env python3
"""
scripts/05_build_validation_sample.py  —  Build the detection-validation sample.

Config-driven, three strata (from config.validation):
  RANDOM_N           — reproducible random sample (validation.random_sample_n, seed).
  ENDORSED_CENSUS    — every trial the algorithm flagged uses_endorsed=True, no cap
                       (critical when the endorsed set is rare, e.g. BODY-Q).
  VARIANT_SCAN       — trials whose raw text contains an endorsed-instrument spelling
                       variant (validation.variant_scan_terms) NOT already flagged —
                       candidate missed endorsed detections.

Emits TWO blinded reviewer copies (reviewer1/reviewer2) — the v1 bug was a single
shared file — plus a lead-only KEY with the algorithm's answers, and a
recognition_list.md generated from the operative dictionary so reviewers and the
algorithm share identical instrument info.
"""
import csv, json, importlib.util, random, re, yaml
from datetime import date
from pathlib import Path
import openpyxl
from openpyxl.styles import Font

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "topic_config.yaml"
SCREENED = ROOT / "data" / "screened_kept.csv"
DETECT = ROOT / "data" / "detection_results.csv"
REV1 = ROOT / "validation_sample_REVIEW_reviewer1.xlsx"
REV2 = ROOT / "validation_sample_REVIEW_reviewer2.xlsx"
KEY = ROOT / "validation_sample_KEY.xlsx"
RECOG = ROOT / "config" / "recognition_list.md"
DLOG = ROOT / "DECISION_LOG.md"
LOG = ROOT / "qc_logs" / "05_build_validation_sample.log"


def log_print(line, log_lines):
    print(line); log_lines.append(line)

def write_log(log_lines):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text("\n".join(log_lines) + "\n")

def load_csv(p):
    with p.open(newline="") as f: return list(csv.DictReader(f))

def load_instruments(p):
    spec = importlib.util.spec_from_file_location("d", p); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m.INSTRUMENTS

def outcome_text(row):
    chunks = []
    for c in ("primary_outcomes","secondary_outcomes"):
        for o in json.loads(row.get(c,"") or "[]"):
            chunks.append(f"{o.get('measure','')} {o.get('description','')}")
    return " ".join(chunks)

def write_recog(instruments, dict_path):
    pro = [i for i in instruments if i.get("is_pro")]
    lines = ["# PRO Instrument Recognition List","",
             f"Generated from `{dict_path.name}`. Classify using ONLY what is listed here. "
             "Do not count an instrument not on this list; do not open the dictionary source.",""]
    for i in pro:
        lines.append(f"## {i['canonical']}" + (" *(endorsed)*" if i.get("endorsed") else ""))
        for p in i["patterns"]: lines.append(f"- `{p}`")
        lines.append("")
    RECOG.write_text("\n".join(lines)); return len(pro)

def dlog(body):
    t = DLOG.read_text(); nums=[int(n) for n in re.findall(r"^## Entry #(\d+)", t, re.MULTILINE)]
    nxt=max(nums,default=0)+1
    with DLOG.open("a") as f: f.write(f"\n## Entry #{nxt} — {date.today().isoformat()}\n{body}\n")
    return nxt

def blinded_sheet(rows):
    wb = openpyxl.Workbook(); ws = wb.active; ws.title="Review"
    ws.append(["Number","NCT","Trial Title","Outcome Text","Stratum","Reviewer Classification","Notes / Flags"])
    for c in ws[1]: c.font = Font(bold=True)
    for r in rows: ws.append([r["n"], r["nct"], r["title"], r["text"], r["stratum"], "", ""])
    return wb

def main():
    log_lines = []
    cfg = yaml.safe_load(CONFIG.read_text())
    vc = cfg["validation"]
    N = vc["random_sample_n"]; seed = vc["random_seed"]
    census_on = bool(vc.get("endorsed_census", True))
    variants = vc.get("variant_scan_terms", [])
    dict_path = ROOT / cfg["dictionary"]["operative_file"]

    screened = {r["nct_id"]: r for r in load_csv(SCREENED)}
    detection = {r["nct_id"]: r for r in load_csv(DETECT)}
    all_ids = sorted(screened)
    log_print(f"Loaded {len(screened)} screened, {len(detection)} detection rows", log_lines)

    if N > len(all_ids): raise ValueError(f"random_sample_n={N} exceeds cohort {len(all_ids)}")
    random.seed(seed); rand = set(random.sample(all_ids, N))
    log_print(f"RANDOM_{N}: {len(rand)} (seed={seed})", log_lines)

    census = set()
    if census_on:
        census = {i for i in all_ids if detection.get(i,{}).get("uses_endorsed")=="True"}
    log_print(f"ENDORSED_CENSUS: {len(census)}", log_lines)

    vpat = [re.compile(re.escape(v), re.IGNORECASE) for v in variants]
    vscan = {}
    for i in all_ids:
        if i in census: continue
        txt = outcome_text(screened[i])
        hits = [v for v, rx in zip(variants, vpat) if rx.search(txt)]
        if hits: vscan[i] = hits
    log_print(f"VARIANT_SCAN: {len(vscan)}", log_lines)

    strata = {}
    for i in rand: strata.setdefault(i, []).append(f"RANDOM_{N}")
    for i in census: strata.setdefault(i, []).append("ENDORSED_CENSUS")
    for i in vscan: strata.setdefault(i, []).append("VARIANT_SCAN")
    ids = sorted(strata)
    overlap = sum(1 for v in strata.values() if len(v) > 1)
    log_print(f"Combined unique: {len(ids)} ({overlap} in >1 stratum)", log_lines)

    # Safe re-run guard: never clobber reviewer work already in progress. If either
    # blinded reviewer file exists, PRESERVE all existing sample files (reviewer copies,
    # KEY, recognition_list.md); write only the qc log (with the summary computed above)
    # and exit — do not regenerate files or append a DECISION_LOG entry.
    if REV1.exists() or REV2.exists():
        existing = ", ".join(p.name for p in (REV1, REV2, KEY) if p.exists())
        log_print(f"Reviewer file(s) already exist ({existing}) — PRESERVING existing sample "
                  f"files; NOT regenerating. Writing qc log only.", log_lines)
        write_log(log_lines)
        print(f"Wrote {LOG.relative_to(ROOT)} (existing reviewer files preserved)")
        return

    review_rows, key_wb = [], openpyxl.Workbook()
    kws = key_wb.active; kws.title = "Key"
    kws.append(["Number","NCT","Trial Title","Outcome Text","Stratum","Algo: Has Named PRO",
                "Algo: Uses Endorsed","Matched","Matched PRO","Matched Endorsed","Variant(s) Found"])
    for c in kws[1]: c.font = Font(bold=True)
    for n, i in enumerate(ids, 1):
        sr, dr = screened[i], detection.get(i, {})
        txt = outcome_text(sr); strat = "|".join(strata[i])
        review_rows.append({"n":n,"nct":i,"title":sr.get("brief_title",""),"text":txt,"stratum":strat})
        kws.append([n, i, sr.get("brief_title",""), txt, strat, dr.get("has_any_named_pro",""),
                    dr.get("uses_endorsed",""), dr.get("matched_instruments",""),
                    dr.get("matched_is_pro_instruments",""), dr.get("matched_endorsed_instruments",""),
                    ", ".join(vscan.get(i, []))])

    blinded_sheet(review_rows).save(REV1)
    blinded_sheet(review_rows).save(REV2)
    key_wb.save(KEY)
    log_print(f"Wrote {REV1.name} and {REV2.name} (blinded) and {KEY.name} (lead-only)", log_lines)

    pro = write_recog(load_instruments(dict_path), dict_path)
    log_print(f"Wrote config/recognition_list.md ({pro} is_pro instruments)", log_lines)

    n = dlog(f"Built detection-validation sample (`scripts/05_build_validation_sample.py`). Strata over "
             f"{len(all_ids)}-trial cohort: RANDOM_{N} (seed={seed}), ENDORSED_CENSUS ({len(census)}), "
             f"VARIANT_SCAN ({len(vscan)}). Combined {len(ids)} unique ({overlap} multi-stratum). "
             f"Two blinded reviewer files + lead KEY + recognition_list.md written.")
    log_print(f"Appended DECISION_LOG.md Entry #{n}", log_lines)

    write_log(log_lines)

if __name__ == "__main__": main()
