# -*- coding: utf-8 -*-
u"""既定の profile を P26 から P27 に切り替える(段 2)の測定 ― 封 ``docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md`` §2(S-1〜S-12)。

    cd audit-core
    python3 measure/xbrl_default_p27_2026-10-28.py --stage all --out fixtures/xbrl/default_p27_2026-10-28.json --reds <試験の赤の表>
    python3 measure/xbrl_default_p27_2026-10-28.py --stage s1 --out <file> --docs S100YMFV,S100YXFQ      # 軽い走らせ直し(--out 必須)

**0 USD・通信なし・鍵の値は読まない・席は呼ばない。** 書類は手元の cache の ZIP だけ: 67 書類は ``~/.cache/audit-core/edinet/``、新しい標本の 30 書類は
``~/.cache/audit-core/edinet-fresh-2026-10-21/``(どちらも**読むだけ**で 1 file も足さない。件数と名前の一覧の sha256 を測定の前後で記録に残す)。
engine(``core/``・``adapters/``)は**測る側から 1 行も変えない**。評価用・調整用の AI の文・DB の応答(``~/.cache/audit-core/edinetdb-p27/``)は開かない
(この script は ``edinet`` と ``edinet-fresh-2026-10-21`` の ZIP と、同梱の儀式の書類と、repo の記録・文書しか読まない)。

この測定が確かめること: **profile を省いた(= 既定の)製品の経路が、P27 を明示した経路と 1 byte も違わない**(S-1)。さらに既定の出力は、手元の 97 書類の
後退の記録 ``fixtures/xbrl/p27/regress97_2026-10-27.json``(P27 を明示して E の engine で測った)の P27 の欄と、書類ごとの 4 state・出力の sha256(engine の欄を除く)・
動いた行の集合で 1 行ずつ比べて同じ(S-2・S-3)。

  S-1  97 書類(67 + 30)を ``verify_document(zb, None, None)``(既定)と ``verify_document(zb, "P27", None)`` で検証し、``sort_keys`` の JSON の字が 1 byte も違わない書類の数。
       対照(『差 0』が自分の欠陥でないことの確かめ): ``vocabulary.DEFAULT_PROFILE`` を**実行中だけ** P26 に戻すと、同じ比較で違う書類が出る(97 / 97)。
  S-2  67 書類の既定の 4 state。既定(P27)と P26 の差(動いた行・向き・GROUNDED を離れる行・VALUE_MISMATCH に入る行・新しい GROUNDED)。regress97 の P27 の欄との照合。
  S-3  30 書類の既定の 4 state と、既定と P26 で state の違う行の向き。regress97 の P27 の欄との照合。
  S-4  儀式(同梱の 1 書類)を既定で。P26 の記録(写し ``ritual_2026-10-20_p26.json``)と違う欄。
  S-5  67 書類の既定の報告形(``report_customer``)の節の件数。
  S-6  誤りを通す側: 穴 B の注入 485 件を既定で。段 2 の材料の注入 64 件で Core 自身が GROUNDED にした数。P26 の記録(``p26_2026-10-21.json`` の Q3)の P26 の欄と 1 行ずつ比べる。
  S-7  engine の差分(封の commit からの ``git diff --numstat``)。
  S-10 README の儀式の節の数と記録、README.md の「いまの段」の行、``docs/FACTS_FOR_BUYERS_2026-10-20.md`` の P26・P27 の字の数。
  S-11 試験 file の数(ディスク上)と ``fixtures/suite_coverage_2026-10-16.json`` の覆われていない file。
  S-12 判定の記録(評価用の結果の文書 ``docs/XBRL_P27_RESULT_2026-10-27.md`` の判定の文)。
  S-8・S-9 は試験の赤の数(実装席が走らせた実測を人が書いた表。``--reds`` で渡す)。この script は測らず、表を記録に写して file の sha256 を残し、封の幅と突き合わせる。
"""
from __future__ import print_function

import argparse
import collections
import concurrent.futures
import hashlib
import importlib.util
import io
import json
import multiprocessing
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


PB = _mod("measure/xbrl_period_bind_2026-10-20.py", "period_bind_for_default_p27")
PP, RIT, FP = PB.PP, PB.RIT, PB.FP
RF = _mod("measure/xbrl_customer_report_fix_2026-10-21.py", "report_fix_for_default_p27")

from adapters.xbrl import edinet as ED           # noqa: E402
from adapters.xbrl import report_customer as RC  # noqa: E402
from adapters.xbrl import verify_document as VD  # noqa: E402
from adapters.xbrl import vocabulary as V        # noqa: E402

SEAL = "docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md"
SEAL_COMMIT = "87f83fd"
OUT_REL = "fixtures/xbrl/default_p27_2026-10-28.json"
P26_REL = "fixtures/xbrl/p26_2026-10-21.json"
FETCHED_REL = "fixtures/xbrl/fresh/fetched_2026-10-21.json"
REGRESS_REL = "fixtures/xbrl/p27/regress97_2026-10-27.json"
RITUAL_REL = "fixtures/xbrl/ritual_2026-10-20.json"
RITUAL_P26_REL = "fixtures/xbrl/ritual_2026-10-20_p26.json"
SUITE_REL = "fixtures/suite_coverage_2026-10-16.json"
README_REL = ("README.md", "README.en.md")
FACTS_REL = "docs/FACTS_FOR_BUYERS_2026-10-20.md"
P27_RESULT_REL = "docs/XBRL_P27_RESULT_2026-10-27.md"
EXISTING_CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
FRESH_DIR = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet-fresh-2026-10-21")
OLD, NEW = "P26", "P27"
KEY_NAMES = PB.KEY_NAMES
ENGINE_FILES = ("adapters/xbrl/vocabulary.py", "adapters/xbrl/verify_document.py", "adapters/xbrl/recipes.py", "adapters/xbrl/extract.py",
                "adapters/xbrl/registry_setup.py", "adapters/xbrl/report_customer.py", "adapters/xbrl/comparators.py", "adapters/xbrl/report.py",
                "adapters/xbrl/run.py")
STATES = ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND")
PARTIAL_PATH = None
G = {}      # fork した子プロセスが読む(run() が pool を作る前に埋める)


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def frac(a, b):
    return {u"件": a, u"分母": b, u"率": pct(a, b)}


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    with io.open(p, "rb") as fh:
        return sha_bytes(fh.read())


def jload(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return json.load(fh)


def dumps(o):
    return json.dumps(o, ensure_ascii=False, sort_keys=True)


def dump_no_engine(out):
    u"""regress97 の script(``dump_no_engine``)と同じ字: engine の欄を除いた JSON。"""
    d = dict(out)
    d.pop("engine", None)
    return json.dumps(d, ensure_ascii=False, sort_keys=True)


def git(*a):
    return PP.git(*a)


def kv(c):
    return dict(sorted((str(k), v) for k, v in dict(c).items()))


def list_zips_of(d):
    return sorted(f for f in os.listdir(d) if f.endswith(".zip")) if os.path.isdir(d) else None


def cache_snapshot():
    u"""既存の cache 2 つの件数と名前の一覧の sha256(file の中身は読まない)。"""
    out = {}
    for key, d in ((u"edinet", EXISTING_CACHE), (u"edinet-fresh-2026-10-21", FRESH_DIR)):
        names = sorted(os.listdir(d)) if os.path.isdir(d) else []
        out[key] = {u"件数": len([n for n in names if n.endswith(".zip")]), u"名前の一覧の sha256": sha_bytes(u"\n".join(names).encode("utf-8"))}
    return out


# ====================================================================================================
# 入力(書類の一覧)
def doc_lists():
    p26 = jload(P26_REL)
    ids67 = sorted(p26[u"入力の sha256"][u"書類 67(経営分析の文を持つ)の sha256"])
    fetched = jload(FETCHED_REL)
    ids30 = list(fetched[u"使う書類"])
    return p26, ids67, fetched, ids30


def zip_path(doc, fresh):
    return os.path.join(FRESH_DIR if fresh else EXISTING_CACHE, doc + ".zip")


# ====================================================================================================
# S-1〜S-3: 書類ごと(既定・P27 明示・既定を実行中だけ P26 に戻した対照)
def _states(out):
    return collections.Counter(c["state"] for c in out["claims"])


def _row(c):
    return (c["state"], c["reason"])


def doc_job(args):
    doc, fresh = args
    with io.open(zip_path(doc, fresh), "rb") as fh:
        zb = fh.read()
    out_def = VD.verify_document(zb, None, None)
    out_27 = VD.verify_document(zb, NEW, None)
    old_default = V.DEFAULT_PROFILE
    V.DEFAULT_PROFILE = OLD
    try:
        out_ctrl = VD.verify_document(zb, None, None)       # 対照: 既定を実行中だけ P26 に戻す = P26 の経路
    finally:
        V.DEFAULT_PROFILE = old_default
    if V.DEFAULT_PROFILE != old_default:
        raise SystemExit(u"**変異を戻せていない。止める**")
    d_def, d_27, d_ctrl = dumps(out_def), dumps(out_27), dumps(out_ctrl)
    ids = [c["id"] for c in out_def["claims"]]
    if ids != [c["id"] for c in out_ctrl["claims"]] or ids != [c["id"] for c in out_27["claims"]]:
        raise SystemExit(u"**claim の id の並びが違う: %s。止める**" % doc)
    moved = []             # state が違う行
    moved_any = []         # state・reason・pointers のどれかが違う行
    for x, y in zip(out_ctrl["claims"], out_def["claims"]):          # x = P26(対照)、y = 既定
        if _row(x) != _row(y) or x.get("pointers") != y.get("pointers"):
            moved_any.append(x["id"])
        if x["state"] != y["state"]:
            moved.append({u"doc": doc, u"id": x["id"], u"P26": {u"state": x["state"], u"reason": x["reason"]}, u"既定": {u"state": y["state"], u"reason": y["reason"]}})
    return {u"doc": doc, u"標本": u"新しい標本 30" if fresh else u"手元の 67",
            u"zip の sha256": sha_bytes(zb), u"claims": len(ids),
            u"既定と P27 明示が同じ byte": d_def == d_27, u"既定を P26 に戻した対照が既定と同じ byte": d_def == d_ctrl,
            u"profile の欄": {u"既定": out_def["profile"], u"P27 明示": out_27["profile"], u"対照": out_ctrl["profile"]},
            u"既定の出力の sha256(engine の欄を除く)": sha_bytes(dump_no_engine(out_def).encode("utf-8")),
            u"既定の state": kv(_states(out_def)), u"P27 明示の state": kv(_states(out_27)), u"P26 の state": kv(_states(out_ctrl)),
            u"state の違う行": moved, u"state・reason・pointers のどれかが違う行の数": len(moved_any)}


def direction(m):
    return u"%s → %s" % (m[u"P26"][u"state"], m[u"既定"][u"state"])


def population_summary(rows, reg_pop):
    u"""1 つの標本の集計と、regress97 の P27 の欄との照合(``reg_pop`` = その標本の regress97 の書類の行と動いた行)。"""
    n = len(rows)
    claims = sum(r[u"claims"] for r in rows)
    st = collections.Counter()
    st26 = collections.Counter()
    moved = []
    for r in rows:
        st.update(r[u"既定の state"])
        st26.update(r[u"P26 の state"])
        moved.extend(r[u"state の違う行"])
    dirs = collections.Counter(direction(m) for m in moved)
    reg_docs = dict((d["docID"], d) for d in reg_pop["docs"])
    st_diff = [r[u"doc"] for r in rows if reg_docs[r[u"doc"]][u"4 state"]["P27"] != dict((s, r[u"既定の state"].get(s, 0)) for s in STATES)]
    sha_diff = [r[u"doc"] for r in rows if reg_docs[r[u"doc"]][u"出力の sha256(engine の欄を除く)"]["P27"] != r[u"既定の出力の sha256(engine の欄を除く)"]]
    reg_moved = set((m["docID"], m["id"], m[u"前"]["state"], m[u"前"]["reason"], m[u"後"]["state"], m[u"後"]["reason"]) for m in reg_pop["moved"])
    got_moved = set((m[u"doc"], m[u"id"], m[u"P26"]["state"], m[u"P26"]["reason"], m[u"既定"]["state"], m[u"既定"]["reason"]) for m in moved)
    return {u"書類": n, u"claims": claims,
            u"既定と P27 明示で違った書類": sum(1 for r in rows if not r[u"既定と P27 明示が同じ byte"]),
            u"対照(既定を実行中だけ P26 に戻す)で違った書類": sum(1 for r in rows if not r[u"既定を P26 に戻した対照が既定と同じ byte"]),
            u"既定の 4 state": dict((s, st.get(s, 0)) for s in STATES), u"P26 の 4 state": dict((s, st26.get(s, 0)) for s in STATES),
            u"既定と P26 で state の違う行": len(moved), u"state は同じで reason か pointer が違う行": sum(r[u"state・reason・pointers のどれかが違う行の数"] for r in rows) - len(moved),
            u"向き": kv(dirs),
            u"GROUNDED を離れる行": sum(1 for m in moved if m[u"P26"][u"state"] == "GROUNDED"),
            u"VALUE_MISMATCH に入る行": sum(1 for m in moved if m[u"既定"][u"state"] == "VALUE_MISMATCH" and m[u"P26"][u"state"] != "VALUE_MISMATCH"),
            u"新しい GROUNDED": sum(1 for m in moved if m[u"既定"][u"state"] == "GROUNDED"),
            u"regress97 の P27 の 4 state と違う書類": st_diff,
            u"regress97 の P27 の出力の sha256 と違う書類": sha_diff,
            u"regress97 の動いた行(P26 → P27)と同じ集合": reg_moved == got_moved,
            u"regress97 に無い動いた行": len(got_moved - reg_moved), u"regress97 に在って今回に無い行": len(reg_moved - got_moved)}


# ====================================================================================================
# S-4: 儀式(既定)
def ritual_default(label_shas):
    zp = os.path.join(ROOT, RIT.ZIP_REL)
    with io.open(zp, "rb") as fh:
        zb = fh.read()
    if sha_bytes(zb) != RIT.ZIP_SHA256:
        raise SystemExit(u"**儀式の入力の sha256 が封の字と違う。止める**")
    built = RIT.build(zb, V.DEFAULT_PROFILE, label_shas)       # 儀式 script の main と同じ呼び方(profile = 既定)
    rec = jload(RITUAL_P26_REL)
    now = jload(RITUAL_REL)
    vol = lambda r: dict((k, v) for k, v in r.items() if k not in (u"所要秒", u"実行環境"))
    differ = [k for k in sorted(set(vol(rec)) | set(vol(built))) if rec.get(k) != built.get(k)]
    differ_now = [k for k in sorted(set(vol(now)) | set(vol(built))) if now.get(k) != built.get(k)]
    ids = lambda r: sorted((x.get(u"id"), x.get(u"型")) for x in r[u"通した の一覧"])
    return {u"profile": built[u"入力"][u"profile"], u"通した": built[u"通した"], u"止めた": built[u"止めた"],
            u"止めた でも 通した でもない結果": built[u"止めた でも 通した でもない結果"], u"通した の分け方": built[u"通した の分け方"],
            u"素の書類 claim": built[u"素の書類"][u"claim"], u"素の書類の state の分布": built[u"素の書類"][u"state の分布"],
            u"土台の state の分布": built[u"注入"][u"土台(経営分析の文のまま)の state の分布"], u"注入の対象": built[u"注入"][u"注入の対象(GROUNDED の site)"],
            u"通した の一覧の (id, 型)": ids(built), u"P26 の記録の 通した の一覧の (id, 型)": ids(rec),
            u"P26 の記録(ritual_2026-10-20_p26.json)と違う欄(所要秒・実行環境を除く)": differ,
            u"採り直した儀式の記録(ritual_2026-10-20.json)と違う欄(所要秒・実行環境を除く)": differ_now,
            u"P26 の記録の通した": rec[u"通した"], u"P26 の記録の止めた": rec[u"止めた"], u"P26 の記録のその他": rec[u"止めた でも 通した でもない結果"],
            u"P26 の記録の素の書類の state の分布": rec[u"素の書類"][u"state の分布"]}


# ====================================================================================================
# S-5: 報告形(既定)
def report_doc(doc):
    zp = ED.cache_path(doc)
    with io.open(zp, "rb") as fh:
        zb = fh.read()
    labels, _meta = RF.compose(G["std_labels"], G["std_meta"], zp)
    out = VD.verify_document(zb, None, None)
    dei = RC.dei_from_zip(zp, (out.get("input") or {}).get("instance_source"))
    md = RC.render_markdown(out, labels, True, dei)
    heads = RF.heading_counts(md)
    states = collections.Counter(c["state"] for c in out["claims"])
    return {u"doc": doc, u"違う(節の件数)": heads[u"違う"], u"VALUE_MISMATCH(state)": states.get("VALUE_MISMATCH", 0),
            u"要確認(節の件数)": heads[u"要確認"], u"一致(節の件数)": heads[u"一致"], u"対象外": heads[u"対象外"], u"判断しない": heads[u"判断しない"], u"claims": len(out["claims"])}


# ====================================================================================================
# S-6: 穴 B の注入 485 件(既定と P26 明示)
def hole_b_doc(doc):
    zb, text = G["texts"][doc]
    sites, _diag, _b, _o, sentences, _base = PP.find_sites(zb, text)
    for s in sites:
        s[u"書類"] = doc
    rows_def = PB.inject_with_profile(doc, zb, text, sites, sentences, None)           # 既定
    rows_old = PB.inject_with_profile(doc, zb, text, sites, sentences, OLD)            # 対照: P26 明示
    by_old = dict((r[u"id"], r) for r in rows_old)
    out = []
    for r in rows_def:
        o = by_old[r[u"id"]]
        out.append({u"書類": doc, u"id": r[u"id"],
                    u"既定": {u"結果": r[u"結果"], u"state": r[u"結果の細目"], u"reason": r.get(u"後の reason"), u"pointers": r.get(u"後の pointers")},
                    u"P26": {u"結果": o[u"結果"], u"state": o[u"結果の細目"], u"reason": o.get(u"後の reason"), u"pointers": o.get(u"後の pointers")}})
    return out


def s2_default(work):
    u"""段 2 の材料の注入(192 行 = 注入 64 + 無改変 128)の Core 自身を既定で。``PB.e4`` と同じ再構成で、profile だけ省略(None)。"""
    mat = PB.jload(PB.S2_MATERIAL_REL)
    seed, _meta = PB.IJ.verify_seed_sealed(PB.MB.SEED_FILE)
    rows_out = []
    with PB.HS2.patched():
        for p in mat[u"書類ごと"]:
            doc = p["docID"]
            rb = PB.HS2.rebuild(doc, work, seed)
            if sha_bytes(rb["task"].encode("utf-8")) != p[u"材料"][u"sha256"]:
                raise SystemExit(u"**再構成した task の sha256 が材料の記録と合わない: %s**" % doc)
            with io.open(ED.cache_path(doc), "rb") as fh:
                zb = fh.read()
            chosen = dict((c["id"], c) for c in rb["chosen"])
            core_def = PB.core_say_for(zb, rb["tampered"], None, rb["rows"])
            for m in sorted(rb["rows"], key=lambda r: r["id"]):
                rid = m["id"]
                inj_id = m.get("**注入**")
                typ = chosen[inj_id]["type"] if inj_id else None
                rows_out.append({u"doc": doc, u"id": rid, u"注入か": bool(inj_id), u"注入の型": typ,
                                 u"Core 自身(既定)": {u"state": PB.HT.core_state(core_def[rid]), u"参照先": core_def[rid]["参照先"]}})
    return rows_out


# ====================================================================================================
# S-7: engine の差分
def numstat():
    out = {}
    for f in ENGINE_FILES:
        rc, o = git("diff", SEAL_COMMIT, "--numstat", "--", f)
        p = o.split()
        out[f] = {u"挿入": int(p[0]), u"削除": int(p[1])} if len(p) >= 2 and p[0].isdigit() else {u"挿入": 0, u"削除": 0}
    rc, o = git("diff", SEAL_COMMIT, "--numstat", "--", "core")
    rc2, st = git("status", "--porcelain", "--", "core")
    out[u"core/"] = {u"差の行数": sum(int(l.split("\t")[0]) + int(l.split("\t")[1]) for l in o.splitlines() if l.split("\t")[0].isdigit()), u"status": st.strip()}
    others = sorted(f for f in os.listdir(os.path.join(ROOT, "adapters", "xbrl")) if f.endswith(".py"))
    out[u"adapters/xbrl の file 数"] = len(others)
    out[u"vocabulary.py・verify_document.py 以外で封の commit から動いた file"] = [
        f for f in others if f not in ("vocabulary.py", "verify_document.py") and (git("diff", SEAL_COMMIT, "--numstat", "--", "adapters/xbrl/" + f)[1].strip() != u"")]
    out[u"vocabulary.py の削除された行(封の commit から)"] = [l[1:] for l in git("diff", "-U0", SEAL_COMMIT, "--", "adapters/xbrl/vocabulary.py")[1].splitlines() if l.startswith("-") and not l.startswith("---")]
    out[u"verify_document.py の削除された行(封の commit から)"] = [l[1:] for l in git("diff", "-U0", SEAL_COMMIT, "--", "adapters/xbrl/verify_document.py")[1].splitlines() if l.startswith("-") and not l.startswith("---")]
    return out


# ====================================================================================================
# S-10・S-11・S-12 の材料(記録・文書から機械で読む)
def readme_block():
    ritual = jload(RITUAL_REL)
    out = {}
    for rel in README_REL:
        with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
            t = fh.read()
        head = u"## 10 分の再現" if rel == "README.md" else u"## 10-minute reproduction"
        i = t.index(u"\n" + head) + 1
        j = t.find(u"\n## ", i + 1)
        sec = t[i:j + 1] if j >= 0 else t[i:]
        out[rel] = {u"節に 通した の字": ritual[u"通した"][u"字"] in sec, u"節に 止めた の字": ritual[u"止めた"][u"字"] in sec}
    with io.open(os.path.join(ROOT, "README.md"), encoding="utf-8") as fh:
        ja = fh.read()
    out[u"README.md の いまの段 の行"] = {u"P27(2026-10-28、既定を P27)": len(re.findall(r"(?m)^- \*\*いまの段\(2026-10-28、既定を P27\)\*\*", ja)),
                                       u"P26(2026-10-23、既定を P26)": len(re.findall(r"(?m)^- \*\*いまの段\(2026-10-23、既定を P26\)\*\*", ja)),
                                       u"いまの段 の行の合計": len(re.findall(r"(?m)^- \*\*いまの段", ja))}
    with io.open(os.path.join(ROOT, FACTS_REL), encoding="utf-8") as fh:
        facts = fh.read()
    out[FACTS_REL] = {u"P26 の字の数": facts.count(u"P26"), u"P27 の字の数": facts.count(u"P27")}
    return out


def suite_block():
    u"""試験 file の数はディスクを数える(記録 ``suite_coverage_2026-10-16.json`` は ``--write`` の後に動くので、この記録は記録を読まない)。覆われていない file は記録から。"""
    n = 0
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "__pycache__", ".pytest_cache")]
        n += sum(1 for f in files if f.startswith("test_") and f.endswith(".py"))
    d = jload(SUITE_REL)
    return {u"試験 file の数(ディスク上)": n, u"覆われていない file": len(d["uncovered_files"]), u"覆いの記録の試験 file の数": d["test_files_on_disk"]}


def decision_block():
    with io.open(os.path.join(ROOT, P27_RESULT_REL), encoding="utf-8") as fh:
        t = fh.read()
    lines = [l for l in t.splitlines() if l.startswith(u"判定(P27)") or l.startswith(u"判定(P27E)")]
    return {u"判定の文": lines}


# ====================================================================================================
def seal_bounds():
    u"""封 §2 の予測の行の太字を、出てくる順に読む(判定の幅は封の字から。実行の後に書き換えない)。"""
    with io.open(os.path.join(ROOT, SEAL), encoding="utf-8") as fh:
        t = fh.read()
    b = {}
    for l in t.splitlines():
        m = re.match(r"\| \*\*S-(\d+)\*\* \|", l)
        if m:
            cells = [c.strip() for c in l.strip().strip(u"|").split(u"|")]
            b["S-" + m.group(1)] = re.findall(r"\*\*([^*]+)\*\*", cells[1])
    return b


def num(s):
    return int(s.replace(u",", u""))


def rng(s):
    a, b = s.split(u"〜")
    return int(a), int(b)


def judge(rec, bounds):
    u"""予測 S-1〜S-12 の当たり外れを、記録の数と封の字の太字から機械で。S-8・S-9 は記録に試験の赤の表(``--reds``)が在るときだけ。"""
    J = {}
    s1 = rec[u"S1"]
    b = bounds["S-1"]       # ['0 / 67', '0 / 30', '97 / 97']
    J["S-1"] = (s1[u"手元の 67"][u"既定と P27 明示で違った書類"] == int(b[0].split(u" / ")[0]) and s1[u"新しい標本 30"][u"既定と P27 明示で違った書類"] == int(b[1].split(u" / ")[0])
                and s1[u"手元の 67"][u"対照(既定を実行中だけ P26 に戻す)で違った書類"] + s1[u"新しい標本 30"][u"対照(既定を実行中だけ P26 に戻す)で違った書類"] == int(b[2].split(u" / ")[0]))
    b = bounds["S-2"]       # [4,371, 433, 1,601, 1,394, 28, 25, 3, 0(他の向き), 0(離れる), 0(VM に入る), 0(新 GROUNDED), 0(reason か pointer), 0(過不足)]
    s2 = rec[u"S2"]
    J["S-2"] = ([s2[u"既定の 4 state"][s] for s in STATES] == [num(x) for x in b[:4]] and s2[u"既定と P26 で state の違う行"] == num(b[4])
                and s2[u"向き"] == {u"POINTER_NOT_FOUND → UNVERIFIABLE": num(b[5]), u"UNVERIFIABLE → POINTER_NOT_FOUND": num(b[6])}
                and s2[u"GROUNDED を離れる行"] == num(b[8]) and s2[u"VALUE_MISMATCH に入る行"] == num(b[9]) and s2[u"新しい GROUNDED"] == num(b[10])
                and s2[u"state は同じで reason か pointer が違う行"] == num(b[11])
                and s2[u"regress97 に無い動いた行"] + s2[u"regress97 に在って今回に無い行"] == num(b[12]) and s2[u"regress97 の動いた行(P26 → P27)と同じ集合"])
    b = bounds["S-3"]
    s3 = rec[u"S3"]
    J["S-3"] = ([s3[u"既定の 4 state"][s] for s in STATES] == [num(x) for x in b[:4]] and s3[u"既定と P26 で state の違う行"] == num(b[4])
                and s3[u"向き"] == {u"POINTER_NOT_FOUND → UNVERIFIABLE": num(b[5]), u"UNVERIFIABLE → POINTER_NOT_FOUND": num(b[6])}
                and s3[u"GROUNDED を離れる行"] == num(b[8]) and s3[u"VALUE_MISMATCH に入る行"] == num(b[9]) and s3[u"新しい GROUNDED"] == num(b[10])
                and s3[u"regress97 に無い動いた行"] + s3[u"regress97 に在って今回に無い行"] == num(b[11]) and s3[u"regress97 の動いた行(P26 → P27)と同じ集合"])
    s4 = rec[u"S4"]
    b = bounds["S-4"]       # ['2 / 243 = 0.8%', '210 / 243 = 86.4%', '31', '340', '25', '33', '14', ...]
    o = s4[u"止めた でも 通した でもない結果"]
    st = s4[u"素の書類の state の分布"]
    J["S-4"] = (s4[u"通した"][u"字"] == b[0] and s4[u"止めた"][u"字"] == b[1] and o == {"detected:POINTER_NOT_FOUND": num(b[2])}
                and [st["GROUNDED"], st["POINTER_NOT_FOUND"], st["UNVERIFIABLE"], st["VALUE_MISMATCH"]] == [num(x) for x in b[3:7]]
                and sorted(s4[u"P26 の記録(ritual_2026-10-20_p26.json)と違う欄(所要秒・実行環境を除く)"]) == sorted([u"入力", u"注入", u"素の書類"])
                and s4[u"採り直した儀式の記録(ritual_2026-10-20.json)と違う欄(所要秒・実行環境を除く)"] == []
                and s4[u"通した の一覧の (id, 型)"] == s4[u"P26 の記録の 通した の一覧の (id, 型)"])
    s5 = rec[u"S5"]
    b = bounds["S-5"]
    J["S-5"] = ([s5[u"違う"], s5[u"要確認"], s5[u"対象外"], s5[u"判断しない"], s5[u"一致"]] == [num(x) for x in b[:5]] and s5[u"違う"] == s5[u"VALUE_MISMATCH(state)の合計"]
                and s5[u"節の合計"] == s5[u"総 claim"])
    s6 = rec[u"S6"]
    b = bounds["S-6"]       # ['0 / 485', '480', '5', '0 / 64', '0', '0']
    J["S-6"] = (s6[u"穴 B"][u"既定で通した"][u"件"] == int(b[0].split(u" / ")[0]) and s6[u"穴 B"][u"既定で止めた"] == num(b[1]) and s6[u"穴 B"][u"既定のその他"] == num(b[2])
                and s6[u"段 2"][u"全注入で Core 自身(既定)が GROUNDED"][u"件"] == int(b[3].split(u" / ")[0])
                and s6[u"穴 B"][u"P26 の記録の P26 の欄と違った行"] == num(b[4]) and s6[u"段 2"][u"P26 の記録の P26 の欄と違った行"] == num(b[5]))
    s7 = rec[u"S7"]
    b = bounds["S-7"]       # ['≤ 8', '1', '1', '1', '16', '37']
    voc, vd = s7[u"adapters/xbrl/vocabulary.py"], s7[u"adapters/xbrl/verify_document.py"]
    J["S-7"] = (voc[u"挿入"] <= int(b[0].split(u"≤")[1]) + 0 and voc[u"削除"] == num(b[1]) and vd[u"挿入"] == num(b[2]) and vd[u"削除"] == num(b[3])
                and s7[u"core/"][u"差の行数"] == 0 and s7[u"vocabulary.py・verify_document.py 以外で封の commit から動いた file"] == []
                and s7[u"adapters/xbrl の file 数"] == num(b[4]) and rec[u"環境"][u"engine の指紋"][u"adapter_xbrl_py_files"] == num(b[4])
                and rec[u"環境"][u"frozen_bundle の本数"] == num(b[5]))
    if u"試験の赤" in rec:
        J["S-8"], J["S-9"] = judge_reds(rec, bounds)
    p10 = rec[u"S10"]
    J["S-10"] = (all(p10[r][u"節に 通した の字"] and p10[r][u"節に 止めた の字"] for r in README_REL) and p10[FACTS_REL][u"P26 の字の数"] == 0 and p10[FACTS_REL][u"P27 の字の数"] == 0
                 and p10[u"README.md の いまの段 の行"][u"P27(2026-10-28、既定を P27)"] == 1 and p10[u"README.md の いまの段 の行"][u"P26(2026-10-23、既定を P26)"] == 1)
    s11 = rec[u"S11"]
    b = bounds["S-11"]      # ['232', '232', '234']? 太字の並びは封の字の通り
    J["S-11"] = s11[u"試験 file の数(ディスク上)"] == num(b[2]) and s11[u"覆われていない file"] == 0 and s11[u"覆いの記録の試験 file の数"] == num(b[2])
    J["S-12"] = rec[u"S12"][u"判定の文"] == [u"判定(P27E): P27E を「外部の数の文に使う profile」として採用する。", u"判定(P27): P27 を「既定の候補」として記録する。"]
    return J


def judge_reds(rec, bounds):
    u"""S-8・S-9。表の足し算と封の幅との当たり外れ。"""
    r = rec[u"試験の赤"]
    s8, s9 = r[u"S8"], r[u"S9"]
    kinds = collections.Counter(s8[u"種類"][i] for i in s8[u"tests/measure"][u"ids"] + s8[u"tests/adapters/xbrl"][u"ids"])
    total = s8[u"tests/measure"][u"赤"] + s8[u"tests/adapters/xbrl"][u"赤"]
    b8 = bounds["S-8"]       # ['81 本', '29 file', '16 本', '11 file', '97', '98〜105', '37', '17', '9', '18', '0', '記録(fixtures)…門 0', '0', '2', '7', '3', '0', '0']
    lo, hi = rng([x for x in b8 if u"〜" in x][0])
    p27 = s8[u"P27 の門 5 本の赤"]
    ok8 = (lo <= total <= hi and s8[u"golden・fixtures・measure/tests・core の赤"] == 0 and s8[u"記録を書き換えないと緑にならない門"] == 0 and s8[u"人間の決定の字の門の赤"] == 0
           and set(kinds) <= set([u"1", u"2", u"3", u"4"])
           and [p27[k] for k in (u"test_xbrl_p27_result.py", u"test_xbrl_p27_seal.py", u"test_xbrl_p27_engine_result.py", u"test_xbrl_p27_eval.py", u"test_xbrl_p27_order.py")] == [num(x) for x in b8[-5:]])
    ok9 = s9[u"増えた赤"] == num(bounds["S-9"][0].split(u" ")[0]) and s9[u"実装の後"][u"赤"] == 0
    return ok8, ok9


# ====================================================================================================
def run(stage, only_docs=None, jobs=3, reds_path=None):
    t_all = time.time()
    label_shas, why = RIT.check_labels()
    if why:
        print(RIT.label_guidance(why), file=sys.stderr)
        raise SystemExit(2)
    p26, ids67, fetched, ids30 = doc_lists()
    if only_docs:
        want = set(only_docs)
        ids67 = [d for d in ids67 if d in want]
        ids30 = [d for d in ids30 if d in want]
    snap0 = cache_snapshot()
    reg = jload(REGRESS_REL)
    reg_pops = {}
    for pop in (u"手元の 67", u"新しい標本 30"):
        reg_pops[pop] = {"docs": [d for d in reg[u"書類"] if d[u"標本"] == pop], "moved": reg[u"動いた行"][pop][u"P26 → P27"]}
    jobs_list = [(d, False) for d in ids67] + [(d, True) for d in ids30]
    ctx = multiprocessing.get_context("fork")
    secs = {}
    rec = {}
    t = time.time()
    with concurrent.futures.ProcessPoolExecutor(max_workers=jobs, mp_context=ctx) as ex:
        rows = list(ex.map(doc_job, jobs_list))
    secs[u"S1〜S3"] = round(time.time() - t, 1)
    r67 = [r for r in rows if r[u"標本"] == u"手元の 67"]
    r30 = [r for r in rows if r[u"標本"] == u"新しい標本 30"]
    sha67 = dict((r[u"doc"], r[u"zip の sha256"]) for r in r67)
    sha30 = dict((r[u"doc"], r[u"zip の sha256"]) for r in r30)
    sums = {}
    for pop, rr in ((u"手元の 67", r67), (u"新しい標本 30", r30)):
        pop_docs = set(r[u"doc"] for r in rr)
        sub = {"docs": [d for d in reg_pops[pop]["docs"] if d["docID"] in pop_docs], "moved": [m for m in reg_pops[pop]["moved"] if m["docID"] in pop_docs]}
        sums[pop] = population_summary(rr, sub)
    rec[u"S1"] = dict(sums, **{u"書類別": [dict((k, v) for k, v in r.items() if k != u"state の違う行") for r in rows]})
    rec[u"S2"] = dict(sums[u"手元の 67"], **{u"動いた行": [m for r in r67 for m in r[u"state の違う行"]]})
    rec[u"S3"] = dict(sums[u"新しい標本 30"], **{u"動いた行": [m for r in r30 for m in r[u"state の違う行"]]})
    if stage in ("s1",):
        return finish(rec, secs, t_all, label_shas, sha67, sha30, snap0, ids67, ids30, p26, fetched, reg, partial=True)
    # S-4
    t = time.time()
    rec[u"S4"] = ritual_default(label_shas)
    secs[u"S4"] = round(time.time() - t, 1)
    # S-5
    t = time.time()
    G["std_labels"], G["std_meta"] = RC.load_labels_with_meta(RF.labels_dir(), None)
    with concurrent.futures.ProcessPoolExecutor(max_workers=jobs, mp_context=ctx) as ex:
        per = list(ex.map(report_doc, ids67))
    tot = lambda k: sum(x[k] for x in per)
    rec[u"S5"] = {u"書類別": per, u"違う": tot(u"違う(節の件数)"), u"要確認": tot(u"要確認(節の件数)"), u"対象外": tot(u"対象外"), u"判断しない": tot(u"判断しない"),
                  u"一致": tot(u"一致(節の件数)"), u"VALUE_MISMATCH(state)の合計": tot(u"VALUE_MISMATCH(state)"), u"総 claim": tot(u"claims"),
                  u"節の合計": tot(u"違う(節の件数)") + tot(u"要確認(節の件数)") + tot(u"対象外") + tot(u"判断しない") + tot(u"一致(節の件数)")}
    secs[u"S5"] = round(time.time() - t, 1)
    # S-6 穴 B
    t = time.time()
    texts = {}
    for doc_id, path in PP.list_zips():
        if doc_id not in ids67:
            continue
        with io.open(path, "rb") as fh:
            zb = fh.read()
        cat, _why, text = PP.classify_doc(zb)
        if cat == PP.CAT_TEXT:
            texts[doc_id] = (zb, text)
    want_docs = sorted(d[u"書類"] for d in p26[u"Q3"][u"穴 B"][u"書類別"])
    if not only_docs and sorted(texts) != want_docs:
        raise SystemExit(u"**経営分析の文を持つ書類が P26 の記録の穴 B の書類と違う。止める**")
    G["texts"] = texts
    with concurrent.futures.ProcessPoolExecutor(max_workers=jobs, mp_context=ctx) as ex:
        hb = [r for part in ex.map(hole_b_doc, sorted(texts)) for r in part]
    want = dict(((r[u"書類"], r[u"id"]), r[u"P26"]) for r in p26[u"Q3"][u"穴 B"][u"行"])
    keyf = lambda v: (v[u"結果"], v[u"state"], v[u"reason"], v[u"pointers"])
    diff = [r for r in hb if (r[u"書類"], r[u"id"]) not in want or keyf(r[u"既定"]) != keyf(want[(r[u"書類"], r[u"id"])])]
    diff_ctrl = [r for r in hb if keyf(r[u"既定"]) != keyf(r[u"P26"])]
    passed_kinds = (PP.K_MOVED, PP.K_SAME, PP.K_OTHER, PP.K_ODD)
    kd = collections.Counter(r[u"既定"][u"結果"] for r in hb)
    k26 = collections.Counter(r[u"P26"][u"結果"] for r in hb)
    n = len(hb)
    hole = {u"注入": n, u"記録(P26 の欄)の行": len(want), u"既定で通した": frac(sum(kd[k] for k in passed_kinds), n), u"既定で止めた": kd[PP.K_STOP],
            u"既定のその他": kd[PP.K_ELSE], u"既定の結果": kv(kd), u"P26 明示(対照)で通した": frac(sum(k26[k] for k in passed_kinds), n),
            u"P26 明示(対照)で止めた": k26[PP.K_STOP], u"P26 明示の結果": kv(k26),
            u"P26 の記録の P26 の欄と違った行": len(diff), u"違った行": [{u"書類": r[u"書類"], u"id": r[u"id"]} for r in diff[:20]],
            u"P26 明示(対照)と違った行": len(diff_ctrl)}
    # S-6 段 2
    work = tempfile.mkdtemp(prefix="default_p27_s2_", dir=os.environ.get("TMPDIR"))
    try:
        s2 = s2_default(work)
    finally:
        import shutil
        shutil.rmtree(work, ignore_errors=True)
    want2 = dict(((r[u"doc"], r[u"id"]), r[u"Core 自身 P26"]) for r in p26[u"Q3"][u"段 2"][u"行"])
    diff2 = [r for r in s2 if want2.get((r[u"doc"], r[u"id"])) != r[u"Core 自身(既定)"]]
    inj = [r for r in s2 if r[u"注入か"]]
    step2 = {u"行": len(s2), u"注入": len(inj), u"記録(P26 の欄)の行": len(want2),
             u"全注入で Core 自身(既定)が GROUNDED": frac(sum(1 for r in inj if r[u"Core 自身(既定)"][u"state"] == "GROUNDED"), len(inj)),
             u"P26 の記録の P26 の欄と違った行": len(diff2), u"違った行": [u"%s %s" % (r[u"doc"], r[u"id"]) for r in diff2[:20]]}
    rec[u"S6"] = {u"穴 B": hole, u"段 2": step2}
    secs[u"S6"] = round(time.time() - t, 1)
    rec.update({u"S7": numstat(), u"S10": readme_block(), u"S11": suite_block(), u"S12": decision_block()})
    if reds_path:
        with io.open(reds_path, encoding="utf-8") as fh:
            rec[u"試験の赤"] = json.load(fh)
        rec[u"試験の赤の入力 file の sha256"] = sha_file(reds_path)
    return finish(rec, secs, t_all, label_shas, sha67, sha30, snap0, ids67, ids30, p26, fetched, reg, partial=False)


def finish(rec, secs, t_all, label_shas, sha67, sha30, snap0, ids67, ids30, p26, fetched, reg, partial):
    bundle, n_files = RIT.engine_bundle_sha256()
    in67 = p26[u"入力の sha256"][u"書類 67(経営分析の文を持つ)の sha256"]
    in30 = dict((x["docID"], x["sha256"]) for x in fetched[u"取得した書類"])
    fz = subprocess.run([sys.executable, os.path.join(ROOT, "fixtures", "frozen_bundle_sha.py")], cwd=os.path.dirname(ROOT), capture_output=True, text=True).stdout
    m = re.search(r"束ねた sha: ([0-9a-f]{64})  \(対象 (\d+) 本", fz)
    snap1 = cache_snapshot()
    rc_seal, seal_full = git("rev-parse", SEAL_COMMIT)
    fp = VD.engine_fingerprint()
    out = {u"step": u"**既定の profile を P26 から P27 に切り替える(段 2)の測定。profile を省いた製品の経路が P27 を明示した経路と 1 byte も違わないか。0 USD・通信なし・engine は測る側から 1 行も変えない**",
           u"封": SEAL,
           u"封の commit": seal_full.strip(),
           u"環境": {u"HEAD": RIT.git_head(), u"python": platform.python_version(), u"DEFAULT_PROFILE": V.DEFAULT_PROFILE,
                   u"比べた profile": [u"省略(None = vocabulary.DEFAULT_PROFILE)", u"P27(明示)", u"P26(既定を実行中だけ P26 に戻した対照)"],
                   u"engine の指紋": dict((k, fp[k]) for k in (u"adapter_xbrl_py_sha256", u"adapter_xbrl_py_files", u"core_py_sha256", u"core_py_files")),
                   u"engine の束ねた sha256(core/ と adapters/ の file。__pycache__ を除く。repo 相対の path 順)": bundle, u"engine の file 数": n_files,
                   u"frozen_bundle の束ねた sha": m.group(1) if m else None, u"frozen_bundle の本数": int(m.group(2)) if m else None,
                   u"recipes.py の sha16": sha_file(os.path.join(ROOT, "adapters/xbrl/recipes.py"))[:16],
                   u"vocabulary.py の sha16": sha_file(os.path.join(ROOT, "adapters/xbrl/vocabulary.py"))[:16],
                   u"verify_document.py の sha16": sha_file(os.path.join(ROOT, "adapters/xbrl/verify_document.py"))[:16],
                   u"鍵の名前の有無(値は読まない)": dict((k, (k in os.environ)) for k in KEY_NAMES),
                   u"ラベル 2 file の sha256(起動時に照合)": label_shas, u"費用": u"0 USD",
                   u"評価用・調整用の AI の文・DB の応答": u"開いていない(この script は ~/.cache/audit-core/edinetdb-p27/ を読まない)",
                   u"通信": u"この script は urllib・socket・http を import しない。adapters は urllib を import するが接続は起きない"},
           u"入力": {u"手元の 67 書類の sha256": dict((d, sha67[d]) for d in sorted(sha67)), u"新しい標本 30 書類の sha256": dict((d, sha30[d]) for d in sorted(sha30)),
                   u"手元の 67 が P26 の記録の入力と同じ": all(in67.get(d) == s for d, s in sha67.items()) and len(sha67) == len(ids67),
                   u"新しい標本 30 が取得の記録の入力と同じ": all(in30.get(d) == s for d, s in sha30.items()) and len(sha30) == len(ids30),
                   u"regress97 の記録の sha256": sha_file(os.path.join(ROOT, REGRESS_REL)),
                   u"置き場": u"~/.cache/audit-core/edinet/ と ~/.cache/audit-core/edinet-fresh-2026-10-21/(どちらも読むだけ。1 file も足さない)"},
           u"cache の前後": {u"前": snap0, u"後": snap1, u"変化なし": snap0 == snap1}}
    out.update(rec)
    out[u"所要秒"] = dict(secs, **{u"全体": round(time.time() - t_all, 1)})
    if PARTIAL_PATH and not partial:           # 判定の前の測った値を残す(判定の字が落ちても重い測定を失わない。--rejudge で判定だけやり直せる)
        with io.open(PARTIAL_PATH, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(out, ensure_ascii=False, indent=1) + u"\n")
    if not partial:
        if u"試験の赤の入力 file の sha256" in out:
            out[u"入力"][u"試験の赤の入力 file の sha256"] = out.pop(u"試験の赤の入力 file の sha256")
        out[u"予測の判定"] = dict((k, {u"当たり": v}) for k, v in sorted(judge(out, seal_bounds()).items(), key=lambda kv: int(kv[0].split(u"-")[1])))
        out[u"limits"] = [u"S-8(試験の赤の数)・S-9(重い走らせ直し)は実装席が走らせた実測を人が書いた表(入力の file の sha256 を記録した)で、この script は測っていない",
                         u"S-1 の対照は『既定を実行中だけ P26 に戻す』変異で、P26 を明示した経路と同じ出力になる(profile の欄が違う)",
                         u"読み(正しい文かどうか)は測っていない。この測定は『既定の配線が P27 の明示と同じか』だけを見る",
                         u"S-12 は評価用の結果の文書の判定の文を写すだけ。判定を求め直すのは結果の門(記録 4 つから別の関数で)"]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=("all", "s1"), default="all")
    ap.add_argument("--out", default=None)
    ap.add_argument("--docs", default=None, help=u"カンマ区切りの書類 ID(軽い走らせ直し用)")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--partial", default=None, help=u"判定の前の測った値を書く file(デバッグ用)")
    ap.add_argument("--rejudge", default=None, help=u"--partial の file から判定だけやり直す(デバッグ用)")
    ap.add_argument("--reds", default=None, help=u"試験の赤の表(人が書いた表)。内容は記録に写し、file の sha256 を残す")
    a = ap.parse_args(argv)
    only = [x for x in (a.docs or u"").split(u",") if x] or None
    if a.stage != "all" or only:
        if not a.out:
            raise SystemExit(u"--stage s1 か --docs のときは --out が必須(正本の記録を上書きしない)")
    out_path = a.out or os.path.join(ROOT, OUT_REL)
    global PARTIAL_PATH
    if a.rejudge:
        if not a.out:
            raise SystemExit(u"--rejudge のときは --out が必須")
        with io.open(a.rejudge, encoding="utf-8") as fh:
            out = json.load(fh)
        out[u"予測の判定"] = dict((k, {u"当たり": v}) for k, v in sorted(judge(out, seal_bounds()).items(), key=lambda kv: int(kv[0].split(u"-")[1])))
        with io.open(out_path, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(out, ensure_ascii=False, indent=1) + u"\n")
        print(u"rejudge → %s: %s" % (out_path, out[u"予測の判定"]))
        return 0
    if a.partial:
        PARTIAL_PATH = a.partial
    if V.DEFAULT_PROFILE != NEW:
        raise SystemExit(u"**既定 profile が %s でない: %r(この測定は既定が P27 になった後)。止める**" % (NEW, V.DEFAULT_PROFILE))
    out = run(a.stage, only, a.jobs, a.reds)
    with io.open(out_path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=False) + u"\n")
    s2 = out.get(u"S2", {})
    print(u"=== 既定 %s・書類 %d + %d ===" % (V.DEFAULT_PROFILE, len(out[u"入力"][u"手元の 67 書類の sha256"]), len(out[u"入力"][u"新しい標本 30 書類の sha256"])))
    print(u"S-1  既定と P27 明示で違った書類: 67 で %s・30 で %s / 対照(既定を P26 に戻す)で違った書類 %s・%s" % (
        out[u"S1"][u"手元の 67"][u"既定と P27 明示で違った書類"], out[u"S1"][u"新しい標本 30"][u"既定と P27 明示で違った書類"],
        out[u"S1"][u"手元の 67"][u"対照(既定を実行中だけ P26 に戻す)で違った書類"], out[u"S1"][u"新しい標本 30"][u"対照(既定を実行中だけ P26 に戻す)で違った書類"]))
    print(u"S-2  67 の既定の 4 state: %s" % s2.get(u"既定の 4 state"))
    if u"予測の判定" in out:
        print(u"予測: " + u"・".join(u"%s=%s" % (k, u"当たり" if v[u"当たり"] else u"外れ") for k, v in out[u"予測の判定"].items()))
    print(u"所要 %s 秒 → %s" % (out[u"所要秒"][u"全体"], out_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
