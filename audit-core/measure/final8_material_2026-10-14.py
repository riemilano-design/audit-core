# -*- coding: utf-8 -*-
"""最終評価用 8 書類(docs/FINAL_EVAL_8_SEAL_2026-10-14.md)の材料を作る。

P16 の限定確認の材料 script(holdout_p16_material_2026-10-13.py)を 8 書類・上限 100・
種 20261016 に写したもの。席に渡すのは material / facts / contexts の 3 ファイルだけ。

サブコマンド
  classify  8 書類を engine と同じ規則で 連結あり(A)/ 連結なし(B)に分け、zip sha256 と
            一緒に <BASE>/classify_<date>.json に書く(ラベルの前に記録する。封 §1)。
  build     材料を作る(書類ごとに seat/ と commander_only/)。既に在れば上書きしない。
  check     席に見せる 3 ファイルの**司令塔が書いた文面**(purpose・欄の意味・行の欄)に
            禁止語が無いことを機械で確かめる。書類自身の文字列(文・要素名・ラベル)は対象外。

環境変数で差し替えられるのは下見のためだけ(本番は既定のまま):
  FINAL8_BASE  出力先(既定 fixtures/xbrl/final8)
  FINAL8_DOCS  docID をカンマ区切り(既定 split の final_eval_sealed)
  FINAL8_SEED  抽出の種(既定 20261016。Q2 の封 §3 は 20261017 を指定している)
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

from adapters.xbrl import vocabulary as V, instance as I, recipes as R, extract as E, edinet  # noqa: E402

SPLIT = os.path.join(ROOT, "fixtures", "xbrl", "holdout_p17", "split_2026-10-14.json")
DATE = "2026-10-14"
SEED = int(os.environ.get("FINAL8_SEED") or 20261016)   # Q2 の封は 20261017(封 §3)
CAP = 100
PROFILE = "P16"
BASE = os.environ.get("FINAL8_BASE") or os.path.join(ROOT, "fixtures", "xbrl", "final8")
STD_PREFIXES = ("jppfs_cor", "jpcrp_cor", "jpdei_cor", "jpigp_cor", "jppfs-cor", "jpcrp-cor")

# 席に見せる文面に入れてはいけない語(封 §1)。書類自身の文字列には掛けない。
BANNED = ("engine", "GROUNDED", "停止", "pointer", "profile", "P16", "P20", "真偽",
          "正解", "誤り", "連結", "単体", "UNVERIFIABLE", "VALUE_MISMATCH", "POINTER_NOT_FOUND")

PURPOSE = ("各行の文が指している数値について、元データ(この docID の XBRL)の中のどの fact を指しているかを特定する。"
           "数が 2 つ以上の fact の差・比・和として述べられている場合は、それぞれの fact を所定の欄に書き、形を答える。"
           "文が指す対象に当たる fact が元データに無いときは、無理に選ばず判定不能とし、その理由を所定の列挙から選ぶ。")
FIELDS = {
    "行の鍵": "回答に使う鍵",
    "docID": "提出書類の番号",
    "文": "本文から取った 1 文(600 字を超える文は対象の数の前後 300 字)",
    "対象の数(文中の表記)": "この行で判定する数(機械が読んだ値。null の行は抜粋が示す方向の語が対象)",
    "単位(切り出し時)": "機械が読んだ単位",
    "対象の数の前後(文中の位置を示すための抜粋)": "同じ数が文中に複数あるときの位置の手がかり",
}


def docs():
    env = os.environ.get("FINAL8_DOCS")
    if env:
        return tuple(x for x in env.split(",") if x)
    with io.open(SPLIT, encoding="utf-8") as fh:
        return tuple(json.load(fh)["final_eval_sealed"])


def sha(b):
    return hashlib.sha256(b).hexdigest()


def content_key(c):
    return "%s|%s|%s" % (c.get("span"), c.get("value"), c.get("word"))


def person_member(m):
    pre = m.split(":", 1)[0]
    return pre not in STD_PREFIXES and "Segment" not in m


def read_zip(doc):
    return open(edinet.cache_path(doc), "rb").read()


# ---------------------------------------------------------------- classify
def classify():
    out = []
    for doc in docs():
        zb = read_zip(doc)
        inst = I.load_instance(zb)
        n = I.consolidated_element_count(inst["facts"])
        out.append({"docID": doc, "zip_sha256": sha(zb), "consolidated_element_count": n,
                    "group": "A" if n > 0 else "B",
                    "facts": len(inst["facts"]), "contexts": len(inst["contexts"])})
    p = os.path.join(BASE, "classify_%s.json" % DATE)
    if os.path.exists(p):
        raise SystemExit("既に在る。上書きしない: %s" % p)
    os.makedirs(BASE, exist_ok=True)
    rec = {"rule": "instance.consolidated_element_count(facts) == 0 なら B(連結なし)。engine と同じ規則",
           "k": sum(1 for r in out if r["group"] == "B"), "docs": out}
    with io.open(p, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
    print(json.dumps(rec, ensure_ascii=False, indent=1))


# ---------------------------------------------------------------- build
def build(doc):
    zb = read_zip(doc)
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

    seat = os.path.join(BASE, "seat")
    paths = {
        "material": os.path.join(seat, "material_%s.json" % doc),
        "facts": os.path.join(seat, "facts_%s.json" % doc),
        "contexts": os.path.join(seat, "contexts_%s.json" % doc),
        "key": os.path.join(BASE, "commander_only", "key_%s.json" % doc),
    }
    for p in paths.values():
        if os.path.exists(p):
            raise SystemExit("既に在る。上書きしない: %s" % p)
    os.makedirs(seat, exist_ok=True)
    os.makedirs(os.path.join(BASE, "commander_only"), exist_ok=True)
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
        json.dump({"note": "司令塔のみ。席には渡さない。", "docID": doc, "seed": SEED, "cap": CAP,
                   "profile": PROFILE, "claims_all": n_all, "rows": len(key), "zip_sha256": sha(zb),
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


# ---------------------------------------------------------------- check
def commander_prose(material):
    """席に見せる material のうち、司令塔が書いた文面だけを取り出す(書類の文は含めない)。"""
    out = [material["purpose"]]
    out += list(material["欄の意味"].keys()) + list(material["欄の意味"].values())
    out += list(material["元データ"].keys()) + list(material["元データ"].values())
    for row in material["行"]:
        out += list(row.keys())          # 欄の名前は司令塔の字
        out.append(str(row["docID"]))    # docID も司令塔が入れる値
    return out


def leaks(texts, banned=BANNED):
    found = []
    for t in texts:
        for b in banned:
            if b in t:
                found.append((b, t[:60]))
    return found


def check():
    bad_total = 0
    for doc in docs():
        p = os.path.join(BASE, "seat", "material_%s.json" % doc)
        mat = json.load(io.open(p, encoding="utf-8"))
        found = leaks(commander_prose(mat))
        bad_total += len(found)
        print("%s: 司令塔の文面 %d 片、禁止語 %d 件 %s" % (doc, len(commander_prose(mat)), len(found), found[:3]))
        # 指示文も同じ検査に掛ける
    ins = os.path.join(BASE, "seat", "seat_instruction_%s.md" % DATE)
    if os.path.exists(ins):
        found = leaks([io.open(ins, encoding="utf-8").read()])
        bad_total += len(found)
        print("seat_instruction: 禁止語 %d 件 %s" % (len(found), found[:3]))
    print("禁止語 合計 %d 件" % bad_total)
    return 1 if bad_total else 0


def main():
    cmd = sys.argv[1]
    if cmd == "classify":
        classify()
    elif cmd == "build":
        print(json.dumps([build(d) for d in docs()], ensure_ascii=False, indent=1))
    elif cmd == "check":
        sys.exit(check())
    else:
        raise SystemExit("classify | build | check")


if __name__ == "__main__":
    main()
