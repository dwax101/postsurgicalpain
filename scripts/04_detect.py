#!/usr/bin/env python3
"""
scripts/04_detect.py  —  PRO instrument detection (config-driven, general engine).

Reads data/screened_kept.csv and the frozen dictionary (config/dictionary.py),
and classifies each trial. Everything topic-specific comes from
config/topic_config.yaml — this script is IDENTICAL across all thirteen topics;
only the config and the dictionary change.

What the config controls here:
  classification.nrs_vas_is_pro     -> whether single-item NRS/VAS counts as a
                                        named PRO (False for obesity; True for
                                        postsurgical pain and low back pain).
  alignment.mode                    -> how "aligned with the endorsed set" is
                                        decided. FOUR modes, all implemented:
      single       : aligned if the one endorsed instrument is present.
                     (OBESITY — endorsed set = BODY-Q only.)
      any_of       : aligned if ANY listed instrument present.
                     (e.g. low back pain: ODI OR RMDQ.)
      all_of       : aligned only if ALL listed instruments present.
                     (strict full-core-set topics.)
      age_branched : the endorsed instrument depends on a subgroup, so the trial
                     is aligned if it carries the instrument for ANY branch it
                     could belong to. (e.g. eczema QoL: DLQI/CDLQI/IDQoL.)

Detection precedence (the appetite-VAS fix v1's code omitted): the dictionary may
mark an instrument `detect_before: [names]`. Such an instrument is tested first,
and any instrument it pre-empts is NOT also credited on the same trial — so a
"hunger VAS" mention lands on the Appetite/Hunger VAS line only, never double-counted
on the general VAS line.

The dictionary is READ-ONLY. Nothing is added, inferred, or discovered here.
"""

import csv
import json
import re
import importlib.util
from datetime import date
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = REPO_ROOT / "config" / "topic_config.yaml"
INPUT_FILE = REPO_ROOT / "data" / "screened_kept.csv"
OUTPUT_FILE = REPO_ROOT / "data" / "detection_results.csv"
LOG_FILE = REPO_ROOT / "qc_logs" / "04_detect.log"
DECISION_LOG_FILE = REPO_ROOT / "DECISION_LOG.md"


def log_print(line, log_lines):
    print(line)
    log_lines.append(line)


def load_config():
    return yaml.safe_load(CONFIG_FILE.read_text())


def load_instruments(dict_path):
    spec = importlib.util.spec_from_file_location("pro_dictionary", dict_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.INSTRUMENTS


def build_trial_text(row):
    chunks = []
    for column in ("primary_outcomes", "secondary_outcomes"):
        raw = row.get(column, "") or "[]"
        for outcome in json.loads(raw):
            chunks.append(f"{outcome.get('measure','')} {outcome.get('description','')}")
    return " ".join(chunks)


def compile_instruments(instruments):
    compiled = []
    for inst in instruments:
        compiled.append({
            "canonical": inst["canonical"],
            "regexes": [re.compile(p, re.IGNORECASE) for p in inst["patterns"]],
            "is_pro": bool(inst.get("is_pro", False)),
            "endorsed": bool(inst.get("endorsed", False)),
            "detect_before": inst.get("detect_before", []),  # precedence list
        })
    return compiled


def detect_matches(text, compiled):
    """Return matched instruments, honoring detect_before precedence so a more
    specific instrument suppresses the general one it pre-empts on the same trial."""
    raw_hits = {inst["canonical"] for inst in compiled if any(rx.search(text) for rx in inst["regexes"])}
    suppressed = set()
    for inst in compiled:
        if inst["canonical"] in raw_hits:
            for preempted in inst["detect_before"]:
                suppressed.add(preempted)
    return [inst for inst in compiled if inst["canonical"] in raw_hits and inst["canonical"] not in suppressed]


def is_aligned(matched_canonicals, align_cfg):
    """Apply the configured alignment mode against the set of matched instruments."""
    mode = align_cfg.get("mode", "single")
    matched = set(matched_canonicals)

    if mode in ("single", "any_of"):
        endorsed = set(align_cfg.get("endorsed_instruments", []))
        return len(matched & endorsed) > 0

    if mode == "all_of":
        endorsed = set(align_cfg.get("endorsed_instruments", []))
        return endorsed.issubset(matched) and len(endorsed) > 0

    if mode == "age_branched":
        # aligned if the trial carries the endorsed instrument for ANY branch.
        for branch in align_cfg.get("branches", []):
            if set(branch.get("endorsed_instruments", [])) & matched:
                return True
        return False

    raise ValueError(f"Unknown alignment.mode: {mode!r}")


def append_decision_log_entry(body):
    text = DECISION_LOG_FILE.read_text()
    nums = [int(n) for n in re.findall(r"^## Entry #(\d+)", text, flags=re.MULTILINE)]
    nxt = max(nums, default=0) + 1
    with DECISION_LOG_FILE.open("a") as f:
        f.write(f"\n## Entry #{nxt} — {date.today().isoformat()}\n{body}\n")
    return nxt


def main():
    log_lines = []
    config = load_config()
    align_cfg = config.get("alignment", {})
    dict_path = REPO_ROOT / config["dictionary"]["operative_file"]

    instruments = load_instruments(dict_path)
    compiled = compile_instruments(instruments)
    log_print(f"Loaded {len(instruments)} instruments (read-only) from {dict_path.relative_to(REPO_ROOT)}", log_lines)
    log_print(f"Alignment mode: {align_cfg.get('mode')}", log_lines)

    with INPUT_FILE.open(newline="") as f:
        trials = list(csv.DictReader(f))
    log_print(f"Loaded {len(trials)} trials from {INPUT_FILE.relative_to(REPO_ROOT)}\n", log_lines)

    results = []
    completeness = 0
    alignment = 0

    for row in trials:
        text = build_trial_text(row)
        matched = detect_matches(text, compiled)
        matched_names = [m["canonical"] for m in matched]
        matched_pro = [m["canonical"] for m in matched if m["is_pro"]]
        matched_endorsed = [m["canonical"] for m in matched if m["endorsed"]]

        has_named_pro = len(matched_pro) > 0
        aligned = is_aligned(matched_names, align_cfg)

        completeness += 1 if has_named_pro else 0
        alignment += 1 if aligned else 0

        results.append({
            "nct_id": row["nct_id"],
            "first_posted_date": row.get("first_posted_date",""),
            "matched_instruments": "|".join(matched_names),
            "matched_is_pro_instruments": "|".join(matched_pro),
            "matched_endorsed_instruments": "|".join(matched_endorsed),
            "has_any_named_pro": has_named_pro,
            "uses_endorsed": aligned,
        })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "nct_id", "first_posted_date", "matched_instruments", "matched_is_pro_instruments",
            "matched_endorsed_instruments", "has_any_named_pro", "uses_endorsed"])
        w.writeheader()
        w.writerows(results)

    total = len(trials)
    c_pct = completeness / total * 100 if total else 0
    a_pct = alignment / total * 100 if total else 0
    log_print(f"Total trials:                     {total}", log_lines)
    log_print(f"Completeness (has_any_named_pro):  {completeness} ({c_pct:.2f}%)", log_lines)
    log_print(f"Alignment (mode={align_cfg.get('mode')}):        {alignment} ({a_pct:.2f}%)", log_lines)
    log_print(f"\nWrote {OUTPUT_FILE.relative_to(REPO_ROOT)} ({len(results)} rows)", log_lines)

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text("\n".join(log_lines) + "\n")

    entry = (
        f"PRO detection (`scripts/04_detect.py`, config-driven). Dictionary: "
        f"`{dict_path.relative_to(REPO_ROOT)}` ({len(instruments)} instruments, read-only). "
        f"Alignment mode: {align_cfg.get('mode')}. Input: {total} trials. "
        f"Completeness {completeness} ({c_pct:.2f}%); alignment {alignment} ({a_pct:.2f}%)."
    )
    print(f"Appended DECISION_LOG.md Entry #{append_decision_log_entry(entry)}")


if __name__ == "__main__":
    main()
