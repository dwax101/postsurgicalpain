#!/usr/bin/env python3
"""
scripts/08_reference_table.py — Reviewer instrument reference table.

Reads the frozen dictionary (config/dictionary.py) and writes a per-topic
reference table that reviewers use during detection validation. Reviewers must
recognize PRO instruments in trial outcome text — many of which they may never
have seen — so this table lists, for every instrument in the dictionary:

    Instrument        — the canonical name
    Also written as   — its alternate spellings / abbreviations (from the patterns)
    Is PRO            — whether it counts as a named PRO (is_pro)
    Endorsed          — whether it is in the consensus-endorsed set (endorsed)
    What it measures  — LEFT BLANK, marked [VERIFY]. The dictionary has no
                        description, and instrument facts are exactly where
                        sourcing errors hide, so this column is filled by the
                        TEAM against the actual instrument/source — never
                        auto-written. See note below.

Output: reference_table.csv (project root). The team opens it in Excel, fills the
"What it measures" column against each instrument's source, and hands the
completed sheet to reviewers.

Wired into run_all.py so it regenerates for every topic automatically. It does
NOT invent descriptions — by construction it cannot emit a wrong instrument fact.
"""

import csv
import importlib.util
import re
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DICT_FILE = REPO_ROOT / "config" / "dictionary.py"
OUT_FILE = REPO_ROOT / "reference_table.csv"
LOG_FILE = REPO_ROOT / "qc_logs" / "08_reference_table.log"
DECISION_LOG_FILE = REPO_ROOT / "DECISION_LOG.md"


def load_instruments(dict_path):
    spec = importlib.util.spec_from_file_location("pro_dictionary", dict_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.INSTRUMENTS


def readable_alternates(patterns):
    """Turn regex patterns into a human-readable 'also written as' list.
    Patterns are detection regexes (e.g. r'\\bSGRQ\\b', r"St\\.?\\s*George").
    We strip the common regex scaffolding to recover the plain text a reviewer
    would actually see. Best-effort display cleanup only; does not affect detection.

    IMPORTANT: this must not corrupt real letters. Earlier a broad 's?' cleanup
    ate every literal 's'. We now only remove genuine regex metacharacters and
    leave all alphabetic text intact."""
    out = []
    for p in patterns:
        s = p
        s = s.replace(r"\b", "")               # word-boundary anchors
        s = re.sub(r"\\s[?*+]?", " ", s)        # \s, \s?, \s* -> a space
        s = re.sub(r"\\\.", ".", s)             # \. -> literal .
        s = re.sub(r"\\", "", s)                # any remaining backslashes
        s = re.sub(r"\(\?:[^)]*\)[?*+]?", "", s)  # non-capturing groups (e.g. (?:...)?)
        s = re.sub(r"\([^)]*\)[?*+]?", "", s)   # optional groups like (ue)?
        s = re.sub(r"\[[^\]]*\][?*+]?", "", s)  # character classes like [- ]
        s = re.sub(r"(?<=[A-Za-z0-9])[?*+]", "", s)  # trailing quantifier on a char
        s = re.sub(r"(?<=[.\-':])[?*+]", "", s)       # quantifier after punctuation (St.? '?s)
        s = re.sub(r"\s+", " ", s).strip(" -")
        if s and s not in out:
            out.append(s)
    return "; ".join(out)


def dlog(body):
    text = DECISION_LOG_FILE.read_text() if DECISION_LOG_FILE.exists() else "# Decision Log\n"
    nums = [int(m) for m in re.findall(r"^## Entry #(\d+)", text, re.MULTILINE)]
    nxt = max(nums, default=0) + 1
    with DECISION_LOG_FILE.open("a") as f:
        f.write(f"\n## Entry #{nxt} — {date.today().isoformat()}\n{body}\n")
    return nxt


def main():
    if not DICT_FILE.exists():
        raise SystemExit(f"Missing {DICT_FILE}. Build and freeze the dictionary (Stage A) first.")
    instruments = load_instruments(DICT_FILE)

    # sort: endorsed first, then PRO, then the rest — so the instruments reviewers
    # most need to recognize sit at the top. Alphabetical within each group.
    def sort_key(i):
        return (not i.get("endorsed", False), not i.get("is_pro", False), i["canonical"].lower())
    instruments = sorted(instruments, key=sort_key)

    rows = []
    for i in instruments:
        rows.append({
            "Instrument": i["canonical"],
            "Also written as": readable_alternates(i.get("patterns", [])),
            "Is PRO": "Yes" if i.get("is_pro", False) else "No",
            "Endorsed": "Yes" if i.get("endorsed", False) else "No",
            "What it measures (FILL — verify against source)": "[VERIFY]",
        })

    with OUT_FILE.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "Instrument", "Also written as", "Is PRO", "Endorsed",
            "What it measures (FILL — verify against source)"])
        w.writeheader()
        w.writerows(rows)

    n_pro = sum(1 for i in instruments if i.get("is_pro"))
    n_end = sum(1 for i in instruments if i.get("endorsed"))
    msg = (f"Wrote reference_table.csv: {len(rows)} instruments "
           f"({n_pro} PRO, {n_end} endorsed). The 'What it measures' column is "
           f"[VERIFY] — the team fills it from each instrument's source before "
           f"handing the sheet to reviewers.")
    print(msg)
    print(f"  -> {OUT_FILE.relative_to(REPO_ROOT)}")
    print("  NEXT: open it in Excel, fill 'What it measures' for each instrument, "
          "verify against the source, then give it to your validation reviewers.")

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text(msg + "\n")
    entry = dlog(f"Reviewer reference table (`scripts/08_reference_table.py`). {msg}")
    print(f"Appended DECISION_LOG.md Entry #{entry}")


if __name__ == "__main__":
    main()
