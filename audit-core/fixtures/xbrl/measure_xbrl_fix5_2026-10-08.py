# -*- coding: utf-8 -*-
"""XBRL 抽出器の直し 5 つを、1 つずつ・全部の順で採点する計測 script。Core のコードではない。

人間の指示(2026-10-08): 「直す前と直した後の両方で S100Z4Q1 の 91 件を採点し、
件数の変化を項目ごとに分けて出す。5 つを一度に入れて合計だけ出さない。」

通信はしない(ZIP は ~/.cache/audit-core/edinet/ から)。API は呼ばない(費用 0 円)。

    python3 fixtures/xbrl/measure_xbrl_fix5_2026-10-08.py --doc S100Z4Q1 --out <dir>

## 対応づけ(ここを曖昧にすると「正しい答えを外れに数える」)

`fix4`(括弧の中の句点では切らない)は文の切り方を変えるので ``N%03d``/``T%03d`` の
連番がずれる。そこで**すべての構成で ID ではなく「本文の中の絶対位置」で対応づける**:
文の列を同じ 1 か所(`extract.split_sentences`)から取り、NFKC 正規化した本文の上で
文の先頭位置を前から順に探し(見つからなければその場で落ちる)、
`文の先頭 + claim["pos"]` を鍵にする。本文そのものは 5 つの直しのどれでも変わらない。

鍵が 1 つに決まらない(重複する)場合はその場で落ちる。対応がつかなかった行は
1 件も捨てず「消えた(dropped/absent)」「現れた(new)」として全件書き出す。
"""

import argparse
import collections
import dataclasses
import hashlib
import json
import os
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))

import audit_core as core  # noqa: E402
from adapters.xbrl import edinet as E, instance as I, recipes as R, resolve as RV, registry_setup as RS, vocabulary as V  # noqa: E402

# 構成の表。base は P7(= 直す前。1 社目では P6 と 5 欄すべて差 0 なのを確認済み)。
# 1 つずつ入れるために dataclasses.replace でフラグを 1 つだけ立てる。
CONFIGS = [
    ("base", {}),
    ("fix1a_vocab", {"subjects": V.SUBJECTS_P8}),
    ("fix1b_stop", {"prior2_required": True}),
    ("fix1_both", {"subjects": V.SUBJECTS_P8, "prior2_required": True}),
    ("fix2_rounding", {"doc_rounding": True}),
    ("fix3_target", {"target_both": True}),
    ("fix4_paren", {"paren_sentence": True}),
    ("fix5_qualitative", {"drop_qualitative": True}),
    ("all", None),  # = V.PROFILES["P8"](5 つとも。6 つ目は入っていない)
    # XBRL 直し §6(2026-10-08 の追加の指示): 6 つ目を単独と組み合わせの両方で測る。
    ("fix6_prior_paren", {"text_prior_year_paren": True}),
    ("fix6_with_vocab", {"text_prior_year_paren": True, "subjects": V.SUBJECTS_P8}),
    ("all6", "P9"),  # = V.PROFILES["P9"](6 つとも)
]

ROW_FIELDS = ("state", "pointers", "recomputed", "reason", "comparator", "normalization")


def profile_of(name, over):
    if over is None:
        return V.PROFILES["P8"]
    if isinstance(over, str):
        return V.PROFILES[over]
    base = V.PROFILES["P7"]
    return base if not over else dataclasses.replace(base, name="P7+" + name, **over)


def sentence_offsets(text, sentences):
    """NFKC 正規化した本文の上での、各文の先頭位置。前から順に探す
    (文は本文の中で順番に現れるので、見つからなければ取り出し方が壊れている)。
    """

    ntext = unicodedata.normalize("NFKC", text)
    offs, cur = [], 0
    for i, s in enumerate(sentences):
        j = ntext.find(s, cur)
        if j < 0:
            raise SystemExit("sentence %d not found in the normalized text: %r" % (i, s[:40]))
        offs.append(j)
        cur = j + len(s)
    return offs


def run_one(zb, inst, profile):
    """1 構成ぶん。raw な claim 辞書(``pos`` つき)と Core の結果を揃えて返す。"""

    info = {}
    num, txt = R.build_raw_claims(zb, profile, info)
    recipes = [R.claim_to_recipe(c, "num") for c in num] + [R.claim_to_recipe(c, "text") for c in txt]
    raws = list(num) + list(txt)
    resolver = RV.make_resolver(inst["facts"])
    registry = RS.register_all(core.Registry.default())
    results = core.verify_all(recipes, resolver, registry)

    tbs = inst["textblocks"]
    mdna = I.select_mdna(tbs)
    text = I.strip_html(tbs[mdna]) if mdna else ""
    from adapters.xbrl import extract as X
    sentences = X.split_sentences(text, profile.paren_sentence)
    offs = sentence_offsets(text, sentences)

    rows = {}
    for raw, rc, rs in zip(raws, recipes, results):
        kind = rc.claim.provenance["kind"]
        key = (kind, offs[raw["sentence"]] + raw["pos"])
        if key in rows:
            raise SystemExit("duplicate key %r (ids %s / %s)" % (key, rows[key]["id"], raw["id"]))
        rows[key] = {
            "id": raw["id"], "kind": kind, "state": rs.state.value, "pointers": list(rs.pointers),
            "recomputed": rs.recomputed, "reason": rs.reason, "comparator": rs.comparator,
            "normalization": rc.claim.modifiers.normalization,
            "subject": rc.claim.subject, "value": rc.claim.value, "unit": rc.claim.unit,
            "word": rc.claim.provenance.get("word"), "span": raw.get("span"),
            "dropped": raw.get("dropped"),
        }
    C = collections.Counter
    tally = {
        "claims": len(rows), "num": sum(1 for r in rows.values() if r["kind"] == "num"),
        "text": sum(1 for r in rows.values() if r["kind"] == "text"),
        "state": dict(C(r["state"] for r in rows.values())),
        "stopped": sum(1 for r in rows.values() if r["state"] != "GROUNDED"),
        "reason": dict(C(r["reason"] for r in rows.values() if r["reason"])),
        "normalization": dict(C(r["normalization"] for r in rows.values() if r["normalization"])),
        "comparator": dict(C(r["comparator"] for r in rows.values() if r["comparator"])),
    }
    return rows, tally, info


def diff_against(base_rows, rows):
    """base との差。鍵(種類, 本文の中の位置)で 1 対 1 に対応づける。"""

    changed, gone, new = [], [], []
    for key, b in sorted(base_rows.items(), key=lambda kv: kv[0][1]):
        a = rows.get(key)
        if a is None:
            gone.append({"key_pos": key[1], "base": b})
            continue
        d = {f: (b[f], a[f]) for f in ROW_FIELDS if b[f] != a[f]}
        if d:
            changed.append({"base_id": b["id"], "id": a["id"], "key_pos": key[1], "kind": a["kind"],
                            "subject": a["subject"], "value": a["value"], "unit": a["unit"], "word": a["word"],
                            "span": a["span"], "changed": d})
    for key, a in sorted(rows.items(), key=lambda kv: kv[0][1]):
        if key not in base_rows:
            new.append({"key_pos": key[1], "row": a})
    return {"changed": changed, "gone": gone, "new": new}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", default="S100Z4Q1")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    path = E.cache_path(a.doc)
    zb = open(path, "rb").read()
    sha = hashlib.sha256(zb).hexdigest()
    inst = I.load_instance(zb)

    out = {"tool": "measure_xbrl_fix5", "doc": a.doc, "zip_sha256": sha, "configs": {}}
    base_rows = None
    for name, over in CONFIGS:
        rows, tally, info = run_one(zb, inst, profile_of(name, over))
        if name == "base":
            base_rows = rows
            d = {"changed": [], "gone": [], "new": []}
        else:
            d = diff_against(base_rows, rows)
        out["configs"][name] = {"tally": tally, "info": info, "diff": d}
        if name in ("base", "all", "all6"):
            # 行の全表は「直す前」と「5 つとも入れた後」の 2 つだけ置く。
            # 1 つずつの構成は base との差分(全件)で足りる。
            out["configs"][name]["rows"] = {"%s|%d" % k: v for k, v in rows.items()}
        print("%-18s claims=%3d  stopped=%2d  state=%s  changed=%2d gone=%d new=%d  rounding=%s" % (
            name, tally["claims"], tally["stopped"],
            {k[0] + k[-1]: v for k, v in sorted(tally["state"].items())},
            len(d["changed"]), len(d["gone"]), len(d["new"]), info.get("rounding")))

    os.makedirs(a.out, exist_ok=True)
    p = os.path.join(a.out, "measure_xbrl_fix5_%s.json" % (a.doc,))
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("written:", p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
