# -*- coding: utf-8 -*-
u"""封 docs/XBRL_TYPE_CARRYOVER_SEAL_2026-11-22.md(XK0 ― 同じ会社の前の年の型と対応表が、今年の型にどれだけ持ち越せるか)の封の門。

**この門は置き場を読まない**(今年の側・前の年の側の置き場・分析の本物は 1 度も開かない)。通信しない。
読むのは repo の中の封の file・script だけ。作り物の 2 年分の型(``analyze`` の戻り値の形)を、本物の関数のまま直に渡す(zip は作らない)。作り物の名・日付は全部作り物(本物の字は使わない)。

**この門が縛るもの**

1. 封の字: 封の commit(1fc4c736)・封の file が commit した blob と同じ・組の数 63・訓練 3・判定 60・4 つの分け・期の区分・予測の境(XK0-1〜XK0-10。以上/未満/超える/以下)・
   先に疑う旗の 6 つ・限界の 6 行・記録に書かないものの字が、script の定数と同じ。
2. engine は封の commit から 0 行。境界の門の import 一覧にこの便の名前を足していない。
3. 作り物の 2 年分の型で、1.〜6.(名・名が足りる行(科目・軸・member を 1 つずつ)・同じ行(日)・同じ行の中身の 4 つの分けの順・`-0`・`無い` 同士・枠・逆向き)を手で数えた値と照らす(近くの数と違う数)。
   期の区分の 4 つ・鍵(日)と鍵(枠)の別・今年と前の年の取り違え・期の名を前の年の書類の決めで付けること・退化値(空の型・行 0・名 0・断った組だけ)も同じ。
4. 断り: 今年の側が断れば前の年の側は分析しない・断った組は数の全部で 0・分母にも入れない。M.Refuse 以外の例外は止まる。
5. 訓練の 3 組と判定の 60 組と全部の 63 組を分け(番号 3 / 4 の境)、判定の数(XK0-1〜XK0-10)と旗 6 つを、手で数えた値と照らす。旗は立っても止めず、境で変わる。
6. 記録: 排他で書く・書く前と書いた後に禁止のものを検査する・``--check`` が組ごとの数から集計・判定の数・旗を導き直して照らす・便 XM0 の記録の並びが違えば止まる。
7. script の import は標準ライブラリと importlib だけ(engine を読む import を足さない)。前の便の script は importlib で一意の名で読み、関数は呼ぶ(写さない)。``derive_folder``・``process_doc`` は呼ばない。
8. 行頭の名前: この門は ``ENGINE_LATER``・``UNTOUCHED``・``PIN_DEF``・``LATER_ENGINE_COMMITS``・``FROZEN_LATER``・``ENGINE_TRANSITIONS`` を行頭に置かない。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``。script の字を 1 か所替えた版を memory の中に作る。file は書き換えない)。
黙る変異は ``SILENT_BY_DESIGN`` に理由とともに置き、「黙ること」自体を別の試験で縛る。
記録(``fixtures/xbrl/cd8/type_carryover_2026-11-22.json``)は本番の走りの後に書かれる。記録が在れば中身を見て、無ければ見ない(skip にしない。見る作りが「在れば」)。
"""
import ast
import collections
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
    mod = types.ModuleType("xbrl_type_carryover_mutant")
    mod.__file__ = os.path.join(ROOT, SCRIPT_REL)
    before = dict(sys.modules)
    try:
        exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    finally:
        for k, v in before.items():
            if sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


SEAL_REL = "docs/XBRL_TYPE_CARRYOVER_SEAL_2026-11-22.md"
SEAL_COMMIT_SHORT = "1fc4c736"                # 封の commit(literal に留める。script の定数と違えば赤)
SCRIPT_REL = "measure/xbrl_type_carryover_2026-11-22.py"
GATE_REL = "tests/measure/test_xbrl_type_carryover_seal.py"
RECORD_REL = "fixtures/xbrl/cd8/type_carryover_2026-11-22.json"
XM0_RECORD_REL = "fixtures/xbrl/cd8/input_type_2026-11-22.json"
MS = load_module(SCRIPT_REL, "xbrl_type_carryover_script_for_seal_gate")
PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_type_carryover_seal")      # 順序・履歴の部品。門としては走らせない
ORDER_FILES = (SCRIPT_REL, GATE_REL)          # 記録の順序は記録が在るときの結果の門に置く
od = collections.OrderedDict
KN, KT = u"数", u"文"
KINDS = (u"科目", u"軸", u"member")
CLASS4 = (u"当期", u"前期", u"それより前", u"提出日")
CONTENT4 = (u"全部同じ", u"値は同じで、単位・表示の位・精度のどれかが違う", u"値が違う", u"片方だけが 無い")
NONE_V = u"無い"


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


def stops(ms, fn, *a, **kw):
    u"""fn が ``ms.Stop`` を投げれば True。投げなければ False。別の例外は投げ直す。"""
    try:
        fn(*a, **kw)
    except ms.Stop:
        return True
    return False


class Temp(object):
    def __enter__(self):
        self.d = tempfile.mkdtemp(prefix="xk0_gate_")
        return self.d

    def __exit__(self, *a):
        shutil.rmtree(self.d, ignore_errors=True)


# ======================================================================== 作り物の 2 年分の型(``analyze`` の戻り値の形)
def D(y, m, d):
    return u"%04d-%02d-%02d" % (y, m, d)


DEC_C = od([("start", D(2030, 4, 1)), ("end", D(2031, 3, 31)), ("filing", D(2031, 6, 30))])       # 今年の書類の決め
DEC_P = od([("start", D(2029, 4, 1)), ("end", D(2030, 3, 31)), ("filing", D(2030, 6, 30))])       # 前の年の書類の決め


def DUR(y1, y2):
    return ("duration", [D(y1, 4, 1), D(y2, 3, 31)])


def INST(y, m, d):
    return ("instant", [D(y, m, d)])


X = u"xa_cor:"
I1, I2, I3, I4, I5, I6, I7 = [X + u"Item%d" % i for i in range(1, 8)]
GONE, TEXT1 = X + u"Gone", X + u"Text1"
NEW1, TNEW, NEWC, NEWD, NEWE, NEWH = u"xb:New1", u"xb:TNew", X + u"NewC", u"xc_cor2:NewD", u"xe_cor:NewE", u"xh:NewH"
AX1, AX2, AXGONE, AXNEW = X + u"Ax1", X + u"Ax2", X + u"AxGone", X + u"AxNew"
MB1, MB2, MBGONE, MBNEW = X + u"Mb1", X + u"Mb2", X + u"MbGone", u"xf:MbNew"
JPY, USD = u"通貨:JPY", u"通貨:USD"


def R(kind, name, per, dims=(), target=u"既定", value=u"1", unit=JPY, shift=6, prec=-6):
    u"""型の行 1 つ(``analyze`` の rows の形)。文の行は値・単位・位・精度が None。"""
    pk, dates = per
    if kind == KT:
        value = unit = shift = prec = None
    return od([("kind", kind), ("name", name), ("period", list(dates)), ("pkind", pk), ("target", target),
               ("dims", [list(x) for x in dims]), ("value", value), ("unit", unit), ("shift", shift), ("prec", prec), ("count", 1)])


def NIL(kind, name, per, dims=()):
    return R(kind, name, per, dims, value=NONE_V, shift=None, prec=None)


def AN(dec, rows, outside=()):
    u"""分析の戻り値の形: 型の行ごとに型に入った fact を 1 つ・型の外の fact(isnum, 理由の集まり)。"""
    facts = [{"isnum": r["kind"] == KN, "reasons": set()} for r in rows] + [{"isnum": n, "reasons": set(rs)} for n, rs in outside]
    return {"dec": dec, "rows": list(rows), "facts": facts}


# ---- 場面 S1: 今年の側(数 24 行・文 5 行)。コメントの「日」は鍵(日)が前の年に在る・「枠」は鍵(枠)が在る
CUR_S1 = [
    R(KN, I1, DUR(2030, 2031), value=u"100"),                                              # c1 当期・枠
    R(KN, I1, DUR(2029, 2030), value=u"90"),                                               # c2 前期・日(全部同じ)・枠
    R(KN, I1, DUR(2028, 2029), value=u"81"),                                               # c3 それより前・日(値が違う)
    R(KN, I2, INST(2030, 3, 31), dims=[(AX1, MB1)], value=u"50", unit=USD),                # c4 前期・日(単位だけ違う)
    NIL(KN, I3, INST(2030, 3, 31)),                                                        # c5 前期・日(片方だけが 無い)
    R(KN, I4, INST(2030, 3, 31), value=u"-0"),                                             # c6 前期・日(-0 と 0 で値が違う)
    NIL(KN, I5, INST(2030, 3, 31)),                                                        # c7 前期・日(無い 同士で全部同じ)
    R(KN, I6, INST(2030, 3, 31), value=u"7", shift=3),                                     # c8 前期・日(位だけ違う)
    R(KN, I7, INST(2030, 3, 31), value=u"7", prec=0),                                      # c9 前期・日(精度だけ違う)
    R(KN, NEW1, DUR(2030, 2031)),                                                          # c10 当期・名が足りない(科目)
    R(KN, I1, DUR(2030, 2031), dims=[(AXNEW, MB1)]),                                       # c11 当期・名が足りない(軸だけ)
    R(KN, I1, DUR(2030, 2031), dims=[(AX1, MBNEW)]),                                       # c12 当期・名が足りない(member だけ)
    R(KN, I1, INST(2028, 3, 31), value=u"3"),                                              # c13 それより前・日(全部同じ)
    R(KN, I1, INST(2031, 6, 30), value=u"8"),                                              # c14 提出日・枠
    R(KN, I1, DUR(2030, 2031), dims=[(AX1, MB1)], value=u"5"),                             # c15 当期
    R(KN, I1, DUR(2030, 2031), dims=[(AX2, MB2), (AX1, MB1)], value=u"12"),                # c16 当期・枠(次元の並びが違っても同じ集まり)
    R(KN, I1, DUR(2029, 2030), dims=[(AX2, MB2), (AX1, MB1)], value=u"12"),                # c17 前期・日(全部同じ。集まり)
    R(KN, I1, DUR(2030, 2031), target=u"個別"),                                            # c18 当期(対象が違えば枠は無い)
    R(KN, I1, DUR(2029, 2030), target=u"個別", value=u"90"),                               # c19 前期(対象が違えば日は無い)
    R(KN, NEWC, DUR(2030, 2031)),                                                          # c21 当期・新しい名(_cor)
    R(KN, NEWD, DUR(2030, 2031)),                                                          # c22 当期・新しい名(接頭辞に _cor を含むが終わらない)
    R(KN, NEWE, DUR(2030, 2031)),                                                          # c23 当期・新しい名(_cor)
    R(KN, I2, INST(2031, 3, 31), dims=[(AX1, MB1)], value=u"60"),                          # c24 当期・枠
    R(KN, NEWH, DUR(2030, 2031)),                                                          # c25 当期・新しい名
    R(KT, TEXT1, DUR(2030, 2031)),                                                         # t1 当期・枠
    R(KT, TEXT1, DUR(2029, 2030)),                                                         # t2 前期・日・枠
    R(KT, TEXT1, DUR(2028, 2029)),                                                         # t3 それより前・日
    R(KT, TNEW, DUR(2030, 2031)),                                                          # t4 当期・新しい名
    R(KT, I1, DUR(2029, 2030)),                                                            # t5 前期(同じ名・日の数の行 c2 と種類だけ違う)
]
PRIOR_S1 = [
    R(KN, I1, DUR(2029, 2030), value=u"90"),                                               # P1
    R(KN, I1, DUR(2028, 2029), value=u"80"),                                               # P2
    R(KN, I2, INST(2030, 3, 31), dims=[(AX1, MB1)], value=u"50"),                          # P3
    R(KN, I3, INST(2030, 3, 31), value=u"5"),                                              # P4
    R(KN, I4, INST(2030, 3, 31), value=u"0"),                                              # P5
    NIL(KN, I5, INST(2030, 3, 31)),                                                        # P6
    R(KN, I6, INST(2030, 3, 31), value=u"7"),                                              # P7
    R(KN, I7, INST(2030, 3, 31), value=u"7"),                                              # P8
    R(KN, GONE, DUR(2029, 2030)),                                                          # P9 消えた名
    R(KN, I1, DUR(2029, 2030), dims=[(AXGONE, MBGONE)]),                                   # P10 消えた軸・member
    R(KN, I1, INST(2030, 6, 30), value=u"9"),                                              # P14 提出日
    R(KN, I1, INST(2028, 3, 31), value=u"3"),                                              # P15
    R(KN, I1, DUR(2029, 2030), dims=[(AX1, MB1), (AX2, MB2)], value=u"12"),                # P16
    R(KN, GONE, INST(2030, 3, 31)),                                                        # P17 消えた名の行(前の年だけ)
    R(KN, GONE, INST(2029, 3, 31)),                                                        # P18
    R(KN, GONE, DUR(2028, 2029)),                                                          # P19
    R(KT, TEXT1, DUR(2029, 2030)),                                                         # P11
    R(KT, TEXT1, DUR(2028, 2029)),                                                         # P12
]
OUT_C = ((True, {"e"}), (True, {"d", "f"}), (False, {"a"}))
OUT_P = ((True, {"e"}),)
CUR1, PRIOR1 = AN(DEC_C, CUR_S1, OUT_C), AN(DEC_P, PRIOR_S1, OUT_P)


def hand(**kw):
    u"""手で数えた 1 組の数。名前の付け方は script の記録と同じ。"""
    return kw


def flat(out):
    u"""組の数 → 手で数えた値と比べる形(数は tuple に)。"""
    nm = out[u"対応表の名"]
    return dict(
        facts=tuple((out[u"対象の fact"][s][KN], out[u"対象の fact"][s][KT]) for s in (u"今年", u"前の年")),
        outside=tuple((out[u"型の外の fact"][s][u"合計"][KN], out[u"型の外の fact"][s][u"合計"][KT]) for s in (u"今年", u"前の年")),
        reasons=tuple(tuple(out[u"型の外の fact"][s][u"理由ごと"][r][k] for r in "abcdefgh") for s in (u"今年", u"前の年") for k in (KN, KT)),
        rows=tuple((out[u"型の行"][s][KN], out[u"型の行"][s][KT]) for s in (u"今年", u"前の年")),
        names=tuple(tuple(nm[k].values()) for k in KINDS),
        enough=(out[u"名が足りる行"][KN], out[u"名が足りる行"][KT]),
        cls=tuple(tuple(out[u"今年の行の期の区分"][k].values()) for k in (KN, KT)),
        same=tuple(tuple(out[u"同じ行(日)"][k].values()) for k in (KN, KT)),
        content=tuple(out[u"同じ行の中身(数)"].values()),
        frame=tuple(tuple(out[u"枠が在る行"][k].values()) for k in (KN, KT)),
        back=tuple(tuple(out[u"逆向き"][k].values()) for k in (KN, KT)))


HAND_S1 = dict(
    facts=((26, 6), (17, 2)), outside=((2, 1), (1, 0)),
    reasons=((0, 0, 0, 1, 1, 1, 0, 0), (1, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 1, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0)),
    rows=((24, 5), (16, 2)),
    names=((14, 8, 6, 2, 4, 1), (3, 2, 1, 1, 0, 1), (3, 2, 1, 0, 1, 1)),
    enough=(17, 4), cls=((12, 9, 2, 1), (2, 2, 1, 0)), same=((0, 8, 2, 0), (0, 1, 1, 0)), content=(4, 3, 2, 1),
    frame=((3, 1, 0, 1), (1, 1, 0, 0)), back=((16, 10, 5, 11), (2, 2, 2, 0)))
# S2(小さい組): 今年 e1(当期・枠)・e2(前期・日で全部同じ)・前の年 q1
CUR2 = AN(DEC_C, [R(KN, I1, DUR(2030, 2031), value=u"11"), R(KN, I1, DUR(2029, 2030), value=u"10")])
PRIOR2 = AN(DEC_P, [R(KN, I1, DUR(2029, 2030), value=u"10")])
HAND_S2 = dict(
    facts=((2, 0), (1, 0)), outside=((0, 0), (0, 0)), reasons=((0,) * 8,) * 4, rows=((2, 0), (1, 0)),
    names=((1, 1, 0, 0, 0, 0), (0,) * 6, (0,) * 6), enough=(2, 0), cls=((1, 1, 0, 0), (0,) * 4), same=((0, 1, 0, 0), (0,) * 4), content=(1, 0, 0, 0),
    frame=((1, 0, 0, 0), (0,) * 4), back=((1, 1, 1, 0), (0, 0, 0, 0)))
EMPTY_C, EMPTY_P = AN(DEC_C, []), AN(DEC_P, [])
# S3: 前の年が空で、新しい名の接頭辞だけを変える(_cor で終わる・含むが終わらない・cor だけ・_cor だけ・大文字・接頭辞なし)。今年の行は全部 7 行の数の行(当期)
CUR3 = AN(DEC_C, [R(KN, nm, DUR(2030, 2031)) for nm in (u"a_cor:Item9", u"a_cor2:Item9", u"acor:Item9", u"_cor:Item9", u"cor_:Item9", u"A_COR:Item9", u"NoColon_cor")])
# S4: 次元が 2 つの行(1 つでも前の年の対応表に無ければ名が足りない)。今年 3 行・前の年 1 行
CUR4 = AN(DEC_C, [R(KN, I1, DUR(2030, 2031), dims=[(AX1, MB1), (AXNEW, MB1)]), R(KN, I1, DUR(2030, 2031), dims=[(AX1, MB1), (AX1, MBNEW)]), R(KN, I1, DUR(2030, 2031), dims=[(AX1, MB1)])])
PRIOR4 = AN(DEC_P, [R(KN, I1, DUR(2029, 2030), dims=[(AX1, MB1)])])
HAND_S4 = dict(rows=((3, 0), (1, 0)), enough=(1, 0), cls=((3, 0, 0, 0), (0,) * 4), same=((0,) * 4, (0,) * 4), frame=((1, 0, 0, 0), (0,) * 4), content=(0, 0, 0, 0),
               names=((1, 1, 0, 0, 0, 0), (2, 1, 1, 1, 0, 0), (2, 1, 1, 0, 1, 0)), back=((1, 0, 1, 0), (0, 0, 0, 0)))
# S5: 今年の当期・提出日の日が前の年の行に在る作り物(本物では起きない。旗 1 の形)。同じ行(日)は当期 1・前期 1・提出日 1。前の年の行の期の名は書類の決めで付く(行 3 つのうち枠は 1 つ)
CUR5 = AN(DEC_C, [R(KN, I1, DUR(2030, 2031)), R(KN, I1, INST(2031, 6, 30)), R(KN, I1, DUR(2029, 2030))])
PRIOR5 = AN(DEC_P, [R(KN, I1, DUR(2030, 2031)), R(KN, I1, INST(2031, 6, 30)), R(KN, I1, DUR(2029, 2030))])
HAND_S5 = dict(rows=((3, 0), (3, 0)), enough=(3, 0), cls=((1, 1, 0, 1), (0,) * 4), same=((1, 1, 0, 1), (0,) * 4), content=(3, 0, 0, 0), frame=((1, 0, 0, 0), (0,) * 4),
               names=((1, 1, 0, 0, 0, 0), (0,) * 6, (0,) * 6), back=((3, 3, 1, 2), (0, 0, 0, 0)))
HAND_S3 = dict(facts=((7, 0), (0, 0)), rows=((7, 0), (0, 0)), names=((7, 0, 7, 2, 5, 0), (0,) * 6, (0,) * 6), enough=(0, 0), cls=((7, 0, 0, 0), (0,) * 4))
HAND_S1_VS_EMPTY = dict(
    facts=((26, 6), (0, 0)), outside=((2, 1), (0, 0)), reasons=HAND_S1["reasons"][:2] + ((0,) * 8,) * 2, rows=((24, 5), (0, 0)),
    names=((14, 0, 14, 10, 4, 0), (3, 0, 3, 3, 0, 0), (3, 0, 3, 2, 1, 0)), enough=(0, 0), cls=HAND_S1["cls"], same=((0,) * 4, (0,) * 4), content=(0, 0, 0, 0),
    frame=((0,) * 4, (0,) * 4), back=((0, 0, 0, 0), (0, 0, 0, 0)))
HAND_EMPTY_VS_S1 = dict(
    facts=((0, 0), (17, 2)), outside=((0, 0), (1, 0)), reasons=((0,) * 8, (0,) * 8, HAND_S1["reasons"][2], (0,) * 8), rows=((0, 0), (16, 2)),
    names=((0, 0, 0, 0, 0, 9), (0, 0, 0, 0, 0, 3), (0, 0, 0, 0, 0, 3)), enough=(0, 0), cls=((0,) * 4, (0,) * 4), same=((0,) * 4, (0,) * 4), content=(0, 0, 0, 0),
    frame=((0,) * 4, (0,) * 4), back=((16, 0, 0, 16), (2, 0, 0, 2)))


def entry_of(ms, n, cur, prior):
    u"""作り物の分析を返す analyzer で ``pair_entry`` を呼ぶ。(組, 呼ばれた path の並び)。"""
    an, calls = fake_analyzer({"c": cur, "p": prior})
    ent, nm = ms.pair_entry(n, "c", "p", an)
    return ent, nm, calls


def fake_analyzer(table):
    calls = []

    def an(path):
        calls.append(path)
        v = table[path]
        if isinstance(v, BaseException):
            raise v
        return v
    return an, calls


# ======================================================================== 1. 封の字
def seal_text():
    return read(SEAL_REL)


EXPECT_BOUNDS = od([("XK0-1", (96, True, None, False)), ("XK0-2", (97, True, None, False)), ("XK0-3", (97, True, None, False)), ("XK0-4", (96, True, 100, False)),
                    ("XK0-5", (44, True, 52, False)), ("XK0-6", (95, True, None, False)), ("XK0-7", (50, False, None, False)), ("XK0-8", (None, False, 3, True)),
                    ("XK0-9", (48, True, None, False)), ("XK0-10", (57, True, None, False))])
SEAL_BOUND_TEXT = {
    "XK0-1": (u"今年の科目の名のうち、前の年の対応表に在る名は 96% 以上", u"96% 未満"), "XK0-2": (u"数の型の行のうち、名が足りる行は 97% 以上", u"97% 未満"),
    "XK0-3": (u"期の区分が「前期」か「それより前」の数の行のうち、同じ行が前の年の型に在るのは 97% 以上", u"97% 未満"),
    "XK0-4": (u"同じ行(数)のうち「全部同じ」は 96% 以上 100% 未満", u"96% 未満・または 100%"),
    "XK0-5": (u"今年の数の型の行の全部のうち、「同じ行」で「全部同じ」の行は 44% 以上 52% 未満", u"44% 未満・または 52% 以上"),
    "XK0-6": (u"今年の数の型の行のうち、枠が在る行は 95% 以上", u"95% 未満"), "XK0-7": (u"新しい科目の名のうち、接頭辞が `_cor` で終わるものは半分より多い", u"半分以下"),
    "XK0-8": (u"断った組は 3 以下", u"4 以上"), "XK0-9": (u"科目の名の持ち越しが 95% 以上の組は、60 組のうち 48 組以上", u"47 組以下"),
    "XK0-10": (u"同じ行(数)に「全部同じ」でない行が 1 つ以上在る組は、60 組のうち 57 組以上", u"56 組以下")}
#: 予測の境で値を替える(下限・上限の中・ちょうど・すぐ外)。(名前, [(値, 当たりか)])。値は % か組の数
BOUND_CASES = od([
    ("XK0-1", [(96, True), (95.9, False), (100, True)]), ("XK0-2", [(97, True), (96.9, False)]), ("XK0-3", [(97, True), (96.9, False)]),
    ("XK0-4", [(96, True), (95.9, False), (99.9, True), (100, False)]), ("XK0-5", [(44, True), (43.9, False), (51.9, True), (52, False)]),
    ("XK0-6", [(95, True), (94.9, False)]), ("XK0-7", [(50, False), (50.1, True), (49.9, False)]), ("XK0-8", [(3, True), (4, False), (0, True)]),
    ("XK0-9", [(48, True), (47, False)]), ("XK0-10", [(57, True), (56, False)])])
SEAL_FLAG_TEXT = (u"期の区分が「当期」の行に同じ行(日)が 1 つでも在る・科目の名の持ち越しが 60 組の全部で 100%・同じ行(数)が 60 組の合計で 0・枠が在る行が名が足りる行より多い組が在る・"
                  u"断った組が 6 以上・便 XM0 の記録の、同じ書類の型の行の数(数・文)とこの便の今年の側の型の行の数が違う組が在る")


def holds(b, x):
    lo, lo_in, hi, hi_in = b
    ok = True
    if lo is not None:
        ok = ok and (x >= lo if lo_in else x > lo)
    if hi is not None:
        ok = ok and (x <= hi if hi_in else x < hi)
    return ok


def seal_problems(ms=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    out = []
    if ms.SEAL_COMMIT != SEAL_COMMIT_SHORT or ms.SEAL_REL != SEAL_REL:
        out.append(u"封の commit・path が門と違う")
    if ms.SCRIPT_REL != SCRIPT_REL or ms.RECORD_REL != RECORD_REL or ms.XM0_RECORD_REL != XM0_RECORD_REL:
        out.append(u"script・記録の path が封・門と違う")
    if ms.PAIRS_WANT != 63 or u"組の数が 63 でなければ script は止まる" not in seal:
        out.append(u"組の数 63 が封と違う")
    if (ms.SEEN_MAX_NO, ms.TRAIN_WANT, ms.JUDGE_WANT, tuple(ms.DEV_NOS)) != (3, 3, 60, (1, 2, 3)) or u"番号 1・2・3 が訓練の 3 組、番号 4〜63 が判定の 60 組" not in seal:
        out.append(u"訓練の 3 組・判定の 60 組の分けが封と違う")
    if ms.DOCS_WANT != 67:
        out.append(u"今年の側の本数 67 が便 XY0 の字と違う")
    if tuple(ms.KINDS) != KINDS or (ms.KN, ms.KT) != (KN, KT) or tuple(ms.CLASS4) != CLASS4 or tuple(ms.CONTENT4) != CONTENT4 or ms.COR_END != u"_cor" or tuple(ms.REASONS) != tuple(u"abcdefgh"):
        out.append(u"種類・期の区分・同じ行の中身の分け・_cor・型の外の理由の字が門と違う")
    for w in (u"**型の行の鍵(日)**", u"**型の行の鍵(枠)**", u"**期の区分**(今年の行): 期の名が `CurrentYear` なら「当期」・`Prior1Year` なら「前期」・`Prior<N>Year`(N は 2 以上)なら「それより前」・`FilingDate` なら「提出日」",
              u"種類は 科目・軸・member の 3 つ", u"今年の行は今年の書類の決めで、前の年の行は前の年の書類の決めで名を付ける", u"接頭辞が `_cor` で終わる/終わらない",
              u"全部同じ: 値・単位・表示の位・精度が全部同じ", u"`無い` 同士は同じ。`-0` と `0` は違う", u"値は同じで、単位・表示の位・精度のどれかが違う", u"値が違い、どちらも `無い` でない", u"片方だけが `無い`",
              u"3. の行を次の 4 つに重ならないように分ける", u"**枠が在る行の値は別の年の値なので、値は比べない。**", u"今年、要らなくなった枠 = 前の年の行の数 − 枠が今年に在る数",
              u"断った組は下の数の全部で 0 と数える(分母にも入れない)", u"`M.derive_folder`・`M.process_doc` は呼ばない", u"個別を表す軸と member は便 XM0 のとおり対応表に入らない",
              u"記録に書かないもの: docID・会社の名・EDINET コード・file の名・要素の名・接頭辞の字・文脈の名・値・日付・本文の字。組は番号だけで書く。"):
        if w not in seal:
            out.append(u"封に字が無い: %s" % w)
    if dict(ms.BOUNDS) != dict(EXPECT_BOUNDS):
        out.append(u"予測の境の数が門と違う")
    for k, (a, b) in SEAL_BOUND_TEXT.items():
        row_ = [ln for ln in seal.splitlines() if re.match(r"^\| %s(?!\d)" % re.escape(k), ln)]
        if len(row_) != 1 or a not in row_[0] or b not in row_[0]:
            out.append(u"封の予測の行の字が違う: %s" % k)
    for k, cases in BOUND_CASES.items():
        for x, want in cases:
            if holds(ms.BOUNDS[k], x) != want:
                out.append(u"予測の境の読みが違う: %s %s" % (k, x))
    if SEAL_FLAG_TEXT not in seal or ms.FLAG_REFUSE_MIN != 6 or ms.KEEP_ONE_PCT != 95:
        out.append(u"先に疑う旗・95% の字が封と違う")
    sec7 = seal.split(u"## §7", 1)[-1]
    lines7 = [ln[2:] for ln in sec7.splitlines() if ln.startswith(u"- ")]
    if len(lines7) != 6 or list(ms.LIMITS) != lines7:
        out.append(u"限界の 6 行が封 §7 と違う")
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
    u"""封 ⊏ script・この門(足した commit が封の後)。未 commit は赤。"""
    others = list(ORDER_FILES) if others is None else others
    return list(PR.order_problems(root, PREFIX, SEAL_REL, seal_short, [], others))


def engine_zero_problems(root=REPO):
    rc = subprocess.run(["git", "-C", root, "diff", "--name-only", SEAL_COMMIT_SHORT, "--", PREFIX + "adapters", PREFIX + "core"], stdout=subprocess.PIPE, universal_newlines=True)
    return [u"engine が封の後に変わっている: %s" % ln for ln in rc.stdout.splitlines() if ln.strip()]


# ======================================================================== 2. 部品(名・鍵・期の区分・中身の分け・率・組の判定)
def blank(ms, n, **over):
    u"""全部 0 の組(``zero_pair``)に番号と旗用の数を付けた記録の書類 1 つ。``over`` は {欄: 値} で上書き。"""
    ent = od([(u"番号", n)])
    ent.update(ms.zero_pair())
    ent[u"旗用の数"] = ms.entry_tail((True, 0, 0))
    for k, v in over.items():
        ent[k] = v
    return ent


def pure_problems(ms=None):
    ms = ms or MS
    out = []
    for name, want in ((u"xa_cor:Foo", u"xa_cor"), (u"Foo", u""), (u"a:b:c", u"a"), (u"xc_cor2:N", u"xc_cor2"), (u"", u"")):
        if ms.name_prefix(name) != want:
            out.append(u"接頭辞が違う: %r" % name)
    if ms.dims_key(R(KN, I1, DUR(2030, 2031), dims=[(u"b", u"2"), (u"a", u"1")])) != ((u"a", u"1"), (u"b", u"2")) or ms.dims_key(R(KN, I1, DUR(2030, 2031))) != ():
        out.append(u"次元の集まりの鍵が違う")
    base = R(KN, I1, DUR(2029, 2030))
    want_day = (KN, I1, "duration", (D(2029, 4, 1), D(2030, 3, 31)), u"既定", ())
    if ms.key_day(base) != want_day:
        out.append(u"鍵(日)が違う: %s" % (ms.key_day(base),))
    if ms.key_frame(base, DEC_C) != (KN, I1, "duration", "Prior1Year", u"既定", ()) or ms.key_frame(base, DEC_P) != (KN, I1, "duration", "CurrentYear", u"既定", ()):
        out.append(u"鍵(枠)が違う(期の名はその行の書類の決めで付ける)")
    for what, other in ((u"種類", R(KT, I1, DUR(2029, 2030))), (u"科目", R(KN, I2, DUR(2029, 2030))), (u"期間の種類", R(KN, I1, INST(2030, 3, 31))), (u"期間の日", R(KN, I1, DUR(2028, 2029))),
                        (u"対象", R(KN, I1, DUR(2029, 2030), target=u"個別")), (u"次元", R(KN, I1, DUR(2029, 2030), dims=[(AX1, MB1)])), (u"member", R(KN, I1, DUR(2029, 2030), dims=[(AX1, MB2)]))):
        if ms.key_day(other) == ms.key_day(base) or ms.key_frame(other, DEC_C) == ms.key_frame(base, DEC_C):
            out.append(u"鍵が %s の違いを見ない" % what)
    odd = ("duration", [D(2029, 4, 1), D(2030, 3, 31)])
    for what, per in ((u"期間の終わりの日", ("duration", [D(2029, 4, 1), D(2030, 6, 30)])), (u"期間の始まりの日", ("duration", [D(2029, 5, 1), D(2030, 3, 31)])), (u"期間の長さの形(時点)", ("instant", [D(2030, 3, 31)]))):
        if ms.key_day(R(KN, I1, per)) == ms.key_day(R(KN, I1, odd)):
            out.append(u"鍵(日)が %s の違いを見ない" % what)
    if ms.key_day(R(KN, I1, DUR(2029, 2030), value=u"1")) != ms.key_day(R(KN, I1, DUR(2029, 2030), value=u"2", unit=USD, shift=1, prec=0)):
        out.append(u"鍵(日)が値・単位・位・精度を見ている")
    for per, dec, want in ((DUR(2030, 2031), DEC_C, u"当期"), (INST(2031, 3, 31), DEC_C, u"当期"), (DUR(2029, 2030), DEC_C, u"前期"), (INST(2030, 3, 31), DEC_C, u"前期"),
                           (DUR(2028, 2029), DEC_C, u"それより前"), (INST(2022, 3, 31), DEC_C, u"それより前"), (INST(2031, 6, 30), DEC_C, u"提出日"), (DUR(2029, 2030), DEC_P, u"当期"),
                           (INST(2030, 6, 30), DEC_P, u"提出日"), (INST(2029, 3, 31), DEC_P, u"前期")):
        got = ms.period_class(R(KN, I1, per), dec)
        if got != want:
            out.append(u"期の区分が違う: %s %s -> %s(正しくは %s)" % (per, dec["end"], got, want))
    if not stops(ms, ms.period_class, R(KN, I1, INST(2031, 1, 1)), DEC_C):
        out.append(u"期の名が付かない行で止まらない")

    def rc(value, unit=JPY, shift=6, prec=-6):
        return R(KN, I1, DUR(2029, 2030), value=value, unit=unit, shift=shift, prec=prec)

    nil_r = NIL(KN, I1, DUR(2029, 2030))
    for r, q, want in ((rc(u"1"), rc(u"1"), CONTENT4[0]), (rc(u"1"), rc(u"2"), CONTENT4[2]), (rc(u"1"), rc(u"1", unit=USD), CONTENT4[1]), (rc(u"1"), rc(u"1", shift=3), CONTENT4[1]),
                       (rc(u"1"), rc(u"1", prec=0), CONTENT4[1]), (nil_r, nil_r, CONTENT4[0]), (nil_r, rc(u"1"), CONTENT4[3]), (rc(u"1"), nil_r, CONTENT4[3]),
                       (rc(u"-0"), rc(u"0"), CONTENT4[2]), (rc(u"-0"), rc(u"-0"), CONTENT4[0]), (rc(u"1"), rc(u"2", unit=USD, shift=1, prec=0), CONTENT4[2]),
                       (nil_r, R(KN, I1, DUR(2029, 2030), value=u"1", unit=USD), CONTENT4[3]), (rc(u"1.50"), rc(u"1.5"), CONTENT4[2])):
        if ms.content_class(r, q) != want:
            out.append(u"同じ行の中身の分けが違う: %s %s -> %s(正しくは %s)" % (r["value"], q["value"], ms.content_class(r, q), want))
    nil_usd = NIL(KN, I1, DUR(2029, 2030))
    nil_usd["unit"] = USD
    if ms.content_class(nil_r, nil_usd) != CONTENT4[1]:
        out.append(u"無い 同士で単位が違うとき、全部同じになっている")
    for n_, d_, want in ((1, 8, 12.5), (1, 16, 6.3), (5, 5, 100.0), (959, 1000, 95.9), (146, 160, 91.3), (66, 160, 41.3), (0, 7, 0.0)):
        got = ms.rate_of(n_, d_)
        if tuple(got.values()) != (n_, d_, want):
            out.append(u"率が違う(数・分母・% の順。% は小数第 1 位・0.5 は上げる): %s" % dict(got))
    if ms.rate_of(0, 0)[u"%"] is not None:
        out.append(u"分母 0 の率が None でない")
    # 判定の組(XK0-9・XK0-10)
    def with_names(n_, d_, refused=False):
        e = blank(ms, 9)
        e[u"対応表の名"][u"科目"][u"今年"], e[u"対応表の名"][u"科目"][u"持ち越せる"] = d_, n_
        e[u"断った"] = refused
        return e

    for e, want in ((with_names(19, 20), True), (with_names(18, 20), False), (with_names(95, 100), True), (with_names(94, 100), False), (with_names(0, 0), False), (with_names(20, 20), True),
                    (with_names(19, 20, refused=True), False), (with_names(1, 1), True), (with_names(1000, 1053), False), (with_names(1000, 1052), True)):
        if ms.keep_pct_pair(e) != want:
            out.append(u"XK0-9 の組の判定が違う: %s" % (dict(e[u"対応表の名"][u"科目"]),))
    for vals, refused, want in (((5, 0, 0, 0), False, False), ((5, 1, 0, 0), False, True), ((5, 0, 1, 0), False, True), ((5, 0, 0, 1), False, True), ((0, 0, 0, 0), False, False), ((0, 3, 0, 0), False, True),
                                ((5, 2, 0, 0), True, False)):
        e = blank(ms, 9)
        for c, v in zip(CONTENT4, vals):
            e[u"同じ行の中身(数)"][c] = v
        e[u"断った"] = refused
        if ms.not_all_same_pair(e) != want:
            out.append(u"XK0-10 の組の判定が違う: %s %s" % (vals, refused))
    return out


# ======================================================================== 3. 2 年分の型の手の数
def count_problems(ms=None):
    ms = ms or MS
    out = []
    for name, cur, prior, h in ((u"S1", CUR1, PRIOR1, HAND_S1), (u"S2", CUR2, PRIOR2, HAND_S2), (u"S3(接頭辞)", CUR3, EMPTY_P, HAND_S3), (u"S4(次元が 2 つ)", CUR4, PRIOR4, HAND_S4), (u"S5(当期・提出日の同じ行)", CUR5, PRIOR5, HAND_S5), (u"S1 と空の前の年", CUR1, EMPTY_P, HAND_S1_VS_EMPTY), (u"空の今年と S1", EMPTY_C, PRIOR1, HAND_EMPTY_VS_S1)):
        got = flat(ms.count_types(cur, prior))
        for k, w in h.items():
            if got[k] != w:
                out.append(u"%s の数 %s が手で数えた値と違う: %s != %s" % (name, k, got[k], w))
    # 退化値: 空と空は全部 0(組の数の欄が全部 0 の ``zero_pair`` と同じ)
    if ms.dumps(ms.count_types(EMPTY_C, EMPTY_P)) != ms.dumps(ms.zero_pair()):
        out.append(u"空と空の型の数が全部 0 でない")
    # 今年と前の年を入れ替えると逆向きの数が入れ替わる(前の年の側として今年の分析を読んでいない)
    sw = flat(ms.count_types(PRIOR1, CUR1))
    if sw["rows"] != ((16, 2), (24, 5)) or sw["names"][0] != (9, 8, 1, 1, 0, 6) or sw["back"] != ((24, 10, 5, 19), (5, 2, 2, 3)) or sw["enough"] != (11, 2):
        out.append(u"今年と前の年を入れ替えた数が手で数えた値と違う: %s %s %s" % (sw["names"][0], sw["back"], sw["enough"]))
    # 前の年の行の鍵(日)が重なれば止まる
    dup = AN(DEC_P, [R(KN, I1, DUR(2029, 2030)), R(KN, I1, DUR(2029, 2030), value=u"2")])
    if not stops(ms, ms.count_types, CUR1, dup):
        out.append(u"前の年の型の行の鍵(日)が重なるのに止まらない")
    # 期の名を前の年の書類の決めで付ける: 前の年の行を今年の決めで名付けると鍵(枠)が合わなくなる(同じ型を両側に渡すと全部の行に枠が在る)
    same = flat(ms.count_types(CUR1, AN(DEC_C, CUR_S1)))
    if same["frame"] != ((12, 9, 2, 1), (2, 2, 1, 0)) or same["same"] != ((12, 9, 2, 1), (2, 2, 1, 0)):
        out.append(u"同じ型を両側に渡したときの同じ行・枠が全部の行にならない: %s" % (same["frame"],))
    return out


# ======================================================================== 4. 組 1 つ・断り・集計・判定の数・旗
def entry_problems_gate(ms=None):
    ms = ms or MS
    out = []
    ent, nm, calls = entry_of(ms, 4, CUR1, PRIOR1)
    if calls != ["c", "p"] or ent[u"番号"] != 4 or ent[u"断った"] or ent[u"断った年"] != u"" or ent[u"断った理由"] != u"":
        out.append(u"組の記録の頭が違う(番号・断った・分析の呼び方): %s" % calls)
    if flat(ent) != HAND_S1 or ent[u"旗用の数"] != od([(u"今年の側を分析できた", True), (u"今年の側の型の行", od([(KN, 24), (KT, 5)]))]):
        out.append(u"組の記録の数・旗用の数が手で数えた値と違う")
    if list(ent) != [u"番号"] + list(ms.zero_pair()) + [u"旗用の数"]:
        out.append(u"組の記録の欄の並びが違う")
    if not (set([u"Item1", I1, u"xa_cor", u"NewC", u"xb", u"MbNew", u"Mb1", u"Ax1", u"Gone"]) <= nm):
        out.append(u"secret 用の名の集まりに名・接頭辞・局所名が入っていない(今年の側・前の年の側の両方): %s" % sorted(nm)[:5])
    # 今年の側が断れば前の年の側は分析しない
    ent, nm, calls = entry_of(ms, 5, ms.Refuse(u"理由ア"), PRIOR1)
    z = ms.zero_pair()
    if calls != ["c"] or not ent[u"断った"] or ent[u"断った年"] != u"今年" or ent[u"断った理由"] != u"理由ア" or nm != set():
        out.append(u"今年の側の断りの扱いが違う: %s %s" % (calls, ent[u"断った年"]))
    if dumps_body(ms, ent) != dumps_body(ms, z) or ent[u"旗用の数"][u"今年の側を分析できた"] or ent[u"旗用の数"][u"今年の側の型の行"][KN]:
        out.append(u"今年の側が断った組の数が 0 でない")
    ent, nm, calls = entry_of(ms, 6, CUR1, ms.Refuse(u"理由イ"))
    if calls != ["c", "p"] or not ent[u"断った"] or ent[u"断った年"] != u"前の年" or ent[u"断った理由"] != u"理由イ" or dumps_body(ms, ent) != dumps_body(ms, z):
        out.append(u"前の年の側の断りの扱いが違う(数の全部が 0)")
    if ent[u"旗用の数"] != od([(u"今年の側を分析できた", True), (u"今年の側の型の行", od([(KN, 24), (KT, 5)]))]) or u"Item1" not in nm:
        out.append(u"前の年の側が断った組の旗用の数が今年の側の型の行でない")
    both, _nm, calls = entry_of(ms, 7, ms.Refuse(u"理由ア"), ms.Refuse(u"理由イ"))
    if calls != ["c"] or both[u"断った年"] != u"今年" or both[u"断った理由"] != u"理由ア":
        out.append(u"両方の年が断るとき、先に断った今年の側を書いていない")
    if not _raises(ValueError, lambda: entry_of(ms, 8, ValueError("x"), PRIOR1)) or not _raises(ValueError, lambda: entry_of(ms, 8, CUR1, ValueError("x"))):
        out.append(u"M.Refuse 以外の例外を止めずに飲み込んでいる")
    # 集計: 訓練(番号 3 以下)と判定(4 以上)と全部。断った組は数に足さず・組には数える
    e = [entry_of(ms, n, c, p)[0] for n, c, p in ((2, CUR1, PRIOR1), (3, CUR2, PRIOR2), (4, CUR1, PRIOR1), (5, CUR2, PRIOR2), (6, ms.Refuse(u"理由ア"), PRIOR1))]
    tot = ms.totals_of(e)
    names_ = list(tot)
    if names_ != [u"訓練の 3 組", u"判定の 60 組", u"全部の 63 組"]:
        out.append(u"集計の 3 つの分けの名・並びが違う")
    tr, ju, al = (tot[k] for k in names_)
    pick = lambda g: (g[u"組"], g[u"断った組"], g[u"数"][u"型の行"][u"今年"][KN], g[u"数"][u"対応表の名"][u"科目"][u"今年"], g[u"数"][u"同じ行の中身(数)"][CONTENT4[0]])      # noqa: E731
    if pick(tr) != (2, 0, 26, 15, 5) or pick(ju) != (3, 1, 26, 15, 5) or pick(al) != (5, 1, 52, 30, 10):
        out.append(u"訓練・判定・全部の集計が手で数えた値と違う(番号 3 は訓練・4 は判定): %s %s %s" % (pick(tr), pick(ju), pick(al)))
    if "旗用の数" in ju[u"数"] or u"断った" in ju[u"数"] or u"番号" in ju[u"数"]:
        out.append(u"集計に旗用の数・断った・番号が足されている")
    # 判定の数(判定の組だけ。S1 + S2 + 断った組)
    j = ms.judged([e[2], e[3], e[3], e[4]])
    keys = list(j)
    want = ((8 + 1 + 1, 14 + 1 + 1, 62.5), (17 + 2 + 2, 24 + 2 + 2, 75.0), (10 + 1 + 1, 11 + 1 + 1, 92.3), (4 + 1 + 1, 10 + 1 + 1, 50.0), (4 + 1 + 1, 24 + 2 + 2, 21.4), (5 + 1 + 1, 24 + 2 + 2, 25.0), (2, 6, 33.3))
    for i, (n_, d_, p_) in enumerate(want):
        if not keys[i].startswith(u"XK0-%d " % (i + 1)) or tuple(j[keys[i]].values()) != (n_, d_, p_):
            out.append(u"判定の数 XK0-%d が手で数えた値と違う: %s" % (i + 1, dict(j[keys[i]])))
    for i, (n_, d_) in ((7, (1, 4)), (8, (2, 4)), (9, (1, 4))):
        if not keys[i].startswith(u"XK0-%d " % (i + 1)) or tuple(j[keys[i]].values()) != (n_, d_):
            out.append(u"判定の数 XK0-%d が手で数えた値と違う: %s" % (i + 1, dict(j[keys[i]])))
    if len(keys) != 10:
        out.append(u"判定の数が 10 本でない")
    # 当期・提出日にも同じ行(日)が在る作り物の組(S5)。XK0-3 の分子は前期とそれより前だけ
    j5 = ms.judged([entry_of(ms, 4, CUR5, PRIOR5)[0]])
    k5 = list(j5)
    want5 = [(1, 1, 100.0), (3, 3, 100.0), (1, 1, 100.0), (3, 3, 100.0), (3, 3, 100.0), (1, 3, 33.3), (0, 0, None), (0, 1), (1, 1), (0, 1)]
    if [tuple(j5[k].values()) for k in k5] != want5:
        out.append(u"S5 の判定の数が手で数えた値と違う: %s" % [tuple(j5[k].values()) for k in k5])
    # 断った組だけの判定(退化値): 数は全部 0・率は None・組は断った組を分母に入れる
    jr = ms.judged([entry_of(ms, 4, ms.Refuse(u"理由ア"), PRIOR1)[0], entry_of(ms, 5, CUR1, ms.Refuse(u"理由イ"))[0]])
    jk = list(jr)
    if [tuple(jr[k].values()) for k in jk[:7]] != [(0, 0, None)] * 7 or tuple(jr[jk[7]].values()) != (2, 2) or tuple(jr[jk[8]].values()) != (0, 2) or tuple(jr[jk[9]].values()) != (0, 2):
        out.append(u"断った組だけの判定の数が違う: %s" % [dict(jr[k]) for k in jk])
    return out


def _raises(exc, fn):
    try:
        fn()
    except exc:
        return True
    return False


def dumps_body(ms, ent):
    return ms.dumps(od((k, v) for k, v in ent.items() if k not in ms.NOT_SUMMED))


def flags_problems(ms=None):
    ms = ms or MS
    out = []
    s1 = lambda n: entry_of(ms, n, CUR1, PRIOR1)[0]                                                      # noqa: E731
    s2 = lambda n: entry_of(ms, n, CUR2, PRIOR2)[0]                                                      # noqa: E731
    r0 = lambda n: entry_of(ms, n, ms.Refuse(u"理由ア"), PRIOR1)[0]                                      # noqa: E731
    rp = lambda n: entry_of(ms, n, CUR1, ms.Refuse(u"理由イ"))[0]                                        # noqa: E731
    xm = lambda *rows: {u"書類": [{u"番号": n, u"型の行": od([(KN, a), (KT, b)])} for n, a, b in rows]}   # noqa: E731

    def fl(entries, x):
        return tuple(v[u"旗"] for v in ms.flags(entries, x).values())

    base = [s2(2), s1(4), s2(5)]
    xs = xm((2, 2, 0), (4, 24, 5), (5, 2, 0))
    if len(ms.flags(base, xs)) != 6 or fl(base, xs) != (False, False, False, False, False, False):
        out.append(u"何も立たない組の並びで旗が立つ: %s" % (fl(base, xs),))
    # 旗 1: 当期の行に同じ行(日)(63 組。数・文・訓練の組も)
    for k in (KN, KT):
        for n in (2, 4):
            b = [s2(2), s1(4)]
            for e in b:
                if e[u"番号"] == n:
                    e[u"同じ行(日)"][k][u"当期"] = 1
            if not fl(b, xm((2, 2, 0), (4, 24, 5)))[0]:
                out.append(u"旗 1 が %s・番号 %d の当期の同じ行で立たない" % (k, n))
    b = [s2(2), s1(4)]
    b[1][u"同じ行(日)"][KN][u"前期"] = 9
    if fl(b, xm((2, 2, 0), (4, 24, 5)))[0]:
        out.append(u"旗 1 が当期でない同じ行で立つ")
    if fl([entry_of(ms, 4, CUR5, PRIOR5)[0]], xm((4, 3, 0))) != (True, True, False, False, False, False):
        out.append(u"当期・提出日に同じ行(日)が在る組(S5)の旗が違う: %s" % (fl([entry_of(ms, 4, CUR5, PRIOR5)[0]], xm((4, 3, 0))),))
    # 旗 2: 判定の 60 組の全部で科目の名の持ち越しが 100%(断った組が在れば立たない・訓練の組は見ない・分析できなかった組は満たさない)
    only2 = [s2(1), s2(4), s2(5), s2(6)]
    if not fl(only2, xm((1, 2, 0), (4, 2, 0), (5, 2, 0), (6, 2, 0)))[1]:
        out.append(u"旗 2 が判定の組の全部が 100% で立たない")
    with_s1_train = [s1(1), s2(4), s2(5)]
    if not fl(with_s1_train, xm((1, 24, 5), (4, 2, 0), (5, 2, 0)))[1]:
        out.append(u"旗 2 が訓練の組(番号 1)を見ている")
    if fl([s2(4), s1(5)], xm((4, 2, 0), (5, 24, 5)))[1] or fl([s2(4), r0(5)], xm((4, 2, 0), (5, 0, 0)))[1] or fl([s2(4), rp(5)], xm((4, 2, 0), (5, 24, 5)))[1]:
        out.append(u"旗 2 が 100% でない組・断った組が在っても立つ")
    if fl([s2(1)], xm((1, 2, 0)))[1]:
        out.append(u"旗 2 が判定の組が 0 本のとき立つ")
    one_short = [s2(4), s2(5), s2(6)]
    one_short[1][u"対応表の名"][u"科目"][u"今年"] = 2
    one_short[1][u"対応表の名"][u"科目"][u"持ち越せる"] = 1
    if fl(one_short, xm((4, 2, 0), (5, 2, 0), (6, 2, 0)))[1]:
        out.append(u"旗 2 が名が 1 つだけ前の年に無い組が在って立つ(ほかは全部 100%。境の 1 つ手前)")
    zero_names = [s2(4)]
    zero_names[0][u"対応表の名"][u"科目"][u"今年"] = 0
    zero_names[0][u"対応表の名"][u"科目"][u"持ち越せる"] = 0
    if fl(zero_names, xm((4, 2, 0)))[1]:
        out.append(u"旗 2 が科目の名が 0 の組で立つ(名 0 は 100% と読まない)")
    # 旗 3: 同じ行(数)が判定の 60 組の合計で 0
    none_same = [entry_of(ms, 4, CUR1, EMPTY_P)[0], entry_of(ms, 5, CUR2, EMPTY_P)[0]]
    if not fl(none_same, xm((4, 24, 5), (5, 2, 0)))[2]:
        out.append(u"旗 3 が判定の組の同じ行(数)が 0 で立たない")
    if not fl([entry_of(ms, 1, CUR2, PRIOR2)[0], none_same[0]], xm((1, 2, 0), (4, 24, 5)))[2]:
        out.append(u"旗 3 が訓練の組の同じ行(数)を数えている(60 組だけを見る)")
    if fl([entry_of(ms, 4, CUR2, PRIOR2)[0], entry_of(ms, 5, CUR1, EMPTY_P)[0]], xm((4, 2, 0), (5, 24, 5)))[2]:
        out.append(u"旗 3 が 1 つでも同じ行(数)が在る判定の組で立つ")
    tf = entry_of(ms, 4, CUR1, EMPTY_P)[0]
    tf[u"同じ行(日)"][KT][u"前期"] = 3
    if not fl([tf], xm((4, 24, 5)))[2]:
        out.append(u"旗 3 が文の同じ行を数えている(数の行だけ)")
    # 旗 4: 枠が在る行が名が足りる行より多い組(63 組。数・文の別)
    for k in (KN, KT):
        for n in (2, 4):
            b = [s2(2), s1(4)]
            for e in b:
                if e[u"番号"] == n:
                    e[u"枠が在る行"][k][u"当期"] = e[u"名が足りる行"][k] + 1
            if not fl(b, xm((2, 2, 0), (4, 24, 5)))[3]:
                out.append(u"旗 4 が %s・番号 %d で立たない" % (k, n))
    b = [s2(2), s1(4)]
    b[1][u"枠が在る行"][KN][u"当期"] = b[1][u"名が足りる行"][KN] - sum(v for c, v in b[1][u"枠が在る行"][KN].items() if c != u"当期")
    if fl(b, xm((2, 2, 0), (4, 24, 5)))[3]:
        out.append(u"旗 4 が名が足りる行と同じ数(ちょうど)で立つ")
    b = [s2(2)]
    b[0][u"枠が在る行"][KN][u"当期"] = 1
    b[0][u"枠が在る行"][KT][u"当期"] = 0
    b[0][u"名が足りる行"][KN] = 0
    b[0][u"名が足りる行"][KT] = 5
    if not fl(b, xm((2, 2, 0)))[3]:
        out.append(u"旗 4 が数と文を合わせて比べている(数だけで多い)")
    # 旗 5: 断った組が 6 以上(判定の 60 組だけ)
    five = [r0(n) for n in range(4, 9)]
    six = [r0(n) for n in range(4, 10)]
    zeros = lambda es: xm(*[(e[u"番号"], 0, 0) for e in es])                                             # noqa: E731
    if fl(five, zeros(five))[4] or not fl(six, zeros(six))[4]:
        out.append(u"旗 5 が 6 の境で変わらない")
    train3 = [r0(1), r0(2), r0(3)] + five
    if fl(train3, zeros(train3))[4]:
        out.append(u"旗 5 が訓練の組の断りを数えている")
    mixed = [r0(4), r0(5), r0(6), rp(7), rp(8), rp(9)]
    if not fl(mixed, xm((4, 0, 0), (5, 0, 0), (6, 0, 0), (7, 24, 5), (8, 24, 5), (9, 24, 5)))[4]:
        out.append(u"旗 5 が今年・前の年の両方の断りを数えていない")
    # 旗 6: 便 XM0 の記録の型の行の数(数・文)と違う組(63 組。番号で照らす。分析できなかった組は 0)
    ok = [s2(1), s1(4)]
    for nm_, rows_ in ((u"数 1 つ違う", ((1, 2, 0), (4, 25, 5))), (u"文 1 つ違う", ((1, 2, 0), (4, 24, 4))), (u"訓練の組が違う", ((1, 3, 0), (4, 24, 5))), (u"数と文が入れ替わっている", ((1, 0, 2), (4, 24, 5)))):
        if not fl(ok, xm(*rows_))[5]:
            out.append(u"旗 6 が立たない(%s)" % nm_)
    if fl([r0(4)], xm((4, 0, 0)))[5] or not fl([r0(4)], xm((4, 24, 5)))[5]:
        out.append(u"旗 6 が今年の側を分析できなかった組を 0 と照らしていない")
    if fl([rp(4)], xm((4, 24, 5)))[5] or not fl([rp(4)], xm((4, 0, 0)))[5]:
        out.append(u"旗 6 が前の年の側が断った組の今年の側の型の行(旗用の数)と照らしていない")
    if not stops(ms, ms.flags, ok, xm((1, 2, 0))):
        out.append(u"便 XM0 の記録に同じ番号が無いのに旗 6 が止まらない")
    if fl(ok, xm((1, 2, 0), (4, 24, 5), (9, 9, 9)))[5]:
        out.append(u"便 XM0 の記録の余分な番号で旗 6 が立つ")
    return out


# ======================================================================== 5. 記録・e2e
STEMS = [u"D%03d" % i for i in range(1, 68)]
NOS = [n for n in range(1, 68) if n not in (10, 22, 40, 66)]          # 除いた 4 本。組は 63 組(番号 3 以下 = 3 組・4 以上 = 60 組)
S1_AT, CUR_REFUSE_AT, PRIOR_REFUSE_AT = (3, 4, 30), 5, 6


def fake_pairs():
    return [(n, STEMS[n - 1], u"cur%d" % n, u"P%03d" % n, u"prv%d" % n, u"E9%04d" % n) for n in NOS]


def fake_table(ms):
    t = {}
    for n in NOS:
        if n == CUR_REFUSE_AT:
            t[u"cur%d" % n], t[u"prv%d" % n] = ms.Refuse(u"理由ア"), PRIOR1
        elif n == PRIOR_REFUSE_AT:
            t[u"cur%d" % n], t[u"prv%d" % n] = CUR1, ms.Refuse(u"理由イ")
        elif n in S1_AT:
            t[u"cur%d" % n], t[u"prv%d" % n] = CUR1, PRIOR1
        else:
            t[u"cur%d" % n], t[u"prv%d" % n] = CUR2, PRIOR2
    return t


def fake_xm0(rows=None):
    rows = rows or dict((n, (0, 0) if n == CUR_REFUSE_AT else (24, 5) if n in S1_AT or n == PRIOR_REFUSE_AT else (2, 0)) for n in NOS)
    sha = hashlib.sha256(u"\n".join(sorted(STEMS)).encode("utf-8")).hexdigest()
    return {u"材料": {u"書類の file 名の並びの sha256": sha}, u"書類": [{u"番号": n, u"型の行": od([(KN, a), (KT, b)])} for n, (a, b) in sorted(rows.items())]}


def fake_docs():
    return [(s, u"path%d" % i, []) for i, s in enumerate(STEMS, 1)]


def build_fake(ms, xm0=None, table=None, analyzer=None):
    an, calls = (analyzer, []) if analyzer is not None else fake_analyzer(table or fake_table(ms))
    rec, secret = ms.build_record(None, None, 67, 63, xm0 or fake_xm0(), u"x" * 64, fake_pairs(), fake_docs(), an)
    return rec, secret, calls


def build_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out = []
    rec, secret, calls = build_fake(ms)
    mat = rec[u"材料"]
    want_mat = [(u"今年の側の書類の本数", 67), (u"組の数", 63), (u"訓練の組の数", 3), (u"判定の組の数", 60), (u"除いた今年の書類の数", 4), (u"便 XM0 の記録の sha256", u"x" * 64)]
    for k, v in want_mat:
        if mat[k] != v:
            out.append(u"材料 %s が違う: %s" % (k, mat[k]))
    if mat[u"今年の側の書類の file 名の並びの sha256"] != hashlib.sha256(u"\n".join(STEMS).encode("utf-8")).hexdigest():
        out.append(u"今年の側の並びの sha256 が違う")
    if mat[u"前の年の側の組の相手の file 名の並びの sha256"] != hashlib.sha256(u"\n".join(u"P%03d" % n for n in NOS).encode("utf-8")).hexdigest():
        out.append(u"前の年の側の組の相手の並びの sha256 が違う(今年の側の番号の順)")
    if rec[u"この script の sha256"] != sha_of(SCRIPT_REL) or rec[u"封の commit"] != SEAL_COMMIT_SHORT or rec[u"seal"] != SEAL_REL:
        out.append(u"記録の script の sha256・封の commit・封の path が違う")
    if rec[u"限界"] != list(ms.LIMITS) or len(rec[u"限界"]) != 6:
        out.append(u"記録の限界が 6 行でない")
    if [d[u"番号"] for d in rec[u"書類"]] != NOS:
        out.append(u"書類の番号が違う(除いた書類の番号は飛ぶ)")
    want_calls = []
    for n in NOS:
        want_calls.append(u"cur%d" % n)
        if n != CUR_REFUSE_AT:
            want_calls.append(u"prv%d" % n)
    if calls != want_calls:
        out.append(u"分析の呼び方が(今年 → 前の年。今年が断れば前の年は呼ばない)の 63 組の並びでない")
    tr, ju, al = (rec[u"集計"][k] for k in (u"訓練の 3 組", u"判定の 60 組", u"全部の 63 組"))
    z = lambda g: g[u"数"]                                                                                    # noqa: E731
    got = (ju[u"組"], ju[u"断った組"], z(ju)[u"対応表の名"][u"科目"][u"今年"], z(ju)[u"対応表の名"][u"科目"][u"持ち越せる"], z(ju)[u"型の行"][u"今年"][KN], z(ju)[u"名が足りる行"][KN],
           z(ju)[u"同じ行の中身(数)"][CONTENT4[0]], sum(z(ju)[u"枠が在る行"][KN].values()))
    if got != (60, 2, 84, 72, 160, 146, 64, 66):
        out.append(u"判定の 60 組の合計が手で数えた値と違う: %s" % (got,))
    got = (tr[u"組"], tr[u"断った組"], z(tr)[u"対応表の名"][u"科目"][u"今年"], z(tr)[u"型の行"][u"今年"][KN], al[u"組"], z(al)[u"対応表の名"][u"科目"][u"今年"], z(al)[u"型の行"][u"今年"][KN])
    if got != (3, 0, 16, 28, 63, 100, 188):
        out.append(u"訓練の 3 組・全部の 63 組の合計が手で数えた値と違う: %s" % (got,))
    pv = [v for k, v in rec.items() if k.startswith(u"予測の判定に要る数")][0]
    want = (u"XK0-1", (72, 84, 85.7)), (u"XK0-2", (146, 160, 91.3)), (u"XK0-3", (76, 78, 97.4)), (u"XK0-4", (64, 76, 84.2)), (u"XK0-5", (64, 160, 40.0)), (u"XK0-6", (66, 160, 41.3)), \
        (u"XK0-7", (4, 12, 33.3)), (u"XK0-8", (2, 60)), (u"XK0-9", (56, 60)), (u"XK0-10", (2, 60))
    for key, w in want:
        hit = [v for k, v in pv.items() if k.startswith(key + u" ")]
        if len(hit) != 1 or tuple(hit[0].values()) != w:
            out.append(u"判定の数 %s が手で数えた値(判定の 60 組だけ)と違う: %s" % (key, [dict(h) for h in hit]))
    fv = list(rec[u"先に自分の欠陥を疑う旗"].values())
    if [f[u"旗"] for f in fv] != [False] * 6 or fv[2][u"同じ行(数)"] != 76 or fv[4][u"断った組"] != 2 or fv[1][u"100% の組"] != 56 or fv[5][u"違う組"] != 0:
        out.append(u"旗が違う: %s" % [dict(f) for f in fv])
    # 便 XM0 の記録の 1 組が違えば旗 6 が立つ(止めない)
    bad_rows = dict((n, (0, 0) if n == CUR_REFUSE_AT else (24, 5) if n in S1_AT or n == PRIOR_REFUSE_AT else (2, 0)) for n in NOS)
    bad_rows[4] = (23, 5)
    r2, _s2, _c2 = build_fake(ms, xm0=fake_xm0(bad_rows))
    f2 = list(r2[u"先に自分の欠陥を疑う旗"].values())
    if not f2[5][u"旗"] or f2[5][u"違う組"] != 1 or any(f[u"旗"] for f in f2[:5]):
        out.append(u"便 XM0 の記録の 1 組が違うときの旗 6 が違う: %s" % [dict(f) for f in f2])
    bad_rows[4] = (24, 5)
    bad_rows[2] = (3, 0)
    r3, _s3, _c3 = build_fake(ms, xm0=fake_xm0(bad_rows))
    f3 = list(r3[u"先に自分の欠陥を疑う旗"].values())
    if not f3[5][u"旗"] or f3[5][u"違う組"] != 1:
        out.append(u"訓練の組(番号 2)で便 XM0 の記録と違うとき、旗 6 が立たない(63 組を見る)")
    # 止まる条件
    base_t = fake_table(ms)
    x = fake_xm0()
    x[u"材料"][u"書類の file 名の並びの sha256"] = u"0" * 64
    if not stops(ms, build_fake, ms, x):
        out.append(u"便 XM0 の記録の並びが今年の側の並びと違うのに止まらない")
    if not stops(ms, ms.build_record, None, None, 67, 63, None, u"x", fake_pairs(), fake_docs(), fake_analyzer(base_t)[0]):
        out.append(u"便 XM0 の記録が無いのに止まらない")
    if not stops(ms, ms.build_record, None, None, 67, 63, fake_xm0(), u"x", fake_pairs()[1:], fake_docs(), fake_analyzer(base_t)[0]):
        out.append(u"組の数が 63 でないのに止まらない")
    # 置き場から組を作る呼び方(前の便の make_pairs。module の実体に差して確かめる)
    seen = []
    saved_mp = ms.Y.make_pairs
    ms.Y.make_pairs = lambda *a: (seen.append(a), (fake_docs(), fake_pairs(), 4))[1]
    try:
        r4, _s4 = ms.build_record(u"DOCS", u"PRIOR", 67, 63, fake_xm0(), u"x", None, None, fake_analyzer(fake_table(ms))[0])
        r5, _s5 = ms.build_record(None, None, 67, 63, fake_xm0(), u"x", None, None, fake_analyzer(fake_table(ms))[0])
    finally:
        ms.Y.make_pairs = saved_mp
    if seen != [(u"DOCS", u"PRIOR", 67, 63), (ms.DOCS_DIR, ms.PRIOR_DIR, 67, 63)] or r4[u"材料"][u"組の数"] != 63 or r4[u"材料"][u"除いた今年の書類の数"] != 4:
        out.append(u"置き場から組を作る呼び方が違う(置き場・本数・組の数を前の便の make_pairs に渡す): %s" % (seen,))
    # secret の配線
    labels, elems, ids, ecodes, heads = secret
    if sorted(ids) != sorted(STEMS + [u"P%03d" % n for n in NOS]):
        out.append(u"secret の docID が今年の側の 67 本と前の年の側の組の相手の stem でない")
    if not (set([u"E90001", u"E90067"]) <= set(ecodes)) or not (set([u"Item1", u"NewC", u"xa_cor", u"MbNew"]) <= set(elems)):
        out.append(u"secret の EDINET コード・名・接頭辞の配線が違う")
    text = ms.record_text(rec, secret)
    for leak in STEMS[:3] + [u"E90001", u"Item1", u"xa_cor", u"NewC", u"xb:", u"xf:", u"cur4", u"prv4", u"2030", u"2031", u"通貨"]:
        if leak in text:
            out.append(u"記録に材料の字が在る: %s" % leak)
    return out


def e2e_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out = []
    with Temp() as d:
        xp = os.path.join(d, "xm0.json")
        with io.open(xp, "w", encoding="utf-8") as fh:
            fh.write(ms.dumps(fake_xm0()))
        an, calls = fake_analyzer(fake_table(ms))
        rec_path = os.path.join(d, "rec", "r.json")
        lines = []
        before = sha_or_none(RECORD_REL)
        kw = dict(xm0_path=xp, analyzer=an, pairs=fake_pairs(), docs_list=fake_docs())
        ms.run(root=d, out=rec_path, say=lines.append, **kw)
        flag_lines = [ln for ln in lines if ln.startswith(u"旗 ")]
        if not os.path.isfile(rec_path) or lines[-1] != u"-> r.json(組 63)" or len(flag_lines) != 6 or any(not ln.endswith(u": 立たない") for ln in flag_lines) or sha_or_none(RECORD_REL) != before:
            out.append(u"本番が記録を書かない・旗 6 つを表示しない・本物の記録を触った: %s" % lines[-3:])
        if not stops(ms, ms.run, root=d, out=rec_path, say=lambda *a: None, **kw):
            out.append(u"記録が既に在るのに run が止まらない")
        ms.check(root=d, rec_path=rec_path, xm0_path=xp, say=lambda *a: None)
        text = io.open(rec_path, encoding="utf-8").read()
        # 組ごとの数を変えた記録・集計だけを変えた記録・旗だけを変えた記録・判定の数だけを変えた記録で --check が止まる
        t60 = u'"組": 60'
        cases = ((u"組ごとの数", text.replace(u'"今年": 14,', u'"今年": 15,', 1)), (u"集計の組", text.replace(t60, u'"組": 61', 1)), (u"旗", text.replace(u'"旗": false', u'"旗": true', 1)),
                 (u"判定の数", text.replace(u'"分母": 60', u'"分母": 59', 1)), (u"限界", text.replace(ms.LIMITS[0], ms.LIMITS[1], 1)), (u"断った組の数", text.replace(u'"断った理由": "理由ア"', u'"断った理由": ""', 1)))
        for what, bad in cases:
            bp = os.path.join(d, "bad.json")
            with io.open(bp, "w", encoding="utf-8") as fh:
                fh.write(bad)
            if bad == text or not stops(ms, ms.check, root=d, rec_path=bp, xm0_path=xp, say=lambda *a: None):
                out.append(u"記録の %s を変えても --check が止まらない" % what)
        if not stops(ms, ms.check, root=d, rec_path=os.path.join(d, "none.json"), xm0_path=xp, say=lambda *a: None):
            out.append(u"記録が無いのに --check が止まらない")
        if not stops(ms, ms.check, root=d, rec_path=rec_path, xm0_path=os.path.join(d, "none.json"), say=lambda *a: None):
            out.append(u"便 XM0 の記録が無いのに --check が止まらない")
        x2 = fake_xm0(dict((n, (1, 1)) for n in NOS))
        with io.open(xp, "w", encoding="utf-8") as fh:
            fh.write(ms.dumps(x2))
        if not stops(ms, ms.check, root=d, rec_path=rec_path, xm0_path=xp, say=lambda *a: None):
            out.append(u"便 XM0 の記録の数が違えば旗 6 が変わるのに --check が止まらない")
        if not stops(ms, ms.run, root=d, out=os.path.join(d, "rec", "r2.json"), say=lambda *a: None, xm0_path=os.path.join(d, "none.json"), analyzer=an, pairs=fake_pairs(), docs_list=fake_docs()):
            out.append(u"便 XM0 の記録が無いのに run が止まらない")
        # 旗が立つ記録も、旗を表示するだけで止めない
        lines2 = []
        with io.open(xp, "w", encoding="utf-8") as fh:
            fh.write(ms.dumps(x2))
        ms.run(root=d, out=os.path.join(d, "rec", "r3.json"), say=lines2.append, xm0_path=xp, analyzer=fake_analyzer(fake_table(ms))[0], pairs=fake_pairs(), docs_list=fake_docs())
        if not [ln for ln in lines2 if ln.startswith(u"旗 6")][0].endswith(u": 立った") or lines2[-1] != u"-> r3.json(組 63)":
            out.append(u"旗が立った記録を止める(か、立ったと表示しない)")
    return out


def dev_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out = []
    an, calls = fake_analyzer(fake_table(ms))
    lines = []
    writes = []
    saved = (ms.write_record, ms.write_exclusive, ms.Y.make_pairs)
    ms.write_record = lambda *a, **k: writes.append(a)                 # 変異が記録を書いても、本物の path へは書かせない(この関数の中は全部)
    ms.write_exclusive = lambda *a, **k: writes.append(a)
    before = sha_or_none(RECORD_REL)
    try:
        ents = ms.dev_run(None, None, say=lines.append, analyzer=an, pairs=fake_pairs())
        if writes or sha_or_none(RECORD_REL) != before:
            out.append(u"--dev が記録を書く")
        if [e[u"番号"] for e in ents] != [1, 2, 3] or calls != [u"cur1", u"prv1", u"cur2", u"prv2", u"cur3", u"prv3"]:
            out.append(u"--dev が番号 1・2・3 の 3 組だけを分析していない(番号 4 以上は分析しない): %s" % calls)
        shown = json.loads(lines[0], object_pairs_hook=od)
        if shown[u"組"] != 3 or shown[u"数の行"][u"今年"] != 24 + 2 + 2 or shown[u"科目"][u"今年"] != 14 + 1 + 1 or shown[u"数の行"][u"同じ行の中身"][CONTENT4[0]] != 4 + 1 + 1:
            out.append(u"--dev の表示が 3 組の合計でない: %s" % shown[u"数の行"])
        seen = []
        ms.Y.make_pairs = lambda *a: (seen.append(a), (fake_docs(), fake_pairs(), 4))[1]
        an2, calls2 = fake_analyzer(fake_table(ms))
        ms.dev_run(None, None, say=lambda *a: None, analyzer=an2)
        ms.dev_run(u"DOCS", u"PRIOR", say=lambda *a: None, analyzer=an2)
        if seen != [(ms.DOCS_DIR, ms.PRIOR_DIR), (u"DOCS", u"PRIOR")] or calls2 != [u"cur1", u"prv1", u"cur2", u"prv2", u"cur3", u"prv3"] * 2:
            out.append(u"--dev が置き場から組を作る呼び方・番号 1〜3 だけの分析が違う: %s" % (seen,))
        if writes:
            out.append(u"--dev が記録を書く(置き場から組を作る道)")
    finally:
        ms.write_record, ms.write_exclusive, ms.Y.make_pairs = saved
    return out


def clean_problems(ms=None):
    ms = ms or MS
    out = []
    secret = (set(), set([u"Item1", u"xa_cor"]), ["S1ZZ0001", "S1ZP0001"], set(["E99001"]), set())
    for what, bad in ((u"docID の形", od([(u"x", u"S1ZZ9999")])), (u"EDINET コードの形", od([(u"x", u"E99991")])), (u"日付の形", od([(u"x", D(2030, 3, 31))])),
                      (u"禁止の欄", od([(u"docid", 1)])), (u"禁止の欄(名)", od([(u"name", 1)])), (u"今年の側の docID", od([(u"x", u"a S1ZZ0001 b")])),
                      (u"前の年の側の docID", od([(u"x", u"a S1ZP0001 b")])), (u"コード", od([(u"x", u"a E99001 b")])), (u"要素の局所名", od([(u"x", u"a Item1 b")])),
                      (u"接頭辞の字", od([(u"x", u"a xa_cor b")]))):
        if not stops(ms, ms.record_text, bad, secret):
            out.append(u"記録の検査が止めない: %s" % what)
    if stops(ms, ms.record_text, od([(u"a", 1), (u"seal", ms.SEAL_REL), (u"b", u"_cor で終わる")]), secret):
        out.append(u"封の path の中の日付・封に在る _cor の字で止まる(書いてよい)")
    with Temp() as d:
        p = os.path.join(d, "r.json")
        good = od([(u"x", 1)])
        ms.write_record(p, good)
        if not stops(ms, ms.write_record, p, good):
            out.append(u"記録が既に在るのに書き直せる")
        q = os.path.join(d, "q.json")
        orig = ms.write_exclusive
        ms.write_exclusive = lambda path, data: orig(path, data + u" {}".format(D(2030, 3, 31)).encode("utf-8"))
        try:
            stopped = stops(ms, ms.write_record, q, good)
        finally:
            ms.write_exclusive = orig
        if not stopped or os.path.exists(q):
            out.append(u"書いた後の検査が止めない(か file を消さない)")
        r = os.path.join(d, "bad.json")
        wrote = []
        orig = ms.write_exclusive
        ms.write_exclusive = lambda path, data: wrote.append(path)
        try:
            stopped = stops(ms, ms.write_record, r, od([(u"x", u"S1ZZ0001")]), secret)
        finally:
            ms.write_exclusive = orig
        if not stopped or wrote or os.path.exists(r):
            out.append(u"書く前の検査が止めない(書き出しに入る・file を作る)")
    return out


def entry_shape_problems(ms=None):
    u"""記録の導ける関係(``entry_problems``)が、足し算の合わない組・断った組の 0 でない数を止める。"""
    ms = ms or MS
    out = []
    good = entry_of(ms, 4, CUR1, PRIOR1)[0]
    if ms.entry_problems(good) != u"" or ms.entry_problems(entry_of(ms, 5, ms.Refuse(u"理由ア"), PRIOR1)[0]) != u"" or ms.entry_problems(entry_of(ms, 6, CUR2, PRIOR2)[0]) != u"":
        out.append(u"正しい組を止める")
    json_copy = lambda e: json.loads(json.dumps(e), object_pairs_hook=od)                                  # noqa: E731
    muts = []

    def add(what, fn):
        e = json_copy(good)
        fn(e)
        muts.append((what, e))

    add(u"持ち越せる + 新しい ≠ 今年", lambda e: e[u"対応表の名"][u"科目"].__setitem__(u"持ち越せる", 9))
    add(u"新しい の _cor の足し算", lambda e: e[u"対応表の名"][u"軸"].__setitem__(u"新しい・_cor で終わらない", 1))
    add(u"期の区分の合計 ≠ 型の行", lambda e: e[u"今年の行の期の区分"][KN].__setitem__(u"当期", 11))
    add(u"名が足りる行 > 型の行", lambda e: e[u"名が足りる行"].__setitem__(KT, 6))
    add(u"枠が在る行 > 今年の行(期の区分ごと)", lambda e: e[u"枠が在る行"][KT].__setitem__(u"提出日", 1))
    add(u"同じ行(日)が名が足りる行より多い", lambda e: (e[u"名が足りる行"].__setitem__(KT, 2), e[u"同じ行(日)"][KT].__setitem__(u"前期", 1), e[u"同じ行(日)"][KT].__setitem__(u"それより前", 1), e[u"同じ行(日)"][KT].__setitem__(u"当期", 1)))
    add(u"逆向き 日 ≠ 同じ行(日)", lambda e: e[u"逆向き"][KN].__setitem__(u"同じ鍵(日)が今年に在る", 9))
    add(u"逆向き 要らなくなった枠", lambda e: e[u"逆向き"][KN].__setitem__(u"今年、要らなくなった枠", 7))
    add(u"逆向き 前の年の行", lambda e: e[u"逆向き"][KT].__setitem__(u"前の年の行", 3))
    add(u"中身の 4 つの合計 ≠ 同じ行(数)", lambda e: e[u"同じ行の中身(数)"].__setitem__(CONTENT4[0], 5))
    add(u"型の外の fact > 対象の fact", lambda e: e[u"型の外の fact"][u"今年"][u"合計"].__setitem__(KT, 9))
    add(u"理由ごと > 合計", lambda e: e[u"型の外の fact"][u"今年"][u"理由ごと"][u"a"].__setitem__(KN, 3))
    add(u"型の行 > 型に入った fact", lambda e: e[u"型の行"][u"今年"].__setitem__(KN, 25))
    add(u"旗用の数 ≠ 型の行", lambda e: e[u"旗用の数"][u"今年の側の型の行"].__setitem__(KN, 23))
    add(u"断った 欄", lambda e: e.__setitem__(u"断った年", u"今年"))
    add(u"断った年の字", lambda e: (e.__setitem__(u"断った", True), e.__setitem__(u"断った年", u"両方"), e.__setitem__(u"断った理由", u"ア")))
    add(u"断った組の数が 0 でない", lambda e: (e.__setitem__(u"断った", True), e.__setitem__(u"断った年", u"今年"), e.__setitem__(u"断った理由", u"ア")))
    add(u"欄の並び", lambda e: e.move_to_end(u"断った"))
    for what, e in muts:
        if ms.entry_problems(e) == u"":
            out.append(u"組の導ける関係の違いを止めない: %s" % what)
    return out


# ======================================================================== 6. 配線
STDLIB_OK = ("__future__", "argparse", "collections", "hashlib", "importlib", "io", "json", "os", "re", "sys")
NETWORK_MODULES = ("http", "socket", "ssl", "urllib", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx", "subprocess", "tempfile", "shutil", "glob", "zipfile")
CALLED = (("Y", "make_pairs"), ("M", "analyze"), ("M", "code_maps"), ("M", "period_name"), ("M", "sum_nested"), ("M", "check_clean"), ("W", "order_sha256"))
CHAIN_CALLED = ("peel_tables", "load_package")
NEVER_CALLED = ("derive_folder", "process_doc", "run_facts", "exec_make", "build_definitions", "write_type_folder")
NOT_COPIED = ("analyze", "code_maps", "period_name", "make_pairs", "sum_nested", "order_sha256", "select_docs", "peel_tables", "load_package")
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS")
SIBLING_NAMES = ("_xk0_input_type_2026_11_22", "_xk0_prior_year_draft_2026_11_22")
HARNESS_WORDS = ("apply_edits(", "inject_with_profile(", "run_doc(", "mutate(", "IJ.select(", "inject(", "inject_doc(", "verify_document(", "verify_external(")


def import_problems(src=None):
    u"""script の import は標準ライブラリと importlib だけ。前の便の関数は ``Y.``・``M.``・``W.`` から呼び写さない。``derive_folder``・``process_doc`` を呼ばない。"""
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
            if top in NETWORK_MODULES:
                out.append(u"許さない module を import している: %s" % nm)
            elif top not in STDLIB_OK:
                out.append(u"許す一覧に無い module(engine を含む): %s" % nm)
    attrs = [(n.value.id, n.attr) for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)]
    all_attr = set(n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute))
    if ("os", "environ") in attrs or ("os", "getenv") in attrs:
        out.append(u"環境変数を読んでいる")
    called = set((n.func.value.id, n.func.attr) for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name))
    for pair in CALLED:
        if pair not in called:
            out.append(u"%s.%s を呼んでいない" % pair)
    called_any = set(n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute))
    for fn in CHAIN_CALLED:
        if fn not in called_any:
            out.append(u"%s を呼んでいない(zip → 型の分析)" % fn)
    for fn in NEVER_CALLED:
        if fn in all_attr:
            out.append(u"呼んではいけない %s を使っている" % fn)
    funcs = dict((n.name, n) for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    for fn in NOT_COPIED:
        if fn in funcs:
            out.append(u"前の便の %s を script が自分で定義している(写している)" % fn)
    doc = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant):
            doc.add(id(n.body[0].value))
    consts = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc:
            v = n.value
            if u".env" in v or u"dotenv" in v or u"API_KEY" in v:
                out.append(u"鍵・.env の字が在る")
            if any(s in v for s in HARNESS_WORDS):
                out.append(u"注入の仕掛けの規準の字が在る: %s" % v)
    for nm in SIBLING_NAMES:
        if nm not in consts:
            out.append(u"前の便の script を読む名が一意の名(%s)でない" % nm)
    for n in funcs:
        if any(w.rstrip(u"(").split(u".")[-1] == n for w in HARNESS_WORDS):
            out.append(u"関数の名が注入の仕掛けの規準の字に当たる: %s" % n)
    return out


def wiring_problems(ms=None):
    u"""``analyze_side`` が zip → 読み込み → 表を剥がす → 型の分析の順に前の便の関数を呼び、戻り値を使う(module の実体に差して確かめる)。"""
    ms = ms or MS
    out = []
    M_, P_, B_ = ms.M, ms.M.P, ms.M.B
    saved = (B_.load_package, P_.peel_tables, M_.analyze)
    log = []
    try:
        B_.load_package = lambda p: (log.append(("load", p)), u"ENTRIES")[1]
        P_.peel_tables = lambda e: (log.append(("peel", e)), (u"FILES", u"N", u"T"))[1]
        M_.analyze = lambda f: (log.append(("analyze", f)), u"RESULT")[1]
        got = ms.analyze_side(u"pathX")
    finally:
        B_.load_package, P_.peel_tables, M_.analyze = saved
    if got != u"RESULT" or log != [("load", u"pathX"), ("peel", u"ENTRIES"), ("analyze", u"FILES")]:
        out.append(u"analyze_side の呼び方・戻り値が違う: %s %s" % (got, log))
    try:
        B_.load_package = lambda p: []
        P_.peel_tables = lambda e: (_ for _ in ()).throw(ms.Refuse(u"理由ウ"))
        if not _raises(ms.Refuse, lambda: ms.analyze_side(u"p")):
            out.append(u"analyze_side が断りをそのまま投げない")
    finally:
        B_.load_package, P_.peel_tables, M_.analyze = saved
    if ms.Refuse is not ms.M.Refuse or ms.Stop is not ms.W.Stop:
        out.append(u"Refuse・Stop の型が前の便と同じ object でない")
    # 前の便の make_pairs は Y の関数(置き場の既定は Y と同じ)
    if ms.DOCS_DIR != ms.Y.DOCS_DIR or ms.PRIOR_DIR != ms.Y.PRIOR_DIR or ms.PAIRS_WANT != ms.Y.PAIRS_WANT:
        out.append(u"置き場・組の数が便 XY0 の字と違う")
    return out


def reserved_problems(rel=GATE_REL, base=ROOT):
    out = []
    with open(os.path.join(base, rel), encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    for n, line in enumerate(lines, 1):
        if any(line.startswith(p) for p in RESERVED_PREFIXES):
            out.append(u"%s:%d" % (rel, n))
    return out


ORDER_SNIPPET = (
    "import importlib.util, os, sys\n"
    "root = sys.argv[1]\n"
    "files = {'xm0': ('_gate_order_xm0', 'measure/xbrl_input_type_2026-11-22.py'), 'xy0': ('_gate_order_xy0', 'measure/xbrl_prior_year_draft_2026-11-22.py'), 'xk0': ('_gate_order_xk0', 'measure/xbrl_type_carryover_2026-11-22.py')}\n"
    "mods = {}\n"
    "for key in sys.argv[2:]:\n"
    "    name, rel = files[key]\n"
    "    spec = importlib.util.spec_from_file_location(name, os.path.join(root, rel))\n"
    "    m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m); mods[key] = m\n"
    "k = mods['xk0']\n"
    "assert k.M.P is sys.modules['_xm0_pack_build_2026_11_22'] or k.M.P is mods['xm0'].P\n"
    "assert k.Y.make_pairs and k.M.analyze and k.W is k.M.W\n"
    "print('ok')\n")


def order_import_problems():
    u"""前の便の script と自分を並べて読む順を入れ替えても、動く(sys.modules の名を上書きして赤にならない)。別の process で確かめる。"""
    out = []
    for order in (("xm0", "xy0", "xk0"), ("xk0", "xy0", "xm0"), ("xy0", "xk0", "xm0"), ("xk0",)):
        rc = subprocess.run([sys.executable, "-I", "-c", ORDER_SNIPPET, ROOT] + list(order), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, cwd=ROOT, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        if rc.returncode != 0 or rc.stdout.strip() != "ok":
            out.append(u"読む順 %s で動かない: %s" % (u"→".join(order), rc.stderr.strip().splitlines()[-1:] or rc.stdout))
    return out


# ======================================================================== 7. 記録の導き直し(--check)
def reseal(ms, rec, xm0):
    u"""記録の書類を書き換えたあと、集計・判定の数・旗を書類から導き直して揃える(``--check`` の「組ごとの数の関係」の検査だけが拾える形にする)。"""
    docs = rec[u"書類"]
    rec[u"集計"] = ms.totals_of(docs)
    key = [k for k in rec if k.startswith(u"予測の判定に要る数")][0]
    rec[key] = ms.judged([d for d in docs if d[u"番号"] > ms.SEEN_MAX_NO])
    rec[u"先に自分の欠陥を疑う旗"] = ms.flags(docs, xm0)
    return rec


def verify_problems(ms=None):
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out = []
    rec, _secret, _calls = build_fake(ms)
    xm0 = fake_xm0()
    rec = json.loads(json.dumps(rec), object_pairs_hook=od)
    if stops(ms, ms.verify_record, json.loads(json.dumps(reseal(ms, rec, xm0)), object_pairs_hook=od), xm0, None):
        out.append(u"導き直しだけをした記録(何も変えていない)を止める")

    def tampered(fn):
        r = json.loads(json.dumps(rec), object_pairs_hook=od)
        fn(r)
        return reseal(ms, r, xm0) if r[u"書類"] and all(isinstance(d.get(u"番号"), int) for d in r[u"書類"]) else r

    def swap_two(r):
        r[u"書類"][6], r[u"書類"][7] = r[u"書類"][7], r[u"書類"][6]

    def dup_no(r):
        r[u"書類"][7][u"番号"] = r[u"書類"][6][u"番号"]

    cases = (
        (u"持ち越せる + 新しい ≠ 今年(判定の組)", lambda r: r[u"書類"][20][u"対応表の名"][u"科目"].__setitem__(u"持ち越せる", 0)),
        (u"断った組に数が在る", lambda r: r[u"書類"][[d[u"番号"] for d in r[u"書類"]].index(CUR_REFUSE_AT)][u"同じ行の中身(数)"].__setitem__(CONTENT4[0], 1)),
        (u"逆向きの数(訓練の組)", lambda r: r[u"書類"][0][u"逆向き"][KN].__setitem__(u"同じ鍵(日)が今年に在る", 5)),
        (u"組の並びが昇順でない", swap_two), (u"組の番号が重なる", dup_no), (u"組が 62", lambda r: r[u"書類"].pop()),
        (u"材料の訓練の組の数", lambda r: r[u"材料"].__setitem__(u"訓練の組の数", 4)), (u"材料の判定の組の数", lambda r: r[u"材料"].__setitem__(u"判定の組の数", 59)),
        (u"組が 62 で材料の判定の組の数も 59", lambda r: (r[u"書類"].pop(), r[u"材料"].__setitem__(u"判定の組の数", 59))),
        (u"限界", lambda r: r.__setitem__(u"限界", r[u"限界"][:5])), (u"材料の組の数", lambda r: r[u"材料"].__setitem__(u"組の数", 62)))
    for what, fn in cases:
        if not stops(ms, ms.verify_record, tampered(fn), xm0, None):
            out.append(u"記録の %s の違いを --check が止めない(集計・判定の数・旗は導き直して揃えてある)" % what)
    for what, fn in ((u"集計", lambda r: r[u"集計"][u"判定の 60 組"].__setitem__(u"断った組", 9)), (u"旗", lambda r: r[u"先に自分の欠陥を疑う旗"][list(r[u"先に自分の欠陥を疑う旗"])[0]].__setitem__(u"旗", True))):
        r = json.loads(json.dumps(rec), object_pairs_hook=od)
        fn(r)
        if not stops(ms, ms.verify_record, r, xm0, None):
            out.append(u"記録の %s だけを変えても --check が止めない" % what)
    r = json.loads(json.dumps(rec), object_pairs_hook=od)
    key = [k for k in r if k.startswith(u"予測の判定に要る数")][0]
    list(r[key].values())[0][u"数"] += 1
    if not stops(ms, ms.verify_record, r, xm0, None):
        out.append(u"記録の判定の数だけを変えても --check が止めない")
    # 禁止のもの(日付・禁止の欄)は、組ごとの数の関係が全部合っていても止まる
    r = json.loads(json.dumps(rec), object_pairs_hook=od)
    r[u"step"] = r[u"step"] + u" " + D(2030, 3, 31)
    if not stops(ms, ms.verify_record, r, xm0, None):
        out.append(u"記録に日付の形の字が在るのに --check が止めない")
    r = json.loads(json.dumps(rec), object_pairs_hook=od)
    r[u"docid"] = 1
    if not stops(ms, ms.verify_record, r, xm0, None):
        out.append(u"記録に禁止の欄が在るのに --check が止めない")
    r = json.loads(json.dumps(rec), object_pairs_hook=od)
    if not stops(ms, ms.verify_record, r, xm0, ms.dumps(r) + u"\n" + D(2030, 3, 31)):
        out.append(u"verify_record が渡された記録の字の検査をしない(日付の形)")
    # 引き数なしの main --check は root の下の記録を読む(置き場は読まない)
    with Temp() as d:
        cd = os.path.join(d, "fixtures", "xbrl", "cd8")
        os.makedirs(cd)
        with io.open(os.path.join(cd, os.path.basename(ms.RECORD_REL)), "w", encoding="utf-8") as fh:
            fh.write(ms.dumps(rec))
        with io.open(os.path.join(cd, os.path.basename(ms.XM0_RECORD_REL)), "w", encoding="utf-8") as fh:
            fh.write(ms.dumps(xm0))
        lines = []
        saved = ms.check
        ms.check = lambda **kw: lines.append(kw)
        try:
            ms.main(["--check", "--root", d])
        finally:
            ms.check = saved
        if lines != [dict(root=d)]:
            out.append(u"main --check が check に root を渡さない: %s" % lines)
        ms.main(["--check", "--root", d])                          # 本物の check(置き場は読まない)
    return out


# ======================================================================== 変異
def bound_mutants():
    u"""予測の境の表の 10 行を、下限・下限を含むか・上限・上限を含むかの 1 つずつ(あれば)替える。"""
    out = []
    for k, v in EXPECT_BOUNDS.items():
        old = u'("%s", %s)' % (k, repr(v))
        lo, lo_in, hi, hi_in = v
        variants = [(u"下限を含むかを逆にする", (lo, not lo_in, hi, hi_in))]
        if lo is not None:
            variants += [(u"下限を 1 上げる", (lo + 1, lo_in, hi, hi_in)), (u"下限を 1 下げる", (lo - 1, lo_in, hi, hi_in))]
        if hi is not None:
            variants += [(u"上限を含むかを逆にする", (lo, lo_in, hi, not hi_in)), (u"上限を 1 上げる", (lo, lo_in, hi + 1, hi_in))]
        for what, nv in variants:
            out.append((u"B %s の%s" % (k, what), old, u'("%s", %s)' % (k, repr(nv)), ("seal",)))
    return out


#: (名前, 置き換え前(script の中でちょうど 1 回)・置き換え後・赤になるべき検査の名前)。**約束の側から作った。予測は「その検査が赤になる」(各検査が 1 つずつ赤)。**
MUTANTS = tuple(bound_mutants()) + (
    # ---- 名・鍵(§1)
    (u"N1 接頭辞の「: が無ければ空」を外す", u'return name.split(":", 1)[0] if ":" in name else ""', u'return name.split(":", 1)[0]', ("pure", "count")),
    (u"N2 接頭辞を最後の : の前にする", u'return name.split(":", 1)[0] if ":" in name else ""', u'return name.rsplit(":", 1)[0] if ":" in name else ""', ("pure",)),
    (u"D1 次元の集まりを並べ替えない(並びで比べる)", u'return tuple(sorted(tuple(x) for x in row["dims"]))', u'return tuple(tuple(x) for x in row["dims"])', ("pure", "count")),
    (u"K1 鍵(日)に対象を入れない", u'return (row["kind"], row["name"], row["pkind"], tuple(row["period"]), row["target"], dims_key(row))', u'return (row["kind"], row["name"], row["pkind"], tuple(row["period"]), dims_key(row))', ("pure", "count")),
    (u"K2 鍵(日)に種類(数・文)を入れない", u'return (row["kind"], row["name"], row["pkind"], tuple(row["period"]), row["target"], dims_key(row))', u'return (row["name"], row["pkind"], tuple(row["period"]), row["target"], dims_key(row))', ("pure", "count")),
    (u"K3 鍵(日)に期間の種類を入れない", u'return (row["kind"], row["name"], row["pkind"], tuple(row["period"]), row["target"], dims_key(row))', u'return (row["kind"], row["name"], tuple(row["period"]), row["target"], dims_key(row))', ("pure",)),
    (u"K4 鍵(日)の期間を終わりの日だけにする", u'return (row["kind"], row["name"], row["pkind"], tuple(row["period"]), row["target"], dims_key(row))', u'return (row["kind"], row["name"], row["pkind"], tuple(row["period"][-1:]), row["target"], dims_key(row))', ("pure",)),
    (u"K5 鍵(日)の期間を始まりの日だけにする", u'return (row["kind"], row["name"], row["pkind"], tuple(row["period"]), row["target"], dims_key(row))', u'return (row["kind"], row["name"], row["pkind"], tuple(row["period"][:1]), row["target"], dims_key(row))', ("pure",)),
    (u"K6 鍵(日)に科目の名を入れない", u'return (row["kind"], row["name"], row["pkind"], tuple(row["period"]), row["target"], dims_key(row))', u'return (row["kind"], row["pkind"], tuple(row["period"]), row["target"], dims_key(row))', ("pure", "count")),
    (u"K7 鍵(日)に次元を入れない", u'return (row["kind"], row["name"], row["pkind"], tuple(row["period"]), row["target"], dims_key(row))', u'return (row["kind"], row["name"], row["pkind"], tuple(row["period"]), row["target"])', ("pure", "count")),
    (u"K8 鍵(枠)の期の名を使わず日のままにする(鍵(日)と同じ)", u'return (row["kind"], row["name"], row["pkind"], M.period_name(row["pkind"], row["period"], dec), row["target"], dims_key(row))',
     u'return (row["kind"], row["name"], row["pkind"], tuple(row["period"]), row["target"], dims_key(row))', ("pure", "count")),
    (u"K9 鍵(枠)に対象を入れない", u'return (row["kind"], row["name"], row["pkind"], M.period_name(row["pkind"], row["period"], dec), row["target"], dims_key(row))',
     u'return (row["kind"], row["name"], row["pkind"], M.period_name(row["pkind"], row["period"], dec), dims_key(row))', ("pure", "count")),
    (u"K10 鍵(枠)に種類を入れない", u'return (row["kind"], row["name"], row["pkind"], M.period_name(row["pkind"], row["period"], dec), row["target"], dims_key(row))',
     u'return (row["name"], row["pkind"], M.period_name(row["pkind"], row["period"], dec), row["target"], dims_key(row))', ("pure", "count")),
    (u"K11 鍵(枠)に次元を入れない", u'return (row["kind"], row["name"], row["pkind"], M.period_name(row["pkind"], row["period"], dec), row["target"], dims_key(row))',
     u'return (row["kind"], row["name"], row["pkind"], M.period_name(row["pkind"], row["period"], dec), row["target"])', ("pure", "count")),
    (u"K12 鍵(枠)に科目の名を入れない", u'return (row["kind"], row["name"], row["pkind"], M.period_name(row["pkind"], row["period"], dec), row["target"], dims_key(row))',
     u'return (row["kind"], row["pkind"], M.period_name(row["pkind"], row["period"], dec), row["target"], dims_key(row))', ("pure", "count")),
    (u"K13 鍵(枠)に期間の種類を入れない", u'return (row["kind"], row["name"], row["pkind"], M.period_name(row["pkind"], row["period"], dec), row["target"], dims_key(row))',
     u'return (row["kind"], row["name"], M.period_name(row["pkind"], row["period"], dec), row["target"], dims_key(row))', ("pure",)),
    # ---- 期の区分
    (u"P1 期の区分の前期を Prior2 まで広げる", u'return u"前期" if int(m.group(1)) == 1 else u"それより前"', u'return u"前期" if int(m.group(1)) <= 2 else u"それより前"', ("pure", "count")),
    (u"P2 期の区分の前期を Prior1 だけにしない(それより前を前期にする)", u'return u"前期" if int(m.group(1)) == 1 else u"それより前"', u'return u"前期" if int(m.group(1)) >= 1 else u"それより前"', ("pure", "count")),
    (u"P3 期の名が付かない行で止めない", u'        raise Stop(u"**型の行に期の名が付かない。止める**")', u'        return u"提出日"', ("pure",)),
    (u"P4 提出日を当期にする", u'    if pn == M.PERIOD_FILING:\n        return u"提出日"', u'    if pn == M.PERIOD_FILING:\n        return u"当期"', ("pure", "count")),
    (u"P5 当期を提出日と同じ扱いにする(当期の判定を外す)", u'    if pn == M.PERIOD_CUR:\n        return u"当期"', u'    if pn == M.PERIOD_CUR:\n        return u"前期"', ("pure", "count")),
    # ---- 同じ行の中身
    (u"C1 無い 同士を片方だけが 無い にする", u'    if (rv == VALUE_NONE) != (pv == VALUE_NONE):\n        return CONTENT4[3]', u'    if rv == VALUE_NONE or pv == VALUE_NONE:\n        return CONTENT4[3]', ("pure", "count")),
    (u"C2 -0 と 0 を同じ値にする", u'    if rv != pv:\n        return CONTENT4[2]', u'    if rv.lstrip("-") != pv.lstrip("-"):\n        return CONTENT4[2]', ("pure", "count")),
    (u"C3 単位を比べない", u'if (row["unit"], row["shift"], row["prec"]) == (prow["unit"], prow["shift"], prow["prec"]):', u'if (row["shift"], row["prec"]) == (prow["shift"], prow["prec"]):', ("pure", "count")),
    (u"C4 表示の位を比べない", u'if (row["unit"], row["shift"], row["prec"]) == (prow["unit"], prow["shift"], prow["prec"]):', u'if (row["unit"], row["prec"]) == (prow["unit"], prow["prec"]):', ("pure", "count")),
    (u"C5 精度を比べない", u'if (row["unit"], row["shift"], row["prec"]) == (prow["unit"], prow["shift"], prow["prec"]):', u'if (row["unit"], row["shift"]) == (prow["unit"], prow["shift"]):', ("pure", "count")),
    (u"C6 値が違い単位も違うとき他違いにする(値の違いを先に見ない)", u'    if rv != pv:\n        return CONTENT4[2]', u'    if rv != pv and (row["unit"], row["shift"], row["prec"]) == (prow["unit"], prow["shift"], prow["prec"]):\n        return CONTENT4[2]', ("pure",)),
    (u"C7 片方だけが 無い を値が違うに数える(値の違いを先に見る)", u'    if (rv == VALUE_NONE) != (pv == VALUE_NONE):\n        return CONTENT4[3]', u'    if (rv == VALUE_NONE) != (pv == VALUE_NONE):\n        return CONTENT4[2]', ("pure", "count")),
    (u"C8 値が違うを他違いに数える", u'    if rv != pv:\n        return CONTENT4[2]', u'    if rv != pv:\n        return CONTENT4[1]', ("pure", "count")),
    # ---- 名の数(§2-1)・名が足りる行(§2-2)
    (u"T1 名が足りる行で科目の名を見ない", u'if r["name"] in pn[u"科目"] and all(ax in pn[u"軸"] and m in pn[u"member"] for ax, m in r["dims"]):', u'if all(ax in pn[u"軸"] and m in pn[u"member"] for ax, m in r["dims"]):', ("count",)),
    (u"T2 名が足りる行で軸を見ない", u'if r["name"] in pn[u"科目"] and all(ax in pn[u"軸"] and m in pn[u"member"] for ax, m in r["dims"]):', u'if r["name"] in pn[u"科目"] and all(m in pn[u"member"] for ax, m in r["dims"]):', ("count",)),
    (u"T3 名が足りる行で member を見ない", u'if r["name"] in pn[u"科目"] and all(ax in pn[u"軸"] and m in pn[u"member"] for ax, m in r["dims"]):', u'if r["name"] in pn[u"科目"] and all(ax in pn[u"軸"] for ax, m in r["dims"]):', ("count",)),
    (u"T4 名が足りる行で次元を 1 つでも在ればよいとする", u'if r["name"] in pn[u"科目"] and all(ax in pn[u"軸"] and m in pn[u"member"] for ax, m in r["dims"]):', u'if r["name"] in pn[u"科目"] and (not r["dims"] or any(ax in pn[u"軸"] and m in pn[u"member"] for ax, m in r["dims"])):', ("count",)),
    (u"T5 名が足りる行を今年の対応表で見る", u'if r["name"] in pn[u"科目"] and all(ax in pn[u"軸"] and m in pn[u"member"] for ax, m in r["dims"]):', u'if r["name"] in cn[u"科目"] and all(ax in cn[u"軸"] and m in cn[u"member"] for ax, m in r["dims"]):', ("count",)),
    (u"T6 名が足りる行の軸を member の表で見る", u'if r["name"] in pn[u"科目"] and all(ax in pn[u"軸"] and m in pn[u"member"] for ax, m in r["dims"]):', u'if r["name"] in pn[u"科目"] and all(ax in pn[u"member"] and m in pn[u"member"] for ax, m in r["dims"]):', ("count",)),
    (u"T7 持ち越せる名を和集合で数える", u'd[u"持ち越せる"] = len(cn[k] & pn[k])', u'd[u"持ち越せる"] = len(cn[k] | pn[k])', ("count",)),
    (u"T8 新しい名を前の年にだけ在る名にする", u'new = cn[k] - pn[k]', u'new = pn[k] - cn[k]', ("count",)),
    (u"T9 消えた名を今年にだけ在る名にする", u'd[u"消えた"] = len(pn[k] - cn[k])', u'd[u"消えた"] = len(cn[k] - pn[k])', ("count",)),
    (u"T10 _cor で終わるを含むにする(両方の行)", u'''d[u"新しい・_cor で終わる"] = sum(1 for n in new if name_prefix(n).endswith(COR_END))
        d[u"新しい・_cor で終わらない"] = sum(1 for n in new if not name_prefix(n).endswith(COR_END))''', u'''d[u"新しい・_cor で終わる"] = sum(1 for n in new if COR_END in name_prefix(n))
        d[u"新しい・_cor で終わらない"] = sum(1 for n in new if COR_END not in name_prefix(n))''', ("count",)),
    (u"T11 _cor で終わるを接頭辞の頭にする", u'd[u"新しい・_cor で終わる"] = sum(1 for n in new if name_prefix(n).endswith(COR_END))', u'd[u"新しい・_cor で終わる"] = sum(1 for n in new if name_prefix(n).startswith(COR_END))', ("count",)),
    (u"T12 _cor で終わらないを新しい名の全部にする", u'd[u"新しい・_cor で終わらない"] = sum(1 for n in new if not name_prefix(n).endswith(COR_END))', u'd[u"新しい・_cor で終わらない"] = len(new)', ("count",)),
    (u"T13 _cor を cor にする(下線の無い cor で終わる接頭辞も数える)", u'COR_END = "_cor"', u'COR_END = "cor"', ("seal", "count")),
    (u"T14 対応表を今年の行だけから作る(前の年の対応表を今年の型から作る)", u'pmaps, _pi = M.code_maps(prior["rows"])', u'pmaps, _pi = M.code_maps(cur["rows"])', ("count",)),
    (u"T15 今年の対応表を前の年の型から作る", u'cmaps, _ci = M.code_maps(cur["rows"])', u'cmaps, _ci = M.code_maps(prior["rows"])', ("count",)),
    (u"T16 対応表の名を作らない(code_maps を呼ばない)", u'cmaps, _ci = M.code_maps(cur["rows"])', u'cmaps = dict((k, {}) for k in KINDS)', ("count",)),
    (u"T17 対応表の種類の 軸 を数えない", u'KINDS = (u"科目", u"軸", u"member")', u'KINDS = (u"科目", u"member")', ("seal", "count")),
    # ---- 対象の fact・型の外の fact・型の行(§2-7)
    (u"F1 対象の fact の数・文を逆にする", u'k = KN if f["isnum"] else KT', u'k = KT if f["isnum"] else KN', ("count",)),
    (u"F2 型の外の fact を理由が無い fact にする", u'            if f["reasons"]:\n                out[u"型の外の fact"]', u'            if not f["reasons"]:\n                out[u"型の外の fact"]', ("count",)),
    (u"F3 型の外の理由ごとの数を 1 つ目の理由だけにする", u'for r in f["reasons"]:', u'for r in sorted(f["reasons"])[:1]:', ("count",)),
    (u"F4 今年と前の年の分析を入れ替える(組)", u'for side, an in zip(SIDES, (cur, prior)):', u'for side, an in zip(SIDES, (prior, cur)):', ("count",)),
    (u"F5 型の行の数を数だけにする", u'out[u"型の行"][side][r["kind"]] += 1', u'out[u"型の行"][side][KN] += 1', ("count",)),
    # ---- 今年の行(§2-2〜§2-5)
    (u"R1 期の区分を前の年の書類の決めで付ける", u'cls = period_class(r, cur["dec"])', u'cls = period_class(r, prior["dec"])', ("count",)),
    (u"R2 今年の行の期の区分を数の行にだけ入れる(種類の取り違え)", u'out[u"今年の行の期の区分"][k][cls] += 1', u'out[u"今年の行の期の区分"][KN][cls] += 1', ("count",)),
    (u"R3 同じ行(日)を数の行にだけ入れる", u'out[u"同じ行(日)"][k][cls] += 1', u'out[u"同じ行(日)"][KN][cls] += 1', ("count",)),
    (u"R4 枠が在る行を数の行にだけ入れる", u'out[u"枠が在る行"][k][cls] += 1', u'out[u"枠が在る行"][KN][cls] += 1', ("count",)),
    (u"R5 名が足りる行を数の行にだけ入れる", u'out[u"名が足りる行"][k] += 1', u'out[u"名が足りる行"][KN] += 1', ("count",)),
    (u"R6 同じ行(日)の探し方を鍵(枠)にする", u'q = pday.get(key_day(r))', u'q = pday.get(key_day(r)) if key_frame(r, cur["dec"]) in pframe else None', ("count",)),
    (u"R7 同じ行の中身を文の行にも数える", u'            if k == KN:\n                out[u"同じ行の中身(数)"]', u'            if True:\n                out[u"同じ行の中身(数)"]', ("count",)),
    (u"R8 前の年の鍵(枠)の期の名を今年の書類の決めで付ける", u'pframe = set(key_frame(r, prior["dec"]) for r in prior["rows"])', u'pframe = set(key_frame(r, cur["dec"]) for r in prior["rows"])', ("count",)),
    (u"R9 今年の鍵(枠)の期の名を前の年の書類の決めで付ける", u'if key_frame(r, cur["dec"]) in pframe:', u'if key_frame(r, prior["dec"]) in pframe:', ("count",)),
    (u"R10 枠が在る行の判定を鍵(日)にする", u'if key_frame(r, cur["dec"]) in pframe:', u'if key_day(r) in pday:', ("count",)),
    (u"R11 前の年の鍵(日)の重なりで止めない", u'if len(pday) != len(prior["rows"]):', u'if False:', ("count",)),
    # ---- 逆向き(§2-6)
    (u"V1 逆向きの日の数を鍵(枠)で数える", u'        if key_day(q) in cday:', u'        if key_frame(q, prior["dec"]) in cframe:', ("count",)),
    (u"V2 逆向きの枠の数を鍵(日)で数える", u'        if key_frame(q, prior["dec"]) in cframe:\n            d[u"同じ鍵(枠)が今年に在る"] += 1', u'        if key_day(q) in cday:\n            d[u"同じ鍵(枠)が今年に在る"] += 1', ("count",)),
    (u"V3 逆向きの枠の期の名を今年の書類の決めで付ける", u'        if key_frame(q, prior["dec"]) in cframe:', u'        if key_frame(q, cur["dec"]) in cframe:', ("count",)),
    (u"V4 今年の鍵(枠)の集まりを前の年の書類の決めで作る", u'cframe = set(key_frame(r, cur["dec"]) for r in cur["rows"])', u'cframe = set(key_frame(r, prior["dec"]) for r in cur["rows"])', ("count",)),
    (u"V5 要らなくなった枠を鍵(日)の数から引く", u'd[u"今年、要らなくなった枠"] = d[u"前の年の行"] - d[u"同じ鍵(枠)が今年に在る"]', u'd[u"今年、要らなくなった枠"] = d[u"前の年の行"] - d[u"同じ鍵(日)が今年に在る"]', ("count",)),
    (u"V6 要らなくなった枠を枠が無い数でなく枠が在る数にする", u'd[u"今年、要らなくなった枠"] = d[u"前の年の行"] - d[u"同じ鍵(枠)が今年に在る"]', u'd[u"今年、要らなくなった枠"] = d[u"同じ鍵(枠)が今年に在る"]', ("count",)),
    (u"V7 逆向きの前の年の行を今年の行の数にする", u'        d[u"前の年の行"] += 1', u'        d[u"前の年の行"] += 0', ("count",)),
    (u"V8 逆向きの鍵(日)を今年の鍵(日)の集まりでなく前の年の集まりで引く", u'        if key_day(q) in cday:', u'        if key_day(q) in pday:', ("count",)),
    # ---- 組 1 つ・断り
    (u"E1 今年の側が断った年を前の年にする", u'ent[u"断った"], ent[u"断った年"], ent[u"断った理由"] = True, u"今年", exc.reason', u'ent[u"断った"], ent[u"断った年"], ent[u"断った理由"] = True, u"前の年", exc.reason', ("entry",)),
    (u"E2 前の年の側が断った年を今年にする", u'ent[u"断った"], ent[u"断った年"], ent[u"断った理由"] = True, u"前の年", exc.reason', u'ent[u"断った"], ent[u"断った年"], ent[u"断った理由"] = True, u"今年", exc.reason', ("entry",)),
    (u"E3 断った理由を空にする(今年の側)", u'True, u"今年", exc.reason', u'True, u"今年", u""', ("entry",)),
    (u"E4 断った組の数を 0 にしない(今年の側)", u'''    except Refuse as exc:
        ent.update(zero_pair())
        ent[u"断った"], ent[u"断った年"], ent[u"断った理由"] = True, u"今年", exc.reason''', u'''    except Refuse as exc:
        ent[u"断った"], ent[u"断った年"], ent[u"断った理由"] = True, u"今年", exc.reason''', ("entry",)),
    (u"E5 断った組の数を 0 にしない(前の年の側)", u'''    except Refuse as exc:
        ent.update(zero_pair())
        ent[u"断った"], ent[u"断った年"], ent[u"断った理由"] = True, u"前の年", exc.reason''', u'''    except Refuse as exc:
        ent.update(count_types(cur, cur))
        ent[u"断った"], ent[u"断った年"], ent[u"断った理由"] = True, u"前の年", exc.reason''', ("entry",)),
    (u"E6 今年の側を分析するとき前の年の path を渡す", u'cur = analyzer(cur_path)', u'cur = analyzer(prior_path)', ("entry", "build")),
    (u"E7 今年の側が断っても前の年の側を分析する", u'''        ent[u"旗用の数"] = entry_tail((False, 0, 0))
        return ent, set()''', u'''        ent[u"旗用の数"] = entry_tail((False, 0, 0))
        analyzer(prior_path)
        return ent, set()''', ("entry", "build")),
    (u"E8 M.Refuse 以外の例外も断りにする(今年の側)", u'''    try:
        cur = analyzer(cur_path)
    except Refuse as exc:''', u'''    try:
        cur = analyzer(cur_path)
    except Exception as exc:
        exc.reason = u"例外"''', ("entry",)),
    (u"E9 M.Refuse 以外の例外も断りにする(前の年の側)", u'''    try:
        prior = analyzer(prior_path)
    except Refuse as exc:''', u'''    try:
        prior = analyzer(prior_path)
    except Exception as exc:
        exc.reason = u"例外"''', ("entry",)),
    (u"E10 旗用の数の数・文を逆にする", u'cur_rows = (True, sum(1 for r in cur["rows"] if r["kind"] == KN), sum(1 for r in cur["rows"] if r["kind"] == KT))', u'cur_rows = (True, sum(1 for r in cur["rows"] if r["kind"] == KT), sum(1 for r in cur["rows"] if r["kind"] == KN))', ("entry",)),
    (u"E11 前の年の側が断った組の旗用の数を 0 にする", u'        ent[u"旗用の数"] = entry_tail(cur_rows)\n        return ent, names_in(cur)', u'        ent[u"旗用の数"] = entry_tail((False, 0, 0))\n        return ent, names_in(cur)', ("entry",)),
    (u"E12 名の集まりに前の年の名を入れない", u'return ent, names_in(cur) | names_in(prior)', u'return ent, names_in(cur)', ("entry",)),
    (u"E13 名の集まりに接頭辞を入れない", u'            out.add(name_prefix(n))\n', u'', ("entry",)),
    (u"E14 名の集まりに局所名を入れない", u'            out.add(n.split(":", 1)[-1])\n', u'', ("entry",)),
    (u"E15 分析を注入された analyzer でなく本物にする", u'    analyzer = analyzer or analyze_side\n    ent = od([(u"番号", n)])', u'    analyzer = analyze_side\n    ent = od([(u"番号", n)])', ("entry", "build", "dev")),
    (u"E16 組の記録に番号を入れない", u'    ent = od([(u"番号", n)])\n    try:\n        cur = analyzer(cur_path)', u'    ent = od([(u"番号", 0)])\n    try:\n        cur = analyzer(cur_path)', ("entry",)),
    (u"E17 前の年を分析するとき今年の path を渡す", u'prior = analyzer(prior_path)', u'prior = analyzer(cur_path)', ("entry", "build")),
    (u"E18 count_types に今年と前の年を逆に渡す", u'    ent.update(count_types(cur, prior))', u'    ent.update(count_types(prior, cur))', ("entry",)),
    # ---- 集計・判定の数
    (u"G1 訓練を番号 2 以下にする", u'train = [e for e in entries if e[u"番号"] <= SEEN_MAX_NO]', u'train = [e for e in entries if e[u"番号"] < SEEN_MAX_NO]', ("entry",)),
    (u"G2 判定を番号 3 以上にする", u'rest = [e for e in entries if e[u"番号"] > SEEN_MAX_NO]\n    return od', u'rest = [e for e in entries if e[u"番号"] >= SEEN_MAX_NO]\n    return od', ("entry",)),
    (u"G3 全部の集計に断った組を入れない", u'(u"全部の 63 組", group_total(entries))', u'(u"全部の 63 組", group_total([e for e in entries if not e[u"断った"]]))', ("entry",)),
    (u"G4 組の数を断っていない組だけで数える", u'od([(u"組", len(entries)), (u"断った組", sum(1 for e in entries if e[u"断った"])), (u"数", M.sum_nested(body) if body else od())])',
     u'od([(u"組", sum(1 for e in entries if not e[u"断った"])), (u"断った組", sum(1 for e in entries if e[u"断った"])), (u"数", M.sum_nested(body) if body else od())])', ("entry",)),
    (u"G5 断った組の数を数えない", u'(u"断った組", sum(1 for e in entries if e[u"断った"]))', u'(u"断った組", 0)', ("entry",)),
    (u"G6 足す数から旗用の数を外さない", u'NOT_SUMMED = (u"番号", u"断った", u"断った年", u"断った理由", u"旗用の数")', u'NOT_SUMMED = (u"番号", u"断った", u"断った年", u"断った理由")', ("entry",)),
    (u"G7 足す数から断ったを外さない", u'NOT_SUMMED = (u"番号", u"断った", u"断った年", u"断った理由", u"旗用の数")', u'NOT_SUMMED = (u"番号", u"断った年", u"断った理由", u"旗用の数")', ("entry",)),
    (u"G8 訓練の 3 組と判定の 60 組を入れ替える", u'return od([(u"訓練の 3 組", group_total(train)), (u"判定の 60 組", group_total(rest)), (u"全部の 63 組", group_total(entries))])',
     u'return od([(u"訓練の 3 組", group_total(rest)), (u"判定の 60 組", group_total(train)), (u"全部の 63 組", group_total(entries))])', ("entry", "build")),
    (u"G9 見た 3 組の分けを 2 にする", u'SEEN_MAX_NO = 3 ', u'SEEN_MAX_NO = 2 ', ("seal", "entry")),
    (u"J1 XK0-1 の分母を新しい名にする", u'rate_of(sc[u"持ち越せる"], sc[u"今年"])', u'rate_of(sc[u"持ち越せる"], sc[u"新しい"])', ("entry", "build")),
    (u"J2 XK0-1 の分子を新しい名にする", u'rate_of(sc[u"持ち越せる"], sc[u"今年"])', u'rate_of(sc[u"新しい"], sc[u"今年"])', ("entry", "build")),
    (u"J3 XK0-2 を文の行で数える", u'rate_of(z[u"名が足りる行"][KN], rows_n)', u'rate_of(z[u"名が足りる行"][KT], rows_n)', ("entry", "build")),
    (u"J4 XK0-2 の分母を文の行にする", u'rate_of(z[u"名が足りる行"][KN], rows_n)', u'rate_of(z[u"名が足りる行"][KN], z[u"型の行"][u"今年"][KT])', ("entry", "build")),
    (u"J5 XK0-3 の分子を前期以外も入れる", u'rate_of(sum4(same_n, old), sum4(cls_n, old))', u'rate_of(sum4(same_n), sum4(cls_n, old))', ("entry",)),
    (u"J6 XK0-3 の分母を全部の期の区分にする", u'rate_of(sum4(same_n, old), sum4(cls_n, old))', u'rate_of(sum4(same_n, old), sum4(cls_n))', ("entry", "build")),
    (u"J7 XK0-3 の前期とそれより前をそれより前だけにする", u'old = (u"前期", u"それより前")', u'old = (u"それより前",)', ("entry", "build")),
    (u"J8 XK0-3 の前期とそれより前を前期だけにする", u'old = (u"前期", u"それより前")', u'old = (u"前期",)', ("entry", "build")),
    (u"J9 XK0-4 の分母を今年の数の行にする", u'rate_of(cont[CONTENT4[0]], sum4(same_n))', u'rate_of(cont[CONTENT4[0]], rows_n)', ("entry", "build")),
    (u"J10 XK0-5 の分母を同じ行(数)にする", u'rate_of(cont[CONTENT4[0]], rows_n)', u'rate_of(cont[CONTENT4[0]], sum4(same_n))', ("entry", "build")),
    (u"J11 XK0-5 の分子を同じ行(数)にする", u'(u"XK0-5 今年の数の型の行のうち、同じ行で全部同じの行 / 今年の数の型の行", rate_of(cont[CONTENT4[0]], rows_n))', u'(u"XK0-5 今年の数の型の行のうち、同じ行で全部同じの行 / 今年の数の型の行", rate_of(sum4(same_n), rows_n))', ("entry", "build")),
    (u"J12 XK0-6 の分子を同じ行(日)にする", u'rate_of(sum4(z[u"枠が在る行"][KN]), rows_n)', u'rate_of(sum4(same_n), rows_n)', ("entry", "build")),
    (u"J13 XK0-6 を数・文の合計にする", u'rate_of(sum4(z[u"枠が在る行"][KN]), rows_n)', u'rate_of(sum4(z[u"枠が在る行"][KN]) + sum4(z[u"枠が在る行"][KT]), rows_n)', ("entry", "build")),
    (u"J14 XK0-7 の分子を _cor で終わらない名にする", u'rate_of(sc[u"新しい・_cor で終わる"], sc[u"新しい"])', u'rate_of(sc[u"新しい・_cor で終わらない"], sc[u"新しい"])', ("entry", "build")),
    (u"J15 XK0-7 の分母を今年の科目の名にする", u'rate_of(sc[u"新しい・_cor で終わる"], sc[u"新しい"])', u'rate_of(sc[u"新しい・_cor で終わる"], sc[u"今年"])', ("entry", "build")),
    (u"J16 XK0-8 を判定の組の数にする", u'(u"組", g[u"断った組"]), (u"分母", g[u"組"])', u'(u"組", g[u"組"]), (u"分母", g[u"組"])', ("entry", "build")),
    (u"J17 XK0-9 を not_all_same で数える", u'(u"組", sum(1 for e in judge_entries if keep_pct_pair(e))), (u"分母", g[u"組"])', u'(u"組", sum(1 for e in judge_entries if not_all_same_pair(e))), (u"分母", g[u"組"])', ("entry", "build")),
    (u"J18 XK0-10 を keep_pct で数える", u'(u"組", sum(1 for e in judge_entries if not_all_same_pair(e))), (u"分母", g[u"組"])', u'(u"組", sum(1 for e in judge_entries if keep_pct_pair(e))), (u"分母", g[u"組"])', ("entry", "build")),
    (u"J19 XK0-9 の分母を断っていない組にする", u'(u"組", sum(1 for e in judge_entries if keep_pct_pair(e))), (u"分母", g[u"組"])', u'(u"組", sum(1 for e in judge_entries if keep_pct_pair(e))), (u"分母", g[u"組"] - g[u"断った組"])', ("entry", "build")),
    (u"J20 組の判定の 95% を 94% にする", u'KEEP_ONE_PCT = 95 ', u'KEEP_ONE_PCT = 94 ', ("seal", "pure")),
    (u"J21 組の判定の「以上」を「超える」にする", u'100 * c[u"持ち越せる"] >= KEEP_ONE_PCT * c[u"今年"]', u'100 * c[u"持ち越せる"] > KEEP_ONE_PCT * c[u"今年"]', ("pure",)),
    (u"J22 組の判定の名 0 を満たすにする", u'c[u"今年"] > 0 and 100', u'c[u"今年"] >= 0 and 100', ("pure",)),
    (u"J23 組の判定で断った組を除かない(XK0-9)", u'return (not e[u"断った"]) and c[u"今年"] > 0', u'return c[u"今年"] > 0', ("pure",)),
    (u"J24 組の判定で断った組を除かない(XK0-10)", u'return (not e[u"断った"]) and sum(z.values()) - z[CONTENT4[0]] >= 1', u'return sum(z.values()) - z[CONTENT4[0]] >= 1', ("pure",)),
    (u"J25 全部同じでない行の 1 を 2 にする", u'sum(z.values()) - z[CONTENT4[0]] >= 1', u'sum(z.values()) - z[CONTENT4[0]] >= 2', ("pure",)),
    (u"J26 全部同じでない行を全部同じ以外でなく値が違うだけにする", u'sum(z.values()) - z[CONTENT4[0]] >= 1', u'z[CONTENT4[2]] >= 1', ("pure",)),
    (u"J27 率を切り捨てにする", u'    return od([(u"数", n), (u"分母", d), (u"%", pct1(n, d))])', u'    return od([(u"数", n), (u"分母", d), (u"%", (1000 * n // d) / 10.0 if d else None)])', ("pure",)),
    (u"J28 率の数と分母を入れ替える", u'    return od([(u"数", n), (u"分母", d), (u"%", pct1(n, d))])', u'    return od([(u"数", d), (u"分母", n), (u"%", pct1(n, d))])', ("pure", "entry")),
    (u"J29 判定の数に訓練の組も混ぜる(build_record が全部の組で判定する)", u'rec[u"予測の判定に要る数(XK0-1〜XK0-10。判定の 60 組だけ。当たり・外れは結果の文書で)"] = judged(rest)', u'rec[u"予測の判定に要る数(XK0-1〜XK0-10。判定の 60 組だけ。当たり・外れは結果の文書で)"] = judged(entries)', ("build",)),
    (u"J30 判定の組を番号 3 以上にする(build_record)", u'    rest = [e for e in entries if e[u"番号"] > SEEN_MAX_NO]\n    rec = od()', u'    rest = [e for e in entries if e[u"番号"] >= SEEN_MAX_NO]\n    rec = od()', ("build",)),
    # ---- 旗
    (u"L1 旗 1 を当期でなく前期で数える", u'cur_same = sum(sum4(e[u"同じ行(日)"][k], (u"当期",)) for e in entries for k in (KN, KT))', u'cur_same = sum(sum4(e[u"同じ行(日)"][k], (u"前期",)) for e in entries for k in (KN, KT))', ("flags",)),
    (u"L2 旗 1 を数の行だけで数える", u'cur_same = sum(sum4(e[u"同じ行(日)"][k], (u"当期",)) for e in entries for k in (KN, KT))', u'cur_same = sum(sum4(e[u"同じ行(日)"][k], (u"当期",)) for e in entries for k in (KN,))', ("flags",)),
    (u"L3 旗 1 を判定の組だけで数える", u'cur_same = sum(sum4(e[u"同じ行(日)"][k], (u"当期",)) for e in entries for k in (KN, KT))', u'cur_same = sum(sum4(e[u"同じ行(日)"][k], (u"当期",)) for e in rest for k in (KN, KT))', ("flags",)),
    (u"L4 旗 1 を 2 つ以上にする", u'(u"旗", cur_same >= 1)', u'(u"旗", cur_same >= 2)', ("flags",)),
    (u"L5 旗 2 の分けを訓練の組も見る", u'names_ok = [e for e in rest if', u'names_ok = [e for e in entries if', ("flags",)),
    (u"L6 旗 2 の組の数を判定の組の数と比べない(全部を 100% とする)", u'(u"旗", len(names_ok) == len(rest) and len(rest) > 0)', u'(u"旗", len(names_ok) > 0)', ("flags",)),
    # 予測(走らせる前): L7b は flags だけが赤。one_short の場面で旗 2 が立つため。ほかの検査は赤にならない。
    (u"L7b 旗 2 を名が 1 つだけ足りない組まで 100% に数える", u'e[u"対応表の名"][u"科目"][u"持ち越せる"] == e[u"対応表の名"][u"科目"][u"今年"]]', u'e[u"対応表の名"][u"科目"][u"持ち越せる"] >= e[u"対応表の名"][u"科目"][u"今年"] - 1]', ("flags",)),
    (u"L7 旗 2 が判定の組 0 本で立つ", u'(u"旗", len(names_ok) == len(rest) and len(rest) > 0)', u'(u"旗", len(names_ok) == len(rest))', ("flags",)),
    (u"L8 旗 2 が科目の名 0 の組を 100% に数える", u'e[u"対応表の名"][u"科目"][u"今年"] > 0 and e[u"対応表の名"][u"科目"][u"持ち越せる"] ==', u'e[u"対応表の名"][u"科目"][u"今年"] >= 0 and e[u"対応表の名"][u"科目"][u"持ち越せる"] ==', ("flags",)),
    (u"L9 旗 3 を全部の組の合計で数える", u'same_num = sum(sum4(e[u"同じ行(日)"][KN]) for e in rest)', u'same_num = sum(sum4(e[u"同じ行(日)"][KN]) for e in entries)', ("flags",)),
    (u"L10 旗 3 を文の行で数える", u'same_num = sum(sum4(e[u"同じ行(日)"][KN]) for e in rest)', u'same_num = sum(sum4(e[u"同じ行(日)"][KT]) for e in rest)', ("flags",)),
    (u"L11 旗 3 を 1 以下にする", u'(u"旗", same_num == 0)', u'(u"旗", same_num <= 1)', ("flags",)),
    (u"L12 旗 4 を判定の組だけで数える", u'for e in entries if any(sum4(e[u"枠が在る行"][k]) > e[u"名が足りる行"][k] for k in (KN, KT))]', u'for e in rest if any(sum4(e[u"枠が在る行"][k]) > e[u"名が足りる行"][k] for k in (KN, KT))]', ("flags",)),
    (u"L13 旗 4 を数の行だけで比べる", u'for e in entries if any(sum4(e[u"枠が在る行"][k]) > e[u"名が足りる行"][k] for k in (KN, KT))]', u'for e in entries if any(sum4(e[u"枠が在る行"][k]) > e[u"名が足りる行"][k] for k in (KN,))]', ("flags",)),
    (u"L14 旗 4 を以上で比べる", u'sum4(e[u"枠が在る行"][k]) > e[u"名が足りる行"][k] for k in (KN, KT))]', u'sum4(e[u"枠が在る行"][k]) >= e[u"名が足りる行"][k] for k in (KN, KT))]', ("flags",)),
    (u"L15 旗 4 を型の行の数と比べる", u'sum4(e[u"枠が在る行"][k]) > e[u"名が足りる行"][k] for k in (KN, KT))]', u'sum4(e[u"枠が在る行"][k]) > e[u"型の行"][u"今年"][k] for k in (KN, KT))]', ("flags",)),
    (u"L16 旗 4 を数と文の合計で比べる", u'if any(sum4(e[u"枠が在る行"][k]) > e[u"名が足りる行"][k] for k in (KN, KT))]', u'if sum(sum4(e[u"枠が在る行"][k]) for k in (KN, KT)) > sum(e[u"名が足りる行"][k] for k in (KN, KT))]', ("flags",)),
    (u"L17 旗 5 を全部の組の断りで数える", u'refused = sum(1 for e in rest if e[u"断った"])', u'refused = sum(1 for e in entries if e[u"断った"])', ("flags",)),
    (u"L18 旗 5 を 6 を超えたにする", u'(u"旗", refused >= FLAG_REFUSE_MIN)', u'(u"旗", refused > FLAG_REFUSE_MIN)', ("flags",)),
    (u"L19 旗 5 の 6 を 5 にする", u'FLAG_REFUSE_MIN = 6 ', u'FLAG_REFUSE_MIN = 5 ', ("seal", "flags")),
    (u"L20 旗 6 を数の行だけで照らす", u'if (tail[KN], tail[KT]) != (x[u"型の行"][KN], x[u"型の行"][KT]):', u'if tail[KN] != x[u"型の行"][KN]:', ("flags",)),
    (u"L21 旗 6 を文の行だけで照らす", u'if (tail[KN], tail[KT]) != (x[u"型の行"][KN], x[u"型の行"][KT]):', u'if tail[KT] != x[u"型の行"][KT]:', ("flags",)),
    (u"L22 旗 6 の数・文を入れ替えて照らす", u'if (tail[KN], tail[KT]) != (x[u"型の行"][KN], x[u"型の行"][KT]):', u'if (tail[KN], tail[KT]) != (x[u"型の行"][KT], x[u"型の行"][KN]):', ("flags",)),
    (u"L23 旗 6 を判定の組だけで照らす", u'    diff = 0\n    for e in entries:', u'    diff = 0\n    for e in rest:', ("flags", "build")),
    (u"L24 旗 6 の便 XM0 の記録に番号が無くても止めない", u'''        if x is None:
            raise Stop(u"**便 XM0 の記録に同じ番号が無い。止める**")''', u'''        if x is None:
            continue''', ("flags",)),
    (u"L25 旗 6 を今年の側が断った組を照らさない", u'        tail = e[u"旗用の数"][u"今年の側の型の行"]\n', u'        if not e[u"旗用の数"][u"今年の側を分析できた"]:\n            continue\n        tail = e[u"旗用の数"][u"今年の側の型の行"]\n', ("flags",)),
    (u"L26 旗 6 を違う組が 2 つ以上のとき立てる", u'(u"旗", diff >= 1)', u'(u"旗", diff >= 2)', ("flags",)),
    (u"L27 旗を番号でなく並びの位置で便 XM0 の記録と照らす", u'    by_no = dict((d[u"番号"], d) for d in xm0[u"書類"])', u'    by_no = dict((i, d) for i, d in enumerate(xm0[u"書類"], 1))', ("flags", "build")),
    (u"L28 旗が立ったら止める", u'''    return od([
        (u"旗 1 期の区分が当期の行に''', u'''    if cur_same or refused >= FLAG_REFUSE_MIN:
        raise Stop(u"旗")
    return od([
        (u"旗 1 期の区分が当期の行に''', ("flags",)),
    # ---- 記録・build_record
    (u"B1 便 XM0 の記録の並びの照合を外す", u'    if xm0[u"材料"][u"書類の file 名の並びの sha256"] != order_sha:', u'    if False:', ("build",)),
    (u"B2 組の数の照合を外す", u'    if len(entries) != want_pairs or tot[u"訓練の 3 組"][u"組"] != TRAIN_WANT or tot[u"判定の 60 組"][u"組"] != JUDGE_WANT:', u'    if False:', ("build",)),
    (u"B5 記録の旗を判定の組だけで作る", u'rec[u"先に自分の欠陥を疑う旗"] = flags(entries, xm0)', u'rec[u"先に自分の欠陥を疑う旗"] = flags(rest, xm0)', ("build",)),
    (u"B6 記録の集計を判定の組だけにする", u'rec[u"集計"] = tot', u'rec[u"集計"] = totals_of(rest)', ("build",)),
    (u"B7 記録の script の sha256 を空にする", u'rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))', u'rec[u"この script の sha256"] = u""', ("build",)),
    (u"B8 記録の封の commit を空にする", u'rec[u"封の commit"] = SEAL_COMMIT', u'rec[u"封の commit"] = u""', ("build",)),
    (u"B9 記録の限界を 5 行にする", u'rec[u"限界"] = list(LIMITS)', u'rec[u"限界"] = list(LIMITS)[:5]', ("build",)),
    (u"B10 前の年の側の並びの sha256 を今年の側の並びにする", u'sha256_bytes(u"\\n".join(p[3] for p in pairs).encode("utf-8"))', u'sha256_bytes(u"\\n".join(p[1] for p in pairs).encode("utf-8"))', ("build",)),
    (u"B11 今年の側の並びの sha256 を前の年の側にする", u'order_sha = W.order_sha256([d[0] for d in docs])', u'order_sha = W.order_sha256([p[3] for p in pairs])', ("build",)),
    (u"B12 secret の docID に前の年の側を入れない", u'[d[0] for d in docs] + [p[3] for p in pairs]', u'[d[0] for d in docs]', ("build",)),
    (u"B13 secret の EDINET コードに組のコードを入れない", u'    ecodes = set(p[5] for p in pairs)\n', u'    ecodes = set()\n', ("build",)),
    (u"B14 secret の名を 3 字以上に絞らない", u'set(n for n in names if len(n) >= 3)', u'set(n for n in names if len(n) >= 99)', ("build",)),
    (u"B15 除いた書類の数を組の数にする", u'excluded = len(docs) - len(pairs)', u'excluded = len(pairs)', ("build",)),
    (u"B16 分析を呼ぶ数を 1 組分にする(最後の組だけ)", u'    for n, _stem, p, _pstem, pp, _code in pairs:\n        ent, nm = pair_entry(n, p, pp, analyzer)\n        entries.append(ent)', u'    for n, _stem, p, _pstem, pp, _code in pairs:\n        ent, nm = pair_entry(n, p, pp, analyzer)\n        entries[:] = [ent]', ("build",)),
    (u"B17 記録の材料の訓練の組の数を判定の組の数にする", u'(u"訓練の組の数", tot[u"訓練の 3 組"][u"組"])', u'(u"訓練の組の数", tot[u"判定の 60 組"][u"組"])', ("build",)),
    (u"B18 記録の材料の便 XM0 の sha256 を書かない", u'(u"便 XM0 の記録の sha256", xm0_sha)', u'(u"便 XM0 の記録の sha256", u"")', ("build",)),
    # ---- --check・検査・書き方
    (u"X1 --check が集計の導き直しを照らさない", u'    if dumps(tot) != dumps(rec[u"集計"]):', u'    if False:', ("verify",)),
    (u"X2 --check が判定の数の導き直しを照らさない", u'    if dumps(judged(rest)) != dumps(rec[key]):', u'    if False:', ("verify",)),
    (u"X3 --check が旗の導き直しを照らさない", u'    if dumps(flags(docs, xm0)) != dumps(rec[u"先に自分の欠陥を疑う旗"]):', u'    if False:', ("verify",)),
    (u"X4 --check が組の数の関係を照らさない", u'        why = entry_problems(d)\n        if why:', u'        why = u""\n        if why:', ("verify",)),
    (u"X5 --check が組の番号の昇順を照らさない", u'if any(not isinstance(n, int) for n in nos) or nos != sorted(set(nos)):', u'if any(not isinstance(n, int) for n in nos):', ("verify",)),
    (u"X6 --check が組の番号の重なりを照らさない", u'if any(not isinstance(n, int) for n in nos) or nos != sorted(set(nos)):', u'if any(not isinstance(n, int) for n in nos) or nos != sorted(nos):', ("verify",)),
    (u"X7 --check が組の数 63 を照らさない", u'if not isinstance(docs, list) or len(docs) != want or rec[u"材料"][u"組の数"] != want:', u'if not isinstance(docs, list) or rec[u"材料"][u"組の数"] != want:', ("verify",)),
    (u"X8 --check が材料の組の数を照らさない", u'if not isinstance(docs, list) or len(docs) != want or rec[u"材料"][u"組の数"] != want:', u'if not isinstance(docs, list) or len(docs) != want:', ("verify",)),
    (u"X9 --check が材料の訓練・判定の組の数を照らさない", u'if (mat[u"訓練の組の数"], mat[u"判定の組の数"]) != (tot[u"訓練の 3 組"][u"組"], tot[u"判定の 60 組"][u"組"]) or rec[u"限界"] != list(LIMITS):', u'if rec[u"限界"] != list(LIMITS):', ("verify",)),
    (u"X10 --check が限界を照らさない", u'(tot[u"訓練の 3 組"][u"組"], tot[u"判定の 60 組"][u"組"]) or rec[u"限界"] != list(LIMITS):', u'(tot[u"訓練の 3 組"][u"組"], tot[u"判定の 60 組"][u"組"]):', ("verify",)),
    (u"X11 --check が禁止のものを検査しない", u'    check_clean(rec, text if text is not None else dumps(rec))', u'    pass', ("verify",)),
    (u"X12 --check が渡された字でなく作り直した字を検査する", u'    check_clean(rec, text if text is not None else dumps(rec))', u'    check_clean(rec, dumps(rec))', ("verify",)),
    (u"X13 --check が便 XM0 の記録を読まない(旗を照らさない)", u'    xm0, _sha = load_xm0(root, xm0_path)\n    verify_record(rec, xm0, text, want)', u'    verify_record(rec, {u"書類": [], u"材料": {}}, text, want)', ("e2e",)),
    (u"X14 --check が記録を引数の path でなく root から読む(rec_path を無視する)", u'    p = rec_path or os.path.join(root, RECORD_REL)\n    if not os.path.isfile(p):\n        raise Stop(u"**在る記録が無い。止める**")\n    with io.open(p, encoding="utf-8") as fh:\n        text = fh.read()\n    rec = json.loads(text, object_pairs_hook=od)\n    xm0',
     u'    p = os.path.join(root, RECORD_REL)\n    if not os.path.isfile(p):\n        raise Stop(u"**在る記録が無い。止める**")\n    with io.open(p, encoding="utf-8") as fh:\n        text = fh.read()\n    rec = json.loads(text, object_pairs_hook=od)\n    xm0', ("e2e",)),
    (u"X15 記録を排他で書かない", u'    if os.path.exists(path):\n        raise Stop(u"**記録が既に在る', u'    if False:\n        raise Stop(u"**記録が既に在る', ("clean", "e2e")),
    (u"X16 書いた後の検査を外す", u'    try:\n        check_clean(rec, back, secret)\n    except SystemExit:', u'    try:\n        pass\n    except SystemExit:', ("clean",)),
    (u"X17 書く前の検査を外す", u'    text = record_text(rec, secret)\n    os.makedirs', u'    text = dumps(rec)\n    os.makedirs', ("clean",)),
    (u"X18 検査で日付の形を見ない", u'    if DATE_RE.search(W.HEX_RE.sub(u"", text).replace(SEAL_REL, u"")):', u'    if False:', ("clean",)),
    (u"X19 検査で封の path の中の日付を見る", u'.replace(SEAL_REL, u"")):', u'):', ("clean",)),
    (u"X20 検査を前の便の検査に渡さない(secret を渡さない)", u'    M.check_clean(rec, text, secret)\n', u'    M.check_clean(rec, text)\n', ("clean",)),
    (u"X21 run が旗を表示しない", u'    show_flags(rec, say)\n', u'', ("e2e",)),
    (u"X22 run が旗の立った/立たないを逆にして表示する", u'u"立った" if v[u"旗"] else u"立たない"', u'u"立たない" if v[u"旗"] else u"立った"', ("e2e",)),
    (u"X23 run が便 XM0 の記録の path を無視する", u'    xm0, xm0_sha = load_xm0(root, xm0_path)\n    rec, secret = build_record(docs,', u'    xm0, xm0_sha = load_xm0(root, None)\n    rec, secret = build_record(docs,', ("e2e",)),
    (u"X24 run が組・docs・analyzer を build_record に渡さない", u'build_record(docs, prior, want_docs, want_pairs, xm0, xm0_sha, pairs, docs_list, analyzer, progress)', u'build_record(docs, prior, want_docs, want_pairs, xm0, xm0_sha, None, None, None, progress)', ("e2e",)),
    (u"X25 run が書いた後の記録の組の数でない数を表示する", u'say(u"-> %s(組 %d)" % (os.path.basename(out), rec[u"材料"][u"組の数"]))', u'say(u"-> %s(組 %d)" % (os.path.basename(out), 62))', ("e2e",)),
    (u"X27 --check が記録が無くても止まらない", u'    p = rec_path or os.path.join(root, RECORD_REL)\n    if not os.path.isfile(p):\n        raise Stop(u"**在る記録が無い。止める**")\n    with io.open(p, encoding="utf-8") as fh:\n        text = fh.read()\n    rec = json.loads(text, object_pairs_hook=od)\n    xm0',
     u'    p = rec_path or os.path.join(root, RECORD_REL)\n    with io.open(p, encoding="utf-8") as fh:\n        text = fh.read()\n    rec = json.loads(text, object_pairs_hook=od)\n    xm0', ("e2e",)),
    (u"X28 main の --check が root を渡さない", u'        check(root=a.root)', u'        check()', ("verify",)),
    # ---- --dev
    (u"Z1 --dev が番号 1・2・3 だけに絞らない", u'        if n not in DEV_NOS:\n            continue\n', u'', ("dev",)),
    (u"Z2 --dev の番号を 1・2・3・4 にする", u'DEV_NOS = (1, 2, 3)', u'DEV_NOS = (1, 2, 3, 4)', ("seal", "dev")),
    (u"Z3 --dev が記録を書く", u'    tot = group_total(entries)\n    say(json.dumps(dev_summary(tot), ensure_ascii=False, indent=1))', u'    tot = group_total(entries)\n    write_record(os.path.join(ROOT, RECORD_REL), od([(u"x", 1)]))\n    say(json.dumps(dev_summary(tot), ensure_ascii=False, indent=1))', ("dev",)),
    (u"Z4 --dev の表示が今年の数の行を文の行にする", u'(u"数の行", od([(u"今年", z[u"型の行"][u"今年"][KN])', u'(u"数の行", od([(u"今年", z[u"型の行"][u"今年"][KT])', ("dev",)),
    (u"Z5 --dev の表示の科目を軸にする", u'(u"科目", dict(nm[u"科目"])), (u"軸", dict(nm[u"軸"]))', u'(u"科目", dict(nm[u"軸"])), (u"軸", dict(nm[u"軸"]))', ("dev",)),
    # ---- 前の便の関数の呼び方・配線
    (u"W1 分析の zip 読みで表を剥がさない", u'files, _names, _tables = M.P.peel_tables(M.B.load_package(zip_path))\n    return M.analyze(files)', u'files = M.B.load_package(zip_path)\n    return M.analyze(files)', ("wiring", "import")),
    (u"W2 分析の戻り値を使わない", u'    return M.analyze(files)', u'    M.analyze(files)\n    return None', ("wiring",)),
    (u"W3 分析に断りを握りつぶさせる", u'    files, _names, _tables = M.P.peel_tables(M.B.load_package(zip_path))\n', u'    try:\n        files, _names, _tables = M.P.peel_tables(M.B.load_package(zip_path))\n    except Refuse:\n        return {"dec": {}, "rows": [], "facts": []}\n', ("wiring",)),
    (u"W4 前の便の script を一意でない名で読む(M)", u'M = _load_sibling("_xk0_input_type_2026_11_22",', u'M = _load_sibling("xbrl_input_type",', ("import",)),
    (u"W5 前の便の script を一意でない名で読む(Y)", u'Y = _load_sibling("_xk0_prior_year_draft_2026_11_22",', u'Y = _load_sibling("xbrl_prior_year_draft",', ("import",)),
    (u"W6 network の module を import する", u'import json\nimport os', u'import json\nimport socket\nimport os', ("import",)),
    (u"W7 engine を読む import を足す", u'import json\nimport os', u'import json\nfrom adapters.xbrl import instance as I\nimport os', ("import",)),
    (u"W8 環境変数を読む", u'ROOT = os.path.dirname(HERE)\n', u'ROOT = os.path.dirname(HERE)\nHOME_X = os.environ.get("HOME")\n', ("import",)),
    (u"W9 型の folder を書く関数を呼ぶ", u'    files, _names, _tables = M.P.peel_tables', u'    M.derive_folder\n    files, _names, _tables = M.P.peel_tables', ("import",)),
    (u"W10 注入の仕掛けの規準の字の関数を持つ", u'def two():', u'def run_doc():\n    return None\n\n\ndef two():', ("import",)),
    (u"W11 前の便の analyze を写す", u'def analyze_side(zip_path):', u'def analyze(files):\n    return None\n\n\ndef analyze_side(zip_path):', ("import",)),
    (u"W12 make_pairs を呼ばない(置き場から組を作らない)", u'docs, pairs, excluded = Y.make_pairs(docs_dir or DOCS_DIR, prior_dir or PRIOR_DIR, want_docs, want_pairs)', u'docs, pairs, excluded = [], [], 0', ("build",)),
    (u"W13 sum_nested を写す", u'def group_total(entries):', u'def sum_nested(items):\n    return od()\n\n\ndef group_total(entries):', ("import",)),
    (u"W14 order_sha256 を呼ばない", u'order_sha = W.order_sha256([d[0] for d in docs])', u'order_sha = u"0" * 64', ("import", "build")),
    (u"W15 Refuse を前の便と別の型にする", u'Refuse = M.Refuse', u'class Refuse(Exception):\n    def __init__(self, reason):\n        Exception.__init__(self, reason)\n        self.reason = reason', ("wiring",)),
    (u"W16 Stop を前の便と別の型にする", u'Stop = W.Stop', u'class Stop(SystemExit):\n    pass', ("wiring",)),
    (u"W17 置き場の既定を便 XY0 と別にする", u'DOCS_DIR = Y.DOCS_DIR', u'DOCS_DIR = "/nonexistent"', ("wiring",)),
    (u"W18 組の数 63 を便 XY0 の定数から外す", u'PAIRS_WANT = Y.PAIRS_WANT', u'PAIRS_WANT = 62', ("wiring", "seal")),
    (u"W19 封の commit を違う字にする", u'SEAL_COMMIT = "1fc4c736"', u'SEAL_COMMIT = "1fc4c735"', ("seal",)),
    (u"W20 記録の path を違う字にする", u'RECORD_REL = "fixtures/xbrl/cd8/type_carryover_2026-11-22.json"', u'RECORD_REL = "fixtures/xbrl/cd8/type_carryover_2026-11-23.json"', ("seal",)),
    (u"W21 便 XM0 の記録の path を違う字にする", u'XM0_RECORD_REL = "fixtures/xbrl/cd8/input_type_2026-11-22.json"', u'XM0_RECORD_REL = "fixtures/xbrl/cd8/input_type_2026-11-21.json"', ("seal",)),
    (u"W22 限界の 1 行目を変える", u'u"どちらの年の型も対応表も答えから作った。', u'u"どちらの年の型も対応表も答えから作った(変えた)。', ("seal",)),
    (u"W23 型の外の理由の数を 7 つにする", u'REASONS = M.REASONS', u'REASONS = M.REASONS[:7]', ("seal",)),
    (u"W24 同じ行の中身の分けの名を変える", u'CONTENT4 = (u"全部同じ", ', u'CONTENT4 = (u"全て同じ", ', ("seal",)),
    (u"W25 期の区分の並びを変える", u'CLASS4 = (u"当期", u"前期", u"それより前", u"提出日")', u'CLASS4 = (u"当期", u"それより前", u"前期", u"提出日")', ("seal",)),
    (u"W26 訓練の組の数を 4 にする", u'TRAIN_WANT, JUDGE_WANT = 3, 60', u'TRAIN_WANT, JUDGE_WANT = 4, 60', ("seal",)),
    (u"W27 判定の組の数を 59 にする", u'TRAIN_WANT, JUDGE_WANT = 3, 60', u'TRAIN_WANT, JUDGE_WANT = 3, 59', ("seal",)),
)

#: 黙るのが設計どおりの変異(同値)。理由を書き、別の試験で「黙ること」を縛る
SILENT_BY_DESIGN = (
    (u"S1 期の名の正規表現の先頭・末尾の固定を外す", u'PRIOR_N_RE = re.compile(r"^Prior([0-9]+)Year$")', u'PRIOR_N_RE = re.compile(r"Prior([0-9]+)Year")',
     u"``M.period_name`` が返すのは ``Prior<N>Year`` の形だけ(前後に字は付かない)ので、固定を外しても同じ。"),
    (u"S2 旗 2 が断った組を明示で除く(科目の名の数が 0 の組は 100% と読まない)の「断った」を重ねる", u'names_ok = [e for e in rest if not e[u"断った"] and', u'names_ok = [e for e in rest if',
     u"断った組の科目の名は全部 0 なので ``今年 > 0`` で落ちる(同値)。断った組の数に 0 でない数が入ることは ``entry_problems`` が止める。"),
    (u"S3 旗 4 の「数・文の別に比べる」の順を逆にする", u'for k in (KN, KT))]', u'for k in (KT, KN))]',
     u"any は並びの順に依らない(同値)。"),
    (u"S5 同じ行の中身を今年と前の年を逆に渡す", u'out[u"同じ行の中身(数)"][content_class(r, q)] += 1', u'out[u"同じ行の中身(数)"][content_class(q, r)] += 1',
     u"``content_class`` は 2 つの行の入れ替えに対して対称(値・単位・位・精度の等しさだけを見る)。入れ替えても 4 つの分けは変わらない(同値)。"),
    (u"S6 組の数の照合で訓練の 3 組を見ない", u'or tot[u"訓練の 3 組"][u"組"] != TRAIN_WANT or', u'or',
     u"組の数 63 と判定の 60 組が合えば、訓練の 3 組は自動で合う(同値)。組の数・判定の組の数のどちらかが違えば止まる。"),
    (u"S7 便 XM0 の記録が無いとき、空の記録で進める(build_record)", u'    if xm0 is None:\n        raise Stop(u"**便 XM0 の記録が無い。止める**")', u'    if xm0 is None:\n        xm0 = {u"材料": {u"書類の file 名の並びの sha256": W.order_sha256([d[0] for d in docs])}, u"書類": []}',
     u"空の記録では旗 6 が「便 XM0 の記録に同じ番号が無い」で止まる(止まる理由が別になるだけで、止まることは同じ。同値)。"),
    (u"S8 便 XM0 の記録が無いとき、空の記録を返す(load_xm0)", u'    if not os.path.isfile(p):\n        raise Stop(u"**便 XM0 の記録が無い。止める**")', u'    if not os.path.isfile(p):\n        return od([(u"材料", od([(u"書類の file 名の並びの sha256", u"")])), (u"書類", [])]), u""',
     u"空の記録では並びの sha256 の照合が違って止まる(止まる理由が別になるだけ。同値)。"),
    (u"S4 組の記録の secret の名に空の字も入れる(3 字未満は検査に使わない)", u'out.add(name_prefix(n))', u'out.add(name_prefix(n) or n)',
     u"接頭辞が空の名は局所名と同じ字になる(同値)。"),
)


def increment_sweep():
    u"""``count_types`` の中の ``+= 1`` を 1 行ずつ ``+= 0`` に替える(数え落とし)。script の字から作る(同じ行が 2 回以上在る行は作らない)。"""
    base = read(SCRIPT_REL)
    lines = base.splitlines()
    start = [i for i, ln in enumerate(lines) if ln.startswith("def count_types(")][0]
    end = [i for i, ln in enumerate(lines) if i > start and ln.startswith("def ")][0]
    out = []
    for i in range(start, end):
        ln = lines[i]
        if u"+= 1" in ln and base.count(ln) == 1:
            out.append((u"I%d 数え落とし: %s" % (i + 1, ln.strip()), ln, ln.replace(u"+= 1", u"+= 0"), ("count",)))
    return out


INCREMENT_MUTANTS = tuple(increment_sweep())


def check_by_name(name, mod, src):
    table_ = {u"seal": seal_problems, u"pure": pure_problems, u"count": count_problems, u"entry": entry_problems_gate, u"flags": flags_problems, u"build": build_problems,
              u"clean": clean_problems, u"e2e": e2e_problems, u"dev": dev_problems, u"verify": verify_problems, u"wiring": wiring_problems}
    if name in table_:
        return table_[name](mod)
    if name == u"import":
        return import_problems(src)
    raise AssertionError(name)


ALL_CHECKS = (u"seal", u"pure", u"count", u"entry", u"flags", u"build", u"clean", u"e2e", u"dev", u"verify", u"wiring", u"import")


def run_mutants(table_=MUTANTS + INCREMENT_MUTANTS):
    base = read(SCRIPT_REL)
    out = []
    for name, old, new, checks in table_:
        assert base.count(old) == 1, (name, base.count(old))
        src = base.replace(old, new)
        try:
            mod = load_source(src)
        except BaseException as exc:                # noqa: BLE001
            out.append((name, [(c, True) for c in checks], u"読めない: %s" % type(exc).__name__))
            continue
        res = [(c, bool(guard(check_by_name, c, mod, src))) for c in checks]
        out.append((name, res, u""))
    return out


# ======================================================================== 試験
class SealTextTest(unittest.TestCase):
    def test_a_1_the_script_constants_equal_the_seal(self):
        self.assertEqual([], seal_problems())

    def test_a_2_the_seal_file_is_the_sealed_commit_and_unchanged(self):
        self.assertEqual([], seal_history_problems())

    def test_a_3_a_changed_seal_character_turns_the_comparison_red(self):
        seal = seal_text()
        for old, new in ((u"組の数が 63 でなければ script は止まる", u"組の数が 62 でなければ script は止まる"),
                         (u"番号 1・2・3 が訓練の 3 組、番号 4〜63 が判定の 60 組", u"番号 1・2・3 が訓練の 3 組、番号 4〜63 が判定の 59 組"),
                         (u"今年の科目の名のうち、前の年の対応表に在る名は 96% 以上", u"今年の科目の名のうち、前の年の対応表に在る名は 97% 以上"),
                         (u"同じ行(数)のうち「全部同じ」は 96% 以上 100% 未満", u"同じ行(数)のうち「全部同じ」は 96% 以上 100% 以下"),
                         (u"「同じ行」で「全部同じ」の行は 44% 以上 52% 未満", u"「同じ行」で「全部同じ」の行は 44% 以上 53% 未満"),
                         (u"接頭辞が `_cor` で終わるものは半分より多い", u"接頭辞が `_cor` で終わるものは半分以上"), (u"断った組は 3 以下", u"断った組は 4 以下"),
                         (u"60 組のうち 48 組以上", u"60 組のうち 49 組以上"), (u"60 組のうち 57 組以上", u"60 組のうち 58 組以上"),
                         (u"断った組が 6 以上", u"断った組が 7 以上"), (u"`-0` と `0` は違う", u"`-0` と `0` は同じ"),
                         (u"値は同じで、単位・表示の位・精度のどれかが違う", u"値は同じで、単位・表示の位のどれかが違う"), (u"今年、要らなくなった枠 = 前の年の行の数 − 枠が今年に在る数", u"今年、要らなくなった枠 = 前の年の行の数"),
                         (u"**枠が在る行の値は別の年の値なので、値は比べない。**", u"枠が在る行の値は比べる。"), (u"予測は司令塔が立てた。盲検ではない。", u"予測は盲検で立てた。")):
            self.assertGreaterEqual(seal.count(old), 1, old)
            self.assertNotEqual([], seal_problems(seal=seal.replace(old, new)), old)

    def test_a_4_engine_is_zero_lines_from_the_seal_commit(self):
        self.assertEqual([], engine_zero_problems())

    def test_a_5_the_boundary_import_list_is_not_widened(self):
        p = os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py")
        with io.open(p, encoding="utf-8") as fh:
            body = fh.read()
        self.assertNotIn(u"type_carryover", body)
        self.assertNotIn(u"xbrl_type", body)


class OrderTest(unittest.TestCase):
    def test_d_1_the_real_history_has_the_seal_before_the_script_and_the_gate(self):
        u"""script・門のどちらかが未 commit なら赤(足した commit が無い。skip にしない)。両方 commit された後で初めて緑。"""
        self.assertEqual([], order_of())

    def test_d_2_the_order_check_lists_the_script_and_the_gate_and_not_the_record(self):
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, rel)) for rel in ORDER_FILES))
        self.assertNotIn(RECORD_REL, ORDER_FILES)


class PartsTest(unittest.TestCase):
    def test_b_1_names_keys_period_classes_content_classes_rates_and_pair_judgments(self):
        self.assertEqual([], pure_problems())

    def test_b_2_made_up_two_year_types_equal_the_hand_count(self):
        self.assertEqual([], count_problems())

    def test_b_3_the_entry_the_refusal_the_totals_and_the_judgment_numbers_by_hand(self):
        self.assertEqual([], entry_problems_gate())

    def test_b_4_the_six_flags_change_at_the_exact_boundaries_and_populations(self):
        self.assertEqual([], flags_problems())

    def test_b_5_the_hand_scenes_are_not_nearby_numbers(self):
        u"""手で決めた値が互いに違う(近くの数と同じにしない): S1 の主な数・S1 と S2 の合計・判定の数の組。"""
        h = HAND_S1
        main = [h["rows"][0][0], h["enough"][0], sum(h["same"][0]), h["content"][0], sum(h["frame"][0]), h["names"][0][0], h["names"][0][1], h["names"][0][2], h["back"][0][0], h["back"][0][3]]
        self.assertEqual(len(set(main)), len(main), main)
        self.assertEqual(len(set(h["content"])), 4)
        self.assertEqual(sum(h["content"]), sum(h["same"][0]))
        self.assertEqual(sum(h["cls"][0]), h["rows"][0][0])
        self.assertEqual(sum(h["cls"][1]), h["rows"][0][1])
        self.assertEqual(h["names"][0][1] + h["names"][0][2], h["names"][0][0])
        self.assertEqual(h["names"][0][3] + h["names"][0][4], h["names"][0][2])

    def test_b_6_the_record_shape_checks_stop_every_broken_relation(self):
        self.assertEqual([], entry_shape_problems())


class RecordTest(unittest.TestCase):
    def test_c_1_the_forbidden_checks_stop_planted_content(self):
        self.assertEqual([], clean_problems())

    def test_c_2_pairs_to_record_to_check_without_reading_the_real_cache(self):
        self.assertEqual([], build_problems())
        self.assertEqual([], e2e_problems())

    def test_c_3_check_rederives_the_totals_the_judgment_numbers_and_the_flags_from_the_pairs(self):
        self.assertEqual([], verify_problems())

    def test_c_4_dev_counts_only_the_first_three_pairs_and_writes_nothing(self):
        self.assertEqual([], dev_problems())

    def test_c_5_the_real_record_when_present_is_clean(self):
        u"""記録は本番の走りの後に書かれる。在れば中身を見て、無ければ見ない(skip にしない)。"""
        p = os.path.join(ROOT, RECORD_REL)
        if os.path.exists(p):
            rec = json.loads(read(RECORD_REL), object_pairs_hook=od)
            MS.check(root=ROOT, say=lambda *a: None)
            self.assertEqual(MS.SEAL_COMMIT, rec[u"封の commit"])
            self.assertEqual(63, rec[u"材料"][u"組の数"])
            self.assertEqual(sha_of(SCRIPT_REL), rec[u"この script の sha256"])
            self.assertEqual([x for x in rec[u"書類"] if x[u"番号"] <= 3].__len__(), 3)
        else:
            self.assertFalse(os.path.exists(p))


class WiringTest(unittest.TestCase):
    def test_e_1_imports_previous_script_calls_and_no_copies(self):
        self.assertEqual([], import_problems())

    def test_e_2_the_import_check_sees_planted_violations(self):
        base = read(SCRIPT_REL)
        self.assertNotEqual([], import_problems(base + u"\nimport socket\n"))
        self.assertNotEqual([], import_problems(base + u"\nimport urllib.request\n"))
        self.assertNotEqual([], import_problems(base + u"\nimport zipfile\n"))
        self.assertNotEqual([], import_problems(base + u"\nfrom adapters.xbrl import instance\n"))
        self.assertNotEqual([], import_problems(base + u"\nX = os.environ.get('A')\n"))
        self.assertNotEqual([], import_problems(base + u"\ndef analyze(a):\n    return None\n"))
        self.assertNotEqual([], import_problems(base + u"\ndef code_maps(a):\n    return None\n"))
        self.assertNotEqual([], import_problems(base + u"\ndef mutate(x):\n    return x\n"))
        self.assertNotEqual([], import_problems(base + u"\nX = 'run_doc('\n"))
        self.assertNotEqual([], import_problems(base + u"\nM.derive_folder(1, 2)\n"))
        self.assertNotEqual([], import_problems(base + u"\nM.process_doc(1, 2)\n"))
        self.assertNotEqual([], import_problems(base.replace(u"M.code_maps(", u"code_maps(")))
        self.assertNotEqual([], import_problems(base.replace(u"M.period_name(", u"period_name(")))
        self.assertNotEqual([], import_problems(base.replace(u'"_xk0_prior_year_draft_2026_11_22"', u'"xbrl_prior_year_draft"')))

    def test_e_3_the_gate_does_not_use_the_reserved_names(self):
        self.assertEqual([], reserved_problems())
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("ENGINE_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rel="g.py", base=d))

    def test_e_4_the_script_leaves_sys_modules_as_it_found_them_except_its_own_sibling_names(self):
        before = dict(sys.modules)
        mod = load_module(SCRIPT_REL, "xbrl_type_carryover_script_for_sysmodules_check")
        self.assertEqual([], [k for k, v in before.items() if sys.modules.get(k) is not v])
        for nm in SIBLING_NAMES:
            self.assertIn(nm, sys.modules)
        self.assertIs(mod.M, sys.modules[SIBLING_NAMES[0]])
        self.assertIs(mod.Y, sys.modules[SIBLING_NAMES[1]])
        self.assertIs(mod.W, mod.M.W)
        self.assertIs(mod.Refuse, mod.M.Refuse)
        del mod

    def test_e_5_loading_the_previous_scripts_and_this_one_in_any_order_works(self):
        self.assertEqual([], order_import_problems())

    def test_e_6_analyze_side_calls_the_previous_functions_in_order_and_uses_the_result(self):
        self.assertEqual([], wiring_problems())

    def test_e_7_the_default_places_are_outside_the_repo_and_the_gate_never_opens_them(self):
        top = os.path.realpath(REPO)
        for p in (MS.DOCS_DIR, MS.PRIOR_DIR):
            self.assertFalse(os.path.realpath(p).startswith(top + os.sep), p)
        src = read(GATE_REL)
        for m in re.finditer(r"ms\.(build_record|run|check|dev_run)\(([^)]*)\)", src):
            self.assertTrue(re.search(r"\bd\b|docs|DOCS|\*\*kw|rec_path|prior|None|pairs|root|build_fake", m.group(2)), m.group(0))

    def test_e_8_the_script_uses_no_name_of_the_injection_harness_criteria(self):
        src = read(SCRIPT_REL)
        for w in HARNESS_WORDS:
            self.assertNotIn(w, src, w)


class MutantTest(unittest.TestCase):
    def test_f_1_every_mutant_turns_its_checks_red_and_the_files_are_unchanged(self):
        before = (sha_of(SCRIPT_REL), sha_or_none(RECORD_REL))
        modules_before = dict(sys.modules)
        results = run_mutants()
        self.assertEqual(before, (sha_of(SCRIPT_REL), sha_or_none(RECORD_REL)))
        self.assertEqual([], [k for k, v in modules_before.items() if sys.modules.get(k) is not v])
        silent = [(n, c) for n, res, _w in results for c, red in res if not red]
        self.assertEqual([], silent)
        self.assertEqual(len(MUTANTS) + len(INCREMENT_MUTANTS), len(results))
        self.assertEqual([], [n for n, res, _w in results if not res])                   # 検査を 1 つも持たない変異は無い
        self.assertGreaterEqual(len(MUTANTS), 200)
        self.assertGreaterEqual(len(INCREMENT_MUTANTS), 10)

    def test_f_2_the_unmutated_script_is_green_on_every_check(self):
        base = read(SCRIPT_REL)
        mod = load_source(base)
        for name in ALL_CHECKS:
            self.assertEqual([], check_by_name(name, mod, base), name)

    def test_f_3_the_silent_mutants_are_silent_for_the_stated_reason(self):
        u"""同値の変異は、作り物の全部の検査でも、元と同じ。"""
        base = read(SCRIPT_REL)
        for name, old, new, _why in SILENT_BY_DESIGN:
            self.assertEqual(1, base.count(old), name)
            mod = load_source(base.replace(old, new))
            for c in (u"pure", u"count", u"entry", u"flags", u"build", u"clean", u"e2e", u"dev", u"verify", u"wiring"):
                self.assertEqual([], check_by_name(c, mod, None), (name, c))

    def test_f_4_the_mutant_names_are_unique_and_the_predicted_checks_exist(self):
        names = [m[0] for m in MUTANTS + INCREMENT_MUTANTS]
        self.assertEqual(len(names), len(set(names)))
        self.assertTrue(all(c in ALL_CHECKS for m in MUTANTS + INCREMENT_MUTANTS for c in m[3]))


if __name__ == "__main__":
    unittest.main()
