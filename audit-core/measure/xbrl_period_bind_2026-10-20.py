# -*- coding: utf-8 -*-
u"""期を縛る直し P22 の段 1 の測定 ― 封 ``docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md`` §2(E-1〜E-7。E-8 は段 2 なので判定しない)。

    cd audit-core
    python3 measure/xbrl_period_bind_2026-10-20.py --stage all                 # 記録 fixtures/xbrl/period_bind_2026-10-20.json を書く
    python3 measure/xbrl_period_bind_2026-10-20.py --stage e1 --out <file> --docs S100YMFV    # 軽い走らせ直し(--out 必須)

**0 USD・通信なし・鍵の値は読まない。** 書類は ``~/.cache/audit-core/edinet/*.zip`` の手元の cache だけ(無い書類は取りに行かない・
「無い」と記録する)。engine(``core/``・``adapters/``)は**測る側から 1 行も変えない**(P22 は別に実装済み)。
穴 B の道具(``measure/xbrl_point_prior_2026-10-20.py`` の ``find_sites``・``classify_after``)・儀式(``measure/ritual_2026-10-20.py``
の ``build``)・名指しの直しの 40 書類(``measure/xbrl_naming_fix_2026-10-20.py`` の ``untouched_40``)・段 2 の材料
(``measure/xbrl_hybrid_s2_2026-10-20.py`` の ``rebuild``)は import して使う(書き直さない)。

  E-1  穴 B の 485 件(既定 P21 で GROUNDED の site に前期の値を入れた注入)を **P22** で再検証。対照として同じ注入を P21 で再検証し、
       穴 B の記録(``fixtures/xbrl/point_prior_2026-10-20.json``)の 485 行と 1 行ずつ一致することを確かめる(道具の再現)。
  E-2  経営分析の文を持つ 67 書類の**無改変**を P21 と P22 で ``verify_document`` し、claim ごとに
       ``(state, pointers, reason, recomputed, form)`` を比べる。動いた行の一覧・向き・手がかりあり 190 / 当期 1,726 の不動を数える。
  E-3  名指しの直しの無改変 40 書類(``naming_fix/p21_2026-10-20.json`` の集合)で同じ比較。
  E-4  段 2 の材料(24 行 × 8 書類)の Core 自身を P22 で当て直し T6 の GROUNDED を数える(対照: P21 で当て直すと材料の記録に 192 行全部一致)。
       α 型(``verify_external``、席の参照先)は 192 行のうち席が参照先を名指した行を再計算して記録との差を数える(profile を取らない経路)。
  E-5  儀式(同梱の 1 書類 E36539、241 件)を P22 で。対照: P21 で回すと儀式の記録に 241 件全部一致。
  E-6  E-2・E-3 で動いた GROUNDED の行に機械の印(文に「減少」「減」)を付ける。型の読みは人の読み(結果文書)。
  E-7  engine の差分の行数(``git diff HEAD --numstat``)と、既存試験 ``tests/adapters/xbrl`` の結果(``--stage all`` のとき pytest を走らせる)。

段 2(2026-10-20。既定 P21 -> P22):
    python3 measure/xbrl_period_bind_2026-10-20.py --stage default [--run-tests]   # 記録の新欄 ``stage2_default_2026-10-20`` を足す(他の欄は 1 字も変えない)
  製品の経路 = **profile を省いた** ``verify_document`` が P22 の数を出すことの証拠。E-1(485 件)・E-2(67 書類の無改変)・E-5(儀式 240 件)を
  profile 省略で回し、段 1 の記録の P22 の行と 1 行ずつ比べる(差 0 が当たり)。段 1 の測定(``--stage e1|e2|e3|e4|e5|e7|all``)は
  P21・P22 を**明示**して比べるので、既定が P22 になった後も同じ数が出る(``--stage all`` の正本の記録への上書きだけは P21 が既定の時点に限る)。
"""
from __future__ import print_function

import argparse
import collections
import hashlib
import importlib.util
import inspect
import io
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))


def _mod(rel, name):
    sp = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


PP = _mod("measure/xbrl_point_prior_2026-10-20.py", "point_prior_for_period_bind")
RIT = PP._load_ritual()
NF = _mod("measure/xbrl_naming_fix_2026-10-20.py", "naming_fix_for_period_bind")
HS2 = _mod("measure/xbrl_hybrid_s2_2026-10-20.py", "hybrid_s2_for_period_bind")
FP = PP.FP
HT = HS2.HT
MB = HS2.MB
IJ = HS2.IJ
A1 = MB.A1

from adapters.xbrl import edinet as ED          # noqa: E402
from adapters.xbrl import recipes as R          # noqa: E402
from adapters.xbrl import verify_document as VD  # noqa: E402
from adapters.xbrl import vocabulary as V        # noqa: E402

SEAL = "docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md"
OUT_REL = "fixtures/xbrl/period_bind_2026-10-20.json"
OLD, NEW = "P21", "P22"
POINT_PRIOR_REL = "fixtures/xbrl/point_prior_2026-10-20.json"
#: 儀式の記録。2026-10-20 段 2 で ``ritual_2026-10-20.json`` は P22(既定)で採り直した。段 1 の対照は P21 のときの記録なので、
#: 同じ中身(sha256 dad4c56e…)の写し ``ritual_2026-10-20_p21.json`` を読む。段 1 の記録の ``入力の sha256`` の欄の名前は変えない(RITUAL_KEY_AT_MEASURE)。
RITUAL_REL = "fixtures/xbrl/ritual_2026-10-20_p21.json"
RITUAL_KEY_AT_MEASURE = "fixtures/xbrl/ritual_2026-10-20.json"
RITUAL_P22_REL = "fixtures/xbrl/ritual_2026-10-20.json"
STAGE2_KEY = "stage2_default_2026-10-20"
CONTROL_DOC = "S100YMFV"      # 注入 4 件(P21 では 4 件とも通し、P22 では 4 件とも止める)。『0 件』の対照に使う軽い書類
NAMING_REL = "fixtures/xbrl/naming_fix/p21_2026-10-20.json"
S2_MATERIAL_REL = "fixtures/xbrl/gen_c/hybrid_s2_material_2026-10-20.json"
S2_REC_REL = "fixtures/xbrl/gen_c/hybrid_s2_2026-10-20.json"
#: 封 §0 の代価 26 / 手がかりあり 190 / 当期 1,726 の数え方(tests/measure/test_xbrl_period_bind_seal.py の CUE と同じ字)。
CUE = re.compile(u"前期|前年|前連結会計年度|前事業年度|\\(同|（同|前期末|前年度")
DEC_RX = re.compile(u"減少|減")
INC_RX = re.compile(u"増加|増")
#: 封 §1・§4 は既存試験の直しを 3 か所(test_vocabulary.py の一覧 2・test_p20.py の除外 1)と書いた。ほかに直した試験(実装席が見つけ、司令塔が 1 行の直しを決めた)。
#: これが空でないとき E-7(『既存試験 全部緑のまま』= 封の 3 か所を直した後の緑)は外れ。
EXTRA_EXISTING_FIXES = [u"tests/adapters/xbrl/test_recipes_p21.py::FlagShapeTest::test_only_p21_has_the_flag_on(期待を [P21] から [P21, P22] に 1 行。P22 は P21 から作るので last_branch_cues を引き継ぐ)"]
KEY_NAMES = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL", "EDINET_API_KEY", "OPENAI_API_KEY")


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def frac(a, b):
    return {u"件": a, u"分母": b, u"率": pct(a, b)}


def sha_file(p):
    with io.open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def jload(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return json.load(fh)


def git(*a):
    return PP.git(*a)


def claim_key(c):
    return (c["state"], tuple(c["pointers"]), c["reason"], c["recomputed"], c["form"])


def view(c):
    return {u"state": c["state"], u"pointers": c["pointers"], u"reason": c["reason"], u"recomputed": c["recomputed"],
            u"form": c["form"]}


# ====================================================================================================
# E-1
def reverify(zb, text, profile):
    return {c["id"]: c for c in VD.verify_document(zb, profile, text)["claims"]}


def inject_with_profile(doc_id, zb, text0, sites, sentences, profile):
    u"""``PP.inject_doc`` と同じ作り(1 文 1 件・25 件の束・同じ順)で、**profile だけ**引数にしたもの。
    注入の text は profile に依らず決まる(site と 後の字 は P21 の土台から作った)。"""
    pending = [s for s in sites if s[u"作れた"]]
    rows = []
    while pending:
        batch, used, rest = [], set(), []
        for s in pending:
            if len(batch) < PP.BATCH and s[u"_si"] not in used:
                batch.append(s)
                used.add(s[u"_si"])
            else:
                rest.append(s)
        pending = rest
        new_sents = {}
        plan = []
        for s in batch:
            sent = sentences[s[u"_si"]]
            new_sents[s[u"_si"]] = sent[:s[u"_a"]] + s[u"後の字"] + sent[s[u"_b"]:]
            vals = [v for (_a, _b, v, _u, _p) in FP.E.iter_numbers(s[u"後の字"])]
            plan.append((s, vals[0] if len(vals) == 1 else None))
        text = text0
        for (s, exp) in sorted(plan, key=lambda t: -text0.find(sentences[t[0][u"_si"]])):
            pos = text.find(sentences[s[u"_si"]])
            if pos < 0:
                rows.append(dict(PP._row(doc_id, s), **{u"結果": PP.K_ELSE, u"結果の細目": u"sentence_not_found"}))
                continue
            text = text[:pos] + new_sents[s[u"_si"]] + text[pos + len(sentences[s[u"_si"]]):]
        got = reverify(zb, text, profile)
        for (s, exp) in plan:
            if any(r[u"id"] == s[u"id"] and r[u"結果の細目"] == u"sentence_not_found" for r in rows if r[u"書類"] == doc_id):
                continue
            c = got.get(s[u"id"])
            row = PP._row(doc_id, s)
            if c is None:
                row.update({u"結果": PP.K_ELSE, u"結果の細目": u"missing"})
            elif exp is None or c.get("value") is None or abs(c["value"] - exp) > 1e-6 * max(1.0, abs(exp)):
                row.update({u"結果": PP.K_ELSE, u"結果の細目": u"id_shift"})
            else:
                kind, st, reason, ptr = PP.classify_after(s, c)
                row.update({u"結果": kind, u"結果の細目": st, u"後の reason": reason, u"後の pointers": ptr,
                            u"_cue": {u"_prior_cue": bool(R._prior_cue(new_sents[s[u"_si"]], s[u"_a"], s[u"_a"] + len(s[u"後の字"]))),
                                      u"_prior_cue_clause": bool(R._prior_cue_clause(new_sents[s[u"_si"]], s[u"_a"]))},
                            u"_文": new_sents[s[u"_si"]][max(0, s[u"_a"] - 40):s[u"_a"] + len(s[u"後の字"]) + 40]})
            rows.append(row)
    return rows


def e1_doc(doc_id, zb, text0):
    sites, _diag, _b, _o, sentences, _base = PP.find_sites(zb, text0)
    for s in sites:
        s[u"書類"] = doc_id
    rows_old = inject_with_profile(doc_id, zb, text0, sites, sentences, OLD)
    rows_new = inject_with_profile(doc_id, zb, text0, sites, sentences, NEW)
    made = [s for s in sites if s[u"作れた"]]
    if len(rows_old) != len(made) or len(rows_new) != len(made):
        raise SystemExit(u"**注入の行の数が作れた site の数と違う(%s): %d / %d / %d。止める**" % (doc_id, len(rows_old), len(rows_new), len(made)))
    by_old = dict((r[u"id"], r) for r in rows_old)
    out = []
    for r in rows_new:
        o = by_old[r[u"id"]]
        out.append({u"書類": doc_id, u"id": r[u"id"], u"要素": r[u"要素"], u"単位": r[u"単位"], u"元の字": r[u"元の字"], u"後の字": r[u"後の字"],
                    u"当期の fact": r[u"当期の fact"], u"前期の fact": r[u"前期の fact"], u"文脈 60 字": r[u"文脈 60 字"],
                    u"P21(対照)": {u"結果": o[u"結果"], u"state": o[u"結果の細目"], u"reason": o.get(u"後の reason"), u"pointers": o.get(u"後の pointers")},
                    u"P22": {u"結果": r[u"結果"], u"state": r[u"結果の細目"], u"reason": r.get(u"後の reason"), u"pointers": r.get(u"後の pointers"),
                           u"手がかり(注入後の文)": r.get(u"_cue"), u"注入後の文脈": r.get(u"_文")}})
    return out, len(sites), len(made)


def e1_summary(rows):
    u"""E-1 の集計。**行から数える純関数**(門が記録の行に同じ関数ではなく独立に当て直す)。"""
    n = len(rows)
    new = collections.Counter(r[u"P22"][u"結果"] for r in rows)
    old = collections.Counter(r[u"P21(対照)"][u"結果"] for r in rows)
    passed_kinds = (PP.K_MOVED, PP.K_SAME, PP.K_OTHER, PP.K_ODD)
    p_new = sum(new[k] for k in passed_kinds)
    p_old = sum(old[k] for k in passed_kinds)
    other_states = collections.Counter((r[u"P22"][u"state"], r[u"P22"][u"reason"]) for r in rows if r[u"P22"][u"結果"] == PP.K_ELSE)
    by_unit = {}
    for r in rows:
        by_unit.setdefault(r[u"単位"], collections.Counter())[r[u"P22"][u"結果"]] += 1
    by_unit_old = {}
    for r in rows:
        by_unit_old.setdefault(r[u"単位"], collections.Counter())[r[u"P21(対照)"][u"結果"]] += 1
    trans = collections.Counter(u"%s → %s" % (r[u"P21(対照)"][u"結果"], r[u"P22"][u"結果"]) for r in rows)
    still = [r for r in rows if r[u"P22"][u"結果"] in passed_kinds]
    cue_true = sum(1 for r in still if (r[u"P22"][u"手がかり(注入後の文)"] or {}).get(u"_prior_cue_clause") or (r[u"P22"][u"手がかり(注入後の文)"] or {}).get(u"_prior_cue"))
    return {u"注入": n,
            u"P22 の結果": dict(sorted(new.items())), u"P21(対照)の結果": dict(sorted(old.items())),
            u"P22 で通した(GROUNDED のまま)": frac(p_new, n), u"P21(対照)で通した": frac(p_old, n),
            u"P22 で通した のうち参照先が Prior1Year": frac(new[PP.K_MOVED], n),
            u"P22 で止めた(VALUE_MISMATCH)": frac(new[PP.K_STOP], n),
            u"P22 でその他(通した でも 止めた でもない)": frac(new[PP.K_ELSE], n),
            u"P22 のその他の内訳(state, reason)": dict(sorted((u"%s | %s" % k, v) for k, v in other_states.items())),
            u"単位別 P22": dict((k, dict(sorted(v.items()))) for k, v in sorted(by_unit.items())),
            u"単位別 P21(対照)": dict((k, dict(sorted(v.items()))) for k, v in sorted(by_unit_old.items())),
            u"P21 → P22 の遷移": dict(sorted(trans.items())),
            u"P22 で通した行のうち 手がかり(_prior_cue か _prior_cue_clause)が注入後の文で真": cue_true,
            u"P22 で通した行": len(still)}


def e1_vs_record(rows):
    u"""対照の再現: 穴 B の記録の 485 行と、(書類, id) ごとに 結果・後の pointers が一致するか。"""
    rec = jload(POINT_PRIOR_REL)["B"]["行"]
    want = dict(((r[u"書類"], r[u"id"]), r) for r in rec)
    diff = []
    for r in rows:
        w = want.get((r[u"書類"], r[u"id"]))
        o = r[u"P21(対照)"]
        if w is None or w[u"結果"] != o[u"結果"] or w.get(u"後の pointers") != o[u"pointers"] or w.get(u"結果の細目") != o[u"state"]:
            diff.append({u"書類": r[u"書類"], u"id": r[u"id"]})
    return {u"記録の行": len(want), u"今回の行": len(rows), u"記録に無い行": sum(1 for r in rows if (r[u"書類"], r[u"id"]) not in want),
            u"違った行": len(diff), u"違った行の id": diff[:20]}


# ====================================================================================================
# E-2 / E-3
def compare_docs(doc_ids, texts_of=None, label=u""):
    u"""各書類を P21 と P22 で verify_document(自身の本文 = 製品の経路)し、claim ごとに比べる。"""
    per_doc, moved = [], []
    base_groups = collections.Counter()
    moved_groups = collections.Counter()
    tot = collections.Counter()
    missing = []
    for d in doc_ids:
        p = ED.cache_path(d)
        if not os.path.exists(p):
            missing.append(d)
            continue
        with io.open(p, "rb") as fh:
            zb = fh.read()
        a = VD.verify_document(zb, OLD)
        b = VD.verify_document(zb, NEW)
        if [c["id"] for c in a["claims"]] != [c["id"] for c in b["claims"]]:
            raise SystemExit(u"**claim の id の並びが P21 と P22 で違う: %s。止める**" % d)
        if [c["span"] for c in a["claims"]] != [c["span"] for c in b["claims"]]:
            raise SystemExit(u"**claim の span が P21 と P22 で違う: %s。止める**" % d)
        n_moved = 0
        text = None
        try:
            text = PP.classify_doc(zb)[2]
        except Exception:  # noqa: BLE001
            text = None
        for x, y in zip(a["claims"], b["claims"]):
            tot[u"claims"] += 1
            grp = None
            if x["state"] == "GROUNDED":
                tot[u"P21 の GROUNDED"] += 1
                if len(x["pointers"]) == 1:
                    if x["pointers"][0].split("@")[-1].startswith("Prior1Year"):
                        grp = u"Prior1Year・手がかりあり" if CUE.search(x["span"] or u"") else u"Prior1Year・手がかり無し"
                    else:
                        grp = u"当期"
                    base_groups[grp] += 1
                else:
                    base_groups[u"pointer が 1 本でない"] += 1
            if claim_key(x) == claim_key(y):
                continue
            n_moved += 1
            tot[u"動いた(全 state)"] += 1
            kind = u"%s → %s" % (x["state"], y["state"])
            tot[kind] += 1
            if x["state"] == "GROUNDED":
                moved_groups[grp or u"pointer が 1 本でない"] += 1
            ctx = None
            if text and x["span"]:
                i = text.find(x["span"])
                if i >= 0:
                    ctx = text[max(0, i - 20):i + len(x["span"]) + 40]
            moved.append({u"doc": d, u"id": x["id"], u"subject": x["subject"], u"unit": x["unit"], u"value": x["value"], u"span": x["span"],
                          u"文脈": ctx, u"P21": view(x), u"P22": view(y), u"向き": kind, u"P21 の群": grp,
                          u"印: 文に 減少・減": bool(DEC_RX.search(ctx or x["span"] or u"")),
                          u"印: 文に 増加・増": bool(INC_RX.search(ctx or x["span"] or u""))})
        per_doc.append({u"doc": d, u"claims": len(a["claims"]), u"動いた": n_moved,
                        u"GROUNDED(P21)": a["document"]["states"].get("GROUNDED", 0), u"GROUNDED(P22)": b["document"]["states"].get("GROUNDED", 0)})
    return {u"書類": per_doc, u"動いた行": moved, u"キャッシュに無い書類": missing, u"集計": dict(sorted(tot.items())),
            u"P21 の GROUNDED の群": dict(sorted(base_groups.items())), u"動いた GROUNDED の群": dict(sorted(moved_groups.items()))}


def cmp_summary(rec):
    u"""E-2 / E-3 の集計。**動いた行から数える純関数**。"""
    mv = rec[u"動いた行"]
    g2n = [r for r in mv if r[u"P21"][u"state"] == "GROUNDED" and r[u"P22"][u"state"] != "GROUNDED"]
    n2g = [r for r in mv if r[u"P21"][u"state"] != "GROUNDED" and r[u"P22"][u"state"] == "GROUNDED"]
    g2g = [r for r in mv if r[u"P21"][u"state"] == "GROUNDED" and r[u"P22"][u"state"] == "GROUNDED"]
    return {u"動いた(全 state)": len(mv),
            u"GROUNDED → GROUNDED でない": len(g2n), u"GROUNDED でない → GROUNDED(新 GROUNDED)": len(n2g), u"GROUNDED → GROUNDED(参照先だけ動いた)": len(g2g),
            u"GROUNDED → の向き": dict(sorted(collections.Counter(r[u"向き"] for r in g2n).items())),
            u"GROUNDED → 非 GROUNDED の群": dict(sorted(collections.Counter(r[u"P21 の群"] for r in g2n).items())),
            u"向き(全部)": dict(sorted(collections.Counter(r[u"向き"] for r in mv).items())),
            u"GROUNDED → 非 GROUNDED のうち 印: 文に 減少・減": sum(1 for r in g2n if r[u"印: 文に 減少・減"]),
            u"GROUNDED → 非 GROUNDED のうち 印: 文に 増加・増(減少・減 でない)": sum(1 for r in g2n if r[u"印: 文に 増加・増"] and not r[u"印: 文に 減少・減"]),
            u"GROUNDED → 非 GROUNDED のうち 印なし": sum(1 for r in g2n if not r[u"印: 文に 減少・減"] and not r[u"印: 文に 増加・増"]),
            u"GROUNDED → 非 GROUNDED の書類数": len({r[u"doc"] for r in g2n})}


# ====================================================================================================
# E-4
def core_say_for(zb, tampered, profile, rows):
    u"""cd8 の材料 script(``xbrl_cd_material_2026-10-17.py``)と同じ claim の対の付け方・同じ ``core_pointer_say``。"""
    claims = VD.verify_document(zb, profile, tampered)["claims"]
    out = {}
    for r in rows:
        claim = None
        for c in claims:
            if c.get("value") is None:
                continue
            if abs(c["value"] - r["値"]) <= A1.TOL and r["数の字面"] in (c.get("span") or ""):
                claim = c
                break
        out[r["id"]] = A1.core_pointer_say(claim)
    return out


def e4(work):
    mat = jload(S2_MATERIAL_REL)
    rec = jload(S2_REC_REL)
    rec_rows = dict(((r["doc"], r["id"]), r) for r in rec[u"行"])
    seed, _meta = IJ.verify_seed_sealed(MB.SEED_FILE)
    registry = HT.RS.register_all(HT.core.Registry.default())
    ans_dir = HS2.ANS_DIR
    rows_out = []
    with HS2.patched():
        for p in mat[u"書類ごと"]:
            doc = p["docID"]
            rb = HS2.rebuild(doc, work, seed)
            if hashlib.sha256(rb["task"].encode("utf-8")).hexdigest() != p[u"材料"][u"sha256"]:
                raise SystemExit(u"**再構成した task の sha256 が材料の記録と合わない: %s**" % doc)
            with io.open(ED.cache_path(doc), "rb") as fh:
                zb = fh.read()
            chosen = dict((c["id"], c) for c in rb["chosen"])
            core_old = core_say_for(zb, rb["tampered"], OLD, rb["rows"])
            core_new = core_say_for(zb, rb["tampered"], NEW, rb["rows"])
            by_id = HT.AL.answers_by_id(ans_dir, doc)
            dc = HT.AL.DocCtx(doc)
            for m in sorted(rb["rows"], key=lambda r: r["id"]):
                rid = m["id"]
                inj_id = m.get("**注入**")
                typ = chosen[inj_id]["type"] if inj_id else None
                want = rec_rows[(doc, rid)]
                seat = HT.AL.SC.seat_row(by_id.get(rid))
                al = None
                if seat[u"参照先"] is not None:
                    raw = str(by_id[rid][u"参照先"]).strip()
                    al = HT.AL.engine_item(dc, registry, m, raw, u"席 A の参照先", "S2", with_reading=True)
                rows_out.append({
                    u"doc": doc, u"id": rid, u"注入か": bool(inj_id), u"注入の型": typ,
                    u"Core 自身 P21(今回)": {u"state": HT.core_state(core_old[rid]), u"参照先": core_old[rid]["参照先"]},
                    u"Core 自身 P22": {u"state": HT.core_state(core_new[rid]), u"参照先": core_new[rid]["参照先"]},
                    u"Core 自身(段 2 の記録)": {u"state": want[u"Core 自身(既定)の state"], u"参照先": want[u"Core 自身(既定)の参照先"]},
                    u"α 型を当てた": al is not None,
                    u"α 型(今回)": (None if al is None else {u"state": al[u"engine の state"], u"reason": al[u"engine の reason"],
                                                           u"held": al[u"held(製品の経路)"], u"参照先の fact の値": al[u"参照先の fact の値"]}),
                    u"α 型(段 2 の記録)": (None if want[u"α 型の state"] == u"参照先なし" else
                                      {u"state": want[u"α 型の state"], u"reason": want[u"α 型の reason"], u"held": want[u"α 型の held"],
                                       u"参照先の fact の値": want[u"α 型の参照先の fact の値"]})})
    return rows_out


def e4_summary(rows):
    u"""E-4 の集計(行から数える純関数)。"""
    t6 = [r for r in rows if r[u"注入の型"] == "T6_PRIOR"]
    ctrl_diff = [r for r in rows if r[u"Core 自身 P21(今回)"] != r[u"Core 自身(段 2 の記録)"]]
    moved = [r for r in rows if r[u"Core 自身 P21(今回)"] != r[u"Core 自身 P22"]]
    al = [r for r in rows if r[u"α 型を当てた"]]
    al_diff = [r for r in al if r[u"α 型(今回)"] != r[u"α 型(段 2 の記録)"]]
    return {u"行": len(rows), u"注入": sum(1 for r in rows if r[u"注入か"]),
            u"T6_PRIOR の注入": len(t6),
            u"T6 で Core 自身 P22 が GROUNDED": frac(sum(1 for r in t6 if r[u"Core 自身 P22"][u"state"] == "GROUNDED"), len(t6)),
            u"T6 で Core 自身 P21(今回の再計算)が GROUNDED": frac(sum(1 for r in t6 if r[u"Core 自身 P21(今回)"][u"state"] == "GROUNDED"), len(t6)),
            u"T6 で Core 自身 段 2 の記録が GROUNDED": frac(sum(1 for r in t6 if r[u"Core 自身(段 2 の記録)"][u"state"] == "GROUNDED"), len(t6)),
            u"T6 の Core 自身 P22 の state": dict(sorted(collections.Counter(str(r[u"Core 自身 P22"][u"state"]) for r in t6).items())),
            u"対照: P21 の再計算が 段 2 の記録と違った行": len(ctrl_diff),
            u"Core 自身が P21 → P22 で動いた行(型を問わず)": len(moved),
            u"Core 自身が動いた行の型": dict(sorted(collections.Counter(str(r[u"注入の型"]) for r in moved).items())),
            u"Core 自身が動いた行 P21 → P22 の state": dict(sorted(collections.Counter(u"%s → %s" % (str(r[u"Core 自身 P21(今回)"][u"state"]), str(r[u"Core 自身 P22"][u"state"])) for r in moved).items())),
            u"全注入(64)で Core 自身 P22 が GROUNDED": frac(sum(1 for r in rows if r[u"注入か"] and r[u"Core 自身 P22"][u"state"] == "GROUNDED"), sum(1 for r in rows if r[u"注入か"])),
            u"全注入(64)で Core 自身 段 2 の記録が GROUNDED": frac(sum(1 for r in rows if r[u"注入か"] and r[u"Core 自身(段 2 の記録)"][u"state"] == "GROUNDED"), sum(1 for r in rows if r[u"注入か"])),
            u"α 型を当てた行": len(al), u"α 型が記録と違った行": len(al_diff)}


def e4_structure():
    u"""α 型の経路(``verify_external``)が profile を引数に取らず、``_direct_value_claim`` を呼ばない、という構造の事実。"""
    VE = HT.AL.VE
    sig = list(inspect.signature(VE.verify_external).parameters)
    src = inspect.getsource(VE)
    return {u"verify_external の引数": sig, u"引数に profile が在る": any("profile" in x for x in sig),
            u"verify_external の module の字に _direct_value_claim が在る": "_direct_value_claim" in src,
            u"verify_external の module の字に recipes の import が在る": bool(re.search(r"(?m)^\s*(from|import)\s+.*recipes", src))}


# ====================================================================================================
# E-5
def e5(label_shas):
    zp = os.path.join(ROOT, RIT.ZIP_REL)
    with io.open(zp, "rb") as fh:
        zb = fh.read()
    if hashlib.sha256(zb).hexdigest() != RIT.ZIP_SHA256:
        raise SystemExit(u"**儀式の入力の sha256 が封の字と違う。止める**")
    old = RIT.build(zb, OLD, label_shas)
    new = RIT.build(zb, NEW, label_shas)
    rec = jload(RITUAL_REL)
    key = lambda x: (x[u"id"], x[u"型"])
    by_rec = dict((key(x), x[u"結果"]) for x in rec[u"注入の一覧"])
    by_old = dict((key(x), x[u"結果"]) for x in old[u"注入の一覧"])
    by_new = dict((key(x), x[u"結果"]) for x in new[u"注入の一覧"])
    moved = [{u"id": k[0], u"型": k[1], u"P21": by_old[k], u"P22": by_new[k]} for k in sorted(by_new) if by_new[k] != by_old.get(k)]
    new_rows = dict((key(x), x) for x in new[u"注入の一覧"])
    dropped = [{u"id": k[0], u"型": k[1], u"P21 の結果": by_old[k]} for k in sorted(by_old) if k not in by_new]
    appeared = [{u"id": k[0], u"型": k[1], u"P22 の結果": by_new[k]} for k in sorted(by_new) if k not in by_old]
    plain_old = VD.verify_document(zb, OLD, None)["claims"]
    plain_new = VD.verify_document(zb, NEW, None)["claims"]
    plain_moved = [{u"id": x["id"], u"span": x["span"], u"P21": view(x), u"P22": view(y)}
                   for x, y in zip(plain_old, plain_new) if claim_key(x) != claim_key(y)]
    return {u"通した P22": new[u"通した"], u"止めた P22": new[u"止めた"],
            u"通した P21(対照)": old[u"通した"], u"止めた P21(対照)": old[u"止めた"],
            u"通した 記録": rec[u"通した"], u"止めた 記録": rec[u"止めた"],
            u"対照: P21 の再計算が儀式の記録と違った行": sum(1 for k in by_rec if by_rec[k] != by_old.get(k)),
            u"記録の行数": len(by_rec), u"今回の行数": len(by_new),
            u"P21 → P22 で結果が動いた行": moved,
            u"P22 の注入の対象から外れた行(P21 の対象に在った)": dropped, u"P22 の注入の対象に増えた行": appeared,
            u"他の行(両方に在る)で結果が同じ": sum(1 for k in by_new if k in by_old and by_new[k] == by_old[k]),
            u"素の書類で P21 → P22 で動いた claim": plain_moved,
            u"P22 の通した 一覧(id と型)": sorted(u"%s %s" % (x[u"id"], x[u"型"]) for x in new[u"通した の一覧"]),
            u"P22 の通した のうち N125・N199": sorted(x[u"id"] for x in new[u"通した の一覧"] if x[u"id"] in ("N125", u"N199")),
            u"N125・N199 の P22 の結果": dict((i, [new_rows[k][u"結果"] for k in sorted(new_rows) if k[0] == i]) for i in ("N125", "N199")),
            u"素の書類 P22": new[u"素の書類"], u"素の書類 P21": old[u"素の書類"],
            u"注入の対象": new[u"注入"][u"注入の対象(GROUNDED の site)"],
            u"所要秒": {u"P21": old[u"所要秒"][u"全体"], u"P22": new[u"所要秒"][u"全体"]}}


# ====================================================================================================
# E-7
def numstat():
    out = {}
    for f in ("adapters/xbrl/recipes.py", "adapters/xbrl/vocabulary.py"):
        rc, o = git("diff", "--numstat", "HEAD", "--", f)
        p = o.split()
        out[f] = {u"挿入": int(p[0]), u"削除": int(p[1])} if len(p) >= 2 and p[0].isdigit() else {u"挿入": 0, u"削除": 0}
    rc, o = git("diff", "--numstat", "HEAD", "--", "core")
    rc2, st = git("status", "--porcelain", "--", "core")
    out[u"core/"] = {u"差の行数": sum(int(l.split("\t")[0]) + int(l.split("\t")[1]) for l in o.splitlines() if l.split("\t")[0].isdigit()),
                     u"status": st.strip()}
    return out


def run_pytest(target):
    t = time.time()
    p = subprocess.run([sys.executable, "-m", "pytest", "-q", target], cwd=ROOT, capture_output=True, text=True)
    tail = [l for l in p.stdout.strip().splitlines() if l.strip()][-1] if p.stdout.strip() else u""
    return {u"コマンド": u"python3 -m pytest -q %s" % target, u"rc": p.returncode, u"最後の行": tail, u"所要秒": round(time.time() - t, 1)}


# ====================================================================================================
def env_block(label_shas):
    bundle, n_files = RIT.engine_bundle_sha256()
    return {u"封": SEAL, u"HEAD": RIT.git_head(), u"python": platform.python_version(),
            u"engine の束ねた sha256(core/ と adapters/ の file。__pycache__ を除く。repo 相対の path 順。変更後)": bundle,
            u"engine の file 数": n_files,
            u"recipes.py の sha16": sha_file(os.path.join(ROOT, "adapters/xbrl/recipes.py"))[:16],
            u"vocabulary.py の sha16": sha_file(os.path.join(ROOT, "adapters/xbrl/vocabulary.py"))[:16],
            u"DEFAULT_PROFILE": V.DEFAULT_PROFILE, u"比べた profile": [OLD, NEW],
            u"鍵の名前の有無(値は読まない)": dict((k, (k in os.environ)) for k in KEY_NAMES),
            u"名前が ANTHROPIC/OPENAI/GOOGLE/GEMINI で始まる環境変数の数(値は読まない)": sum(1 for k in os.environ if k.split("_")[0] in ("ANTHROPIC", "OPENAI", "GOOGLE", "GEMINI")),
            u"ラベル 2 file の sha256(起動時に照合)": label_shas,
            u"cache": u"~/.cache/audit-core/edinet/*.zip(手元の file だけ。取りに行かない)",
            u"通信": u"この script は urllib・socket・http を import しない。adapters は urllib を import するが接続は起きない",
            u"費用": u"0 USD"}


def judge(rec):
    u"""封 §2 の E-1〜E-8 の機械的な判定(E-6 の「過半は別の型」と E-7 の「全部緑」の人の読みの部分は文書で)。"""
    J = {}
    if u"E1" in rec:
        s = rec[u"E1"][u"集計"]
        p, st = s[u"P22 で通した(GROUNDED のまま)"], s[u"P22 で止めた(VALUE_MISMATCH)"]
        ok = 0 <= p[u"件"] <= 10 and 420 <= st[u"件"] <= 485
        J[u"E-1"] = {u"実測": u"通した %d / %d・止めた(VALUE_MISMATCH)%d・その他 %d" % (p[u"件"], p[u"分母"], st[u"件"], s[u"P22 でその他(通した でも 止めた でもない)"][u"件"]),
                   u"判定": u"当たり" if ok else u"外れ"}
    if u"E2" in rec:
        c = rec[u"E2"][u"集計"]
        g = rec[u"E2"][u"P21 の GROUNDED の群"]
        mg = rec[u"E2"][u"動いた GROUNDED の群"]
        n_leave = c[u"GROUNDED → GROUNDED でない"]
        n_stay = c[u"GROUNDED → GROUNDED(参照先だけ動いた)"]
        cue_moved, cur_moved = mg.get(u"Prior1Year・手がかりあり", 0), mg.get(u"当期", 0)
        parts = {u"幅 22〜30(GROUNDED を離れた行)": 22 <= n_leave <= 30,
                 u"動いた GROUNDED の行の総数(離れた + 参照先だけ動いた)も 22〜30": 22 <= n_leave + n_stay <= 30,
                 u"新 GROUNDED 0": c[u"GROUNDED でない → GROUNDED(新 GROUNDED)"] == 0,
                 u"向きが全部 GROUNDED → 非 GROUNDED(参照先だけ動いた行 0)": n_stay == 0,
                 u"手がかりあり %d 行が不動" % g.get(u"Prior1Year・手がかりあり", 0): cue_moved == 0,
                 u"当期 %d 行が不動" % g.get(u"当期", 0): cur_moved == 0}
        J[u"E-2"] = {u"実測": u"P21 で GROUNDED の行のうち動いた %d(GROUNDED を離れた %d・GROUNDED のまま参照先だけ動いた %d)、新 GROUNDED %d。群別(動いた GROUNDED): 手がかり無し %d / %d・手がかりあり %d / %d・当期 %d / %d" % (
            n_leave + n_stay, n_leave, n_stay, c[u"GROUNDED でない → GROUNDED(新 GROUNDED)"],
            mg.get(u"Prior1Year・手がかり無し", 0), g.get(u"Prior1Year・手がかり無し", 0), cue_moved, g.get(u"Prior1Year・手がかりあり", 0), cur_moved, g.get(u"当期", 0)),
            u"部分の判定": parts,
            u"判定": u"当たり" if (parts[u"幅 22〜30(GROUNDED を離れた行)"] and parts[u"新 GROUNDED 0"] and cue_moved == 0 and cur_moved == 0) else u"外れ"}
    if u"E3" in rec:
        c = rec[u"E3"][u"集計"]
        mv = rec[u"E3"][u"動いた GROUNDED の群"]
        n_g = sum(mv.values())
        parts = {u"動いた GROUNDED の行 ≤ 40": n_g <= 40, u"新 GROUNDED 0(向きが逆でない)": c[u"GROUNDED でない → GROUNDED(新 GROUNDED)"] == 0,
                 u"全部 GROUNDED → 非 GROUNDED(参照先だけ動いた行 0)": c[u"GROUNDED → GROUNDED(参照先だけ動いた)"] == 0}
        J[u"E-3"] = {u"実測": u"動いた行(全 state)%d・うち P21 で GROUNDED だった行 %d(GROUNDED を離れた %d・参照先だけ動いた %d)・新 GROUNDED %d。キャッシュに無い書類 %d" % (
            c[u"動いた(全 state)"], n_g, c[u"GROUNDED → GROUNDED でない"], c[u"GROUNDED → GROUNDED(参照先だけ動いた)"],
            c[u"GROUNDED でない → GROUNDED(新 GROUNDED)"], len(rec[u"E3"][u"キャッシュに無い書類"])),
            u"部分の判定": parts, u"判定": u"当たり" if (parts[u"動いた GROUNDED の行 ≤ 40"] and parts[u"新 GROUNDED 0(向きが逆でない)"]) else u"外れ"}
    if u"E4" in rec:
        s = rec[u"E4"][u"集計"]
        t6 = s[u"T6 で Core 自身 P22 が GROUNDED"]
        ok = 0 <= t6[u"件"] <= 1 and s[u"α 型が記録と違った行"] == 0
        J[u"E-4"] = {u"実測": u"T6 の Core 自身 P22 が GROUNDED %d / %d(段 2 の記録 %d)。α 型を当てた %d 行のうち記録と違った %d" % (
            t6[u"件"], t6[u"分母"], s[u"T6 で Core 自身 段 2 の記録が GROUNDED"][u"件"], s[u"α 型を当てた行"], s[u"α 型が記録と違った行"]),
            u"判定": u"当たり" if ok else u"外れ"}
    if u"E5" in rec:
        e = rec[u"E5"]
        parts = {u"通した 15": e[u"通した P22"][u"件"] == 15, u"止めた 226": e[u"止めた P22"][u"件"] == 226,
                 u"N125・N199 が VALUE_MISMATCH に(動いた行はこの 2 つだけ)": sorted(x[u"id"] for x in e[u"P21 → P22 で結果が動いた行"]) == ["N125", "N199"]
                 and all(x[u"P22"] == "detected:VALUE_MISMATCH" for x in e[u"P21 → P22 で結果が動いた行"]),
                 u"他の 239 件は同じ結果(対象 241 のまま)": e[u"注入の対象"] == 241 and e[u"他の行(両方に在る)で結果が同じ"] == 239}
        J[u"E-5"] = {u"実測": u"通した %d / %d・止めた %d / %d・動いた行 %d(%s)・対象から外れた行 %d・他で結果が同じ %d" % (
            e[u"通した P22"][u"件"], e[u"通した P22"][u"分母"], e[u"止めた P22"][u"件"], e[u"止めた P22"][u"分母"],
            len(e[u"P21 → P22 で結果が動いた行"]), u"・".join(x[u"id"] for x in e[u"P21 → P22 で結果が動いた行"]),
            len(e[u"P22 の注入の対象から外れた行(P21 の対象に在った)"]), e[u"他の行(両方に在る)で結果が同じ"]),
            u"部分の判定": parts, u"判定": u"当たり" if all(parts.values()) else u"外れ"}
    if u"E2" in rec and u"E3" in rec:
        a = rec[u"E2"][u"集計"]
        n_leave = a[u"GROUNDED → GROUNDED でない"]
        n_g = n_leave + a[u"GROUNDED → GROUNDED(参照先だけ動いた)"]
        J[u"E-6"] = {u"実測": u"GROUNDED を離れた行 %d のうち、機械の印(文に 減少・減)%d・(増加・増 だけ)%d・印なし %d。動いた行の分母は 3 通り(GROUNDED を離れた行 %d・動いた GROUNDED の行 %d・動いた全 state の行 %d)で、過半かどうかは分母の選び方に依る。型の読みは人の読み(結果文書)" % (
            n_leave, a[u"GROUNDED → 非 GROUNDED のうち 印: 文に 減少・減"],
            a[u"GROUNDED → 非 GROUNDED のうち 印: 文に 増加・増(減少・減 でない)"], a[u"GROUNDED → 非 GROUNDED のうち 印なし"],
            n_leave, n_g, a[u"動いた(全 state)"]),
            u"判定": u"判定は文書で(人の読み)"}
    if u"E7" in rec:
        e = rec[u"E7"]
        r = e[u"engine の差分"]
        n_r = r["adapters/xbrl/recipes.py"][u"挿入"] + r["adapters/xbrl/recipes.py"][u"削除"]
        n_v = r["adapters/xbrl/vocabulary.py"][u"挿入"] + r["adapters/xbrl/vocabulary.py"][u"削除"]
        tests_ok = all(t[u"rc"] == 0 for t in e.get(u"既存試験", [])) and not e.get(u"封の 3 か所のほかに直した既存試験")
        J[u"E-7"] = {u"実測": u"recipes.py 挿入 %d・削除 %d、vocabulary.py 挿入 %d・削除 %d、core/ %d 行。既存試験 %s" % (
            r["adapters/xbrl/recipes.py"][u"挿入"], r["adapters/xbrl/recipes.py"][u"削除"],
            r["adapters/xbrl/vocabulary.py"][u"挿入"], r["adapters/xbrl/vocabulary.py"][u"削除"], r[u"core/"][u"差の行数"],
            u"・".join(u"%s → %s" % (t[u"コマンド"], t[u"最後の行"]) for t in e.get(u"既存試験", [])) or u"(この実行では走らせていない)"),
            u"判定": u"当たり" if (n_r <= 15 and n_v <= 6 and r[u"core/"][u"差の行数"] == 0 and e.get(u"既存試験") and tests_ok) else u"外れ"}
    J[u"E-8"] = {u"実測": u"段 2(既定 P21 → P22)は人間の承認の後。この実行では何も変えていない(DEFAULT_PROFILE = %s)" % V.DEFAULT_PROFILE,
               u"判定": u"判定しない(段 2)"}
    return J


def inputs_block(doc_ids_67, doc_ids_40):
    d = {}
    for rel in (POINT_PRIOR_REL, RITUAL_REL, NAMING_REL, S2_MATERIAL_REL, S2_REC_REL):
        d[RITUAL_KEY_AT_MEASURE if rel == RITUAL_REL else rel] = sha_file(os.path.join(ROOT, rel))
    d[u"seat answers(hybrid_s2_answers)"] = dict((fn, sha_file(os.path.join(HS2.ANS_DIR, fn))) for fn in sorted(os.listdir(HS2.ANS_DIR)) if fn.endswith("_answer.json"))
    d[u"儀式の同梱書類"] = sha_file(os.path.join(ROOT, RIT.ZIP_REL))
    d[u"書類 67(経営分析の文を持つ)の sha256"] = dict((x, sha_file(ED.cache_path(x))) for x in doc_ids_67 if os.path.exists(ED.cache_path(x)))
    d[u"書類 40(名指しの直しの無改変)の sha256"] = dict((x, sha_file(ED.cache_path(x))) for x in doc_ids_40 if os.path.exists(ED.cache_path(x)))
    return d


# ====================================================================================================
# 段 2(既定 P21 -> P22): profile を省いた製品の経路が P22 の数を出すことの証拠
def p22_view(r):
    u"""``e1_doc`` が記録の ``P22`` 欄に書く dict と同じ作り(profile だけが違う実行の行から)。"""
    return {u"結果": r[u"結果"], u"state": r[u"結果の細目"], u"reason": r.get(u"後の reason"), u"pointers": r.get(u"後の pointers"),
            u"手がかり(注入後の文)": r.get(u"_cue"), u"注入後の文脈": r.get(u"_文")}


def stage2_e1(texts, rec):
    u"""E-1: 穴 B の注入 485 件を **profile 省略**(= 既定)で再検証し、段 1 の記録の P22 の欄と 1 行ずつ比べる。"""
    want = dict(((r[u"書類"], r[u"id"]), r) for r in rec[u"E1"][u"行"] if r[u"書類"] in texts)      # texts が全 67 書類なら全 485 行
    got_rows, diff = {}, []
    for d in sorted(texts):
        zb, text = texts[d]
        sites, _diag, _b, _o, sentences, _base = PP.find_sites(zb, text)
        for st in sites:
            st[u"書類"] = d
        for r in inject_with_profile(d, zb, text, sites, sentences, None):
            got_rows[(d, r[u"id"])] = r
    for k in sorted(want):
        g = got_rows.get(k)
        if g is None or p22_view(g) != want[k][u"P22"]:
            diff.append({u"書類": k[0], u"id": k[1]})
    extra = sorted(k for k in got_rows if k not in want)
    passed_kinds = (PP.K_MOVED, PP.K_SAME, PP.K_OTHER, PP.K_ODD)
    kinds = collections.Counter(g[u"結果"] for g in got_rows.values())
    p, st_, el = sum(kinds[k] for k in passed_kinds), kinds[PP.K_STOP], kinds[PP.K_ELSE]
    n = len(got_rows)
    return {u"profile": u"省略(None = vocabulary.DEFAULT_PROFILE)",
            u"記録(段 1)の行": len(want), u"今回の行": n, u"記録に無い行": len(extra),
            u"段 1 の P22 の欄と違った行": len(diff), u"違った行の id": diff[:20],
            u"通した(GROUNDED のまま)": frac(p, n), u"止めた(VALUE_MISMATCH)": frac(st_, n), u"その他": frac(el, n),
            u"通した のうち参照先が Prior1Year": frac(kinds[PP.K_MOVED], n)}


def stage2_e2(texts, rec):
    u"""E-2: 67 書類の無改変を P21 と **profile 省略** で verify_document し、動いた行が段 1 の記録の動いた行と過不足なく同じか。"""
    want = dict(((r[u"doc"], r[u"id"]), r) for r in rec[u"E2"][u"動いた行"] if r[u"doc"] in texts)      # texts が全 67 書類なら全部
    n_claims = 0
    moved, diff = {}, []
    for d in sorted(texts):
        zb, _text = texts[d]
        a = VD.verify_document(zb, OLD)
        b = VD.verify_document(zb, None)
        if [c["id"] for c in a["claims"]] != [c["id"] for c in b["claims"]]:
            raise SystemExit(u"**claim の id の並びが P21 と既定で違う: %s。止める**" % d)
        for x, y in zip(a["claims"], b["claims"]):
            n_claims += 1
            if claim_key(x) != claim_key(y):
                moved[(d, x["id"])] = (x, y)
    for k, w in sorted(want.items()):
        m = moved.get(k)
        if m is None or view(m[0]) != w[u"P21"] or view(m[1]) != w[u"P22"]:
            diff.append({u"doc": k[0], u"id": k[1]})
    extra = sorted(k for k in moved if k not in want)
    leave = sum(1 for (x, y) in moved.values() if x["state"] == "GROUNDED" and y["state"] != "GROUNDED")
    new_g = sum(1 for (x, y) in moved.values() if x["state"] != "GROUNDED" and y["state"] == "GROUNDED")
    return {u"profile": u"省略(None = vocabulary.DEFAULT_PROFILE)", u"書類": len(texts), u"claims": n_claims,
            u"既定と P21 で動いた行": len(moved), u"記録(段 1)の動いた行": len(want),
            u"記録に無い動いた行": len(extra), u"記録の動いた行のうち違った行(P21・P22 の欄)": len(diff), u"違った行": diff[:20],
            u"GROUNDED を離れた": leave, u"新 GROUNDED": new_g}


def stage2_e5(label_shas):
    u"""E-5: 儀式を既定(``RIT.build(zb, V.DEFAULT_PROFILE, …)`` = 儀式 script の main と同じ呼び方)で回し、
    P21 の記録 + 段 1 の E-5 の動いた行・外れた行から作った 240 行の期待と、採り直した儀式の記録の 240 行に 1 行ずつ比べる。
    あわせて素の書類を profile 省略で検証し、P22 明示と全 claim 一致を見る。"""
    zp = os.path.join(ROOT, RIT.ZIP_REL)
    with io.open(zp, "rb") as fh:
        zb = fh.read()
    if hashlib.sha256(zb).hexdigest() != RIT.ZIP_SHA256:
        raise SystemExit(u"**儀式の入力の sha256 が封の字と違う。止める**")
    built = RIT.build(zb, V.DEFAULT_PROFILE, label_shas)
    p21 = jload(RITUAL_REL)
    e5_rec = jload(OUT_REL)[u"E5"]
    key = lambda x: (x[u"id"], x[u"型"])
    expect = dict((key(x), x[u"結果"]) for x in p21[u"注入の一覧"])
    for m in e5_rec[u"P21 → P22 で結果が動いた行"]:
        expect[(m[u"id"], m[u"型"])] = m[u"P22"]
    for dr in e5_rec[u"P22 の注入の対象から外れた行(P21 の対象に在った)"]:
        del expect[(dr[u"id"], dr[u"型"])]
    for ap in e5_rec[u"P22 の注入の対象に増えた行"]:
        expect[(ap[u"id"], ap[u"型"])] = ap[u"P22 の結果"]
    got = dict((key(x), x[u"結果"]) for x in built[u"注入の一覧"])
    diff_exp = sorted(k for k in set(expect) | set(got) if expect.get(k) != got.get(k))
    new_rec = jload(RITUAL_P22_REL)
    vol = lambda r: dict((k, v) for k, v in r.items() if k not in (u"所要秒", u"実行環境"))
    plain_def = VD.verify_document(zb, None, None)["claims"]
    plain_p22 = VD.verify_document(zb, NEW, None)["claims"]
    plain_diff = sum(1 for x, y in zip(plain_def, plain_p22) if claim_key(x) != claim_key(y)) + abs(len(plain_def) - len(plain_p22))
    return {u"profile": built[u"入力"][u"profile"] if u"入力" in built else V.DEFAULT_PROFILE,
            u"通した": built[u"通した"], u"止めた": built[u"止めた"],
            u"期待(P21 の記録 + 段 1 の動いた行・外れた行)の行": len(expect), u"今回の行": len(got),
            u"期待と違った行": len(diff_exp), u"違った行の id": [u"%s %s" % k for k in diff_exp[:20]],
            u"採り直した儀式の記録(ritual_2026-10-20.json)と違う欄(所要秒・実行環境を除く)": [k for k in sorted(set(vol(new_rec)) | set(vol(built))) if new_rec.get(k) != built.get(k)],
            u"素の書類: 既定と P22 明示で違った claim": plain_diff, u"素の書類の claim": len(plain_def),
            u"素の書類の state の分布(既定)": built[u"素の書類"][u"state の分布"]}


def stage2_default(label_shas, run_tests=False):
    if V.DEFAULT_PROFILE != NEW:
        raise SystemExit(u"**既定 profile が %s でない: %r(段 2 の測定は既定が P22 になった後)。止める**" % (NEW, V.DEFAULT_PROFILE))
    rec = jload(OUT_REL)
    zips = PP.list_zips()
    texts = {}
    for doc_id, path in zips:
        with io.open(path, "rb") as fh:
            zb = fh.read()
        cat, _why, text = PP.classify_doc(zb)
        if cat == PP.CAT_TEXT:
            texts[doc_id] = (zb, text)
    if sorted(texts) != sorted(d[u"書類"] for d in rec[u"E1"][u"書類別"]):
        raise SystemExit(u"**経営分析の文を持つ書類が段 1 の 67 書類と違う。止める**")
    secs = {}
    t0 = time.time()
    t = time.time()
    e1_ = stage2_e1(texts, rec)
    secs[u"E1"] = round(time.time() - t, 1)
    t = time.time()
    e2_ = stage2_e2(texts, rec)
    secs[u"E2"] = round(time.time() - t, 1)
    # 対照(『0 件』が自分の欠陥でないことの確かめ): 既定を P21 に戻す変異。比較器が差を拾えるなら、E-1 の軽い書類で違った行が出る。
    ctrl_doc = CONTROL_DOC
    old_default = V.DEFAULT_PROFILE
    V.DEFAULT_PROFILE = OLD
    try:
        ctrl = stage2_e1({ctrl_doc: texts[ctrl_doc]}, rec)
    finally:
        V.DEFAULT_PROFILE = old_default
    ctrl_ = {u"書類": ctrl_doc, u"変異": u"vocabulary.DEFAULT_PROFILE を実行中だけ P21 に戻す", u"比べた行": ctrl[u"今回の行"], u"段 1 の P22 の欄と違った行": ctrl[u"段 1 の P22 の欄と違った行"]}
    if V.DEFAULT_PROFILE != old_default:
        raise SystemExit(u"**変異を戻せていない。止める**")
    t = time.time()
    e5_ = stage2_e5(label_shas)
    secs[u"E5"] = round(time.time() - t, 1)
    bundle, n_files = RIT.engine_bundle_sha256()
    out = {u"step": u"**期を縛る P22 の段 2(既定 P21 -> P22)の測定。profile を省いた製品の経路が段 1 の P22 の数と 1 行ずつ一致するか。0 USD・通信なし・engine は測る側から 1 行も変えない**",
           u"封": SEAL, u"HEAD": RIT.git_head(), u"python": platform.python_version(),
           u"engine の束ねた sha256(core/ と adapters/ の file。__pycache__ を除く。repo 相対の path 順)": bundle, u"engine の file 数": n_files,
           u"recipes.py の sha16": sha_file(os.path.join(ROOT, "adapters/xbrl/recipes.py"))[:16],
           u"vocabulary.py の sha16": sha_file(os.path.join(ROOT, "adapters/xbrl/vocabulary.py"))[:16],
           u"DEFAULT_PROFILE": V.DEFAULT_PROFILE,
           u"鍵の名前の有無(値は読まない)": dict((k, (k in os.environ)) for k in KEY_NAMES),
           u"ラベル 2 file の sha256(起動時に照合)": label_shas,
           u"費用": u"0 USD",
           u"E1": e1_, u"E2": e2_, u"E5": e5_, u"対照: 既定を P21 に戻す変異(比較器が差を拾えるか)": ctrl_}
    if run_tests:
        out[u"既存試験"] = [run_pytest("tests/adapters/xbrl")]
    secs[u"全体"] = round(time.time() - t0, 1)
    out[u"所要秒"] = secs
    out[u"差 0 の行数"] = {u"E-1": e1_[u"今回の行"] - e1_[u"段 1 の P22 の欄と違った行"],
                         u"E-2": e2_[u"記録(段 1)の動いた行"] - e2_[u"記録の動いた行のうち違った行(P21・P22 の欄)"],
                         u"E-5": e5_[u"今回の行"] - e5_[u"期待と違った行"]}
    out[u"差のあった行の合計"] = (e1_[u"段 1 の P22 の欄と違った行"] + e1_[u"記録に無い行"] + e2_[u"記録の動いた行のうち違った行(P21・P22 の欄)"] + e2_[u"記録に無い動いた行"]
                          + e5_[u"期待と違った行"] + e5_[u"素の書類: 既定と P22 明示で違った claim"] + len(e5_[u"採り直した儀式の記録(ritual_2026-10-20.json)と違う欄(所要秒・実行環境を除く)"]))
    return out


def run(stage, only_docs=None, run_tests=False, progress=None):
    t_all = time.time()
    label_shas, why = RIT.check_labels()
    if why:
        print(RIT.label_guidance(why), file=sys.stderr)
        raise SystemExit(2)
    # 段 1 の測定は P21・P22 を明示して比べるので、既定がどちらでも同じ数が出る。2026-10-20 段 2 で既定は P22 になった
    # (正本の記録への上書きの guard は main にある)。
    zips = PP.list_zips()
    if only_docs:
        zips = [(d, p) for d, p in zips if d in only_docs]
    texts = {}
    for doc_id, path in zips:
        with io.open(path, "rb") as fh:
            zb = fh.read()
        cat, _why, text = PP.classify_doc(zb)
        if cat == PP.CAT_TEXT:
            texts[doc_id] = (zb, text)
    ids67 = sorted(texts)
    groups, ids40, missing40 = NF.untouched_40()
    if only_docs:
        ids40 = [d for d in ids40 if d in only_docs]
    rec = {u"step": u"**期を縛る直し P22 の段 1 の測定。0 USD・通信なし・engine は測る側から 1 行も変えない**",
           u"環境": env_block(label_shas), u"書類の数": {u"経営分析の文を持つ": len(ids67), u"無改変 40 の集合": len(ids40)}}
    secs = {}
    if stage in ("e1", "all"):
        t = time.time()
        rows, per = [], []
        for d in ids67:
            zb, text = texts[d]
            r, ns, nm = e1_doc(d, zb, text)
            rows.extend(r)
            per.append({u"書類": d, u"site": ns, u"作れた": nm})
            if progress:
                progress(u"E-1 %s site %d 作れた %d" % (d, ns, nm))
        rec[u"E1"] = {u"書類別": per, u"行": rows, u"集計": e1_summary(rows),
                      u"対照: P21 の再計算と穴 B の記録": (e1_vs_record(rows) if not only_docs else None)}
        secs[u"E1"] = round(time.time() - t, 1)
    if stage in ("e2", "all"):
        t = time.time()
        r = compare_docs(ids67)
        r[u"集計2"] = cmp_summary(r)
        rec[u"E2"] = dict(r, **{u"集計": dict(r[u"集計"], **r[u"集計2"])})
        del rec[u"E2"][u"集計2"]
        secs[u"E2"] = round(time.time() - t, 1)
    if stage in ("e3", "all"):
        t = time.time()
        r = compare_docs(ids40)
        s2 = cmp_summary(r)
        r[u"集計"] = dict(r[u"集計"], **s2)
        r[u"40 のうち 67 と重なる書類"] = sorted(set(ids40) & set(ids67))
        rec[u"E3"] = r
        secs[u"E3"] = round(time.time() - t, 1)
    if stage in ("e4", "all"):
        t = time.time()
        work = tempfile.mkdtemp(prefix="period_bind_e4_")
        try:
            rows = e4(work)
        finally:
            import shutil
            shutil.rmtree(work, ignore_errors=True)
        rec[u"E4"] = {u"行": rows, u"集計": e4_summary(rows), u"α 型の経路の構造": e4_structure()}
        secs[u"E4"] = round(time.time() - t, 1)
    if stage in ("e5", "all"):
        t = time.time()
        rec[u"E5"] = e5(label_shas)
        secs[u"E5"] = round(time.time() - t, 1)
    if stage in ("e7", "all"):
        t = time.time()
        e7 = {u"engine の差分": numstat()}
        if run_tests:
            e7[u"既存試験"] = [run_pytest("tests/adapters/xbrl")]
        e7[u"封の 3 か所のほかに直した既存試験"] = EXTRA_EXISTING_FIXES
        rec[u"E7"] = e7
        secs[u"E7"] = round(time.time() - t, 1)
    secs[u"全体"] = round(time.time() - t_all, 1)
    rec[u"所要秒"] = secs
    rec[u"入力の sha256"] = inputs_block(ids67, ids40)
    rec[u"予測の判定"] = judge(rec)
    rec[u"limits"] = [
        u"手元の cache の 67 書類(経営分析の文を持つ)と名指しの直しの無改変 40 書類。無作為ではない。別の書類では動く行が増えうる。",
        u"E-1 の 485 件は『前期の値がそのまま書かれる』誤りだけ(穴 B の限界を引き継ぐ)。作れなかった 287 は通すか不明。千円の提出者に寄る。",
        u"E-1 の site は既定 P21 の土台で選んだ(P22 の土台では選び直していない)。注入の text は profile に依らない。",
        u"E-2・E-3 の『動いた』は (state, pointers, reason, recomputed, form) の組が P21 と P22 で違った claim。正しさは人の読み(結果文書)。",
        u"E-6 の機械の印は span 前後の字の正規表現。型の判定ではない。",
        u"E-4 の Core 自身は cd8 の材料 script と同じ claim の対の付け方の再現(対照 P21 で記録に全行一致を確かめた)。α 型は profile を取らない経路。",
        u"E-7 の既存試験は tests/adapters/xbrl だけ(tests/measure は結果文書に別に書く)。",
        u"前々期(Prior2Year)の値への置き換えは P22 でも通る(P22 が外すのは Prior1Year だけ。未測定。test_recipes_p22.py に挙動の試験)。",
        u"E-1 の注入は構造上『手がかり無し』の文にしか作れない(前期の値を当期の数の位置に書く)。手がかりを付けた文は測れていない。",
        u"手がかりの規則の外の形『前連結会計年度は、9,709千円』(語と数の間に読点)は、P21 では前期の fact に GROUNDED、P22 では前期の fact を外して §1b の止め no_element(no prior2 for prior-year diff) に落ちる。今回の直しが §1b の止めへ新しい行を送る(合成で確認、test_recipes_p22.py に挙動の試験。実書類での件数は未測定)。",
        u"E-6 の『過半』は分母の選び方に依る(GROUNDED を離れた行 / 動いた GROUNDED の行 / 動いた全 state の行)。3 つの率を結果文書に並べた。"]
    return rec


def main_default(a):
    if a.out or a.docs or a.merge:
        raise SystemExit(u"--stage default は正本の記録に新欄 %s を足す(--out・--docs・--merge は取らない)" % STAGE2_KEY)
    label_shas, why = RIT.check_labels()
    if why:
        print(RIT.label_guidance(why), file=sys.stderr)
        return 2
    new = stage2_default(label_shas, run_tests=a.run_tests)
    path = os.path.join(ROOT, OUT_REL)
    rec = jload(OUT_REL)
    rec[STAGE2_KEY] = new
    with io.open(path, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
        fh.write(u"\n")
    print(u"=== 期を縛る P22 の段 2(profile 省略 = %s・手元の cache・鍵なし・0 USD)===" % V.DEFAULT_PROFILE)
    f_ = lambda d: u"%d / %d" % (d[u"件"], d[u"分母"])
    print(u"E-1: 今回の行 %d・段 1 の P22 の欄と違った行 %d・通した %s・止めた %s" % (
        new[u"E1"][u"今回の行"], new[u"E1"][u"段 1 の P22 の欄と違った行"], f_(new[u"E1"][u"通した(GROUNDED のまま)"]), f_(new[u"E1"][u"止めた(VALUE_MISMATCH)"])))
    print(u"E-2: 動いた行 %d・記録 %d・違った行 %d・記録に無い %d" % (
        new[u"E2"][u"既定と P21 で動いた行"], new[u"E2"][u"記録(段 1)の動いた行"], new[u"E2"][u"記録の動いた行のうち違った行(P21・P22 の欄)"], new[u"E2"][u"記録に無い動いた行"]))
    print(u"E-5: 通した %s・止めた %s・期待と違った行 %d" % (new[u"E5"][u"通した"][u"字"], new[u"E5"][u"止めた"][u"字"], new[u"E5"][u"期待と違った行"]))
    print(u"差のあった行の合計 %d / 所要 %s / 記録: %s の %s" % (new[u"差のあった行の合計"], json.dumps(new[u"所要秒"], ensure_ascii=False), path, STAGE2_KEY))
    return 0


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=u"P22 の段 1 の測定(0 USD・通信なし)")
    ap.add_argument("--stage", choices=["e1", "e2", "e3", "e4", "e5", "e7", "all", "default"], default="all")
    ap.add_argument("--out", default=None, help=u"記録の出力先。--stage all の既定は " + OUT_REL)
    ap.add_argument("--docs", default=None, help=u"docID をコンマ区切りで絞る(軽い走らせ直し用)")
    ap.add_argument("--no-tests", action="store_true", help=u"E-7 で pytest を走らせない")
    ap.add_argument("--run-tests", action="store_true", help=u"--stage default で tests/adapters/xbrl の pytest も走らせて記録する(約 20 分)")
    ap.add_argument("--merge", action="store_true",
                    help=u"--out の既存の記録に、この --stage の節(E1…E7)だけを差し替えて書く(判定・所要秒・環境を作り直す)。E-7 の既存試験だけを走らせ直すとき")
    a = ap.parse_args(argv)
    if a.stage == "default":
        return main_default(a)
    out = a.out
    if out is None:
        if a.stage != "all" or a.docs:
            raise SystemExit(u"--stage all 以外か --docs のときは --out を渡す(正本の記録を上書きしない)")
        if V.DEFAULT_PROFILE != "P21":
            raise SystemExit(u"**正本の記録 %s は段 1(既定が P21 の時点)の記録。既定が %s の今は上書きしない(--out を渡すか --stage default)**" % (OUT_REL, V.DEFAULT_PROFILE))
        out = os.path.join(ROOT, OUT_REL)
    if a.merge and (a.stage == "all" or not a.out or not os.path.exists(a.out)):
        raise SystemExit(u"--merge は --stage e1〜e7 のどれか 1 つと、既に在る --out が要る")
    rec = run(a.stage, set(a.docs.split(",")) if a.docs else None,
              run_tests=((a.stage == "all" or (a.merge and a.stage == "e7")) and not a.no_tests),
              progress=lambda m: print(m, file=sys.stderr))
    if a.merge:
        with io.open(out, encoding="utf-8") as fh:
            old_rec = json.load(fh)
        sec = {"e1": u"E1", "e2": u"E2", "e3": u"E3", "e4": u"E4", "e5": u"E5", "e7": u"E7"}[a.stage]
        old_rec[sec] = rec[sec]
        old_rec[u"環境"] = rec[u"環境"]
        old_rec.setdefault(u"所要秒", {})[sec] = rec[u"所要秒"][sec]
        old_rec[u"所要秒"].setdefault(u"追記", []).append(u"%s を走らせ直した(--merge)。所要 %s 秒" % (sec, rec[u"所要秒"][sec]))
        old_rec[u"予測の判定"] = judge(old_rec)
        rec = old_rec
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with io.open(out, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
        fh.write(u"\n")
    print(u"=== 期を縛る P22 の段 1(%s → %s・手元の cache・鍵なし・0 USD)===" % (OLD, NEW))
    for k, v in sorted(rec[u"予測の判定"].items()):
        print(u"%s: %s → %s" % (k, v[u"実測"], v[u"判定"]))
    print(u"所要 %s 秒 / 記録: %s" % (json.dumps(rec[u"所要秒"], ensure_ascii=False), out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
