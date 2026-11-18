# -*- coding: utf-8 -*-
u"""封 docs/XBRL_SUMMARY_ENGINE_SEAL_2026-11-18.md(SE ― サマリーを engine に渡したときに動く行と、engine の語彙が予想の枠の fact に届くか)の測定。
**0 USD・通信なし・鍵は読まない・LLM は呼ばない。engine(``core/``・``adapters/``)は 1 行も変えない。**材料は TSS の置き場(~/.cache/audit-core/tanshin-self-2026-11-14/)の ZIP 400 本を読むだけ。

    python3 measure/xbrl_summary_engine_2026-11-18.py run --out PATH [--material DIR] [--procs N]      # 段 1・段 2 を数える → fixtures/xbrl/summary_engine/states_2026-11-18.json
    python3 measure/xbrl_summary_engine_2026-11-18.py run --check [--material DIR] [--procs N]         # 書かずに作り直し、在る記録と比べる(時間の欄は除く)

実装の注(封 §2 が 1 通りに決めていない細部の決め。実装より先に決め、結果を見て変えない。報告にも書く):
- 前の便の script は ``load_module`` の形(読み込みの前に居た名前を元の object へ戻す)で読み、関数を **呼ぶ**(写さない)。RT = 便 RT の script(``dumps``・``rate``・中の ``TSS`` の ``judge_book``)・PS = 便 PS の script。
- §2-2 の第 1 の確認の「便 RT の段 1 の後」: 便 RT の記録は段 1 の行(reason)を持たない形なので、便 RT の段 1 が呼ぶ ``judge_book``(RT の中の TSS のもの)を本ごとに呼んで作った行と、
  ``PS.claims_of`` の「前」の (文の番号, 位置, state, reason) の並びが同じことを見る。加えて全体では「前」の行の数が便 RT の記録の段 1 の「行(後)」と同じこと(400 本のときだけ)。違えば止める。
- 「前」の ZIP の member を写すときも info は ``TSS._info(名前)``(``wrap`` と同じ info)。「後」にサマリーの名前が既に在れば止める。
- 段 1 の「変わった行」= state が変わった行。「変わった行を 1 行でも持つ本」は 2 つ数える(state が変わった行を持つ本・前後のどこかの欄(state・reason・pointer・前にだけ・後にだけ)が違う行を持つ本)。
  「前は GROUNDED で後は GROUNDED でない行」は両方に在る行の数と、前は GROUNDED で後に無い行の数を別の欄で持つ(足さない)。分母は「前」の行の数(§3)。
- 段 1 の群別・前の state 別: 前の state 別は、両方に在る行の動きと前にだけ在る行の数を前の state で割る(後にだけ在る行は前の state が無いので別の欄)。
- 段 2 の F は、各 fact を ``PS.is_forecast_context`` と ``PS.split_facts`` と同じ除く条件(単位なし・値 0)で自分で選び、``PS.split_facts`` の F の個数と違えば止める。名前は局所名(``:`` の後ろ)で持つ(記録には書かない)。
- 完全一致の条件は ``instance.facts_for`` の条件の写し(局所名が要素名・要素名 + SummaryOfBusinessResults・Income を IncomeLoss に替えた要素名 + SummaryOfBusinessResults)。
  部分一致は要素名の小文字が局所名の小文字に含まれる。完全一致が 1 つでも在れば部分一致は見ない。試験が ``facts_for`` と同じ答えを返すことを縛る。
- 札 3・4 の副(F のどれかに値が合うか)と札 5 の副(完全一致か部分一致か)は行の欄として持つ。副の欄は札に関係なく全部の行に付ける(札 1・2 の行は値が合う = 偽)。
- 別の本は ``PS.other_books`` の輪(読みごとではなく 1 つ。サマリーは「そのまま」だけ)。対照の札は、自分の本の主語・語彙のまま F だけを別の本のものに替えて付ける。
- 読みの軸との重ね: 90 行(甲組・乙組)の鍵が段 2 の P の行に引けなかった数を数える。SE-7 の分母は 90(read_types の甲組・乙組の行数)・引けた行数も別に持つ。
- 記録は文・値・要素名・主語の語・枠の id・会社名・証券コード・docID・金額を持たない。数・鍵(本の #, 文の番号, 位置)・札だけ。時間(秒)以外は 2 回走らせて byte で同じ。
"""
from __future__ import print_function

import argparse
import collections
import importlib.util
import io
import json
import os
import sys
import time
import zipfile

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


RT = load_module("xbrl_tss_retake_2026-11-18.py", "tss_retake_for_summary_engine")         # 便 RT(中に PS・TSS)
PS = load_module("xbrl_plan_source_2026-11-17.py", "plan_source_for_summary_engine")       # 便 PS
TSS = PS.TSS
ST = TSS.ST
TS = TSS.TS
Stop = ST.Stop
I = PS.I
V = PS.V
VD = PS.VD

SEAL_REL = "docs/XBRL_SUMMARY_ENGINE_SEAL_2026-11-18.md"
SEAL_COMMIT = "fabd87ba"
SCRIPT_REL = "measure/xbrl_summary_engine_2026-11-18.py"
REC_DIR_REL = "fixtures/xbrl/summary_engine"
RECORD_REL = REC_DIR_REL + "/states_2026-11-18.json"
RT_RECORD_REL = "fixtures/xbrl/tss_retake/retake_2026-11-18.json"
READ_TYPES_REL = "fixtures/xbrl/plan_source/read_types_2026-11-17.json"

#: 封 §1 の入力(# , path, sha256)。違えば止まる。門が封の表と 1 行ずつ照らす
INPUTS = (
    (1, "fixtures/xbrl/tss_retake/retake_2026-11-18.json", "34845f1b3772993aebc0a48d1cec0f6ee5889f9f66843a88f94e572392263cd7"),
    (2, "fixtures/xbrl/plan_source/read_types_2026-11-17.json", "c244d1bf51e7867e1772f98bd6d4c0085fa816faf1ec09f7855050aa99fe5e56"),
    (3, "measure/xbrl_plan_source_2026-11-17.py", "0617d75a98e9aca390426b2751bed5ae40a8aa8759b3e80bffab163e1abeb8ea"),
    (4, "measure/xbrl_tanshin_self_2026-11-14.py", "fa603d1c2dbfdee7c3ad4197ab9c4a9f1428419ada57293f346418bc0997aeb6"),
    (5, "measure/xbrl_tss_retake_2026-11-18.py", "4d1c4276f67f2fd5551ba0372b2a09c07a2ee4c493b09942e3f360ee35e5b82e"),
    (6, "adapters/xbrl/recipes.py", "346adb0d586e3af233b381f721c3512eea02809c287e02aa948bb0d04031e403"),
    (7, "adapters/xbrl/instance.py", "1b8c00f86eafe765ce44be9ee93cc9ff7a492bd119074e9aa8f49e13e4970cd8"),
    (8, "adapters/xbrl/vocabulary.py", "369891933a5876c4a942e59b85b500d7fa2aa826f8b0c95e2b1c905623b3806c"),
    (9, "adapters/xbrl/extract.py", "a61da3fc3c336e80a214a5fc71978d9ce63f52b4eec5a763e91f434c2ef06d05"),
)

PROFILE = "P33E"
REASON_P = "target_or_plan"
EXPECT_P = 794
EXPECT_READ_ROWS = 90
FP_KEYS = PS.FP_KEYS
STATES = tuple(TS.STATES)
G = STATES[0]
GROUPS = PS.GROUPS
READ_LITERAL, READ_FAMILY = PS.READING_LITERAL, PS.READING_FAMILY
READINGS = (READ_LITERAL, READ_FAMILY)
SUMMARY_NAME = PS.SUMMARY_MEMBER

#: 札(封 §2-4。上から順に 1 つだけ)
L_NA, L_FEMPTY, L_NOSUBJ, L_OUTVOCAB, L_BOTH, L_VALONLY, L_NAMEONLY, L_NEITHER = (
    u"当てない", u"F が空", u"主語なし", u"語彙の外", u"両方", u"値だけ", u"名前だけ", u"どちらも無し")
LABELS = (L_NA, L_FEMPTY, L_NOSUBJ, L_OUTVOCAB, L_BOTH, L_VALONLY, L_NAMEONLY, L_NEITHER)
REACH_EXACT, REACH_LOOSE = u"完全一致", u"部分一致"

K_RT = u"配線の確認(封 §2-2。予測ではない。違えば止まる)"
K_S1 = u"段 1(サマリーを足したときに動く行)"
K_S2 = u"段 2(engine の語彙は予想の枠の fact に届くか)"
K_PRED = u"予測の判定に要る数(SE-1〜SE-7。当たり・外れは結果の文書で)"
ROW_COLUMNS_S1 = [u"本の #", u"文の番号", u"位置", u"前の state", u"後の state", u"前の reason", u"後の reason"]
ROW_COLUMNS_S2 = [u"本の #", u"文の番号", u"位置", u"群",
                  u"字のとおり: 札", u"字のとおり: F のどれかに値が合う", u"字のとおり: 届き方", u"字のとおり: 札(他)",
                  u"円の族: 札", u"円の族: F のどれかに値が合う", u"円の族: 届き方", u"円の族: 札(他)"]

LIMITS = (
    u"engine は変えていない。「両方」は「名前の語彙が届き、値も合う fact がサマリーの予想の枠に在る」ことで、engine が結べることではない。期・範囲(連結か単体か)・幅の上下は段 2 で見ていない",
    u"段 1 は「サマリーの member を足しただけ」の測定で、engine に予想の枠を読ませる測定ではない",
    u"語彙は手書きの P33E の主語の語だけ。engine が label で置き換えた後の語彙は見ていない",
    u"封じる前に見たのは 1 本だけ。予測の幅はその 1 本と前の便の記録からの見立て",
    u"材料は TSS の 400 本(決算短信)。ほかの書類には言えない。AI の席の読みは付けていない(読みの軸の 90 行は前の便の読みの鍵だけを引く。読みの字は引かない)",
    u"行は数・鍵(本の #, 文の番号, 位置)・札だけで、文・値・要素名・主語の語・枠の id・会社名・証券コード・docID・金額は持たない")


def rate(n, d):
    return RT.rate(n, d)


def load_json(p):
    return TSS.load_json(p)


# ======================================================================================================
# 段 2 の部品(純粋な関数。試験が作り物の入力で走らせる)
def subject_elems(subject, subjects=None):
    u"""主語の語 → (語彙に在るか, 要素名の列)。手書きの語彙の中で、語が ``subject`` と字で同じ組の要素名を全部合わせる(順は語彙の順・重なりは 1 つ)。"""
    subjects = V.PROFILES[PROFILE].subjects if subjects is None else subjects
    found, out = False, []
    for word, elems in subjects:
        if word == subject:
            found = True
            for e in elems:
                if e not in out:
                    out.append(e)
    return found, out


def is_exact_name(local, elems):
    u"""``instance.facts_for`` の「完全一致」の条件の写し。"""
    return any(local == e or local == e + "SummaryOfBusinessResults" or local == e.replace("Income", "IncomeLoss") + "SummaryOfBusinessResults" for e in elems)


def is_loose_name(local, elems):
    u"""``instance.facts_for`` の「部分一致」の条件の写し(完全一致でないものの中で)。"""
    return any(e.lower() in local.lower() for e in elems)


def reached(facts, elems):
    u"""F(各 fact は (名前, 単位, 値))と要素名の列 → (N の fact の列, 届き方)。完全一致が 1 つでも在れば部分一致は見ない。無ければ ([], None)。"""
    exact = [f for f in facts if is_exact_name(f[0].split(":")[-1], elems)]
    if exact:
        return exact, REACH_EXACT
    loose = [f for f in facts if is_loose_name(f[0].split(":")[-1], elems)]
    if loose:
        return loose, REACH_LOOSE
    return [], None


def any_value_match(claim, facts, reading):
    return any(PS.match_fact(claim, f[1], f[2], reading) for f in facts)


def label_claim(claim, reading, facts, subjects=None):
    u"""P の行 1 つ(raw の claim)・読み・F(その行に当てる本の F)→ (札, F のどれかに値が合う, 届き方)。札は封 §2-4 の上から順に 1 つ。"""
    any_v = any_value_match(claim, facts, reading)
    if PS.claim_kind(claim, reading) is None:
        return L_NA, any_v, None
    if not facts:
        return L_FEMPTY, any_v, None
    subject = claim.get("subject")
    if not subject:
        return L_NOSUBJ, any_v, None
    found, elems = subject_elems(subject, subjects)
    if not found:
        return L_OUTVOCAB, any_v, None
    n, how = reached(facts, elems)
    if any_value_match(claim, n, reading):
        return L_BOTH, any_v, how
    if any_v:
        return L_VALONLY, any_v, how
    if n:
        return L_NAMEONLY, any_v, how
    return L_NEITHER, any_v, how


def row_labels(claim, f_self, f_other, subjects=None):
    u"""P の行 → 欄(読みごとに 札・値が合う・届き方・札(他))。"""
    out = []
    for rd in READINGS:
        lab, anyv, how = label_claim(claim, rd, f_self, subjects)
        lab_o, _a, _h = label_claim(claim, rd, f_other, subjects)
        out.extend([lab, anyv, how, lab_o])
    return out


# ======================================================================================================
# 段 1 の部品
def key_rows(books, which):
    u"""本 → {(本の #, 文の番号, 位置): (state, reason, pointers)}。which は ``前`` か ``後``(本の欄の名)。"""
    out = {}
    for b in books:
        for (si, pos, st, why, ptr) in b[which]:
            out[(b[u"#"], si, pos)] = (st, why, tuple(ptr))
    return out


def compare_rows(books, grp_of=None):
    u"""段 1。「前」と「後」を鍵で突き合わせて数える(全体・群別・前の state 別)。"""
    before, after = key_rows(books, u"前"), key_rows(books, u"後")
    both = sorted(k for k in before if k in after)
    only_b = sorted(k for k in before if k not in after)
    only_a = sorted(k for k in after if k not in before)
    grp_of = grp_of or dict((b[u"#"], b[u"群"]) for b in books)

    def kind(k):
        b, a = before[k], after[k]
        if b[0] != a[0]:
            return u"state"
        if b[1] != a[1]:
            return u"reason"
        if b[2] != a[2]:
            return u"pointer"
        return u"同じ"

    def part(keys_both, keys_only_b, keys_only_a):
        ks = collections.Counter(kind(k) for k in keys_both)
        changed = [k for k in keys_both if kind(k) == u"state"]
        trans = collections.Counter((before[k][0], after[k][0]) for k in keys_both)
        return collections.OrderedDict([
            (u"前の行", len(keys_both) + len(keys_only_b)), (u"後の行", len(keys_both) + len(keys_only_a)), (u"両方に在る行", len(keys_both)),
            (u"前にだけ在る行", len(keys_only_b)), (u"後にだけ在る行", len(keys_only_a)),
            (u"state が変わった行", ks.get(u"state", 0)),
            (u"state は同じで reason だけ変わった行", ks.get(u"reason", 0)),
            (u"state も reason も同じで pointer の並びだけ変わった行", ks.get(u"pointer", 0)),
            (u"全部同じ行", ks.get(u"同じ", 0)),
            (u"state の移り変わり(前 → 後。両方に在る行)", collections.OrderedDict((u"%s → %s" % (a, b), trans.get((a, b), 0)) for a in STATES for b in STATES)),
            (u"前は GROUNDED で後は GROUNDED でない行(両方に在る行)", sum(1 for k in changed if before[k][0] == G)),
            (u"前は GROUNDED でなく後は GROUNDED の行(両方に在る行)", sum(1 for k in changed if after[k][0] == G)),
            (u"前は GROUNDED で後に無い行(前にだけ在る行)", sum(1 for k in keys_only_b if before[k][0] == G)),
            (u"前の GROUNDED の行", sum(1 for k in list(keys_both) + list(keys_only_b) if before[k][0] == G)),
            (u"state が変わった行を持つ本", len(set(k[0] for k in changed))),
            (u"前後のどこかの欄が違う行(前にだけ・後にだけを含む)を持つ本", len(set(k[0] for k in keys_only_b + keys_only_a + [k for k in keys_both if kind(k) != u"同じ"])))])

    out = collections.OrderedDict()
    out[u"全体"] = part(both, only_b, only_a)
    out[u"群別"] = collections.OrderedDict(
        (g, part([k for k in both if grp_of[k[0]] == g], [k for k in only_b if grp_of[k[0]] == g], [k for k in only_a if grp_of[k[0]] == g])) for g in GROUPS)
    by_state = collections.OrderedDict()
    for s in STATES:
        kb = [k for k in both if before[k][0] == s]
        ko = [k for k in only_b if before[k][0] == s]
        ks = collections.Counter(kind(k) for k in kb)
        by_state[s] = collections.OrderedDict([
            (u"両方に在る行", len(kb)), (u"前にだけ在る行", len(ko)), (u"state が変わった行", ks.get(u"state", 0)),
            (u"state は同じで reason だけ変わった行", ks.get(u"reason", 0)), (u"pointer の並びだけ変わった行", ks.get(u"pointer", 0))])
    out[u"前の state 別"] = by_state
    out[u"後にだけ在る行の後の state 別"] = collections.OrderedDict((s, sum(1 for k in only_a if after[k][0] == s)) for s in STATES)
    out[u"変わった行の欄"] = ROW_COLUMNS_S1
    diff = [k for k in both if kind(k) != u"同じ"]
    out[u"変わった行(state・reason・pointer のどれか。pointer だけの行も入る)"] = [[k[0], k[1], k[2], before[k][0], after[k][0], before[k][1], after[k][1]] for k in diff]
    out[u"前にだけ在る行"] = [[k[0], k[1], k[2], before[k][0], None, before[k][1], None] for k in only_b]
    out[u"後にだけ在る行"] = [[k[0], k[1], k[2], None, after[k][0], None, after[k][1]] for k in only_a]
    return out


def fact_growth(books):
    u"""SE-2a の欠陥の確認: 「後」の fact の個数が「前」より増えた本の数と、個数の合計。"""
    cut = [b for b in books if b[u"切れた"]]
    return collections.OrderedDict([
        (u"切れた本", len(cut)), (u"fact の個数が前より増えた本", sum(1 for b in cut if b[u"fact(後)"] > b[u"fact(前)"])),
        (u"fact の個数が前より減った本", sum(1 for b in cut if b[u"fact(後)"] < b[u"fact(前)"])),
        (u"fact の個数の合計(前)", sum(b[u"fact(前)"] for b in cut)), (u"fact の個数の合計(後)", sum(b[u"fact(後)"] for b in cut))])


# ======================================================================================================
# 段 2
def p_rows_of(books, other):
    u"""本 → 段 2 の行(P の行ごと。欄は ``ROW_COLUMNS_S2``)。``other`` は {本の #: 別の本の #}。"""
    by_n = dict((b[u"#"], b) for b in books)
    rows = []
    for b in books:
        if not b[u"切れた"]:
            continue
        for (si, pos, st, why, ptr), claim in zip(b[u"前"], b[u"前の claim"]):
            if why != REASON_P:
                continue
            rows.append([b[u"#"], si, pos, b[u"群"]] + row_labels(claim, b[u"F"], by_n[other[b[u"#"]]][u"F"]))
    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    return rows


(C_BOOK, C_SI, C_POS, C_GRP) = range(4)
COLS = collections.OrderedDict((rd, collections.OrderedDict(zip((u"札", u"値", u"届", u"他"), range(4 + 4 * i, 8 + 4 * i)))) for i, rd in enumerate(READINGS))


def tally_reading(rows, rd):
    u"""1 つの読みの札の数と副の欄・対照。"""
    c = COLS[rd]
    labs = collections.Counter(r[c[u"札"]] for r in rows)
    not12 = [r for r in rows if r[c[u"札"]] not in (L_NA, L_FEMPTY)]
    anyv = [r for r in rows if r[c[u"値"]]]
    both = [r for r in rows if r[c[u"札"]] == L_BOTH]
    both_o = [r for r in rows if r[c[u"他"]] == L_BOTH]
    return collections.OrderedDict([
        (u"行", len(rows)),
        (u"札", collections.OrderedDict((l, labs.get(l, 0)) for l in LABELS)),
        (u"札 1・2 でない行(副の分母)", len(not12)),
        (u"F のどれかに値が合う行(副の分母)", len(anyv)),
        (u"札 3・4(主語なし・語彙の外)の行のうち F のどれかに値が合う行", collections.OrderedDict([
            (L_NOSUBJ, sum(1 for r in rows if r[c[u"札"]] == L_NOSUBJ and r[c[u"値"]])), (L_OUTVOCAB, sum(1 for r in rows if r[c[u"札"]] == L_OUTVOCAB and r[c[u"値"]]))])),
        (u"札 5(両方)の行の届き方", collections.OrderedDict((h, sum(1 for r in both if r[c[u"届"]] == h)) for h in (REACH_EXACT, REACH_LOOSE))),
        (u"対照: 札(他)", collections.OrderedDict((l, sum(1 for r in rows if r[c[u"他"]] == l)) for l in LABELS)),
        (u"対照: 両方(他)の行", len(both_o)),
        (u"両方の行(自分の本)", len(both))])


def overlay(rows, read_types):
    u"""読みの軸との重ね。read_types の甲組・乙組の行(本の #, 文の番号, 位置)を段 2 の行に引き、円の族の札を数える。"""
    keyed = dict(((r[C_BOOK], r[C_SI], r[C_POS]), r) for r in rows)
    sel = [t for t in read_types if t[4] in (PS.GRP_KOU, PS.GRP_OTSU)]
    c = COLS[READ_FAMILY]
    found = [keyed[(t[1], t[2], t[3])] for t in sel if (t[1], t[2], t[3]) in keyed]
    labs = collections.Counter(r[c[u"札"]] for r in found)
    per_grp = collections.OrderedDict()
    for g in (PS.GRP_KOU, PS.GRP_OTSU):
        gs = [t for t in sel if t[4] == g]
        gf = [keyed[(t[1], t[2], t[3])] for t in gs if (t[1], t[2], t[3]) in keyed]
        per_grp[g] = collections.OrderedDict([(u"行", len(gs)), (u"引けた行", len(gf)), (u"両方", sum(1 for r in gf if r[c[u"札"]] == L_BOTH))])
    return collections.OrderedDict([
        (u"甲組・乙組の行", len(sel)), (u"鍵が段 2 の P の行に引けた行", len(found)), (u"鍵が引けない行", len(sel) - len(found)),
        (u"円の族の読みの札", collections.OrderedDict((l, labs.get(l, 0)) for l in LABELS)),
        (u"組別", per_grp),
        (u"札の行の欄", [u"本の #", u"文の番号", u"位置", u"円の族: 札"]),
        (u"札の行", [[r[C_BOOK], r[C_SI], r[C_POS], r[c[u"札"]]] for r in found])])


def stage2(books, other, read_types):
    rows = p_rows_of(books, other)
    out = collections.OrderedDict()
    out[u"P の行"] = len(rows)
    out[u"読み"] = collections.OrderedDict((rd, tally_reading(rows, rd)) for rd in READINGS)
    out[u"読みの軸との重ね"] = overlay(rows, read_types)
    out[u"行の欄"] = ROW_COLUMNS_S2
    out[u"行"] = rows
    return out


def frac(n, d):
    return collections.OrderedDict([(u"分子", n), (u"分母", d)])


def predictions(s1, fg, s2):
    u"""予測の判定に要る分子と分母(当たり・外れは書かない)。主の読みは字のとおり。"""
    w = s1[u"全体"]
    lit = s2[u"読み"][READ_LITERAL]
    fam = s2[u"読み"][READ_FAMILY]
    labs = lit[u"札"]

    def p4(t):
        n = t[u"札"]
        return frac(n[L_NOSUBJ] + n[L_OUTVOCAB], t[u"札 1・2 でない行(副の分母)"])
    ov = s2[u"読みの軸との重ね"]
    return collections.OrderedDict([
        (u"SE-1 前にだけ在る行・後にだけ在る行", collections.OrderedDict([(u"前にだけ在る行", w[u"前にだけ在る行"]), (u"後にだけ在る行", w[u"後にだけ在る行"])])),
        (u"SE-2a state が変わった行(1 行以上か)", w[u"state が変わった行"]),
        (u"SE-2a の欠陥の確認(fact の個数が前より増えた本 / 切れた本)", frac(fg[u"fact の個数が前より増えた本"], fg[u"切れた本"])),
        (u"SE-2b state が変わった行 / 前の行", frac(w[u"state が変わった行"], w[u"前の行"])),
        (u"SE-3 前は GROUNDED で後は GROUNDED でない行(両方に在る行) / 前の GROUNDED の行", frac(w[u"前は GROUNDED で後は GROUNDED でない行(両方に在る行)"], w[u"前の GROUNDED の行"])),
        (u"SE-3 参考: 前は GROUNDED で後に無い行(前にだけ在る行)", w[u"前は GROUNDED で後に無い行(前にだけ在る行)"]),
        (u"SE-4 主語なし + 語彙の外 / 札 1・2 でない行(字のとおり。主)", p4(lit)),
        (u"SE-4 参考(円の族)", p4(fam)),
        (u"SE-5 両方 / F のどれかに値が合う行(字のとおり。主)", frac(labs[L_BOTH], lit[u"F のどれかに値が合う行(副の分母)"])),
        (u"SE-5 参考(円の族)", frac(fam[u"札"][L_BOTH], fam[u"F のどれかに値が合う行(副の分母)"])),
        (u"SE-6 両方(他) / 両方(字のとおり。主)", frac(lit[u"対照: 両方(他)の行"], labs[L_BOTH])),
        (u"SE-6 参考(円の族)", frac(fam[u"対照: 両方(他)の行"], fam[u"札"][L_BOTH])),
        (u"SE-7 読みの軸の甲組・乙組の行のうち円の族の読みで両方 / 甲組・乙組の行", frac(ov[u"円の族の読みの札"][L_BOTH], ov[u"甲組・乙組の行"])),
        (u"SE-7 引けなかった行の数", ov[u"鍵が引けない行"])])


# ======================================================================================================
# 1 本
def after_zip(wrapped, summary_bytes):
    u"""「前」の包んだ ZIP の member を全部そのまま写し、サマリーを 1 byte も変えずに ``XBRL/PublicDoc/summary_ixbrl.htm`` として足した ZIP の bytes。"""
    buf = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(wrapped)) as z, zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as out:
        names = [i.filename for i in z.infolist()]
        if SUMMARY_NAME in names:
            raise Stop(u"**包んだ ZIP にサマリーの名前が既に在る。止める**")
        for info in z.infolist():
            out.writestr(TSS._info(info.filename), z.read(info.filename))
        out.writestr(TSS._info(SUMMARY_NAME), summary_bytes)
    return buf.getvalue()


def row4(r, c):
    return (r["sentence"], r["pos"], c["state"], TS.RUN.safe_reason(c["reason"]), list(c["pointers"]))


def forecast_facts(zb):
    u"""サマリーの F(各 fact は (名前, 単位, 値))。``PS.split_facts`` の F の個数と違えば止める。"""
    inst = I.load_instance(PS.summary_zip(zb))
    f_list = []
    for f in inst["facts"]:
        if not f.get("unit") or not f.get("value"):
            continue
        if PS.is_forecast_context(inst["contexts"].get(f.get("context"))):
            f_list.append((f["name"], f["unit"], f["value"]))
    if len(f_list) != len(PS.split_facts(inst)[0]):
        raise Stop(u"**F の個数が PS.split_facts の F の個数と違う。止める**")
    return f_list


def book_job(args):
    u"""1 本: 「前」「後」の行と、P の行の raw の claim と、サマリーの F を返す。便 RT の段 1(``judge_book``)の行と「前」が同じでなければ止める(§2-2)。"""
    n, grp, kind, sha, path = args
    if not os.path.exists(path):
        raise Stop(u"**材料の ZIP が置き場に無い(# %d)。止める**" % n)
    with io.open(path, "rb") as fh:
        zb = fh.read()
    if ST.sha256_bytes(zb) != sha:
        raise Stop(u"**材料の ZIP の sha256 が封の表と違う(# %d)。止める**" % n)
    text = TSS.cut(zb)[0]
    book = collections.OrderedDict([(u"#", n), (u"群", grp), (u"切れた", text is not None), (u"前", []), (u"後", []), (u"前の claim", []), (u"F", []),
                                    (u"fact(前)", 0), (u"fact(後)", 0), (u"RT の行", [])])
    if text is None:
        return book
    wrapped, _nf = TSS.wrap(zb, text)
    rt = RT.TSS.judge_book(n, grp, kind, sha, zb)
    book[u"RT の行"] = [[r[0], r[1], r[2], r[3]] for r in rt[u"行"]]
    before = PS.claims_of(wrapped)
    after = PS.claims_of(after_zip(wrapped, PS.summary_member_bytes(zb)))
    book[u"前"] = [row4(r, c) for r, c in before]
    book[u"後"] = [row4(r, c) for r, c in after]
    book[u"前の claim"] = [dict((k, r.get(k)) for k in (u"subject", u"unit", u"value", u"unit_scale", u"claim_scale", u"pct_tolerance")) for r, _c in before]
    book[u"F"] = forecast_facts(zb)
    book[u"fact(前)"] = len(I.load_instance(wrapped)["facts"])
    book[u"fact(後)"] = len(I.load_instance(after_zip(wrapped, PS.summary_member_bytes(zb)))["facts"])
    return book


# ======================================================================================================
# 配線の確認(封 §2-2)
def wiring(books, expect_rows=None, expect_p=None):
    u"""§2-2。違えば止める。返り値は数。"""
    same_rt = 0
    for b in books:
        if [list(r[:4]) for r in b[u"前"]] != [list(r) for r in b[u"RT の行"]]:
            raise Stop(u"**「前」の行が便 RT の段 1 の行と違う(# %d)。止める**" % b[u"#"])
        same_rt += 1
    before = key_rows(books, u"前")
    after = key_rows(books, u"後")
    p_keys = [k for k, v in before.items() if v[1] == REASON_P]
    if expect_rows is not None and len(before) != expect_rows:
        raise Stop(u"**「前」の行が %d(便 RT の記録の段 1 の行(後)は %d)。止める**" % (len(before), expect_rows))
    if expect_p is not None and len(p_keys) != expect_p:
        raise Stop(u"**P の行が %d(%d でない)。止める**" % (len(p_keys), expect_p))
    for k in p_keys:
        if k not in after or after[k][0] != before[k][0] or after[k][1] != before[k][1]:
            raise Stop(u"**P の行が「後」で同じ鍵・state・reason で在らない(# %d)。止める**" % k[0])
    return collections.OrderedDict([
        (u"本", len(books)), (u"「前」の行が便 RT の段 1 の行と同じ本", same_rt), (u"「前」の行", len(before)),
        (u"P の行(前)", len(p_keys)), (u"P の行のうち後でも同じ鍵・state・reason で在る行", len(p_keys))])


# ======================================================================================================
# 入力・記録
def check_inputs(root):
    out = []
    for no, rel, want in INPUTS:
        p = os.path.join(root, rel)
        if not os.path.isfile(p) or ST.sha256_file(p) != want:
            raise Stop(u"**入力 %d の sha256 が封の表と違う。止める**" % no)
        out.append(collections.OrderedDict([(u"#", no), (u"path", rel), (u"sha256", want)]))
    return out


def engine_fp(rt_rec):
    u"""今の engine の指紋(4 欄)。便 RT の記録の「engine の指紋(今)」と同じでなければ止める。"""
    fp = VD.engine_fingerprint()
    now = collections.OrderedDict((k, fp[k]) for k in FP_KEYS)
    want = collections.OrderedDict((k, rt_rec[u"engine の指紋(今。便 NRE の記録の直した後と同じ)"][k]) for k in FP_KEYS)
    if now != want:
        raise Stop(u"**engine の指紋が便 RT の記録の「今」と違う。止める**")
    return now


def subset_shape(pop):
    return RT.subset_shape(pop)


def orchestrate(root=ROOT, procs=1, material=None, say=print, population=None, clock=time.time, rt_rec=None, read_rec=None, inputs=None):
    u"""400 本 → 配線の確認 → 段 1・段 2 → 記録(OrderedDict)。書かない。``rt_rec``・``read_rec`` を渡すと(試験用)入力の確かめと読みを飛ばす。"""
    mat, prod = RT.material_dir(material)
    if rt_rec is None:
        inputs = check_inputs(root)
        rt_rec = load_json(os.path.join(root, RT_RECORD_REL))
        read_rec = load_json(os.path.join(root, READ_TYPES_REL))
    inputs = inputs or []
    pop = ST.read_population(root) if population is None else population
    shape = subset_shape(pop)
    fp = engine_fp(rt_rec)
    ST.validate_population(pop, *(shape or (ST.N_ROWS, ST.GROUP_COUNTS)))
    for (n, _g, _k, sha) in pop:
        if not os.path.exists(os.path.join(mat, sha + u".zip")):
            raise Stop(u"**材料の ZIP が置き場に無い(# %d)。止める**" % n)
    before_names = ST.names_snapshot(mat)
    jobs = [(n, g, k, sha, os.path.join(mat, sha + u".zip")) for (n, g, k, sha) in pop]
    say(u"段 1・2 %d 本 × %s ― procs %d" % (len(jobs), PROFILE, procs))
    t0 = clock()
    books = TS.NF.map_pool(book_job, jobs, procs)
    elapsed = clock() - t0
    if before_names != ST.names_snapshot(mat):
        raise Stop(u"**材料の置き場の件数か名前が変わった。止める**")
    full = shape is None
    wire = wiring(books, rt_rec[u"段 1(第 1 便。400 本の判定)"][u"行(後)"] if full else None, EXPECT_P if full else None)
    other = PS.other_books([(b[u"群"], b[u"#"], b[u"切れた"], bool(b[u"F"])) for b in books])
    s1 = compare_rows(books)
    fg = fact_growth(books)
    s2 = stage2(books, other, read_rec[u"行"])
    rec = collections.OrderedDict()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"SE(サマリーを engine に渡したら何が動くか・engine の語彙は予想の枠の fact に届くか)― 段 1・段 2(0 USD・通信なし・engine は 0 行)"
    rec[u"この script の sha256"] = ST.sha256_file(os.path.abspath(__file__))
    rec[u"入力"] = inputs
    rec[u"engine の指紋(今。便 RT の記録の今と同じ)"] = fp
    rec[u"profile"] = PROFILE
    rec[u"材料"] = collections.OrderedDict([(u"置き場", ST.display_path(mat) if prod else u"使い捨ての置き場(本番の folder ではない)"), (u"表と一致した ZIP", len(pop))])
    rec[u"切り出し"] = collections.OrderedDict([(u"本", len(books)), (u"切れた本", sum(1 for b in books if b[u"切れた"])), (u"切れない本", sum(1 for b in books if not b[u"切れた"]))])
    rec[K_RT] = wire
    rec[K_S1] = s1
    rec[u"fact の個数の確かめ(SE-2a の欠陥の確認)"] = fg
    rec[K_S2] = s2
    rec[K_PRED] = predictions(s1, fg, s2)
    rec[u"限界"] = list(LIMITS)
    rec[u"時間(秒)"] = round(elapsed, 1)
    rec[u"key_leaks"] = []
    return rec


def check_text(rec, text, key_value=None):
    scan = text.replace(SEAL_REL, u"")
    for _no, rel, _sha in INPUTS:
        scan = scan.replace(rel, u"")
    TSS.check_clean(rec, scan, key_value)


def dumps(o, level=0):
    return RT.dumps(o, level)


def record_text(rec, key_value=None):
    text = dumps(rec) + u"\n"
    check_text(rec, text, key_value)
    return text


def run(root=ROOT, procs=1, out=None, material=None, say=print, check=False, **kw):
    if not check and out is None:
        raise Stop(u"**--out を指定する(書かずに比べるなら --check)。止める**")
    out = os.path.abspath(out) if out else None
    if out and os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    rec = orchestrate(root=root, procs=procs, material=material, say=say, **kw)
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
    a.add_argument("--procs", type=int, default=1)
    a_ = ap.parse_args(argv)
    if a_.cmd == "run":
        run(root=a_.root, procs=a_.procs, out=a_.out, material=a_.material, check=a_.check)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
