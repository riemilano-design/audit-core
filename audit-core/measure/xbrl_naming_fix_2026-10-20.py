# -*- coding: utf-8 -*-
u"""名指しの直し(P21)の段 1 の測定(封 `docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md` §2・§3)。

**0 USD・席を呼ばない・通信しない。** engine(`adapters/xbrl/recipes.py` の最後の枝と
`adapters/xbrl/vocabulary.py` の旗 `last_branch_cues` と P21)は別に実装済みで、この script は測るだけ。
記録・答え(C0・C1・cd8・`c0_p20`)は読むだけで書き換えない。

測るもの(封 §2):

  1. gen_c 8 書類の (ア)(注入 128 件、種 `measure/SEED.json`)を P21 と P20 で。行ごとに並べる。
  2. cd8 の (ア) 8 書類を P21 で(P20 の記録 `a_core_vs_grep_P20_2026-10-17.json` と行ごとに並べる)。
  3. 無改変の 40 書類(下の ``UNTOUCHED_40``)を ``verify_document`` で P20 と P21。
  4. K-4 の 20 行 / C0-3(engine を Core-P(P21)の参照先に)。
  5. 対照 M-C1(P20 で回すと `c0_p20` の記録に全欄一致)・M-C3(旗を P20 でも真にすると M-C1 が赤)。
     M-C2(既存の試験の緑)は pytest を別に走らせて結果文書に書く(この script では測らない)。

読み方(数を見る前に決めた。封の字で 1 通りに決まらなかった所):

  * 封 N-1 の「誤認定 3(P20 19)」は **T5 50 件のうち Core-P が別の参照先を名指した件数**(``誤認定`` が真の行)。
    参照先を出した件(T3 の名指し 7 を含む)を分母にした率は別欄に出す。
  * 封 N-4 の「GROUNDED の行で state か参照先が動いた数」は、P20 か P21 のどちらかで GROUNDED の主張のうち
    ``(state, pointers, reason, recomputed, form)`` が違った数。「動いた行」は同じ 5 つの組が違った主張。
  * 実装の置き場所: 最後の枝の 3 つの直しは、§1b の止め(前々期が無い「前連結会計年度は…」)の**後ろ**(``if cur:`` の中)に置いた。
    最初の実装は止めの前に置き、無改変の 40 書類の試行で、止めていた 2 行(S100YYN7 N054・S100Z4Q1 N025)が名指しに戻った
    (PNF -> VM)。止めは 2026-10-08 の人間の決定なので、止めを先に効かせる置き方に直してから測り直した(試行の記録は結果文書)。
  * 封 N-12 は段 2(既定 = P21)の予測で、段 1 では判定しない。参考として、P21 を ``test_p16_matches_the_holdout_dumps``
    と同じ照合に当てた結果の差を出す(判定に使わない)。

    cd audit-core
    python3 measure/xbrl_naming_fix_2026-10-20.py [--out PATH]
"""
import argparse
import collections
import dataclasses
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, HERE)


def _mod(rel, name):
    sp = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


#: P20 の測定の script(書き直さない。``run_profile``・``counts``・``gold_of_row`` を使う)。
PM = _mod("measure/xbrl_gen_c_p20_2026-10-20.py", "gen_c_p20_for_naming_fix")
C0 = PM.C0
AC = PM.AC
RS = PM.RS
core = PM.core

from adapters.xbrl import edinet as ED          # noqa: E402
from adapters.xbrl import verify_document as VD  # noqa: E402
from adapters.xbrl import vocabulary as V        # noqa: E402

SEAL = "docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md"
FX = os.path.join(ROOT, "fixtures", "xbrl", "naming_fix")
OUT = os.path.join(FX, "p21_2026-10-20.json")
GEN = PM.GEN
CD8 = PM.CD8
C0P20_REC = os.path.join(GEN, "c0_p20_2026-10-20.json")
C1_REC = PM.C1_REC
CD8_P20_REC = PM.CD8_P20_REC
K45 = PM.K45
HOLDOUT = os.path.join(ROOT, "fixtures", "xbrl", "holdout_p16", "commander_only")

#: 無改変の 40 書類(診断席の集合)。5 群の id。開発 14 は ``tests/adapters/xbrl/test_verify_entry.py`` の
#: ``ROBUSTNESS_P16`` の key、未使用 2 は ``HOLDOUT_DOCS``(``fixtures/xbrl/holdout_p16/commander_only`` の dump の書類)。
DEV_14 = ["S100YMFV", "S100Z1WR", "S100Z35K", "S100Z37J", "S100Z3BW", "S100Z3CO", "S100Z3HP", "S100Z3JY",
          "S100Z3V1", "S100Z433", "S100Z4B6", "S100Z4DE", "S100Z4PA", "S100Z4Q1"]
UNUSED_2 = ["S100Z39P", "S100Z4N9"]
EXPECTED_HOLDOUT_P21_ROWS = ("S100Z4N9", "S100Z39P")


def _load(p):
    return C0._load(p)


def sha_file(p):
    return PM.sha_file(p)


def jround(x):
    return PM.jround(x)


def pct(a, b):
    return PM.pct(a, b)


def frac(a, b):
    return PM.frac(a, b)


def cp(r):
    return r[u"腕"]["Core-P"]


def t5_of(rows):
    return [r for r in rows if r[u"型"] == "T5_COINCIDENT"]


def score(rows):
    u"""(ア) の rows から封 N-1〜N-3 の数を**数え直す**(同じ関数を P20・P21 の rows に当てる)。"""
    t5 = t5_of(rows)
    t1 = [r for r in rows if r[u"型"] == "T1_VALUE"]
    t3 = [r for r in rows if r[u"型"] == "T3_ABSENT"]
    pointed = [r for r in rows if cp(r)[u"判定"][u"参照先を出した"]]
    return {
        u"T5 の件数": len(t5), u"注入の合計": len(rows),
        u"T5 の特定(Core-P)": frac(sum(1 for r in t5 if cp(r)[u"判定"][u"特定"]), len(t5)),
        u"T5 の誤認定(Core-P。別の参照先を名指した行)": sum(1 for r in t5 if cp(r)[u"判定"][u"誤認定"]),
        u"T5 の誤認定の id": [r["id"] for r in t5 if cp(r)[u"判定"][u"誤認定"]],
        u"T5 の特定の id": [r["id"] for r in t5 if cp(r)[u"判定"][u"特定"]],
        u"誤認定率(分母 = 参照先を出した全型の件。参考)": frac(sum(1 for r in pointed if cp(r)[u"判定"][u"誤認定"]), len(pointed)),
        u"T1 の通し(Core-P。確認済みと言った)": frac(sum(1 for r in t1 if cp(r)[u"言うこと"] == u"確認済み"), len(t1)),
        u"T3 の名指し(Core-P)": frac(sum(1 for r in t3 if cp(r)[u"判定"][u"参照先を出した"]), len(t3)),
    }


def row_diff(rows_a, rows_b, la, lb):
    u"""同じ注入 id の行で違ったものを 1 件ずつ(Core-P の参照先・特定・誤認定、Core の言うこと)。"""
    if [r["id"] for r in rows_a] != [r["id"] for r in rows_b]:
        raise SystemExit(u"**注入の id の並びが違う。止める**")
    out = []
    for x, y in zip(rows_a, rows_b):
        if jround(x) == jround(y):
            continue
        out.append({u"id": x["id"], u"型": x[u"型"], u"gold": x[u"正解"][u"正解"],
                    la: {u"参照先": cp(x)[u"参照先"], u"言うこと": cp(x)[u"言うこと"], u"特定": cp(x)[u"判定"][u"特定"],
                         u"誤認定": cp(x)[u"判定"][u"誤認定"]},
                    lb: {u"参照先": cp(y)[u"参照先"], u"言うこと": cp(y)[u"言うこと"], u"特定": cp(y)[u"判定"][u"特定"],
                         u"誤認定": cp(y)[u"判定"][u"誤認定"]}})
    return out


def state_totals(per):
    tot = collections.Counter()
    for p in per:
        for k, v in p[u"states"].items():
            tot[k] += v
    return dict(sorted(tot.items()))


# ------------------------------------------------------------------ 無改変の 40 書類
def claim_key(c):
    return (c["state"], tuple(c["pointers"]), c["reason"], c["recomputed"], c["form"])


def classify_move(x, y):
    u"""動いた主張がどの直しの形か(機械的な読み。f1/f2/f3 の定義は結果文書に書く)。"""
    py, px = y["pointers"], x["pointers"]
    if y["state"] == "POINTER_NOT_FOUND" and x["state"] == "VALUE_MISMATCH":
        return u"F2′(名指さず止めた)"
    if len(py) == 3 and py[-1] == "formula:a-b" and len(px) == 1:
        return u"F3b(残高の対)"
    if len(py) == 1 and "@Prior1Year" in py[0] and px != py:
        return u"F1′(前期の fact)"
    return u"その他"


def untouched_40():
    gen = _load(PM.C0.DRAW)[u"引いた 8 件"]
    ar = _load(CD8_P20_REC)[u"書類"]
    cd = _load(os.path.join(CD8, "draw_2026-10-17.json"))[u"引いた 8 件"]
    groups = [(u"gen_c 8", gen), (u"(ア)/final8 8", ar), (u"cd8 の引いた 8", cd), (u"開発 14", DEV_14), (u"未使用 2", UNUSED_2)]
    allv = [d for _n, l in groups for d in l]
    if len(allv) != 40 or len(set(allv)) != 40:
        raise SystemExit(u"**無改変 40 書類が 40 でない / 重なりがある: %d / %d。止める**" % (len(allv), len(set(allv))))
    missing = [d for d in allv if not os.path.exists(ED.cache_path(d))]
    return groups, allv, missing


def run_untouched(allv, groups):
    per_doc, moved_rows = [], []
    tot = collections.Counter()
    for d in allv:
        zb = io.open(ED.cache_path(d), "rb").read()
        a = VD.verify_document(zb, "P20")
        b = VD.verify_document(zb, "P21")
        if [c["id"] for c in a["claims"]] != [c["id"] for c in b["claims"]]:
            raise SystemExit(u"**claim の id の並びが P20 と P21 で違う: %s。止める**" % d)
        if [c["span"] for c in a["claims"]] != [c["span"] for c in b["claims"]]:
            raise SystemExit(u"**claim の span が P20 と P21 で違う: %s。止める**" % d)
        n_moved = 0
        for x, y in zip(a["claims"], b["claims"]):
            tot[u"claims"] += 1
            if claim_key(x) == claim_key(y):
                continue
            n_moved += 1
            tot[u"動いた"] += 1
            g = x["state"] == "GROUNDED" or y["state"] == "GROUNDED"
            if g:
                tot[u"GROUNDED の行で動いた"] += 1
            tot[u"%s -> %s" % (x["state"], y["state"])] += 1
            kind = classify_move(x, y)
            tot[u"型 " + kind] += 1
            moved_rows.append({u"doc": d, u"id": x["id"], u"subject": x["subject"], u"span": x["span"],
                               u"P20": {u"state": x["state"], u"pointers": x["pointers"], u"reason": x["reason"],
                                        u"recomputed": x["recomputed"], u"form": x["form"]},
                               u"P21": {u"state": y["state"], u"pointers": y["pointers"], u"reason": y["reason"],
                                        u"recomputed": y["recomputed"], u"form": y["form"]},
                               u"型(機械的な読み)": kind, u"GROUNDED が関わる": g})
        per_doc.append({u"doc": d, u"claims": len(a["claims"]), u"動いた": n_moved,
                        u"GROUNDED(P20)": a["document"]["states"].get("GROUNDED", 0),
                        u"GROUNDED(P21)": b["document"]["states"].get("GROUNDED", 0),
                        u"states(P20)": a["document"]["states"], u"states(P21)": b["document"]["states"]})
    return per_doc, moved_rows, dict(sorted(tot.items()))


def holdout_dump_reference():
    u"""参考(判定に使わない): P21 を ``test_p16_matches_the_holdout_dumps`` と同じ照合に当てて、違う行を出す。"""
    out = {}
    for doc in UNUSED_2:
        dump = _load(os.path.join(HOLDOUT, "dump_P16_%s.json" % doc))
        key = _load(os.path.join(HOLDOUT, "key_%s.json" % doc))
        by_row = {r[u"行の鍵"]: r["claim_id"] for r in key["rows_map"]}
        zb = io.open(ED.cache_path(doc), "rb").read()
        res = {}
        for pname in ("P20", "P21"):
            got = {c["id"]: c for c in VD.verify_document(zb, pname)["claims"]}
            diff = []
            for row_key, want in dump.items():
                cid = by_row[row_key.split(":", 1)[1]]
                g = got[cid]
                if (g["state"], g["pointers"], g["reason"], g["subject"]) != (want["state"], want["pointers"], want["reason"], want["subject"]):
                    diff.append({u"行の鍵": row_key, u"claim_id": cid, u"dump(P16)": {u"state": want["state"], u"pointers": want["pointers"]},
                                 pname: {u"state": g["state"], u"pointers": g["pointers"]}})
            res[pname] = {u"dump の行": len(dump), u"違った行": len(diff), u"明細": diff}
        out[doc] = res
    return out


# ------------------------------------------------------------------ engine の差分(N-9)
def _git(args, binary=False):
    return C0._git(args, binary=binary)


def engine_diff():
    num = _git(["diff", "HEAD", "--numstat", "--relative", "--", "core", "adapters"])
    status = _git(["status", "--porcelain", "--", "core", "adapters"])
    files = {}
    for ln in num.split("\n"):
        if ln.strip():
            ad, de, p = ln.split("\t")
            files[p] = (int(ad), int(de))
    # recipes.py: ``git diff -U0`` の hunk が 1 つだけで、削除 0 行の挿入。直前の HEAD の行が最後の枝の ``cur = ...`` であること
    old = _git(["show", "HEAD:./adapters/xbrl/recipes.py"]).split("\n")
    hunks = [ln for ln in _git(["diff", "HEAD", "-U0", "--relative", "--", "adapters/xbrl/recipes.py"]).split("\n") if ln.startswith("@@")]
    only_insert = False
    anchor = func = ins_n = None
    if len(hunks) == 1:
        m = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", hunks[0])
        o_start, o_len, n_len = int(m.group(1)), int(m.group(2) if m.group(2) is not None else 1), int(m.group(4) if m.group(4) is not None else 1)
        only_insert = (o_len == 0)
        if only_insert:
            # -N,0: N 行目の**直後**に挿入。直前の 2 行 = §1b の止め(前々期が無い)の理由と return
            anchor = old[o_start - 2].strip() + " / " + old[o_start - 1].strip()
            i = o_start - 1
            while i >= 0 and not old[i].startswith("def "):
                i -= 1
            func = old[i].split("(")[0] if i >= 0 else None
            ins_n = n_len
    return {u"git diff HEAD --numstat -- core adapters": files,
            u"git status --porcelain -- core adapters": status,
            u"recipes.py の差分は挿入 1 か所だけ(HEAD の行は 1 つも変えていない)": only_insert,
            u"挿入の直前の HEAD の行": anchor, u"挿入先の関数": func,
            u"挿入の行数": ins_n,
            u"core/ の差分の file": [p for p in files if p.startswith("core/")],
            u"instance.py・extract.py の差分": [p for p in files if p.endswith(("instance.py", "extract.py"))]}


def engine_sha():
    u"""cwd に依らず repo 相対の path で、core/ と adapters/ の追跡 file(作業木の内容)の束ねた sha256。"""
    paths = [p for p in _git(["ls-files", "--", "core", "adapters"]).split("\n") if p]
    rows = []
    for p in paths:
        with io.open(os.path.join(ROOT, p), "rb") as fh:
            rows.append("%s\t%s" % (p, hashlib.sha256(fh.read()).hexdigest()))
    one = {}
    for rel in ("adapters/xbrl/recipes.py", "adapters/xbrl/vocabulary.py", "adapters/xbrl/verify_document.py",
                "adapters/xbrl/instance.py", "adapters/xbrl/extract.py"):
        one[rel] = sha_file(os.path.join(ROOT, rel))
    return {u"file 数": len(paths), u"束ねた sha256(repo 相対 path・作業木の内容)": hashlib.sha256("\n".join(sorted(rows)).encode("utf-8")).hexdigest(),
            u"主な file の sha256": one, u"git HEAD": _git(["rev-parse", "--short", "HEAD"])}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    if os.path.exists(a.out):
        raise SystemExit(u"既に在る: %s(測り直さない)" % a.out)
    t_start = time.time()
    env = C0.env_check()
    if env[u"設定されている key の数"] != 0:
        raise SystemExit(u"**LLM の API key が設定されている。席を呼ばない段なので止める**")
    if V.DEFAULT_PROFILE != "P20":
        raise SystemExit(u"**既定の profile が P20 でない(段 1 は P20 のまま)。止める**")
    if V.PROFILES["P21"] != dataclasses.replace(V.PROFILES["P20"], name="P21", last_branch_cues=True):
        raise SystemExit(u"**P21 が P20 + 旗 1 つでない。止める**")
    if [n for n, p in V.PROFILES.items() if p.last_branch_cues] != ["P21"]:
        raise SystemExit(u"**旗が P21 以外でも真。止める**")

    in_sha = lambda: {u"c0_p20_2026-10-20.json": sha_file(C0P20_REC), u"c0_2026-10-20.json": sha_file(C0.OUT),
                      u"c1_2026-10-20.json": sha_file(C1_REC), u"draw_2026-10-20.json": sha_file(C0.DRAW),
                      u"cd8 a_core_vs_grep_P20_2026-10-17.json": sha_file(CD8_P20_REC),
                      u"cd8 draw_2026-10-17.json": sha_file(os.path.join(CD8, "draw_2026-10-17.json"))}
    in_before = in_sha()
    c0p20 = _load(C0P20_REC)
    c1 = _load(C1_REC)
    draw = _load(C0.DRAW)
    docs = draw[u"引いた 8 件"]
    fetched = _load(C0.FETCHED)
    fetched_by = {x["docID"]: x for x in fetched[u"取得した書類"]}
    seed, seed_meta = AC.IJ.verify_seed_sealed(AC.SEED_FILE)
    registry = RS.register_all(core.Registry.default())
    os.makedirs(AC.TMP, exist_ok=True)

    # ================================================================ gen_c: P21 / P20
    p21 = PM.run_profile("P21", docs, seed, registry, fetched_by)
    p20 = PM.run_profile("P20", docs, seed, registry, fetched_by)
    rows21, rows20 = p21["rows"], p20["rows"]
    rows_rec = c0p20[u"C0-2 rows(P20)"]

    # ---- M-C1: P20 の run が c0_p20 の記録に全欄一致
    rec_main = c0p20[u"**C0-2 (ア) の main() の出力(P20)**"]
    rec_c03 = c0p20[u"**C0-3 engine を Core-P(P20)の参照先に当てた**"]
    mc1_main_diff = sorted(k for k in set(rec_main) | set(p20["main"]) if k != "rows" and rec_main.get(k) != p20["main"].get(k))
    rec_c01 = {x[u"doc"]: x for x in c0p20[u"C0-1(P20 を明示して回した)"][u"書類ごと"]}
    c01_20 = [{k: v for k, v in x.items() if k != "_out"} for x in p20["per"]]
    mc1 = {u"(ア) main() の出力(rows 以外)で違った欄": mc1_main_diff,
           u"(ア) main() の rows が c0_p20 の C0-2 rows と一致": p20["main"]["rows"] == rows_rec,
           u"Recorder 再走の rows が一致": jround(p20["rows"]) == rows_rec,
           u"C0-3 の rows が一致": jround(p20["c03"]) == rec_c03["rows"],
           u"C0-3 の集計が一致": jround(PM.c03_tally(p20["c03"])) == rec_c03[u"集計"],
           u"注入の件数が一致": jround(p20["counts"]) == rec_main[u"注入の件数"],
           u"各注入に対応が付いた claim が一致": jround(p20["claim_info"]) == c0p20[u"C0-2 各注入に対応が付いた Core の claim(P20。読むための記録)"],
           u"C0-1 の claims・states が書類ごとに一致": all(x[u"claims"] == rec_c01[x[u"doc"]][u"claims"] and x[u"states"] == rec_c01[x[u"doc"]][u"states"]
                                                   for x in c01_20),
           u"Recorder 再走 = main() の出力(P20)": p20["recorder_same"]}
    mc1[u"当たり"] = mc1_main_diff == [] and all(v is True for k, v in mc1.items() if not k.startswith(u"(ア) main() の出力(rows 以外)"))

    # ---- cd8 (ア): P20 の記録 / P21 / (補助) P20 を回して記録と一致
    rec8 = _load(CD8_P20_REC)
    t0 = time.time()
    tmp8 = tempfile.mkdtemp(prefix="naming_fix_cd8_")
    p8_21 = os.path.join(tmp8, "cd8_P21.json")
    AC.main(["--docs", ",".join(rec8[u"書類"]), "--profile", "P21", "--out", p8_21])
    cd21 = _load(p8_21)
    p8_20 = os.path.join(tmp8, "cd8_P20.json")
    AC.main(["--docs", ",".join(rec8[u"書類"]), "--profile", "P20", "--out", p8_20])
    cd20 = _load(p8_20)
    diff8_20 = sorted(k for k in set(rec8) | set(cd20) if rec8.get(k) != cd20.get(k))
    t_cd8 = time.time() - t0

    # ---- M-C3: 旗を P20 でも真にすると M-C1(の rows の一致)が赤になる
    t0 = time.time()
    saved = V.PROFILES["P20"]
    V.PROFILES["P20"] = dataclasses.replace(saved, last_branch_cues=True)
    try:
        tmp3 = os.path.join(tempfile.mkdtemp(prefix="naming_fix_mc3_"), "gen_c_P20_flagged.json")
        AC.main(["--docs", ",".join(docs), "--profile", "P20", "--out", tmp3])
        mc3_rec = _load(tmp3)
    finally:
        V.PROFILES["P20"] = saved
    if V.PROFILES["P20"].last_branch_cues:
        raise SystemExit(u"**M-C3 の変異を戻せていない。止める**")
    mc3_diff_ids = [r["id"] for r, o in zip(mc3_rec["rows"], rows_rec) if jround(r) != o]
    mc3 = {u"変異": u"V.PROFILES['P20'] を last_branch_cues=True にして (ア) を回した(終わったら戻した)",
           u"rows が c0_p20 の記録と一致": mc3_rec["rows"] == rows_rec,
           u"違った注入の件数": len(mc3_diff_ids),
           u"違った注入の id が P21 の run で動いた id と同じ": mc3_diff_ids == [d[u"id"] for d in row_diff(rows20, rows21, "P20", "P21")],
           u"赤になった(= 一致しない)": mc3_rec["rows"] != rows_rec}
    mc3[u"当たり"] = mc3[u"赤になった(= 一致しない)"] and mc3[u"違った注入の id が P21 の run で動いた id と同じ"]
    t_mc3 = time.time() - t0

    # ================================================================ 数え直し
    s21, s20 = score(rows21), score(rows20)
    s_cd21, s_cd20 = score(cd21["rows"]), score(rec8["rows"])
    cross = {u"gen_c P20: 数え直し = c0_p20 の記録の採点の T5 の特定": (s20[u"T5 の特定(Core-P)"][u"分子"], s20[u"T5 の特定(Core-P)"][u"分母"])
             == (c0p20[u"**数え直し(P16 は C0 の記録の rows、P20 は今回の rows。同じ関数を当てた)**"][u"P20"][u"T5 の特定(Core-P)"][u"分子"],
                 c0p20[u"**数え直し(P16 は C0 の記録の rows、P20 は今回の rows。同じ関数を当てた)**"][u"P20"][u"T5 の特定(Core-P)"][u"分母"]),
             u"gen_c P21: 数え直し = (ア) の採点の T5 の特定": (s21[u"T5 の特定(Core-P)"][u"分子"], s21[u"T5 の特定(Core-P)"][u"分母"])
             == (p21["main"][u"採点"]["Core-P"][u"特定率(分母 = T5 の件数)"][u"分子"], p21["main"][u"採点"]["Core-P"][u"特定率(分母 = T5 の件数)"][u"分母"]),
             u"cd8 P21: 数え直し = (ア) の採点の T5 の特定": (s_cd21[u"T5 の特定(Core-P)"][u"分子"], s_cd21[u"T5 の特定(Core-P)"][u"分母"])
             == (cd21[u"採点"]["Core-P"][u"特定率(分母 = T5 の件数)"][u"分子"], cd21[u"採点"]["Core-P"][u"特定率(分母 = T5 の件数)"][u"分母"]),
             u"cd8 P20: 数え直し = 記録の採点の T5 の特定": (s_cd20[u"T5 の特定(Core-P)"][u"分子"], s_cd20[u"T5 の特定(Core-P)"][u"分母"])
             == (rec8[u"採点"]["Core-P"][u"特定率(分母 = T5 の件数)"][u"分子"], rec8[u"採点"]["Core-P"][u"特定率(分母 = T5 の件数)"][u"分母"])}
    cross[u"全部一致"] = all(cross.values())
    gc_diff = row_diff(rows20, rows21, "P20", "P21")
    cd_diff = row_diff(rec8["rows"], cd21["rows"], "P20", "P21")
    newly_spec = sorted(set(s21[u"T5 の特定の id"]) - set(s20[u"T5 の特定の id"]))
    lost_spec = sorted(set(s20[u"T5 の特定の id"]) - set(s21[u"T5 の特定の id"]))
    cd_newly = sorted(set(s_cd21[u"T5 の特定の id"]) - set(s_cd20[u"T5 の特定の id"]))
    cd_lost = sorted(set(s_cd20[u"T5 の特定の id"]) - set(s_cd21[u"T5 の特定の id"]))

    # ---- C0-1(製品の経路): gen_c 8 書類の state の合計
    st20, st21 = state_totals(c01_20), state_totals([{k: v for k, v in x.items() if k != "_out"} for x in p21["per"]])

    # ---- K-4
    by21 = {r["id"]: r for r in rows21}
    by20 = {r["id"]: r for r in rows20}
    k4_rows, gold_diff = [], []
    for x in c1[K45]["rows"]:
        o21, o20 = by21[x[u"注入の id"]], by20[x[u"注入の id"]]
        if PM.gold_of_row(o21) != x["gold"]:
            gold_diff.append(x[u"注入の id"])
        k4_rows.append({u"doc": x[u"doc"], u"注入の id": x[u"注入の id"], u"gold": x["gold"], u"gold の枠が次元つき": x[u"gold の枠が次元つき"],
                        u"席 A が特定": bool(x[u"席 A が特定"]), u"席 A の参照先": x[u"席 A の参照先"],
                        u"Core-P(P20)が特定": bool(cp(o20)[u"判定"][u"特定"]), u"Core-P(P20)の参照先": cp(o20)[u"参照先"],
                        u"Core-P(P21)が特定": bool(cp(o21)[u"判定"][u"特定"]), u"Core-P(P21)の参照先": cp(o21)[u"参照先"]})
    if gold_diff:
        raise SystemExit(u"**C1 の gold と P21 の gold が違う注入: %s。止める**" % gold_diff)
    kn = len(k4_rows)
    k_a = sum(1 for r in k4_rows if r[u"席 A が特定"])
    k_20 = sum(1 for r in k4_rows if r[u"Core-P(P20)が特定"])
    k_21 = sum(1 for r in k4_rows if r[u"Core-P(P21)が特定"])
    k4 = {u"T5 の行": kn, u"席 A の特定(C1 の記録。不変)": frac(k_a, kn), u"Core-P(P20)の特定": frac(k_20, kn),
          u"Core-P(P21)の特定": frac(k_21, kn),
          u"差 席 A − Core-P(P20)(pt)": round(pct(k_a, kn) - pct(k_20, kn), 1),
          u"差 席 A − Core-P(P21)(pt)": round(pct(k_a, kn) - pct(k_21, kn), 1),
          u"P20 の値の照合(c0_p20 の記録の K-4)": c0p20[u"**K-4 の再計算**"][u"Core-P(P20)の特定"] == frac(k_20, kn),
          u"P21 で特定が増えた行": [r[u"注入の id"] for r in k4_rows if r[u"Core-P(P21)が特定"] and not r[u"Core-P(P20)が特定"]],
          u"P21 で特定が減った行": [r[u"注入の id"] for r in k4_rows if r[u"Core-P(P20)が特定"] and not r[u"Core-P(P21)が特定"]],
          u"rows": k4_rows}

    # ---- C0-3
    t3_21, t3_20 = PM.c03_tally(p21["c03"]), PM.c03_tally(p20["c03"])

    # ---- 無改変の 40 書類
    groups, allv, missing = untouched_40()
    if missing:
        raise SystemExit(u"**キャッシュに無い書類: %s。止める(「無い」と記録して外す判断は人間に返す)**" % missing)
    per_doc, moved_rows, tot40 = run_untouched(allv, groups)
    ref12 = holdout_dump_reference()
    moved_pairs = collections.Counter((m[u"P20"][u"state"], m[u"P21"][u"state"]) for m in moved_rows)
    gen_ids = set(docs)
    moved_gen = [m for m in moved_rows if m[u"doc"] in gen_ids]
    gen_vm_to_pnf = sum(1 for m in moved_gen if m[u"P20"][u"state"] == "VALUE_MISMATCH" and m[u"P21"][u"state"] == "POINTER_NOT_FOUND")

    ed = engine_diff()
    esha = engine_sha()
    in_after = in_sha()

    # ================================================================ 予測 N-1〜N-12
    g_moved = tot40.get(u"GROUNDED の行で動いた", 0)
    n_moved = tot40.get(u"動いた", 0)
    only_vmpnf = all(m[u"P20"][u"state"] in ("VALUE_MISMATCH", "POINTER_NOT_FOUND") and m[u"P21"][u"state"] in ("VALUE_MISMATCH", "POINTER_NOT_FOUND")
                     for m in moved_rows)
    c01_moves = sum(1 for x20, x21 in zip(c01_20, p21["per"]) if x20[u"states"] != x21[u"states"])
    gen_state_delta = {k: st21.get(k, 0) - st20.get(k, 0) for k in sorted(set(st20) | set(st21))}
    wanted_new = ["S100Z4GF-T5-02", "S100Z4GF-T5-07", "S100Z4GF-T5-12", "S100Z4GF-T5-16", "S100Z4GF-T5-23"]
    f_files = ed[u"git diff HEAD --numstat -- core adapters"]
    pred = [
        {u"記号": "N-1", u"予測": u"gen_c T5 50 件: Core-P(P21)の特定 26 / 50(P20 21)、誤認定 3(P20 19)。増えた特定はちょうど Z4GF-T5-02・07・12・16・23",
         u"実測": {u"P21 の特定": s21[u"T5 の特定(Core-P)"], u"P20 の特定": s20[u"T5 の特定(Core-P)"],
                 u"P21 の誤認定": s21[u"T5 の誤認定(Core-P。別の参照先を名指した行)"], u"P20 の誤認定": s20[u"T5 の誤認定(Core-P。別の参照先を名指した行)"],
                 u"増えた特定の id": newly_spec, u"減った特定の id": lost_spec},
         u"当たり": (s21[u"T5 の特定(Core-P)"][u"分子"] == 26 and s21[u"T5 の特定(Core-P)"][u"分母"] == 50 and s20[u"T5 の特定(Core-P)"][u"分子"] == 21
                  and s21[u"T5 の誤認定(Core-P。別の参照先を名指した行)"] == 3 and s20[u"T5 の誤認定(Core-P。別の参照先を名指した行)"] == 19
                  and newly_spec == sorted(wanted_new) and lost_spec == [])},
        {u"記号": "N-2", u"予測": u"cd8 (ア) T5 64 件: 特定 46 / 64 のまま、誤認定 12 → 6",
         u"実測": {u"P21": {u"特定": s_cd21[u"T5 の特定(Core-P)"], u"誤認定": s_cd21[u"T5 の誤認定(Core-P。別の参照先を名指した行)"]},
                 u"P20(記録)": {u"特定": s_cd20[u"T5 の特定(Core-P)"], u"誤認定": s_cd20[u"T5 の誤認定(Core-P。別の参照先を名指した行)"]},
                 u"増えた特定の id": cd_newly, u"減った特定の id": cd_lost},
         u"当たり": (s_cd21[u"T5 の特定(Core-P)"][u"分子"] == 46 and s_cd21[u"T5 の特定(Core-P)"][u"分母"] == 64
                  and s_cd20[u"T5 の特定(Core-P)"][u"分子"] == 46 and s_cd20[u"T5 の誤認定(Core-P。別の参照先を名指した行)"] == 12
                  and s_cd21[u"T5 の誤認定(Core-P。別の参照先を名指した行)"] == 6)},
        {u"記号": "N-3", u"予測": u"T1 の通し gen_c 0 / 38・cd8 0 / 38。T3 の名指し gen_c 7 / 40・cd8 6 / 40(どちらも不変)",
         u"実測": {u"gen_c T1(P21)": s21[u"T1 の通し(Core-P。確認済みと言った)"], u"cd8 T1(P21)": s_cd21[u"T1 の通し(Core-P。確認済みと言った)"],
                 u"gen_c T3(P21)": s21[u"T3 の名指し(Core-P)"], u"cd8 T3(P21)": s_cd21[u"T3 の名指し(Core-P)"],
                 u"gen_c T3(P20)": s20[u"T3 の名指し(Core-P)"], u"cd8 T3(P20)": s_cd20[u"T3 の名指し(Core-P)"]},
         u"当たり": (s21[u"T1 の通し(Core-P。確認済みと言った)"][u"分子"] == 0 and s21[u"T1 の通し(Core-P。確認済みと言った)"][u"分母"] == 38
                  and s_cd21[u"T1 の通し(Core-P。確認済みと言った)"][u"分子"] == 0 and s_cd21[u"T1 の通し(Core-P。確認済みと言った)"][u"分母"] == 38
                  and s21[u"T3 の名指し(Core-P)"][u"分子"] == 7 and s21[u"T3 の名指し(Core-P)"][u"分母"] == 40
                  and s_cd21[u"T3 の名指し(Core-P)"][u"分子"] == 6 and s_cd21[u"T3 の名指し(Core-P)"][u"分母"] == 40)},
        {u"記号": "N-4", u"予測": u"無改変 40 書類: GROUNDED の行で state か参照先が動いた数 0。動いた行は VALUE_MISMATCH / POINTER_NOT_FOUND の参照先の移動だけで、合計 120〜220 行",
         u"実測": {u"書類数": len(allv), u"主張の延べ": tot40.get(u"claims"), u"GROUNDED の行で動いた": g_moved, u"動いた合計": n_moved,
                 u"動いた行の state の組": {"%s -> %s" % k: v for k, v in sorted(moved_pairs.items())},
                 u"動いた行は全部 VM / PNF の間": only_vmpnf,
                 u"型(機械的な読み)": {k: v for k, v in tot40.items() if k.startswith(u"型 ")}},
         u"当たり": g_moved == 0 and only_vmpnf and 120 <= n_moved <= 220},
        {u"記号": "N-5", u"予測": u"gen_c 8 書類の C0-1 の state の合計は P20 と P21 で同じ(GROUNDED 443・VM 194・UNVERIFIABLE 165・PNF 111)。VM → PNF に動く行は 0〜10 行",
         u"実測": {u"P20": st20, u"P21": st21, u"差(P21 − P20)": gen_state_delta, u"state の合計が動いた書類数": c01_moves,
                 u"gen_c 8 書類で VM -> PNF に動いた行": gen_vm_to_pnf,
                 u"gen_c 8 書類で動いた行の延べ": len(moved_gen)},
         u"当たり": (st20 == {"GROUNDED": 443, "POINTER_NOT_FOUND": 111, "UNVERIFIABLE": 165, "VALUE_MISMATCH": 194}
                  and gen_state_delta.get("GROUNDED", 0) == 0 and 0 <= gen_vm_to_pnf <= 10
                  and sum(abs(v) for v in gen_state_delta.values()) <= 20)},
        {u"記号": "N-6", u"予測": u"K-4 の 20 行: Core-P(P21)9〜12 / 20(P20 7)、席 A 16 / 20 との差 +20〜+35 pt",
         u"実測": {u"Core-P(P21)": k4[u"Core-P(P21)の特定"], u"Core-P(P20)": k4[u"Core-P(P20)の特定"],
                 u"席 A": k4[u"席 A の特定(C1 の記録。不変)"], u"差(pt)": k4[u"差 席 A − Core-P(P21)(pt)"]},
         u"当たり": 9 <= k_21 <= 12 and kn == 20 and 20 <= k4[u"差 席 A − Core-P(P21)(pt)"] <= 35 and k_20 == 7},
        {u"記号": "N-7", u"予測": u"C0-3: Core-P(P21)の参照先で engine が GROUNDED にする件数 0",
         u"実測": {u"GROUNDED": t3_21[u"**GROUNDED(誤りを通した)**"], u"分母(engine を通せた行)": t3_21[u"engine を通せた行(分母)"],
                 u"Core-P が名指した注入の行": t3_21[u"Core-P が名指した注入の行"], u"P20": t3_20[u"**GROUNDED(誤りを通した)**"]},
         u"当たり": t3_21[u"**GROUNDED(誤りを通した)**"][u"件数"] == 0 and t3_21[u"engine を通せた行(分母)"] > 0},
        {u"記号": "N-8", u"予測": u"対照 M-C1 全欄一致・M-C2 緑・M-C3 赤",
         u"実測": {u"M-C1": mc1[u"当たり"], u"M-C3": mc3[u"当たり"], u"M-C2": u"この script では測らない(pytest を別に走らせて結果文書に書く)",
                 u"補助: cd8 の P20 が記録に全欄一致": diff8_20 == []},
         u"当たり": None, u"この script が測った部分": mc1[u"当たり"] and mc3[u"当たり"]},
        {u"記号": "N-9", u"予測": u"engine の差分: recipes.py は最後の枝の中だけ(+40 行以下)、vocabulary.py は field 1 つ + P21 の 1 行 + PROFILES の登録。core/py 0 行。instance.py・extract.py 0 行",
         u"実測": ed,
         u"当たり": (sorted(f_files) == ["adapters/xbrl/recipes.py", "adapters/xbrl/vocabulary.py"]
                  and f_files["adapters/xbrl/recipes.py"][1] == 0 and f_files["adapters/xbrl/recipes.py"][0] <= 40
                  and ed[u"recipes.py の差分は挿入 1 か所だけ(HEAD の行は 1 つも変えていない)"] and ed[u"挿入先の関数"] == "def _direct_value_claim"
                  and ed[u"挿入の直前の HEAD の行"] == 'claim["reason"] = "no_element(no prior2 for prior-year diff)" / return'
                  and ed[u"core/ の差分の file"] == [] and ed[u"instance.py・extract.py の差分"] == [])},
        {u"記号": "N-10", u"予測": u"mutations.json の old の字は全部そのまま file に 1 回在る(test_mutations 緑)",
         u"実測": u"この script では測らない(pytest tests/adapters/xbrl/test_mutations.py を別に走らせて結果文書に書く)", u"当たり": None},
        {u"記号": "N-11", u"予測": u"§1 の門に遷移の字を足し、pytest -q tests/measure の赤は axis3 の test_9 だけ",
         u"実測": u"この script では測らない(pytest を別に走らせて結果文書に書く)", u"当たり": None},
        {u"記号": "N-12", u"予測": u"段 2(既定 = P21): test_p16_matches_the_holdout_dumps で動く行は S100Z4N9 の 4 行と S100Z39P の 1 行の 5 行だけ、全部 VALUE_MISMATCH の参照先の移動",
         u"実測": u"段 2 の予測なので段 1 では判定しない。参考(判定に使わない): " + json.dumps({d: {p: ref12[d][p][u"違った行"] for p in ("P20", "P21")} for d in UNUSED_2}, ensure_ascii=False),
         u"当たり": None},
    ]

    rec = {
        "seal": SEAL, "step": u"**名指しの直し(P21)の段 1 の測定。0 USD・席を呼ばない・通信しない。engine は実装済み(この script は測るだけ)。C0・C1・cd8 の記録と答えは読むだけ**",
        "profile": "P21(対照 P20)", u"環境": env, u"engine の差分": ed, u"engine の sha": esha,
        u"材料": {u"gen_c 8 書類": docs, u"draw": "fixtures/xbrl/gen_c/draw_2026-10-20.json", u"cd8 の (ア) 8 書類": rec8[u"書類"],
                u"注入の種": {"file": "measure/SEED.json", "sealed_on": seed_meta.get("sealed_on")}},
        u"入力の sha256(前後で変えていない)": {u"前": in_before, u"後": in_after, u"一致": in_before == in_after},
        u"無改変の 40 書類": {u"群": {n: l for n, l in groups}, u"id の一覧": allv, u"キャッシュに無い書類": missing,
                         u"開発 14 の出どころ": u"tests/adapters/xbrl/test_verify_entry.py の ROBUSTNESS_P16 の key",
                         u"未使用 2 の出どころ": u"fixtures/xbrl/holdout_p16/commander_only の dump_P16_<doc>.json の書類(HOLDOUT_DOCS)",
                         u"text": u"None(書類自身の本文。製品の経路。C0-1 と同じ)",
                         u"集計": tot40, u"書類ごと": per_doc, u"動いた行(1 件ずつ)": moved_rows,
                         u"参考(判定に使わない): 未使用 2 書類を test_p16_matches_the_holdout_dumps と同じ照合に当てた": ref12},
        u"gen_c (ア) P21 の採点": s21, u"gen_c (ア) P20 の採点": s20,
        u"gen_c (ア) の main() の出力(P21)": {k: v for k, v in p21["main"].items() if k != "rows"},
        u"gen_c (ア) rows(P21)": p21["main"]["rows"],
        u"gen_c P20 と P21 で rows が違った注入(1 件ずつ)": gc_diff,
        u"cd8 (ア) P21 の採点": s_cd21, u"cd8 (ア) P20(記録)の採点": s_cd20,
        u"cd8 (ア) の main() の出力(P21)": {k: v for k, v in cd21.items() if k != "rows"},
        u"cd8 (ア) rows(P21)": cd21["rows"],
        u"cd8 P20 と P21 で rows が違った注入(1 件ずつ)": cd_diff,
        u"数え直しの照合": cross,
        u"C0-1(製品の経路)gen_c 8 書類の state の合計": {u"P20": st20, u"P21": st21, u"差(P21 − P20)": gen_state_delta},
        u"C0-1 書類ごと(P21)": [{k: v for k, v in x.items() if k != "_out"} for x in p21["per"]],
        u"**K-4 の再計算**": k4,
        u"**C0-3 engine を Core-P(P21)の参照先に当てた**": {u"集計": t3_21, u"rows": p21["c03"]},
        u"参考: C0-3 の集計(P20。今回の P20 の run)": t3_20,
        u"補助: C-2(P21。無改変の主張の state が動いたか。封の外)": {u"一意に対になった主張(延べ)": sum(x[u"一意に対になった主張"] for x in p21["c2"]),
                                                  u"判定が動いた(延べ)": sum(x[u"判定が動いた"] for x in p21["c2"])},
        u"**対照 M-C1**": mc1, u"**対照 M-C3**": mc3,
        u"補助: cd8 の (ア) を P20 で回すと記録に全欄一致": {u"違った欄": diff8_20, u"当たり": diff8_20 == []},
        u"**予測 N-1〜N-12**": pred,
        u"所要秒": {u"gen_c P21": p21[u"秒"], u"gen_c P20": p20[u"秒"], u"cd8 (ア) P21 + P20": round(t_cd8, 1), u"M-C3": round(t_mc3, 1),
                u"全体": round(time.time() - t_start, 1)},
        u"limits": [u"8 書類 1 回である。合格線は作らない。新しい標本での汎化は測っていない(封 §4)。",
                    u"無改変 40 書類に正解の参照先は無い(GROUNDED の不動 = 退行なし、であって正しさの証明ではない)。",
                    u"特定が増えるのは F1′ の 5 件だけ。F2′・F3b は誤った 1 本の名指しをやめる直しで、特定率は 26 / 50 止まり。",
                    u"M-C2・N-10・N-11 は pytest を別に走らせた結果で、この記録の外(結果文書に書く)。",
                    u"(ア) の脚注: 正解は identified_sites(値の一意性 + 単位・ラベル)で作られ、正解そのものが誤りうる。"],
    }
    os.makedirs(FX, exist_ok=True)
    with io.open(a.out, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(u"=== 名指しの直し(P21)段 1(0 USD)===")
    for p in pred:
        print(u"  %-5s %s" % (p[u"記号"], {True: u"当たり", False: u"**外れ**", None: u"(別に判定)"}[p[u"当たり"]]),
              json.dumps(p[u"実測"], ensure_ascii=False)[:260])
    print(u"M-C1 %s / M-C3 %s / cd8 の P20 一致 %s / 数え直し %s" % (mc1[u"当たり"], mc3[u"当たり"], diff8_20 == [], cross[u"全部一致"]))
    print(u"入力の sha256 前後一致:", in_before == in_after)
    print(u"所要:", rec[u"所要秒"])
    print("->", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
