# -*- coding: utf-8 -*-
u"""席と Core の一致の信頼(3 群)― 封 ``docs/XBRL_HYBRID_TRUST_SEAL_2026-10-20.md`` の段 1(0 USD)。

**席は 1 回も呼ばない。通信しない。``core/``・``adapters/`` は 0 行。** 席の答え・材料・既存の記録は読むだけ。
予測 H-1〜H-8 は封の字(commit 4a4df01)。幅はここに字で持つ(封と合わせた)。

やること
  1. α 型: 席が参照先を出した行の全部(gen_c 102・cd8 85)に ``xbrl_gen_c_alpha_2026-10-20.py`` の ``collect_named``
     (= ``engine_item``。``verify_external``・``period_pair=True``・profile を取らない経路)を当てる。写さない。
  2. Core 自身: 材料の ``席の前に出せる分`` の ``Core`` を作った経路(``xbrl_cd_material_2026-10-17.py`` の ``main``。
     ``C1.run_material`` が入出力だけ差し替えて回す)を、測った当時の既定 profile = P21(``PROFILE_AT_MEASURE``)で全 192 行 × 2 集合
     に当て直す。対照として P16 を明示して同じ経路を回し、記録の材料の ``Core`` と全 384 行を突き合わせる。
  3. 3 群(G1 = 席が確認済み・G2 = G1 のうち Core が GROUNDED・G3 = G1 のうち GROUNDED でない)を α 型(主)と
     Core 自身(副)で作り、大きさ・精度(= 注入でない行 / 群)・G3 の state の内訳を出す。
  4. 合成 H(席を上書きしない)を全 384 行に当てる。
  5. 予測 H-1〜H-8 を判定する。

席の字は記録 ``c1_2026-10-20.json``・``cd8/score_2026-10-17.json`` の ``rows`` の ``席`` から読む(答えの file は α 型の
参照先の原文を読むためにだけ開く)。

    cd audit-core
    TMPDIR=<repo の外> python3 measure/xbrl_hybrid_trust_2026-10-20.py
"""
from __future__ import print_function

import argparse
import collections
import hashlib
import importlib.util
import io
import json
import os
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


#: α 型の実物(``collect_named`` → ``engine_item``)。書き直さない。
AL = _mod("measure/xbrl_gen_c_alpha_2026-10-20.py", "alpha_for_hybrid")
C1, MB, G0 = AL.C1, AL.MB, AL.G0
RS, core = AL.RS, AL.core
from adapters.xbrl import vocabulary as V   # noqa: E402

# 記録(hybrid_trust_*.json)を測った時点の既定は P21。2026-10-20 段 2(期を縛る P22。封 docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md)で
# vocabulary.DEFAULT_PROFILE は P22 になったので、測った当時の P21 を字で留める(Core 自身の当て直しは P21 の経路。α 型は profile を取らない経路で不変)。
PROFILE_AT_MEASURE = "P21"

SEAL = "docs/XBRL_HYBRID_TRUST_SEAL_2026-10-20.md"
SEAL_COMMIT = "4a4df01"
GEN, CD8 = AL.GEN, AL.CD8
OUT = os.path.join(GEN, "hybrid_trust_2026-10-20.json")
SETS = (
    (u"gen_c", C1.GEN_C1, AL.GEN_MAT, AL.GEN_ANS, AL.GEN_DRAW),
    (u"cd8", C1.CD8_SCORE, AL.CD8_MAT, AL.CD8_ANS, C1.CD8_DRAW))
SET_NAMES = tuple(s[0] for s in SETS)

#: 封の字(事実 1)。分母・期待の数。
N_ROWS, N_INJ = 192, 64
FACT_G1 = {u"gen_c": 77, u"cd8": 41}
FACT_HOLD_INJ = {u"gen_c": 39, u"cd8": 13}

#: 予測の幅(封 §1 の字)。
H2 = {u"gen_c": (44, 50), u"cd8": (30, 35)}
H3_HOLD = {u"gen_c": (18, 26), u"cd8": (5, 10)}
H3_VM = {u"gen_c": (7, 11), u"cd8": (0, 3)}
H4_G2 = {u"gen_c": (20, 28), u"cd8": (1, 5)}
H4_NOMATCH = {u"gen_c": 80, u"cd8": 51}
H6 = {u"gen_c": (0, 3), u"cd8": (0, 2)}
H8 = {u"gen_c": (44, 53), u"cd8": (30, 40)}

#: α-2 の読み(**人の読み。記録の外・門で縛れない**)。VALUE_MISMATCH の行ごとに「席の側」「Core の側」のどちらか。
#: 空なら止まる(読みを書いてから採る)。キーは (集合, doc, id)。値は (ラベル, 根拠の字)。
_INC = u"抜粋は『増加し』『減少し』『増収』『増益』のどれかを含む増減額の文。席の参照先は残高または当期の実績の要素で、主張の数は参照先の値と桁が違う。同じ枠で期間だけ違う fact との差が主張の数に 1 単位以内で合う(2 つの fact の差として導ける)"
READING = {
    (u"gen_c", "S100YYN7", "R006"): (u"Core の側", u"席の参照先はセグメント利益(正しい要素)。PP の再計算は 352.97 で、主張 352.2 との差は百万円単位に丸めた fact から出る"),
    (u"gen_c", "S100YYT4", "R002"): (u"席の側", _INC),
    (u"gen_c", "S100YYT4", "R004"): (u"席の側", _INC),
    (u"gen_c", "S100Z4J8", "R002"): (u"席の側", _INC),
    (u"gen_c", "S100Z4J8", "R006"): (u"席の側", _INC),
    (u"gen_c", "S100Z4J8", "R009"): (u"席の側", _INC),
    (u"gen_c", "S100Z4J8", "R012"): (u"席の側", _INC),
    (u"gen_c", "S100Z4J8", "R015"): (u"席の側", _INC),
    (u"gen_c", "S100Z4J8", "R017"): (u"席の側", _INC),
    (u"cd8", "S100YZEV", "R017"): (u"席の側", _INC),
}

STATES_SELF = (u"GROUNDED", u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND", u"対応なし")


def pct(a, b):
    return None if not b else round(100.0 * a / b, 1)


def frac(a, b):
    return {u"分子": a, u"分母": b, u"率": pct(a, b)}


def inr(x, rng):
    return rng[0] <= x <= rng[1]


def sha_file(p):
    return C1.sha_file(p)


def core_state(c):
    u"""材料の ``Core`` の state。``state`` が None(対応が付かない)は ``対応なし``。"""
    s = c.get("state")
    return s if s else u"対応なし"


def make_mat(draw, profile, work, out_path):
    old = MB.PROFILE
    MB.PROFILE = profile
    try:
        rec = C1.run_material(draw, work, out_path)
    finally:
        MB.PROFILE = old
    if rec.get("profile") != profile:
        raise SystemExit(u"**材料の profile が差し替わっていない: %r != %r**" % (rec.get("profile"), profile))
    return rec


def core_map(mat):
    out = {}
    for p in mat[u"書類ごと"]:
        for rid, pre in p[u"席の前に出せる分"].items():
            out[(p["docID"], rid)] = pre["Core"]
    return out


def engine_pins():
    u"""HEAD・core/ と adapters/ の追跡 file(HEAD の中身)と作業木の sha256。束ねた sha は repo 相対の path で cwd に依らない。"""
    head = G0._git(["rev-parse", "HEAD"])
    paths = [p for p in G0._git(["ls-files", "--", "adapters", "core"]).split("\n") if p]
    rows, mism = [], []
    for p in paths:
        with io.open(os.path.join(ROOT, p), "rb") as fh:
            now = G0.sha256_bytes(fh.read())
        rows.append("%s\t%s" % (p, now))
        if G0.sha256_bytes(G0._git(["show", "HEAD:./%s" % p], binary=True)) != now:
            mism.append(p)
    numstat = G0._git(["diff", "HEAD", "--numstat", "--", "core", "adapters"])
    status = G0._git(["status", "--porcelain", "--", "core", "adapters"])
    return {u"HEAD": head, u"core/ と adapters/ の追跡 file 数": len(paths),
            u"作業木で HEAD と sha256 が違う file": mism,
            u"束ねた sha256(core/ と adapters/ の追跡 file。作業木の内容。repo 相対の path で cwd に依らない)":
                G0.sha256_bytes("\n".join(sorted(rows)).encode("utf-8")),
            u"git diff HEAD --numstat -- core adapters": numstat,
            u"git status --porcelain -- core adapters": status,
            u"vocabulary.DEFAULT_PROFILE": PROFILE_AT_MEASURE,
            u"一致": (not mism and numstat == "" and status == "")}


def h_rule(seat, core_ok):
    u"""合成 H(封 §1)。席を上書きしない。"""
    if seat == u"誤りが在る":
        return u"誤り(席)"
    if seat == u"確認済み":
        return u"二重確認" if core_ok else u"警告"
    if seat == u"判定できない":
        return u"Core のみ確認" if core_ok else u"保留"
    raise SystemExit(u"**席の判定語が 3 つの外: %r。止める**" % (seat,))


def tally_groups(rows, key_state, key_group):
    u"""G1・G2・G3 の大きさ・精度・G3 の state の内訳。``rows`` は 1 集合の行。"""
    g1 = [r for r in rows if r[u"G1(席が確認済み)"]]
    out = {}
    for g in (u"G1", u"G2", u"G3"):
        if g == u"G1":
            m = g1
        else:
            m = [r for r in g1 if r[key_group] == g]
        inj = sum(1 for r in m if r[u"注入か"])
        out[g] = {u"行": len(m), u"注入": inj, u"無改変": len(m) - inj,
                  u"精度(注入でない行 / 群)": frac(len(m) - inj, len(m))}
    g3 = [r for r in g1 if r[key_group] == u"G3"]
    out[u"G3 の state の内訳"] = dict(sorted(collections.Counter(r[key_state] for r in g3).items()))
    out[u"G1 の state の内訳"] = dict(sorted(collections.Counter(r[key_state] for r in g1).items()))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--explore", action="store_true", help=u"読みのラベルが無くても採る(下見用。記録は作業用)")
    a = ap.parse_args(argv)
    if os.path.exists(a.out):
        raise SystemExit(u"既に在る: %s(採り直さない)" % a.out)
    t_start = time.time()
    env = C1.no_keys()
    base = AL.base_dir()
    for d in ("work_gen", "work_cd8", "work_gen_p16", "work_gen_def", "work_cd8_p16", "work_cd8_def",
              "work_gen_p20", "work_cd8_p20"):
        os.makedirs(os.path.join(base, d), exist_ok=True)
    tmpd = tempfile.mkdtemp(prefix="hybrid_", dir=base)
    default_profile = PROFILE_AT_MEASURE
    if default_profile != "P21":
        raise SystemExit(u"**測った当時の profile が P21 でない: %r。止める**" % default_profile)

    ans_files = {}
    for name, _rec, _mat, ans, _draw in SETS:
        ans_files[name] = {p: sha_file(os.path.join(ans, p)) for p in sorted(os.listdir(ans)) if p.endswith("_answer.json")}
    inputs = {
        u"席の答え": ans_files,
        u"材料": {u"gen_c": sha_file(AL.GEN_MAT), u"cd8": sha_file(AL.CD8_MAT)},
        u"席の字の記録(rows の 席)": {u"gen_c c1_2026-10-20.json": sha_file(C1.GEN_C1),
                              u"cd8 score_2026-10-17.json": sha_file(C1.CD8_SCORE)},
        u"α 型の記録(読むだけ)": sha_file(AL.OUT),
        u"draw": {u"gen_c": sha_file(AL.GEN_DRAW), u"cd8": sha_file(C1.CD8_DRAW)},
        u"封": sha_file(os.path.join(ROOT, SEAL))}

    seed, _meta = MB.IJ.verify_seed_sealed(MB.SEED_FILE)
    registry = RS.register_all(core.Registry.default())

    t0 = time.time()
    rows_all, per_set = [], {}
    contrast = {}
    mats = {}
    for name, rec_path, mat_path, ans_dir, draw in SETS:
        key = name.replace("_", "")
        seat_rows = C1._load(rec_path)["rows"]
        if len(seat_rows) != N_ROWS:
            raise SystemExit(u"**席の行が 192 でない: %s %d**" % (name, len(seat_rows)))
        mat_old = C1._load(mat_path)
        # ---- α 型
        items, _per_doc = AL.collect_named(mat_path, ans_dir, os.path.join(base, "work_" + ("gen" if name == u"gen_c" else "cd8")),
                                           registry, seed, with_reading=True)
        alpha = {(x["doc"], x["id"]): x for x in items}
        # ---- Core 自身(既定 P21)と対照(P16 明示)
        mat_def = make_mat(draw, default_profile, os.path.join(base, "work_%s_def" % key), os.path.join(tmpd, "%s_def.json" % key))
        mat_p16 = make_mat(draw, "P16", os.path.join(base, "work_%s_p16" % key), os.path.join(tmpd, "%s_p16.json" % key))
        mat_p20 = make_mat(draw, "P20", os.path.join(base, "work_%s_p20" % key), os.path.join(tmpd, "%s_p20.json" % key))
        mats[name] = (mat_old, mat_def, mat_p16)
        inv_def = AL.material_invariants(mat_old, mat_def)
        inv_p16 = AL.material_invariants(mat_old, mat_p16)
        c_old, c_def, c_p16 = core_map(mat_old), core_map(mat_def), core_map(mat_p16)
        if not (set(c_old) == set(c_def) == set(c_p16) and len(c_old) == N_ROWS):
            raise SystemExit(u"**材料の行の集合が一致しない: %s。止める**" % name)
        gold = {(p["docID"], rid): pre[u"正解"] for p in mat_old[u"書類ごと"] for rid, pre in p[u"席の前に出せる分"].items()}
        p16_diff = sorted(k for k in c_old if c_old[k] != c_p16[k])
        state_diff_p16 = sorted(k for k in c_old if core_state(c_old[k]) != core_state(c_p16[k]))
        g_old = sorted(k for k in c_old if core_state(c_old[k]) == u"GROUNDED")
        g_def = sorted(k for k in c_def if core_state(c_def[k]) == u"GROUNDED")
        g_p16 = sorted(k for k in c_p16 if core_state(c_p16[k]) == u"GROUNDED")
        def_vs_p16 = sorted(k for k in c_def if c_def[k] != c_p16[k])
        c_p20 = core_map(mat_p20)
        g_p20 = sorted(k for k in c_p20 if core_state(c_p20[k]) == u"GROUNDED")
        gained = sorted(set(g_def) - set(g_p16))
        lost = sorted(set(g_p16) - set(g_def))
        inj_of = {(r["doc"], r["id"]): bool(r[u"注入か"]) for r in seat_rows}
        seat_of = {(r["doc"], r["id"]): r[u"席"][u"判定"] for r in seat_rows}
        contrast[name] = {
            u"P16 明示で回した Core が記録の材料の Core と全行一致(192 行)": not p16_diff,
            u"一致しなかった行": [list(k) for k in p16_diff],
            u"state だけ見て一致しなかった行": [list(k) for k in state_diff_p16],
            u"材料の不変(P16 で回した材料。task の sha256・注入 id・行 id・注入か・正解)": inv_p16,
            u"材料の不変(既定で回した材料)": inv_def,
            u"GROUNDED の行の数(記録の材料 / P16 で回した / 既定)": [len(g_old), len(g_p16), len(g_def)],
            u"GROUNDED の集合: 既定 と P16 で違う行": [list(k) for k in sorted(set(g_def) ^ set(g_p16))],
            u"Core の言うこと(state・参照先・言うこと)が既定と P16 で違う行": [list(k) for k in def_vs_p16],
            u"補助(封の外): P16 → 既定(P21)で GROUNDED に増えた行": [list(k) for k in gained],
            u"補助(封の外): P16 → 既定(P21)で GROUNDED から減った行": [list(k) for k in lost],
            u"補助(封の外): 増えた行のうち注入の行": sum(1 for k in gained if inj_of[k]),
            u"補助(封の外): 増えた行の席の判定": dict(sorted(collections.Counter(seat_of[k] for k in gained).items())),
            u"補助(封の外): P20 明示で回した GROUNDED の集合 と 既定で違う行": [list(k) for k in sorted(set(g_p20) ^ set(g_def))],
            u"補助(封の外): P20 明示の材料の不変": AL.material_invariants(mat_old, mat_p20),
            u"記録の材料の profile": mat_old.get("profile"),
            u"既定で回した材料の profile": mat_def.get("profile")}
        # ---- 行
        for sr in seat_rows:
            k = (sr["doc"], sr["id"])
            seat = sr[u"席"][u"判定"]
            al = alpha.get(k)
            if al is not None and al[u"席の判定"] != seat:
                raise SystemExit(u"**席の判定が答えと記録で違う: %s %s**" % k)
            if (sr[u"席"][u"参照先"] is not None) != (al is not None):
                raise SystemExit(u"**席が参照先を出した行と α 型の行が合わない: %s %s**" % k)
            cs = core_state(c_def[k])
            a_state = al[u"engine の state"] if al else None
            g1 = seat == u"確認済み"
            grp_a = grp_s = None
            if g1:
                grp_a = u"G2" if a_state == "GROUNDED" else u"G3"
                grp_s = u"G2" if cs == "GROUNDED" else u"G3"
            use = u"α 型" if al is not None else u"Core 自身"
            use_state = a_state if al is not None else cs
            h = h_rule(seat, use_state == "GROUNDED")
            rows_all.append({
                u"集合": name, u"doc": k[0], u"id": k[1], u"注入か": bool(sr[u"注入か"]), u"正解": gold[k],
                u"席の判定": seat, u"席の参照先": sr[u"席"][u"参照先"],
                u"α 型の state": a_state if al is not None else u"参照先なし",
                u"α 型の参照先": al[u"参照先(原文)"] if al is not None else None,
                u"α 型の reason": al[u"engine の reason"] if al is not None else None,
                u"Core 自身(既定)の state": cs, u"Core 自身(既定)の参照先": c_def[k]["参照先"],
                u"Core 自身(既定)の言うこと": c_def[k][u"言うこと"],
                u"Core 自身(P16 明示)の state": core_state(c_p16[k]),
                u"G1(席が確認済み)": g1, u"群(α 型)": grp_a, u"群(Core 自身)": grp_s,
                u"H の Core の出どころ": use, u"H の Core の state": use_state, u"H の出力": h})
        per_set[name] = {u"items": items, u"alpha": alpha}
    t_run = time.time() - t0

    # ---- 集計(行から数える)
    agg = {}
    vm_view = []
    for name in SET_NAMES:
        rs = [r for r in rows_all if r[u"集合"] == name]
        inj = [r for r in rs if r[u"注入か"]]
        unc = [r for r in rs if not r[u"注入か"]]
        seat_c = lambda m, w: sum(1 for r in m if r[u"席の判定"] == w)
        seat_facts = {u"行": len(rs), u"注入": len(inj), u"無改変": len(unc),
                      u"席が確認済みにした注入": seat_c(inj, u"確認済み"), u"席が判定できないにした注入": seat_c(inj, u"判定できない"),
                      u"席が確認済みにした無改変": seat_c(unc, u"確認済み"), u"席が判定できないにした無改変": seat_c(unc, u"判定できない"),
                      u"席の偽警報(無改変で誤りが在る)": seat_c(unc, u"誤りが在る")}
        ga = tally_groups(rs, u"α 型の state", u"群(α 型)")
        gs = tally_groups(rs, u"Core 自身(既定)の state", u"群(Core 自身)")
        hout = {}
        for kind, m in ((u"無改変", unc), (u"注入", inj), (u"全部", rs)):
            hout[kind] = dict(sorted(collections.Counter(r[u"H の出力"] for r in m).items()))
        h_confirm = sum(1 for r in rs if r[u"H の出力"] in (u"二重確認", u"Core のみ確認"))
        h_through = sum(1 for r in inj if r[u"H の出力"] in (u"二重確認", u"Core のみ確認"))
        hold_inj = [r for r in inj if r[u"席の判定"] == u"判定できない"]
        a_inj_g = [r for r in inj if r[u"α 型の state"] == "GROUNDED"]
        s_inj_g = [r for r in inj if r[u"Core 自身(既定)の state"] == "GROUNDED"]
        s_nomatch = sum(1 for r in rs if r[u"Core 自身(既定)の state"] == u"対応なし")
        s_nomatch_p16 = sum(1 for r in rs if r[u"Core 自身(P16 明示)の state"] == u"対応なし")
        agg[name] = {
            u"席の字(事実 1)": seat_facts, u"3 群(α 型)": ga, u"3 群(Core 自身)": gs,
            u"H の出力": hout, u"H の確認(二重確認 + Core のみ確認)": frac(h_confirm, len(rs)),
            u"誤りを通した(注入の行が二重確認か Core のみ確認)": frac(h_through, len(inj)),
            u"注入で Core(α 型)が GROUNDED": frac(len(a_inj_g), len(inj)),
            u"注入で Core 自身が GROUNDED": frac(len(s_inj_g), len(inj)),
            u"α 型の行(席が参照先を出した行)": sum(1 for r in rs if r[u"α 型の state"] != u"参照先なし"),
            u"G1 のうち参照先なしの行(α 型が効かない)": sum(1 for r in rs if r[u"G1(席が確認済み)"] and r[u"α 型の state"] == u"参照先なし"),
            u"席が迷った注入": {u"行": len(hold_inj),
                           u"Core 自身の state の分布": dict(sorted(collections.Counter(
                               r[u"Core 自身(既定)の state"] for r in hold_inj).items())),
                           u"Core 自身が VALUE_MISMATCH で止めた": frac(sum(
                               1 for r in hold_inj if r[u"Core 自身(既定)の state"] == "VALUE_MISMATCH"), len(hold_inj)),
                           u"Core 自身が見ていない(対応なし)": frac(sum(
                               1 for r in hold_inj if r[u"Core 自身(既定)の state"] == u"対応なし"), len(hold_inj))},
            u"Core 自身が対応なし(192 行。既定)": s_nomatch, u"Core 自身が対応なし(192 行。P16 明示)": s_nomatch_p16}
        # VALUE_MISMATCH の読みの材料(α 型・G3)
        alpha = per_set[name]["alpha"]
        for r in rs:
            if r[u"G1(席が確認済み)"] and r[u"α 型の state"] == "VALUE_MISMATCH":
                x = alpha[(r["doc"], r["id"])]
                lab = READING.get((name, r["doc"], r["id"]))
                vm_view.append({
                    u"集合": name, u"doc": r["doc"], u"id": r["id"], u"注入か": r[u"注入か"],
                    u"材料の値": x[u"材料の値"], u"材料の単位": x[u"材料の単位"], u"抜粋": x[u"抜粋"],
                    u"席の参照先": x[u"参照先(原文)"], u"参照先の fact の値": x[u"参照先の fact の値"],
                    u"参照先の fact の context": x[u"参照先の fact の context"], u"engine の reason": x[u"engine の reason"],
                    u"engine の recomputed": x[u"engine の recomputed"],
                    u"読みの材料(α-2)": x.get(u"読みの材料(α-2)"),
                    u"読み": lab[0] if lab else None, u"読みの根拠": lab[1] if lab else None})
    missing = [(v[u"集合"], v["doc"], v["id"]) for v in vm_view if v[u"読み"] is None]
    extra = sorted(set(READING) - set((v[u"集合"], v["doc"], v["id"]) for v in vm_view))
    if (missing or extra) and not a.explore:
        raise SystemExit(u"**読みのラベルが VALUE_MISMATCH の行と合わない: 足りない %r / 余る %r**" % (missing, extra))

    # ---- 予測 H-1〜H-8
    def ga_(n, g, field=u"3 群(α 型)"):
        return agg[n][field][g]

    prec = lambda n, g, f: ga_(n, g, f)[u"精度(注入でない行 / 群)"][u"率"]
    h1_ok = all(ga_(n, u"G1")[u"行"] == FACT_G1[n] for n in SET_NAMES) and all(
        prec(n, g, f) == 100.0 and ga_(n, g, f)[u"行"] > 0
        for n in SET_NAMES for g in (u"G1", u"G2", u"G3") for f in (u"3 群(α 型)", u"3 群(Core 自身)"))
    h2 = {n: ga_(n, u"G2")[u"行"] for n in SET_NAMES}
    h2_ok = all(inr(h2[n], H2[n]) for n in SET_NAMES)
    h3 = {}
    for n in SET_NAMES:
        br = agg[n][u"3 群(α 型)"][u"G3 の state の内訳"]
        h3[n] = {u"保留(UNPROVABLE + POINTER_NOT_FOUND)": br.get("UNPROVABLE", 0) + br.get("POINTER_NOT_FOUND", 0),
                 u"VALUE_MISMATCH": br.get("VALUE_MISMATCH", 0),
                 u"G3 の内訳": br}
    h3_range = all(inr(h3[n][u"保留(UNPROVABLE + POINTER_NOT_FOUND)"], H3_HOLD[n]) and inr(h3[n][u"VALUE_MISMATCH"], H3_VM[n])
                   for n in SET_NAMES)
    n_vm = len(vm_view)
    n_seat_side = sum(1 for v in vm_view if v[u"読み"] == u"席の側")
    h3_read = None if (not n_vm or any(v[u"読み"] is None for v in vm_view)) else (2 * n_seat_side > n_vm)
    h3_ok = None if h3_read is None else bool(h3_range and h3_read)
    h4 = {n: ga_(n, u"G2", u"3 群(Core 自身)")[u"行"] for n in SET_NAMES}
    h4_ok = all(inr(h4[n], H4_G2[n]) for n in SET_NAMES) and all(
        agg[n][u"Core 自身が対応なし(192 行。既定)"] == H4_NOMATCH[n] == agg[n][u"Core 自身が対応なし(192 行。P16 明示)"]
        for n in SET_NAMES)
    h5 = {n: {u"α 型": agg[n][u"注入で Core(α 型)が GROUNDED"], u"Core 自身": agg[n][u"注入で Core 自身が GROUNDED"]}
          for n in SET_NAMES}
    h5_ok = all(h5[n][k][u"分子"] == 0 and h5[n][k][u"分母"] == N_INJ for n in SET_NAMES for k in h5[n])
    h6 = {n: agg[n][u"席が迷った注入"][u"Core 自身が VALUE_MISMATCH で止めた"] for n in SET_NAMES}
    h6_ok = all(h6[n][u"分母"] == FACT_HOLD_INJ[n] and inr(h6[n][u"分子"], H6[n]) for n in SET_NAMES)
    h7_ok = all(contrast[n][u"P16 明示で回した Core が記録の材料の Core と全行一致(192 行)"]
                and not contrast[n][u"GROUNDED の集合: 既定 と P16 で違う行"] for n in SET_NAMES)
    h8 = {n: agg[n][u"H の確認(二重確認 + Core のみ確認)"] for n in SET_NAMES}
    # H-8 の「席の 77 より少ない」は gen_c にだけ付く条件(cd8 は幅だけ)
    h8_ok = (inr(h8[u"gen_c"][u"分子"], H8[u"gen_c"]) and h8[u"gen_c"][u"分子"] < FACT_G1[u"gen_c"]
             and inr(h8[u"cd8"][u"分子"], H8[u"cd8"]))
    preds = [
        {u"記号": "H-1", u"予測": u"G1 = gen_c 77・cd8 41。3 群の精度は両集合とも 100 / 100 / 100(α 型・Core 自身とも)",
         u"実測": {n: {u"G1": ga_(n, u"G1")[u"行"],
                      u"精度 α 型 G1/G2/G3": [prec(n, g, u"3 群(α 型)") for g in (u"G1", u"G2", u"G3")],
                      u"精度 Core 自身 G1/G2/G3": [prec(n, g, u"3 群(Core 自身)") for g in (u"G1", u"G2", u"G3")]}
                 for n in SET_NAMES}, u"当たり": bool(h1_ok)},
        {u"記号": "H-2", u"予測": u"G2(α 型、P21)は gen_c 44〜50 / 77、cd8 30〜35 / 41",
         u"実測": {n: frac(h2[n], ga_(n, u"G1")[u"行"]) for n in SET_NAMES}, u"当たり": bool(h2_ok)},
        {u"記号": "H-3", u"予測": u"G3 の Core の state: gen_c 保留 18〜26・VALUE_MISMATCH 7〜11、cd8 保留 5〜10・VALUE_MISMATCH 0〜3。"
                         u"VALUE_MISMATCH の過半は席の側",
         u"実測": {u"G3 の state": h3, u"VALUE_MISMATCH の行(両集合)": n_vm, u"うち席の側": n_seat_side,
                 u"幅の部分": bool(h3_range), u"読みの部分(過半が席の側。人の読み)": h3_read},
         u"当たり": h3_ok},
        {u"記号": "H-4", u"予測": u"G2(Core 自身、P21)は gen_c 20〜28 / 77、cd8 1〜5 / 41。対応なしは gen_c 80・cd8 51(192 行。P16 と同じ)",
         u"実測": {n: {u"G2": frac(h4[n], ga_(n, u"G1")[u"行"]),
                      u"対応なし(既定)": agg[n][u"Core 自身が対応なし(192 行。既定)"],
                      u"対応なし(P16 明示)": agg[n][u"Core 自身が対応なし(192 行。P16 明示)"]} for n in SET_NAMES},
         u"当たり": bool(h4_ok)},
        {u"記号": "H-5", u"予測": u"注入 64 行で Core(α 型・Core 自身とも)が GROUNDED にする行は gen_c 0 / 64、cd8 0 / 64",
         u"実測": h5, u"当たり": bool(h5_ok)},
        {u"記号": "H-6", u"予測": u"席が迷った注入を Core 自身が VALUE_MISMATCH で止める数は gen_c 0〜3 / 39、cd8 0〜2 / 13",
         u"実測": h6, u"当たり": bool(h6_ok)},
        {u"記号": "H-7", u"予測": u"対照 P16 は材料の Core と全 384 行一致。P21 と P16 の GROUNDED の集合は同じ(差 0 行)",
         u"実測": {n: {u"P16 と材料の Core が全行一致": contrast[n][u"P16 明示で回した Core が記録の材料の Core と全行一致(192 行)"],
                      u"GROUNDED の集合の差の行": len(contrast[n][u"GROUNDED の集合: 既定 と P16 で違う行"])}
                 for n in SET_NAMES}, u"当たり": bool(h7_ok)},
        {u"記号": "H-8", u"予測": u"H の確認(二重 + Core のみ)は gen_c で席の 77 より少ない 44〜53、cd8 で 30〜40",
         u"実測": h8, u"当たり": bool(h8_ok)}]

    rec = {
        u"step": u"**席と Core の一致の信頼 段 1。0 USD・席は呼ばない・通信しない・engine 0 行**",
        u"seal": SEAL, u"seal の commit": SEAL_COMMIT,
        u"環境": env, u"入力の sha256(読むだけ。1 文字も直していない)": inputs,
        u"engine の留め": engine_pins(),
        u"行": rows_all,
        u"集計": agg,
        u"VALUE_MISMATCH の行(α 型・G3。読みの材料つき)": vm_view,
        u"対照(P16 明示)": contrast,
        u"**予測 H-1〜H-8**": preds,
        u"所要秒": {u"α 型と Core 自身の当て直し": round(t_run, 1), u"全体": round(time.time() - t_start, 1)},
        "limits": [
            u"精度の物差しは『注入か』だけ。無改変の行の値が正しいことは前提で測っていない",
            u"G1 に注入が 0 件なので、3 群の精度の差は測れない(100 / 100 / 100 は『差が無かった』ではなく『差を測れる標本が無い』)",
            u"席は 1 席 × 1 便の答え。席の揺れは測らない",
            u"α 型は席の参照先に依る。席が参照先を出さない行には効かない。Core 自身の『対応なし』は行 ↔ claim の写像の限界を含む",
            u"α-2 の読み(席の側か Core の側か)は記録の外の人の読み。門で縛れない",
            u"cd8 の材料は P16 の記録の材料(Core 自身を既定に当て直した値は本記録にだけ在る)"]}
    C1._dump(rec, a.out)
    print(u"=== 席と Core の一致の信頼 段 1(0 USD)===")
    for pr in preds:
        print(u"  %-4s %s" % (pr[u"記号"], {True: u"当たり", False: u"**外れ**", None: u"(読みを待つ)"}[pr[u"当たり"]]),
              json.dumps(pr[u"実測"], ensure_ascii=False)[:260])
    print("->", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
