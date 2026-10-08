# -*- coding: utf-8 -*-
"""List the candidate documents and say, for each, what "unseen" means.

"分解器が見ていない対局と提出書類に限る" has two readings, and they select
different documents, so this script reports both instead of choosing:

``decomposer_unseen``
    The claim decomposition layer has never been run on this text. Measured
    from ``scripts/playtest/out/decomposer/``: every run so far used the four
    hand-written ``gold-01``..``gold-04`` fixtures, so **every real document
    is unseen under this reading.**

``pipeline_unseen``
    No part of Audit Core has processed this document before, so no judgment
    of it is already known to whoever picks the injection sites. The three
    cached filings all fail this: each has an expectation file, and the
    S100Z4Q1 run is the 91-claim baseline the 誤停止率 work is built on.

Why the difference matters: the injector chooses sites from a sealed seed, so
a known judgment cannot steer the choice. But the person reading the score
has seen S100Z4Q1's verdicts, and "I already know this document's weak
spots" is the kind of leak that does not show up in any count.

Usage::

    python3 select_documents.py --repo <repo root>
"""

import argparse
import json
import os
import subprocess
import sys

CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")

# Filings whose text the Adapter has already turned into claims, with the
# artefact that proves it. Keep this table literal: deriving it from a glob
# would quietly shrink when files move.
XBRL_PRIOR_USE = {
    "S100Z4Q1": ["core_expectation_1B.json", "core_expectation_1B_v2.json", "probe1B_S100Z4Q1.json", "c1g_first_run_1B_P6.json"],
    "S100Z4B6": ["core_expectation_5F.json", "probe5F_S100Z4B6.json", "c1g_first_run_5F_P6.json"],
    "S100YMFV": ["third_S100YMFV_P5F.json", "c1g_first_run_3rd_P6.json"],
}

SHOGI_PRIOR_USE = {
    "shogi-c5": ["scripts/playtest/out/c5/... (booklet and packet; the 5th round deliverable)"],
}


def decomposer_runs(repo):
    """Which documents the decomposition layer has actually been run on."""
    root = os.path.join(repo, "scripts", "playtest", "out", "decomposer")
    seen = set()
    if not os.path.isdir(root):
        # Distinguish "nothing has been run" from "the directory is not here".
        # scripts/playtest/out/ is gitignored, so in a fresh worktree this
        # path is simply absent and an empty answer means nothing at all.
        return None, root
    for run in sorted(os.listdir(root)):
        rp = os.path.join(root, run)
        if not os.path.isdir(rp):
            continue
        for seat in sorted(os.listdir(rp)):
            sp = os.path.join(rp, seat)
            if not os.path.isdir(sp):
                continue
            for doc in sorted(os.listdir(sp)):
                if os.path.isdir(os.path.join(sp, doc)):
                    seen.add(doc)
    return seen, root


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    repo = os.path.abspath(args.repo)

    seen, root = decomposer_runs(repo)
    if seen is None:
        sys.stderr.write(
            "REFUSING TO ANSWER: %s does not exist.\n"
            "scripts/playtest/out/ is gitignored, so a worktree has no copy of it. "
            "An empty 'seen' list here would mean 'not measured', not 'nothing was run'.\n"
            "Re-run with --repo pointing at the checkout that holds the decomposer runs.\n"
            % os.path.relpath(root, repo)
        )
        return 2
    cached = sorted(n[:-4] for n in os.listdir(CACHE)) if os.path.isdir(CACHE) else []

    rows = []
    for doc in SHOGI_PRIOR_USE:
        rows.append({
            "document_id": doc,
            "source": "shogi",
            "available_locally": True,
            "decomposer_unseen": doc not in seen,
            "pipeline_unseen": False,
            "prior_use": SHOGI_PRIOR_USE[doc],
            "note": "冊子の文は AI が書いた文。手を加えていない文で止まったものは (a) 誤停止 と (b) AI が本当に間違えていた に分かれる(第 2 便 問い 3)",
        })
    for doc in cached:
        rows.append({
            "document_id": doc,
            "source": "xbrl",
            "available_locally": True,
            "decomposer_unseen": doc not in seen,
            "pipeline_unseen": doc not in XBRL_PRIOR_USE,
            "prior_use": XBRL_PRIOR_USE.get(doc, []),
            "note": "提出書類の本文。人が書いて監査を受けた文であり、AI が書いた文ではない(第 2 便 問い 1)",
        })

    # Ranked: fewest prior artefacts first, so the least-known document is
    # the default pick when only decomposer_unseen is required.
    rows.sort(key=lambda r: (not r["pipeline_unseen"], len(r["prior_use"]), r["document_id"]))

    payload = {
        "decomposer_runs_root": os.path.relpath(root, repo),
        "documents_the_decomposer_has_seen": sorted(seen),
        "candidates": rows,
        "blocked": [{
            "what": "pipeline_unseen な提出書類",
            "why": "ローカルのキャッシュは 3 件で、3 件とも Adapter が処理済み。新しい docID は EDINET からの取得が要る",
            "cost": "EDINET API は無料だが、取得は人の判断(今回の指示は「API は使わない」)",
            "how": "EDINET_API_KEY を設定して adapters/xbrl/edinet.py fetch(docID) ― このツールは取得を行わない",
        }],
    }
    if args.json:
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=1)
        sys.stdout.write("\n")
        return 0

    print("decomposer has been run on: %s" % (", ".join(sorted(seen)) or "(nothing)"))
    print("  -> every real document below is unseen under the decomposer reading\n")
    print("%-11s %-6s %-11s %-10s %s" % ("document", "source", "decomp.新規", "pipeline新規", "prior artefacts"))
    for r in rows:
        print("%-11s %-6s %-11s %-10s %d" % (
            r["document_id"], r["source"],
            "yes" if r["decomposer_unseen"] else "no",
            "yes" if r["pipeline_unseen"] else "no",
            len(r["prior_use"]),
        ))
    print("\nblocked: %s" % payload["blocked"][0]["why"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
