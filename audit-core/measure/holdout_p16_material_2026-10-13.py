# -*- coding: utf-8 -*-
"""限定確認(docs/HOLDOUT_P16_CONDITIONS_2026-10-13.md)の材料を作る。

未使用 2 書類(S100Z39P・S100Z4N9)を **P16(285713e)の Claim 切り出し**で読み、
記憶のない独立 2 席に渡す材料(文・対象の数・前後)と fact・context を、
前回(docs/research/e2_labels/e2_material2_2026-10-13.json)と同じ欄で書く。

- 席に見せるもの: fixtures/xbrl/holdout_p16/seat/{material,facts,contexts}_<doc>.json
- 司令塔だけ: fixtures/xbrl/holdout_p16/commander_only/key_<doc>.json
  (行の鍵 → P16 の claim id と内容の鍵。席には渡さない)
- 1 書類 150 件以下なら全件、超えるなら種 20261015 で 150 件。行は同じ種で並べ替える
  (num/text の順が鍵の並びから漏れないように)。
- fact・context から、会社拡張の member のうち名前に Segment を含まないもの
  (役員などの個人の member)を持つ context とその fact を外す(前回の「個人名 member 除外」に相当。機械の規則で書く)。

通信しない。engine の state・pointer は材料に書かない。
"""

import hashlib
import io
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))

from adapters.xbrl import vocabulary as V, instance as I, recipes as R, extract as E  # noqa: E402

DOCS = ("S100Z39P", "S100Z4N9")
SEED = 20261015
CAP = 150
PROFILE = "P16"
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
OUT = os.path.join(ROOT, "fixtures", "xbrl", "holdout_p16")
STD_PREFIXES = ("jppfs_cor", "jpcrp_cor", "jpdei_cor", "jpigp_cor", "jppfs-cor", "jpcrp-cor")

PURPOSE = ("各行の文が指している数値について、元データ(この docID の XBRL)の中のどの fact を指しているかを特定する。"
           "数が 2 つ以上の fact の差・比・和として述べられている場合は、それぞれの fact を所定の欄に書き、形を答える。")
FIELDS = {
    "行の鍵": "回答に使う鍵",
    "docID": "提出書類の番号",
    "文": "本文から取った 1 文(600 字を超える文は対象の数の前後 300 字)",
    "対象の数(文中の表記)": "この行で判定する数(機械が読んだ値。null の行は抜粋が示す方向の語が対象)",
    "単位(切り出し時)": "機械が読んだ単位",
    "対象の数の前後(文中の位置を示すための抜粋)": "同じ数が文中に複数あるときの位置の手がかり",
}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def content_key(c):
    """profile に依らず同じ Claim を指す鍵(span・値・語)。"""
    return "%s|%s|%s" % (c.get("span"), c.get("value"), c.get("word"))


def person_member(m):
    pre = m.split(":", 1)[0]
    return pre not in STD_PREFIXES and "Segment" not in m


def build(doc):
    zb = open(os.path.join(CACHE, doc + ".zip"), "rb").read()
    inst = I.load_instance(zb)
    prof = V.PROFILES[PROFILE]
    num_claims, text_claims = R.build_raw_claims(zb, prof)
    mdna = I.select_mdna(inst["textblocks"])
    text = I.strip_html(inst["textblocks"][mdna])
    sentences = E.split_sentences(text, prof.paren_sentence)

    rows = []
    for kind, claims in (("num", num_claims), ("text", text_claims)):
        for c in claims:
            s = sentences[c["sentence"]]
            span = c.get("span")
            if len(s) > 600:
                p = s.find(span[:20]) if span else -1
                p = max(0, p)
                s = s[max(0, p - 300):p + 300]
            rows.append({
                "kind": kind, "id": c["id"], "ckey": content_key(c),
                "文": s,
                "対象の数(文中の表記)": (c.get("value") if kind == "num" else None),
                "単位(切り出し時)": (c.get("unit") if kind == "num" else None),
                "前後": span,
            })
    n_all = len(rows)
    rnd = random.Random(SEED)
    if n_all > CAP:
        rows = rnd.sample(rows, CAP)
    rnd.shuffle(rows)
    key, material = [], []
    for i, r in enumerate(rows, 1):
        k = "H-%03d" % i
        key.append({"行の鍵": k, "claim_id": r["id"], "kind": r["kind"], "content_key": r["ckey"]})
        material.append({
            "行の鍵": k, "docID": doc, "文": r["文"],
            "対象の数(文中の表記)": r["対象の数(文中の表記)"],
            "単位(切り出し時)": r["単位(切り出し時)"],
            "対象の数の前後(文中の位置を示すための抜粋)": r["前後"],
        })

    # fact / context(個人の member を外す)
    ctx_out, dropped_ctx = {}, []
    for cid, c in inst["contexts"].items():
        if any(person_member(m) for m in c["members"]):
            dropped_ctx.append(cid)
            continue
        ctx_out[cid] = {"start": c["start"], "end": c["end"], "instant": c["instant"], "members": c["members"]}
    facts_out, dropped_f = [], 0
    for f in inst["facts"]:
        if f["context"] not in ctx_out:
            dropped_f += 1
            continue
        facts_out.append({"要素": f["name"], "context": f["context"], "値": f["value"],
                          "単位": f["unit"], "decimals": f["decimals"]})

    seat = os.path.join(OUT, "seat")
    paths = {
        "material": os.path.join(seat, "material_%s.json" % doc),
        "facts": os.path.join(seat, "facts_%s.json" % doc),
        "contexts": os.path.join(seat, "contexts_%s.json" % doc),
        "key": os.path.join(OUT, "commander_only", "key_%s.json" % doc),
    }
    for p in paths.values():
        if os.path.exists(p):
            raise SystemExit("既に在る。上書きしない: %s" % p)
    mat = {"purpose": PURPOSE,
           "元データ": {"facts": os.path.basename(paths["facts"]), "contexts": os.path.basename(paths["contexts"])},
           "欄の意味": FIELDS, "行": material}
    with io.open(paths["material"], "w", encoding="utf-8") as fh:
        json.dump(mat, fh, ensure_ascii=False, indent=1)
    with io.open(paths["facts"], "w", encoding="utf-8") as fh:
        json.dump(facts_out, fh, ensure_ascii=False, indent=1)
    with io.open(paths["contexts"], "w", encoding="utf-8") as fh:
        json.dump(ctx_out, fh, ensure_ascii=False, indent=1)
    with io.open(paths["key"], "w", encoding="utf-8") as fh:
        json.dump({"note": "司令塔のみ。席には渡さない。", "docID": doc, "seed": SEED, "profile": PROFILE,
                   "claims_all": n_all, "rows": len(key), "zip_sha256": sha(zb),
                   "dropped_contexts": dropped_ctx, "dropped_facts": dropped_f, "rows_map": key},
                  fh, ensure_ascii=False, indent=1)
    rec = {"docID": doc, "zip_sha256": sha(zb), "claims_all": n_all, "rows": len(key),
           "num_rows": sum(1 for r in key if r["kind"] == "num"),
           "facts_in": len(inst["facts"]), "facts_out": len(facts_out),
           "contexts_in": len(inst["contexts"]), "contexts_out": len(ctx_out),
           "dropped_contexts": len(dropped_ctx)}
    for name, p in paths.items():
        rec["sha256_" + name] = sha(open(p, "rb").read())
    return rec


def main():
    out = [build(d) for d in DOCS]
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
