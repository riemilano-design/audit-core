# -*- coding: utf-8 -*-
u"""汎化 C の段 C1-B(封 `docs/XBRL_GENERALITY_SEAL_2026-10-20.md` 追記 1 の A-2〜A-6)。

**cd8 の材料・採点の module を import して使い(書き直さない)、入出力を ``fixtures/xbrl/gen_c/`` に向ける。**
席(LLM API)は 1 回も呼ばない。通信しない。``core/``・``adapters/`` は 0 行。

  --stage material  8 書類の材料(task file は repo の外 = ``$TMPDIR/gen_c1/tasks/``)と記録
                    ``fixtures/xbrl/gen_c/material_2026-10-20.json``。対照 K-C1〜K-C3 を記録の ``対照`` に書く。
  --stage score     ``fixtures/xbrl/gen_c/seat_answers/`` を読み、cd8 と同じ関数で A / C′ / D′ / D″ を採点して
                    ``fixtures/xbrl/gen_c/c1_2026-10-20.json`` に書く。**答えが 8 件そろっていなければ止まる**。
                    ``--with-engine`` を付けると C1-3 も同じ file の ``C1-3`` に入れる。
  --stage engine    C1-3。席 A が参照先を名指した注入の行で、その参照先を
                    ``verify_external(spec, period_pair=True)`` の ``pointers`` に渡して state を数える。
                    ``--answers`` ``--material`` ``--out`` を取る(cd8 の答え + cd8 の材料でも動く)。

**数を見る前に決めた読み方(迷った所。封の字で 1 通りに決まらなかった所)**

  * task file の置き場: cd8 の材料 module は ``TMP`` の 1 か所に「task file」と「(ア) の中間 file(本文・refs)」を
    書く。席が自分の task 以外を読めないよう、中間 file は ``$TMPDIR/gen_c1/work/``、task file は
    ``$TMPDIR/gen_c1/tasks/`` に分け、``work`` から ``tasks`` へ**コピー**して sha256 が記録と一致することを確かめる
    (``tasks/`` には task file 8 本だけが在る)。
  * module の差し替え: ``DRAW``・``TMP``・``OUT``(材料)/ ``MAT``・``OUT``(採点)は module の global で、
    ``main`` がそれを読む。差し替えが呼び出し先に届いたことを、``work/<doc>.original.txt`` の実在と
    出力 file の実在で確かめる。
  * トークン見込み: cd8 の下見(``fixtures/xbrl/cd8/cost_breakdown_2026-10-17.json``)の 2 つの見方を**平均せず両方**書く。
    (傾き)席の往復 + 傾き × 字数、(素朴)ASCII は 4 字で 1・日本語は 1 字で 1 の材料だけ。
  * C1-3 の spec の (値, 単位, 符号): C0-3 と同じ(cd8 の材料 ``build_rows`` の注入行の 値・単位・抜粋。率は
    ``sign_from_text``)。行は本文から**再構成**し、再構成した task の sha256 が材料の記録と一致しなければ止まる。
  * 席が参照先を名指した行: ``seat_row`` が欠けにしなかった行のうち参照先が ``なし`` でない行。席の判定語
    (確認済み / 誤りが在る / 判定できない)は問わない。語ごとの内訳を併記する。

    cd audit-core
    TMPDIR=<scratchpad> python3 measure/xbrl_gen_c1_2026-10-20.py --stage material
"""
import argparse
import collections
import copy
import hashlib
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, HERE)

import audit_core as core                                # noqa: E402
from adapters.xbrl import edinet as ED                    # noqa: E402
from adapters.xbrl import holds as H                      # noqa: E402
from adapters.xbrl import instance as I                   # noqa: E402
from adapters.xbrl import registry_setup as RS            # noqa: E402
from adapters.xbrl import verify_external as VE           # noqa: E402


def _mod(rel, name):
    sp = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


#: cd8 の材料・採点・C0 の実物。**書き直さない**。
MB = _mod("measure/xbrl_cd_material_2026-10-17.py", "cd_material_for_gen_c1")
SC = _mod("measure/xbrl_cd_score_2026-10-17.py", "cd_score_for_gen_c1")
G0 = _mod("measure/xbrl_gen_c_2026-10-20.py", "gen_c_for_gen_c1")

SEAL = "docs/XBRL_GENERALITY_SEAL_2026-10-20.md"
GEN = os.path.join(ROOT, "fixtures", "xbrl", "gen_c")
CD8 = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
GEN_DRAW = os.path.join(GEN, "draw_2026-10-20.json")
GEN_MAT = os.path.join(GEN, "material_2026-10-20.json")
GEN_ANS = os.path.join(GEN, "seat_answers")
GEN_C1 = os.path.join(GEN, "c1_2026-10-20.json")
CD8_MAT = os.path.join(CD8, "material_2026-10-17.json")
CD8_SCORE = os.path.join(CD8, "score_2026-10-17.json")
CD8_ANS = os.path.join(CD8, "seat_answers")
CD8_COST = os.path.join(CD8, "cost_breakdown_2026-10-17.json")
CD8_DRAW = os.path.join(CD8, "draw_2026-10-17.json")

#: 人間が決めた数。**字で留める**(定数から作らない)。
PROMPT_SHA = "4c63022014736bb25de0c3808d227c06bbfcd72856aaf3a2e2dfdf31cb85c0fb"
PROMPT_CHARS = 411
#: spec §2 の「見せないもの」(字で持つ。MB.BANNED はこの上位集合)
SPEC_BANNED = (u"注入", u"正解", u"Core", u"engine", u"GROUNDED", u"pointer", u"T1", u"T3", u"T5")
#: 封 A-4 K-1
K1_T5_RANGE = (16, 20)
#: K-C2 の期待(cd8 の A。score_2026-10-17.json から読んだ数を字で留める)
KC2_EXPECT = {u"誤認定": (8, 85), u"見逃し": (0, 64), u"正しい参照先の特定": (35, 50), u"保留": (107, 192)}


def _load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def _dump(rec, p):
    with io.open(p, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    with io.open(p, "rb") as fh:
        return sha_bytes(fh.read())


def pct(a, b):
    return None if not b else round(100.0 * a / b, 1)


def base_dirs():
    tmp = os.environ.get("TMPDIR")
    if not tmp:
        raise SystemExit(u"**TMPDIR が未設定。task file を repo の外に置くため、scratchpad を TMPDIR に向ける**")
    root = os.path.realpath(os.path.join(tmp, "gen_c1"))
    if os.path.realpath(root).startswith(os.path.realpath(ROOT) + os.sep):
        raise SystemExit(u"**task file の置き場が repo の中。止める: %s**" % root)
    return root, os.path.join(root, "work"), os.path.join(root, "tasks")


def no_keys():
    env = G0.env_check()
    if env[u"設定されている key の数"] != 0:
        raise SystemExit(u"**LLM の API key が設定されている。席を呼ばない段なので止める**")
    return env


# ------------------------------------------------------------------ 材料(cd8 の module をそのまま回す)
def run_material(draw_path, work, out_path, docs=None):
    u"""cd8 の ``MB.main`` を、入出力だけ差し替えて回す。差し替えが届いたことを path の実在で確かめる。"""
    old = (MB.DRAW, MB.TMP, MB.OUT)
    MB.DRAW, MB.TMP, MB.OUT = draw_path, work, out_path
    try:
        argv = ["--out", out_path]
        if docs:
            argv = ["--docs", ",".join(docs)] + argv
        MB.main(argv)
    finally:
        MB.DRAW, MB.TMP, MB.OUT = old
    if not os.path.exists(out_path):
        raise SystemExit(u"**材料の出力が出ていない: %s(差し替えが届いていない)**" % out_path)
    rec = _load(out_path)
    for p in rec[u"書類ごと"]:
        d = p["docID"]
        for f in ("%s_task.txt" % d, "%s.original.txt" % d, "%s.reference_numbers.json" % d):
            if not os.path.exists(os.path.join(work, f)):
                raise SystemExit(u"**差し替えた TMP に file が無い: %s/%s**" % (work, f))
    return rec


def token_views(chars, text):
    u"""トークンの 2 つの見方。**平均しない**(cd8 の下見 §5-3 と同じ)。"""
    c = _load(CD8_COST)[u"2 1 便のトークンの分け方"]
    s1, s2 = c[u"過去の 2 点"]
    slope = float(s2[u"トークン(実測)"] - s1[u"トークン(実測)"]) / (s2[u"材料の字数"] - s1[u"材料の字数"])
    loop = s1[u"トークン(実測)"] - slope * s1[u"材料の字数"]
    a = sum(1 for ch in text if ord(ch) < 128)
    naive = a / 4.0 + (len(text) - a)
    return {u"傾き(席の往復 + 傾き × 字数)": int(loop + slope * chars),
            u"素朴(材料だけ。ASCII は 4 字で 1・日本語は 1 字で 1。席の往復を含まない)": int(naive)}


def check_banned_disk(path):
    blob = io.open(path, encoding="utf-8").read()
    return {w: blob.count(w) for w in SPEC_BANNED if w in blob}


def k1_table(rec, tasks_dir):
    rows, tot = [], collections.Counter()
    for p in rec[u"書類ごと"]:
        d = p["docID"]
        pre = p[u"席の前に出せる分"]
        t5 = sum(1 for v in pre.values() if (v[u"正解"] or {}).get(u"種類") == u"参照先が在る")
        t5_inj = p[u"注入"][u"型の内訳"].get("T5_COINCIDENT", 0)
        path = os.path.join(tasks_dir, "%s_task.txt" % d)
        text = io.open(path, encoding="utf-8").read()
        raw = io.open(path, "rb").read()
        banned = check_banned_disk(path)
        tok = token_views(len(text), text)
        row = {u"docID": d, u"注入の型ごとの件数": p[u"注入"][u"型の内訳"],
               u"注入の件数": p[u"注入"][u"件数"], u"注入が 8 件そろったか": p[u"注入"][u"**8 件そろったか**"],
               u"T5 の作れる site(cd8 の script が数えた)": p[u"注入"][u"型ごと"]["T5_COINCIDENT"][u"作れる site"],
               u"行の合計": p[u"行"][u"合計"], u"注入の行": p[u"行"][u"注入の行"],
               u"無改変の行": p[u"行"][u"無改変の行"], u"無改変の候補の総数": p[u"行"][u"無改変の候補の総数"],
               u"**24 行そろったか**": p[u"行"][u"**24 行そろったか**"],
               u"T5 の行(軸B の分母)": t5, u"T5 の行 = T5 を注入した行": t5 == t5_inj,
               u"見せない字(材料 script の検査)": p[u"**見せない字**"][u"見つかった"],
               u"見せない字(task file を読み直して spec §2 の 9 語)": banned,
               u"**見せない字 0 件か**": (not p[u"**見せない字**"][u"見つかった"]) and not banned,
               u"task の字数": len(text), u"task の字数(記録)": p[u"材料"][u"字数"],
               u"task の sha256": sha_bytes(raw), u"task の sha256(記録)": p[u"材料"][u"sha256"],
               u"task が記録と一致": sha_bytes(raw) == p[u"材料"][u"sha256"] and len(text) == p[u"材料"][u"字数"],
               u"トークン見込み": tok,
               u"席の前に出せる分": {u"行": len(pre), u"Core": sum(1 for v in pre.values() if v.get(u"Core") is not None),
                              u"D′": sum(1 for v in pre.values() if v.get(u"D′") is not None),
                              u"D″": sum(1 for v in pre.values() if v.get(u"D″") is not None)},
               u"他の行への影響(判定が動いた)": p[u"**他の行への影響の検査**"][u"**判定が動いた**"]}
        rows.append(row)
        tot[u"行"] += row[u"行の合計"]
        tot[u"注入"] += row[u"注入の件数"]
        tot[u"T5 の行"] += t5
        tot[u"task の字数"] += row[u"task の字数"]
        tot[u"トークン見込み(傾き)"] += tok[u"傾き(席の往復 + 傾き × 字数)"]
        tot[u"トークン見込み(素朴)"] += tok[u"素朴(材料だけ。ASCII は 4 字で 1・日本語は 1 字で 1。席の往復を含まない)"]
        for k, v in p[u"注入"][u"型の内訳"].items():
            tot[u"型 " + k] += v
    lo, hi = K1_T5_RANGE
    summary = {u"書類": len(rows), u"合計": dict(tot),
               u"T5 の行の合計": tot[u"T5 の行"],
               u"T5 が 1 件以上の書類": sorted(r[u"docID"] for r in rows if r[u"T5 の行(軸B の分母)"] >= 1),
               u"K-1 の各欄(機械の比較。意味づけは結果の席)": {
                   u"8 書類とも 24 行そろった": all(r[u"**24 行そろったか**"] for r in rows),
                   u"8 書類とも注入 8 件そろった": all(r[u"注入が 8 件そろったか"] for r in rows),
                   u"見せない字 0 件(8 書類とも)": all(r[u"**見せない字 0 件か**"] for r in rows),
                   u"問いの sha256 が一致": rec[u"問いの sha256"] == PROMPT_SHA,
                   u"問いが 411 字": rec[u"問いの字数"] == PROMPT_CHARS,
                   u"task が記録の sha256・字数と一致(8 書類とも)": all(r[u"task が記録と一致"] for r in rows),
                   u"T5 の行の合計が %d〜%d" % (lo, hi): lo <= tot[u"T5 の行"] <= hi,
                   u"T5 の行は 3 書類": sum(1 for r in rows if r[u"T5 の行(軸B の分母)"] >= 1) == 3},
               u"分母の注記": u"軸B(参照先の正しさ)の分母は T5 の行だけ。cd8 は 50 行・7 書類"}
    return rows, summary


def banned_control(tasks_dir):
    u"""見せない字の検査が**効いている**ことを、故障(語を 1 つ混ぜた task)を作って当てて確かめる。1 回に 1 語。"""
    d0 = sorted(f for f in os.listdir(tasks_dir) if f.endswith("_task.txt"))[0]
    blob = io.open(os.path.join(tasks_dir, d0), encoding="utf-8").read()
    res = []
    for w in SPEC_BANNED:
        found = MB.check_banned(blob + w)
        res.append({u"混ぜた語": w, u"MB.check_banned が見つけた": sorted(found), u"当たった": w in found})
    return {u"混ぜる前の task": MB.check_banned(blob), u"語ごと": res,
            u"全語で当たった": all(r[u"当たった"] for r in res)}


# ------------------------------------------------------------------ 対照
def score_run(mat_path, ans_dir, out_path):
    old = (SC.MAT, SC.OUT)
    SC.MAT, SC.OUT = mat_path, out_path
    try:
        SC.main(["--answers", ans_dir, "--out", out_path])
    finally:
        SC.MAT, SC.OUT = old
    if not os.path.exists(out_path):
        raise SystemExit(u"**採点の出力が出ていない: %s(差し替えが届いていない)**" % out_path)
    return _load(out_path)


def kc1(work_tmp):
    u"""K-C1: 材料 script を cd8 の 8 書類で一時 file に向けて回し、記録と照合。"""
    tmp_out = os.path.join(work_tmp, "kc1_material_cd8.json")
    work = os.path.join(work_tmp, "kc1_work")
    new = run_material(CD8_DRAW, work, tmp_out)
    old = _load(CD8_MAT)
    per = []
    for po, pn in zip(old[u"書類ごと"], new[u"書類ごと"]):
        per.append({u"docID": po["docID"], u"docID が同じ": po["docID"] == pn["docID"],
                    u"注入の型ごとの件数": [po[u"注入"][u"型の内訳"], pn[u"注入"][u"型の内訳"]],
                    u"型ごとの件数が一致": po[u"注入"][u"型の内訳"] == pn[u"注入"][u"型の内訳"],
                    u"行の合計": [po[u"行"][u"合計"], pn[u"行"][u"合計"]],
                    u"行の合計が一致": po[u"行"][u"合計"] == pn[u"行"][u"合計"],
                    u"task の sha256 が一致(追加の照合)": po[u"材料"][u"sha256"] == pn[u"材料"][u"sha256"],
                    u"席の前に出せる分が一致(追加の照合)": po[u"席の前に出せる分"] == pn[u"席の前に出せる分"]})
    ok = (len(old[u"書類ごと"]) == len(new[u"書類ごと"]) == 8
          and all(r[u"docID が同じ"] and r[u"型ごとの件数が一致"] and r[u"行の合計が一致"] for r in per)
          and old[u"問いの sha256"] == new[u"問いの sha256"]
          and old[u"合計"] == new[u"合計"])
    return {u"中身": u"材料 script を cd8 の 8 書類で一時 file に向けて回し、material_2026-10-17.json と照合",
            u"期待": u"全欄一致", u"書類ごと": per,
            u"問いの sha256": [old[u"問いの sha256"], new[u"問いの sha256"]],
            u"問いの sha256 が一致": old[u"問いの sha256"] == new[u"問いの sha256"],
            u"合計": [old[u"合計"], new[u"合計"]], u"合計が一致": old[u"合計"] == new[u"合計"],
            u"task の sha256 が 8 書類とも一致(追加)": all(r[u"task の sha256 が一致(追加の照合)"] for r in per),
            u"席の前に出せる分が 8 書類とも一致(追加)": all(r[u"席の前に出せる分が一致(追加の照合)"] for r in per),
            u"**一致したか**": ok}


def kc2(work_tmp):
    u"""K-C2: 採点の関数を cd8 の ``seat_answers/`` に当て、``score_2026-10-17.json`` の A を再現。"""
    out = os.path.join(work_tmp, "kc2_score_cd8.json")
    new = score_run(CD8_MAT, CD8_ANS, out)
    old = _load(CD8_SCORE)
    a = new[u"採点"]["A"]
    got = {k: (a[k][u"分子"], [v for kk, v in a[k].items() if kk.startswith(u"分母")][0]) for k in KC2_EXPECT}
    gaps = new[u"**欠けは 4 腕で同数**"]
    return {u"中身": u"採点の関数を cd8 の seat_answers に当て、score_2026-10-17.json の A を再現",
            u"期待": u"A: 誤認定 8/85・見逃し 0/64・特定 35/50・保留 107/192",
            u"A(今回)": {k: list(v) for k, v in got.items()},
            u"A(字で留めた期待)": {k: list(v) for k, v in KC2_EXPECT.items()},
            u"A の 4 つの数が期待と一致": {k: got[k] == KC2_EXPECT[k] for k in KC2_EXPECT},
            u"A の 4 つの数が score_2026-10-17.json の A と一致": all(
                (a[k][u"分子"] == old[u"採点"]["A"][k][u"分子"]) for k in KC2_EXPECT),
            u"採点(4 腕すべて)が score_2026-10-17.json と一致(追加)": new[u"採点"] == old[u"採点"],
            u"rows が一致(追加)": new["rows"] == old["rows"],
            u"欠け(4 腕)": gaps,
            u"**一致したか**": got == KC2_EXPECT and new[u"採点"] == old[u"採点"]}


def kc3(work_tmp):
    u"""K-C3: 答えの json から 1 行を消した(未回答)入力で、4 腕すべて ``欠け`` が 1。1 回に 1 件。"""
    d = os.path.join(work_tmp, "kc3_answers")
    if os.path.exists(d):
        shutil.rmtree(d)
    shutil.copytree(CD8_ANS, d)
    doc = sorted(f for f in os.listdir(d))[0].replace("_answer.json", "")
    path = os.path.join(d, "%s_answer.json" % doc)
    ans = _load(path)
    dropped = ans[2]["id"]
    ans = [r for r in ans if r["id"] != dropped]
    _dump(ans, path)
    out = os.path.join(work_tmp, "kc3_score.json")
    new = score_run(CD8_MAT, d, out)
    gaps = new[u"**欠けは 4 腕で同数**"]
    return {u"中身": u"cd8 の答えの 1 行(%s の %s)を消した入力を採点器に食わせる" % (doc, dropped),
            u"期待": u"4 腕すべて 欠け = 1", u"欠け(4 腕)": gaps,
            u"**一致したか**": all(gaps.get(k) == 1 for k in ("A", "C′", "D′", "D″")) and len(gaps) == 4,
            u"消した行の席の欄": [r for r in new["rows"] if r[u"doc"] == doc and r[u"id"] == dropped][0][u"席"]
            if [r for r in new["rows"] if r[u"doc"] == doc and r[u"id"] == dropped] else None,
            u"note": u"行を消すと採点器は ``行が無い`` を欠けにする。行の総数は 192 のまま(材料の行が正本)"}


# ------------------------------------------------------------------ C1-3(engine)
def rebuild_rows(doc, work, seed, mat_doc):
    u"""材料の記録と同じ行を本文から再構成する。task の sha256 が一致しなければ止まる。"""
    old, MB.A1.TMP = MB.A1.TMP, work
    try:
        text, refs = MB.A1.material(doc)
    finally:
        MB.A1.TMP = old
    chosen, _counts = MB.pick_injections(text, refs, seed, doc)
    tampered, placements = MB.IJ.apply_edits(text, chosen)
    rows, _n = MB.build_rows(tampered, chosen, placements)
    task = MB.seat_text(rows, tampered, refs)
    if hashlib.sha256(task.encode("utf-8")).hexdigest() != mat_doc[u"材料"][u"sha256"]:
        raise SystemExit(u"**再構成した task の sha256 が材料の記録と合わない: %s。止める**" % doc)
    if sorted(r["id"] for r in rows) != sorted(mat_doc[u"席の前に出せる分"]):
        raise SystemExit(u"**再構成した行の id が材料の記録と合わない: %s。止める**" % doc)
    return rows, chosen


def engine_stage(mat_path, ans_dir, work):
    no_keys()
    mat = _load(mat_path)
    seed, _meta = MB.IJ.verify_seed_sealed(MB.SEED_FILE)
    registry = RS.register_all(core.Registry.default())
    items, per_doc = [], {}
    for p in mat[u"書類ごと"]:
        doc = p["docID"]
        path = os.path.join(ans_dir, "%s_answer.json" % doc)
        if not os.path.exists(path):
            raise SystemExit(u"**答えが無い: %s。止める**" % path)
        ans = _load(path)
        by_id = {}
        for r in (ans if isinstance(ans, list) else ans.get(u"answers", [])):
            if isinstance(r, dict) and r.get("id"):
                by_id[str(r["id"]).strip()] = r
        rows, chosen = rebuild_rows(doc, work, seed, p)
        inj_by_id = {c["id"]: c for c in chosen}
        zb = io.open(ED.cache_path(doc), "rb").read()
        inst = I.load_instance(zb)
        facts, contexts = inst["facts"], inst["contexts"]
        by_loc, by_norm = G0._mk_index(facts)
        n_inj = n_named = 0
        for m in rows:
            if not m.get(u"**注入**"):
                continue
            n_inj += 1
            inj = inj_by_id[m[u"**注入**"]]
            seat = SC.seat_row(by_id.get(m["id"]))
            if seat[u"判定"] == SC.MISSING or seat[u"参照先"] is None:
                continue
            n_named += 1
            raw = str(by_id[m["id"]][u"参照先"]).strip()
            f, how = G0._resolve(by_loc, by_norm, raw)
            loc = ("%s@%s" % (f["name"], f["context"])) if f else G0._loc_of(raw)
            unit, val = m[u"単位"], m[u"値"]
            is_ratio = unit in VE.RATIO_UNITS
            sign = G0.R1.sign_from_text(m[u"抜粋"], m[u"数の字面"]) if is_ratio else None
            spec = {"kind": "ratio_change" if is_ratio else "single_value", "value": val, "unit": unit,
                    "pointers": [loc]}
            if is_ratio:
                spec["sign"] = sign
            cid = "C13-%s-%s" % (doc, m["id"])
            on = VE.verify_external(spec, facts, contexts, registry, claim_id=cid, period_pair=True)
            off = VE.verify_external(spec, facts, contexts, registry, claim_id=cid, period_pair=False)
            tol = VE.tol_of(unit)
            if f is not None:
                u_fire, ucc, ufc = H.unit_mismatch(unit, f)
                d_sibs = H.dimension_siblings(facts, f, tol)
                p_sibs = H.period_siblings(facts, f, tol)
            else:
                u_fire, ucc, ufc, d_sibs, p_sibs = False, None, None, [], []
            gold = p[u"席の前に出せる分"][m["id"]][u"正解"]
            # 対照: 同じ参照先に「その fact 自身の値」を当てれば GROUNDED になるはず(0 件が道具の欠陥でないことを示す)
            ctrl = None
            if f is not None and f.get("value") is not None and not is_ratio:
                scale = float(G0.V_UNIT_SCALE.get(unit, 1))
                csp = {"kind": "single_value", "value": float(f["value"]) / scale, "unit": unit, "pointers": [loc]}
                co = VE.verify_external(csp, facts, contexts, registry, claim_id=cid + "-ctl", period_pair=True)
                ctrl = {u"state": co["state"], u"reason": co["reason"], u"held": co["held"]}
            items.append({
                u"対照(その fact 自身の値を同じ参照先に当てた)": ctrl,
                u"doc": doc, u"id": m["id"], u"注入の id": inj["id"], u"型": inj["type"], u"正解": gold,
                u"席の判定": seat[u"判定"], u"席の参照先(正規化)": seat[u"参照先"], u"席の参照先(原文)": raw,
                u"参照先の解き方": how,
                u"席の参照先が正解": (gold or {}).get(u"正解") == seat[u"参照先"] if (gold or {}).get(u"種類") == u"参照先が在る" else None,
                u"材料の値": val, u"材料の単位": unit, u"数の字面": m[u"数の字面"], u"spec の kind": spec["kind"],
                u"符号": sign, u"参照先の fact の単位": (f or {}).get("unit"),
                u"参照先の fact の値": (f or {}).get("value"),
                u"engine の state": on["state"], u"engine の reason": on["reason"],
                u"engine の recomputed": on["recomputed"], u"held(製品の経路)": on["held"],
                u"hold_rules(製品の経路)": list(on["hold_rules"]), u"derived_pointers": on["derived_pointers"],
                u"direction_checked": on["direction_checked"],
                u"露出 U(単位の種類が違う)": bool(u_fire), u"露出 U の明細": [ucc, ufc],
                u"露出 (d)(同額の次元兄弟)": bool(d_sibs), u"露出 P(同額の期間兄弟)": bool(p_sibs),
                u"PP の行": is_ratio,
                u"engine(PP あり)": G0.keyed(on), u"engine(PP なし)": G0.keyed(off)})
        per_doc[doc] = {u"注入の行": n_inj, u"席 A が参照先を名指した注入の行": n_named}
    t = G0.tally_c03(items)
    words = collections.Counter(x[u"席の判定"] for x in items)
    unresolved = [x[u"id"] for x in items if x[u"参照先の解き方"] == u"解けない"]
    pp_diff = [x[u"id"] for x in items if x[u"engine(PP あり)"] != x[u"engine(PP なし)"]]
    n = len(items)
    return {u"step": u"C1-3(0 USD。席は呼ばない)。席 A が参照先を名指した注入の行を engine に当てた",
            u"材料": os.path.relpath(mat_path, ROOT), u"書類ごと": per_doc,
            u"注入の行": sum(v[u"注入の行"] for v in per_doc.values()),
            u"席 A が参照先を名指した注入の行(分母)": n,
            u"分母の出どころ": u"seat_row が欠けにせず、参照先が なし でない注入の行。席の判定語は問わない",
            u"席の判定語ごと": dict(words), u"参照先が解けなかった行": unresolved,
            u"集計": t,
            u"PP あり/なしで state・reason 等が変わった行": pp_diff,
            u"対照(その fact 自身の値を同じ参照先に当てた。率でない行は除く)": {
                u"当てた行": sum(1 for x in items if x[u"対照(その fact 自身の値を同じ参照先に当てた)"]),
                u"state の分布": dict(collections.Counter(
                    x[u"対照(その fact 自身の値を同じ参照先に当てた)"][u"state"] for x in items
                    if x[u"対照(その fact 自身の値を同じ参照先に当てた)"])),
                u"note": u"0 件の GROUNDED が道具の欠陥でないことを示す。保留(UNPROVABLE)になる行は露出の規則による"},
            u"席の参照先が正解だった T5 の行": sum(1 for x in items if x[u"席の参照先が正解"]),
            u"rows": items,
            u"limits": [u"席の名指しに依る(Core の名指しではない)。T5 の注入は単位込みで値が一致しないので、"
                        u"GROUNDED 0 は engine の独立した証拠ではない(封 K-8)",
                        u"分母は席が名指した注入の行だけ(欠け・なし は入らない)"]}


# ------------------------------------------------------------------ stage
def stage_material(a):
    root, work, tasks = base_dirs()
    if os.path.exists(GEN_MAT):
        raise SystemExit(u"既に在る: %s(作り直さない)" % GEN_MAT)
    env = no_keys()
    for d in (work, tasks):
        if os.path.exists(d) and os.listdir(d):
            raise SystemExit(u"**空でない: %s(作り直さない。消すのは人)**" % d)
        if not os.path.exists(d):
            os.makedirs(d)
    draw = _load(GEN_DRAW)
    docs = draw[u"引いた 8 件"]
    for d in docs:
        if not os.path.exists(ED.cache_path(d)):
            raise SystemExit(u"**ZIP が無い: %s**" % d)
    t0 = time.time()
    tmp_rec = os.path.join(work, "material_gen_c.json")
    rec = run_material(GEN_DRAW, work, tmp_rec, docs)
    t_mat = time.time() - t0
    if [p["docID"] for p in rec[u"書類ごと"]] != docs:
        raise SystemExit(u"**材料の書類が draw の 8 件と合わない**")
    for d in docs:
        shutil.copyfile(os.path.join(work, "%s_task.txt" % d), os.path.join(tasks, "%s_task.txt" % d))
    if sorted(os.listdir(tasks)) != sorted("%s_task.txt" % d for d in docs):
        raise SystemExit(u"**tasks/ に task file 8 本以外が在る**")
    rows, summary = k1_table(rec, tasks)
    bad = [r[u"docID"] for r in rows if not r[u"task が記録と一致"]]
    if bad:
        raise SystemExit(u"**task file が記録と合わない: %s**" % bad)
    ctrl_banned = banned_control(tasks)
    t0 = time.time()
    c1 = kc1(work)
    c2 = kc2(work)
    c3 = kc3(work)
    t_ctrl = time.time() - t0
    rec["spec"] = MB.SPEC
    rec["cd8 の script の既定値だった seal"] = rec.pop("seal")
    rec["seal"] = SEAL + u" 追記 1(A-2・A-3)"
    rec["step"] = u"**汎化 C の段 C1-B。0 USD・席を 1 回も呼んでいない・通信していない**"
    rec[u"引いた 8 件"] = docs
    rec[u"draw"] = "fixtures/xbrl/gen_c/draw_2026-10-20.json"
    rec[u"環境"] = env
    rec[u"問いの sha256 が封の字と一致"] = rec[u"問いの sha256"] == PROMPT_SHA
    rec[u"task file の置き場"] = {u"絶対 path": tasks, u"repo の外か": not os.path.realpath(tasks).startswith(
        os.path.realpath(ROOT) + os.sep), u"file 数": len(os.listdir(tasks)),
        u"note": u"席は自分の task file 1 つだけを読む。(ア) の中間 file は別の work/ に在り tasks/ には無い"}
    rec[u"**K-1 の数**"] = {u"書類ごと": rows, u"集計": summary}
    rec[u"見せない字の検査の対照(故障を作って当てた)"] = ctrl_banned
    rec[u"対照"] = {u"K-C1": c1, u"K-C2": c2, u"K-C3": c3,
                  u"K-11 の入力(3 つとも一致したか)": c1[u"**一致したか**"] and c2[u"**一致したか**"] and c3[u"**一致したか**"]}
    rec[u"所要秒"] = {u"材料": round(t_mat, 1), u"対照 K-C1〜K-C3": round(t_ctrl, 1)}
    rec["limits"] = rec["limits"] + [
        u"**task file は repo に入れていない。**sha256 と字数だけを記録に書いた",
        u"**軸B の分母(T5 の行)は 20 行以下・3 書類。**cd8 の 50 行・7 書類と並べるときは分母を書く",
        u"トークン見込みは 2 つの見方を平均せず並べた。実測は席の便の後"]
    _dump(rec, GEN_MAT)
    print(u"=== C1-B 材料: 書類 %d / 行 %d / 注入 %d / T5 の行 %d / 見せない字 %s ==="
          % (len(rows), summary[u"合計"][u"行"], summary[u"合計"][u"注入"], summary[u"T5 の行の合計"],
             u"0 件" if summary[u"K-1 の各欄(機械の比較。意味づけは結果の席)"][u"見せない字 0 件(8 書類とも)"] else u"在る"))
    print(u"  K-C1 %s / K-C2 %s / K-C3 %s" % (c1[u"**一致したか**"], c2[u"**一致したか**"], c3[u"**一致したか**"]))
    print("->", GEN_MAT)
    return 0


def stage_score(a):
    no_keys()
    if os.path.exists(GEN_C1):
        raise SystemExit(u"既に在る: %s(採り直さない)" % GEN_C1)
    mat = _load(GEN_MAT)
    missing = [p["docID"] for p in mat[u"書類ごと"]
               if not os.path.exists(os.path.join(GEN_ANS, "%s_answer.json" % p["docID"]))]
    if missing:
        raise SystemExit(u"**席の答えが無い: %s。止める**(%s)" % (missing, GEN_ANS))
    os.makedirs(base_dirs()[0], exist_ok=True)
    tmpd = tempfile.mkdtemp(prefix="gen_c1_score_", dir=base_dirs()[0])
    rec = score_run(GEN_MAT, GEN_ANS, os.path.join(tmpd, "c1.json"))
    rec["spec"] = MB.SPEC
    rec["seal"] = SEAL + u" 追記 1"
    rec["step"] = u"**汎化 C の C1 採点。A 対 C′ が主比較(論点は K-4: 席 A 対 Core-P)**"
    rec[u"軸B の分母の注記"] = u"T5 の行だけ。20 行以下・3 書類。cd8 の 50 行・7 書類と並べるときは分母を書く"
    if a.with_engine:
        rec[u"C1-3"] = engine_stage(GEN_MAT, GEN_ANS, base_dirs()[1])
    _dump(rec, GEN_C1)
    print("->", GEN_C1)
    return 0


def stage_engine(a):
    if not a.out:
        raise SystemExit(u"--out が要る(C1-3 の単独の実行は一時 file へ)")
    if os.path.exists(a.out):
        raise SystemExit(u"既に在る: %s" % a.out)
    mat = a.material or GEN_MAT
    ans = a.answers or GEN_ANS
    work = base_dirs()[1] if not a.work else a.work
    if not os.path.exists(work):
        os.makedirs(work)
    rec = engine_stage(mat, ans, work)
    _dump(rec, a.out)
    t = rec[u"集計"]
    print(u"=== C1-3: 注入の行 %d / 席 A が名指した %d / state %s / GROUNDED %d ==="
          % (rec[u"注入の行"], rec[u"席 A が参照先を名指した注入の行(分母)"], t[u"state の分布"],
             t[u"**GROUNDED(誤りを通した)**"][u"件数"]))
    print("->", a.out)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--stage", required=True, choices=["material", "score", "engine"])
    ap.add_argument("--answers", default=None)
    ap.add_argument("--material", default=None)
    ap.add_argument("--work", default=None, help="engine: (ア) の中間 file を置く dir(既定は $TMPDIR/gen_c1/work)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--with-engine", action="store_true")
    a = ap.parse_args(argv)
    return {"material": stage_material, "score": stage_score, "engine": stage_engine}[a.stage](a)


if __name__ == "__main__":
    sys.exit(main())
