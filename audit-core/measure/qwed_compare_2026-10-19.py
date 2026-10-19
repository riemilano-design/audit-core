# -*- coding: utf-8 -*-
u"""QWED と同じ材料で測る ― 封 `docs/QWED_COMPARE_SEAL_2026-10-19.md`(commit `ba75d10`)の段 B。

**取り込まない。並べて測る。**Audit Core を測ったのと同じ 2 つの材料
(XBRL 8 書類 192 行・表計算 35 件 = 11 文)に QWED 7.3.0 の 0 USD の入口
(`FactVerifier(use_llm_fallback=False).verify_fact(claim, context, provider=None)`)を通し、
封 §0 の「読む欄」を全行で記録に写す。Audit Core 側は**記録から写す。再実行しない。**

走らせ方 3 本 + 対照 3 件(封 §2・§3 の字のとおり。入力の作り方は 1 通り):
  W1  XBRL、日本語のまま、本文を読ませる(192 行)
  E   XBRL、英語の機械文、fact の一覧を読ませる(192 行。95,000 字以下の chunk に行の境で割る)
  S   表計算、日本語のまま(11 文。誤り 8 文は 元の表記 → 植えた表記 を 1 回だけ置換)
  C-1 英文の再現(下見 §5 の (a)(b)) / C-2 E の +1 / C-3 `\\b` の読み

**engine(`core/`・`adapters/`)は触らない。QWED のコードも変えない。LLM は呼ばない。通信しない。0 USD。**
**この script は Python 3.11 の venv(qwed 7.3.0 入り)で走らせる。**3.9 で `qwed_new` が import できなければ
理由を印字して rc≠0 で止まる。門(`tests/measure`)は 3.9 で走り、記録 JSON しか読まない。

    cd audit-core
    <venv>/bin/python measure/qwed_compare_2026-10-19.py --write
    python3 measure/qwed_compare_2026-10-19.py --set-pytest-log <pytest の log>   # Q-17 の赤の本数を記録に写す
"""
import argparse
import collections
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import time
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                    # audit-core/
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)

SEAL = "docs/QWED_COMPARE_SEAL_2026-10-19.md"
SEAL_COMMIT = "ba75d10"
CD8 = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
REC_PU = os.path.join(CD8, "period_unit_hold_2026-10-19.json")
DRAW = os.path.join(CD8, "draw_2026-10-17.json")
FX_SHEET = os.path.join(ROOT, "fixtures", "sheet")
POC_GOLD = os.path.join(FX_SHEET, "poc_gold_2026-10-17.json")
ERRDET_MAKE = os.path.join(FX_SHEET, "errdet_make_2026-10-17.json")
ERRDET_CORE = os.path.join(FX_SHEET, "errdet_core_2026-10-17.json")
OUT = os.path.join(CD8, "qwed_compare_2026-10-19.json")
SEAL_SIDE_FILES = ("docs/QWED_COMPARE_SEAL_2026-10-19.md", "tests/measure/test_qwed_compare_seal.py")
RESULT_SIDE_FILES = ("measure/qwed_compare_2026-10-19.py", "fixtures/xbrl/cd8/qwed_compare_2026-10-19.json",
                     "docs/QWED_COMPARE_RESULT_2026-10-19.md", "tests/measure/test_qwed_compare_result.py")

#: 封 Q-16。**1 つでも在れば止める**(0 USD)。
KEY_ENV = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY")
#: 封 §2 E。QWED は context を 100,000 字で切る(下見 §3-2)。
CHUNK_MAX = 95000
#: 封 §1-1 の下見の表(**字で留める**。8 / 8 一致しなければ描き方が封と違うので止める)。
SEAL_E_LIST = {"S100YWGX": (1122, 110764), "S100YXF5": (947, 91439), "S100YXMA": (1223, 116712),
               "S100YYRG": (777, 70358), "S100YYRV": (943, 88326), "S100YZ7E": (502, 52041),
               "S100YZCT": (1097, 105881), "S100YZEV": (397, 41062)}
SEAL_CHUNKS = {"S100YWGX": 2, "S100YXMA": 2, "S100YZCT": 2}        # 他は 1。合計 11
SEAL_INJECT_TYPES = {"T5_COINCIDENT": 50, "T3_ABSENT": 12, "T1_VALUE": 2}
SEAL_SHEET = {u"文": 11, u"誤り": 8, u"抜粋の字数": 4194}
#: 封 §3 C-3 の字(QWED `fact_verifier.py` の数の正規表現と同じ字。QWED は import しない道でも読めるよう字で持つ)。
NUM_RE = r"\b\d{1,20}(?:\.\d{1,10})?\b"
C2_DOC, C2_ID = "S100YXMA", "R004"
C3_ID = "R010"
#: 下見 §5 の英文(`scratchpad/qwed/smoke_fact.py` と同じ字)。
C1_CONTEXT = ("Acme Corp reported total revenue of 1234 million yen for fiscal 2025. "
              "Operating income was 210 million yen. "
              "The company employs 450 people in Tokyo.")
C1_CLAIMS = {"a": "Acme Corp reported total revenue of 1234 million yen for fiscal 2025.",
             "b": "Acme Corp reported total revenue of 1239 million yen for fiscal 2025."}
FIELDS = ("status", "deterministic_verdict", "deterministic_confidence", "semantic_similarity",
          "keyword_overlap", "entity_match", "negation_conflict", "citations", "constraint_id")


def _load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def _mod(rel, name):
    sp = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def _sha(p):
    return hashlib.sha256(io.open(p, "rb").read()).hexdigest()


# ---------------------------------------------------------------- 0 USD の門・入口
def check_zero_usd():
    present = [k for k in KEY_ENV if os.environ.get(k)]
    if present:
        raise SystemExit(u"**API 鍵の環境変数が在る: %s。0 USD の封なので止める**" % present)
    return {u"見た環境変数": list(KEY_ENV), u"在った件数": 0, "provider": None}


def import_qwed():
    if sys.version_info < (3, 10):
        print(u"**qwed は Python >= 3.10 が要る(いま %s)。venv の python で走らせる**" % sys.version.split()[0])
        raise SystemExit(2)
    try:
        import qwed_new
        from qwed_new.core import fact_verifier as fv
    except ImportError as e:
        print(u"**qwed_new を import できない: %r。venv の python で走らせる**" % (e,))
        raise SystemExit(2)
    try:
        import importlib.metadata as md
        dist = md.version("qwed")
    except Exception:                              # pragma: no cover
        dist = None
    return fv, {u"配布名 qwed の版(importlib.metadata)": dist,
                u"qwed_new.__version__": getattr(qwed_new, "__version__", None),
                u"注": u"封の字は `qwed.__version__` だが `qwed` という module は無い(配布名 qwed・import 名 qwed_new)",
                "sys.version": sys.version, "sys.executable": sys.executable,
                u"fact_verifier.py": fv.__file__, u"fact_verifier.py の sha256": _sha(fv.__file__)}


def read_fields(r):
    """封 §0 の「読む欄」を 1 行分。`evidence` は欄の外だが原因を読むために残す。"""
    d = r.to_dict()
    dev = d.get("developer_fields") or {}
    sc = dev.get("scores") or {}
    return {"status": d["status"], "deterministic_verdict": dev.get("deterministic_verdict"),
            "deterministic_confidence": dev.get("deterministic_confidence"),
            "semantic_similarity": sc.get("semantic_similarity"), "keyword_overlap": sc.get("keyword_overlap"),
            "entity_match": sc.get("entity_match"), "negation_conflict": sc.get("negation_conflict"),
            "citations": len(dev.get("citations") or []), "constraint_id": dev.get("constraint_id"),
            "evidence": dev.get("evidence")}


def classify(f):
    """封 §0 の 3 分類(QWED の語彙ではない)。"""
    em, v = f["entity_match"], f["deterministic_verdict"]
    if v == "REFUTED" or f["status"] == "BLOCKED" or (em is not None and em < 1.0):
        return u"違うと言う"
    if em == 1.0 and v == "SUPPORTED":
        return u"通す"
    return u"判定なし"


def verify(fv_cls, claim, context):
    return read_fields(fv_cls(use_llm_fallback=False).verify_fact(claim, context, provider=None))


# ---------------------------------------------------------------- 原因を読むための字(QWED は呼ばない。同じ正規表現で材料を読む)
#: QWED `fact_verifier.py` の tokenizer・否定語(字で持つ。**外れの原因を 1 件ずつ読むため**。判定には使わない)
WORD_RE = r"\b[a-zA-Z]+\b"
NEGATION_WORDS = ("not", "no", "never", "none", "nothing", "nowhere", "neither", "nobody", "n't", "cannot",
                  "can't", "won't", "wouldn't", "shouldn't", "couldn't", "didn't", "doesn't", "don't", "isn't",
                  "aren't", "wasn't", "weren't", "hasn't", "haven't", "hadn't")


def reading(claim, context):
    """claim の英字の語・数の字と、context の数の字に無いもの・否定語の部分一致。"""
    nums = sorted(set(re.findall(NUM_RE, claim)))
    ctx_nums = set(re.findall(NUM_RE, context))
    return {u"claim の英字の語": sorted(set(w.lower() for w in re.findall(WORD_RE, claim))),
            u"claim の数の字": nums, u"context に無い数の字": [n for n in nums if n not in ctx_nums],
            u"claim の否定語(部分一致)": [n for n in NEGATION_WORDS if n in claim.lower()]}


# ---------------------------------------------------------------- 材料(③ と同じ組み立て)
def material_rows(docs, MB, PR, I, ED):
    """`measure/xbrl_holds_product_path_2026-10-19.py` の `_material_rows` と同じ組み立て。
    違いは改変後の本文 `tampered` も返すこと(W1 の context)。"""
    A1, IJ = MB.A1, MB.IJ
    seed, _m = IJ.verify_seed_sealed(MB.SEED_FILE)
    for doc in docs:
        zb = io.open(ED.cache_path(doc), "rb").read()
        old, A1.TMP = A1.TMP, MB.TMP
        try:
            text, refs = A1.material(doc)
        finally:
            A1.TMP = old
        chosen, _c = MB.pick_injections(text, refs, seed, doc)
        tampered, pl = IJ.apply_edits(text, chosen)
        mrows, _n = MB.build_rows(tampered, chosen, pl)
        zb2, _e, _mm = PR.build_modified_zip(zb, tampered)
        yield doc, I.load_instance(zb2), mrows, tampered, chosen, refs


def inject_type(row):
    iid = row.get(u"**注入**")
    if not iid:
        return None
    return {"T5": "T5_COINCIDENT", "T3": "T3_ABSENT", "T1": "T1_VALUE"}[iid.split("-")[1]]


def scaled_value_str(val, unit, UNIT_SCALE):
    """封 §2 E: `値 × UNIT_SCALE[単位]`。％・%・単位なしは `値` のまま。
    整数なら桁区切りなしの整数の字、そうでなければ末尾の 0 を落とした十進の字(指数表記にしない)。"""
    d = Decimal(repr(float(val)))
    scale = UNIT_SCALE.get(unit) if unit else None
    if scale is not None:
        d = d * Decimal(repr(float(scale)))
    d = d.normalize()
    if d == d.to_integral_value():
        return str(int(d))
    return format(d, "f")


def fact_lines(facts):
    """封 §2 E の context: `Fact <局所名> in <context id> equals <値の字>.` を instance の並びで。
    値の字は `str(fact["value"])`(封 §1-1 の字数と 8 / 8 一致する描き方。**instance は値を float で持つ**ので
    整数の値も `12497000000.0` の形になる)。"""
    return ["Fact %s in %s equals %s." % (f["name"].split(":")[-1], f["context"], str(f["value"])) for f in facts]


def chunk_lines(lines, limit=CHUNK_MAX):
    """95,000 字以下の chunk に行の境で割る(前から詰める)。"""
    chunks, cur, n = [], [], 0
    for ln in lines:
        add = len(ln) + (1 if cur else 0)
        if cur and n + add > limit:
            chunks.append("\n".join(cur))
            cur, n = [ln], len(ln)
        else:
            cur.append(ln)
            n += add
    if cur:
        chunks.append("\n".join(cur))
    return chunks


def claim_e(row, ptr, keys, A1, UNIT_SCALE):
    val = scaled_value_str(row[u"値"], row[u"単位"], UNIT_SCALE)
    if ptr is None:
        return "Fact equals %s." % val, None, val
    f = keys.get(A1.norm_pointer(ptr))
    if f is not None:
        return "Fact %s in %s equals %s." % (f["name"].split(":")[-1], f["context"], val), u"解けた", val
    head, _, ctx = ptr.partition("@")
    return "Fact %s in %s equals %s." % (head, ctx, val), u"解けない", val


def best_chunk(results):
    """`entity_match` が最大の chunk(同点は前)。"""
    best_i, best_v = 0, None
    for i, r in enumerate(results):
        v = r["entity_match"] if r["entity_match"] is not None else -1.0
        if best_v is None or v > best_v:
            best_i, best_v = i, v
    return best_i


# ---------------------------------------------------------------- W1・E
def run_xbrl(fv_cls, docs, MB, PR, I, ED, A1, UNIT_SCALE, pu_rows):
    rec = {r["doc"]: r for r in pu_rows}
    pu_by = {(r["doc"], r["id"]): r for r in pu_rows}
    w1_rows, e_rows, e_lists = [], [], {}
    t_mat = t_w1 = t_e = 0.0
    type_count = collections.Counter()
    t0 = time.perf_counter()
    mats = list(material_rows(docs, MB, PR, I, ED))
    t_mat = time.perf_counter() - t0
    t5_mech = collections.Counter()
    for doc, inst, mrows, tampered, chosen, refs in mats:
        # 材料が ③ と同じ組み立てか(id・値・単位・注入か)を記録と突き合わせる
        for r in mrows:
            want = pu_by[(doc, r["id"])]
            same = (want[u"注入か"] == (u"**注入**" in r) and want[u"値"] == r[u"値"] and want[u"単位"] == r[u"単位"])
            if not same:
                raise SystemExit(u"**材料が記録と違う: %s %s %r / %r**" % (doc, r["id"], r, want))
            t = inject_type(r)
            if t:
                type_count[t] += 1
        # ---- W1
        t0 = time.perf_counter()
        for r in mrows:
            want = pu_by[(doc, r["id"])]
            f = verify(fv_cls, r[u"抜粋"], tampered)
            w1_rows.append(dict({"doc": doc, "id": r["id"], u"注入か": want[u"注入か"], u"注入の型": inject_type(r),
                                 "claim": r[u"抜粋"], u"claim の字数": len(r[u"抜粋"]), u"context の字数": len(tampered)},
                                **f, **{u"分類": classify(f), u"読み": reading(r[u"抜粋"], tampered)}))
        t_w1 += time.perf_counter() - t0
        # ---- E
        facts = inst["facts"]
        lines = fact_lines(facts)
        n_chars = len("\n".join(lines))
        e_lists[doc] = {u"fact(全部が数)": len(facts), u"字数": n_chars, u"封 §1-1": list(SEAL_E_LIST[doc]),
                        u"一致": (len(facts), n_chars) == SEAL_E_LIST[doc]}
        if not e_lists[doc][u"一致"]:
            raise SystemExit(u"**E の一覧が封 §1-1 と違う: %s %r / %r。描き方が封と違う**"
                             % (doc, (len(facts), n_chars), SEAL_E_LIST[doc]))
        chunks = chunk_lines(lines)
        e_lists[doc][u"chunk"] = [len(c) for c in chunks]
        e_lists[doc][u"chunk の数"] = len(chunks)
        keys = {A1.norm_pointer("xbrl:%s@%s" % (f["name"], f["context"])): f for f in facts}
        full = "\n".join(lines)
        list_nums = set(re.findall(NUM_RE, full))
        e_lists[doc][u"数の字で '.' の無いもの"] = sorted(t for t in list_nums if "." not in t)
        fact_vals = set(round(f["value"], 6) for f in facts)
        chosen_by = {c["id"]: c for c in chosen}
        refs_by = {x["key"]: x for x in refs}
        t0 = time.perf_counter()
        for r in mrows:
            want = pu_by[(doc, r["id"])]
            ptr = want[u"席の参照先"]
            claim, resolved, val = claim_e(r, ptr, keys, A1, UNIT_SCALE)
            per = [verify(fv_cls, claim, c) for c in chunks]
            bi = best_chunk(per)
            rd = reading(claim, full)
            rd.update({u"値の字が一覧の数の字に在る(そのまま)": val in list_nums,
                       u"値の字 + '.0' が一覧の数の字に在る": (val + ".0") in list_nums,
                       u"換算した値が fact の値に在る(数として)": round(float(Decimal(val)), 6) in fact_vals,
                       u"行の値(換算なし)が fact の値に在る(数として)": round(float(r[u"値"]), 6) in fact_vals})
            e_rows.append(dict({"doc": doc, "id": r["id"], u"注入か": want[u"注入か"], u"注入の型": inject_type(r),
                                u"席の参照先": ptr, u"参照先の解決": resolved, u"換算した値": val, "claim": claim,
                                u"合成の後": want[u"**合成の後**"], u"最終判定(後)": want[u"**最終判定(後)**"],
                                u"採った chunk": bi},
                               **per[bi], **{u"分類": classify(per[bi]), u"読み": rd, u"chunk ごと": per}))
            # T5 の機構(借りた ref の単位と、植えた値がどの換算で fact に在るか)。判定には使わない
            if inject_type(r) == "T5_COINCIDENT":
                d = chosen_by[r[u"**注入**"]]["detail"]
                other = refs_by.get(d["coincident_ref_key"], {})
                t5_mech[(str(r[u"単位"]), str(other.get("unit")),
                         round(float(r[u"値"]), 6) in fact_vals)] += 1
        t_e += time.perf_counter() - t0
    t5_table = [{u"行の単位": k[0], u"借りた ref の単位": k[1], u"行の値(換算なし)が fact の値に在る": k[2], u"件数": n}
                for k, n in sorted(t5_mech.items(), key=lambda x: -x[1])]
    return w1_rows, e_rows, e_lists, dict(type_count), {u"材料の組み立て": t_mat, "W1": t_w1, "E": t_e}, t5_table


# ---------------------------------------------------------------- S
def sheet_material():
    gold = _load(POC_GOLD)
    sents = []
    for r in gold["rows"]:
        if r[u"文"] not in sents:
            sents.append(r[u"文"])
    ids_by_sent = collections.OrderedDict((s, []) for s in sents)
    for r in gold["rows"]:
        ids_by_sent[r[u"文"]].append(r["id"])
    if len(sents) != SEAL_SHEET[u"文"]:
        raise SystemExit(u"**文の数が封と違う: %d / %d**" % (len(sents), SEAL_SHEET[u"文"]))
    planted = _load(ERRDET_MAKE)[u"植えた誤り"]
    if len(planted) != SEAL_SHEET[u"誤り"]:
        raise SystemExit(u"**植えた誤りの数が封と違う: %d / %d**" % (len(planted), SEAL_SHEET[u"誤り"]))
    SM = _mod("measure/sheet_errdet_material_2026-10-17.py", "sheet_errdet_material_for_qwed")
    context = SM.extract_block()
    if len(context) != SEAL_SHEET[u"抜粋の字数"]:
        raise SystemExit(u"**抜粋の字数が封と違う: %d / %d**" % (len(context), SEAL_SHEET[u"抜粋の字数"]))
    claims, errs = [], {}
    for i, s in enumerate(sents):
        claims.append({u"文の番号": i + 1, u"元の文": s, "claim": s, u"誤り": None, "ids": ids_by_sent[s]})
    for p in planted:
        hits = [c for c in claims if p[u"元の表記"] in c[u"元の文"]]
        if len(hits) != 1 or hits[0][u"元の文"].count(p[u"元の表記"]) != 1:
            raise SystemExit(u"**元の表記が 1 文に 1 回でない: %s %r → %d 文**" % (p["id"], p[u"元の表記"], len(hits)))
        c = hits[0]
        if c[u"誤り"] is not None:
            raise SystemExit(u"**同じ文に誤りが 2 件: %s / %s**" % (c[u"誤り"]["id"], p["id"]))
        if p["id"] not in c["ids"]:
            raise SystemExit(u"**誤りの id がその文の id に無い: %s %r**" % (p["id"], c["ids"]))
        new = c[u"元の文"].replace(p[u"元の表記"], p[u"植えた表記"], 1)
        n_rep = (len(new) - len(c[u"元の文"]) == len(p[u"植えた表記"]) - len(p[u"元の表記"])) and (p[u"植えた表記"] in new)
        if not n_rep or new.count(p[u"植えた表記"]) != 1:
            raise SystemExit(u"**置き換えた回数が 1 でない: %s**" % p["id"])
        c["claim"] = new
        c[u"誤り"] = {"id": p["id"], u"型": p[u"型"], u"群": p[u"群"], u"元の表記": p[u"元の表記"],
                     u"植えた表記": p[u"植えた表記"], u"置き換えた回数": 1}
        errs[p["id"]] = c
    if sum(1 for c in claims if c[u"誤り"]) != 8:
        raise SystemExit(u"**誤りの文が 8 でない**")
    return claims, context, planted


def run_sheet(fv_cls, claims, context):
    t0 = time.perf_counter()
    rows = []
    for c in claims:
        f = verify(fv_cls, c["claim"], context)
        rows.append(dict({u"文の番号": c[u"文の番号"], "claim": c["claim"], u"誤り": c[u"誤り"], "ids": c["ids"],
                          u"claim の字数": len(c["claim"]), u"context の字数": len(context)},
                         **f, **{u"分類": classify(f), u"読み": reading(c["claim"], context)}))
    return rows, time.perf_counter() - t0


# ---------------------------------------------------------------- 対照
def run_controls(fv_cls, e_rows, e_lists_chunks, sheet_rows):
    t0 = time.perf_counter()
    out = {}
    # C-1
    c1 = {k: verify(fv_cls, v, C1_CONTEXT) for k, v in C1_CLAIMS.items()}
    ok_a = c1["a"]["entity_match"] == 1.0 and c1["a"]["deterministic_verdict"] == "SUPPORTED"
    ok_b = (c1["b"]["entity_match"] is not None and c1["b"]["entity_match"] < 1.0
            and c1["b"]["deterministic_verdict"] == "SUPPORTED")
    out["C-1"] = {u"期待": u"(a) entity_match 1.0・SUPPORTED / (b) entity_match < 1.0・SUPPORTED",
                  "a": c1["a"], "b": c1["b"], u"**期待どおり**": bool(ok_a and ok_b)}
    # C-2
    base = [r for r in e_rows if r["doc"] == C2_DOC and r["id"] == C2_ID][0]
    if base[u"合成の後"] != "GROUNDED":
        raise SystemExit(u"**C-2 の行が GROUNDED でない: %s**" % base[u"合成の後"])
    val1 = str(int(Decimal(base[u"換算した値"]) + 1))
    claim1 = base["claim"].replace("equals %s." % base[u"換算した値"], "equals %s." % val1)
    if claim1 == base["claim"]:
        raise SystemExit(u"**C-2 の +1 が claim に入らなかった**")
    per = [verify(fv_cls, claim1, c) for c in e_lists_chunks[C2_DOC]]
    bi = best_chunk(per)
    r2 = per[bi]
    out["C-2"] = {u"期待": u"entity_match < 1.0 かつ verdict は SUPPORTED のまま", u"元の claim": base["claim"],
                  u"+1 の claim": claim1, u"元の行の結果": {k: base[k] for k in FIELDS},
                  u"採った chunk": bi, u"chunk ごと": per, u"結果": r2,
                  u"**期待どおり**": bool(r2["entity_match"] is not None and r2["entity_match"] < 1.0
                                   and r2["deterministic_verdict"] == "SUPPORTED")}
    # C-3
    s = [r for r in sheet_rows if r[u"誤り"] and r[u"誤り"]["id"] == C3_ID][0]
    planted = s[u"誤り"][u"植えた表記"]
    a = s["claim"].index(planted)
    b = a + len(planted)
    all_tokens = [(m.group(0), m.start(), m.end()) for m in re.finditer(NUM_RE, s["claim"])]
    from_number = [t for t, x, y in all_tokens if a <= x and y <= b]
    out["C-3"] = {u"期待": u"その数から抜けるのは `385`・`483` の 2 つだけ", u"文": s["claim"], u"植えた表記": planted,
                  u"正規表現": NUM_RE, u"文全体から抜けた字": [t for t, _x, _y in all_tokens],
                  u"**その数から抜けた字**": from_number, u"**期待どおり**": from_number == ["385", "483"]}
    return out, time.perf_counter() - t0


# ---------------------------------------------------------------- Audit Core 側の写し(再実行しない)
def audit_core_copy(pu_rows):
    inj = [r for r in pu_rows if r[u"注入か"]]
    pla = [r for r in pu_rows if not r[u"注入か"]]

    def dist(rows, key):
        c = collections.Counter(("None" if r[key] is None else r[key]) for r in rows)
        return dict(sorted(c.items()))
    ec = _load(ERRDET_CORE)[u"検出 / 保留 / 見落とし(誤り 8 件)"]
    return {u"出どころ": {"XBRL": "fixtures/xbrl/cd8/period_unit_hold_2026-10-19.json",
                       u"表計算": "fixtures/sheet/errdet_core_2026-10-17.json"},
            "XBRL": {u"行": len(pu_rows), u"注入": len(inj), u"無改変": len(pla),
                     u"注入の engine の state(合成の後)": dist(inj, u"**合成の後**"),
                     u"無改変の engine の state(合成の後)": dist(pla, u"**合成の後**"),
                     u"注入の最終判定(後)": dist(inj, u"**最終判定(後)**"),
                     u"無改変の最終判定(後)": dist(pla, u"**最終判定(後)**"),
                     u"**注入で GROUNDED**": sum(1 for r in inj if r[u"**合成の後**"] == "GROUNDED"),
                     u"**注入で検査通過(誤りを通す)**": sum(1 for r in inj if r[u"**最終判定(後)**"] == u"検査通過")},
            u"表計算": {u"検出": ec[u"検出"][u"件数"], u"検出の id": ec[u"検出"]["ids"],
                     u"保留": ec[u"保留"][u"件数"], u"保留の id": ec[u"保留"]["ids"],
                     u"見落とし": ec[u"見落とし"][u"件数"]}}


# ---------------------------------------------------------------- Q-17(木)
def tree_state():
    def git(args):
        r = subprocess.run(["git"] + args, cwd=ROOT, capture_output=True, text=True)
        return r.stdout
    numstat = [l for l in git(["diff", "--numstat", "HEAD", "--", "core", "adapters"]).splitlines() if l.strip()]
    untracked = [l for l in git(["status", "--short", "--", "core", "adapters"]).splitlines() if l.strip()]
    changed = sum(int(a) + int(b) for a, b, _p in (l.split("\t") for l in numstat))
    exists = {rel: os.path.exists(os.path.join(ROOT, rel)) for rel in SEAL_SIDE_FILES + RESULT_SIDE_FILES}
    return {u"core/・adapters/ の差分(numstat の行)": numstat, u"core/・adapters/ の差分の行数": changed,
            u"core/・adapters/ の status": untracked, u"封側の file(在る)": [r for r in SEAL_SIDE_FILES if exists[r]],
            u"結果側の file(在る)": [r for r in RESULT_SIDE_FILES if exists[r]],
            u"pytest(tests/measure、3.9)": None}


def parse_pytest_log(path):
    lines = io.open(path, encoding="utf-8", errors="replace").read().splitlines()
    tail = [l for l in lines if "passed" in l or "failed" in l][-1:]
    if not tail:
        raise SystemExit(u"**pytest の要約の行が無い: %s**" % path)
    red = [l.split()[1] for l in lines if l.startswith("FAILED ")]
    m = re.search(r"(\d+) passed", tail[0])
    f = re.search(r"(\d+) failed", tail[0])
    return {"log": os.path.basename(path), u"要約の行": tail[0].strip(),
            "passed": int(m.group(1)) if m else 0, "failed": int(f.group(1)) if f else 0, u"赤の試験": red}


# ---------------------------------------------------------------- 予測との照合
def _cnt(rows, pred):
    return sum(1 for r in rows if pred(r))


def tally(w1, e, e_lists, s, ctrl, ac, zero, secs, tree, type_count):
    inj_w = [r for r in w1 if r[u"注入か"]]
    inj_e = [r for r in e if r[u"注入か"]]
    pla_e = [r for r in e if not r[u"注入か"]]
    gr_e = [r for r in e if r[u"合成の後"] == "GROUNDED"]
    err_s = [r for r in s if r[u"誤り"]]
    st_w = collections.Counter(r["status"] for r in w1)
    vd_w = collections.Counter(r["deterministic_verdict"] for r in w1)
    cls_w = collections.Counter(r[u"分類"] for r in w1)
    cls_inj_w = collections.Counter(r[u"分類"] for r in inj_w)
    vd_e = collections.Counter(r["deterministic_verdict"] for r in e)
    cls_inj_e = collections.Counter(r[u"分類"] for r in inj_e)
    st_s = collections.Counter(r["status"] for r in s)
    vd_s = collections.Counter(r["deterministic_verdict"] for r in s)
    cls_err_s = collections.Counter(r[u"分類"] for r in err_s)
    q = []

    def add(sym, pred, actual, hit, parts=None):
        q.append({u"記号": sym, u"予測": pred, u"実測": actual, u"当たり": hit, **({u"内訳": parts} if parts else {})})

    add("Q-1", u"W1: status UNVERIFIABLE 192 / 192(VERIFIED 0・BLOCKED 0)",
        dict(st_w), st_w.get("UNVERIFIABLE", 0) == 192)
    add("Q-2", u"W1: verdict は NEUTRAL か INSUFFICIENT_EVIDENCE 192 / 192(SUPPORTED 0・REFUTED 0)",
        dict(vd_w), vd_w.get("SUPPORTED", 0) == 0 and vd_w.get("REFUTED", 0) == 0)
    c0 = _cnt(w1, lambda r: r["citations"] == 0)
    k0 = _cnt(w1, lambda r: r["keyword_overlap"] == 0.0)
    add("Q-3", u"W1: citations 0 が 192 / 192・keyword_overlap 0.0 が 192 / 192",
        {u"citations 0": c0, u"keyword_overlap 0.0": k0}, c0 == 192 and k0 == 192)
    e1_inj = _cnt(inj_w, lambda r: r["entity_match"] == 1.0)
    e1_all = _cnt(w1, lambda r: r["entity_match"] == 1.0)
    add("Q-4", u"W1: entity_match 1.0 は 注入 64 / 64・全体 185 以上 / 192",
        {u"注入": e1_inj, u"全体": e1_all}, e1_inj == 64 and e1_all >= 185)
    add("Q-5", u"W1: 違うと言う 注入 0 / 64・通す 0 / 192・判定なし 185 以上",
        {u"注入の分類": dict(cls_inj_w), u"全体の分類": dict(cls_w)},
        cls_inj_w.get(u"違うと言う", 0) == 0 and cls_w.get(u"通す", 0) == 0 and cls_w.get(u"判定なし", 0) >= 185)
    n_chunks = sum(v[u"chunk の数"] for v in e_lists.values())
    split_ok = all(v[u"chunk の数"] == SEAL_CHUNKS.get(d, 1) for d, v in e_lists.items())
    add("Q-6", u"E: 一覧の字数 8 / 8 一致・chunk 11(S100YWGX・S100YXMA・S100YZCT が 2、他 1)",
        {u"一致": sum(1 for v in e_lists.values() if v[u"一致"]), u"chunk": n_chunks,
         u"書類ごとの chunk": {d: v[u"chunk の数"] for d, v in e_lists.items()}},
        sum(1 for v in e_lists.values() if v[u"一致"]) == 8 and n_chunks == 11 and split_ok)
    add("Q-7", u"E: SUPPORTED 180 以上 / 192", dict(vd_e), vd_e.get("SUPPORTED", 0) >= 180)
    t5 = [r for r in inj_e if r[u"注入の型"] == "T5_COINCIDENT"]
    t31 = [r for r in inj_e if r[u"注入の型"] in ("T3_ABSENT", "T1_VALUE")]
    t5_1 = _cnt(t5, lambda r: r["entity_match"] == 1.0)
    t31_lt = _cnt(t31, lambda r: r["entity_match"] is not None and r["entity_match"] < 1.0)
    add("Q-8", u"E: T5 50 行の entity_match 1.0 は 35 以上・T3+T1 14 行の < 1.0 は 12 以上",
        {u"T5 の行": len(t5), u"T5 で 1.0": t5_1, u"T3+T1 の行": len(t31), u"T3+T1 で < 1.0": t31_lt},
        t5_1 >= 35 and t31_lt >= 12)
    add("Q-9", u"E: 通す 注入 35 以上 / 64。Audit Core は GROUNDED 0 / 64・検査通過 0 / 64",
        {u"QWED が通す(注入)": cls_inj_e.get(u"通す", 0), u"注入の分類": dict(cls_inj_e),
         u"Audit Core 注入で GROUNDED": ac["XBRL"][u"**注入で GROUNDED**"],
         u"Audit Core 注入で検査通過": ac["XBRL"][u"**注入で検査通過(誤りを通す)**"]},
        cls_inj_e.get(u"通す", 0) >= 35 and ac["XBRL"][u"**注入で GROUNDED**"] == 0
        and ac["XBRL"][u"**注入で検査通過(誤りを通す)**"] == 0)
    p1 = _cnt(pla_e, lambda r: r["entity_match"] == 1.0)
    add("Q-10", u"E: 無改変 128 行の entity_match 1.0 は 60〜100", {u"無改変で 1.0": p1, u"無改変の行": len(pla_e)},
        60 <= p1 <= 100)
    g1 = _cnt(gr_e, lambda r: r["entity_match"] == 1.0)
    add("Q-11", u"E: Audit Core が GROUNDED にした 18 行の entity_match 1.0 は 14 以上",
        {u"GROUNDED の行": len(gr_e), u"1.0": g1}, len(gr_e) == 18 and g1 >= 14)
    add("Q-12", u"C-2: entity_match < 1.0 かつ SUPPORTED のまま",
        {k: ctrl["C-2"][u"結果"][k] for k in ("entity_match", "deterministic_verdict")}, ctrl["C-2"][u"**期待どおり**"])
    s_c0 = _cnt(s, lambda r: r["citations"] == 0)
    add("Q-13", u"S: status UNVERIFIABLE 11 / 11・verdict NEUTRAL か INSUFFICIENT_EVIDENCE 11 / 11・citations 0 が 11 / 11",
        {"status": dict(st_s), "verdict": dict(vd_s), u"citations 0": s_c0},
        st_s.get("UNVERIFIABLE", 0) == 11 and vd_s.get("SUPPORTED", 0) == 0 and vd_s.get("REFUTED", 0) == 0 and s_c0 == 11)
    s_e1 = _cnt(err_s, lambda r: r["entity_match"] == 1.0)
    add("Q-14", u"S: 誤り 8 文で entity_match 1.0 は 6 以上・違うと言う ≦ 2 / 8。Audit Core は 検出 4 / 保留 4 / 見落とし 0",
        {u"誤りの文": len(err_s), u"1.0": s_e1, u"分類": dict(cls_err_s),
         u"Audit Core": {k: ac[u"表計算"][k] for k in (u"検出", u"保留", u"見落とし")}},
        s_e1 >= 6 and cls_err_s.get(u"違うと言う", 0) <= 2 and ac[u"表計算"][u"検出"] == 4
        and ac[u"表計算"][u"保留"] == 4 and ac[u"表計算"][u"見落とし"] == 0)
    add("Q-15", u"C-3: 抜けた字は `385`・`483` のちょうど 2 つ", ctrl["C-3"][u"**その数から抜けた字**"],
        ctrl["C-3"][u"**期待どおり**"])
    add("Q-16", u"鍵 0 件・provider=None・3 本 + 対照の所要 300 秒未満",
        {u"鍵": zero[u"在った件数"], "provider": zero["provider"], u"3 本 + 対照の秒": secs[u"3 本 + 対照"]},
        zero[u"在った件数"] == 0 and zero["provider"] is None and secs[u"3 本 + 対照"] < 300)
    q.append(q17_entry(tree))
    return q


def q17_entry(tree):
    py = tree[u"pytest(tests/measure、3.9)"]
    hit = None
    if py is not None:
        hit = (tree[u"core/・adapters/ の差分の行数"] == 0 and not tree[u"core/・adapters/ の status"]
               and len(tree[u"封側の file(在る)"]) == 2 and len(tree[u"結果側の file(在る)"]) == 4 and py["failed"] == 0)
    return {u"記号": "Q-17", u"予測": u"core/・adapters/ の差分 0 行・封側 2 本・結果側 4 本・pytest の赤 0",
            u"実測": {u"差分の行数": tree[u"core/・adapters/ の差分の行数"], u"封側": len(tree[u"封側の file(在る)"]),
                   u"結果側": len(tree[u"結果側の file(在る)"]), "pytest": py},
            u"当たり": hit, u"注": None if py is not None else u"pytest は門を書いた後に `--set-pytest-log` で写す(未測)"}


def summary(q):
    hit = sum(1 for x in q if x[u"当たり"] is True)
    miss = sum(1 for x in q if x[u"当たり"] is False)
    unm = sum(1 for x in q if x[u"当たり"] is None)
    return {u"当たり": hit, u"外れ": miss, u"未測": unm, u"外れの記号": [x[u"記号"] for x in q if x[u"当たり"] is False],
            u"欄ごと": q}


# ---------------------------------------------------------------- main
def measure():
    zero = check_zero_usd()
    fv, env = import_qwed()
    fv_cls = fv.FactVerifier
    from adapters.xbrl import edinet as ED
    from adapters.xbrl import instance as I
    from adapters.xbrl import prose as PR
    from adapters.xbrl import vocabulary as V
    MB = _mod("measure/xbrl_cd_material_2026-10-17.py", "cd_material_for_qwed")
    A1 = MB.A1
    docs = _load(DRAW)[u"引いた 8 件"]
    pu_rows = _load(REC_PU)["rows"]
    if len(pu_rows) != 192:
        raise SystemExit(u"**記録の行が 192 でない: %d**" % len(pu_rows))
    print(u"W1 / E ...")
    w1, e, e_lists, type_count, t_x, t5_table = run_xbrl(fv_cls, docs, MB, PR, I, ED, A1, V.UNIT_SCALE, pu_rows)
    if type_count != SEAL_INJECT_TYPES:
        raise SystemExit(u"**注入の型の数が封と違う: %r / %r**" % (type_count, SEAL_INJECT_TYPES))
    print(u"  W1 %d 行 %.1f 秒 / E %d 行 %.1f 秒(材料 %.1f 秒)" % (len(w1), t_x["W1"], len(e), t_x["E"], t_x[u"材料の組み立て"]))
    print(u"S ...")
    claims, context, _planted = sheet_material()
    s, t_s = run_sheet(fv_cls, claims, context)
    print(u"  S %d 文 %.1f 秒" % (len(s), t_s))
    print(u"対照 ...")
    # E の chunk を対照 C-2 のために組み直す(同じ関数・同じ材料。材料の組み立ては繰り返さない: 一覧は E で保存した字数と一致を確かめた)
    chunks_by_doc = {}
    for doc in docs:
        if doc == C2_DOC:
            zb = io.open(ED.cache_path(doc), "rb").read()
            lines = fact_lines(I.load_instance(zb)["facts"])
            if (len(lines), len("\n".join(lines))) != SEAL_E_LIST[doc]:
                raise SystemExit(u"**C-2 の一覧が封 §1-1 と違う**")
            chunks_by_doc[doc] = chunk_lines(lines)
    ctrl, t_c = run_controls(fv_cls, e, chunks_by_doc, s)
    print(u"  C-1 %s / C-2 %s / C-3 %s(%.1f 秒)" % (ctrl["C-1"][u"**期待どおり**"], ctrl["C-2"][u"**期待どおり**"],
                                                   ctrl["C-3"][u"**期待どおり**"], t_c))
    secs = {u"材料の組み立て": round(t_x[u"材料の組み立て"], 2), "W1": round(t_x["W1"], 2), "E": round(t_x["E"], 2),
            "S": round(t_s, 2), u"対照": round(t_c, 2),
            u"3 本 + 対照": round(t_x["W1"] + t_x["E"] + t_s + t_c, 2)}
    ac = audit_core_copy(pu_rows)
    tree = tree_state()
    q = tally(w1, e, e_lists, s, ctrl, ac, zero, secs, tree, type_count)
    counts = {
        "W1": {u"行": len(w1), "status": dict(collections.Counter(r["status"] for r in w1)),
               "verdict": dict(collections.Counter(r["deterministic_verdict"] for r in w1)),
               u"分類": dict(collections.Counter(r[u"分類"] for r in w1)),
               u"注入の分類": dict(collections.Counter(r[u"分類"] for r in w1 if r[u"注入か"])),
               u"entity_match 1.0": _cnt(w1, lambda r: r["entity_match"] == 1.0)},
        "E": {u"行": len(e), "status": dict(collections.Counter(r["status"] for r in e)),
              "verdict": dict(collections.Counter(r["deterministic_verdict"] for r in e)),
              u"分類": dict(collections.Counter(r[u"分類"] for r in e)),
              u"注入の分類": dict(collections.Counter(r[u"分類"] for r in e if r[u"注入か"])),
              u"無改変の分類": dict(collections.Counter(r[u"分類"] for r in e if not r[u"注入か"])),
              u"entity_match 1.0": _cnt(e, lambda r: r["entity_match"] == 1.0),
              u"参照先の解決": dict(collections.Counter(str(r[u"参照先の解決"]) for r in e)),
              u"chunk の数": sum(v[u"chunk の数"] for v in e_lists.values())},
        "S": {u"文": len(s), u"id": sum(len(r["ids"]) for r in s),
              "status": dict(collections.Counter(r["status"] for r in s)),
              "verdict": dict(collections.Counter(r["deterministic_verdict"] for r in s)),
              u"誤りの文の分類": dict(collections.Counter(r[u"分類"] for r in s if r[u"誤り"])),
              u"entity_match 1.0": _cnt(s, lambda r: r["entity_match"] == 1.0)}}
    # 外れの原因の読み(同じ材料を QWED と同じ正規表現で読んだ数。判定には使わない。QWED は呼んでいない)
    def grp(rows, name):
        return {name: len(rows),
                u"値の字が一覧の数の字に在る(そのまま)": _cnt(rows, lambda r: r[u"読み"][u"値の字が一覧の数の字に在る(そのまま)"]),
                u"値の字 + '.0' が一覧の数の字に在る": _cnt(rows, lambda r: r[u"読み"][u"値の字 + '.0' が一覧の数の字に在る"]),
                u"換算した値が fact の値に在る(数として)": _cnt(rows, lambda r: r[u"読み"][u"換算した値が fact の値に在る(数として)"]),
                u"行の値(換算なし)が fact の値に在る(数として)": _cnt(rows, lambda r: r[u"読み"][u"行の値(換算なし)が fact の値に在る(数として)"])}
    cause = {
        "W1": {u"claim に英字の語が在る行": _cnt(w1, lambda r: r[u"読み"][u"claim の英字の語"]),
               u"claim に英字の語が在る行の verdict": dict(collections.Counter(
                   r["deterministic_verdict"] for r in w1 if r[u"読み"][u"claim の英字の語"])),
               u"context に無い数の字が在る行": _cnt(w1, lambda r: r[u"読み"][u"context に無い数の字"]),
               u"context に無い数の字が在る行の entity_match < 1.0": _cnt(
                   w1, lambda r: r[u"読み"][u"context に無い数の字"] and r["entity_match"] is not None and r["entity_match"] < 1.0),
               u"entity_match < 1.0 の行": _cnt(w1, lambda r: r["entity_match"] is not None and r["entity_match"] < 1.0),
               u"明細(判定なし以外)": [{"doc": r["doc"], "id": r["id"], u"注入か": r[u"注入か"], u"分類": r[u"分類"],
                                  "verdict": r["deterministic_verdict"], "entity_match": r["entity_match"],
                                  u"英字の語": r[u"読み"][u"claim の英字の語"], u"context に無い数の字": r[u"読み"][u"context に無い数の字"],
                                  u"claim の先頭と末尾": [r["claim"][:12], r["claim"][-12:]]}
                                 for r in w1 if r[u"分類"] != u"判定なし"]},
        "E": {u"全体": grp(e, u"行"), u"注入 T5": grp([r for r in e if r[u"注入の型"] == "T5_COINCIDENT"], u"行"),
              u"注入 T3+T1": grp([r for r in e if r[u"注入の型"] in ("T3_ABSENT", "T1_VALUE")], u"行"),
              u"無改変": grp([r for r in e if not r[u"注入か"]], u"行"),
              u"Audit Core が GROUNDED": grp([r for r in e if r[u"合成の後"] == "GROUNDED"], u"行"),
              u"T5 の機構(行の単位 × 借りた ref の単位)": t5_table,
              u"REFUTED の行": _cnt(e, lambda r: r["deterministic_verdict"] == "REFUTED"),
              u"REFUTED で claim に否定語の部分一致が在る": _cnt(
                  e, lambda r: r["deterministic_verdict"] == "REFUTED" and r[u"読み"][u"claim の否定語(部分一致)"]),
              u"REFUTED で claim に否定語の部分一致が無い": _cnt(
                  e, lambda r: r["deterministic_verdict"] == "REFUTED" and not r[u"読み"][u"claim の否定語(部分一致)"]),
              u"一覧の数の字で '.' の無いもの(書類ごと)": {d: v[u"数の字で '.' の無いもの"] for d, v in e_lists.items()}},
        "S": {u"context に無い数の字が在る文": [{u"文の番号": r[u"文の番号"], u"誤り": (r[u"誤り"] or {}).get("id"),
                                            u"context に無い数の字": r[u"読み"][u"context に無い数の字"],
                                            "entity_match": r["entity_match"]}
                                           for r in s if r[u"読み"][u"context に無い数の字"]]}}
    return {"seal": SEAL, "seal_commit": SEAL_COMMIT,
            "step": u"封 §6 段 B。**QWED 7.3.0 の 0 USD の入口に同じ材料を通した。engine 不変。LLM は呼んでいない**",
            u"0 USD": zero, u"入口": env, u"所要秒": secs, u"分母": {u"注入の型": type_count, u"E の一覧": e_lists,
                                                            u"表計算": SEAL_SHEET},
            u"**件数**": counts, u"**Audit Core 側の写し(再実行しない)**": ac, u"対照": ctrl, u"木": tree,
            u"**外れの原因の読み**": cause,
            u"**予測との照合**": summary(q),
            "rows": {"W1": w1, "E": e, "S": s},
            "limits": [u"**QWED の 0 USD の決定論の部分だけ**(LLM の経路・Math・GraphFact は測っていない)",
                       u"**入力の形はこちらが決めた**(W1・S は日本語、E は参照先の解決と単位の換算を Audit Core から渡した)",
                       u"**E の一覧の値の字は `str(float)`**(封 §1-1 の字数と 8 / 8 一致する描き方。整数の値も `.0` が付く)",
                       u"**同じ 8 書類・同じ 35 件である。**", u"**qwed 7.3.0 の数である。**",
                       u"**誤りを通す率(偽陰性)だけを並べる。**"]}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--set-pytest-log", help=u"既存の記録に Q-17 の pytest の結果を写す(測定はしない)")
    a = ap.parse_args(argv)
    if a.set_pytest_log:
        rec = _load(OUT)
        rec[u"木"] = tree_state()
        rec[u"木"][u"pytest(tests/measure、3.9)"] = parse_pytest_log(a.set_pytest_log)
        q = [x for x in rec[u"**予測との照合**"][u"欄ごと"] if x[u"記号"] != "Q-17"] + [q17_entry(rec[u"木"])]
        rec[u"**予測との照合**"] = summary(q)
        with io.open(OUT, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print(json.dumps(rec[u"**予測との照合**"][u"欄ごと"][-1], ensure_ascii=False, indent=1))
        print(u"当たり %(当たり)d / 外れ %(外れ)d / 未測 %(未測)d" % rec[u"**予測との照合**"])
        return 0
    rec = measure()
    p = rec[u"**予測との照合**"]
    for x in p[u"欄ごと"]:
        print(u"%-5s %s  %s" % (x[u"記号"], {True: u"当たり", False: u"外れ", None: u"未測"}[x[u"当たり"]],
                               json.dumps(x[u"実測"], ensure_ascii=False)))
    print(u"当たり %(当たり)d / 外れ %(外れ)d / 未測 %(未測)d" % p)
    print(u"所要秒 %s" % json.dumps(rec[u"所要秒"], ensure_ascii=False))
    if a.write:
        with io.open(OUT, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print(u"wrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
