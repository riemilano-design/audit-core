# -*- coding: utf-8 -*-
"""2 巡目の材料。対の形(当期−前期)の主張を、当期・前期それぞれの fact で答えられる形にする。
1 巡目と同じく engine の出力・Golden・停止通過・差分の理由・主語は入れない。
個人名の member を持つ context と、その context の fact は一覧から外す(PII 分類器対策)。"""
import json, os, sys, random
HERE = sys.argv[1]
sys.path.insert(0, HERE)
from adapters.xbrl import recipes as R
from adapters.xbrl import extract as E
from adapters.xbrl import instance as I
from adapters.xbrl import vocabulary as V
from tests.adapters.xbrl import _material as M

SP = os.environ["AC_SP"]
score_old = json.load(open(os.environ["AC_SCORE_OLD"]))["detail"]
key1 = json.load(open(os.path.join(HERE, "fixtures/xbrl/blind51_key_2026-10-12.json")))["map"]

def is_person_member(m):
    return ":" in m and m.split(":")[0] not in ("jppfs_cor", "jpcrp_cor", "jpdei_cor") and "Segment" not in m

SPANS = {}
_orig = R._dispatch_num_claim
def spy(claim, s, a, b, *rest):
    SPANS[claim["id"]] = (a, b); return _orig(claim, s, a, b, *rest)

def dump(doc, profile):
    SPANS.clear(); R._dispatch_num_claim = spy
    zb = M.load_zip_bytes(doc["docID"], doc["sha256"])
    inst = I.load_instance(zb)
    facts, contexts, tbs = inst["facts"], inst["contexts"], inst["textblocks"]
    mdna = I.select_mdna(tbs); text = I.strip_html(tbs[mdna]) if mdna else ""
    sentences = E.split_sentences(text)
    num, _ = R.build_raw_claims(zb, profile); R._dispatch_num_claim = _orig
    rows = {}
    for c in num:
        s = sentences[c["sentence"]]; ab = SPANS.get(c["id"])
        rows[c["id"]] = {"docID": doc["docID"], "文": s, "対象の数(文中の表記)": s[ab[0]:ab[1]] if ab else None,
                         "対象の数の前後(文中の位置を示すための抜粋)": c["span"]}
    pc = {k: v for k, v in contexts.items() if not any(is_person_member(m) for m in (v.get("members") or []))}
    fd = [{"要素": f["name"], "context": f["context"], "値": f["value"], "単位": f["unit"], "decimals": f.get("decimals")}
          for f in facts if f["context"] in pc]
    cd = {k: {"start": v.get("start"), "end": v.get("end"), "instant": v.get("instant"), "members": v.get("members")} for k, v in pc.items()}
    return rows, fd, cd, len(facts) - len(fd)

rows_by_doc, facts_by_doc, ctx_by_doc = {}, {}, {}
for tag, doc, prof in (("1B", M.DOC_1, V.P1), ("5F", M.DOC_5, V.P5F)):
    r, f, c, dropped = dump(doc, prof)
    rows_by_doc[doc["docID"]] = r; facts_by_doc[doc["docID"]] = f; ctx_by_doc[doc["docID"]] = c
    print(tag, doc["docID"], "fact", len(f), "/ 個人名 member の context の fact を外した", dropped)

# 1 巡目の 98 行から、旧エンジンが対の形だった行を全部 + 決定済みの単一の行からおとり 8 行
pair_rows = [d for d in score_old if d["エンジン"] and len(d["エンジン"][1]) >= 2]
single_decided_decoys = [d for d in score_old if (not d["対象"]) and d["分類"] in ("正答", "誤った束縛") and d["エンジン"] and len(d["エンジン"][1]) == 1]
rnd = random.Random()
rnd.shuffle(single_decided_decoys)
chosen = pair_rows + single_decided_decoys[:8]
print("対の形の行", len(pair_rows), "(対象", sum(1 for d in pair_rows if d["対象"]), ") + 単一のおとり", min(8, len(single_decided_decoys)))

keys = ["Q-%03d" % i for i in range(1, 300)]; rnd.shuffle(keys)
out, mapping = [], {}
for i, d in enumerate(chosen):
    k = keys[i]
    src = rows_by_doc[d["docID"]][d["id"]]
    mapping[k] = {"docID": d["docID"], "id": d["id"], "対象": d["対象"], "1巡目の鍵": d["行の鍵"], "旧エンジンが対の形": len(d["エンジン"][1]) >= 2}
    out.append({"行の鍵": k, **src})
rnd.shuffle(out)
parts = [out[0::2], out[1::2]]
for i, p in enumerate(parts, 1):
    mat = {"purpose": "各行の文が指している数値について、元データの中のどの fact を指しているかを特定する。数が 2 つの fact の差として述べられている場合は、その 2 つの fact を特定する。",
           "元データ": {"facts": "blind_round2_facts_2026-10-12.json(docID ごとの fact の一覧。member の無い context と、セグメント等の member を持つ context の fact)",
                    "contexts": "blind_round2_contexts_2026-10-12.json(context の期間と member)"},
           "欄の意味": {"行の鍵": "回答に使う鍵", "docID": "提出書類の番号", "文": "書類の本文から取った 1 文",
                     "対象の数(文中の表記)": "この行で判定する数", "対象の数の前後(文中の位置を示すための抜粋)": "同じ数が文中に複数あるときの位置の手がかり"},
           "行": p}
    json.dump(mat, open(os.path.join(SP, "blind_round2_material_%d_2026-10-12.json" % i), "w"), ensure_ascii=False, indent=1)
    print("席 %d: %d 行" % (i, len(p)))
json.dump(facts_by_doc, open(os.path.join(SP, "blind_round2_facts_2026-10-12.json"), "w"), ensure_ascii=False, indent=1)
json.dump(ctx_by_doc, open(os.path.join(SP, "blind_round2_contexts_2026-10-12.json"), "w"), ensure_ascii=False, indent=1)
json.dump({"note": "司令塔のみ。2 巡目の鍵 → 書類・id・対象・1 巡目の鍵", "map": mapping}, open(os.path.join(SP, "blind_round2_key_2026-10-12.json"), "w"), ensure_ascii=False, indent=1)
print("合計", len(out))
