# -*- coding: utf-8 -*-
"""欠陥 A の評価のラベル材料を作る(封 docs/DEFECT_A_EVAL_SEAL_2026-10-14.md §4)。

席に渡すのは 1 行につき **行の鍵 / docID / 文 / 対象の数(文中の表記) / 単位 / 数の前後の抜粋** だけ。
**渡さないもの**: 要素名・context・member・engine の判定・pointer・recomputed・
「この行が動いた」という事実・封の内容・実装者の解釈。

**封を強める足し算(採点は変えない)**: 封が定めた採点の対象は「動いた行」だけだが、
材料には**動いていない金額の主張を同数混ぜて並べ替える**。席はどの行が動いたか分からない。
採点は封じたとおり**動いた行だけ**で行う(混ぜた行は報告のみ)。

seed は 260661(設計を commit した 003fa35 の 16 進を 10 進にした値)。
出力が既に在れば上書きを拒む。通信しない。
"""
import io
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

BASE = os.path.join(ROOT, "fixtures", "xbrl", "defect_a")
BA = os.path.join(BASE, "before_after_2026-10-14.json")
MAT = os.path.join(BASE, "seat", "material_2026-10-14.json")
KEY = os.path.join(BASE, "commander_only", "key_2026-10-14.json")
SEED = 260661
PROFILE = "P20"
MONEY = ("百万円", "千円", "円", "億円")

BANNED = ("動いた", "修正", "欠陥", "帯", "truncate", "VALUE_MISMATCH", "GROUNDED",
          "差を水準", "engine", "pointer", "recomputed", "封")


def build():
    from adapters.xbrl import recipes as R, vocabulary as V, edinet, instance as I, extract as E
    ba = json.load(io.open(BA, encoding="utf-8"))
    moved = {m["id"] for m in ba["result"][PROFILE]["moved"]}
    docs = ba["docs"]
    rows = []
    for d in docs:
        zb = io.open(edinet.cache_path(d), "rb").read()
        num, _ = R.build_raw_claims(zb, V.PROFILES[PROFILE])
        inst = I.load_instance(zb)
        mdna = I.select_mdna(inst["textblocks"])
        sents = E.split_sentences(I.strip_html(inst["textblocks"][mdna]), V.PROFILES[PROFILE].paren_sentence)
        for c in num:
            if c.get("unit") not in MONEY:
                continue
            cid = "%s:%s" % (d, c["id"])
            s = sents[c["sentence"]]
            span = c.get("span") or ""
            if len(s) > 600:
                p = max(0, s.find(span[:20]))
                s = s[max(0, p - 300):p + 300]
            rows.append({"claim_id": cid, "docID": d, "moved": cid in moved,
                         "文": s, "数": c["value"], "単位": c["unit"], "前後": span})
    hit = [r for r in rows if r["moved"]]
    rest = [r for r in rows if not r["moved"]]
    rnd = random.Random(SEED)
    mix = hit + rnd.sample(rest, min(len(hit), len(rest)))
    rnd.shuffle(mix)
    return hit, mix


def main():
    if os.path.exists(MAT) or os.path.exists(KEY):
        raise SystemExit("既に在る。上書きしない")
    hit, mix = build()
    material, key = [], []
    for i, r in enumerate(mix, 1):
        k = "L-%03d" % i
        material.append({"行の鍵": k, "docID": r["docID"], "文": r["文"],
                         "対象の数(文中の表記)": r["数"], "単位": r["単位"],
                         "数の前後(文中の位置を示すための抜粋)": r["前後"]})
        key.append({"行の鍵": k, "claim_id": r["claim_id"], "採点対象": r["moved"]})
    out = {"purpose": "文に出てくる金額が『差(増減額)』か『水準(残高・金額そのもの)』かを 1 行ずつ判定する",
           "答え方": {"行の鍵": "material と同じ", "判定": "差 | 水準 | 判定不能",
                   "項目名(文から読める範囲)": "その数が指す項目を文中の語で短く。読めなければ null",
                   "理由": "文のどの語からそう読んだか(1 文)"},
           "見てよいもの": "この材料の 文・対象の数・単位・前後 だけ。他のファイルも外部の知識も見ない",
           "行": material}
    prose = [out["purpose"]] + list(out["答え方"].keys()) + list(out["答え方"].values()) + [out["見てよいもの"]]
    for w in BANNED:
        for t in prose:
            if w in str(t):
                raise AssertionError("司令塔の文面に禁止語 %r" % w)
    os.makedirs(os.path.dirname(MAT), exist_ok=True)
    os.makedirs(os.path.dirname(KEY), exist_ok=True)
    with io.open(MAT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    with io.open(KEY, "w", encoding="utf-8") as fh:
        json.dump({"note": "司令塔のみ。席には渡さない。", "profile": PROFILE, "seed": SEED,
                   "採点対象の件数": len(hit), "材料の行数": len(material), "rows_map": key}, fh,
                  ensure_ascii=False, indent=1)
    print("採点対象 %d 件 / 材料 %d 行" % (len(hit), len(material)))
    print("->", MAT)
    print("->", KEY)


if __name__ == "__main__":
    main()
