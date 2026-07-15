#!/usr/bin/env python3
"""
scripts/06_validation_stats.py  —  Detection-validation statistics.

RUN ONLY AFTER both reviewers have completed their files. Reads the two completed
reviewer workbooks and the lead KEY, then computes:
  - percent agreement and Cohen's kappa between the two reviewers
  - percent agreement between each reviewer and the algorithm
  - false-negative rate (reviewer marked a named PRO the algorithm missed)
  - dictionary-leakage: every "(unlisted)" flag reviewers wrote, listed
Writes the results into VALIDATION.md (reviewer + match columns) and logs an entry.

Reviewer files expected at repo root (from scripts/05):
  validation_sample_REVIEW_reviewer1.xlsx
  validation_sample_REVIEW_reviewer2.xlsx   (each with a filled "Reviewer Classification")
"""
import re, yaml
from datetime import date
from pathlib import Path
import openpyxl

ROOT = Path(__file__).resolve().parent.parent
REV1 = ROOT / "validation_sample_REVIEW_reviewer1.xlsx"
REV2 = ROOT / "validation_sample_REVIEW_reviewer2.xlsx"
KEY = ROOT / "validation_sample_KEY.xlsx"
VALID = ROOT / "VALIDATION.md"
DLOG = ROOT / "DECISION_LOG.md"

PRO_LABEL = "Named PRO"   # the label that means "a named PRO is present"


def read_reviewer(path):
    wb = openpyxl.load_workbook(path); ws = wb.active
    header = [c.value for c in ws[1]]
    ci = {h: i for i, h in enumerate(header)}
    out = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        nct = row[ci["NCT"]]
        if nct is None: continue
        out[nct] = {"cls": (row[ci["Reviewer Classification"]] or "").strip(),
                    "notes": (row[ci["Notes / Flags"]] or "").strip()}
    return out

def read_key(path):
    wb = openpyxl.load_workbook(path); ws = wb.active
    header = [c.value for c in ws[1]]; ci = {h: i for i, h in enumerate(header)}
    out = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        nct = row[ci["NCT"]]
        if nct is None: continue
        out[nct] = str(row[ci["Algo: Has Named PRO"]]).strip()  # "True"/"False"
    return out

def cohens_kappa(a, b):
    labels = sorted(set(a) | set(b))
    n = len(a); 
    if n == 0: return 0.0
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pe = sum((a.count(l)/n) * (b.count(l)/n) for l in labels)
    return (po - pe) / (1 - pe) if pe != 1 else 1.0

def dlog(body):
    t = DLOG.read_text(); nums=[int(n) for n in re.findall(r"^## Entry #(\d+)", t, re.MULTILINE)]
    nxt=max(nums,default=0)+1
    with DLOG.open("a") as f: f.write(f"\n## Entry #{nxt} — {date.today().isoformat()}\n{body}\n")
    return nxt

def main():
    for p in (REV1, REV2, KEY):
        if not p.exists():
            raise SystemExit(f"Missing {p.name}. Both reviewer files and the KEY must exist first — "
                             "this runs only AFTER the human dual-coding is done.")
    r1, r2, key = read_reviewer(REV1), read_reviewer(REV2), read_key(KEY)
    ncts = [n for n in key if n in r1 and n in r2]

    a = [r1[n]["cls"] for n in ncts]; b = [r2[n]["cls"] for n in ncts]
    pa_rr = sum(1 for x, y in zip(a, b) if x == y) / len(ncts) * 100
    kappa_rr = cohens_kappa(a, b)

    def algo_pro(n): return key[n] == "True"
    def rev_pro(cls): return cls == PRO_LABEL
    pa_r1 = sum(1 for n in ncts if rev_pro(r1[n]["cls"]) == algo_pro(n)) / len(ncts) * 100
    pa_r2 = sum(1 for n in ncts if rev_pro(r2[n]["cls"]) == algo_pro(n)) / len(ncts) * 100

    # false negatives: EITHER reviewer says PRO present but algorithm missed it
    fn = [n for n in ncts if (rev_pro(r1[n]["cls"]) or rev_pro(r2[n]["cls"])) and not algo_pro(n)]
    fn_rate = len(fn) / len(ncts) * 100

    # dictionary leakage: any "(unlisted)" note
    leaks = []
    for n in ncts:
        for rv in (r1[n], r2[n]):
            if "(unlisted)" in rv["notes"].lower():
                leaks.append((n, rv["notes"]))

    md = ["# Validation", "",
          "## Detection Validation (dual coding)", "",
          f"Sample reviewed: {len(ncts)} trials.", "",
          "| Metric | Value |", "|---|---|",
          f"| Reviewer–reviewer percent agreement | {pa_rr:.1f}% |",
          f"| Reviewer–reviewer Cohen's kappa | {kappa_rr:.3f} |",
          f"| Reviewer 1 vs algorithm agreement | {pa_r1:.1f}% |",
          f"| Reviewer 2 vs algorithm agreement | {pa_r2:.1f}% |",
          f"| False-negative rate (reviewer PRO, algo missed) | {fn_rate:.1f}% ({len(fn)}/{len(ncts)}) |",
          f"| Dictionary-leakage flags (unlisted instruments) | {len(leaks)} |", ""]
    if fn:
        md += ["**False-negative NCTs:** " + ", ".join(fn), ""]
    if leaks:
        md += ["**Dictionary-leakage flags (candidate missed instruments):**", ""]
        md += [f"- {n}: {note}" for n, note in leaks] + [""]
    VALID.write_text("\n".join(md))
    print(f"Wrote VALIDATION.md — RR agreement {pa_rr:.1f}%, kappa {kappa_rr:.3f}, "
          f"FN {fn_rate:.1f}%, leakage flags {len(leaks)}")
    n = dlog(f"Detection-validation stats (`scripts/06_validation_stats.py`). {len(ncts)} trials. "
             f"RR agreement {pa_rr:.1f}%, kappa {kappa_rr:.3f}; reviewer-vs-algo {pa_r1:.1f}%/{pa_r2:.1f}%; "
             f"false-negative {fn_rate:.1f}%; {len(leaks)} dictionary-leakage flags. Written to VALIDATION.md.")
    print(f"Appended DECISION_LOG.md Entry #{n}")

if __name__ == "__main__": main()
