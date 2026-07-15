#!/usr/bin/env python3
"""
reproducibility/run_all.py  —  the one-command pipeline.

This is what makes the live reviewer handoff real. The Primary Analyst runs it;
the Independent Reviewer, on a fresh clone, runs the SAME command and must get the
same numbers. Every parameter is read from config/topic_config.yaml — nothing is
hardcoded per topic, so the reviewer's run and the analyst's run are driven by the
identical committed inputs.

It runs the pipeline in execution order and HALTS HARD at every gate:

    01_extract  ->  02_screen  ->  [VOLUME GATE]  ->  03_reconcile  ->  [OVERLAP GATE]
                ->  04_detect  ->  05_build_validation_sample

The two gates (cohort volume, reconciliation overlap) are go/no-go. If either
fails, the run stops and prints why — you do not silently proceed to detection on
a cohort that doesn't match what was vetted, or one too thin to analyze.

06_validation_stats is intentionally NOT run here: it requires the two completed
human-reviewer files, which do not exist until the manual dual-coding step is done.
That human step is the wall between the analyst's pipeline and the reviewer's sign-off.

Usage:
    python reproducibility/run_all.py                 # run the whole pipeline
    python reproducibility/run_all.py --from 03        # resume from a step
    python reproducibility/run_all.py --dry-run        # print the plan, run nothing
"""

import argparse
import subprocess
import sys
import csv
from pathlib import Path

import yaml
from datetime import date
import re as _re

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = REPO_ROOT / "config" / "topic_config.yaml"
QC_DIR = REPO_ROOT / "qc_logs"
DECISION_LOG_FILE = REPO_ROOT / "DECISION_LOG.md"


def write_gate_log(logname: str, lines: list, decision_summary: str) -> None:
    """Persist a gate's outcome so it leaves the same audit trail as the numbered
    scripts: a qc_logs/<logname>.log file AND a DECISION_LOG.md entry. The gates
    used to print() only, so their pass/fail decision existed only in the terminal
    — this closes that gap for the reproducibility record."""
    QC_DIR.mkdir(parents=True, exist_ok=True)
    (QC_DIR / logname).write_text("\n".join(lines) + "\n")
    # append a DECISION_LOG entry, numbered like the scripts do
    text = DECISION_LOG_FILE.read_text() if DECISION_LOG_FILE.exists() else "# Decision Log\n"
    nums = [int(m) for m in _re.findall(r"^## Entry #(\d+)", text, _re.MULTILINE)]
    nxt = max(nums, default=0) + 1
    with DECISION_LOG_FILE.open("a") as f:
        f.write(f"\n## Entry #{nxt} — {date.today().isoformat()}\n{decision_summary}\n")
    print(f"  (logged to qc_logs/{logname} and DECISION_LOG.md Entry #{nxt})")


STEPS = [
    ("01", "scripts/01_extract.py",                 "Extract cohort from ClinicalTrials.gov"),
    ("02", "scripts/02_screen.py",                  "Screen to analytic cohort"),
    ("VG", None,                                     "VOLUME GATE (go/no-go)"),
    ("03", "scripts/03_reconcile.py",               "Reconcile against hand-vetted NCT list"),
    ("OG", None,                                     "OVERLAP GATE (go/no-go)"),
    ("04", "scripts/04_detect.py",                  "Detect PRO instruments (frozen dictionary)"),
    ("05", "scripts/05_build_validation_sample.py", "Build detection-validation sample"),
    ("07", "scripts/07_figures.py",                 "Generate the standard descriptive figure set"),
    ("08", "scripts/08_reference_table.py",          "Generate the reviewer instrument reference table"),
]


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        fail(f"Missing {CONFIG_FILE}. The config is the source of truth; nothing runs without it.")
    return yaml.safe_load(CONFIG_FILE.read_text())


def fail(msg: str) -> None:
    print(f"\n  RUN HALTED\n  {msg}\n", file=sys.stderr)
    sys.exit(1)


def run_script(rel_path: str, label: str) -> None:
    path = REPO_ROOT / rel_path
    if not path.exists():
        fail(f"Expected script not found: {rel_path}. Check the folder skeleton and naming rules.")
    print(f"\n{'='*70}\n  RUNNING {rel_path}  —  {label}\n{'='*70}")
    result = subprocess.run([sys.executable, str(path)], cwd=REPO_ROOT)
    if result.returncode != 0:
        fail(f"{rel_path} exited with code {result.returncode}. Fix before continuing; "
             f"downstream steps depend on its output.")


def csv_row_count(path: Path) -> int:
    with path.open(newline="") as f:
        return sum(1 for _ in csv.DictReader(f))


def volume_gate(config: dict) -> None:
    """Compare the screened cohort size against the size root-mapping expected.
    Flags a material shortfall rather than a flat floor — 'did I get roughly the
    cohort root mapping said I should?' is the meaningful check."""
    screened = REPO_ROOT / "data" / "screened_kept.csv"
    if not screened.exists():
        fail("Volume gate: data/screened_kept.csv missing — screening did not complete.")
    n = csv_row_count(screened)
    expected = config.get("volume_gate", {}).get("expected_cohort_size")
    floor = config.get("volume_gate", {}).get("min_cohort_size")

    lines = [f"{'='*70}", "  VOLUME GATE", f"{'='*70}",
             f"  Screened cohort size:            {n}"]
    shortfall = None
    if expected is not None:
        shortfall = (expected - n) / expected * 100 if expected else 0
        lines.append(f"  Root-mapping expected size:      {expected}")
        lines.append(f"  Shortfall vs expected:           {shortfall:.1f}%")
    for ln in lines:
        print(ln if ln.startswith("  ") else f"\n{ln}")

    if expected is not None and shortfall is not None and shortfall > 25:
        lines.append("  VOLUME GATE FAILED.")
        write_gate_log("VG_volume_gate.log", lines,
            f"Volume gate FAILED: screened {n} vs expected {expected} ({shortfall:.1f}% short).")
        fail(f"Volume gate FAILED: screened cohort ({n}) is {shortfall:.1f}% below the "
             f"root-mapping expectation ({expected}). Retrieval likely broke — investigate "
             f"before proceeding. (Threshold: >25% shortfall halts.)")
    if floor is not None and n < floor:
        lines.append("  VOLUME GATE FAILED (below floor).")
        write_gate_log("VG_volume_gate.log", lines,
            f"Volume gate FAILED: screened {n} below minimum viable size {floor}.")
        fail(f"Volume gate FAILED: screened cohort ({n}) is below the minimum viable size "
             f"({floor}). This topic may be too thin to analyze — team go/no-go required.")

    print("  VOLUME GATE PASSED.")
    lines.append("  VOLUME GATE PASSED.")
    exp_txt = f"expected {expected} ({shortfall:.1f}% short)" if expected is not None else "no expected size set"
    write_gate_log("VG_volume_gate.log", lines,
        f"Volume gate PASSED (`run_all.py`). Screened cohort {n}; {exp_txt}. "
        f"Recorded so the gate's decision is on disk, not only in the terminal.")


def overlap_gate(config: dict) -> None:
    """Read the reconciliation report and enforce the minimum overlap with the
    hand-vetted NCT list. Below the bar means the code cohort doesn't match what
    was vetted — retrieval needs a fix, not a push forward."""
    report = REPO_ROOT / "data" / "reconciliation_report.csv"
    if not report.exists():
        fail("Overlap gate: data/reconciliation_report.csv missing — reconciliation did not complete.")
    labels = {"BOTH": 0, "CODE_ONLY": 0, "VETTED_ONLY": 0}
    with report.open(newline="") as f:
        for row in csv.DictReader(f):
            labels[row["label"]] = labels.get(row["label"], 0) + 1
    both = labels["BOTH"]
    union = both + labels["CODE_ONLY"] + labels["VETTED_ONLY"]
    overlap = (both / union * 100) if union else 0.0
    min_overlap = config.get("reconciliation", {}).get("min_overlap_pct", 90)

    lines = [f"{'='*70}", "  OVERLAP GATE", f"{'='*70}",
             f"  In both:      {both}",
             f"  Code only:    {labels['CODE_ONLY']}",
             f"  Vetted only:  {labels['VETTED_ONLY']}",
             f"  Overlap:      {overlap:.1f}%   (minimum required: {min_overlap}%)"]
    for ln in lines:
        print(ln if ln.startswith("  ") else f"\n{ln}")

    if overlap < min_overlap:
        lines.append("  OVERLAP GATE FAILED.")
        write_gate_log("OG_overlap_gate.log", lines,
            f"Overlap gate FAILED: {overlap:.1f}% < {min_overlap}% "
            f"(both {both}, code-only {labels['CODE_ONLY']}, vetted-only {labels['VETTED_ONLY']}).")
        fail(f"Overlap gate FAILED: {overlap:.1f}% < {min_overlap}%. The code's cohort does not "
             f"match the hand-vetted list well enough. Inspect CODE_ONLY / VETTED_ONLY rows in "
             f"data/reconciliation_report.csv and fix retrieval before detection.")

    print("  OVERLAP GATE PASSED.")
    lines.append("  OVERLAP GATE PASSED.")
    write_gate_log("OG_overlap_gate.log", lines,
        f"Overlap gate PASSED (`run_all.py`). Overlap {overlap:.1f}% ≥ {min_overlap}% "
        f"(both {both}, code-only {labels['CODE_ONLY']}, vetted-only {labels['VETTED_ONLY']}). "
        f"This is the gate's own pass/fail record, distinct from 03_reconcile.py's log.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the full topic pipeline from config.")
    parser.add_argument("--from", dest="start", default="01",
                        help="Resume from this step code (01/02/03/04/05).")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan; run nothing.")
    args = parser.parse_args()

    config = load_config()
    topic = config.get("topic", {}).get("name", "<unknown>")
    print(f"Topic: {topic}   |   Config: {CONFIG_FILE.relative_to(REPO_ROOT)}")

    order = [s[0] for s in STEPS]
    if args.start not in [c for c in order if c not in ("VG", "OG")]:
        fail(f"--from {args.start} is not a runnable step. Choose one of: 01 02 03 04 05.")

    started = False
    for code, script, label in STEPS:
        if code == args.start:
            started = True
        # gates always run in-line with their preceding step's sequence
        if not started and code not in ("VG", "OG"):
            continue
        if args.dry_run:
            print(f"  [{code}] {label}" + (f"  ->  {script}" if script else "  (gate)"))
            continue
        if code == "VG":
            volume_gate(config)
        elif code == "OG":
            overlap_gate(config)
        else:
            run_script(script, label)

    if not args.dry_run:
        print(f"\n{'='*70}\n  PIPELINE COMPLETE (through 05_build_validation_sample).\n"
              f"  NEXT — HUMAN STEP: two reviewers independently complete the dual-coding\n"
              f"  review files. Only after both are done do you run 06_validation_stats.py.\n{'='*70}")


if __name__ == "__main__":
    main()
