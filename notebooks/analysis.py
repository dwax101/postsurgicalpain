# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.4
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # PRO Instruments Across Postsurgical Pain Trials — Interpretive Notebook
#
# **Phase 4 — interpretation, not generation.** Reads `data/detection_results.csv`
# (n = 948 reconciled trials; detection against the frozen 58-instrument dictionary
# `config/dictionary.py`). The standard figure set was already produced by
# `scripts/07_figures.py`; this notebook **references the PNGs in `figures/` and does
# NOT regenerate them**. Code cells recompute the headline numbers only for
# transparency/reproducibility (outputs are stripped from the committed notebook).
#
# **Framing (genre = exploratory descriptive).** The whole instrument distribution is
# the subject. The IMI-PainCare PROMPT endorsed set is treated as **one labeled example
# of heterogeneity — never as an adherence, guideline-concordance, or quality benchmark.**
# The two time anchors — the FDA PRO guidance (2006-10-11) and the PROMPT endorsement
# (2025-03-14) — are **reference lines, not filters or cut-offs**. All endorsement names
# remain `# VERIFY` against the PROMPT publication.

# %%
from pathlib import Path
from datetime import datetime
from collections import Counter

import pandas as pd
from IPython.display import Image, display

# This notebook lives in notebooks/; figures/ and data/ sit at the repo root.
REPO = Path.cwd()
while not (REPO / "figures").exists() and REPO != REPO.parent:
    REPO = REPO.parent
FIG = REPO / "figures"

df = pd.read_csv(REPO / "data" / "detection_results.csv").fillna("")
N = len(df)

def year_of(s):
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(str(s), fmt).year
        except ValueError:
            continue
    return None

def categorize(r):
    # Mirrors scripts/07_figures.py: named > matched-non-PRO > none. (The "vague"
    # band is empty here — detection_results carries no vague-descriptor flag.)
    if str(r["has_any_named_pro"]).strip().lower() == "true":
        return "Named PRO"
    if str(r["matched_instruments"]).strip():
        return "Matched non-PRO only"
    return "No PRO"

df["year"] = df["first_posted_date"].map(year_of)
df["category"] = df.apply(categorize, axis=1)
print(f"Loaded {N} trials; figures dir = {FIG}")

# %% [markdown]
# ## 1. The category split — and what the fragmentation says
#
# **Category split (`figures/01_category_split.png`).** Of 948 trials:
# **Named PRO 737 (77.7%)**, **No PRO 181 (19.1%)**, **matched a non-PRO instrument only
# 30 (3.2%)**. So roughly four in five trials name at least one patient-reported
# instrument our frozen dictionary detects; about one in five name none.
#
# **Fragmentation (`figures/02_instrument_frequency.png`, `03_concentration_curve.png`).**
# Across the cohort there are **52 distinct instruments** and **1,404 instrument-uses**,
# but the distribution is steeply concentrated: **NRS (343 trials, 24.4% of uses)** and
# **VAS (327, 23.3%)** alone account for ~48% of all uses, the **top-3 instruments cover
# 54%**, and just **3 instruments reach 50% of all uses**. Everything after the
# pain-intensity pair is a long, thin tail — BPI (9.6%), Quality of Recovery (6.4%), then
# a scatter of function, HRQoL, neuropathic, psych, and sleep measures each in only a few
# percent of trials.
#
# **What the fragmentation says.** The landscape is **bimodal**: a dominant generic
# pain-intensity duo (NRS + VAS) that almost every measuring trial reaches for, plus a
# fragmented tail of ~50 domain-specific instruments with little convergence among them.
# Read as an answer to "how are PRO instruments used across postsurgical pain trials":
# *almost everyone measures pain intensity with a simple 0–10 scale, and beyond that there
# is no shared instrument.* The ~19% "No PRO" band is trials whose **registry outcome
# text** names no dictionary instrument — this may be genuine absence, or an instrument
# named only in the full protocol/publication (a registry-text limitation, not proof of
# absence).

# %%
print(df["category"].value_counts().to_string(), "\n")

uses = Counter()
for s in df["matched_instruments"]:
    for inst in str(s).split("|"):
        if inst.strip():
            uses[inst.strip()] += 1
total_uses = sum(uses.values())

run, n50 = 0, 0
for rank, (_, v) in enumerate(uses.most_common(), 1):
    run += v
    if run / total_uses >= 0.5:
        n50 = rank
        break
print(f"{len(uses)} distinct instruments | {total_uses} instrument-uses | "
      f"top-{n50} cover 50% of uses")
print("Top 5:", uses.most_common(5))

for name in ("01_category_split.png", "02_instrument_frequency.png",
             "03_concentration_curve.png"):
    display(Image(filename=str(FIG / name)))

# %% [markdown]
# ## 2. The over-time category trend (with the 2006 and 2025 reference lines)
#
# **`figures/04_category_trend.png`** (denominator: `S1_registrations_per_year.png`).
# All 948 trials are dated; the window is **2000–2026**. The **Named-PRO share rises
# gradually**, from roughly **58–60% in the mid/late-2000s** to about **85% by 2020** and
# **83–87% in 2024–2026**, while the **"No PRO" band shrinks** correspondingly (~33–40%
# early → ~13–16% recent). Early years are **small-n** (2006 n=12, 2010 n=10), so those
# percentages are noisy; the annual denominator grows steeply over the window (S1).
#
# **Referencing the anchors.** The rise is a **smooth secular trend across the whole
# 25-year window** — already underway before the **FDA 2006** line and continuing through
# the **PROMPT 2025** line with **no visible step change at either anchor**. Descriptively:
# named-PRO reporting became steadily more common over time; this design (no control, no
# counterfactual) **cannot attribute** that drift to the guidance or the endorsement. The
# lines are context, not causes.

# %%
by_year = (df[df["year"] != None].copy()
           .assign(named=lambda d: d["category"].eq("Named PRO"))
           .groupby("year")
           .agg(trials=("nct_id", "size"), named_pct=("named", "mean")))
by_year["named_pct"] = (by_year["named_pct"] * 100).round(0)
print(by_year.to_string())

display(Image(filename=str(FIG / "04_category_trend.png")))
display(Image(filename=str(FIG / "S1_registrations_per_year.png")))

# %% [markdown]
# ## 3. Endorsed-instrument uptake — a heterogeneity example, *not* adherence
#
# **`figures/05_endorsed_uptake.png`** (and `S2_nrs_vas_prevalence.png`). **662 trials
# (69.8% of all; 89.8% of the 737 named-PRO trials)** use at least one endorsed
# instrument. But the composition matters: that "uptake" is **almost entirely NRS (343)
# and VAS (327)**. The genuinely PROMPT-specific endorsed items are **rare in the cohort**
# — **Pain Interference 42, OR-SDS 3, ASES 0**.
#
# **Why this is heterogeneity, not adherence.** "Alignment" here reduces to *"did the trial
# use NRS or VAS"* — instruments that were **already ubiquitous decades before** the 2025
# PROMPT endorsement (see `S2_nrs_vas_prevalence.png`). So the 69.8% is **not** evidence
# that trials adopted the PROMPT core set; it reflects the pre-existing dominance of
# generic pain-intensity scales. The PROMPT-*adapted* tools (ASES adaptation, OR-SDS
# adaptation) are essentially **absent** (ASES 0, OR-SDS 3). Because we kept every endorsed
# instrument in the frozen dictionary **regardless of frequency** (the endorsed-set-is-a-
# floor rule), that near-absence is a **real descriptive finding, not a detection gap**.
# This is exactly why the figure is labeled "descriptive": **alignment must never be read
# as adherence, guideline-concordance, or quality.**

# %%
endorsed_uses = Counter()
for s in df["matched_endorsed_instruments"]:
    for inst in str(s).split("|"):
        if inst.strip():
            endorsed_uses[inst.strip()] += 1

aligned = (df["uses_endorsed"].astype(str).str.lower() == "true").sum()
named = int(df["category"].eq("Named PRO").sum())
print(f"uses_endorsed: {aligned}  ({100*aligned/N:.1f}% of all; "
      f"{100*aligned/named:.1f}% of named-PRO trials)")
print("endorsed composition:", dict(endorsed_uses.most_common()))
print("ASES (endorsed) in cohort:",
      endorsed_uses.get("ASES (Amer. Shoulder & Elbow Surgeons)", 0), "trials")

display(Image(filename=str(FIG / "05_endorsed_uptake.png")))
display(Image(filename=str(FIG / "S2_nrs_vas_prevalence.png")))

# %% [markdown]
# ## 4. The epoch table (`figures/epoch_table.csv`)
#
# | Epoch | Named-PRO trials | Aligned trials | Alignment % |
# |---|---:|---:|---:|
# | Pre-IMI-PainCare PROMPT (<2025) | 587 | 521 | **88.8%** |
# | Post-IMI-PainCare PROMPT (≥2025) | 150 | 141 | **94.0%** |
#
# **Interpretation.** Alignment is **high in both epochs** and rises only **modestly
# (88.8% → 94.0%)** after the endorsement. This is **not** a "PROMPT worked" signal, for
# two reasons: (a) alignment was **already ~89% before the endorsement existed**, because
# it is driven by long-standing NRS/VAS use (Sections 2–3); and (b) the post-epoch is
# **short and small** — the endorsement is 2025-03 and the post band holds only 150
# named-PRO trials, so the estimate is immature and noisy. The table is a **descriptive
# split by epoch**, not a before/after causal comparison: there is no counterfactual, no
# control, and the "standard" is dominated by instruments that pre-date it.

# %%
epoch = pd.read_csv(FIG / "epoch_table.csv")
display(epoch)

# %% [markdown]
# ## Caveats carried through every panel above
#
# - **Time axis = registry first-posted date** (not trial start or publication date).
# - **Registry-text detection only** — the ~19% "No PRO" band may undercount instruments
#   named only in protocols/publications; it is not proof a trial measured no PRO.
# - **Endorsement names are `# VERIFY`** against the PROMPT publication; "Procedure-specific
#   physical function scale" was **excluded** from the endorsed set (no concrete instrument
#   to map it to — see `config/dictionary_derivation.md`).
# - **Alignment ≡ "uses an endorsed instrument (in practice, NRS/VAS)"** — a heterogeneity
#   descriptor, **not** adherence, concordance, or quality.
