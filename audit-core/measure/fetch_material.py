# -*- coding: utf-8 -*-
"""Pick and fetch an 有価証券報告書 that the Adapter has never processed.

Why this is a separate script from ``prepare_material.py``: fetching is the
only step in this package that touches the network and the only one that
needs a credential, so it is kept where it can be audited on its own.

**Cost.** The EDINET API is free of charge; there is no metered call here.
"費用 0 円" is preserved.

**Credential.** EDINET API v2 requires a Subscription-Key. Measured
2026-10-08: an unkeyed request to ``documents.json`` returns HTTP 200 with
``{"StatusCode": 401, "message": "Access denied due to invalid subscription
key..."}``. This script never reads, writes, prints or stores the key's
value -- it only passes ``os.environ["EDINET_API_KEY"]`` straight to the
request, and the value never appears in its output or in any file it writes.

**Which filings are excluded.** The three in ``ADAPTER_USED`` were used to
build the Adapter and the comparators, so their text shaped the code that
would be measured. Selection is otherwise by the sealed seed, not by hand.

Usage::

    export EDINET_API_KEY=...        # the operator sets this, not this script
    python3 fetch_material.py --list --from 2026-09-01 --to 2026-09-30
    python3 fetch_material.py --pick 2 --from 2026-09-01 --to 2026-09-30 \
        --seed-file SEED.json --out out/material
"""

import argparse
import datetime
import hashlib
import io
import json
import os
import random
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from inject import verify_seed_sealed, SealError  # noqa: E402

API = "https://api.edinet-fsa.go.jp/api/v2/"
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")

# Filings whose text shaped the Adapter and the comparators. Never selected.
ADAPTER_USED = {"S100Z4Q1", "S100Z4B6", "S100YMFV"}

# 有価証券報告書: ordinanceCode 010 (企業内容等の開示に関する内閣府令),
# docTypeCode 120 (有価証券報告書). Quarterly and amended filings are a
# different shape of document and are not what the measurement is about.
ORDINANCE = "010"
DOCTYPE = "120"


def _key():
    k = os.environ.get("EDINET_API_KEY")
    if not k:
        raise SystemExit(
            "EDINET_API_KEY is not set.\n"
            "EDINET API v2 requires a Subscription-Key; an unkeyed request returns\n"
            '  {"StatusCode": 401, "message": "Access denied due to invalid subscription key..."}\n'
            "The API itself is free of charge. Set the key in the environment and re-run:\n"
            "  export EDINET_API_KEY=...\n"
            "This script does not read the key from any file and never prints its value."
        )
    return k


def _get(path, params):
    q = dict(params)
    q["Subscription-Key"] = _key()
    url = API + path + "?" + urllib.parse.urlencode(q)
    with urllib.request.urlopen(url, timeout=120) as r:
        return r.read()


def _safe_url_for_log(path, params):
    """The URL with the key omitted, for printing."""
    return API + path + "?" + urllib.parse.urlencode(params)


def iter_days(a, b):
    d = datetime.date.fromisoformat(a)
    end = datetime.date.fromisoformat(b)
    while d <= end:
        yield d.isoformat()
        d += datetime.timedelta(days=1)


def list_filings(date_from, date_to):
    """Every 有価証券報告書 filed in the window, excluding ADAPTER_USED."""
    rows = []
    for day in iter_days(date_from, date_to):
        try:
            body = _get("documents.json", {"date": day, "type": 2})
        except urllib.error.HTTPError as e:
            print("  %s: HTTP %s (skipped)" % (day, e.code), file=sys.stderr)
            continue
        data = json.loads(body.decode("utf-8", "replace"))
        if data.get("metadata", {}).get("status") not in (None, "200"):
            print("  %s: status %s (skipped)" % (day, data.get("metadata", {}).get("status")), file=sys.stderr)
            continue
        for r in data.get("results") or []:
            if r.get("ordinanceCode") != ORDINANCE or r.get("docTypeCode") != DOCTYPE:
                continue
            if r.get("xbrlFlag") != "1":
                continue
            doc_id = r.get("docID")
            if not doc_id or doc_id in ADAPTER_USED:
                continue
            rows.append({
                "docID": doc_id,
                "filerName": r.get("filerName"),
                "secCode": r.get("secCode"),
                "periodEnd": r.get("periodEnd"),
                "submitDateTime": r.get("submitDateTime"),
                "date": day,
            })
    rows.sort(key=lambda r: (r["date"], r["docID"]))
    return rows


def fetch_zip(doc_id):
    """Download one filing's ZIP into the shared cache. Returns (path, sha256)."""
    body = _get("documents/%s" % doc_id, {"type": 1})
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, "%s.zip" % doc_id)
    with open(path, "wb") as fh:
        fh.write(body)
    return path, hashlib.sha256(body).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--from", dest="date_from", required=True)
    ap.add_argument("--to", dest="date_to", required=True)
    ap.add_argument("--list", action="store_true", help="only list the candidates")
    ap.add_argument("--pick", type=int, default=0, help="how many to fetch (1 or 2)")
    ap.add_argument("--seed-file", default=None, help="required with --pick")
    ap.add_argument("--out", default=None, help="prepare material into this directory after fetching")
    args = ap.parse_args(argv)

    print("listing %s" % _safe_url_for_log("documents.json", {"date": "<each day>", "type": 2}))
    rows = list_filings(args.date_from, args.date_to)
    print("candidates: %d (有価証券報告書 with XBRL, excluding %s)"
          % (len(rows), ", ".join(sorted(ADAPTER_USED))))
    for r in rows[:40]:
        print("  %s  %-10s  %s" % (r["docID"], r["periodEnd"] or "", (r["filerName"] or "")[:36]))
    if len(rows) > 40:
        print("  ... %d more" % (len(rows) - 40))

    if args.list or not args.pick:
        return 0
    if not rows:
        raise SystemExit("no candidate filing in %s..%s" % (args.date_from, args.date_to))
    if not args.seed_file:
        raise SystemExit("--pick requires --seed-file (the choice must come from the sealed seed)")

    seed, seal = verify_seed_sealed(args.seed_file)
    rng = random.Random("%s|edinet-pick|%s|%s" % (seed, args.date_from, args.date_to))
    chosen = rng.sample(rows, min(args.pick, len(rows)))

    picked = []
    for r in chosen:
        path, sha = fetch_zip(r["docID"])
        print("fetched %s -> %s (%d bytes, sha256 %s)"
              % (r["docID"], path, os.path.getsize(path), sha[:16]))
        picked.append(dict(r, zip_path=path, zip_sha256=sha))
        if args.out:
            import prepare_material
            prepare_material.main(["xbrl", "--zip", path, "--doc", r["docID"], "--out", args.out])

    here = os.path.dirname(os.path.abspath(__file__))
    rec = os.path.join(here, "material", "xbrl", "fetched.json")
    os.makedirs(os.path.dirname(rec), exist_ok=True)
    with io.open(rec, "w", encoding="utf-8") as fh:
        json.dump({
            "note": "EDINET から取得した提出書類。接続部分の開発に使ったものは除外してある。",
            "excluded_because_used_by_the_adapter": sorted(ADAPTER_USED),
            "window": [args.date_from, args.date_to],
            "candidate_count": len(rows),
            "selection": "封じた種から無作為(手で選んでいない)",
            "seal": seal,
            "picked": picked,
        }, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("record -> %s" % rec)
    return 0


if __name__ == "__main__":
    sys.exit(main())
