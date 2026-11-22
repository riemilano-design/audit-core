# -*- coding: utf-8 -*-
u"""結果の門: 封 docs/XBRL_PRIOR_YEAR_FACT_GUARD_SEAL_2026-11-22.md(2079af62)の結果の文書 docs/XBRL_PRIOR_YEAR_FACT_GUARD_RESULT_2026-11-22.md(便 XZ1)。

封の門 ``test_xbrl_prior_year_fact_guard_seal.py`` の次の段。**追跡されている記録・script・封・封の門・便 XZ0 の記録・結果の文書と git の履歴だけを読む**(書類の置き場は読まない・通信しない・鍵は読まない)。
便 XA0 の結果の門 ``test_xbrl_sheet_wall_result.py`` の部品(読み・sha256・% の丸め・節の切り出し・数のトークン・禁止語・blob の道具)を読み込んで使う(門としては走らせない)。
検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表と、全部のセルを 1 か所ずつ掃く ``SWEEPS`` で(木の file は変異させず、``Ctx`` の写しに当てる)。

 a script・記録・封・封の門・便 XZ0 の記録の sha256(字で留める)・記録の script の sha256・封の commit の欄・記録の限界の欄・材料と engine の指紋(便 XZ0 の記録と同じ)が script の字と同じ
 b 記録の数え直し: 書類ごとの数から、**script の関数を使わずに**、60 組・3 組・63 組の集計の全部の欄を数え直す(類の和・段の間の移りの行と列の和・止めた fact と段の類の関係・属性の和)。
   予測の判定に要る数・先に疑う旗 4 つを集計から作り直した値と照らす。段 HT は便 XZ0 の記録の同じ番号の束 3・段 HT と 63 組の全部で同じ
 c 予測 XZ1-1〜XZ1-8 の当たり外れを、封 §4 の字から取った境(丸める前の整数・分数で)と記録から決め直し、文書 §1 の表・件数と同じことを見る(60 組だけ)。
   封 §4 の「先に自分の欠陥を疑う」4 つの旗を決め直す(どれも立たない)・封 §6 の決め(XZ1-1 と XZ1-2 が両方当たりなら次の便の候補 (i)(ii) を示す)と文書 §5 が合う
 d 結果の文書の数: §1・§2・§4・§5 の数は全部、記録から導く(組ごとの率の最小・中央・最大と 70・80・90・95% 以上の組の数・W1 の在る組・多い順の 5 組と 10 組・5% 以上と 1% 以上の組・S の在る組は門の中で導き直す)。
   記録の数と字から文書の §3 以外の全部の行を組み直し、文書と行ごとに照らす(``render_doc``)。主な主張の文は断片でも縛る。
   **§3 の数(記録に欄の無い読み。監査の席の数え直し)は記録に縛らず**、見出し・字で留めた数の並び・記録の数との足し算・§3 の外にその数が出ないこと・「測っていない」を縛る
 e 文書の頭の負けと限界(封 §7 の 6 本・封 §0 の申告)・禁止語・「XBRL を作れる」「EDINET の検査に通る」「専用の道具が要らない」「AI が書ける」「人が書ける」「黙って違う fact は無い」「0 になった」を肯定で書かない・docID と EDINET コードの形
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


WG = load_module("tests/measure/test_xbrl_sheet_wall_result.py", "xbrl_sheet_wall_result_gate_for_prior_year_fact_guard_result_gate")                # 便 XA0 の結果の門の部品。門としては走らせない
SG = load_module("tests/measure/test_xbrl_prior_year_fact_guard_seal.py", "xbrl_prior_year_fact_guard_seal_gate_for_result_gate")                # 封の門の部品。門としては走らせない
PR = SG.PR
MS = SG.MS

read, sha_file, guard, pct, section = WG.read, WG.sha_file, WG.guard, WG.pct, WG.section
ints_in, doc_number_tokens = WG.ints_in, WG.doc_number_tokens

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
RECORD_REL = SG.RECORD_REL
DRAFT_RECORD_REL = SG.DRAFT_RECORD_REL
GATE_REL = "tests/measure/test_xbrl_prior_year_fact_guard_result.py"
DOC_REL = "docs/XBRL_PRIOR_YEAR_FACT_GUARD_RESULT_2026-11-22.md"
SCRIPT_COMMIT_SHORT = "d6a18d51"                  # script と封の門を足した commit
RECORD_COMMIT_SHORT = "ca34473a"                  # 記録を足した commit
BLOB_AT = collections.OrderedDict([
    (SEAL_REL, SEAL_COMMIT_SHORT), (SCRIPT_REL, SCRIPT_COMMIT_SHORT), (SEAL_GATE_REL, SCRIPT_COMMIT_SHORT), (RECORD_REL, RECORD_COMMIT_SHORT)])
HISTORY = collections.OrderedDict([
    (SEAL_REL, [SEAL_COMMIT_SHORT]), (SCRIPT_REL, [SCRIPT_COMMIT_SHORT]), (SEAL_GATE_REL, [SCRIPT_COMMIT_SHORT]), (RECORD_REL, [RECORD_COMMIT_SHORT])])
DOC_COMMITS = (SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT)

SHA_PIN = collections.OrderedDict([
    (RECORD_REL, "22c7c8bafcb2de913a876080cae047bfc9e4455224ba527814ce4ddd17775f75"),
    (SCRIPT_REL, "eb2bb8de68a92ec0c555f11243d5ac45f656fe8350b31339fe667cf416934240"),
    (SEAL_GATE_REL, "0a0e82c44d2208b7a74f803ce82b829257857964b7a4406a84a3a7568d27dd65"),
    (SEAL_REL, "7de59fd4353d9b0e3fd2b750e0dd51f0c75c660f585492cd56d840420b416e5a"),
    (DRAFT_RECORD_REL, "1b4cea2d252591cf19c66a46b1e05455a029c8b3c97357becdb846665a56e25d")])

PAIRS = 63
DOC_COUNT = 67
DROPPED = 4
SEEN_MAX = 3
N60 = 60
SUM60 = 61100
SUM3 = 3434
SUM63 = 64534
CLS = ("X", "U", "A", "W1", "W2", "N")
CLS_S = CLS + ("S",)
STAGES = ("HT", "O", "G", "OG")
K60 = u"集計 60 組(番号 3 より大きい。予測の判定はここだけ)"
K3 = u"集計 3 組(番号 3 以下。訓練。規則を作るのに見た組)"
K63 = u"集計 63 組"
GROUPS = (K60, K3, K63)
K_FACTS = u"行の中の数の fact の数"
K_ST = u"段ごとの類別"
K_MAT = u"段 HT の類 → 段 O の類(行が段 HT の類・列が段 O の類)"
K_SG = u"段 G が止めた fact の段 HT の類別"
K_SOG = u"段 OG が止めた fact の段 O の類別"
K_NUMCOL = u"番号の列を使った fact の数"
K_ATTR = u"段 HT の W1 の違う属性の組ごとの数"
K_NN = u"段 HT の W1 のうち番号だけの違いの数"
AGG_KEYS = (K_FACTS, K_ST, K_MAT, K_SG, K_SOG, K_NUMCOL, K_ATTR, K_NN)
ATTR_KEYS = tuple(u"違う属性 " + x for x in (u"name", u"contextRef", u"unitRef", u"name+contextRef", u"name+unitRef", u"contextRef+unitRef", u"name+contextRef+unitRef"))
CTX_ATTRS = tuple(k for k in ATTR_KEYS if u"contextRef" in k)
PRED_KEY = u"予測の判定に要る数(XZ1-1〜XZ1-8。60 組だけ。当たり・外れは結果の文書で)"
FLAG_KEY = u"先に自分の欠陥を疑う旗(止めない。当たり外れではない)"
IDS = (u"XZ1-1", u"XZ1-2", u"XZ1-3", u"XZ1-4", u"XZ1-5", u"XZ1-6", u"XZ1-7", u"XZ1-8")
P11 = u"XZ1-1 段 OG の類 W1 / 行の中の数の fact"
P11B = u"XZ1-1 段 OG の類 W1 / 通した(U + W1)"
P12 = u"XZ1-2 段 OG の類 U / 行の中の数の fact"
P13 = u"XZ1-3 段 O の W1 と段 HT の W1"
P14 = u"XZ1-4 段 O の U と段 HT の U"
P15 = u"XZ1-5 段 G が止めた段 HT の U / 行の中の数の fact"
P16 = u"XZ1-6 段 G が止めた段 HT の W1 / 段 HT の W1"
P17 = u"XZ1-7 段 HT の W1 のうち番号だけの違い / 段 HT の W1"
P4 = u"読み方の 4 区分(段 OG)"
P18 = u"XZ1-8 段 OG の W1 が 0 の組の数 / 60 組の組の数"
PRED_KEYS = (P11, P11B, P12, P13, P14, P15, P16, P17, P4, P18)
FL1 = u"段 OG の類 W1 が 60 組の全部で 0(守りが全部を止めていないか)"
FL2 = u"段 G の S が 60 組の fact の 30% を超えた(表の頭の印の取り違えか)"
FL3 = u"段 OG の S が 60 組の fact の 30% を超えた(表の頭の印の取り違えか)"
FL4 = u"番号の列を使った fact が 60 組で 0(形の読み違いか)"
FLAG_KEYS = (FL1, FL2, FL3, FL4)
THRESHOLDS = (70, 80, 90, 95)

# 封の字(封の門が script と照らし、ここでは文書が引く字の在り処を縛る)
BOUND_SEAL_PHRASES = (u"段 OG の類 W1 は fact の 1.0% 以下", u"段 OG の類 U は fact の 72.0% 以上",
                      u"段 O の W1 は段 HT の W1 より 300 以上少なく、段 HT で W1 でも W2 でもなかった fact が段 O で W1 になった数は 50 以下", u"段 O の U は段 HT の U より 400 以上多い",
                      u"段 G が止めた段 HT の U は、fact の 1.0% 以上 8.0% 以下", u"段 G が止めた段 HT の W1 は、段 HT の W1 の 50% 以上",
                      u"段 HT の W1 のうち「番号だけの違い」は 10% 以上 45% 以下", u"段 OG の W1 が 0 の組は 20 組以上",
                      u"段 OG の W1 が 60 組の全部で 0", u"S が fact の 30% を超えた", u"番号の列を使った fact が 60 組で 0",
                      u"XZ1-1 と XZ1-2 が両方当たりなら、次の便の候補を人間に示す", u"どちらかが外れたら、残った W1 の数と段の間の移りを書いて、作る側へ進む道を人間に返す",
                      u"W1 の率は、分母を fact の全部にしたものと「通した」にしたものの 2 通りで書く", u"使う人に見えるのは「通した(U + W1)」「止めた(S)」「候補が複数(A + W2)」「候補なし(N + X)」の 4 つだけ",
                      u"(i) 前の年の書類と今年の数の字から紙(便 XS0 の形)を書き出し、決まった組み方で組み、今年の書類と Arelle が読む fact で比べる(0 USD。別の封が先)",
                      u"(ii) 通さなかった fact(S・A・W2・N・X)だけを、切れない設定に直した AI の席へ送る(有料。別の封と、払う前の知らせが先)",
                      u"「XBRL を作れる」「EDINET の検査に通る」「専用の道具が要らない」「AI が書ける」「黙って違う fact は無い」は、この便からは言えない",
                      u"規則と守りは 3 組を見て作った", u"残りの 60 組(番号 4〜63)だけで判定する", u"3 組の数は「訓練」で、当たって当然")
# 封 §7 の限界 6 本(封の字)に対応する、文書の頭に在るべき断片(文書の言い回しは封と少し違う所が在るので、断片で縛る)。1 本につき断片は全部同じ行に在る。
LIMIT_FRAGS = (
    (u"規則と守りは、並びの頭の 3 組を見て作った(封 §0 の申告)", u"予測は残りの 60 組だけで判定した", u"3 組の数は訓練で、当たって当然", u"60 組の数が本当の数", u"60 組も同じ 63 組の引きの中で、無作為ではない",
     u"業種はほぼ一般商工業・有報だけ・年は 1 年の差だけ"),
    (u"番号つきのメンバーの形は `No`・`Row` で始まる 2 通りだけ", u"ほかの付け方の番号は拾わない"),
    (u"段 O の行の番号は「今年の表の行の順が、今年の正しい番号の順」という仮定に立つ", u"仮定が破れる表では W1 を新しく作る"),
    (u"表の頭の印は、最初に fact を持つ行より前の行の字だけ", u"頭の字が同じまま列がずれた表・頭の行に fact が在る表は止められない", u"数字を除くので、年・期の数字だけが変わった頭は同じと見る"),
    (u"便 XZ0 の限界はそのまま", u"fact の置き場は答えから取っている", u"どちらの年も専用の道具が組んだ後の字", u"文脈は名で比べ定義は見ない", u"`sign`・`format`・nil・値・数でない fact は測らない",
     u"前の年の XBRL が在る会社だけ"),
    (u"「XBRL を作れる」「EDINET の検査に通る」「専用の道具が要らない」「AI が書ける」「黙って違う fact は無い」は、この便からは言えない",))
HEAD_PHRASES = (u"先に負けと限界を書く", u"記録から 1 つずつ読んだもの", u"0 USD・LLM の席は呼んでいない・通信していない", u"engine は 0 行", u"書類は今年の側も前の年の側も置き場に在ったもの",
                u"黙って違う fact を自分で作る", u"W1 が 0 になったのではない", u"止めた fact の半分近くは、止めなくてよかった", u"60 組の数が本当の数", u"予測は残りの 60 組だけで判定した",
                u"3 組の数は訓練で、当たって当然", u"盲検ではない", u"W1 も S の中身も、答えを知らないと見えない", u"使う人に見えるのは「通した」「止めた」「候補が複数」「候補なし」の 4 つだけ",
                u"記録に欄の無い読み")
PHRASES = (u"言えること", u"言えないこと", u"相手の問いへの、この便からの答え", u"封も予測も結果を見てから書き換えていない", u"記録は当たり外れを持たない", u"判定は丸める前の数でした",
           u"原稿からの率ではない", u"0 にはなっていない", u"予測の判定には使わない", u"実装で決めた所", u"封は書き換えない", u"その読みでの数は測っていない", u"60 組では確かめていない",
           u"どれも同じ動きになる書き換え(同値)", u"通した fact も別の手段(値・定義)で確かめる段は要る",
           u"通した fact(U + W1)", u"を分母にすると", u"fact の全部を分母にすると", u"使う人に見える 4 区分(段 OG・60 組)", u"60 組の数が本当の数")
MAIN_CLAIMS = (u"予測の 1 本(XZ1-3)は外れ", u"新しく W1 にした", u"W1 が 0 になったのではない", u"止めた fact の半分近くは、止めなくてよかった", u"60 組の数が本当の数",
               u"100 個に 1 個ほど", u"0 にはなっていない", u"黙って違う fact を自分で作る", u"両方当たりなので示す", u"規則と守りを足しても、黙って違う fact は残る", u"守りは正しい fact も止める",
               u"3 組の数は訓練で、当たって当然")
QUOTED = re.compile(u"「[^」]*(?:作れる|専用の道具が要らない|人が書ける|AI が書ける|検査に通る|黙って違う fact は無い)[^」]*」")
AFFIRM_WORDS = (u"作れる(?!か)", u"作れます", u"専用の道具が要らない", u"人が書ける(?!か)", u"AI が書ける", u"検査に通る(?!こと|か)", u"黙って違う fact は無い", u"0 になった(?!のではない)")
FORBIDDEN_WORDS = tuple(WG.FORBIDDEN_WORDS)
STRUCTURAL = WG.STRUCTURAL
# 記録から組んだ値の外に在ってよい数(字で留める。封の境・文書の見出しや説明の数)。理由は 1 つずつ:
#   1 2 3 4 6 = 項の番号・「6 回」(REVISE 6 回。commit d6a18d51 の message が書く)・「4 つ」「2 通り」/ 72 1 300 50 400 8 10 45 20 30 = 封 §4 の境
#   63 67 60 = 材料の数 / 100 25 = 「100 個に 1 個」「25 個に 1 個」(U + W1 と W1 の比から sanity が見る) / 5 1 = 「5% 以上」「1% 以上」の見出し / 70 80 90 95 = 組ごとの率のしきい値の見出し
#   160 = 封の門の変異の数(MUTANTS の長さ。字で縛る) / 4% = 「4% ほど」(止めた fact の率から sanity が見る)
RESIDUAL_OK = set([u"72.0", u"8.0", u"72", u"1", u"2", u"3", u"4", u"6", u"300", u"50", u"400", u"8", u"10", u"45", u"20", u"30", u"63", u"67", u"60", u"100", u"25", u"5", u"70", u"80", u"90", u"95"])
# 文書 §3(記録に欄の無い読み。監査の席の数え直し)の行ごとの数の並び。記録から導けない = 正本は文書の字そのもの = ここに字で留める(留め)
SEC3_LINES = (
    (u"**規則が新しく作った W1 114**", (u"114", u"45", u"69", u"12", u"3", u"76", u"1", u"97", u"3", u"14")),
    (u"**段 OG に残った W1 474**", (u"474", u"342", u"132")),
    (u"**段 OG が止めた正しい fact 1107**", (u"1107", u"1008", u"99", u"2")),
    (u"ここから言えるのは「残った W1 の 7 割ほどは", (u"7",)),
)
SEC3_ONLY = (u"12", u"76", u"97", u"14", u"1008", u"99", u"132")          # §3 の外に出てはならない数(記録に欄が無い。342 は §2 に記録の数(段 HT の 1 組の最大)として出る。偶然同じ値。§3 の 342 の主張は §3 の外に出ない)
SEC3_PHRASES = (u"測っていない", u"型の名は監査の席が付けた", u"行の字・要素の名・文脈の名は記録にも報告にも無い", u"行の順の仮定が破れた表が主",
                u"今年の fact の本来の番号が行の順の通し番号より大きいもの", u"通し番号と等しいのに W1 になったもの", u"今年の側の文脈に番号つきの形が無いもの",
                u"12 組にしか無く、多い順の 3 組で", u"今年の番号が 1 から始まらない・飛ぶ・数えに入らない行が在る、など", u"仮定が破れた表が主、と読める", u"番号の列を使わない行のものが", u"上の節の段 HT の最大と値が同じなのは偶然で、別の量",
                u"年・期の数字だけの違いではなく", u"が大半、と読める", u"どれも今年の表の頭の印と前の年の頭の印が、どちらも空でなく、違っていた",
                u"候補の文脈が今年と違うのに、表の頭の印は同じだった", u"行の順の規則では直せず、守りも止めない", u"番号の列を使った行のものが", u"番号がずれたまま",
                u"前の年の頭の印と部分的にも重ならないもの", u"一方が他方を含むもの", u"頭の行の語そのものが 2 つの年で変わった表",
                u"残った W1 の 7 割ほどは、頭の字が同じまま文脈がずれた所で、この便の規則と守りの外", u"巻き添えの大半は、頭の語が変わった表",
                u"頭の印の比べ方を緩めれば巻き添えが減るか・残った W1 を別の守りで止められるかは、測っていない")


# ======================================================================================================
class Ctx(object):
    u"""検査が見る写し。変異はこの写しを変える(木の file は変えない)。"""

    def __init__(self):
        self.rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        self.draft = json.loads(read(DRAFT_RECORD_REL), object_pairs_hook=collections.OrderedDict)
        self.doc = read(DOC_REL)
        self.seal = read(SEAL_REL)
        self.shas = collections.OrderedDict((rel, sha_file(rel)) for rel in SHA_PIN)

    def copy(self):
        c = Ctx.__new__(Ctx)
        c.rec = copy.deepcopy(self.rec)
        c.draft = copy.deepcopy(self.draft)
        c.doc = self.doc
        c.seal = self.seal
        c.shas = collections.OrderedDict(self.shas)
        return c

    def with_doc(self, doc):
        u"""文書だけ替えた写し(記録は共有。文書の変異用。記録は変えない)。"""
        c = Ctx.__new__(Ctx)
        c.rec, c.draft, c.seal, c.shas = self.rec, self.draft, self.seal, self.shas
        c.doc = doc
        return c


def norm(o):
    return json.loads(json.dumps(o, ensure_ascii=False))


def plain(s):
    return s.replace(u"**", u"")


def pct2(n, d):
    u"""n/d の % を小数第 2 位まで(四捨五入。0.5 は上げる)。整数で。"""
    return u"%.2f" % (((20000 * n + d) // (2 * d)) / 100.0)


def f(a, b):
    return u"%d/%d(%s%%)" % (a, b, pct(a, b))


def fpct(fr):
    return pct(fr.numerator, fr.denominator)


# ======================================================================================================
# b 数え直し(script の関数は使わない)
def add_tree(x, y):
    if isinstance(x, dict):
        assert list(x) == list(y), (list(x), list(y))
        return collections.OrderedDict((k, add_tree(x[k], y[k])) for k in x)
    return x + y


def sum_docs(docs):
    out = None
    for d in docs:
        v = collections.OrderedDict((k, copy.deepcopy(d[k])) for k in AGG_KEYS)
        out = v if out is None else add_tree(out, v)
    return out


def split_docs(rec):
    docs = rec[u"書類"]
    return [d for d in docs if d[u"番号"] > SEEN_MAX], [d for d in docs if d[u"番号"] <= SEEN_MAX]


def doc_problems(d):
    u"""書類 1 つの中の関係(類の和・X の不変・段の間の移りの行と列の和・止めた fact と段の類・属性の和)。"""
    out = []
    n = d[u"番号"]
    facts = d[K_FACTS]
    st = d[K_ST]
    if list(st) != list(STAGES):
        return [u"書類 %d の段の名・並びが違う" % n]
    for s in STAGES:
        keys = CLS_S if s in (u"G", u"OG") else CLS
        if list(st[s]) != list(keys) or sum(st[s].values()) != facts or min(st[s].values()) < 0:
            out.append(u"書類 %d の段 %s の類の和が fact の数と違う" % (n, s))
    if not (st[u"HT"][u"X"] == st[u"O"][u"X"] == st[u"G"][u"X"] == st[u"OG"][u"X"]):
        out.append(u"書類 %d の X が段で違う" % n)
    mat = d[K_MAT]
    if list(mat) != list(CLS) or any(list(mat[c]) != list(CLS) for c in CLS):
        return out + [u"書類 %d の段の間の移りの表の形が違う" % n]
    for c in CLS:
        if sum(mat[c].values()) != st[u"HT"][c]:
            out.append(u"書類 %d の移りの行 %s の和が段 HT の類と違う" % (n, c))
        if sum(mat[r][c] for r in CLS) != st[u"O"][c]:
            out.append(u"書類 %d の移りの列 %s の和が段 O の類と違う" % (n, c))
    if any(mat[u"X"][c] for c in CLS if c != u"X") or any(mat[r][u"X"] for r in CLS if r != u"X") or any(mat[r][u"N"] for r in CLS if r != u"N"):
        out.append(u"書類 %d で X が動いたか、置き場の無い fact(N)でない fact が N になった" % n)
    for key, src, dst in ((K_SG, u"HT", u"G"), (K_SOG, u"O", u"OG")):
        stop = d[key]
        if list(stop) != list(CLS) or stop[u"X"] != 0 or stop[u"N"] != 0 or min(stop.values()) < 0:
            out.append(u"書類 %d の %s の形・X・N が違う" % (n, key[:6]))
            continue
        if st[dst][u"S"] != sum(stop.values()):
            out.append(u"書類 %d の段 %s の S が止めた fact の和と違う" % (n, dst))
        for c in (u"U", u"A", u"W1", u"W2"):
            if st[dst][c] != st[src][c] - stop[c]:
                out.append(u"書類 %d の段 %s の類 %s が段 %s の類 - 止めた fact と違う" % (n, dst, c, src))
        if st[dst][u"X"] != st[src][u"X"] or st[dst][u"N"] != st[src][u"N"]:
            out.append(u"書類 %d の段 %s の X か N が段 %s と違う" % (n, dst, src))
    attr = d[K_ATTR]
    if list(attr) != list(ATTR_KEYS) or sum(attr.values()) != st[u"HT"][u"W1"] or min(attr.values()) < 0:
        out.append(u"書類 %d の W1 の違う属性の和が段 HT の W1 と違う" % n)
    elif not (0 <= d[K_NN] <= sum(attr[k] for k in CTX_ATTRS)):
        out.append(u"書類 %d の番号だけの違いが contextRef の違う W1 より多いか負" % n)
    if not (0 <= d[K_NUMCOL] <= facts):
        out.append(u"書類 %d の番号の列を使った fact が fact の数より多いか負" % n)
    return out


def zero_docs_og(rec):
    d60, _ = split_docs(rec)
    return sum(1 for d in d60 if d[K_ST][u"OG"][u"W1"] == 0)


def rate_row(n, d):
    return collections.OrderedDict([(u"fact", n), (u"分母", d), (u"%", float(pct(n, d)))])


def pred_expected(rec):
    a = rec[K60]
    S = a[K_ST]
    D = a[K_FACTS]
    ht, o, g, og = S[u"HT"], S[u"O"], S[u"G"], S[u"OG"]
    mat = a[K_MAT]
    through = og[u"U"] + og[u"W1"]
    new_w1 = sum(mat[c][u"W1"] for c in (u"X", u"U", u"A", u"N"))
    sog = a[K_SOG]
    return collections.OrderedDict([
        (P11, rate_row(og[u"W1"], D)), (P11B, rate_row(og[u"W1"], through)), (P12, rate_row(og[u"U"], D)),
        (P13, collections.OrderedDict([(u"段 HT の W1", ht[u"W1"]), (u"段 O の W1", o[u"W1"]), (u"段 HT の W1 から段 O の W1 を引いた数", ht[u"W1"] - o[u"W1"]),
                                       (u"段 HT で W1 でも W2 でもなかった fact が段 O で W1 になった数", new_w1)])),
        (P14, collections.OrderedDict([(u"段 HT の U", ht[u"U"]), (u"段 O の U", o[u"U"]), (u"段 O の U から段 HT の U を引いた数", o[u"U"] - ht[u"U"])])),
        (P15, rate_row(a[K_SG][u"U"], D)), (P16, rate_row(a[K_SG][u"W1"], ht[u"W1"])), (P17, rate_row(a[K_NN], ht[u"W1"])),
        (P4, collections.OrderedDict([(u"通した(U + W1)", through), (u"止めた(S)", og[u"S"]), (u"候補が複数(A + W2)", og[u"A"] + og[u"W2"]), (u"候補なし(N + X)", og[u"N"] + og[u"X"]),
                                      (u"止めたうち正しかった(段 O の類 U)", sog[u"U"]), (u"止めたうち正しかった割合(%)", float(pct(sog[u"U"], og[u"S"])))])),
        (P18, collections.OrderedDict([(u"W1 が 0 の組", zero_docs_og(rec)), (u"60 組の組の数", len(split_docs(rec)[0]))]))])


def flags_expected(rec):
    a = rec[K60]
    S = a[K_ST]
    D = a[K_FACTS]
    z, n60 = zero_docs_og(rec), len(split_docs(rec)[0])
    return collections.OrderedDict([
        (FL1, collections.OrderedDict([(u"W1 が 0 の組の数", z), (u"60 組の組の数", n60), (u"旗", z == n60)])),
        (FL2, collections.OrderedDict([(u"fact", S[u"G"][u"S"]), (u"分母", D), (u"旗", 100 * S[u"G"][u"S"] > 30 * D)])),
        (FL3, collections.OrderedDict([(u"fact", S[u"OG"][u"S"]), (u"分母", D), (u"旗", 100 * S[u"OG"][u"S"] > 30 * D)])),
        (FL4, collections.OrderedDict([(u"fact", a[K_NUMCOL]), (u"旗", a[K_NUMCOL] == 0)]))])


def recount_problems(c):
    rec = c.rec
    out = []
    docs = rec[u"書類"]
    m = rec[u"材料"]
    nums = [d[u"番号"] for d in docs]
    if len(nums) != PAIRS or nums != sorted(set(nums)) or nums[0] < 1 or nums[-1] > DOC_COUNT or m[u"組の数"] != PAIRS or m[u"今年の側の書類の本数"] != DOC_COUNT or m[u"除いた今年の書類の数"] != DROPPED \
            or m[u"今年の側の書類の本数"] != m[u"組の数"] + m[u"除いた今年の書類の数"] or m[u"60 組の組の数(番号 3 より大きい組)"] != N60 or m[u"3 組の組の数(番号 3 以下の組。訓練)"] != SEEN_MAX:
        return [u"書類の番号(67 本の中の昇順の 63 個)・材料の組の数 63・今年の側 67・除いた 4・60 組・3 組が違う"]
    d60, d3 = split_docs(rec)
    if len(d60) != N60 or len(d3) != SEEN_MAX:
        return [u"60 組と 3 組の分けが違う"]
    for d in docs:
        if list(d) != [u"番号"] + list(AGG_KEYS):
            return [u"書類 %d の欄が違う" % d[u"番号"]]
        out.extend(doc_problems(d))
    for key, ds in ((K60, d60), (K3, d3), (K63, docs)):
        want = sum_docs(ds)
        if norm(rec[key]) != norm(want):
            out.append(u"%s が書類ごとの数から数え直した値と違う" % key[:8])
    if list(rec[K60].values()) and (rec[K60][K_FACTS] != SUM60 or rec[K3][K_FACTS] != SUM3 or rec[K63][K_FACTS] != SUM63):
        out.append(u"60 組・3 組・63 組の fact の合計が字で留めた 61100・3434・64534 と違う")
    if list(rec[PRED_KEY]) != list(PRED_KEYS) or list(rec[FLAG_KEY]) != list(FLAG_KEYS):
        return out + [u"予測の判定に要る数・旗の欄の名が違う"]
    if norm(rec[PRED_KEY]) != norm(pred_expected(rec)):
        out.append(u"予測の判定に要る数が集計から作り直した値と違う")
    if norm(rec[FLAG_KEY]) != norm(flags_expected(rec)):
        out.append(u"先に疑う旗の 4 つが集計から作り直した値と違う")
    # 便 XZ0 の記録との照らし: 段 HT は同じ番号の束 3・段 HT と 63 組の全部で同じ・材料と engine の指紋も同じ
    by = dict((d[u"番号"], d) for d in c.draft[u"書類"])
    for d in docs:
        x = by.get(d[u"番号"])
        if x is None or dict(x[u"束と段ごとの類別"][u"束 3"]["HT"]) != dict(d[K_ST][u"HT"]) or x[u"行の中の数の fact の数"] != d[K_FACTS]:
            out.append(u"書類 %d の段 HT が便 XZ0 の記録の束 3・段 HT と違う" % d[u"番号"])
    if dict(m) != dict(c.draft[u"材料"]) and any(m[k] != c.draft[u"材料"][k] for k in c.draft[u"材料"]):
        out.append(u"材料の字が便 XZ0 の記録と違う")
    if rec[u"engine の指紋"] != c.draft[u"engine の指紋"]:
        out.append(u"engine の指紋が便 XZ0 の記録と違う")
    if rec[K63][K_ST][u"HT"][u"U"] != c.draft[u"集計"][u"束と段ごとの類別"][u"束 3"]["HT"][u"U"] or rec[K63][K_ST][u"HT"][u"W1"] != c.draft[u"集計"][u"束と段ごとの類別"][u"束 3"]["HT"][u"W1"]:
        out.append(u"63 組の段 HT の U・W1 が便 XZ0 の記録と違う")
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
    if c.rec[u"step"] != u"XZ1(前の年の下書きが黙って違う属性を付ける fact を、行の順で番号を振り直す規則と表の頭の字の守りで直す・止める)(0 USD・engine は 0 行)":
        out.append(u"記録の step の欄が違う")
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
    rows = [ln for ln in sec4.splitlines() if re.match(r"^\| XZ1-\d", ln)]
    if len(rows) != 8:
        out.append(u"封 §4 の表の行が 8 つでない")
    sec7 = section(c.seal, u"## §7 ", None)
    if len([ln for ln in sec7.splitlines() if ln.startswith(u"- ")]) != 6:
        out.append(u"封 §7 の限界の行が 6 行でない")
    sec0 = section(c.seal, u"## §0 ", u"## §1 ")
    if u"並びの頭の 3 組" not in sec0 or u"3 組の数は「訓練」で、当たって当然" not in sec0:
        out.append(u"封 §0 に頭の 3 組の申告が無い")
    return out


# ======================================================================================================
# c 当たり外れの決め直し(封 §4 の境。丸める前の整数・分数。60 組だけ)
def judge_nums(D, og_w1, og_u, ht_w1, o_w1, new_w1, ht_u, o_u, stop_u, stop_w1, nn, z):
    u"""封 §4 の境(整数のまま)。値は (当たりか, 外れた向き)。"""
    out = collections.OrderedDict()
    out[u"XZ1-1"] = (100 * og_w1 <= 1 * D, u"" if 100 * og_w1 <= D else u"上")
    out[u"XZ1-2"] = (1000 * og_u >= 720 * D, u"" if 1000 * og_u >= 720 * D else u"下")
    a_ok = ht_w1 - o_w1 >= 300
    b_ok = new_w1 <= 50
    out[u"XZ1-3"] = (a_ok and b_ok, u"" if a_ok and b_ok else u"差" if not a_ok and b_ok else u"新" if a_ok else u"差と新")
    out[u"XZ1-4"] = (o_u - ht_u >= 400, u"" if o_u - ht_u >= 400 else u"下")
    lo5, hi5 = 100 * stop_u >= 1 * D, 100 * stop_u <= 8 * D
    out[u"XZ1-5"] = (lo5 and hi5, u"" if lo5 and hi5 else u"下" if not lo5 else u"上")
    out[u"XZ1-6"] = (100 * stop_w1 >= 50 * ht_w1, u"" if 100 * stop_w1 >= 50 * ht_w1 else u"下")
    lo7, hi7 = 100 * nn >= 10 * ht_w1, 100 * nn <= 45 * ht_w1
    out[u"XZ1-7"] = (lo7 and hi7, u"" if lo7 and hi7 else u"下" if not lo7 else u"上")
    out[u"XZ1-8"] = (z >= 20, u"" if z >= 20 else u"下")
    return out


def new_w1_of(a):
    mat = a[K_MAT]
    return sum(mat[c][u"W1"] for c in (u"X", u"U", u"A", u"N"))


def judge(rec):
    a = rec[K60]
    S = a[K_ST]
    return judge_nums(a[K_FACTS], S[u"OG"][u"W1"], S[u"OG"][u"U"], S[u"HT"][u"W1"], S[u"O"][u"W1"], new_w1_of(a), S[u"HT"][u"U"], S[u"O"][u"U"], a[K_SG][u"U"], a[K_SG][u"W1"], a[K_NN],
                      zero_docs_og(rec))


def suspects(c):
    u"""封 §4 の「先に自分の欠陥を疑う」4 つの旗(封の字のまま)。"""
    return tuple(v[u"旗"] for v in flags_expected(c.rec).values())


def cell_text(rec, key):
    a = rec[K60]
    S = a[K_ST]
    D = a[K_FACTS]
    ht, o, og = S[u"HT"], S[u"O"], S[u"OG"]
    return {u"XZ1-1": f(og[u"W1"], D), u"XZ1-2": f(og[u"U"], D),
            u"XZ1-3": u"段 HT %d・段 O %d・差 %d、新しく W1 になった数 %d" % (ht[u"W1"], o[u"W1"], ht[u"W1"] - o[u"W1"], new_w1_of(a)),
            u"XZ1-4": u"段 HT %d・段 O %d・差 %d" % (ht[u"U"], o[u"U"], o[u"U"] - ht[u"U"]),
            u"XZ1-5": f(a[K_SG][u"U"], D), u"XZ1-6": f(a[K_SG][u"W1"], ht[u"W1"]), u"XZ1-7": f(a[K_NN], ht[u"W1"]),
            u"XZ1-8": u"%d 組(60 組のうち)" % zero_docs_og(rec)}[key]


def expected_cells(c):
    out = collections.OrderedDict()
    for k, (ok, way) in judge(c.rec).items():
        out[k] = (cell_text(c.rec, k), u"当たり" if ok else u"外れ")
    return out


def xz13_note(rec):
    u"""XZ1-3 の外れ方の行(2 つの条件のどちらが外か)。両方内なら None。"""
    a = rec[K60]
    S = a[K_ST]
    diff = S[u"HT"][u"W1"] - S[u"O"][u"W1"]
    new = new_w1_of(a)
    a_ok, b_ok = diff >= 300, new <= 50
    if a_ok and b_ok:
        return None
    if not a_ok and not b_ok:
        return u"XZ1-3 は、2 つの条件の両方が外(差 %d は 300 に届かず、新しい W1 %d は 50 を超えた)。" % (diff, new)
    if not a_ok:
        return u"XZ1-3 は、差の側(差 %d は 300 に届かない)が外で、新しい W1 の側(%d)は予測の内。" % (diff, new)
    return u"XZ1-3 は、新しい W1 の側(%d は 50 を超えた)が外で、差の側(差 %d)は予測の内。" % (new, diff)


def miss_ids(j):
    return [k for k in IDS if not j[k][0]]


DECISION_LINE = u"封 §6 の決め"
MARK_RE = re.compile(u"\\(([a-z]{1,4})\\)")


def sec5_decision_problems(sec5, cond, s6):
    u"""封 §6(XZ1-1 と XZ1-2 が両方当たりなら次の便の候補 (i)(ii) を示す。どちらかが外れたら示さず、残った W1 と段の間の移りを書いて人間に返す)と文書 §5 が合う。"""
    out = []
    p5 = plain(sec5)
    lines = [ln for ln in p5.splitlines() if ln.strip()]
    idx = [i for i, ln in enumerate(lines) if DECISION_LINE in ln]
    if len(idx) != 1 or idx[0] != len(lines) - 1:
        return [u"§5 に「封 §6 の決め」の行が最後の行として 1 つでない"]
    last = lines[-1]
    marks = MARK_RE.findall(p5)
    shown = bool(marks)
    if cond != shown:
        out.append(u"封 §6 の決め(XZ1-1 と XZ1-2 が両方当たりなら次の便の候補を示す・どちらかが外れたら示さない)と文書 §5 が合わない")
    if cond:
        i6 = s6.index(u"(i) ")
        seg = s6[i6:s6.index(u"\n", i6)].strip()
        if marks != [u"i", u"ii"]:
            out.append(u"§5 の次の便の候補の見出しが (i)(ii) の 2 つだけでない: %s" % u",".join(marks))
        if seg not in p5:
            out.append(u"§5 の次の便の候補 (i)(ii) が封 §6 の字と違う")
        if p5.count(seg) != 1 or not last.endswith(seg):
            out.append(u"§5 の候補 (i)(ii) の後ろに別の字が在るか、(i)(ii) が 1 つでない")
        if u"0 USD。別の封が先" not in last or u"有料。別の封と、払う前の知らせが先" not in last or u"両方当たりなので示す" not in last:
            out.append(u"§5 の (i) の「0 USD。別の封が先」・(ii) の「有料。別の封と、払う前の知らせが先」・「両方当たりなので示す」が落ちている")
        if last.find(u"(i) ") < 0 or last.find(u"(i) ") > last.find(u"(ii) ") or last.count(u"(i) ") != 1 or last.count(u"(ii) ") != 1:
            out.append(u"§5 の (i)(ii) の順・数が違う")
    else:
        if u"残った W1" not in last or u"人間に返す" not in last:
            out.append(u"外れたのに、残った W1 の数と段の間の移りを書いて人間に返す道が §5 に無い")
    return out


def verdict_problems(c):
    rec = c.rec
    j = judge(rec)
    want = expected_cells(c)
    out = []
    rows = {}
    for ln in c.doc.splitlines():
        m = re.match(r"^\| (XZ1-\d)(?:\(主\))? \|(.*)\|$", ln)
        if m:
            rows[m.group(1)] = [x.strip() for x in m.group(2).split(u"|")]
    if sorted(rows) != sorted(j):
        return [u"文書 §1 の表の行が XZ1-1〜XZ1-8 でない"]
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
    for k in (u"XZ1-1", u"XZ1-2"):
        if not re.search(r"^\| %s\(主\) \|" % k, c.doc, re.M):
            out.append(u"%s の行に「(主)」が無い(封 §4 の主の読み)" % k)
    for k in IDS[2:]:
        if re.search(r"^\| %s\(主\) \|" % k, c.doc, re.M):
            out.append(u"%s の行に「(主)」が付いている(封 §4 の主は XZ1-1・XZ1-2)" % k)
    hits = sum(1 for v in j.values() if v[0])
    if u"- 当たり %d・外れ %d。" % (hits, len(j) - hits) not in c.doc.splitlines():
        out.append(u"文書の件数の行が決め直した件数と違う")
    head = plain(c.doc.split(u"## §1")[0])
    miss = miss_ids(j)
    if u"判定した %d 本は 当たり %d・外れ %d(%s が外れ)。" % (len(j), hits, len(j) - hits, u"・".join(miss)) not in head:
        out.append(u"文書の頭の件数・外れた予測の名が決め直した値と違う")
    if miss and u"予測の %d 本(%s)は外れ。" % (len(miss), u"・".join(miss)) not in head:
        out.append(u"外れた予測の言い切りが文書の頭に無い(%s)" % u"・".join(miss))
    mains = [k for k in miss if k in (u"XZ1-1", u"XZ1-2")]
    if mains:
        if u"主の予測の" not in head:
            out.append(u"外れた主の予測の言い切りが文書の頭に無い(%s)" % u"・".join(mains))
    elif re.search(u"主の予測の[^。]*は外れ", head):
        out.append(u"主の予測は両方当たりなのに文書の頭が外れと書いている")
    if not miss and re.search(u"予測の[^。]*本[^。]*は外れ", head):
        out.append(u"外れが無いのに文書の頭が外れと書いている")
    sec1, sec5 = section(c.doc, u"## §1 ", u"## §2 "), section(c.doc, u"## §5 ", None)
    sus = suspects(c)
    if any(sus):
        out.append(u"封 §4 の「先に自分の欠陥を疑う」旗が立っている: %s" % (sus,))
    line = [ln for ln in sec1.splitlines() if u"「先に自分の欠陥を疑う」旗 4 つ" in ln]
    if len(line) != 1 or u"(段 OG の W1 が 60 組の全部で 0・段 G の S が fact の 30% を超えた・段 OG の S が fact の 30% を超えた・番号の列を使った fact が 60 組で 0)は、どれも立っていない。" not in line[0]:
        out.append(u"文書 §1 の自己点検の言い切り(4 つの旗・どれも立っていない)が封の字・記録と合わない")
    note = xz13_note(rec)
    if note is not None and (u"- " + note) not in sec1.splitlines():
        out.append(u"XZ1-3 の外れ方の行が記録から組んだ字と違う")
    if note is None and u"XZ1-3 は、" in sec1:
        out.append(u"XZ1-3 は当たりなのに外れ方の行が在る")
    cond = j[u"XZ1-1"][0] and j[u"XZ1-2"][0]
    s6 = section(c.seal, u"## §6 ", u"## §7 ")
    out.extend(sec5_decision_problems(sec5, cond, s6))
    # 判定の表に 3 組・63 組の数が混ざらない(60 組の数だけ)
    only_other = set()
    for key in (K3, K63):
        ints_in(rec[key], only_other)
    only60 = set()
    ints_in(rec[K60], only60)
    ints_in(rec[PRED_KEY], only60)
    mixed = [t for ln in rows for t in doc_number_tokens(u" ".join(rows[ln])) if t in only_other and t not in only60 and t not in STRUCTURAL]
    if mixed:
        out.append(u"判定の表に 3 組・63 組だけの数が混ざっている: %s" % u",".join(mixed))
    return out


# ======================================================================================================
# d 文書の数・主な主張の文(§3 以外の全部の行を記録と字から組み直す)
def doc_rates(d60, st):
    u"""60 組の組ごとの段 st の U の率の最小・中央・最大・しきい値ごとの組の数(分数で)。"""
    fr = sorted(Fraction(d[K_ST][st][u"U"], d[K_FACTS]) for d in d60 if d[K_FACTS] > 0)
    n = len(fr)
    mid = fr[n // 2] if n % 2 else (fr[n // 2 - 1] + fr[n // 2]) / 2
    cnt = [sum(1 for d in d60 if d[K_FACTS] > 0 and 100 * d[K_ST][st][u"U"] >= t * d[K_FACTS]) for t in THRESHOLDS]
    return fr[0], mid, fr[-1], cnt


def w1_docs(d60, st):
    u"""段 st の W1: 0 の組・1 つ以上の組・1 組の中の最大・多い順の 5 組の合計・10 組の合計。"""
    v = sorted(d[K_ST][st][u"W1"] for d in d60)
    return v.count(0), sum(1 for x in v if x > 0), max(v), sum(v[-5:]), sum(v[-10:])


def stat_values(rec):
    d60, _ = split_docs(rec)
    return collections.OrderedDict([
        (u"og_rates", doc_rates(d60, u"OG")), (u"ht_rates", doc_rates(d60, u"HT")), (u"og_w1", w1_docs(d60, u"OG")), (u"ht_w1", w1_docs(d60, u"HT")),
        (u"og_more", sum(1 for d in d60 if d[K_ST][u"OG"][u"W1"] > d[K_ST][u"HT"][u"W1"])), (u"o_more", sum(1 for d in d60 if d[K_ST][u"O"][u"W1"] > d[K_ST][u"HT"][u"W1"])),
        (u"w5", sum(1 for d in d60 if 100 * d[K_ST][u"OG"][u"W1"] >= 5 * d[K_FACTS])), (u"w1p", sum(1 for d in d60 if 100 * d[K_ST][u"OG"][u"W1"] >= d[K_FACTS])),
        (u"s_docs", sum(1 for d in d60 if d[K_ST][u"OG"][u"S"] > 0)), (u"s_top5", sum(sorted(d[K_ST][u"OG"][u"S"] for d in d60)[-5:])),
        (u"stop_u_docs", sum(1 for d in d60 if d[K_SOG][u"U"] > 0)), (u"numcol_docs", sum(1 for d in d60 if d[K_NUMCOL] > 0))])


def tbl_row(label, cl, den, pct_keys):
    cells = []
    for k in CLS_S:
        if k == u"S" and k not in cl:
            cells.append(u"―")
        else:
            cells.append(u"%d(%s%%)" % (cl[k], pct(cl[k], den)) if k in pct_keys else u"%d" % cl[k])
    return u"| %s | %s |" % (label, u" | ".join(cells))


def sec3_text(c):
    return section(c.doc, u"## §3 ", u"## §4 ")


def render_doc(c):
    u"""記録(と字で留めた文)から、文書の §3 以外の全部の行を組み直す。§3 は ``sec3``(文書の字。sec3_problems が見る)を差し込む。"""
    rec = c.rec
    sec3 = sec3_text(c)
    a, b, t = rec[K60], rec[K3], rec[K63]
    S = a[K_ST]
    D = a[K_FACTS]
    ht, o, g, og = S[u"HT"], S[u"O"], S[u"G"], S[u"OG"]
    mat = a[K_MAT]
    sg, sog = a[K_SG], a[K_SOG]
    m = rec[u"材料"]
    st = stat_values(rec)
    j = judge(rec)
    hits = sum(1 for v in j.values() if v[0])
    miss = miss_ids(j)
    through, through_ht = og[u"U"] + og[u"W1"], ht[u"U"] + ht[u"W1"]
    new_w1 = new_w1_of(a)
    lo, mid, hi, cnt = st[u"og_rates"]
    hlo, hmid, hhi, hcnt = st[u"ht_rates"]
    z, ge1, mx, top5, top10 = st[u"og_w1"]
    hz, hge1, hmx, htop5, htop10 = st[u"ht_w1"]
    attr = a[K_ATTR]
    ax = lambda k: attr[u"違う属性 " + k]
    sec1_note3 = xz13_note(rec)
    cells = expected_cells(c)
    pred = collections.OrderedDict([
        (u"XZ1-1", u"段 OG の類 W1 は fact の 1.0% 以下"), (u"XZ1-2", u"段 OG の類 U は fact の 72.0% 以上"),
        (u"XZ1-3", u"段 O の W1 は段 HT の W1 より 300 以上少なく、段 HT で W1 でも W2 でもなかった fact が段 O で W1 になった数は 50 以下"),
        (u"XZ1-4", u"段 O の U は段 HT の U より 400 以上多い"), (u"XZ1-5", u"段 G が止めた段 HT の U は、fact の 1.0% 以上 8.0% 以下"),
        (u"XZ1-6", u"段 G が止めた段 HT の W1 は、段 HT の W1 の 50% 以上"), (u"XZ1-7", u"段 HT の W1 のうち「番号だけの違い」は 10% 以上 45% 以下"),
        (u"XZ1-8", u"段 OG の W1 が 0 の組は 20 組以上")])
    L = []
    w = L.append
    w(u"# 結果: 便 XZ1 ― 前の年の下書きが黙って違う属性を付ける fact を、行の順で番号を振り直す規則と、表の頭の字が前の年と違えば止める守りで、どれだけ直せ、どれだけ止められ、正しい fact をどれだけ巻き添えにしたか ― 2026-11-22")
    w(u"")
    w(u"封 `%s`(commit %s)。script `%s` と封の門 `%s` は commit %s(独立監査 REVISE 6 回 → 直し → GO。REVISE はどれも門の穴で、script は 1 回目から変えていない)。"
      u"記録 `%s` は commit %s(独立監査 GO。監査の席が script の関数を使わない別の実装で %d 組の全部を数え直し、記録と一致した)。"
      u"**0 USD・LLM の席は呼んでいない・通信していない。** engine は 0 行。書類は今年の側も前の年の側も置き場に在ったもの(新しく取っていない。便 XZ0 と同じ %d 組)。" % (
          SEAL_REL, SEAL_COMMIT_SHORT, SCRIPT_REL, SEAL_GATE_REL, SCRIPT_COMMIT_SHORT, RECORD_REL, RECORD_COMMIT_SHORT, m[u"組の数"], m[u"組の数"]))
    w(u"")
    w(u"この文書の §1・§2 の数は全部、記録から 1 つずつ読んだもの(結果の門が、記録の数と字で同じことを見る)。§3 は記録に欄の無い読みで、出どころを書く。")
    w(u"")
    w(u"**先に負けと限界を書く。**")
    w(u"")
    w(u"- **予測の %d 本(%s)は外れ。** 行の順で番号を振り直す規則(段 O)は、黙って違う fact(W1)を %d しか減らさず(予測は 300 以上)、"
      u"**段 HT では W1 でも W2 でもなかった fact %d を新しく W1 にした**(予測は 50 以下)。規則は直すだけでなく、黙って違う fact を自分で作る。" % (
          len(miss), u"・".join(miss), ht[u"W1"] - o[u"W1"], new_w1))
    w(u"- **規則と守りを足しても、黙って違う fact は残る。** 段 OG の W1 は %s。通した fact(U + W1)%d を分母にすると %s%%。**W1 が 0 になったのではない。** "
      u"60 組のうち W1 が 1 つ以上残った組は %d で、%d 組では段 OG の W1 が段 HT の W1 より多い。" % (f(og[u"W1"], D), through, pct(og[u"W1"], through), ge1, st[u"og_more"]))
    w(u"- **守りは正しい fact も止める。** 段 OG が止めた fact(S)は %d で、そのうち %d(%s%%)は段 O で正しかった(類 U)。止めた fact の半分近くは、止めなくてよかった。" % (
        og[u"S"], sog[u"U"], pct(sog[u"U"], og[u"S"])))
    w(u"- **規則と守りは、並びの頭の 3 組を見て作った(封 §0 の申告)。** 予測は残りの 60 組だけで判定した。3 組の数は訓練で、当たって当然(3 組の段 OG の W1 は %d)。"
      u"60 組では 0 ではなかった。**60 組の数が本当の数。** 60 組も同じ 63 組の引きの中で、無作為ではない(業種はほぼ一般商工業・有報だけ・年は 1 年の差だけ)。" % b[K_ST][u"OG"][u"W1"])
    w(u"- 判定した %d 本は 当たり %d・外れ %d(%s が外れ)。予測は便 XZ0 の 63 組の類の数と、頭の 3 組の fact を見てから立てた。盲検ではない。" % (len(j), hits, len(j) - hits, u"・".join(miss)))
    w(u"- 番号つきのメンバーの形は `No`・`Row` で始まる 2 通りだけ。ほかの付け方の番号は拾わない。")
    w(u"- 段 O の行の番号は「今年の表の行の順が、今年の正しい番号の順」という仮定に立つ。仮定が破れる表では W1 を新しく作る(上の %d)。" % new_w1)
    w(u"- 表の頭の印は、最初に fact を持つ行より前の行の字だけ。頭の字が同じまま列がずれた表・頭の行に fact が在る表は止められない。数字を除くので、年・期の数字だけが変わった頭は同じと見る。")
    w(u"- **W1 も S の中身も、答えを知らないと見えない。** 使う人に見えるのは「通した」「止めた」「候補が複数」「候補なし」の 4 つだけ(§2)。")
    w(u"- 便 XZ0 の限界はそのまま: fact の置き場は答えから取っている・どちらの年も専用の道具が組んだ後の字・文脈は名で比べ定義は見ない・`sign`・`format`・nil・値・数でない fact は測らない・前の年の XBRL が在る会社だけ。")
    w(u"- **「XBRL を作れる」「EDINET の検査に通る」「専用の道具が要らない」「AI が書ける」「黙って違う fact は無い」は、この便からは言えない。**")
    w(u"")
    w(u"## §1 予測の当たり外れ(司令塔。盲検ではない)")
    w(u"")
    w(u"封 §4 の字の境と記録から、結果の門が XZ1-1〜XZ1-8 の当たり外れを決め直した(この表と同じ)。封も予測も結果を見てから書き換えていない。判定は丸める前の数でした。"
      u"分母は、断らないかぎり 60 組(規則を作るのに見ていない組)の今年の側の、行の中の数の fact %d(行の字が空の fact X を含む)。" % D)
    w(u"")
    w(u"| # | 予測(封の字の要約) | 実測(記録) | 判定 |")
    w(u"|---|---|---|---|")
    for k in IDS:
        w(u"| %s%s | %s | %s | %s |" % (k, u"(主)" if k in (u"XZ1-1", u"XZ1-2") else u"", pred[k], cells[k][0], cells[k][1]))
    w(u"")
    w(u"- 当たり %d・外れ %d。" % (hits, len(j) - hits))
    if sec1_note3 is not None:
        w(u"- " + sec1_note3)
    w(u"- XZ1-1 は、分母を fact の全部にした率(%s%%)で判定した(封 §4 の字)。分母を「通した」にすると %s%%(丸める前は %s%%)。" % (pct(og[u"W1"], D), pct(og[u"W1"], through), pct2(og[u"W1"], through)))
    w(u"- 封 §4 の「先に自分の欠陥を疑う」旗 4 つ(段 OG の W1 が 60 組の全部で 0・段 G の S が fact の 30% を超えた・段 OG の S が fact の 30% を超えた・番号の列を使った fact が 60 組で 0)は、"
      u"どれも立っていない。段 HT の組ごとの類の数は便 XZ0 の記録と 63 組の全部で同じ(違えば script が止まる)。")
    w(u"")
    w(u"## §2 数(記録)")
    w(u"")
    w(u"材料: 今年の側 %d 本・組 %d・除いた今年の書類 %d(便 XZ0 と同じ)。**60 組**(規則を作るのに見ていない組。予測の判定はここだけ)の行の中の数の fact は %d。**3 組**(訓練)は %d。63 組の合計は %d。" % (
        m[u"今年の側の書類の本数"], m[u"組の数"], m[u"除いた今年の書類の数"], D, b[K_FACTS], t[K_FACTS]))
    w(u"")
    w(u"類の意味: X(行の字が空)・U(候補が 1 つで正しい)・A(候補が 2 つ以上で答えを含む)・W1(候補が 1 つで違う。黙って違う)・W2(候補が 2 つ以上で答えを含まない)・N(前の年に置き場が無い)・S(守りが止めた)。")
    w(u"")
    w(u"段の意味: 段 HT(便 XZ0 の下書きのまま)・段 O(行の順で番号を振り直す規則を足す)・段 G(段 HT に表の頭の字の守りを足す)・段 OG(規則と守りの両方)。")
    w(u"")
    w(u"60 組の段ごとの類(分母 %d):" % D)
    w(u"")
    w(u"| 段 | X | U | A | W1 | W2 | N | S |")
    w(u"|---|---|---|---|---|---|---|---|")
    w(tbl_row(u"段 HT", ht, D, (u"U", u"W1")))
    w(tbl_row(u"段 O", o, D, (u"U", u"W1")))
    w(tbl_row(u"段 G", g, D, (u"U", u"W1", u"S")))
    w(tbl_row(u"段 OG", og, D, (u"U", u"W1", u"S")))
    w(u"")
    w(u"**使う人に見える 4 区分(段 OG・60 組)**: 通した(U + W1)%d・止めた(S)%d・候補が複数(A + W2)%d・候補なし(N + X)%d。" % (through, og[u"S"], og[u"A"] + og[u"W2"], og[u"N"] + og[u"X"]))
    w(u"")
    w(u"- **誤りを通す率**: 通した %d のうち W1 は %d(%s%%)。fact の全部を分母にすると %s。段 HT では、通した %d のうち W1 は %d(%s%%)、fact の全部では %s%%。" % (
        through, og[u"W1"], pct(og[u"W1"], through), f(og[u"W1"], D), through_ht, ht[u"W1"], pct(ht[u"W1"], through_ht), pct(ht[u"W1"], D)))
    w(u"- **止めた fact の中身**: 段 OG が止めた %d は、段 O の類で U %d・W1 %d・W2 %d。止めたうち正しかった(U)のは %s%%。段 G が止めた %d は、段 HT の類で U %d・W1 %d・W2 %d。" % (
        og[u"S"], sog[u"U"], sog[u"W1"], sog[u"W2"], pct(sog[u"U"], og[u"S"]), g[u"S"], sg[u"U"], sg[u"W1"], sg[u"W2"]))
    w(u"")
    w(u"段 HT の類 → 段 O の類(60 組。行の順の規則が動かした fact):")
    w(u"")
    w(u"| 段 HT の類 | 段 O で U | A | W1 | W2 | N |")
    w(u"|---|---|---|---|---|---|")
    for c_ in (u"U", u"A", u"W1", u"W2", u"N"):
        w(u"| %s %d | %s |" % (c_, ht[c_], u" | ".join(u"%d" % mat[c_][k] for k in (u"U", u"A", u"W1", u"W2", u"N"))))
    w(u"")
    w(u"- 規則が直した fact: W1 → U が %d・N → U が %d。**規則が壊した fact: U → W1 が %d・N → W1 が %d(合わせて %d)**・U → A が %d・U → W2 が %d。" % (
        mat[u"W1"][u"U"], mat[u"N"][u"U"], mat[u"U"][u"W1"], mat[u"N"][u"W1"], new_w1, mat[u"U"][u"A"], mat[u"U"][u"W2"]))
    w(u"- 番号の列を使った fact は %d(60 組の全部の組に 1 つ以上在る)。" % a[K_NUMCOL])
    w(u"- 段 HT の W1 %d の、違う属性の組: `contextRef` だけ %d・`name` だけ %d・`name` と `contextRef` %d・`name` と `unitRef` %d・3 つとも %d・`unitRef` だけ %d・`contextRef` と `unitRef` %d。"
      u"`contextRef` が違う W1 のうち「番号だけの違い」(番号つきのメンバーの番号だけが違う)は %d(W1 の %s%%)。" % (
          ht[u"W1"], ax(u"contextRef"), ax(u"name"), ax(u"name+contextRef"), ax(u"name+unitRef"), ax(u"name+contextRef+unitRef"), ax(u"unitRef"), ax(u"contextRef+unitRef"), a[K_NN], pct(a[K_NN], ht[u"W1"])))
    w(u"- 組ごとの段 OG の U の率(60 組): 最小 %s%%・中央 %s%%・最大 %s%%。70%% 以上が %d 組・80%% 以上が %d 組・90%% 以上が %d 組・95%% 以上が %d 組。段 HT では最小 %s%%・中央 %s%%・最大 %s%%。" % (
        fpct(lo), fpct(mid), fpct(hi), cnt[0], cnt[1], cnt[2], cnt[3], fpct(hlo), fpct(hmid), fpct(hhi)))
    w(u"- 組ごとの段 OG の W1: 0 の組が %d・1 つ以上の組が %d。1 組の中の最大は %d。多い順の 5 組で %d・10 組で %d(%d の 8 割を超える)。段 HT では W1 が 0 の組は %d・1 組の中の最大は %d。"
      u"**段 OG の W1 が段 HT の W1 より多い組が %d 組在る**(段 O の W1 が段 HT より多い組も %d 組)。W1 がその組の fact の 5%% 以上の組は %d・1%% 以上の組は %d。" % (
          z, ge1, mx, top5, top10, og[u"W1"], hz, hmx, st[u"og_more"], st[u"o_more"], st[u"w5"], st[u"w1p"]))
    w(u"- 組ごとの段 OG の S: 1 つ以上の組が %d。多い順の 5 組で %d。止めた U が 1 つ以上の組は %d。" % (st[u"s_docs"], st[u"s_top5"], st[u"stop_u_docs"]))
    w(u"")
    w(u"3 組(訓練。規則と守りを作るのに見た組。分母 %d)― **予測の判定には使わない**:" % b[K_FACTS])
    w(u"")
    w(u"| 段 | X | U | A | W1 | W2 | N | S |")
    w(u"|---|---|---|---|---|---|---|---|")
    w(tbl_row(u"段 HT", b[K_ST][u"HT"], b[K_FACTS], ()))
    w(tbl_row(u"段 OG", b[K_ST][u"OG"], b[K_FACTS], ()))
    w(u"")
    w(u"63 組の合計(分母 %d): 段 HT は U %d・W1 %d(便 XZ0 の記録と同じ)。段 OG は U %d・A %d・W1 %d・W2 %d・N %d・S %d・X %d。" % (
        t[K_FACTS], t[K_ST][u"HT"][u"U"], t[K_ST][u"HT"][u"W1"], t[K_ST][u"OG"][u"U"], t[K_ST][u"OG"][u"A"], t[K_ST][u"OG"][u"W1"], t[K_ST][u"OG"][u"W2"], t[K_ST][u"OG"][u"N"], t[K_ST][u"OG"][u"S"],
        t[K_ST][u"OG"][u"X"]))
    w(u"")
    L.extend(sec3.rstrip(u"\n").split(u"\n"))
    w(u"")
    w(u"## §4 実装で決めた所(封の字で 1 通りに決まらなかった所。監査 GO。2026-11-22 追記。封は書き換えていない)")
    w(u"")
    w(u"script の頭に列挙した。結果を左右しうるのは次の 3 つ:")
    w(u"")
    w(u"- **封 §0・§3 の「番号 4〜63 の 60 組」**: 組の番号は便 XZ0 の記録の番号で、除いた書類の番号は飛ぶ(63 組の通し番号ではない)。script は「番号 4 以上」と読んだ。"
      u"その 60 組の fact の合計は封 §3 の字の %d と同じ(違えば script が止まる)。**封の「4〜63」の字は、番号の上の端を取り違えた書き方だった**(封は書き換えない)。" % D)
    w(u"- **封 §2-1 の「2 つ目より後ろの部品」**: script は「`_` で切った 2 つ目以降(先頭の部品だけを除く)」と読んだ。「2 つ目を除いて 3 つ目から」の読みも字の上では成り立つ。その読みでの数は測っていない。")
    w(u"- **表の数えの `<table` の大文字小文字**: 表の番号は便 XZ0 の script の関数(大文字小文字を区別しない)で数える。封の門は、小文字だけに狭める変異で黙ったままだった。"
      u"訓練の 3 組には大文字の `<TABLE` は 0 件と監査の席が確かめた。60 組では確かめていない。")
    w(u"")
    w(u"ほかに: 類 S は候補が 1 つ以上在る fact(U・A・W1・W2)にだけ付く(X・N は止めない)・「最初に数の fact を持つ行」は空の欄の fact も数える・旗は記録に書くだけで script は止めない。記録は当たり外れを持たない。")
    w(u"")
    w(u"封の門は変異 %d 本で赤を確かめた。緑のまま残った変異は %d 本で、どれも同じ動きになる書き換え(同値)と監査の席が見た。" % (len(SG.MUTANTS), len(SG.SILENT_BY_DESIGN)))
    w(u"")
    w(u"## §5 この便から言えること・言えないこと・人間に示すこと")
    w(u"")
    w(u"- 言えること(封 §6 の字): 公開済みの 60 組(規則を作るのに見ていない組)で、前の年の下書きに行の順の規則と表の頭の守りを足すと、3 つの属性が 1 つに決まり正しかった fact は %s%%・"
      u"黙って違った fact は %s%%(通した fact を分母にすると %s%%)・止めた fact は %s%%(うち正しかったものは %s%%)だった。" % (
          pct(og[u"U"], D), pct(og[u"W1"], D), pct(og[u"W1"], through), pct(og[u"S"], D), pct(sog[u"U"], og[u"S"])))
    w(u"- 言えること: 規則と守りが無いとき(段 HT)の同じ 60 組は、正しかった fact %s%%・黙って違った fact %s%%。**黙って違う fact は %d から %d に減り、正しく決まる fact は %d から %d に減った。** "
      u"減らしたのは主に守り(段 G だけで W1 は %d)で、行の順の規則だけ(段 O)では W1 は %d。" % (pct(ht[u"U"], D), pct(ht[u"W1"], D), ht[u"W1"], og[u"W1"], ht[u"U"], og[u"U"], g[u"W1"], o[u"W1"]))
    w(u"- 言えないこと: 残った W1 %d を止める手・巻き添えを減らす手・ほかの年やほかの業種での率・原稿の字での率・どのセルが fact かを答えなしに決められるか・「XBRL を作れる」「専用の道具が要らない」「AI が書ける」。" % og[u"W1"])
    w(u"- 相手の問いへの、この便からの答え: 2 年目からの会社で、前の年の提出書類を下書きにし、行の順の規則と表の頭の守りを足すと、通した fact のうち黙って違うのは 100 個に 1 個ほどまで減る(足さないと 25 個に 1 個ほど)。"
      u"代わりに fact の 4% ほどを止め、その半分近くは正しかった。**0 にはなっていない**ので、通した fact も別の手段(値・定義)で確かめる段は要る。測ったのは道具が組んだ後の字どうしで、原稿からの率ではない。")
    s6 = section(c.seal, u"## §6 ", u"## §7 ")
    i6 = s6.index(u"(i) ")
    seg = s6[i6:s6.index(u"\n", i6)].strip()
    cond = j[u"XZ1-1"][0] and j[u"XZ1-2"][0]
    if cond:
        w(u"- **封 §6 の決め: XZ1-1 と XZ1-2 が両方当たりなら、次の便の候補を人間に示す。両方当たりなので示す**: " + seg)
    else:
        w(u"- **封 §6 の決め: XZ1-1 と XZ1-2 が両方当たりなら、次の便の候補を人間に示す。どちらかが外れたので、残った W1 の数と段の間の移りを書いて、作る側へ進む道を人間に返す。**")
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


def derived_numbers(c):
    u"""記録から導ける数(文書の §3 以外の数はこの内か字で留めた境の数)。"""
    rec = c.rec
    out = set()
    for k in GROUPS:
        ints_in(rec[k], out)
    ints_in(rec[PRED_KEY], out)
    ints_in(rec[FLAG_KEY], out)
    for k in GROUPS:
        den = rec[k][K_FACTS]
        for s in STAGES:
            for cl in CLS_S:
                if cl in rec[k][K_ST][s]:
                    out.add(pct(rec[k][K_ST][s][cl], den))
    a = rec[K60]
    S = a[K_ST]
    D = a[K_FACTS]
    ht, og = S[u"HT"], S[u"OG"]
    for key, vals in stat_values(rec).items():
        if isinstance(vals, tuple):
            for v in vals:
                if isinstance(v, Fraction):
                    out.add(fpct(v))
                elif isinstance(v, list):
                    out |= set(str(x) for x in v)
                else:
                    out.add(str(v))
        else:
            out.add(str(vals))
    out |= set([str(og[u"U"] + og[u"W1"]), str(ht[u"U"] + ht[u"W1"]), str(new_w1_of(a)), str(ht[u"W1"] - S[u"O"][u"W1"]), str(S[u"O"][u"U"] - ht[u"U"]),
                pct(og[u"W1"], og[u"U"] + og[u"W1"]), pct2(og[u"W1"], og[u"U"] + og[u"W1"]), pct(ht[u"W1"], ht[u"U"] + ht[u"W1"]), pct(a[K_NN], ht[u"W1"]), pct(a[K_SG][u"W1"], ht[u"W1"]),
                pct(a[K_SG][u"U"], D), pct(a[K_SOG][u"U"], og[u"S"]), pct(og[u"S"], D)])
    for d in rec[u"書類"][:0]:
        pass
    for k in (u"今年の側の書類の本数", u"組の数", u"除いた今年の書類の数"):
        out.add(str(rec[u"材料"][k]))
    out |= set(str(v) for v in (len(SG.MUTANTS), len(SG.SILENT_BY_DESIGN)))
    out |= set(DOC_COMMITS)
    out |= set(STRUCTURAL) | RESIDUAL_OK
    return out


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
    u"""文書の言い切りの向き(100 個に 1 個・25 個に 1 個・4% ほど・半分近く・8 割を超える・減った・主に守り・訓練は 0・60 組は 0 でない・4〜63 の端)が記録の数に合う。"""
    rec = c.rec
    a, b = rec[K60], rec[K3]
    S = a[K_ST]
    D = a[K_FACTS]
    ht, o, g, og = S[u"HT"], S[u"O"], S[u"G"], S[u"OG"]
    through, through_ht = og[u"U"] + og[u"W1"], ht[u"U"] + ht[u"W1"]
    sogu = a[K_SOG][u"U"]
    out = []
    if not (95 * og[u"W1"] <= through <= 105 * og[u"W1"]):
        out.append(u"文書の「100 個に 1 個ほど」が記録と合わない")
    if not (24 * ht[u"W1"] <= through_ht <= 26 * ht[u"W1"]):
        out.append(u"文書の「25 個に 1 個ほど」が記録と合わない")
    if not (35 * D <= 1000 * og[u"S"] <= 45 * D):
        out.append(u"文書の「fact の 4% ほどを止め」が記録と合わない")
    if not (40 * og[u"S"] <= 100 * sogu < 50 * og[u"S"]):
        out.append(u"文書の「その半分近くは正しかった」が記録と合わない(止めた fact のうち正しかったものが 40% 以上 50% 未満でない)")
    if not (st_top10(rec) * 10 > 8 * og[u"W1"]):
        out.append(u"文書の「474 の 8 割を超える」が記録と合わない")
    if not (ht[u"W1"] > og[u"W1"] > 0 and ht[u"U"] > og[u"U"]):
        out.append(u"文書の「黙って違う fact は減り、正しく決まる fact も減った・0 になったのではない」が記録と合わない")
    if not (g[u"W1"] < o[u"W1"] < ht[u"W1"] and ht[u"W1"] - g[u"W1"] > ht[u"W1"] - o[u"W1"]):
        out.append(u"文書の「減らしたのは主に守り」が記録と合わない")
    if not (new_w1_of(a) > 50 and a[K_MAT][u"W1"][u"U"] + a[K_MAT][u"N"][u"U"] > 0 and ht[u"W1"] - o[u"W1"] < 300):
        out.append(u"文書の「規則は直すだけでなく、黙って違う fact を自分で作る」が記録と合わない")
    if not (b[K_ST][u"OG"][u"W1"] == 0 and og[u"W1"] > 0):
        out.append(u"文書の「3 組の段 OG の W1 は 0・60 組では 0 ではなかった」が記録と合わない")
    if stat_values(rec)[u"numcol_docs"] != N60:
        out.append(u"文書の「番号の列を使った fact は 60 組の全部の組に 1 つ以上在る」が記録と合わない")
    if not (max(d[u"番号"] for d in rec[u"書類"]) > 63 and min(d[u"番号"] for d in split_docs(rec)[0]) == SEEN_MAX + 1):
        out.append(u"文書の「封の 4〜63 の字は番号の上の端の取り違え(番号は 63 を超える)」が記録と合わない")
    if not (g[u"S"] > og[u"S"] - og[u"S"] and g[u"U"] < ht[u"U"] and o[u"U"] > ht[u"U"]):
        out.append(u"段 G が止めると U が減る・段 O は U が増える、が記録と合わない")
    return out


def st_top10(rec):
    return stat_values(rec)[u"og_w1"][4]


def sec3_problems(c):
    u"""§3 は記録に欄の無い読み(監査の席の数え直し)の節。数は記録に縛らず、見出し・字で留めた数の並び・記録の数との足し算・§3 の外にその数が無い・「測っていない」を縛る。"""
    s = sec3_text(c)
    out = []
    if u"記録に欄の無い読み" not in s.splitlines()[0]:
        out.append(u"§3 の見出しが「記録に欄の無い読み」でない")
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
    # 記録にも在る数との足し算(§3 の数どうしと、記録の 114・474・1107 の和)
    a = c.rec[K60]
    mat = a[K_MAT]
    try:
        k1, k2, k3 = [SEC3_LINES[i][0] for i in range(3)]
        t1, t2, t3 = toks[k1], toks[k2], toks[k3]
        n114, n45, n69, n12, n3a, n76, n1x, n97, n3b, n14 = [int(x) for x in t1]
        n474, n342, n132 = [int(x) for x in t2]
        n1107, n1008, n99, _ = [int(x) for x in t3]
        if (n114, n45, n69) != (new_w1_of(a), mat[u"U"][u"W1"], mat[u"N"][u"W1"]) or n97 + n3b + n14 != n114 or not (0 < n3a <= n12 <= N60 and n76 <= n114):
            out.append(u"§3 の 1 つ目(114 = 97 + 3 + 14・記録の 114・45・69)が記録と合わない")
        if n474 != a[K_ST][u"OG"][u"W1"] or n342 + n132 != n474 or not (Fraction(65, 100) <= Fraction(n342, n474) <= Fraction(75, 100)):
            out.append(u"§3 の 2 つ目(474 = 342 + 132・「7 割ほど」)が記録と合わない")
        if n1107 != a[K_SOG][u"U"] or n1008 + n99 != n1107:
            out.append(u"§3 の 3 つ目(1107 = 1008 + 99・記録の 1107)が記録と合わない")
    except (KeyError, ValueError, IndexError):
        out.append(u"§3 の数が読めない")
    rest = outside_sec3(c)
    rt = set(t.replace(u",", u"") for ln in rest.splitlines() for t in doc_number_tokens(ln))
    for n in SEC3_ONLY:
        if n in rt:
            out.append(u"記録に欄の無い数 %s が §3 の外に出ている" % n)
    if u"7 割" in rest or u"頭の字が同じまま文脈がずれた所" in rest:
        out.append(u"§3 の「7 割ほど」が §3 の外で主張として出ている")
    if u"頭の語そのものが 2 つの年で変わった表" in rest:
        out.append(u"§3 の「頭の語が変わった表が大半」が §3 の外で主張として出ている")
    return out


def affirm_problems(c):
    u"""「作れる」「専用の道具が要らない」「人が書ける」「AI が書ける」「検査に通る」「黙って違う fact は無い」「0 になった」は、言えないことの引用(「…」の中)・否定の中にしか無い。引用の在る行には「言えない」か「読まない」が在る。"""
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
    if len([ln for ln in sec7.splitlines() if ln.startswith(u"- ")]) != len(LIMIT_FRAGS):
        out.append(u"封 §7 の限界の行の数が門の限界の断片の組の数と違う")
    hlines = head.splitlines()
    for i, frags in enumerate(LIMIT_FRAGS, 1):
        for p in frags:
            if p not in head:
                out.append(u"封 §7 の限界の %d 本目の断片が文書の頭に無い: %s" % (i, p[:20]))
        if not any(all(p in ln for p in frags) for ln in hlines):
            out.append(u"封 §7 の限界の %d 本目の断片が文書の頭の 1 つの行に揃っていない" % i)
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
    u"""文書が書く 3 つの commit が実の履歴と合う: 封は 2079af62・script と封の門は d6a18d51・記録は ca34473a。commit の message が文書の言う「REVISE 6 回」「独立監査 GO」を書いている。"""
    out = []
    for rel, want in HISTORY.items():
        r = subprocess.run(["git", "-C", root, "log", "--format=%H", "--reverse", "--", PREFIX + rel], stdout=subprocess.PIPE, universal_newlines=True)
        got = [x for x in r.stdout.split() if x]
        if len(got) != len(want) or any(not g.startswith(w) for g, w in zip(got, want)):
            out.append(u"%s の履歴が文書の書く commit %s と違う" % (rel, u"・".join(want)))
    for short, words in ((SCRIPT_COMMIT_SHORT, (u"REVISE 6 回", u"同値 6 本", u"変異 160 本")), (RECORD_COMMIT_SHORT, (u"独立監査 GO", u"全 63 組を別の実装で数え直して一致"))):
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
(変異を実行する前に書いた予測。右 = 赤になるべき検査。「整合」= 書類ごとの数から集計・予測・旗を作り直し、recount は緑のまま当たり外れ・向きだけが変わる)
固定の変異 F1〜: 記録・封・文書の 1 か所を替える。右の検査が赤。
F1  記録の sha256 の写しを違う値に                                                       -> sha
F2  記録の「この script の sha256」を 1 字替える                                         -> sha
F3  記録の限界の欄の 1 行を消す                                                          -> sha
F4  記録の封の commit の欄を 1 字替える                                                  -> sha
F5  便 XZ0 の記録の sha256 の写しを違う値に                                              -> sha
F6  記録の step の欄を 1 字替える                                                        -> sha
F7  記録の 材料 の sha の 1 字を替える(便 XZ0 の記録と違う)                                -> recount
F8  記録の engine の指紋を 1 字替える                                                    -> recount
F9  書類 10 の段 HT の U を 1 増やす(集計は直さない)                                     -> recount
F10 集計 60 組の段 HT の W1 を 1 増やす(書類ごとは直さない)                               -> recount
F11 書類 10 の段 OG の U を 1 減らす                                                      -> recount
F12 書類 10 の移りの表の [U][U] から [U][W1] へ 1 移す(行の和は同じ・列の和が合わない)         -> recount
F13 書類 10 の段 G が止めた U を 1 増やす(段 G の S・U は直さない)                          -> recount
F14 書類 4 の番号の列を使った fact を 1 増やす(集計は直さない)                              -> recount
F15 書類 4 の違う属性の contextRef だけを 1 減らす                                         -> recount
F16 書類 4 の番号だけの違いを contextRef が違う W1 より多くする                             -> recount
F17 材料の組の数 63 → 64                                                                 -> recount
F18 予測の欄 XZ1-2 の fact を 1 増やす                                                    -> recount
F19 先に疑う旗の 1 つを True にする                                                       -> recount
F20 集計 60 組と集計 3 組を入れ替える(60 組と 3 組の取り違え)                               -> recount
F21 便 XZ0 の記録の書類 10 の束 3・段 HT の U を 1 増やす(段 HT が便 XZ0 と違う)              -> recount
F22 書類の番号 3 を 99 にする(番号の並び・60 組と 3 組の分けが崩れる)                                     -> recount
F23 記録に docid の欄を足す                                                               -> clean
F24 記録に EDINET コードの形の字を足す                                                     -> clean
F25 記録に日付の形の字を足す                                                               -> clean
F26 封の写しから XZ1-1 の境の字を消す                                                      -> bound
F27 封の写しから §6 の「W1 の率は…2 通りで書く」を消す                                     -> bound
F28 封の写しから §7 の限界の 1 本を消す                                                    -> bound
F29 封の写しから §0 の「並びの頭の 3 組」を消す                                            -> bound
整合の変異 C1〜: recount は緑のまま、文書が合わなくなる(verdict・lines)。
C1  XZ1-1 を外れにする(段 O・段 OG の U を W1 へ移す)                                      -> verdict
C2  XZ1-2 を外れにする(U を A へ移す)                                                     -> verdict
C3  XZ1-3 を当たりにする(N → W1・U → W1 を戻す)                                           -> verdict
C4  XZ1-3 の差の側だけを外にする(新しい W1 は 50 以下・差は 300 未満)                       -> verdict(「両方が外」が違う)
C5  XZ1-3 の新しい W1 の側だけを外にする(差は 300 以上)                                   -> verdict
C6  XZ1-4 を外れにする(N → U を A へ)                                                     -> verdict
C7  XZ1-5 を上の外にする(止めた U が 8% 超)                                                -> verdict
C8  XZ1-5 を下の外にする(止めた U が 0)                                                    -> verdict
C9  XZ1-6 を外れにする(止めた W1 が 0)                                                     -> verdict
C10 XZ1-7 を上の外にする(番号だけの違いが 45% 超)                                          -> verdict
C11 XZ1-8 を外れにする(W1 が 0 の組を 0 に)                                                 -> verdict
C12 旗: 段 OG の W1 が 60 組の全部で 0                                                     -> verdict
C13 旗: 段 G の S が 30% 超                                                                -> verdict
C14 旗: 段 OG の S が 30% 超                                                               -> verdict
C15 旗: 番号の列を使った fact が 0                                                         -> verdict
C16 XZ1-1 だけを外れにして、文書の「示す」(§5 の候補 (i)(ii))と合わなくする                  -> verdict(封 §6 の決め)
C17 整合: 止めた fact の半分近く、を崩す(正しかった止めた fact を 7 割にする)                  -> sanity
C18 整合: 「100 個に 1 個ほど」を崩す(段 OG の W1 を 3 倍にする)                              -> sanity
文書の固定の変異 D1〜: 右の検査が赤。
D1  判定の「外れ」「当たり」を行ごとに入れ替える(8 行の全部。掃き)                              -> verdict
D2  頭の「予測の 1 本(XZ1-3)は外れ」を「(XZ1-1)」に                                       -> verdict・lines
D3  頭の「当たり 7・外れ 1」を「当たり 6・外れ 2」に                                         -> verdict・lines
D4  「新しく W1 にした」を「新しく U にした」に                                              -> lines
D5  「W1 が 0 になったのではない」を「W1 が 0 になった」に                                   -> affirm・lines
D6  「止めた fact の半分近くは、止めなくてよかった」を「1 割ほどは」に                          -> lines
D7  「60 組の数が本当の数」を「3 組の数が本当の数」に                                         -> lines
D8  「100 個に 1 個ほど」を「10 個に 1 個ほど」に                                            -> lines・sanity
D9  「0 にはなっていない」を「0 になった」に                                                 -> affirm・lines
D10 §5 に「(iii)」の候補を足す                                                              -> verdict
D11 §5 の (i) の「0 USD。別の封が先」を消す                                                 -> verdict
D12 §5 の (ii) の「有料。別の封と、払う前の知らせが先」を消す                                  -> verdict
D13 §5 の最後の行の後ろに候補の見出しのない案の 1 行を足す                                    -> verdict
D14 §5 の「両方当たりなので示す」を消す                                                     -> verdict
D15 §5 の最後の行の前に「- (c) …」を足す                                                    -> verdict
D16 頭の限界の 1 本を消す(6 本の全部。掃き)                                                   -> head
D17 頭の限界の断片を 1 つ消す(全部の断片。掃き)                                               -> head
D18 引用の外に「XBRL を作れる。」「人が書ける。」「AI が書ける。」「専用の道具が要らない。」「EDINET の検査に通る。」「黙って違う fact は無い。」「W1 は 0 になった。」を足す(掃き)    -> affirm
D19 引用の行から「言えない」「読まない」を全部消す                                             -> affirm
D20 文書に「保証」を足す・docID の形を足す・commit の字を替える・知らない commit の字を足す      -> forbidden・commits
D21 §3 の見出しの「記録に欄の無い読み」を消す・§3 の数を替える・§3 の中の数を 1 つ増やす・§3 の外に §3 の数を足す(全部の §3 の数。掃き)    -> sec3
D22 §3 の中の語を替える(「測っていない」を消す・「7 割ほど」を「3 割ほど」に・「大半」を「少数」に)  -> sec3
掃き(SWEEPS。文書の全部に 1 か所ずつ当てる。1 つでも黙れば報告):
W1  文書の全部の数(§3 を含む)を、(a) 1 増やす (b) 同じ文書の別の所の数に替える (c) §3 の数に替える          -> 全部赤(lines か sec3)
W2  向きの語(以上/以下・多い/少ない・減る/増える・高い/低い・超える/満たない など)を、出た所ごとに反対に -> 全部赤
W3  「60 組」「3 組」「63 組」の数を互いに取り違える・61100/48612/64534/3434/2078/50537/2494 を互いに取り違える  -> 全部赤
W4  §3 の数を §2 に 1 行として足す(全部)                                                    -> 全部赤(numbers・sec3)
W5  表の 1 セルを、同じ表の別の行の同じ列のセルへ替える(§1 の表・§2 の表の全部のセル)           -> 全部赤
W6  §3 の外の全部の行を 1 行ずつ消す・全部の文を 1 つずつ消す・「・」でつないだ節を 1 つずつ消す        -> 全部赤
W7  記録の全部の整数の葉(集計 3 つ・予測・旗・書類 4 つ分)を 1 増やす・旗を反転する                     -> 全部赤(recount)
W8  §3 の文を 1 つずつ消す・向きの語を反対に                                                   -> 黙る所が在りうる(§3 の中の括弧の例示と、SEC3_PHRASES に無い言い回し)。黙った所は報告
予測の自己点検: 黙るとすれば W8(§3 は形で縛るため)と、W5 で「同じ文字列のセル」に替わる場合(スキップ)。W1〜W7 に黙りは無いと予測する。
(実行後の追記。予測は書き換えていない。外れた所を日付つきで残す。2026-11-22)
- 1 回目の実行の結果: 固定の変異で黙ったのは F25(日付の形)だけ。理由は門の側の欠陥: 記録の検査に便 XZ0 の script の ``N.check_clean`` を呼んでいた(日付の検査は script 自身の ``check_clean`` に在る)。script の ``check_clean`` を呼ぶ形に直した。予測(clean で赤)は直した後で当たった。
- 同じ実行で、門自身の境の試験(g_5)が、XZ1-5 の上の境を ``10 * 止めた U <= 8 * 分母`` と書き間違えていたのを赤にした(8.0% は ``100 * 止めた U <= 8 * 分母``)。実物の記録では当たり外れは変わらない(1.7%)。直した。
- W2 の向きの語の反転は、1 回目は §3 の中の出現にも当てて 10 件黙った(§3 を形で縛るため。予測のとおり W8 の側の話で、掃きの設計の誤りで W2 に混ぜていた)。W2 は §3 の外だけに当てる形に直した。
- W8(§3 の中)は 1 回目に 15 件黙った: 末尾の空の文の削除 5 件(変異の作りの誤り。空の部分は飛ばす)と、§3 の言い回しの 10 件(「多い順の 3 組」「が大半、と読める」「今年の番号が 1 から始まらない…など」「だけの違いではなく」「前の年の頭の印」など)。後者は §3 の「言える範囲」を決める言い回しなので ``SEC3_PHRASES`` に留めた。留めた後、W8 は全部赤(``SEC3_SILENT`` は空)。
- g_3 の整合の変異のうち 1 つ(止めた W1 を止めた U へ移す)が、1 回目は書類 13・22 で段 OG の U が負になり recount が赤だった(変異の作りの誤り。段 OG の U の上限で切る形に直した)。
- W1〜W7 に黙りは 0(W1 の 1141 件・W2 189・W3 246・W4 13・W5 716・W6 351・W7 632 の全部が赤。数は ``MIN_CASES`` の下限で留める)。
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
    return [d for d in rec[u"書類"] if d[u"番号"] == n][0]


# ---- 記録を整合して作り直す変異の道具
def rebuild(rec):
    d60, d3 = split_docs(rec)
    rec[K60] = sum_docs(d60)
    rec[K3] = sum_docs(d3)
    rec[K63] = sum_docs(rec[u"書類"])
    rec[PRED_KEY] = pred_expected(rec)
    rec[FLAG_KEY] = flags_expected(rec)


def move_mat(d, r, cf, ct, n):
    u"""書類 d で、段 HT の類 r の fact のうち段 O の類 cf になっていた fact から n(上限あり)を ct にする。段 O と段 OG も合わせる(止めた fact は動かさない)。動かした数を返す。"""
    st = d[K_ST]
    n = max(0, min(n, d[K_MAT][r][cf], st[u"OG"][cf]))
    d[K_MAT][r][cf] -= n
    d[K_MAT][r][ct] += n
    for s in (u"O", u"OG"):
        st[s][cf] -= n
        st[s][ct] += n
    return n


def each_doc(c, fn, group=None):
    for d in c.rec[u"書類"]:
        if group is None or (group == 60) == (d[u"番号"] > SEEN_MAX):
            fn(d)
    rebuild(c.rec)


def m_og_w1_over(c):
    each_doc(c, lambda d: move_mat(d, u"U", u"U", u"W1", d[K_ST][u"OG"][u"U"] // 40))


def m_og_u_low(c):
    each_doc(c, lambda d: move_mat(d, u"U", u"U", u"A", d[K_ST][u"OG"][u"U"] * 10 // 100))


def m_xz13_good(c):
    def fn(d):
        move_mat(d, u"N", u"W1", u"N", 10 ** 9)
        move_mat(d, u"U", u"W1", u"U", 10 ** 9)
    each_doc(c, fn)


def m_xz13_only_diff(c):
    def fn(d):
        move_mat(d, u"N", u"W1", u"N", 10 ** 9)
        move_mat(d, u"U", u"W1", u"U", 10 ** 9)
        move_mat(d, u"W1", u"U", u"W1", d[K_MAT][u"W1"][u"U"] // 4)
    each_doc(c, fn)


def m_xz13_only_new(c):
    each_doc(c, lambda d: move_mat(d, u"W1", u"W1", u"U", d[K_MAT][u"W1"][u"W1"] // 20))


def m_o_u_low(c):
    each_doc(c, lambda d: move_mat(d, u"N", u"U", u"A", 10 ** 9))


def stop_g_more(d, n):
    n = min(n, d[K_ST][u"G"][u"U"])
    d[K_SG][u"U"] += n
    d[K_ST][u"G"][u"U"] -= n
    d[K_ST][u"G"][u"S"] += n


def m_stop_u_high(c):
    each_doc(c, lambda d: stop_g_more(d, d[K_ST][u"G"][u"U"] // 5))


def m_stop_u_zero(c):
    def fn(d):
        n = d[K_SG][u"U"]
        d[K_SG][u"U"] = 0
        d[K_ST][u"G"][u"U"] += n
        d[K_ST][u"G"][u"S"] -= n
    each_doc(c, fn)


def m_stop_w1_zero(c):
    def fn(d):
        n = d[K_SG][u"W1"]
        d[K_SG][u"W1"] = 0
        d[K_ST][u"G"][u"W1"] += n
        d[K_ST][u"G"][u"S"] -= n
    each_doc(c, fn)


def m_nn_high(c):
    each_doc(c, lambda d: d.__setitem__(K_NN, sum(d[K_ATTR][k] for k in CTX_ATTRS)))


def m_zero_docs_low(c):
    def fn(d):
        if d[u"番号"] > SEEN_MAX and d[K_ST][u"OG"][u"W1"] == 0:
            move_mat(d, u"U", u"U", u"W1", 1)
    each_doc(c, fn)


def m_all_zero_og_w1(c):
    def fn(d):
        for r in (u"U", u"A", u"W1", u"W2", u"N"):
            move_mat(d, r, u"W1", u"U", 10 ** 9)
    each_doc(c, fn)


def m_sg_over30(c):
    each_doc(c, lambda d: stop_g_more(d, d[K_ST][u"G"][u"U"]))


def m_sog_over30(c):
    def fn(d):
        n = d[K_ST][u"OG"][u"U"] * 4 // 10
        d[K_SOG][u"U"] += n
        d[K_ST][u"OG"][u"U"] -= n
        d[K_ST][u"OG"][u"S"] += n
    each_doc(c, fn)


def m_numcol_zero(c):
    each_doc(c, lambda d: d.__setitem__(K_NUMCOL, 0))


def m_sog_u_high(c):
    u"""止めた fact のうち正しかったものを 8 割にする(止めた W1 を止めた U へ移す。S の数は同じ。段 OG の U・W1 も合わせる)。"""
    def fn(d):
        n = min(d[K_SOG][u"W1"], d[K_ST][u"OG"][u"U"])
        d[K_SOG][u"W1"] -= n
        d[K_SOG][u"U"] += n
        d[K_ST][u"OG"][u"W1"] += n
        d[K_ST][u"OG"][u"U"] -= n
    each_doc(c, fn)


def m_og_w1_triple(c):
    each_doc(c, lambda d: move_mat(d, u"U", u"U", u"W1", d[K_ST][u"OG"][u"U"] // 20))


def m_swap_60_3(c):
    c.rec[K60], c.rec[K3] = c.rec[K3], c.rec[K60]


def m_renumber(c):
    doc_at(c.rec, 3)[u"番号"] = 99


def m_mat_cell(c):
    d = doc_at(c.rec, 10)
    d[K_MAT][u"U"][u"U"] -= 1
    d[K_MAT][u"U"][u"W1"] += 1


def m_nn_over(c):
    d = doc_at(c.rec, 4)
    d[K_NN] = sum(d[K_ATTR][k] for k in CTX_ATTRS) + 1


def add_before_last(c, text):
    ls = c.doc.rstrip(u"\n").split(u"\n")
    ls.insert(len(ls) - 1, text)
    c.doc = u"\n".join(ls) + u"\n"


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
    (u"F5 便 XZ0 の記録の sha256 の写しを違う値に", lambda c: c.shas.__setitem__(DRAFT_RECORD_REL, u"0" * 64), (u"sha",)),
    (u"F6 記録の step の欄を 1 字替える", lambda c: c.rec.__setitem__(u"step", c.rec[u"step"].replace(u"XZ1", u"XZ2", 1)), (u"sha",)),
    (u"F7 記録の材料の sha の 1 字を替える", lambda c: c.rec[u"材料"].__setitem__(u"今年の側の書類の file 名の並びの sha256", u"0" + c.rec[u"材料"][u"今年の側の書類の file 名の並びの sha256"][1:]), (u"recount",)),
    (u"F8 記録の engine の指紋を 1 字替える", lambda c: c.rec[u"engine の指紋"].__setitem__(u"core_py_sha256", u"0" + c.rec[u"engine の指紋"][u"core_py_sha256"][1:]), (u"recount",)),
    (u"F9 書類 10 の段 HT の U を 1 増やす", lambda c: doc_at(c.rec, 10)[K_ST][u"HT"].__setitem__(u"U", doc_at(c.rec, 10)[K_ST][u"HT"][u"U"] + 1), (u"recount",)),
    (u"F10 集計 60 組の段 HT の W1 を 1 増やす", lambda c: inc(c, (K60, K_ST, u"HT", u"W1")), (u"recount",)),
    (u"F11 書類 10 の段 OG の U を 1 減らす", lambda c: doc_at(c.rec, 10)[K_ST][u"OG"].__setitem__(u"U", doc_at(c.rec, 10)[K_ST][u"OG"][u"U"] - 1), (u"recount",)),
    (u"F12 書類 10 の移りの表の [U][U] から [U][W1] へ 1 移す", m_mat_cell, (u"recount",)),
    (u"F13 書類 10 の段 G が止めた U を 1 増やす", lambda c: doc_at(c.rec, 10)[K_SG].__setitem__(u"U", doc_at(c.rec, 10)[K_SG][u"U"] + 1), (u"recount",)),
    (u"F14 書類 4 の番号の列を使った fact を 1 増やす", lambda c: doc_at(c.rec, 4).__setitem__(K_NUMCOL, doc_at(c.rec, 4)[K_NUMCOL] + 1), (u"recount",)),
    (u"F15 書類 4 の違う属性の contextRef だけを 1 減らす", lambda c: doc_at(c.rec, 4)[K_ATTR].__setitem__(ATTR_KEYS[1], doc_at(c.rec, 4)[K_ATTR][ATTR_KEYS[1]] - 1), (u"recount",)),
    (u"F16 書類 4 の番号だけの違いを contextRef が違う W1 より多くする", m_nn_over, (u"recount",)),
    (u"F17 材料の組の数を 64 に", lambda c: c.rec[u"材料"].__setitem__(u"組の数", 64), (u"recount",)),
    (u"F18 予測の欄 XZ1-2 の fact を 1 増やす", lambda c: inc(c, (PRED_KEY, P12, u"fact")), (u"recount",)),
    (u"F19 先に疑う旗の 1 つを True にする", lambda c: set_rec(c, (FLAG_KEY, FL2, u"旗"), True), (u"recount",)),
    (u"F20 集計 60 組と集計 3 組を入れ替える", m_swap_60_3, (u"recount",)),
    (u"F21 便 XZ0 の記録の書類 10 の束 3・段 HT の U を 1 増やす", lambda c: [d for d in c.draft[u"書類"] if d[u"番号"] == 10][0][u"束と段ごとの類別"][u"束 3"]["HT"].__setitem__(u"U", [d for d in c.draft[u"書類"] if d[u"番号"] == 10][0][u"束と段ごとの類別"][u"束 3"]["HT"][u"U"] + 1), (u"recount",)),
    (u"F22 書類の番号 3 を 99 にする", m_renumber, (u"recount",)),
    (u"F23 記録に docid の欄を足す", lambda c: c.rec.__setitem__(u"docID", u"S100ABCD"), (u"clean",)),
    (u"F24 記録に EDINET コードの形の字を足す", lambda c: c.rec.__setitem__(u"メモ", u"E01234"), (u"clean",)),
    (u"F25 記録に日付の形の字を足す", lambda c: c.rec.__setitem__(u"メモ", u"2025-03-31"), (u"clean",)),
    (u"F26 封の写しから XZ1-1 の境の字を消す", lambda c: drop_seal(c, u"段 OG の類 W1 は fact の 1.0% 以下"), (u"bound",)),
    (u"F27 封の写しから §6 の「W1 の率は…2 通りで書く」を消す", lambda c: drop_seal(c, u"W1 の率は、分母を fact の全部にしたものと「通した」にしたものの 2 通りで書く"), (u"bound",)),
    (u"F28 封の写しから §7 の限界の 1 本を消す", lambda c: rep(c, u"- 番号つきのメンバーの形は", u"番号つきのメンバーの形は", attr="seal"), (u"bound",)),
    (u"F29 封の写しから §0 の「並びの頭の 3 組」を消す", lambda c: drop_seal(c, u"並びの頭の 3 組"), (u"bound",)),
    (u"C1 XZ1-1 を外れにする", m_og_w1_over, (u"verdict",)),
    (u"C2 XZ1-2 を外れにする", m_og_u_low, (u"verdict",)),
    (u"C3 XZ1-3 を当たりにする", m_xz13_good, (u"verdict",)),
    (u"C4 XZ1-3 の差の側だけを外にする", m_xz13_only_diff, (u"verdict",)),
    (u"C5 XZ1-3 の新しい W1 の側だけを外にする", m_xz13_only_new, (u"verdict",)),
    (u"C6 XZ1-4 を外れにする", m_o_u_low, (u"verdict",)),
    (u"C7 XZ1-5 を上の外にする", m_stop_u_high, (u"verdict",)),
    (u"C8 XZ1-5 を下の外にする", m_stop_u_zero, (u"verdict",)),
    (u"C9 XZ1-6 を外れにする", m_stop_w1_zero, (u"verdict",)),
    (u"C10 XZ1-7 を上の外にする", m_nn_high, (u"verdict",)),
    (u"C11 XZ1-8 を外れにする", m_zero_docs_low, (u"verdict",)),
    (u"C12 旗: 段 OG の W1 が 60 組の全部で 0", m_all_zero_og_w1, (u"verdict",)),
    (u"C13 旗: 段 G の S が 30% 超", m_sg_over30, (u"verdict",)),
    (u"C14 旗: 段 OG の S が 30% 超", m_sog_over30, (u"verdict",)),
    (u"C15 旗: 番号の列を使った fact が 0", m_numcol_zero, (u"verdict",)),
    (u"C16 XZ1-1 だけを外れにして文書の「示す」と合わなくする", m_og_w1_over, (u"verdict",)),
    (u"C17 整合: 止めた fact のうち正しかったものを 8 割にする", m_sog_u_high, (u"sanity",)),
    (u"C18 整合: 段 OG の W1 を 3 倍にする", m_og_w1_triple, (u"sanity",)),
    (u"D2 頭の「予測の 1 本(XZ1-3)は外れ」を「(XZ1-1)」に", lambda c: rep(c, u"**予測の 1 本(XZ1-3)は外れ。**", u"**予測の 1 本(XZ1-1)は外れ。**"), (u"verdict", u"lines")),
    (u"D3 頭の「当たり 7・外れ 1」を「当たり 6・外れ 2」に", lambda c: rep(c, u"判定した 8 本は 当たり 7・外れ 1", u"判定した 8 本は 当たり 6・外れ 2"), (u"verdict", u"lines")),
    (u"D4 「新しく W1 にした」を「新しく U にした」に", lambda c: rep(c, u"を新しく W1 にした**", u"を新しく U にした**"), (u"lines",)),
    (u"D5 「W1 が 0 になったのではない」を「W1 が 0 になった」に", lambda c: rep(c, u"**W1 が 0 になったのではない。**", u"**W1 が 0 になった。**"), (u"affirm", u"lines")),
    (u"D6 「止めた fact の半分近くは、止めなくてよかった」を「1 割ほどは」に", lambda c: rep(c, u"止めた fact の半分近くは、止めなくてよかった", u"止めた fact の 1 割ほどは、止めなくてよかった"), (u"lines",)),
    (u"D7 「60 組の数が本当の数」を「3 組の数が本当の数」に", lambda c: rep(c, u"**60 組の数が本当の数。**", u"**3 組の数が本当の数。**"), (u"lines",)),
    (u"D8 「100 個に 1 個ほど」を「10 個に 1 個ほど」に", lambda c: rep(c, u"100 個に 1 個ほど", u"10 個に 1 個ほど"), (u"lines", u"phrases")),
    (u"D9 「0 にはなっていない」を「0 になった」に", lambda c: rep(c, u"**0 にはなっていない**", u"**0 になった**"), (u"affirm", u"lines")),
    (u"D10 §5 に「(iii)」の候補を足す", lambda c: rep(c, u"(ii) 通さなかった fact", u"(iii) 通した fact の値を確かめる (ii) 通さなかった fact"), (u"verdict",)),
    (u"D11 §5 の (i) の「0 USD。別の封が先」を消す", lambda c: rep(c, u"(0 USD。別の封が先)", u""), (u"verdict",)),
    (u"D12 §5 の (ii) の「有料。別の封と、払う前の知らせが先」を消す", lambda c: rep(c, u"(有料。別の封と、払う前の知らせが先)", u""), (u"verdict",)),
    (u"D13 §5 の最後の行の後ろに見出しのない案の 1 行を足す", lambda c: add_doc(c, u"- 次は頭の印の比べ方を緩める手もある。"), (u"verdict",)),
    (u"D14 §5 の「両方当たりなので示す」を消す", lambda c: rep(c, u"両方当たりなので示す", u"示す"), (u"verdict",)),
    (u"D15 §5 の最後の行の前に「- (c) …」を足す", lambda c: add_before_last(c, u"- (c) 守りを緩める"), (u"verdict",)),
    (u"D16 頭の限界の 1 本目(3 組を見て作った)の申告の字を消す", lambda c: rep(c, u"(封 §0 の申告)", u""), (u"head", u"lines")),
    (u"D23 文書に「48%」の言い切りを足す", lambda c: add_doc(c, u"決まった fact は 48% だった。"), (u"numbers", u"resid")),
    (u"D19 引用の行から「言えない」「読まない」を全部消す", lambda c: setattr(c, "doc", u"\n".join((ln.replace(u"言えないこと", u"X").replace(u"言えない", u"X").replace(u"読まない", u"X") if QUOTED.search(ln) else ln) for ln in c.doc.splitlines())), (u"affirm",)),
    (u"D20a 文書に「保証」を足す", lambda c: add_doc(c, u"保証する。"), (u"forbidden",)),
    (u"D20b 文書に docID の形を足す", lambda c: add_doc(c, u"S100ABCD"), (u"forbidden",)),
    (u"D20c 文書の commit の字 ca34473a を 1 字替える", lambda c: rep(c, u"ca34473a", u"ca34473b", count=100), (u"commits",)),
    (u"D20d 文書の commit の字 d6a18d51 を 1 字替える", lambda c: rep(c, u"d6a18d51", u"d6a18d52", count=100), (u"commits",)),
    (u"D20e 文書に知らない commit の字を足す", lambda c: add_doc(c, u"commit 1a2b3c4d。"), (u"commits",)),
    (u"D21a §3 の見出しの「記録に欄の無い読み」を消す", lambda c: rep(c, u"(記録に欄の無い読み。", u"(X。"), (u"sec3",)),
    (u"D21b §3 の外に「1008」を足す", lambda c: add_doc(c, u"1008 fact が止まった。"), (u"sec3", u"numbers")),
    (u"D22a §3 の「測っていない」を消す", lambda c: rep(c, u"は、測っていない。", u"は、X。"), (u"sec3",)),
    (u"D22b §3 の「7 割ほど」を「3 割ほど」に", lambda c: rep(c, u"残った W1 の 7 割ほど", u"残った W1 の 3 割ほど"), (u"sec3",)),
    (u"D22c §3 の「大半」を「少数」に", lambda c: rep(c, u"巻き添えの大半は、頭の語が変わった表", u"巻き添えの少数は、頭の語が変わった表"), (u"sec3",)),
)
# 記録を替えて作り直す(整合)変異の名(recount が緑のまま当たり外れ・向きだけが変わることを別の試験で見る)
CONSISTENT = (m_og_w1_over, m_og_u_low, m_xz13_good, m_xz13_only_diff, m_xz13_only_new, m_o_u_low, m_stop_u_high, m_stop_u_zero, m_stop_w1_zero, m_nn_high, m_zero_docs_low,
              m_all_zero_og_w1, m_sg_over30, m_sog_over30, m_numcol_zero, m_sog_u_high, m_og_w1_triple)
DOC_ONLY_NAMES = tuple(n for n, _, _ in MUTATIONS if n.startswith(u"D"))


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
FLIPS = ((u"以上", u"以下"), (u"以下", u"以上"), (u"多い", u"少ない"), (u"少ない", u"多い"), (u"多く", u"少なく"), (u"少なく", u"多く"), (u"減", u"増"), (u"増", u"減"), (u"高", u"低"), (u"低", u"高"),
         (u"超える", u"満たない"), (u"満たない", u"超える"), (u"大きい", u"小さい"), (u"小さい", u"大きい"), (u"大半", u"少数"), (u"大半", u"一部"), (u"主に", u"わずかに"), (u"全部", u"一部"), (u"両方", u"片方"),
         (u"前の年", u"今年"), (u"今年", u"前の年"), (u"正しかった", u"違った"), (u"違った", u"正しかった"), (u"当たり", u"外れ"), (u"外れ", u"当たり"), (u"立っていない", u"立っている"), (u"同じ", u"違う"),
         (u"より", u"と同じ"), (u"だけ", u"も"), (u"ない", u"ある"))
DENOMS = (u"61100", u"48612", u"64534", u"3434", u"2078", u"50537", u"2494")
GROUP_NUMS = (u"60", u"3", u"63")


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
    u"""頭の限界(6 本)の行を消す・断片を 1 つずつ消す・§3 の数を §2 に足す・主張の語の取り違え。"""
    out = []
    head, rest = c.doc.split(u"## §1", 1)
    lines = head.split(u"\n")
    for i, frags in enumerate(LIMIT_FRAGS, 1):
        idx = [k for k, ln in enumerate(lines) if all(p in plain(ln) for p in frags)]
        for k in idx:
            out.append((u"W6L 限界 %d 本目の行を消す" % i, u"\n".join(lines[:k] + lines[k + 1:]) + u"## §1" + rest))
        for p in frags:
            out.append((u"W6L 限界 %d 本目の断片「%s」を消す" % (i, p[:10]), c.doc.replace(p, u"X", 1)))
    for tok in sorted(set(sec3_number_tokens(c))):
        out.append((u"W4 §3 の数 %s を §2 に足す" % tok, c.doc.replace(u"\n## §3 ", u"\n- 足した行 %s 件。\n\n## §3 " % tok, 1)))
    for w in (u"XBRL を作れる。", u"人が書ける。", u"AI が書ける。", u"専用の道具が要らない。", u"EDINET の検査に通る。", u"黙って違う fact は無い。", u"W1 は 0 になった。", u"0 になった。"):
        out.append((u"D18 引用の外に「%s」を足す" % w, c.doc + u"\n" + w + u"\n"))
    return out


def all_doc_cases(c):
    doc = c.doc
    s3n = sec3_number_tokens(c) or [u"114"]
    cases = span_cases(doc, s3n) + flip_cases(doc, c) + group_cases(doc) + table_cell_cases(doc) + delete_cases(doc, c) + limit_cases(c)
    return cases


def judge_rows_cases(c):
    u"""§1 の表の 8 行の 判定・実測・予測 のセルを、行どうしで入れ替える(全部の対)。"""
    lines = c.doc.split(u"\n")
    idx = [i for i, ln in enumerate(lines) if re.match(r"^\| XZ1-\d", ln)]
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


def record_sweep_cases(rec):
    u"""記録の整数・小数・旗の葉を 1 つずつ替える対象(集計 3 つ・予測・旗・書類 4 つ分)。"""
    out = []
    for key in (K60, K3, K63, PRED_KEY, FLAG_KEY):
        for p in leaf_paths(rec[key]):
            out.append((key,) + p)
    for n in (1, 3, 4, 67):
        d = doc_at(rec, n)
        for p in leaf_paths(d):
            if p[0] != u"番号":
                out.append((u"書類", n) + p)
    return out


def apply_leaf(c, path):
    if path[0] == u"書類":
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
MIN_CASES = {u"W1a": 300, u"W1b": 300, u"W1c": 300, u"W2": 150, u"W3": 200, u"W5": 600, u"W6": 250, u"W6L": 20, u"W4": 10, u"D18": 8}


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
        a, b, t = rec[K60], rec[K3], rec[K63]
        S = a[K_ST]
        self.assertEqual((61100, 3434, 64534), (a[K_FACTS], b[K_FACTS], t[K_FACTS]))
        self.assertEqual((2087, 48459, 2299, 2078, 64, 6113), tuple(S[u"HT"][k] for k in CLS))
        self.assertEqual((2087, 49245, 2308, 1826, 67, 5567), tuple(S[u"O"][k] for k in CLS))
        self.assertEqual((2087, 47417, 2299, 744, 29, 6113, 2411), tuple(S[u"G"][k] for k in CLS_S))
        self.assertEqual((2087, 48138, 2308, 474, 32, 5567, 2494), tuple(S[u"OG"][k] for k in CLS_S))
        self.assertEqual((129, 2831, 126, 119, 3, 226), tuple(b[K_ST][u"HT"][k] for k in CLS))
        self.assertEqual((129, 2752, 131, 0, 3, 210, 209), tuple(b[K_ST][u"OG"][k] for k in CLS_S))
        self.assertEqual((2216, 51290, 2425, 2197, 67, 6339), tuple(t[K_ST][u"HT"][k] for k in CLS))
        self.assertEqual((2216, 50890, 2439, 474, 35, 5777, 2703), tuple(t[K_ST][u"OG"][k] for k in CLS_S))
        self.assertEqual((1042, 1334, 35, 1107, 1352, 35), (a[K_SG][u"U"], a[K_SG][u"W1"], a[K_SG][u"W2"], a[K_SOG][u"U"], a[K_SOG][u"W1"], a[K_SOG][u"W2"]))
        self.assertEqual((2301, 408), (a[K_NUMCOL], a[K_NN]))
        self.assertEqual((1922, 95, 53, 2, 6, 0, 0), (a[K_ATTR][ATTR_KEYS[1]], a[K_ATTR][ATTR_KEYS[0]], a[K_ATTR][ATTR_KEYS[3]], a[K_ATTR][ATTR_KEYS[4]], a[K_ATTR][ATTR_KEYS[6]], a[K_ATTR][ATTR_KEYS[2]],
                                                         a[K_ATTR][ATTR_KEYS[5]]))
        self.assertEqual(114, new_w1_of(a))
        sv = stat_values(rec)
        lo, mid, hi, cnt = sv[u"og_rates"]
        self.assertEqual((u"4.2", u"83.8", u"95.3", [52, 45, 7, 2]), (fpct(lo), fpct(mid), fpct(hi), cnt))
        lo, mid, hi, cnt = sv[u"ht_rates"]
        self.assertEqual((u"7.6", u"84.5", u"95.3", [52, 47, 6, 1]), (fpct(lo), fpct(mid), fpct(hi), cnt))
        self.assertEqual((28, 32, 74, 283, 410), sv[u"og_w1"])
        self.assertEqual((6, 54, 342, 1126, 1529), sv[u"ht_w1"])
        self.assertEqual((5, 5, 3, 9, 41, 1151, 35, 60), (sv[u"og_more"], sv[u"o_more"], sv[u"w5"], sv[u"w1p"], sv[u"s_docs"], sv[u"s_top5"], sv[u"stop_u_docs"], sv[u"numcol_docs"]))
        self.assertEqual((160, 6), (len(SG.MUTANTS), len(SG.SILENT_BY_DESIGN)))

    def test_c_1_the_seal_has_the_bound_phrases(self):
        self.assertEqual([], bound_problems(self.c))

    def test_c_2_the_verdicts_are_decided_again_and_equal_the_document(self):
        self.assertEqual([], verdict_problems(self.c))
        j = judge(self.c.rec)
        self.assertEqual(7, sum(1 for v in j.values() if v[0]))
        self.assertEqual([u"XZ1-3"], miss_ids(j))
        self.assertEqual(list(IDS), list(j))
        self.assertEqual((False, False, False, False), suspects(self.c))
        # 当たり外れの判定は丸める前の数。XZ1-1 は fact の全部を分母にした 474/61100(0.78%)で当たり・通した 48612 を分母にすると 474/48612(0.975%。丸めて 1.0)も 1.0% 以下で当たり
        a = self.c.rec[K60]
        self.assertTrue(100 * a[K_ST][u"OG"][u"W1"] <= a[K_FACTS])
        self.assertTrue(100 * a[K_ST][u"OG"][u"W1"] < 1 * (a[K_ST][u"OG"][u"U"] + a[K_ST][u"OG"][u"W1"]))
        # XZ1-3 は 2 つの条件の両方が外(差 252 < 300・新しい W1 114 > 50)
        self.assertEqual((252, 114), (a[K_ST][u"HT"][u"W1"] - a[K_ST][u"O"][u"W1"], new_w1_of(a)))
        self.assertEqual((False, u"差と新"), j[u"XZ1-3"])
        # 封 §6: XZ1-1 と XZ1-2 が両方当たり → 候補 (i)(ii) を示す(文書 §5 がそれ)
        self.assertTrue(j[u"XZ1-1"][0] and j[u"XZ1-2"][0])

    def test_d_1_every_number_in_the_document_is_bound_to_the_record(self):
        self.assertEqual([], doc_number_problems(self.c))
        self.assertEqual([], residual_problems(self.c))

    def test_d_2_every_line_outside_section3_equals_the_one_built_from_the_record(self):
        self.assertEqual([], lines_problems(self.c))
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
        self.assertEqual((u"2079af62", u"d6a18d51", u"ca34473a"), DOC_COMMITS)

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
        self.assertGreaterEqual(len(MUTATIONS), 70)

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
        flips = ((m_og_w1_over, u"XZ1-1"), (m_og_u_low, u"XZ1-2"), (m_xz13_good, u"XZ1-3"), (m_o_u_low, u"XZ1-4"), (m_stop_u_high, u"XZ1-5"), (m_stop_u_zero, u"XZ1-5"),
                 (m_stop_w1_zero, u"XZ1-6"), (m_nn_high, u"XZ1-7"), (m_zero_docs_low, u"XZ1-8"))
        for fn, key in flips:
            c = self.base.copy()
            fn(c)
            self.assertNotEqual(base_j[key][0], judge(c.rec)[key][0], (fn.__name__, key))
            self.assertNotEqual([], verdict_problems(c), fn.__name__)
        for fn, idx in ((m_all_zero_og_w1, 0), (m_sg_over30, 1), (m_sog_over30, 2), (m_numcol_zero, 3)):
            c = self.base.copy()
            fn(c)
            self.assertTrue(suspects(c)[idx], (fn.__name__, suspects(c)))
            self.assertNotEqual([], verdict_problems(c), fn.__name__)
        # XZ1-3 の 3 つの外れ方(両方・差の側だけ・新しい W1 の側だけ)は、それぞれ違う外れ方の行を作る
        notes = set()
        for fn in (m_xz13_only_diff, m_xz13_only_new):
            c = self.base.copy()
            fn(c)
            n = xz13_note(c.rec)
            self.assertIsNotNone(n)
            self.assertNotIn(u"両方が外", n)
            notes.add(n[:20])
        self.assertEqual(2, len(notes))
        self.assertIn(u"両方が外", xz13_note(self.base.rec))
        c = self.base.copy()
        m_xz13_good(c)
        self.assertIsNone(xz13_note(c.rec))

    def test_g_4_every_check_name_a_mutation_names_exists_and_every_check_has_a_mutation(self):
        named = set(k for _, _, ks in MUTATIONS for k in ks)
        self.assertEqual(set(CHECKS), named)
        self.assertTrue(named <= set(CHECKS))
        for k in (u"numbers", u"resid"):
            self.assertIn(k, ORDER_DOC)

    def test_g_5_the_judgement_edges_at_the_seal_bounds(self):
        u"""境の 1 つ手前と境の数(丸める前の整数): 下限・上限とも含む。分母 1000。"""
        def j(**kw):
            a = dict(D=1000, og_w1=10, og_u=800, ht_w1=100, o_w1=50, new_w1=10, ht_u=700, o_u=720, stop_u=50, stop_w1=60, nn=20, z=30)
            a.update(kw)
            return judge_nums(**a)
        self.assertTrue(j(og_w1=10)[u"XZ1-1"][0])
        self.assertFalse(j(og_w1=11)[u"XZ1-1"][0])
        self.assertTrue(j(og_u=720)[u"XZ1-2"][0])
        self.assertFalse(j(og_u=719)[u"XZ1-2"][0])
        self.assertTrue(j(ht_w1=350, o_w1=50, new_w1=50)[u"XZ1-3"][0])
        self.assertFalse(j(ht_w1=349, o_w1=50, new_w1=50)[u"XZ1-3"][0])
        self.assertFalse(j(ht_w1=350, o_w1=50, new_w1=51)[u"XZ1-3"][0])
        self.assertEqual(u"差", j(ht_w1=349, o_w1=50, new_w1=50)[u"XZ1-3"][1])
        self.assertEqual(u"新", j(ht_w1=350, o_w1=50, new_w1=51)[u"XZ1-3"][1])
        self.assertEqual(u"差と新", j(ht_w1=349, o_w1=50, new_w1=51)[u"XZ1-3"][1])
        self.assertTrue(j(ht_u=700, o_u=1100)[u"XZ1-4"][0])
        self.assertFalse(j(ht_u=700, o_u=1099)[u"XZ1-4"][0])
        self.assertTrue(j(stop_u=10)[u"XZ1-5"][0])
        self.assertFalse(j(stop_u=9)[u"XZ1-5"][0])
        self.assertTrue(j(stop_u=80)[u"XZ1-5"][0])
        self.assertFalse(j(stop_u=81)[u"XZ1-5"][0])
        self.assertEqual(u"下", j(stop_u=9)[u"XZ1-5"][1])
        self.assertEqual(u"上", j(stop_u=81)[u"XZ1-5"][1])
        self.assertTrue(j(ht_w1=100, stop_w1=50)[u"XZ1-6"][0])
        self.assertFalse(j(ht_w1=100, stop_w1=49)[u"XZ1-6"][0])
        self.assertTrue(j(ht_w1=100, nn=10)[u"XZ1-7"][0])
        self.assertFalse(j(ht_w1=100, nn=9)[u"XZ1-7"][0])
        self.assertTrue(j(ht_w1=100, nn=45)[u"XZ1-7"][0])
        self.assertFalse(j(ht_w1=100, nn=46)[u"XZ1-7"][0])
        self.assertTrue(j(z=20)[u"XZ1-8"][0])
        self.assertFalse(j(z=19)[u"XZ1-8"][0])

    def test_g_6_the_section5_decision_follows_the_seal_section6(self):
        c = self.base
        sec5 = section(c.doc, u"## §5 ", None)
        s6 = section(c.seal, u"## §6 ", u"## §7 ")
        self.assertEqual([], sec5_decision_problems(sec5, True, s6))
        self.assertNotEqual([], sec5_decision_problems(sec5, False, s6))
        # 3 つ目の候補・候補の費用の字が落ちる・候補が 1 つ・順の入れ替え・最後の行の後ろの字・決めの行が最後でない
        for old, new in ((u"(ii) 通さなかった", u"(iii) 通さなかった"), (u"(0 USD。別の封が先)", u""), (u"(有料。別の封と、払う前の知らせが先)", u""), (u"両方当たりなので示す", u"示す"),
                         (u"(i) 前の年", u"(a) 前の年"), (u"(ii) 通さなかった", u"(i) 通さなかった")):
            self.assertIn(old, sec5, old)
            self.assertNotEqual([], sec5_decision_problems(sec5.replace(old, new, 1), True, s6), old)
        self.assertNotEqual([], sec5_decision_problems(sec5.rstrip(u"\n") + u"\n- 次は別の手がある。\n", True, s6))
        self.assertNotEqual([], sec5_decision_problems(sec5.rstrip(u"\n") + u"\n- (c) 別の案。\n", True, s6))
        # 外れたときの形(候補を示さず、残った W1 と段の間の移りを書いて人間に返す)は緑で、そこに (i) が在れば赤
        miss = u"- **封 §6 の決め: XZ1-1 と XZ1-2 が両方当たりなら、次の便の候補を人間に示す。どちらかが外れたので、残った W1 の数と段の間の移りを書いて、作る側へ進む道を人間に返す。**\n"
        head5 = sec5[:sec5.index(u"- **封 §6 の決め")]
        self.assertEqual([], sec5_decision_problems(head5 + miss, False, s6))
        self.assertNotEqual([], sec5_decision_problems(head5 + miss, True, s6))
        self.assertNotEqual([], sec5_decision_problems(head5 + miss.replace(u"人間に返す", u"示す"), False, s6))
        # 記録を写しの上で外れに変えると(XZ1-1 を外れ)、「示す」の §5 は赤になる(向き)
        cc = self.base.copy()
        m_og_w1_over(cc)
        jj = judge(cc.rec)
        self.assertFalse(jj[u"XZ1-1"][0])
        self.assertNotEqual([], sec5_decision_problems(sec5, jj[u"XZ1-1"][0] and jj[u"XZ1-2"][0], s6))
        # 外れから当たりへ(XZ1-2 を外れにして XZ1-1 は当たりのまま)も同じ
        cc = self.base.copy()
        m_og_u_low(cc)
        jj = judge(cc.rec)
        self.assertFalse(jj[u"XZ1-2"][0])
        self.assertNotEqual([], sec5_decision_problems(sec5, jj[u"XZ1-1"][0] and jj[u"XZ1-2"][0], s6))

    def test_g_7_the_self_suspicion_flags_fire_at_the_exact_boundaries(self):
        c = self.base.copy()
        a = c.rec[K60]
        a[K_FACTS] = 1000
        a[K_ST][u"G"][u"S"] = 300
        a[K_ST][u"OG"][u"S"] = 300
        a[K_NUMCOL] = 1
        self.assertEqual((False, False, False, False), suspects(c))
        a[K_ST][u"G"][u"S"] = 301
        a[K_ST][u"OG"][u"S"] = 301
        a[K_NUMCOL] = 0
        self.assertEqual((False, True, True, True), suspects(c))

    def test_g_8_the_group_sizes_and_the_numbers_are_not_confused(self):
        rec = self.base.rec
        self.assertEqual((60, 3, 63), (len(split_docs(rec)[0]), len(split_docs(rec)[1]), len(rec[u"書類"])))
        self.assertEqual(len(set([SUM60, SUM3, SUM63])), 3)
        self.assertEqual(SUM60 + SUM3, SUM63)
        self.assertNotEqual([], recount_problems(self._swap60_3()))

    def test_g_9_the_verdict_table_stays_the_60_group_numbers(self):
        c = self.base.with_doc(self.base.doc.replace(u"| 474/61100(0.8%) | 当たり |", u"| 0/3434(0.0%) | 当たり |", 1))
        p = verdict_problems(c)
        self.assertNotEqual([], p)
        self.assertTrue(any(u"混ざっている" in x for x in p), p)
        c = self.base.with_doc(self.base.doc.replace(u"| 474/61100(0.8%) | 当たり |", u"| 474/64534(0.7%) | 当たり |", 1))
        self.assertNotEqual([], verdict_problems(c))
        c = self.base.with_doc(self.base.doc.replace(u"| 48138/61100(78.8%) | 当たり |", u"| 50890/64534(78.9%) | 当たり |", 1))
        self.assertTrue(any(u"混ざっている" in x for x in verdict_problems(c)))

    def _swap60_3(self):
        c = self.base.copy()
        m_swap_60_3(c)
        return c

    def test_h_1_the_sweep_over_every_number_direction_word_group_swap_cell_and_line_stays_red(self):
        c = self.base
        cases = all_doc_cases(c) + judge_rows_cases(c)
        results = run_doc_cases(c, cases)
        silent = [n for n, k in results if k is None]
        by_kind = collections.Counter(n.split(u" ")[0] for n, _ in results)
        self.assertEqual(sorted(EXPECTED_SILENT), sorted(silent))
        for kind, lo in MIN_CASES.items():
            self.assertGreaterEqual(by_kind[kind], lo, kind)
        self.assertGreater(len(results), 1000)

    def test_h_2_the_record_leaf_sweep_stays_red(self):
        results = run_record_sweep(self.base)
        silent = [n for n, k in results if k is None]
        self.assertEqual([], silent)
        self.assertGreater(len(results), 500)

    def test_h_3_section3_prose_sweep_reports_what_stays_silent(self):
        u"""§3 は形で縛る(数の並び・足し算・語の留め)。§3 の中の文の削除・向きの語の反転で黙る所が在れば、それを数えて留める(増えたら赤)。"""
        c = self.base
        results = run_doc_cases(c, sec3_cases(c))
        silent = [n for n, k in results if k is None]
        self.assertEqual(sorted(SEC3_SILENT), sorted(silent))


SEC3_SILENT = ()


if __name__ == "__main__":
    unittest.main()
