# DISCREPANCY_LOG

## 2026-07-14 — Alignment endorsed-set names do not match frozen dictionary canonicals — RESOLVED 2026-07-14
**RESOLVED 2026-07-14** (DECISION_LOG Entry #4): `config/topic_config.yaml →
alignment.endorsed_instruments` was updated to the EXACT 5 canonical strings of the frozen
dictionary's `endorsed=True` entries (VAS, NRS, Pain Interference, ASES, ORSDS); the frozen
`config/dictionary.py` was NOT modified. 3-line check confirms 5 = 5, character-for-character.
"Procedure-specific physical function scale" was EXCLUDED by decision (DECISION_LOG #4),
not left open. The stale copy of the endorsement names in
`time_anchors.endorsement_milestones[0].instruments` was reconciled to the same 5 frozen
canonicals (DECISION_LOG #5); all three sets now equal, 5 = 5 = 5. No open items remain
for this discrepancy (endorsement names stay `# VERIFY` against the PROMPT publication).

--- original entry ---

`scripts/04_detect.py → is_aligned()` (mode `any_of`) computes alignment by intersecting
`config/topic_config.yaml → alignment.endorsed_instruments` (strings) with the set of
matched dictionary **canonical names**. The config strings ("Numerical Rating Scale",
"NRS", "Pain interference", "ASES IMI PROMPT adaptation", "OR-SDS IMI PROMPT adaptation",
"Procedure-specific physical/pain scales") do NOT equal the frozen canonicals ("Numeric
Rating Scale (NRS)", "Pain Interference (PROMIS/BPI domain)", "ASES (Amer. Shoulder &
Elbow Surgeons)", "Opioid-Related Symptom Distress Scale (ORSDS)", …).

**Effect:** `uses_endorsed` (the alignment column) would read 0% by construction, a false
"finding." The dictionary `endorsed` flag (driving `matched_endorsed_instruments`) is
correct and unaffected.

**Fix needed before detection runs:** reconcile `alignment.endorsed_instruments` to the
frozen canonical names, OR change `is_aligned()` to use the dictionary `endorsed` flag.
Config endorsement names are also `# VERIFY` pending the PROMPT publication. Not changed
here (config is owned separately; frozen dictionary must not change). See
config/dictionary_derivation.md §6.
