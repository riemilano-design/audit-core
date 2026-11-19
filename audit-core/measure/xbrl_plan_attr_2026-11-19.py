# -*- coding: utf-8 -*-
u"""封 docs/XBRL_PLAN_ATTR_SEAL_2026-11-19.md(PA ― 「実績の数でない(見積り・計画の数)のに実績の fact に結んだ行」を文の字で止める後付けの規則は、取り違えをどれだけ止め、正しい結びをどれだけ減らすか)の測定。
**0 USD・通信なし・鍵は読まない・LLM は呼ばない。engine(``core/``・``adapters/``)は 1 行も変えない。**止める規則は engine の外に置いた後付けの数え直しで、state は書き換えない。
材料は TSS の置き場(~/.cache/audit-core/tanshin-self-2026-11-14/)の ZIP 400 本と、KAM・YS の 3 つの folder(~/.cache/audit-core/ の甲・乙・丙)の ZIP 201 本を読むだけ。

    python3 measure/xbrl_plan_attr_2026-11-19.py run --out PATH [--material DIR] [--cache-base DIR] [--procs N]   # 数える → fixtures/xbrl/plan_attr/stops_2026-11-19.json
    python3 measure/xbrl_plan_attr_2026-11-19.py run --check [--material DIR] [--cache-base DIR] [--procs N]      # 書かずに作り直し、在る記録と比べる(時間の欄は除く)

実装の注(封 §2 が 1 通りに決めていない細部の決め。実装より先に決め、結果を見て変えない。報告にも書く):
- 前の便の script は ``load_module`` の形(読み込みの前に居た名前を元の object へ戻す)で読み、関数を **呼ぶ**(写さない)。便 SC の script の ``sentences_of``・``read_bytes``・``number_start_kind``・
  ``heading_indices``・``nearest_heading``・``build_labels``・``cat_name``・``is_drop``・``match``・``index_rows``・``wire``系の下の層・``engine_fp``・``cut_counts`` を呼ぶ。
  便 SC の ``unit_digest`` は文の字と claim を外へ返さず、段の語も SC の表なので、この便の ``unit_digest`` は自分で書き、行の引き方(``PS.claims_of``・``cut_*``・``build_modified_zip``)は便 SC と同じ呼び方にする。
- 行は state が GROUNDED か VALUE_MISMATCH の数の claim の全部(member の欄を問わない。封 §2-1)。行の欄は便 SC の行の欄から「member が空」を除いたもの(先頭 6 欄 = 鍵 5 + state は便 SC と同じ並び)。
- P の行 = verify の claim の state が UNVERIFIABLE で reason が ``target_or_plan``(``PS.REASON_P``)。決算期の字の規則で止まった行 = **raw の claim** の ``p27_gate`` が ``future_period``
  (``_p27_gate`` が書くのは raw の ``num_claims``。実物で確かめる)。「当たるはずの行」= P の行から ``future_period`` を除いた行。95% の確かめは 3 便の合計に掛ける(分母 0 のときは止めない)。
- 当たった類(封 §2-4): 段 1 = 前の字の P。段 2 = 段 1 + 前の字の F + 見出しの P か F(H)。段 3 = 段 2 + 前の字の E + 文の全部の P か F で、**前の字に P も F も無いとき**だけ W。
  (封の「W は文の全部(前の字では当たらず、数の後ろの字で当たった)」を、P と F の組で「前の字で当たらず」と読んだ。P か F が前の字に在れば、その行は段 1・段 2 で既に止まっているので W は付けない。)
- 札の鍵・引き方・属性の写しは便 SC と同じ(``SC.match``・``SC.build_labels``)。V の札の「見積り・計画」= 便 AT の写しの表で 外(見積り・計画)に写る札(``SC.cat_name``)。
  「それ以外」= 分母から除く札を除いた残り。「それ以外」の属性ごとは V の札の属性ごとの欄に並ぶ。
- 重なり(封 §2-5 の 4)の便 SC の側は、便 SC の記録の行の「段 2 の当たりの類」の欄が空でないかで読む(計算し直さない)。この便の側は今回の行の段 2。
- 記録は文・値・要素名・枠の id・pointer の字・主語の語・会社名・証券コード・docID・金額を持たない。数・鍵・state・段ごとの当たりの類だけ。時間(秒)以外は 2 回走らせて byte で同じ。
"""
from __future__ import print_function

import argparse
import collections
import importlib.util
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)


def load_module(name_file, mod_name):
    u"""importlib で読み込む。読み込んだ file が中で読む前の便の script は決まった名前で ``sys.modules`` に登録し直して先に居た module を上書きする。
    読み込みの前に居た名前は、読み込みの後に元の object へ戻す(自分の名前 ``mod_name`` は残す)。"""
    before = dict(sys.modules)
    spec = importlib.util.spec_from_file_location(mod_name, os.path.join(HERE, name_file))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        for k, v in before.items():
            if k != mod_name and sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


SC = load_module("xbrl_scope_cond_2026-11-19.py", "scope_cond_for_plan_attr")                    # 便 SC(切り出し・札・見出し・照合)
AT = SC.AT
RT = SC.RT
PS = SC.PS
YS = SC.YS
KAM = SC.KAM
TSS = SC.TSS
ST = SC.ST
TS = SC.TS
Stop = SC.Stop
V = SC.V
VD = SC.VD

SEAL_REL = "docs/XBRL_PLAN_ATTR_SEAL_2026-11-19.md"
SEAL_COMMIT = "e69b733c"
SCRIPT_REL = "measure/xbrl_plan_attr_2026-11-19.py"
REC_DIR_REL = "fixtures/xbrl/plan_attr"
RECORD_REL = REC_DIR_REL + "/stops_2026-11-19.json"
SC_RECORD_REL = SC.RECORD_REL
SC_SCRIPT_REL = SC.SCRIPT_REL

#: 封 §1 の入力(# , path, sha256)。便 SC の封 §1 の表の全部 + 2 行。違えば止まる。門が封の表と 1 行ずつ照らす
INPUTS = (
    (1, "fixtures/xbrl/kam/read_types_2026-11-15.json", "8c9fe6b8def7430908bf925f697ea5a1b1d634dd754933aab7c71b0a913c964a"),
    (2, "fixtures/xbrl/kam/population_2026-11-15.json", "86e31ca230850d9a13061a18f647c17dea2b95a76927d2587374978af2aef410"),
    (3, "fixtures/xbrl/kam/states_2026-11-15.json", "3ba57f55e62a29e20578b87f527de35d9bc3d2310cbba232d9311c9b187103e7"),
    (4, "fixtures/xbrl/yuho_sections/read_types_2026-11-16.json", "9087a95d0f51e559012b72a9f5f2af7c9575e57589120b50b7ba1d93f46fd3bb"),
    (5, "fixtures/xbrl/yuho_sections/population_2026-11-16.json", "7264bd201eeff1f2b011e783fe26ae4b9435ca7e3fb0436f148a662ff16a3374"),
    (6, "fixtures/xbrl/yuho_sections/states_2026-11-16.json", "130498b4781160154210cacd31d35a8498e4d460f7d3ac88968bf21a7aae4ac5"),
    (7, "fixtures/xbrl/tanshin_self/vm_types_2026-11-14.json", "d1392722f345c408372ec644e15170463554683c3c7ff3951a51d9f66a1f5183"),
    (8, "fixtures/xbrl/tanshin_self/vm_types_subreading_2026-11-14.json", "d5d336bf3eeda37b36db41c02f8a84142257c22921daeb56b5818b262b3235bb"),
    (9, "fixtures/xbrl/tanshin_self/population_2026-11-14.json", "48ba8e5574be70d85b3d1affacc9403cffbfc698f529c095c6c882cd8ccfa9b0"),
    (10, "fixtures/xbrl/tss_retake/retake_2026-11-18.json", "34845f1b3772993aebc0a48d1cec0f6ee5889f9f66843a88f94e572392263cd7"),
    (11, "fixtures/xbrl/attr_tally/tally_2026-11-17.json", "dbbf45e5cd0363bfbc533b5a832454c325de546b845a292d08d17a58194545b6"),
    (12, "measure/xbrl_kam_2026-11-15.py", "cc2aab3029ef76d91e73aceae562370d3e74a58f51d90cecfb6153e28259aa4a"),
    (13, "measure/xbrl_yuho_sections_2026-11-16.py", "23162fa9221aaa7a71e2ab602c46ac92cb473bb85d3fdeef75ba4c2d22373191"),
    (14, "measure/xbrl_tanshin_self_2026-11-14.py", "fa603d1c2dbfdee7c3ad4197ab9c4a9f1428419ada57293f346418bc0997aeb6"),
    (15, "measure/xbrl_plan_source_2026-11-17.py", "0617d75a98e9aca390426b2751bed5ae40a8aa8759b3e80bffab163e1abeb8ea"),
    (16, "measure/xbrl_attr_tally_2026-11-17.py", "e6f66feaf3027ee425c3d421e97abd6edf49f77f5e9e2e515061afdcb4014346"),
    (17, "measure/xbrl_tss_retake_2026-11-18.py", "4d1c4276f67f2fd5551ba0372b2a09c07a2ee4c493b09942e3f360ee35e5b82e"),
    (18, "adapters/xbrl/recipes.py", "346adb0d586e3af233b381f721c3512eea02809c287e02aa948bb0d04031e403"),
    (19, "adapters/xbrl/instance.py", "1b8c00f86eafe765ce44be9ee93cc9ff7a492bd119074e9aa8f49e13e4970cd8"),
    (20, "adapters/xbrl/vocabulary.py", "369891933a5876c4a942e59b85b500d7fa2aa826f8b0c95e2b1c905623b3806c"),
    (21, "adapters/xbrl/extract.py", "a61da3fc3c336e80a214a5fc71978d9ce63f52b4eec5a763e91f434c2ef06d05"),
    (22, "measure/xbrl_scope_cond_2026-11-19.py", "c7ec858ea9523ede23ab2da6d16b53ec338d50cb35899ecac66705e16919e065"),
    (23, "fixtures/xbrl/scope_cond/stops_2026-11-19.json", "d938942bffb39176464f3c644932cf53258f84676aacdbbbc421de74d4dc08a7"),
)

PROFILE = SC.PROFILE
FP_KEYS = SC.FP_KEYS
STATES = SC.STATES
G_STATE, V_STATE, UN_STATE = STATES[0], STATES[1], STATES[2]
SHORT = SC.SHORT
GV = SC.GV
REASON_P = PS.REASON_P
FUTURE_GATE = u"future_period"
BATCHES = SC.BATCHES
NO_SIDE = SC.NO_SIDE
SIDE_ORDER = SC.SIDE_ORDER
READ_SETS = SC.READ_SETS
STAGES = (1, 2, 3)
STAGE_NAMES = collections.OrderedDict((t, u"段 %d" % t) for t in STAGES)
PLAN_CAT = u"外(見積り・計画)"
HIT_FLOOR_NUM, HIT_FLOOR_DEN = 95, 100                           # 封 §2-2: 当たる率が 95% 未満なら止める

#: 封 §2-3 の手がかりの語の表(字で留める。門が封の表と 1 字ずつ照らす)
WORDS = collections.OrderedDict([
    (u"P", (u"目標", u"計画", u"見込", u"見通")),
    (u"F", (u"予想", u"予定", u"予測", u"想定", u"次期", u"翌期", u"来期", u"翌事業年度", u"翌連結会計年度", u"方針")),
    (u"E", (u"見積", u"仮定", u"試算"))])
CLASS_ORDER = u"PFEHW"

#: 記録の行の欄(行 = 結んだ行 = state が G か V の数の claim。member の欄は問わない)
ROW_COLUMNS = [u"便", u"本の #", u"文の種類か節", u"文の番号", u"位置", u"state", u"段 1 の当たりの類", u"段 2 の当たりの類", u"段 3 の当たりの類"]
(C_BATCH, C_BOOK, C_SIDE, C_SI, C_POS, C_STATE, C_H1, C_H2, C_H3) = range(9)
C_HIT = {1: C_H1, 2: C_H2, 3: C_H3}
SC_C_H2 = SC.C_H2

K_WIRE = u"配線の確認(封 §2-2。予測ではない。違えば止まる)"
K_ALL = u"結んだ行の全部(封 §2-5 の 1)"
K_P = u"engine が止めた行(P の行。封 §2-5 の 1)"
K_LABEL = u"読みの札つきの行(封 §2-5 の 2)"
K_CLASS = u"当たった類ごとの数(封 §2-5 の 3)"
K_OVER = u"便 SC の段 2 との重なり(封 §2-5 の 4)"
K_PRED = u"予測の判定に要る数(PA-1〜PA-8。当たり・外れは結果の文書で)"

STAGE_DEFS = collections.OrderedDict([
    (u"対象", u"結んだ行(state が GROUNDED か VALUE_MISMATCH の数の claim)の全部。member の欄は問わない"),
    (u"前の字", u"その行の文の、頭から数の位置の手前まで"),
    (u"見出し", u"便 SC と同じ: 文の列の中で、長さが 40 字以下・「。」で終わらない・数の claim を 1 つも持たない文。最も近い見出し = その行の文より前で最も近い 1 つだけ(無ければ当たらない)"),
    (u"段 1", u"前の字に類 P の語"),
    (u"段 2", u"段 1、または、前の字に類 F の語、または、最も近い見出しに類 P か F の語"),
    (u"段 3", u"段 2、または、その行の文の全部(数の後ろも)に類 P か F の語、または、前の字に類 E の語")])

LIMITS = (
    u"engine は変えていない。止めた数は engine の外の後付けの規則の数で、engine の旗にしたときの数ではない",
    u"読みの札は AI の席(司令塔)1 席が付けた。盲検でなく、人は読んでいない。この便は札の正しさを 1 つも確かめない",
    u"「見積り・計画」の札の V の行は少なく、KAM は 0 行。YS のその行は 1 つの節。率は粗い",
    u"TSS の G の行には札が無い。「正しい結びの減り」を札で言えるのは KAM と YS だけ",
    u"手がかりの語の表は司令塔が書いた。盲検でない。別の語の表なら数は変わる",
    u"止めた行が「止めて正しかった」かは札の在る行でしか言えない。止めたあとに計画の出所へ結べるかは測らない",
    u"見積りの数(類 E)は「計画」と性質が違う。KAM の「値が違う」の行に見積りの札は 0 行だったので、類 E が何かを正しく止めるかはこの便の札では言えない。数えるのは副作用の側だけ",
    u"材料は決算短信の概況の文(400 本)と有報の KAM・3 つの節(201 本)。ほかの書類には言えない",
    u"W は「前の字に P も F も無く、文の全部(数の後ろ)に P か F の語が在る」と読んだ",
    u"行は鍵・state・段ごとの当たりの類だけで、文・値・要素名・枠の id・pointer の字・主語の語・会社名・証券コード・docID・金額は持たない")


def rate(n, d):
    return RT.rate(n, d)


def load_json(p):
    return TSS.load_json(p)


def dumps(o, level=0):
    return RT.dumps(o, level)


def od(pairs=()):
    return collections.OrderedDict(pairs)


# ======================================================================================================
# 規則(封 §2-3・§2-4。純粋な関数。試験が作り物の入力で走らせる)
def has_word(text, cls):
    u"""字の中に類 ``cls`` の語が在る(部分一致)。"""
    return any(w in text for w in WORDS[cls])


def has_pf(text):
    return has_word(text, u"P") or has_word(text, u"F")


def fmt_hits(hits):
    return u"".join(c for c in CLASS_ORDER if c in hits)


def stage_hits(prefix, whole, heading):
    u"""(段 1, 段 2, 段 3 の当たりの類の字)。``heading`` は最も近い見出しの字(無ければ None)。"""
    p_pre, f_pre, e_pre = has_word(prefix, u"P"), has_word(prefix, u"F"), has_word(prefix, u"E")
    h1 = set(u"P") if p_pre else set()
    h2 = set(h1)
    if f_pre:
        h2.add(u"F")
    if heading is not None and has_pf(heading):
        h2.add(u"H")
    h3 = set(h2)
    if e_pre:
        h3.add(u"E")
    if has_pf(whole) and not (p_pre or f_pre):
        h3.add(u"W")
    return fmt_hits(h1), fmt_hits(h2), fmt_hits(h3)


def unit_digest(pairs, sentences):
    u"""1 つの文(TSS は 1 本・KAM は文の種類・YS は節)の [(raw の claim, verify の claim)] と文の列 → 数えた結果(OrderedDict)。
    位置の確かめ(便 SC の関数)に 1 行でも違えば止める。行は結んだ行だけ。P の行は数だけ数える。"""
    num_sentences = set(r["sentence"] for r, _c in pairs)
    heads = SC.heading_indices(sentences, num_sentences)
    triples, rows = [], []
    counts = collections.Counter()
    for r, c in pairs:
        si, pos = r["sentence"], r["pos"]
        if not isinstance(si, int) or not 0 <= si < len(sentences):
            raise Stop(u"**数の claim の文の番号が文の列の外。止める**")
        s = sentences[si]
        kind = SC.number_start_kind(s, pos, r.get("span"))
        if kind is None:
            raise Stop(u"**数の claim の位置の欄が「文の中の字の位置」でない(数の字で始まらない・span と合わない)。止めて司令塔に返す**")
        counts[u"位置: 数字から" if kind == 0 else u"位置: 符号か空白から"] += 1
        state = c["state"]
        triples.append((si, pos, state))
        if state == UN_STATE and c.get("reason") == REASON_P:
            counts[u"P の行"] += 1
            if r.get("p27_gate") == FUTURE_GATE:
                counts[u"P の行のうち決算期の字の規則(future_period)で止まった行"] += 1
            else:
                counts[u"P の行のうち future_period 以外(当たるはずの行)"] += 1
                if has_word(s, u"P"):
                    counts[u"当たるはずの行のうち文の全部に類 P の語が在る"] += 1
                else:
                    counts[u"当たるはずの行のうち文の全部に類 P の語が無い"] += 1
                    counts[u"当たらなかった行の p27_gate: %s" % (r.get("p27_gate"),)] += 1
        if state not in SHORT:
            continue
        nh = SC.nearest_heading(heads, si)
        h1, h2, h3 = stage_hits(s[:pos], s, sentences[nh] if nh is not None else None)
        rows.append([si, pos, SHORT[state], h1, h2, h3])
    rows.sort(key=lambda x: (x[0], x[1]))
    return od([(u"cut", True), (u"triples", triples), (u"rows", rows), (u"counts", dict(counts)), (u"claims", len(pairs))])


def empty_digest():
    return SC.empty_digest()


# ======================================================================================================
# 1 本の job
def tss_units(zb):
    text = TSS.cut(zb)[0]
    if text is None:
        return [(None, empty_digest())]
    wrapped = TSS.wrap(zb, text)[0]
    return [(None, unit_digest(PS.claims_of(wrapped), SC.sentences_of(wrapped)))]


def kam_units(zb):
    out = []
    for side in KAM.SIDES:
        text = KAM.cut_kam(zb, side)[0]
        if text is None:
            out.append((side, empty_digest()))
            continue
        zm = KAM.PR.build_modified_zip(zb, text)[0]
        out.append((side, unit_digest(PS.claims_of(zm), SC.sentences_of(zm))))
    return out


def ys_units(zb):
    out = []
    for section in YS.SECTIONS:
        text = YS.cut_section(zb, section)[0]
        if text is None:
            out.append((section, empty_digest()))
            continue
        zm = YS.PR.build_modified_zip(zb, text)[0]
        out.append((section, unit_digest(PS.claims_of(zm), SC.sentences_of(zm))))
    return out


UNITS_OF = {u"TSS": tss_units, u"KAM": kam_units, u"YS": ys_units}


def book_job(args):
    u"""1 本: (便, 本の #, 群, sha256, ZIP の path) → {便, 本の #, units: [(文の種類か節, 数えた結果)]}。"""
    batch, n, _grp, sha, path = args
    zb = SC.read_bytes(path, sha, n)
    return od([(u"便", batch), (u"#", n), (u"units", UNITS_OF[batch](zb))])


# ======================================================================================================
# 結んだ行
def link_rows(books):
    u"""本の job の結果の列 → 記録の行(結んだ行)。便の順(TSS・KAM・YS)→ 本の # → 文の種類か節の順 → 文の番号 → 位置。"""
    rows = []
    for b in sorted(books, key=lambda b: (BATCHES.index(b[u"便"]), b[u"#"])):
        for side, u in b[u"units"]:
            for r in u[u"rows"]:
                rows.append([b[u"便"], b[u"#"], side] + list(r))
    return rows


def stopped(row, t):
    return row[C_HIT[t]] != u""


def index_rows(rows):
    return SC.index_rows(rows)


def stage_cells(rows):
    u"""結んだ行の集まり → {結んだ行, 止めた行: {段 1..3}}。"""
    return od([(u"結んだ行", len(rows)), (u"止めた行", od((STAGE_NAMES[t], sum(1 for r in rows if stopped(r, t))) for t in STAGES))])


def tally_all(rows):
    u"""§2-5 の 1。便ごと・state ごと(KAM は文の種類ごと・YS は節ごとにも)。"""
    out = od()
    for batch in BATCHES:
        br = [r for r in rows if r[C_BATCH] == batch]
        b = od([(u"全体", od((s, stage_cells([r for r in br if r[C_STATE] == s])) for s in GV))])
        if batch != u"TSS":
            b[u"文の種類別" if batch == u"KAM" else u"節別"] = od(
                (side, od((s, stage_cells([r for r in br if r[C_SIDE] == side and r[C_STATE] == s])) for s in GV)) for side in SIDE_ORDER[batch])
        out[batch] = b
    return out


P_KEYS = (u"P の行", u"P の行のうち決算期の字の規則(future_period)で止まった行", u"P の行のうち future_period 以外(当たるはずの行)",
          u"当たるはずの行のうち文の全部に類 P の語が在る", u"当たるはずの行のうち文の全部に類 P の語が無い")


def p_cells(counts):
    u"""``Counter`` → P の行の数の欄(当たらなかった行の p27_gate の内訳も)。"""
    out = od((k, counts.get(k, 0)) for k in P_KEYS)
    out[u"当たる率(当たるはずの行のうち)"] = rate(counts.get(P_KEYS[3], 0), counts.get(P_KEYS[2], 0))
    out[u"当たらなかった行の p27_gate の内訳"] = od(sorted((k.split(u": ", 1)[1], v) for k, v in counts.items() if k.startswith(u"当たらなかった行の p27_gate: ")))
    return out


def p_counts(books, batch, side=False):
    u"""便(と文の種類・節)ごとの P の行の数の合計の Counter。"""
    c = collections.Counter()
    for b in books:
        if b[u"便"] != batch:
            continue
        for s, u in b[u"units"]:
            if side is False or s == side:
                c.update(dict((k, v) for k, v in u[u"counts"].items() if k.startswith((u"P の行", u"当たる", u"当たらなかった"))))
    return c


def tally_p(books):
    u"""§2-5 の 1 の P の行の数。便ごと(KAM は文の種類ごと・YS は節ごと)と 3 便の合計。"""
    out = od()
    total = collections.Counter()
    for batch in BATCHES:
        c = p_counts(books, batch)
        total.update(c)
        b = od([(u"全体", p_cells(c))])
        if batch != u"TSS":
            b[u"文の種類別" if batch == u"KAM" else u"節別"] = od((side, p_cells(p_counts(books, batch, side))) for side in SIDE_ORDER[batch])
        out[batch] = b
    out[u"合計"] = od([(u"全体", p_cells(total))])
    return out


def class_counts(rows, t):
    u"""段 t で止めた行の、類ごとの数(複数に当たれば全部に数える)。"""
    hit = [r for r in rows if stopped(r, t)]
    return od([(u"止めた行", len(hit))] + [(c, sum(1 for r in hit if c in r[C_HIT[t]])) for c in CLASS_ORDER])


def tally_class(rows):
    u"""§2-5 の 3。便ごと(と 3 便の合計)・段ごと・state ごと。"""
    out = od()
    for batch in list(BATCHES) + [u"合計"]:
        br = rows if batch == u"合計" else [r for r in rows if r[C_BATCH] == batch]
        out[batch] = od((STAGE_NAMES[t], od((s, class_counts([r for r in br if r[C_STATE] == s], t)) for s in GV)) for t in STAGES)
    return out


# ======================================================================================================
# 読みの札(封 §2-5 の 2)
def match(labels, index):
    return SC.match(labels, index)


def cell(matched):
    u"""[(札, 行 or None, 理由)] → 札の行・引けた行(分母)・引けなかった行(理由別)・止めた行(段別)。"""
    got = [m[1] for m in matched if m[1] is not None]
    why = collections.Counter(m[2] for m in matched if m[1] is None)
    return od([(u"札の行", len(matched)), (u"引けた行(分母)", len(got)), (u"引けなかった行", len(matched) - len(got)),
               (u"引けなかった理由", od([(u"行が無い", why.get(u"行が無い", 0)), (u"state が違う", why.get(u"state が違う", 0))])),
               (u"止めた行", od((STAGE_NAMES[t], sum(1 for r in got if stopped(r, t))) for t in STAGES))])


def is_plan(lab):
    return SC.cat_name(lab) == PLAN_CAT


def is_drop(lab):
    return SC.is_drop(lab)


def v_split(ms):
    u"""V の札の [(札, 行, 理由)] → (見積り・計画, それ以外, 分母から除く札)。"""
    plan = [m for m in ms if is_plan(m[0])]
    other = [m for m in ms if not is_plan(m[0]) and not is_drop(m[0])]
    drop = [m for m in ms if is_drop(m[0])]
    return plan, other, drop


def v_tally(vms_by_batch):
    u"""V の札。便ごと・3 便の合計。属性ごと(「それ以外」の属性ごとを含む)・見積り・計画 / それ以外 / 分母から除く札。"""
    out = od()
    names = list(AT.ATTRS)
    for batch in BATCHES:
        for r in AT.out_reasons(batch):
            if u"外(%s)" % r not in names:
                names.append(u"外(%s)" % r)
    names.append(AT.EXCLUDE)
    total = []
    for batch in list(BATCHES) + [u"合計"]:
        ms = total if batch == u"合計" else vms_by_batch[batch]
        if batch != u"合計":
            total = total + vms_by_batch[batch]
        plan, other, drop = v_split(ms)
        out[batch] = od([
            (u"全体", cell(ms)),
            (u"属性ごと", od((nm, cell([m for m in ms if SC.cat_name(m[0]) == nm])) for nm in names)),
            (u"1 株あたりについて", u"この属性に写る型は表に無い。0 は作りで、測った 0 ではない"),
            (u"見積り・計画", cell(plan)), (u"それ以外(分母から除く札は除く)", cell(other)), (u"分母から除く札", cell(drop))])
    return out


def g_tally(gms_by_batch):
    u"""G の札(KAM・YS)。a・b・c ごと。便ごと・合計。"""
    out = od()
    total = []
    for batch in (u"KAM", u"YS", u"合計"):
        ms = total if batch == u"合計" else gms_by_batch[batch]
        if batch != u"合計":
            total = total + gms_by_batch[batch]
        out[batch] = od([(u"全体", cell(ms)), (u"型ごと", od((t, cell([m for m in ms if m[0][u"型"] == t])) for t in AT.G_TYPES))])
    return out


def split_labels(labels, index):
    return SC.split_labels(labels, index)


def tally_label(labels, rows):
    vms, gms = split_labels(labels, index_rows(rows))
    return od([(u"V の札", v_tally(vms)), (u"G の札(KAM・YS)", g_tally(gms))])


# ======================================================================================================
# 便 SC の段 2 との重なり(封 §2-5 の 4)
def sc_index(sc_rec):
    u"""便 SC の記録の行 → {鍵: 行}。"""
    return dict(((r[0], r[1], r[2], r[3], r[4]), r) for r in sc_rec[u"行"])


def sc_stopped(sc_idx, row):
    u"""便 SC の段 2 で止めた行か(便 SC の記録の行の「段 2 の当たりの類」の欄が空でない)。鍵が便 SC の記録に無ければ止める。"""
    k = (row[C_BATCH], row[C_BOOK], row[C_SIDE], row[C_SI], row[C_POS])
    if k not in sc_idx:
        raise Stop(u"**この便の結んだ行が便 SC の記録の行に無い。止める**")
    return sc_idx[k][SC_C_H2] != u""


def over_cell(rows, sc_idx):
    u"""行の集まり → 便 SC の段 2 × この便の段 2 の 4 つの数。"""
    a = collections.Counter()
    for r in rows:
        a[(sc_stopped(sc_idx, r), stopped(r, 2))] += 1
    return od([(u"行", len(rows)), (u"両方で止めた", a[(True, True)]), (u"便 SC だけが止めた", a[(True, False)]),
               (u"この便だけが止めた", a[(False, True)]), (u"どちらも止めない", a[(False, False)])])


def ms_rows(ms):
    return [m[1] for m in ms if m[1] is not None]


def tally_over(rows, labels, sc_idx):
    u"""結んだ行の全部(便ごと・state ごと・合計)と、札つきの行(引けた行)のそれぞれ。"""
    out = od()
    allr = od()
    for batch in list(BATCHES) + [u"合計"]:
        br = rows if batch == u"合計" else [r for r in rows if r[C_BATCH] == batch]
        allr[batch] = od((s, over_cell([r for r in br if r[C_STATE] == s], sc_idx)) for s in GV)
    out[u"結んだ行の全部"] = allr
    vms, gms = split_labels(labels, index_rows(rows))
    vl = od()
    total = []
    for batch in list(BATCHES) + [u"合計"]:
        ms = total if batch == u"合計" else vms[batch]
        if batch != u"合計":
            total = total + vms[batch]
        plan, other, drop = v_split(ms)
        vl[batch] = od([(u"札つきの V の行(分母から除く札は除く)", over_cell(ms_rows(plan + other), sc_idx)), (u"見積り・計画", over_cell(ms_rows(plan), sc_idx)),
                        (u"それ以外", over_cell(ms_rows(other), sc_idx)), (u"分母から除く札", over_cell(ms_rows(drop), sc_idx))])
    out[u"V の札(引けた行)"] = vl
    gl = od()
    gtotal = []
    for batch in (u"KAM", u"YS", u"合計"):
        ms = gtotal if batch == u"合計" else gms[batch]
        if batch != u"合計":
            gtotal = gtotal + gms[batch]
        gl[batch] = od([(u"全体", over_cell(ms_rows(ms), sc_idx))] + [(t, over_cell(ms_rows([m for m in ms if m[0][u"型"] == t]), sc_idx)) for t in AT.G_TYPES])
    out[u"G の札(KAM・YS。引けた行)"] = gl
    return out


# ======================================================================================================
# 予測の判定に要る数
def stage_fracs(num_by_stage, den):
    return od((STAGE_NAMES[t], rate(num_by_stage[t], den)) for t in STAGES)


def ms_counts(ms):
    got = [m[1] for m in ms if m[1] is not None]
    return len(got), dict((t, sum(1 for r in got if stopped(r, t))) for t in STAGES)


def fr(ms):
    den, cnt = ms_counts(ms)
    return stage_fracs(cnt, den)


def rows_fr(rs):
    return stage_fracs(dict((t, sum(1 for r in rs if stopped(r, t))) for t in STAGES), len(rs))


def point_diff_stage(a_ms, b_ms, t):
    u"""(a の率 − b の率)× 100 を小数 2 桁の字で(RT の ``point_diff``。分母 0 があれば「分母 0」)。"""
    da, ca = ms_counts(a_ms)
    db, cb = ms_counts(b_ms)
    return RT.point_diff(cb[t], db, ca[t], da)


def predictions(rows, labels, sc_idx):
    vms, gms = split_labels(labels, index_rows(rows))
    plan_b = dict((b, v_split(vms[b])[0]) for b in BATCHES)
    other_b = dict((b, v_split(vms[b])[1]) for b in BATCHES)
    drop_b = dict((b, v_split(vms[b])[2]) for b in BATCHES)
    plan = [m for b in BATCHES for m in plan_b[b]]
    plan_ys_tss = plan_b[u"YS"] + plan_b[u"TSS"]
    other = [m for b in BATCHES for m in other_b[b]]
    v_all = [m for b in BATCHES for m in vms[b]]
    v_kept = plan + other
    g_all = [m for b in (u"KAM", u"YS") for m in gms[b]]
    a_b = dict((b, [m for m in gms[b] if m[0][u"型"] == u"a"]) for b in (u"KAM", u"YS"))
    a_all = [m for b in (u"KAM", u"YS") for m in a_b[b]]
    tss = [r for r in rows if r[C_BATCH] == u"TSS"]
    tss_g = [r for r in tss if r[C_STATE] == u"G"]
    tss_v = [r for r in tss if r[C_STATE] == u"V"]
    den_plan = ms_counts(plan)[0]

    out = od()
    out[u"分母の確かめ(「見積り・計画」の札の V の行の引けた行が 15 行未満なら PA-1・PA-5・PA-6 は測れていない)"] = od([
        (u"「見積り・計画」の札の V の行(札)", len(plan)), (u"「見積り・計画」の札の V の行(引けた行)", den_plan), (u"15 行未満", den_plan < 15),
        (u"V の札の行(札)", len(v_all)), (u"V の札の行(引けた)", ms_counts(v_all)[0]), (u"G の札の行(札)", len(g_all)), (u"G の札の行(引けた)", ms_counts(g_all)[0])])
    out[u"PA-1 「見積り・計画」の札の V の行(YS と TSS の合計)の止めた行 / 引けた行(段 1・2・3。主は段 2)"] = od([
        (u"YS と TSS の合計", fr(plan_ys_tss))] + [(u"3 便の合計", fr(plan))] + [(b, fr(plan_b[b])) for b in BATCHES])
    out[u"PA-2 同じ行の段 1 の止めた行 / 引けた行(上の PA-1 の欄の段 1)"] = od([(u"YS と TSS の合計", fr(plan_ys_tss)[STAGE_NAMES[1]])])
    out[u"PA-3 札 a の G の行(KAM と YS の合計)の止めた行 / 引けた行(段 1・2・3。主は段 2)"] = od([(u"KAM と YS の合計", fr(a_all))] + [(b, fr(a_b[b])) for b in (u"KAM", u"YS")])
    out[u"PA-4 KAM の札 a の G の行の止めた行 / 引けた行(段 1・2・3。主は段 3)"] = fr(a_b[u"KAM"])
    out[u"PA-5 「それ以外」の札の V の行(3 便の合計)の止めた行 / 引けた行(段 1・2・3。主は段 2)"] = od([(u"3 便の合計", fr(other))] + [(b, fr(other_b[b])) for b in BATCHES])
    out[u"PA-5 率の差(ポイント。「見積り・計画」の率 − 「それ以外」の率。小数 2 桁の字)"] = od((STAGE_NAMES[t], point_diff_stage(plan, other, t)) for t in STAGES)
    out[u"PA-6 段ごとの「見積り・計画の札の V の行(3 便の合計)」の止めた行 / 引けた行 と「札 a の G の行(KAM と YS の合計)」の止めた行 / 引けた行"] = od(
        (STAGE_NAMES[t], od([(u"見積り・計画の札の V の行", fr(plan)[STAGE_NAMES[t]]), (u"札 a の G の行", fr(a_all)[STAGE_NAMES[t]])])) for t in STAGES)
    out[u"PA-7a TSS の G の全部の行の止めた行 / TSS の G の行(段 1・2・3。主は段 2)"] = rows_fr(tss_g)
    out[u"PA-7b TSS の V の全部の行の止めた行 / TSS の V の行(段 1・2・3。主は段 2)"] = rows_fr(tss_v)
    out[u"PA-8 札つきの V の行(3 便の合計。分母から除く札は除く)の便 SC の段 2 とこの便の段 2 の重なり(引けた行)"] = over_cell(ms_rows(v_kept), sc_idx)
    out[u"PA-8 参考 分母から除く札の V の行の重なり(3 便の合計)"] = over_cell(ms_rows([m for b in BATCHES for m in drop_b[b]]), sc_idx)
    return out


# ======================================================================================================
# 配線の確認(封 §2-2)
def wire_sc(rows, sc_rec, books):
    u"""引き直した結んだ行の(鍵, state)の集まりが、便 SC の記録の行のうち同じ本のものと同じ(行の数も)。違えば止める。"""
    present = set((b[u"便"], b[u"#"]) for b in books)
    now = [tuple(r[:6]) for r in rows]
    want = [tuple(r[:6]) for r in sc_rec[u"行"] if (r[0], r[1]) in present]
    if len(set(now)) != len(now) or len(set(want)) != len(want):
        raise Stop(u"**結んだ行の鍵が重なる。止める**")
    out = od()
    for batch in BATCHES:
        n_ = set(x for x in now if x[0] == batch)
        w_ = set(x for x in want if x[0] == batch)
        out[batch] = od([(u"引き直した結んだ行", len(n_)), (u"便 SC の記録の結んだ行(同じ本)", len(w_)), (u"鍵と state が同じ行", len(n_ & w_)),
                         (u"今にだけ在る行", len(n_ - w_)), (u"便 SC の記録にだけ在る行", len(w_ - n_))])
    if set(now) != set(want) or len(now) != len(want):
        raise Stop(u"**引き直した結んだ行の(鍵, state)が便 SC の記録の行と違う。止めて司令塔に返す**")
    return out


def wiring_counts(books):
    u"""位置の確かめ(便ごと)。"""
    out = od()
    for batch in BATCHES:
        c = collections.Counter()
        for b in books:
            if b[u"便"] == batch:
                for _side, u in b[u"units"]:
                    c.update(u[u"counts"])
        out[batch] = od([(u"位置を確かめた数の claim(state を問わない)", c.get(u"位置: 数字から", 0) + c.get(u"位置: 符号か空白から", 0)),
                         (u"うち pos の字が数字", c.get(u"位置: 数字から", 0)), (u"うち pos の字が符号か空白", c.get(u"位置: 符号か空白から", 0))])
    return out


def check_p_hit(books):
    u"""「当たるはずの行」に文の全部の類 P の語が当たる率(3 便の合計)。95% 未満なら止める。"""
    c = collections.Counter()
    for batch in BATCHES:
        c.update(p_counts(books, batch))
    total, hit = c.get(P_KEYS[2], 0), c.get(P_KEYS[3], 0)
    if total > 0 and hit * HIT_FLOOR_DEN < HIT_FLOOR_NUM * total:
        raise Stop(u"**当たるはずの行に類 P の語が当たる率が 95% 未満(語の当て方か文の取り方が engine と違う疑い)。止めて司令塔に返す**")
    return od([(u"当たるはずの行(3 便の合計)", total), (u"当たった", hit), (u"当たらなかった", c.get(P_KEYS[4], 0)), (u"率", rate(hit, total)),
               (u"止める条件", u"率が 95% 未満"), (u"止まらなかった", True)])


# ======================================================================================================
# 入力・記録
def check_inputs(root):
    out = []
    for no, rel, want in INPUTS:
        p = os.path.join(root, rel)
        if not os.path.isfile(p) or ST.sha256_file(p) != want:
            raise Stop(u"**入力 %d の sha256 が封の表と違う。止める**" % no)
        out.append(od([(u"#", no), (u"path", rel), (u"sha256", want)]))
    return out


def load_records(root):
    recs = SC.load_records(root)
    recs[u"sc"] = load_json(os.path.join(root, SC_RECORD_REL))
    return recs


def engine_fp(rt_rec):
    return SC.engine_fp(rt_rec)


def scan_material(base, pop):
    return KAM.scan_material(base, pop)


def folder_snapshots(base):
    return KAM.folder_snapshots(base)


def subset_shape(pop):
    return RT.subset_shape(pop)


def orchestrate(root=ROOT, procs=1, material=None, cache_base=None, say=print, populations=None, clock=time.time, recs=None, inputs=None):
    u"""TSS 400 本・KAM 201 本・YS 201 本 → 配線の確認 → 数える → 記録(OrderedDict)。書かない。
    ``recs``(入力の記録)を渡すと(試験用)入力の sha256 の確かめと記録の読みを飛ばす。``populations`` = {便: 母集団}(試験用)。"""
    if recs is None:
        inputs = check_inputs(root)
        recs = load_records(root)
    inputs = inputs or []
    mat, prod = RT.material_dir(material)
    base = cache_base or KAM.default_base()
    if populations is None:
        tss_pop = ST.read_population(root)
        kam_pop = KAM.read_population(root)
        ys_pop = YS.read_population(root)
        SC.check_pop_record(kam_pop, recs[u"kam_pop"], u"KAM")
        SC.check_pop_record(ys_pop, recs[u"ys_pop"], u"YS")
    else:
        tss_pop, kam_pop, ys_pop = populations[u"TSS"], populations[u"KAM"], populations[u"YS"]
    shape = subset_shape(tss_pop)
    fp = engine_fp(recs[u"rt"])
    ST.validate_population(tss_pop, *(shape or (ST.N_ROWS, ST.GROUP_COUNTS)))
    for (n, _g, _k, sha) in tss_pop:
        if not os.path.exists(os.path.join(mat, sha + u".zip")):
            raise Stop(u"**材料の ZIP が置き場に無い(# %d)。止める**" % n)
    before_tss = ST.names_snapshot(mat)
    before_cache = folder_snapshots(base)
    kam_found = scan_material(base, kam_pop)
    ys_found = scan_material(base, ys_pop)
    jobs = [(u"TSS", n, g, sha, os.path.join(mat, sha + u".zip")) for (n, g, _k, sha) in tss_pop]
    jobs += [(u"KAM", n, g, sha, kam_found[sha][0]) for (n, g, sha) in kam_pop]
    jobs += [(u"YS", n, g, sha, ys_found[sha][0]) for (n, g, sha) in ys_pop]
    say(u"TSS %d 本・KAM %d 本・YS %d 本 × %s ― procs %d" % (len(tss_pop), len(kam_pop), len(ys_pop), PROFILE, procs))
    t0 = clock()
    books = TS.NF.map_pool(book_job, jobs, procs)
    elapsed = clock() - t0
    if before_tss != ST.names_snapshot(mat) or before_cache != folder_snapshots(base):
        raise Stop(u"**材料の置き場の件数か名前が変わった。止める**")
    rows = link_rows(books)
    sc_idx = sc_index(recs[u"sc"])
    wire = od()
    wire[u"結んだ行の(鍵, state)と便 SC の記録の行の照合(違えば止まる)"] = wire_sc(rows, recs[u"sc"], books)
    wire[u"位置の確かめ(便ごと。便 SC の関数)"] = wiring_counts(books)
    wire[u"当たるはずの行に当たるか(P の行から future_period を除いた行に文の全部の類 P の語。95% 未満なら止まる)"] = check_p_hit(books)
    wire[u"本の数"] = od([(u"TSS", len(tss_pop)), (u"KAM", len(kam_pop)), (u"YS", len(ys_pop))])
    labels = SC.build_labels(recs)
    rec = od()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"PA(実績の数でないのに実績の fact に結んだ行を文の字で止める後付けの規則 ― 段 1・2・3)(0 USD・通信なし・engine は 0 行)"
    rec[u"この script の sha256"] = ST.sha256_file(os.path.abspath(__file__))
    rec[u"入力"] = inputs
    rec[u"engine の指紋(今。便 RT の記録の今と同じ)"] = fp
    rec[u"profile"] = PROFILE
    rec[u"材料"] = od([(u"TSS の置き場", ST.display_path(mat) if prod else u"使い捨ての置き場(本番の folder ではない)"),
                      (u"KAM・YS の置き場", u"~/.cache/audit-core の 3 つの folder(甲・乙・丙。名前は書かない)"),
                      (u"表と一致した ZIP", od([(u"TSS", len(tss_pop)), (u"KAM", len(kam_pop)), (u"YS", len(ys_pop))]))])
    rec[u"手がかりの語の表"] = od([(c, list(w)) for c, w in WORDS.items()])
    rec[u"段の定義"] = STAGE_DEFS
    rec[u"切り出し"] = SC.cut_counts(books)
    rec[K_WIRE] = wire
    rec[K_ALL] = tally_all(rows)
    rec[K_P] = tally_p(books)
    rec[K_LABEL] = tally_label(labels, rows)
    rec[K_CLASS] = tally_class(rows)
    rec[K_OVER] = tally_over(rows, labels, sc_idx)
    rec[K_PRED] = predictions(rows, labels, sc_idx)
    rec[u"限界"] = list(LIMITS)
    rec[u"時間(秒)"] = round(elapsed, 1)
    rec[u"key_leaks"] = []
    rec[u"行の欄"] = list(ROW_COLUMNS)
    rec[u"行"] = rows
    return rec


def check_text(rec, text, key_value=None):
    scan = text.replace(SEAL_REL, u"")
    for _no, rel, _sha in INPUTS:
        scan = scan.replace(rel, u"")
    TSS.check_clean(rec, scan, key_value)


def record_text(rec, key_value=None):
    text = dumps(rec) + u"\n"
    check_text(rec, text, key_value)
    return text


def run(root=ROOT, procs=1, out=None, material=None, cache_base=None, say=print, check=False, **kw):
    if not check and out is None:
        raise Stop(u"**--out を指定する(書かずに比べるなら --check)。止める**")
    out = os.path.abspath(out) if out else None
    if out and os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    rec = orchestrate(root=root, procs=procs, material=material, cache_base=cache_base, say=say, **kw)
    text = record_text(rec)
    if check:
        want = os.path.join(root, RECORD_REL)
        if not os.path.isfile(want):
            raise Stop(u"**在る記録が無い。止める**")
        cur = load_json(want)
        cur[u"時間(秒)"] = 0
        rec2 = json.loads(text, object_pairs_hook=collections.OrderedDict)
        rec2[u"時間(秒)"] = 0
        if dumps(cur) != dumps(rec2):
            raise Stop(u"**作り直した記録が在る記録と違う(時間の欄は除く)。止める**")
        say(u"--check: 在る記録と同じ(時間の欄は除く)")
        return rec
    ST.write_text_exclusive(out, text)
    say(u"-> %s" % os.path.basename(out))
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    a = sub.add_parser("run")
    a.add_argument("--root", default=ROOT)
    a.add_argument("--out", default=None)
    a.add_argument("--check", action="store_true")
    a.add_argument("--material", default=None)
    a.add_argument("--cache-base", default=None)
    a.add_argument("--procs", type=int, default=1)
    a_ = ap.parse_args(argv)
    if a_.cmd == "run":
        run(root=a_.root, procs=a_.procs, out=a_.out, material=a_.material, cache_base=a_.cache_base, check=a_.check)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
