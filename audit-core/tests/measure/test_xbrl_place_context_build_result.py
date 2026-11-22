# -*- coding: utf-8 -*-
u"""結果の門: 封 docs/XBRL_PLACE_CONTEXT_BUILD_SEAL_2026-11-22.md(97eff9a2)の結果の文書 docs/XBRL_PLACE_CONTEXT_BUILD_RESULT_2026-11-22.md(便 XH0)。

封の門 ``test_xbrl_place_context_build_seal.py`` の次の段。**追跡されている記録・script・封・封への追記・封の門・結果の文書と git の履歴だけを読む**(書類の置き場も道具(Arelle)も読まない・通信しない・鍵は読まない)。
便 XA0 の結果の門 ``test_xbrl_sheet_wall_result.py`` の部品(読み・sha256・% の丸め・節の切り出し・数のトークン・禁止語・blob の道具)と、便 XS0 の結果の門の部品を読み込んで使う(門としては走らせない)。
検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表で 1 つずつ(木の file は変異させず、``Ctx`` の写しに当てる)。

 a script・記録・封・封への追記・封の門の sha256(字で留める)・記録の script の sha256・封の commit の欄・記録の限界の欄・材料の欄が script の字と同じ
 b 記録の数え直し: 書類ごとの数から、**script の関数を使わずに**、3 つの塊(開発の 5 本・本番だけの 62 本・全部)の集計の全部の欄を数え直す(秒の合計だけ 0.1 刻みの丸めの幅で)。
   書類ごとの関係(段と真偽の欄・紙の欄の項の和と紙 2 の項・置き場の数どうし・文脈の同じの導き方)・予測の判定に要る数を群の数から作り直した値と照らす
 c 予測 XH0-1〜XH0-10 の当たり外れを、封 §4 の字から取った境(丸める前の整数で。下限は含む・上限は XH0-9 が含まない)と記録から決め直し、文書 §1 の表・件数と同じことを見る。
   封 §4 の「先に自分の欠陥を疑う場合」(本番の数での値)・封 §6 の決め(XH0-3 と XH0-5 が当たりなら次の便の候補を示す)と文書が合う
 d 結果の文書の数: 数字を含む行は全部、記録(と便 XS0 の記録・封への追記)から組んだ数の並びの内。表の行・言い切りは記録から組んだ字とそのまま照らす。
   「断った 1 本」「1 つずつ書く fact の在る cell の中の 1 つずつ書く fact でない fact(7 本の書類)」「タクソノミが同じ 60(組めた 61 本では 60)」は書類ごとの数から導き直す。
   紙の欄の数の先頭 9 項が便 XS0 の記録と同じこと・比が便 XS0 の比より多いことは便 XS0 の記録と照らす
 e 文書の要点の字・頭の負けと限界・禁止語・「作れる」「専用の道具が要らない」「人が書ける」を肯定で書かない・docID と EDINET コードの形
 f 封・script・記録・封への追記・封の門が commit の blob と一致(結果の便で 0 行)・engine は封の commit から 0 行・順序・文書が書く commit の字が実の履歴と合う
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


WG = load_module("tests/measure/test_xbrl_sheet_wall_result.py", "xbrl_sheet_wall_result_gate_for_place_context_result_gate")                # 便 XA0 の結果の門の部品。門としては走らせない
SG = load_module("tests/measure/test_xbrl_place_context_build_seal.py", "xbrl_place_context_build_seal_gate_for_result_gate")                # 封の門の部品。門としては走らせない
PR = SG.load_order_helpers()
MS = SG.MS

read, sha_file, guard, pct, section, rep = WG.read, WG.sha_file, WG.guard, WG.pct, WG.section, WG.rep
add_doc, drop_all = WG.add_doc, WG.drop_all

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
RECORD_REL = SG.RECORD_REL
ADDENDUM_REL = "docs/XBRL_PLACE_CONTEXT_BUILD_SEAL_ADDENDUM_2026-11-22.md"
XS0_RECORD_REL = "fixtures/xbrl/cd8/sheet_build_2026-11-22.json"
GATE_REL = "tests/measure/test_xbrl_place_context_build_result.py"
DOC_REL = "docs/XBRL_PLACE_CONTEXT_BUILD_RESULT_2026-11-22.md"
SCRIPT_COMMIT_SHORT = "2761b2dd"                  # script・封の門・封への追記を足した commit
RECORD_COMMIT_SHORT = "32e6c6a4"                  # 記録を足した commit
BLOB_AT = collections.OrderedDict([
    (SEAL_REL, SEAL_COMMIT_SHORT), (SCRIPT_REL, SCRIPT_COMMIT_SHORT), (SEAL_GATE_REL, SCRIPT_COMMIT_SHORT), (ADDENDUM_REL, SCRIPT_COMMIT_SHORT), (RECORD_REL, RECORD_COMMIT_SHORT)])
DOC_COMMITS = (SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT)

SHA_PIN = collections.OrderedDict([
    (RECORD_REL, "b440eee93d6aa33eb9443c10ce2dc7f9aeebb3e2b3aae878120210c13a764e7e"),
    (SCRIPT_REL, "5d78457abf301bb5b9b30b0ecdeb937b493f99a02be1056261f1703f2b0f5679"),
    (SEAL_GATE_REL, "7a4f5253a076194fc6feefa81b05598f506b96a1c79115725467fee97b925e0d"),
    (SEAL_REL, "dc295d8c178dbaefd26066520f6654f607e7f32cebb72821bda44ad1f1d8d3fd"),
    (ADDENDUM_REL, "3659c8b188bf99313832f07ff975580d27f9627bb1b77ec729b0955c5bb5e099"),
    (XS0_RECORD_REL, "f3f781d6c44820e38172d37bbc0135ba32fbc2b2676a74f17b64cb28af66d539")])

DEV_COUNT = 5
DOC_COUNT = 67
G_DEV, G_PROD = WG.G_DEV, WG.G_PROD
G_ALL = u"全部"
GROUPS = (G_DEV, G_PROD, G_ALL)
AGG = u"集計"
PRED_KEY = u"予測の判定に要る数(XH0-1〜XH0-10。本番だけの 62 本。当たり・外れは結果の文書で)"
PK = (u"XH0-1 規則が当てた fact / 1 つずつ書く fact でない fact", u"XH0-2 例外の cell / 決めの在る cell(1 つずつ書く fact の在る cell を除く)", u"XH0-3 文脈が同じ書類",
      u"XH0-4 文脈と単位を作る命令が断った書類", u"XH0-5 道具が読む fact が同じ書類", u"XH0-6 鳴り方が同じ書類", u"XH0-7 元にだけ在る id が 1 つ以上在る書類",
      u"XH0-8 混ぜ物が効いた書類 / 作れた書類", u"XH0-9 紙の欄の数 / fact の数 × 7", u"XH0-10 包みが元と byte で同じ書類")
STAGES = tuple(MS.STAGES)
ST_PAPER, ST_PLACE, ST_CTX, ST_ATTR, ST_BUILD = STAGES
assert STAGES == (u"紙を作る", u"置き場を作る", u"文脈と単位を作る", u"属性を作る", u"組む")
HAND_REASONS = (u"表の外", u"便 XA1 の段 2 で全部決まらない", u"文脈の定義が 2 つ以上", u"期間の種類が name の決めと違う")
CELL_KEYS = (u"書式の類の決め", u"name ごとの期間の種類", u"表ごとの 3", u"要素の線 × 4", u"終わりの日を決める側の線 × 1", u"member の組を決める側の線 × 1", u"空の fact の印", u"そのほかの属性",
             u"1 つずつ書く fact × 7", u"空の fact の形", u"1 つずつ書く fact の始まりと終わり", u"例外の cell", u"例外の cell の中の fact の始まりと終わり", u"識別子と scheme", u"期の表", u"member の表",
             u"単位の表")
XS0_ITEMS = CELL_KEYS[:9]
PAPER2_ITEMS = CELL_KEYS[9:]
ATTR_KEYS = (u"属性 name", u"属性 contextRef", u"属性 unitRef", u"属性 decimals", u"属性 scale", u"属性 format", u"属性 sign", u"属性 footnoteRefs", u"属性 id", u"属性 escape", u"属性 xsi:nil")
IDS = (u"XH0-1", u"XH0-2", u"XH0-3", u"XH0-4", u"XH0-5", u"XH0-6", u"XH0-7", u"XH0-8", u"XH0-9", u"XH0-10")
K_A = u"例外の cell の数(元は fact が無いのに規則が付ける)"
K_B = u"例外の cell の数(元は fact が在るのに規則が違う)"
K_EXC = u"例外の cell の数"
K_INNER = u"1 つずつ書く fact の在る cell の中の 1 つずつ書く fact でない fact の数"
K_OUT = u"決めの在る cell の外に在る 1 つずつ書く fact でない fact の数"
K_NONHAND = u"1 つずつ書く fact でない fact の数"
K_HIT = u"規則が当てた fact の数"
K_DECIDED = u"決めの在る cell の数"
K_HANDCELL = u"1 つずつ書く fact の在る cell の数"
K_REASON = u"1 つずつ書く fact の理由(重ねて数える)"
CTX_NULL_KEYS = (u"元の文脈の定義の数", u"作った定義の数", u"中身が違う id の数", u"元にだけ在る id の数", u"作った側にだけ在る id の数", u"期の名の数", u"member の数", u"単位の数", u"(ア)だけが指す id の数")
SEC_KEYS = (u"置き場を作る命令の秒の合計", u"文脈と単位を作る命令の秒の合計", u"属性を作る命令の秒の合計", u"組む命令の秒の合計")
SEC_DOC_KEYS = (u"置き場を作る命令の秒", u"文脈と単位を作る命令の秒", u"属性を作る命令の秒", u"組む命令の秒")
NEXT_START, NEXT_END = u"(i) 文の fact の置き場と属性を紙から作る", u"同じことをする。"

BOUND_SEAL_PHRASES = (u"置き場の規則が当てたものは 97% 以上", u"例外の cell は、決めの在る cell(1 つずつ書く fact の在る cell を除く)の 3% 以下", u"文脈が同じ書類は 55 本以上",
                      u"文脈と単位を作る命令が断った書類は 5 本以下", u"道具が読む fact が元と同じ書類は 55 本以上", u"鳴り方が同じ書類は 55 本以上", u"1 つ以上在る書類は 5 本以下",
                      u"混ぜ物は 2 つとも、作れた書類の全部で効く", u"紙の欄の比は 40% 以上 44% 未満", u"包みが元と byte で同じ書類は 0 本",
                      u"決めの在る cell の外に、1 つずつ書く fact でない fact が 1 つでも在る・置き場が同じでない書類が在る・例外の cell が 62 本の全部で 0・文脈が同じなのに道具が読む fact が違う書類が在る・断った書類が 10 本以上・混ぜ物を作れなかった書類(期)が 1 本でも在る",
                      u"XH0-3 と XH0-5 が当たりなら、次の便の候補を人間に示す", u"「XBRL を作れる」「専用の道具が要らない」は、この便からは言えない")
# 文書 §1 の表の予測の欄に在るべき境の字(封 §4 の同じ行にも在る)
ROW_BOUND = collections.OrderedDict([(u"XH0-1", u"97% 以上"), (u"XH0-2", u"3% 以下"), (u"XH0-3", u"55 本以上"), (u"XH0-4", u"5 本以下"), (u"XH0-5", u"55 本以上"), (u"XH0-6", u"55 本以上"),
                                      (u"XH0-7", u"5 本以下"), (u"XH0-8", u"作れた書類の全部で効く"), (u"XH0-9", u"40% 以上 44% 未満"), (u"XH0-10", u"0 本")])
HEAD_PHRASES = (u"先に負けと限界を書く", u"記録から 1 つずつ読んだもの", u"ただし予測は全部、開発の 5 本で数を見てから置いた", u"XH0-1・XH0-2 の境は 5 本の数より緩く置いた", u"当たりの数そのものに情報は少ない",
                u"紙も紙 2 も答え(元の書類)から作っている", u"「人が紙を書けば XBRL が作れる」とは読まない", u"人が書く紙が正しいかは測っていない",
                u"例外の cell は元と比べて決めている", u"「置き場が同じ」の 62/62 は、例外を元から写した上での数で、作りから当たる",
                u"XH0-8(混ぜ物・期)は弱い証拠", u"封の字のとおりには実装できず(封の誤り", u"読めていない数が 1 つ在る", u"どういう cell かは読んでいない",
                u"持ち込み(素の本文・文の fact と脚注の行・見えない fact・参照・提出者別タクソノミの表)はこの便でも作っていない", u"文の fact(どの文にどの要素を付けるか)は元から写している",
                u"member の表・期の表・単位の表は元の定義から写している", u"未使用ではない", u"未使用の書類で同じ率になるとは言えない", u"置き場は字の番号で比べている",
                u"その 1 本は属性も包みも作れていない", u"封の字のままなら", u"期の表は「期の名 1 つに期間 1 つ」を前提にしていて、その前提が合わない書類が在る",
                u"記録の監査の限界", u"封の門の穴(追記 §4。直していない)", u"道具が読む fact が元と同じでも、EDINET の本物の検査に通ることは言えない",
                u"便 XA0・便 XA1・便 XB0・便 XT0・便 XP0・便 XS0 の限界の全部を継ぐ", u"0 USD・LLM の席は呼んでいない", u"engine は 0 行", u"書類は便 XG0 と同じ 67 本",
                u"「XBRL を作れる」「専用の道具が要らない」は、この便からは言えない")
PHRASES = (u"言えること", u"言えないこと", u"人間に示す次の便の候補", u"別の封が先", u"盲検ではない", u"実装で決めた所", u"記録に欄の無い読み", u"人間に返すこと",
           u"人が紙を書けるか・人が書いた紙が正しいか", u"例外の cell を元を見ずに決められるか", u"EDINET の本物の検査に通るか", u"相手の問いへの、この便からの答え", u"印刷会社の道具の代わりと言うには",
           u"期の表の形を変えれば作れるかは測っていない")
STRUCTURAL = WG.STRUCTURAL
BOUND_NUMBERS = set([u"97", u"3", u"55", u"5", u"40", u"44", u"10", u"62", u"67", u"61", u"60", u"1"])
QUOTED_CLAIM = WG.QUOTED_CLAIM
AFFIRM_WORDS = tuple(WG.AFFIRM_WORDS) + (u"人が紙を書ける(?!か)", u"紙は人が書ける", u"紙を人が書ける", u"人が紙を書けば XBRL が作れる(?!」)")


# ======================================================================================================
class Ctx(object):
    u"""検査が見る写し。変異はこの写しを変える(木の file は変えない)。"""

    def __init__(self):
        self.rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        self.xs0 = json.loads(read(XS0_RECORD_REL), object_pairs_hook=collections.OrderedDict)
        self.doc = read(DOC_REL)
        self.seal = read(SEAL_REL)
        self.add = read(ADDENDUM_REL)
        self.shas = collections.OrderedDict((rel, sha_file(rel)) for rel in SHA_PIN)

    def copy(self):
        c = Ctx.__new__(Ctx)
        c.rec = copy.deepcopy(self.rec)
        c.xs0 = copy.deepcopy(self.xs0)
        c.doc = self.doc
        c.seal = self.seal
        c.add = self.add
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


def ssum(docs, key):
    u"""値が None でない書類だけを足す(断った書類は文脈の欄が None)。"""
    return sum(d[key] for d in docs if d[key] is not None)


def totals(docs):
    u"""書類ごとの数から、記録の集計の 1 つの塊の欄を数え直す(秒の合計は 0.1 刻みに丸めた値)。"""
    live = [d for d in docs if d[u"断った段"] != ST_PAPER]
    ctxd = [d for d in docs if d[u"文脈と単位を作れた"]]
    made = [d for d in docs if d[u"属性を作れた"]]
    t = collections.OrderedDict()
    t[u"書類の数"] = len(docs)
    t[u"断った書類の数"] = sum(1 for d in docs if d[u"断った"])
    t[u"断った段ごとの数"] = collections.OrderedDict((st, sum(1 for d in docs if d[u"断った段"] == st)) for st in STAGES)
    reasons = collections.OrderedDict()
    for d in docs:
        if d[u"断った"]:
            k = u"%s: %s" % (d[u"断った段"], d[u"断った理由"])
            reasons[k] = reasons.get(k, 0) + 1
    t[u"断った理由ごとの数"] = reasons
    t[u"紙を作れた書類の数"] = len(live)
    fact = sum(d[u"fact の数"] for d in live)
    t[u"fact の数(紙を作れた書類)"] = fact
    t[u"1 つずつ書く fact の数"] = sum(d[u"1 つずつ書く fact の数"] for d in live)
    t[u"1 つずつ書く fact の理由ごとの数(重ねて数える)"] = collections.OrderedDict((k, sum(d[K_REASON][k] for d in live)) for k in HAND_REASONS)
    t[u"そのほかの属性を持つ fact の数"] = sum(d[u"そのほかの属性を持つ fact の数"] for d in live)
    t[K_DECIDED] = sum(d[K_DECIDED] for d in live)
    t[K_HANDCELL] = sum(d[K_HANDCELL] for d in live)
    t[K_A] = sum(d[K_A] for d in live)
    t[K_B] = sum(d[K_B] for d in live)
    t[K_EXC] = t[K_A] + t[K_B]
    t[u"例外の cell が在る書類の数"] = sum(1 for d in live if d[K_A] + d[K_B] > 0)
    t[K_INNER] = sum(d[K_INNER] for d in live)
    t[K_NONHAND] = sum(d[K_NONHAND] for d in live)
    t[K_HIT] = sum(d[K_HIT] for d in live)
    t[K_OUT] = sum(d[K_OUT] for d in live)
    t[u"置き場を作れた書類の数"] = sum(1 for d in docs if d[u"置き場を作れた"])
    t[u"置き場が同じ書類の数"] = sum(1 for d in docs if d[u"置き場が同じ"])
    t[u"表 F の行が全部同じ書類の数"] = sum(1 for d in docs if d[u"表 F の行が全部同じ"])
    t[u"文脈と単位を作れた書類の数"] = len(ctxd)
    for k in (u"元の文脈の定義の数", u"作った定義の数", u"中身が違う id の数", u"元にだけ在る id の数"):
        t[k] = ssum(docs, k)
    t[u"元にだけ在る id が 1 つ以上在る書類の数"] = sum(1 for d in docs if (d[u"元にだけ在る id の数"] or 0) > 0)
    t[u"作った側にだけ在る id の数"] = ssum(docs, u"作った側にだけ在る id の数")
    t[u"文脈が同じ書類の数"] = sum(1 for d in docs if d[u"文脈が同じ"])
    t[u"単位が同じ書類の数"] = sum(1 for d in docs if d[u"単位が同じ"])
    t[u"定義の並びまで同じ書類の数"] = sum(1 for d in docs if d[u"定義の並びまで同じ"])
    for k in (u"期の名の数", u"member の数", u"単位の数", u"(ア)だけが指す id の数"):
        t[k] = ssum(docs, k)
    t[u"属性を作れた書類の数"] = len(made)
    t[u"fact の数(属性を作れた書類)"] = sum(d[u"fact の数"] for d in made)
    t[u"表 F が同じ書類の数"] = sum(1 for d in docs if d[u"表 F が同じ"])
    t[u"attrs が違う fact の数"] = ssum(made, u"attrs が違う fact の数")
    t[u"attrs が違う属性ごとの fact の数(重ねて数える)"] = collections.OrderedDict((k, sum(d[u"attrs が違う属性ごとの fact の数(重ねて数える)"][k] for d in made)) for k in ATTR_KEYS)
    t[u"組めた書類の数"] = sum(1 for d in docs if d[u"組めた"])
    t[u"fact が同じ書類の数"] = sum(1 for d in docs if d[u"fact が同じ"])
    t[u"鳴り方が同じ書類の数"] = sum(1 for d in docs if d[u"鳴り方が同じ"])
    t[u"タクソノミが同じ書類の数"] = sum(1 for d in docs if d[u"タクソノミが同じ"])
    t[u"全部同じ書類の数"] = sum(1 for d in docs if d[u"全部同じ"])
    t[u"2 回組んで同じ書類の数"] = sum(1 for d in docs if d[u"2 回組んで同じ"])
    t[u"包みが元と byte で同じ書類の数"] = sum(1 for d in docs if d[u"包みが元と byte で同じ"])
    t[u"混ぜ物(期)を作れた書類の数"] = sum(1 for d in docs if d[u"混ぜ物(期)"][u"作れた"])
    t[u"混ぜ物(期)が効いた書類の数"] = sum(1 for d in docs if d[u"混ぜ物(期)"][u"効いた"])
    t[u"混ぜ物(置き場)を作れた書類の数"] = sum(1 for d in docs if d[u"混ぜ物(置き場)"][u"作れた"])
    t[u"混ぜ物(置き場)が効いた書類の数"] = sum(1 for d in docs if d[u"混ぜ物(置き場)"][u"効いた"])
    items = collections.OrderedDict((k, sum(d[u"紙の欄の数(項ごと)"][k] for d in live)) for k in CELL_KEYS)
    t[u"紙の欄の数(項ごと)"] = items
    t[u"紙の欄の数"] = sum(items.values())
    t[u"fact の数 × 7"] = 7 * fact
    t[u"紙の欄の比"] = rate_row(t[u"紙の欄の数"], 7 * fact)
    for k, dk in zip(SEC_KEYS, SEC_DOC_KEYS):
        t[k] = round(sum(d[dk] for d in docs if d[dk] is not None), 1)
    return t


def norm(o):
    return json.loads(json.dumps(o, ensure_ascii=False))


def z(d, k):
    return d[k] or 0


def doc_problems(d):
    u"""書類 1 つの中の関係(段と真偽の欄・紙の欄の項の和と紙 2 の項・置き場の数どうし・文脈の同じの導き方)。"""
    out = []
    n = d[u"番号"]
    dec = d[u"断った"]
    if dec != bool(d[u"断った理由"]) or dec != bool(d[u"断った段"]) or (dec and d[u"断った段"] not in STAGES):
        out.append(u"書類 %d の断りの欄が合わない" % n)
        return out
    idx = STAGES.index(d[u"断った段"]) if dec else len(STAGES)
    if d[u"置き場を作れた"] != (idx > 1) or d[u"文脈と単位を作れた"] != (idx > 2) or d[u"属性を作れた"] != (idx > 3):
        out.append(u"書類 %d の「作れた」の欄が断った段と合わない" % n)
    if d[u"組めた"] and dec:
        out.append(u"書類 %d が断ったのに組めた" % n)
    if d[u"全部同じ"] != (d[u"タクソノミが同じ"] and d[u"fact が同じ"]):
        out.append(u"書類 %d の全部同じが、タクソノミが同じと fact が同じの両方でない" % n)
    if d[u"表 F が同じ"] != (d[u"属性を作れた"] and d[u"attrs が違う fact の数"] == 0):
        out.append(u"書類 %d の表 F が同じが、attrs の違い 0 と属性を作れたの両方でない" % n)
    if (d[u"fact が同じ"] or d[u"鳴り方が同じ"] or d[u"2 回組んで同じ"]) and not d[u"組めた"]:
        out.append(u"書類 %d が組めていないのに fact・鳴り方・2 回組んで同じ" % n)
    if d[u"組めた"] and not d[u"属性を作れた"]:
        out.append(u"書類 %d が属性を作れていないのに組めた" % n)
    if d[u"文脈が同じ"] != (d[u"文脈と単位を作れた"] and z(d, u"中身が違う id の数") == 0 and z(d, u"元にだけ在る id の数") == 0 and z(d, u"作った側にだけ在る id の数") == 0):
        out.append(u"書類 %d の文脈が同じが、作れたと id の違い 0 の全部でない" % n)
    if d[u"単位が同じ"] and not d[u"文脈と単位を作れた"]:
        out.append(u"書類 %d が文脈と単位を作れていないのに単位が同じ" % n)
    if d[u"定義の並びまで同じ"] and not d[u"文脈が同じ"]:
        out.append(u"書類 %d が文脈が同じでないのに定義の並びまで同じ" % n)
    if d[u"混ぜ物(期)"][u"効いた"] and not d[u"混ぜ物(期)"][u"作れた"]:
        out.append(u"書類 %d の混ぜ物(期)が作れていないのに効いた" % n)
    if d[u"混ぜ物(期)"][u"作れた"] and not d[u"文脈と単位を作れた"]:
        out.append(u"書類 %d が文脈を作れていないのに混ぜ物(期)を作れた" % n)
    if d[u"混ぜ物(置き場)"][u"効いた"] and not d[u"混ぜ物(置き場)"][u"作れた"]:
        out.append(u"書類 %d の混ぜ物(置き場)が作れていないのに効いた" % n)
    if d[u"混ぜ物(置き場)"][u"作れた"] and not d[u"置き場を作れた"]:
        out.append(u"書類 %d が置き場を作れていないのに混ぜ物(置き場)を作れた" % n)
    if d[u"置き場が同じ"] and not d[u"置き場を作れた"]:
        out.append(u"書類 %d が置き場を作れていないのに置き場が同じ" % n)
    if idx > 3 and d[u"表 F の行が全部同じ"] and not d[u"置き場が同じ"]:
        out.append(u"書類 %d の表 F の行が全部同じなのに置き場が同じでない" % n)
    if dec and (d[u"全部同じ"] or d[u"fact が同じ"] or d[u"鳴り方が同じ"] or d[u"組めた"] or d[u"2 回組んで同じ"]):
        out.append(u"書類 %d が断ったのに組めた・同じの欄が真" % n)
    if idx > 2:
        for k in CTX_NULL_KEYS:
            if d[k] is None:
                out.append(u"書類 %d が文脈を作れたのに %s が None" % (n, k))
    # 紙の欄・置き場の数
    items = d[u"紙の欄の数(項ごと)"]
    if list(items) != list(CELL_KEYS) or d[u"紙の欄の数"] != sum(items.values()):
        out.append(u"書類 %d の紙の欄の項の和が紙の欄の数と違う" % n)
        return out
    h = d[u"1 つずつ書く fact の数"]
    if items[CELL_KEYS[8]] != 7 * h:
        out.append(u"書類 %d の「1 つずつ書く fact × 7」が 7 倍と違う" % n)
    if items[CELL_KEYS[10]] != 2 * h:
        out.append(u"書類 %d の「1 つずつ書く fact の始まりと終わり」が 2 倍と違う" % n)
    if items[CELL_KEYS[9]] != 1 or items[CELL_KEYS[13]] != 2:
        out.append(u"書類 %d の「空の fact の形」「識別子と scheme」が 1・2 でない" % n)
    exc = d[K_A] + d[K_B] + d[K_INNER] + d[K_OUT]
    if items[CELL_KEYS[11]] != exc or items[CELL_KEYS[12]] != 2 * (d[K_B] + d[K_INNER] + d[K_OUT]):
        out.append(u"書類 %d の例外の cell の項が例外の数と合わない" % n)
    if d[u"文脈と単位を作れた"]:
        if items[CELL_KEYS[15]] != 2 * d[u"member の数"] or items[CELL_KEYS[16]] != 2 * d[u"単位の数"] or not 2 * d[u"期の名の数"] <= items[CELL_KEYS[14]] <= 3 * d[u"期の名の数"]:
            out.append(u"書類 %d の期の表・member の表・単位の表の欄が表の行の数と合わない" % n)
    rs = d[K_REASON]
    if list(rs) != list(HAND_REASONS):
        out.append(u"書類 %d の理由の名が違う" % n)
    else:
        if not (max(rs.values()) <= h <= sum(rs.values())) or h > d[u"fact の数"]:
            out.append(u"書類 %d の 1 つずつ書く fact の数が理由の数・fact の数と合わない" % n)
        if d[K_HANDCELL] != rs[HAND_REASONS[1]]:
            out.append(u"書類 %d の 1 つずつ書く fact の在る cell が便 XA1 の理由の数と違う" % n)
    if d[K_NONHAND] != d[u"fact の数"] - h:
        out.append(u"書類 %d の 1 つずつ書く fact でない fact が fact − 1 つずつ書く fact と違う" % n)
    if d[K_NONHAND] - d[K_HIT] != d[K_B] + d[K_INNER] + d[K_OUT]:
        out.append(u"書類 %d の当てなかった fact が「元は fact が在るのに規則が違う cell」+ 手の cell の中 + 決めの外と違う" % n)
    if d[K_DECIDED] < d[K_HANDCELL]:
        out.append(u"書類 %d の決めの在る cell が 1 つずつ書く fact の在る cell より少ない" % n)
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
    return out


def pred_expected(rec):
    s = rec[AGG][G_PROD]
    n = s[u"書類の数"]

    def docs(a, b=None):
        return collections.OrderedDict([(u"書類", a), (u"分母", n if b is None else b)])
    return collections.OrderedDict([
        (PK[0], rate_row(s[K_HIT], s[K_NONHAND])),
        (PK[1], rate_row(s[K_EXC], s[K_DECIDED] - s[K_HANDCELL])),
        (PK[2], docs(s[u"文脈が同じ書類の数"])),
        (PK[3], docs(s[u"断った段ごとの数"][ST_CTX])),
        (PK[4], docs(s[u"fact が同じ書類の数"])),
        (PK[5], docs(s[u"鳴り方が同じ書類の数"])),
        (PK[6], docs(s[u"元にだけ在る id が 1 つ以上在る書類の数"])),
        (PK[7], collections.OrderedDict([(u"期", docs(s[u"混ぜ物(期)が効いた書類の数"], s[u"混ぜ物(期)を作れた書類の数"])),
                                         (u"置き場", docs(s[u"混ぜ物(置き場)が効いた書類の数"], s[u"混ぜ物(置き場)を作れた書類の数"]))])),
        (PK[8], rate_row(s[u"紙の欄の数"], s[u"fact の数 × 7"])),
        (PK[9], docs(s[u"包みが元と byte で同じ書類の数"]))])


def judge(rec):
    u"""封 §4 の境(丸める前の整数)から XH0-1〜XH0-10 を決め直す。値は (当たりか, 外れた向き)。"""
    s = rec[AGG][G_PROD]
    out = collections.OrderedDict()

    def put(k, lo_ok, hi_ok):
        out[k] = (lo_ok and hi_ok, u"" if lo_ok and hi_ok else (u"下" if not lo_ok else u"上"))
    put(u"XH0-1", 100 * s[K_HIT] >= 97 * s[K_NONHAND], True)
    put(u"XH0-2", True, 100 * s[K_EXC] <= 3 * (s[K_DECIDED] - s[K_HANDCELL]))
    put(u"XH0-3", s[u"文脈が同じ書類の数"] >= 55, True)
    put(u"XH0-4", True, s[u"断った段ごとの数"][ST_CTX] <= 5)
    put(u"XH0-5", s[u"fact が同じ書類の数"] >= 55, True)
    put(u"XH0-6", s[u"鳴り方が同じ書類の数"] >= 55, True)
    put(u"XH0-7", True, s[u"元にだけ在る id が 1 つ以上在る書類の数"] <= 5)
    both = (s[u"混ぜ物(期)を作れた書類の数"] > 0 and s[u"混ぜ物(期)が効いた書類の数"] == s[u"混ぜ物(期)を作れた書類の数"]
            and s[u"混ぜ物(置き場)を作れた書類の数"] > 0 and s[u"混ぜ物(置き場)が効いた書類の数"] == s[u"混ぜ物(置き場)を作れた書類の数"])
    put(u"XH0-8", both, True)
    put(u"XH0-9", 100 * s[u"紙の欄の数"] >= 40 * s[u"fact の数 × 7"], 100 * s[u"紙の欄の数"] < 44 * s[u"fact の数 × 7"])
    put(u"XH0-10", True, s[u"包みが元と byte で同じ書類の数"] <= 0)
    return out


def suspects(c):
    u"""封 §4 の「先に自分の欠陥を疑う場合」の、本番の数での値(順に: 決めの外の 1 つずつ書く fact でない fact・置き場が同じでない書類・例外の cell が全部の書類で 0 か(0 か 1)・
    文脈が同じなのに道具が読む fact が違う書類・断った書類・混ぜ物(期)を作れなかった書類・そのうち断っていない書類)。"""
    docs = docs_of(c.rec, G_PROD)
    s = c.rec[AGG][G_PROD]
    unmade = [d for d in docs if not d[u"混ぜ物(期)"][u"作れた"]]
    return (s[K_OUT], sum(1 for d in docs if not d[u"置き場が同じ"]), 1 if all(d[K_A] + d[K_B] == 0 for d in docs) else 0,
            sum(1 for d in docs if d[u"文脈が同じ"] and not d[u"fact が同じ"]), s[u"断った書類の数"], len(unmade), sum(1 for d in unmade if not d[u"断った"]))


def fires(sus):
    u"""封 §4 の 6 つの条件(封の字のまま)ごとの発火。混ぜ物(期)を作れなかった書類は、断った書類でも 1 本でも在れば発火する(緩めない)。"""
    return (sus[0] > 0, sus[1] > 0, sus[2] > 0, sus[3] > 0, sus[4] >= 10, sus[5] > 0)


def suspect_fires(sus):
    return any(fires(sus))


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
    m = c.rec[u"材料"]
    if m[u"道具の版"] != MS.TOOL_VERSION or m[u"規則の年"] != MS.YEAR or m[u"時間の上限(秒)"] != MS.TIMEOUT_SEC:
        out.append(u"記録の道具の版・規則の年・時間の上限が script と違う")
    if m[u"script の決めの字"] != list(MS.RULES):
        out.append(u"記録の「script の決めの字」が script の字と違う")
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
    rows = [ln for ln in sec4.splitlines() if re.match(r"^\| XH0-\d", ln)]
    if len(rows) != 10:
        out.append(u"封 §4 の表の行が 10 でない")
    return out


# ======================================================================================================
def cell_text(rec, key):
    s = rec[AGG][G_PROD]
    n = s[u"書類の数"]

    def f(a, b):
        return u"%d/%d(%s%%)" % (a, b, pct(a, b))
    return {u"XH0-1": f(s[K_HIT], s[K_NONHAND]), u"XH0-2": f(s[K_EXC], s[K_DECIDED] - s[K_HANDCELL]), u"XH0-3": u"%d/%d" % (s[u"文脈が同じ書類の数"], n),
            u"XH0-4": u"%d/%d" % (s[u"断った段ごとの数"][ST_CTX], n), u"XH0-5": u"%d/%d" % (s[u"fact が同じ書類の数"], n), u"XH0-6": u"%d/%d" % (s[u"鳴り方が同じ書類の数"], n),
            u"XH0-7": u"%d/%d" % (s[u"元にだけ在る id が 1 つ以上在る書類の数"], n),
            u"XH0-8": u"期 %d/%d・置き場 %d/%d" % (s[u"混ぜ物(期)が効いた書類の数"], s[u"混ぜ物(期)を作れた書類の数"], s[u"混ぜ物(置き場)が効いた書類の数"], s[u"混ぜ物(置き場)を作れた書類の数"]),
            u"XH0-9": f(s[u"紙の欄の数"], s[u"fact の数 × 7"]), u"XH0-10": u"%d/%d" % (s[u"包みが元と byte で同じ書類の数"], n)}[key]


def expected_cells(c):
    out = collections.OrderedDict()
    for k, (ok, way) in judge(c.rec).items():
        verdict = (u"当たり(期は弱い証拠)" if k == u"XH0-8" else u"当たり") if ok else u"外れ(%s)" % way
        out[k] = (cell_text(c.rec, k), verdict)
    return out


def verdict_problems(c):
    rec = c.rec
    j = judge(rec)
    want = expected_cells(c)
    out = []
    rows = {}
    for ln in c.doc.splitlines():
        m = re.match(r"^\| (XH0-\d+)(?:\(主\))? \|(.*)\|$", ln)
        if m:
            rows[m.group(1)] = [x.strip() for x in m.group(2).split(u"|")]
    if sorted(rows) != sorted(j):
        return [u"文書 §1 の表の行が XH0-1〜XH0-10 でない"]
    sec4 = section(c.seal, u"## §4 ", u"## §5 ")
    seal_rows = dict((ln.split(u"|")[1].strip().replace(u"(主)", u""), ln) for ln in sec4.splitlines() if re.match(r"^\| XH0-\d", ln))
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
    sec1, sec5 = section(c.doc, u"## §1 ", u"## §2 "), section(c.doc, u"## §5 ", None)
    sus = suspects(c)
    f = fires(sus)
    if f != (False, False, False, False, False, True) or sus[6] != 0:
        out.append(u"封 §4 の発火の組が文書の書く「混ぜ物(期)の 1 つだけ(作れなかったのは断った書類だけ)」と違う")
    nctx = c.rec[AGG][G_PROD][u"文脈と単位を作れた書類の数"]
    dec = declined(rec)
    reason = dec[0][u"断った理由"] if dec else u""
    line = (u"- 封 §4 の「先に自分の欠陥を疑う場合」%d つのうち、%d つは当たらない: 決めの在る cell の外に在る 1 つずつ書く fact でない fact は %d・置き場が同じでない書類は %d・例外の cell は 0 でない・"
            u"文脈が同じなのに道具が読む fact が違う書類は %d・断った書類は %d(10 本より少ない)。残る 1 つ「混ぜ物を作れなかった書類(期)が 1 本でも在る」は封の字のままなら当たる: %d 本(断った書類。"
            u"命令が文脈を作らなかったので混ぜ物も作っていない。文脈を作れた %d 本では全部作れた)。自分の欠陥を疑って読んだのは記録から言える範囲だけで、断った理由は「%s」。それ以上の原因の読みは足さない。"
            u"(2026-11-22 追記: 初めの版は「当たらない」と書いていた。封の字のままの読みに直した)" % (
                len(f), len(f) - sum(f), sus[0], sus[1], sus[3], sus[4], sus[5], nctx, reason))
    if line not in sec1.splitlines():
        out.append(u"文書 §1 の自己点検の言い切りが記録から組んだ字と違う")
    if u"- 封 §4 の「先に自分の欠陥を疑う場合」は、封の字のままなら %d つ発火している(混ぜ物(期)を作れなかった書類が %d 本。断った書類)。" % (sum(f), sus[5]) not in head.splitlines():
        out.append(u"文書の頭の「封の字のままなら発火している」の行が記録から組んだ字と違う")
    # 封 §6: XH0-3 と XH0-5 が当たりなら次の便の候補を示す
    cond = j[u"XH0-3"][0] and j[u"XH0-5"][0]
    shown = u"人間に示す次の便の候補(封 §6。XH0-3 と XH0-5 が当たりなので示す)" in sec5.replace(u"**", u"")
    if cond != shown:
        out.append(u"封 §6 の決め(XH0-3 と XH0-5 が当たりなら次の便の候補を示す)と文書 §5 が合わない")
    if cond:
        s6 = section(c.seal, u"## §6 ", u"## §7 ")
        seg = s6[s6.index(NEXT_START):s6.index(NEXT_END) + len(NEXT_END)].strip()
        if seg not in sec5:
            out.append(u"§5 の次の便の候補が封 §6 の字と違う")
        if u"別の封が先" not in sec5:
            out.append(u"§5 に「別の封が先」が無い")
    return out


# ======================================================================================================
def doc_places(rec):
    return [d for d in docs_of(rec, G_PROD)]


def inner_docs(rec, g=G_PROD):
    return [d for d in docs_of(rec, g) if d[K_INNER] > 0]


def declined(rec, g=G_PROD):
    return [d for d in docs_of(rec, g) if d[u"断った"]]


def xs0_pct(c):
    s = c.xs0[AGG][G_PROD]
    return pct(s[u"紙の欄の数"], s[u"fact の数 × 7"])


def addendum_items(c):
    sec = section(c.add, u"## 2 ", u"## 3 ")
    return len([ln for ln in sec.splitlines() if re.match(r"^\d+\. ", ln)])


def expected_lines(c):
    rec = c.rec
    p, d, a = rec[AGG][G_PROD], rec[AGG][G_DEV], rec[AGG][G_ALL]
    out = []
    one = lambda label, key: out.append(u"| %s | %d | %d |" % (label, p[key], d[key]))
    out.append(u"| 断った書類 | %d | %d |" % (p[u"断った書類の数"], d[u"断った書類の数"]))
    out.append(u"| うち文脈と単位を作る段 | %d | %d |" % (p[u"断った段ごとの数"][ST_CTX], d[u"断った段ごとの数"][ST_CTX]))
    one(u"fact", u"fact の数(紙を作れた書類)")
    one(u"1 つずつ書く fact", u"1 つずつ書く fact の数")
    one(u"1 つずつ書く fact でない fact", K_NONHAND)
    one(u"規則が当てた fact", K_HIT)
    one(u"決めの在る cell", K_DECIDED)
    one(u"1 つずつ書く fact の在る cell", K_HANDCELL)
    one(K_A.replace(u"例外の cell の数", u"例外の cell"), K_A)
    one(K_B.replace(u"例外の cell の数", u"例外の cell"), K_B)
    one(u"例外の cell", K_EXC)
    one(u"例外の cell が在る書類", u"例外の cell が在る書類の数")
    one(u"1 つずつ書く fact の在る cell の中の 1 つずつ書く fact でない fact", K_INNER)
    one(u"決めの在る cell の外に在る 1 つずつ書く fact でない fact", K_OUT)
    one(u"置き場が同じ書類", u"置き場が同じ書類の数")
    one(u"文脈と単位を作れた書類", u"文脈と単位を作れた書類の数")
    out.append(u"| 元の文脈の定義・作った定義 | %d・%d | %d・%d |" % (p[u"元の文脈の定義の数"], p[u"作った定義の数"], d[u"元の文脈の定義の数"], d[u"作った定義の数"]))
    out.append(u"| 中身が違う `id`・元にだけ在る `id`・作った側にだけ在る `id` | %d・%d・%d | %d・%d・%d |" % (
        p[u"中身が違う id の数"], p[u"元にだけ在る id の数"], p[u"作った側にだけ在る id の数"], d[u"中身が違う id の数"], d[u"元にだけ在る id の数"], d[u"作った側にだけ在る id の数"]))
    out.append(u"| 文脈が同じ書類・単位が同じ書類 | %d・%d | %d・%d |" % (p[u"文脈が同じ書類の数"], p[u"単位が同じ書類の数"], d[u"文脈が同じ書類の数"], d[u"単位が同じ書類の数"]))
    one(u"定義の並びまで同じ書類", u"定義の並びまで同じ書類の数")
    out.append(u"| 期の名・member・単位(表の行の数) | %d・%d・%d | %d・%d・%d |" % (p[u"期の名の数"], p[u"member の数"], p[u"単位の数"], d[u"期の名の数"], d[u"member の数"], d[u"単位の数"]))
    one(u"表 F が同じ書類", u"表 F が同じ書類の数")
    one(u"`attrs` が違う fact", u"attrs が違う fact の数")
    one(u"組めた書類", u"組めた書類の数")
    one(u"道具が読む fact が同じ書類", u"fact が同じ書類の数")
    one(u"鳴り方が同じ書類", u"鳴り方が同じ書類の数")
    one(u"タクソノミが同じ書類", u"タクソノミが同じ書類の数")
    one(u"全部同じ書類", u"全部同じ書類の数")
    one(u"2 回組んで同じ書類", u"2 回組んで同じ書類の数")
    one(u"包みが元と byte で同じ書類", u"包みが元と byte で同じ書類の数")
    out.append(u"| 混ぜ物(期)を作れた書類・効いた書類 | %d・%d | %d・%d |" % (p[u"混ぜ物(期)を作れた書類の数"], p[u"混ぜ物(期)が効いた書類の数"], d[u"混ぜ物(期)を作れた書類の数"], d[u"混ぜ物(期)が効いた書類の数"]))
    out.append(u"| 混ぜ物(置き場)を作れた書類・効いた書類 | %d・%d | %d・%d |" % (p[u"混ぜ物(置き場)を作れた書類の数"], p[u"混ぜ物(置き場)が効いた書類の数"], d[u"混ぜ物(置き場)を作れた書類の数"], d[u"混ぜ物(置き場)が効いた書類の数"]))
    one(u"紙の欄の数", u"紙の欄の数")
    one(u"fact の数 × 7", u"fact の数 × 7")
    out.append(u"| 紙の欄の比 | %s%% | %s%% |" % (pct(p[u"紙の欄の数"], p[u"fact の数 × 7"]), pct(d[u"紙の欄の数"], d[u"fact の数 × 7"])))
    for k in CELL_KEYS:
        out.append(u"| %s | %d |" % (k.replace(u"name ごと", u"`name` ごと"), p[u"紙の欄の数(項ごと)"][k]))
    out.append(u"- 67 本の全部では: 断った書類 %d・fact %d・規則が当てた fact %d/%d・例外の cell %d・文脈が同じ %d 本・道具が読む fact が同じ %d 本・鳴り方が同じ %d 本・タクソノミが同じ %d 本・紙の欄の比 %s%%(%d/%d)。" % (
        a[u"断った書類の数"], a[u"fact の数(紙を作れた書類)"], a[K_HIT], a[K_NONHAND], a[K_EXC], a[u"文脈が同じ書類の数"], a[u"fact が同じ書類の数"], a[u"鳴り方が同じ書類の数"], a[u"タクソノミが同じ書類の数"],
        pct(a[u"紙の欄の数"], a[u"fact の数 × 7"]), a[u"紙の欄の数"], a[u"fact の数 × 7"]))
    return out


def expected_fragments(c):
    rec = c.rec
    p, d = rec[AGG][G_PROD], rec[AGG][G_DEV]
    dec = declined(rec)
    f = []
    reason = dec[0][u"断った理由"] if dec else u""
    f.append(u"**文脈と単位を作る命令は、%d 本のうち %d 本を断った(理由: %s)。**" % (p[u"書類の数"], p[u"断った段ごとの数"][ST_CTX], reason))
    f.append(u"文脈・fact・鳴り方が同じ書類は %d/%d" % (p[u"文脈が同じ書類の数"], p[u"書類の数"]))
    f.append(u"**置き場の規則が元と違う答えを出す cell(例外の cell)は %d 本の全部に在る(合わせて %d)。**" % (p[u"例外の cell が在る書類の数"], p[K_EXC]))
    f.append(u"「置き場が同じ」の %d/%d は" % (p[u"置き場が同じ書類の数"], p[u"書類の数"]))
    f.append(u"1 つずつ書く fact の在る cell の中に、1 つずつ書く fact でない fact が %d 本で %d 在った(%d 本の書類。開発の 5 本では %d)" % (
        p[u"書類の数"], p[K_INNER], len(inner_docs(rec)), d[K_INNER]))
    f.append(u"提出者別タクソノミが元と同じ書類は %d/%d(断った 1 本は組んでいないので同じに数えていない。組めた %d 本では %d)" % (
        p[u"タクソノミが同じ書類の数"], p[u"書類の数"], p[u"組めた書類の数"], p[u"タクソノミが同じ書類の数"]))
    f.append(u"紙の欄の数の項ごと(%d 本。上の %d 項は便 XS0 の紙、下の %d 項はこの便で足した紙 2):" % (p[u"書類の数"], len(XS0_ITEMS), len(PAPER2_ITEMS)))
    f.append(u"封の字で 1 通りに決まらなかった所の %d 項と" % addendum_items(c))
    f.append(u"置き場は %d 本の全部で(例外を紙 2 に書いた上で)元に戻り、文脈と単位の定義は %d 本で元と同じになり、組んだ包みを道具が読むと fact は %d 本で元と同じだった。%d 本は命令が断った。" % (
        p[u"置き場が同じ書類の数"], p[u"文脈が同じ書類の数"], p[u"fact が同じ書類の数"], p[u"断った書類の数"]))
    f.append(u"は %d 本のうち %d 本で確かめた。ただし紙は元の書類から逆に作ったもので、置き場の例外(%d 本で %d cell)は元を見て書いている" % (
        p[u"書類の数"], p[u"組めた書類の数"], p[u"例外の cell が在る書類の数"], p[K_EXC]))
    f.append(u"`id` の作法(期の名 + member の字)は %d 本で 1 通りだった" % p[u"文脈と単位を作れた書類の数"])
    f.append(u"使われない定義を持つ書類が %d 本だったので" % p[u"元にだけ在る id が 1 つ以上在る書類の数"])
    f.append(u"定義の並びまで同じ書類は %d" % p[u"定義の並びまで同じ書類の数"])
    f.append(u"混ぜ物(置き場)は %d 本の全部で効いた" % p[u"混ぜ物(置き場)が効いた書類の数"])
    f.append(u"同じ期の名が 2 つの違う日付に当たっていて、%d つの fact がその定義を要る" % 9)
    return f


def derived_lines(c):
    u"""§3 の、記録から導く言い切り(3 桁以上の数・% を持てるのはこの字だけ)。"""
    p, d = c.rec[AGG][G_PROD], c.rec[AGG][G_DEV]
    return [u"規則を当てる対象の fact の %s%% を当てた" % pct(p[K_HIT], p[K_NONHAND]),
            u"元は fact が無いのに規則が付ける cell が %d・元は fact が在るのに規則が違う cell が %d" % (p[K_A], p[K_B]),
            u"作った定義 %d は元の定義 %d と" % (p[u"作った定義の数"], p[u"元の文脈の定義の数"]),
            u"紙の欄の比は便 XS0 の %s%% から %s%% に増えた" % (xs0_pct(c), pct(p[u"紙の欄の数"], p[u"fact の数 × 7"]))]


def sanity_problems(c):
    u"""文書の言い切りが記録の数に合う(便 XS0 の記録・封への追記との関係を含む)。"""
    rec = c.rec
    s, dv, al = rec[AGG][G_PROD], rec[AGG][G_DEV], rec[AGG][G_ALL]
    x, xd = c.xs0[AGG][G_PROD], c.xs0[AGG][G_DEV]
    out = []
    dec = declined(rec)
    if len(dec) != 1 or dec[0][u"断った段"] != ST_CTX or dec[0][u"断った理由"] != u"期の名が 1 つに決まらない" or dec[0][u"番号"] <= DEV_COUNT:
        out.append(u"断った書類が「本番の 1 本・文脈と単位を作る段・期の名が 1 つに決まらない」でない")
    if s[u"断った理由ごとの数"] != collections.OrderedDict([(u"文脈と単位を作る: 期の名が 1 つに決まらない", 1)]):
        out.append(u"断った理由ごとの数が文書の「1 本・期の名が 1 つに決まらない」と合わない")
    if (s[u"1 つずつ書く fact の数"], dv[u"1 つずつ書く fact の数"], s[u"fact の数(紙を作れた書類)"], dv[u"fact の数(紙を作れた書類)"]) != (
            x[u"1 つずつ書く fact の数"], xd[u"1 つずつ書く fact の数"], x[u"fact の数(紙を作れた書類)"], xd[u"fact の数(紙を作れた書類)"]):
        out.append(u"1 つずつ書く fact・fact の数が便 XS0 の記録と違う")
    for g, xg in ((G_PROD, x), (G_DEV, xd)):
        items = rec[AGG][g][u"紙の欄の数(項ごと)"]
        if [items[k] for k in XS0_ITEMS] != [xg[u"紙の欄の数(項ごと)"][k] for k in XS0_ITEMS] or list(xg[u"紙の欄の数(項ごと)"]) != list(XS0_ITEMS):
            out.append(u"%s の紙の欄の先頭 9 項が便 XS0 の記録の項と違う" % g)
        if rec[AGG][g][u"紙の欄の数"] - sum(items[k] for k in PAPER2_ITEMS) != xg[u"紙の欄の数"]:
            out.append(u"%s の紙の欄の数 − 紙 2 の 8 項が便 XS0 の紙の欄の数と違う" % g)
    if not s[u"紙の欄の数"] * x[u"fact の数 × 7"] > x[u"紙の欄の数"] * s[u"fact の数 × 7"]:
        out.append(u"紙の欄の比が便 XS0 の比より多くない")
    if (s[u"表 F が同じ書類の数"], s[u"fact が同じ書類の数"]) != (s[u"組めた書類の数"], s[u"組めた書類の数"]) or s[u"attrs が違う fact の数"] != 0:
        out.append(u"文書の「表 F・fact が組めた書類の全部で同じ・attrs の違い 0」が記録と合わない")
    if s[u"書類の数"] - s[u"断った書類の数"] != s[u"組めた書類の数"] or s[u"全部同じ書類の数"] != s[u"タクソノミが同じ書類の数"] or s[u"タクソノミが同じ書類の数"] != s[u"組めた書類の数"] - 1:
        out.append(u"文書の「タクソノミが同じ 60/62(組めた 61 本では 60)」が記録と合わない")
    if dec and dec[0][u"タクソノミが同じ"]:
        out.append(u"断った書類のタクソノミが同じが真(文書は同じに数えていないと書く)")
    if (s[K_INNER], len(inner_docs(rec)), dv[K_INNER]) != (50, 7, 0):
        out.append(u"文書の「1 つずつ書く fact の在る cell の中に 50(7 本の書類。開発の 5 本では 0)」が記録と合わない")
    if inner_docs(rec) and any(d[u"番号"] <= DEV_COUNT for d in inner_docs(rec)):
        out.append(u"「1 つずつ書く fact の在る cell の中」の fact が開発の 5 本に在る")
    if s[K_EXC] != s[K_A] + s[K_B] or s[u"例外の cell が在る書類の数"] != s[u"書類の数"] or al[K_EXC] != al[K_A] + al[K_B]:
        out.append(u"文書の「例外の cell は 62 本の全部に在る(合わせて足し算)」が記録と合わない")
    if s[K_DECIDED] - s[K_HANDCELL] != rec[PRED_KEY][PK[1]][u"分母"]:
        out.append(u"XH0-2 の分母が決めの在る cell − 1 つずつ書く fact の在る cell と違う")
    if (s[u"作った定義の数"], s[u"中身が違う id の数"], s[u"元にだけ在る id の数"], s[u"作った側にだけ在る id の数"]) != (s[u"元の文脈の定義の数"], 0, 0, 0):
        out.append(u"文書の「作った定義は元の定義と id も中身も全部同じ」が記録と合わない")
    if s[u"文脈が同じ書類の数"] != s[u"文脈と単位を作れた書類の数"] or s[u"単位が同じ書類の数"] != s[u"文脈と単位を作れた書類の数"]:
        out.append(u"文書の「文脈と単位を作れた書類の全部で同じ」が記録と合わない")
    if s[u"混ぜ物(置き場)を作れた書類の数"] != s[u"書類の数"] or s[u"混ぜ物(置き場)が効いた書類の数"] != s[u"書類の数"]:
        out.append(u"文書の「混ぜ物(置き場)は 62 本の全部で効いた」が記録と合わない")
    if s[u"混ぜ物(期)を作れた書類の数"] != s[u"文脈と単位を作れた書類の数"]:
        out.append(u"混ぜ物(期)を作れた書類が文脈と単位を作れた書類と違う")
    if not (s[K_NONHAND] - s[K_HIT] == s[K_B] + s[K_INNER] + s[K_OUT]):
        out.append(u"当てなかった fact の数が文書の導きと合わない")
    if al[u"書類の数"] != DOC_COUNT:
        out.append(u"全部の塊の書類の数が 67 でない")
    if addendum_items(c) != 12:
        out.append(u"封への追記の実装で決めた所が 12 項でない")
    sec4 = section(c.doc, u"## §4 ", u"## §5 ")
    if u"ADDENDUM_2026-11-22.md" not in sec4:
        out.append(u"§4 が封への追記を指していない")
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
    out.add(pct(s[K_HIT], s[K_NONHAND]))
    out.add(pct(s[K_EXC], s[K_DECIDED] - s[K_HANDCELL]))
    out.add(xs0_pct(c))
    for g in (G_DEV, G_PROD, G_ALL):
        out.add(pct(c.rec[AGG][g][u"紙の欄の数"], c.rec[AGG][g][u"fact の数 × 7"]))
    out.add(str(addendum_items(c)))
    out.add(str(len(inner_docs(c.rec))))
    out |= set(BOUND_NUMBERS)
    return out


def doc_number_tokens(line):
    line = re.sub(r"XH0-\d+", u" ", line)
    line = re.sub(r"X[HD]0", u" ", line)
    return WG.doc_number_tokens(line)


def doc_number_problems(c):
    allowed = set(STRUCTURAL) | derived_numbers(c)
    out = []
    for i, ln in enumerate(c.doc.splitlines(), 1):
        for tok in doc_number_tokens(re.sub(r"^\d+\. ", u"", ln)):
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
    for p in (u"期の表の形を変えれば作れるかは測っていない", u"外した側は 2 通り在る", u"字だけからは見分けられない", u"増えた分は紙 2"):
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
    u"""文書が書く 3 つの commit が実の履歴と合う: 封は 97eff9a2 が足し(1 commit)・script と封の門と封への追記は 2761b2dd が足し・記録は 32e6c6a4 が足した(どれも 1 commit)。"""
    out = []
    for rel, want in ((SEAL_REL, [SEAL_COMMIT_SHORT]), (SCRIPT_REL, [SCRIPT_COMMIT_SHORT]), (SEAL_GATE_REL, [SCRIPT_COMMIT_SHORT]), (ADDENDUM_REL, [SCRIPT_COMMIT_SHORT]), (RECORD_REL, [RECORD_COMMIT_SHORT])):
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
    for rel in (SCRIPT_REL, SEAL_GATE_REL, ADDENDUM_REL):
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
M5  封への追記の sha256 の写しを違う値に                                                 -> sha
M6  便 XS0 の記録の sha256 の写しを違う値に                                              -> sha
M7  記録の「script の決めの字」の 1 つを消す                                             -> sha
M8  書類 10 の 1 つずつ書く fact を 1 増やす(群は直さない)                                -> recount
M9  本番の例外の cell の数を 1 減らす(書類ごとは直さない)                                 -> recount
M10 本番の文脈が同じ書類の数を 1 減らす(書類ごとは直さない)                               -> recount
M11 材料の書類の本数 67 → 68                                                             -> recount
M12 書類 10 の紙の欄の数を 1 増やす(項は直さない)                                         -> recount
M13 本番の紙の欄の項「例外の cell」を 1 増やす(和は直さない)                              -> recount
M14 書類 10 の混ぜ物(期)の「効いた」を偽に(群は直さない)                                  -> recount
M15 全部の塊の規則が当てた fact を 1 減らす                                               -> recount
M16 本番の紙の欄の比の % を 42.2 → 42.3                                                  -> recount
M17 書類 10 の例外(元は fact が無いのに規則が付ける)を 1 増やす(項・群は直さない)           -> recount
M18 書類 10 の規則が当てた fact を 1 減らす(群は直さない)                                 -> recount
M19 書類 10 の 1 つずつ書く fact の在る cell を 1 増やす(群は直さない)                      -> recount
M20 断った 1 本の「断った段」を「属性を作る」に(群は直さない)                              -> recount
M21 断った 1 本の「文脈が同じ」を真に                                                    -> recount
M22 タクソノミが違う書類の「全部同じ」を真に(導き方に反する)                                -> recount
M23 書類 10 の「例外の cell の中の fact の始まりと終わり」を 2 増やす(群は直さない)          -> recount
M24 書類 10 の member の表の欄を 1 増やす(群は直さない)                                    -> recount
M25 全部の塊の元の文脈の定義の数を 1 減らす                                               -> recount
M26 予測の欄 XH0-2 の分母を 1 増やす                                                      -> recount
M27 本番の「決めの在る cell の外に在る…」を 1 にする(書類ごとは直さない)                    -> recount
M28 記録に docid の欄を足す                                                              -> clean
M29 記録に EDINET コードの形の字を足す                                                    -> clean
M30 封の写しから XH0-1 の境の字を消す                                                     -> bound
M31 封の写しから自己点検の「断った書類が 10 本以上」を消す                                  -> bound
M32 封の写しから §6 の「XH0-3 と XH0-5 が当たりなら…」を消す                              -> bound
M33 文書の XH0-1 の判定「当たり」を「外れ(下)」に                                          -> verdict
M34 文書の XH0-8 の判定「当たり(期は弱い証拠)」を「当たり」に                              -> verdict
M35 文書の件数の行 当たり 10・外れ 0 → 当たり 9・外れ 1                                    -> verdict
M36 頭の「判定した 10 本は当たり 10・外れ 0」を 当たり 9・外れ 1 に                          -> verdict
M37 文書の XH0-9 のセル 186606/442652(42.2%) → (42.3%)                                    -> verdict・numbers
M38 文書の XH0-9 の予測の字「40% 以上 44% 未満」を「40% 以上 45% 未満」に                   -> verdict
M39 §5 の「人間に示す次の便の候補」の見出しの字を消す                                      -> verdict・phrases
M40 §5 の次の便の候補の「(iii) 未使用の書類で同じことをする」を替える                      -> verdict
M41 自己点検の「断った書類は 1(10 本より少ない)」を 2 に                                  -> verdict
M42 自己点検の「例外の cell は 0 でない」を「例外の cell は 0」に                          -> verdict
M43 自己点検の「断った 1 本だけ」を「断った 2 本だけ」に                                   -> verdict
M44 文書の XH0-4 のセル 1/62 → 2/62                                                      -> verdict
M45 文書の XH0-8 のセル「期 61/61」→「期 62/62」                                          -> verdict
M46 整合: 例外(元は fact が在るのに規則が違う)を 1500 増やして XH0-1 が 97% 未満              -> verdict
M47 整合: 例外(元は fact が無いのに規則が付ける)を 1000 増やして XH0-2 が 3% 超             -> verdict
M48 整合: 文脈が同じ書類を 8 本減らして XH0-3 が 54 本以下(外れ)                           -> verdict
M49 整合: 文脈と単位を作る命令が断った書類を 7 本にして XH0-4 が外れ                        -> verdict
M50 整合: 道具が読む fact が同じ書類を 8 本減らして XH0-5 が外れ                            -> verdict
M51 整合: 鳴り方が同じ書類を 8 本減らして XH0-6 が外れ                                      -> verdict
M52 整合: 元にだけ在る id の在る書類を 6 本にして XH0-7 が外れ                              -> verdict
M53 整合: 混ぜ物(置き場)が効かなかった書類を 1 本にして XH0-8 が外れ                        -> verdict
M54 整合: 混ぜ物(期)が効かなかった書類を 1 本にして XH0-8 が外れ                            -> verdict
M55 整合: 紙の欄を増やして XH0-9 が 44% 以上(上に外れ)                                     -> verdict
M56 整合: 紙の欄を減らして XH0-9 が 40% 未満(下に外れ)                                     -> verdict
M57 整合: 包みが元と byte で同じ書類を 1 本にして XH0-10 が外れ                              -> verdict
M58 整合: 決めの在る cell の外の fact を 1 つにして自己点検が発火                             -> verdict
M59 整合: 置き場が同じでない書類を 1 本にして自己点検が発火                                  -> verdict
M60 整合: 全部の書類の例外の cell を 0 にして自己点検が発火                                  -> verdict
M61 整合: 文脈が同じなのに道具が読む fact が違う書類を 1 本にして自己点検が発火              -> verdict
M62 整合: 混ぜ物(期)を作れなかった書類(断っていない)を 1 本にして自己点検が発火            -> verdict
M63 文書 §2 の本番の fact 63236 を 63237 に(表の行)                                        -> frag・numbers
M64 文書 §2 の紙の欄の数 186606 を 186607 に                                               -> frag・numbers
M65 文書の項の表の「要素の線 × 4 | 93644」を 93645 に                                       -> frag・numbers
M66 文書の「例外の cell | 1132 | 61」を 1133 に                                            -> frag・numbers
M67 文書に 9999 の言い切りを足す                                                          -> numbers
M68 文書の「タクソノミが同じ 65 本」を 66 本に                                             -> frag・numbers (外れ: numbers は黙った)
M69 頭の「合わせて 1132」を 1131 に                                                       -> frag・numbers
M70 頭の「(7 本の書類」を「(8 本の書類」に                                                  -> frag
M71 §5 の「62 本のうち 61 本で確かめた」を「62 本のうち 62 本で確かめた」に                    -> frag
M72 §2 の「空の fact の形 | 62」を 61 に                                                    -> frag・numbers (外れ: numbers は黙った)
M73 §3 の「cell が 612」を 613 に                                                         -> sec3・numbers
M74 §3 に 3 桁の数を足した行                                                              -> sec3
M75 §3 の「99.1%」を 99.2% に                                                             -> sec3・numbers
M76 §3 の「42.2% に増えた」を 42.3% に                                                    -> sec3・numbers
M77 §3 の「期の表の形を変えれば作れるかは測っていない」を消す                              -> sec3
M78 便 XS0 の記録の写しの本番の 1 つずつ書く fact を 1 増やす                                -> sanity
M79 便 XS0 の記録の写しの本番の紙の欄の数を 1 減らす                                         -> sanity
M80 封への追記の写しの §2 の 12 項の 1 つを消す                                             -> sanity
M81 文書に「XBRL を作れる。」を引用の外で足す                                              -> affirm
M82 文書に「専用の道具が要らない。」を足す                                                 -> affirm
M83 文書に「紙は人が書ける。」を足す                                                       -> affirm
M84 文書に「人が紙を書ける。」を足す                                                       -> affirm
M85 引用の行から「言えない」「読まない」を全部消す                                          -> affirm
M86 §5 の「言えないこと」を消す                                                           -> phrases
M87 §4 の「実装で決めた所」を消す                                                          -> phrases
M88 頭の「この便からは言えない」を消す                                                     -> head
M89 頭の「先に負けと限界を書く」を消す                                                     -> head
M90 頭の「未使用ではない」を消す                                                           -> head
M91 頭の「LLM の席は呼んでいない」を消す                                                   -> head
M92 頭の「紙も紙 2 も答え(元の書類)から作っている」を消す                                   -> head
M93 頭の「XH0-8(混ぜ物・期)は弱い証拠」を消す                                              -> head
M94 頭の「読めていない数が 1 つ在る」を消す                                                -> head
M95 文書に「保証」を足す                                                                  -> forbidden
M96 文書に docID の形を足す                                                               -> forbidden
M97 文書の commit の字 32e6c6a4 を 1 字替える                                              -> commits
M98 文書に知らない commit の字を足す                                                       -> commits
M99 自己点検の行の「封の字のままなら当たる」を「当たらない」に戻す                          -> verdict
M100 自己点検の行の「5 つは当たらない」を「6 つは当たらない」(発火 0 と書く)に              -> verdict
M101 頭の「封の字のままなら 1 つ発火している」の行を消す                                   -> verdict・head
M102 頭の発火の数 1 を 0 に                                                              -> verdict
M103 自己点検の行の 2026-11-22 追記の字を消す                                             -> verdict
M104 整合: 断った書類を 10 本にして発火の組を変える                                         -> verdict
(自己点検の読みを封の字のままに直した後の追加。「作れなかったのは断った書類だけなら発火しない」という緩めは外した)

(1 回目の実行で外れた予測。門は直していない(予測の側を直した)。記録: M68・M72 は予測 frag・numbers だったが numbers が黙った)
- M68(タクソノミが同じ 66 本)・M72(空の fact の形 61): numbers が黙った。66 は 67 本の塊の「道具が読む fact が同じ」の数、61 は本番の文脈が同じ書類の数として記録に在るので、文書の数の門は
  記録に在る数を通す。書き換えは frag が記録から組んだ字と照らして赤にする。
"""


def doc_at(rec, k):
    return rec[u"書類"][DEV_COUNT + k]


def rebuild(rec):
    u"""書類ごとの数はそのままに、3 つの塊の集計と予測の欄を作り直す(整合した変更)。"""
    for g in GROUPS:
        rec[AGG][g] = totals(docs_of(rec, g))
    rec[PRED_KEY] = pred_expected(rec)


def add_paper(d, delta):
    d[u"紙の欄の数"] += delta


def shift_place(d, db=0, da=0):
    u"""例外の cell を整合して変える: db = 「元は fact が在るのに規則が違う」の増え(当てた fact がその分減る)・da = 「元は fact が無いのに規則が付ける」の増え。"""
    d[K_B] += db
    d[K_A] += da
    d[K_HIT] -= db
    it = d[u"紙の欄の数(項ごと)"]
    it[CELL_KEYS[11]] += db + da
    it[CELL_KEYS[12]] += 2 * db
    add_paper(d, db + da + 2 * db)


def m_place_low(c):
    shift_place(doc_at(c.rec, 4), db=1500)
    rebuild(c.rec)


def m_exc_high(c):
    shift_place(doc_at(c.rec, 4), da=1000)
    rebuild(c.rec)


def decline_ctx(d):
    d[u"断った"] = True
    d[u"断った段"] = ST_CTX
    d[u"断った理由"] = u"x"
    for k in (u"文脈と単位を作れた", u"文脈が同じ", u"単位が同じ", u"属性を作れた", u"表 F が同じ", u"組めた", u"2 回組んで同じ", u"タクソノミが同じ", u"fact が同じ", u"鳴り方が同じ", u"全部同じ", u"定義の並びまで同じ"):
        d[k] = False
    d[u"混ぜ物(期)"] = collections.OrderedDict([(u"作れた", False), (u"効いた", False)])
    for k in CTX_NULL_KEYS:
        d[k] = None
    d[u"attrs が違う fact の数"] = None


def live_docs(rec, n):
    return [d for d in docs_of(rec, G_PROD) if not d[u"断った"]][:n]


def m_ctx_low(c):
    for d in live_docs(c.rec, 8):
        d[u"中身が違う id の数"] = 1
        d[u"文脈が同じ"] = False
        d[u"単位が同じ"] = False
    rebuild(c.rec)


def m_decline7(c):
    for d in live_docs(c.rec, 6):
        decline_ctx(d)
    rebuild(c.rec)


def m_tool_low(c):
    for d in live_docs(c.rec, 8):
        d[u"fact が同じ"] = False
        d[u"全部同じ"] = False
    rebuild(c.rec)


def m_ring_low(c):
    for d in live_docs(c.rec, 8):
        d[u"鳴り方が同じ"] = False
    rebuild(c.rec)


def m_orphan(c):
    for d in live_docs(c.rec, 6):
        d[u"元にだけ在る id の数"] = 1
        d[u"文脈が同じ"] = False
        d[u"単位が同じ"] = False
    rebuild(c.rec)


def m_mix_place_low(c):
    doc_at(c.rec, 0)[u"混ぜ物(置き場)"][u"効いた"] = False
    rebuild(c.rec)


def m_mix_period_low(c):
    live_docs(c.rec, 1)[0][u"混ぜ物(期)"][u"効いた"] = False
    rebuild(c.rec)


def scale_lines(c, factor):
    for d in c.rec[u"書類"]:
        it = d[u"紙の欄の数(項ごと)"]
        it[CELL_KEYS[3]] = int(it[CELL_KEYS[3]] * factor)
        d[u"紙の欄の数"] = sum(it.values())
    rebuild(c.rec)


def m_cells_high(c):
    scale_lines(c, 1.1)


def m_cells_low(c):
    scale_lines(c, 0.8)


def m_byte_one(c):
    doc_at(c.rec, 0)[u"包みが元と byte で同じ"] = True
    rebuild(c.rec)


def m_outside(c):
    d = doc_at(c.rec, 0)
    d[K_OUT] += 1
    d[K_HIT] -= 1
    it = d[u"紙の欄の数(項ごと)"]
    it[CELL_KEYS[11]] += 1
    it[CELL_KEYS[12]] += 2
    add_paper(d, 3)
    rebuild(c.rec)


def m_place_not_same(c):
    doc_at(c.rec, 0)[u"置き場が同じ"] = False
    rebuild(c.rec)


def m_all_zero_exc(c):
    for d in c.rec[u"書類"]:
        it = d[u"紙の欄の数(項ごと)"]
        it[CELL_KEYS[11]] = 0
        it[CELL_KEYS[12]] = 0
        d[K_A] = d[K_B] = d[K_INNER] = d[K_OUT] = 0
        d[K_HIT] = d[K_NONHAND]
        d[u"紙の欄の数"] = sum(it.values())
    rebuild(c.rec)


def m_tool_diff_one(c):
    d = doc_at(c.rec, 0)
    d[u"fact が同じ"] = False
    d[u"全部同じ"] = False
    rebuild(c.rec)


def m_decline10(c):
    for d in live_docs(c.rec, 9):
        decline_ctx(d)
    rebuild(c.rec)


def m_mix_unmade(c):
    d = live_docs(c.rec, 1)[0]
    d[u"混ぜ物(期)"] = collections.OrderedDict([(u"作れた", False), (u"効いた", False)])
    rebuild(c.rec)


def m_taxo_all_same(c):
    for d in c.rec[u"書類"]:
        if not d[u"タクソノミが同じ"]:
            d[u"全部同じ"] = True
            break


def m_declined_stage(c):
    for d in c.rec[u"書類"]:
        if d[u"断った"]:
            d[u"断った段"] = ST_ATTR


def m_declined_ctx_same(c):
    for d in c.rec[u"書類"]:
        if d[u"断った"]:
            d[u"文脈が同じ"] = True


def m_drop_quote_negation(c):
    lines = []
    for ln in c.doc.splitlines():
        if QUOTED_CLAIM.search(ln):
            for w in (u"言えないこと", u"言えない", u"読まない", u"示していない"):
                ln = ln.replace(w, u"X")
        lines.append(ln)
    c.doc = u"\n".join(lines)


def m_drop_addendum_item(c):
    lines = c.add.splitlines()
    i = [k for k, ln in enumerate(lines) if ln.startswith(u"12. ")][0]
    del lines[i]
    c.add = u"\n".join(lines)


def add_sec3(c, text):
    rep(c, u"## §4 ", text + u"\n\n## §4 ")


def m_dec_reason_doc(c):
    rep(c, u"文脈と単位を作る命令は、62 本のうち 1 本を断った", u"文脈と単位を作る命令は、62 本のうち 2 本を断った")


def m_xs0_hand(c):
    c.xs0[AGG][G_PROD][u"1 つずつ書く fact の数"] += 1


def m_xs0_cells(c):
    c.xs0[AGG][G_PROD][u"紙の欄の数"] -= 1


def m_drop_decision(c):
    c.rec[u"材料"][u"script の決めの字"] = c.rec[u"材料"][u"script の決めの字"][1:]


MUTATIONS = (
    (u"M1 記録の sha256 の写しを違う値に", lambda c: c.shas.__setitem__(RECORD_REL, u"0" * 64), (u"sha",)),
    (u"M2 記録の script の sha256 を 1 字替える", lambda c: c.rec.__setitem__(u"この script の sha256", u"f" + c.rec[u"この script の sha256"][1:]), (u"sha",)),
    (u"M3 記録の限界の欄の 1 行を消す", lambda c: c.rec.__setitem__(u"限界", c.rec[u"限界"][1:]), (u"sha",)),
    (u"M4 記録の封の commit の欄を 1 字替える", lambda c: c.rec.__setitem__(u"封の commit", u"0" + c.rec[u"封の commit"][1:]), (u"sha",)),
    (u"M5 封への追記の sha256 の写しを違う値に", lambda c: c.shas.__setitem__(ADDENDUM_REL, u"0" * 64), (u"sha",)),
    (u"M6 便 XS0 の記録の sha256 の写しを違う値に", lambda c: c.shas.__setitem__(XS0_RECORD_REL, u"0" * 64), (u"sha",)),
    (u"M7 記録の「script の決めの字」の 1 つを消す", m_drop_decision, (u"sha",)),
    (u"M8 書類 10 の 1 つずつ書く fact を 1 増やす", lambda c: doc_at(c.rec, 4).__setitem__(u"1 つずつ書く fact の数", doc_at(c.rec, 4)[u"1 つずつ書く fact の数"] + 1), (u"recount",)),
    (u"M9 本番の例外の cell の数を 1 減らす", lambda c: c.rec[AGG][G_PROD].__setitem__(K_EXC, c.rec[AGG][G_PROD][K_EXC] - 1), (u"recount",)),
    (u"M10 本番の文脈が同じ書類の数を 1 減らす", lambda c: c.rec[AGG][G_PROD].__setitem__(u"文脈が同じ書類の数", c.rec[AGG][G_PROD][u"文脈が同じ書類の数"] - 1), (u"recount",)),
    (u"M11 材料の書類の本数を 68 に", lambda c: c.rec[u"材料"].__setitem__(u"書類の本数", 68), (u"recount",)),
    (u"M12 書類 10 の紙の欄の数を 1 増やす", lambda c: doc_at(c.rec, 4).__setitem__(u"紙の欄の数", doc_at(c.rec, 4)[u"紙の欄の数"] + 1), (u"recount",)),
    (u"M13 本番の紙の欄の項「例外の cell」を 1 増やす", lambda c: c.rec[AGG][G_PROD][u"紙の欄の数(項ごと)"].__setitem__(CELL_KEYS[11], c.rec[AGG][G_PROD][u"紙の欄の数(項ごと)"][CELL_KEYS[11]] + 1), (u"recount",)),
    (u"M14 書類 10 の混ぜ物(期)の「効いた」を偽に", lambda c: live_docs(c.rec, 5)[4][u"混ぜ物(期)"].__setitem__(u"効いた", False), (u"recount",)),
    (u"M15 全部の塊の規則が当てた fact を 1 減らす", lambda c: c.rec[AGG][G_ALL].__setitem__(K_HIT, c.rec[AGG][G_ALL][K_HIT] - 1), (u"recount",)),
    (u"M16 本番の紙の欄の比の % を 42.3 に", lambda c: c.rec[AGG][G_PROD][u"紙の欄の比"].__setitem__(u"%", 42.3), (u"recount",)),
    (u"M17 書類 10 の例外(元は fact が無い)を 1 増やす", lambda c: doc_at(c.rec, 4).__setitem__(K_A, doc_at(c.rec, 4)[K_A] + 1), (u"recount",)),
    (u"M18 書類 10 の規則が当てた fact を 1 減らす", lambda c: doc_at(c.rec, 4).__setitem__(K_HIT, doc_at(c.rec, 4)[K_HIT] - 1), (u"recount",)),
    (u"M19 書類 10 の 1 つずつ書く fact の在る cell を 1 増やす", lambda c: doc_at(c.rec, 4).__setitem__(K_HANDCELL, doc_at(c.rec, 4)[K_HANDCELL] + 1), (u"recount",)),
    (u"M20 断った 1 本の断った段を「属性を作る」に", m_declined_stage, (u"recount",)),
    (u"M21 断った 1 本の「文脈が同じ」を真に", m_declined_ctx_same, (u"recount",)),
    (u"M22 タクソノミが違う書類の「全部同じ」を真に", m_taxo_all_same, (u"recount",)),
    (u"M23 書類 10 の例外の cell の中の fact の始まりと終わりを 2 増やす",
     lambda c: doc_at(c.rec, 4)[u"紙の欄の数(項ごと)"].__setitem__(CELL_KEYS[12], doc_at(c.rec, 4)[u"紙の欄の数(項ごと)"][CELL_KEYS[12]] + 2), (u"recount",)),
    (u"M24 書類 10 の member の表の欄を 1 増やす", lambda c: doc_at(c.rec, 4)[u"紙の欄の数(項ごと)"].__setitem__(CELL_KEYS[15], doc_at(c.rec, 4)[u"紙の欄の数(項ごと)"][CELL_KEYS[15]] + 1), (u"recount",)),
    (u"M25 全部の塊の元の文脈の定義の数を 1 減らす", lambda c: c.rec[AGG][G_ALL].__setitem__(u"元の文脈の定義の数", c.rec[AGG][G_ALL][u"元の文脈の定義の数"] - 1), (u"recount",)),
    (u"M26 予測の欄 XH0-2 の分母を 1 増やす", lambda c: c.rec[PRED_KEY][PK[1]].__setitem__(u"分母", c.rec[PRED_KEY][PK[1]][u"分母"] + 1), (u"recount",)),
    (u"M27 本番の「決めの在る cell の外に在る…」を 1 に", lambda c: c.rec[AGG][G_PROD].__setitem__(K_OUT, 1), (u"recount",)),
    (u"M28 記録に docid の欄を足す", lambda c: c.rec[u"書類"][0].__setitem__(u"docid", u"x"), (u"clean",)),
    (u"M29 記録に EDINET コードの形の字を足す", lambda c: c.rec.__setitem__(u"step", c.rec[u"step"] + u" E12345"), (u"clean",)),
    (u"M30 封の写しから XH0-1 の境の字を消す", lambda c: rep(c, u"置き場の規則が当てたものは 97% 以上", u"X", attr="seal"), (u"bound",)),
    (u"M31 封の写しから「断った書類が 10 本以上」を消す", lambda c: rep(c, u"断った書類が 10 本以上", u"X", attr="seal"), (u"bound",)),
    (u"M32 封の写しから §6 の決めの字を消す", lambda c: rep(c, u"XH0-3 と XH0-5 が当たりなら、次の便の候補を人間に示す", u"X", attr="seal"), (u"bound",)),
    (u"M33 XH0-1 の判定を外れ(下)に", lambda c: rep(c, u"| 59595/60165(99.1%) | 当たり |", u"| 59595/60165(99.1%) | 外れ(下) |"), (u"verdict",)),
    (u"M34 XH0-8 の判定の但し書きを消す", lambda c: rep(c, u"当たり(期は弱い証拠) |", u"当たり |"), (u"verdict",)),
    (u"M35 件数の行を当たり 9・外れ 1 に", lambda c: rep(c, u"- 当たり 10・外れ 0。", u"- 当たり 9・外れ 1。"), (u"verdict",)),
    (u"M36 頭の件数を当たり 9・外れ 1 に", lambda c: rep(c, u"判定した 10 本は当たり 10・外れ 0。", u"判定した 10 本は当たり 9・外れ 1。"), (u"verdict",)),
    (u"M37 XH0-9 のセルの 42.2% を 42.3% に", lambda c: rep(c, u"186606/442652(42.2%)", u"186606/442652(42.3%)"), (u"verdict", u"numbers")),
    (u"M38 XH0-9 の予測の字を 45% 未満に", lambda c: rep(c, u"40% 以上 44% 未満", u"40% 以上 45% 未満"), (u"verdict",)),
    (u"M39 §5 の次の便の候補の見出しの字を消す", lambda c: rep(c, u"人間に示す次の便の候補(封 §6。XH0-3 と XH0-5 が当たりなので示す)", u"X"), (u"verdict", u"phrases")),
    (u"M40 §5 の次の便の候補の (iii) を替える", lambda c: rep(c, u"(iii) 未使用の書類で同じことをする", u"(iii) X"), (u"verdict",)),
    (u"M41 自己点検の「断った書類は 1(10 本より少ない)」を 2 に", lambda c: rep(c, u"断った書類は 1(10 本より少ない)", u"断った書類は 2(10 本より少ない)"), (u"verdict",)),
    (u"M42 自己点検の「例外の cell は 0 でない」を「例外の cell は 0」に", lambda c: rep(c, u"例外の cell は 0 でない", u"例外の cell は 0"), (u"verdict",)),
    (u"M43 自己点検の「封の字のままなら当たる: 1 本」を 2 本に", lambda c: rep(c, u"封の字のままなら当たる: 1 本", u"封の字のままなら当たる: 2 本"), (u"verdict",)),
    (u"M44 XH0-4 のセルの 1/62 を 2/62 に", lambda c: rep(c, u"| 1/62 | 当たり |", u"| 2/62 | 当たり |"), (u"verdict",)),
    (u"M45 XH0-8 のセルの「期 61/61」を「期 62/62」に", lambda c: rep(c, u"期 61/61・置き場 62/62", u"期 62/62・置き場 62/62"), (u"verdict",)),
    (u"M46 整合: 例外(元は fact が在る)を増やして XH0-1 が外れ", m_place_low, (u"verdict",)),
    (u"M47 整合: 例外(元は fact が無い)を増やして XH0-2 が外れ", m_exc_high, (u"verdict",)),
    (u"M48 整合: 文脈が同じ書類を 8 本減らす", m_ctx_low, (u"verdict",)),
    (u"M49 整合: 文脈と単位を作る命令が断った書類を 7 本に", m_decline7, (u"verdict",)),
    (u"M50 整合: 道具が読む fact が同じ書類を 8 本減らす", m_tool_low, (u"verdict",)),
    (u"M51 整合: 鳴り方が同じ書類を 8 本減らす", m_ring_low, (u"verdict",)),
    (u"M52 整合: 元にだけ在る id の在る書類を 6 本に", m_orphan, (u"verdict",)),
    (u"M53 整合: 混ぜ物(置き場)が効かなかった書類を 1 本に", m_mix_place_low, (u"verdict",)),
    (u"M54 整合: 混ぜ物(期)が効かなかった書類を 1 本に", m_mix_period_low, (u"verdict",)),
    (u"M55 整合: 紙の欄を増やして XH0-9 が 44% 以上", m_cells_high, (u"verdict",)),
    (u"M56 整合: 紙の欄を減らして XH0-9 が 40% 未満", m_cells_low, (u"verdict",)),
    (u"M57 整合: 包みが元と byte で同じ書類を 1 本に", m_byte_one, (u"verdict",)),
    (u"M58 整合: 決めの在る cell の外の fact を 1 つに", m_outside, (u"verdict",)),
    (u"M59 整合: 置き場が同じでない書類を 1 本に", m_place_not_same, (u"verdict",)),
    (u"M60 整合: 全部の書類の例外の cell を 0 に", m_all_zero_exc, (u"verdict",)),
    (u"M61 整合: 文脈が同じなのに道具が読む fact が違う書類を 1 本に", m_tool_diff_one, (u"verdict",)),
    (u"M62 整合: 混ぜ物(期)を作れなかった書類(断っていない)を 1 本に", m_mix_unmade, (u"verdict",)),
    (u"M63 §2 の本番の fact を 63237 に", lambda c: rep(c, u"| fact | 63236 |", u"| fact | 63237 |"), (u"frag", u"numbers")),
    (u"M64 §2 の紙の欄の数 186606 を 186607 に", lambda c: rep(c, u"| 紙の欄の数 | 186606 |", u"| 紙の欄の数 | 186607 |"), (u"frag", u"numbers")),
    (u"M65 項の表の「要素の線 × 4」の 93644 を 93645 に", lambda c: rep(c, u"| 要素の線 × 4 | 93644 |", u"| 要素の線 × 4 | 93645 |"), (u"frag", u"numbers")),
    (u"M66 「例外の cell | 1132 | 61」を 1133 に", lambda c: rep(c, u"| 例外の cell | 1132 | 61 |", u"| 例外の cell | 1133 | 61 |"), (u"frag", u"numbers")),
    (u"M67 文書に 9999 の言い切りを足す", lambda c: add_doc(c, u"fact の行は 9999 本に近い。"), (u"numbers",)),
    (u"M68 タクソノミが同じ 65 本を 66 本に", lambda c: rep(c, u"タクソノミが同じ 65 本", u"タクソノミが同じ 66 本"), (u"frag",)),
    (u"M69 頭の「合わせて 1132」を 1131 に", lambda c: rep(c, u"(合わせて 1132)", u"(合わせて 1131)"), (u"frag", u"numbers")),
    (u"M70 頭の「(7 本の書類」を 8 本に", lambda c: rep(c, u"(7 本の書類", u"(8 本の書類"), (u"frag",)),
    (u"M71 §5 の「62 本のうち 61 本で確かめた」を 62 本に", lambda c: rep(c, u"62 本のうち 61 本で確かめた", u"62 本のうち 62 本で確かめた"), (u"frag",)),
    (u"M72 §2 の「空の fact の形 | 62」を 61 に", lambda c: rep(c, u"| 空の fact の形 | 62 |", u"| 空の fact の形 | 61 |"), (u"frag",)),
    (u"M73 §3 の「cell が 612」を 613 に", lambda c: rep(c, u"cell が 612", u"cell が 613"), (u"sec3", u"numbers")),
    (u"M74 §3 に 3 桁の数を足した行", lambda c: add_sec3(c, u"- 別の確かめは 100 本。"), (u"sec3",)),
    (u"M75 §3 の 99.1% を 99.2% に", lambda c: rep(c, u"fact の 99.1% を当てた", u"fact の 99.2% を当てた"), (u"sec3", u"numbers")),
    (u"M76 §3 の「42.2% に増えた」を 42.3% に", lambda c: rep(c, u"42.2% に増えた", u"42.3% に増えた"), (u"sec3", u"numbers")),
    (u"M77 §3 の「期の表の形を変えれば作れるかは測っていない」を消す", lambda c: rep(c, u"期の表の形を変えれば作れるかは測っていない", u"X"), (u"sec3",)),
    (u"M78 便 XS0 の記録の写しの本番の 1 つずつ書く fact を 1 増やす", m_xs0_hand, (u"sanity",)),
    (u"M79 便 XS0 の記録の写しの本番の紙の欄の数を 1 減らす", m_xs0_cells, (u"sanity",)),
    (u"M80 封への追記の写しの §2 の 12 項の 1 つを消す", m_drop_addendum_item, (u"sanity",)),
    (u"M81 文書に「XBRL を作れる。」を引用の外で足す", lambda c: add_doc(c, u"XBRL を作れる。"), (u"affirm",)),
    (u"M82 文書に「専用の道具が要らない。」を足す", lambda c: add_doc(c, u"専用の道具が要らない。"), (u"affirm",)),
    (u"M83 文書に「紙は人が書ける。」を足す", lambda c: add_doc(c, u"紙は人が書ける。"), (u"affirm",)),
    (u"M84 文書に「人が紙を書ける。」を足す", lambda c: add_doc(c, u"人が紙を書ける。"), (u"affirm",)),
    (u"M85 引用の行から「言えない」「読まない」を消す", m_drop_quote_negation, (u"affirm",)),
    (u"M86 「言えないこと」を消す", lambda c: drop_all(c, u"言えないこと"), (u"phrases",)),
    (u"M87 §4 の「実装で決めた所」を消す", lambda c: drop_all(c, u"実装で決めた所"), (u"phrases",)),
    (u"M88 頭の「この便からは言えない」を消す", lambda c: rep(c, u"、この便からは言えない。**", u"、X。**", count=1), (u"head",)),
    (u"M89 頭の「先に負けと限界を書く」を消す", lambda c: drop_all(c, u"先に負けと限界を書く"), (u"head",)),
    (u"M90 頭の「未使用ではない」を消す", lambda c: rep(c, u"未使用ではない", u"X"), (u"head",)),
    (u"M91 頭の「LLM の席は呼んでいない」を消す", lambda c: rep(c, u"LLM の席は呼んでいない", u"X"), (u"head",)),
    (u"M92 頭の「紙も紙 2 も答え(元の書類)から作っている」を消す", lambda c: rep(c, u"紙も紙 2 も答え(元の書類)から作っている", u"X"), (u"head",)),
    (u"M93 頭の「XH0-8(混ぜ物・期)は弱い証拠」を消す", lambda c: rep(c, u"XH0-8(混ぜ物・期)は弱い証拠", u"X"), (u"head",)),
    (u"M94 頭の「読めていない数が 1 つ在る」を消す", lambda c: rep(c, u"読めていない数が 1 つ在る", u"X"), (u"head",)),
    (u"M95 文書に「保証」を足す", lambda c: add_doc(c, u"保証する。"), (u"forbidden",)),
    (u"M96 文書に docID の形を足す", lambda c: add_doc(c, u"書類 S100ABCD。"), (u"forbidden",)),
    (u"M97 文書の commit の字 32e6c6a4 を 1 字替える", lambda c: rep(c, u"32e6c6a4", u"32e6c6a5"), (u"commits",)),
    (u"M98 文書に知らない commit の字を足す", lambda c: add_doc(c, u"commit 1a2b3c4d。"), (u"commits",)),
    (u"M99 自己点検の行を「当たらない」に戻す", lambda c: rep(c, u"残る 1 つ「混ぜ物を作れなかった書類(期)が 1 本でも在る」は封の字のままなら当たる", u"残る 1 つ「混ぜ物を作れなかった書類(期)が 1 本でも在る」は当たらない"), (u"verdict",)),
    (u"M100 自己点検の行の「5 つは当たらない」を「6 つは当たらない」(発火 0)に", lambda c: rep(c, u"6 つのうち、5 つは当たらない", u"6 つのうち、6 つは当たらない"), (u"verdict",)),
    (u"M101 頭の「封の字のままなら 1 つ発火している」の行を消す", lambda c: rep(c, u"- 封 §4 の「先に自分の欠陥を疑う場合」は、封の字のままなら 1 つ発火している(混ぜ物(期)を作れなかった書類が 1 本。断った書類)。", u"- X"), (u"verdict", u"head")),
    (u"M102 頭の発火の数を 0 に", lambda c: rep(c, u"封の字のままなら 1 つ発火している", u"封の字のままなら 0 つ発火している"), (u"verdict",)),
    (u"M103 自己点検の行の追記の字を消す", lambda c: rep(c, u"初めの版は「当たらない」と書いていた。封の字のままの読みに直した", u"X"), (u"verdict",)),
    (u"M104 整合: 断った書類を 10 本にして「断った書類」も発火(組が変わる)", m_decline10, (u"verdict",)),
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
        self.assertEqual((63236, 3071, 60165, 59595, 71715, 2589, 1132, 612, 520, 62), (
            s[u"fact の数(紙を作れた書類)"], s[u"1 つずつ書く fact の数"], s[K_NONHAND], s[K_HIT], s[K_DECIDED], s[K_HANDCELL], s[K_EXC], s[K_A], s[K_B], s[u"例外の cell が在る書類の数"]))
        self.assertEqual((1, 1, 61, 61, 61, 61, 61, 60, 0, 0), (
            s[u"断った書類の数"], s[u"断った段ごとの数"][ST_CTX], s[u"文脈が同じ書類の数"], s[u"fact が同じ書類の数"], s[u"鳴り方が同じ書類の数"], s[u"組めた書類の数"], s[u"文脈と単位を作れた書類の数"],
            s[u"タクソノミが同じ書類の数"], s[u"元にだけ在る id が 1 つ以上在る書類の数"], s[u"包みが元と byte で同じ書類の数"]))
        self.assertEqual((186606, 442652), (s[u"紙の欄の数"], s[u"fact の数 × 7"]))
        self.assertEqual((50, 7, 69126), (s[K_INNER], len(inner_docs(self.c.rec)), s[K_DECIDED] - s[K_HANDCELL]))
        self.assertEqual(1, len(declined(self.c.rec)))

    def test_c_1_the_seal_has_the_bound_phrases(self):
        self.assertEqual([], bound_problems(self.c))

    def test_c_2_the_verdicts_are_decided_again_and_equal_the_document(self):
        self.assertEqual([], verdict_problems(self.c))
        j = judge(self.c.rec)
        self.assertEqual(10, sum(1 for v in j.values() if v[0]))
        self.assertEqual([], [k for k, v in j.items() if not v[0]])
        self.assertEqual(list(IDS), list(j))

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
        self.assertEqual([SEAL_REL, SCRIPT_REL, SEAL_GATE_REL, ADDENDUM_REL, RECORD_REL], list(BLOB_AT))
        self.assertEqual([SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT], list(BLOB_AT.values()))
        self.assertEqual((SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT), DOC_COMMITS)
        self.assertEqual((u"97eff9a2", u"2761b2dd", u"32e6c6a4"), DOC_COMMITS)

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
        self.assertGreaterEqual(len(MUTATIONS), 90)

    def test_g_2_the_unmutated_copy_is_green_on_every_check(self):
        c = Ctx().copy()
        for k, fn in CHECKS.items():
            self.assertEqual([], fn(c), k)

    def test_g_3_the_recount_stays_green_when_the_data_changes_consistently_but_the_verdict_does_not(self):
        base = Ctx()
        for fn, key in ((m_place_low, u"XH0-1"), (m_exc_high, u"XH0-2"), (m_ctx_low, u"XH0-3"), (m_decline7, u"XH0-4"), (m_tool_low, u"XH0-5"), (m_ring_low, u"XH0-6"),
                        (m_orphan, u"XH0-7"), (m_mix_place_low, u"XH0-8"), (m_mix_period_low, u"XH0-8"), (m_cells_high, u"XH0-9"), (m_cells_low, u"XH0-9"), (m_byte_one, u"XH0-10")):
            c = base.copy()
            fn(c)
            self.assertEqual([], recount_problems(c), fn.__name__)
            self.assertNotEqual([], verdict_problems(c), fn.__name__)
            self.assertNotEqual(judge(base.rec)[key][0], judge(c.rec)[key][0], (fn.__name__, key))

    def test_g_4_every_check_name_a_mutation_names_exists_and_every_check_has_a_mutation(self):
        named = set(k for _, _, ks in MUTATIONS for k in ks)
        self.assertEqual(set(CHECKS), named)

    def test_g_5_the_judgement_edges_at_the_seal_bounds(self):
        u"""境の 1 つ手前と境の数(丸める前の整数): 下限は含む(XH0-1 は 97%・XH0-9 は 40%・書類の本数は 55)・上限は XH0-9 が含まない(44%)・XH0-2 の 3% は含む・XH0-4・XH0-7 は 5 本まで・XH0-10 は 0 本。"""
        def with_(**kw):
            c = Ctx().copy()
            s = c.rec[AGG][G_PROD]
            s[K_NONHAND] = 1000
            s[K_HIT] = 990
            s[K_DECIDED] = 1100
            s[K_HANDCELL] = 100
            s[K_EXC] = 10
            s[u"文脈が同じ書類の数"] = 62
            s[u"断った段ごとの数"][ST_CTX] = 0
            s[u"fact が同じ書類の数"] = 62
            s[u"鳴り方が同じ書類の数"] = 62
            s[u"元にだけ在る id が 1 つ以上在る書類の数"] = 0
            s[u"混ぜ物(期)を作れた書類の数"] = 62
            s[u"混ぜ物(期)が効いた書類の数"] = 62
            s[u"混ぜ物(置き場)を作れた書類の数"] = 62
            s[u"混ぜ物(置き場)が効いた書類の数"] = 62
            s[u"fact の数 × 7"] = 7000
            s[u"紙の欄の数"] = 2900
            s[u"包みが元と byte で同じ書類の数"] = 0
            m = {u"hit": K_HIT, u"exc": K_EXC, u"ctx": u"文脈が同じ書類の数", u"tool": u"fact が同じ書類の数", u"ring": u"鳴り方が同じ書類の数", u"orphan": u"元にだけ在る id が 1 つ以上在る書類の数",
                 u"cells": u"紙の欄の数", u"byte": u"包みが元と byte で同じ書類の数", u"mixp": u"混ぜ物(期)が効いた書類の数", u"mixl": u"混ぜ物(置き場)が効いた書類の数"}
            for key, val in kw.items():
                if key == u"decl":
                    s[u"断った段ごとの数"][ST_CTX] = val
                else:
                    s[m[key]] = val
            return judge(c.rec)
        self.assertTrue(with_(hit=970)[u"XH0-1"][0])
        self.assertFalse(with_(hit=969)[u"XH0-1"][0])
        self.assertEqual(u"下", with_(hit=969)[u"XH0-1"][1])
        self.assertTrue(with_(exc=30)[u"XH0-2"][0])                 # 30/1000 = 3%(含む)
        self.assertFalse(with_(exc=31)[u"XH0-2"][0])
        self.assertEqual(u"上", with_(exc=31)[u"XH0-2"][1])
        self.assertTrue(with_(ctx=55)[u"XH0-3"][0])
        self.assertFalse(with_(ctx=54)[u"XH0-3"][0])
        self.assertTrue(with_(decl=5)[u"XH0-4"][0])
        self.assertFalse(with_(decl=6)[u"XH0-4"][0])
        self.assertTrue(with_(tool=55)[u"XH0-5"][0])
        self.assertFalse(with_(tool=54)[u"XH0-5"][0])
        self.assertTrue(with_(ring=55)[u"XH0-6"][0])
        self.assertFalse(with_(ring=54)[u"XH0-6"][0])
        self.assertTrue(with_(orphan=5)[u"XH0-7"][0])
        self.assertFalse(with_(orphan=6)[u"XH0-7"][0])
        self.assertTrue(with_(mixp=62, mixl=62)[u"XH0-8"][0])
        self.assertFalse(with_(mixp=61)[u"XH0-8"][0])
        self.assertFalse(with_(mixl=61)[u"XH0-8"][0])
        self.assertTrue(with_(cells=2800)[u"XH0-9"][0])             # 40%(含む)
        self.assertFalse(with_(cells=2799)[u"XH0-9"][0])
        self.assertEqual(u"下", with_(cells=2799)[u"XH0-9"][1])
        self.assertTrue(with_(cells=3079)[u"XH0-9"][0])
        self.assertFalse(with_(cells=3080)[u"XH0-9"][0])            # 44%(含まない)
        self.assertEqual(u"上", with_(cells=3080)[u"XH0-9"][1])
        self.assertTrue(with_(byte=0)[u"XH0-10"][0])
        self.assertFalse(with_(byte=1)[u"XH0-10"][0])

    def test_g_6_the_miss_direction_follows_the_bound(self):
        c = Ctx().copy()
        m_cells_high(c)
        self.assertEqual(u"上", judge(c.rec)[u"XH0-9"][1])
        c = Ctx().copy()
        m_cells_low(c)
        self.assertEqual(u"下", judge(c.rec)[u"XH0-9"][1])
        c = Ctx().copy()
        m_place_low(c)
        self.assertEqual(u"下", judge(c.rec)[u"XH0-1"][1])
        self.assertEqual(u"上", judge(c.rec)[u"XH0-2"][1])

    def test_g_7_the_self_suspicion_conditions_fire_for_each_cause(self):
        base = Ctx()
        # 実物: 封の字のままなら、混ぜ物(期)を作れなかった書類(断った 1 本)で 1 つだけ発火する
        self.assertEqual((False, False, False, False, False, True), fires(suspects(base)))
        self.assertEqual((0, 0, 0, 0, 1, 1, 0), suspects(base))
        for fn, idx in ((m_outside, 0), (m_place_not_same, 1), (m_all_zero_exc, 2), (m_tool_diff_one, 3), (m_mix_unmade, 5)):
            c = base.copy()
            fn(c)
            f = fires(suspects(c))
            self.assertTrue(f[idx], (fn.__name__, f))
            self.assertNotEqual([], verdict_problems(c), fn.__name__)
        # 断った書類が 10 本ちょうどで 5 番目が発火・9 本では発火しない
        for n, fire in ((10, True), (9, False)):
            c = base.copy()
            for d in live_docs(c.rec, n - 1):
                decline_ctx(d)
            rebuild(c.rec)
            self.assertEqual(n, suspects(c)[4])
            self.assertEqual(fire, fires(suspects(c))[4])
        # 断った書類だけなら発火しない、とは決めない: 作れなかった書類が断った書類でも発火は真
        self.assertTrue(suspect_fires(suspects(base)))


if __name__ == "__main__":
    unittest.main()
