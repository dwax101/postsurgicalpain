#!/usr/bin/env python3
"""
scripts/01_extract.py  —  Extraction (config-driven).

Reads retrieval settings from config/topic_config.yaml. Supports BOTH retrieval
modes with the same code:
  retrieval.mode = expert_strings  -> run each expert search string from
      config/search.txt separately, combine, de-duplicate by NCT. (OBESITY)
  retrieval.mode = bins            -> run the root-term condition query built
      from config/search.txt (root term + bin-1 variants). (STANDARD topics)

In both modes: interventional-only filter applied at retrieval if configured,
full pagination with a fetched==totalCount assertion before any write, and one
row per trial written to data/raw_export.csv.
"""
import csv, json, re, sys, time, importlib.util
from datetime import date
from pathlib import Path
import requests, yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "topic_config.yaml"
OUT = ROOT / "data" / "raw_export.csv"
LOG = ROOT / "qc_logs" / "01_extract.log"
DLOG = ROOT / "DECISION_LOG.md"
BASE = "https://clinicaltrials.gov/api/v2/studies"
PAGE_SIZE, TIMEOUT, RETRIES, BACKOFF, DELAY = 1000, 60, 3, 2, 0.2
FIELDS = ["nct_id","brief_title","overall_status","first_posted_date","conditions","interventions",
          "lead_sponsor","study_type","primary_outcomes","secondary_outcomes"]


def logp(line, buf): print(line); buf.append(line)

def load_searches(path):
    """Read search.txt. Two kinds of non-comment lines are recognized:
      - a normal expert-search line (condition/bin-1), run as query.term
      - a line beginning 'NCTIDS:' followed by NCT IDs (bin-2 trials pulled
        directly by ID; robust against special characters in trial titles)
    Returns (search_terms, nct_ids)."""
    terms, ncts = [], []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.upper().startswith("NCTIDS:"):
            body = line.split(":", 1)[1]
            for tok in re.split(r"[,\s]+", body):
                tok = tok.strip().upper()
                if tok:
                    if not re.fullmatch(r"NCT\d{8}", tok):
                        raise ValueError(f"'{tok}' on an NCTIDS line is not a valid NCT ID "
                                         f"(expected NCT followed by 8 digits)")
                    ncts.append(tok)
        else:
            terms.append(line)
    if not terms and not ncts:
        raise ValueError(f"No search strings or NCT IDs in {path}")
    # de-duplicate NCTs while preserving order
    seen = set(); ncts = [n for n in ncts if not (n in seen or seen.add(n))]
    return terms, ncts

def fetch_ncts(nct_ids, buf):
    """Pull a set of trials directly by NCT ID via the API's id filter, in
    batches to stay under the URL length limit. Returns list of study dicts.
    NCT IDs contain no special characters, so this is robust where full-title
    title matching is not."""
    if not nct_ids:
        return []
    # ~11 chars per id + separator; keep each batch well under the URL limit
    PER = 300
    batches = [nct_ids[i:i+PER] for i in range(0, len(nct_ids), PER)]
    logp(f"[Bin-2 by NCT ID] {len(nct_ids)} trials"
         + (f" in {len(batches)} batches" if len(batches) > 1 else ""), buf)
    all_studies = []
    for j, b in enumerate(batches, 1):
        # CTG v2 accepts a comma-separated id list on filter.ids
        studies, token, pages = [], None, 0
        while True:
            params = {"filter.ids": ",".join(b), "countTotal": "true", "pageSize": PAGE_SIZE}
            if token: params["pageToken"] = token
            data = req(params)
            studies += data.get("studies", []); pages += 1
            token = data.get("nextPageToken")
            if not token: break
            time.sleep(DELAY)
        if len(batches) > 1:
            logp(f"    id-batch {j}/{len(batches)}: requested {len(b)}, returned {len(studies)}", buf)
        all_studies += studies
    returned = {s["protocolSection"]["identificationModule"]["nctId"] for s in all_studies}
    missing = [n for n in nct_ids if n not in returned]
    if missing:
        logp(f"  WARNING: {len(missing)} requested NCT ID(s) were not returned by the API: "
             f"{', '.join(missing[:10])}{'...' if len(missing)>10 else ''}. These will be "
             f"absent from the cohort; check they are valid and public.", buf)
    return all_studies

def req(params):
    last = None
    for a in range(1, RETRIES+1):
        try:
            r = requests.get(BASE, params=params, timeout=TIMEOUT)
            if r.status_code == 429 or r.status_code >= 500:
                raise requests.HTTPError(f"retryable {r.status_code}")
            r.raise_for_status(); return r.json()
        except requests.RequestException as e:
            last = e
            if a == RETRIES: break
            time.sleep(BACKOFF*a)
    raise RuntimeError(f"request failed after {RETRIES}: {last}")

# Maximum length (characters) we allow for a single query.term value before we split
# it. ClinicalTrials.gov rejects over-long request URLs with HTTP 414. Full-title
# bin-2 lists can push a single search past that limit, so we split proactively.
# This is deliberately conservative to leave room for the rest of the URL.
MAX_TERM_LEN = 3500

def _find_area_groups(term):
    """Find every  AREA[Field] ( ... )  group, correctly handling parentheses
    that appear INSIDE the OR-items (e.g. "COPD Exacerbation (AECOPD)" or a title
    containing "(COPD)"). Returns a list of dicts with the field prefix, the inner
    text, and the start/end offsets of the whole group in `term`. A plain regex
    cannot do this because inner items contain unbalanced-looking parentheses;
    we walk the string and track paren depth instead."""
    groups = []
    for m in re.finditer(r'AREA\[[^\]]+\]\s*\(', term):
        prefix_end = m.end()          # position just after the opening '('
        depth = 1
        i = prefix_end
        while i < len(term) and depth > 0:
            if term[i] == '(':
                depth += 1
            elif term[i] == ')':
                depth -= 1
            i += 1
        if depth == 0:
            groups.append({
                "prefix": term[m.start():prefix_end],      # 'AREA[Field] ('
                "inner": term[prefix_end:i-1],             # content between the outer parens
                "start": m.start(),
                "end": i,                                  # position just after the closing ')'
            })
    return groups

def _split_items(inner):
    """Split an OR-list on top-level ' OR ' only, ignoring ' OR ' that sits inside
    a parenthesized part of an item."""
    items, depth, buf = [], 0, ""
    tokens = re.split(r'(\s+OR\s+|\(|\))', inner)
    for tok in tokens:
        if tok == '(':
            depth += 1; buf += tok
        elif tok == ')':
            depth -= 1; buf += tok
        elif re.fullmatch(r'\s+OR\s+', tok or "") and depth == 0:
            if buf.strip(): items.append(buf.strip())
            buf = ""
        else:
            buf += tok
    if buf.strip():
        items.append(buf.strip())
    return items

def split_or_group(term):
    """If a search term is too long, split it into several shorter terms that
    together cover the same records, then let NCT de-duplication recombine them.

    The term has the shape
        AREA[FieldA] (x OR y OR ...) OR AREA[FieldB] (a OR b OR ...)
    We split the LARGEST bracketed OR-group into chunks and emit one term per
    chunk (carrying the other groups along unchanged). A trial matched by more
    than one chunk is de-duplicated downstream, so the combined result is
    identical to the un-split search. Parentheses inside items are handled."""
    if len(term) <= MAX_TERM_LEN:
        return [term]

    groups = _find_area_groups(term)
    if not groups:
        return [term]

    target = max(groups, key=lambda g: len(g["inner"]))
    items = _split_items(target["inner"])
    if len(items) <= 1:
        return [term]

    before = term[:target["start"]]
    after = term[target["end"]:]
    prefix = target["prefix"]                      # 'AREA[Field] ('

    fixed_len = len(before) + len(after) + len(prefix) + 1   # +1 for ')'
    avg = max(1, sum(len(it) for it in items)//len(items) + 4)
    per_chunk = max(1, (MAX_TERM_LEN - fixed_len) // avg)

    chunks = [items[i:i+per_chunk] for i in range(0, len(items), per_chunk)]
    out = []
    for ch in chunks:
        grp = prefix + " OR ".join(ch) + ")"
        rebuilt = before + grp + after
        if len(rebuilt) > MAX_TERM_LEN and len(ch) > 1:
            out.extend(split_or_group(rebuilt))
        else:
            out.append(rebuilt)
    return out

def fetch(term, interventional):
    studies, total, token, pages = [], None, None, 0
    while True:
        params = {"query.term": term, "countTotal": "true", "pageSize": PAGE_SIZE}
        if interventional: params["filter.advanced"] = "AREA[StudyType]INTERVENTIONAL"
        if token: params["pageToken"] = token
        data = req(params)
        if total is None:
            total = data.get("totalCount")
            if total is None: raise RuntimeError("no totalCount despite countTotal=true")
        studies += data.get("studies", []); pages += 1
        token = data.get("nextPageToken")
        if not token: break
        time.sleep(DELAY)
    if len(studies) != total:
        raise AssertionError(f"pagination mismatch for {term!r}: fetched {len(studies)} vs total {total}")
    return studies, total, pages

def fetch_search(term, interventional, buf):
    """Fetch one logical search, auto-splitting it into batches if the URL would
    be too long. Returns (all_studies, n_batches). De-duplication happens upstream."""
    pieces = split_or_group(term)
    if len(pieces) > 1:
        logp(f"  search too long ({len(term)} chars) — auto-split into {len(pieces)} "
             f"batches to stay under the API URL limit; results are combined and "
             f"de-duplicated by NCT.", buf)
    all_studies = []
    for j, p in enumerate(pieces, 1):
        studies, total, pages = fetch(p, interventional)
        if len(pieces) > 1:
            logp(f"    batch {j}/{len(pieces)}: {total} records, {pages} page(s)", buf)
        all_studies += studies
    return all_studies, len(pieces)

def dedupe(studies):
    u, d = {}, 0
    for s in studies:
        n = s["protocolSection"]["identificationModule"]["nctId"]
        if n in u: d += 1
        else: u[n] = s
    return u, d

def outj(outcomes):
    return json.dumps([{"measure": o.get("measure",""), "description": o.get("description","")} for o in outcomes])

def row(nct, s):
    ps = s.get("protocolSection", {})
    idm, st, cm = ps.get("identificationModule",{}), ps.get("statusModule",{}), ps.get("conditionsModule",{})
    am, sm, dm, om = ps.get("armsInterventionsModule",{}), ps.get("sponsorCollaboratorsModule",{}), ps.get("designModule",{}), ps.get("outcomesModule",{})
    iv = "|".join(f"{i.get('type','')}: {i.get('name','')}" for i in am.get("interventions",[]))
    # first-posted date = when the registration went public on ClinicalTrials.gov.
    # This is the time axis for all descriptive over-time figures. The statusModule
    # is already being read for overallStatus; the date lives in the same module.
    first_posted = st.get("studyFirstPostDateStruct",{}).get("date","")
    return {"nct_id":nct,"brief_title":idm.get("briefTitle",""),"overall_status":st.get("overallStatus",""),
            "first_posted_date":first_posted,
            "conditions":"|".join(cm.get("conditions",[])),"interventions":iv,
            "lead_sponsor":sm.get("leadSponsor",{}).get("name",""),"study_type":dm.get("studyType",""),
            "primary_outcomes":outj(om.get("primaryOutcomes",[])),"secondary_outcomes":outj(om.get("secondaryOutcomes",[]))}

def dlog(body):
    t = DLOG.read_text(); nums=[int(n) for n in re.findall(r"^## Entry #(\d+)", t, re.MULTILINE)]
    nxt = max(nums, default=0)+1
    with DLOG.open("a") as f: f.write(f"\n## Entry #{nxt} — {date.today().isoformat()}\n{body}\n")
    return nxt

def main():
    cfg = yaml.safe_load(CONFIG.read_text())
    rc = cfg["retrieval"]
    search_file = ROOT / rc["expert_strings_file"] if rc["mode"]=="expert_strings" else ROOT / "config" / "search.txt"
    interventional = bool(rc.get("interventional_only", True))
    buf = []
    logp(f"Retrieval mode: {rc['mode']}   interventional_only: {interventional}", buf)
    terms, bin2_ncts = load_searches(search_file)
    logp(f"Loaded {len(terms)} search string(s)"
         + (f" and {len(bin2_ncts)} bin-2 NCT ID(s)" if bin2_ncts else "")
         + f" from {search_file.relative_to(ROOT)}\n", buf)
    if rc["mode"]=="expert_strings" and rc.get("expert_strings_count"):
        assert len(terms)==rc["expert_strings_count"], \
            f"config says {rc['expert_strings_count']} strings but search.txt has {len(terms)}"

    per, summ = [], []
    for i, t in enumerate(terms, 1):
        logp(f"[Search {i}] {t[:80]}", buf)
        studies, nbatch = fetch_search(t, interventional, buf)
        u, dd = dedupe(studies); per.append(u)
        summ.append((len(u)+dd, nbatch, len(u), dd))
        logp(f"  unique {len(u)} | within-search dupes {dd}"
             + (f" | {nbatch} batches" if nbatch > 1 else "") + "\n", buf)

    # bin-2 trials pulled directly by NCT ID (robust against title punctuation).
    # NOTE: these are pulled by ID regardless of study type — they are trials the
    # team explicitly vetted for inclusion. The interventional filter is applied to
    # the CONDITION search, not to an explicit include-by-ID list.
    if bin2_ncts:
        id_studies = fetch_ncts(bin2_ncts, buf)
        u, dd = dedupe(id_studies); per.append(u)
        logp(f"  unique {len(u)} from NCT-ID pull | within-list dupes {dd}\n", buf)

    combined, cross = {}, 0
    for u in per:
        for n, s in u.items():
            if n in combined: cross += 1
            else: combined[n] = s
    rows = [row(n, s) for n, s in combined.items()]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)

    logp(f"[Combined] cross-search dupes removed {cross} | final unique {len(combined)} | rows written {len(rows)}", buf)
    LOG.parent.mkdir(parents=True, exist_ok=True); LOG.write_text("\n".join(buf)+"\n")
    n = dlog(f"Extraction (`scripts/01_extract.py`, mode={rc['mode']}, interventional={interventional}). "
             f"{len(terms)} search string(s); cross-search dupes removed {cross}; final {len(combined)} trials "
             f"to `data/raw_export.csv`. Pagination asserted == totalCount per string before write.")
    print(f"Appended DECISION_LOG.md Entry #{n}")

if __name__ == "__main__": main()
