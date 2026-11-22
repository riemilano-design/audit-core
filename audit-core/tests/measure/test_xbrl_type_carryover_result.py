# -*- coding: utf-8 -*-
u"""結果の門: 封 docs/XBRL_TYPE_CARRYOVER_SEAL_2026-11-22.md(1fc4c736)の結果の文書 docs/XBRL_TYPE_CARRYOVER_RESULT_2026-11-22.md(便 XK0)。

封の門 ``test_xbrl_type_carryover_seal.py`` の次の段。**追跡されている記録・script・封・封の門・便 XM0 の記録・結果の文書と git の履歴だけを読む**(書類の置き場は読まない・道具は呼ばない・通信しない・鍵は読まない)。
便 XA0 の結果の門 ``test_xbrl_sheet_wall_result.py`` の部品(読み・sha256・% の丸め・節の切り出し・数のトークン・禁止語・blob の道具)を読み込んで使う(門としては走らせない)。
検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表と、全部のセル・数・向きの語を 1 か所ずつ掃く ``SWEEPS`` で(木の file は変異させず、``Ctx`` の写しに当てる)。

 a script・記録・封・封の門の sha256(字で留める)・記録の script の sha256・封の commit の欄・記録の限界の欄・材料の欄が script の字と同じ
 b 記録の数え直し: 組ごとの数から、**script の関数を使わずに**、訓練の 3 組・判定の 60 組・全部の 63 組の集計の全部の欄・予測に要る数・旗 6 つを数え直す(組ごとの足し算の関係を含む)
 c 予測 XK0-1〜XK0-10 の当たり外れを、封 §4 の字から取った境(丸める前の整数で)と記録(判定の 60 組だけ)から決め直し、文書 §1 の表・件数と同じことを見る。
   封 §4 の「先に自分の欠陥を疑う」旗 6 つを決め直す(どれも立たない)・封 §6 の決め(XK0-1 と XK0-6 が両方当たりなら (i)(ii)(iii) を示す。どちらかが外れなら示さない)と文書 §5 が合う
 d 結果の文書の数: §1・§2・§4・§5 の数は全部、記録から導く(組ごとの率の最小・中央・最大・組の数・枠が無い行・値が違う組などは門の中で組ごとから導き直す)。
   記録の数と字から文書の §3 以外の全部の行を組み直し、文書と行ごとに照らす(``render_doc``)。主な主張の文は断片でも縛る。
   **§3 の読み(記録に欄の無い読み。出どころは記録の監査の席)は記録に縛らず**、見出し・「測った数ではない」・字で留めた数の並び・記録から導ける数(1147・4154・8・782・251 と、足して合う内訳)・
   §3 の主張が §3 の外に出ないこと・「測っていない」を縛る。§4 の数(30・277・265・12・8)は封の門の本数に縛り、3465 は記録に無い(監査の席の数)ので §4 の外に出ないことだけを見る
 e 文書の頭の負けと限界(封 §7 の 6 本・封 §6 の読み方)・禁止語・「XBRL を作れる」「専用の道具が要らない」「会社が型を埋められる」「入力が半分で済む」「誤りが無くなる」「EDINET の検査に通る」を肯定で書かない・docID と EDINET コードの形
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


WG = load_module("tests/measure/test_xbrl_sheet_wall_result.py", "xbrl_sheet_wall_result_gate_for_type_carryover_result_gate")                # 便 XA0 の結果の門の部品。門としては走らせない
SG = load_module("tests/measure/test_xbrl_type_carryover_seal.py", "xbrl_type_carryover_seal_gate_for_result_gate")                # 封の門の部品。門としては走らせない
PR = WG.PR
MS = SG.MS

read, sha_file, guard, pct, section = WG.read, WG.sha_file, WG.guard, WG.pct, WG.section
ints_in, doc_number_tokens = WG.ints_in, WG.doc_number_tokens

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
RECORD_REL = SG.RECORD_REL
XM0_RECORD_REL = SG.XM0_RECORD_REL
GATE_REL = "tests/measure/test_xbrl_type_carryover_result.py"
DOC_REL = "docs/XBRL_TYPE_CARRYOVER_RESULT_2026-11-22.md"
SCRIPT_COMMIT_SHORT = "aaeeb21c"                  # script と封の門を足した commit
RECORD_COMMIT_SHORT = "1392a222"                  # 記録を足した commit
BLOB_AT = collections.OrderedDict([
    (SEAL_REL, SEAL_COMMIT_SHORT), (SCRIPT_REL, SCRIPT_COMMIT_SHORT), (SEAL_GATE_REL, SCRIPT_COMMIT_SHORT), (RECORD_REL, RECORD_COMMIT_SHORT)])
HISTORY = collections.OrderedDict([
    (SEAL_REL, [SEAL_COMMIT_SHORT]), (SCRIPT_REL, [SCRIPT_COMMIT_SHORT]), (SEAL_GATE_REL, [SCRIPT_COMMIT_SHORT]), (RECORD_REL, [RECORD_COMMIT_SHORT])])
DOC_COMMITS = (SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT)

SHA_PIN = collections.OrderedDict([
    (RECORD_REL, "8201a143d798a1433b31a44037ff5ee2fa299e93088b427408acb83100c20583"),
    (SCRIPT_REL, "348dce845ae6e1095585091396e6903f6960bfd25497cd1933872edee12c8b0d"),
    (SEAL_GATE_REL, "ef11322afc9875b518bf802e366fdbb2e9a33f5b94f098fba5b1d39afac89ba5"),
    (SEAL_REL, "4aa99288b171893119caca1263739d244be0355f46b13701534b473a58c1b9af")])
XM0_RECORD_SHA = "28e83050cc01faf40ab5dd765c6d6bf670fcb18b94dabcc5c04bb322e7402110"      # 便 XM0 の記録(記録の材料の欄が字で持つ)
MATERIAL_PIN = collections.OrderedDict([
    (u"今年の側の書類の本数", 67), (u"今年の側の書類の file 名の並びの sha256", "f240150645a9b05a8d9bf5a9fe0ab89633ae338e42b8cc4d891dc04ca401e3f5"), (u"組の数", 63), (u"訓練の組の数", 3), (u"判定の組の数", 60),
    (u"除いた今年の書類の数", 4), (u"前の年の側の組の相手の file 名の並びの sha256", "8ddf19964316e3a88e72b0ea12c8a691f8a3520a317c3bb94cb7cd24b55a5cf6"), (u"便 XM0 の記録の sha256", XM0_RECORD_SHA)])

PAIR_COUNT, TRAIN_COUNT, JUDGE_COUNT, DOC67 = 63, 3, 60, 67
KN, KT = u"数", u"文"
KINDS = (u"科目", u"軸", u"member")
CLASS4 = (u"当期", u"前期", u"それより前", u"提出日")
OLD2 = (u"前期", u"それより前")
CONTENT4 = (u"全部同じ", u"値は同じで、単位・表示の位・精度のどれかが違う", u"値が違う", u"片方だけが 無い")
SIDES = (u"今年", u"前の年")
CONTENT_LABEL = dict(zip(CONTENT4, (CONTENT4[0], u"値は同じで、単位・表示の位・`decimals` のどれかが違う", CONTENT4[2], CONTENT4[3])))      # 文書の表の字(記録の欄の名の「精度」は文書では使えない語なので `decimals` と書く)
LETTERS = u"abcdefgh"
NOT_SUMMED = (u"番号", u"断った", u"断った年", u"断った理由", u"旗用の数")
K_DOCS = u"書類"
K_SUM = u"集計"
G_TRAIN, G_JUDGE, G_ALL = u"訓練の 3 組", u"判定の 60 組", u"全部の 63 組"
GROUPS = (G_TRAIN, G_JUDGE, G_ALL)
PRED_KEY = u"予測の判定に要る数(XK0-1〜XK0-10。判定の 60 組だけ。当たり・外れは結果の文書で)"
FLAG_KEY = u"先に自分の欠陥を疑う旗"
PK = (u"XK0-1 今年の科目の名のうち前の年の対応表に在る名 / 今年の科目の名", u"XK0-2 名が足りる数の行 / 今年の数の型の行", u"XK0-3 期の区分が前期かそれより前の数の行のうち、同じ行(日)が在る行 / その数の行",
      u"XK0-4 同じ行(数)のうち全部同じ / 同じ行(数)", u"XK0-5 今年の数の型の行のうち、同じ行で全部同じの行 / 今年の数の型の行", u"XK0-6 今年の数の型の行のうち、枠が在る行 / 今年の数の型の行",
      u"XK0-7 新しい科目の名のうち、接頭辞が _cor で終わる名 / 新しい科目の名", u"XK0-8 断った組 / 判定の組", u"XK0-9 科目の名の持ち越しが 95% 以上の組 / 判定の組",
      u"XK0-10 同じ行(数)に全部同じでない行が 1 つ以上在る組 / 判定の組")
IDS = tuple(u"XK0-%d" % i for i in range(1, 11))
DOC_KEYS = (u"番号", u"断った", u"断った年", u"断った理由", u"対象の fact", u"型の外の fact", u"型の行", u"対応表の名", u"名が足りる行", u"今年の行の期の区分", u"同じ行(日)", u"同じ行の中身(数)",
            u"枠が在る行", u"逆向き", u"旗用の数")
FLAG_KEYS = (u"旗 1 期の区分が当期の行に、同じ行(日)が 1 つでも在る(63 組)", u"旗 2 科目の名の持ち越しが判定の 60 組の全部で 100%", u"旗 3 同じ行(数)が判定の 60 組の合計で 0",
             u"旗 4 枠が在る行が名が足りる行より多い組が在る(63 組。数・文の別に比べる)", u"旗 5 断った組が 6 以上(判定の 60 組)", u"旗 6 便 XM0 の記録の型の行の数(数・文)と、今年の側の型の行の数が違う組が在る(63 組)")
NAME_FIELDS = (u"今年", u"持ち越せる", u"新しい", u"新しい・_cor で終わる", u"新しい・_cor で終わらない", u"消えた")
BACK_FIELDS = (u"前の年の行", u"同じ鍵(日)が今年に在る", u"同じ鍵(枠)が今年に在る", u"今年、要らなくなった枠")

# 封の字(封の門が script と照らし、ここでは文書が引く字の在り処を縛る)
CAND_KEYS = (u"型の外の理由のうち fact がいちばん多いものを型の拡張で入れる第 1 版", u"型から本文の表示の字と表も作る", u"去年の型と XBRL でない今年の資料から、今年の当期の行を埋める")
BOUND_SEAL_PHRASES = tuple(x for pair in SG.SEAL_BOUND_TEXT.values() for x in pair) + (
    u"**この便の数は「会社が型を埋められる」とは読まない。**", u"その値が正しいことは言わない", u"鍵が同じでも、指すものが同じとは限らない(番号つきの member は年で中身が入れ替わりうる。",
    u"「新しい名」は、会社が今年、新しく決める名の数の**下限ではない**", u"XK0-1 と XK0-6 が両方当たり → (i) ", u"どちらかが外れ → 次の便の候補は示さない。新しい名・枠の無い行の中身を読むのが先。",
    u"(0 USD。別の封が先)・(ii) ", u"(有料。別の封と、払う前の知らせが先)", u"番号 1・2・3 が訓練の 3 組、番号 4〜63 が判定の 60 組", u"司令塔の足し(申告)",
    u"**言えないこと**: 「XBRL を作れる」「専用の道具が要らない」「会社が型を埋められる」「入力が半分で済む」「誤りが無くなる」。",
    u"今年 1499・前の年にも在る 1460", u"今年 3337・使う名が全部前の年の対応表に在る 3274・同じ鍵が前の年の型に在る 1626(値・表示の位・精度が全部同じ 1585・値が違う 41") + CAND_KEYS
# 文書の頭の限界 6 本(封 §7)は、1 本ずつ文ごとに(「。」で切って)文書の頭の 1 つの行に在る。** は除いて照らす
HEAD_PHRASES = (u"先に負けと限界を書く", u"記録から 1 つずつ読んだもの", u"記録に欄の無い読み", u"判定の 60 組では高すぎた", u"頭の 3 組は持ち越しやすい側に寄っていた", u"どちらの年の型も対応表も答えから作った",
                u"「会社が型を埋められる」とは読まない", u"組による差が大きい", u"盲検ではない", u"費用は 0 USD", u"engine(`core/`・`adapters/`)は 0 行", u"外れは外れとして残す", u"日付つきの補足",
                u"封の字と実装が合わない所", u"旗の母集団", u"XK0-9 の数え方", u"「旗用の数」", u"司令塔が足した数え", u"封の門に穴が 1 つ残っている", u"「全部同じ」の行は", u"鍵が同じでも、指すものが同じとは限らない",
                u"「新しい名」は、会社が今年、新しく決める名の数の下限ではない", u"言えない")
PHRASES = (u"封も予測も結果を見てから書き換えていない", u"判定は丸める前の数でした", u"予測の判定には使わない", u"測った数ではない", u"記録から言えること", u"記録から言えないこと",
           u"続けるか・どの向きへ続けるかは人間が決める", u"XBRL は組んでいない", u"道具には掛けていない", u"独立監査 REVISE → 直し → GO", u"差は 0", u"次の便の候補は示さない")
MAIN_CLAIMS = (u"主の予測(XK0-1)を含む 6 本は外れ", u"判定の 60 組では高すぎた", u"どちらの年の型も対応表も答えから作った", u"持ち越しは上限", u"組による差が大きい", u"合計の率は 1 つの会社について言える数ではない",
               u"次の便の候補は示さない", u"直していない", u"当たり 4・外れ 6", u"外れは外れとして残す", u"「会社が型を埋められる」とは読まない", u"鍵が同じでも、指すものが同じとは限らない",
               u"名の数の下限ではない", u"「去年の型の値がそのまま今年の前期の欄に使える」だけを言う", u"この便は両方とも外れ", u"新しい名・枠の無い行の中身を読むのが先", u"6 つとも立たない", u"持ち越しは上限")
QUOTED = re.compile(u"「[^」]*(?:作れる|専用の道具が要らない|人が書ける|誤りが無くなる|会社が型を埋められる|入力が半分で済む|検査に通る)[^」]*」")
AFFIRM_WORDS = (u"作れる(?!か)", u"作れます", u"専用の道具が要らない", u"人が書ける(?!か)", u"誤りが無くなる", u"会社が型を埋められる(?!か)", u"入力が半分で済む", u"検査に通る(?!こと|か)")
FORBIDDEN_WORDS = tuple(WG.FORBIDDEN_WORDS)
STRUCTURAL = WG.STRUCTURAL
# 記録から組んだ値の外に在ってよい数(字で留める。封の境・文書の見出しや説明の数)。理由は 1 つずつ:
#   1 2 3 4 5 6 8 10 = 項の番号・「6 つ」「1 つ」「3 組」「4 本」・判定の件数が封の境の表と別に在る数(当たり 4・外れ 6 は記録から作り直す件数と照らす)
#   96 97 44 52 95 48 57 100 = 封 §4 の境(予測の字の要約) / 90 98 80 = 組の数え方の見出し(90%・98% 以上・80% 未満) / 60 63 67 = 組・書類の数の見出し(記録の欄と別に縛る) / 3 4 = 判定の境
RESIDUAL_OK = set([u"1", u"2", u"3", u"4", u"5", u"6", u"8", u"10", u"96", u"97", u"44", u"52", u"95", u"48", u"57", u"100", u"90", u"98", u"80", u"60", u"63", u"67"])
AUDIT_ONLY = (u"3465",)           # 記録に無い(記録の監査の席の数)。§4 の外に出てはならない
SEC3_LINES = (
    (u"前期かそれより前の数の行で同じ行が無い", (u"1147", u"901", u"78", u"154", u"14")),
    (u"枠が無い数の行 4154:", (u"4154", u"2252", u"774", u"1128", u"1128")),
    (u"「値は同じで、単位・表示の位・`decimals` のどれかが違う」", (u"8", u"2")),
    (u"「値が違う」782 行は", (u"782", u"3")),
    (u"で終わらない新しい科目の名 251 は", (u"251", u"1")),
)
SEC3_ONLY_PHRASES = (u"科目の名が前の年に無い", u"次元の名が前の年に無い", u"同じ対象の行が前の年に無い", u"同じ行の別の日だけ在る", u"期の名が違う", u"同じ位の別の数", u"符号が逆",
                     u"1 種類の接頭辞", u"鍵の取り違え", u"表示の位・`decimals` の差だけ")      # §3 の外に主張として出てはならない字
SEC3_PHRASES = (u"記録の監査の席が実物を読んで分けた数", u"記録にも門にも縛っていない", u"見つからなかった", u"封の枠の決め(期の名で比べる)どおり", u"2 つの組の表示の位・`decimals` の差だけ",
                u"同じ位の別の数が大半", u"会社が決めた名ではない", u"追加か改名かは見ていない", u"測った数ではない",
                u"記録は「なぜ持ち越せなかったか」を分けていない", u"科目の名が前の年に無い 901・次元の名が前の年に無い 78・名は在るが同じ対象の行が前の年に無い 154・同じ行の別の日だけ在る 14",
                u"科目の名が前の年に無い 2252・名は在るが枠が無い 774・同じ行(日)は在るが期の名が違う 1128", u"今年の前期の日が前の年の書類では当期の枠に当たるため", u"同じ位の別の数が大半で、符号が逆のものが 3 行在った",
                u"全部が標準の側の 1 種類の接頭辞の名だった")      # §3 の中の向きの語・言い切りの形を決める言い回し(§3 の文の削除・向きの語の反転の掃きが黙らないように留める)


# ======================================================================================================
class Ctx(object):
    u"""検査が見る写し。変異はこの写しを変える(木の file は変えない)。"""

    def __init__(self):
        self.rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        self.xm0 = json.loads(read(XM0_RECORD_REL), object_pairs_hook=collections.OrderedDict)
        self.doc = read(DOC_REL)
        self.seal = read(SEAL_REL)
        self.shas = collections.OrderedDict((rel, sha_file(rel)) for rel in SHA_PIN)
        self.shas[XM0_RECORD_REL] = sha_file(XM0_RECORD_REL)
        self.cache = {}

    def copy(self):
        c = Ctx.__new__(Ctx)
        c.rec = copy.deepcopy(self.rec)
        c.xm0 = copy.deepcopy(self.xm0)
        c.doc = self.doc
        c.seal = self.seal
        c.shas = collections.OrderedDict(self.shas)
        c.cache = {}
        return c

    def with_doc(self, doc):
        u"""文書だけ替えた写し(記録・組み直しの記憶は共有。文書の変異用。記録は変えない)。"""
        c = Ctx.__new__(Ctx)
        c.rec, c.xm0, c.seal, c.shas, c.cache = self.rec, self.xm0, self.seal, self.shas, self.cache
        c.doc = doc
        return c


def norm(o):
    return json.loads(json.dumps(o, ensure_ascii=False))


def plain(s):
    return s.replace(u"**", u"")


def f(a, b):
    if b == 0:
        return u"%d/%d(―)" % (a, b)
    return u"%d/%d(%s%%)" % (a, b, pct(a, b))


def pct_fr(x):
    u"""分数の % を小数第 1 位まで四捨五入した字。"""
    return pct(x.numerator, x.denominator)


def num_s(x):
    x = Fraction(x)
    return str(x.numerator) if x.denominator == 1 else u"%.1f" % float(x)


def median(v):
    v = sorted(v)
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2


def s4(d, names=CLASS4):
    return sum(d[c] for c in names)


# ======================================================================================================
# b 数え直し(script の関数は使わない)
def tsum(trees):
    u"""同じ形の木の列 → 葉を足した木(script の関数を使わない別の足し方)。"""
    first = trees[0]
    out = collections.OrderedDict()
    for k, v in first.items():
        if isinstance(v, dict):
            out[k] = tsum([t[k] for t in trees])
        else:
            out[k] = sum(t[k] for t in trees)
    return out


def agg_of(docs):
    body = [collections.OrderedDict((k, v) for k, v in d.items() if k not in NOT_SUMMED) for d in docs]
    return collections.OrderedDict([(u"組", len(docs)), (u"断った組", sum(1 for d in docs if d[u"断った"])), (u"数", tsum(body) if body else collections.OrderedDict())])


def split_docs(rec):
    docs = rec[K_DOCS]
    return [d for d in docs if d[u"番号"] <= TRAIN_COUNT], [d for d in docs if d[u"番号"] > TRAIN_COUNT]


def zero_like(o):
    if isinstance(o, dict):
        return all(zero_like(v) for v in o.values())
    if isinstance(o, bool):
        return not o
    if isinstance(o, (int, float)):
        return o == 0
    return o is None or o == u""


def doc_problems(d):
    u"""組 1 つの中の関係(足し算・大小)。"""
    out = []
    n = d[u"番号"]
    if list(d) != list(DOC_KEYS):
        return [u"組 %s の欄が違う" % n]
    dec = d[u"断った"]
    if dec != bool(d[u"断った年"]) or dec != bool(d[u"断った理由"]) or (dec and d[u"断った年"] not in SIDES):
        out.append(u"組 %d の断りの欄の形が違う" % n)
    if dec:
        rest = dict((k, v) for k, v in d.items() if k not in NOT_SUMMED)
        if not zero_like(rest):
            out.append(u"組 %d は断ったのに数が 0 でない" % n)
        return out
    for k in KINDS:
        x = d[u"対応表の名"][k]
        if list(x) != list(NAME_FIELDS) or x[u"持ち越せる"] + x[u"新しい"] != x[u"今年"] or x[u"新しい・_cor で終わる"] + x[u"新しい・_cor で終わらない"] != x[u"新しい"]:
            out.append(u"組 %d の対応表の名(%s)が足し算と合わない" % (n, k))
    for k in (KN, KT):
        rows = d[u"型の行"][u"今年"][k]
        cls = d[u"今年の行の期の区分"][k]
        if s4(cls) != rows or d[u"名が足りる行"][k] > rows:
            out.append(u"組 %d の今年の行(%s)が足し算と合わない" % (n, k))
        for c in CLASS4:
            if d[u"枠が在る行"][k][c] > cls[c] or d[u"同じ行(日)"][k][c] > cls[c]:
                out.append(u"組 %d の同じ行・枠が在る行(%s・%s)が今年の行より多い" % (n, k, c))
        if s4(d[u"枠が在る行"][k]) > d[u"名が足りる行"][k] or s4(d[u"同じ行(日)"][k]) > d[u"名が足りる行"][k]:
            out.append(u"組 %d の同じ行・枠が在る行(%s)が名が足りる行より多い" % (n, k))
        b = d[u"逆向き"][k]
        if list(b) != list(BACK_FIELDS):
            out.append(u"組 %d の逆向きの欄が違う" % n)
            continue
        if b[u"前の年の行"] != d[u"型の行"][u"前の年"][k] or b[u"同じ鍵(日)が今年に在る"] != s4(d[u"同じ行(日)"][k]) or b[u"同じ鍵(枠)が今年に在る"] != s4(d[u"枠が在る行"][k]) or \
                b[u"今年、要らなくなった枠"] != b[u"前の年の行"] - b[u"同じ鍵(枠)が今年に在る"] or b[u"今年、要らなくなった枠"] < 0:
            out.append(u"組 %d の逆向き(%s)が今年の側の数と合わない" % (n, k))
    if sum(d[u"同じ行の中身(数)"].values()) != s4(d[u"同じ行(日)"][KN]) or list(d[u"同じ行の中身(数)"]) != list(CONTENT4):
        out.append(u"組 %d の同じ行の中身の 4 つの分けの合計が同じ行(数)と違う" % n)
    for s in SIDES:
        o = d[u"型の外の fact"][s]
        for k in (KN, KT):
            rs = [o[u"理由ごと"][r][k] for r in LETTERS]
            if o[u"合計"][k] > d[u"対象の fact"][s][k] or max(rs) > o[u"合計"][k] or sum(rs) < o[u"合計"][k] or d[u"型の行"][s][k] > d[u"対象の fact"][s][k] - o[u"合計"][k]:
                out.append(u"組 %d の型の外の fact(%s・%s)が合わない" % (n, s, k))
    t = d[u"旗用の数"]
    if not t[u"今年の側を分析できた"] or (t[u"今年の側の型の行"][KN], t[u"今年の側の型の行"][KT]) != (d[u"型の行"][u"今年"][KN], d[u"型の行"][u"今年"][KT]):
        out.append(u"組 %d の旗用の数が今年の型の行の数と違う" % n)
    return out


def rate_pairs(docs):
    u"""断らなかった組の (今年の科目の名の持ち越し率, 枠が在る数の行の率) などを導く元。"""
    return [d for d in docs if not d[u"断った"]]


def pred_numbers(rec):
    u"""判定の 60 組から、XK0-1〜XK0-10 の (数, 分母) を導く(組の数で言う XK0-8・9・10 は 組, 分母)。"""
    docs = split_docs(rec)[1]
    g = agg_of(docs)[u"数"]
    sc = g[u"対応表の名"][u"科目"]
    rows = g[u"型の行"][u"今年"][KN]
    cls = g[u"今年の行の期の区分"][KN]
    same = g[u"同じ行(日)"][KN]
    cont = g[u"同じ行の中身(数)"]
    keep = sum(1 for d in docs if not d[u"断った"] and d[u"対応表の名"][u"科目"][u"今年"] > 0 and 100 * d[u"対応表の名"][u"科目"][u"持ち越せる"] >= 95 * d[u"対応表の名"][u"科目"][u"今年"])
    notall = sum(1 for d in docs if not d[u"断った"] and sum(d[u"同じ行の中身(数)"].values()) - d[u"同じ行の中身(数)"][CONTENT4[0]] >= 1)
    return collections.OrderedDict([
        (u"XK0-1", (sc[u"持ち越せる"], sc[u"今年"])), (u"XK0-2", (g[u"名が足りる行"][KN], rows)), (u"XK0-3", (s4(same, OLD2), s4(cls, OLD2))),
        (u"XK0-4", (cont[CONTENT4[0]], s4(same))), (u"XK0-5", (cont[CONTENT4[0]], rows)), (u"XK0-6", (s4(g[u"枠が在る行"][KN]), rows)),
        (u"XK0-7", (sc[u"新しい・_cor で終わる"], sc[u"新しい"])), (u"XK0-8", (sum(1 for d in docs if d[u"断った"]), len(docs))), (u"XK0-9", (keep, len(docs))), (u"XK0-10", (notall, len(docs)))])


def pred_expected(rec):
    out = collections.OrderedDict()
    for key, (id_, (a, b)) in zip(PK, pred_numbers(rec).items()):
        if id_ in (u"XK0-8", u"XK0-9", u"XK0-10"):
            out[key] = collections.OrderedDict([(u"組", a), (u"分母", b)])
        else:
            out[key] = collections.OrderedDict([(u"数", a), (u"分母", b), (u"%", float(pct(a, b)) if b else None)])
    return out


def flags_expected(rec, xm0):
    u"""封 §4 の「先に自分の欠陥を疑う」旗 6 つ(組ごとから導く。旗 6 は便 XM0 の記録と照らす)。"""
    docs = rec[K_DOCS]
    judge = split_docs(rec)[1]
    cur_same = sum(d[u"同じ行(日)"][k][u"当期"] for d in docs for k in (KN, KT))
    all100 = [d for d in judge if not d[u"断った"] and d[u"対応表の名"][u"科目"][u"今年"] > 0 and d[u"対応表の名"][u"科目"][u"持ち越せる"] == d[u"対応表の名"][u"科目"][u"今年"]]
    same_num = sum(s4(d[u"同じ行(日)"][KN]) for d in judge)
    over = [d for d in docs if any(s4(d[u"枠が在る行"][k]) > d[u"名が足りる行"][k] for k in (KN, KT))]
    refused = sum(1 for d in judge if d[u"断った"])
    by_no = dict((x[u"番号"], x) for x in xm0[K_DOCS])
    diff = sum(1 for d in docs if (d[u"旗用の数"][u"今年の側の型の行"][KN], d[u"旗用の数"][u"今年の側の型の行"][KT]) != (by_no[d[u"番号"]][u"型の行"][KN], by_no[d[u"番号"]][u"型の行"][KT]))
    O = collections.OrderedDict
    return O([
        (FLAG_KEYS[0], O([(u"同じ行(日)の当期の行", cur_same), (u"旗", cur_same >= 1)])),
        (FLAG_KEYS[1], O([(u"100% の組", len(all100)), (u"判定の組", len(judge)), (u"旗", len(all100) == len(judge) and len(judge) > 0)])),
        (FLAG_KEYS[2], O([(u"同じ行(数)", same_num), (u"旗", same_num == 0)])),
        (FLAG_KEYS[3], O([(u"その組", len(over)), (u"旗", len(over) >= 1)])),
        (FLAG_KEYS[4], O([(u"断った組", refused), (u"旗", refused >= 6)])),
        (FLAG_KEYS[5], O([(u"違う組", diff), (u"旗", diff >= 1)]))])


def recount_problems(c):
    rec = c.rec
    out = []
    docs = rec[K_DOCS]
    m = rec[u"材料"]
    nums = [d[u"番号"] for d in docs]
    if len(docs) != PAIR_COUNT or nums != sorted(set(nums)) or nums[-1] != DOC67 or any(n < 1 for n in nums):
        return [u"組の番号が昇順の 63 個(最大 67)でない"]
    for k, v in MATERIAL_PIN.items():
        if m[k] != v:
            out.append(u"材料の欄が字で留めた値と違う: %s" % k)
    if m[u"今年の側の書類の本数"] - m[u"組の数"] != m[u"除いた今年の書類の数"]:
        out.append(u"材料の書類の本数 − 組の数 が除いた書類の数と違う")
    train, judge = split_docs(rec)
    if len(train) != TRAIN_COUNT or len(judge) != JUDGE_COUNT:
        return out + [u"訓練の 3 組と判定の 60 組の分け(番号 3 / 4 の境)が違う"]
    for d in docs:
        out.extend(doc_problems(d))
    if list(rec[K_SUM]) != list(GROUPS):
        return out + [u"集計の欄の名が違う"]
    for key, ds in ((G_TRAIN, train), (G_JUDGE, judge), (G_ALL, docs)):
        if norm(rec[K_SUM][key]) != norm(agg_of(ds)):
            out.append(u"%s の集計が組ごとの数から数え直した値と違う" % key)
    if list(rec[PRED_KEY]) != list(PK):
        return out + [u"予測の判定に要る数の欄の名が違う"]
    if norm(rec[PRED_KEY]) != norm(pred_expected(rec)):
        out.append(u"予測の判定に要る数が組ごとから作り直した値と違う")
    if list(rec[FLAG_KEY]) != list(FLAG_KEYS):
        return out + [u"旗の欄の名が違う"]
    if norm(rec[FLAG_KEY]) != norm(flags_expected(rec, c.xm0)):
        out.append(u"旗が組ごとから作り直した値と違う")
    if rec[K_SUM][G_JUDGE][u"組"] != JUDGE_COUNT or rec[K_SUM][G_TRAIN][u"組"] != TRAIN_COUNT or rec[K_SUM][G_ALL][u"組"] != PAIR_COUNT:
        out.append(u"集計の組の数が 3・60・63 でない")
    return out


def sha_problems(c):
    out = []
    for rel, want in SHA_PIN.items():
        if c.shas[rel] != want:
            out.append(u"sha256 が字で留めた値と違う: %s" % rel)
    if c.shas[XM0_RECORD_REL] != XM0_RECORD_SHA:
        out.append(u"便 XM0 の記録の sha256 が字で留めた値と違う")
    if c.rec[u"この script の sha256"] != SHA_PIN[SCRIPT_REL]:
        out.append(u"記録の script の sha256 が script と違う")
    if (c.rec[u"seal"], c.rec[u"封の commit"]) != (SEAL_REL, SEAL_COMMIT_SHORT):
        out.append(u"記録の封の欄が違う")
    if c.rec[u"限界"] != MS.LIMITS:
        out.append(u"記録の限界の欄が script の字と違う")
    if c.rec[u"step"] != u"XK0(同じ会社の前の年の型と対応表が今年の型にどれだけ持ち越せるか・今年、新しく決める名・新しく入れる行はどれだけ残るか)(0 USD・engine は 0 行)":
        out.append(u"記録の step の欄が違う")
    return out


DATE_FORM = re.compile(r"(?<![0-9])(?:19|20)\d{2}[-/.]\d{1,2}[-/.]\d{1,2}(?![0-9])|(?<![0-9])(?:19|20)\d{2}年\d{1,2}月")


def record_clean_problems(c):
    text = json.dumps(c.rec, ensure_ascii=False)
    out = []
    try:
        MS.check_clean(c.rec, text)
    except BaseException as exc:                    # noqa: BLE001
        out.append(u"記録の検査(欄・形・file の名・日付)が止める: %s" % type(exc).__name__)
    if WG.DOCID_FORM.search(re.sub(r"[0-9a-fA-F]{32,}", u"", text)) or WG.ECODE_FORM.search(text):
        out.append(u"記録に docid か EDINET コードの形が在る")
    if DATE_FORM.search(text.replace(SEAL_REL, u"")):
        out.append(u"記録に日付の形が在る(封 §3 は日付を持たないと決めた。門が見る)")
    return out


def seal_s6_lines(seal):
    s6 = section(seal, u"## §6 ", u"## §7 ")
    return s6


def bound_problems(c):
    out = [u"封に字が無い: %s" % p[:24] for p in BOUND_SEAL_PHRASES if p not in c.seal]
    sec4 = section(c.seal, u"## §4 ", u"## §5 ")
    rows = [ln for ln in sec4.splitlines() if re.match(r"^\| XK0-\d", ln)]
    if len(rows) != 10:
        out.append(u"封 §4 の表の行が 10 でない")
    sec7 = section(c.seal, u"## §7 ", None)
    if len([ln for ln in sec7.splitlines() if ln.startswith(u"- ")]) != 6:
        out.append(u"封 §7 の限界の行が 6 行でない")
    if u"旗用の数" in c.seal:
        out.append(u"封に「旗用の数」が在る(文書の補足は「封に無い欄」と書く)")
    return out


# ======================================================================================================
# c 当たり外れの決め直し(封 §4 の境。丸める前の整数。判定の 60 組)
def judge_nums(p):
    u"""封 §4 の境(整数のまま)。p は pred_numbers の形。値は (当たりか, 外れた向き)。"""
    O = collections.OrderedDict
    out = O()
    k1, d1 = p[u"XK0-1"]
    out[u"XK0-1"] = (d1 > 0 and 100 * k1 >= 96 * d1, u"" if (d1 > 0 and 100 * k1 >= 96 * d1) else u"下")
    for key, pc in ((u"XK0-2", 97), (u"XK0-3", 97), (u"XK0-6", 95)):
        a, b = p[key]
        ok = b > 0 and 100 * a >= pc * b
        out[key] = (ok, u"" if ok else u"下")
    a, b = p[u"XK0-4"]
    lo, hi = b > 0 and 100 * a >= 96 * b, b > 0 and a < b
    out[u"XK0-4"] = (lo and hi, u"" if lo and hi else u"下" if not lo else u"上")
    a, b = p[u"XK0-5"]
    lo, hi = b > 0 and 100 * a >= 44 * b, b > 0 and 100 * a < 52 * b
    out[u"XK0-5"] = (lo and hi, u"" if lo and hi else u"下" if not lo else u"上")
    a, b = p[u"XK0-7"]
    out[u"XK0-7"] = (b > 0 and 2 * a > b, u"" if (b > 0 and 2 * a > b) else u"下")
    out[u"XK0-8"] = (p[u"XK0-8"][0] <= 3, u"" if p[u"XK0-8"][0] <= 3 else u"上")
    out[u"XK0-9"] = (p[u"XK0-9"][0] >= 48, u"" if p[u"XK0-9"][0] >= 48 else u"下")
    out[u"XK0-10"] = (p[u"XK0-10"][0] >= 57, u"" if p[u"XK0-10"][0] >= 57 else u"下")
    return O((k, out[k]) for k in IDS)


def judge(rec):
    return judge_nums(pred_numbers(rec))


def miss_ids(j):
    return [k for k in IDS if not j[k][0]]


def suspects(c):
    return tuple(v[u"旗"] for v in flags_expected(c.rec, c.xm0).values())


PRED_TEXT = collections.OrderedDict([
    (u"XK0-1", u"今年の科目の名のうち、前の年の対応表に在る名は 96% 以上"), (u"XK0-2", u"数の型の行のうち、名が足りる行は 97% 以上"),
    (u"XK0-3", u"前期かそれより前の数の行のうち、同じ行が前の年の型に在るのは 97% 以上"), (u"XK0-4", u"同じ行(数)のうち「全部同じ」は 96% 以上 100% 未満"),
    (u"XK0-5", u"今年の数の型の行の全部のうち、同じ行で全部同じの行は 44% 以上 52% 未満"), (u"XK0-6", u"今年の数の型の行のうち、枠が在る行は 95% 以上"),
    (u"XK0-7", u"新しい科目の名のうち、接頭辞が `_cor` で終わるものは半分より多い"), (u"XK0-8", u"断った組は 3 以下"),
    (u"XK0-9", u"科目の名の持ち越しが 95% 以上の組は 48 組以上"), (u"XK0-10", u"同じ行(数)に「全部同じ」でない行が 1 つ以上在る組は 57 組以上")])


def cell_text(rec, key):
    p = pred_numbers(rec)[key]
    if key in (u"XK0-8",):
        return u"%d 組" % p[0]
    if key in (u"XK0-9", u"XK0-10"):
        return u"%d 組(%d 組のうち)" % p
    return f(*p)


def expected_cells(c):
    out = collections.OrderedDict()
    for k, (ok, way) in judge(c.rec).items():
        out[k] = (cell_text(c.rec, k), u"当たり" if ok else u"外れ")
    return out


CAND_MARK = re.compile(u"^  - \\((i|ii|iii)\\) ", re.M)
ANY_MARK = re.compile(u"\\((?:i|ii|iii|iv|v)\\)")
DECISION_RE = re.compile(u"^- 封 §6 の決め: ")


def seal_candidates(s6):
    u"""封 §6 の次の便の候補 (i)(ii)(iii) を、封の字から取る(3 つ。(iii) は封の字のまま・(i)(ii) は文書が「。別の封が先」を足す)。"""
    line = [ln for ln in s6.splitlines() if ln.startswith(u"  - XK0-1 と XK0-6 が両方当たり")][0]
    body = line[line.index(u"(i) "):]
    parts = re.split(u"(?<=[)])・(?=\\((?:ii|iii)\\) )", body)
    assert len(parts) == 3, parts
    parts[2] = parts[2][:parts[2].index(u")。") + 1]
    return [p.strip() for p in parts]


def sec5_decision_problems(sec5, hit_both, s6):
    u"""封 §6(XK0-1 と XK0-6 が両方当たりなら (i)(ii)(iii) をちょうど示す。どちらかが外れなら示さず、新しい名・枠の無い行の中身を読むのが先)と文書 §5 が合う。"""
    out = []
    p5 = plain(sec5)
    lines = [ln for ln in p5.splitlines() if ln.strip()]
    idx = [i for i, ln in enumerate(lines) if DECISION_RE.search(ln)]
    if len(idx) != 1:
        return [u"§5 に「封 §6 の決め:」の行が 1 つでない"]
    head_i = idx[0]
    head = lines[head_i]
    marks = CAND_MARK.findall(p5)
    shown = bool(marks)
    if hit_both != shown:
        out.append(u"封 §6 の決め(両方当たりなら次の便の候補を示す・どちらかが外れなら示さない)と文書 §5 が合わない")
    if hit_both:
        want = seal_candidates(s6)
        if marks != [u"i", u"ii", u"iii"] or len(ANY_MARK.findall(p5)) != 3:
            out.append(u"§5 の次の便の候補の見出しが (i)(ii)(iii) の 3 つだけでない: %s" % u",".join(marks))
        got = lines[head_i + 1:head_i + 4]
        if got != [u"  - " + w + u"。" for w in want]:
            out.append(u"§5 の次の便の候補の行が封 §6 の字と違う")
        if p5.count(u"0 USD。別の封が先)") != 2 or p5.count(u"(有料。別の封と、払う前の知らせが先)") != 1:
            out.append(u"§5 の費用の字が (i)(ii) の「0 USD。別の封が先」2 つ・(iii) の「有料…」1 つでない")
        if u"次の便の候補を 3 つ示す" not in head or u"選ぶのは人間" not in head or u"どれも別の封が先" not in head or u"両方当たり" not in head:
            out.append(u"§5 の決めの行に「両方当たり」「次の便の候補を 3 つ示す」「どれも別の封が先」「選ぶのは人間」が無い")
    else:
        if u"次の便の候補は示さない" not in head or u"新しい名・枠の無い行の中身を読むのが先" not in head or u"どちらかが外れ" not in head:
            out.append(u"外れたのに、「次の便の候補は示さない」「新しい名・枠の無い行の中身を読むのが先」が §5 の決めの行に無い")
        if ANY_MARK.search(p5) or p5.count(u"候補") != 1 or p5.count(u"次の便") != 1:
            out.append(u"外れたのに §5 が次の便の候補を示している(候補の見出し・「候補」の字が決めの行の 1 つ以外に在る)")
        for w in CAND_KEYS + (u"0 USD。別の封が先", u"(有料", u"第 1 版", u"答えを見ない席"):
            if w in p5:
                out.append(u"外れたのに §5 に封の当たりの側の候補の字が在る: %s" % w[:12])
    if u"続けるか・どの向きへ続けるかは人間が決める" not in p5:
        out.append(u"§5 に「続けるか・どの向きへ続けるかは人間が決める」が無い")
    return out


def verdict_problems(c):
    rec = c.rec
    j = judge(rec)
    want = expected_cells(c)
    out = []
    rows = {}
    for ln in c.doc.splitlines():
        m = re.match(r"^\| (XK0-\d+)(?:\(主\))? \|(.*)\|$", ln)
        if m:
            rows[m.group(1)] = [x.strip() for x in m.group(2).split(u"|")]
    if sorted(rows) != sorted(j):
        return [u"文書 §1 の表の行が XK0-1〜XK0-10 でない"]
    sec4 = section(c.seal, u"## §4 ", u"## §5 ")
    for k, cells in rows.items():
        if len(cells) != 3:
            out.append(u"%s の行の欄の数が違う" % k)
            continue
        if cells[0] != PRED_TEXT[k]:
            out.append(u"%s の予測の字が門の留めた要約と違う: %s" % (k, cells[0]))
        srow = [x for x in sec4.splitlines() if re.match(r"^\| %s[^0-9]" % re.escape(k), x)]
        if len(srow) != 1 or any(x not in srow[0] for x in SG.SEAL_BOUND_TEXT[k]):
            out.append(u"%s の境の字が封 §4 の表に無い" % k)
        if cells[1] != want[k][0]:
            out.append(u"%s の実測の字が記録から組んだ字と違う: %s" % (k, cells[1]))
        if cells[2] != want[k][1]:
            out.append(u"%s の判定が決め直した判定と違う: %s(決め直し: %s)" % (k, cells[2], want[k][1]))
    if not re.search(r"^\| XK0-1\(主\) \|", c.doc, re.M):
        out.append(u"XK0-1 の行に「(主)」が無い(封 §4 の主の読み)")
    for k in IDS[1:]:
        if re.search(r"^\| %s\(主\) \|" % k, c.doc, re.M):
            out.append(u"%s の行に「(主)」が付いている(封 §4 の主は XK0-1 だけ)" % k)
    hits = sum(1 for v in j.values() if v[0])
    if u"- 当たり %d・外れ %d。" % (hits, len(j) - hits) not in c.doc.splitlines():
        out.append(u"文書の件数の行が決め直した件数と違う")
    head = plain(c.doc.split(u"## §1")[0])
    miss = miss_ids(j)
    if u"判定した %d 本は 当たり %d・外れ %d。" % (len(j), hits, len(j) - hits) not in head:
        out.append(u"文書の頭の件数が決め直した値と違う")
    if u"XK0-1" in miss:
        if u"主の予測(XK0-1)を含む %d 本は外れ。 外れは %s。" % (len(miss), u"・".join(miss)) not in head:
            out.append(u"外れた主の予測の言い切りが文書の頭に無い(%s)" % u"・".join(miss))
    else:
        if re.search(u"主の予測[^。]*は外れ", head):
            out.append(u"主の予測は当たりなのに文書の頭が外れと書いている")
        if miss and u"予測の %d 本(%s)は外れ。" % (len(miss), u"・".join(miss)) not in head:
            out.append(u"外れた予測の言い切りが文書の頭に無い(%s)" % u"・".join(miss))
    if not miss and re.search(u"予測の[^。]*本[^。]*は外れ|を含む[^。]*本は外れ", head):
        out.append(u"外れが無いのに文書の頭が外れと書いている")
    sec1, sec5 = section(c.doc, u"## §1 ", u"## §2 "), section(c.doc, u"## §5 ", None)
    sus = suspects(c)
    if any(sus):
        out.append(u"封 §4 の「先に自分の欠陥を疑う」旗が立っている: %s" % (sus,))
    line = [ln for ln in sec1.splitlines() if u"「先に自分の欠陥を疑う」旗" in ln]
    if len(line) != 1 or line[0].count(u"6 つとも立たない") != 1 or any(line[0].count(u"― 0 ") < 1 for _ in [0]):
        out.append(u"文書 §1 の自己点検の言い切り(旗 6 つ・どれも立たない)が封の字・記録と合わない")
    hit_both = j[u"XK0-1"][0] and j[u"XK0-6"][0]
    s6 = seal_s6_lines(c.seal)
    out.extend(sec5_decision_problems(sec5, hit_both, s6))
    # 判定の表に 3 組・63 組の数が混ざらない(判定の 60 組の数だけ)
    only_other = set()
    for key in (G_TRAIN, G_ALL):
        ints_in(rec[K_SUM][key], only_other)
    only_judge = set()
    ints_in(rec[K_SUM][G_JUDGE], only_judge)
    ints_in(rec[PRED_KEY], only_judge)
    mixed = [t for ln in rows for t in doc_number_tokens(rows[ln][1]) if t in only_other and t not in only_judge and t not in STRUCTURAL]
    if mixed:
        out.append(u"判定の表に 3 組・63 組だけの数が混ざっている: %s" % u",".join(mixed))
    return out


# ======================================================================================================
# d 文書の数・主な主張の文(§3 以外の全部の行を記録と字から組み直す)
def cached(c, key, fn):
    if key not in c.cache:
        c.cache[key] = fn()
    return c.cache[key]


def stat_values(rec):
    u"""組ごとから導く数(判定の 60 組のうち断らなかった組)。"""
    nd = [d for d in split_docs(rec)[1] if not d[u"断った"]]
    train = split_docs(rec)[0]
    judge = split_docs(rec)[1]
    keep = sorted(Fraction(d[u"対応表の名"][u"科目"][u"持ち越せる"], d[u"対応表の名"][u"科目"][u"今年"]) for d in nd if d[u"対応表の名"][u"科目"][u"今年"] > 0)
    new = [d[u"対応表の名"][u"科目"][u"新しい"] for d in nd]
    frame = []
    noframe = []
    for d in nd:
        n = d[u"型の行"][u"今年"][KN]
        k = s4(d[u"枠が在る行"][KN])
        frame.append(Fraction(k, n))
        noframe.append(n - k)
    frame.sort()
    diff = [d[u"同じ行の中身(数)"][CONTENT4[2]] for d in nd]
    g = agg_of(judge)[u"数"]
    ta = agg_of(train)[u"数"]
    al = agg_of(rec[K_DOCS])[u"数"]
    return collections.OrderedDict([
        (u"nd", len(nd)),
        (u"keep", (pct_fr(keep[0]), pct_fr(median(keep)), pct_fr(keep[-1]), sum(1 for x in keep if x * 100 >= 90), sum(1 for x in keep if x * 100 >= 95), sum(1 for x in keep if x * 100 >= 98), sum(1 for x in keep if x * 100 < 80))),
        (u"new", (min(new), num_s(median(new)), max(new), sum(1 for x in new if x == 0), sum(sorted(new, reverse=True)[:5]))),
        (u"frame", (pct_fr(frame[0]), pct_fr(median(frame)), pct_fr(frame[-1]), sum(1 for x in frame if x * 100 >= 95), sum(1 for x in frame if x * 100 >= 90), sum(1 for x in frame if x * 100 < 80))),
        (u"noframe", (sum(noframe), sum(sorted(noframe, reverse=True)[:5]), max(noframe))),
        (u"diff", (sum(1 for x in diff if x >= 1), max(diff), sum(sorted(diff, reverse=True)[:5]))),
        (u"cur_noframe", g[u"今年の行の期の区分"][KN][u"当期"] - g[u"枠が在る行"][KN][u"当期"]),
        (u"not_same", g[u"型の行"][u"今年"][KN] - g[u"同じ行の中身(数)"][CONTENT4[0]]),
        (u"old_nosame", s4(g[u"今年の行の期の区分"][KN], OLD2) - s4(g[u"同じ行(日)"][KN], OLD2)),
        (u"train", ta), (u"all", al), (u"judge", g)])


def render_pre(c):
    u"""記録(と字で留めた文)から、文書の §3 より前の全部の行を組み直す。"""
    rec = c.rec
    Tr, Jd, Al = rec[K_SUM][G_TRAIN], rec[K_SUM][G_JUDGE], rec[K_SUM][G_ALL]
    PN, TN, AN = Jd[u"数"], Tr[u"数"], Al[u"数"]
    st = cached(c, u"st", lambda: stat_values(rec))
    j = cached(c, u"judge", lambda: judge(rec))
    hits = sum(1 for v in j.values() if v[0])
    miss = miss_ids(j)
    cells = cached(c, u"cells", lambda: expected_cells(c))
    pn = pred_numbers(rec)
    m = rec[u"材料"]
    L = []
    w = L.append
    w(u"# 結果: 便 XK0 ― 同じ会社の前の年の型と対応表は、今年の型にどれだけ持ち越せたか。今年、新しく決める名・新しく入れる行はどれだけ残ったか ― 2026-11-22")
    w(u"")
    w(u"封 `%s`(commit %s)。script `%s` と封の門 `%s` は commit %s(独立監査 REVISE → 直し → GO。REVISE は門の穴 1 つで、script は 1 回目から変えていない)。"
      u"記録 `%s` は commit %s(独立監査 GO。%d 組の全部を別の実装で数え直して差は 0)。費用は 0 USD。engine(`core/`・`adapters/`)は 0 行。XBRL は組んでいない。道具には掛けていない。" % (
          SEAL_REL, SEAL_COMMIT_SHORT, SCRIPT_REL, SEAL_GATE_REL, SCRIPT_COMMIT_SHORT, RECORD_REL, RECORD_COMMIT_SHORT, Al[u"組"]))
    w(u"")
    w(u"この文書の §1・§2 の数は全部、記録から 1 つずつ読んだもの(結果の門が、記録の数と字で同じことを見る)。§3 は記録に欄の無い読みで、出どころを書く。")
    w(u"")
    w(u"**先に負けと限界を書く。**")
    w(u"")
    sc_k1, sc_k6 = pn[u"XK0-1"], pn[u"XK0-6"]
    lead = (u"**主の予測(XK0-1)を含む %d 本は外れ。** 外れは %s。" % (len(miss), u"・".join(miss))) if u"XK0-1" in miss else (u"**予測の %d 本(%s)は外れ。**" % (len(miss), u"・".join(miss)))
    tail = u""
    if u"XK0-1" in miss:
        tail += u"今年の科目の名のうち前の年の対応表に在る名は %sで、予測の 96%% 以上に届かなかった。" % f(*sc_k1)
    if u"XK0-6" in miss:
        tail += u"枠が在る数の行は %sで、予測の 95%% 以上に届かなかった。" % f(*sc_k6)
    w(u"- %s%s" % (lead, tail))
    w(u"- **予測の境は頭の 3 組を見て立て、判定の 60 組では高すぎた。** 頭の 3 組は持ち越しやすい側に寄っていた。外れは外れとして残す。")
    w(u"- **どちらの年の型も対応表も答えから作った。** 会社が型を埋められるか・対応表を作れるか・埋めた中身が正しいかは測っていない。持ち越しは上限。**この便の数は「会社が型を埋められる」とは読まない。**")
    kp, fr = st[u"keep"], st[u"frame"]
    w(u"- **組による差が大きい。** 科目の名の持ち越しは、組ごとに最小 %s%%・最大 %s%%。枠が在る数の行は、組ごとに最小 %s%%・最大 %s%%。合計の率は 1 つの会社について言える数ではない。" % (kp[0], kp[2], fr[0], fr[2]))
    w(u"- 「全部同じ」の行は「去年の型の値がそのまま今年の前期の欄に使える」だけを言う。その値が正しいことは言わない。")
    w(u"- 鍵が同じでも、指すものが同じとは限らない(番号つきの member は年で中身が入れ替わりうる)。")
    w(u"- 「新しい名」は、会社が今年、新しく決める名の数の下限ではない(答えの側で使われた名を数えただけ)。")
    for lim in MS.LIMITS[1:-1]:
        w(u"- " + lim)
    w(u"- %s判定した %d 本は 当たり %d・外れ %d。" % (MS.LIMITS[-1], len(j), hits, len(j) - hits))
    w(u"- **「XBRL を作れる」「専用の道具が要らない」「会社が型を埋められる」「入力が半分で済む」「誤りが無くなる」は、この便からは言えない。**")
    w(u"")
    w(u"**日付つきの補足(2026-11-22。封は書き換えていない)。**")
    w(u"")
    w(u"- **封の字と実装が合わない所**(封の門が字で留めている)。封は判定の組を「番号 4〜63」と書いたが、番号は今年の側の %d 本の中の位置で、%d まで在る。実装は「番号が %d より大きい組」を判定の %d 組にした(組の数は封の字どおり %d)。" % (
        m[u"今年の側の書類の本数"], rec[K_DOCS][-1][u"番号"], MS.SEEN_MAX_NO, Jd[u"組"], Jd[u"組"]))
    w(u"- **旗の母集団**: 旗 1・4・6 は %d 組、旗 2・3・5 は判定の %d 組で見た(封は母集団を書いていなかった)。" % (Al[u"組"], Jd[u"組"]))
    w(u"- **XK0-9 の数え方**: 科目の名が 0 の組は「95% 以上」に数えない(そういう組は無かった)。次元の組は並べ替えた組で比べる。")
    w(u"- **記録に封に無い欄が 1 つ在る**: 「旗用の数」(旗 6 を導き直すための、今年の側の型の行の数)。")
    w(u"- **司令塔が足した数え**: 型の行の持ち越し(名だけでなく行)は、便 XM0 の封の次の便の字(対応表の持ち越し)より広い。封 §0 に申告済み。")
    w(u"- **封の門に穴が 1 つ残っている。** 旗 2(科目の名の持ち越しが 60 組の全部で 100%)の「100%」を 95% に緩める変異は、作り物の場面が小さく黙る。旗は止めない作りで、判定の数にも記録の数にも効かない。直していない。")
    w(u"")
    w(u"## §1 予測の当たり外れ(司令塔。盲検ではない)")
    w(u"")
    w(u"封 §4 の字の境と記録から、結果の門が XK0-1〜XK0-10 の当たり外れを決め直した(この表と同じ)。封も予測も結果を見てから書き換えていない。判定は丸める前の数でした。分母は判定の %d 組だけ。頭の %d 組の数は予測の判定には使わない。" % (Jd[u"組"], Tr[u"組"]))
    w(u"")
    w(u"| # | 予測(封の字の要約) | 実測(記録) | 判定 |")
    w(u"|---|---|---|---|")
    for k in IDS:
        w(u"| %s%s | %s | %s | %s |" % (k, u"(主)" if k == u"XK0-1" else u"", PRED_TEXT[k], cells[k][0], cells[k][1]))
    w(u"")
    w(u"- 当たり %d・外れ %d。" % (hits, len(j) - hits))
    w(u"- XK0-5 の当たりは期の区分の作りに縛られる(当期と提出日の行は、作りから同じ行が前の年に無い)。")
    w(u"- XK0-8 は断った組が %d で、境(3 以下)から遠い。" % Jd[u"断った組"])
    fl = rec[FLAG_KEY]
    f1, f2, f3, f4, f5, f6 = [fl[k] for k in FLAG_KEYS]
    w(u"- 封 §4 の「先に自分の欠陥を疑う」旗は 6 つとも立たない: 期の区分が当期の行に同じ行(日)が在る ― %d 行。科目の名の持ち越しが 60 組の全部で 100%% ― 100%% の組は %d。"
      u"同じ行(数)が 60 組の合計で 0 ― %d。枠が在る行が名が足りる行より多い組 ― %d 組。断った組が 6 以上 ― %d 組。"
      u"便 XM0 の記録の型の行の数とこの便の今年の側の型の行の数が違う組 ― %d 組。" % (f1[u"同じ行(日)の当期の行"], f2[u"100% の組"], f3[u"同じ行(数)"], f4[u"その組"], f5[u"断った組"], f6[u"違う組"]))
    w(u"")
    w(u"## §2 数(記録)")
    w(u"")
    w(u"材料: 今年の側の書類 %d 本のうち、前の年の相手が在る %d 組(除いた今年の書類は %d 本)。訓練の %d 組・判定の %d 組。下の数は、断らないかぎり判定の %d 組。断った組は %d。" % (
        m[u"今年の側の書類の本数"], m[u"組の数"], m[u"除いた今年の書類の数"], Tr[u"組"], Jd[u"組"], Jd[u"組"], Jd[u"断った組"]))
    w(u"")
    w(u"**対象の fact と型の行**:")
    w(u"")
    tg, ou, rw = PN[u"対象の fact"], PN[u"型の外の fact"], PN[u"型の行"]
    w(u"| | 今年・数 | 今年・文 | 前の年・数 | 前の年・文 |")
    w(u"|---|---|---|---|---|")
    w(u"| 対象の fact | %d | %d | %d | %d |" % (tg[u"今年"][KN], tg[u"今年"][KT], tg[u"前の年"][KN], tg[u"前の年"][KT]))
    w(u"| 型の外の fact | %d | %d | %d | %d |" % (ou[u"今年"][u"合計"][KN], ou[u"今年"][u"合計"][KT], ou[u"前の年"][u"合計"][KN], ou[u"前の年"][u"合計"][KT]))
    w(u"| 型の行 | %d | %d | %d | %d |" % (rw[u"今年"][KN], rw[u"今年"][KT], rw[u"前の年"][KN], rw[u"前の年"][KT]))
    w(u"")
    w(u"**対応表の名の持ち越し**(今年の対応表の名のうち、前の年の対応表に同じ字の名が在るもの):")
    w(u"")
    mp = PN[u"対応表の名"]
    w(u"| | 今年の名 | 持ち越せる | 新しい | うち `_cor` で終わる | うち `_cor` で終わらない | 消えた |")
    w(u"|---|---|---|---|---|---|---|")
    for k in KINDS:
        x = mp[k]
        w(u"| %s | %d | %d | %d | %d | %d | %d |" % (k, x[u"今年"], x[u"持ち越せる"], x[u"新しい"], x[u"新しい・_cor で終わる"], x[u"新しい・_cor で終わらない"], x[u"消えた"]))
    w(u"")
    w(u"- 科目の名の持ち越しは、組ごとに最小 %s%%・中央 %s%%・最大 %s%%。90%% 以上の組は %d・95%% 以上の組は %d・98%% 以上の組は %d・80%% 未満の組は %d。" % kp)
    nw = st[u"new"]
    w(u"- 新しい科目の名は、組ごとに最小 %d・中央 %s・最大 %d。新しい科目の名が 0 の組は%s。多い順の 5 組で %d(%d のうち)。" % (nw[0], nw[1], nw[2], u"無い" if nw[3] == 0 else u"%d" % nw[3], nw[4], mp[u"科目"][u"新しい"]))
    w(u"")
    w(u"**名が足りる行**(行の科目・軸・member の名が全部、前の年の対応表に在る行): 数 %s・文 %d/%d。" % (f(PN[u"名が足りる行"][KN], rw[u"今年"][KN]), PN[u"名が足りる行"][KT], rw[u"今年"][KT]))
    w(u"")
    w(u"**今年の数の行の期の区分と、同じ行・枠**:")
    w(u"")
    w(u"| 期の区分 | 今年の数の行 | 同じ行(日)が前の年に在る | 枠が在る |")
    w(u"|---|---|---|---|")
    cl, sm, fm = PN[u"今年の行の期の区分"][KN], PN[u"同じ行(日)"][KN], PN[u"枠が在る行"][KN]
    for c_ in CLASS4:
        w(u"| %s | %d | %d | %d |" % (c_, cl[c_], sm[c_], fm[c_]))
    w(u"| 合計 | %d | %d | %d |" % (s4(cl), s4(sm), s4(fm)))
    w(u"")
    w(u"- 今年、値を新しく入れる当期の数の行は %d。そのうち、前の年の型に同じ枠(科目・期の名・対象・次元が同じ行)が在るのは %d。枠も無い当期の数の行は %d。" % (cl[u"当期"], fm[u"当期"], st[u"cur_noframe"]))
    w(u"- 枠が在る数の行は、組ごとに最小 %s%%・中央 %s%%・最大 %s%%。95%% 以上の組は %d・90%% 以上の組は %d・80%% 未満の組は %d。" % fr)
    nf = st[u"noframe"]
    w(u"- 枠が無い数の行は %d。多い順の 5 組で %d。1 組の最大は %d。" % nf)
    w(u"")
    w(u"**同じ行(数)の中身**(同じ行 %d の分け):" % s4(sm))
    w(u"")
    w(u"| 分け | 行 |")
    w(u"|---|---|")
    ct = PN[u"同じ行の中身(数)"]
    for k in CONTENT4:
        w(u"| %s | %d |" % (CONTENT_LABEL[k], ct[k]))
    w(u"")
    df = st[u"diff"]
    w(u"- 「値が違う」が 1 行以上在る組は %d。1 組の最大は %d。多い順の 5 組で %d。" % df)
    w(u"- 今年の数の行の全部 %d のうち、去年の型の値がそのまま使える行は %d(%s%%)。残りの %d は、今年、値を入れるか確かめ直す行。" % (
        rw[u"今年"][KN], ct[CONTENT4[0]], pct(ct[CONTENT4[0]], rw[u"今年"][KN]), st[u"not_same"]))
    w(u"")
    tc, tf_, tx = PN[u"今年の行の期の区分"][KT], PN[u"枠が在る行"][KT], PN[u"同じ行(日)"][KT]
    w(u"**今年の文の行**: 当期 %d・前期 %d・それより前 %d・提出日 %d。同じ行(日)が在るのは前期の %d。枠が在るのは 当期 %d・前期 %d・提出日 %d(合計 %d/%d)。" % (
        tc[u"当期"], tc[u"前期"], tc[u"それより前"], tc[u"提出日"], tx[u"前期"], tf_[u"当期"], tf_[u"前期"], tf_[u"提出日"], s4(tf_), rw[u"今年"][KT]))
    w(u"")
    w(u"**逆向き**(前の年の型の行から見て):")
    w(u"")
    w(u"| | 前の年の行 | 同じ鍵(日)が今年に在る | 同じ鍵(枠)が今年に在る | 今年、要らなくなった枠 |")
    w(u"|---|---|---|---|---|")
    bk = PN[u"逆向き"]
    for k in (KN, KT):
        w(u"| %s | %d | %d | %d | %d |" % (k, bk[k][u"前の年の行"], bk[k][u"同じ鍵(日)が今年に在る"], bk[k][u"同じ鍵(枠)が今年に在る"], bk[k][u"今年、要らなくなった枠"]))
    w(u"")
    ta = st[u"train"]
    w(u"**頭の 3 組(訓練。予測の判定には使わない)**: 科目の名 %d/%d・数の行で名が足りる %d/%d・同じ行(数)%d のうち全部同じ %d・値が違う %d。封 §0 の申告の数と同じ。" % (
        ta[u"対応表の名"][u"科目"][u"持ち越せる"], ta[u"対応表の名"][u"科目"][u"今年"], ta[u"名が足りる行"][KN], ta[u"型の行"][u"今年"][KN], s4(ta[u"同じ行(日)"][KN]), ta[u"同じ行の中身(数)"][CONTENT4[0]],
        ta[u"同じ行の中身(数)"][CONTENT4[2]]))
    w(u"")
    aa = st[u"all"][u"対応表の名"][u"科目"]
    w(u"**全部の 63 組(予測の判定には使わない)**: 科目の名 %d/%d・新しい科目の名 %d(`_cor` で終わる %d・終わらない %d)・消えた %d。" % (
        aa[u"持ち越せる"], aa[u"今年"], aa[u"新しい"], aa[u"新しい・_cor で終わる"], aa[u"新しい・_cor で終わらない"], aa[u"消えた"]))
    w(u"")
    return L


def render_post(c):
    u"""文書の §4 以降(封の門の本数・記録の監査・§5)を、記録と封の門の本数から組み直す。"""
    rec = c.rec
    j = cached(c, u"judge", lambda: judge(rec))
    pn = pred_numbers(rec)
    hit_both = j[u"XK0-1"][0] and j[u"XK0-6"][0]
    L = []
    w = L.append
    w(u"## §4 門と監査")
    w(u"")
    w(u"- 封の門: 試験 %d 本。変異 %d 本(字を 1 か所替える %d 本・掃く形の %d 本)が赤。作りから黙る変異 %d 本は理由つきで別の試験が縛る。独立監査の 1 回目は REVISE(旗 2 を「持ち越しが名の数より 1 少なくてもよい」に緩める変異が黙った)。場面を 1 つ足して GO。" % (
        seal_test_count(), len(SG.MUTANTS) + len(SG.INCREMENT_MUTANTS), len(SG.MUTANTS), len(SG.INCREMENT_MUTANTS), len(SG.SILENT_BY_DESIGN)))
    w(u"- 残った穴 1 つは頭の補足に書いた。")
    w(u"- 記録の監査: 63 組の全部を別の実装で数え直し、組ごとの欄 3465 項目で差は 0。予測に要る数 10 本・集計・旗も導き直して同じ。")
    w(u"- 実装の途中の事故: 変異の 1 本が本物の木に file を 2 回書いた。実装の席が消し、門は前後の sha256 を見る形に直した。commit した木には残っていない。")
    w(u"")
    w(u"## §5 読みと次(封 §6 の決めどおり)")
    w(u"")
    s6 = seal_s6_lines(c.seal)
    both = u"この便は両方とも外れ。" if (not j[u"XK0-1"][0] and not j[u"XK0-6"][0]) else u"この便はどちらかが外れ。"
    if hit_both:
        w(u"- 封 §6 の決め: XK0-1 と XK0-6 が両方当たりなので、次の便の候補を 3 つ示す(どれも別の封が先。選ぶのは人間):")
        for item in seal_candidates(s6):
            w(u"  - " + item + u"。")
    else:
        w(u"- 封 §6 の決め: XK0-1 と XK0-6 のどちらかが外れ → **次の便の候補は示さない。** 新しい名・枠の無い行の中身を読むのが先。%s" % both)
    p1, p6, p5 = pn[u"XK0-1"], pn[u"XK0-6"], pn[u"XK0-5"]
    w(u"- 記録から言えること: 去年の型と対応表を持っていたとして、科目の名の %s%%・数の行の枠の %s%% は今年に在った(上限)。今年の数の行の %s%% は去年の値がそのまま使えた。残りは今年、入れる行。" % (
        pct(*p1), pct(*p6), pct(*p5)))
    st = cached(c, u"st", lambda: stat_values(rec))
    w(u"- 記録から言えないこと: 会社がその残りを埋められるか。持ち越せない名・枠が、会社にとって決めやすいものか。組による差(最小 %s%%・%s%%)が何から来るか。" % (st[u"keep"][0], st[u"frame"][0]))
    w(u"- 続けるか・どの向きへ続けるかは人間が決める。")
    return L


def seal_test_count():
    n = 0
    for case in unittest.defaultTestLoader.loadTestsFromModule(SG):
        n += case.countTestCases()
    return n


SEAL_TESTS = {}


def seal_tests():
    if u"n" not in SEAL_TESTS:
        SEAL_TESTS[u"n"] = seal_test_count()
    return SEAL_TESTS[u"n"]


def sec3_text(c):
    return section(c.doc, u"## §3 ", u"## §4 ")


def render_doc(c):
    pre = cached(c, u"pre", lambda: render_pre(c))
    post = cached(c, u"post", lambda: render_post(c))
    return pre + sec3_text(c).rstrip(u"\n").split(u"\n") + [u""] + post


def lines_problems(c):
    u"""文書の §3 以外の全部の行が、記録と字から組み直した行と同じ(1 字でも違えば赤)。"""
    want = render_doc(c)
    got = c.doc.rstrip(u"\n").split(u"\n")
    out = []
    for i, (x, y) in enumerate(zip(want, got), 1):
        if x != y:
            out.append(u"文書の %d 行目が記録から組んだ行と違う: %s" % (i, y[:30]))
    if len(want) != len(got):
        out.append(u"文書の行数 %d が組み直した行数 %d と違う" % (len(got), len(want)))
    return out


def outside_sec3(c):
    return c.doc.replace(sec3_text(c), u"")


def sec4_text(c):
    return section(c.doc, u"## §4 ", u"## §5 ")


def derived_numbers(c):
    u"""記録から導ける数(文書の §3 以外の数はこの内か字で留めた境の数)。render_doc とは別に、記録の整数・組ごとから作る。"""
    rec = c.rec
    out = set()
    for k in GROUPS:
        ints_in(rec[K_SUM][k], out)
    ints_in(rec[PRED_KEY], out)
    ints_in(rec[FLAG_KEY], out)
    st = stat_values(rec)
    for key in (u"keep", u"new", u"frame", u"noframe", u"diff"):
        for x in st[key]:
            out.add(str(x))
    out |= set([str(st[u"cur_noframe"]), str(st[u"not_same"]), str(st[u"old_nosame"])])
    g = st[u"judge"]
    out |= set([str(s4(g[u"今年の行の期の区分"][KN])), str(s4(g[u"同じ行(日)"][KN])), str(s4(g[u"枠が在る行"][KN])), str(s4(g[u"同じ行(日)"][KN], OLD2)), str(s4(g[u"今年の行の期の区分"][KN], OLD2)),
                str(s4(g[u"枠が在る行"][KT])), str(g[u"型の行"][u"今年"][KT])])
    out |= set(pct(a, b) for a, b in pred_numbers(rec).values() if b)
    out |= set([pct(g[u"名が足りる行"][KT], g[u"型の行"][u"今年"][KT])])
    out |= set([str(rec[u"材料"][u"今年の側の書類の本数"]), str(rec[u"材料"][u"除いた今年の書類の数"]), str(rec[K_DOCS][-1][u"番号"]), str(MS.SEEN_MAX_NO)])
    out |= set(str(v) for v in (seal_tests(), len(SG.MUTANTS) + len(SG.INCREMENT_MUTANTS), len(SG.MUTANTS), len(SG.INCREMENT_MUTANTS), len(SG.SILENT_BY_DESIGN)))
    out |= set(AUDIT_ONLY) | set(DOC_COMMITS)
    out |= set(STRUCTURAL) | RESIDUAL_OK
    return out


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
    u"""組み直した行と同じ行を文書から除いた残りの数は、字で留めた境の数と commit の内(組み直しと文書の両方を同じに書き換えても残る見張り)。"""
    want = set(render_doc(c))
    rest = [ln for ln in outside_sec3(c).splitlines() if ln not in want]
    out = []
    allowed = RESIDUAL_OK | set(STRUCTURAL) | set(DOC_COMMITS)
    for ln in rest:
        for tok in doc_number_tokens(ln):
            if tok.replace(u",", u"") not in allowed:
                out.append(u"組み直した行に無い行の数 %s が留めた境の数の外: %s" % (tok, ln[:24]))
    return out


def sanity_problems(c):
    u"""文書の静的な言い切り(組み直した行の数以外の字)が記録の数に合う。"""
    rec = c.rec
    st = stat_values(rec)
    train, judge_docs = split_docs(rec)
    g = st[u"judge"]
    ta = st[u"train"]
    out = []
    pj = pred_numbers(rec)
    ptr = collections.OrderedDict()
    tg = agg_of(train)[u"数"]
    ptr[u"XK0-1"] = (tg[u"対応表の名"][u"科目"][u"持ち越せる"], tg[u"対応表の名"][u"科目"][u"今年"])
    ptr[u"XK0-2"] = (tg[u"名が足りる行"][KN], tg[u"型の行"][u"今年"][KN])
    ptr[u"XK0-3"] = (s4(tg[u"同じ行(日)"][KN], OLD2), s4(tg[u"今年の行の期の区分"][KN], OLD2))
    ptr[u"XK0-6"] = (s4(tg[u"枠が在る行"][KN]), tg[u"型の行"][u"今年"][KN])
    for k, (a, b) in ptr.items():
        if not (Fraction(a, b) > Fraction(pj[k][0], pj[k][1])):
            out.append(u"文書の「頭の 3 組は持ち越しやすい側に寄っていた」が記録と合わない(%s: 訓練の率が判定の率より高くない)" % k)
    for k in (u"XK0-1", u"XK0-2", u"XK0-6"):
        a, b = ptr[k]
        if not (100 * a >= {u"XK0-1": 96, u"XK0-2": 97, u"XK0-6": 95}[k] * b):
            out.append(u"文書の「判定の 60 組では高すぎた」の対比に使う頭の 3 組の率が境に届いていない(%s)" % k)
    if not (all(d[u"対応表の名"][u"科目"][u"今年"] > 0 for d in rec[K_DOCS]) and st[u"new"][3] == 0):
        out.append(u"文書の「科目の名が 0 の組は無かった」「新しい科目の名が 0 の組は無い」が記録と合わない")
    if not (g[u"今年の行の期の区分"][KT][u"それより前"] == 0 and g[u"枠が在る行"][KT][u"それより前"] == 0 and g[u"同じ行(日)"][KT][u"当期"] == 0 and g[u"同じ行(日)"][KT][u"提出日"] == 0
            and g[u"同じ行(日)"][KT][u"それより前"] == 0):
        out.append(u"文書の「今年の文の行」の言い切り(それより前 0・同じ行(日)は前期だけ)が記録と合わない")
    if not (g[u"同じ行(日)"][KN][u"当期"] == 0 and g[u"同じ行(日)"][KN][u"提出日"] == 0):
        out.append(u"文書の「当期と提出日の行は、作りから同じ行が前の年に無い」が記録と合わない")
    if rec[K_SUM][G_JUDGE][u"断った組"] != 0:
        out.append(u"文書の「断った組は 0」が記録と合わない")
    if rec[u"材料"][u"今年の側の書類の本数"] != DOC67 or rec[K_DOCS][-1][u"番号"] != DOC67:
        out.append(u"文書の「番号は 67 まで在る」が記録と合わない")
    if not (MS.SEEN_MAX_NO == 3 and u"番号 1・2・3 が訓練の 3 組、番号 4〜63 が判定の 60 組" in c.seal):
        out.append(u"文書の補足(封は「番号 4〜63」・実装は「番号が 3 より大きい組」)が封・script と合わない")
    flag_pop = {FLAG_KEYS[0]: u"(63 組)", FLAG_KEYS[1]: u"判定の 60 組", FLAG_KEYS[2]: u"判定の 60 組", FLAG_KEYS[3]: u"(63 組", FLAG_KEYS[4]: u"(判定の 60 組)", FLAG_KEYS[5]: u"(63 組)"}
    for k, w in flag_pop.items():
        if w not in k:
            out.append(u"文書の「旗の母集団(旗 1・4・6 は 63 組・旗 2・3・5 は判定の 60 組)」が旗の欄の名と合わない")
    if list(rec[K_DOCS][0]).count(u"旗用の数") != 1:
        out.append(u"記録の「旗用の数」の欄が無い")
    if not (st[u"new"][3] == 0 and st[u"keep"][4] == pj[u"XK0-9"][0]):
        out.append(u"文書の「95% 以上の組は 45」が XK0-9 の数と合わない")
    if not (st[u"old_nosame"] == st[u"judge"][u"今年の行の期の区分"][KN][u"前期"] + st[u"judge"][u"今年の行の期の区分"][KN][u"それより前"] - s4(g[u"同じ行(日)"][KN])):
        out.append(u"導いた数(同じ行が無い行)が組ごとの数と合わない")
    return out


def sec3_problems(c):
    u"""§3 は記録に欄の無い読み(監査の席の読み)の節。数は記録に縛らず、見出し・「測った数ではない」・字で留めた数の並び・記録から導ける数(1147・4154・8・782・251 と足して合う内訳)・
    §3 の主張が外に出ないこと・語の留めを縛る。"""
    s = sec3_text(c)
    out = []
    if u"記録に欄の無い読み" not in s.splitlines()[0]:
        out.append(u"§3 の見出しが「記録に欄の無い読み」でない")
    if u"測った数ではない" not in s.splitlines()[0]:
        out.append(u"§3 の見出しに「測った数ではない」が無い")
    bullets = [ln for ln in s.splitlines()[1:] if ln.startswith(u"- ")]
    if len(bullets) != len(SEC3_LINES):
        out.append(u"§3 の箇条の数 %d が留めた行の数 %d と違う" % (len(bullets), len(SEC3_LINES)))
    toks = {}
    for key, nums in SEC3_LINES:
        hit = [ln for ln in bullets if key in ln]
        if len(hit) != 1:
            out.append(u"§3 に鍵の句の行が 1 つでない(%d 行): %s" % (len(hit), key[:16]))
            continue
        got = tuple(doc_number_tokens(hit[0]))
        toks[key] = got
        if got != tuple(nums):
            out.append(u"§3 の行 %s の数の並び %s が留めた並び %s と違う" % (key[:12], u",".join(got), u",".join(nums)))
    for ln in bullets:
        if not any(key in ln for key, _ in SEC3_LINES):
            out.append(u"§3 に留めていない行: %s" % ln[:20])
    for p in SEC3_PHRASES:
        if p not in plain(s):
            out.append(u"§3 に字が無い: %s" % p)
    st = stat_values(c.rec)
    PN = st[u"judge"]
    try:
        a1147, a901, a78, a154, a14 = [int(x) for x in toks[SEC3_LINES[0][0]]]
        a4154, a2252, a774, a1128, b1128 = [int(x) for x in toks[SEC3_LINES[1][0]]]
        a8, a2 = [int(x) for x in toks[SEC3_LINES[2][0]]]
        a782, a3 = [int(x) for x in toks[SEC3_LINES[3][0]]]
        a251, a1 = [int(x) for x in toks[SEC3_LINES[4][0]]]
        if a1147 != st[u"old_nosame"] or a901 + a78 + a154 + a14 != a1147:
            out.append(u"§3 の 1147(前期かそれより前で同じ行が無い行)が記録から導いた数・内訳の和と合わない")
        if a4154 != st[u"noframe"][0] or a2252 + a774 + a1128 != a4154 or a1128 != b1128:
            out.append(u"§3 の 4154(枠が無い行)が記録から導いた数・内訳の和と合わない")
        if a8 != PN[u"同じ行の中身(数)"][CONTENT4[1]] or a782 != PN[u"同じ行の中身(数)"][CONTENT4[2]] or a251 != PN[u"対応表の名"][u"科目"][u"新しい・_cor で終わらない"]:
            out.append(u"§3 の 8・782・251 が記録の数と合わない")
        if (a2, a3, a1) != (2, 3, 1):
            out.append(u"§3 の 2・3・1 が字で留めた値と違う")
    except (KeyError, ValueError, IndexError):
        out.append(u"§3 の数が読めない")
    rest = outside_sec3(c)
    for p in SEC3_ONLY_PHRASES:
        if p in rest:
            out.append(u"記録に欄の無い §3 の主張「%s」が §3 の外に出ている" % p)
    only3 = [u"901", u"154", u"14", u"2252", u"774", u"1128"]      # 78 は記録から導ける数(1 組の最大)と重なる。この 6 つは記録のどこにも無い
    derived = derived_numbers(c)
    for t in only3:
        if t in derived:
            out.append(u"§3 だけの数 %s が記録から導ける数と重なっている(門の留めが古い)" % t)
        if t in [x for ln in rest.splitlines() for x in doc_number_tokens(ln)]:
            out.append(u"§3 だけの数 %s が §3 の外に出ている" % t)
    return out


def sec4_problems(c):
    u"""§4 の 30・277・265・12・8 は封の門の本数に縛る(render が組み直す)。3465 は記録に無い数なので、§4 の外に出ないことだけを見る。"""
    out = []
    s4t = sec4_text(c)
    for t in AUDIT_ONLY:
        if t not in [x for x in doc_number_tokens(s4t)]:
            out.append(u"§4 に監査の席の数 %s が無い" % t)
        if t in [x for ln in outside_sec4(c).splitlines() for x in doc_number_tokens(ln)]:
            out.append(u"監査の席の数 %s が §4 の外に出ている" % t)
    if (len(SG.MUTANTS), len(SG.INCREMENT_MUTANTS), len(SG.SILENT_BY_DESIGN), seal_tests()) != (265, 12, 8, 30):
        out.append(u"封の門の本数(変異 265・掃く形 12・同値 8・試験 30)が文書の §4 の数と違う")
    return out


def outside_sec4(c):
    return c.doc.replace(sec4_text(c), u"")


def affirm_problems(c):
    u"""「作れる」「専用の道具が要らない」「人が書ける」「入力が半分で済む」「誤りが無くなる」「会社が型を埋められる」「検査に通る」は、言えないことの引用(「…」の中)・否定の中にしか無い。引用の在る行には「言えない」か「読まない」が在る。"""
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
    return [u"文書に要点の字が無い: %s" % p for p in PHRASES + MAIN_CLAIMS if p not in doc]


def head_problems(c):
    head = plain(c.doc.split(u"## §1")[0])
    out = [u"文書の頭(§1 の前)に無い: %s" % p for p in HEAD_PHRASES if p not in head]
    sec7 = section(c.seal, u"## §7 ", None)
    lim7 = [ln[2:] for ln in sec7.splitlines() if ln.startswith(u"- ")]
    if len(lim7) != 6:
        out.append(u"封 §7 の限界の行が 6 本でない")
    hlines = head.splitlines()
    for i, lim in enumerate(lim7, 1):
        frags = [x for x in lim.split(u"。") if x]
        if not any(all(x in ln for x in frags) for ln in hlines):
            out.append(u"封 §7 の %d 本目の限界が文書の頭の 1 つの行に揃って無い: %s" % (i, lim[:16]))
    # 封 §6 の読み方 4 つ
    for p in (u"「会社が型を埋められる」とは読まない", u"その値が正しいことは言わない", u"鍵が同じでも、指すものが同じとは限らない", u"名の数の下限ではない"):
        if p not in head:
            out.append(u"封 §6 の読み方の字が文書の頭に無い: %s" % p)
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
    (u"verdict", verdict_problems), (u"numbers", doc_number_problems), (u"lines", lines_problems), (u"resid", residual_problems), (u"sanity", sanity_problems),
    (u"sec3", sec3_problems), (u"sec4", sec4_problems), (u"affirm", affirm_problems), (u"phrases", phrase_problems), (u"head", head_problems), (u"forbidden", forbidden_problems),
    (u"commits", doc_commit_problems)])


# ======================================================================================================
def blob_problems(root, prefix, at):
    return WG.blob_problems(root, prefix, at)


def commit_problems(root=REPO):
    u"""文書が書く 3 つの commit が実の履歴と合う: 封は 1fc4c736・script と封の門は aaeeb21c・記録は 1392a222。commit の message が文書の言う「REVISE」「独立監査 GO」「差は 0」を書いている。"""
    out = []
    for rel, want in HISTORY.items():
        r = subprocess.run(["git", "-C", root, "log", "--format=%H", "--reverse", "--", PREFIX + rel], stdout=subprocess.PIPE, universal_newlines=True)
        got = [x for x in r.stdout.split() if x]
        if len(got) != len(want) or any(not g.startswith(w) for g, w in zip(got, want)):
            out.append(u"%s の履歴が文書の書く commit %s と違う" % (rel, u"・".join(want)))
    for short, words in ((SCRIPT_COMMIT_SHORT, (u"独立監査 REVISE(門の穴 1 つ)→ 直し → GO", u"同値 8 本", u"変異 277 本が赤", u"旗 2 の「100%」を 95% に緩める変異は場面が小さく黙る")),
                         (RECORD_COMMIT_SHORT, (u"独立監査 GO", u"63 組の全部を別の実装で数え直して差は 0"))):
        r = subprocess.run(["git", "-C", root, "log", "-1", "--format=%B", short], stdout=subprocess.PIPE, universal_newlines=True)
        for w in words:
            if w not in r.stdout:
                out.append(u"commit %s の message に「%s」が無い" % (short, w))
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
(変異を実行する前に書いた予測。右 = 赤になるべき検査。「整合」= 組ごとの数から集計・予測・旗を作り直し、recount は緑のまま当たり外れ・向きだけが変わる)
固定の変異 F1〜: 記録・封・文書の 1 か所を替える。右の検査が赤。
F1  記録の sha256 の写しを違う値に                                                       -> sha
F2  記録の「この script の sha256」を 1 字替える                                         -> sha
F3  記録の限界の欄の 1 行を消す                                                          -> sha
F4  記録の封の commit の欄を 1 字替える                                                  -> sha
F5  記録の step の欄を 1 字替える                                                        -> sha
F6  封の写しの sha256 の写しを違う値に / 便 XM0 の記録の sha256 の写しを違う値に          -> sha
F7  記録の材料の組の数 63 → 62                                                          -> recount
F8  記録の材料の便 XM0 の記録の sha256 を 1 字替える                                       -> recount
F9  組 20 の対応表の名(科目)の持ち越せるを 1 増やす(集計は直さない)                          -> recount
F10 集計の判定の 60 組の「科目の持ち越せる」を 1 増やす(組ごとは直さない)                     -> recount
F11 組 6 の同じ行の中身の「全部同じ」を 1 増やす(同じ行(日)は直さない)                       -> recount
F12 組 5 の断った年に字を入れる(断ったは False のまま)                                      -> recount
F13 組 7 の逆向きの同じ鍵(日)を 1 増やす(集計は直さない)                                    -> recount
F14 予測の欄 XK0-3 の数を 1 増やす                                                        -> recount
F15 組の番号 5 を 99 にする                                                               -> recount
F16 集計の全部の 63 組の枠が在る行(数・当期)を 1 増やす                                     -> recount
F17 集計の訓練の 3 組と判定の 60 組を入れ替える                                              -> recount
F18 旗の欄の「旗 3」の旗を反転する                                                        -> recount
F19 記録に docid の欄を足す                                                               -> clean
F20 記録に EDINET コードの形の字を足す                                                     -> clean
F21 記録に日付の形の字を足す                                                               -> clean
F22 封の写しから XK0-3 の境の字を消す                                                      -> bound
F23 封の写しから §6 の (iii) の候補の字を消す                                              -> bound
F24 封の写しから §7 の限界の 1 本を消す                                                    -> bound
F25 封の写しから §0 の頭の 3 組の数(1499・1460)を消す                                       -> bound
整合の変異 C1〜: recount は緑のまま、文書が合わなくなる(verdict・lines)。
C1  XK0-1 を当たりにする(判定の 60 組の科目の持ち越しを 97% に)                               -> verdict
C2  XK0-2 を当たりにする(名が足りる行を全部に)                                               -> verdict
C3  XK0-3 を当たりにする(前期・それより前の同じ行を全部に)                                    -> verdict
C4  XK0-4 を外れにする(下: 全部同じを 5% 動かす)                                             -> verdict
C5  XK0-4 を外れにする(上: 全部同じ 100%)                                                    -> verdict
C6  XK0-5 を外れにする(下: 全部同じを減らす)                                                 -> verdict
C7  XK0-5 を外れにする(上: 当期にも同じ行を入れる)                                           -> verdict
C8  XK0-6 を当たりにする(枠が在る行を全部に)                                                 -> verdict
C9  XK0-7 を外れにする(_cor で終わる新しい名を 0 に)                                         -> verdict
C10 XK0-8 を外れにする(判定の 60 組のうち 4 組を断る)                                         -> verdict
C11 XK0-9 を当たりにする(5 組を 97% に)                                                      -> verdict
C12 XK0-10 を当たりにする(全部同じだけの 7 組に 1 行ずつ違う行を足す)                          -> verdict
C13 旗 1: 当期に同じ行(日)を 1 つ入れる                                                      -> verdict
C14 旗 2: 判定の 60 組の全部で科目の名の持ち越しを 100% に                                    -> verdict
C15 旗 3: 判定の 60 組の同じ行(数)を 0 に                                                    -> verdict
C16 旗 5: 判定の 60 組のうち 6 組を断る                                                       -> verdict
C17 旗 6: 便 XM0 の記録の型の行の数を 1 組だけ 1 増やす                                        -> verdict
C18 XK0-1 だけを外れ側に保ち XK0-6 と XK0-1 を両方当たりにする(文書の「示さない」と合わなくする) -> verdict(封 §6 の決め)
C19 整合: 組による差を消す(全部の組の科目の持ち越しを同じ率に。「組による差が大きい」と合わない) -> lines
C20 整合: 頭の 3 組の率を判定の 60 組より低くする                                              -> sanity
文書の固定の変異 D1〜: 右の検査が赤。
D1  判定の「外れ」「当たり」を行ごとに入れ替える(10 行の全部。掃き)                              -> verdict
D2  頭の「主の予測(XK0-1)を含む 6 本は外れ」を「5 本」に                                      -> verdict・lines
D3  頭の「当たり 4・外れ 6」を「当たり 5・外れ 5」に                                          -> verdict・lines
D4  「どちらの年の型も対応表も答えから作った」を「…答えから作っていない」に                       -> lines
D5  「持ち越しは上限」を「持ち越しは下限」に                                                  -> lines
D6  「判定の 60 組では高すぎた」を「…低すぎた」に                                              -> lines
D7  「合計の率は 1 つの会社について言える数ではない」を「…言える数だ」に                          -> lines
D8  §5 に「(i)」の候補を足す                                                                 -> verdict
D9  §5 に候補の見出しの無い案の 1 行を足す(「第 1 版」「次の便の候補」)                         -> verdict
D10 §5 の「次の便の候補は示さない」を消す                                                     -> verdict
D11 §5 の「続けるか・どの向きへ続けるかは人間が決める」を消す                                  -> verdict・lines
D12 頭の限界の 1 本を消す(全部の組。掃き)                                                    -> head
D13 頭の限界の文を 1 つ消す(全部の文。掃き)                                                  -> head
D14 引用の外に「XBRL を作れる。」「会社が型を埋められる。」「専用の道具が要らない。」「入力が半分で済む。」「誤りが無くなる。」「EDINET の検査に通る。」を足す(掃き)    -> affirm
D15 引用の行から「言えない」「読まない」を全部消す                                             -> affirm
D16 文書に「保証」を足す・docID の形を足す・commit の字を替える・知らない commit の字を足す      -> forbidden・commits
D17 §3 の見出しの「記録に欄の無い読み」を消す・「測った数ではない」を消す・§3 の数を替える・§3 の主張を §2 に写す・3465 を §3 に写す      -> sec3・sec4
D18 補足を 1 本消す(6 本の全部。掃き)・§4 の 3465 を替える・§4 の 277 を替える                       -> lines・sec4
掃き(SWEEPS。文書の全部に 1 か所ずつ当てる。1 つでも黙れば報告):
W1  文書の全部の数(§3 を含む)を、(a) 1 増やす (b) 同じ文書の別の所の数に替える (c) §3 の数に替える          -> 全部赤(lines か sec3)
W2  向きの語(以上/以下/未満・多い/少ない・全部/一部・当たり/外れ・在る/無い・今年/前の年 など)を、出た所ごとに反対に -> 全部赤
W3  「60 組」「63 組」「3 組」の数を互いに取り違える・59122/58382/27829/28976/27104 を互いに取り違える     -> 全部赤
W4  §3 の数・主張を §2 に 1 行として足す(全部)                                              -> 全部赤(lines・numbers・sec3)
W5  表の 1 セルを、同じ表の別の行の同じ列のセルへ替える(§1 の表・§2 の表の全部のセル。当たり外れの行の入れ替えを含む)    -> 全部赤
W6  §3 の外の全部の行を 1 行ずつ消す・全部の文を 1 つずつ消す・「・」でつないだ節を 1 つずつ消す        -> 全部赤
W7  記録の全部の整数・小数・旗の葉(集計 3 つ・予測・旗・組の代表 7 つ分)を 1 増やす・旗を反転する          -> 全部赤(recount)
W8  §3 の文を 1 つずつ消す・向きの語を反対に                                                   -> 黙る所が在りうる(§3 の中の括弧の例示と、SEC3_PHRASES に無い言い回し)。黙った所は報告
予測の自己点検: 黙るとすれば W8(§3 は形で縛るため)と、W5 で「同じ文字列のセル」に替わる場合(スキップ)・W2 の「だけ→も」「より→と同じ」のような意味を変えない置換。W1〜W7 の他に黙りは無いと予測する。
"""

ORDER_DOC = (u"lines", u"verdict", u"numbers", u"resid", u"sec3", u"sec4", u"affirm", u"phrases", u"head", u"forbidden", u"commits", u"sanity", u"bound", u"clean", u"sha", u"recount")
ORDER_REC = (u"sha", u"recount", u"verdict", u"lines", u"sanity", u"clean", u"bound", u"numbers", u"resid", u"sec3", u"sec4", u"affirm", u"phrases", u"head", u"forbidden", u"commits")


def first_red(c, order):
    for k in order:
        if guard(CHECKS[k], c):
            return k
    return None


def rep(c, old, new, attr="doc", count=1):
    s = getattr(c, attr)
    assert old in s, old
    setattr(c, attr, s.replace(old, new, count))


def add_doc(c, text):
    c.doc = c.doc + u"\n" + text + u"\n"


def drop_seal(c, phrase):
    assert phrase in c.seal, phrase
    c.seal = c.seal.replace(phrase, u"X", 1)


def doc_at(rec, n):
    return [d for d in rec[K_DOCS] if d[u"番号"] == n][0]


# ---- 記録を整合して作り直す変異の道具
def rebuild(c):
    rec = c.rec
    train, judge_docs = split_docs(rec)
    rec[K_SUM][G_TRAIN] = agg_of(train)
    rec[K_SUM][G_JUDGE] = agg_of(judge_docs)
    rec[K_SUM][G_ALL] = agg_of(rec[K_DOCS])
    rec[PRED_KEY] = pred_expected(rec)
    rec[FLAG_KEY] = flags_expected(rec, c.xm0)
    c.cache = {}


def each_judge(c, fn):
    for d in c.rec[K_DOCS]:
        if d[u"番号"] > TRAIN_COUNT and not d[u"断った"]:
            fn(d)
    rebuild(c)


def first_judge(c, n, pred, fn):
    u"""判定の 60 組の断らなかった組のうち pred を満たす最初の n 組に fn を当てる。"""
    k = 0
    for d in c.rec[K_DOCS]:
        if d[u"番号"] > TRAIN_COUNT and not d[u"断った"] and pred(d) and k < n:
            fn(d)
            k += 1
    assert k == n, (k, n)
    rebuild(c)


def set_keep(d, num, den):
    x = d[u"対応表の名"][u"科目"]
    k = min(x[u"今年"], -(-x[u"今年"] * num // den))
    x[u"持ち越せる"] = k
    x[u"新しい"] = x[u"今年"] - k
    x[u"新しい・_cor で終わる"] = x[u"新しい"]
    x[u"新しい・_cor で終わらない"] = 0


def names_all(d):
    for k in (KN, KT):
        d[u"名が足りる行"][k] = d[u"型の行"][u"今年"][k]


def move_same(d, cls, to):
    u"""数の行の期の区分 cls の同じ行(日)を to にする(全部同じに足す・逆向きを揃える)。"""
    cur = d[u"同じ行(日)"][KN][cls]
    delta = to - cur
    d[u"同じ行(日)"][KN][cls] = to
    d[u"同じ行の中身(数)"][CONTENT4[0]] += delta
    d[u"逆向き"][KN][u"同じ鍵(日)が今年に在る"] += delta


def move_content(d, frm, to, n):
    n = min(n, d[u"同じ行の中身(数)"][frm])
    d[u"同じ行の中身(数)"][frm] -= n
    d[u"同じ行の中身(数)"][to] += n


def set_frame_full(d):
    for k in (KN, KT):
        target = min(d[u"型の行"][u"今年"][k], d[u"型の行"][u"前の年"][k])
        names_all(d)
        rest = target
        for c_ in CLASS4:
            t = min(d[u"今年の行の期の区分"][k][c_], rest)
            d[u"枠が在る行"][k][c_] = t
            rest -= t
        back = d[u"逆向き"][k]
        back[u"同じ鍵(枠)が今年に在る"] = target
        back[u"今年、要らなくなった枠"] = back[u"前の年の行"] - target


def decline_doc(d, year=u"前の年"):
    for k in list(d):
        if k in (u"番号", u"断った", u"断った年", u"断った理由", u"旗用の数"):
            continue
        d[k] = zero_tree(d[k])
    d[u"断った"] = True
    d[u"断った年"] = year
    d[u"断った理由"] = u"書類の決めが 1 通りに決まらない"


def zero_tree(o):
    if isinstance(o, dict):
        return collections.OrderedDict((k, zero_tree(v)) for k, v in o.items())
    if isinstance(o, bool):
        return False
    if isinstance(o, (int, float)):
        return 0
    return o


def m_k1_hit(c):
    each_judge(c, lambda d: set_keep(d, 97, 100))


def m_k2_hit(c):
    each_judge(c, names_all)


def m_k3_hit(c):
    def fn(d):
        names_all(d)
        for c_ in OLD2:
            move_same(d, c_, d[u"今年の行の期の区分"][KN][c_])
    each_judge(c, fn)


def m_k4_low(c):
    each_judge(c, lambda d: move_content(d, CONTENT4[0], CONTENT4[2], sum(d[u"同じ行の中身(数)"].values()) * 5 // 100 + 1))


def m_k4_100(c):
    def fn(d):
        for k in CONTENT4[1:]:
            move_content(d, k, CONTENT4[0], d[u"同じ行の中身(数)"][k])
    each_judge(c, fn)


def m_k5_low(c):
    each_judge(c, lambda d: move_content(d, CONTENT4[0], CONTENT4[2], d[u"型の行"][u"今年"][KN] * 4 // 100 + 1))


def m_k5_high(c):
    def fn(d):
        names_all(d)
        move_same(d, u"当期", d[u"今年の行の期の区分"][KN][u"当期"])
    each_judge(c, fn)


def m_k6_hit(c):
    each_judge(c, set_frame_full)


def m_k7_miss(c):
    def fn(d):
        x = d[u"対応表の名"][u"科目"]
        x[u"新しい・_cor で終わらない"] = x[u"新しい"]
        x[u"新しい・_cor で終わる"] = 0
    each_judge(c, fn)


def m_k8_declined4(c):
    first_judge(c, 4, lambda d: True, decline_doc)


def m_k9_hit(c):
    first_judge(c, 5, lambda d: 100 * d[u"対応表の名"][u"科目"][u"持ち越せる"] < 95 * d[u"対応表の名"][u"科目"][u"今年"], lambda d: set_keep(d, 97, 100))


def m_k10_hit(c):
    first_judge(c, 7, lambda d: sum(d[u"同じ行の中身(数)"].values()) == d[u"同じ行の中身(数)"][CONTENT4[0]] and d[u"同じ行の中身(数)"][CONTENT4[0]] > 0,
                lambda d: move_content(d, CONTENT4[0], CONTENT4[2], 1))


def m_f1(c):
    def fn(d):
        names_all(d)
        move_same(d, u"当期", 1)
    first_judge(c, 1, lambda d: True, fn)


def m_f2(c):
    def fn(d):
        x = d[u"対応表の名"][u"科目"]
        x[u"持ち越せる"] = x[u"今年"]
        x[u"新しい"] = 0
        x[u"新しい・_cor で終わる"] = 0
        x[u"新しい・_cor で終わらない"] = 0
    each_judge(c, fn)


def m_f3(c):
    def fn(d):
        for c_ in CLASS4:
            move_same(d, c_, 0)
        d[u"同じ行の中身(数)"] = collections.OrderedDict((k, 0) for k in CONTENT4)
    each_judge(c, fn)


def m_f5(c):
    first_judge(c, 6, lambda d: True, decline_doc)


def m_f6(c):
    by_no = dict((x[u"番号"], x) for x in c.xm0[K_DOCS])
    by_no[10][u"型の行"][KN] += 1
    rebuild(c)


def m_xm01_hit_only(c):
    m_k1_hit(c)
    m_k6_hit(c)


def m_no_variation(c):
    each_judge(c, lambda d: set_keep(d, 96, 100))


def m_train_low(c):
    for d in c.rec[K_DOCS]:
        if d[u"番号"] <= TRAIN_COUNT:
            x = d[u"対応表の名"][u"科目"]
            x[u"持ち越せる"] = x[u"今年"] // 2
            x[u"新しい"] = x[u"今年"] - x[u"持ち越せる"]
            x[u"新しい・_cor で終わる"] = x[u"新しい"]
            x[u"新しい・_cor で終わらない"] = 0
    rebuild(c)


def swap_lines(c, a, b):
    ls = c.doc.split(u"\n")
    ia = [i for i, ln in enumerate(ls) if a in ln][0]
    ib = [i for i, ln in enumerate(ls) if b in ln][0]
    ls[ia], ls[ib] = ls[ib], ls[ia]
    c.doc = u"\n".join(ls)


def inc(c, path, delta=1):
    o = c.rec
    for p in path[:-1]:
        o = o[p]
    o[path[-1]] += delta


def m_swap_groups(c):
    c.rec[K_SUM][G_TRAIN], c.rec[K_SUM][G_JUDGE] = c.rec[K_SUM][G_JUDGE], c.rec[K_SUM][G_TRAIN]


def m_flip_flag3(c):
    c.rec[FLAG_KEY][FLAG_KEYS[2]][u"旗"] = not c.rec[FLAG_KEY][FLAG_KEYS[2]][u"旗"]


MUTATIONS = (
    (u"F1 記録の sha256 の写しを違う値に", lambda c: c.shas.__setitem__(RECORD_REL, u"0" * 64), (u"sha",)),
    (u"F2 記録の script の sha256 を 1 字替える", lambda c: c.rec.__setitem__(u"この script の sha256", u"f" + c.rec[u"この script の sha256"][1:]), (u"sha",)),
    (u"F3 記録の限界の欄の 1 行を消す", lambda c: c.rec.__setitem__(u"限界", c.rec[u"限界"][1:]), (u"sha",)),
    (u"F4 記録の封の commit の欄を 1 字替える", lambda c: c.rec.__setitem__(u"封の commit", u"0" + c.rec[u"封の commit"][1:]), (u"sha",)),
    (u"F5 記録の step の欄を 1 字替える", lambda c: c.rec.__setitem__(u"step", c.rec[u"step"].replace(u"XK0", u"XK1", 1)), (u"sha",)),
    (u"F6a 封の写しの sha256 の写しを違う値に", lambda c: c.shas.__setitem__(SEAL_REL, u"0" * 64), (u"sha",)),
    (u"F6b 便 XM0 の記録の sha256 の写しを違う値に", lambda c: c.shas.__setitem__(XM0_RECORD_REL, u"0" * 64), (u"sha",)),
    (u"F7 記録の材料の組の数を 62 に", lambda c: c.rec[u"材料"].__setitem__(u"組の数", 62), (u"recount",)),
    (u"F8 記録の材料の便 XM0 の記録の sha256 を 1 字替える", lambda c: c.rec[u"材料"].__setitem__(u"便 XM0 の記録の sha256", u"0" + c.rec[u"材料"][u"便 XM0 の記録の sha256"][1:]), (u"recount",)),
    (u"F9 組 20 の科目の持ち越せるを 1 増やす(集計は直さない)", lambda c: doc_at(c.rec, 20)[u"対応表の名"][u"科目"].__setitem__(u"持ち越せる", doc_at(c.rec, 20)[u"対応表の名"][u"科目"][u"持ち越せる"] + 1), (u"recount",)),
    (u"F10 集計の判定の 60 組の科目の持ち越せるを 1 増やす", lambda c: inc(c, (K_SUM, G_JUDGE, u"数", u"対応表の名", u"科目", u"持ち越せる")), (u"recount",)),
    (u"F11 組 6 の同じ行の中身の全部同じを 1 増やす", lambda c: doc_at(c.rec, 6)[u"同じ行の中身(数)"].__setitem__(CONTENT4[0], doc_at(c.rec, 6)[u"同じ行の中身(数)"][CONTENT4[0]] + 1), (u"recount",)),
    (u"F12 組 5 の断った年に字を入れる", lambda c: doc_at(c.rec, 5).__setitem__(u"断った年", u"今年"), (u"recount",)),
    (u"F13 組 7 の逆向きの同じ鍵(日)を 1 増やす", lambda c: doc_at(c.rec, 7)[u"逆向き"][KN].__setitem__(u"同じ鍵(日)が今年に在る", doc_at(c.rec, 7)[u"逆向き"][KN][u"同じ鍵(日)が今年に在る"] + 1), (u"recount",)),
    (u"F14 予測の欄 XK0-3 の数を 1 増やす", lambda c: inc(c, (PRED_KEY, PK[2], u"数")), (u"recount",)),
    (u"F15 組の番号 5 を 99 にする", lambda c: doc_at(c.rec, 5).__setitem__(u"番号", 99), (u"recount",)),
    (u"F16 集計の全部の 63 組の枠が在る行(数・当期)を 1 増やす", lambda c: inc(c, (K_SUM, G_ALL, u"数", u"枠が在る行", KN, u"当期")), (u"recount",)),
    (u"F17 集計の訓練の 3 組と判定の 60 組を入れ替える", m_swap_groups, (u"recount",)),
    (u"F18 旗の欄の旗 3 を反転する", m_flip_flag3, (u"recount",)),
    (u"F19 記録に docid の欄を足す", lambda c: c.rec.__setitem__(u"docID", u"S100ABCD"), (u"clean",)),
    (u"F20 記録に EDINET コードの形の字を足す", lambda c: c.rec.__setitem__(u"メモ", u"E01234"), (u"clean",)),
    (u"F21 記録に日付の形の字を足す", lambda c: c.rec.__setitem__(u"メモ", u"2025-03-31"), (u"clean",)),
    (u"F22 封の写しから XK0-3 の境の字を消す", lambda c: drop_seal(c, u"期の区分が「前期」か「それより前」の数の行のうち、同じ行が前の年の型に在るのは 97% 以上"), (u"bound",)),
    (u"F23 封の写しから §6 の (iii) の候補の字を消す", lambda c: drop_seal(c, u"去年の型と XBRL でない今年の資料から、今年の当期の行を埋める"), (u"bound",)),
    (u"F24 封の写しから §7 の限界の 1 本を消す", lambda c: rep(c, u"\n- 型の外の fact は数えるだけで", u"\n型の外の fact は数えるだけで", attr="seal"), (u"bound",)),
    (u"F25 封の写しから §0 の頭の 3 組の数を消す", lambda c: drop_seal(c, u"今年 1499・前の年にも在る 1460"), (u"bound",)),
    (u"C1 XK0-1 を当たりにする", m_k1_hit, (u"verdict",)),
    (u"C2 XK0-2 を当たりにする", m_k2_hit, (u"verdict",)),
    (u"C3 XK0-3 を当たりにする", m_k3_hit, (u"verdict",)),
    (u"C4 XK0-4 を外れにする(下)", m_k4_low, (u"verdict",)),
    (u"C5 XK0-4 を外れにする(上: 100%)", m_k4_100, (u"verdict",)),
    (u"C6 XK0-5 を外れにする(下)", m_k5_low, (u"verdict",)),
    (u"C7 XK0-5 を外れにする(上)", m_k5_high, (u"verdict",)),
    (u"C8 XK0-6 を当たりにする", m_k6_hit, (u"verdict",)),
    (u"C9 XK0-7 を外れにする", m_k7_miss, (u"verdict",)),
    (u"C10 XK0-8 を外れにする", m_k8_declined4, (u"verdict",)),
    (u"C11 XK0-9 を当たりにする", m_k9_hit, (u"verdict",)),
    (u"C12 XK0-10 を当たりにする", m_k10_hit, (u"verdict",)),
    (u"C13 旗 1: 当期に同じ行(日)を入れる", m_f1, (u"verdict",)),
    (u"C14 旗 2: 全部の組で 100%", m_f2, (u"verdict",)),
    (u"C15 旗 3: 同じ行(数)が 0", m_f3, (u"verdict",)),
    (u"C16 旗 5: 6 組を断る", m_f5, (u"verdict",)),
    (u"C17 旗 6: 便 XM0 の記録の型の行の数を 1 組だけ替える", m_f6, (u"verdict",)),
    (u"C18 XK0-1 と XK0-6 を両方当たりにする(「示さない」と合わなくする)", m_xm01_hit_only, (u"verdict",)),
    (u"C19 整合: 組による差を消す", m_no_variation, (u"lines",)),
    (u"C20 整合: 頭の 3 組の率を判定の 60 組より低くする", m_train_low, (u"sanity",)),
    (u"D2 頭の「主の予測(XK0-1)を含む 6 本は外れ」を「5 本」に", lambda c: rep(c, u"**主の予測(XK0-1)を含む 6 本は外れ。**", u"**主の予測(XK0-1)を含む 5 本は外れ。**"), (u"verdict", u"lines")),
    (u"D3 頭の「当たり 4・外れ 6」を「当たり 5・外れ 5」に", lambda c: rep(c, u"判定した 10 本は 当たり 4・外れ 6", u"判定した 10 本は 当たり 5・外れ 5"), (u"verdict", u"lines")),
    (u"D4 「どちらの年の型も対応表も答えから作った」を「…作っていない」に", lambda c: rep(c, u"**どちらの年の型も対応表も答えから作った。**", u"**どちらの年の型も対応表も答えから作っていない。**"), (u"lines",)),
    (u"D5 「持ち越しは上限」を「持ち越しは下限」に", lambda c: rep(c, u"持ち越しは上限。**この便", u"持ち越しは下限。**この便"), (u"lines",)),
    (u"D6 「判定の 60 組では高すぎた」を「低すぎた」に", lambda c: rep(c, u"判定の 60 組では高すぎた", u"判定の 60 組では低すぎた"), (u"lines",)),
    (u"D7 「合計の率は 1 つの会社について言える数ではない」を「言える数だ」に", lambda c: rep(c, u"言える数ではない", u"言える数だ"), (u"lines",)),
    (u"D8 §5 に「(i)」の候補を足す", lambda c: add_doc(c, u"  - (i) 型の外の理由のうち fact がいちばん多いものを型の拡張で入れる第 1 版(0 USD。別の封が先)。"), (u"verdict",)),
    (u"D9 §5 に候補の見出しの無い案の 1 行を足す", lambda c: add_doc(c, u"- 次の便の候補は、第 1 版を作ること。"), (u"verdict",)),
    (u"D10 §5 の「次の便の候補は示さない」を消す", lambda c: rep(c, u"**次の便の候補は示さない。** ", u""), (u"verdict",)),
    (u"D11 §5 の「続けるか・どの向きへ続けるかは人間が決める」を消す", lambda c: rep(c, u"続けるか・どの向きへ続けるかは人間が決める", u"X"), (u"verdict", u"lines")),
    (u"D12 頭の限界(型の外の fact)の文を消す", lambda c: rep(c, u"型の外の fact は数えるだけで、持ち越しの分母に入らない。", u"X。"), (u"head", u"lines")),
    (u"D13 頭の「費用は 0 USD」を消す", lambda c: rep(c, u"費用は 0 USD", u"費用は 0"), (u"head", u"lines")),
    (u"D19 「記録から言えないこと」を消す", lambda c: rep(c, u"- 記録から言えないこと:", u"- X:"), (u"phrases", u"lines")),
    (u"D20 文書に「4999999%」の言い切りを足す", lambda c: add_doc(c, u"決まった fact は 4999999% だった。"), (u"numbers", u"resid")),
    (u"D15 引用の行から「言えない」「読まない」を全部消す", lambda c: setattr(c, "doc", u"\n".join((ln.replace(u"言えない", u"X").replace(u"読まない", u"X") if QUOTED.search(ln) else ln) for ln in c.doc.splitlines())), (u"affirm",)),
    (u"D16a 文書に「保証」を足す", lambda c: add_doc(c, u"保証する。"), (u"forbidden",)),
    (u"D16b 文書に docID の形を足す", lambda c: add_doc(c, u"S100ABCD"), (u"forbidden",)),
    (u"D16c 文書の commit の字 1392a222 を 1 字替える", lambda c: rep(c, u"1392a222", u"1392a223", count=100), (u"commits",)),
    (u"D16d 文書の commit の字 aaeeb21c を 1 字替える", lambda c: rep(c, u"aaeeb21c", u"aaeeb21d", count=100), (u"commits",)),
    (u"D16e 文書に知らない commit の字を足す", lambda c: add_doc(c, u"commit 1a2b3c4d。"), (u"commits",)),
    (u"D17a §3 の見出しの「記録に欄の無い読み」を消す", lambda c: rep(c, u"## §3 記録に欄の無い読み(", u"## §3 X("), (u"sec3",)),
    (u"D17b §3 の見出しの「測った数ではない」を消す", lambda c: rep(c, u"測った数ではない", u"X"), (u"sec3",)),
    (u"D17c §3 の外に「次元の名が前の年に無い」を足す", lambda c: add_doc(c, u"次元の名が前の年に無い行が在った。"), (u"sec3",)),
    (u"D17d §3 の 901 を 902 に", lambda c: rep(c, u"前の年に無い 901・", u"前の年に無い 902・"), (u"sec3",)),
    (u"D17e §3 の 1147 を 1148 に", lambda c: rep(c, u"で同じ行が無い 1147 行", u"で同じ行が無い 1148 行"), (u"sec3",)),
    (u"D17f §3 の 251 を 252 に", lambda c: rep(c, u"新しい科目の名 251 は", u"新しい科目の名 252 は"), (u"sec3",)),
    (u"D17g §3 の 4154 を 4155 に", lambda c: rep(c, u"枠が無い数の行 4154:", u"枠が無い数の行 4155:"), (u"sec3",)),
    (u"D17h §3 の「見つからなかった」を消す", lambda c: rep(c, u"見つからなかった", u"X"), (u"sec3",)),
    (u"D17i 3465 を §4 の外(§3)に足す", lambda c: rep(c, u"符号が逆のものが 3 行在った。", u"符号が逆のものが 3 行在った(3465)。"), (u"sec3", u"sec4")),
    (u"D18a §4 の 3465 を 3466 に", lambda c: rep(c, u"3465 項目", u"3466 項目"), (u"sec4", u"lines")),
    (u"D18b §4 の 277 を 278 に", lambda c: rep(c, u"変異 277 本", u"変異 278 本"), (u"lines",)),
    (u"D18c 補足の 1 本を消す(旗の母集団)", lambda c: rep(c, u"- **旗の母集団**", u"- **X**"), (u"lines",)),
)
# 記録を替えて作り直す(整合)変異の名(recount が緑のまま当たり外れ・向きだけが変わることを別の試験で見る)
CONSISTENT = (m_k1_hit, m_k2_hit, m_k3_hit, m_k4_low, m_k4_100, m_k5_low, m_k5_high, m_k6_hit, m_k7_miss, m_k8_declined4, m_k9_hit, m_k10_hit, m_f1, m_f2, m_f3, m_f5, m_f6, m_xm01_hit_only,
              m_no_variation, m_train_low)


def run_mutations(base=None):
    base = base or Ctx()
    out = []
    for name, fn, checks in MUTATIONS:
        doc_only = name.startswith(u"D")
        c = base.with_doc(base.doc) if doc_only else base.copy()
        if doc_only:
            c.cache = {}          # 文書だけの変異でも、組み直しの記憶は記録だけに依るので共有してよいが、念のため別に持つ
        fn(c)
        res = [(k, bool(guard(CHECKS[k], c))) for k in checks]
        out.append((name, res))
    return out


# ======================================================================================================
# 掃き: 文書・記録の全部の所に 1 か所ずつ当てる
NUM_RE = WG.NUM_RE
FLIPS = ((u"以上", u"以下"), (u"以下", u"以上"), (u"未満", u"以上"), (u"多い", u"少ない"), (u"少ない", u"多い"), (u"多く", u"少なく"), (u"少なく", u"多く"), (u"増", u"減"), (u"減", u"増"), (u"高", u"低"), (u"低", u"高"),
         (u"最小", u"最大"), (u"最大", u"最小"), (u"超える", u"満たない"), (u"満たない", u"超える"), (u"大きい", u"小さい"), (u"小さい", u"大きい"), (u"全部", u"一部"), (u"一部", u"全部"), (u"両方", u"片方"),
         (u"前の年", u"今年"), (u"今年", u"前の年"), (u"当たり", u"外れ"), (u"外れ", u"当たり"), (u"立たない", u"立つ"), (u"同じ", u"違う"), (u"違う", u"同じ"),
         (u"在る", u"無い"), (u"無い", u"在る"), (u"断った", u"通した"), (u"作った", u"作らなかった"), (u"当期", u"前期"), (u"前期", u"当期"), (u"上限", u"下限"), (u"下限", u"上限"),
         (u"より", u"と同じ"), (u"だけ", u"も"), (u"ない", u"ある"), (u"先", u"後"), (u"有料", u"無料"), (u"持ち越せる", u"持ち越せない"), (u"新しい", u"古い"), (u"消えた", u"増えた"), (u"どちらか", u"両方"))
DENOMS = (u"59122", u"58382", u"27829", u"28976", u"27104")
GROUP_NUMS = (u"60", u"63", u"3")


def num_spans(doc):
    out = []
    for m in NUM_RE.finditer(doc):
        if doc[:m.start()].count(u"`") % 2 == 1:
            continue
        out.append((m.start(), m.end(), m.group(1)))
    return out


def plus_one(tok):
    return u"%.1f" % (float(tok) + 0.1) if u"." in tok else str(int(tok.replace(u",", u"")) + 1)


def span_cases(doc, sec3_numbers):
    u"""(名前, 替えた文書)の列: 全部の数のトークンを 1 つずつ (a) 1 増やす (b) 文書の別の所の数に替える (c) §3 の数に替える。"""
    spans = num_spans(doc)
    uniq = sorted(set(t for _, _, t in spans), key=lambda t: (float(t.replace(u",", u"")), t))
    out = []
    for i, (s, e, tok) in enumerate(spans):
        a = plus_one(tok)
        out.append((u"W1a %d %s→%s" % (i, tok, a), doc[:s] + a + doc[e:]))
        j = (uniq.index(tok) + 1 + (i % 7)) % len(uniq)
        if uniq[j] == tok:
            j = (j + 1) % len(uniq)
        out.append((u"W1b %d %s→%s" % (i, tok, uniq[j]), doc[:s] + uniq[j] + doc[e:]))
        n3 = sec3_numbers[i % len(sec3_numbers)]
        if n3 != tok:
            out.append((u"W1c %d %s→%s" % (i, tok, n3), doc[:s] + n3 + doc[e:]))
    return out


def flip_cases(doc, c):
    out = []
    s3 = sec3_text(c)
    lo = doc.index(s3)
    hi = lo + len(s3)
    for a, b in FLIPS:
        for m in re.finditer(re.escape(a), doc):
            if lo <= m.start() < hi:
                continue
            out.append((u"W2 %s→%s @%d" % (a, b, m.start()), doc[:m.start()] + b + doc[m.end():]))
    return out


def group_cases(doc):
    out = []
    for g in GROUP_NUMS:
        for m in re.finditer(r"(?<![0-9A-Za-z.\-])%s(?= ?組)" % g, doc):
            for h in GROUP_NUMS:
                if h != g:
                    out.append((u"W3 %s 組→%s 組 @%d" % (g, h, m.start()), doc[:m.start()] + h + doc[m.end():]))
    for d in DENOMS:
        for m in re.finditer(r"(?<![0-9A-Za-z.\-])%s(?![0-9A-Za-z])" % d, doc):
            for h in DENOMS:
                if h != d:
                    out.append((u"W3 %s→%s @%d" % (d, h, m.start()), doc[:m.start()] + h + doc[m.end():]))
    return out


def table_cell_cases(doc):
    u"""表の 1 セルを、同じ表の別の行の同じ列のセルに替える(同じ字のときは飛ばす)。"""
    lines = doc.split(u"\n")
    out = []
    i = 0
    while i < len(lines):
        if lines[i].startswith(u"| ") and i + 1 < len(lines) and lines[i + 1].startswith(u"|---"):
            j = i + 2
            while j < len(lines) and lines[j].startswith(u"|"):
                j += 1
            rows = list(range(i, i + 1)) + list(range(i + 2, j))
            cells = {}
            for r in rows:
                cells[r] = lines[r].strip().strip(u"|").split(u" | ")
            for r in rows:
                for ci in range(len(cells[r])):
                    for r2 in rows:
                        if r2 == r or ci >= len(cells[r2]) or cells[r2][ci] == cells[r][ci]:
                            continue
                        new = list(cells[r])
                        new[ci] = cells[r2][ci]
                        nl = list(lines)
                        nl[r] = u"| " + u" | ".join(new) + u" |"
                        out.append((u"W5 表@%d 行 %d 列 %d ← 行 %d" % (i, r, ci, r2), u"\n".join(nl)))
            i = j
        else:
            i += 1
    return out


def delete_cases(doc, c):
    u"""§3 の外の全部の行・全部の文(。で切る)・「・」でつないだ節を 1 つずつ消す。"""
    s3 = sec3_text(c)
    lines = doc.split(u"\n")
    s3_lines = set(s3.split(u"\n"))
    out = []
    for i, ln in enumerate(lines):
        if not ln.strip() or ln in s3_lines:
            continue
        out.append((u"W6 行 %d を消す" % i, u"\n".join(lines[:i] + lines[i + 1:])))
        if ln.startswith(u"|"):
            continue
        for sep, tag in ((u"。", u"文"), (u"・", u"節")):
            parts = ln.split(sep)
            if len(parts) < 2:
                continue
            for k in range(len(parts)):
                if not parts[k]:
                    continue
                new = sep.join(parts[:k] + parts[k + 1:])
                if new == ln:
                    continue
                out.append((u"W6 行 %d の%s %d を消す" % (i, tag, k), u"\n".join(lines[:i] + [new] + lines[i + 1:])))
    return out


def sec3_cases(c):
    u"""§3 の中だけ: 文を 1 つずつ消す・向きの語を反対に(黙る所が在りうる。報告する)。"""
    s3 = sec3_text(c)
    out = []
    lines = s3.split(u"\n")
    for i, ln in enumerate(lines):
        if not ln.strip() or ln.startswith(u"## "):
            continue
        parts = ln.split(u"。")
        for k in range(len(parts)):
            if not parts[k]:
                continue
            new = u"。".join(parts[:k] + parts[k + 1:])
            if new != ln:
                out.append((u"W8 §3 行 %d の文 %d を消す" % (i, k), c.doc.replace(s3, u"\n".join(lines[:i] + [new] + lines[i + 1:]))))
    for a, b in FLIPS:
        for m in re.finditer(re.escape(a), s3):
            out.append((u"W8 §3 %s→%s @%d" % (a, b, m.start()), c.doc.replace(s3, s3[:m.start()] + b + s3[m.end():])))
    return out


def sec3_number_tokens(c):
    return [t for _, _, t in num_spans(sec3_text(c)) if t not in STRUCTURAL]


def limit_cases(c):
    u"""頭の限界の行を消す・文を 1 つずつ消す・§3 の数・主張を §2 に足す・3465 を §3 に写す・引用の外の肯定。"""
    out = []
    head, rest = c.doc.split(u"## §1", 1)
    lines = head.split(u"\n")
    sec7 = section(c.seal, u"## §7 ", None)
    lim7 = [ln[2:] for ln in sec7.splitlines() if ln.startswith(u"- ")]
    for i, lim in enumerate(lim7, 1):
        frags = [x for x in lim.split(u"。") if x]
        idx = [k for k, ln in enumerate(lines) if all(p in plain(ln) for p in frags)]
        for k in idx:
            out.append((u"W6L 限界の組 %d の行を消す" % i, u"\n".join(lines[:k] + lines[k + 1:]) + u"## §1" + rest))
        for p in frags:
            out.append((u"W6L 限界の組 %d の文「%s」を消す" % (i, p[:10]), c.doc.replace(p, u"X", 1)))
    for p in (u"「会社が型を埋められる」とは読まない", u"その値が正しいことは言わない", u"鍵が同じでも、指すものが同じとは限らない", u"名の数の下限ではない"):
        out.append((u"W6L 読み方「%s」を消す" % p[:10], c.doc.replace(p, u"X", 1)))
    for tok in sorted(set(sec3_number_tokens(c))):
        out.append((u"W4 §3 の数 %s を §2 に足す" % tok, c.doc.replace(u"\n## §3 ", u"\n- 足した行 %s 件。\n\n## §3 " % tok, 1)))
    for p in SEC3_ONLY_PHRASES:
        out.append((u"W4 §3 の主張「%s」を §2 に足す" % p[:6], c.doc.replace(u"\n## §3 ", u"\n- 足した行 %s。\n\n## §3 " % p, 1)))
    out.append((u"W4 3465 を §2 に足す", c.doc.replace(u"\n## §3 ", u"\n- 足した行 3465 件。\n\n## §3 ", 1)))
    for w in (u"XBRL を作れる。", u"会社が型を埋められる。", u"専用の道具が要らない。", u"入力が半分で済む。", u"誤りが無くなる。", u"EDINET の検査に通る。", u"人が書ける。"):
        out.append((u"D14 引用の外に「%s」を足す" % w, c.doc + u"\n" + w + u"\n"))
    return out


def all_doc_cases(c):
    doc = c.doc
    s3n = sec3_number_tokens(c) or [u"901"]
    return span_cases(doc, s3n) + flip_cases(doc, c) + group_cases(doc) + table_cell_cases(doc) + delete_cases(doc, c) + limit_cases(c)


def judge_rows_cases(c):
    u"""§1 の表の 10 行の 判定・実測・予測 のセルを、行どうしで入れ替える(全部の対)。"""
    lines = c.doc.split(u"\n")
    idx = [i for i, ln in enumerate(lines) if re.match(r"^\| XK0-\d", ln)]
    out = []
    for i in idx:
        for j in idx:
            if i == j:
                continue
            ci = lines[i].strip().strip(u"|").split(u" | ")
            cj = lines[j].strip().strip(u"|").split(u" | ")
            for col, nm in ((3, u"判定"), (2, u"実測"), (1, u"予測")):
                if ci[col] == cj[col]:
                    continue
                new = list(ci)
                new[col] = cj[col]
                nl = list(lines)
                nl[i] = u"| " + u" | ".join(new) + u" |"
                out.append((u"W5 §1 行 %d の%sを行 %d から" % (i, nm, j), u"\n".join(nl)))
    return out


def run_doc_cases(c, cases, order=ORDER_DOC):
    u"""各ケースで、どの検査が先に赤になったかを返す(黙れば None)。"""
    out = []
    for name, text in cases:
        c2 = c.with_doc(text)
        out.append((name, first_red(c2, order)))
    return out


def leaf_paths(o, path=()):
    if isinstance(o, dict):
        for k, v in o.items():
            for p in leaf_paths(v, path + (k,)):
                yield p
    elif isinstance(o, bool):
        yield path
    elif isinstance(o, (int, float)):
        yield path


REC_SWEEP_DOCS = (1, 3, 5, 6, 19, 20, 56, 67)      # 記録に無い番号(18・42・64・66)は選ばない


def record_sweep_cases(rec):
    u"""記録の整数・小数・旗の葉を 1 つずつ替える対象(集計 3 つ・予測・旗・組の代表 8 つ分)。"""
    out = []
    for key in GROUPS:
        for p in leaf_paths(rec[K_SUM][key]):
            out.append((K_SUM, key) + p)
    for p in leaf_paths(rec[PRED_KEY]):
        out.append((PRED_KEY,) + p)
    for p in leaf_paths(rec[FLAG_KEY]):
        out.append((FLAG_KEY,) + p)
    for n in REC_SWEEP_DOCS:
        d = doc_at(rec, n)
        for p in leaf_paths(d):
            if p[0] != u"番号":
                out.append((K_DOCS, n) + p)
    return out


def apply_leaf(c, path):
    if path[0] == K_DOCS:
        o = doc_at(c.rec, path[1])
        path = path[2:]
    else:
        o = c.rec
    for p in path[:-1]:
        o = o[p]
    v = o[path[-1]]
    o[path[-1]] = (not v) if isinstance(v, bool) else v + (0.1 if isinstance(v, float) else 1)


def run_record_sweep(base):
    out = []
    for path in record_sweep_cases(base.rec):
        c = base.copy()
        apply_leaf(c, path)
        out.append((u"W7 " + u"/".join(str(p)[:12] for p in path), first_red(c, ORDER_REC)))
    return out


# ======================================================================================================
EXPECTED_SILENT = ()         # 掃きで黙るのが設計どおりと確かめた名(理由は結果の報告と PREDICT の追記)。空 = 黙る所は無い
MIN_CASES = {u"W1a": 200, u"W1b": 200, u"W1c": 190, u"W2": 150, u"W3": 60, u"W5": 400, u"W6": 200, u"W6L": 25, u"W4": 10, u"D14": 7}


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
        rec = self.c.rec
        tr, jd, al = rec[K_SUM][G_TRAIN], rec[K_SUM][G_JUDGE], rec[K_SUM][G_ALL]
        PN = jd[u"数"]
        self.assertEqual((3, 60, 63), (tr[u"組"], jd[u"組"], al[u"組"]))
        self.assertEqual((0, 0, 0), (tr[u"断った組"], jd[u"断った組"], al[u"断った組"]))
        self.assertEqual((62189, 17270, 61698, 17572), (PN[u"対象の fact"][u"今年"][KN], PN[u"対象の fact"][u"今年"][KT], PN[u"対象の fact"][u"前の年"][KN], PN[u"対象の fact"][u"前の年"][KT]))
        self.assertEqual((612, 7, 928, 7), (PN[u"型の外の fact"][u"今年"][u"合計"][KN], PN[u"型の外の fact"][u"今年"][u"合計"][KT], PN[u"型の外の fact"][u"前の年"][u"合計"][KN], PN[u"型の外の fact"][u"前の年"][u"合計"][KT]))
        self.assertEqual((59122, 17261, 58382, 17500), (PN[u"型の行"][u"今年"][KN], PN[u"型の行"][u"今年"][KT], PN[u"型の行"][u"前の年"][KN], PN[u"型の行"][u"前の年"][KT]))
        mp = PN[u"対応表の名"]
        self.assertEqual((27104, 25772, 1332, 1081, 251, 1174), tuple(mp[u"科目"][k] for k in NAME_FIELDS))
        self.assertEqual((449, 448, 1, 1, 0, 0), tuple(mp[u"軸"][k] for k in NAME_FIELDS))
        self.assertEqual((3228, 3124, 104, 40, 64, 119), tuple(mp[u"member"][k] for k in NAME_FIELDS))
        self.assertEqual((56626, 16265), (PN[u"名が足りる行"][KN], PN[u"名が足りる行"][KT]))
        self.assertEqual((28740, 21437, 7539, 1406), tuple(PN[u"今年の行の期の区分"][KN][k] for k in CLASS4))
        self.assertEqual((0, 20424, 7405, 0), tuple(PN[u"同じ行(日)"][KN][k] for k in CLASS4))
        self.assertEqual((27015, 19467, 7247, 1239), tuple(PN[u"枠が在る行"][KN][k] for k in CLASS4))
        self.assertEqual((27026, 8, 782, 13), tuple(PN[u"同じ行の中身(数)"][k] for k in CONTENT4))
        self.assertEqual((6943, 399, 0, 9919), tuple(PN[u"今年の行の期の区分"][KT][k] for k in CLASS4))
        self.assertEqual((0, 388, 0, 0), tuple(PN[u"同じ行(日)"][KT][k] for k in CLASS4))
        self.assertEqual((6551, 363, 0, 9119), tuple(PN[u"枠が在る行"][KT][k] for k in CLASS4))
        self.assertEqual((58382, 27829, 54968, 3414), tuple(PN[u"逆向き"][KN][k] for k in BACK_FIELDS))
        self.assertEqual((17500, 388, 16033, 1467), tuple(PN[u"逆向き"][KT][k] for k in BACK_FIELDS))
        sv = stat_values(rec)
        self.assertEqual((u"55.2", u"96.4", u"99.7", 57, 45, 11, 1), sv[u"keep"])
        self.assertEqual((1, u"17", 239, 0, 444), sv[u"new"])
        self.assertEqual((u"38.7", u"96.2", u"100.0", 38, 52, 5), sv[u"frame"])
        self.assertEqual((4154, 1775, 698), sv[u"noframe"])
        self.assertEqual((53, 78, 282), sv[u"diff"])
        self.assertEqual((1725, 32096, 1147), (sv[u"cur_noframe"], sv[u"not_same"], sv[u"old_nosame"]))
        t = tr[u"数"]
        self.assertEqual((1460, 1499, 3274, 3337, 1626, 1585, 41), (t[u"対応表の名"][u"科目"][u"持ち越せる"], t[u"対応表の名"][u"科目"][u"今年"], t[u"名が足りる行"][KN], t[u"型の行"][u"今年"][KN],
                                                                    s4(t[u"同じ行(日)"][KN]), t[u"同じ行の中身(数)"][CONTENT4[0]], t[u"同じ行の中身(数)"][CONTENT4[2]]))
        a = al[u"数"][u"対応表の名"][u"科目"]
        self.assertEqual((27232, 28603, 1371, 1111, 260, 1208), (a[u"持ち越せる"], a[u"今年"], a[u"新しい"], a[u"新しい・_cor で終わる"], a[u"新しい・_cor で終わらない"], a[u"消えた"]))
        self.assertEqual((67, 4), (rec[u"材料"][u"今年の側の書類の本数"], rec[u"材料"][u"除いた今年の書類の数"]))

    def test_c_1_the_seal_has_the_bound_phrases(self):
        self.assertEqual([], bound_problems(self.c))

    def test_c_2_the_verdicts_are_decided_again_and_equal_the_document(self):
        self.assertEqual([], verdict_problems(self.c))
        j = judge(self.c.rec)
        self.assertEqual(4, sum(1 for v in j.values() if v[0]))
        self.assertEqual([u"XK0-1", u"XK0-2", u"XK0-3", u"XK0-6", u"XK0-9", u"XK0-10"], miss_ids(j))
        self.assertEqual(list(IDS), list(j))
        self.assertEqual((False,) * 6, suspects(self.c))
        # 当たり外れの判定は丸める前の数。XK0-1 は 25772/27104(95.08%)で 96% に届かない(100 * 25772 = 2577200 < 96 * 27104 = 2601984)
        self.assertTrue(100 * 25772 < 96 * 27104)
        self.assertTrue(100 * 54968 < 95 * 59122)
        self.assertEqual((False, u"下"), j[u"XK0-1"])
        self.assertEqual((False, u"下"), j[u"XK0-2"])
        self.assertEqual((False, u"下"), j[u"XK0-3"])
        self.assertEqual((True, u""), j[u"XK0-4"])
        self.assertEqual((True, u""), j[u"XK0-5"])
        self.assertEqual((False, u"下"), j[u"XK0-6"])
        self.assertEqual((True, u""), j[u"XK0-7"])
        self.assertEqual((True, u""), j[u"XK0-8"])
        self.assertEqual((False, u"下"), j[u"XK0-9"])
        self.assertEqual((False, u"下"), j[u"XK0-10"])
        # 封 §6: XK0-1 と XK0-6 のどちらかが外れ → 次の便の候補は示さない(文書 §5 がそれ)。両方が外れ
        self.assertFalse(j[u"XK0-1"][0])
        self.assertFalse(j[u"XK0-6"][0])

    def test_d_1_every_number_in_the_document_is_bound_to_the_record(self):
        self.assertEqual([], doc_number_problems(self.c))
        self.assertEqual([], residual_problems(self.c))

    def test_d_2_every_line_outside_section3_equals_the_one_built_from_the_record(self):
        self.assertEqual([], lines_problems(self.c))
        self.assertEqual([], sanity_problems(self.c))

    def test_d_3_section3_is_bound_only_by_form_not_by_the_record(self):
        self.assertEqual([], sec3_problems(self.c))

    def test_d_4_the_audit_only_number_stays_in_section4_and_the_seal_gate_counts_are_bound(self):
        self.assertEqual([], sec4_problems(self.c))
        self.assertEqual((265, 12, 8, 30), (len(SG.MUTANTS), len(SG.INCREMENT_MUTANTS), len(SG.SILENT_BY_DESIGN), seal_tests()))
        self.assertIn(u"試験 30 本。変異 277 本(字を 1 か所替える 265 本・掃く形の 12 本)が赤。作りから黙る変異 8 本", self.c.doc)
        self.assertIn(u"3465 項目", self.c.doc)

    def test_d_5_the_date_supplement_follows_the_seal_and_the_record(self):
        self.assertIn(u"番号 1・2・3 が訓練の 3 組、番号 4〜63 が判定の 60 組", self.c.seal)
        self.assertIn(u"番号は今年の側の 67 本の中の位置で、67 まで在る。実装は「番号が 3 より大きい組」を判定の 60 組にした(組の数は封の字どおり 60)", self.c.doc)
        self.assertEqual(3, MS.SEEN_MAX_NO)
        self.assertEqual(67, self.c.rec[K_DOCS][-1][u"番号"])
        self.assertEqual(63, len(self.c.rec[K_DOCS]))
        self.assertIn(u"旗 1・4・6 は 63 組、旗 2・3・5 は判定の 60 組で見た", self.c.doc)
        self.assertNotIn(u"旗用の数", self.c.seal)

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
        self.assertEqual((u"1fc4c736", u"aaeeb21c", u"1392a222"), DOC_COMMITS)

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
    @classmethod
    def setUpClass(cls):
        cls.base = Ctx()

    def test_g_1_every_mutation_turns_its_checks_red_and_the_files_are_unchanged(self):
        files = list(SHA_PIN) + [DOC_REL, XM0_RECORD_REL]
        before = tuple(sha_file(r) for r in files)
        results = run_mutations(self.base)
        self.assertEqual(before, tuple(sha_file(r) for r in files))
        self.assertEqual(len(MUTATIONS), len(results))
        silent = [(n, k) for n, res in results for k, red in res if not red]
        self.assertEqual([], silent)
        self.assertGreaterEqual(len(MUTATIONS), 78)

    def test_g_2_the_unmutated_copy_is_green_on_every_check(self):
        c = self.base.copy()
        for k, fn in CHECKS.items():
            self.assertEqual([], fn(c), k)

    def test_g_3_the_recount_stays_green_when_the_data_changes_consistently_but_the_document_check_does_not(self):
        base_j = judge(self.base.rec)
        for fn in CONSISTENT:
            c = self.base.copy()
            fn(c)
            self.assertEqual([], recount_problems(c), fn.__name__)
            self.assertIsNotNone(first_red(c, ORDER_REC), fn.__name__)
        flips = ((m_k1_hit, u"XK0-1"), (m_k2_hit, u"XK0-2"), (m_k3_hit, u"XK0-3"), (m_k4_low, u"XK0-4"), (m_k4_100, u"XK0-4"), (m_k5_low, u"XK0-5"), (m_k5_high, u"XK0-5"),
                 (m_k6_hit, u"XK0-6"), (m_k7_miss, u"XK0-7"), (m_k8_declined4, u"XK0-8"), (m_k9_hit, u"XK0-9"), (m_k10_hit, u"XK0-10"))
        for fn, key in flips:
            c = self.base.copy()
            fn(c)
            self.assertNotEqual(base_j[key][0], judge(c.rec)[key][0], (fn.__name__, key))
            self.assertNotEqual([], verdict_problems(c), (fn.__name__, key))
        for fn, idx in ((m_f1, 0), (m_f2, 1), (m_f3, 2), (m_f5, 4), (m_f6, 5)):
            c = self.base.copy()
            fn(c)
            self.assertTrue(suspects(c)[idx], (fn.__name__, suspects(c)))
            self.assertNotEqual([], verdict_problems(c), fn.__name__)
        # 外れの向き(XK0-4 と XK0-5 の下と上)は別々に出る
        for fn, key, way in ((m_k4_low, u"XK0-4", u"下"), (m_k4_100, u"XK0-4", u"上"), (m_k5_low, u"XK0-5", u"下"), (m_k5_high, u"XK0-5", u"上")):
            c = self.base.copy()
            fn(c)
            self.assertEqual(way, judge(c.rec)[key][1], (fn.__name__, key))
        # XK0-1 と XK0-6 が両方当たりになる(封 §6 は (i)(ii)(iii) を示す)。文書は「示さない」のままなので §5 の検査が赤
        c = self.base.copy()
        m_xm01_hit_only(c)
        jj = judge(c.rec)
        self.assertTrue(jj[u"XK0-1"][0] and jj[u"XK0-6"][0])
        self.assertNotEqual([], sec5_decision_problems(section(c.doc, u"## §5 ", None), True, seal_s6_lines(c.seal)))
        self.assertNotEqual([], verdict_problems(c))
        # 整合の sanity 変異は sanity が赤(recount は緑のまま)
        c = self.base.copy()
        m_train_low(c)
        self.assertEqual([], recount_problems(c))
        self.assertNotEqual([], sanity_problems(c))

    def test_g_4_every_check_name_a_mutation_names_exists_and_every_check_has_a_mutation(self):
        named = set(k for _, _, ks in MUTATIONS for k in ks)
        self.assertEqual(set(CHECKS), named)
        for k in (u"numbers", u"resid"):
            self.assertIn(k, ORDER_DOC)

    def test_g_5_the_judgement_edges_at_the_seal_bounds(self):
        u"""境の 1 つ手前と境の数(丸める前の整数): 下限・上限とも含む/含まない。"""
        def j(**kw):
            p = collections.OrderedDict([(u"XK0-1", (96, 100)), (u"XK0-2", (97, 100)), (u"XK0-3", (97, 100)), (u"XK0-4", (97, 100)), (u"XK0-5", (50, 100)), (u"XK0-6", (95, 100)),
                                         (u"XK0-7", (60, 100)), (u"XK0-8", (0, 60)), (u"XK0-9", (48, 60)), (u"XK0-10", (57, 60))])
            for k, v in kw.items():
                p[k.replace(u"_", u"-")] = v
            return judge_nums(p)
        self.assertTrue(j(XK0_1=(96, 100))[u"XK0-1"][0])
        self.assertFalse(j(XK0_1=(95, 100))[u"XK0-1"][0])
        self.assertFalse(j(XK0_1=(0, 0))[u"XK0-1"][0])
        self.assertTrue(j(XK0_2=(97, 100))[u"XK0-2"][0])
        self.assertFalse(j(XK0_2=(96, 100))[u"XK0-2"][0])
        self.assertTrue(j(XK0_3=(97, 100))[u"XK0-3"][0])
        self.assertFalse(j(XK0_3=(96, 100))[u"XK0-3"][0])
        self.assertTrue(j(XK0_4=(96, 100))[u"XK0-4"][0])
        self.assertFalse(j(XK0_4=(95, 100))[u"XK0-4"][0])
        self.assertEqual(u"下", j(XK0_4=(95, 100))[u"XK0-4"][1])
        self.assertTrue(j(XK0_4=(99, 100))[u"XK0-4"][0])
        self.assertFalse(j(XK0_4=(100, 100))[u"XK0-4"][0])
        self.assertEqual(u"上", j(XK0_4=(100, 100))[u"XK0-4"][1])
        self.assertTrue(j(XK0_5=(44, 100))[u"XK0-5"][0])
        self.assertFalse(j(XK0_5=(43, 100))[u"XK0-5"][0])
        self.assertTrue(j(XK0_5=(51, 100))[u"XK0-5"][0])
        self.assertFalse(j(XK0_5=(52, 100))[u"XK0-5"][0])
        self.assertEqual(u"下", j(XK0_5=(43, 100))[u"XK0-5"][1])
        self.assertEqual(u"上", j(XK0_5=(52, 100))[u"XK0-5"][1])
        self.assertTrue(j(XK0_6=(95, 100))[u"XK0-6"][0])
        self.assertFalse(j(XK0_6=(94, 100))[u"XK0-6"][0])
        self.assertTrue(j(XK0_7=(51, 100))[u"XK0-7"][0])
        self.assertFalse(j(XK0_7=(50, 100))[u"XK0-7"][0])
        self.assertFalse(j(XK0_7=(0, 0))[u"XK0-7"][0])
        self.assertTrue(j(XK0_8=(3, 60))[u"XK0-8"][0])
        self.assertFalse(j(XK0_8=(4, 60))[u"XK0-8"][0])
        self.assertTrue(j(XK0_8=(0, 60))[u"XK0-8"][0])
        self.assertTrue(j(XK0_9=(48, 60))[u"XK0-9"][0])
        self.assertFalse(j(XK0_9=(47, 60))[u"XK0-9"][0])
        self.assertTrue(j(XK0_10=(57, 60))[u"XK0-10"][0])
        self.assertFalse(j(XK0_10=(56, 60))[u"XK0-10"][0])

    def test_g_6_the_section5_decision_follows_the_seal_section6(self):
        c = self.base
        sec5 = section(c.doc, u"## §5 ", None)
        s6 = seal_s6_lines(c.seal)
        cands = seal_candidates(s6)
        self.assertEqual(3, len(cands))
        self.assertEqual([], sec5_decision_problems(sec5, False, s6))
        self.assertNotEqual([], sec5_decision_problems(sec5, True, s6))
        # 外れの §5 に候補を 1 つ足すと赤(見出しの有る案・見出しの無い案・封の当たりの側の字・「候補」の字・「第 1 版」)
        for add in (u"  - (i) 別の案。\n", u"  - (iv) 別の案。\n", u"- 次の便の候補は別にある。\n", u"- 次は第 1 版を作る。\n", u"- 別の案は答えを見ない席に任せる。\n", u"- 費用は 0 USD。別の封が先。\n"):
            self.assertNotEqual([], sec5_decision_problems(sec5.rstrip(u"\n") + u"\n" + add, False, s6), add)
        for old, new in ((u"**次の便の候補は示さない。** ", u""), (u"新しい名・枠の無い行の中身を読むのが先", u"X"), (u"のどちらかが外れ", u"が両方当たり"), (u"続けるか・どの向きへ続けるかは人間が決める", u"X")):
            self.assertIn(old, sec5, old)
            self.assertNotEqual([], sec5_decision_problems(sec5.replace(old, new, 1), False, s6), old)
        # 当たりの形((i)(ii)(iii) を示す)は緑で、1 つ足す・落とす・費用の字が落ちる・順の入れ替えで赤
        head_line = u"- 封 §6 の決め: XK0-1 と XK0-6 が両方当たりなので、次の便の候補を 3 つ示す(どれも別の封が先。選ぶのは人間):\n"
        good = u"## §5 読みと次\n\n" + head_line + u"".join(u"  - " + x + u"。\n" for x in cands) + u"- 続けるか・どの向きへ続けるかは人間が決める。\n"
        self.assertEqual([], sec5_decision_problems(good, True, s6))
        self.assertNotEqual([], sec5_decision_problems(good, False, s6))
        self.assertNotEqual([], sec5_decision_problems(good.replace(u"次の便の候補を 3 つ示す", u"次の便の候補を 4 つ示す"), True, s6))
        self.assertNotEqual([], sec5_decision_problems(good.replace(u"(有料。別の封と、払う前の知らせが先)", u""), True, s6))
        self.assertNotEqual([], sec5_decision_problems(good.replace(u"(0 USD。別の封が先)。\n  - (ii)", u"。\n  - (ii)"), True, s6))
        self.assertNotEqual([], sec5_decision_problems(good.replace(u"  - (iii)", u"  - (iv)"), True, s6))
        self.assertNotEqual([], sec5_decision_problems(good.replace(u"- 続けるか", u"  - (iv) 別の案。\n- 続けるか"), True, s6))
        lines = good.split(u"\n")
        i2, i3 = [k for k, ln in enumerate(lines) if u"(ii)" in ln][0], [k for k, ln in enumerate(lines) if u"(iii)" in ln][0]
        lines[i2], lines[i3] = lines[i3], lines[i2]
        self.assertNotEqual([], sec5_decision_problems(u"\n".join(lines), True, s6))
        # 記録を写しの上で XK0-1 と XK0-6 の両方を当たりに変えると、「示さない」の §5 は赤になる(向き)
        cc = self.base.copy()
        m_xm01_hit_only(cc)
        jj = judge(cc.rec)
        self.assertTrue(jj[u"XK0-1"][0] and jj[u"XK0-6"][0])
        self.assertNotEqual([], sec5_decision_problems(sec5, jj[u"XK0-1"][0] and jj[u"XK0-6"][0], s6))
        # 片方だけ当たりに変えても(XK0-1 だけ)、示さない形のまま緑で、「両方とも外れ」の言い切りは lines が赤にする
        c1 = self.base.copy()
        m_k1_hit(c1)
        j1 = judge(c1.rec)
        self.assertTrue(j1[u"XK0-1"][0] and not j1[u"XK0-6"][0])
        self.assertEqual([], sec5_decision_problems(sec5, False, s6))
        self.assertNotEqual([], lines_problems(c1))

    def test_g_7_the_self_suspicion_flags_fire_at_the_exact_boundaries(self):
        c = self.base.copy()
        rec = c.rec
        judge_docs = split_docs(rec)[1]
        # 旗 4: 枠が在る行が名が足りる行より多い組(記録として整合しないので recount は赤だが、旗の値は立つ)
        d = judge_docs[0]
        f0 = flags_expected(rec, c.xm0)
        self.assertFalse(f0[FLAG_KEYS[3]][u"旗"])
        d[u"名が足りる行"][KN] = s4(d[u"枠が在る行"][KN])
        self.assertFalse(flags_expected(rec, c.xm0)[FLAG_KEYS[3]][u"旗"])
        d[u"名が足りる行"][KN] -= 1
        self.assertTrue(flags_expected(rec, c.xm0)[FLAG_KEYS[3]][u"旗"])
        self.assertNotEqual([], recount_problems(c))
        # 旗 5: 断った組が 5 → 立たない・6 → 立つ(判定の 60 組)。訓練の 3 組の断りは数えない
        c = self.base.copy()
        docs = [x for x in c.rec[K_DOCS] if x[u"番号"] > TRAIN_COUNT]
        for x in docs[:5]:
            decline_doc(x)
        self.assertFalse(flags_expected(c.rec, c.xm0)[FLAG_KEYS[4]][u"旗"])
        decline_doc(docs[5])
        self.assertTrue(flags_expected(c.rec, c.xm0)[FLAG_KEYS[4]][u"旗"])
        c = self.base.copy()
        for x in c.rec[K_DOCS][:3]:
            decline_doc(x)
        self.assertFalse(flags_expected(c.rec, c.xm0)[FLAG_KEYS[4]][u"旗"])
        # 旗 1: 当期の同じ行(日)は 63 組の全部で見る(訓練の組の 1 行でも立つ)
        c = self.base.copy()
        c.rec[K_DOCS][0][u"同じ行(日)"][KT][u"当期"] = 1
        self.assertTrue(flags_expected(c.rec, c.xm0)[FLAG_KEYS[0]][u"旗"])
        # 旗 2: 判定の 60 組の全部で 100%。1 組でも 100% でなければ立たない
        c = self.base.copy()
        for x in c.rec[K_DOCS]:
            if x[u"番号"] > TRAIN_COUNT:
                y = x[u"対応表の名"][u"科目"]
                y[u"持ち越せる"], y[u"新しい"] = y[u"今年"], 0
        self.assertTrue(flags_expected(c.rec, c.xm0)[FLAG_KEYS[1]][u"旗"])
        y = c.rec[K_DOCS][10][u"対応表の名"][u"科目"]
        y[u"持ち越せる"] -= 1
        self.assertFalse(flags_expected(c.rec, c.xm0)[FLAG_KEYS[1]][u"旗"])
        # 旗 3: 同じ行(数)が 60 組の合計で 0 は立つ。訓練の 3 組の同じ行は数えない
        c = self.base.copy()
        for x in c.rec[K_DOCS]:
            if x[u"番号"] > TRAIN_COUNT:
                for k in CLASS4:
                    x[u"同じ行(日)"][KN][k] = 0
        self.assertTrue(flags_expected(c.rec, c.xm0)[FLAG_KEYS[2]][u"旗"])

    def test_g_8_the_group_sizes_and_the_numbers_are_not_confused(self):
        rec = self.base.rec
        train, judge_docs = split_docs(rec)
        self.assertEqual((3, 60, 63), (len(train), len(judge_docs), len(rec[K_DOCS])))
        self.assertEqual(len(set([3, 60, 63])), 3)
        c = self.base.copy()
        m_swap_groups(c)
        self.assertNotEqual([], recount_problems(c))

    def test_g_9_the_verdict_table_stays_the_60_group_numbers(self):
        for old, new in ((u"| 25772/27104(95.1%) | 外れ |", u"| 1460/1499(97.4%) | 外れ |"), (u"| 25772/27104(95.1%) | 外れ |", u"| 27232/28603(95.2%) | 外れ |"),
                         (u"| 56626/59122(95.8%) | 外れ |", u"| 3274/3337(98.1%) | 外れ |"), (u"| 27026/27829(97.1%) | 当たり |", u"| 1585/1626(97.5%) | 当たり |"),
                         (u"| 54968/59122(93.0%) | 外れ |", u"| 3240/3337(97.1%) | 外れ |"), (u"| 1081/1332(81.2%) | 当たり |", u"| 1111/1371(81.0%) | 当たり |"),
                         (u"| 45 組(60 組のうち) | 外れ |", u"| 45 組(63 組のうち) | 外れ |"), (u"| 53 組(60 組のうち) | 外れ |", u"| 53 組(3 組のうち) | 外れ |")):
            self.assertIn(old, self.base.doc, old)
            c = self.base.with_doc(self.base.doc.replace(old, new, 1))
            self.assertNotEqual([], verdict_problems(c), old)
        c = self.base.with_doc(self.base.doc.replace(u"| 54968/59122(93.0%) | 外れ |", u"| 3240/3337(97.1%) | 外れ |", 1))
        self.assertTrue(any(u"混ざっている" in x for x in verdict_problems(c)))
        c = self.base.with_doc(self.base.doc.replace(u"| 56626/59122(95.8%) | 外れ |", u"| 3274/3337(98.1%) | 外れ |", 1))
        self.assertTrue(any(u"混ざっている" in x for x in verdict_problems(c)))

    def test_h_1_the_sweep_over_every_number_direction_word_group_swap_cell_and_line_stays_red(self):
        c = self.base
        cases = all_doc_cases(c) + judge_rows_cases(c)
        results = run_doc_cases(c, cases)
        silent = [n for n, k in results if k is None]
        by_kind = collections.Counter(n.split(u" ")[0] for n, _ in results)
        self.assertEqual(sorted(EXPECTED_SILENT), sorted(silent))
        for kind, lo in MIN_CASES.items():
            self.assertGreaterEqual(by_kind[kind], lo, kind)
        self.assertGreater(len(results), 1500)

    def test_h_2_the_record_leaf_sweep_stays_red(self):
        results = run_record_sweep(self.base)
        silent = [n for n, k in results if k is None]
        self.assertEqual([], silent)
        self.assertGreater(len(results), 500)

    def test_h_3_section3_prose_sweep_reports_what_stays_silent(self):
        u"""§3 は形で縛る(数の並び・記録との整合・語の留め)。§3 の中の文の削除・向きの語の反転で黙る所が在れば、それを数えて留める(増えたら赤)。"""
        c = self.base
        results = run_doc_cases(c, sec3_cases(c))
        silent = [n for n, k in results if k is None]
        self.assertEqual(sorted(SEC3_SILENT), sorted(silent))


SEC3_SILENT = ()


if __name__ == "__main__":
    unittest.main()
