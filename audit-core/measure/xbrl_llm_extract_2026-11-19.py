# -*- coding: utf-8 -*-
u"""封 docs/XBRL_LLM_EXTRACT_SEAL_2026-11-19.md(LX ― 文の字だけを読んだ LLM の席の答え(範囲・性質)で結んだ行を止めると、語の表の規則(便 SC・便 PA の段 2)と比べて、取り違えをどれだけ止め、正しい結びをどれだけ減らすか)の測定。
**有料(LLM の席 = Anthropic の API を呼ぶ)。** 走らせるのは司令塔だけ。``--dry-run``・``--check`` は鍵を読まず通信しない(0 USD)。engine(``core/``・``adapters/``)は 1 行も変えない。止める規則は engine の外に置いた後付けの数え直しで、state は書き換えない。

    python3 measure/xbrl_llm_extract_2026-11-19.py --dry-run [--procs N]            # 0 USD。本番と同じ関数で 842 本の指示文を組み、行の数・字数・見積り・配線の確認を出す。記録は書かない
    ANTHROPIC_API_KEY=... python3 measure/xbrl_llm_extract_2026-11-19.py --trial [--procs N]    # 有料。鍵の昇順の頭 5 行 × 2 席に 1 回ずつ(10 回)。形だけ見る
    ANTHROPIC_API_KEY=... python3 measure/xbrl_llm_extract_2026-11-19.py [--resume] [--procs N] # 有料。本番(試しの後は --resume)。全部済んだときにだけ記録を書く
    python3 measure/xbrl_llm_extract_2026-11-19.py --check [--procs N]                # 0 USD。記録の答えから数を作り直して記録と照らし、材料から指示文を組み直して行ごとの sha256 を照らす

守り(封 §3):
  - 鍵は環境変数 ``ANTHROPIC_API_KEY`` だけから読む(.env は読まない)。値は印字・記録・例外の文に通さない。記録は書く前と書いた後に検査する。
  - 上限 ``COST_CAP_USD`` を字で留める。走らせる前に(最大の回数で)見積り、上限を超えるなら 1 回も呼ばない。走っている間も、使った額(返った usage で。返らなかった呼び出しは見積りの額で)が上限に届くなら止まる。試しの額も ``--resume`` で引き継ぐ。
  - 再試行は 429 / 5xx のときだけ最大 2 回(``xbrl_aiforms_gen_2026-11-03.py`` の ``call_with_retry`` をそのまま使う)。答えが読めないときは同じ指示文でもう 1 回だけ呼ぶ(封 §2-3)。
  - 送った文と返った text は ``~/.cache/audit-core/llm_extract_2026-11-19/`` にだけ置く(追跡しない)。途中の答え(``--resume`` 用)もここ。記録 ``fixtures/xbrl/llm_extract/answers_2026-11-19.json`` は本番が全部済んだときにだけ書く。

実装の注(封の字では 1 通りに決まらなかった所の決め。実装より先に決め、結果を見て変えない。報告にも書く):
- 行の引き方・見出しの選び・数の位置の確かめは便 SC・便 PA の script の関数を **呼ぶ**(写さない)。札つきの行の本だけを読む(札の無い本は engine を通さない)。
- 行の順 = 便 PA の記録の行と同じ並び(便の順 TSS・KAM・YS → 本の # → 文の種類か節の順 → 文の番号 → 位置)。封の「鍵の昇順」をこう読んだ。
- 【 】を入れる範囲 = 数の字(符号と空白をはさんでよい)。万・億・兆でつながる組(「1,234万」「12億3,456万」)は 1 つの数として全部を囲み、単位(円・百万円・% など)は囲まない(封 §2-2 の例「【1,234】百万円」)。
  空白で始まる位置(「 5.6%」)は空白を除いた数の字の前に 【 を置く。同じ文の別の数には入れない。
- 「分かち書きの 1 回」= 呼び出し 1 回(HTTP の再試行を含めて 1 回)。答えが読めない回の再試行(封 §2-3)は「答えのやり直し」と呼び、HTTP の再試行とは別に数える。
- HTTP 400・401・403 は設定の誤りなので全体を止める(封は 401・403 を明示していない。400 は思考の指定・temperature の断りを試しで見るため)。
- 上限の比較は 1 回の transport の呼び出しごと(HTTP の再試行を含む)。返らなかった呼び出し(通信の失敗・429・5xx・usage の無い返事)は 1 回ごとに見積りの額を数える。
- 封 §8(追記 a2ed6d0b): 上限は 15 USD。元から 【 か 】 が在る行(文 / 見出し)は別の束に数え、予測の判定に要る数は全部の行のまま、その 2 つの束を除いた数を「参考」に並べる。行の順は上の読みのまま(§8 と同じ)。
- 封 §9(追記 07719813): temperature の欄は送らない(この model が断る)。400 の本文の error.message は鍵を含まないと確かめてから進捗の file と印字に残す(記録には書かない)。前の走りが 400・401・403 で止めた呼び出しは答えの回に数えず、額を残して中断した呼び出しに移し、試しをもう 1 度走らせられる(答えが 1 つも無い置き場でだけ)。
- 呼んでいる間に中断した呼び出し(次の ``--resume`` で見つかる)は見積りの額で数える。
"""
from __future__ import print_function

import argparse
import collections
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request

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


PA = load_module("xbrl_plan_attr_2026-11-19.py", "plan_attr_for_llm_extract")                    # 便 PA(中に便 SC)。札・行の引き方・記録の読み
GEN = load_module("xbrl_aiforms_gen_2026-11-03.py", "aiforms_gen_for_llm_extract")               # API の版・やり直し(call_with_retry)・鍵の検査の字
SC = PA.SC
RT = PA.RT
AT = PA.AT
ST = PA.ST
TSS = PA.TSS
TS = PA.TS
PS = PA.PS
KAM = PA.KAM
YS = PA.YS
Stop = PA.Stop

SEAL_REL = "docs/XBRL_LLM_EXTRACT_SEAL_2026-11-19.md"
SEAL_COMMIT = "198961e6"
SEAL_ADDENDUM2_COMMIT = "07719813"                         # 封の §9 追記の commit(temperature を送らない)
SEAL_ADDENDUM_COMMIT = "a2ed6d0b"                          # 封の §8 追記の commit(上限の替え・元から 【 】 が在る行・行の順の読み)
SCRIPT_REL = "measure/xbrl_llm_extract_2026-11-19.py"
REC_DIR_REL = "fixtures/xbrl/llm_extract"
RECORD_REL = REC_DIR_REL + "/answers_2026-11-19.json"
PA_SCRIPT_REL = "measure/xbrl_plan_attr_2026-11-19.py"
PA_RECORD_REL = "fixtures/xbrl/plan_attr/stops_2026-11-19.json"
SC_RECORD_REL = SC.RECORD_REL
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "llm_extract_2026-11-19")
STATE_NAME = "progress.json"

#: 封 §1 の入力(# , path, sha256)。便 PA の封 §1 の表の全部(23 行)+ 便 PA の script と記録の 2 行。違えば止まる。門が封の表と 1 行ずつ照らす
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
    (22, "measure/xbrl_scope_cond_2026-11-19.py", "c7ec858ea9523ede23ab2da6d16b53ec338d50cb35899ecac66705e16919e065"),
    (23, "fixtures/xbrl/scope_cond/stops_2026-11-19.json", "d938942bffb39176464f3c644932cf53258f84676aacdbbbc421de74d4dc08a7"),
    (24, "measure/xbrl_plan_attr_2026-11-19.py", "711c6ae73538a2140610dd64485a8b5bdf00f9439905a4a9dfdc7ea690eb054d"),
    (25, "fixtures/xbrl/plan_attr/stops_2026-11-19.json", "53891449b95acaf4812cd77fbc3cb9ebc85573999df39b75f359ef87b69d5176"),
)

PROFILE = SC.PROFILE
FP_KEYS = SC.FP_KEYS
SHORT = SC.SHORT
BATCHES = SC.BATCHES
SIDE_ORDER = SC.SIDE_ORDER
G_STATE, V_STATE = SC.STATES[0], SC.STATES[1]
EXPECT_ROWS = 421                                           # 封 §2-1(TSS 119・KAM 133・YS 169 のうち V 174・G 247)。違えば止める
TRIAL_ROWS = 5                                              # 封 §3 の試し(鍵の昇順の頭 5 行 × 2 席)

# ---- 封 §3 の決めごと(字で留める。門が封の字と照らす)
SEATS = ("claude-sonnet-5-5", "claude-haiku-5-5")           # 主の席・副の席
SEAT_TAG = collections.OrderedDict([("claude-sonnet-5-5", u"主"), ("claude-haiku-5-5", u"副")])
SEAT_FILE = {"claude-sonnet-5-5": "main", "claude-haiku-5-5": "sub"}
MAX_TOKENS = 200
TEMPERATURE = None                                          # 封 §9: temperature の欄を送らない(§3 の 0 を外す)
THINKING = {"claude-sonnet-5-5": {"type": "between_tools"}, "claude-haiku-5-5": {"type": "disabled"}}
COST_CAP_USD = 15.0                                         # 封 §8 の「上限の替え」(§3 の 10 USD を置き換える)
PRICE_IN = 5.0                                              # USD / M tokens(両席に当てる保守的な字)
PRICE_OUT = 25.0
MAX_ANSWER_ATTEMPTS = 2                                     # 封 §2-3: 読めなければもう 1 回だけ
KEY_ENV = GEN.KEY_ENV
STOP_HTTP = (400, 401, 403)

# ---- 封 §2-2 の指示文(字で留める。system は無し = user の 1 message)。封の門が封の文書の code block と 1 字ずつ照らす
PROMPT_TEMPLATE = u"""次は、日本の上場企業の開示書類(決算短信または有価証券報告書)の中の 1 つの文と、その文の直前に在った見出しです。文の中の【 】で囲んだ数について、2 つの問いに答えてください。渡した字だけで判断し、推測で埋めないでください。

見出し: {HEADING}
文: {SENTENCE}

問い 1(範囲): 【 】の数は、会社の全体(連結の全体、または提出会社の単体の全体)の数ですか。それとも、その一部分(特定のセグメント・事業・部門・地域・製品・子会社・関連会社・拠点・資産のまとまり・個別の案件や取引先など)の数ですか。
- 全体
- 一部分
- 分からない

問い 2(性質): 【 】の数は、すでに確定して報告・計上された実績の数ですか。それとも、これから先の予想・計画・目標・予定・見通しの数ですか。会計上の見積りを伴っていても、すでに計上された額は「実績」としてください。
- 実績
- 計画・予想
- 分からない

答えは次の形の JSON だけを 1 行で返してください。説明は書かないでください。
{"範囲": "全体 | 一部分 | 分からない のどれか", "性質": "実績 | 計画・予想 | 分からない のどれか"}"""
PLACEHOLDERS = (u"{HEADING}", u"{SENTENCE}")
_PH_RE = re.compile("|".join(re.escape(p) for p in PLACEHOLDERS))
NO_HEADING = u"(なし)"
MARK_OPEN, MARK_CLOSE = u"【", u"】"

F_RANGE, F_NATURE = u"範囲", u"性質"
RANGE_WORDS = (u"全体", u"一部分", u"分からない")
NATURE_WORDS = (u"実績", u"計画・予想", u"分からない")
PART, PLAN = u"一部分", u"計画・予想"
NO_ANSWER = u"答えなし"

# 数の字(【 】の範囲)。符号・空白をはさんでよい。万・億・兆でつながる組は 1 つの数。単位は囲まない
_X = u"(?:\\d{1,3}(?:,\\d{3})+|\\d+)(?:\\.\\d+)?"
MARK_RE = re.compile(u"\\s*((?:△|▲|－|-|マイナス)?\\s*" + _X + u"(?:[兆億万](?:" + _X + u")?)*)")

K_WIRE = u"配線の確認(封 §2-1。予測ではない。違えば止まる)"
K_TALLY = u"数えるもの(封 §2-5 の 1〜5。束 × 便。語の表の数を隣に)"
K_CALLS = u"呼び出しの記録(封 §2-5 の 6)"
K_PRED = u"予測の判定に要る数(LX-1〜LX-11。当たり・外れは結果の文書で)"
REF_KEY = u"参考 文か見出しに元から 【 か 】 が在る行を除いた行だけの数(当たり・外れは全部の行で付ける。封 §8)"
B_SENT, B_HEAD = u"文に元から 【 か 】 が在る行(封 §8)", u"見出しに元から 【 か 】 が在る行(封 §8)"

ROW_COLUMNS = [u"便", u"本の #", u"文の種類か節", u"文の番号", u"位置", u"state", u"member が空", u"主の席の範囲", u"主の席の性質", u"副の席の範囲", u"副の席の性質",
               u"指示文の sha256", u"主の席の呼び出しの数", u"副の席の呼び出しの数", u"文に元から 【 か 】 が在る", u"見出しに元から 【 か 】 が在る"]
(C_BATCH, C_BOOK, C_SIDE, C_SI, C_POS, C_STATE, C_EMPTY, C_MR, C_MN, C_SR, C_SN, C_SHA, C_MC, C_SC, C_SB, C_HB) = range(16)
CALL_COLUMNS = [u"行の番号", u"席", u"答えの回", u"中断した呼び出し", u"HTTP の状態", u"HTTP の再試行の数", u"stop_reason", u"block の type の並び", u"入力 token", u"出力 token",
                u"返った usage の USD", u"見積りで数えた USD", u"返った text の字数", u"答えが読めた"]
(K_ROW, K_SEAT, K_ATT, K_ABORT, K_HTTP, K_RETRY, K_STOP, K_BLOCKS, K_TIN, K_TOUT, K_USD_U, K_USD_E, K_CHARS, K_OK) = range(14)

LIMITS = (
    u"engine は変えていない。止めた数は engine の外の後付けの規則の数",
    u"読みの札は AI の席(司令塔)1 席が付けた。盲検でなく、人は読んでいない。席と札は同じ系統の model で、一致には系統の癖の一致が混ざる。この便は札の正しさを確かめない",
    u"指示文は司令塔が書いた。盲検でない。前の便で読んだ材料と同じ材料に当てている。別の指示文・別の材料なら数は変わる",
    u"席に渡したのは見出し 1 つと文 1 つだけ。前後の文・表・fact の側の字は渡していない。「項目」や「期」の取り違えは席に問うていない",
    u"送ったのは札つきの 421 行だけ。結んだ行の全部でどれだけ止めるか・TSS の正しい結びをどれだけ減らすかは測っていない",
    u"席の答えは呼ぶたびに変わりうる。数は 1 回の呼び出しの記録で、繰り返しの幅は測らない。model の版が変われば同じ数は出ない",
    u"止めたあとに正しい fact へ結び直せるかは測らない",
    u"材料は決算短信の概況の文と有報の KAM・3 つの節。ほかの書類には言えない",
    u"記録は文・見出しの字・値・要素名・枠の id・pointer の字・主語の語・会社名・証券コード・docID・金額・席の返した text を持たない")


def od(pairs=()):
    return collections.OrderedDict(pairs)


def sha256_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def rate(n, d):
    return RT.rate(n, d)


def load_json(p):
    return TSS.load_json(p)


def dumps(o, level=0):
    return RT.dumps(o, level)


class CapStop(Exception):
    u"""上限で止める(1 回の transport の呼び出しの前)。文言に鍵・文を入れない。"""


# ======================================================================================================
# 指示文(封 §2-1・§2-2)
def mark_range(s, pos):
    u"""文 ``s`` の位置 ``pos`` から始まる数の字の (始め, 終わり)。符号・空白をはさんでよい・万億兆でつながる組は 1 つ。数の字が無ければ止める。"""
    m = MARK_RE.match(s, pos)
    if m is None:
        raise Stop(u"**数の位置から数の字が読めない(【 】を入れられない)。止める**")
    return m.span(1)


def mark_sentence(s, pos):
    u"""その行の数の字の前に 【・後ろに 】 を入れた文。同じ文の別の数には入れない。"""
    a, b = mark_range(s, pos)
    return s[:a] + MARK_OPEN + s[a:b] + MARK_CLOSE + s[b:]


def build_prompt(heading, marked):
    u"""指示文の全体。``{HEADING}`` と ``{SENTENCE}`` だけを 1 回の走査で埋める(文の中の ``{…}`` が再び置き換わらない)。``heading`` が None なら ``(なし)``。"""
    values = {u"{HEADING}": NO_HEADING if heading is None else heading, u"{SENTENCE}": marked}
    return _PH_RE.sub(lambda m: values[m.group(0)], PROMPT_TEMPLATE)


# ======================================================================================================
# 答えの読み方(封 §2-3)・止める条件(封 §2-4)
def read_answer(text, stop_reason):
    u"""返った text → (範囲, 性質) か None。最初の ``{`` と最後の ``}`` の間を JSON として読み、欄「範囲」「性質」が 3 つの語のどれかと字で一致するときだけ(前後の空白は落とす)。
    読めない・語が違う・text が 0 字・stop_reason が end_turn でないときは None。"""
    if stop_reason != "end_turn" or not isinstance(text, str) or not text:
        return None
    i, j = text.find(u"{"), text.rfind(u"}")
    if i < 0 or j < i:
        return None
    try:
        obj = json.loads(text[i:j + 1])
    except ValueError:
        return None
    if not isinstance(obj, dict):
        return None
    a, b = obj.get(F_RANGE), obj.get(F_NATURE)
    if not isinstance(a, str) or not isinstance(b, str):
        return None
    a, b = a.strip(), b.strip()
    if a not in RANGE_WORDS or b not in NATURE_WORDS:
        return None
    return (a, b)


def stops_of(answer, empty):
    u"""席の答え((範囲, 性質) か None)と、その行の raw の claim の member の欄が空か → (L-S, L-P, L-U)。
    L-S = 範囲が「一部分」かつ member の欄が空。L-P = 性質が「計画・予想」(member を問わない)。L-U = どちらか。「分からない」と答えなしは止めない。"""
    if answer is None:
        return False, False, False
    ls = answer[0] == PART and bool(empty)
    lp = answer[1] == PLAN
    return ls, lp, (ls or lp)


# ======================================================================================================
# 見積り・費用(封 §3)
def estimate_usd(prompt_chars):
    u"""1 回の見積り = 入力の字数 × 1.0 を token とみなす + 出力は MAX_TOKENS の全部(保守的な単価)。"""
    return (prompt_chars * PRICE_IN + MAX_TOKENS * PRICE_OUT) / 1e6


def cost_usd(input_tokens, output_tokens):
    return ((input_tokens or 0) * PRICE_IN + (output_tokens or 0) * PRICE_OUT) / 1e6


# ======================================================================================================
# 行(材料から引く。封 §2-1)
def unit_rows(pairs, sentences, wanted):
    u"""1 つの文(TSS は 1 本・KAM は文の種類・YS は節)の [(raw の claim, verify の claim)] と文の列と、札つきの行の (文の番号, 位置) の集まり
    → [[文の番号, 位置, state, member が空, 文, 最も近い見出し or None]](札つきで結んだ行だけ)。位置の確かめ(便 SC の関数)に 1 つでも違えば止める。"""
    num_sentences = set(r["sentence"] for r, _c in pairs)
    heads = SC.heading_indices(sentences, num_sentences)
    rows = []
    for r, c in pairs:
        si, pos = r["sentence"], r["pos"]
        if not isinstance(si, int) or not 0 <= si < len(sentences):
            raise Stop(u"**数の claim の文の番号が文の列の外。止める**")
        s = sentences[si]
        if SC.number_start_kind(s, pos, r.get("span")) is None:
            raise Stop(u"**数の claim の位置の欄が「文の中の字の位置」でない(数の字で始まらない・span と合わない)。止めて司令塔に返す**")
        state = c["state"]
        if state not in SHORT or (si, pos) not in wanted:
            continue
        nh = SC.nearest_heading(heads, si)
        rows.append([si, pos, SHORT[state], not r.get("member"), s, sentences[nh] if nh is not None else None])
    rows.sort(key=lambda x: (x[0], x[1]))
    return rows


def tss_units(zb, wanted):
    text = TSS.cut(zb)[0]
    if text is None:
        return [(None, [])]
    wrapped = TSS.wrap(zb, text)[0]
    return [(None, unit_rows(PS.claims_of(wrapped), SC.sentences_of(wrapped), wanted.get(None, frozenset())))]


def kam_units(zb, wanted):
    out = []
    for side in KAM.SIDES:
        text = KAM.cut_kam(zb, side)[0]
        if text is None:
            out.append((side, []))
            continue
        zm = KAM.PR.build_modified_zip(zb, text)[0]
        out.append((side, unit_rows(PS.claims_of(zm), SC.sentences_of(zm), wanted.get(side, frozenset()))))
    return out


def ys_units(zb, wanted):
    out = []
    for section in YS.SECTIONS:
        text = YS.cut_section(zb, section)[0]
        if text is None:
            out.append((section, []))
            continue
        zm = YS.PR.build_modified_zip(zb, text)[0]
        out.append((section, unit_rows(PS.claims_of(zm), SC.sentences_of(zm), wanted.get(section, frozenset()))))
    return out


UNITS_OF = {u"TSS": tss_units, u"KAM": kam_units, u"YS": ys_units}


def book_job(args):
    u"""1 本: (便, 本の #, 群, sha256, ZIP の path, {文の種類か節: 札つきの (文の番号, 位置) の集まり}) → {便, 本の #, units: [(文の種類か節, 行の列)]}。"""
    batch, n, _grp, sha, path, wanted = args
    zb = SC.read_bytes(path, sha, n)
    return od([(u"便", batch), (u"#", n), (u"units", UNITS_OF[batch](zb, wanted))])


def link_rows(books):
    u"""本の job の結果の列 → 行([便, 本の #, 文の種類か節, 文の番号, 位置, state, member が空, 文, 見出し])。便の順(TSS・KAM・YS)→ 本の # → 文の種類か節の順 → 文の番号 → 位置。"""
    rows = []
    for b in sorted(books, key=lambda b: (BATCHES.index(b[u"便"]), b[u"#"])):
        for side, us in b[u"units"]:
            for r in us:
                rows.append([b[u"便"], b[u"#"], side] + list(r))
    return rows


def row_order(batch, book, side, si, pos):
    return (BATCHES.index(batch), book, SIDE_ORDER[batch].index(side), si, pos)


def wanted_by_book(labels):
    u"""札 → {(便, 本の #): {文の種類か節: frozenset((文の番号, 位置))}}。"""
    out = {}
    for lab in labels:
        out.setdefault((lab[u"便"], lab[u"#"]), {}).setdefault(lab[u"側"], set()).add((lab[u"si"], lab[u"pos"]))
    return dict((k, dict((s, frozenset(v)) for s, v in d.items())) for k, d in out.items())


def items_from_books(books, labels, pa_rec, expect=EXPECT_ROWS):
    u"""本の job の結果と札と便 PA の記録 → 送る行の列(鍵の昇順)。各行は指示文と指示文の sha256 を持つ。配線の確認(行の数・鍵の重なり・便 PA の記録の行に在るか)に違えば止める。
    (items, 配線の確認の数)。"""
    rows = link_rows(books)
    index = SC.index_rows(rows)
    matched = SC.match(labels, index)
    got = [(lab, row) for lab, row, _why in matched if row is not None]
    keys = [(r[0], r[1], r[2], r[3], r[4]) for _l, r in got]
    if len(set(keys)) != len(keys):
        raise Stop(u"**送る行の鍵が重なる。止める**")
    if len(got) != expect:
        raise Stop(u"**送る行の数が %d でない(%d)。止めて司令塔に返す**" % (expect, len(got)))
    pa_keys = set((r[0], r[1], r[2], r[3], r[4], r[5]) for r in pa_rec[u"行"])
    missing = [k for (_l, r), k in zip(got, keys) if k + (r[5],) not in pa_keys]
    if missing:
        raise Stop(u"**送る行の(鍵, state)が便 PA の記録の行に無い(%d 行)。止める**" % len(missing))
    got.sort(key=lambda g: row_order(*[g[1][i] for i in range(5)]))
    items = []
    bracket = 0
    for lab, r in got:
        batch, book, side, si, pos, state, empty, sentence, heading = r
        sb = MARK_OPEN in sentence or MARK_CLOSE in sentence
        hb = heading is not None and (MARK_OPEN in heading or MARK_CLOSE in heading)
        if sb or hb:
            bracket += 1
        prompt = build_prompt(heading, mark_sentence(sentence, pos))
        items.append(od([(u"batch", batch), (u"book", book), (u"side", side), (u"si", si), (u"pos", pos), (u"state", state), (u"empty", bool(empty)),
                         (u"label", lab), (u"prompt", prompt), (u"prompt_sha256", sha256_text(prompt)), (u"sent_bracket", sb), (u"head_bracket", hb)]))
    per_batch = od((b, od((s, sum(1 for it in items if it[u"batch"] == b and it[u"state"] == s)) for s in (u"V", u"G"))) for b in BATCHES)
    wire = od([(u"送る行の数(札つきで同じ state で引けた行)", len(items)), (u"封の行の数", expect), (u"札の数", len(labels)), (u"引けなかった札", len(labels) - len(items)),
               (u"便ごとの送る行(V・G)", per_batch), (u"送る行の鍵の重なり", 0),
               (u"送る行の(鍵, state)が便 PA の記録の行に在る", od([(u"在る行", len(items) - len(missing)), (u"無い行", len(missing)), (u"止まらなかった", True)])),
               (u"member の欄が空の行", sum(1 for it in items if it[u"empty"])),
               (u"文か見出しに元から 【 か 】 が在る行(数えるだけ。字は変えない)", bracket),
               (B_SENT, sum(1 for it in items if it[u"sent_bracket"])), (B_HEAD, sum(1 for it in items if it[u"head_bracket"])),
               (u"見出しが無い行(%s)" % NO_HEADING, sum(1 for it in items if it[u"prompt"].find(u"見出し: " + NO_HEADING + u"\n") >= 0))])
    return items, wire


# ======================================================================================================
# 入力・材料
def check_inputs(root):
    out = []
    for no, rel, want in INPUTS:
        p = os.path.join(root, rel)
        if not os.path.isfile(p) or ST.sha256_file(p) != want:
            raise Stop(u"**入力 %d の sha256 が封の表と違う。止める**" % no)
        out.append(od([(u"#", no), (u"path", rel), (u"sha256", want)]))
    return out


def load_all_records(root):
    u"""便 PA の ``load_records``(便 SC の記録を ``sc`` に持つ)に、便 PA の記録を ``pa`` として足す。"""
    recs = PA.load_records(root)
    recs[u"pa"] = load_json(os.path.join(root, PA_RECORD_REL))
    return recs


def collect_books(root, labels, recs, procs=1, material=None, cache_base=None, say=print, populations=None):
    u"""札つきの行が在る本だけを読んで、行の列(job の結果)を返す。(books, 材料の欄の字)。材料の置き場の件数と名前が変わったら止める。"""
    mat, prod = RT.material_dir(material)
    base = cache_base or KAM.default_base()
    if populations is None:
        tss_pop = ST.read_population(root)
        kam_pop = KAM.read_population(root)
        ys_pop = YS.read_population(root)
        SC.check_pop_record(kam_pop, recs[u"kam_pop"], u"KAM")
        SC.check_pop_record(ys_pop, recs[u"ys_pop"], u"YS")
    else:
        tss_pop, kam_pop, ys_pop = populations[u"TSS"], populations[u"KAM"], populations[u"YS"]
    shape = PA.subset_shape(tss_pop)
    ST.validate_population(tss_pop, *(shape or (ST.N_ROWS, ST.GROUP_COUNTS)))
    for (n, _g, _k, sha) in tss_pop:
        if not os.path.exists(os.path.join(mat, sha + u".zip")):
            raise Stop(u"**材料の ZIP が置き場に無い(# %d)。止める**" % n)
    before_tss = ST.names_snapshot(mat)
    before_cache = PA.folder_snapshots(base)
    kam_found = PA.scan_material(base, kam_pop)
    ys_found = PA.scan_material(base, ys_pop)
    want = wanted_by_book(labels)
    jobs = []
    for (n, g, _k, sha) in tss_pop:
        if (u"TSS", n) in want:
            jobs.append((u"TSS", n, g, sha, os.path.join(mat, sha + u".zip"), want[(u"TSS", n)]))
    for (n, g, sha) in kam_pop:
        if (u"KAM", n) in want:
            jobs.append((u"KAM", n, g, sha, kam_found[sha][0], want[(u"KAM", n)]))
    for (n, g, sha) in ys_pop:
        if (u"YS", n) in want:
            jobs.append((u"YS", n, g, sha, ys_found[sha][0], want[(u"YS", n)]))
    say(u"札つきの行が在る本 %d 本(TSS・KAM・YS の全 %d 本のうち)× %s ― procs %d" % (len(jobs), len(tss_pop) + len(kam_pop) + len(ys_pop), PROFILE, procs))
    books = TS.NF.map_pool(book_job, jobs, procs)
    if before_tss != ST.names_snapshot(mat) or before_cache != PA.folder_snapshots(base):
        raise Stop(u"**材料の置き場の件数か名前が変わった。止める**")
    material_cell = od([(u"TSS の置き場", ST.display_path(mat) if prod else u"使い捨ての置き場(本番の folder ではない)"),
                        (u"KAM・YS の置き場", u"~/.cache/audit-core の 3 つの folder(甲・乙・丙。名前は書かない)"),
                        (u"表と一致した ZIP", od([(u"TSS", len(tss_pop)), (u"KAM", len(kam_pop)), (u"YS", len(ys_pop))])),
                        (u"札つきの行が在って読んだ本", len(jobs))])
    return books, material_cell


def collect_items(root=ROOT, procs=1, material=None, cache_base=None, say=print, recs=None, inputs=None, populations=None, books=None):
    u"""入力の確かめ → 札 → 材料から行 → 送る行(指示文つき)。(items, 配線の確認の字, 入力の欄, 記録の組, 指紋, 札, 材料の欄)。通信しない・鍵を読まない。
    ``recs``(入力の記録。便 PA の記録を ``pa``・便 SC の記録を ``sc`` に持つ)・``books`` を渡すと(試験用)入力の確かめと材料の読みを飛ばす。"""
    if recs is None:
        inputs = check_inputs(root)
        recs = load_all_records(root)
    inputs = inputs or []
    fp = PA.engine_fp(recs[u"rt"])
    labels = SC.build_labels(recs)
    material_cell = None
    if books is None:
        books, material_cell = collect_books(root, labels, recs, procs, material, cache_base, say, populations)
    items, wire = items_from_books(books, labels, recs[u"pa"], EXPECT_ROWS)
    return items, wire, inputs, recs, fp, labels, material_cell


# ======================================================================================================
# API(通信する唯一の所)
def call_api(prompt, model, key):
    u"""(status, body)。HTTP の 4xx・5xx は例外にせず status で返す。例外の文には鍵を通さない(型だけ)。"""
    body = json.dumps({"model": model, "max_tokens": MAX_TOKENS, "thinking": THINKING[model],
                       "messages": [{"role": "user", "content": prompt}]}).encode("utf-8")
    req = urllib.request.Request(GEN.API_URL, data=body, method="POST",
                                 headers={"content-type": "application/json", "x-api-key": key, "anthropic-version": GEN.API_VERSION})
    try:
        with urllib.request.urlopen(req, timeout=GEN.TIMEOUT_SEC) as r:
            return r.getcode(), r.read()
    except urllib.error.HTTPError as e:
        try:
            return e.code, e.read()
        except Exception:                                # noqa: BLE001
            return e.code, b""
    except Exception as e:                               # noqa: BLE001  通信の失敗。文は捨てる
        return None, type(e).__name__.encode("ascii", "replace")


def get_key():
    key = os.environ.get(KEY_ENV)
    if not key:
        raise Stop(u"**環境変数 %s が無い。止める**" % KEY_ENV)
    return key


def parse_response(body):
    u"""HTTP 200 の返事の字 → {text, blocks, stop_reason, tin, tout} か None(形が読めない)。text は type が text の block の text だけをつなぐ。"""
    try:
        res = json.loads(body.decode("utf-8"))
        content = [b for b in res.get("content", []) if isinstance(b, dict)]
        text = u"".join(b.get("text") for b in content if b.get("type") == "text" and isinstance(b.get("text"), str))
        usage = res.get("usage") or {}
        return {u"text": text, u"blocks": [b.get("type") for b in content], u"stop_reason": res.get("stop_reason"),
                u"tin": usage.get("input_tokens"), u"tout": usage.get("output_tokens")}
    except Exception:                                    # noqa: BLE001  形が違う返事。文は捨てる
        return None


def usage_returned(status, body):
    u"""返った(usage まで読めた)呼び出しか。違えば見積りの額で数える。"""
    if status != 200:
        return False
    p = parse_response(body)
    return p is not None and isinstance(p[u"tin"], int) and isinstance(p[u"tout"], int)


def error_message_of(body, key=None, limit=300):
    u"""HTTP 4xx・5xx の本文の error.message(短く)。鍵らしい字が在れば残さない(型だけ)。読めなければ None。本文のほかの欄は残さない。"""
    try:
        m = json.loads(body.decode("utf-8"))["error"]["message"]
    except Exception:                                    # noqa: BLE001
        return None
    if not isinstance(m, str):
        return None
    m = m[:limit]
    if GEN.key_leaks(m, key, False):
        return u"(鍵らしい字が在るので残さない)"
    return m


def do_call(prompt, seat, key, transport, sleep, cum, cap, row, attempt, script_sha):
    u"""1 行 1 席 1 回の呼び出し(HTTP の再試行を含む)。(呼び出しの記録(OrderedDict), 返った text か None)。
    上限は transport を呼ぶ前に毎回見る(累計 + この呼び出しで見積りの額を数えた分 + 次の見積り > 上限 なら止める)。返らなかった呼び出しは 1 回ごとに見積りの額を数える。"""
    est = estimate_usd(len(prompt))
    meter = {"extra": 0.0}

    def metered(p, model, k):
        if cum + meter["extra"] + est > cap:
            raise CapStop()
        status, body = transport(p, model, k)
        if not usage_returned(status, body):
            meter["extra"] += est
        return status, body

    item = od([(u"row", row), (u"seat", seat), (u"attempt", attempt), (u"aborted", False), (u"prompt_sha256", sha256_text(prompt)), (u"est_usd", round(est, 6)),
               (u"script_sha256", script_sha[:16]), (u"retries", 0), (u"http_status", None), (u"stop_reason", None), (u"blocks", None), (u"tin", None), (u"tout", None),
               (u"chars", None), (u"reply_sha256", None), (u"answer", None), (u"usage_usd", 0.0), (u"est_counted_usd", 0.0), (u"cost_usd", 0.0)])
    try:
        status, body, retries = GEN.call_with_retry(prompt, seat, key, metered, sleep)
    except CapStop:
        item.update({u"attempt": None, u"aborted": True, u"capped": True, u"est_counted_usd": round(meter["extra"], 6), u"cost_usd": round(meter["extra"], 6)})
        return item, None
    item[u"retries"] = retries
    item[u"http_status"] = status
    text = None
    usable = usage_returned(status, body)
    p = parse_response(body) if status == 200 else None
    usage_cost = cost_usd(p[u"tin"], p[u"tout"]) if usable else 0.0
    if p is not None:
        text = p[u"text"]
        item.update({u"stop_reason": p[u"stop_reason"], u"blocks": p[u"blocks"], u"tin": p[u"tin"], u"tout": p[u"tout"], u"chars": len(text)})
        item[u"answer"] = read_answer(text, p[u"stop_reason"])
        if item[u"answer"] is not None:
            item[u"answer"] = list(item[u"answer"])
    if status is not None and status >= 400:
        item[u"error_message"] = error_message_of(body, key)
    item[u"usage_usd"] = round(usage_cost, 6)
    item[u"est_counted_usd"] = round(meter["extra"], 6)
    item[u"cost_usd"] = round(usage_cost + meter["extra"], 6)
    return item, text


# ======================================================================================================
# 途中の答え(``--resume`` 用。追跡しない置き場にだけ置く)
def new_state():
    return od([(u"seal", SEAL_REL), (u"calls", []), (u"in_flight", None), (u"stopped", None)])


def state_path(work):
    return os.path.join(work, STATE_NAME)


def load_state(work):
    p = state_path(work)
    if not os.path.exists(p):
        return None
    with io.open(p, encoding="utf-8") as fh:
        st = json.load(fh, object_pairs_hook=collections.OrderedDict)
    if st.get(u"seal") != SEAL_REL:
        raise Stop(u"**途中の答えの file が別の便のもの。止める**")
    return st


def save_state(work, state):
    GEN.write_text(state_path(work), json.dumps(state, ensure_ascii=False, indent=1) + u"\n")


def seat_attempts(state, row, seat):
    return [c for c in state[u"calls"] if c[u"row"] == row and c[u"seat"] == seat and not c[u"aborted"]]


def seat_answer(state, row, seat):
    for c in seat_attempts(state, row, seat):
        if c[u"answer"] is not None:
            return tuple(c[u"answer"])
    return None


def seat_done(state, row, seat, max_attempts=MAX_ANSWER_ATTEMPTS):
    return seat_answer(state, row, seat) is not None or len(seat_attempts(state, row, seat)) >= max_attempts


def state_cost(state):
    return round(sum(c[u"cost_usd"] for c in state[u"calls"]), 6)


def retire_config_failures(state):
    u"""前の走りが HTTP 400・401・403(設定の誤り)で止めた呼び出しは答えの回に数えない(答えは 1 つも返っていない)。額は残したまま中断した呼び出しの側へ移す(上限をすり抜けさせない)。"""
    n = 0
    for c in state[u"calls"]:
        if not c[u"aborted"] and c[u"http_status"] in STOP_HTTP:
            c[u"aborted"] = True
            c[u"attempt"] = None
            c[u"config_error"] = c[u"http_status"]
            n += 1
    return n


def resolve_in_flight(state):
    u"""前の走りが呼んでいる最中に止まっていたら、その呼び出しは見積りの額で数える(中断した呼び出しは上限をすり抜けさせない)。"""
    f = state.get(u"in_flight")
    if not f:
        return False
    state[u"calls"].append(od([(u"row", f[u"row"]), (u"seat", f[u"seat"]), (u"attempt", None), (u"aborted", True), (u"prompt_sha256", f[u"prompt_sha256"]), (u"est_usd", f[u"est_usd"]),
                               (u"script_sha256", None), (u"retries", 0), (u"http_status", None), (u"stop_reason", None), (u"blocks", None), (u"tin", None), (u"tout", None),
                               (u"chars", None), (u"reply_sha256", None), (u"answer", None), (u"usage_usd", 0.0), (u"est_counted_usd", f[u"est_usd"]), (u"cost_usd", f[u"est_usd"]),
                               (u"interrupted", True)]))
    state[u"in_flight"] = None
    return True


def reply_path(work, row, seat, attempt):
    return os.path.join(work, "replies", "%03d_%s_%d.txt" % (row, SEAT_FILE[seat], attempt))


def prompt_path(work, row):
    return os.path.join(work, "prompts", "%03d.txt" % row)


def write_prompts(items, work):
    u"""送る文を置き場に置く。既に在る file は同じ字でなければ止める。"""
    for i, it in enumerate(items):
        p = prompt_path(work, i)
        if os.path.exists(p):
            with io.open(p, encoding="utf-8") as fh:
                if fh.read() != it[u"prompt"]:
                    raise Stop(u"**置き場の送る文が今組んだ指示文と違う(行 %d)。止める**" % i)
        else:
            GEN.write_text(p, it[u"prompt"])


def check_state(items, state, work):
    u"""途中の答えが今の指示文・今の置き場の返った text と合う(違えば止める)。"""
    for c in state[u"calls"]:
        i = c[u"row"]
        if not 0 <= i < len(items) or c[u"seat"] not in SEATS:
            raise Stop(u"**途中の答えの行の番号か席が今の行の列と合わない。止める**")
        if c[u"prompt_sha256"] != items[i][u"prompt_sha256"]:
            raise Stop(u"**途中の答えの指示文の sha256 が今組んだ指示文と違う(行 %d)。止める**" % i)
        if c[u"reply_sha256"] is not None:
            p = reply_path(work, i, c[u"seat"], c[u"attempt"])
            if not os.path.exists(p):
                raise Stop(u"**途中の答えの返った text が置き場に無い(行 %d)。止める**" % i)
            with io.open(p, encoding="utf-8") as fh:
                if sha256_text(fh.read()) != c[u"reply_sha256"]:
                    raise Stop(u"**途中の答えの返った text の sha256 が記録と違う(行 %d)。止める**" % i)


def max_estimate(items, state, rows_limit=None, one_attempt=False):
    u"""まだ済んでいない(行, 席)を、残りの回数が最大のときの見積り。(額, 呼び出しの最大の数)。"""
    ma = 1 if one_attempt else MAX_ANSWER_ATTEMPTS
    total, n = 0.0, 0
    for i, it in enumerate(items[:rows_limit]):
        for seat in SEATS:
            if seat_answer(state, i, seat) is not None:
                continue
            left = max(0, ma - len(seat_attempts(state, i, seat)))
            n += left
            total += left * estimate_usd(len(it[u"prompt"]))
    return total, n


def plan_problem(items, state, rows_limit=None, one_attempt=False, cap=COST_CAP_USD, say=print):
    u"""走らせる前の止め。使った額 + 残りを最大の回数で見積った額が上限を超えるなら理由の文、超えなければ None。"""
    base = state_cost(state)
    est, n = max_estimate(items, state, rows_limit, one_attempt)
    say(u"走らせる前の確かめ: 使った額 %.4f USD + 残り最大 %d 回の見積り %.4f USD = %.4f USD(上限 %.2f)" % (base, n, est, base + est, cap))
    if base + est > cap:
        return u"**使った額 %.4f + 残りの見積り %.4f = %.4f USD が上限 %.2f USD を超える。1 回も呼ばずに止める**" % (base, est, base + est, cap)
    return None


def run_calls(items, state, work, key, transport=call_api, sleep=None, say=print, rows_limit=None, one_attempt=False, cap=COST_CAP_USD):
    u"""行の順に、行ごとに 主の席・副の席の順で呼ぶ。済んだ(行, 席)は飛ばす。一度に書く file は呼ぶたびに更新する(止まっても累計が残る)。
    ``one_attempt`` は試し(1 回だけ。読めなければ本番の ``--resume`` で 2 回目を呼ぶ)。止める事情(上限・HTTP 400/401/403)は ``Stop``。"""
    sleep = sleep if sleep is not None else time.sleep
    this_sha = ST.sha256_file(os.path.abspath(__file__))
    check_state(items, state, work)
    if resolve_in_flight(state) | bool(retire_config_failures(state)):
        save_state(work, state)
    problem = plan_problem(items, state, rows_limit, one_attempt, cap, say)
    if problem:
        raise Stop(problem)
    write_prompts(items, work)
    max_attempts = 1 if one_attempt else MAX_ANSWER_ATTEMPTS
    n_new = 0
    for i, it in enumerate(items[:rows_limit]):
        for seat in SEATS:
            while True:
                att = seat_attempts(state, i, seat)
                if seat_answer(state, i, seat) is not None or len(att) >= max_attempts:
                    break
                attempt = len(att) + 1
                est = estimate_usd(len(it[u"prompt"]))
                state[u"in_flight"] = od([(u"row", i), (u"seat", seat), (u"prompt_sha256", it[u"prompt_sha256"]), (u"est_usd", round(est, 6))])
                save_state(work, state)
                item, text = do_call(it[u"prompt"], seat, key, transport, sleep, state_cost(state), cap, i, attempt, this_sha)
                if text:
                    GEN.write_text(reply_path(work, i, seat, attempt), text)
                    item[u"reply_sha256"] = sha256_text(text)
                state[u"in_flight"] = None
                if item[u"cost_usd"] > 0 or not item.get(u"capped"):
                    state[u"calls"].append(item)
                n_new += 1
                if item.get(u"capped"):
                    state[u"stopped"] = u"累計 %.4f + 次の見積り %.4f が上限 %.2f USD を超える(行 %d・%s の前)" % (state_cost(state), est, cap, i, SEAT_TAG[seat])
                    save_state(work, state)
                    raise Stop(u"**%s**" % state[u"stopped"])
                save_state(work, state)
                say(u"  行 %3d %s %d 回目 http=%s stop=%s block=%s 字数=%s %s 累計 %.4f USD" % (
                    i, SEAT_TAG[seat], attempt, item[u"http_status"], item[u"stop_reason"], u",".join(x or u"?" for x in (item[u"blocks"] or [])), item[u"chars"],
                    u"読めた" if item[u"answer"] is not None else u"読めない", state_cost(state)))
                if item[u"http_status"] in STOP_HTTP:
                    say(u"  HTTP %s の断りの文: %s" % (item[u"http_status"], item.get(u"error_message")))
                    state[u"stopped"] = u"HTTP %s(設定の誤りか鍵の問題)" % item[u"http_status"]
                    save_state(work, state)
                    raise Stop(u"**HTTP %s。全体を止める**" % item[u"http_status"])
    return n_new


# ======================================================================================================
# 記録の行・呼び出しの欄
def answer_cells(ans):
    return (NO_ANSWER, NO_ANSWER) if ans is None else (ans[0], ans[1])


def build_rows(items, state):
    u"""記録の行。1 行 = 送る行 1 つ。席ごとの答え(語か「答えなし」)・指示文の sha256・席ごとの呼び出しの数(HTTP の再試行を除く)。"""
    rows = []
    for i, it in enumerate(items):
        m, s = SEATS
        ma, sa = answer_cells(seat_answer(state, i, m)), answer_cells(seat_answer(state, i, s))
        rows.append([it[u"batch"], it[u"book"], it[u"side"], it[u"si"], it[u"pos"], it[u"state"], it[u"empty"], ma[0], ma[1], sa[0], sa[1], it[u"prompt_sha256"],
                     len(seat_attempts(state, i, m)), len(seat_attempts(state, i, s)), it[u"sent_bracket"], it[u"head_bracket"]])
    return rows


def build_call_rows(state):
    out = []
    for c in state[u"calls"]:
        out.append([c[u"row"], SEAT_TAG[c[u"seat"]], c[u"attempt"], bool(c[u"aborted"]), c[u"http_status"], c[u"retries"], c[u"stop_reason"], u",".join(x or u"?" for x in (c[u"blocks"] or [])),
                    c[u"tin"], c[u"tout"], c[u"usage_usd"], c[u"est_counted_usd"], c[u"chars"], c[u"answer"] is not None])
    return out


# ======================================================================================================
# 数えるもの(封 §2-5)。記録の行・呼び出しの欄・札・便 SC の記録・便 PA の記録だけから作る(--check が同じ関数で作り直す)
def views_of(rows, labels, sc_rec, pa_rec):
    u"""記録の行 → 数える行(札・席ごとの答え・語の表の止め)の列。札・便 SC・便 PA の行が鍵で引けなければ止める。"""
    lab_by = dict((SC.label_key(lab), lab) for lab in labels)
    sc_by = dict(((r[0], r[1], r[2], r[3], r[4]), r) for r in sc_rec[u"行"])
    pa_by = dict(((r[0], r[1], r[2], r[3], r[4]), r) for r in pa_rec[u"行"])
    out = []
    for r in rows:
        k = (r[C_BATCH], r[C_BOOK], r[C_SIDE], r[C_SI], r[C_POS])
        if k not in lab_by or lab_by[k][u"state"] != r[C_STATE] or k not in sc_by or k not in pa_by:
            raise Stop(u"**記録の行の鍵が札か便 SC・便 PA の記録に無い。止める**")
        ws = sc_by[k][SC.C_H2] != u""
        wp = pa_by[k][PA.C_H2] != u""
        ans = []
        for a, b in ((r[C_MR], r[C_MN]), (r[C_SR], r[C_SN])):
            ans.append(None if a == NO_ANSWER else (a, b))
        out.append(od([(u"batch", k[0]), (u"key", k), (u"label", lab_by[k]), (u"empty", bool(r[C_EMPTY])), (u"sb", bool(r[C_SB])), (u"hb", bool(r[C_HB])), (u"main", ans[0]), (u"sub", ans[1]), (u"WS", ws), (u"WP", wp), (u"WU", ws or wp)]))
    return out


def is_v(lab):
    return lab[u"state"] == u"V"


def is_range(lab):
    return is_v(lab) and SC.is_range(lab)


def is_plan(lab):
    return is_v(lab) and PA.is_plan(lab)


def is_drop(lab):
    return is_v(lab) and SC.is_drop(lab)


def is_other(lab):
    return is_v(lab) and not SC.is_range(lab) and not PA.is_plan(lab) and not SC.is_drop(lab)


def g_type(lab, t):
    return lab[u"state"] == u"G" and lab[u"型"] == t


#: 札の束(封 §2-5 の 1・2)。名前 → 札を取る述語
BUCKETS = collections.OrderedDict([
    (u"札つきの行の全部", lambda lab: True),
    (u"V の札の全部(分母から除く札を含む)", is_v),
    (u"V 「範囲」の札", is_range),
    (u"V 「見積り・計画」の札", is_plan),
    (u"V 「それ以外」の札(分母から除く札は除く)", is_other),
    (u"V 分母から除く札", is_drop),
    (u"V 「範囲」と「見積り・計画」の札の合わせ", lambda lab: is_range(lab) or is_plan(lab)),
    (u"G の札(KAM・YS)の全部", lambda lab: lab[u"state"] == u"G"),
    (u"G 札 a", lambda lab: g_type(lab, u"a")),
    (u"G 札 b", lambda lab: g_type(lab, u"b")),
    (u"G 札 b のうち「違うもの」が範囲", lambda lab: g_type(lab, u"b") and lab[u"違うもの"] == u"範囲"),
    (u"G 札 b のうち「違うもの」が範囲でない", lambda lab: g_type(lab, u"b") and lab[u"違うもの"] != u"範囲"),
    (u"G 札 c", lambda lab: g_type(lab, u"c")),
])
COLS = (u"全体",) + tuple(BATCHES)
RULES = (u"S", u"P", u"U")
RULE_FIELD = {u"S": (u"WS", 0), u"P": (u"WP", 1), u"U": (u"WU", 2)}
SEAT_KEY = collections.OrderedDict([(u"主", u"main"), (u"副", u"sub")])
DIST_KEYS = [u"%s / %s" % (a, b) for a in RANGE_WORDS for b in NATURE_WORDS] + [NO_ANSWER]


def seat_cell(vs, field):
    u"""行の集まりと席(``main`` か ``sub``)→ 止めた数・答えなし・答えの分布・語の表との重なり。"""
    stopped = dict((r, 0) for r in RULES)
    overlap = od((r, collections.Counter()) for r in RULES)
    dist = collections.Counter()
    none = 0
    for v in vs:
        a = v[field]
        if a is None:
            none += 1
            dist[NO_ANSWER] += 1
        else:
            dist[u"%s / %s" % a] += 1
        flags = stops_of(a, v[u"empty"])
        for rule in RULES:
            seat_stop = flags[RULE_FIELD[rule][1]]
            stopped[rule] += 1 if seat_stop else 0
            overlap[rule][(bool(v[RULE_FIELD[rule][0]]), seat_stop)] += 1
    return od([(u"止めた行", od((u"L-" + r, stopped[r]) for r in RULES)), (u"答えなしの行", none),
               (u"答えの分布(範囲 / 性質)", od((k, dist.get(k, 0)) for k in DIST_KEYS)),
               (u"語の表との重なり", od((r, od([(u"語の表も席も止めた", overlap[r][(True, True)]), (u"語の表だけが止めた", overlap[r][(True, False)]),
                                                (u"席だけが止めた", overlap[r][(False, True)]), (u"どちらも止めない", overlap[r][(False, False)])])) for r in RULES))])


def agree_cell(vs):
    u"""2 つの席の答えの一致(封 §2-5 の 4)。範囲・性質のそれぞれで、両方に答えが在る行・同じ答えの行。答えなしの行は別に。"""
    both = [v for v in vs if v[u"main"] is not None and v[u"sub"] is not None]
    return od([(u"両方の席に答えが在る行", len(both)),
               (u"範囲が同じ答えの行", sum(1 for v in both if v[u"main"][0] == v[u"sub"][0])),
               (u"性質が同じ答えの行", sum(1 for v in both if v[u"main"][1] == v[u"sub"][1])),
               (u"範囲と性質の両方が同じ答えの行", sum(1 for v in both if v[u"main"] == v[u"sub"])),
               (u"どちらかの席が答えなしの行", len(vs) - len(both)), (u"両方の席が答えなしの行", sum(1 for v in vs if v[u"main"] is None and v[u"sub"] is None))])


def tally_cell(vs):
    return od([(u"行", len(vs)), (u"member の欄が空の行", sum(1 for v in vs if v[u"empty"])),
               (u"語の表で止めた行", od([(u"W-S(便 SC の段 2)", sum(1 for v in vs if v[u"WS"])), (u"W-P(便 PA の段 2)", sum(1 for v in vs if v[u"WP"])),
                                    (u"W-U(どちらか)", sum(1 for v in vs if v[u"WU"]))])),
               (u"主の席", seat_cell(vs, u"main")), (u"副の席", seat_cell(vs, u"sub")), (u"2 つの席の一致", agree_cell(vs))])


def other_attrs(views):
    u"""「それ以外」の札の属性の名(札の先)の並び(字の順)。"""
    return sorted(set(SC.cat_name(v[u"label"]) for v in views if is_other(v[u"label"])))


def tally(views):
    u"""束 × 便(と全体)の数。「それ以外」の札は属性ごとにも(封 §2-5 の 1)。"""
    out = od()
    buckets = list(BUCKETS.items()) + [(u"V 「それ以外」の札 / 属性 %s" % nm, (lambda lab, nm=nm: is_other(lab) and SC.cat_name(lab) == nm)) for nm in other_attrs(views)]
    for name, pred in buckets:
        sel = [v for v in views if pred(v[u"label"])]
        out[name] = od((col, tally_cell(sel if col == u"全体" else [v for v in sel if v[u"batch"] == col])) for col in COLS)
    for name, field in ((B_SENT, u"sb"), (B_HEAD, u"hb")):
        sel = [v for v in views if v[field]]
        out[name] = od((col, tally_cell(sel if col == u"全体" else [v for v in sel if v[u"batch"] == col])) for col in COLS)
    return out


def pairs_of(values):
    u"""API の返事の字(block の type・stop_reason・HTTP の状態)の種類 → [[字, 回数], ...](字の順)。字を dict の key にしない(``text`` などの禁止欄に当たるため)。"""
    return [[k, v] for k, v in sorted(collections.Counter(values).items())]


def call_tally(call_rows, n_rows):
    u"""呼び出しの欄 → 席ごとの数(封 §2-5 の 6)。回数・答えのやり直し・答えなし・token・USD・block の type の並びの種類・stop_reason の種類・HTTP の状態。"""
    out = od()
    total_usd = 0.0
    for seat, tag in SEAT_TAG.items():
        cs = [c for c in call_rows if c[K_SEAT] == tag]
        real = [c for c in cs if not c[K_ABORT]]
        none_rows = n_rows - len(set(c[K_ROW] for c in real if c[K_OK]))
        usd_u = round(sum(c[K_USD_U] for c in cs), 6)
        usd_e = round(sum(c[K_USD_E] for c in cs), 6)
        total_usd += usd_u + usd_e
        out[tag] = od([(u"model", seat), (u"呼び出しの数(HTTP の再試行を除く。中断した呼び出しを除く)", len(real)), (u"うち 1 回目", sum(1 for c in real if c[K_ATT] == 1)),
                       (u"答えのやり直し(封 §2-3)", sum(1 for c in real if c[K_ATT] == 2)), (u"HTTP の再試行(429・5xx)の合計", sum(c[K_RETRY] for c in real)),
                       (u"中断した(次の走りで見つけた・上限で止めた)呼び出し", sum(1 for c in cs if c[K_ABORT])),
                       (u"答えなしの行", none_rows), (u"入力 token の合計", sum(c[K_TIN] or 0 for c in cs)), (u"出力 token の合計", sum(c[K_TOUT] or 0 for c in cs)),
                       (u"USD(返った usage で。§3 の単価)", usd_u), (u"USD(返らなかった呼び出しの見積りで数えた分)", usd_e), (u"USD 合計", round(usd_u + usd_e, 6)),
                       (u"返った block の type の並びの種類", pairs_of(c[K_BLOCKS] for c in real if c[K_BLOCKS] is not None)),
                       (u"stop_reason の種類", pairs_of(str(c[K_STOP]) for c in real)),
                       (u"HTTP の状態の種類", pairs_of(str(c[K_HTTP]) for c in real))])
    out[u"USD の全部"] = round(total_usd, 6)
    return out


def pct_diff(a_n, a_d, b_n, b_d):
    u"""(a の率 − b の率)× 100 を小数 2 桁の字で(RT の ``point_diff``。分母 0 があれば「分母 0」)。"""
    return RT.point_diff(b_n, b_d, a_n, a_d)


def predictions(views):
    u"""封 §5 の LX-1〜LX-11 の判定に要る数(主の席の数。副の席・語の表は隣に)。当たり・外れは書かない(結果の文書で)。"""
    def sel(pred, batches=None):
        return [v for v in views if pred(v[u"label"]) and (batches is None or v[u"batch"] in batches)]

    def stops(vs, field, rule):
        return sum(1 for v in vs if stops_of(v[field], v[u"empty"])[RULE_FIELD[rule][1]])

    def wstops(vs, rule):
        return sum(1 for v in vs if v[RULE_FIELD[rule][0]])

    def pair(vs, rule):
        return od([(u"行", len(vs)), (u"主の席", stops(vs, u"main", rule)), (u"副の席", stops(vs, u"sub", rule)), (u"語の表", wstops(vs, rule))])

    rng, plan, other = sel(is_range), sel(is_plan), sel(is_other)
    both = rng + plan
    g_a = sel(lambda lab: g_type(lab, u"a"))
    g_b_range = sel(lambda lab: g_type(lab, u"b") and lab[u"違うもの"] == u"範囲")
    out = od()
    out[u"LX-1 L-S の止めた行 / V 「範囲」の札"] = pair(rng, u"S")
    out[u"LX-2 L-S の止めた行 / V 「範囲」の札(KAM と YS)"] = pair(sel(is_range, (u"KAM", u"YS")), u"S")
    out[u"LX-3 L-S の止めた行 / G 札 a"] = pair(g_a, u"S")
    out[u"LX-4 L-P の止めた行 / V 「見積り・計画」の札"] = pair(plan, u"P")
    out[u"LX-5 L-P の止めた行 / V 「見積り・計画」の札(YS)"] = pair(sel(is_plan, (u"YS",)), u"P")
    out[u"LX-6 L-P の止めた行 / G 札 a"] = pair(g_a, u"P")
    out[u"LX-7 L-S の止めた行 / G 札 b のうち「違うもの」が範囲"] = pair(g_b_range, u"S")
    out[u"LX-8 L-U の止めた行(V 「範囲」と「見積り・計画」の合わせ / G 札 a)と W-U との差(席 − 語の表)"] = od([
        (u"V 「範囲」と「見積り・計画」の合わせ", pair(both, u"U")),
        (u"V の差(主の席 − 語の表)", stops(both, u"main", u"U") - wstops(both, u"U")),
        (u"G 札 a", pair(g_a, u"U")), (u"G 札 a の差(主の席 − 語の表)", stops(g_a, u"main", u"U") - wstops(g_a, u"U"))])
    out[u"LX-9 L-U の止めた行 / 行(V 「それ以外」の札と、「範囲」と「見積り・計画」の合わせ)と率の差(ポイント。合わせ − それ以外)"] = od([
        (u"V 「それ以外」の札", rate(stops(other, u"main", u"U"), len(other))), (u"V 「範囲」と「見積り・計画」の合わせ", rate(stops(both, u"main", u"U"), len(both))),
        (u"率の差(ポイント)", pct_diff(stops(both, u"main", u"U"), len(both), stops(other, u"main", u"U"), len(other)))])
    ag = agree_cell(views)
    out[u"LX-10 2 つの席の答えの一致(札つきの行の全部)"] = od([
        (u"範囲", rate(ag[u"範囲が同じ答えの行"], ag[u"両方の席に答えが在る行"])), (u"性質", rate(ag[u"性質が同じ答えの行"], ag[u"両方の席に答えが在る行"]))])
    out[u"LX-11 主の席の答えなしの行"] = sum(1 for v in views if v[u"main"] is None)
    out[u"分母の確かめ(前の記録の数と違えば結果の文書にそう書く)"] = od([
        (u"V 「範囲」の札", len(rng)), (u"V 「範囲」の札(KAM と YS)", len(sel(is_range, (u"KAM", u"YS")))), (u"V 「見積り・計画」の札", len(plan)),
        (u"V 「見積り・計画」の札(YS)", len(sel(is_plan, (u"YS",)))), (u"V 「それ以外」の札", len(other)), (u"G 札 a", len(g_a)), (u"G 札 b のうち「違うもの」が範囲", len(g_b_range)),
        (u"札つきの行の全部", len(views))])
    return out


def derived_sections(rows, call_rows, labels, sc_rec, pa_rec):
    u"""記録の行と呼び出しの欄から作る欄(§2-5 の 1〜6・予測の判定に要る数)。作る側(本番)と照らす側(--check)が同じ関数を使う。"""
    views = views_of(rows, labels, sc_rec, pa_rec)
    pred = predictions(views)
    pred[REF_KEY] = predictions([v for v in views if not (v[u"sb"] or v[u"hb"])])
    return od([(K_TALLY, tally(views)), (K_CALLS, call_tally(call_rows, len(rows))), (K_PRED, pred)])


# ======================================================================================================
# 記録
def check_text(rec, text, key_value=None):
    scan = text
    for rel in [SEAL_REL, SCRIPT_REL, RECORD_REL] + [r for _no, r, _sha in INPUTS]:
        scan = scan.replace(rel, u"")
    TSS.check_clean(rec, scan, key_value)


def record_text(rec, key_value=None):
    text = dumps(rec) + u"\n"
    check_text(rec, text, key_value)
    return text


def build_record(items, state, labels, recs, inputs, fp, wire, material_cell):
    u"""全部の(行, 席)が済んだ途中の答え → 記録(OrderedDict)。書かない。"""
    rows = build_rows(items, state)
    call_rows = build_call_rows(state)
    rec = od()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"封の追記の commit"] = SEAL_ADDENDUM_COMMIT
    rec[u"封の追記 2 の commit"] = SEAL_ADDENDUM2_COMMIT
    rec[u"step"] = u"LX(文の字だけを読んだ LLM の席の答え(範囲・性質)で結んだ行を止める後付けの規則 ― L-S・L-P・L-U。語の表(便 SC・便 PA の段 2)と並べる)(有料・engine は 0 行)"
    rec[u"この script の sha256"] = ST.sha256_file(os.path.abspath(__file__))
    rec[u"入力"] = inputs
    rec[u"engine の指紋(今。便 RT の記録の今と同じ)"] = fp
    rec[u"profile"] = PROFILE
    rec[u"材料"] = material_cell
    rec[u"席"] = od([(u"主の席", od([(u"model", SEATS[0]), (u"thinking", THINKING[SEATS[0]])])), (u"副の席", od([(u"model", SEATS[1]), (u"thinking", THINKING[SEATS[1]])]))])
    rec[u"呼び出しの形"] = od([(u"max_tokens", MAX_TOKENS), (u"temperature", u"送らない(封 §9)"), (u"API の版", GEN.API_VERSION), (u"送り先", GEN.API_URL),
                          (u"HTTP の再試行", u"429 / 5xx のときだけ最大 %d 回(待ち %s 秒)" % (len(GEN.RETRY_WAITS), list(GEN.RETRY_WAITS))),
                          (u"答えのやり直し", u"読めない答えは同じ指示文でもう 1 回だけ(封 §2-3)"), (u"system", u"無し(user の 1 message)")])
    rec[u"指示文の型(封 §2-2)"] = od([(u"字", PROMPT_TEMPLATE), (u"sha256", sha256_text(PROMPT_TEMPLATE)), (u"置き換える所", list(PLACEHOLDERS))])
    rec[u"回数"] = od([(u"行", len(items)), (u"席", len(SEATS)), (u"呼び出しの予定", len(items) * len(SEATS)), (u"やり直しを入れた最大", len(items) * len(SEATS) * MAX_ANSWER_ATTEMPTS)])
    rec[u"費用"] = od([(u"上限 USD", COST_CAP_USD), (u"単価 入力 USD / M tokens", PRICE_IN), (u"単価 出力 USD / M tokens", PRICE_OUT),
                     (u"見積りの規則", u"入力の字数 × 1.0 を token とみなし、出力は max_tokens の全部(保守的な単価を両席に当てる)"),
                     (u"使った額 USD", state_cost(state))])
    rec[K_WIRE] = wire
    rec[u"行の欄"] = list(ROW_COLUMNS)
    rec[u"行"] = rows
    rec[u"呼び出しの欄"] = list(CALL_COLUMNS)
    rec[u"呼び出し"] = call_rows
    for k, v in derived_sections(rows, call_rows, labels, recs[u"sc"], recs[u"pa"]).items():
        rec[k] = v
    rec[u"限界"] = list(LIMITS)
    rec[u"key_leaks"] = []
    return rec


def write_record(path, rec, key_value=None):
    u"""書く前と書いた後に鍵の検査を当てる。既に在れば止める(測り直さない)。"""
    if os.path.exists(path):
        raise Stop(u"**記録が既に在る: %s。止める**" % os.path.basename(path))
    text = record_text(rec, key_value)
    ST.write_text_exclusive(path, text)
    with io.open(path, encoding="utf-8") as fh:
        back = fh.read()
    try:
        check_text(rec, back, key_value)
    except SystemExit:
        os.remove(path)
        raise


def all_done(items, state):
    return all(seat_done(state, i, seat) for i in range(len(items)) for seat in SEATS)


# ======================================================================================================
# 入口
def trial_report(items, state, say):
    u"""試しの形(HTTP の状態・stop_reason・返った block の type・text の字数・答えが読めたか)。答えの中身・文は出さない。"""
    for c in state[u"calls"]:
        if c[u"aborted"] or c[u"row"] >= TRIAL_ROWS:
            continue
        say(u"  試し 行 %d %s: http=%s stop_reason=%s block=%s 字数=%s 答えが読めた=%s" % (
            c[u"row"], SEAT_TAG[c[u"seat"]], c[u"http_status"], c[u"stop_reason"], u",".join(x or u"?" for x in (c[u"blocks"] or [])), c[u"chars"], c[u"answer"] is not None))


def run(root=ROOT, procs=1, material=None, cache_base=None, say=print, trial=False, resume=False, work=None, out=None, key=None, key_value=None,
        transport=call_api, sleep=None, recs=None, inputs=None, populations=None, books=None):
    u"""試し(``trial``)か本番。鍵は ``key``(試験用。無ければ環境変数)。本番は全部済んだときにだけ記録を書く。"""
    work = os.path.abspath(work or CACHE_DIR)
    out = out or os.path.join(root, RECORD_REL)
    if not trial and os.path.exists(out):
        raise Stop(u"**記録が既に在る: %s。止める**" % os.path.basename(out))
    exists = os.path.exists(state_path(work))
    if trial and exists:
        prev = load_state(work)
        if any(c[u"answer"] is not None or c[u"http_status"] == 200 for c in prev[u"calls"]):
            raise Stop(u"**途中の答えが既に在る(試しは答えが 1 つも返っていない置き場でだけ)。止める**")
    if not trial and exists and not resume:
        raise Stop(u"**途中の答えが既に在る。続きは --resume を付ける(有料の呼び出しを二度しない)。止める**")
    if TSS.inside_repo(work):
        raise Stop(u"**送った文と返った text の置き場が repo の中。追跡しない場所に置く。止める**")
    items, wire, inputs, recs, fp, labels, material_cell = collect_items(root=root, procs=procs, material=material, cache_base=cache_base, say=say, recs=recs, inputs=inputs,
                                                                         populations=populations, books=books)
    state = load_state(work) if exists else new_state()
    key = key if key is not None else get_key()
    n = run_calls(items, state, work, key, transport=transport, sleep=sleep, say=say, rows_limit=TRIAL_ROWS if trial else None, one_attempt=trial)
    say(u"新しく呼んだ %d・累計 %.4f USD" % (n, state_cost(state)))
    if trial:
        trial_report(items, state, say)
        return state
    if not all_done(items, state):
        raise Stop(u"**まだ済んでいない(行, 席)が在る。止める**")
    rec = build_record(items, state, labels, recs, inputs, fp, wire, material_cell)
    write_record(out, rec, key_value if key_value is not None else key)
    say(u"-> %s" % os.path.basename(out))
    return rec


def dry_run(root=ROOT, procs=1, material=None, cache_base=None, say=print, **kw):
    u"""0 USD。鍵を読まない・通信しない・記録を書かない。本番と同じ関数で全部の指示文を組み、数と配線の確認を出す。作り物の transport で答えの読み方・やり直し・上限を通す。"""
    items, wire, inputs, recs, fp, labels, material_cell = collect_items(root=root, procs=procs, material=material, cache_base=cache_base, say=say, **kw)
    chars = sum(len(it[u"prompt"]) for it in items)
    est_one = sum(estimate_usd(len(it[u"prompt"])) for it in items) * len(SEATS)
    est_max = est_one * MAX_ANSWER_ATTEMPTS
    say(u"行の数: %d(封の行の数 %d)" % (len(items), EXPECT_ROWS))
    for b in BATCHES:
        say(u"  %s: V %d・G %d" % (b, wire[u"便ごとの送る行(V・G)"][b][u"V"], wire[u"便ごとの送る行(V・G)"][b][u"G"]))
    say(u"席ごとの本数: %s" % u"・".join(u"%s(%s)=%d 本" % (SEAT_TAG[s], s, len(items)) for s in SEATS))
    say(u"指示文: 全部で %d 本(行 %d × 席 %d)・字数の合計 %d(1 本あたり最小 %d・最大 %d・平均 %.1f)" % (
        len(items) * len(SEATS), len(items), len(SEATS), chars * len(SEATS), min(len(it[u"prompt"]) for it in items), max(len(it[u"prompt"]) for it in items), chars / float(len(items))))
    say(u"見積り(保守的な単価 入力 %.1f / 出力 %.1f USD / M tokens・入力 = 字数 × 1.0・出力 = max_tokens %d): %d 回で %.4f USD・やり直しを入れた最大 %d 回で %.4f USD(上限 %.2f)" % (
        PRICE_IN, PRICE_OUT, MAX_TOKENS, len(items) * len(SEATS), est_one, len(items) * len(SEATS) * MAX_ANSWER_ATTEMPTS, est_max, COST_CAP_USD))
    say(u"走らせる前の見積り(最大の回数)が上限を超えるか: %s" % (u"超える(本番は 1 回も呼ばずに止まる)" if est_max > COST_CAP_USD else u"超えない"))
    say(u"元から 【 】 が在る行の内訳: 文に在る行 %d・見出しに在る行 %d" % (wire[B_SENT], wire[B_HEAD]))
    say(u"配線の確認: 行の数 %d・鍵の重なり %d・便 PA の記録の行に無い行 %d・member の欄が空の行 %d・文か見出しに元から 【 か 】 が在る行 %d・見出しが無い行 %d" % (
        wire[u"送る行の数(札つきで同じ state で引けた行)"], wire[u"送る行の鍵の重なり"], wire[u"送る行の(鍵, state)が便 PA の記録の行に在る"][u"無い行"], wire[u"member の欄が空の行"],
        wire[u"文か見出しに元から 【 か 】 が在る行(数えるだけ。字は変えない)"], wire[u"見出しが無い行(%s)" % NO_HEADING]))
    checks = self_test(items, say)
    say(u"--dry-run: 通信していない・鍵は読んでいない・記録は書いていない。")
    return od([(u"items", items), (u"wire", wire), (u"chars", chars), (u"est_usd", est_one), (u"est_max_usd", est_max), (u"self_test", checks)])


def fake_body(text, tin=100, tout=20, stop="end_turn", blocks=("thinking", "text")):
    content = [{"type": b, ("thinking" if b == "thinking" else "text"): (u"…" if b == "thinking" else text)} for b in blocks]
    return json.dumps({"content": content, "usage": {"input_tokens": tin, "output_tokens": tout}, "stop_reason": stop}).encode("utf-8")


def self_test(items, say):
    u"""作り物の transport で、答えの読み方・答えのやり直し・429 の再試行・上限での停止を本番と同じ道(``run_calls``)で通す。通信しない。違えば止める。"""
    sub = items[:2]
    good = u'{"範囲": "一部分", "性質": "計画・予想"}'
    seq = [(200, fake_body(good)), (200, fake_body(good)), (200, fake_body(u"x")), (200, fake_body(good)), (429, b""), (200, fake_body(good))]
    calls = []

    def transport(prompt, model, key):
        calls.append(model)
        return seq[len(calls) - 1]
    tmp = tempfile.mkdtemp(prefix="llm_extract_dry_")
    results = od()
    try:
        w = os.path.join(tmp, "a")
        st = new_state()
        run_calls(sub, st, w, u"fake", transport=transport, sleep=lambda s: None, say=lambda *a: None)
        results[u"答えの読み方(全部読めた)"] = all(seat_answer(st, i, s) == (PART, PLAN) for i in range(2) for s in SEATS)
        results[u"答えのやり直し(読めない 1 回目の後にもう 1 回)"] = len(seat_attempts(st, 1, SEATS[0])) == 2 and len(seat_attempts(st, 0, SEATS[0])) == 1
        results[u"429 の再試行(待ちは作り物)"] = [c[u"retries"] for c in st[u"calls"]][-1] == 1
        results[u"L-S・L-P(member が空と空でない)"] = stops_of((PART, PLAN), True) == (True, True, True) and stops_of((PART, u"実績"), False) == (False, False, False)
        w2 = os.path.join(tmp, "b")
        st2 = new_state()
        n_before = len(calls)
        try:
            run_calls(sub, st2, w2, u"fake", transport=transport, sleep=lambda s: None, say=lambda *a: None, cap=0.0001)
            results[u"上限で止まる"] = False
        except Stop:
            results[u"上限で止まる"] = len(calls) == n_before
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for k, v in results.items():
        say(u"  作り物の transport: %s ― %s" % (k, u"OK" if v else u"違う"))
    if not all(results.values()):
        raise Stop(u"**作り物の transport の検査に違いがある。止める**")
    return results


def check(root=ROOT, procs=1, material=None, cache_base=None, say=print, recs=None, inputs=None, rec=None, **kw):
    u"""0 USD。記録の答えから数を作り直して記録と照らし、材料から指示文を組み直して行ごとの sha256 を照らす。鍵も通信も無い。"""
    if rec is None:
        p = os.path.join(root, RECORD_REL)
        if not os.path.isfile(p):
            raise Stop(u"**在る記録が無い。止める**")
        rec = load_json(p)
    if recs is None:
        inputs = check_inputs(root)
        recs = load_all_records(root)
    labels = SC.build_labels(recs)
    rows, call_rows = rec[u"行"], rec[u"呼び出し"]
    if rec[u"行の欄"] != ROW_COLUMNS or rec[u"呼び出しの欄"] != CALL_COLUMNS:
        raise Stop(u"**記録の行の欄か呼び出しの欄が決めと違う。止める**")
    now = derived_sections(rows, call_rows, labels, recs[u"sc"], recs[u"pa"])
    for k, v in now.items():
        if dumps(rec[k]) != dumps(v):
            raise Stop(u"**記録の欄が行・呼び出しの欄から作り直した数と違う: %s。止める**" % k)
    for i, r in enumerate(rows):                              # 行と呼び出しの欄の対応(席ごとの呼び出しの数・答え)
        for seat, tag, (cr, cn), cc in ((SEATS[0], u"主", (C_MR, C_MN), C_MC), (SEATS[1], u"副", (C_SR, C_SN), C_SC)):
            cs = [c for c in call_rows if c[K_ROW] == i and c[K_SEAT] == tag and not c[K_ABORT]]
            if len(cs) != r[cc] or any(c[K_ATT] != n + 1 for n, c in enumerate(cs)):
                raise Stop(u"**行の呼び出しの数が呼び出しの欄と合わない(行 %d)。止める**" % i)
            if (r[cr] == NO_ANSWER) != (r[cn] == NO_ANSWER) or (r[cr] == NO_ANSWER) != (not any(c[K_OK] for c in cs)):
                raise Stop(u"**行の答えと呼び出しの欄の「答えが読めた」が合わない(行 %d)。止める**" % i)
    for c in call_rows:
        if c[K_USD_U] != round(cost_usd(c[K_TIN], c[K_TOUT]), 6) and c[K_TIN] is not None:
            raise Stop(u"**呼び出しの欄の USD が token と §3 の単価から作り直した額と違う。止める**")
    items, wire, _inputs, _recs, fp, _labels, _mat = collect_items(root=root, procs=procs, material=material, cache_base=cache_base, say=say, recs=recs, inputs=inputs, **kw)
    if [it[u"prompt_sha256"] for it in items] != [r[C_SHA] for r in rows] or \
            [(it[u"batch"], it[u"book"], it[u"side"], it[u"si"], it[u"pos"], it[u"state"], it[u"empty"], it[u"sent_bracket"], it[u"head_bracket"]) for it in items] != \
            [tuple(r[:7]) + (r[C_SB], r[C_HB]) for r in rows]:
        raise Stop(u"**材料から組み直した指示文の sha256・鍵が記録の行と違う。止める**")
    if rec[u"この script の sha256"] != ST.sha256_file(os.path.abspath(__file__)) or rec[K_WIRE] != json.loads(dumps(wire)):
        raise Stop(u"**記録の script の sha256・配線の確認が今と違う。止める**")
    check_text(rec, dumps(rec) + u"\n")
    say(u"--check: 記録の数は行・呼び出しの欄から作り直した数と同じ・指示文の sha256 は材料から組み直した %d 本と同じ" % len(items))
    return now


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true", help="0 USD。指示文を組み、数・見積り・配線の確認を出す。鍵は読まない・通信しない")
    ap.add_argument("--trial", action="store_true", help="有料。頭 5 行 × 2 席に 1 回ずつ(10 回)。形だけ見る")
    ap.add_argument("--resume", action="store_true", help="途中の答え(試しを含む)の続きから")
    ap.add_argument("--check", action="store_true", help="0 USD。記録を作り直して照らす")
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--material", default=None)
    ap.add_argument("--cache-base", default=None)
    ap.add_argument("--procs", type=int, default=1)
    a = ap.parse_args(argv)
    if sum(1 for x in (a.dry_run, a.trial, a.check) if x) > 1:
        raise Stop(u"**--dry-run・--trial・--check は 1 つだけ。止める**")
    if a.dry_run:
        dry_run(root=a.root, procs=a.procs, material=a.material, cache_base=a.cache_base)
    elif a.check:
        check(root=a.root, procs=a.procs, material=a.material, cache_base=a.cache_base)
    else:
        run(root=a.root, procs=a.procs, material=a.material, cache_base=a.cache_base, trial=a.trial, resume=a.resume)


if __name__ == "__main__":
    main()
