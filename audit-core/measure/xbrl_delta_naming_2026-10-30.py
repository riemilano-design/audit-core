# -*- coding: utf-8 -*-
u"""診断: 候補の要素の「当期末 − 前期末」が文中の金額と一致するかを、無改変の 296 行で機械で測る便の script ― 2026-10-30。

封 ``docs/XBRL_DELTA_NAMING_DIAG_SEAL_2026-10-30.md``(commit ``68c0a3b``)§2-1〜§2-6 のとおり。
**診断だけ。engine(``core/``・``adapters/``)は 0 行。出力の形(``verify_document.py`` の ``CLAIM_FIELDS``・``report_customer.py``)も 0 行。
既存の記録(``unnamed_fact_2026-10-29.json``・``unnamed_candidate_2026-10-29.json``・``candidate_eyes_2026-10-30.json``・``fresh/fetched_2026-10-21.json``)は書き換えない(別の記録を足す)。**
席(LLM)は立てない。0 USD・通信なし・鍵の値は読まない。評価用・調整用(``~/.cache/audit-core/edinetdb-p27/``)は開かない。
``~/.cache/audit-core/edinet/``(281)は読まず書かない。``edinet-fresh-2026-10-21/``(40)は読むだけ(最初と最後に数える)。

    cd audit-core
    python3 measure/xbrl_delta_naming_2026-10-30.py --procs 4                      # 既に出力が在れば測り直さない
    python3 measure/xbrl_delta_naming_2026-10-30.py --docs 2 --out <scratch の file>  # 試走(先頭 n 書類。配線の門 (ii)(iii)(iv) はその n 書類の分)

**一致しても出所と判定しない。** 記録と文書は、一致の行を「差分候補として機械的に名指せた」と書く(封 §4 の 1。人間の注意: 為替換算・売却・除却・組替え・連結範囲の変更でも期末残高は変わる)。
条件(§2-2〜§2-5 の対・窓・語・帯・段・対照)は、296 行での一致率を見てから調整しない(人間の条件 (7))。変えるなら別の封。
"""
from __future__ import print_function

import argparse
import collections
import hashlib
import importlib.util
import io
import json
import multiprocessing
import os
import re
import subprocess
import sys
import time
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)


def _load(name, mod_name):
    spec = importlib.util.spec_from_file_location(mod_name, os.path.join(HERE, name))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CS = _load("xbrl_unnamed_candidate_2026-10-29.py", "cand_for_delta")      # doc_lists・zip_path・sha16_at・names_sha・jload・sha64(engine のパスもここで通る)
T = _load("xbrl_p27_tune_2026-10-27.py", "tune_for_delta")                # dumps・sha256_hex・read_json・assert_record_clean・record_key_leaks・Stop
from adapters.xbrl import instance as I            # noqa: E402
from adapters.xbrl import extract as E             # noqa: E402
from adapters.xbrl import verify_document as VD    # noqa: E402
from adapters.xbrl import vocabulary as V          # noqa: E402

Stop = T.Stop

SEAL_REL = "docs/XBRL_DELTA_NAMING_DIAG_SEAL_2026-10-30.md"
SEAL_COMMIT = "68c0a3b"
ADDENDUM_COMMIT = "31808fa"                # 封への追記 2(探索と検証の分離。2026-10-30)
OUT_REL = "fixtures/xbrl/delta_naming_2026-10-30.json"
UNNAMED_REL = "fixtures/xbrl/unnamed_fact_2026-10-29.json"
CAND_REL = "fixtures/xbrl/unnamed_candidate_2026-10-29.json"
FETCHED_REL = "fixtures/xbrl/fresh/fetched_2026-10-21.json"
FRESH_REC_REL = "fixtures/xbrl/fresh/fresh_2026-10-21.json"
INPUT_RELS = (UNNAMED_REL, CAND_REL, FETCHED_REL, FRESH_REC_REL)
CAND_KEY = u"候補の行(P27C。reason が no_same_value か候補が辞書の行)"
INJ_KEY = u"注入の書類(出てくる順)"
PROFILE = "P27C"
ENGINE_FILES = ("adapters/xbrl/extract.py", "adapters/xbrl/vocabulary.py", "adapters/xbrl/recipes.py", "adapters/xbrl/resolve.py",
                "adapters/xbrl/comparators.py", "adapters/xbrl/verify_document.py", "adapters/xbrl/report_customer.py")
#: 封の頭の字(人の目の便の封の頭の字と同じ)。違えば別の木なので止める
ENGINE_SHA16 = {"adapters/xbrl/extract.py": "3cf55966f12919f0", "adapters/xbrl/vocabulary.py": "7fbcfbf0e472f366",
                "adapters/xbrl/recipes.py": "52d645e713c53c1c", "adapters/xbrl/resolve.py": "a41043763c1d4073",
                "adapters/xbrl/comparators.py": "d8706338325e725b", "adapters/xbrl/verify_document.py": "6c76c8ade6c7b1c8",
                "adapters/xbrl/report_customer.py": "bdbaa00a419219fe"}

#: 人の目の便の 10 行の位置(封 ``9d847c0`` §2-1。この便は特別扱いせず、旗だけ付ける)
POSITIONS = (0, 30, 60, 90, 120, 150, 180, 210, 240, 270)
NROWS = 296
NDOCS = 30
#: 人間の指示(2026-10-30。封への日付つき追記): 下調べで見た先頭 2 書類の 38 行(並びの位置 0〜37)は探索データ、残りの 258 行(位置 38〜295)は未探索の検証データ。別々に集計する
EXPLORE_MAX_POS = 37
EXPLORE, VERIFY = u"探索", u"検証"
GROUPS = (u"全体", EXPLORE, VERIFY)


def split_of(pos):
    return EXPLORE if pos <= EXPLORE_MAX_POS else VERIFY

# ---------------------------------------------------------------------------------------------------------------
# 封 §2-3 の語(字そのまま。NFKC の字に当てる)と窓
UPDOWN_AFTER_RE = re.compile(u"増加|減少|増収|減収|増益|減益|上回|下回|増|減")
UPDOWN_BEFORE_RE = re.compile(u"増加額|減少額|増加分|減少分|増減額|比べ|比較し")
FLOW_RE = re.compile(u"取得|売却|支出|収入|計上|投資|返済|借入|調達|償還|配当|支払|受取|償却|引当|除却|出資|貸付|回収")
SEGMENT_WORD_RE = re.compile(u"セグメント|事業別|所在地別|地域別|部門|区分別")
#: 封 §2-6 の 10(D-7): engine の ``is_diff`` の後の条件に当たる語(後の窓の最初の 4 字)
ENGINE_AFTER4_RE = re.compile(u"増加|減少|増|減")
TYPE_ORDER = (u"増減の型", u"流量の型", u"区分の型", u"その他")
UP_WORDS = (u"増加", u"増収", u"増益", u"上回", u"増")
DOWN_WORDS = (u"減少", u"減収", u"減益", u"下回", u"減")
UP_NOUNS = (u"増加額", u"増加分")
DOWN_NOUNS = (u"減少額", u"減少分")
AFTER_WINDOW = 10                        # 後の窓 = span の末尾 10 字
NONCONS = "NonConsolidatedMember"
D_UP, D_DOWN, D_UNKNOWN, D_NONE = u"増", u"減", u"不明", u"なし"
DIRECTIONS = (D_UP, D_DOWN, D_UNKNOWN, D_NONE)

# ---------------------------------------------------------------------------------------------------------------
# 封 §2-4 の帯と段
#: 帯 w = 文の単位の 1 単位(``UNIT_SCALE[unit]`` の ``TOL_UNITS`` 倍)。完全一致は差 0
TOL_UNITS = 1
S_EXACT, S_TOL, S_SIGN, S_MISMATCH, S_NA = u"完全一致", u"許容差内", u"符号不一致", u"不一致", u"比較不能"
STAGES = (S_EXACT, S_TOL, S_SIGN, S_MISMATCH, S_NA)
MAGS = (S_EXACT, S_TOL, S_MISMATCH)
R_CUR_MULTI, R_NO_P, R_DIM, R_NO_PF = u"当期の値が一意でない", u"前期の枠なし", u"前期の枠の次元が違う", u"前期の fact なし"
R_PRI_MULTI, R_UNIT, R_NONINT = u"前期の値が一意でない", u"単位が違う", u"整数でない"
REASONS = (R_CUR_MULTI, R_NO_P, R_DIM, R_NO_PF, R_PRI_MULTI, R_UNIT, R_NONINT)
# 封 §2-5 の対照の 5 段と前期残高の段
C_ONLY, C_ALSO, C_OTHER, C_NONE, C_NA = u"候補だけが一致", u"候補以外にも在る", u"候補は一致せず別の要素が一致", u"どれも一致しない", u"候補が比較不能"
CONTROLS = (C_ONLY, C_ALSO, C_OTHER, C_NONE, C_NA)
P_EXACT, P_TOL, P_MISMATCH, P_NA = u"前期残高と完全一致", u"前期残高と許容差内", u"不一致", u"比較不能"
PRIORS = (P_EXACT, P_TOL, P_MISMATCH, P_NA)
STD_PREFIXES = ("jppfs_cor", "jpcrp_cor", "jpigp_cor", "jpdei_cor")


# ======================================================================================================
# 小さい道具
def sha256_hex(b):
    return hashlib.sha256(b).hexdigest()


def git_out(*a):
    r = subprocess.run(["git"] + list(a), cwd=ROOT, capture_output=True, text=True)
    return (r.returncode, r.stdout.strip())


def cache_names():
    return {u"edinet": CS.names_sha(CS.EXISTING_CACHE), u"edinet-fresh-2026-10-21": CS.names_sha(CS.FRESH_DIR)}


def check_engine():
    u"""木の engine が封の頭の sha16 と同じで、未 commit の変更が無いことを確かめる(封 §2-6 の (v))。"""
    now = dict((f, CS.sha16_at(ROOT, f)) for f in ENGINE_FILES)
    if now != ENGINE_SHA16:
        raise Stop(u"**engine の sha16 が封の頭の字と違う: %s。止める**" % T.dumps(now))
    rc, out = git_out("status", "--porcelain", "--", "adapters", "core")
    if rc != 0 or out:
        raise Stop(u"**engine に未 commit の変更が在るか git が読めない。止める**")
    return now


def split_pointer(named):
    u"""封 §2-2: ``xbrl:`` の後ろを最初の ``@`` で切り、要素名 N と枠 C を得る。"""
    body = named[len("xbrl:"):] if named.startswith("xbrl:") else named
    name, ctx = body.split("@", 1)
    return name, ctx


def tol_of_unit(unit):
    u"""封 §2-4: 帯 w = 文の単位の 1 単位(円 1・千円 1,000・百万円 1,000,000)。"""
    return int(V.UNIT_SCALE[unit] * TOL_UNITS)


# ======================================================================================================
# §2-3 窓と型
def windows(span):
    u"""``(前の窓, 後の窓)``。後の窓 = span の末尾 10 字(10 字に満たなければ全部)、前の窓 = それを除いた字。"""
    if not span:
        return u"", u""
    after = span[-AFTER_WINDOW:]
    before = span[:-AFTER_WINDOW] if len(span) > AFTER_WINDOW else u""
    return before, after


def direction_of(before, after):
    u"""封 §2-3 の向きの語: ``(向き, 後の窓に増と減の両方が在る)``。"""
    both = bool(any(w in after for w in UP_WORDS)) and bool(any(w in after for w in DOWN_WORDS))
    m = UPDOWN_AFTER_RE.search(after)
    if m:
        return (D_UP if m.group(0) in UP_WORDS else D_DOWN), both
    mb = UPDOWN_BEFORE_RE.search(before)
    if mb:
        if mb.group(0) in UP_NOUNS:
            return D_UP, both
        if mb.group(0) in DOWN_NOUNS:
            return D_DOWN, both
        return D_UNKNOWN, both
    return D_NONE, both


def type_of(f_updown, f_flow, f_seg):
    u"""封 §2-3: 型は 増減 → 流量 → 区分 → その他 の順で最初に当たった 1 つ。"""
    if f_updown:
        return TYPE_ORDER[0]
    if f_flow:
        return TYPE_ORDER[1]
    if f_seg:
        return TYPE_ORDER[2]
    return TYPE_ORDER[3]


def member_kind(members):
    u"""``(なし | 単体 | それ以外)``。単体 = ``NonConsolidatedMember`` だけ。"""
    if not members:
        return u"なし"
    if [m.split(":")[-1] for m in members] == [NONCONS]:
        return u"単体"
    return u"それ以外"


# ======================================================================================================
# §2-4 段(1 か所)
def sign_of(d):
    return None if d is None else (u"正" if d > 0 else (u"負" if d < 0 else u"0"))


def magnitude_of(d, t, w):
    u"""大きさの段: ``e = | |d| − t |``。e == 0 なら完全一致、0 < e <= w なら許容差内、e > w なら不一致。"""
    e = abs(abs(d) - t)
    if e == 0:
        return S_EXACT
    if e <= w:
        return S_TOL
    return S_MISMATCH


def stage_of(d, t, w, direction):
    u"""封 §2-4 の段(この順で 1 つ)。``d`` が None なら比較不能。大きさが一致の側で、向きが 増・減 に決まり、符号が期待と逆(d が 0 でない)なら符号不一致。"""
    if d is None:
        return S_NA
    mag = magnitude_of(d, t, w)
    if mag == S_MISMATCH:
        return S_MISMATCH
    if d != 0 and ((direction == D_UP and d < 0) or (direction == D_DOWN and d > 0)):
        return S_SIGN
    return mag


# ======================================================================================================
# §2-5 対照・前期残高との一致
def prior_stage_of(prior_value, t, w):
    u"""前期残高との一致: ``e' = | |前期の値| − t |``。前期の値が None なら比較不能。"""
    if prior_value is None:
        return P_NA
    e = abs(abs(prior_value) - t)
    if e == 0:
        return P_EXACT
    if e <= w:
        return P_TOL
    return P_MISMATCH


def control_of(index, candidate_name, c_ctx, p_ctx, unit0, t, w):
    u"""対照: 候補の枠 C と対の枠 P の両方に fact を持つ候補以外の全要素 M(unit が候補と同じ、当期・前期の値の集合がそれぞれ 1 つ)の
    ``d_M = 当期 − 前期`` のうち ``| |d_M| − t | <= w`` の数 m と分母。``(m, 分母)``。符号は問わない。"""
    cur = index.get(c_ctx, {})
    pri = index.get(p_ctx, {})
    m = denom = 0
    for (name, unit), cvals in cur.items():
        if name == candidate_name or unit != unit0:
            continue
        pvals = pri.get((name, unit))
        if not pvals or len(cvals) != 1 or len(pvals) != 1:
            continue
        denom += 1
        dm = list(cvals)[0] - list(pvals)[0]
        if abs(abs(dm) - t) <= w:
            m += 1
    return m, denom


def control_stage_of(comparable, stage, m):
    u"""封 §2-5 の 5 段。``comparable`` = 候補の段が比較不能でない。候補の段が 完全一致 / 許容差内 のとき『候補が一致』。"""
    if not comparable:
        return C_NA
    if stage in (S_EXACT, S_TOL):
        return C_ONLY if m == 0 else C_ALSO
    return C_OTHER if m >= 1 else C_NONE


def coarse_of(decimals, w):
    u"""封 §2-6 の 9: 10 の −decimals 乗 > w なら、文の単位より粗い。decimals が数でない(INF・None)ときは粗いと数えない。"""
    try:
        return 10.0 ** (-int(decimals)) > w
    except (TypeError, ValueError):
        return False


# ======================================================================================================
# 書類 1 本(別の process)
def doc_job(args):
    u"""1 書類の行。ZIP の sha256・engine の出力(P27C)・文・窓を読み、封 §2 の欄を行ごとに作る。span・文・ラベルの字は返さない。"""
    doc, rows, expect_sha_fetched, expect_sha_rec, pos_of_row = args
    t0 = time.time()
    with io.open(CS.zip_path(doc, True), "rb") as fh:
        zb = fh.read()
    zsha = sha256_hex(zb)
    zip_ok = (zsha == expect_sha_fetched) and (zsha == expect_sha_rec)
    inst = I.load_instance(zb)
    facts, contexts, tbs = inst["facts"], inst["contexts"], inst["textblocks"]
    out = VD.verify_document(zb, PROFILE, None)
    claims = out["claims"]
    prof = V.PROFILES[PROFILE]
    mname = I.select_mdna(tbs)
    text = I.strip_html(tbs[mname]) if mname else u""
    sentences = E.split_sentences(text, prof.paren_sentence)
    z = zipfile.ZipFile(io.BytesIO(zb))
    labels = I.labels_from_zip(z, z.namelist())
    seg_labels = []
    for mm in I.segment_member_denominator(contexts):
        lab = labels.get(mm.replace(":", "_")) or labels.get(mm.split(":")[-1])
        if lab:
            seg_labels.append(lab)
    # (context) -> {(name, unit): {値}} と (name, context) -> [fact]
    index = {}
    by_nc = {}
    for f in facts:
        index.setdefault(f["context"], {}).setdefault((f["name"], f["unit"]), set()).add(f["value"])
        by_nc.setdefault((f["name"], f["context"]), []).append(f)
    out_rows = []
    for r in rows:
        cid = r["id"]
        named = r["named"]
        t = r[u"文の値"]
        unit = r["unit"]
        w = tol_of_unit(unit)
        N, C = split_pointer(named)
        cl = [c for c in claims if c["id"] == cid]
        claim = cl[0] if len(cl) == 1 else None
        cand = (claim.get("candidate") if claim else None) or {}
        cur_f = by_nc.get((N, C), [])
        cur_vals = sorted(set(f["value"] for f in cur_f))
        scale = V.UNIT_SCALE.get(claim.get("unit")) if claim else None
        wiring = {
            u"(iii) 当期の値の集合に named の value": r[u"named の value"] in cur_vals,
            u"(iv) claim がちょうど 1 つ": claim is not None,
            u"(iv) 候補の pointer・value が記録と同じ": bool(claim) and cand.get("pointer") == named and cand.get("value") == r[u"named の value"],
            u"(iv) 文の値と unit が記録と同じ": bool(claim) and claim.get("unit") == unit and scale is not None and claim["value"] * scale == t,
        }
        span = claim.get("span") if claim else None
        sent = next((s for s in sentences if span and span in s), None)
        before_w, after_w = windows(span)
        f_updown = bool(UPDOWN_AFTER_RE.search(after_w) or UPDOWN_BEFORE_RE.search(before_w))
        f_flow = bool(FLOW_RE.search(before_w) or FLOW_RE.search(after_w))
        cmem = (contexts.get(C) or {}).get("members") or []
        mkind = member_kind(cmem)
        seg_word = bool(sent and SEGMENT_WORD_RE.search(sent))
        seg_label = bool(sent and any(lab in sent for lab in seg_labels))
        f_seg = (mkind in (u"なし", u"単体")) and (seg_word or seg_label)
        typ = type_of(f_updown, f_flow, f_seg)
        direction, both = direction_of(before_w, after_w)
        # §2-2 前期の対
        P = C.replace("CurrentYear", "Prior1Year", 1)
        pri_f = by_nc.get((N, P), [])
        pri_vals = sorted(set(f["value"] for f in pri_f))
        same_dim = (P in contexts) and (contexts[P].get("members") or []) == (contexts[C].get("members") or []) \
            and (contexts[P].get("axes") or []) == (contexts[C].get("axes") or [])
        cur_unit = cur_f[0]["unit"] if cur_f else None
        pri_unit = pri_f[0]["unit"] if pri_f else None
        reason = None
        if len(cur_vals) != 1:
            reason = R_CUR_MULTI
        elif P not in contexts:
            reason = R_NO_P
        elif not same_dim:
            reason = R_DIM
        elif not pri_f:
            reason = R_NO_PF
        elif len(pri_vals) != 1:
            reason = R_PRI_MULTI
        elif pri_unit != cur_unit:
            reason = R_UNIT
        elif not float(cur_vals[0]).is_integer() or not float(pri_vals[0]).is_integer():
            reason = R_NONINT
        cur_v = cur_vals[0] if len(cur_vals) == 1 else None
        # 前期の値は、前期の fact が一意で、対の枠の次元が同じで、単位が同じとき持つ(前期残高との一致は差の段と独立に記録する)
        prior_usable = same_dim and len(pri_f) > 0 and len(pri_vals) == 1 and pri_unit == cur_unit
        pri_v = pri_vals[0] if prior_usable else None
        d = (cur_v - pri_v) if reason is None else None
        stage = stage_of(d, t, w, direction)
        mag = magnitude_of(d, t, w) if d is not None else None
        prior_stage = prior_stage_of(pri_v, t, w)
        # §2-5 対照(P が instance の枠に在る限り作る)
        m_cnt = denom = None
        if P in contexts and cur_f:
            m_cnt, denom = control_of(index, N, C, P, cur_unit, t, w)
        cstage = control_stage_of(reason is None, stage, m_cnt)
        cur_dec = cur_f[0].get("decimals") if cur_f else None
        pri_dec = pri_f[0].get("decimals") if pri_f else None
        out_rows.append({
            u"位置": pos_of_row[cid], u"書類の位置": None, "doc": doc, "id": cid, u"pointers": [named], u"named の value": r[u"named の value"],
            u"期": u"Instant" if C.startswith("CurrentYearInstant") else u"Duration", "member": mkind, u"単位": unit, u"帯の幅": w, u"文の値": t,
            u"当期の値": cur_v, u"前期の値": pri_v, u"差": d, u"差の符号": sign_of(d), u"当期の decimals": cur_dec, u"前期の decimals": pri_dec,
            u"当期の unit": cur_unit, u"前期の unit": pri_unit, u"前期の fact 在り": bool(pri_f), u"比較不能の理由": reason,
            u"大きさの段": mag, u"段": stage, u"型": typ, u"旗": {u"増減": f_updown, u"流量": f_flow, u"区分": f_seg},
            u"区分の語に当たった": seg_word, u"区分のラベルに当たった": seg_label, u"向き": direction, u"両方在る": both,
            u"後の窓の先頭 4 字に engine の語": bool(ENGINE_AFTER4_RE.search(after_w[:4])),
            u"窓なし": sent is None, u"文の全体に増減の語": bool(sent and UPDOWN_AFTER_RE.search(sent)),
            u"対照 m": m_cnt, u"対照の分母": denom, u"対照の段": cstage, u"前期残高の段": prior_stage,
            u"decimals が文の単位より粗い": coarse_of(cur_dec, w) or coarse_of(pri_dec, w),
            u"10 行": pos_of_row[cid] in POSITIONS, u"探索/検証": split_of(pos_of_row[cid]), u"配線": wiring,
        })
    return {u"doc": doc, u"zip の sha256": zsha, u"zip の sha256 が取得の記録と材料の記録の両方と一致": zip_ok, u"rows": out_rows, u"claims": len(claims),
            u"事業の member": len(I.segment_member_denominator(contexts)), u"ラベルが引けた member": len(seg_labels),
            u"文の数": len(sentences), u"秒": round(time.time() - t0, 1)}


def run_pool(jobs, procs):
    if procs <= 1:
        return [doc_job(j) for j in jobs]
    ctx = multiprocessing.get_context("fork")
    with ctx.Pool(procs) as pool:
        return list(pool.imap(doc_job, jobs, chunksize=1))


# ======================================================================================================
# 集計(封 §2-6 の表の元。記録の ``集計``。門が行から別実装で作り直して一致させる)
def _cnt(it):
    return collections.OrderedDict(sorted(collections.Counter(it).items(), key=lambda kv: str(kv[0])))


def _full(keys, it):
    c = collections.Counter(it)
    return collections.OrderedDict((k, c.get(k, 0)) for k in keys)


def _median(xs):
    xs = sorted(xs)
    n = len(xs)
    if not n:
        return None
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2.0


def element_of(r):
    u"""標準の名前空間の要素名(``接頭辞:要素名``)。提出者別は字を書かない。"""
    name = split_pointer(r["pointers"][0])[0]
    return name if name.split(":", 1)[0] in STD_PREFIXES else u"(提出者別の要素)"


def member_flag(r):
    return u"なし" if r["member"] == u"なし" else u"あり"


def tally(rows):
    ms = [r for r in rows if r[u"段"] in (S_EXACT, S_TOL)]
    ctl = [r for r in rows if r[u"対照 m"] is not None]
    denoms = [r[u"対照の分母"] for r in ctl]
    ud = [r for r in rows if r[u"向き"] in (D_UP, D_DOWN)]
    other = [r for r in rows if r[u"向き"] not in (D_UP, D_DOWN)]
    coarse = [r for r in rows if r[u"decimals が文の単位より粗い"]]
    ew = [r for r in rows if r[u"型"] == TYPE_ORDER[0]]
    out = collections.OrderedDict()
    out[u"types"] = collections.OrderedDict([
        (u"型の行数", _full(TYPE_ORDER, (r[u"型"] for r in rows))),
        (u"旗の組", _cnt(u"増減%d 流量%d 区分%d" % (r[u"旗"][u"増減"], r[u"旗"][u"流量"], r[u"旗"][u"区分"]) for r in rows)),
        (u"向き", _full(DIRECTIONS, (r[u"向き"] for r in rows))),
        (u"両方在る", sum(1 for r in rows if r[u"両方在る"])),
        (u"窓の外の旗", collections.OrderedDict([(u"窓なし(span が文の中に見つからない)", sum(1 for r in rows if r[u"窓なし"])),
                                              (u"文の全体に増減の語が在る", sum(1 for r in rows if r[u"文の全体に増減の語"])),
                                              (u"窓の中に増減の語が在る(増減の型)", sum(1 for r in rows if r[u"旗"][u"増減"])),
                                              (u"文の全体に在るが窓の中に無い", sum(1 for r in rows if r[u"文の全体に増減の語"] and not r[u"旗"][u"増減"]))])),
        (u"型×期×member", _cnt(u"%s / %s / member %s" % (r[u"型"], r[u"期"], member_flag(r)) for r in rows)),
    ])
    out[u"stages"] = collections.OrderedDict([
        (u"段", _full(STAGES, (r[u"段"] for r in rows))),
        (u"比較不能の理由", _full(REASONS, (r[u"比較不能の理由"] for r in rows if r[u"比較不能の理由"]))),
        (u"型×段", _cnt(u"%s / %s" % (r[u"型"], r[u"段"]) for r in rows)),
        (u"期×段", _cnt(u"%s / %s" % (r[u"期"], r[u"段"]) for r in rows)),
        (u"単位×段", _cnt(u"%s / %s" % (r[u"単位"], r[u"段"]) for r in rows)),
        (u"member×段", _cnt(u"member %s / %s" % (member_flag(r), r[u"段"]) for r in rows)),
    ])
    out[u"sign"] = collections.OrderedDict([
        (u"向きが増・減の行の向きと差の符号", _cnt(u"%s / %s" % (r[u"向き"], r[u"差の符号"] or u"比較不能") for r in ud)),
        (u"向きが不明・なしの行の差の符号", _full((u"正", u"負", u"0", u"比較不能"), (r[u"差の符号"] or u"比較不能" for r in other))),
        (u"符号不一致", sum(1 for r in rows if r[u"段"] == S_SIGN)),
    ])
    out[u"control"] = collections.OrderedDict([
        (u"対照の段", _full(CONTROLS, (r[u"対照の段"] for r in rows))),
        (u"型×対照の段", _cnt(u"%s / %s" % (r[u"型"], r[u"対照の段"]) for r in rows)),
        (u"対照の分母", collections.OrderedDict([(u"最小", min(denoms) if denoms else None), (u"最大", max(denoms) if denoms else None), (u"中央値", _median(denoms))])),
        (u"m の分布", _full((u"0", u"1", u"2〜5", u"6 以上", u"(対照なし)"),
                         (u"(対照なし)" if r[u"対照 m"] is None else (u"0" if r[u"対照 m"] == 0 else (u"1" if r[u"対照 m"] == 1 else (u"2〜5" if r[u"対照 m"] <= 5 else u"6 以上"))) for r in rows))),
        (u"m が 6 以上の行", sum(1 for r in ctl if r[u"対照 m"] >= 6)),
        (u"m が 1 以上で単位が円の行", sum(1 for r in ctl if r[u"対照 m"] >= 1 and r[u"単位"] == u"円")),
    ])
    out[u"prior"] = collections.OrderedDict([
        (u"前期残高の段", _full(PRIORS, (r[u"前期残高の段"] for r in rows))),
        (u"差の段×前期残高の段", _cnt(u"%s / %s" % (r[u"段"], r[u"前期残高の段"]) for r in rows)),
        (u"両方に一致", sum(1 for r in ms if r[u"前期残高の段"] in (P_EXACT, P_TOL))),
    ])
    out[u"ten"] = [[r[u"位置"], r[u"型"], r[u"段"], r[u"対照の段"], r[u"前期残高の段"]] for r in rows if r[u"10 行"]]
    out[u"decimals"] = collections.OrderedDict([
        (u"組", _cnt(u"%s / %s" % (r[u"当期の decimals"], r[u"前期の decimals"]) for r in rows)),
        (u"文の単位より粗い行", len(coarse)),
        (u"文の単位より粗い行の段", _cnt(r[u"段"] for r in coarse)),
    ])
    out[u"engine_window"] = collections.OrderedDict([
        (u"増減の型の行", _cnt(u"後の窓の先頭 4 字に engine の語 %s / %s / 前期の fact %s" % (u"あり" if r[u"後の窓の先頭 4 字に engine の語"] else u"なし", r[u"期"],
                                                                                  u"あり" if r[u"前期の fact 在り"] else u"なし") for r in ew)),
        (u"D-7 の行(Instant・増減の型・後の窓の先頭 4 字に engine の語・前期の fact あり)",
         sum(1 for r in ew if r[u"期"] == u"Instant" and r[u"後の窓の先頭 4 字に engine の語"] and r[u"前期の fact 在り"])),
    ])
    out[u"elements"] = [collections.OrderedDict([(u"位置", r[u"位置"]), (u"pointers", [element_of(r)]), (u"期", r[u"期"]), (u"member", member_flag(r)), (u"単位", r[u"単位"]), (u"段", r[u"段"])])
                        for r in ms]
    return out


#: 封の追記 2 の 5: 探索 38 行の数は封 §6 で見た数と一致しなければ配線の門として赤(止める)
EXPLORE_PIN = collections.OrderedDict([
    (u"型", {u"増減の型": 10, u"流量の型": 13, u"区分の型": 0, u"その他": 15}),
    (u"段", {u"完全一致": 0, u"許容差内": 4, u"符号不一致": 1, u"不一致": 33, u"比較不能": 0}),
    (u"対照の段", {u"候補だけが一致": 4, u"候補以外にも在る": 0, u"候補は一致せず別の要素が一致": 1, u"どれも一致しない": 33, u"候補が比較不能": 0}),
    (u"前期残高の段", {u"前期残高と完全一致": 0, u"前期残高と許容差内": 0, u"不一致": 38, u"比較不能": 0})])


def explore_pin_ok(rows):
    u"""探索 38 行(位置 0〜37)の型・段・対照の段・前期残高の段が EXPLORE_PIN と同じか。"""
    ex = [r for r in rows if r[u"探索/検証"] == EXPLORE]
    got = {u"型": dict(_full(TYPE_ORDER, (r[u"型"] for r in ex))), u"段": dict(_full(STAGES, (r[u"段"] for r in ex))),
           u"対照の段": dict(_full(CONTROLS, (r[u"対照の段"] for r in ex))), u"前期残高の段": dict(_full(PRIORS, (r[u"前期残高の段"] for r in ex)))}
    return len(ex) == 38 and got == dict(EXPLORE_PIN)


# ======================================================================================================
def build_gate(rows_all, results, cand_map):
    u"""封 §2-6 の配線の門 (i)〜(iv)(v)(vi) は main で足す。1 つでも外れたら止める判断は main。"""
    n_i = sum(1 for r in rows_all if cand_map.get((r["doc"], r["id"]), {}).get("pointer") == r["named"]
              and cand_map.get((r["doc"], r["id"]), {}).get("value") == r[u"named の value"])
    n_ii = sum(1 for x in results if x[u"zip の sha256 が取得の記録と材料の記録の両方と一致"])
    rr = [row for x in results for row in x["rows"]]
    keys = (u"(iii) 当期の値の集合に named の value", u"(iv) claim がちょうど 1 つ", u"(iv) 候補の pointer・value が記録と同じ", u"(iv) 文の値と unit が記録と同じ")
    n_iii = sum(1 for row in rr if row[u"配線"][keys[0]])
    n_iv = sum(1 for row in rr if all(row[u"配線"][k] for k in keys[1:]))
    return {u"(i) 296 行の (doc, id, named, named の value) が記録と候補の記録の両方と一致": [n_i, len(rows_all)],
            u"(ii) ZIP の sha256 が取得の記録と材料の記録の両方と一致": [n_ii, len(results)],
            u"(iii) instance の named の値の集合に named の value": [n_iii, len(rr)],
            u"(iv) claim 1 つ・候補一致・文の値と unit 一致": [n_iv, len(rr)]}


def dump_record(rec, rowkeys):
    u"""行は 1 行 1 件の compact JSON(296 行を indent で広げない)。それ以外は indent=1。妥当な JSON。"""
    parts = []
    for k, v in rec.items():
        if k in rowkeys:
            body = u"[\n" + u",\n".join(u"  " + json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in v) + u"\n ]"
        else:
            body = json.dumps(v, ensure_ascii=False, indent=1).replace(u"\n", u"\n ")
        parts.append(u" %s: %s" % (json.dumps(k, ensure_ascii=False), body))
    return u"{\n" + u",\n".join(parts) + u"\n}\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    ap.add_argument("--docs", type=int, default=None, help="先頭 n 書類だけ(試走。正本の記録は 30 書類全部)")
    ap.add_argument("--procs", type=int, default=1)
    args = ap.parse_args()
    if args.procs < 1 or args.procs > 4:
        raise Stop(u"**--procs は 1〜4。止める**")
    if os.path.exists(args.out):
        print(u"出力が既に在る(測り直さない): %s" % args.out)
        return
    t_start = time.time()
    before = cache_names()
    engine = check_engine()
    unnamed = CS.jload(UNNAMED_REL)
    cand = CS.jload(CAND_REL)
    _p67, _s67, ids30, sha30 = CS.doc_lists()
    order = unnamed[u"書類(出てくる順)"]
    if order != ids30 or order != cand[INJ_KEY]:
        raise Stop(u"**書類の並びが取得の記録・候補の記録と違う。止める**")
    pos = dict((d, i) for i, d in enumerate(order))
    rows_all = sorted(unnamed["plain_rows"], key=lambda r: (pos[r["doc"]], r["id"]))
    if len(rows_all) != NROWS or len(set((r["doc"], r["id"]) for r in rows_all)) != NROWS:
        raise Stop(u"**plain_rows が 296 行でないか (doc, id) が重複している。止める**")
    inj = set(cand[INJ_KEY])
    cand_map = dict(((r["doc"], r["id"]), r["candidate"]) for r in cand[CAND_KEY] if r["doc"] in inj)
    if set(cand_map) != set((r["doc"], r["id"]) for r in rows_all):
        raise Stop(u"**候補の記録の 30 書類の行が plain_rows と同じ集合でない。止める**")
    rec_docs = unnamed[u"書類ごと"]
    position = dict(((r["doc"], r["id"]), i) for i, r in enumerate(rows_all))
    docs = order if args.docs is None else order[:args.docs]
    jobs = []
    for d in docs:
        rows = [r for r in rows_all if r["doc"] == d]
        jobs.append((d, rows, sha30[d], rec_docs[d][u"材料の sha256"], dict((r["id"], position[(d, r["id"])]) for r in rows)))
    results = run_pool(jobs, args.procs)
    for x in results:
        for row in x["rows"]:
            row[u"書類の位置"] = pos[x["doc"]]
    rows_run = [row for x in results for row in x["rows"]]
    rows_run.sort(key=lambda r: r[u"位置"])
    gate = build_gate(rows_all, results, cand_map)
    after = cache_names()
    gate[u"(v) engine の sha16 7 本が封の頭の字と一致・adapters と core に未 commit の変更なし"] = True
    gate[u"(vi) cache の件数と名前の一覧の sha256 が開始時と終了時で同じ"] = before == after
    gate[u"窓なしの行数(止めない)"] = sum(1 for r in rows_run if r[u"窓なし"])
    gate[u"当期の値が一意でない行数(止めない)"] = sum(1 for r in rows_run if r[u"比較不能の理由"] == R_CUR_MULTI)
    ok = (gate[u"(i) 296 行の (doc, id, named, named の value) が記録と候補の記録の両方と一致"][0] == NROWS
          and gate[u"(ii) ZIP の sha256 が取得の記録と材料の記録の両方と一致"][0] == len(docs)
          and gate[u"(iii) instance の named の値の集合に named の value"][0] == len(rows_run)
          and gate[u"(iv) claim 1 つ・候補一致・文の値と unit 一致"][0] == len(rows_run)
          and gate[u"(vi) cache の件数と名前の一覧の sha256 が開始時と終了時で同じ"]
          and after[u"edinet"][u"件数"] == 281 and after[u"edinet-fresh-2026-10-21"][u"件数"] == 40)
    if args.docs is None or args.docs >= 2:
        gate[u"探索 38 行の数が封 §6 の数と一致(追記 2 の 5)"] = explore_pin_ok(rows_run)
        ok = ok and gate[u"探索 38 行の数が封 §6 の数と一致(追記 2 の 5)"]
    gate[u"通った"] = bool(ok)
    if not ok:
        raise Stop(u"**配線の門が通らない: %s。記録を書かずに止める**" % T.dumps(gate))
    if args.docs is None and len(rows_run) != NROWS:
        raise Stop(u"**行が 296 でない。止める**")
    _rc, head = git_out("rev-parse", "HEAD")
    if git_out("merge-base", "--is-ancestor", SEAL_COMMIT, "HEAD")[0] != 0 or git_out("merge-base", "--is-ancestor", ADDENDUM_COMMIT, "HEAD")[0] != 0:
        raise Stop(u"**封の commit か追記 2 の commit が HEAD の祖先でない。止める**")
    rec = collections.OrderedDict()
    rec[u"注意"] = (u"診断の記録(封 %s)。一致の行は『差分候補として機械的に名指せた』までで、出所として正しいとは言わない"
                  u"(為替換算・売却・除却・組替え・連結範囲の変更でも期末残高は変わる)。engine は 0 行。既存の記録は書き換えない。"
                  u"記録に span・文・段落・窓の字・ラベルの字・理由の自由文は入れない。" % SEAL_REL)
    rec[u"封"] = {u"file": SEAL_REL, u"commit": SEAL_COMMIT, u"追記 2 の commit": ADDENDUM_COMMIT}
    rec[u"全書類"] = args.docs is None
    rec[u"HEAD の commit"] = head
    rec[u"DEFAULT_PROFILE"] = V.DEFAULT_PROFILE
    rec[u"測る profile"] = PROFILE
    rec[u"engine sha16"] = engine
    rec[u"engine の指紋"] = VD.engine_fingerprint()
    with io.open(os.path.abspath(__file__), "rb") as fh:
        rec[u"この script の sha256"] = sha256_hex(fh.read())
    rec[u"読んだ入力の sha256"] = dict((rel, CS.sha64(rel)) for rel in INPUT_RELS)
    rec[u"定数"] = collections.OrderedDict([
        (u"UPDOWN_AFTER_RE", UPDOWN_AFTER_RE.pattern), (u"UPDOWN_BEFORE_RE", UPDOWN_BEFORE_RE.pattern), (u"FLOW_RE", FLOW_RE.pattern),
        (u"SEGMENT_WORD_RE", SEGMENT_WORD_RE.pattern), (u"ENGINE_AFTER4_RE", ENGINE_AFTER4_RE.pattern), (u"TYPE_ORDER", list(TYPE_ORDER)),
        (u"後の窓の字数", AFTER_WINDOW), (u"帯の単位数 TOL_UNITS", TOL_UNITS), (u"UNIT_SCALE", dict((k, int(v)) for k, v in sorted(V.UNIT_SCALE.items()))),
        (u"人の目の便の 10 行の位置", list(POSITIONS)), (u"探索の最後の位置 EXPLORE_MAX_POS", EXPLORE_MAX_POS)])
    rec[u"書類の並び"] = docs
    rec[u"書類ごと"] = collections.OrderedDict((x["doc"], collections.OrderedDict([
        (u"zip の sha256", x[u"zip の sha256"]), (u"行", len(x["rows"])), (u"claim", x["claims"]), (u"文の数", x[u"文の数"]),
        (u"事業の member", x[u"事業の member"]), (u"ラベルが引けた member", x[u"ラベルが引けた member"]), (u"秒", x[u"秒"])])) for x in results)
    rec[u"配線の門"] = gate
    rec[u"cache"] = {u"開始": before, u"終了": after, u"変化なし": before == after}
    rec[u"所要秒"] = round(time.time() - t_start)
    rec[u"limits"] = [
        u"一致は出所の判定ではない。差額と一致したことは、その差額が文章の主張の正しい出所であることを証明しない(為替換算・売却・除却・組替え・連結範囲の変更でも期末残高は変わる)。",
        u"engine の recipes.py は is_diff の行で同じ要素の a−b を既に試して外している。この便の一致は帯(半単位 → 文の単位の 1 単位)・窓(4 字 → span の後 10 字)・対(家族の最初の枠 → 候補の枠)の違いの分。",
        u"対照は同じ書類の中だけ。別の書類・前期 − 前々期・2 つの要素の和や差は作らない。",
        u"型分けは語の一覧で、窓は engine の span(前 30 字・後 10 字)に固定した。文の後ろの方の向きの語は拾わない(文の全体に増減の語が在る行は旗で数えた)。区分の型は書類自身のラベルの字の完全一致。",
        u"候補の枠の対だけ。セグメントの枠に結び直す試みはしない。",
        u"帯は文の単位の 1 単位で、fact の decimals の粗さを見ない(decimals は欄で数えるだけ)。",
        u"296 行での一致率を見てから条件を調整しない(人間の条件 (7))。条件を変えるなら別の封。",
    ]
    rec[u"行"] = rows_run
    rec[u"集計"] = collections.OrderedDict([(u"全体", tally(rows_run)), (EXPLORE, tally([r for r in rows_run if r[u"探索/検証"] == EXPLORE])),
                                          (VERIFY, tally([r for r in rows_run if r[u"探索/検証"] == VERIFY]))])
    rec[u"key_leaks"] = []
    T.assert_record_clean(rec)
    blob = dump_record(rec, (u"行",))
    json.loads(blob)
    d = os.path.dirname(args.out)
    if d:
        os.makedirs(d, exist_ok=True)
    with io.open(args.out, "w", encoding="utf-8", newline="") as fh:
        fh.write(blob)
    back = T.read_json(args.out)
    if T.record_key_leaks(back):
        os.remove(args.out)
        raise Stop(u"**書いた後の記録に鍵らしい字が在った。消して止める**")
    print(T.dumps({u"配線の門": gate, u"集計": rec[u"集計"]}))
    print(u"cache", before, after, u"DEFAULT_PROFILE", V.DEFAULT_PROFILE, u"所要秒", rec[u"所要秒"])
    print(u"->", args.out)


if __name__ == "__main__":
    main()
