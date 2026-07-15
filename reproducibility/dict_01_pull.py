#!/usr/bin/env python3
"""
scripts/dict_01_pull.py  —  Dictionary discovery: broad pull (Stage A, step 1).

Broad, deliberately over-inclusive pull of trial outcome text used to EMPIRICALLY
DERIVE the instrument dictionary. This is discovery, not the analytic cohort:

  - Runs the retrieval search from config/search.txt as expert query.term searches,
    honoring AREA[...] syntax (the raw line is passed straight to query.term). If the
    file holds MORE THAN ONE query string, each is run separately, combined, and
    de-duplicated by NCT.
  - Does NOT apply an interventional filter — observational studies are included on
    purpose, to mine the widest possible instrument vocabulary.
  - countTotal=true; full pagination via nextPageToken; asserts fetched == reported
    total PER STRING before anything is written.
  - Keeps, per trial: NCT id, the outcome-measure NAME field and the outcome
    DESCRIPTION field (primary + secondary + other outcomes), index-aligned.
  - Writes data/dict_raw.csv; prints per-string and combined counts.

Bin-2 note: config/search.txt also carries an `NCTIDS:` line of vetted trials. Those
are pulled by ID (batched) and folded into the same output, because dictionary
discovery should mine the outcome text of cohort trials too — otherwise the frozen
dictionary could miss instruments those trials use. To restrict discovery to the two
query strings only, comment out the Bin-2 block in main().
"""
import csv, json, re, time
from datetime import date
from pathlib import Path
import requests, yaml

ROOT = Path(__file__).resolve().parent.parent
SEARCH = ROOT / "config" / "search.txt"
OUT = ROOT / "data" / "dict_raw.csv"
LOG = ROOT / "qc_logs" / "dict_01_pull.log"
BASE = "https://clinicaltrials.gov/api/v2/studies"
PAGE_SIZE, TIMEOUT, RETRIES, BACKOFF, DELAY = 1000, 60, 3, 2, 0.2
FIELDS = ["nct_id", "outcome_measures", "outcome_descriptions"]

# CTG v2 rejects over-long request URLs (HTTP 414). The current root strings are well
# under this, so rather than silently splitting (which would complicate the per-string
# fetched==total assertion) we raise and ask the maintainer to split the line.
MAX_TERM_LEN = 3500


def logp(line, buf):
    print(line); buf.append(line)


def load_searches(path):
    """Parse search.txt. Returns (query_terms, nct_ids). '#' lines are ignored; a line
    starting 'NCTIDS:' is a by-ID list (Bin-2); everything else is a query.term string."""
    terms, ncts = [], []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.upper().startswith("NCTIDS:"):
            for tok in re.split(r"[,\s]+", line.split(":", 1)[1]):
                tok = tok.strip().upper()
                if not tok:
                    continue
                if not re.fullmatch(r"NCT\d{8}", tok):
                    raise ValueError(f"'{tok}' on an NCTIDS line is not a valid NCT ID")
                ncts.append(tok)
        else:
            terms.append(line)
    if not terms and not ncts:
        raise ValueError(f"No search strings or NCT IDs in {path}")
    seen = set()
    ncts = [n for n in ncts if not (n in seen or seen.add(n))]
    return terms, ncts


def req(params):
    last = None
    for a in range(1, RETRIES + 1):
        try:
            r = requests.get(BASE, params=params, timeout=TIMEOUT)
            if r.status_code == 429 or r.status_code >= 500:
                raise requests.HTTPError(f"retryable {r.status_code}")
            r.raise_for_status(); return r.json()
        except requests.RequestException as e:
            last = e
            if a == RETRIES:
                break
            time.sleep(BACKOFF * a)
    raise RuntimeError(f"request failed after {RETRIES}: {last}")


def fetch_term(term):
    """Paginate one query.term string fully. No interventional filter (broad
    discovery). Returns (studies, total, pages). Asserts fetched == totalCount."""
    if len(term) > MAX_TERM_LEN:
        raise ValueError(f"query string is {len(term)} chars (> {MAX_TERM_LEN}); split the "
                         f"line in search.txt so each string stays under the URL limit")
    studies, total, token, pages = [], None, None, 0
    while True:
        params = {"query.term": term, "countTotal": "true", "pageSize": PAGE_SIZE}
        if token:
            params["pageToken"] = token
        data = req(params)
        if total is None:
            total = data.get("totalCount")
            if total is None:
                raise RuntimeError("no totalCount despite countTotal=true")
        studies += data.get("studies", []); pages += 1
        token = data.get("nextPageToken")
        if not token:
            break
        time.sleep(DELAY)
    if len(studies) != total:
        raise AssertionError(f"pagination mismatch for {term[:60]!r}: fetched {len(studies)} vs total {total}")
    return studies, total, pages


def fetch_ncts(nct_ids, buf):
    """Pull vetted Bin-2 trials directly by NCT ID (batched, no study-type filter).
    Warns on any requested ID the API does not return."""
    if not nct_ids:
        return []
    PER = 300
    batches = [nct_ids[i:i + PER] for i in range(0, len(nct_ids), PER)]
    logp(f"[Bin-2 by NCT ID] {len(nct_ids)} trials"
         + (f" in {len(batches)} batches" if len(batches) > 1 else ""), buf)
    all_studies = []
    for j, b in enumerate(batches, 1):
        studies, token = [], None
        while True:
            params = {"filter.ids": ",".join(b), "countTotal": "true", "pageSize": PAGE_SIZE}
            if token:
                params["pageToken"] = token
            data = req(params)
            studies += data.get("studies", [])
            token = data.get("nextPageToken")
            if not token:
                break
            time.sleep(DELAY)
        if len(batches) > 1:
            logp(f"    id-batch {j}/{len(batches)}: requested {len(b)}, returned {len(studies)}", buf)
        all_studies += studies
    returned = {s["protocolSection"]["identificationModule"]["nctId"] for s in all_studies}
    missing = [n for n in nct_ids if n not in returned]
    if missing:
        logp(f"  WARNING: {len(missing)} requested NCT ID(s) not returned by the API: "
             f"{', '.join(missing[:10])}{'...' if len(missing) > 10 else ''}", buf)
    return all_studies


def dedupe(studies):
    u, d = {}, 0
    for s in studies:
        n = s["protocolSection"]["identificationModule"]["nctId"]
        if n in u:
            d += 1
        else:
            u[n] = s
    return u, d


def row(nct, s):
    """Emit NCT plus the outcome NAME field and DESCRIPTION field, across primary +
    secondary + other outcomes, as two index-aligned JSON arrays."""
    om = s.get("protocolSection", {}).get("outcomesModule", {})
    outcomes = (om.get("primaryOutcomes", []) or []) \
        + (om.get("secondaryOutcomes", []) or []) \
        + (om.get("otherOutcomes", []) or [])
    measures = [o.get("measure", "") for o in outcomes]
    descriptions = [o.get("description", "") for o in outcomes]
    return {"nct_id": nct,
            "outcome_measures": json.dumps(measures),
            "outcome_descriptions": json.dumps(descriptions)}


def main():
    buf = []
    logp("Dictionary discovery pull — broad (observational included, NO interventional filter)", buf)
    terms, bin2_ncts = load_searches(SEARCH)
    logp(f"Loaded {len(terms)} query string(s)"
         + (f" and {len(bin2_ncts)} Bin-2 NCT ID(s)" if bin2_ncts else "")
         + f" from {SEARCH.relative_to(ROOT)}\n", buf)

    per = []
    for i, t in enumerate(terms, 1):
        logp(f"[String {i}] {t[:80]}", buf)
        studies, total, pages = fetch_term(t)
        u, dd = dedupe(studies); per.append(u)
        logp(f"  total {total} | pages {pages} | unique {len(u)} | within-string dupes {dd}\n", buf)

    # Bin-2 vetted trials by NCT ID — folded into discovery so their outcome text is
    # mined too. Comment out this block to restrict discovery to the query strings only.
    if bin2_ncts:
        id_studies = fetch_ncts(bin2_ncts, buf)
        u, dd = dedupe(id_studies); per.append(u)
        logp(f"  unique {len(u)} from NCT-ID pull | within-list dupes {dd}\n", buf)

    combined, cross = {}, 0
    for u in per:
        for n, s in u.items():
            if n in combined:
                cross += 1
            else:
                combined[n] = s

    rows = [row(n, s) for n, s in combined.items()]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)

    logp(f"[Combined] cross-string/list dupes removed {cross} | final unique {len(combined)} "
         f"| rows written {len(rows)} -> {OUT.relative_to(ROOT)}", buf)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text("\n".join(buf) + "\n")


if __name__ == "__main__":
    main()
