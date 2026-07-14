#!/usr/bin/env python3
"""
scripts/dict_03_check.py  —  Dictionary discovery: dead-pattern check (Stage A, step 4).

Imports INSTRUMENTS from config/DRAFT_dictionary.py and counts, for each instrument,
how many trials in data/dict_raw.csv match ANY of its patterns. It then LOUDLY flags
three failure classes:

  1. DEAD is_pro     — an is_pro=True instrument that matches ZERO trials (it can never
                       contribute to PRO-usage stats; likely a broken/typo pattern).
  2. DEAD endorsed   — an endorsed=True instrument that matches ZERO trials. This is the
                       "rare-endorsed-instrument trap": alignment would read zero by
                       construction. (Endorsed instruments must still enter the frozen
                       dictionary regardless of frequency — this check confirms they are
                       actually detectable.)
  3. ACRONYM GAP     — an instrument that carries BOTH a spelled-out-name pattern and an
                       acronym pattern, but only ONE side ever matches (name matches, acronym
                       never — or vice versa). That asymmetry usually means a typo'd acronym
                       or a wrong/spurious spelling, i.e. the acronym-gap class of bug.

Counts are printed high-to-low. Read-only; writes nothing. Run after editing the DRAFT.
"""
import csv, json, re, sys, importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRAFT = ROOT / "config" / "DRAFT_dictionary.py"
RAW = ROOT / "data" / "dict_raw.csv"
csv.field_size_limit(sys.maxsize)


def load_instruments(path):
    spec = importlib.util.spec_from_file_location("draft_dictionary", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.INSTRUMENTS


def is_acronym_pattern(pat):
    """Classify a single regex pattern as an ACRONYM form (True) or a spelled-out
    NAME form (False). Multiword patterns (containing \\s or a space) are names;
    otherwise a short, uppercase-dominant token (\\bVAS\\b, \\bEQ-?5D\\b, \\bPD-?Q\\b)
    is an acronym, while a lowercase word (oswestry, lysholm, euroqol) is a name."""
    if "\\s" in pat or " " in pat:
        return False
    core = re.sub(r"\\[bBdDwWsS]", "", pat)      # drop anchors / char-classes
    core = re.sub(r"[^A-Za-z]", "", core)         # keep letters only
    if not core:
        return False
    up = sum(c.isupper() for c in core)
    lo = sum(c.islower() for c in core)
    return up >= 2 and up >= lo


def build_text(row):
    meas = json.loads(row.get("outcome_measures") or "[]")
    desc = json.loads(row.get("outcome_descriptions") or "[]")
    return "  ".join(meas) + "  " + "  ".join(desc)


def main():
    instruments = load_instruments(DRAFT)
    rows = list(csv.DictReader(RAW.open()))
    n_trials = len(rows)

    # Pre-compile, splitting each instrument's patterns into name vs acronym groups.
    compiled = []
    for inst in instruments:
        name_rx, acro_rx = [], []
        for p in inst["patterns"]:
            (acro_rx if is_acronym_pattern(p) else name_rx).append(re.compile(p, re.IGNORECASE))
        compiled.append({
            "canonical": inst["canonical"],
            "is_pro": bool(inst.get("is_pro", False)),
            "endorsed": inst.get("endorsed") is True,   # None/False both -> not endorsed
            "name_rx": name_rx,
            "acro_rx": acro_rx,
            "total": 0, "name_hits": 0, "acro_hits": 0,
        })

    # Count trials (each trial counted once per instrument / per class).
    for row in rows:
        text = build_text(row)
        for c in compiled:
            name_m = any(rx.search(text) for rx in c["name_rx"])
            acro_m = any(rx.search(text) for rx in c["acro_rx"])
            if name_m:
                c["name_hits"] += 1
            if acro_m:
                c["acro_hits"] += 1
            if name_m or acro_m:
                c["total"] += 1

    # -------- counts, high to low --------
    print(f"Dead-pattern check — {len(compiled)} instruments over {n_trials} trials "
          f"(config/DRAFT_dictionary.py)\n")
    print(f"{'n':>6}  {'pct':>5}  {'pro':>3} {'end':>3}  {'name':>6} {'acro':>6}  instrument")
    for c in sorted(compiled, key=lambda x: (-x["total"], x["canonical"].lower())):
        print(f"{c['total']:>6}  {100*c['total']/n_trials:>4.1f}%  "
              f"{'Y' if c['is_pro'] else '-':>3} {'Y' if c['endorsed'] else '-':>3}  "
              f"{c['name_hits']:>6} {c['acro_hits']:>6}  {c['canonical']}")

    # -------- LOUD flags --------
    dead_pro = [c for c in compiled if c["is_pro"] and c["total"] == 0]
    dead_end = [c for c in compiled if c["endorsed"] and c["total"] == 0]
    # acronym gap: has BOTH a name and an acronym pattern, but only one side ever fires
    gap = [c for c in compiled
           if c["name_rx"] and c["acro_rx"]
           and (c["name_hits"] == 0) != (c["acro_hits"] == 0)]

    def banner(title, items, fmt):
        bar = "!" * 72
        print(f"\n{bar}\n!!! {title}: {len(items)}\n{bar}")
        if not items:
            print("    (none)")
        for c in items:
            print("    " + fmt(c))

    banner("DEAD is_pro INSTRUMENTS (is_pro=True, 0 trials)", dead_pro,
           lambda c: f"{c['canonical']}")
    banner("DEAD ENDORSED INSTRUMENTS (endorsed=True, 0 trials) — rare-endorsed trap", dead_end,
           lambda c: f"{c['canonical']}")
    banner("ACRONYM-GAP (name and acronym patterns disagree — one matches, the other 0)", gap,
           lambda c: (f"{c['canonical']}: "
                      + ("NAME matches but ACRONYM never fires "
                         f"(name={c['name_hits']}, acro=0) — check the acronym pattern"
                         if c["acro_hits"] == 0 else
                         "ACRONYM matches but NAME never fires "
                         f"(acro={c['acro_hits']}, name=0) — check the spelled-out pattern")))

    print(f"\nSummary: {len(dead_pro)} dead is_pro, {len(dead_end)} dead endorsed, "
          f"{len(gap)} acronym-gap. "
          + ("ALL CLEAR." if not (dead_pro or dead_end or gap) else "REVIEW FLAGS ABOVE."))


if __name__ == "__main__":
    main()
