# -*- coding: utf-8 -*-
u"""汎化 C 追記 2(改善 1)の段 P-B(封 `docs/XBRL_GENERALITY_SEAL_2026-10-20.md` 追記 2 B-0〜B-5)。

**C0-2・C0-3 を製品の既定 profile(P20)で測り直す。席は 1 回も呼ばない。通信しない。engine は 1 行も変えない。**

C0 の script(``measure/xbrl_gen_c_2026-10-20.py``)は書き直さず、そのまま import する。C0 の関数
``c01`` / ``c02_and_c03_c2`` は profile を module 変数 ``CD8_PROFILE`` から読むので、**この script が
``C0.CD8_PROFILE`` を P20(・対照では P16)に差し替えて呼び、戻す**。差し替えが効いたことは、記録の ``profile``
と、P16 の run が C0 の記録に全欄一致すること(R-C1)・P20 の run が連結の無い 2 書類だけ P16 と違うこと
(R-C2)で確かめる。

読み方(数を見る前に決めた。封の字で 1 通りに決まらなかった所):

  * R-1 は先に確かめる。注入の id の並び・件数が C0 の記録(P16)と違えば、その事実だけを書いて止める。
  * R-3 の括弧『(Z4GF 以外の 6 件は 0〜2)』は封の予測欄の補足で、外れ方の欄は『幅の外』。判定は幅 14〜24 / 30 で行い、
    括弧内の数は別欄(``括弧内の補助``)に出す。
  * R-6 は『Core-P(P20)11〜16 / 20』と『席 A 16 / 20 との差 0〜+25 pt』の両方が成り立つとき当たり。
  * R-8 は C0-3 の P20 の run の GROUNDED の件数(分母 = Core-P(P20)が名指した注入の行)。
  * K-4 の席 A の答えは C1 の記録(``c1_2026-10-20.json`` の ``K-4・K-5 の数`` の rows)から読む(再生成しない)。
    Core-P(P20)は同じ注入の id の P20 の rows から読む。

    cd audit-core
    python3 measure/xbrl_gen_c_p20_2026-10-20.py [--out PATH]
"""
import argparse
import hashlib
import importlib.util
import io
import json
import os
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


#: C0 の script(書き直さない。関数を profile を差し替えて呼ぶ)。
C0 = _mod("measure/xbrl_gen_c_2026-10-20.py", "gen_c0_for_p20")
AC = C0.AC
VE = C0.VE
RS = C0.RS
core = C0.core

SEAL = "docs/XBRL_GENERALITY_SEAL_2026-10-20.md 追記 2"
GEN = C0.GEN
CD8 = C0.CD8
OUT = os.path.join(GEN, "c0_p20_2026-10-20.json")
C0_REC = os.path.join(GEN, "c0_2026-10-20.json")
C1_REC = os.path.join(GEN, "c1_2026-10-20.json")
CD8_P20_REC = os.path.join(CD8, "a_core_vs_grep_P20_2026-10-17.json")
CONSOLIDATED = ["S100Z0OS", "S100YYN7", "S100YYT8", "S100Z42X", "S100YYT4", "S100YYUD"]
NONCONSOL = ["S100Z4GF", "S100Z4J8"]
K45 = u"**K-4・K-5 の数**"


def pct(a, b):
    return None if not b else round(100.0 * a / b, 1)


def frac(a, b):
    return {u"分子": a, u"分母": b, u"率": pct(a, b)}


def sha_file(p):
    with io.open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def jround(x):
    u"""json に書いて読み直した形(file と比べるため)。"""
    return json.loads(json.dumps(x, ensure_ascii=False))


def rng(x, lo, hi):
    return x is not None and lo <= x <= hi


# ------------------------------------------------------------------ 数え方(P16 の c0 の rows にも P20 の rows にも同じ関数を当てる)
def gold_of_row(r):
    return r[u"正解"][u"正解"]


def dimmed(r):
    g = gold_of_row(r)
    return g is not None and "_" in g.split("@", 1)[1]


def cp(r):
    return r[u"腕"]["Core-P"]


def spec_ok(r):
    return bool(cp(r)[u"判定"][u"特定"])


def counts(rows):
    u"""rows(C0-2 の rows と同じ形)から、R-2〜R-9 に要る数を**数え直す**。"""
    t5 = [r for r in rows if r[u"型"] == "T5_COINCIDENT"]
    t1 = [r for r in rows if r[u"型"] == "T1_VALUE"]
    t3 = [r for r in rows if r[u"型"] == "T3_ABSENT"]
    pointed = [r for r in rows if cp(r)[u"判定"][u"参照先を出した"]]
    wrong = [r for r in pointed if cp(r)[u"判定"][u"誤認定"]]
    dim = [r for r in t5 if dimmed(r)]
    gf = [r for r in t5 if r["doc"] == "S100Z4GF"]
    j8 = [r for r in rows if r["doc"] == "S100Z4J8"]
    j8_t1 = [r for r in j8 if r[u"型"] == "T1_VALUE"]
    j8_t3 = [r for r in j8 if r[u"型"] == "T3_ABSENT"]
    return {
        u"T5 の件数": len(t5), u"注入の合計": len(rows), u"T1": len(t1), u"T3": len(t3),
        u"T5 の特定(Core-P)": frac(sum(1 for r in t5 if spec_ok(r)), len(t5)),
        u"Core-P の誤認定率(分母 = 参照先を出した件)": frac(len(wrong), len(pointed)),
        u"T1 の通し(Core-P。確認済みと言った)": frac(sum(1 for r in t1 if cp(r)[u"言うこと"] == u"確認済み"), len(t1)),
        u"T3 の名指し(Core-P)": frac(sum(1 for r in t3 if cp(r)[u"判定"][u"参照先を出した"]), len(t3)),
        u"S100Z4GF の T5": frac(sum(1 for r in gf if spec_ok(r)), len(gf)),
        u"次元つき gold の T5": frac(sum(1 for r in dim if spec_ok(r)), len(dim)),
        u"次元つき gold のうち S100Z4GF": frac(sum(1 for r in dim if r["doc"] == "S100Z4GF" and spec_ok(r)),
                                       sum(1 for r in dim if r["doc"] == "S100Z4GF")),
        u"次元つき gold のうち S100Z4GF 以外": frac(sum(1 for r in dim if r["doc"] != "S100Z4GF" and spec_ok(r)),
                                          sum(1 for r in dim if r["doc"] != "S100Z4GF")),
        u"次元なし gold の T5": frac(sum(1 for r in t5 if not dimmed(r) and spec_ok(r)),
                               sum(1 for r in t5 if not dimmed(r))),
        u"S100Z4J8 の T5 の件数": sum(1 for r in j8 if r[u"型"] == "T5_COINCIDENT"),
        u"S100Z4J8 の T3 の名指し": frac(sum(1 for r in j8_t3 if cp(r)[u"判定"][u"参照先を出した"]), len(j8_t3)),
        u"S100Z4J8 の T1 の通し": frac(sum(1 for r in j8_t1 if cp(r)[u"言うこと"] == u"確認済み"), len(j8_t1)),
        u"D′ の特定": frac(sum(1 for r in t5 if r[u"腕"][u"D′"][u"判定"][u"特定"]), len(t5)),
    }


def t5_read(rows, claim_info):
    u"""C0 の ``補助: T5 50 件の読み`` と同じ分類(gold の枠が次元つきか × Core-P の結果)。"""
    ci = {(x[u"doc"], x[u"id"]): x[u"claim"] for x in claim_info}
    out = {}
    for x in rows:
        if x[u"型"] != "T5_COINCIDENT":
            continue
        cl = ci[(x["doc"], x["id"])]
        c = cp(x)
        if not x[u"対応が付いた"]:
            outc = u"対応が付かない"
        elif c[u"参照先"] is None:
            outc = u"参照先を出さない(%s/%s)" % (cl["state"], cl["reason"])
        elif c[u"判定"][u"特定"]:
            outc = u"特定"
        else:
            outc = u"誤認定"
        d = dimmed(x)
        for key in (u"全体|gold の枠が次元つき=%s" % d, u"%s|gold の枠が次元つき=%s" % (x["doc"], d)):
            out.setdefault(key, {})
            out[key][outc] = out[key].get(outc, 0) + 1
    return dict(sorted(out.items()))


def c03_tally(c03):
    u"""C0-3 の rows から。``C0.tally_c03`` をそのまま使う(書き直さない)。"""
    return C0.tally_c03(c03)


def run_profile(profile, docs, seed, registry, fetched_by):
    u"""C0 の ``c01`` と ``c02_and_c03_c2`` を、``C0.CD8_PROFILE`` を差し替えて呼ぶ。終わったら戻す。"""
    orig = C0.CD8_PROFILE
    C0.CD8_PROFILE = profile
    try:
        t0 = time.time()
        per = C0.c01(docs, fetched_by, profile)
        t_c01 = time.time() - t0
        baseline = {p[u"doc"]: p["_out"] for p in per}
        t0 = time.time()
        rows, cnt, c03, c2, claim_info, decoy = C0.c02_and_c03_c2(docs, seed, registry, baseline)
        t_run = time.time() - t0
        # (ア) の main() そのまま(一時 file。腕・採点は (ア) の実物)
        t0 = time.time()
        tmpdir = tempfile.mkdtemp(prefix="gen_c_p20_%s_" % profile)
        outp = os.path.join(tmpdir, "a_core_vs_grep_%s.json" % profile)
        AC.main(["--docs", ",".join(docs), "--profile", profile, "--out", outp])
        main_rec = C0._load(outp)
        t_main = time.time() - t0
    finally:
        C0.CD8_PROFILE = orig
    recorder_same = (jround(rows) == main_rec["rows"] and jround(cnt) == main_rec[u"注入の件数"])
    return {"profile": profile, "per": per, "rows": rows, "counts": cnt, "c03": c03, "c2": c2,
            "claim_info": claim_info, "decoy": decoy, "main": main_rec, "recorder_same": recorder_same,
            u"秒": {u"c01": round(t_c01, 1), u"Recorder 再走 + C0-3 + C-2": round(t_run, 1),
                   u"(ア) main()": round(t_main, 1)}}


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
    if C0.CD8_PROFILE != "P16":
        raise SystemExit(u"**C0 の CD8_PROFILE が P16 でない。止める**")

    in_sha_before = {u"c0_2026-10-20.json": sha_file(C0_REC), u"c1_2026-10-20.json": sha_file(C1_REC),
                     u"material_2026-10-20.json": sha_file(os.path.join(GEN, "material_2026-10-20.json")),
                     u"draw_2026-10-20.json": sha_file(C0.DRAW), u"fetched_2026-10-20.json": sha_file(C0.FETCHED),
                     u"cd8 a_core_vs_grep_P20_2026-10-17.json": sha_file(CD8_P20_REC),
                     u"cd8 a_core_vs_grep_2026-10-17.json": sha_file(C0.CD8_A_REC)}
    c0 = C0._load(C0_REC)
    c1 = C0._load(C1_REC)
    draw = C0._load(C0.DRAW)
    docs = draw[u"引いた 8 件"]
    fetched = C0._load(C0.FETCHED)
    fetched_by = {x["docID"]: x for x in fetched[u"取得した書類"]}
    if sorted(fetched_by) != sorted(docs):
        raise SystemExit(u"**取得の記録と引いた 8 件が合わない。止める**")
    seed, seed_meta = AC.IJ.verify_seed_sealed(AC.SEED_FILE)
    registry = RS.register_all(core.Registry.default())
    os.makedirs(AC.TMP, exist_ok=True)

    # ================================================================ P20 の run
    p20 = run_profile("P20", docs, seed, registry, fetched_by)
    rows20 = p20["rows"]
    rows16_c0 = c0[u"C0-2 rows"]

    # ---- R-1 を先に: 注入の id の並び・件数
    ids20 = [r["id"] for r in rows20]
    ids16 = [r["id"] for r in rows16_c0]
    type_cnt = lambda rows: {t: sum(1 for r in rows if r[u"型"] == t) for t in ("T5_COINCIDENT", "T1_VALUE", "T3_ABSENT")}
    r1 = {u"注入の id の並びが P16(C0 の記録)と同じ": ids20 == ids16,
          u"件数 P20": len(ids20), u"件数 P16(C0 の記録)": len(ids16),
          u"型別 P20": type_cnt(rows20), u"型別 P16(C0 の記録)": type_cnt(rows16_c0),
          u"注入の件数(作れる site・注入した)が同じ": jround(p20["counts"]) == c0["**C0-2 (ア) の main() の出力**"][u"注入の件数"],
          u"gold が全部同じ": [r[u"正解"] for r in rows20] == [r[u"正解"] for r in rows16_c0],
          u"改変後の値が全部同じ": [r[u"改変後の値"] for r in rows20] == [r[u"改変後の値"] for r in rows16_c0]}
    r1[u"当たり"] = (r1[u"注入の id の並びが P16(C0 の記録)と同じ"] and r1[u"件数 P20"] == 128
                  and r1[u"型別 P20"] == {"T5_COINCIDENT": 50, "T1_VALUE": 38, "T3_ABSENT": 40}
                  and r1[u"注入の件数(作れる site・注入した)が同じ"] and r1[u"gold が全部同じ"])
    if not r1[u"当たり"]:
        rec = {"seal": SEAL, "step": u"**R-1 が外れた。依った事実を書いて止めた(R-2 以降は測っていない)**",
               u"環境": env, u"R-1": r1,
               u"P20 の注入の id のうち P16 に無い": sorted(set(ids20) - set(ids16)),
               u"P16 の注入の id のうち P20 に無い": sorted(set(ids16) - set(ids20))}
        with io.open(a.out, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print(u"**R-1 外れ。止めた**", json.dumps(r1, ensure_ascii=False)[:800])
        return 2

    # ================================================================ P16 の run(R-C1)
    p16 = run_profile("P16", docs, seed, registry, fetched_by)

    # ---- R-C1: P16 の run が C0 の記録に全欄一致
    c0_main = c0["**C0-2 (ア) の main() の出力**"]
    c0_c03 = c0["**C0-3 engine を Core-P の参照先に当てた**"]
    rc1_main_diff = sorted(k for k in set(c0_main) | set(p16["main"]) if k != "rows" and c0_main.get(k) != p16["main"].get(k))
    rc1 = {u"(ア) main() の出力(rows 以外)で違った欄": rc1_main_diff,
           u"(ア) main() の rows が C0 の記録の C0-2 rows と一致": p16["main"]["rows"] == c0[u"C0-2 rows"],
           u"Recorder 再走の rows が C0-2 rows と一致": jround(p16["rows"]) == c0[u"C0-2 rows"],
           u"C0-3 の rows が C0 の記録と一致": jround(p16["c03"]) == c0_c03["rows"],
           u"C0-3 の集計が C0 の記録と一致": jround(c03_tally(p16["c03"])) == c0_c03[u"集計"],
           u"注入の件数が C0 の記録と一致": jround(p16["counts"]) == c0_main[u"注入の件数"],
           u"各注入に対応が付いた claim が C0 の記録と一致": jround(p16["claim_info"]) == c0[u"C0-2 各注入に対応が付いた Core の claim(読むための記録)"],
           u"Recorder 再走 = main() の出力(P16)": p16["recorder_same"]}
    rc1[u"当たり"] = (rc1_main_diff == [] and all(v is True for k, v in rc1.items() if k != u"(ア) main() の出力(rows 以外)で違った欄"))

    # ---- R-C2: 連結のある 6 書類の rows は P16 と P20 で全行一致
    def of(rows, ds):
        return [r for r in rows if r["doc"] in ds]
    same6 = jround(of(rows20, CONSOLIDATED)) == of(rows16_c0, CONSOLIDATED)
    same6_c03 = jround([x for x in p20["c03"] if x["doc"] in CONSOLIDATED]) == [x for x in c0_c03["rows"] if x["doc"] in CONSOLIDATED]
    diff_ids_nc = [r["id"] for r, o in zip(of(rows20, NONCONSOL), of(rows16_c0, NONCONSOL)) if jround(r) != o]
    rc2 = {u"連結のある 6 書類": CONSOLIDATED, u"6 書類の rows(P20)が P16(C0 の記録)と全行一致": same6,
           u"6 書類の rows の件数": len(of(rows20, CONSOLIDATED)),
           u"補助: 6 書類の C0-3 の行も一致": same6_c03,
           u"連結の無い 2 書類で P20 と P16 の rows が違った注入": len(diff_ids_nc),
           u"連結の無い 2 書類の注入の件数": len(of(rows20, NONCONSOL)),
           u"連結の無い 2 書類で違った注入の id": diff_ids_nc,
           u"当たり": bool(same6)}

    # ---- R-C3: cd8 の (ア) を P20 で回す
    t0 = time.time()
    rec8 = C0._load(CD8_P20_REC)
    tmp8 = os.path.join(tempfile.mkdtemp(prefix="gen_c_p20_cd8_"), "a_core_vs_grep_cd8_P20_repro.json")
    AC.main(["--docs", ",".join(rec8[u"書類"]), "--profile", rec8["profile"], "--out", tmp8])
    new8 = C0._load(tmp8)
    diff8 = sorted(k for k in set(rec8) | set(new8) if rec8.get(k) != new8.get(k))
    rc3 = {u"cd8 の記録": "fixtures/xbrl/cd8/a_core_vs_grep_P20_2026-10-17.json", u"profile": rec8["profile"],
           u"書類": rec8[u"書類"], u"違った欄": diff8, u"採点が一致": rec8[u"採点"] == new8[u"採点"],
           u"rows が一致": rec8["rows"] == new8["rows"], u"注入の合計": new8[u"注入の合計"],
           u"当たり": diff8 == []}
    t_rc3 = time.time() - t0

    # ================================================================ 数え直し(P16・P20 に同じ関数)
    n20, n16 = counts(rows20), counts(rows16_c0)
    # (ア) の採点(tally)と数え直しが一致すること(測る道具を疑う)
    tal20 = p20["main"][u"採点"]["Core-P"]
    tal16 = c0_main[u"採点"]["Core-P"]
    cross = {u"P20: T5 の特定が (ア) の採点と一致": (tal20[u"特定率(分母 = T5 の件数)"][u"分子"], tal20[u"特定率(分母 = T5 の件数)"][u"分母"])
             == (n20[u"T5 の特定(Core-P)"][u"分子"], n20[u"T5 の特定(Core-P)"][u"分母"]),
             u"P20: 誤認定率が (ア) の採点と一致": (tal20[u"誤認定率(分母 = 参照先を出した件)"][u"分子"], tal20[u"誤認定率(分母 = 参照先を出した件)"][u"分母"])
             == (n20[u"Core-P の誤認定率(分母 = 参照先を出した件)"][u"分子"], n20[u"Core-P の誤認定率(分母 = 参照先を出した件)"][u"分母"]),
             u"P20: T1 の通しが (ア) の採点と一致": tal20[u"T1 の通し(値がどこにも無いのに確認済み)"][u"分子"] == n20[u"T1 の通し(Core-P。確認済みと言った)"][u"分子"],
             u"P20: T3 の名指しが (ア) の採点と一致": tal20[u"T3 の名指し(参照先が無いのに名指した)"][u"分子"] == n20[u"T3 の名指し(Core-P)"][u"分子"],
             u"P16: T5 の特定が C0 の記録の採点と一致": (tal16[u"特定率(分母 = T5 の件数)"][u"分子"], tal16[u"特定率(分母 = T5 の件数)"][u"分母"])
             == (n16[u"T5 の特定(Core-P)"][u"分子"], n16[u"T5 の特定(Core-P)"][u"分母"])}
    cross[u"全部一致"] = all(cross.values())

    # ---- K-4 の再計算(席 A の答えは C1 の記録から読む。再生成しない)
    k_rows_c1 = c1[K45]["rows"]
    by20 = {r["id"]: r for r in rows20}
    k4_rows, gold_diff = [], []
    for x in k_rows_c1:
        o = by20[x[u"注入の id"]]
        if gold_of_row(o) != x["gold"]:
            gold_diff.append(x[u"注入の id"])
        k4_rows.append({u"doc": x[u"doc"], u"注入の id": x[u"注入の id"], u"gold": x["gold"],
                        u"gold の枠が次元つき": x[u"gold の枠が次元つき"], u"席 A が特定": bool(x[u"席 A が特定"]),
                        u"席 A の参照先": x[u"席 A の参照先"],
                        u"Core-P(P16。C0 の記録)が特定": bool(x[u"Core-P が特定(C0 の記録)"]),
                        u"Core-P(P16)の参照先": x[u"Core-P の参照先(C0 の記録)"],
                        u"Core-P(P20)が特定": spec_ok(o), u"Core-P(P20)の参照先": cp(o)[u"参照先"]})
    if gold_diff:
        raise SystemExit(u"**C1 の gold と P20 の gold が違う注入: %s。止める**" % gold_diff)
    kn = len(k4_rows)
    k_a = sum(1 for r in k4_rows if r[u"席 A が特定"])
    k_c16 = sum(1 for r in k4_rows if r[u"Core-P(P16。C0 の記録)が特定"])
    k_c20 = sum(1 for r in k4_rows if r[u"Core-P(P20)が特定"])
    kdim = [r for r in k4_rows if r[u"gold の枠が次元つき"]]
    knod = [r for r in k4_rows if not r[u"gold の枠が次元つき"]]
    kx = [r for r in k4_rows if r[u"doc"] != "S100Z4GF"]
    kgf = [r for r in k4_rows if r[u"doc"] == "S100Z4GF"]
    k4 = {u"T5 の行": kn, u"gold が C1 と P20 で一致した注入": kn - len(gold_diff),
          u"席 A の特定(C1 の記録。不変)": frac(k_a, kn),
          u"Core-P(P16)の特定(C0 の記録)": frac(k_c16, kn),
          u"Core-P(P20)の特定": frac(k_c20, kn),
          u"差 席 A − Core-P(P16)(pt)": round(pct(k_a, kn) - pct(k_c16, kn), 1),
          u"差 席 A − Core-P(P20)(pt)": round(pct(k_a, kn) - pct(k_c20, kn), 1),
          u"C1 の記録の K-4 の差(照合用)": c1[K45][u"**K-4 差(pt)**"],
          u"次元つき 10 行(K-5 の行)": {u"行": len(kdim), u"席 A": frac(sum(1 for r in kdim if r[u"席 A が特定"]), len(kdim)),
                                  u"Core-P(P16)": frac(sum(1 for r in kdim if r[u"Core-P(P16。C0 の記録)が特定"]), len(kdim)),
                                  u"Core-P(P20)": frac(sum(1 for r in kdim if r[u"Core-P(P20)が特定"]), len(kdim))},
          u"次元なし 10 行": {u"行": len(knod), u"席 A": frac(sum(1 for r in knod if r[u"席 A が特定"]), len(knod)),
                         u"Core-P(P16)": frac(sum(1 for r in knod if r[u"Core-P(P16。C0 の記録)が特定"]), len(knod)),
                         u"Core-P(P20)": frac(sum(1 for r in knod if r[u"Core-P(P20)が特定"]), len(knod))},
          u"S100Z4GF の 8 行": {u"行": len(kgf), u"席 A": frac(sum(1 for r in kgf if r[u"席 A が特定"]), len(kgf)),
                              u"Core-P(P16)": frac(sum(1 for r in kgf if r[u"Core-P(P16。C0 の記録)が特定"]), len(kgf)),
                              u"Core-P(P20)": frac(sum(1 for r in kgf if r[u"Core-P(P20)が特定"]), len(kgf))},
          u"S100Z4GF を除く 12 行": {u"行": len(kx), u"席 A": frac(sum(1 for r in kx if r[u"席 A が特定"]), len(kx)),
                                 u"Core-P(P16)": frac(sum(1 for r in kx if r[u"Core-P(P16。C0 の記録)が特定"]), len(kx)),
                                 u"Core-P(P20)": frac(sum(1 for r in kx if r[u"Core-P(P20)が特定"]), len(kx)),
                                 u"差 席 A − Core-P(P20)(pt)": round(pct(sum(1 for r in kx if r[u"席 A が特定"]), len(kx))
                                                              - pct(sum(1 for r in kx if r[u"Core-P(P20)が特定"]), len(kx)), 1)},
          u"席 A が外した行の Core-P(P20)": [{u"注入の id": r[u"注入の id"], u"席 A の参照先": r[u"席 A の参照先"],
                                         u"Core-P(P20)の参照先": r[u"Core-P(P20)の参照先"]}
                                        for r in k4_rows if not r[u"席 A が特定"]],
          u"席 A が当てて Core-P(P20)が当てなかった行": [r[u"注入の id"] for r in k4_rows
                                            if r[u"席 A が特定"] and not r[u"Core-P(P20)が特定"]],
          u"Core-P(P20)が当てて席 A が外した行": [r[u"注入の id"] for r in k4_rows
                                          if r[u"Core-P(P20)が特定"] and not r[u"席 A が特定"]],
          u"rows": k4_rows}

    # ---- C0-3(P20)
    t3_20 = c03_tally(p20["c03"])
    t3_16 = c03_tally(p16["c03"])

    # ---- P20 で特定しなかった T5 の行(1 件ずつ読むための記録)
    ci20 = {(x[u"doc"], x[u"id"]): x[u"claim"] for x in p20["claim_info"]}
    ci16 = {(x[u"doc"], x[u"id"]): x[u"claim"] for x in c0[u"C0-2 各注入に対応が付いた Core の claim(読むための記録)"]}
    by16 = {r["id"]: r for r in rows16_c0}

    def brief(rows_by, ci, r):
        c = cp(rows_by[r["id"]])
        cl = ci[(r["doc"], r["id"])]
        return {u"参照先": c[u"参照先"], u"特定": bool(c[u"判定"][u"特定"]), u"誤認定": bool(c[u"判定"][u"誤認定"]),
                u"Core の claim の state": None if cl is None else cl["state"],
                u"reason": None if cl is None else cl["reason"]}
    nonspec = []
    for r in rows20:
        if r[u"型"] != "T5_COINCIDENT" or spec_ok(r):
            continue
        nonspec.append({u"doc": r["doc"], u"id": r["id"], u"gold": gold_of_row(r), u"偶然一致する側": r[u"正解"][u"偶然一致する側"],
                        u"gold の枠が次元つき": dimmed(r), u"P20": brief(by20, ci20, r), u"P16": brief(by16, ci16, r)})
    changed = [{u"id": r["id"], u"型": r[u"型"], u"P16": brief(by16, ci16, r), u"P20": brief(by20, ci20, r)}
               for r in rows20 if jround(r) != by16[r["id"]]]

    # ---- 率の主張・C0-1(P20 明示 と 既定の C0 の記録の照合)
    per20 = [{k: v for k, v in p.items() if k != "_out"} for p in p20["per"]]
    def_rec = {x[u"doc"]: x for x in c0["**C0-1 製品の経路(既定の profile)**"][u"書類ごと"]}
    c01_same = [{u"doc": p[u"doc"], u"claims が既定(C0 の記録)と同じ": p[u"claims"] == def_rec[p[u"doc"]][u"claims"],
                 u"states が既定(C0 の記録)と同じ": p[u"states"] == def_rec[p[u"doc"]][u"states"]} for p in per20]
    p16_per = {x[u"doc"]: x for x in c0["C0-1(P16。C-2 と (ア) の基準)"][u"書類ごと"]}
    c01_p16_same = [{u"doc": p[u"doc"], u"claims が P16(C0 の記録)と同じ": p[u"claims"] == p16_per[p[u"doc"]][u"claims"],
                     u"states が P16(C0 の記録)と同じ": p[u"states"] == p16_per[p[u"doc"]][u"states"]} for p in per20]

    # ---- 補助: T5 の偶然一致する側を engine に渡した(R-8 の 0 が独立した証拠でないことの確認。判定に使わない)
    dec_ev = [x for x in p20["decoy"] if x.get(u"state") is not None]
    dec_st = {}
    for x in dec_ev:
        dec_st[x[u"state"]] = dec_st.get(x[u"state"], 0) + 1
    decoy_summary = {u"T5 の行": len(p20["decoy"]), u"engine を通せた行": len(dec_ev), u"state の分布": dec_st,
                     u"GROUNDED": dec_st.get("GROUNDED", 0),
                     u"単位込み(円換算)で値が一致する行": sum(1 for x in dec_ev if x[u"単位込みで値が一致(許容 = 単位の 1)"])}

    # ---- C-2(P20。無改変の主張の state が動かないか。封の外の補助)
    moved = sum(x[u"判定が動いた"] for x in p20["c2"])
    paired = sum(x[u"一意に対になった主張"] for x in p20["c2"])

    # ================================================================ 予測 R-1〜R-11
    ident = n20[u"T5 の特定(Core-P)"]
    wrong = n20[u"Core-P の誤認定率(分母 = 参照先を出した件)"]
    t1p, t3n = n20[u"T1 の通し(Core-P。確認済みと言った)"], n20[u"T3 の名指し(Core-P)"]
    gf = n20[u"S100Z4GF の T5"]
    dm = n20[u"次元つき gold の T5"]
    dm_x = n20[u"次元つき gold のうち S100Z4GF 以外"]
    j8n, j81 = n20[u"S100Z4J8 の T3 の名指し"], n20[u"S100Z4J8 の T1 の通し"]
    kc20 = k4[u"Core-P(P20)の特定"]
    kd20 = k4[u"次元つき 10 行(K-5 の行)"][u"Core-P(P20)"]
    pins = C0.engine_pins()
    g20 = t3_20[u"**GROUNDED(誤りを通した)**"]
    pred = [
        {u"記号": "R-1", u"予測": u"注入の id・件数は P16 と P20 で同じ(128。T5 50・T1 38・T3 40)",
         u"実測": {u"件数": r1[u"件数 P20"], u"型別": r1[u"型別 P20"], u"id の並びが同じ": r1[u"注入の id の並びが P16(C0 の記録)と同じ"]},
         u"当たり": r1[u"当たり"]},
        {u"記号": "R-2", u"予測": u"S100Z4GF の T5 24 件で Core-P(P20)の特定 14〜22 / 24(P16 は 0)",
         u"実測": gf, u"P16": n16[u"S100Z4GF の T5"], u"当たり": 14 <= gf[u"分子"] <= 22 and gf[u"分母"] == 24},
        {u"記号": "R-3", u"予測": u"次元つき gold 30 件で Core-P(P20)の特定 14〜24 / 30(Z4GF 以外の 6 件は 0〜2)",
         u"実測": dm, u"P16": n16[u"次元つき gold の T5"],
         u"括弧内の補助": {u"Z4GF 以外の次元つき gold": dm_x, u"0〜2 の中か": 0 <= dm_x[u"分子"] <= 2 and dm_x[u"分母"] == 6},
         u"当たり": 14 <= dm[u"分子"] <= 24 and dm[u"分母"] == 30},
        {u"記号": "R-4", u"予測": u"T5 50 件で Core-P(P20)の特定 27〜37 / 50(54〜74%。cd8 71.9%)",
         u"実測": ident, u"P16": n16[u"T5 の特定(Core-P)"], u"当たり": 27 <= ident[u"分子"] <= 37 and ident[u"分母"] == 50},
        {u"記号": "R-5", u"予測": u"Core-P(P20)の誤認定率 15〜40%(分母 = 参照先を出した件)、T1 の通し 0 / 38、T3 の名指し 25% 以下",
         u"実測": {u"誤認定率": wrong, u"T1 の通し": t1p, u"T3 の名指し": t3n},
         u"P16": {u"誤認定率": n16[u"Core-P の誤認定率(分母 = 参照先を出した件)"], u"T1 の通し": n16[u"T1 の通し(Core-P。確認済みと言った)"],
                u"T3 の名指し": n16[u"T3 の名指し(Core-P)"]},
         u"当たり": rng(wrong[u"率"], 15, 40) and t1p[u"分子"] == 0 and t1p[u"分母"] == 38
         and t3n[u"率"] is not None and t3n[u"率"] <= 25},
        {u"記号": "R-6", u"予測": u"K-4 の再計算: 同じ 20 行で Core-P(P20)11〜16 / 20、席 A 16 / 20 との差 0〜+25 pt",
         u"実測": {u"席 A": k4[u"席 A の特定(C1 の記録。不変)"], u"Core-P(P20)": kc20,
                 u"差(pt)": k4[u"差 席 A − Core-P(P20)(pt)"]},
         u"P16": {u"Core-P(P16)": k4[u"Core-P(P16)の特定(C0 の記録)"], u"差(pt)": k4[u"差 席 A − Core-P(P16)(pt)"]},
         u"当たり": 11 <= kc20[u"分子"] <= 16 and kc20[u"分母"] == 20 and 0 <= k4[u"差 席 A − Core-P(P20)(pt)"] <= 25},
        {u"記号": "R-7", u"予測": u"次元つき 10 行(K-5 の行)で Core-P(P20)6〜10 / 10(P16 は 0)",
         u"実測": kd20, u"P16": k4[u"次元つき 10 行(K-5 の行)"][u"Core-P(P16)"],
         u"当たり": 6 <= kd20[u"分子"] <= 10 and kd20[u"分母"] == 10},
        {u"記号": "R-8", u"予測": u"C0-3(P20 の参照先): engine が GROUNDED にする件数 0(独立した証拠ではない)",
         u"実測": {u"GROUNDED": g20, u"分母(engine を通せた行)": t3_20[u"engine を通せた行(分母)"],
                 u"Core-P が名指した注入の行": t3_20[u"Core-P が名指した注入の行"]},
         u"P16": {u"GROUNDED": t3_16[u"**GROUNDED(誤りを通した)**"], u"分母": t3_16[u"engine を通せた行(分母)"]},
         u"当たり": g20[u"件数"] == 0 and t3_20[u"engine を通せた行(分母)"] > 0},
        {u"記号": "R-9", u"予測": u"S100Z4J8(T5 0)の T3 の名指しは P20 で 0〜3 / 5、T1 の通し 0 / 5",
         u"実測": {u"S100Z4J8 の T5 の件数": n20[u"S100Z4J8 の T5 の件数"], u"T3 の名指し": j8n, u"T1 の通し": j81},
         u"P16": {u"T3 の名指し": n16[u"S100Z4J8 の T3 の名指し"], u"T1 の通し": n16[u"S100Z4J8 の T1 の通し"]},
         u"当たり": 0 <= j8n[u"分子"] <= 3 and j8n[u"分母"] == 5 and j81[u"分子"] == 0 and j81[u"分母"] == 5},
        {u"記号": "R-10", u"予測": u"対照 R-C1〜R-C3 が全部期待どおり",
         u"実測": {u"R-C1": rc1[u"当たり"], u"R-C2": rc2[u"当たり"], u"R-C3": rc3[u"当たり"]},
         u"当たり": rc1[u"当たり"] and rc2[u"当たり"] and rc3[u"当たり"]},
        {u"記号": "R-11", u"予測": u"core/・adapters/ の差分 0 行。覆い +1(結果の門)",
         u"実測": {u"core/・adapters/ の差分 0 行(ac8c3ff・HEAD・作業木)": pins[u"一致"],
                 u"過去の門・覆いの数": u"この script では測らない(pytest と suite_coverage を別に走らせて結果文書に書く)"},
         u"当たり": None, u"この script が測った部分": pins[u"一致"]},
    ]
    in_sha_after = {u"c0_2026-10-20.json": sha_file(C0_REC), u"c1_2026-10-20.json": sha_file(C1_REC),
                    u"material_2026-10-20.json": sha_file(os.path.join(GEN, "material_2026-10-20.json")),
                    u"draw_2026-10-20.json": sha_file(C0.DRAW), u"fetched_2026-10-20.json": sha_file(C0.FETCHED),
                    u"cd8 a_core_vs_grep_P20_2026-10-17.json": sha_file(CD8_P20_REC),
                    u"cd8 a_core_vs_grep_2026-10-17.json": sha_file(C0.CD8_A_REC)}

    rec = {
        "seal": SEAL, "step": u"**汎化 C 追記 2 の段 P-B。0 USD・席を呼ばない・通信しない。engine は 1 行も変えない。C0・C1 の記録と答えは読むだけ**",
        "profile": "P20", u"環境": env, u"engine の指紋": p20["per"][0][u"engine"], u"engine の留め": pins,
        u"材料": {u"書類": docs, u"draw": "fixtures/xbrl/gen_c/draw_2026-10-20.json",
                u"取得の記録": "fixtures/xbrl/gen_c/fetched_2026-10-20.json",
                u"注入の種": {"file": "measure/SEED.json", "sealed_on": seed_meta.get("sealed_on")}},
        u"入力の sha256(前後で変えていない)": {u"前": in_sha_before, u"後": in_sha_after, u"一致": in_sha_before == in_sha_after},
        u"**R-1**": r1,
        u"C0-1(P20 を明示して回した)": {u"書類ごと": per20, u"既定(C0 の記録)と同じか": c01_same,
                                 u"P16(C0 の記録)と同じか": c01_p16_same,
                                 u"補助: S100Z4GF・S100Z4J8 の states(P20 / P16)": {
                                     d: {u"P20": [x for x in per20 if x[u"doc"] == d][0][u"states"], u"P16": p16_per[d][u"states"]}
                                     for d in NONCONSOL}},
        u"**C0-2 (ア) の main() の出力(P20)**": {k: v for k, v in p20["main"].items() if k != "rows"},
        u"C0-2 rows(P20)": p20["main"]["rows"],
        u"Recorder をかぶせた再走が main() の出力と一致(P20)": p20["recorder_same"],
        u"C0-2 各注入に対応が付いた Core の claim(P20。読むための記録)": p20["claim_info"],
        u"**数え直し(P16 は C0 の記録の rows、P20 は今回の rows。同じ関数を当てた)**": {u"P20": n20, u"P16": n16},
        u"(ア) の採点と数え直しの照合": cross,
        u"補助: T5 50 件の読み(P20。gold の枠が次元つきか × Core-P の結果)": t5_read(rows20, p20["claim_info"]),
        u"補助: T5 50 件の読み(P16。C0 の記録と同じ分類を今回の P16 の run に)": t5_read(p16["rows"], p16["claim_info"]),
        u"**P20 で特定しなかった T5 の行(1 件ずつ読む)**": nonspec,
        u"P16 と P20 で rows が違った注入(全型)": changed,
        u"**K-4 の再計算**": k4,
        u"**C0-3 engine を Core-P(P20)の参照先に当てた**": {u"集計": t3_20, u"rows": p20["c03"]},
        u"参考: C0-3 の集計(P16。今回の P16 の run)": t3_16,
        u"**補助(封の外。R-8 の 0 が独立した証拠でないことの確認。判定に使わない)T5 の偶然一致する側を engine に渡した(P20)**": {
            u"集計": decoy_summary, u"rows": p20["decoy"]},
        u"補助: C-2(P20。無改変の主張の state が動いたか。封の外)": {u"一意に対になった主張(延べ)": paired, u"判定が動いた(延べ)": moved},
        u"**対照 R-C1**": rc1, u"**対照 R-C2**": rc2, u"**対照 R-C3**": rc3,
        u"**予測 R-1〜R-11**": pred,
        u"cd8 の数・C0 の数(並べる相手。C0 の記録から読んだ)": {
            u"C0 の T5 の特定": c0_main[u"採点"]["Core-P"][u"特定率(分母 = T5 の件数)"],
            u"C0 の誤認定率": c0_main[u"採点"]["Core-P"][u"誤認定率(分母 = 参照先を出した件)"],
            u"cd8 の Core-P の特定": u"46 / 64 = 71.9%", u"C1 の K-4(P16)": c1[K45][u"**K-4 差(pt)**"]},
        u"所要秒": {u"P20": p20[u"秒"], u"P16": p16[u"秒"], u"R-C3 cd8 の (ア) を P20 で": round(t_rc3, 1),
                u"全体": round(time.time() - t_start, 1)},
        u"limits": [u"8 書類 1 回である。合格線は作らない。",
                    u"席の答えは再生成していない(C1 の記録のまま)。席が見た本文は 8 件同時注入の本文で、Core-P の本文は 1 件ずつの注入。",
                    u"R-8 の 0 は engine の独立した証拠ではない(T5 の注入は単位込みで一致しない。Core が先に止める)。",
                    u"T5 の site 規則(G-4)・増減額の文で残高を名指す型は触っていない。",
                    u"(ア) の脚注: 正解は identified_sites(値の一意性 + 単位・ラベル)で作られ、正解そのものが誤りうる。"],
    }
    with io.open(a.out, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(u"=== 汎化 C 追記 2 段 P-B(0 USD)===")
    for p in pred:
        print(u"  %-5s %s" % (p[u"記号"], {True: u"当たり", False: u"**外れ**", None: u"(別に判定)"}[p[u"当たり"]]),
              json.dumps(p[u"実測"], ensure_ascii=False)[:230])
    print(u"R-C1 %s / R-C2 %s / R-C3 %s" % (rc1[u"当たり"], rc2[u"当たり"], rc3[u"当たり"]))
    print(u"入力の sha256 前後一致:", in_sha_before == in_sha_after, "/ 数え直しの照合:", cross[u"全部一致"])
    print(u"所要:", rec[u"所要秒"])
    print("->", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
