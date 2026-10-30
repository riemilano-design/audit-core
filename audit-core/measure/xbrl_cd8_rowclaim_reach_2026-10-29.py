# -*- coding: utf-8 -*-
u"""診断: cd8 の系統の「行 -> claim」(値と字の最初の 1 件)を、位置(engine の文の番号と文の中の位置)で引き直して行ごとに数える ― 2026-10-29。

封 ``docs/XBRL_CD8_ROWCLAIM_REACH_SEAL_2026-10-29.md``(commit ``5f3ae0a``)§2 と、その §6-5 の補い(空白だけ違う engine の本文は、空白を除いた字の並びで位置を写す)の測定。
**診断だけ。engine(``core/``・``adapters/``)は 0 行。既存の記録は 1 字も書き換えない(別の記録を足す)。台帳・結果文書の字も直さない。** 0 USD・通信なし・鍵の値は読まない・席(LLM)は呼ばない。

    cd audit-core
    python3 measure/xbrl_cd8_rowclaim_reach_2026-10-29.py --procs 6                       # 既に出力が在れば測り直さない
    python3 measure/xbrl_cd8_rowclaim_reach_2026-10-29.py --docs 2 --out <scratch の file>   # 試走(先頭 n 書類。全書類を要する門は照らさない)

4 つの母集団(封 §0-2): A1 = cd8 の材料 192 行(P16)・A2 = 段 2 の材料 192 行(P22・P27)・B1 = (ア) の 8 書類 142 行(P16・P20・P21)・B2 = gen_c の (ア) 128 行(P16・P20・P21)。
材料・行・注入・値で引く対応付け・判定は、記録を作った script の関数をそのまま呼ぶ(``_mod`` で読み込む)。**自分で書く対応付けの規則は ``claim_at`` の 1 つだけ**(本文の位置 -> engine の文の番号と文の中の範囲 -> num の claim の数の範囲と重なるもの)。
配線の門(封 §2-2): 1 つでも違えば**記録を書かずに止める**。生 ZIP は ``~/.cache/audit-core/edinet/`` から読むだけ。``edinet-fresh-2026-10-21/`` は件数だけ数える。``edinetdb-p27/`` は開かない。
"""
from __future__ import print_function

import argparse
import collections
import concurrent.futures
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import math
import multiprocessing
import os
import re
import subprocess
import sys
import tempfile
import time
import unicodedata

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


MB = _mod("measure/xbrl_cd_material_2026-10-17.py", "cd_material_for_rowclaim")
RM = _mod("measure/xbrl_rowclaim_map_2026-10-17.py", "rowclaim_map_for_rowclaim")
HS2 = _mod("measure/xbrl_hybrid_s2_2026-10-20.py", "hybrid_s2_for_rowclaim")
PB = _mod("measure/xbrl_period_bind_2026-10-20.py", "period_bind_for_rowclaim")
GC = _mod("measure/xbrl_gen_c_2026-10-20.py", "gen_c_for_rowclaim")
T2D = _mod("measure/xbrl_t2_pass_diag_2026-10-28.py", "t2diag_for_rowclaim")
LB = _mod("measure/xbrl_lastbranch_2026-10-21.py", "lastbranch_for_rowclaim")
FR = _mod("measure/xbrl_fresh_2026-10-21.py", "fresh_for_rowclaim")
XS = _mod("measure/xbrl_cd_score_2026-10-17.py", "cd_score_for_rowclaim")
XC = _mod("measure/xbrl_cd_ceiling_2026-10-17.py", "cd_ceiling_for_rowclaim")
NF = _mod("measure/xbrl_naming_fix_2026-10-20.py", "naming_fix_for_rowclaim")
FC = _mod("measure/facts_check_2026-10-20.py", "facts_check_for_rowclaim")
AC = GC.AC          # Recorder が包むのは GC の AC の実体(module の差し替えは使う側の実体に届かないと黙って効かない)
IJ, HT = MB.IJ, HS2.HT

from adapters.xbrl import edinet as ED           # noqa: E402
from adapters.xbrl import verify_document as VD  # noqa: E402
from adapters.xbrl import recipes as R           # noqa: E402
from adapters.xbrl import extract as E           # noqa: E402
from adapters.xbrl import vocabulary as V        # noqa: E402

SEAL_REL = "docs/XBRL_CD8_ROWCLAIM_REACH_SEAL_2026-10-29.md"
SEAL_COMMIT = "5f3ae0a"
OUT_REL = "fixtures/xbrl/cd8/rowclaim_reach_2026-10-29.json"
ENGINE_FILES = T2D.ENGINE_FILES
TOL = MB.A1.TOL

POPS = ("A1", "A2", "B1", "B2")
PROFILES = {"A1": ("P16",), "A2": ("P22", "P27"), "B1": ("P16", "P20", "P21"), "B2": ("P16", "P20", "P21")}

# ---- 分類(封 §2-4。機械で 1 か所 ``classify``)
C_UNFIX, C_MANY, C_NONE = u"(位置が決まらない)", u"(位置で 1 件に決まらない)", u"(両方なし)"
C_VONLY, C_PONLY, C_SAME, C_DIFF = u"(値だけ)", u"(位置だけ)", u"(同じ)", u"(違う)"
CLASSES = (C_UNFIX, C_MANY, C_NONE, C_VONLY, C_PONLY, C_SAME, C_DIFF)
# ---- 本文の語(封 §6-5 の 2)
T_SAME, T_WS, T_OTHER = u"字で同じ", u"空白だけ違う", u"空白以外が違う"
# ---- 細目
U_OTHER, U_WSONLY, U_NOSENT, U_NOFIT = u"空白以外が違う", u"範囲が空白だけ", u"文に収まらない", u"写せない文"
D_SAMESENT, D_OTHERSENT, D_NOTNUM = u"同じ文・別の数", u"別の文", u"値で引いた claim が num の claim でない"
P_SAME, P_POW10, P_SIGN, P_ELSE = u"値が同じ(字面が span に無かった)", u"値が違う・10 の冪の倍", u"値が違う・符号だけ", u"値が違う・その他"
V_HASNUM, V_NONUM = u"行の範囲に engine の数が在る", u"行の範囲に engine の数が無い"

# 記録を読む(sha256 を記録に書く)。配線の門・数え直し・重なり・台帳で読む
REC = {
    "draw": "fixtures/xbrl/cd8/draw_2026-10-17.json",
    "fetched": "fixtures/xbrl/cd8/fetched_2026-10-17.json",
    "material": "fixtures/xbrl/cd8/material_2026-10-17.json",
    "score": "fixtures/xbrl/cd8/score_2026-10-17.json",
    "ceiling": "fixtures/xbrl/cd8/ceiling_2026-10-17.json",
    "rowclaim_map": "fixtures/xbrl/cd8/rowclaim_map_2026-10-17.json",
    "p20_rerun": "fixtures/xbrl/cd8/p20_rerun_2026-10-17.json",
    "role_swap": "fixtures/xbrl/cd8/role_swap_2026-10-17.json",
    "verify_inventory": "fixtures/xbrl/cd8/verify_inventory_2026-10-17.json",
    "pnf_diag": "fixtures/xbrl/cd8/pnf_diag_2026-10-17.json",
    "contract_v1": "fixtures/xbrl/cd8/contract_v1_2026-10-17.json",
    "p20_pred_recheck": "fixtures/xbrl/cd8/p20_pred_recheck_2026-10-17.json",
    "ac_p16": "fixtures/xbrl/cd8/a_core_vs_grep_2026-10-17.json",
    "ac_p20": "fixtures/xbrl/cd8/a_core_vs_grep_P20_2026-10-17.json",
    "s2_material": "fixtures/xbrl/gen_c/hybrid_s2_material_2026-10-20.json",
    "period_bind": "fixtures/xbrl/period_bind_2026-10-20.json",
    "default_p27": "fixtures/xbrl/default_p27_2026-10-28.json",
    "c0": "fixtures/xbrl/gen_c/c0_2026-10-20.json",
    "c0_p20": "fixtures/xbrl/gen_c/c0_p20_2026-10-20.json",
    "c1": "fixtures/xbrl/gen_c/c1_2026-10-20.json",
    "naming_fix": "fixtures/xbrl/naming_fix/p21_2026-10-20.json",
}
# 生きた文書 2 本(後の便が行や追記を足す)。file 全体の sha256 では照らさない(封の追記 2026-10-29)。
# 台帳は §2-7 の対象の行の字、総点検の文書は読み分けの表(ledger)の門のブロックの中の字の sha256 を記録に持つ。
HARNESS_REL = "docs/XBRL_INJECT_HARNESS_REVIEW_2026-10-29.md"
FACTS_REL = "docs/FACTS_FOR_BUYERS_2026-10-20.md"
LEDGER_BLOCK = "ledger"
ROWKEYS = {"A1": u"材料の行(cd8)", "A2": u"段 2 の材料の行", "B1": u"(ア) cd8", "B2": u"(ア) gen_c"}


def jload(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return json.load(fh)


def sha16(rel):
    with io.open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def sha64(rel):
    with io.open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def sha_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def git(*a):
    r = subprocess.run(["git"] + list(a), cwd=ROOT, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def count_zip(d):
    return len([f for f in os.listdir(d) if f.endswith(".zip")]) if os.path.isdir(d) else None


def rt(x):
    u"""JSON の往復(tuple -> list、key の型をそろえる)。記録との比較に使う。"""
    return json.loads(json.dumps(x, ensure_ascii=False))


# ----------------------------------------------------------------------------------------------------------------
# engine の生の claim・本文・文の一覧を拾う(``LB._RawTap`` の土台に、``_member_material`` の ``text_`` を足す。返り値は同じ object)
class Tap(LB._RawTap):
    def __enter__(self):
        LB._RawTap.__enter__(self)
        self.mid = R._member_material
        inner, tap = self.mid, self

        def mm(zb, inst, text_, sentences, profile):
            out = inner(zb, inst, text_, sentences, profile)
            tap.cur["text_"] = text_
            return out
        R._member_material = mm
        return self

    def __exit__(self, *a):
        R._member_material = self.mid
        LB._RawTap.__exit__(self, *a)

    def snap(self):
        return {"num": dict((c["id"], c) for c in self.cur.get("num", [])), "sentences": list(self.cur.get("sentences", [])),
                "text_": self.cur.get("text_")}


def verify(tap, zb, prof, text):
    tap.cur.clear()
    out = VD.verify_document(zb, prof, text)
    if out["profile"] != prof:
        raise SystemExit(u"**profile が違う: %s != %s。止める**" % (out["profile"], prof))
    snap = tap.snap()
    ids = set(c["id"] for c in out["claims"])
    if not set(snap["num"]) <= ids:
        raise SystemExit(u"**tap が拾った num の claim が verify_document の出力に無い。止める**")
    if snap["text_"] is None:
        raise SystemExit(u"**tap が engine の本文を拾えていない。止める**")
    return out, snap


# ----------------------------------------------------------------------------------------------------------------
# §2-3 の 1・2・3(本文の位置 -> engine の文)。§6-5 の補い(空白を除いた字の並びで写す)もここ
def rebuild_sentences(text, paren):
    u"""engine の ``_split_lines`` と同じ切り方。段落の始まり + 断片の始まり + 断片の先頭の空白の字数 = 文の本文の始まり。"""
    out, pos = [], 0
    for para in text.split("\n"):
        pieces = E.split_after_kuten_outside_parens(para) if paren else re.split(r"(?<=。)", para)
        if "".join(pieces) != para:
            raise SystemExit(u"**断片をつなぐと段落に戻らない。止める**")
        off = pos
        for s in pieces:
            if s and s.strip():
                lead = len(s) - len(s.lstrip())
                st = s.strip()
                nf = unicodedata.normalize("NFKC", st)
                if nf == st:
                    cum, ok = None, True
                else:
                    parts = [unicodedata.normalize("NFKC", ch) for ch in st]
                    ok = "".join(parts) == nf
                    cum = [0]
                    for p_ in parts:
                        cum.append(cum[-1] + len(p_))
                out.append({"start": off + lead, "len": len(st), "nfkc": nf, "cum": cum, "ok": ok})
            off += len(s)
        pos += len(para) + 1
    return out


class Loc(object):
    u"""verify に渡した本文 ``given`` と engine の本文 ``snap['text_']`` の対応、engine の文の一覧の作り直し(W-T)。1 verify に 1 つ。"""

    def __init__(self, given, snap, prof):
        eng = snap["text_"]
        self.given, self.eng = given, eng
        self.sents = rebuild_sentences(eng, V.PROFILES[prof].paren_sentence)
        if [s["nfkc"] for s in self.sents] != snap["sentences"]:
            raise SystemExit(u"**作り直した文の一覧が engine の sentences と字で違う(W-T)。止める**")
        self.m = None
        if given == eng:
            self.word = T_SAME
        else:
            gi = [i for i, ch in enumerate(given) if not ch.isspace()]
            ei = [j for j, ch in enumerate(eng) if not ch.isspace()]
            if len(gi) != len(ei) or any(given[i] != eng[j] for i, j in zip(gi, ei)):
                self.word = T_OTHER
            else:
                self.word = T_WS
                self.m = dict(zip(gi, ei))

    def map_range(self, a, b):
        u"""(engine の本文の [始まり, 終わり), 理由)。決まらなければ (None, None, 理由)。"""
        if self.word == T_SAME:
            return a, b, None
        if self.word == T_OTHER:
            return None, None, U_OTHER
        nz = [i for i in range(a, b) if not self.given[i].isspace()]
        if not nz:
            return None, None, U_WSONLY
        return self.m[nz[0]], self.m[nz[-1]] + 1, None

    def locate(self, a, b):
        u"""engine の本文の [a, b) が 1 つの文に収まるなら (文の番号, (文の中の始まり, 終わり), None)。"""
        for i, s in enumerate(self.sents):
            if s["start"] <= a and (b - 1) < s["start"] + s["len"]:
                if not s["ok"]:
                    return None, None, U_NOFIT
                if s["cum"] is None:
                    return i, (a - s["start"], b - s["start"]), None
                return i, (s["cum"][a - s["start"]], s["cum"][b - s["start"]]), None
        return None, None, U_NOSENT


def claim_at(claims, snap, prof, si, ab):
    u"""§2-3 の 4・5(この便が自分で書く対応付けの規則)。文 ``si`` の中の範囲 ``ab`` と数の範囲が 1 字以上重なる num の claim の候補と、数の終わりが決まらなかった数。"""
    a2, b2 = ab
    sent = snap["sentences"][si]
    nums = R._numbers_of(V.PROFILES[prof], sent)
    cands, nend_unknown = [], 0
    for c in claims:
        r = snap["num"].get(c["id"])
        if r is None or r.get("sentence") != si:
            continue
        pos = r["pos"]
        ends = [t[1] for t in nums if t[0] == pos]
        e = ends[0] if ends else pos + 1
        if not ends:
            nend_unknown += 1
        if pos < b2 and a2 < e:
            cands.append(c)
    return cands, nend_unknown


def classify(unfixed, ncand, vid, same):
    u"""§2-4(先に当たったものを取る)。``same`` は候補がちょうど 1 つのときの、値で引いた id との一致。"""
    if unfixed:
        return C_UNFIX
    if ncand >= 2:
        return C_MANY
    if vid is None and ncand == 0:
        return C_NONE
    if vid is not None and ncand == 0:
        return C_VONLY
    if vid is None:
        return C_PONLY
    return C_SAME if same else C_DIFF


def value_kind(cv, rv):
    u"""(位置だけ)の細目(§6-5 の 3)。claim の値 cv と行の値 rv。"""
    if cv is None or rv is None:
        return P_ELSE
    if abs(cv - rv) <= TOL:
        return P_SAME
    if abs(abs(cv) - abs(rv)) <= TOL and (cv < 0) != (rv < 0):
        return P_SIGN
    if rv != 0 and cv != 0 and (cv > 0) == (rv > 0):
        lg = math.log10(abs(cv / rv))
        k = round(lg)
        if k != 0 and abs(lg - k) < 1e-9:
            return P_POW10
    return P_ELSE


def observe(loc, claims, snap, prof, rng, vid, rowval):
    u"""1 行の観測(位置の観測と分類・細目)。``rng`` は verify に渡した本文の [始まり, 終わり)。"""
    a0, b0, why = loc.map_range(rng[0], rng[1])
    d = {u"本文": loc.word, u"範囲": [rng[0], rng[1]], u"写した範囲": None if a0 is None else [a0, b0]}
    vr = snap["num"].get(vid) if vid is not None else None
    d[u"値で引いた"] = None if vid is None else {u"id": vid, u"文の番号": (vr or {}).get("sentence"), u"pos": (vr or {}).get("pos"), u"num の claim": vr is not None}
    si, ab = None, None
    if a0 is not None:
        si, ab, why = loc.locate(a0, b0)
    if a0 is None or si is None:
        d.update({u"文の番号": None, u"文の中の範囲": None, u"位置の候補": [], u"数の終わりが決まらない": 0, u"位置で引いた": None,
                  u"分類": classify(True, 0, vid, False), u"細目": why})
        return d
    cands, neu = claim_at(claims, snap, prof, si, ab)
    same = len(cands) == 1 and vid is not None and cands[0]["id"] == vid
    cls = classify(False, len(cands), vid, same)
    d.update({u"文の番号": si, u"文の中の範囲": [ab[0], ab[1]], u"位置の候補": [c["id"] for c in cands], u"数の終わりが決まらない": neu})
    pc = cands[0] if len(cands) == 1 else None
    if pc is not None:
        pr = snap["num"][pc["id"]]
        d[u"位置で引いた"] = {u"id": pc["id"], u"文の番号": pr["sentence"], u"pos": pr["pos"],
                          u"値が行の値と同じ": pc.get("value") is not None and rowval is not None and abs(pc["value"] - rowval) <= TOL}
    else:
        d[u"位置で引いた"] = None
    det = None
    if cls == C_DIFF:
        det = D_NOTNUM if vr is None else (D_SAMESENT if vr.get("sentence") == si else D_OTHERSENT)
    elif cls == C_PONLY:
        det = value_kind(pc.get("value"), rowval)
    elif cls == C_VONLY:
        has = [t for t in R._numbers_of(V.PROFILES[prof], snap["sentences"][si]) if t[0] < ab[1] and ab[0] < t[1]]
        det = V_HASNUM if has else V_NONUM
    elif cls == C_MANY:
        det = u"候補 %d 件" % len(cands)
    d[u"分類"], d[u"細目"] = cls, det
    return d


def decided(o):
    return o[u"分類"] not in (C_UNFIX, C_MANY)


# ----------------------------------------------------------------------------------------------------------------
# 判定の形(封 §2-5。記録が持つ判定の形)
def jud_A1(c):
    a, b = MB.A1.core_pointer_say(c), MB.A1.core_say(c)
    return {u"Core": [a[u"言うこと"], a[u"参照先"], a[u"state"]], u"Core(厳しい読み方)": [b[u"言うこと"], b[u"参照先"], b[u"state"]]}


def key_A1(j):
    return [j[u"Core"][:2], j[u"Core(厳しい読み方)"][:2]]


def jud_A2(c):
    s = MB.A1.core_pointer_say(c)
    return [HT.core_state(s), s[u"参照先"]]


def jud_B(c, inj, gold):
    out = {}
    for nm, say in ((u"Core", AC.core_say(c)), (u"Core-P", AC.core_pointer_say(c))):
        out[nm] = [say[u"言うこと"], say[u"参照先"], AC.judge(inj, say, gold)]
    return out


def finish(o, jv, jp_of, by, key=lambda x: x):
    u"""判定(値)・判定(位置)・判定が変わる を ``o`` に足す。位置が決まらない・1 件に決まらない行は判定を作らない。"""
    o[u"判定(値)"] = jv
    if not decided(o):
        o[u"判定(位置)"], o[u"判定が変わる"] = None, None
        return o
    pc = by.get(o[u"位置の候補"][0]) if o[u"位置の候補"] else None
    jp = jp_of(pc)
    o[u"判定(位置)"] = jp
    o[u"判定が変わる"] = key(jv) != key(jp)
    return o


# ----------------------------------------------------------------------------------------------------------------
# 単位(書類ごと)。fork の子で走る。CTX は親が作った読み込み済みの記録
CTX = {}


def read_zip(doc):
    with io.open(ED.cache_path(doc), "rb") as fh:
        return fh.read()


def gate_add(g, name, ok):
    x = g.setdefault(name, [0, 0])
    x[0] += 1 if ok else 0
    x[1] += 1


def unit_A1(doc):
    t0 = time.time()
    g, rows_out = {}, []
    zb = read_zip(doc)
    gate_add(g, u"W-A1-1 ZIP の sha256", hashlib.sha256(zb).hexdigest() == CTX["fetched_by"][doc])
    work = tempfile.mkdtemp(prefix="rowclaim_A1_", dir=os.environ.get("TMPDIR"))
    old, MB.A1.TMP = MB.A1.TMP, work
    try:
        text, refs = MB.A1.material(doc)
    finally:
        MB.A1.TMP = old
    chosen, _c = MB.pick_injections(text, refs, CTX["seed"], doc)
    tampered, pl = IJ.apply_edits(text, chosen)
    if IJ.revert(tampered, chosen, pl, text) != text:
        raise SystemExit(u"**round-trip が合わない: %s。止める**" % doc)
    rows, _n = MB.build_rows(tampered, chosen, pl)
    task = MB.seat_text(rows, tampered, refs)
    gate_add(g, u"W-A1-1 材料の sha256", hashlib.sha256(task.encode("utf-8")).hexdigest() == CTX["mat_by"][doc][u"材料"][u"sha256"])
    ctype = dict((c["id"], c["type"]) for c in chosen)
    with Tap() as tap:
        out, snap = verify(tap, zb, "P16", tampered)
    claims = out["claims"]
    by = dict((c["id"], c) for c in claims)
    loc = Loc(tampered, snap, "P16")
    vids = dict((r["id"], RM.claim_of(r, claims)) for r in rows)
    mult = collections.Counter(v for v in vids.values() if v is not None)
    pre = CTX["mat_by"][doc][u"席の前に出せる分"]
    for r in rows:
        rid, vid = r["id"], vids[r["id"]]
        jv = jud_A1(by.get(vid))
        gate_add(g, u"W-A1-2 値で引いた id = p20_rerun の主張 id(P16)", vid == CTX["p20_by"][(doc, rid)][u"主張 id(P16)"])
        gate_add(g, u"W-A1-3 判定 = 材料の Core・Core(厳しい読み方)", jv[u"Core"] == [pre[rid][u"Core"][u"言うこと"], pre[rid][u"Core"][u"参照先"], pre[rid][u"Core"][u"state"]]
                 and jv[u"Core(厳しい読み方)"] == [pre[rid][u"Core(厳しい読み方)"][u"言うこと"], pre[rid][u"Core(厳しい読み方)"][u"参照先"], pre[rid][u"Core(厳しい読み方)"][u"state"]]
                 and MB.A1.core_pointer_say(by.get(vid)) == pre[rid][u"Core"] and MB.A1.core_say(by.get(vid)) == pre[rid][u"Core(厳しい読み方)"])
        for nm, dd, key in (("role_swap", CTX["rsw_by"], u"主張 id"), ("verify_inventory", CTX["inv_by"], u"主張 id"), ("pnf_diag", CTX["pnf_by"], u"Core の主張 id")):
            x = dd.get((doc, rid))
            if x is not None and x.get(key) is not None:
                gate_add(g, u"W-A1-5 %s の主張 id = 値で引いた id" % nm, x[key] == vid)
        o = observe(loc, claims, snap, "P16", r["span"], vid, r[u"値"])
        o = finish(o, jv, lambda pc: jud_A1(pc), by, key_A1)
        o.update({u"母集団": "A1", u"profile": "P16", u"doc": doc, u"id": rid, u"型": ctype.get(r.get("**注入**")), u"注入か": bool(r.get("**注入**")),
                  u"共有された": bool(vid is not None and mult[vid] > 1)})
        rows_out.append(o)
    return {"pop": "A1", "doc": doc, "rows": rows_out, "gates": g, "sec": round(time.time() - t0), "zip": hashlib.sha256(zb).hexdigest(),
            "vids": dict((k, v) for k, v in vids.items()),
            "wt": {u"P16": {loc.word: 1}}}


def unit_A2(doc):
    t0 = time.time()
    g, rows_out, wt = {}, [], {}
    zb = read_zip(doc)
    work = tempfile.mkdtemp(prefix="rowclaim_A2_", dir=os.environ.get("TMPDIR"))
    with HS2.patched():
        rb = HS2.rebuild(doc, work, CTX["seed"])
    gate_add(g, u"W-A2-1 材料の sha256", hashlib.sha256(rb["task"].encode("utf-8")).hexdigest() == CTX["s2_by"][doc][u"材料"][u"sha256"])
    chosen = dict((c["id"], c) for c in rb["chosen"])
    for prof in PROFILES["A2"]:
        with Tap() as tap:
            out, snap = verify(tap, zb, prof, rb["tampered"])
        claims = out["claims"]
        by = dict((c["id"], c) for c in claims)
        loc = Loc(rb["tampered"], snap, prof)
        wt[prof] = {loc.word: 1}
        csf = PB.core_say_for(zb, rb["tampered"], prof, rb["rows"])
        for r in rb["rows"]:
            rid = r["id"]
            vid = RM.claim_of(r, claims)
            say = MB.A1.core_pointer_say(by.get(vid))
            gate_add(g, u"W-A2-2 %s core_say_for と同じ" % prof, say == csf[rid])
            if prof == "P22":
                want = CTX["e4_by"][(doc, rid)][u"Core 自身 P22"]
                gate_add(g, u"W-A2-2 P22 の判定 = E4 の Core 自身 P22", {u"state": HT.core_state(say), u"参照先": say[u"参照先"]} == want)
            inj = r.get("**注入**")
            o = observe(loc, claims, snap, prof, r["span"], vid, r[u"値"])
            o = finish(o, jud_A2(by.get(vid)), lambda pc: jud_A2(pc), by)
            o.update({u"母集団": "A2", u"profile": prof, u"doc": doc, u"id": rid, u"型": chosen[inj]["type"] if inj else None, u"注入か": bool(inj)})
            rows_out.append(o)
    return {"pop": "A2", "doc": doc, "rows": rows_out, "gates": g, "sec": round(time.time() - t0), "zip": hashlib.sha256(zb).hexdigest(), "wt": wt}


class SnapRecorder(GC.Recorder):
    u"""``GC.Recorder`` に、各注入の ``claim_for`` が呼ばれた時点の tap の中身(その注入の verify の生の claim・本文・文の一覧)を足す。返り値は同じ object。"""

    def __init__(self, tap):
        GC.Recorder.__init__(self)
        self.tap = tap
        self.snaps = []

    def __enter__(self):
        GC.Recorder.__enter__(self)
        self.mid = AC.claim_for
        inner, me = self.mid, self

        def claim_for(claims, inj):
            c = inner(claims, inj)
            me.snaps.append((inj["id"], me.tap.snap()))
            return c
        AC.claim_for = claim_for
        return self

    def __exit__(self, *a):
        AC.claim_for = self.mid
        GC.Recorder.__exit__(self, *a)
        return False


def unit_B(pop, doc):
    t0 = time.time()
    g, rows_out, wt = {}, [], {}
    zb = read_zip(doc)
    work = tempfile.mkdtemp(prefix="rowclaim_%s_" % pop, dir=os.environ.get("TMPDIR"))
    old_tmp, AC.TMP = AC.TMP, work
    try:
        for prof in PROFILES[pop]:
            text0, _refs = AC.material(doc)
            orig_cf = AC.claim_for
            with Tap() as tap:
                _o0, snap0 = verify(tap, zb, prof, text0)
                with SnapRecorder(tap) as rec:
                    rows, _counts = AC.run_doc(doc, CTX["seed"], prof)
            if AC.claim_for is not orig_cf:
                raise SystemExit(u"**AC.claim_for が戻っていない。止める**")
            want = [r for r in CTX["brec"][(pop, prof)] if r["doc"] == doc]
            gate_add(g, u"W-B-1 run_doc の rows = 記録の rows(%s %s)" % (pop, prof), rt(rows) == want)
            gate_add(g, u"W-B-2 Recorder の件数 = rows", len(rec.apply) == len(rec.claims) == len(rows) == len(rec.snaps))
            app = dict((x[0], (x[1], x[2])) for x in rec.apply)
            snapd = dict(rec.snaps)
            wt_c = collections.Counter()
            for (iid, inj, c, claims), row in zip(rec.claims, rows):
                if iid != row["id"]:
                    raise SystemExit(u"**Recorder の id が合わない。止める**")
                tampered, placements = app[iid]
                snap = snapd[iid]
                if pop == "B2" and prof in ("P16", "P20"):
                    gate_add(g, u"W-B-2 拾った claim の id = c0 の記録(%s)" % prof, (c["id"] if c else None) == CTX["c0claims"][prof].get(iid))
                loc = Loc(tampered, snap, prof)
                wt_c[loc.word] += 1
                by = dict((x["id"], x) for x in claims)
                vid = c["id"] if c else None
                gold = AC.gold_of(inj)
                o = observe(loc, claims, snap, prof, placements[iid], vid, inj["new_value"])
                ds = T2D.diff_sentence(snap0["sentences"], snap["sentences"])[0]
                o[u"diff_sentence の番号"] = ds
                if o.get(u"文の番号") is not None and inj["type"] != "T3_ABSENT":
                    o[u"diff_sentence と同じ"] = ds == o[u"文の番号"]
                else:
                    o[u"diff_sentence と同じ"] = None
                jv = jud_B(c, inj, gold)
                o = finish(o, jv, lambda pc, _i=inj, _g=gold: jud_B(pc, _i, _g), by)
                o.update({u"母集団": pop, u"profile": prof, u"doc": doc, u"id": iid, u"型": inj["type"], u"注入か": True})
                rows_out.append(o)
            wt[prof] = dict(wt_c)
    finally:
        AC.TMP = old_tmp
    return {"pop": pop, "doc": doc, "rows": rows_out, "gates": g, "sec": round(time.time() - t0), "zip": hashlib.sha256(zb).hexdigest(), "wt": wt}


def run_unit(a):
    pop, doc = a
    with contextlib.redirect_stdout(io.StringIO()):          # prepare_xbrl の印字を捨てる
        if pop == "A1":
            return unit_A1(doc)
        if pop == "A2":
            return unit_A2(doc)
        return unit_B(pop, doc)


# ----------------------------------------------------------------------------------------------------------------
# 入力(記録)を読む。親で 1 回
def prepare(ndocs):
    recs = dict((k, jload(v)) for k, v in REC.items() if v.endswith(".json"))
    seed, meta = IJ.verify_seed_sealed(MB.SEED_FILE)
    docs = {}
    docs["A1"] = list(recs["draw"][u"引いた 8 件"])
    docs["A2"] = [p["docID"] for p in recs["s2_material"][u"書類ごと"]]
    docs["B1"] = list(recs["ac_p16"][u"書類"])
    docs["B2"] = list(recs["c0"][u"材料"][u"書類"])
    if ndocs is not None:
        docs = dict((k, v[:ndocs]) for k, v in docs.items())
    CTX.update({
        "recs": recs, "seed": seed, "seed_meta": meta, "docs": docs,
        "fetched_by": dict((x["docID"], x["sha256"]) for x in recs["fetched"][u"取得した書類"]),
        "mat_by": dict((p["docID"], p) for p in recs["material"][u"書類ごと"]),
        "p20_by": dict(((r["doc"], r["id"]), r) for r in recs["p20_rerun"]["rows"]),
        "rsw_by": dict(((r["doc"], r["id"]), r) for r in recs["role_swap"]["rows"]),
        "inv_by": dict(((r["doc"], r["id"]), r) for r in recs["verify_inventory"][u"**第 2 部 実物での発火**"]["rows"]),
        "pnf_by": dict(((r["doc"], r["id"]), r) for r in recs["pnf_diag"]["rows"]),
        "s2_by": dict((p["docID"], p) for p in recs["s2_material"][u"書類ごと"]),
        "e4_by": dict(((r["doc"], r["id"]), r) for r in recs["period_bind"]["E4"][u"行"]),
        "brec": {("B1", "P16"): recs["ac_p16"]["rows"], ("B1", "P20"): recs["ac_p20"]["rows"], ("B1", "P21"): recs["naming_fix"][u"cd8 (ア) rows(P21)"],
                 ("B2", "P16"): recs["c0"][u"C0-2 rows"], ("B2", "P20"): recs["c0_p20"][u"C0-2 rows(P20)"], ("B2", "P21"): recs["naming_fix"][u"gen_c (ア) rows(P21)"]},
        "c0claims": {"P16": dict((x["id"], x["claim"]["id"] if x.get("claim") else None) for x in recs["c0"][u"C0-2 各注入に対応が付いた Core の claim(読むための記録)"]),
                     "P20": dict((x["id"], x["claim"]["id"] if x.get("claim") else None) for x in recs["c0_p20"][u"C0-2 各注入に対応が付いた Core の claim(P20。読むための記録)"])},
    })


# ----------------------------------------------------------------------------------------------------------------
# 配線の門のうち全書類の合計に当てるもの(W-A1-4)
def rowclaim_totals(vids_by_doc, mat_by, docs):
    u"""``rowclaim_map`` の ``合計`` の 10 欄を、値で引いた id から数え直す(``xbrl_rowclaim_map`` の ``main`` と同じ式)。"""
    t = collections.Counter()
    for doc in docs:
        m = vids_by_doc[doc]
        pre = mat_by[doc][u"席の前に出せる分"]
        mult = collections.Counter(v for v in m.values() if v is not None)
        sh = dict((cid, sorted(rid for rid, v in m.items() if v == cid)) for cid, n in mult.items() if n > 1)
        t[u"行"] += len(m)
        t[u"対応が付かない行"] += sum(1 for v in m.values() if v is None)
        t[u"共有された行"] += sum(len(v) for v in sh.values())
        t[u"共有された主張"] += len(sh)
        for rid, cid in m.items():
            gd = pre[rid][u"正解"]
            if not (gd and gd.get(u"種類") == u"参照先が在る"):
                continue
            one = cid is not None and mult[cid] == 1
            hit = pre[rid]["Core"][u"参照先"] == gd[u"正解"]
            t[u"T5"] += 1
            t[u"T5 のうち 1 対 1"] += one
            t[u"T5 のうち対応が付かない"] += cid is None
            t[u"T5 のうち共有"] += (cid is not None and mult[cid] > 1)
            t[u"特定(全部の行)"] += hit
            if one:
                t[u"特定(1 対 1 の行だけ)"] += hit
    return dict(t)


RC_KEYS = (u"行", u"対応が付かない行", u"共有された行", u"共有された主張", u"T5", u"T5 のうち 1 対 1", u"T5 のうち対応が付かない", u"T5 のうち共有", u"特定(全部の行)", u"特定(1 対 1 の行だけ)")


# ----------------------------------------------------------------------------------------------------------------
# §2-6 の 1: 数え直し(記録を作った関数をそのまま当てる。位置の判定を入れるのは ``jsel`` が持つ行だけ)
def _sub_A1(mat, jsel):
    m2 = copy.deepcopy(mat)
    for p in m2[u"書類ごと"]:
        for rid, pre in p[u"席の前に出せる分"].items():
            j = jsel.get((p["docID"], rid))
            if j is not None:
                a, b = j[u"Core"], j[u"Core(厳しい読み方)"]
                pre["Core"] = {u"言うこと": a[0], u"参照先": a[1], u"state": a[2]}
                pre[u"Core(厳しい読み方)"] = {u"言うこと": b[0], u"参照先": b[1], u"state": b[2]}
    return m2


def recount_A1(mat, score, jsel):
    m2 = _sub_A1(mat, jsel)
    pre_by = dict(((p["docID"], rid), pre) for p in m2[u"書類ごと"] for rid, pre in p[u"席の前に出せる分"].items())
    rows = []
    for r in score["rows"]:
        pre = pre_by[(r["doc"], r["id"])]
        arms = XS.arms_of(r[u"席"], pre)
        row = {"doc": r["doc"], "id": r["id"], u"注入か": pre[u"注入か"], u"正解": pre[u"正解"], u"席": r[u"席"], u"腕": {}}
        for name, arm in arms.items():
            row[u"腕"][name] = dict(arm)
            row[u"腕"][name][u"判定結果"] = XS.verdict(arm, pre[u"正解"], pre[u"注入か"])
        rows.append(row)
    t = XS.tally(rows)
    seat_by = dict(((r["doc"], r["id"]), r) for r in score["rows"])
    t5 = XC.t5_rows(m2, seat_by)
    return {u"採点": t, u"主比較の判定": XS.judge_z(t), u"α の天井": XC.ceiling(t5),
            u"Core 自身の特定率(本番)": XC.rate(sum(1 for r in t5 if r[u"Core の参照先"] == r[u"正解"]), len(t5))}


def recount_A2(e4rows, jsel22, jsel27):
    rows = copy.deepcopy(e4rows)
    for r in rows:
        j = jsel22.get((r["doc"], r["id"]))
        if j is not None:
            r[u"Core 自身 P22"] = {u"state": j[0], u"参照先": j[1]}
    inj = [r for r in e4rows if r[u"注入か"]]
    g27 = sum(1 for r in inj if (jsel27.get((r["doc"], r["id"])) or [None])[0] == "GROUNDED")
    return {u"E4 集計": PB.e4_summary(rows), u"S6 段 2": PB.frac(g27, len(inj))}


def recount_B(recrows, jsel):
    rows = copy.deepcopy(recrows)
    for r in rows:
        j = jsel.get((r["doc"], r["id"]))
        if j is not None:
            for nm in (u"Core", u"Core-P"):
                x = j[nm]
                r[u"腕"][nm] = {u"言うこと": x[0], u"参照先": x[1], u"判定": x[2]}
    return {u"AC.tally": AC.tally(rows), u"NF.score": NF.score(rows)}


def upd(a, b):
    c = dict(a)
    c.update(b)
    return c


def leaves(x, pre=u""):
    u"""入れ子の dict の葉(list は葉)。{path: 値}。"""
    if isinstance(x, dict):
        out = {}
        for k, v in x.items():
            out.update(leaves(v, pre + u" > " + str(k) if pre else str(k)))
        return out
    return {pre: x}


def moved(rec, new):
    a, b = leaves(rt(rec)), leaves(rt(new))
    return sorted(set(k for k in set(a) | set(b) if a.get(k, u"(欄なし)") != b.get(k, u"(欄なし)")))


def judges_by(rows, pop, prof, which):
    u"""{(doc, id): 判定}。which = ``判定(値)`` か ``判定(位置)``(位置は決まった行だけ)。"""
    out = {}
    for r in rows:
        if r[u"母集団"] == pop and r[u"profile"] == prof and r.get(which) is not None:
            out[(r["doc"], r["id"])] = r[which]
    return out


def all_recounts(rows, recs):
    u"""§2-6 の 1 の全部。[{節, 記録, 値で数え直し, 位置で数え直し, 動いた欄, …}]。"""
    mat, score = recs["material"], recs["score"]
    items = []

    def add(pop, prof, label, rel, keypath, rec_value, v_val, v_pos):
        items.append({u"母集団": pop, u"profile": prof, u"欄": label, u"記録の節": rel + u"#" + u" > ".join(keypath), u"_rel": rel, u"_keypath": keypath,
                      u"記録": rec_value, u"値で数え直し": v_val, u"位置で数え直し": v_pos, u"値で数え直しが記録と一致": rt(v_val) == rt(rec_value),
                      u"動いた欄": moved(rec_value, v_pos)})

    # A1
    jv = judges_by(rows, "A1", "P16", u"判定(値)")
    jp = judges_by(rows, "A1", "P16", u"判定(位置)")
    rv, rp = recount_A1(mat, score, jv), recount_A1(mat, score, upd(jv, jp))
    ce = recs["ceiling"]
    add("A1", "P16", u"採点", REC["score"], [u"採点"], score[u"採点"], rv[u"採点"], rp[u"採点"])
    add("A1", "P16", u"主比較の判定", REC["score"], [u"**主比較の判定**"], score[u"**主比較の判定**"], rv[u"主比較の判定"], rp[u"主比較の判定"])
    add("A1", "P16", u"α の天井", REC["ceiling"], [u"**α の天井(席が外した行で Core が正解を持っていたか)**"], ce[u"**α の天井(席が外した行で Core が正解を持っていたか)**"], rv[u"α の天井"], rp[u"α の天井"])
    add("A1", "P16", u"Core 自身の特定率(本番)", REC["ceiling"], [u"Core 自身の特定率", u"本番(未使用 8 書類)"], ce[u"Core 自身の特定率"][u"本番(未使用 8 書類)"],
        rv[u"Core 自身の特定率(本番)"], rp[u"Core 自身の特定率(本番)"])
    # A2
    e4rows = recs["period_bind"]["E4"][u"行"]
    j22v, j22p = judges_by(rows, "A2", "P22", u"判定(値)"), judges_by(rows, "A2", "P22", u"判定(位置)")
    j27v, j27p = judges_by(rows, "A2", "P27", u"判定(値)"), judges_by(rows, "A2", "P27", u"判定(位置)")
    a2v, a2p = recount_A2(e4rows, j22v, j27v), recount_A2(e4rows, upd(j22v, j22p), upd(j27v, j27p))
    add("A2", "P22", u"E4 の集計", REC["period_bind"], ["E4", u"集計"], recs["period_bind"]["E4"][u"集計"], a2v[u"E4 集計"], a2p[u"E4 集計"])
    add("A2", "P27", u"全注入で Core 自身(既定)が GROUNDED", REC["default_p27"], ["S6", u"段 2", u"全注入で Core 自身(既定)が GROUNDED"],
        recs["default_p27"]["S6"][u"段 2"][u"全注入で Core 自身(既定)が GROUNDED"], a2v[u"S6 段 2"], a2p[u"S6 段 2"])
    # B
    nf = recs["naming_fix"]
    ac_sec = {("B1", "P16"): (REC["ac_p16"], [u"採点"], recs["ac_p16"][u"採点"]), ("B1", "P20"): (REC["ac_p20"], [u"採点"], recs["ac_p20"][u"採点"]),
              ("B2", "P16"): (REC["c0"], [u"**C0-2 (ア) の main() の出力**", u"採点"], recs["c0"][u"**C0-2 (ア) の main() の出力**"][u"採点"]),
              ("B2", "P20"): (REC["c0_p20"], [u"**C0-2 (ア) の main() の出力(P20)**", u"採点"], recs["c0_p20"][u"**C0-2 (ア) の main() の出力(P20)**"][u"採点"])}
    nf_sec = {("B1", "P20"): u"cd8 (ア) P20(記録)の採点", ("B1", "P21"): u"cd8 (ア) P21 の採点", ("B2", "P20"): u"gen_c (ア) P20 の採点", ("B2", "P21"): u"gen_c (ア) P21 の採点"}
    for pop in ("B1", "B2"):
        for prof in PROFILES[pop]:
            recrows = CTX["brec"][(pop, prof)]
            bv = recount_B(recrows, judges_by(rows, pop, prof, u"判定(値)"))
            bp = recount_B(recrows, upd(judges_by(rows, pop, prof, u"判定(値)"), judges_by(rows, pop, prof, u"判定(位置)")))
            if (pop, prof) in ac_sec:
                rel, kp, val = ac_sec[(pop, prof)]
                add(pop, prof, u"採点(AC.tally)", rel, kp, val, bv[u"AC.tally"], bp[u"AC.tally"])
            else:
                items.append({u"母集団": pop, u"profile": prof, u"欄": u"採点(AC.tally。記録の欄なし)", u"記録の節": None, u"_rel": None, u"_keypath": None, u"記録": None,
                              u"値で数え直し": bv[u"AC.tally"], u"位置で数え直し": bp[u"AC.tally"], u"値で数え直しが記録と一致": None,
                              u"動いた欄": moved(bv[u"AC.tally"], bp[u"AC.tally"])})
            if (pop, prof) in nf_sec:
                add(pop, prof, u"採点(NF.score)", REC["naming_fix"], [nf_sec[(pop, prof)]], nf[nf_sec[(pop, prof)]], bv[u"NF.score"], bp[u"NF.score"])
    return items


# ----------------------------------------------------------------------------------------------------------------
# §2-6 の 2: 行の重なりだけを数える(記録の節の行の集合と、この便の行)
def overlap_sets(recs):
    u"""[(母集団, profile, 記録の file, 節の名, [(doc, id)])]。A2 の P21 は測らないので、同じ行の集合を P22 と P27 の両方に当てる。"""
    out = []

    def add(pop, profs, rel, name, keys):
        for prof in profs:
            out.append((pop, prof, rel, name, keys))
    ks = lambda rows, k="id": [(r["doc"], r[k]) for r in rows]
    add("A1", ["P16"], REC["role_swap"], u"rows(主張 id が None でない行)", ks([r for r in recs["role_swap"]["rows"] if r.get(u"主張 id") is not None]))
    add("A1", ["P16"], REC["role_swap"], u"rows(全部)", ks(recs["role_swap"]["rows"]))
    add("A1", ["P16"], REC["contract_v1"], u"rows", ks(recs["contract_v1"]["rows"]))
    add("A1", ["P16"], REC["verify_inventory"], u"第 2 部 rows", ks(recs["verify_inventory"][u"**第 2 部 実物での発火**"]["rows"]))
    add("A1", ["P16"], REC["pnf_diag"], u"rows", ks(recs["pnf_diag"]["rows"]))
    add("A1", ["P16"], REC["p20_rerun"], u"rows", ks(recs["p20_rerun"]["rows"]))
    add("A1", ["P16"], REC["p20_pred_recheck"], u"rows(行)", ks(recs["p20_pred_recheck"]["rows"], u"行"))
    add("A2", ["P22", "P27"], REC["period_bind"], u"E4 > 行(P21 の欄)", ks(recs["period_bind"]["E4"][u"行"]))
    add("B1", ["P16"], REC["ceiling"], u"Core 自身の特定率 > (ア)(T5 で対応が付いた行)",
        [(r["doc"], r["id"]) for r in recs["ac_p16"]["rows"] if r[u"型"] == "T5_COINCIDENT" and r[u"対応が付いた"]])
    add("B2", ["P16"], REC["c1"], u"**K-4・K-5 の数** > rows", ks(recs["c1"][u"**K-4・K-5 の数**"]["rows"], u"注入の id"))
    add("B2", ["P20", "P21"], REC["naming_fix"], u"**K-4 の再計算** > rows", ks(recs["naming_fix"][u"**K-4 の再計算**"]["rows"], u"注入の id"))
    add("B2", ["P16"], REC["c0"], u"**C0-3 ...** > rows", ks(recs["c0"][u"**C0-3 engine を Core-P の参照先に当てた**"]["rows"]))
    add("B2", ["P20"], REC["c0_p20"], u"**C0-3 ...(P20)** > rows", ks(recs["c0_p20"][u"**C0-3 engine を Core-P(P20)の参照先に当てた**"]["rows"]))
    add("B2", ["P21"], REC["naming_fix"], u"**C0-3 ...(P21)** > rows", ks(recs["naming_fix"][u"**C0-3 engine を Core-P(P21)の参照先に当てた**"]["rows"]))
    return out


def overlaps(rows, recs):
    info = {}
    for r in rows:
        info[(r[u"母集団"], r["profile"], r["doc"], r["id"])] = (r[u"分類"], r[u"判定が変わる"])
    out = []
    for pop, prof, rel, name, keys in overlap_sets(recs):
        hit = [info[(pop, prof, d, i)] for d, i in keys if (pop, prof, d, i) in info]
        out.append({u"母集団": pop, u"profile": prof, u"記録": rel, u"節": name, u"行の集合": len(keys), u"この便の行に在る": len(hit),
                    u"(違う)": sum(1 for c, _ in hit if c == C_DIFF), u"(値だけ)": sum(1 for c, _ in hit if c == C_VONLY), u"(位置だけ)": sum(1 for c, _ in hit if c == C_PONLY),
                    u"分類が(違う)(値だけ)(位置だけ)の行": sum(1 for c, _ in hit if c in (C_DIFF, C_VONLY, C_PONLY)),
                    u"(位置が決まらない)+(位置で 1 件に決まらない)": sum(1 for c, _ in hit if c in (C_UNFIX, C_MANY)),
                    u"判定が変わる行": sum(1 for _, ch in hit if ch)})
    return out


# ----------------------------------------------------------------------------------------------------------------
# §2-7: 台帳の行
LEDGER_MECH = ("M-03", "M-05", "M-13", "M-16", "M-18", "M-20", "M-21", "M-23")
BLOCK_RE = re.compile(r"<!-- 門:start (\S+) -->\n(.*?)\n<!-- 門:end -->", re.S)


def ledger_block_text(harness_doc):
    u"""総点検の文書の読み分けの表(ledger)の門のブロックの中の字(開きと閉じの印の行は含まない)。"""
    blocks = BLOCK_RE.findall(harness_doc)
    named = [b for n, b in blocks if n == LEDGER_BLOCK]
    if len(named) != 1:
        raise SystemExit(u"**総点検の文書に門のブロック %s が %d 個。止める**" % (LEDGER_BLOCK, len(named)))
    return named[0]


def ledger_rows_part(harness_doc, facts_doc):
    u"""台帳の §2-7 の対象の行(ID は総点検の文書の表で選ぶ)。台帳の file の中の並びのまま、(ID の列, 行の字を改行でつないだもの)。
    対象の ID の行が台帳に 1 つずつ在らなければ止める。"""
    ids = set(t[0] for t in ledger_targets(harness_doc))
    found = collections.OrderedDict()
    for line in facts_doc.split(u"\n"):
        rid = FC.row_id(line)
        if rid in ids:
            found.setdefault(rid, []).append(line)
    if set(found) != ids or any(len(v) != 1 for v in found.values()):
        raise SystemExit(u"**台帳に対象の行が 1 つずつ在らない(在る %d・対象 %d)。止める**" % (len(found), len(ids)))
    return list(found), u"\n".join(v[0] for v in found.values())


def ledger_targets(harness_doc):
    u"""総点検の文書の ledger の表のうち、``引いた仕掛け`` が対象の仕掛けのどれかを含む行。[(ID, 引いた仕掛け, 読み)]。"""
    blk = ledger_block_text(harness_doc)
    out = []
    for line in blk.split(u"\n"):
        if not line.startswith(u"|"):
            continue
        cells = [c.strip() for c in line.strip().strip(u"|").split(u"|")]
        if len(cells) >= 4 and FC.ID_RE.match(cells[0]) and any(m in re.findall(r"M-\d+", cells[1]) for m in LEDGER_MECH):
            out.append((cells[0], cells[1], cells[3]))
    return out


def mark_files(body):
    return sorted(set(re.findall(r"(\S+?\.json)#", body)))


def eval_marks(marks):
    u"""[(行, 種類, 本体)] -> {index: 'ok' | 'ng' | 'skip'}。"""
    out = {}
    for k, (rid, kind, body) in enumerate(marks):
        try:
            FC.evaluate(kind, body)
            out[k] = "ok"
        except FC.Skip:
            out[k] = "skip"
        except Exception:
            out[k] = "ng"
    return out


def ledger_words(recs, items, ovl):
    u"""§2-7 の 3・4。影の記録は memory の中(``FC._CACHE``)。file には書かない。"""
    doc_text = FC.read_doc()
    with io.open(os.path.join(ROOT, HARNESS_REL), encoding="utf-8") as fh:
        tg = ledger_targets(fh.read())
    ids = [t[0] for t in tg]
    marks = [(rid, kind, body) for (_ln, rid, kind, body, _bare) in FC.claims(doc_text) if rid in ids]
    FC._CACHE.clear()
    real = eval_marks(marks)
    shadow = {}
    for it in items:
        if it[u"_rel"] is None:
            continue
        rel = it[u"_rel"]
        if rel not in shadow:
            shadow[rel] = copy.deepcopy(jload(rel))
        node = shadow[rel]
        for k in it[u"_keypath"][:-1]:
            node = node[k]
        node[it[u"_keypath"][-1]] = it[u"位置で数え直し"]
    FC._CACHE.clear()
    for rel, v in shadow.items():
        FC._CACHE[rel] = v
    shad = eval_marks(marks)
    FC._CACHE.clear()
    rel1 = set(it[u"_rel"] for it in items if it[u"_rel"])
    rel2 = set(o[u"記録"] for o in ovl)
    rel2_changed = set(o[u"記録"] for o in ovl if o[u"判定が変わる行"] >= 1)
    out = []
    for rid, mech, read in tg:
        mk = [k for k, m in enumerate(marks) if m[0] == rid]
        moving = [k for k in mk if real[k] == "ok" and shad[k] != "ok"]
        files = sorted(set(f for k in mk for f in mark_files(marks[k][2])))
        if moving:
            word = u"数が動く"
        elif any(f in rel2_changed for f in files):
            word = u"動きうる(数え直していない)"
        elif any(f in rel1 or f in rel2 for f in files):
            word = u"動かない"
        else:
            word = u"この便の外"
        out.append({u"台帳の行": rid, u"引いた仕掛け": mech, u"読み": read, u"印": len(mk), u"本物で通らなかった印": sum(1 for k in mk if real[k] != "ok"),
                    u"動く印": len(moving), u"引く記録": files, u"語": word})
    return out


# ----------------------------------------------------------------------------------------------------------------
def dump_record(rec, rowkeys):
    u"""rows は 1 行 1 件の compact JSON。それ以外は indent=1。妥当な JSON。"""
    parts = []
    for k, v in rec.items():
        if k in rowkeys:
            body = u"[\n" + u",\n".join(u"  " + json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in v) + u"\n ]"
        else:
            body = json.dumps(v, ensure_ascii=False, indent=1).replace(u"\n", u"\n ")
        parts.append(u" %s: %s" % (json.dumps(k, ensure_ascii=False), body))
    return u"{\n" + u",\n".join(parts) + u"\n}\n"


def merge_gates(results):
    g = collections.OrderedDict()
    for r in results:
        for k, (ok, n) in r["gates"].items():
            x = g.setdefault(k, [0, 0])
            x[0] += ok
            x[1] += n
    return g


def build_rows(results, docs):
    u"""母集団 -> profile -> 書類の順(書類の中は観測した順)。"""
    by = dict(((r["pop"], r["doc"]), r) for r in results)
    out = []
    for pop in POPS:
        for prof in PROFILES[pop]:
            for doc in docs[pop]:
                out.extend(x for x in by[(pop, doc)]["rows"] if x["profile"] == prof)
    return out


def run_all(tasks, procs):
    ctx = multiprocessing.get_context("fork")
    res = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=procs, mp_context=ctx) as ex:
        futs = dict((ex.submit(run_unit, t), t) for t in tasks)
        for f in concurrent.futures.as_completed(futs):
            r = f.result()
            res.append(r)
            print(u"完了 %d / %d 単位 (%s, %d 行, %d 秒)" % (len(res), len(tasks), r["pop"], len(r["rows"]), r["sec"]), file=sys.stderr)
            sys.stderr.flush()
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    ap.add_argument("--docs", type=int, default=None, help="各母集団の先頭 n 書類だけ(試走。全書類を要する門は照らさない)")
    ap.add_argument("--procs", type=int, default=6)
    args = ap.parse_args()
    if os.path.exists(args.out):
        print(u"既に在る(測り直さない): %s" % args.out)
        return
    t_start = time.time()
    full = args.docs is None
    cache0 = {u"edinet": count_zip(FR.EXISTING_CACHE), u"edinet-fresh-2026-10-21": count_zip(FR.FRESH_DIR)}
    prepare(args.docs)
    docs, recs = CTX["docs"], CTX["recs"]
    tasks = [(pop, d) for pop in ("B1", "B2", "A2", "A1") for d in docs[pop]]
    res = run_all(tasks, args.procs)
    rows = build_rows(res, docs)
    gates = merge_gates(res)

    # ---- 行の集合が記録の集合と同じか(件数だけでなく集合で)
    cover = collections.OrderedDict()
    a1keys = set((r["doc"], r["id"]) for r in rows if r[u"母集団"] == "A1")
    a2keys = set((r["doc"], r["id"]) for r in rows if r[u"母集団"] == "A2" and r["profile"] == "P22")
    in_docs = lambda keys, pop: set(k for k in keys if k[0] in docs[pop])
    cover[u"A1 の行 = p20_rerun の rows"] = a1keys == in_docs(CTX["p20_by"].keys(), "A1")
    cover[u"A2 の行 = period_bind の E4 > 行"] = a2keys == in_docs(CTX["e4_by"].keys(), "A2")
    for nm, dd in (("role_swap", CTX["rsw_by"]), ("verify_inventory", CTX["inv_by"]), ("pnf_diag", CTX["pnf_by"])):
        cover[u"W-A1-5 %s の行がこの便の行に全部在る" % nm] = in_docs(dd.keys(), "A1") <= a1keys
    for pop in ("B1", "B2"):
        for prof in PROFILES[pop]:
            mine = set((r["doc"], r["id"]) for r in rows if r[u"母集団"] == pop and r["profile"] == prof)
            want = set((r["doc"], r["id"]) for r in CTX["brec"][(pop, prof)] if r["doc"] in docs[pop])
            cover[u"%s %s の注入 = 記録の rows" % (pop, prof)] = mine == want
    gate = collections.OrderedDict()
    for k, (ok, n) in gates.items():
        gate[k] = {u"一致": ok, u"数": n, u"通った": ok == n and n > 0}
    for k, v in cover.items():
        gate[u"集合 " + k] = {u"一致": int(v), u"数": 1, u"通った": bool(v)}
    gate[u"DEFAULT_PROFILE が P27"] = {u"一致": int(V.DEFAULT_PROFILE == "P27"), u"数": 1, u"通った": V.DEFAULT_PROFILE == "P27"}
    # W-A1-4(全書類のとき)
    vids_by_doc = dict((r["doc"], r["vids"]) for r in res if r["pop"] == "A1")
    rct = rowclaim_totals(vids_by_doc, CTX["mat_by"], docs["A1"])
    rc_rec = recs["rowclaim_map"][u"合計"]
    w_a14 = dict((k, [rc_rec.get(k), rct.get(k, 0)]) for k in RC_KEYS)
    if full:
        gate[u"W-A1-4 rowclaim_map の合計 10 欄"] = {u"一致": sum(1 for k in RC_KEYS if k in rc_rec and rc_rec[k] == rct.get(k, 0)), u"数": len(RC_KEYS),
                                                  u"通った": all(k in rc_rec and rc_rec[k] == rct.get(k, 0) for k in RC_KEYS)}
    # W-S と数え直し・重なり・台帳(全書類のとき)
    items, ovl, ledger = [], [], []
    if full:
        items = all_recounts(rows, recs)
        gate[u"W-S 値で引いた判定のまま数え直すと記録と同じ"] = {u"一致": sum(1 for it in items if it[u"値で数え直しが記録と一致"] in (True, None)), u"数": len(items),
                                                  u"通った": all(it[u"値で数え直しが記録と一致"] in (True, None) for it in items)}
        a2 = [it for it in items if it[u"欄"] == u"全注入で Core 自身(既定)が GROUNDED"][0]
        gate[u"W-A2-3 P27 の注入で GROUNDED の数 = default_p27 の記録"] = {u"一致": int(rt(a2[u"値で数え直し"]) == rt(a2[u"記録"])), u"数": 1, u"通った": rt(a2[u"値で数え直し"]) == rt(a2[u"記録"])}
        ovl = overlaps(rows, recs)
        ledger = ledger_words(recs, items, ovl)
    bad = [k for k, v in gate.items() if not v[u"通った"]]
    if bad:
        raise SystemExit(u"**配線の門が通らない: %s。記録を書かずに止める**" % bad)

    # ---- 付随
    wt = []
    for r in sorted(res, key=lambda r: (POPS.index(r["pop"]), docs[r["pop"]].index(r["doc"]))):
        for prof, c in r["wt"].items():
            wt.append({u"母集団": r["pop"], u"profile": prof, u"doc": r["doc"], u"本文の語ごとの verify の数": c})
    b3 = [x for x in rows if x[u"母集団"] in ("B1", "B2")]
    cache1 = {u"edinet": count_zip(FR.EXISTING_CACHE), u"edinet-fresh-2026-10-21": count_zip(FR.FRESH_DIR)}
    read_sha = dict((rel, sha64(rel)) for rel in sorted(REC.values()))
    with io.open(os.path.join(ROOT, HARNESS_REL), encoding="utf-8") as fh:
        harness_doc = fh.read()
    with io.open(os.path.join(ROOT, FACTS_REL), encoding="utf-8") as fh:
        facts_doc = fh.read()
    ids_part, rows_part = ledger_rows_part(harness_doc, facts_doc)
    live_part = {
        FACTS_REL: {u"読んだ部分": u"§2-7 の対象の行(台帳の file の並びで、行の字を改行でつないだもの)", u"ID の列": ids_part, u"行数": len(ids_part), u"sha256": sha_text(rows_part)},
        HARNESS_REL: {u"読んだ部分": u"読み分けの表の門のブロック %s の中の字" % LEDGER_BLOCK, u"sha256": sha_text(ledger_block_text(harness_doc))},
    }
    live_whole = {FACTS_REL: sha64(FACTS_REL), HARNESS_REL: sha64(HARNESS_REL)}
    for it in items:
        it.pop("_rel", None)
        it.pop("_keypath", None)
    rec = collections.OrderedDict()
    rec[u"注意"] = u"診断の記録(封 docs/XBRL_CD8_ROWCLAIM_REACH_SEAL_2026-10-29.md §2-8)。engine は 0 行。既存の記録は書き換えない。位置で引いた claim が正しいとは言っていない。"
    rec[u"封"] = {u"file": SEAL_REL, u"commit": git("log", "--diff-filter=A", "--format=%h", "--", SEAL_REL), u"期待する commit": SEAL_COMMIT}
    rec[u"全書類"] = full
    rec[u"HEAD"] = git("rev-parse", "HEAD")
    rec[u"DEFAULT_PROFILE"] = V.DEFAULT_PROFILE
    rec[u"engine sha16"] = dict((rel, sha16(rel)) for rel in ENGINE_FILES)
    rec[u"種"] = CTX["seed_meta"]
    rec[u"読んだ記録の sha256"] = read_sha
    rec[u"読んだ生きた文書の部分の sha256"] = live_part
    rec[u"生きた文書の file 全体の sha256(情報。門は照らさない)"] = live_whole
    rec[u"ZIP の sha256"] = dict((pop, dict((r["doc"], r["zip"]) for r in res if r["pop"] == pop)) for pop in POPS)
    rec[u"書類(出てくる順)"] = docs
    rec[u"母集団と profile"] = dict((p, list(v)) for p, v in PROFILES.items())
    rec[u"配線の門"] = gate
    rec[u"W-A1-4 の欄ごと(記録, 数え直し)"] = w_a14
    rec[u"W-T の単位ごと"] = wt
    rec[u"W-B-3 diff_sentence との照合"] = dict((u"%s %s" % (pop, prof), {u"照合した行": sum(1 for x in b3 if x[u"母集団"] == pop and x["profile"] == prof and x.get(u"diff_sentence と同じ") is not None),
                                                                      u"同じ": sum(1 for x in b3 if x[u"母集団"] == pop and x["profile"] == prof and x.get(u"diff_sentence と同じ") is True)})
                                              for pop in ("B1", "B2") for prof in PROFILES[pop])
    rec[u"cache"] = {u"開始": cache0, u"終了": cache1}
    rec[u"数え直し(§2-6 の 1)"] = items
    rec[u"行の重なり(§2-6 の 2)"] = ovl
    rec[u"台帳の行(§2-7)"] = ledger
    rec[u"所要秒"] = round(time.time() - t_start)
    rec[u"limits"] = [
        u"位置で引いた claim が『その行の claim として正しい』とは言えない。行の意味は人が読んでいない。位置の一致は、engine の文の一覧の中で行の token の範囲と claim の数の範囲が重なるという機械の事実だけ。",
        u"4 つの母集団の 24 書類・全 profile の行だけ。他の書類・他の注入で同じ形が出ないとは言えない。",
        u"測らないもの: gen_c の C1 の材料の Core 欄、A1 の P20、A2 の P21・P23〜P26、role_swap・contract_v1・verify_inventory・pnf_diag の B・B′・recipe の差し替えの結果、naming_fix の K-4・C0-3、c1 の K-4・K-5(重なりだけを数えた)。",
        u"台帳・結果文書・外に出した紙の字は直さない。台帳の行の語は印の評価の機械の値で、行の主張の読みではない。",
        u"engine は記録を作った時点から変わっている。配線の門は、いまの engine が記録と同じ claim と判定を出すことを行ごとに見た。",
        u"『位置』は engine の文の一覧の中の位置。engine の本文は渡した本文と空白だけ違い、空白を除いた字の並びで位置を写した。空白以外が違う単位・NFKC で 1 字ずつに写せない文は(位置が決まらない)に落ちる。",
        u"num の claim だけを位置の候補にする。値で引いた claim が text の claim だった行は(違う)か(値だけ)に落ちる。B の T3 は挿入した文の全体が範囲で、文の中の数が 2 つ以上なら(位置で 1 件に決まらない)に落ちる。",
        u"読みは無い(席は呼ばない。人の目も入らない)。観測は全部 engine の出力と記録からの機械の値。",
    ]
    rec[u"rows"] = rows
    blob = dump_record(rec, (u"rows",))
    leaks = FR.key_leaks(blob)
    if leaks:
        raise SystemExit(u"**鍵らしい字が在る: %s。書かずに止める**" % leaks)
    rec[u"key_leaks"] = []
    blob = dump_record(rec, (u"rows",))
    leaks = FR.key_leaks(blob)
    if leaks:
        raise SystemExit(u"**鍵らしい字が在る: %s。書かずに止める**" % leaks)
    with io.open(args.out, "w", encoding="utf-8") as fh:
        fh.write(blob)
    print(u"配線の門 %d 本。行 %d" % (len(gate), len(rows)))
    print(u"cache", cache0, cache1, u"DEFAULT_PROFILE", V.DEFAULT_PROFILE, u"所要秒", rec[u"所要秒"])
    print(u"->", args.out)


if __name__ == "__main__":
    main()
