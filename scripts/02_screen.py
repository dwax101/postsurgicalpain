#!/usr/bin/env python3
"""
scripts/02_screen.py  —  Screening (config-driven).

Reads data/raw_export.csv and applies screening rules, appending KEEP/DROP
columns rather than deleting, so every drop stays auditable.

Rule 1 (all topics): keep only INTERVENTIONAL studies — re-checks the retrieval
filter independently.

Rules 2 & 3 (STANDARD topics only, when retrieval.mode == bins): a condition-field
regex from bin-1 and a title inclusion/exclusion screen from bin-2/bin-3, read from
config/bins.yaml. For OBESITY (retrieval.mode == expert_strings) these are skipped —
the expert strings already scoped condition + intervention, so screening is the
interventional re-check only.

Writes data/screened_flagged.csv (all rows + decision/reason) and
data/screened_kept.csv (KEEP rows only).
"""
import csv, re, yaml
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "topic_config.yaml"
INP = ROOT / "data" / "raw_export.csv"
FLAG = ROOT / "data" / "screened_flagged.csv"
KEPT = ROOT / "data" / "screened_kept.csv"
LOG = ROOT / "qc_logs" / "02_screen.log"
DLOG = ROOT / "DECISION_LOG.md"


def logp(l, b): print(l); b.append(l)

def dlog(body):
    t = DLOG.read_text(); nums=[int(n) for n in re.findall(r"^## Entry #(\d+)", t, re.MULTILINE)]
    nxt=max(nums,default=0)+1
    with DLOG.open("a") as f: f.write(f"\n## Entry #{nxt} — {date.today().isoformat()}\n{body}\n")
    return nxt

def main():
    cfg = yaml.safe_load(CONFIG.read_text())
    mode = cfg["retrieval"]["mode"]
    use_bins = (mode == "bins")
    # Bin-1 (condition variants) and bin-2 (title inclusion) are handled in the
    # RETRIEVAL search (search.txt), not here — a trial is pulled if its condition
    # matches root/bin-1 OR its title matches bin-2. So screening does NOT re-check
    # those. The ONLY screen is bin-3: remove trials whose title matches an exclusion
    # term. Bin-3 lives in the main config under screening.title_exclude.
    t_exc = []
    if use_bins:
        t_exc = (cfg.get("screening", {}) or {}).get("title_exclude", []) or []

    buf = []
    with INP.open(newline="") as f:
        rdr = csv.DictReader(f); raw_fields = rdr.fieldnames; rows = list(rdr)
    logp(f"Loaded {len(rows)} rows from data/raw_export.csv", buf)
    logp(f"Retrieval mode: {mode} | bin-3 title exclusion terms: {len(t_exc)}", buf)

    d1 = d3 = 0; kept = []; flagged = []
    exc_rx = [re.compile(re.escape(t), re.IGNORECASE) for t in t_exc]

    for r in rows:
        decision, reason = "KEEP", ""
        if r.get("study_type","") != "INTERVENTIONAL":
            decision, reason, d1 = "DROP", f"Rule 1: study_type={r.get('study_type','')!r}", d1+1
        elif use_bins and exc_rx:
            title = r.get("brief_title","")
            if any(rx.search(title) for rx in exc_rx):
                decision, reason, d3 = "DROP", "Rule 2: bin-3 title exclusion", d3+1
        if decision == "KEEP": kept.append(r)
        fr = {"screen_decision": decision, "screen_reason": reason}; fr.update(r); flagged.append(fr)

    FLAG.parent.mkdir(parents=True, exist_ok=True)
    with FLAG.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["screen_decision","screen_reason"]+raw_fields); w.writeheader(); w.writerows(flagged)
    with KEPT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=raw_fields); w.writeheader(); w.writerows(kept)

    logp(f"Dropped Rule 1 (non-interventional): {d1}", buf)
    if use_bins:
        logp(f"Dropped Rule 2 (bin-3 title exclusion): {d3}", buf)
    logp(f"Final kept: {len(kept)}", buf)
    LOG.parent.mkdir(parents=True, exist_ok=True); LOG.write_text("\n".join(buf)+"\n")
    n = dlog(f"Screening (`scripts/02_screen.py`, mode={mode}). Loaded {len(rows)}; dropped "
             f"{d1} non-interventional" + (f", {d3} bin-3 title exclusion" if use_bins else "") +
             f"; final kept {len(kept)} to `data/screened_kept.csv`.")
    print(f"Appended DECISION_LOG.md Entry #{n}")

if __name__ == "__main__": main()
