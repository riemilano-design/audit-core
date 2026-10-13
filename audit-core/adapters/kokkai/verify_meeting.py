# -*- coding: utf-8 -*-
"""CLI: 席の claims(要約の文 + 添えた根拠)を会議録と照らして、claim ごと・
検査ごとの state を返す入口。

順は ``adapters.xbrl.verify_document`` と同じ:
``load_meeting -> make_resolver -> register_all -> build_recipes -> verify_all``。
判定規則は足さない。claim の state は、その claim の検査(発言者・引用・数)の
state を **字で決めた順** で畳む(``CLAIM_STATE_RULE``)。

使い方::

    python3 -m adapters.kokkai.verify_meeting --meeting fixtures/kokkai/meeting_<issueID>.json \
        --summary fixtures/kokkai/summary_<issueID>_seat.json --out out.json

通信しない。
"""

import argparse
import hashlib
import io
import json
import os
import subprocess
import sys

import audit_core as core

from . import load as L
from . import recipes as R
from . import registry_setup as RS
from . import resolve as RV

_HERE = os.path.dirname(os.path.abspath(__file__))
_CORE_DIR = os.path.join(os.path.dirname(os.path.dirname(_HERE)), "core", "py", "audit_core")

# **字で留める。** claim の state は検査の state をこの順で畳む:
CLAIM_STATE_RULE = (
    "claim の検査(発言者・引用・数)の state のうち、1 つでも POINTER_NOT_FOUND なら POINTER_NOT_FOUND。"
    "無ければ、1 つでも VALUE_MISMATCH なら VALUE_MISMATCH。"
    "無ければ、1 つでも UNVERIFIABLE なら UNVERIFIABLE。"
    "全部 GROUNDED なら GROUNDED。検査が 0 件の claim は無い(発言者の検査は必ず作る)。"
)
_FOLD_ORDER = ("POINTER_NOT_FOUND", "VALUE_MISMATCH", "UNVERIFIABLE")

CHECK_FIELDS = ("id", "claim_id", "check", "subject", "value", "unit", "word", "state",
                "pointers", "reason", "recomputed", "detail")
CLAIM_FIELDS = ("id", "text", "speech_order", "speaker", "state", "checks")


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def _py_digest(directory):
    rows = []
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".py"):
            continue
        with open(os.path.join(directory, name), "rb") as fh:
            rows.append("%s\t%s" % (name, sha256_bytes(fh.read())))
    return sha256_bytes("\n".join(rows).encode("utf-8")), len(rows)


def _git_commit():
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=_HERE,
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except OSError:
        return None
    if out.returncode != 0:
        return None
    return out.stdout.decode("ascii", "replace").strip() or None


def engine_fingerprint():
    a_sha, a_n = _py_digest(_HERE)
    c_sha, c_n = _py_digest(_CORE_DIR)
    return {"adapter_kokkai_py_sha256": a_sha, "adapter_kokkai_py_files": a_n,
            "core_py_sha256": c_sha, "core_py_files": c_n, "git_commit": _git_commit()}


def fold_claim_state(check_states):
    """**CLAIM_STATE_RULE そのまま。**"""

    if not check_states:
        raise ValueError("検査が 0 件の claim")
    for st in _FOLD_ORDER:
        if st in check_states:
            return st
    return "GROUNDED"


def verify_meeting(meeting_data, summary):
    """``meeting_data`` は API の応答(dict)、``summary`` は席の JSON(dict)。出力の dict を返す。"""

    meeting = L.index_meeting(meeting_data)
    if summary.get("issueID") != meeting["issueID"]:
        raise ValueError("issueID が違う: summary=%r meeting=%r" % (summary.get("issueID"), meeting["issueID"]))

    resolver = RV.make_resolver(meeting)
    registry = RS.register_all(core.Registry.default())
    recipe_list = R.build_recipes(summary)
    results = core.verify_all(recipe_list, resolver, registry)
    by_id = {r.claim_id: r for r in results}

    checks = []
    per_claim = {}
    for recipe in recipe_list:
        claim = recipe.claim
        result = by_id[claim.id]
        row = {
            "id": claim.id,
            "claim_id": claim.provenance["claim_id"],
            "check": claim.provenance["check"],
            "subject": claim.subject,
            "value": claim.value,
            "unit": claim.unit,
            "word": claim.provenance.get("word"),
            "state": result.state.name,
            "pointers": [str(p) for p in result.pointers],
            "reason": result.reason,
            "recomputed": result.recomputed,
            "detail": dict((result.provenance.get("comparison") or {})),
        }
        checks.append({k: row[k] for k in CHECK_FIELDS})
        per_claim.setdefault(row["claim_id"], []).append(row)

    claims_out = []
    counts = {}
    for c in summary.get("claims") or []:
        rows = per_claim.get(c["id"], [])
        state = fold_claim_state([r["state"] for r in rows])
        counts[state] = counts.get(state, 0) + 1
        claims_out.append({
            "id": c["id"], "text": c.get("text"), "speech_order": c.get("speech_order"),
            "speaker": c.get("speaker"), "state": state,
            "checks": {r["check"]: r["state"] for r in rows},
        })

    check_counts = {}
    for row in checks:
        check_counts[row["state"]] = check_counts.get(row["state"], 0) + 1

    return {
        "tool": "adapters.kokkai.verify_meeting",
        "engine": engine_fingerprint(),
        "input": {
            "meeting": meeting["meta"],
            "meeting_sha256": sha256_bytes(json.dumps(meeting_data, ensure_ascii=False, sort_keys=True).encode("utf-8")),
            "speeches": len(meeting["speeches"]),
            "summary_written_by": summary.get("written_by"),
            "summary_sha256": sha256_bytes(json.dumps(summary, ensure_ascii=False, sort_keys=True).encode("utf-8")),
        },
        "document": {
            "claims": len(claims_out),
            "states": {k: counts[k] for k in sorted(counts)},
            "checks": len(checks),
            "check_states": {k: check_counts[k] for k in sorted(check_counts)},
            "rule": CLAIM_STATE_RULE,
        },
        "claims": claims_out,
        "checks": checks,
    }


def dumps(out):
    return json.dumps(out, ensure_ascii=False, indent=1, sort_keys=False) + "\n"


def _read_json(path):
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--meeting", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = verify_meeting(_read_json(a.meeting), _read_json(a.summary))
    with io.open(a.out, "w", encoding="utf-8") as fh:
        fh.write(dumps(out))
    d = out["document"]
    print("written: %s  claims=%d %s  checks=%d %s" % (a.out, d["claims"], d["states"], d["checks"], d["check_states"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
