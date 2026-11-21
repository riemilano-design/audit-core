# -*- coding: utf-8 -*-
u"""結果の門: 封 docs/XBRL_SHEET_CONTEXT_SEAL_2026-11-22.md(d46f92aa)・封への追記(4f836c94)の結果の文書 docs/XBRL_SHEET_CONTEXT_RESULT_2026-11-22.md(便 XA1)。

封の門 ``test_xbrl_sheet_context_seal.py`` の次の段。**追跡されている記録・script・封・追記・封の門・結果の文書と git の履歴だけを読む**(書類の置き場も道具(Arelle)も読まない・通信しない・鍵は読まない)。
便 XA0 の結果の門 ``test_xbrl_sheet_wall_result.py`` の部品(読み・sha256・% の丸め・節の切り出し・数のトークン・「作れる」等の肯定の検査・禁止語・blob・順序の道具)を読み込んで使う(門としては走らせない)。
検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表で 1 つずつ(木の file は変異させず、``Ctx`` の写しに当てる)。

 a script・記録・封・追記・封の門の sha256(字で留める)と、記録の script の sha256・封の commit の欄・記録の限界の欄・記録が持つ便 XA0 の記録の sha256 が便 XA0 の記録の sha256 と同じ
 b 記録の数え直し: 書類ごとの数から、**script の関数を使わずに**、2 群の fact・段ごとの全部決まる fact・段ごとの 90% 以上の書類を数え直し、群の数の間の関係
   (段 0 ⊂ 段 1 ⊂ 段 2 の順に減らない・8 通りの和が表の数・書く欄の項の和・理由の数と「終わりの日か member の組が違う」の関係)と **段 0 が便 XA0 の記録と全部の数で同じ**ことと、予測の判定に要る数を見る
 c 予測 XA1-1〜XA1-8 の当たり外れを、封 §4 の字から取った境(丸める前の整数で。下限は含む・上限は XA1-1・XA1-6 が含まない)と記録から決め直し、文書 §1 の表・件数と同じことを見る。
   封 §4 の自己点検の条・封 §6 の決め(XA1-2 が当たりなら次の便の候補を示す)と文書が合う
 d 結果の文書の数: 数字を含む行は全部、記録(と便 XA0 の記録)から組んだ数の並びの内。表の行・言い切りは記録から組んだ字とそのまま照らす。
   §3 の導いた数(書類ごとの最小・最大の率・2997・74・482)は書類ごとの数・記録から導き直して字で照らす
 e 文書の要点の字・頭の負けと限界・禁止語・「作れる」「専用の道具が要らない」「人が書ける」を肯定で書かない・docID と EDINET コードの形
 f 封・追記・script・記録・封の門が commit の blob と一致(結果の便で 0 行)・engine は封の commit から 0 行・順序・文書が書く commit の字が実の履歴と合う
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


WG = load_module("tests/measure/test_xbrl_sheet_wall_result.py", "xbrl_sheet_wall_result_gate_for_context_result_gate")     # 便 XA0 の結果の門の部品。門としては走らせない
SG = load_module("tests/measure/test_xbrl_sheet_context_seal.py", "xbrl_sheet_context_seal_gate_for_result_gate")            # 封の門の部品。門としては走らせない
PR = SG.load_order_helpers()
MS = SG.MS

read, sha_file, guard, pct, section, rep = WG.read, WG.sha_file, WG.guard, WG.pct, WG.section, WG.rep
add_doc, drop_all = WG.add_doc, WG.drop_all

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
ADD_REL = "docs/XBRL_SHEET_CONTEXT_SEAL_ADDENDUM_2026-11-22.md"
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
RECORD_REL = SG.RECORD_REL
PRIOR_RECORD_REL = SG.PRIOR_RECORD_REL
GATE_REL = "tests/measure/test_xbrl_sheet_context_result.py"
DOC_REL = "docs/XBRL_SHEET_CONTEXT_RESULT_2026-11-22.md"
SCRIPT_COMMIT_SHORT = "4f836c94"                  # 追記・script・封の門を足した commit
RECORD_COMMIT_SHORT = "bf03d019"                  # 記録を足した commit
BLOB_AT = collections.OrderedDict([
    (SEAL_REL, SEAL_COMMIT_SHORT), (ADD_REL, SCRIPT_COMMIT_SHORT), (SCRIPT_REL, SCRIPT_COMMIT_SHORT), (SEAL_GATE_REL, SCRIPT_COMMIT_SHORT), (RECORD_REL, RECORD_COMMIT_SHORT)])
DOC_COMMITS = (SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT)

SHA_PIN = collections.OrderedDict([
    (RECORD_REL, "9f9b654c321bd2b41fc6fad991df98f12f574f510402a5108334a26219a4809a"),
    (SCRIPT_REL, "e6d15bcc0c179dd29f167404e6be26704ba1b003cbd1867d27da96198799c4df"),
    (SEAL_GATE_REL, "147f431b650dc16f438dab224e57371c2e7c51dc9e740c56bd2adf2523bf1a29"),
    (SEAL_REL, "f5303eb8407c2211e7e7ed9f1aa78f63d4ec3abadc5640267a40a011d2737532"),
    (ADD_REL, "c28f73b5f2da92d25b14c9a7715b75bea05a362a15fe0799ebd93d9de0e2e483"),
    (PRIOR_RECORD_REL, "f5d45ab221809b19d87a58801127504055e45d689d48586463babf9a6dbf0a09")])

DEV_COUNT = 5
DOC_COUNT = 67
G_DEV, G_PROD = WG.G_DEV, WG.G_PROD
GROUPS = (G_DEV, G_PROD)
STAGES = (u"段 0", u"段 1", u"段 2")
PRED_KEY = u"予測の判定に要る数(XA1-1〜XA1-8。本番だけの 62 本のうち断らなかった書類を合わせた fact。当たり・外れは結果の文書で)"
PK = (u"XA1-1 段 1 の全部決まる fact / fact", u"XA1-2 段 2 の全部決まる fact / fact", u"XA1-3 段 2 で終わりの日か member の組が線の決めと違う fact の数",
      u"XA1-4 段 2 の決まらなかった理由ごとの fact の数と、いちばん多い理由", u"XA1-5 段 2 の全部決まる fact が 90% 以上の書類 / fact が 1 つ以上在る書類",
      u"XA1-6 段 2 の書く欄の数 / fact の数 × 7", u"XA1-7 期間の種類が 2 つ在る name の fact / fact", u"XA1-8 文脈の線・文脈の線を選ばなかった表 / fact の在る表")
RS = u"決まらなかった理由ごとの fact の数(重ねて数える)"
DOC90 = u"全部決まる fact が 90% 以上の書類の数"
DECIDED, FULL, CELLS, BASE, RATIO = u"表の決めで決まる fact の数", u"全部決まる fact の数", u"書く欄の数", u"fact の数 × 7", u"書く欄の比"
S2_DIFF = u"終わりの日か member の組が線の決めと違う fact の数(どちらかが違えば 1)"
S2_TABLES, S2_COMBOS, S2_NOT_CC, S2_ITEMS = u"fact の在る表の数", u"8 通りのそれぞれを選んだ表の数", u"文脈の線・文脈の線を選ばなかった表の数", u"書く欄の数(項ごと)"
ITEMS = (u"表ごとの 3", u"要素の線 × 4", u"終わりの日を決める側の線 × 1", u"member の組を決める側の線 × 1", u"書式の類の数", u"空の fact の数 × 1", u"表の中で全部決まらない fact × 7", u"表の外の fact × 7")
COMBOS = (u"ACC", u"ACE", u"AEC", u"AEE", u"BCC", u"BCE", u"BEC", u"BEE")
S0_REASONS = (u"name が線の決めと違う", u"contextRef が線の決めと違う", u"unitRef が線の決めと違う", u"decimals が線の決めと違う", u"scale が線の決めと違う")
S1_REASONS = (u"name が線の決めと違う", u"対が線の決めと違う", u"unitRef が線の決めと違う", u"decimals が線の決めと違う", u"scale が線の決めと違う")
S2_REASONS = (u"name が線の決めと違う", u"終わりの日が線の決めと違う", u"member の組が線の決めと違う", u"unitRef が線の決めと違う", u"decimals が線の決めと違う", u"scale が線の決めと違う")
PERIOD_N, PERIOD_F, START_F = u"期間の種類が 2 つ在る name の数", u"期間の種類が 2 つ在る name の fact の数", u"始まりの日が違う期間の文脈を指す fact の数"
LIVE = u"fact が 1 つ以上在る書類の数(断らなかった)"

BOUND_SEAL_PHRASES = (u"段 1 の全部決まる fact は、fact の 82% 以上 92% 未満", u"段 2 の全部決まる fact は、fact の 90% 以上", u"3500 以下", u"いちばん多いのは `name`",
                      u"全部決まる fact が 90% 以上の書類は 31 本以上", u"段 2 の書く欄の比は 25% 以上 38% 未満", u"fact は、fact の 0.5% 以下", u"fact の在る表の 15% 以上",
                      u"段 0 が便 XA0 の記録と違う(止める)・段 2 の全部決まる fact がちょうど 100%・段 2 が段 1 より少ない・段 1 が段 0 より少ない・断った書類が 6 本以上",
                      u"XA1-2 が当たりなら、次の便の候補を人間に示す",
                      u"「XBRL を作れる」「専用の道具が要らない」は、この便からは言えない")
# 文書 §1 の表の予測の欄に在るべき境の字と、封 §4 の同じ行に在るべき境の字
ROW_BOUND = collections.OrderedDict([(u"XA1-1", u"82% 以上 92% 未満"), (u"XA1-2", u"90% 以上"), (u"XA1-3", u"3500 以下"), (u"XA1-4", u"`name`"), (u"XA1-5", u"31 本以上"),
                                      (u"XA1-6", u"25% 以上 38% 未満"), (u"XA1-7", u"0.5% 以下"), (u"XA1-8", u"15% 以上")])
HEAD_PHRASES = (u"先に負けと限界を書く", u"当たり 8・外れ 0", u"予測は便 XA0 の 62 本の結果を見てから書いた(封 §0)", u"62 本は便 XA0 で既に数えた書類で、未使用ではない",
                u"境の置き方しだいで外れていた", u"XA1-5(31 本以上)は低い境だった", u"表ごとの 8 通りの選びも答えを見て選んでいる", u"作りから当たり前",
                u"「人が書く量はこれだけで済む」とは読まない", u"分けても 4.9% は紙に収まらない", u"文脈を分けても直らない型", u"書く欄の数は減らなかった",
                u"期間の種類と始まりの日は線で決めていない(数えただけ)", u"四半期の書類は測っていない", u"文脈の `id` と定義を作ることは、この便では作っていない",
                u"便 XA0 の限界の全部を継ぐ", u"同じ member を別の字で書いた文脈は別の member に数える", u"封の門に直していない穴が 2 つ在る",
                u"0 USD・LLM の席も道具(Arelle)も呼んでいない", u"engine は 0 行", u"表・fact・符号・書式の読み取りの部を便 XA0 の script と共有している",
                u"「XBRL を作れる」「専用の道具が要らない」は、この便からは言えない")
PHRASES = (u"言えること", u"言えないこと", u"人間に示す次の便の候補", u"別の封が先", u"盲検ではない", u"記録から導いた読み", u"人間に返すこと",
           u"「選ばれない形」とは言わない(測っていない)", u"同じ fact であることまでは測っていない", u"読んでいない", u"人がその紙を正しく書けるか・書く手間がどれだけ減るか")
STRUCTURAL = WG.STRUCTURAL
BOUND_NUMBERS = set([u"82", u"92", u"90", u"3500", u"31", u"25", u"38", u"0.5", u"15", u"62", u"67", u"100", u"4", u"8", u"6", u"5", u"3"])


# ======================================================================================================
class Ctx(object):
    u"""検査が見る写し。変異はこの写しを変える(木の file は変えない)。"""

    def __init__(self):
        self.rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        self.prior = json.loads(read(PRIOR_RECORD_REL), object_pairs_hook=collections.OrderedDict)
        self.doc = read(DOC_REL)
        self.seal = read(SEAL_REL)
        self.add = read(ADD_REL)
        self.shas = collections.OrderedDict((rel, sha_file(rel)) for rel in SHA_PIN)

    def copy(self):
        c = Ctx.__new__(Ctx)
        c.rec = copy.deepcopy(self.rec)
        c.prior = self.prior
        c.doc = self.doc
        c.seal = self.seal
        c.add = self.add
        c.shas = collections.OrderedDict(self.shas)
        return c


# ======================================================================================================
# b 数え直し(script の関数は使わない)
def docs_of(rec, g):
    docs = rec[u"書類"]
    return docs[:DEV_COUNT] if g == G_DEV else docs[DEV_COUNT:]


def stage_key(i):
    return u"段 %d の全部決まる fact の数" % i


def doc90(docs, i):
    return sum(1 for d in docs if not d[u"断った"] and d[u"fact の数"] > 0 and 100 * d[stage_key(i)] >= 90 * d[u"fact の数"])


def rate_row(n, d):
    return collections.OrderedDict([(u"数", n), (u"分母", d), (u"%", float(pct(n, d)))])


def group_problems(c, g):
    rec, prior = c.rec, c.prior
    s, p = rec[g], prior[g]
    docs = docs_of(rec, g)
    live = [d for d in docs if not d[u"断った"]]
    out = []
    if s[u"書類の数"] != len(docs) or s[u"断った書類の数"] != len(docs) - len(live) or s[u"断らなかった書類の数"] != len(live):
        out.append(u"%s の書類の数・断った書類の数が書類ごとの行と違う" % g)
    fact = sum(d[u"fact の数"] for d in live)
    if s[u"fact の数"] != fact or s[LIVE] != sum(1 for d in live if d[u"fact の数"] > 0):
        out.append(u"%s の fact の数・fact が 1 つ以上在る書類の数が書類ごとの和と違う" % g)
    outside = p[u"表の外の fact の数"]                                   # 表の外・空の fact は便 XA0 の記録(段 0 が同じと確かめる)から
    inside = fact - outside
    prev = None
    for i, st in enumerate(STAGES):
        t = s[st]
        full = sum(d[stage_key(i)] for d in live)
        if t[FULL] != full:
            out.append(u"%s の %s の全部決まる fact が書類ごとの和 %d と違う" % (g, st, full))
        if t[DOC90] != doc90(docs, i):
            out.append(u"%s の %s の 90%% 以上の書類の数が書類ごとの数から数え直した値と違う" % (g, st))
        if not (full <= t[DECIDED] <= inside) or t[BASE] != 7 * fact:
            out.append(u"%s の %s の全部決まる・表の決めで決まる・表の中の関係・fact の数 × 7 が合わない" % (g, st))
        r = t[RATIO]
        if (r[u"数"], r[u"分母"]) != (t[CELLS], 7 * fact) or u"%.1f" % r[u"%"] != pct(t[CELLS], 7 * fact):
            out.append(u"%s の %s の書く欄の比が数え直した値と違う" % (g, st))
        if prev is not None and full < prev:
            out.append(u"%s の %s の全部決まる fact が前の段より少ない" % (g, st))
        prev = full
    for d in live:
        if not (d[stage_key(0)] <= d[stage_key(1)] <= d[stage_key(2)] <= d[u"fact の数"]):
            out.append(u"書類 %d の段ごとの全部決まる fact が段 0 ≤ 段 1 ≤ 段 2 ≤ fact の順でない" % d[u"番号"])
    t2 = s[u"段 2"]
    if list(t2[RS]) != list(S2_REASONS) or list(s[u"段 1"][RS]) != list(S1_REASONS) or list(s[u"段 0"][RS]) != list(S0_REASONS):
        out.append(u"%s の理由の名が違う" % g)
        return out
    for st in STAGES:
        und = inside - s[st][DECIDED]
        if sum(s[st][RS].values()) < und or max(s[st][RS].values()) > und:
            out.append(u"%s の %s の理由の数が、決まらなかった fact の数と合わない" % (g, st))
    diff = t2[S2_DIFF]
    if not (max(t2[RS][S2_REASONS[1]], t2[RS][S2_REASONS[2]]) <= diff <= t2[RS][S2_REASONS[1]] + t2[RS][S2_REASONS[2]]):
        out.append(u"%s の「終わりの日か member の組が違う」が 2 つの理由の数と合わない" % g)
    tables = t2[S2_TABLES]
    if list(t2[S2_COMBOS]) != list(COMBOS) or sum(t2[S2_COMBOS].values()) != tables or t2[S2_NOT_CC] != tables - t2[S2_COMBOS][u"ACC"] - t2[S2_COMBOS][u"BCC"]:
        out.append(u"%s の 8 通りの和・「文脈の線・文脈の線を選ばなかった表」が表の数と合わない" % g)
    if tables != p[u"fact の在る表の数"]:
        out.append(u"%s の fact の在る表の数が便 XA0 の記録と違う" % g)
    cl = t2[S2_ITEMS]
    if list(cl) != list(ITEMS):
        out.append(u"%s の書く欄の項の名が違う" % g)
        return out
    want = (3 * tables, None, None, None, None, p[u"空の fact の数"], 7 * (inside - t2[FULL]), 7 * outside)
    for k, w in zip(ITEMS, want):
        if w is not None and cl[k] != w:
            out.append(u"%s の書く欄の項 %s が数え直した値 %d と違う" % (g, k, w))
    if t2[CELLS] != sum(cl.values()):
        out.append(u"%s の段 2 の書く欄の数が項の和と違う" % g)
    # 段 0 は便 XA0 の記録と全部の数で同じ
    t0 = s[u"段 0"]
    same = ((t0[DECIDED], p[u"表の決めで決まる fact の数"]), (t0[FULL], p[u"全部決まる fact の数"]), (t0[DOC90], p[DOC90]), (t0[CELLS], p[u"書く欄の数"]), (t0[BASE], p[u"fact の数 × 7"]),
           (s[u"fact の数"], p[u"fact の数"]), (list(t0[RS].values()), list(p[u"決まらなかった理由ごとの fact の数(重ねて数える)"].values())))
    if any(a != b for a, b in same):
        out.append(u"%s の段 0 が便 XA0 の記録と違う" % g)
    for d, pd in zip(docs, docs_of(prior, g)):
        if (d[u"断った"], d[u"fact の数"], d[stage_key(0)]) != (pd[u"断った"], pd[u"fact の数"], pd[u"全部決まる fact の数"]):
            out.append(u"書類 %d の段 0 が便 XA0 の記録と違う" % d[u"番号"])
    if s[PERIOD_N] > 0 and s[PERIOD_F] == 0:
        out.append(u"%s の期間の種類が 2 つ在る name の数と fact の数が合わない" % g)
    return out


def reason_max(t2):
    cnt = t2[RS]
    top = max(cnt.values())
    return [k.replace(u"が線の決めと違う", u"の違い") for k, v in cnt.items() if v == top]


def pred_expected(rec):
    s = rec[G_PROD]
    fact = s[u"fact の数"]
    t1, t2 = s[u"段 1"], s[u"段 2"]
    cnt = collections.OrderedDict((k.replace(u"が線の決めと違う", u"の違い"), v) for k, v in t2[RS].items())
    return collections.OrderedDict([
        (PK[0], rate_row(t1[FULL], fact)), (PK[1], rate_row(t2[FULL], fact)), (PK[2], collections.OrderedDict([(u"数", t2[S2_DIFF])])),
        (PK[3], collections.OrderedDict([(u"理由ごとの数", cnt), (u"いちばん多い理由", reason_max(t2))])),
        (PK[4], collections.OrderedDict([(u"書類", t2[DOC90]), (u"分母", s[LIVE])])), (PK[5], rate_row(t2[CELLS], 7 * fact)),
        (PK[6], rate_row(s[PERIOD_F], fact)), (PK[7], rate_row(t2[S2_NOT_CC], t2[S2_TABLES]))])


def judge(rec):
    u"""封 §4 の境(丸める前の整数)から XA1-1〜XA1-8 を決め直す。値は (当たりか, 外れた向き)。"""
    s = rec[G_PROD]
    fact = s[u"fact の数"]
    t1, t2 = s[u"段 1"], s[u"段 2"]
    out = collections.OrderedDict()

    def put(k, lo_ok, hi_ok):
        out[k] = (lo_ok and hi_ok, u"" if lo_ok and hi_ok else (u"下" if not lo_ok else u"上"))
    put(u"XA1-1", 100 * t1[FULL] >= 82 * fact, 100 * t1[FULL] < 92 * fact)
    put(u"XA1-2", 100 * t2[FULL] >= 90 * fact, True)
    put(u"XA1-3", True, t2[S2_DIFF] <= 3500)
    put(u"XA1-4", reason_max(t2) == [u"name の違い"], True)
    put(u"XA1-5", t2[DOC90] >= 31, True)
    put(u"XA1-6", 100 * t2[CELLS] >= 25 * 7 * fact, 100 * t2[CELLS] < 38 * 7 * fact)
    put(u"XA1-7", True, 1000 * s[PERIOD_F] <= 5 * fact)
    put(u"XA1-8", 100 * t2[S2_NOT_CC] >= 15 * t2[S2_TABLES], True)
    return out


def sha_problems(c):
    out = []
    for rel, want in SHA_PIN.items():
        if c.shas[rel] != want:
            out.append(u"sha256 が字で留めた値と違う: %s" % rel)
    if c.rec[u"この script の sha256"] != SHA_PIN[SCRIPT_REL]:
        out.append(u"記録の script の sha256 が script と違う")
    if c.rec[u"材料"][u"便 XA0 の記録の sha256"] != SHA_PIN[PRIOR_RECORD_REL]:
        out.append(u"記録が持つ便 XA0 の記録の sha256 が便 XA0 の記録と違う")
    if (c.rec[u"seal"], c.rec[u"封の commit"]) != (SEAL_REL, SEAL_COMMIT_SHORT):
        out.append(u"記録の封の欄が違う")
    if c.rec[u"限界"] != MS.LIMITS:
        out.append(u"記録の限界の欄が script の字と違う")
    return out


def recount_problems(c):
    rec = c.rec
    out = []
    docs = rec[u"書類"]
    if [d[u"番号"] for d in docs] != list(range(1, DOC_COUNT + 1)) or rec[u"材料"][u"書類の本数"] != DOC_COUNT or rec[u"材料"][u"開発の 5 本の番号"] != list(range(1, DEV_COUNT + 1)):
        out.append(u"書類の番号・材料の書類の本数・開発の 5 本の番号が違う")
    for g in GROUPS:
        out.extend(group_problems(c, g))
    if json.loads(json.dumps(rec[PRED_KEY])) != json.loads(json.dumps(pred_expected(rec))):
        out.append(u"予測の判定に要る数が群の数から作り直した値と違う")
    return out


def record_clean_problems(c):
    text = json.dumps(c.rec, ensure_ascii=False)
    out = []
    try:
        MS.check_clean(c.rec, text)
    except SystemExit:
        out.append(u"記録の検査(欄・形・file の名・日付)が止める")
    if WG.DOCID_FORM.search(re.sub(r"[0-9a-fA-F]{32,}", u"", text)) or WG.ECODE_FORM.search(text):
        out.append(u"記録に docid か EDINET コードの形が在る")
    return out


def bound_problems(c):
    out = [u"封に境の字が無い: %s" % p for p in BOUND_SEAL_PHRASES if p not in c.seal]
    sec4 = section(c.seal, u"## §4 ", u"## §5 ")
    rows = [ln for ln in sec4.splitlines() if re.match(r"^\| XA1-\d", ln)]
    if len(rows) != 8:
        out.append(u"封 §4 の表の行が 8 つでない")
    return out


def addendum_problems(c):
    u"""追記が「本番の数はまだ見ていない」と書き、封の本文を変えていないと書き、残った穴 2 つを書いている。"""
    out = []
    for p in (u"本番の数はまだ見ていない", u"予測 XA1-1〜XA1-8 は変えていない", u"監査で残った穴(直していない)", u"XA1-5 の分母を", u"「script・門より後」は縛っていない"):
        if p not in c.add:
            out.append(u"追記に字が無い: %s" % p)
    return out


# ======================================================================================================
def cell_text(rec, key):
    s = rec[G_PROD]
    fact = s[u"fact の数"]
    t1, t2 = s[u"段 1"], s[u"段 2"]
    if key == u"XA1-3":
        return u"%d" % t2[S2_DIFF]
    if key == u"XA1-4":
        cnt = t2[RS]
        second = sorted(((v, k) for k, v in cnt.items() if k != S2_REASONS[0]), reverse=True)[0]
        return u"`name` が %d(次は終わりの日の %d)" % (cnt[S2_REASONS[0]], second[0]) if second[1] == S2_REASONS[1] else u"?"
    if key == u"XA1-5":
        return u"%d/%d" % (t2[DOC90], s[LIVE])
    pairs = {u"XA1-1": (t1[FULL], fact), u"XA1-2": (t2[FULL], fact), u"XA1-6": (t2[CELLS], 7 * fact), u"XA1-7": (s[PERIOD_F], fact), u"XA1-8": (t2[S2_NOT_CC], t2[S2_TABLES])}
    n, d = pairs[key]
    return u"%d/%d(%s%%)" % (n, d, pct(n, d))


def expected_cells(c):
    out = collections.OrderedDict()
    for k, (ok, way) in judge(c.rec).items():
        out[k] = (cell_text(c.rec, k), u"当たり" if ok else u"**外れ**(%sに外れた)" % way)
    return out


def verdict_problems(c):
    rec = c.rec
    j = judge(rec)
    want = expected_cells(c)
    out = []
    rows = {}
    for ln in c.doc.splitlines():
        m = re.match(r"^\| (XA1-\d)(?:\(主\))? \|(.*)\|$", ln)
        if m:
            rows[m.group(1)] = [x.strip() for x in m.group(2).split(u"|")]
    if sorted(rows) != sorted(j):
        return [u"文書 §1 の表の行が XA1-1〜XA1-8 でない"]
    sec4 = section(c.seal, u"## §4 ", u"## §5 ")
    seal_rows = dict((ln.split(u"|")[1].strip().replace(u"(主)", u""), ln) for ln in sec4.splitlines() if re.match(r"^\| XA1-\d", ln))
    for k, cells in rows.items():
        if len(cells) != 3:
            out.append(u"%s の行の欄の数が違う" % k)
            continue
        if ROW_BOUND[k] not in cells[0] or ROW_BOUND[k] not in seal_rows[k]:
            out.append(u"%s の境の字(%s)が文書の欄か封の行に無い" % (k, ROW_BOUND[k]))
        if cells[1] != want[k][0]:
            out.append(u"%s の実測の字が記録から組んだ字と違う: %s" % (k, cells[1]))
        if cells[2] != want[k][1]:
            out.append(u"%s の判定が決め直した判定と違う: %s(決め直し: %s)" % (k, cells[2], want[k][1]))
    hits = sum(1 for v in j.values() if v[0])
    if u"- 当たり %d・外れ %d。" % (hits, len(j) - hits) not in c.doc.splitlines():
        out.append(u"文書の件数の行が決め直した件数と違う")
    head = c.doc.split(u"## §1")[0]
    if u"判定した %d 本は" % len(j) not in head or u"(当たり %d・外れ %d)" % (hits, len(j) - hits) not in head:
        out.append(u"文書の頭の件数が決め直した件数と違う")
    if hits == len(j) and u"全部が当たり" not in head:
        out.append(u"全部当たりなのに頭に「全部が当たり」が無い")
    if hits != len(j) and u"全部が当たり" in head:
        out.append(u"外れが在るのに頭に「全部が当たり」が在る")
    sec1, sec4doc = section(c.doc, u"## §1 ", u"## §2 "), section(c.doc, u"## §4 ", None)
    s = rec[G_PROD]
    f1, f2 = s[u"段 1"][FULL], s[u"段 2"][FULL]
    fact = s[u"fact の数"]
    s0, s2 = s[u"段 0"][FULL], s[u"段 2"]
    suspect = [s2[FULL] == fact, f2 < f1, f1 < s0, s[u"断った書類の数"] >= 6]
    if any(suspect):
        out.append(u"封 §4 の「先に自分の欠陥を疑う場合」が発火している")
    if u"封 §4 の「先に自分の欠陥を疑う場合」" not in sec1 or u"には当たらない" not in sec1 or u"段 0 の数は便 XA0 の記録と同じ" not in sec1:
        out.append(u"文書 §1 に自己点検の言い切りが無い")
    # 封 §6: XA1-2 が当たりなら次の便の候補を示す
    cond = j[u"XA1-2"][0]
    shown = u"人間に示す次の便の候補**(封 §6。XA1-2 が当たりなので示す)" in sec4doc
    if cond != shown:
        out.append(u"封 §6 の決め(XA1-2 が当たりなら次の便の候補を示す)と文書 §4 が合わない")
    if cond:
        s6 = section(c.seal, u"## §6 ", u"## §7 ")
        seg = s6[s6.index(u"行・列の紙(向き"):s6.index(u"別の封が先。") + len(u"別の封が先。")].strip()
        if seg not in sec4doc:
            out.append(u"§4 の次の便の候補が封 §6 の字と違う")
    return out


# ======================================================================================================
def stage_rows(c):
    u"""§2 の段ごとの表(本番)の行。"""
    s = c.rec[G_PROD]
    out = []
    for st, label in zip(STAGES, (u"段 0(便 XA0 と同じ)", u"段 1(終わりの日と member の組の対を文脈の線で)", u"段 2(終わりの日と member の組を別々の線で)")):
        t = s[st]
        i = STAGES.index(st)
        out.append(u"| %s | %d | %d | %s%% | %d | %d | %s%% |" % (label, t[DECIDED], t[FULL], pct(t[FULL], s[u"fact の数"]), t[DOC90], t[CELLS], pct(t[CELLS], t[BASE])))
    return out


def expected_lines(c):
    rec = c.rec
    p, d = rec[G_PROD], rec[G_DEV]
    out = []
    for label, key in ((u"断った書類", u"断った書類の数"), (u"fact", u"fact の数"), (u"文脈の定義", u"文脈の定義の数"), (u"member を 1 つ以上持つ文脈を指す fact", u"member を 1 つ以上持つ文脈を指す fact の数"),
                       (u"`typedMember` を持つ文脈を指す fact", u"typedMember を持つ文脈を指す fact の数"), (u"期間の種類が 2 つ在る `name`", PERIOD_N), (u"始まりの日が違う期間の文脈を指す fact", START_F)):
        out.append(u"| %s | %d | %d |" % (label, p[key], d[key]))
    out.extend(stage_rows(c))
    t0, t1, t2 = p[u"段 0"][RS], p[u"段 1"][RS], p[u"段 2"][RS]
    out.append(u"| `name` | %d | %d | %d |" % (t0[S0_REASONS[0]], t1[S1_REASONS[0]], t2[S2_REASONS[0]]))
    out.append(u"| 文脈(段 0 は `contextRef`・段 1 は対) | %d | %d | ― |" % (t0[S0_REASONS[1]], t1[S1_REASONS[1]]))
    out.append(u"| 終わりの日 | ― | ― | %d |" % t2[S2_REASONS[1]])
    out.append(u"| member の組 | ― | ― | %d |" % t2[S2_REASONS[2]])
    for lab, i0, i1, i2 in ((u"unitRef", 2, 2, 3), (u"decimals", 3, 3, 4), (u"scale", 4, 4, 5)):
        out.append(u"| `%s` | %d | %d | %d |" % (lab, t0[S0_REASONS[i0]], t1[S1_REASONS[i1]], t2[S2_REASONS[i2]]))
    return out


def expected_fragments(c):
    rec = c.rec
    s, dev = rec[G_PROD], rec[G_DEV]
    j = judge(rec)
    hits = sum(1 for v in j.values() if v[0])
    fact = s[u"fact の数"]
    t0, t1, t2 = s[u"段 0"], s[u"段 1"], s[u"段 2"]
    d0, d1, d2 = dev[u"段 0"], dev[u"段 1"], dev[u"段 2"]
    cl = t2[S2_ITEMS]
    und = fact - t2[FULL]
    f = []
    f.append(u"判定した %d 本は全部が当たり(当たり %d・外れ %d)" % (len(j), hits, len(j) - hits))
    f.append(u"XA1-1 の %s%% は上の境 92%% のすぐ下" % pct(t1[FULL], fact))
    f.append(u"分けても %s%% は紙に収まらない**(%d のうち全部決まらない fact は %d)" % (pct(und, fact), fact, und))
    f.append(u"`name` が線の決めと違う fact で %d" % t2[RS][S2_REASONS[0]])
    f.append(u"書く欄の比は段 1 の %s%% から段 2 で %s%% に増えた" % (pct(t1[CELLS], t1[BASE]), pct(t2[CELLS], t2[BASE])))
    f.append(u"段ごと(開発の 5 本): 段 0 は %d・段 1 は %d・段 2 は %d(fact %d)。書く欄の比は %s%%・%s%%・%s%%。" % (
        d0[FULL], d1[FULL], d2[FULL], dev[u"fact の数"], pct(d0[CELLS], d0[BASE]), pct(d1[CELLS], d1[BASE]), pct(d2[CELLS], d2[BASE])))
    f.append(u"段 2 で選んだ 8 通り(62 本・fact の在る表 %d。" % t2[S2_TABLES])
    f.append(u"・".join(u"%s %d" % (k, t2[S2_COMBOS][k]) for k in COMBOS) + u"。文脈の線・文脈の線を選ばなかった表は %d。" % t2[S2_NOT_CC])
    f.append(u"表ごとの 3 は %d・要素の線 × 4 は %d・終わりの日を決める側の線 × 1 は %d・member の組を決める側の線 × 1 は %d・書式の類 %d・空の fact × 1 は %d・表の中で全部決まらない fact × 7 は %d・表の外の fact × 7 は %d。" % tuple(cl[k] for k in ITEMS))
    f.append(u"行・列ごとの決めに全部収まる fact は %s%% から %s%% になった" % (pct(t0[FULL], fact), pct(t2[FULL], fact)))
    f.append(u"62 本の全部で 90% を超えた")
    f.append(u"文脈を 2 つに分ければ数の fact の %d%% まで紙の形に収まる" % int(round(100.0 * t2[FULL] / fact)))
    f.append(u"残りの %d%% は 1 つずつ書く欄が要る" % int(round(100.0 * und / fact)))
    f.append(u"どちらも 62 本で 0 だった")
    return f


def per_doc_range(rec, i):
    docs = [d for d in rec[u"書類"][DEV_COUNT:] if not d[u"断った"] and d[u"fact の数"] > 0]
    lo = min(docs, key=lambda d: d[stage_key(i)] / float(d[u"fact の数"]))
    hi = max(docs, key=lambda d: d[stage_key(i)] / float(d[u"fact の数"]))
    return pct(lo[stage_key(i)], lo[u"fact の数"]), pct(hi[stage_key(i)], hi[u"fact の数"])


def derived_lines(c):
    u"""§3 の、記録(と便 XA0 の記録)から導く言い切り。"""
    rec = c.rec
    s = rec[G_PROD]
    fact = s[u"fact の数"]
    t2 = s[u"段 2"]
    und = fact - t2[FULL]
    undec = fact - t2[DECIDED]
    sign = t2[DECIDED] - t2[FULL]
    p = c.prior[G_PROD]
    out = []
    parts = []
    for i, st in enumerate(STAGES):
        lo, hi = per_doc_range(rec, i)
        parts.append(u"%s は最小 %s%%・最大 %s%%" % (st, lo, hi))
    out.append(u"・".join(parts).replace(u"・段 1", u"。段 1").replace(u"・段 2", u"。段 2") + u"。")
    out.append(u"段 2 で全部決まらない %d の内わけ(記録から導く): 表の決めで決まらない fact は %d(表の外の %d を含む)・表の決めで決まるのに符号で落ちた fact は %d。" % (und, undec, p[u"表の外の fact の数"], sign))
    out.append(u"74 は便 XA0 の符号が合わない数と同じ数だが、同じ fact であることまでは測っていない。")
    return out


def sanity_problems(c):
    u"""文書の言い切りが記録の数に合う: 段 2 の書く欄が段 1 より多い・AEE・BCE・BEE が 0・74 は便 XA0 の符号が合わない数・期間・始まりの日が 0・4.9%・62 本の全部で 90% 超。"""
    rec = c.rec
    s = rec[G_PROD]
    out = []
    t1, t2 = s[u"段 1"], s[u"段 2"]
    if not t2[CELLS] > t1[CELLS]:
        out.append(u"文書の「段 2 の書く欄が段 1 より多い」が記録と合わない")
    if [t2[S2_COMBOS][k] for k in (u"AEE", u"BCE", u"BEE")] != [0, 0, 0]:
        out.append(u"文書の「AEE・BCE・BEE が 0」が記録と合わない")
    pw = c.prior[G_PROD]
    if t2[DECIDED] - t2[FULL] != pw[u"符号が合わない fact の数(負と読んだが sign が - でない)"] + pw[u"符号が合わない fact の数(sign が - だが負と読めない)"]:
        out.append(u"文書の「74 は便 XA0 の符号が合わない数と同じ数」が記録と合わない")
    if (s[PERIOD_N], s[PERIOD_F], s[START_F], s[u"typedMember を持つ文脈を指す fact の数"]) != (0, 0, 0, 0):
        out.append(u"文書の「期間の種類・始まりの日・typedMember は 0」が記録と合わない")
    if t2[DOC90] != s[LIVE] or s[u"断った書類の数"] != 0:
        out.append(u"文書の「62 本の全部で 90% を超えた」「断った書類は 0」が記録と合わない")
    if s[u"段 1"][CELLS] >= s[u"段 0"][CELLS] or 100 * t1[FULL] >= 92 * s[u"fact の数"] or t1[FULL] <= s[u"段 0"][FULL]:
        out.append(u"文書の段 1 の言い切り(書く欄が段 0 より少ない・92% 未満・段 0 より多い)が記録と合わない")
    if t2[DECIDED] - t2[FULL] > t2[DECIDED]:
        out.append(u"符号で落ちた fact が表の決めで決まる fact より多い")
    if t2[RS][S2_REASONS[0]] <= t2[RS][S2_REASONS[1]]:
        out.append(u"文書の「`name` がいちばん多い(次は終わりの日)」が記録と合わない")
    return out


def fragment_problems(c):
    out = []
    lines = c.doc.splitlines()
    for want in expected_lines(c):
        if want not in lines:
            out.append(u"文書に記録から組んだ行が無い: %s" % want[:40])
    for frag in expected_fragments(c):
        if frag not in c.doc:
            out.append(u"文書に記録から組んだ字が無い: %s" % frag[:40])
    sec3 = section(c.doc, u"## §3 ", u"## §4 ")
    for frag in derived_lines(c):
        if frag not in sec3:
            out.append(u"§3 に記録から導いた字が無い: %s" % frag[:40])
    return out


def derived_numbers(c):
    out = set()
    for g in GROUPS:
        WG.ints_in(c.rec[g], out)
    WG.ints_in(c.rec[PRED_KEY], out)
    for g in GROUPS:                                              # 便 XA0 の記録の「表の外」「空」の数は §3 が引く
        out.add(str(c.prior[g][u"表の外の fact の数"]))
    s = c.rec[G_PROD]
    fact = s[u"fact の数"]
    t0, t1, t2 = s[u"段 0"], s[u"段 1"], s[u"段 2"]
    for st in STAGES:
        out.add(pct(s[st][FULL], fact))                              # 段ごとの率
    out.add(str(fact - t2[FULL]))                                   # 全部決まらない fact
    out.add(pct(fact - t2[FULL], fact))                              # 収まらない率
    out.add(str(fact - t2[DECIDED]))                                 # 表の決めで決まらない fact
    out.add(str(t2[DECIDED] - t2[FULL]))                             # 符号で落ちた fact
    out.add(str(int(round(100.0 * t2[FULL] / fact))))                # 95%
    out.add(str(int(round(100.0 * (fact - t2[FULL]) / fact))))       # 5%
    for i in range(3):
        for v in per_doc_range(c.rec, i):
            out.add(v)
    out |= set(BOUND_NUMBERS)
    return out


def doc_number_problems(c):
    allowed = set(STRUCTURAL) | derived_numbers(c)
    out = []
    for i, ln in enumerate(c.doc.splitlines(), 1):
        for tok in WG.doc_number_tokens(ln):
            if tok.replace(u",", u"") not in allowed:
                out.append(u"文書の %d 行目の数 %s が記録から組んだ数の外: %s" % (i, tok, ln[:30]))
    return out


def sec3_problems(c):
    u"""§3 は記録から導いた読みの節。3 桁以上の数・% は derived_lines の字だけ(それ以外の行に記録に無い 3 桁以上の数が無い)。"""
    s = section(c.doc, u"## §3 ", u"## §4 ")
    out = []
    if u"記録から導いた読み" not in s.splitlines()[0] or u"記録の監査で見たこと" not in s.splitlines()[0]:
        out.append(u"§3 の見出しが「記録から導いた読みと、記録の監査で見たこと」でない")
    keep = s
    for frag in derived_lines(c):
        keep = keep.replace(frag, u" ")
    left = re.sub(r"`[^`]*`|\b(?=[0-9]*[a-f])[0-9a-f]{8}\b", u" ", keep)
    if re.search(r"\d{3}|%|％", left):
        out.append(u"§3 の導いた字の外に 3 桁以上の数か % が在る")
    for p in (u"書類ごとの全部決まる fact の率(62 本。記録の書類ごとの数から導く)", u"同じ fact であることまでは測っていない", u"監査の席の読み", u"段 2 の書く欄が段 1 より多い理由"):
        if p not in s:
            out.append(u"§3 に字が無い: %s" % p)
    return out


def affirm_problems(c):
    return WG.affirm_problems(c)


def forbidden_problems(c):
    return WG.forbidden_problems(c)


def phrase_problems(c):
    return [u"文書に要点の字が無い: %s" % p for p in PHRASES if p not in c.doc]


def head_problems(c):
    head = c.doc.split(u"## §1")[0]
    return [u"文書の頭(§1 の前)に無い: %s" % p for p in HEAD_PHRASES if p not in head]


def doc_commit_problems(c):
    out = []
    for w in DOC_COMMITS:
        if w not in c.doc:
            out.append(u"文書に commit の字が無い: %s" % w)
    if not set(re.findall(r"\b(?=[0-9]*[a-f])[0-9a-f]{8}\b", c.doc)) <= set(DOC_COMMITS):
        out.append(u"文書が知らない commit の字を書いている")
    return out


CHECKS = collections.OrderedDict([
    (u"sha", sha_problems), (u"recount", recount_problems), (u"clean", record_clean_problems), (u"bound", bound_problems), (u"addendum", addendum_problems),
    (u"verdict", verdict_problems), (u"numbers", doc_number_problems), (u"frag", fragment_problems), (u"sanity", sanity_problems), (u"sec3", sec3_problems),
    (u"affirm", affirm_problems), (u"phrases", phrase_problems), (u"head", head_problems), (u"forbidden", forbidden_problems), (u"commits", doc_commit_problems)])


# ======================================================================================================
def blob_problems(root, prefix, at):
    return WG.blob_problems(root, prefix, at)


def commit_problems(root=REPO):
    u"""文書が書く 3 つの commit が実の履歴と合う: 封は d46f92aa が足し(1 commit)・追記と script と封の門は 4f836c94 が足し・記録は bf03d019 が足した。"""
    out = []
    for rel, want in ((SEAL_REL, [SEAL_COMMIT_SHORT]), (ADD_REL, [SCRIPT_COMMIT_SHORT]), (SCRIPT_REL, [SCRIPT_COMMIT_SHORT]), (SEAL_GATE_REL, [SCRIPT_COMMIT_SHORT]),
                      (RECORD_REL, [RECORD_COMMIT_SHORT])):
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
    u"""封 ⊏ script と封の門と追記 ⊏ 記録 ⊏ 結果の文書と門。未 commit は赤。"""
    out = list(PR.order_problems(root, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, [SCRIPT_REL, SEAL_GATE_REL, ADD_REL], [RECORD_REL, DOC_REL, GATE_REL]))
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
(変異を実行する前に書いた予測。右 = 赤になるべき検査。「整合」= 書類ごとの数・群の数・予測の欄を直し、recount は緑のまま当たり外れだけが変わる)
M1  記録の sha256 の写しを違う値に                                                    -> sha
M2  記録の「この script の sha256」を 1 字替える                                      -> sha
M3  記録の限界の欄の 1 行を消す                                                       -> sha
M4  記録が持つ便 XA0 の記録の sha256 を 1 字替える                                     -> sha
M5  書類 10 の段 2 の全部決まる fact を 1 増やす(群は直さない)                           -> recount
M6  本番の段 2 の全部決まる fact を 1 減らす(書類ごとは直さない)                         -> recount
M7  予測の欄 XA1-2 の分母を 1 増やす                                                  -> recount
M8  材料の書類の本数 67 → 68                                                          -> recount
M9  本番の段 0 の全部決まる fact を 1 増やす(便 XA0 の記録と違う・書類ごとも直す)         -> recount
M10 本番の 8 通りの ACC を 1 増やす                                                    -> recount
M11 本番の段 2 の書く欄の項「終わりの日を決める側の線 × 1」を 1 増やす(和は直さない)      -> recount
M12 書類 10 の段 1 の全部決まる fact を段 0 より 1 少なくする                            -> recount
M13 本番の段 2 の書く欄の比の % を 33.6 → 33.7                                          -> recount
M14 本番の段 2 の「終わりの日か member の組が違う」を 2 つの理由の和より大きくする          -> recount
M15 記録に docid の欄を足す                                                           -> clean
M16 封の写しから XA1-2 の境の字を消す                                                  -> bound
M17 封の写しから自己点検の条を消す                                                     -> bound
M18 追記の写しから「本番の数はまだ見ていない」を消す                                     -> addendum
M19 文書の XA1-1 の判定「当たり」を「**外れ**(下に外れた)」に                            -> verdict
M20 文書の件数の行 当たり 8・外れ 0 → 当たり 7・外れ 1                                   -> verdict
M21 文書の XA1-2 のセル 60165/63236(95.1%) → 60164/63236(95.1%)                        -> verdict
M22 文書の XA1-4 のセル「次は終わりの日の 848」を 849 に                                 -> verdict・numbers
M23 §4 の「人間に示す次の便の候補」の見出しの字を消す                                     -> verdict・phrases
M24 文書の予測の字 XA1-6「25% 以上 38% 未満」を「25% 以上 39% 未満」に                    -> verdict
M25 整合: 段 1 の全部決まる fact を増やして XA1-1 が 92% 以上(上に外れ)                  -> verdict
M26 整合: 段 1 の全部決まる fact を減らして XA1-1 が 82% 未満(下に外れ)                  -> verdict
M27 整合: 段 2 の全部決まる fact を減らして XA1-2 が 90% 未満                            -> verdict
M28 整合: 段 2 の終わりの日の理由を増やして XA1-3 が 3500 超                              -> verdict
M29 整合: 段 2 の name の理由を減らして XA1-4 の最多が name でなくなる                     -> verdict
M30 整合: 段 2 で 90% 以上の書類を 30 本以下に                                            -> verdict
M31 整合: 段 2 の書く欄を増やして XA1-6 が 38% 以上                                       -> verdict
M32 整合: 期間の種類が 2 つ在る name の fact を増やして XA1-7 が 0.5% 超                   -> verdict
M33 整合: 8 通りを ACC に寄せて XA1-8 が 15% 未満                                         -> verdict
M34 整合: 段 2 の全部決まる fact を 100% に(自己点検が発火)                                -> verdict
M35 文書 §2 の本番の fact 63236 を 63237 に(表の行)                                       -> frag・numbers
M36 文書の段の表の行の書く欄の数 148687 を 148688 に                                       -> frag・numbers
M37 文書の理由の表の「`unitRef` | 400 | 400 | 258」を 259 に                                -> frag・numbers
M38 文書に 9999 の言い切りを足す                                                          -> numbers
M39 文書の頭の「4.9%」を 5.0% に                                                          -> frag・numbers・head
M40 文書の「8 通り」の行の BCC 622 を 623 に                                               -> frag・numbers
M41 §3 の「段 2 は最小 92.4%」を 92.5% に                                                  -> frag・numbers
M42 §3 の「2997」を 2998 に                                                               -> frag・numbers
M43 §3 に 3 桁の数を足した行                                                               -> sec3
M44 §3 の「監査の席の読み」を消す                                                          -> sec3
M45 文書に「XBRL を作れる。」を引用の外で足す                                               -> affirm
M46 文書に「専用の道具が要らない。」を足す                                                  -> affirm
M47 文書に「人が書ける。」を足す                                                            -> affirm
M48 引用の行から「言えない」「読まない」を全部消す                                           -> affirm
M49 §4 の「言えないこと」を消す                                                             -> phrases
M50 頭の「この便からは言えない」を消す                                                       -> head
M51 頭の「先に負けと限界を書く」を消す                                                       -> head
M52 頭の「未使用ではない」を消す                                                             -> head
M53 頭の「LLM の席も道具(Arelle)も呼んでいない」を消す                                       -> head
M54 文書に「保証」を足す                                                                    -> forbidden
M55 文書に docID の形を足す                                                                 -> forbidden
M56 文書の commit の字 bf03d019 を 1 字替える                                                -> commits
M57 文書に知らない commit の字を足す                                                          -> commits
M58 文書の「AEE・BCE・BEE が 0 なのは」の字の数を替える(段 2 の書く欄が段 1 より多いを少ないに)  -> sanity(下に注)
M59 記録で AEE を 1 にして整合(和を合わせる)                                                  -> sanity
M60 整合: 記録の期間の種類が 2 つ在る name の数を 1 にする(fact は 0 のまま)                     -> recount・sanity

(1 回目の実行で外れた予測 2 つ。黙った変異は門を強くして表を直した)
- M12(段 1 を段 0 より 1 少なく): recount が黙った(群の和は段 0 より多いままで、書類ごとの順を見ていなかった)。書類ごとに 段 0 <= 段 1 <= 段 2 <= fact を足して赤になった。
- M58(§3 の「多い理由」を「少ない理由」に): sec3 が黙った(その字を縛っていなかった)。sec3 に「段 2 の書く欄が段 1 より多い理由」を足して赤になった。
"""


def rebuild(rec):
    u"""書類ごとの数・群の項はそのままに、群の導ける欄(段ごとの全部決まる fact・90% 以上の書類・書く欄の数・比・理由の数の上限・予測の欄)を作り直す(整合した変更)。"""
    for g in GROUPS:
        s = rec[g]
        docs = docs_of(rec, g)
        fact = s[u"fact の数"]
        for i, st in enumerate(STAGES):
            t = s[st]
            old_gap = t[DECIDED] - t[FULL]
            t[FULL] = sum(d[stage_key(i)] for d in docs)
            t[DOC90] = doc90(docs, i)
        t2 = s[u"段 2"]
        cl = t2[S2_ITEMS]
        outside = cl[ITEMS[7]] // 7
        inside = fact - outside
        for i, st in enumerate(STAGES):
            t = s[st]
            t[DECIDED] = min(inside, max(t[DECIDED], t[FULL]))
            und = inside - t[DECIDED]
            rs = t[RS]
            for k in list(rs):
                rs[k] = min(rs[k], und)
            if sum(rs.values()) < und:
                first = list(rs)[1]
                rs[first] += und - sum(rs.values())
        t2[S2_DIFF] = max(t2[S2_DIFF], max(t2[RS][S2_REASONS[1]], t2[RS][S2_REASONS[2]]))
        t2[S2_DIFF] = min(t2[S2_DIFF], t2[RS][S2_REASONS[1]] + t2[RS][S2_REASONS[2]])
        cl[ITEMS[6]] = 7 * (inside - t2[FULL])
        t2[CELLS] = sum(cl.values())
        t2[S2_NOT_CC] = t2[S2_TABLES] - t2[S2_COMBOS][u"ACC"] - t2[S2_COMBOS][u"BCC"]
        for st in STAGES:
            t = s[st]
            t[RATIO] = rate_row(t[CELLS], 7 * fact)
    rec[PRED_KEY] = pred_expected(rec)


def set_stage_full(rec, i, fn):
    for d in rec[u"書類"][DEV_COUNT:]:
        d[stage_key(i)] = fn(d)


def m_s1_high(c):
    set_stage_full(c.rec, 1, lambda d: max(d[stage_key(1)], (d[u"fact の数"] * 94 + 99) // 100))
    set_stage_full(c.rec, 2, lambda d: max(d[stage_key(2)], d[stage_key(1)]))
    rebuild(c.rec)


def m_s1_low(c):
    set_stage_full(c.rec, 1, lambda d: max(d[stage_key(0)], int(d[stage_key(1)] * 0.85)))
    rebuild(c.rec)


def m_s2_low(c):
    set_stage_full(c.rec, 2, lambda d: max(d[stage_key(0)], int(d[stage_key(2)] * 0.88)))
    set_stage_full(c.rec, 1, lambda d: max(d[stage_key(0)], min(d[stage_key(1)], d[stage_key(2)])))
    rebuild(c.rec)


def m_s2_full(c):
    for d in c.rec[u"書類"][DEV_COUNT:]:
        d[stage_key(2)] = d[u"fact の数"]
    rebuild(c.rec)


def m_diff(c):
    set_stage_full(c.rec, 2, lambda d: max(d[stage_key(1)], int(d[stage_key(2)] * 0.9)))
    t2 = c.rec[G_PROD][u"段 2"]
    t2[DECIDED] = c.rec[G_PROD][u"fact の数"] - c.rec[G_PROD][u"段 2"][S2_ITEMS][ITEMS[7]] // 7 - 3700
    t2[RS][S2_REASONS[1]] = 3600
    t2[S2_DIFF] = 3600
    rebuild(c.rec)


def m_name_low(c):
    t2 = c.rec[G_PROD][u"段 2"]
    t2[RS][S2_REASONS[0]] = 800
    rebuild(c.rec)
    t2[RS][S2_REASONS[0]] = 800
    c.rec[PRED_KEY] = pred_expected(c.rec)


def m_doc90_low(c):
    for d in c.rec[u"書類"][DEV_COUNT:DEV_COUNT + 40]:
        d[stage_key(2)] = max(d[stage_key(0)], min(d[stage_key(2)], (d[u"fact の数"] * 89) // 100))
    set_stage_full(c.rec, 1, lambda d: max(d[stage_key(0)], min(d[stage_key(1)], d[stage_key(2)])))
    rebuild(c.rec)


def m_cells_high(c):
    t2 = c.rec[G_PROD][u"段 2"]
    t2[S2_ITEMS][ITEMS[1]] += 40000
    rebuild(c.rec)


def m_period(c):
    s = c.rec[G_PROD]
    s[PERIOD_N] = 40
    s[PERIOD_F] = 400
    rebuild(c.rec)


def m_acc(c):
    t2 = c.rec[G_PROD][u"段 2"]
    t2[S2_COMBOS][u"ACC"] += sum(v for k, v in t2[S2_COMBOS].items() if k not in (u"ACC", u"BCC"))
    for k in list(t2[S2_COMBOS]):
        if k not in (u"ACC", u"BCC"):
            t2[S2_COMBOS][k] = 0
    t2[S2_COMBOS][u"ACC"] += t2[S2_TABLES] - sum(t2[S2_COMBOS].values())
    rebuild(c.rec)


def m_stage0(c):
    d = c.rec[u"書類"][DEV_COUNT + 3]
    d[stage_key(0)] += 1
    rebuild(c.rec)


def m_stage1_below(c):
    d = c.rec[u"書類"][9]
    d[stage_key(1)] = d[stage_key(0)] - 1
    rebuild(c.rec)


def m_aee(c):
    t2 = c.rec[G_PROD][u"段 2"]
    t2[S2_COMBOS][u"AEE"] = 1
    t2[S2_COMBOS][u"ACC"] -= 1
    rebuild(c.rec)


def m_period_name(c):
    c.rec[G_PROD][PERIOD_N] = 1


def m_wrong_cells_text(c):
    rep(c, u"段 2 の書く欄が段 1 より多い理由", u"段 2 の書く欄が段 1 より少ない理由")


def m_drop_quote_negation(c):
    lines = []
    for ln in c.doc.splitlines():
        if WG.QUOTED_CLAIM.search(ln):
            for w in (u"言えないこと", u"言えない", u"読まない", u"示していない"):
                ln = ln.replace(w, u"X")
        lines.append(ln)
    c.doc = u"\n".join(lines)


def add_sec3(c, text):
    rep(c, u"## §4 ", text + u"\n\n## §4 ")


MUTATIONS = (
    (u"M1 記録の sha256 の写しを違う値に", lambda c: c.shas.__setitem__(RECORD_REL, u"0" * 64), (u"sha",)),
    (u"M2 記録の script の sha256 を 1 字替える", lambda c: c.rec.__setitem__(u"この script の sha256", u"f" + c.rec[u"この script の sha256"][1:]), (u"sha",)),
    (u"M3 記録の限界の欄の 1 行を消す", lambda c: c.rec.__setitem__(u"限界", c.rec[u"限界"][1:]), (u"sha",)),
    (u"M4 記録が持つ便 XA0 の記録の sha256 を 1 字替える", lambda c: c.rec[u"材料"].__setitem__(u"便 XA0 の記録の sha256", u"0" + c.rec[u"材料"][u"便 XA0 の記録の sha256"][1:]), (u"sha",)),
    (u"M5 書類 10 の段 2 の全部決まる fact を 1 増やす", lambda c: c.rec[u"書類"][9].__setitem__(stage_key(2), c.rec[u"書類"][9][stage_key(2)] + 1), (u"recount",)),
    (u"M6 本番の段 2 の全部決まる fact を 1 減らす", lambda c: c.rec[G_PROD][u"段 2"].__setitem__(FULL, c.rec[G_PROD][u"段 2"][FULL] - 1), (u"recount",)),
    (u"M7 予測の欄 XA1-2 の分母を 1 増やす", lambda c: c.rec[PRED_KEY][PK[1]].__setitem__(u"分母", c.rec[PRED_KEY][PK[1]][u"分母"] + 1), (u"recount",)),
    (u"M8 材料の書類の本数を 68 に", lambda c: c.rec[u"材料"].__setitem__(u"書類の本数", 68), (u"recount",)),
    (u"M9 段 0 の全部決まる fact を 1 増やす(書類ごとも直す)", m_stage0, (u"recount",)),
    (u"M10 本番の 8 通りの ACC を 1 増やす", lambda c: c.rec[G_PROD][u"段 2"][S2_COMBOS].__setitem__(u"ACC", c.rec[G_PROD][u"段 2"][S2_COMBOS][u"ACC"] + 1), (u"recount",)),
    (u"M11 本番の書く欄の項「終わりの日を決める側の線 × 1」を 1 増やす", lambda c: c.rec[G_PROD][u"段 2"][S2_ITEMS].__setitem__(ITEMS[2], c.rec[G_PROD][u"段 2"][S2_ITEMS][ITEMS[2]] + 1), (u"recount",)),
    (u"M12 書類 10 の段 1 の全部決まる fact を段 0 より 1 少なくする", m_stage1_below, (u"recount",)),
    (u"M13 本番の段 2 の書く欄の比の % を 33.7 に", lambda c: c.rec[G_PROD][u"段 2"][RATIO].__setitem__(u"%", 33.7), (u"recount",)),
    (u"M14 本番の段 2 の「終わりの日か member の組が違う」を 2 つの理由の和より大きくする", lambda c: c.rec[G_PROD][u"段 2"].__setitem__(S2_DIFF, 900), (u"recount",)),
    (u"M15 記録に docid の欄を足す", lambda c: c.rec[u"書類"][0].__setitem__(u"docid", u"x"), (u"clean",)),
    (u"M16 封の写しから XA1-2 の境の字を消す", lambda c: rep(c, u"段 2 の全部決まる fact は、fact の 90% 以上", u"X", attr="seal"), (u"bound",)),
    (u"M17 封の写しから自己点検の条を消す", lambda c: rep(c, u"段 2 の全部決まる fact がちょうど 100%", u"X", attr="seal"), (u"bound",)),
    (u"M18 追記の写しから「本番の数はまだ見ていない」を消す", lambda c: rep(c, u"本番の数はまだ見ていない", u"X", attr="add"), (u"addendum",)),
    (u"M19 XA1-1 の判定を外れに", lambda c: rep(c, u"| 57692/63236(91.2%) | 当たり |", u"| 57692/63236(91.2%) | **外れ**(下に外れた) |"), (u"verdict",)),
    (u"M20 件数の行を当たり 7・外れ 1 に", lambda c: rep(c, u"- 当たり 8・外れ 0。", u"- 当たり 7・外れ 1。"), (u"verdict",)),
    (u"M21 XA1-2 のセルの 60165 を 60164 に", lambda c: rep(c, u"| 60165/63236(95.1%) |", u"| 60164/63236(95.1%) |"), (u"verdict",)),
    (u"M22 XA1-4 のセルの 848 を 849 に", lambda c: rep(c, u"(次は終わりの日の 848)", u"(次は終わりの日の 849)"), (u"verdict", u"numbers")),
    (u"M23 §4 の次の便の候補の見出しの字を消す", lambda c: rep(c, u"人間に示す次の便の候補**(封 §6。XA1-2 が当たりなので示す)", u"X"), (u"verdict", u"phrases")),
    (u"M24 XA1-6 の予測の字を 39% 未満に", lambda c: rep(c, u"25% 以上 38% 未満", u"25% 以上 39% 未満"), (u"verdict",)),
    (u"M25 整合: 段 1 が 92% 以上(XA1-1 が上に外れ)", m_s1_high, (u"verdict",)),
    (u"M26 整合: 段 1 が 82% 未満(XA1-1 が下に外れ)", m_s1_low, (u"verdict",)),
    (u"M27 整合: 段 2 が 90% 未満", m_s2_low, (u"verdict",)),
    (u"M28 整合: 終わりの日の理由を増やして XA1-3 が 3500 超", m_diff, (u"verdict",)),
    (u"M29 整合: name の理由を減らして最多が name でなくなる", m_name_low, (u"verdict",)),
    (u"M30 整合: 段 2 で 90% 以上の書類を 30 本以下に", m_doc90_low, (u"verdict",)),
    (u"M31 整合: 段 2 の書く欄を増やして XA1-6 が 38% 以上", m_cells_high, (u"verdict",)),
    (u"M32 整合: 期間の種類が 2 つ在る name の fact を増やす", m_period, (u"verdict",)),
    (u"M33 整合: 8 通りを ACC・BCC に寄せて XA1-8 が 15% 未満", m_acc, (u"verdict",)),
    (u"M34 整合: 段 2 を 100% にする(自己点検が発火)", m_s2_full, (u"verdict",)),
    (u"M35 §2 の本番の fact を 63237 に", lambda c: rep(c, u"| fact | 63236 |", u"| fact | 63237 |"), (u"frag", u"numbers")),
    (u"M36 段の表の書く欄の数 148687 を 148688 に", lambda c: rep(c, u"| 148687 |", u"| 148688 |"), (u"frag", u"numbers")),
    (u"M37 理由の表の `unitRef` の 258 を 259 に", lambda c: rep(c, u"| `unitRef` | 400 | 400 | 258 |", u"| `unitRef` | 400 | 400 | 259 |"), (u"frag", u"numbers")),
    (u"M38 文書に 9999 の言い切りを足す", lambda c: add_doc(c, u"fact の行は 9999 本に近い。"), (u"numbers",)),
    (u"M39 頭の「4.9%」を 5.0% に", lambda c: rep(c, u"分けても 4.9% は", u"分けても 5.0% は"), (u"frag", u"numbers", u"head")),
    (u"M40 8 通りの行の BCC 622 を 623 に", lambda c: rep(c, u"BCC 622", u"BCC 623"), (u"frag", u"numbers")),
    (u"M41 §3 の「段 2 は最小 92.4%」を 92.5% に", lambda c: rep(c, u"段 2 は最小 92.4%", u"段 2 は最小 92.5%"), (u"frag", u"numbers")),
    (u"M42 §3 の 2997 を 2998 に", lambda c: rep(c, u"2997", u"2998"), (u"frag", u"numbers")),
    (u"M43 §3 に 3 桁の数を足した行", lambda c: add_sec3(c, u"- 別の確かめは 100 本。"), (u"sec3",)),
    (u"M44 §3 の「監査の席の読み」を消す", lambda c: rep(c, u"監査の席の読み", u"X"), (u"sec3",)),
    (u"M45 文書に「XBRL を作れる。」を引用の外で足す", lambda c: add_doc(c, u"XBRL を作れる。"), (u"affirm",)),
    (u"M46 文書に「専用の道具が要らない。」を足す", lambda c: add_doc(c, u"専用の道具が要らない。"), (u"affirm",)),
    (u"M47 文書に「人が書ける。」を足す", lambda c: add_doc(c, u"紙は人が書ける。"), (u"affirm",)),
    (u"M48 引用の行から「言えない」「読まない」を消す", m_drop_quote_negation, (u"affirm",)),
    (u"M49 「言えないこと」を消す", lambda c: drop_all(c, u"言えないこと"), (u"phrases",)),
    (u"M50 頭の「この便からは言えない」を消す", lambda c: rep(c, u"、この便からは言えない。**", u"、X。**"), (u"head",)),
    (u"M51 頭の「先に負けと限界を書く」を消す", lambda c: drop_all(c, u"先に負けと限界を書く"), (u"head",)),
    (u"M52 頭の「未使用ではない」を消す", lambda c: rep(c, u"未使用ではない", u"X"), (u"head",)),
    (u"M53 頭の「LLM の席も道具(Arelle)も呼んでいない」を消す", lambda c: rep(c, u"LLM の席も道具(Arelle)も呼んでいない", u"X"), (u"head",)),
    (u"M54 文書に「保証」を足す", lambda c: add_doc(c, u"保証する。"), (u"forbidden",)),
    (u"M55 文書に docID の形を足す", lambda c: add_doc(c, u"書類 S100ABCD。"), (u"forbidden",)),
    (u"M56 文書の commit の字 bf03d019 を 1 字替える", lambda c: rep(c, u"bf03d019", u"bf03d018"), (u"commits",)),
    (u"M57 文書に知らない commit の字を足す", lambda c: add_doc(c, u"commit 1a2b3c4d。"), (u"commits",)),
    (u"M58 §3 の「書く欄が段 1 より多い理由」を「少ない理由」に", m_wrong_cells_text, (u"sec3",)),
    (u"M59 整合: AEE を 1 にして和を合わせる", m_aee, (u"sanity",)),
    (u"M60 期間の種類が 2 つ在る name の数を 1 に(fact は 0 のまま)", m_period_name, (u"recount", u"sanity")),
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
        s = self.c.rec[G_PROD]
        self.assertEqual((63236, 57692, 60165, 3071, 62, 62), (s[u"fact の数"], s[u"段 1"][FULL], s[u"段 2"][FULL], s[u"fact の数"] - s[u"段 2"][FULL], s[u"段 2"][DOC90], s[LIVE]))
        self.assertEqual((0, 47, 62), tuple(s[st][DOC90] for st in STAGES))
        self.assertEqual((u"name の違い",), tuple(reason_max(s[u"段 2"])))
        self.assertEqual(((u"75.1", u"85.0"), (u"87.1", u"95.8"), (u"92.4", u"98.7")), tuple(per_doc_range(self.c.rec, i) for i in range(3)))

    def test_c_1_the_seal_has_the_bound_phrases(self):
        self.assertEqual([], bound_problems(self.c))
        self.assertEqual([], addendum_problems(self.c))

    def test_c_2_the_verdicts_are_decided_again_and_equal_the_document(self):
        self.assertEqual([], verdict_problems(self.c))
        j = judge(self.c.rec)
        self.assertEqual(8, sum(1 for v in j.values() if v[0]))

    def test_d_1_every_number_in_the_document_is_bound_to_the_record(self):
        self.assertEqual([], doc_number_problems(self.c))

    def test_d_2_the_table_rows_and_the_statements_equal_the_record(self):
        self.assertEqual([], fragment_problems(self.c))
        self.assertEqual([], sanity_problems(self.c))

    def test_d_3_section3_holds_only_the_derived_numbers(self):
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

    def test_f_3_the_blob_check_lists_the_five_frozen_files_at_their_commits(self):
        self.assertEqual([SEAL_REL, ADD_REL, SCRIPT_REL, SEAL_GATE_REL, RECORD_REL], list(BLOB_AT))
        self.assertEqual([SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT], list(BLOB_AT.values()))
        self.assertEqual((SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT), DOC_COMMITS)

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
        self.assertGreaterEqual(len(MUTATIONS), 40)

    def test_g_2_the_unmutated_copy_is_green_on_every_check(self):
        c = Ctx().copy()
        for k, fn in CHECKS.items():
            self.assertEqual([], fn(c), k)

    def test_g_3_the_recount_stays_green_when_the_data_changes_consistently_but_the_verdict_does_not(self):
        for fn, key in ((m_s1_high, u"XA1-1"), (m_s1_low, u"XA1-1"), (m_s2_low, u"XA1-2"), (m_diff, u"XA1-3"), (m_name_low, u"XA1-4"), (m_doc90_low, u"XA1-5"),
                        (m_cells_high, u"XA1-6"), (m_period, u"XA1-7"), (m_acc, u"XA1-8")):
            c = Ctx().copy()
            fn(c)
            self.assertEqual([], recount_problems(c), fn.__name__)
            self.assertNotEqual([], verdict_problems(c), fn.__name__)
            self.assertNotEqual(judge(Ctx().rec)[key][0], judge(c.rec)[key][0], (fn.__name__, key))

    def test_g_4_every_check_name_a_mutation_names_exists_and_every_check_has_a_mutation(self):
        named = set(k for _, _, ks in MUTATIONS for k in ks)
        self.assertEqual(set(CHECKS), named)

    def test_g_5_the_judgement_edges_at_the_seal_bounds(self):
        u"""境の 1 つ手前と境の数(丸める前の整数): XA1-1 は 82% ちょうどが当たり・92% ちょうどが外れ(上が含まない)。XA1-6 は 25% ちょうどが当たり・38% ちょうどが外れ。XA1-3 は 3500 が当たり。"""
        def with_(**kw):
            c = Ctx().copy()
            s = c.rec[G_PROD]
            s[u"fact の数"] = 1000
            s[PERIOD_F] = 0
            s[u"段 1"][FULL] = 850
            s[u"段 2"][FULL] = 950
            s[u"段 2"][DOC90] = 40
            s[u"段 2"][CELLS] = 3000
            s[u"段 2"][S2_DIFF] = 100
            s[u"段 2"][S2_TABLES] = 100
            s[u"段 2"][S2_NOT_CC] = 30
            for key, val in kw.items():
                if key == u"s1":
                    s[u"段 1"][FULL] = val
                elif key == u"s2":
                    s[u"段 2"][FULL] = val
                elif key == u"s2doc":
                    s[u"段 2"][DOC90] = val
                elif key == u"cells":
                    s[u"段 2"][CELLS] = val
                elif key == u"diff":
                    s[u"段 2"][S2_DIFF] = val
                elif key == u"nocc":
                    s[u"段 2"][S2_NOT_CC] = val
                elif key == u"pf":
                    s[PERIOD_F] = val
            return judge(c.rec)
        self.assertTrue(with_(s1=820)[u"XA1-1"][0])
        self.assertFalse(with_(s1=819)[u"XA1-1"][0])
        self.assertFalse(with_(s1=920)[u"XA1-1"][0])
        self.assertTrue(with_(s1=919)[u"XA1-1"][0])
        self.assertTrue(with_(s2=900)[u"XA1-2"][0])
        self.assertFalse(with_(s2=899)[u"XA1-2"][0])
        self.assertTrue(with_(diff=3500)[u"XA1-3"][0])
        self.assertFalse(with_(diff=3501)[u"XA1-3"][0])
        self.assertTrue(with_(s2doc=31)[u"XA1-5"][0])
        self.assertFalse(with_(s2doc=30)[u"XA1-5"][0])
        self.assertTrue(with_(cells=1750)[u"XA1-6"][0])
        self.assertFalse(with_(cells=1749)[u"XA1-6"][0])
        self.assertFalse(with_(cells=2660)[u"XA1-6"][0])
        self.assertTrue(with_(cells=2659)[u"XA1-6"][0])
        self.assertTrue(with_(pf=5)[u"XA1-7"][0])
        self.assertFalse(with_(pf=6)[u"XA1-7"][0])
        self.assertTrue(with_(nocc=15)[u"XA1-8"][0])
        self.assertFalse(with_(nocc=14)[u"XA1-8"][0])

    def test_g_6_the_most_common_reason_must_be_alone_and_name(self):
        c = Ctx().copy()
        t2 = c.rec[G_PROD][u"段 2"]
        t2[RS][S2_REASONS[1]] = t2[RS][S2_REASONS[0]]                 # 同数は「name だけがいちばん多い」でない
        self.assertFalse(judge(c.rec)[u"XA1-4"][0])
        c = Ctx().copy()
        t2 = c.rec[G_PROD][u"段 2"]
        t2[RS][S2_REASONS[1]] = t2[RS][S2_REASONS[0]] + 1
        self.assertFalse(judge(c.rec)[u"XA1-4"][0])
        self.assertTrue(judge(Ctx().rec)[u"XA1-4"][0])

    def test_g_7_the_miss_direction_follows_the_bound(self):
        c = Ctx().copy()
        m_s1_high(c)
        self.assertEqual(u"上", judge(c.rec)[u"XA1-1"][1])
        c = Ctx().copy()
        m_s1_low(c)
        self.assertEqual(u"下", judge(c.rec)[u"XA1-1"][1])


if __name__ == "__main__":
    unittest.main()
