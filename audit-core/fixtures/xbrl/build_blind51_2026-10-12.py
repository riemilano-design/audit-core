# -*- coding: utf-8 -*-
"""独立判定用の材料を作る。
engine の pointer・状態・Golden・停止/通過・差分の理由・engine が取った主語は 1 欄も入れない。
行の鍵は乱数で振り、id から計算できないようにする。"""
import json, os, sys, random
HERE = sys.argv[1]
sys.path.insert(0, HERE)
from adapters.xbrl import recipes as R
from adapters.xbrl import extract as E
from adapters.xbrl import instance as I
from adapters.xbrl import vocabulary as V
from tests.adapters.xbrl import _material as M

TARGET = json.load(open(os.path.join(HERE, "fixtures/xbrl/binding_order_diag_2026-10-12.json")))["golden_delta"]["with_rule4"]

SPANS = {}
_orig_dispatch = R._dispatch_num_claim
def dispatch_spy(claim, s, a, b, *rest):
    SPANS[claim["id"]] = (a, b)
    return _orig_dispatch(claim, s, a, b, *rest)

def dump(tag, doc, profile):
    SPANS.clear()
    R._dispatch_num_claim = dispatch_spy
    zb = M.load_zip_bytes(doc["docID"], doc["sha256"])
    inst = I.load_instance(zb)
    facts, contexts, tbs = inst["facts"], inst["contexts"], inst["textblocks"]
    mdna = I.select_mdna(tbs)
    text = I.strip_html(tbs[mdna]) if mdna else ""
    sentences = E.split_sentences(text)
    num, txt = R.build_raw_claims(zb, profile)
    R._dispatch_num_claim = _orig_dispatch
    rows = []
    for c in num:
        s = sentences[c["sentence"]]
        ab = SPANS.get(c["id"])
        rows.append({"id": c["id"], "docID": doc["docID"],
                     "文": s,
                     "対象の数(文中の表記)": s[ab[0]:ab[1]] if ab else None,
                     "対象の数の前後(文中の位置を示すための抜粋)": c["span"]})
    fdump = [{"要素": f["name"], "context": f["context"], "値": f["value"],
              "単位": f["unit"], "decimals": f.get("decimals")} for f in facts]
    cdump = {k: {"start": v.get("start"), "end": v.get("end"), "instant": v.get("instant"),
                 "members": v.get("members")} for k, v in contexts.items()}
    return rows, fdump, cdump

out_rows, facts_by_doc, ctx_by_doc = [], {}, {}
mapping = {}
rnd = random.Random()
keys = ["R-%03d" % i for i in range(1, 300)]
rnd.shuffle(keys)
ki = 0
for tag, doc, prof in (("1B", M.DOC_1, V.P1), ("5F", M.DOC_5, V.P5F)):
    rows, fdump, cdump = dump(tag, doc, prof)
    facts_by_doc[doc["docID"]] = fdump
    ctx_by_doc[doc["docID"]] = cdump
    tgt = set(TARGET[tag])
    others = [r for r in rows if r["id"] not in tgt]
    rnd.shuffle(others)
    decoys = others[:len(tgt)]
    for r in [x for x in rows if x["id"] in tgt] + decoys:
        key = keys[ki]; ki += 1
        mapping[key] = {"docID": doc["docID"], "profile": tag, "id": r["id"], "対象": r["id"] in tgt}
        rr = {"行の鍵": key, "docID": r["docID"], "文": r["文"],
              "対象の数(文中の表記)": r["対象の数(文中の表記)"],
              "対象の数の前後(文中の位置を示すための抜粋)": r["対象の数の前後(文中の位置を示すための抜粋)"]}
        out_rows.append(rr)
rnd.shuffle(out_rows)

SP = os.environ["AC_SP"]
parts = [out_rows[i::3] for i in range(3)]
for i, p in enumerate(parts, 1):
    mat = {"purpose": "各行の文が指している数値について、元データの中のどの fact を指しているかを特定する。",
           "元データ": {"facts": "blind51_facts_2026-10-12.json(docID ごとの fact の一覧)",
                    "contexts": "blind51_contexts_2026-10-12.json(context の期間と member)"},
           "欄の意味": {"行の鍵": "回答に使う鍵", "docID": "提出書類の番号",
                     "文": "書類の本文から取った 1 文", "対象の数(文中の表記)": "この行で判定する数",
                     "対象の数の前後(文中の位置を示すための抜粋)": "同じ数が文中に複数あるときの位置の手がかり"},
           "行": p}
    json.dump(mat, open(os.path.join(SP, "blind51_material_%d_2026-10-12.json" % i), "w"), ensure_ascii=False, indent=1)
    print("席 %d: %d 行" % (i, len(p)))
json.dump(facts_by_doc, open(os.path.join(SP, "blind51_facts_2026-10-12.json"), "w"), ensure_ascii=False, indent=1)
json.dump(ctx_by_doc, open(os.path.join(SP, "blind51_contexts_2026-10-12.json"), "w"), ensure_ascii=False, indent=1)
json.dump({"note": "司令塔のみ。行の鍵 → 書類・id・対象かどうか。鍵は乱数で、id から計算できない",
           "map": mapping},
          open(os.path.join(SP, "blind51_key_2026-10-12.json"), "w"), ensure_ascii=False, indent=1)
print("合計", len(out_rows), "行 / 対象", sum(1 for v in mapping.values() if v["対象"]), "/ おとり", sum(1 for v in mapping.values() if not v["対象"]))
