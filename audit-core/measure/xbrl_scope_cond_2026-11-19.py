# -*- coding: utf-8 -*-
u"""封 docs/XBRL_SCOPE_COND_SEAL_2026-11-19.md(SC ― 「文は一部分を言っているのに全体の fact に結んだ行」を文の字で止める後付けの規則は、取り違えをどれだけ止め、正しい結びをどれだけ減らすか)の測定。
**0 USD・通信なし・鍵は読まない・LLM は呼ばない。engine(``core/``・``adapters/``)は 1 行も変えない。**止める規則は engine の外に置いた後付けの数え直しで、state は書き換えない。
材料は TSS の置き場(~/.cache/audit-core/tanshin-self-2026-11-14/)の ZIP 400 本と、KAM・YS の 3 つの folder(~/.cache/audit-core/ の甲・乙・丙)の ZIP 201 本を読むだけ。

    python3 measure/xbrl_scope_cond_2026-11-19.py run --out PATH [--material DIR] [--cache-base DIR] [--procs N]   # 数える → fixtures/xbrl/scope_cond/stops_2026-11-19.json
    python3 measure/xbrl_scope_cond_2026-11-19.py run --check [--material DIR] [--cache-base DIR] [--procs N]      # 書かずに作り直し、在る記録と比べる(時間の欄は除く)

実装の注(封 §2 が 1 通りに決めていない細部の決め。実装より先に決め、結果を見て変えない。報告にも書く):
- 前の便の script は ``load_module`` の形(読み込みの前に居た名前を元の object へ戻す)で読み、関数を **呼ぶ**(写さない)。TSS の行は便 SE と同じ ``PS.claims_of(包んだ ZIP)``、
  KAM・YS の行は ``PR.build_modified_zip(ZIP, 文)[0]`` を ``PS.claims_of`` に渡して取る(``verify_document(ZIP, P33E, text=文)`` は中で同じ ZIP を作るので、前の便の ``profile_rows`` と同じ行になる。記録の突き合わせで確かめる)。
- 文の列は ``TS.RUN.sentence_list(その ZIP, P33E)``(raw の ``sentence`` が指す文)。見出しは文の列の中で、長さ(``len``)が 40 以下・``。`` で終わらず・その本のその種類で数の raw の claim を 1 つも持たない文。
- 位置の確かめ(封 §2-2): raw の ``pos`` は文の中の字の位置。engine の数の読みは符号と空白を数の一部として読むので、``pos`` の字が空白・符号のことがある。確かめは
  「文の ``pos`` から ``(△|▲|－|-|マイナス)?\\s*\\d`` が当たる」と「raw の ``span`` の ``min(pos, 30)`` 字目から後ろが文の ``pos`` から後ろと同じ」の 2 つ。全部の数の claim(state を問わない)で確かめ、1 行でも違えば止める。
  前の字(=頭から ``pos`` の手前まで)は ``pos`` が空白の位置なら、その空白を含まない。
- 事業の形は語を探す字(前の字・見出し・文の全部)の中で「事業」が出る所ごとに見る。字の終わりも「文の終わり」に数える(前の字の終わりが「事業」の行は、その数を記録の配線の欄に別に書く)。
- 当たった類(封 §2-5 の 3)は、その段の規則が実際に使った字で当たった類。段 1 = 前の字の S・N・U。段 2 = 段 1 + 見出し(H = 最も近い見出しに S)。
  段 3 = 段 2 + 前の字の R・K + 文の全部の S・N・U。N のただし書きは前の字・文の全部の別々に、その字で当たった類が N だけで pointer に ``NonConsolidated`` が在るなら、その字の当たりを全部捨てる。
  N と別の類に当たっていれば N もそのまま数える。member が空でない行はどの段でも当たりを持たない(止めない)。
- 札の鍵は (便, 本の #, 文の種類か節, 文の番号, 位置)。V の札は同じ鍵が今の引き直しで V・G の札は G のときだけ「引けた」。引けなかった行は「行が無い」と「state が違う」に分けて数える。
- V の札の属性は便 AT の script の写しの表(``TABLE``・``table_lookup``)で写す。TSS は細目の記録の字(ケ は細目によらず ケ)。「範囲」= 属性が範囲、「範囲でない」= 内の他の属性と外、分母から除く札は別に数える。
- G の札 b の「違うもの」は 4 つ(項目・範囲・側・期)を別々に数え、「範囲(違うものの字が範囲)」と「範囲 + 側(便 AT の写し)」の 2 通りの束ねを並べる。封は束ね方を決めていないので、どちらも書く。
- 記録は文・値・要素名・枠の id・pointer の字・主語の語・会社名・証券コード・docID・金額を持たない。数・鍵・state・member が空か・段ごとの当たりの類だけ。時間(秒)以外は 2 回走らせて byte で同じ。
"""
from __future__ import print_function

import argparse
import collections
import importlib.util
import io
import json
import os
import re
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


AT = load_module("xbrl_attr_tally_2026-11-17.py", "attr_tally_for_scope_cond")                   # 便 AT(写しの表・読みの記録の検査)
RT = load_module("xbrl_tss_retake_2026-11-18.py", "tss_retake_for_scope_cond")                   # 便 RT(dumps・rate・point_diff)
PS = load_module("xbrl_plan_source_2026-11-17.py", "plan_source_for_scope_cond")                 # 便 PS(claims_of)
YS = load_module("xbrl_yuho_sections_2026-11-16.py", "yuho_sections_for_scope_cond")             # 便 YS(中に KAM)
KAM = YS.KAM
TSS = PS.TSS
ST = TSS.ST
TS = TSS.TS
Stop = ST.Stop
V = PS.V
VD = PS.VD

SEAL_REL = "docs/XBRL_SCOPE_COND_SEAL_2026-11-19.md"
SEAL_COMMIT = "5b77133b"
SCRIPT_REL = "measure/xbrl_scope_cond_2026-11-19.py"
REC_DIR_REL = "fixtures/xbrl/scope_cond"
RECORD_REL = REC_DIR_REL + "/stops_2026-11-19.json"
RT_RECORD_REL = "fixtures/xbrl/tss_retake/retake_2026-11-18.json"
KAM_STATES_REL = "fixtures/xbrl/kam/states_2026-11-15.json"
KAM_READ_REL = "fixtures/xbrl/kam/read_types_2026-11-15.json"
KAM_POP_REL = "fixtures/xbrl/kam/population_2026-11-15.json"
YS_STATES_REL = "fixtures/xbrl/yuho_sections/states_2026-11-16.json"
YS_READ_REL = "fixtures/xbrl/yuho_sections/read_types_2026-11-16.json"
YS_POP_REL = "fixtures/xbrl/yuho_sections/population_2026-11-16.json"
TSS_VM_REL = "fixtures/xbrl/tanshin_self/vm_types_2026-11-14.json"
TSS_SUB_REL = "fixtures/xbrl/tanshin_self/vm_types_subreading_2026-11-14.json"

#: 封 §1 の入力(# , path, sha256)。違えば止まる。門が封の表と 1 行ずつ照らす
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
)

PROFILE = "P33E"
FP_KEYS = PS.FP_KEYS
STATES = tuple(TS.STATES)
G_STATE, V_STATE = STATES[0], STATES[1]
SHORT = {G_STATE: u"G", V_STATE: u"V"}
GV = (u"G", u"V")

#: 封 §2-3 の手がかりの語の表(字で留める。門が封の表と 1 字ずつ照らす)
WORDS = collections.OrderedDict([
    (u"S", (u"セグメント", u"部門", u"分野")),
    (u"N", (u"単体", u"個別", u"提出会社")),
    (u"U", (u"うち", u"内訳")),
    (u"R", (u"国内", u"海外", u"日本", u"北米", u"米国", u"欧州", u"アジア", u"中国", u"地域")),
    (u"K", (u"子会社", u"関連会社"))])
BIZ = u"事業"
BIZ_AFTER = (u"は", u"では", u"において", u"におきまして", u"につきまして", u"について", u"の売上", u"セグメント", u"部門", u"分野")
BIZ_CLOSE = (u"]", u")", u"】", u"〕", u">", u"》", u"」")
HEAD_MAX = 40
HEAD_END = u"。"
NONCONS = u"NonConsolidated"
CLASS_ORDER = u"SNURKH"
STAGES = (1, 2, 3)
STAGE_NAMES = collections.OrderedDict((t, u"段 %d" % t) for t in STAGES)

POS_RE = re.compile(u"(?:△|▲|－|-|マイナス)?\\s*\\d")
SPAN_BEFORE = 30

#: 記録の行の欄(行 = 結んだ行 = state が G か V の数の claim)
ROW_COLUMNS = [u"便", u"本の #", u"文の種類か節", u"文の番号", u"位置", u"state", u"member が空", u"段 1 の当たりの類", u"段 2 の当たりの類", u"段 3 の当たりの類"]
(C_BATCH, C_BOOK, C_SIDE, C_SI, C_POS, C_STATE, C_EMPTY, C_H1, C_H2, C_H3) = range(10)
C_HIT = {1: C_H1, 2: C_H2, 3: C_H3}

BATCHES = (u"TSS", u"KAM", u"YS")
NO_SIDE = u"(文の種類なし)"                                  # TSS の単位の名前(記録の欄の名前に「文」の 1 字は使えない)
SIDE_ORDER = {u"TSS": (None,), u"KAM": tuple(KAM.SIDES), u"YS": tuple(YS.SECTIONS)}
READ_SETS = {u"KAM": KAM.READ_SETS, u"YS": YS.READ_SETS}
EXPECT_TSS_BOOKS = 400
EXPECT_KAM_BOOKS = 201

K_WIRE = u"配線の確認(封 §2-2。予測ではない。違えば止まる)"
K_ALL = u"結んだ行の全部(封 §2-5 の 1)"
K_LABEL = u"読みの札つきの行(封 §2-5 の 2)"
K_CLASS = u"当たった類ごとの数(封 §2-5 の 3)"
K_PRED = u"予測の判定に要る数(SC-1〜SC-7。当たり・外れは結果の文書で)"

STAGE_DEFS = collections.OrderedDict([
    (u"対象", u"結んだ行(state が GROUNDED か VALUE_MISMATCH の数の claim)のうち raw の claim の member の欄が空の行。member が入っている行はどの段でも止めない"),
    (u"前の字", u"その行の文の、頭から数の位置の手前まで"),
    (u"見出し", u"文の列の中で、長さが 40 字以下・「。」で終わらない・数の claim を 1 つも持たない文"),
    (u"段 1", u"前の字に S・N・U のどれかの語。N の語だけで当たった行は、その行の pointer の字のどれにも NonConsolidated が無いときだけ止める"),
    (u"段 2", u"段 1、または、その行の文より前で最も近い見出しに S の語"),
    (u"段 3", u"段 2、または、前の字に R・K の語、または、その行の文の全部に S・N・U の語(N のただし書きは同じ)")])

LIMITS = (
    u"engine は変えていない。止めた数は engine の外の後付けの規則の数で、engine の旗にしたときの数ではない(engine の中では止めたあとに別の枠へ結び直す道が在りうる。それは測らない)",
    u"読みの札は AI の席(司令塔)1 席が付けた。盲検でなく、人は読んでいない。この便は札の正しさを 1 つも確かめない。TSS の札は便 NRE の直しの前の engine の行に付けたもので、いまの engine で同じ state で引けた行だけを数える",
    u"TSS の G の行には札が無い。「正しい結びの減り」を札で言えるのは KAM と YS だけ",
    u"手がかりの語の表は司令塔が書いた。盲検でない。別の語の表なら数は変わる",
    u"止めた行が「止めて正しかった」かは札の在る行でしか言えない。止めたあとに正しい fact へ結び直せるかは測らない",
    u"材料は決算短信の概況の文(400 本)と有報の KAM・3 つの節(201 本)。ほかの書類には言えない",
    u"位置の欄は数の字の手前の空白・符号から始まることがある(engine の数の読みが符号と空白を数の一部に読むため)。前の字はその手前までで、空白を含まない",
    u"事業の形の「文の終わり」は、探す字(前の字・見出し・文の全部)の終わりを指すと決めた。前の字の終わりが「事業」の行の数は配線の欄に書いた",
    u"行は鍵・state・member が空か・段ごとの当たりの類だけで、文・値・要素名・枠の id・pointer の字・主語の語・会社名・証券コード・docID・金額は持たない")


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
def has_biz_form(text):
    u"""「事業」の直後が事業の形(BIZ_AFTER のどれか・閉じ括弧・字の終わり)の所が 1 つでも在る。"""
    i = text.find(BIZ)
    while i >= 0:
        rest = text[i + len(BIZ):]
        if rest == u"" or rest.startswith(BIZ_AFTER) or rest[:1] in BIZ_CLOSE:
            return True
        i = text.find(BIZ, i + 1)
    return False


def has_class(text, cls):
    u"""字の中に類 ``cls`` の語が在る(部分一致)。S は事業の形も数える。"""
    if any(w in text for w in WORDS[cls]):
        return True
    return cls == u"S" and has_biz_form(text)


def snu_hits(text, pointers):
    u"""字の中の S・N・U の当たり(類の並び)。N の語だけの当たりは pointer のどれかに NonConsolidated が在れば全部捨てる。"""
    raw = [c for c in u"SNU" if has_class(text, c)]
    if raw == [u"N"] and any(isinstance(p, str) and NONCONS in p for p in pointers):
        return []
    return raw


def fmt_hits(hits):
    return u"".join(c for c in CLASS_ORDER if c in hits)


def stage_hits(prefix, whole, heading, pointers):
    u"""(段 1, 段 2, 段 3 の当たりの類の字)。``heading`` は最も近い見出しの字(無ければ None)。"""
    h1 = set(snu_hits(prefix, pointers))
    h2 = set(h1)
    if heading is not None and has_class(heading, u"S"):
        h2.add(u"H")
    h3 = set(h2)
    h3.update(c for c in u"RK" if has_class(prefix, c))
    h3.update(snu_hits(whole, pointers))
    return fmt_hits(h1), fmt_hits(h2), fmt_hits(h3)


def is_heading(sentence):
    return len(sentence) <= HEAD_MAX and not sentence.endswith(HEAD_END)


def heading_indices(sentences, num_sentences):
    u"""見出しの文の番号の昇順。``num_sentences`` は数の claim を持つ文の番号の集まり。"""
    return [i for i, s in enumerate(sentences) if is_heading(s) and i not in num_sentences]


def nearest_heading(heads, si):
    u"""文の番号 ``si`` より前で最も近い見出しの番号(無ければ None)。"""
    best = None
    for h in heads:
        if h < si:
            best = h
        else:
            break
    return best


def number_start_kind(sentence, pos, span):
    u"""位置の確かめ。数の字で始まる(符号・空白をはさんでよい)・span がその位置の前後と合うなら、0(``pos`` の字が数字)か 1(符号・空白)。違えば None。"""
    if not isinstance(pos, int) or not 0 <= pos < len(sentence):
        return None
    if not POS_RE.match(sentence, pos):
        return None
    if span is not None:
        tail = span[min(pos, SPAN_BEFORE):]
        if not tail or sentence[pos:pos + len(tail)] != tail:
            return None
    return 0 if sentence[pos].isdigit() else 1


def unit_digest(pairs, sentences):
    u"""1 つの文(TSS は 1 本・KAM は文の種類・YS は節)の [(raw の claim, verify の claim)] と文の列 → 数えた結果(OrderedDict)。
    位置の確かめに 1 行でも違えば止める。行は結んだ行だけ。"""
    num_sentences = set(r["sentence"] for r, _c in pairs)
    heads = heading_indices(sentences, num_sentences)
    triples, rows = [], []
    counts = collections.Counter()
    for r, c in pairs:
        si, pos = r["sentence"], r["pos"]
        if not isinstance(si, int) or not 0 <= si < len(sentences):
            raise Stop(u"**数の claim の文の番号が文の列の外。止める**")
        s = sentences[si]
        kind = number_start_kind(s, pos, r.get("span"))
        if kind is None:
            raise Stop(u"**数の claim の位置の欄が「文の中の字の位置」でない(数の字で始まらない・span と合わない)。止めて司令塔に返す**")
        counts[u"位置: 数字から" if kind == 0 else u"位置: 符号か空白から"] += 1
        counts[u"member の欄が在る" if u"member" in r else u"member の欄が無い"] += 1
        state = c["state"]
        triples.append((si, pos, state))
        if state not in SHORT:
            continue
        empty = not r.get(u"member")
        if empty:
            prefix = s[:pos]
            if prefix.endswith(BIZ):
                counts[u"前の字の終わりが「事業」"] += 1
            nh = nearest_heading(heads, si)
            h1, h2, h3 = stage_hits(prefix, s, sentences[nh] if nh is not None else None, c.get("pointers") or [])
        else:
            h1 = h2 = h3 = u""
        rows.append([si, pos, SHORT[state], bool(empty), h1, h2, h3])
    rows.sort(key=lambda x: (x[0], x[1]))
    return od([(u"cut", True), (u"triples", triples), (u"rows", rows), (u"counts", dict(counts)), (u"claims", len(pairs))])


def empty_digest():
    return od([(u"cut", False), (u"triples", []), (u"rows", []), (u"counts", {}), (u"claims", 0)])


# ======================================================================================================
# 1 本の job
def read_bytes(path, sha, n):
    if not os.path.exists(path):
        raise Stop(u"**材料の ZIP が置き場に無い(# %d)。止める**" % n)
    with io.open(path, "rb") as fh:
        zb = fh.read()
    if ST.sha256_bytes(zb) != sha:
        raise Stop(u"**材料の ZIP の sha256 が封の表と違う(# %d)。止める**" % n)
    return zb


def sentences_of(zbytes):
    return TS.RUN.sentence_list(zbytes, V.PROFILES[PROFILE])


def tss_units(zb):
    text = TSS.cut(zb)[0]
    if text is None:
        return [(None, empty_digest())]
    wrapped = TSS.wrap(zb, text)[0]
    return [(None, unit_digest(PS.claims_of(wrapped), sentences_of(wrapped)))]


def kam_units(zb):
    out = []
    for side in KAM.SIDES:
        text = KAM.cut_kam(zb, side)[0]
        if text is None:
            out.append((side, empty_digest()))
            continue
        zm = KAM.PR.build_modified_zip(zb, text)[0]
        out.append((side, unit_digest(PS.claims_of(zm), sentences_of(zm))))
    return out


def ys_units(zb):
    out = []
    for section in YS.SECTIONS:
        text = YS.cut_section(zb, section)[0]
        if text is None:
            out.append((section, empty_digest()))
            continue
        zm = YS.PR.build_modified_zip(zb, text)[0]
        out.append((section, unit_digest(PS.claims_of(zm), sentences_of(zm))))
    return out


UNITS_OF = {u"TSS": tss_units, u"KAM": kam_units, u"YS": ys_units}


def book_job(args):
    u"""1 本: (便, 本の #, 群, sha256, ZIP の path) → {便, 本の #, units: [(文の種類か節, 数えた結果)]}。"""
    batch, n, _grp, sha, path = args
    zb = read_bytes(path, sha, n)
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
    return dict(((r[C_BATCH], r[C_BOOK], r[C_SIDE], r[C_SI], r[C_POS]), r) for r in rows)


def frac3(n, d):
    return rate(n, d)


def stage_cells(rows):
    u"""結んだ行の集まり → {結んだ行, member が空の行, 止めた行: {段 1..3}}。"""
    return od([(u"結んだ行", len(rows)), (u"member が空の行", sum(1 for r in rows if r[C_EMPTY])),
               (u"止めた行", od((STAGE_NAMES[t], sum(1 for r in rows if stopped(r, t))) for t in STAGES))])


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
def tss_key(t, d):
    u"""TSS の型・細目 → 便 AT の写しの表の字(細目を持つ型は細目の字。ケ は細目によらず ケ)。"""
    if t in AT.DETAIL_TYPES:
        if d is None:
            raise Stop(u"**細目を持つはずの型の行に細目が無い。止める**")
        return u"ケ" if t == u"ケ" else d
    return t


def tss_labels(vm, sub):
    u"""TSS の 2 つの記録(型・細目)→ [(本の #, 文の番号, 位置, 表の字)]。形が決めと違えば止める。"""
    if vm.get(u"行の欄") != AT.VM_FIELDS or sub.get(u"行の欄") != AT.SUB_FIELDS:
        raise Stop(u"**TSS の行の欄が決めと違う。止める**")
    rows = vm[u"行"]
    ids = [r[0] for r in rows]
    if len(set(ids)) != len(ids) or len(rows) != vm[u"標本の規則"][u"標本の数"]:
        raise Stop(u"**TSS の標本の番号が重なるか標本の数が行と違う。止める**")
    type_of = {}
    for r in rows:
        if len(r) != len(AT.VM_FIELDS) or r[4] not in AT.V_TYPES or not isinstance(r[1], int):
            raise Stop(u"**TSS の標本の行の形か型の字が決めの外。止める**")
        type_of[r[0]] = r[4]
    detail_of = {}
    for r in sub[u"行"]:
        if len(r) != len(AT.SUB_FIELDS) or r[0] not in type_of or r[0] in detail_of or r[1] != type_of[r[0]] or r[1] not in AT.DETAIL_TYPES \
                or r[2] not in sub[u"細目の字"] or not r[2].startswith(r[1]):
            raise Stop(u"**TSS の細目の行の形が決めと違う。止める**")
        detail_of[r[0]] = r[2]
    if set(i for i, t in type_of.items() if t in AT.DETAIL_TYPES) != set(detail_of):
        raise Stop(u"**細目を持つはずの型の行に細目が無い(または余る)。止める**")
    return [(r[1], r[2], r[3], tss_key(r[4], detail_of.get(r[0]))) for r in rows]


def label_row(batch, n, side, si, pos, state, key, diff, lookup):
    u"""札つきの行 1 つ。V の札は属性の種別(内・外・除く)と先の字も持つ。"""
    kind, name = (lookup[key] if state == u"V" else (None, None))
    if state == u"V" and key not in lookup:
        raise Stop(u"**写しの表に無い型・細目の字。止める**")
    return od([(u"便", batch), (u"#", n), (u"側", side), (u"si", si), (u"pos", pos), (u"state", state), (u"型", key), (u"違うもの", diff), (u"種別", kind), (u"先", name)])


def build_labels(recs):
    u"""入力の記録 → 札つきの行(list of OrderedDict)。KAM・YS は便 AT の検査(記録の集計の欄と行の数え直し)を通す。"""
    out = []
    for batch, key in ((u"KAM", u"kam_read"), (u"YS", u"ys_read")):
        by = AT.read_ys_kam_rows(recs[key], batch)
        lookup = AT.table_lookup(batch)
        for g, grows in by.items():
            if g not in READ_SETS[batch]:
                raise Stop(u"**読みの組の名前が決めの外。止める**")
            side = READ_SETS[batch][g][0]
            state = u"V" if g.startswith(u"V") else u"G"
            for r in grows:
                out.append(label_row(batch, r[1], side, r[2], r[3], state, r[4], r[5], lookup))
    lookup = AT.table_lookup(u"TSS")
    for n, si, pos, key in tss_labels(recs[u"tss_vm"], recs[u"tss_sub"]):
        out.append(label_row(u"TSS", n, None, si, pos, u"V", key, None, lookup))
    return out


def label_key(lab):
    return (lab[u"便"], lab[u"#"], lab[u"側"], lab[u"si"], lab[u"pos"])


def match(labels, index):
    u"""札つきの行 → [(札, 引けた行 or None, 引けなかった理由 or None)]。同じ鍵で札の state(V か G)と同じ state の行だけ引けた。"""
    out = []
    for lab in labels:
        row = index.get(label_key(lab))
        if row is None:
            out.append((lab, None, u"行が無い"))
        elif row[C_STATE] != lab[u"state"]:
            out.append((lab, None, u"state が違う"))
        else:
            out.append((lab, row, None))
    return out


def cell(matched):
    u"""[(札, 行 or None, 理由)] → 札の行・引けた行(分母)・引けなかった行(理由別)・止めた行(段別)。"""
    got = [m[1] for m in matched if m[1] is not None]
    why = collections.Counter(m[2] for m in matched if m[1] is None)
    return od([(u"札の行", len(matched)), (u"引けた行(分母)", len(got)), (u"引けなかった行", len(matched) - len(got)),
               (u"引けなかった理由", od([(u"行が無い", why.get(u"行が無い", 0)), (u"state が違う", why.get(u"state が違う", 0))])),
               (u"止めた行", od((STAGE_NAMES[t], sum(1 for r in got if stopped(r, t))) for t in STAGES))])


def cat_name(lab):
    kind, name = lab[u"種別"], lab[u"先"]
    if kind == AT.KIND_IN:
        return name
    if kind == AT.KIND_OUT:
        return u"外(%s)" % name
    return AT.EXCLUDE


def is_range(lab):
    return lab[u"種別"] == AT.KIND_IN and lab[u"先"] == u"範囲"


def is_drop(lab):
    return lab[u"種別"] == AT.KIND_DROP


def v_split(ms):
    u"""V の札の [(札, 行, 理由)] → (範囲, 範囲でない, 分母から除く札)。"""
    rng = [m for m in ms if is_range(m[0])]
    non = [m for m in ms if not is_range(m[0]) and not is_drop(m[0])]
    drop = [m for m in ms if is_drop(m[0])]
    return rng, non, drop


def v_tally(vms_by_batch):
    u"""V の札。便ごと・3 便の合計。属性ごと(1 株あたりは作りで 0)・範囲 / 範囲でない / 分母から除く札。"""
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
        rng, non, drop = v_split(ms)
        out[batch] = od([
            (u"全体", cell(ms)),
            (u"属性ごと", od((nm, cell([m for m in ms if cat_name(m[0]) == nm])) for nm in names)),
            (u"1 株あたりについて", u"この属性に写る型は表に無い。0 は作りで、測った 0 ではない"),
            (u"範囲", cell(rng)), (u"範囲でない(分母から除く札は除く)", cell(non)), (u"分母から除く札", cell(drop))])
    return out


def g_tally(gms_by_batch):
    u"""G の札(KAM・YS)。a・b・c ごと・b は違うものごと・「範囲(字のとおり)」と「範囲 + 側(便 AT の写し)」。便ごと・合計。"""
    out = od()
    total = []
    for batch in (u"KAM", u"YS", u"合計"):
        ms = total if batch == u"合計" else gms_by_batch[batch]
        if batch != u"合計":
            total = total + gms_by_batch[batch]
        b = [m for m in ms if m[0][u"型"] == u"b"]
        out[batch] = od([
            (u"全体", cell(ms)),
            (u"型ごと", od((t, cell([m for m in ms if m[0][u"型"] == t])) for t in AT.G_TYPES)),
            (u"b の違うものごと", od((d, cell([m for m in b if m[0][u"違うもの"] == d])) for d in AT.DIFFS)),
            (u"b の違うものが範囲(字のとおり)", cell([m for m in b if m[0][u"違うもの"] == u"範囲"])),
            (u"b の違うものが範囲か側(便 AT の写し)", cell([m for m in b if AT.DIFF_TO_ATTR[m[0][u"違うもの"]] == u"範囲"]))])
    return out


def split_labels(labels, index):
    u"""札つきの行 → (V の [便 → matched]・G の [便 → matched])。"""
    vms = dict((b, []) for b in BATCHES)
    gms = dict((b, []) for b in (u"KAM", u"YS"))
    for lab, row, why in match(labels, index):
        if lab[u"state"] == u"V":
            vms[lab[u"便"]].append((lab, row, why))
        else:
            gms[lab[u"便"]].append((lab, row, why))
    return vms, gms


def tally_label(labels, rows):
    vms, gms = split_labels(labels, index_rows(rows))
    return od([(u"V の札", v_tally(vms)), (u"G の札(KAM・YS)", g_tally(gms))])


# ======================================================================================================
# 予測の判定に要る数
def stage_fracs(num_den_rows, den):
    u"""止めた行の数(段別)と分母 → {段 1..3: {分子, 分母, 率}}。"""
    return od((STAGE_NAMES[t], frac3(num_den_rows[t], den)) for t in STAGES)


def ms_counts(ms):
    got = [m[1] for m in ms if m[1] is not None]
    return len(got), dict((t, sum(1 for r in got if stopped(r, t))) for t in STAGES)


def fr(ms):
    den, cnt = ms_counts(ms)
    return stage_fracs(cnt, den)


def point_diff_stage(a_ms, b_ms, t):
    u"""(a の率 − b の率)× 100 を小数 2 桁の字で(RT の ``point_diff``。分母 0 があれば「分母 0」)。"""
    da, ca = ms_counts(a_ms)
    db, cb = ms_counts(b_ms)
    return RT.point_diff(cb[t], db, ca[t], da)


def predictions(rows, labels):
    vms, gms = split_labels(labels, index_rows(rows))
    v_all = [m for b in BATCHES for m in vms[b]]
    rng_b = dict((b, v_split(vms[b])[0]) for b in BATCHES)
    non_b = dict((b, v_split(vms[b])[1]) for b in BATCHES)
    rng = [m for b in BATCHES for m in rng_b[b]]
    non = [m for b in BATCHES for m in non_b[b]]
    g_all = [m for b in (u"KAM", u"YS") for m in gms[b]]
    a_b = dict((b, [m for m in gms[b] if m[0][u"型"] == u"a"]) for b in (u"KAM", u"YS"))
    a_all = [m for b in (u"KAM", u"YS") for m in a_b[b]]
    b_rng = [m for m in g_all if m[0][u"型"] == u"b" and m[0][u"違うもの"] == u"範囲"]
    b_rng_side = [m for m in g_all if m[0][u"型"] == u"b" and AT.DIFF_TO_ATTR[m[0][u"違うもの"]] == u"範囲"]
    tss = [r for r in rows if r[C_BATCH] == u"TSS"]
    tss_g = [r for r in tss if r[C_STATE] == u"G"]
    tss_v = [r for r in tss if r[C_STATE] == u"V"]

    def rows_fr(rs):
        return stage_fracs(dict((t, sum(1 for r in rs if stopped(r, t))) for t in STAGES), len(rs))

    out = od()
    out[u"SC-1 段 2 で「範囲」の札の V の行(3 便の合計)のうち止めた行 / 引けた行(段 1・3 も並べる)"] = od([
        (u"3 便の合計", fr(rng))] + [(b, fr(rng_b[b])) for b in BATCHES])
    out[u"SC-2 段 1 で札 a の G の行(KAM と YS の合計)のうち止めた行 / 引けた行(段 2・3 も並べる)"] = od([
        (u"KAM と YS の合計", fr(a_all))] + [(b, fr(a_b[b])) for b in (u"KAM", u"YS")])
    c_all = ms_counts(a_all)
    out[u"SC-3 札 a の G の行の止める数(段 1・段 3。分母は引けた行)"] = od([
        (u"引けた行", c_all[0]), (u"段 1 の止めた行", c_all[1][1]), (u"段 3 の止めた行", c_all[1][3]),
        (u"段 1 の率", frac3(c_all[1][1], c_all[0])), (u"段 3 の率", frac3(c_all[1][3], c_all[0]))])
    out[u"SC-4a TSS の G の全部の行のうち段 2 で止めた行 / TSS の G の行(段 1・3 も並べる)"] = rows_fr(tss_g)
    out[u"SC-4b TSS の V の全部の行のうち段 2 で止めた行 / TSS の V の行(段 1・3 も並べる)"] = rows_fr(tss_v)
    out[u"SC-5 段 2 で「範囲でない」札の V の行(3 便の合計)の止めた行 / 引けた行(段 1・3 も並べる)"] = od([
        (u"3 便の合計", fr(non))] + [(b, fr(non_b[b])) for b in BATCHES])
    out[u"SC-5 率の差(ポイント。範囲の率 − 範囲でない率。小数 2 桁の字)"] = od((STAGE_NAMES[t], point_diff_stage(rng, non, t)) for t in STAGES)
    out[u"SC-6 段ごとの「範囲の札の V の行」の止めた行 / 引けた行 と「札 a の G の行」の止めた行 / 引けた行"] = od(
        (STAGE_NAMES[t], od([(u"範囲の札の V の行", fr(rng)[STAGE_NAMES[t]]), (u"札 a の G の行", fr(a_all)[STAGE_NAMES[t]])])) for t in STAGES)
    out[u"SC-7 札 b のうち「違うもの」が範囲の行(字のとおり。KAM と YS の合計)の止めた行 / 引けた行(段 1・2・3)"] = fr(b_rng)
    out[u"SC-7 参考(違うものが範囲か側。便 AT の写し)"] = fr(b_rng_side)
    out[u"分母の確かめ(V の札 3 便の合計・G の札 KAM と YS の合計・札の行の数)"] = od([
        (u"V の札の行(札)", len(v_all)), (u"V の札の行(引けた)", ms_counts(v_all)[0]), (u"G の札の行(札)", len(g_all)), (u"G の札の行(引けた)", ms_counts(g_all)[0])])
    return out


# ======================================================================================================
# 配線の確認(封 §2-2)
def triples_of(books, batch):
    out = {}
    for b in books:
        if b[u"便"] != batch:
            continue
        for side, u in b[u"units"]:
            for si, pos, st in u[u"triples"]:
                out[(b[u"#"], side, si, pos)] = st
    return out


def rt_state_counts(rt_rec):
    u"""便 RT の記録の段 1「集計(後)」の群ごとの 4 state の合計。"""
    c = collections.Counter()
    groups = rt_rec[u"段 1(第 1 便。400 本の判定)"][u"集計(後)"][u"群"]
    for g in groups.values():
        for s, k in g[u"4 state"].items():
            c[s] += k
    return od((s, c.get(s, 0)) for s in STATES)


def wire_tss(books, rt_rec, full):
    u"""TSS の行の数と state ごとの数が便 RT の記録と同じ(400 本のときだけ)。"""
    tr = triples_of(books, u"TSS")
    c = collections.Counter(tr.values())
    now = od((s, c.get(s, 0)) for s in STATES)
    want_rows = rt_rec[u"段 1(第 1 便。400 本の判定)"][u"行(後)"]
    want = rt_state_counts(rt_rec)
    if full and (len(tr) != want_rows or now != want):
        raise Stop(u"**TSS の引き直しの行の数か state ごとの数が便 RT の記録の段 1(後)と違う。止める**")
    return od([(u"TSS の引き直しの行", len(tr)), (u"TSS の state ごとの行", now), (u"便 RT の記録の段 1(後)の行", want_rows),
               (u"便 RT の記録の段 1(後)の state ごとの行", want), (u"400 本の確かめを掛けた", bool(full))])


def prev_triples(prev_rec, sides, ns):
    out, cut = {}, {}
    for b in prev_rec[u"本"]:
        if b[u"#"] not in ns:
            continue
        for side in sides:
            cut[(b[u"#"], side)] = (b[side][u"切り出し"] == KAM.CUT_OK)
            for r in b[side][u"行"]:
                out[(b[u"#"], side, r[0], r[1])] = r[2]
    return out, cut


def compare_prev(books, batch, prev_rec, ns):
    u"""KAM・YS の引き直しの行を前の記録の行と (本の #, 文の種類か節, 文の番号, 位置) で突き合わせる。同じ state・state が違う・今にだけ・前にだけ。止めない。"""
    sides = SIDE_ORDER[batch]
    now = triples_of(books, batch)
    prev, prev_cut = prev_triples(prev_rec, sides, ns)
    now_cut = {}
    for b in books:
        if b[u"便"] == batch:
            for side, u in b[u"units"]:
                now_cut[(b[u"#"], side)] = u[u"cut"]

    def part(side):
        ks_n = [k for k in now if side is None or k[1] == side]
        ks_p = [k for k in prev if side is None or k[1] == side]
        same = sum(1 for k in ks_n if k in prev and prev[k] == now[k])
        diff = sum(1 for k in ks_n if k in prev and prev[k] != now[k])
        cut_diff = sum(1 for k in now_cut if (side is None or k[1] == side) and k in prev_cut and prev_cut[k] != now_cut[k])
        return od([(u"同じ鍵で同じ state の行", same), (u"同じ鍵で state が違う行", diff),
                   (u"今の引き直しにだけ在る行", sum(1 for k in ks_n if k not in prev)), (u"前の記録にだけ在る行", sum(1 for k in ks_p if k not in now)),
                   (u"前の記録の行", len(ks_p)), (u"今の引き直しの行", len(ks_n)), (u"切り出しの成否が前と違う本 × 側", cut_diff)])
    out = od([(u"全体", part(None))])
    out[u"文の種類別" if batch == u"KAM" else u"節別"] = od((side, part(side)) for side in sides)
    return out


def wiring_counts(books):
    u"""位置の確かめ・member の欄・「事業」で終わる前の字の数(便ごと)。"""
    out = od()
    for batch in BATCHES:
        c = collections.Counter()
        for b in books:
            if b[u"便"] == batch:
                for _side, u in b[u"units"]:
                    c.update(u[u"counts"])
        out[batch] = od([
            (u"位置を確かめた数の claim(state を問わない)", c.get(u"位置: 数字から", 0) + c.get(u"位置: 符号か空白から", 0)),
            (u"うち pos の字が数字", c.get(u"位置: 数字から", 0)), (u"うち pos の字が符号か空白", c.get(u"位置: 符号か空白から", 0)),
            (u"raw の claim に member の欄が在る", c.get(u"member の欄が在る", 0)), (u"raw の claim に member の欄が無い", c.get(u"member の欄が無い", 0)),
            (u"前の字の終わりが「事業」の結んだ行(member が空)", c.get(u"前の字の終わりが「事業」", 0))])
    return out


def cut_counts(books):
    out = od()
    for batch in BATCHES:
        per = od()
        for side in SIDE_ORDER[batch]:
            us = [u for b in books if b[u"便"] == batch for s, u in b[u"units"] if s == side]
            per[side if side is not None else NO_SIDE] = od([(u"本", len(us)), (u"切れた", sum(1 for u in us if u[u"cut"])), (u"切れない", sum(1 for u in us if not u[u"cut"])),
                                                         (u"数の claim", sum(u[u"claims"] for u in us))])
        out[batch] = per
    return out


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
    return {u"rt": load_json(os.path.join(root, RT_RECORD_REL)),
            u"kam_states": load_json(os.path.join(root, KAM_STATES_REL)), u"ys_states": load_json(os.path.join(root, YS_STATES_REL)),
            u"kam_read": load_json(os.path.join(root, KAM_READ_REL)), u"ys_read": load_json(os.path.join(root, YS_READ_REL)),
            u"kam_pop": load_json(os.path.join(root, KAM_POP_REL)), u"ys_pop": load_json(os.path.join(root, YS_POP_REL)),
            u"tss_vm": load_json(os.path.join(root, TSS_VM_REL)), u"tss_sub": load_json(os.path.join(root, TSS_SUB_REL))}


def engine_fp(rt_rec):
    u"""今の engine の指紋(4 欄)。便 RT の記録の「今」と同じでなければ止める。"""
    fp = VD.engine_fingerprint()
    now = od((k, fp[k]) for k in FP_KEYS)
    want = od((k, rt_rec[u"engine の指紋(今。便 NRE の記録の直した後と同じ)"][k]) for k in FP_KEYS)
    if now != want:
        raise Stop(u"**engine の指紋が便 RT の記録の「今」と違う。止める**")
    return now


def scan_material(base, pop):
    return KAM.scan_material(base, pop)


def folder_snapshots(base):
    return KAM.folder_snapshots(base)


def subset_shape(pop):
    return RT.subset_shape(pop)


def check_pop_record(pop, rec, label):
    u"""封の表から読んだ母集団が、その便の母集団の記録の行(#, 群, sha256)と同じ。"""
    if [list(r[:3]) for r in rec[u"行"]] != [[r[0], r[1], r[2]] for r in pop]:
        raise Stop(u"**%s の母集団の表が母集団の記録と違う。止める**" % label)


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
        check_pop_record(kam_pop, recs[u"kam_pop"], u"KAM")
        check_pop_record(ys_pop, recs[u"ys_pop"], u"YS")
    else:
        tss_pop, kam_pop, ys_pop = populations[u"TSS"], populations[u"KAM"], populations[u"YS"]
    shape = subset_shape(tss_pop)
    full = shape is None
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
    wire = od()
    wire[u"TSS の行(便 RT の記録との確かめ)"] = wire_tss(books, recs[u"rt"], full)
    wire[u"KAM の行(前の記録との突き合わせ。止めない)"] = compare_prev(books, u"KAM", recs[u"kam_states"], set(r[0] for r in kam_pop))
    wire[u"YS の行(前の記録との突き合わせ。止めない)"] = compare_prev(books, u"YS", recs[u"ys_states"], set(r[0] for r in ys_pop))
    wire[u"位置の確かめ・member の欄・「事業」で終わる前の字(便ごと)"] = wiring_counts(books)
    wire[u"本の数"] = od([(u"TSS", len(tss_pop)), (u"KAM", len(kam_pop)), (u"YS", len(ys_pop))])
    rows = link_rows(books)
    labels = build_labels(recs)
    rec = od()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"SC(文は一部分を言うのに全体の fact に結んだ行を文の字で止める後付けの規則 ― 段 1・2・3)(0 USD・通信なし・engine は 0 行)"
    rec[u"この script の sha256"] = ST.sha256_file(os.path.abspath(__file__))
    rec[u"入力"] = inputs
    rec[u"engine の指紋(今。便 RT の記録の今と同じ)"] = fp
    rec[u"profile"] = PROFILE
    rec[u"材料"] = od([(u"TSS の置き場", ST.display_path(mat) if prod else u"使い捨ての置き場(本番の folder ではない)"),
                      (u"KAM・YS の置き場", u"~/.cache/audit-core の 3 つの folder(甲・乙・丙。名前は書かない)"),
                      (u"表と一致した ZIP", od([(u"TSS", len(tss_pop)), (u"KAM", len(kam_pop)), (u"YS", len(ys_pop))]))])
    rec[u"手がかりの語の表"] = od([(c, list(w)) for c, w in WORDS.items()])
    rec[u"事業の形"] = od([(u"基準の字", BIZ), (u"直後", list(BIZ_AFTER) + list(BIZ_CLOSE) + [u"文の終わり(探す字の終わり)"])])
    rec[u"段の定義"] = STAGE_DEFS
    rec[u"切り出し"] = cut_counts(books)
    rec[K_WIRE] = wire
    rec[K_ALL] = tally_all(rows)
    rec[K_LABEL] = tally_label(labels, rows)
    rec[K_CLASS] = tally_class(rows)
    rec[K_PRED] = predictions(rows, labels)
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
