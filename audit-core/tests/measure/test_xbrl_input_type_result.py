# -*- coding: utf-8 -*-
u"""結果の門: 封 docs/XBRL_INPUT_TYPE_SEAL_2026-11-22.md(34afe495)の結果の文書 docs/XBRL_INPUT_TYPE_RESULT_2026-11-22.md(便 XM0)。

封の門 ``test_xbrl_input_type_seal.py`` の次の段。**追跡されている記録・script・封・封の門・結果の文書と git の履歴だけを読む**(書類の置き場は読まない・道具は呼ばない・通信しない・鍵は読まない)。
便 XA0 の結果の門 ``test_xbrl_sheet_wall_result.py`` の部品(読み・sha256・% の丸め・節の切り出し・数のトークン・禁止語・blob の道具)を読み込んで使う(門としては走らせない)。
検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表と、全部のセルを 1 か所ずつ掃く ``SWEEPS`` で(木の file は変異させず、``Ctx`` の写しに当てる)。

 a script・記録・封・封の門の sha256(字で留める)・記録の script の sha256・封の commit の欄・記録の限界の欄・材料の指紋が script の字と同じ
 b 記録の数え直し: 書類ごとの数から、**script の関数を使わずに**、開発の 5 本・本番だけの 62 本・全部の集計の全部の欄を数え直す(断った書類の形・型に入った + 型の外 = 対象・理由ごとの数が合計を超えない・
   比べ方 1 と 2 と混ぜ物の含意・表示の字の数)。予測の判定に要る数を集計から作り直した値と照らす
 c 予測 XM0-1〜XM0-10 の当たり外れを、封 §4 の字から取った境(丸める前の整数で)と記録(本番だけの 62 本)から決め直し、文書 §1 の表・件数と同じことを見る。
   封 §4 の「先に自分の欠陥を疑う」旗を決め直す(どれも立たない)・封 §6 の決め(XM0-1 が当たりなら次の便の候補 (i)〜(iv) をちょうど示す。外れなら示さない)と文書 §5 が合う
 d 結果の文書の数: §1・§2・§4・§5 の数は全部、記録から導く(理由ごとの書類の数・最大・型の外が 1 つだけの書類・最大の書類の対象の fact・`-0` の在る書類・単位が 4 つの書類は門の中で書類ごとから導き直す)。
   記録の数と字から文書の §3 以外の全部の行を組み直し、文書と行ごとに照らす(``render_doc``)。主な主張の文は断片でも縛る。
   **§3 の読み(記録に欄の無い読み。出どころは監査の席)は記録に縛らず**、見出し・「測った数ではない」・字で留めた数の並び・記録の数との整合・§3 の主張が §3 の外に出ないこと・「測っていない」を縛る
 e 文書の頭の負けと限界(封 §7 の 6 本・封 §6 の読み方)・禁止語・「XBRL を作れる」「専用の道具が要らない」「どんな資料も作れる」「誤りが無くなる」「会社が型を埋めれば」「EDINET の検査に通る」を肯定で書かない・docID と EDINET コードの形
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


WG = load_module("tests/measure/test_xbrl_sheet_wall_result.py", "xbrl_sheet_wall_result_gate_for_input_type_result_gate")                # 便 XA0 の結果の門の部品。門としては走らせない
SG = load_module("tests/measure/test_xbrl_input_type_seal.py", "xbrl_input_type_seal_gate_for_result_gate")                # 封の門の部品。門としては走らせない
PR = WG.PR
MS = SG.MS

read, sha_file, guard, pct, section = WG.read, WG.sha_file, WG.guard, WG.pct, WG.section
ints_in, doc_number_tokens = WG.ints_in, WG.doc_number_tokens

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
RECORD_REL = SG.RECORD_REL
GATE_REL = "tests/measure/test_xbrl_input_type_result.py"
DOC_REL = "docs/XBRL_INPUT_TYPE_RESULT_2026-11-22.md"
SCRIPT_COMMIT_SHORT = "6f719410"                  # script と封の門を足した commit
RECORD_COMMIT_SHORT = "3cd49ad4"                  # 記録を足した commit
BLOB_AT = collections.OrderedDict([
    (SEAL_REL, SEAL_COMMIT_SHORT), (SCRIPT_REL, SCRIPT_COMMIT_SHORT), (SEAL_GATE_REL, SCRIPT_COMMIT_SHORT), (RECORD_REL, RECORD_COMMIT_SHORT)])
HISTORY = collections.OrderedDict([
    (SEAL_REL, [SEAL_COMMIT_SHORT]), (SCRIPT_REL, [SCRIPT_COMMIT_SHORT]), (SEAL_GATE_REL, [SCRIPT_COMMIT_SHORT]), (RECORD_REL, [RECORD_COMMIT_SHORT])])
DOC_COMMITS = (SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT)

SHA_PIN = collections.OrderedDict([
    (RECORD_REL, "28e83050cc01faf40ab5dd765c6d6bf670fcb18b94dabcc5c04bb322e7402110"),
    (SCRIPT_REL, "00d5e51752604e7c507e5c66b02fac1d9f941cabe2c66ea08c7512c6a8fcf60a"),
    (SEAL_GATE_REL, "8892058c3bf6fb589c69552812cfc9794dfd9bfea126b5a874ffa354a40f513a"),
    (SEAL_REL, "ecf7631177233eb1402b90463617972b673a358645e9d3ba9657f9a764997a99")])
MATERIAL_PIN = collections.OrderedDict([
    (u"書類の本数", 67), (u"書類の file 名の並びの sha256", "f240150645a9b05a8d9bf5a9fe0ab89633ae338e42b8cc4d891dc04ca401e3f5"), (u"開発の 5 本の番号", [1, 2, 3, 4, 5]), (u"道具の版", u"2.47.5"),
    (u"道具 P の ModelValue.py の sha256", "fd9b0d08bf283452fe4ebd6ec9de2f273010de0420b70e61c993a6c033814635"),
    (u"道具 P の package の一覧の sha256", "51e7d2857de748b879e21995908efe50a9350041596e1cd73bef7aac595004a1"), (u"Python の版(道具 P)", u"Python 3.11.17"), (u"規則の年", u"EDINET-2026"),
    (u"混ぜ物の種類", [u"対象を個別に変える"]), (u"時間の上限(秒)", 600)])

DOC_COUNT = 67
DEV_COUNT = 5
PROD_COUNT = DOC_COUNT - DEV_COUNT
SEAL_DECLARED = 4982          # 封 §0 が開発の 5 本の数の fact として申告した数(字で留める。封の字と照らす)
LETTERS = u"abcdefgh"
STAGES = (u"型を作る", u"型から作る", u"組む", u"道具")
K_SUM = u"集計"
G_DEV, G_PROD, G_ALL = u"開発の 5 本", u"本番だけの 62 本", u"全部"
GROUPS = (G_DEV, G_PROD, G_ALL)
K_DOCS = u"書類"
PRED_KEY = u"予測の判定に要る数(XM0-1〜XM0-10。当たり・外れは結果の文書で)"
PK = (u"XM0-1 fact が意味として同じ書類", u"XM0-2 型の外の fact が 0 の書類", u"XM0-3 型の外の fact", u"XM0-4 型の外の理由ごとの fact", u"XM0-5 文脈の名も同じ書類",
      u"XM0-6 作らなかった文脈の定義が 1 つ以上在る書類", u"XM0-7 鳴り方が同じ書類", u"XM0-8 混ぜ物が効いた書類", u"XM0-9 数の型の行", u"XM0-10 表示の字が合った fact")
IDS = tuple(u"XM0-%d" % i for i in range(1, 11))
DOC_KEYS = (u"番号", u"断った", u"断った段", u"断った理由", u"対象の fact", u"型に入った fact", u"型の外の fact", u"型の行", u"対応表の行", u"持ち込みの属性を持つ fact", u"文脈の定義", u"単位の定義",
            u"比べ方 1", u"比べ方 2", u"混ぜ物", u"表示の字の検査", u"秒")
REASON_LABEL = collections.OrderedDict([(u"a", u"(a) 期間が期の表に無い"), (u"d", u"(d) 単位が 4 つの形のどれでもない"), (u"e", u"(e) `format`・`decimals`・`scale` の形"), (u"f", u"(f) 表示の字から値を作れない")])
OTHER_REASONS = u"bcgh"
FLAG_KEYS = (u"型の外の fact が 0(62 本の全部で)", u"型に入った fact が対象の fact の 90% 未満", u"属性が意味として同じなのに道具の fact が違う書類", u"混ぜ物を作れなかった書類が 6 本以上",
             u"断った書類が 6 本以上", u"値が `-0` の行が 0")

# 封の字(封の門が script と照らし、ここでは文書が引く字の在り処を縛る)
BOUND_SEAL_PHRASES = tuple(SG.SEAL_BOUND_TEXT.values()) + (
    u"XM0-1・XM0-8 は作りから当たりやすい", u"型の外の fact が 0(62 本の全部で)・型に入った fact が対象の fact の 90% 未満・属性が意味として同じなのに道具の fact が違う書類が在る",
    u"混ぜ物を作れなかった書類が 6 本以上・断った書類が 6 本以上", u"値が `-0` の行が 0(理由を 1 件ずつ読むまで「無い」と書かない)", u"「会社が型を埋めれば XBRL が作れる」とは読まない",
    u"持ち込み(素の本文・fact の置き場・どの置き場がどの数か・文の中身・脚注・提出者別タクソノミの表)はこの便では作っていない", u"対象の `既定` は「個別の印が無い」という意味で、連結とは限らない",
    u"道具が読む fact が元と同じでも、EDINET の本物の検査に通ることは言えない", u"「XBRL を作れる」「専用の道具が要らない」「どんな資料も作れる」「誤りが無くなる」は、この便からは言えない",
    u"次の便の候補(別の封が先。人間に示す): XM0-1 が当たりなら", u"XM0-1 が外れなら、違った所の型を読む(読むのは開発の 5 本だけ)のが先で、(i)〜(iv) は示さない",
    u"(i) 型の外の理由のうち fact がいちばん多いものを型の拡張で入れる第 1 版(0 USD)", u"(ii) 型から本文の表示の字と表も作る(持ち込みを減らす。0 USD)",
    u"(iii) 前の年の対応表を今年に持ち越せる割合を数える(0 USD)", u"(iv) 答えを見ない席が、XBRL でない資料から型を埋める(有料。別の封と、払う前の知らせが先)",
    u"開発の 5 本だけ", u"数の fact 4982")
# 封 §7 の限界 6 本(封の字)に対応する、文書の頭に在るべき断片。(封 §7 の何本目か, 断片)。1 組の断片は全部同じ行に在る(封 §7 の 1 本目は文書では 2 行に分かれる)。
LIMIT_FRAGS = (
    (u"7-1", (u"62 本は前の便で数えた書類で、未使用ではない", u"67 本は無作為ではない", u"有報だけ")),
    (u"7-1", (u"道具 1 つ(道具 P。本家の版でない)の fact の一覧だけ", u"EDINET の本物の検査とは照らしていない", u"`.xbrl` を落とした包み", u"script は前の便の script を経て engine の module を間接に読み込む")),
    (u"7-2", (u"型も対応表も答えから作った", u"型の外の fact は元から写すので、その fact が元と同じになるのは当たり前", u"会社がこの型で情報を用意できるか・対応表を作れるか・埋めた中身が正しいかは測っていない")),
    (u"7-3", (u"型の欄と規則(期の名の 3 つの型・単位の 4 つの形・`format` の 1 通り・個別の軸と member)は開発の 5 本を見て決めた", u"62 本は前の便で数えた書類で、未使用ではない")),
    (u"7-4", (u"比べ方 2 は `contextRef` の字を見ず、`unitRef` は measure に置き換えて比べる", u"字まで同じかは別の数で書く")),
    (u"7-5", (u"混ぜ物は 1 本につき 1 つ・対象の欄だけ", u"ほかの欄を変えた確かめは封の門の作り物だけ")),
    (u"7-6", (u"文の fact は、型が持つのは科目・期間・対象・次元だけで、文の中身と書式の属性は持ち込み",)),
    (u"6-持ち込み", (u"持ち込みは作っていない", u"素の本文・fact の置き場・どの置き場がどの数か・文の中身・脚注・提出者別タクソノミの表は、元から写した")),
    (u"6-連結", (u"対象の `既定` は「個別の印が無い」という意味で、連結とは限らない",)),
    (u"6-言えない", (u"「XBRL を作れる」「専用の道具が要らない」「どんな資料も作れる」「誤りが無くなる」は、この便からは言えない",)))
HEAD_PHRASES = (u"先に負けと限界を書く", u"記録から 1 つずつ読んだもの", u"記録に欄の無い読み", u"第 0 版の型のままで全部の fact が入る書類は 1 本も無かった", u"型も対応表も答えから作った",
                u"「会社が型を埋めれば XBRL が作れる」とは読まない", u"持ち込みは作っていない", u"作りから当たりやすい", u"断った書類が 1 本在る", u"連結とは限らない", u"盲検ではない",
                u"費用は 0 USD", u"engine(`core/`・`adapters/`)は 0 行", u"封 §0 の申告の数は足りていなかった", u"外れは外れとして残す", u"型の値の大きさは、作る XBRL の側に効かない",
                u"封の字が 1 通りに読めず、script が決めた所")
PHRASES = (u"読めること", u"読めないこと", u"封も予測も結果を見てから書き換えていない", u"判定は丸める前の数でした", u"予測の判定には使わない", u"書類の偏りに支えられている", u"理由は 4 つに固まっていた",
           u"どれも別の封が先。選ぶのは人間", u"断らなかった 61 本は全部同じ", u"(0 USD。別の封が先)", u"(有料。別の封と、払う前の知らせが先)", u"測った数ではない",
           u"作りから同値と申告", u"実装の監査の席が、元の包みを読めない形であることを仕掛けで確かめた(記録の欄ではない)")
MAIN_CLAIMS = (u"予測の 2 本(XM0-2・XM0-3)は外れ", u"1 本も無かった", u"型も対応表も答えから作った", u"620 のうち 519 は 1 本の書類", u"書類の偏りに支えられている", u"封 §0 の申告の数は足りていなかった",
               u"持ち込みは作っていない", u"断った書類が 1 本在る", u"当たり 8・外れ 2", u"外れは外れとして残す", u"XM0-1 は当たりなので", u"次の便の候補を 4 つ示す", u"型に入らなかった fact は対象の fact の 0.8%")
QUOTED = re.compile(u"「[^」]*(?:作れる|専用の道具が要らない|人が書ける|誤りが無くなる|会社が型を埋めれば|検査に通る)[^」]*」")
AFFIRM_WORDS = (u"作れる(?!か)", u"作れます", u"専用の道具が要らない", u"人が書ける(?!か)", u"誤りが無くなる", u"会社が型を埋めれば", u"検査に通る(?!こと|か)")
FORBIDDEN_WORDS = tuple(WG.FORBIDDEN_WORDS)
STRUCTURAL = WG.STRUCTURAL
# 記録から組んだ値の外に在ってよい数(字で留める。封の境・文書の見出しや説明の数)。理由は 1 つずつ:
#   0 1 2 3 4 5 6 8 10 = 項の番号・「4 つ」「3 つ」「2 つ」「5 本」「6 本以上」・判定の件数が封の境の表と別に在る数(8・2 は当たり 8・外れ 2 の字。記録から作り直す件数と照らす)
#   45 50 58 94 98 99 = 封 §4 の境(予測の字の要約) / 90 = 旗の「90% 未満」 / 0.5 = 封 §4 の XM0-3 の境 / 2.47 = 道具の版の字 2.47.5 の先頭(記録の材料の欄と別に縛る)
RESIDUAL_OK = set([u"1", u"2", u"3", u"4", u"5", u"6", u"8", u"10", u"45", u"50", u"58", u"94", u"98", u"99", u"90", u"0.5", u"2.47", u"67", u"62", u"1000"])
# 文書 §3(記録に欄の無い読み。監査の席の実物の読み)の行ごとの数の並び。記録から導けない = 正本は文書の字そのもの = ここに字で留める(留め)
SEC3_LINES = (
    (u"理由 (a) の fact は、当期末", ()),
    (u"理由 (d) の 24 は", (u"24",)),
    (u"理由 (e) の 64 のうち", (u"64", u"61", u"1", u"3", u"3")),
    (u"断った 1 本は、当期の始まりの日が", (u"1", u"2")),
    (u"これらは次の版の型の材料の候補で", ()),
)
SEC3_ONLY_PHRASES = (u"温室効果ガス", u"提出の回数を表す", u"決算期の変更", u"四半期の数", u"「円」「銭」", u"個別の印の在る文脈と無い文脈", u"次の版の型の材料の候補")      # §3 の外に主張として出てはならない字
SEC3_PHRASES = (u"測定の記録ではない", u"通貨でも株でも純数でもない単位", u"これが理由 (f) の 3 つと同じ fact かどうか", u"61 本に 1 つずつ在るのは", u"個別の印の在る文脈と無い文脈とで",
                u"そういう期が多いのか", u"測っていない", u"記録の欄からは言えない", u"測った数ではない", u"次の版の型の材料の候補", u"温室効果ガスの量の単位", u"提出の回数を表す", u"元から `format` を持たない",
                u"当期末・提出日・その N 年前のどれにも当たらない時点や期間", u"決算期の変更か、四半期の数か", u"「円」「銭」の字を含む表示の形", u"2 通り在った", u"記録の監査の席が実物を読んだ報告")


# ======================================================================================================
class Ctx(object):
    u"""検査が見る写し。変異はこの写しを変える(木の file は変えない)。"""

    def __init__(self):
        self.rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        self.doc = read(DOC_REL)
        self.seal = read(SEAL_REL)
        self.shas = collections.OrderedDict((rel, sha_file(rel)) for rel in SHA_PIN)

    def copy(self):
        c = Ctx.__new__(Ctx)
        c.rec = copy.deepcopy(self.rec)
        c.doc = self.doc
        c.seal = self.seal
        c.shas = collections.OrderedDict(self.shas)
        return c

    def with_doc(self, doc):
        u"""文書だけ替えた写し(記録は共有。文書の変異用。記録は変えない)。"""
        c = Ctx.__new__(Ctx)
        c.rec, c.seal, c.shas = self.rec, self.seal, self.shas
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


def nsum(x):
    u"""数 + 文(欄が {数, 文} の dict)。"""
    return x[u"数"] + x[u"文"]


# ======================================================================================================
# b 数え直し(script の関数は使わない)
def msum(ds):
    out = {}
    for d in ds:
        for k, v in d.items():
            out[k] = out.get(k, 0) + v
    return out


def nsum_docs(docs, path):
    u"""書類の path(キーの並び)の整数を足す。"""
    t = 0
    for d in docs:
        o = d
        for p in path:
            o = o[p]
        t += o
    return t


def cnt_true(docs, path):
    n = 0
    for d in docs:
        o = d
        for p in path:
            o = o[p]
        n += 1 if o else 0
    return n


def total_out(d):
    return nsum(d[u"型の外の fact"][u"合計"])


def agg_of(docs):
    u"""書類の列から、記録の集計の 1 組と同じ形を作る(script の関数を使わない別の数え方)。"""
    nd = [d for d in docs if not d[u"断った"]]
    dec = [d for d in docs if d[u"断った"]]
    stages = collections.OrderedDict((s, collections.OrderedDict()) for s in STAGES)
    for d in dec:
        r = stages[d[u"断った段"]]
        r[d[u"断った理由"]] = r.get(d[u"断った理由"], 0) + 1
    S = lambda *p: nsum_docs(docs, p)
    ext = u"型の外の fact"
    reasons = collections.OrderedDict((r, collections.OrderedDict((k, S(ext, u"理由ごと", r, k)) for k in (u"数", u"文"))) for r in LETTERS)
    num = collections.OrderedDict([
        (u"断った", len(dec)),
        (u"対象の fact", collections.OrderedDict((k, S(u"対象の fact", k)) for k in (u"数", u"文", u"隠し", u"脚注"))),
        (u"型に入った fact", collections.OrderedDict((k, S(u"型に入った fact", k)) for k in (u"数", u"文"))),
        (ext, collections.OrderedDict([(u"理由ごと", reasons), (u"合計", collections.OrderedDict((k, S(ext, u"合計", k)) for k in (u"数", u"文")))])),
        (u"型の行", collections.OrderedDict((k, S(u"型の行", k)) for k in (u"数", u"文", u"2 つ以上の fact をまとめた行", u"値が -0 の行"))),
        (u"対応表の行", collections.OrderedDict((k, S(u"対応表の行", k)) for k in (u"科目", u"軸", u"member", u"_cor で終わらない名"))),
        (u"持ち込みの属性を持つ fact", collections.OrderedDict([(u"数", S(u"持ち込みの属性を持つ fact", u"数")), (u"文", S(u"持ち込みの属性を持つ fact", u"文")),
                                                          (u"属性ごと", msum([d[u"持ち込みの属性を持つ fact"][u"属性ごと"] for d in docs]))])),
        (u"文脈の定義", collections.OrderedDict((k, S(u"文脈の定義", k)) for k in (u"作った", u"作らなかった"))),
        (u"単位の定義", collections.OrderedDict((k, S(u"単位の定義", k)) for k in (u"作った", u"作らなかった"))),
        (u"比べ方 1", collections.OrderedDict([(u"属性が意味として同じ", cnt_true(docs, (u"比べ方 1", u"属性が意味として同じ"))), (u"文脈の名も同じ", cnt_true(docs, (u"比べ方 1", u"文脈の名も同じ"))),
                                            (u"違った fact", S(u"比べ方 1", u"違った fact")), (u"属性ごとの違った fact", msum([d[u"比べ方 1"][u"属性ごとの違った fact"] for d in docs]))])),
        (u"比べ方 2", collections.OrderedDict((k, cnt_true(docs, (u"比べ方 2", k))) for k in (u"組めた", u"fact が意味として同じ", u"字も含めて行が同じ", u"鳴り方が同じ", u"2 回が同じ"))),
        (u"混ぜ物", collections.OrderedDict((k, cnt_true(docs, (u"混ぜ物", k))) for k in (u"作れた", u"効いた"))),
        (u"表示の字の検査", collections.OrderedDict((k, S(u"表示の字の検査", k)) for k in (u"掛けた fact", u"合った fact")))])
    return collections.OrderedDict([
        (K_DOCS, len(docs)), (u"断った書類", len(dec)), (u"断った段と理由ごと", stages), (u"型の外の fact が 0 の書類", sum(1 for d in nd if total_out(d) == 0)), (u"数", num),
        (u"作らなかった文脈の定義が 1 つ以上在る書類", sum(1 for d in docs if d[u"文脈の定義"][u"作らなかった"] > 0)),
        (u"型から作る命令の秒の合計", round(sum(d[u"秒"][u"型から作る命令"] or 0 for d in docs), 1))])


def split_docs(rec):
    docs = rec[K_DOCS]
    return [d for d in docs if d[u"番号"] <= DEV_COUNT], [d for d in docs if d[u"番号"] > DEV_COUNT]


def zero_like(o):
    if isinstance(o, dict):
        return all(zero_like(v) for v in o.values())
    if isinstance(o, bool):
        return not o
    if isinstance(o, (int, float)):
        return o == 0
    return o is None or o == u""


def doc_problems(d):
    u"""書類 1 つの中の関係。"""
    out = []
    n = d[u"番号"]
    if list(d) != list(DOC_KEYS):
        return [u"書類 %s の欄が違う" % n]
    dec = d[u"断った"]
    if dec != bool(d[u"断った段"]) or dec != bool(d[u"断った理由"]) or (dec and d[u"断った段"] not in STAGES):
        out.append(u"書類 %d の断りの欄の形が違う" % n)
    cnt, inn, o = d[u"対象の fact"], d[u"型に入った fact"], d[u"型の外の fact"]
    if list(o) != [u"理由ごと", u"合計"] or list(o[u"理由ごと"]) != list(LETTERS):
        return out + [u"書類 %d の型の外の欄の形が違う" % n]
    if dec:
        rest = dict((k, v) for k, v in d.items() if k not in (u"番号", u"断った", u"断った段", u"断った理由"))
        if not zero_like(rest):
            out.append(u"書類 %d は断ったのに数・結果が 0 でない" % n)
        return out
    for k in (u"数", u"文"):
        if inn[k] + o[u"合計"][k] != cnt[k]:
            out.append(u"書類 %d の %s: 型に入った fact + 型の外の fact が対象の fact と違う" % (n, k))
        rs = [o[u"理由ごと"][r][k] for r in LETTERS]
        if max(rs) > o[u"合計"][k] or sum(rs) < o[u"合計"][k] or min(rs) < 0:
            out.append(u"書類 %d の %s: 理由ごとの数が合計と合わない(最大 ≤ 合計 ≤ 和)" % (n, k))
    rows = d[u"型の行"]
    if rows[u"数"] > inn[u"数"] or rows[u"文"] > inn[u"文"] or rows[u"値が -0 の行"] > rows[u"数"] or rows[u"2 つ以上の fact をまとめた行"] > rows[u"数"] + rows[u"文"]:
        out.append(u"書類 %d の型の行が型に入った fact より多い" % n)
    c1, c2, mx, ck = d[u"比べ方 1"], d[u"比べ方 2"], d[u"混ぜ物"], d[u"表示の字の検査"]
    if c1[u"文脈の名も同じ"] and not c1[u"属性が意味として同じ"]:
        out.append(u"書類 %d: 文脈の名も同じなのに属性が意味として同じでない" % n)
    if c1[u"属性が意味として同じ"] and (c1[u"違った fact"] != 0 or c1[u"属性ごとの違った fact"]):
        out.append(u"書類 %d: 属性が意味として同じなのに違った fact が在る" % n)
    if sum(c1[u"属性ごとの違った fact"].values()) != c1[u"違った fact"] and not (c1[u"属性ごとの違った fact"] == {} and c1[u"違った fact"] == 0):
        out.append(u"書類 %d: 属性ごとの違った fact の和が違った fact と違う" % n)
    if (c2[u"字も含めて行が同じ"] or c2[u"鳴り方が同じ"] or c2[u"2 回が同じ"] or c2[u"fact が意味として同じ"]) and not c2[u"組めた"]:
        out.append(u"書類 %d: 組めていないのに比べ方 2 の結果が在る" % n)
    if c2[u"字も含めて行が同じ"] and not c2[u"fact が意味として同じ"]:
        out.append(u"書類 %d: 字も含めて同じなのに fact が意味として同じでない" % n)
    if mx[u"効いた"] and not mx[u"作れた"]:
        out.append(u"書類 %d: 作れなかった混ぜ物が効いた" % n)
    if not (0 <= ck[u"合った fact"] <= ck[u"掛けた fact"] <= inn[u"数"]):
        out.append(u"書類 %d: 表示の字の検査の数が合わない" % n)
    if d[u"秒"][u"型から作る命令"] is None or d[u"秒"][u"型から作る命令"] < 0:
        out.append(u"書類 %d: 型から作る命令の秒が無い" % n)
    return out


def pred_expected(rec):
    P = rec[K_SUM][G_PROD]
    N = P[u"数"]
    o = N[u"型の外の fact"]
    n_docs = P[K_DOCS]
    two = lambda a, b, ka, kb: collections.OrderedDict([(ka, a), (kb, b)])
    return collections.OrderedDict([
        (PK[0], two(N[u"比べ方 2"][u"fact が意味として同じ"], n_docs, u"書類", u"分母")),
        (PK[1], two(P[u"型の外の fact が 0 の書類"], n_docs, u"書類", u"分母")),
        (PK[2], two(nsum(o[u"合計"]), nsum(N[u"対象の fact"]), u"fact", u"分母(対象の fact)")),
        (PK[3], collections.OrderedDict((r, nsum(o[u"理由ごと"][r])) for r in LETTERS)),
        (PK[4], two(N[u"比べ方 1"][u"文脈の名も同じ"], n_docs, u"書類", u"分母")),
        (PK[5], two(P[u"作らなかった文脈の定義が 1 つ以上在る書類"], n_docs, u"書類", u"分母")),
        (PK[6], two(N[u"比べ方 2"][u"鳴り方が同じ"], n_docs, u"書類", u"分母")),
        (PK[7], two(N[u"混ぜ物"][u"効いた"], N[u"混ぜ物"][u"作れた"], u"効いた", u"作れた")),
        (PK[8], two(N[u"型の行"][u"数"], N[u"型に入った fact"][u"数"], u"行", u"分母(型に入った数の fact)")),
        (PK[9], two(N[u"表示の字の検査"][u"合った fact"], N[u"表示の字の検査"][u"掛けた fact"], u"合った", u"分母(掛けた fact)"))])


def recount_problems(c):
    rec = c.rec
    out = []
    docs = rec[K_DOCS]
    m = rec[u"材料"]
    nums = [d[u"番号"] for d in docs]
    if nums != list(range(1, DOC_COUNT + 1)) or len(docs) != DOC_COUNT:
        return [u"書類の番号が 1〜67 の昇順 67 個でない"]
    for k, v in MATERIAL_PIN.items():
        if m[k] != v:
            out.append(u"材料の欄が字で留めた値と違う: %s" % k)
    dev, prod = split_docs(rec)
    if len(dev) != DEV_COUNT or len(prod) != PROD_COUNT:
        return out + [u"開発の 5 本と本番だけの 62 本の分けが違う"]
    for d in docs:
        out.extend(doc_problems(d))
    if list(rec[K_SUM]) != list(GROUPS):
        return out + [u"集計の欄の名が違う"]
    for key, ds in ((G_DEV, dev), (G_PROD, prod), (G_ALL, docs)):
        if norm(rec[K_SUM][key]) != norm(agg_of(ds)):
            out.append(u"%s の集計が書類ごとの数から数え直した値と違う" % key)
    if list(rec[PRED_KEY]) != list(PK):
        return out + [u"予測の判定に要る数の欄の名が違う"]
    if norm(rec[PRED_KEY]) != norm(pred_expected(rec)):
        out.append(u"予測の判定に要る数が集計から作り直した値と違う")
    if rec[K_SUM][G_PROD][K_DOCS] != PROD_COUNT or rec[K_SUM][G_DEV][K_DOCS] != DEV_COUNT or rec[K_SUM][G_ALL][K_DOCS] != DOC_COUNT:
        out.append(u"集計の書類の数が 5・62・67 でない")
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
    if c.rec[u"step"] != u"XM0(機械の側が決めた入力の型(第 0 版)と対応表だけから fact の属性と文脈・単位の定義を作ると、公開の道具が読む fact は元と意味として同じになるか。型に入らない fact は何か)(0 USD・engine は読まない)":
        out.append(u"記録の step の欄が違う")
    sd = c.rec[u"script の決めの字"]
    if list(sd[u"型の外の理由"]) != list(LETTERS) or sd[u"format"] != u"ixt:numdotdecimal" or sd[u"桁あふれの守り"] != 1000 or len(sd[u"単位の形"]) != 4:
        out.append(u"記録の script の決めの字が違う")
    return out


DATE_FORM = re.compile(r"(?<![0-9])(?:19|20)\d{2}[-/.]\d{1,2}[-/.]\d{1,2}(?![0-9])|(?<![0-9])(?:19|20)\d{2}年\d{1,2}月")


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
    if DATE_FORM.search(text.replace(SEAL_REL, u"")):
        out.append(u"記録に日付の形が在る(封 §3 は日付を持たないと決めた。script の検査は日付を見ないので、門が見る)")
    return out


def bound_problems(c):
    out = [u"封に字が無い: %s" % p[:24] for p in BOUND_SEAL_PHRASES if p not in c.seal]
    sec4 = section(c.seal, u"## §4 ", u"## §5 ")
    rows = [ln for ln in sec4.splitlines() if re.match(r"^\| XM0-\d", ln)]
    if len(rows) != 10:
        out.append(u"封 §4 の表の行が 10 でない")
    sec7 = section(c.seal, u"## §7 ", None)
    if len([ln for ln in sec7.splitlines() if ln.startswith(u"- ")]) != 6:
        out.append(u"封 §7 の限界の行が 6 行でない")
    sec0 = section(c.seal, u"## §0 ", u"## §0-2 ")
    if u"数の fact 4982" not in sec0 or u"本番だけの 62 本では上のどれも数えていない" not in sec0:
        out.append(u"封 §0 の開発の 5 本の申告(4982)が無い")
    return out


# ======================================================================================================
# c 当たり外れの決め直し(封 §4 の境。丸める前の整数。本番だけの 62 本)
def judge_nums(n_docs, same2, zero_docs, out_total, tgt_total, reasons, same_ctx, no_made, ring, eff, made, rows, in_num, ok_disp, tried):
    u"""封 §4 の境(整数のまま)。値は (当たりか, 外れた向き)。reasons は理由 → fact の数(数 + 文)の dict。"""
    out = collections.OrderedDict()
    out[u"XM0-1"] = (same2 >= 58, u"" if same2 >= 58 else u"下")
    out[u"XM0-2"] = (zero_docs >= 45, u"" if zero_docs >= 45 else u"下")
    out[u"XM0-3"] = (1000 * out_total <= 5 * tgt_total, u"" if 1000 * out_total <= 5 * tgt_total else u"上")
    others = max(v for r, v in reasons.items() if r != u"a")
    if sum(reasons.values()) == 0:
        out[u"XM0-4"] = (False, u"判定できない")
    else:
        out[u"XM0-4"] = (reasons[u"a"] > others, u"" if reasons[u"a"] > others else u"他")
    out[u"XM0-5"] = (same_ctx >= 50, u"" if same_ctx >= 50 else u"下")
    out[u"XM0-6"] = (no_made <= 10, u"" if no_made <= 10 else u"上")
    out[u"XM0-7"] = (ring >= 45, u"" if ring >= 45 else u"下")
    out[u"XM0-8"] = (made > 0 and eff == made, u"" if made > 0 and eff == made else u"下")
    lo9, hi9 = 100 * rows >= 94 * in_num, 100 * rows < 98 * in_num
    out[u"XM0-9"] = (lo9 and hi9, u"" if lo9 and hi9 else u"下" if not lo9 else u"上")
    out[u"XM0-10"] = (tried > 0 and 100 * ok_disp >= 99 * tried, u"" if tried > 0 and 100 * ok_disp >= 99 * tried else u"下")
    return out


def reasons_of(P):
    o = P[u"数"][u"型の外の fact"][u"理由ごと"]
    return collections.OrderedDict((r, nsum(o[r])) for r in LETTERS)


def judge(rec):
    P = rec[K_SUM][G_PROD]
    N = P[u"数"]
    return judge_nums(P[K_DOCS], N[u"比べ方 2"][u"fact が意味として同じ"], P[u"型の外の fact が 0 の書類"], nsum(N[u"型の外の fact"][u"合計"]), nsum(N[u"対象の fact"]), reasons_of(P),
                      N[u"比べ方 1"][u"文脈の名も同じ"], P[u"作らなかった文脈の定義が 1 つ以上在る書類"], N[u"比べ方 2"][u"鳴り方が同じ"], N[u"混ぜ物"][u"効いた"], N[u"混ぜ物"][u"作れた"],
                      N[u"型の行"][u"数"], N[u"型に入った fact"][u"数"], N[u"表示の字の検査"][u"合った fact"], N[u"表示の字の検査"][u"掛けた fact"])


def nondeclined_prod(rec):
    return [d for d in split_docs(rec)[1] if not d[u"断った"]]


def flags_expected(rec):
    u"""封 §4 の「先に自分の欠陥を疑う」旗 6 つ(門の中で書類ごとから導く)。値と旗。"""
    P = rec[K_SUM][G_PROD]
    N = P[u"数"]
    nd = nondeclined_prod(rec)
    out_t = nsum(N[u"型の外の fact"][u"合計"])
    in_t, tgt_t = nsum(N[u"型に入った fact"]), nsum(N[u"対象の fact"])
    diff = sum(1 for d in nd if d[u"比べ方 1"][u"属性が意味として同じ"] and not d[u"比べ方 2"][u"fact が意味として同じ"])
    not_made = sum(1 for d in nd if not d[u"混ぜ物"][u"作れた"])
    neg0 = N[u"型の行"][u"値が -0 の行"]
    return collections.OrderedDict([
        (FLAG_KEYS[0], collections.OrderedDict([(u"型の外の fact", out_t), (u"旗", out_t == 0)])),
        (FLAG_KEYS[1], collections.OrderedDict([(u"型に入った fact", in_t), (u"対象の fact", tgt_t), (u"旗", 100 * in_t < 90 * tgt_t)])),
        (FLAG_KEYS[2], collections.OrderedDict([(u"書類", diff), (u"旗", diff > 0)])),
        (FLAG_KEYS[3], collections.OrderedDict([(u"作れなかった書類", not_made), (u"旗", not_made >= 6)])),
        (FLAG_KEYS[4], collections.OrderedDict([(u"断った書類", P[u"断った書類"]), (u"旗", P[u"断った書類"] >= 6)])),
        (FLAG_KEYS[5], collections.OrderedDict([(u"値が -0 の行", neg0), (u"旗", neg0 == 0)]))])


def suspects(c):
    return tuple(v[u"旗"] for v in flags_expected(c.rec).values())


PRED_TEXT = collections.OrderedDict([
    (u"XM0-1", u"道具が読む fact が意味として同じ書類は 58 本以上"), (u"XM0-2", u"型の外の fact が 0 の書類は 45 本以上"), (u"XM0-3", u"型の外の fact は対象の fact の 0.5% 以下"),
    (u"XM0-4", u"型の外の理由でいちばん fact が多いのは (a)"), (u"XM0-5", u"文脈の名も同じ書類は 50 本以上"), (u"XM0-6", u"元に在って作らなかった文脈の定義が 1 つ以上在る書類は 10 本以下"),
    (u"XM0-7", u"鳴り方が同じ書類は 45 本以上"), (u"XM0-8", u"混ぜ物が効いた書類は、作れた書類の全部"), (u"XM0-9", u"数の型の行は、型に入った数の fact の 94% 以上 98% 未満"),
    (u"XM0-10", u"表示の字の検査が合う fact は 99% 以上")])


def reason_cell(P):
    rs = reasons_of(P)
    items = sorted(((r, v) for r, v in rs.items() if v > 0), key=lambda t: (-t[1], t[0]))
    return u"・".join(u"(%s) %d" % (r, v) for r, v in items)


def cell_text(rec, key):
    P = rec[K_SUM][G_PROD]
    N = P[u"数"]
    nd = P[K_DOCS]
    return {u"XM0-1": u"%d 本(%d 本のうち)" % (N[u"比べ方 2"][u"fact が意味として同じ"], nd),
            u"XM0-2": u"%d 本(%d 本のうち)" % (P[u"型の外の fact が 0 の書類"], nd),
            u"XM0-3": f(nsum(N[u"型の外の fact"][u"合計"]), nsum(N[u"対象の fact"])),
            u"XM0-4": reason_cell(P),
            u"XM0-5": u"%d 本" % N[u"比べ方 1"][u"文脈の名も同じ"], u"XM0-6": u"%d 本" % P[u"作らなかった文脈の定義が 1 つ以上在る書類"], u"XM0-7": u"%d 本" % N[u"比べ方 2"][u"鳴り方が同じ"],
            u"XM0-8": u"効いた %d・作れた %d" % (N[u"混ぜ物"][u"効いた"], N[u"混ぜ物"][u"作れた"]),
            u"XM0-9": f(N[u"型の行"][u"数"], N[u"型に入った fact"][u"数"]),
            u"XM0-10": u"%d/%d" % (N[u"表示の字の検査"][u"合った fact"], N[u"表示の字の検査"][u"掛けた fact"])}[key]


def expected_cells(c):
    out = collections.OrderedDict()
    for k, (ok, way) in judge(c.rec).items():
        out[k] = (cell_text(c.rec, k), u"当たり" if ok else u"外れ")
    return out


def miss_ids(j):
    return [k for k in IDS if not j[k][0]]


NEXT_MARKS = (u"i", u"ii", u"iii", u"iv")
MARK_RE = re.compile(u"^  - \\((i|ii|iii|iv)\\) ", re.M)


def seal_candidates(s6):
    u"""封 §6 の次の便の候補 (i)〜(iv) を、封の字から取る(4 つ)。(iv) は封の字のまま・(i)〜(iii) は文書が「。別の封が先」を足す。"""
    line = [ln for ln in s6.splitlines() if ln.startswith(u"- 次の便の候補")][0]
    body = line[line.index(u"(i) "):]
    parts = re.split(u"(?<=[)]) (?=\\((?:ii|iii|iv)\\) )", body)
    assert len(parts) == 4, parts
    parts[3] = parts[3][:parts[3].index(u")。") + 1]
    items = []
    for p in parts:
        p = p.strip()
        if p.endswith(u"0 USD)"):
            p = p[:-len(u"0 USD)")] + u"0 USD。別の封が先)"
        items.append(p)
    return items


DECISION_RE = re.compile(u"^- XM0-1 は(当たり|外れ)なので")


def sec5_decision_problems(sec5, cond, s6):
    u"""封 §6(XM0-1 が当たりなら次の便の候補 (i)〜(iv) をちょうど示す。外れなら示さず、違った所の型を読む)と文書 §5 が合う。"""
    out = []
    p5 = plain(sec5)
    lines = [ln for ln in p5.splitlines() if ln.strip()]
    idx = [i for i, ln in enumerate(lines) if DECISION_RE.search(ln)]
    if len(idx) != 1:
        return [u"§5 に「XM0-1 は当たり(外れ)なので」の決めの行が 1 つでない"]
    head_i = idx[0]
    head = lines[head_i]
    tail = lines[head_i + 1:]
    marks = MARK_RE.findall(p5)
    shown = bool(marks)
    if cond != shown or cond != (DECISION_RE.search(head).group(1) == u"当たり"):
        out.append(u"封 §6 の決め(XM0-1 が当たりなら次の便の候補を示す・外れなら示さない)と文書 §5 が合わない")
    if cond:
        want = seal_candidates(s6)
        if marks != list(NEXT_MARKS):
            out.append(u"§5 の次の便の候補の見出しが (i)(ii)(iii)(iv) の 4 つだけでない: %s" % u",".join(marks))
        if tail != [u"  - " + w + u"。" for w in want]:
            out.append(u"§5 の次の便の候補の行が封 §6 の字(と「。別の封が先」)と違うか、後ろに別の行が在る")
        for w in (u"0 USD。別の封が先)", u"(有料。別の封と、払う前の知らせが先)"):
            if w not in p5:
                out.append(u"§5 の「%s」が落ちている" % w)
        if len(tail) != 4 or p5.count(u"0 USD。別の封が先)") != 3 or p5.count(u"(有料。別の封と、払う前の知らせが先)") != 1:
            out.append(u"§5 の費用の字が (i)(ii)(iii) の「0 USD。別の封が先」3 つ・(iv) の「有料…」1 つでない")
        if u"次の便の候補を 4 つ示す" not in head or u"選ぶのは人間" not in head or u"どれも別の封が先" not in head:
            out.append(u"§5 の決めの行に「次の便の候補を 4 つ示す」「どれも別の封が先」「選ぶのは人間」が無い")
    else:
        if u"違った所の型を読む" not in head or u"示さない" not in head or tail:
            out.append(u"外れたのに、違った所の型を読む・(i)〜(iv) は示さない、が §5 の最後の行に無いか、後ろに別の行が在る")
    return out


def verdict_problems(c):
    rec = c.rec
    j = judge(rec)
    want = expected_cells(c)
    out = []
    rows = {}
    for ln in c.doc.splitlines():
        m = re.match(r"^\| (XM0-\d+)(?:\(主\))? \|(.*)\|$", ln)
        if m:
            rows[m.group(1)] = [x.strip() for x in m.group(2).split(u"|")]
    if sorted(rows) != sorted(j):
        return [u"文書 §1 の表の行が XM0-1〜XM0-10 でない"]
    sec4 = section(c.seal, u"## §4 ", u"## §5 ")
    for k, cells in rows.items():
        if len(cells) != 3:
            out.append(u"%s の行の欄の数が違う" % k)
            continue
        if cells[0] != PRED_TEXT[k] or (SG.SEAL_BOUND_TEXT[k] if k != u"XM0-4" else u"(a)") not in cells[0]:
            out.append(u"%s の予測の字が門の留めた要約・封の境の字と違う: %s" % (k, cells[0]))
        srow = [x for x in sec4.splitlines() if re.match(r"^\| %s[^0-9]" % re.escape(k), x)]
        if len(srow) != 1 or SG.SEAL_BOUND_TEXT[k] not in srow[0]:
            out.append(u"%s の境の字が封 §4 の表に無い" % k)
        if cells[1] != want[k][0]:
            out.append(u"%s の実測の字が記録から組んだ字と違う: %s" % (k, cells[1]))
        if cells[2] != want[k][1]:
            out.append(u"%s の判定が決め直した判定と違う: %s(決め直し: %s)" % (k, cells[2], want[k][1]))
    if not re.search(r"^\| XM0-1\(主\) \|", c.doc, re.M):
        out.append(u"XM0-1 の行に「(主)」が無い(封 §4 の主の読み)")
    for k in IDS[1:]:
        if re.search(r"^\| %s\(主\) \|" % k, c.doc, re.M):
            out.append(u"%s の行に「(主)」が付いている(封 §4 の主は XM0-1 だけ)" % k)
    hits = sum(1 for v in j.values() if v[0])
    if u"- 当たり %d・外れ %d。" % (hits, len(j) - hits) not in c.doc.splitlines():
        out.append(u"文書の件数の行が決め直した件数と違う")
    head = plain(c.doc.split(u"## §1")[0])
    miss = miss_ids(j)
    if u"判定した %d 本は 当たり %d・外れ %d。" % (len(j), hits, len(j) - hits) not in head:
        out.append(u"文書の頭の件数が決め直した値と違う")
    if miss and u"予測の %d 本(%s)は外れ。" % (len(miss), u"・".join(miss)) not in head:
        out.append(u"外れた予測の言い切りが文書の頭に無い(%s)" % u"・".join(miss))
    if not miss and re.search(u"予測の[^。]*本[^。]*は外れ", head):
        out.append(u"外れが無いのに文書の頭が外れと書いている")
    if u"XM0-1" in miss:
        if u"主の予測の" not in head:
            out.append(u"外れた主の予測の言い切りが文書の頭に無い")
    elif re.search(u"主の予測の[^。]*は外れ", head):
        out.append(u"主の予測は当たりなのに文書の頭が外れと書いている")
    sec1, sec5 = section(c.doc, u"## §1 ", u"## §2 "), section(c.doc, u"## §5 ", None)
    sus = suspects(c)
    if any(sus):
        out.append(u"封 §4 の「先に自分の欠陥を疑う」旗が立っている: %s" % (sus,))
    line = [ln for ln in sec1.splitlines() if u"「先に自分の欠陥を疑う」旗" in ln]
    if len(line) != 1 or line[0].count(u"立たない") != 5 or u"― 無い。" not in line[0]:
        out.append(u"文書 §1 の自己点検の言い切り(旗 6 つ・どれも立たない)が封の字・記録と合わない")
    cond = j[u"XM0-1"][0]
    s6 = section(c.seal, u"## §6 ", u"## §7 ")
    out.extend(sec5_decision_problems(sec5, cond, s6))
    # 判定の表に 5 本・67 本の数が混ざらない(本番だけの 62 本の数だけ)
    only_other = set()
    for key in (G_DEV, G_ALL):
        ints_in(rec[K_SUM][key], only_other)
    only_prod = set()
    ints_in(rec[K_SUM][G_PROD], only_prod)
    ints_in(rec[PRED_KEY], only_prod)
    mixed = [t for ln in rows for t in doc_number_tokens(u" ".join(rows[ln])) if t in only_other and t not in only_prod and t not in STRUCTURAL]
    if mixed:
        out.append(u"判定の表に 5 本・全部だけの数が混ざっている: %s" % u",".join(mixed))
    return out


# ======================================================================================================
# d 文書の数・主な主張の文(§3 以外の全部の行を記録と字から組み直す)
def stat_values(rec):
    u"""書類ごとから導く数(本番だけの 62 本のうち断らなかった書類)。"""
    nd = nondeclined_prod(rec)
    dev = split_docs(rec)[0]
    reasons = collections.OrderedDict()
    for r in LETTERS:
        v = [nsum(d[u"型の外の fact"][u"理由ごと"][r]) for d in nd]
        reasons[r] = (sum(nsum(d[u"型の外の fact"][u"理由ごと"][r]) for d in nd), sum(1 for x in v if x > 0), max(v))
    tot = sorted(total_out(d) for d in nd)
    one = [d for d in nd if total_out(d) == 1]
    one_e = all([r for r in LETTERS if nsum(d[u"型の外の fact"][u"理由ごと"][r]) > 0] == [u"e"] for d in one)
    big = [d for d in nd if total_out(d) == tot[-1]][0]
    other = [sum(nsum(d[u"型の外の fact"][u"理由ごと"][r]) for r in OTHER_REASONS) for d in nd]
    sums_cells = sum(nsum(rec[K_SUM][G_PROD][u"数"][u"型の外の fact"][u"理由ごと"][r]) for r in LETTERS)
    return collections.OrderedDict([
        (u"reasons", reasons), (u"nd", len(nd)), (u"one", len(one)), (u"one_e", one_e), (u"top3", tot[-3:][::-1]), (u"big_target", nsum(big[u"対象の fact"])),
        (u"neg0_docs", sum(1 for d in nd if d[u"型の行"][u"値が -0 の行"] > 0)), (u"units4", all(d[u"単位の定義"][u"作った"] == 4 for d in nd)), (u"units_n", sum(1 for d in nd if d[u"単位の定義"][u"作った"] == 4)),
        (u"other_docs", sum(1 for x in other if x > 0)), (u"other_sum", sum(other)), (u"other_max", max(other)), (u"cells", sums_cells),
        (u"dev_e", [nsum(d[u"型の外の fact"][u"理由ごと"][u"e"]) for d in dev]), (u"dev_total", [total_out(d) for d in dev])])


def render_doc(c):
    u"""記録(と字で留めた文)から、文書の §3 以外の全部の行を組み直す。§3 は文書の字を差し込む(sec3_problems が見る)。"""
    rec = c.rec
    sec3 = section(c.doc, u"## §3 ", u"## §4 ")
    Dv, Pr, Al = rec[K_SUM][G_DEV], rec[K_SUM][G_PROD], rec[K_SUM][G_ALL]
    PN, DN = Pr[u"数"], Dv[u"数"]
    st = stat_values(rec)
    j = judge(rec)
    hits = sum(1 for v in j.values() if v[0])
    miss = miss_ids(j)
    cells = expected_cells(c)
    tgt, inn, out_ = PN[u"対象の fact"], PN[u"型に入った fact"], PN[u"型の外の fact"][u"合計"]
    rs = st[u"reasons"]
    zero_docs = Pr[u"型の外の fact が 0 の書類"]
    nd = st[u"nd"]
    L = []
    w = L.append
    w(u"# 結果: 便 XM0 ― 機械の側が決めた入力の型(第 0 版)と対応表だけから、fact の属性と文脈・単位の定義を作ると、道具が読む fact は元と意味として同じになったか。型に入らなかった fact は何か ― 2026-11-22")
    w(u"")
    w(u"封 `%s`(commit %s)。script `%s` と封の門 `%s` は commit %s(独立監査 REVISE → 直し → GO。REVISE は門の穴 3 つで、script は 1 回目から変えていない)。"
      u"記録 `%s` は commit %s(独立監査 GO。断った 1 本を除く %d 本を別の実装で数え直して一致)。費用は 0 USD。engine(`core/`・`adapters/`)は 0 行。" % (
          SEAL_REL, SEAL_COMMIT_SHORT, SCRIPT_REL, SEAL_GATE_REL, SCRIPT_COMMIT_SHORT, RECORD_REL, RECORD_COMMIT_SHORT, Al[K_DOCS] - Al[u"断った書類"]))
    w(u"")
    w(u"この文書の §1・§2 の数は全部、記録から 1 つずつ読んだもの(結果の門が、記録の数と字で同じことを見る)。§3 は記録に欄の無い読みで、出どころを書く。")
    w(u"")
    w(u"**先に負けと限界を書く。**")
    w(u"")
    w(u"- **予測の %d 本(%s)は外れ。** 型の外の fact が 0 の書類は %d 本のうち %d 本(予測は 45 本以上)。型の外の fact は %sで、予測の 0.5%% 以下を超えた。"
      u"**第 0 版の型のままで全部の fact が入る書類は 1 本も無かった。**" % (len(miss), u"・".join(miss), Pr[K_DOCS], zero_docs, f(nsum(out_), nsum(tgt))))
    w(u"- **型も対応表も答えから作った。** 型・対応表・持ち込み・型の外は、どれも受理済みの XBRL から作った。型の外の fact は元から写すので、その fact が元と同じになるのは当たり前。"
      u"**会社がこの型で情報を用意できるか・対応表を作れるか・埋めた中身が正しいかは測っていない。** この便の数は「会社が型を埋めれば XBRL が作れる」とは読まない。")
    w(u"- **持ち込みは作っていない。** 素の本文・fact の置き場・どの置き場がどの数か・文の中身・脚注・提出者別タクソノミの表は、元から写した。")
    w(u"- **主の予測(XM0-1)と XM0-8 は作りから当たりやすい**(封 §4 の字)。規則どおりに作れば戻るはずのものが戻った、という数。")
    w(u"- **断った書類が %d 本在る**(型を作る命令で「書類の決めが 1 通りに決まらない」)。この %d 本は fact を 1 つも数えていない。" % (Pr[u"断った書類"], Pr[u"断った書類"]))
    w(u"- 型の欄と規則(期の名の 3 つの型・単位の 4 つの形・`format` の 1 通り・個別の軸と member)は開発の 5 本を見て決めた。62 本は前の便で数えた書類で、未使用ではない。67 本は無作為ではない。有報だけ。")
    w(u"- 比べ方 2 は `contextRef` の字を見ず、`unitRef` は measure に置き換えて比べる。字まで同じかは別の数で書く。道具 1 つ(道具 P。本家の版でない)の fact の一覧だけで、EDINET の本物の検査とは照らしていない。"
      u"`.xbrl` を落とした包み。script は前の便の script を経て engine の module を間接に読み込む。")
    w(u"- 混ぜ物は 1 本につき 1 つ・対象の欄だけ。ほかの欄を変えた確かめは封の門の作り物だけ。")
    w(u"- 文の fact は、型が持つのは科目・期間・対象・次元だけで、文の中身と書式の属性は持ち込み。")
    w(u"- 対象の `既定` は「個別の印が無い」という意味で、連結とは限らない。")
    w(u"- 判定した %d 本は 当たり %d・外れ %d。予測は司令塔が立てた。盲検ではない。" % (len(j), hits, len(j) - hits))
    w(u"- **「XBRL を作れる」「専用の道具が要らない」「どんな資料も作れる」「誤りが無くなる」は、この便からは言えない。**")
    w(u"")
    w(u"**日付つきの補足(2026-11-22。封は書き換えていない)。**")
    w(u"")
    w(u"- **封 §0 の申告の数は足りていなかった。** 封 §0 は開発の 5 本の数の fact を %d と申告したが、実装が数えた対象の数の fact は %d。差の %d は、書類ごとに 1 つ在る、`hidden` の中の `format` を持たない空でない数の fact で、"
      u"下調べの席が数え漏らした。この fact は封 §1 の理由 (e) の字どおり型の外になる。XM0-2 の外れはこの数え漏らしから来ている。外れは外れとして残す。" % (
          SEAL_DECLARED, DN[u"対象の fact"][u"数"], DN[u"対象の fact"][u"数"] - SEAL_DECLARED))
    w(u"- **型の値の大きさは、作る XBRL の側に効かない。** 本文の表示の字は持ち込みなので、型の値のうち出力を決めるのは符号と「無い」だけ。大きさを縛るのは表示の字の検査(XM0-10)だけ。")
    w(u"- **封の字が 1 通りに読めず、script が決めた所**(封の門が字で留めている): `resources` の部が 2 つ以上在る書類は断る・`scale` の属性が無い空でない数の fact には、作る側で `scale` を付ける"
      u"(比べ方 1 はこの差を「違い」に数えない)・提出者の識別子は当期末の時点の文脈から取る・`unitRef` の無い数の fact は理由 (d)・`sign` が `-` でない字なら理由 (f)・"
      u"`decimals` か `scale` の大きさが 1000 を超えたら理由 (e)・空の fact が `format` を持てば理由 (h)・対応表は個別の軸と member を持たない・「元に在って作らなかった定義」は中身で数える。")
    w(u"")
    w(u"## §1 予測の当たり外れ(司令塔。盲検ではない)")
    w(u"")
    w(u"封 §4 の字の境と記録から、結果の門が XM0-1〜XM0-10 の当たり外れを決め直した(この表と同じ)。封も予測も結果を見てから書き換えていない。判定は丸める前の数でした。分母は本番だけの %d 本。" % Pr[K_DOCS])
    w(u"")
    w(u"| # | 予測(封の字の要約) | 実測(記録) | 判定 |")
    w(u"|---|---|---|---|")
    for k in IDS:
        w(u"| %s%s | %s | %s | %s |" % (k, u"(主)" if k == u"XM0-1" else u"", PRED_TEXT[k], cells[k][0], cells[k][1]))
    w(u"")
    w(u"- 当たり %d・外れ %d。" % (hits, len(j) - hits))
    w(u"- XM0-1 で同じにならなかった %d 本は、断った %d 本。断らなかった %d 本は全部同じ。" % (Pr[K_DOCS] - PN[u"比べ方 2"][u"fact が意味として同じ"], Pr[u"断った書類"], PN[u"比べ方 2"][u"fact が意味として同じ"]))
    w(u"- XM0-4 の当たりは書類の偏りに支えられている。(a) の %d は %d 本の書類にだけ在り、そのうち %d は 1 本。書類の数で見ると、いちばん多くの書類に在る理由は (e)(%d 本)。" % (
        rs[u"a"][0], rs[u"a"][1], rs[u"a"][2], rs[u"e"][1]))
    fl = flags_expected(rec)
    w(u"- 封 §4 の「先に自分の欠陥を疑う」旗: 型の外の fact が %d 本の全部で 0 ― 立たない(%d)。型に入った fact が対象の fact の 90%% 未満 ― 立たない(%d/%d)。"
      u"属性が意味として同じなのに道具の fact が違う書類 ― 無い。混ぜ物を作れなかった書類が 6 本以上 ― 立たない(断らなかった %d 本の全部で作れた)。断った書類が 6 本以上 ― 立たない(%d 本)。"
      u"値が `-0` の行が 0 ― 立たない(%d)。" % (Pr[K_DOCS], fl[FLAG_KEYS[0]][u"型の外の fact"], fl[FLAG_KEYS[1]][u"型に入った fact"], fl[FLAG_KEYS[1]][u"対象の fact"], nd - fl[FLAG_KEYS[3]][u"作れなかった書類"],
                                  fl[FLAG_KEYS[4]][u"断った書類"], fl[FLAG_KEYS[5]][u"値が -0 の行"]))
    w(u"")
    w(u"## §2 数(記録)")
    w(u"")
    w(u"材料: %d 本(開発の 5 本・本番だけの 62 本)。道具の版は 2.47.5。下の数は、断らないかぎり本番だけの %d 本(うち断った %d 本は fact を数えていないので、fact の数は %d 本の分)。" % (
        Al[K_DOCS], Pr[K_DOCS], Pr[u"断った書類"], nd))
    w(u"")
    dst = Pr[u"断った段と理由ごと"]
    w(u"**断り**: 断った書類は %d 本(型を作る命令。「書類の決めが 1 通りに決まらない」)。型から作る命令・組む命令・道具で断った書類は %d 本。" % (
        Pr[u"断った書類"], sum(sum(dst[s].values()) for s in (u"型から作る", u"組む", u"道具"))))
    w(u"")
    w(u"**対象の fact と型**:")
    w(u"")
    w(u"| | 数の fact | 文の fact | 合計 |")
    w(u"|---|---|---|---|")
    w(u"| 対象の fact | %d | %d | %d |" % (tgt[u"数"], tgt[u"文"], nsum(tgt)))
    w(u"| 型に入った fact | %d | %d | %d |" % (inn[u"数"], inn[u"文"], nsum(inn)))
    w(u"| 型の外の fact | %d | %d | %d |" % (out_[u"数"], out_[u"文"], nsum(out_)))
    w(u"")
    w(u"- 対象の fact のうち `hidden` の中のものは %d。脚注(対象の外)は %d。" % (tgt[u"隠し"], tgt[u"脚注"]))
    rows = PN[u"型の行"]
    w(u"- 型の行: 数 %d・文 %d。2 つ以上の fact をまとめた行は %d。値が `-0` の行は %d(%d 本の書類に在る)。" % (rows[u"数"], rows[u"文"], rows[u"2 つ以上の fact をまとめた行"], rows[u"値が -0 の行"], st[u"neg0_docs"]))
    mp = PN[u"対応表の行"]
    w(u"- 対応表の行: 科目 %d・軸 %d・member %d。そのうち接頭辞が `_cor` で終わらない名は %d。" % (mp[u"科目"], mp[u"軸"], mp[u"member"], mp[u"_cor で終わらない名"]))
    ca = PN[u"持ち込みの属性を持つ fact"]
    w(u"- 持ち込みの属性を持つ fact: 数 %d・文 %d。" % (ca[u"数"], ca[u"文"]))
    w(u"")
    w(u"**型の外の理由ごと**(重ねて数える。理由ごとの数の和は %d で、合計 %d より %d 多い = %d つの fact が 2 つの理由に当たる):" % (
        st[u"cells"], nsum(out_), st[u"cells"] - nsum(out_), st[u"cells"] - nsum(out_)))
    w(u"")
    w(u"| 理由 | 数の fact | 文の fact | その理由の fact が在る書類 | 1 本の中の最大 |")
    w(u"|---|---|---|---|---|")
    rr = PN[u"型の外の fact"][u"理由ごと"]
    for r, label in REASON_LABEL.items():
        w(u"| %s | %d | %d | %d 本 | %d |" % (label, rr[r][u"数"], rr[r][u"文"], rs[r][1], rs[r][2]))
    w(u"| (b)(c)(g)(h) | %d | %d | %d 本 | %d |" % (sum(rr[r][u"数"] for r in OTHER_REASONS), sum(rr[r][u"文"] for r in OTHER_REASONS), st[u"other_docs"], st[u"other_max"]))
    w(u"")
    w(u"- 型の外の fact が 1 つだけの書類は %d 本で、その 1 つはどれも理由 (e)。" % st[u"one"])
    t3 = st[u"top3"]
    w(u"- 型の外の fact がいちばん多い書類は %d(その書類の対象の fact は %d)。次に多いのは %d・%d。**%d のうち %d は 1 本の書類。**" % (t3[0], st[u"big_target"], t3[1], t3[2], nsum(out_), t3[0]))
    w(u"")
    cx, un = PN[u"文脈の定義"], PN[u"単位の定義"]
    w(u"**作った定義**: 文脈の定義は %d を作り、元に在って作らなかったものは %d。単位の定義は %d を作り(%d 本のどれも 4 つ)、作らなかったものは %d。" % (
        cx[u"作った"], cx[u"作らなかった"], un[u"作った"], st[u"units_n"], un[u"作らなかった"]))
    w(u"")
    b1, b2, mx, ck = PN[u"比べ方 1"], PN[u"比べ方 2"], PN[u"混ぜ物"], PN[u"表示の字の検査"]
    w(u"**比べ方 1(属性)**: 属性が意味として同じ書類 %d・文脈の名も同じ書類 %d・違った fact %d。" % (b1[u"属性が意味として同じ"], b1[u"文脈の名も同じ"], b1[u"違った fact"]))
    w(u"")
    w(u"**比べ方 2(道具)**: 組めた %d・fact が意味として同じ %d・`contextRef` と `unitRef` の字も含めて行が同じ %d・鳴り方が同じ %d・2 回組んで包みが同じ %d。" % (
        b2[u"組めた"], b2[u"fact が意味として同じ"], b2[u"字も含めて行が同じ"], b2[u"鳴り方が同じ"], b2[u"2 回が同じ"]))
    w(u"")
    w(u"**混ぜ物**: 作れた %d・効いた %d。" % (mx[u"作れた"], mx[u"効いた"]))
    w(u"")
    w(u"**表示の字の検査**: 掛けた fact %d・合った fact %d。" % (ck[u"掛けた fact"], ck[u"合った fact"]))
    w(u"")
    dtg = DN[u"対象の fact"]
    w(u"**開発の 5 本**(訓練。予測の判定には使わない): 断った %d・対象の fact は数 %d・文 %d・型の外は %d(どれも理由 (e)。1 本に 1 つ)・比べ方 1 と 2 は 5 本とも同じ・混ぜ物は 5 本とも効いた・"
      u"表示の字の検査は %d/%d。" % (Dv[u"断った書類"], dtg[u"数"], dtg[u"文"], nsum(DN[u"型の外の fact"][u"合計"]), DN[u"表示の字の検査"][u"合った fact"], DN[u"表示の字の検査"][u"掛けた fact"]))
    w(u"")
    L.extend(sec3.rstrip(u"\n").split(u"\n"))
    w(u"")
    w(u"## §4 門")
    w(u"")
    w(u"- 封の門: 変異 %d 本のうち %d 本が赤・緑のまま %d 本(作りから同値と申告)。" % (len(SG.MUTANTS), len(SG.MUTANTS) - len(SG.SILENT_BY_DESIGN), len(SG.SILENT_BY_DESIGN)))
    w(u"- 型から作る命令は、型の folder だけを読む別の process で走る。実装の監査の席が、元の包みを読めない形であることを仕掛けで確かめた(記録の欄ではない)。")
    w(u"")
    w(u"## §5 読みと次の便の候補(封 §6 の決めのとおり)")
    w(u"")
    w(u"- 読めること: 答えから作った第 0 版の型と対応表を、それだけを読む命令に渡すと、断らなかった %d 本の全部で、道具が読む fact は意味として元に戻った。"
      u"型に入らなかった fact は対象の fact の %s%% で、理由は %d つに固まっていた。" % (nd, pct(nsum(out_), nsum(tgt)), sum(1 for r in LETTERS if rs[r][0] > 0)))
    w(u"- 読めないこと: 会社が型を埋められるか・対応表を作れるか・本文と置き場を型から作れるか・EDINET の本物の検査に通るか。")
    s6 = section(c.seal, u"## §6 ", u"## §7 ")
    if j[u"XM0-1"][0]:
        w(u"- XM0-1 は当たりなので、封 §6 の決めのとおり、次の便の候補を 4 つ示す(どれも別の封が先。選ぶのは人間):")
        for item in seal_candidates(s6):
            w(u"  - " + item + u"。")
    else:
        w(u"- XM0-1 は外れなので、封 §6 の決めのとおり、違った所の型を読むのが先で、(i)〜(iv) は示さない。")
    return u"\n".join(L) + u"\n"


def lines_problems(c):
    u"""文書の §3 以外の全部の行が、記録と字から組み直した行と同じ(1 字でも違えば赤)。"""
    want = render_doc(c).splitlines()
    got = c.doc.splitlines()
    out = []
    for i, (x, y) in enumerate(zip(want, got), 1):
        if x != y:
            out.append(u"文書の %d 行目が記録から組んだ行と違う: %s" % (i, y[:30]))
    if len(want) != len(got):
        out.append(u"文書の行数 %d が組み直した行数 %d と違う" % (len(got), len(want)))
    return out


def sec3_text(c):
    return section(c.doc, u"## §3 ", u"## §4 ")


def outside_sec3(c):
    return c.doc.replace(sec3_text(c), u"")


def derived_numbers(c):
    u"""記録から導ける数(文書の §3 以外の数はこの内か字で留めた境の数)。render_doc とは別に、記録の整数・書類ごとから作る。"""
    rec = c.rec
    out = set()
    for k in GROUPS:
        ints_in(rec[K_SUM][k], out)
    ints_in(rec[PRED_KEY], out)
    P = rec[K_SUM][G_PROD]
    PN = P[u"数"]
    st = stat_values(rec)
    for r, (s, nd_, mx) in st[u"reasons"].items():
        out |= set([str(s), str(nd_), str(mx)])
    out |= set(str(x) for x in st[u"top3"])
    out |= set([str(st[u"nd"]), str(st[u"one"]), str(st[u"big_target"]), str(st[u"neg0_docs"]), str(st[u"units_n"]), str(st[u"other_docs"]), str(st[u"other_max"]), str(st[u"cells"]),
                str(st[u"cells"] - nsum(PN[u"型の外の fact"][u"合計"]))])
    out |= set([str(nsum(PN[u"対象の fact"])), str(nsum(PN[u"型に入った fact"])), str(nsum(PN[u"型の外の fact"][u"合計"]))])
    out |= set([str(rec[K_SUM][G_ALL][K_DOCS] - rec[K_SUM][G_ALL][u"断った書類"]), str(rec[K_SUM][G_DEV][u"数"][u"対象の fact"][u"数"] - SEAL_DECLARED), str(SEAL_DECLARED)])
    out |= set([pct(nsum(PN[u"型の外の fact"][u"合計"]), nsum(PN[u"対象の fact"])), pct(PN[u"型の行"][u"数"], PN[u"型に入った fact"][u"数"])])
    out |= set(str(v) for v in (len(SG.MUTANTS), len(SG.MUTANTS) - len(SG.SILENT_BY_DESIGN), len(SG.SILENT_BY_DESIGN)))
    out |= set(DOC_COMMITS)
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
    want = set(render_doc(c).splitlines())
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
    P = rec[K_SUM][G_PROD]
    PN = P[u"数"]
    st = stat_values(rec)
    rs = st[u"reasons"]
    out = []
    nd = nondeclined_prod(rec)
    if not (PN[u"比べ方 2"][u"fact が意味として同じ"] == st[u"nd"] == PN[u"比べ方 1"][u"属性が意味として同じ"] and P[K_DOCS] - st[u"nd"] == P[u"断った書類"]):
        out.append(u"文書の「断らなかった 61 本は全部同じ」が記録と合わない")
    if not (PN[u"混ぜ物"][u"作れた"] == PN[u"混ぜ物"][u"効いた"] == st[u"nd"]):
        out.append(u"文書の「断らなかった 61 本の全部で作れた」が記録と合わない")
    if not (rs[u"a"][1] <= 3 and 2 * rs[u"a"][2] > rs[u"a"][0] and rs[u"a"][1] < st[u"nd"] // 2):
        out.append(u"文書の「書類の偏りに支えられている」((a) が少数の書類に在り 1 本が過半)が記録と合わない")
    if not (all(rs[u"e"][1] > rs[r][1] for r in LETTERS if r != u"e")):
        out.append(u"文書の「いちばん多くの書類に在る理由は (e)」が記録と合わない")
    if not st[u"one_e"] or st[u"one"] == 0:
        out.append(u"文書の「1 つだけの書類の 1 つはどれも理由 (e)」が記録と合わない")
    if not (st[u"top3"][0] * 2 > nsum(PN[u"型の外の fact"][u"合計"]) and st[u"top3"][0] > st[u"top3"][1]):
        out.append(u"文書の「620 のうち 519 は 1 本の書類」が記録と合わない(最大の書類が合計の過半でない)")
    if not st[u"units4"]:
        out.append(u"文書の「61 本のどれも 4 つ」が記録と合わない")
    if sum(1 for r in LETTERS if rs[r][0] > 0) != 4:
        out.append(u"文書の「理由は 4 つに固まっていた」が記録と合わない")
    if not (PN[u"文脈の定義"][u"作らなかった"] == 0 and PN[u"単位の定義"][u"作らなかった"] == 0):
        out.append(u"文書の「元に在って作らなかったものは 0」が記録と合わない")
    dst = P[u"断った段と理由ごと"]
    if not (sum(dst[u"型を作る"].values()) == P[u"断った書類"] and all(not dst[s] for s in (u"型から作る", u"組む", u"道具"))):
        out.append(u"文書の「型を作る命令で断った・ほかで断った書類は 0」が記録と合わない")
    dv = rec[K_SUM][G_DEV]
    DN = dv[u"数"]
    if not (st[u"dev_e"] == [1] * DEV_COUNT and st[u"dev_total"] == [1] * DEV_COUNT and DN[u"対象の fact"][u"数"] - DN[u"型に入った fact"][u"数"] == DEV_COUNT):
        out.append(u"文書の「差の 5 は書類ごとに 1 つ在る・どれも理由 (e)・1 本に 1 つ」が記録と合わない")
    if not (DN[u"比べ方 1"][u"属性が意味として同じ"] == DN[u"比べ方 2"][u"fact が意味として同じ"] == DN[u"混ぜ物"][u"効いた"] == DEV_COUNT and dv[u"断った書類"] == 0):
        out.append(u"文書の「開発の 5 本: 比べ方 1 と 2 は 5 本とも同じ・混ぜ物は 5 本とも効いた・断った 0」が記録と合わない")
    if SEAL_DECLARED != DN[u"型に入った fact"][u"数"]:
        out.append(u"封 §0 の申告の数(4982)が開発の 5 本の型に入った数の fact と違う")
    declined = [d for d in rec[K_DOCS] if d[u"断った"]]
    if not all(zero_like(d[u"対象の fact"]) for d in declined) or len(declined) != 1:
        out.append(u"文書の「断った 1 本は fact を 1 つも数えていない」が記録と合わない")
    if not (nsum(PN[u"型の外の fact"][u"合計"]) > 0 and st[u"nd"] > 0 and all(total_out(d) > 0 for d in nd)):
        out.append(u"文書の「全部の fact が入る書類は 1 本も無かった」が記録と合わない")
    return out


def sec3_problems(c):
    u"""§3 は記録に欄の無い読み(監査の席の読み)の節。数は記録に縛らず、見出し・「測った数ではない」・字で留めた数の並び・記録の数との整合・§3 の主張が外に出ないこと・「測っていない」を縛る。"""
    s = sec3_text(c)
    out = []
    if u"記録に欄の無い読み" not in s.splitlines()[0]:
        out.append(u"§3 の見出しが「記録に欄の無い読み」でない")
    if u"測った数ではない" not in s:
        out.append(u"§3 に「測った数ではない」が無い")
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
    # 記録にも在る数との整合(§3 の 24・64・61・3 は記録の理由ごとの数・書類の数)
    st = stat_values(c.rec)
    rs = st[u"reasons"]
    try:
        n24 = int(toks[SEC3_LINES[1][0]][0])
        n64, n61, n1, n3a, n3b = [int(x) for x in toks[SEC3_LINES[2][0]]]
        if n24 != rs[u"d"][0] or n64 != rs[u"e"][0] or n61 != rs[u"e"][1] or n64 - n61 != n3a or n3b != rs[u"f"][0] or n1 != 1:
            out.append(u"§3 の数(24・64・61・3)が記録の理由ごとの数と合わない")
    except (KeyError, ValueError, IndexError):
        out.append(u"§3 の数が読めない")
    rest = outside_sec3(c)
    for p in SEC3_ONLY_PHRASES:
        if p in rest:
            out.append(u"記録に欄の無い §3 の主張「%s」が §3 の外に出ている" % p)
    return out


def affirm_problems(c):
    u"""「作れる」「専用の道具が要らない」「人が書ける」「誤りが無くなる」「会社が型を埋めれば」「検査に通る」は、言えないことの引用(「…」の中)・否定の中にしか無い。引用の在る行には「言えない」か「読まない」が在る。"""
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
    n7 = len([ln for ln in sec7.splitlines() if ln.startswith(u"- ")])
    if n7 != 6 or sorted(set(t for t, _ in LIMIT_FRAGS if t.startswith(u"7-"))) != [u"7-%d" % i for i in range(1, n7 + 1)]:
        out.append(u"封 §7 の限界の行の数が門の限界の断片の組と合わない")
    hlines = head.splitlines()
    for i, (no, frags) in enumerate(LIMIT_FRAGS, 1):
        for p in frags:
            if p not in head:
                out.append(u"限界の断片 %d(封 §7 の %d 本目)が文書の頭に無い: %s" % (i, no, p[:20]))
        if not any(all(p in ln for p in frags) for ln in hlines):
            out.append(u"限界の断片 %d(封 §7 の %d 本目)が文書の頭の 1 つの行に揃っていない" % (i, no))
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
    (u"sec3", sec3_problems), (u"affirm", affirm_problems), (u"phrases", phrase_problems), (u"head", head_problems), (u"forbidden", forbidden_problems), (u"commits", doc_commit_problems)])


# ======================================================================================================
def blob_problems(root, prefix, at):
    return WG.blob_problems(root, prefix, at)


def commit_problems(root=REPO):
    u"""文書が書く 3 つの commit が実の履歴と合う: 封は 34afe495・script と封の門は 6f719410・記録は 3cd49ad4。commit の message が文書の言う「REVISE」「独立監査 GO」「66 本」を書いている。"""
    out = []
    for rel, want in HISTORY.items():
        r = subprocess.run(["git", "-C", root, "log", "--format=%H", "--reverse", "--", PREFIX + rel], stdout=subprocess.PIPE, universal_newlines=True)
        got = [x for x in r.stdout.split() if x]
        if len(got) != len(want) or any(not g.startswith(w) for g, w in zip(got, want)):
            out.append(u"%s の履歴が文書の書く commit %s と違う" % (rel, u"・".join(want)))
    for short, words in ((SCRIPT_COMMIT_SHORT, (u"独立監査 REVISE(門の穴 3 つ)→ 直し → GO", u"同値 3 本", u"変異 226 本のうち 223 本が赤")),
                         (RECORD_COMMIT_SHORT, (u"独立監査 GO", u"断った 1 本を除く 66 本を別の実装で数え直して一致"))):
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
(変異を実行する前に書いた予測。右 = 赤になるべき検査。「整合」= 書類ごとの数から集計・予測を作り直し、recount は緑のまま当たり外れ・向きだけが変わる)
固定の変異 F1〜: 記録・封・文書の 1 か所を替える。右の検査が赤。
F1  記録の sha256 の写しを違う値に                                                       -> sha
F2  記録の「この script の sha256」を 1 字替える                                         -> sha
F3  記録の限界の欄の 1 行を消す                                                          -> sha
F4  記録の封の commit の欄を 1 字替える                                                  -> sha
F5  記録の step の欄を 1 字替える                                                        -> sha
F6  封の写しの sha256 の写しを違う値に                                                   -> sha
F7  記録の材料の書類の本数 67 → 66                                                      -> recount
F8  記録の材料の道具 P の ModelValue.py の sha を 1 字替える                              -> recount
F9  書類 20 の型に入った数の fact を 1 増やす(集計は直さない)                              -> recount
F10 集計の本番だけの 62 本の「比べ方 2・fact が意味として同じ」を 1 増やす(書類ごとは直さない) -> recount
F11 書類 6 の理由 (a) の数を 1 増やす(合計は直さない = 最大 ≤ 合計 ≤ 和 が崩れる)            -> recount
F12 書類 18(断った)の断った段を空にする                                                  -> recount
F13 書類 7 の「比べ方 1・属性が意味として同じ」を False にする(集計は直さない)             -> recount
F14 予測の欄 XM0-3 の fact を 1 増やす                                                    -> recount
F15 書類の番号 5 を 99 にする                                                             -> recount
F16 集計の全部の「混ぜ物・効いた」を 1 増やす                                              -> recount
F17 集計の開発の 5 本と本番だけの 62 本を入れ替える                                         -> recount
F18 書類 6 の秒を 0.1 増やす(集計は直さない)                                              -> recount
F19 記録に docid の欄を足す                                                               -> clean
F20 記録に EDINET コードの形の字を足す                                                     -> clean
F21 記録に日付の形の字を足す                                                               -> clean
F22 封の写しから XM0-3 の境の字を消す                                                      -> bound
F23 封の写しから §6 の「(iv)」の候補の字を消す                                             -> bound
F24 封の写しから §7 の限界の 1 本を消す                                                    -> bound
F25 封の写しから §0 の「数の fact 4982」を消す                                              -> bound
整合の変異 C1〜: recount は緑のまま、文書が合わなくなる(verdict・lines)。
C1  XM0-1 を外れにする(本番の 10 書類の比べ方 2 の fact が意味として同じ を False に)            -> verdict
C2  XM0-2 を当たりにする(型の外を全部型に入れる = 型の外が 0 の書類が 45 以上)                  -> verdict
C3  XM0-3 を当たりにする(同上)                                                            -> verdict
C4  XM0-4 を外れにする((e) の fact を (a) より多くする)                                   -> verdict
C5  XM0-5 を外れにする(文脈の名も同じ を 15 書類で False に)                                -> verdict
C6  XM0-6 を外れにする(作らなかった文脈の定義が 1 の書類を 11 に)                            -> verdict
C7  XM0-7 を外れにする(鳴り方が同じ を 20 書類で False に)                                  -> verdict
C8  XM0-8 を外れにする(効いた を 1 書類で False に)                                         -> verdict
C9  XM0-9 を下の外にする(型の行の数を型に入った数の 90% にする)                              -> verdict
C10 XM0-9 を上の外にする(型の行の数を型に入った数の全部にする)                               -> verdict
C11 XM0-10 を外れにする(表示の字の合った fact を 9 割にする)                                -> verdict
C12 旗: 型の外の fact が 0(型の外を全部型に入れる)                                          -> verdict
C13 旗: 型に入った fact が対象の 90% 未満(型の外を増やす)                                    -> verdict
C14 旗: 属性が意味として同じなのに道具の fact が違う書類                                      -> verdict
C15 旗: 混ぜ物を作れなかった書類が 6 本以上                                                -> verdict
C16 旗: 断った書類が 6 本以上                                                              -> verdict
C17 旗: 値が -0 の行が 0                                                                  -> verdict
C18 XM0-1 だけを外れにして、文書の「示す」(§5 の候補 (i)〜(iv))と合わなくする                  -> verdict(封 §6 の決め)
C19 整合: (a) を多数の書類に散らす(偏りでなくす)                                             -> sanity
C20 整合: (d) の書類の数を (e) より多くする                                                  -> sanity
C21 整合: 単位の定義の数を 1 書類だけ 4 でなくする                                            -> sanity
C22 整合: 理由 (b) に fact を足す(理由が 5 つになる)                                         -> sanity
文書の固定の変異 D1〜: 右の検査が赤。
D1  判定の「外れ」「当たり」を行ごとに入れ替える(10 行の全部。掃き)                              -> verdict
D2  頭の「予測の 2 本(XM0-2・XM0-3)は外れ」を「(XM0-1・XM0-2)」に                          -> verdict・lines
D3  頭の「当たり 8・外れ 2」を「当たり 7・外れ 3」に                                          -> verdict・lines
D4  「型も対応表も答えから作った」を「型は答えから作っていない」に                              -> lines
D5  「1 本も無かった」を「1 本は在った」に                                                  -> lines
D6  「書類の偏りに支えられている」を「書類の偏りに支えられていない」に                          -> lines
D7  「620 のうち 519 は 1 本の書類」を「620 のうち 519 は 3 本の書類」に                      -> lines
D8  「封 §0 の申告の数は足りていなかった」を「封 §0 の申告の数は足りていた」に                 -> lines
D9  §5 に「(v)」の候補を足す                                                               -> verdict
D10 §5 の (i) の「0 USD。別の封が先」を消す                                                 -> verdict
D11 §5 の (iv) の「有料。別の封と、払う前の知らせが先」を消す                                  -> verdict
D12 §5 の最後の行の後ろに候補の見出しのない案の 1 行を足す                                    -> verdict
D13 §5 の「次の便の候補を 4 つ示す」を「次の便の候補を 3 つ示す」に                            -> verdict
D14 §5 の (ii) と (iii) の行を入れ替える                                                    -> verdict
D15 頭の限界の 1 本を消す(全部の組。掃き)                                                     -> head
D16 頭の限界の断片を 1 つ消す(全部の断片。掃き)                                               -> head
D17 引用の外に「XBRL を作れる。」「会社が型を埋めれば XBRL が作れる。」「どんな資料も作れる。」「誤りが無くなる。」「専用の道具が要らない。」「EDINET の検査に通る。」を足す(掃き)    -> affirm
D18 引用の行から「言えない」「読まない」を全部消す                                             -> affirm
D19 文書に「保証」を足す・docID の形を足す・commit の字を替える・知らない commit の字を足す      -> forbidden・commits
D20 §3 の見出しの「記録に欄の無い読み」を消す・「測った数ではない」を消す・§3 の数を替える・§3 の主張を §2 に写す(全部の §3 の主張。掃き)    -> sec3
D21 §3 の中の語を替える(「測っていない」を消す・「決算期の変更」を消す)                         -> sec3
掃き(SWEEPS。文書の全部に 1 か所ずつ当てる。1 つでも黙れば報告):
W1  文書の全部の数(§3 を含む)を、(a) 1 増やす (b) 同じ文書の別の所の数に替える (c) §3 の数に替える          -> 全部赤(lines か sec3)
W2  向きの語(以上/以下/未満・多い/少ない・全部/一部・当たり/外れ・在る/無い など)を、出た所ごとに反対に -> 全部赤
W3  「62 本」「61 本」「67 本」「5 本」の数を互いに取り違える・80253/79633/62747/62134 を互いに取り違える  -> 全部赤
W4  §3 の数を §2 に 1 行として足す(全部)                                                    -> 全部赤(numbers・sec3)
W5  表の 1 セルを、同じ表の別の行の同じ列のセルへ替える(§1 の表・§2 の表の全部のセル)           -> 全部赤
W6  §3 の外の全部の行を 1 行ずつ消す・全部の文を 1 つずつ消す・「・」でつないだ節を 1 つずつ消す        -> 全部赤
W7  記録の全部の整数・小数・旗の葉(集計 3 つ・予測・書類の代表 7 つ分)を 1 増やす・旗を反転する          -> 全部赤(recount)
W8  §3 の文を 1 つずつ消す・向きの語を反対に                                                   -> 黙る所が在りうる(§3 の中の括弧の例示と、SEC3_PHRASES に無い言い回し)。黙った所は報告
予測の自己点検: 黙るとすれば W8(§3 は形で縛るため)と、W5 で「同じ文字列のセル」に替わる場合(スキップ)。W1〜W7 に黙りは無いと予測する。
(実行後の追記。予測は書き換えていない。外れた所を日付つきで残す。2026-11-22)
- 1 回目の実行の結果: 固定の変異で黙ったのは F21(日付の形)だけ。理由は門の側の欠陥: 記録の検査に script の ``check_clean`` を呼んでいたが、それは日付を見ない(封 §3 は「日付を持たない」と決めた)。門に日付の形の検査を足した(記録の「封」欄が書く封の path の日付は除く)。予測(clean で赤)は直した後で当たった。
- 同じ実行で、整合の変異の作りの誤りが 3 つ出た(変異の側の欠陥で、門の欠陥ではない): (1) 型の外へ移す道具が、表示の字の検査の掛けた数・型の行の数を型に入った数に合わせていなかった(recount が赤になり「整合」にならなかった)。(2) 型に入った数の fact が 0 になる変異で % の計算が 0 で割った。% を ―(分母 0)にした。(3) 固定の変異の表に、検査名 head・phrases を指す変異が無く、g_4 が赤になった。D15・D16・D22 を足した。
- W8(§3 の中)は 1 回目に 7 件黙った: §3 の中の向きの語(「測定の記録ではない」「純数でもない」「同じ fact かどうか」「在るのは」「在る文脈と無い文脈」「多いのか」)。§3 の「言える範囲」を決める言い回しなので ``SEC3_PHRASES`` に留めた。留めた後、W8 は全部赤(``SEC3_SILENT`` は空)。
- W1〜W7 に黙りは 0(W1 の 717 件・W2 185・W3 108・W4 10・W5 774・W6 286・W6L 31・W7 601 の全部が赤。数は ``MIN_CASES`` の下限で留める)。
"""

ORDER_DOC = (u"lines", u"verdict", u"numbers", u"resid", u"sec3", u"affirm", u"phrases", u"head", u"forbidden", u"commits", u"sanity", u"bound", u"clean", u"sha", u"recount")
ORDER_REC = (u"sha", u"recount", u"verdict", u"lines", u"sanity", u"clean", u"bound", u"numbers", u"resid", u"sec3", u"affirm", u"phrases", u"head", u"forbidden", u"commits")


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
def rebuild(rec):
    dev, prod = split_docs(rec)
    rec[K_SUM][G_DEV] = agg_of(dev)
    rec[K_SUM][G_PROD] = agg_of(prod)
    rec[K_SUM][G_ALL] = agg_of(rec[K_DOCS])
    rec[PRED_KEY] = pred_expected(rec)


def each_prod(c, fn):
    for d in c.rec[K_DOCS]:
        if d[u"番号"] > DEV_COUNT:
            fn(d)
    rebuild(c.rec)


def first_prod(c, n, pred, fn):
    u"""本番の断らなかった書類のうち pred を満たす最初の n 本に fn を当てる。"""
    k = 0
    for d in c.rec[K_DOCS]:
        if d[u"番号"] > DEV_COUNT and not d[u"断った"] and pred(d) and k < n:
            fn(d)
            k += 1
    assert k == n, (k, n)
    rebuild(c.rec)


def clear_outside(d):
    u"""型の外の fact を全部型に入れる(理由も 0。型の行は型に入った数の 96% 相当を保つ)。"""
    for k in (u"数", u"文"):
        d[u"型に入った fact"][k] += d[u"型の外の fact"][u"合計"][k]
        d[u"型の外の fact"][u"合計"][k] = 0
        for r in LETTERS:
            d[u"型の外の fact"][u"理由ごと"][r][k] = 0


def add_outside(d, r, k, n):
    u"""型に入った fact から n を型の外(理由 r)へ移す(上限あり)。"""
    n = min(n, d[u"型に入った fact"][k])
    d[u"型に入った fact"][k] -= n
    d[u"型の外の fact"][u"合計"][k] += n
    d[u"型の外の fact"][u"理由ごと"][r][k] += n
    d[u"型の行"][k] = min(d[u"型の行"][k], d[u"型に入った fact"][k])
    if k == u"数":
        ck = d[u"表示の字の検査"]
        ck[u"掛けた fact"] = min(ck[u"掛けた fact"], d[u"型に入った fact"][u"数"])
        ck[u"合った fact"] = min(ck[u"合った fact"], ck[u"掛けた fact"])
        d[u"型の行"][u"値が -0 の行"] = min(d[u"型の行"][u"値が -0 の行"], d[u"型の行"][u"数"])


def set_false(path):
    def fn(d):
        o = d
        for p in path[:-1]:
            o = o[p]
        o[path[-1]] = False
    return fn


def m_xm01_miss(c):
    first_prod(c, 10, lambda d: d[u"比べ方 2"][u"fact が意味として同じ"], lambda d: (set_false((u"比べ方 2", u"fact が意味として同じ"))(d), set_false((u"比べ方 2", u"字も含めて行が同じ"))(d)))


def m_clear_all(c):
    each_prod(c, lambda d: None if d[u"断った"] else clear_outside(d))


def m_e_over_a(c):
    def fn(d):
        if not d[u"断った"]:
            add_outside(d, u"e", u"数", 100000)
    each_prod(c, fn)


def m_ctx_miss(c):
    first_prod(c, 15, lambda d: d[u"比べ方 1"][u"文脈の名も同じ"], set_false((u"比べ方 1", u"文脈の名も同じ")))


def m_no_made_over(c):
    def fn(d):
        d[u"文脈の定義"][u"作らなかった"] = 1
    first_prod(c, 11, lambda d: True, fn)


def m_ring_miss(c):
    first_prod(c, 20, lambda d: d[u"比べ方 2"][u"鳴り方が同じ"], set_false((u"比べ方 2", u"鳴り方が同じ")))


def m_mix_miss(c):
    first_prod(c, 1, lambda d: d[u"混ぜ物"][u"効いた"], set_false((u"混ぜ物", u"効いた")))


def m_rows_low(c):
    def fn(d):
        if not d[u"断った"]:
            d[u"型の行"][u"数"] = d[u"型に入った fact"][u"数"] * 9 // 10
            d[u"型の行"][u"値が -0 の行"] = min(d[u"型の行"][u"値が -0 の行"], d[u"型の行"][u"数"])
    each_prod(c, fn)


def m_rows_high(c):
    def fn(d):
        if not d[u"断った"]:
            d[u"型の行"][u"数"] = d[u"型に入った fact"][u"数"]
    each_prod(c, fn)


def m_disp_low(c):
    def fn(d):
        if not d[u"断った"]:
            d[u"表示の字の検査"][u"合った fact"] = d[u"表示の字の検査"][u"掛けた fact"] * 9 // 10
    each_prod(c, fn)


def m_in_under90(c):
    def fn(d):
        if not d[u"断った"]:
            add_outside(d, u"a", u"数", d[u"対象の fact"][u"数"] // 5)
    each_prod(c, fn)


def m_flag_diff(c):
    def fn(d):
        d[u"比べ方 2"][u"fact が意味として同じ"] = False
        d[u"比べ方 2"][u"字も含めて行が同じ"] = False
    first_prod(c, 1, lambda d: d[u"比べ方 1"][u"属性が意味として同じ"], fn)


def m_flag_not_made(c):
    def fn(d):
        d[u"混ぜ物"][u"作れた"] = False
        d[u"混ぜ物"][u"効いた"] = False
    first_prod(c, 6, lambda d: d[u"混ぜ物"][u"作れた"], fn)


def m_declined_many(c):
    first_prod(c, 5, lambda d: True, decline_doc_keep)


def decline_doc_keep(d):
    for k in list(d):
        if k in (u"番号", u"断った", u"断った段", u"断った理由"):
            continue
        d[k] = zero_tree(d[k])
    d[u"秒"] = collections.OrderedDict([(u"型から作る命令", None)])
    d[u"断った"] = True
    d[u"断った段"] = u"型を作る"
    d[u"断った理由"] = u"書類の決めが 1 通りに決まらない"


def zero_tree(o):
    if isinstance(o, dict):
        return collections.OrderedDict((k, collections.OrderedDict() if k in (u"属性ごと", u"属性ごとの違った fact") else zero_tree(v)) for k, v in o.items())
    if isinstance(o, bool):
        return False
    if isinstance(o, (int, float)):
        return 0
    return o


def m_neg0_zero(c):
    def fn(d):
        d[u"型の行"][u"値が -0 の行"] = 0
    each_prod(c, fn)


def m_a_spread(c):
    u"""理由 (a) の fact を、最大の書類から 10 の書類へ散らす(偏りでなくす)。"""
    big = max(nondeclined_prod(c.rec), key=lambda d: nsum(d[u"型の外の fact"][u"理由ごと"][u"a"]))
    n = nsum(big[u"型の外の fact"][u"理由ごと"][u"a"])
    per = n // 10
    for k in (u"数", u"文"):
        x = big[u"型の外の fact"][u"理由ごと"][u"a"][k]
        big[u"型の外の fact"][u"理由ごと"][u"a"][k] = 0
        big[u"型の外の fact"][u"合計"][k] -= x
        big[u"型に入った fact"][k] += x
    others = [d for d in nondeclined_prod(c.rec) if d is not big and nsum(d[u"型の外の fact"][u"理由ごと"][u"a"]) == 0][:10]
    for d in others:
        add_outside(d, u"a", u"数", per)
    rebuild(c.rec)


def m_d_docs_over_e(c):
    u"""理由 (d) を、(e) の書類の数より多くの書類に付ける(全部の書類に 1 つずつ)。"""
    def fn(d):
        if not d[u"断った"]:
            add_outside(d, u"d", u"数", 1)
    each_prod(c, fn)
    for d in c.rec[K_DOCS]:
        pass


def m_unit_not4(c):
    first_prod(c, 1, lambda d: True, lambda d: d[u"単位の定義"].__setitem__(u"作った", 3))


def m_add_b(c):
    first_prod(c, 1, lambda d: True, lambda d: add_outside(d, u"b", u"数", 1))


def m_swap_dev_prod(c):
    c.rec[K_SUM][G_DEV], c.rec[K_SUM][G_PROD] = c.rec[K_SUM][G_PROD], c.rec[K_SUM][G_DEV]


def m_renumber(c):
    doc_at(c.rec, 5)[u"番号"] = 99


def m_mix_all(c):
    c.rec[K_SUM][G_ALL][u"数"][u"混ぜ物"][u"効いた"] += 1


def add_before_last(c, text):
    ls = c.doc.rstrip(u"\n").split(u"\n")
    ls.insert(len(ls) - 1, text)
    c.doc = u"\n".join(ls) + u"\n"


def swap_lines(c, a, b):
    ls = c.doc.split(u"\n")
    ia = [i for i, ln in enumerate(ls) if a in ln][0]
    ib = [i for i, ln in enumerate(ls) if b in ln][0]
    ls[ia], ls[ib] = ls[ib], ls[ia]
    c.doc = u"\n".join(ls)


def set_rec(c, path, val):
    o = c.rec
    for p in path[:-1]:
        o = o[p]
    o[path[-1]] = val


def inc(c, path, delta=1):
    o = c.rec
    for p in path[:-1]:
        o = o[p]
    o[path[-1]] += delta


MUTATIONS = (
    (u"F1 記録の sha256 の写しを違う値に", lambda c: c.shas.__setitem__(RECORD_REL, u"0" * 64), (u"sha",)),
    (u"F2 記録の script の sha256 を 1 字替える", lambda c: c.rec.__setitem__(u"この script の sha256", u"f" + c.rec[u"この script の sha256"][1:]), (u"sha",)),
    (u"F3 記録の限界の欄の 1 行を消す", lambda c: c.rec.__setitem__(u"限界", c.rec[u"限界"][1:]), (u"sha",)),
    (u"F4 記録の封の commit の欄を 1 字替える", lambda c: c.rec.__setitem__(u"封の commit", u"0" + c.rec[u"封の commit"][1:]), (u"sha",)),
    (u"F5 記録の step の欄を 1 字替える", lambda c: c.rec.__setitem__(u"step", c.rec[u"step"].replace(u"XM0", u"XM1", 1)), (u"sha",)),
    (u"F6 封の写しの sha256 の写しを違う値に", lambda c: c.shas.__setitem__(SEAL_REL, u"0" * 64), (u"sha",)),
    (u"F7 記録の材料の書類の本数を 66 に", lambda c: c.rec[u"材料"].__setitem__(u"書類の本数", 66), (u"recount",)),
    (u"F8 記録の材料の道具 P の ModelValue.py の sha を 1 字替える", lambda c: c.rec[u"材料"].__setitem__(u"道具 P の ModelValue.py の sha256", u"0" + c.rec[u"材料"][u"道具 P の ModelValue.py の sha256"][1:]), (u"recount",)),
    (u"F9 書類 20 の型に入った数の fact を 1 増やす", lambda c: doc_at(c.rec, 20)[u"型に入った fact"].__setitem__(u"数", doc_at(c.rec, 20)[u"型に入った fact"][u"数"] + 1), (u"recount",)),
    (u"F10 集計の本番だけの 62 本の比べ方 2 の fact が意味として同じを 1 増やす", lambda c: inc(c, (K_SUM, G_PROD, u"数", u"比べ方 2", u"fact が意味として同じ")), (u"recount",)),
    (u"F11 書類 6 の理由 (a) の数を 1 増やす(合計は直さない)", lambda c: doc_at(c.rec, 6)[u"型の外の fact"][u"理由ごと"][u"a"].__setitem__(u"数", doc_at(c.rec, 6)[u"型の外の fact"][u"理由ごと"][u"a"][u"数"] + 1), (u"recount",)),
    (u"F12 書類 18(断った)の断った段を空にする", lambda c: doc_at(c.rec, 18).__setitem__(u"断った段", u""), (u"recount",)),
    (u"F13 書類 7 の比べ方 1 の属性が意味として同じを False にする", lambda c: doc_at(c.rec, 7)[u"比べ方 1"].__setitem__(u"属性が意味として同じ", False), (u"recount",)),
    (u"F14 予測の欄 XM0-3 の fact を 1 増やす", lambda c: inc(c, (PRED_KEY, PK[2], u"fact")), (u"recount",)),
    (u"F15 書類の番号 5 を 99 にする", m_renumber, (u"recount",)),
    (u"F16 集計の全部の混ぜ物の効いたを 1 増やす", m_mix_all, (u"recount",)),
    (u"F17 集計の開発の 5 本と本番だけの 62 本を入れ替える", m_swap_dev_prod, (u"recount",)),
    (u"F18 書類 6 の秒を 0.1 増やす", lambda c: doc_at(c.rec, 6)[u"秒"].__setitem__(u"型から作る命令", doc_at(c.rec, 6)[u"秒"][u"型から作る命令"] + 0.1), (u"recount",)),
    (u"F19 記録に docid の欄を足す", lambda c: c.rec.__setitem__(u"docID", u"S100ABCD"), (u"clean",)),
    (u"F20 記録に EDINET コードの形の字を足す", lambda c: c.rec.__setitem__(u"メモ", u"E01234"), (u"clean",)),
    (u"F21 記録に日付の形の字を足す", lambda c: c.rec.__setitem__(u"メモ", u"2025-03-31"), (u"clean",)),
    (u"F22 封の写しから XM0-3 の境の字を消す", lambda c: drop_seal(c, u"0.5% 以下"), (u"bound",)),
    (u"F23 封の写しから §6 の (iv) の候補の字を消す", lambda c: drop_seal(c, u"(iv) 答えを見ない席が、XBRL でない資料から型を埋める"), (u"bound",)),
    (u"F24 封の写しから §7 の限界の 1 本を消す", lambda c: rep(c, u"\n- 文の fact は、型が持つのは科目・期間・対象・次元だけで", u"\n文の fact は、型が持つのは科目・期間・対象・次元だけで", attr="seal"), (u"bound",)),
    (u"F25 封の写しから §0 の「数の fact 4982」を消す", lambda c: drop_seal(c, u"数の fact 4982"), (u"bound",)),
    (u"C1 XM0-1 を外れにする", m_xm01_miss, (u"verdict",)),
    (u"C2 XM0-2 を当たりにする", m_clear_all, (u"verdict",)),
    (u"C3 XM0-3 を当たりにする", m_clear_all, (u"verdict",)),
    (u"C4 XM0-4 を外れにする", m_e_over_a, (u"verdict",)),
    (u"C5 XM0-5 を外れにする", m_ctx_miss, (u"verdict",)),
    (u"C6 XM0-6 を外れにする", m_no_made_over, (u"verdict",)),
    (u"C7 XM0-7 を外れにする", m_ring_miss, (u"verdict",)),
    (u"C8 XM0-8 を外れにする", m_mix_miss, (u"verdict",)),
    (u"C9 XM0-9 を下の外にする", m_rows_low, (u"verdict",)),
    (u"C10 XM0-9 を上の外にする", m_rows_high, (u"verdict",)),
    (u"C11 XM0-10 を外れにする", m_disp_low, (u"verdict",)),
    (u"C12 旗: 型の外の fact が 0", m_clear_all, (u"verdict",)),
    (u"C13 旗: 型に入った fact が対象の 90% 未満", m_in_under90, (u"verdict",)),
    (u"C14 旗: 属性が意味として同じなのに道具の fact が違う書類", m_flag_diff, (u"verdict",)),
    (u"C15 旗: 混ぜ物を作れなかった書類が 6 本以上", m_flag_not_made, (u"verdict",)),
    (u"C16 旗: 断った書類が 6 本以上", m_declined_many, (u"verdict",)),
    (u"C17 旗: 値が -0 の行が 0", m_neg0_zero, (u"verdict",)),
    (u"C18 XM0-1 だけを外れにして文書の「示す」と合わなくする", m_xm01_miss, (u"verdict",)),
    (u"C19 整合: (a) を多数の書類に散らす", m_a_spread, (u"sanity",)),
    (u"C20 整合: (d) の書類の数を (e) より多くする", m_d_docs_over_e, (u"sanity",)),
    (u"C21 整合: 単位の定義の数を 1 書類だけ 4 でなくする", m_unit_not4, (u"sanity",)),
    (u"C22 整合: 理由 (b) に fact を足す", m_add_b, (u"sanity",)),
    (u"D2 頭の「予測の 2 本(XM0-2・XM0-3)は外れ」を「(XM0-1・XM0-2)」に", lambda c: rep(c, u"**予測の 2 本(XM0-2・XM0-3)は外れ。**", u"**予測の 2 本(XM0-1・XM0-2)は外れ。**"), (u"verdict", u"lines")),
    (u"D3 頭の「当たり 8・外れ 2」を「当たり 7・外れ 3」に", lambda c: rep(c, u"判定した 10 本は 当たり 8・外れ 2", u"判定した 10 本は 当たり 7・外れ 3"), (u"verdict", u"lines")),
    (u"D4 「型も対応表も答えから作った」を「型は答えから作っていない」に", lambda c: rep(c, u"**型も対応表も答えから作った。**", u"**型は答えから作っていない。**"), (u"lines",)),
    (u"D5 「1 本も無かった」を「1 本は在った」に", lambda c: rep(c, u"1 本も無かった", u"1 本は在った"), (u"lines",)),
    (u"D6 「書類の偏りに支えられている」を「…いない」に", lambda c: rep(c, u"書類の偏りに支えられている", u"書類の偏りに支えられていない"), (u"lines",)),
    (u"D7 「620 のうち 519 は 1 本の書類」を「…3 本の書類」に", lambda c: rep(c, u"**620 のうち 519 は 1 本の書類。**", u"**620 のうち 519 は 3 本の書類。**"), (u"lines",)),
    (u"D8 「封 §0 の申告の数は足りていなかった」を「足りていた」に", lambda c: rep(c, u"申告の数は足りていなかった", u"申告の数は足りていた"), (u"lines",)),
    (u"D9 §5 に「(v)」の候補を足す", lambda c: add_doc(c, u"  - (v) 前の年の対応表を使わない案。"), (u"verdict",)),
    (u"D10 §5 の (i) の「0 USD。別の封が先」を消す", lambda c: rep(c, u"第 1 版(0 USD。別の封が先)", u"第 1 版"), (u"verdict",)),
    (u"D11 §5 の (iv) の「有料。別の封と、払う前の知らせが先」を消す", lambda c: rep(c, u"(有料。別の封と、払う前の知らせが先)", u""), (u"verdict",)),
    (u"D12 §5 の最後の行の後ろに見出しのない案の 1 行を足す", lambda c: add_doc(c, u"- 次は型の欄を増やす手もある。"), (u"verdict",)),
    (u"D13 §5 の「次の便の候補を 4 つ示す」を「3 つ示す」に", lambda c: rep(c, u"次の便の候補を 4 つ示す", u"次の便の候補を 3 つ示す"), (u"verdict",)),
    (u"D14 §5 の (ii) と (iii) の行を入れ替える", lambda c: swap_lines(c, u"(ii) 型から本文", u"(iii) 前の年の対応表"), (u"verdict",)),
    (u"D15 頭の「費用は 0 USD」を消す", lambda c: rep(c, u"費用は 0 USD", u"費用は 0"), (u"head", u"lines")),
    (u"D16 頭の限界(混ぜ物は 1 本につき 1 つ)の字を消す", lambda c: rep(c, u"混ぜ物は 1 本につき 1 つ・対象の欄だけ。ほかの欄", u"X。ほかの欄"), (u"head", u"lines")),
    (u"D22 「読めないこと」を消す", lambda c: rep(c, u"- 読めないこと:", u"- X:"), (u"phrases", u"lines")),
    (u"D17a 文書に「保証」を足す", lambda c: add_doc(c, u"保証する。"), (u"forbidden",)),
    (u"D17b 文書に docID の形を足す", lambda c: add_doc(c, u"S100ABCD"), (u"forbidden",)),
    (u"D17c 文書の commit の字 3cd49ad4 を 1 字替える", lambda c: rep(c, u"3cd49ad4", u"3cd49ad5", count=100), (u"commits",)),
    (u"D17d 文書の commit の字 6f719410 を 1 字替える", lambda c: rep(c, u"6f719410", u"6f719411", count=100), (u"commits",)),
    (u"D17e 文書に知らない commit の字を足す", lambda c: add_doc(c, u"commit 1a2b3c4d。"), (u"commits",)),
    (u"D18 引用の行から「言えない」「読まない」を全部消す", lambda c: setattr(c, "doc", u"\n".join((ln.replace(u"言えないこと", u"X").replace(u"言えない", u"X").replace(u"読まない", u"X") if QUOTED.search(ln) else ln) for ln in c.doc.splitlines())), (u"affirm",)),
    (u"D20a §3 の見出しの「記録に欄の無い読み」を消す", lambda c: rep(c, u"## §3 記録に欄の無い読み(", u"## §3 X("), (u"sec3",)),
    (u"D20b §3 の「測った数ではない」を消す", lambda c: rep(c, u"測った数ではない", u"X"), (u"sec3",)),
    (u"D20c §3 の外に「温室効果ガス」を足す", lambda c: add_doc(c, u"温室効果ガスの量の単位だった。"), (u"sec3",)),
    (u"D21a §3 の「測っていない」を消す", lambda c: rep(c, u"四半期の数か)は測っていない。", u"四半期の数か)は X。"), (u"sec3",)),
    (u"D21b §3 の「決算期の変更」を消す", lambda c: rep(c, u"決算期の変更か、", u"X、"), (u"sec3",)),
    (u"D21c §3 の「24」を「25」に", lambda c: rep(c, u"理由 (d) の 24 は", u"理由 (d) の 25 は"), (u"sec3",)),
    (u"D21d 文書に「48%」の言い切りを足す", lambda c: add_doc(c, u"決まった fact は 48% だった。"), (u"numbers", u"resid")),
)
# 記録を替えて作り直す(整合)変異の名(recount が緑のまま当たり外れ・向きだけが変わることを別の試験で見る)
CONSISTENT = (m_xm01_miss, m_clear_all, m_e_over_a, m_ctx_miss, m_no_made_over, m_ring_miss, m_mix_miss, m_rows_low, m_rows_high, m_disp_low, m_in_under90, m_flag_diff, m_flag_not_made,
              m_declined_many, m_neg0_zero, m_a_spread, m_d_docs_over_e, m_unit_not4, m_add_b)


def run_mutations(base=None):
    base = base or Ctx()
    out = []
    for name, fn, checks in MUTATIONS:
        doc_only = name.startswith(u"D")
        c = base.with_doc(base.doc) if doc_only else base.copy()
        fn(c)
        res = [(k, bool(guard(CHECKS[k], c))) for k in checks]
        out.append((name, res))
    return out


# ======================================================================================================
# 掃き: 文書・記録の全部の所に 1 か所ずつ当てる
NUM_RE = WG.NUM_RE
FLIPS = ((u"以上", u"以下"), (u"以下", u"以上"), (u"未満", u"以上"), (u"多い", u"少ない"), (u"少ない", u"多い"), (u"多く", u"少なく"), (u"少なく", u"多く"), (u"増", u"減"), (u"減", u"増"), (u"高", u"低"), (u"低", u"高"),
         (u"超える", u"満たない"), (u"満たない", u"超える"), (u"大きい", u"小さい"), (u"小さい", u"大きい"), (u"大半", u"少数"), (u"全部", u"一部"), (u"一部", u"全部"), (u"両方", u"片方"),
         (u"前の年", u"今年"), (u"今年", u"前の年"), (u"当たり", u"外れ"), (u"外れ", u"当たり"), (u"立たない", u"立つ"), (u"同じ", u"違う"), (u"違った", u"同じ"),
         (u"在る", u"無い"), (u"無い", u"在る"), (u"断った", u"通した"), (u"作った", u"作らなかった"), (u"作れた", u"作れなかった"), (u"効いた", u"効かなかった"), (u"入った", u"入らなかった"),
         (u"より", u"と同じ"), (u"だけ", u"も"), (u"ない", u"ある"), (u"先", u"後"), (u"有料", u"無料"))
DENOMS = (u"80253", u"79633", u"62747", u"62134")
GROUP_NUMS = (u"62", u"61", u"67", u"5")


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
        for m in re.finditer(r"(?<![0-9A-Za-z.\-])%s(?= ?本)" % g, doc):
            for h in GROUP_NUMS:
                if h != g:
                    out.append((u"W3 %s 本→%s 本 @%d" % (g, h, m.start()), doc[:m.start()] + h + doc[m.end():]))
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
    u"""頭の限界の行を消す・断片を 1 つずつ消す・§3 の数を §2 に足す・§3 の主張を §2 に写す・引用の外の肯定。"""
    out = []
    head, rest = c.doc.split(u"## §1", 1)
    lines = head.split(u"\n")
    for i, (no, frags) in enumerate(LIMIT_FRAGS, 1):
        idx = [k for k, ln in enumerate(lines) if all(p in plain(ln) for p in frags)]
        for k in idx:
            out.append((u"W6L 限界の組 %d の行を消す" % i, u"\n".join(lines[:k] + lines[k + 1:]) + u"## §1" + rest))
        for p in frags:
            out.append((u"W6L 限界の組 %d の断片「%s」を消す" % (i, p[:10]), c.doc.replace(p, u"X", 1)))
    for tok in sorted(set(sec3_number_tokens(c))):
        out.append((u"W4 §3 の数 %s を §2 に足す" % tok, c.doc.replace(u"\n## §3 ", u"\n- 足した行 %s 件。\n\n## §3 " % tok, 1)))
    for p in SEC3_ONLY_PHRASES:
        out.append((u"W4 §3 の主張「%s」を §2 に足す" % p[:6], c.doc.replace(u"\n## §3 ", u"\n- 足した行 %s。\n\n## §3 " % p, 1)))
    for w in (u"XBRL を作れる。", u"会社が型を埋めれば XBRL が作れる。", u"どんな資料も作れる。", u"誤りが無くなる。", u"専用の道具が要らない。", u"EDINET の検査に通る。", u"人が書ける。"):
        out.append((u"D17 引用の外に「%s」を足す" % w, c.doc + u"\n" + w + u"\n"))
    return out


def all_doc_cases(c):
    doc = c.doc
    s3n = sec3_number_tokens(c) or [u"24"]
    cases = span_cases(doc, s3n) + flip_cases(doc, c) + group_cases(doc) + table_cell_cases(doc) + delete_cases(doc, c) + limit_cases(c)
    return cases


def judge_rows_cases(c):
    u"""§1 の表の 10 行の 判定・実測・予測 のセルを、行どうしで入れ替える(全部の対)。"""
    lines = c.doc.split(u"\n")
    idx = [i for i, ln in enumerate(lines) if re.match(r"^\| XM0-\d", ln)]
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


REC_SWEEP_DOCS = (1, 5, 6, 18, 20, 56, 67)


def record_sweep_cases(rec):
    u"""記録の整数・小数・旗の葉を 1 つずつ替える対象(集計 3 つ・予測・書類の代表 7 つ分)。"""
    out = []
    for key in GROUPS:
        for p in leaf_paths(rec[K_SUM][key]):
            out.append((K_SUM, key) + p)
    for p in leaf_paths(rec[PRED_KEY]):
        out.append((PRED_KEY,) + p)
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
MIN_CASES = {u"W1a": 230, u"W1b": 230, u"W1c": 220, u"W2": 170, u"W3": 100, u"W5": 700, u"W6": 270, u"W6L": 28, u"W4": 10, u"D17": 7}


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
        dv, pr, al = rec[K_SUM][G_DEV], rec[K_SUM][G_PROD], rec[K_SUM][G_ALL]
        PN = pr[u"数"]
        self.assertEqual((5, 62, 67), (dv[K_DOCS], pr[K_DOCS], al[K_DOCS]))
        self.assertEqual((62747, 17506, 1647, 2547), tuple(PN[u"対象の fact"][k] for k in (u"数", u"文", u"隠し", u"脚注")))
        self.assertEqual((62134, 17499), (PN[u"型に入った fact"][u"数"], PN[u"型に入った fact"][u"文"]))
        self.assertEqual((613, 7), (PN[u"型の外の fact"][u"合計"][u"数"], PN[u"型の外の fact"][u"合計"][u"文"]))
        self.assertEqual({u"a": 532, u"b": 0, u"c": 0, u"d": 24, u"e": 64, u"f": 3, u"g": 0, u"h": 0}, dict(reasons_of(pr)))
        sv = stat_values(rec)
        self.assertEqual({u"a": (532, 2, 518), u"b": (0, 0, 0), u"c": (0, 0, 0), u"d": (24, 4, 15), u"e": (64, 61, 3), u"f": (3, 2, 2), u"g": (0, 0, 0), u"h": (0, 0, 0)}, dict(sv[u"reasons"]))
        self.assertEqual((61, 53, True, [519, 16, 15], 1640, 14, True, 61, 623), (sv[u"nd"], sv[u"one"], sv[u"one_e"], sv[u"top3"], sv[u"big_target"], sv[u"neg0_docs"], sv[u"units4"], sv[u"units_n"], sv[u"cells"]))
        self.assertEqual((59652, 17497, 2278, 135), tuple(PN[u"型の行"][k] for k in (u"数", u"文", u"2 つ以上の fact をまとめた行", u"値が -0 の行")))
        self.assertEqual((27466, 461, 3281, 1380), tuple(PN[u"対応表の行"][k] for k in (u"科目", u"軸", u"member", u"_cor で終わらない名")))
        self.assertEqual((2305, 12994), (PN[u"持ち込みの属性を持つ fact"][u"数"], PN[u"持ち込みの属性を持つ fact"][u"文"]))
        self.assertEqual((9842, 0, 244, 0), (PN[u"文脈の定義"][u"作った"], PN[u"文脈の定義"][u"作らなかった"], PN[u"単位の定義"][u"作った"], PN[u"単位の定義"][u"作らなかった"]))
        self.assertEqual((61, 61, 0), (PN[u"比べ方 1"][u"属性が意味として同じ"], PN[u"比べ方 1"][u"文脈の名も同じ"], PN[u"比べ方 1"][u"違った fact"]))
        self.assertEqual((61, 61, 61, 61, 61), tuple(PN[u"比べ方 2"][k] for k in (u"組めた", u"fact が意味として同じ", u"字も含めて行が同じ", u"鳴り方が同じ", u"2 回が同じ")))
        self.assertEqual((61, 61, 54807, 54807), (PN[u"混ぜ物"][u"作れた"], PN[u"混ぜ物"][u"効いた"], PN[u"表示の字の検査"][u"掛けた fact"], PN[u"表示の字の検査"][u"合った fact"]))
        self.assertEqual((1, 0), (pr[u"断った書類"], pr[u"型の外の fact が 0 の書類"]))
        self.assertEqual((4987, 1457, 4982, 4481), (dv[u"数"][u"対象の fact"][u"数"], dv[u"数"][u"対象の fact"][u"文"], dv[u"数"][u"型に入った fact"][u"数"], dv[u"数"][u"表示の字の検査"][u"合った fact"]))
        self.assertEqual((226, 3), (len(SG.MUTANTS), len(SG.SILENT_BY_DESIGN)))

    def test_c_1_the_seal_has_the_bound_phrases(self):
        self.assertEqual([], bound_problems(self.c))

    def test_c_2_the_verdicts_are_decided_again_and_equal_the_document(self):
        self.assertEqual([], verdict_problems(self.c))
        j = judge(self.c.rec)
        self.assertEqual(8, sum(1 for v in j.values() if v[0]))
        self.assertEqual([u"XM0-2", u"XM0-3"], miss_ids(j))
        self.assertEqual(list(IDS), list(j))
        self.assertEqual((False,) * 6, suspects(self.c))
        # 当たり外れの判定は丸める前の数。XM0-3 は 620/80253(0.77%)で 0.5% を超え(5 * 80253 = 401265 < 1000 * 620 = 620000)
        P = self.c.rec[K_SUM][G_PROD][u"数"]
        self.assertTrue(1000 * 620 > 5 * 80253)
        self.assertEqual((620, 80253), (nsum(P[u"型の外の fact"][u"合計"]), nsum(P[u"対象の fact"])))
        self.assertEqual((False, u"上"), j[u"XM0-3"])
        self.assertEqual((False, u"下"), j[u"XM0-2"])
        # XM0-9 は 59652/62134 = 96.0%(94% 以上 98% 未満の内)
        self.assertEqual((True, u""), j[u"XM0-9"])
        # 封 §6: XM0-1 が当たり → 候補 (i)〜(iv) を示す(文書 §5 がそれ)
        self.assertTrue(j[u"XM0-1"][0])

    def test_d_1_every_number_in_the_document_is_bound_to_the_record(self):
        self.assertEqual([], doc_number_problems(self.c))
        self.assertEqual([], residual_problems(self.c))

    def test_d_2_every_line_outside_section3_equals_the_one_built_from_the_record(self):
        self.assertEqual([], lines_problems(self.c))
        self.assertEqual([], sanity_problems(self.c))

    def test_d_3_section3_is_bound_only_by_form_not_by_the_record(self):
        self.assertEqual([], sec3_problems(self.c))

    def test_d_4_the_date_supplement_numbers_follow_the_seal_and_the_record(self):
        u"""頭の日付つきの補足の 4982・4987・差の 5 は、封 §0 の字(4982)と記録の開発の 5 本(4987)に縛る。"""
        sec0 = section(self.c.seal, u"## §0 ", u"## §0-2 ")
        self.assertIn(u"数の fact %d(" % SEAL_DECLARED, sec0)
        dv = self.c.rec[K_SUM][G_DEV][u"数"]
        self.assertEqual(4987, dv[u"対象の fact"][u"数"])
        self.assertEqual(5, dv[u"対象の fact"][u"数"] - SEAL_DECLARED)
        self.assertEqual(dv[u"型の外の fact"][u"合計"][u"数"], dv[u"対象の fact"][u"数"] - SEAL_DECLARED)
        self.assertIn(u"開発の 5 本の数の fact を 4982 と申告したが、実装が数えた対象の数の fact は 4987。差の 5 は", self.c.doc)

    def test_d_5_the_gate_counts_in_section4_follow_the_seal_gate(self):
        self.assertEqual(226, len(SG.MUTANTS))
        self.assertEqual(3, len(SG.SILENT_BY_DESIGN))
        self.assertIn(u"変異 226 本のうち 223 本が赤・緑のまま 3 本", self.c.doc)

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
        self.assertEqual((u"34afe495", u"6f719410", u"3cd49ad4"), DOC_COMMITS)

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
        files = list(SHA_PIN) + [DOC_REL]
        before = tuple(sha_file(r) for r in files)
        results = run_mutations(self.base)
        self.assertEqual(before, tuple(sha_file(r) for r in files))
        self.assertEqual(len(MUTATIONS), len(results))
        silent = [(n, k) for n, res in results for k, red in res if not red]
        self.assertEqual([], silent)
        self.assertGreaterEqual(len(MUTATIONS), 76)

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
        flips = ((m_xm01_miss, u"XM0-1"), (m_clear_all, u"XM0-2"), (m_clear_all, u"XM0-3"), (m_e_over_a, u"XM0-4"), (m_ctx_miss, u"XM0-5"), (m_no_made_over, u"XM0-6"), (m_ring_miss, u"XM0-7"),
                 (m_mix_miss, u"XM0-8"), (m_rows_low, u"XM0-9"), (m_rows_high, u"XM0-9"), (m_disp_low, u"XM0-10"))
        for fn, key in flips:
            c = self.base.copy()
            fn(c)
            self.assertNotEqual(base_j[key][0], judge(c.rec)[key][0], (fn.__name__, key))
            self.assertNotEqual([], verdict_problems(c), (fn.__name__, key))
        for fn, idx in ((m_clear_all, 0), (m_in_under90, 1), (m_flag_diff, 2), (m_flag_not_made, 3), (m_declined_many, 4), (m_neg0_zero, 5)):
            c = self.base.copy()
            fn(c)
            self.assertTrue(suspects(c)[idx], (fn.__name__, suspects(c)))
            self.assertNotEqual([], verdict_problems(c), fn.__name__)
        # 外れの向き(XM0-9 の下と上)は別々に出る
        c = self.base.copy()
        m_rows_low(c)
        self.assertEqual(u"下", judge(c.rec)[u"XM0-9"][1])
        c = self.base.copy()
        m_rows_high(c)
        self.assertEqual(u"上", judge(c.rec)[u"XM0-9"][1])
        # 整合の sanity 変異は sanity が赤(recount は緑のまま)
        for fn in (m_a_spread, m_d_docs_over_e, m_unit_not4, m_add_b):
            c = self.base.copy()
            fn(c)
            self.assertEqual([], recount_problems(c), fn.__name__)
            self.assertNotEqual([], sanity_problems(c), fn.__name__)

    def test_g_4_every_check_name_a_mutation_names_exists_and_every_check_has_a_mutation(self):
        named = set(k for _, _, ks in MUTATIONS for k in ks)
        self.assertEqual(set(CHECKS), named)
        for k in (u"numbers", u"resid"):
            self.assertIn(k, ORDER_DOC)

    def test_g_5_the_judgement_edges_at_the_seal_bounds(self):
        u"""境の 1 つ手前と境の数(丸める前の整数): 下限・上限とも含む/含まない。"""
        def j(**kw):
            a = dict(n_docs=62, same2=61, zero_docs=0, out_total=6, tgt_total=1000, reasons=dict((r, 0) for r in LETTERS), same_ctx=61, no_made=0, ring=61, eff=61, made=61, rows=960, in_num=1000,
                     ok_disp=1000, tried=1000)
            a["reasons"][u"a"] = 5
            a.update(kw)
            return judge_nums(**a)
        self.assertTrue(j(same2=58)[u"XM0-1"][0])
        self.assertFalse(j(same2=57)[u"XM0-1"][0])
        self.assertTrue(j(zero_docs=45)[u"XM0-2"][0])
        self.assertFalse(j(zero_docs=44)[u"XM0-2"][0])
        self.assertTrue(j(out_total=5, tgt_total=1000)[u"XM0-3"][0])
        self.assertFalse(j(out_total=6, tgt_total=1000)[u"XM0-3"][0])
        self.assertEqual(u"上", j(out_total=6, tgt_total=1000)[u"XM0-3"][1])
        r = dict((x, 0) for x in LETTERS)
        r.update({u"a": 5, u"e": 4})
        self.assertTrue(j(reasons=r)[u"XM0-4"][0])
        r.update({u"e": 5})
        self.assertFalse(j(reasons=r)[u"XM0-4"][0])
        r.update({u"e": 6})
        self.assertFalse(j(reasons=r)[u"XM0-4"][0])
        self.assertEqual(u"判定できない", j(reasons=dict((x, 0) for x in LETTERS))[u"XM0-4"][1])
        self.assertTrue(j(same_ctx=50)[u"XM0-5"][0])
        self.assertFalse(j(same_ctx=49)[u"XM0-5"][0])
        self.assertTrue(j(no_made=10)[u"XM0-6"][0])
        self.assertFalse(j(no_made=11)[u"XM0-6"][0])
        self.assertTrue(j(ring=45)[u"XM0-7"][0])
        self.assertFalse(j(ring=44)[u"XM0-7"][0])
        self.assertTrue(j(eff=61, made=61)[u"XM0-8"][0])
        self.assertFalse(j(eff=60, made=61)[u"XM0-8"][0])
        self.assertFalse(j(eff=0, made=0)[u"XM0-8"][0])
        self.assertTrue(j(rows=940, in_num=1000)[u"XM0-9"][0])
        self.assertFalse(j(rows=939, in_num=1000)[u"XM0-9"][0])
        self.assertTrue(j(rows=979, in_num=1000)[u"XM0-9"][0])
        self.assertFalse(j(rows=980, in_num=1000)[u"XM0-9"][0])
        self.assertEqual(u"下", j(rows=939, in_num=1000)[u"XM0-9"][1])
        self.assertEqual(u"上", j(rows=980, in_num=1000)[u"XM0-9"][1])
        self.assertTrue(j(ok_disp=99, tried=100)[u"XM0-10"][0])
        self.assertFalse(j(ok_disp=98, tried=100)[u"XM0-10"][0])
        self.assertFalse(j(ok_disp=0, tried=0)[u"XM0-10"][0])

    def test_g_6_the_section5_decision_follows_the_seal_section6(self):
        c = self.base
        sec5 = section(c.doc, u"## §5 ", None)
        s6 = section(c.seal, u"## §6 ", u"## §7 ")
        self.assertEqual(4, len(seal_candidates(s6)))
        self.assertEqual([], sec5_decision_problems(sec5, True, s6))
        self.assertNotEqual([], sec5_decision_problems(sec5, False, s6))
        # 5 つ目の候補・費用の字が落ちる・順の入れ替え・見出しの字・最後の行の後ろの字・見出しの無い案・候補が 3 つ
        for old, new in ((u"(iv) 答えを見ない席", u"(v) 答えを見ない席"), (u"(0 USD。別の封が先)。\n  - (ii)", u"。\n  - (ii)"), (u"(有料。別の封と、払う前の知らせが先)", u""),
                         (u"次の便の候補を 4 つ示す", u"次の便の候補を 3 つ示す"), (u"  - (iv) 答えを見ない席", u"  - (iii) 答えを見ない席"), (u"選ぶのは人間", u"選ばない")):
            self.assertIn(old, sec5, old)
            self.assertNotEqual([], sec5_decision_problems(sec5.replace(old, new, 1), True, s6), old)
        self.assertNotEqual([], sec5_decision_problems(sec5.rstrip(u"\n") + u"\n  - (v) 別の案。\n", True, s6))
        self.assertNotEqual([], sec5_decision_problems(sec5.rstrip(u"\n") + u"\n- 次は別の手がある。\n", True, s6))
        i3 = sec5.index(u"  - (iii)")
        self.assertNotEqual([], sec5_decision_problems(sec5[:i3] + sec5[i3:].split(u"\n", 1)[1], True, s6))
        # 外れたときの形(候補を示さず、違った所の型を読む)は緑で、そこに (i) が在れば赤
        head5 = sec5[:sec5.index(u"- XM0-1 は当たりなので")]
        miss = u"- XM0-1 は外れなので、封 §6 の決めのとおり、違った所の型を読むのが先で、(i)〜(iv) は示さない。\n"
        self.assertEqual([], sec5_decision_problems(head5 + miss, False, s6))
        self.assertNotEqual([], sec5_decision_problems(head5 + miss, True, s6))
        self.assertNotEqual([], sec5_decision_problems(head5 + miss.replace(u"違った所の型を読む", u"X"), False, s6))
        self.assertNotEqual([], sec5_decision_problems(head5 + miss.replace(u"示さない", u"示す"), False, s6))
        # 記録を写しの上で外れに変えると(XM0-1 を外れ)、「示す」の §5 は赤になる(向き)
        cc = self.base.copy()
        m_xm01_miss(cc)
        jj = judge(cc.rec)
        self.assertFalse(jj[u"XM0-1"][0])
        self.assertNotEqual([], sec5_decision_problems(sec5, jj[u"XM0-1"][0], s6))
        self.assertNotEqual([], verdict_problems(cc))

    def test_g_7_the_self_suspicion_flags_fire_at_the_exact_boundaries(self):
        c = self.base.copy()
        P = c.rec[K_SUM][G_PROD]
        N = P[u"数"]
        N[u"対象の fact"][u"数"], N[u"対象の fact"][u"文"] = 1000, 0
        N[u"型に入った fact"][u"数"], N[u"型に入った fact"][u"文"] = 900, 0
        N[u"型の外の fact"][u"合計"][u"数"], N[u"型の外の fact"][u"合計"][u"文"] = 100, 0
        self.assertFalse(suspects(c)[1])
        N[u"型に入った fact"][u"数"] = 899
        self.assertTrue(suspects(c)[1])
        N[u"型の外の fact"][u"合計"][u"数"] = 0
        self.assertTrue(suspects(c)[0])
        N[u"型の外の fact"][u"合計"][u"数"] = 1
        self.assertFalse(suspects(c)[0])
        P[u"断った書類"] = 5
        self.assertFalse(suspects(c)[4])
        P[u"断った書類"] = 6
        self.assertTrue(suspects(c)[4])
        N[u"型の行"][u"値が -0 の行"] = 0
        self.assertTrue(suspects(c)[5])
        N[u"型の行"][u"値が -0 の行"] = 1
        self.assertFalse(suspects(c)[5])

    def test_g_8_the_group_sizes_and_the_numbers_are_not_confused(self):
        rec = self.base.rec
        dev, prod = split_docs(rec)
        self.assertEqual((5, 62, 67), (len(dev), len(prod), len(rec[K_DOCS])))
        self.assertEqual(len(set([5, 62, 67])), 3)
        c = self.base.copy()
        m_swap_dev_prod(c)
        self.assertNotEqual([], recount_problems(c))

    def test_g_9_the_verdict_table_stays_the_62_group_numbers(self):
        c = self.base.with_doc(self.base.doc.replace(u"| 620/80253(0.8%) | 外れ |", u"| 5/4987(0.1%) | 外れ |", 1))
        p = verdict_problems(c)
        self.assertNotEqual([], p)
        self.assertTrue(any(u"混ざっている" in x for x in p), p)
        c = self.base.with_doc(self.base.doc.replace(u"| 620/80253(0.8%) | 外れ |", u"| 625/84740(0.7%) | 外れ |", 1))
        self.assertNotEqual([], verdict_problems(c))
        c = self.base.with_doc(self.base.doc.replace(u"| 59652/62134(96.0%) | 当たり |", u"| 64434/67116(96.0%) | 当たり |", 1))
        self.assertTrue(any(u"混ざっている" in x for x in verdict_problems(c)))
        c = self.base.with_doc(self.base.doc.replace(u"| 54807/54807 | 当たり |", u"| 59288/59288 | 当たり |", 1))
        self.assertTrue(any(u"混ざっている" in x for x in verdict_problems(c)))
        c = self.base.with_doc(self.base.doc.replace(u"| 61 本(62 本のうち) | 当たり |", u"| 66 本(67 本のうち) | 当たり |", 1))
        self.assertNotEqual([], verdict_problems(c))

    def test_h_1_the_sweep_over_every_number_direction_word_group_swap_cell_and_line_stays_red(self):
        c = self.base
        cases = all_doc_cases(c) + judge_rows_cases(c)
        results = run_doc_cases(c, cases)
        silent = [n for n, k in results if k is None]
        by_kind = collections.Counter(n.split(u" ")[0] for n, _ in results)
        self.assertEqual(sorted(EXPECTED_SILENT), sorted(silent))
        for kind, lo in MIN_CASES.items():
            self.assertGreaterEqual(by_kind[kind], lo, kind)
        self.assertGreater(len(results), 2000)

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
