# -*- coding: utf-8 -*-
"""全母集団の「文・数の位置」を落とす(エンジンは変更せず、読むだけ)。
使い方: python3 dump_numbers_2026-10-12.py <repo の audit-core> <出力 json>
  環境変数 AC_ZIP = ai_prose_instance_2026-10-09.zip の絶対パス(git 管理外)。
母集団 = 1B(S100Z4Q1×P1)・5F(S100Z4B6×P5F)・P7(AI 文 S100Z4Q1×P7)。
各行 = {"s": 文, "ab": [数の始点, 終点], "money": 金額か}"""
import json, os, sys
HERE, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, HERE)
from tests.adapters.xbrl import _material as M
from adapters.xbrl import vocabulary as V, instance as I, recipes as R, extract as E

SPN = {}
_orig = R._dispatch_num_claim
def spy(claim, s, a, b, *rest):
    SPN[claim["id"]] = (a, b)
    return _orig(claim, s, a, b, *rest)

def run(zb, prof):
    SPN.clear(); R._dispatch_num_claim = spy
    inst = I.load_instance(zb); tbs = inst["textblocks"]; md = I.select_mdna(tbs)
    sents = E.split_sentences(I.strip_html(tbs[md]) if md else "")
    num, _ = R.build_raw_claims(zb, prof)
    R._dispatch_num_claim = _orig
    return {c["id"]: {"s": sents[c["sentence"]], "ab": list(SPN[c["id"]]) if c["id"] in SPN else None,
                      "unit": c.get("unit"), "subject": c.get("subject")} for c in num}

out = {}
for tag, doc, prof in (("1B", M.DOC_1, V.P1), ("5F", M.DOC_5, V.P5F)):
    out[tag] = run(M.load_zip_bytes(doc["docID"], doc["sha256"]), prof)
out["P7"] = run(open(os.environ["AC_ZIP"], "rb").read(), V.P7)
json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1, sort_keys=True)
print({k: len(v) for k, v in out.items()})
