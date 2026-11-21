# -*- coding: utf-8 -*-
u"""結果の門: 封 docs/XBRL_SHEET_BUILD_SEAL_2026-11-22.md(483e3e93)の結果の文書 docs/XBRL_SHEET_BUILD_RESULT_2026-11-22.md(便 XS0)。

封の門 ``test_xbrl_sheet_build_seal.py`` の次の段。**追跡されている記録・script・封・封の門・結果の文書と git の履歴だけを読む**(書類の置き場も道具(Arelle)も読まない・通信しない・鍵は読まない)。
便 XA0 の結果の門 ``test_xbrl_sheet_wall_result.py`` の部品(読み・sha256・% の丸め・節の切り出し・数のトークン・禁止語・blob・順序の道具)を読み込んで使う(門としては走らせない)。
検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表で 1 つずつ(木の file は変異させず、``Ctx`` の写しに当てる)。

 a script・記録・封・封の門の sha256(字で留める)・記録の script の sha256・封の commit の欄・記録の限界の欄が script の字と同じ
 b 記録の数え直し: 書類ごとの数から、**script の関数を使わずに**、3 つの塊(開発の 5 本・本番だけの 62 本・全部)の集計の全部の欄を数え直す(秒の合計だけ 0.1 刻みの丸めの幅で)。
   書類ごとの関係(紙の欄の項の和・全部同じの導き方・表 F が同じの導き方・理由の数と 1 つずつ書く fact の数)・予測の判定に要る数を群の数から作り直した値と照らす
 c 予測 XS0-1〜XS0-8 の当たり外れを、封 §4 の字から取った境(丸める前の整数で。下限は含む・上限は XS0-3・XS0-6・XS0-8 が含まない)と記録から決め直し、文書 §1 の表・件数と同じことを見る。
   封 §4 の「先に自分の欠陥を疑う場合」・封 §6 の決め(XS0-1 と XS0-4 が当たりなら次の便の候補を示す)と文書が合う
 d 結果の文書の数: 数字を含む行は全部、記録(と便 XA0・便 XA1 の記録)から組んだ数の並びの内。表の行・言い切りは記録から組んだ字とそのまま照らす。
   §2 の書類ごとの率(最小・中央・最大)は書類ごとの数から導き直す。1 つずつ書く fact が便 XA1 の「全部決まらない fact」と同じ数であること・紙の欄の比が便 XA1 の段 2 より多いことは便 XA1 の記録と照らす
 e 文書の要点の字・頭の負けと限界・禁止語・「作れる」「専用の道具が要らない」「人が書ける」を肯定で書かない・docID と EDINET コードの形
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


WG = load_module("tests/measure/test_xbrl_sheet_wall_result.py", "xbrl_sheet_wall_result_gate_for_build_result_gate")     # 便 XA0 の結果の門の部品。門としては走らせない
SG = load_module("tests/measure/test_xbrl_sheet_build_seal.py", "xbrl_sheet_build_seal_gate_for_result_gate")               # 封の門の部品。門としては走らせない
PR = SG.load_order_helpers()
MS = SG.MS

read, sha_file, guard, pct, section, rep = WG.read, WG.sha_file, WG.guard, WG.pct, WG.section, WG.rep
add_doc, drop_all = WG.add_doc, WG.drop_all

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
RECORD_REL = SG.RECORD_REL
XA1_RECORD_REL = "fixtures/xbrl/cd8/sheet_context_2026-11-22.json"
XA0_RECORD_REL = "fixtures/xbrl/cd8/sheet_wall_2026-11-22.json"
GATE_REL = "tests/measure/test_xbrl_sheet_build_result.py"
DOC_REL = "docs/XBRL_SHEET_BUILD_RESULT_2026-11-22.md"
SCRIPT_COMMIT_SHORT = "6d82a612"                  # script と封の門を足した commit
RECORD_COMMIT_SHORT = "7706dc70"                  # 記録を足した commit
BLOB_AT = collections.OrderedDict([
    (SEAL_REL, SEAL_COMMIT_SHORT), (SCRIPT_REL, SCRIPT_COMMIT_SHORT), (SEAL_GATE_REL, SCRIPT_COMMIT_SHORT), (RECORD_REL, RECORD_COMMIT_SHORT)])
DOC_COMMITS = (SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT)

SHA_PIN = collections.OrderedDict([
    (RECORD_REL, "f3f781d6c44820e38172d37bbc0135ba32fbc2b2676a74f17b64cb28af66d539"),
    (SCRIPT_REL, "52d092d119e347890ec24fa1fbfb7dbd94961a5f085a13ce6600bd1a48688a82"),
    (SEAL_GATE_REL, "0e8956c53399f42f44a50d0e212bad71db51d764898c8570e6ccee28f937602f"),
    (SEAL_REL, "e902b8de9a8f8d06e44284710b15083473681616f0c90809a3ec02ccc72df6e9"),
    (XA1_RECORD_REL, "9f9b654c321bd2b41fc6fad991df98f12f574f510402a5108334a26219a4809a"),
    (XA0_RECORD_REL, "f5d45ab221809b19d87a58801127504055e45d689d48586463babf9a6dbf0a09")])

DEV_COUNT = 5
DOC_COUNT = 67
G_DEV, G_PROD = WG.G_DEV, WG.G_PROD
G_ALL = u"全部"
GROUPS = (G_DEV, G_PROD, G_ALL)
AGG = u"集計"
PRED_KEY = u"予測の判定に要る数(XS0-1〜XS0-8。本番だけの 62 本。当たり・外れは結果の文書で)"
PK = (u"XS0-1 表 F が同じ書類", u"XS0-2 attrs が違う fact / fact(属性を作れた書類)", u"XS0-3 1 つずつ書く fact / fact(紙を作れた書類)", u"XS0-4 道具が読む fact が同じ書類",
      u"XS0-5 属性を作る命令が断った書類", u"XS0-6 紙の欄の数 / fact の数 × 7", u"XS0-7 混ぜ物が効いた書類 / 作れた書類", u"XS0-8 そのほかの属性を持つ fact / fact(紙を作れた書類)")
STAGES = (u"紙を作る", u"属性を作る", u"組む")
HAND_REASONS = (u"表の外", u"便 XA1 の段 2 で全部決まらない", u"文脈の定義が 2 つ以上", u"期間の種類が name の決めと違う")
CELL_KEYS = (u"書式の類の決め", u"name ごとの期間の種類", u"表ごとの 3", u"要素の線 × 4", u"終わりの日を決める側の線 × 1", u"member の組を決める側の線 × 1", u"空の fact の印", u"そのほかの属性",
             u"1 つずつ書く fact × 7")
HAND_ITEM = CELL_KEYS[8]
ATTR_KEYS = (u"属性 name", u"属性 contextRef", u"属性 unitRef", u"属性 decimals", u"属性 scale", u"属性 format", u"属性 sign", u"属性 footnoteRefs", u"属性 id", u"属性 escape", u"属性 xsi:nil")
IDS = (u"XS0-1", u"XS0-2", u"XS0-3", u"XS0-4", u"XS0-5", u"XS0-6", u"XS0-7", u"XS0-8")

BOUND_SEAL_PHRASES = (u"表 F が同じ書類は 60 本以上", u"`attrs` が元と違う fact は、fact の 0.2% 以下", u"1 つずつ書く fact は、fact の 4.8% 以上 6.5% 未満", u"道具が読む fact が元と同じ書類は 60 本以上",
                      u"属性を作る命令が断った書類は 2 本以下", u"紙の欄の比は 33.6% 以上 38% 未満", u"混ぜ物が効いた書類は、作れた書類の全部", u"そのほかの属性を持つ fact は、fact の 2% 以上 10% 未満",
                      u"1 つずつ書く fact が 3071 より少ない・表 F が同じなのに道具が読む fact が違う書類が在る・表 F が違うのに 1 つずつ書く fact が 0 の書類・混ぜ物を作れなかった書類が 6 本以上・断った書類が 6 本以上",
                      u"XS0-1 と XS0-4 が当たりなら、次の便の候補を人間に示す", u"「XBRL を作れる」「専用の道具が要らない」は、この便からは言えない")
# 文書 §1 の表の予測の欄に在るべき境の字(封 §4 の同じ行にも在る)
ROW_BOUND = collections.OrderedDict([(u"XS0-1", u"60 本以上"), (u"XS0-2", u"0.2% 以下"), (u"XS0-3", u"4.8% 以上 6.5% 未満"), (u"XS0-4", u"60 本以上"), (u"XS0-5", u"2 本以下"),
                                      (u"XS0-6", u"33.6% 以上 38% 未満"), (u"XS0-7", u"全部"), (u"XS0-8", u"2% 以上 10% 未満")])
HEAD_PHRASES = (u"先に負けと限界を書く", u"記録から 1 つずつ読んだもの", u"外れは XS0-6(紙の欄の比)", u"「人が紙を書けば XBRL が作れる」とは読まない",
                u"紙は答え(元の書類)から作っている", u"人が書く紙が正しいかは測っていない",
                u"持ち込み(素の本文・数の置き場・表 H の全部・文の fact・脚注・提出者別タクソノミの表)はこの便で作っていない",
                u"どの数に fact を付けるか(置き場)と、文脈・単位の定義は元から写している", u"作りから当たりやすい", u"規則どおりに作れば元と同じになる",
                u"本番の前に開発の 5 本で数を見ている", u"未使用ではない", u"その fact が元と同じになるのは当たり前", u"混ぜ物は 1 本につき 1 つ・`name` だけ",
                u"変えた先の `name` の期間の種類を紙に足している", u"EDINET の本物の検査に通ることは言えない", u"便 XA0・便 XA1・便 XB0・便 XT0・便 XP0 の限界の全部を継ぐ",
                u"0 USD・LLM の席は呼んでいない", u"engine は 0 行", u"書類は便 XG0 と同じ 67 本",
                u"「XBRL を作れる」「専用の道具が要らない」は、この便からは言えない")
PHRASES = (u"言えること", u"言えないこと", u"人間に示す次の便の候補", u"別の封が先", u"盲検ではない", u"実装で決めた所", u"人が紙を書けるか・人が書いた紙が正しいか",
           u"数の置き場と文脈・単位の定義を紙から作れるか", u"EDINET の本物の検査に通るか", u"相手の問いへの、この便からの答え", u"印刷会社の道具の代わりと言うには")
STRUCTURAL = WG.STRUCTURAL
BOUND_NUMBERS = set([u"60", u"0.2", u"4.8", u"6.5", u"2", u"33.6", u"38", u"10", u"62", u"67", u"5", u"6", u"7", u"8", u"3", u"4"])
QUOTED_CLAIM = WG.QUOTED_CLAIM
AFFIRM_WORDS = tuple(WG.AFFIRM_WORDS) + (u"人が紙を書ける(?!か)", u"紙は人が書ける", u"紙を人が書ける", u"人が紙を書けば XBRL が作れる(?!」)")


# ======================================================================================================
class Ctx(object):
    u"""検査が見る写し。変異はこの写しを変える(木の file は変えない)。"""

    def __init__(self):
        self.rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        self.xa1 = json.loads(read(XA1_RECORD_REL), object_pairs_hook=collections.OrderedDict)
        self.xa0 = json.loads(read(XA0_RECORD_REL), object_pairs_hook=collections.OrderedDict)
        self.doc = read(DOC_REL)
        self.seal = read(SEAL_REL)
        self.shas = collections.OrderedDict((rel, sha_file(rel)) for rel in SHA_PIN)

    def copy(self):
        c = Ctx.__new__(Ctx)
        c.rec = copy.deepcopy(self.rec)
        c.xa1 = copy.deepcopy(self.xa1)
        c.xa0 = copy.deepcopy(self.xa0)
        c.doc = self.doc
        c.seal = self.seal
        c.shas = collections.OrderedDict(self.shas)
        return c


# ======================================================================================================
# b 数え直し(script の関数は使わない)
def docs_of(rec, g):
    docs = rec[u"書類"]
    if g == G_DEV:
        return docs[:DEV_COUNT]
    if g == G_PROD:
        return docs[DEV_COUNT:]
    return docs


def rate_row(n, d):
    return collections.OrderedDict([(u"数", n), (u"分母", d), (u"%", float(pct(n, d)) if d else 0.0)])


def totals(docs):
    u"""書類ごとの数から、記録の集計の 1 つの塊の欄を数え直す(秒の合計は 0.1 刻みに丸めた値)。"""
    live = [d for d in docs if d[u"断った段"] != STAGES[0]]
    made = [d for d in docs if d[u"属性を作れた"]]
    t = collections.OrderedDict()
    t[u"書類の数"] = len(docs)
    t[u"断った書類の数"] = sum(1 for d in docs if d[u"断った"])
    t[u"断った段ごとの数"] = collections.OrderedDict((st, sum(1 for d in docs if d[u"断った段"] == st)) for st in STAGES)
    reasons = collections.OrderedDict()
    for d in docs:
        if d[u"断った"]:
            reasons[d[u"断った理由"]] = reasons.get(d[u"断った理由"], 0) + 1
    t[u"断った理由ごとの数"] = reasons
    t[u"紙を作れた書類の数"] = len(live)
    fact = sum(d[u"fact の数"] for d in live)
    t[u"fact の数(紙を作れた書類)"] = fact
    t[u"1 つずつ書く fact の数"] = sum(d[u"1 つずつ書く fact の数"] for d in live)
    t[u"1 つずつ書く fact の理由ごとの数(重ねて数える)"] = collections.OrderedDict((k, sum(d[u"1 つずつ書く fact の理由(重ねて数える)"][k] for d in live)) for k in HAND_REASONS)
    t[u"そのほかの属性を持つ fact の数"] = sum(d[u"そのほかの属性を持つ fact の数"] for d in live)
    t[u"属性を作れた書類の数"] = len(made)
    t[u"fact の数(属性を作れた書類)"] = sum(d[u"fact の数"] for d in made)
    t[u"表 F が同じ書類の数"] = sum(1 for d in docs if d[u"表 F が同じ"])
    t[u"attrs が違う fact の数"] = sum(d[u"attrs が違う fact の数"] for d in made)
    t[u"attrs が違う属性ごとの fact の数(重ねて数える)"] = collections.OrderedDict((k, sum(d[u"attrs が違う属性ごとの fact の数(重ねて数える)"][k] for d in made)) for k in ATTR_KEYS)
    t[u"組めた書類の数"] = sum(1 for d in docs if d[u"組めた"])
    t[u"fact が同じ書類の数"] = sum(1 for d in docs if d[u"fact が同じ"])
    t[u"鳴り方が同じ書類の数"] = sum(1 for d in docs if d[u"鳴り方が同じ"])
    t[u"タクソノミが同じ書類の数"] = sum(1 for d in docs if d[u"タクソノミが同じ"])
    t[u"全部同じ書類の数"] = sum(1 for d in docs if d[u"全部同じ"])
    t[u"2 回組んで同じ書類の数"] = sum(1 for d in docs if d[u"2 回組んで同じ"])
    t[u"混ぜ物を作れた書類の数"] = sum(1 for d in docs if d[u"混ぜ物"][u"作れた"])
    t[u"混ぜ物が効いた書類の数"] = sum(1 for d in docs if d[u"混ぜ物"][u"効いた"])
    items = collections.OrderedDict((k, sum(d[u"紙の欄の数(項ごと)"][k] for d in live)) for k in CELL_KEYS)
    t[u"紙の欄の数(項ごと)"] = items
    t[u"紙の欄の数"] = sum(items.values())
    t[u"fact の数 × 7"] = 7 * fact
    t[u"紙の欄の比"] = rate_row(t[u"紙の欄の数"], 7 * fact)
    t[u"属性を作る命令の秒の合計"] = round(sum(d[u"属性を作る命令の秒"] for d in docs), 1)
    t[u"組む命令の秒の合計"] = round(sum(d[u"組む命令の秒"] for d in docs), 1)
    return t


SEC_KEYS = (u"属性を作る命令の秒の合計", u"組む命令の秒の合計")


def norm(o):
    return json.loads(json.dumps(o, ensure_ascii=False))


def doc_problems(d):
    u"""書類 1 つの中の関係(紙の欄の項の和・導き方・理由の数)。"""
    out = []
    n = d[u"番号"]
    if d[u"断った"] != bool(d[u"断った理由"]) or d[u"断った"] != bool(d[u"断った段"]) or (d[u"断った"] and d[u"断った段"] not in STAGES):
        out.append(u"書類 %d の断りの欄が合わない" % n)
    if d[u"全部同じ"] != (d[u"タクソノミが同じ"] and d[u"fact が同じ"]):
        out.append(u"書類 %d の全部同じが、タクソノミが同じと fact が同じの両方でない" % n)
    if d[u"表 F が同じ"] != (d[u"attrs が違う fact の数"] == 0 and d[u"属性を作れた"]):
        out.append(u"書類 %d の表 F が同じが、attrs の違い 0 と属性を作れたの両方でない" % n)
    if d[u"fact が同じ"] and not d[u"組めた"]:
        out.append(u"書類 %d が組めていないのに fact が同じ" % n)
    if d[u"混ぜ物"][u"効いた"] and not d[u"混ぜ物"][u"作れた"]:
        out.append(u"書類 %d の混ぜ物が作れていないのに効いた" % n)
    if d[u"断った"] and (d[u"全部同じ"] or d[u"fact が同じ"] or d[u"鳴り方が同じ"] or d[u"組めた"] or d[u"2 回組んで同じ"]):
        out.append(u"書類 %d が断ったのに組めた・同じの欄が真" % n)
    if d[u"断った段"] != STAGES[0]:
        items = d[u"紙の欄の数(項ごと)"]
        if list(items) != list(CELL_KEYS) or d[u"紙の欄の数"] != sum(items.values()):
            out.append(u"書類 %d の紙の欄の項の和が紙の欄の数と違う" % n)
        elif items[HAND_ITEM] != 7 * d[u"1 つずつ書く fact の数"]:
            out.append(u"書類 %d の「1 つずつ書く fact × 7」が 7 倍と違う" % n)
        rs = d[u"1 つずつ書く fact の理由(重ねて数える)"]
        if list(rs) != list(HAND_REASONS):
            out.append(u"書類 %d の理由の名が違う" % n)
        else:
            h = d[u"1 つずつ書く fact の数"]
            if not (max(rs.values()) <= h <= sum(rs.values())) or h > d[u"fact の数"]:
                out.append(u"書類 %d の 1 つずつ書く fact の数が理由の数・fact の数と合わない" % n)
        if d[u"属性を作れた"]:
            av = d[u"attrs が違う属性ごとの fact の数(重ねて数える)"]
            if list(av) != list(ATTR_KEYS) or not (max(av.values()) <= d[u"attrs が違う fact の数"] <= sum(av.values())):
                out.append(u"書類 %d の attrs が違う fact の数が属性ごとの数と合わない" % n)
    return out


def group_problems(c, g):
    rec = c.rec
    docs = docs_of(rec, g)
    out = []
    want, have = totals(docs), rec[AGG][g]
    if list(have) != list(want):
        return [u"%s の集計の欄の名・並びが数え直しと違う" % g]
    for k in want:
        if k in SEC_KEYS:
            if abs(have[k] - want[k]) > 0.05 * len(docs) + 0.06:
                out.append(u"%s の %s が書類ごとの秒の和と離れている" % (g, k))
        elif norm(have[k]) != norm(want[k]):
            out.append(u"%s の「%s」が書類ごとの数から数え直した値と違う" % (g, k))
    r = have[u"紙の欄の比"]
    if u"%.1f" % r[u"%"] != pct(r[u"数"], r[u"分母"]) or (r[u"数"], r[u"分母"]) != (have[u"紙の欄の数"], have[u"fact の数 × 7"]):
        out.append(u"%s の紙の欄の比が数え直した値と違う" % g)
    # 理由 (c)(d) が 0 なら、1 つずつ書く fact は (a) + (b) のちょうど(足されたものが無い)
    rs = have[u"1 つずつ書く fact の理由ごとの数(重ねて数える)"]
    if rs[HAND_REASONS[2]] == 0 and rs[HAND_REASONS[3]] == 0 and have[u"1 つずつ書く fact の数"] != rs[HAND_REASONS[0]] + rs[HAND_REASONS[1]]:
        out.append(u"%s の理由 (c)(d) が 0 なのに 1 つずつ書く fact が (a) + (b) と違う" % g)
    return out


def pred_expected(rec):
    s = rec[AGG][G_PROD]
    fact_s, fact_a = s[u"fact の数(紙を作れた書類)"], s[u"fact の数(属性を作れた書類)"]
    return collections.OrderedDict([
        (PK[0], collections.OrderedDict([(u"書類", s[u"表 F が同じ書類の数"]), (u"分母", s[u"書類の数"])])),
        (PK[1], rate_row(s[u"attrs が違う fact の数"], fact_a)),
        (PK[2], rate_row(s[u"1 つずつ書く fact の数"], fact_s)),
        (PK[3], collections.OrderedDict([(u"書類", s[u"fact が同じ書類の数"]), (u"分母", s[u"書類の数"])])),
        (PK[4], collections.OrderedDict([(u"書類", s[u"断った段ごとの数"][STAGES[1]]), (u"分母", s[u"書類の数"])])),
        (PK[5], rate_row(s[u"紙の欄の数"], s[u"fact の数 × 7"])),
        (PK[6], collections.OrderedDict([(u"書類", s[u"混ぜ物が効いた書類の数"]), (u"分母", s[u"混ぜ物を作れた書類の数"])])),
        (PK[7], rate_row(s[u"そのほかの属性を持つ fact の数"], fact_s))])


def judge(rec):
    u"""封 §4 の境(丸める前の整数)から XS0-1〜XS0-8 を決め直す。値は (当たりか, 外れた向き)。"""
    s = rec[AGG][G_PROD]
    fs, fa = s[u"fact の数(紙を作れた書類)"], s[u"fact の数(属性を作れた書類)"]
    hand, other, cells, base = s[u"1 つずつ書く fact の数"], s[u"そのほかの属性を持つ fact の数"], s[u"紙の欄の数"], s[u"fact の数 × 7"]
    out = collections.OrderedDict()

    def put(k, lo_ok, hi_ok):
        out[k] = (lo_ok and hi_ok, u"" if lo_ok and hi_ok else (u"下" if not lo_ok else u"上"))
    put(u"XS0-1", s[u"表 F が同じ書類の数"] >= 60, True)
    put(u"XS0-2", True, 1000 * s[u"attrs が違う fact の数"] <= 2 * fa)
    put(u"XS0-3", 1000 * hand >= 48 * fs, 1000 * hand < 65 * fs)
    put(u"XS0-4", s[u"fact が同じ書類の数"] >= 60, True)
    put(u"XS0-5", True, s[u"断った段ごとの数"][STAGES[1]] <= 2)
    put(u"XS0-6", 1000 * cells >= 336 * base, 100 * cells < 38 * base)
    put(u"XS0-7", s[u"混ぜ物を作れた書類の数"] > 0 and s[u"混ぜ物が効いた書類の数"] == s[u"混ぜ物を作れた書類の数"], True)
    put(u"XS0-8", 100 * other >= 2 * fs, 100 * other < 10 * fs)
    return out


def suspects(c):
    u"""封 §4 の「先に自分の欠陥を疑う場合」の、本番の数での値(順に: 1 つずつ書く fact・道具が違う書類・表 F が違うのに 1 つずつ書く fact が 0 の書類・混ぜ物を作れなかった書類・断った書類)。"""
    docs = docs_of(c.rec, G_PROD)
    xa1 = c.xa1[G_PROD]
    xa1_hand = xa1[u"fact の数"] - xa1[u"段 2"][u"全部決まる fact の数"]
    s = c.rec[AGG][G_PROD]
    return (s[u"1 つずつ書く fact の数"], xa1_hand,
            sum(1 for d in docs if d[u"表 F が同じ"] and not d[u"fact が同じ"]),
            sum(1 for d in docs if not d[u"表 F が同じ"] and d[u"1 つずつ書く fact の数"] == 0),
            sum(1 for d in docs if not d[u"混ぜ物"][u"作れた"]),
            sum(1 for d in docs if d[u"断った"]))


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
    if c.rec[u"材料"][u"道具の版"] != MS.TOOL_VERSION:
        out.append(u"記録の道具の版が script と違う")
    return out


def recount_problems(c):
    rec = c.rec
    out = []
    docs = rec[u"書類"]
    if [d[u"番号"] for d in docs] != list(range(1, DOC_COUNT + 1)) or rec[u"材料"][u"書類の本数"] != DOC_COUNT or rec[u"材料"][u"開発の 5 本の番号"] != list(range(1, DEV_COUNT + 1)):
        out.append(u"書類の番号・材料の書類の本数・開発の 5 本の番号が違う")
        return out
    if list(rec[AGG]) != list(GROUPS):
        return out + [u"集計の塊が 3 つでない"]
    for d in docs:
        out.extend(doc_problems(d))
    for g in GROUPS:
        out.extend(group_problems(c, g))
    if norm(rec[PRED_KEY]) != norm(pred_expected(rec)):
        out.append(u"予測の判定に要る数が群の数から作り直した値と違う")
    return out


def record_clean_problems(c):
    text = json.dumps(c.rec, ensure_ascii=False)
    out = []
    try:
        MS.check_clean(c.rec, text)
    except SystemExit:
        out.append(u"記録の検査(欄・形・file の名・日付)が止める")
    except Exception as exc:                    # noqa: BLE001  script の Stop など
        out.append(u"記録の検査が止める: %s" % type(exc).__name__)
    if WG.DOCID_FORM.search(re.sub(r"[0-9a-fA-F]{32,}", u"", text)) or WG.ECODE_FORM.search(text):
        out.append(u"記録に docid か EDINET コードの形が在る")
    return out


def bound_problems(c):
    out = [u"封に境の字が無い: %s" % p for p in BOUND_SEAL_PHRASES if p not in c.seal]
    sec4 = section(c.seal, u"## §4 ", u"## §5 ")
    rows = [ln for ln in sec4.splitlines() if re.match(r"^\| XS0-\d", ln)]
    if len(rows) != 8:
        out.append(u"封 §4 の表の行が 8 つでない")
    return out


# ======================================================================================================
def cell_text(rec, key):
    s = rec[AGG][G_PROD]
    fs, fa = s[u"fact の数(紙を作れた書類)"], s[u"fact の数(属性を作れた書類)"]
    n = s[u"書類の数"]

    def f(a, b):
        return u"%d/%d(%s%%)" % (a, b, pct(a, b))
    return {u"XS0-1": u"%d/%d" % (s[u"表 F が同じ書類の数"], n), u"XS0-2": f(s[u"attrs が違う fact の数"], fa), u"XS0-3": f(s[u"1 つずつ書く fact の数"], fs),
            u"XS0-4": u"%d/%d" % (s[u"fact が同じ書類の数"], n), u"XS0-5": u"%d/%d" % (s[u"断った段ごとの数"][STAGES[1]], n), u"XS0-6": f(s[u"紙の欄の数"], s[u"fact の数 × 7"]),
            u"XS0-7": u"%d/%d" % (s[u"混ぜ物が効いた書類の数"], s[u"混ぜ物を作れた書類の数"]), u"XS0-8": f(s[u"そのほかの属性を持つ fact の数"], fs)}[key]


def expected_cells(c):
    out = collections.OrderedDict()
    for k, (ok, way) in judge(c.rec).items():
        out[k] = (cell_text(c.rec, k), u"当たり" if ok else u"外れ(%s)" % way)
    return out


def verdict_problems(c):
    rec = c.rec
    j = judge(rec)
    want = expected_cells(c)
    out = []
    rows = {}
    for ln in c.doc.splitlines():
        m = re.match(r"^\| (XS0-\d)(?:\(主\))? \|(.*)\|$", ln)
        if m:
            rows[m.group(1)] = [x.strip() for x in m.group(2).split(u"|")]
    if sorted(rows) != sorted(j):
        return [u"文書 §1 の表の行が XS0-1〜XS0-8 でない"]
    sec4 = section(c.seal, u"## §4 ", u"## §5 ")
    seal_rows = dict((ln.split(u"|")[1].strip().replace(u"(主)", u""), ln) for ln in sec4.splitlines() if re.match(r"^\| XS0-\d", ln))
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
    if u"判定した %d 本は当たり %d・外れ %d。" % (len(j), hits, len(j) - hits) not in head:
        out.append(u"文書の頭の件数が決め直した件数と違う")
    missed = [k for k, v in j.items() if not v[0]]
    for k in missed:
        if u"外れは %s" % k not in head:
            out.append(u"文書の頭が外れた予測 %s を名指ししていない" % k)
    for k, v in j.items():
        if v[0] and u"外れは %s" % k in head:
            out.append(u"当たりの予測 %s を頭が外れと書いている" % k)
    if u"XS0-6" in missed:
        s = rec[AGG][G_PROD]
        if u"外れは XS0-6(紙の欄の比)。%s%% で、封の範囲(33.6%% 以上 38%% 未満)を%sに外れた。" % (pct(s[u"紙の欄の数"], s[u"fact の数 × 7"]), j[u"XS0-6"][1]) not in head:
            out.append(u"頭の XS0-6 の外れの言い切りが記録と違う")
    sec1, sec5 = section(c.doc, u"## §1 ", u"## §2 "), section(c.doc, u"## §5 ", None)
    sus = suspects(c)
    if sus[0] < sus[1] or sus[2] > 0 or sus[3] > 0 or sus[4] >= 6 or sus[5] >= 6:
        out.append(u"封 §4 の「先に自分の欠陥を疑う場合」が発火している")
    line = u"1 つずつ書く fact は %d(%d より少なくない)・表 F が同じなのに道具が読む fact が違う書類は %d・表 F が違う書類は %d・混ぜ物を作れなかった書類は %d・断った書類は %d。" % (
        sus[0], sus[1], sus[2], len([1 for d in docs_of(rec, G_PROD) if not d[u"表 F が同じ"]]), sus[4], sus[5])
    if u"封 §4 の「先に自分の欠陥を疑う場合」には当たらない: " + line not in sec1:
        out.append(u"文書 §1 の自己点検の言い切りが記録から組んだ字と違う")
    # 封 §6: XS0-1 と XS0-4 が当たりなら次の便の候補を示す
    cond = j[u"XS0-1"][0] and j[u"XS0-4"][0]
    shown = u"人間に示す次の便の候補(封 §6。XS0-1 と XS0-4 が当たりなので示す)" in sec5.replace(u"**", u"")
    if cond != shown:
        out.append(u"封 §6 の決め(XS0-1 と XS0-4 が当たりなら次の便の候補を示す)と文書 §5 が合わない")
    if cond:
        s6 = section(c.seal, u"## §6 ", u"## §7 ")
        seg = s6[s6.index(u"(i) 文脈と単位の定義"):s6.index(u"同じことをする。") + len(u"同じことをする。")].strip()
        if seg not in sec5:
            out.append(u"§5 の次の便の候補が封 §6 の字と違う")
        if u"別の封が先" not in sec5:
            out.append(u"§5 に「別の封が先」が無い")
    return out


# ======================================================================================================
def rates_by_doc(rec):
    docs = [d for d in docs_of(rec, G_PROD) if d[u"断った段"] != STAGES[0] and d[u"fact の数"] > 0]
    return sorted(Fraction(d[u"1 つずつ書く fact の数"], d[u"fact の数"]) for d in docs)


def frac_pct(fr):
    u"""Fraction を % の小数第 1 位(0.5 は上げる)の字に。"""
    x = fr * 1000
    return u"%.1f" % (int(x + Fraction(1, 2)) / 10.0)


def rate_range(rec):
    r = rates_by_doc(rec)
    n = len(r)
    med = r[n // 2] if n % 2 else (r[n // 2 - 1] + r[n // 2]) / 2
    return frac_pct(r[0]), frac_pct(med), frac_pct(r[-1])


ITEM_LABEL = dict((k, k.replace(u"name ごと", u"`name` ごと")) for k in CELL_KEYS)


def expected_lines(c):
    rec = c.rec
    p, d, a = rec[AGG][G_PROD], rec[AGG][G_DEV], rec[AGG][G_ALL]
    out = []
    out.append(u"| 断った書類(紙を作る・属性を作る・組む) | %s | %s |" % tuple(u"・".join(str(t[u"断った段ごとの数"][st]) for st in STAGES) for t in (p, d)))
    simple = ((u"fact", u"fact の数(紙を作れた書類)"), (u"1 つずつ書く fact", u"1 つずつ書く fact の数"), (u"そのほかの属性を持つ fact", u"そのほかの属性を持つ fact の数"),
              (u"表 F が同じ書類", u"表 F が同じ書類の数"), (u"`attrs` が違う fact", u"attrs が違う fact の数"), (u"組めた書類", u"組めた書類の数"), (u"道具が読む fact が同じ書類", u"fact が同じ書類の数"),
              (u"鳴り方が同じ書類", u"鳴り方が同じ書類の数"), (u"タクソノミが同じ書類", u"タクソノミが同じ書類の数"), (u"全部同じ書類", u"全部同じ書類の数"), (u"2 回組んで同じ書類", u"2 回組んで同じ書類の数"),
              (u"紙の欄の数", u"紙の欄の数"), (u"fact の数 × 7", u"fact の数 × 7"))
    for label, key in simple:
        out.append(u"| %s | %d | %d |" % (label, p[key], d[key]))
    for label, i in ((u"うち表の外", 0), (u"うち便 XA1 の段 2 で全部決まらない", 1), (u"うち文脈の定義が 2 つ以上", 2), (u"うち期間の種類が `name` の決めと違う", 3)):
        k = HAND_REASONS[i]
        out.append(u"| %s | %d | %d |" % (label, p[u"1 つずつ書く fact の理由ごとの数(重ねて数える)"][k], d[u"1 つずつ書く fact の理由ごとの数(重ねて数える)"][k]))
    out.append(u"| 混ぜ物を作れた書類・効いた書類 | %d・%d | %d・%d |" % (p[u"混ぜ物を作れた書類の数"], p[u"混ぜ物が効いた書類の数"], d[u"混ぜ物を作れた書類の数"], d[u"混ぜ物が効いた書類の数"]))
    out.append(u"| 紙の欄の比 | %s%% | %s%% |" % (pct(p[u"紙の欄の数"], p[u"fact の数 × 7"]), pct(d[u"紙の欄の数"], d[u"fact の数 × 7"])))
    for k in CELL_KEYS:
        out.append(u"| %s | %d |" % (ITEM_LABEL[k], p[u"紙の欄の数(項ごと)"][k]))
    lo, mid, hi = rate_range(rec)
    out.append(u"- 書類ごとの 1 つずつ書く fact の率(%d 本): 最小 %s%%・中央 %s%%・最大 %s%%。" % (len(rates_by_doc(rec)), lo, mid, hi))
    out.append(u"- 67 本の全部では: fact %d・1 つずつ書く fact %d・表 F が同じ %d 本・`attrs` が違う fact %d・道具が読む fact が同じ %d 本・タクソノミが同じ %d 本・紙の欄の比 %s%%(%d/%d)。" % (
        a[u"fact の数(紙を作れた書類)"], a[u"1 つずつ書く fact の数"], a[u"表 F が同じ書類の数"], a[u"attrs が違う fact の数"], a[u"fact が同じ書類の数"], a[u"タクソノミが同じ書類の数"],
        pct(a[u"紙の欄の数"], a[u"fact の数 × 7"]), a[u"紙の欄の数"], a[u"fact の数 × 7"]))
    return out


def expected_fragments(c):
    rec = c.rec
    p, d = rec[AGG][G_PROD], rec[AGG][G_DEV]
    f = []
    rp = pct(p[u"紙の欄の数"], p[u"fact の数 × 7"])
    f.append(u"XS0-3 の %s%% は下の境 4.8%% のすぐ上。1 つずつ書く fact は %d で、便 XA1 の「全部決まらない fact」の数と同じ(理由 (c)(d) が 0 だったので、足されたものが無い)。" % (
        pct(p[u"1 つずつ書く fact の数"], p[u"fact の数(紙を作れた書類)"]), p[u"1 つずつ書く fact の数"]))
    f.append(u"提出者別タクソノミが元と同じ書類は %d/%d(便 XP0 と同じ数)。全部同じ書類も %d/%d。" % (p[u"タクソノミが同じ書類の数"], p[u"書類の数"], p[u"全部同じ書類の数"], p[u"書類の数"]))
    f.append(u"(5 本では紙の欄の比は %s%% で範囲の中だった)" % pct(d[u"紙の欄の数"], d[u"fact の数 × 7"]))
    f.append(u"属性を 1 つずつ全部書く場合の 4 割弱")
    f.append(u"| 紙の欄の数 | %d | %d |" % (p[u"紙の欄の数"], d[u"紙の欄の数"]))
    f.append(u"紙の欄の数は、属性を 1 つずつ書く場合の %s%%。" % rp)
    if p[u"表 F が同じ書類の数"] == p[u"書類の数"]:
        f.append(u"数の fact の属性は %d 本の全部で元に戻り" % p[u"書類の数"])
    if p[u"fact が同じ書類の数"] == p[u"書類の数"]:
        f.append(u"fact は %d 本の全部で元と同じだった" % p[u"書類の数"])
    f.append(u"表 F が %d 本の全部で同じだったことは" % p[u"表 F が同じ書類の数"])
    return f


def derived_lines(c):
    u"""§3 の、記録から導く言い切り(3 桁以上の数・% を持てるのはこの字だけ)。"""
    d = c.rec[AGG][G_DEV]
    return [u"開発の 5 本の比(%s%%)は範囲の中で、62 本は上へ出た" % pct(d[u"紙の欄の数"], d[u"fact の数 × 7"])]


def sanity_problems(c):
    u"""文書の言い切りが記録の数に合う(便 XA1・便 XA0 の記録との関係を含む)。"""
    rec = c.rec
    s, dv = rec[AGG][G_PROD], rec[AGG][G_DEV]
    out = []
    x1, x0 = c.xa1[G_PROD], c.xa0[G_PROD]
    x1d, x0d = c.xa1[G_DEV], c.xa0[G_DEV]
    hand1 = x1[u"fact の数"] - x1[u"段 2"][u"全部決まる fact の数"]
    hand1d = x1d[u"fact の数"] - x1d[u"段 2"][u"全部決まる fact の数"]
    if (s[u"1 つずつ書く fact の数"], dv[u"1 つずつ書く fact の数"]) != (hand1, hand1d):
        out.append(u"文書の「1 つずつ書く fact は便 XA1 の全部決まらない fact の数と同じ」が便 XA1 の記録と合わない")
    if (s[u"fact の数(紙を作れた書類)"], dv[u"fact の数(紙を作れた書類)"]) != (x1[u"fact の数"], x1d[u"fact の数"]):
        out.append(u"fact の数が便 XA1 の記録と違う")
    gr = s[u"1 つずつ書く fact の理由ごとの数(重ねて数える)"]
    if (gr[HAND_REASONS[0]], dv[u"1 つずつ書く fact の理由ごとの数(重ねて数える)"][HAND_REASONS[0]]) != (x0[u"表の外の fact の数"], x0d[u"表の外の fact の数"]):
        out.append(u"文書の「うち表の外」が便 XA0 の記録の表の外の fact の数と合わない")
    if not s[u"紙の欄の数"] > x1[u"段 2"][u"書く欄の数"]:
        out.append(u"文書の「紙の欄の数は便 XA1 の段 2 の書く欄の数より多い」が記録と合わない")
    if pct(x1[u"段 2"][u"書く欄の数"], x1[u"段 2"][u"fact の数 × 7"]) != u"33.6" or u"33.6% 以上" not in c.seal:
        out.append(u"文書の「封の範囲の下の境は便 XA1 の段 2 の比そのもの」が記録と合わない")
    if not (350 * s[u"fact の数 × 7"] <= 1000 * s[u"紙の欄の数"] < 400 * s[u"fact の数 × 7"]):
        out.append(u"文書の「4 割弱」が記録の紙の欄の比と合わない")
    if not (336 * dv[u"fact の数 × 7"] <= 1000 * dv[u"紙の欄の数"] and 100 * dv[u"紙の欄の数"] < 38 * dv[u"fact の数 × 7"]):
        out.append(u"文書の「開発の 5 本の比は範囲の中」が記録と合わない")
    if not 100 * s[u"紙の欄の数"] >= 38 * s[u"fact の数 × 7"]:
        out.append(u"文書の「62 本は上へ出た」が記録と合わない")
    if s[u"書類の数"] - s[u"タクソノミが同じ書類の数"] != 2 or s[u"全部同じ書類の数"] != s[u"タクソノミが同じ書類の数"]:
        out.append(u"文書の「タクソノミが元と違う 2 本・全部同じは 60/62」が記録と合わない")
    if s[u"表 F が同じ書類の数"] != s[u"書類の数"] or s[u"attrs が違う fact の数"] != 0:
        out.append(u"文書の「表 F が 62 本の全部で同じ」が記録と合わない")
    if rec[AGG][G_ALL][u"書類の数"] != DOC_COUNT:
        out.append(u"全部の塊の書類の数が 67 でない")
    sec4 = section(c.doc, u"## §4 ", u"## §5 ")
    if len([ln for ln in sec4.splitlines() if re.match(r"^\d+\. ", ln)]) != 13:
        out.append(u"§4 の実装で決めた所が 13 でない")
    if u"fact が同じ書類" in sec4 or s[u"断った書類の数"] != 0:
        out.append(u"断った書類が 0 でない")
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
    return out


def derived_numbers(c):
    out = set()
    for g in GROUPS:
        WG.ints_in(c.rec[AGG][g], out)
    WG.ints_in(c.rec[PRED_KEY], out)
    s = c.rec[AGG][G_PROD]
    out.add(pct(s[u"紙の欄の数"], s[u"fact の数 × 7"]))
    out.add(pct(s[u"1 つずつ書く fact の数"], s[u"fact の数(紙を作れた書類)"]))
    for v in rate_range(c.rec):
        out.add(v)
    for g in (G_DEV, G_PROD, G_ALL):
        out.add(pct(c.rec[AGG][g][u"紙の欄の数"], c.rec[AGG][g][u"fact の数 × 7"]))
    x1 = c.xa1[G_PROD]
    out.add(str(x1[u"fact の数"] - x1[u"段 2"][u"全部決まる fact の数"]))
    out |= set(BOUND_NUMBERS)
    return out


def doc_number_problems(c):
    allowed = set(STRUCTURAL) | derived_numbers(c)
    out = []
    for i, ln in enumerate(c.doc.splitlines(), 1):
        for tok in WG.doc_number_tokens(re.sub(r"^\d+\. ", u"", ln)):
            if tok.replace(u",", u"") not in allowed:
                out.append(u"文書の %d 行目の数 %s が記録から組んだ数の外: %s" % (i, tok, ln[:30]))
    return out


def sec3_problems(c):
    u"""§3 は記録に欄の無い読みの節。3 桁以上の数・% は derived_lines の字だけ。"""
    s = section(c.doc, u"## §3 ", u"## §4 ")
    out = []
    if u"記録に欄の無い読み" not in s.splitlines()[0]:
        out.append(u"§3 の見出しが「記録に欄の無い読み」でない")
    keep = s
    for frag in derived_lines(c):
        if frag not in keep:
            out.append(u"§3 に記録から導いた字が無い: %s" % frag[:40])
        keep = keep.replace(frag, u" ")
    left = re.sub(r"`[^`]*`|\b(?=[0-9]*[a-f])[0-9a-f]{8}\b", u" ", keep)
    if re.search(r"\d{3}|%|％", left):
        out.append(u"§3 の導いた字の外に 3 桁以上の数か % が在る")
    for p in (u"紙に書く量は、便 XA1 の数より大きい側に在る", u"記録の監査の席は", u"別の混ぜ方", u"再現ではない", u"この便で新しく出た違いではない"):
        if p not in s:
            out.append(u"§3 に字が無い: %s" % p)
    return out


def affirm_problems(c):
    u"""「作れる」「専用の道具が要らない」「人が書ける」は、言えないことの引用(「…」の中)にしか無い。引用の在る行には「言えない」か「読まない」か「示していない」が在る。"""
    out = []
    for i, ln in enumerate(c.doc.splitlines(), 1):
        if QUOTED_CLAIM.search(ln) and not any(w in ln for w in (u"言えない", u"読まない", u"示していない")):
            out.append(u"文書の %d 行目が引用の主張を否定の外で書いている" % i)
        rest = QUOTED_CLAIM.sub(u"", ln)
        for w in AFFIRM_WORDS:
            if re.search(w, rest):
                out.append(u"文書の %d 行目に引用の外の字: %s" % (i, w))
    return out


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
    (u"sha", sha_problems), (u"recount", recount_problems), (u"clean", record_clean_problems), (u"bound", bound_problems),
    (u"verdict", verdict_problems), (u"numbers", doc_number_problems), (u"frag", fragment_problems), (u"sanity", sanity_problems), (u"sec3", sec3_problems),
    (u"affirm", affirm_problems), (u"phrases", phrase_problems), (u"head", head_problems), (u"forbidden", forbidden_problems), (u"commits", doc_commit_problems)])


# ======================================================================================================
def blob_problems(root, prefix, at):
    return WG.blob_problems(root, prefix, at)


def commit_problems(root=REPO):
    u"""文書が書く 3 つの commit が実の履歴と合う: 封は 483e3e93 が足し(1 commit)・script と封の門は 6d82a612 が足し・記録は 7706dc70 が足した(どれも 1 commit)。"""
    out = []
    for rel, want in ((SEAL_REL, [SEAL_COMMIT_SHORT]), (SCRIPT_REL, [SCRIPT_COMMIT_SHORT]), (SEAL_GATE_REL, [SCRIPT_COMMIT_SHORT]), (RECORD_REL, [RECORD_COMMIT_SHORT])):
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
(変異を実行する前に書いた予測。右 = 赤になるべき検査。「整合」= 書類ごとの数から群の数・予測の欄を作り直し、recount は緑のまま当たり外れ・言い切りだけが変わる)
M1  記録の sha256 の写しを違う値に                                                       -> sha
M2  記録の「この script の sha256」を 1 字替える                                         -> sha
M3  記録の限界の欄の 1 行を消す                                                          -> sha
M4  記録の封の commit の欄を 1 字替える                                                  -> sha
M5  書類 10 の 1 つずつ書く fact を 1 増やす(群は直さない)                                -> recount
M6  本番の表 F が同じ書類の数を 1 減らす(書類ごとは直さない)                              -> recount
M7  予測の欄 XS0-3 の分母を 1 増やす                                                     -> recount
M8  材料の書類の本数 67 → 68                                                             -> recount
M9  書類 10 の紙の欄の数を 1 増やす(項は直さない)                                         -> recount
M10 本番の紙の欄の項「要素の線 × 4」を 1 増やす(和は直さない)                             -> recount
M11 書類 10 の混ぜ物の「効いた」を偽に(群は直さない)                                      -> recount
M12 全部の塊の fact を 1 減らす                                                          -> recount
M13 本番の紙の欄の比の % を 38.2 → 38.3                                                  -> recount
M14 開発の理由 (a) を 1 増やす(書類ごとは直さない)                                         -> recount
M15 タクソノミが違う書類の「全部同じ」を真に(導き方に反する)                                -> recount
M16 記録に docid の欄を足す                                                              -> clean
M17 封の写しから XS0-1 の境の字を消す                                                    -> bound
M18 封の写しから自己点検の「断った書類が 6 本以上」を消す                                  -> bound
M19 文書の XS0-1 の判定「当たり」を「外れ(下)」に                                         -> verdict
M20 文書の XS0-6 の判定「外れ(上)」を「当たり」に                                         -> verdict
M21 文書の XS0-6 の判定「外れ(上)」を「外れ(下)」に                                       -> verdict
M22 文書の件数の行 当たり 7・外れ 1 → 当たり 8・外れ 0                                    -> verdict
M23 文書の XS0-3 のセル 3071/63236 → 3072/63236                                         -> verdict・numbers
M24 §5 の「人間に示す次の便の候補」の見出しの字を消す                                      -> verdict・phrases
M25 文書の XS0-6 の予測の字「33.6% 以上 38% 未満」を「33.6% 以上 39% 未満」に               -> verdict
M26 頭の「判定した 8 本は当たり 7・外れ 1」を 当たり 6・外れ 2 に                          -> verdict
M27 整合: 紙の欄を減らして XS0-6 が範囲の中(当たりに変わる)                                -> verdict
M28 整合: 表 F が同じ書類を 5 本減らして XS0-1 が 57(下に外れ)                              -> verdict
M29 整合: attrs が違う fact を増やして XS0-2 が 0.2% 超                                   -> verdict
M30 整合: 1 つずつ書く fact を半分にして XS0-3 が下に外れ                                  -> verdict
M31 整合: 1 つずつ書く fact を増やして XS0-3 が上に外れ                                    -> verdict
M32 整合: 道具が読む fact が同じ書類を 5 本減らして XS0-4 が外れ                            -> verdict
M33 整合: 属性を作る命令が断った書類を 3 本にして XS0-5 が外れ                              -> verdict
M34 整合: 混ぜ物が効かなかった書類を 1 本にして XS0-7 が外れ                                -> verdict
M35 整合: そのほかの属性を持つ fact を 0 にして XS0-8 が下に外れ                            -> verdict
M36 整合: 表 F が同じなのに道具が違う書類を 1 本作る(自己点検が発火)                         -> verdict
M37 文書 §2 の本番の fact 63236 を 63237 に(表の行)                                        -> frag・numbers
M38 文書 §2 の紙の欄の数 168966 を 168967 に                                               -> frag・numbers・sanity
M39 文書の項の表の「要素の線 × 4 | 93644」を 93645 に                                       -> frag・numbers
M40 文書の書類ごとの率「最小 1.3%」を 1.4% に                                              -> frag・numbers
M41 文書の「タクソノミが同じ 65 本」を 66 本に                                             -> frag・numbers
M42 文書に 9999 の言い切りを足す                                                          -> numbers
M43 頭の「XS0-3 の 4.9%」を 5.0% に                                                       -> frag・numbers
M44 §3 に 3 桁の数を足した行                                                              -> sec3
M45 §3 の「開発の 5 本の比(37.4%)」を 37.5% に                                            -> sec3・numbers
M46 §3 の「紙に書く量は、便 XA1 の数より大きい側に在る」を消す                                -> sec3
M47 文書に「XBRL を作れる。」を引用の外で足す                                              -> affirm
M48 文書に「専用の道具が要らない。」を足す                                                 -> affirm
M49 文書に「紙は人が書ける。」を足す                                                       -> affirm
M50 文書に「人が紙を書ける。」を足す                                                       -> affirm
M51 引用の行から「言えない」「読まない」を全部消す                                          -> affirm
M52 §5 の「言えないこと」を消す                                                           -> phrases
M53 頭の「この便からは言えない」を消す                                                     -> head
M54 頭の「先に負けと限界を書く」を消す                                                     -> head
M55 頭の「未使用ではない」を消す                                                           -> head
M56 頭の「LLM の席は呼んでいない」を消す                                                   -> head
M57 頭の「紙は答え(元の書類)から作っている」を消す                                         -> head
M58 文書に「保証」を足す                                                                  -> forbidden
M59 文書に docID の形を足す                                                               -> forbidden
M60 文書の commit の字 7706dc70 を 1 字替える                                              -> commits
M61 文書に知らない commit の字を足す                                                       -> commits
M62 便 XA1 の記録の写しで本番の段 2 の全部決まる fact を 1 減らす                            -> sanity
M63 便 XA0 の記録の写しで本番の表の外の fact の数を 1 増やす                                 -> sanity
M64 文書 §4 の実装で決めた所を 1 つ消す                                                    -> sanity
M65 §5 の次の便の候補の「(iii) 未使用の書類で同じことをする」を替える                        -> verdict
M66 整合: 開発の 5 本の紙の欄を増やして比が 38% 以上(「開発は範囲の中」が崩れる)              -> sanity
M67 頭の「便 XA1 の「全部決まらない fact」の数と同じ」を消す                                  -> frag
M68 文書の自己点検の言い切り「混ぜ物を作れなかった書類は 0」を 1 に                          -> verdict・numbers

(1 回目の実行で外れた予測。門は直していない(予測の側を直した)。記録: M68 は予測 verdict・numbers だったが numbers が黙った)
- M68(「混ぜ物を作れなかった書類は 0」を 1 に): numbers が黙った。文書の数の門は 0〜10 の字を構造の数として通すので、1 は記録に無くても通る。書き換えは verdict が記録から組んだ字と照らして赤にする。
- M28・M29 の作りの誤り: 初めは表 F が違う書類の「全部同じ」も偽にしていた(全部同じはタクソノミと fact だけで決まる)ので recount が赤くなり、整合の変更になっていなかった。作りを直した。
"""


def doc_at(rec, k):
    return rec[u"書類"][DEV_COUNT + k]


def rebuild(rec):
    u"""書類ごとの数はそのままに、3 つの塊の集計と予測の欄を作り直す(整合した変更)。"""
    for g in GROUPS:
        rec[AGG][g] = totals(docs_of(rec, g))
    rec[PRED_KEY] = pred_expected(rec)


def set_hand(d, h):
    rs = d[u"1 つずつ書く fact の理由(重ねて数える)"]
    a = min(rs[HAND_REASONS[0]], h)
    rs[HAND_REASONS[0]], rs[HAND_REASONS[1]] = a, h - a
    d[u"1 つずつ書く fact の数"] = h
    it = d[u"紙の欄の数(項ごと)"]
    it[HAND_ITEM] = 7 * h
    d[u"紙の欄の数"] = sum(it.values())


def m_cells_in_range(c):
    for d in c.rec[u"書類"]:
        it = d[u"紙の欄の数(項ごと)"]
        it[CELL_KEYS[3]] = int(it[CELL_KEYS[3]] * 0.9)
        d[u"紙の欄の数"] = sum(it.values())
    rebuild(c.rec)


def m_tablef_low(c):
    for k in range(5):
        d = doc_at(c.rec, k)
        d[u"表 F が同じ"] = False
        d[u"attrs が違う fact の数"] = 1
        d[u"attrs が違う属性ごとの fact の数(重ねて数える)"][u"属性 name"] = 1
    rebuild(c.rec)


def m_attrs_diff(c):
    d = doc_at(c.rec, 0)
    d[u"表 F が同じ"] = False
    d[u"attrs が違う fact の数"] = 200
    d[u"attrs が違う属性ごとの fact の数(重ねて数える)"][u"属性 name"] = 200
    rebuild(c.rec)


def m_hand_low(c):
    for d in docs_of(c.rec, G_PROD):
        set_hand(d, d[u"1 つずつ書く fact の数"] // 2)
    rebuild(c.rec)


def m_hand_high(c):
    for d in docs_of(c.rec, G_PROD):
        set_hand(d, min(d[u"fact の数"], d[u"1 つずつ書く fact の数"] * 3 // 2))
    rebuild(c.rec)


def m_tool_low(c):
    for k in range(5):
        d = doc_at(c.rec, k)
        d[u"fact が同じ"] = False
        d[u"全部同じ"] = False
    rebuild(c.rec)


def decline_attrs(d):
    d[u"断った"] = True
    d[u"断った段"] = STAGES[1]
    d[u"断った理由"] = u"x"
    for k in (u"属性を作れた", u"表 F が同じ", u"組めた", u"2 回組んで同じ", u"タクソノミが同じ", u"fact が同じ", u"鳴り方が同じ", u"全部同じ"):
        d[k] = False


def m_decline3(c):
    for k in range(3):
        decline_attrs(doc_at(c.rec, k))
    rebuild(c.rec)


def m_mix_low(c):
    doc_at(c.rec, 0)[u"混ぜ物"][u"効いた"] = False
    rebuild(c.rec)


def m_other_zero(c):
    for d in docs_of(c.rec, G_PROD):
        d[u"そのほかの属性を持つ fact の数"] = 0
        it = d[u"紙の欄の数(項ごと)"]
        it[CELL_KEYS[7]] = 0
        d[u"紙の欄の数"] = sum(it.values())
    rebuild(c.rec)


def m_tool_diff_one(c):
    d = doc_at(c.rec, 0)
    d[u"fact が同じ"] = False
    d[u"全部同じ"] = False
    rebuild(c.rec)


def m_dev_cells_high(c):
    for d in docs_of(c.rec, G_DEV):
        it = d[u"紙の欄の数(項ごと)"]
        it[CELL_KEYS[3]] = int(it[CELL_KEYS[3]] * 1.2)
        d[u"紙の欄の数"] = sum(it.values())
    rebuild(c.rec)


def m_taxo_all_same(c):
    for d in c.rec[u"書類"]:
        if not d[u"タクソノミが同じ"]:
            d[u"全部同じ"] = True
            break


def m_drop_quote_negation(c):
    lines = []
    for ln in c.doc.splitlines():
        if QUOTED_CLAIM.search(ln):
            for w in (u"言えないこと", u"言えない", u"読まない", u"示していない"):
                ln = ln.replace(w, u"X")
        lines.append(ln)
    c.doc = u"\n".join(lines)


def m_drop_item(c):
    lines = c.doc.splitlines()
    i = [k for k, ln in enumerate(lines) if ln.startswith(u"13. ")][0]
    del lines[i]
    c.doc = u"\n".join(lines)


def add_sec3(c, text):
    rep(c, u"## §4 ", text + u"\n\n## §4 ")


def m_xa1_full(c):
    c.xa1[G_PROD][u"段 2"][u"全部決まる fact の数"] -= 1


def m_xa0_outside(c):
    c.xa0[G_PROD][u"表の外の fact の数"] += 1


MUTATIONS = (
    (u"M1 記録の sha256 の写しを違う値に", lambda c: c.shas.__setitem__(RECORD_REL, u"0" * 64), (u"sha",)),
    (u"M2 記録の script の sha256 を 1 字替える", lambda c: c.rec.__setitem__(u"この script の sha256", u"f" + c.rec[u"この script の sha256"][1:]), (u"sha",)),
    (u"M3 記録の限界の欄の 1 行を消す", lambda c: c.rec.__setitem__(u"限界", c.rec[u"限界"][1:]), (u"sha",)),
    (u"M4 記録の封の commit の欄を 1 字替える", lambda c: c.rec.__setitem__(u"封の commit", u"0" + c.rec[u"封の commit"][1:]), (u"sha",)),
    (u"M5 書類 10 の 1 つずつ書く fact を 1 増やす", lambda c: doc_at(c.rec, 4).__setitem__(u"1 つずつ書く fact の数", doc_at(c.rec, 4)[u"1 つずつ書く fact の数"] + 1), (u"recount",)),
    (u"M6 本番の表 F が同じ書類の数を 1 減らす", lambda c: c.rec[AGG][G_PROD].__setitem__(u"表 F が同じ書類の数", c.rec[AGG][G_PROD][u"表 F が同じ書類の数"] - 1), (u"recount",)),
    (u"M7 予測の欄 XS0-3 の分母を 1 増やす", lambda c: c.rec[PRED_KEY][PK[2]].__setitem__(u"分母", c.rec[PRED_KEY][PK[2]][u"分母"] + 1), (u"recount",)),
    (u"M8 材料の書類の本数を 68 に", lambda c: c.rec[u"材料"].__setitem__(u"書類の本数", 68), (u"recount",)),
    (u"M9 書類 10 の紙の欄の数を 1 増やす", lambda c: doc_at(c.rec, 4).__setitem__(u"紙の欄の数", doc_at(c.rec, 4)[u"紙の欄の数"] + 1), (u"recount",)),
    (u"M10 本番の紙の欄の項「要素の線 × 4」を 1 増やす", lambda c: c.rec[AGG][G_PROD][u"紙の欄の数(項ごと)"].__setitem__(CELL_KEYS[3], c.rec[AGG][G_PROD][u"紙の欄の数(項ごと)"][CELL_KEYS[3]] + 1), (u"recount",)),
    (u"M11 書類 10 の混ぜ物の「効いた」を偽に", lambda c: doc_at(c.rec, 4)[u"混ぜ物"].__setitem__(u"効いた", False), (u"recount",)),
    (u"M12 全部の塊の fact を 1 減らす", lambda c: c.rec[AGG][G_ALL].__setitem__(u"fact の数(紙を作れた書類)", c.rec[AGG][G_ALL][u"fact の数(紙を作れた書類)"] - 1), (u"recount",)),
    (u"M13 本番の紙の欄の比の % を 38.3 に", lambda c: c.rec[AGG][G_PROD][u"紙の欄の比"].__setitem__(u"%", 38.3), (u"recount",)),
    (u"M14 開発の理由 (a) を 1 増やす", lambda c: c.rec[AGG][G_DEV][u"1 つずつ書く fact の理由ごとの数(重ねて数える)"].__setitem__(HAND_REASONS[0], c.rec[AGG][G_DEV][u"1 つずつ書く fact の理由ごとの数(重ねて数える)"][HAND_REASONS[0]] + 1), (u"recount",)),
    (u"M15 タクソノミが違う書類の「全部同じ」を真に", m_taxo_all_same, (u"recount",)),
    (u"M16 記録に docid の欄を足す", lambda c: c.rec[u"書類"][0].__setitem__(u"docid", u"x"), (u"clean",)),
    (u"M17 封の写しから XS0-1 の境の字を消す", lambda c: rep(c, u"表 F が同じ書類は 60 本以上", u"X", attr="seal"), (u"bound",)),
    (u"M18 封の写しから「断った書類が 6 本以上」を消す", lambda c: rep(c, u"断った書類が 6 本以上", u"X", attr="seal"), (u"bound",)),
    (u"M19 XS0-1 の判定を外れ(下)に", lambda c: rep(c, u"| 62/62 | 当たり |", u"| 62/62 | 外れ(下) |"), (u"verdict",)),
    (u"M20 XS0-6 の判定を当たりに", lambda c: rep(c, u"| 外れ(上) |", u"| 当たり |"), (u"verdict",)),
    (u"M21 XS0-6 の判定を外れ(下)に", lambda c: rep(c, u"| 外れ(上) |", u"| 外れ(下) |"), (u"verdict",)),
    (u"M22 件数の行を当たり 8・外れ 0 に", lambda c: rep(c, u"- 当たり 7・外れ 1。", u"- 当たり 8・外れ 0。"), (u"verdict",)),
    (u"M23 XS0-3 のセルの 3071 を 3072 に", lambda c: rep(c, u"| 3071/63236(4.9%) |", u"| 3072/63236(4.9%) |"), (u"verdict", u"numbers")),
    (u"M24 §5 の次の便の候補の見出しの字を消す", lambda c: rep(c, u"人間に示す次の便の候補(封 §6。XS0-1 と XS0-4 が当たりなので示す)", u"X"), (u"verdict", u"phrases")),
    (u"M25 XS0-6 の予測の字を 39% 未満に", lambda c: rep(c, u"33.6% 以上 38% 未満 |", u"33.6% 以上 39% 未満 |"), (u"verdict",)),
    (u"M26 頭の件数を当たり 6・外れ 2 に", lambda c: rep(c, u"判定した 8 本は当たり 7・外れ 1。", u"判定した 8 本は当たり 6・外れ 2。"), (u"verdict",)),
    (u"M27 整合: 紙の欄を減らして XS0-6 が範囲の中", m_cells_in_range, (u"verdict",)),
    (u"M28 整合: 表 F が同じ書類を 5 本減らす", m_tablef_low, (u"verdict",)),
    (u"M29 整合: attrs が違う fact を増やして XS0-2 が外れ", m_attrs_diff, (u"verdict",)),
    (u"M30 整合: 1 つずつ書く fact を半分に(XS0-3 が下に外れ)", m_hand_low, (u"verdict",)),
    (u"M31 整合: 1 つずつ書く fact を増やして XS0-3 が上に外れ", m_hand_high, (u"verdict",)),
    (u"M32 整合: 道具が読む fact が同じ書類を 5 本減らす", m_tool_low, (u"verdict",)),
    (u"M33 整合: 属性を作る命令が断った書類を 3 本に", m_decline3, (u"verdict",)),
    (u"M34 整合: 混ぜ物が効かなかった書類を 1 本に", m_mix_low, (u"verdict",)),
    (u"M35 整合: そのほかの属性を持つ fact を 0 に", m_other_zero, (u"verdict",)),
    (u"M36 整合: 表 F が同じなのに道具が違う書類を 1 本作る", m_tool_diff_one, (u"verdict",)),
    (u"M37 §2 の本番の fact を 63237 に", lambda c: rep(c, u"| fact | 63236 |", u"| fact | 63237 |"), (u"frag", u"numbers")),
    (u"M38 §2 の紙の欄の数 168966 を 168967 に", lambda c: rep(c, u"| 紙の欄の数 | 168966 |", u"| 紙の欄の数 | 168967 |"), (u"frag", u"numbers")),
    (u"M39 項の表の「要素の線 × 4」の 93644 を 93645 に", lambda c: rep(c, u"| 要素の線 × 4 | 93644 |", u"| 要素の線 × 4 | 93645 |"), (u"frag", u"numbers")),
    (u"M40 書類ごとの率の最小 1.3% を 1.4% に", lambda c: rep(c, u"最小 1.3%", u"最小 1.4%"), (u"frag", u"numbers")),
    (u"M41 タクソノミが同じ 65 本を 66 本に", lambda c: rep(c, u"タクソノミが同じ 65 本", u"タクソノミが同じ 66 本"), (u"frag", u"numbers")),
    (u"M42 文書に 9999 の言い切りを足す", lambda c: add_doc(c, u"fact の行は 9999 本に近い。"), (u"numbers",)),
    (u"M43 頭の「XS0-3 の 4.9%」を 5.0% に", lambda c: rep(c, u"XS0-3 の 4.9%", u"XS0-3 の 5.0%"), (u"frag", u"numbers")),
    (u"M44 §3 に 3 桁の数を足した行", lambda c: add_sec3(c, u"- 別の確かめは 100 本。"), (u"sec3",)),
    (u"M45 §3 の 37.4% を 37.5% に", lambda c: rep(c, u"開発の 5 本の比(37.4%)", u"開発の 5 本の比(37.5%)"), (u"sec3", u"numbers")),
    (u"M46 §3 の「紙に書く量は、便 XA1 の数より大きい側に在る」を消す", lambda c: rep(c, u"紙に書く量は、便 XA1 の数より大きい側に在る", u"X"), (u"sec3",)),
    (u"M47 文書に「XBRL を作れる。」を引用の外で足す", lambda c: add_doc(c, u"XBRL を作れる。"), (u"affirm",)),
    (u"M48 文書に「専用の道具が要らない。」を足す", lambda c: add_doc(c, u"専用の道具が要らない。"), (u"affirm",)),
    (u"M49 文書に「紙は人が書ける。」を足す", lambda c: add_doc(c, u"紙は人が書ける。"), (u"affirm",)),
    (u"M50 文書に「人が紙を書ける。」を足す", lambda c: add_doc(c, u"人が紙を書ける。"), (u"affirm",)),
    (u"M51 引用の行から「言えない」「読まない」を消す", m_drop_quote_negation, (u"affirm",)),
    (u"M52 「言えないこと」を消す", lambda c: drop_all(c, u"言えないこと"), (u"phrases",)),
    (u"M53 頭の「この便からは言えない」を消す", lambda c: rep(c, u"、この便からは言えない。**", u"、X。**"), (u"head",)),
    (u"M54 頭の「先に負けと限界を書く」を消す", lambda c: drop_all(c, u"先に負けと限界を書く"), (u"head",)),
    (u"M55 頭の「未使用ではない」を消す", lambda c: rep(c, u"未使用ではない", u"X"), (u"head",)),
    (u"M56 頭の「LLM の席は呼んでいない」を消す", lambda c: rep(c, u"LLM の席は呼んでいない", u"X"), (u"head",)),
    (u"M57 頭の「紙は答え(元の書類)から作っている」を消す", lambda c: rep(c, u"紙は答え(元の書類)から作っている", u"X"), (u"head",)),
    (u"M58 文書に「保証」を足す", lambda c: add_doc(c, u"保証する。"), (u"forbidden",)),
    (u"M59 文書に docID の形を足す", lambda c: add_doc(c, u"書類 S100ABCD。"), (u"forbidden",)),
    (u"M60 文書の commit の字 7706dc70 を 1 字替える", lambda c: rep(c, u"7706dc70", u"7706dc71"), (u"commits",)),
    (u"M61 文書に知らない commit の字を足す", lambda c: add_doc(c, u"commit 1a2b3c4d。"), (u"commits",)),
    (u"M62 便 XA1 の記録の写しの本番の段 2 の全部決まる fact を 1 減らす", m_xa1_full, (u"sanity",)),
    (u"M63 便 XA0 の記録の写しの本番の表の外を 1 増やす", m_xa0_outside, (u"sanity",)),
    (u"M64 §4 の実装で決めた所を 1 つ消す", m_drop_item, (u"sanity",)),
    (u"M65 §5 の次の便の候補の (iii) を替える", lambda c: rep(c, u"(iii) 未使用の書類で同じことをする", u"(iii) X"), (u"verdict",)),
    (u"M66 整合: 開発の 5 本の紙の欄を増やして比が 38% 以上", m_dev_cells_high, (u"sanity",)),
    (u"M67 頭の「便 XA1 の「全部決まらない fact」の数と同じ」を消す", lambda c: rep(c, u"便 XA1 の「全部決まらない fact」の数と同じ", u"X"), (u"frag",)),
    (u"M68 自己点検の言い切り「混ぜ物を作れなかった書類は 0」を 1 に", lambda c: rep(c, u"混ぜ物を作れなかった書類は 0", u"混ぜ物を作れなかった書類は 1"), (u"verdict",)),
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
        s = self.c.rec[AGG][G_PROD]
        self.assertEqual((63236, 3071, 62, 62, 168966, 442652), (s[u"fact の数(紙を作れた書類)"], s[u"1 つずつ書く fact の数"], s[u"表 F が同じ書類の数"], s[u"fact が同じ書類の数"],
                                                                 s[u"紙の欄の数"], s[u"fact の数 × 7"]))
        self.assertEqual((u"1.3", u"4.8", u"7.6"), rate_range(self.c.rec))
        self.assertEqual(62, len(rates_by_doc(self.c.rec)))

    def test_c_1_the_seal_has_the_bound_phrases(self):
        self.assertEqual([], bound_problems(self.c))

    def test_c_2_the_verdicts_are_decided_again_and_equal_the_document(self):
        self.assertEqual([], verdict_problems(self.c))
        j = judge(self.c.rec)
        self.assertEqual(7, sum(1 for v in j.values() if v[0]))
        self.assertEqual([u"XS0-6"], [k for k, v in j.items() if not v[0]])
        self.assertEqual(u"上", j[u"XS0-6"][1])

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

    def test_f_3_the_blob_check_lists_the_four_frozen_files_at_their_commits(self):
        self.assertEqual([SEAL_REL, SCRIPT_REL, SEAL_GATE_REL, RECORD_REL], list(BLOB_AT))
        self.assertEqual([SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT], list(BLOB_AT.values()))
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
        self.assertGreaterEqual(len(MUTATIONS), 60)

    def test_g_2_the_unmutated_copy_is_green_on_every_check(self):
        c = Ctx().copy()
        for k, fn in CHECKS.items():
            self.assertEqual([], fn(c), k)

    def test_g_3_the_recount_stays_green_when_the_data_changes_consistently_but_the_verdict_does_not(self):
        base = Ctx()
        for fn, key in ((m_cells_in_range, u"XS0-6"), (m_tablef_low, u"XS0-1"), (m_attrs_diff, u"XS0-2"), (m_hand_low, u"XS0-3"), (m_hand_high, u"XS0-3"), (m_tool_low, u"XS0-4"),
                        (m_decline3, u"XS0-5"), (m_mix_low, u"XS0-7"), (m_other_zero, u"XS0-8")):
            c = base.copy()
            fn(c)
            self.assertEqual([], recount_problems(c), fn.__name__)
            self.assertNotEqual([], verdict_problems(c), fn.__name__)
            self.assertNotEqual(judge(base.rec)[key][0], judge(c.rec)[key][0], (fn.__name__, key))

    def test_g_4_every_check_name_a_mutation_names_exists_and_every_check_has_a_mutation(self):
        named = set(k for _, _, ks in MUTATIONS for k in ks)
        self.assertEqual(set(CHECKS), named)

    def test_g_5_the_judgement_edges_at_the_seal_bounds(self):
        u"""境の 1 つ手前と境の数(丸める前の整数): 下限は含む(XS0-3 は 4.8%・XS0-6 は 33.6%・XS0-8 は 2%)・上限は XS0-3・XS0-6・XS0-8 が含まない。XS0-2 の 0.2% は含む。"""
        def with_(**kw):
            c = Ctx().copy()
            s = c.rec[AGG][G_PROD]
            s[u"fact の数(紙を作れた書類)"] = 1000
            s[u"fact の数(属性を作れた書類)"] = 1000
            s[u"fact の数 × 7"] = 7000
            s[u"1 つずつ書く fact の数"] = 50
            s[u"そのほかの属性を持つ fact の数"] = 50
            s[u"紙の欄の数"] = 2400
            s[u"attrs が違う fact の数"] = 0
            s[u"表 F が同じ書類の数"] = 62
            s[u"fact が同じ書類の数"] = 62
            s[u"断った段ごとの数"][STAGES[1]] = 0
            s[u"混ぜ物を作れた書類の数"] = 62
            s[u"混ぜ物が効いた書類の数"] = 62
            m = {u"hand": u"1 つずつ書く fact の数", u"other": u"そのほかの属性を持つ fact の数", u"cells": u"紙の欄の数", u"diff": u"attrs が違う fact の数", u"tf": u"表 F が同じ書類の数",
                 u"tool": u"fact が同じ書類の数", u"mixed": u"混ぜ物が効いた書類の数"}
            for key, val in kw.items():
                if key == u"decl":
                    s[u"断った段ごとの数"][STAGES[1]] = val
                else:
                    s[m[key]] = val
            return judge(c.rec)
        for key, lo_hit, lo_miss, hi_hit, hi_miss in ((u"XS0-3", 48, 47, 64, 65), (u"XS0-8", 20, 19, 99, 100)):
            name = {u"XS0-3": u"hand", u"XS0-8": u"other"}[key]
            self.assertTrue(with_(**{name: lo_hit})[key][0])
            self.assertFalse(with_(**{name: lo_miss})[key][0])
            self.assertTrue(with_(**{name: hi_hit})[key][0])
            self.assertFalse(with_(**{name: hi_miss})[key][0])
        self.assertTrue(with_(cells=2352)[u"XS0-6"][0])
        self.assertFalse(with_(cells=2351)[u"XS0-6"][0])
        self.assertTrue(with_(cells=2659)[u"XS0-6"][0])
        self.assertFalse(with_(cells=2660)[u"XS0-6"][0])
        self.assertTrue(with_(diff=2)[u"XS0-2"][0])
        self.assertFalse(with_(diff=3)[u"XS0-2"][0])
        self.assertTrue(with_(tf=60)[u"XS0-1"][0])
        self.assertFalse(with_(tf=59)[u"XS0-1"][0])
        self.assertTrue(with_(tool=60)[u"XS0-4"][0])
        self.assertFalse(with_(tool=59)[u"XS0-4"][0])
        self.assertTrue(with_(decl=2)[u"XS0-5"][0])
        self.assertFalse(with_(decl=3)[u"XS0-5"][0])
        self.assertTrue(with_(mixed=62)[u"XS0-7"][0])
        self.assertFalse(with_(mixed=61)[u"XS0-7"][0])

    def test_g_6_the_miss_direction_follows_the_bound(self):
        c = Ctx().copy()
        m_cells_in_range(c)
        self.assertTrue(judge(c.rec)[u"XS0-6"][0])
        c = Ctx().copy()
        m_dev_cells_high(c)
        self.assertEqual(u"上", judge(Ctx().rec)[u"XS0-6"][1])
        c = Ctx().copy()
        m_hand_low(c)
        self.assertEqual(u"下", judge(c.rec)[u"XS0-3"][1])
        c = Ctx().copy()
        m_hand_high(c)
        self.assertEqual(u"上", judge(c.rec)[u"XS0-3"][1])

    def test_g_7_the_self_suspicion_conditions_fire_for_each_cause(self):
        c = Ctx().copy()
        m_hand_low(c)
        self.assertEqual([u"封 §4 の「先に自分の欠陥を疑う場合」が発火している"], [p for p in verdict_problems(c) if u"発火" in p])
        c = Ctx().copy()
        m_tool_diff_one(c)
        self.assertEqual(1, suspects(c)[2])
        c = Ctx().copy()
        m_tablef_low(c)
        for d in docs_of(c.rec, G_PROD)[:5]:
            set_hand(d, 0)
        rebuild(c.rec)
        self.assertEqual(5, suspects(c)[3])
        self.assertEqual((0, 0, 0, 0, 0), (suspects(Ctx())[2], suspects(Ctx())[3], suspects(Ctx())[4], suspects(Ctx())[5], 0))


if __name__ == "__main__":
    unittest.main()
