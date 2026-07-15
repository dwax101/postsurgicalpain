#!/usr/bin/env python3
"""
scripts/03_reconcile.py  —  Cohort reconciliation (config-driven).

Compares the screened cohort (data/screened_kept.csv) against the hand-vetted
NCT list named in config (config/vetted_ncts.csv, column from config). Writes a
labeled report (BOTH / CODE_ONLY / VETTED_ONLY) and the overlap percentage. The
OVERLAP GATE in run_all.py reads this report and halts if overlap is below the
configured minimum — this script just produces the numbers.
"""
import csv, re, yaml
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "topic_config.yaml"
CODE = ROOT / "data" / "screened_kept.csv"
REPORT = ROOT / "data" / "reconciliation_report.csv"
LOG = ROOT / "qc_logs" / "03_reconcile.log"
DLOG = ROOT / "DECISION_LOG.md"


def logp(l, b): print(l); b.append(l)

def read_csv_rows(path):
    """Read a CSV resiliently, regardless of how it was saved.

    Excel and other tools often save CSVs as Windows-1252/Latin-1 rather than
    UTF-8, or prepend a UTF-8 byte-order mark (BOM). A plain utf-8 open() then
    dies with UnicodeDecodeError on the first stray byte (e.g. a curly quote,
    accented letter, or non-breaking space). We try the common encodings in
    order and fall back to a lossless latin-1 read so the pipeline never halts
    on an encoding quirk. 'utf-8-sig' transparently strips the Excel BOM."""
    last = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            with path.open(newline="", encoding=enc) as f:
                return list(csv.DictReader(f))
        except (UnicodeDecodeError, UnicodeError) as e:
            last = e
            continue
    # final fallback: read bytes and decode latin-1 (never fails; 1 byte -> 1 char)
    text = path.read_bytes().decode("latin-1")
    import io
    return list(csv.DictReader(io.StringIO(text)))

def load_set(path, col):
    rows = read_csv_rows(path)
    if rows and col not in rows[0]:
        # tolerate a stray BOM or whitespace on the header name
        header_map = {k.lstrip("\ufeff").strip(): k for k in rows[0].keys()}
        if col in header_map:
            col = header_map[col]
        else:
            raise KeyError(f"column {col!r} not found in {path.name}; "
                           f"available columns: {list(rows[0].keys())}")
    return {r[col].strip() for r in rows if r.get(col, "").strip()}

def dlog(body):
    t = DLOG.read_text(); nums=[int(n) for n in re.findall(r"^## Entry #(\d+)", t, re.MULTILINE)]
    nxt=max(nums,default=0)+1
    with DLOG.open("a") as f: f.write(f"\n## Entry #{nxt} — {date.today().isoformat()}\n{body}\n")
    return nxt

def main():
    cfg = yaml.safe_load(CONFIG.read_text())
    vetted_file = ROOT / cfg["reconciliation"]["vetted_ncts_file"]
    vetted_col = cfg["reconciliation"]["vetted_nct_column"]
    min_overlap = cfg["reconciliation"].get("min_overlap_pct", 90)

    buf = []
    code = load_set(CODE, "nct_id")
    vetted = load_set(vetted_file, vetted_col)
    logp(f"Code cohort:   {len(code)} NCTs (data/screened_kept.csv)", buf)
    logp(f"Vetted list:   {len(vetted)} NCTs ({vetted_file.relative_to(ROOT)}, col {vetted_col!r})\n", buf)

    both, code_only, vetted_only = code & vetted, code - vetted, vetted - code
    union = code | vetted
    overlap = len(both)/len(union)*100 if union else 0.0

    logp(f"In both:      {len(both)}", buf)
    logp(f"Code only:    {len(code_only)}", buf)
    logp(f"Vetted only:  {len(vetted_only)}", buf)
    logp(f"Overlap:      {overlap:.2f}%  (minimum required by config: {min_overlap}%)", buf)
    if overlap < min_overlap:
        logp(f"  NOTE: below the configured minimum — run_all's OVERLAP GATE will halt here.", buf)

    rows = ([{"nct_id":n,"label":"BOTH"} for n in sorted(both)] +
            [{"nct_id":n,"label":"CODE_ONLY"} for n in sorted(code_only)] +
            [{"nct_id":n,"label":"VETTED_ONLY"} for n in sorted(vetted_only)])
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["nct_id","label"]); w.writeheader(); w.writerows(rows)
    logp(f"\nWrote data/reconciliation_report.csv ({len(rows)} rows)", buf)
    LOG.parent.mkdir(parents=True, exist_ok=True); LOG.write_text("\n".join(buf)+"\n")
    n = dlog(f"Cohort reconciliation (`scripts/03_reconcile.py`). Code {len(code)} vs vetted {len(vetted)}. "
             f"Both {len(both)}, code-only {len(code_only)}, vetted-only {len(vetted_only)}. "
             f"Overlap {overlap:.2f}% (min {min_overlap}%). Report: `data/reconciliation_report.csv`.")
    print(f"Appended DECISION_LOG.md Entry #{n}")

if __name__ == "__main__": main()
