# -*- coding: utf-8 -*-
"""CLI: **1 書類を実際に検証して、Claim ごとの state・pointer・reason を返す入口。**

人間の決定(2026-10-13、第 3 段階「まず内部道具として動く入口を 1 本作る」)。
``run.py`` は Claim の層(結果なし)しか書かないので、入力から判定までを
一貫して回す経路が本番側に無かった。これがその 1 本。

**新しい判定規則は入れない。** 既存の関数を、試験の補助(``tests/golden/_instrument.py``)
と**同じ順**で呼ぶだけ::

    load_instance -> make_resolver -> register_all -> build_recipes -> verify_all

足したのは**書類レベルの旗 1 つ**だけ(人間が承認した文面、``DOC_UNVERIFIABLE_RULE``)。
Claim 個別の state は変えない。

**候補の欄(封 ``docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md``、人間の承認 2026-10-30)。** 出力の Claim に
``candidate`` を 1 欄足した(末尾)。``reason`` が ``no_same_value`` で ``provenance`` に ``no_same_value`` の鍵が在る行だけ
``{"pointer", "value", "basis"}``、他は ``None``(欄は常に在る)。旗が偽の profile では全行 ``None``(P27C だけが真)。
state・reason・pointers・recomputed は変えない。候補は「止めた行で道具が見ていた fact」で、正しさは測っていない。

使い方::

    python3 -m adapters.xbrl.verify_document --zip ~/.cache/audit-core/edinet/S100Z4N9.zip --out out.json
    python3 -m adapters.xbrl.verify_document --zip <書類.zip> --text <文章.txt> --out out.json
    python3 -m adapters.xbrl.verify_document --doc S100Z4N9 --out out.json      # キャッシュから

``--profile`` を省くと ``vocabulary.DEFAULT_PROFILE``(いまは P27。P20 → P21 → P22 → P26 → P27 の履歴と根拠は vocabulary.py の注記。この行は 2026-10-28 の人間の委任「君に任せるよ」で直した)。
``--text`` を渡すと、その書類の経営分析の節をその文章で差し替えてから検証する
(差し替えは ``prose.build_modified_zip``。開発書類の測定と同じ方法)。

通信しない。EDINET に触らない(ZIP は手元の file だけ)。
"""

import argparse
import hashlib
import io
import json
import os
import subprocess
import sys

import audit_core as core

from . import instance as I
from . import prose as PR
from . import recipes as R
from . import registry_setup as RS
from . import resolve as RV
from . import vocabulary as V

_HERE = os.path.dirname(os.path.abspath(__file__))
_ADAPTER_DIR = _HERE
_CORE_DIR = os.path.join(os.path.dirname(os.path.dirname(_HERE)), "core", "py", "audit_core")
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")

# **人間が承認した文面(2026-10-13)。字で留める。**
# 変えるには人間の決定と DECISION_LOG の項目が要る。
DOC_UNVERIFIABLE_RULE = (
    "Claim 件数が 0 件の場合、書類レベルを UNVERIFIABLE とする。"
    "Claim 件数が 1 件以上の場合、GROUNDED 件数が 0 件、かつ "
    "POINTER_NOT_FOUND 件数 ÷ 全 Claim 件数が 0.5 を超える場合、書類レベルを UNVERIFIABLE とする。"
    "それ以外は、この規則によって UNVERIFIABLE とは判定しない。"
    "Claim 個別の state は変更しない。"
)
DOC_UNVERIFIABLE_PNF_THRESHOLD = 0.5

# 出力の Claim の欄(**並びを字で固定する**。byte の安定のため)
CLAIM_FIELDS = ("id", "kind", "form", "subject", "value", "unit", "word", "span",
                "state", "pointers", "reason", "recomputed", "candidate")


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def _py_digest(directory):
    """ディレクトリ直下の .py の内容から作る指紋(git が無くても決まる)。"""

    rows = []
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".py"):
            continue
        with open(os.path.join(directory, name), "rb") as fh:
            rows.append("%s\t%s" % (name, sha256_bytes(fh.read())))
    return sha256_bytes("\n".join(rows).encode("utf-8")), len(rows)


def _git_commit():
    """取れなければ ``None``(環境によって取れない。出力の再現性を壊さない)。"""

    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=_HERE,
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except OSError:
        return None
    if out.returncode != 0:
        return None
    return out.stdout.decode("ascii", "replace").strip() or None


def engine_fingerprint():
    """``adapters/xbrl`` と Core の .py の内容から作る指紋。git に依存しない。"""

    a_sha, a_n = _py_digest(_ADAPTER_DIR)
    c_sha, c_n = _py_digest(_CORE_DIR)
    return {
        "adapter_xbrl_py_sha256": a_sha, "adapter_xbrl_py_files": a_n,
        "core_py_sha256": c_sha, "core_py_files": c_n,
        "git_commit": _git_commit(),
    }


def document_level(counts, total):
    """**承認された規則そのまま。** ``(unverifiable, 理由)``。"""

    if total == 0:
        return True, "claims=0"
    if counts.get("GROUNDED", 0) == 0:
        share = counts.get("POINTER_NOT_FOUND", 0) / float(total)
        if share > DOC_UNVERIFIABLE_PNF_THRESHOLD:
            return True, "grounded=0 and pointer_not_found/claims=%.4f > %s" % (
                share, DOC_UNVERIFIABLE_PNF_THRESHOLD)
    return False, None


def verify_document(zip_bytes, profile_name=None, text=None):
    """1 書類を検証して、出力の辞書を返す(file は書かない)。"""

    profile_name = profile_name or V.DEFAULT_PROFILE
    if profile_name not in V.PROFILES:
        raise ValueError("unknown profile: %s" % profile_name)
    profile = V.PROFILES[profile_name]

    source_sha = sha256_bytes(zip_bytes)
    replaced = None
    if text is not None:
        zip_bytes, element, member = PR.build_modified_zip(zip_bytes, text)
        replaced = {"element": element, "member": member,
                    "text_sha256": sha256_bytes(text.encode("utf-8")),
                    "text_chars": len(text)}

    # **試験の補助(tests/golden/_instrument.run_verification)と同じ順。**
    inst = I.load_instance(zip_bytes)
    resolver = RV.make_resolver(inst["facts"])
    registry = RS.register_all(core.Registry.default())
    recipe_list = R.build_recipes(zip_bytes, profile)
    results = core.verify_all(recipe_list, resolver, registry)
    by_id = {r.claim_id: r for r in results}

    claims, counts = [], {}
    for recipe in recipe_list:
        claim = recipe.claim
        result = by_id[claim.id]
        counts[result.state.name] = counts.get(result.state.name, 0) + 1
        row = {
            "id": claim.id,
            "kind": claim.provenance.get("kind"),
            "form": claim.form.value,
            "subject": claim.subject,
            "value": claim.value,
            "unit": claim.unit,
            "word": claim.provenance.get("word"),
            "span": claim.provenance.get("span"),
            "state": result.state.name,
            "pointers": [(p if isinstance(p, str) else p.scheme + ":" + p.locator)
                         for p in result.pointers],
            "reason": result.reason,
            "recomputed": result.recomputed,
            "candidate": None,
        }
        if getattr(profile, "unnamed_candidate_2026_10_29", False) and result.reason == R.NO_SAME_VALUE:
            nsv = claim.provenance.get("no_same_value")
            if nsv is not None:
                row["candidate"] = {"pointer": nsv["named"], "value": nsv["value"], "basis": R.NO_SAME_VALUE}
        claims.append({k: row[k] for k in CLAIM_FIELDS})

    total = len(claims)
    unverifiable, why = document_level(counts, total)
    return {
        "tool": "adapters.xbrl.verify_document",
        "engine": engine_fingerprint(),
        "profile": profile_name,
        "input": {"zip_sha256": source_sha, "zip_bytes": len(zip_bytes),
                  "instance_source": inst["source"], "facts": len(inst["facts"]),
                  "contexts": len(inst["contexts"]), "text_replaced": replaced},
        "document": {
            "claims": total,
            "states": {k: counts[k] for k in sorted(counts)},
            "unverifiable": unverifiable,
            "unverifiable_why": why,
            "rule": DOC_UNVERIFIABLE_RULE,
        },
        "claims": claims,
    }


def dumps(out):
    """**byte を 1 通りに決める。**(同じ入力 -> 同じ byte)"""

    return json.dumps(out, ensure_ascii=False, indent=1, sort_keys=False) + "\n"


def load_zip(path=None, doc=None, expected_sha256=None):
    if (path is None) == (doc is None):
        raise ValueError("--zip か --doc のどちらか 1 つを渡す")
    if path is None:
        path = os.path.join(CACHE_DIR, "%s.zip" % doc)
    with open(path, "rb") as fh:
        zb = fh.read()
    got = sha256_bytes(zb)
    if expected_sha256 and got != expected_sha256:
        raise ValueError("zip sha256 が違う: %s != %s" % (got, expected_sha256))
    return zb


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--zip", default=None, help="書類の ZIP の道")
    ap.add_argument("--doc", default=None, help="EDINET docID(手元のキャッシュから読む)")
    ap.add_argument("--text", default=None, help="経営分析の節を差し替える文章の file")
    ap.add_argument("--profile", default=None, choices=sorted(V.PROFILES.keys()),
                    help="既定は vocabulary.DEFAULT_PROFILE(= %s)" % V.DEFAULT_PROFILE)
    ap.add_argument("--zip-sha256", default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    zb = load_zip(a.zip, a.doc, a.zip_sha256)
    text = None
    if a.text:
        with io.open(a.text, encoding="utf-8") as fh:
            text = fh.read()
    out = verify_document(zb, a.profile, text)
    with io.open(a.out, "w", encoding="utf-8") as fh:
        fh.write(dumps(out))
    d = out["document"]
    print("written: %s  profile=%s  claims=%d  %s  document_unverifiable=%s"
          % (a.out, out["profile"], d["claims"], d["states"], d["unverifiable"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
