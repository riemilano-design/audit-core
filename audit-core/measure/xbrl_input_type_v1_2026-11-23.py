# -*- coding: utf-8 -*-
u"""封 docs/XBRL_INPUT_TYPE_V1_SEAL_2026-11-23.md(XJ0 ― 入力の型(第 1 版)を字で決め、会社の AI に渡す指示書と、型どおりでない file を理由つきで断る受け口の検査を作る)の測定。
**0 USD。LLM の席は呼ばない。鍵は使わない。** engine(``core/``・``adapters/``)は読まない・変えない。
起こす(答えを読む)側は、便 XM0 の script の関数を importlib で呼ぶ(写さない・変えない)。**受け口の検査(``--accept``)は標準の library だけで動く**:
この file の頭の import は標準の library だけで、前の便の script はこの file の中の ``prev()`` が最初に呼ばれた時に初めて読み込む(受け口の検査は ``prev()`` を呼ばない)。

    python3 measure/xbrl_input_type_v1_2026-11-23.py --make <folder> --zip <zip>           # 起こす命令(答えを読む)。<folder> に type/・carry/・outside/ を別々に書く
    python3 -I measure/xbrl_input_type_v1_2026-11-23.py --accept <型の file>               # 受け口の検査。断りの並びを JSON で標準出力に。例外で落ちない
    python3 -I measure/xbrl_input_type_v1_2026-11-23.py --build <folder> <原稿の folder>    # 型から作る命令(受け口が断った file からは作らない)
    python3 measure/xbrl_input_type_v1_2026-11-23.py --break <folder>                      # 壊し方 44 通りと変え方 6 通りを作って受け口に掛け、数を JSON で出す
    python3 measure/xbrl_input_type_v1_2026-11-23.py --dev --tool-p <venv の場所>            # 開発の 5 本だけを全部の工程に通す。記録は書かない
    python3 measure/xbrl_input_type_v1_2026-11-23.py --run --tool-p <venv の場所>            # 本番(67 本。記録を排他で書く。本番は 1 回)
    python3 measure/xbrl_input_type_v1_2026-11-23.py --check                              # 記録の検査(書類ごとの数から集計を導き直す・禁止のもの)。道具は呼ばない
    python3 measure/xbrl_input_type_v1_2026-11-23.py --write-instruction [<path>]          # 指示書を書き出す(既定は docs/INPUT_TYPE_V1_INSTRUCTION_2026-11-23.md)

実装の注(封の字では 1 通りに決まらなかった所の素直な読み。実装より先に決め、結果を見て変えない。報告にも書く):
- 断りの欄: 書類の日・識別子は鍵の名・書類の鍵の数は ``書類``・``独自の名`` の中は ``独自の名``・行の中は鍵の名(鍵の過不足は鍵の名ごとに 1 つ)・名は ``科目`` か ``次元``・行と行の規則は R10 ``行``・R11 ``期間``・R12 ``単位``・R13 ``種類``。
  file の形(JSON・頂・鍵の数・同じ鍵)は ``file``。同じ鍵の断り(S2)は 1 つ。
- 断りの理由は規則の表の「断る時」の ``・`` で分けた 1 つの字(``RULES``)。1 つの規則に 2 つ以上の「断る時」が当たれば、当たった数だけ断りを返す。
- 辞書の名 = 標準ラベルの file の ``xlink:href`` の ``#`` より後ろの字。辞書の在る接頭辞は ``jppfs_cor``・``jpcrp_cor``・``jpigp_cor``。
- 独自の名の並びの昇順 = (種類, 名) の字(コードポイント)の昇順(``member`` < ``科目`` < ``軸``)。
- N2・N5 は名が N1 の形のときだけ見る。N3 は行の中の科目・軸・member だけ(独自の名の要素自身には掛けない)。独自の名の要素には N1・N2・N5 を掛ける。
- 行の欄が形として読めない行(R1〜R7 に当たった行)は R8〜R13 に掛けない。R1 で種類が読めない・行が object でない行は、R2〜R7 も名の規則も掛けない。
- R10〜R13 は R1〜R7 に当たっていない行だけで数える(R10 で断った行も数える)。
- R7: 値が ``無い`` でなければ「値が在る」(値が字でなくても在るとする)。整数 = 型が int(真偽・小数・字は整数でない)。
- R6: ``他:`` の形 = ``他:<分子>`` か ``他:<分子>÷<分母>``(分子・分母は空でなく、空白・``*``・``÷`` を含まない measure の名を字の昇順に ``*`` でつないだ字。``÷`` は 1 つだけ)。4 つの形に当たるもの = 分子が 1 つで ``xbrli:shares``・``xbrli:pure``・``iso4217:XXX``(XXX は英大文字 3 つ)のどれか、か、分子が ``iso4217:XXX`` 1 つで分母が ``xbrli:shares`` 1 つ。
- 起こす側: 期が型に書けない(形が時点でも期間でもない・日が在る日でない・始まりが終わりより後)fact だけ理由 (a) を残す。単位は、第 0 版の 4 つの形(通貨は英大文字 3 つだけ)に当たらないものを ``他:`` の字にし、単位の定義が読めないものだけ (d) を残す。
  (g)(同じ鍵で値・単位・表示の位・精度が違う)は (a)(d) を外した後で数え直す。
- 記録の限界の字(``LIMITS``)は封 §7 の字のとおり。ただし 1 行目の「`.xbrl` を落とした包み」だけ「拡張子 xbrl の file を落とした包み」にした(記録の禁止の字の検査が file の名の形 ``.xbrl`` を断るため)。
- 壊し方の狙った所(規則・行・欄): 上の欄の決めのとおり。壊し方・変え方の「最初」は行の番号の昇順。変え方 Q2 は、変えた行の科目が提出者別の名で、その行が唯一の使い手のとき選ばない(独自の名が使われない名になり型の規則を破るため)。
"""
from __future__ import print_function

import argparse
import collections
import copy
import datetime
import decimal
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT_PATH = os.path.abspath(__file__)
od = collections.OrderedDict

SEAL_REL = "docs/XBRL_INPUT_TYPE_V1_SEAL_2026-11-23.md"
SEAL_COMMIT = "8f3ec76b"
SCRIPT_REL = "measure/xbrl_input_type_v1_2026-11-23.py"
RECORD_REL = "fixtures/xbrl/cd8/input_type_v1_2026-11-23.json"
INSTRUCTION_REL = "docs/INPUT_TYPE_V1_INSTRUCTION_2026-11-23.md"
PREV_NAME = "_xj0_input_type_2026_11_22"
PREV_FILE = "xbrl_input_type_2026-11-22.py"

# ---- 型(封 §1)
TYPE_VERSION = u"1"
TOP_KEYS = (u"型の版", u"書類", u"独自の名", u"行")
DOC_KEYS = (u"提出者の識別子", u"識別子の scheme", u"当期の始まり", u"当期の終わり", u"提出日")
DOC_DATE_KEYS = (u"当期の始まり", u"当期の終わり", u"提出日")
DOC_ID_KEYS = (u"提出者の識別子", u"識別子の scheme")
NAME_KEYS = (u"種類", u"名")
NAME_KINDS = (u"科目", u"軸", u"member")
NUM_KEYS = (u"種類", u"科目", u"期間", u"対象", u"次元", u"値", u"単位", u"表示の位", u"精度")
TEXT_KEYS = (u"種類", u"科目", u"期間", u"対象", u"次元")
KIND_NUM, KIND_TEXT = u"数", u"文"
TARGET_IND, TARGET_DEF = u"個別", u"既定"
VALUE_NONE = u"無い"
UNIT_SHARES, UNIT_PURE = u"株", u"純数"
UNIT_OTHER = u"他:"
UNIT_PER = u"÷"
AXIS_CONS = "jppfs_cor:ConsolidatedOrNonConsolidatedAxis"
MEMBER_IND = "jppfs_cor:NonConsolidatedMember"
FORMAT_OK = "ixt:numdotdecimal"
MAX_EXP = 1000
DICT_PREFIXES = ("jppfs_cor", "jpcrp_cor", "jpigp_cor")
DICT_SUBDIR = (".cache", "audit-core", "edinet-taxonomy", "2025-11-01")
LAB_FILES = od([("jppfs_2025-11-01_lab.xml", "bf56ea1585afe426b398a9053ec4de4dbeafc211a53675b5d6d19453e4e04bf4"),
                ("jpcrp_2025-11-01_lab.xml", "df9c23764ec9a63cb65b5ef62e79a2907c590523797421442ea2a60e334cd684"),
                ("jpigp_2025-11-01_lab.xml", "d45c95cc634202973557f5ed935d747ba25e751b7386c5269fe3e7bdb2c82d09")])
HREF_RE = re.compile(r'xlink:href="[^"#]*#([A-Za-z0-9_\-]+)"')
NAME_RE = re.compile(r"[A-Za-z0-9_\-]+:[A-Za-z0-9_\-]+", re.ASCII)
DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", re.ASCII)
VALUE_RE = re.compile(r"-?(0|[1-9][0-9]*)(\.[0-9]*[1-9])?", re.ASCII)
UNIT_FORM_RE = re.compile(u"通貨:[A-Z]{3}(÷株)?", re.ASCII)
CUR_MEASURE_RE = re.compile(r"iso4217:[A-Z]{3}", re.ASCII)
REASONS = ("a", "b", "c", "d", "e", "f", "g", "h")
STAGES = (u"起こす", u"受け口", u"型から作る", u"組む", u"道具")
EXIT_USAGE, EXIT_DECLINE, EXIT_ERROR, EXIT_DICT = 64, 2, 1, 3
DECLINE_PREFIX = "DECLINE: "
REASON_MAX = 80
TIMEOUT_SEC = 600
DEV_COUNT = 5
DOCS_WANT = 67
YEAR = None                                            # 規則の年は便 XM0 の字(P.YEAR)。記録を組む時に読む
CARRY_FMT = "c%04d.json"
BREAK_RESULT_KEYS = (u"作れた", u"断った", u"ちょうど 1 つ", u"別の規則で断った", u"断らなかった")

RULES = (
    ('S1', 'file', (
        'JSON として読めない',
        '頂が object でない',
        '頂の鍵が 4 つちょうどでない',
        '`型の版` が字 `1` でない',
        '`行` が 1 つ以上の並びでない',
        '`独自の名` が並びでない',
        '`書類` が object でない')),
    ('S2', 'file', (
        'どこかの object に同じ鍵が 2 回在る',)),
    ('D1', '`書類`', (
        '鍵が 5 つちょうどでない',
        '日が `YYYY-MM-DD` の形の在る日でない')),
    ('D2', '`書類`', (
        '`当期の始まり` が `当期の終わり` より後',)),
    ('D3', '`書類`', (
        '`提出日` が `当期の終わり` より前',)),
    ('D4', '`書類`', (
        '`提出者の識別子` か `識別子の scheme` が、空白を含まない 1 字以上の字でない',)),
    ('N1', '名(科目・軸・member・`独自の名`)', (
        '`<接頭辞>:<局所名>` の形(どちらも英数字と `_` と `-` だけ・1 字以上・`:` は 1 つ)でない',)),
    ('N2', '名', (
        '接頭辞が辞書の在る接頭辞なのに、辞書に無い',)),
    ('N3', '名', (
        '接頭辞が `_cor` で終わらないのに、その種類で `独自の名` に無い',)),
    ('N4', '`独自の名`', (
        '要素の鍵が 2 つちょうどでない',
        '種類が 3 つのどれでもない',
        '接頭辞が `_cor` で終わる名',
        'どの行もその種類で使わない名',
        '同じ (種類, 名) が 2 回',
        '並びが昇順でない')),
    ('N5', '名', (
        '軸の名が `Axis` で終わらない',
        'member の名が `Member` で終わらない')),
    ('R1', '行', (
        '行が object でない',
        '`種類` が `数` でも `文` でもない',
        '鍵がその種類の鍵ちょうどでない')),
    ('R2', '`期間`', (
        '鍵が `時点` だけ・`始まり` と `終わり` だけ、のどちらでもない',
        '日が在る日の形でない',
        '`始まり` が `終わり` より後')),
    ('R3', '`対象`', (
        '`個別` でも `既定` でもない',)),
    ('R4', '`次元`', (
        '並びでない',
        '要素が 2 つの字の並びでない',
        '同じ軸が 2 回',
        '軸の名の昇順でない',
        '個別の軸(`jppfs_cor:ConsolidatedOrNonConsolidatedAxis`)が在る')),
    ('R5', '`値`', (
        '字でない',
        '`無い` でも `-?(0|[1-9][0-9]*)(\\.[0-9]*[1-9])?` の形(半角。全体が合う)でもない')),
    ('R6', '`単位`', (
        '字でない',
        '上の形のどれでもない',
        '4 つの形に当たるのに `他:` で書いている')),
    ('R7', '`表示の位`・`精度`', (
        '値が在るのに整数でない(真偽・小数・字は整数でない)',
        '大きさが 1000 を超える',
        '値が `無い` なのに `null` でない')),
    ('R8', '`表示の位`・`精度`', (
        '精度 + 表示の位 が 0 より小さい',)),
    ('R9', '`値`・`精度`', (
        '値が 10 の(−精度)乗の倍数でない',)),
    ('R10', '行と行', (
        '(種類・科目・期間・対象・次元)の組が同じ行が 2 つ以上在る(後ろの行を断る)',)),
    ('R11', '行と行', (
        '1 つの科目が、時点の行と期間の行の両方に在る(その科目の、数の少ない側の行を断る。同じ数なら期間の側)',)),
    ('R12', '行と行', (
        '1 つの科目の数の行に、単位が 2 通り以上在る(その科目の、いちばん多い単位でない行を断る。同じ数なら字の昇順で先の単位を残す)',)),
    ('R13', '行と行', (
        '1 つの科目が、数の行と文の行の両方に在る(その科目の、数の少ない側の行を断る。同じ数なら文の側)',)),
)
BREAK_TEXT = collections.OrderedDict([
    ('S1a', '`型の版` を字 `0` にする'),
    ('S1b', '頂に鍵 `備考` を足す'),
    ('S2a', 'file の字の頭の `{` の直後に、`"型の版": "1",` をもう 1 回書く'),
    ('D1a', '`当期の終わり` の月を `13` にする'),
    ('D1b', '`書類` に鍵 `備考` を足す'),
    ('D2a', '`当期の始まり` を `当期の終わり` の次の日にする'),
    ('D3a', '`提出日` を `当期の終わり` の前の日にする'),
    ('D4a', '`提出者の識別子` を空の字にする'),
    ('N1a', '最初の行の `科目` の `:` を取る'),
    ('N2a', '科目が辞書の在る接頭辞の最初の行の `科目` の後ろに `Zz` を足す(足した名が辞書に在れば、無くなるまで `Zz` を足す)'),
    ('N3a', '科目が提出者別の名の最初の行について、`独自の名` からその (科目, 名) を取る'),
    ('N4a', '`独自の名` に、どの行も使わない (科目, `zz_unused:Zz`) を昇順の位置に足す'),
    ('N4b', '`独自の名` が 2 つ以上在る時、頭の 2 つを入れ替える'),
    ('N5a', '次元が 1 つ以上在る最初の行の、最初の軸の名の後ろに `X` を足す'),
    ('N5b', '同じ行の、最初の member の名の後ろに `X` を足す'),
    ('R1a', '最初の行から鍵 `対象` を取る'),
    ('R1b', '最初の行に鍵 `備考` を足す'),
    ('R1c', '最初の `文` の行に鍵 `値`(`無い`)を足す'),
    ('R2a', '最初の時点の行の `期間` に鍵 `始まり`(同じ日)を足す'),
    ('R2b', '始まりと終わりが違う最初の期間の行の、始まりと終わりを入れ替える'),
    ('R2c', '最初の時点の行の日の `-` を `/` にする'),
    ('R3a', '最初の行の `対象` を `連結` にする'),
    ('R4a', '次元が 2 つ以上在る最初の行の、次元の並びを逆にする'),
    ('R4b', '次元が 1 つ以上在る最初の行の、最初の組をもう 1 回足す'),
    ('R4c', '最初の行の `次元` の頭に [個別の軸, 個別の member] を足す'),
    ('R5a', '値の整数の部が 4 桁以上の最初の行の値に、3 桁ごとの `,` を入れる'),
    ('R5b', '値の在る最初の行の値を、字でなく JSON の数にする'),
    ('R5c', '値が `-` で始まらない、値の在る最初の行の値の頭に `+` を足す'),
    ('R5d', '値に小数点の無い、値の在る最初の行の値の後ろに `.0` を足す'),
    ('R5e', '値の在る最初の行の値の数字を全角にする'),
    ('R6a', '単位が `通貨:JPY` の最初の行の単位を `円` にする'),
    ('R6b', '単位が `通貨:` で始まる最初の行の単位の英字を小文字にする'),
    ('R6c', '単位が `純数` の最初の行の単位を `他:xbrli:pure` にする'),
    ('R7a', '値の在る最初の行の `精度` を、同じ数字の字にする'),
    ('R7b', '値が `無い` の最初の行の `精度` を 0 にする'),
    ('R7c', '値の在る最初の行の `表示の位` を `null` にする'),
    ('R7d', '値の在る最初の行の `精度` を `true` にする'),
    ('R8a', '値が `0` の最初の行の `精度` を、−(表示の位)− 1 にする'),
    ('R9a', '値の在る最初の行(値が `0`・`-0` でない)の値に、10 の(−精度 − 1)乗を足す(符号はそのまま・大きさに足す)'),
    ('R10a', '最初の行の写しを、行の並びの最後に足す'),
    ('R10b', '値の在る最初の行の写しの値だけを変えて(R9 を破らない最小の幅で 1 つ足す)最後に足す'),
    ('R11a', '時点の行が 2 つ以上在る最初の科目の、後ろの 1 行を期間(`始まり` = `当期の始まり`・`終わり` = その日。始まりが終わりより後になるなら `始まり` = その日)にする'),
    ('R12a', '数の行が 2 つ以上在る最初の科目の、後ろの 1 行の単位を、`純数` なら `株` に・ほかなら `純数` にする'),
    ('R13a', '数の行が 2 つ以上在る最初の科目の、後ろの 1 行を `文` にする(6.〜9. の鍵を取る)'),
])
CHANGE_TEXT = collections.OrderedDict([
    ('Q1', '数の行(次元が空・値が在る)の `対象` を逆にする(逆にした鍵の行が無い最初の行)'),
    ('Q2', '数の行(値が在る)の `科目` を、同じ file の別の科目(数・同じ時点か期間か・同じ単位。変えた鍵の行が無い)にする。別の科目は行の番号の昇順で最初に当てはまるもの'),
    ('Q3', '値の在る最初の行の値の大きさに、10 の(−精度)乗を 1 つ足す'),
    ('Q4', '値が `0`・`-0` でない最初の行の値の符号を逆にする'),
    ('Q5', '数の行(値が在る)の `期間` の日を全部 1 年前の同じ月日にする(変えた鍵の行が無い最初の行。2 月 29 日の行は選ばない)'),
    ('Q6', '数の行が 1 つだけの科目の、単位が `通貨:JPY` の最初の行の単位を `通貨:USD` にする'),
])
LIMITS = [
    '便 XM0 の限界の全部(67 本は無作為でない・有報だけ・62 本は未使用でない・道具 P は本家の版でない・拡張子 xbrl の file を落とした包み・持ち込みは作っていない・型は答えから起こした・文の fact の中身は持ち込み・対象の `既定` は連結とは限らない)。',
    'AI は呼んでいない。指示書が AI に伝わるか・AI がそのとおりに書くかは測っていない。',
    '壊し方は 1 か所ずつ・最初の当てはまる所だけ・この封の表に在る 44 通りだけ。2 か所以上を同時に壊した file・表に無い壊れ方は測っていない。規則と壊し方は同じ席が書いた。',
    '受け口の規則の一部は開発の 5 本を見て置いた。型の広げ方(期間・単位)は実物を見ずに決めた。',
    '標準の辞書は 3 つの接頭辞だけ。ほかの `_cor` の接頭辞の名は形しか見ていない。',
]

#: 封 §4 の予測の境(記録には判定を書かない。封の門が封の表と照らす)。(下限, 上限, 上限を含むか)。下限は常に「以上」。None = 無い。
BOUNDS = od([
    ("XJ0-1", (52, None, False)), ("XJ0-2", (None, 3, True)), ("XJ0-3", (None, u"0.2%", True)), ("XJ0-4", (None, 5, True)), ("XJ0-5", (u"受理した書類の全部", None, False)),
    ("XJ0-6", (u"作れた file の全部", None, False)), ("XJ0-7", (u"85%", None, False)), ("XJ0-8", (u"95%", None, False)), ("XJ0-9", (u"4%", u"8%", False)), ("XJ0-10", (None, 3, True))])

RULE_ORDER = tuple(r[0] for r in RULES)
RULE_CONDS = od((r[0], r[2]) for r in RULES)
RULE_PLACE = od((r[0], r[1]) for r in RULES)
BREAK_IDS = tuple(BREAK_TEXT)
CHANGE_IDS = tuple(CHANGE_TEXT)


# ======================================================================================================
# 受け口の検査(標準の library だけ。前の便の script・元の包み・持ち込み・型の外を読まない)
class DictError(Exception):
    u"""標準の辞書の file が読めない・sha256 が合わない。"""


def default_dictionary_dir():
    return os.path.join(os.path.expanduser("~"), *DICT_SUBDIR)


def load_dictionary(directory, shas=None):
    u"""標準ラベルの file 3 つを sha256 を確かめて読み、辞書の名(``<接頭辞>_<局所名>``)の集まりを返す。合わなければ ``DictError``。"""
    shas = LAB_FILES if shas is None else shas
    names = set()
    for fn, want in shas.items():
        try:
            with open(os.path.join(directory, fn), "rb") as fh:
                data = fh.read()
        except OSError:
            raise DictError(u"標準ラベルの file が読めない")
        if hashlib.sha256(data).hexdigest() != want:
            raise DictError(u"標準ラベルの file の sha256 が合わない")
        names.update(HREF_RE.findall(data.decode("utf-8")))
    return frozenset(names)


def load_names_file(path):
    u"""辞書の名の集まりの file(JSON の字の並び)を読む。作り物の辞書を渡す入口(門・下見用)。"""
    with open(path, "rb") as fh:
        data = json.loads(fh.read().decode("utf-8"))
    if not isinstance(data, list) or not all(isinstance(x, str) for x in data):
        raise DictError(u"辞書の名の file の形が違う")
    return frozenset(data)


def parse_date(s):
    u"""``YYYY-MM-DD`` の字 → date。形が違う・無い日なら ``None``。"""
    if not isinstance(s, str) or not DATE_RE.fullmatch(s):
        return None
    try:
        return datetime.date(int(s[0:4]), int(s[5:7]), int(s[8:10]))
    except ValueError:
        return None


def refusal(rule, idx, row, field):
    u"""断り 1 つ。``idx`` は規則の表の「断る時」の何番目か(0 から)。"""
    return od([(u"行", row), (u"欄", field), (u"規則", rule), (u"理由", RULE_CONDS[rule][idx])])


def parse_json(text):
    u"""JSON の字 → (object, 同じ鍵が在ったか)。読めなければ ``ValueError``・深すぎれば ``RecursionError``。NaN・Infinity は読めないとする。"""
    dups = []

    def hook(pairs):
        d = {}
        for k, v in pairs:
            if k in d:
                dups.append(k)
            d[k] = v
        return d

    def bad_constant(s):
        raise ValueError(s)
    obj = json.loads(text, object_pairs_hook=hook, parse_constant=bad_constant)
    return obj, bool(dups)


def good_id(s):
    return isinstance(s, str) and len(s) >= 1 and not re.search(r"\s", s)


def split_name(name):
    u"""N1 の形の名 → (接頭辞, 局所名)。形が違えば ``None``。"""
    if isinstance(name, str) and NAME_RE.fullmatch(name):
        return tuple(name.split(":"))
    return None


def check_name(name, kind, row, field, names, custom, out, own=False):
    u"""名 1 つに N1〜N5 を掛ける。``own`` = 独自の名の要素自身(N3 を掛けない)。"""
    sp = split_name(name)
    if sp is None:
        out.append(refusal("N1", 0, row, field))
        return
    prefix, local = sp
    if prefix in DICT_PREFIXES:
        if prefix + "_" + local not in names:
            out.append(refusal("N2", 0, row, field))
    elif not prefix.endswith("_cor") and not own and (kind, name) not in custom:
        out.append(refusal("N3", 0, row, field))
    if kind == u"軸" and not name.endswith("Axis"):
        out.append(refusal("N5", 0, row, field))
    if kind == u"member" and not name.endswith("Member"):
        out.append(refusal("N5", 1, row, field))


def check_unit(u):
    u"""単位の字 → 0(形のとおり)・1(上の形のどれでもない)・2(4 つの形に当たるのに ``他:`` で書いている)。"""
    if u in (UNIT_SHARES, UNIT_PURE) or UNIT_FORM_RE.fullmatch(u):
        return 0
    if not u.startswith(UNIT_OTHER):
        return 1
    parts = u[len(UNIT_OTHER):].split(UNIT_PER)
    if len(parts) > 2:
        return 1
    groups = []
    for p in parts:
        ms = p.split("*")
        if not p or any((m == "" or re.search(r"\s", m)) for m in ms) or ms != sorted(ms):
            return 1
        groups.append(ms)
    if len(groups) == 1:
        m = groups[0]
        if len(m) == 1 and (m[0] in ("xbrli:shares", "xbrli:pure") or CUR_MEASURE_RE.fullmatch(m[0])):
            return 2
    elif len(groups[0]) == 1 and len(groups[1]) == 1 and CUR_MEASURE_RE.fullmatch(groups[0][0]) and groups[1][0] == "xbrli:shares":
        return 2
    return 0


def period_key(p):
    u"""R2 に通った期間 → 比べる鍵。"""
    return tuple(sorted(p.items()))


def multiple_of_precision(value, prec):
    u"""値(R5 の形の字)が 10 の(−精度)乗の倍数か。字だけで見る(巨大な桁でも整数への変換をしない)。"""
    body = value[1:] if value.startswith("-") else value
    ip, _dot, fp = body.partition(".")
    digits = (ip + fp).lstrip("0")
    k = len(fp) - prec
    if digits == "" or k <= 0:
        return True
    return len(digits) - len(digits.rstrip("0")) >= k


def check_row(i, r, names, custom, out):
    u"""行 1 つに R1〜R9 と名の規則を掛ける。R1〜R7 のどれかに当たれば True(R8〜R13 に掛けない)。"""
    if not isinstance(r, dict):
        out.append(refusal("R1", 0, i, u"行"))
        return True
    kind = r.get(u"種類")
    if kind != KIND_NUM and kind != KIND_TEXT:
        out.append(refusal("R1", 1, i, u"種類"))
        return True
    hit = False
    want = NUM_KEYS if kind == KIND_NUM else TEXT_KEYS
    for k in sorted(set(want) ^ set(r), key=lambda x: (x not in want, x)):
        out.append(refusal("R1", 2, i, k))
        hit = True
    if u"科目" in r:
        check_name(r[u"科目"], u"科目", i, u"科目", names, custom, out)
    if u"期間" in r:
        p = r[u"期間"]
        ds = None
        if isinstance(p, dict) and set(p) == {u"時点"}:
            ds = [p[u"時点"]]
        elif isinstance(p, dict) and set(p) == {u"始まり", u"終わり"}:
            ds = [p[u"始まり"], p[u"終わり"]]
        if ds is None:
            out.append(refusal("R2", 0, i, u"期間"))
            hit = True
        else:
            dd = [parse_date(x) for x in ds]
            if any(x is None for x in dd):
                out.append(refusal("R2", 1, i, u"期間"))
                hit = True
            elif len(dd) == 2 and dd[0] > dd[1]:
                out.append(refusal("R2", 2, i, u"期間"))
                hit = True
    if u"対象" in r and r[u"対象"] != TARGET_IND and r[u"対象"] != TARGET_DEF:
        out.append(refusal("R3", 0, i, u"対象"))
        hit = True
    if u"次元" in r:
        d = r[u"次元"]
        if not isinstance(d, list):
            out.append(refusal("R4", 0, i, u"次元"))
            hit = True
        else:
            axes = []
            for e in d:
                if isinstance(e, list) and len(e) == 2 and isinstance(e[0], str) and isinstance(e[1], str):
                    axes.append(e[0])
                    check_name(e[0], u"軸", i, u"次元", names, custom, out)
                    check_name(e[1], u"member", i, u"次元", names, custom, out)
                else:
                    out.append(refusal("R4", 1, i, u"次元"))
                    hit = True
            seen = set()
            for a in axes:
                if a in seen:
                    out.append(refusal("R4", 2, i, u"次元"))
                    hit = True
                seen.add(a)
            if any(axes[j] > axes[j + 1] for j in range(len(axes) - 1)):
                out.append(refusal("R4", 3, i, u"次元"))
                hit = True
            if AXIS_CONS in axes:
                out.append(refusal("R4", 4, i, u"次元"))
                hit = True
    if kind == KIND_NUM:
        v = r.get(u"値")
        if u"値" in r:
            if not isinstance(v, str):
                out.append(refusal("R5", 0, i, u"値"))
                hit = True
            elif v != VALUE_NONE and not VALUE_RE.fullmatch(v):
                out.append(refusal("R5", 1, i, u"値"))
                hit = True
        if u"単位" in r:
            u = r[u"単位"]
            if not isinstance(u, str):
                out.append(refusal("R6", 0, i, u"単位"))
                hit = True
            else:
                c = check_unit(u)
                if c:
                    out.append(refusal("R6", c, i, u"単位"))
                    hit = True
        if u"値" in r and u"表示の位" in r and u"精度" in r:
            has_value = v != VALUE_NONE
            for f in (u"表示の位", u"精度"):
                x = r[f]
                if has_value:
                    if type(x) is not int:
                        out.append(refusal("R7", 0, i, f))
                        hit = True
                    elif abs(x) > MAX_EXP:
                        out.append(refusal("R7", 1, i, f))
                        hit = True
                elif x is not None:
                    out.append(refusal("R7", 2, i, f))
                    hit = True
            if not hit and has_value:
                if r[u"表示の位"] + r[u"精度"] < 0:
                    out.append(refusal("R8", 0, i, u"精度"))
                if not multiple_of_precision(v, r[u"精度"]):
                    out.append(refusal("R9", 0, i, u"値"))
    return hit


def check_custom(entries, used, names, out):
    u"""独自の名の並びに N1・N2・N4・N5 を掛ける。(種類, 名) の集まり(N3 に使う)を返す。"""
    custom = set()
    for e in entries:
        if isinstance(e, dict) and set(e) == set(NAME_KEYS) and e[u"種類"] in NAME_KINDS and isinstance(e[u"名"], str):
            custom.add((e[u"種類"], e[u"名"]))
    last = None
    seen = set()
    for e in entries:
        f = u"独自の名"
        if not isinstance(e, dict) or set(e) != set(NAME_KEYS):
            out.append(refusal("N4", 0, None, f))
            continue
        kind, name = e[u"種類"], e[u"名"]
        if kind not in NAME_KINDS:
            out.append(refusal("N4", 1, None, f))
            continue
        check_name(name, kind, None, f, names, custom, out, own=True)
        sp = split_name(name)
        if sp is not None:
            if sp[0].endswith("_cor"):
                out.append(refusal("N4", 2, None, f))
            elif (kind, name) not in used:
                out.append(refusal("N4", 3, None, f))
        if isinstance(name, str):
            if (kind, name) in seen:
                out.append(refusal("N4", 4, None, f))
            elif last is not None and (kind, name) < last:
                out.append(refusal("N4", 5, None, f))
            seen.add((kind, name))
            last = (kind, name)
    return custom


def used_names(rows):
    u"""行の中で使われている (種類, 名) の集まり(形が読めない行・欄は数えない)。"""
    used = set()
    for r in rows:
        if not isinstance(r, dict):
            continue
        if isinstance(r.get(u"科目"), str):
            used.add((u"科目", r[u"科目"]))
        d = r.get(u"次元")
        if isinstance(d, list):
            for e in d:
                if isinstance(e, list) and len(e) == 2 and isinstance(e[0], str) and isinstance(e[1], str):
                    used.add((u"軸", e[0]))
                    used.add((u"member", e[1]))
    return used


def check_doc(doc, out):
    keys = set(doc)
    if keys != set(DOC_KEYS):
        out.append(refusal("D1", 0, None, u"書類"))
    dates = {}
    for k in DOC_DATE_KEYS:
        if k in doc:
            d = parse_date(doc[k])
            if d is None:
                out.append(refusal("D1", 1, None, k))
            else:
                dates[k] = d
    if u"当期の始まり" in dates and u"当期の終わり" in dates and dates[u"当期の始まり"] > dates[u"当期の終わり"]:
        out.append(refusal("D2", 0, None, u"当期の始まり"))
    if u"提出日" in dates and u"当期の終わり" in dates and dates[u"提出日"] < dates[u"当期の終わり"]:
        out.append(refusal("D3", 0, None, u"提出日"))
    for k in DOC_ID_KEYS:
        if k in doc and not good_id(doc[k]):
            out.append(refusal("D4", 0, None, k))


def check_pairs(clean, out):
    u"""R10〜R13(R1〜R7 に当たっていない行 ``clean`` = [(行の番号, 行)] だけで数える)。"""
    seen = {}
    for i, r in clean:
        key = (r[u"種類"], r[u"科目"], period_key(r[u"期間"]), r[u"対象"], tuple(tuple(x) for x in r[u"次元"]))
        if key in seen:
            out.append(refusal("R10", 0, i, u"行"))
        else:
            seen[key] = i
    by = od()
    for i, r in clean:
        by.setdefault(r[u"科目"], []).append((i, r))
    for name, rs in by.items():
        inst = [i for i, r in rs if u"時点" in r[u"期間"]]
        dur = [i for i, r in rs if u"時点" not in r[u"期間"]]
        if inst and dur:
            for i in (inst if len(inst) < len(dur) else dur):
                out.append(refusal("R11", 0, i, u"期間"))
        nums = [(i, r) for i, r in rs if r[u"種類"] == KIND_NUM]
        texts = [i for i, r in rs if r[u"種類"] == KIND_TEXT]
        units = collections.Counter(r[u"単位"] for _i, r in nums)
        if len(units) > 1:
            keep = sorted(units, key=lambda u: (-units[u], u))[0]
            for i, r in nums:
                if r[u"単位"] != keep:
                    out.append(refusal("R12", 0, i, u"単位"))
        if nums and texts:
            for i in ([i for i, _r in nums] if len(nums) < len(texts) else texts):
                out.append(refusal("R13", 0, i, u"種類"))


def check_text(text, names):
    u"""型の file の字 → 断りの並び(空なら受理)。**例外を投げない作りにする**(門が壊れた入力で確かめる)。``names`` = 辞書の名の集まり。"""
    try:
        obj, dup = parse_json(text)
    except (ValueError, RecursionError):
        return [refusal("S1", 0, None, u"file")]
    out = []
    if not isinstance(obj, dict):
        return [refusal("S1", 1, None, u"file")]
    if set(obj) != set(TOP_KEYS):
        out.append(refusal("S1", 2, None, u"file"))
    if not (isinstance(obj.get(u"型の版"), str) and obj[u"型の版"] == TYPE_VERSION):
        out.append(refusal("S1", 3, None, u"型の版"))
    rows = obj.get(u"行")
    if not (isinstance(rows, list) and len(rows) >= 1):
        out.append(refusal("S1", 4, None, u"行"))
    entries = obj.get(u"独自の名")
    if not isinstance(entries, list):
        out.append(refusal("S1", 5, None, u"独自の名"))
    doc = obj.get(u"書類")
    if not isinstance(doc, dict):
        out.append(refusal("S1", 6, None, u"書類"))
    if dup:
        out.append(refusal("S2", 0, None, u"file"))
    if out:
        return sort_refusals(out)
    check_doc(doc, out)
    custom = check_custom(entries, used_names(rows), names, out)
    clean = []
    for i, r in enumerate(rows, 1):
        if not check_row(i, r, names, custom, out) and isinstance(r.get(u"科目"), str):
            clean.append((i, r))
    check_pairs(clean, out)
    return sort_refusals(out)


def sort_refusals(out):
    return sorted(out, key=lambda x: (RULE_ORDER.index(x[u"規則"]), x[u"行"] if x[u"行"] is not None else 0, x[u"欄"], x[u"理由"]))


def check_bytes(data, names):
    u"""型の file のバイト列 → 断りの並び。UTF-8 でなければ S1。"""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return [refusal("S1", 0, None, u"file")]
    return check_text(text, names)


def check_safe(data, names):
    u"""``check_bytes`` に、予期しない例外が出ても落ちない守りを掛ける(入口用。門は守りの無い ``check_bytes`` が例外を出さないことを別に確かめる)。"""
    try:
        return check_bytes(data, names)
    except Exception:                                      # noqa: BLE001
        return [refusal("S1", 0, None, u"file")]


def result_of(refusals):
    return od([(u"受理", not refusals), (u"断り", refusals)])


def emit_json_text(text):
    u"""受け口の出力を標準出力へ書く。入力由来の字(鍵・file の名)に UTF-8 へ直せない字(孤立 surrogate など)が在っても落ちず、その字を ``\\uXXXX`` の形へ逃がす。普通の字は 1 byte も変わらない。"""
    safe = text.encode("utf-8", "backslashreplace")
    buf = getattr(sys.stdout, "buffer", None)
    if buf is not None:
        sys.stdout.flush()
        buf.write(safe)
        buf.flush()
    else:
        sys.stdout.write(safe.decode("utf-8"))


def accept_main(argv):
    u"""受け口の検査の入口。``--accept <file>``・``--accept-dir <folder>``(folder の中の file ごと)・``--names-file <辞書の名の JSON>``(作り物の辞書。既定は標準ラベルの file を sha256 を確かめて読む)。
    終わりの値: 0・64(使い方)・3(辞書が読めない)。断りは標準出力の JSON(終わりの値は 0)。"""
    args = list(argv)
    names_file = None
    if "--names-file" in args:
        i = args.index("--names-file")
        if i + 1 >= len(args):
            print(u"使い方: --accept <型の file> [--names-file <辞書の名の JSON>]", file=sys.stderr)
            return EXIT_USAGE
        names_file = args[i + 1]
        del args[i:i + 2]
    if len(args) != 2 or args[0] not in ("--accept", "--accept-dir"):
        print(u"使い方: --accept <型の file> [--names-file <辞書の名の JSON>]", file=sys.stderr)
        return EXIT_USAGE
    try:
        names = load_names_file(names_file) if names_file else load_dictionary(default_dictionary_dir())
    except (DictError, OSError, ValueError):
        print(DECLINE_PREFIX + u"標準の辞書が読めない", file=sys.stderr)
        return EXIT_DICT
    path = args[1]
    try:
        if args[0] == "--accept":
            with open(path, "rb") as fh:
                data = fh.read()
            res = result_of(check_safe(data, names))
        else:
            res = od()
            for fn in sorted(os.listdir(path)):
                with open(os.path.join(path, fn), "rb") as fh:
                    res[fn] = result_of(check_safe(fh.read(), names))
    except OSError:
        print(u"使い方: 読める型の file(か folder)を渡す", file=sys.stderr)
        return EXIT_USAGE
    if args[0] == "--accept":
        emit_json_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n")                       # 1 つの file の結果(入力由来の字は鍵の字)
    else:
        emit_json_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n")                       # folder の結果(入力由来の字は file の名と鍵の字)
    return 0


# ======================================================================================================
# 断りの型(壊し方・変え方。受理された型の file から 1 か所だけ変えた file を作る)
DEC_CTX = decimal.Context(prec=20000, Emax=999999, Emin=-999999)


class Refuse(Exception):
    u"""この script の断り(別の process の命令の断り・起こす側の断り)。``reason`` は固定の字(材料の字を入れない)。"""

    def __init__(self, reason):
        Exception.__init__(self, reason)
        self.reason = reason


def dump_text(obj):
    u"""型の file の書き方(UTF-8。字は escape しない。1 字下げ)。"""
    return json.dumps(obj, ensure_ascii=False, indent=1) + "\n"


def loads_ordered(text):
    return json.loads(text, object_pairs_hook=od)


def is_num(r):
    return r[u"種類"] == KIND_NUM


def has_value(r):
    return is_num(r) and r[u"値"] != VALUE_NONE


def first_row(rows, pred):
    u"""(行の番号(1 から), 行)。無ければ ``None``。"""
    for i, r in enumerate(rows, 1):
        if pred(r):
            return i, r
    return None


def fmt_dec(d):
    return format(DEC_CTX.normalize(d), "f")


def add_step(value, exp):
    u"""値の字の大きさに 10 の ``exp`` 乗を足す(符号はそのまま)。"""
    sign = u"-" if value.startswith(u"-") else u""
    mag = DEC_CTX.create_decimal(value[1:] if sign else value)
    return sign + fmt_dec(DEC_CTX.add(mag, DEC_CTX.scaleb(decimal.Decimal(1), exp)))


def shift_day(s, days):
    d = parse_date(s)
    try:
        return (d + datetime.timedelta(days=days)).isoformat() if d is not None else None
    except OverflowError:
        return None


def row_key(r):
    p = r[u"期間"]
    return (r[u"種類"], r[u"科目"], tuple(sorted(p.items())), r[u"対象"], tuple(tuple(x) for x in r[u"次元"]))


def with_commas(value):
    sign = u"-" if value.startswith(u"-") else u""
    body = value[1:] if sign else value
    ip, dot, fp = body.partition(".")
    return sign + format(int(ip), ",") + dot + fp


_BREAK_FUNCS = {}
_CHANGE_FUNCS = {}


def break_of(bid):
    def deco(fn):
        _BREAK_FUNCS[bid] = fn
        return fn
    return deco


def change_of(qid):
    def deco(fn):
        _CHANGE_FUNCS[qid] = fn
        return fn
    return deco


# 壊し方の関数の約束: ``f(obj, text, names)`` は ``((規則, 行, 欄), 新しい obj か字)`` か、当てはまる所が無ければ ``None``。``obj`` は呼ぶ側が写しを渡す。
@break_of("S1a")
def brk_s1a(o, t, names):
    o[u"型の版"] = u"0"
    return ("S1", None, u"型の版"), o


@break_of("S1b")
def brk_s1b(o, t, names):
    o[u"備考"] = u"x"
    return ("S1", None, u"file"), o


@break_of("S2a")
def brk_s2a(o, t, names):
    i = t.index("{")
    return ("S2", None, u"file"), t[:i + 1] + u'"型の版": "1",' + t[i + 1:]


@break_of("D1a")
def brk_d1a(o, t, names):
    s = o[u"書類"][u"当期の終わり"]
    o[u"書類"][u"当期の終わり"] = s[:5] + u"13" + s[7:]
    return ("D1", None, u"当期の終わり"), o


@break_of("D1b")
def brk_d1b(o, t, names):
    o[u"書類"][u"備考"] = u"x"
    return ("D1", None, u"書類"), o


@break_of("D2a")
def brk_d2a(o, t, names):
    s = shift_day(o[u"書類"][u"当期の終わり"], 1)
    if s is None:
        return None
    o[u"書類"][u"当期の始まり"] = s
    return ("D2", None, u"当期の始まり"), o


@break_of("D3a")
def brk_d3a(o, t, names):
    s = shift_day(o[u"書類"][u"当期の終わり"], -1)
    if s is None:
        return None
    o[u"書類"][u"提出日"] = s
    return ("D3", None, u"提出日"), o


@break_of("D4a")
def brk_d4a(o, t, names):
    o[u"書類"][u"提出者の識別子"] = u""
    return ("D4", None, u"提出者の識別子"), o


@break_of("N1a")
def brk_n1a(o, t, names):
    r = o[u"行"][0]
    r[u"科目"] = r[u"科目"].replace(u":", u"", 1)
    return ("N1", 1, u"科目"), o


@break_of("N2a")
def brk_n2a(o, t, names):
    f = first_row(o[u"行"], lambda r: r[u"科目"].split(u":")[0] in DICT_PREFIXES)
    if f is None:
        return None
    i, r = f
    name = r[u"科目"] + u"Zz"
    while name.replace(u":", u"_", 1) in names:
        name += u"Zz"
    r[u"科目"] = name
    return ("N2", i, u"科目"), o


@break_of("N3a")
def brk_n3a(o, t, names):
    f = first_row(o[u"行"], lambda r: not r[u"科目"].split(u":")[0].endswith(u"_cor"))
    if f is None:
        return None
    i, r = f
    want = (u"科目", r[u"科目"])
    o[u"独自の名"] = [e for e in o[u"独自の名"] if (e[u"種類"], e[u"名"]) != want]
    return ("N3", i, u"科目"), o


@break_of("N4a")
def brk_n4a(o, t, names):
    new = od([(u"種類", u"科目"), (u"名", u"zz_unused:Zz")])
    es = o[u"独自の名"]
    at = len(es)
    for j, e in enumerate(es):
        if (e[u"種類"], e[u"名"]) > (new[u"種類"], new[u"名"]):
            at = j
            break
    es.insert(at, new)
    return ("N4", None, u"独自の名"), o


@break_of("N4b")
def brk_n4b(o, t, names):
    es = o[u"独自の名"]
    if len(es) < 2:
        return None
    es[0], es[1] = es[1], es[0]
    return ("N4", None, u"独自の名"), o


@break_of("N5a")
def brk_n5a(o, t, names):
    f = first_row(o[u"行"], lambda r: len(r[u"次元"]) >= 1)
    if f is None:
        return None
    i, r = f
    r[u"次元"][0][0] += u"X"
    return ("N5", i, u"次元"), o


@break_of("N5b")
def brk_n5b(o, t, names):
    f = first_row(o[u"行"], lambda r: len(r[u"次元"]) >= 1)
    if f is None:
        return None
    i, r = f
    r[u"次元"][0][1] += u"X"
    return ("N5", i, u"次元"), o


@break_of("R1a")
def brk_r1a(o, t, names):
    del o[u"行"][0][u"対象"]
    return ("R1", 1, u"対象"), o


@break_of("R1b")
def brk_r1b(o, t, names):
    o[u"行"][0][u"備考"] = u"x"
    return ("R1", 1, u"備考"), o


@break_of("R1c")
def brk_r1c(o, t, names):
    f = first_row(o[u"行"], lambda r: r[u"種類"] == KIND_TEXT)
    if f is None:
        return None
    i, r = f
    r[u"値"] = VALUE_NONE
    return ("R1", i, u"値"), o


@break_of("R2a")
def brk_r2a(o, t, names):
    f = first_row(o[u"行"], lambda r: u"時点" in r[u"期間"])
    if f is None:
        return None
    i, r = f
    r[u"期間"][u"始まり"] = r[u"期間"][u"時点"]
    return ("R2", i, u"期間"), o


@break_of("R2b")
def brk_r2b(o, t, names):
    f = first_row(o[u"行"], lambda r: u"始まり" in r[u"期間"] and r[u"期間"][u"始まり"] != r[u"期間"][u"終わり"])
    if f is None:
        return None
    i, r = f
    p = r[u"期間"]
    p[u"始まり"], p[u"終わり"] = p[u"終わり"], p[u"始まり"]
    return ("R2", i, u"期間"), o


@break_of("R2c")
def brk_r2c(o, t, names):
    f = first_row(o[u"行"], lambda r: u"時点" in r[u"期間"])
    if f is None:
        return None
    i, r = f
    r[u"期間"][u"時点"] = r[u"期間"][u"時点"].replace(u"-", u"/")
    return ("R2", i, u"期間"), o


@break_of("R3a")
def brk_r3a(o, t, names):
    o[u"行"][0][u"対象"] = u"連結"
    return ("R3", 1, u"対象"), o


@break_of("R4a")
def brk_r4a(o, t, names):
    f = first_row(o[u"行"], lambda r: len(r[u"次元"]) >= 2)
    if f is None:
        return None
    i, r = f
    r[u"次元"].reverse()
    return ("R4", i, u"次元"), o


@break_of("R4b")
def brk_r4b(o, t, names):
    f = first_row(o[u"行"], lambda r: len(r[u"次元"]) >= 1)
    if f is None:
        return None
    i, r = f
    r[u"次元"].insert(1, list(r[u"次元"][0]))
    return ("R4", i, u"次元"), o


@break_of("R4c")
def brk_r4c(o, t, names):
    o[u"行"][0][u"次元"].insert(0, [AXIS_CONS, MEMBER_IND])
    return ("R4", 1, u"次元"), o


@break_of("R5a")
def brk_r5a(o, t, names):
    f = first_row(o[u"行"], lambda r: has_value(r) and len(r[u"値"].lstrip(u"-").partition(u".")[0]) >= 4)
    if f is None:
        return None
    i, r = f
    r[u"値"] = with_commas(r[u"値"])
    return ("R5", i, u"値"), o


@break_of("R5b")
def brk_r5b(o, t, names):
    f = first_row(o[u"行"], has_value)
    if f is None:
        return None
    i, r = f
    r[u"値"] = float(r[u"値"]) if u"." in r[u"値"] else int(r[u"値"])
    return ("R5", i, u"値"), o


@break_of("R5c")
def brk_r5c(o, t, names):
    f = first_row(o[u"行"], lambda r: has_value(r) and not r[u"値"].startswith(u"-"))
    if f is None:
        return None
    i, r = f
    r[u"値"] = u"+" + r[u"値"]
    return ("R5", i, u"値"), o


@break_of("R5d")
def brk_r5d(o, t, names):
    f = first_row(o[u"行"], lambda r: has_value(r) and u"." not in r[u"値"])
    if f is None:
        return None
    i, r = f
    r[u"値"] = r[u"値"] + u".0"
    return ("R5", i, u"値"), o


@break_of("R5e")
def brk_r5e(o, t, names):
    f = first_row(o[u"行"], has_value)
    if f is None:
        return None
    i, r = f
    r[u"値"] = r[u"値"].translate(dict((ord(str(n)), ord(u"０") + n) for n in range(10)))
    return ("R5", i, u"値"), o


@break_of("R6a")
def brk_r6a(o, t, names):
    f = first_row(o[u"行"], lambda r: is_num(r) and r[u"単位"] == u"通貨:JPY")
    if f is None:
        return None
    i, r = f
    r[u"単位"] = u"円"
    return ("R6", i, u"単位"), o


@break_of("R6b")
def brk_r6b(o, t, names):
    f = first_row(o[u"行"], lambda r: is_num(r) and r[u"単位"].startswith(u"通貨:"))
    if f is None:
        return None
    i, r = f
    r[u"単位"] = re.sub(r"[A-Z]", lambda m: m.group(0).lower(), r[u"単位"])
    return ("R6", i, u"単位"), o


@break_of("R6c")
def brk_r6c(o, t, names):
    f = first_row(o[u"行"], lambda r: is_num(r) and r[u"単位"] == UNIT_PURE)
    if f is None:
        return None
    i, r = f
    r[u"単位"] = u"他:xbrli:pure"
    return ("R6", i, u"単位"), o


@break_of("R7a")
def brk_r7a(o, t, names):
    f = first_row(o[u"行"], has_value)
    if f is None:
        return None
    i, r = f
    r[u"精度"] = str(r[u"精度"])
    return ("R7", i, u"精度"), o


@break_of("R7b")
def brk_r7b(o, t, names):
    f = first_row(o[u"行"], lambda r: is_num(r) and r[u"値"] == VALUE_NONE)
    if f is None:
        return None
    i, r = f
    r[u"精度"] = 0
    return ("R7", i, u"精度"), o


@break_of("R7c")
def brk_r7c(o, t, names):
    f = first_row(o[u"行"], has_value)
    if f is None:
        return None
    i, r = f
    r[u"表示の位"] = None
    return ("R7", i, u"表示の位"), o


@break_of("R7d")
def brk_r7d(o, t, names):
    f = first_row(o[u"行"], has_value)
    if f is None:
        return None
    i, r = f
    r[u"精度"] = True
    return ("R7", i, u"精度"), o


@break_of("R8a")
def brk_r8a(o, t, names):
    f = first_row(o[u"行"], lambda r: is_num(r) and r[u"値"] == u"0")
    if f is None:
        return None
    i, r = f
    r[u"精度"] = -r[u"表示の位"] - 1
    return ("R8", i, u"精度"), o


@break_of("R9a")
def brk_r9a(o, t, names):
    f = first_row(o[u"行"], lambda r: has_value(r) and r[u"値"] not in (u"0", u"-0"))
    if f is None:
        return None
    i, r = f
    r[u"値"] = add_step(r[u"値"], -r[u"精度"] - 1)
    return ("R9", i, u"値"), o


@break_of("R10a")
def brk_r10a(o, t, names):
    o[u"行"].append(copy.deepcopy(o[u"行"][0]))
    return ("R10", len(o[u"行"]), u"行"), o


@break_of("R10b")
def brk_r10b(o, t, names):
    f = first_row(o[u"行"], has_value)
    if f is None:
        return None
    _i, r = f
    c = copy.deepcopy(r)
    c[u"値"] = add_step(c[u"値"], -c[u"精度"])
    o[u"行"].append(c)
    return ("R10", len(o[u"行"]), u"行"), o


@break_of("R11a")
def brk_r11a(o, t, names):
    rows = o[u"行"]
    count = collections.Counter(r[u"科目"] for r in rows if u"時点" in r[u"期間"])
    f = first_row(rows, lambda r: u"時点" in r[u"期間"] and count[r[u"科目"]] >= 2)
    if f is None:
        return None
    name = f[1][u"科目"]
    i = max(j for j, r in enumerate(rows, 1) if r[u"科目"] == name and u"時点" in r[u"期間"])
    day = rows[i - 1][u"期間"][u"時点"]
    start = o[u"書類"][u"当期の始まり"]
    rows[i - 1][u"期間"] = od([(u"始まり", start if start <= day else day), (u"終わり", day)])
    return ("R11", i, u"期間"), o


@break_of("R12a")
def brk_r12a(o, t, names):
    rows = o[u"行"]
    count = collections.Counter(r[u"科目"] for r in rows if is_num(r))
    f = first_row(rows, lambda r: is_num(r) and count[r[u"科目"]] >= 2)
    if f is None:
        return None
    name = f[1][u"科目"]
    i = max(j for j, r in enumerate(rows, 1) if r[u"科目"] == name and is_num(r))
    r = rows[i - 1]
    r[u"単位"] = UNIT_SHARES if r[u"単位"] == UNIT_PURE else UNIT_PURE
    return ("R12", i, u"単位"), o


@break_of("R13a")
def brk_r13a(o, t, names):
    rows = o[u"行"]
    count = collections.Counter(r[u"科目"] for r in rows if is_num(r))
    f = first_row(rows, lambda r: is_num(r) and count[r[u"科目"]] >= 2)
    if f is None:
        return None
    name = f[1][u"科目"]
    i = max(j for j, r in enumerate(rows, 1) if r[u"科目"] == name and is_num(r))
    r = rows[i - 1]
    for k in (u"値", u"単位", u"表示の位", u"精度"):
        del r[k]
    r[u"種類"] = KIND_TEXT
    return ("R13", i, u"種類"), o


BREAKERS = od((k, _BREAK_FUNCS[k]) for k in BREAK_IDS)


# 変え方の関数の約束: ``f(obj)`` は新しい obj か ``None``(当てはまる所が無い)。型の規則を破らないように作る。
@change_of("Q1")
def chg_q1(o):
    rows = o[u"行"]
    keys = set(row_key(r) for r in rows)
    for r in rows:
        if is_num(r) and not r[u"次元"] and r[u"値"] != VALUE_NONE:
            other = TARGET_IND if r[u"対象"] == TARGET_DEF else TARGET_DEF
            k = (r[u"種類"], r[u"科目"], tuple(sorted(r[u"期間"].items())), other, ())
            if k not in keys:
                r[u"対象"] = other
                return o
    return None


@change_of("Q2")
def chg_q2(o):
    rows = o[u"行"]
    keys = set(row_key(r) for r in rows)
    users = collections.Counter(r[u"科目"] for r in rows)
    for r in rows:
        if not has_value(r):
            continue
        if not r[u"科目"].split(u":")[0].endswith(u"_cor") and users[r[u"科目"]] == 1:
            continue
        for r2 in rows:
            if is_num(r2) and r2[u"科目"] != r[u"科目"] and (u"時点" in r2[u"期間"]) == (u"時点" in r[u"期間"]) and r2[u"単位"] == r[u"単位"]:
                k = (r[u"種類"], r2[u"科目"], tuple(sorted(r[u"期間"].items())), r[u"対象"], tuple(tuple(x) for x in r[u"次元"]))
                if k not in keys:
                    r[u"科目"] = r2[u"科目"]
                    return o
    return None


@change_of("Q3")
def chg_q3(o):
    f = first_row(o[u"行"], has_value)
    if f is None:
        return None
    r = f[1]
    r[u"値"] = add_step(r[u"値"], -r[u"精度"])
    return o


@change_of("Q4")
def chg_q4(o):
    f = first_row(o[u"行"], lambda r: has_value(r) and r[u"値"] not in (u"0", u"-0"))
    if f is None:
        return None
    r = f[1]
    r[u"値"] = r[u"値"][1:] if r[u"値"].startswith(u"-") else u"-" + r[u"値"]
    return o


@change_of("Q5")
def chg_q5(o):
    rows = o[u"行"]
    keys = set(row_key(r) for r in rows)
    for r in rows:
        if not has_value(r):
            continue
        ds = [parse_date(x) for x in r[u"期間"].values()]
        if any(d is None or d.year <= 1 or (d.month, d.day) == (2, 29) for d in ds):
            continue
        new = od((k, parse_date(v).replace(year=parse_date(v).year - 1).isoformat()) for k, v in r[u"期間"].items())
        k = (r[u"種類"], r[u"科目"], tuple(sorted(new.items())), r[u"対象"], tuple(tuple(x) for x in r[u"次元"]))
        if k not in keys:
            r[u"期間"] = new
            return o
    return None


@change_of("Q6")
def chg_q6(o):
    rows = o[u"行"]
    count = collections.Counter(r[u"科目"] for r in rows if is_num(r))
    f = first_row(rows, lambda r: is_num(r) and count[r[u"科目"]] == 1 and r[u"単位"] == u"通貨:JPY")
    if f is None:
        return None
    f[1][u"単位"] = u"通貨:USD"
    return o


CHANGERS = od((k, _CHANGE_FUNCS[k]) for k in CHANGE_IDS)


def make_variants(type_text, names):
    u"""型の file の字から壊した file(壊し方ごと)と変えた file(変え方ごと)を作る。(壊し方 → (狙い, 字) か None, 変え方 → 字 か None)。"""
    base = loads_ordered(type_text)
    broken, changed = od(), od()
    for bid, fn in BREAKERS.items():
        made = fn(copy.deepcopy(base), type_text, names)
        broken[bid] = None if made is None else (made[0], made[1] if isinstance(made[1], str) else dump_text(made[1]))
    for qid, fn in CHANGERS.items():
        made = fn(copy.deepcopy(base))
        changed[qid] = None if made is None else dump_text(made)
    return broken, changed


def zero_break():
    return od((k, 0) for k in BREAK_RESULT_KEYS)


def zero_rules():
    return od((r, 0) for r in RULE_ORDER)


def judge_break(target, refusals):
    u"""壊した file の断りの並び → 壊し方の数(作れた 1 つ分)。"""
    rule, row, field = target
    hit = any(x[u"規則"] == rule and x[u"行"] == row and x[u"欄"] == field for x in refusals)
    res = zero_break()
    res[u"作れた"] = 1
    res[u"断った"] = 1 if hit else 0
    res[u"ちょうど 1 つ"] = 1 if hit and len(refusals) == 1 else 0
    res[u"別の規則で断った"] = 1 if (not hit and refusals) else 0
    res[u"断らなかった"] = 0 if refusals else 1
    return res


def judge_change(refusals):
    u"""変えた file の断りの並び → 変え方の数(作れた 1 つ分)。"""
    rules = zero_rules()
    for x in refusals:
        rules[x[u"規則"]] = 1
    return od([(u"作れた", 1), (u"通した", 0 if refusals else 1), (u"断った", rules)])


def zero_change():
    return od([(u"作れた", 0), (u"通した", 0), (u"断った", zero_rules())])


def write_variant_file(path, text):
    u"""型の file 由来の字(鍵・値)を file へ書く。UTF-8 に直せない字(孤立 surrogate)は ``\\uXXXX`` の形へ逃がす(JSON の字の中では読み戻すと元の字)。普通の字は 1 byte も変わらない。"""
    with open(path, "wb") as fh:
        fh.write(text.encode("utf-8", "backslashreplace"))


def run_variants(type_text, names, work, cwd, cap=None, names_file=None):
    u"""壊した file・変えた file を ``work`` の中に書き、受け口(別の process)に 1 回で掛ける。(壊し方ごとの数, 変え方ごとの数)。"""
    broken, changed = make_variants(type_text, names)
    folder = os.path.join(work, "variants")
    os.makedirs(folder)
    for bid, made in broken.items():
        if made is not None:
            write_variant_file(os.path.join(folder, bid + ".json"), made[1])
    for qid, text in changed.items():
        if text is not None:
            write_variant_file(os.path.join(folder, qid + ".json"), text)
    res = exec_accept(folder, cwd, cap, names_file, many=True) if os.listdir(folder) else od()
    brk, chg = od(), od()
    for bid, made in broken.items():
        brk[bid] = zero_break() if made is None else judge_break(made[0], res[bid + ".json"][u"断り"])
    for qid, text in changed.items():
        if text is None:
            chg[qid] = zero_change()
        else:
            chg[qid] = judge_change(res[qid + ".json"][u"断り"])
    return brk, chg


# ======================================================================================================
# 別の process で受け口の検査を掛ける
def accept_command(path, names_file=None, many=False):
    cmd = [sys.executable, "-I", SCRIPT_PATH, "--accept-dir" if many else "--accept", path]
    if names_file:
        cmd += ["--names-file", names_file]
    return cmd


def run_capture(cmd, cwd, timeout):
    u"""(終わりの値, 標準出力の字, 標準のエラーの字, 時間の上限を超えたか)。shell を通さない。"""
    try:
        p = subprocess.run(list(cmd), cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, shell=False)
    except subprocess.TimeoutExpired:
        return None, u"", u"", True
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace"), False


def exec_accept(path, cwd, cap=None, names_file=None, many=False):
    u"""受け口の検査を別の process で 1 回。返り値は標準出力の JSON(1 つの file なら {受理, 断り}・folder ならファイル名 → {受理, 断り})。読めなければ ``Refuse``。"""
    cap = cap or run_capture
    rc, out, err, timed_out = cap(accept_command(path, names_file, many), cwd, TIMEOUT_SEC)
    if timed_out:
        raise Refuse(u"受け口の検査が時間の上限を超えた")
    if rc != 0:
        raise Refuse(u"受け口の検査が 0 でない終わりの値で終わった")
    try:
        return json.loads(out, object_pairs_hook=od)
    except ValueError:
        raise Refuse(u"受け口の検査の出力が JSON でない")


# ======================================================================================================
# 起こす命令(答えを読む。前の便の script を ``prev()`` で読む)と型から作る命令
_PREV = {}


def load_sibling(name, fname):
    u"""前の便の script を、他と重ならない一意の名で読む(関数は呼ぶだけ。写さない)。"""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, fname))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def prev():
    u"""便 XM0 の script(と、それが読む便 XP0・XT0・XB0・XV0・XG0 の script)。**受け口の検査はこれを呼ばない。**"""
    if not _PREV:
        m = load_sibling(PREV_NAME, PREV_FILE)
        _PREV.update(M=m, P=m.P, T=m.T, B=m.B, V=m.V, W=m.W)
    return types.SimpleNamespace(**_PREV)


def name_class(name):
    u"""名 → 辞書の在る接頭辞・辞書の無い ``_cor`` の接頭辞・提出者別。"""
    prefix = name.split(":")[0]
    if prefix in DICT_PREFIXES:
        return u"辞書の在る接頭辞"
    return u"辞書の無い _cor の接頭辞" if prefix.endswith("_cor") else u"提出者別"


def other_unit(unit):
    u"""単位の定義 → ``他:`` の字。単位の定義が読めなければ ``None``。"""
    def ok(ms):
        return bool(ms) and all(isinstance(x, str) and x != "" and not re.search(r"\s|[*÷]", x) for x in ms)
    ms, d = list(unit.get("measures") or ()), unit.get("divide")
    if d is None:
        return UNIT_OTHER + u"*".join(sorted(ms)) if ok(ms) else None
    if ms or not ok(d["num"]) or not ok(d["den"]):
        return None
    return UNIT_OTHER + u"*".join(sorted(d["num"])) + UNIT_PER + u"*".join(sorted(d["den"]))


def v1_unit(unit):
    u"""単位の定義 → 型の単位の字(4 つの形か ``他:``)。読めなければ ``None``。"""
    f = prev().M.unit_form(unit)
    if f is not None and (f in (UNIT_SHARES, UNIT_PURE) or UNIT_FORM_RE.fullmatch(f)):
        return f
    return other_unit(unit)


def period_writable(period):
    u"""期の (種類, 日) が型に書けるか(形が時点か期間・日が在る日・始まりが終わり以前)。"""
    kind, dates = period
    if kind not in ("instant", "duration") or not dates:
        return False
    ds = [parse_date(x) for x in dates]
    return all(x is not None for x in ds) and (len(ds) == 1 or ds[0] <= ds[1])


def reanalyze(an):
    u"""便 XM0 の解析の戻り(``analyze``)を、第 1 版の決めで読み直す(理由 (a)(d) を狭め、(g) を数え直し、型の行を作り直す)。"""
    facts = an["facts"]
    for f in facts:
        keep = set(f["reasons"])
        keep.discard("g")
        if "a" in keep and period_writable(f["period"]):
            keep.discard("a")
        f["form1"] = None
        if f["isnum"] and f["unit"] is not None:
            f["form1"] = v1_unit(f["unit"])
        if "d" in keep and f["form1"] is not None:
            keep.discard("d")
        f["reasons"] = keep
        for k in ("row", "out", "key"):
            f.pop(k, None)
    groups = od()
    for f in facts:
        if not f["reasons"]:
            f["key"] = (f["isnum"], f["attrs"]["name"], tuple(f["period"][1]), f["period"][0], f["target"], tuple(f["dims"]))
            groups.setdefault(f["key"], []).append(f)
    for key, fs in groups.items():
        if key[0] and len(set((x["value"], x["form1"], x["shift"], x["prec"]) for x in fs)) > 1:
            for x in fs:
                x["reasons"].add("g")
    rows, row_of = [], {}
    for f in facts:
        if f["reasons"]:
            continue
        k = f["key"]
        if k not in row_of:
            row_of[k] = len(rows)
            rows.append(od([("kind", KIND_NUM if f["isnum"] else KIND_TEXT), ("name", f["attrs"]["name"]), ("period", list(f["period"][1])), ("pkind", f["period"][0]), ("target", f["target"]),
                            ("dims", [list(x) for x in f["dims"]]), ("value", f["value"]), ("unit", f["form1"]), ("shift", f["shift"]), ("prec", f["prec"]), ("count", 0)]))
        rows[row_of[k]]["count"] += 1
        f["row"] = row_of[k]
    outside = [f for f in facts if f["reasons"]]
    for j, f in enumerate(outside):
        f["out"] = j
    return od([("dec", an["dec"]), ("facts", facts), ("rows", rows), ("outside", outside), ("ctxs", an["ctxs"]), ("units", an["units"])])


def type_object(v1):
    u"""第 1 版の解析 → 型の file の object。"""
    dec = v1["dec"]
    custom = set()
    rows = []
    for r in v1["rows"]:
        if name_class(r["name"]) == u"提出者別":
            custom.add((u"科目", r["name"]))
        for ax, m in r["dims"]:
            for kind, n in ((u"軸", ax), (u"member", m)):
                if name_class(n) == u"提出者別":
                    custom.add((kind, n))
        per = od([(u"時点", r["period"][0])]) if r["pkind"] == "instant" else od([(u"始まり", r["period"][0]), (u"終わり", r["period"][1])])
        o = od([(u"種類", r["kind"]), (u"科目", r["name"]), (u"期間", per), (u"対象", r["target"]), (u"次元", [list(x) for x in r["dims"]])])
        if r["kind"] == KIND_NUM:
            o[u"値"], o[u"単位"] = r["value"], r["unit"]
            o[u"表示の位"] = None if r["value"] == VALUE_NONE else r["shift"]
            o[u"精度"] = None if r["value"] == VALUE_NONE else r["prec"]
        rows.append(o)
    return od([(u"型の版", TYPE_VERSION),
               (u"書類", od([(u"提出者の識別子", dec["ident"]), (u"識別子の scheme", dec["scheme"]), (u"当期の始まり", dec["start"]), (u"当期の終わり", dec["end"]), (u"提出日", dec["filing"])])),
               (u"独自の名", [od([(u"種類", k), (u"名", n)]) for k, n in sorted(custom)]), (u"行", rows)])


def write_folders(root, files, names, tables, v1):
    u"""``type/``(型の file)・``carry/``(持ち込み)・``outside/``(型の外)を別々の folder に書く。元の字・元の属性・元の文脈と単位の定義は carry に置かない(型の外だけは outside に写す)。"""
    M = prev().M
    P, wb = M.P, M.write_bytes
    for sub in ("type", "carry", "outside"):
        os.makedirs(os.path.join(root, sub))
    by_where = dict(((f["fi"], f["where"], f["idx"]), f) for f in v1["facts"])
    index = od([("htm", []), ("taxonomy", od([("file", M.TAXONOMY_FILE), ("names", od((k, P.rel_of(names[k])) for k in M.FILE_KINDS))]))])
    carry = os.path.join(root, "carry")
    for fi, (name, plain, F, H) in enumerate(files):
        wb(os.path.join(carry, P.TEXT_FMT % fi), plain.encode("utf-8"))
        cf = []
        for i, e in enumerate(F):
            o = od([("kind", e["kind"]), ("self", e["self"]), ("start", e["start"]), ("end", e["end"]), ("parent", e["parent"])])
            f = by_where.get((fi, "F", i))
            if f is None:
                o["attrs"] = e["attrs"]
            elif "row" in f:
                o["row"], o["carry"] = f["row"], M.carried_attrs(f)
            else:
                o["out"] = f["out"]
            cf.append(o)
        ch = None
        if H is not None:
            hid = []
            for j, h in enumerate(H["hidden"]):
                f = by_where[(fi, "H", j)]
                o = od([("kind", h["kind"]), ("self", h["self"]), ("text", h["text"])])
                if "row" in f:
                    o["row"], o["carry"] = f["row"], M.carried_attrs(f)
                else:
                    o["out"] = f["out"]
                hid.append(o)
            ch = od([("pos", H["pos"]), ("before", H["before"]), ("sections", H["sections"]), ("hidden", hid), ("references", H["references"]),
                     ("resources", [r for r in H["resources"] if r["type"] == "ref"])])
        wb(os.path.join(carry, CARRY_FMT % fi), P.jdump(od([("F", cf), ("H", ch)])))
        index["htm"].append(od([("name", P.rel_of(name)), ("text", P.TEXT_FMT % fi), ("carry", CARRY_FMT % fi)]))
    wb(os.path.join(carry, M.TAXONOMY_FILE), P.jdump(od([("tables", tables)])))
    wb(os.path.join(carry, M.INDEX_FILE), P.jdump(index))
    wb(os.path.join(root, "type", "type.json"), dump_text(type_object(v1)).encode("utf-8"))
    ofacts, used_ctx, used_unit = [], set(), set()
    for f in v1["outside"]:
        ofacts.append(od([("kind", f["kind"]), ("reasons", sorted(f["reasons"])), ("attrs", f["attrs"])]))
        used_ctx.add(f["attrs"]["contextRef"])
        if f["isnum"] and f["attrs"].get("unitRef") in v1["units"]:
            used_unit.add(f["attrs"]["unitRef"])
    wb(os.path.join(root, "outside", M.OUTSIDE_FILE), P.jdump(od([("facts", ofacts), ("contexts", [c for i, c in v1["ctxs"].items() if i in used_ctx]),
                                                                    ("units", [u for i, u in v1["units"].items() if i in used_unit])])))


def derive_v1(entries, root):
    u"""元の包みから型・持ち込み・型の外の folder を作る。(第 1 版の解析, 表の並び)。断りは ``Refuse``。"""
    M = prev().M
    try:
        files, names, tables = M.P.peel_tables(entries)
        v1 = reanalyze(M.analyze(files))
    except M.Refuse as exc:
        raise Refuse(exc.reason)
    except (M.B.Decline, M.T.Decline) as exc:
        raise Refuse(exc.reason)
    try:
        write_folders(root, files, names, tables, v1)
    except Exception:                                      # noqa: BLE001
        shutil.rmtree(root, ignore_errors=True)
        raise Refuse(u"folder に書けない形")
    return v1, files


# ---- 型から作る
def period_label(kind, dates, dec):
    u"""期の名: 便 XM0 の規則で作れればその名。作れなければ ``At`` + 日の数字 8 つ・``From`` + 始まり + ``To`` + 終わり。"""
    n = prev().M.period_name(kind, dates, dec)
    if n:
        return n
    dg = [d.replace(u"-", u"") for d in dates]
    return u"At" + dg[0] if kind == "instant" else u"From" + dg[0] + u"To" + dg[1]


def row_period(r):
    p = r[u"期間"]
    return ("instant", [p[u"時点"]]) if u"時点" in p else ("duration", [p[u"始まり"], p[u"終わり"]])


def row_members(r):
    m = [tuple(x) for x in r[u"次元"]]
    return m + ([(AXIS_CONS, MEMBER_IND)] if r[u"対象"] == TARGET_IND else [])


def other_def(uid, form):
    parts = form[len(UNIT_OTHER):].split(UNIT_PER)
    if len(parts) == 1:
        return od([("type", "unit"), ("id", uid), ("measures", parts[0].split("*")), ("divide", None)])
    return od([("type", "unit"), ("id", uid), ("measures", []), ("divide", od([("num", parts[0].split("*")), ("den", parts[1].split("*"))]))])


def v1_definitions(dec, rows):
    u"""型の行 → (文脈の定義の並び, 単位の定義の並び, 行ごとの (文脈の id, 単位の id))。id が違う組で重なれば ``Refuse``。"""
    M = prev().M
    defs, info = {}, []
    others = sorted(set(r[u"単位"] for r in rows if r[u"種類"] == KIND_NUM and r[u"単位"].startswith(UNIT_OTHER)))
    other_id = dict((u, "U%04d" % n) for n, u in enumerate(others, 1))
    units, uid_of = od(), {}
    for r in rows:
        kind, dates = row_period(r)
        members = row_members(r)
        cid = M.context_id(period_label(kind, dates, dec), kind, members)
        group = (kind, tuple(dates), tuple(sorted(members)))
        if cid in defs and defs[cid][0] != group:
            raise Refuse(u"文脈の id が違う組で重なる")
        defs.setdefault(cid, (group, M.context_def(cid, dec, kind, dates, members)))
        uid = None
        if r[u"種類"] == KIND_NUM:
            u = r[u"単位"]
            if u in other_id:
                uid, d = other_id[u], other_def(other_id[u], u)
            else:
                uid, d = M.unit_from_form(u)
            units.setdefault(uid, d)
        info.append((cid, uid))
    return [defs[k][1] for k in sorted(defs)], [units[k] for k in sorted(units)], info


def v1_attrs(r, cid, uid, carry):
    u"""型の行 + 持ち込みの属性 → 作る fact の属性(名の昇順)。"""
    M = prev().M
    typed = M.NUM_TYPED if r[u"種類"] == KIND_NUM else M.TEXT_TYPED
    if any(k in typed for k in carry):
        raise Refuse(u"持ち込みに型の属性が在る")
    a = {"name": r[u"科目"], "contextRef": cid}
    if r[u"種類"] == KIND_NUM:
        a["unitRef"] = uid
        if r[u"値"] == VALUE_NONE:
            a["xsi:nil"] = "true"
        else:
            a["decimals"], a["scale"], a["format"] = str(r[u"精度"]), str(r[u"表示の位"]), FORMAT_OK
            if r[u"値"].startswith(u"-"):
                a["sign"] = "-"
    a.update(carry)
    return dict(sorted(a.items()))


def render_v1(folder):
    u"""型・持ち込み・型の外の folder → (表の並び [(名, 素の本文, 表 F, 表 H)], 名, 表)。folder の中の file のほかを読まない。知らない形・例外は ``Refuse``。"""
    M = prev().M
    P = M.P
    try:
        with open(os.path.join(folder, "type", "type.json"), "rb") as fh:
            typ = json.loads(fh.read().decode("utf-8"), object_pairs_hook=od)
        index = M.jload(M.read_bytes(os.path.join(folder, "carry", M.INDEX_FILE)))
        outside = M.jload(M.read_bytes(os.path.join(folder, "outside", M.OUTSIDE_FILE)))
        doc, rows = typ[u"書類"], typ[u"行"]
        dec = od([("scheme", doc[u"識別子の scheme"]), ("ident", doc[u"提出者の識別子"]), ("start", doc[u"当期の始まり"]), ("end", doc[u"当期の終わり"]), ("filing", doc[u"提出日"])])
        ctxs, units, info = v1_definitions(dec, rows)
        ctxs = M.merge_outside(ctxs, outside["contexts"])
        units = M.merge_outside(units, outside["units"])
        files, host = [], None
        for item in index["htm"]:
            plain = M.read_bytes(os.path.join(folder, "carry", P.safe_local(item["text"]))).decode("utf-8")
            carry = M.jload(M.read_bytes(os.path.join(folder, "carry", P.safe_local(item["carry"]))))
            F = []
            for e in carry["F"]:
                a = e.get("attrs")
                if "row" in e:
                    a = v1_attrs(rows[e["row"]], info[e["row"]][0], info[e["row"]][1], e["carry"])
                elif "out" in e:
                    a = dict(sorted(outside["facts"][e["out"]]["attrs"].items()))
                else:
                    a = dict(sorted(a.items()))
                F.append(od([("kind", e["kind"]), ("self", e["self"]), ("start", e["start"]), ("end", e["end"]), ("parent", e["parent"]), ("attrs", a)]))
            H = None
            ch = carry["H"]
            if ch is not None:
                hid = []
                for h in ch["hidden"]:
                    if "row" in h:
                        a = v1_attrs(rows[h["row"]], info[h["row"]][0], info[h["row"]][1], h["carry"])
                    else:
                        a = dict(sorted(outside["facts"][h["out"]]["attrs"].items()))
                    hid.append(od([("kind", h["kind"]), ("self", h["self"]), ("attrs", a), ("text", h["text"])]))
                res = list(ch["resources"])
                if "ix:resources" in ch["sections"]:
                    host = True
                    res = res + ctxs + units
                H = od([("sections", ch["sections"]), ("hidden", hid), ("references", ch["references"]), ("resources", res), ("pos", ch["pos"]), ("before", ch["before"])])
            files.append((M.PUBLICDOC + P.safe_rel(item["name"]), plain, F, H))
        if (ctxs or units) and not host:
            raise Refuse(u"作った定義を置く頭の部が無い")
        tax = index["taxonomy"]
        tables = M.jload(M.read_bytes(os.path.join(folder, "carry", P.safe_local(tax["file"]))))["tables"]
        names = od((k, M.PUBLICDOC + P.safe_rel(tax["names"][k])) for k in M.FILE_KINDS)
        return files, names, tables
    except Refuse:
        raise
    except M.Refuse as exc:
        raise Refuse(exc.reason)
    except (M.B.Decline, M.T.Decline) as exc:
        raise Refuse(exc.reason)
    except Exception:                                      # noqa: BLE001  知らない形は断る
        raise Refuse(u"作る途中の例外")


def build_main(argv):
    u"""型から作る命令。``--build <folder> <原稿の folder> [--names-file <辞書の名の JSON>]``。**受け口が断った file からは作らない。** 終わりの値: 0・64(使い方)・2(断り)・3(辞書)・1(例外)。"""
    args = list(argv)
    names_file = None
    if "--names-file" in args:
        i = args.index("--names-file")
        if i + 1 >= len(args):
            print(u"使い方: --build <folder> <原稿の folder>", file=sys.stderr)
            return EXIT_USAGE
        names_file = args[i + 1]
        del args[i:i + 2]
    if len(args) != 3 or args[0] != "--build":
        print(u"使い方: --build <folder> <原稿の folder>", file=sys.stderr)
        return EXIT_USAGE
    folder, out = args[1], args[2]
    try:
        names = load_names_file(names_file) if names_file else load_dictionary(default_dictionary_dir())
    except (DictError, OSError, ValueError):
        print(DECLINE_PREFIX + u"標準の辞書が読めない", file=sys.stderr)
        return EXIT_DICT
    try:
        with open(os.path.join(folder, "type", "type.json"), "rb") as fh:
            data = fh.read()
        refusals = check_safe(data, names)
        if refusals:
            rules = u",".join(sorted(set(x[u"規則"] for x in refusals), key=RULE_ORDER.index))
            print(DECLINE_PREFIX + (u"受け口が断った(規則 %s)" % rules)[:REASON_MAX], file=sys.stderr)
            return EXIT_DECLINE
        files, tnames, tables = render_v1(folder)
        prev().M.P.write_folder(out, files, tnames, tables)
    except Refuse as exc:
        print(DECLINE_PREFIX + exc.reason, file=sys.stderr)
        return EXIT_DECLINE
    except Exception:                                      # noqa: BLE001
        print(u"ERROR", file=sys.stderr)
        return EXIT_ERROR
    return 0


def build_command(folder, out, names_file=None):
    cmd = [sys.executable, "-I", SCRIPT_PATH, "--build", folder, out]
    return cmd + (["--names-file", names_file] if names_file else [])


def decline_reason(stderr_text):
    for line in stderr_text.splitlines():
        if line.startswith(DECLINE_PREFIX):
            return line[len(DECLINE_PREFIX):][:REASON_MAX]
    return None


def exec_build(folder, out, cwd, proc=None, names_file=None):
    u"""型から作る命令を別の process で 1 回。(成功か, 断りの理由, 秒)。"""
    proc = proc or prev().P.run_process
    t0 = time.time()
    rc, err, timed_out = proc(build_command(folder, out, names_file), cwd, TIMEOUT_SEC)
    secs = time.time() - t0
    if timed_out:
        return False, u"型から作る命令が時間の上限を超えた", secs
    if rc != 0:
        reason = decline_reason(err)
        return False, (reason if reason is not None else u"型から作る命令が 0 でない終わりの値で終わった"), secs
    return True, u"", secs


# ======================================================================================================
# 書類 1 本
def zero_rec():
    def two():
        return od([(KIND_NUM, 0), (KIND_TEXT, 0)])

    def classes():
        return od((c, 0) for c in (u"辞書の在る接頭辞", u"辞書の無い _cor の接頭辞", u"提出者別"))
    return od([
        (u"断った", False), (u"断った段", u""), (u"断った理由", u""),
        (u"対象の fact", od([(KIND_NUM, 0), (KIND_TEXT, 0), (u"隠し", 0), (u"脚注", 0)])),
        (u"型に入った fact", two()),
        (u"型の外の fact", od([(u"理由ごと", od((r, two()) for r in REASONS)), (u"合計", two())])),
        (u"型の行", od([(KIND_NUM, 0), (KIND_TEXT, 0), (u"2 つ以上の fact をまとめた行", 0), (u"値が -0 の行", 0), (u"期の表に無い期間の行", 0), (u"他: の単位の行", 0)])),
        (u"独自の名", od((k, 0) for k in NAME_KINDS)),
        (u"名の数", od((k, classes()) for k in NAME_KINDS)),
        (u"受け口", od([(u"受理した", False), (u"断った", False), (u"断りの数", 0), (u"規則ごとの断りの数", zero_rules()), (u"規則ごとの断った書類", od((r, False) for r in RULE_ORDER)),
                       (u"規則と欄ごとの断りの数", od())])),
        (u"比べ方 1", od([(u"属性が意味として同じ", False), (u"文脈の名も同じ", False), (u"違った fact", 0), (u"属性ごとの違った fact", od())])),
        (u"比べ方 2", od([(u"組めた", False), (u"fact が意味として同じ", False), (u"字も含めて行が同じ", False), (u"鳴り方が同じ", False), (u"2 回が同じ", False)])),
        (u"壊し方", od((k, zero_break()) for k in BREAK_IDS)),
        (u"形は合っているが中身が違う", od((k, zero_change()) for k in CHANGE_IDS)),
        (u"秒", od([(u"型から作る命令", None)])),
    ])


def fill_type_stats(rec, v1):
    M = prev().M
    for f in v1["facts"]:
        k = KIND_NUM if f["isnum"] else KIND_TEXT
        rec[u"対象の fact"][k] += 1
        if f["where"] == "H":
            rec[u"対象の fact"][u"隠し"] += 1
        if f["reasons"]:
            rec[u"型の外の fact"][u"合計"][k] += 1
            for r in f["reasons"]:
                rec[u"型の外の fact"][u"理由ごと"][r][k] += 1
        else:
            rec[u"型に入った fact"][k] += 1
    rows = rec[u"型の行"]
    names = od((k, set()) for k in NAME_KINDS)
    for r in v1["rows"]:
        rows[r["kind"]] += 1
        rows[u"2 つ以上の fact をまとめた行"] += 1 if r["count"] >= 2 else 0
        rows[u"値が -0 の行"] += 1 if r["value"] == u"-0" else 0
        rows[u"期の表に無い期間の行"] += 1 if M.period_name(r["pkind"], r["period"], v1["dec"]) is None else 0
        rows[u"他: の単位の行"] += 1 if (r["kind"] == KIND_NUM and r["unit"].startswith(UNIT_OTHER)) else 0
        names[u"科目"].add(r["name"])
        for ax, m in r["dims"]:
            names[u"軸"].add(ax)
            names[u"member"].add(m)
    for k, ns in names.items():
        for n in ns:
            rec[u"名の数"][k][name_class(n)] += 1
        rec[u"独自の名"][k] = sum(1 for n in ns if name_class(n) == u"提出者別")


def fill_footnotes(rec, files):
    rec[u"対象の fact"][u"脚注"] = sum(1 for x in files for e in x[2] if e["kind"] == "footnote")


def fill_accept(rec, res):
    refs = res[u"断り"]
    a = rec[u"受け口"]
    a[u"受理した"], a[u"断った"], a[u"断りの数"] = not refs, bool(refs), len(refs)
    for x in refs:
        a[u"規則ごとの断りの数"][x[u"規則"]] += 1
        a[u"規則ごとの断った書類"][x[u"規則"]] = True
        key = x[u"規則"] + u"/" + x[u"欄"]
        a[u"規則と欄ごとの断りの数"][key] = a[u"規則と欄ごとの断りの数"].get(key, 0) + 1
    a[u"規則と欄ごとの断りの数"] = od(sorted(a[u"規則と欄ごとの断りの数"].items()))


def decline(rec, stage, reason):
    rec[u"断った"], rec[u"断った段"], rec[u"断った理由"] = True, stage, reason
    return rec


def carry_forbidden_v1(root):
    u"""持ち込み(carry/)に入れないもの(型に入った fact の型の属性・文脈と単位の定義)が在れば、その説明の並び。無ければ空。"""
    M = prev().M
    bad = []
    index = M.jload(M.read_bytes(os.path.join(root, "carry", M.INDEX_FILE)))
    rows = json.loads(M.read_bytes(os.path.join(root, "type", "type.json")).decode("utf-8"))[u"行"]
    for item in index["htm"]:
        carry = M.jload(M.read_bytes(os.path.join(root, "carry", item["carry"])))
        ents = [e for e in carry["F"] if "row" in e]
        ch = carry["H"]
        if ch is not None:
            ents += [h for h in ch["hidden"] if "row" in h]
            bad += [u"持ち込みに文脈か単位の定義が在る" for r in ch["resources"] if r.get("type") != "ref"]
        for e in ents:
            typed = M.NUM_TYPED if rows[e["row"]][u"種類"] == KIND_NUM else M.TEXT_TYPED
            if "attrs" in e or any(k in typed for k in e["carry"]):
                bad.append(u"型に入った fact の型の属性が持ち込みに在る")
    return bad


def process_doc(tool, zip_path, tmp_root=None, runner=None, proc=None, cap=None, keep=None, names_file=None, names=None):
    u"""書類 1 本。書類ごとの数。元の包みと組み直した包みを同じ掛け方で 1 回ずつ。受け口の検査・型から作る命令は別の process で呼ぶ。``keep`` が在れば型・持ち込み・型の外の folder と組んだ原稿をそこへ残す。"""
    pv = prev()
    M, P, B, V = pv.M, pv.P, pv.B, pv.V
    entries = B.load_package(zip_path)
    rec = zero_rec()
    d = tempfile.mkdtemp(prefix="xj0_", dir=tmp_root)
    try:
        orig_zip = os.path.join(d, "orig.zip")
        B.write_package(entries, orig_zip)
        orig, oh, orows = M.run_facts(tool, orig_zip, d, "orig", runner)
        cwd = os.path.join(d, "cwd")
        os.makedirs(cwd)
        root = os.path.join(d, "made")
        try:
            v1, files = derive_v1(entries, root)
        except Refuse as exc:
            return decline(rec, STAGES[0], exc.reason)
        except Exception:                                  # noqa: BLE001
            return decline(rec, STAGES[0], u"型を作る途中の例外")
        fill_type_stats(rec, v1)
        fill_footnotes(rec, files)
        if carry_forbidden_v1(root):
            raise pv.W.Stop(u"**持ち込みに入れないものが在る。止める**")
        type_path = os.path.join(root, "type", "type.json")
        try:
            res = exec_accept(type_path, cwd, cap, names_file)
        except Refuse as exc:
            return decline(rec, STAGES[1], exc.reason)
        fill_accept(rec, res)
        if res[u"断り"]:
            rules = u",".join(sorted(set(x[u"規則"] for x in res[u"断り"]), key=RULE_ORDER.index))
            return decline(rec, STAGES[1], (u"規則 %s" % rules)[:REASON_MAX])
        try:
            with io.open(type_path, encoding="utf-8") as fh:
                type_text = fh.read()
            dict_names = names if names is not None else (load_names_file(names_file) if names_file else load_dictionary(default_dictionary_dir()))
            rec[u"壊し方"], rec[u"形は合っているが中身が違う"] = run_variants(type_text, dict_names, d, cwd, cap, names_file)
        except Refuse as exc:
            return decline(rec, STAGES[1], exc.reason)
        if keep:
            shutil.copytree(root, os.path.join(keep, "made"))
        out1 = os.path.join(d, "man1")
        ok, reason, secs = exec_build(root, out1, cwd, proc, names_file)
        rec[u"秒"][u"型から作る命令"] = round(secs, 1)
        if not ok:
            return decline(rec, STAGES[2], reason)
        new_files = M.load_manuscript(out1)
        a1, names_same, ndiff, per = M.compare_attrs(files, new_files)
        rec[u"比べ方 1"] = od([(u"属性が意味として同じ", bool(a1)), (u"文脈の名も同じ", bool(names_same)), (u"違った fact", ndiff), (u"属性ごとの違った fact", per)])
        if keep:
            shutil.copytree(out1, os.path.join(keep, "manuscript"))
        out2 = os.path.join(d, "man2")
        ok2, _r2, _s2 = exec_build(root, out2, cwd, proc, names_file)
        tree_same = bool(ok2 and P.read_tree(out2) == P.read_tree(out1))
        b1 = os.path.join(d, "pack1")
        okb, reason, _sb = P.exec_build(out1, b1, cwd, proc)
        if not okb:
            return decline(rec, STAGES[3], reason)
        tree = P.read_tree(b1)
        if set(tree) != P.expected_names(M.jload(M.read_bytes(os.path.join(out1, P.INDEX_FILE)))):
            return decline(rec, STAGES[3], u"出す folder の file の名が目次と合わない")
        b2 = os.path.join(d, "pack2")
        okb2, _rb2, _sb2 = P.exec_build(out2, b2, cwd, proc) if ok2 else (False, u"", 0)
        rec[u"比べ方 2"][u"2 回が同じ"] = bool(tree_same and okb2 and P.read_tree(b2) == tree)
        new_zip = os.path.join(d, "new.zip")
        B.write_package(P.rebuilt_pack(entries, tree), new_zip)
        new, nh, nrows = M.run_facts(tool, new_zip, d, "new", runner)
        if new[u"類"] == V.CLS_STOPPED and orig[u"類"] != V.CLS_STOPPED:
            return decline(rec, STAGES[4], u"道具が組み直した包みで止まった")
        om = M.normalize_rows(oh, orows, M.unit_map_of(files))
        nm = M.normalize_rows(nh, nrows, M.unit_map_of(new_files))
        c2 = rec[u"比べ方 2"]
        c2[u"組めた"] = True
        c2[u"fact が意味として同じ"] = bool(om and nm and om == nm)
        c2[u"字も含めて行が同じ"] = B.facts_same(sorted(orows), sorted(nrows))
        c2[u"鳴り方が同じ"] = B.sounds_same(orig, new)
        return rec
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ======================================================================================================
# 数える(封 §2)
def sum_nested(items):
    return prev().M.sum_nested(items)


def group_totals(entries):
    u"""書類ごとの数の並び → §2 の数。"""
    body = [od((k, v) for k, v in e.items() if k not in (u"番号", u"断った段", u"断った理由", u"秒")) for e in entries]
    tot = sum_nested(body) if body else od()
    reasons = collections.Counter((e[u"断った段"], e[u"断った理由"]) for e in entries if e[u"断った"])
    stage = od((s, od(sorted((r, n) for (st, r), n in reasons.items() if st == s))) for s in STAGES)
    zero_out = sum(1 for e in entries if not e[u"断った"] and e[u"型の外の fact"][u"合計"][KIND_NUM] + e[u"型の外の fact"][u"合計"][KIND_TEXT] == 0)
    out = od([(u"書類", len(entries)), (u"断った書類", sum(1 for e in entries if e[u"断った"])), (u"断った段と理由ごと", stage), (u"型の外の fact が 0 の書類", zero_out)])
    out[u"数"] = tot
    out[u"期の表に無い期間の行が在る書類"] = sum(1 for e in entries if e[u"型の行"][u"期の表に無い期間の行"] >= 1)
    out[u"他: の単位の行が在る書類"] = sum(1 for e in entries if e[u"型の行"][u"他: の単位の行"] >= 1)
    out[u"型から作る命令の秒の合計"] = round(sum(e[u"秒"][u"型から作る命令"] or 0 for e in entries), 1)
    return out


def totals_of(per_doc, dev_count=DEV_COUNT):
    dev, prod = per_doc[:dev_count], per_doc[dev_count:]
    return od([(u"開発の 5 本", group_totals(dev)), (u"本番だけの %d 本" % (len(per_doc) - dev_count), group_totals(prod)), (u"全部", group_totals(per_doc))])


def judged(tot):
    u"""封 §4 の判定に要る数(当たり・外れは書かない)。分母は本番だけの 62 本。"""
    prod = tot[[k for k in tot if k.startswith(u"本番だけの")][0]]
    z = prod[u"数"]
    out_tot, tgt = z[u"型の外の fact"][u"合計"], z[u"対象の fact"]
    acc = z[u"受け口"]
    brk, chg = z[u"壊し方"], z[u"形は合っているが中身が違う"]
    s = lambda key: sum(v[key] for v in brk.values())                                   # noqa: E731
    qrules = od((r, sum(v[u"断った"][r] for v in chg.values())) for r in RULE_ORDER)
    cor = z[u"名の数"][u"科目"]
    return od([
        (u"XJ0-1 起こした file を受け口が受理した書類", od([(u"書類", acc[u"受理した"]), (u"分母", prod[u"書類"])])),
        (u"XJ0-2 1 本でも断った規則", od([(u"規則の数", sum(1 for n in acc[u"規則ごとの断った書類"].values() if n >= 1)), (u"規則ごとの断った書類", od(acc[u"規則ごとの断った書類"]))])),
        (u"XJ0-3 型の外の fact", od([(u"fact", out_tot[KIND_NUM] + out_tot[KIND_TEXT]), (u"分母(対象の fact)", tgt[KIND_NUM] + tgt[KIND_TEXT])])),
        (u"XJ0-4 型の外の fact が 0 の書類", od([(u"書類", prod[u"型の外の fact が 0 の書類"]), (u"分母", prod[u"書類"])])),
        (u"XJ0-5 道具が読む fact が意味として同じ書類", od([(u"書類", z[u"比べ方 2"][u"fact が意味として同じ"]), (u"分母(受理した書類)", acc[u"受理した"])])),
        (u"XJ0-6 壊し方で断った file", od([(u"断った", s(u"断った")), (u"作れた", s(u"作れた")), (u"別の規則で断った", s(u"別の規則で断った")), (u"断らなかった", s(u"断らなかった"))])),
        (u"XJ0-7 壊し方でちょうど 1 つ", od([(u"ちょうど 1 つ", s(u"ちょうど 1 つ")), (u"分母(作れた)", s(u"作れた"))])),
        (u"XJ0-8 形は合っているが中身が違う file を通した", od([(u"通した", sum(v[u"通した"] for v in chg.values())), (u"作れた", sum(v[u"作れた"] for v in chg.values())), (u"断った(規則ごと)", qrules)])),
        (u"XJ0-9 辞書の無い _cor の接頭辞の科目の名", od([(u"名", cor[u"辞書の無い _cor の接頭辞"]), (u"分母(科目の名)", sum(cor.values()))])),
        (u"XJ0-10 期の表に無い期間の行が在る書類", od([(u"書類", prod[u"期の表に無い期間の行が在る書類"]), (u"分母", prod[u"書類"])]))])


# ======================================================================================================
# 記録
def check_tool(tool, runner=None, sha_reader=None, want_version=None, want_sha=None):
    M = prev().M
    return M.check_tool(tool, runner, sha_reader or M.sha256_file, want_version or M.TOOL_VERSION, want_sha or M.SHA_P)


def dev_docs(docs_dir, count=DEV_COUNT):
    return prev().M.dev_docs(docs_dir, count)


def script_sha():
    return prev().M.sha256_file(SCRIPT_PATH)


def assemble(per_doc, order_sha, info, dev_count=DEV_COUNT):
    M = prev().M
    tot = totals_of(per_doc, dev_count)
    rec = od()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"XJ0(入力の型(第 1 版)を字で決め、会社の AI に渡す指示書と、型どおりでない file を理由つきで断る受け口の検査を作る)(0 USD・engine は読まない)"
    rec[u"この script の sha256"] = script_sha()
    rec[u"材料"] = od([
        (u"書類の本数", len(per_doc)), (u"書類の file 名の並びの sha256", order_sha), (u"開発の 5 本の番号", list(range(1, dev_count + 1))),
        (u"標準ラベルの file の sha256", list(LAB_FILES.values())),
        (u"道具の版", info[u"版"]), (u"道具 P の ModelValue.py の sha256", info[u"ModelValue.py の sha256"]), (u"道具 P の package の一覧の sha256", info[u"package の一覧の sha256"]),
        (u"Python の版(道具 P)", info[u"Python の版"]), (u"規則の年", M.YEAR), (u"時間の上限(秒)", TIMEOUT_SEC)])
    rec[u"script の決めの字"] = od([
        (u"型の版", TYPE_VERSION), (u"規則の番号", list(RULE_ORDER)), (u"壊し方", list(BREAK_IDS)), (u"変え方", list(CHANGE_IDS)), (u"型の外の理由", list(REASONS)),
        (u"単位の形", [u"通貨:XXX", UNIT_SHARES, UNIT_PURE, u"通貨:XXX÷株", UNIT_OTHER + u"<分子>[÷<分母>]"]), (u"辞書の在る接頭辞", list(DICT_PREFIXES)), (u"format", FORMAT_OK), (u"桁あふれの守り", MAX_EXP)])
    rec[u"書類"] = per_doc
    rec[u"集計"] = tot
    rec[u"予測の判定に要る数(XJ0-1〜XJ0-10。当たり・外れは結果の文書で)"] = judged(tot)
    rec[u"限界"] = list(LIMITS)
    return rec


def build_record(tool_p, docs_dir=None, want=DOCS_WANT, runner=None, sha_reader=None, tmp_root=None, dev_count=DEV_COUNT, proc=None, cap=None, progress=None, keep=None, names_file=None, want_sha=None, want_version=None):
    u"""道具を確かめてから、書類を 1 本ずつ掛ける。(記録, secret)。書かない。"""
    pv = prev()
    M, B, T, W = pv.M, pv.B, pv.T, pv.W
    docs = W.select_docs(docs_dir or W.DOCS_DIR, want)
    info = check_tool(tool_p, runner, sha_reader, want_version, want_sha)
    names = load_names_file(names_file) if names_file else load_dictionary(default_dictionary_dir())
    per_doc = []
    elems, labels = set(), set()
    for n, (_stem, p, _xs) in enumerate(docs, 1):
        t0 = time.time()
        kdir = None
        if keep:
            kdir = os.path.join(keep, "doc%02d" % n)
            os.makedirs(kdir)
        r = process_doc(tool_p, p, tmp_root, runner, proc=proc, cap=cap, keep=kdir, names_file=names_file, names=names)
        per_doc.append(od([(u"番号", n)] + list(r.items())))
        el, lb = T.secret_of([B.load_package(p)])
        elems |= el
        labels |= lb
        if progress is not None:
            progress(u"doc %d/%d(%.0f 秒)" % (n, len(docs), time.time() - t0))
    ecodes = set()
    for _stem, _p, xs in docs:
        for x in xs:
            ecodes.update(re.findall(r"E\d{5}", x))
    secret = (labels, elems, [d[0] for d in docs], ecodes, set())
    return assemble(per_doc, W.order_sha256([d[0] for d in docs]), info, dev_count), secret


def verify_record(rec, text=None, want=DOCS_WANT, dev_count=DEV_COUNT):
    u"""記録の形・合計・禁止のものを検査する(道具は呼ばない・掛け直さない)。違えば止まる。"""
    M, W = prev().M, prev().W
    Stop = W.Stop
    docs = rec.get(u"書類")
    if not isinstance(docs, list) or len(docs) != want or rec[u"材料"][u"書類の本数"] != want:
        raise Stop(u"**記録の書類が 67 本でない。止める**")
    shape = list(zero_rec())
    for i, d in enumerate(docs, 1):
        if d.get(u"番号") != i or list(d)[1:] != shape:
            raise Stop(u"**記録の書類の形が違う。止める**")
        if d[u"断った"] != bool(d[u"断った段"]) or d[u"断った"] != bool(d[u"断った理由"]) or (d[u"断った"] and d[u"断った段"] not in STAGES):
            raise Stop(u"**断った書類の形が違う。止める**")
        a = d[u"受け口"]
        if a[u"受理した"] and a[u"断った"]:
            raise Stop(u"**受理した書類が断られてもいる。止める**")
        if a[u"断った"] != (a[u"断りの数"] >= 1) or sum(a[u"規則ごとの断りの数"].values()) != a[u"断りの数"] or any((n >= 1) != a[u"規則ごとの断った書類"][r] for r, n in a[u"規則ごとの断りの数"].items()):
            raise Stop(u"**受け口の数が合わない。止める**")
        if sum(a[u"規則と欄ごとの断りの数"].values()) != a[u"断りの数"]:
            raise Stop(u"**規則と欄ごとの断りの数が合わない。止める**")
        if d[u"断った"] and d[u"断った段"] != STAGES[0] and d[u"断った段"] != STAGES[1] and not a[u"受理した"]:
            raise Stop(u"**受け口を通っていない書類が後ろの段で断られている。止める**")
        if d[u"断った"] and (d[u"比べ方 2"][u"fact が意味として同じ"] or d[u"比べ方 2"][u"組めた"]):
            raise Stop(u"**断った書類に比べ方 2 の結果が在る。止める**")
        if not a[u"受理した"] and any(v[u"作れた"] for v in d[u"壊し方"].values()):
            raise Stop(u"**受理していない書類に壊し方が在る。止める**")
        o, t = d[u"型の外の fact"][u"合計"], d[u"型に入った fact"]
        for k in (KIND_NUM, KIND_TEXT):
            if o[k] + t[k] != d[u"対象の fact"][k]:
                raise Stop(u"**型に入った fact と型の外の fact の合計が対象の fact と合わない。止める**")
            if max(d[u"型の外の fact"][u"理由ごと"][r][k] for r in REASONS) > o[k]:
                raise Stop(u"**理由ごとの数が合計より多い。止める**")
        for k, v in d[u"壊し方"].items():
            if v[u"断った"] + v[u"別の規則で断った"] + v[u"断らなかった"] != v[u"作れた"] or v[u"ちょうど 1 つ"] > v[u"断った"]:
                raise Stop(u"**壊し方の数が合わない: %s。止める**" % k)
        for k, v in d[u"形は合っているが中身が違う"].items():
            if v[u"通した"] > v[u"作れた"] or (v[u"通した"] and any(v[u"断った"].values())) or (v[u"作れた"] and not v[u"通した"] and not any(v[u"断った"].values())):
                raise Stop(u"**変え方の数が合わない: %s。止める**" % k)
    tot = totals_of(docs, dev_count)
    if M.dumps(tot) != M.dumps(rec[u"集計"]) or M.dumps(judged(tot)) != M.dumps(rec[[k for k in rec if k.startswith(u"予測の判定に要る数")][0]]):
        raise Stop(u"**記録の合計が書類ごとの数と合わない。止める**")
    M.check_clean(rec, text if text is not None else M.dumps(rec))


def write_record(path, rec, secret=None):
    u"""書く前と書いた後に禁止のものを検査する。既に在れば止める(測り直さない)。便 XM0 の関数をそのまま呼ぶ。"""
    prev().M.write_record(path, rec, secret)


def run(tool_p, root=ROOT, docs=None, out=None, want=DOCS_WANT, runner=None, sha_reader=None, tmp_root=None, say=print, dev_count=DEV_COUNT, proc=None, cap=None, progress=None, keep=None, names_file=None, want_sha=None, want_version=None):
    rec, secret = build_record(tool_p, docs, want, runner, sha_reader, tmp_root, dev_count, proc, cap, progress, keep, names_file, want_sha, want_version)
    out = out or os.path.join(root, RECORD_REL)
    write_record(out, rec, secret)
    say(u"-> %s(書類 %d)" % (os.path.basename(out), rec[u"材料"][u"書類の本数"]))
    return rec


def check(root=ROOT, rec_path=None, say=print, want=DOCS_WANT, dev_count=DEV_COUNT):
    u"""記録の形・合計・禁止のものを検査する。置き場も道具も読まない。"""
    Stop = prev().W.Stop
    p = rec_path or os.path.join(root, RECORD_REL)
    if not os.path.isfile(p):
        raise Stop(u"**在る記録が無い。止める**")
    with io.open(p, encoding="utf-8") as fh:
        text = fh.read()
    rec = json.loads(text, object_pairs_hook=od)
    verify_record(rec, text, want, dev_count)
    say(u"--check: 記録の形・合計・禁止のものの検査は通った(書類 %d)" % len(rec[u"書類"]))
    return rec


def dev_run(tool_p, docs_dir=None, runner=None, tmp_root=None, say=print, proc=None, cap=None, keep=None, names_file=None, want_sha=None, want_version=None):
    u"""開発の 5 本だけ(記録は書かない)。(書類ごとの数の並び)。"""
    W = prev().W
    docs = dev_docs(docs_dir or W.DOCS_DIR, DEV_COUNT)
    check_tool(tool_p, runner, None, want_version, want_sha)
    names = load_names_file(names_file) if names_file else load_dictionary(default_dictionary_dir())
    per = []
    t_all = time.time()
    for n, (_s, p, _x) in enumerate(docs, 1):
        t0 = time.time()
        kdir = None
        if keep:
            kdir = os.path.join(keep, "doc%02d" % n)
            os.makedirs(kdir)
        r = process_doc(tool_p, p, tmp_root, runner, proc=proc, cap=cap, keep=kdir, names_file=names_file, names=names)
        per.append(od([(u"番号", n)] + list(r.items())))
        say(u"doc %d(%.0f 秒): %s" % (n, time.time() - t0, json.dumps(r, ensure_ascii=False)))
    say(u"開発の 5 本の合計: %.0f 秒" % (time.time() - t_all))
    say(json.dumps(group_totals(per), ensure_ascii=False, indent=1))
    return per


# ======================================================================================================
# 指示書(会社の AI に渡す文書。規則の番号と「断る時」の字は ``RULES`` から書き出す)
#: 指示書の作り物の例の辞書(門が持つ作り物の辞書と同じ名)。実在の名ではない。
EXAMPLE_NAMES = frozenset(["jppfs_cor_ExampleAssets", "jppfs_cor_ExampleReceivable", "jpcrp_cor_ExampleShares", "jpcrp_cor_ExampleText"])
EX_PREFIX = "example-prefix_E00000-000"


def example_ok():
    u"""受理される作り物の file の object。"""
    cur = od([(u"始まり", u"2030-04-01"), (u"終わり", u"2031-03-31")])

    def num(name, per, target, dims, value, unit, shift, prec):
        return od([(u"種類", KIND_NUM), (u"科目", name), (u"期間", per), (u"対象", target), (u"次元", dims), (u"値", value), (u"単位", unit), (u"表示の位", shift), (u"精度", prec)])
    return od([
        (u"型の版", TYPE_VERSION),
        (u"書類", od([(u"提出者の識別子", u"E00000-000"), (u"識別子の scheme", u"http://example.org/id"), (u"当期の始まり", u"2030-04-01"), (u"当期の終わり", u"2031-03-31"), (u"提出日", u"2031-06-30")])),
        (u"独自の名", [od([(u"種類", u"member"), (u"名", EX_PREFIX + u":ExampleSegmentMember")]), od([(u"種類", u"科目"), (u"名", EX_PREFIX + u":ExampleCustomItem")]),
                       od([(u"種類", u"軸"), (u"名", EX_PREFIX + u":ExampleSegmentAxis")])]),
        (u"行", [
            num(u"jppfs_cor:ExampleAssets", od([(u"時点", u"2031-03-31")]), TARGET_DEF, [], u"1234000", u"通貨:JPY", 3, -3),
            num(u"jppfs_cor:ExampleAssets", od([(u"時点", u"2030-03-31")]), TARGET_DEF, [], u"987000", u"通貨:JPY", 3, -3),
            num(u"jpcrp_cor:ExampleShares", od([(u"時点", u"2031-03-31")]), TARGET_DEF, [], u"1000", UNIT_SHARES, 0, 0),
            num(EX_PREFIX + u":ExampleCustomItem", cur, TARGET_IND, [[EX_PREFIX + u":ExampleSegmentAxis", EX_PREFIX + u":ExampleSegmentMember"]], u"12.5", u"通貨:JPY÷株", 0, 1),
            num(u"jppfs_cor:ExampleReceivable", od([(u"時点", u"2031-03-31")]), TARGET_DEF, [], VALUE_NONE, u"通貨:JPY", None, None),
            od([(u"種類", KIND_TEXT), (u"科目", u"jpcrp_cor:ExampleText"), (u"期間", cur), (u"対象", TARGET_DEF), (u"次元", [])])])])


def example_bad():
    u"""断られる作り物の file の object(例 1 から 4 か所だけ変えた)。"""
    o = example_ok()
    o[u"行"][0][u"科目"] = u"jppfs_cor:ExampleAssetz"
    o[u"行"][1][u"値"] = u"987,000"
    o[u"行"][2][u"精度"] = u"0"
    o[u"独自の名"] = [e for e in o[u"独自の名"] if e[u"名"] != EX_PREFIX + u":ExampleCustomItem"]
    return o


def fence(text, lang=u"json"):
    return [u"```" + lang] + text.rstrip(u"\n").split(u"\n") + [u"```"]


def instruction_text():
    u"""指示書の字。``--write-instruction`` が書き出す字そのもの(門が file と同じかを見る)。"""
    L = []
    add = L.append
    add(u"# 入力の型(第 1 版)の指示書")
    add(u"")
    add(u"この文書は、会社の AI が「型の file」を書くための決めである。型の file を書くのは会社の AI、受け口の検査は型どおりかだけを見て、型どおりでなければ理由を付けて断る。")
    add(u"受け口は推さない・補わない。書かれていない所を機械が埋めることはしない。断られたら、断りの `行`・`欄`・`規則` が指す所だけを直して、もう一度出す。")
    add(u"")
    add(u"## 1. 書くもの")
    add(u"")
    add(u"- 型の file は JSON 1 つ(UTF-8)。頂は object で、鍵は `型の版`・`書類`・`独自の名`・`行` の 4 つだけ。同じ鍵を 2 回書かない(どの object でも)。")
    add(u"- `型の版` は字 `1`(数の 1 ではない)。")
    add(u"- 数は字で書く(`値`)。JSON の数にしない。表示の位・精度だけが整数。")
    add(u"- 書かないと決めた所を機械が推すことはない。必要な欄は全部書く。")
    add(u"")
    add(u"## 2. `書類`")
    add(u"")
    add(u"- 鍵は `提出者の識別子`・`識別子の scheme`・`当期の始まり`・`当期の終わり`・`提出日` の 5 つだけ。")
    add(u"- こう書く: 日は `YYYY-MM-DD`(半角・在る日)。`当期の始まり` は `当期の終わり` と同じかそれより前。`提出日` は `当期の終わり` と同じかそれより後。`提出者の識別子`・`識別子の scheme` は空白を含まない 1 字以上の字。")
    add(u"- こう書かない: 月を 13 にする・`2031/03/31` と書く・`提出日` を期末より前にする・識別子を空にする・5 つの鍵に別の鍵を足す。")
    add(u"- 断られた時の直し方: 規則 D1(鍵の数か日の形)・D2(始まりが終わりより後)・D3(提出日が期末より前)・D4(識別子)の `欄` の鍵を直す。")
    add(u"")
    add(u"## 3. `独自の名`")
    add(u"")
    add(u"- 行で使う提出者別の名(接頭辞が `_cor` で終わらない名)の全部を、1 回ずつ並びで書く。要素は `種類`(`科目`・`軸`・`member` のどれか)と `名` の 2 つの鍵だけの object。")
    add(u"- 並びは (種類, 名) の字(コードポイント)の昇順。`member` が先、次に `科目`、最後に `軸`。")
    add(u"- こう書く: 行の `科目`・`次元` に出てくる提出者別の名を、その種類で 1 つずつ。")
    add(u"- こう書かない: 行で使わない名・接頭辞が `_cor` で終わる名・同じ (種類, 名) の 2 回目・昇順でない並び。")
    add(u"- 断られた時の直し方: 規則 N3(行で使った提出者別の名が並びに無い)は並びにその (種類, 名) を足す。規則 N4(余計な名・重なり・並びの順)は余りを消して昇順に直す。")
    add(u"")
    add(u"## 4. `行`")
    add(u"")
    add(u"- 1 つ以上の並び。1 行 = 1 つの数か 1 つの文。要素は object。`種類` が `数` なら鍵は `種類`・`科目`・`期間`・`対象`・`次元`・`値`・`単位`・`表示の位`・`精度` の 9 つだけ。`種類` が `文` なら `種類`・`科目`・`期間`・`対象`・`次元` の 5 つだけ(`値` などを足さない)。")
    add(u"- 同じ (種類・科目・期間・対象・次元) の行を 2 つ書かない。1 つの科目を、時点の行と期間の行の両方に書かない。1 つの科目の数の行に単位を 2 通り書かない。1 つの科目を数の行と文の行の両方に書かない(規則 R10〜R13)。")
    add(u"- 断られた時の直し方: 規則 R1 は `欄` の鍵を過不足なく揃える。")
    add(u"")
    add(u"### 4-1. `科目`・名の字")
    add(u"")
    add(u"- こう書く: `<接頭辞>:<局所名>`。どちらも英数字と `_` と `-` だけ・1 字以上・`:` は 1 つ。接頭辞が `jppfs_cor`・`jpcrp_cor`・`jpigp_cor` の名は標準の辞書に在る名だけ。接頭辞が `_cor` で終わらない名は `独自の名` に書いた名だけ。")
    add(u"- こう書かない: `:` が無い名・辞書に無い名・`独自の名` に書いていない提出者別の名・軸の名を `Axis` で終えない・member の名を `Member` で終えない。")
    add(u"- 断られた時の直し方: 規則 N1(形)・N2(辞書に無い)・N3(独自の名に無い)・N5(軸・member の終わりの字)の `行`・`欄` の名を直す。")
    add(u"")
    add(u"### 4-2. `期間`")
    add(u"")
    add(u"- こう書く: 時点なら `{\"時点\": \"YYYY-MM-DD\"}`。期間なら `{\"始まり\": \"YYYY-MM-DD\", \"終わり\": \"YYYY-MM-DD\"}`。期の表に在るかどうかは問わない。`始まり` は `終わり` と同じかそれより前。")
    add(u"- こう書かない: `時点` と `始まり` を一緒に書く・`始まり` を `終わり` より後にする・`/` で区切る。")
    add(u"- 断られた時の直し方: 規則 R2 の `行` の `期間` を直す。")
    add(u"")
    add(u"### 4-3. `対象`")
    add(u"")
    add(u"- こう書く: `個別` か `既定`。個別の財務諸表の数なら `個別`、それ以外は `既定`(`既定` は連結とは限らない)。")
    add(u"- こう書かない: `連結` など別の字。")
    add(u"- 断られた時の直し方: 規則 R3 の `行` の `対象` を `個別` か `既定` に直す。")
    add(u"")
    add(u"### 4-4. `次元`")
    add(u"")
    add(u"- こう書く: 並び(空でもよい)。要素は `[軸の名, member の名]` の 2 つの字の並び。軸の名の字の昇順。同じ軸を 2 回書かない。")
    add(u"- こう書かない: 個別の軸 `jppfs_cor:ConsolidatedOrNonConsolidatedAxis` を書く(個別かどうかは `対象` に書く)・順を逆にする。")
    add(u"- 断られた時の直し方: 規則 R4 の `行` の `次元` を直す。")
    add(u"")
    add(u"### 4-5. `値`(`数` の行)")
    add(u"")
    add(u"- こう書く: `無い`(空の数)か、符号つきの本当の大きさの 10 進の字。形は `-?(0|[1-9][0-9]*)(\\.[0-9]*[1-9])?`(半角。頭に余計な 0 を付けない・小数の末尾に 0 を付けない・`,` を入れない・`+` を付けない)。負の印の付いた 0 は `-0`。")
    add(u"- こう書かない: `1,234`・`+5`・`5.0`・全角の数字・JSON の数。")
    add(u"- 断られた時の直し方: 規則 R5 の `行` の `値` を上の形の字に直す。")
    add(u"")
    add(u"### 4-6. `単位`(`数` の行)")
    add(u"")
    add(u"- こう書く: `通貨:XXX`(XXX は英大文字 3 つ。例 `通貨:JPY`)・`株`・`純数`・`通貨:XXX÷株` のどれか。この 4 つの形に当たらない単位だけ `他:<分子>` か `他:<分子>÷<分母>`(分子・分母は measure の名を字の昇順に `*` でつないだ字)。")
    add(u"- こう書かない: `円`・`通貨:jpy`・4 つの形に当たる単位を `他:` で書く(例 `他:xbrli:pure`)。")
    add(u"- 断られた時の直し方: 規則 R6 の `行` の `単位` を直す。")
    add(u"")
    add(u"### 4-7. `表示の位`・`精度`(`数` の行)")
    add(u"")
    add(u"- こう書く: `値` が在れば 2 つとも整数(大きさは 1000 以下)。`値` が `無い` なら 2 つとも `null`。精度 + 表示の位 は 0 以上。`値` は 10 の(−精度)乗の倍数(例: 精度が −3 なら千の倍数)。")
    add(u"- `表示の位` は、書類に載せる数の字が、`値` を 10 の何乗で割った字かを表す整数(数の字の書き方)。例: `値` が `1234000` で書類には `1,234`(千単位)と載せるなら `3`・`値` をそのまま載せるなら `0`。")
    add(u"- `精度` は、`値` が 10 の何乗の位まで確かな字かを表す整数。例: 千の位まで確かな `1234000` は `-3`・一の位まで確かな `42` は `0`・小数第 2 位まで確かな `12.34` は `2`。")
    add(u"- こう書かない: 字の `\"0\"`・真偽・小数・`値` が在るのに `null`・`値` が `無い` のに数。")
    add(u"- 断られた時の直し方: 規則 R7(整数・null)・R8(精度 + 表示の位)・R9(倍数)の `行` の `欄` を直す。")
    add(u"")
    add(u"## 5. 受け口の検査の規則")
    add(u"")
    add(u"断りは 1 つずつ `行`(1 から数えた行の番号。行でない所は `null`)・`欄`・`規則`・`理由` で返す。全部の規則を掛け、当たった全部を返す(最初の 1 つで止めない。ただし S1・S2 に当たったら、ほかの規則は掛けない)。")
    add(u"")
    add(u"| 規則 | 見る所 | 断る時 |")
    add(u"|---|---|---|")
    for rid, place, conds in RULES:
        add(u"| %s | %s | %s |" % (rid, place, u"・".join(conds)))
    add(u"")
    add(u"- 行の欄が形として読めない時(R1〜R7 のどれかに当たった行)は、その行を R8〜R13 に掛けない。")
    add(u"- 辞書の無い `_cor` の接頭辞(例 `jpdei_cor`)の名は、形(N1)だけを見て通す。")
    add(u"")
    add(u"## 6. 断りの返り方")
    add(u"")
    add(u"受理なら `{\"受理\": true, \"断り\": []}`。断りなら `受理` が `false` で、`断り` に上の 4 つの鍵の object が並ぶ。`理由` は上の表の「断る時」の 1 つ。")
    add(u"")
    add(u"## 7. 作り物の例")
    add(u"")
    add(u"例の名は作り物(作り物の辞書に `jppfs_cor_ExampleAssets`・`jppfs_cor_ExampleReceivable`・`jpcrp_cor_ExampleShares`・`jpcrp_cor_ExampleText` が在るものとする)。実在の会社・書類の字ではない。")
    add(u"")
    add(u"### 7-1. 受理される file")
    add(u"")
    L.extend(fence(dump_text(example_ok())))
    add(u"")
    add(u"### 7-2. 断られる file と断りの並び")
    add(u"")
    add(u"7-1 から 4 か所だけ変えた(1 行目の科目の名を辞書に無い名に・2 行目の値に `,` を入れ・3 行目の精度を字にし・`独自の名` から使っている名を 1 つ取った)。")
    add(u"")
    bad = dump_text(example_bad())
    L.extend(fence(bad))
    add(u"")
    add(u"断りの並び:")
    add(u"")
    L.extend(fence(json.dumps(result_of(check_text(bad, EXAMPLE_NAMES)), ensure_ascii=False, indent=1)))
    add(u"")
    return u"\n".join(L)


def write_instruction(path=None):
    path = path or os.path.join(ROOT, INSTRUCTION_REL)
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(instruction_text())
    return path


# ======================================================================================================
# 入口
def run_make(folder, zip_path):
    u"""起こす命令(答えを読む)。``folder`` は無いか空であること。"""
    if os.path.isdir(folder) and os.listdir(folder):
        raise prev().W.Stop(u"**folder が空でない。止める**")
    if os.path.isdir(folder):
        os.rmdir(folder)
    derive_v1(prev().B.load_package(zip_path), folder)


def run_break(folder, names_file=None, say=print):
    u"""``--break``: folder の型の file から壊し方・変え方を作って受け口に掛け、数を JSON で出す。"""
    with io.open(os.path.join(folder, "type", "type.json"), encoding="utf-8") as fh:
        text = fh.read()
    names = load_names_file(names_file) if names_file else load_dictionary(default_dictionary_dir())
    work = tempfile.mkdtemp(prefix="xj0_break_")
    try:
        brk, chg = run_variants(text, names, work, work, None, names_file)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    say(json.dumps(od([(u"壊し方", brk), (u"形は合っているが中身が違う", chg)]), ensure_ascii=False, indent=1))
    return brk, chg


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in ("--accept", "--accept-dir"):
        sys.exit(accept_main(argv))
    if argv and argv[0] == "--build":
        sys.exit(build_main(argv))
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--make", default=None, metavar="FOLDER", help="起こす命令(--zip と一緒に)")
    ap.add_argument("--zip", default=None)
    ap.add_argument("--break", dest="break_", default=None, metavar="FOLDER", help="壊し方 44 通りと変え方 6 通りを受け口に掛ける")
    ap.add_argument("--names-file", default=None, help="作り物の辞書(JSON の字の並び)。既定は標準ラベルの file")
    ap.add_argument("--run", action="store_true", help="本番(67 本)。記録を排他で書く")
    ap.add_argument("--dev", action="store_true", help="開発の 5 本だけ。記録は書かない")
    ap.add_argument("--check", action="store_true", help="記録の形・合計・禁止のものを検査する。道具は呼ばない")
    ap.add_argument("--write-instruction", nargs="?", const="", default=None, metavar="PATH")
    ap.add_argument("--tool-p", default=None, help="道具 P(1 行の直し)の venv の場所")
    ap.add_argument("--keep", default=None, help="書類ごとの folder を残す場所(空の場所)")
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--docs", default=None, help="書類の置き場(既定は封の字)")
    a = ap.parse_args(argv)
    if a.write_instruction is not None:
        print(write_instruction(a.write_instruction or None))
        return
    if a.check:
        check(root=a.root)
        return
    if a.make:
        if not a.zip:
            raise prev().W.Stop(u"**--zip が要る。止める**")
        run_make(a.make, a.zip)
        return
    if a.break_:
        run_break(a.break_, a.names_file)
        return
    if not (a.run or a.dev):
        ap.print_usage()
        return
    Stop = prev().W.Stop
    if not a.tool_p:
        raise Stop(u"**--tool-p が要る。止める**")
    if a.keep:
        os.makedirs(a.keep, exist_ok=True)
        if os.listdir(a.keep):
            raise Stop(u"**--keep の場所が空でない。止める**")
    if a.dev:
        dev_run(a.tool_p, docs_dir=a.docs, keep=a.keep, names_file=a.names_file)
        return
    run(a.tool_p, root=a.root, docs=a.docs, progress=lambda s: print(s, file=sys.stderr), keep=a.keep, names_file=a.names_file)


if __name__ == "__main__":
    main()
