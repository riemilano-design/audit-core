# -*- coding: utf-8 -*-
u"""汎化 C の段 C0(封 `docs/XBRL_GENERALITY_SEAL_2026-10-20.md` §0・§3・§4・§6)。

**未使用 8 書類で、いまの engine(③ + PP)の数が出るかを 0 USD で測る。席(LLM API)は 1 回も呼ばない。通信しない。**

新しい腕・新しい規則は作らない。cd8 で測った経路を import して使うだけ:

  C0-1  ``adapters.xbrl.verify_document.verify_document``(Core が主張を切り出し・名指し・検算)
  C0-2  ``measure/xbrl_a_core_vs_grep_2026-10-17.py``(profile P16・種 ``measure/SEED.json``・腕 Core / Core-P / D′ / D″)
  C0-3  ``adapters.xbrl.verify_external.verify_external(spec, ..., period_pair=True)``
        に **Core-P が名指した参照先**を ``pointers`` として渡す(席の参照先の代わり)

測るだけ。**engine(``core/``・``adapters/``)は 1 行も変えない。測ってから直さない。**

**数を見る前に決めた読み方(迷った所。封の字で 1 通りに決まらなかった所)**

  * C0-1 の profile: 封は ``--doc <id>``(profile を省く = ``vocabulary.DEFAULT_PROFILE``)。(ア) と C-2 の
    基準は P16。**両方を回して記録する**。G-2・G-3・G-11・G-12 は既定の profile の run で判定する。
  * G-10 の「U 保留」「(d) 保留」: cd8 の ``period_unit_hold_2026-10-19.json`` D2 は「名指した行の参照先 fact に
    規則が**当たる**か」(state を変えない露出)で数えた。``holds.apply_holds`` は GROUNDED にしか当たらない
    ので、製品の経路の ``held`` だけ数えると VALUE_MISMATCH の行は永久に 0 になる。**cd8 と並べるため
    露出(``holds.unit_mismatch`` / ``holds.dimension_siblings`` を fact に直接当てる)で判定し、製品の経路の
    ``held`` の数も並べて記録する**。
  * G-12 の「PP が発火」: ``verify_document`` の出力には ``derived_pointers`` が無い。C0-1 の主張のうち
    率の単位(``％``/``%``)で参照先が 1 本のものを ``verify_external(ratio_change, 参照先 1 本, period_pair=True)``
    に通し、``derived_pointers`` が空でない行を数える。符号は ``measure/xbrl_period_pair_rule_2026-10-19.py`` の
    ``sign_from_text(span, 数の字面)``(数の字面は span の中で値が一致する最初の数)。
  * C0-3 の spec の (値, 単位): cd8 の材料(``MB.build_rows`` の注入行の 値・単位・抜粋)をそのまま使う
    (③ と同じ入口)。Core の claim の値・単位は使わない(百万円が「円」に直った claim は
    ``verify_external`` が「円」を外すので UNPROVABLE になり、Core-P の参照先の検査が測れなくなるため)。
  * C1 の条件の「G-10・G-11(実証できた行・保留)が cd8 から 15 pt 以上落ちた」: (実証できた行の率)が
    40.1% から 15 pt 以上落ちた(25.1% 以下)、または(U 保留の露出の率)が 20.0% から 15 pt 以上落ちた(5.0% 以下)、
    のどちらか。**両方を記録に出す。**

    cd audit-core
    python3 measure/xbrl_gen_c_2026-10-20.py [--out PATH]
"""
import argparse
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
import zipfile

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
from adapters.xbrl import verify_document as VD           # noqa: E402
from adapters.xbrl import verify_external as VE           # noqa: E402

SEAL = "docs/XBRL_GENERALITY_SEAL_2026-10-20.md"
GEN = os.path.join(ROOT, "fixtures", "xbrl", "gen_c")
CD8 = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
DRAW = os.path.join(GEN, "draw_2026-10-20.json")
FETCHED = os.path.join(GEN, "fetched_2026-10-20.json")
OUT = os.path.join(GEN, "c0_2026-10-20.json")
CD8_A_REC = os.path.join(CD8, "a_core_vs_grep_2026-10-17.json")
ENGINE_COMMIT = "ac8c3ff"
KEY_NAMES = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY")
KEY_PREFIXES = ("ANTHROPIC", "OPENAI", "GOOGLE", "GEMINI")
CD8_PROFILE = "P16"
V_UNIT_SCALE = VD.V.UNIT_SCALE


def _mod(rel, name):
    sp = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


#: (ア) の実物。腕・採点・正規化は書き直さない。
AC = _mod("measure/xbrl_a_core_vs_grep_2026-10-17.py", "a_core_for_gen_c")
#: cd8 の材料(注入行の 値・単位・抜粋、汚染の検査)。
MB = _mod("measure/xbrl_cd_material_2026-10-17.py", "cd_material_for_gen_c")
#: PP の符号(文を読んで符号を決めるのは呼び出し側。engine ではない)。
R1 = _mod("measure/xbrl_period_pair_rule_2026-10-19.py", "pp_rule_for_gen_c")


def _load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def pct(a, b):
    return None if not b else round(100.0 * a / b, 1)


def _git(args, binary=False):
    r = subprocess.run(["git"] + args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        raise SystemExit("git %s: %s" % (" ".join(args), r.stderr.decode("utf-8", "replace")))
    return r.stdout if binary else r.stdout.decode("utf-8", "replace").strip()


# ------------------------------------------------------------------ 環境
def env_check():
    u"""API key が未設定(0)であること。**値は読まない・記録しない**(設定の有無だけ)。"""
    named = {k: (k in os.environ and bool(os.environ.get(k))) for k in KEY_NAMES}
    prefixed = sorted(k for k in os.environ if k.startswith(KEY_PREFIXES))
    return {u"4 つの key の名前が設定されているか": named,
            u"設定されている key の数": sum(1 for v in named.values() if v),
            u"名前が ANTHROPIC/OPENAI/GOOGLE/GEMINI で始まる環境変数(名前だけ。値は記録しない)": prefixed,
            u"note": u"席(LLM API)は 1 回も呼ばない。通信しない"}


# ------------------------------------------------------------------ engine の留め(C-3 / G-14)
def engine_pins():
    u"""``core/``・``adapters/`` の追跡 file を ac8c3ff と作業木で sha256 比較する。"""
    paths = _git(["ls-tree", "-r", "--name-only", ENGINE_COMMIT, "--", "adapters", "core"]).split("\n")
    paths = [p for p in paths if p]
    mism, missing = [], []
    rows = []
    for p in paths:
        old = _git(["show", "%s:./%s" % (ENGINE_COMMIT, p)], binary=True)
        fp = os.path.join(ROOT, p)
        if not os.path.exists(fp):
            missing.append(p)
            continue
        with io.open(fp, "rb") as fh:
            now = fh.read()
        a, b = sha256_bytes(old), sha256_bytes(now)
        rows.append("%s\t%s" % (p, b))
        if a != b:
            mism.append(p)
    head_paths = [p for p in _git(["ls-files", "--", "adapters", "core"]).split("\n") if p]
    extra = sorted(set(head_paths) - set(paths))
    ve = os.path.join(ROOT, "adapters", "xbrl", "verify_external.py")
    with io.open(ve, "rb") as fh:
        ve_now = sha256_bytes(fh.read())
    ve_old = sha256_bytes(_git(["show", "%s:./adapters/xbrl/verify_external.py" % ENGINE_COMMIT], binary=True))
    numstat = _git(["diff", "HEAD", "--numstat", "--", "core", "adapters"])
    status = _git(["status", "--porcelain", "--", "core", "adapters"])
    return {u"比べた commit": ENGINE_COMMIT,
            u"ac8c3ff の core/ と adapters/ の file 数": len(paths),
            u"作業木で sha256 が違う file": mism, u"作業木に無い file": missing,
            u"HEAD にだけ在る file(ac8c3ff に無い)": extra,
            u"verify_external.py の sha256": {u"ac8c3ff": ve_old, u"作業木": ve_now, u"一致": ve_old == ve_now},
            u"束ねた sha256(core/ と adapters/ の ac8c3ff の file、作業木の内容、cwd に依らず repo 相対)":
                sha256_bytes("\n".join(sorted(rows)).encode("utf-8")),
            u"git diff HEAD --numstat -- core adapters": numstat,
            u"git status --porcelain -- core adapters": status,
            u"一致": (not mism and not missing and not extra and ve_old == ve_now
                    and numstat == "" and status == "")}


# ------------------------------------------------------------------ C0-1
def c01(docs, fetched_by, profile):
    per = []
    for d in docs:
        path = ED.cache_path(d)
        with io.open(path, "rb") as fh:
            zb = fh.read()
        rec_f = fetched_by[d]
        try:
            zf = zipfile.ZipFile(io.BytesIO(zb))
            zip_ok = zf.testzip() is None
            n_members = len(zf.namelist())
        except Exception as e:                      # noqa: BLE001
            zip_ok, n_members = False, 0
        out = VD.verify_document(zb, profile)
        per.append({u"doc": d, u"bytes": len(zb),
                    u"sha256 が取得の記録と一致": sha256_bytes(zb) == rec_f["sha256"],
                    u"bytes が取得の記録と一致": len(zb) == rec_f["bytes"],
                    u"zip が開く": zip_ok, u"zip の member 数": n_members,
                    u"facts": out["input"]["facts"], u"contexts": out["input"]["contexts"],
                    u"claims": out["document"]["claims"], u"states": out["document"]["states"],
                    u"書類単位 UNVERIFIABLE": out["document"]["unverifiable"],
                    u"engine": out["engine"], u"_out": out})
    return per


def _numtext(span, value):
    u"""span の中で値が一致する最初の数の字面(無ければ None)。"""
    for m in re.finditer(r"\d[\d,]*(?:\.\d+)?", span or ""):
        try:
            if abs(float(m.group(0).replace(",", "")) - float(value)) <= 1e-9:
                return m.group(0)
        except ValueError:
            continue
    return None


def _loc_of(raw):
    s = str(raw)
    return s[len("xbrl:"):] if s.startswith("xbrl:") else s


def _resolve(facts_by_loc, facts_by_norm, raw):
    u"""参照先の字 → fact。(fact, どう解いたか)。解けなければ (None, '解けない')。"""
    loc = _loc_of(raw)
    if loc in facts_by_loc:
        return facts_by_loc[loc], u"字が一致"
    n = AC.norm_pointer(raw)
    if n in facts_by_norm:
        return facts_by_norm[n], u"norm_pointer で一致"
    return None, u"解けない"


def _mk_index(facts):
    by_loc, by_norm = {}, {}
    for f in facts:
        loc = "%s@%s" % (f["name"], f["context"])
        by_loc.setdefault(loc, f)
        by_norm.setdefault(AC.norm_pointer("xbrl:" + loc), f)
    return by_loc, by_norm


def keyed(out):
    return {k: out[k] for k in ("state", "reason", "recomputed", "held", "hold_rules", "derived_pointers",
                                "direction_checked")}


def pp_rows_from_c01(per, registry):
    u"""G-12 の材料: 率の主張で参照先 1 本の行を ``verify_external(ratio_change, period_pair=True)`` に通す。"""
    rows = []
    for p in per:
        d = p[u"doc"]
        zb = io.open(ED.cache_path(d), "rb").read()
        inst = I.load_instance(zb)
        facts, contexts = inst["facts"], inst["contexts"]
        by_loc, by_norm = _mk_index(facts)
        for c in p["_out"]["claims"]:
            if c["unit"] not in VE.RATIO_UNITS or len(c.get("pointers") or []) != 1:
                continue
            f, how = _resolve(by_loc, by_norm, c["pointers"][0])
            loc = ("%s@%s" % (f["name"], f["context"])) if f else _loc_of(c["pointers"][0])
            nt = _numtext(c["span"], c["value"])
            sign = R1.sign_from_text(c["span"], nt) if nt is not None else None
            spec = {"kind": "ratio_change", "value": c["value"], "unit": c["unit"],
                    "pointers": [loc], "sign": sign}
            on = VE.verify_external(spec, facts, contexts, registry, claim_id="G12-%s-%s" % (d, c["id"]),
                                    period_pair=True)
            off = VE.verify_external(spec, facts, contexts, registry, claim_id="G12-%s-%s" % (d, c["id"]),
                                     period_pair=False)
            rows.append({u"doc": d, u"id": c["id"], u"Core の state": c["state"], u"値": c["value"],
                         u"単位": c["unit"], u"参照先": loc, u"参照先の解き方": how,
                         u"数の字面": nt, u"符号": sign, u"span": c["span"],
                         u"PP が発火(derived_pointers 非空)": bool(on["derived_pointers"]),
                         u"engine(PP あり)": keyed(on), u"engine(PP なし)": keyed(off)})
    return rows


# ------------------------------------------------------------------ C0-2 / C0-3 / C-2
class Recorder(object):
    u"""``run_doc`` の中で各注入の (tampered, placements, claim, 改変後の全 claims) を拾う。結果は変えない。"""

    def __init__(self):
        self.apply = []
        self.claims = []
        self._orig_apply = None
        self._orig_claim = None

    def __enter__(self):
        self._orig_apply = AC.IJ.apply_edits
        self._orig_claim = AC.claim_for
        rec = self

        def apply_edits(text, chosen):
            tampered, placements = rec._orig_apply(text, chosen)
            if len(chosen) == 1:
                rec.apply.append((chosen[0]["id"], tampered, placements))
            return tampered, placements

        def claim_for(claims, inj):
            c = rec._orig_claim(claims, inj)
            rec.claims.append((inj["id"], inj, c, claims))
            return c

        AC.IJ.apply_edits = apply_edits
        AC.claim_for = claim_for
        return self

    def __exit__(self, *a):
        AC.IJ.apply_edits = self._orig_apply
        AC.claim_for = self._orig_claim
        return False


def c02_and_c03_c2(docs, seed, registry, baseline_p16):
    u"""(ア) の ``run_doc`` を Recorder の下で回し、同じ注入で C0-3 と C-2 を測る。"""
    rows_all, counts_all = [], {}
    c03, c2 = [], []
    claim_info, decoy = [], []
    for doc in docs:
        zb = io.open(ED.cache_path(doc), "rb").read()
        inst = I.load_instance(zb)
        facts, contexts = inst["facts"], inst["contexts"]
        by_loc, by_norm = _mk_index(facts)
        rec = Recorder()
        with rec:
            rows, counts = AC.run_doc(doc, seed, CD8_PROFILE)
        rows_all.extend(rows)
        counts_all[doc] = counts
        if not (len(rec.apply) == len(rec.claims) == len(rows)):
            raise SystemExit(u"**Recorder の件数が合わない: %s apply %d claims %d rows %d。止める**"
                             % (doc, len(rec.apply), len(rec.claims), len(rows)))
        for row, (aid, tampered, placements), (cid, inj, claim, claims_all) in zip(rows, rec.apply, rec.claims):
            if not (row["id"] == aid == cid == inj["id"]):
                raise SystemExit(u"**Recorder の id が合わない: %s %s %s。止める**" % (row["id"], aid, cid))
            # ---- C-2: 無改変の主張の state が動いていないか(cd8 の contamination をそのまま使う)
            cont = MB.contamination(baseline_p16[doc], {"claims": claims_all,
                                                        "document": {"unverifiable": None}})
            c2.append({u"doc": doc, u"id": inj["id"], u"型": inj["type"],
                       u"一意に対になった主張": cont[u"一意に対になった主張"],
                       u"判定が動いた": cont[u"**判定が動いた**"], u"明細": cont[u"明細"],
                       u"対にならなかった(原文側)": cont[u"対にならなかった(原文側)"],
                       u"対にならなかった(改変後側)": cont[u"対にならなかった(改変後側)"]})
            # ---- 読むための記録: 各注入に対応が付いた Core の claim(付かなければ None)
            claim_info.append({u"doc": doc, u"id": inj["id"], u"型": inj["type"],
                               u"claim": (None if claim is None else
                                          {k: claim.get(k) for k in ("id", "form", "subject", "value", "unit",
                                                                     "state", "reason", "pointers", "span")})})
            # ---- 補助(封の外。数を見た後に足した。G の判定には使わない): T5 の偶然一致する側を engine に渡す
            if inj["type"] == "T5_COINCIDENT":
                mrows0, _n0 = MB.build_rows(tampered, [inj], placements)
                mine0 = [m for m in mrows0 if m.get(u"**注入**") == inj["id"]]
                dkey = row[u"正解"][u"偶然一致する側"]
                df, dhow = _resolve(by_loc, by_norm, dkey)
                drec = {u"doc": doc, u"id": inj["id"], u"偶然一致する側": dkey, u"解き方": dhow}
                if len(mine0) == 1 and df is not None:
                    m0 = mine0[0]
                    u0, v0 = m0[u"単位"], m0[u"値"]
                    dloc = "%s@%s" % (df["name"], df["context"])
                    sp0 = {"kind": "single_value", "value": v0, "unit": u0, "pointers": [dloc]}
                    if u0 in VE.RATIO_UNITS:
                        sp0 = {"kind": "ratio_change", "value": v0, "unit": u0, "pointers": [dloc],
                               "sign": R1.sign_from_text(m0[u"抜粋"], m0[u"数の字面"])}
                    o0 = VE.verify_external(sp0, facts, contexts, registry, claim_id="DEC-%s" % inj["id"],
                                            period_pair=True)
                    t0_ = VE.tol_of(u0)
                    scaled = v0 * float(V_UNIT_SCALE.get(u0, 1))
                    drec.update({u"単位": u0, u"値": v0, u"単位込みの値(円)": scaled,
                                 u"偶然一致する側の fact の値": df.get("value"),
                                 u"単位込みで値が一致(許容 = 単位の 1)": (df.get("value") is not None
                                                          and abs(scaled - float(df["value"])) <= VE.tol_of(u0)),
                                 u"state": o0["state"], u"reason": o0["reason"],
                                 u"held": o0["held"], u"hold_rules": list(o0["hold_rules"]),
                                 u"露出 U": bool(H.unit_mismatch(u0, df)[0]),
                                 u"露出 (d)": bool(H.dimension_siblings(facts, df, t0_)),
                                 u"露出 P": bool(H.period_siblings(facts, df, t0_))})
                else:
                    drec.update({u"state": None, u"除外の理由": u"材料の行が %d 本 / 偶然一致する側が解けない=%s"
                                 % (len(mine0), df is None)})
                decoy.append(drec)
            # ---- C0-3: Core-P が名指した注入の行だけ
            cp = row[u"腕"][u"Core-P"]
            if cp[u"参照先"] is None:
                continue
            item = {u"doc": doc, u"id": inj["id"], u"型": inj["type"],
                    u"Core-P の参照先(正規化)": cp[u"参照先"],
                    u"Core-P の判定": cp[u"判定"], u"正解": row[u"正解"]}
            if claim is None:
                item.update({u"engine の state": None, u"除外の理由": u"対応が付かなかった(Core-P の参照先が 1 件も無いはずなのに)"})
                c03.append(item)
                continue
            raw = sorted(claim.get("pointers") or [])[0]
            f, how = _resolve(by_loc, by_norm, raw)
            item.update({u"Core-P の参照先(原文)": raw, u"参照先の解き方": how, u"Core の state": claim["state"],
                         u"Core の claim の値": claim["value"], u"Core の claim の単位": claim["unit"]})
            mrows, _n = MB.build_rows(tampered, [inj], placements)
            mine = [m for m in mrows if m.get(u"**注入**") == inj["id"]]
            if len(mine) != 1:
                item.update({u"engine の state": None,
                             u"除外の理由": u"材料の行が %d 本(1 本でない)" % len(mine)})
                c03.append(item)
                continue
            m = mine[0]
            unit, val = m[u"単位"], m[u"値"]
            loc = ("%s@%s" % (f["name"], f["context"])) if f else _loc_of(raw)
            is_ratio = unit in VE.RATIO_UNITS
            sign = R1.sign_from_text(m[u"抜粋"], m[u"数の字面"]) if is_ratio else None
            spec = {"kind": "ratio_change" if is_ratio else "single_value", "value": val, "unit": unit,
                    "pointers": [loc]}
            if is_ratio:
                spec["sign"] = sign
            cid2 = "C03-%s" % inj["id"]
            on = VE.verify_external(spec, facts, contexts, registry, claim_id=cid2, period_pair=True)
            off = VE.verify_external(spec, facts, contexts, registry, claim_id=cid2, period_pair=False)
            tol = VE.tol_of(unit)
            if f is not None:
                u_fire, ucc, ufc = H.unit_mismatch(unit, f)
                d_sibs = H.dimension_siblings(facts, f, tol)
                p_sibs = H.period_siblings(facts, f, tol)
            else:
                u_fire, ucc, ufc, d_sibs, p_sibs = False, None, None, [], []
            item.update({u"材料の値": val, u"材料の単位": unit, u"数の字面": m[u"数の字面"],
                         u"spec の kind": spec["kind"], u"符号": sign, u"参照先の fact の単位": (f or {}).get("unit"),
                         u"参照先の fact の値": (f or {}).get("value"),
                         u"engine の state": on["state"], u"engine の reason": on["reason"],
                         u"engine の recomputed": on["recomputed"], u"held(製品の経路)": on["held"],
                         u"hold_rules(製品の経路)": list(on["hold_rules"]),
                         u"derived_pointers": on["derived_pointers"],
                         u"direction_checked": on["direction_checked"],
                         u"露出 U(単位の種類が違う)": bool(u_fire), u"露出 U の明細": [ucc, ufc],
                         u"露出 (d)(同額の次元兄弟)": bool(d_sibs), u"露出 P(同額の期間兄弟)": bool(p_sibs),
                         u"PP の行": (spec["kind"] == "ratio_change"),
                         u"engine(PP あり)": keyed(on), u"engine(PP なし)": keyed(off)})
            c03.append(item)
    return rows_all, counts_all, c03, c2, claim_info, decoy


def tally_c03(c03):
    ev = [x for x in c03 if x.get(u"engine の state") is not None]
    st = {}
    for x in ev:
        st[x[u"engine の state"]] = st.get(x[u"engine の state"], 0) + 1
    by_type = {}
    for x in ev:
        t = x[u"型"]
        by_type.setdefault(t, {})
        by_type[t][x[u"engine の state"]] = by_type[t].get(x[u"engine の state"], 0) + 1
    grounded = [x for x in ev if x[u"engine の state"] == "GROUNDED"]
    held = [x for x in ev if x[u"held(製品の経路)"]]
    u_exp = [x for x in ev if x[u"露出 U(単位の種類が違う)"]]
    d_exp = [x for x in ev if x[u"露出 (d)(同額の次元兄弟)"]]
    p_exp = [x for x in ev if x[u"露出 P(同額の期間兄弟)"]]
    u_held = [x for x in ev if "U" in x[u"hold_rules(製品の経路)"]]
    d_held = [x for x in ev if "d" in x[u"hold_rules(製品の経路)"]]
    unprov = [x for x in ev if x[u"engine の state"] == "UNPROVABLE"]
    reasons = {}
    for x in unprov:
        r = x[u"engine の reason"]
        reasons[r] = reasons.get(r, 0) + 1
    n = len(ev)
    return {u"Core-P が名指した注入の行": len(c03), u"engine を通せた行(分母)": n,
            u"通せなかった行": [{u"id": x[u"id"], u"理由": x.get(u"除外の理由")} for x in c03
                         if x.get(u"engine の state") is None],
            u"state の分布": st, u"型別の state": by_type,
            u"**GROUNDED(誤りを通した)**": {u"件数": len(grounded), u"ids": [x[u"id"] for x in grounded]},
            u"VALUE_MISMATCH": {u"件数": st.get("VALUE_MISMATCH", 0), u"率": pct(st.get("VALUE_MISMATCH", 0), n)},
            u"UNPROVABLE": {u"件数": st.get("UNPROVABLE", 0), u"率": pct(st.get("UNPROVABLE", 0), n),
                            u"理由の分布": reasons},
            u"U 保留の露出": {u"件数": len(u_exp), u"分母": n, u"率": pct(len(u_exp), n)},
            u"(d) 保留の露出": {u"件数": len(d_exp), u"分母": n, u"率": pct(len(d_exp), n)},
            u"P 保留の露出": {u"件数": len(p_exp), u"分母": n, u"率": pct(len(p_exp), n)},
            u"製品の経路の held(GROUNDED だけが対象)": {u"件数": len(held), u"分母": n, u"率": pct(len(held), n),
                                           u"うち U": len(u_held), u"うち (d)": len(d_held)}}


# ------------------------------------------------------------------ main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    if os.path.exists(a.out):
        raise SystemExit(u"既に在る: %s(測り直さない)" % a.out)
    t_start = time.time()
    env = env_check()
    if env[u"設定されている key の数"] != 0:
        raise SystemExit(u"**LLM の API key が設定されている。席を呼ばない段なので止める**")

    draw = _load(DRAW)
    docs = draw[u"引いた 8 件"]
    fetched = _load(FETCHED)
    fetched_by = {x["docID"]: x for x in fetched[u"取得した書類"]}
    if sorted(fetched_by) != sorted(docs):
        raise SystemExit(u"**取得の記録と引いた 8 件が合わない。止める**")
    seed, seed_meta = AC.IJ.verify_seed_sealed(AC.SEED_FILE)
    registry = RS.register_all(core.Registry.default())
    os.makedirs(AC.TMP, exist_ok=True)

    timing = {}
    # ---- C0-1(既定の profile = 製品の経路そのまま)と P16(C-2 と (ア) の基準)
    t0 = time.time()
    per_def = c01(docs, fetched_by, None)
    default_profile = VD.V.DEFAULT_PROFILE
    per_p16 = c01(docs, fetched_by, CD8_PROFILE)
    timing[u"C0-1(既定 + P16)秒"] = round(time.time() - t0, 1)
    baseline_p16 = {p[u"doc"]: p["_out"] for p in per_p16}
    same_profiles = []
    for pd, pp in zip(per_def, per_p16):
        same_profiles.append({u"doc": pd[u"doc"],
                              u"claims が同じ": pd["_out"]["claims"] == pp["_out"]["claims"],
                              u"states が同じ": pd[u"states"] == pp[u"states"]})

    # ---- C0-2 を (ア) の main() そのままで(一時 file へ)。これが「script の出力」
    t0 = time.time()
    tmpdir = tempfile.mkdtemp(prefix="gen_c_c02_")
    c02_out = os.path.join(tmpdir, "a_core_vs_grep_gen_c.json")
    AC.main(["--docs", ",".join(docs), "--profile", CD8_PROFILE, "--out", c02_out])
    c02 = _load(c02_out)
    timing[u"C0-2 (ア) の main() 秒"] = round(time.time() - t0, 1)

    # ---- 同じ注入に Recorder をかぶせて C0-3 と C-2
    t0 = time.time()
    rows_r, counts_r, c03, c2, claim_info, decoy = c02_and_c03_c2(docs, seed, registry, baseline_p16)
    timing[u"C0-2 再走(Recorder)+ C0-3 + C-2 秒"] = round(time.time() - t0, 1)
    recorder_same = (json.loads(json.dumps(rows_r, ensure_ascii=False)) == c02["rows"]
                     and json.loads(json.dumps(counts_r, ensure_ascii=False)) == c02[u"注入の件数"])

    # ---- G-12 の材料(C0-1 既定 profile の率の主張)
    pp_rows = pp_rows_from_c01(per_def, registry)

    # ---- C-1 cd8 の再現(使用済み 8 書類。一時 file に向ける)
    t0 = time.time()
    rec8 = _load(CD8_A_REC)
    c1_out = os.path.join(tmpdir, "a_core_vs_grep_cd8_repro.json")
    AC.main(["--docs", ",".join(rec8[u"書類"]), "--profile", rec8["profile"], "--out", c1_out])
    new8 = _load(c1_out)
    diff_keys = sorted(k for k in set(rec8) | set(new8) if rec8.get(k) != new8.get(k))
    timing[u"C-1 cd8 再現秒"] = round(time.time() - t0, 1)
    c1 = {u"cd8 の記録": "fixtures/xbrl/cd8/a_core_vs_grep_2026-10-17.json", u"書類": rec8[u"書類"],
          u"違った欄": diff_keys, u"採点が一致": rec8[u"採点"] == new8[u"採点"],
          u"rows が一致": rec8["rows"] == new8["rows"], u"全欄一致": diff_keys == [],
          u"注入の合計": new8[u"注入の合計"]}

    # ---- C-2
    moved = sum(x[u"判定が動いた"] for x in c2)
    paired = sum(x[u"一意に対になった主張"] for x in c2)
    c2s = {u"注入ごとに測った件数": len(c2), u"一意に対になった主張(延べ)": paired, u"**判定が動いた(延べ)**": moved,
           u"動いた注入": [x for x in c2 if x[u"判定が動いた"]][:20],
           u"対にならなかった(原文側)の最大": max(x[u"対にならなかった(原文側)"] for x in c2) if c2 else None,
           u"対にならなかった(改変後側)の最大": max(x[u"対にならなかった(改変後側)"] for x in c2) if c2 else None,
           u"期待どおり(判定が動いた 0 かつ対になった主張が 1 件以上)": moved == 0 and paired > 0}

    # ---- C-3
    pins = engine_pins()
    toggle_rows = ([(x, x[u"engine(PP あり)"], x[u"engine(PP なし)"], x[u"PP の行"]) for x in c03
                    if x.get(u"engine の state") is not None]
                   + [(x, x[u"engine(PP あり)"], x[u"engine(PP なし)"], True) for x in pp_rows])
    diff_pp = sum(1 for x, on, off, is_pp in toggle_rows if is_pp and on != off)
    diff_non_pp = [x[u"id"] for x, on, off, is_pp in toggle_rows if (not is_pp) and on != off]
    n_pp = sum(1 for r in toggle_rows if r[3])
    c3 = {u"engine の留め": pins, u"PP の行(行数)": n_pp, u"PP でない行(行数)": len(toggle_rows) - n_pp,
          u"PP の行で period_pair=False と違った行": diff_pp,
          u"PP でない行で違った行(ids)": diff_non_pp,
          u"期待どおり": pins[u"一致"] and not diff_non_pp and diff_pp > 0}

    # ---- 集計
    tot_claims = sum(p[u"claims"] for p in per_def)
    st_tot = {}
    for p in per_def:
        for k, v in p[u"states"].items():
            st_tot[k] = st_tot.get(k, 0) + v
    g, vm = st_tot.get("GROUNDED", 0), st_tot.get("VALUE_MISMATCH", 0)
    proven = g + vm
    core_p = c02[u"採点"]["Core-P"]
    dprime = c02[u"採点"][u"D′"]
    inj_total = c02[u"注入の合計"]
    t5_docs = sum(1 for d in docs if c02[u"注入の件数"][d]["T5_COINCIDENT"][u"注入した"] >= 1)
    t3 = tally_c03(c03)
    pp_fired = [x for x in pp_rows if x[u"PP が発火(derived_pointers 非空)"]]
    pp_fired_g = [x for x in pp_fired if x[u"engine(PP あり)"]["state"] == "GROUNDED"]
    cd8_pts = {u"実証できた行": 40.1, u"U 保留の露出": 20.0}

    ident = core_p[u"特定率(分母 = T5 の件数)"]
    wrong = core_p[u"誤認定率(分母 = 参照先を出した件)"]
    t1p = core_p[u"T1 の通し(値がどこにも無いのに確認済み)"]
    t3n = core_p[u"T3 の名指し(参照先が無いのに名指した)"]
    dp_id, dp_wr = dprime[u"特定率(分母 = T5 の件数)"], dprime[u"誤認定率(分母 = 参照先を出した件)"]

    def rng(x, lo, hi):
        return x is not None and lo <= x <= hi

    g1_rows = [{u"doc": p[u"doc"], u"bytes": p[u"bytes"], u"facts": p[u"facts"],
                u"ok": (p[u"bytes"] > 0 and p[u"zip が開く"] and p[u"facts"] >= 300
                        and p[u"sha256 が取得の記録と一致"])} for p in per_def]
    g2_docs = [{u"doc": p[u"doc"], u"claims": p[u"claims"], u"60〜250": 60 <= p[u"claims"] <= 250} for p in per_def]
    u_rate, d_rate = t3[u"U 保留の露出"][u"率"], t3[u"(d) 保留の露出"][u"率"]
    vm_rate, unp_rate = t3[u"VALUE_MISMATCH"][u"率"], t3[u"UNPROVABLE"][u"率"]
    g12_n = len(pp_fired)
    pred = [
        {u"記号": "G-1", u"予測": u"8 件とも取れる(byte > 0・zip が開く・fact ≥ 300)", u"実測": g1_rows,
         u"当たり": all(r[u"ok"] for r in g1_rows)},
        {u"記号": "G-2", u"予測": u"claims 書類ごと 60〜250・合計 600〜1,600",
         u"実測": {u"書類ごと": g2_docs, u"合計": tot_claims},
         u"当たり": all(r[u"60〜250"] for r in g2_docs) and 600 <= tot_claims <= 1600},
        {u"記号": "G-3", u"予測": u"GROUNDED 35〜60%・VALUE_MISMATCH 10〜30%(8 書類合計の割合)",
         u"実測": {u"GROUNDED": pct(g, tot_claims), u"VALUE_MISMATCH": pct(vm, tot_claims), u"分母": tot_claims},
         u"当たり": rng(pct(g, tot_claims), 35, 60) and rng(pct(vm, tot_claims), 10, 30)},
        {u"記号": "G-4", u"予測": u"注入の合計 100〜180・T5 が 1 件以上の書類 6 以上 / 8",
         u"実測": {u"注入の合計": inj_total, u"T5 が 1 件以上の書類": t5_docs},
         u"当たり": 100 <= inj_total <= 180 and t5_docs >= 6},
        {u"記号": "G-5", u"予測": u"Core-P の特定率(T5)55〜80%(cd8 71.9%)", u"実測": ident,
         u"当たり": rng(ident[u"率"], 55, 80)},
        {u"記号": "G-6", u"予測": u"Core-P の誤認定率 15〜35%・T1 の通し 0%・T3 の名指し 25% 以下",
         u"実測": {u"誤認定率": wrong, u"T1 の通し": t1p, u"T3 の名指し": t3n},
         u"当たり": rng(wrong[u"率"], 15, 35) and t1p[u"分子"] == 0
         and t3n[u"率"] is not None and t3n[u"率"] <= 25},
        {u"記号": "G-7", u"予測": u"D′ の特定率 0%(0 件)・誤認定率 90% 以上",
         u"実測": {u"特定率": dp_id, u"誤認定率": dp_wr},
         u"当たり": dp_id[u"分子"] == 0 and dp_wr[u"率"] is not None and dp_wr[u"率"] >= 90},
        {u"記号": "G-8", u"予測": u"Core-P が名指した注入の行で engine が GROUNDED にする件数 0",
         u"実測": t3[u"**GROUNDED(誤りを通した)**"], u"分母": t3[u"engine を通せた行(分母)"],
         u"当たり": t3[u"**GROUNDED(誤りを通した)**"][u"件数"] == 0 and t3[u"engine を通せた行(分母)"] > 0},
        {u"記号": "G-9", u"予測": u"名指した注入の行の state: VALUE_MISMATCH 60% 以上・UNPROVABLE 40% 以下",
         u"実測": {u"VALUE_MISMATCH": t3[u"VALUE_MISMATCH"], u"UNPROVABLE": t3[u"UNPROVABLE"]},
         u"当たり": vm_rate is not None and vm_rate >= 60 and unp_rate is not None and unp_rate <= 40},
        {u"記号": "G-10", u"予測": u"名指した行の U 保留 5〜35%・(d) 保留 0〜10%(露出で判定。製品の経路の held も並べる)",
         u"実測": {u"U 保留の露出": t3[u"U 保留の露出"], u"(d) 保留の露出": t3[u"(d) 保留の露出"],
                 u"製品の経路の held": t3[u"製品の経路の held(GROUNDED だけが対象)"]},
         u"当たり": rng(u_rate, 5, 35) and rng(d_rate, 0, 10)},
        {u"記号": "G-11", u"予測": u"実証できた行(GROUNDED + VALUE_MISMATCH)の割合 25〜65%(cd8 40.1%。分母は Core の切り出し全部)",
         u"実測": {u"分子": proven, u"分母": tot_claims, u"率": pct(proven, tot_claims)},
         u"当たり": rng(pct(proven, tot_claims), 25, 65)},
        {u"記号": "G-12", u"予測": u"率の主張で PP が発火する行 10 以上・そのうち GROUNDED 半分以上",
         u"実測": {u"率の主張で参照先 1 本の行": len(pp_rows), u"PP が発火": g12_n,
                 u"うち GROUNDED": len(pp_fired_g)},
         u"当たり": g12_n >= 10 and len(pp_fired_g) * 2 >= g12_n},
        {u"記号": "G-13", u"予測": u"対照 C-1〜C-3 が全部期待どおり",
         u"実測": {u"C-1": c1[u"全欄一致"], u"C-2": c2s[u"期待どおり(判定が動いた 0 かつ対になった主張が 1 件以上)"],
                 u"C-3": c3[u"期待どおり"]},
         u"当たり": c1[u"全欄一致"] and c2s[u"期待どおり(判定が動いた 0 かつ対になった主張が 1 件以上)"] and c3[u"期待どおり"]},
        {u"記号": "G-14", u"予測": u"core/・adapters/ の差分 0 行。過去の門の engine の留めは衝突しない。覆い +2",
         u"実測": {u"core/・adapters/ の差分 0 行(ac8c3ff・HEAD・作業木)": pins[u"一致"],
                 u"過去の門・覆いの数": u"この script では測らない(pytest と suite_coverage を別に走らせて結果文書に書く)"},
         u"当たり": None, u"この script が測った部分": pins[u"一致"]},
    ]

    # ---- 補助の集計(判定には使わない)
    dec_ev = [x for x in decoy if x.get(u"state") is not None]
    dec_st = {}
    for x in dec_ev:
        dec_st[x[u"state"]] = dec_st.get(x[u"state"], 0) + 1
    decoy_summary = {u"T5 の行": len(decoy), u"engine を通せた行": len(dec_ev), u"state の分布": dec_st,
                     u"GROUNDED": dec_st.get("GROUNDED", 0),
                     u"保留(held)": sum(1 for x in dec_ev if x[u"held"]),
                     u"保留のうち (d)": sum(1 for x in dec_ev if "d" in x[u"hold_rules"]),
                     u"保留のうち P": sum(1 for x in dec_ev if "P" in x[u"hold_rules"]),
                     u"保留のうち U": sum(1 for x in dec_ev if "U" in x[u"hold_rules"]),
                     u"単位込み(円換算)で値が一致する行": sum(1 for x in dec_ev if x[u"単位込みで値が一致(許容 = 単位の 1)"]),
                     u"通せなかった行": [x[u"id"] for x in decoy if x.get(u"state") is None]}
    # T5 50 件の読み: gold の枠が次元つきか × Core-P の結果
    ci_by = {(x[u"doc"], x[u"id"]): x[u"claim"] for x in claim_info}
    t5_read = {}
    for x in rows_r:
        if x[u"型"] != "T5_COINCIDENT":
            continue
        gold = x[u"正解"][u"正解"]
        dimmed = "_" in gold.split("@", 1)[1]
        cp = x[u"腕"][u"Core-P"]
        cl = ci_by[(x["doc"], x["id"])]
        if not x[u"対応が付いた"]:
            outc = u"対応が付かない"
        elif cp[u"参照先"] is None:
            outc = u"参照先を出さない(%s/%s)" % (cl["state"], cl["reason"])
        elif cp[u"判定"][u"特定"]:
            outc = u"特定"
        else:
            outc = u"誤認定"
        for key in (u"全体|gold の枠が次元つき=%s" % dimmed, u"%s|gold の枠が次元つき=%s" % (x["doc"], dimmed)):
            t5_read.setdefault(key, {})
            t5_read[key][outc] = t5_read[key].get(outc, 0) + 1
    t5_read = dict(sorted(t5_read.items()))
    shape = {}
    for p in per_def:
        for c in p["_out"]["claims"]:
            if c["unit"] in VE.RATIO_UNITS:
                k = "%s|参照先 %d 本|%s" % (c["form"], len(c.get("pointers") or []), c["state"])
                shape[k] = shape.get(k, 0) + 1
    ratio_shape = dict(sorted(shape.items()))
    p16_tot = sum(p[u"claims"] for p in per_p16)
    p16_st = {}
    for p in per_p16:
        for k, v in p[u"states"].items():
            p16_st[k] = p16_st.get(k, 0) + v
    p16_side = {u"claims の合計": p16_tot, u"書類ごとの claims": {p[u"doc"]: p[u"claims"] for p in per_p16},
                u"state の合計": p16_st,
                u"GROUNDED の割合": pct(p16_st.get("GROUNDED", 0), p16_tot),
                u"VALUE_MISMATCH の割合": pct(p16_st.get("VALUE_MISMATCH", 0), p16_tot),
                u"実証できた行の率": pct(p16_st.get("GROUNDED", 0) + p16_st.get("VALUE_MISMATCH", 0), p16_tot)}

    # ---- C1 の条件(封 §0 の字)
    g5_miss = not rng(ident[u"率"], 55, 80)
    g8_miss = t3[u"**GROUNDED(誤りを通した)**"][u"件数"] != 0
    proven_rate = pct(proven, tot_claims)
    drop_proven = None if proven_rate is None else round(cd8_pts[u"実証できた行"] - proven_rate, 1)
    drop_u = None if u_rate is None else round(cd8_pts[u"U 保留の露出"] - u_rate, 1)
    c1_cond = {u"G-5 が外れた": g5_miss, u"G-8 が外れた": g8_miss,
               u"実証できた行が cd8 の 40.1% から落ちた pt": drop_proven,
               u"実証できた行が 15 pt 以上落ちた": drop_proven is not None and drop_proven >= 15,
               u"U 保留の露出が cd8 の 20.0% から落ちた pt": drop_u,
               u"U 保留の露出が 15 pt 以上落ちた": drop_u is not None and drop_u >= 15}
    c1_cond[u"**C1 をやる条件に当たったか**"] = (g5_miss or g8_miss or c1_cond[u"実証できた行が 15 pt 以上落ちた"]
                                       or c1_cond[u"U 保留の露出が 15 pt 以上落ちた"])

    per_doc_def = [{k: v for k, v in p.items() if k != "_out"} for p in per_def]
    per_doc_p16 = [{k: v for k, v in p.items() if k not in ("_out", u"engine")} for p in per_p16]
    rec = {
        "seal": SEAL, "step": u"**汎化 C の段 C0。0 USD・席を呼ばない・通信しない。engine は 1 行も変えない**",
        u"環境": env,
        u"engine の指紋": per_def[0][u"engine"],
        u"engine の留め": pins,
        u"材料": {u"書類": docs, u"draw": "fixtures/xbrl/gen_c/draw_2026-10-20.json",
                u"取得の記録": "fixtures/xbrl/gen_c/fetched_2026-10-20.json",
                u"注入の種": {"file": "measure/SEED.json", "sealed_on": seed_meta.get("sealed_on")}},
        u"**C0-1 製品の経路(既定の profile)**": {u"profile": default_profile, u"書類ごと": per_doc_def,
                                          u"claims の合計": tot_claims, u"state の合計": st_tot,
                                          u"GROUNDED + VALUE_MISMATCH": proven,
                                          u"実証できた行の率(分母 = claims の合計)": pct(proven, tot_claims)},
        u"C0-1(P16。C-2 と (ア) の基準)": {u"profile": CD8_PROFILE, u"書類ごと": per_doc_p16,
                                    u"既定と P16 で claims・states が同じか": same_profiles},
        u"**C0-2 (ア) の main() の出力**": {k: c02[k] for k in c02 if k != "rows"},
        u"C0-2 rows": c02["rows"],
        u"Recorder をかぶせた再走が main() の出力と一致": recorder_same,
        u"C0-2 各注入に対応が付いた Core の claim(読むための記録)": claim_info,
        u"**補助(封の外。数を見た後に足した。G の判定に使わない)T5 の偶然一致する側を engine に渡した**": {
            u"集計": decoy_summary, u"rows": decoy},
        u"補助: T5 50 件の読み(gold の枠が次元つきか × Core-P の結果。書類別も)": t5_read,
        u"補助: 率の単位(%/％)の claims の形(C0-1 既定 profile。form × 参照先の本数 × state)": ratio_shape,
        u"補助: P16 で数えた G-2・G-3・G-11(既定 profile と違う書類があるため)": p16_side,
        u"**C0-3 engine を Core-P の参照先に当てた**": {u"集計": t3, u"rows": c03},
        u"**G-12 率の主張(C0-1 の既定 profile)**": {u"行数": len(pp_rows), u"PP が発火": g12_n,
                                               u"うち GROUNDED": len(pp_fired_g), u"rows": pp_rows},
        u"**対照 C-1**": c1, u"**対照 C-2**": {u"集計": c2s, u"rows": c2}, u"**対照 C-3**": c3,
        u"**予測 G-1〜G-14**": pred,
        u"**C1 の条件(封 §0)**": c1_cond,
        u"cd8 の数(§2。並べる相手)": {u"C0-1 S100YXMA": {u"claims": 119, u"GROUNDED": 60, u"VALUE_MISMATCH": 24,
                                                  u"UNVERIFIABLE": 18, u"POINTER_NOT_FOUND": 17},
                                u"Core-P 特定率": u"46 / 64 = 71.9%", u"Core-P 誤認定率": u"18 / 76 = 23.7%",
                                u"U 保留(席の参照先)": u"17 / 85 = 20.0%", u"実証できた行": u"77 / 192 = 40.1%"},
        u"所要秒": dict(timing, **{u"全体": round(time.time() - t_start, 1)}),
        u"limits": [u"8 書類 1 回である。合格線は作らない。",
                    u"C0 の engine の数は Core 自身の名指しに依る(席の名指しではない)。",
                    u"C0-1 の claims は Core の切り出しで、席の 24 行の材料とは単位が違う。",
                    u"(ア) の脚注: 正解は identified_sites(値の一意性 + 単位・ラベル)で作られ、正解そのものが誤りうる。"],
    }
    with io.open(a.out, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(u"=== 汎化 C 段 C0(0 USD)===")
    for p in pred:
        print(u"  %-5s %s" % (p[u"記号"], {True: u"当たり", False: u"**外れ**", None: u"(別に判定)"}[p[u"当たり"]]),
              json.dumps(p[u"実測"], ensure_ascii=False)[:230])
    print(u"C-1 %s / C-2 %s / C-3 %s" % (c1[u"全欄一致"], c2s[u"期待どおり(判定が動いた 0 かつ対になった主張が 1 件以上)"],
                                       c3[u"期待どおり"]))
    print(u"C1 の条件:", json.dumps(c1_cond, ensure_ascii=False))
    print(u"Recorder 再走 = main() の出力:", recorder_same)
    print(u"所要:", rec[u"所要秒"])
    print("->", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
