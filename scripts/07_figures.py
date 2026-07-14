#!/usr/bin/env python3
"""
scripts/07_figures.py — SAFE Lab standard descriptive figure set.

Runs after detection. Reads data/detection_results.csv (which carries
first_posted_date per trial) and config/topic_config.yaml, and writes a
CONSISTENT figure set to figures/ for every topic. Per-topic differences
(endorsed instruments, endorsement dates) are read from the config — the
code is identical across all topics.

Genre: EXPLORATORY DESCRIPTIVE. The whole instrument distribution is the
subject; the endorsed instrument is one labeled example of heterogeneity,
never the headline. Two time anchors are drawn as reference lines only,
never as filters: the 2006 FDA PRO guidance (global) and this topic's
endorsement date(s) (per-topic).

Outputs (all 300 dpi):
  figures/01_category_split.png          three co-equal categories
  figures/02_instrument_frequency.png    ranked, endorsed highlighted
  figures/03_concentration_curve.png     Pareto / fragmentation
  figures/04_category_trend.png          stacked area over time + reference lines
  figures/05_endorsed_uptake.png         endorsed tool since its endorsement date
  figures/S1_registrations_per_year.png  honest denominator for the proportions
  figures/S2_nrs_vas_prevalence.png      single-scale-only prevalence over time
  figures/epoch_table.csv                alignment by endorsement epoch (reads YAML)
"""

import csv
import json
from datetime import date, datetime
from pathlib import Path

import yaml
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = REPO_ROOT / "config" / "topic_config.yaml"
DETECT_FILE = REPO_ROOT / "data" / "detection_results.csv"
FIG_DIR = REPO_ROOT / "figures"
LOG_FILE = REPO_ROOT / "qc_logs" / "07_figures.log"
DECISION_LOG_FILE = REPO_ROOT / "DECISION_LOG.md"

DPI = 300
# color system: neutral greys/blues for the landscape, one accent for the endorsed tool
C_NAMED = "#4C72A0"      # named PRO
C_NRSVAS = "#8FB0D4"     # NRS/VAS only
C_VAGUE = "#C9D6E5"      # vague only
C_NONE = "#E8ECEF"       # no PRO
C_ENDORSED = "#B5651D"   # the accent — endorsed instrument, used sparingly
C_REF = "#999999"        # reference lines


def log(lines, s):
    print(s)
    lines.append(s)


def load_config():
    return yaml.safe_load(CONFIG_FILE.read_text())


def year_of(datestr):
    """Parse a CTG first-posted date into a year int, or None."""
    if not datestr:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(datestr, fmt).year
        except ValueError:
            continue
    return None


def load_rows():
    with DETECT_FILE.open(newline="") as f:
        return list(csv.DictReader(f))


def as_bool(v):
    return str(v).strip().lower() in ("true", "1", "yes")


def categorize(row):
    """Every trial falls into exactly one of four co-equal categories.
    named > nrs_vas > vague > none  (named wins ties)."""
    if as_bool(row.get("has_any_named_pro")):
        return "named"
    matched = row.get("matched_instruments", "")
    # NRS/VAS-only: matched something, but it wasn't a named PRO -> treat as nrs/vas band.
    # (The dictionary marks NRS/VAS is_pro per config; if is_pro False they land here.)
    if matched.strip():
        return "nrs_vas"
    # vague vs none can't be distinguished from detection alone; the pipeline marks
    # a trial 'vague' if it had outcome text but no instrument. We approximate:
    # no matched instrument and no named PRO -> 'none' unless a vague flag exists.
    if as_bool(row.get("has_vague_descriptor", "")):
        return "vague"
    return "none"


def endorsement_dates(cfg):
    """Return list of (body, year, instruments) from the config, sorted by year."""
    out = []
    for m in cfg.get("time_anchors", {}).get("endorsement_milestones", []) or []:
        y = year_of(m.get("date", ""))
        if y:
            out.append((m.get("body", "?"), y, m.get("instruments", [])))
    return sorted(out, key=lambda x: x[1])


# --------------------------------------------------------------------------
# FIGURE 1 — category split (three+ co-equal categories, endorsed as a sliver)
# --------------------------------------------------------------------------
def fig_category_split(rows, endorsed_count, total, buf):
    cats = {"named": 0, "nrs_vas": 0, "vague": 0, "none": 0}
    for r in rows:
        cats[categorize(r)] += 1
    fig, ax = plt.subplots(layout="constrained", figsize=(8, 5))
    labels = ["Named PRO", "NRS/VAS only", "Vague only", "No PRO"]
    vals = [cats["named"], cats["nrs_vas"], cats["vague"], cats["none"]]
    colors = [C_NAMED, C_NRSVAS, C_VAGUE, C_NONE]
    bars = ax.bar(labels, vals, color=colors, edgecolor="white")
    # endorsed shown as a small sliver WITHIN the named-PRO bar
    if endorsed_count > 0:
        ax.bar(["Named PRO"], [endorsed_count], color=C_ENDORSED, edgecolor="white",
               label=f"of which endorsed: {endorsed_count}")
        ax.legend(frameon=False, fontsize=9, loc="upper right")
    for b, v in zip(bars, vals):
        pct = 100 * v / total if total else 0
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v}\n({pct:.1f}%)",
                ha="center", va="bottom", fontsize=10, fontweight="bold")
    # headroom so the value labels above the tallest bar don't touch the title
    ax.set_ylim(0, max(vals) * 1.18 if vals else 1)
    ax.set_ylabel("Number of trials")
    ax.set_title(f"PRO measurement categories (n={total} trials)", pad=12)
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(FIG_DIR / "01_category_split.png", dpi=DPI)
    plt.close(fig)
    log(buf, f"  01_category_split: named={cats['named']} nrsvas={cats['nrs_vas']} "
             f"vague={cats['vague']} none={cats['none']} endorsed_sliver={endorsed_count}")


# --------------------------------------------------------------------------
# FIGURE 2 — ranked instrument frequency, endorsed highlighted
# --------------------------------------------------------------------------
def fig_frequency(rows, endorsed_set, buf):
    from collections import Counter
    c = Counter()
    for r in rows:
        for inst in r.get("matched_instruments", "").split("|"):
            inst = inst.strip()
            if inst:
                c[inst] += 1
    if not c:
        log(buf, "  02_instrument_frequency: no instruments detected, skipped")
        return
    items = c.most_common()
    names = [n for n, _ in items][::-1]
    counts = [v for _, v in items][::-1]
    colors = [C_ENDORSED if n in endorsed_set else C_NAMED for n in names]
    fig, ax = plt.subplots(layout="constrained", figsize=(9, max(4, len(names) * 0.28)))
    ax.barh(names, counts, color=colors, edgecolor="white")
    ax.set_xlabel("Number of trials")
    ax.set_title(f"PRO instrument frequency, ranked (n={len(names)} instruments)", pad=12)
    ax.spines[["top", "right"]].set_visible(False)
    legend = [Patch(facecolor=C_NAMED, label="instrument"),
              Patch(facecolor=C_ENDORSED, label="endorsed by consensus body")]
    ax.legend(handles=legend, frameon=False, fontsize=9, loc="lower right")
    fig.savefig(FIG_DIR / "02_instrument_frequency.png", dpi=DPI)
    plt.close(fig)
    log(buf, f"  02_instrument_frequency: {len(names)} instruments, "
             f"{sum(1 for n in names if n in endorsed_set)} endorsed highlighted")


# --------------------------------------------------------------------------
# FIGURE 3 — concentration / Pareto curve
# --------------------------------------------------------------------------
def fig_concentration(rows, buf):
    from collections import Counter
    c = Counter()
    for r in rows:
        for inst in r.get("matched_instruments", "").split("|"):
            if inst.strip():
                c[inst.strip()] += 1
    if not c:
        log(buf, "  03_concentration_curve: no instruments, skipped")
        return
    counts = sorted(c.values(), reverse=True)
    total = sum(counts)
    cum, run = [], 0
    for v in counts:
        run += v
        cum.append(run / total)
    ranks = list(range(1, len(cum) + 1))
    fig, ax = plt.subplots(layout="constrained", figsize=(8, 5))
    ax.plot(ranks, cum, marker="o", color=C_NAMED, markersize=4)
    ax.axhline(0.5, ls="--", color=C_REF, lw=1)
    n50 = next((i for i, v in enumerate(cum, 1) if v >= 0.5), len(cum))
    ax.set_xlabel("Instrument rank")
    ax.set_ylabel("Cumulative share of total instrument-uses")
    ax.set_title("Concentration of PRO instrument usage (Pareto curve)", pad=12)
    ax.set_ylim(0, 1.02)
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(FIG_DIR / "03_concentration_curve.png", dpi=DPI)
    plt.close(fig)
    log(buf, f"  03_concentration_curve: top {n50} instruments = 50% of uses")


# --------------------------------------------------------------------------
# FIGURE 4 — category trend over time (stacked area) + reference lines
# --------------------------------------------------------------------------
def fig_category_trend(rows, cfg, buf):
    from collections import defaultdict
    by_year = defaultdict(lambda: {"named": 0, "nrs_vas": 0, "vague": 0, "none": 0})
    for r in rows:
        y = year_of(r.get("first_posted_date", ""))
        if y:
            by_year[y][categorize(r)] += 1
    if not by_year:
        log(buf, "  04_category_trend: no dated trials, skipped")
        return
    years = sorted(by_year)
    def frac(cat):
        out = []
        for y in years:
            tot = sum(by_year[y].values())
            out.append(100 * by_year[y][cat] / tot if tot else 0)
        return out
    fig, ax = plt.subplots(layout="constrained", figsize=(10, 5))
    ax.stackplot(years, frac("named"), frac("nrs_vas"), frac("vague"), frac("none"),
                 labels=["Named PRO", "NRS/VAS only", "Vague only", "No PRO"],
                 colors=[C_NAMED, C_NRSVAS, C_VAGUE, C_NONE])
    # 2006 FDA reference line (global). Label sits INSIDE the plot (near the top,
    # top-aligned) so it never collides with the title above the axes.
    fda = year_of(cfg.get("time_anchors", {}).get("fda_guidance_date", ""))
    if fda and years[0] <= fda <= years[-1]:
        ax.axvline(fda, color="#333333", ls="--", lw=1.3)
        ax.text(fda, 97, "FDA 2006 ", rotation=90, va="top", ha="right",
                fontsize=8, color="#333333")
    # endorsement date reference line(s) (per-topic, from YAML)
    for body, ey, _ in endorsement_dates(cfg):
        if years[0] <= ey <= years[-1]:
            ax.axvline(ey, color=C_ENDORSED, ls=":", lw=1.5)
            ax.text(ey, 97, f"{body} {ey} ", rotation=90, va="top", ha="right",
                    fontsize=8, color=C_ENDORSED)
    ax.set_xlabel("First-posted year")
    ax.set_ylabel("% of trials that year")
    ax.set_title("PRO category composition by year", pad=12)
    ax.set_ylim(0, 100)
    # legend BELOW the x-axis label, outside the plot, so it never overlaps the
    # year tick labels. constrained_layout reserves the space automatically.
    ax.legend(loc="upper center", ncol=4, frameon=False, fontsize=9,
              bbox_to_anchor=(0.5, -0.16))
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(FIG_DIR / "04_category_trend.png", dpi=DPI)
    plt.close(fig)
    log(buf, f"  04_category_trend: {years[0]}–{years[-1]}; FDA line={fda}; "
             f"endorsement lines={[e[1] for e in endorsement_dates(cfg)]}")


# --------------------------------------------------------------------------
# FIGURE 5 — endorsed-instrument uptake from its endorsement date forward
# --------------------------------------------------------------------------
def fig_endorsed_uptake(rows, cfg, buf):
    from collections import defaultdict
    # If no instrument is endorsed for this condition, alignment is NOT APPLICABLE,
    # not zero. Drawing a flat-zero line would falsely imply a standard existed that
    # trials failed to adopt. Skip the figure and say so.
    endorsed_set = cfg.get("alignment", {}).get("endorsed_instruments", []) or []
    if not endorsed_set:
        log(buf, "  05_endorsed_uptake: SKIPPED — no endorsed instrument exists for this "
                 "condition; alignment is not applicable (not zero).")
        return
    miles = endorsement_dates(cfg)
    fig, ax = plt.subplots(layout="constrained", figsize=(9, 4.5))
    by_year_tot = defaultdict(int)
    by_year_end = defaultdict(int)
    for r in rows:
        y = year_of(r.get("first_posted_date", ""))
        if not y:
            continue
        by_year_tot[y] += 1
        if as_bool(r.get("uses_endorsed")):
            by_year_end[y] += 1
    if not by_year_tot:
        log(buf, "  05_endorsed_uptake: no dated trials, skipped")
        plt.close(fig)
        return
    years = sorted(by_year_tot)
    pct = [100 * by_year_end[y] / by_year_tot[y] if by_year_tot[y] else 0 for y in years]
    ax.plot(years, pct, marker="o", color=C_ENDORSED, markersize=4)
    ymax = max(pct) if pct else 1
    for body, ey, _ in miles:
        if years[0] <= ey <= years[-1]:
            ax.axvline(ey, color=C_ENDORSED, ls=":", lw=1.5)
            ax.text(ey, ymax * 0.96, f"{body} endorses ", rotation=90,
                    va="top", ha="right", fontsize=8, color=C_ENDORSED)
    ax.set_xlabel("First-posted year")
    ax.set_ylabel("% of trials using the endorsed instrument")
    ax.set_title("Endorsed-instrument uptake over time (descriptive)", pad=12)
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(FIG_DIR / "05_endorsed_uptake.png", dpi=DPI)
    plt.close(fig)
    tot_end = sum(by_year_end.values())
    log(buf, f"  05_endorsed_uptake: {tot_end} endorsed-using trials across {len(years)} years")


# --------------------------------------------------------------------------
# FIGURE S1 — registrations per year (the honest denominator)
# --------------------------------------------------------------------------
def fig_registrations(rows, buf):
    from collections import Counter
    c = Counter(y for y in (year_of(r.get("first_posted_date", "")) for r in rows) if y)
    if not c:
        log(buf, "  S1_registrations_per_year: no dated trials, skipped")
        return
    years = sorted(c)
    fig, ax = plt.subplots(layout="constrained", figsize=(9, 4))
    ax.bar(years, [c[y] for y in years], color=C_NAMED, edgecolor="white")
    ax.set_xlabel("First-posted year")
    ax.set_ylabel("Number of registered trials")
    ax.set_title("Trial registrations per year", pad=12)
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(FIG_DIR / "S1_registrations_per_year.png", dpi=DPI)
    plt.close(fig)
    log(buf, f"  S1_registrations_per_year: {years[0]}–{years[-1]}, "
             f"min/yr={min(c.values())} max/yr={max(c.values())}")


# --------------------------------------------------------------------------
# FIGURE S2 — NRS/VAS-only prevalence over time
# --------------------------------------------------------------------------
def fig_nrsvas_prevalence(rows, buf):
    from collections import defaultdict
    tot = defaultdict(int)
    nv = defaultdict(int)
    for r in rows:
        y = year_of(r.get("first_posted_date", ""))
        if not y:
            continue
        tot[y] += 1
        if categorize(r) == "nrs_vas":
            nv[y] += 1
    if not tot:
        log(buf, "  S2_nrs_vas_prevalence: no dated trials, skipped")
        return
    years = sorted(tot)
    pct = [100 * nv[y] / tot[y] if tot[y] else 0 for y in years]
    fig, ax = plt.subplots(layout="constrained", figsize=(9, 4))
    ax.plot(years, pct, marker="o", color=C_NRSVAS, markersize=4)
    ax.set_xlabel("First-posted year")
    ax.set_ylabel("% of trials with NRS/VAS only")
    ax.set_title("NRS/VAS-only prevalence over time", pad=12)
    ax.set_ylim(0, max(pct + [10]) * 1.15)
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(FIG_DIR / "S2_nrs_vas_prevalence.png", dpi=DPI)
    plt.close(fig)
    log(buf, f"  S2_nrs_vas_prevalence: {years[0]}–{years[-1]}")


# --------------------------------------------------------------------------
# EPOCH TABLE — alignment by endorsement epoch (reads YAML milestones)
# --------------------------------------------------------------------------
def epoch_table(rows, cfg, buf):
    # No endorsed instrument -> alignment is not applicable -> no epoch table.
    # (Writing an epoch table with 0% would misrepresent "no standard exists" as
    # "trials failed to meet the standard.")
    endorsed_set = cfg.get("alignment", {}).get("endorsed_instruments", []) or []
    if not endorsed_set:
        with (FIG_DIR / "epoch_table.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Epoch", "Named-PRO trials", "Aligned trials", "Alignment %"])
            w.writerow(["NOT APPLICABLE — no consensus-endorsed instrument exists for this condition",
                        "", "", "N/A"])
        log(buf, "  epoch_table: N/A — no endorsed instrument; alignment not computed.")
        return
    miles = endorsement_dates(cfg)
    # boundaries: pre-first / between each / post-last. For 1 milestone -> 2 epochs.
    bounds = [m[1] for m in miles]
    def epoch_label(y):
        if not bounds:
            return "all years (no endorsement date set)"
        if y < bounds[0]:
            return f"Pre-{miles[0][0]} (<{bounds[0]})"
        for i in range(len(bounds) - 1):
            if bounds[i] <= y < bounds[i + 1]:
                return f"{miles[i][0]}–{miles[i+1][0]} ({bounds[i]}–{bounds[i+1]-1})"
        return f"Post-{miles[-1][0]} (≥{bounds[-1]})"
    from collections import defaultdict
    named = defaultdict(int)
    aligned = defaultdict(int)
    order = []
    for r in rows:
        y = year_of(r.get("first_posted_date", ""))
        if y is None:
            continue
        if not as_bool(r.get("has_any_named_pro")):
            continue
        ep = epoch_label(y)
        if ep not in order:
            order.append(ep)
        named[ep] += 1
        if as_bool(r.get("uses_endorsed")):
            aligned[ep] += 1
    # write CSV — epochs in CHRONOLOGICAL order (Pre before Post), not alphabetical.
    # Each label carries its year range in parens; sort by the first year in it,
    # with the "Pre-...(<YYYY)" epoch (which has no lower bound) coming first.
    def epoch_sort_key(label):
        import re as _r
        # "Pre-X (<2014)" -> sort before everything; use bound-1
        m_pre = _r.search(r"\(<(\d{4})\)", label)
        if m_pre:
            return int(m_pre.group(1)) - 1
        m = _r.search(r"\((?:≥)?(\d{4})", label)
        return int(m.group(1)) if m else 0
    with (FIG_DIR / "epoch_table.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Epoch", "Named-PRO trials", "Aligned trials", "Alignment %"])
        for ep in sorted(order, key=epoch_sort_key):
            n = named[ep]
            a = aligned[ep]
            w.writerow([ep, n, a, f"{100*a/n:.1f}%" if n else "—"])
    log(buf, f"  epoch_table: {len(order)} epoch(s) from {len(miles)} milestone(s)")


def dlog(body):
    txt = DECISION_LOG_FILE.read_text() if DECISION_LOG_FILE.exists() else "# Decision Log\n"
    import re
    nums = [int(m) for m in re.findall(r"## Entry #(\d+)", txt)]
    nxt = (max(nums) + 1) if nums else 1
    with DECISION_LOG_FILE.open("a") as f:
        f.write(f"\n## Entry #{nxt} — {date.today().isoformat()}\n{body}\n")
    return nxt


def main():
    cfg = load_config()
    rows = load_rows()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    endorsed_set = set(cfg.get("alignment", {}).get("endorsed_instruments", []) or [])
    endorsed_count = sum(1 for r in rows if as_bool(r.get("uses_endorsed")))
    total = len(rows)

    buf = []
    log(buf, "=" * 60)
    log(buf, f"07_figures — {cfg['topic']['name']} — {total} trials")
    log(buf, "=" * 60)
    fig_category_split(rows, endorsed_count, total, buf)
    fig_frequency(rows, endorsed_set, buf)
    fig_concentration(rows, buf)
    fig_category_trend(rows, cfg, buf)
    fig_endorsed_uptake(rows, cfg, buf)
    fig_registrations(rows, buf)
    fig_nrsvas_prevalence(rows, buf)
    epoch_table(rows, cfg, buf)
    log(buf, "Wrote 7 figures + epoch_table.csv to figures/")

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text("\n".join(buf) + "\n")
    n = dlog(f"Standard figure set (`scripts/07_figures.py`). Wrote 7 figures + epoch "
             f"table to `figures/` for {cfg['topic']['name']} ({total} trials). "
             f"Time anchors: FDA 2006 + {len(endorsement_dates(cfg))} endorsement milestone(s).")
    print(f"Appended DECISION_LOG.md Entry #{n}")


if __name__ == "__main__":
    main()
