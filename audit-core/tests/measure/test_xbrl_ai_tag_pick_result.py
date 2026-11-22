# -*- coding: utf-8 -*-
u"""結果の門: 封 docs/XBRL_AI_TAG_PICK_SEAL_2026-11-22.md(7bb4fa24)の結果の文書 docs/XBRL_AI_TAG_PICK_RESULT_2026-11-22.md(便 XD0。有料の便)。

封の門 ``test_xbrl_ai_tag_pick_seal.py`` の次の段。**追跡されている記録・script・封・封の門・結果の文書と git の履歴だけを読む**(書類の置き場も置き場の返事の字も読まない・通信しない・鍵は読まない・API は呼ばない)。
便 XA0 の結果の門 ``test_xbrl_sheet_wall_result.py`` の部品(読み・sha256・% の丸め・節の切り出し・数のトークン・blob の道具)を読み込んで使う(門としては走らせない)。
検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表で 1 つずつ(木の file は変異させず、``Ctx`` の写しに当てる)。

 a script・記録・封・封の門の sha256(字で留める)・記録の script の sha256・封の commit の欄・記録の限界の欄・席・呼び出しの形・指示文の型・費用の欄が script の字と同じ
 b 記録の数え直し: 行(394)と呼び出し(910・試し 10)の欄から、**script の関数を使わずに**、席ごとの札・P1・P2・帯・計算書の種類・呼び出しの記録・予測の判定に要る数・自己点検の数・使った額を数え直し、
   記録の欄と照らす。行と呼び出しの関係(札と「答えが読めた」・やり直しの形・USD の式・2 席が同じ要素を選んだと札の関係・類 W に「正」が無い)も見る
 c 予測 XD0-1〜XD0-11 の当たり外れを、封 §5 の字の境と記録から決め直し、文書 §1 の表・件数と同じことを見る(XD0-4 は主の席の「誤」が 9 行以下なので判定しない)。
   封 §5 の読み方の決め(XD0-2 と XD0-3 が当たりなら次の便の候補)・封 §5 の「先に自分の欠陥を疑う条件」(封の字のまま・条件ごと。主の席だけの読みと副の席も入れた読みの両方)と文書が合う
 d 結果の文書の数: §3 の記録に欄の無い読みの 1 行を除いて、数字を含む行は全部、記録から組んだ数の並びの内。表の行・主な主張の文は、記録から組んだ字とそのまま(断片で)照らす
 e 文書の要点の字・頭の負けと限界・禁止語・「作れる」「紙を AI が書ける」「専用の道具が要らない」を肯定で書かない・docID と EDINET コードの形
 f 封・script・記録・封の門が commit の blob と一致(結果の便で 0 行)・engine は封の commit から 0 行・順序・文書が書く commit の字が実の履歴と合う
 g 使った額は記録の呼び出しの USD の和・記録の「使った額」・文書の字が同じ。呼び出しの USD は 1 回ごとに「入力 × 5 + 出力 × 25 / 100 万」の式と合う
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


WG = load_module("tests/measure/test_xbrl_sheet_wall_result.py", "xbrl_sheet_wall_result_gate_for_ai_tag_pick_result_gate")                # 便 XA0 の結果の門の部品。門としては走らせない
SG = load_module("tests/measure/test_xbrl_ai_tag_pick_seal.py", "xbrl_ai_tag_pick_seal_gate_for_result_gate")                # 封の門の部品。門としては走らせない
PR = SG.PR
MS = SG.MS

read, sha_file, guard, pct, section, rep = WG.read, WG.sha_file, WG.guard, WG.pct, WG.section, WG.rep
add_doc, drop_all = WG.add_doc, WG.drop_all
od = collections.OrderedDict

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
RECORD_REL = SG.RECORD_REL
GATE_REL = "tests/measure/test_xbrl_ai_tag_pick_result.py"
DOC_REL = "docs/XBRL_AI_TAG_PICK_RESULT_2026-11-22.md"
SCRIPT_COMMIT_SHORT = "f119b80c"                  # script・封の門を足した commit
RECORD_COMMIT_SHORT = "e066a557"                  # 記録を足した commit
BLOB_AT = collections.OrderedDict([
    (SEAL_REL, SEAL_COMMIT_SHORT), (SCRIPT_REL, SCRIPT_COMMIT_SHORT), (SEAL_GATE_REL, SCRIPT_COMMIT_SHORT), (RECORD_REL, RECORD_COMMIT_SHORT)])
DOC_COMMITS = (SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT)

SHA_PIN = collections.OrderedDict([
    (RECORD_REL, "16042d2d6fb8ffd1562c0eed42c3b8f9d5258b6729339bf39d1d9df9328b0e00"),
    (SCRIPT_REL, "8305b2b5b9281b3879bc1a2d332095a902f3570ed22a1bdafe85d4435bacbdd1"),
    (SEAL_GATE_REL, "4dab0d2ae3ec9ba94e4a4e32e61fec246df044af33ad6eaa0b011454a66ce5ba"),
    (SEAL_REL, "85a1dd82e5df520a9de7f005446aa1768d21a1c5b85d941e825fb7cd7b4bce79")])
XG1_SCRIPT_SHA = "24159344be6b2ecf6957339b1356d8049bfe90cab1f4660be5b2f7151a7d6a33"

# 行の欄・呼び出しの欄の列(記録の「行の欄」「呼び出しの欄」の順。script の定数は使わず字で留める)
ROW_COLS = [u"書類の番号", u"類", u"候補の数", u"計算書の種類", u"主の席の札", u"副の席の札", u"2 席が同じ要素を選んだ", u"昇順の頭の候補が書類の要素と同じ", u"主の席の指示文の sha256", u"副の席の指示文の sha256",
            u"主の席の呼び出しの数", u"副の席の呼び出しの数"]
I_DOC, I_CLS, I_N, I_KIND, I_M, I_S, I_SAME, I_HEAD, I_MSHA, I_SSHA, I_MC, I_SC = range(12)
CALL_COLS = [u"行の番号", u"席", u"答えの回", u"中断した呼び出し", u"HTTP の状態", u"HTTP の再試行の数", u"stop_reason", u"block の type の並び", u"入力 token", u"出力 token", u"返った usage の USD",
             u"見積りで数えた USD", u"返った text の字数", u"答えが読めた"]
J_ROW, J_SEAT, J_ATT, J_ABORT, J_HTTP, J_RETRY, J_STOP, J_BLOCKS, J_TIN, J_TOUT, J_USD, J_EST, J_CHARS, J_OK = range(14)

L_OK, L_BAD, L_ZERO, L_NONE = u"正", u"誤", u"0", u"答えなし"
LABS = (L_OK, L_BAD, L_ZERO, L_NONE)
KINDS = (u"貸借", u"損益", u"キャッシュフロー", u"株主資本等変動", u"種類なし")
KINDS_WITH = (u"貸借", u"損益", u"キャッシュフロー")
BANDS = od([(u"候補 2", lambda n: n == 2), (u"候補 3〜6", lambda n: 3 <= n <= 6), (u"候補 7 以上", lambda n: n >= 7)])
SEAT_MAIN, SEAT_SUB = u"主", u"副"
PRICE_IN, PRICE_OUT, CAP_USD = 5, 25, 5
DEV_COUNT = 5

K_TALLY = u"数えるもの(封 §2-5 の 1〜4)"
K_LINES = u"並べる 2 行(封 §2-5 の 5。類 A)"
K_CALLS = u"呼び出しの記録(封 §2-5 の 6)"
K_TRIAL = u"試しの 10 回(封 §3。本番の数に入れない)"
K_PRED = u"予測の判定に要る数(XD0-1〜XD0-11。当たり・外れは結果の文書で)"
K_SUSPECT = u"先に自分の欠陥を疑う条件の数(封 §5)"
K_WIRE = u"配線の確認(封 §1・§2-1。予測ではない。違えば止まる)"
SECTION_KEYS = (K_TALLY, K_LINES, K_CALLS, K_TRIAL, K_PRED, K_SUSPECT)
BIG_KEYS = (u"行", u"呼び出し", u"試しの行", u"試しの呼び出し")
IDS = (u"XD0-1", u"XD0-2", u"XD0-3", u"XD0-4", u"XD0-5", u"XD0-6", u"XD0-7", u"XD0-8", u"XD0-9", u"XD0-10", u"XD0-11")

# 封 §5 の予測の表の境の字(封の字そのまま)。文書 §1 の表の予測の欄にも同じ字が在る
SEAL_ROW_BOUND = od([(u"XD0-1", u"245 行以上 310 行以下"), (u"XD0-2", u"228 行以上"), (u"XD0-3", u"5% 以下"), (u"XD0-4", u"半分以上"), (u"XD0-5", u"20 行以下"), (u"XD0-6", u"34 行以上"),
                     (u"XD0-7", u"70% 以上"), (u"XD0-8", u"10 ポイント以上低い"), (u"XD0-9", u"10 行以上少ない"), (u"XD0-10", u"5 行以下"), (u"XD0-11", u"3 USD 以下")])
BOUND_SEAL_PHRASES = (u"主の席が「誤」の行のうち、P2 が止める行は半分以上", u"主の席の「誤」が 9 行以下なら判定しない", u"類 A の 326 行で、主の席の「正」は 245 行以上 310 行以下", u"類 A で、P2 が通す行は 228 行以上",
                      u"P2 が誤って通した行は 1 行以上、かつ、P2 が通した行の 5% 以下", u"類 W の 68 行で、主の席の「0」は 20 行以下", u"P2 が誤って通す行は 34 行以上",
                      u"主の席の「正」はその行の 70% 以上", u"10 ポイント以上低い", u"副の席の「正」は主の席の「正」より 10 行以上少ない", u"主の席の答えなしは、394 行のうち 5 行以下",
                      u"使った額は 3 USD 以下",
                      u"XD0-2 と XD0-3 がどちらも当たったときだけ", u"XD0-3 が上に外れたら「2 席の一致だけでは通せない」と読む", u"XD0-6 が当たったら「候補の中に答えが無い行は、席の一致では止まらない。別の止めが要る」と読む",
                      u"類 A で主の席の「正」が 130 行以下(でたらめの率に近い)・席の「0」が類 A の半分を超える・答えなしが 40 行以上・P2 が通した行が 300 行以上で誤 0",
                      u"番号と要素の名の戻し・並びの向き・答えの読み方を、作り物の行と答えの分布で確かめて結果に書く",
                      u"「AI が XBRL を作れる」「紙を AI が書ける」は、この便からは言えない", u"**上限**: 5 USD", u"U 1033・A 208・N 18・W 2", u"U 12444・A 2603・N 387・W 68", u"合わせて 394 行")
HEAD_PHRASES = (u"先に負けと限界を書く", u"この文書の数は、§3 を除いて全部、記録から 1 つずつ読んだもの", u"有料。使った額は試しを含めて", u"独立監査 GO", u"engine は 0 行", u"書類は便 XG0 と同じ 67 本",
                u"答えなしが 40 行以上", u"原因は封の決めの側(司令塔の設計)に在る", u"司令塔は上限を上げずに本番を走らせた", u"同じ型(返事が上限で切れる)は前の便で踏んで記憶に書いてあった",
                u"このため主の席の数は低く出ている", u"この便は「主の席がどれだけ正しく選べるか」を測りきれていない", u"対の XD0-2 が大きく外れた",
                u"字のあいまいさは封を書いた司令塔の落ち度", u"どちらの読みでも、確かめること", u"行の字は提出済みの書類の字で、AI や人がこれから書く紙の字ではない",
                u"送る行は答えを使って選んだ", u"2 つの類を足した率は書かない", u"指示文は司令塔が書いた(盲検でない)", u"席と司令塔は同じ系統の model", u"繰り返しの幅は測っていない",
                u"測ったのは要素の選びだけ", u"「AI が XBRL を作れる」「紙を AI が書ける」「専用の道具が要らない」は、この便からは言えない")
PHRASES = (u"言えること", u"言えないこと", u"人間に返すこと", u"記録に欄の無い読み", u"取り直しの便", u"script の監査で残った指摘", u"緩い読みは封の読み方ではないので、§1 の判定には使わない",
           u"封 §5 の読み方の決め", u"判定しない(封の決め: 主の席の「誤」が 9 行以下)")
FORBIDDEN_WORDS = (u"精度", u"世界で 1 社", u"LLM より正確", u"保証", u"完璧")
DOCID_FORM = WG.DOCID_FORM
ECODE_FORM = WG.ECODE_FORM
STRUCTURAL = WG.STRUCTURAL
BOUND_NUMBERS = set([u"245", u"310", u"228", u"5", u"20", u"34", u"70", u"10", u"130", u"300", u"40", u"3", u"8", u"9", u"1", u"67", u"62", u"12", u"7", u"2", u"6"])
QUOTED_CLAIM = re.compile(u"「[^」]*(?:作れる|専用の道具が要らない|人が書ける|AI が書ける)[^」]*」")
AFFIRM_WORDS = (u"作れる(?!か)", u"作れます", u"専用の道具が要らない", u"人が書ける(?!か)", u"AI が書ける(?!か)", u"紙を AI が書ける", u"検査に通る(?!こと|か)")
SEC3_FREE_START = u"- **84 行のうち 4 行"          # §3 の、記録に欄の無い読み(出所は記録の監査の席)の 1 行。数は記録に縛らない(この行の外に、その数が出ていないことは見る)


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


# ======================================================================================================
# b 数え直し(script の関数は使わない)
def norm(o):
    return json.loads(json.dumps(o, ensure_ascii=False))


def rate_row(n, d):
    return od([(u"行", n), (u"分母", d), (u"%", float(pct(n, d)) if d else None)])


def lab_cell(vs, i):
    c = collections.Counter(v[i] for v in vs)
    return od((k, c.get(k, 0)) for k in LABS)


def rule_cell(vs, passed):
    ps = [v for v in vs if passed(v)]
    st = [v for v in vs if not passed(v)]
    return od([(u"通した行", len(ps)), (u"誤って通した行", sum(1 for v in ps if v[I_M] == L_BAD)), (u"止めた行", len(st)), (u"止めた行のうち主の席が正", sum(1 for v in st if v[I_M] == L_OK))])


def cell_of(vs):
    p1 = lambda v: v[I_M] in (L_OK, L_BAD)          # noqa: E731  P1: 主の席が 1 以上の番号を答えた(正か誤)
    p2 = lambda v: bool(v[I_SAME])                  # noqa: E731  P2: 2 席が同じ要素を選んだ
    return od([(u"行", len(vs)), (u"主の席の札", lab_cell(vs, I_M)), (u"副の席の札", lab_cell(vs, I_S)), (u"P1(主の席だけ)", rule_cell(vs, p1)), (u"P2(2 席の一致)", rule_cell(vs, p2)),
               (u"主の席が誤の行", sum(1 for v in vs if v[I_M] == L_BAD)), (u"主の席が誤の行のうち P2 が止めた行", sum(1 for v in vs if v[I_M] == L_BAD and not v[I_SAME]))])


def tally_of(rows):
    a = [v for v in rows if v[I_CLS] == u"A"]
    w = [v for v in rows if v[I_CLS] == u"W"]
    out = od()
    out[u"類 A"] = cell_of(a)
    out[u"類 W"] = cell_of(w)
    out[u"類 A を候補の数の帯で分けた"] = od((k, cell_of([v for v in a if fn(v[I_N])])) for k, fn in BANDS.items())
    out[u"類 A を計算書の種類で分けた"] = od((k, cell_of([v for v in a if v[I_KIND] == k])) for k in KINDS)
    return out


def lines_of(rows):
    a = [v for v in rows if v[I_CLS] == u"A"]
    w = [v for v in rows if v[I_CLS] == u"W"]
    p2a = [v for v in a if v[I_SAME]]
    exp = float(sum(Fraction(1, v[I_N]) for v in a))
    return od([(u"何もしなかったら: でたらめに 1 つ選んだときの正の数の期待(行ごとの 1 ÷ 候補の数の和)", round(exp, 4)),
               (u"何もしなかったら: 昇順の頭の候補を選んだときの正の数", sum(1 for v in a if v[I_HEAD])), (u"類 A の行", len(a)),
               (u"完璧に動いたら: P2 が通す類 A の行・誤って通す行・類 W で止める行", od([(u"類 A を通す", len(a)), (u"誤って通す", 0), (u"類 W を止める", len(w))])),
               (u"今: P2 が通した類 A の行・誤って通した行・類 W で止めた行", od([(u"類 A を通した", len(p2a)), (u"誤って通した", sum(1 for v in p2a if v[I_M] == L_BAD)), (u"類 W を止めた", sum(1 for v in w if not v[I_SAME]))]))])


def pairs_of(values):
    return [[k, v] for k, v in sorted(collections.Counter(values).items())]


def calls_of(calls, n_rows):
    out = od()
    total = 0.0
    for model, tag in ((u"claude-sonnet-5-5", SEAT_MAIN), (u"claude-haiku-5-5", SEAT_SUB)):
        cs = [c for c in calls if c[J_SEAT] == tag]
        real = [c for c in cs if not c[J_ABORT]]
        none_rows = n_rows - len(set(c[J_ROW] for c in real if c[J_OK]))
        uu = round(sum(c[J_USD] for c in cs), 6)
        ue = round(sum(c[J_EST] for c in cs), 6)
        total += uu + ue
        out[tag] = od([(u"model", model), (u"呼び出しの数(HTTP の再試行を除く。中断した呼び出しを除く)", len(real)), (u"うち 1 回目", sum(1 for c in real if c[J_ATT] == 1)),
                       (u"答えのやり直し(封 §2-3)", sum(1 for c in real if c[J_ATT] == 2)), (u"HTTP の再試行(429・5xx)の合計", sum(c[J_RETRY] for c in real)),
                       (u"中断した(次の走りで見つけた・上限で止めた)呼び出し", sum(1 for c in cs if c[J_ABORT])), (u"答えなしの行", none_rows),
                       (u"入力 token の合計", sum(c[J_TIN] or 0 for c in cs)), (u"出力 token の合計", sum(c[J_TOUT] or 0 for c in cs)),
                       (u"USD(返った usage で。§3 の単価)", uu), (u"USD(返らなかった呼び出しの見積りで数えた分)", ue), (u"USD 合計", round(uu + ue, 6)),
                       (u"返った block の type の並びの種類", pairs_of(c[J_BLOCKS] for c in real if c[J_BLOCKS] is not None)),
                       (u"stop_reason の種類", pairs_of(str(c[J_STOP]) for c in real)), (u"HTTP の状態の種類", pairs_of(str(c[J_HTTP]) for c in real))])
    out[u"USD の全部"] = round(total, 6)
    return out


def usd_all_of(rec):
    return round(sum(c[J_USD] + c[J_EST] for c in list(rec[u"試しの呼び出し"]) + list(rec[u"呼び出し"])), 6)


def pred_of(rows, usd):
    a = [v for v in rows if v[I_CLS] == u"A"]
    w = [v for v in rows if v[I_CLS] == u"W"]
    p2a = [v for v in a if v[I_SAME]]
    bad = [v for v in a if v[I_M] == L_BAD]
    big = [v for v in a if v[I_N] >= 7]
    nok = [v for v in a if v[I_KIND] == u"種類なし"]
    wk = [v for v in a if v[I_KIND] in KINDS_WITH]
    ss = [v for v in a if v[I_KIND] not in KINDS_WITH and v[I_KIND] != u"種類なし"]
    ok = lambda vs: sum(1 for v in vs if v[I_M] == L_OK)                # noqa: E731
    sok = lambda vs: sum(1 for v in vs if v[I_S] == L_OK)               # noqa: E731
    diff = u"分母 0" if not nok or not wk else u"%.2f" % (100.0 * ok(nok) / len(nok) - 100.0 * ok(wk) / len(wk))
    out = od()
    out[u"XD0-1 類 A の主の席の正"] = od([(u"行", len(a)), (u"主の席の正", ok(a))])
    out[u"XD0-2 類 A で P2 が通した行"] = od([(u"行", len(a)), (u"P2 が通した行", len(p2a))])
    wr = sum(1 for v in p2a if v[I_M] == L_BAD)
    out[u"XD0-3 類 A で P2 が誤って通した行 / P2 が通した行"] = od([(u"P2 が通した行", len(p2a)), (u"誤って通した行", wr), (u"誤って通した行 / 通した行", rate_row(wr, len(p2a)))])
    out[u"XD0-4 類 A で主の席が誤の行のうち P2 が止めた行"] = od([(u"主の席が誤の行", len(bad)), (u"P2 が止めた行", sum(1 for v in bad if not v[I_SAME]))])
    out[u"XD0-5 類 W の主の席の 0"] = od([(u"行", len(w)), (u"主の席の 0", sum(1 for v in w if v[I_M] == L_ZERO))])
    out[u"XD0-6 類 W で P2 が誤って通した行"] = od([(u"行", len(w)), (u"P2 が通した行(類 W は全部誤)", sum(1 for v in w if v[I_SAME]))])
    out[u"XD0-7 類 A の候補が 7 以上の行の主の席の正"] = od([(u"行", len(big)), (u"主の席の正", ok(big)), (u"率", rate_row(ok(big), len(big)))])
    out[u"XD0-8 類 A の主の席の正の率(種類なし / 種類の在る行(貸借・損益・キャッシュフロー))"] = od([
        (u"種類なし", rate_row(ok(nok), len(nok))), (u"種類の在る行(貸借・損益・キャッシュフロー)", rate_row(ok(wk), len(wk))), (u"差(ポイント。種類なし − 種類の在る行)", diff),
        (u"株主資本等変動の行(封の字の外。別に並べる)", rate_row(ok(ss), len(ss)))])
    out[u"XD0-9 類 A の副の席の正と主の席の正"] = od([(u"副の席の正", sok(a)), (u"主の席の正", ok(a)), (u"差(主 − 副)", ok(a) - sok(a))])
    out[u"XD0-10 主の席の答えなし(送った行の全部)"] = od([(u"行", len(rows)), (u"主の席の答えなし", sum(1 for v in rows if v[I_M] == L_NONE))])
    out[u"XD0-11 使った額 USD(試しを含む全部)"] = usd
    return out


def suspect_of(rows):
    a = [v for v in rows if v[I_CLS] == u"A"]
    ok = sum(1 for v in a if v[I_M] == L_OK)
    zero = sum(1 for v in a if v[I_M] == L_ZERO)
    none = sum(1 for v in rows if v[I_M] == L_NONE)
    p2 = [v for v in a if v[I_SAME]]
    wr = sum(1 for v in p2 if v[I_M] == L_BAD)
    return od([(u"類 A の主の席の正", ok), (u"類 A の主の席の 0", zero), (u"類 A の行", len(a)), (u"主の席の答えなし(送った行の全部)", none), (u"類 A で P2 が通した行", len(p2)), (u"うち誤", wr),
               (u"条件に当たる(正が 130 行以下)", ok <= 130), (u"条件に当たる(0 が類 A の半分を超える)", 2 * zero > len(a)), (u"条件に当たる(答えなしが 40 行以上)", none >= 40),
               (u"条件に当たる(P2 が通した行が 300 行以上で誤 0)", len(p2) >= 300 and wr == 0)])


def derive(rec):
    u"""行・呼び出しの欄から、記録の 6 つの欄を数え直す。"""
    rows, calls = rec[u"行"], rec[u"呼び出し"]
    return od([(K_TALLY, tally_of(rows)), (K_LINES, lines_of(rows)), (K_CALLS, calls_of(calls, len(rows))), (K_TRIAL, od([(u"呼び出し", calls_of(rec[u"試しの呼び出し"], len(rec[u"試しの行"])))])),
               (K_PRED, pred_of(rows, usd_all_of(rec))), (K_SUSPECT, suspect_of(rows))])


def rebuild(rec):
    u"""行・呼び出しの欄はそのままに、6 つの欄と「使った額」を作り直す(整合した変更)。"""
    d = derive(rec)
    for k in SECTION_KEYS:
        rec[k] = d[k]
    rec[u"費用"][u"使った額 USD(試しを含む)"] = usd_all_of(rec)


def relation_problems(rec):
    u"""行と呼び出しの関係・行の中の関係・呼び出し 1 回の中の関係。"""
    out = []
    rows, calls = rec[u"行"], rec[u"呼び出し"]
    if rec[u"行の欄"] != ROW_COLS or rec[u"呼び出しの欄"] != CALL_COLS:
        return [u"行の欄・呼び出しの欄の列の名が違う"]
    if len(rows) != 394 or len(rec[u"試しの行"]) != 5 or len(rec[u"試しの呼び出し"]) != 10:
        return [u"行 394・試しの行 5・試しの呼び出し 10 でない"]
    # 行の中
    for i, r in enumerate(rows):
        if r[I_CLS] not in (u"A", u"W") or r[I_M] not in LABS or r[I_S] not in LABS or r[I_KIND] not in KINDS or not isinstance(r[I_SAME], bool) or not isinstance(r[I_HEAD], bool):
            out.append(u"行 %d の類・札・種類・真偽の欄が決めの字でない" % i)
            continue
        if r[I_CLS] == u"W" and (r[I_M] == L_OK or r[I_S] == L_OK):
            out.append(u"行 %d: 類 W に「正」が在る(候補の中に答えが無い)" % i)
        if r[I_CLS] == u"W" and r[I_HEAD]:
            out.append(u"行 %d: 類 W の「昇順の頭の候補が書類の要素と同じ」が真" % i)
        if r[I_SAME]:
            if r[I_M] not in (L_OK, L_BAD) or r[I_S] not in (L_OK, L_BAD) or (r[I_M] == L_OK) != (r[I_S] == L_OK):
                out.append(u"行 %d: 2 席が同じ要素を選んだのに札が合わない(同じ要素なら正と誤は揃う)" % i)
        if r[I_DOC] <= DEV_COUNT:
            out.append(u"行 %d の書類の番号が開発の 5 本" % i)
        if r[I_N] < (2 if r[I_CLS] == u"A" else 1):
            out.append(u"行 %d の候補の数が小さすぎる" % i)
        if r[I_HEAD] and r[I_M] == L_NONE:
            pass
    if [r[I_DOC] for r in rows] != sorted(r[I_DOC] for r in rows):
        out.append(u"行の書類の番号が昇順でない")
    if sum(1 for r in rows if r[I_CLS] == u"A") != 326 or sum(1 for r in rows if r[I_CLS] == u"W") != 68:
        out.append(u"類 A が 326・類 W が 68 でない")
    # 呼び出しと行
    byrs = collections.defaultdict(list)
    for c in calls:
        byrs[(c[J_ROW], c[J_SEAT])].append(c)
        if c[J_HTTP] != 200 or c[J_RETRY] != 0 or c[J_ABORT] or c[J_BLOCKS] != u"text" or c[J_STOP] not in (u"end_turn", u"max_tokens") or c[J_EST] != 0:
            out.append(u"呼び出し(行 %s・%s)の HTTP・再試行・中断・block・stop_reason・見積りが本番の形(200・0・偽・text・end_turn か max_tokens・0)でない" % (c[J_ROW], c[J_SEAT]))
    for i, r in enumerate(rows):
        for seat, li, ci in ((SEAT_MAIN, I_M, I_MC), (SEAT_SUB, I_S, I_SC)):
            cs = sorted(byrs.get((i, seat), []), key=lambda c: c[J_ATT])
            if [c[J_ATT] for c in cs] not in ([1], [1, 2]) or len(cs) != r[ci]:
                out.append(u"行 %d の%sの席の呼び出しの回・数が行の欄と合わない" % (i, seat))
                continue
            readable = [c[J_OK] for c in cs]
            if len(cs) == 2 and readable[0]:
                out.append(u"行 %d の%sの席: 1 回目が読めたのにやり直した" % (i, seat))
            if (r[li] == L_NONE) != (not any(readable)):
                out.append(u"行 %d の%sの席の札が「答えなし」であることと、答えが読めた呼び出しが無いことが合わない" % (i, seat))
            if r[li] == L_NONE and len(cs) != 2:
                out.append(u"行 %d の%sの席: 答えなしなのにやり直していない" % (i, seat))
    for c in list(calls) + list(rec[u"試しの呼び出し"]):
        if c[J_OK] and c[J_STOP] != u"end_turn":
            out.append(u"呼び出し(行 %s・%s): end_turn でないのに答えが読めた(封 §2-3)" % (c[J_ROW], c[J_SEAT]))
        if abs(c[J_USD] - (c[J_TIN] * PRICE_IN + c[J_TOUT] * PRICE_OUT) / 1e6) > 1e-9:
            out.append(u"呼び出し(行 %s・%s)の USD が入力 × 5 + 出力 × 25 の式と合わない" % (c[J_ROW], c[J_SEAT]))
        if c[J_STOP] == u"max_tokens" and c[J_TOUT] != 100:
            out.append(u"呼び出し(行 %s・%s): max_tokens で終わったのに出力が 100 token でない" % (c[J_ROW], c[J_SEAT]))
    tr = rec[u"試しの行"]
    if [r[I_CLS] for r in tr] != [u"A"] * 5 or any(r[I_DOC] > DEV_COUNT for r in tr):
        out.append(u"試しの行が「開発の 5 本の類 A の 5 行」でない")
    if sorted((c[J_ROW], c[J_SEAT]) for c in rec[u"試しの呼び出し"]) != sorted((i, s) for i in range(5) for s in (SEAT_MAIN, SEAT_SUB)):
        out.append(u"試しの呼び出しが 5 行 × 2 席の 1 回ずつでない")
    if usd_all_of(rec) > CAP_USD:
        out.append(u"使った額が上限 5 USD を超えている")
    return out


def recount_problems(c):
    rec = c.rec
    out = []
    for k in BIG_KEYS:
        if k not in rec:
            return [u"記録に欄が無い: %s" % k]
    rel = relation_problems(rec)
    if rel:
        return rel[:20]
    want = derive(rec)
    for k in SECTION_KEYS:
        if norm(rec[k]) != norm(want[k]):
            out.append(u"記録の「%s」が行・呼び出しの欄から数え直した値と違う" % k[:20])
    if abs(rec[u"費用"][u"使った額 USD(試しを含む)"] - usd_all_of(rec)) > 1e-9:
        out.append(u"記録の「使った額」が呼び出しの USD の和と違う")
    if rec[u"回数"] != od([(u"行(本番)", 394), (u"席", 2), (u"呼び出しの予定(本番)", 788), (u"試しの行", 5), (u"試しの呼び出し", 10), (u"やり直しを入れた本番の最大", 1576)]):
        out.append(u"記録の回数の欄が決めと違う")
    w = rec[K_WIRE]
    if (w[u"段 3 の類の数(開発)"], w[u"段 3 の類の数(本番)"]) != (od([(u"U", 1033), (u"A", 208), (u"N", 18), (u"W", 2)]), od([(u"U", 12444), (u"A", 2603), (u"N", 387), (u"W", 68)])) or (
            w[u"本番の類 A の行(8 行に 1 行)"], w[u"本番の類 W の行"], w[u"送る行(本番)"], w[u"試しの行"]) != (326, 68, 394, 5):
        out.append(u"配線の確認の欄が封 §1・§2-1 の数(U 1033・A 208・N 18・W 2 / U 12444・A 2603・N 387・W 68 / 326・68・394・5)と違う")
    return out


def sha_problems(c):
    out = []
    for rel, want in SHA_PIN.items():
        if c.shas[rel] != want:
            out.append(u"sha256 が字で留めた値と違う: %s" % rel)
    rec = c.rec
    if rec[u"この script の sha256"] != SHA_PIN[SCRIPT_REL]:
        out.append(u"記録の script の sha256 が script と違う")
    if (rec[u"seal"], rec[u"封の commit"]) != (SEAL_REL, SEAL_COMMIT_SHORT):
        out.append(u"記録の封の欄が違う")
    if rec[u"便 XG1 の script の sha256"] != XG1_SCRIPT_SHA or rec[u"材料"][u"便 XG1 の script の sha256"] != XG1_SCRIPT_SHA or MS.XG1_SCRIPT_SHA256 != XG1_SCRIPT_SHA:
        out.append(u"便 XG1 の script の sha256 の欄が留めた字と違う")
    if rec[u"限界"] != list(MS.LIMITS):
        out.append(u"記録の限界の欄が script の字と違う")
    seats = rec[u"席"]
    if (seats[u"主の席"][u"model"], seats[u"副の席"][u"model"]) != (MS.SEATS[0], MS.SEATS[1]) or seats[u"主の席"][u"thinking"] != MS.THINKING[MS.SEATS[0]] or seats[u"副の席"][u"thinking"] != MS.THINKING[MS.SEATS[1]] or (
            seats[u"主の席"][u"候補の並び"], seats[u"副の席"][u"候補の並び"]) != (u"昇順", u"降順"):
        out.append(u"記録の席の欄が封 §3 の決め(主 = sonnet・thinking between_tools・昇順 / 副 = haiku・disabled・降順)と違う")
    f = rec[u"呼び出しの形"]
    if f[u"max_tokens"] != MS.MAX_TOKENS or f[u"max_tokens"] != 100 or f[u"temperature"] != u"送らない" or f[u"system"] != u"無し(user の 1 message)":
        out.append(u"記録の呼び出しの形が封 §3 の決め(max_tokens 100・temperature 送らない・system 無し)と違う")
    p = rec[u"指示文の型(封 §2-2)"]
    if p[u"字"] != MS.PROMPT_TEMPLATE or p[u"sha256"] != MS.sha256_text(MS.PROMPT_TEMPLATE) or p[u"置き換える所"] != [u"{HEADING}", u"{PREV}", u"{ROW}", u"{CANDS}"]:
        out.append(u"記録の指示文の型が script の字と違う")
    m = rec[u"費用"]
    if (m[u"上限 USD"], m[u"単価 入力 USD / M tokens"], m[u"単価 出力 USD / M tokens"]) != (CAP_USD, PRICE_IN, PRICE_OUT):
        out.append(u"記録の費用の欄(上限 5・単価 5 / 25)が封 §3 と違う")
    return out


def record_clean_problems(c):
    text = json.dumps(c.rec, ensure_ascii=False)
    out = []
    try:
        MS.check_text(c.rec, text)
    except SystemExit:
        out.append(u"記録の検査(欄・形・file の名・日付・鍵らしい字)が止める")
    except Exception as exc:                    # noqa: BLE001  script の Stop など
        out.append(u"記録の検査が止める: %s" % type(exc).__name__)
    if WG.DOCID_FORM.search(re.sub(r"[0-9a-fA-F]{32,}", u"", text)) or WG.ECODE_FORM.search(text):
        out.append(u"記録に docid か EDINET コードの形が在る")
    if c.rec.get(u"key_leaks") != []:
        out.append(u"記録の key_leaks が空でない")
    for r in c.rec[u"行"]:
        for x in r:
            if isinstance(x, str) and x not in (u"A", u"W") + LABS + KINDS and not re.match(r"^[0-9a-f]{64}$", x):
                out.append(u"記録の行に決めの語・sha256 以外の字が在る")
                break
    return out


def bound_problems(c):
    out = [u"封に境の字が無い: %s" % p for p in BOUND_SEAL_PHRASES if p not in c.seal]
    sec5 = section(c.seal, u"## §5 ", u"## §6 ")
    rows = [ln for ln in sec5.splitlines() if re.match(r"^\| XD0-\d", ln)]
    if len(rows) != 11:
        out.append(u"封 §5 の表の行が 11 でない")
    for k, ph in SEAL_ROW_BOUND.items():
        ln = [r for r in rows if r.startswith(u"| %s" % k + u" ") or r.startswith(u"| %s(" % k)]
        if len(ln) != 1 or ph not in ln[0]:
            out.append(u"封 §5 の %s の行に境の字(%s)が無い" % (k, ph))
    return out


# ======================================================================================================
# c 当たり外れの決め直し
def judge(D):
    u"""封 §5 の境(整数・分数で)から XD0-1〜XD0-11 を決め直す。値は (状態, 文書の判定の欄の字)。状態は 当たり・外れ・判定しない。"""
    A, W = D[K_TALLY][u"類 A"], D[K_TALLY][u"類 W"]
    band7 = D[K_TALLY][u"類 A を候補の数の帯で分けた"][u"候補 7 以上"]
    kinds = D[K_TALLY][u"類 A を計算書の種類で分けた"]
    out = od()
    ok = A[u"主の席の札"][L_OK]
    if ok < 245:
        out[u"XD0-1"] = (u"外れ", u"外れ(下に。境まで %d 行)" % (245 - ok))
    elif ok > 310:
        out[u"XD0-1"] = (u"外れ", u"外れ(上に。境まで %d 行)" % (ok - 310))
    else:
        out[u"XD0-1"] = (u"当たり", u"当たり")
    p2 = A[u"P2(2 席の一致)"][u"通した行"]
    out[u"XD0-2"] = (u"当たり", u"当たり") if p2 >= 228 else (u"外れ", u"外れ(境まで %d 行)" % (228 - p2))
    wr = A[u"P2(2 席の一致)"][u"誤って通した行"]
    if wr == 0:
        out[u"XD0-3"] = (u"外れ", u"外れ(下に。0 行)")
    elif 100 * wr > 5 * p2:
        out[u"XD0-3"] = (u"外れ", u"外れ(上に)")
    else:
        out[u"XD0-3"] = (u"当たり", u"当たり(下の境 0 行まで %d 行)" % wr)
    bad, stopped = A[u"主の席が誤の行"], A[u"主の席が誤の行のうち P2 が止めた行"]
    if bad <= 9:
        out[u"XD0-4"] = (u"判定しない", u"判定しない(封の決め: 主の席の「誤」が 9 行以下)")
    else:
        out[u"XD0-4"] = (u"当たり", u"当たり") if 2 * stopped >= bad else (u"外れ", u"外れ")
    wz = W[u"主の席の札"][L_ZERO]
    out[u"XD0-5"] = (u"当たり", u"当たり") if wz <= 20 else (u"外れ", u"外れ")
    w2 = W[u"P2(2 席の一致)"][u"通した行"]
    out[u"XD0-6"] = (u"当たり", u"当たり") if w2 >= 34 else (u"外れ", u"外れ(境まで %d 行)" % (34 - w2))
    b_rows, b_ok = band7[u"行"], band7[u"主の席の札"][L_OK]
    if b_rows and 100 * b_ok >= 70 * b_rows:
        lo = -(-70 * b_rows // 100)                 # 70% 以上になる最小の行数
        out[u"XD0-7"] = (u"当たり", u"当たり(%d 行なら 70%% を割る。境まで %d 行)" % (lo - 1, b_ok - (lo - 1)))
    else:
        out[u"XD0-7"] = (u"外れ", u"外れ")
    nk, wk = kinds[u"種類なし"], [kinds[k] for k in KINDS_WITH]
    n_rows, n_ok = nk[u"行"], nk[u"主の席の札"][L_OK]
    w_rows, w_ok = sum(x[u"行"] for x in wk), sum(x[u"主の席の札"][L_OK] for x in wk)
    hit8 = bool(n_rows and w_rows and Fraction(w_ok, w_rows) - Fraction(n_ok, n_rows) >= Fraction(1, 10))
    out[u"XD0-8"] = (u"当たり", u"当たり") if hit8 else (u"外れ", u"外れ")
    sub = A[u"副の席の札"][L_OK]
    out[u"XD0-9"] = (u"当たり", u"当たり") if ok - sub >= 10 else (u"外れ", u"外れ")
    none = A[u"主の席の札"][L_NONE] + W[u"主の席の札"][L_NONE]
    out[u"XD0-10"] = (u"当たり", u"当たり") if none <= 5 else (u"外れ", u"外れ")
    usd = D[K_PRED][u"XD0-11 使った額 USD(試しを含む全部)"]
    out[u"XD0-11"] = (u"当たり", u"当たり") if Fraction(str(usd)) <= 3 else (u"外れ", u"外れ")
    return out


def counts(j):
    return tuple(sum(1 for v in j.values() if v[0] == s) for s in (u"当たり", u"外れ", u"判定しない"))


def fires(D):
    u"""封 §5 の「先に自分の欠陥を疑う条件」を封の字のまま 4 つに分けた発火: (正が 130 行以下・0 が類 A の半分を超える[主の席だけ]・[副の席も入れて]・答えなしが 40 行以上・P2 が通した行が 300 行以上で誤 0)。"""
    A, W = D[K_TALLY][u"類 A"], D[K_TALLY][u"類 W"]
    n = A[u"行"]
    return (A[u"主の席の札"][L_OK] <= 130, 2 * A[u"主の席の札"][L_ZERO] > n, 2 * max(A[u"主の席の札"][L_ZERO], A[u"副の席の札"][L_ZERO]) > n,
            A[u"主の席の札"][L_NONE] + W[u"主の席の札"][L_NONE] >= 40, A[u"P2(2 席の一致)"][u"通した行"] >= 300 and A[u"P2(2 席の一致)"][u"誤って通した行"] == 0)


def pred_cells(D):
    A, W = D[K_TALLY][u"類 A"], D[K_TALLY][u"類 W"]
    band7 = D[K_TALLY][u"類 A を候補の数の帯で分けた"][u"候補 7 以上"]
    kinds = D[K_TALLY][u"類 A を計算書の種類で分けた"]
    nk, wk = kinds[u"種類なし"], [kinds[k] for k in KINDS_WITH]
    n_rows, n_ok = nk[u"行"], nk[u"主の席の札"][L_OK]
    w_rows, w_ok = sum(x[u"行"] for x in wk), sum(x[u"主の席の札"][L_OK] for x in wk)
    p2 = A[u"P2(2 席の一致)"]
    return od([
        (u"XD0-1", u"%d 行" % A[u"主の席の札"][L_OK]), (u"XD0-2", u"%d 行" % p2[u"通した行"]),
        (u"XD0-3", u"%d 行・%d 行のうち %s%%" % (p2[u"誤って通した行"], p2[u"通した行"], pct(p2[u"誤って通した行"], p2[u"通した行"]))),
        (u"XD0-4", u"主の席の「誤」は %d 行・うち P2 が止めたのは %d 行" % (A[u"主の席が誤の行"], A[u"主の席が誤の行のうち P2 が止めた行"])),
        (u"XD0-5", u"%d 行" % W[u"主の席の札"][L_ZERO]), (u"XD0-6", u"%d 行" % W[u"P2(2 席の一致)"][u"通した行"]),
        (u"XD0-7", u"%d 行のうち %d 行・%s%%" % (band7[u"行"], band7[u"主の席の札"][L_OK], pct(band7[u"主の席の札"][L_OK], band7[u"行"]))),
        (u"XD0-8", u"種類なし %d 行のうち %d 行・%s%%、種類の在る行 %d 行のうち %d 行・%s%%、差 %.2f ポイント" % (
            n_rows, n_ok, pct(n_ok, n_rows), w_rows, w_ok, pct(w_ok, w_rows), 100.0 * w_ok / w_rows - 100.0 * n_ok / n_rows)),
        (u"XD0-9", u"副 %d 行・主 %d 行・差 %d 行" % (A[u"副の席の札"][L_OK], A[u"主の席の札"][L_OK], A[u"主の席の札"][L_OK] - A[u"副の席の札"][L_OK])),
        (u"XD0-10", u"%d 行" % (A[u"主の席の札"][L_NONE] + W[u"主の席の札"][L_NONE])), (u"XD0-11", u"%s USD" % D[K_PRED][u"XD0-11 使った額 USD(試しを含む全部)"])])


def verdict_problems(c):
    D = derive(c.rec)
    j = judge(D)
    cells = pred_cells(D)
    out = []
    rows = {}
    for ln in c.doc.splitlines():
        m = re.match(r"^\| (XD0-\d+)(?:\(主\))? \|(.*)\|$", ln)
        if m:
            rows[m.group(1)] = [x.strip() for x in m.group(2).split(u"|")]
    if sorted(rows) != sorted(IDS) or list(j) != list(IDS):
        return [u"文書 §1 の表の行が XD0-1〜XD0-11 でない"]
    for k, cs in rows.items():
        if len(cs) != 3:
            out.append(u"%s の行の欄の数が違う" % k)
            continue
        if SEAL_ROW_BOUND[k] not in cs[0]:
            out.append(u"%s の予測の欄に封の境の字(%s)が無い" % (k, SEAL_ROW_BOUND[k]))
        if cs[1] != cells[k]:
            out.append(u"%s の実測の字が記録から組んだ字と違う: %s" % (k, cs[1]))
        if cs[2] != j[k][1]:
            out.append(u"%s の判定が決め直した判定と違う: %s(決め直し: %s)" % (k, cs[2], j[k][1]))
    hit, miss, none = counts(j)
    if u"- 当たり %d・外れ %d・判定しない %d。" % (hit, miss, none) not in c.doc.splitlines():
        out.append(u"文書の件数の行が決め直した件数と違う")
    head = c.doc.split(u"## §1")[0]
    if u"判定した %d 本は 当たり %d・外れ %d(XD0-4 は封の決めで判定しない)" % (hit + miss, hit, miss) not in head:
        out.append(u"文書の頭の件数が決め直した件数と違う")
    if (u"主の予測 XD0-3 は当たりだが、対の XD0-2 が大きく外れた。" in head) != (j[u"XD0-3"][0] == u"当たり" and j[u"XD0-2"][0] == u"外れ"):
        out.append(u"文書の頭の「主の予測 XD0-3 は当たりだが、対の XD0-2 が外れた」が決め直した判定と合わない")
    sec1 = section(c.doc, u"## §1 ", u"## §2 ")
    up = u"次の便の候補として**上げない**" in sec1
    cond = j[u"XD0-2"][0] == u"当たり" and j[u"XD0-3"][0] == u"当たり"
    if up == cond:
        out.append(u"封 §5 の読み方の決め(XD0-2 と XD0-3 がどちらも当たったときだけ次の便の候補)と文書 §1 が合わない")
    if not cond and u"XD0-2 が外れたので" not in sec1 and j[u"XD0-2"][0] == u"外れ":
        out.append(u"文書 §1 が「XD0-2 が外れたので」と書いていない")
    six = j[u"XD0-6"][0] == u"当たり"
    if six != (u"別の止めが要る」と読む" in sec1 or u"別の止めが要る。" in sec1):
        out.append(u"封 §5 の読み方の決め(XD0-6 が当たったら別の止めが要る)と文書 §1 が合わない")
    if (not six) and u"XD0-6 は外れたが、類 W で %d 行を誤って通しており、「候補の中に答えが無い行が席の一致で止まる」とは読めない" % D[K_TALLY][u"類 W"][u"P2(2 席の一致)"][u"誤って通した行"] not in sec1:
        out.append(u"文書 §1 の XD0-6 の読みが記録から組んだ字と違う")
    # XD0-3 が上に外れたとき
    if j[u"XD0-3"][1] == u"外れ(上に)" and u"2 席の一致だけでは通せない" not in c.doc:
        out.append(u"XD0-3 が上に外れたのに「2 席の一致だけでは通せない」と読んでいない")
    if j[u"XD0-3"][1] != u"外れ(上に)" and u"2 席の一致だけでは通せない" in c.doc.replace(u"「2 席の一致だけでは通せない」と読む", u""):
        out.append(u"XD0-3 が上に外れていないのに「2 席の一致だけでは通せない」と書いている")
    return out


def suspect_problems(c):
    u"""封 §5 の「先に自分の欠陥を疑う条件」: 封の字のままの条件ごとの発火を決め直し、記録の欄・文書の言い切り(両方の読み)と合わせる。"""
    D = derive(c.rec)
    f = fires(D)
    A, W = D[K_TALLY][u"類 A"], D[K_TALLY][u"類 W"]
    s = c.rec[K_SUSPECT]
    out = []
    if (s[u"条件に当たる(正が 130 行以下)"], s[u"条件に当たる(0 が類 A の半分を超える)"], s[u"条件に当たる(答えなしが 40 行以上)"], s[u"条件に当たる(P2 が通した行が 300 行以上で誤 0)"]) != (f[0], f[1], f[3], f[4]):
        out.append(u"記録の自己点検の欄が決め直した発火(主の席だけの読み)と違う")
    head = c.doc.split(u"## §1")[0]
    n = A[u"行"]
    zm, zs = A[u"主の席の札"][L_ZERO], A[u"副の席の札"][L_ZERO]
    none = A[u"主の席の札"][L_NONE] + W[u"主の席の札"][L_NONE]
    if f[3] != (u"の「先に自分の欠陥を疑う条件」に当たった(答えなしが 40 行以上)。" in head):
        out.append(u"文書の頭の「答えなしが 40 行以上に当たった」が決め直した発火と合わない")
    if f[3] and (u"主の席の答えなしは、送った %d 行のうち %d 行。" % (A[u"行"] + W[u"行"], none)) not in head:
        out.append(u"文書の頭の「主の席の答えなしは、送った N 行のうち M 行」が記録の数と違う")
    two = (u"副の席の「0」は類 A の %d 行のうち %d 行で、半分(%d 行)を超える。" % (n, zs, n // 2)) in head
    if f[2] != two:
        out.append(u"文書の頭の「副の席の 0 が類 A の半分を超える」が決め直した発火(副の席も入れた読み)と合わない")
    main_line = u"**主の席だけで読むと %d 行で当たらない(記録の欄はこの読みで false)。副の席も入れて読むと当たる。**" % zm
    if (not f[1] and f[2]) != (main_line in head):
        out.append(u"文書の頭の「主の席だけなら当たらない・副を入れると当たる」が決め直した発火と合わない")
    if (f[1], f[2]) != (False, True):
        out.append(u"主の席だけは当たらず副の席も入れると当たる、という文書の書く組と違う")
    if f[0] or f[4]:
        out.append(u"「正が 130 行以下」「P2 が 300 行以上で誤 0」が当たっている(文書は当たらないと書く)")
    return out


# ======================================================================================================
def sec3_free_line(doc):
    return [ln for ln in doc.splitlines() if ln.startswith(SEC3_FREE_START)]


def expected_lines(c):
    D = derive(c.rec)
    T = D[K_TALLY]
    A, W = T[u"類 A"], T[u"類 W"]
    out = []
    out.append(u"送った行は %d 行(類 A %d・類 W %d)。席は主 `claude-sonnet-5-5`(候補は昇順)・副 `claude-haiku-5-5`(候補は降順)。" % (A[u"行"] + W[u"行"], A[u"行"], W[u"行"]))

    def labs(name, cl, seat, key):
        x = cl[key]
        out.append(u"| %s | %s | %d | %d | %d | %d |" % (name, seat, x[L_OK], x[L_BAD], x[L_ZERO], x[L_NONE]))
    for nm, cl in ((u"類 A(%d 行)" % A[u"行"], A), (u"類 W(%d 行)" % W[u"行"], W)):
        labs(nm, cl, u"主", u"主の席の札")
        labs(nm, cl, u"副", u"副の席の札")
    for nm, cl in ((u"類 A", A), (u"類 W", W)):
        for rule, key in ((u"P1(主の席だけ)", u"P1(主の席だけ)"), (u"P2(2 席の一致)", u"P2(2 席の一致)")):
            x = cl[key]
            out.append(u"| %s | %s | %d | %d | %d | %d |" % (nm, rule, x[u"通した行"], x[u"誤って通した行"], x[u"止めた行"], x[u"止めた行のうち主の席が正"]))
    L = D[K_LINES]
    out.append(u"- 何もしなかったら: でたらめに 1 つ選んだときの正の数の期待は %s 行・昇順の頭の候補を選んだときの正は %d 行。" % (
        L[u"何もしなかったら: でたらめに 1 つ選んだときの正の数の期待(行ごとの 1 ÷ 候補の数の和)"], L[u"何もしなかったら: 昇順の頭の候補を選んだときの正の数"]))
    perfect = L[u"完璧に動いたら: P2 が通す類 A の行・誤って通す行・類 W で止める行"]
    now = L[u"今: P2 が通した類 A の行・誤って通した行・類 W で止めた行"]
    out.append(u"- 完璧に動いたら: P2 が類 A の %d 行を通して誤 %d・類 W の %d 行を止める。" % (perfect[u"類 A を通す"], perfect[u"誤って通す"], perfect[u"類 W を止める"]))
    out.append(u"- 今: P2 が通した類 A は %d 行・誤って通したのは %d 行・類 W で止めたのは %d 行。" % (now[u"類 A を通した"], now[u"誤って通した"], now[u"類 W を止めた"]))
    for grp in (u"類 A を候補の数の帯で分けた", u"類 A を計算書の種類で分けた"):
        for k, x in T[grp].items():
            if x[u"行"] == 0:
                continue
            lab = {u"候補 2": u"候補 2", u"候補 3〜6": u"候補 3〜6", u"候補 7 以上": u"候補 7 以上"}.get(k, k)
            out.append(u"| %s | %d | %d | %d | %d | %d | %d | %d |" % (lab, x[u"行"], x[u"主の席の札"][L_OK], x[u"主の席の札"][L_BAD], x[u"主の席の札"][L_ZERO], x[u"主の席の札"][L_NONE],
                                                               x[u"P2(2 席の一致)"][u"通した行"], x[u"P2(2 席の一致)"][u"誤って通した行"]))
    zero_kinds = [k for k, x in T[u"類 A を計算書の種類で分けた"].items() if x[u"行"] == 0]
    out.append(u"類 A を計算書の種類で分けた(%sは 0 行):" % u"・".join(zero_kinds))
    C = D[K_CALLS]
    for tag in (u"主", u"副"):
        x = C[tag]
        maxt = [d for d in c.rec[u"呼び出し"] if d[J_SEAT] == tag and d[J_STOP] == u"max_tokens"]
        out.append(u"| %s | %d | %d | %d | %d | %d | %d | %s |" % (tag, x[u"呼び出しの数(HTTP の再試行を除く。中断した呼び出しを除く)"], x[u"うち 1 回目"], x[u"答えのやり直し(封 §2-3)"], len(maxt),
                                                         x[u"入力 token の合計"], x[u"出力 token の合計"], x[u"USD 合計"]))
    tr = D[K_TRIAL][u"呼び出し"]
    out.append(u"- 本番の合計は %s USD・試しの %d 回は %s USD・合わせて %s USD。" % (C[u"USD の全部"], len(c.rec[u"試しの呼び出し"]), tr[u"USD の全部"], D[K_PRED][u"XD0-11 使った額 USD(試しを含む全部)"]))
    return out


def expected_fragments(c):
    u"""主な主張の文(断片)。数は記録から導いた値を入れる。"""
    D = derive(c.rec)
    T = D[K_TALLY]
    A, W = T[u"類 A"], T[u"類 W"]
    am, asub, wm, wsub = A[u"主の席の札"], A[u"副の席の札"], W[u"主の席の札"], W[u"副の席の札"]
    p2a, p2w = A[u"P2(2 席の一致)"], W[u"P2(2 席の一致)"]
    n_all = A[u"行"] + W[u"行"]
    none = am[L_NONE] + wm[L_NONE]
    read_n = A[u"行"] - am[L_NONE]
    j = judge(D)
    hit, miss, unj = counts(j)
    usd = D[K_PRED][u"XD0-11 使った額 USD(試しを含む全部)"]
    kinds = T[u"類 A を計算書の種類で分けた"]
    band7 = T[u"類 A を候補の数の帯で分けた"][u"候補 7 以上"]
    nk = kinds[u"種類なし"]
    f = []
    f.append(u"**有料。使った額は試しを含めて %s USD(上限 %d USD)。**" % (usd, CAP_USD))
    f.append(u"主の席の答えなしは、送った %d 行のうち %d 行。**" % (n_all, none))
    f.append(u"84 行は 1 回目もやり直しも `max_tokens` で終わっている(§3)".replace(u"84", str(none)))
    f.append(u"類 A の主の席の「正」%d 行は、答えなし %d 行を「正でない」に数えた数。答えが読めた %d 行(%d − %d)の中では 正 %d・誤 %d・0 が %d。" % (
        am[L_OK], am[L_NONE], read_n, A[u"行"], am[L_NONE], am[L_OK], am[L_BAD], am[L_ZERO]))
    f.append(u"判定した %d 本は 当たり %d・外れ %d(XD0-4 は封の決めで判定しない)。" % (hit + miss, hit, miss))
    f.append(u"**2 席の一致(P2)は、類 A の %d 行のうち %d 行しか通さなかった。** 通した %d 行のうち誤りは %d 行(%s%%)。止めた %d 行のうち %d 行は主の席が正だった行。" % (
        A[u"行"], p2a[u"通した行"], p2a[u"通した行"], p2a[u"誤って通した行"], pct(p2a[u"誤って通した行"], p2a[u"通した行"]), p2a[u"止めた行"], p2a[u"止めた行のうち主の席が正"]))
    f.append(u"通す行が少ないのは、副の席が %d 行のうち %d 行で「0」と答えたことと、主の席の答えなし %d 行による。" % (A[u"行"], asub[L_ZERO], am[L_NONE]))
    f.append(u"**候補の中に答えが無い類 W の %d 行で、P2 は %d 行を誤って通した。** 止めたのは %d 行。「完璧に動いたら」の %d 行に届かない。" % (W[u"行"], p2w[u"誤って通した行"], p2w[u"止めた行"], W[u"行"]))
    f.append(u"副の席の「0」は類 A の %d 行のうち %d 行で、半分(%d 行)を超える。" % (A[u"行"], asub[L_ZERO], A[u"行"] // 2))
    f.append(u"**主の席だけで読むと %d 行で当たらない(記録の欄はこの読みで false)。副の席も入れて読むと当たる。**" % am[L_ZERO])
    f.append(u"- XD0-7・XD0-8 は当たりだが、主の席の答えなしが帯と種類に偏って入っている(候補 7 以上の %d 行に %d 行・種類なしの %d 行に %d 行)。" % (
        band7[u"行"], band7[u"主の席の札"][L_NONE], nk[u"行"], nk[u"主の席の札"][L_NONE]))
    f.append(u"**種類なしの行の「正」の率が低いことには、答えなしが混ざっている(種類なしの %d 行のうち答えなし %d 行)。席が選べなかったことと切れたことを分けられない。**" % (nk[u"行"], nk[u"主の席の札"][L_NONE]))
    f.append(u"- 当たり %d・外れ %d・判定しない %d。" % (hit, miss, unj))
    f.append(u"XD0-6 は外れたが、類 W で %d 行を誤って通しており、「候補の中に答えが無い行が席の一致で止まる」とは読めない。" % p2w[u"誤って通した行"])
    f.append(u"言えること: 候補が 2 つ以上残る行(類 A)の 8 行に 1 行(%d 行)で、主の席が答えを返した %d 行のうち、提出済みの書類の要素と同じ要素を選んだのは %d 行・別の候補を選んだのは %d 行だった。" % (
        A[u"行"], read_n, am[L_OK], am[L_BAD]))
    f.append(u"2 席の一致で通した %d 行のうち誤りは %d 行だった。" % (p2a[u"通した行"], p2a[u"誤って通した行"]))
    f.append(u"言えること: 2 席の一致は、通す行が少なすぎた(%d 行のうち %d 行)。副の席は半分を超える行で「0」と答えた。" % (A[u"行"], p2a[u"通した行"]))
    f.append(u"この 2 席の組では、人が見る行は %d 行から %d 行に減るが、封の予測(%d 行以上を通す)には届かず、通した %d 行にも誤りが %d 行在る。" % (
        A[u"行"], p2a[u"止めた行"], 228, p2a[u"通した行"], p2a[u"誤って通した行"]))
    f.append(u"言えること: 候補の中に答えが無い行(類 W)で、主の席は %d 行のうち %d 行で、副の席は %d 行で、在る候補のどれかを選んだ。2 席の一致でも %d 行が通る。" % (
        W[u"行"], wm[L_BAD], wsub[L_BAD], p2w[u"誤って通した行"]))
    f.append(u"言えないこと: 主の席が切れなかったら何行で正しかったか(%d 行は測れていない)。" % none)
    return f


def sanity_problems(c):
    u"""文書の言い切りが記録の数に合う。§3 の導ける数(記録の呼び出しから導く)も見る。"""
    rec = c.rec
    D = derive(rec)
    T = D[K_TALLY]
    A, W = T[u"類 A"], T[u"類 W"]
    out = []
    rows, calls = rec[u"行"], rec[u"呼び出し"]
    none_rows = [i for i, r in enumerate(rows) if r[I_M] == L_NONE]
    if len(none_rows) != A[u"主の席の札"][L_NONE] + W[u"主の席の札"][L_NONE]:
        out.append(u"主の席の答えなしの行の数が札の数と違う")
    main_none = [x for x in calls if x[J_SEAT] == u"主" and x[J_ROW] in set(none_rows)]
    if not (len(main_none) == 2 * len(none_rows) and all(x[J_STOP] == u"max_tokens" and x[J_TOUT] == 100 and not x[J_OK] for x in main_none)):
        out.append(u"文書 §3 の「答えなしの全部が 1 回目もやり直しも max_tokens で終わり出力は 100 token」が記録の呼び出しと合わない")
    short = sum(1 for x in calls if x[J_SEAT] == u"主" and x[J_STOP] == u"end_turn" and x[J_TOUT] < 10)
    if u"主の席の `end_turn` の返事のうち %d 本は出力が 10 token 未満" % short not in c.doc:
        out.append(u"文書 §3 の「end_turn の返事のうち N 本は出力が 10 token 未満」が記録の呼び出しから数えた値と違う")
    trial_main = [x[J_TOUT] for x in rec[u"試しの呼び出し"] if x[J_SEAT] == u"主"]
    if not any(t >= 10 for t in trial_main) or u"出力 %d token の返事が在った" % [t for t in trial_main if t >= 10][0] not in c.doc:
        out.append(u"文書の頭の「試しの時点で主の席は説明を書いていた(出力 N token の返事)」が試しの呼び出しと合わない")
    if u"788 本" not in c.doc or rec[u"回数"][u"呼び出しの予定(本番)"] != 788:
        out.append(u"§3 の「送った指示文 788 本」が記録の回数と合わない")
    if u"394 行の札に不一致は 0 行" not in c.doc or len(rows) != 394:
        out.append(u"§3 の「394 行の札に不一致は 0 行」の 394 が記録の行と合わない")
    if u"主の席の「正」%d 行を 1 行ずつ" % A[u"主の席の札"][L_OK] not in c.doc:
        out.append(u"§3 の「主の席の「正」N 行を 1 行ずつ」が記録の札と合わない")
    free = sec3_free_line(c.doc)
    if len(free) != 1:
        out.append(u"§3 の記録に欄の無い読みの 1 行が 1 つでない")
    else:
        ln = free[0]
        if (u"切れた返事の中に読める" not in ln) or (u"誤って通した行は %d 行のまま" % A[u"P2(2 席の一致)"][u"誤って通した行"]) not in ln:
            out.append(u"§3 の記録に欄の無い読みの 1 行の「誤って通した行は N 行のまま」が記録と合わない")
        if (u"類 A の主の席の「正」は %d 行" % (A[u"主の席の札"][L_OK] + 4)) not in ln or u"この 4 行を緩く読むと 4 行とも主の席は「正」" not in ln:
            out.append(u"§3 の記録に欄の無い読みの 1 行の 4 行・226 の関係(正 + 4)が合わない")
        for tok in (u"226",):
            rest = u"\n".join(x for x in c.doc.splitlines() if x != ln)
            if re.search(r"(?<![0-9])%s(?![0-9])" % tok, rest):
                out.append(u"記録に縛らない数 %s が §3 のその 1 行の外に出ている" % tok)
    if A[u"行"] != 326 or W[u"行"] != 68:
        out.append(u"類 A・類 W の行の数が 326・68 でない")
    if usd_all_of(rec) != D[K_PRED][u"XD0-11 使った額 USD(試しを含む全部)"] or rec[u"費用"][u"使った額 USD(試しを含む)"] != usd_all_of(rec):
        out.append(u"使った額が記録の呼び出しの和と違う")
    if u"%s USD" % D[K_PRED][u"XD0-11 使った額 USD(試しを含む全部)"] not in c.doc:
        out.append(u"文書が書く使った額が記録と違う")
    # 文書 §1 の読み方の決めの 2 つ(XD0-7・XD0-8 の「当たり」と答えなしの偏り)
    j = judge(D)
    if not (j[u"XD0-7"][0] == u"当たり" and j[u"XD0-8"][0] == u"当たり"):
        out.append(u"「XD0-7・XD0-8 は当たり」が決め直した判定と違う")
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


def float_str(x):
    s = (u"%.6f" % x).rstrip(u"0").rstrip(u".")
    return s


def nums_in(o, acc):
    if isinstance(o, dict):
        for v in o.values():
            nums_in(v, acc)
    elif isinstance(o, list):
        for v in o:
            nums_in(v, acc)
    elif isinstance(o, bool) or o is None:
        return
    elif isinstance(o, float):
        acc.add(float_str(o))
        acc.add(u"%.1f" % o)
    elif isinstance(o, int):
        acc.add(str(o))
    elif isinstance(o, str):
        for m in re.finditer(r"\d+(?:\.\d+)?", o):
            acc.add(m.group(0))


def derived_numbers(c):
    rec = c.rec
    D = derive(rec)
    out = set()
    for k in SECTION_KEYS:
        nums_in(D[k], out)
    for k in (u"回数", u"費用", u"呼び出しの形"):
        nums_in(rec[k], out)
    for k in (u"段 3 の類の数(開発)", u"段 3 の類の数(本番)"):
        nums_in(rec[K_WIRE][k], out)
    nums_in([rec[K_WIRE][k] for k in rec[K_WIRE] if not isinstance(rec[K_WIRE][k], dict)], out)
    A, W = D[K_TALLY][u"類 A"], D[K_TALLY][u"類 W"]
    out.add(str(A[u"行"] - A[u"主の席の札"][L_NONE]))                       # 答えが読めた行
    out.add(str(A[u"行"] // 2))                                           # 類 A の半分
    out.add(str(A[u"主の席の札"][L_NONE] + W[u"主の席の札"][L_NONE]))        # 主の席の答えなし(全部)
    out.add(str(A[u"行"] + W[u"行"]))
    out.add(str(sum(1 for x in rec[u"呼び出し"] if x[J_SEAT] == u"主" and x[J_STOP] == u"end_turn" and x[J_TOUT] < 10)))
    out.add(str(sum(1 for x in rec[u"呼び出し"] if x[J_SEAT] == u"主" and x[J_STOP] == u"max_tokens")))
    out.add(str(sum(1 for x in rec[u"呼び出し"] if x[J_SEAT] == u"副" and x[J_STOP] == u"max_tokens")))
    for x in rec[u"試しの呼び出し"]:
        if x[J_SEAT] == u"主" and x[J_TOUT] >= 10:
            out.add(str(x[J_TOUT]))
    j = judge(D)
    for k, v in j.items():
        for m in re.finditer(r"\d+(?:\.\d+)?", v[1]):
            out.add(m.group(0))
    for k, v in pred_cells(D).items():
        for m in re.finditer(r"\d+(?:\.\d+)?", v):
            out.add(m.group(0))
    out |= set(BOUND_NUMBERS)
    return out


def doc_number_tokens(line):
    line = re.sub(r"XD0-\d+", u" ", line)
    line = re.sub(r"X[A-Z]\d", u" ", line)
    return WG.doc_number_tokens(line)


def doc_number_problems(c):
    allowed = set(STRUCTURAL) | derived_numbers(c)
    free = set(sec3_free_line(c.doc))
    out = []
    for i, ln in enumerate(c.doc.splitlines(), 1):
        if ln in free:
            continue                                   # §3 の記録に欄の無い読みの 1 行(数は記録に縛らない。その数が他の行に出ていないことは sanity が見る)
        for tok in doc_number_tokens(re.sub(r"^\d+\. ", u"", ln)):
            if tok.replace(u",", u"") not in allowed:
                out.append(u"文書の %d 行目の数 %s が記録から組んだ数の外: %s" % (i, tok, ln[:30]))
    return out


def sec3_problems(c):
    u"""§3 は記録に欄の無い読みの節。見出しの字・§3 の中の 3 桁以上の数と % は「記録の呼び出しから導いた数」か「記録に縛らない 1 行」だけ。"""
    s = section(c.doc, u"## §3 ", u"## §4 ")
    out = []
    if u"記録に欄の無い読み" not in s.splitlines()[0]:
        out.append(u"§3 の見出しが「記録に欄の無い読み」でない")
    if u"出所は監査の席が置き場の返事の字を読んだ結果" not in s.splitlines()[0]:
        out.append(u"§3 の見出しが出所を書いていない")
    D = derive(c.rec)
    allowed = derived_numbers(c)
    free = set(sec3_free_line(c.doc))
    for ln in s.splitlines():
        if ln in free:
            continue
        left = re.sub(r"`[^`]*`", u" ", ln)
        for tok in re.findall(r"\d{3,}(?:\.\d+)?", left):
            if tok not in allowed:
                out.append(u"§3 の 3 桁以上の数 %s が記録から導いた数の外" % tok)
        if u"%" in left or u"％" in left:
            out.append(u"§3 に % が在る(記録から導く率は §3 に書かない)")
    for p in (u"思考の block が token を食ったのではなく", u"script の欠陥ではない", u"戻し・並びの向き・答えの読み方の取り違えは見つからなかった", u"欠陥は読み方でなく"):
        if p not in s:
            out.append(u"§3 に字が無い: %s" % p)
    if not sec3_free_line(c.doc):
        out.append(u"§3 に記録に縛らない 1 行が無い")
    return out


def affirm_problems(c):
    u"""「作れる」「紙を AI が書ける」「専用の道具が要らない」は、言えないことの引用(「…」の中)にしか無い。引用の在る行には「言えない」か「読まない」か「示していない」が在る。"""
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
    u"""禁止語(「完璧に動いたら」は封が決めた並べる行の名。その字だけは除く)・docID と EDINET コードの形。"""
    text = c.doc.replace(u"完璧に動いたら", u" ")
    out = [u"文書に禁止語: %s" % w for w in FORBIDDEN_WORDS if w in text]
    scan = re.sub(r"\b(?=[0-9]*[a-f])[0-9a-f]{8}\b", u" ", c.doc)
    if DOCID_FORM.search(scan):
        out.append(u"文書に docID の形が在る")
    if ECODE_FORM.search(scan):
        out.append(u"文書に EDINET コードの形が在る")
    return out


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
    (u"sha", sha_problems), (u"recount", recount_problems), (u"clean", record_clean_problems), (u"bound", bound_problems), (u"verdict", verdict_problems), (u"suspect", suspect_problems),
    (u"numbers", doc_number_problems), (u"frag", fragment_problems), (u"sanity", sanity_problems), (u"sec3", sec3_problems),
    (u"affirm", affirm_problems), (u"phrases", phrase_problems), (u"head", head_problems), (u"forbidden", forbidden_problems), (u"commits", doc_commit_problems)])


# ======================================================================================================
def blob_problems(root, prefix, at):
    return WG.blob_problems(root, prefix, at)


def commit_problems(root=REPO):
    u"""文書が書く 3 つの commit が実の履歴と合う: 封は 7bb4fa24 が足し(1 commit)・script と封の門は f119b80c が足し・記録は e066a557 が足した(どれも 1 commit)。"""
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
    out.extend(SG.xg1_pin_problems(root=root))
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
(変異を実行する前に書いた予測。右 = 赤になるべき検査。「整合」= 行と呼び出しの欄はそのままに(または整合して変えて)6 つの欄を数え直し、recount は緑のまま当たり外れ・言い切りだけが変わる)
(約束の側から作った: 「記録の数は行と呼び出しから導ける」「当たり外れは封の境で決まる」「文書の主な主張は記録の数を言う」「1 つの主張に別の主張の数を入れても赤」「禁止の肯定は書かない」「使った額は上限の内で式と合う」)
M1  記録の sha256 の写しを違う値に                                                -> sha
M2  記録の「この script の sha256」を 1 字替える                                  -> sha
M3  記録の限界の欄の 1 行を消す                                                   -> sha
M4  記録の封の commit の欄を 1 字替える                                           -> sha
M5  記録の max_tokens を 100 → 1000                                               -> sha
M6  記録の主の席の thinking を disabled に                                         -> sha
M7  記録の指示文の字の 1 字を替える                                                -> sha
M8  記録の費用の上限を 5 → 50                                                      -> sha
M9  便 XG1 の script の sha256 の欄を 1 字替える                                   -> sha
M10 記録の主の席の model を haiku に                                               -> sha
M11 記録の temperature の欄を 0 に                                                 -> sha
M12 記録の副の席の候補の並びを昇順に                                                -> sha
M13 行 10 の主の席の札を 正 → 誤(群は直さない)                                     -> recount
M14 類 A の行の候補の数を 1 増やす(群は直さない。でたらめの期待が変わる)               -> recount
M15 呼び出し 5 の出力 token を 1 増やす(USD・群は直さない)                           -> recount
M16 呼び出し 5 の USD を 0.000001 増やす(式と合わない)                              -> recount
M17 記録の A の主の席の正を 1 減らす(行は直さない)                                  -> recount
M18 記録の P2 の通した行を 1 増やす                                                -> recount
M19 記録の使った額 USD を 0.01 増やす                                              -> recount
M20 記録の XD0-3 の % を 1.2 → 1.3                                                 -> recount
M21 記録の自己点検の「答えなし 40 行以上」を false に                                -> recount
M22 記録の試しの 10 回の USD の全部を 1 増やす                                      -> recount
M23 行 10 の「2 席が同じ要素を選んだ」を真に(札が合わない)                          -> recount
M24 類 W の行の主の席の札を 正 に(類 W に正は無い)                                  -> recount
M25 答えなしの行の呼び出しの「答えが読めた」を真に                                  -> recount
M26 答えなしの行の 2 回目の呼び出しを消す                                           -> recount
M27 呼び出しの 1 回目が読めたのに 2 回目の呼び出しを足す                            -> recount
M28 呼び出しの stop_reason を max_tokens にして読めたを真のまま                     -> recount
M29 呼び出しの HTTP の状態を 429 に                                                 -> recount
M30 行の欄の列の名を 1 つ替える                                                    -> recount
M31 配線の確認の本番の類 A を 2603 → 2604                                          -> recount
M32 回数の呼び出しの予定を 788 → 789                                               -> recount
M33 試しの行の類を W に                                                            -> recount
M34 行の書類の番号を開発の 5 本の番号に                                             -> recount
M35 記録に docid の欄を足す                                                         -> clean
M36 記録に EDINET コードの形の字を足す                                              -> clean
M37 記録の key_leaks に字を足す                                                     -> clean
M38 行に決めの語でない字を足す                                                      -> clean
M39 記録に鍵らしい字(鍵の形の長い字)を足す                                  -> clean
M40 封の写しから XD0-1 の境の字(245 行以上 310 行以下)を消す                         -> bound
M41 封の写しから「主の席の「誤」が 9 行以下なら判定しない」を消す                    -> bound
M42 封の写しから自己点検の字を消す                                                  -> bound
M43 封の写しから「XD0-2 と XD0-3 がどちらも当たったときだけ」を消す                 -> bound
M44 封の写しから「合わせて 394 行」を消す                                            -> bound
M45 文書の XD0-1 の判定「外れ(下に。境まで 23 行)」を「当たり」に                   -> verdict
M46 文書の XD0-4 の判定「判定しない(…)」を「当たり」に                              -> verdict
M47 文書の XD0-3 の判定を「外れ(上に)」に                                           -> verdict
M48 文書の件数の行 当たり 5・外れ 5・判定しない 1 → 当たり 6・外れ 4・判定しない 1    -> verdict
M49 頭の「判定した 10 本は 当たり 5・外れ 5」を 当たり 6・外れ 4 に                    -> verdict
M50 文書の XD0-1 の実測 222 行 → 224 行                                            -> verdict・frag
M51 文書の XD0-7 の実測 70.6% → 71.6%                                              -> verdict
M52 文書の XD0-8 の差 36.91 → 26.91                                                -> verdict
M53 文書の XD0-2 の予測の欄の「228 行以上」を「229 行以上」に                         -> verdict
M54 文書の XD0-9 の実測の字を主 98 行・副 222 行に入れ替える                         -> verdict
M55 §1 の「次の便の候補として**上げない**」を「上げる」に                            -> verdict
M56 §1 の XD0-6 の読みの 27 行を 41 行に                                            -> verdict・frag
M57 頭の「対の XD0-2 が大きく外れた」を消す                                          -> verdict・head
M58 整合: 主の席の 0・誤の行を 正 に直して XD0-1 が当たり(245 以上)                  -> verdict
M59 整合: 類 A の主の席の答えなしを全部読めた正に直して XD0-1 が上に外れ(311 以上)    -> verdict
M60 整合: P2 が通した類 A を 228 行以上にして XD0-2 が当たり                          -> verdict
M61 整合: 誤って通した類 A を 0 行にして XD0-3 が外れ(下)                             -> verdict
M62 整合: 誤って通した類 A を 5% 超にして XD0-3 が外れ(上)                            -> verdict
M63 整合: 主の席の誤を 10 行以上・P2 が止めたのを半分以上にして XD0-4 が判定する(当たり)  -> verdict
M64 整合: 主の席の誤を増やし P2 が止めたのを半分未満にして XD0-4 が外れ                -> verdict
M65 整合: 類 W の主の席の 0 を 20 行以下にして XD0-5 が当たり                           -> verdict
M66 整合: 類 W で P2 が通す行を 34 行以上にして XD0-6 が当たり                          -> verdict
M67 整合: 候補 7 以上の主の席の正を 2 行減らして XD0-7 が外れ                          -> verdict
M68 整合: 種類なしの主の席の答えなしを読めた正に直して XD0-8 が外れ                    -> verdict
M69 整合: 副の席の正を増やして差を 9 行以下にして XD0-9 が外れ                         -> verdict
M70 整合: 主の席の答えなしを 5 行以下にして XD0-10 が当たり                            -> verdict
M71 整合: 全部の呼び出しの入力 token を 300 増やして使った額を 3 USD 超にして XD0-11 が外れ   -> verdict
M72 整合: 主の席の正を 130 行以下にして自己点検の「正が 130 行以下」が発火               -> verdict・suspect
M73 整合: 主の席の 0 を類 A の半分超にして主の席だけの読みが発火                        -> verdict・suspect
M74 整合: 答えなしを 40 行未満にして「答えなしが 40 行以上」が発火しない                 -> verdict・suspect
M75 整合: P2 が通した類 A を 300 行以上で誤 0 にして発火                                -> verdict・suspect
M76 頭の「答えなしが 40 行以上に当たった」の 84 行を 83 行に                              -> suspect・frag
M77 頭の「副の席の「0」は類 A の 326 行のうち 206 行」を 205 行に                          -> suspect・frag
M78 頭の「主の席だけで読むと 18 行で当たらない」を 17 行に                                -> suspect・frag
M79 頭の「副の席も入れて読むと当たる」を「副の席も入れて読んでも当たらない」に           -> suspect
M80 頭の「(記録の欄はこの読みで false)」を消す                                         -> suspect
M81 文書 §2 の席の札の表の 類 A 主の 222 を 221 に                                      -> frag・numbers (外れ: 221 は numbers を通る。frag だけで赤)
M82 文書 §2 の P2 の行の 83 を 82 に                                                    -> frag
M83 文書 §2 の呼び出しの表の出力 token 29616 を 29617 に                                 -> frag・numbers
M84 文書 §2 の使った額 2.87673 を 2.87674 に(全部の箇所)                                 -> frag・numbers・sanity
M85 文書 §2 の「何もしなかったら」の 99.9546 を 99.9547 に                                -> frag・numbers
M86 文書 §2 の帯の表の「候補 2 | 146」の主の正 100 を 101 に                              -> frag
M87 文書 §2 の種類の表の「種類なし | 49」を 50 に                                        -> frag・numbers (外れ: 50 は numbers を通る)
M88 頭の「P2 は 27 行を誤って通した」を 41 行に(別の主張の数)                              -> frag (外れ: numbers は黙る)
M89 頭の「通した 83 行のうち誤りは 1 行」の 83 を 243 に(別の主張の数)                     -> frag
M90 頭の「答えが読めた 246 行(326 − 80)」の 246 を 245 に                                 -> frag・numbers
M91 §4 の「答えを返した 246 行のうち 222 行・6 行」の 222 と 6 を入れ替える                 -> frag
M92 §4 の「類 W で主の席は 68 行のうち 35 行」の 35 を 32 に(別の主張の数)                  -> frag
M93 §4 の「84 行は測れていない」を 80 行に                                              -> frag
M94 文書に 9999 の言い切りを足す                                                        -> numbers
M95 §3 の「213 本は出力が 10 token 未満」を 212 本に                                      -> sanity・numbers
M96 §3 の「788 本」を 787 本に                                                          -> sanity・numbers
M97 §3 に 3 桁の数を足した行                                                            -> sec3・numbers
M98 §3 に % を足した行                                                                 -> sec3
M99 §3 の「script の欠陥ではない」を消す                                                -> sec3
M100 §3 の記録に縛らない 1 行の 226 を §3 の外の行にも書く                                  -> sanity
M101 §3 の記録に縛らない 1 行の「誤って通した行は 1 行のまま」を 2 行のままに               -> sanity
M102 §3 の見出しの「記録に欄の無い読み」を消す                                             -> sec3・phrases
M103 文書に「XBRL を作れる。」を引用の外で足す                                            -> affirm
M104 文書に「専用の道具が要らない。」を足す                                               -> affirm
M105 文書に「紙を AI が書ける。」を足す                                                   -> affirm
M106 文書に「AI が書ける。」を足す                                                        -> affirm
M107 引用の行から「言えない」「読まない」を全部消す                                        -> affirm
M108 §4 の「言えないこと」を消す                                                          -> phrases
M109 §1 の「判定しない(封の決め: 主の席の「誤」が 9 行以下)」の字を消す                    -> phrases・verdict
M110 頭の「この便からは言えない」を消す                                                   -> head
M111 頭の「先に負けと限界を書く」を消す                                                    -> head
M112 頭の「司令塔は上限を上げずに本番を走らせた」を消す                                    -> head
M113 頭の「字のあいまいさは封を書いた司令塔の落ち度」を消す                                -> head
M114 頭の「このため主の席の数は低く出ている」を消す                                        -> head
M115 頭の「engine は 0 行」を消す                                                        -> head
M116 文書に「保証」を足す                                                                -> forbidden
M117 文書に「精度」を足す                                                                -> forbidden
M118 文書に「完璧」(「完璧に動いたら」の外)を足す                                          -> forbidden
M119 文書に docID の形を足す                                                              -> forbidden
M120 文書の commit の字 e066a557 を 1 字替える                                            -> commits
M121 文書に知らない commit の字を足す                                                     -> commits
"""


def row_of(rec, i):
    return rec[u"行"][i]


def a_rows(rec, pred=None):
    return [r for r in rec[u"行"] if r[I_CLS] == u"A" and (pred is None or pred(r))]


def w_rows(rec, pred=None):
    return [r for r in rec[u"行"] if r[I_CLS] == u"W" and (pred is None or pred(r))]


def idx_of(rec, r):
    for i, x in enumerate(rec[u"行"]):
        if x is r:
            return i
    raise KeyError


def set_pair(r, main, sub, same=None):
    u"""札を整合して変える(同じ要素を選んだ行は札の正と誤が揃う)。"""
    r[I_M] = main
    r[I_S] = sub
    if same is not None:
        r[I_SAME] = same


def make_read(rec, r, label, sub=None):
    u"""主の席の答えなしの行を、2 回目の呼び出しが読めた形に整合して直し、札を label にする。"""
    i = idx_of(rec, r)
    cs = [x for x in rec[u"呼び出し"] if x[J_ROW] == i and x[J_SEAT] == u"主"]
    last = [x for x in cs if x[J_ATT] == 2][0]
    last[J_STOP] = u"end_turn"
    last[J_OK] = True
    last[J_TOUT] = 7
    last[J_USD] = (last[J_TIN] * PRICE_IN + 7 * PRICE_OUT) / 1e6
    r[I_M] = label
    if r[I_SAME]:
        r[I_SAME] = False


def fix_pair_for(r, main_ok):
    u"""2 席が同じ要素を選んだ行の札を揃えて直す。"""
    if r[I_SAME]:
        lab = L_OK if main_ok else L_BAD
        r[I_M] = lab
        r[I_S] = lab


def m_x1_hit(c):
    for r in a_rows(c.rec, lambda r: r[I_M] in (L_ZERO, L_BAD)):
        r[I_M] = L_OK
        if r[I_SAME]:
            r[I_S] = L_OK
    rebuild(c.rec)


def m_x1_high(c):
    m_x1_hit(c)
    for r in a_rows(c.rec, lambda r: r[I_M] == L_NONE):
        make_read(c.rec, r, L_OK)
    rebuild(c.rec)


def m_x2_hit(c):
    for r in a_rows(c.rec, lambda r: not r[I_SAME] and r[I_M] != L_NONE):
        set_pair(r, L_OK, L_OK, True)
    rebuild(c.rec)


def m_x3_zero(c):
    for r in a_rows(c.rec, lambda r: r[I_SAME] and r[I_M] == L_BAD):
        set_pair(r, L_OK, L_OK)
    rebuild(c.rec)


def m_x3_high(c):
    for r in a_rows(c.rec, lambda r: r[I_SAME] and r[I_M] == L_OK)[:6]:
        set_pair(r, L_BAD, L_BAD)
    rebuild(c.rec)


def m_x4_hit(c):
    for r in a_rows(c.rec, lambda r: not r[I_SAME] and r[I_M] == L_OK)[:6]:
        set_pair(r, L_BAD, r[I_S])
    rebuild(c.rec)


def m_x4_miss(c):
    for r in a_rows(c.rec, lambda r: r[I_SAME] and r[I_M] == L_OK)[:20]:
        set_pair(r, L_BAD, L_BAD)
    rebuild(c.rec)


def m_x5_hit(c):
    for r in w_rows(c.rec, lambda r: r[I_M] == L_ZERO)[:12]:
        r[I_M] = L_BAD
    rebuild(c.rec)


def m_x6_hit(c):
    for r in w_rows(c.rec, lambda r: not r[I_SAME] and r[I_M] in (L_BAD, L_ZERO) and r[I_S] in (L_BAD, L_ZERO))[:9]:
        set_pair(r, L_BAD, L_BAD, True)
    rebuild(c.rec)


def m_x7_miss(c):
    for r in a_rows(c.rec, lambda r: r[I_N] >= 7 and r[I_M] == L_OK)[:3]:
        set_pair(r, L_BAD, L_BAD if r[I_SAME] else r[I_S])
    rebuild(c.rec)


def m_x8_miss(c):
    for r in a_rows(c.rec, lambda r: r[I_KIND] == u"種類なし" and r[I_M] == L_NONE):
        make_read(c.rec, r, L_OK)
    rebuild(c.rec)


def m_x9_miss(c):
    for r in a_rows(c.rec, lambda r: r[I_S] == L_ZERO)[:130]:
        r[I_S] = L_OK
    rebuild(c.rec)


def m_x10_hit(c):
    for r in a_rows(c.rec, lambda r: r[I_M] == L_NONE):
        make_read(c.rec, r, L_OK)
    rebuild(c.rec)


def m_x11_miss(c):
    for x in list(c.rec[u"呼び出し"]):
        x[J_TIN] += 300
        x[J_USD] = (x[J_TIN] * PRICE_IN + x[J_TOUT] * PRICE_OUT) / 1e6
    rebuild(c.rec)


def m_s1(c):
    for r in a_rows(c.rec, lambda r: r[I_M] == L_OK):
        set_pair(r, L_BAD, L_BAD if r[I_SAME] else r[I_S])
    rebuild(c.rec)


def m_s2(c):
    for r in a_rows(c.rec, lambda r: r[I_M] == L_OK)[:150]:
        set_pair(r, L_ZERO, r[I_S], False)
    rebuild(c.rec)


def m_s3(c):
    rows = [r for r in c.rec[u"行"] if r[I_M] == L_NONE]
    for r in rows[:50]:
        make_read(c.rec, r, L_OK if r[I_CLS] == u"A" else L_BAD)
    rebuild(c.rec)


def m_s4(c):
    for r in a_rows(c.rec):
        if r[I_M] == L_NONE:
            make_read(c.rec, r, L_OK)
        set_pair(r, L_OK, L_OK, True)
    rebuild(c.rec)


def set_call(c, i, key, val):
    c.rec[u"呼び出し"][i][key] = val


def m_read_true(c):
    r = [r for r in c.rec[u"行"] if r[I_M] == L_NONE][0]
    i = idx_of(c.rec, r)
    [x for x in c.rec[u"呼び出し"] if x[J_ROW] == i and x[J_SEAT] == u"主"][0][J_OK] = True


def m_drop_second(c):
    r = [r for r in c.rec[u"行"] if r[I_M] == L_NONE][0]
    i = idx_of(c.rec, r)
    calls = c.rec[u"呼び出し"]
    k = [n for n, x in enumerate(calls) if x[J_ROW] == i and x[J_SEAT] == u"主" and x[J_ATT] == 2][0]
    del calls[k]


def m_extra_after_read(c):
    calls = c.rec[u"呼び出し"]
    k = [n for n, x in enumerate(calls) if x[J_ATT] == 1 and x[J_OK] and x[J_SEAT] == u"主"][0]
    y = list(calls[k])
    y[J_ATT] = 2
    calls.append(y)


def m_stop_max_ok(c):
    k = [n for n, x in enumerate(c.rec[u"呼び出し"]) if x[J_OK] and x[J_SEAT] == u"副"][0]
    c.rec[u"呼び出し"][k][J_STOP] = u"max_tokens"


def m_bad_cols(c):
    c.rec[u"行の欄"] = [u"X"] + c.rec[u"行の欄"][1:]


def m_w_ok(c):
    r = w_rows(c.rec)[0]
    r[I_M] = L_OK


def m_trial_w(c):
    c.rec[u"試しの行"][0][I_CLS] = u"W"


def m_row_dev(c):
    c.rec[u"行"][0][I_DOC] = 3


def m_same_true(c):
    r = [r for r in c.rec[u"行"] if not r[I_SAME] and r[I_M] == L_OK and r[I_S] != L_OK][0]
    r[I_SAME] = True


def m_drop_quote_negation(c):
    lines = []
    for ln in c.doc.splitlines():
        if QUOTED_CLAIM.search(ln):
            for w in (u"言えないこと", u"言えない", u"読まない", u"示していない"):
                ln = ln.replace(w, u"X")
        lines.append(ln)
    c.doc = u"\n".join(lines)


def add_sec3(c, text):
    rep(c, u"## §4 ", text + u"\n\n## §4 ")


def add_outside_226(c):
    add_doc(c, u"緩く読むと 226 行。")


def m_swap_nine(c):
    rep(c, u"| 副 98 行・主 222 行・差 124 行 |", u"| 主 98 行・副 222 行・差 124 行 |")


def m_swap_sec4(c):
    rep(c, u"選んだのは 222 行・別の候補を選んだのは 6 行だった", u"選んだのは 6 行・別の候補を選んだのは 222 行だった")


def m_all_usd(c):
    c.doc = c.doc.replace(u"2.87673", u"2.87674")


def m_set_rec(c, key, val):
    c.rec[key] = val


MUTATIONS = (
    (u"M1 記録の sha256 の写しを違う値に", lambda c: c.shas.__setitem__(RECORD_REL, u"0" * 64), (u"sha",)),
    (u"M2 記録の script の sha256 を 1 字替える", lambda c: c.rec.__setitem__(u"この script の sha256", u"f" + c.rec[u"この script の sha256"][1:]), (u"sha",)),
    (u"M3 記録の限界の欄の 1 行を消す", lambda c: c.rec.__setitem__(u"限界", c.rec[u"限界"][1:]), (u"sha",)),
    (u"M4 記録の封の commit の欄を 1 字替える", lambda c: c.rec.__setitem__(u"封の commit", u"0" + c.rec[u"封の commit"][1:]), (u"sha",)),
    (u"M5 記録の max_tokens を 1000 に", lambda c: c.rec[u"呼び出しの形"].__setitem__(u"max_tokens", 1000), (u"sha",)),
    (u"M6 記録の主の席の thinking を disabled に", lambda c: c.rec[u"席"][u"主の席"].__setitem__(u"thinking", {u"type": u"disabled"}), (u"sha",)),
    (u"M7 記録の指示文の字の 1 字を替える", lambda c: c.rec[u"指示文の型(封 §2-2)"].__setitem__(u"字", c.rec[u"指示文の型(封 §2-2)"][u"字"].replace(u"次は", u"次が", 1)), (u"sha",)),
    (u"M8 記録の費用の上限を 50 に", lambda c: c.rec[u"費用"].__setitem__(u"上限 USD", 50.0), (u"sha",)),
    (u"M9 便 XG1 の script の sha256 の欄を 1 字替える", lambda c: c.rec.__setitem__(u"便 XG1 の script の sha256", u"0" + c.rec[u"便 XG1 の script の sha256"][1:]), (u"sha",)),
    (u"M10 記録の主の席の model を haiku に", lambda c: c.rec[u"席"][u"主の席"].__setitem__(u"model", u"claude-haiku-5-5"), (u"sha",)),
    (u"M11 記録の temperature の欄を 0 に", lambda c: c.rec[u"呼び出しの形"].__setitem__(u"temperature", 0), (u"sha",)),
    (u"M12 記録の副の席の候補の並びを昇順に", lambda c: c.rec[u"席"][u"副の席"].__setitem__(u"候補の並び", u"昇順"), (u"sha",)),
    (u"M13 行 10 の主の席の札を 誤 に", lambda c: row_of(c.rec, 9).__setitem__(I_M, L_BAD if row_of(c.rec, 9)[I_M] != L_BAD else L_OK), (u"recount",)),
    (u"M14 類 A の行の候補の数を 1 増やす", lambda c: a_rows(c.rec)[3].__setitem__(I_N, a_rows(c.rec)[3][I_N] + 1), (u"recount",)),
    (u"M15 呼び出し 5 の出力 token を 1 増やす", lambda c: set_call(c, 4, J_TOUT, c.rec[u"呼び出し"][4][J_TOUT] + 1), (u"recount",)),
    (u"M16 呼び出し 5 の USD を 0.000001 増やす", lambda c: set_call(c, 4, J_USD, c.rec[u"呼び出し"][4][J_USD] + 0.000001), (u"recount",)),
    (u"M17 記録の A の主の席の正を 1 減らす", lambda c: c.rec[K_TALLY][u"類 A"][u"主の席の札"].__setitem__(L_OK, 221), (u"recount",)),
    (u"M18 記録の P2 の通した行を 1 増やす", lambda c: c.rec[K_TALLY][u"類 A"][u"P2(2 席の一致)"].__setitem__(u"通した行", 84), (u"recount",)),
    (u"M19 記録の使った額 USD を 0.01 増やす", lambda c: c.rec[u"費用"].__setitem__(u"使った額 USD(試しを含む)", 2.88673), (u"recount",)),
    (u"M20 記録の XD0-3 の % を 1.3 に", lambda c: c.rec[K_PRED][u"XD0-3 類 A で P2 が誤って通した行 / P2 が通した行"][u"誤って通した行 / 通した行"].__setitem__(u"%", 1.3), (u"recount",)),
    (u"M21 記録の自己点検の「答えなしが 40 行以上」を false に", lambda c: c.rec[K_SUSPECT].__setitem__(u"条件に当たる(答えなしが 40 行以上)", False), (u"recount",)),
    (u"M22 記録の試しの 10 回の USD の全部を 1 増やす", lambda c: c.rec[K_TRIAL][u"呼び出し"].__setitem__(u"USD の全部", c.rec[K_TRIAL][u"呼び出し"][u"USD の全部"] + 1), (u"recount",)),
    (u"M23 行の「2 席が同じ要素を選んだ」を札の合わない行で真に", m_same_true, (u"recount",)),
    (u"M24 類 W の行の主の席の札を 正 に", m_w_ok, (u"recount",)),
    (u"M25 答えなしの行の呼び出しの「答えが読めた」を真に", m_read_true, (u"recount",)),
    (u"M26 答えなしの行の 2 回目の呼び出しを消す", m_drop_second, (u"recount",)),
    (u"M27 1 回目が読めたのに 2 回目の呼び出しを足す", m_extra_after_read, (u"recount",)),
    (u"M28 読めた呼び出しの stop_reason を max_tokens に", m_stop_max_ok, (u"recount",)),
    (u"M29 呼び出しの HTTP の状態を 429 に", lambda c: set_call(c, 0, J_HTTP, 429), (u"recount",)),
    (u"M30 行の欄の列の名を 1 つ替える", m_bad_cols, (u"recount",)),
    (u"M31 配線の確認の本番の類 A を 2604 に", lambda c: c.rec[K_WIRE][u"段 3 の類の数(本番)"].__setitem__(u"A", 2604), (u"recount",)),
    (u"M32 回数の呼び出しの予定を 789 に", lambda c: c.rec[u"回数"].__setitem__(u"呼び出しの予定(本番)", 789), (u"recount",)),
    (u"M33 試しの行の類を W に", m_trial_w, (u"recount",)),
    (u"M34 行の書類の番号を開発の 5 本の番号に", m_row_dev, (u"recount",)),
    (u"M35 記録に docid の欄を足す", lambda c: c.rec.__setitem__(u"docid", u"x"), (u"clean",)),
    (u"M36 記録に EDINET コードの形の字を足す", lambda c: c.rec.__setitem__(u"step", c.rec[u"step"] + u" E12345"), (u"clean",)),
    (u"M37 記録の key_leaks に字を足す", lambda c: c.rec.__setitem__(u"key_leaks", [u"x"]), (u"clean",)),
    (u"M38 行に決めの語でない字を足す", lambda c: row_of(c.rec, 0).__setitem__(I_MSHA, u"要素の名"), (u"clean",)),
    (u"M39 記録に鍵らしい字を足す", lambda c: c.rec.__setitem__(u"step", c.rec[u"step"] + u" sk-" + u"ant-api03-" + u"A" * 40), (u"clean",)),
    (u"M40 封の写しから XD0-1 の境の字を消す", lambda c: rep(c, u"245 行以上 310 行以下", u"X", attr="seal"), (u"bound",)),
    (u"M41 封の写しから「主の席の「誤」が 9 行以下なら判定しない」を消す", lambda c: rep(c, u"主の席の「誤」が 9 行以下なら判定しない", u"X", attr="seal"), (u"bound",)),
    (u"M42 封の写しから自己点検の字を消す", lambda c: rep(c, u"答えなしが 40 行以上・P2 が通した行が 300 行以上で誤 0", u"X", attr="seal"), (u"bound",)),
    (u"M43 封の写しから「XD0-2 と XD0-3 がどちらも当たったときだけ」を消す", lambda c: rep(c, u"XD0-2 と XD0-3 がどちらも当たったときだけ", u"X", attr="seal"), (u"bound",)),
    (u"M44 封の写しから「合わせて 394 行」を消す", lambda c: rep(c, u"合わせて 394 行", u"X", attr="seal"), (u"bound",)),
    (u"M45 XD0-1 の判定を当たりに", lambda c: rep(c, u"外れ(下に。境まで 23 行)", u"当たり"), (u"verdict",)),
    (u"M46 XD0-4 の判定を当たりに", lambda c: rep(c, u"判定しない(封の決め: 主の席の「誤」が 9 行以下) |", u"当たり |"), (u"verdict",)),
    (u"M47 XD0-3 の判定を外れ(上に)に", lambda c: rep(c, u"当たり(下の境 0 行まで 1 行)", u"外れ(上に)"), (u"verdict",)),
    (u"M48 件数の行を当たり 6・外れ 4 に", lambda c: rep(c, u"- 当たり 5・外れ 5・判定しない 1。", u"- 当たり 6・外れ 4・判定しない 1。"), (u"verdict",)),
    (u"M49 頭の件数を当たり 6・外れ 4 に", lambda c: rep(c, u"判定した 10 本は 当たり 5・外れ 5", u"判定した 10 本は 当たり 6・外れ 4"), (u"verdict",)),
    (u"M50 XD0-1 の実測 222 行を 224 行に", lambda c: rep(c, u"| 222 行 |", u"| 224 行 |"), (u"verdict",)),
    (u"M51 XD0-7 の実測の 70.6% を 71.6% に", lambda c: rep(c, u"96 行・70.6%", u"96 行・71.6%"), (u"verdict",)),
    (u"M52 XD0-8 の差 36.91 を 26.91 に", lambda c: rep(c, u"差 36.91 ポイント", u"差 26.91 ポイント"), (u"verdict",)),
    (u"M53 XD0-2 の予測の欄の 228 行以上を 229 行以上に", lambda c: rep(c, u"P2 が通す行は 228 行以上", u"P2 が通す行は 229 行以上"), (u"verdict",)),
    (u"M54 XD0-9 の実測の字を主・副の入れ替えに", m_swap_nine, (u"verdict",)),
    (u"M55 §1 の「次の便の候補として**上げない**」を「上げる」に", lambda c: rep(c, u"次の便の候補として**上げない**", u"次の便の候補として**上げる**"), (u"verdict",)),
    (u"M56 §1 の XD0-6 の読みの 27 行を 41 行に", lambda c: rep(c, u"XD0-6 は外れたが、類 W で 27 行を誤って通しており", u"XD0-6 は外れたが、類 W で 41 行を誤って通しており"), (u"verdict", u"frag")),
    (u"M57 頭の「対の XD0-2 が大きく外れた」を消す", lambda c: rep(c, u"、対の XD0-2 が大きく外れた", u""), (u"verdict", u"head")),
    (u"M58 整合: 主の席の 0・誤の行を 正 に直して XD0-1 が当たり", m_x1_hit, (u"verdict",)),
    (u"M59 整合: 主の席の答えなしを全部読めた正に直して XD0-1 が上に外れ", m_x1_high, (u"verdict",)),
    (u"M60 整合: P2 が通した類 A を 228 行以上にして XD0-2 が当たり", m_x2_hit, (u"verdict",)),
    (u"M61 整合: 誤って通した類 A を 0 行にして XD0-3 が外れ(下)", m_x3_zero, (u"verdict",)),
    (u"M62 整合: 誤って通した類 A を 5% 超にして XD0-3 が外れ(上)", m_x3_high, (u"verdict",)),
    (u"M63 整合: 主の席の誤を 10 行以上にして XD0-4 を判定する", m_x4_hit, (u"verdict",)),
    (u"M64 整合: 主の席の誤を増やし P2 が止めたのを半分未満にして XD0-4 が外れ", m_x4_miss, (u"verdict",)),
    (u"M65 整合: 類 W の主の席の 0 を 20 行以下にして XD0-5 が当たり", m_x5_hit, (u"verdict",)),
    (u"M66 整合: 類 W で P2 が通す行を 34 行以上にして XD0-6 が当たり", m_x6_hit, (u"verdict",)),
    (u"M67 整合: 候補 7 以上の主の席の正を 3 行減らして XD0-7 が外れ", m_x7_miss, (u"verdict",)),
    (u"M68 整合: 種類なしの主の席の答えなしを読めた正に直して XD0-8 が外れ", m_x8_miss, (u"verdict",)),
    (u"M69 整合: 副の席の正を増やして差を 9 行以下にして XD0-9 が外れ", m_x9_miss, (u"verdict",)),
    (u"M70 整合: 主の席の答えなしを 5 行以下にして XD0-10 が当たり", m_x10_hit, (u"verdict",)),
    (u"M71 整合: 入力 token を 300 増やして使った額を 3 USD 超にして XD0-11 が外れ", m_x11_miss, (u"verdict",)),
    (u"M72 整合: 主の席の正を 130 行以下にして自己点検が発火", m_s1, (u"verdict", u"suspect")),
    (u"M73 整合: 主の席の 0 を類 A の半分超にして主の席だけの読みが発火", m_s2, (u"verdict", u"suspect")),
    (u"M74 整合: 答えなしを 40 行未満にして発火しない", m_s3, (u"verdict", u"suspect")),
    (u"M75 整合: P2 が通した類 A を 300 行以上で誤 0 にして発火", m_s4, (u"verdict", u"suspect")),
    (u"M76 頭の「答えなしが 40 行以上に当たった」の 84 行を 83 行に", lambda c: rep(c, u"送った 394 行のうち 84 行。**", u"送った 394 行のうち 83 行。**"), (u"suspect", u"frag")),
    (u"M77 頭の「副の席の「0」は類 A の 326 行のうち 206 行」を 205 行に", lambda c: rep(c, u"副の席の「0」は類 A の 326 行のうち 206 行で、半分", u"副の席の「0」は類 A の 326 行のうち 205 行で、半分"), (u"suspect", u"frag")),
    (u"M78 頭の「主の席だけで読むと 18 行で当たらない」を 17 行に", lambda c: rep(c, u"主の席だけで読むと 18 行で当たらない", u"主の席だけで読むと 17 行で当たらない"), (u"suspect", u"frag")),
    (u"M79 頭の「副の席も入れて読むと当たる」を「副の席も入れて読んでも当たらない」に", lambda c: rep(c, u"副の席も入れて読むと当たる。**", u"副の席も入れて読んでも当たらない。**"), (u"suspect",)),
    (u"M80 頭の「(記録の欄はこの読みで false)」を消す", lambda c: rep(c, u"(記録の欄はこの読みで false)", u""), (u"suspect",)),
    (u"M81 §2 の席の札の表の 類 A 主の 222 を 221 に", lambda c: rep(c, u"| 類 A(326 行) | 主 | 222 |", u"| 類 A(326 行) | 主 | 221 |"), (u"frag",)),
    (u"M82 §2 の P2 の行の 83 を 82 に", lambda c: rep(c, u"| 類 A | P2(2 席の一致) | 83 |", u"| 類 A | P2(2 席の一致) | 82 |"), (u"frag",)),
    (u"M83 §2 の呼び出しの表の出力 token 29616 を 29617 に", lambda c: rep(c, u"| 233290 | 29616 |", u"| 233290 | 29617 |"), (u"frag", u"numbers")),
    (u"M84 §2 の使った額 2.87673 を 2.87674 に(全部の箇所)", m_all_usd, (u"frag", u"numbers", u"sanity")),
    (u"M85 §2 の 99.9546 を 99.9547 に", lambda c: rep(c, u"99.9546", u"99.9547"), (u"frag", u"numbers")),
    (u"M86 §2 の帯の表の「候補 2」の主の正 100 を 101 に", lambda c: rep(c, u"| 候補 2 | 146 | 100 |", u"| 候補 2 | 146 | 101 |"), (u"frag",)),
    (u"M87 §2 の種類の表の「種類なし | 49」を 50 に", lambda c: rep(c, u"| 種類なし | 49 |", u"| 種類なし | 50 |"), (u"frag",)),
    (u"M88 頭の「P2 は 27 行を誤って通した」を 41 行に(別の主張の数)", lambda c: rep(c, u"P2 は 27 行を誤って通した", u"P2 は 41 行を誤って通した"), (u"frag",)),
    (u"M89 頭の「通した 83 行のうち誤りは 1 行」の 83 を 243 に(別の主張の数)", lambda c: rep(c, u"通した 83 行のうち誤りは 1 行", u"通した 243 行のうち誤りは 1 行"), (u"frag",)),
    (u"M90 頭の「答えが読めた 246 行(326 − 80)」の 246 を 245 に", lambda c: rep(c, u"答えが読めた 246 行(326 − 80)", u"答えが読めた 245 行(326 − 80)"), (u"frag",)),
    (u"M91 §4 の「222 行・6 行」を入れ替える", m_swap_sec4, (u"frag",)),
    (u"M92 §4 の「類 W で主の席は 68 行のうち 35 行」の 35 を 32 に", lambda c: rep(c, u"主の席は 68 行のうち 35 行で", u"主の席は 68 行のうち 32 行で"), (u"frag",)),
    (u"M93 §4 の「84 行は測れていない」を 80 行に", lambda c: rep(c, u"(84 行は測れていない)", u"(80 行は測れていない)"), (u"frag",)),
    (u"M94 文書に 9999 の言い切りを足す", lambda c: add_doc(c, u"主の席の行は 9999 行に近い。"), (u"numbers",)),
    (u"M95 §3 の「213 本は出力が 10 token 未満」を 212 本に", lambda c: rep(c, u"213 本は出力が 10 token 未満", u"212 本は出力が 10 token 未満"), (u"sanity", u"numbers")),
    (u"M96 §3 の「788 本」を 787 本に", lambda c: rep(c, u"788 本", u"787 本"), (u"sanity", u"numbers")),
    (u"M97 §3 に 3 桁の数を足した行", lambda c: add_sec3(c, u"- 別の確かめは 777 行。"), (u"sec3", u"numbers")),
    (u"M98 §3 に % を足した行", lambda c: add_sec3(c, u"- 別の確かめは 9%。"), (u"sec3",)),
    (u"M99 §3 の「script の欠陥ではない」を消す", lambda c: rep(c, u"script の欠陥ではない", u"X"), (u"sec3",)),
    (u"M100 §3 の記録に縛らない 1 行の 226 を §3 の外の行にも書く", add_outside_226, (u"sanity",)),
    (u"M101 §3 の記録に縛らない 1 行の「誤って通した行は 1 行のまま」を 2 行のままに", lambda c: rep(c, u"誤って通した行は 1 行のまま", u"誤って通した行は 2 行のまま"), (u"sanity",)),
    (u"M102 §3 の見出しの「記録に欄の無い読み」を消す", lambda c: rep(c, u"記録に欄の無い読み。出所は", u"X。出所は"), (u"sec3", u"phrases")),
    (u"M103 文書に「XBRL を作れる。」を引用の外で足す", lambda c: add_doc(c, u"XBRL を作れる。"), (u"affirm",)),
    (u"M104 文書に「専用の道具が要らない。」を足す", lambda c: add_doc(c, u"専用の道具が要らない。"), (u"affirm",)),
    (u"M105 文書に「紙を AI が書ける。」を足す", lambda c: add_doc(c, u"紙を AI が書ける。"), (u"affirm",)),
    (u"M106 文書に「AI が書ける。」を足す", lambda c: add_doc(c, u"AI が書ける。"), (u"affirm",)),
    (u"M107 引用の行から「言えない」「読まない」を消す", m_drop_quote_negation, (u"affirm",)),
    (u"M108 「言えないこと」を消す", lambda c: drop_all(c, u"言えないこと"), (u"phrases",)),
    (u"M109 §1 の「判定しない(封の決め: …)」の字を消す", lambda c: rep(c, u"判定しない(封の決め: 主の席の「誤」が 9 行以下) |", u"X |"), (u"phrases", u"verdict")),
    (u"M110 頭の「この便からは言えない」を消す", lambda c: rep(c, u"は、この便からは言えない。**", u"は、X。**", count=1), (u"head",)),
    (u"M111 頭の「先に負けと限界を書く」を消す", lambda c: drop_all(c, u"先に負けと限界を書く"), (u"head",)),
    (u"M112 頭の「司令塔は上限を上げずに本番を走らせた」を消す", lambda c: rep(c, u"司令塔は上限を上げずに本番を走らせた", u"X"), (u"head",)),
    (u"M113 頭の「字のあいまいさは封を書いた司令塔の落ち度」を消す", lambda c: rep(c, u"字のあいまいさは封を書いた司令塔の落ち度", u"X"), (u"head",)),
    (u"M114 頭の「このため主の席の数は低く出ている」を消す", lambda c: rep(c, u"このため主の席の数は低く出ている", u"X"), (u"head",)),
    (u"M115 頭の「engine は 0 行」を消す", lambda c: rep(c, u"engine は 0 行", u"X"), (u"head",)),
    (u"M116 文書に「保証」を足す", lambda c: add_doc(c, u"保証する。"), (u"forbidden",)),
    (u"M117 文書に「精度」を足す", lambda c: add_doc(c, u"精度が高い。"), (u"forbidden",)),
    (u"M118 文書に「完璧」を足す", lambda c: add_doc(c, u"完璧な結果。"), (u"forbidden",)),
    (u"M119 文書に docID の形を足す", lambda c: add_doc(c, u"書類 S100ABCD。"), (u"forbidden",)),
    (u"M120 文書の commit の字 e066a557 を 1 字替える", lambda c: rep(c, u"e066a557", u"e066a558"), (u"commits",)),
    (u"M121 文書に知らない commit の字を足す", lambda c: add_doc(c, u"commit 1a2b3c4d。"), (u"commits",)),
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
        D = derive(self.c.rec)
        A, W = D[K_TALLY][u"類 A"], D[K_TALLY][u"類 W"]
        self.assertEqual((326, 68), (A[u"行"], W[u"行"]))
        self.assertEqual((222, 6, 18, 80), tuple(A[u"主の席の札"][k] for k in LABS))
        self.assertEqual((98, 22, 206, 0), tuple(A[u"副の席の札"][k] for k in LABS))
        self.assertEqual((0, 35, 29, 4), tuple(W[u"主の席の札"][k] for k in LABS))
        self.assertEqual((0, 32, 36, 0), tuple(W[u"副の席の札"][k] for k in LABS))
        self.assertEqual((83, 1, 243, 140), tuple(A[u"P2(2 席の一致)"][k] for k in (u"通した行", u"誤って通した行", u"止めた行", u"止めた行のうち主の席が正")))
        self.assertEqual((27, 27, 41), tuple(W[u"P2(2 席の一致)"][k] for k in (u"通した行", u"誤って通した行", u"止めた行")))
        self.assertEqual((228, 6, 98), tuple(A[u"P1(主の席だけ)"][k] for k in (u"通した行", u"誤って通した行", u"止めた行")))
        self.assertEqual(2.87673, D[K_PRED][u"XD0-11 使った額 USD(試しを含む全部)"])
        self.assertEqual(2.853115, D[K_CALLS][u"USD の全部"])
        self.assertEqual(0.023615, D[K_TRIAL][u"呼び出し"][u"USD の全部"])
        self.assertEqual((515, 395), (D[K_CALLS][u"主"][u"呼び出しの数(HTTP の再試行を除く。中断した呼び出しを除く)"], D[K_CALLS][u"副"][u"呼び出しの数(HTTP の再試行を除く。中断した呼び出しを除く)"]))

    def test_c_1_the_seal_has_the_bound_phrases(self):
        self.assertEqual([], bound_problems(self.c))

    def test_c_2_the_verdicts_are_decided_again_and_equal_the_document(self):
        self.assertEqual([], verdict_problems(self.c))
        j = judge(derive(self.c.rec))
        self.assertEqual(list(IDS), list(j))
        self.assertEqual((5, 5, 1), counts(j))
        self.assertEqual([u"XD0-3", u"XD0-7", u"XD0-8", u"XD0-9", u"XD0-11"], [k for k, v in j.items() if v[0] == u"当たり"])
        self.assertEqual([u"XD0-1", u"XD0-2", u"XD0-5", u"XD0-6", u"XD0-10"], [k for k, v in j.items() if v[0] == u"外れ"])
        self.assertEqual([u"XD0-4"], [k for k, v in j.items() if v[0] == u"判定しない"])

    def test_c_3_the_self_suspicion_conditions_are_decided_again_in_both_readings(self):
        self.assertEqual([], suspect_problems(self.c))
        f = fires(derive(self.c.rec))
        self.assertEqual((False, False, True, True, False), f)         # 正 130 以下・0(主だけ)・0(副も入れる)・答えなし 40 以上・P2 300 以上で誤 0

    def test_d_1_every_number_in_the_document_is_bound_to_the_record(self):
        self.assertEqual([], doc_number_problems(self.c))

    def test_d_2_the_table_rows_and_the_main_statements_equal_the_record(self):
        self.assertEqual([], fragment_problems(self.c))
        self.assertEqual([], sanity_problems(self.c))

    def test_d_3_section3_holds_only_derived_numbers_and_one_unbound_line(self):
        self.assertEqual([], sec3_problems(self.c))
        self.assertEqual(1, len(sec3_free_line(self.c.doc)))
        self.assertNotIn(u"226", derived_numbers(self.c))

    def test_e_1_the_important_phrases_are_present(self):
        self.assertEqual([], phrase_problems(self.c))

    def test_e_2_the_losses_and_limits_are_at_the_head(self):
        self.assertEqual([], head_problems(self.c))

    def test_e_3_the_document_has_no_forbidden_words_or_forms_and_no_affirmation(self):
        self.assertEqual([], forbidden_problems(self.c))
        self.assertEqual([], affirm_problems(self.c))

    def test_e_4_the_commits_the_document_names(self):
        self.assertEqual([], doc_commit_problems(self.c))
        self.assertEqual((u"7bb4fa24", u"f119b80c", u"e066a557"), DOC_COMMITS)

    def test_f_1_the_seal_history_the_blobs_and_the_engine(self):
        self.assertEqual([], git_problems())

    def test_f_2_order_the_seal_then_script_then_record_then_the_document_and_the_gate(self):
        u"""結果の文書と門のどちらかが未 commit なら赤(足した commit が無い。skip にしない)。両方 commit された後で初めて緑。"""
        self.assertEqual([], order_problems_real())

    def test_f_3_the_blob_check_lists_the_four_frozen_files_at_their_commits(self):
        self.assertEqual([SEAL_REL, SCRIPT_REL, SEAL_GATE_REL, RECORD_REL], list(BLOB_AT))
        self.assertEqual([SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT], list(BLOB_AT.values()))

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
    def test_h_1_every_mutation_turns_its_checks_red_and_the_files_are_unchanged(self):
        files = list(SHA_PIN) + [DOC_REL]
        before = tuple(sha_file(r) for r in files)
        base = Ctx()
        results = run_mutations(base)
        self.assertEqual(before, tuple(sha_file(r) for r in files))
        self.assertEqual(len(MUTATIONS), len(results))
        silent = [(n, k) for n, res in results for k, red in res if not red]
        self.assertEqual([], silent)
        self.assertGreaterEqual(len(MUTATIONS), 120)

    def test_h_2_the_unmutated_copy_is_green_on_every_check(self):
        c = Ctx().copy()
        for k, fn in CHECKS.items():
            self.assertEqual([], fn(c), k)

    def test_h_3_the_recount_stays_green_when_the_data_changes_consistently_but_the_verdict_does_not(self):
        base = Ctx()
        for fn, key in ((m_x1_hit, u"XD0-1"), (m_x1_high, u"XD0-1"), (m_x2_hit, u"XD0-2"), (m_x3_zero, u"XD0-3"), (m_x3_high, u"XD0-3"), (m_x4_hit, u"XD0-4"), (m_x4_miss, u"XD0-4"),
                        (m_x5_hit, u"XD0-5"), (m_x6_hit, u"XD0-6"), (m_x7_miss, u"XD0-7"), (m_x8_miss, u"XD0-8"), (m_x9_miss, u"XD0-9"), (m_x10_hit, u"XD0-10"), (m_x11_miss, u"XD0-11")):
            c = base.copy()
            fn(c)
            self.assertEqual([], recount_problems(c), fn.__name__)
            self.assertNotEqual([], verdict_problems(c), fn.__name__)
            self.assertNotEqual(judge(derive(base.rec))[key][1], judge(derive(c.rec))[key][1], (fn.__name__, key))

    def test_h_4_every_check_name_a_mutation_names_exists_and_every_check_has_a_mutation(self):
        named = set(k for _, _, ks in MUTATIONS for k in ks)
        self.assertEqual(set(CHECKS), named)

    def test_h_5_the_judgement_edges_at_the_seal_bounds(self):
        u"""境の 1 つ手前と境の数: 下限は含む(XD0-1 は 245・310・XD0-2 は 228・XD0-6 は 34・XD0-7 は 70%・XD0-8 と XD0-9 は 10)・XD0-3 は 5% を含む・XD0-4 は 9 行以下で判定しない・XD0-5 と XD0-10 は含む・XD0-11 は 3 USD を含む。"""
        base = Ctx().copy()

        def judged(**kw):
            D = derive(base.rec)
            A, W = D[K_TALLY][u"類 A"], D[K_TALLY][u"類 W"]
            band = D[K_TALLY][u"類 A を候補の数の帯で分けた"][u"候補 7 以上"]
            kinds = D[K_TALLY][u"類 A を計算書の種類で分けた"]
            A[u"主の席の札"][L_OK] = kw.get(u"ok", 250)
            A[u"主の席の札"][L_NONE] = 0
            W[u"主の席の札"][L_NONE] = kw.get(u"none", 0)
            A[u"P2(2 席の一致)"][u"通した行"] = kw.get(u"p2", 230)
            A[u"P2(2 席の一致)"][u"誤って通した行"] = kw.get(u"wr", 5)
            A[u"主の席が誤の行"] = kw.get(u"bad", 20)
            A[u"主の席が誤の行のうち P2 が止めた行"] = kw.get(u"stop", 10)
            W[u"主の席の札"][L_ZERO] = kw.get(u"wz", 20)
            W[u"P2(2 席の一致)"][u"通した行"] = kw.get(u"w2", 34)
            band[u"行"] = 100
            band[u"主の席の札"][L_OK] = kw.get(u"b7", 70)
            kinds[u"種類なし"][u"行"], kinds[u"種類なし"][u"主の席の札"][L_OK] = 100, kw.get(u"nk", 60)
            for k in KINDS_WITH:
                kinds[k][u"行"], kinds[k][u"主の席の札"][L_OK] = 0, 0
            kinds[u"貸借"][u"行"], kinds[u"貸借"][u"主の席の札"][L_OK] = 100, 70
            A[u"副の席の札"][L_OK] = kw.get(u"sub", 240)
            D[K_PRED][u"XD0-11 使った額 USD(試しを含む全部)"] = kw.get(u"usd", 3.0)
            return judge(D)
        st = lambda j, k: j[k][0]                                           # noqa: E731
        self.assertEqual(u"当たり", st(judged(ok=245), u"XD0-1"))
        self.assertEqual(u"外れ", st(judged(ok=244), u"XD0-1"))
        self.assertEqual(u"当たり", st(judged(ok=310), u"XD0-1"))
        self.assertEqual(u"外れ", st(judged(ok=311), u"XD0-1"))
        self.assertEqual(u"当たり", st(judged(p2=228), u"XD0-2"))
        self.assertEqual(u"外れ", st(judged(p2=227), u"XD0-2"))
        self.assertEqual(u"当たり", st(judged(p2=100, wr=5), u"XD0-3"))         # 5/100 = 5%(含む)
        self.assertEqual(u"外れ", st(judged(p2=100, wr=6), u"XD0-3"))
        self.assertEqual(u"外れ", st(judged(p2=100, wr=0), u"XD0-3"))
        self.assertEqual(u"当たり", st(judged(p2=100, wr=1), u"XD0-3"))
        self.assertEqual(u"判定しない", st(judged(bad=9), u"XD0-4"))
        self.assertEqual(u"当たり", st(judged(bad=10, stop=5), u"XD0-4"))          # ちょうど半分(含む)
        self.assertEqual(u"外れ", st(judged(bad=10, stop=4), u"XD0-4"))
        self.assertEqual(u"当たり", st(judged(wz=20), u"XD0-5"))
        self.assertEqual(u"外れ", st(judged(wz=21), u"XD0-5"))
        self.assertEqual(u"当たり", st(judged(w2=34), u"XD0-6"))
        self.assertEqual(u"外れ", st(judged(w2=33), u"XD0-6"))
        self.assertEqual(u"当たり", st(judged(b7=70), u"XD0-7"))
        self.assertEqual(u"外れ", st(judged(b7=69), u"XD0-7"))
        self.assertEqual(u"当たり", st(judged(nk=60), u"XD0-8"))                  # 種類なし 60%・種類の在る行 70% → 差 10 ポイント(含む)
        self.assertEqual(u"外れ", st(judged(nk=61), u"XD0-8"))
        self.assertEqual(u"当たり", st(judged(ok=250, sub=240), u"XD0-9"))        # 差 10 行(含む)
        self.assertEqual(u"外れ", st(judged(ok=250, sub=241), u"XD0-9"))
        self.assertEqual(u"当たり", st(judged(none=5), u"XD0-10"))
        self.assertEqual(u"外れ", st(judged(none=6), u"XD0-10"))
        self.assertEqual(u"当たり", st(judged(usd=3.0), u"XD0-11"))
        self.assertEqual(u"外れ", st(judged(usd=3.000001), u"XD0-11"))

    def test_h_6_the_miss_direction_follows_the_bound(self):
        c = Ctx().copy()
        m_x1_high(c)
        self.assertEqual(u"外れ(上に。境まで %d 行)" % (derive(c.rec)[K_TALLY][u"類 A"][u"主の席の札"][L_OK] - 310), judge(derive(c.rec))[u"XD0-1"][1])
        c = Ctx().copy()
        self.assertEqual(u"外れ(下に。境まで 23 行)", judge(derive(c.rec))[u"XD0-1"][1])
        c = Ctx().copy()
        m_x3_zero(c)
        self.assertEqual(u"外れ(下に。0 行)", judge(derive(c.rec))[u"XD0-3"][1])
        c = Ctx().copy()
        m_x3_high(c)
        self.assertEqual(u"外れ(上に)", judge(derive(c.rec))[u"XD0-3"][1])

    def test_h_7_the_self_suspicion_fires_in_each_reading(self):
        base = Ctx()
        self.assertEqual((False, False, True, True, False), fires(derive(base.rec)))
        for fn, idx in ((m_s1, 0), (m_s2, 1), (m_s4, 4)):
            c = base.copy()
            fn(c)
            f = fires(derive(c.rec))
            self.assertTrue(f[idx], (fn.__name__, f))
            self.assertNotEqual([], verdict_problems(c) + suspect_problems(c), fn.__name__)
        c = base.copy()
        m_s3(c)
        self.assertFalse(fires(derive(c.rec))[3])                            # 答えなしが 40 行未満なら発火しない
        # 主の席の 0 が半分を超えたときは、副の席を入れた読みも発火する(副の席だけの読みは主の席より広い)
        c = base.copy()
        m_s2(c)
        self.assertTrue(fires(derive(c.rec))[2])

    def test_h_8_the_main_claim_sentences_are_bound_to_their_own_numbers(self):
        u"""前の便の監査の指摘: 数の門が「集合に入っているか」だけだと、別の主張が使う数への書き換えは黙る。主な主張の文は断片の一致で縛る(numbers が黙る書き換えを frag が赤にする)。"""
        base = Ctx()
        for old, new in ((u"P2 は 27 行を誤って通した", u"P2 は 41 行を誤って通した"), (u"通した 83 行のうち誤りは 1 行", u"通した 243 行のうち誤りは 1 行"),
                         (u"類 W の 68 行で", u"類 W の 326 行で"), (u"主の席の答えなし 80 行による", u"主の席の答えなし 84 行による"),
                         (u"| 類 A(326 行) | 副 | 98 | 22 | 206 | 0 |", u"| 類 A(326 行) | 副 | 206 | 22 | 98 | 0 |")):
            c = base.copy()
            rep(c, old, new)
            self.assertEqual([], doc_number_problems(c), old)                # 数の集合には入っている(numbers は黙る)
            self.assertNotEqual([], fragment_problems(c), old)               # 主張ごとの断片が赤にする


if __name__ == "__main__":
    unittest.main()
