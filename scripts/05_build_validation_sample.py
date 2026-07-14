#!/usr/bin/env python3
"""
scripts/05_build_validation_sample.py  —  Build the detection-validation sample.

The sample is EXACTLY one reproducible random draw of validation.random_sample_n trials
(using validation.random_seed) from the screened cohort — nothing added. There is no
endorsed-census or variant-scan stratum and no union with any other trials. (Any
endorsed_census / variant_scan_terms config fields are left in place but ignored.)

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
    ws.append(["Number","NCT","Trial Title","Outcome Text","Reviewer Classification","Notes / Flags"])
    for c in ws[1]: c.font = Font(bold=True)
    for r in rows: ws.append([r["n"], r["nct"], r["title"], r["text"], "", ""])
    return wb

def main():
    log_lines = []
    cfg = yaml.safe_load(CONFIG.read_text())
    vc = cfg["validation"]
    N = vc["random_sample_n"]; seed = vc["random_seed"]
    dict_path = ROOT / cfg["dictionary"]["operative_file"]

    screened = {r["nct_id"]: r for r in load_csv(SCREENED)}
    detection = {r["nct_id"]: r for r in load_csv(DETECT)}
    all_ids = sorted(screened)
    log_print(f"Loaded {len(screened)} screened, {len(detection)} detection rows", log_lines)

    # EXACTLY one reproducible random draw of N trials — no other strata, no unions.
    if N > len(all_ids): raise ValueError(f"random_sample_n={N} exceeds cohort {len(all_ids)}")
    random.seed(seed); ids = sorted(random.sample(all_ids, N))
    log_print(f"RANDOM_{N}: {len(ids)} trials (seed={seed}) — single random sample, no other strata", log_lines)

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
    kws.append(["Number","NCT","Trial Title","Outcome Text","Algo: Has Named PRO",
                "Algo: Uses Endorsed","Matched","Matched PRO","Matched Endorsed"])
    for c in kws[1]: c.font = Font(bold=True)
    for n, i in enumerate(ids, 1):
        sr, dr = screened[i], detection.get(i, {})
        txt = outcome_text(sr)
        review_rows.append({"n":n,"nct":i,"title":sr.get("brief_title",""),"text":txt})
        kws.append([n, i, sr.get("brief_title",""), txt, dr.get("has_any_named_pro",""),
                    dr.get("uses_endorsed",""), dr.get("matched_instruments",""),
                    dr.get("matched_is_pro_instruments",""), dr.get("matched_endorsed_instruments","")])

    blinded_sheet(review_rows).save(REV1)
    blinded_sheet(review_rows).save(REV2)
    key_wb.save(KEY)
    log_print(f"Wrote {REV1.name} and {REV2.name} (blinded) and {KEY.name} (lead-only)", log_lines)

    pro = write_recog(load_instruments(dict_path), dict_path)
    log_print(f"Wrote config/recognition_list.md ({pro} is_pro instruments)", log_lines)

    n = dlog(f"Built detection-validation sample (`scripts/05_build_validation_sample.py`). "
             f"Single random sample of {N} trials (seed={seed}) over the {len(all_ids)}-trial cohort — "
             f"no endorsed-census or variant-scan strata. Two blinded reviewer files + lead KEY + "
             f"recognition_list.md written.")
    log_print(f"Appended DECISION_LOG.md Entry #{n}", log_lines)

    write_log(log_lines)

if __name__ == "__main__": main()
