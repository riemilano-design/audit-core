# -*- coding: utf-8 -*-
u"""結果の門: 封 docs/XBRL_PRIOR_YEAR_FACT_DRAFT_SEAL_2026-11-22.md(4ee140d2)の結果の文書 docs/XBRL_PRIOR_YEAR_FACT_DRAFT_RESULT_2026-11-22.md(便 XZ0)。

封の門 ``test_xbrl_prior_year_fact_draft_seal.py`` の次の段。**追跡されている記録・script・封・封の門・便 XY0 の記録・結果の文書と git の履歴だけを読む**(書類の置き場は読まない・通信しない・鍵は読まない)。
便 XA0 の結果の門 ``test_xbrl_sheet_wall_result.py`` の部品(読み・sha256・% の丸め・節の切り出し・数のトークン・禁止語・blob の道具)を読み込んで使う(門としては走らせない)。
検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表で 1 つずつ(木の file は変異させず、``Ctx`` の写しに当てる)。

 a script・記録・封・封の門・便 XY0 の記録の sha256(字で留める)・記録の script の sha256・封の commit の欄・記録の限界の欄が script の字と同じ
 b 記録の数え直し: 書類ごとの数から、**script の関数を使わずに**、集計の全部の欄を数え直す(類の和・段 F = 段 HT + 落ちた fact・段 H の N = 段 F の N・属性ごとの U ≥ 束 3 の U も)。
   予測の判定に要る数・先に疑う旗 4 つを集計から作り直した値と照らす
 c 予測 XZ0-1〜XZ0-8 の当たり外れを、封 §4 の字から取った境(丸める前の整数・分数で)と記録から決め直し、文書 §1 の表・件数と同じことを見る。
   封 §4 の「先に自分の欠陥を疑う」4 つの旗を決め直す(どれも立たない)・封 §6 の決め(XZ0-1 と XZ0-2 のどちらかが外れ → 次の便の候補を司令塔から示さず、外れ方を書いて人間に返す)と文書 §5 が合う
 d 結果の文書の数: §1・§2 の数は全部、記録から導く(書類ごとの率の最小・中央・最大と 70・80・85・90・95% 以上の本数・W1 の在る書類・多い順の 5 本・5% 以上と 1% 以下の書類・U + W1 は門の中で導き直す)。
   主な主張の文(主の予測の 1 本は外れ・黙って違うのは、ほぼ文脈の側・25 個に 1 個ほど・8 割ほど・「そのまま通してよい下書き」ではなく)は、記録から組んだ字と断片で一致を見る。
   **§3 の数(記録に欄の無い読み。監査の席の数え直し)は記録に縛らず**、見出し・字で留めた数の並び・§3 の外にその数が出ないこと・「直せるとも直せないとも、この便からは言えない」を縛る
 e 文書の頭の負けと限界(封 §7 の 7 本・封 §0 の申告)・禁止語・「XBRL を作れる」「EDINET の検査に通る」「専用の道具が要らない」「AI が書ける」「人が書ける」を肯定で書かない・docID と EDINET コードの形
 f 封・script・記録・封の門が commit の blob と一致(結果の便で 0 行)・engine は封の commit から 0 行・順序・文書が書く commit の字が実の履歴と合う
この file は docID の字を持たない。
"""
import collections
import copy
import json
import os
import re
import subprocess
import sys
import unittest
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)

import importlib.util  # noqa: E402


def load_module(rel, name):
    u"""importlib で読み込む。読み込みの前に居た名前は、読み込みの後に元の object へ戻す(自分の名前 ``name`` は残す)。"""
    before = dict(sys.modules)
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        for k, v in before.items():
            if k != name and sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


WG = load_module("tests/measure/test_xbrl_sheet_wall_result.py", "xbrl_sheet_wall_result_gate_for_prior_year_fact_draft_result_gate")                # 便 XA0 の結果の門の部品。門としては走らせない
SG = load_module("tests/measure/test_xbrl_prior_year_fact_draft_seal.py", "xbrl_prior_year_fact_draft_seal_gate_for_result_gate")                # 封の門の部品。門としては走らせない
PR = SG.PR
MS = SG.MS

read, sha_file, guard, pct, section = WG.read, WG.sha_file, WG.guard, WG.pct, WG.section
ints_in, doc_number_tokens = WG.ints_in, WG.doc_number_tokens

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
RECORD_REL = SG.RECORD_REL
XY0_RECORD_REL = "fixtures/xbrl/cd8/prior_year_draft_2026-11-22.json"
GATE_REL = "tests/measure/test_xbrl_prior_year_fact_draft_result.py"
DOC_REL = "docs/XBRL_PRIOR_YEAR_FACT_DRAFT_RESULT_2026-11-22.md"
SCRIPT_COMMIT_SHORT = "77662224"                  # script と封の門を足した commit
RECORD_COMMIT_SHORT = "861879cb"                  # 記録を足した commit
BLOB_AT = collections.OrderedDict([
    (SEAL_REL, SEAL_COMMIT_SHORT), (SCRIPT_REL, SCRIPT_COMMIT_SHORT), (SEAL_GATE_REL, SCRIPT_COMMIT_SHORT), (RECORD_REL, RECORD_COMMIT_SHORT)])
HISTORY = collections.OrderedDict([
    (SEAL_REL, [SEAL_COMMIT_SHORT]), (SCRIPT_REL, [SCRIPT_COMMIT_SHORT]), (SEAL_GATE_REL, [SCRIPT_COMMIT_SHORT]), (RECORD_REL, [RECORD_COMMIT_SHORT])])
DOC_COMMITS = (SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT)

SHA_PIN = collections.OrderedDict([
    (RECORD_REL, "1b4cea2d252591cf19c66a46b1e05455a029c8b3c97357becdb846665a56e25d"),
    (SCRIPT_REL, "99c0b847cf4d0825342a658e56bca7a329e3d0fc41864b8fddc0635cc46c32c7"),
    (SEAL_GATE_REL, "cf9639665ee61eedb571f83aa2bb243dd4c056d6709900e234966853774fafe5"),
    (SEAL_REL, "c5096874e993b5fd0689c7d41bff5cbcc9c44ab3b18bd0829ce38c0ba485a829"),
    (XY0_RECORD_REL, "9e7b32f6ec4ec0b8645213cc66b6df520319f5e6e6dd316fcc232d531d98fcfb")])

PAIRS = 63
DOC_COUNT = 67
DROPPED = 4
CLS = ("X", "U", "A", "W1", "W2", "N")
STAGES = ("HT", "H", "F")
AGG = u"集計"
PRED_KEY = u"予測の判定に要る数(XZ0-1〜XZ0-8。当たり・外れは結果の文書で)"
FLAG_KEY = u"先に自分の欠陥を疑う旗(止めない。当たり外れではない)"
K_STAGE = u"束と段ごとの類別"
K_FACTS = u"行の中の数の fact の数"
K_NIL = u"空の欄の fact の数"
K_NONNIL = u"空の欄でない fact の数"
K_OUT = u"行の外の fact の数"
K_ROWS = u"行の数"
K_FALL = u"段 F で段 H へ落ちた fact の数"
K_FALLC = u"段 F で段 H へ落ちた fact の類別(束 3)"
K_NONEMPTY = u"fact が 1 つ以上在る書類の数"
K_RATE = u"段 HT・束 3 の U の率(%)"
B3, B5, NAME, CTX, UNIT, B3NN = u"束 3", u"束 5", u"属性 name だけ", u"属性 contextRef だけ", u"属性 unitRef だけ", u"束 3(空の欄でない fact の分母)"
FULL_BUNDLES = (B3, NAME, CTX, UNIT)               # 分母が行の中の数の fact の全部
NONNIL_BUNDLES = (B5, B3NN)                        # 分母が空の欄でない fact
IDS = (u"XZ0-1", u"XZ0-2", u"XZ0-3", u"XZ0-4", u"XZ0-5", u"XZ0-6", u"XZ0-7", u"XZ0-8")
PK = collections.OrderedDict([
    ("1", u"XZ0-1 段 HT・束 3 の類 U / 行の中の数の fact"), ("2", u"XZ0-2 段 HT・束 3 の類 W1 / 行の中の数の fact"), ("2b", u"XZ0-2 段 HT・束 3 の類 W1 / (U + W1)"),
    ("3", u"XZ0-3 段 HT・束 3 の類 N と類 X の合計 / 行の中の数の fact"), ("4u", u"XZ0-4 段 F・束 3 の類 U / 行の中の数の fact"),
    ("4w", u"XZ0-4 段 F・束 3 の類 W1 / 行の中の数の fact"), ("4wb", u"XZ0-4 段 F・束 3 の類 W1 / (U + W1)"),
    ("5", u"XZ0-5 段 H・束 3 の類 U と段 HT の類 U"), ("6", u"XZ0-6 空の欄でない fact・段 HT の束 5 と束 3 の類 U"),
    ("7", u"XZ0-7 段 HT の contextRef だけの類 U と name だけの類 U"), ("8", u"XZ0-8 段 HT・束 3 の U の率の書類ごとの本数")])
THRESHOLDS = (70, 80, 85, 90, 95)

# 封の字(封の門が script と照らし、ここでは文書が引く字の在り処を縛る)
BOUND_SEAL_PHRASES = (u"段 HT・束 3 の類 U は 70% 以上 86% 以下", u"段 HT・束 3 の類 W1 は 2.5% 以下", u"段 HT・束 3 の類 N と類 X の合計は 6% 以上 20% 以下",
                      u"段 F・束 3 の類 U は段 HT より 1 ポイント以上高く、類 W1 は 3.5% 以下", u"段 H・束 3 の類 U は、段 HT より 15 ポイント以上低い",
                      u"段 HT の束 5 の類 U の率は、束 3 の類 U の率より 2 ポイントを超えて低くはならない", u"`contextRef` だけの類 U の率は `name` だけの類 U の率以上",
                      u"U の率が 95% 以上の書類は 3 本以下で、80% 以上の書類は 20 本以上 50 本以下",
                      u"段 HT・束 3 の U が 95% を超えた", u"N が 30% を超えた", u"`name` だけの U が 70% 未満", u"行の外の fact が全体の 5% を超えた",
                      u"XZ0-1 と XZ0-2 が両方当たりなら、次の便の候補を人間に示す", u"どちらかが外れたら、外れ方を書いて、作る側へ進む道を人間に返す",
                      u"W1 の率は、分母を U + W1 にしたものと fact の全部にしたものの 2 通りで書く",
                      u"「XBRL を作れる」「EDINET の検査に通る」「専用の道具が要らない」「AI が書ける」は、この便からは言えない",
                      u"並びの頭の 1 組だけ", u"ほかの 62 組は fact の単位では 1 つも数えていない")
HEAD_PHRASES = (u"先に負けと限界を書く", u"記録から 1 つずつ読んだもの", u"予測は 63 組のうち並びの頭の 1 組を数えてから立てた(封 §0 の申告)", u"頭の 1 組は合計を代表していなかった",
                u"0 USD・LLM の席は呼んでいない・通信していない", u"engine は 0 行", u"前の年の下書きは、fact の単位では、黙って違う属性を付ける",
                u"便 XY0 の「要素の名は 0.1% しか黙って違わない」は要素の名だけの話で、文脈を足すと成り立たない", u"桁(`decimals`・`scale`)を足すと、決まる fact はさらに減る",
                u"書類による差が大きい", u"記録に欄の無い読み", u"「XBRL を作れる」「EDINET の検査に通る」「専用の道具が要らない」「AI が書ける」は、この便からは言えない")
PHRASES = (u"言えること", u"言えないこと", u"盲検ではない", u"相手の問いへの、この便からの答え", u"封も予測も結果を見てから書き換えていない", u"記録は当たり外れを持たない",
           u"原稿からの率ではない", u"文脈を別の手段で確かめる段が要る", u"文脈のどの部分が違うかは、この便では分けていない", u"次の便は人間が決める。")
QUOTED = re.compile(u"「[^」]*(?:作れる|専用の道具が要らない|人が書ける|AI が書ける|検査に通る)[^」]*」")
AFFIRM_WORDS = (u"作れる(?!か)", u"作れます", u"専用の道具が要らない", u"人が書ける(?!か)", u"AI が書ける", u"検査に通る(?!こと|か)")
FORBIDDEN_WORDS = tuple(WG.FORBIDDEN_WORDS)
STRUCTURAL = WG.STRUCTURAL
# 記録から組んだ値の外に在ってよい数(字で留める。封の境・文書の見出しや説明の数)。理由は 1 つずつ:
#   70 86 6 20 1 2 2.5 3.5 15 95 80 3 50 30 5 = 封 §4 の境 / 85 90 = 書類ごとの率のしきい値の見出し / 11 = script の頭に列挙した「実装で決めた所」の数
#   25 = 「25 個に 1 個ほど」(U + W1 と W1 の比から sanity が見る) / 62 67 63 4 = 材料の数 / 8 = 予測の数
RESIDUAL_OK = set([u"70", u"86", u"6", u"20", u"2.5", u"3.5", u"15", u"95", u"80", u"50", u"30", u"5", u"85", u"90", u"11", u"25", u"62", u"67", u"63", u"4", u"8", u"1", u"2", u"3"])
# 文書 §3(記録に欄の無い読み。監査の席の数え直し)の行ごとの数の並び。記録から導けない = 正本は文書の字そのもの = ここに字で留める(留め)
SEC3_LINES = (
    (u"段 HT・束 3 の W1 2197 を、監査の席が自分の実装で", (u"3", u"2197", u"2100", u"2037", u"160", u"8", u"1", u"2", u"2197", u"2130", u"2100", u"30")),
    (u"W1 2197 のうち、空の欄の fact は 349", (u"2197", u"349")),
    (u"`contextRef` が違う 2100 を、監査の席が文脈の名の字の違い方で分けた", (u"2100", u"1479", u"621")),
    (u"その 7 割ほどは期・数字・時点の語の違いに見える", (u"7",)),
)
SEC3_ONLY = (u"2100", u"2037", u"349", u"1479", u"621")          # §3 の外に出てはならない数(記録に欄が無い)
SEC3_PHRASES = (u"直せるとも直せないとも、この便からは言えない", u"文脈の名そのものは記録にも報告にも無い", u"分けていない")
DOC_COUNT_OF_PAIRS = u"63"


# ======================================================================================================
class Ctx(object):
    u"""検査が見る写し。変異はこの写しを変える(木の file は変えない)。"""

    def __init__(self):
        self.rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        self.xy0 = json.loads(read(XY0_RECORD_REL), object_pairs_hook=collections.OrderedDict)
        self.doc = read(DOC_REL)
        self.seal = read(SEAL_REL)
        self.shas = collections.OrderedDict((rel, sha_file(rel)) for rel in SHA_PIN)

    def copy(self):
        c = Ctx.__new__(Ctx)
        c.rec = copy.deepcopy(self.rec)
        c.xy0 = copy.deepcopy(self.xy0)
        c.doc = self.doc
        c.seal = self.seal
        c.shas = collections.OrderedDict(self.shas)
        return c


def norm(o):
    return json.loads(json.dumps(o, ensure_ascii=False))


def plain(s):
    return s.replace(u"**", u"")


def spct(n, d):
    u"""符号つきの % を小数第 1 位まで(整数で。符号は外して丸める)。"""
    return (u"-" if n < 0 else u"") + pct(abs(n), d)


def xy0_numbers(c):
    s = c.xy0[AGG]
    pk = s[u"集まり S の段ごとの類別"]["PK"]
    rows = s[u"集まり S の行の数"]
    return rows, pk["U"], pk["W1"]


# ======================================================================================================
# b 数え直し(script の関数は使わない)
def cls_sum_of(docs, bundle, stage):
    return collections.OrderedDict((k, sum(d[K_STAGE][bundle][stage][k] for d in docs)) for k in CLS)


def totals(docs):
    u"""書類ごとの数から、記録の集計の欄を数え直す。"""
    t = collections.OrderedDict()
    t[K_ROWS] = sum(d[K_ROWS] for d in docs)
    t[K_FACTS] = sum(d[K_FACTS] for d in docs)
    t[K_NIL] = sum(d[K_NIL] for d in docs)
    t[K_NONNIL] = t[K_FACTS] - t[K_NIL]
    t[K_OUT] = sum(d[K_OUT] for d in docs)
    t[K_STAGE] = collections.OrderedDict((b, collections.OrderedDict((st, cls_sum_of(docs, b, st)) for st in STAGES)) for b in docs[0][K_STAGE])
    t[K_FALL] = sum(d[K_FALL] for d in docs)
    t[K_FALLC] = collections.OrderedDict((k, sum(d[K_FALLC][k] for d in docs)) for k in CLS)
    t[K_NONEMPTY] = sum(1 for d in docs if d[K_FACTS] > 0)
    return t


def doc_problems(d):
    u"""書類 1 つの中の関係(類の和・段 F = 段 HT + 落ちた fact・段 H の N = 段 F の N・属性ごとの U ≥ 束 3 の U)。"""
    out = []
    n = d[u"番号"]
    facts = d[K_FACTS]
    nonnil = facts - d[K_NIL]
    st = d[K_STAGE]
    if d[K_NIL] > facts or d[K_NIL] < 0:
        out.append(u"書類 %d の空の欄の fact が行の中の fact より多い" % n)
    for b in st:
        want = facts if b in FULL_BUNDLES else nonnil if b in NONNIL_BUNDLES else None
        if want is None:
            out.append(u"書類 %d に知らない束 %s" % (n, b))
            continue
        for s in STAGES:
            if list(st[b][s]) != list(CLS) or sum(st[b][s].values()) != want:
                out.append(u"書類 %d の %s・段 %s の類の和が fact の数と違う" % (n, b, s))
        if not (st[b]["HT"]["X"] == st[b]["H"]["X"] == st[b]["F"]["X"]):
            out.append(u"書類 %d の %s の X が段で違う" % (n, b))
        if st[b]["H"]["N"] != st[b]["F"]["N"] or st[b]["H"]["N"] > st[b]["HT"]["N"]:
            out.append(u"書類 %d の %s の段 H の N が段 F の N と違うか段 HT の N より多い" % (n, b))
    if st[B5]["HT"]["X"] != st[B3NN]["HT"]["X"]:
        out.append(u"書類 %d の束 5 と束 3(空の欄でない fact)の X が違う" % n)
    for b in (NAME, CTX, UNIT):
        for s in STAGES:
            if st[b][s]["U"] < st[B3][s]["U"] or st[b][s]["N"] != st[B3][s]["N"]:
                out.append(u"書類 %d の %s・段 %s の U が束 3 より少ないか N が違う(束 3 を 1 つの属性へ写すと決まる fact は減らない)" % (n, b, s))
    fc = d[K_FALLC]
    ht, f = st[B3]["HT"], st[B3]["F"]
    if list(fc) != list(CLS) or sum(fc.values()) != d[K_FALL] or fc["X"] != 0 or d[K_FALL] != ht["N"]:
        out.append(u"書類 %d の落ちた fact の類の和が落ちた fact の数か段 HT の N と違う" % n)
    for k in (u"U", u"A", u"W1", u"W2"):
        if f[k] != ht[k] + fc[k]:
            out.append(u"書類 %d の段 F の類 %s が段 HT + 落ちた fact と違う" % (n, k))
    if f["N"] != fc["N"] or f["X"] != ht["X"]:
        out.append(u"書類 %d の段 F の N か X が落ちた fact と違う" % n)
    if d[K_OUT] < 0 or d[K_ROWS] < 0:
        out.append(u"書類 %d の行の数か行の外の fact が負" % n)
    if facts > 0 and d[K_RATE] != float(pct(ht["U"], facts)):
        out.append(u"書類 %d の U の率の欄が数え直した値と違う" % n)
    return out


def rate_row(n, d):
    return collections.OrderedDict([(u"fact", n), (u"分母", d), (u"%", float(pct(n, d)))])


def pred_expected(rec):
    s = rec[AGG]
    S = s[K_STAGE]
    D = s[K_FACTS]
    dn = s[K_NONNIL]
    ht, hh, ff = S[B3]["HT"], S[B3]["H"], S[B3]["F"]
    n95, n80 = doc_counts(rec)
    return collections.OrderedDict([
        (PK["1"], rate_row(ht["U"], D)),
        (PK["2"], rate_row(ht["W1"], D)),
        (PK["2b"], rate_row(ht["W1"], ht["U"] + ht["W1"])),
        (PK["3"], rate_row(ht["N"] + ht["X"], D)),
        (PK["4u"], collections.OrderedDict([
            (u"段 F の U の fact", ff["U"]), (u"段 HT の U の fact", ht["U"]), (u"分母", D), (u"段 F の U の %", float(pct(ff["U"], D))),
            (u"段 HT の U の %", float(pct(ht["U"], D))), (u"段 F から段 HT を引いた差(ポイント)", float(spct(ff["U"] - ht["U"], D)))])),
        (PK["4w"], rate_row(ff["W1"], D)),
        (PK["4wb"], rate_row(ff["W1"], ff["U"] + ff["W1"])),
        (PK["5"], collections.OrderedDict([
            (u"段 H の U の fact", hh["U"]), (u"段 HT の U の fact", ht["U"]), (u"分母", D), (u"段 H の U の %", float(pct(hh["U"], D))),
            (u"段 HT の U の %", float(pct(ht["U"], D))), (u"段 HT から段 H を引いた差(ポイント)", float(spct(ht["U"] - hh["U"], D)))])),
        (PK["6"], collections.OrderedDict([
            (u"束 5 の U の fact", S[B5]["HT"]["U"]), (u"束 3 の U の fact(空の欄でない fact だけ)", S[B3NN]["HT"]["U"]), (u"分母(空の欄でない fact)", dn),
            (u"束 5 の U の %", float(pct(S[B5]["HT"]["U"], dn))), (u"束 3 の U の %", float(pct(S[B3NN]["HT"]["U"], dn))),
            (u"束 5 から束 3 を引いた差(ポイント)", float(spct(S[B5]["HT"]["U"] - S[B3NN]["HT"]["U"], dn)))])),
        (PK["7"], collections.OrderedDict([
            (u"contextRef の U の fact", S[CTX]["HT"]["U"]), (u"name の U の fact", S[NAME]["HT"]["U"]), (u"分母", D),
            (u"contextRef の U の %", float(pct(S[CTX]["HT"]["U"], D))), (u"name の U の %", float(pct(S[NAME]["HT"]["U"], D))),
            (u"unitRef の U の fact", S[UNIT]["HT"]["U"]), (u"unitRef の U の %", float(pct(S[UNIT]["HT"]["U"], D)))])),
        (PK["8"], collections.OrderedDict([(u"95% 以上の書類", n95), (u"80% 以上の書類", n80), (u"fact が 1 つ以上在る書類", s[K_NONEMPTY]), (u"組の数", len(rec[u"書類"]))]))])


def flags_expected(rec):
    s = rec[AGG]
    S = s[K_STAGE]
    D = s[K_FACTS]
    out = s[K_OUT]
    ht = S[B3]["HT"]
    return [(ht["U"], D, 100 * ht["U"] > 95 * D), (ht["N"], D, 100 * ht["N"] > 30 * D),
            (S[NAME]["HT"]["U"], D, 100 * S[NAME]["HT"]["U"] < 70 * D), (out, D + out, 100 * out > 5 * (D + out))]


def recount_problems(c):
    rec = c.rec
    out = []
    docs = rec[u"書類"]
    m = rec[u"材料"]
    nums = [d[u"番号"] for d in docs]
    if len(nums) != PAIRS or nums != sorted(set(nums)) or nums[0] < 1 or nums[-1] > DOC_COUNT or m[u"組の数"] != PAIRS or m[u"今年の側の書類の本数"] != DOC_COUNT or m[u"除いた今年の書類の数"] != DROPPED \
            or m[u"今年の側の書類の本数"] != m[u"組の数"] + m[u"除いた今年の書類の数"]:
        return [u"書類の番号(67 本の中の昇順の 63 個)・材料の組の数 63・今年の側 67・除いた 4 が違う"]
    for d in docs:
        out.extend(doc_problems(d))
    want, have = totals(docs), rec[AGG]
    if list(have) != list(want):
        return out + [u"集計の欄の名・並びが数え直しと違う"]
    for k in want:
        if norm(have[k]) != norm(want[k]):
            out.append(u"集計の「%s」が書類ごとの数から数え直した値と違う" % k)
    if norm(rec[PRED_KEY]) != norm(pred_expected(rec)):
        out.append(u"予測の判定に要る数が集計から作り直した値と違う")
    flags = list(rec[FLAG_KEY].values())
    fe = flags_expected(rec)
    if len(flags) != len(fe) or any(f[u"fact"] != e[0] or f[u"分母"] != e[1] or f[u"旗"] is not e[2] for f, e in zip(flags, fe)):
        out.append(u"先に疑う旗の 4 つが集計から作り直した値と違う")
    return out


def sha_problems(c):
    out = []
    for rel, want in SHA_PIN.items():
        if c.shas[rel] != want:
            out.append(u"sha256 が字で留めた値と違う: %s" % rel)
    if c.rec[u"この script の sha256"] != SHA_PIN[SCRIPT_REL]:
        out.append(u"記録の script の sha256 が script と違う")
    if (c.rec[u"seal"], c.rec[u"封の commit"]) != (SEAL_REL, SEAL_COMMIT_SHORT):
        out.append(u"記録の封の欄が違う")
    if c.rec[u"限界"] != MS.LIMITS:
        out.append(u"記録の限界の欄が script の字と違う")
    return out


def record_clean_problems(c):
    text = json.dumps(c.rec, ensure_ascii=False)
    out = []
    try:
        MS.check_clean(c.rec, text)
    except SystemExit:
        out.append(u"記録の検査(欄・形・file の名・日付)が止める")
    except Exception as exc:                    # noqa: BLE001
        out.append(u"記録の検査が止める: %s" % type(exc).__name__)
    if WG.DOCID_FORM.search(re.sub(r"[0-9a-fA-F]{32,}", u"", text)) or WG.ECODE_FORM.search(text):
        out.append(u"記録に docid か EDINET コードの形が在る")
    return out


def bound_problems(c):
    out = [u"封に字が無い: %s" % p for p in BOUND_SEAL_PHRASES if p not in c.seal]
    sec4 = section(c.seal, u"## §4 ", u"## §5 ")
    rows = [ln for ln in sec4.splitlines() if re.match(r"^\| XZ0-\d", ln)]
    if len(rows) != 8:
        out.append(u"封 §4 の表の行が 8 つでない")
    sec7 = section(c.seal, u"## §7 ", None)
    if len([ln for ln in sec7.splitlines() if ln.startswith(u"- ")]) != 7:
        out.append(u"封 §7 の限界の行が 7 行でない")
    sec0 = section(c.seal, u"## §0 ", u"## §1 ")
    if u"並びの頭の 1 組だけ" not in sec0:
        out.append(u"封 §0 に頭の 1 組の申告が無い")
    return out


# ======================================================================================================
# c 当たり外れの決め直し(封 §4 の境。丸める前の整数・分数)
def doc_counts(rec):
    u"""段 HT・束 3 の U の率が 95% 以上・80% 以上の書類の本数(fact が 1 つ以上在る書類だけ)。"""
    docs = [d for d in rec[u"書類"] if d[K_FACTS] > 0]
    n95 = sum(1 for d in docs if 100 * d[K_STAGE][B3]["HT"]["U"] >= 95 * d[K_FACTS])
    n80 = sum(1 for d in docs if 100 * d[K_STAGE][B3]["HT"]["U"] >= 80 * d[K_FACTS])
    return n95, n80


def judge_nums(D, ht_u, ht_w1, ht_n, ht_x, f_u, f_w1, h_u, Dn, u5, u3, c_u, n_u, n95, n80):
    u"""封 §4 の境(整数のまま)。値は (当たりか, 外れた向き)。"""
    out = collections.OrderedDict()

    def put(k, lo, hi):
        out[k] = (lo and hi, u"" if lo and hi else (u"下" if not lo else u"上"))
    put(u"XZ0-1", 100 * ht_u >= 70 * D, 100 * ht_u <= 86 * D)
    put(u"XZ0-2", True, 1000 * ht_w1 <= 25 * D)
    put(u"XZ0-3", 100 * (ht_n + ht_x) >= 6 * D, 100 * (ht_n + ht_x) <= 20 * D)
    u_ok = 100 * (f_u - ht_u) >= 1 * D
    w_ok = 1000 * f_w1 <= 35 * D
    out[u"XZ0-4"] = (u_ok and w_ok, u"" if u_ok and w_ok else u"U か W1")
    put(u"XZ0-5", 100 * (ht_u - h_u) >= 15 * D, True)
    put(u"XZ0-6", 100 * (u5 - u3) >= -2 * Dn, True)
    put(u"XZ0-7", c_u >= n_u, True)
    ok8 = n95 <= 3 and 20 <= n80 <= 50
    out[u"XZ0-8"] = (ok8, u"" if ok8 else u"95% か 80%")
    return out


def judge(rec):
    s = rec[AGG]
    S = s[K_STAGE]
    ht = S[B3]["HT"]
    n95, n80 = doc_counts(rec)
    return judge_nums(s[K_FACTS], ht["U"], ht["W1"], ht["N"], ht["X"], S[B3]["F"]["U"], S[B3]["F"]["W1"], S[B3]["H"]["U"], s[K_NONNIL], S[B5]["HT"]["U"], S[B3NN]["HT"]["U"],
                      S[CTX]["HT"]["U"], S[NAME]["HT"]["U"], n95, n80)


def suspects(c):
    u"""封 §4 の「先に自分の欠陥を疑う」4 つの旗(封の字のまま)。"""
    return tuple(e[2] for e in flags_expected(c.rec))


def cell_text(rec, key):
    s = rec[AGG]
    S = s[K_STAGE]
    D, Dn = s[K_FACTS], s[K_NONNIL]
    ht = S[B3]["HT"]
    n95, n80 = doc_counts(rec)

    def f(a, b):
        return u"%d/%d(%s%%)" % (a, b, pct(a, b))

    def sgn(n, d):
        return (u"+" if n >= 0 else u"−") + pct(abs(n), d)
    return {u"XZ0-1": f(ht["U"], D), u"XZ0-2": f(ht["W1"], D), u"XZ0-3": f(ht["N"] + ht["X"], D),
            u"XZ0-4": u"U %s・差 %s ポイント・W1 %s" % (f(S[B3]["F"]["U"], D), sgn(S[B3]["F"]["U"] - ht["U"], D), f(S[B3]["F"]["W1"], D)),
            u"XZ0-5": u"段 H %s・差 %s ポイント" % (f(S[B3]["H"]["U"], D), pct(ht["U"] - S[B3]["H"]["U"], D)),
            u"XZ0-6": u"束 5 %s・束 3 %s・差 %s ポイント" % (f(S[B5]["HT"]["U"], Dn), f(S[B3NN]["HT"]["U"], Dn), sgn(S[B5]["HT"]["U"] - S[B3NN]["HT"]["U"], Dn)),
            u"XZ0-7": u"`contextRef` %s・`name` %s" % (f(S[CTX]["HT"]["U"], D), f(S[NAME]["HT"]["U"], D)),
            u"XZ0-8": u"95%% 以上 %d 本・80%% 以上 %d 本(%d 本のうち)" % (n95, n80, s[K_NONEMPTY])}[key]


def expected_cells(c):
    out = collections.OrderedDict()
    for k, (ok, way) in judge(c.rec).items():
        out[k] = (cell_text(c.rec, k), u"当たり" if ok else u"外れ")
    return out


def xz04_note(c):
    s = c.rec[AGG]
    S = s[K_STAGE]
    D = s[K_FACTS]
    ht, ff = S[B3]["HT"], S[B3]["F"]
    u_side = u"予測の内" if 100 * (ff["U"] - ht["U"]) >= D else u"予測の外"
    w_side = u"予測の内" if 1000 * ff["W1"] <= 35 * D else u"外"
    return u"XZ0-4 は、U の側(%s%s ポイント)は%sで、W1 の側(%s%%)が%s。" % (u"+" if ff["U"] >= ht["U"] else u"−", pct(abs(ff["U"] - ht["U"]), D), u_side, pct(ff["W1"], D), w_side)


def miss_ids(j):
    return [k for k in IDS if not j[k][0]]


DECISION_LINE = u"封 §6 の決め"
OPTION_LINE = re.compile(u"^\\s+- \\(|\\([a-z]\\)|\\((?:i|ii|iii|iv|v|vi)\\)")
TAIL_WORDS = (u"0 USD", u"有料", u"候補")
TAIL_END = u"次の便は人間が決める。"


def sec5_tail_problems(sec5):
    u"""封 §6(どちらかが外れたら次の便の候補を示さず外れ方を書いて人間に返す)の形の見張り。「封 §6 の決め」の行より後ろに、選択肢の行・費用や候補の語が無く、最後の行が「次の便は人間が決める。」で終わる。"""
    lines = [ln for ln in plain(sec5).splitlines() if ln.strip()]
    idx = [i for i, ln in enumerate(lines) if DECISION_LINE in ln]
    if len(idx) != 1:
        return [u"§5 に「封 §6 の決め」の行が 1 つでない"]
    out = []
    after = lines[idx[0] + 1:]
    for ln in after:
        if OPTION_LINE.search(ln):
            out.append(u"§5 の決めの行より後ろに選択肢の行が在る: %s" % ln[:30])
        for w in TAIL_WORDS:
            if w in ln:
                out.append(u"§5 の決めの行より後ろに「%s」が在る" % w)
    if not after or not after[-1].endswith(TAIL_END) or after[-1] != lines[-1]:
        out.append(u"§5 の最後の行が「%s」で終わっていない" % TAIL_END)
    return out


def verdict_problems(c):
    rec = c.rec
    j = judge(rec)
    want = expected_cells(c)
    out = []
    rows = {}
    for ln in c.doc.splitlines():
        m = re.match(r"^\| (XZ0-\d)(?:\(主\))? \|(.*)\|$", ln)
        if m:
            rows[m.group(1)] = [x.strip() for x in m.group(2).split(u"|")]
    if sorted(rows) != sorted(j):
        return [u"文書 §1 の表の行が XZ0-1〜XZ0-8 でない"]
    sec4 = section(c.seal, u"## §4 ", u"## §5 ")
    for k, cells in rows.items():
        if len(cells) != 3:
            out.append(u"%s の行の欄の数が違う" % k)
            continue
        if cells[0] not in sec4:
            out.append(u"%s の予測の字が封 §4 の表に無い: %s" % (k, cells[0]))
        if cells[1] != want[k][0]:
            out.append(u"%s の実測の字が記録から組んだ字と違う: %s" % (k, cells[1]))
        if cells[2] != want[k][1]:
            out.append(u"%s の判定が決め直した判定と違う: %s(決め直し: %s)" % (k, cells[2], want[k][1]))
    for k in (u"XZ0-1", u"XZ0-2"):
        if not re.search(r"^\| %s\(主\) \|" % k, c.doc, re.M):
            out.append(u"%s の行に「(主)」が無い(封 §4 の主の読み)" % k)
    for k in IDS[2:]:
        if re.search(r"^\| %s\(主\) \|" % k, c.doc, re.M):
            out.append(u"%s の行に「(主)」が付いている(封 §4 の主は XZ0-1・XZ0-2)" % k)
    hits = sum(1 for v in j.values() if v[0])
    if u"- 当たり %d・外れ %d。" % (hits, len(j) - hits) not in c.doc.splitlines():
        out.append(u"文書の件数の行が決め直した件数と違う")
    head = plain(c.doc.split(u"## §1")[0])
    miss = miss_ids(j)
    if u"判定した %d 本は 当たり %d・外れ %d(%s が外れ)。" % (len(j), hits, len(j) - hits, u"・".join(miss)) not in head:
        out.append(u"文書の頭の件数・外れた予測の名が決め直した値と違う")
    mains = [k for k in miss if k in (u"XZ0-1", u"XZ0-2")]
    if mains:
        if u"主の予測の %d 本(%s)は外れ。" % (len(mains), u"・".join(mains)) not in head:
            out.append(u"外れた主の予測の言い切りが文書の頭に無い(%s)" % u"・".join(mains))
    elif re.search(u"主の予測の[^。]*は外れ", head):
        out.append(u"主の予測は両方当たりなのに文書の頭が外れと書いている")
    sec1, sec5 = section(c.doc, u"## §1 ", u"## §2 "), section(c.doc, u"## §5 ", None)
    sus = suspects(c)
    if any(sus):
        out.append(u"封 §4 の「先に自分の欠陥を疑う」旗が立っている: %s" % (sus,))
    line = [ln for ln in sec1.splitlines() if u"「先に自分の欠陥を疑う」旗 4 つ" in ln]
    s = rec[AGG]
    if len(line) != 1 or u"(段 HT・束 3 の U が 95% を超えた・N が 30% を超えた・`name` だけの U が 70% 未満・行の外の fact が全体の 5% を超えた)は、どれも立っていない。" not in line[0] \
            or u"行の外の fact は %d/%d。" % (s[K_OUT], s[K_FACTS] + s[K_OUT]) not in sec1:
        out.append(u"文書 §1 の自己点検の言い切り(4 つの旗・どれも立っていない)が封の字・記録と合わない")
    # XZ0-4 の外れ方(U の側・W1 の側)
    note = xz04_note(c)
    if not j[u"XZ0-4"][0] and note not in plain(sec1):
        out.append(u"XZ0-4 の外れ方の行が記録から組んだ字と違う")
    # 封 §6: XZ0-1 と XZ0-2 が両方当たりなら次の便の候補を示す。どちらかが外れたら、次の便の候補は司令塔からは示さず、外れ方を書いて人間に返す
    cond = j[u"XZ0-1"][0] and j[u"XZ0-2"][0]
    s6 = section(c.seal, u"## §6 ", u"## §7 ")
    tail = sec5_tail_problems(sec5)
    shown = u"人間に示す次の便の候補" in sec5 or u"(i) " in sec5 or u"(ii) " in sec5 or u"次の便の候補" in sec5 or bool(tail)
    if cond != shown:
        out.append(u"封 §6 の決め(XZ0-1 と XZ0-2 が両方当たりなら次の便の候補を示す・どちらかが外れたら示さない)と文書 §5 が合わない")
    if cond:
        i6 = s6.index(u"(i) ")
        seg = s6[i6:s6.index(u"\n", i6)].strip()
        if seg not in plain(sec5):
            out.append(u"§5 の次の便の候補 (i)(ii) が封 §6 の字と違う")
    else:
        if u"%s が外れたので、次の便は司令塔からは示さず、人間に返す。" % u"と".join(m for m in (u"XZ0-1", u"XZ0-2") if not j[m][0]) not in plain(sec5):
            out.append(u"外れた主の予測の名と「次の便は司令塔からは示さず、人間に返す」が §5 に無い")
        if u"外れ方を書いて" not in sec5:
            out.append(u"外れ方を書いて人間に返す道が §5 に無い")
        out.extend(tail)
    return out


# ======================================================================================================
# d 文書の数・主な主張の文
def doc_rate_rows(rec):
    return [(d[K_STAGE][B3]["HT"]["U"], d[K_FACTS]) for d in rec[u"書類"] if d[K_FACTS] > 0]


def doc_stats(rec):
    u"""書類ごとの率の最小・中央・最大・しきい値ごとの本数(分数で)。"""
    fr = sorted(Fraction(u, n) for u, n in doc_rate_rows(rec))
    mid = fr[len(fr) // 2] if len(fr) % 2 else (fr[len(fr) // 2 - 1] + fr[len(fr) // 2]) / 2
    cnt = [sum(1 for u, n in doc_rate_rows(rec) if 100 * u >= t * n) for t in THRESHOLDS]
    return fr[0], mid, fr[-1], cnt


def w1_stats(rec):
    u"""W1 が 1 つ以上在る書類・1 本の中の最大・多い順の 5 本の合計・5% 以上の書類・1% 以下の書類。"""
    w = [(d[K_STAGE][B3]["HT"]["W1"], d[K_FACTS]) for d in rec[u"書類"]]
    vals = sorted(v for v, _ in w)
    return (sum(1 for v, _ in w if v > 0), max(vals), sum(vals[-5:]), sum(1 for v, n in w if n > 0 and 100 * v >= 5 * n), sum(1 for v, n in w if n > 0 and 100 * v <= n))


def fpct(fr):
    return pct(fr.numerator, fr.denominator)


def tbl(label, cl, den, pct_keys):
    return u"| %s | %s |" % (label, u" | ".join((u"%d(%s%%)" % (cl[k], pct(cl[k], den))) if k in pct_keys else u"%d" % cl[k] for k in CLS))


def expected_lines(c):
    rec = c.rec
    s = rec[AGG]
    S = s[K_STAGE]
    D, Dn = s[K_FACTS], s[K_NONNIL]
    return [tbl(u"段 HT(見出し・表の番号・行の字・セルの番号)", S[B3]["HT"], D, (u"U", u"W1", u"N")), tbl(u"段 H(見出し・行の字・セルの番号)", S[B3]["H"], D, (u"U",)),
            tbl(u"段 F(段 HT が空なら段 H へ)", S[B3]["F"], D, (u"U", u"W1")),
            tbl(u"`name` だけ", S[NAME]["HT"], D, (u"U", u"W1")), tbl(u"`contextRef` だけ", S[CTX]["HT"], D, (u"U", u"W1")), tbl(u"`unitRef` だけ", S[UNIT]["HT"], D, (u"U",)),
            tbl(u"束 3", S[B3NN]["HT"], Dn, (u"U",)), tbl(u"束 5(束 3 に `decimals`・`scale` を足す)", S[B5]["HT"], Dn, (u"U",))]


def expected_fragments(c):
    rec = c.rec
    s = rec[AGG]
    m = rec[u"材料"]
    S = s[K_STAGE]
    D, Dn = s[K_FACTS], s[K_NONNIL]
    ht, hh, ff, fc = S[B3]["HT"], S[B3]["H"], S[B3]["F"], s[K_FALLC]
    lo, mid, hi, cnt = doc_stats(rec)
    w1docs, w1max, top5, w5, w1 = w1_stats(rec)
    first = rec[u"書類"][0]
    j = judge(rec)
    hits = sum(1 for v in j.values() if v[0])
    xrows, xu, xw = xy0_numbers(c)
    n95 = cnt[4]
    ctx_w, name_w, unit_w = S[CTX]["HT"]["W1"], S[NAME]["HT"]["W1"], S[UNIT]["HT"]["W1"]
    f = []
    f.append(u"fact(W1)は %d/%d(%s%%)で、予測の 2.5%% 以下を超えた" % (ht["W1"], D, pct(ht["W1"], D)))
    f.append(u"下書きがそのまま通す fact(U + W1)%d のうち W1 は %s%%。" % (ht["U"] + ht["W1"], pct(ht["W1"], ht["U"] + ht["W1"])))
    f.append(u"判定した %d 本は 当たり %d・外れ %d(%s が外れ)。" % (len(j), hits, len(j) - hits, u"・".join(miss_ids(j))))
    f.append(u"その 1 組の W1 は %s%% で、63 組の合計はその 4 倍近くだった。" % pct(first[K_STAGE][B3]["HT"]["W1"], first[K_FACTS]))
    f.append(u"W1 は `contextRef` だけで %d・`name` だけで %d・`unitRef` だけで %d(§2)" % (ctx_w, name_w, unit_w))
    f.append(u"(XZ0-6 外れ。空の欄でない fact で %s%% → %s%%)" % (pct(S[B3NN]["HT"]["U"], Dn), pct(S[B5]["HT"]["U"], Dn)))
    f.append(u"段 HT・束 3 の U の率は、書類ごとに最小 %s%%・中央 %s%%・最大 %s%%。95%% 以上は %d 本のうち %d 本。W1 が 1 つも無い書類は %d 本だけ。" % (fpct(lo), fpct(mid), fpct(hi), PAIRS, n95, PAIRS - w1docs))
    f.append(u"今年の側 %d 本・組 %d・除いた今年の書類 %d(前の年の側に相手が無い)。行は %d・行の中の数の fact は %d(うち空の欄の fact %d・空の欄でない fact %d)・行の外の fact は %d(分母の外)。"
             u"fact が 1 つ以上在る書類は %d。" % (m[u"今年の側の書類の本数"], m[u"組の数"], m[u"除いた今年の書類の数"], s[K_ROWS], D, s[K_NIL], Dn, s[K_OUT], s[K_NONEMPTY]))
    f.append(u"束 3(`name`・`contextRef`・`unitRef`)の段ごとの類(分母 %d):" % D)
    f.append(u"段 HT の属性ごとの類(同じ置き場の候補を、その属性だけで見たもの。分母 %d):" % D)
    f.append(u"空の欄でない fact(分母 %d)の段 HT:" % Dn)
    f.append(u"下書きがそのまま通す fact(U + W1)は %d で、そのうち W1 は %d(%s%%)。fact の全部を分母にすると %d/%d(%s%%)。段 F では U + W1 が %d・W1 は %d(%s%%)、fact の全部では %s%%。" % (
        ht["U"] + ht["W1"], ht["W1"], pct(ht["W1"], ht["U"] + ht["W1"]), ht["W1"], D, pct(ht["W1"], D), ff["U"] + ff["W1"], ff["W1"], pct(ff["W1"], ff["U"] + ff["W1"]), pct(ff["W1"], D)))
    f.append(u"段 F で段 H へ落ちた fact は %d(段 HT の N と同じ数)。その類は U %d・A %d・W1 %d・W2 %d・N %d。" % (s[K_FALL], fc["U"], fc["A"], fc["W1"], fc["W2"], fc["N"]))
    f.append(u"表の番号を外して拾い直すと、%d が決まるが、黙って違う fact が %d 増える。" % (fc["U"], fc["W1"]))
    f.append(u"書類ごとの段 HT・束 3 の U の率(%d 本): 最小 %s%%・中央 %s%%・最大 %s%%。70%% 以上が %d 本・80%% 以上が %d 本・85%% 以上が %d 本・90%% 以上が %d 本・95%% 以上が %d 本。" % (
        PAIRS, fpct(lo), fpct(mid), fpct(hi), cnt[0], cnt[1], cnt[2], cnt[3], cnt[4]))
    f.append(u"段 HT・束 3 の W1 が 1 つ以上在る書類は %d 本(無い書類は %d 本)。1 本の中の最大は %d。W1 の多い順の 5 本で %d(W1 の全部 %d の半分を超える)。"
             u"W1 がその書類の fact の 5%% 以上の書類は %d 本・1%% 以下の書類は %d 本。" % (w1docs, PAIRS - w1docs, w1max, top5, ht["W1"], w5, w1))
    f.append(u"便 XY0 の行の単位の数(標準の計算書の行 %d 行で、要素の名が 1 つに決まり正しい行 %s%%・違う行 %s%%)とは、分母(行と fact・標準の計算書の行と全部の行)も鍵も違う。並べて差を読まない。" % (
        xrows, pct(xu, xrows), pct(xw, xrows)))
    f.append(u"公開済みの 63 組で、前の年の提出書類の表の中の置き場と数の fact の属性の対応を今年の fact に当てると、要素・文脈・単位の 3 つが 1 つに決まり正しかった fact は %s%%・"
             u"1 つに決まって違った fact は %s%%・前の年に置き場が無かった fact は %s%% だった。" % (pct(ht["U"], D), pct(ht["W1"], D), pct(ht["N"], D)))
    f.append(u"黙って違う fact は、属性ごとに見ると文脈の側に集まる(`contextRef` だけの W1 %d・`name` だけ %d・`unitRef` だけ %d)。書類による偏りも大きい(多い順の 5 本で半分を超える)。" % (ctx_w, name_w, unit_w))
    f.append(u"8 割ほどの fact は要素・文脈・単位がそのまま決まる。ただし 決まった中の 25 個に 1 個ほどは黙って違い、その大半は文脈の側(文脈のどの部分が違うかは、この便では分けていない)。"
             u"前の年の写しは「そのまま通してよい下書き」ではなく、文脈を別の手段で確かめる段が要る。測ったのは道具が組んだ後の字どうしで、原稿からの率ではない。")
    f.append(u"黙って違うのは、ほぼ文脈の側。")
    f.append(u"便 XY0 の「要素の名は %s%% しか黙って違わない」は要素の名だけの話で、文脈を足すと成り立たない" % pct(xw, xrows))
    f.append(u"行の中の数の fact %d(行の字が空の fact X を含む)" % D)
    f.append(u"行の外の fact は %d/%d。" % (s[K_OUT], D + s[K_OUT]))
    f.append(xz04_note(c))
    f.append(u"前の年の下書きは、fact の単位では、黙って違う属性を付ける。")
    return f


def sanity_problems(c):
    u"""文書の言い切りの向き(ほぼ文脈の側・25 個に 1 個ほど・8 割ほど・4 倍近く・桁を足すと減る・半分を超える・落ちると決まるが違うのも増える)が記録の数に合う。"""
    s = c.rec[AGG]
    S = s[K_STAGE]
    D, Dn = s[K_FACTS], s[K_NONNIL]
    ht, ff, fc = S[B3]["HT"], S[B3]["F"], s[K_FALLC]
    out = []
    cw, nw, uw = S[CTX]["HT"]["W1"], S[NAME]["HT"]["W1"], S[UNIT]["HT"]["W1"]
    if not (10 * cw >= 9 * ht["W1"] and cw > 10 * nw and nw > uw):
        out.append(u"文書の「黙って違うのは、ほぼ文脈の側」が記録と合わない(contextRef だけの W1 が束 3 の W1 の 9 割以上・name の 10 倍超・name > unitRef でない)")
    if not (24 * ht["W1"] <= ht["U"] + ht["W1"] <= 26 * ht["W1"]):
        out.append(u"文書の「25 個に 1 個ほど」が記録と合わない")
    if not (75 * D <= 100 * ht["U"] < 85 * D):
        out.append(u"文書の「8 割ほど」が記録と合わない")
    first = c.rec[u"書類"][0]
    r = Fraction(ht["W1"], D) / Fraction(first[K_STAGE][B3]["HT"]["W1"], first[K_FACTS])
    if not (Fraction(7, 2) <= r < 4):
        out.append(u"文書の「その 4 倍近く」が記録と合わない(63 組の W1 の率が頭の 1 組の 3.5 倍以上 4 倍未満でない)")
    if not (Fraction(S[B5]["HT"]["U"], Dn) < Fraction(S[B3NN]["HT"]["U"], Dn)):
        out.append(u"文書の「桁を足すと、決まる fact はさらに減る」が記録と合わない")
    if not (2 * w1_stats(c.rec)[2] > ht["W1"]):
        out.append(u"文書の「多い順の 5 本で半分を超える」が記録と合わない")
    if not (fc["W1"] > 0 and ff["W1"] - ht["W1"] == fc["W1"] and ff["U"] - ht["U"] == fc["U"] and fc["U"] < ht["N"]):
        out.append(u"文書の「表の番号を外すと決まるが、黙って違う fact も増える」が記録と合わない")
    if not (Fraction(ht["W1"], D) > Fraction(25, 1000)):
        out.append(u"文書の「予測の 2.5% 以下を超えた」が記録と合わない")
    xrows, xu, xw = xy0_numbers(c)
    if not (Fraction(xw, xrows) < Fraction(1, 100) < Fraction(ht["W1"], D)):
        out.append(u"文書の「便 XY0 の 0.1% は文脈を足すと成り立たない」が記録と合わない")
    if not (S[B3]["HT"]["U"] > S[B3]["H"]["U"] and ff["U"] > ht["U"]):
        out.append(u"段 HT の U が段 H より多い・段 F が段 HT より多い、が記録と合わない")
    return out


def fragment_problems(c):
    out = []
    lines = c.doc.splitlines()
    doc = plain(c.doc)
    for want in expected_lines(c):
        if want not in lines:
            out.append(u"文書に記録から組んだ行が無い: %s" % want[:40])
    for frag in expected_fragments(c):
        if frag not in doc:
            out.append(u"文書に記録から組んだ字が無い: %s" % frag[:40])
    if doc.count(u"そのまま通してよい") != 1 or u"「そのまま通してよい下書き」ではなく" not in doc:
        out.append(u"「そのまま通してよい下書き」を肯定で書いているか、否定の形が無い")
    return out


def derived_numbers(c):
    rec = c.rec
    out = set()
    ints_in(rec[AGG], out)
    ints_in(rec[PRED_KEY], out)
    ints_in(rec[FLAG_KEY], out)
    lo, mid, hi, cnt = doc_stats(rec)
    for fr in (lo, mid, hi):
        out.add(fpct(fr))
    out |= set(str(v) for v in cnt)
    out |= set(str(v) for v in w1_stats(rec))
    s = rec[AGG]
    S = s[K_STAGE]
    D, Dn = s[K_FACTS], s[K_NONNIL]
    ht, hh, ff = S[B3]["HT"], S[B3]["H"], S[B3]["F"]
    out |= set([str(PAIRS), str(DOC_COUNT), str(DROPPED), str(ht["U"] + ht["W1"]), str(ff["U"] + ff["W1"]), str(D + s[K_OUT]),
                pct(ht["W1"], ht["U"] + ht["W1"]), pct(ff["W1"], ff["U"] + ff["W1"]), pct(ff["W1"], D), pct(s[K_OUT], D + s[K_OUT]), str(PAIRS - w1_stats(rec)[0])])
    for b in S:
        den = D if b in FULL_BUNDLES else Dn
        for st in STAGES:
            for k in CLS:
                out.add(pct(S[b][st][k], den))
    first = rec[u"書類"][0]
    out.add(pct(first[K_STAGE][B3]["HT"]["W1"], first[K_FACTS]))
    out.add(spct(ff["U"] - ht["U"], D).lstrip(u"-"))
    out.add(pct(ht["U"] - hh["U"], D))
    out.add(spct(S[B5]["HT"]["U"] - S[B3NN]["HT"]["U"], Dn).lstrip(u"-"))
    xrows, xu, xw = xy0_numbers(c)
    out |= set([str(xrows), pct(xu, xrows), pct(xw, xrows)])
    out |= set(DOC_COMMITS)
    out |= set(STRUCTURAL) | RESIDUAL_OK
    return out


def sec3_text(c):
    return section(c.doc, u"## §3 ", u"## §4 ")


def outside_sec3(c):
    return c.doc.replace(sec3_text(c), u"")


def doc_number_problems(c):
    u"""§3 の外の数字は、記録から導いた値か字で留めた境の数の内。§3 は sec3_problems が見る。"""
    allowed = derived_numbers(c)
    out = []
    for i, ln in enumerate(outside_sec3(c).splitlines(), 1):
        for tok in doc_number_tokens(re.sub(r"^\d+\. ", u"", ln)):
            if tok.replace(u",", u"") not in allowed:
                out.append(u"文書の(§3 の外の)%d 行目の数 %s が記録から組んだ数の外: %s" % (i, tok, ln[:30]))
    return out


def residual_problems(c):
    u"""記録から組んだ字(行・断片・§1 の表の行・§3)を文書から除いた残りの数は、字で留めた境の数(RESIDUAL_OK)と記録の整数の内、かつ文書の文の数としての向き。"""
    rest = plain(c.doc)
    rest = rest.replace(plain(sec3_text(c)), u" ")
    for frag in expected_fragments(c) + expected_lines(c):
        rest = rest.replace(frag, u" ")
    rows = [ln for ln in rest.splitlines() if re.match(r"^\| XZ0-\d", ln)]
    for ln in rows:
        rest = rest.replace(ln, u" ")
    out = []
    allowed = RESIDUAL_OK | set(STRUCTURAL) | set(DOC_COMMITS)
    for i, ln in enumerate(rest.splitlines(), 1):
        for tok in doc_number_tokens(ln):
            t = tok.replace(u",", u"")
            if t not in allowed:
                out.append(u"記録から組んだ字を除いた残りの数 %s(%s)が留めた境の数の外" % (t, ln[:24]))
    return out


def sec3_problems(c):
    u"""§3 は記録に欄の無い読み(監査の席の数え直し)の節。記録に縛らない。見出し・字で留めた数の並び・自己整合・§3 の外にその数が無い・「直せるとも直せないとも言えない」。"""
    s = sec3_text(c)
    out = []
    if u"記録に欄の無い読み" not in s.splitlines()[0]:
        out.append(u"§3 の見出しが「記録に欄の無い読み」でない")
    bullets = [ln for ln in s.splitlines()[1:] if ln.strip()]
    if len(bullets) != len(SEC3_LINES):
        out.append(u"§3 の箇条の数 %d が留めた行の数 %d と違う" % (len(bullets), len(SEC3_LINES)))
    for key, nums in SEC3_LINES:
        hit = [ln for ln in bullets if key in ln]
        if len(hit) != 1:
            out.append(u"§3 に鍵の句の行が 1 つでない(%d 行): %s" % (len(hit), key[:16]))
            continue
        got = tuple(doc_number_tokens(hit[0]))
        if got != tuple(nums):
            out.append(u"§3 の行 %s の数の並び %s が留めた並び %s と違う" % (key[:12], u",".join(got), u",".join(nums)))
    for ln in bullets:
        if not any(key in ln for key, _ in SEC3_LINES):
            out.append(u"§3 に留めていない行: %s" % ln[:20])
    for p in SEC3_PHRASES:
        if p not in s:
            out.append(u"§3 に字が無い: %s" % p)
    # 文書の中の自己整合(記録には欄が無い数どうしの足し算・差)
    nums = dict((k, v) for k, v in zip((u"c", u"cn", u"n", u"nonempty", u"a", u"b"), (2100, 2037, 160, 349, 1479, 621)))
    if nums[u"a"] + nums[u"b"] != nums[u"c"] or not (nums[u"cn"] <= nums[u"c"]) or not (Fraction(65, 100) <= Fraction(nums[u"a"], nums[u"c"]) <= Fraction(75, 100)):
        out.append(u"§3 の数どうし(1479 + 621 = 2100・「7 割ほど」)が合わない")
    # 記録にも在る数との照らし(2197・2130・160・8)
    S = c.rec[AGG][K_STAGE]
    if not (u"W1 %d を" % S[B3]["HT"]["W1"] in s and u"この 2100 とは %d ずれる" % (S[CTX]["HT"]["W1"] - 2100) in s and u"W1 %d は" % S[CTX]["HT"]["W1"] in s
            and u"`name` が違う fact %d" % S[NAME]["HT"]["W1"] in s and u"`unitRef` が違う fact %d" % S[UNIT]["HT"]["W1"] in s):
        out.append(u"§3 の 2197・2130・160・8・30 が記録(§2 の数)と合わない")
    # §3 の数は §3 の外に出ない(主張として使われない)
    rest = outside_sec3(c)
    toks = set(t.replace(u",", u"") for ln in rest.splitlines() for t in doc_number_tokens(ln))
    for n in SEC3_ONLY:
        if n in toks:
            out.append(u"記録に欄の無い数 %s が §3 の外に出ている" % n)
    if u"7 割" in rest or u"その大半は文脈の名の違い" in rest:
        out.append(u"§3 の「7 割」が §3 の外で主張として出ている")
    return out


def affirm_problems(c):
    u"""「作れる」「専用の道具が要らない」「人が書ける」「AI が書ける」「検査に通る」は、言えないことの引用(「…」の中)にしか無い。引用の在る行には「言えない」か「読まない」が在る。"""
    out = []
    for i, ln in enumerate(c.doc.splitlines(), 1):
        if QUOTED.search(ln) and not any(w in ln for w in (u"言えない", u"読まない", u"示していない")):
            out.append(u"文書の %d 行目が引用の主張を否定の外で書いている" % i)
        rest = QUOTED.sub(u"", ln)
        for w in AFFIRM_WORDS:
            if re.search(w, rest):
                out.append(u"文書の %d 行目に引用の外の字: %s" % (i, w))
    return out


def phrase_problems(c):
    doc = plain(c.doc)
    return [u"文書に要点の字が無い: %s" % p for p in PHRASES if p not in doc]


def head_problems(c):
    head = plain(c.doc.split(u"## §1")[0])
    out = [u"文書の頭(§1 の前)に無い: %s" % p for p in HEAD_PHRASES if p not in head]
    sec7 = section(c.seal, u"## §7 ", None)
    lines = [plain(ln[2:].strip()) for ln in sec7.splitlines() if ln.startswith(u"- ")]
    for ln in lines:
        if ln not in head:
            out.append(u"封 §7 の限界の 1 本が文書の頭に無い: %s" % ln[:20])
    if u"「XBRL を作れる」「EDINET の検査に通る」「専用の道具が要らない」「AI が書ける」は、この便からは言えない" not in head:
        out.append(u"文書の頭の否定の一覧が無い")
    return out


def forbidden_problems(c):
    out = [u"文書に禁止語: %s" % w for w in FORBIDDEN_WORDS if w in c.doc]
    scan = re.sub(r"(?<![0-9A-Za-z])[0-9a-f]{8}(?![0-9A-Za-z])", u" ", c.doc)
    if WG.DOCID_FORM.search(scan):
        out.append(u"文書に docID の形が在る")
    if WG.ECODE_FORM.search(scan):
        out.append(u"文書に EDINET コードの形が在る")
    return out


def doc_commit_problems(c):
    out = []
    for w in DOC_COMMITS:
        if w not in c.doc:
            out.append(u"文書に commit の字が無い: %s" % w)
    if not set(re.findall(r"(?<![0-9A-Za-z])[0-9a-f]{8}(?![0-9A-Za-z])", c.doc)) <= set(DOC_COMMITS):
        out.append(u"文書が知らない commit の字を書いている")
    return out


CHECKS = collections.OrderedDict([
    (u"sha", sha_problems), (u"recount", recount_problems), (u"clean", record_clean_problems), (u"bound", bound_problems),
    (u"verdict", verdict_problems), (u"numbers", doc_number_problems), (u"frag", fragment_problems), (u"resid", residual_problems), (u"sanity", sanity_problems),
    (u"sec3", sec3_problems), (u"affirm", affirm_problems), (u"phrases", phrase_problems), (u"head", head_problems), (u"forbidden", forbidden_problems), (u"commits", doc_commit_problems)])


# ======================================================================================================
def blob_problems(root, prefix, at):
    return WG.blob_problems(root, prefix, at)


def commit_problems(root=REPO):
    u"""文書が書く 3 つの commit が実の履歴と合う: 封は 4ee140d2・script と封の門は 77662224・記録は 861879cb。"""
    out = []
    for rel, want in HISTORY.items():
        r = subprocess.run(["git", "-C", root, "log", "--format=%H", "--reverse", "--", PREFIX + rel], stdout=subprocess.PIPE, universal_newlines=True)
        got = [x for x in r.stdout.split() if x]
        if len(got) != len(want) or any(not g.startswith(w) for g, w in zip(got, want)):
            out.append(u"%s の履歴が文書の書く commit %s と違う" % (rel, u"・".join(want)))
    return out


def git_problems(root=REPO):
    out = []
    out.extend(SG.seal_history_problems(root))
    out.extend(SG.engine_zero_problems(root))
    out.extend(blob_problems(root, PREFIX, BLOB_AT))
    out.extend(commit_problems(root))
    return out


def order_problems_real(root=REPO):
    u"""封 ⊏ script と封の門 ⊏ 記録 ⊏ 結果の文書と門。未 commit は赤。"""
    out = list(PR.order_problems(root, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, [SCRIPT_REL, SEAL_GATE_REL], [RECORD_REL, DOC_REL, GATE_REL]))
    for rel in (SCRIPT_REL, SEAL_GATE_REL):
        added = PR.added_commits(root, PREFIX + rel)
        if len(added) != 1 or not added[0].startswith(SCRIPT_COMMIT_SHORT):
            out.append(u"%s を足した commit が %s でない" % (rel, SCRIPT_COMMIT_SHORT))
        rc, last = PR.git_in(root, "log", "-1", "--format=%H", "--", PREFIX + rel)
        if not last.startswith(SCRIPT_COMMIT_SHORT):
            out.append(u"%s の最後の commit が %s でない(記録を書いた後に変わった)" % (rel, SCRIPT_COMMIT_SHORT))
    rec = PR.added_commits(root, PREFIX + RECORD_REL)
    if len(rec) != 1 or not rec[0].startswith(RECORD_COMMIT_SHORT):
        out.append(u"記録を足した commit が %s でない" % RECORD_COMMIT_SHORT)
    else:
        rc, lastrec = PR.git_in(root, "log", "-1", "--format=%H", "--", PREFIX + RECORD_REL)
        if not lastrec.startswith(RECORD_COMMIT_SHORT):
            out.append(u"記録の最後の commit が %s でない" % RECORD_COMMIT_SHORT)
        for rel in (SCRIPT_REL, SEAL_GATE_REL):
            added = PR.added_commits(root, PREFIX + rel)
            if added and not PR.is_anc(root, added[0], rec[0]):
                out.append(u"記録が %s より前" % rel)
    return out


# ======================================================================================================
PREDICT = u"""
(変異を実行する前に書いた予測。右 = 赤になるべき検査。「整合」= 書類ごとの数から集計・予測の欄を作り直し、recount は緑のまま当たり外れ・向きだけが変わる)
M1  記録の sha256 の写しを違う値に                                                       -> sha
M2  記録の「この script の sha256」を 1 字替える                                         -> sha
M3  記録の限界の欄の 1 行を消す                                                          -> sha
M4  記録の封の commit の欄を 1 字替える                                                  -> sha
M5  便 XY0 の記録の sha256 の写しを違う値に                                              -> sha
M6  書類 10 の段 HT・束 3 の U を 1 増やす(群・率は直さない)                              -> recount
M7  集計の段 HT・束 3 の W1 を 1 増やす(書類ごとは直さない)                                -> recount
M8  書類 10 の段 F・束 3 の U を 1 減らす(段 F = 段 HT + 落ちた fact の関係が崩れる)         -> recount
M9  書類 10 の `name` だけ・段 HT の U を束 3 の U より小さくする(写すと減らない、が崩れる)     -> recount
M10 材料の組の数 63 → 64                                                                 -> recount
M11 書類 10 の U の率の欄を 0.1 ずらす                                                    -> recount
M12 予測の欄 XZ0-2 の行を 1 増やす                                                        -> recount
M13 予測の欄 XZ0-8 の 95% 以上の書類を 1 増やす                                           -> recount
M14 集計の落ちた fact の数を 1 増やす                                                     -> recount
M15 先に疑う旗の 1 つを True にする                                                       -> recount
M16 書類 10 の空の欄の fact の数を 1 増やす(束 5 の分母が崩れる)                           -> recount
M17 書類 10 の段 H の N を段 HT の N より大きくする                                        -> recount
M18 記録に docid の欄を足す                                                              -> clean
M19 記録に EDINET コードの形の字を足す                                                    -> clean
M20 記録に日付の形の字を足す                                                              -> clean
M21 封の写しから XZ0-2 の境の字を消す                                                     -> bound
M22 封の写しから旗の「N が 30% を超えた」を消す                                            -> bound
M23 封の写しから §6 の「XZ0-1 と XZ0-2 が両方当たりなら…」を消す                          -> bound
M24 封の写しから §6 の「W1 の率は…2 通りで書く」を消す                                     -> bound
M25 封の写しから §0 の「並びの頭の 1 組だけ」を消す                                        -> bound
M26 文書の XZ0-2 の判定「外れ」を「当たり」に                                              -> verdict
M27 文書の XZ0-1 の判定「当たり」を「外れ」に                                              -> verdict
M28 文書の件数の行 当たり 4・外れ 4 → 当たり 5・外れ 3                                    -> verdict
M29 頭の「判定した 8 本は 当たり 4・外れ 4(…が外れ)」の外れの名から XZ0-6 を消す           -> verdict・frag
M30 文書の XZ0-2 のセル 2197/64534(3.4%) → (3.5%)                                      -> verdict・frag
M31 文書の XZ0-6 のセルの差「−2.4」→「−1.4」                                              -> verdict
M32 文書の XZ0-6 の判定「外れ」を「当たり」に(差 −2.43 は外れ)                              -> verdict
M33 文書の XZ0-1 の予測の字「70% 以上 86% 以下」を「70% 以上 87% 以下」に                  -> verdict
M34 §5 の「次の便は司令塔からは示さず、人間に返す」を「次の便の候補 (i) を示す」に            -> verdict
M35 §5 に「(ii) 」の見出しを足す                                                           -> verdict
M36 XZ0-2 の行の「(主)」を消す                                                           -> verdict
M37 XZ0-4 の行に「(主)」を足す                                                           -> verdict
M38 自己点検の「どれも立っていない」を「1 つ立っている」に                                  -> verdict
M39 自己点検の「N が 30% を超えた」を「N が 20% を超えた」に                              -> verdict
M40 頭の「**主の予測の 1 本(XZ0-2)は外れ。**」を「(XZ0-1)」に                            -> verdict
M41 §1 の XZ0-4 の外れ方「W1 の側(4.2%)が外」を「U の側(+1.3 ポイント)が外」に            -> verdict
M42 整合: XZ0-1 が 70% 未満になるよう段 HT・段 F の U を A へ移す(下に外れ)                  -> verdict
M43 整合: XZ0-2 を当たりにする(W1 を U へ移して 2.5% 以下に)                               -> verdict
M44 整合: 段 HT の N と X の合計を 20% 超にして XZ0-3 を外れに(U から N へ)                   -> verdict
M45 整合: 段 F の W1 を 3.5% 以下にして XZ0-4 を当たりに                                    -> verdict
M46 整合: 段 H の U を段 HT の U の近くまで上げて XZ0-5 を外れに                           -> verdict
M47 整合: 束 5 の U を束 3 に揃えて XZ0-6 を当たりに                                       -> verdict
M48 整合: contextRef だけの U を name だけの U 以上にして XZ0-7 を当たりに                  -> verdict
M49 整合: 95% 以上の書類を 4 本にして XZ0-8 を外れに                                       -> verdict
M50 整合: 段 HT の U を 95% 超にして旗が立つ                                                -> verdict
M51 整合: 段 HT の N を 30% 超にして旗が立つ                                                -> verdict
M52 整合: name だけの U を 70% 未満にして旗が立つ                                          -> verdict
M53 整合: 行の外の fact を 5% 超にして旗が立つ                                              -> verdict
M54 文書の「63 本のうち 1 本」を「63 本のうち 2 本」に                                     -> frag
M55 文書の「W1 は `contextRef` だけで 2130」を 2131 に                                     -> frag・numbers・sec3
M56 文書の「ほぼ文脈の側」の頭の言い切りを「ほぼ要素の名の側」に                            -> frag
M57 文書の「25 個に 1 個ほど」を「250 個に 1 個ほど」に                                    -> frag・resid
M58 文書の「8 割ほどの fact」を「5 割ほどの fact」に                                       -> frag
M59 文書の「「そのまま通してよい下書き」ではなく」を「そのまま通してよい下書きで」に           -> frag
M60 文書の「その 4 倍近く」を「その 2 倍近く」に                                          -> frag
M61 文書の「W1 の全部 2197 の半分を超える」を「半分に満たない」に                          -> frag
M62 文書の「表の番号を外して拾い直すと、831 が決まるが、黙って違う fact が 540 増える」の 540 を減る向きに  -> frag
M63 文書の「最小 7.6%」を 7.7% に                                                         -> frag・numbers
M64 文書の「95% 以上が 1 本」を「95% 以上が 2 本」に                                        -> frag
M65 文書の「W1 が 1 つ以上在る書類は 57 本」を 58 本に                                      -> frag
M66 文書の「便 XY0 の…87.3%」を 87.4% に                                                  -> frag・numbers
M67 文書の §2 の段 HT の行 51290(79.5%) を 51291(79.5%) に                                 -> frag・numbers
M68 文書の「便 XY0 の…並べて差を読まない」を「並べて差を読む」に                           -> frag
M69 文書に 9999 の言い切りを §3 の外へ足す                                                  -> numbers
M70 文書に「48%」の言い切りを足す                                                          -> numbers・resid
M71 §3 の見出しの「記録に欄の無い読み」を消す                                               -> sec3
M72 §3 の 2037 を 2038 に                                                                  -> sec3
M73 §3 の「1479」を「1480」に(足して 2100 にならない)                                      -> sec3
M74 §3 の「直せるとも直せないとも、この便からは言えない」を消す                              -> sec3
M75 §3 に 3 桁の数を足した行                                                               -> sec3
M76 §3 の外に「2100」を足す                                                                -> sec3・numbers
M77 §3 の外に「7 割」を足す                                                                -> sec3
M78 文書に「XBRL を作れる。」を引用の外で足す                                               -> affirm
M79 文書に「専用の道具が要らない。」を足す                                                  -> affirm
M80 文書に「AI が書ける。」を足す                                                          -> affirm
M81 文書に「人が書ける。」を足す                                                           -> affirm
M82 文書に「EDINET の検査に通る。」を足す                                                   -> affirm
M83 引用の行から「言えない」「読まない」を全部消す                                          -> affirm
M84 §5 の「言えないこと」を消す                                                           -> phrases
M85 文書の「文脈を別の手段で確かめる段が要る」を消す                                          -> phrases・frag
M86 頭の限界「前の年の XBRL が在る会社にしか使えない」を消す                                -> head
M87 頭の限界「63 組は無作為ではない」を消す                                                -> head
M88 頭の限界「文脈は `contextRef` の字(名)で比べる」を消す                                 -> head
M89 頭の限界「どのセルに fact を置くか」を消す                                              -> head
M90 頭の「(封 §0 の申告)」の字を消す                                                      -> head
M91 頭の「先に負けと限界を書く」を消す                                                     -> head
M92 頭の「LLM の席は呼んでいない」を消す                                                   -> head
M93 頭の「この便の U は「上の限り」に近い読み」を消す                                       -> head
M94 頭の「頭の 1 組は合計を代表していなかった」を消す                                       -> head
M95 文書に「保証」を足す                                                                  -> forbidden
M96 文書に docID の形を足す                                                               -> forbidden
M97 文書の commit の字 861879cb を 1 字替える(全部の数字の 77662224 も同じく)                -> commits
M98 文書の commit の字 77662224 を 77662225 に(全部が数字の commit)                        -> commits
M99 文書に知らない commit の字を足す                                                      -> commits
M100 整合: 段 HT の W1 を contextRef だけの W1 より小さくして「ほぼ文脈の側」を崩す             -> sanity
M101 整合: 束 5 の U を束 3 の U より大きくして「桁を足すと減る」を崩す(XZ0-6 は当たりへ)       -> sanity・verdict
(2026-11-22 追記。監査 REVISE の直し。§5 の候補を消した後、変異を足す前に書いた予測。M35 は定義を替えた)
M35 §5 の「封 §6 の決め」の行の後ろに字下げした「  - (ii) …」の行を足す                          -> verdict
M102 §5 の「封 §6 の決め」の行の後ろに「  - (d) …」の選択肢の行を足す                           -> verdict
M103 §5 の最後の行の後ろに、箇条書きでも候補の語でもない案の 1 行を足す                         -> verdict(最後の行の検査)
M104 §5 の最後の行の前に「  - (a) W1 の中身を分ける」の行を戻す                                  -> verdict
M105 「文脈の側」を「文脈(期・連結か個別か・軸)の側」に戻す                                     -> frag
M106 最後の行の「次の便は人間が決める。」を「次の便の候補は人間が決める。」に                      -> verdict(「候補」の語)
M107 最後の行の前に「0 USD の便」「有料」の字を含む案の行を足す                                    -> verdict
"""


def doc_at(rec, n):
    return rec[u"書類"][n - 1]


def rep(c, old, new, attr="doc", count=1):
    s = getattr(c, attr)
    assert old in s, old
    setattr(c, attr, s.replace(old, new, count))


def add_before_last5(c, text):
    ls = c.doc.rstrip(u"\n").split(u"\n")
    ls.insert(len(ls) - 1, text)
    c.doc = u"\n".join(ls) + u"\n"


def add_doc(c, text):
    c.doc = c.doc + u"\n" + text + u"\n"


def drop_all(c, phrase):
    assert phrase in c.doc, phrase
    c.doc = c.doc.replace(phrase, u"X")


def fix_attrs(d):
    u"""属性ごとの U が束 3 の U より少なくならないように、A・W1・W2 から U へ移す(整合の変異が保つ関係)。"""
    st = d[K_STAGE]
    for b in (NAME, CTX, UNIT):
        for s_ in STAGES:
            need = st[B3][s_][u"U"] - st[b][s_][u"U"]
            for k in (u"A", u"W1", u"W2"):
                t = min(max(need, 0), st[b][s_][k])
                st[b][s_][k] -= t
                st[b][s_][u"U"] += t
                need -= t


def rebuild(rec):
    u"""書類ごとの数から集計と予測の欄を作り直す(整合の変異用)。旗も作り直す。"""
    docs = rec[u"書類"]
    for d in docs:
        fix_attrs(d)
    new = totals(docs)
    for k, v in new.items():
        rec[AGG][k] = copy.deepcopy(v)
    rec[PRED_KEY] = pred_expected(rec)
    for f, e in zip(rec[FLAG_KEY].values(), flags_expected(rec)):
        f[u"fact"], f[u"分母"], f[u"旗"] = e
    for d in docs:
        if d[K_FACTS] > 0:
            d[K_RATE] = float(pct(d[K_STAGE][B3]["HT"]["U"], d[K_FACTS]))


def take(d, bundle, stage, dst, n, order):
    u"""束 bundle・段 stage の order の類から合わせて n を dst へ移す。移せた数を返す。"""
    left = n
    for k in order:
        t = min(left, d[K_STAGE][bundle][stage][k])
        d[K_STAGE][bundle][stage][k] -= t
        d[K_STAGE][bundle][stage][dst] += t
        left -= t
    return n - left


def shift(d, bundle, stages, a, b, n):
    u"""書類 d の束 bundle の段 stages で類 a から類 b へ n fact 移す。"""
    for st in stages:
        d[K_STAGE][bundle][st][a] -= n
        d[K_STAGE][bundle][st][b] += n


def shift3(d, a, b, n):
    u"""束 3 の段 HT と段 F で類 a から b へ n 移す(段 F = 段 HT + 落ちた fact の関係を保つ。a・b は N 以外)。"""
    shift(d, B3, ("HT", "F"), a, b, n)


def shift_all(c, a, b, frac_num, frac_den):
    for d in c.rec[u"書類"]:
        n = d[K_STAGE][B3]["HT"][a] * frac_num // frac_den
        shift3(d, a, b, n)
    rebuild(c.rec)


def to_n(d, n):
    u"""n fact を「前の年に置き場が無い(N)」へ移す(整合: 段 HT・段 H・段 F の N・落ちた fact の N・段 F = 段 HT + 落ちた fact・段 H の N = 段 F の N を保つ)。
    束 3 と 3 つの属性(属性は束 3 と同じ N)で、段 HT と段 F は U から、段 H は U・A・W1・W2 の順に取る。"""
    for b in (B3, NAME, CTX, UNIT):
        shift(d, b, ("HT", "F"), u"U", u"N", n)
        take(d, b, "H", u"N", n, (u"U", u"A", u"W1", u"W2"))
    d[K_FALLC][u"N"] += n
    d[K_FALL] += n


def to_all_known(d):
    u"""全部を U にする(整合: 置き場の無い fact も、候補が 2 つ以上の fact も、黙って違う fact も無い。X は動かさない)。"""
    for b in (B3, NAME, CTX, UNIT):
        for st in STAGES:
            cl = d[K_STAGE][b][st]
            x, tot = cl[u"X"], sum(cl.values()) - cl[u"X"]
            for k in CLS:
                cl[k] = 0
            cl[u"X"], cl[u"U"] = x, tot
    for k in CLS:
        d[K_FALLC][k] = 0
    d[K_FALL] = 0


def m_u_low(c):
    u"""XZ0-1 を下に外す: 束 3 の U を A へ 2 割移す(段 HT・段 F。属性ごとの U ≥ 束 3 の U は保たれる)。"""
    shift_all(c, u"U", u"A", 2, 10)


def m_w1_to_u(c):
    u"""XZ0-2 を当たりにする: 束 3 の W1 を U へ移す(段 HT・段 F)。"""
    for d in c.rec[u"書類"]:
        shift3(d, u"W1", u"U", d[K_STAGE][B3]["HT"][u"W1"] * 3 // 4)
    rebuild(c.rec)


def m_n_high(c):
    u"""XZ0-3 を外す: 段 HT の N と X の合計を 20% 超にする(U から N へ)。"""
    for d in c.rec[u"書類"]:
        to_n(d, d[K_STAGE][B3]["HT"][u"U"] // 5)
    rebuild(c.rec)


def m_f_w1_low(c):
    u"""XZ0-4 を当たりにする: 落ちた fact の W1 を U へ移して、段 F の W1 を段 HT の W1 と同じ(3.4%)にする。"""
    for d in c.rec[u"書類"]:
        fc = d[K_FALLC]
        t = fc[u"W1"]
        fc[u"W1"] -= t
        fc[u"U"] += t
        shift(d, B3, ("F",), u"W1", u"U", t)
    rebuild(c.rec)


def m_h_up(c):
    u"""XZ0-5 を外す: 段 H の U を段 HT の U の近くまで上げる(A から U へ)。"""
    for d in c.rec[u"書類"]:
        h, ht = d[K_STAGE][B3]["H"], d[K_STAGE][B3]["HT"]
        take(d, B3, "H", u"U", max(0, ht[u"U"] - h[u"U"]), (u"A",))
    rebuild(c.rec)


def m_b5_equal(c):
    u"""XZ0-6 を当たりにする: 束 5 の段 HT の U を束 3(空の欄でない fact)の U に近づける(A・W1・W2 から U へ。N は動かさない)。"""
    for d in c.rec[u"書類"]:
        take(d, B5, "HT", u"U", max(0, d[K_STAGE][B3NN]["HT"][u"U"] - d[K_STAGE][B5]["HT"][u"U"]), (u"A", u"W1", u"W2"))
    rebuild(c.rec)


def m_b5_over(c):
    u"""束 5 の U を束 3 より多くする(「桁を足すと減る」を崩す。XZ0-6 は当たり)。"""
    for d in c.rec[u"書類"]:
        take(d, B5, "HT", u"U", max(0, d[K_STAGE][B3NN]["HT"][u"U"] - d[K_STAGE][B5]["HT"][u"U"]) + 100, (u"A", u"W1", u"W2"))
    rebuild(c.rec)
    s = c.rec[AGG][K_STAGE]
    assert s[B5]["HT"][u"U"] > s[B3NN]["HT"][u"U"]


def m_ctx_over_name(c):
    u"""XZ0-7 を当たりにする: contextRef だけの U を name だけの U 以上にする(A・W1・W2 から U へ)。"""
    for d in c.rec[u"書類"]:
        ctx, nm = d[K_STAGE][CTX]["HT"], d[K_STAGE][NAME]["HT"]
        take(d, CTX, "HT", u"U", max(0, nm[u"U"] - ctx[u"U"]) + 1, (u"A", u"W1", u"W2"))
    rebuild(c.rec)


def m_docs95_four(c):
    u"""XZ0-8 を外す: 段 HT・束 3 の U の率が 95% 以上の書類を 4 本にする(最も高い 4 本の U を fact の 96% にする。A・W1・W2 から)。"""
    docs = [d for d in c.rec[u"書類"] if d[K_FACTS] > 0]
    docs.sort(key=lambda d: Fraction(d[K_STAGE][B3]["HT"][u"U"], d[K_FACTS]), reverse=True)
    for d in docs[:4]:
        ht = d[K_STAGE][B3]["HT"]
        need = (d[K_FACTS] * 96 + 99) // 100 - ht[u"U"]
        for k in (u"A", u"W1", u"W2"):
            t = min(max(need, 0), ht[k])
            shift3(d, k, u"U", t)
            need -= t
    rebuild(c.rec)


def m_u_over95(c):
    u"""段 HT の U を 95% 超にする(整合。全部を U にする)。"""
    for d in c.rec[u"書類"]:
        to_all_known(d)
    rebuild(c.rec)


def m_n_over30(c):
    u"""段 HT の N を 30% 超にする(整合。U から N へ)。"""
    for d in c.rec[u"書類"]:
        to_n(d, d[K_STAGE][B3]["HT"][u"U"] // 2)
    rebuild(c.rec)


def m_name_u_low(c):
    u"""name だけの U を 70% 未満にする(整合。束 3 の U より少なくならないよう、束 3 の U も同じだけ A へ)。"""
    for d in c.rec[u"書類"]:
        n = d[K_STAGE][NAME]["HT"][u"U"] // 3
        shift(d, NAME, ("HT", "F"), u"U", u"A", n)
        shift(d, B3, ("HT", "F"), u"U", u"A", min(d[K_STAGE][B3]["HT"][u"U"], n))
    rebuild(c.rec)


def m_out_over5(c):
    u"""行の外の fact を 5% 超にする(整合)。"""
    for d in c.rec[u"書類"]:
        d[K_OUT] = d[K_FACTS] // 10
    rebuild(c.rec)


def m_w1_below_ctx(c):
    u"""束 3 の W1 を contextRef だけの W1 より少なくする(「ほぼ文脈の側」を崩す。W1 を A へ)。"""
    for d in c.rec[u"書類"]:
        shift3(d, u"W1", u"A", d[K_STAGE][B3]["HT"][u"W1"] * 3 // 4)
    rebuild(c.rec)


def m_drop_quote_negation(c):
    lines = []
    for ln in c.doc.splitlines():
        if QUOTED.search(ln):
            for w in (u"言えないこと", u"言えない", u"読まない", u"示していない"):
                ln = ln.replace(w, u"X")
        lines.append(ln)
    c.doc = u"\n".join(lines)


def m_drop_seal(c, phrase):
    assert phrase in c.seal, phrase
    c.seal = c.seal.replace(phrase, u"X", 1)


def m_nil_plus(c):
    d = doc_at(c.rec, 10)
    d[K_NIL] += 1


def m_h_over_ht(c):
    d = doc_at(c.rec, 10)
    for b in (B3,):
        d[K_STAGE][b]["H"][u"N"] = d[K_STAGE][b]["HT"][u"N"] + 1
        d[K_STAGE][b]["H"][u"U"] -= 1


def m_name_below(c):
    d = doc_at(c.rec, 10)
    st = d[K_STAGE]
    st[NAME]["HT"][u"U"] = st[B3]["HT"][u"U"] - 1
    st[NAME]["HT"][u"A"] += 1


def m_flag_true(c):
    k = list(c.rec[FLAG_KEY])[0]
    c.rec[FLAG_KEY][k][u"旗"] = True


def m_doc10_u_plus(c):
    d = doc_at(c.rec, 10)
    d[K_STAGE][B3]["HT"][u"U"] += 1


def m_f_u_minus(c):
    d = doc_at(c.rec, 10)
    d[K_STAGE][B3]["F"][u"U"] -= 1


MUTATIONS = (
    (u"M1 記録の sha256 の写しを違う値に", lambda c: c.shas.__setitem__(RECORD_REL, u"0" * 64), (u"sha",)),
    (u"M2 記録の script の sha256 を 1 字替える", lambda c: c.rec.__setitem__(u"この script の sha256", u"f" + c.rec[u"この script の sha256"][1:]), (u"sha",)),
    (u"M3 記録の限界の欄の 1 行を消す", lambda c: c.rec.__setitem__(u"限界", c.rec[u"限界"][1:]), (u"sha",)),
    (u"M4 記録の封の commit の欄を 1 字替える", lambda c: c.rec.__setitem__(u"封の commit", u"0" + c.rec[u"封の commit"][1:]), (u"sha",)),
    (u"M5 便 XY0 の記録の sha256 の写しを違う値に", lambda c: c.shas.__setitem__(XY0_RECORD_REL, u"0" * 64), (u"sha",)),
    (u"M6 書類 10 の段 HT・束 3 の U を 1 増やす", m_doc10_u_plus, (u"recount",)),
    (u"M7 集計の段 HT・束 3 の W1 を 1 増やす", lambda c: c.rec[AGG][K_STAGE][B3]["HT"].__setitem__("W1", c.rec[AGG][K_STAGE][B3]["HT"]["W1"] + 1), (u"recount",)),
    (u"M8 書類 10 の段 F・束 3 の U を 1 減らす", m_f_u_minus, (u"recount",)),
    (u"M9 書類 10 の name だけ・段 HT の U を束 3 の U より小さくする", m_name_below, (u"recount",)),
    (u"M10 材料の組の数を 64 に", lambda c: c.rec[u"材料"].__setitem__(u"組の数", 64), (u"recount",)),
    (u"M11 書類 10 の U の率の欄を 0.1 ずらす", lambda c: doc_at(c.rec, 10).__setitem__(K_RATE, doc_at(c.rec, 10)[K_RATE] + 0.1), (u"recount",)),
    (u"M12 予測の欄 XZ0-2 の fact を 1 増やす", lambda c: c.rec[PRED_KEY][PK["2"]].__setitem__(u"fact", c.rec[PRED_KEY][PK["2"]][u"fact"] + 1), (u"recount",)),
    (u"M13 予測の欄 XZ0-8 の 95% 以上の書類を 1 増やす", lambda c: c.rec[PRED_KEY][PK["8"]].__setitem__(u"95% 以上の書類", c.rec[PRED_KEY][PK["8"]][u"95% 以上の書類"] + 1), (u"recount",)),
    (u"M14 集計の落ちた fact の数を 1 増やす", lambda c: c.rec[AGG].__setitem__(K_FALL, c.rec[AGG][K_FALL] + 1), (u"recount",)),
    (u"M15 先に疑う旗の 1 つを True にする", m_flag_true, (u"recount",)),
    (u"M16 書類 10 の空の欄の fact の数を 1 増やす", m_nil_plus, (u"recount",)),
    (u"M17 書類 10 の段 H の N を段 HT の N より大きくする", m_h_over_ht, (u"recount",)),
    (u"M18 記録に docid の欄を足す", lambda c: c.rec.__setitem__(u"docID", u"S100ABCD"), (u"clean",)),
    (u"M19 記録に EDINET コードの形の字を足す", lambda c: c.rec.__setitem__(u"メモ", u"E01234"), (u"clean",)),
    (u"M20 記録に日付の形の字を足す", lambda c: c.rec.__setitem__(u"メモ", u"2025-03-31"), (u"clean",)),
    (u"M21 封の写しから XZ0-2 の境の字を消す", lambda c: m_drop_seal(c, u"段 HT・束 3 の類 W1 は 2.5% 以下"), (u"bound",)),
    (u"M22 封の写しから旗の「N が 30% を超えた」を消す", lambda c: m_drop_seal(c, u"N が 30% を超えた"), (u"bound",)),
    (u"M23 封の写しから §6 の「XZ0-1 と XZ0-2 が両方当たりなら…」を消す", lambda c: m_drop_seal(c, u"XZ0-1 と XZ0-2 が両方当たりなら、次の便の候補を人間に示す"), (u"bound",)),
    (u"M24 封の写しから §6 の「W1 の率は…2 通りで書く」を消す", lambda c: m_drop_seal(c, u"W1 の率は、分母を U + W1 にしたものと fact の全部にしたものの 2 通りで書く"), (u"bound",)),
    (u"M25 封の写しから §0 の「並びの頭の 1 組だけ」を消す", lambda c: m_drop_seal(c, u"並びの頭の 1 組だけ"), (u"bound",)),
    (u"M26 文書の XZ0-2 の判定「外れ」を「当たり」に", lambda c: rep(c, u"2197/64534(3.4%) | 外れ |", u"2197/64534(3.4%) | 当たり |"), (u"verdict",)),
    (u"M27 文書の XZ0-1 の判定「当たり」を「外れ」に", lambda c: rep(c, u"51290/64534(79.5%) | 当たり |", u"51290/64534(79.5%) | 外れ |"), (u"verdict",)),
    (u"M28 文書の件数の行を 当たり 5・外れ 3 に", lambda c: rep(c, u"- 当たり 4・外れ 4。", u"- 当たり 5・外れ 3。"), (u"verdict",)),
    (u"M29 頭の外れの名から XZ0-6 を消す", lambda c: rep(c, u"(XZ0-2・XZ0-4・XZ0-6・XZ0-7 が外れ)", u"(XZ0-2・XZ0-4・XZ0-7 が外れ)"), (u"verdict", u"frag")),
    (u"M30 文書の XZ0-2 のセル 3.4% → 3.5%", lambda c: rep(c, u"| 2197/64534(3.4%) | 外れ |", u"| 2197/64534(3.5%) | 外れ |"), (u"verdict",)),
    (u"M31 文書の XZ0-6 のセルの差「−2.4」を「−1.4」に", lambda c: rep(c, u"差 −2.4 ポイント", u"差 −1.4 ポイント"), (u"verdict",)),
    (u"M32 文書の XZ0-6 の判定「外れ」を「当たり」に", lambda c: rep(c, u"差 −2.4 ポイント | 外れ |", u"差 −2.4 ポイント | 当たり |"), (u"verdict",)),
    (u"M33 文書の XZ0-1 の予測の字を「70% 以上 87% 以下」に", lambda c: rep(c, u"段 HT・束 3 の類 U は 70% 以上 86% 以下", u"段 HT・束 3 の類 U は 70% 以上 87% 以下"), (u"verdict",)),
    (u"M34 §5 の「次の便は司令塔からは示さず、人間に返す」を「次の便の候補 (i) を示す」に", lambda c: rep(c, u"次の便は司令塔からは示さず、人間に返す。", u"次の便の候補 (i) を示す。"), (u"verdict",)),
    (u"M35 §5 の決めの行の後ろに「  - (ii) …」の行を足す", lambda c: add_before_last5(c, u"  - (ii) 類 N・A・X・W2 の fact だけを AI の席へ送る"), (u"verdict",)),
    (u"M36 XZ0-2 の行の「(主)」を消す", lambda c: rep(c, u"| XZ0-2(主) |", u"| XZ0-2 |"), (u"verdict",)),
    (u"M37 XZ0-4 の行に「(主)」を足す", lambda c: rep(c, u"| XZ0-4 |", u"| XZ0-4(主) |"), (u"verdict",)),
    (u"M38 自己点検の「どれも立っていない」を「1 つ立っている」に", lambda c: rep(c, u"は、どれも立っていない。", u"は、1 つ立っている。"), (u"verdict",)),
    (u"M39 自己点検の「N が 30% を超えた」を「N が 20% を超えた」に", lambda c: rep(c, u"N が 30% を超えた・`name`", u"N が 20% を超えた・`name`"), (u"verdict",)),
    (u"M40 頭の「**主の予測の 1 本(XZ0-2)は外れ。**」を「(XZ0-1)」に", lambda c: rep(c, u"**主の予測の 1 本(XZ0-2)は外れ。**", u"**主の予測の 1 本(XZ0-1)は外れ。**"), (u"verdict",)),
    (u"M41 §1 の XZ0-4 の外れ方を「U の側が外」に替える", lambda c: rep(c, u"U の側(+1.3 ポイント)は予測の内で、W1 の側(4.2%)が外。", u"U の側(+1.3 ポイント)が外で、W1 の側(4.2%)は予測の内。"), (u"verdict",)),
    (u"M42 整合: 束 3 の U を A へ 2 割移して XZ0-1 が 70% 未満", m_u_low, (u"verdict",)),
    (u"M43 整合: W1 を U へ移して XZ0-2 を当たりに", m_w1_to_u, (u"verdict",)),
    (u"M44 整合: 段 HT の N と X の合計を 20% 超にして XZ0-3 を外れに", m_n_high, (u"verdict",)),
    (u"M45 整合: 段 F の W1 を 3.5% 以下にして XZ0-4 を当たりに", m_f_w1_low, (u"verdict",)),
    (u"M46 整合: 段 H の U を段 HT の近くまで上げて XZ0-5 を外れに", m_h_up, (u"verdict",)),
    (u"M47 整合: 束 5 の U を束 3 に揃えて XZ0-6 を当たりに", m_b5_equal, (u"verdict",)),
    (u"M48 整合: contextRef だけの U を name だけの U 以上にして XZ0-7 を当たりに", m_ctx_over_name, (u"verdict",)),
    (u"M49 整合: 95% 以上の書類を 4 本にして XZ0-8 を外れに", m_docs95_four, (u"verdict",)),
    (u"M50 整合: 段 HT の U を 95% 超にして旗が立つ", m_u_over95, (u"verdict",)),
    (u"M51 整合: 段 HT の N を 30% 超にして旗が立つ", m_n_over30, (u"verdict",)),
    (u"M52 整合: name だけの U を 70% 未満にして旗が立つ", m_name_u_low, (u"verdict",)),
    (u"M53 整合: 行の外の fact を 5% 超にして旗が立つ", m_out_over5, (u"verdict",)),
    (u"M54 文書の「63 本のうち 1 本」を「63 本のうち 2 本」に", lambda c: rep(c, u"95% 以上は 63 本のうち 1 本", u"95% 以上は 63 本のうち 2 本"), (u"frag",)),
    (u"M55 文書の「`contextRef` だけで 2130」を 2131 に", lambda c: rep(c, u"`contextRef` だけで 2130", u"`contextRef` だけで 2131"), (u"frag",)),
    (u"M56 文書の頭の「ほぼ文脈の側」を「ほぼ要素の名の側」に", lambda c: rep(c, u"**黙って違うのは、ほぼ文脈の側。**", u"**黙って違うのは、ほぼ要素の名の側。**"), (u"frag",)),
    (u"M57 文書の「25 個に 1 個ほど」を「250 個に 1 個ほど」に", lambda c: rep(c, u"25 個に 1 個ほど", u"250 個に 1 個ほど"), (u"frag", u"resid")),
    (u"M58 文書の「8 割ほどの fact」を「5 割ほどの fact」に", lambda c: rep(c, u"8 割ほどの fact", u"5 割ほどの fact"), (u"frag",)),
    (u"M59 文書の「「そのまま通してよい下書き」ではなく」を肯定に", lambda c: rep(c, u"「そのまま通してよい下書き」ではなく", u"「そのまま通してよい下書き」で"), (u"frag",)),
    (u"M60 文書の「その 4 倍近く」を「その 2 倍近く」に", lambda c: rep(c, u"その 4 倍近くだった", u"その 2 倍近くだった"), (u"frag",)),
    (u"M61 文書の「半分を超える」を「半分に満たない」に", lambda c: rep(c, u"(W1 の全部 2197 の半分を超える)", u"(W1 の全部 2197 の半分に満たない)"), (u"frag",)),
    (u"M62 文書の「黙って違う fact が 540 増える」を「540 減る」に", lambda c: rep(c, u"黙って違う fact が 540 増える", u"黙って違う fact が 540 減る"), (u"frag",)),
    (u"M63 文書の「最小 7.6%」を 7.7% に", lambda c: rep(c, u"最小 7.6%・中央 84.4%・最大 95.3%。95% 以上は", u"最小 7.7%・中央 84.4%・最大 95.3%。95% 以上は"), (u"frag",)),
    (u"M64 文書の「95% 以上が 1 本」を「95% 以上が 2 本」に", lambda c: rep(c, u"95% 以上が 1 本。", u"95% 以上が 2 本。"), (u"frag",)),
    (u"M65 文書の「W1 が 1 つ以上在る書類は 57 本」を 58 本に", lambda c: rep(c, u"在る書類は 57 本", u"在る書類は 58 本"), (u"frag",)),
    (u"M66 文書の XY0 の「87.3%」を 87.4% に", lambda c: rep(c, u"正しい行 87.3%", u"正しい行 87.4%"), (u"frag", u"numbers")),
    (u"M67 文書の §2 の段 HT の行 51290(79.5%) を 51291(79.5%) に", lambda c: rep(c, u"| 51290(79.5%) |", u"| 51291(79.5%) |"), (u"frag", u"numbers")),
    (u"M68 文書の「並べて差を読まない」を「並べて差を読む」に", lambda c: rep(c, u"並べて差を読まない", u"並べて差を読む"), (u"frag",)),
    (u"M69 文書に 9999 の言い切りを §3 の外へ足す", lambda c: add_doc(c, u"9999 fact が決まった。"), (u"numbers",)),
    (u"M70 文書に「48%」の言い切りを足す", lambda c: add_doc(c, u"決まった fact は 48% だった。"), (u"numbers", u"resid")),
    (u"M71 §3 の見出しの「記録に欄の無い読み」を消す", lambda c: rep(c, u"## §3 記録の監査で見たこと(記録に欄の無い読み。", u"## §3 記録の監査で見たこと(X。"), (u"sec3",)),
    (u"M72 §3 の 2037 を 2038 に", lambda c: rep(c, u"2037", u"2038"), (u"sec3",)),
    (u"M73 §3 の「1479」を「1480」に", lambda c: rep(c, u"1479", u"1480"), (u"sec3",)),
    (u"M74 §3 の「直せるとも直せないとも、この便からは言えない」を消す", lambda c: rep(c, u"直せるとも直せないとも、この便からは言えない", u"X"), (u"sec3",)),
    (u"M75 §3 に 3 桁の数を足した行", lambda c: rep(c, u"## §4 ", u"- 足した行 321 件。\n\n## §4 "), (u"sec3",)),
    (u"M76 §3 の外に「2100」を足す", lambda c: add_doc(c, u"2100 fact が文脈の側。"), (u"sec3", u"numbers")),
    (u"M77 §3 の外に「7 割」を足す", lambda c: add_doc(c, u"その 7 割は期の語。"), (u"sec3",)),
    (u"M78 文書に「XBRL を作れる。」を引用の外で足す", lambda c: add_doc(c, u"XBRL を作れる。"), (u"affirm",)),
    (u"M79 文書に「専用の道具が要らない。」を足す", lambda c: add_doc(c, u"専用の道具が要らない。"), (u"affirm",)),
    (u"M80 文書に「AI が書ける。」を足す", lambda c: add_doc(c, u"AI が書ける。"), (u"affirm",)),
    (u"M81 文書に「人が書ける。」を足す", lambda c: add_doc(c, u"人が書ける。"), (u"affirm",)),
    (u"M82 文書に「EDINET の検査に通る。」を足す", lambda c: add_doc(c, u"EDINET の検査に通る。"), (u"affirm",)),
    (u"M83 引用の行から「言えない」「読まない」を全部消す", m_drop_quote_negation, (u"affirm",)),
    (u"M84 §5 の「言えないこと」を消す", lambda c: drop_all(c, u"言えないこと"), (u"phrases",)),
    (u"M85 文書の「文脈を別の手段で確かめる段が要る」を消す", lambda c: drop_all(c, u"文脈を別の手段で確かめる段が要る"), (u"phrases", u"frag")),
    (u"M86 頭の限界「前の年の XBRL が在る会社にしか使えない」を消す", lambda c: drop_all(c, u"前の年の XBRL が在る会社にしか使えない"), (u"head",)),
    (u"M87 頭の限界「63 組は無作為ではない」を消す", lambda c: drop_all(c, u"63 組は無作為ではない"), (u"head",)),
    (u"M88 頭の限界「文脈は `contextRef` の字(名)で比べる」を消す", lambda c: drop_all(c, u"文脈は `contextRef` の字(名)で比べる"), (u"head",)),
    (u"M89 頭の限界「どのセルに fact を置くか」を消す", lambda c: rep(c, u"どのセルに fact を置くか", u"X", count=1), (u"head",)),
    (u"M90 頭の「(封 §0 の申告)」を消す", lambda c: drop_all(c, u"(封 §0 の申告)"), (u"head",)),
    (u"M91 頭の「先に負けと限界を書く」を消す", lambda c: drop_all(c, u"先に負けと限界を書く"), (u"head",)),
    (u"M92 頭の「LLM の席は呼んでいない」を消す", lambda c: drop_all(c, u"LLM の席は呼んでいない"), (u"head",)),
    (u"M93 頭の「この便の U は「上の限り」に近い読み」を消す", lambda c: drop_all(c, u"この便の U は「上の限り」に近い読み"), (u"head",)),
    (u"M94 頭の「頭の 1 組は合計を代表していなかった」を消す", lambda c: drop_all(c, u"頭の 1 組は合計を代表していなかった"), (u"head",)),
    (u"M95 文書に「保証」を足す", lambda c: add_doc(c, u"保証する。"), (u"forbidden",)),
    (u"M96 文書に docID の形を足す", lambda c: add_doc(c, u"S100ABCD"), (u"forbidden",)),
    (u"M97 文書の commit の字 861879cb を 1 字替える", lambda c: rep(c, u"861879cb", u"861879cc", count=100), (u"commits",)),
    (u"M98 文書の commit の字 77662224 を 77662225 に", lambda c: rep(c, u"77662224", u"77662225", count=100), (u"commits",)),
    (u"M99 文書に知らない commit の字を足す", lambda c: add_doc(c, u"commit 1a2b3c4d。"), (u"commits",)),
    (u"M100 整合: 束 3 の W1 を contextRef だけの W1 より少なくして「ほぼ文脈の側」を崩す", m_w1_below_ctx, (u"sanity",)),
    (u"M101 整合: 束 5 の U を束 3 の U より多くして「桁を足すと減る」を崩す", m_b5_over, (u"sanity", u"verdict")),
    (u"M102 §5 の決めの行の後ろに「  - (d) …」の行を足す", lambda c: add_before_last5(c, u"  - (d) 前の年の写しをやめる"), (u"verdict",)),
    (u"M103 §5 の最後の行の後ろに案の 1 行を足す", lambda c: rep(c, u"次の便は人間が決める。\n", u"次の便は人間が決める。\n- 次は文脈だけを別の手段で決めるとよい。\n"), (u"verdict",)),
    (u"M104 §5 の最後の行の前に「  - (a) W1 の中身を分ける」を戻す", lambda c: add_before_last5(c, u"  - (a) W1 の中身を分ける"), (u"verdict",)),
    (u"M105 「文脈の側」を「文脈(期・連結か個別か・軸)の側」に戻す", lambda c: rep(c, u"その大半は文脈の側**", u"その大半は文脈(期・連結か個別か・軸)の側**"), (u"frag",)),
    (u"M106 最後の行の「次の便は人間が決める。」を「次の便の候補は人間が決める。」に", lambda c: rep(c, u"次の便は人間が決める。", u"次の便の候補は人間が決める。"), (u"verdict",)),
    (u"M107 最後の行の前に「0 USD」「有料」の字を含む案の行を足す", lambda c: add_before_last5(c, u"- 最後の 1 つは有料で、先の 2 つは 0 USD。"), (u"verdict",)),
)


def run_mutations(base=None):
    base = base or Ctx()
    out = []
    for name, fn, checks in MUTATIONS:
        c = base.copy()
        fn(c)
        res = [(k, bool(guard(CHECKS[k], c))) for k in checks]
        out.append((name, res))
    return out


# ======================================================================================================
class RealTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = Ctx()

    def test_a_1_sha256_and_provenance(self):
        self.assertEqual([], sha_problems(self.c))

    def test_b_1_the_record_numbers_recount_without_the_script_functions(self):
        self.assertEqual([], recount_problems(self.c))

    def test_b_2_the_record_has_no_forbidden_fields_or_forms(self):
        self.assertEqual([], record_clean_problems(self.c))

    def test_b_3_the_derived_numbers_the_document_states(self):
        s = self.c.rec[AGG]
        S = s[K_STAGE]
        self.assertEqual((74229, 64534, 7277, 57257, 1142), (s[K_ROWS], s[K_FACTS], s[K_NIL], s[K_NONNIL], s[K_OUT]))
        self.assertEqual((2216, 51290, 2425, 2197, 67, 6339), tuple(S[B3]["HT"][k] for k in CLS))
        self.assertEqual((2216, 32121, 22733, 1781, 1142, 4541), tuple(S[B3]["H"][k] for k in CLS))
        self.assertEqual((2216, 52121, 2699, 2737, 220, 4541), tuple(S[B3]["F"][k] for k in CLS))
        self.assertEqual((1988, 46009, 2282, 1848, 51, 5079), tuple(S[B3NN]["HT"][k] for k in CLS))
        self.assertEqual((1988, 44619, 2164, 1785, 78, 6623), tuple(S[B5]["HT"][k] for k in CLS))
        self.assertEqual((6339, 0, 831, 274, 540, 153, 4541), (s[K_FALL],) + tuple(s[K_FALLC][k] for k in CLS))
        lo, mid, hi, cnt = doc_stats(self.c.rec)
        self.assertEqual((u"7.6", u"84.4", u"95.3", [55, 49, 27, 6, 1]), (fpct(lo), fpct(mid), fpct(hi), cnt))
        self.assertEqual((57, 342, 1126, 11, 30), w1_stats(self.c.rec))
        self.assertEqual((1, 49), doc_counts(self.c.rec))
        self.assertEqual((16063, 14021, 16), xy0_numbers(self.c))

    def test_c_1_the_seal_has_the_bound_phrases(self):
        self.assertEqual([], bound_problems(self.c))

    def test_c_2_the_verdicts_are_decided_again_and_equal_the_document(self):
        self.assertEqual([], verdict_problems(self.c))
        j = judge(self.c.rec)
        self.assertEqual(4, sum(1 for v in j.values() if v[0]))
        self.assertEqual([u"XZ0-2", u"XZ0-4", u"XZ0-6", u"XZ0-7"], miss_ids(j))
        self.assertEqual(list(IDS), list(j))
        self.assertEqual((False, False, False, False), suspects(self.c))
        # XZ0-6 は丸める前の差 -2.43 ポイントで外れ(丸めた 77.9 - 80.4 = -2.5 や 小数第 1 位の -2.4 ではなく整数で決める)
        s = self.c.rec[AGG][K_STAGE]
        Dn = self.c.rec[AGG][K_NONNIL]
        diff = Fraction(100 * (s[B5]["HT"]["U"] - s[B3NN]["HT"]["U"]), Dn)
        self.assertTrue(Fraction(-244, 100) < diff < Fraction(-242, 100))
        self.assertFalse(j[u"XZ0-6"][0])

    def test_d_1_every_number_in_the_document_is_bound_to_the_record(self):
        self.assertEqual([], doc_number_problems(self.c))
        self.assertEqual([], residual_problems(self.c))

    def test_d_2_the_table_rows_and_the_statements_equal_the_record(self):
        self.assertEqual([], fragment_problems(self.c))
        self.assertEqual([], sanity_problems(self.c))

    def test_d_3_section3_is_bound_only_by_form_not_by_the_record(self):
        self.assertEqual([], sec3_problems(self.c))

    def test_e_1_the_important_phrases_are_present(self):
        self.assertEqual([], phrase_problems(self.c))

    def test_e_2_the_losses_and_limits_are_at_the_head(self):
        self.assertEqual([], head_problems(self.c))

    def test_e_3_the_document_has_no_forbidden_words_or_forms_and_no_affirmation(self):
        self.assertEqual([], forbidden_problems(self.c))
        self.assertEqual([], affirm_problems(self.c))

    def test_e_4_the_commits_the_document_names(self):
        self.assertEqual([], doc_commit_problems(self.c))

    def test_f_1_the_seal_history_the_blobs_and_the_engine(self):
        self.assertEqual([], git_problems())

    def test_f_2_order_the_seal_then_script_then_record_then_the_document_and_the_gate(self):
        u"""結果の文書と門のどちらかが未 commit なら赤(足した commit が無い。skip にしない)。両方 commit された後で初めて緑。"""
        self.assertEqual([], order_problems_real())

    def test_f_3_the_blob_check_lists_the_four_frozen_files_at_their_commits(self):
        self.assertEqual([SEAL_REL, SCRIPT_REL, SEAL_GATE_REL, RECORD_REL], list(BLOB_AT))
        self.assertEqual([SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT], list(BLOB_AT.values()))
        self.assertEqual((SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT), DOC_COMMITS)
        self.assertEqual((u"4ee140d2", u"77662224", u"861879cb"), DOC_COMMITS)

    def test_f_4_the_commit_history_check_matches_the_real_history(self):
        self.assertEqual([], commit_problems())

    def test_f_5_the_blob_check_is_red_for_a_changed_file(self):
        r = PR.Repo()
        r.put("measure/s.py")
        c1 = r.commit("measure/s.py")
        at = {"measure/s.py": c1[:8]}
        self.assertEqual([], blob_problems(r.d, PREFIX, at))
        with open(os.path.join(r.d, PREFIX, "measure/s.py"), "a", encoding="utf-8") as fh:
            fh.write(u"# 結果の便で足した 1 行\n")
        self.assertNotEqual([], blob_problems(r.d, PREFIX, at))


class MutationTest(unittest.TestCase):
    def test_g_1_every_mutation_turns_its_checks_red_and_the_files_are_unchanged(self):
        files = list(SHA_PIN) + [DOC_REL]
        before = tuple(sha_file(r) for r in files)
        base = Ctx()
        results = run_mutations(base)
        self.assertEqual(before, tuple(sha_file(r) for r in files))
        self.assertEqual(len(MUTATIONS), len(results))
        silent = [(n, k) for n, res in results for k, red in res if not red]
        self.assertEqual([], silent)
        self.assertGreaterEqual(len(MUTATIONS), 100)

    def test_g_2_the_unmutated_copy_is_green_on_every_check(self):
        c = Ctx().copy()
        for k, fn in CHECKS.items():
            self.assertEqual([], fn(c), k)

    def test_g_3_the_recount_stays_green_when_the_data_changes_consistently_but_the_verdict_does_not(self):
        base = Ctx()
        for fn, key in ((m_u_low, u"XZ0-1"), (m_w1_to_u, u"XZ0-2"), (m_n_high, u"XZ0-3"), (m_f_w1_low, u"XZ0-4"), (m_h_up, u"XZ0-5"), (m_b5_equal, u"XZ0-6"),
                        (m_ctx_over_name, u"XZ0-7"), (m_docs95_four, u"XZ0-8")):
            c = base.copy()
            fn(c)
            self.assertEqual([], recount_problems(c), fn.__name__)
            self.assertNotEqual([], verdict_problems(c), fn.__name__)
            self.assertNotEqual(judge(base.rec)[key][0], judge(c.rec)[key][0], (fn.__name__, key))

    def test_g_4_every_check_name_a_mutation_names_exists_and_every_check_has_a_mutation(self):
        named = set(k for _, _, ks in MUTATIONS for k in ks)
        self.assertEqual(set(CHECKS), named)

    def test_g_5_the_judgement_edges_at_the_seal_bounds(self):
        u"""境の 1 つ手前と境の数(丸める前の整数): 下限・上限とも含む。分母 1000(束 5 は 500)。"""
        def j(**kw):
            a = dict(D=1000, ht_u=800, ht_w1=20, ht_n=100, ht_x=20, f_u=810, f_w1=30, h_u=500, Dn=500, u5=400, u3=410, c_u=830, n_u=829, n95=1, n80=30)
            a.update(kw)
            return judge_nums(**a)
        self.assertTrue(j(ht_u=700)[u"XZ0-1"][0])
        self.assertFalse(j(ht_u=699)[u"XZ0-1"][0])
        self.assertTrue(j(ht_u=860)[u"XZ0-1"][0])
        self.assertFalse(j(ht_u=861)[u"XZ0-1"][0])
        self.assertTrue(j(ht_w1=25)[u"XZ0-2"][0])
        self.assertFalse(j(ht_w1=26)[u"XZ0-2"][0])
        self.assertTrue(j(ht_n=40, ht_x=20)[u"XZ0-3"][0])
        self.assertFalse(j(ht_n=39, ht_x=20)[u"XZ0-3"][0])
        self.assertTrue(j(ht_n=180, ht_x=20)[u"XZ0-3"][0])
        self.assertFalse(j(ht_n=181, ht_x=20)[u"XZ0-3"][0])
        self.assertTrue(j(ht_u=800, f_u=810)[u"XZ0-4"][0])
        self.assertFalse(j(ht_u=800, f_u=809)[u"XZ0-4"][0])
        self.assertTrue(j(f_w1=35)[u"XZ0-4"][0])
        self.assertFalse(j(f_w1=36)[u"XZ0-4"][0])
        self.assertTrue(j(ht_u=800, h_u=650)[u"XZ0-5"][0])
        self.assertFalse(j(ht_u=800, h_u=651)[u"XZ0-5"][0])
        # XZ0-6: 差 -2 ポイントちょうど(分母 500 で -10 fact)は当たり・-11 は外れ
        self.assertTrue(j(u5=400, u3=410)[u"XZ0-6"][0])
        self.assertFalse(j(u5=399, u3=410)[u"XZ0-6"][0])
        self.assertTrue(j(c_u=500, n_u=500)[u"XZ0-7"][0])
        self.assertFalse(j(c_u=499, n_u=500)[u"XZ0-7"][0])
        self.assertTrue(j(n95=3, n80=20)[u"XZ0-8"][0])
        self.assertFalse(j(n95=4, n80=20)[u"XZ0-8"][0])
        self.assertTrue(j(n95=3, n80=50)[u"XZ0-8"][0])
        self.assertFalse(j(n95=3, n80=51)[u"XZ0-8"][0])
        self.assertFalse(j(n95=3, n80=19)[u"XZ0-8"][0])

    def test_g_6_the_miss_direction_follows_the_bound(self):
        c = Ctx().copy()
        m_u_low(c)
        self.assertEqual(u"下", judge(c.rec)[u"XZ0-1"][1])
        self.assertEqual(u"上", judge_nums(1000, 861, 20, 100, 20, 870, 30, 500, 500, 400, 410, 830, 829, 1, 30)[u"XZ0-1"][1])

    def test_g_7_the_self_suspicion_flags_fire_for_each_cause_and_not_at_the_bound(self):
        base = Ctx()
        self.assertEqual((False, False, False, False), suspects(base))
        for fn, idx in ((m_u_over95, 0), (m_n_over30, 1), (m_name_u_low, 2), (m_out_over5, 3)):
            c = base.copy()
            fn(c)
            f = suspects(c)
            self.assertTrue(f[idx], (fn.__name__, f))
            self.assertEqual([], recount_problems(c), fn.__name__)
            self.assertNotEqual([], verdict_problems(c), fn.__name__)
        # ちょうど 95%・30%・70%(未満の境)・5% は立たない(「超えた」「未満」)
        c = base.copy()
        s = c.rec[AGG]
        s[K_FACTS] = 1000
        s[K_OUT] = 0
        ht = s[K_STAGE][B3]["HT"]
        ht[u"U"], ht[u"N"] = 950, 300
        s[K_STAGE][NAME]["HT"][u"U"] = 700
        self.assertEqual((False, False, False, False), suspects(c))
        ht[u"U"], ht[u"N"] = 951, 301
        s[K_STAGE][NAME]["HT"][u"U"] = 699
        s[K_OUT] = 53                    # 53 / 1053 = 5.03%
        self.assertEqual((True, True, True, True), suspects(c))
        s[K_OUT] = 52                    # 52 / 1052 = 4.94%
        self.assertFalse(suspects(c)[3])


if __name__ == "__main__":
    unittest.main()
