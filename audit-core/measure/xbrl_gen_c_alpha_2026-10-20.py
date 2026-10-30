# -*- coding: utf-8 -*-
u"""汎化 C 追記 3(改善 2・α)の段 α-B(封 `docs/XBRL_GENERALITY_SEAL_2026-10-20.md` 追記 3 の C-0〜C-5)。

**席(LLM)が名指した参照先を Core が検算して、席の確信を裏づける/止める。席は 1 回も呼ばない。通信しない。
``core/``・``adapters/`` は 0 行。** 席の答え(f0b7140)・C0 の記録・P20 の記録・C1 の記録・cd8 の答えと材料は読むだけ。

C1 の module(``measure/xbrl_gen_c1_2026-10-20.py``)と cd8 の採点 module(``measure/xbrl_cd_score_2026-10-17.py``)は
**書き直さず import する**。``engine_stage`` は「席が名指した**注入**の行」しか回さないので、無改変の行にも回せるよう、
その**組み立て(spec の作り・``verify_external(spec, period_pair=True)``・対照・露出の記録)を 1 行ずつ同じに**
``engine_item`` に写した。注入 25 行は C1-3 の記録と一致することを確かめる(対照 α-C1)。

  α-1  無改変 128 行のうち 席 A が ``確認済み`` + 参照先の行(77)に engine を当てて state を数える
  α-2  VALUE_MISMATCH の行ごとに、読みの材料(材料の値・単位・抜粋、席の参照先、参照先の fact、同じ要素の他の
       期間・枠の fact、値が合う他の要素)を並べる。**読み(席の側か Core の側か)は記録の外**(文書に 1 件ずつ)
  α-3  腕 A+α = 席が ``確認済み`` + 参照先で engine が VALUE_MISMATCH なら ``判定できない`` に下げる
       (参照先は外す。``誤りが在る`` には上書きしない)。4 つの数 + 偽警報を A と並べる(同じ ``SC.tally``)
  α-4  材料の「席の前に出せる分」を profile P20 で作り直し(task file の sha256 は不変であることを確かめる)、
       席が ``判定できない`` の 90 行で Core-P が参照先を出す行を数える。注入の行で Core-P(P20)の参照先を engine に当てる

**数を見る前に決めた読み方(封の字で 1 通りに決まらなかった所)**

  * α-3 の「注入 25 行も同じ規則」: 規則は ``席が 確認済み + 参照先``の行に掛かる。注入 25 行は席が ``誤りが在る`` なので、
    規則は掛からず席のまま(= 25 行の A+α の腕は A と同じ)。C1-3 の state は、25 行に ``確認済み`` が無いこと(= 規則が
    掛かる行が 0)の根拠として記録に並べる。S-4 の「誤認定 4・特定 16 / 20 のまま」は、25 行の参照先を外さない読みと整合する。
  * 下げた行の腕は ``判定 = 判定できない``・``参照先 = None``(S-4 の「誤認定の分母『参照先を出した件』から外れる」と
    「保留は A の 90 から VM の分だけ増える」を満たす読み)。
  * S-C1 の「その fact 自身の値」は C1-3 の対照と同じ作り(金額の単位の行: ``single_value`` に fact の値 / 倍率)。
    率の行・単位が無い行は「fact 自身の値」を C1-3 の作りでは当てられない(``single_value`` は金額の単位を要る)。
    **当てられなかった行は数えて記録に出し、S-8 は 77 / 77 の字面で判定する**(補助: 率の行に engine 自身の
    ``recomputed`` を返した対照を別欄に置く。封の外)。
  * α-4 の「Core-P」は材料の ``席の前に出せる分`` の ``Core``(``core_pointer_say`` = 止めても pointers を読む)の参照先。
  * S-3 は読み(文書)で判定する。記録は ``当たり: null``。S-9 の覆い・pytest の部分は文書で判定する。

    cd audit-core
    TMPDIR=<scratchpad> python3 measure/xbrl_gen_c_alpha_2026-10-20.py [--out PATH]
"""
import argparse
import collections
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


#: C1 の module(書き直さない)。cd8 の材料・採点・C0 の実物は C1 経由で同じ実体を使う。
C1 = _mod("measure/xbrl_gen_c1_2026-10-20.py", "gen_c1_for_alpha")
MB, SC, G0 = C1.MB, C1.SC, C1.G0
VE, H, I, ED, RS, core = C1.VE, C1.H, C1.I, C1.ED, C1.RS, C1.core

SEAL = "docs/XBRL_GENERALITY_SEAL_2026-10-20.md 追記 3"
GEN = C1.GEN
CD8 = C1.CD8
OUT = os.path.join(GEN, "alpha_2026-10-20.json")
C0_REC = os.path.join(GEN, "c0_2026-10-20.json")
C0P20_REC = os.path.join(GEN, "c0_p20_2026-10-20.json")
C1_REC = C1.GEN_C1
GEN_MAT = C1.GEN_MAT
GEN_ANS = C1.GEN_ANS
GEN_DRAW = C1.GEN_DRAW
CD8_MAT = C1.CD8_MAT
CD8_ANS = C1.CD8_ANS
EIGHT = ["S100Z0OS", "S100YYN7", "S100YYT8", "S100Z42X", "S100YYT4", "S100Z4GF", "S100Z4J8", "S100YYUD"]

#: 封 追記 3 C-3 の幅(字で留める。封の字と合わせてある)。
S1_RANGE = (50, 70)            # GROUNDED / 77
S2_VM_RANGE = (3, 15)          # VALUE_MISMATCH / 77
S2_HOLD_RANGE = (0, 12)        # UNPROVABLE + POINTER_NOT_FOUND / 77
S4_WRONG = 4                   # A+α の誤認定(A と同じ 4)
S4_MISS = 0
S4_IDENT = 16                  # 特定 16 / 20 のまま
S4_HOLD_A = 90                 # A の保留
S6_RANGE = (10, 40)            # 席が迷った 90 行で Core-P(P20)が参照先を出す行
#: 封 C-0 の字で留めた分母(C1 の記録から。ここに字で持ち、実測と突き合わせる)
N_PLAIN = 128
N_NAMED_CONFIRMED = 77
N_NAMED_CONFIRMED_BY_DOC = {"S100Z0OS": 3, "S100YYN7": 14, "S100YYT8": 1, "S100Z42X": 14,
                            "S100YYT4": 15, "S100Z4GF": 9, "S100Z4J8": 15, "S100YYUD": 6}
N_INJ_NAMED = 25
N_HOLD_PLAIN, N_HOLD_INJ = 51, 39
#: S-C2 の期待(cd8 の A。K-C2 と同じ数)
KC2_EXPECT = C1.KC2_EXPECT

SIB_CAP = 40
VALMATCH_CAP = 12


def pct(a, b):
    return None if not b else round(100.0 * a / b, 1)


def frac(a, b):
    return {u"分子": a, u"分母": b, u"率": pct(a, b)}


def base_dir():
    tmp = os.environ.get("TMPDIR")
    if not tmp:
        raise SystemExit(u"**TMPDIR が未設定。中間 file を repo の外に置くため、scratchpad を TMPDIR に向ける**")
    root = os.path.realpath(os.path.join(tmp, "gen_c_alpha"))
    if root.startswith(os.path.realpath(ROOT) + os.sep):
        raise SystemExit(u"**中間 file の置き場が repo の中。止める: %s**" % root)
    return root


# ------------------------------------------------------------------ 1 行の engine(C1 の engine_stage の組み立てを 1 行ずつ同じに)
class DocCtx(object):
    def __init__(self, doc):
        self.doc = doc
        zb = io.open(ED.cache_path(doc), "rb").read()
        inst = I.load_instance(zb)
        self.facts, self.contexts = inst["facts"], inst["contexts"]
        self.by_loc, self.by_norm = G0._mk_index(self.facts)


def ctx_view(contexts, cid):
    c = contexts.get(cid) or {}
    per = c.get("instant") if c.get("instant") else u"%s〜%s" % (c.get("start"), c.get("end"))
    return {u"context": cid, u"期間": per, u"軸": [list(a) for a in (c.get("axes") or [])]}


def fact_view(f, contexts, claim_base, tol):
    d = ctx_view(contexts, f["context"])
    d.update({u"name": f["name"], u"unit": f.get("unit"), u"value": f.get("value"), u"decimals": f.get("decimals")})
    if claim_base is not None and f.get("value") is not None:
        diff = f["value"] - claim_base
        d[u"主張の値(基準単位)との差"] = diff
        d[u"差の絶対値が 1 単位(UNIT_SCALE)未満"] = abs(diff) < tol
    return d


def reading_material(dc, f, m, unit, is_ratio, tol, scale, derived):
    u"""α-2: 読みの材料。**読みそのものは書かない**(席の側か Core の側かは文書)。"""
    claim_base = None if is_ratio else float(m[u"値"]) * scale
    out = {u"材料の値": m[u"値"], u"材料の単位": unit, u"数の字面": m[u"数の字面"], u"抜粋": m[u"抜粋"],
           u"主張の値(基準単位。率の行は None)": claim_base}
    if f is None:
        out[u"参照先の fact"] = None
        return out
    out[u"参照先の fact"] = fact_view(f, dc.contexts, claim_base, tol)
    sibs = [g for g in dc.facts if g["name"] == f["name"] and g["context"] != f["context"]]
    out[u"同じ要素の他の期間・枠の fact の件数"] = len(sibs)
    out[u"同じ要素の他の期間・枠の fact(先頭 %d 件まで。context 順)" % SIB_CAP] = [
        fact_view(g, dc.contexts, claim_base, tol) for g in sorted(sibs, key=lambda g: g["context"])[:SIB_CAP]]
    if is_ratio:
        by_name_ctx = {(g["name"], g["context"]): g for g in dc.facts}
        dv = []
        for d in (derived or []):
            nm, _, cx = str(d).partition("@")
            g = by_name_ctx.get((nm, cx))
            dv.append(fact_view(g, dc.contexts, None, tol) if g else {u"name": nm, u"context": cx, u"解けない": True})
        out[u"PP が派生させた参照先の fact"] = dv
    if claim_base is not None:
        # 同じ枠(次元)で期間だけ違う fact との差が主張の値に合うか(増減額の文の機械的な目印。読みそのものではない)
        pdiff = []
        for g in sibs:
            if g.get("value") is None or H.dim_of(g["context"]) != H.dim_of(f["context"]):
                continue
            delta = abs(f["value"] - g["value"]) if f.get("value") is not None else None
            if delta is not None and abs(delta - abs(claim_base)) <= tol:
                pdiff.append({u"context": g["context"], u"その fact の値": g["value"], u"2 つの fact の差の絶対値": delta,
                              u"主張の値(基準単位)": abs(claim_base)})
        out[u"同じ枠で期間だけ違う fact との差が主張の値に合う(差の差が 1 単位以内)"] = pdiff
        same = [g for g in sibs if g.get("value") is not None and abs(g["value"] - claim_base) < tol]
        out[u"同じ要素の他の fact で差が 1 単位未満の件数"] = len(same)
        other = [g for g in dc.facts if g["name"] != f["name"] and g.get("value") is not None
                 and abs(g["value"] - claim_base) < tol]
        out[u"値が合う他の要素の fact の件数"] = len(other)
        out[u"値が合う他の要素の fact(先頭 %d 件まで)" % VALMATCH_CAP] = [
            u"%s@%s" % (g["name"], g["context"]) for g in other[:VALMATCH_CAP]]
    return out


def engine_item(dc, registry, m, raw, tag, claim_prefix, with_reading=False):
    u"""材料の 1 行 ``m`` と参照先の字 ``raw`` を engine に当てる。**C1 の ``engine_stage`` の組み立てと同じ。**"""
    f, how = G0._resolve(dc.by_loc, dc.by_norm, raw)
    loc = ("%s@%s" % (f["name"], f["context"])) if f else G0._loc_of(raw)
    unit, val = m[u"単位"], m[u"値"]
    is_ratio = unit in VE.RATIO_UNITS
    sign = G0.R1.sign_from_text(m[u"抜粋"], m[u"数の字面"]) if is_ratio else None
    spec = {"kind": "ratio_change" if is_ratio else "single_value", "value": val, "unit": unit, "pointers": [loc]}
    if is_ratio:
        spec["sign"] = sign
    cid = "%s-%s-%s" % (claim_prefix, dc.doc, m["id"])
    on = VE.verify_external(spec, dc.facts, dc.contexts, registry, claim_id=cid, period_pair=True)
    off = VE.verify_external(spec, dc.facts, dc.contexts, registry, claim_id=cid, period_pair=False)
    tol = VE.tol_of(unit)
    if f is not None:
        u_fire, ucc, ufc = H.unit_mismatch(unit, f)
        d_sibs = H.dimension_siblings(dc.facts, f, tol)
        p_sibs = H.period_siblings(dc.facts, f, tol)
    else:
        u_fire, ucc, ufc, d_sibs, p_sibs = False, None, None, [], []
    # 対照 S-C1: 同じ参照先に「その fact 自身の値」を当てる(金額の単位の行だけ。C1-3 と同じ作り)
    ctrl = None
    ctrl_why = None
    scale = float(G0.V_UNIT_SCALE.get(unit, 1))
    if f is None:
        ctrl_why = u"参照先が解けない"
    elif f.get("value") is None:
        ctrl_why = u"fact に値が無い"
    elif is_ratio:
        ctrl_why = u"率の行(ratio_change に「fact 自身の値」は定義できない)"
    elif unit not in H.CLAIM_CLASS or H.CLAIM_CLASS[unit] != "JPY":
        ctrl_why = u"金額の単位でない(単位 %r)" % (unit,)
    if ctrl_why is None:
        csp = {"kind": "single_value", "value": float(f["value"]) / scale, "unit": unit, "pointers": [loc]}
        co = VE.verify_external(csp, dc.facts, dc.contexts, registry, claim_id=cid + "-ctl", period_pair=True)
        ctrl = {u"state": co["state"], u"reason": co["reason"], u"held": co["held"]}
    # 補助(封の外): 率の行に engine 自身の recomputed を返す(配線の確認。独立した証拠ではない)
    aux = None
    if is_ratio and f is not None and on.get("recomputed") is not None:
        asp = dict(spec)
        asp["value"] = float(on["recomputed"])
        ao = VE.verify_external(asp, dc.facts, dc.contexts, registry, claim_id=cid + "-aux", period_pair=True)
        aux = {u"返した値": asp["value"], u"state": ao["state"], u"reason": ao["reason"]}
    item = {
        u"出どころ": tag, u"doc": dc.doc, u"id": m["id"], u"注入か": bool(m.get(u"**注入**")),
        u"参照先(原文)": raw, u"参照先の解き方": how,
        u"材料の値": val, u"材料の単位": unit, u"数の字面": m[u"数の字面"], u"抜粋": m[u"抜粋"],
        u"spec の kind": spec["kind"], u"符号": sign,
        u"参照先の fact の単位": (f or {}).get("unit"), u"参照先の fact の値": (f or {}).get("value"),
        u"参照先の fact の context": (f or {}).get("context"),
        u"engine の state": on["state"], u"engine の reason": on["reason"], u"engine の recomputed": on["recomputed"],
        u"held(製品の経路)": on["held"], u"hold_rules(製品の経路)": list(on["hold_rules"]),
        u"derived_pointers": on["derived_pointers"], u"direction_checked": on["direction_checked"],
        u"露出 U(単位の種類が違う)": bool(u_fire), u"露出 (d)(同額の次元兄弟)": bool(d_sibs),
        u"露出 P(同額の期間兄弟)": bool(p_sibs),
        u"PP の行": is_ratio,
        u"engine(PP あり)": G0.keyed(on), u"engine(PP なし)": G0.keyed(off),
        u"対照(その fact 自身の値)": ctrl, u"対照を当てなかった理由": ctrl_why,
        u"補助(率の行に recomputed を返した。封の外)": aux}
    if with_reading and on["state"] == "VALUE_MISMATCH":
        item[u"読みの材料(α-2)"] = reading_material(dc, f, m, unit, is_ratio, tol, scale, on["derived_pointers"])
    return item


def answers_by_id(ans_dir, doc):
    ans = C1._load(os.path.join(ans_dir, "%s_answer.json" % doc))
    by_id = {}
    for r in (ans if isinstance(ans, list) else ans.get(u"answers", [])):
        if isinstance(r, dict) and r.get("id"):
            by_id[str(r["id"]).strip()] = r
    return by_id


def collect_named(mat_path, ans_dir, work, registry, seed, with_reading=True):
    u"""席が参照先を出した行(判定語は問わない)の全部に engine を当てる。無改変の行も入る。"""
    mat = C1._load(mat_path)
    items, per_doc = [], {}
    for p in mat[u"書類ごと"]:
        doc = p["docID"]
        by_id = answers_by_id(ans_dir, doc)
        rows, _chosen = C1.rebuild_rows(doc, work, seed, p)
        dc = DocCtx(doc)
        n = collections.Counter()
        for m in rows:
            seat = SC.seat_row(by_id.get(m["id"]))
            n[(u"注入" if m.get(u"**注入**") else u"無改変", seat[u"判定"])] += 1
            if seat[u"判定"] == SC.MISSING or seat[u"参照先"] is None:
                continue
            raw = str(by_id[m["id"]][u"参照先"]).strip()
            it = engine_item(dc, registry, m, raw, u"席 A の参照先", "AL1", with_reading=with_reading)
            it[u"席の判定"] = seat[u"判定"]
            it[u"席の参照先(正規化)"] = seat[u"参照先"]
            items.append(it)
        per_doc[doc] = {u"行": len(rows), u"種類別": {u"%s × %s" % k: v for k, v in sorted(n.items())}}
    return items, per_doc


def state_counts(items):
    c = collections.Counter(x[u"engine の state"] for x in items)
    return dict(sorted(c.items()))


def alpha_score(score_rows, items):
    u"""α-3。``SC.tally`` を変えずに、腕 A の位置に A+α を入れて数える(他の腕はそのまま)。"""
    state_of = {(x[u"doc"], x[u"id"]): x[u"engine の state"] for x in items}
    rows2, lowered, applicable = [], [], 0
    for r in score_rows:
        r2 = dict(r)
        r2[u"腕"] = dict(r[u"腕"])
        a = dict(r[u"腕"]["A"])
        seat = r[u"席"]
        if seat[u"判定"] == u"確認済み" and seat[u"参照先"] is not None:
            applicable += 1
            st = state_of.get((r["doc"], r["id"]))
            if st is None:
                raise SystemExit(u"**engine の state が無い(確認済み + 参照先の行): %s %s。止める**" % (r["doc"], r["id"]))
            if st == "VALUE_MISMATCH":
                a = {u"判定": u"判定できない", u"参照先": None, u"足した": True}
                lowered.append({u"doc": r["doc"], u"id": r["id"], u"注入か": r[u"注入か"]})
        arm = {u"判定": a[u"判定"], u"参照先": a[u"参照先"], u"足した": a.get(u"足した", False)}
        arm[u"判定結果"] = SC.verdict(arm, r[u"正解"], r[u"注入か"])
        r2[u"腕"]["A"] = arm
        rows2.append(r2)
    return SC.tally(rows2)["A"], lowered, applicable


def four(t):
    return {u"誤認定": t[u"誤認定"], u"見逃し": t[u"見逃し"], u"正しい参照先の特定": t[u"正しい参照先の特定"],
            u"保留": t[u"保留"], u"偽警報": t[u"偽警報(**判定には使わない**)"], u"軸A 停止判定": t[u"軸A 停止判定"],
            u"照合器を足した行": t[u"照合器を足した行"], u"欠け": t[u"欠け"]}


# ------------------------------------------------------------------ α-4(P20 の材料)
def make_material(profile, work, out_path):
    old = MB.PROFILE
    MB.PROFILE = profile
    try:
        rec = C1.run_material(GEN_DRAW, work, out_path)
    finally:
        MB.PROFILE = old
    if rec.get("profile") != profile:
        raise SystemExit(u"**材料の profile が差し替わっていない: %r != %r**" % (rec.get("profile"), profile))
    return rec


def core_p_pointers(mat_rec):
    out = {}
    for p in mat_rec[u"書類ごと"]:
        for rid, pre in p[u"席の前に出せる分"].items():
            out[(p["docID"], rid)] = pre["Core"]
    return out


def material_invariants(old, new):
    u"""task file の sha256・行 id・注入 id・注入か・正解が、P16 の材料と P20 の材料で同じか。"""
    bad = []
    for po, pn in zip(old[u"書類ごと"], new[u"書類ごと"]):
        d = po["docID"]
        if po["docID"] != pn["docID"]:
            bad.append((d, u"docID の並び"))
            continue
        if po[u"材料"][u"sha256"] != pn[u"材料"][u"sha256"]:
            bad.append((d, u"task の sha256"))
        if po[u"注入"][u"ids"] != pn[u"注入"][u"ids"]:
            bad.append((d, u"注入の id"))
        if sorted(po[u"席の前に出せる分"]) != sorted(pn[u"席の前に出せる分"]):
            bad.append((d, u"行の id"))
        for rid, a in po[u"席の前に出せる分"].items():
            b = pn[u"席の前に出せる分"][rid]
            if a[u"注入か"] != b[u"注入か"] or a[u"正解"] != b[u"正解"]:
                bad.append((d, rid, u"注入か/正解"))
    return bad


# ------------------------------------------------------------------ 本体
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    if os.path.exists(a.out):
        raise SystemExit(u"既に在る: %s(採り直さない)" % a.out)
    t_start = time.time()
    env = C1.no_keys()
    base = base_dir()
    work_gen = os.path.join(base, "work_gen")
    work_cd8 = os.path.join(base, "work_cd8")
    work_p16 = os.path.join(base, "work_p16")
    work_p20 = os.path.join(base, "work_p20")
    for d in (work_gen, work_cd8, work_p16, work_p20):
        os.makedirs(d, exist_ok=True)
    tmpd = tempfile.mkdtemp(prefix="alpha_", dir=base)

    inputs = {
        u"席の答え(f0b7140)": {d: C1.sha_file(os.path.join(GEN_ANS, "%s_answer.json" % d)) for d in EIGHT},
        u"材料 material_2026-10-20.json": C1.sha_file(GEN_MAT),
        u"C0 の記録 c0_2026-10-20.json": C1.sha_file(C0_REC),
        u"P20 の記録 c0_p20_2026-10-20.json": C1.sha_file(C0P20_REC),
        u"C1 の記録 c1_2026-10-20.json": C1.sha_file(C1_REC),
        u"cd8 の答え": {os.path.basename(p): C1.sha_file(os.path.join(CD8_ANS, p))
                      for p in sorted(os.listdir(CD8_ANS)) if p.endswith("_answer.json")},
        u"cd8 の材料 material_2026-10-17.json": C1.sha_file(CD8_MAT)}

    seed, _meta = MB.IJ.verify_seed_sealed(MB.SEED_FILE)
    registry = RS.register_all(core.Registry.default())
    c1rec = C1._load(C1_REC)

    # ---- 採点(A の 4 つの数を C1 の記録と突き合わせる。同じ関数・同じ答え)
    t0 = time.time()
    score = C1.score_run(GEN_MAT, GEN_ANS, os.path.join(tmpd, "gen_score.json"))
    score_rows = score["rows"]
    a_repro = score[u"採点"]["A"] == c1rec[u"採点"]["A"] and len(score_rows) == len(c1rec["rows"]) == 192

    # ---- α-1 / α-2: 席が参照先を出した 102 行(無改変 77 + 注入 25)
    items, per_doc = collect_named(GEN_MAT, GEN_ANS, work_gen, registry, seed, with_reading=True)
    plain77 = [x for x in items if not x[u"注入か"] and x[u"席の判定"] == u"確認済み"]
    plain_other = [x for x in items if not x[u"注入か"] and x[u"席の判定"] != u"確認済み"]
    inj25 = [x for x in items if x[u"注入か"]]
    by_doc77 = collections.Counter(x["doc"] for x in plain77)
    n_expect_ok = (len(plain77) == N_NAMED_CONFIRMED and dict(by_doc77) == N_NAMED_CONFIRMED_BY_DOC
                   and len(inj25) == N_INJ_NAMED and not plain_other)
    st77 = state_counts(plain77)
    hold77 = st77.get("UNPROVABLE", 0) + st77.get("POINTER_NOT_FOUND", 0)
    vm77 = [x for x in plain77 if x[u"engine の state"] == "VALUE_MISMATCH"]
    ratio77 = [x for x in plain77 if x[u"PP の行"]]
    unitless77 = [x for x in plain77 if x[u"材料の単位"] is None]
    money77 = [x for x in plain77 if not x[u"PP の行"] and x[u"材料の単位"] is not None]
    alpha1 = {
        u"分母(席 A が 確認済み + 参照先の無改変の行)": len(plain77),
        u"分母の出どころ": u"c1_2026-10-20.json の rows(席 A)。封 C-0 の 77 と書類ごとの数を字で留めて突き合わせた",
        u"封の 77 と書類ごとの数が一致": n_expect_ok, u"書類ごと": dict(by_doc77),
        u"state の分布": st77,
        u"GROUNDED": frac(st77.get("GROUNDED", 0), len(plain77)),
        u"VALUE_MISMATCH": frac(st77.get("VALUE_MISMATCH", 0), len(plain77)),
        u"保留(UNPROVABLE + POINTER_NOT_FOUND)": frac(hold77, len(plain77)),
        u"state が 4 つの外": {k: v for k, v in st77.items()
                           if k not in ("GROUNDED", "VALUE_MISMATCH", "UNPROVABLE", "POINTER_NOT_FOUND")},
        u"書類ごとの state": {d: dict(sorted(collections.Counter(
            x[u"engine の state"] for x in plain77 if x["doc"] == d).items())) for d in EIGHT},
        u"行の種類ごとの state": {
            u"率の行(単位 %)": state_counts(ratio77), u"金額の行": state_counts(money77),
            u"単位が無い行": state_counts(unitless77)},
        u"行の種類ごとの件数": {u"率の行": len(ratio77), u"金額の行": len(money77), u"単位が無い行": len(unitless77)},
        u"UNPROVABLE の理由の分布": dict(collections.Counter(
            x[u"engine の reason"] for x in plain77 if x[u"engine の state"] == "UNPROVABLE")),
        u"露出 U / (d) / P": {u"U": sum(1 for x in plain77 if x[u"露出 U(単位の種類が違う)"]),
                           u"(d)": sum(1 for x in plain77 if x[u"露出 (d)(同額の次元兄弟)"]),
                           u"P": sum(1 for x in plain77 if x[u"露出 P(同額の期間兄弟)"]),
                           u"分母": len(plain77)},
        u"held(製品の経路)": sum(1 for x in plain77 if x[u"held(製品の経路)"]),
        u"参照先が解けなかった行": [x["id"] for x in plain77 if x[u"参照先の解き方"] == u"解けない"]}

    # ---- 注入 25 行: C1-3 の記録と一致するか(対照 α-C1)と、規則が掛かる行(席が 確認済み)の有無
    c13_rows = {(r["doc"], r["id"]): r for r in c1rec[u"C1-3"]["rows"]}
    mism_c13 = []
    for x in inj25:
        r = c13_rows.get((x["doc"], x["id"]))
        if r is None or (r[u"engine の state"], r[u"engine の reason"], r[u"engine の recomputed"],
                         r[u"held(製品の経路)"]) != (x[u"engine の state"], x[u"engine の reason"],
                                               x[u"engine の recomputed"], x[u"held(製品の経路)"]):
            mism_c13.append((x["doc"], x["id"]))
    inj25_words = collections.Counter(x[u"席の判定"] for x in inj25)
    alpha_inj = {u"席が 参照先を出した注入の行": len(inj25), u"席の判定語": dict(inj25_words),
                 u"state の分布(この script で当て直した)": state_counts(inj25),
                 u"C1-3 の記録の state の分布": c1rec[u"C1-3"][u"集計"][u"state の分布"],
                 u"C1-3 の rows と state・reason・recomputed・held が違う行": mism_c13,
                 u"規則が掛かる行(席が 確認済み)": inj25_words.get(u"確認済み", 0),
                 u"注": u"25 行は席が 誤りが在る なので規則は掛からず、A+α の腕は A と同じ(読み方は script の先頭)"}

    # ---- α-3
    tA = score[u"採点"]["A"]
    tAa, lowered, applicable = alpha_score(score_rows, items)
    lowered_ids = [(l["doc"], l["id"]) for l in lowered]
    alpha3 = {
        u"規則が掛かる行(席が 確認済み + 参照先)": applicable,
        u"下げた行(VALUE_MISMATCH → 判定できない・参照先を外す)": len(lowered), u"下げた行の ids": lowered,
        u"下げた行のうち注入の行": sum(1 for l in lowered if l[u"注入か"]),
        u"A(席そのまま。採点器の出力)": four(tA), u"A+α": four(tAa),
        u"A の再現(c1 の記録の 採点/A と全欄一致)": a_repro,
        u"保留の増分": tAa[u"保留"][u"分子"] - tA[u"保留"][u"分子"],
        u"誤認定の分母(参照先を出した件)の増分": tAa[u"誤認定"][u"分母(参照先を出した件)"] - tA[u"誤認定"][u"分母(参照先を出した件)"],
        u"note": u"腕の A+α は SC.tally の A の位置に入れて同じ関数で数えた。他の腕・行・正解は触っていない"}

    # ---- S-C3: PP あり/なし
    pp_diff = [x for x in items if x[u"engine(PP あり)"] != x[u"engine(PP なし)"]]
    off_states = collections.Counter()
    for x in plain77:
        off_states[x[u"engine(PP なし)"]["state"]] += 1
    c3 = {u"PP あり/なしで変わった行(席が参照先を出した 102 行のうち)": [(x["doc"], x["id"]) for x in pp_diff],
          u"うち率でない行": [(x["doc"], x["id"]) for x in pp_diff if not x[u"PP の行"]],
          u"無改変 77 行の state(PP なし)": dict(sorted(off_states.items())),
          u"無改変 77 行の state(PP あり)": st77,
          u"率の行(77 行のうち)": len(ratio77)}

    # ---- S-C1
    ctl_rows = [x for x in plain77 if x[u"対照(その fact 自身の値)"] is not None]
    ctl_g = [x for x in ctl_rows if x[u"対照(その fact 自身の値)"][u"state"] == "GROUNDED"]
    no_ctl = [x for x in plain77 if x[u"対照(その fact 自身の値)"] is None]
    aux_rows = [x for x in plain77 if x[u"補助(率の行に recomputed を返した。封の外)"] is not None]
    aux_g = [x for x in aux_rows if x[u"補助(率の行に recomputed を返した。封の外)"][u"state"] == "GROUNDED"]
    c1ctl = {
        u"対照を当てた行": len(ctl_rows), u"GROUNDED": len(ctl_g), u"分母(封の字)": len(plain77),
        u"state の分布(当てた行)": dict(sorted(collections.Counter(
            x[u"対照(その fact 自身の値)"][u"state"] for x in ctl_rows).items())),
        u"当てられなかった行": len(no_ctl),
        u"当てられなかった理由の分布": dict(collections.Counter(x[u"対照を当てなかった理由"] for x in no_ctl)),
        u"当てた行で GROUNDED でなかった行": [(x["doc"], x["id"], x[u"対照(その fact 自身の値)"]) for x in ctl_rows
                                    if x[u"対照(その fact 自身の値)"][u"state"] != "GROUNDED"],
        u"補助(封の外): 率の行に engine 自身の recomputed を返した": {
            u"当てた行": len(aux_rows), u"GROUNDED": len(aux_g),
            u"当てられなかった率の行(recomputed が無い)": len(ratio77) - len(aux_rows),
            u"GROUNDED でなかった行": [(x["doc"], x["id"], x[u"補助(率の行に recomputed を返した。封の外)"])
                                 for x in aux_rows if x[u"補助(率の行に recomputed を返した。封の外)"][u"state"] != "GROUNDED"]},
        u"封の期待": u"GROUNDED 77 / 77"}

    # ---- α-4: P20 の材料
    t0 = time.time()
    mat_p16_new = make_material("P16", work_p16, os.path.join(tmpd, "mat_p16.json"))
    mat_p20 = make_material("P20", work_p20, os.path.join(tmpd, "mat_p20.json"))
    mat_old = C1._load(GEN_MAT)
    t_mat = time.time() - t0
    inv_p20 = material_invariants(mat_old, mat_p20)
    inv_p16 = material_invariants(mat_old, mat_p16_new)
    pre_old = core_p_pointers(mat_old)
    pre_p16 = core_p_pointers(mat_p16_new)
    pre_p20 = core_p_pointers(mat_p20)
    p16_repro = pre_old == pre_p16
    changed = sorted(k for k in pre_old if pre_old[k] != pre_p20[k])
    hold_rows = [r for r in score_rows if r[u"席"][u"判定"] == u"判定できない"]
    hold_plain = [r for r in hold_rows if not r[u"注入か"]]
    hold_inj = [r for r in hold_rows if r[u"注入か"]]

    def pointed(rows, pre):
        return [r for r in rows if pre[(r["doc"], r["id"])]["参照先"] is not None]

    pp20, pp16 = pointed(hold_rows, pre_p20), pointed(hold_rows, pre_old)
    # Core-P(P20) の参照先を engine に当てる(90 行のうち参照先を出した行)
    core_items = []
    for p in mat_p20[u"書類ごと"]:
        doc = p["docID"]
        rows, _chosen = C1.rebuild_rows(doc, work_p20, seed, p)
        dc = DocCtx(doc)
        for m in rows:
            key = (doc, m["id"])
            seat = [r for r in hold_rows if r["doc"] == doc and r["id"] == m["id"]]
            if not seat:
                continue
            ptr = pre_p20[key]["参照先"]
            if ptr is None:
                continue
            it = engine_item(dc, registry, m, ptr, u"Core-P(P20)の参照先", "AL4")
            it[u"Core-P の言うこと"] = pre_p20[key][u"言うこと"]
            it[u"Core 自身の state"] = pre_p20[key].get("state")
            core_items.append(it)
    core_inj = [x for x in core_items if x[u"注入か"]]
    core_plain = [x for x in core_items if not x[u"注入か"]]
    core_inj_g = [x for x in core_inj if x[u"engine の state"] == "GROUNDED"]
    # 注入の行は正解の参照先か(gold)を並べる(P20 の材料の 正解)
    gold_of = {(p["docID"], rid): pre[u"正解"] for p in mat_p20[u"書類ごと"] for rid, pre in p[u"席の前に出せる分"].items()}
    core_inj_view = []
    for x in core_inj:
        g = gold_of[(x["doc"], x["id"])]
        core_inj_view.append({u"doc": x["doc"], u"id": x["id"], u"engine の state": x[u"engine の state"],
                              u"Core-P の参照先": x[u"参照先(原文)"], u"正解の種類": (g or {}).get(u"種類"),
                              u"正解の参照先": (g or {}).get(u"正解"),
                              u"Core 自身の state": x[u"Core 自身の state"]})
    alpha4 = {
        u"席が 判定できない の行": {u"合計": len(hold_rows), u"無改変": len(hold_plain), u"注入": len(hold_inj),
                           u"封の字(51 + 39 = 90)と一致": (len(hold_plain), len(hold_inj)) == (N_HOLD_PLAIN, N_HOLD_INJ)},
        u"席が 判定できない の行の ids": [[r["doc"], r["id"], bool(r[u"注入か"])] for r in hold_rows],
        u"Core-P(P20)が参照先を出す行の ids": [[r["doc"], r["id"]] for r in pp20],
        u"Core-P(P16。材料の記録)が参照先を出す行の ids": [[r["doc"], r["id"]] for r in pp16],
        u"Core-P(P20)が参照先を出す行": frac(len(pp20), len(hold_rows)),
        u"うち無改変": frac(len(pointed(hold_plain, pre_p20)), len(hold_plain)),
        u"うち注入": frac(len(pointed(hold_inj, pre_p20)), len(hold_inj)),
        u"書類ごと(Core-P(P20)が参照先を出す行 / 判定できない の行)": {
            d: [sum(1 for r in pp20 if r["doc"] == d), sum(1 for r in hold_rows if r["doc"] == d)] for d in EIGHT},
        u"Core-P(P16。材料の記録 material_2026-10-20.json)が参照先を出す行": frac(len(pp16), len(hold_rows)),
        u"P16 と P20 で Core の言うことが違う行(192 行のうち)": [list(k) for k in changed],
        u"P16 と P20 で参照先が違う行の件数": len(changed),
        u"材料の不変(P20 の材料 対 P16 の材料: task の sha256・注入 id・行 id・注入か・正解)": {
            u"違った所": inv_p20, u"違った所の件数": len(inv_p20)},
        u"材料の再現(P16 で作り直した材料 対 記録の材料)": {u"席の前に出せる分の Core が全行一致": p16_repro,
                                          u"不変の検査で違った所": inv_p16},
        u"Core-P(P20)の参照先を engine に当てた行": {
            u"合計": len(core_items), u"state の分布": state_counts(core_items),
            u"注入": {u"行": len(core_inj), u"state の分布": state_counts(core_inj),
                    u"GROUNDED(誤りを通した)": {u"件数": len(core_inj_g), u"分母": len(core_inj),
                                          u"ids": [x["id"] for x in core_inj_g]},
                    u"型の内訳": dict(collections.Counter(
                        (gold_of[(x["doc"], x["id"])] or {}).get(u"種類") for x in core_inj))},
            u"無改変": {u"行": len(core_plain), u"state の分布": state_counts(core_plain),
                      u"note": u"無改変の行に正解は無い。GROUNDED は『Core の名指しで値が合った』であって参照先が正しい証明ではない"}},
        u"注入の行の明細": core_inj_view,
        u"note": u"P16 の材料の Core-P の数は記録 material_2026-10-20.json の席の前に出せる分から数えた(封の『P16 の材料では 4』と並べる)"}

    # ---- S-C2: cd8
    work8 = work_cd8
    t0 = time.time()
    items8, per_doc8 = collect_named(CD8_MAT, CD8_ANS, work8, registry, seed, with_reading=False)
    score8 = C1.score_run(CD8_MAT, CD8_ANS, os.path.join(tmpd, "cd8_score.json"))
    rows8 = score8["rows"]
    tA8 = score8[u"採点"]["A"]
    tAa8, lowered8, applicable8 = alpha_score(rows8, items8)
    conf8 = [x for x in items8 if x[u"席の判定"] == u"確認済み" and not x[u"注入か"]]
    conf8_inj = [x for x in items8 if x[u"席の判定"] == u"確認済み" and x[u"注入か"]]
    kc2_ok = all((tA8[k][u"分子"], tA8[k][[kk for kk in tA8[k] if kk.startswith(u"分母")][0]]) == v
                 for k, v in KC2_EXPECT.items())
    cd8_block = {
        u"行の合計": len(rows8), u"欠け": tA8[u"欠け"],
        u"完走": len(rows8) == 192 and applicable8 == len(conf8) + len(conf8_inj),
        u"A の再現(K-C2 の 4 つの数: 誤認定 8 / 85・見逃し 0 / 64・特定 35 / 50・保留 107 / 192)": kc2_ok,
        u"席が参照先を出した行(判定語は問わない)": len(items8),
        u"書類ごとの行・席の判定語": per_doc8,
        u"α-1: 確認済み + 参照先の無改変の行": {u"行": len(conf8), u"state の分布": state_counts(conf8),
                                     u"VALUE_MISMATCH": frac(state_counts(conf8).get("VALUE_MISMATCH", 0), len(conf8)),
                                     u"GROUNDED": frac(state_counts(conf8).get("GROUNDED", 0), len(conf8))},
        u"α-1: 確認済み + 参照先の注入の行(= 見逃し)": {u"行": len(conf8_inj), u"state の分布": state_counts(conf8_inj)},
        u"全 state(席が参照先を出した行の全部)": state_counts(items8),
        u"A": four(tA8), u"A+α": four(tAa8),
        u"規則が掛かる行": applicable8, u"下げた行": len(lowered8), u"下げた行の ids": lowered8,
        u"保留の増分": tAa8[u"保留"][u"分子"] - tA8[u"保留"][u"分子"],
        u"VALUE_MISMATCH の行(無改変)": [
            {u"doc": x["doc"], u"id": x["id"], u"材料の値": x[u"材料の値"], u"材料の単位": x[u"材料の単位"],
             u"抜粋": x[u"抜粋"], u"席の参照先": x[u"参照先(原文)"], u"参照先の fact の値": x[u"参照先の fact の値"],
             u"engine の recomputed": x[u"engine の recomputed"], u"PP の行": x[u"PP の行"]}
            for x in conf8 if x[u"engine の state"] == "VALUE_MISMATCH"]}
    t_cd8 = time.time() - t0

    pins = G0.engine_pins()

    # ---- 予測 S-1〜S-9
    g_n = st77.get("GROUNDED", 0)
    vm_n = st77.get("VALUE_MISMATCH", 0)
    s4_ok = (tAa[u"誤認定"][u"分子"] == S4_WRONG and tAa[u"見逃し"][u"分子"] == S4_MISS
             and tAa[u"正しい参照先の特定"][u"分子"] == S4_IDENT
             and tAa[u"保留"][u"分子"] == S4_HOLD_A + vm_n)
    s6_n = len(pp20)
    c2_ok = bool(cd8_block[u"完走"] and cd8_block[u"欠け"] == 0 and kc2_ok)
    c1_ok = len(ctl_g) == len(plain77) == N_NAMED_CONFIRMED
    c3_ok = len(c3[u"うち率でない行"]) == 0
    s9_pins = pins[u"一致"]
    preds = [
        {u"記号": "S-1", u"予測": u"α-1: GROUNDED 50〜70 / 77(65〜91%)",
         u"実測": {u"GROUNDED": g_n, u"分母": len(plain77), u"率": pct(g_n, len(plain77))},
         u"当たり": S1_RANGE[0] <= g_n <= S1_RANGE[1]},
        {u"記号": "S-2", u"予測": u"α-1: VALUE_MISMATCH 3〜15 / 77、保留(UNPROVABLE + POINTER_NOT_FOUND)0〜12 / 77",
         u"実測": {u"VALUE_MISMATCH": vm_n, u"保留": hold77, u"分母": len(plain77)},
         u"当たり": (S2_VM_RANGE[0] <= vm_n <= S2_VM_RANGE[1]) and (S2_HOLD_RANGE[0] <= hold77 <= S2_HOLD_RANGE[1])},
        {u"記号": "S-3", u"予測": u"α-2: VALUE_MISMATCH のうち『席の参照先が違う』が半分以上",
         u"実測": {u"VALUE_MISMATCH の行": vm_n, u"note": u"読みは文書(記録の外・門で縛れない)"}, u"当たり": None},
        {u"記号": "S-4", u"予測": u"α-3: A+α の誤認定 4・見逃し 0・特定 16 / 20・保留は 90 + S-2 の VM",
         u"実測": {u"誤認定": tAa[u"誤認定"][u"分子"], u"見逃し": tAa[u"見逃し"][u"分子"],
                 u"特定": tAa[u"正しい参照先の特定"][u"分子"], u"保留": tAa[u"保留"][u"分子"],
                 u"期待した保留": S4_HOLD_A + vm_n}, u"当たり": s4_ok},
        {u"記号": "S-5", u"予測": u"α-3: A+α の偽警報 0 / 128",
         u"実測": tAa[u"偽警報(**判定には使わない**)"], u"当たり": tAa[u"偽警報(**判定には使わない**)"][u"分子"] == 0},
        {u"記号": "S-6", u"予測": u"α-4: 席が迷った 90 行で Core-P(P20)が参照先を出す行 10〜40 / 90",
         u"実測": {u"Core-P(P20)が参照先を出す行": s6_n, u"分母": len(hold_rows),
                 u"P16 の材料": len(pp16),
                 u"補助(封の外): 言うことが『一意でない』(参照先 2 本以上)の行": sum(
                     1 for r in hold_rows if pre_p20[(r["doc"], r["id"])][u"言うこと"] == u"一意でない")},
         u"当たり": S6_RANGE[0] <= s6_n <= S6_RANGE[1]},
        {u"記号": "S-7", u"予測": u"α-4: 注入 39 行で Core-P(P20)の参照先に engine を当てて GROUNDED 0",
         u"実測": {u"GROUNDED": len(core_inj_g), u"engine を当てた注入の行": len(core_inj), u"注入の行": len(hold_inj),
                 u"空振り(engine を当てた注入の行が 0)": len(core_inj) == 0,
                 u"注入の行の Core-P の言うこと": dict(collections.Counter(
                     pre_p20[(r["doc"], r["id"])][u"言うこと"] for r in hold_inj))},
         u"当たり": len(core_inj_g) == 0},
        {u"記号": "S-8", u"予測": u"対照 S-C1 77 / 77・S-C2 完走・S-C3 率でない行の差 0",
         u"実測": {u"S-C1": {u"GROUNDED": len(ctl_g), u"当てた行": len(ctl_rows), u"分母": len(plain77), u"一致": c1_ok},
                 u"S-C2": {u"完走・欠け 0・A の再現": c2_ok},
                 u"S-C3": {u"率でない行の差": len(c3[u"うち率でない行"]), u"一致": c3_ok}},
         u"当たり": bool(c1_ok and c2_ok and c3_ok)},
        {u"記号": "S-9", u"予測": u"木: core/・adapters/ 差分 0 行。覆い +1 / 赤 0",
         u"実測": {u"engine の留め(ac8c3ff と一致)": s9_pins, u"覆い・pytest": u"文書で判定"},
         u"当たり": None}]

    rec = {
        u"step": u"**汎化 C 追記 3(改善 2・α)段 α-B。0 USD・席は呼ばない・通信しない・engine 0 行**",
        u"seal": SEAL, u"spec": u"C-0〜C-5。幅は script 内の定数(封の字と合わせた)",
        u"環境": env, u"入力の sha256(読むだけ。1 文字も直していない)": inputs,
        u"engine の留め": pins,
        u"α-1": alpha1, u"α-1 の行(席が参照先を出した 102 行。α-2 の読みの材料つき)": items,
        u"α-1(注入 25 行)": alpha_inj, u"α-3": alpha3, u"α-4": alpha4,
        u"cd8(S-C2)": cd8_block,
        u"対照": {u"S-C1": c1ctl, u"S-C2": {u"完走・欠け 0・A の再現": c2_ok, u"cd8": u"cd8(S-C2) 欄"},
                u"S-C3": c3,
                u"α-C1(注入 25 行が C1-3 の記録と一致)": {u"違った行": mism_c13, u"一致": not mism_c13},
                u"α-C2(P16 で作り直した材料が記録の材料と一致)": {u"一致": p16_repro and not inv_p16}},
        u"**予測 S-1〜S-9**": preds,
        u"所要秒": {u"材料の作り直し(P16 と P20)": round(t_mat, 1), u"cd8": round(t_cd8, 1),
                u"全体": round(time.time() - t_start, 1)},
        "limits": [
            u"無改変 77 行に正解の参照先は無い。α-1 の GROUNDED は『席と Core が同じ参照先で同じ値を読んだ』であって参照先が正しい証明ではない",
            u"席 1 席 × 1 便の答えに依る。席の揺れは測らない",
            u"S-7 の 0 は engine の独立した証拠ではない(C0・C1 と同じ)",
            u"α-2 の読み(席の側か Core の側か)は記録の外。門で縛れない",
            u"S-C1 は率の行・単位が無い行に『fact 自身の値』を C1-3 の作りでは当てられない"]}
    C1._dump(rec, a.out)
    print(u"=== α-B(0 USD)===")
    for pr in preds:
        print(u"  %-4s %s" % (pr[u"記号"], {True: u"当たり", False: u"**外れ**", None: u"(別に判定)"}[pr[u"当たり"]]),
              json.dumps(pr[u"実測"], ensure_ascii=False)[:230])
    print("->", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
