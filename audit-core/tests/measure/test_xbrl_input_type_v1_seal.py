# -*- coding: utf-8 -*-
u"""封 docs/XBRL_INPUT_TYPE_V1_SEAL_2026-11-23.md(XJ0 ― 入力の型(第 1 版)を字で決め、会社の AI に渡す指示書と、型どおりでない file を理由つきで断る受け口の検査を作る)の封の門。

**この門は置き場も道具も標準の辞書の file も読まない**(書類の置き場 ``~/.cache/audit-core/edinet/``・道具の venv・``~/.cache/audit-core/edinet-taxonomy/`` は 1 度も開かない)。通信しない。
作り物の辞書(``NAMES``。門が持つ)・作り物の型の file(``BASE``)・作り物の書類(便 XM0 の封の門の部品を importlib で読んで使う)に、本物の関数を掛ける。
subprocess を呼ぶのは git と、受け口の検査・型から作る命令(``python3 -I <script> --accept ...``・``--build ...``)を作り物の folder に掛ける所だけ。

**この門が縛るもの**

1. 封の字: 封の commit(8f3ec76b)・封の file が commit した blob と同じ・規則の表 24 行(番号・見る所・「断る時」を ``・`` で分けた 1 つずつ)・壊し方 44・変え方 6・予測の境 XJ0-1〜XJ0-10・限界 5 行・標準の辞書の sha256 3 つ・型の欄が、script の定数と同じ。
2. engine は読まない・封の commit から 0 行。境界の門の import 一覧にこの便の名前を足していない。
3. **規則ごと・「断る時」の ``・`` の 1 つずつに「破れば断る・破らなければ断らない」**(断りの行・欄・規則・理由まで)。S1・S2 に当たった時にほかを掛けない・R1〜R7 に当たった行を R8〜R13 に掛けない・R10〜R13 の「どの行を断るか」(少ない側・同じ数・後ろの行)・N2 の辞書の在る接頭辞 3 つ・N3 の種類の取り違え・R5 の形・R7 の型・R9 の桁(負の精度・巨大な数)。
4. 壊し方 44 通りと変え方 6 通りを 1 つずつ(狙った所だけが変わる・狙った組・断りの並びが手の値と同じ・変え方は型の規則を破らない)。判定(作れた・断った・ちょうど 1 つ・別の規則で断った・断らなかった・通した)を手の値と照らす。
5. 受け口の検査は壊れた入力(空の file・JSON でない字・頂が並び・深い入れ子・巨大な数・鍵が字でない形・行 0・``独自の名`` が空・UTF-8 でない)で例外を出さず断りを返す。
6. **受け口の検査は標準の library だけで動き、前の便の script・元の包み・持ち込み・型の外を読まない**(AST・差し替え・``python3 -I`` の別 process。元の包み・持ち込みの答え・型の外が無い場所で動く。型から作る命令は元の包みが無い場所で動き、受け口が断った file からは作らない)。
7. 指示書の字が script の書き出しと同じ・指示書の例が字どおりに受理・断りになる。型の値を 1 つ変えると作った属性か定義が変わる(欄ごと)。期の名の後ろの形(``At…``・``From…To…``)・``他:`` の単位の ``U0001`` からの振り方。
8. 書類 1 本の通し(作り物の書類)・断り(起こす・受け口・型から作る・組む・道具)・数え方(§2)・記録の検査と禁止のもの・封 → script → 記録の commit の順(記録が無いときと在るときの両方で走る)。
9. 行頭の名前: この門は ``ENGINE_LATER``・``UNTOUCHED``・``PIN_DEF``・``LATER_ENGINE_COMMITS``・``FROZEN_LATER``・``ENGINE_TRANSITIONS`` を行頭に置かない。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``。script の字を 1 か所替えた版を memory の中に作る。file は書き換えない)。表は実行より先に書いた(予測 = 赤になるべき検査の名前)。
黙る変異は ``SILENT_BY_DESIGN`` に理由とともに置き、「黙ること」自体を別の試験で縛る。
"""
import ast
import builtins
import collections
import contextlib
import copy
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
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)


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


def load_source(src):
    u"""script の字(``src``)から module を memory の中に作る。file は読み書きしない。``__file__`` は本物の script。"""
    mod = types.ModuleType("xbrl_input_type_v1_mutant")
    mod.__file__ = os.path.join(ROOT, SCRIPT_REL)
    before = dict(sys.modules)
    try:
        exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    finally:
        for k, v in before.items():
            if sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


SEAL_REL = "docs/XBRL_INPUT_TYPE_V1_SEAL_2026-11-23.md"
SEAL_COMMIT_SHORT = "8f3ec76b"
SCRIPT_REL = "measure/xbrl_input_type_v1_2026-11-23.py"
GATE_REL = "tests/measure/test_xbrl_input_type_v1_seal.py"
RECORD_REL = "fixtures/xbrl/cd8/input_type_v1_2026-11-23.json"
INSTRUCTION_REL = "docs/INPUT_TYPE_V1_INSTRUCTION_2026-11-23.md"
MS = load_module(SCRIPT_REL, "xbrl_input_type_v1_script_for_seal_gate")
XG = load_module("tests/measure/test_xbrl_input_type_seal.py", "xj0_gate_helpers_from_xm0_gate")      # 作り物の書類・作り物の道具(便 XM0 の封の門)
PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_input_type_v1_seal")      # 順序・履歴の部品。門としては走らせない
X = XG.X
ORDER_FILES = (SCRIPT_REL, GATE_REL, INSTRUCTION_REL)          # 記録の順序は記録が在るときの結果の門に置く
od = collections.OrderedDict
JPY, SHARES, PURE, JPYPS = u"通貨:JPY", u"株", u"純数", u"通貨:JPY÷株"
NONE_V = u"無い"
CONS_AXIS, IND_MEMBER = u"jppfs_cor:ConsolidatedOrNonConsolidatedAxis", u"jppfs_cor:NonConsolidatedMember"
RULE_IDS = (u"S1", u"S2", u"D1", u"D2", u"D3", u"D4", u"N1", u"N2", u"N3", u"N4", u"N5", u"R1", u"R2", u"R3", u"R4", u"R5", u"R6", u"R7", u"R8", u"R9", u"R10", u"R11", u"R12", u"R13")


def read(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def sha_of(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def sha_or_none(rel):
    return sha_of(rel) if os.path.exists(os.path.join(ROOT, rel)) else None


def guard(fn, *a, **kw):
    u"""fn が例外(``SystemExit`` を含む)を投げたら、その例外の型の名前の字を返す。違いを見るための道具。"""
    try:
        return fn(*a, **kw)
    except BaseException as exc:                # noqa: BLE001
        return [u"例外: %s" % type(exc).__name__]


def stops(fn, *a, **kw):
    u"""fn が止まれば(``SystemExit``。``Stop`` を含む)True。"""
    try:
        fn(*a, **kw)
    except SystemExit:
        return True
    return False


class Temp(object):
    def __enter__(self):
        self.d = tempfile.mkdtemp(prefix="xj0_gate_")
        return self.d

    def __exit__(self, *a):
        shutil.rmtree(self.d, ignore_errors=True)


def wfile(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data if isinstance(data, bytes) else data.encode("utf-8"))


def rfile(path):
    with open(path, "rb") as fh:
        return fh.read()


# ======================================================================== 1. 封の字
def seal_text():
    return read(SEAL_REL)


def seal_table(seal, ident, parts):
    u"""封の表の行(``| <ident> | ... |``)の、``<ident>`` を除く ``parts - 1`` 個のセル(最後のセルは残りの字全部。セルの中に `` | `` が在っても割らない)。無ければ ``None``。"""
    rows = [ln for ln in seal.splitlines() if re.match(r"^\| %s \| " % re.escape(ident), ln)]
    if len(rows) != 1:
        return None
    body = rows[0][2:-2].split(u" | ", parts - 1)
    return tuple(body[1:])


#: 手で書いた封の規則の表(番号・見る所・「断る時」)。**script の表から作っていない。**
SEAL_RULES = od([
    ("S1", (u"file", u"JSON として読めない・頂が object でない・頂の鍵が 4 つちょうどでない・`型の版` が字 `1` でない・`行` が 1 つ以上の並びでない・`独自の名` が並びでない・`書類` が object でない")),
    ("S2", (u"file", u"どこかの object に同じ鍵が 2 回在る")),
    ("D1", (u"`書類`", u"鍵が 5 つちょうどでない・日が `YYYY-MM-DD` の形の在る日でない")), ("D2", (u"`書類`", u"`当期の始まり` が `当期の終わり` より後")),
    ("D3", (u"`書類`", u"`提出日` が `当期の終わり` より前")), ("D4", (u"`書類`", u"`提出者の識別子` か `識別子の scheme` が、空白を含まない 1 字以上の字でない")),
    ("N1", (u"名(科目・軸・member・`独自の名`)", u"`<接頭辞>:<局所名>` の形(どちらも英数字と `_` と `-` だけ・1 字以上・`:` は 1 つ)でない")),
    ("N2", (u"名", u"接頭辞が辞書の在る接頭辞なのに、辞書に無い")), ("N3", (u"名", u"接頭辞が `_cor` で終わらないのに、その種類で `独自の名` に無い")),
    ("N4", (u"`独自の名`", u"要素の鍵が 2 つちょうどでない・種類が 3 つのどれでもない・接頭辞が `_cor` で終わる名・どの行もその種類で使わない名・同じ (種類, 名) が 2 回・並びが昇順でない")),
    ("N5", (u"名", u"軸の名が `Axis` で終わらない・member の名が `Member` で終わらない")),
    ("R1", (u"行", u"行が object でない・`種類` が `数` でも `文` でもない・鍵がその種類の鍵ちょうどでない")),
    ("R2", (u"`期間`", u"鍵が `時点` だけ・`始まり` と `終わり` だけ、のどちらでもない・日が在る日の形でない・`始まり` が `終わり` より後")),
    ("R3", (u"`対象`", u"`個別` でも `既定` でもない")),
    ("R4", (u"`次元`", u"並びでない・要素が 2 つの字の並びでない・同じ軸が 2 回・軸の名の昇順でない・個別の軸(`jppfs_cor:ConsolidatedOrNonConsolidatedAxis`)が在る")),
    ("R5", (u"`値`", u"字でない・`無い` でも `-?(0|[1-9][0-9]*)(\\.[0-9]*[1-9])?` の形(半角。全体が合う)でもない")),
    ("R6", (u"`単位`", u"字でない・上の形のどれでもない・4 つの形に当たるのに `他:` で書いている")),
    ("R7", (u"`表示の位`・`精度`", u"値が在るのに整数でない(真偽・小数・字は整数でない)・大きさが 1000 を超える・値が `無い` なのに `null` でない")),
    ("R8", (u"`表示の位`・`精度`", u"精度 + 表示の位 が 0 より小さい")), ("R9", (u"`値`・`精度`", u"値が 10 の(−精度)乗の倍数でない")),
    ("R10", (u"行と行", u"(種類・科目・期間・対象・次元)の組が同じ行が 2 つ以上在る(後ろの行を断る)")),
    ("R11", (u"行と行", u"1 つの科目が、時点の行と期間の行の両方に在る(その科目の、数の少ない側の行を断る。同じ数なら期間の側)")),
    ("R12", (u"行と行", u"1 つの科目の数の行に、単位が 2 通り以上在る(その科目の、いちばん多い単位でない行を断る。同じ数なら字の昇順で先の単位を残す)")),
    ("R13", (u"行と行", u"1 つの科目が、数の行と文の行の両方に在る(その科目の、数の少ない側の行を断る。同じ数なら文の側)"))])
#: 手で数えた「断る時」の個数(``・`` で分けた 1 つずつ。括弧の中の ``・`` は 1 つに数える)
SEAL_COND_COUNT = {"S1": 7, "S2": 1, "D1": 2, "D2": 1, "D3": 1, "D4": 1, "N1": 1, "N2": 1, "N3": 1, "N4": 6, "N5": 2, "R1": 3, "R2": 3, "R3": 1, "R4": 5, "R5": 2, "R6": 3, "R7": 3,
                   "R8": 1, "R9": 1, "R10": 1, "R11": 1, "R12": 1, "R13": 1}
EXPECT_BOUNDS = od([("XJ0-1", (52, None, False)), ("XJ0-2", (None, 3, True)), ("XJ0-3", (None, u"0.2%", True)), ("XJ0-4", (None, 5, True)), ("XJ0-5", (u"受理した書類の全部", None, False)),
                    ("XJ0-6", (u"作れた file の全部", None, False)), ("XJ0-7", (u"85%", None, False)), ("XJ0-8", (u"95%", None, False)), ("XJ0-9", (u"4%", u"8%", False)), ("XJ0-10", (None, 3, True))])
SEAL_BOUND_TEXT = od([("XJ0-1", (u"起こした file を受け口の検査が受理する書類は 52 本以上。", u"51 本以下なら外れ")), ("XJ0-2", (u"起こした file を 1 本でも断った規則は 3 つ以下。", u"4 つ以上なら外れ")),
                      ("XJ0-3", (u"型の外の fact は、対象の fact の 0.2% 以下。", u"0.2% を超えたら外れ")), ("XJ0-4", (u"型の外の fact が 0 の書類は 5 本以下。", u"6 本以上なら外れ")),
                      ("XJ0-5", (u"受理した書類のうち、道具が読む fact が意味として同じ書類は、受理した書類の全部。", u"1 本でも違えば外れ")),
                      ("XJ0-6", (u"壊し方の全部で、作れた file は全部「断った」。", u"作れた file が 1 つでも「断った」にならなければ外れ")),
                      ("XJ0-7", (u"壊した file のうち「ちょうど 1 つ」は、作れた file の 85% 以上。", u"85% 未満なら外れ")),
                      ("XJ0-8", (u"形は合っているが中身が違う file は、作れたものの 95% 以上を受け口が通す。", u"95% 未満なら外れ")),
                      ("XJ0-9", (u"辞書の無い `_cor` の接頭辞の科目の名は、科目の名の 4% 以上 8% 未満。", u"範囲の外なら外れ")), ("XJ0-10", (u"期の表に無い期間の行が在る書類は 3 本以下。", u"4 本以上なら外れ"))])
LAB_SHAS = (u"bf56ea1585afe426b398a9053ec4de4dbeafc211a53675b5d6d19453e4e04bf4", u"df9c23764ec9a63cb65b5ef62e79a2907c590523797421442ea2a60e334cd684",
            u"d45c95cc634202973557f5ed935d747ba25e751b7386c5269fe3e7bdb2c82d09")
LAB_NAMES = (u"jppfs_2025-11-01_lab.xml", u"jpcrp_2025-11-01_lab.xml", u"jpigp_2025-11-01_lab.xml")
BREAK_IDS_HAND = (u"S1a", u"S1b", u"S2a", u"D1a", u"D1b", u"D2a", u"D3a", u"D4a", u"N1a", u"N2a", u"N3a", u"N4a", u"N4b", u"N5a", u"N5b", u"R1a", u"R1b", u"R1c", u"R2a", u"R2b", u"R2c", u"R3a",
                  u"R4a", u"R4b", u"R4c", u"R5a", u"R5b", u"R5c", u"R5d", u"R5e", u"R6a", u"R6b", u"R6c", u"R7a", u"R7b", u"R7c", u"R7d", u"R8a", u"R9a", u"R10a", u"R10b", u"R11a", u"R12a", u"R13a")
CHANGE_IDS_HAND = (u"Q1", u"Q2", u"Q3", u"Q4", u"Q5", u"Q6")
#: 封の字で留めた言い回し(型・指示書に要る字)。封の字に在る
SEAL_PHRASES = (u"頂は object で、鍵は次の 4 つだけ", u"字 `1`", u"鍵は `提出者の識別子`・`識別子の scheme`・`当期の始まり`・`当期の終わり`・`提出日` の 5 つだけ", u"日は `YYYY-MM-DD` の字",
                u"(種類, 名) の字の昇順", u"`種類` が `数` なら次の 9 つだけ、`文` なら 1.〜5. の 5 つだけ", u"`通貨:XXX`・`株`・`純数`・`通貨:XXX÷株` のどれか", u"他:<分子>", u"`他:<分子>÷<分母>`",
                u"4 つの形に当たる単位を `他:` で書かない", u"負の印つきの 0 は `-0`", u"`U0001` から", u"`At` + 日の数字 8 つ", u"`From` + 始まりの数字 8 つ + `To` + 終わりの数字 8 つ",
                u"行の欄が形として読めない時(R1〜R7 のどれかに当たった行)は、その行を R8〜R13 に掛けない", u"辞書の無い `_cor` の接頭辞(開発の 5 本では `jpdei_cor`)の名は、形(N1)だけを見て通す",
                u"最初の当てはまる所**(行は番号の昇順)", u"**変えた後も型の規則を 1 つも破らないように作る。**", u"**対応表は無い**")


def holds(b, x):
    lo, hi, hi_in = b
    ok = True
    if lo is not None:
        ok = ok and x >= lo
    if hi is not None:
        ok = ok and (x <= hi if hi_in else x < hi)
    return ok


def seal_problems(ms=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    out = []
    if ms.SEAL_COMMIT != SEAL_COMMIT_SHORT or ms.SEAL_REL != SEAL_REL or ms.SCRIPT_REL != SCRIPT_REL or ms.RECORD_REL != RECORD_REL or ms.INSTRUCTION_REL != INSTRUCTION_REL:
        out.append(u"封の commit・path・script・記録・指示書の path が門と違う")
    if tuple(r[0] for r in ms.RULES) != RULE_IDS or len(ms.RULES) != 24:
        out.append(u"規則の番号の並びが封と違う")
    for rid, place, conds in ms.RULES:
        want = SEAL_RULES.get(rid)
        got = seal_table(seal, rid, 3)
        if want is None or got is None or got != want:
            out.append(u"封の規則の行が手の字と違う(封の字が変わった): %s" % rid)
            continue
        if (place, u"・".join(conds)) != want:
            out.append(u"script の規則の表が封と違う: %s" % rid)
        if len(conds) != SEAL_COND_COUNT[rid]:
            out.append(u"「断る時」の個数が違う: %s" % rid)
    if tuple(ms.BREAK_IDS) != BREAK_IDS_HAND or tuple(ms.CHANGE_IDS) != CHANGE_IDS_HAND:
        out.append(u"壊し方・変え方の番号の並びが封と違う")
    for k, v in ms.BREAK_TEXT.items():
        got = seal_table(seal, k, 2)
        if got is None or got != (v,):
            out.append(u"壊し方の字が封と違う: %s" % k)
    for k, v in ms.CHANGE_TEXT.items():
        got = seal_table(seal, k, 2)
        if got is None or got != (v,):
            out.append(u"変え方の字が封と違う: %s" % k)
    if len(ms.BREAK_TEXT) != 44 or len(ms.CHANGE_TEXT) != 6:
        out.append(u"壊し方 44・変え方 6 の数が違う")
    if tuple(ms.LAB_FILES) != LAB_NAMES or tuple(ms.LAB_FILES.values()) != LAB_SHAS or tuple(ms.DICT_PREFIXES) != (u"jppfs_cor", u"jpcrp_cor", u"jpigp_cor"):
        out.append(u"標準の辞書の file・sha256・接頭辞が封と違う")
    for w in LAB_NAMES + LAB_SHAS:
        if w not in seal:
            out.append(u"封に標準の辞書の字が無い: %s" % w)
    if tuple(ms.TOP_KEYS) != (u"型の版", u"書類", u"独自の名", u"行") or tuple(ms.DOC_KEYS) != (u"提出者の識別子", u"識別子の scheme", u"当期の始まり", u"当期の終わり", u"提出日"):
        out.append(u"頂・書類の鍵が封と違う")
    if tuple(ms.NUM_KEYS) != (u"種類", u"科目", u"期間", u"対象", u"次元", u"値", u"単位", u"表示の位", u"精度") or tuple(ms.TEXT_KEYS) != (u"種類", u"科目", u"期間", u"対象", u"次元"):
        out.append(u"行の鍵が封と違う")
    if ms.TYPE_VERSION != u"1" or tuple(ms.NAME_KINDS) != (u"科目", u"軸", u"member") or tuple(ms.NAME_KEYS) != (u"種類", u"名") or ms.MAX_EXP != 1000:
        out.append(u"型の版・種類・鍵・1000 が封と違う")
    if (ms.KIND_NUM, ms.KIND_TEXT, ms.TARGET_IND, ms.TARGET_DEF, ms.VALUE_NONE, ms.UNIT_SHARES, ms.UNIT_PURE, ms.UNIT_OTHER, ms.UNIT_PER) != (u"数", u"文", u"個別", u"既定", u"無い", u"株", u"純数", u"他:", u"÷"):
        out.append(u"型の字(数・文・個別・既定・無い・株・純数・他:・÷)が封と違う")
    if ms.AXIS_CONS != CONS_AXIS[:] or ms.MEMBER_IND != IND_MEMBER:
        out.append(u"個別の軸・member が封と違う")
    if ms.VALUE_RE.pattern != r"-?(0|[1-9][0-9]*)(\.[0-9]*[1-9])?" or ms.NAME_RE.pattern != r"[A-Za-z0-9_\-]+:[A-Za-z0-9_\-]+" or ms.DATE_RE.pattern != r"[0-9]{4}-[0-9]{2}-[0-9]{2}":
        out.append(u"値・名・日の形が封と違う")
    for w in SEAL_PHRASES:
        if w not in seal:
            out.append(u"封に字が無い: %s" % w)
    if dict(ms.BOUNDS) != dict(EXPECT_BOUNDS):
        out.append(u"予測の境の数が門と違う")
    for k, (a, b) in SEAL_BOUND_TEXT.items():
        row_ = [ln for ln in seal.splitlines() if re.match(r"^\| %s(?!\d)" % re.escape(k), ln)]
        if len(row_) != 1 or a not in row_[0] or b not in row_[0]:
            out.append(u"封の予測の行の字が違う: %s" % k)
    cases = {"XJ0-1": [(52, True), (51, False), (62, True)], "XJ0-2": [(3, True), (4, False), (0, True)], "XJ0-4": [(5, True), (6, False)], "XJ0-10": [(3, True), (4, False)]}
    for k, cs in cases.items():
        for x, want in cs:
            if holds(ms.BOUNDS[k], x) != want:
                out.append(u"予測の境の読みが違う: %s %s" % (k, x))
    sec7 = seal.split(u"## §7", 1)[-1]
    lines7 = [ln[2:] for ln in sec7.splitlines() if ln.startswith(u"- ")]
    lines7 = [x.replace(u"`.xbrl` を落とした包み", u"拡張子 xbrl の file を落とした包み") for x in lines7]                   # 記録の禁止の字の検査が .xbrl を断るため 1 か所だけ言い換える(script の注に書いた)
    if len(lines7) != 5 or list(ms.LIMITS) != lines7:
        out.append(u"限界の 5 行が封 §7 と違う")
    if ms.STAGES != (u"起こす", u"受け口", u"型から作る", u"組む", u"道具") or ms.REASONS != ("a", "b", "c", "d", "e", "f", "g", "h"):
        out.append(u"断りの段・型の外の理由が封と違う")
    return out


def seal_history_problems(root=REPO):
    rc = subprocess.run(["git", "-C", root, "log", "--format=%H", "--", PREFIX + SEAL_REL], stdout=subprocess.PIPE, universal_newlines=True)
    hs = [x for x in rc.stdout.split() if x]
    if len(hs) != 1 or not hs[0].startswith(SEAL_COMMIT_SHORT):
        return [u"封の file の履歴が封 %s の 1 commit でない" % SEAL_COMMIT_SHORT]
    blob = subprocess.run(["git", "-C", root, "show", "%s:%s" % (hs[0], PREFIX + SEAL_REL)], stdout=subprocess.PIPE).stdout.decode("utf-8")
    if blob != seal_text():
        return [u"今の封が封の commit の blob と違う"]
    return []


def order_of(root=REPO, seal_short=SEAL_COMMIT_SHORT, others=None):
    u"""封 ⊏ script・この門・指示書(足した commit が封の後)。未 commit は赤。"""
    others = list(ORDER_FILES) if others is None else others
    return list(PR.order_problems(root, PREFIX, SEAL_REL, seal_short, [], others))


def engine_zero_problems(root=REPO):
    rc = subprocess.run(["git", "-C", root, "diff", "--name-only", SEAL_COMMIT_SHORT, "--", PREFIX + "adapters", PREFIX + "core"], stdout=subprocess.PIPE, universal_newlines=True)
    return [u"engine が封の後に変わっている: %s" % ln for ln in rc.stdout.splitlines() if ln.strip()]



# ======================================================================== 2. 作り物の辞書と作り物の型の file(手で書いた字。script の例を使わない)
NAMES = frozenset(["jppfs_cor_Assets", "jppfs_cor_Profit", "jppfs_cor_Equity", "jppfs_cor_Ratio", "jppfs_cor_EPS", "jppfs_cor_Receivable", "jppfs_cor_ConsolidatedOrNonConsolidatedAxis",
                   "jppfs_cor_NonConsolidatedMember", "jppfs_cor_ComponentsOfEquityAxis", "jppfs_cor_CapitalStockMember", "jpcrp_cor_Text", "jpigp_cor_Item"])
CA, CM = u"jppfs_cor:ComponentsOfEquityAxis", u"jppfs_cor:CapitalStockMember"
SA, SM, OWN = u"x_E1:SegAxis", u"x_E1:AMember", u"x_E1:Own"


def per_i(d):
    return od([(u"時点", d)])


def per_d(a, b):
    return od([(u"始まり", a), (u"終わり", b)])


def num(name, per, target, dims, value, unit, shift, prec):
    return od([(u"種類", u"数"), (u"科目", name), (u"期間", per), (u"対象", target), (u"次元", dims), (u"値", value), (u"単位", unit), (u"表示の位", shift), (u"精度", prec)])


def txt(name, per, target=u"既定", dims=None):
    return od([(u"種類", u"文"), (u"科目", name), (u"期間", per), (u"対象", target), (u"次元", dims or [])])


def doc_of(rows, custom=(), **kw):
    d = od([(u"提出者の識別子", u"E99999-000"), (u"識別子の scheme", u"http://example.org/id"), (u"当期の始まり", u"2030-04-01"), (u"当期の終わり", u"2031-03-31"), (u"提出日", u"2031-06-30")])
    d.update(kw)
    return od([(u"型の版", u"1"), (u"書類", d), (u"独自の名", [od([(u"種類", k), (u"名", n)]) for k, n in custom]), (u"行", list(rows))])


def base():
    u"""11 行の作り物の型の file(手で決めた値。近くの数と同じにしない)。"""
    return doc_of([
        num(u"jppfs_cor:Assets", per_i(u"2031-03-31"), u"既定", [], u"1234000", JPY, 3, -3),                                   # 1
        num(u"jppfs_cor:Assets", per_i(u"2030-03-31"), u"既定", [], u"-987000", JPY, 3, -3),                                  # 2
        num(u"jppfs_cor:Assets", per_i(u"2031-03-31"), u"個別", [], u"555000", JPY, 3, -3),                                   # 3
        num(u"jppfs_cor:Profit", per_d(u"2030-04-01", u"2031-03-31"), u"既定", [[CA, CM], [SA, SM]], u"0", JPY, 0, 0),         # 4
        num(u"jppfs_cor:Equity", per_i(u"2030-03-31"), u"既定", [], u"42", JPY, 0, 0),                                         # 5
        num(OWN, per_i(u"2031-03-31"), u"既定", [], u"3", SHARES, 0, 0),                                                      # 6
        num(u"jppfs_cor:Ratio", per_i(u"2031-03-31"), u"既定", [], u"0.25", PURE, 0, 2),                                      # 7
        num(u"jppfs_cor:EPS", per_d(u"2030-04-01", u"2031-03-31"), u"既定", [], u"12.34", JPYPS, 0, 2),                        # 8
        num(u"jppfs_cor:Receivable", per_i(u"2031-03-31"), u"既定", [], NONE_V, JPY, None, None),                              # 9
        txt(u"jpcrp_cor:Text", per_d(u"2030-04-01", u"2031-03-31")),                                                           # 10
        num(u"jpigp_cor:Item", per_i(u"2031-03-31"), u"既定", [], u"5", u"他:iso4217:USD÷iso4217:JPY", 0, 0)],                 # 11
        custom=[(u"member", SM), (u"科目", OWN), (u"軸", SA)])


def dump(o):
    return MS.dump_text(o)


def rr(ms, o, names=None):
    u"""型の file の object(か字)を受け口の関数に掛け、断りを [(規則, 「断る時」の番号, 行, 欄)] にする。"""
    text = o if isinstance(o, str) else dump(o)
    out = []
    for x in ms.check_text(text, NAMES if names is None else names):
        conds = ms.RULE_CONDS[x[u"規則"]]
        out.append((x[u"規則"], conds.index(x[u"理由"]), x[u"行"], x[u"欄"]))
    return out


def edit(fn, o=None):
    o = copy.deepcopy(o if o is not None else base())
    fn(o)
    return o


def row_of(o, i):
    return o[u"行"][i - 1]


def set_row(i, key, value):
    def f(o):
        o[u"行"][i - 1][key] = value
    return f


def del_row_key(i, key):
    def f(o):
        del o[u"行"][i - 1][key]
    return f


def set_doc(key, value):
    def f(o):
        o[u"書類"][key] = value
    return f


def set_top(key, value):
    def f(o):
        o[key] = value
    return f


def mini(rows, custom=(), **kw):
    return doc_of(rows, custom, **kw)


def sample_row(name=u"jppfs_cor:Assets", per=None, target=u"既定", dims=(), value=u"10", unit=JPY, shift=0, prec=0):
    return num(name, per or per_i(u"2031-03-31"), target, (list(dims) if isinstance(dims, tuple) else dims), value, unit, shift, prec)



# ======================================================================== 3. 規則ごと・「断る時」の 1 つずつ(破れば断る・破らなければ断らない)
def key_of(t):
    return (t[0], t[1], -1 if t[2] is None else t[2], t[3])


def same(a, b):
    return sorted(a, key=key_of) == sorted(b, key=key_of)


def rm_key(key):
    def f(o):
        del o[key]
    return f


def append_custom(entry):
    def f(o):
        o[u"独自の名"].append(entry)
    return f


def one(k, n):
    return od([(u"種類", k), (u"名", n)])


def rule_cases():
    u"""[(label, object か字, 手で決めた断りの並び [(規則, 「断る時」の番号, 行, 欄)])]。"""
    C = []
    add = lambda label, o, want: C.append((label, o, want))                                         # noqa: E731
    b = base()
    text = dump(b)
    # ---- 基本: 作り物の file は受理
    add(u"基本は受理", b, [])
    # ---- S1
    for label, t in ((u"空", u""), (u"{ だけ", u"{"), (u"NaN", u'{"型の版": NaN}'), (u"途中で切れた字", text[:-7]), (u"BOM つき", u"﻿" + text), (u"Infinity", u'{"a": [Infinity]}'), (u"単独の引用符", u"'a'")):
        add(u"S1-0 JSON として読めない: " + label, t, [("S1", 0, None, u"file")])
    for label, t in ((u"並び", u"[]"), (u"数", u"1"), (u"null", u"null"), (u"字", u'"x"'), (u"真偽", u"true")):
        add(u"S1-1 頂が object でない: " + label, t, [("S1", 1, None, u"file")])
    add(u"S1-2 頂の鍵が 5 つ", edit(set_top(u"備考", u"x")), [("S1", 2, None, u"file")])
    add(u"S1-2 鍵 独自の名 が無い(独自の名の欄の断りも付く)", edit(rm_key(u"独自の名")), [("S1", 2, None, u"file"), ("S1", 5, None, u"独自の名")])
    add(u"S1-2 鍵 書類 が無い", edit(rm_key(u"書類")), [("S1", 2, None, u"file"), ("S1", 6, None, u"書類")])
    add(u"S1-2 鍵 行 が無い", edit(rm_key(u"行")), [("S1", 2, None, u"file"), ("S1", 4, None, u"行")])
    add(u"S1-2 鍵 型の版 が無い", edit(rm_key(u"型の版")), [("S1", 2, None, u"file"), ("S1", 3, None, u"型の版")])
    add(u"S1-2 鍵が 4 つで名が違う", edit(lambda o: (o.pop(u"独自の名"), o.__setitem__(u"備考", []))), [("S1", 2, None, u"file"), ("S1", 5, None, u"独自の名")])
    for v in (u"2", 1, True, None, u"", [u"1"]):
        add(u"S1-3 型の版が字 1 でない: %r" % (v,), edit(set_top(u"型の版", v)), [("S1", 3, None, u"型の版")])
    for v in ([], u"x", {}, None, 0):
        add(u"S1-4 行が 1 つ以上の並びでない: %r" % (v,), edit(set_top(u"行", v)), [("S1", 4, None, u"行")])
    for v in ({}, u"x", None, 0):
        add(u"S1-5 独自の名が並びでない: %r" % (v,), edit(set_top(u"独自の名", v)), [("S1", 5, None, u"独自の名")])
    for v in ([], u"x", None, 0):
        add(u"S1-6 書類が object でない: %r" % (v,), edit(set_top(u"書類", v)), [("S1", 6, None, u"書類")])
    add(u"S1 に当たったらほかを掛けない(行が壊れていても S1 だけ)", edit(lambda o: (o.__setitem__(u"型の版", u"2"), row_of(o, 1).__setitem__(u"値", u"1,234"), o[u"書類"].__setitem__(u"提出日", u"x"))),
        [("S1", 3, None, u"型の版")])
    add(u"行が 1 つだけ・独自の名が空は受理", mini([sample_row()]), [])
    # ---- S2
    add(u"S2 頂に同じ鍵", u'{"型の版": "1",' + text[1:], [("S2", 0, None, u"file")])
    add(u"S2 書類に同じ鍵", text.replace(u'"提出日":', u'"提出日": "2031-06-30", "提出日":', 1), [("S2", 0, None, u"file")])
    add(u"S2 行に同じ鍵(行の中の別の誤りも見ない)", text.replace(u'"対象": "既定",', u'"対象": "既定", "対象": "連結",', 1), [("S2", 0, None, u"file")])
    add(u"S2 独自の名の要素に同じ鍵", text.replace(u'"名": "x_E1:AMember"', u'"名": "x_E1:AMember", "名": "x_E1:AMember"', 1), [("S2", 0, None, u"file")])
    add(u"S1 と S2 の両方(ほかは掛けない)", u'{"型の版": "0", "型の版": "0"}', [("S1", 2, None, u"file"), ("S1", 3, None, u"型の版"), ("S1", 4, None, u"行"), ("S1", 5, None, u"独自の名"),
                                                                                  ("S1", 6, None, u"書類"), ("S2", 0, None, u"file")])
    # ---- D
    add(u"D1-0 書類に鍵を足す", edit(set_doc(u"備考", u"x")), [("D1", 0, None, u"書類")])
    for k in DOC_KEYS_H:
        add(u"D1-0 書類から鍵を取る: " + k, edit(lambda o, k=k: o[u"書類"].pop(k)), [("D1", 0, None, u"書類")])
    for k in (u"当期の始まり", u"当期の終わり", u"提出日"):
        for v in (u"2031-13-31", u"2031-02-30", u"2031-3-31", u"２０３１-03-31", u"20310331", None, 5, u"", u" 2031-03-31", u"2031-03-31 ", u"0000-01-01", u"2031-00-10"):
            add(u"D1-1 日が形の在る日でない: %s %r" % (k, v), edit(set_doc(k, v)), [("D1", 1, None, k)])
    add(u"D1-1 閏日は在る日", edit(set_doc(u"提出日", u"2032-02-29")), [])
    add(u"D1-1 閏日でない 2 月 29 日", edit(set_doc(u"提出日", u"2031-02-29")), [("D1", 1, None, u"提出日")])
    add(u"D2-0 始まりが終わりより後", edit(set_doc(u"当期の始まり", u"2031-04-01")), [("D2", 0, None, u"当期の始まり")])
    add(u"D2 始まり = 終わりは受理", edit(set_doc(u"当期の始まり", u"2031-03-31")), [])
    add(u"D3-0 提出日が期末より前", edit(set_doc(u"提出日", u"2031-03-30")), [("D3", 0, None, u"提出日")])
    add(u"D3 提出日 = 期末は受理", edit(set_doc(u"提出日", u"2031-03-31")), [])
    add(u"D2 と D3 の両方", edit(lambda o: (o[u"書類"].__setitem__(u"当期の始まり", u"2031-04-01"), o[u"書類"].__setitem__(u"提出日", u"2031-03-30"))), [("D2", 0, None, u"当期の始まり"), ("D3", 0, None, u"提出日")])
    add(u"D1 の日が無効なら D2・D3 は掛けない", edit(lambda o: (o[u"書類"].__setitem__(u"当期の終わり", u"x"), o[u"書類"].__setitem__(u"当期の始まり", u"2040-01-01"), o[u"書類"].__setitem__(u"提出日", u"2000-01-01"))),
        [("D1", 1, None, u"当期の終わり")])
    for v in (u"", u"a b", u"a　b", u"a\tb", 5, None, u" ", [u"a"]):
        for k in (u"提出者の識別子", u"識別子の scheme"):
            add(u"D4-0 識別子が空白を含まない 1 字以上の字でない: %s %r" % (k, v), edit(set_doc(k, v)), [("D4", 0, None, k)])
    add(u"D4 両方悪い", edit(lambda o: (o[u"書類"].__setitem__(u"提出者の識別子", u""), o[u"書類"].__setitem__(u"識別子の scheme", u""))), [("D4", 0, None, u"提出者の識別子"), ("D4", 0, None, u"識別子の scheme")])
    add(u"D4 1 字の識別子は受理", edit(set_doc(u"提出者の識別子", u"x")), [])
    # ---- N
    for v in (u"jppfs_corEquity", u"a:b:c", u":x", u"x:", u"a b:c", u"ａ:b", u"a:ｂ", u"", 5, None, [u"a:b"], u"a:b\n", u"é:b", u"a:b.c", u"a/b:c"):
        add(u"N1-0 科目の形: %r" % (v,), edit(set_row(5, u"科目", v)), [("N1", 0, 5, u"科目")])
    add(u"N1-0 軸の名の形(`:` が無い)", edit(set_row(4, u"次元", [[u"Axis", CM], [SA, SM]])), [("N1", 0, 4, u"次元")])
    add(u"N1-0 member の名の形", edit(set_row(4, u"次元", [[CA, u"Member"], [SA, SM]])), [("N1", 0, 4, u"次元")])
    add(u"N1-0 独自の名の名の形", edit(lambda o: o[u"独自の名"].insert(1, one(u"科目", u"nocolon"))), [("N1", 0, None, u"独自の名")])
    add(u"N1-0 独自の名の名が字でない", edit(lambda o: o[u"独自の名"].insert(1, one(u"科目", 5))), [("N1", 0, None, u"独自の名")])
    for v in (u"jppfs_cor:Nope", u"jpcrp_cor:Nope", u"jpigp_cor:Nope"):
        add(u"N2-0 辞書に無い(辞書の在る接頭辞): " + v, mini([sample_row(name=v)]), [("N2", 0, 1, u"科目")])
    for v in (u"jppfs_cor:Assets", u"jpcrp_cor:Text", u"jpigp_cor:Item", u"jpdei_cor:Anything", u"jpdei_cor:Assets", u"zzz_cor:Whatever"):
        add(u"N2 辞書に在る・辞書の無い _cor の接頭辞は通す: " + v, mini([sample_row(name=v)]), [])
    add(u"N2 辞書の名は接頭辞ごと(別の接頭辞の名は通さない)", mini([sample_row(name=u"jpcrp_cor:Assets")]), [("N2", 0, 1, u"科目")])
    add(u"N2-0 軸の名", mini([sample_row(dims=[[u"jppfs_cor:NoAxis", CM]])]), [("N2", 0, 1, u"次元")])
    add(u"N2-0 member の名", mini([sample_row(dims=[[CA, u"jppfs_cor:NoMember"]])]), [("N2", 0, 1, u"次元")])
    add(u"N2 軸と member の両方", mini([sample_row(dims=[[u"jppfs_cor:NoAxis", u"jppfs_cor:NoMember"]])]), [("N2", 0, 1, u"次元"), ("N2", 0, 1, u"次元")])
    add(u"N2 独自の名の要素(辞書に在る名は N4 だけ)", mini([sample_row()], custom=[(u"科目", u"jppfs_cor:Assets")]), [("N4", 2, None, u"独自の名")])
    add(u"N2 独自の名の要素(辞書に無い名は N2 と N4)", mini([sample_row()], custom=[(u"科目", u"jppfs_cor:Nope")]), [("N2", 0, None, u"独自の名"), ("N4", 2, None, u"独自の名")])
    add(u"N3-0 独自の名に無い提出者別の科目", mini([sample_row(name=u"x_E1:Item")]), [("N3", 0, 1, u"科目")])
    add(u"N3 独自の名に在れば受理", mini([sample_row(name=u"x_E1:Item")], custom=[(u"科目", u"x_E1:Item")]), [])
    add(u"N3-0 軸が独自の名に無い", mini([sample_row(dims=[[SA, CM]])]), [("N3", 0, 1, u"次元")])
    add(u"N3-0 member が独自の名に無い", mini([sample_row(dims=[[CA, SM]])]), [("N3", 0, 1, u"次元")])
    add(u"N3-0 軸と member の両方が無い", mini([sample_row(dims=[[SA, SM]])]), [("N3", 0, 1, u"次元"), ("N3", 0, 1, u"次元")])
    add(u"N3 種類の取り違え(member で宣言した名を科目で使う)", mini([sample_row(name=u"x_E1:ItemMember")], custom=[(u"member", u"x_E1:ItemMember")]), [("N3", 0, 1, u"科目"), ("N4", 3, None, u"独自の名")])
    add(u"N3 種類の取り違え(科目で宣言した名を member で使う)", mini([sample_row(dims=[[CA, u"x_E1:OwnMember"]])], custom=[(u"科目", u"x_E1:OwnMember")]), [("N3", 0, 1, u"次元"), ("N4", 3, None, u"独自の名")])
    add(u"N3 同じ名を使う行ごとに断る", mini([sample_row(name=u"x_E1:Item"), sample_row(name=u"x_E1:Item", per=per_i(u"2031-03-30"))]), [("N3", 0, 1, u"科目"), ("N3", 0, 2, u"科目")])
    add(u"N4-0 要素に鍵が 3 つ(余計な要素)", edit(lambda o: o[u"独自の名"].append(od([(u"種類", u"軸"), (u"名", u"zz_a:BAxis"), (u"備考", u"x")]))), [("N4", 0, None, u"独自の名")])
    add(u"N4-0 使っている名の要素の鍵が 3 つ(宣言とみなさない。行の側の N3 も付く)", edit(lambda o: o[u"独自の名"][0].__setitem__(u"備考", u"x")), [("N3", 0, 4, u"次元"), ("N4", 0, None, u"独自の名")])
    add(u"N4-0 要素が object でない", edit(lambda o: o[u"独自の名"].append(5)), [("N4", 0, None, u"独自の名")])
    add(u"N4-0 要素に名が無い", edit(lambda o: o[u"独自の名"].append(od([(u"種類", u"軸"), (u"備考", u"x")]))), [("N4", 0, None, u"独自の名")])
    add(u"N4-1 種類が 3 つのどれでもない", edit(lambda o: o[u"独自の名"].append(one(u"x", u"zz_a:B"))), [("N4", 1, None, u"独自の名")])
    add(u"N4-1 種類が字でない", edit(lambda o: o[u"独自の名"].append(one(5, u"zz_a:B"))), [("N4", 1, None, u"独自の名")])
    add(u"N4-2 接頭辞が _cor で終わる名", edit(lambda o: o[u"独自の名"].insert(1, one(u"科目", u"jpdei_cor:Foo"))), [("N4", 2, None, u"独自の名")])
    add(u"N4-3 どの行も使わない名", edit(lambda o: o[u"独自の名"].insert(2, one(u"科目", u"zz_unused:Zz"))), [("N4", 3, None, u"独自の名")])
    add(u"N4-3 使う種類が違う(軸で宣言し科目でだけ使う)", edit(lambda o: o[u"独自の名"].insert(2, one(u"軸", OWN + u"Axis"))), [("N4", 3, None, u"独自の名")])
    add(u"N4-4 同じ (種類, 名) が 2 回", edit(lambda o: o[u"独自の名"].append(copy.deepcopy(o[u"独自の名"][-1]))), [("N4", 4, None, u"独自の名")])
    add(u"N4-5 頭の 2 つを入れ替える", edit(lambda o: o[u"独自の名"].insert(0, o[u"独自の名"].pop(1))), [("N4", 5, None, u"独自の名")])
    add(u"N4-5 全部逆順(逆転が 2 か所)", edit(lambda o: o[u"独自の名"].reverse()), [("N4", 5, None, u"独自の名"), ("N4", 5, None, u"独自の名")])
    add(u"N4 並びは種類の字の昇順(member < 科目 < 軸)で受理", base(), [])
    add(u"N5-0 軸の名が Axis で終わらない(行と独自の名)", edit(lambda o: (o[u"独自の名"].__setitem__(2, one(u"軸", SA + u"Z")), row_of(o, 4).__setitem__(u"次元", [[CA, CM], [SA + u"Z", SM]]))),
        [("N5", 0, 4, u"次元"), ("N5", 0, None, u"独自の名")])
    add(u"N5-1 member の名が Member で終わらない(行と独自の名)", edit(lambda o: (o[u"独自の名"].__setitem__(0, one(u"member", SM + u"Z")), row_of(o, 4).__setitem__(u"次元", [[CA, CM], [SA, SM + u"Z"]]))),
        [("N5", 1, 4, u"次元"), ("N5", 1, None, u"独自の名")])
    add(u"N5 科目の名は Axis・Member で終わってよい", mini([sample_row(name=u"x_E1:ItemAxis")], custom=[(u"科目", u"x_E1:ItemAxis")]), [])
    add(u"N5 標準の名の終わり(辞書に在る軸・member)", mini([sample_row(dims=[[CA, CM]])]), [])
    # ---- R1
    for v in (5, u"x", [], None, True):
        add(u"R1-0 行が object でない: %r" % (v,), edit(lambda o, v=v: o[u"行"].__setitem__(1, v)), [("R1", 0, 2, u"行")])
    for v in (u"x", None, [u"数"], 1, u"", {}):
        add(u"R1-1 種類が 数・文 でない: %r" % (v,), edit(set_row(2, u"種類", v)), [("R1", 1, 2, u"種類")])
    add(u"R1-1 種類の鍵が無い", edit(del_row_key(2, u"種類")), [("R1", 1, 2, u"種類")])
    add(u"R1-2 対象が無い", edit(del_row_key(2, u"対象")), [("R1", 2, 2, u"対象")])
    add(u"R1-2 鍵を足す", edit(set_row(2, u"備考", u"x")), [("R1", 2, 2, u"備考")])
    add(u"R1-2 文の行に値を足す", edit(set_row(10, u"値", NONE_V)), [("R1", 2, 10, u"値")])
    add(u"R1-2 文の行に精度を足す", edit(set_row(10, u"精度", 0)), [("R1", 2, 10, u"精度")])
    add(u"R1-2 数の行から精度を取る", edit(del_row_key(7, u"精度")), [("R1", 2, 7, u"精度")])
    add(u"R1-2 数の行から 2 つ取る(鍵ごとに 1 つ)", edit(lambda o: (o[u"行"][6].pop(u"値"), o[u"行"][6].pop(u"単位"))), [("R1", 2, 7, u"値"), ("R1", 2, 7, u"単位")])
    add(u"R1-2 取って足す", edit(lambda o: (o[u"行"][6].pop(u"値"), o[u"行"][6].__setitem__(u"備考", 1))), [("R1", 2, 7, u"値"), ("R1", 2, 7, u"備考")])
    add(u"R1 の行は R8〜R13 に掛けない(R10)", edit(lambda o: o[u"行"].append(od(list(copy.deepcopy(o[u"行"][0]).items()) + [(u"備考", u"x")]))), [("R1", 2, 12, u"備考")])
    # ---- R2
    for v in (od([(u"時点", u"2031-03-31"), (u"始まり", u"2031-03-31")]), od(), od([(u"始まり", u"2031-03-31")]), u"x", None, od([(u"時点", u"2031-03-31"), (u"x", 1)]), [u"2031-03-31"], od([(u"終わり", u"2031-03-31")])):
        add(u"R2-0 期間の鍵: %r" % (v,), edit(set_row(1, u"期間", v)), [("R2", 0, 1, u"期間")])
    for v in (u"2031/03/31", u"2031-02-30", 5, None, u"2031-3-31", u""):
        add(u"R2-1 時点が在る日の形でない: %r" % (v,), edit(set_row(1, u"期間", per_i(v))), [("R2", 1, 1, u"期間")])
    add(u"R2-1 始まりが在る日の形でない", edit(set_row(4, u"期間", per_d(u"2030-04-31", u"2031-03-31"))), [("R2", 1, 4, u"期間")])
    add(u"R2-1 終わりが在る日の形でない(始まりとの前後は見ない)", edit(set_row(4, u"期間", per_d(u"2030-04-01", u"x"))), [("R2", 1, 4, u"期間")])
    add(u"R2-2 始まりが終わりより後", edit(set_row(4, u"期間", per_d(u"2031-03-31", u"2030-04-01"))), [("R2", 2, 4, u"期間")])
    add(u"R2 始まり = 終わりは受理", mini([sample_row(per=per_d(u"2031-03-31", u"2031-03-31"))]), [])
    add(u"R2 閏日の時点は受理", mini([sample_row(per=per_i(u"2032-02-29"))]), [])
    add(u"R2 期の表に在るかは問わない(書類の期と関係ない日)", mini([sample_row(per=per_i(u"1999-01-05")), sample_row(name=u"jppfs_cor:Profit", per=per_d(u"1900-01-01", u"2999-12-31"))]), [])
    # ---- R3
    for v in (u"連結", None, 5, u"既定 ", u"", [u"既定"]):
        add(u"R3-0 対象: %r" % (v,), edit(set_row(1, u"対象", v)), [("R3", 0, 1, u"対象")])
    # ---- R4
    for v in (u"x", od(), None, 5):
        add(u"R4-0 次元が並びでない: %r" % (v,), mini([sample_row(dims=v)]), [("R4", 0, 1, u"次元")])
    for v in ([[u"a"]], [u"x"], [[1, u"b"]], [[u"a", u"b", u"c"]], [[u"a", 2]], [None], [[]], [od()]):
        add(u"R4-1 要素が 2 つの字の並びでない: %r" % (v,), mini([sample_row(dims=v)]), [("R4", 1, 1, u"次元")])
    add(u"R4-1 要素が 2 つ悪い(1 つずつ)", mini([sample_row(dims=[[u"a"], [u"b"]])]), [("R4", 1, 1, u"次元"), ("R4", 1, 1, u"次元")])
    add(u"R4-2 同じ軸が 2 回(member が違っても)", edit(set_row(4, u"次元", [[CA, CM], [CA, u"jppfs_cor:CapitalStockMember"], [SA, SM]])), [("R4", 2, 4, u"次元")])
    add(u"R4-2 同じ軸が 3 回(2 回目以降)", mini([sample_row(dims=[[CA, CM], [CA, CM], [CA, CM]])]), [("R4", 2, 1, u"次元"), ("R4", 2, 1, u"次元")])
    add(u"R4-3 軸の名の昇順でない", edit(set_row(4, u"次元", [[SA, SM], [CA, CM]])), [("R4", 3, 4, u"次元")])
    add(u"R4-4 個別の軸が在る(個別の member)", mini([sample_row(dims=[[CONS_AXIS, IND_MEMBER]])]), [("R4", 4, 1, u"次元")])
    add(u"R4-4 個別の軸が在る(ほかの member)", mini([sample_row(dims=[[CONS_AXIS, CM]])]), [("R4", 4, 1, u"次元")])
    add(u"R4-4 個別の軸が在る(昇順を保つ並びなら 1 つだけ)", mini([sample_row(dims=[[CA, CM], [CONS_AXIS, IND_MEMBER]])]), [("R4", 4, 1, u"次元")])
    add(u"R4-3・R4-4 個別の軸が先で昇順が崩れる", mini([sample_row(dims=[[CONS_AXIS, IND_MEMBER], [CA, CM]])]), [("R4", 3, 1, u"次元"), ("R4", 4, 1, u"次元")])
    add(u"R4 次元が 2 つの昇順は受理", base(), [])
    # ---- R5
    add(u"R5-0 値の型(整数)", edit(set_row(1, u"値", 5)), [("R5", 0, 1, u"値")])
    for v in (None, [], {}, True, 1.5, [u"1"]):
        add(u"R5-0 値の型: %r" % (v,), edit(set_row(1, u"値", v)), [("R5", 0, 1, u"値")])
    for v in (u"1,234", u"+5", u"5.0", u"05", u"-", u"", u".", u".5", u"5.", u"１２", u"1e3", u" 5", u"5\n", u"--5", u"0.10", u"-0.0", u"0x1", u"٣", u"00", u"-00", u"1 2", u"５", u"1_0", u"0.0",
              u"+0", u"1E3", u"∞", u"NaN", u"無", u"無い ", u"-無い"):
        add(u"R5-1 値の形: %r" % (v,), mini([sample_row(value=v, prec=5)]), [("R5", 1, 1, u"値")])
    for v in (u"0", u"-0", u"0.5", u"10", u"-12.34", u"1234567890123456789012345678901234567890", u"0.00001", u"100", u"-100000", u"90.00009", u"1.5"):
        add(u"R5 値の形は受理: %r" % (v,), mini([sample_row(value=v, prec=5)]), [])
    add(u"R5 無い は受理(表示の位・精度 null)", mini([sample_row(value=NONE_V, shift=None, prec=None)]), [])
    # ---- R6
    for v in (5, None, [u"通貨:JPY"], True):
        add(u"R6-0 単位が字でない: %r" % (v,), mini([sample_row(unit=v)]), [("R6", 0, 1, u"単位")])
    for v in (u"円", u"通貨:jpy", u"通貨:JP", u"通貨:JPYY", u"通貨:JPY÷", u"通貨:JPY÷株式", u"他:", u"他:a÷", u"他:÷a", u"他:a÷b÷c", u"他:b*a", u"他:a**b", u"他: a", u"他:a*", u"他:*a", u"yen", u"", u"通貨:", u"通貨:ＪＰＹ",
              u"通貨:JPY ", u"株式", u"純数 ", u"通貨:JPY÷株÷株", u"通貨：JPY", u"他:a b", u"他:a÷b c", u"他:a\tb"):
        add(u"R6-1 単位が形のどれでもない: %r" % (v,), mini([sample_row(unit=v)]), [("R6", 1, 1, u"単位")])
    for v in (u"他:xbrli:pure", u"他:xbrli:shares", u"他:iso4217:JPY", u"他:iso4217:JPY÷xbrli:shares", u"他:iso4217:USD÷xbrli:shares"):
        add(u"R6-2 4 つの形に当たるのに 他: で書く: %r" % (v,), mini([sample_row(unit=v)]), [("R6", 2, 1, u"単位")])
    for v in (u"他:iso4217:JPY*xbrli:pure", u"他:a*b÷c", u"他:iso4217:jpy", u"他:iso4217:USD÷iso4217:JPY", u"他:xbrli:shares÷xbrli:shares", u"他:iso4217:JPY÷iso4217:USD", u"株", u"純数", u"通貨:USD",
              u"通貨:USD÷株", u"他:xbrli:pure*xbrli:shares", u"他:iso4217:JP", u"他:iso4217:JPYY", u"他:iso4217:JPY÷xbrli:shares*xbrli:shares", u"他:a:b", u"他:a÷a"):
        add(u"R6 単位は受理: %r" % (v,), mini([sample_row(unit=v)]), [])
    # ---- R7
    for f in (u"表示の位", u"精度"):
        for v in (u"0", True, False, 1.5, None, [], {}, 1.0):
            add(u"R7-0 整数でない: %s %r" % (f, v), mini([sample_row(**{(u"shift" if f == u"表示の位" else u"prec"): v})]), [("R7", 0, 1, f)])
        for v in (1001, -1001, 10 ** 100):
            add(u"R7-1 大きさが 1000 を超える: %s %r" % (f, v), mini([sample_row(**{(u"shift" if f == u"表示の位" else u"prec"): v})]), [("R7", 1, 1, f)])
    add(u"R7 両方悪い(欄ごとに 1 つ)", mini([sample_row(shift=u"0", prec=True)]), [("R7", 0, 1, u"表示の位"), ("R7", 0, 1, u"精度")])
    add(u"R7 1000 は受理(精度 1000・位 −1000)", mini([sample_row(value=u"0", shift=-1000, prec=1000)]), [])
    add(u"R7 位 1000 は受理", mini([sample_row(shift=1000, prec=0)]), [])
    add(u"R7 −1000 は受理(精度 1000)", mini([sample_row(shift=-1000, prec=1000)]), [])
    add(u"R7 精度 −1000 位 1000 は受理(値 0)", mini([sample_row(value=u"0", shift=1000, prec=-1000)]), [])
    add(u"R7-2 無い なのに精度が数", mini([sample_row(value=NONE_V, shift=None, prec=0)]), [("R7", 2, 1, u"精度")])
    add(u"R7-2 無い なのに表示の位が数", mini([sample_row(value=NONE_V, shift=0, prec=None)]), [("R7", 2, 1, u"表示の位")])
    add(u"R7-2 無い なのに両方が数", mini([sample_row(value=NONE_V, shift=0, prec=0)]), [("R7", 2, 1, u"表示の位"), ("R7", 2, 1, u"精度")])
    add(u"R7 値が在るのに null(R7 だけ。R8・R9 は掛けない)", mini([sample_row(shift=None, prec=-5)]), [("R7", 0, 1, u"表示の位")])
    add(u"R7 値が 無い でも整数が在れば R7 だけ", mini([sample_row(value=NONE_V, shift=0, prec=u"x")]), [("R7", 2, 1, u"表示の位"), ("R7", 2, 1, u"精度")])
    # ---- R8
    add(u"R8-0 精度 + 表示の位 が −1", mini([sample_row(value=u"0", shift=0, prec=-1)]), [("R8", 0, 1, u"精度")])
    add(u"R8-0 位が負・精度が小さい", mini([sample_row(value=u"0", shift=-3, prec=2)]), [("R8", 0, 1, u"精度")])
    add(u"R8 精度 + 表示の位 = 0 は受理", mini([sample_row(value=u"7000", shift=3, prec=-3)]), [])
    add(u"R8 と R9 は別々に出る", mini([sample_row(value=u"1234000", shift=3, prec=-4)]), [("R8", 0, 1, u"精度"), ("R9", 0, 1, u"値")])
    # ---- R9(精度が負・0・正・巨大な桁)
    for value, prec, ok in ((u"1500", -3, False), (u"1000", -3, True), (u"-2000", -3, True), (u"0", -5, True), (u"-0", -5, True), (u"100", -2, True), (u"100", -3, False), (u"10", -1, True), (u"10", -2, False),
                            (u"0.001", 3, True), (u"0.0011", 3, False), (u"0.05", 1, False), (u"0.5", 1, True), (u"12.5", 0, False), (u"12", 0, True), (u"1.25", 1, False), (u"1.25", 2, True),
                            (u"-1500", -2, True), (u"-1500", -4, False), (u"1" + u"0" * 5000, -1000, True), (u"1" + u"0" * 5000 + u"5", -1000, False), (u"0." + u"0" * 400 + u"1", 401, True),
                            (u"0." + u"0" * 400 + u"1", 400, False), (u"5", 0, True), (u"5", -1, False), (u"50", -1, True), (u"-50", -1, True), (u"-50", -2, False)):
        shift = max(0, -prec)
        add(u"R9 値 %s 精度 %d" % (value if len(value) < 20 else value[:6] + u"…(%d 字)" % len(value), prec), mini([sample_row(value=value, shift=shift, prec=prec)]), [] if ok else [("R9", 0, 1, u"値")])
    # ---- R10
    add(u"R10-0 同じ組の行(後ろを断る)", edit(lambda o: o[u"行"].append(copy.deepcopy(o[u"行"][0]))), [("R10", 0, 12, u"行")])
    add(u"R10-0 値だけ違う写し(R9 を破らない)", edit(lambda o: o[u"行"].append(od(list(copy.deepcopy(o[u"行"][0]).items())[:5] + [(u"値", u"1235000")] + list(copy.deepcopy(o[u"行"][0]).items())[6:]))), [("R10", 0, 12, u"行")])
    add(u"R10 同じ組が 3 つ(2・3 番目を断る)", mini([sample_row(), sample_row(), sample_row()]), [("R10", 0, 2, u"行"), ("R10", 0, 3, u"行")])
    add(u"R10 先の行は断らない(間に別の行)", mini([sample_row(), sample_row(per=per_i(u"2031-03-30")), sample_row(value=u"20")]), [("R10", 0, 3, u"行")])
    add(u"R10 対象が違えば別の組", mini([sample_row(), sample_row(target=u"個別")]), [])
    add(u"R10 次元が違えば別の組", mini([sample_row(), sample_row(dims=[[CA, CM]])]), [])
    add(u"R10 科目が違えば別の組", mini([sample_row(name=u"jppfs_cor:Assets", per=per_i(u"2031-03-31")), sample_row(name=u"jppfs_cor:Profit", per=per_i(u"2031-03-31"))]), [])
    add(u"R10 種類が違えば別の組(数と文は R13)", mini([sample_row(), txt(u"jppfs_cor:Assets", per_i(u"2031-03-31"))]), [("R13", 0, 2, u"種類")])
    # ---- R11(少ない側・同じ数・後ろの行)
    I1, I2, I3 = per_i(u"2031-03-31"), per_i(u"2031-03-30"), per_i(u"2031-03-29")
    D1, D2, D3 = per_d(u"2030-04-01", u"2031-03-31"), per_d(u"2030-04-01", u"2031-03-30"), per_d(u"2030-04-01", u"2031-03-29")
    add(u"R11-0 時点 2・期間 1 → 期間を断る", mini([sample_row(per=I1), sample_row(per=I2), sample_row(per=D1)]), [("R11", 0, 3, u"期間")])
    add(u"R11-0 時点 1・期間 2 → 時点を断る", mini([sample_row(per=D1), sample_row(per=I1), sample_row(per=D2)]), [("R11", 0, 2, u"期間")])
    add(u"R11-0 同じ数(1 と 1)→ 期間の側を断る", mini([sample_row(per=I1), sample_row(per=D1)]), [("R11", 0, 2, u"期間")])
    add(u"R11-0 同じ数(期間が先の行でも期間の側)", mini([sample_row(per=D1), sample_row(per=I1)]), [("R11", 0, 1, u"期間")])
    add(u"R11-0 同じ数(2 と 2)→ 期間の 2 行", mini([sample_row(per=I1), sample_row(per=D1), sample_row(per=I2), sample_row(per=D2)]), [("R11", 0, 2, u"期間"), ("R11", 0, 4, u"期間")])
    add(u"R11-0 時点 3・期間 1(後ろの行でなく少ない側)", mini([sample_row(per=D1), sample_row(per=I1), sample_row(per=I2), sample_row(per=I3)]), [("R11", 0, 1, u"期間")])
    add(u"R11 科目が違えば別(時点と期間が別の科目に在る)", mini([sample_row(per=I1), sample_row(name=u"jppfs_cor:Profit", per=D1)]), [])
    add(u"R11 時点だけ・期間だけは受理", mini([sample_row(per=I1), sample_row(per=I2), sample_row(name=u"jppfs_cor:Profit", per=D1), sample_row(name=u"jppfs_cor:Profit", per=D2)]), [])
    add(u"R11 文の行も数える", mini([txt(u"jpcrp_cor:Text", I1), txt(u"jpcrp_cor:Text", D1), txt(u"jpcrp_cor:Text", D2)]), [("R11", 0, 1, u"期間")])
    # ---- R12(いちばん多い単位・同じ数は字の昇順で先を残す)
    add(u"R12-0 単位 2 通り(多い側を残す)", mini([sample_row(), sample_row(per=I2), sample_row(per=I3, unit=PURE)]), [("R12", 0, 3, u"単位")])
    add(u"R12-0 単位 2 通り(少ない側が先の行)", mini([sample_row(unit=PURE), sample_row(per=I2), sample_row(per=I3)]), [("R12", 0, 1, u"単位")])
    add(u"R12-0 同じ数(純数 と 通貨:JPY → 純数 を残す)", mini([sample_row(), sample_row(per=I2, unit=PURE)]), [("R12", 0, 1, u"単位")])
    add(u"R12-0 同じ数(通貨:JPY が後)", mini([sample_row(unit=PURE), sample_row(per=I2)]), [("R12", 0, 2, u"単位")])
    add(u"R12-0 同じ数(株 と 通貨:JPY → 株 を残す)", mini([sample_row(), sample_row(per=I2, unit=SHARES)]), [("R12", 0, 1, u"単位")])
    add(u"R12-0 3 通りが 1 つずつ(字の昇順で先を残す)", mini([sample_row(), sample_row(per=I2, unit=SHARES), sample_row(per=I3, unit=PURE)]), [("R12", 0, 1, u"単位"), ("R12", 0, 3, u"単位")])
    add(u"R12 無い 行の単位も数える", mini([sample_row(), sample_row(per=I2), sample_row(per=I3, unit=PURE, value=NONE_V, shift=None, prec=None)]), [("R12", 0, 3, u"単位")])
    add(u"R12 文の行は単位を持たず数えない(R11・R13 は別に出る)", mini([sample_row(), txt(u"jppfs_cor:Assets", D1), sample_row(per=I2), sample_row(per=I3)]), [("R11", 0, 2, u"期間"), ("R13", 0, 2, u"種類")])
    add(u"R12 科目が違えば別", mini([sample_row(), sample_row(name=u"jppfs_cor:Profit", unit=PURE)]), [])
    # ---- R13
    add(u"R13-0 数 2・文 1 → 文を断る", mini([sample_row(), sample_row(per=I2), txt(u"jppfs_cor:Assets", I3)]), [("R13", 0, 3, u"種類")])
    add(u"R13-0 数 1・文 2 → 数を断る", mini([txt(u"jppfs_cor:Assets", I1), sample_row(), txt(u"jppfs_cor:Assets", I2)]), [("R13", 0, 2, u"種類")])
    add(u"R13-0 同じ数 → 文の側を断る", mini([sample_row(), txt(u"jppfs_cor:Assets", I2)]), [("R13", 0, 2, u"種類")])
    add(u"R13-0 同じ数(文が先の行でも文の側)", mini([txt(u"jppfs_cor:Assets", I1), sample_row()]), [("R13", 0, 1, u"種類")])
    add(u"R13-0 同じ数(2 と 2)→ 文の 2 行", mini([sample_row(), txt(u"jppfs_cor:Assets", I2), sample_row(per=I2), txt(u"jppfs_cor:Assets", I3)]), [("R13", 0, 2, u"種類"), ("R13", 0, 4, u"種類")])
    add(u"R13 科目が違えば別", mini([sample_row(), txt(u"jpcrp_cor:Text", D1)]), [])
    # ---- R1〜R7 に当たった行は R8〜R13 に掛けない / R8・R9 の行は掛ける
    add(u"R5 に当たった行は R12 に掛けない", mini([sample_row(), sample_row(per=I2), sample_row(per=I3, unit=PURE, value=u"1,0")]), [("R5", 1, 3, u"値")])
    add(u"R6 に当たった行は R12 に掛けない", mini([sample_row(), sample_row(per=I2), sample_row(per=I3, unit=u"円")]), [("R6", 1, 3, u"単位")])
    add(u"R2 に当たった行は R11 に掛けない", mini([sample_row(per=I1), sample_row(per=u"x")]), [("R2", 0, 2, u"期間")])
    add(u"R2 に当たった行は R10 に掛けない", mini([sample_row(per=I1), sample_row(per=od([(u"時点", u"2031-03-31"), (u"始まり", u"2031-03-31")]))]), [("R2", 0, 2, u"期間")])
    add(u"R7 に当たった行は R13 に掛けない", mini([txt(u"jppfs_cor:Assets", I1), txt(u"jppfs_cor:Assets", I2), sample_row(per=I3), sample_row(per=per_i(u"2031-03-28"), prec=u"0")]),
        [("R7", 0, 4, u"精度"), ("R13", 0, 3, u"種類")])
    add(u"R4 に当たった行は R10 に掛けない(同じ組の 2 行)", mini([sample_row(dims=[[SA, SM], [CA, CM]]), sample_row(dims=[[SA, SM], [CA, CM]])], custom=[(u"member", SM), (u"軸", SA)]),
        [("R4", 3, 1, u"次元"), ("R4", 3, 2, u"次元")])
    add(u"R9 に当たった行も R10 に掛ける", mini([sample_row(value=u"12.5"), sample_row(value=u"12.5")]), [("R9", 0, 1, u"値"), ("R9", 0, 2, u"値"), ("R10", 0, 2, u"行")])
    add(u"R8 に当たった行も R12 に掛ける", mini([sample_row(value=u"0", prec=-1), sample_row(per=I2), sample_row(per=I3, unit=PURE)]), [("R8", 0, 1, u"精度"), ("R12", 0, 3, u"単位")])
    add(u"R1 で行を読めない行は名の規則も掛けない", mini([sample_row(), od([(u"種類", u"x"), (u"科目", u"nocolon")])]), [("R1", 1, 2, u"種類")])
    add(u"行が object でなくても他の行は見る", edit(lambda o: (o[u"行"].__setitem__(1, 5), row_of(o, 1).__setitem__(u"値", u"1,2"))), [("R1", 0, 2, u"行"), ("R5", 1, 1, u"値")])
    # ---- 掃く変異で穴が見つかった所(2026-11-23 の変異の掃きで足した手の値)
    add(u"N1 `-` を含む名は通す", mini([sample_row(name=u"x_E1:Own-Two")], custom=[(u"科目", u"x_E1:Own-Two")]), [])
    add(u"N4 同じ名でも種類が違えば重ならない(並びも種類・名の順)", mini([sample_row(name=SA), sample_row(name=u"jppfs_cor:Profit", dims=[[SA, SM]])], custom=[(u"member", SM), (u"科目", SA), (u"軸", SA)]), [])
    add(u"R2 期間の鍵が 始まり・終わり・備考", mini([sample_row(per=od([(u"始まり", u"2030-04-01"), (u"終わり", u"2031-03-31"), (u"備考", u"x")]))]), [("R2", 0, 1, u"期間")])
    add(u"R4-2 同じ軸で member が違う", mini([sample_row(dims=[[CA, CM], [CA, IND_MEMBER]])]), [("R4", 2, 1, u"次元")])
    AA, AB, AC = u"x_E1:AAxis", u"x_E1:BAxis", u"x_E1:CAxis"
    MA, MB, MC = u"x_E1:AMember", u"x_E1:BMember", u"x_E1:CMember"
    add(u"R4-3 昇順の崩れが 2 組目", mini([sample_row(dims=[[AA, MA], [AC, MC], [AB, MB]])], custom=[(u"member", MA), (u"member", MB), (u"member", MC), (u"軸", AA), (u"軸", AB), (u"軸", AC)]), [("R4", 3, 1, u"次元")])
    add(u"R4-4 個別の member は別の軸なら通す", mini([sample_row(dims=[[SA, IND_MEMBER]])], custom=[(u"軸", SA)]), [])
    add(u"R5-1 全角の数字が混ざる(1 字目だけ半角)", mini([sample_row(value=u"1\uff12\uff13")]), [("R5", 1, 1, u"値")])
    add(u"R6-1 `他:` が頭に無い", mini([sample_row(unit=u"x他:iso4217:USD")]), [("R6", 1, 1, u"単位")])
    add(u"R6 分子が 2 つの 他: は 4 つの形に当たらない", mini([sample_row(unit=u"他:iso4217:JPY*iso4217:USD÷xbrli:shares")]), [])
    add(u"R5 に当たっても R7 は掛ける(値が字でない形)", mini([sample_row(value=u"abc", shift=1.5)]), [("R5", 1, 1, u"値"), ("R7", 0, 1, u"表示の位")])
    add(u"R12-0 同じ数で字の昇順が長い側(通貨:EUR÷株 を残す)", mini([sample_row(unit=u"通貨:EUR÷株"), sample_row(per=I2, unit=u"通貨:USD")]), [("R12", 0, 2, u"単位")])
    return C


ORDERED_CASES = [
    (u"R11 を 2 つの科目に(先の科目の断りが後ろの行)", mini([sample_row(per=per_i(u"2031-03-31")), sample_row(name=u"jppfs_cor:Profit", per=per_d(u"2030-04-01", u"2031-03-31")),
                                                       sample_row(name=u"jppfs_cor:Profit", per=per_i(u"2031-03-31")), sample_row(per=per_d(u"2030-04-01", u"2031-03-31"))]),
     [("R11", 0, 2, u"期間"), ("R11", 0, 4, u"期間")]),
]


DOC_KEYS_H = (u"提出者の識別子", u"識別子の scheme", u"当期の始まり", u"当期の終わり", u"提出日")


def rules_problems(ms=None):
    ms = ms or MS
    out = []
    for label, o, want in rule_cases():
        got = rr(ms, o)
        if not same(got, want):
            out.append(u"%s: 手の値 %s ≠ %s" % (label, want, got))
    for label, o, want in ORDERED_CASES:
        if rr(ms, o) != want:
            out.append(u"%s: 並びの順が違う %s ≠ %s" % (label, want, rr(ms, o)))
    # 断りの欄・理由が表の字そのもの(理由は「断る時」の 1 つ)
    x = ms.check_text(dump(edit(set_row(1, u"値", u"1,2"))), NAMES)
    if len(x) != 1 or list(x[0]) != [u"行", u"欄", u"規則", u"理由"] or x[0][u"理由"] != SEAL_RULES["R5"][1].split(u"・")[1] or x[0][u"行"] != 1:
        out.append(u"断りの鍵・順・理由が違う: %s" % x)
    # 並び: 規則の表の順・行の昇順
    got = ms.check_text(dump(edit(lambda o: (o[u"行"][2].__setitem__(u"値", u"x"), o[u"行"][0].__setitem__(u"単位", u"円"), o[u"書類"].__setitem__(u"提出日", u"x")))), NAMES)
    if [(g[u"規則"], g[u"行"]) for g in got] != [("D1", None), ("R5", 3), ("R6", 1)]:
        out.append(u"断りの並びの順が違う: %s" % [(g[u"規則"], g[u"行"]) for g in got])
    # 受け口は引数の辞書だけを見る(空の辞書なら辞書の在る接頭辞の名は全部断る)
    got = rr(ms, mini([sample_row(name=u"jppfs_cor:Assets")]), frozenset())
    if got != [("N2", 0, 1, u"科目")]:
        out.append(u"空の辞書で辞書の名を断らない: %s" % got)
    return out



# ======================================================================== 4. 壊し方 44 通り・変え方 6 通り(手で決めた編集と手で決めた断り)
def hand_edits():
    u"""壊し方ごとの手の編集(``base()`` の写しを変える)。S2a だけは字(``dump(base())`` の字)で別に持つ。"""
    E = od()
    E["S1a"] = set_top(u"型の版", u"0")
    E["S1b"] = set_top(u"備考", u"x")
    E["D1a"] = set_doc(u"当期の終わり", u"2031-13-31")
    E["D1b"] = set_doc(u"備考", u"x")
    E["D2a"] = set_doc(u"当期の始まり", u"2031-04-01")
    E["D3a"] = set_doc(u"提出日", u"2031-03-30")
    E["D4a"] = set_doc(u"提出者の識別子", u"")
    E["N1a"] = set_row(1, u"科目", u"jppfs_corAssets")
    E["N2a"] = set_row(1, u"科目", u"jppfs_cor:AssetsZz")
    E["N3a"] = lambda o: o.__setitem__(u"独自の名", [e for e in o[u"独自の名"] if e[u"名"] != OWN])
    E["N4a"] = lambda o: o[u"独自の名"].insert(2, one(u"科目", u"zz_unused:Zz"))
    E["N4b"] = lambda o: o[u"独自の名"].insert(0, o[u"独自の名"].pop(1))
    E["N5a"] = lambda o: row_of(o, 4)[u"次元"][0].__setitem__(0, CA + u"X")
    E["N5b"] = lambda o: row_of(o, 4)[u"次元"][0].__setitem__(1, CM + u"X")
    E["R1a"] = del_row_key(1, u"対象")
    E["R1b"] = set_row(1, u"備考", u"x")
    E["R1c"] = set_row(10, u"値", NONE_V)
    E["R2a"] = set_row(1, u"期間", od([(u"時点", u"2031-03-31"), (u"始まり", u"2031-03-31")]))
    E["R2b"] = set_row(4, u"期間", per_d(u"2031-03-31", u"2030-04-01"))
    E["R2c"] = set_row(1, u"期間", per_i(u"2031/03/31"))
    E["R3a"] = set_row(1, u"対象", u"連結")
    E["R4a"] = set_row(4, u"次元", [[SA, SM], [CA, CM]])
    E["R4b"] = set_row(4, u"次元", [[CA, CM], [CA, CM], [SA, SM]])
    E["R4c"] = set_row(1, u"次元", [[CONS_AXIS, IND_MEMBER]])
    E["R5a"] = set_row(1, u"値", u"1,234,000")
    E["R5b"] = set_row(1, u"値", 1234000)
    E["R5c"] = set_row(1, u"値", u"+1234000")
    E["R5d"] = set_row(1, u"値", u"1234000.0")
    E["R5e"] = set_row(1, u"値", u"１２３４０００")
    E["R6a"] = set_row(1, u"単位", u"円")
    E["R6b"] = set_row(1, u"単位", u"通貨:jpy")
    E["R6c"] = set_row(7, u"単位", u"他:xbrli:pure")
    E["R7a"] = set_row(1, u"精度", u"-3")
    E["R7b"] = set_row(9, u"精度", 0)
    E["R7c"] = set_row(1, u"表示の位", None)
    E["R7d"] = set_row(1, u"精度", True)
    E["R8a"] = set_row(4, u"精度", -1)
    E["R9a"] = set_row(1, u"値", u"1234100")
    E["R10a"] = lambda o: o[u"行"].append(copy.deepcopy(o[u"行"][0]))
    E["R10b"] = lambda o: o[u"行"].append(od(list(copy.deepcopy(o[u"行"][0]).items())[:5] + [(u"値", u"1235000")] + list(copy.deepcopy(o[u"行"][0]).items())[6:]))
    E["R11a"] = set_row(3, u"期間", per_d(u"2030-04-01", u"2031-03-31"))
    E["R12a"] = set_row(3, u"単位", PURE)
    E["R13a"] = lambda o: o[u"行"].__setitem__(2, od([(u"種類", u"文"), (u"科目", u"jppfs_cor:Assets"), (u"期間", per_i(u"2031-03-31")), (u"対象", u"個別"), (u"次元", [])]))
    return E


def change_edits():
    E = od()
    E["Q1"] = set_row(2, u"対象", u"個別")
    E["Q2"] = set_row(1, u"科目", u"jppfs_cor:Equity")
    E["Q3"] = set_row(1, u"値", u"1235000")
    E["Q4"] = set_row(1, u"値", u"-1234000")
    E["Q5"] = set_row(2, u"期間", per_i(u"2029-03-31"))
    E["Q6"] = set_row(4, u"単位", u"通貨:USD")
    return E


#: 壊し方ごとの、狙った組と、断りの並びの全部(手で数えた値)
EXPECT_BREAK = od([
    ("S1a", (("S1", None, u"型の版"), [("S1", 3, None, u"型の版")])), ("S1b", (("S1", None, u"file"), [("S1", 2, None, u"file")])), ("S2a", (("S2", None, u"file"), [("S2", 0, None, u"file")])),
    ("D1a", (("D1", None, u"当期の終わり"), [("D1", 1, None, u"当期の終わり")])), ("D1b", (("D1", None, u"書類"), [("D1", 0, None, u"書類")])),
    ("D2a", (("D2", None, u"当期の始まり"), [("D2", 0, None, u"当期の始まり")])), ("D3a", (("D3", None, u"提出日"), [("D3", 0, None, u"提出日")])),
    ("D4a", (("D4", None, u"提出者の識別子"), [("D4", 0, None, u"提出者の識別子")])),
    ("N1a", (("N1", 1, u"科目"), [("N1", 0, 1, u"科目")])), ("N2a", (("N2", 1, u"科目"), [("N2", 0, 1, u"科目")])), ("N3a", (("N3", 6, u"科目"), [("N3", 0, 6, u"科目")])),
    ("N4a", (("N4", None, u"独自の名"), [("N4", 3, None, u"独自の名")])), ("N4b", (("N4", None, u"独自の名"), [("N4", 5, None, u"独自の名")])),
    ("N5a", (("N5", 4, u"次元"), [("N2", 0, 4, u"次元"), ("N5", 0, 4, u"次元")])), ("N5b", (("N5", 4, u"次元"), [("N2", 0, 4, u"次元"), ("N5", 1, 4, u"次元")])),
    ("R1a", (("R1", 1, u"対象"), [("R1", 2, 1, u"対象")])), ("R1b", (("R1", 1, u"備考"), [("R1", 2, 1, u"備考")])), ("R1c", (("R1", 10, u"値"), [("R1", 2, 10, u"値")])),
    ("R2a", (("R2", 1, u"期間"), [("R2", 0, 1, u"期間")])), ("R2b", (("R2", 4, u"期間"), [("R2", 2, 4, u"期間")])), ("R2c", (("R2", 1, u"期間"), [("R2", 1, 1, u"期間")])),
    ("R3a", (("R3", 1, u"対象"), [("R3", 0, 1, u"対象")])),
    ("R4a", (("R4", 4, u"次元"), [("R4", 3, 4, u"次元")])), ("R4b", (("R4", 4, u"次元"), [("R4", 2, 4, u"次元")])), ("R4c", (("R4", 1, u"次元"), [("R4", 4, 1, u"次元")])),
    ("R5a", (("R5", 1, u"値"), [("R5", 1, 1, u"値")])), ("R5b", (("R5", 1, u"値"), [("R5", 0, 1, u"値")])), ("R5c", (("R5", 1, u"値"), [("R5", 1, 1, u"値")])),
    ("R5d", (("R5", 1, u"値"), [("R5", 1, 1, u"値")])), ("R5e", (("R5", 1, u"値"), [("R5", 1, 1, u"値")])),
    ("R6a", (("R6", 1, u"単位"), [("R6", 1, 1, u"単位")])), ("R6b", (("R6", 1, u"単位"), [("R6", 1, 1, u"単位")])), ("R6c", (("R6", 7, u"単位"), [("R6", 2, 7, u"単位")])),
    ("R7a", (("R7", 1, u"精度"), [("R7", 0, 1, u"精度")])), ("R7b", (("R7", 9, u"精度"), [("R7", 2, 9, u"精度")])), ("R7c", (("R7", 1, u"表示の位"), [("R7", 0, 1, u"表示の位")])),
    ("R7d", (("R7", 1, u"精度"), [("R7", 0, 1, u"精度")])), ("R8a", (("R8", 4, u"精度"), [("R8", 0, 4, u"精度")])), ("R9a", (("R9", 1, u"値"), [("R9", 0, 1, u"値")])),
    ("R10a", (("R10", 12, u"行"), [("R10", 0, 12, u"行")])), ("R10b", (("R10", 12, u"行"), [("R10", 0, 12, u"行")])),
    ("R11a", (("R11", 3, u"期間"), [("R11", 0, 3, u"期間")])), ("R12a", (("R12", 3, u"単位"), [("R12", 0, 3, u"単位")])), ("R13a", (("R13", 3, u"種類"), [("R13", 0, 3, u"種類")]))])
#: 当てはまる所が無い最小の file(行 1 つ・独自の名なし)で「作れなかった」になる壊し方・変え方
NONE_ON_MINI = (u"N3a", u"N4b", u"N5a", u"N5b", u"R1c", u"R2b", u"R4a", u"R4b", u"R5a", u"R6c", u"R7b", u"R8a", u"R11a", u"R12a", u"R13a", u"Q2")


def parse_back(text):
    return json.loads(text, object_pairs_hook=od)


def breaks_problems(ms=None):
    ms = ms or MS
    out = []
    b0 = base()
    t0 = dump(b0)
    broken, changed = ms.make_variants(t0, NAMES)
    if list(broken) != list(BREAK_IDS_HAND) or list(changed) != list(CHANGE_IDS_HAND):
        out.append(u"壊し方・変え方の並びが違う")
    edits = hand_edits()
    if len(edits) != 43:
        out.append(u"手の編集の数が違う(S2a を除く 43)")
    for bid, want in EXPECT_BREAK.items():
        made = broken.get(bid)
        if made is None:
            out.append(u"%s が作れない(BASE には当てはまる所が在る)" % bid)
            continue
        target, text = made
        if target != want[0]:
            out.append(u"%s の狙いが違う: 手の値 %s ≠ %s" % (bid, want[0], target))
        if bid == "S2a":
            if text != t0[:1] + u'"型の版": "1",' + t0[1:]:
                out.append(u"S2a の字が違う")
        else:
            exp = copy.deepcopy(b0)
            edits[bid](exp)
            if parse_back(text) != exp or list(parse_back(text)) != list(exp):
                out.append(u"%s が手の編集と違う(狙った所だけが変わっていない)" % bid)
            if text != dump(exp):
                out.append(u"%s の書き方が違う" % bid)
        got = rr(ms, text)
        if not same(got, want[1]):
            out.append(u"%s の断りの並びが手の値と違う: %s ≠ %s" % (bid, want[1], got))
        if ms.judge_break(target, ms.check_text(text, NAMES)) != od(zip(ms.BREAK_RESULT_KEYS, [1, 1, 1 if len(want[1]) == 1 else 0, 0, 0])):
            out.append(u"%s の判定が手の値と違う" % bid)
    cedits = change_edits()
    for qid, fn in cedits.items():
        text = changed.get(qid)
        exp = copy.deepcopy(b0)
        fn(exp)
        if text is None or parse_back(text) != exp or text != dump(exp):
            out.append(u"%s が手の編集と違う" % qid)
            continue
        if rr(ms, text):
            out.append(u"%s が型の規則を破っている: %s" % (qid, rr(ms, text)))
    # 当てはまる所が無ければ作れない
    mt = dump(mini([sample_row()]))
    mb, mc = ms.make_variants(mt, NAMES)
    none_got = tuple(k for k, v in list(mb.items()) + list(mc.items()) if v is None)
    if sorted(none_got) != sorted(NONE_ON_MINI):
        out.append(u"最小の file で作れない壊し方・変え方が手の値と違う: %s" % sorted(set(none_got) ^ set(NONE_ON_MINI)))
    for k, v in mb.items():
        if v is not None and not rr(ms, v[1]):
            out.append(u"最小の file の壊し方 %s を受け口が断らない" % k)
    for k, v in mc.items():
        if v is not None and rr(ms, v):
            out.append(u"最小の file の変え方 %s が型の規則を破る" % k)
    out += first_match_problems(ms)
    return out


def first_match_problems(ms):
    u"""「最初の当てはまる所(行は番号の昇順)」: 先の行が当てはまらず、2 つ目・3 つ目の行が当てはまる file で、狙いがその行になる。"""
    out = []
    I1, I2, I3, I4 = per_i(u"2031-03-31"), per_i(u"2031-03-30"), per_i(u"2031-03-29"), per_i(u"2031-03-28")
    D1, D2 = per_d(u"2030-04-01", u"2031-03-31"), per_d(u"2030-04-01", u"2031-03-30")
    cus = [(u"member", SM), (u"科目", OWN), (u"軸", SA)]
    rows = [sample_row(name=u"jppfs_cor:Profit", per=I1, value=u"7.5", prec=1),                                                         # 1 小数点が在る・4 桁未満
            sample_row(name=u"jppfs_cor:Assets", per=I1, value=u"12345", unit=PURE, shift=0, prec=0),                                      # 2 値が 4 桁以上・純数
            sample_row(name=u"jppfs_cor:Assets", per=I2, value=u"67890", unit=PURE),                                                       # 3
            sample_row(name=OWN, per=I3, value=u"0", shift=0, prec=0),                                                                    # 4 独自の科目・値 0
            sample_row(name=OWN, per=I4, value=u"0"),                                                                                      # 5
            sample_row(name=u"jppfs_cor:Equity", per=D2, value=NONE_V, shift=None, prec=None),                                             # 6 無い・期間(始まり≠終わり)
            sample_row(name=u"jppfs_cor:Equity", per=D1, value=u"9", dims=[[CA, CM], [SA, SM]]),                                          # 7 次元 2 つ
            sample_row(name=u"jppfs_cor:EPS", per=D1, value=u"3", dims=[[SA, SM]]),                                                       # 8 次元 1 つ
            txt(u"jpcrp_cor:Text", I1), txt(u"jpcrp_cor:Text", I2)]                                                                      # 9・10 文
    text = dump(doc_of(rows, cus))
    if rr(ms, text):
        return [u"最初の当てはまる所の作り物が受理されない: %s" % rr(ms, text)]
    broken, changed = ms.make_variants(text, NAMES)
    want = {"R5a": ("R5", 2, u"値"), "R5d": ("R5", 2, u"値"), "R5c": ("R5", 1, u"値"), "R6c": ("R6", 2, u"単位"), "R6a": ("R6", 1, u"単位"), "N3a": ("N3", 4, u"科目"), "R7b": ("R7", 6, u"精度"),
            "R2b": ("R2", 6, u"期間"), "R2a": ("R2", 1, u"期間"), "R8a": ("R8", 4, u"精度"), "N5a": ("N5", 7, u"次元"), "N5b": ("N5", 7, u"次元"), "R4a": ("R4", 7, u"次元"), "R4b": ("R4", 7, u"次元"),
            "R1c": ("R1", 9, u"値"), "R9a": ("R9", 1, u"値"), "R10a": ("R10", 11, u"行"), "R11a": ("R11", 3, u"期間"), "R12a": ("R12", 3, u"単位"), "R13a": ("R13", 3, u"種類"), "R7a": ("R7", 1, u"精度")}
    for k, w in want.items():
        if broken[k] is None or broken[k][0] != w:
            out.append(u"最初の当てはまる所が違う: %s 手の値 %s ≠ %s" % (k, w, None if broken[k] is None else broken[k][0]))
    return out



# ======================================================================== 5. 判定・壊れた入力・辞書・別の process
def judge_problems(ms=None):
    ms = ms or MS
    out = []
    tgt = ("R9", 3, u"値")
    R = lambda rule, idx, row, field: ms.refusal(rule, idx, row, field)                              # noqa: E731
    keys = ms.BREAK_RESULT_KEYS
    cases = [(u"狙った 1 つだけ", [R("R9", 0, 3, u"値")], [1, 1, 1, 0, 0]), (u"狙った組と別の断り", [R("R9", 0, 3, u"値"), R("R5", 0, 2, u"値")], [1, 1, 0, 0, 0]),
             (u"行が違う", [R("R9", 0, 4, u"値")], [1, 0, 0, 1, 0]), (u"欄が違う", [R("R9", 0, 3, u"精度")], [1, 0, 0, 1, 0]), (u"規則が違う", [R("R8", 0, 3, u"値")], [1, 0, 0, 1, 0]),
             (u"断らない", [], [1, 0, 0, 0, 1]), (u"狙った組が 2 つ", [R("R9", 0, 3, u"値"), R("R9", 0, 3, u"値")], [1, 1, 0, 0, 0])]
    for label, refs, want in cases:
        got = ms.judge_break(tgt, refs)
        if list(got) != list(keys) or list(got.values()) != want:
            out.append(u"壊し方の判定(%s)が違う: %s ≠ %s" % (label, want, list(got.values())))
    g = ms.judge_change([R("R9", 0, 3, u"値"), R("R5", 0, 3, u"値"), R("R9", 0, 4, u"値")])
    if g[u"作れた"] != 1 or g[u"通した"] != 0 or list(g[u"断った"]) != list(RULE_IDS) or {k: v for k, v in g[u"断った"].items() if v} != {"R5": 1, "R9": 1}:
        out.append(u"変え方の判定(断った)が違う: %s" % g)
    g = ms.judge_change([])
    if g[u"作れた"] != 1 or g[u"通した"] != 1 or any(g[u"断った"].values()):
        out.append(u"変え方の判定(通した)が違う: %s" % g)
    z = ms.zero_change()
    if z[u"作れた"] != 0 or z[u"通した"] != 0 or list(z[u"断った"]) != list(RULE_IDS) or ms.zero_break() != od(zip(keys, [0] * 5)):
        out.append(u"作れなかった行の零が違う")
    # run_variants: 壊した file(元の file でない)を受け口に掛け、作れた分だけ数える
    t0 = dump(base())
    calls = []

    def cap(cmd, cwd, timeout):
        calls.append((list(cmd), cwd, timeout, sorted(os.listdir(cmd[4])) if os.path.isdir(cmd[4]) else None, dict((f, rfile(os.path.join(cmd[4], f)).decode("utf-8")) for f in os.listdir(cmd[4]))))
        out_, err_ = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out_), contextlib.redirect_stderr(err_):
            rc = ms.accept_main(list(cmd[3:]))
        return rc, out_.getvalue(), err_.getvalue(), False
    with Temp() as d:
        nf = os.path.join(d, "names.json")
        wfile(nf, json.dumps(sorted(NAMES)))
        brk, chg = ms.run_variants(t0, NAMES, d, d, cap, nf)
        if len(calls) != 1:
            out.append(u"受け口を 1 回で掛けない: %d" % len(calls))
        else:
            cmd, cwd, timeout, listing, contents = calls[0]
            want_files = sorted(f + u".json" for f in BREAK_IDS_HAND + CHANGE_IDS_HAND)
            if cmd[:4] != [sys.executable, "-I", ms.SCRIPT_PATH, "--accept-dir"] or cmd[5:] != ["--names-file", nf] or cwd != d or timeout != 600 or listing != want_files:
                out.append(u"受け口の呼び方が違う: %s" % (cmd, ))
            broken, changed = ms.make_variants(t0, NAMES)
            for k, v in broken.items():
                if contents.get(k + u".json") != v[1] or contents[k + u".json"] == t0:
                    out.append(u"受け口に掛けた file が壊した file でない: %s" % k)
                    break
            for k, v in changed.items():
                if contents.get(k + u".json") != v or v == t0:
                    out.append(u"受け口に掛けた file が変えた file でない: %s" % k)
                    break
        want_b = od((k, od(zip(keys, [1, 1, 1 if len(EXPECT_BREAK[k][1]) == 1 else 0, 0, 0]))) for k in BREAK_IDS_HAND)
        if brk != want_b:
            out.append(u"壊し方の数が手の値と違う: %s" % [k for k in brk if brk[k] != want_b[k]])
        if any(v[u"作れた"] != 1 or v[u"通した"] != 1 or any(v[u"断った"].values()) for v in chg.values()) or list(chg) != list(CHANGE_IDS_HAND):
            out.append(u"変え方の数が手の値と違う")
    with Temp() as d:
        nf = os.path.join(d, "names.json")
        wfile(nf, json.dumps(sorted(NAMES)))
        brk, chg = ms.run_variants(dump(mini([sample_row()])), NAMES, d, d, cap, nf)
        if [k for k, v in brk.items() if v[u"作れた"] == 0] + [k for k, v in chg.items() if v[u"作れた"] == 0] != [k for k in BREAK_IDS_HAND + CHANGE_IDS_HAND if k in NONE_ON_MINI]:
            out.append(u"作れなかった壊し方・変え方の数が零にならない")
        for k, v in brk.items():
            if v[u"作れた"] == 0 and any(v.values()):
                out.append(u"作れなかった壊し方に数が在る: %s" % k)
        if len(calls) != 2 or len(calls[1][3]) != 50 - len(NONE_ON_MINI):
            out.append(u"最小の file で受け口に掛けた file の数が違う: %s" % (len(calls[1][3]) if len(calls) > 1 else None))
    # 受け口が 0 でない終わりの値・JSON でない出力・時間切れ → Refuse
    def bad_cap(rc, text, to=False):
        return lambda cmd, cwd, timeout: (rc, text, u"", to)
    for what, cp in ((u"終わりの値", bad_cap(1, u"")), (u"JSON でない", bad_cap(0, u"x")), (u"時間", bad_cap(None, u"", True))):
        with Temp() as d:
            try:
                ms.exec_accept(os.path.join(d, "x"), d, cp)
                out.append(u"受け口が壊れた出力を返しても断りにならない: " + what)
            except ms.Refuse as exc:
                if exc.reason != {u"終わりの値": u"受け口の検査が 0 でない終わりの値で終わった", u"JSON でない": u"受け口の検査の出力が JSON でない", u"時間": u"受け口の検査が時間の上限を超えた"}[what]:
                    out.append(u"受け口の断りの理由が違う: %s" % exc.reason)
    return out


DEGENERATE = [
    ("empty", b""), ("space", b"  \n"), ("not json", b"abc"), ("array", b"[1,2]"), ("scalar", b"5"), ("null", b"null"), ("string", b'"x"'), ("nan", b"NaN"), ("object nan", b'{"a": NaN}'),
    ("deep array", b"[" * 100000 + b"]" * 100000), ("deep object", (b'{"a":' * 50000) + b"1" + (b"}" * 50000)), ("deep inside rows", b'{"\xe5\x9e\x8b\xe3\x81\xae\xe7\x89\x88": "1", "\xe6\x9b\xb8\xe9\xa1\x9e": {}, "\xe7\x8b\xac\xe8\x87\xaa\xe3\x81\xae\xe5\x90\x8d": [], "\xe8\xa1\x8c": ' + b"[" * 50000 + b"]" * 50000 + b"}"),
    ("huge int", b'{"\xe5\x9e\x8b\xe3\x81\xae\xe7\x89\x88": "1", "\xe6\x9b\xb8\xe9\xa1\x9e": {}, "\xe7\x8b\xac\xe8\x87\xaa\xe3\x81\xae\xe5\x90\x8d": [], "\xe8\xa1\x8c": [{"\xe7\xa8\xae\xe9\xa1\x9e": "\xe6\x95\xb0", "\xe7\xb2\xbe\xe5\xba\xa6": ' + b"9" * 6000 + b"}]}"), ("huge float", b'{"a": 1e999}'), ("neg huge", b'{"a": -' + b"9" * 5000 + b"}"),
    ("bad utf8", b'\xff\xfe{"a":1}'), ("lone surrogate", '{"a": "\\ud800"}'.encode("utf-8")), ("bom", b"\xef\xbb\xbf{}"), ("nul", b"{\x00}"),
    ("top list", b"[]"), ("keys not string rows", b'{"\xe5\x9e\x8b\xe3\x81\xae\xe7\x89\x88": "1", "\xe6\x9b\xb8\xe9\xa1\x9e": {"\xe6\x8f\x90\xe5\x87\xba\xe8\x80\x85\xe3\x81\xae\xe8\xad\x98\xe5\x88\xa5\xe5\xad\x90": 5}, "\xe7\x8b\xac\xe8\x87\xaa\xe3\x81\xae\xe5\x90\x8d": [[]], "\xe8\xa1\x8c": [[], 5, null, "x", {}]}'),
    ("rows zero", b'{"\xe5\x9e\x8b\xe3\x81\xae\xe7\x89\x88": "1", "\xe6\x9b\xb8\xe9\xa1\x9e": {}, "\xe7\x8b\xac\xe8\x87\xaa\xe3\x81\xae\xe5\x90\x8d": [], "\xe8\xa1\x8c": []}'), ("custom empty", b'{"\xe5\x9e\x8b\xe3\x81\xae\xe7\x89\x88": "1", "\xe6\x9b\xb8\xe9\xa1\x9e": {}, "\xe7\x8b\xac\xe8\x87\xaa\xe3\x81\xae\xe5\x90\x8d": [], "\xe8\xa1\x8c": [{}]}'),
    ("custom odd", b'{"\xe5\x9e\x8b\xe3\x81\xae\xe7\x89\x88": "1", "\xe6\x9b\xb8\xe9\xa1\x9e": {}, "\xe7\x8b\xac\xe8\x87\xaa\xe3\x81\xae\xe5\x90\x8d": [1, "a", null, [], {}, {"\xe7\xa8\xae\xe9\xa1\x9e": [], "\xe5\x90\x8d": {}}, {"\xe7\xa8\xae\xe9\xa1\x9e": "\xe7\xa7\x91\xe7\x9b\xae", "\xe5\x90\x8d": []}], "\xe8\xa1\x8c": [5]}'),
    ("row odd values", b'{"\xe5\x9e\x8b\xe3\x81\xae\xe7\x89\x88": "1", "\xe6\x9b\xb8\xe9\xa1\x9e": {"x": 1}, "\xe7\x8b\xac\xe8\x87\xaa\xe3\x81\xae\xe5\x90\x8d": [], "\xe8\xa1\x8c": [{"\xe7\xa8\xae\xe9\xa1\x9e": "\xe6\x95\xb0", "\xe7\xa7\x91\xe7\x9b\xae": [], "\xe6\x9c\x9f\xe9\x96\x93": [], "\xe5\xaf\xbe\xe8\xb1\xa1": {}, "\xe6\xac\xa1\xe5\x85\x83": [[[]], [{}, {}], 5], "\xe5\x80\xa4": {}, "\xe5\x8d\x98\xe4\xbd\x8d": [], "\xe8\xa1\xa8\xe7\xa4\xba\xe3\x81\xae\xe4\xbd\x8d": [], "\xe7\xb2\xbe\xe5\xba\xa6": {}}]}'),
    ("row odd text", b'{"\xe5\x9e\x8b\xe3\x81\xae\xe7\x89\x88": "1", "\xe6\x9b\xb8\xe9\xa1\x9e": {}, "\xe7\x8b\xac\xe8\x87\xaa\xe3\x81\xae\xe5\x90\x8d": [], "\xe8\xa1\x8c": [{"\xe7\xa8\xae\xe9\xa1\x9e": "\xe6\x96\x87", "\xe7\xa7\x91\xe7\x9b\xae": 5, "\xe6\x9c\x9f\xe9\x96\x93": 5, "\xe5\xaf\xbe\xe8\xb1\xa1": [], "\xe6\xac\xa1\xe5\x85\x83": {}}]}'),
    ("unhashable subject", b'{"\xe5\x9e\x8b\xe3\x81\xae\xe7\x89\x88": "1", "\xe6\x9b\xb8\xe9\xa1\x9e": {}, "\xe7\x8b\xac\xe8\x87\xaa\xe3\x81\xae\xe5\x90\x8d": [], "\xe8\xa1\x8c": [{"\xe7\xa8\xae\xe9\xa1\x9e": "\xe6\x96\x87", "\xe7\xa7\x91\xe7\x9b\xae": ["a"], "\xe6\x9c\x9f\xe9\x96\x93": {"\xe6\x99\x82\xe7\x82\xb9": "2031-03-31"}, "\xe5\xaf\xbe\xe8\xb1\xa1": "\xe6\x97\xa2\xe5\xae\x9a", "\xe6\xac\xa1\xe5\x85\x83": []}]}'),
    ("unhashable kind", b'{"\xe5\x9e\x8b\xe3\x81\xae\xe7\x89\x88": "1", "\xe6\x9b\xb8\xe9\xa1\x9e": {}, "\xe7\x8b\xac\xe8\x87\xaa\xe3\x81\xae\xe5\x90\x8d": [{"\xe7\xa8\xae\xe9\xa1\x9e": ["x"], "\xe5\x90\x8d": "a:b"}], "\xe8\xa1\x8c": [{"\xe7\xa8\xae\xe9\xa1\x9e": ["\xe6\x95\xb0"]}]}'),
    ("dup keys everywhere", b'{"a": 1, "a": 2, "\xe5\x9e\x8b\xe3\x81\xae\xe7\x89\x88": "1", "\xe5\x9e\x8b\xe3\x81\xae\xe7\x89\x88": "1"}'), ("big", b'{"\xe8\xa1\x8c": [' + b",".join([b"{}"] * 20000) + b"]}"),
    ("value is bool", b'{"\xe5\x9e\x8b\xe3\x81\xae\xe7\x89\x88": "1", "\xe6\x9b\xb8\xe9\xa1\x9e": {}, "\xe7\x8b\xac\xe8\x87\xaa\xe3\x81\xae\xe5\x90\x8d": [], "\xe8\xa1\x8c": [{"\xe7\xa8\xae\xe9\xa1\x9e": "\xe6\x95\xb0", "\xe7\xa7\x91\xe7\x9b\xae": "a:b", "\xe6\x9c\x9f\xe9\x96\x93": {"\xe6\x99\x82\xe7\x82\xb9": "2031-03-31"}, "\xe5\xaf\xbe\xe8\xb1\xa1": "\xe6\x97\xa2\xe5\xae\x9a", "\xe6\xac\xa1\xe5\x85\x83": [], "\xe5\x80\xa4": true, "\xe5\x8d\x98\xe4\xbd\x8d": "\xe6\xa0\xaa", "\xe8\xa1\xa8\xe7\xa4\xba\xe3\x81\xae\xe4\xbd\x8d": true, "\xe7\xb2\xbe\xe5\xba\xa6": false}]}'),
    ("float prec", b'{"\xe5\x9e\x8b\xe3\x81\xae\xe7\x89\x88": "1", "\xe6\x9b\xb8\xe9\xa1\x9e": {}, "\xe7\x8b\xac\xe8\x87\xaa\xe3\x81\xae\xe5\x90\x8d": [], "\xe8\xa1\x8c": [{"\xe7\xa8\xae\xe9\xa1\x9e": "\xe6\x95\xb0", "\xe7\xa7\x91\xe7\x9b\xae": "a:b", "\xe6\x9c\x9f\xe9\x96\x93": {"\xe6\x99\x82\xe7\x82\xb9": "2031-03-31"}, "\xe5\xaf\xbe\xe8\xb1\xa1": "\xe6\x97\xa2\xe5\xae\x9a", "\xe6\xac\xa1\xe5\x85\x83": [], "\xe5\x80\xa4": "1", "\xe5\x8d\x98\xe4\xbd\x8d": "\xe6\xa0\xaa", "\xe8\xa1\xa8\xe7\xa4\xba\xe3\x81\xae\xe4\xbd\x8d": 1.0, "\xe7\xb2\xbe\xe5\xba\xa6": 1e400}]}'),
    ("unit parts", b'{"\xe5\x9e\x8b\xe3\x81\xae\xe7\x89\x88": "1", "\xe6\x9b\xb8\xe9\xa1\x9e": {}, "\xe7\x8b\xac\xe8\x87\xaa\xe3\x81\xae\xe5\x90\x8d": [], "\xe8\xa1\x8c": [{"\xe7\xa8\xae\xe9\xa1\x9e": "\xe6\x95\xb0", "\xe7\xa7\x91\xe7\x9b\xae": "a:b", "\xe6\x9c\x9f\xe9\x96\x93": {"\xe6\x99\x82\xe7\x82\xb9": "2031-03-31"}, "\xe5\xaf\xbe\xe8\xb1\xa1": "\xe6\x97\xa2\xe5\xae\x9a", "\xe6\xac\xa1\xe5\x85\x83": [], "\xe5\x80\xa4": "1", "\xe5\x8d\x98\xe4\xbd\x8d": "\xe4\xbb\x96:\xc3\xb7\xc3\xb7", "\xe8\xa1\xa8\xe7\xa4\xba\xe3\x81\xae\xe4\xbd\x8d": 0, "\xe7\xb2\xbe\xe5\xba\xa6": 0}]}'),
]


def _huge_digits():
    o = base()
    o[u"行"][0][u"値"] = u"1" + u"0" * 5000
    return dump(o).encode("utf-8")


DEGENERATE.append(("huge digits", _huge_digits()))


def degenerate_problems(ms=None):
    ms = ms or MS
    out = []
    for label, data in DEGENERATE:
        r = guard(ms.check_bytes, data, NAMES)
        if not isinstance(r, list) or (r and isinstance(r[0], str)):
            out.append(u"壊れた入力で例外が出た: %s %s" % (label, r))
            continue
        if any(list(x) != [u"行", u"欄", u"規則", u"理由"] or x[u"規則"] not in RULE_IDS or ms.RULE_CONDS[x[u"規則"]].count(x[u"理由"]) != 1 for x in r):
            out.append(u"壊れた入力の断りの形が違う: %s" % label)
    expect_s1 = {"empty": 0, "space": 0, "not json": 0, "nan": 0, "object nan": 0, "deep array": 0, "deep object": 0, "bad utf8": 0, "bom": 0, "nul": 0, "array": 1, "scalar": 1, "null": 1, "string": 1}
    for label, data in DEGENERATE:
        if label in expect_s1:
            r = ms.check_bytes(data, NAMES)
            if [(x[u"規則"], ms.RULE_CONDS["S1"].index(x[u"理由"]), x[u"行"], x[u"欄"]) for x in r] != [("S1", expect_s1[label], None, u"file")]:
                out.append(u"壊れた入力の S1 が違う: %s %s" % (label, r))
    r = ms.check_bytes(DEGENERATE[[k for k, _v in DEGENERATE].index("rows zero")][1], NAMES)
    if sorted((x[u"規則"], x[u"欄"]) for x in r) != sorted([("S1", u"行")]):
        out.append(u"行が 0 の file の断りが違う: %s" % r)
    r = ms.check_bytes(b'{"a": 1, "a": 2, "\xe5\x9e\x8b\xe3\x81\xae\xe7\x89\x88": "1"}', NAMES)
    if ("S2", u"file") not in [(x[u"規則"], x[u"欄"]) for x in r]:
        out.append(u"同じ鍵を見つけない")
    # check_safe は守り: 予期しない例外が出ても S1 の断りを返す
    saved = ms.check_bytes
    ms.check_bytes = lambda data, names: 1 / 0
    try:
        r = ms.check_safe(b"{}", NAMES)
    finally:
        ms.check_bytes = saved
    if [(x[u"規則"], ms.RULE_CONDS["S1"].index(x[u"理由"]), x[u"行"], x[u"欄"]) for x in r] != [("S1", 0, None, u"file")]:
        out.append(u"予期しない例外のとき断りを返さない: %s" % r)
    return out


def dict_problems(ms=None):
    ms = ms or MS
    out = []
    xml = u'<link:loc xlink:href="x.xsd#jppfs_cor_Assets"/><link:loc xlink:href="../y.xsd#jppfs_cor_Profit-1"/><x href="z#ignored"/><link:loc xlink:href="x.xsd#jpcrp_cor_Text" />'
    with Temp() as d:
        shas = od()
        for i, fn in enumerate(LAB_NAMES):
            data = (xml + (u"<!-- %d -->" % i)).encode("utf-8")
            wfile(os.path.join(d, fn), data)
            shas[fn] = hashlib.sha256(data).hexdigest()
        names = ms.load_dictionary(d, shas)
        if names != frozenset([u"jppfs_cor_Assets", u"jppfs_cor_Profit-1", u"jpcrp_cor_Text"]):
            out.append(u"辞書の名の読み方が違う: %s" % sorted(names))
        for what, mod in ((u"sha256 が違う", lambda fn: wfile(os.path.join(d, fn), b"x")), (u"file が無い", lambda fn: os.remove(os.path.join(d, fn)))):
            saved = rfile(os.path.join(d, LAB_NAMES[1]))
            mod(LAB_NAMES[1])
            try:
                ms.load_dictionary(d, shas)
                out.append(u"辞書が%sのに読む" % what)
            except ms.DictError:
                pass
            wfile(os.path.join(d, LAB_NAMES[1]), saved)
        bad = od(shas)
        bad[LAB_NAMES[0]] = u"0" * 64
        if not raises_(ms.DictError, ms.load_dictionary, d, bad):
            out.append(u"最初の file の sha256 を見ない")
        bad = od(shas)
        bad[LAB_NAMES[2]] = u"0" * 64
        if not raises_(ms.DictError, ms.load_dictionary, d, bad):
            out.append(u"最後の file の sha256 を見ない")
        # 本物の辞書の sha256(script の定数)・既定の場所は home の下
        if tuple(ms.LAB_FILES.values()) != LAB_SHAS:
            out.append(u"辞書の sha256 が封と違う")
        want_dir = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet-taxonomy", "2025-11-01")
        if ms.default_dictionary_dir() != want_dir:
            out.append(u"辞書の既定の場所が違う")
        # 作り物の辞書(名の file)
        nf = os.path.join(d, "n.json")
        wfile(nf, json.dumps([u"a_cor_b", u"c"]))
        if ms.load_names_file(nf) != frozenset([u"a_cor_b", u"c"]):
            out.append(u"名の file の読み方が違う")
        for what, data in ((u"並びでない", u"{}"), (u"字でない要素", u"[1]"), (u"JSON でない", u"x")):
            wfile(nf, data)
            if not raises_((ms.DictError, ValueError), ms.load_names_file, nf):
                out.append(u"名の file が%sのに読む" % what)
        # 既定の辞書を home の下の作り物で読む(HOME を差し替えた別 process。sha256 が合わなければ止まる)
        home = os.path.join(d, "home")
        for fn in LAB_NAMES:
            wfile(os.path.join(home, ".cache", "audit-core", "edinet-taxonomy", "2025-11-01", fn), b"fake")
        tf = os.path.join(d, "t.json")
        wfile(tf, dump(base()))
        p = subprocess.run([sys.executable, "-I", ms.SCRIPT_PATH, "--accept", tf], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=dict(os.environ, HOME=home), cwd=d)
        if p.returncode != 3 or p.stdout or b"DECLINE: " not in p.stderr:
            out.append(u"既定の辞書の sha256 が合わないのに止まらない(rc=%s)" % p.returncode)
        p = subprocess.run([sys.executable, "-I", ms.SCRIPT_PATH, "--accept", tf], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=dict(os.environ, HOME=os.path.join(d, "nohome")), cwd=d)
        if p.returncode != 3:
            out.append(u"辞書が無いのに止まらない(rc=%s)" % p.returncode)
    return out


def raises_(exc, fn, *a, **kw):
    try:
        fn(*a, **kw)
    except exc:
        return True
    return False


def accept_cli_problems(ms=None):
    u"""受け口の入口(``accept_main``・``main``)を、作り物の辞書で通す。別の process(``python3 -I``)でも 1 回通す。"""
    ms = ms or MS
    out = []
    with Temp() as d:
        nf = os.path.join(d, "n.json")
        wfile(nf, json.dumps(sorted(NAMES)))
        good, bad = os.path.join(d, "good.json"), os.path.join(d, "bad.json")
        wfile(good, dump(base()))
        wfile(bad, dump(edit(set_row(1, u"値", u"1,2"))))
        def run_in(args):
            o_, e_ = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(o_), contextlib.redirect_stderr(e_):
                rc = ms.accept_main(list(args))
            return rc, o_.getvalue(), e_.getvalue()
        rc, o, e = run_in(["--accept", good, "--names-file", nf])
        if rc != 0 or json.loads(o) != {u"受理": True, u"断り": []} or e:
            out.append(u"受理の出力が違う: %s %s" % (rc, o))
        rc, o, e = run_in(["--accept", bad, "--names-file", nf])
        j = json.loads(o)
        if rc != 0 or j[u"受理"] is not False or len(j[u"断り"]) != 1 or j[u"断り"][0] != {u"行": 1, u"欄": u"値", u"規則": u"R5", u"理由": ms.RULE_CONDS["R5"][1]} or list(j) != [u"受理", u"断り"]:
            out.append(u"断りの出力が違う: %s" % o)
        dd = os.path.join(d, "many")
        wfile(os.path.join(dd, "b.json"), dump(edit(set_row(1, u"対象", u"連結"))))
        wfile(os.path.join(dd, "a.json"), dump(base()))
        rc, o, e = run_in(["--accept-dir", dd, "--names-file", nf])
        j = json.loads(o, object_pairs_hook=od)
        if rc != 0 or list(j) != ["a.json", "b.json"] or j["a.json"][u"受理"] is not True or j["b.json"][u"断り"][0][u"規則"] != "R3":
            out.append(u"folder の出力が違う: %s" % o)
        for args in ([], ["--accept"], ["--accept", good, "extra"], ["--accept", good, "--names-file"], ["--other", good], ["--accept", os.path.join(d, "none.json"), "--names-file", nf],
                     ["--accept-dir", os.path.join(d, "none"), "--names-file", nf], ["--accept", good, "--names-file", os.path.join(d, "none.json")]):
            rc, o, e = run_in(args)
            want = 3 if args[-2:-1] == ["--names-file"] and not os.path.exists(args[-1]) else 64
            if rc != want or o:
                out.append(u"使い方の誤りの終わりの値が違う: %s rc=%s" % (args, rc))
        # 別の process(python3 -I)・何も無い場所(cwd は空の folder)
        empty = os.path.join(d, "empty")
        os.makedirs(empty)
        p = subprocess.run([sys.executable, "-I", ms.SCRIPT_PATH, "--accept", bad, "--names-file", nf], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=empty)
        if p.returncode != 0 or json.loads(p.stdout.decode("utf-8"))[u"断り"][0][u"規則"] != "R5" or os.listdir(empty):
            out.append(u"別の process の受け口が違う: rc=%s %s" % (p.returncode, p.stderr[-200:]))
    return out



# ======================================================================== 6. 作り物の書類 1 本の通し(起こす → 受け口 → 型から作る → 組む → 道具 → 数え方)
NAMES2 = frozenset([u"jppfs_cor_" + n for n in (u"Assets", u"Profit", u"Zero", u"Receivable", u"EPS", u"Shares", u"Ratio", u"Equity", u"Seg", u"NoScale", u"Carry", u"Inner", u"BOnly", u"X1",
                                                u"ComponentsOfEquityAxis", u"CapitalStockMember", u"ConsolidatedOrNonConsolidatedAxis", u"NonConsolidatedMember")] +
                   [u"jpcrp_cor_" + n for n in (u"Text", u"NilText", u"Nest", u"Text3")])
CPLAN = u"jpcrp030000-asr_E99991-000"


def v1_row_plan():
    u"""第 0 版の型の行の手の表(便 XM0 の封の門)に、第 1 版で入る 3 行(期の表に無い時点の Assets・単位が 他: の X1・期の表に無い時点の Text3)を、事実の並びの位置に足した手の表。"""
    rp = list(XG.ROW_PLAN)
    odd = (u"数", u"jppfs_cor:Assets", "instant", [u"2026-02-15"], u"既定", [], u"3", u"通貨:JPY", 0, 0, 1)
    x1 = (u"数", u"jppfs_cor:X1", "instant", [u"2026-03-31"], u"既定", [], u"5", u"他:iso4217:USD÷iso4217:JPY", 0, 0, 1)
    t3 = (u"文", u"jpcrp_cor:Text3", "instant", [u"2026-02-15"], u"既定", [], None, None, None, None, 1)
    return rp[:10] + [odd, x1] + rp[10:16] + [t3] + rp[16:]


def plan_type(plan):
    rows = []
    for kind, name, pk, per, target, dims, value, unit, shift, prec, _cnt in plan:
        p = per_i(per[0]) if pk == "instant" else per_d(per[0], per[1])
        d = [list(x) for x in dims]
        rows.append(num(name, p, target, d, value, unit, shift, prec) if kind == u"数" else txt(name, p, target, d))
    o = doc_of(rows, [(u"member", XG.MEM_A), (u"軸", XG.SEG)], **{u"提出者の識別子": u"E99991-000", u"識別子の scheme": u"http://example.org/id", u"当期の始まり": u"2025-04-01", u"当期の終わり": u"2026-03-31", u"提出日": u"2026-06-30"})
    return o


OUTSIDE_REASONS = [["b"], ["c"], ["c"], ["d"], ["e"], ["e"], ["e"], ["e"], ["f"], ["f"], ["f"]] + [["g"]] * 8 + [["h"], ["h"], ["d"], ["b"], ["g"], ["g"], ["e"]]


class Proc(object):
    u"""別の process の命令(型から作る命令・便 XP0 の組む命令)の作り物。呼ばれた引数・cwd を覚え、同じ process の中で入口の関数を走らせる。"""

    def __init__(self, ms, fail=None, hook=None):
        self.ms = ms
        self.calls = []
        self.fail = fail                      # (動詞, 何回目, (rc, 標準のエラー))
        self.hook = hook

    def __call__(self, cmd, cwd, timeout):
        verb = cmd[3]
        n = sum(1 for c in self.calls if c["verb"] == verb) + 1
        self.calls.append(dict(cmd=list(cmd), cwd=cwd, timeout=timeout, verb=verb, listing=sorted(os.listdir(cwd)) if os.path.isdir(cwd) else None))
        if self.fail is not None and self.fail[0] == verb and n == self.fail[1]:
            return self.fail[2][0], self.fail[2][1], False
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            rc = self.ms.build_main(list(cmd[3:])) if verb == "--build" else self.ms.prev().P.build_main(list(cmd[4:]))
        if self.hook is not None and rc == 0:
            self.hook(verb, n, cmd[-1] if verb != "--build" or "--names-file" not in cmd else cmd[5])
        return rc, err.getvalue(), False


class Cap(object):
    u"""受け口の検査(別の process)の作り物。入口の関数を同じ process の中で走らせ、標準出力を返す。"""

    def __init__(self, ms, fail=None):
        self.ms = ms
        self.calls = []
        self.fail = fail

    def __call__(self, cmd, cwd, timeout):
        self.calls.append(dict(cmd=list(cmd), cwd=cwd, timeout=timeout, many=cmd[3] == "--accept-dir", cwd_listing=sorted(os.listdir(cwd)) if os.path.isdir(cwd) else None))
        if self.fail is not None:
            return self.fail
        o_, e_ = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(o_), contextlib.redirect_stderr(e_):
            rc = self.ms.accept_main(list(cmd[3:]))
        return rc, o_.getvalue(), e_.getvalue(), False


def doc_run(ms, d, proc=None, cap=None, runner=None, a=None, b=None, keep=None, runner_cls=None, rkw=None, names=None, no=1):
    docs = os.path.join(d, "docs")
    os.makedirs(docs, exist_ok=True)
    zp = os.path.join(docs, "S2FAKE0%d.zip" % no)
    XG.make_doc(zp, no, a, b)
    tool, mv = X.make_tool(d)
    tmp = os.path.join(d, "tmp")
    os.makedirs(tmp, exist_ok=True)
    nf = os.path.join(d, "names.json")
    wfile(nf, json.dumps(sorted(names if names is not None else NAMES2)))
    r = runner or (runner_cls or XG.FactRunner)(mv, **(rkw or {}))
    proc = proc or Proc(ms)
    cap = cap or Cap(ms)
    rec = ms.process_doc(tool, zp, tmp, r, proc=proc, cap=cap, keep=keep, names_file=nf, names=names if names is not None else NAMES2)
    return rec, r, proc, cap, zp, tmp


def plain_rec(rec):
    o = json.loads(json.dumps(rec))
    return o, o.pop(u"秒")


def pair(n, t):
    return {u"数": n, u"文": t}


def doc_expect():
    u"""作り物の書類 1 本の、手で数えた値(便 XM0 の封の門の手の値 + 第 1 版で変わる所を理由から数えた)。"""
    zr = lambda: {r: 0 for r in RULE_IDS}                                                            # noqa: E731
    brk_keys = [u"作れた", u"断った", u"ちょうど 1 つ", u"別の規則で断った", u"断らなかった"]
    made_none = (u"N3a", u"R4a", u"R8a")
    brk = od()
    for k in BREAK_IDS_HAND:
        brk[k] = dict(zip(brk_keys, [0, 0, 0, 0, 0] if k in made_none else [1, 1, 0 if k in (u"N5a", u"N5b") else 1, 0, 0]))
    chg = od((k, {u"作れた": 1, u"通した": 1, u"断った": zr()}) for k in CHANGE_IDS_HAND)
    return {
        u"断った": False, u"断った段": u"", u"断った理由": u"",
        u"対象の fact": {u"数": 47, u"文": 7, u"隠し": 2, u"脚注": 1}, u"型に入った fact": pair(22, 6),
        u"型の外の fact": {u"理由ごと": {u"a": pair(0, 0), u"b": pair(1, 1), u"c": pair(2, 0), u"d": pair(2, 0), u"e": pair(5, 0), u"f": pair(3, 0), u"g": pair(10, 0), u"h": pair(2, 0)}, u"合計": pair(25, 1)},
        u"型の行": {u"数": 18, u"文": 5, u"2 つ以上の fact をまとめた行": 3, u"値が -0 の行": 1, u"期の表に無い期間の行": 2, u"他: の単位の行": 1},
        u"独自の名": {u"科目": 0, u"軸": 1, u"member": 1},
        u"名の数": {u"科目": {u"辞書の在る接頭辞": 18, u"辞書の無い _cor の接頭辞": 1, u"提出者別": 0}, u"軸": {u"辞書の在る接頭辞": 1, u"辞書の無い _cor の接頭辞": 0, u"提出者別": 1},
                  u"member": {u"辞書の在る接頭辞": 1, u"辞書の無い _cor の接頭辞": 0, u"提出者別": 1}},
        u"受け口": {u"受理した": True, u"断った": False, u"断りの数": 0, u"規則ごとの断りの数": zr(), u"規則ごとの断った書類": {r: False for r in RULE_IDS}, u"規則と欄ごとの断りの数": {}},
        u"比べ方 1": {u"属性が意味として同じ": False, u"文脈の名も同じ": False, u"違った fact": 1, u"属性ごとの違った fact": {u"scale": 1}},
        u"比べ方 2": {u"組めた": True, u"fact が意味として同じ": True, u"字も含めて行が同じ": False, u"鳴り方が同じ": True, u"2 回が同じ": True},
        u"壊し方": brk, u"形は合っているが中身が違う": chg}


def zero_of(ms):
    z = json.loads(json.dumps(ms.zero_rec()))
    z.pop(u"秒")
    return z


def derive_fake(ms, d, a=None, b=None):
    zp = os.path.join(d, "doc.zip")
    XG.make_doc(zp, 1, a, b)
    root = os.path.join(d, "made")
    v1, files = ms.derive_v1(ms.prev().B.load_package(zp), root)
    return zp, root, v1, files


def derive_problems(ms=None):
    ms = ms or MS
    out = []
    with Temp() as d:
        zp, root, v1, files = derive_fake(ms, d)
        if sorted(os.listdir(root)) != ["carry", "outside", "type"] or os.listdir(os.path.join(root, "type")) != ["type.json"] or os.listdir(os.path.join(root, "outside")) != ["outside.json"]:
            out.append(u"folder の中身が type・carry・outside に分かれていない: %s" % sorted(os.listdir(root)))
        text = rfile(os.path.join(root, "type", "type.json")).decode("utf-8")
        want = plan_type(v1_row_plan())
        got = parse_back(text)
        if got != want or list(got) != list(want) or text != dump(want):
            diffs = [i for i, (g, w) in enumerate(zip(got[u"行"], want[u"行"]), 1) if g != w]
            out.append(u"型の file が手の値と違う: 書類 %s 独自の名 %s 行の違い %s 行の数 %d/%d" % (got[u"書類"] == want[u"書類"], got[u"独自の名"] == want[u"独自の名"], diffs[:5], len(got[u"行"]), len(want[u"行"])))
        if [sorted(f["reasons"]) for f in v1["outside"]] != OUTSIDE_REASONS:
            out.append(u"型の外の理由が手の値と違う: %s" % [sorted(f["reasons"]) for f in v1["outside"]])
        o = json.loads(rfile(os.path.join(root, "outside", "outside.json")).decode("utf-8"))
        if [f["reasons"] for f in o["facts"]] != OUTSIDE_REASONS:
            out.append(u"型の外の file の理由が違う")
        if ms.carry_forbidden_v1(root):
            out.append(u"持ち込みに入れないものが在る: %s" % ms.carry_forbidden_v1(root))
        # 持ち込みに答え(型に入った fact の属性・文脈・単位の定義)が無い
        index = json.loads(rfile(os.path.join(root, "carry", "index.json")).decode("utf-8"))
        for item in index["htm"]:
            c = json.loads(rfile(os.path.join(root, "carry", item["carry"])).decode("utf-8"))
            for e in c["F"] + (c["H"]["hidden"] if c["H"] else []):
                if "row" not in e:
                    continue
                typed_ = (u"name", u"contextRef", u"unitRef", u"decimals", u"scale", u"sign", u"format", u"xsi:nil") if got[u"行"][e["row"]][u"種類"] == u"数" else (u"name", u"contextRef")
                if "attrs" in e or any(k in typed_ for k in e["carry"]):
                    out.append(u"型に入った fact の持ち込みに型の属性が在る")
                    break
            if c["H"] and any(r.get("type") != "ref" for r in c["H"]["resources"]):
                out.append(u"持ち込みに文脈か単位の定義が在る")
        if rr(ms, text, NAMES2):
            out.append(u"作り物の書類の型の file を受け口が断る: %s" % rr(ms, text, NAMES2))
        # 受け口に渡した型の file は答えを持たない: 型の外の file とは別の folder
        if os.path.exists(os.path.join(root, "type", "outside.json")):
            out.append(u"型の file の folder に型の外が在る")
    # 第 0 版で型の外だった理由 (a)(d) の読み: 期が書けない形・単位の定義が読めない
    with Temp() as d:
        a = XG.HTM_A_TEXT.replace(u'<xbrli:period>\n<xbrli:instant>2026-02-15</xbrli:instant>', u'<xbrli:period>\n<xbrli:forever/>')
        zp, root, v1, files = derive_fake(ms, d, a=a)
        r = [sorted(f["reasons"]) for f in v1["facts"] if f["attrs"].get("contextRef") == "OddInstant"]
        if r != [["a"], ["a", "d"], ["a"]]:
            out.append(u"書けない期の fact の理由が違う: %s" % r)
    with Temp() as d:
        a = XG.HTM_A_TEXT.replace(u'<xbrli:instant>2026-02-15</xbrli:instant>', u'<xbrli:instant>2026-02-30</xbrli:instant>')
        zp, root, v1, files = derive_fake(ms, d, a=a)
        r = [sorted(f["reasons"]) for f in v1["facts"] if f["attrs"].get("contextRef") == "OddInstant"]
        if r != [["a"], ["a", "d"], ["a"]]:
            out.append(u"在る日でない期の fact の理由が違う: %s" % r)
    with Temp() as d:
        # measure に空白が在る単位は 他: に書けず (d)
        a = XG.HTM_A_TEXT.replace(u'<xbrli:divide>\n<xbrli:unitNumerator>\n<xbrli:measure>iso4217:USD</xbrli:measure>', u'<xbrli:divide>\n<xbrli:unitNumerator>\n<xbrli:measure>iso4217: USD</xbrli:measure>')
        zp, root, v1, files = derive_fake(ms, d, a=a)
        r = [sorted(f["reasons"]) for f in v1["facts"] if f["attrs"].get("name") == u"jppfs_cor:X1"]
        if r != [["d"]]:
            out.append(u"measure に空白が在る単位が (d) にならない: %s" % r)
    with Temp() as d:
        # 単位の measure の順は字の昇順にして 他: の字にする(元の順に関わらない)
        a = XG.HTM_A_TEXT.replace(u'<xbrli:measure>iso4217:USD</xbrli:measure>\n</xbrli:unitNumerator>', u'<xbrli:measure>iso4217:USD</xbrli:measure>\n<xbrli:measure>iso4217:EUR</xbrli:measure>\n</xbrli:unitNumerator>')
        zp, root, v1, files = derive_fake(ms, d, a=a)
        r = [x[u"単位"] for x in parse_back(rfile(os.path.join(root, "type", "type.json")).decode("utf-8"))[u"行"] if x[u"科目"] == u"jppfs_cor:X1"]
        if r != [u"他:iso4217:EUR*iso4217:USD÷iso4217:JPY"]:
            out.append(u"他: の単位の字が昇順でない: %s" % r)
    return out



def diff_keys(got, want):
    return [k for k in want if got.get(k) != want[k]]


def doc_problems(ms=None):
    ms = ms or MS
    out = []
    with Temp() as d:
        keep = os.path.join(d, "keep")
        os.makedirs(keep)
        rec, r, proc, cap, zp, tmp = doc_run(ms, d, keep=keep)
        before = rfile(zp)
        got, secs = plain_rec(rec)
        want = doc_expect()
        if got != want:
            for k in diff_keys(got, want):
                out.append(u"書類 1 本の数が手で数えた値と違う: %s 手の値 %s ≠ %s" % (k, json.dumps(want[k], ensure_ascii=False)[:300], json.dumps(got.get(k), ensure_ascii=False)[:300]))
        if list(rec) != list(ms.zero_rec()) or not isinstance(secs[u"型から作る命令"], float):
            out.append(u"書類ごとの欄の並び・秒が違う")
        if [os.path.basename(c["zip"]) for c in r.calls] != ["orig.zip", "new.zip"]:
            out.append(u"道具の呼び出しが 2 回(元・組み直し)でない: %s" % [os.path.basename(c["zip"]) for c in r.calls])
        else:
            for c in r.calls:
                cmd = c["cmd"]
                if u"--validate" not in cmd or u"--facts" not in cmd or cmd[cmd.index(u"--factListCols") + 1] != ms.prev().T.FACT_COLS or u"http://www.xbrl.org/2003/arcrole/general-special" in cmd:
                    out.append(u"道具の掛け方が掛け方 A の字でない")
                    break
            if any(c["timeout"] != 600 for c in r.calls) or any(not c["existed"] for c in r.calls) or any(c["raw"][:2] != X.SEED or c["raw"][2:] != c["cmd"] for c in r.calls):
                out.append(u"時間の上限・zip・PYTHONHASHSEED=0 の前置きが違う")
        # 別の process の呼び方: 受け口 2 回(型の file・壊した file の folder)・型から作る 2 回・便 XP0 の組む 2 回
        if [(c["many"], c["cmd"][:4]) for c in cap.calls] != [(False, [sys.executable, "-I", ms.SCRIPT_PATH, "--accept"]), (True, [sys.executable, "-I", ms.SCRIPT_PATH, "--accept-dir"])]:
            out.append(u"受け口の呼び方が違う: %s" % [(c["many"], c["cmd"][:4]) for c in cap.calls])
        else:
            nf = os.path.join(d, "names.json")
            p0, p1 = cap.calls[0]["cmd"], cap.calls[1]["cmd"]
            if not p0[4].endswith(os.path.join("made", "type", "type.json")) or p0[5:] != ["--names-file", nf] or p1[5:] != ["--names-file", nf] or not p1[4].endswith("variants"):
                out.append(u"受け口に渡した file・folder・辞書が違う: %s %s" % (p0[4:], p1[4:]))
            if any(c["cwd"] != os.path.join(d, "tmp", os.listdir(os.path.join(d, "tmp"))[0] if os.path.isdir(os.path.join(d, "tmp")) and os.listdir(os.path.join(d, "tmp")) else "x", "cwd") and not c["cwd"].endswith("cwd") for c in cap.calls):
                out.append(u"受け口の cwd が空の folder でない")
            if any(c["cwd_listing"] != [] and c["cwd_listing"] is not None for c in cap.calls[:1]) or any(c["timeout"] != 600 for c in cap.calls):
                out.append(u"受け口の cwd の中身・時間の上限が違う")
            if any(os.path.dirname(os.path.dirname(a)) == os.path.join(d, "docs") or a.endswith(".zip") for c in cap.calls for a in c["cmd"][4:5]):
                out.append(u"受け口に元の包みの path を渡している")
        if [c["verb"] for c in proc.calls] != ["--build", "--build", "build", "build"]:
            out.append(u"別の process の呼び出しの並びが違う: %s" % [c["verb"] for c in proc.calls])
        else:
            for c in proc.calls[:2]:
                cmd = c["cmd"]
                if cmd[:4] != [sys.executable, "-I", ms.SCRIPT_PATH, "--build"] or cmd[6:] != ["--names-file", os.path.join(d, "names.json")] or not cmd[4].endswith("made") or os.path.basename(cmd[5]) not in ("man1", "man2"):
                    out.append(u"型から作る命令の呼び方が違う: %s" % cmd[3:])
                if c["listing"] != []:
                    out.append(u"型から作る命令の cwd が空でない: %s" % c["listing"])
            if any(c["timeout"] != 600 for c in proc.calls):
                out.append(u"型から作る命令の時間の上限が違う")
        if rfile(zp) != before:
            out.append(u"元の包みが変わった")
        if sorted(os.listdir(keep)) != ["made", "manuscript"] or sorted(os.listdir(os.path.join(keep, "made"))) != ["carry", "outside", "type"]:
            out.append(u"--keep の folder が違う: %s" % sorted(os.listdir(keep)))
        if os.listdir(os.path.join(d, "tmp")):
            out.append(u"使い捨ての場所が残っている")
    # 戻る版: 文脈・単位の id を作る規則の字に合わせ、scale の無い fact に scale を足す → 属性は全部同じ(文脈の名は期の表に無い時点の名が違う)
    with Temp() as d:
        rec, r, proc, cap, zp, tmp = doc_run(ms, d, a=XG.good_variant(XG.HTM_A_TEXT))
        c1 = plain_rec(rec)[0][u"比べ方 1"]
        c2 = plain_rec(rec)[0][u"比べ方 2"]
        if c1 != {u"属性が意味として同じ": True, u"文脈の名も同じ": False, u"違った fact": 0, u"属性ごとの違った fact": {}} or c2 != {u"組めた": True, u"fact が意味として同じ": True, u"字も含めて行が同じ": False, u"鳴り方が同じ": True, u"2 回が同じ": True}:
            out.append(u"戻る版の比べ方 1・2 が手の値と違う: %s %s" % (c1, c2))
    return out


R8BAD_FACT = u'<ix:nonFraction name="jppfs_cor:R8bad" contextRef="CurrentYearInstant" unitRef="JPY" decimals="-1" scale="0" format="ixt:numdotdecimal">15</ix:nonFraction>'
R9BAD_FACT = u'<ix:nonFraction name="jppfs_cor:R9bad" contextRef="CurrentYearInstant" unitRef="JPY" decimals="-1" scale="1" format="ixt:numdotdecimal">1.5</ix:nonFraction>'


def decline_problems(ms=None):
    ms = ms or MS
    out = []
    zero = zero_of(ms)
    HA = XG.HTM_A_TEXT

    def run_case(proc=None, cap=None, runner_cls=None, a=None, b=None, names=None, **rkw):
        with Temp() as d:
            rec, r, p, c, zp, tmp = doc_run(ms, d, proc=proc, cap=cap, runner_cls=runner_cls, rkw=rkw, a=a, b=b, names=names)
            return plain_rec(rec), r, p, c
    # ---- 起こす
    for what, kw, reason in ((u"当期の終わりの文脈が無い", dict(a=HA.replace(u"CurrentYearInstant", u"CurYI")), u"書類の決めが 1 通りに決まらない"),
                             (u"文脈の定義が無い fact", dict(a=HA.replace(u'contextRef="OddInstant"', u'contextRef="Nowhere"', 1)), u"文脈の定義が無い fact"),
                             (u"知らない ix の要素(落とす側の断り)", dict(a=HA + u"<ix:zzz>"), u"知らない ix の要素")):
        (got, _s), r, p, c = run_case(**kw)
        w = dict(zero, **{u"断った": True, u"断った段": u"起こす", u"断った理由": reason})
        if got != w or len(r.calls) != 1 or p.calls or c.calls:
            out.append(u"断り(起こす・%s)が違う: %s tool=%d proc=%d cap=%d" % (what, [(k, got[k]) for k in got if got[k] != w[k]][:3], len(r.calls), len(p.calls), len(c.calls)))
    # ---- 受け口(断りが付く)
    (got, secs), r, p, c = run_case(a=HA.replace(u"</p>\n</body>", R9BAD_FACT + u"</p>\n</body>"), names=NAMES2 | frozenset([u"jppfs_cor_R9bad"]))
    ws = dict(zero[u"受け口"], **{u"受理した": False, u"断った": True, u"断りの数": 1})
    ws[u"規則ごとの断りの数"] = dict(ws[u"規則ごとの断りの数"], R9=1)
    ws[u"規則ごとの断った書類"] = dict(ws[u"規則ごとの断った書類"], R9=True)
    ws[u"規則と欄ごとの断りの数"] = {u"R9/値": 1}
    if got[u"断った段"] != u"受け口" or got[u"断った理由"] != u"規則 R9" or got[u"受け口"] != ws or got[u"壊し方"] != zero[u"壊し方"] or got[u"比べ方 2"] != zero[u"比べ方 2"] or len(r.calls) != 1 or p.calls or len(c.calls) != 1:
        out.append(u"断り(受け口が断る)が違う: %s %s tool=%d proc=%d cap=%d" % (got[u"断った段"], got[u"断った理由"], len(r.calls), len(p.calls), len(c.calls)))
    if got[u"型に入った fact"][u"数"] != 23 or got[u"型の行"][u"数"] != 19 or secs[u"型から作る命令"] is not None:
        out.append(u"受け口が断る書類の型の数・秒が違う: %s %s" % (got[u"型に入った fact"], secs))
    # 規則が複数 → 規則の表の順
    (got, _s), r, p, c = run_case(a=HA.replace(u"</p>\n</body>", R9BAD_FACT + R8BAD_FACT + u"</p>\n</body>"), names=NAMES2 | frozenset([u"jppfs_cor_R9bad", u"jppfs_cor_R8bad"]))
    if got[u"断った理由"] != u"規則 R8,R9":
        out.append(u"断りの理由が規則の表の順の規則の並びでない: %s" % got[u"断った理由"])
    # ---- 受け口の process の失敗
    for what, fail, reason in ((u"0 でない終わりの値", (1, u"", u"x", False), u"受け口の検査が 0 でない終わりの値で終わった"), (u"JSON でない出力", (0, u"x", u"", False), u"受け口の検査の出力が JSON でない"),
                               (u"時間", (None, u"", u"", True), u"受け口の検査が時間の上限を超えた")):
        (got, _s), r, p, c = run_case(cap=Cap(ms, fail=fail))
        w = dict(zero, **{u"断った": True, u"断った段": u"受け口", u"断った理由": reason})
        for k in (u"対象の fact", u"型に入った fact", u"型の外の fact", u"型の行", u"独自の名", u"名の数"):
            w[k] = got[k]
        if got != w or len(c.calls) != 1 or p.calls:
            out.append(u"断り(受け口の process・%s)が違う: %s" % (what, [(k, got[k]) for k in got if got[k] != w[k]][:3]))
    # ---- 型から作る
    for what, proc, reason in ((u"断り", Proc(ms, fail=("--build", 1, (2, u"x\nDECLINE: 固定の理由\n"))), u"固定の理由"), (u"例外", Proc(ms, fail=("--build", 1, (1, u"ERROR\n"))), u"型から作る命令が 0 でない終わりの値で終わった"),
                               (u"使い方", Proc(ms, fail=("--build", 1, (64, u"使い方\n"))), u"型から作る命令が 0 でない終わりの値で終わった"),
                               (u"長い理由", Proc(ms, fail=("--build", 1, (2, u"DECLINE: " + u"あ" * 100 + u"\n"))), u"あ" * 80)):
        (got, secs), r, p, c = run_case(proc=proc)
        if got[u"断った段"] != u"型から作る" or got[u"断った理由"] != reason or len(r.calls) != 1 or len(p.calls) != 1 or secs[u"型から作る命令"] is None or got[u"比べ方 1"] != zero[u"比べ方 1"] or got[u"比べ方 2"] != zero[u"比べ方 2"]:
            out.append(u"断り(型から作る・%s)が違う: %s %s tool=%d proc=%d" % (what, got[u"断った段"], got[u"断った理由"], len(r.calls), len(p.calls)))
        if got[u"受け口"][u"受理した"] is not True or got[u"壊し方"][u"R5a"][u"作れた"] != 1 or len(c.calls) != 2:
            out.append(u"型から作る所で断る書類に、受け口・壊し方の数が残っていない")

    class TimeoutProc(Proc):
        def __call__(self, cmd, cwd, timeout):
            Proc.__call__(self, cmd, cwd, timeout)
            return None, u"", True
    (got, secs), r, p, c = run_case(proc=TimeoutProc(ms))
    if got[u"断った理由"] != u"型から作る命令が時間の上限を超えた" or got[u"断った段"] != u"型から作る":
        out.append(u"型から作る命令の時間切れの断りが違う")
    # ---- 組む
    (got, _s), r, p, c = run_case(proc=Proc(ms, fail=("build", 1, (2, u"DECLINE: 組めない\n"))))
    if got[u"断った段"] != u"組む" or got[u"断った理由"] != u"組めない" or len(r.calls) != 1 or [x["verb"] for x in p.calls] != ["--build", "--build", "build"] or got[u"比べ方 2"][u"組めた"]:
        out.append(u"断り(組む)が違う: %s %s" % (got[u"断った段"], got[u"断った理由"]))

    def drop_first(verb, n, o):
        if verb == "build" and n == 1:
            os.remove(os.path.join(o, sorted(os.listdir(o))[0]))
    (got, _s), r, p, c = run_case(proc=Proc(ms, hook=drop_first))
    if got[u"断った段"] != u"組む" or got[u"断った理由"] != u"出す folder の file の名が目次と合わない" or len(r.calls) != 1:
        out.append(u"出す folder の file の名が目次と合わないのに断らない: %s %s" % (got[u"断った段"], got[u"断った理由"]))
    # ---- 道具
    (got, _s), r, p, c = run_case(runner_cls=XG.FactRunner, stop_at=2)
    if got[u"断った段"] != u"道具" or got[u"断った理由"] != u"道具が組み直した包みで止まった" or len(r.calls) != 2 or got[u"比べ方 2"][u"組めた"] or got[u"比べ方 2"][u"2 回が同じ"] is not True:
        out.append(u"断り(道具)が違う: %s %s" % (got[u"断った段"], got[u"断った理由"]))
    (got, _s), r, p, c = run_case(runner_cls=XG.FactRunner, stop_at=1)
    if got[u"断った"] or len(r.calls) != 2:
        out.append(u"元だけが止まったのに断った")
    (got, _s), r, p, c = run_case(runner_cls=XG.FactRunner, stop_all=True)
    if got[u"断った"] or len(r.calls) != 2:
        out.append(u"元も止まったのに組み直しの止まりで断った(元が止まっていないときだけ断る)")
    # ---- 2 回が同じ
    for what, proc in ((u"2 回目の型から作る命令が断る", Proc(ms, fail=("--build", 2, (2, u"DECLINE: x\n")))), (u"2 回目の組む命令が断る", Proc(ms, fail=("build", 2, (2, u"DECLINE: x\n"))))):
        (got, _s), r, p, c = run_case(proc=proc)
        if got[u"比べ方 2"][u"2 回が同じ"] or not got[u"比べ方 2"][u"組めた"] or got[u"断った"]:
            out.append(u"%s のに 2 回が同じと言う" % what)

    def mangle(verb, n, o):
        if verb == "--build" and n == 2:
            wfile(os.path.join(o, "extra.txt"), b"x")
    (got, _s), r, p, c = run_case(proc=Proc(ms, hook=mangle))
    if got[u"比べ方 2"][u"2 回が同じ"] or got[u"断った"]:
        out.append(u"2 回目の型から作る命令が違う字を書くのに 2 回が同じと言う")
    # ---- 持ち込みに入れないものが在れば止まる
    saved = ms.carry_forbidden_v1
    ms.carry_forbidden_v1 = lambda root: [u"x"]
    try:
        with Temp() as d:
            if not stops(doc_run, ms, d):
                out.append(u"持ち込みに入れないものが在るのに止まらない")
    finally:
        ms.carry_forbidden_v1 = saved
    return out


# ======================================================================== 7. 型から作る(型の値を 1 つ変えると作った属性か定義が変わる)
def clone_root(src, dst):
    shutil.copytree(src, dst)


def write_type(root, obj):
    wfile(os.path.join(root, "type", "type.json"), dump(obj))


def load_type(root):
    return parse_back(rfile(os.path.join(root, "type", "type.json")).decode("utf-8"))


def attrs_list(ms, files):
    return [dict(a) for a in ms.prev().M.fact_attr_list(files)]


def defs_of(ms, files):
    M = ms.prev().M
    c, u = M.context_view([x[3] for x in files])
    return dict((k, M.canon_ctx(v)) for k, v in c.items()), dict((k, M.canon_unit(v)) for k, v in u.items())


def render_problems(ms=None):
    ms = ms or MS
    out = []
    ENT_ = (u"http://example.org/id", u"E99991-000")
    with Temp() as d:
        zp, root, v1, files = derive_fake(ms, d)
        base_files, _n, _t = ms.render_v1(root)
        battrs = attrs_list(ms, base_files)
        bctx, bunit = defs_of(ms, base_files)
        P0 = [i for i, a in enumerate(battrs) if a.get("name") == u"jppfs_cor:Assets" and a.get("contextRef") == u"CurrentYearInstant"]
        base_a0 = {"name": u"jppfs_cor:Assets", "contextRef": u"CurrentYearInstant", "unitRef": u"JPY", "decimals": u"-3", "scale": u"3", "format": u"ixt:numdotdecimal"}
        if len(P0) != 3 or any(battrs[i] != base_a0 for i in P0):
            out.append(u"作った属性の元が手の値と違う: %s %s" % (P0, [battrs[i] for i in P0[:1]]))
            return out
        # 作った定義の手の値
        want_cur = (ENT_[0], ENT_[1], ((u"xbrli:instant", u"2026-03-31"),), ())
        if bctx.get(u"CurrentYearInstant") != want_cur or bctx.get(u"At20260215Instant") != (ENT_[0], ENT_[1], ((u"xbrli:instant", u"2026-02-15"),), ()):
            out.append(u"作った文脈の定義・期の名(At…)が手の値と違う")
        if bunit.get(u"JPY") != ((u"iso4217:JPY",), None) or bunit.get(u"U0001") != ((), ((u"iso4217:USD",), (u"iso4217:JPY",))):
            out.append(u"作った単位の定義(他: の U0001)が手の値と違う: %s" % sorted(bunit))
        a_odd = [a for a in battrs if a.get("contextRef") == u"At20260215Instant"]
        a_x1 = [a for a in battrs if a.get("name") == u"jppfs_cor:X1"]
        if len(a_odd) != 2 or a_x1 != [{"name": u"jppfs_cor:X1", "contextRef": u"CurrentYearInstant", "unitRef": u"U0001", "decimals": u"0", "scale": u"0", "format": u"ixt:numdotdecimal"}]:
            out.append(u"期の表に無い時点・他: の単位の fact の属性が手の値と違う: %s %s" % (a_odd, a_x1))
        typ = load_type(root)

        def trial(fn, label, expect0, others_same=True, ctx=None, unit=None):
            r2 = os.path.join(d, "t_" + str(abs(hash(label))))
            clone_root(root, r2)
            t2 = copy.deepcopy(typ)
            fn(t2)
            write_type(r2, t2)
            try:
                f2, _n2, _t2 = ms.render_v1(r2)
            except BaseException as exc:                    # noqa: BLE001
                out.append(u"%s: 作る途中で例外 %s" % (label, type(exc).__name__))
                return
            na = attrs_list(ms, f2)
            c2, u2 = defs_of(ms, f2)
            if len(na) != len(battrs):
                out.append(u"%s: fact の数が変わった" % label)
                return
            for i in P0:
                if na[i] != expect0:
                    out.append(u"%s: 行 1 の fact の属性が手の値と違う: %s ≠ %s" % (label, expect0, na[i]))
                    break
            if others_same and any(na[i] != battrs[i] for i in range(len(na)) if i not in P0):
                out.append(u"%s: 行 1 以外の fact の属性が変わった" % label)
            if ctx is not None and (c2.get(ctx[0]) != ctx[1]):
                out.append(u"%s: 作った文脈の定義が手の値と違う: %s" % (label, c2.get(ctx[0])))
            if unit is not None and (u2.get(unit[0]) != unit[1]):
                out.append(u"%s: 作った単位の定義が手の値と違う: %s" % (label, u2.get(unit[0])))
            if others_same and ctx is None and unit is None and (c2 != bctx or u2 != bunit):
                out.append(u"%s: 定義まで変わった" % label)
        e0 = lambda **kw: dict(base_a0, **kw)                                                        # noqa: E731
        trial(lambda t: t[u"行"][0].__setitem__(u"値", u"-1234000"), u"値 負", e0(sign=u"-"))
        trial(lambda t: t[u"行"][0].__setitem__(u"値", u"1235000"), u"値 別の数(属性は変わらない)", base_a0)
        trial(lambda t: t[u"行"][0].update({u"値": NONE_V, u"表示の位": None, u"精度": None}), u"値 無い", {"name": u"jppfs_cor:Assets", "contextRef": u"CurrentYearInstant", "unitRef": u"JPY", "xsi:nil": u"true"})
        trial(lambda t: t[u"行"][0].__setitem__(u"単位", u"通貨:USD"), u"単位 USD", e0(unitRef=u"USD"), unit=(u"USD", ((u"iso4217:USD",), None)))
        trial(lambda t: t[u"行"][0].__setitem__(u"単位", u"株"), u"単位 株", e0(unitRef=u"shares"), unit=(u"shares", ((u"xbrli:shares",), None)))
        trial(lambda t: t[u"行"][0].__setitem__(u"単位", u"純数"), u"単位 純数", e0(unitRef=u"pure"), unit=(u"pure", ((u"xbrli:pure",), None)))
        trial(lambda t: t[u"行"][0].__setitem__(u"単位", u"通貨:JPY÷株"), u"単位 円÷株", e0(unitRef=u"JPYPerShares"), unit=(u"JPYPerShares", ((), ((u"iso4217:JPY",), (u"xbrli:shares",)))))
        # 他: の単位は書類の中の 他: の字の昇順に U0001 から(他:a*b < 他:iso4217:USD÷iso4217:JPY)
        r2 = os.path.join(d, "t_other")
        clone_root(root, r2)
        t2 = copy.deepcopy(typ)
        t2[u"行"][0][u"単位"] = u"他:a*b"
        write_type(r2, t2)
        f2, _n2, _t2 = ms.render_v1(r2)
        na = attrs_list(ms, f2)
        c2, u2 = defs_of(ms, f2)
        if [na[i].get("unitRef") for i in P0] != [u"U0001"] * 3 or [a for a in na if a.get("name") == u"jppfs_cor:X1"][0]["unitRef"] != u"U0002" or u2.get(u"U0001") != ((u"a", u"b"), None) or u2.get(u"U0002") != ((), ((u"iso4217:USD",), (u"iso4217:JPY",))):
            out.append(u"他: の単位の id が字の昇順の U0001 から振られていない: %s" % sorted(u2))
        trial(lambda t: t[u"行"][0].__setitem__(u"表示の位", 6), u"表示の位", e0(scale=u"6"))
        trial(lambda t: t[u"行"][0].__setitem__(u"精度", -6), u"精度", e0(decimals=u"-6"))
        trial(lambda t: t[u"行"][0].__setitem__(u"科目", u"jppfs_cor:Profit"), u"科目", e0(name=u"jppfs_cor:Profit"))
        trial(lambda t: t[u"行"][0].__setitem__(u"期間", per_i(u"2025-03-31")), u"期間 前期", e0(contextRef=u"Prior1YearInstant"), ctx=(u"Prior1YearInstant", (ENT_[0], ENT_[1], ((u"xbrli:instant", u"2025-03-31"),), ())))
        trial(lambda t: t[u"行"][0].__setitem__(u"期間", per_i(u"2026-06-30")), u"期間 提出日", e0(contextRef=u"FilingDateInstant"), ctx=(u"FilingDateInstant", (ENT_[0], ENT_[1], ((u"xbrli:instant", u"2026-06-30"),), ())))
        trial(lambda t: t[u"行"][0].__setitem__(u"期間", per_i(u"2026-02-14")), u"期間 表に無い時点", e0(contextRef=u"At20260214Instant"), ctx=(u"At20260214Instant", (ENT_[0], ENT_[1], ((u"xbrli:instant", u"2026-02-14"),), ())))
        trial(lambda t: t[u"行"][0].__setitem__(u"期間", per_d(u"2025-04-02", u"2026-03-31")), u"期間 表に無い期間", e0(contextRef=u"From20250402To20260331Duration"),
              ctx=(u"From20250402To20260331Duration", (ENT_[0], ENT_[1], ((u"xbrli:startDate", u"2025-04-02"), (u"xbrli:endDate", u"2026-03-31")), ())))
        trial(lambda t: t[u"行"][0].__setitem__(u"期間", per_d(u"2025-04-01", u"2026-03-31")), u"期間 当期", e0(contextRef=u"CurrentYearDuration"),
              ctx=(u"CurrentYearDuration", (ENT_[0], ENT_[1], ((u"xbrli:startDate", u"2025-04-01"), (u"xbrli:endDate", u"2026-03-31")), ())))
        trial(lambda t: t[u"行"][0].__setitem__(u"期間", per_d(u"2024-04-01", u"2025-03-31")), u"期間 前期の期間", e0(contextRef=u"Prior1YearDuration"),
              ctx=(u"Prior1YearDuration", (ENT_[0], ENT_[1], ((u"xbrli:startDate", u"2024-04-01"), (u"xbrli:endDate", u"2025-03-31")), ())))
        trial(lambda t: t[u"行"][0].__setitem__(u"対象", u"個別"), u"対象", e0(contextRef=u"CurrentYearInstant_NonConsolidatedMember"), others_same=False,
              ctx=(u"CurrentYearInstant_NonConsolidatedMember", (ENT_[0], ENT_[1], ((u"xbrli:instant", u"2026-03-31"),), ((CONS_AXIS, IND_MEMBER),))))
        trial(lambda t: t[u"行"][0].__setitem__(u"次元", [[CA, CM]]), u"次元", e0(contextRef=u"CurrentYearInstant_CapitalStockMember"), others_same=False,
              ctx=(u"CurrentYearInstant_CapitalStockMember", (ENT_[0], ENT_[1], ((u"xbrli:instant", u"2026-03-31"),), ((CA, CM),))))
        trial(lambda t: (t[u"行"][0].__setitem__(u"期間", per_i(u"2026-02-14")), t[u"行"][0].__setitem__(u"対象", u"個別")), u"期間 表に無い時点と個別", e0(contextRef=u"At20260214Instant_NonConsolidatedMember"), others_same=False)
        # 提出者別の member の字(接頭辞 + 局所名)と 並び(個別が先・軸の昇順)
        trial(lambda t: (t[u"行"][0].__setitem__(u"次元", [[XG.SEG, XG.MEM_A], [CA, CM]]), t[u"行"][0].__setitem__(u"対象", u"個別")), u"次元 2 つと個別",
              e0(contextRef=u"CurrentYearInstant_NonConsolidatedMember_" + CPLAN + u"AMember_CapitalStockMember"), others_same=False)
        # 文に替える(行の鍵が変わる: 属性は名と文脈だけ)
        def to_text(t):
            for k in (u"値", u"単位", u"表示の位", u"精度"):
                del t[u"行"][0][k]
            t[u"行"][0][u"種類"] = u"文"
        trial(to_text, u"種類 文", {"name": u"jppfs_cor:Assets", "contextRef": u"CurrentYearInstant"})
        # 書類の決め
        trial(lambda t: t[u"書類"].__setitem__(u"当期の終わり", u"2026-04-30"), u"書類 当期の終わり", e0(contextRef=u"At20260331Instant"), others_same=False)
        r2 = os.path.join(d, "t_ident")
        clone_root(root, r2)
        t2 = copy.deepcopy(typ)
        t2[u"書類"][u"提出者の識別子"], t2[u"書類"][u"識別子の scheme"] = u"E00001-000", u"http://example.org/other"
        write_type(r2, t2)
        try:
            ms.render_v1(r2)
            out.append(u"型の外の定義が作った定義と同じ id で中身が違うのに断らない(書類の識別子を替えた)")
        except ms.Refuse as exc:
            if exc.reason != u"型の外の定義が作った定義と同じ id で中身が違う":
                out.append(u"id の重なりの断りの理由が違う: %s" % exc.reason)
        # 提出日が当期の終わりと同じなら CurrentYear が先
        trial(lambda t: (t[u"書類"].__setitem__(u"提出日", u"2026-03-31"), t[u"行"][0].__setitem__(u"期間", per_i(u"2026-03-31"))), u"提出日 = 期末は CurrentYear", base_a0, others_same=False)
    return out


# ======================================================================== 8. 型から作る命令は受け口が断った file からは作らない・元の包みが無い場所で動く
def build_wiring_problems(ms=None):
    ms = ms or MS
    out = []

    def run_build(argv):
        o_, e_ = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(o_), contextlib.redirect_stderr(e_):
            rc = ms.build_main(list(argv))
        return rc, o_.getvalue(), e_.getvalue()
    with Temp() as d:
        zp, root, v1, files = derive_fake(ms, d)
        nf = os.path.join(d, "n.json")
        wfile(nf, json.dumps(sorted(NAMES2)))
        o1 = os.path.join(d, "out1")
        rc, so, se = run_build(["--build", root, o1, "--names-file", nf])
        if rc != 0 or "index.json" not in os.listdir(o1):
            out.append(u"受理された型の file から作れない: rc=%s %s" % (rc, se[-200:]))
        # 断った file からは作らない(R9 を破った型)
        typ = load_type(root)
        bad = copy.deepcopy(typ)
        bad[u"行"][0][u"値"] = u"1234500"
        r2 = os.path.join(d, "bad")
        clone_root(root, r2)
        write_type(r2, bad)
        calls = []
        saved_r, saved_w = ms.render_v1, ms.prev().M.P.write_folder
        ms.render_v1 = lambda f: calls.append(("render", f)) or saved_r(f)
        ms.prev().M.P.write_folder = lambda *a, **k: calls.append(("write", a)) or saved_w(*a, **k)
        try:
            o2 = os.path.join(d, "out2")
            rc, so, se = run_build(["--build", r2, o2, "--names-file", nf])
            if rc != 2 or os.path.exists(o2) or calls or se.strip() != u"DECLINE: 受け口が断った(規則 R9)" or so:
                out.append(u"受け口が断った型の file から作る(か断りの字が違う): rc=%s %s calls=%d" % (rc, se.strip(), len(calls)))
            # 2 つの規則 → 規則の表の順
            bad2 = copy.deepcopy(typ)
            bad2[u"行"][0][u"値"] = u"1,2"
            bad2[u"行"][1][u"対象"] = u"連結"
            r3 = os.path.join(d, "bad2")
            clone_root(root, r3)
            write_type(r3, bad2)
            rc, so, se = run_build(["--build", r3, os.path.join(d, "out3"), "--names-file", nf])
            if rc != 2 or se.strip() != u"DECLINE: 受け口が断った(規則 R3,R5)" or calls:
                out.append(u"断った規則の並びが表の順でない: %s" % se.strip())
            # 型の file が JSON でない・無い
            wfile(os.path.join(r3, "type", "type.json"), b"x")
            rc, so, se = run_build(["--build", r3, os.path.join(d, "out4"), "--names-file", nf])
            if rc != 2 or calls or os.path.exists(os.path.join(d, "out4")):
                out.append(u"壊れた型の file から作る")
            os.remove(os.path.join(r3, "type", "type.json"))
            rc, so, se = run_build(["--build", r3, os.path.join(d, "out5"), "--names-file", nf])
            if rc != 1 or calls:
                out.append(u"型の file が無いときの終わりの値が違う: %s" % rc)
        finally:
            ms.render_v1, ms.prev().M.P.write_folder = saved_r, saved_w
        # 使い方・辞書
        for args, want in (([], 64), (["--build"], 64), (["--build", root], 64), (["--build", root, o1, "extra"], 64), (["--build", root, os.path.join(d, "o6"), "--names-file"], 64),
                           (["--other", root, os.path.join(d, "o7")], 64), (["--build", root, os.path.join(d, "o8"), "--names-file", os.path.join(d, "none.json")], 3)):
            rc, so, se = run_build(args)
            if rc != want:
                out.append(u"型から作る命令の終わりの値が違う: %s rc=%s" % (args[1:], rc))
        # 受け口と同じ辞書を見る(辞書に無い名の型は断る)
        wfile(os.path.join(d, "empty.json"), b"[]")
        rc, so, se = run_build(["--build", root, os.path.join(d, "o9"), "--names-file", os.path.join(d, "empty.json")])
        if rc != 2 or not se.startswith(u"DECLINE: 受け口が断った(規則 N2"):
            out.append(u"空の辞書で型の file を断らない: %s" % se[-100:])
        # 元の包みが無い場所(包み・答えを消した空の場所)で、別の process(python3 -I)から作れる・断った file からは作らない
        clean = os.path.join(d, "clean")
        os.makedirs(os.path.join(clean, "cwd"))
        shutil.copytree(root, os.path.join(clean, "made"))
        os.remove(zp)
        shutil.rmtree(os.path.join(d, "made"))
        p = subprocess.run([sys.executable, "-I", ms.SCRIPT_PATH, "--build", os.path.join(clean, "made"), os.path.join(clean, "out"), "--names-file", nf], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           cwd=os.path.join(clean, "cwd"))
        if p.returncode != 0 or "index.json" not in os.listdir(os.path.join(clean, "out")) or os.listdir(os.path.join(clean, "cwd")):
            out.append(u"元の包みが無い場所で型から作る命令が動かない: rc=%s %s" % (p.returncode, p.stderr[-200:]))
        write_type(os.path.join(clean, "made"), bad)
        p = subprocess.run([sys.executable, "-I", ms.SCRIPT_PATH, "--build", os.path.join(clean, "made"), os.path.join(clean, "out2"), "--names-file", nf], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           cwd=os.path.join(clean, "cwd"))
        if p.returncode != 2 or os.path.exists(os.path.join(clean, "out2")) or b"DECLINE: " not in p.stderr:
            out.append(u"別の process でも断った file から作る: rc=%s" % p.returncode)
    return out


ACCEPT_FUNCS = ("default_dictionary_dir", "load_dictionary", "load_names_file", "parse_date", "refusal", "parse_json", "good_id", "split_name", "check_name", "check_unit", "period_key",
                "multiple_of_precision", "check_row", "check_custom", "used_names", "check_doc", "check_pairs", "check_text", "sort_refusals", "check_bytes", "check_safe", "result_of", "emit_json_text", "accept_main")
ACCEPT_DENY = ("prev", "load_sibling", "_PREV", "derive_v1", "process_doc", "render_v1", "write_folders", "reanalyze", "exec_accept", "run_variants", "make_variants", "run_capture", "exec_build",
               "build_main", "types", "importlib", "subprocess", "shutil", "tempfile", "sys_modules", "compile", "exec", "eval", "__import__", "M", "P", "B", "T", "V", "W", "SimpleNamespace")
STDLIB_TOP = ("__future__", "argparse", "collections", "copy", "datetime", "decimal", "hashlib", "importlib", "io", "json", "os", "re", "shutil", "subprocess", "sys", "tempfile", "time", "types")
NETWORK = ("http", "socket", "ssl", "urllib", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx", "glob", "csv", "zipfile", "openpyxl")
HARNESS_WORDS = ("apply_edits(", "inject_with_profile(", "run_doc(", "mutate(", "IJ.select(", "inject(", "inject_doc(", "verify_document(", "verify_external(")
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS")
NOT_COPIED = ("analyze", "period_name", "unit_form", "context_id", "context_def", "compare_attrs", "run_facts", "normalize_rows", "merge_outside", "unit_map_of", "load_manuscript", "carried_attrs",
              "sum_nested_like", "peel_tables", "load_package", "select_docs", "check_clean", "write_exclusive", "unit_from_form", "member_str", "years_before", "canon_ctx", "canon_unit", "target_facts")
CALLED_ATTRS = ("analyze", "period_name", "unit_form", "context_id", "context_def", "unit_from_form", "merge_outside", "compare_attrs", "run_facts", "normalize_rows", "unit_map_of", "load_manuscript",
                "carried_attrs", "peel_tables", "load_package", "write_package", "write_folder", "read_tree", "expected_names", "rebuilt_pack", "exec_build", "facts_same", "sounds_same", "secret_of",
                "order_sha256", "select_docs", "write_record", "check_clean", "dumps", "sum_nested", "check_tool", "dev_docs")


def iso_ast_problems(src=None):
    u"""受け口の検査の関数は、前の便の script・元の包みを読む名を使わない。この script の頭の import は標準の library だけ。"""
    src = src if src is not None else read(SCRIPT_REL)
    tree = ast.parse(src)
    out = []
    funcs = dict((n.name, n) for n in tree.body if isinstance(n, ast.FunctionDef))
    for fn in ACCEPT_FUNCS:
        if fn not in funcs:
            out.append(u"受け口の関数が無い: %s" % fn)
            continue
        f = funcs[fn]
        docs_ = set([id(f.body[0].value)]) if f.body and isinstance(f.body[0], ast.Expr) and isinstance(f.body[0].value, ast.Constant) else set()
        for n in ast.walk(f):
            if id(n) in docs_:
                continue
            if isinstance(n, ast.Name) and n.id in ACCEPT_DENY:
                out.append(u"%s が使ってはいけない名を使う: %s" % (fn, n.id))
            if isinstance(n, ast.Attribute) and n.attr in ACCEPT_DENY:
                out.append(u"%s が使ってはいけない名を使う: %s" % (fn, n.attr))
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                out.append(u"%s の中で import している" % fn)
    f = funcs.get("accept_main")
    if f is not None:
        opens = [n for n in ast.walk(f) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "open"]
        if len(opens) != 2:
            out.append(u"accept_main が開く file が 型の file・folder の中の file の 2 つでない: %d" % len(opens))
    for n in tree.body:
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name.split(".")[0] not in STDLIB_TOP:
                    out.append(u"頭の import が標準の library でない: %s" % a.name)
        elif isinstance(n, ast.ImportFrom):
            if (n.module or u"").split(".")[0] not in STDLIB_TOP:
                out.append(u"頭の import が標準の library でない: %s" % n.module)
        elif isinstance(n, (ast.Expr, ast.Assign, ast.AugAssign)):
            for c in ast.walk(n):
                if isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id in ("prev", "load_sibling"):
                    out.append(u"頭の文が前の便の script を読む")
    return out


def iso_problems(ms=None):
    ms = ms or MS
    out = []
    import builtins as _b
    with Temp() as d:
        nf, good = os.path.join(d, "n.json"), os.path.join(d, "g.json")
        wfile(nf, json.dumps(sorted(NAMES)))
        wfile(good, dump(base()))
        many = os.path.join(d, "many")
        wfile(os.path.join(many, "a.json"), dump(base()))
        wfile(os.path.join(many, "b.json"), dump(edit(set_row(1, u"対象", u"連結"))))
        # 前の便の script を読めない状態(prev が呼ばれたら落ちる)で動く・開く file は決めた file だけ
        saved_prev, real_open = ms.prev, _b.open
        opened = []

        def boom():
            raise AssertionError(u"prev() が呼ばれた")
        ms.prev = boom
        _b.open = lambda p, *a, **k: (opened.append(str(p)), real_open(p, *a, **k))[1]
        try:
            for argv, want_open in ((["--accept", good, "--names-file", nf], [nf, good]), (["--accept-dir", many, "--names-file", nf], [nf, os.path.join(many, "a.json"), os.path.join(many, "b.json")])):
                del opened[:]
                o_, e_ = io.StringIO(), io.StringIO()
                code = None
                with contextlib.redirect_stdout(o_), contextlib.redirect_stderr(e_):
                    try:
                        ms.main(list(argv))
                    except SystemExit as exc:
                        code = exc.code
                if code != 0 or sorted(opened) != sorted(want_open) or not o_.getvalue():
                    out.append(u"受け口が決めた file 以外を開く・出力が無い: %s %s" % (argv[0], opened))
        except BaseException as exc:                    # noqa: BLE001
            out.append(u"受け口が前の便の script を読む・例外: %s" % type(exc).__name__)
        finally:
            ms.prev, _b.open = saved_prev, real_open
        # 別の process の import(-X importtime): 受け口の process は zipfile・csv・engine を import しない
        p = subprocess.run([sys.executable, "-I", "-X", "importtime", ms.SCRIPT_PATH, "--accept", good, "--names-file", nf], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=d)
        imported = set(re.findall(r"\| ([A-Za-z0-9_\.]+)\s*$", p.stderr.decode("utf-8", "replace"), re.M))
        bad = sorted(m for m in imported if m.split(".")[0] in ("zipfile", "csv", "adapters", "audit_core", "core", "openpyxl") or m.startswith("_xm0") or m.startswith("_xj0"))
        if p.returncode != 0 or bad:
            out.append(u"受け口の process が標準の library 以外を import している: rc=%s %s" % (p.returncode, bad))
        if not {"argparse", "json", "hashlib"} <= imported:
            out.append(u"importtime の読み方が違う(標準の library が見えない)")
    return out


def import_problems(src=None):
    u"""script の import・前の便の関数の呼び方・写し・注入の仕掛けの規準の字。"""
    src = src if src is not None else read(SCRIPT_REL)
    tree = ast.parse(src)
    out = []
    for n in ast.walk(tree):
        names = []
        if isinstance(n, ast.Import):
            names = [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            names = [(n.module or u"")]
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("__import__", "eval", "exec"):
            out.append(u"動的な import・eval・exec の呼び出し")
        for nm in names:
            top = nm.split(".")[0]
            if top in NETWORK:
                out.append(u"許さない module を import している: %s" % nm)
            elif top not in STDLIB_TOP:
                out.append(u"許す一覧に無い module(engine を含む): %s" % nm)
    attrs = [(n.value.id, n.attr) for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)]
    if ("os", "environ") in attrs or ("os", "getenv") in attrs:
        out.append(u"環境変数を読んでいる")
    all_attr = set(n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute))
    for a in CALLED_ATTRS:
        if a not in all_attr:
            out.append(u"前の便の関数 %s を呼んでいない" % a)
    funcs = dict((n.name, n) for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    for fn in NOT_COPIED:
        if fn in funcs:
            out.append(u"前の便の %s を script が自分で定義している(写している)" % fn)
    sub_users = []
    for f in funcs.values():
        for n in ast.walk(f):
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "subprocess":
                sub_users.append(f.name)
    if sorted(set(sub_users)) != ["run_capture"]:
        out.append(u"subprocess を使う関数が run_capture だけでない: %s" % sorted(set(sub_users)))
    doc = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant):
            doc.add(id(n.body[0].value))
    consts = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc:
            v = n.value
            if u".env" in v or u"dotenv" in v or u"API_KEY" in v or u"anthropic" in v.lower():
                out.append(u"鍵・.env・API の字が在る")
            if any(s in v for s in HARNESS_WORDS):
                out.append(u"注入の仕掛けの規準の字が在る: %s" % v)
    if "_xj0_input_type_2026_11_22" not in consts:
        out.append(u"前の便の script を読む名が一意の名でない")
    for n in funcs:
        if any(w.rstrip(u"(").split(u".")[-1] == n for w in HARNESS_WORDS):
            out.append(u"関数の名が注入の仕掛けの規準の字に当たる: %s" % n)
    return out


def reserved_problems(rel=GATE_REL, base_=ROOT):
    out = []
    with open(os.path.join(base_, rel), encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    for n, line in enumerate(lines, 1):
        if any(line.startswith(p) for p in RESERVED_PREFIXES):
            out.append(u"%s:%d" % (rel, n))
    return out


ORDER_SNIPPET = (
    "import importlib.util, os, sys\n"
    "root = sys.argv[1]\n"
    "files = {'xm0': ('_gate_order_xm0', 'measure/xbrl_input_type_2026-11-22.py'), 'xk0': ('_gate_order_xk0', 'measure/xbrl_type_carryover_2026-11-22.py'), "
    "'xe0': ('_gate_order_xe0', 'measure/xbrl_company_excel_2026-11-22.py'), 'xj0': ('_gate_order_xj0', 'measure/xbrl_input_type_v1_2026-11-23.py')}\n"
    "mods = {}\n"
    "for key in sys.argv[2:]:\n"
    "    name, rel = files[key]\n"
    "    spec = importlib.util.spec_from_file_location(name, os.path.join(root, rel))\n"
    "    m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m); mods[key] = m\n"
    "k = mods['xj0']\n"
    "assert k.prev().M.analyze and k.prev().P.write_folder and k.prev().W.Stop and k.Refuse is not k.prev().M.Refuse\n"
    "assert k.check_text and k.derive_v1 and k.process_doc\n"
    "print('ok')\n")


def order_import_problems():
    u"""前の便の script と自分を並べて読む順を入れ替えても、動く(sys.modules の名を上書きして赤にならない)。別の process で確かめる。"""
    out = []
    for order in (("xm0", "xj0"), ("xj0", "xm0"), ("xe0", "xk0", "xj0", "xm0"), ("xj0", "xk0", "xe0", "xm0"), ("xk0", "xj0"), ("xj0",)):
        rc = subprocess.run([sys.executable, "-c", ORDER_SNIPPET, ROOT] + list(order), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, cwd=ROOT,
                            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        if rc.returncode != 0 or rc.stdout.strip() != "ok":
            out.append(u"読む順 %s で動かない: %s" % (u"→".join(order), rc.stderr.strip().splitlines()[-1:] or rc.stdout))
    return out



# ======================================================================== 9. 記録(作り物の書類 3 本)
STEMS = XG.STEMS
ORDER_SHA = XG.ORDER_SHA


def record_args(d, ms, runner=None, count=3, proc=None, cap=None, **kw):
    docs = os.path.join(d, "docs")
    os.makedirs(docs)
    XG.make_docs_dir(docs, count, XG.DOC_VARIANTS)
    tool, mv = X.make_tool(os.path.join(d, "tool"))
    tmp = os.path.join(d, "tmp")
    os.makedirs(tmp)
    nf = os.path.join(d, "names.json")
    wfile(nf, json.dumps(sorted(NAMES2)))
    runner = runner or XG.FactRunner(mv)
    proc = proc or Proc(ms)
    cap = cap or Cap(ms)
    args = dict(want=count, runner=runner, tmp_root=tmp, sha_reader=None, dev_count=1, proc=proc, cap=cap, names_file=nf, want_sha=hashlib.sha256(X.MV_P).hexdigest())
    args.update(kw)
    return tool, docs, runner, tmp, args


def run_problems(ms=None):
    ms = ms or MS
    out = []
    with Temp() as d:
        keep = os.path.join(d, "keep")
        os.makedirs(keep)
        tool, docs, runner, tmp, args = record_args(d, ms)
        progress = []
        rec, secret = ms.build_record(tool, docs, progress=progress.append, keep=keep, **dict(args))
        if len(runner.calls) != 2 + 2 + 1 or len(args["proc"].calls) != 4 + 4 or len(args["cap"].calls) != 2 + 2:
            out.append(u"道具・別の process の呼び出しの数が違う: tool=%d proc=%d cap=%d" % (len(runner.calls), len(args["proc"].calls), len(args["cap"].calls)))
        if len(progress) != 3 or not progress[0].startswith(u"doc 1/3("):
            out.append(u"書類ごとの進みを出さない: %s" % progress)
        mat = rec[u"材料"]
        if (mat[u"書類の本数"], mat[u"書類の file 名の並びの sha256"], mat[u"開発の 5 本の番号"], mat[u"標準ラベルの file の sha256"], mat[u"道具の版"], mat[u"規則の年"], mat[u"時間の上限(秒)"]) != (
                3, ORDER_SHA, [1], list(LAB_SHAS), u"2.47.5", u"EDINET-2026", 600):
            out.append(u"材料の欄が手で数えた値と違う: %s" % dict(mat))
        if list(rec)[:6] != [u"seal", u"封の commit", u"step", u"この script の sha256", u"材料", u"script の決めの字"] or rec[u"封の commit"] != SEAL_COMMIT_SHORT or rec[u"seal"] != SEAL_REL:
            out.append(u"記録の頭の欄が違う")
        if [dd[u"番号"] for dd in rec[u"書類"]] != [1, 2, 3] or [dd[u"断った"] for dd in rec[u"書類"]] != [False, False, True] or rec[u"書類"][2][u"断った段"] != u"起こす":
            out.append(u"書類の番号・断った書類が違う")
        t = rec[u"集計"]
        dev, prod, allg = t[u"開発の 5 本"], t[u"本番だけの 2 本"], t[u"全部"]
        if (dev[u"書類"], prod[u"書類"], allg[u"書類"], prod[u"断った書類"], dev[u"断った書類"], allg[u"数"][u"比べ方 2"][u"fact が意味として同じ"], allg[u"数"][u"受け口"][u"受理した"]) != (1, 2, 3, 1, 0, 2, 2):
            out.append(u"集計が手で数えた値と違う")
        if allg[u"数"][u"対象の fact"][u"数"] != 47 * 2 or allg[u"数"][u"型の外の fact"][u"合計"][u"数"] != 25 * 2 or prod[u"断った段と理由ごと"][u"起こす"] != {u"書類の決めが 1 通りに決まらない": 1}:
            out.append(u"全部の対象の fact の数・断りの理由が手で数えた値と違う(断った書類は数えない)")
        j = rec[[k for k in rec if k.startswith(u"予測の判定に要る数")][0]]
        want_j = [(u"書類", 1), (u"分母", 2)]
        vals = list(j.values())
        if list(vals[0].items()) != want_j or vals[1][u"規則の数"] != 0 or list(vals[2].values()) != [26, 54] or list(vals[3].values()) != [0, 2] or list(vals[4].values()) != [1, 1] or \
                list(vals[5].values()) != [41, 41, 0, 0] or list(vals[6].values()) != [39, 41] or [vals[7][u"通した"], vals[7][u"作れた"]] != [6, 6] or list(vals[8].values()) != [1, 19] or list(vals[9].values()) != [1, 2]:
            out.append(u"予測の判定に要る数が手で数えた値と違う: %s" % json.dumps(j, ensure_ascii=False)[:600])
        if len(j) != 10 or [k[:6] for k in j] != [u"XJ0-%d " % i if i < 10 else u"XJ0-10" for i in range(1, 11)][:10]:
            out.append(u"判定の欄の並びが違う: %s" % [k[:7] for k in j])
        if rec[u"この script の sha256"] != sha_of(SCRIPT_REL) and ms is MS:
            out.append(u"記録の script の sha256 が違う")
        text = ms.prev().M.dumps(rec)
        for leak in STEMS + [u"E9999", u"S2OTHER1", u".xbrl", u".htm", u".xsd", u"Alpha", u"Beta", u"Gamma", u"http", u"Assets", u"BOnly", u"Profit", u"OtherEntity", u"OddInstant", u"PublicDoc", u"1,234",
                             u"index.json", u"Prior1Year", u"注記", u"2026-03-31", u"2025-04-01", u"SegAxis", u"ixt:numcomma", u"At2026", u"U0001", u"jpcrp030000"]:
            if leak in text:
                out.append(u"記録に材料の字が在る: %s" % leak)
        if set(secret[3]) != set([u"E9999%d" % i for i in (1, 2, 3)]) or list(secret[2]) != STEMS:
            out.append(u"secret の docID・EDINET コードが違う")
        if os.listdir(tmp):
            out.append(u"使い捨ての場所が残っている")
        if sorted(os.listdir(keep)) != [u"doc01", u"doc02", u"doc03"] or sorted(os.listdir(os.path.join(keep, "doc01"))) != [u"made", u"manuscript"] or os.listdir(os.path.join(keep, "doc03")) != []:
            out.append(u"--keep の書類ごとの folder が違う")
        ms.verify_record(rec, text, want=3, dev_count=1)
        r2 = XG.FactRunner(runner.mv_path)
        a2 = dict(args, runner=r2, want=67, proc=Proc(ms), cap=Cap(ms))
        if not stops(ms.build_record, tool, docs, **a2) or r2.calls or a2["proc"].calls or a2["cap"].calls:
            out.append(u"書類が 67 本でないのに止まらない(か掛けた)")
    return out


def verify_problems(ms=None):
    ms = ms or MS
    out = []
    with Temp() as d:
        tool, docs, runner, tmp, args = record_args(d, ms)
        rec, secret = ms.build_record(tool, docs, **dict(args))
        ms.verify_record(rec, want=3, dev_count=1)

        def broken(fn):
            r = json.loads(json.dumps(rec), object_pairs_hook=od)
            fn(r)
            return r

        def bump(path, delta=1):
            def f(r):
                o = r
                for k in path[:-1]:
                    o = o[k]
                o[path[-1]] += delta
            return f
        D1 = lambda r: r[u"書類"][0]                                                                  # noqa: E731
        cases = [
            (u"書類の本数", lambda r: r[u"書類"].pop()), (u"番号", lambda r: r[u"書類"][1].__setitem__(u"番号", 5)), (u"欄の並び", lambda r: r[u"書類"][0].__setitem__(u"余り", 1)),
            (u"断った段が空なのに断った", lambda r: r[u"書類"][0].__setitem__(u"断った", True)), (u"断った理由が空", lambda r: r[u"書類"][2].__setitem__(u"断った理由", u"")),
            (u"断った段が知らない段", lambda r: r[u"書類"][2].__setitem__(u"断った段", u"x")),
            (u"受理かつ断り", lambda r: D1(r)[u"受け口"].__setitem__(u"断った", True)), (u"断りの数と断った", lambda r: D1(r)[u"受け口"].__setitem__(u"断りの数", 1)),
            (u"規則ごとの数の合計", lambda r: D1(r)[u"受け口"][u"規則ごとの断りの数"].__setitem__(u"R9", 1)),
            (u"規則ごとの断った書類", lambda r: D1(r)[u"受け口"][u"規則ごとの断った書類"].__setitem__(u"R9", True)),
            (u"規則と欄ごとの合計", lambda r: D1(r)[u"受け口"][u"規則と欄ごとの断りの数"].__setitem__(u"R9/値", 1)),
            (u"受け口を通っていない書類が後ろの段で断られている", lambda r: (r[u"書類"][0].__setitem__(u"断った", True), r[u"書類"][0].__setitem__(u"断った段", u"組む"), r[u"書類"][0].__setitem__(u"断った理由", u"x"),
                                                                   r[u"書類"][0][u"受け口"].__setitem__(u"受理した", False))),
            (u"断った書類に比べ方 2", lambda r: r[u"書類"][2][u"比べ方 2"].__setitem__(u"組めた", True)),
            (u"受理していない書類に壊し方", lambda r: (r[u"書類"][2][u"壊し方"][u"R5a"].__setitem__(u"作れた", 1))),
            (u"対象の fact と型の合計", bump([u"書類", 0, u"型に入った fact", u"数"])), (u"理由ごとが合計より多い", lambda r: D1(r)[u"型の外の fact"][u"理由ごと"][u"b"].__setitem__(u"数", 99)),
            (u"壊し方の数の合計", lambda r: D1(r)[u"壊し方"][u"R5a"].__setitem__(u"断った", 0)), (u"壊し方のちょうど 1 つ", lambda r: D1(r)[u"壊し方"][u"N5a"].__setitem__(u"ちょうど 1 つ", 1)),
            (u"変え方の通した", lambda r: D1(r)[u"形は合っているが中身が違う"][u"Q1"].__setitem__(u"通した", 0)), (u"変え方の断りと通した", lambda r: D1(r)[u"形は合っているが中身が違う"][u"Q1"][u"断った"].__setitem__(u"R9", 1)),
            (u"集計", lambda r: r[u"集計"][u"全部"].__setitem__(u"書類", 99)), (u"判定に要る数", lambda r: list(r[[k for k in r if k.startswith(u"予測の判定に要る数")][0]].values())[0].__setitem__(u"書類", 99)),
            (u"禁止の字(docID)", lambda r: r[u"限界"].append(u"S100ABCD")), (u"禁止の字(URI)", lambda r: r[u"限界"].append(u"http://example.org/x")), (u"禁止の字(file の名)", lambda r: r[u"限界"].append(u"0101010_honbun.htm"))]
        for what, fn in cases:
            if not stops(ms.verify_record, broken(fn), None, 3, 1):
                out.append(u"記録の形・合計が壊れているのに止まらない: %s" % what)
        # write_record: 排他・書く前に検査・書いた後に検査
        p = os.path.join(d, "rec", "r.json")
        ms.write_record(p, rec, secret)
        if not os.path.exists(p) or stops(ms.verify_record, json.loads(rfile(p).decode("utf-8"), object_pairs_hook=od), rfile(p).decode("utf-8"), 3, 1):
            out.append(u"書いた記録が検査を通らない")
        before = rfile(p)
        if not stops(ms.write_record, p, rec, secret) or rfile(p) != before:
            out.append(u"記録が在るのに書き直す(排他でない)")
        p2 = os.path.join(d, "rec", "leak.json")
        leak = broken(lambda r: r[u"限界"].append(u"S100ABCD"))
        if not stops(ms.write_record, p2, leak, secret) or os.path.exists(p2):
            out.append(u"禁止の字が在る記録を書く")
        # check: 記録が無ければ止まる・在れば通る(root を替えて)
        root = os.path.join(d, "root")
        if not stops(ms.check, root=root, say=lambda *a: None, want=3, dev_count=1):
            out.append(u"記録が無いのに --check が止まらない")
        wfile(os.path.join(root, RECORD_REL), before)
        got = ms.check(root=root, say=lambda *a: None, want=3, dev_count=1)
        if got != json.loads(before.decode("utf-8"), object_pairs_hook=od):
            out.append(u"--check が記録を返さない")
        # run: 書く場所の既定は root の RECORD_REL
        root2 = os.path.join(d, "root2")
        r3 = XG.FactRunner(runner.mv_path)
        tool2, docs2, runner2, tmp2, args2 = record_args(os.path.join(d, "x2"), ms) if os.makedirs(os.path.join(d, "x2")) is None else (None,) * 5
        said = []
        rec2 = ms.run(tool2, root=root2, docs=docs2, say=said.append, **dict(args2))
        if not os.path.exists(os.path.join(root2, RECORD_REL)) or len(said) != 1 or not said[0].startswith(u"-> input_type_v1_2026-11-23.json(書類 3)"):
            out.append(u"run が既定の場所に記録を書かない: %s" % said)
    return out


def dev_run_problems(ms=None):
    ms = ms or MS
    out = []
    with Temp() as d:
        tool, docs, runner, tmp, args = record_args(d, ms, count=7)
        said = []
        per = ms.dev_run(tool, docs_dir=docs, runner=runner, tmp_root=tmp, say=said.append, proc=args["proc"], cap=args["cap"], names_file=args["names_file"], want_sha=args["want_sha"])
        if len(per) != 5 or len(runner.calls) != 4 * 2 + 1 or sum(1 for s in said if s.startswith(u"doc ")) != 5:
            out.append(u"開発の 5 本だけを掛けない: %d %d" % (len(per), len(runner.calls)))
        if [dd[u"番号"] for dd in per] != [1, 2, 3, 4, 5]:
            out.append(u"開発の番号が違う")
        if any(not s for s in said):
            out.append(u"出力が空")
        if not said[-1].startswith(u"{"):
            out.append(u"§2 の数を出さない")
    return out


# ======================================================================== 10. 指示書
EX_NAMES = frozenset(["jppfs_cor_ExampleAssets", "jppfs_cor_ExampleReceivable", "jpcrp_cor_ExampleShares", "jpcrp_cor_ExampleText"])         # 門が持つ作り物の辞書
EXP = u"example-prefix_E00000-000"


def ex_ok():
    u"""指示書の例 1(受理される file)の手の値。"""
    cur = per_d(u"2030-04-01", u"2031-03-31")
    return od([(u"型の版", u"1"), (u"書類", od([(u"提出者の識別子", u"E00000-000"), (u"識別子の scheme", u"http://example.org/id"), (u"当期の始まり", u"2030-04-01"), (u"当期の終わり", u"2031-03-31"),
                                          (u"提出日", u"2031-06-30")])),
               (u"独自の名", [one(u"member", EXP + u":ExampleSegmentMember"), one(u"科目", EXP + u":ExampleCustomItem"), one(u"軸", EXP + u":ExampleSegmentAxis")]),
               (u"行", [num(u"jppfs_cor:ExampleAssets", per_i(u"2031-03-31"), u"既定", [], u"1234000", JPY, 3, -3), num(u"jppfs_cor:ExampleAssets", per_i(u"2030-03-31"), u"既定", [], u"987000", JPY, 3, -3),
                       num(u"jpcrp_cor:ExampleShares", per_i(u"2031-03-31"), u"既定", [], u"1000", SHARES, 0, 0),
                       num(EXP + u":ExampleCustomItem", cur, u"個別", [[EXP + u":ExampleSegmentAxis", EXP + u":ExampleSegmentMember"]], u"12.5", JPYPS, 0, 1),
                       num(u"jppfs_cor:ExampleReceivable", per_i(u"2031-03-31"), u"既定", [], NONE_V, JPY, None, None), txt(u"jpcrp_cor:ExampleText", cur)])])


def ex_bad():
    o = ex_ok()
    o[u"行"][0][u"科目"] = u"jppfs_cor:ExampleAssetz"
    o[u"行"][1][u"値"] = u"987,000"
    o[u"行"][2][u"精度"] = u"0"
    o[u"独自の名"] = [e for e in o[u"独自の名"] if e[u"名"] != EXP + u":ExampleCustomItem"]
    return o


EX_BAD_WANT = [("N2", 0, 1, u"科目"), ("N3", 0, 4, u"科目"), ("R5", 1, 2, u"値"), ("R7", 0, 3, u"精度")]
FIELD_SECTIONS = 9


def instruction_problems(ms=None, text=None):
    ms = ms or MS
    out = []
    text = text if text is not None else read(INSTRUCTION_REL)
    if text != ms.instruction_text():
        out.append(u"指示書の字が script の書き出しと違う")
    fences = re.findall(r"```json\n(.*?)\n```", text, re.S)
    if len(fences) != 3:
        out.append(u"指示書の json の塊が 3 つでない: %d" % len(fences))
        return out
    ok_t, bad_t, ref_t = fences
    ok_o = json.loads(ok_t, object_pairs_hook=od)
    if ok_o != ex_ok() or ok_t + u"\n" != dump(ex_ok()):
        out.append(u"指示書の例 1 が手の値と違う")
    got = rr(ms, ok_t + u"\n", EX_NAMES)
    if got:
        out.append(u"指示書の例 1 を受け口が断る(作り物の辞書の下): %s" % got)
    if json.loads(bad_t, object_pairs_hook=od) != ex_bad() or bad_t + u"\n" != dump(ex_bad()):
        out.append(u"指示書の例 2 が手の値と違う")
    got = rr(ms, bad_t + u"\n", EX_NAMES)
    if not same(got, EX_BAD_WANT):
        out.append(u"指示書の例 2 の断りが文書の字どおりでない: %s" % got)
    real = ms.check_text(bad_t + u"\n", EX_NAMES)
    ref = json.loads(ref_t, object_pairs_hook=od)
    if ref != od([(u"受理", False), (u"断り", [od(x) for x in real])]) or list(ref) != [u"受理", u"断り"] or ref_t != json.dumps(ref, ensure_ascii=False, indent=1):
        out.append(u"指示書の断りの並びが受け口の出力と違う")
    for x in ref[u"断り"]:
        rid = x[u"規則"]
        if x[u"理由"] not in SEAL_RULES[rid][1]:
            out.append(u"指示書の断りの理由が封の表の字でない: %s" % rid)
    # 規則の表は封の表と同じ
    for rid, (place, cond) in SEAL_RULES.items():
        rows = [ln for ln in text.splitlines() if ln.startswith(u"| %s | " % rid)]
        if len(rows) != 1 or tuple(rows[0][2:-2].split(u" | ", 2))[1:] != (place, cond):
            out.append(u"指示書の規則の表の行が封と違う: %s" % rid)
    for w in (u"型の版", u"書類", u"独自の名", u"提出者の識別子", u"識別子の scheme", u"当期の始まり", u"当期の終わり", u"提出日", u"科目", u"期間", u"対象", u"次元", u"値", u"単位", u"表示の位", u"精度", u"種類"):
        if u"`%s`" % w not in text:
            out.append(u"指示書に欄の名が無い: %s" % w)
    if text.count(u"- こう書く:") != FIELD_SECTIONS or text.count(u"- こう書かない:") != FIELD_SECTIONS or text.count(u"- 断られた時の直し方:") != FIELD_SECTIONS + 1:
        out.append(u"指示書の「こう書く」「こう書かない」「断られた時の直し方」の数が欄の数と合わない: %d %d %d" % (text.count(u"- こう書く:"), text.count(u"- こう書かない:"), text.count(u"- 断られた時の直し方:")))
    if re.search(r"S100[0-9A-Z]{4}", text) or u"jpcrp030000" in text or u"jppfs_cor:Assets" in text or re.search(r"\b20[0-9]{2}年", text):
        out.append(u"指示書に実在の書類・名の字が在る")
    for rid in RULE_IDS:
        if text.count(rid) < 1:
            out.append(u"指示書に規則の番号が無い: %s" % rid)
    if not text.startswith(u"# ") or u"\n## 7. 作り物の例\n" not in text:
        out.append(u"指示書の見出しが違う")
    return out


def sample_instruction_text(ms=None):
    return (ms or MS).instruction_text()


def write_instruction_problems(ms=None):
    ms = ms or MS
    out = []
    with Temp() as d:
        p = os.path.join(d, "i.md")
        got = ms.write_instruction(p)
        if got != p or rfile(p).decode("utf-8") != ms.instruction_text():
            out.append(u"--write-instruction が書き出しの字を書かない")
        o_ = io.StringIO()
        with contextlib.redirect_stdout(o_):
            ms.main(["--write-instruction", os.path.join(d, "j.md")])
        if rfile(os.path.join(d, "j.md")).decode("utf-8") != ms.instruction_text() or o_.getvalue().strip() != os.path.join(d, "j.md"):
            out.append(u"main の --write-instruction が違う")
        # 既定の書き出し先は docs/INPUT_TYPE_V1_INSTRUCTION_2026-11-23.md
        saved = ms.write_instruction
        seen = []
        ms.write_instruction = lambda path=None: seen.append(path) or u"x"
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                ms.main(["--write-instruction"])
        finally:
            ms.write_instruction = saved
        if seen != [None]:
            out.append(u"--write-instruction の既定の path の渡し方が違う: %s" % seen)
        if os.path.join(ms.ROOT, ms.INSTRUCTION_REL) != os.path.join(ROOT, INSTRUCTION_REL):
            out.append(u"指示書の既定の path が違う")
    return out


def main_dispatch_problems(ms=None):
    u"""入口の分岐: ``--make``・``--break``・``--check``・``--run``・``--dev``・使い方。作り物の関数に差し替えて、引数が正しく渡るか。"""
    ms = ms or MS
    out = []
    log = []
    saved = dict((k, getattr(ms, k)) for k in ("run_make", "run_break", "check", "run", "dev_run", "accept_main", "build_main"))
    ms.run_make = lambda folder, zp: log.append(("make", folder, zp))
    ms.run_break = lambda folder, nf=None, say=print: log.append(("break", folder, nf))
    ms.check = lambda root=None, **kw: log.append(("check", root))
    ms.run = lambda tool, root=None, docs=None, keep=None, names_file=None, **kw: log.append(("run", tool, root, docs, keep, names_file))
    ms.dev_run = lambda tool, docs_dir=None, keep=None, names_file=None, **kw: log.append(("dev", tool, docs_dir, keep, names_file))
    ms.accept_main = lambda argv: log.append(("accept", list(argv))) or 0
    ms.build_main = lambda argv: log.append(("build", list(argv))) or 0
    try:
        with Temp() as d:
            cases = [(["--make", "F", "--zip", "Z"], [("make", "F", "Z")]), (["--break", "F", "--names-file", "N"], [("break", "F", "N")]), (["--check", "--root", "R"], [("check", "R")]),
                     (["--run", "--tool-p", "T", "--root", "R", "--docs", "D", "--names-file", "N"], [("run", "T", "R", "D", None, "N")]),
                     (["--dev", "--tool-p", "T", "--docs", "D", "--names-file", "N"], [("dev", "T", "D", None, "N")]),
                     (["--accept", "f", "--names-file", "n"], [("accept", ["--accept", "f", "--names-file", "n"])]), (["--accept-dir", "d"], [("accept", ["--accept-dir", "d"])]),
                     (["--build", "a", "b"], [("build", ["--build", "a", "b"])])]
            for argv, want in cases:
                del log[:]
                code = None
                try:
                    ms.main(list(argv))
                except SystemExit as exc:
                    code = exc.code
                if log != want or (argv[0] in ("--accept", "--accept-dir", "--build") and code != 0):
                    out.append(u"入口の分岐が違う: %s → %s" % (argv, log))
            for argv in (["--make", "F"], ["--run"], ["--dev"]):
                del log[:]
                if not stops(ms.main, list(argv)) or log:
                    out.append(u"必要な引数が無いのに止まらない: %s" % argv)
            keep = os.path.join(d, "k")
            os.makedirs(keep)
            wfile(os.path.join(keep, "x"), b"x")
            if not stops(ms.main, ["--dev", "--tool-p", "T", "--keep", keep]):
                out.append(u"--keep の場所が空でないのに止まらない")
            del log[:]
            with contextlib.redirect_stdout(io.StringIO()) as buf:
                ms.main([])
            if log:
                out.append(u"引数が無いとき何かを走らせた")
    finally:
        for k, v in saved.items():
            setattr(ms, k, v)
    return out



# ======================================================================== 10. 数え方・判定に要る数(手で作った書類ごとの数 4 本から、手で数えた §2 の数)
def put(rec, path, value):
    o = rec
    for k in path[:-1]:
        o = o[k]
    o[path[-1]] = value


def hand_entries(ms):
    u"""書類ごとの数 4 本(番号 1 = 開発・2〜4 = 本番)。値は近くの数と重ならない作り物。"""
    A, B, C, D = (ms.zero_rec() for _ in range(4))
    for rec, n in ((A, 1), (B, 2), (C, 3), (D, 4)):
        rec[u"番号"] = n
    # 1 本目(開発の側。本番の数に入らないことを見る)
    put(A, [u"受け口", u"受理した"], True)
    put(A, [u"対象の fact", u"数"], 100)
    put(A, [u"型の外の fact", u"合計", u"数"], 50)
    put(A, [u"型の行", u"期の表に無い期間の行"], 9)
    put(A, [u"秒", u"型から作る命令"], 12.3)
    # 2 本目
    put(B, [u"受け口", u"受理した"], True)
    put(B, [u"受け口", u"規則ごとの断った書類", u"R9"], True)
    put(B, [u"対象の fact", u"数"], 4)
    put(B, [u"対象の fact", u"文"], 2)
    put(B, [u"型の外の fact", u"合計", u"文"], 2)
    put(B, [u"型の行", u"期の表に無い期間の行"], 3)
    put(B, [u"型の行", u"他: の単位の行"], 1)
    put(B, [u"比べ方 2", u"組めた"], True)
    for k, v in ((u"作れた", 2), (u"断った", 1), (u"別の規則で断った", 1)):
        put(B, [u"壊し方", u"R5a", k], v)
    put(B, [u"壊し方", u"R5a", u"ちょうど 1 つ"], 1)
    put(B, [u"壊し方", u"N5a", u"作れた"], 1)
    put(B, [u"壊し方", u"N5a", u"断った"], 1)
    put(B, [u"形は合っているが中身が違う", u"Q1", u"作れた"], 1)
    put(B, [u"形は合っているが中身が違う", u"Q1", u"通した"], 1)
    put(B, [u"形は合っているが中身が違う", u"Q2", u"作れた"], 1)
    put(B, [u"形は合っているが中身が違う", u"Q2", u"断った", u"R9"], 1)
    put(B, [u"名の数", u"科目", u"辞書の無い _cor の接頭辞"], 4)
    put(B, [u"名の数", u"科目", u"辞書の在る接頭辞"], 6)
    put(B, [u"名の数", u"科目", u"提出者別"], 2)
    put(B, [u"秒", u"型から作る命令"], 2.2)
    # 3 本目(断った書類)
    put(C, [u"断った"], True)
    put(C, [u"断った段"], u"起こす")
    put(C, [u"断った理由"], u"x")
    # 4 本目
    put(D, [u"受け口", u"受理した"], True)
    put(D, [u"受け口", u"規則ごとの断った書類", u"R9"], True)
    put(D, [u"受け口", u"規則ごとの断った書類", u"R5"], True)
    put(D, [u"対象の fact", u"数"], 7)
    put(D, [u"対象の fact", u"文"], 1)
    put(D, [u"型の行", u"期の表に無い期間の行"], 1)
    put(D, [u"比べ方 2", u"組めた"], True)
    put(D, [u"比べ方 2", u"fact が意味として同じ"], True)
    put(D, [u"壊し方", u"R5a", u"作れた"], 1)
    put(D, [u"壊し方", u"R5a", u"断らなかった"], 1)
    put(D, [u"形は合っているが中身が違う", u"Q1", u"作れた"], 1)
    put(D, [u"形は合っているが中身が違う", u"Q1", u"断った", u"R5"], 1)
    put(D, [u"形は合っているが中身が違う", u"Q3", u"作れた"], 1)
    put(D, [u"形は合っているが中身が違う", u"Q3", u"通した"], 1)
    put(D, [u"名の数", u"科目", u"辞書の無い _cor の接頭辞"], 1)
    put(D, [u"名の数", u"科目", u"辞書の在る接頭辞"], 3)
    put(D, [u"秒", u"型から作る命令"], 3.4)
    return [od(e.items()) for e in (A, B, C, D)]


def count_problems(ms=None):
    ms = ms or MS
    out = []
    ents = hand_entries(ms)
    tot = ms.totals_of(ents, 1)
    keys = list(tot)
    if keys != [u"開発の 5 本", u"本番だけの 3 本", u"全部"]:
        out.append(u"集計の組の名が違う: %s" % keys)
        return out
    dev, prod, allg = tot[keys[0]], tot[keys[1]], tot[keys[2]]
    if (dev[u"書類"], prod[u"書類"], allg[u"書類"], dev[u"断った書類"], prod[u"断った書類"], allg[u"断った書類"]) != (1, 3, 4, 0, 1, 1):
        out.append(u"書類の数・断った書類の数が違う")
    if (dev[u"型の外の fact が 0 の書類"], prod[u"型の外の fact が 0 の書類"], allg[u"型の外の fact が 0 の書類"]) != (0, 1, 1):
        out.append(u"型の外の fact が 0 の書類が違う(断った書類は数えない・数の側だけで 0 にしない): %s" % (prod[u"型の外の fact が 0 の書類"],))
    if (prod[u"期の表に無い期間の行が在る書類"], prod[u"他: の単位の行が在る書類"], dev[u"期の表に無い期間の行が在る書類"], allg[u"期の表に無い期間の行が在る書類"]) != (2, 1, 1, 3):
        out.append(u"期の表に無い期間・他: の単位の行が在る書類の数が違う")
    if (dev[u"型から作る命令の秒の合計"], prod[u"型から作る命令の秒の合計"], allg[u"型から作る命令の秒の合計"]) != (12.3, 5.6, 17.9):
        out.append(u"秒の合計が違う: %s %s %s" % (dev[u"型から作る命令の秒の合計"], prod[u"型から作る命令の秒の合計"], allg[u"型から作る命令の秒の合計"]))
    if list(prod[u"断った段と理由ごと"]) != list(ms.STAGES) or prod[u"断った段と理由ごと"][u"起こす"] != {u"x": 1} or any(prod[u"断った段と理由ごと"][s] for s in ms.STAGES[1:]):
        out.append(u"断った段と理由ごとが違う: %s" % json.dumps(prod[u"断った段と理由ごと"], ensure_ascii=False))
    want_keys = [k for k in ms.zero_rec() if k not in (u"番号", u"断った段", u"断った理由", u"秒")]
    if list(prod[u"数"]) != want_keys or list(prod[u"数"]) != [k for k in want_keys if k != u"番号"]:
        out.append(u"集計の 数 の欄が違う(番号・断った段・断った理由・秒は入れない): %s" % list(prod[u"数"]))
    z = prod[u"数"]
    if z[u"受け口"][u"受理した"] != 2 or z[u"受け口"][u"規則ごとの断った書類"][u"R9"] != 2 or z[u"受け口"][u"規則ごとの断った書類"][u"R5"] != 1 or z[u"断った"] != 1:
        out.append(u"受け口の数の合計が違う")
    # 判定に要る数(手で数えた値。分母は本番だけ)
    j = ms.judged(tot)
    vals = list(j.values())
    want = [
        [(u"書類", 2), (u"分母", 3)],
        [(u"規則の数", 2)],
        [(u"fact", 2), (u"分母(対象の fact)", 14)],
        [(u"書類", 1), (u"分母", 3)],
        [(u"書類", 1), (u"分母(受理した書類)", 2)],
        [(u"断った", 2), (u"作れた", 4), (u"別の規則で断った", 1), (u"断らなかった", 1)],
        [(u"ちょうど 1 つ", 1), (u"分母(作れた)", 4)],
        [(u"通した", 2), (u"作れた", 4)],
        [(u"名", 5), (u"分母(科目の名)", 16)],
        [(u"書類", 2), (u"分母", 3)]]
    if len(vals) != 10:
        out.append(u"判定の欄の数が違う")
        return out
    for i, w in enumerate(want):
        got = [(k, vals[i][k]) for k, _v in w]
        if got != w:
            out.append(u"判定の数 XJ0-%d が手で数えた値と違う: 手の値 %s ≠ %s" % (i + 1, w, got))
    if vals[1][u"規則ごとの断った書類"][u"R9"] != 2 or vals[1][u"規則ごとの断った書類"][u"R5"] != 1 or sum(vals[1][u"規則ごとの断った書類"].values()) != 3:
        out.append(u"XJ0-2 の規則ごとの断った書類が違う")
    q = vals[7][u"断った(規則ごと)"]
    if q[u"R9"] != 1 or q[u"R5"] != 1 or sum(q.values()) != 2:
        out.append(u"XJ0-8 の規則ごとの断った数が違う")
    # 開発の数は本番の判定に入らない(開発の 1 本は受理・対象 100 だが入っていない)
    if vals[2][u"分母(対象の fact)"] == 114:
        out.append(u"開発の 5 本が本番の分母に入っている")
    return out


class VCap(Cap):
    u"""受け口の作り物に、変えた断りの並びを割り込ませる。``over`` = {file 名: 断りの並びを返す関数 (狙い) -> 断りの並び}。受け取った変異の file の字・type の字も覚える。"""

    def __init__(self, ms, over):
        Cap.__init__(self, ms)
        self.over = over
        self.type_text = None
        self.variants = {}

    def __call__(self, cmd, cwd, timeout):
        rc, o, e, t = Cap.__call__(self, cmd, cwd, timeout)
        if cmd[3] == "--accept":
            with io.open(cmd[4], encoding="utf-8") as fh:
                self.type_text = fh.read()
            return rc, o, e, t
        res = json.loads(o, object_pairs_hook=od)
        broken, _changed = self.ms.make_variants(self.type_text, NAMES2)
        for fn in sorted(os.listdir(cmd[4])):
            with io.open(os.path.join(cmd[4], fn), encoding="utf-8") as fh:
                self.variants[fn] = fh.read()
            if fn in self.over:
                bid = fn[:-5]
                target = broken[bid][0] if bid in broken and broken[bid] else None
                res[fn] = self.ms.result_of(self.over[fn](target))
        return rc, json.dumps(res, ensure_ascii=False), e, t


def refusal_of(ms, rule, row, field, idx=0):
    return ms.refusal(rule, idx, row, field)


def variant_problems(ms=None):
    ms = ms or MS
    out = []
    only = lambda t: [refusal_of(ms, t[0], t[1], t[2])]                                                  # noqa: E731
    over = {
        "R5a.json": only,                                                                                  # 狙いだけで断る
        "R5b.json": lambda t: only(t) + [refusal_of(ms, "R13", 7, u"種類")],                              # 狙いの他にも断る
        "N5a.json": lambda t: [refusal_of(ms, "R13", 7, u"種類")],                                        # 別の規則だけで断る
        "R9a.json": lambda t: [],                                                                          # 断らない
        "R6a.json": lambda t: [refusal_of(ms, t[0], t[1] + 1, t[2])],                                     # 狙いの行の次の行で断る(別の行)
        "R6b.json": lambda t: [refusal_of(ms, t[0], t[1], u"値" if t[2] != u"値" else u"単位")],         # 狙いの欄の別の欄で断る
        "Q1.json": lambda t: [refusal_of(ms, "R9", 3, u"値")],                                             # 変え方が断られた
        "Q2.json": lambda t: []}
    with Temp() as d:
        cap = VCap(ms, over)
        rec, r, proc, _c, zp, tmp = doc_run(ms, d, cap=cap)
        if rec[u"断った"]:
            return [u"作り物の書類が断られた: %s" % rec[u"断った理由"]]
        broken, changed = ms.make_variants(cap.type_text, NAMES2)
        for bid, made in broken.items():
            if made is not None and cap.variants.get(bid + ".json") != made[1]:
                out.append(u"受け口に掛けた壊した file が make_variants の字と違う: %s" % bid)
            if made is not None and made[1] == cap.type_text:
                out.append(u"壊した file が元の file と同じ: %s" % bid)
        for qid, text in changed.items():
            if text is not None and cap.variants.get(qid + ".json") != text:
                out.append(u"受け口に掛けた変えた file が make_variants の字と違う: %s" % qid)
            if text is not None and text == cap.type_text:
                out.append(u"変えた file が元の file と同じ: %s" % qid)
        if sorted(cap.variants) != sorted([b + ".json" for b, m in broken.items() if m is not None] + [q + ".json" for q, t in changed.items() if t is not None]):
            out.append(u"受け口に掛けた file の名の並びが違う")
        brk, chg = rec[u"壊し方"], rec[u"形は合っているが中身が違う"]
        keys = [u"作れた", u"断った", u"ちょうど 1 つ", u"別の規則で断った", u"断らなかった"]
        want = {u"R5a": [1, 1, 1, 0, 0], u"R5b": [1, 1, 0, 0, 0], u"N5a": [1, 0, 0, 1, 0], u"R9a": [1, 0, 0, 0, 1], u"R6a": [1, 0, 0, 1, 0], u"R6b": [1, 0, 0, 1, 0]}
        for bid, w in want.items():
            if bid in broken and broken[bid] is not None and [brk[bid][k] for k in keys] != w:
                out.append(u"壊し方 %s の判定が手の値と違う: 手の値 %s ≠ %s" % (bid, w, [brk[bid][k] for k in keys]))
        if chg[u"Q1"][u"通した"] != 0 or chg[u"Q1"][u"断った"][u"R9"] != 1 or sum(chg[u"Q1"][u"断った"].values()) != 1 or chg[u"Q1"][u"作れた"] != 1:
            out.append(u"断られた変え方の判定が違う: %s" % json.dumps(chg[u"Q1"], ensure_ascii=False))
        if chg[u"Q2"] != {u"作れた": 1, u"通した": 1, u"断った": {r_: 0 for r_ in RULE_IDS}}:
            out.append(u"通した変え方の判定が違う")
    return out


def verify_alone_problems(ms=None):
    u"""記録の検査の 1 つずつ。壊した記録の集計・判定の数は導き直す(合計の照合に頼らず、その検査だけが止める形)。"""
    ms = ms or MS
    out = []
    with Temp() as d:
        tool, docs, runner, tmp, args = record_args(d, ms)
        rec, secret = ms.build_record(tool, docs, **dict(args))
        jkey = [k for k in rec if k.startswith(u"予測の判定に要る数")][0]

        def broken(fn):
            r = json.loads(json.dumps(rec), object_pairs_hook=od)
            fn(r)
            tot = ms.totals_of(r[u"書類"], 1)
            r[u"集計"] = tot
            r[jkey] = ms.judged(tot)
            return r
        D1 = lambda r: r[u"書類"][0]                                                                  # noqa: E731
        A = lambda r: D1(r)[u"受け口"]                                                                # noqa: E731

        def many(*fns):
            def f(r):
                for g in fns:
                    g(r)
            return f
        sr = lambda path, v: (lambda r: put(r, path, v))                                              # noqa: E731
        cases = [
            (u"K1 書類が 2 本", lambda r: r[u"書類"].pop()), (u"K1 材料の本数だけ違う", lambda r: r[u"材料"].__setitem__(u"書類の本数", 2)),
            (u"K1 番号", sr([u"書類", 1, u"番号"], 5)), (u"K1 欄の並び", lambda r: D1(r).__setitem__(u"余り", 1)),
            (u"K2 断った段が空なのに断った", sr([u"書類", 0, u"断った"], True)), (u"K2 断った理由が空", sr([u"書類", 2, u"断った理由"], u"")), (u"K2 断った段が知らない段", sr([u"書類", 2, u"断った段"], u"x")),
            (u"K2 断っていないのに断った段が在る", sr([u"書類", 0, u"断った段"], u"起こす")),
            (u"K3 受理かつ断り(数は揃える)", many(sr([u"書類", 0, u"受け口", u"断った"], True), sr([u"書類", 0, u"受け口", u"断りの数"], 1), lambda r: A(r)[u"規則ごとの断りの数"].__setitem__(u"R9", 1),
                                         lambda r: A(r)[u"規則ごとの断った書類"].__setitem__(u"R9", True), lambda r: A(r)[u"規則と欄ごとの断りの数"].__setitem__(u"R9/値", 1))),
            (u"K4 断りの数が 1 で規則ごとの合計が 0", many(sr([u"書類", 0, u"受け口", u"断りの数"], 1), lambda r: A(r)[u"規則と欄ごとの断りの数"].__setitem__(u"R9/値", 1))),
            (u"K4 規則ごとの断った書類が数と合わない", lambda r: A(r)[u"規則ごとの断った書類"].__setitem__(u"R9", True)),
            (u"K5 規則と欄ごとの合計", lambda r: A(r)[u"規則と欄ごとの断りの数"].__setitem__(u"R9/値", 1)),
            (u"K6 受け口を通っていない書類が後ろの段で断られている", many(sr([u"書類", 0, u"断った"], True), sr([u"書類", 0, u"断った段"], u"組む"), sr([u"書類", 0, u"断った理由"], u"x"), sr([u"書類", 0, u"受け口", u"受理した"], False),
                                                           lambda r: D1(r).__setitem__(u"壊し方", json.loads(json.dumps(ms.zero_rec()), object_pairs_hook=od)[u"壊し方"]),
                                                           lambda r: D1(r).__setitem__(u"比べ方 2", json.loads(json.dumps(ms.zero_rec()), object_pairs_hook=od)[u"比べ方 2"]))),
            (u"K7 断った書類に比べ方 2(組めた)", sr([u"書類", 2, u"比べ方 2", u"組めた"], True)), (u"K7 断った書類に比べ方 2(同じ)", sr([u"書類", 2, u"比べ方 2", u"fact が意味として同じ"], True)),
            (u"K8 受理していない書類に壊し方", many(sr([u"書類", 2, u"壊し方", u"R5a", u"作れた"], 1), sr([u"書類", 2, u"壊し方", u"R5a", u"断らなかった"], 1))),
            (u"K9 対象の fact と型の合計", lambda r: D1(r)[u"型に入った fact"].__setitem__(u"数", D1(r)[u"型に入った fact"][u"数"] + 1)),
            (u"K9 文の側", lambda r: D1(r)[u"型の外の fact"][u"合計"].__setitem__(u"文", D1(r)[u"型の外の fact"][u"合計"][u"文"] + 1)),
            (u"K10 理由ごとが合計より多い", sr([u"書類", 0, u"型の外の fact", u"理由ごと", u"b", u"数"], 99)),
            (u"K11 ちょうど 1 つが断ったより多い", many(sr([u"書類", 0, u"壊し方", u"R5a", u"断った"], 0), sr([u"書類", 0, u"壊し方", u"R5a", u"断らなかった"], 1), sr([u"書類", 0, u"壊し方", u"R5a", u"ちょうど 1 つ"], 1))),
            (u"K12 壊し方の合計", many(sr([u"書類", 0, u"壊し方", u"R5a", u"断った"], 0), sr([u"書類", 0, u"壊し方", u"R5a", u"ちょうど 1 つ"], 0))),
            (u"K13 通したが作れたより多い", sr([u"書類", 0, u"形は合っているが中身が違う", u"Q1", u"通した"], 2)),
            (u"K14 通したのに断った", sr([u"書類", 0, u"形は合っているが中身が違う", u"Q1", u"断った", u"R9"], 1)),
            (u"K15 通さず断りも無い", sr([u"書類", 0, u"形は合っているが中身が違う", u"Q1", u"通した"], 0)),
            (u"K18 禁止の字(docID)", lambda r: r[u"限界"].append(u"S100ABCD")), (u"K18 禁止の字(URI)", lambda r: r[u"限界"].append(u"http://example.org/x")),
            (u"K18 禁止の字(file の名)", lambda r: r[u"限界"].append(u"0101010_honbun.htm"))]
        for what, fn in cases:
            r = broken(fn)
            if not stops(ms.verify_record, r, None, 3, 1):
                out.append(u"記録の検査が 1 つずつでは止まらない: %s" % what)
        ms.verify_record(broken(lambda r: None), None, 3, 1)
        # 集計・判定の数が書類ごとの数から導き直したものと違えば止まる(書類ごとの数はそのまま)
        r = json.loads(json.dumps(rec), object_pairs_hook=od)
        r[u"集計"][u"全部"][u"書類"] += 1
        if not stops(ms.verify_record, r, None, 3, 1):
            out.append(u"集計が違うのに止まらない")
        r = json.loads(json.dumps(rec), object_pairs_hook=od)
        list(r[jkey].values())[0][u"書類"] += 1
        if not stops(ms.verify_record, r, None, 3, 1):
            out.append(u"判定の数が違うのに止まらない")
        # --check は記録の検査を通す(壊した記録は止まる)
        root = os.path.join(d, "root")
        bad = broken(lambda r: r[u"書類"].pop())
        wfile(os.path.join(root, RECORD_REL), ms.prev().M.dumps(bad).encode("utf-8"))
        if not stops(ms.check, root=root, say=lambda *a: None, want=3, dev_count=1):
            out.append(u"壊した記録を --check が通す")
        # 開発の 5 本: 道具が違えば 1 本も掛けない
        tool7, docs7, runner7, tmp7, args7 = record_args(os.path.join(d, "x7"), ms, count=7) if os.makedirs(os.path.join(d, "x7")) is None else (None,) * 5
        if not stops(ms.dev_run, tool7, docs_dir=docs7, runner=runner7, tmp_root=tmp7, say=lambda *a: None, proc=args7["proc"], cap=args7["cap"], names_file=args7["names_file"], want_sha=u"0" * 64) or runner7.calls:
            out.append(u"道具が違うのに --dev が止まらない(か書類を掛けた)")
        tool8, docs8, runner8, tmp8, args8 = record_args(os.path.join(d, "x8"), ms, count=3) if os.makedirs(os.path.join(d, "x8")) is None else (None,) * 5
        if not stops(ms.build_record, tool8, docs8, **dict(args8, want_sha=u"0" * 64)) or runner8.calls:
            out.append(u"道具が違うのに本番が止まらない(か書類を掛けた)")
    return out


class DiffRunner(XG.FactRunner):
    u"""2 回目の呼び出し(組み直した包み)の fact の一覧から最後の 1 行を落とす作り物の道具。"""

    def __init__(self, mv_path, **kw):
        XG.FactRunner.__init__(self, mv_path, **kw)
        self.k = 0

    def __call__(self, cmd, timeout):
        self.k += 1
        return XG.FactRunner.__call__(self, cmd, timeout)

    def facts_rows(self, blobs):
        rows = XG.FactRunner.facts_rows(self, blobs)
        return rows[:-1] if self.k >= 2 else rows


def units_problems(ms=None):
    ms = ms or MS
    out = []
    # ---- 期が書けるか(型に入る期の形)
    for what, p, want in ((u"時点", ("instant", [u"2031-03-31"]), True), (u"期間", ("duration", [u"2030-04-01", u"2031-03-31"]), True), (u"始まり = 終わり", ("duration", [u"2031-03-31", u"2031-03-31"]), True),
                          (u"始まりが終わりより後", ("duration", [u"2031-03-31", u"2030-04-01"]), False), (u"日が在る日でない", ("instant", [u"2031-02-30"]), False),
                          (u"期間の片方が在る日でない", ("duration", [u"2030-04-01", u"2031-13-01"]), False), (u"日が無い", ("instant", []), False), (u"知らない種類", ("forever", [u"2031-03-31"]), False)):
        if ms.period_writable(p) is not want:
            out.append(u"期が書けるかの判定が違う: %s" % what)
    # ---- 単位の字
    U = lambda ms_, d=None: {"measures": ms_, "divide": d}                                              # noqa: E731
    for what, got, want in ((u"他: 分子 2 つの並べ替え", ms.other_unit(U([u"b:y", u"a:x"])), u"他:a:x*b:y"),
                            (u"他: 分子・分母 2 つずつの並べ替え", ms.other_unit(U([], {"num": [u"y:2", u"x:1"], "den": [u"z:4", u"w:3"]})), u"他:x:1*y:2÷w:3*z:4"),
                            (u"他: 分子が空", ms.other_unit(U([])), None), (u"他: 空白", ms.other_unit(U([u"a b"])), None), (u"他: ÷", ms.other_unit(U([u"a÷b"])), None),
                            (u"他: *", ms.other_unit(U([u"a*b"])), None), (u"他: 空の名", ms.other_unit(U([u""])), None), (u"他: 割り算に分子の measures も在る", ms.other_unit(U([u"a"], {"num": [u"b"], "den": [u"c"]})), None),
                            (u"他: 分母が空", ms.other_unit(U([], {"num": [u"b"], "den": []})), None), (u"4 つの形(通貨)", ms.v1_unit(U([u"iso4217:JPY"])), u"通貨:JPY"),
                            (u"4 つの形(株)", ms.v1_unit(U([u"xbrli:shares"])), u"株"), (u"4 つの形(円÷株)", ms.v1_unit(U([], {"num": [u"iso4217:JPY"], "den": [u"xbrli:shares"]})), u"通貨:JPY÷株"),
                            (u"4 つの形でなければ 他:", ms.v1_unit(U([u"iso4217:JPY", u"xbrli:pure"])), u"他:iso4217:JPY*xbrli:pure")):
        if got != want:
            out.append(u"単位の字が違う: %s 手の値 %r ≠ %r" % (what, want, got))
    # ---- 第 1 版の読み直し(手で作った第 0 版の解析から。(a)(d) を狭め (g) を数え直す)
    def fact(**kw):
        f = dict(reasons=set(), period=("instant", [u"2031-03-31"]), isnum=True, unit={"measures": ["iso4217:JPY"], "divide": None}, attrs={"name": u"jppfs_cor:Assets"}, target=u"既定", dims=(),
                 value=u"5", shift=0, prec=0, row=99, out=99, key=99)
        f.update(kw)
        return f
    pure_jpy = {"measures": ["xbrli:pure", "iso4217:JPY"], "divide": None}
    FA = [
        fact(reasons={"g"}),                                                                                                      # 0 古い (g) は外す
        fact(reasons={"a"}, period=("instant", [u"2031-02-15"])),                                                                  # 1 (a) 期が書ければ外す
        fact(reasons={"a"}, period=("duration", [u"2031-03-31", u"2030-04-01"])),                                                  # 2 (a) 期が書けなければ残す
        fact(reasons={"d"}, unit=pure_jpy, period=("instant", [u"2031-02-16"])),                                                   # 3 (d) 単位が書ければ外す
        fact(reasons={"d"}, unit={"measures": [], "divide": None}, period=("instant", [u"2031-02-17"])),                           # 4 (d) 単位が書けなければ残す
        fact(period=("instant", [u"2031-02-14"]), value=u"1"), fact(period=("instant", [u"2031-02-14"]), value=u"2"),             # 5 6 同じ組で値が違う → (g)
        fact(period=("instant", [u"2031-02-13"])), fact(period=("instant", [u"2031-02-13"])),                                      # 7 8 同じ組で同じ値 → 1 行
        fact(reasons={"a", "d"}, period=("instant", [u"2031-02-12"]), unit={"measures": [], "divide": None}),                      # 9 (a) は外れ (d) が残る
        fact(isnum=False, unit=None, period=("instant", [u"2031-02-11"]), value=None, shift=None, prec=None)]                      # 10 文
    v1r = ms.reanalyze(od([("dec", {}), ("facts", FA), ("ctxs", {}), ("units", {})]))
    got_r = [sorted(f["reasons"]) for f in FA]
    want_r = [[], [], ["a"], [], ["d"], ["g"], ["g"], [], [], ["d"], []]
    if got_r != want_r:
        out.append(u"読み直した理由が手の値と違う: 手の値 %s ≠ %s" % (want_r, got_r))
    if [f.get("row") for f in FA] != [0, 1, None, 2, None, None, None, 3, 3, None, 4] or [f.get("out") for f in FA] != [None, None, 0, None, 1, 2, 3, None, None, 4, None]:
        out.append(u"読み直した行・外の番号が違う: %s %s" % ([f.get("row") for f in FA], [f.get("out") for f in FA]))
    if [r["count"] for r in v1r["rows"]] != [1, 1, 1, 2, 1] or [r["kind"] for r in v1r["rows"]] != [u"数", u"数", u"数", u"数", u"文"] or len(v1r["outside"]) != 5:
        out.append(u"読み直した行の数・まとめた数が違う")
    if [f["form1"] for f in FA][:5] != [JPY, JPY, JPY, u"他:iso4217:JPY*xbrli:pure", None] or FA[10]["form1"] is not None:
        out.append(u"読み直した単位の字が違う: %s" % [f["form1"] for f in FA])
    # ---- 型の object(手で作った第 1 版の解析から)
    dec = od([("scheme", u"http://example.org/id"), ("ident", u"E99999-000"), ("start", u"2030-04-01"), ("end", u"2031-03-31"), ("filing", u"2031-06-30")])
    row = lambda **kw: od(list(dict(kind=u"数", name=u"jppfs_cor:Assets", period=[u"2031-03-31"], pkind="instant", target=u"既定", dims=[], value=u"5", unit=JPY, shift=0, prec=0, count=1).items()))   # noqa: E731

    def mk(**kw):
        r = row()
        r.update(kw)
        return r
    v1 = od([("dec", dec), ("rows", [
        mk(name=u"x_E1:Own", dims=[[u"x_E1:SegAxis", u"x_E1:AMember"]], value=u"-5", unit=SHARES, shift=3, prec=-3),
        mk(value=NONE_V, shift=3, prec=-3),
        mk(kind=u"文", name=u"jpcrp_cor:Text", period=[u"2030-04-01", u"2031-03-31"], pkind="duration", value=None, unit=None, shift=None, prec=None),
        mk(name=u"jpdei_cor:Other", target=u"個別")])])
    got = ms.type_object(v1)
    want = od([(u"型の版", u"1"), (u"書類", od([(u"提出者の識別子", u"E99999-000"), (u"識別子の scheme", u"http://example.org/id"), (u"当期の始まり", u"2030-04-01"), (u"当期の終わり", u"2031-03-31"), (u"提出日", u"2031-06-30")])),
               (u"独自の名", [od([(u"種類", u"member"), (u"名", u"x_E1:AMember")]), od([(u"種類", u"科目"), (u"名", u"x_E1:Own")]), od([(u"種類", u"軸"), (u"名", u"x_E1:SegAxis")])]),
               (u"行", [
                   od([(u"種類", u"数"), (u"科目", u"x_E1:Own"), (u"期間", od([(u"時点", u"2031-03-31")])), (u"対象", u"既定"), (u"次元", [[u"x_E1:SegAxis", u"x_E1:AMember"]]), (u"値", u"-5"), (u"単位", u"株"), (u"表示の位", 3), (u"精度", -3)]),
                   od([(u"種類", u"数"), (u"科目", u"jppfs_cor:Assets"), (u"期間", od([(u"時点", u"2031-03-31")])), (u"対象", u"既定"), (u"次元", []), (u"値", u"無い"), (u"単位", JPY), (u"表示の位", None), (u"精度", None)]),
                   od([(u"種類", u"文"), (u"科目", u"jpcrp_cor:Text"), (u"期間", od([(u"始まり", u"2030-04-01"), (u"終わり", u"2031-03-31")])), (u"対象", u"既定"), (u"次元", [])]),
                   od([(u"種類", u"数"), (u"科目", u"jpdei_cor:Other"), (u"期間", od([(u"時点", u"2031-03-31")])), (u"対象", u"個別"), (u"次元", []), (u"値", u"5"), (u"単位", JPY), (u"表示の位", 0), (u"精度", 0)])])])
    if json.dumps(got, ensure_ascii=False) != json.dumps(want, ensure_ascii=False):
        out.append(u"型の object が手で書いた値と違う: %s" % json.dumps(got, ensure_ascii=False)[:400])
    # 名の分類
    for n, want in ((u"jppfs_cor:A", u"辞書の在る接頭辞"), (u"jpcrp_cor:A", u"辞書の在る接頭辞"), (u"jpigp_cor:A", u"辞書の在る接頭辞"), (u"jpdei_cor:A", u"辞書の無い _cor の接頭辞"), (u"x_E1:A", u"提出者別"), (u"jpfoo:A", u"提出者別")):
        if ms.name_class(n) != want:
            out.append(u"名の分類が違う: %s" % n)
    # ---- 作る側の文脈・単位の定義
    R = lambda per, dims=(), unit=JPY, kind=u"数", target=u"既定": od([(u"種類", kind), (u"科目", u"jppfs_cor:Assets"), (u"期間", per), (u"対象", target), (u"次元", [list(x) for x in dims])] +   # noqa: E731
                                                                  ([(u"値", u"5"), (u"単位", unit), (u"表示の位", 0), (u"精度", 0)] if kind == u"数" else []))
    rows = [R(per_i(u"2031-02-15"), unit=u"他:zz"), R(per_i(u"2031-03-30"), unit=u"他:aa"), R(per_i(u"2031-03-30"), unit=u"他:zz"), R(per_d(u"2030-05-01", u"2031-01-31"), unit=u"他:a*b÷c*d")]
    ctxs, units, info = ms.v1_definitions(dec, rows)
    if [c["id"] for c in ctxs] != [u"At20310215Instant", u"At20310330Instant", u"From20300501To20310131Duration"] or [u["id"] for u in units] != [u"U0001", u"U0002", u"U0003"]:
        out.append(u"作る側の文脈・単位の id の並びが違う: %s %s" % ([c["id"] for c in ctxs], [u["id"] for u in units]))
    elif [i[1] for i in info] != [u"U0003", u"U0002", u"U0003", u"U0001"] or [i[0] for i in info] != [u"At20310215Instant", u"At20310330Instant", u"At20310330Instant", u"From20300501To20310131Duration"]:
        out.append(u"作る側の行ごとの id が違う: %s" % info)
    else:
        if units[0] != od([("type", "unit"), ("id", "U0001"), ("measures", []), ("divide", od([("num", ["a", "b"]), ("den", ["c", "d"])]))]) or units[1]["measures"] != ["aa"] or units[2]["measures"] != ["zz"]:
            out.append(u"他: の単位の定義が違う")
    a1, a2 = u"x_E1:SegAxis", u"x_E1:SegAxis"
    if not stops_with(ms.v1_definitions, ms.Refuse, dec, [R(per_i(u"2031-03-31"), dims=[[a1, u"x:ASegMember"]]), R(per_i(u"2031-03-31"), dims=[[a2, u"xA:SegMember"]])]):
        out.append(u"文脈の id が違う組で重なっても断らない")
    c2, _u2, _i2 = ms.v1_definitions(dec, [R(per_i(u"2031-03-31"), dims=[[a1, u"x:ASegMember"]]), R(per_i(u"2031-03-31"), dims=[[a1, u"x:ASegMember"]])])
    if len(c2) != 1:
        out.append(u"同じ組の文脈の定義を 1 つにしない")
    # ---- 作る fact の属性
    num_r = R(per_i(u"2031-03-31"))
    num_r.update({u"値": u"-5", u"表示の位": 3, u"精度": -3})
    pos_r = dict(num_r, **{u"値": u"5"})
    nil_r = dict(num_r, **{u"値": NONE_V, u"表示の位": None, u"精度": None})
    txt_r = R(per_i(u"2031-03-31"), kind=u"文")
    want_a = {"contextRef": "C1", "decimals": "-3", "format": "ixt:numdotdecimal", "name": "jppfs_cor:Assets", "scale": "3", "sign": "-", "unitRef": "U1", "id": "f1"}
    if ms.v1_attrs(num_r, "C1", "U1", {"id": "f1"}) != dict(sorted(want_a.items())) or list(ms.v1_attrs(num_r, "C1", "U1", {"id": "f1"})) != sorted(want_a):
        out.append(u"作る fact の属性(負の数)が違う: %s" % ms.v1_attrs(num_r, "C1", "U1", {"id": "f1"}))
    if ms.v1_attrs(pos_r, "C1", "U1", {}) != {"contextRef": "C1", "decimals": "-3", "format": "ixt:numdotdecimal", "name": "jppfs_cor:Assets", "scale": "3", "unitRef": "U1"}:
        out.append(u"作る fact の属性(正の数)が違う")
    if ms.v1_attrs(nil_r, "C1", "U1", {}) != {"contextRef": "C1", "name": "jppfs_cor:Assets", "unitRef": "U1", "xsi:nil": "true"}:
        out.append(u"作る fact の属性(無い)が違う: %s" % ms.v1_attrs(nil_r, "C1", "U1", {}))
    if ms.v1_attrs(txt_r, "C1", None, {"id": "t"}) != {"contextRef": "C1", "id": "t", "name": "jppfs_cor:Assets"}:
        out.append(u"作る fact の属性(文)が違う")
    for k in ("decimals", "scale", "format", "sign", "unitRef", "contextRef", "name", "xsi:nil"):
        if not stops_with(ms.v1_attrs, ms.Refuse, num_r, "C1", "U1", {k: "x"}):
            out.append(u"持ち込みに型の属性(%s)が在っても断らない" % k)
    if not stops_with(ms.v1_attrs, ms.Refuse, txt_r, "C1", None, {"contextRef": "x"}):
        out.append(u"持ち込みに型の属性(文の contextRef)が在っても断らない")
    # ---- 型・持ち込み・型の外の folder から作る側
    with Temp() as d:
        zp, root, v1, files = derive_fake(ms, d)
        tcarry = sorted(os.listdir(os.path.join(root, "carry")))
        base_out = ms.render_v1(root)
        if ms.carry_forbidden_v1(root) != []:
            out.append(u"正しい持ち込みに入れないものが在ると言う")
        # 型の file を壊すと例外でなく断り
        tp = os.path.join(root, "type", "type.json")
        orig = rfile(tp)
        for what, data in ((u"行が無い", json.dumps({u"書類": json.loads(orig.decode("utf-8"))[u"書類"]}, ensure_ascii=False).encode("utf-8")), (u"JSON でない", b"x"), (u"空", b"")):
            wfile(tp, data)
            if not stops_with(ms.render_v1, ms.Refuse, root):
                out.append(u"型の file が壊れていても断りにならない: %s" % what)
        wfile(tp, orig)
        # 作った定義を置く頭の部が無ければ断る
        cfiles = [f for f in tcarry if f.startswith("c0")]
        saved = {}
        for f in cfiles:
            p = os.path.join(root, "carry", f)
            saved[f] = rfile(p)
            o = json.loads(saved[f].decode("utf-8"), object_pairs_hook=od)
            if o["H"] is not None:
                o["H"]["sections"] = [s for s in o["H"]["sections"] if s != "ix:resources"]
            wfile(p, json.dumps(o, ensure_ascii=False).encode("utf-8"))
        if not stops_with(ms.render_v1, ms.Refuse, root):
            out.append(u"作った定義を置く頭の部が無いのに断らない")
        for f, data in saved.items():
            wfile(os.path.join(root, "carry", f), data)
        # 型の外の単位・文脈は作った定義に足す
        op = os.path.join(root, "outside", ms.prev().M.OUTSIDE_FILE)
        oo = json.loads(rfile(op).decode("utf-8"), object_pairs_hook=od)
        oo["units"].append(od([("type", "unit"), ("id", "UZZ"), ("measures", [u"zz:q"]), ("divide", None)]))
        oo["contexts"].append(od([("type", "context"), ("id", "CZZ"), ("scheme", "s"), ("ident", "i"), ("period", [["xbrli:instant", "2031-01-01"]]), ("members", []), ("has_scenario", False)]))
        wfile(op, json.dumps(oo, ensure_ascii=False).encode("utf-8"))
        files2, _n2, _t2 = ms.render_v1(root)
        ids_before = [r["id"] for f in base_out[0] for r in (f[3]["resources"] if f[3] else []) if r["type"] != "ref"]
        ids_after = [r["id"] for f in files2 for r in (f[3]["resources"] if f[3] else []) if r["type"] != "ref"]
        if sorted(ids_after) != sorted(ids_before + ["UZZ", "CZZ"]):
            out.append(u"型の外の単位・文脈を作った定義に足さない: %s" % (sorted(set(ids_after) - set(ids_before)),))
        # 持ち込みに型の属性が在れば検査が見つける
        c0 = os.path.join(root, "carry", [f for f in tcarry if f.startswith("c0")][0])
        co = json.loads(rfile(c0).decode("utf-8"), object_pairs_hook=od)
        for e in co["F"]:
            if "row" in e:
                e["carry"]["decimals"] = "0"
                break
        wfile(c0, json.dumps(co, ensure_ascii=False).encode("utf-8"))
        if not ms.carry_forbidden_v1(root):
            out.append(u"持ち込みに型の属性が在るのに見つけない")
    # ---- process_doc: 持ち込みに入れないものが在れば止まる(導き直しの後ろ・受け口の前)
    saved_derive = ms.derive_v1

    def tamper(entries, root):
        res = saved_derive(entries, root)
        c = os.path.join(root, "carry")
        f = os.path.join(c, sorted(x for x in os.listdir(c) if x.startswith("c0"))[0])
        o = json.loads(rfile(f).decode("utf-8"), object_pairs_hook=od)
        for e in o["F"]:
            if "row" in e:
                e["carry"]["decimals"] = "0"
                break
        wfile(f, json.dumps(o, ensure_ascii=False).encode("utf-8"))
        return res
    ms.derive_v1 = tamper
    try:
        with Temp() as d:
            cap = Cap(ms)
            if not stops(doc_run, ms, d, cap=cap) or cap.calls:
                out.append(u"持ち込みに型の属性が在るのに止まらない(か受け口に掛けた)")
    finally:
        ms.derive_v1 = saved_derive
    # ---- 組み直した包みの fact が違えば 意味として同じ でない
    with Temp() as d:
        rec, r, p, c, zp, tmp = doc_run(ms, d, runner_cls=DiffRunner)
        c2 = rec[u"比べ方 2"]
        if rec[u"断った"] or c2[u"組めた"] is not True or c2[u"fact が意味として同じ"] is not False or c2[u"字も含めて行が同じ"] is not False:
            out.append(u"組み直した包みの fact が違うのに 意味として同じ と言う: %s" % dict(c2))
    # ---- --make・--break
    with Temp() as d:
        zp = os.path.join(d, "docs", "S2FAKE01.zip")
        os.makedirs(os.path.dirname(zp))
        XG.make_doc(zp, 1, None, None)
        made = os.path.join(d, "made1")
        ms.run_make(made, zp)
        if sorted(os.listdir(made)) != ["carry", "outside", "type"]:
            out.append(u"--make が 3 つの folder を作らない: %s" % sorted(os.listdir(made)))
        if not stops(ms.run_make, made, zp):
            out.append(u"--make が空でない folder に書く")
        nf = os.path.join(d, "names.json")
        wfile(nf, json.dumps(sorted(NAMES2)))
        said = []
        brk, chg = ms.run_break(made, nf, say=said.append)
        if len(said) != 1 or json.loads(said[0])[u"壊し方"][u"R5a"][u"作れた"] != 1 or brk[u"R5a"][u"断った"] != 1 or chg[u"Q1"][u"通した"] != 1 or sum(v[u"断った"] for v in brk.values()) != 41:
            out.append(u"--break の数が違う: %s" % said[:1])
    return out


def stops_with(fn, exc, *a, **kw):
    u"""fn が ``exc`` を投げれば True(ほかの例外・投げなければ False)。"""
    try:
        fn(*a, **kw)
    except exc:
        return True
    except BaseException:                # noqa: BLE001
        return False
    return False


# ======================================================================== 11. 変異(約束の側から。script の字を 1 か所替えた版を memory の中に作る)
SRC0 = read(SCRIPT_REL)
LINES0 = SRC0.split(u"\n")
ALT_FIELD = od([(u"値", u"対象"), (u"対象", u"値"), (u"期間", u"次元"), (u"次元", u"期間"), (u"科目", u"種類"), (u"種類", u"科目"), (u"単位", u"値"), (u"精度", u"表示の位"), (u"表示の位", u"精度"),
                (u"行", u"値"), (u"file", u"行"), (u"書類", u"file"), (u"独自の名", u"書類"), (u"型の版", u"行"), (u"当期の始まり", u"提出日"), (u"当期の終わり", u"当期の始まり"), (u"提出日", u"当期の終わり"),
                (u"提出者の識別子", u"識別子の scheme"), (u"識別子の scheme", u"提出者の識別子"), (u"備考", u"対象")])
ALT_RULE = {"S2": "D2", "D2": "D3", "D3": "D4", "D4": "D2", "N1": "N2", "N2": "N3", "N3": "N2", "R3": "R8", "R8": "R9", "R9": "R8", "R10": "R11", "R11": "R12", "R12": "R13", "R13": "R10"}
REFUSAL_CALL = re.compile(r'refusal\("(\w+)", (\w+), ([^,]+), (u"[^"]*"|\w+)\)')


def func_lines(prefix_decorator=None, names=None):
    u"""script の関数の (名前, 先頭の行の番号 0 から, 終わりの行の番号)。"""
    tree = ast.parse(SRC0)
    out = []
    for n in tree.body:
        if isinstance(n, ast.FunctionDef):
            out.append((n.name, n.lineno - 1, n.end_lineno - 1))
    return out


FUNCS0 = func_lines()


def func_of_line(i):
    for name, a, b in FUNCS0:
        if a <= i <= b:
            return name
    return None


def with_lines(changes):
    u"""``{行の番号: 新しい行}`` を当てた script の字。"""
    ls = list(LINES0)
    for i, new in changes.items():
        ls[i] = new
    return u"\n".join(ls)


def generated_mutants():
    u"""断りの呼び出しの 1 つずつ・壊し方・変え方の 1 つずつを掃く変異(約束の側から)。(名前, {行: 新しい行}, 検査の名前の並び)。"""
    out = []
    conds_n = dict((r[0], len(r[2])) for r in MS.RULES)
    for i, ln in enumerate(LINES0):
        fn = func_of_line(i)
        if fn is None or fn.startswith(("brk_", "chg_")):
            continue
        indent = ln[:len(ln) - len(ln.lstrip())]
        s = ln.strip()
        m = REFUSAL_CALL.search(ln)
        if (s.startswith(u"out.append(refusal(") or s.startswith(u"return [refusal(")) and m:
            rid, idx, row, field = m.groups()
            tag = u"%s-%s %s:%d" % (rid, idx, fn, i + 1)
            lone = s.startswith(u"return [")                                     # 1 つだけ返して終わる断り(S1)。抜くときは空の並びを返す
            out.append((u"G1 断りを 1 つ抜く %s" % tag, {i: indent + (u"return []" if lone else u"pass")}, (u"rules", u"degen")))
            if idx.isdigit():
                k = conds_n[rid]
                if k > 1:
                    new = ln.replace(u'refusal("%s", %s,' % (rid, idx), u'refusal("%s", %d,' % (rid, (int(idx) + 1) % k))
                else:
                    new = ln.replace(u'refusal("%s", %s,' % (rid, idx), u'refusal("%s", %s,' % (ALT_RULE[rid], idx))
                out.append((u"G2 断りの番号(規則・条件)をずらす %s" % tag, {i: new}, (u"rules", u"degen")))
            elif idx == u"c":
                out.append((u"G2 断りの番号をずらす %s" % tag, {i: ln.replace(u'refusal("%s", c,' % rid, u'refusal("%s", 3 - c,' % rid)}, (u"rules",)))
            if row in (u"i", u"None"):
                new_row = u"i + 1" if row == u"i" else u"1"
                out.append((u"G3 行の番号をずらす %s" % tag, {i: ln.replace(m.group(0), m.group(0).replace(u", %s, " % row, u", %s, " % new_row, 1))}, (u"rules", u"degen")))
            if field.startswith(u'u"') and field[2:-1] in ALT_FIELD:
                out.append((u"G4 欄の名を取り違える %s" % tag, {i: ln.replace(m.group(0), m.group(0).replace(field, u'u"%s"' % ALT_FIELD[field[2:-1]]))}, (u"rules", u"degen")))
    # 壊し方・変え方: 編集の 1 行を抜く・狙いの行・欄・規則をずらす
    edit_start = (u"o[", u"r[", u"rows[", u"del ", u"r.", u"es.", u"es[", u"o.", u"c[", u"p[", u"p.", u"rows[i", u"f[")
    for i, ln in enumerate(LINES0):
        fn = func_of_line(i)
        if fn is None or not fn.startswith(("brk_", "chg_")):
            continue
        indent = ln[:len(ln) - len(ln.lstrip())]
        s = ln.strip()
        if s.startswith(edit_start) and not s.startswith(u"o = ") and u"return" not in s:
            out.append((u"G6 編集の 1 行を抜く %s:%d" % (fn, i + 1), {i: indent + u"pass"}, (u"breaks",)))
        m = re.match(r'(\s+)return \(("\w+"), ([^,]+), (u"[^"]*")\), (.*)$', ln)
        if m:
            ind, rid, row, field, rest = m.groups()
            tag = u"%s:%d" % (fn, i + 1)
            nrow = u"1" if row == u"None" else (str(int(row) + 1) if row.isdigit() else u"%s + 1" % row)
            out.append((u"G7 狙いの行をずらす %s" % tag, {i: u'%sreturn (%s, %s, %s), %s' % (ind, rid, nrow, field, rest)}, (u"breaks",)))
            out.append((u"G7 狙いの欄をずらす %s" % tag, {i: u'%sreturn (%s, %s, u"%s"), %s' % (ind, rid, row, ALT_FIELD.get(field[2:-1], u"値"), rest)}, (u"breaks",)))
            out.append((u"G7 狙いの規則をずらす %s" % tag, {i: u'%sreturn ("%s", %s, %s), %s' % (ind, u"R13" if rid != u'"R13"' else u"R12", row, field, rest)}, (u"breaks",)))
    return out


def hand_text_mutants():
    u"""手で書いた変異(条件を 1 つ緩める・取り違える。名前, 元の字(script に 1 回だけ在る), 新しい字, 検査の名前の並び)。"""
    M = []
    a = M.append
    R, B_ = (u"rules",), (u"breaks",)
    # ---- S1・S2
    a((u"S1 頂の鍵の集まりを 含む にする", u"if set(obj) != set(TOP_KEYS):", u"if not set(TOP_KEYS) <= set(obj):", R))
    a((u"S1 頂の鍵の集まりを 一部 にする", u"if set(obj) != set(TOP_KEYS):", u"if not set(obj) <= set(TOP_KEYS):", R))
    a((u"S1 型の版の型を見ない", u"if not (isinstance(obj.get(u\"型の版\"), str) and obj[u\"型の版\"] == TYPE_VERSION):", u"if obj.get(u\"型の版\") != TYPE_VERSION and obj.get(u\"型の版\") != 1:", R))
    a((u"S1 行が 0 個でもよい", u"if not (isinstance(rows, list) and len(rows) >= 1):", u"if not isinstance(rows, list):", R))
    a((u"S1 行が 2 つ以上", u"if not (isinstance(rows, list) and len(rows) >= 1):", u"if not (isinstance(rows, list) and len(rows) >= 2):", R))
    a((u"S1 独自の名が object でもよい", u"if not isinstance(entries, list):", u"if not isinstance(entries, (list, dict)):", R))
    a((u"S1 書類が並びでもよい", u"if not isinstance(doc, dict):", u"if not isinstance(doc, (dict, list)):", R))
    a((u"S1 頂が object でなくても進む", u"    if not isinstance(obj, dict):\n        return [refusal(\"S1\", 1, None, u\"file\")]", u"    if not isinstance(obj, (dict, list)):\n        return [refusal(\"S1\", 1, None, u\"file\")]", R))
    a((u"S1・S2 に当たってもほかを掛ける", u"    if out:\n        return sort_refusals(out)\n    check_doc(doc, out)", u"    check_doc(doc, out)", R))
    a((u"S2 の同じ鍵を見ない", u"            if k in d:\n                dups.append(k)", u"            if False:\n                dups.append(k)", R))
    a((u"S2 の同じ鍵を最初の object だけ見る", u"        d = {}\n        for k, v in pairs:\n            if k in d:\n                dups.append(k)\n            d[k] = v\n        return d", u"        d = {}\n        for k, v in pairs:\n            if k in d and not dups and len(d) > 3:\n                dups.append(k)\n            d[k] = v\n        return d", R))
    a((u"S2 を 1 つも返さない", u"    if dup:\n        out.append(refusal(\"S2\", 0, None, u\"file\"))", u"    if False:\n        out.append(refusal(\"S2\", 0, None, u\"file\"))", R))
    a((u"S1 の NaN を読めるとする", u"    def bad_constant(s):\n        raise ValueError(s)\n", u"    def bad_constant(s):\n        return 0\n", R))
    a((u"S1 の深い入れ子を落とす", u"    except (ValueError, RecursionError):\n        return [refusal(\"S1\", 0, None, u\"file\")]", u"    except ValueError:\n        return [refusal(\"S1\", 0, None, u\"file\")]", (u"degen",)))
    a((u"S1 の UTF-8 でない字を落とす", u"    except UnicodeDecodeError:\n        return [refusal(\"S1\", 0, None, u\"file\")]", u"    except ZeroDivisionError:\n        return [refusal(\"S1\", 0, None, u\"file\")]", (u"degen",)))
    # ---- D
    a((u"D1 鍵の集まりを 含む にする", u"if keys != set(DOC_KEYS):", u"if not set(DOC_KEYS) <= keys:", R))
    a((u"D1 日の形を見ない(match)", u"if not isinstance(s, str) or not DATE_RE.fullmatch(s):", u"if not isinstance(s, str) or not DATE_RE.match(s):", R))
    a((u"D1 日が在る日でなくてもよい", u"    try:\n        return datetime.date(int(s[0:4]), int(s[5:7]), int(s[8:10]))\n    except ValueError:\n        return None", u"    try:\n        return datetime.date(int(s[0:4]), int(s[5:7]), min(int(s[8:10]), 28))\n    except ValueError:\n        return None", R))
    a((u"D1 日の形を 3 つとも見ない(終わりだけ)", u"    for k in DOC_DATE_KEYS:\n        if k in doc:", u"    for k in DOC_DATE_KEYS[1:2]:\n        if k in doc:", R))
    a((u"D2 始まり = 終わりも断る", u"dates[u\"当期の始まり\"] > dates[u\"当期の終わり\"]:", u"dates[u\"当期の始まり\"] >= dates[u\"当期の終わり\"]:", R))
    a((u"D2 を見ない", u"and dates[u\"当期の始まり\"] > dates[u\"当期の終わり\"]:", u"and False:", R))
    a((u"D3 提出日 = 期末も断る", u"dates[u\"提出日\"] < dates[u\"当期の終わり\"]:", u"dates[u\"提出日\"] <= dates[u\"当期の終わり\"]:", R))
    a((u"D3 の向きが逆", u"dates[u\"提出日\"] < dates[u\"当期の終わり\"]:", u"dates[u\"提出日\"] > dates[u\"当期の終わり\"]:", R))
    a((u"D4 空の字もよい", u"return isinstance(s, str) and len(s) >= 1 and not re.search(r\"\\s\", s)", u"return isinstance(s, str) and not re.search(r\"\\s\", s)", R))
    a((u"D4 空白を見ない", u"return isinstance(s, str) and len(s) >= 1 and not re.search(r\"\\s\", s)", u"return isinstance(s, str) and len(s) >= 1", R))
    a((u"D4 半角の空白だけ見る", u"return isinstance(s, str) and len(s) >= 1 and not re.search(r\"\\s\", s)", u"return isinstance(s, str) and len(s) >= 1 and u\" \" not in s", R))
    a((u"D4 字の型を見ない", u"return isinstance(s, str) and len(s) >= 1 and not re.search(r\"\\s\", s)", u"return not isinstance(s, str) or (len(s) >= 1 and not re.search(r\"\\s\", s))", R))
    a((u"D4 scheme を見ない", u"    for k in DOC_ID_KEYS:\n        if k in doc and not good_id(doc[k]):", u"    for k in DOC_ID_KEYS[:1]:\n        if k in doc and not good_id(doc[k]):", R))
    # ---- N
    a((u"N1 形を全体で見ない(match)", u"if isinstance(name, str) and NAME_RE.fullmatch(name):", u"if isinstance(name, str) and NAME_RE.match(name):", R))
    a((u"N1 ハイフンを通さない", u'NAME_RE = re.compile(r"[A-Za-z0-9_\\-]+:[A-Za-z0-9_\\-]+", re.ASCII)', u'NAME_RE = re.compile(r"[A-Za-z0-9_]+:[A-Za-z0-9_]+", re.ASCII)', R))
    a((u"N1 全角の英数字を通す", u'NAME_RE = re.compile(r"[A-Za-z0-9_\\-]+:[A-Za-z0-9_\\-]+", re.ASCII)', u'NAME_RE = re.compile(r"[\\w\\-]+:[\\w\\-]+")', R))
    a((u"N1 局所名が空でもよい", u'NAME_RE = re.compile(r"[A-Za-z0-9_\\-]+:[A-Za-z0-9_\\-]+", re.ASCII)', u'NAME_RE = re.compile(r"[A-Za-z0-9_\\-]+:[A-Za-z0-9_\\-]*", re.ASCII)', R))
    a((u"N1 `:` が 2 つでもよい", u'NAME_RE = re.compile(r"[A-Za-z0-9_\\-]+:[A-Za-z0-9_\\-]+", re.ASCII)', u'NAME_RE = re.compile(r"[A-Za-z0-9_\\-]+:[A-Za-z0-9_\\-:]+", re.ASCII)', R))
    for drop in ("jppfs_cor", "jpcrp_cor", "jpigp_cor"):
        keep = tuple(p for p in ("jppfs_cor", "jpcrp_cor", "jpigp_cor") if p != drop)
        a((u"N2 辞書の在る接頭辞 %s を落とす" % drop, u'DICT_PREFIXES = ("jppfs_cor", "jpcrp_cor", "jpigp_cor")', u"DICT_PREFIXES = %r" % (keep,), R + (u"cli",) if False else R))
    a((u"N2 辞書の名を局所名だけで引く", u'if prefix + "_" + local not in names:', u'if local not in set(n.split("_", 2)[-1] for n in names):', R))
    a((u"N2 接頭辞を足さない", u'if prefix + "_" + local not in names:', u'if "_" + local not in names:', R))
    a((u"N3 種類を見ない(名だけ)", u'elif not prefix.endswith("_cor") and not own and (kind, name) not in custom:', u'elif not prefix.endswith("_cor") and not own and name not in set(n for _k, n in custom):', R))
    a((u"N3 `_cor` の接頭辞にも掛ける", u'elif not prefix.endswith("_cor") and not own and (kind, name) not in custom:', u'elif not own and (kind, name) not in custom:', R))
    a((u"N3 独自の名の要素にも掛ける", u'elif not prefix.endswith("_cor") and not own and (kind, name) not in custom:', u'elif not prefix.endswith("_cor") and (kind, name) not in custom:', R))
    a((u"N3 を掛けない", u'elif not prefix.endswith("_cor") and not own and (kind, name) not in custom:', u'elif False:', R))
    a((u"N3 の接頭辞の見方が前方一致", u'elif not prefix.endswith("_cor") and not own and (kind, name) not in custom:', u'elif not prefix.startswith("jp") and not own and (kind, name) not in custom:', R))
    a((u"N4 要素の鍵を含むで見る", u"if not isinstance(e, dict) or set(e) != set(NAME_KEYS):\n            out.append(refusal(\"N4\", 0, None, f))", u"if not isinstance(e, dict) or not set(NAME_KEYS) <= set(e):\n            out.append(refusal(\"N4\", 0, None, f))", R))
    a((u"N4 種類を見ない", u"        if kind not in NAME_KINDS:\n            out.append(refusal(\"N4\", 1, None, f))\n            continue", u"        if False:\n            out.append(refusal(\"N4\", 1, None, f))\n            continue", R + (u"degen",)))
    a((u"N4 `_cor` を見ない", u"            if sp[0].endswith(\"_cor\"):", u"            if sp[0] == \"never_cor\":", R))
    a((u"N4 `_cor` の見方が jpdei だけ", u"            if sp[0].endswith(\"_cor\"):", u"            if sp[0] == \"jpdei_cor\":", R))
    a((u"N4 使われない名を名だけで見る", u"            elif (kind, name) not in used:", u"            elif name not in set(n for _k, n in used):", R))
    a((u"N4 使われない名を見ない", u"            elif (kind, name) not in used:", u"            elif False:", R))
    a((u"N4 重なりを名だけで見る", u"            if (kind, name) in seen:", u"            if name in set(n for _k, n in seen):", R))
    a((u"N4 重なりを見ない", u"            if (kind, name) in seen:", u"            if False:", R))
    a((u"N4 並びを名だけで見る", u"            elif last is not None and (kind, name) < last:", u"            elif last is not None and name < last[1]:", R))
    a((u"N4 並びを <= で見る", u"            elif last is not None and (kind, name) < last:", u"            elif last is not None and (kind, name) <= last:", R))
    a((u"N4 並びの向きが逆", u"            elif last is not None and (kind, name) < last:", u"            elif last is not None and (kind, name) > last:", R))
    a((u"N4 並びを見ない", u"            elif last is not None and (kind, name) < last:", u"            elif False:", R))
    a((u"N5 軸の見方が含む", u'if kind == u"軸" and not name.endswith("Axis"):', u'if kind == u"軸" and "Axis" not in name:', R))
    a((u"N5 member の見方が含む", u'if kind == u"member" and not name.endswith("Member"):', u'if kind == u"member" and "Member" not in name:', R))
    a((u"N5 軸の種類を取り違える", u'if kind == u"軸" and not name.endswith("Axis"):', u'if kind == u"member" and not name.endswith("Axis"):', R))
    a((u"N5 を科目にも掛ける", u'if kind == u"軸" and not name.endswith("Axis"):', u'if kind != u"member" and not name.endswith("Axis"):', R))
    a((u"N2・N3・N5 を N1 に当たった名にも掛ける", u"    sp = split_name(name)\n    if sp is None:\n        out.append(refusal(\"N1\", 0, row, field))\n        return\n    prefix, local = sp", u"    sp = split_name(name)\n    if sp is None:\n        out.append(refusal(\"N1\", 0, row, field))\n        sp = (str(name).split(\":\")[0], str(name).split(\":\")[-1])\n    prefix, local = sp", R))
    # ---- R1〜R4
    a((u"R1 種類の見方が 数 だけ", u"    if kind != KIND_NUM and kind != KIND_TEXT:", u"    if kind != KIND_NUM:", R))
    a((u"R1 行が object でなくても進む", u"    if not isinstance(r, dict):\n        out.append(refusal(\"R1\", 0, i, u\"行\"))\n        return True", u"    if not isinstance(r, dict):\n        out.append(refusal(\"R1\", 0, i, u\"行\"))\n        r = {}", R))
    a((u"R1 余計な鍵を見ない", u"    for k in sorted(set(want) ^ set(r), key=lambda x: (x not in want, x)):", u"    for k in sorted(set(want) - set(r)):", R))
    a((u"R1 足りない鍵を見ない", u"    for k in sorted(set(want) ^ set(r), key=lambda x: (x not in want, x)):", u"    for k in sorted(set(r) - set(want)):", R))
    a((u"R1 鍵の過不足を 1 つにまとめる", u"    for k in sorted(set(want) ^ set(r), key=lambda x: (x not in want, x)):\n        out.append(refusal(\"R1\", 2, i, k))\n        hit = True", u"    for k in sorted(set(want) ^ set(r), key=lambda x: (x not in want, x))[:1]:\n        out.append(refusal(\"R1\", 2, i, k))\n        hit = True", R))
    a((u"R1 の鍵の種類を取り違える(文も数の鍵)", u"    want = NUM_KEYS if kind == KIND_NUM else TEXT_KEYS", u"    want = NUM_KEYS", R))
    a((u"R1 の鍵の種類を取り違える(数も文の鍵)", u"    want = NUM_KEYS if kind == KIND_NUM else TEXT_KEYS", u"    want = TEXT_KEYS", R))
    a((u"R2 鍵の見方が 時点 を含む", u"if isinstance(p, dict) and set(p) == {u\"時点\"}:", u"if isinstance(p, dict) and u\"時点\" in p:", R))
    a((u"R2 鍵の見方が 始まり を含む", u"elif isinstance(p, dict) and set(p) == {u\"始まり\", u\"終わり\"}:", u"elif isinstance(p, dict) and u\"始まり\" in p and u\"終わり\" in p:", R))
    a((u"R2 日の形を見ない", u"            if any(x is None for x in dd):", u"            if False:", R))
    a((u"R2 日の形を最初の日だけ見る", u"            if any(x is None for x in dd):", u"            if dd[0] is None:", R))
    a((u"R2 始まり = 終わりも断る", u"            elif len(dd) == 2 and dd[0] > dd[1]:", u"            elif len(dd) == 2 and dd[0] >= dd[1]:", R))
    a((u"R2 始まり > 終わりを見ない", u"            elif len(dd) == 2 and dd[0] > dd[1]:", u"            elif False:", R))
    a((u"R3 個別 だけ通す", u'if u"対象" in r and r[u"対象"] != TARGET_IND and r[u"対象"] != TARGET_DEF:', u'if u"対象" in r and r[u"対象"] != TARGET_IND:', R))
    a((u"R3 既定 だけ通す", u'if u"対象" in r and r[u"対象"] != TARGET_IND and r[u"対象"] != TARGET_DEF:', u'if u"対象" in r and r[u"対象"] != TARGET_DEF:', R))
    a((u"R3 を見ない", u'if u"対象" in r and r[u"対象"] != TARGET_IND and r[u"対象"] != TARGET_DEF:', u'if False:', R))
    a((u"R4 並びの型を見ない", u"        if not isinstance(d, list):\n            out.append(refusal(\"R4\", 0, i, u\"次元\"))", u"        if not isinstance(d, (list, dict)):\n            out.append(refusal(\"R4\", 0, i, u\"次元\"))", R))
    a((u"R4 要素の長さが 2 以上", u"if isinstance(e, list) and len(e) == 2 and isinstance(e[0], str) and isinstance(e[1], str):", u"if isinstance(e, list) and len(e) >= 2 and isinstance(e[0], str) and isinstance(e[1], str):", R))
    a((u"R4 要素の 2 つ目の型を見ない", u"if isinstance(e, list) and len(e) == 2 and isinstance(e[0], str) and isinstance(e[1], str):", u"if isinstance(e, list) and len(e) == 2 and isinstance(e[0], str):", R + (u"degen",)))
    a((u"R4 同じ軸を見ない", u"                if a in seen:\n                    out.append(refusal(\"R4\", 2, i, u\"次元\"))", u"                if False:\n                    out.append(refusal(\"R4\", 2, i, u\"次元\"))", R))
    a((u"R4 同じ軸の見方が (軸, member) の組", u"            seen = set()\n            for a in axes:", u"            seen = set()\n            for a in [tuple(x) for x in d if isinstance(x, list)]:", R))
    a((u"R4 昇順を <= で見る", u"            if any(axes[j] > axes[j + 1] for j in range(len(axes) - 1)):", u"            if any(axes[j] >= axes[j + 1] for j in range(len(axes) - 1)):", R))
    a((u"R4 昇順を最初の 2 つだけ見る", u"            if any(axes[j] > axes[j + 1] for j in range(len(axes) - 1)):", u"            if any(axes[j] > axes[j + 1] for j in range(min(1, len(axes) - 1))):", R))
    a((u"R4 昇順を見ない", u"            if any(axes[j] > axes[j + 1] for j in range(len(axes) - 1)):", u"            if False:", R))
    a((u"R4 個別の軸を見ない", u"            if AXIS_CONS in axes:", u"            if False:", R))
    a((u"R4 個別の軸を member も見る", u"            if AXIS_CONS in axes:", u"            if AXIS_CONS in axes or MEMBER_IND in [x[1] for x in d if isinstance(x, list) and len(x) == 2]:", R))
    # ---- R5〜R9
    a((u"R5 値の型を見ない", u"            if not isinstance(v, str):\n                out.append(refusal(\"R5\", 0, i, u\"値\"))", u"            if False:\n                out.append(refusal(\"R5\", 0, i, u\"値\"))", R))
    a((u"R5 形を全体で見ない(match)", u"elif v != VALUE_NONE and not VALUE_RE.fullmatch(v):", u"elif v != VALUE_NONE and not VALUE_RE.match(v):", R))
    a((u"R5 頭の 0 を通す", u'VALUE_RE = re.compile(r"-?(0|[1-9][0-9]*)(\\.[0-9]*[1-9])?", re.ASCII)', u'VALUE_RE = re.compile(r"-?[0-9]+(\\.[0-9]*[1-9])?", re.ASCII)', R))
    a((u"R5 末尾の 0 を通す", u'VALUE_RE = re.compile(r"-?(0|[1-9][0-9]*)(\\.[0-9]*[1-9])?", re.ASCII)', u'VALUE_RE = re.compile(r"-?(0|[1-9][0-9]*)(\\.[0-9]+)?", re.ASCII)', R))
    a((u"R5 `-0` を通さない", u'VALUE_RE = re.compile(r"-?(0|[1-9][0-9]*)(\\.[0-9]*[1-9])?", re.ASCII)', u'VALUE_RE = re.compile(r"(-?[1-9][0-9]*|0)(\\.[0-9]*[1-9])?", re.ASCII)', R))
    a((u"R5 `+` を通す", u'VALUE_RE = re.compile(r"-?(0|[1-9][0-9]*)(\\.[0-9]*[1-9])?", re.ASCII)', u'VALUE_RE = re.compile(r"[-+]?(0|[1-9][0-9]*)(\\.[0-9]*[1-9])?", re.ASCII)', R))
    a((u"R5 全角の数字を通す", u'VALUE_RE = re.compile(r"-?(0|[1-9][0-9]*)(\\.[0-9]*[1-9])?", re.ASCII)', u'VALUE_RE = re.compile(r"-?(0|[1-9]\\d*)(\\.\\d*[1-9])?")', R))
    a((u"R5 空の字を通す", u'VALUE_RE = re.compile(r"-?(0|[1-9][0-9]*)(\\.[0-9]*[1-9])?", re.ASCII)', u'VALUE_RE = re.compile(r"-?(0|[1-9][0-9]*)?(\\.[0-9]*[1-9])?", re.ASCII)', R))
    a((u"R5 小数点だけを通す", u'VALUE_RE = re.compile(r"-?(0|[1-9][0-9]*)(\\.[0-9]*[1-9])?", re.ASCII)', u'VALUE_RE = re.compile(r"-?(0|[1-9][0-9]*)?(\\.[0-9]*)?", re.ASCII)', R))
    a((u"R5 整数の部が無い小数を通す", u'VALUE_RE = re.compile(r"-?(0|[1-9][0-9]*)(\\.[0-9]*[1-9])?", re.ASCII)', u'VALUE_RE = re.compile(r"-?(0|[1-9][0-9]*)?(\\.[0-9]*[1-9])?", re.ASCII)', R))
    a((u"R5 小数の整数の部の 0 だけ通す(0.5 を断る)", u'VALUE_RE = re.compile(r"-?(0|[1-9][0-9]*)(\\.[0-9]*[1-9])?", re.ASCII)', u'VALUE_RE = re.compile(r"-?([1-9][0-9]*|0)(\\.[0-9]*[1-9])?(?<!^0\\.5)", re.ASCII)', R))
    a((u"R5 無い の全角を通す", u"VALUE_NONE = u\"無い\"", u"VALUE_NONE = u\"無い \"", R))
    a((u"R6 通貨を小文字も通す", u'UNIT_FORM_RE = re.compile(u"通貨:[A-Z]{3}(÷株)?", re.ASCII)', u'UNIT_FORM_RE = re.compile(u"通貨:[A-Za-z]{3}(÷株)?", re.ASCII)', R))
    a((u"R6 通貨の長さを 2〜3 通す", u'UNIT_FORM_RE = re.compile(u"通貨:[A-Z]{3}(÷株)?", re.ASCII)', u'UNIT_FORM_RE = re.compile(u"通貨:[A-Z]{2,3}(÷株)?", re.ASCII)', R))
    a((u"R6 通貨の長さを 3 以上通す", u'UNIT_FORM_RE = re.compile(u"通貨:[A-Z]{3}(÷株)?", re.ASCII)', u'UNIT_FORM_RE = re.compile(u"通貨:[A-Z]{3,}(÷株)?", re.ASCII)', R))
    a((u"R6 全体で見ない(match)", u"    if u in (UNIT_SHARES, UNIT_PURE) or UNIT_FORM_RE.fullmatch(u):", u"    if u in (UNIT_SHARES, UNIT_PURE) or UNIT_FORM_RE.match(u):", R))
    a((u"R6 株 を通さない", u"    if u in (UNIT_SHARES, UNIT_PURE) or UNIT_FORM_RE.fullmatch(u):", u"    if u in (UNIT_PURE,) or UNIT_FORM_RE.fullmatch(u):", R))
    a((u"R6 `他:` の見方が前方一致の無視", u"    if not u.startswith(UNIT_OTHER):\n        return 1", u"    if UNIT_OTHER not in u:\n        return 1", R))
    a((u"R6 `÷` が 2 つでもよい", u"    if len(parts) > 2:\n        return 1", u"    if len(parts) > 3:\n        return 1", R))
    a((u"R6 空の measure を通す", u"        if not p or any((m == \"\" or re.search(r\"\\s\", m)) for m in ms) or ms != sorted(ms):", u"        if any(re.search(r\"\\s\", m) for m in ms) or ms != sorted(ms):", R))
    a((u"R6 measure の空白を通す", u"        if not p or any((m == \"\" or re.search(r\"\\s\", m)) for m in ms) or ms != sorted(ms):", u"        if not p or any((m == \"\") for m in ms) or ms != sorted(ms):", R))
    a((u"R6 measure の並びを見ない", u"        if not p or any((m == \"\" or re.search(r\"\\s\", m)) for m in ms) or ms != sorted(ms):", u"        if not p or any((m == \"\" or re.search(r\"\\s\", m)) for m in ms):", R))
    a((u"R6 4 つの形に当たる 他: を見ない", u"        if len(m) == 1 and (m[0] in (\"xbrli:shares\", \"xbrli:pure\") or CUR_MEASURE_RE.fullmatch(m[0])):\n            return 2", u"        if False:\n            return 2", R))
    a((u"R6 4 つの形の 純数 を見ない", u"        if len(m) == 1 and (m[0] in (\"xbrli:shares\", \"xbrli:pure\") or CUR_MEASURE_RE.fullmatch(m[0])):", u"        if len(m) == 1 and (m[0] in (\"xbrli:shares\",) or CUR_MEASURE_RE.fullmatch(m[0])):", R))
    a((u"R6 4 つの形の 株 を見ない", u"        if len(m) == 1 and (m[0] in (\"xbrli:shares\", \"xbrli:pure\") or CUR_MEASURE_RE.fullmatch(m[0])):", u"        if len(m) == 1 and (m[0] in (\"xbrli:pure\",) or CUR_MEASURE_RE.fullmatch(m[0])):", R))
    a((u"R6 4 つの形の通貨を小文字も", u'CUR_MEASURE_RE = re.compile(r"iso4217:[A-Z]{3}", re.ASCII)', u'CUR_MEASURE_RE = re.compile(r"iso4217:[A-Za-z]{3}", re.ASCII)', R))
    a((u"R6 4 つの形の 円÷株 を見ない", u"    elif len(groups[0]) == 1 and len(groups[1]) == 1 and CUR_MEASURE_RE.fullmatch(groups[0][0]) and groups[1][0] == \"xbrli:shares\":\n        return 2", u"    elif False:\n        return 2", R))
    a((u"R6 4 つの形の分母を見ない", u"CUR_MEASURE_RE.fullmatch(groups[0][0]) and groups[1][0] == \"xbrli:shares\":", u"CUR_MEASURE_RE.fullmatch(groups[0][0]):", R))
    a((u"R6 4 つの形の分子の数を見ない", u"    elif len(groups[0]) == 1 and len(groups[1]) == 1 and CUR_MEASURE_RE", u"    elif len(groups[1]) == 1 and CUR_MEASURE_RE", R))
    a((u"R7 真偽を整数と見る", u"                    if type(x) is not int:", u"                    if not isinstance(x, int):", R))
    a((u"R7 小数を整数と見る", u"                    if type(x) is not int:", u"                    if not isinstance(x, (int, float)):", R))
    a((u"R7 字を整数と見る", u"                    if type(x) is not int:", u"                    if not isinstance(x, (int, str)):", R))
    a((u"R7 型を見ない", u"                    if type(x) is not int:", u"                    if False:", R))
    a((u"R7 1000 も断る", u"                    elif abs(x) > MAX_EXP:", u"                    elif abs(x) >= MAX_EXP:", R))
    a((u"R7 1001 を通す", u"                    elif abs(x) > MAX_EXP:", u"                    elif abs(x) > MAX_EXP + 1:", R))
    a((u"R7 負の側を見ない", u"                    elif abs(x) > MAX_EXP:", u"                    elif x > MAX_EXP:", R))
    a((u"R7 無い の null を見ない", u"                elif x is not None:\n                    out.append(refusal(\"R7\", 2, i, f))", u"                elif False:\n                    out.append(refusal(\"R7\", 2, i, f))", R))
    a((u"R7 無い の null を 0 と取り違える", u"                elif x is not None:\n                    out.append(refusal(\"R7\", 2, i, f))", u"                elif x != 0:\n                    out.append(refusal(\"R7\", 2, i, f))", R))
    a((u"R7 値が在るの見方が null でない", u"            has_value = v != VALUE_NONE", u"            has_value = v is not None", R))
    a((u"R7 値が在るの見方が字だけ", u"            has_value = v != VALUE_NONE", u"            has_value = isinstance(v, str) and v != VALUE_NONE", R))
    a((u"R7 を値の 3 欄が揃うときだけ見る", u"        if u\"値\" in r and u\"表示の位\" in r and u\"精度\" in r:", u"        if u\"値\" in r and u\"表示の位\" in r and u\"精度\" in r and isinstance(v, str) and VALUE_RE.fullmatch(v) is not None or v == VALUE_NONE:", R))
    a((u"R8 精度 + 位 = 0 も断る", u"                if r[u\"表示の位\"] + r[u\"精度\"] < 0:", u"                if r[u\"表示の位\"] + r[u\"精度\"] <= 0:", R))
    a((u"R8 の符号が逆", u"                if r[u\"表示の位\"] + r[u\"精度\"] < 0:", u"                if r[u\"表示の位\"] + r[u\"精度\"] > 0:", R))
    a((u"R8 を位だけで見る", u"                if r[u\"表示の位\"] + r[u\"精度\"] < 0:", u"                if r[u\"精度\"] < 0:", R))
    a((u"R8 を精度だけで見る", u"                if r[u\"表示の位\"] + r[u\"精度\"] < 0:", u"                if r[u\"表示の位\"] < 0:", R))
    a((u"R8 を引き算にする", u"                if r[u\"表示の位\"] + r[u\"精度\"] < 0:", u"                if r[u\"表示の位\"] - r[u\"精度\"] < 0:", R))
    a((u"R8・R9 を R1〜R7 に当たった行にも掛ける", u"            if not hit and has_value:", u"            if has_value and isinstance(v, str) and VALUE_RE.fullmatch(v) and type(r[u\"表示の位\"]) is int and type(r[u\"精度\"]) is int:", R))
    a((u"R9 を R8 のときだけ見る", u"                if not multiple_of_precision(v, r[u\"精度\"]):", u"                if r[u\"表示の位\"] + r[u\"精度\"] < 0 and not multiple_of_precision(v, r[u\"精度\"]):", R))
    a((u"R9 の桁が 1 つ多い", u"    k = len(fp) - prec\n", u"    k = len(fp) - prec + 1\n", R))
    a((u"R9 の桁が 1 つ少ない", u"    k = len(fp) - prec\n", u"    k = len(fp) - prec - 1\n", R))
    a((u"R9 の末尾の 0 の数が k 未満を通す", u"    return len(digits) - len(digits.rstrip(\"0\")) >= k", u"    return len(digits) - len(digits.rstrip(\"0\")) >= k - 1", R))
    a((u"R9 の末尾の 0 の数が k 超だけ通す", u"    return len(digits) - len(digits.rstrip(\"0\")) >= k", u"    return len(digits) - len(digits.rstrip(\"0\")) > k", R))
    a((u"R9 の k = 0 を断る", u"    if digits == \"\" or k <= 0:\n        return True", u"    if digits == \"\" or k < 0:\n        return True", R))
    a((u"R9 の値 0 を断る", u"    if digits == \"\" or k <= 0:\n        return True", u"    if k <= 0:\n        return True", R))
    a((u"R9 の負の精度を見ない", u"    if digits == \"\" or k <= 0:\n        return True", u"    if digits == \"\" or k <= 0 or prec < 0:\n        return True", R))
    a((u"R9 の符号を数える", u"    body = value[1:] if value.startswith(\"-\") else value", u"    body = value", R))
    a((u"R9 の整数の部の頭の 0 を数える", u"    digits = (ip + fp).lstrip(\"0\")", u"    digits = (ip + fp)", R))
    a((u"R9 の小数の部だけ見る", u"    digits = (ip + fp).lstrip(\"0\")", u"    digits = fp.lstrip(\"0\") or \"\"", R))
    a((u"R9 を整数に直して見る(桁が 4000 を超えると落ちる版。python 3.11 以降の int の字数の上限の再現)", u"    digits = (ip + fp).lstrip(\"0\")\n", u"    digits = (ip + fp).lstrip(\"0\")\n    if len(ip + fp) > 4000:\n        raise ValueError(\"int limit\")\n", (u"degen",)))
    # ---- R10〜R13・R1〜R7 に当たった行の除外
    a((u"R10 後ろでなく先の行を断る", u"            out.append(refusal(\"R10\", 0, i, u\"行\"))", u"            out.append(refusal(\"R10\", 0, seen[key], u\"行\"))", R))
    a((u"R10 を最後の行だけ断る", u"        if key in seen:\n            out.append(refusal(\"R10\", 0, i, u\"行\"))\n        else:\n            seen[key] = i", u"        if key in seen:\n            out.append(refusal(\"R10\", 0, i, u\"行\"))\n            seen[key] = i\n        else:\n            seen[key] = i", R))
    a((u"R10 の鍵に対象を入れない", u"        key = (r[u\"種類\"], r[u\"科目\"], period_key(r[u\"期間\"]), r[u\"対象\"], tuple(tuple(x) for x in r[u\"次元\"]))", u"        key = (r[u\"種類\"], r[u\"科目\"], period_key(r[u\"期間\"]), tuple(tuple(x) for x in r[u\"次元\"]))", R))
    a((u"R10 の鍵に次元を入れない", u"        key = (r[u\"種類\"], r[u\"科目\"], period_key(r[u\"期間\"]), r[u\"対象\"], tuple(tuple(x) for x in r[u\"次元\"]))", u"        key = (r[u\"種類\"], r[u\"科目\"], period_key(r[u\"期間\"]), r[u\"対象\"])", R))
    a((u"R10 の鍵に期間を入れない", u"        key = (r[u\"種類\"], r[u\"科目\"], period_key(r[u\"期間\"]), r[u\"対象\"], tuple(tuple(x) for x in r[u\"次元\"]))", u"        key = (r[u\"種類\"], r[u\"科目\"], r[u\"対象\"], tuple(tuple(x) for x in r[u\"次元\"]))", R))
    a((u"R10 の鍵に種類を入れない", u"        key = (r[u\"種類\"], r[u\"科目\"], period_key(r[u\"期間\"]), r[u\"対象\"], tuple(tuple(x) for x in r[u\"次元\"]))", u"        key = (r[u\"科目\"], period_key(r[u\"期間\"]), r[u\"対象\"], tuple(tuple(x) for x in r[u\"次元\"]))", R))
    a((u"R10 の鍵に科目を入れない", u"        key = (r[u\"種類\"], r[u\"科目\"], period_key(r[u\"期間\"]), r[u\"対象\"], tuple(tuple(x) for x in r[u\"次元\"]))", u"        key = (r[u\"種類\"], period_key(r[u\"期間\"]), r[u\"対象\"], tuple(tuple(x) for x in r[u\"次元\"]))", R))
    a((u"R10 の期間の鍵を種類だけにする", u"    return tuple(sorted(p.items()))", u"    return tuple(sorted(p))", R))
    a((u"R11 少ない側でなく多い側を断る", u"            for i in (inst if len(inst) < len(dur) else dur):", u"            for i in (inst if len(inst) > len(dur) else dur):", R))
    a((u"R11 同じ数のとき時点の側を断る", u"            for i in (inst if len(inst) < len(dur) else dur):", u"            for i in (inst if len(inst) <= len(dur) else dur):", R))
    a((u"R11 いつも期間を断る", u"            for i in (inst if len(inst) < len(dur) else dur):", u"            for i in dur:", R))
    a((u"R11 いつも時点を断る", u"            for i in (inst if len(inst) < len(dur) else dur):", u"            for i in inst:", R))
    a((u"R11 を両方断る", u"            for i in (inst if len(inst) < len(dur) else dur):", u"            for i in inst + dur:", R))
    a((u"R11 の後ろの 1 行だけ断る", u"            for i in (inst if len(inst) < len(dur) else dur):", u"            for i in (inst if len(inst) < len(dur) else dur)[-1:]:", R))
    a((u"R11 の先の 1 行だけ断る", u"            for i in (inst if len(inst) < len(dur) else dur):", u"            for i in (inst if len(inst) < len(dur) else dur)[:1]:", R))
    a((u"R11 を数の行だけで見る", u"        inst = [i for i, r in rs if u\"時点\" in r[u\"期間\"]]\n        dur = [i for i, r in rs if u\"時点\" not in r[u\"期間\"]]", u"        inst = [i for i, r in rs if u\"時点\" in r[u\"期間\"] and r[u\"種類\"] == KIND_NUM]\n        dur = [i for i, r in rs if u\"時点\" not in r[u\"期間\"] and r[u\"種類\"] == KIND_NUM]", R))
    a((u"R12 いちばん少ない単位を残す", u"            keep = sorted(units, key=lambda u: (-units[u], u))[0]", u"            keep = sorted(units, key=lambda u: (units[u], u))[0]", R))
    a((u"R12 同じ数なら字の降順で先を残す", u"            keep = sorted(units, key=lambda u: (-units[u], u))[0]", u"            keep = sorted(units, key=lambda u: (-units[u], u))[-1]", R))
    a((u"R12 同じ数なら最初に出た単位を残す", u"            keep = sorted(units, key=lambda u: (-units[u], u))[0]", u"            keep = nums[0][1][u\"単位\"]", R))
    a((u"R12 同じ数なら最後に出た単位を残す", u"            keep = sorted(units, key=lambda u: (-units[u], u))[0]", u"            keep = nums[-1][1][u\"単位\"]", R))
    a((u"R12 の字の昇順を数の昇順にする", u"            keep = sorted(units, key=lambda u: (-units[u], u))[0]", u"            keep = sorted(units, key=lambda u: (-units[u], len(u)))[0]", R))
    a((u"R12 を残す単位の行も断る", u"                if r[u\"単位\"] != keep:", u"                if True:", R))
    a((u"R12 を断る行の見方が先の 1 行", u"            for i, r in nums:\n                if r[u\"単位\"] != keep:\n                    out.append(refusal(\"R12\", 0, i, u\"単位\"))", u"            for i, r in nums[:1]:\n                if r[u\"単位\"] != keep:\n                    out.append(refusal(\"R12\", 0, i, u\"単位\"))", R))
    a((u"R12 を単位が 3 通り以上で見る", u"        if len(units) > 1:", u"        if len(units) > 2:", R))
    a((u"R13 少ない側でなく多い側を断る", u"            for i in ([i for i, _r in nums] if len(nums) < len(texts) else texts):", u"            for i in ([i for i, _r in nums] if len(nums) > len(texts) else texts):", R))
    a((u"R13 同じ数のとき数の側を断る", u"            for i in ([i for i, _r in nums] if len(nums) < len(texts) else texts):", u"            for i in ([i for i, _r in nums] if len(nums) <= len(texts) else texts):", R))
    a((u"R13 いつも文を断る", u"            for i in ([i for i, _r in nums] if len(nums) < len(texts) else texts):", u"            for i in texts:", R))
    a((u"R13 いつも数を断る", u"            for i in ([i for i, _r in nums] if len(nums) < len(texts) else texts):", u"            for i in [i for i, _r in nums]:", R))
    a((u"R13 を両方断る", u"            for i in ([i for i, _r in nums] if len(nums) < len(texts) else texts):", u"            for i in [i for i, _r in nums] + texts:", R))
    a((u"R13 の科目の組み方を名の前半だけにする", u"        by.setdefault(r[u\"科目\"], []).append((i, r))", u"        by.setdefault(r[u\"科目\"].split(u\":\")[0], []).append((i, r))", R))
    a((u"R11〜R13 の科目の組み方を種類ごとにする", u"        by.setdefault(r[u\"科目\"], []).append((i, r))", u"        by.setdefault((r[u\"種類\"], r[u\"科目\"]), []).append((i, r))", R))
    a((u"R1〜R7 に当たった行も R10〜R13 に掛ける", u"        if not check_row(i, r, names, custom, out) and isinstance(r.get(u\"科目\"), str):", u"        if (not check_row(i, r, names, custom, out) or True) and isinstance(r.get(u\"科目\"), str) and isinstance(r.get(u\"期間\"), dict) and isinstance(r.get(u\"次元\"), list) and isinstance(r.get(u\"種類\"), str):", R))
    a((u"科目が字でない行を R10〜R13 に掛ける(落ちる)", u"        if not check_row(i, r, names, custom, out) and isinstance(r.get(u\"科目\"), str):", u"        if not check_row(i, r, names, custom, out):", R + (u"degen",)))
    a((u"断りの並べ替えをしない", u"    return sorted(out, key=lambda x: (RULE_ORDER.index(x[u\"規則\"]), x[u\"行\"] if x[u\"行\"] is not None else 0, x[u\"欄\"], x[u\"理由\"]))", u"    return out", R))
    a((u"断りの並びの行を見ない", u"    return sorted(out, key=lambda x: (RULE_ORDER.index(x[u\"規則\"]), x[u\"行\"] if x[u\"行\"] is not None else 0, x[u\"欄\"], x[u\"理由\"]))", u"    return sorted(out, key=lambda x: (RULE_ORDER.index(x[u\"規則\"]), x[u\"欄\"], x[u\"理由\"]))", R))
    a((u"断りの並びが規則の表の逆順", u"    return sorted(out, key=lambda x: (RULE_ORDER.index(x[u\"規則\"]), x[u\"行\"] if x[u\"行\"] is not None else 0, x[u\"欄\"], x[u\"理由\"]))", u"    return sorted(out, key=lambda x: (-RULE_ORDER.index(x[u\"規則\"]), x[u\"行\"] if x[u\"行\"] is not None else 0, x[u\"欄\"], x[u\"理由\"]))", R))
    a((u"断りの理由が規則の表の別の条件", u"    return od([(u\"行\", row), (u\"欄\", field), (u\"規則\", rule), (u\"理由\", RULE_CONDS[rule][idx])])", u"    return od([(u\"行\", row), (u\"欄\", field), (u\"規則\", rule), (u\"理由\", RULE_CONDS[rule][0])])", R))
    a((u"断りの鍵の並びが違う", u"    return od([(u\"行\", row), (u\"欄\", field), (u\"規則\", rule), (u\"理由\", RULE_CONDS[rule][idx])])", u"    return od([(u\"欄\", field), (u\"行\", row), (u\"規則\", rule), (u\"理由\", RULE_CONDS[rule][idx])])", R))
    return M

    return M



# ======================================================================== 11a. 直し 1(独立監査 REVISE): 孤立 surrogate が入った型の file でも受け口は落ちない・変え方の「選ばない」守りを 1 つずつ
SURR = u"\ud800"


def esc_json(o):
    u"""孤立 surrogate を ``\\ud800`` の形で書く(UTF-8 の file として書ける JSON の字)。"""
    return json.dumps(o, ensure_ascii=True)


def accept_inproc(ms, args):
    u"""``accept_main`` を、厳密な UTF-8 の標準出力(``buffer`` を持つ)に向けて同じ process で走らせる。守りを外すと書き込みで落ちる。(rc か例外名, 標準出力の byte, 標準のエラー)。"""
    raw = io.BytesIO()
    w = io.TextIOWrapper(raw, encoding="utf-8", newline="")
    e_ = io.StringIO()
    rc = None
    with contextlib.redirect_stdout(w), contextlib.redirect_stderr(e_):
        try:
            rc = ms.accept_main(list(args))
        except BaseException as exc:                # noqa: BLE001
            rc = u"例外: %s" % type(exc).__name__
    w.flush()
    return rc, raw.getvalue(), e_.getvalue()


def surrogate_cases():
    u"""(名前, 孤立 surrogate を入れた型の file の object)。(i) 数の行の鍵 (ii) 文の行の鍵 (iii) 書類の鍵 (iv) 独自の名の要素の鍵と値 (v) 期間の鍵 (vi) 科目の値・次元の値 (+ 頂の鍵・単位の値)。"""
    S = SURR

    def e(fn):
        return edit(fn)
    return [
        (u"i 数の行の鍵", e(lambda o: o[u"行"][0].__setitem__(S, 1))),
        (u"ii 文の行の鍵", e(lambda o: o[u"行"][9].__setitem__(S, 1))),
        (u"iii 書類の鍵", e(lambda o: o[u"書類"].__setitem__(S, 1))),
        (u"iv 独自の名の要素の鍵", e(lambda o: o[u"独自の名"][0].__setitem__(S, 1))),
        (u"iv 独自の名の要素の値", e(lambda o: o[u"独自の名"][0].__setitem__(u"名", S))),
        (u"v 期間の鍵", e(lambda o: o[u"行"][0][u"期間"].__setitem__(S, u"2031-03-31"))),
        (u"vi 科目の値", e(lambda o: o[u"行"][0].__setitem__(u"科目", S))),
        (u"vi 次元の値", e(lambda o: o[u"行"][3].__setitem__(u"次元", [[S, S]]))),
        (u"vii 頂の鍵", e(lambda o: o.__setitem__(S, 1))),
        (u"viii 単位の値", e(lambda o: o[u"行"][0].__setitem__(u"単位", S)))]


def surrogate_problems(ms=None):
    u"""孤立 surrogate(UTF-8 に直せない字)が入った型の file を ``--accept``・``--accept-dir`` に掛けても、例外で落ちず JSON の断りを返す。普通の入力では出力が 1 byte も変わらない。"""
    ms = ms or MS
    out = []
    with Temp() as d:
        nf = os.path.join(d, "n.json")
        wfile(nf, json.dumps(sorted(NAMES)))
        cases = surrogate_cases()
        dd = os.path.join(d, "many")
        wfile(os.path.join(dd, "good.json"), dump(base()))
        for i, (label, o) in enumerate(cases):
            wfile(os.path.join(d, "c%02d.json" % i), esc_json(o))
            wfile(os.path.join(dd, "s%02d.json" % i), esc_json(o))
        for i, (label, o) in enumerate(cases):
            rc, so, se = accept_inproc(ms, ["--accept", os.path.join(d, "c%02d.json" % i), "--names-file", nf])
            try:
                j = json.loads(so.decode("utf-8"), object_pairs_hook=od)
            except ValueError:
                out.append(u"surrogate(%s)の --accept の出力が JSON でない: rc=%s" % (label, rc))
                continue
            if rc != 0 or j.get(u"受理") is not False or len(j.get(u"断り", [])) < 1 or list(j) != [u"受理", u"断り"]:
                out.append(u"surrogate(%s)の --accept が受理か断りの正規の形でない: rc=%s" % (label, rc))
        # 鍵の字が出力で元の字に戻る(逃がした字を読み戻すと、入れた鍵と同じ)
        for i in (0, 1):
            rc, so, se = accept_inproc(ms, ["--accept", os.path.join(d, "c%02d.json" % i), "--names-file", nf])
            try:
                got = [x[u"欄"] for x in json.loads(so.decode("utf-8"))[u"断り"]]
            except (ValueError, KeyError):
                got = []
            if SURR not in got or b"\\ud800" not in so:
                out.append(u"surrogate の鍵が \\uXXXX の形で出ていない: case %d %s" % (i, got))
        # folder: surrogate の file と正常な file を並べても、正常な file の結果が返る
        rc, so, se = accept_inproc(ms, ["--accept-dir", dd, "--names-file", nf])
        try:
            j = json.loads(so.decode("utf-8"), object_pairs_hook=od)
        except ValueError:
            out.append(u"surrogate の file を含む folder の出力が JSON でない: rc=%s" % rc)
            j = None
        if j is not None:
            want = sorted([u"good.json"] + [u"s%02d.json" % i for i in range(len(cases))])
            if rc != 0 or list(j) != want or j[u"good.json"] != od([(u"受理", True), (u"断り", [])]) or any(j[k][u"受理"] or not j[k][u"断り"] for k in want if k != u"good.json"):
                out.append(u"surrogate の file を含む folder の結果が違う: rc=%s" % rc)
        # 普通の入力では出力が 1 byte も変わらない(日本語の字は escape しない)
        bad = os.path.join(d, "bad.json")
        wfile(bad, dump(edit(set_row(1, u"値", u"1,2"))))
        rc, so, se = accept_inproc(ms, ["--accept", bad, "--names-file", nf])
        want_b = (json.dumps(ms.result_of(ms.check_text(dump(edit(set_row(1, u"値", u"1,2"))), NAMES)), ensure_ascii=False, indent=1) + u"\n").encode("utf-8")
        if so != want_b or rc != 0 or u"断り".encode("utf-8") not in so or b"\\u" in so:
            out.append(u"普通の入力の出力が変わった")
        # 別の process(python3 -I・空の場所)でも全部。標準出力は JSON として読め、終わりの値は 0
        empty = os.path.join(d, "empty")
        os.makedirs(empty)
        argvs = [["--accept", os.path.join(d, "c%02d.json" % i), "--names-file", nf] for i in range(len(cases))] + [["--accept-dir", dd, "--names-file", nf]]
        for argv in argvs:
            p = subprocess.run([sys.executable, "-I", ms.SCRIPT_PATH] + argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=empty)
            try:
                j = json.loads(p.stdout.decode("utf-8"))
            except ValueError:
                j = None
            if p.returncode != 0 or j is None or b"Traceback" in p.stderr:
                out.append(u"別の process の受け口が surrogate で落ちる: %s rc=%s" % (os.path.basename(argv[1]), p.returncode))
            elif argv[0] == "--accept" and (j[u"受理"] is not False or not j[u"断り"]):
                out.append(u"別の process の受け口が surrogate の file を断らない: %s" % os.path.basename(argv[1]))
            elif argv[0] == "--accept-dir" and j[u"good.json"][u"受理"] is not True:
                out.append(u"別の process の受け口が folder の正常な file を返さない")
        if os.listdir(empty):
            out.append(u"受け口が空の場所に file を書いた")
        # 型から作る命令: 受け口が受理した(識別子の scheme に surrogate)型の file からは、落ちずに断る(か終わる)。出力の folder は残らない。別の process
        zp, root, v1, files = derive_fake(ms, d)
        typ = load_type(root)
        typ[u"書類"][u"識別子の scheme"] = typ[u"書類"][u"識別子の scheme"] + SURR
        wfile(os.path.join(root, "type", "type.json"), esc_json(typ))
        wfile(os.path.join(d, "n2.json"), json.dumps(sorted(NAMES2)))
        p = subprocess.run([sys.executable, "-I", ms.SCRIPT_PATH, "--build", root, os.path.join(d, "bout"), "--names-file", os.path.join(d, "n2.json")], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=empty)
        if p.returncode not in (1, 2) or b"Traceback" in p.stderr or os.path.exists(os.path.join(d, "bout")):
            out.append(u"surrogate の入った型の file から作る命令が落ちる・出力を残す: rc=%s" % p.returncode)
    out.extend(surrogate_break_problems(ms))
    return out


def surrogate_break_problems(ms=None):
    u"""受理される型の file(識別子の scheme・提出者の識別子に孤立 surrogate)で ``--break`` が Traceback なく終わる(別の process)・同じ process で ``run_break`` が壊し方 44・変え方 6 を返す・普通の入力では書き出す file が 1 byte も変わらない。"""
    ms = ms or MS
    out = []
    with Temp() as d:
        nf = os.path.join(d, "n.json")
        wfile(nf, json.dumps(sorted(NAMES)))
        empty = os.path.join(d, "empty")
        os.makedirs(empty)
        for label, fn in ((u"scheme", lambda o: o[u"書類"].__setitem__(u"識別子の scheme", o[u"書類"][u"識別子の scheme"] + SURR)), (u"識別子", lambda o: o[u"書類"].__setitem__(u"提出者の識別子", SURR))):
            root = os.path.join(d, "r_" + label)
            wfile(os.path.join(root, "type", "type.json"), esc_json(edit(fn)))
            if ms.check_text(rfile(os.path.join(root, "type", "type.json")).decode("utf-8"), NAMES):
                out.append(u"surrogate(%s)の作り物の型の file を受け口が断る(作り物の誤り)" % label)
                continue
            p = subprocess.run([sys.executable, "-I", ms.SCRIPT_PATH, "--break", root, "--names-file", nf], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=empty)
            try:
                j = json.loads(p.stdout.decode("utf-8"))
            except ValueError:
                j = None
            if p.returncode != 0 or b"Traceback" in p.stderr or j is None or len(j.get(u"壊し方", {})) != 44 or len(j.get(u"形は合っているが中身が違う", {})) != 6:
                out.append(u"surrogate(%s)の型の file で --break が落ちる・数を返さない: rc=%s" % (label, p.returncode))
            lines = []
            try:
                brk, chg = ms.run_break(root, nf, say=lines.append)
            except BaseException as exc:                # noqa: BLE001
                out.append(u"surrogate(%s)の型の file で run_break が例外: %s" % (label, type(exc).__name__))
                continue
            if len(brk) != 44 or len(chg) != 6 or sum(v[u"作れた"] for v in brk.values()) < 1:
                out.append(u"surrogate(%s)の型の file で run_break の数が違う" % label)
        if os.listdir(empty):
            out.append(u"--break が空の場所に file を書いた")
        # 普通の入力: 書き出す file の字は write_variant_file の前後で同じ(日本語は escape しない・改行は変えない)
        wv = os.path.join(d, "wv.json")
        txt_ = u"{\n \"値\": \"日本語\"\n}\r\n"
        ms.write_variant_file(wv, txt_)
        if rfile(wv) != txt_.encode("utf-8"):
            out.append(u"write_variant_file が普通の字の byte を変えた")
        wv2 = os.path.join(d, "wv2.json")
        ms.write_variant_file(wv2, u"\"" + SURR + u"\"")
        if rfile(wv2) != b'"\\ud800"':
            out.append(u"write_variant_file が孤立 surrogate を \\uXXXX に逃がさない")
    return out


def row_diffs(a, b):
    u"""2 つの型の file の object の違い: [(行の番号, 欄, 新しい値)]。行の外の違いは (0, 鍵, None)。"""
    out = []
    for k in set(a) | set(b):
        if k != u"行" and a.get(k) != b.get(k):
            out.append((0, k, None))
    for i, (ra, rb) in enumerate(zip(a[u"行"], b[u"行"]), 1):
        for k in sorted(set(ra) | set(rb)):
            if ra.get(k) != rb.get(k):
                out.append((i, k, json.loads(json.dumps(rb.get(k)))))
    if len(a[u"行"]) != len(b[u"行"]):
        out.append((0, u"行", None))
    return sorted(out, key=lambda x: (x[0], x[1]))


def q_guard_cases():
    u"""(名前, 変え方, 型の file の object, 手で決めた変わる所 [(行, 欄, 新しい値)])。各 file は、先の候補が 1 つの「選ばない」守りだけに当たって選ばれず、あとの候補だけが選ばれる作り。"""
    I1, I2, I3 = per_i(u"2031-03-31"), per_i(u"2031-03-30"), per_i(u"2031-03-29")
    D1 = per_d(u"2030-04-01", u"2031-03-31")
    R = lambda name, per, value, unit=JPY, tgt=u"既定", dims=None, prec=0: num(name, per, tgt, dims or [], value, unit, 0, prec)       # noqa: E731
    NV = lambda name, per: num(name, per, u"既定", [], NONE_V, JPY, None, None)                                                       # noqa: E731
    cases = []
    # Q1: 対象(既定 ↔ 個別)。行 1 は文・行 2 は次元つき・行 3 は値が 無い・行 4,5 は相手が在る・行 6 だけが選ばれる(行 7 も選べる行で、番号の若い行 6 が選ばれる)
    cases.append((u"Q1", u"Q1", doc_of([txt(u"jpcrp_cor:Text", I1), R(u"jppfs_cor:Profit", D1, u"3", dims=[[SA, SM]]), NV(u"jppfs_cor:Receivable", I1), R(u"jppfs_cor:Assets", I1, u"10"),
                                       R(u"jppfs_cor:Assets", I1, u"20", tgt=u"個別"), R(u"jppfs_cor:Equity", I1, u"30"), R(u"jppfs_cor:Equity", I2, u"31")], [(u"member", SM), (u"軸", SA)]), [(6, u"対象", u"個別")]))
    # Q2: 科目。行 1 は値が 無い・行 2 は提出者別の科目の唯一の使い手・行 3(標準の科目の唯一の使い手)だけが選ばれ、その行の入れ替え先は行 8(行 1,2,4,5,6,7 は 1 つずつ別の守りで落ちる。行 9 も入れ替え先の候補で、番号の若い行 8 が選ばれる)
    cases.append((u"Q2", u"Q2", doc_of([NV(u"jppfs_cor:Receivable", I1), R(OWN, I1, u"7"), R(u"jppfs_cor:Assets", I1, u"10"), txt(u"jpcrp_cor:Text", I1),
                                       R(u"jppfs_cor:Profit", D1, u"30"), R(u"jppfs_cor:Ratio", I2, u"0.5", unit=PURE, prec=1), R(u"jppfs_cor:Equity", I1, u"40"), R(u"jppfs_cor:EPS", I3, u"50"),
                                       R(u"jpigp_cor:Item", I3, u"9")], [(u"科目", OWN)]), [(3, u"科目", u"jppfs_cor:EPS")]))
    # Q2b: 提出者別の科目でも使い手が 2 行なら選ぶ(行 1 が選ばれ、入れ替え先は行 4)
    cases.append((u"Q2b", u"Q2", doc_of([R(OWN, I1, u"7"), R(OWN, I2, u"8"), R(u"jppfs_cor:Assets", I1, u"10"), R(u"jppfs_cor:EPS", I3, u"50")], [(u"科目", OWN)]), [(1, u"科目", u"jppfs_cor:EPS")]))
    # Q3: 値。行 1 は値が 無い
    cases.append((u"Q3", u"Q3", doc_of([NV(u"jppfs_cor:Receivable", I1), R(u"jppfs_cor:Assets", I1, u"10"), R(u"jppfs_cor:Assets", I2, u"20")]), [(2, u"値", u"11")]))
    # Q4: 値の符号。行 1 は値が 無い・行 2 は値が -0・行 3 は値が 0(どちらも選ばれず、行 4 だけが変わる)
    cases.append((u"Q4", u"Q4", doc_of([NV(u"jppfs_cor:Receivable", I1), R(u"jppfs_cor:Assets", I1, u"-0"), R(u"jppfs_cor:Assets", I2, u"0"), R(u"jppfs_cor:Assets", I3, u"5"), R(u"jppfs_cor:Assets", per_i(u"2031-03-28"), u"7")]), [(4, u"値", u"-5")]))
    # Q4b: 先の候補の値が負なら、符号を取る
    cases.append((u"Q4b", u"Q4", doc_of([R(u"jppfs_cor:Assets", I1, u"-8"), R(u"jppfs_cor:Assets", I2, u"9")]), [(1, u"値", u"8")]))
    # Q5: 期間の日を 1 年前へ。行 1 は値が 無い・行 2 は 1 年・行 3 は始まりだけが 2 月 29 日・行 4 は終わりだけが 2 月 29 日・行 5 は時点が 2 月 29 日・行 6 は 1 年前に同じ組が在る・行 7 だけが選ばれる
    cases.append((u"Q5", u"Q5", doc_of([NV(u"jppfs_cor:Receivable", I1), R(u"jppfs_cor:Assets", per_i(u"0001-03-31"), u"10"), R(u"jppfs_cor:Profit", per_d(u"2028-02-29", u"2029-03-31"), u"20"),
                                       R(u"jppfs_cor:Profit", per_d(u"2027-03-01", u"2028-02-29"), u"25"), R(u"jppfs_cor:Equity", per_i(u"2028-02-29"), u"35"),
                                       R(u"jppfs_cor:Equity", per_i(u"2031-03-31"), u"30"), R(u"jppfs_cor:Equity", per_i(u"2030-03-31"), u"40"), R(u"jppfs_cor:Equity", per_i(u"2030-03-30"), u"50")]), [(7, u"期間", {u"時点": u"2029-03-31"})]))
    # Q5b: 2 月でも 29 日でない日は選ぶ・Q5c: 3 月 29 日(29 日だが 2 月でない)も選ぶ
    cases.append((u"Q5b", u"Q5", doc_of([R(u"jppfs_cor:Equity", per_i(u"2031-02-28"), u"10")]), [(1, u"期間", {u"時点": u"2030-02-28"})]))
    cases.append((u"Q5c", u"Q5", doc_of([R(u"jppfs_cor:Equity", per_i(u"2031-03-29"), u"10")]), [(1, u"期間", {u"時点": u"2030-03-29"})]))
    # Q6: 単位。行 1 は文・行 2,3 は同じ科目が 2 行・行 4 は単位が 純数・行 5 だけが選ばれる
    cases.append((u"Q6", u"Q6", doc_of([txt(u"jpcrp_cor:Text", I1), R(u"jppfs_cor:Assets", I1, u"10"), R(u"jppfs_cor:Assets", I2, u"20"), R(u"jppfs_cor:Ratio", I1, u"0.5", unit=PURE, prec=1),
                                       R(u"jppfs_cor:Profit", D1, u"30"), R(u"jppfs_cor:EPS", I1, u"40")]), [(5, u"単位", u"通貨:USD")]))
    return cases


def changer_guard_problems(ms=None):
    u"""変え方 Q1〜Q6 の「選ばない」守りを 1 つずつ縛る: 守りに当たる先の候補が選ばれず、決めた行だけが決めた値に変わり、変えた file を受け口が通す(断り 0)。"""
    ms = ms or MS
    out = []
    for label, qid, o, want in q_guard_cases():
        text = dump(o)
        got0 = guard(rr, ms, text)
        if got0:
            out.append(u"%s の作り物の file を受け口が通さない: %s" % (label, got0))
            continue
        made = guard(ms.make_variants, text, NAMES)
        if not isinstance(made, tuple):
            out.append(u"%s の作り物の file で変え方が例外: %s" % (label, made))
            continue
        new = made[1].get(qid)
        if new is None:
            out.append(u"%s の作り物の file で変え方が作れない" % label)
            continue
        got = row_diffs(o, parse_back(new))
        if got != want:
            out.append(u"%s が選んだ所が手の値と違う: 手の値 %s ≠ %s" % (label, want, got))
        if rr(ms, new):
            out.append(u"%s の変えた file を受け口が断る: %s" % (label, rr(ms, new)))
    return out


CHECKS = od([(u"rules", u"rules_problems"), (u"breaks", u"breaks_problems"), (u"degen", u"degenerate_problems"), (u"judge", u"judge_problems"), (u"dict", u"dict_problems"),
             (u"cli", u"accept_cli_problems"), (u"derive", u"derive_problems"), (u"doc", u"doc_problems"), (u"decline", u"decline_problems"), (u"render", u"render_problems"),
             (u"wiring", u"build_wiring_problems"), (u"iso", u"iso_problems"), (u"run", u"run_problems"), (u"verify", u"verify_problems"), (u"devrun", u"dev_run_problems"),
             (u"instr", u"instruction_problems"), (u"write", u"write_instruction_problems"), (u"main", u"main_dispatch_problems"),
             (u"count", u"count_problems"), (u"variant", u"variant_problems"), (u"valone", u"verify_alone_problems"), (u"units", u"units_problems"),
             (u"surr", u"surrogate_problems"), (u"qguard", u"changer_guard_problems")])


def check_by_name(tag):
    return globals()[CHECKS[tag]]


def mutant_source(old, new):
    u"""``old`` が script に在るだけ(1 回でも 2 回でも)全部 ``new`` にした字。無ければ None。"""
    return SRC0.replace(old, new) if old in SRC0 else None


def run_one(src, tags):
    u"""変異の字を module にして ``tags`` の検査を掛ける。(赤くした検査の tag の並び, 読み込みの失敗)。"""
    try:
        mod = load_source(src)
    except BaseException as exc:                # noqa: BLE001
        return [u"load"], type(exc).__name__
    red = []
    for t in tags:
        try:
            if check_by_name(t)(mod):
                red.append(t)
        except BaseException:                # noqa: BLE001
            red.append(t)
    return red, None


def fix1_mutants():
    u"""直し 1 の変異(名前, 元の字, 新しい字, 検査の名前の並び)。**予測(実行より先に書いた)**: 受け口の書き込みの守りを外す・変える変異は surr が赤・変え方の「選ばない」守りを外す変異は qguard が赤。
    黙ると予測したもの(同値): Q2 の ``r2 科目 != r 科目``(外しても同じ科目の候補は ``k in keys`` で落ちる)・Q5 の ``d is None``(受理された型の file の日は全部読める)・Q6 の ``is_num(r)``(文の行の ``count`` は 0 で ``== 1`` が偽)。"""
    M = []
    a = M.append
    SU = (u"surr",)
    EMIT = u'emit_json_text(json.dumps(res, ensure_ascii=False, indent=1) + "\\n")                       # 1 つの file の結果(入力由来の字は鍵の字)'
    EMIT_D = u'emit_json_text(json.dumps(res, ensure_ascii=False, indent=1) + "\\n")                       # folder の結果(入力由来の字は file の名と鍵の字)'
    PLAIN = u'sys.stdout.write(json.dumps(res, ensure_ascii=False, indent=1) + "\\n")'
    a((u"E1 --accept の書き込みを元の書き方へ戻す", EMIT, PLAIN, SU))
    a((u"E2 --accept-dir の書き込みを元の書き方へ戻す", EMIT_D, PLAIN, SU))
    a((u"E3 逃がしを strict にする", u'safe = text.encode("utf-8", "backslashreplace")', u'safe = text.encode("utf-8")', SU))
    a((u"E4 逃がしを replace にする", u'safe = text.encode("utf-8", "backslashreplace")', u'safe = text.encode("utf-8", "replace")', SU))
    a((u"E5 逃がしを ignore にする", u'safe = text.encode("utf-8", "backslashreplace")', u'safe = text.encode("utf-8", "ignore")', SU))
    a((u"E6 逃がしを xmlcharrefreplace にする(JSON で読めない)", u'safe = text.encode("utf-8", "backslashreplace")', u'safe = text.encode("utf-8", "xmlcharrefreplace")', SU))
    a((u"E7 日本語も ASCII に逃がす", u'safe = text.encode("utf-8", "backslashreplace")', u'safe = text.encode("ascii", "backslashreplace")', SU))
    a((u"E8 出力に ensure_ascii=True を使う(普通の字が変わる)", EMIT, EMIT.replace(u"ensure_ascii=False", u"ensure_ascii=True"), SU))
    a((u"E9 出力の終わりの改行を落とす", EMIT, EMIT.replace(u' + "\\n")', u')'), SU))
    a((u"E10 --accept-dir の結果を --accept の字で出す(file の名の鍵を落とす)", EMIT_D, EMIT_D.replace(u"json.dumps(res,", u"json.dumps(list(res.values())[0] if res else res,"), SU))
    SB = (u"surr",)
    WV = u'    with open(path, "wb") as fh:\n        fh.write(text.encode("utf-8", "backslashreplace"))'
    a((u"E12 --break の file の書き込みを strict にする", WV, WV.replace(u'"backslashreplace"', u'"strict"'), SB))
    a((u"E13 --break の file の書き込みを replace にする", WV, WV.replace(u'"backslashreplace"', u'"replace"'), SB))
    a((u"E14 --break の file の書き込みを ignore にする", WV, WV.replace(u'"backslashreplace"', u'"ignore"'), SB))
    a((u"E15 --break の file の書き込みを元の書き方(text mode・utf-8)へ戻す", WV, u'    with io.open(path, "w", encoding="utf-8", newline="") as fh:\n        fh.write(text)', SB))
    a((u"E16 --break の file の書き込みが日本語も ASCII に逃がす", WV, WV.replace(u'"utf-8"', u'"ascii"'), SB))
    a((u"E18 壊し方の file を write_variant_file でなく元の書き方で書く", u'            write_variant_file(os.path.join(folder, bid + ".json"), made[1])', u'            with io.open(os.path.join(folder, bid + ".json"), "w", encoding="utf-8", newline="") as fh:\n                fh.write(made[1])', SB))
    a((u"E19 変えた file を write_variant_file でなく元の書き方で書く", u'            write_variant_file(os.path.join(folder, qid + ".json"), text)', u'            with io.open(os.path.join(folder, qid + ".json"), "w", encoding="utf-8", newline="") as fh:\n                fh.write(text)', SB))
    a((u"E20 --break が run_variants の例外を握りつぶして 0 を返す", u'        brk, chg = run_variants(text, names, work, work, None, names_file)', u'        brk, chg = od(), od()', SB))
    a((u"E11 受け口が例外で落ちるのを許す(check_safe の守りを外す)", u"    try:\n        return check_bytes(data, names)\n    except Exception:                                      # noqa: BLE001\n        return [refusal(\"S1\", 0, None, u\"file\")]", u"    return check_bytes(data, names)", (u"degen", u"surr", u"rules")))
    # ---- 変え方の「選ばない」守り(1 つずつ)
    QG = (u"qguard",)
    a((u"Q1a 文の行も選ぶ", u'        if is_num(r) and not r[u"次元"] and r[u"値"] != VALUE_NONE:', u'        if not r[u"次元"] and r[u"値"] != VALUE_NONE:', QG))
    a((u"Q1b 次元つきの行も選ぶ", u'        if is_num(r) and not r[u"次元"] and r[u"値"] != VALUE_NONE:', u'        if is_num(r) and r[u"値"] != VALUE_NONE:', QG))
    a((u"Q1c 値が 無い 行も選ぶ", u'        if is_num(r) and not r[u"次元"] and r[u"値"] != VALUE_NONE:', u'        if is_num(r) and not r[u"次元"]:', QG))
    a((u"Q1d 相手が在る組も選ぶ", u'            if k not in keys:\n                r[u"対象"] = other', u'            if True:\n                r[u"対象"] = other', QG))
    a((u"Q2a 値が 無い 行も選ぶ", u'        if not has_value(r):\n            continue\n        if not r[u"科目"].split(u":")[0].endswith(u"_cor") and users[r[u"科目"]] == 1:', u'        if False:\n            continue\n        if not r[u"科目"].split(u":")[0].endswith(u"_cor") and users[r[u"科目"]] == 1:', QG))
    a((u"Q2b 提出者別の科目の唯一の使い手も選ぶ(M52)", u'        if not r[u"科目"].split(u":")[0].endswith(u"_cor") and users[r[u"科目"]] == 1:\n            continue', u'        if False:\n            continue', QG))
    a((u"Q2b2 唯一の使い手の条件を 2 つ以上にする", u'endswith(u"_cor") and users[r[u"科目"]] == 1:', u'endswith(u"_cor") and users[r[u"科目"]] == 2:', QG))
    a((u"Q2b3 標準の科目の唯一の使い手も選ばない", u'if not r[u"科目"].split(u":")[0].endswith(u"_cor") and users[r[u"科目"]] == 1:', u'if users[r[u"科目"]] == 1:', QG))
    a((u"Q2c 入れ替え先に文の行も選ぶ", u'            if is_num(r2) and r2[u"科目"] != r[u"科目"] and (', u'            if r2[u"科目"] != r[u"科目"] and (', QG))
    a((u"Q2d 入れ替え先が同じ科目の行も選ぶ(同値の予測)", u'            if is_num(r2) and r2[u"科目"] != r[u"科目"] and (', u'            if is_num(r2) and (', QG))
    a((u"Q2e 入れ替え先の期の種類を見ない", u'and (u"時点" in r2[u"期間"]) == (u"時点" in r[u"期間"]) and r2[u"単位"] == r[u"単位"]:', u'and r2[u"単位"] == r[u"単位"]:', QG))
    a((u"Q2f 入れ替え先の単位を見ない", u'and r2[u"単位"] == r[u"単位"]:\n                k = ', u':\n                k = ', QG))
    a((u"Q2g 入れ替え先が同じ組になっても選ぶ", u'                if k not in keys:\n                    r[u"科目"] = r2[u"科目"]', u'                if True:\n                    r[u"科目"] = r2[u"科目"]', QG))
    a((u"Q3a 値が 無い 行も選ぶ", u'    f = first_row(o[u"行"], has_value)\n    if f is None:\n        return None\n    r = f[1]\n    r[u"値"] = add_step', u'    f = first_row(o[u"行"], is_num)\n    if f is None:\n        return None\n    r = f[1]\n    r[u"値"] = add_step', QG))
    a((u"Q4a 値が 無い 行も選ぶ", u'def chg_q4(o):\n    f = first_row(o[u"行"], lambda r: has_value(r) and r[u"値"] not in (u"0", u"-0"))', u'def chg_q4(o):\n    f = first_row(o[u"行"], lambda r: is_num(r) and r[u"値"] not in (u"0", u"-0"))', QG))
    a((u"Q4b 値が 0 の行も選ぶ", u'def chg_q4(o):\n    f = first_row(o[u"行"], lambda r: has_value(r) and r[u"値"] not in (u"0", u"-0"))', u'def chg_q4(o):\n    f = first_row(o[u"行"], lambda r: has_value(r))', QG))
    a((u"Q5a 値が 無い 行も選ぶ", u'        if not has_value(r):\n            continue\n        ds = ', u'        if False:\n            continue\n        ds = ', QG))
    a((u"Q5b 日が読めない行も選ぶ(同値の予測)", u'if any(d is None or d.year <= 1 or (d.month, d.day) == (2, 29) for d in ds):', u'if any(d.year <= 1 or (d.month, d.day) == (2, 29) for d in ds):', QG))
    a((u"Q5c 1 年の行も選ぶ", u'if any(d is None or d.year <= 1 or (d.month, d.day) == (2, 29) for d in ds):', u'if any(d is None or (d.month, d.day) == (2, 29) for d in ds):', QG))
    a((u"Q5d 2 月 29 日の行も選ぶ(M53)", u'if any(d is None or d.year <= 1 or (d.month, d.day) == (2, 29) for d in ds):', u'if any(d is None or d.year <= 1 for d in ds):', QG))
    a((u"Q5d2 2 月 29 日でなく 3 月 1 日を避ける", u'(d.month, d.day) == (2, 29) for d in ds', u'(d.month, d.day) == (3, 1) for d in ds', QG))
    a((u"Q5e 1 年前に同じ組が在っても選ぶ", u'        if k not in keys:\n            r[u"期間"] = new', u'        if True:\n            r[u"期間"] = new', QG))
    a((u"Q6a 文の行も選ぶ(同値の予測)", u'lambda r: is_num(r) and count[r[u"科目"]] == 1 and r[u"単位"] == u"通貨:JPY")', u'lambda r: count[r[u"科目"]] == 1 and r[u"単位"] == u"通貨:JPY")', QG))
    a((u"Q6b 同じ科目が 2 行以上の行も選ぶ", u'lambda r: is_num(r) and count[r[u"科目"]] == 1 and r[u"単位"] == u"通貨:JPY")', u'lambda r: is_num(r) and r[u"単位"] == u"通貨:JPY")', QG))
    a((u"Q6c 単位が円でない行も選ぶ", u'lambda r: is_num(r) and count[r[u"科目"]] == 1 and r[u"単位"] == u"通貨:JPY")', u'lambda r: is_num(r) and count[r[u"科目"]] == 1)', QG))
    return M


def func_text(name):
    u"""script の関数 ``name`` の字(``def`` の行から次の 2 行の空きまで)。"""
    i = SRC0.index(u"def %s(" % name)
    j = SRC0.index(u"\n\n\n", i)
    return SRC0[i:j]


def fix2_mutants():
    u"""直し 2 の変異(名前, 元の字, 新しい字, 検査の名前の並び)。変え方 Q1〜Q6 の「選ばない」守りを、条件ごと外す型(直し 1)に加えて、**半分だけ外す型**(``in`` の要素を 1 つ落とす・``any`` ↔ ``all``・``and`` ↔ ``or``・境の ``<=`` ↔ ``<``・比べの向き)と、**走査の向き**(最初に当てはまるものでなく最後を選ぶ)で全部掃く。
    **予測(実行より先に書いた)**: 全部 qguard が赤。黙ると予測したのは次の 3 本(同値): Q2 の ``users`` を数の行だけにする(R13 で文と数の同じ科目は断られるので同じ数)・Q2 の ``!=`` 科目を外す(直し 1 で同値と書いた)・Q5 の ``d is None``(受理された型の file の日は全部読める)。
    **結果(1 回目の実行)**: 49 本のうち 14 本が黙った。9 本は作り物の file の穴(走査の向き 5 本・Q2 の ``>= 1``・Q4 の符号を取らない・Q5 の月だけ・日だけ)で、作り物の file を足して赤にした(その後 5 本が黙る)。残る 5 本は同値(``SILENT_BY_DESIGN`` に理由)。予測の 3 本のうち 2 本(Q2 の ``!=`` 科目・Q5 の ``d is None``)は直し 1 の表に在る。"""
    M = []

    def f(name, fn, old, new, tags=(u"qguard",)):
        t = func_text(fn)
        assert t.count(old) >= 1, (name, old)
        M.append((name, t, t.replace(old, new), tags))
    # ---- 走査の向き(最初に当てはまる行 → 最後に当てはまる行)
    f(u"Q1r 走査を後ろから", u"chg_q1", u"    for r in rows:\n", u"    for r in reversed(rows):\n")
    f(u"Q2r 元の行の走査を後ろから", u"chg_q2", u"    for r in rows:\n        if not has_value(r):", u"    for r in reversed(rows):\n        if not has_value(r):")
    f(u"Q2r2 入れ替え先の走査を後ろから(N6)", u"chg_q2", u"        for r2 in rows:\n", u"        for r2 in reversed(rows):\n")
    f(u"Q3r 走査を後ろから", u"chg_q3", u'first_row(o[u"行"], has_value)', u'first_row(o[u"行"][::-1], has_value)')
    f(u"Q4r 走査を後ろから", u"chg_q4", u'first_row(o[u"行"], lambda', u'first_row(o[u"行"][::-1], lambda')
    f(u"Q5r 走査を後ろから", u"chg_q5", u"    for r in rows:\n", u"    for r in reversed(rows):\n")
    f(u"Q6r 走査を後ろから", u"chg_q6", u"first_row(rows, lambda", u"first_row(rows[::-1], lambda")
    # ---- Q1 の半分外し
    f(u"Q1h1 次元の条件と数の条件を or にする", u"chg_q1", u'is_num(r) and not r[u"次元"] and', u'is_num(r) and not r[u"次元"] or')
    f(u"Q1h2 数の条件と次元の条件を or にする", u"chg_q1", u'if is_num(r) and not r[u"次元"] and', u'if is_num(r) or not r[u"次元"] and')
    f(u"Q1h3 値が 無い を != から == にする", u"chg_q1", u'r[u"値"] != VALUE_NONE', u'r[u"値"] == VALUE_NONE')
    f(u"Q1h4 次元の条件を反転", u"chg_q1", u'not r[u"次元"]', u'r[u"次元"]')
    f(u"Q1h5 相手が在る組を選び、無い組を選ばない(in)", u"chg_q1", u"if k not in keys:", u"if k in keys:")
    f(u"Q1h6 相手の対象を取り違える(既定 → 既定)", u"chg_q1", u'other = TARGET_IND if r[u"対象"] == TARGET_DEF else TARGET_DEF', u'other = TARGET_DEF if r[u"対象"] == TARGET_DEF else TARGET_DEF')
    f(u"Q1h7 相手の鍵に次元を空でなく元の次元で作る(同値の予測は無い)", u"chg_q1", u"other, ())", u'other, tuple(tuple(x) for x in r[u"次元"]))')
    # ---- Q2 の半分外し
    f(u"Q2h1 提出者別の守りの and を or にする", u"chg_q2", u'endswith(u"_cor") and users', u'endswith(u"_cor") or users')
    f(u"Q2h2 提出者別の守りの endswith を startswith にする", u"chg_q2", u'endswith(u"_cor")', u'startswith(u"_cor")')
    f(u"Q2h3 唯一の使い手を <= 1 にする(同値の予測: 値の在る行の科目は 1 以上)", u"chg_q2", u'users[r[u"科目"]] == 1:', u'users[r[u"科目"]] <= 1:')
    f(u"Q2h4 唯一の使い手を >= 1 にする", u"chg_q2", u'users[r[u"科目"]] == 1:', u'users[r[u"科目"]] >= 1:')
    f(u"Q2h5 唯一の使い手を < 2 でなく < 1 にする", u"chg_q2", u'users[r[u"科目"]] == 1:', u'users[r[u"科目"]] < 1:')
    f(u"Q2h6 users を数の行だけで数える(R13 で同値の予測)", u"chg_q2", u'users = collections.Counter(r[u"科目"] for r in rows)', u'users = collections.Counter(r[u"科目"] for r in rows if is_num(r))')
    f(u"Q2h7 入れ替え先の 1 つ目と 2 つ目の and を or にする", u"chg_q2", u'r2[u"科目"] != r[u"科目"] and (', u'r2[u"科目"] != r[u"科目"] or (')
    f(u"Q2h8 入れ替え先の 期の種類と単位の and を or にする", u"chg_q2", u'(u"時点" in r[u"期間"]) and r2[u"単位"]', u'(u"時点" in r[u"期間"]) or r2[u"単位"]')
    f(u"Q2h9 入れ替え先の期の種類を != にする", u"chg_q2", u'(u"時点" in r2[u"期間"]) == (u"時点" in r[u"期間"])', u'(u"時点" in r2[u"期間"]) != (u"時点" in r[u"期間"])')
    f(u"Q2h10 入れ替え先の単位を != にする", u"chg_q2", u'r2[u"単位"] == r[u"単位"]', u'r2[u"単位"] != r[u"単位"]')
    f(u"Q2h11 入れ替え先の科目を == にする", u"chg_q2", u'r2[u"科目"] != r[u"科目"]', u'r2[u"科目"] == r[u"科目"]')
    f(u"Q2h13 k not in keys を in にする", u"chg_q2", u"if k not in keys:", u"if k in keys:")
    f(u"Q2h14 提出者別の判定を split の 2 つ目で見る(接頭辞を取り違える)", u"chg_q2", u'split(u":")[0]', u'split(u":")[-1]')
    # ---- Q3 の半分外し
    f(u"Q3h1 値の在る行を 値が 無い 行に反転", u"chg_q3", u'first_row(o[u"行"], has_value)', u'first_row(o[u"行"], lambda r: is_num(r) and not has_value(r))')
    # ---- Q4 の半分外し
    f(u"Q4h1 0 の除外から -0 を落とす(N7)", u"chg_q4", u'not in (u"0", u"-0")', u'not in (u"0",)')
    f(u"Q4h2 0 の除外から 0 を落とす(N7)", u"chg_q4", u'not in (u"0", u"-0")', u'not in (u"-0",)')
    f(u"Q4h3 0 の除外を in にする", u"chg_q4", u'not in (u"0", u"-0")', u'in (u"0", u"-0")')
    f(u"Q4h4 has_value と 0 の除外の and を or にする", u"chg_q4", u"has_value(r) and r", u"has_value(r) or r")
    f(u"Q4h5 符号を付ける向きを逆にする(負の値に - を足す)", u"chg_q4", u'r[u"値"][1:] if r[u"値"].startswith(u"-") else u"-" + r[u"値"]', u'u"-" + r[u"値"]')
    # ---- Q5 の半分外し
    f(u"Q5h1 any を all にする(N19)", u"chg_q5", u"if any(d is None", u"if all(d is None")
    f(u"Q5h2 年の条件を < 1 にする", u"chg_q5", u"d.year <= 1", u"d.year < 1")
    f(u"Q5h3 3 つの or のうち d is None と year の or を and にする", u"chg_q5", u"d is None or d.year <= 1 or", u"d is None and d.year <= 1 or")
    f(u"Q5h4 year と 2 月 29 日の or を and にする", u"chg_q5", u"d.year <= 1 or (d.month, d.day) == (2, 29)", u"d.year <= 1 and (d.month, d.day) == (2, 29)")
    f(u"Q5h5 2 月 29 日の比べを != にする", u"chg_q5", u"(d.month, d.day) == (2, 29)", u"(d.month, d.day) != (2, 29)")
    f(u"Q5h6 2 月 29 日の月だけを見る", u"chg_q5", u"(d.month, d.day) == (2, 29)", u"d.month == 2")
    f(u"Q5h7 2 月 29 日の日だけを見る", u"chg_q5", u"(d.month, d.day) == (2, 29)", u"d.day == 29")
    f(u"Q5h8 k not in keys を in にする", u"chg_q5", u"if k not in keys:", u"if k in keys:")
    f(u"Q5h9 1 年前でなく 1 年後へ(守りでなく変え方の向き)", u"chg_q5", u"year - 1)", u"year + 1)")
    # ---- Q6 の半分外し
    f(u"Q6h1 同じ科目が 1 行 を <= 1 にする(同値の予測)", u"chg_q6", u'count[r[u"科目"]] == 1', u'count[r[u"科目"]] <= 1')
    f(u"Q6h2 同じ科目が 1 行 を >= 1 にする", u"chg_q6", u'count[r[u"科目"]] == 1', u'count[r[u"科目"]] >= 1')
    f(u"Q6h3 同じ科目が 1 行 を == 2 にする", u"chg_q6", u'count[r[u"科目"]] == 1', u'count[r[u"科目"]] == 2')
    f(u"Q6h4 単位の比べを != にする", u"chg_q6", u'r[u"単位"] == u"通貨:JPY"', u'r[u"単位"] != u"通貨:JPY"')
    f(u"Q6h5 数の条件と count の and を or にする", u"chg_q6", u"is_num(r) and count", u"is_num(r) or count")
    f(u"Q6h6 count と単位の and を or にする", u"chg_q6", u"== 1 and r", u"== 1 or r")
    f(u"Q6h7 count を数の行だけでなくすべての行で数える(R13 で同値の予測)", u"chg_q6", u"for r in rows if is_num(r))", u"for r in rows)")
    return [m for m in M if m is not None]


def all_mutants():
    u"""(名前, 変異の字 または None, 検査の tag の並び)。字が None は、元の字が script に無い(= 変異の表が古い)。"""
    out = []
    for n, old, new, tags in hand_text_mutants() + hand_other_mutants() + fix1_mutants() + fix2_mutants():
        out.append((n, mutant_source(old, new), tags))
    for n, changes, tags in generated_mutants():
        out.append((n, with_lines(changes), tags))
    return out


def hand_other_mutants():
    u"""配線・作る側・数える側・入口の変異(名前, 元の字, 新しい字, 検査の tag の並び)。"""
    M = []
    a = lambda n, old, new, tags: M.append((n, old, new, tags))                                 # noqa: E731
    # ---- 配線: 受け口を呼ばずに作る・断った file から作る・壊した file でなく元の file を受け口に掛ける
    a(u"W1 型から作る命令が断りを見ない", u'        refusals = check_safe(data, names)\n        if refusals:', u'        refusals = check_safe(data, names)\n        if False:', (u"wiring",))
    a(u"W2 型から作る命令が受け口を呼ばない", u'        refusals = check_safe(data, names)\n', u'        refusals = []\n', (u"wiring",))
    a(u"W3 型から作る命令が断っても 0 で終わる", u'            return EXIT_DECLINE\n        files, tnames, tables = render_v1(folder)', u'            return 0\n        files, tnames, tables = render_v1(folder)', (u"wiring",))
    a(u"W4 型から作る命令が別の file(carry の index)を受け口に掛ける", u'with open(os.path.join(folder, "type", "type.json"), "rb") as fh:\n            data = fh.read()\n        refusals', u'with open(os.path.join(folder, "carry", "index.json"), "rb") as fh:\n            data = fh.read()\n        refusals', (u"wiring",))
    a(u"W5 受け口の process の終わりの値を見ない", u'    if rc != 0:\n        raise Refuse(u"受け口の検査が 0 でない終わりの値で終わった")', u'    if False:\n        raise Refuse(u"受け口の検査が 0 でない終わりの値で終わった")', (u"wiring",))
    a(u"W6 受け口の process が -I で動かない", u'cmd = [sys.executable, "-I", SCRIPT_PATH, "--accept-dir" if many else "--accept", path]', u'cmd = [sys.executable, SCRIPT_PATH, "--accept-dir" if many else "--accept", path]', (u"iso", u"wiring"))
    a(u"W7 型から作る process が -I で動かない", u'cmd = [sys.executable, "-I", SCRIPT_PATH, "--build", folder, out]', u'cmd = [sys.executable, SCRIPT_PATH, "--build", folder, out]', (u"iso", u"wiring"))
    a(u"W8 書類 1 本の流れで受け口を呼ばない", u'            res = exec_accept(type_path, cwd, cap, names_file)\n', u'            res = od([(u"受理", True), (u"断り", [])])\n', (u"doc", u"decline"))
    a(u"W9 受け口が断っても作る", u'        if res[u"断り"]:\n            rules', u'        if False:\n            rules', (u"decline", u"doc"))
    a(u"W10 壊した file でなく元の file を受け口に掛ける", u'            write_variant_file(os.path.join(folder, bid + ".json"), made[1])', u'            write_variant_file(os.path.join(folder, bid + ".json"), type_text)', (u"doc", u"decline"))
    a(u"W11 変えた file でなく元の file を受け口に掛ける", u'            write_variant_file(os.path.join(folder, qid + ".json"), text)', u'            write_variant_file(os.path.join(folder, qid + ".json"), type_text)', (u"doc", u"decline"))
    a(u"W12 壊し方の判定に断りの並びを渡さない", u'judge_break(made[0], res[bid + ".json"][u"断り"])', u'judge_break(made[0], [])', (u"doc", u"decline"))
    a(u"W13 変え方の判定に断りの並びを渡さない", u'chg[qid] = judge_change(res[qid + ".json"][u"断り"])', u'chg[qid] = judge_change([])', (u"doc", u"decline"))
    a(u"W14 持ち込みに答えの属性を丸ごと置く", u'                o["row"], o["carry"] = f["row"], M.carried_attrs(f)\n            else:\n                o["out"] = f["out"]\n            cf.append(o)', u'                o["row"], o["carry"] = f["row"], f["attrs"]\n            else:\n                o["out"] = f["out"]\n            cf.append(o)', (u"doc", u"derive"))
    a(u"W15 持ち込みの検査を掛けない", u'        if carry_forbidden_v1(root):', u'        if False:', (u"doc", u"derive"))
    a(u"W16 --build の使い方の引数の数を見ない", u'    if len(args) != 3 or args[0] != "--build":', u'    if len(args) < 1:', (u"wiring", u"main"))
    a(u"W17 作った原稿の folder の 2 回目を 1 回目と同じにする", u'        ok2, _r2, _s2 = exec_build(root, out2, cwd, proc, names_file)\n        tree_same = bool(ok2 and P.read_tree(out2) == P.read_tree(out1))', u'        ok2, _r2, _s2 = True, u"", 0\n        tree_same = True', (u"doc",))
    a(u"W18 2 回が同じ を見ない", u'rec[u"比べ方 2"][u"2 回が同じ"] = bool(tree_same and okb2 and P.read_tree(b2) == tree)', u'rec[u"比べ方 2"][u"2 回が同じ"] = True', (u"doc",))
    a(u"W19 fact が意味として同じ を 片側の空だけで見る", u'c2[u"fact が意味として同じ"] = bool(om and nm and om == nm)', u'c2[u"fact が意味として同じ"] = bool(om and nm)', (u"doc",))
    a(u"W20 道具が止まったのを断らない", u'        if new[u"類"] == V.CLS_STOPPED and orig[u"類"] != V.CLS_STOPPED:', u'        if False:', (u"doc", u"decline"))
    a(u"W21 出す folder の file の名を見ない", u'        if set(tree) != P.expected_names(M.jload(M.read_bytes(os.path.join(out1, P.INDEX_FILE)))):', u'        if False:', (u"doc", u"decline"))
    a(u"W22 時間の上限を見ない(受け口)", u'    if timed_out:\n        raise Refuse(u"受け口の検査が時間の上限を超えた")', u'    if False:\n        raise Refuse(u"受け口の検査が時間の上限を超えた")', (u"wiring", u"decline"))
    a(u"W23 時間の上限を見ない(型から作る)", u'    if timed_out:\n        return False, u"型から作る命令が時間の上限を超えた", secs', u'    if False:\n        return False, u"型から作る命令が時間の上限を超えた", secs', (u"wiring", u"decline"))
    a(u"W24 断りの理由を落とす(型から作る)", u'        reason = decline_reason(err)\n        return False, (reason if reason is not None else u"型から作る命令が 0 でない終わりの値で終わった"), secs', u'        return False, u"", secs', (u"wiring", u"decline"))
    # ---- 数える側
    a(u"C1 隠しの fact を数えない", u'        if f["where"] == "H":\n            rec[u"対象の fact"][u"隠し"] += 1', u'        if f["where"] == "X":\n            rec[u"対象の fact"][u"隠し"] += 1', (u"doc", u"derive"))
    a(u"C2 値が -0 の行を数え違える", u'rows[u"値が -0 の行"] += 1 if r["value"] == u"-0" else 0', u'rows[u"値が -0 の行"] += 1 if r["value"] == u"0" else 0', (u"doc", u"derive"))
    a(u"C3 期の表に無い期間の行を数え違える", u'M.period_name(r["pkind"], r["period"], v1["dec"]) is None else 0', u'M.period_name(r["pkind"], r["period"], v1["dec"]) is not None else 0', (u"doc", u"derive"))
    a(u"C4 脚注を数え違える", u'e["kind"] == "footnote"', u'e["kind"] == "fact"', (u"doc", u"derive"))
    a(u"C5 規則ごとの断った書類を立てない", u'        a[u"規則ごとの断った書類"][x[u"規則"]] = True\n', u'', (u"doc", u"decline", u"run", u"verify"))
    a(u"C6 規則と欄ごとの数の鍵が欄を持たない", u'        key = x[u"規則"] + u"/" + x[u"欄"]', u'        key = x[u"規則"]', (u"doc", u"decline"))
    a(u"C7 集計から 番号 を外さない", u'if k not in (u"番号", u"断った段", u"断った理由", u"秒")', u'if k not in (u"断った段", u"断った理由", u"秒")', (u"run", u"verify"))
    a(u"C8 型の外が 0 の書類を数字の側だけで見る", u'e[u"型の外の fact"][u"合計"][KIND_NUM] + e[u"型の外の fact"][u"合計"][KIND_TEXT] == 0', u'e[u"型の外の fact"][u"合計"][KIND_NUM] == 0', (u"run", u"verify"))
    a(u"C9 開発の 5 本と本番の境が 1 つずれる", u'dev, prod = per_doc[:dev_count], per_doc[dev_count:]', u'dev, prod = per_doc[:dev_count + 1], per_doc[dev_count + 1:]', (u"run", u"verify"))
    a(u"J1 XJ0-1 の分子が断った書類", u'(u"書類", acc[u"受理した"]), (u"分母", prod[u"書類"])', u'(u"書類", acc[u"断った"]), (u"分母", prod[u"書類"])', (u"run", u"verify"))
    a(u"J2 XJ0-5 の分子が組めた書類", u'(u"書類", z[u"比べ方 2"][u"fact が意味として同じ"])', u'(u"書類", z[u"比べ方 2"][u"組めた"])', (u"run", u"verify"))
    a(u"J3 XJ0-3 の分子が数の fact だけ", u'(u"fact", out_tot[KIND_NUM] + out_tot[KIND_TEXT])', u'(u"fact", out_tot[KIND_NUM])', (u"run", u"verify"))
    a(u"J4 XJ0-7 の分子が断った", u'(u"ちょうど 1 つ", s(u"ちょうど 1 つ"))', u'(u"ちょうど 1 つ", s(u"断った"))', (u"run", u"verify"))
    a(u"J5 XJ0-8 の分子が作れた", u'(u"通した", sum(v[u"通した"] for v in chg.values()))', u'(u"通した", sum(v[u"作れた"] for v in chg.values()))', (u"run", u"verify"))
    a(u"J6 XJ0-9 の分母が名の種類の 1 つだけ", u'sum(cor.values())', u'cor[u"提出者別"]', (u"run", u"verify"))
    a(u"J7 XJ0-10 の分子が他: の単位の行", u'(u"書類", prod[u"期の表に無い期間の行が在る書類"])', u'(u"書類", prod[u"他: の単位の行が在る書類"])', (u"run", u"verify"))
    # ---- 記録の検査
    a(u"K1 書類の本数を見ない", u'    if not isinstance(docs, list) or len(docs) != want or rec[u"材料"][u"書類の本数"] != want:', u'    if not isinstance(docs, list):', (u"verify",))
    a(u"K2 断った書類の形を見ない", u'        if d[u"断った"] != bool(d[u"断った段"]) or d[u"断った"] != bool(d[u"断った理由"]) or (d[u"断った"] and d[u"断った段"] not in STAGES):', u'        if False:', (u"verify",))
    a(u"K3 受理して断った書類を見ない", u'        if a[u"受理した"] and a[u"断った"]:', u'        if False:', (u"verify",))
    a(u"K4 受け口の数の合わなさを見ない", u'        if a[u"断った"] != (a[u"断りの数"] >= 1) or sum(a[u"規則ごとの断りの数"].values()) != a[u"断りの数"] or any((n >= 1) != a[u"規則ごとの断った書類"][r] for r, n in a[u"規則ごとの断りの数"].items()):', u'        if False:', (u"verify",))
    a(u"K5 規則と欄ごとの数の合わなさを見ない", u'        if sum(a[u"規則と欄ごとの断りの数"].values()) != a[u"断りの数"]:', u'        if False:', (u"verify",))
    a(u"K6 受け口を通っていない書類の後ろの段を見ない", u'        if d[u"断った"] and d[u"断った段"] != STAGES[0] and d[u"断った段"] != STAGES[1] and not a[u"受理した"]:', u'        if False:', (u"verify",))
    a(u"K7 断った書類の比べ方 2 を見ない", u'        if d[u"断った"] and (d[u"比べ方 2"][u"fact が意味として同じ"] or d[u"比べ方 2"][u"組めた"]):', u'        if False:', (u"verify",))
    a(u"K8 受理していない書類の壊し方を見ない", u'        if not a[u"受理した"] and any(v[u"作れた"] for v in d[u"壊し方"].values()):', u'        if False:', (u"verify",))
    a(u"K9 型に入った fact と外の合計を見ない", u'            if o[k] + t[k] != d[u"対象の fact"][k]:', u'            if False:', (u"verify",))
    a(u"K10 理由ごとの数が合計より多いのを見ない", u'            if max(d[u"型の外の fact"][u"理由ごと"][r][k] for r in REASONS) > o[k]:', u'            if False:', (u"verify",))
    a(u"K11 壊し方の ちょうど 1 つ を見ない", u' != v[u"作れた"] or v[u"ちょうど 1 つ"] > v[u"断った"]:', u' != v[u"作れた"]:', (u"verify",))
    a(u"K12 壊し方の合計を見ない", u'if v[u"断った"] + v[u"別の規則で断った"] + v[u"断らなかった"] != v[u"作れた"] or', u'if False or', (u"verify",))
    a(u"K13 変え方の 通した > 作れた を見ない", u'            if v[u"通した"] > v[u"作れた"] or (v[u"通した"]', u'            if False or (v[u"通した"]', (u"verify",))
    a(u"K14 変え方の通したのに断ったを見ない", u'(v[u"通した"] and any(v[u"断った"].values())) or', u'False or', (u"verify",))
    a(u"K15 変え方の 通さず断らずを見ない", u'(v[u"作れた"] and not v[u"通した"] and not any(v[u"断った"].values()))', u'False', (u"verify",))
    a(u"K16 記録の合計を導き直さない", u'    if M.dumps(tot) != M.dumps(rec[u"集計"]) or M.dumps(judged(tot))', u'    if False or M.dumps(judged(tot))', (u"verify",))
    a(u"K17 判定の数を導き直さない", u'M.dumps(judged(tot)) != M.dumps(rec[[k for k in rec if k.startswith(u"予測の判定に要る数")][0]]):', u'False:', (u"verify",))
    a(u"K18 禁止のものの検査を掛けない", u'    M.check_clean(rec, text if text is not None else M.dumps(rec))', u'    pass', (u"verify", u"run"))
    a(u"K19 --check が記録を検査しない", u'    verify_record(rec, text, want, dev_count)\n    say(u"--check', u'    say(u"--check', (u"verify", u"run"))
    a(u"K20 --check が無い記録で止まらない", u'    if not os.path.isfile(p):\n        raise Stop(u"**在る記録が無い。止める**")', u'    if False:\n        raise Stop(u"**在る記録が無い。止める**")', (u"verify", u"run"))
    a(u"K21 記録を書く前後の検査を掛けない", u'    prev().M.write_record(path, rec, secret)', u'    with io.open(path, "x", encoding="utf-8") as fh:\n        fh.write(prev().M.dumps(rec))', (u"run",))
    a(u"K22 本番が記録を書かない", u'    write_record(out, rec, secret)\n    say(u"-> ', u'    say(u"-> ', (u"run",))
    a(u"K23 開発の 5 本が道具を確かめない", u'    check_tool(tool_p, runner, None, want_version, want_sha)\n    names = load_names_file', u'    names = load_names_file', (u"devrun",))
    a(u"K24 開発の 5 本が記録を書く", u'    say(json.dumps(group_totals(per), ensure_ascii=False, indent=1))\n    return per', u'    say(json.dumps(group_totals(per), ensure_ascii=False, indent=1))\n    write_record(os.path.join(tempfile.gettempdir(), "xj0_dev_record_mutant.json"), assemble(per, "x", {}, 5))\n    return per', (u"devrun",))
    a(u"K25 本番が道具を確かめない", u'    info = check_tool(tool_p, runner, sha_reader, want_version, want_sha)\n', u'    info = od([(u"版", u""), (u"ModelValue.py の sha256", u""), (u"package の一覧の sha256", u""), (u"Python の版", u"")])\n', (u"run",))
    a(u"K26 記録の書類の並びの sha を取り違える", u'return assemble(per_doc, W.order_sha256([d[0] for d in docs]), info, dev_count), secret', u'return assemble(per_doc, W.order_sha256([d[0] for d in docs][::-1]), info, dev_count), secret', (u"run",))
    # ---- 起こす側(derive・render)
    a(u"D1 (g) の印を数え直さない(1 つの組の値が違うとき)", u'        if key[0] and len(set((x["value"], x["form1"], x["shift"], x["prec"]) for x in fs)) > 1:', u'        if key[0] and len(set((x["value"], x["form1"], x["shift"], x["prec"]) for x in fs)) > 2:', (u"derive",))
    a(u"D2 (a) を期が書けるときも残す", u'        if "a" in keep and period_writable(f["period"]):\n            keep.discard("a")', u'        if False:\n            keep.discard("a")', (u"derive",))
    a(u"D3 (a) を期が書けないときも外す", u'        if "a" in keep and period_writable(f["period"]):', u'        if "a" in keep:', (u"derive",))
    a(u"D4 (d) を単位が書けないときも外す", u'        if "d" in keep and f["form1"] is not None:', u'        if "d" in keep:', (u"derive",))
    a(u"D5 (d) を残す", u'        if "d" in keep and f["form1"] is not None:\n            keep.discard("d")', u'        if False:\n            keep.discard("d")', (u"derive",))
    a(u"D6 (g) を元の理由に残す", u'        keep.discard("g")\n', u'', (u"derive",))
    a(u"D7 期の始まりが終わりより後も書けるとする", u'    return all(x is not None for x in ds) and (len(ds) == 1 or ds[0] <= ds[1])', u'    return all(x is not None for x in ds)', (u"derive",))
    a(u"D8 期の始まり = 終わりを書けないとする", u'(len(ds) == 1 or ds[0] <= ds[1])', u'(len(ds) == 1 or ds[0] < ds[1])', (u"derive",))
    a(u"D9 無い の表示の位を書く", u'o[u"表示の位"] = None if r["value"] == VALUE_NONE else r["shift"]', u'o[u"表示の位"] = r["shift"]', (u"derive",))
    a(u"D10 無い の精度を書く", u'o[u"精度"] = None if r["value"] == VALUE_NONE else r["prec"]', u'o[u"精度"] = r["prec"]', (u"derive",))
    a(u"D11 独自の名に辞書の名も入れる", u'        if name_class(r["name"]) == u"提出者別":\n            custom.add((u"科目", r["name"]))', u'        if True:\n            custom.add((u"科目", r["name"]))', (u"derive",))
    a(u"D12 独自の名を降順に並べる", u'for k, n in sorted(custom)]', u'for k, n in sorted(custom, reverse=True)]', (u"derive",))  # 並べ替えを外すだけの変異は set の並び(起動ごとの hash の乱数)がたまたま昇順だと黙るので、乱数に依らない形にした
    a(u"D13 辞書の無い _cor を提出者別にする", u'    return u"辞書の無い _cor の接頭辞" if prefix.endswith("_cor") else u"提出者別"', u'    return u"提出者別"', (u"derive",))
    a(u"D14 他: の単位の分子を並べ替えない", u'        return UNIT_OTHER + u"*".join(sorted(ms)) if ok(ms) else None', u'        return UNIT_OTHER + u"*".join(ms) if ok(ms) else None', (u"derive", u"render"))
    a(u"D15 他: の単位の分母を並べ替えない", u'UNIT_PER + u"*".join(sorted(d["den"]))', u'UNIT_PER + u"*".join(d["den"])', (u"derive", u"render"))
    a(u"D16 型の書類の識別子を取り違える", u'od([(u"提出者の識別子", dec["ident"]), (u"識別子の scheme", dec["scheme"])', u'od([(u"提出者の識別子", dec["scheme"]), (u"識別子の scheme", dec["ident"])', (u"derive",))
    a(u"D17 提出日と期末を取り違える", u'(u"当期の終わり", dec["end"]), (u"提出日", dec["filing"])', u'(u"当期の終わり", dec["filing"]), (u"提出日", dec["end"])', (u"derive",))
    a(u"D18 期間の始まりと終わりを取り違える", u'od([(u"始まり", r["period"][0]), (u"終わり", r["period"][1])])', u'od([(u"始まり", r["period"][1]), (u"終わり", r["period"][0])])', (u"derive",))
    a(u"D19 行を作るのに型の行の数をまとめ数えない(count)", u'        rows[row_of[k]]["count"] += 1\n', u'', (u"derive", u"doc"))
    a(u"D20 型の行の鍵に対象を入れない", u'f["key"] = (f["isnum"], f["attrs"]["name"], tuple(f["period"][1]), f["period"][0], f["target"], tuple(f["dims"]))', u'f["key"] = (f["isnum"], f["attrs"]["name"], tuple(f["period"][1]), f["period"][0], tuple(f["dims"]))', (u"derive",))
    a(u"D21 型の行の鍵に期の種類を入れない", u'tuple(f["period"][1]), f["period"][0], f["target"]', u'tuple(f["period"][1]), f["target"]', (u"derive",))
    a(u"D22 型の行の鍵に次元を入れない", u', f["target"], tuple(f["dims"]))', u', f["target"])', (u"derive",))
    a(u"R-1 作る側の単位 id を 0 から振る", u'for n, u in enumerate(others, 1))', u'for n, u in enumerate(others, 0))', (u"render",))
    a(u"R-2 作る側の単位 id の桁数が違う", u'"U%04d" % n', u'"U%03d" % n', (u"render",))
    a(u"R-3 作る側の単位 id を字の順でなく出た順に振る", u'others = sorted(set(r[u"単位"] for r in rows', u'others = list(od.fromkeys(r[u"単位"] for r in rows', (u"render",))
    a(u"R-4 期の名の At の字が違う", u'return u"At" + dg[0] if kind == "instant"', u'return u"At-" + dg[0] if kind == "instant"', (u"render",))
    a(u"R-5 期の名の To の字が違う", u'u"From" + dg[0] + u"To" + dg[1]', u'u"From" + dg[0] + u"to" + dg[1]', (u"render",))
    a(u"R-6 期の名で第 0 版の規則を使わない", u'    n = prev().M.period_name(kind, dates, dec)\n    if n:\n        return n\n', u'', (u"render",))
    a(u"R-7 decimals と scale を取り違える", u'a["decimals"], a["scale"], a["format"] = str(r[u"精度"]), str(r[u"表示の位"]), FORMAT_OK', u'a["decimals"], a["scale"], a["format"] = str(r[u"表示の位"]), str(r[u"精度"]), FORMAT_OK', (u"render",))
    a(u"R-8 負の値に sign を付けない", u'            if r[u"値"].startswith(u"-"):\n                a["sign"] = "-"', u'            if False:\n                a["sign"] = "-"', (u"render",))
    a(u"R-9 無い の fact に nil を付けない", u'            a["xsi:nil"] = "true"', u'            pass', (u"render",))
    a(u"R-10 持ち込みを足さない", u'    a.update(carry)\n    return dict(sorted(a.items()))', u'    return dict(sorted(a.items()))', (u"render",))
    a(u"R-11 持ち込みに型の属性が在っても通す", u'    if any(k in typed for k in carry):\n        raise Refuse(u"持ち込みに型の属性が在る")', u'    if False:\n        raise Refuse(u"持ち込みに型の属性が在る")', (u"render",))
    a(u"R-12 個別の対象に連結の軸を足さない", u'    return m + ([(AXIS_CONS, MEMBER_IND)] if r[u"対象"] == TARGET_IND else [])', u'    return m', (u"render",))
    a(u"R-13 既定の対象に連結の軸を足す", u'if r[u"対象"] == TARGET_IND else [])', u'if True else [])', (u"render",))
    a(u"R-14 文脈の id の重なりを見ない", u'        if cid in defs and defs[cid][0] != group:', u'        if False:', (u"render",))
    a(u"R-15 作った定義を置く頭の部が無くても進む", u'        if (ctxs or units) and not host:', u'        if False:', (u"render",))
    a(u"R-16 型の外の文脈を足さない", u'        ctxs = M.merge_outside(ctxs, outside["contexts"])', u'        pass', (u"render",))
    a(u"R-17 型の外の単位を足さない", u'        units = M.merge_outside(units, outside["units"])', u'        pass', (u"render",))
    a(u"R-18 型の外の fact の属性を読まない(row でも out でもない)", u'                elif "out" in e:\n                    a = dict(sorted(outside["facts"][e["out"]]["attrs"].items()))', u'                elif "out" in e:\n                    a = {}', (u"render",))
    a(u"R-19 隠しの fact の属性を型から作らない", u'                    if "row" in h:\n                        a = v1_attrs(rows[h["row"]], info[h["row"]][0], info[h["row"]][1], h["carry"])', u'                    if False:\n                        a = v1_attrs(rows[h["row"]], info[h["row"]][0], info[h["row"]][1], h["carry"])', (u"render",))
    a(u"R-20 例外を断りにしない", u'    except Exception:                                      # noqa: BLE001  知らない形は断る\n        raise Refuse(u"作る途中の例外")', u'    except ZeroDivisionError:                                      # noqa: BLE001  知らない形は断る\n        raise Refuse(u"作る途中の例外")', (u"render", u"wiring", u"decline"))
    # ---- 指示書・入口
    a(u"I1 指示書の書き出しが別の字", u'        fh.write(instruction_text())', u'        fh.write(instruction_text() + u"\\n")', (u"write",))
    a(u"I2 指示書の書き出しが改行を変える", u'with io.open(path, "w", encoding="utf-8", newline="") as fh:\n        fh.write(instruction_text())', u'with io.open(path, "w", encoding="utf-8") as fh:\n        fh.write(instruction_text().replace(u"\\n", u"\\r\\n"))', (u"write",))
    a(u"I3 指示書の例の断り例が受理例と同じ", u'    bad = dump_text(example_bad())', u'    bad = dump_text(example_ok())', (u"instr",))
    a(u"I4 指示書の例の辞書が空", u'EXAMPLE_NAMES = frozenset(["jppfs_cor_ExampleAssets"', u'EXAMPLE_NAMES = frozenset(["jppfs_cor_ExampleAssetz"', (u"instr",))
    a(u"I5 入口が --accept を渡さない", u'    if argv and argv[0] in ("--accept", "--accept-dir"):\n        sys.exit(accept_main(argv))', u'    if False:\n        sys.exit(accept_main(argv))', (u"main",))
    a(u"I6 入口が --build を渡さない", u'    if argv and argv[0] == "--build":\n        sys.exit(build_main(argv))', u'    if False:\n        sys.exit(build_main(argv))', (u"main",))
    a(u"I7 --write-instruction が書かない", u'        print(write_instruction(a.write_instruction or None))\n        return', u'        return', (u"main", u"write"))
    a(u"I8 --check が検査しない", u'    if a.check:\n        check(root=a.root)\n        return', u'    if a.check:\n        return', (u"main",))
    a(u"I9 --make が folder の空を見ない", u'    if os.path.isdir(folder) and os.listdir(folder):\n        raise prev().W.Stop(u"**folder が空でない。止める**")', u'    if False:\n        raise prev().W.Stop(u"**folder が空でない。止める**")', (u"main",))
    a(u"I10 --run が --tool-p を要らない", u'    if not a.tool_p:\n        raise Stop(u"**--tool-p が要る。止める**")', u'    if False:\n        raise Stop(u"**--tool-p が要る。止める**")', (u"main",))
    a(u"I11 --keep の場所が空でなくても進む", u'        if os.listdir(a.keep):\n            raise Stop(u"**--keep の場所が空でない。止める**")', u'        if False:\n            raise Stop(u"**--keep の場所が空でない。止める**")', (u"main",))
    a(u"I12 --dev が --run と同じに記録を書く", u'        dev_run(a.tool_p, docs_dir=a.docs, keep=a.keep, names_file=a.names_file)\n        return', u'        pass', (u"main",))
    a(u"I13 --break が受け口に掛けない", u'        brk, chg = run_variants(text, names, work, work, None, names_file)', u'        brk, chg = od(), od()', (u"main", u"doc"))
    # ---- 壊し方・変え方の判定
    a(u"B1 壊し方の判定が行を見ない", u'x[u"規則"] == rule and x[u"行"] == row and x[u"欄"] == field', u'x[u"規則"] == rule and x[u"欄"] == field', (u"judge",))
    a(u"B2 壊し方の判定が欄を見ない", u'x[u"規則"] == rule and x[u"行"] == row and x[u"欄"] == field', u'x[u"規則"] == rule and x[u"行"] == row', (u"judge",))
    a(u"B3 壊し方の判定が規則だけ", u'x[u"規則"] == rule and x[u"行"] == row and x[u"欄"] == field', u'x[u"規則"] == rule', (u"judge",))
    a(u"B4 壊し方の判定が断りが在れば当たり", u'x[u"規則"] == rule and x[u"行"] == row and x[u"欄"] == field', u'True', (u"judge",))
    a(u"B5 ちょうど 1 つを 1 つ以上にする", u'res[u"ちょうど 1 つ"] = 1 if hit and len(refusals) == 1 else 0', u'res[u"ちょうど 1 つ"] = 1 if hit and len(refusals) >= 1 else 0', (u"judge",))
    a(u"B6 ちょうど 1 つを 2 つまでにする", u'res[u"ちょうど 1 つ"] = 1 if hit and len(refusals) == 1 else 0', u'res[u"ちょうど 1 つ"] = 1 if hit and len(refusals) <= 2 else 0', (u"judge",))
    a(u"B7 ちょうど 1 つが当たりを見ない", u'res[u"ちょうど 1 つ"] = 1 if hit and len(refusals) == 1 else 0', u'res[u"ちょうど 1 つ"] = 1 if len(refusals) == 1 else 0', (u"judge",))
    a(u"B8 別の規則で断ったに当たりも数える", u'res[u"別の規則で断った"] = 1 if (not hit and refusals) else 0', u'res[u"別の規則で断った"] = 1 if refusals else 0', (u"judge",))
    a(u"B9 断らなかったを取り違える", u'res[u"断らなかった"] = 0 if refusals else 1', u'res[u"断らなかった"] = 1 if refusals else 0', (u"judge",))
    a(u"B10 変え方の通したを断りが在れば 1", u'od([(u"作れた", 1), (u"通した", 0 if refusals else 1), (u"断った", rules)])', u'od([(u"作れた", 1), (u"通した", 1 if refusals else 0), (u"断った", rules)])', (u"judge",))
    a(u"B11 変え方の断った規則を数えない", u'    for x in refusals:\n        rules[x[u"規則"]] = 1\n    return od([(u"作れた", 1)', u'    return od([(u"作れた", 1)', (u"judge",))
    a(u"B12 変え方の断った規則を断りの数で数える", u'        rules[x[u"規則"]] = 1\n    return od([(u"作れた", 1)', u'        rules[x[u"規則"]] += 1\n    return od([(u"作れた", 1)', (u"judge",))
    return M


# ======================================================================== 11c. 予測の外れ(予測した検査では赤くならず、別の検査で赤くなった変異)と、同値の変異
#: 予測の外れ: 名前 → 実際に赤くした検査の tag。予測は ``all_mutants`` の表(変異の 4 つ目の欄)に残し、結果の欄にこの表を足して見る。
CAUGHT_BY = {
    "W5 受け口の process の終わりの値を見ない": ('judge', 'decline'),
    "W6 受け口の process が -I で動かない": ('judge', 'doc', 'decline', 'run', 'verify', 'devrun', 'variant', 'valone', 'units'),
    "W7 型から作る process が -I で動かない": ('doc', 'decline', 'run', 'verify', 'devrun', 'variant', 'valone', 'units'),
    "W11 変えた file でなく元の file を受け口に掛ける": ('judge', 'variant'),
    "W13 変え方の判定に断りの並びを渡さない": ('variant',),
    "W15 持ち込みの検査を掛けない": ('decline', 'units'),
    "W18 2 回が同じ を見ない": ('decline',),
    "W19 fact が意味として同じ を 片側の空だけで見る": ('units',),
    "C7 集計から 番号 を外さない": ('count',),
    "C8 型の外が 0 の書類を数字の側だけで見る": ('count',),
    "J2 XJ0-5 の分子が組めた書類": ('count',),
    "J5 XJ0-8 の分子が作れた": ('count',),
    "J7 XJ0-10 の分子が他: の単位の行": ('count',),
    "K1 書類の本数を見ない": ('valone',),
    "K2 断った書類の形を見ない": ('valone',),
    "K3 受理して断った書類を見ない": ('valone',),
    "K4 受け口の数の合わなさを見ない": ('valone',),
    "K5 規則と欄ごとの数の合わなさを見ない": ('valone',),
    "K6 受け口を通っていない書類の後ろの段を見ない": ('valone',),
    "K7 断った書類の比べ方 2 を見ない": ('valone',),
    "K8 受理していない書類の壊し方を見ない": ('valone',),
    "K9 型に入った fact と外の合計を見ない": ('valone',),
    "K10 理由ごとの数が合計より多いのを見ない": ('valone',),
    "K11 壊し方の ちょうど 1 つ を見ない": ('valone',),
    "K12 壊し方の合計を見ない": ('valone',),
    "K13 変え方の 通した > 作れた を見ない": ('valone',),
    "K14 変え方の通したのに断ったを見ない": ('valone',),
    "K15 変え方の 通さず断らずを見ない": ('valone',),
    "K19 --check が記録を検査しない": ('valone',),
    "K21 記録を書く前後の検査を掛けない": ('verify',),
    "K22 本番が記録を書かない": ('verify',),
    "K23 開発の 5 本が道具を確かめない": ('valone',),
    "D6 (g) を元の理由に残す": ('units',),
    "D7 期の始まりが終わりより後も書けるとする": ('units',),
    "D8 期の始まり = 終わりを書けないとする": ('units',),
    "D9 無い の表示の位を書く": ('units',),
    "D10 無い の精度を書く": ('units',),
    "D12 独自の名を降順に並べる": ('units',),
    "D14 他: の単位の分子を並べ替えない": ('units',),
    "D15 他: の単位の分母を並べ替えない": ('units',),
    "R-3 作る側の単位 id を字の順でなく出た順に振る": ('units',),
    "R-10 持ち込みを足さない": ('doc', 'units'),
    "R-11 持ち込みに型の属性が在っても通す": ('units',),
    "R-14 文脈の id の重なりを見ない": ('units',),
    "R-15 作った定義を置く頭の部が無くても進む": ('units',),
    "R-17 型の外の単位を足さない": ('units',),
    "R-18 型の外の fact の属性を読まない(row でも out でもない)": ('doc', 'decline', 'run', 'verify', 'devrun', 'variant', 'valone', 'units'),
    "R-20 例外を断りにしない": ('units',),
    "I9 --make が folder の空を見ない": ('units',),
    "I13 --break が受け口に掛けない": ('units',),
}

#: 同値の変異(どの検査でも元と同じ。理由は字で)。門は「作り物の全部の検査で元と同じ」を見る。
SILENT_BY_DESIGN = [
    (u"Q1h7 相手の鍵に次元を空でなく元の次元で作る(同値の予測は無い)", u"選ばれる行は ``not r 次元``(次元が空)の行だけなので、元の次元で作っても ``()`` と同じ(冗長)"),
    (u"Q2h3 唯一の使い手を <= 1 にする(同値の予測: 値の在る行の科目は 1 以上)", u"``users`` は行そのものを数えるので、いま見ている行の科目の ``users`` は 1 以上。``<= 1`` と ``== 1`` は同じ"),
    (u"Q2h6 users を数の行だけで数える(R13 で同値の予測)", u"守りに来るのは値の在る行(数の行)だけで、R13 により 1 つの科目が数の行と文の行の両方に在る file は受け口が断る。受理された file では、全部の行で数えても数の行だけで数えても、数の行の科目の使い手の数は同じ"),
    (u"Q6h1 同じ科目が 1 行 を <= 1 にする(同値の予測)", u"``is_num(r)`` の行の科目は ``count`` に 1 以上入っているので、``<= 1`` と ``== 1`` は同じ"),
    (u"Q6h7 count を数の行だけでなくすべての行で数える(R13 で同値の予測)", u"R13 により 1 つの科目が数の行と文の行の両方に在る file は受理されない。選ぶ行は ``is_num`` の行なので、その科目を使う文の行は無く、数える行を広げても数は同じ"),
    (u"Q2d 入れ替え先が同じ科目の行も選ぶ(同値の予測)", u"入れ替え先が同じ科目の行なら、新しい組 ``k`` は元の行自身の組と同じで必ず ``keys`` に在るので、``r2 科目 != r 科目`` を外しても ``k not in keys`` が同じ行を落とす(冗長)"),
    (u"Q5b 日が読めない行も選ぶ(同値の予測)", u"変え方は受理された型の file にだけ掛ける。受理された file の日は R2 で全部読める形なので ``parse_date`` は ``None`` を返さず、``d is None`` は常に偽(冗長)"),
    (u"Q6a 文の行も選ぶ(同値の予測)", u"``count`` は数の行だけを数える ``Counter`` なので、文の行の科目の ``count`` は 0 で(R13 で数の行と同じ科目は受理されない)``== 1`` が偽。``is_num(r)`` は ``count`` の判定に含まれて冗長"),
    (u"N3 独自の名の要素にも掛ける", u"独自の名の要素の (種類, 名) は、形が読める要素なら ``custom`` の集まりに必ず入っているので、``not own`` を外しても N3 は出ない(``own`` は N3 に対して冗長)"),
    (u"N4 並びを <= で見る", u"同じ (種類, 名) が 2 回在れば、先に ``in seen`` の枝(重なり)が当たり、並びの枝(``elif``)には来ない。``<=`` と ``<`` の差は同じ組のときだけで、その組は上の枝が取る"),
    (u"R9 の k = 0 を断る", u"``k <= 0`` と ``k < 0`` の差は k = 0 のときだけで、そのとき ``末尾の 0 の数 >= 0`` は常に真なので、どちらでも「倍数である」を返す"),
    (u"R10 を最後の行だけ断る", u"重なった行で ``seen`` の番号を上書きしても、``seen`` は「在るか」の判定にしか使わず、番号は断りの行に使わないので出力は同じ"),
    (u"K26 記録の書類の並びの sha を取り違える", u"``order_sha256`` は並べ替えてから取る(便 XG0 の関数)ので、並びを逆にしても sha256 は同じ"),
    (u"D21 型の行の鍵に期の種類を入れない", u"期の日の並び(1 つか 2 つ)の長さが時点(1)と期間(2)で違うので、鍵に日の並びが在れば期の種類は日の並びから決まる(期の種類は冗長)"),
]


# 予測した検査と、実際に赤くした検査が違った変異(予測の外れ。名前 → 実際に赤くした検査の tag)は ``CAUGHT_BY`` に持つ(予測は ``all_mutants`` の表に残す)。
# 同値の変異(どの検査も赤くならない。理由を書く)は ``SILENT_BY_DESIGN``。


def tags_for(name, tags):
    return tuple(tags) + tuple(CAUGHT_BY.get(name, ()))


def run_mutants(items=None):
    u"""(名前, 予測の tag, 赤くなった tag の並び, 読み込みの失敗) の並び。"""
    out = []
    for n, src, tags in (items if items is not None else all_mutants()):
        if src is None:
            out.append((n, tags, [], u"元の字が script に無い"))
            continue
        red, err = run_one(src, tags_for(n, tags))
        out.append((n, tags, red, err))
    return out


def silent_names():
    return [n for n, _why in SILENT_BY_DESIGN]


def mutant_table_problems():
    u"""表そのものの検査: 名前が 1 つずつ・元の字が在る・元と違う・予測の tag が在る・断りの呼び出しと「断る時」の 1 つずつに G1・G2 が在る・壊し方 44・変え方 6 を 1 つずつ掃く。"""
    out = []
    ms = all_mutants()
    names = [m[0] for m in ms]
    if len(names) != len(set(names)):
        out.append(u"変異の名前が重なる: %s" % [n for n, c in collections.Counter(names).items() if c > 1][:5])
    for n, src, tags in ms:
        if src is None:
            out.append(u"変異の元の字が script に無い: %s" % n)
        elif src == SRC0:
            out.append(u"変異が元と同じ字: %s" % n)
        for t in tuple(tags) + tuple(CAUGHT_BY.get(n, ())):
            if t not in CHECKS:
                out.append(u"変異の検査の名前が無い: %s %s" % (n, t))
    for n in CAUGHT_BY:
        if n not in names:
            out.append(u"CAUGHT_BY の名前が表に無い: %s" % n)
    for n in silent_names():
        if n not in names:
            out.append(u"SILENT_BY_DESIGN の名前が表に無い: %s" % n)
    # 断りの呼び出し 1 つずつ・「断る時」1 つずつ
    calls = []
    for i, ln in enumerate(LINES0):
        fn = func_of_line(i)
        if fn is not None and not fn.startswith(("brk_", "chg_")) and (ln.strip().startswith(u"out.append(refusal(") or ln.strip().startswith(u"return [refusal(")) and REFUSAL_CALL.search(ln):
            calls.append((REFUSAL_CALL.search(ln).group(1), REFUSAL_CALL.search(ln).group(2), i + 1))
    g1 = [n for n in names if n.startswith(u"G1 ")]
    if len(g1) != len(calls) or len(calls) < 40:
        out.append(u"断りの呼び出しの数と G1 の変異の数が合わない: %d %d" % (len(calls), len(g1)))
    seen = set()
    for rid, idx, _ln in calls:
        if idx.isdigit():
            seen.add((rid, int(idx)))
    has_var = set(r for r, idx, _l in calls if idx == u"c")
    for rid, _place, conds in MS.RULES:
        for k in range(len(conds)):
            if (rid, k) not in seen and rid not in has_var:
                out.append(u"「断る時」の呼び出しが見つからない: %s-%d" % (rid, k))
    for rid in RULE_IDS:
        if not any(r == rid for r, _i, _l in calls):
            out.append(u"規則の断りの呼び出しが無い: %s" % rid)
    for kind, deco in ((u"壊し方", "break_of"), (u"変え方", "change_of")):
        for bid, fn in re.findall(r'@%s\("(\w+)"\)\ndef (\w+)' % deco, SRC0):
            if not any((u" %s:" % fn) in n for n in names if n[:2] in (u"G6", u"G7")):
                out.append(u"%s %s(関数 %s)を掃く変異が無い" % (kind, bid, fn))
    ids_in_script = set(re.findall(r'@break_of\("(\w+)"\)', SRC0)) | set(re.findall(r'@change_of\("(\w+)"\)', SRC0))
    if ids_in_script != set(MS.BREAK_IDS) | set(MS.CHANGE_IDS):
        out.append(u"壊し方・変え方の関数の番号が表と合わない")
    return out


# ======================================================================== 11b. 封の字を 1 字変えると比べが赤になること・手の値が近くの数と重ならないこと
SEAL_CHANGES = (
    (u"精度 + 表示の位 が 0 より小さい", u"精度 + 表示の位 が 1 より小さい"), (u"値が 10 の(−精度)乗の倍数でない", u"値が 10 の(精度)乗の倍数でない"),
    (u"大きさが 1000 を超える", u"大きさが 1001 を超える"), (u"同じ数なら字の昇順で先の単位を残す", u"同じ数なら字の昇順で後の単位を残す"),
    (u"同じ数なら期間の側", u"同じ数なら時点の側"), (u"同じ数なら文の側", u"同じ数なら数の側"),
    (u"起こした file を受け口の検査が受理する書類は 52 本以上。", u"起こした file を受け口の検査が受理する書類は 53 本以上。"),
    (u"型の外の fact は、対象の fact の 0.2% 以下。", u"型の外の fact は、対象の fact の 0.3% 以下。"),
    (u"辞書の無い `_cor` の接頭辞の科目の名は、科目の名の 4% 以上 8% 未満。", u"辞書の無い `_cor` の接頭辞の科目の名は、科目の名の 5% 以上 8% 未満。"),
    (u"壊した file のうち「ちょうど 1 つ」は、作れた file の 85% 以上。", u"壊した file のうち「ちょうど 1 つ」は、作れた file の 86% 以上。"),
    (u"`U0001` から", u"`U0000` から"), (u"**対応表は無い**", u"**対応表が在る**"), (u"字 `1`", u"字 `2`"),
    (LAB_SHAS[0][:12], LAB_SHAS[0][:11] + u"0" if LAB_SHAS[0][11] != u"0" else LAB_SHAS[0][:11] + u"1"),
    (LAB_NAMES[1], LAB_NAMES[1].replace(u"2025", u"2024")))


def nearby_problems(ms=None):
    ms = ms or MS
    out = []
    w = doc_expect()
    for k in (u"数", u"文"):
        a, b, c = w[u"対象の fact"][k], w[u"型に入った fact"][k], w[u"型の外の fact"][u"合計"][k]
        if a != b + c or len(set((a, b, c))) != 3:
            out.append(u"手の値(対象・型に入った・型の外)が足し算になっていないか近くの数と重なる: %s %s %s %s" % (k, a, b, c))
    if len(set([w[u"対象の fact"][u"数"], w[u"型の行"][u"数"], w[u"型に入った fact"][u"数"], w[u"型の外の fact"][u"合計"][u"数"]])) != 4:
        out.append(u"手の値の数が重なる")
    return out


# ======================================================================== 12. 試験の本体
class SealTextTest(unittest.TestCase):
    def test_a_1_the_script_constants_equal_the_seal(self):
        self.assertEqual([], seal_problems())

    def test_a_2_the_seal_file_is_the_sealed_commit_and_unchanged(self):
        self.assertEqual([], seal_history_problems())

    def test_a_3_a_changed_seal_character_turns_the_comparison_red(self):
        seal = seal_text()
        for old, new in SEAL_CHANGES:
            self.assertGreaterEqual(seal.count(old), 1, old)
            self.assertNotEqual([], seal_problems(seal=seal.replace(old, new)), old)

    def test_a_4_engine_is_zero_lines_from_the_seal_commit(self):
        self.assertEqual([], engine_zero_problems())

    def test_a_5_the_boundary_import_list_is_not_widened(self):
        with io.open(os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py"), encoding="utf-8") as fh:
            body = fh.read()
        self.assertNotIn(u"input_type_v1", body)
        self.assertNotIn(u"xj0", body)


class OrderTest(unittest.TestCase):
    def test_d_1_the_real_history_has_the_seal_before_the_script_the_gate_and_the_instruction(self):
        u"""script・門・指示書のどれかが未 commit なら赤(足した commit が無い。skip にしない)。全部 commit された後で初めて緑。記録は別(記録が在る時だけ、記録の commit が script・門・指示書の後)。"""
        self.assertEqual([], order_of())

    def test_d_2_the_order_check_lists_the_script_the_gate_and_the_instruction_and_not_the_record(self):
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, rel)) for rel in ORDER_FILES))
        self.assertEqual((SCRIPT_REL, GATE_REL, INSTRUCTION_REL), tuple(ORDER_FILES))
        self.assertNotIn(RECORD_REL, ORDER_FILES)


class PartsTest(unittest.TestCase):
    def test_b_1_every_rule_and_every_refusal_condition_by_hand(self):
        self.assertEqual([], rules_problems())

    def test_b_2_the_44_breaks_and_6_changes_by_hand(self):
        self.assertEqual([], breaks_problems())

    def test_b_3_the_judging_of_breaks_and_changes_by_hand(self):
        self.assertEqual([], judge_problems())

    def test_b_4_degenerate_inputs_never_raise(self):
        self.assertEqual([], degenerate_problems())

    def test_b_5_the_dictionary_is_read_with_its_sha256(self):
        self.assertEqual([], dict_problems())

    def test_b_6_the_accept_command_line_in_a_separate_process(self):
        self.assertEqual([], accept_cli_problems())

    def test_b_7_deriving_the_type_from_a_made_up_document(self):
        self.assertEqual([], derive_problems())

    def test_b_8_one_document_end_to_end_by_hand(self):
        self.assertEqual([], doc_problems())

    def test_b_9_every_decline_and_the_variant_wiring(self):
        self.assertEqual([], decline_problems())
        self.assertEqual([], variant_problems())

    def test_b_10_building_from_the_type_attribute_by_attribute(self):
        self.assertEqual([], render_problems())
        self.assertEqual([], units_problems())

    def test_b_11_totals_and_judged_numbers_by_hand(self):
        self.assertEqual([], count_problems())

    def test_b_12_the_hand_scene_is_not_nearby_numbers(self):
        self.assertEqual([], nearby_problems())


class RecordTest(unittest.TestCase):
    def test_c_1_record_build_run_and_check_without_the_real_cache(self):
        self.assertEqual([], run_problems())

    def test_c_2_every_broken_record_relation_stops(self):
        self.assertEqual([], verify_problems())
        self.assertEqual([], verify_alone_problems())

    def test_c_3_dev_run_runs_the_five_only_and_writes_no_record(self):
        self.assertEqual([], dev_run_problems())

    def test_c_4_the_instruction_equals_the_written_output_and_its_examples_hold(self):
        self.assertEqual([], instruction_problems())
        self.assertEqual([], write_instruction_problems())

    def test_c_5_the_entry_points_dispatch(self):
        self.assertEqual([], main_dispatch_problems())

    def test_c_6_the_real_record_when_present_is_clean(self):
        u"""記録は本番の走りの後に書かれる。在れば中身を見て、無ければ見ない(skip にしない)。"""
        p = os.path.join(ROOT, RECORD_REL)
        if os.path.exists(p):
            rec = json.loads(read(RECORD_REL), object_pairs_hook=od)
            MS.check(root=ROOT, say=lambda *a: None)
            self.assertEqual(MS.SEAL_COMMIT, rec[u"封の commit"])
            self.assertEqual(67, rec[u"材料"][u"書類の本数"])
            self.assertEqual(sha_of(SCRIPT_REL), rec[u"この script の sha256"])
        else:
            self.assertFalse(os.path.exists(p))


class IsolationTest(unittest.TestCase):
    def test_g_1_the_accept_check_reads_only_the_type_file_and_the_dictionary(self):
        self.assertEqual([], iso_ast_problems())

    def test_g_2_the_accept_check_runs_where_the_answer_the_zip_and_the_previous_scripts_do_not_exist(self):
        self.assertEqual([], iso_problems())

    def test_g_3_the_build_command_runs_where_the_original_package_does_not_exist(self):
        self.assertEqual([], build_wiring_problems())


class WiringTest(unittest.TestCase):
    def test_e_1_the_imports_are_the_previous_scripts_and_nothing_wider(self):
        self.assertEqual([], import_problems())

    def test_e_3_the_gate_does_not_use_the_reserved_names(self):
        self.assertEqual([], reserved_problems())
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("ENGINE_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rel="g.py", base_=d))

    def test_e_5_loading_the_previous_scripts_and_this_one_in_any_order_works(self):
        self.assertEqual([], order_import_problems())

    def test_e_8_the_script_uses_no_name_of_the_injection_harness_criteria(self):
        src = read(SCRIPT_REL)
        for w in HARNESS_WORDS:
            self.assertNotIn(w, src, w)


class MutantTest(unittest.TestCase):
    def test_f_1_every_mutant_turns_its_checks_red_and_the_files_are_unchanged(self):
        before = (sha_of(SCRIPT_REL), sha_or_none(RECORD_REL), sha_of(INSTRUCTION_REL))
        modules_before = dict(sys.modules)
        results = run_mutants()
        self.assertEqual(before, (sha_of(SCRIPT_REL), sha_or_none(RECORD_REL), sha_of(INSTRUCTION_REL)))
        self.assertEqual([], [k for k, v in modules_before.items() if sys.modules.get(k) is not v])
        silent = set(silent_names())
        bad = [(n, err) for n, _t, red, err in results if n not in silent and (not red or err)]
        self.assertEqual([], bad)                                                           # 黙った変異・読み込めない変異(変異自身の誤り)は無い
        self.assertEqual(len(all_mutants()), len(results))
        self.assertGreaterEqual(len(results), 600)

    def test_f_2_the_unmutated_script_is_green_on_every_check(self):
        for tag, fn in CHECKS.items():
            self.assertEqual([], check_by_name(tag)(MS), tag)

    def test_f_3_the_silent_mutants_are_silent_for_the_stated_reason(self):
        u"""同値の変異は、どの検査でも元と同じ(理由は ``SILENT_BY_DESIGN`` に書いた字)。"""
        table = dict((n, src) for n, src, _t in all_mutants())
        for name, why in SILENT_BY_DESIGN:
            self.assertTrue(why.strip(), name)
            mod = load_source(table[name])
            for tag in CHECKS:
                self.assertEqual([], check_by_name(tag)(mod), (name, tag))

    def test_f_4_the_table_is_complete_and_names_are_unique(self):
        self.assertEqual([], mutant_table_problems())


if __name__ == "__main__":
    unittest.main()
