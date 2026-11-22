# -*- coding: utf-8 -*-
u"""封 docs/XBRL_COMPANY_EXCEL_SEAL_2026-11-22.md(XE0 ― 会社が Excel で出すとしたら、XBRL の言葉を書かない欄だけで今年の型はどれだけ決まり・黙って違い・止まるか)の封の門。

**この門は置き場を読まない**(今年の側・前の年の側の置き場・分析の本物は 1 度も開かない)。通信しない。
読むのは repo の中の封の file・script だけ。作り物の fact の並び(``build_side`` の戻りの形)と作り物の字を、本物の関数・本物の openpyxl のまま直に渡す。作り物の名・日付は全部作り物(本物の字は使わない)。

**この門が縛るもの**

1. 封の字: 封の commit(aec0496d)・封の file が commit した blob と同じ・組の数 63・訓練 3・判定 60・欄 9 つ・単位の字の表の 8 行と空の fact の 4 行・負の印の 5 字・止めの 7 つとその順・守り 4 つ・
   予測の境(XE0-1〜XE0-9。以上/以下/未満/超える)・§0 の 4 つの数・限界 8 行が、script の定数と同じ。
2. engine は封の commit から 0 行。境界の門の import 一覧にこの便の名前を足していない。
3. 3 つの工程(作る・受ける・採点)の決めを、手で数えた値と 1 つずつ照らす: 負の印・xlsx に書かない理由と順・数のセルと表示形式・日付のセル・「－」・往復(本物の openpyxl)・
   鍵の 4 つの部品・候補の 3 つの部品・止めの順(6 つの止めの全部の組み合わせ)・守り 4 つ・符号の XOR・去年が空のときの既定「順」・精度と値の式・単位の字の逆引き・正しかった止め・場面の数。
   入口の配線: ``main`` の 5 つの分岐・``score_run``・``material_of``・``check``(``verify_record`` の呼び・``rec_path``・``want``)・``dev_run`` を、作り物の 63 組と差し替えた ``Y.make_pairs``・``read_zip_side`` で本物のまま通し、
   引数の入れ替え・落とし・置き場の既定を手の値と照らす(記録は一時の folder にだけ書く)。
4. 受ける側は今年の書類も答えも無い場所で動く(関数の引数に取らない・AST に答えを読む名が無い・答えの folder が無い場所で動く)。採点は受ける側の出力と答えを比べる(答え同士ではない)。
5. 訓練の 3 組と判定の 60 組を分け(番号 3 / 4 の境)、予測 XE0-1〜XE0-9 と §0 の旗を、境の両側で手の値と照らす。記録: 排他で書く・書く前と書いた後に禁止のものを検査する・``--check`` が導き直す。
6. script の import は標準ライブラリ・zipfile・openpyxl と importlib だけ(engine を読む import を足さない)。前の便の script は importlib で一意の名で読み、関数は呼ぶ(写さない)。
7. 行頭の名前: この門は ``ENGINE_LATER``・``UNTOUCHED``・``PIN_DEF``・``LATER_ENGINE_COMMITS``・``FROZEN_LATER``・``ENGINE_TRANSITIONS`` を行頭に置かない。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``。script の字を 1 か所替えた版を memory の中に作る。file は書き換えない)。
黙る変異は ``SILENT_BY_DESIGN`` に理由とともに置き、「黙ること」自体を別の試験で縛る。
記録(``fixtures/xbrl/cd8/company_excel_2026-11-22.json``)は本番の走りの後に書かれる。記録が在れば中身を見て、無ければ見ない(skip にしない。見る作りが「在れば」)。
"""
import ast
import collections
import contextlib
import hashlib
import importlib.util
import io
import itertools
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
    mod = types.ModuleType("xbrl_company_excel_mutant")
    mod.__file__ = os.path.join(ROOT, SCRIPT_REL)
    before = dict(sys.modules)
    try:
        exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    finally:
        for k, v in before.items():
            if sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


SEAL_REL = "docs/XBRL_COMPANY_EXCEL_SEAL_2026-11-22.md"
SEAL_COMMIT_SHORT = "aec0496d"                # 封の commit(literal に留める。script の定数と違えば赤)
SCRIPT_REL = "measure/xbrl_company_excel_2026-11-22.py"
GATE_REL = "tests/measure/test_xbrl_company_excel_seal.py"
RECORD_REL = "fixtures/xbrl/cd8/company_excel_2026-11-22.json"
MS = load_module(SCRIPT_REL, "xbrl_company_excel_script_for_seal_gate")
PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_company_excel_seal")      # 順序・履歴の部品。門としては走らせない
ORDER_FILES = (SCRIPT_REL, GATE_REL)          # 記録の順序は記録が在るときの結果の門に置く
od = collections.OrderedDict
JPY, USD = u"通貨:JPY", u"通貨:USD"
SHARES, PURE, JPYPS = u"株", u"純数", u"通貨:JPY÷株"
NONE_V = u"無い"
STOP_ORDER = (u"候補が 2 つ以上", u"表の頭が違う", u"期が違う", u"番号つき", u"単位が違う", u"符号の向きが 2 通り")


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
    u"""fn が止まれば(``SystemExit``。``ms.Stop`` を含む。前の便の script の ``Stop`` も同じ親)True。投げなければ False。別の例外は投げ直す。"""
    try:
        fn(*a, **kw)
    except SystemExit:
        return True
    return False


def raises(exc, fn, *a, **kw):
    u"""fn が ``exc`` を投げれば True。"""
    try:
        fn(*a, **kw)
    except exc:
        return True
    return False


class Temp(object):
    def __enter__(self):
        self.d = tempfile.mkdtemp(prefix="xe0_gate_")
        return self.d

    def __exit__(self, *a):
        shutil.rmtree(self.d, ignore_errors=True)


# ======================================================================== 1. 封の字
def seal_text():
    return read(SEAL_REL)


EXPECT_BOUNDS = od([("XE0-1", (74.0, True, None, False)), ("XE0-2", (None, False, 0.5, True)), ("XE0-3", (None, False, 30, True)), ("XE0-4", (16.0, True, 26.0, True)),
                    ("XE0-5", (40.0, True, 65.0, True)), ("XE0-6", (None, False, 2.0, True)), ("XE0-7", (None, False, 1.0, True)), ("XE0-8", (35, True, None, False)),
                    ("XE0-9", (None, False, 2, True))])
SEAL_BOUND_TEXT = {
    "XE0-1": (u"決めて全部同じ ÷ D は **74.0% 以上**", u"74.0% 未満なら外れ"), "XE0-2": (u"決めたが違う ÷ D は **0.5% 以下で、0 ではない(1 fact 以上)**", u"0.5% を超えるか、0 なら外れ"),
    "XE0-3": (u"「符号だけ違う」は **30 fact 以下**", u"31 以上なら外れ"), "XE0-4": (u"止めた ÷ D は **16.0% 以上 26.0% 以下**", u"外なら外れ"),
    "XE0-5": (u"「正しかった止め」は **40% 以上 65% 以下**", u"外なら外れ"), "XE0-6": (u"合わせて **1 fact 以上で、D の 2.0% 以下**", u"0 か、2.0% を超えるなら外れ"),
    "XE0-7": (u"合わせて **行の中の数の fact の 1.0% 以下**", u"超えるなら外れ"), "XE0-8": (u"60 本のうち **35 本以上**", u"34 本以下なら外れ"),
    "XE0-9": (u"95% 以上の書類は **2 本以下**", u"3 本以上なら外れ")}
#: 予測の境で値を替える(下限・上限の中・ちょうど・すぐ外)。(名前, [(値, 当たりか)])。値は % か数
BOUND_CASES = od([
    ("XE0-1", [(74.0, True), (73.9, False), (100, True)]), ("XE0-2", [(0.5, True), (0.6, False), (0.1, True)]), ("XE0-3", [(30, True), (31, False), (0, True)]),
    ("XE0-4", [(16.0, True), (15.9, False), (26.0, True), (26.1, False)]), ("XE0-5", [(40.0, True), (39.9, False), (65.0, True), (65.1, False)]),
    ("XE0-6", [(2.0, True), (2.1, False)]), ("XE0-7", [(1.0, True), (1.1, False)]), ("XE0-8", [(35, True), (34, False)]), ("XE0-9", [(2, True), (3, False), (0, True)])])


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
    if ms.SCRIPT_REL != SCRIPT_REL or ms.RECORD_REL != RECORD_REL:
        out.append(u"script・記録の path が封・門と違う")
    if ms.PAIRS_WANT != 63 or u"組の数が 63 でなければ script は止まる" not in seal:
        out.append(u"組の数 63 が封と違う")
    if (ms.SEEN_MAX_NO, ms.TRAIN_WANT, ms.JUDGE_WANT, tuple(ms.DEV_NOS)) != (3, 3, 60, (1, 2, 3)) or u"番号 1・2・3 が訓練、番号 4〜63 が判定の 60 組" not in seal:
        out.append(u"訓練の 3 組・判定の 60 組の分けが封と違う")
    if ms.DOCS_WANT != 67:
        out.append(u"今年の側の本数 67 が便 XY0 の字と違う")
    if (ms.SHEET_DOC, ms.SHEET_NUM) != (u"書類", u"数") or u"シート「書類」" not in seal or u"シート「数」" not in seal:
        out.append(u"シートの名が封と違う")
    if len(ms.HEAD_DOC) != 3 or len(ms.HEAD_NUM) != 9 or u"欄は 9 つ" not in seal:
        out.append(u"欄の数が封と違う")
    for w, key in zip((u"当期の始まりの日", u"当期の終わりの日", u"提出の日"), ms.HEAD_DOC):
        if w != key or w not in seal:
            out.append(u"書類のシートの欄が封と違う: %s" % w)
    for w, key in zip((u"見出しの字", u"表の番号", u"行の字", u"列の番号", u"表の頭の印", u"金額", u"期の始まりの日", u"期の終わりの日", u"単位の字"), ms.HEAD_NUM):
        if w != key or w not in seal:
            out.append(u"数のシートの欄が封と違う: %s" % w)
    if ms.NIL_CELL != u"－" or u"字「－」" not in seal:
        out.append(u"空の fact の字が封と違う")
    if ms.MARKS != u"△▲-－−" or u"「△」「▲」「-」「－」「−」のどれか" not in seal:
        out.append(u"負の印の字が封と違う")
    if ms.MAX_DIGITS != 15 or u"有効数字が 15 桁を超える" not in seal:
        out.append(u"有効数字の桁の数が封と違う")
    line_ = [ln for ln in seal.splitlines() if ln.startswith(u"- **xlsx に書かない fact**")]
    pos_ = [line_[0].find(w) if line_ else -1 for w in (u"突き合わせの外", u"行の字が空", u"型の外", u"単位が書けない", u"有効数字が 15 桁を超える")]
    if tuple(ms.EXCLUDES) != (u"行の字が空", u"型の外", u"単位が書けない", u"有効数字が 15 桁を超える") or min(pos_) < 0 or pos_ != sorted(pos_):
        out.append(u"xlsx に書かない理由の並びが封と違う")
    want_unit = u"通貨:JPY × 0 → 「円」、× 3 → 「千円」、× 6 → 「百万円」。株 × 0 → 「株」、× 3 → 「千株」。純数 × 0 → 「数」、× −2 → 「％」。通貨:JPY÷株 × 0 → 「円/株」"
    want_form = u"(通貨:JPY → 「円」、株 → 「株」、純数 → 「数」、通貨:JPY÷株 → 「円/株」)"
    if want_unit not in seal or want_form not in seal:
        out.append(u"単位の字の表が封に無い")
    if set(ms.UNIT_ROWS) != set([(JPY, 0, u"円"), (JPY, 3, u"千円"), (JPY, 6, u"百万円"), (SHARES, 0, u"株"), (SHARES, 3, u"千株"), (PURE, 0, u"数"), (PURE, -2, u"％"), (JPYPS, 0, u"円/株")]) or len(ms.UNIT_ROWS) != 8:
        out.append(u"単位の字の表(単位の形 × 表示の位)が封と違う")
    if set(ms.UNIT_FORM_ROWS) != set([(JPY, u"円"), (SHARES, u"株"), (PURE, u"数"), (JPYPS, u"円/株")]) or len(ms.UNIT_FORM_ROWS) != 4:
        out.append(u"空の fact の単位の字の表が封と違う")
    if tuple(ms.STOPS)[:1] != (u"去年に無い行",) or tuple(ms.STOPS)[1:] != STOP_ORDER:
        out.append(u"止めの理由の並びが封と違う")
    pos = -1
    for k, w in enumerate((u"止め「去年に無い行」", u"止め「候補が 2 つ以上」", u"止め「表の頭が違う」", u"止め「期が違う」", u"止め「番号つき」", u"止め「単位が違う」", u"止め「符号の向きが 2 通り」")):
        i = seal.find(w)
        if i <= pos:
            out.append(u"封に止めの字が無い・順が違う: %s" % w)
        pos = i
    if tuple(ms.GUARDS) != (u"表の頭が違う", u"期が違う", u"番号つき", u"単位が違う") or u"守り G: 表の頭の印" not in seal or u"守り G1:" not in seal or u"守り G3:" not in seal or u"守り G2:" not in seal:
        out.append(u"守り 4 つが封と違う")
    if tuple(ms.FIELDS) != (u"名", u"個別か既定か", u"区分", u"期の日", u"期の種類", u"値", u"単位の形", u"表示の位", u"精度", u"空か") or u"(名・個別か既定か・区分・期の日・期の種類・値・単位の形・表示の位・精度・空か)" not in seal:
        out.append(u"採点で比べる欄が封と違う")
    for w in (u"**決めて全部同じ**: 決めた欄の全部が答えと同じ", u"精度 = −(表示の位) + (セルの表示形式の小数の桁の数)、値 = |金額| × 10^(表示の位) に符号(金額が負)XOR(去年の符号の向きが逆)",
              u"**去年の符号の向きが 1 つも無い(去年は空だった)ときは「順」とする。**", u"金額が「－」なら空", u"期の日と期の種類は xlsx の日付(1 つなら時点・2 つなら期間)",
              u"**表に無い組は「書けない」**", u"受ける側は、金額が「－」の行では単位の字から単位の形だけを決める", u"最初に数の fact が出る行より前の行の字", u"接頭辞を除いた名で見る",
              u"鍵が去年の表に無い → 止め「去年に無い行」", u"**D** = 判定の 60 組の今年の側で、xlsx に書いた行の数", u"受ける側の関数は今年の zip も答えも引数に取らない",
              u"違うのは値だけで、絶対値は同じ", u"「正しかった止め」", u"去年の表の鍵のうち今年の xlsx に 1 行も無いもの(無くなった行)",
              u"数えるだけ", u"**負の印**", u"**符号の向き**", u"fact のタグより前に在る最後の `<td` か `<th` の開きタグの後ろから fact のタグの手前までの字を取り"):
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
    if (ms.MIN_DIFF, ms.MIN_G12, ms.DOC_SAME_PCT) != (1, 1, 95.0):
        out.append(u"1 fact 以上の下限・95% の字が封と違う")
    if dict(ms.SEAL_TRAIN) != {u"行の中の数の fact": 3434, u"決めて全部同じ": 2636, u"決めたが違う": 0, u"止めた": 669} or u"行の中の数の fact 3434・決めて全部同じ 2636・決めたが違う 0・止めた 669" not in seal:
        out.append(u"§0 の 4 つの数が封と違う")
    sec7 = seal.split(u"## §7", 1)[-1]
    lines7 = [ln[2:] for ln in sec7.splitlines() if ln.startswith(u"- ")]
    if len(lines7) != 8 or list(ms.LIMITS) != lines7:
        out.append(u"限界の 8 行が封 §7 と違う")
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


# ======================================================================== 作り物の材料(``build_side`` の戻りの形)
DEC_C = od([("start", u"2030-04-01"), ("end", u"2031-03-31"), ("filing", u"2031-06-30")])       # 今年の書類の決め(作り物)
DEC_P = od([("start", u"2029-04-01"), ("end", u"2030-03-31"), ("filing", u"2030-06-30")])       # 前の年の書類の決め
CUR_DUR = [u"2030-04-01", u"2031-03-31"]
PRI_DUR = [u"2029-04-01", u"2030-03-31"]
HM, HM2 = u"頭甲", u"頭乙"


def mk(T, td=1, h=u"見出し甲", th=0, hmark=HM, name=u"xa_cor:Item", target=u"既定", dims=(), pkind="duration", dates=None, pn=u"CurrentYear",
       value=u"1000000", form=JPY, shift=6, prec=-6, nil=False, content=u"1", neg=False, sign=None, bad=False):
    u"""行の中の数の fact 1 つ(``build_side`` の ``records`` の 1 つの形)。"""
    if nil:
        value, shift, prec, content = NONE_V, None, None, u""
    return od([("h", h), ("th", th), ("T", T), ("td", td), ("hmark", hmark), ("neg", neg), ("name", name), ("target", target),
               ("dims", tuple(tuple(d) for d in dims)), ("pkind", pkind), ("dates", list(dates if dates is not None else CUR_DUR)), ("pn", pn), ("value", value),
               ("form", form), ("shift", shift), ("prec", prec), ("nil", nil), ("content", content), ("sign", sign), ("bad", bad)])


def side_of(records, dec, inrow=None, files_out=0, ix_out=0, inrow_out=0):
    return od([("dec", dict(dec)), ("records", list(records)), ("stats", od([("inrow", len(records) if inrow is None else inrow), ("files_out", files_out), ("ix_out", ix_out), ("inrow_out", inrow_out)]))])


def prior_s1():
    u"""場面 S1 の前の年の側。"""
    N = u"xa_cor:Item"
    p = []
    p.append(mk(u"行01", name=N + u"1"))
    p.append(mk(u"行02", name=N + u"2", neg=True, sign=u"-", value=u"-1000000"))
    p.append(mk(u"行03", name=N + u"3", sign=u"-", value=u"-1000000"))
    p.append(mk(u"行04", name=N + u"4a"))
    p.append(mk(u"行04", name=N + u"4b"))
    p.append(mk(u"行05", name=N + u"5"))
    p.append(mk(u"行06", name=N + u"6"))
    p.append(mk(u"行07", name=N + u"7", dims=[(u"xa_cor:Ax1", u"xb:No1Member")]))
    p.append(mk(u"行08", name=N + u"8"))
    p.append(mk(u"行09", name=N + u"9"))
    p.append(mk(u"行09", name=N + u"9", sign=u"-", value=u"-1000000"))
    p.append(mk(u"行10", name=N + u"10", nil=True))
    p.append(mk(u"行11", name=N + u"11", nil=True))
    p.append(mk(u"行11", name=N + u"11", sign=u"-", value=u"-1000000"))
    p.append(mk(u"行12", name=u"xa_cor:BadName", bad=True))
    p.append(mk(u"行12", name=N + u"12"))
    p.append(mk(u"行13", name=N + u"13", bad=True))
    p.append(mk(u"", name=N + u"14"))
    p.append(mk(u"行15", name=N + u"15"))
    p.append(mk(u"行16", name=N + u"16"))
    p.append(mk(u"行17", h=u"", name=N + u"17"))
    p.append(mk(u"行18", name=N + u"18", dims=[(u"xa_cor:Ax2", u"Row12AMember")]))
    p.append(mk(u"行19", name=N + u"19", dims=[(u"xa_cor:No1Axis", u"xb:XNo1Member")]))
    p.append(mk(u"行20", name=N + u"20", dims=[(u"xa_cor:Ax3", u"xb:No1MemberX")]))
    p.append(mk(u"行21", name=N + u"21"))
    p.append(mk(u"行22", name=N + u"22"))
    p.append(mk(u"行23", name=N + u"23"))
    p.append(mk(u"行24", name=N + u"24", shift=3, prec=-3))
    p.append(mk(u"行25", name=N + u"25", form=PURE, shift=-2, prec=2))
    p.append(mk(u"行26", name=N + u"26", form=JPYPS, shift=0, prec=0))
    p.append(mk(u"行27", name=N + u"27", pkind="instant", dates=[u"2030-03-31"]))
    p.append(mk(u"行28", name=N + u"28", neg=True))
    for k in (29, 30, 31, 32):                                                 # 今年に 1 行も無い去年の鍵(無くなった行)
        p.append(mk(u"行%d" % k, name=N + str(k)))
    return side_of(p, DEC_P)


def cur_s1():
    u"""場面 S1 の今年の側(31 行)。コメントは手で決めた「受ける側の決め」。"""
    N = u"xa_cor:Item"
    c = []
    c.append(mk(u"行01", name=N + u"1"))                                                       # 1 決めて全部同じ
    c.append(mk(u"行02", name=N + u"2", neg=True, sign=u"-", value=u"-1000000"))                # 2 同じ(負の印と sign が同じ・去年も同じ向き)
    c.append(mk(u"行03", name=N + u"3", sign=u"-", value=u"-1000000"))                          # 3 同じ(去年は向きが逆 → 符号を反転して戻す)
    c.append(mk(u"行04", name=N + u"4a"))                                                       # 4 止め 候補が 2 つ以上
    c.append(mk(u"行05", name=N + u"5", hmark=HM2))                                             # 5 止め 表の頭(止めなければ同じ)
    c.append(mk(u"行06", name=N + u"6", dates=PRI_DUR, pn=u"Prior1Year"))                       # 6 止め 期(止めなければ同じ)
    c.append(mk(u"行06", name=N + u"6", pkind="instant", dates=[u"2030-05-05"], pn=None))       # 7 止め 期(期の名が作れない。止めなければ同じ)
    c.append(mk(u"行07", name=u"xa_cor:Other7", dims=[(u"xa_cor:Ax1", u"xb:No1Member")]))       # 8 止め 番号つき(止めなければ名が違う)
    c.append(mk(u"行08", name=N + u"8", content=u"5", value=u"5", form=SHARES, shift=0, prec=0))  # 9 止め 単位(止めなければ同じ)・表示の位が違う
    c.append(mk(u"行09", name=N + u"9"))                                                        # 10 止め 符号の向きが 2 通り
    c.append(mk(u"行09", name=N + u"9", nil=True))                                              # 11 同じ(空は符号の向きを見ない)
    c.append(mk(u"行10", name=N + u"10"))                                                       # 12 同じ(去年が空 → 既定の順)
    c.append(mk(u"行10", name=N + u"10", neg=True, sign=u"-", value=u"-1000000"))               # 13 同じ(既定の順)
    c.append(mk(u"行10", name=N + u"10", sign=u"-", value=u"-1000000"))                         # 14 違う(値だけ・符号だけ・既定の順を使った)
    c.append(mk(u"行10", name=N + u"10", content=u"0", value=u"-0", neg=True, sign=u"-"))      # 15 違う(値だけ・符号だけ・答えが -0・既定の順)
    c.append(mk(u"行11", name=N + u"11", sign=u"-", value=u"-1000000"))                         # 16 同じ(去年は空と逆向き 1 つ → 逆)
    c.append(mk(u"行12", name=N + u"12"))                                                       # 17 同じ(型の外の去年の fact は表に入らない)
    c.append(mk(u"行13", name=N + u"13"))                                                       # 18 止め 去年に無い行(去年は型の外だけ)
    c.append(mk(u"行99", name=N + u"99"))                                                       # 19 止め 去年に無い行
    c.append(mk(u"行17", h=None, name=N + u"17"))                                               # 20 同じ(見出しの字が空は無いと同じ)
    c.append(mk(u"行18", name=N + u"18", dims=[(u"xa_cor:Ax2", u"Row12AMember")]))              # 21 止め 番号つき(接頭辞なしの member。止めなければ同じ)
    c.append(mk(u"行19", name=N + u"19", dims=[(u"xa_cor:No1Axis", u"xb:XNo1Member")]))         # 22 同じ(番号つきは軸でなく member の名で見る・member は形が違う)
    c.append(mk(u"行20", name=N + u"20", dims=[(u"xa_cor:Ax3", u"xb:No1MemberX")]))             # 23 同じ(No1MemberX は Member で終わらない)
    c.append(mk(u"行21", name=N + u"21", content=u"7", value=u"7000", shift=3, prec=-3))        # 24 同じ・去年と表示の位が違う
    c.append(mk(u"行22", name=u"xa_cor:Changed22"))                                             # 25 違う(名)
    c.append(mk(u"行23", name=N + u"23", target=u"個別", dims=[(u"xa_cor:AxN", u"xb:MbN")]))     # 26 違う(個別か既定か・区分)
    c.append(mk(u"行24", name=N + u"24", content=u"12.5", value=u"12500", shift=3, prec=-2))   # 27 同じ(精度 = -3 + 1)
    c.append(mk(u"行25", name=N + u"25", content=u"3.14", value=u"0.0314", form=PURE, shift=-2, prec=4))     # 28 同じ(精度 = 2 + 2)
    c.append(mk(u"行26", name=N + u"26", content=u"250", value=u"250", form=JPYPS, shift=0, prec=0))        # 29 同じ
    c.append(mk(u"行27", name=N + u"27", pkind="instant", dates=[u"2031-03-31"], pn=u"CurrentYear"))        # 30 同じ(時点)
    c.append(mk(u"行28", name=N + u"28", neg=True))                                             # 31 同じ(去年は逆向き・負の印だけで sign なし → 反転して正)
    return side_of(c, DEC_C)


#: 場面 S1 の手の決め: 行ごとの (止めの理由か空, 違う欄の並び, 去年が空で既定の順を使った, 去年と表示の位が違う)
S1_ROWS = [
    (u"", [], False, False), (u"", [], False, False), (u"", [], False, False), (u"候補が 2 つ以上", None, False, False), (u"表の頭が違う", None, False, False),
    (u"期が違う", None, False, False), (u"期が違う", None, False, False), (u"番号つき", None, False, False), (u"単位が違う", None, False, True), (u"符号の向きが 2 通り", None, False, False),
    (u"", [], False, False), (u"", [], True, False), (u"", [], True, False), (u"", [u"値"], True, False), (u"", [u"値"], True, False),
    (u"", [], False, False), (u"", [], False, False), (u"去年に無い行", None, False, False), (u"去年に無い行", None, False, False), (u"", [], False, False),
    (u"番号つき", None, False, False), (u"", [], False, False), (u"", [], False, False), (u"", [], False, True), (u"", [u"名"], False, False),
    (u"", [u"個別か既定か", u"区分"], False, False), (u"", [], False, False), (u"", [], False, False), (u"", [], False, False), (u"", [], False, False), (u"", [], False, False)]
#: 守りの止めのうち止めなければ全部同じだった行(S1 の行の番号 1 始まり)
S1_GUARD_OK = {5, 6, 7, 9, 21}
HAND_S1_ENTRY = {
    u"D": 31, u"決めて全部同じ": 17, u"決めたが違う": 4, u"止めた": 10, u"無くなった行": 6,
    u"止めた理由ごと": od([(u"去年に無い行", 2), (u"候補が 2 つ以上", 1), (u"表の頭が違う", 1), (u"期が違う", 2), (u"番号つき", 2), (u"単位が違う", 1), (u"符号の向きが 2 通り", 1)]),
    u"守りの止め": od([(u"守り G 表の頭", (1, 1)), (u"守り G1 期", (2, 2)), (u"守り G3 番号つき", (2, 1)), (u"守り G2 単位", (1, 1))]),
    u"欄ごと": od([(u"名", 1), (u"個別か既定か", 1), (u"区分", 1), (u"期の日", 0), (u"期の種類", 0), (u"値", 2), (u"単位の形", 0), (u"表示の位", 0), (u"精度", 0), (u"空か", 0)]),
    u"符号だけ違う": 2, u"符号だけ違うのうち答えの値が符号つきの 0": 1, u"去年が空で既定の順を使った": 2,
    u"場面": od([(u"負の印あり", 4), (u"表示の数が 0", 1), (u"空", 1), (u"符号の向きが逆", 4)]),
    u"表示の位が違う": (2, 1, 0, 1)}


def run_scene(ms, prior, cur, d, n=1):
    u"""作り物の 2 年 → (xlsx の行, 答えの行, 作る側の数, 受ける側の出力)。xlsx は ``d`` の下に本物の openpyxl で書いて読み直す。"""
    rows, answers, cnt = ms.sheet_rows_of(cur)
    path = os.path.join(d, u"%02d.xlsx" % n)
    ms.write_xlsx(path, cur["dec"], rows)
    return rows, answers, cnt, ms.receive_pair(path, prior)


def diff_names(dec, ans):
    u"""門の側の比べ(script の関数を使わない)。"""
    keys = ((u"名", "name"), (u"個別か既定か", "target"), (u"区分", "dims"), (u"期の日", "period"), (u"期の種類", "pkind"), (u"値", "value"), (u"単位の形", "form"), (u"表示の位", "shift"), (u"精度", "prec"), (u"空か", "nil"))
    return [k for k, f in keys if dec[f] != ans[f]]


# ======================================================================== 2. 部品
def pure_problems(ms=None):
    ms = ms or MS
    out = []
    F = u'<ix:nonFraction name="x:A" contextRef="c1">5</ix:nonFraction>'

    def neg(before, row=None):
        row = row if row is not None else u"<tr><td>科目</td><td>" + before + F + u"</td></tr>"
        return ms.negative_mark(row, row.rindex(u"<ix:nonFraction"))
    # 負の印: 5 つの字を 1 つずつ(末尾の 1 字)
    for ch in u"△▲-－−":
        if not neg(ch):
            out.append(u"負の印の字を見ない: %r" % ch)
        if not neg(u"&#160;" + ch + u"&#160;") or not neg(u" " + ch + u"\u3000") or not neg(u"\u00a0" + ch + u"\u00a0") or not neg(ch + u"\u3000"):
            out.append(u"負の印の前後の空白(&#160;・空白・U+3000・U+00A0)を除かない: %r" % ch)
        if not neg(u"<span>" + ch + u"</span>"):
            out.append(u"負の印のタグを除かない: %r" % ch)
        if neg(ch + u"1"):
            out.append(u"負の印が末尾の 1 字でない(後ろに字が在るのに印と読む): %r" % ch)
    for what, before in ((u"空", u""), (u"空白だけ", u" \u3000\u00a0&#160;"), (u"プラス", u"+"), (u"数字", u"1"), (u"注", u"(注1)"), (u"開き括弧", u"("), (u"語", u"純"), (u"全角のマイナスに似た長音", u"ー"), (u"ハイフンに似た字", u"‐"),
                         (u"文字の途中の印", u"△注")):
        if neg(before):
            out.append(u"負の印でない字を印と読む: %s" % what)
    row = u'<tr><td style="margin-left:-1px">科目</td><td class="a-b" style="width:-3px">' + F + u"</td></tr>"
    if neg(u"", row):
        out.append(u"タグの属性の中の - を印と読む")
    row = u'<tr><td>△<ix:nonFraction name="x:Z" contextRef="c0">9</ix:nonFraction></td><td>' + F + u"</td></tr>"
    if neg(u"", row) or neg(u"", row.replace(u"</td><td>" + F, u"</td><td> " + F)) or neg(u"", row.replace(u"</td><td>" + F, u"</td><td>1" + F)):
        out.append(u"前の欄の印を今の欄の印と読む(最後の開きタグの後ろだけを見る)")
    row = u'<tr><td><ix:nonFraction name="x:Z" contextRef="c0">9</ix:nonFraction>' + u"△" + F + u"</td></tr>"
    if not ms.negative_mark(row, row.rindex(u"<ix:nonFraction")):
        out.append(u"同じ欄の中の前の fact の後ろの印を見ない")
    row = u'<tr><td>科目</td>' + F + u"</tr>"
    if ms.negative_mark(u"<tr>1" + F, 5) or not ms.negative_mark(u"<tr>△" + F, 5) or not ms.negative_mark(u"<tr>△" + F, 5):
        out.append(u"開きタグが無いときは行の頭から見る")
    row = u'<tr><td>科目△</td>' + F + u"</tr>"
    if not ms.negative_mark(row, row.index(u"<ix:nonFraction")):
        out.append(u"最後の開きタグの後ろから fact の手前までの字(閉じた欄の字を含む)を見ない")
    row = u'<tr><th>△</th><th>' + F + u"</th></tr>"
    if neg(u"", row):
        out.append(u"<th の開きタグを欄の区切りに見ない")
    row = u'<tr><td>△</td><td>1</td><th>' + F + u"</th></tr>"
    if neg(u"", row):
        out.append(u"<th の開きタグを欄の区切りに見ない(td と th が混ざる行)")
    row = u'<tr><td>科目</td><th>△' + F + u"</th></tr>"
    if not neg(u"", row):
        out.append(u"<th の欄の中の印を見ない")
    # 字・桁
    for content, want in ((u"1,234", 4), (u"0.05", 1), (u"000", 0), (u"123456789012345", 15), (u"1234567890123456", 16), (u"1,234,567,890,123.45", 15), (u"1,234,567,890,123.456", 16), (u"0.000000000000001", 1), (u"", 0), (u"0", 0)):
        if ms.sig_digits(content) != want:
            out.append(u"有効数字の桁の数が違う: %s -> %s" % (content, ms.sig_digits(content)))
    for content, want in ((u"1,234", 0), (u"12.5", 1), (u"3.14", 2), (u"0.00001", 5), (u"1,000.0", 1)):
        if ms.frac_digits(content) != want:
            out.append(u"小数の桁の数が違う: %s" % content)
    if ms.hkey(u"") is not None or ms.hkey(None) is not None or ms.hkey(u"甲") != u"甲":
        out.append(u"見出しの字の鍵が違う(空の字は無いと同じ)")
    r = mk(u"行01", h=u"", th=3, td=5)
    if ms.key_of(r) != (None, 3, u"行01", 5):
        out.append(u"鍵が (見出し・表の番号・行の字・列の番号) でない: %s" % (ms.key_of(r),))
    for a, b in (("h", u"他"), ("th", 4), ("T", u"行02"), ("td", 6)):
        r2 = dict(r)
        r2[a] = b
        if ms.key_of(r2) == ms.key_of(r):
            out.append(u"鍵が %s の違いを見ない" % a)
    r3 = dict(r)
    r3.update(hmark=u"他", name=u"他", value=u"9", neg=True)
    if ms.key_of(r3) != ms.key_of(r):
        out.append(u"鍵が表の頭の印・名・値を見ている")
    for name, want in ((u"xb:No1Member", u"No1Member"), (u"No1Member", u"No1Member"), (u"a:b:c", u"b:c"), (u"", u"")):
        if ms.local_name(name) != want:
            out.append(u"局所名が違う: %r" % name)
    for dims, want in (([(u"a:Ax", u"b:No1Member")], True), ([(u"a:Ax", u"b:Row12AMember")], True), ([(u"a:Ax", u"No5Member")], True), ([(u"a:Ax", u"b:XNo1Member")], False), ([(u"a:Ax", u"b:No1MemberX")], False),
                       ([(u"a:No1Member", u"b:Mb")], False), ([], False), ([(u"a:Ax", u"b:Mb"), (u"c:Ay", u"d:No2Member")], True), ([(u"a:Ax", u"b:NoMember")], False), ([(u"a:Ax", u"b:Row1Member")], True)):
        if ms.numbered_cand((u"n", u"既定", tuple(dims))) != want:
            out.append(u"番号つきの member の判定が違う: %s" % (dims,))
    # 単位の字の表(1 行ずつ)・空の fact の字
    for form, shift, want in ((JPY, 0, u"円"), (JPY, 3, u"千円"), (JPY, 6, u"百万円"), (SHARES, 0, u"株"), (SHARES, 3, u"千株"), (PURE, 0, u"数"), (PURE, -2, u"％"), (JPYPS, 0, u"円/株")):
        r = mk(u"行01", form=form, shift=shift, prec=0)
        if ms.exclusion_of(r) is not None:
            out.append(u"書ける単位が書けないと読まれる: %s %s" % (form, shift))
        rows, _a, _c = ms.sheet_rows_of(side_of([r], DEC_C))
        if len(rows) != 1 or rows[0]["unit"] != want:
            out.append(u"単位の字が違う: %s %s" % (form, shift))
        if ms.LETTER_TO_UNIT.get(want) != (form, shift):
            out.append(u"単位の字の逆引きが違う: %s" % want)
    for form, shift in ((JPY, 1), (JPY, -2), (SHARES, 6), (PURE, 3), (PURE, 2), (JPYPS, 3), (USD, 0), (USD, 6), (u"通貨:USD÷株", 0), (SHARES, -2), (u"", 0)):
        if ms.exclusion_of(mk(u"行01", form=form, shift=shift)) != u"単位が書けない":
            out.append(u"表に無い単位の組が書けないにならない: %s %s" % (form, shift))
    for form, want in ((JPY, u"円"), (SHARES, u"株"), (PURE, u"数"), (JPYPS, u"円/株")):
        rows, _a, _c = ms.sheet_rows_of(side_of([mk(u"行01", form=form, nil=True)], DEC_C))
        if len(rows) != 1 or rows[0]["unit"] != want or rows[0]["amount"] != u"－":
            out.append(u"空の fact の単位の字が単位の形だけから決まらない: %s" % form)
    for form in (USD, u"通貨:USD÷株", u""):
        if ms.exclusion_of(mk(u"行01", form=form, nil=True)) != u"単位が書けない":
            out.append(u"空の fact の書けない単位の形が書けないにならない: %s" % form)
    if ms.LETTER_TO_FORM.get(u"千円") != JPY or ms.LETTER_TO_FORM.get(u"百万円") != JPY or ms.LETTER_TO_FORM.get(u"千株") != SHARES or ms.LETTER_TO_FORM.get(u"％") != PURE or ms.LETTER_TO_FORM.get(u"円/株") != JPYPS:
        out.append(u"単位の字から単位の形だけを決める逆引きが違う")
    # xlsx に書かない理由と順(重ならない)
    for what, r, want in ((u"行の字が空", mk(u""), u"行の字が空"), (u"型の外", mk(u"行01", bad=True), u"型の外"), (u"単位", mk(u"行01", form=USD), u"単位が書けない"),
                          (u"15 桁を超える", mk(u"行01", content=u"1234567890123456", value=u"1", prec=0, shift=0, form=JPY), u"有効数字が 15 桁を超える"),
                          (u"15 桁ちょうど", mk(u"行01", content=u"123456789012345", shift=0, prec=0), None), (u"15 桁を超えるが小数", mk(u"行01", content=u"1,234,567,890,123.456", shift=0, prec=-3), u"有効数字が 15 桁を超える"),
                          (u"空と型の外", mk(u"", bad=True), u"行の字が空"), (u"型の外と単位", mk(u"行01", bad=True, form=USD), u"型の外"), (u"単位と桁", mk(u"行01", form=USD, content=u"1234567890123456"), u"単位が書けない"),
                          (u"空の fact は桁を見ない", mk(u"行01", nil=True), None), (u"正常", mk(u"行01"), None)):
        if ms.exclusion_of(r) != want:
            out.append(u"xlsx に書かない理由が違う: %s -> %s" % (what, ms.exclusion_of(r)))
    # 数のセル
    for content, neg_, want in ((u"1,234", False, (1234, u"0")), (u"1,234", True, (-1234, u"0")), (u"12.5", False, (12.5, u"0.0")), (u"12.5", True, (-12.5, u"0.0")), (u"3.14", False, (3.14, u"0.00")),
                                (u"12.50", True, (-12.5, u"0.00")), (u"0", False, (0, u"0")), (u"0.00001", False, (0.00001, u"0.00000")), (u"999999999999999", False, (999999999999999, u"0")), (u"1,000.0", False, (1000.0, u"0.0"))):
        v, fmt = ms.amount_cell(mk(u"行01", content=content, neg=neg_))
        if (v, fmt) != want or type(v) is not type(want[0]):
            out.append(u"数のセルが違う: %s %s -> %r %s" % (content, neg_, v, fmt))
    if ms.amount_cell(mk(u"行01", nil=True)) != (u"－", "General"):
        out.append(u"空の fact のセルが「－」でない")
    if ms.day_of(u"2030-04-01").isoformat() != u"2030-04-01" or ms.day_of(u"2031-12-31").day != 31:
        out.append(u"日の字が日付にならない")
    # 数のセルを読む(表示形式・負・ゼロ)
    for cell, fmt, want in ((u"－", u"General", (True, False, None, None)), (5, u"0", (False, False, u"5", 0)), (-5, u"0", (False, True, u"5", 0)), (12.5, u"0.0", (False, False, u"12.5", 1)),
                            (12.5, u"0.00", (False, False, u"12.50", 2)), (-12.5, u"0.0", (False, True, u"12.5", 1)), (3, u"0.0", (False, False, u"3.0", 1)), (0, u"0", (False, False, u"0", 0)),
                            (-0.0, u"0.0", (False, True, u"0.0", 1)), (1e-05, u"0.00000", (False, False, u"0.00001", 5)), (123456789012345, u"0", (False, False, u"123456789012345", 0)),
                            (1234.5, u"0.0", (False, False, u"1234.5", 1)), (0.1, u"0.00", (False, False, u"0.10", 2))):
        got = ms.read_amount(cell, fmt)
        if got != want:
            out.append(u"数のセルの読みが違う: %r %s -> %s" % (cell, fmt, got))
    for cell, fmt in ((5, u"General"), (5, u"0.0.0"), (5, u"#,##0"), (5, u""), (5, None), (u"abc", u"0"), (u"-", u"0"), (True, u"0"), (None, u"0"), (5, u"00"), (5, u"0.")):
        if not stops(ms, ms.read_amount, cell, fmt):
            out.append(u"決めた形でない数のセルで止まらない: %r %r" % (cell, fmt))
    # 採点の部品
    ans = od([("name", u"a"), ("target", u"既定"), ("dims", []), ("period", [u"2031-03-31"]), ("pkind", "instant"), ("value", u"5"), ("form", JPY), ("shift", 6), ("prec", -6), ("nil", False)])
    if ms.differing_fields(dict(ans), ans) != []:
        out.append(u"同じ中身で違う欄が出る")
    for f, k, v in ((u"名", "name", u"b"), (u"個別か既定か", "target", u"個別"), (u"区分", "dims", [[u"a", u"b"]]), (u"期の日", "period", [u"2031-03-30"]), (u"期の種類", "pkind", "duration"), (u"値", "value", u"6"),
                    (u"単位の形", "form", USD), (u"表示の位", "shift", 3), (u"精度", "prec", 0), (u"空か", "nil", True)):
        d = dict(ans)
        d[k] = v
        if ms.differing_fields(d, ans) != [f]:
            out.append(u"違う欄 %s を見ない: %s" % (f, ms.differing_fields(d, ans)))
    d = dict(ans)
    d.update(name=u"b", value=u"9", prec=0)
    if ms.differing_fields(d, ans) != [u"名", u"値", u"精度"]:
        out.append(u"違う欄の並びが欄の順でない")
    for dv, av, diffs, want in ((u"5", u"-5", [u"値"], True), (u"-0", u"0", [u"値"], True), (u"0", u"-0", [u"値"], True), (u"5", u"6", [u"値"], False), (u"5", u"-6", [u"値"], False),
                                (u"5", u"-5", [u"値", u"精度"], False), (u"5", u"-5", [u"名"], False), (u"-5", u"5", [u"値"], True), (u"--5", u"5", [u"値"], True)):
        if ms.sign_only({"value": dv}, {"value": av}, diffs) != want:
            out.append(u"符号だけ違うの判定が違う: %s %s %s" % (dv, av, diffs))
    # 予測の境の読み(厳密な比べ)
    for b, n, d, want in (((74.0, True, None, False), 74, 100, True), ((74.0, True, None, False), 739, 1000, False), ((74.0, True, None, False), 740, 1000, True), ((None, False, 0.5, True), 1, 200, True),
                          ((None, False, 0.5, True), 1, 199, False), ((None, False, 0.5, True), 0, 200, True), ((16.0, True, 26.0, True), 26, 100, True), ((16.0, True, 26.0, True), 261, 1000, False),
                          ((16.0, True, 26.0, True), 159, 1000, False), ((16.0, True, 26.0, True), 16, 100, True), ((74.0, True, None, False), 0, 0, False), ((None, False, 2.0, True), 0, 0, False),
                          ((74.0, True, None, False), 1, 1, True), ((None, False, 1.0, True), 1, 100, True), ((None, False, 1.0, True), 101, 10000, False), ((40.0, True, 65.0, True), 13, 20, True),
                          ((40.0, True, 65.0, True), 261, 400, False), ((40.0, True, 65.0, True), 2, 5, True)):
        if ms.rate_holds(n, d, b) != want:
            out.append(u"率の境の読みが違う: %s %s/%s" % (b, n, d))
    import fractions as _fr
    for b, x, want in (((10, False, 20, False), 10, False), ((10, False, 20, False), 20, False), ((10, False, 20, False), 11, True), ((10, True, 20, True), 10, True), ((10, True, 20, True), 20, True),
                       ((10, True, 20, True), 21, False), ((0.1, True, None, False), _fr.Fraction(1, 10), True), ((None, False, 0.1, True), _fr.Fraction(1, 10), True), ((0.1, False, None, False), _fr.Fraction(1, 10), False),
                       ((None, False, 0.3, False), _fr.Fraction(3, 10), False), ((0.3, True, None, False), _fr.Fraction(3, 10), True)):
        if ms.holds_bound(b, x) != want:
            out.append(u"境(含む・含まない・小数の字)の読みが違う: %s %s" % (b, x))
    for b, x, want in (((None, False, 30, True), 30, True), ((None, False, 30, True), 31, False), ((35, True, None, False), 35, True), ((35, True, None, False), 34, False), ((None, False, 2, True), 3, False), ((None, False, 2, True), 2, True)):
        if ms.holds_bound(b, x) != want:
            out.append(u"数の境の読みが違う: %s %s" % (b, x))
    for n_, d_, want in ((1, 8, 12.5), (1, 16, 6.3), (5, 5, 100.0), (959, 1000, 95.9), (146, 160, 91.3), (66, 160, 41.3), (0, 7, 0.0)):
        got = ms.rate_of(n_, d_)
        if tuple(got.values()) != (n_, d_, want):
            out.append(u"率が違う(数・分母・% の順。% は小数第 1 位・0.5 は上げる): %s" % dict(got))
    if ms.rate_of(0, 0)[u"%"] is not None:
        out.append(u"分母 0 の率が None でない")
    return out


# ======================================================================== 3. xlsx の往復(本物の openpyxl)
def xlsx_problems(ms=None):
    ms = ms or MS
    out = []
    N = u"xa_cor:Item"
    recs = [
        mk(u"行01", content=u"1,234", name=N + u"a"),                                                                          # 整数 0 桁
        mk(u"行02", content=u"12.5", neg=True, name=N + u"b", shift=3),                                                        # 小数 1 桁・負
        mk(u"行03", content=u"3.14", name=N + u"c", form=PURE, shift=-2, prec=2),                                              # 小数 2 桁
        mk(u"行04", content=u"0.00001", name=N + u"d", shift=0, prec=5),                                                       # 指数の形で書かれる小さい数
        mk(u"行05", nil=True, name=N + u"e", form=SHARES),                                                                     # 「－」
        mk(u"=SUM(A1)", content=u"999999999999999", name=N + u"f", shift=0, prec=0),                                          # 式の形の行の字・15 桁
        mk(u"行07", h=None, pkind="instant", dates=[u"2031-03-31"], name=N + u"g", form=JPYPS, shift=0, prec=0),              # 時点・見出し無し
        mk(u"行08", h=u"", hmark=u"", name=N + u"h"),                                                                          # 見出しの字が空・表の頭の印が空
        mk(u"行09", th=7, td=12, content=u"0", neg=True, sign=u"-", value=u"-0", name=N + u"i"),                                                       # 負の印つきの 0
        mk(u"行10", content=u"1,000.0", name=N + u"j", shift=3, prec=-2),
        mk(u"行11", content=u"12.50", neg=True, name=N + u"k", shift=3, prec=-1),
    ]
    with Temp() as d:
        rows, answers, cnt = ms.sheet_rows_of(side_of(recs, DEC_C))
        p = os.path.join(d, "a.xlsx")
        ms.write_xlsx(p, DEC_C, rows)
        if not raises(FileExistsError, ms.write_xlsx, p, DEC_C, rows):
            out.append(u"同じ path に書き直せる(排他でない)")
        dec, back = ms.read_xlsx(p)
        if dict(dec) != dict(DEC_C):
            out.append(u"書類のシートの日が往復で戻らない: %s" % dict(dec))
        if len(back) != 11:
            return out + [u"xlsx の行の数が戻らない: %d" % len(back)]
        want = [(u"見出し甲", 0, u"行01", 1, HM, 1234, u"0", u"2030-04-01", u"2031-03-31", u"百万円"), (u"見出し甲", 0, u"行02", 1, HM, -12.5, u"0.0", u"2030-04-01", u"2031-03-31", u"千円"),
                (u"見出し甲", 0, u"行03", 1, HM, 3.14, u"0.00", u"2030-04-01", u"2031-03-31", u"％"), (u"見出し甲", 0, u"行04", 1, HM, 0.00001, u"0.00000", u"2030-04-01", u"2031-03-31", u"円"),
                (u"見出し甲", 0, u"行05", 1, HM, u"－", u"General", u"2030-04-01", u"2031-03-31", u"株"), (u"見出し甲", 0, u"=SUM(A1)", 1, HM, 999999999999999, u"0", u"2030-04-01", u"2031-03-31", u"円"),
                (None, 0, u"行07", 1, HM, 5 * 0 + 1, u"0", None, u"2031-03-31", u"円/株"), (None, 0, u"行08", 1, u"", 1, u"0", u"2030-04-01", u"2031-03-31", u"百万円"),
                (u"見出し甲", 7, u"行09", 12, HM, 0, u"0", u"2030-04-01", u"2031-03-31", u"百万円"), (u"見出し甲", 0, u"行10", 1, HM, 1000, u"0.0", u"2030-04-01", u"2031-03-31", u"千円"),
                (u"見出し甲", 0, u"行11", 1, HM, -12.5, u"0.00", u"2030-04-01", u"2031-03-31", u"千円")]
        for i, (r, w) in enumerate(zip(back, want)):
            got = (r["h"], r["th"], r["T"], r["td"], r["hmark"], r["amount"], r["fmt"], r["start"], r["end"], r["unit"])
            if got != w or type(got[5]) is not type(w[5]):
                out.append(u"xlsx の行 %d が往復で戻らない: %r != %r" % (i + 1, got, w))
        # 受ける側が読む数のセルから、表示の字・負・桁が戻る
        for i, (cell, fmt, content, neg_) in enumerate(((1234, u"0", u"1234", False), (-12.5, u"0.0", u"12.5", True), (3.14, u"0.00", u"3.14", False), (0.00001, u"0.00000", u"0.00001", False),
                                                        (u"－", u"General", None, False), (999999999999999, u"0", u"999999999999999", False), (1, u"0", u"1", False), (1, u"0", u"1", False),
                                                        (0, u"0", u"0", False), (1000.0, u"0.0", u"1000.0", False), (-12.5, u"0.00", u"12.50", True))):
            r = back[i]
            nil, ng, ct, dig = ms.read_amount(r["amount"], r["fmt"])
            if (ct, ng) != (content, neg_) or nil != (cell == u"－"):
                out.append(u"往復した数のセルから表示の字・負が戻らない: 行 %d %r %r" % (i + 1, ct, ng))
        # 日付のセルは日付の形(数でも字でもない)
        import openpyxl
        wb = openpyxl.load_workbook(p)
        if wb.sheetnames != [u"書類", u"数"]:
            out.append(u"シートの名・順が違う: %s" % wb.sheetnames)
        if [c.value for c in wb[u"書類"][1]] != list(ms.HEAD_DOC) or [c.value for c in wb[u"数"][1]] != list(ms.HEAD_NUM):
            out.append(u"見出しの行が違う")
        import datetime as _dt
        for c in wb[u"書類"][2]:
            if not isinstance(c.value, _dt.datetime):
                out.append(u"書類のシートの日が日付のセルでない")
        for c in (wb[u"数"][u"G2"], wb[u"数"][u"H2"], wb[u"数"][u"G8"]):
            if c.value is not None and not isinstance(c.value, _dt.datetime):
                out.append(u"期の日が日付のセルでない")
        if wb[u"数"][u"G8"].value is not None or wb[u"数"][u"H8"].value is None:
            out.append(u"時点のときの期の始まりが空・終わりが日付になっていない")
        if wb[u"数"][u"F6"].value != u"－" or wb[u"数"][u"F2"].number_format != u"0" or wb[u"数"][u"F3"].number_format != u"0.0" or wb[u"数"][u"F4"].number_format != u"0.00" or wb[u"数"][u"F5"].number_format != u"0.00000":
            out.append(u"数のセルの表示形式・「－」が違う")
        if wb[u"数"][u"C7"].value != u"=SUM(A1)" or wb[u"数"][u"C7"].data_type != u"s":
            out.append(u"式の形の字が字のセルでない")
        # 負の印つきの 0 は数のセルの符号を失う(報告の通り。答えは符号つきの 0)
        if answers[8]["value"] != u"-0" or ms.read_amount(back[8]["amount"], back[8]["fmt"])[1] is not False:
            out.append(u"負の印つきの 0 の往復の様子が決めと違う")
        # 答えの file の行は xlsx の行と同じ順・同じ数
        if len(answers) != 11 or [a["name"] for a in answers] != [r["name"] for r in recs] or [a["mark"] for a in answers] != [r["neg"] for r in recs]:
            out.append(u"答えの行の並びが xlsx の行と違う")
        if set(answers[0]) != set(["kind", "name", "target", "dims", "pkind", "period", "value", "form", "shift", "prec", "nil", "mark"]) or answers[0]["kind"] != u"数":
            out.append(u"答えの欄が違う: %s" % sorted(answers[0]))
        if answers[6]["pkind"] != "instant" or answers[6]["period"] != [u"2031-03-31"] or answers[1]["period"] != CUR_DUR or answers[0]["dims"] != []:
            out.append(u"答えの期・区分の形が違う")
        # 返ってきた xlsx の日・数だけから、受ける側が決められる(往復後の行を直に決める)
    # 退化値: 行 0 の xlsx・空の書類
    with Temp() as d:
        rows, answers, cnt = ms.sheet_rows_of(side_of([], DEC_C))
        p = os.path.join(d, "e.xlsx")
        ms.write_xlsx(p, DEC_C, rows)
        dec, back = ms.read_xlsx(p)
        if rows != [] or answers != [] or back != [] or cnt["D"] != 0:
            out.append(u"行 0 の xlsx が行 0 で戻らない")
        got = ms.receive_pair(p, side_of([mk(u"行01")], DEC_P))
        if got["rows"] != [] or got["lost"] != 1:
            out.append(u"行 0 の xlsx を受けて無くなった行が数えられない: %s" % got["lost"])
    # 空の行(全部が空のセル)は読み飛ばす
    import openpyxl
    with Temp() as d:
        rows, answers, cnt = ms.sheet_rows_of(side_of([mk(u"行01"), mk(u"行02")], DEC_C))
        p = os.path.join(d, u"b.xlsx")
        ms.write_xlsx(p, DEC_C, rows)
        wb = openpyxl.load_workbook(p)
        wb[u"数"].insert_rows(3, 2)
        wb.save(p)
        dec, back = ms.read_xlsx(p)
        if [r["T"] for r in back] != [u"行01", u"行02"]:
            out.append(u"空の行を読み飛ばさない: %s" % [r["T"] for r in back])
    # 日付のセルでない日・字の金額・空の書類のシートは止まる
    with Temp() as d:
        for what, fn in ((u"書類のシートの日が字", lambda wb: wb[u"書類"].__setitem__(u"A2", u"2030-04-01")),
                         (u"期の日が字", lambda wb: wb[u"数"].__setitem__(u"H2", u"2031-03-31")),
                         (u"書類のシートの日が空", lambda wb: wb[u"書類"].__setitem__(u"C2", None))):
            rows, answers, cnt = ms.sheet_rows_of(side_of([mk(u"行01")], DEC_C))
            p = os.path.join(d, u"%s.xlsx" % what)
            ms.write_xlsx(p, DEC_C, rows)
            wb = openpyxl.load_workbook(p)
            fn(wb)
            wb.save(p)
            if not stops(ms, ms.read_xlsx, p):
                out.append(u"止まらない: %s" % what)
    return out


# ======================================================================== 4. 書類の字と答えの側の fact の突き合わせ(``build_side``)
def side_build_problems(ms=None):
    ms = ms or MS
    out = []

    def fact(name, ctx, content, sign=None, nil=False, reasons=(), fi=0, where="F", isnum=True, target=u"既定"):
        a = {"name": name, "contextRef": ctx}
        if sign:
            a["sign"] = sign
        return {"where": where, "isnum": isnum, "fi": fi, "attrs": a, "reasons": set(reasons), "target": target, "dims": [(u"xa_cor:Ax", u"xb:Mb")], "period": ("duration", list(CUR_DUR)),
                "value": u"1", "form": JPY, "shift": 6, "prec": -6, "nil": nil, "content": content}
    html1 = (u'<div>【計算書】</div><table><tr><td>科目</td><td>当期</td></tr>'
             u'<tr><td>売上高</td><td>&#160;△<ix:nonFraction name="x:A" contextRef="c1">1,234</ix:nonFraction></td><td><ix:nonFraction name="x:B" contextRef="c2"/></td></tr>'
             u'<tr><td>利益</td><td>5</td><td><ix:nonFraction name="x:C" contextRef="c1" sign="-">56</ix:nonFraction></td></tr></table>'
             u'<p><ix:nonFraction name="x:D" contextRef="c1">9</ix:nonFraction></p>')
    html2 = u'<table><tr><td>名前欄</td><td><ix:nonFraction name="x:E" contextRef="c1">7</ix:nonFraction></td></tr></table>'
    html3 = (u'<table><tr><td>見出し行</td></tr><tr><td></td></tr><tr><td>後</td><td><ix:nonFraction name="x:F" contextRef="c1">3</ix:nonFraction></td></tr>'
             u'<tr><td>注釈の行</td></tr><tr><td>二</td><td><ix:nonFraction name="x:F2" contextRef="c1">4</ix:nonFraction></td></tr>'
             u'</table><table><tr><td>別の表</td></tr><tr><td>行</td><td><ix:nonFraction name="x:G" contextRef="c1">8</ix:nonFraction></td></tr></table>')
    P = u"XBRL/PublicDoc/"
    texts = [(P + u"b.htm", html2), (P + u"a.htm", html1)]
    files = [(u"a.htm",), (u"b.htm",)]
    facts = [fact(u"x:A", u"c1", u"1,234", fi=0), fact(u"x:B", u"c2", u"", nil=True, fi=0), fact(u"x:C", u"c1", u"56", sign=u"-", fi=0, target=u"個別"), fact(u"x:D", u"c1", u"9", fi=0),
             fact(u"x:E", u"c1", u"7", fi=1, reasons=["e"]), fact(u"x:H", u"c1", u"1", fi=1, where="H"), fact(u"x:I", u"c1", u"1", fi=1, isnum=False)]
    side = ms.build_side(texts, files, {"dec": dict(DEC_C), "facts": facts})
    recs = side["records"]
    # file 名の昇順・file の中は出た順・行の外の fact(x:D)は行の中に数えない・隠しの fact・文の fact は結ばない
    if [r["name"] for r in recs] != [u"x:A", u"x:B", u"x:C", u"x:E"]:
        out.append(u"行の中の fact の並びが違う: %s" % [r["name"] for r in recs])
        return out
    st = side["stats"]
    if dict(st) != {"inrow": 4, "files_out": 0, "ix_out": 0, "inrow_out": 0}:
        out.append(u"突き合わせの数が違う: %s" % dict(st))
    a, b, c, e = recs
    if (a["h"], a["th"], a["T"], a["td"]) != (u"計算書", 0, u"売上高", 2) or (b["td"], c["T"], c["td"]) != (3, u"利益", 3) or (e["h"], e["T"], e["td"]) != (None, u"名前欄", 2):
        out.append(u"鍵の 4 つ(見出し・表の番号・行の字・列の番号)が違う: %s" % [(r["h"], r["th"], r["T"], r["td"]) for r in recs])
    if [r["neg"] for r in recs] != [True, False, False, False]:
        out.append(u"負の印が違う: %s" % [r["neg"] for r in recs])
    if [r["hmark"] for r in recs] != [u"科目|当期"[:0] + ms.G.head_mark([u"<tr><td>科目</td><td>当期</td></tr>"])] * 3 + [u""]:
        out.append(u"表の頭の印が違う: %s" % [r["hmark"] for r in recs])
    if (a["name"], a["target"], a["dims"], a["pkind"], a["dates"], a["pn"], a["value"], a["form"], a["shift"], a["prec"], a["nil"], a["content"], a["sign"], a["bad"]) != \
            (u"x:A", u"既定", ((u"xa_cor:Ax", u"xb:Mb"),), "duration", CUR_DUR, u"CurrentYear", u"1", JPY, 6, -6, False, u"1,234", None, False):
        out.append(u"fact の欄(答えの側)が写っていない: %s" % dict(a))
    if c["target"] != u"個別" or a["target"] != u"既定":
        out.append(u"個別か既定かが答えの側の fact の欄を写していない")
    if not b["nil"] or c["sign"] != u"-" or not e["bad"] or e["pn"] is not None or a["pn"] != u"CurrentYear":
        out.append(u"空・sign・型の外・期の名(型の外には付けない)が違う")
    # 表の頭: 最初に数の fact が出る行より前の行の字の並び(空の行も 1 つ)・表ごと
    side3 = ms.build_side([(P + u"c.htm", html3)], [(u"c.htm",)], {"dec": dict(DEC_C), "facts": [fact(u"x:F", u"c1", u"3"), fact(u"x:F2", u"c1", u"4"), fact(u"x:G", u"c1", u"8")]})
    h1 = ms.G.head_mark([u"<tr><td>見出し行</td></tr>", u"<tr><td></td></tr>"])
    h2 = ms.G.head_mark([u"<tr><td>別の表</td></tr>"])
    if [r["hmark"] for r in side3["records"]] != [h1, h1, h2] or h1 == h2:
        out.append(u"表の頭の印が表ごとの頭の行の並びでない")
    # 数が合わない file は結ばない(突き合わせの外に数える)
    bad = ms.build_side(texts, files, {"dec": dict(DEC_C), "facts": [fact(u"x:A", u"c1", u"1,234", fi=0), fact(u"x:E", u"c1", u"7", fi=1, reasons=["e"])]})
    if [r["name"] for r in bad["records"]] != [u"x:E"] or dict(bad["stats"]) != {"inrow": 4, "files_out": 1, "ix_out": 4, "inrow_out": 3}:
        out.append(u"数が合わない file を突き合わせの外に数えない: %s %s" % ([r["name"] for r in bad["records"]], dict(bad["stats"])))
    none_x = ms.build_side(texts, files, {"dec": dict(DEC_C), "facts": []})
    if none_x["records"] != [] or dict(none_x["stats"]) != {"inrow": 4, "files_out": 2, "ix_out": 5, "inrow_out": 4}:
        out.append(u"答えの側の fact が 0 の file を突き合わせの外に数えない: %s" % dict(none_x["stats"]))
    # name か contextRef が違えば止まる
    if not stops(ms, ms.build_side, texts, files, {"dec": dict(DEC_C), "facts": [fact(u"x:Z", u"c1", u"1,234", fi=0)] + facts[1:]}):
        out.append(u"結んだ対の name が違うのに止まらない")
    if not stops(ms, ms.build_side, texts, files, {"dec": dict(DEC_C), "facts": [fact(u"x:A", u"cZ", u"1,234", fi=0)] + facts[1:]}):
        out.append(u"結んだ対の contextRef が違うのに止まらない")
    # 書類の決めは今の側のもの(期の名)
    prior_facts = [dict(f, period=("duration", list(PRI_DUR))) for f in facts]
    sc_ = ms.build_side(texts, files, {"dec": dict(DEC_C), "facts": prior_facts})
    sp_ = ms.build_side(texts, files, {"dec": dict(DEC_P), "facts": prior_facts})
    if sc_["records"][0]["pn"] != u"Prior1Year" or sp_["records"][0]["pn"] != u"CurrentYear" or sp_["dec"] != dict(DEC_P):
        out.append(u"期の名を書類の決めで付けない")
    return out


# ======================================================================== 5. 受ける側
def recv_problems(ms=None):
    ms = ms or MS
    out = []
    with Temp() as d:
        rows, answers, cnt, recv = run_scene(ms, prior_s1(), cur_s1(), d)
    res = recv["rows"]
    if len(res) != 31 or len(rows) != 31 or len(answers) != 31:
        return [u"S1 の行の数が 31 でない"]
    if recv["lost"] != 6:
        out.append(u"無くなった行の数が違う(手の数 6): %s" % recv["lost"])
    if list(res[0]) != ["i", "stop", "decided", "cf", "default", "shift_differs"]:
        out.append(u"行ごとの決めの欄が違う: %s" % list(res[0]))
    for i, (r, a, w) in enumerate(zip(res, answers, S1_ROWS), 1):
        stop, diffs, default, sd = w
        if r["i"] != i - 1:
            out.append(u"行 %d の番号が違う" % i)
        if r["stop"] != stop:
            out.append(u"行 %d の止めが違う: %r != %r" % (i, r["stop"], stop))
            continue
        if r["shift_differs"] != sd:
            out.append(u"行 %d の去年と表示の位が違うが違う: %r" % (i, r["shift_differs"]))
        if stop:
            if r["decided"] is not None:
                out.append(u"行 %d: 止めたのに決めている" % i)
            if stop in (u"表の頭が違う", u"期が違う", u"番号つき", u"単位が違う"):
                if r["cf"] is None or (diff_names(r["cf"], a) == []) != (i in S1_GUARD_OK):
                    out.append(u"行 %d: 止めずに決めていたら同じだったかが違う: %s" % (i, diff_names(r["cf"], a) if r["cf"] else None))
            elif r["cf"] is not None:
                out.append(u"行 %d: 守りの止めでないのに止めずに決めた中身を持つ" % i)
        else:
            if r["decided"] is None or r["cf"] is not None:
                out.append(u"行 %d: 決めていない・決めたのに止めた中身を持つ" % i)
                continue
            if diff_names(r["decided"], a) != diffs:
                out.append(u"行 %d: 決めた中身の違う欄が違う: %s != %s" % (i, diff_names(r["decided"], a), diffs))
            if r["default"] != default:
                out.append(u"行 %d: 去年が空で既定の順を使ったかが違う: %r" % (i, r["default"]))
    # 決めた中身の手の値(精度・値・単位・期・空)
    by = dict((i, r["decided"]) for i, r in enumerate(res, 1) if r["decided"])
    hand = {1: (u"xa_cor:Item1", u"既定", [], "duration", CUR_DUR, u"1000000", JPY, 6, -6, False), 3: (u"xa_cor:Item3", u"既定", [], "duration", CUR_DUR, u"-1000000", JPY, 6, -6, False),
            11: (u"xa_cor:Item9", u"既定", [], "duration", CUR_DUR, NONE_V, JPY, None, None, True), 14: (u"xa_cor:Item10", u"既定", [], "duration", CUR_DUR, u"1000000", JPY, 6, -6, False),
            15: (u"xa_cor:Item10", u"既定", [], "duration", CUR_DUR, u"0", JPY, 6, -6, False), 24: (u"xa_cor:Item21", u"既定", [], "duration", CUR_DUR, u"7000", JPY, 3, -3, False),
            27: (u"xa_cor:Item24", u"既定", [], "duration", CUR_DUR, u"12500", JPY, 3, -2, False), 28: (u"xa_cor:Item25", u"既定", [], "duration", CUR_DUR, u"0.0314", PURE, -2, 4, False),
            29: (u"xa_cor:Item26", u"既定", [], "duration", CUR_DUR, u"250", JPYPS, 0, 0, False), 30: (u"xa_cor:Item27", u"既定", [], "instant", [u"2031-03-31"], u"1000000", JPY, 6, -6, False),
            31: (u"xa_cor:Item28", u"既定", [], "duration", CUR_DUR, u"1000000", JPY, 6, -6, False), 13: (u"xa_cor:Item10", u"既定", [], "duration", CUR_DUR, u"-1000000", JPY, 6, -6, False),
            2: (u"xa_cor:Item2", u"既定", [], "duration", CUR_DUR, u"-1000000", JPY, 6, -6, False), 16: (u"xa_cor:Item11", u"既定", [], "duration", CUR_DUR, u"-1000000", JPY, 6, -6, False),
            23: (u"xa_cor:Item20", u"既定", [[u"xa_cor:Ax3", u"xb:No1MemberX"]], "duration", CUR_DUR, u"1000000", JPY, 6, -6, False)}
    for i, w in hand.items():
        g = by[i]
        if (g["name"], g["target"], g["dims"], g["pkind"], g["period"], g["value"], g["form"], g["shift"], g["prec"], g["nil"]) != w:
            out.append(u"行 %d の決めた中身が手の値と違う: %s" % (i, dict(g)))
    if list(by[1]) != ["name", "target", "dims", "pkind", "period", "value", "form", "shift", "prec", "nil"]:
        out.append(u"決めた中身の欄の並びが違う")
    # 止めの理由と順: 6 つの止めの全部の組み合わせ(先に当たった止めで止める)
    out += stop_order_problems(ms)
    out += key_candidate_problems(ms)
    # 空の書類 / 去年の表が空(退化値)・全部止め
    with Temp() as d:
        _r, _a, _c, got = run_scene(ms, side_of([], DEC_P), cur_s1(), d)
        if [r["stop"] for r in got["rows"]] != [u"去年に無い行"] * 31 or got["lost"] != 0:
            out.append(u"去年の表が空のとき全部が「去年に無い行」で止まらない")
    with Temp() as d:
        only_bad = side_of([mk(u"行01", bad=True), mk(u"", name=u"xa_cor:Q")], DEC_P)
        _r, _a, _c, got = run_scene(ms, only_bad, side_of([mk(u"行01")], DEC_C), d)
        if [r["stop"] for r in got["rows"]] != [u"去年に無い行"] or got["lost"] != 0:
            out.append(u"型の外・行の字が空の去年の fact が去年の表に入る")
    # 表に入る去年の fact(型の外でなく行の字が空でない)・集まり
    tab = ms.prior_table(prior_s1())
    key01 = (u"見出し甲", 0, u"行01", 1)
    if key01 not in tab or len(tab) != 30:
        out.append(u"去年の表の鍵の数が違う(手の数 30): %d" % len(tab))
    e = tab.get((u"見出し甲", 0, u"行11", 1))
    if e is None or e["flips"] != set([True]) or e["cands"] != set([(u"xa_cor:Item11", u"既定", ())]) or e["shifts"] != set([6]) or e["forms"] != set([JPY]) or e["marks"] != set([HM]) or e["pns"] != set([u"CurrentYear"]):
        out.append(u"去年の表の集まりが違う(空の fact は符号の向き・表示の位に入らない): %s" % (e,))
    e = tab.get((u"見出し甲", 0, u"行10", 1))
    if e is None or e["flips"] != set() or e["shifts"] != set() or e["forms"] != set([JPY]):
        out.append(u"空だけの去年の鍵の集まりが違う")
    e = tab.get((u"見出し甲", 0, u"行09", 1))
    if e is None or e["flips"] != set([True, False]):
        out.append(u"符号の向きの集まりが両方にならない")
    e = tab.get((None, 0, u"行17", 1))
    if e is None:
        out.append(u"見出しの字が空の去年の鍵が無い見出しと同じ鍵にならない")
    e = tab.get((u"見出し甲", 0, u"行02", 1))
    if e is None or e["flips"] != set([False]):
        out.append(u"去年の符号の向き(負の印と sign が同じなら順)が違う")
    e = tab.get((u"見出し甲", 0, u"行03", 1))
    if e is None or e["flips"] != set([True]):
        out.append(u"去年の符号の向き(負の印なしで sign なら逆)が違う")
    e = tab.get((u"見出し甲", 0, u"行28", 1))
    if e is None or e["flips"] != set([True]):
        out.append(u"去年の符号の向き(負の印ありで sign なしなら逆)が違う")
    # 去年の期の名の集まり・表の頭の印の集まりは去年の fact から
    t2 = ms.prior_table(side_of([mk(u"行01", pn=u"CurrentYear", hmark=u"a"), mk(u"行01", pn=u"Prior1Year", hmark=u"b")], DEC_P))
    e = t2[(u"見出し甲", 0, u"行01", 1)]
    if e["pns"] != set([u"CurrentYear", u"Prior1Year"]) or e["marks"] != set([u"a", u"b"]) or len(e["cands"]) != 1:
        out.append(u"去年の期の名・表の頭の印の集まりが違う")
    return out


def row_of(T=u"行01", amount=5, fmt=u"0", hmark=HM, start=u"2030-04-01", end=u"2031-03-31", unit=u"百万円", h=u"見出し甲", th=0, td=1):
    return od([("h", h), ("th", th), ("T", T), ("td", td), ("hmark", hmark), ("amount", amount), ("fmt", fmt), ("start", start), ("end", end), ("unit", unit)])


def stop_order_problems(ms):
    u"""6 つの止め(候補が 2 つ以上・表の頭・期・番号つき・単位・符号の向き)の 64 通りの組み合わせの全部で、先に当たった止めで止まる。"""
    out = []
    for k in range(7):
        for S in itertools.combinations(STOP_ORDER, k):
            dims = [(u"xa_cor:Ax", u"xb:No1Member")] if u"番号つき" in S else []
            prior = [mk(u"行01", name=u"xa_cor:N", dims=dims)]
            if u"候補が 2 つ以上" in S:
                prior.append(mk(u"行01", name=u"xa_cor:N2", dims=dims))
            if u"符号の向きが 2 通り" in S:
                prior.append(mk(u"行01", name=u"xa_cor:N", dims=dims, sign=u"-", value=u"-1000000"))
            tab = ms.prior_table(side_of(prior, DEC_P))
            row = row_of(hmark=HM2 if u"表の頭が違う" in S else HM, start=u"2029-04-01" if u"期が違う" in S else u"2030-04-01", end=u"2030-03-31" if u"期が違う" in S else u"2031-03-31",
                         unit=u"株" if u"単位が違う" in S else u"百万円")
            want = u""
            for s in STOP_ORDER:
                if s in S:
                    want = s
                    break
            got = ms.receive_row(0, row, dict(DEC_C), tab)
            if got["stop"] != want:
                out.append(u"止めの組み合わせ %s: %r != %r" % (u"+".join(S) or u"なし", got["stop"], want))
            if want in (u"表の頭が違う", u"期が違う", u"番号つき", u"単位が違う") and got["cf"] is None:
                out.append(u"守りの止めが止めずに決めた中身を持たない: %s" % u"+".join(S))
            if want in (u"表の頭が違う", u"期が違う", u"番号つき", u"単位が違う") and u"符号の向きが 2 通り" in S and got["cf"] is not None and got["cf"]["value"] != (u"5" if u"単位が違う" in S else u"5000000"):
                out.append(u"去年の符号の向きが 2 通りのとき止めずに決めた中身は「順」で決めない: %s" % got["cf"]["value"])
            if want and want not in (u"表の頭が違う", u"期が違う", u"番号つき", u"単位が違う") and got["cf"] is not None:
                out.append(u"守りでない止めが止めずに決めた中身を持つ: %s" % u"+".join(S))
            if not want and (got["decided"] is None or got["cf"] is not None):
                out.append(u"止まらないのに決めていない")
    # 去年に無い行は他の止めより先
    tab = ms.prior_table(side_of([mk(u"行01", name=u"xa_cor:N"), mk(u"行01", name=u"xa_cor:N2")], DEC_P))
    for T in (u"行02",):
        got = ms.receive_row(0, row_of(T=T, hmark=HM2, unit=u"株"), dict(DEC_C), tab)
        if got["stop"] != u"去年に無い行":
            out.append(u"去年に無い行が他の止めより先でない")
    # 符号の向きが 2 通りでも空の金額は止まらない
    tab = ms.prior_table(side_of([mk(u"行01", name=u"xa_cor:N"), mk(u"行01", name=u"xa_cor:N", sign=u"-", value=u"-1000000")], DEC_P))
    got = ms.receive_row(0, row_of(amount=u"－", fmt=u"General"), dict(DEC_C), tab)
    if got["stop"] != u"" or got["decided"] is None or not got["decided"]["nil"]:
        out.append(u"符号の向きが 2 通りでも金額が「－」なら止めない")
    got = ms.receive_row(0, row_of(amount=u"－", fmt=u"General", unit=u"株"), dict(DEC_C), tab)
    if got["stop"] != u"単位が違う":
        out.append(u"金額が「－」の行で単位の字から単位の形だけで守りを見ない")
    # 期の名: 時点・期間・作れない日
    tab = ms.prior_table(side_of([mk(u"行01", name=u"xa_cor:N", pn=u"Prior1Year"), mk(u"行02", name=u"xa_cor:N", pn=u"CurrentYear"), mk(u"行03", name=u"xa_cor:N", pn=u"FilingDate")], DEC_P))
    for T, start, end, want in ((u"行01", None, u"2030-03-31", u""), (u"行01", u"2030-04-01", u"2031-03-31", u"期が違う"), (u"行02", None, u"2031-03-31", u""), (u"行02", u"2030-04-01", u"2031-03-31", u""),
                                (u"行02", None, u"2030-03-31", u"期が違う"), (u"行03", None, u"2031-06-30", u""), (u"行03", None, u"2031-03-31", u"期が違う"), (u"行02", u"2030-04-01", None, u"期が違う"),
                                (u"行02", u"2030-04-02", u"2031-03-31", u"期が違う")):
        got = ms.receive_row(0, row_of(T=T, start=start, end=end), dict(DEC_C), tab)
        if got["stop"] != want:
            out.append(u"期の名の守りが違う: %s %s %s -> %r" % (T, start, end, got["stop"]))
    got = ms.receive_row(0, row_of(T=u"行02", start=None, end=u"2031-03-31"), dict(DEC_C), tab)
    if got["decided"] is None or got["decided"]["pkind"] != "instant" or got["decided"]["period"] != [u"2031-03-31"]:
        out.append(u"日付が 1 つのとき時点にならない")
    got = ms.receive_row(0, row_of(T=u"行02"), dict(DEC_C), tab)
    if got["decided"] is None or got["decided"]["pkind"] != "duration" or got["decided"]["period"] != [u"2030-04-01", u"2031-03-31"]:
        out.append(u"日付が 2 つのとき期間にならない")
    # 書類のシートの決め(今年の書類の決め)から期の名を作る(去年の書類の決めを使わない)
    tab = ms.prior_table(side_of([mk(u"行01", name=u"xa_cor:N", pn=u"CurrentYear")], DEC_P))
    got = ms.receive_row(0, row_of(start=u"2029-04-01", end=u"2030-03-31"), dict(DEC_P), tab)
    if got["stop"] != u"":
        out.append(u"期の名を書類のシートの決めで作らない")
    return out


def key_candidate_problems(ms):
    u"""鍵の 4 つの部品・候補の 3 つの部品を 1 つずつ。"""
    out = []
    base = [mk(u"行01", name=u"xa_cor:N")]
    tab = ms.prior_table(side_of(base, DEC_P))
    for what, kw in ((u"見出しの字", dict(h=u"他")), (u"表の番号", dict(th=1)), (u"行の字", dict(T=u"行02")), (u"列の番号", dict(td=2))):
        got = ms.receive_row(0, row_of(**kw), dict(DEC_C), tab)
        if got["stop"] != u"去年に無い行":
            out.append(u"鍵の %s が違うのに去年に無い行にならない" % what)
    got = ms.receive_row(0, row_of(), dict(DEC_C), tab)
    if got["stop"] != u"":
        out.append(u"同じ鍵なのに決めない")
    if ms.receive_row(0, row_of(h=None), dict(DEC_C), ms.prior_table(side_of([mk(u"行01", h=None)], DEC_P)))["stop"] != u"" or ms.receive_row(0, row_of(h=None), dict(DEC_C), ms.prior_table(side_of([mk(u"行01", h=u"")], DEC_P)))["stop"] != u"":
        out.append(u"見出しの字が無い・空の鍵が合わない")
    for what, other in ((u"名", dict(name=u"xa_cor:N2")), (u"個別か既定か", dict(target=u"個別")), (u"区分", dict(dims=[(u"xa_cor:Ax", u"xb:Mb")]))):
        tab = ms.prior_table(side_of([mk(u"行01", name=u"xa_cor:N"), mk(u"行01", **dict(dict(name=u"xa_cor:N"), **other))], DEC_P))
        got = ms.receive_row(0, row_of(), dict(DEC_C), tab)
        if got["stop"] != u"候補が 2 つ以上":
            out.append(u"候補の %s が違う 2 つで「候補が 2 つ以上」にならない" % what)
    tab = ms.prior_table(side_of([mk(u"行01", name=u"xa_cor:N"), mk(u"行01", name=u"xa_cor:N", sign=u"-", value=u"-1000000", pn=u"Prior1Year", hmark=HM2, form=SHARES, shift=0, prec=0, content=u"5", value_=None)
                                  if False else mk(u"行01", name=u"xa_cor:N", pn=u"CurrentYear")], DEC_P))
    if ms.receive_row(0, row_of(), dict(DEC_C), tab)["stop"] != u"":
        out.append(u"同じ候補が 2 回在るのを 2 つと数える")
    tab = ms.prior_table(side_of([mk(u"行01", name=u"xa_cor:N", dims=[(u"a:X", u"b:M1"), (u"a:Y", u"b:M2")]), mk(u"行01", name=u"xa_cor:N", dims=[(u"a:X", u"b:M1")])], DEC_P))
    if ms.receive_row(0, row_of(), dict(DEC_C), tab)["stop"] != u"候補が 2 つ以上":
        out.append(u"区分の並びが違う候補を同じと数える")
    # 去年が空(空の fact だけ)のとき: 数は既定の順を使ったと数える・空の金額は数えない
    tab = ms.prior_table(side_of([mk(u"行01", name=u"xa_cor:N", nil=True)], DEC_P))
    got_n = ms.receive_row(0, row_of(), dict(DEC_C), tab)
    got_s = ms.receive_row(0, row_of(amount=u"－", fmt=u"General"), dict(DEC_C), tab)
    got_m = ms.receive_row(0, row_of(amount=-5), dict(DEC_C), tab)
    if got_n["default"] is not True or got_s["default"] is not False or got_m["decided"]["value"] != u"-5000000" or got_n["decided"]["value"] != u"5000000":
        out.append(u"去年が空のときの既定の順の扱いが違う: %s %s" % (got_n["default"], got_s["default"]))
    tab = ms.prior_table(side_of([mk(u"行01", name=u"xa_cor:N"), mk(u"行01", name=u"xa_cor:N", nil=True)], DEC_P))
    if ms.receive_row(0, row_of(), dict(DEC_C), tab)["default"] is not False:
        out.append(u"去年に値が在るのに既定の順を使ったと数える")
    # 候補が決めの名・個別か既定か・区分に出る
    tab = ms.prior_table(side_of([mk(u"行01", name=u"xa_cor:Nq", target=u"個別", dims=[(u"a:X", u"b:M1"), (u"a:Y", u"b:M2")])], DEC_P))
    g = ms.receive_row(0, row_of(), dict(DEC_C), tab)["decided"]
    if g is None or (g["name"], g["target"], g["dims"]) != (u"xa_cor:Nq", u"個別", [[u"a:X", u"b:M1"], [u"a:Y", u"b:M2"]]):
        out.append(u"決めた名・個別か既定か・区分が候補でない")
    return out


# ======================================================================== 6. 採点
def score_problems(ms=None):
    ms = ms or MS
    out = []
    with Temp() as d:
        rows, answers, cnt, recv = run_scene(ms, prior_s1(), cur_s1(), d)
    ent = ms.score_pair(5, cnt, answers, recv)
    h = HAND_S1_ENTRY
    if ent[u"番号"] != 5 or list(ent)[0] != u"番号" or ent[u"行の中の数の fact"] != 31 or ent[u"D"] != 31:
        out.append(u"組の番号・行の中の数の fact・D が違う")
    for k in (u"決めて全部同じ", u"決めたが違う", u"止めた", u"無くなった行"):
        if ent[k] != h[k]:
            out.append(u"%s が手の数と違う: %s != %s" % (k, ent[k], h[k]))
    if dict(ent[u"止めた理由ごと"]) != dict(h[u"止めた理由ごと"]):
        out.append(u"止めた理由ごとが手の数と違う: %s" % dict(ent[u"止めた理由ごと"]))
    for g, (n, ok) in h[u"守りの止め"].items():
        s = ent[u"守りの止め"][g]
        if (s[u"止めた"], s[u"正しかった止め"]) != (n, ok):
            out.append(u"守りの止め %s が手の数と違う: %s" % (g, dict(s)))
    if list(ent[u"守りの止め"]) != list(h[u"守りの止め"]):
        out.append(u"守りの止めの並びが違う")
    inner = ent[u"決めたが違うの内訳"]
    if dict(inner[u"欄ごと"]) != dict(h[u"欄ごと"]) or inner[u"符号だけ違う"] != h[u"符号だけ違う"] or inner[u"符号だけ違うのうち答えの値が符号つきの 0"] != h[u"符号だけ違うのうち答えの値が符号つきの 0"] \
            or inner[u"去年が空で既定の順を使った"] != h[u"去年が空で既定の順を使った"]:
        out.append(u"決めたが違うの内訳が手の数と違う: %s" % json.dumps(inner, ensure_ascii=False))
    sc = ent[u"場面"]
    for k, v in h[u"場面"].items():
        if sc[k] != v:
            out.append(u"場面 %s が手の数と違う: %s" % (k, sc[k]))
    s = sc[u"去年の同じ鍵と表示の位が違う"]
    if (s[u"件数"], s[u"決めて全部同じ"], s[u"決めたが違う"], s[u"止めた"]) != h[u"表示の位が違う"]:
        out.append(u"去年の同じ鍵と表示の位が違う fact とその分けが違う: %s" % dict(s))
    if ms.entry_problems(ent) != u"":
        out.append(u"採点した組が導ける関係を満たさない: %s" % ms.entry_problems(ent))
    if [k for k in ent] != [u"番号"] + list(ms.zero_entry()):
        out.append(u"組の欄の並びが違う")
    # 採点は受ける側の出力と答えを比べる(答え同士ではない・出力を直せば数が変わる)
    bad = json.loads(json.dumps(recv), object_pairs_hook=od)
    bad["rows"][0]["decided"]["name"] = u"xa_cor:Wrong"
    e2 = ms.score_pair(5, cnt, answers, bad)
    if e2[u"決めたが違う"] != h[u"決めたが違う"] + 1 or e2[u"決めて全部同じ"] != h[u"決めて全部同じ"] - 1 or e2[u"決めたが違うの内訳"][u"欄ごと"][u"名"] != 2:
        out.append(u"受ける側の出力の中身を直しても採点が変わらない(答え同士を比べている)")
    bad = json.loads(json.dumps(recv), object_pairs_hook=od)
    bad["rows"][4]["cf"]["name"] = u"xa_cor:Wrong"
    e3 = ms.score_pair(5, cnt, answers, bad)
    if e3[u"守りの止め"][u"守り G 表の頭"][u"正しかった止め"] != 0:
        out.append(u"止めずに決めていた中身を直しても正しかった止めが変わらない")
    for f in ("name", "target", "dims", "pkind", "period", "value", "form", "shift", "prec", "nil"):
        bad = json.loads(json.dumps(recv), object_pairs_hook=od)
        bad["rows"][4]["cf"][f] = u"__x__" if f in ("name", "target", "pkind", "value", "form") else [u"__x__"] if f in ("dims", "period") else 99
        e5 = ms.score_pair(5, cnt, answers, bad)
        if e5[u"守りの止め"][u"守り G 表の頭"][u"正しかった止め"] != 0:
            out.append(u"止めずに決めていた中身の %s の違いを正しかった止めが見ない" % f)
    bad = json.loads(json.dumps(recv), object_pairs_hook=od)
    bad["rows"][0]["decided"]["value"] = u"7"
    e6 = ms.score_pair(5, cnt, answers, bad)
    if e6[u"決めたが違う"] != h[u"決めたが違う"] + 1 or e6[u"決めたが違うの内訳"][u"符号だけ違う"] != h[u"符号だけ違う"] or e6[u"決めたが違うの内訳"][u"欄ごと"][u"値"] != 3:
        out.append(u"値の絶対値が違うのに符号だけ違うに数える: %s" % dict(e6[u"決めたが違うの内訳"]))
    ans3 = json.loads(json.dumps(answers), object_pairs_hook=od)
    ans3[10]["mark"] = True                                                  # 行 11 は空の fact: 空の fact の負の印・符号の向きは数えない
    e7 = ms.score_pair(5, cnt, ans3, recv)
    if e7[u"場面"][u"負の印あり"] != h[u"場面"][u"負の印あり"] or e7[u"場面"][u"符号の向きが逆"] != h[u"場面"][u"符号の向きが逆"]:
        out.append(u"空の fact の負の印・符号の向きを場面に数える")
    ans2 = json.loads(json.dumps(answers), object_pairs_hook=od)
    ans2[0]["value"] = u"7"
    e4 = ms.score_pair(5, cnt, ans2, recv)
    if e4[u"決めたが違う"] != h[u"決めたが違う"] + 1:
        out.append(u"答えを直しても採点が変わらない")
    # 行の数が合わなければ止まる
    if not stops(ms, ms.score_pair, 5, cnt, answers[:-1], recv) or not stops(ms, ms.score_pair, 5, dict(cnt, D=30), answers, recv):
        out.append(u"受ける側の行の数と答えの行の数が合わないのに止まらない")
    # xlsx に書かない fact の数と D
    side = side_of([mk(u"", name=u"a"), mk(u"行01", bad=True), mk(u"行01", form=USD), mk(u"行01", content=u"1234567890123456"), mk(u"", bad=True, form=USD), mk(u"行01"), mk(u"行02", nil=True)], DEC_C,
                   inrow=11, files_out=2, ix_out=9, inrow_out=4)
    rows, answers2, cnt2 = ms.sheet_rows_of(side)
    if dict(cnt2) != {"inrow": 11, "files_out": 2, "ix_out": 9, "inrow_out": 4, u"行の字が空": 2, u"型の外": 1, u"単位が書けない": 1, u"有効数字が 15 桁を超える": 1, "D": 2}:
        out.append(u"xlsx に書かない fact の数が違う: %s" % dict(cnt2))
    if len(rows) != 2 or len(answers2) != 2:
        out.append(u"書かない fact が xlsx・答えに入る")
    side_bad = side_of([mk(u"行01")], DEC_C, inrow=5, inrow_out=0)
    if not stops(ms, ms.sheet_rows_of, side_bad):
        out.append(u"D が行の中の数の fact から引いた数と合わないのに止まらない")
    ent2 = ms.score_pair(3, cnt2, answers2, od([("rows", [od([("i", 0), ("stop", u"去年に無い行"), ("decided", None), ("cf", None), ("default", False), ("shift_differs", False)]) for _ in range(2)]), ("lost", 0)]))
    if ent2[u"行の中の数の fact"] != 11 or dict(ent2[u"突き合わせの外"]) != {u"file": 2, u"ix:nonFraction の fact": 9, u"うち行の中の数の fact": 4} or ent2[u"D"] != 2 or ent2[u"止めた"] != 2 \
            or dict(ent2[u"xlsx に書かなかった fact"]) != {u"行の字が空": 2, u"型の外": 1, u"単位が書けない": 1, u"有効数字が 15 桁を超える": 1}:
        out.append(u"突き合わせの外・書かなかった fact が組の数に入らない: %s" % json.dumps(ent2, ensure_ascii=False)[:200])
    return out


# ======================================================================== 7. 集計・判定の数・旗・記録
def vent(ms, n, same=0, diff=0, stop=0, sign=0, zero=0, default=0, guards=None, ok=None, unit_bad=0, digit_bad=0, empty=0, out_inrow=0, out_ix=0, lost=0, fields=None):
    u"""導ける関係を満たす組 1 つ(``entry_problems`` が空)。guards = {理由: 止めた数}・ok = {理由: 正しかった止め}。"""
    e = od([(u"番号", n)])
    e.update(ms.zero_entry())
    D = same + diff + stop
    e[u"D"] = D
    e[u"決めて全部同じ"], e[u"決めたが違う"], e[u"止めた"] = same, diff, stop
    e[u"xlsx に書かなかった fact"] = od([(u"行の字が空", empty), (u"型の外", 0), (u"単位が書けない", unit_bad), (u"有効数字が 15 桁を超える", digit_bad)])
    e[u"突き合わせの外"] = od([(u"file", 1 if out_ix else 0), (u"ix:nonFraction の fact", out_ix), (u"うち行の中の数の fact", out_inrow)])
    e[u"行の中の数の fact"] = D + empty + unit_bad + digit_bad + out_inrow
    inner = e[u"決めたが違うの内訳"]
    inner[u"符号だけ違う"] = sign
    inner[u"符号だけ違うのうち答えの値が符号つきの 0"] = zero
    inner[u"去年が空で既定の順を使った"] = default
    for f in (fields or ([u"値"] * diff)):
        inner[u"欄ごと"][f] += 1
    guards = guards or {}
    ok = ok or {}
    rest = stop
    for g in ms.GUARDS:
        e[u"守りの止め"][ms.GUARD_LABEL[g]][u"止めた"] = guards.get(g, 0)
        e[u"守りの止め"][ms.GUARD_LABEL[g]][u"正しかった止め"] = ok.get(g, 0)
        e[u"止めた理由ごと"][g] = guards.get(g, 0)
        rest -= guards.get(g, 0)
    e[u"止めた理由ごと"][u"去年に無い行"] = rest
    e[u"無くなった行"] = lost
    return e


def uniform_entries(ms, **kw):
    u"""番号 1〜63 の全部が同じ数の組。"""
    return [vent(ms, n, **kw) for n in range(1, 64)]


def base60(ms):
    u"""判定の 60 組の全部で予測 XE0-1〜XE0-9 が当たる並び(番号 1〜3 は訓練の数)。D = 200 の組: 同じ 160・違う 0(40 組)か 1(20 組)・止めた 40 か 39。"""
    es = []
    for n in range(1, 64):
        if n <= 3:
            es.append(vent(ms, n, same=10, stop=1))
            continue
        diff = 1 if n % 3 == 0 else 0
        es.append(vent(ms, n, same=160, diff=diff, stop=40 - diff, sign=1 if diff and n % 9 == 0 else 0, guards={u"表の頭が違う": 10, u"期が違う": 1, u"番号つき": 5}, ok={u"表の頭が違う": 5, u"期が違う": 1, u"番号つき": 2},
                     unit_bad=1, empty=10, default=0))
    return es


def judged_of(ms, es):
    return ms.judged(es)


def hits(ms, es):
    j = ms.judged(es)
    return dict((k.split(" ")[0], v[u"当たり"]) for k, v in j.items())


def tot_problems(ms=None):
    ms = ms or MS
    out = []
    es = base60(ms)
    for e in es:
        if ms.entry_problems(e) != u"":
            return [u"作り物の組が導ける関係を満たさない(門の欠陥): %s" % ms.entry_problems(e)]
    h = hits(ms, es)
    if not all(h.values()) or len(h) != 9:
        out.append(u"基準の並びで予測が全部当たらない: %s" % h)
    j = ms.judged(es)
    keys = list(j)
    if [k.split(" ")[0] for k in keys] != [u"XE0-%d" % i for i in range(1, 10)]:
        out.append(u"判定の欄の並びが違う")
    d60 = 60 * 200
    same60, diff60 = 60 * 160, 20
    if dict(j[keys[0]][u"率"]) != {u"fact": same60, u"分母": d60, u"%": 80.0} or dict(j[keys[1]][u"率"]) != {u"fact": diff60, u"分母": d60, u"%": 0.2}:
        out.append(u"XE0-1・XE0-2 の数が違う: %s %s" % (dict(j[keys[0]][u"率"]), dict(j[keys[1]][u"率"])))
    if (j[keys[2]][u"fact"], j[keys[2]][u"決めたが違う"]) != (sum(1 for e in es[3:] if e[u"決めたが違うの内訳"][u"符号だけ違う"]), diff60):
        out.append(u"XE0-3 の数が違う")
    stop60 = 40 * 40 + 20 * 39
    if dict(j[keys[3]][u"率"]) != {u"fact": stop60, u"分母": d60, u"%": 19.8}:
        out.append(u"XE0-4 の数が違う: %s" % dict(j[keys[3]][u"率"]))
    if dict(j[keys[4]][u"率"]) != {u"fact": 480, u"分母": 960, u"%": 50.0} or dict(j[keys[5]][u"率"]) != {u"fact": 60, u"分母": d60, u"%": 0.5}:
        out.append(u"XE0-5・XE0-6 の数が違う: %s %s" % (dict(j[keys[4]][u"率"]), dict(j[keys[5]][u"率"])))
    if dict(j[keys[6]][u"率"]) != {u"fact": 60, u"分母": 60 * 211, u"%": 0.5}:
        out.append(u"XE0-7 の数が違う: %s" % dict(j[keys[6]][u"率"]))
    if (j[keys[7]][u"書類"], j[keys[7]][u"分母"]) != (40, 60) or (j[keys[8]][u"書類"], j[keys[8]][u"分母"]) != (0, 60):
        out.append(u"XE0-8・XE0-9 の数が違う")
    # 訓練の 3 組は判定に入らない(番号 3 / 4 の境)
    es2 = base60(ms)
    for i in range(3):
        es2[i] = vent(ms, i + 1, same=0, diff=500, stop=0, sign=500, guards={}, empty=9000, unit_bad=9000)
    if dumps(ms, ms.judged(es2)) != dumps(ms, ms.judged(es)):
        out.append(u"訓練の 3 組(番号 3 以下)が判定に入っている")
    es3 = base60(ms)
    es3[3] = vent(ms, 4, same=0, diff=200)
    if hits(ms, es3)["XE0-8"] is not True or ms.judged(es3)[keys[7]][u"書類"] != 39:
        out.append(u"番号 4 の組が判定に入らない(番号 3 / 4 の境)")
    # 予測ごとの境(両側)
    cases = []

    def case(name, f, want):
        cases.append((name, f, want))

    def uni(**kw):
        return [vent(ms, n, **kw) for n in range(1, 64)]
    # XE0-1: same ÷ D は 74.0% 以上(D = 100 × 60)
    for same, want in ((74, True), (73, False), (75, True)):
        case(u"XE0-1 同じ %d/100" % same, lambda s=same: uni(same=s, stop=100 - s, diff=0), ("XE0-1", want))
    # 分子・分母の取り違え: 決めたが違うは分子に入れない・分母は D(行の中の数の fact・書かなかった fact を入れない)
    case(u"XE0-1 違いは分子に入らない", lambda: [vent(ms, n, same=73, diff=1, stop=26) for n in range(1, 64)], ("XE0-1", False))
    case(u"XE0-1 分母は D", lambda: [vent(ms, n, same=74, stop=26, empty=100) for n in range(1, 64)], ("XE0-1", True))
    case(u"XE0-4 分母は D", lambda: [vent(ms, n, same=84, stop=16, empty=100) for n in range(1, 64)], ("XE0-4", True))
    case(u"XE0-6 分母は D", lambda: [vent(ms, n, same=900, stop=100, guards={u"期が違う": 21}, empty=2000) for n in range(1, 64)], ("XE0-6", False))
    case(u"XE0-6 分母は D(当たり)", lambda: [vent(ms, n, same=900, stop=100, guards={u"期が違う": 20}, empty=0) for n in range(1, 64)], ("XE0-6", True))
    case(u"XE0-3 分子は符号だけ違う", lambda: [vent(ms, n, same=1000 - (31 if n == 4 else 0), diff=31 if n == 4 else 0, sign=30 if n == 4 else 0) for n in range(1, 64)], ("XE0-3", True))
    case(u"XE0-9 分母はその書類の D", lambda: [vent(ms, n, same=94, stop=6, empty=50) if n > 3 else vent(ms, n, same=1) for n in range(1, 64)], ("XE0-9", True))
    case(u"XE0-9 分母はその書類の D(外れ)", lambda: [vent(ms, n, same=95, stop=5, empty=50) if n > 3 else vent(ms, n, same=1) for n in range(1, 64)], ("XE0-9", False))
    case(u"XE0-9 分子は決めて全部同じ(止めたでない)", lambda: [vent(ms, n, same=5, stop=95) if n > 3 else vent(ms, n, same=1) for n in range(1, 64)], ("XE0-9", True))
    # XE0-2: 違う ÷ D は 0.5% 以下で 1 fact 以上
    def diff_es(total_diff):
        es_ = [vent(ms, n, same=100, stop=100) for n in range(1, 64)]
        for k in range(60):
            dk = total_diff // 60 + (1 if k < total_diff % 60 else 0)
            es_[3 + k] = vent(ms, 4 + k, same=100 - dk, diff=dk, stop=100, fields=[u"値"] * dk)
        return es_
    case(u"XE0-2 違う 0", lambda: diff_es(0), ("XE0-2", False))
    case(u"XE0-2 違う 1", lambda: diff_es(1), ("XE0-2", True))
    case(u"XE0-2 違う 60(0.5%)", lambda: diff_es(60), ("XE0-2", True))
    case(u"XE0-2 違う 61", lambda: diff_es(61), ("XE0-2", False))
    # XE0-3: 符号だけ違う 30 以下
    for k, want in ((30, True), (31, False), (0, True)):
        e_ = [vent(ms, n, same=1000) for n in range(1, 64)]
        e_[3] = vent(ms, 4, same=1000 - k, diff=k, sign=k)
        case(u"XE0-3 符号だけ %d" % k, lambda e_=e_: e_, ("XE0-3", want))
    # XE0-4: 止めた ÷ D は 16.0% 以上 26.0% 以下(D = 1000 の組 60 本)
    for stop, want in ((160, True), (159, False), (260, True), (261, False)):
        case(u"XE0-4 止めた %d/1000" % stop, lambda s=stop: [vent(ms, n, same=1000 - s, stop=s) for n in range(1, 64)], ("XE0-4", want))
    # XE0-5: 守りの止めのうち正しかった止めは 40% 以上 65% 以下(守りの止め 100 の組 60 本)
    for ok, want in ((40, True), (39, False), (65, True), (66, False)):
        case(u"XE0-5 正しかった %d/100" % ok, lambda o=ok: [vent(ms, n, same=1000, stop=100, guards={u"表の頭が違う": 100}, ok={u"表の頭が違う": o}) for n in range(1, 64)], ("XE0-5", want))
    case(u"XE0-5 守りの止めが 0", lambda: [vent(ms, n, same=1000, stop=100) for n in range(1, 64)], ("XE0-5", False))
    # 4 つの守りの全部が分母・分子に入る
    case(u"XE0-5 4 つの守りの合計", lambda: [vent(ms, n, same=1000, stop=100, guards={u"表の頭が違う": 25, u"期が違う": 25, u"番号つき": 25, u"単位が違う": 25}, ok={u"表の頭が違う": 10, u"期が違う": 10, u"番号つき": 10, u"単位が違う": 10}) for n in range(1, 64)], ("XE0-5", True))
    case(u"XE0-5 4 つの守りの合計(外)", lambda: [vent(ms, n, same=1000, stop=100, guards={u"表の頭が違う": 25, u"期が違う": 25, u"番号つき": 25, u"単位が違う": 25}, ok={u"表の頭が違う": 10, u"期が違う": 10, u"番号つき": 10, u"単位が違う": 9}) for n in range(1, 64)], ("XE0-5", False))
    # XE0-6: G1 と G2 の止めは合わせて 1 fact 以上で D の 2.0% 以下(D = 1000 × 60 = 60000 → 1200)
    for g1, g2, want in ((0, 0, False), (1, 0, True), (0, 1, True), (10, 10, True), (20, 0, True), (21, 0, False), (10, 11, False)):
        case(u"XE0-6 G1 %d G2 %d" % (g1, g2), lambda a=g1, b=g2: [vent(ms, n, same=1000 - 2 * a - 2 * b if False else 900, stop=100, guards={u"期が違う": a, u"単位が違う": b, u"表の頭が違う": 100 - a - b}) if n > 3 else vent(ms, n, same=1000) for n in range(1, 64)], ("XE0-6", want))
    # G1・G2 に G・G3 は入らない
    case(u"XE0-6 G と G3 は入らない", lambda: [vent(ms, n, same=900, stop=100, guards={u"表の頭が違う": 50, u"番号つき": 50}) for n in range(1, 64)], ("XE0-6", False))
    # XE0-7: 単位が書けない・15 桁を超えるは行の中の数の fact の 1.0% 以下
    for ub, db, want in ((100, 0, True), (101, 0, False), (50, 50, True), (50, 51, False), (0, 101, False), (0, 100, True)):
        case(u"XE0-7 単位 %d 桁 %d" % (ub, db), lambda a=ub, b=db: [vent(ms, n, same=10000 - a - b, unit_bad=a, digit_bad=b) for n in range(1, 64)], ("XE0-7", want))
    case(u"XE0-7 行の字が空は入らない", lambda: [vent(ms, n, same=10000, empty=1000, unit_bad=0) for n in range(1, 64)], ("XE0-7", True))
    case(u"XE0-7 突き合わせの外は分母に入る", lambda: [vent(ms, n, same=9000, unit_bad=100, out_inrow=1000, out_ix=1000) for n in range(1, 64)], ("XE0-7", True))
    # XE0-8: 決めたが違うが 0 の書類は 60 本のうち 35 本以上
    for zero_docs, want in ((35, True), (34, False), (60, True), (0, False)):
        e_ = [vent(ms, n, same=100, diff=0 if (n - 4) < zero_docs else 1, stop=0, sign=0) if n > 3 else vent(ms, n, same=100) for n in range(1, 64)]
        case(u"XE0-8 違いが 0 の書類 %d" % zero_docs, lambda e_=e_: e_, ("XE0-8", want))
    # XE0-9: 95% 以上の書類は 2 本以下(D が 0 の書類は入れない)
    for k, want in ((2, True), (3, False), (0, True)):
        e_ = [vent(ms, n, same=95 if (n - 4) < k else 94, stop=5 if (n - 4) < k else 6) if n > 3 else vent(ms, n, same=100) for n in range(1, 64)]
        case(u"XE0-9 95%% 以上の書類 %d" % k, lambda e_=e_: e_, ("XE0-9", want))
    case(u"XE0-9 95.0% ちょうど", lambda: [vent(ms, n, same=19, stop=1) for n in range(1, 64)], ("XE0-9", False))
    case(u"XE0-9 94.9%", lambda: [vent(ms, n, same=949, stop=51) for n in range(1, 64)], ("XE0-9", True))
    case(u"XE0-9 D が 0 の書類は 95% 以上に入らない", lambda: [vent(ms, n) for n in range(1, 64)], ("XE0-9", True))
    for name, f, (k, want) in cases:
        got = hits(ms, f())[k]
        if got != want:
            out.append(u"%s: 当たり外れが違う(%s が %s)" % (name, k, got))
    # §0 の旗(4 つの数のどれが 1 違っても立つ・全部同じなら立たない)
    t = [vent(ms, 1, same=2636, stop=669), vent(ms, 2), vent(ms, 3)]
    t[0][u"行の中の数の fact"] = 3434
    t[0][u"xlsx に書かなかった fact"][u"行の字が空"] = 129
    t[0][u"行の中の数の fact"] = 2636 + 669 + 129
    if ms.seal_flag(t + base60(ms)[3:])[u"§0 と違う"] is not False:
        out.append(u"§0 の数と同じなのに旗が立つ: %s" % dict(ms.seal_flag(t + base60(ms)[3:])[u"訓練の 3 組の数"]))
    for what, mut in ((u"行の中の数の fact", lambda e: e.__setitem__(u"行の中の数の fact", 3435)), (u"決めて全部同じ", lambda e: e.__setitem__(u"決めて全部同じ", 2635)),
                      (u"決めたが違う", lambda e: e.__setitem__(u"決めたが違う", 1)), (u"止めた", lambda e: e.__setitem__(u"止めた", 668))):
        t2 = [vent(ms, 1, same=2636, stop=669), vent(ms, 2), vent(ms, 3)]
        t2[0][u"xlsx に書かなかった fact"][u"行の字が空"] = 129
        t2[0][u"行の中の数の fact"] = 3434
        mut(t2[0])
        f = ms.seal_flag(t2 + base60(ms)[3:])
        if f[u"§0 と違う"] is not True:
            out.append(u"§0 の数が %s だけ違うのに旗が立たない" % what)
    # 訓練の数は 3 組の合計(番号 3 以下)・番号 4 以上は入れない
    t3 = [vent(ms, 1, same=1000), vent(ms, 2, same=1000), vent(ms, 3, same=636, stop=669)] + base60(ms)[3:]
    t3[0][u"行の中の数の fact"] = 1000 + 1000
    f = ms.seal_flag(t3)
    if dict(f[u"訓練の 3 組の数"])[u"決めて全部同じ"] != 2636 or dict(f[u"訓練の 3 組の数"])[u"止めた"] != 669:
        out.append(u"旗の訓練の数が番号 3 以下の合計でない: %s" % dict(f[u"訓練の 3 組の数"]))
    # 集計: 訓練 3・判定 60・全部 63(足し算)
    tot = ms.totals_of(es)
    if tot[u"訓練の 3 組"][u"組"] != 3 or tot[u"判定の 60 組"][u"組"] != 60 or tot[u"全部"][u"組"] != 63:
        out.append(u"集計の組の数が違う")
    if tot[u"判定の 60 組"][u"数"][u"D"] != 12000 or tot[u"訓練の 3 組"][u"数"][u"D"] != 33 or tot[u"全部"][u"数"][u"D"] != 12033:
        out.append(u"集計の D が違う: %s %s %s" % (tot[u"判定の 60 組"][u"数"][u"D"], tot[u"訓練の 3 組"][u"数"][u"D"], tot[u"全部"][u"数"][u"D"]))
    if u"番号" in tot[u"全部"][u"数"] or u"番号" in tot[u"判定の 60 組"][u"数"]:
        out.append(u"集計に番号を足している")
    if tot[u"判定の 60 組"][u"数"][u"決めたが違うの内訳"][u"符号だけ違う"] != sum(e[u"決めたが違うの内訳"][u"符号だけ違う"] for e in es[3:]):
        out.append(u"集計の入れ子の数の足し算が違う")
    if tot[u"判定の 60 組"][u"数"][u"守りの止め"][u"守り G 表の頭"][u"正しかった止め"] != 300 or tot[u"全部"][u"数"][u"無くなった行"] != 0:
        out.append(u"集計の入れ子(守りの止め)の足し算が違う")
    # 退化値: 判定の組が空・全部 0・全部止め
    z60 = ms.judged([vent(ms, n) for n in range(1, 64)])
    if any(v[u"当たり"] for k, v in z60.items() if k.split(u" ")[0] not in (u"XE0-3", u"XE0-8", u"XE0-9")):
        out.append(u"全部 0 の組で予測が当たる(分母 0 は当たりにならない)")
    allstop = hits(ms, [vent(ms, n, stop=100, guards={u"表の頭が違う": 100}, ok={u"表の頭が違う": 50}) for n in range(1, 64)])
    if allstop["XE0-1"] or allstop["XE0-4"] or allstop["XE0-2"] or not allstop["XE0-5"] is True and False:
        out.append(u"全部止めで予測が当たる: %s" % allstop)
    return out


def dumps(ms, o):
    return ms.dumps(o)


def entry_shape_problems(ms=None):
    ms = ms or MS
    out = []
    base = vent(ms, 5, same=7, diff=2, stop=5, sign=1, zero=1, default=1, guards={u"表の頭が違う": 3, u"期が違う": 1}, ok={u"表の頭が違う": 2}, unit_bad=1, digit_bad=1, empty=2, out_inrow=1, out_ix=2, fields=[u"値", u"名"])
    base[u"場面"][u"去年の同じ鍵と表示の位が違う"][u"件数"] = 2
    base[u"場面"][u"去年の同じ鍵と表示の位が違う"][u"止めた"] = 2
    if ms.entry_problems(base) != u"":
        return [u"作り物の組が導ける関係を満たさない(門の欠陥): %s" % ms.entry_problems(base)]
    muts = []

    def add(what, f):
        e = json.loads(json.dumps(base), object_pairs_hook=od)
        f(e)
        muts.append((what, e))
    add(u"D", lambda e: e.__setitem__(u"D", e[u"D"] + 1))
    add(u"行の中の数の fact", lambda e: e.__setitem__(u"行の中の数の fact", e[u"行の中の数の fact"] - 1))
    add(u"書かなかった fact(行の字が空)", lambda e: e[u"xlsx に書かなかった fact"].__setitem__(u"行の字が空", 3))
    add(u"書かなかった fact(型の外)", lambda e: e[u"xlsx に書かなかった fact"].__setitem__(u"型の外", 1))
    add(u"書かなかった fact(単位)", lambda e: e[u"xlsx に書かなかった fact"].__setitem__(u"単位が書けない", 2))
    add(u"書かなかった fact(15 桁)", lambda e: e[u"xlsx に書かなかった fact"].__setitem__(u"有効数字が 15 桁を超える", 2))
    add(u"突き合わせの外(行の中 > ix)", lambda e: e[u"突き合わせの外"].__setitem__(u"うち行の中の数の fact", 3))
    add(u"突き合わせの外(file が 0 で ix が在る)", lambda e: e[u"突き合わせの外"].__setitem__(u"file", 0))
    add(u"突き合わせの外(file が在って ix が 0)", lambda e: (e[u"突き合わせの外"].__setitem__(u"ix:nonFraction の fact", 0), e[u"突き合わせの外"].__setitem__(u"うち行の中の数の fact", 0), e.__setitem__(u"行の中の数の fact", e[u"行の中の数の fact"] - 1)))
    add(u"同じ + 違う + 止めた", lambda e: e.__setitem__(u"決めて全部同じ", 8))
    add(u"違う欄の数が違うより少ない", lambda e: e[u"決めたが違うの内訳"][u"欄ごと"].__setitem__(u"値", 0))
    add(u"違う欄 1 つが違うより多い", lambda e: e[u"決めたが違うの内訳"][u"欄ごと"].__setitem__(u"名", 3))
    add(u"符号だけ違う > 違う", lambda e: e[u"決めたが違うの内訳"].__setitem__(u"符号だけ違う", 3))
    add(u"符号つきの 0 > 符号だけ違う", lambda e: e[u"決めたが違うの内訳"].__setitem__(u"符号だけ違うのうち答えの値が符号つきの 0", 2))
    add(u"既定の順 > 違う", lambda e: e[u"決めたが違うの内訳"].__setitem__(u"去年が空で既定の順を使った", 3))
    add(u"符号だけ違う > 値の違い", lambda e: e[u"決めたが違うの内訳"][u"欄ごと"].__setitem__(u"値", 0) or e[u"決めたが違うの内訳"][u"欄ごと"].__setitem__(u"精度", 2))
    add(u"止めた理由ごとの合計", lambda e: e[u"止めた理由ごと"].__setitem__(u"候補が 2 つ以上", 1))
    add(u"守りの止め(止めた)", lambda e: e[u"守りの止め"][u"守り G 表の頭"].__setitem__(u"止めた", 2))
    add(u"守りの止め(正しかった > 止めた)", lambda e: e[u"守りの止め"][u"守り G1 期"].__setitem__(u"正しかった止め", 2))
    add(u"場面(負の印あり > D)", lambda e: e[u"場面"].__setitem__(u"負の印あり", 15))
    add(u"場面(表示の数が 0 > D)", lambda e: e[u"場面"].__setitem__(u"表示の数が 0", 15))
    add(u"場面(空 > D)", lambda e: e[u"場面"].__setitem__(u"空", 15))
    add(u"場面(逆 > D)", lambda e: e[u"場面"].__setitem__(u"符号の向きが逆", 15))
    add(u"場面(表示の位の分け)", lambda e: e[u"場面"][u"去年の同じ鍵と表示の位が違う"].__setitem__(u"決めて全部同じ", 1))
    add(u"場面(表示の位の件数 > D)", lambda e: e[u"場面"][u"去年の同じ鍵と表示の位が違う"].__setitem__(u"件数", 15))
    add(u"欄の並び", lambda e: e.move_to_end(u"D"))
    add(u"欄が足りない", lambda e: e.pop(u"場面"))
    add(u"余計な欄", lambda e: e.__setitem__(u"余計", 1))
    for what, e in muts:
        if ms.entry_problems(e) == u"":
            out.append(u"組の導ける関係の違いを止めない: %s" % what)
    return out


def rec_problems(ms=None):
    ms = ms or MS
    out = []
    es = base60(ms)
    mat = ms.material_of([(u"S1ZZ%04d" % i, u"p", [u"E99%03d" % i]) for i in range(5)], [(i, u"s", u"p", u"S1ZP%04d" % i, u"q", u"E98%03d" % i) for i in range(1, 6)])
    names = set([u"Itemq", u"xa_cor"])
    secret = ms.secret_of([(u"S1ZZ%04d" % i, u"p", [u"E99%03d" % i]) for i in range(5)], [(i, u"s", u"p", u"S1ZP%04d" % i, u"q", u"E98%03d" % i) for i in range(1, 6)], names)
    rec, _sec = ms.build_record(es, [(u"組の数", 63)] + mat[:0], secret)
    mt = dict(mat)
    if (mt[u"今年の側の書類の本数"], mt[u"組の数"], mt[u"訓練の組の数"], mt[u"判定の組の数"], mt[u"除いた今年の書類の数"]) != (5, 5, 3, 2, 0) or len(mt) != 7 \
            or mt[u"前の年の側の組の相手の file 名の並びの sha256"] != hashlib.sha256(u"\n".join(u"S1ZP%04d" % i for i in range(1, 6)).encode("utf-8")).hexdigest() \
            or mt[u"今年の側の書類の file 名の並びの sha256"] != hashlib.sha256(u"\n".join(sorted(u"S1ZZ%04d" % i for i in range(5))).encode("utf-8")).hexdigest():
        out.append(u"材料の欄(本数・組の数・訓練と判定の組の数・並びの sha256)が違う: %s" % mt)
    if not (set([u"Itemq", u"xa_cor"]) <= secret[1]) or u"ab" in secret[1] or set(secret[2]) != set([u"S1ZZ%04d" % i for i in range(5)] + [u"S1ZP%04d" % i for i in range(1, 6)]) \
            or secret[3] != set([u"E98%03d" % i for i in range(1, 6)] + [u"E99%03d" % i for i in range(5)]) or len(secret) != 6:
        out.append(u"記録に書かないものの集まりが違う")
    sec2 = ms.secret_of([(u"S1ZZ0001", u"p", [u"x E12345 y"])], [(1, u"s", u"p", u"S1ZP0001", u"q", u"E55555")], set([u"ab", u"abc"]))
    if sec2[1] != set([u"abc"]) or sec2[3] != set([u"E55555", u"E12345"]):
        out.append(u"要素の名は 3 字以上・EDINET コードは書類の字の中からも集める")
    if list(rec) != [u"seal", u"封の commit", u"step", u"この script の sha256", u"材料", u"書類", u"集計", u"予測の判定に要る数(XE0-1〜XE0-9。判定の 60 組だけ。当たり・外れ)", u"型の欄ごとの出どころ", u"§3 の旗", u"限界"]:
        out.append(u"記録の欄の並びが違う: %s" % list(rec))
    if rec[u"封の commit"] != SEAL_COMMIT_SHORT or rec[u"seal"] != SEAL_REL or rec[u"限界"] != list(ms.LIMITS) or rec[u"この script の sha256"] != sha_of(SCRIPT_REL):
        out.append(u"記録の封の commit・封の path・限界・script の sha256 が違う")
    if len(rec[u"書類"]) != 63 or rec[u"集計"][u"判定の 60 組"][u"組"] != 60 or rec[u"集計"][u"訓練の 3 組"][u"組"] != 3:
        out.append(u"記録の組の数が違う")
    jk = [k for k in rec if k.startswith(u"予測の判定に要る数")]
    if len(jk) != 1 or ms.dumps(rec[jk[0]]) != ms.dumps(ms.judged(es)):
        out.append(u"記録の判定の数が judged と違う")
    if dict(rec[u"型の欄ごとの出どころ"]) != dict(ms.ORIGIN) or set(rec[u"型の欄ごとの出どころ"].values()) != set([u"去年から持ち越し", u"会社が書いた欄からそのまま", u"規則で(日付が 1 つか 2 つか)", u"会社が書いた欄からそのまま(表示の位は規則で)",
                                                                                         u"規則で(負の印)と去年から持ち越し(符号の向き)", u"規則で(単位の字の表の逆引き)", u"規則で(数のセルの表示形式)", u"会社が書いた欄からそのまま(「－」)"]):
        out.append(u"型の欄ごとの出どころの表が違う")
    if rec[u"§3 の旗"][u"§0 と違う"] is not True:
        out.append(u"作り物の訓練の数が §0 と違うのに旗が立たない")
    # 組の数・番号の並び
    shifted = [dict(e, **{u"番号": e[u"番号"] + 1}) for e in es]
    for what, bad in ((u"62 組", es[:-1]), (u"番号の重なり", es[:-1] + [vent(ms, 62, same=1)]), (u"番号の逆順", list(reversed(es))), (u"番号が 2〜64(訓練 2・判定 61)", shifted)):
        if not stops(ms, ms.build_record, bad, [], secret):
            out.append(u"組が 63・番号が昇順でないのに止まらない: %s" % what)
    # --check(導き直し): 正しい記録は通り、集計・判定・旗・組の数・限界・出どころの 1 つが違えば止まる
    text = ms.dumps(rec)
    ms.verify_record(rec, text)
    ms.verify_record(json.loads(text, object_pairs_hook=od))

    def mutate_rec(f):
        r = json.loads(text, object_pairs_hook=od)
        f(r)
        return r
    jkey = jk[0]

    def resealed(f):
        r = mutate_rec(f)
        r[u"集計"] = ms.totals_of(r[u"書類"])
        r[jkey] = ms.judged(r[u"書類"])
        r[u"§3 の旗"] = ms.seal_flag(r[u"書類"])
        return r
    for what, f in ((u"D が足し算と合わない(集計・判定・旗は導き直した)", lambda r: r[u"書類"][10].__setitem__(u"D", r[u"書類"][10][u"D"] + 1)),
                    (u"止めた理由ごとが止めたと合わない(導き直した)", lambda r: r[u"書類"][10][u"止めた理由ごと"].__setitem__(u"去年に無い行", 0)),
                    (u"欄が足りない(導き直した)", lambda r: r[u"書類"][10].pop(u"場面"))):
        r = resealed(f)
        if not stops(ms, ms.verify_record, r):
            out.append(u"記録の組の関係の違いを --check が止めない(導き直した後): %s" % what)
    for what, f in ((u"集計の D", lambda r: r[u"集計"][u"判定の 60 組"][u"数"].__setitem__(u"D", 1)), (u"集計の組", lambda r: r[u"集計"][u"全部"].__setitem__(u"組", 62)),
                    (u"判定の当たり", lambda r: r[jkey][u"XE0-1 決めて全部同じ ÷ D"].__setitem__(u"当たり", False)),
                    (u"判定の率", lambda r: r[jkey][u"XE0-4 止めた ÷ D"][u"率"].__setitem__(u"fact", 1)), (u"旗", lambda r: r[u"§3 の旗"].__setitem__(u"§0 と違う", False)),
                    (u"組の数", lambda r: r[u"材料"].__setitem__(u"組の数", 62)), (u"限界", lambda r: r[u"限界"].pop()), (u"出どころ", lambda r: r[u"型の欄ごとの出どころ"].__setitem__(u"精度", u"去年から持ち越し")),
                    (u"書類の組の数が足し算と合わない", lambda r: r[u"書類"][10].__setitem__(u"D", r[u"書類"][10][u"D"] + 1)), (u"書類を 1 組落とす", lambda r: r[u"書類"].pop()),
                    (u"番号の並び", lambda r: r[u"書類"].reverse()), (u"訓練の旗の数", lambda r: r[u"§3 の旗"][u"訓練の 3 組の数"].__setitem__(u"止めた", 669)),
                    (u"禁止のもの(日付の形)", lambda r: r[u"材料"].__setitem__(u"x", u"2030-04-01")), (u"禁止のもの(docID の形)", lambda r: r[u"材料"].__setitem__(u"x", u"S1ZZ9999")),
                    (u"禁止のもの(EDINET コードの形)", lambda r: r[u"材料"].__setitem__(u"x", u"E99991")), (u"禁止の欄", lambda r: r[u"材料"].__setitem__(u"name", 1))):
        if not stops(ms, ms.verify_record, mutate_rec(f)):
            out.append(u"記録の導き直しが止めない: %s" % what)
    # 禁止のもの
    out += clean_problems(ms)
    # 排他・書いた後の検査
    with Temp() as d:
        p = os.path.join(d, "rec.json")
        ms.write_record(p, rec, secret)
        if not stops(ms, ms.write_record, p, rec, secret):
            out.append(u"記録が既に在るのに書き直せる")
        if json.loads(open(p, encoding="utf-8").read(), object_pairs_hook=od) != json.loads(text, object_pairs_hook=od):
            out.append(u"書いた記録が dumps と違う")
        with open(os.path.join(d, "bad.json"), "w") as fh:
            fh.write(u"{}")
        bad_rec = mutate_rec(lambda r: r[u"材料"].__setitem__(u"x", u"2030-04-01"))
        if not stops(ms, ms.record_text, bad_rec, secret):
            out.append(u"日付の形の字が在る記録を書ける")
        q = os.path.join(d, "q.json")
        if not stops(ms, ms.write_record, q, mutate_rec(lambda r: r[u"材料"].__setitem__(u"x", u"S1ZZ0001")), secret) or os.path.exists(q):
            out.append(u"書く前の検査が止めない(file を作る)")
        # 書く前の検査: 禁止のものが在れば書き出しに入らない / 書いた後の検査: 書いた字に禁止のものが在れば file を消す
        wrote = []
        orig = ms.write_exclusive
        ms.write_exclusive = lambda path, data: wrote.append(path)
        try:
            stopped = stops(ms, ms.write_record, os.path.join(d, "r1.json"), mutate_rec(lambda r: r[u"材料"].__setitem__(u"x", u"S1ZZ0001")), secret)
        finally:
            ms.write_exclusive = orig
        if not stopped or wrote:
            out.append(u"書く前の検査が止めない(書き出しに入る)")
        r2 = os.path.join(d, "r2.json")
        ms.write_exclusive = lambda path, data: orig(path, data + u"\n 2030-03-31".encode("utf-8"))
        try:
            stopped = stops(ms, ms.write_record, r2, rec, secret)
        finally:
            ms.write_exclusive = orig
        if not stopped or os.path.exists(r2):
            out.append(u"書いた後の検査が止めない(か file を消さない)")
        if not raises(FileExistsError, ms.write_exclusive, p, b"x"):
            out.append(u"write_exclusive が既に在る file に書ける")
    # --check は置き場を読まない(記録の path が無ければ止まる・在れば通る)
    with Temp() as d:
        os.makedirs(os.path.join(d, os.path.dirname(ms.RECORD_REL)))
        if not stops(ms, ms.check, root=d):
            out.append(u"記録が無いのに --check が止まらない")
        ms.write_record(os.path.join(d, ms.RECORD_REL), rec, secret)
        msgs = []
        got = ms.check(root=d, say=msgs.append)
        if len(got[u"書類"]) != 63 or len(msgs) != 1:
            out.append(u"--check が記録を読んで通らない")
    return out


def clean_problems(ms=None):
    ms = ms or MS
    out = []
    secret = (set(), set([u"Itemq", u"xa_cor"]), ["S1ZZ0001", "S1ZP0001"], set(["E99001"]), set([u"見出しの字だよ"]), set())
    for what, bad in ((u"docID の形", od([(u"x", u"S1ZZ9999")])), (u"EDINET コードの形", od([(u"x", u"E99991")])), (u"日付の形", od([(u"x", u"2030-03-31")])),
                      (u"禁止の欄", od([(u"docid", 1)])), (u"禁止の欄(名)", od([(u"name", 1)])), (u"今年の側の docID", od([(u"x", u"a S1ZZ0001 b")])),
                      (u"前の年の側の docID", od([(u"x", u"a S1ZP0001 b")])), (u"コード", od([(u"x", u"a E99001 b")])), (u"要素の局所名", od([(u"x", u"a Itemq b")])),
                      (u"接頭辞の字", od([(u"x", u"a xa_cor b")]))):
        if not stops(ms, ms.record_text, bad, secret):
            out.append(u"記録の検査が止めない: %s" % what)
    if stops(ms, ms.record_text, od([(u"a", 1), (u"seal", ms.SEAL_REL), (u"b", u"_cor で終わる")]), secret):
        out.append(u"封の path の中の日付で止まる(書いてよい)")
    return out


# ======================================================================== 8. 3 つの工程を別の folder で通す(作り物の組・作り物の読み出し)
def fake_pairs(n=5):
    return [(i, u"stem%d" % i, u"CUR%d" % i, u"pstem%d" % i, u"PRIOR%d" % i, u"E9%04d" % i) for i in range(1, n + 1)]


def dev_problems(ms=None):
    ms = ms or MS
    out = []
    calls = []

    def reader(path):
        calls.append(path)
        if path.startswith(u"CUR"):
            return cur_s1()
        if path.startswith(u"PRIOR"):
            return prior_s1()
        raise AssertionError(path)
    with Temp() as d:
        tmp = os.path.join(d, u"w")
        entries = ms.dev_run(tmp, pairs=fake_pairs(5), reader=reader, say=lambda *a: None)
        if sorted(calls) != sorted([u"CUR1", u"CUR2", u"CUR3", u"PRIOR1", u"PRIOR2", u"PRIOR3"]):
            out.append(u"番号 1・2・3 の組だけを読まない: %s" % sorted(calls))
        if [e[u"番号"] for e in entries] != [1, 2, 3] or any(e[u"D"] != 31 or e[u"止めた"] != 10 or e[u"決めたが違う"] != 4 for e in entries):
            out.append(u"3 組が 3 工程を通った数が手の数と違う")
        if sorted(os.listdir(tmp)) != [u"answer", u"out", u"xlsx"] or sorted(os.listdir(os.path.join(tmp, u"xlsx"))) != [u"01.xlsx", u"02.xlsx", u"03.xlsx"] \
                or sorted(os.listdir(os.path.join(tmp, u"answer"))) != [u"01.json", u"02.json", u"03.json"] or sorted(os.listdir(os.path.join(tmp, u"out"))) != [u"01.json", u"02.json", u"03.json"]:
            out.append(u"xlsx・答え・出力の folder が別に 3 つ書かれない: %s" % sorted(os.listdir(tmp)))
        for f in os.listdir(os.path.join(tmp, u"xlsx")):
            if not f.endswith(u".xlsx"):
                out.append(u"xlsx の folder に xlsx でないものが在る")
        if os.path.exists(os.path.join(ROOT, RECORD_REL)) is False and os.path.exists(os.path.join(ROOT, os.path.dirname(RECORD_REL), u"company_excel_dev.json")):
            out.append(u"dev が記録を書いた")
        # 答えの file は答えの folder にだけ在る(xlsx の folder・出力の folder に答えの字が無い)
        a = json.loads(open(os.path.join(tmp, u"answer", u"01.json"), encoding="utf-8").read(), object_pairs_hook=od)
        if a[u"番号"] != 1 or len(a[u"答え"]) != 31 or a[u"数"][u"D"] != 31:
            out.append(u"答えの file の形が違う")
        o = json.loads(open(os.path.join(tmp, u"out", u"01.json"), encoding="utf-8").read(), object_pairs_hook=od)
        if o[u"番号"] != 1 or len(o[u"受けた"][u"rows"]) != 31 or o[u"受けた"][u"lost"] != 6:
            out.append(u"出力の file の形が違う")
        if u"mark" in json.dumps(o, ensure_ascii=False):
            out.append(u"出力の file に答えの側の欄(負の印)が在る")
        # folder が既に在れば止まる(上書きしない)
        if not raises(FileExistsError, ms.make_folders, tmp, [(9, u"s", u"CUR9", u"ps", u"PRIOR9", u"E90009")], reader):
            out.append(u"作る側が既に在る folder に書き直せる")
        if not raises(FileExistsError, ms.receive_folder, os.path.join(tmp, u"xlsx"), os.path.join(tmp, u"out"), {}, reader):
            out.append(u"受ける側が既に在る folder に書き直せる")
        # 採点は出力の folder と答えの folder から(読み出しを呼ばない)
        calls[:] = []
        ents, names = ms.score_folders(os.path.join(tmp, u"out"), os.path.join(tmp, u"answer"), [1, 2, 3])
        if calls or [e[u"番号"] for e in ents] != [1, 2, 3] or u"Item1" not in names or u"xa_cor" not in names:
            out.append(u"採点が出力と答えだけから数えない・名の集まり(secret 用)が無い")
        # 番号の食い違いは止まる
        os.makedirs(os.path.join(d, u"o2"))
        os.makedirs(os.path.join(d, u"a2"))
        shutil.copy(os.path.join(tmp, u"out", u"01.json"), os.path.join(d, u"o2", u"02.json"))
        shutil.copy(os.path.join(tmp, u"answer", u"02.json"), os.path.join(d, u"a2", u"02.json"))
        if not stops(ms, ms.score_folders, os.path.join(d, u"o2"), os.path.join(d, u"a2"), [2]):
            out.append(u"出力の番号が file の番号と違うのに止まらない")
    # dev は番号 4 以上の組を分析しない(読み出しを呼ばない)
    calls[:] = []
    with Temp() as d:
        ms.dev_run(os.path.join(d, u"w"), pairs=fake_pairs(63), reader=reader, say=lambda *a: None)
    if [c for c in calls if c.endswith(tuple(str(i) for i in range(4, 10))) or c in (u"CUR10", u"PRIOR10")] != [] or len(calls) != 6:
        out.append(u"dev が番号 4 以上の組を読む: %d 回" % len(calls))
    # 入口: 工程の指定が無い・dev に --tmp が無いと止まる(置き場は読まない)
    if not stops(ms, ms.main, []) or not stops(ms, ms.main, ["--dev"]):
        out.append(u"工程の指定が無い・--dev に --tmp が無いのに止まらない")
    # 受ける側へ渡すのは組の番号と去年の path だけ
    pp = ms.prior_paths_of(fake_pairs(5))
    if pp != {1: u"PRIOR1", 2: u"PRIOR2", 3: u"PRIOR3", 4: u"PRIOR4", 5: u"PRIOR5"} or ms.prior_paths_of(fake_pairs(5), set([2, 4])) != {2: u"PRIOR2", 4: u"PRIOR4"}:
        out.append(u"受ける側へ渡す path が組の番号と去年の path でない: %s" % pp)
    return out


# ======================================================================== 8b. 入口の配線(作り物の組・作り物の読み出し。``Y.make_pairs`` と ``read_zip_side`` を使う側の実体へ差し替える)
DOCS_ARG, PRIOR_ARG = u"DOCS-ARG", u"PRIOR-ARG"


def empty_dir_of(d):
    u"""``root=`` に渡す一時の folder(記録は ``out=`` で別の path に書くので、root の下には書かない)。"""
    return os.path.join(d, u"unused_root")


def entry_wiring_problems(ms=None):
    u"""``main`` の 5 つの分岐・``score_run``・``material_of``・``check`` を、作り物の 63 組で本物のまま通す。引数の入れ替え・落としで赤になる。
    記録は一時の folder にだけ書く(書き先が一時の folder の外なら書かずに赤)。"""
    ms = ms or MS
    out = []
    pairs = fake_pairs(63)
    docs = [(u"S1ZZ%04d" % i, u"DP%d" % i, [u"E99%03d" % i]) for i in range(70)]
    calls, reads, wrote = [], [], []

    def fake_make_pairs(docs_dir, prior_dir):
        calls.append((docs_dir, prior_dir))
        return docs, pairs, []

    def reader(path):
        reads.append(path)
        if path.startswith(u"CUR"):
            return cur_s1()
        if path.startswith(u"PRIOR"):
            return prior_s1()
        raise AssertionError(path)

    def run(label, argv):
        u"""main を通す。標準出力は返す。例外は問題に書く。"""
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                ms.main(argv)
        except BaseException as exc:                # noqa: BLE001
            out.append(u"%s が例外で止まった: %s" % (label, type(exc).__name__))
            return None
        return buf.getvalue()

    orig_mp, orig_rz, orig_wr = ms.Y.make_pairs, ms.read_zip_side, ms.write_record
    state = {"dir": None}

    def guarded_write(path, rec, secret=None):
        wrote.append((path, secret))
        if state["dir"] is None or not os.path.abspath(path).startswith(os.path.abspath(state["dir"]) + os.sep):
            out.append(u"記録の書き先が一時の folder の外(書かずに止める): %s" % os.path.basename(path))
            return None
        return orig_wr(path, rec, secret)
    ms.Y.make_pairs, ms.read_zip_side, ms.write_record = fake_make_pairs, reader, guarded_write
    try:
        with Temp() as d:
            state["dir"] = d
            t = os.path.join(d, u"w")
            xl, ou, an = os.path.join(t, u"xlsx"), os.path.join(t, u"out"), os.path.join(t, u"answer")
            # --make
            del calls[:], reads[:]
            run(u"--make", ["--make", t, "--docs", DOCS_ARG, "--prior", PRIOR_ARG])
            if calls != [(DOCS_ARG, PRIOR_ARG)]:
                out.append(u"--make が今年の側・前の年の側の置き場を make_pairs に渡さない・入れ替える: %s" % calls)
            if not os.path.isdir(t) or sorted(os.listdir(t)) != [u"answer", u"xlsx"] or len(os.listdir(xl)) != 63 or len(os.listdir(an)) != 63:
                out.append(u"--make が 63 組の xlsx と答えを別の folder に書かない")
            if sorted(reads) != sorted([u"CUR%d" % i for i in range(1, 64)]):
                out.append(u"--make が 63 組の今年の側だけを読まない: %d 回" % len(reads))
            # --receive(前の年の path だけを読む)
            del calls[:], reads[:]
            run(u"--receive", ["--receive", xl, ou, "--docs", DOCS_ARG, "--prior", PRIOR_ARG])
            if calls != [(DOCS_ARG, PRIOR_ARG)]:
                out.append(u"--receive が置き場を make_pairs に渡さない・入れ替える: %s" % calls)
            if sorted(reads) != sorted([u"PRIOR%d" % i for i in range(1, 64)]):
                out.append(u"--receive が前の年の path だけを 63 組読まない: %d 回" % len(reads))
            if not os.path.isdir(ou) or sorted(os.listdir(ou)) != sorted([u"%02d.json" % i for i in range(1, 64)]):
                out.append(u"--receive が出力の folder に 63 組を書かない(引数が入れ替わっている)")
            if os.path.isdir(xl) and len(os.listdir(xl)) != 63:
                out.append(u"--receive が xlsx の folder を書き換えた")
            # --score(記録は一時の folder にだけ)
            del calls[:], reads[:], wrote[:]
            text = run(u"--score", ["--score", ou, an, "--root", d, "--docs", DOCS_ARG, "--prior", PRIOR_ARG])
            if calls != [(DOCS_ARG, PRIOR_ARG)]:
                out.append(u"--score が置き場を make_pairs に渡さない・入れ替える: %s" % calls)
            if reads:
                out.append(u"--score が読み出しを呼んだ")
            recp = os.path.join(d, ms.RECORD_REL)
            if len(wrote) != 1 or wrote[0][0] != recp:
                out.append(u"--score が --root の下の記録の path に書かない: %s" % [os.path.relpath(w[0], d) if os.path.abspath(w[0]).startswith(d) else u"外" for w in wrote])
            sec = wrote[0][1] if wrote else None
            if sec is None or len(sec) != 6 or set(sec[2]) != set([x[0] for x in docs] + [p[3] for p in pairs]) or sec[3] != set([p[5] for p in pairs] + [u"E99%03d" % i for i in range(70)]) \
                    or not set([u"Item1", u"xa_cor"]) <= sec[1]:
                out.append(u"--score が書く前の検査に記録に書かないものの集まり(docID・コード・名)を渡さない・入れ替える")
            if text is None or u"(組 63)" not in text or os.path.basename(recp) not in text or u"§3 の旗: " not in text:
                out.append(u"--score の表示が違う: %s" % text)
            if not os.path.isfile(recp):
                out.append(u"--score が記録を書かない")
                return out
            rec = json.loads(io.open(recp, encoding="utf-8").read(), object_pairs_hook=od)
            mt = rec[u"材料"]
            want_mt = od([(u"今年の側の書類の本数", 70), (u"今年の側の書類の file 名の並びの sha256", hashlib.sha256(u"\n".join(sorted(x[0] for x in docs)).encode("utf-8")).hexdigest()),
                          (u"組の数", 63), (u"訓練の組の数", 3), (u"判定の組の数", 60), (u"除いた今年の書類の数", 7),
                          (u"前の年の側の組の相手の file 名の並びの sha256", hashlib.sha256(u"\n".join(p[3] for p in pairs).encode("utf-8")).hexdigest())])
            if json.dumps(mt, ensure_ascii=False) != json.dumps(want_mt, ensure_ascii=False):
                out.append(u"記録の材料が手の値と違う(書類の本数 70・組の数 63・除いた 7): %s" % dict(mt))
            if [e[u"番号"] for e in rec[u"書類"]] != list(range(1, 64)) or any(e[u"D"] != 31 or e[u"止めた"] != 10 or e[u"決めたが違う"] != 4 for e in rec[u"書類"]):
                out.append(u"--score の組の数が手の数と違う(出力の folder と答えの folder が入れ替わっている)")
            # 直接呼ぶ score_run・dev_run・置き場の既定
            direct, msgs2 = os.path.join(d, u"direct.json"), []
            del calls[:], wrote[:]
            got = guard(ms.score_run, ou, an, root=empty_dir_of(d), docs=DOCS_ARG, prior=PRIOR_ARG, out=direct, say=msgs2.append)
            if not isinstance(got, dict) or got.get(u"seal") != ms.SEAL_REL:
                out.append(u"score_run が記録を返さない・例外で止まった: %s" % (got[0] if isinstance(got, list) else type(got).__name__))
            if calls != [(DOCS_ARG, PRIOR_ARG)] or [w[0] for w in wrote] != [direct] or not os.path.isfile(direct) or len(msgs2) != 2 or not msgs2[0].startswith(u"§3 の旗: ") \
                    or msgs2[1] != u"-> direct.json(組 63)":
                out.append(u"score_run が out= の path に書かない・say に 旗と記録の行を出さない: %s" % msgs2)
            # dev_run の say(標準出力へ出さず say に 1 つ出す)
            msgs3 = []
            ents = guard(ms.dev_run, os.path.join(d, u"dev2"), pairs=pairs, reader=reader, say=msgs3.append)
            if not isinstance(ents, list) or len(ents) != 3 or len(msgs3) != 1 or u"封 §0 と照らす" not in msgs3[0]:
                out.append(u"dev_run が say に表示を 1 つ出さない・3 組の数を返さない")
            # 旗の表示の向き(立つ記録は「立った」・立たない記録は「立たない」。向きを入れ替えると赤)
            for up, want_s in ((True, u"§3 の旗: 立った"), (False, u"§3 の旗: 立たない")):
                msgs4 = []
                guard(ms.show_flag, {u"§3 の旗": {u"§0 と違う": up}}, say=msgs4.append)
                if msgs4 != [want_s]:
                    out.append(u"show_flag が旗が%sときの表示を「%s」にしない: %s" % (u"立つ" if up else u"立たない", want_s, msgs4))
            # 置き場の既定: 引数が無ければ既定の置き場・片方だけ渡せばその 1 つだけ入れ替わらない
            for tag, extra, want_c in ((u"b", [], (ms.DOCS_DIR, ms.PRIOR_DIR)), (u"c", ["--prior", PRIOR_ARG], (ms.DOCS_DIR, PRIOR_ARG)), (u"e", ["--docs", DOCS_ARG], (DOCS_ARG, ms.PRIOR_DIR))):
                t2 = os.path.join(d, u"w_" + tag)
                for label, argv in ((u"--make", ["--make", t2]), (u"--receive", ["--receive", os.path.join(t2, u"xlsx"), os.path.join(t2, u"out")]),
                                    (u"--score", ["--score", os.path.join(t2, u"out"), os.path.join(t2, u"answer"), "--root", os.path.join(d, u"root_" + tag)]),
                                    (u"--dev", ["--dev", "--tmp", os.path.join(d, u"dev_" + tag)])):
                    del calls[:]
                    run(label + u"(既定の置き場)", argv + extra)
                    if calls != [want_c]:
                        out.append(u"%s が置き場の既定(%s)を make_pairs に渡さない: %s" % (label, tag, calls))
            # --dev
            del calls[:], reads[:]
            run(u"--dev", ["--dev", "--tmp", os.path.join(d, u"dev"), "--docs", DOCS_ARG, "--prior", PRIOR_ARG])
            if calls != [(DOCS_ARG, PRIOR_ARG)]:
                out.append(u"--dev が置き場を make_pairs に渡さない・入れ替える: %s" % calls)
            if sorted(reads) != sorted([u"CUR1", u"CUR2", u"CUR3", u"PRIOR1", u"PRIOR2", u"PRIOR3"]):
                out.append(u"--dev が 3 組の作る側(今年の側)・受ける側(前の年の側)だけを読まない: %s" % sorted(reads))
            # --check(--root・導き直し・rec_path・want)
            msgs = run(u"--check", ["--check", "--root", d])
            if msgs is None or u"(組 63)" not in msgs:
                out.append(u"--check が --root の下の記録を検査して通らない")
            good = json.loads(io.open(recp, encoding="utf-8").read(), object_pairs_hook=od)
            jk = [k for k in good if k.startswith(u"予測の判定に要る数")][0]

            def tampered(name, f):
                r = json.loads(json.dumps(good), object_pairs_hook=od)
                f(r)
                p = os.path.join(d, u"bad_%s.json" % name)
                with io.open(p, "w", encoding="utf-8") as fh:
                    fh.write(ms.dumps(r))
                return p
            tamper_cases = ((u"d", lambda r: r[u"書類"][10].__setitem__(u"D", r[u"書類"][10][u"D"] + 1)),
                            (u"tot", lambda r: r[u"集計"][u"判定の 60 組"][u"数"].__setitem__(u"D", 1)),
                            (u"judge", lambda r: r[jk][u"XE0-1 決めて全部同じ ÷ D"].__setitem__(u"当たり", not r[jk][u"XE0-1 決めて全部同じ ÷ D"][u"当たり"])),
                            (u"flag", lambda r: r[u"§3 の旗"].__setitem__(u"§0 と違う", not r[u"§3 の旗"][u"§0 と違う"])))
            empty_root = os.path.join(d, u"empty")
            os.makedirs(empty_root)
            for name, f in tamper_cases:
                bad = tampered(name, f)
                if not stops(ms, ms.check, root=d, rec_path=bad, say=lambda *a: None):
                    out.append(u"check が改竄した記録を止めない(verify_record を呼ばない): %s" % name)
                troot = os.path.join(d, u"troot_%s" % name)
                os.makedirs(os.path.join(troot, os.path.dirname(ms.RECORD_REL)))
                shutil.copy(bad, os.path.join(troot, ms.RECORD_REL))
                with contextlib.redirect_stdout(io.StringIO()):
                    main_stopped = stops(ms, ms.main, ["--check", "--root", troot])
                if not main_stopped:
                    out.append(u"--check が --root の下の改竄した記録を止めない: %s" % name)
            # rec_path: root に記録が無くても rec_path の記録を読む・root に良い記録が在っても rec_path の改竄を読む
            if stops(ms, ms.check, root=empty_root, rec_path=recp, say=lambda *a: None):
                out.append(u"check が rec_path の記録を読まない(root の下を読む)")
            if not stops(ms, ms.check, root=d, rec_path=tampered(u"d2", tamper_cases[0][1]), say=lambda *a: None):
                out.append(u"check が rec_path でなく root の下の記録を読む")
            # want
            if not stops(ms, ms.check, root=d, rec_path=recp, say=lambda *a: None, want=62):
                out.append(u"check が組の数 want を verify_record に渡さない")
            if guard(ms.check, root=d, rec_path=recp, say=lambda *a: None, want=63) != guard(ms.check, root=d, say=lambda *a: None) or len(guard(ms.check, root=d, say=lambda *a: None)[u"書類"]) != 63:
                out.append(u"check が記録を返さない")
    finally:
        ms.Y.make_pairs, ms.read_zip_side, ms.write_record = orig_mp, orig_rz, orig_wr
    return out


# ======================================================================== 9. 受ける側は今年の書類も答えも無い場所で動く
RECEIVE_FUNCS = ("receive_folder", "receive_pair", "receive_row", "decide_row", "read_xlsx", "read_amount", "prior_table", "numbered_cand", "date_text")
DENY_NAMES = ("make_pairs", "DOCS_DIR", "make_folders", "make_pair_files", "sheet_rows_of", "write_xlsx", "score_folders", "score_pair", "load_json", "score_run", "read_zip_side_cur", "Y")


def iso_ast_problems(src=None):
    u"""受ける側の関数の中に、答えを読む名・今年の zip を開く名・今年の書類の path を取る引数が無い。"""
    src = src if src is not None else read(SCRIPT_REL)
    tree = ast.parse(src)
    funcs = dict((n.name, n) for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    out = []
    for fn in RECEIVE_FUNCS:
        if fn not in funcs:
            out.append(u"受ける側の関数が無い: %s" % fn)
            continue
        f = funcs[fn]
        for a in f.args.args + f.args.kwonlyargs:
            low = a.arg.lower()
            if any(w in low for w in ("answer", "zip", "cur", "docs", "truth")):
                out.append(u"%s の引数に今年の書類か答えを取る名が在る: %s" % (fn, a.arg))
        docs_ = set([id(f.body[0].value)]) if f.body and isinstance(f.body[0], ast.Expr) and isinstance(f.body[0].value, ast.Constant) else set()
        for n in ast.walk(f):
            if id(n) in docs_:
                continue
            if isinstance(n, ast.Name) and n.id in DENY_NAMES:
                out.append(u"%s が使ってはいけない名を使う: %s" % (fn, n.id))
            if isinstance(n, ast.Attribute) and n.attr in DENY_NAMES:
                out.append(u"%s が使ってはいけない名を使う: %s" % (fn, n.attr))
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and (u"answer" in n.value or u"答え" in n.value or u"zip" in n.value.lower()):
                out.append(u"%s が答え・zip の字を持つ: %s" % (fn, n.value))
    f = funcs.get("receive_pair")
    if f is not None and [a.arg for a in f.args.args] != ["xlsx_path", "prior_side"]:
        out.append(u"receive_pair の引数が (今年の xlsx の path, 去年の側) だけでない: %s" % [a.arg for a in f.args.args])
    f = funcs.get("receive_folder")
    if f is not None and [a.arg for a in f.args.args] != ["xlsx_dir", "out_dir", "prior_paths", "reader"]:
        out.append(u"receive_folder の引数が (xlsx の folder, 出力の folder, 組の番号 → 去年の path, 読み出し) だけでない: %s" % [a.arg for a in f.args.args])
    return out


def iso_problems(ms=None):
    ms = ms or MS
    out = []
    # 今年の書類・答えが無い場所(xlsx の folder だけ)で受ける側が動く。去年の path 以外は読み出しが呼ばれない
    with Temp() as d:
        xdir = os.path.join(d, u"xlsx")
        os.makedirs(xdir)
        rows, answers, cnt = ms.sheet_rows_of(cur_s1())
        ms.write_xlsx(os.path.join(xdir, u"07.xlsx"), DEC_C, rows)
        asked = []

        def reader(path):
            asked.append(path)
            if path != u"/nonexistent/prior_only.zip":
                raise AssertionError(u"去年以外の path を読んだ: %s" % path)
            return prior_s1()
        ms.receive_folder(xdir, os.path.join(d, u"out"), {7: u"/nonexistent/prior_only.zip"}, reader)
        if asked != [u"/nonexistent/prior_only.zip"]:
            out.append(u"受ける側が去年の path だけを読まない: %s" % asked)
        if sorted(os.listdir(d)) != [u"out", u"xlsx"]:
            out.append(u"受ける側が出力の folder の外に書く: %s" % sorted(os.listdir(d)))
        o = json.loads(open(os.path.join(d, u"out", u"07.json"), encoding="utf-8").read(), object_pairs_hook=od)
        if o[u"番号"] != 7 or sum(1 for r in o[u"受けた"][u"rows"] if r["stop"] == u"") != 21:
            out.append(u"今年の書類も答えも無い場所での受ける側の結果が違う")
        # 答えの folder が xlsx の folder の隣に在るときと無いときで同じ(読んでいれば違いが出る)
        os.makedirs(os.path.join(d, u"answer"))
        with open(os.path.join(d, u"answer", u"07.json"), "w", encoding="utf-8") as fh:
            fh.write(u"{ broken")
        ms.receive_folder(xdir, os.path.join(d, u"out2"), {7: u"/nonexistent/prior_only.zip"}, reader)
        o2 = json.loads(open(os.path.join(d, u"out2", u"07.json"), encoding="utf-8").read(), object_pairs_hook=od)
        if o2 != o:
            out.append(u"受ける側の結果が答えの folder の在る・無いで変わる(答えを読んでいる)")
        # xlsx が無い組は止まる
        if not stops(ms, ms.receive_folder, xdir, os.path.join(d, u"out3"), {8: u"/nonexistent/prior_only.zip"}, reader):
            out.append(u"xlsx が無い組で止まらない")
    # 受ける側の関数が開く file は xlsx と去年の書類だけ(open・ZipFile・load_workbook を差し替えて見る)
    import builtins
    import zipfile as _zf
    import openpyxl
    opened = []
    real_open, real_zip, real_wb = builtins.open, _zf.ZipFile, openpyxl.load_workbook
    with Temp() as d:
        xdir = os.path.join(d, u"xlsx")
        os.makedirs(xdir)
        rows, answers, cnt = ms.sheet_rows_of(cur_s1())
        ms.write_xlsx(os.path.join(xdir, u"07.xlsx"), DEC_C, rows)
        builtins.open = lambda p, *a, **k: (opened.append(("open", str(p))), real_open(p, *a, **k))[1]
        openpyxl.load_workbook = lambda p, *a, **k: (opened.append(("xlsx", str(p))), real_wb(p, *a, **k))[1]
        try:
            ms.receive_folder(xdir, os.path.join(d, u"out"), {7: u"PRIOR"}, lambda p: prior_s1())
        finally:
            builtins.open, openpyxl.load_workbook = real_open, real_wb
        bad = [(k, p) for k, p in opened if k == "open" and not p.startswith(os.path.join(d, u"out")) and not p.startswith(xdir) and "xlsx" not in p and not p.endswith(".xlsx")]
        zips = [p for k, p in opened if k == "open" and p.endswith(".zip")]
        if bad or zips or ("xlsx", os.path.join(xdir, u"07.xlsx")) not in opened:
            out.append(u"受ける側が xlsx と出力の file 以外を開く: %s" % bad[:3])
    return out


# ======================================================================== 10. 配線・import
STDLIB_OK = ("__future__", "argparse", "bisect", "collections", "datetime", "decimal", "fractions", "importlib", "io", "json", "math", "os", "re", "sys", "zipfile", "openpyxl")
NETWORK_MODULES = ("http", "socket", "ssl", "urllib", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx", "subprocess", "tempfile", "shutil", "glob")
CALLED = (("Y", "make_pairs"), ("M", "analyze"), ("M", "period_name"), ("M", "number_value"), ("M", "sum_nested"), ("G", "head_mark"), ("N", "doc_texts"), ("N", "check_clean"), ("W", "order_sha256"), ("Z", "read_rows"))
CHAIN_CALLED = ("peel_tables", "load_package")
NEVER_CALLED = ("derive_folder", "process_doc", "run_facts", "exec_make", "build_definitions", "write_type_folder")
NOT_COPIED = ("analyze", "period_name", "make_pairs", "sum_nested", "order_sha256", "select_docs", "peel_tables", "load_package", "read_rows", "head_mark", "doc_texts", "number_value", "table_rows", "build_tables", "file_rows")
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS")
SIBLING_NAMES = ("_xe0_input_type_2026_11_22", "_xe0_prior_year_fact_guard_2026_11_22")
HARNESS_WORDS = ("apply_edits(", "inject_with_profile(", "run_doc(", "mutate(", "IJ.select(", "inject(", "inject_doc(", "verify_document(", "verify_external(")


def import_problems(src=None):
    u"""script の import は標準ライブラリ・zipfile・openpyxl と importlib だけ。前の便の関数は ``Y.``・``M.``・``G.``・``N.``・``W.``・``Z.`` から呼び写さない。"""
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
    u"""``read_zip_side`` が zip → 字の読み出し → 読み込み → 表を剥がす → 型の分析の順に前の便の関数を呼び、戻り値を使う(module の実体に差して確かめる)。"""
    ms = ms or MS
    out = []
    M_, P_, B_, N_ = ms.M, ms.M.P, ms.M.B, ms.N
    saved = (B_.load_package, P_.peel_tables, M_.analyze, N_.doc_texts)
    log = []
    html = u'<table><tr><td>名</td><td><ix:nonFraction name="x:A" contextRef="c1">1</ix:nonFraction></td></tr></table>'
    fact = {"where": "F", "isnum": True, "fi": 0, "attrs": {"name": "x:A", "contextRef": "c1"}, "reasons": set(), "target": u"既定", "dims": [], "period": ("duration", list(CUR_DUR)),
            "value": u"1", "form": JPY, "shift": 6, "prec": -6, "nil": False, "content": u"1"}
    import zipfile as _zf
    with Temp() as d:
        p = os.path.join(d, u"a.zip")
        with _zf.ZipFile(p, "w") as z:
            z.writestr(u"XBRL/PublicDoc/a.htm", u"x")
        try:
            B_.load_package = lambda q: (log.append(("load", q)), u"ENTRIES")[1]
            P_.peel_tables = lambda e: (log.append(("peel", e)), ([(u"a.htm",)], u"N", u"T"))[1]
            M_.analyze = lambda f: (log.append(("analyze", f)), {"dec": dict(DEC_C), "facts": [fact]})[1]
            N_.doc_texts = lambda z: (log.append(("texts", type(z).__name__)), [(u"XBRL/PublicDoc/a.htm", html)])[1]
            got = ms.read_zip_side(p)
        finally:
            B_.load_package, P_.peel_tables, M_.analyze, N_.doc_texts = saved
        if log != [("texts", "ZipFile"), ("load", p), ("peel", u"ENTRIES"), ("analyze", [(u"a.htm",)])]:
            out.append(u"read_zip_side の呼び方が違う: %s" % log)
        if [r["name"] for r in got["records"]] != [u"x:A"] or got["dec"] != dict(DEC_C):
            out.append(u"read_zip_side の戻り値が分析の戻りを使っていない")

        def refuse(f):
            raise ms.Refuse(u"理由ウ")
        try:
            B_.load_package = lambda q: []
            P_.peel_tables = lambda e: ([], u"N", u"T")
            M_.analyze = refuse
            N_.doc_texts = lambda z: []
            stopped = stops(ms, ms.read_zip_side, p)
        finally:
            B_.load_package, P_.peel_tables, M_.analyze, N_.doc_texts = saved
        if not stopped:
            out.append(u"分析が断りを出したとき止まらない")
    if ms.Refuse is not ms.M.Refuse or ms.Stop is not ms.W.Stop:
        out.append(u"Refuse・Stop の型が前の便と同じ object でない")
    if ms.DOCS_DIR != ms.Y.DOCS_DIR or ms.PRIOR_DIR != ms.Y.PRIOR_DIR or ms.PAIRS_WANT != ms.Y.PAIRS_WANT or ms.Z is not ms.G.Z or ms.Y is not ms.Z.Y or ms.N is not ms.Z.N:
        out.append(u"置き場・組の数・前の便の script の参照が便 XY0・XZ0・XZ1 の字と違う")
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
    "files = {'xm0': ('_gate_order_xm0', 'measure/xbrl_input_type_2026-11-22.py'), 'xy0': ('_gate_order_xy0', 'measure/xbrl_prior_year_draft_2026-11-22.py'), "
    "'xz1': ('_gate_order_xz1', 'measure/xbrl_prior_year_fact_guard_2026-11-22.py'), 'xz0': ('_gate_order_xz0', 'measure/xbrl_prior_year_fact_draft_2026-11-22.py'), "
    "'xk0': ('_gate_order_xk0', 'measure/xbrl_type_carryover_2026-11-22.py'), 'xe0': ('_gate_order_xe0', 'measure/xbrl_company_excel_2026-11-22.py')}\n"
    "mods = {}\n"
    "for key in sys.argv[2:]:\n"
    "    name, rel = files[key]\n"
    "    spec = importlib.util.spec_from_file_location(name, os.path.join(root, rel))\n"
    "    m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m); mods[key] = m\n"
    "k = mods['xe0']\n"
    "assert k.Y.make_pairs and k.M.analyze and k.G.head_mark and k.Z.read_rows and k.W is k.M.W and k.Z is k.G.Z\n"
    "assert k.sheet_rows_of and k.receive_pair and k.score_pair\n"
    "print('ok')\n")


def order_import_problems():
    u"""前の便の script と自分を並べて読む順を入れ替えても、動く(sys.modules の名を上書きして赤にならない)。別の process で確かめる。"""
    out = []
    for order in (("xm0", "xy0", "xz0", "xz1", "xk0", "xe0"), ("xe0", "xk0", "xz1", "xz0", "xy0", "xm0"), ("xz1", "xk0", "xe0", "xm0"), ("xk0", "xz0", "xe0", "xz1", "xy0"), ("xe0",)):
        rc = subprocess.run([sys.executable, "-c", ORDER_SNIPPET, ROOT] + list(order), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, cwd=ROOT,
                            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        if rc.returncode != 0 or rc.stdout.strip() != "ok":
            out.append(u"読む順 %s で動かない: %s" % (u"→".join(order), rc.stderr.strip().splitlines()[-1:] or rc.stdout))
    return out


# ======================================================================== 変異(約束の側から。script の字を 1 か所替えた版を memory の中に作る)
def bound_mutants():
    u"""予測の境の表の 9 行を、下限・下限を含むか・上限・上限を含むかの 1 つずつ(あれば)替える。"""
    out = []
    for k, v in EXPECT_BOUNDS.items():
        old = u'("%s", %s)' % (k, repr(v))
        lo, lo_in, hi, hi_in = v
        variants = []
        if lo is not None:
            variants += [(u"下限を含むかを逆にする", (lo, not lo_in, hi, hi_in)), (u"下限を 1 上げる", (lo + 1, lo_in, hi, hi_in)), (u"下限を 1 下げる", (lo - 1, lo_in, hi, hi_in))]
        if hi is not None:
            variants += [(u"上限を含むかを逆にする", (lo, lo_in, hi, not hi_in)), (u"上限を 1 上げる", (lo, lo_in, hi + 1, hi_in)), (u"上限を 1 下げる", (lo, lo_in, hi - 1, hi_in))]
        for what, nv in variants:
            out.append((u"B %s の%s" % (k, what), old, u'("%s", %s)' % (k, repr(nv)), ("seal", "tot")))
    return out


def unit_mutants():
    u"""単位の字の表の 8 行を 1 行ずつ落とす・字を替える・位を替える。空の fact の 4 行を 1 行ずつ落とす。"""
    out = []
    for form, shift, letter in ((u"通貨:JPY", 0, u"円"), (u"通貨:JPY", 3, u"千円"), (u"通貨:JPY", 6, u"百万円"), (u"M.UNIT_SHARES", 0, u"株"), (u"M.UNIT_SHARES", 3, u"千株"), (u"M.UNIT_PURE", 0, u"数"), (u"M.UNIT_PURE", -2, u"％"), (u"JPY + u\"÷株\"", 0, u"円/株")):
        f = form if form.startswith(u"M.") or form.startswith(u"JPY") else u"JPY"
        old = u'(%s, %s, u"%s")' % (f, shift, letter)
        out.append((u"U 単位の字の表から「%s」の行を落とす" % letter, old, u'(u"X", 99, u"X")', ("pure", "seal")))
        out.append((u"U 単位の字の表の「%s」の位を 1 ずらす" % letter, old, u'(%s, %s, u"%s")' % (f, shift + 1, letter), ("pure", "seal")))
        out.append((u"U 単位の字の表の「%s」の字を替える" % letter, old, u'(%s, %s, u"%sx")' % (f, shift, letter), ("pure", "seal")))
    for f, letter in ((u"JPY", u"円"), (u"M.UNIT_SHARES", u"株"), (u"M.UNIT_PURE", u"数"), (u"JPY + u\"÷株\"", u"円/株")):
        old = u'(%s, u"%s")' % (f, letter)
        out.append((u"U 空の fact の単位の字の表から「%s」の行を落とす" % letter, old, u'(u"X", u"X")', ("pure", "seal")))
        out.append((u"U 空の fact の単位の字の「%s」を替える" % letter, old, u'(%s, u"%sx")' % (f, letter), ("pure", "seal")))
    return out


def mark_mutants():
    u"""負の印の 5 字を 1 つずつ落とす・足す。"""
    out = []
    base = u'MARKS = u"△▲-－−"'
    for ch in u"△▲-－−":
        out.append((u"MK 負の印の字「%s」を落とす" % ch, base, base.replace(ch, u"", 1), ("pure", "seal")))
    out.append((u"MK 負の印に「+」を足す", base, u'MARKS = u"△▲-－−+"', ("pure", "seal")))
    out.append((u"MK 負の印に「ー」を足す", base, u'MARKS = u"△▲-－−ー"', ("pure", "seal")))
    return out


def stop_mutants():
    u"""止めの理由の 7 つの字を 1 つずつ替える・順を入れ替える。"""
    out = []
    old = u'STOPS = (u"去年に無い行", u"候補が 2 つ以上", u"表の頭が違う", u"期が違う", u"番号つき", u"単位が違う", u"符号の向きが 2 通り")'
    words = [u"去年に無い行", u"候補が 2 つ以上", u"表の頭が違う", u"期が違う", u"番号つき", u"単位が違う", u"符号の向きが 2 通り"]
    for i, w in enumerate(words):
        ws = list(words)
        ws[i] = w + u"x"
        out.append((u"ST 止めの理由「%s」の字を替える" % w, old, u"STOPS = (" + u", ".join(u'u"%s"' % x for x in ws) + u")", ("seal", "recv")))
    for i in range(6):
        ws = list(words)
        ws[i], ws[i + 1] = ws[i + 1], ws[i]
        out.append((u"ST 止めの理由の並びの %d・%d 番目を入れ替える" % (i + 1, i + 2), old, u"STOPS = (" + u", ".join(u'u"%s"' % x for x in ws) + u")", ("seal", "recv")))
    return out


EDIT_OF_RECEIVE_ROW = u'''    guard = None
    if row["hmark"] not in e["marks"]:
        guard = S_HEAD
    elif pn is None or pn not in e["pns"]:
        guard = S_PERIOD
    elif numbered_cand(cand):
        guard = S_NUMBERED
    elif form not in e["forms"]:
        guard = S_UNIT
'''


def guard_order_mutants():
    u"""守りの順を入れ替える・守り 4 つを 1 つずつ外す・1 つずつ緩める。"""
    out = []
    g = [(u"表の頭", u'    if row["hmark"] not in e["marks"]:\n        guard = S_HEAD\n'), (u"期", u'    elif pn is None or pn not in e["pns"]:\n        guard = S_PERIOD\n'),
         (u"番号つき", u'    elif numbered_cand(cand):\n        guard = S_NUMBERED\n'), (u"単位", u'    elif form not in e["forms"]:\n        guard = S_UNIT\n')]
    head = u'    guard = None\n'
    body = [x for _n, x in g]

    def mk_src(parts):
        s = u"".join(parts)
        return head + s.replace(u"    elif ", u"    if ", 1) if False else head + (u"    if " + s[len(u"    if "):] if s.startswith(u"    if ") else u"    if " + s[len(u"    elif "):])
    old = head + u"".join(body)
    for i, (name, _x) in enumerate(g):
        rest = body[:i] + body[i + 1:]
        out.append((u"G 守り「%s」を外す" % name, old, mk_src(rest), ("recv",)))
    for i in range(3):
        parts = list(body)
        parts[i], parts[i + 1] = parts[i + 1], parts[i]
        out.append((u"G 守りの %d・%d 番目の順を入れ替える" % (i + 1, i + 2), old, mk_src(parts), ("recv",)))
    return out


def entry_mutants():
    u"""入口の配線(``main`` の分岐・``score_run``・``material_of``・``check``・``dev_run``)の引数の入れ替え・落とし。作り物の 63 組を本物の関数に通す検査(``entry``)で赤になる。"""
    mk_ = (u'    elif a.make:\n        _docs, pairs, _ex = Y.make_pairs(a.docs or DOCS_DIR, a.prior or PRIOR_DIR)\n        make_folders(a.make, pairs)\n',
           u'    elif a.make:\n        _docs, pairs, _ex = Y.make_pairs(a.prior or PRIOR_DIR, a.docs or DOCS_DIR)\n        make_folders(a.make, pairs)\n')
    rc = u'    elif a.receive:\n        _docs, pairs, _ex = Y.make_pairs(a.docs or DOCS_DIR, a.prior or PRIOR_DIR)\n        receive_folder(a.receive[0], a.receive[1], prior_paths_of(pairs))\n'
    t = [(u"E1 check が verify_record を呼ばない", u'    rec = json.loads(text, object_pairs_hook=od)\n    verify_record(rec, text, want)\n', u'    rec = json.loads(text, object_pairs_hook=od)\n'),
         (u"E2 --receive の引数 2 つを入れ替える", u'receive_folder(a.receive[0], a.receive[1], prior_paths_of(pairs))', u'receive_folder(a.receive[1], a.receive[0], prior_paths_of(pairs))'),
         (u"E3 score_run が score_folders に渡す folder を入れ替える", u'score_folders(out_dir, ans_dir, [p[0] for p in pairs])', u'score_folders(ans_dir, out_dir, [p[0] for p in pairs])'),
         (u"E4 material_of の組の数を書類の数にする", u'(u"組の数", len(pairs)),', u'(u"組の数", len(docs)),'),
         (u"E5 score_run が docs・prior を make_pairs に渡さない", u'docs_, pairs, _ex = Y.make_pairs(docs or DOCS_DIR, prior or PRIOR_DIR)', u'docs_, pairs, _ex = Y.make_pairs(DOCS_DIR, PRIOR_DIR)'),
         (u"E6 check が rec_path を無視する", u'    p = rec_path or os.path.join(root, RECORD_REL)\n', u'    p = os.path.join(root, RECORD_REL)\n'),
         (u"E7 check が want を verify_record に渡さない", u'    verify_record(rec, text, want)\n', u'    verify_record(rec, text)\n'),
         (u"E8 check が root でなく既定の root の下を読む", u'def check(root=ROOT, rec_path=None, say=print, want=PAIRS_WANT):', u'def check(root=ROOT, rec_path=None, say=print, want=PAIRS_WANT):\n    root = ROOT'),
         (u"E9 --make で今年の側・前の年の側の置き場を入れ替える", mk_[0], mk_[1]),
         (u"E10 --receive で今年の側・前の年の側の置き場を入れ替える", rc, rc.replace(u"Y.make_pairs(a.docs or DOCS_DIR, a.prior or PRIOR_DIR)", u"Y.make_pairs(a.prior or PRIOR_DIR, a.docs or DOCS_DIR)")),
         (u"E11 --receive が今年の path を受ける側に渡す", rc, rc.replace(u"prior_paths_of(pairs))", u"dict((p[0], p[2]) for p in pairs))")),
         (u"E12 --score が --root を渡さない", u'score_run(a.score[0], a.score[1], root=a.root, docs=a.docs, prior=a.prior)', u'score_run(a.score[0], a.score[1], docs=a.docs, prior=a.prior)'),
         (u"E13 --score が docs を渡さない", u'score_run(a.score[0], a.score[1], root=a.root, docs=a.docs, prior=a.prior)', u'score_run(a.score[0], a.score[1], root=a.root, prior=a.prior)'),
         (u"E14 --score が prior を渡さない", u'score_run(a.score[0], a.score[1], root=a.root, docs=a.docs, prior=a.prior)', u'score_run(a.score[0], a.score[1], root=a.root, docs=a.docs)'),
         (u"E15 --score の docs・prior を入れ替える", u'score_run(a.score[0], a.score[1], root=a.root, docs=a.docs, prior=a.prior)', u'score_run(a.score[0], a.score[1], root=a.root, docs=a.prior, prior=a.docs)'),
         (u"E16 --score の出力の folder と答えの folder を入れ替える", u'score_run(a.score[0], a.score[1], root=a.root, docs=a.docs, prior=a.prior)', u'score_run(a.score[1], a.score[0], root=a.root, docs=a.docs, prior=a.prior)'),
         (u"E17 --check が --root を渡さない", u'        check(root=a.root)\n', u'        check()\n'),
         (u"E18 --dev が docs・prior を入れ替える", u'        dev_run(a.tmp, a.docs, a.prior)\n', u'        dev_run(a.tmp, a.prior, a.docs)\n'),
         (u"E19 --dev が prior を渡さない", u'        dev_run(a.tmp, a.docs, a.prior)\n', u'        dev_run(a.tmp, a.docs)\n'),
         (u"E20 --make の組を 1 組落とす", u'        make_folders(a.make, pairs)\n', u'        make_folders(a.make, pairs[:-1])\n'),
         (u"E21 score_run が記録の材料に書類と組を入れ替えて渡す", u'rec, secret = build_record(entries, material_of(docs_, pairs), secret_of(docs_, pairs, names))', u'rec, secret = build_record(entries, material_of(pairs, docs_), secret_of(docs_, pairs, names))'),
         (u"E22 score_run が記録に書かないものの集まりで書類と組を入れ替える", u'secret_of(docs_, pairs, names))', u'secret_of(pairs, docs_, names))'),
         (u"E23 score_run が書く前の検査に記録に書かないものの集まりを渡さない", u'    write_record(out, rec, secret)\n    show_flag(rec, say)', u'    write_record(out, rec)\n    show_flag(rec, say)'),
         (u"E24 score_run が書く先を root の下でなく既定の root の下にする", u'out = out or os.path.join(root, RECORD_REL)', u'out = out or os.path.join(ROOT, RECORD_REL)'),
         (u"E25 score_run が記録を書いた後の表示で組の数を数えない", u'say(u"-> %s(組 %d)" % (os.path.basename(out), rec[u"材料"][u"組の数"]))', u'say(u"-> %s" % os.path.basename(out))'),
         (u"E26 dev_run が受ける側へ今年の側の path を渡す", u'receive_folder(os.path.join(tmp, u"xlsx"), os.path.join(tmp, u"out"), prior_paths_of(sub), reader)', u'receive_folder(os.path.join(tmp, u"xlsx"), os.path.join(tmp, u"out"), dict((p[0], p[2]) for p in sub), reader)'),
         (u"E27 dev_run が採点で folder を入れ替える", u'score_folders(os.path.join(tmp, u"out"), os.path.join(tmp, u"answer"), [p[0] for p in sub])', u'score_folders(os.path.join(tmp, u"answer"), os.path.join(tmp, u"out"), [p[0] for p in sub])'),
         (u"E28 dev_run が docs・prior を入れ替える", u'Y.make_pairs(docs_dir or DOCS_DIR, prior_dir or PRIOR_DIR)', u'Y.make_pairs(prior_dir or PRIOR_DIR, docs_dir or DOCS_DIR)'),
         (u"E29 check が通ったと言うとき組の数を書類の数でなく 0 にする", u'(組 %d)" % len(rec[u"書類"]))', u'(組 %d)" % 0)'),
         (u"E30 score_run が show_flag に say を渡さない", u'    show_flag(rec, say)\n    say(', u'    show_flag(rec)\n    say('),
         (u"E31 score_run が out= を無視する", u'    out = out or os.path.join(root, RECORD_REL)\n', u'    out = os.path.join(root, RECORD_REL)\n'),
         (u"E32 score_run が最後の表示を say でなく標準出力へ出す", u'    say(u"-> %s(組', u'    print(u"-> %s(組'),
         (u"E33 --receive が受ける側へ番号 1・2・3 の組だけの path を渡す", rc, rc.replace(u"prior_paths_of(pairs))", u"prior_paths_of(pairs, DEV_NOS))")),
         (u"E34 score_run が組の数を 62 にして材料を作る", u'material_of(docs_, pairs)', u'material_of(docs_, pairs[:62])'),
         (u"E35 score_run が記録を返さない", u'    say(u"-> %s(組 %d)" % (os.path.basename(out), rec[u"材料"][u"組の数"]))\n    return rec\n', u'    say(u"-> %s(組 %d)" % (os.path.basename(out), rec[u"材料"][u"組の数"]))\n    return None\n'),
         (u"E36 dev_run が表示を say でなく標準出力へ出す", u'    say(json.dumps(dev_summary(entries)', u'    print(json.dumps(dev_summary(entries)'),
         (u"E37 score_run が書く前の検査に None を渡す", u'    write_record(out, rec, secret)\n', u'    write_record(out, rec, None)\n'),
         (u"E38 score_run が採点する番号を書類の本数から作る", u'score_folders(out_dir, ans_dir, [p[0] for p in pairs])', u'score_folders(out_dir, ans_dir, list(range(1, len(docs_) + 1)))'),
         (u"E39 --make が 1 組落として書く", u'        make_folders(a.make, pairs)\n', u'        make_folders(a.make, [p for p in pairs if p[0] <= 62])\n'),
         (u"E40 score_run の今年の側の置き場の既定を前の年の側の置き場の引数から取る", u'Y.make_pairs(docs or DOCS_DIR, prior or PRIOR_DIR)', u'Y.make_pairs(docs or prior or DOCS_DIR, prior or PRIOR_DIR)'),
         (u"E41 score_run の前の年の側の置き場の既定を落とす", u'Y.make_pairs(docs or DOCS_DIR, prior or PRIOR_DIR)', u'Y.make_pairs(docs or DOCS_DIR, prior)'),
         (u"E42 dev_run の前の年の側の置き場の既定を落とす", u'Y.make_pairs(docs_dir or DOCS_DIR, prior_dir or PRIOR_DIR)', u'Y.make_pairs(docs_dir or DOCS_DIR, prior_dir)'),
         (u"E43 --make の今年の側の置き場の既定を前の年の側にする", mk_[0], mk_[0].replace(u"a.docs or DOCS_DIR", u"a.docs or PRIOR_DIR")),
         (u"E44 --receive の前の年の側の置き場の既定を今年の側にする", rc, rc.replace(u"a.prior or PRIOR_DIR", u"a.prior or DOCS_DIR")),
         (u"E45 show_flag が旗の立った・立たないの表示の向きを入れ替える", u'(u"立った" if rec[u"§3 の旗"][u"§0 と違う"] else u"立たない")', u'(u"立たない" if rec[u"§3 の旗"][u"§0 と違う"] else u"立った")'),
         ]
    return [(n, o, w, ("entry",)) for n, o, w in t]


MUTANTS = tuple(bound_mutants()) + tuple(unit_mutants()) + tuple(mark_mutants()) + tuple(stop_mutants()) + tuple(guard_order_mutants()) + tuple(entry_mutants()) + (
    # ---- 封の字・定数(§1・§3)
    (u"C1 封の commit を替える", u'SEAL_COMMIT = "aec0496d"', u'SEAL_COMMIT = "aec0496e"', ("seal", "rec")),
    (u"C2 組の数を 62 にする", u'PAIRS_WANT = Y.PAIRS_WANT', u'PAIRS_WANT = 62', ("seal", "wiring")),
    (u"C3 訓練の境を 4 にする", u'SEEN_MAX_NO = 3 ', u'SEEN_MAX_NO = 4 ', ("seal", "tot")),
    (u"C4 訓練の組の数を 4 にする", u'TRAIN_WANT, JUDGE_WANT = 3, 60', u'TRAIN_WANT, JUDGE_WANT = 4, 60', ("seal",)),
    (u"C5 判定の組の数を 59 にする", u'TRAIN_WANT, JUDGE_WANT = 3, 60', u'TRAIN_WANT, JUDGE_WANT = 3, 59', ("seal",)),
    (u"C6 dev の番号を 1・2・4 にする", u'DEV_NOS = (1, 2, 3)', u'DEV_NOS = (1, 2, 4)', ("seal", "dev")),
    (u"C7 書類のシートの名を替える", u'SHEET_DOC, SHEET_NUM = u"書類", u"数"', u'SHEET_DOC, SHEET_NUM = u"書類", u"数値"', ("seal", "xlsx")),
    (u"C8 空の fact の字を「-」にする", u'NIL_CELL = u"－"', u'NIL_CELL = u"-"', ("seal", "pure")),
    (u"C9 有効数字の桁の数を 16 にする", u'MAX_DIGITS = 15', u'MAX_DIGITS = 16', ("seal", "pure")),
    (u"C10 有効数字の桁の数を 14 にする", u'MAX_DIGITS = 15', u'MAX_DIGITS = 14', ("seal", "pure")),
    (u"C11 守りの並びから単位を外す", u'GUARDS = (S_HEAD, S_PERIOD, S_NUMBERED, S_UNIT)', u'GUARDS = (S_HEAD, S_PERIOD, S_NUMBERED)', ("seal", "score")),
    (u"C12 比べる欄から精度を外す", u'u"表示の位", u"精度", u"空か")\nFIELD_KEY', u'u"表示の位", u"空か")\nFIELD_KEY', ("seal", "pure")),
    (u"C13 欄の対応の精度を表示の位に替える", u'"value", "form", "shift", "prec", "nil")))\nEXCLUDES', u'"value", "form", "shift", "shift", "nil")))\nEXCLUDES', ("pure",)),
    (u"C14 比べる欄の名を替える(名)", u'FIELDS = (u"名", ', u'FIELDS = (u"要素名", ', ("seal", "pure")),
    (u"C15 書かない理由の並びを替える(行の字が空と型の外)", u'EXCLUDES = (u"行の字が空", u"型の外",', u'EXCLUDES = (u"型の外", u"行の字が空",', ("seal", "pure")),
    (u"C16 §0 の数(決めて全部同じ)を替える", u'(u"決めて全部同じ", 2636)', u'(u"決めて全部同じ", 2635)', ("seal", "tot")),
    (u"C17 §0 の数(止めた)を替える", u'(u"止めた", 669)', u'(u"止めた", 668)', ("seal", "tot")),
    (u"C18 §0 の数(行の中の数の fact)を替える", u'(u"行の中の数の fact", 3434)', u'(u"行の中の数の fact", 3433)', ("seal", "tot")),
    (u"C19 §0 の数(決めたが違う)を替える", u'(u"決めたが違う", 0), (u"止めた", 669)', u'(u"決めたが違う", 1), (u"止めた", 669)', ("seal", "tot")),
    (u"C20 95% を 94% にする", u'DOC_SAME_PCT = 95.0', u'DOC_SAME_PCT = 94.0', ("seal", "tot")),
    (u"C21 XE0-2 の下限 1 fact を 0 にする", u'MIN_DIFF = 1 ', u'MIN_DIFF = 0 ', ("seal", "tot")),
    (u"C22 XE0-6 の下限 1 fact を 0 にする", u'MIN_G12 = 1 ', u'MIN_G12 = 0 ', ("seal", "tot")),
    (u"C23 限界の 1 行を落とす", u'    u"答えは提出された書類そのもので、提出された書類の誤りは見ていない。"]', u']', ("seal",)),
    (u"C24 数のシートの欄の名を替える", u'u"表の番号", u"行の字", u"列の番号"', u'u"表の通し番号", u"行の字", u"列の番号"', ("seal",)),
    (u"C25 組の分けで訓練を番号 3 未満にする", u'e[u"番号"] <= SEEN_MAX_NO])', u'e[u"番号"] < SEEN_MAX_NO])', ("tot", "rec")),
    # ---- 負の印・字(§1)
    (u"N1 負の印を末尾でなく先頭の字で見る", u'return bool(seg) and seg[-1] in MARKS', u'return bool(seg) and seg[0] in MARKS', ("pure",)),
    (u"N2 負の印を字のどこかに在れば印とする", u'return bool(seg) and seg[-1] in MARKS', u'return bool(seg) and any(c in MARKS for c in seg)', ("pure",)),
    (u"N3 &#160; を除かない", u'seg = TAG_RE.sub(u"", seg).replace(u"&#160;", u"")', u'seg = TAG_RE.sub(u"", seg)', ("pure",)),
    (u"N4 空白を除かない", u'seg = SPACE_RE.sub(u"", seg)', u'seg = seg', ("pure",)),
    (u"N5 タグを除かない", u'seg = TAG_RE.sub(u"", seg).replace(u"&#160;", u"")', u'seg = seg.replace(u"&#160;", u"")', ("pure",)),
    (u"N6 空白の字から U+3000 を外す", u'SPACE_RE = re.compile(r"[\\s\u00a0\u3000]")', u'SPACE_RE = re.compile(r"[ \\t\\n\u00a0]")', ("pure",)),
    (u"N7 空白の字から U+00A0 を外す", u'SPACE_RE = re.compile(r"[\\s\u00a0\u3000]")', u'SPACE_RE = re.compile(r"[ \\t\\n\u3000]")', ("pure",)),
    (u"N8 最後の開きタグでなく最初の開きタグから見る", u'seg = rowtext[cells[-1].start():fact_start] if cells else rowtext[:fact_start]', u'seg = rowtext[cells[0].start():fact_start] if cells else rowtext[:fact_start]', ("pure",)),
    (u"N9 開きタグが無いとき空にする", u'seg = rowtext[cells[-1].start():fact_start] if cells else rowtext[:fact_start]', u'seg = rowtext[cells[-1].start():fact_start] if cells else u""', ("pure",)),
    (u"N10 欄の区切りを <td だけにする(<th を見ない)", u'cells = list(Z.CELL_RE.finditer(rowtext[:fact_start]))', u'cells = [m for m in Z.CELL_RE.finditer(rowtext[:fact_start]) if m.group(0).lower() == "<td"]', ("pure",)),
    (u"N11 負の印を 1 字前で見る", u'return bool(seg) and seg[-1] in MARKS', u'return len(seg) > 1 and seg[-2] in MARKS', ("pure",)),
    (u"N12 負の印の空を印とする", u'return bool(seg) and seg[-1] in MARKS', u'return not seg or seg[-1] in MARKS', ("pure",)),
    (u"N13 有効数字から先頭の 0 を除かない", u'return len((content or u"").replace(u",", u"").replace(u".", u"").lstrip(u"0"))', u'return len((content or u"").replace(u",", u"").replace(u".", u""))', ("pure",)),
    (u"N14 有効数字に . を数える", u'return len((content or u"").replace(u",", u"").replace(u".", u"").lstrip(u"0"))', u'return len((content or u"").replace(u",", u"").lstrip(u"0"))', ("pure",)),
    (u"N15 有効数字に , を数える", u'return len((content or u"").replace(u",", u"").replace(u".", u"").lstrip(u"0"))', u'return len((content or u"").replace(u".", u"").lstrip(u"0"))', ("pure",)),
    (u"N16 小数の桁を整数部の桁にする", u'return len(content.split(u".")[1]) if u"." in content else 0', u'return len(content.split(u".")[0]) if u"." in content else 0', ("pure",)),
    (u"N17 小数の桁の数を常に 0 にする", u'return len(content.split(u".")[1]) if u"." in content else 0', u'return 0', ("pure", "xlsx")),
    (u"N18 見出しの字の空を鍵で空のままにする", u'    return h or None', u'    return h', ("pure", "recv")),
    (u"N19 鍵から見出しの字を外す", u'return (hkey(r["h"]), r["th"], r["T"], r["td"])', u'return (r["th"], r["T"], r["td"])', ("pure",)),
    (u"N20 鍵から表の番号を外す", u'return (hkey(r["h"]), r["th"], r["T"], r["td"])', u'return (hkey(r["h"]), r["T"], r["td"])', ("pure",)),
    (u"N21 鍵から行の字を外す", u'return (hkey(r["h"]), r["th"], r["T"], r["td"])', u'return (hkey(r["h"]), r["th"], r["td"])', ("pure",)),
    (u"N22 鍵から列の番号を外す", u'return (hkey(r["h"]), r["th"], r["T"], r["td"])', u'return (hkey(r["h"]), r["th"], r["T"])', ("pure",)),
    (u"N23 鍵に表の頭の印を足す", u'return (hkey(r["h"]), r["th"], r["T"], r["td"])', u'return (hkey(r["h"]), r["th"], r["T"], r["td"], r["hmark"])', ("pure", "recv")),
    (u"N24 局所名を最後の : の後ろにする", u'return name.split(":", 1)[1] if ":" in name else name', u'return name.rsplit(":", 1)[-1] if ":" in name else name', ("pure",)),
    (u"N25 局所名を接頭辞つきのままにする", u'return name.split(":", 1)[1] if ":" in name else name', u'return name', ("pure", "recv")),
    # ---- xlsx に書かない理由の順・数のセル・日付(§2-1・§3)
    (u"X1 行の字が空を見ない", u'    if not r["T"]:\n        return EXCLUDES[0]\n', u'', ("pure", "score")),
    (u"X2 型の外を見ない", u'    if r["bad"]:\n        return EXCLUDES[1]\n', u'', ("pure", "score")),
    (u"X3 単位が書けないを見ない", u'    if letter is None:\n        return EXCLUDES[2]\n', u'', ("pure", "score")),
    (u"X4 15 桁を見ない", u'    if not r["nil"] and sig_digits(r["content"]) > MAX_DIGITS:\n        return EXCLUDES[3]\n', u'', ("pure", "score")),
    (u"X5 15 桁を 15 桁以上にする", u'sig_digits(r["content"]) > MAX_DIGITS', u'sig_digits(r["content"]) >= MAX_DIGITS', ("pure",)),
    (u"X7 型の外と行の字が空の順を入れ替える", u'    if not r["T"]:\n        return EXCLUDES[0]\n    if r["bad"]:\n        return EXCLUDES[1]\n', u'    if r["bad"]:\n        return EXCLUDES[1]\n    if not r["T"]:\n        return EXCLUDES[0]\n', ("pure",)),
    (u"X8 単位と型の外の順を入れ替える", u'    if r["bad"]:\n        return EXCLUDES[1]\n    letter = FORM_LETTER.get(r["form"]) if r["nil"] else UNIT_OF.get((r["form"], r["shift"]))\n',
     u'    letter = FORM_LETTER.get(r["form"]) if r["nil"] else UNIT_OF.get((r["form"], r["shift"]))\n    if letter is None:\n        return EXCLUDES[2]\n    if r["bad"]:\n        return EXCLUDES[1]\n', ("pure",)),
    (u"X9 空の fact の単位を表示の位つきの表で引く", u'letter = FORM_LETTER.get(r["form"]) if r["nil"] else UNIT_OF.get((r["form"], r["shift"]))', u'letter = UNIT_OF.get((r["form"], r["shift"]))', ("pure",)),
    (u"X10 空でない fact の単位を単位の形だけで引く", u'letter = FORM_LETTER.get(r["form"]) if r["nil"] else UNIT_OF.get((r["form"], r["shift"]))', u'letter = FORM_LETTER.get(r["form"])', ("pure",)),
    (u"X11 負のとき負にしない", u'    if r["neg"]:\n        d = -d\n', u'', ("pure", "xlsx")),
    (u"X12 負でないのに負にする", u'    if r["neg"]:\n        d = -d\n', u'    d = -d\n', ("pure", "xlsx")),
    (u"X13 小数の桁が 0 でも float にする", u'v = int(d) if dig == 0 else float(d)', u'v = float(d)', ("pure",)),
    (u"X14 小数の桁が在っても int にする", u'v = int(d) if dig == 0 else float(d)', u'v = int(d)', ("pure", "xlsx")),
    (u"X15 表示形式を常に 0 にする", u'return v, (u"0" if dig == 0 else u"0." + u"0" * dig)', u'return v, u"0"', ("pure", "xlsx")),
    (u"X16 表示形式の小数の桁を 1 つ多くする", u'u"0." + u"0" * dig)', u'u"0." + u"0" * (dig + 1))', ("pure", "xlsx")),
    (u"X17 空の fact のセルを「－」でなく空にする", u'        return NIL_CELL, "General"', u'        return None, "General"', ("pure", "xlsx")),
    (u"X18 表示の字から , を除かない", u'd = decimal.Decimal(r["content"].replace(u",", u""))', u'd = decimal.Decimal(r["content"])', ("pure", "xlsx")),
    (u"X19 時点のとき始まりに日を入れる", u'start, end = (dates[0], dates[1]) if r["pkind"] == "duration" else (None, dates[0])', u'start, end = (dates[0], dates[-1])', ("xlsx", "recv")),
    (u"X20 期間のとき始まりを入れない", u'start, end = (dates[0], dates[1]) if r["pkind"] == "duration" else (None, dates[0])', u'start, end = (None, dates[-1])', ("xlsx", "recv")),
    (u"X21 時点の日を始まりの欄に入れる", u'start, end = (dates[0], dates[1]) if r["pkind"] == "duration" else (None, dates[0])', u'start, end = (dates[0], None) if r["pkind"] != "duration" else (dates[0], dates[1])', ("xlsx", "recv")),
    (u"X22 xlsx の日を字のセルで書く", u'wn.append([r["h"], r["th"], r["T"], r["td"], r["hmark"] or None, r["amount"], day_of(r["start"]) if r["start"] else None, day_of(r["end"]), r["unit"]])',
     u'wn.append([r["h"], r["th"], r["T"], r["td"], r["hmark"] or None, r["amount"], r["start"] if r["start"] else None, r["end"], r["unit"]])', ("xlsx",)),
    (u"X23 書類のシートの日を字で書く", u'ws.append([day_of(dec["start"]), day_of(dec["end"]), day_of(dec["filing"])])', u'ws.append([dec["start"], dec["end"], dec["filing"]])', ("xlsx",)),
    (u"X24 書類のシートの終わりの日と提出の日を入れ替える", u'ws.append([day_of(dec["start"]), day_of(dec["end"]), day_of(dec["filing"])])', u'ws.append([day_of(dec["start"]), day_of(dec["filing"]), day_of(dec["end"])])', ("xlsx", "recv")),
    (u"X25 数のセルの表示形式を書かない", u'        wn["F%d" % i].number_format = r["fmt"]\n', u'', ("xlsx",)),
    (u"X26 字のセルを字に固定しない", u'            if isinstance(c.value, str):\n                c.data_type = "s"\n', u'            pass\n', ("xlsx",)),
    (u"X28 書類のシートを数のシートの後に作る", u'ws.title = SHEET_DOC', u'ws.title = SHEET_NUM', ("xlsx",)),
    (u"X29 xlsx を排他で書かない", u'    with open(path, "xb") as fh:\n        wb.save(fh)', u'    with open(path, "wb") as fh:\n        wb.save(fh)', ("xlsx",)),
    (u"X30 単位の字を 1 行ずらして書く", u'r["amount"], day_of(r["start"]) if r["start"] else None, day_of(r["end"]), r["unit"]])', u'r["amount"], day_of(r["start"]) if r["start"] else None, day_of(r["end"]), r["unit"][:1]])', ("xlsx",)),
    (u"X31 見出しの行を書かない", u'    wn.append(list(HEAD_NUM))\n', u'', ("xlsx",)),
    (u"X32 答えの負の印を書かない", u'(u"mark", r["neg"])' if False else u'("nil", r["nil"]), ("mark", r["neg"])]))', u'("nil", r["nil"]), ("mark", False)]))', ("xlsx", "score")),
    (u"X33 答えの期の日を始まりだけにする", u'("pkind", r["pkind"]), ("period", list(dates)),', u'("pkind", r["pkind"]), ("period", list(dates[:1])),', ("xlsx", "recv", "score")),
    (u"X34 答えの種類を替える", u'("kind", M.KIND_NUM)', u'("kind", M.KIND_TEXT)', ("xlsx",)),
    (u"X35 書かない fact の数を数えない(型の外)", u'            cnt[why] += 1\n            continue\n', u'            continue\n', ("score",)),
    (u"X36 D の検査を外す", u'    if cnt["D"] != cnt["inrow"] - cnt["inrow_out"] - sum(cnt[e] for e in EXCLUDES):\n        raise Stop(u"**D が行の中の数の fact から引いた数と合わない。止める**")\n', u'', ("score",)),
    (u"X37 D から突き合わせの外を引かない", u'cnt["D"] != cnt["inrow"] - cnt["inrow_out"] - sum(', u'cnt["D"] != cnt["inrow"] - sum(', ("score",)),
    # ---- 読む(受ける側・数のセル・表示形式)
    (u"R1 負を負と読まない", u'    neg = math.copysign(1.0, float(cell)) < 0\n', u'    neg = False\n', ("pure", "xlsx", "recv")),
    (u"R2 負を符号なしの比べで読む(0 未満)", u'neg = math.copysign(1.0, float(cell)) < 0', u'neg = float(cell) < 0 and cell != 0', ("pure",)),
    (u"R3 常に負と読む", u'neg = math.copysign(1.0, float(cell)) < 0', u'neg = True', ("pure", "xlsx")),
    (u"R4 表示形式の桁を読まず 0 にする", u'    dig = len(m.group(1)) if m.group(1) else 0\n', u'    dig = 0\n', ("pure", "xlsx", "recv")),
    (u"R5 表示形式の桁を 1 つ少なく読む", u'dig = len(m.group(1)) if m.group(1) else 0', u'dig = max(0, len(m.group(1)) - 1) if m.group(1) else 0', ("pure", "xlsx")),
    (u"R6 決めた形でない表示形式で止まらない", u'    if m is None:\n        raise Stop(u"**数のセルの表示形式が決めた形でない。止める**")\n', u'    if m is None:\n        return False, False, str(cell), 0\n', ("pure",)),
    (u"R7 「－」でない字の金額で止まらない", u'    if isinstance(cell, bool) or not isinstance(cell, (int, float)):\n        raise Stop(u"**金額のセルが数でも「－」でもない。止める**")\n', u'', ("pure",)),
    (u"R8 bool を数と読む", u'    if isinstance(cell, bool) or not isinstance(cell, (int, float)):', u'    if not isinstance(cell, (int, float)):', ("pure",)),
    (u"R9 「－」を数と見る(空にしない)", u'    if cell == NIL_CELL:\n        return True, False, None, None\n', u'', ("pure", "recv")),
    (u"R11 float を丸めない(桁に合わせない)", u'    q = a.quantize(decimal.Decimal(1).scaleb(-dig))\n', u'    q = a\n', ("pure", "xlsx")),
    (u"R12 絶対値を取らない", u'a = decimal.Decimal(repr(abs(cell))) if isinstance(cell, float) else decimal.Decimal(abs(cell))', u'a = decimal.Decimal(repr(cell)) if isinstance(cell, float) else decimal.Decimal(cell)', ("pure",)),
    (u"R13 日付のセルでない日で止まらない", u'    if not isinstance(v, datetime.datetime):\n        raise Stop(u"**日のセルが日付のセルでない。止める**")\n', u'    if not isinstance(v, datetime.datetime):\n        return v\n', ("xlsx",)),
    (u"R14 書類のシートの日が日付でなくても止まらない", u'        if not isinstance(v, datetime.datetime):\n            raise Stop(u"**書類のシートの日が日付のセルでない。止める**")\n        dec[k] = v.date().isoformat()', u'        dec[k] = v.date().isoformat() if isinstance(v, datetime.datetime) else str(v)', ("xlsx",)),
    (u"R15 見出しの行を読み飛ばさない", u'wb[SHEET_NUM].iter_rows(min_row=2)', u'wb[SHEET_NUM].iter_rows(min_row=1)', ("xlsx",)),
    (u"R16 書類のシートの 2 行目でなく 1 行目を読む", u'd = [c.value for c in wb[SHEET_DOC][2]]', u'd = [c.value for c in wb[SHEET_DOC][1]]', ("xlsx",)),
    (u"R17 書類のシートの終わりの日と始まりの日を入れ替える", u'for k, v in zip(("start", "end", "filing"), d):', u'for k, v in zip(("end", "start", "filing"), d):', ("xlsx", "recv")),
    (u"R18 表の頭の印の空を None のまま", u'("hmark", hm or u"")', u'("hmark", hm)', ("xlsx",)),
    (u"R19 空の行を読み飛ばさない", u'        if all(x is None for x in v):\n            continue\n', u'', ("xlsx",)),
    (u"R20 数のセルの表示形式を最初の行のものにする", u'("fmt", cells[5].number_format)', u'("fmt", u"0")', ("xlsx", "recv")),
    (u"R21 期の始まりと終わりを入れ替えて読む", u'("start", date_text(start)), ("end", date_text(end))', u'("start", date_text(end)), ("end", date_text(start))', ("xlsx", "recv")),
    (u"R22 単位の字の列を読み違える", u'h, th, T, td, hm, amount, start, end, unit = v', u'h, th, T, td, hm, amount, start, end, unit = v[0], v[1], v[2], v[3], v[4], v[5], v[6], v[7], v[8][:1]', ("xlsx", "recv")),
    # ---- 去年の表(§2-2)
    (u"P1 去年の表に型の外を入れる", u'        if not r["T"] or r["bad"]:\n            continue\n        e = tab.setdefault', u'        if not r["T"]:\n            continue\n        e = tab.setdefault', ("recv",)),
    (u"P2 去年の表に行の字が空を入れる", u'        if not r["T"] or r["bad"]:\n            continue\n        e = tab.setdefault', u'        if r["bad"]:\n            continue\n        e = tab.setdefault', ("recv",)),
    (u"P3 去年の符号の向きに空を入れる", u'        if not r["nil"]:\n            e["flips"].add(r["neg"] != (r["sign"] == "-"))\n            e["shifts"].add(r["shift"])\n', u'        e["flips"].add(r["neg"] != (r["sign"] == "-"))\n        e["shifts"].add(r["shift"])\n', ("recv",)),
    (u"P4 去年の符号の向きの定義を逆にする", u'e["flips"].add(r["neg"] != (r["sign"] == "-"))', u'e["flips"].add(r["neg"] == (r["sign"] == "-"))', ("recv",)),
    (u"P5 去年の符号の向きを sign だけで見る", u'e["flips"].add(r["neg"] != (r["sign"] == "-"))', u'e["flips"].add(r["sign"] == "-")', ("recv",)),
    (u"P6 去年の符号の向きを負の印だけで見る", u'e["flips"].add(r["neg"] != (r["sign"] == "-"))', u'e["flips"].add(r["neg"])', ("recv",)),
    (u"P7 去年の候補から名を外す", u'e["cands"].add((r["name"], r["target"], r["dims"]))', u'e["cands"].add((r["target"], r["dims"]))', ("recv",)),
    (u"P8 去年の候補から個別か既定かを外す", u'e["cands"].add((r["name"], r["target"], r["dims"]))', u'e["cands"].add((r["name"], r["dims"]))', ("recv",)),
    (u"P9 去年の候補から区分を外す", u'e["cands"].add((r["name"], r["target"], r["dims"]))', u'e["cands"].add((r["name"], r["target"]))', ("recv",)),
    (u"P10 去年の期の名を集めない", u'        e["pns"].add(r["pn"])\n', u'', ("recv",)),
    (u"P11 去年の単位の形を空の fact から集めない", u'        e["forms"].add(r["form"])\n', u'        if not r["nil"]:\n            e["forms"].add(r["form"])\n', ("recv",)),
    (u"P12 去年の表の頭の印を集めない", u'        e["marks"].add(r["hmark"])\n', u'', ("recv",)),
    (u"P13 去年の表示の位を空の fact からも集める", u'            e["shifts"].add(r["shift"])\n', u'            e["shifts"].add(r["shift"])\n        else:\n            e["shifts"].add(r["shift"])\n', ("recv",)),
    # ---- 受ける側の決め(§2-2)
    (u"D1 去年に無い行を見ない(候補が無ければ決める)", u'    if e is None:\n        out["stop"] = S_NONE\n        return out\n', u'    if e is None:\n        e = od([("cands", set([(u"x", u"既定", ())])), ("flips", set()), ("pns", set()), ("forms", set()), ("marks", set()), ("shifts", set())])\n', ("recv",)),
    (u"D2 候補が 2 つ以上を見ない", u'    if len(e["cands"]) >= 2:\n        out["stop"] = S_MULTI\n        return out\n', u'    if len(e["cands"]) >= 3:\n        out["stop"] = S_MULTI\n        return out\n', ("recv",)),
    (u"D3 候補が 2 つ以上を 3 つ以上にする", u'    if len(e["cands"]) >= 2:', u'    if len(e["cands"]) > 2:', ("recv",)),
    (u"D4 候補が 1 つなのに止める", u'    if len(e["cands"]) >= 2:', u'    if len(e["cands"]) >= 1:', ("recv",)),
    (u"D5 表の頭の守りを逆にする", u'    if row["hmark"] not in e["marks"]:\n        guard = S_HEAD', u'    if row["hmark"] in e["marks"]:\n        guard = S_HEAD', ("recv",)),
    (u"D6 期の守りで pn が None を通す", u'    elif pn is None or pn not in e["pns"]:', u'    elif pn is not None and pn not in e["pns"]:', ("recv",)),
    (u"D7 期の守りを集まりの外でなく中にする", u'    elif pn is None or pn not in e["pns"]:', u'    elif pn is None or pn in e["pns"]:', ("recv",)),
    (u"D8 番号つきの守りを逆にする", u'    elif numbered_cand(cand):', u'    elif not numbered_cand(cand):', ("recv",)),
    (u"D9 単位の守りを集まりの中にする", u'    elif form not in e["forms"]:', u'    elif form in e["forms"]:', ("recv",)),
    (u"D10 符号の向きが 2 通りを 1 通り以上にする", u'    if not nil and len(e["flips"]) == 2:', u'    if not nil and len(e["flips"]) >= 1:', ("recv",)),
    (u"D11 符号の向きが 2 通りを空にも掛ける", u'    if not nil and len(e["flips"]) == 2:', u'    if len(e["flips"]) == 2:', ("recv",)),
    (u"D12 符号の向きが 2 通りの守りを外す", u'    if not nil and len(e["flips"]) == 2:\n        out["stop"] = S_SIGN\n        return out\n', u'', ("recv",)),
    (u"D13 守りの止めで止めずに決めた中身を持たない", u'        out["stop"], out["cf"] = guard, cf\n', u'        out["stop"] = guard\n', ("recv", "score")),
    (u"D14 守りの止めで決めた中身も持つ", u'        out["stop"], out["cf"] = guard, cf\n', u'        out["stop"], out["cf"], out["decided"] = guard, cf, cf\n', ("recv",)),
    (u"D15 止まらないとき決めた中身を持たない", u'    out["decided"], out["default"] = cf, default\n', u'    out["default"] = default\n', ("recv",)),
    (u"D16 既定の順の旗を持たない", u'    out["decided"], out["default"] = cf, default\n', u'    out["decided"] = cf\n', ("recv", "score")),
    (u"D17 去年と表示の位が違うを持たない", u'        out["shift_differs"] = LETTER_TO_UNIT[row["unit"]][1] not in e["shifts"]\n', u'        pass\n', ("recv", "score")),
    (u"D18 去年と表示の位が違うを空の fact にも掛ける", u'    if not nil and e["shifts"]:', u'    if e["shifts"] and not nil or nil:', ("recv",)),
    (u"D19 去年と表示の位が違うを集まりが空でも掛ける", u'    if not nil and e["shifts"]:', u'    if not nil:', ("recv",)),
    (u"D20 去年と表示の位が違うの比べを逆にする", u'LETTER_TO_UNIT[row["unit"]][1] not in e["shifts"]', u'LETTER_TO_UNIT[row["unit"]][1] in e["shifts"]', ("recv",)),
    (u"D21 去年と表示の位が違うを単位の形で見る", u'LETTER_TO_UNIT[row["unit"]][1] not in e["shifts"]', u'LETTER_TO_UNIT[row["unit"]][0] not in e["shifts"]', ("recv",)),
    (u"D22 期の名を去年の書類の決めで作る(書類のシートの決めでなく)", u'    pn = M.period_name(kind, [row["start"], row["end"]] if row["start"] else [row["end"]], dec)', u'    pn = M.period_name(kind, [row["start"], row["end"]] if row["start"] else [row["end"]], dict(start=u"2029-04-01", end=u"2030-03-31", filing=u"2030-06-30"))', ("recv",)),
    (u"D23 期の種類を日付の数でなく始まりの欄の有無の逆で決める", u'    kind = "duration" if row["start"] else "instant"\n    pn =', u'    kind = "instant" if row["start"] else "duration"\n    pn =', ("recv",)),
    (u"D24 期の名の日を終わりだけにする", u'M.period_name(kind, [row["start"], row["end"]] if row["start"] else [row["end"]], dec)', u'M.period_name(kind, [row["end"]], dec)', ("recv",)),
    (u"D28 番号つきの守りを候補でなく今年の名で見る", u'    elif numbered_cand(cand):', u'    elif numbered_cand((row["T"], u"", ())):', ("recv",)),
    (u"D29 番号つきの member を軸の名でも見る", u'    return any(G.MEMBER_RE.match(local_name(m)) for _ax, m in cand[2])', u'    return any(G.MEMBER_RE.match(local_name(m)) or G.MEMBER_RE.match(local_name(ax)) for ax, m in cand[2])', ("pure",)),
    (u"D30 番号つきの member の接頭辞を除かない", u'G.MEMBER_RE.match(local_name(m))', u'G.MEMBER_RE.match(m)', ("pure", "recv")),
    (u"D31 番号つきの member を区分の最初の 1 つだけ見る", u'    return any(G.MEMBER_RE.match(local_name(m)) for _ax, m in cand[2])', u'    return any(G.MEMBER_RE.match(local_name(m)) for _ax, m in cand[2][:1])', ("pure",)),
    (u"D32 番号つきの member の局所名を最初の : の前で見る", u'return name.split(":", 1)[1] if ":" in name else name', u'return name.split(":", 1)[0] if ":" in name else name', ("pure", "recv")),
    (u"D33 無くなった行を数えない", u'("lost", sum(1 for k in tab if k not in here))', u'("lost", 0)', ("recv", "score")),
    (u"D34 無くなった行を今年の行の数で数える", u'("lost", sum(1 for k in tab if k not in here))', u'("lost", sum(1 for k in here if k not in tab))', ("recv",)),
    (u"D35 無くなった行を行の数で数える(鍵でなく)", u'("lost", sum(1 for k in tab if k not in here))', u'("lost", len(tab) - len(rows))', ("recv",)),
    (u"D36 今年の鍵の集まりから見出しの字を外す", u'    here = set(key_of(r) for r in rows)', u'    here = set((r["th"], r["T"], r["td"]) for r in rows)', ("recv",)),
    (u"D37 行の番号を 1 始まりにする", u'results = [receive_row(i, r, dec, tab) for i, r in enumerate(rows)]', u'results = [receive_row(i, r, dec, tab) for i, r in enumerate(rows, 1)]', ("recv",)),
    (u"D38 行の順を逆にする", u'results = [receive_row(i, r, dec, tab) for i, r in enumerate(rows)]', u'results = [receive_row(i, r, dec, tab) for i, r in reversed(list(enumerate(rows)))]', ("recv", "score")),
    # ---- 値・精度・符号(§2-2 の 8.)
    (u"V1 符号の XOR を外す(金額の負だけで決める)", u'value = M.number_value(content, shift, u"-" if neg != flip else None)', u'value = M.number_value(content, shift, u"-" if neg else None)', ("recv",)),
    (u"V2 符号の XOR を去年の向きだけにする", u'value = M.number_value(content, shift, u"-" if neg != flip else None)', u'value = M.number_value(content, shift, u"-" if flip else None)', ("recv",)),
    (u"V3 符号の XOR を AND にする", u'value = M.number_value(content, shift, u"-" if neg != flip else None)', u'value = M.number_value(content, shift, u"-" if neg and flip else None)', ("recv",)),
    (u"V4 符号の XOR を OR にする", u'value = M.number_value(content, shift, u"-" if neg != flip else None)', u'value = M.number_value(content, shift, u"-" if neg or flip else None)', ("recv",)),
    (u"V5 符号の XOR を逆(一致で負)にする", u'value = M.number_value(content, shift, u"-" if neg != flip else None)', u'value = M.number_value(content, shift, u"-" if neg == flip else None)', ("recv",)),
    (u"V6 去年の向きが逆を {False} のとき逆とする", u'        flip = flips == set([True])\n', u'        flip = flips == set([False])\n', ("recv",)),
    (u"V7 去年の向きが逆を True を含むとき逆とする", u'        flip = flips == set([True])\n', u'        flip = True in flips\n', ("recv",)),
    (u"V8 去年が空のときの既定を「逆」にする", u'        flip = flips == set([True])\n', u'        flip = flips == set([True]) or not flips\n', ("recv",)),
    (u"V9 去年が空のとき既定を使ったと数えない", u'        default = not flips\n', u'        default = False\n', ("recv", "score")),
    (u"V10 去年が空でなくても既定を使ったと数える", u'        default = not flips\n', u'        default = True\n', ("recv", "score")),
    (u"V11 空の fact にも既定を使ったと数える", u'        form, shift, prec, value = LETTER_TO_FORM[row["unit"]], None, None, VALUE_NONE\n        default = False\n', u'        form, shift, prec, value = LETTER_TO_FORM[row["unit"]], None, None, VALUE_NONE\n        default = not e["flips"]\n', ("recv",)),
    (u"V12 精度の式の表示の位の符号を逆にする", u'        prec = -shift + dig\n', u'        prec = shift + dig\n', ("recv",)),
    (u"V13 精度の式の小数の桁の符号を逆にする", u'        prec = -shift + dig\n', u'        prec = -shift - dig\n', ("recv",)),
    (u"V14 精度の式から小数の桁を外す", u'        prec = -shift + dig\n', u'        prec = -shift\n', ("recv",)),
    (u"V15 精度の式から表示の位を外す", u'        prec = -shift + dig\n', u'        prec = dig\n', ("recv",)),
    (u"V16 値の位を使わない(表示の位 0)", u'        value = M.number_value(content, shift, u"-" if neg != flip else None)', u'        value = M.number_value(content, 0, u"-" if neg != flip else None)', ("recv",)),
    (u"V17 値の位を逆向きにする", u'        value = M.number_value(content, shift, u"-" if neg != flip else None)', u'        value = M.number_value(content, -shift, u"-" if neg != flip else None)', ("recv",)),
    (u"V18 値に精度の位を使う", u'        value = M.number_value(content, shift, u"-" if neg != flip else None)', u'        value = M.number_value(content, prec, u"-" if neg != flip else None)', ("recv",)),
    (u"V19 空の fact の値を 0 にする", u'form, shift, prec, value = LETTER_TO_FORM[row["unit"]], None, None, VALUE_NONE', u'form, shift, prec, value = LETTER_TO_FORM[row["unit"]], None, None, u"0"', ("recv",)),
    (u"V20 空の fact に表示の位を付ける", u'form, shift, prec, value = LETTER_TO_FORM[row["unit"]], None, None, VALUE_NONE', u'form, shift, prec, value = LETTER_TO_FORM[row["unit"]], 0, None, VALUE_NONE', ("recv",)),
    (u"V21 空の fact に精度を付ける", u'form, shift, prec, value = LETTER_TO_FORM[row["unit"]], None, None, VALUE_NONE', u'form, shift, prec, value = LETTER_TO_FORM[row["unit"]], None, 0, VALUE_NONE', ("recv",)),
    (u"V22 空かを逆にする", u'("value", value), ("form", form), ("shift", shift), ("prec", prec), ("nil", nil)]), default', u'("value", value), ("form", form), ("shift", shift), ("prec", prec), ("nil", not nil)]), default', ("recv",)),
    (u"V23 期の種類を常に期間にする", u'return od([("name", cand[0]), ("target", cand[1]), ("dims", [list(d) for d in cand[2]]), ("pkind", kind)', u'return od([("name", cand[0]), ("target", cand[1]), ("dims", [list(d) for d in cand[2]]), ("pkind", "duration")', ("recv",)),
    (u"V24 期の日を終わりだけにする", u'("pkind", kind), ("period", dates),', u'("pkind", kind), ("period", dates[-1:]),', ("recv",)),
    (u"V25 区分を持ち越さない", u'("dims", [list(d) for d in cand[2]]), ("pkind", kind)', u'("dims", []), ("pkind", kind)', ("recv",)),
    (u"V26 個別か既定かを既定に固定する", u'return od([("name", cand[0]), ("target", cand[1]),', u'return od([("name", cand[0]), ("target", u"既定"),', ("recv",)),
    (u"V27 単位の形を表の字の逆引きでなく去年の集まりから取る", u'        form, shift = LETTER_TO_UNIT[row["unit"]]\n', u'        form, shift = sorted(e["forms"])[0] if e["forms"] else LETTER_TO_UNIT[row["unit"]][0], LETTER_TO_UNIT[row["unit"]][1]\n', ("recv",)),
    (u"V28 表示の位を去年の集まりから取る", u'        form, shift = LETTER_TO_UNIT[row["unit"]]\n', u'        form, shift = LETTER_TO_UNIT[row["unit"]][0], (sorted(e["shifts"])[0] if e["shifts"] else LETTER_TO_UNIT[row["unit"]][1])\n', ("recv",)),
    (u"V29 決めた中身の欄の並びを替える", u'return od([("name", cand[0]), ("target", cand[1]),', u'return od([("target", cand[1]), ("name", cand[0]),', ("recv",)),
    (u"V30 守りの止めの決めた中身を去年の符号で逆にする", u'    cf, default = decide_row(row, dec, e)\n', u'    cf, default = decide_row(row, dec, e)\n    cf["value"] = cf["value"][1:] if cf["value"].startswith(u"-") else cf["value"]\n', ("recv",)),
    # ---- 採点(§2-3)
    (u"S1 採点が答え同士を比べる(違う欄)", u'            diffs = differing_fields(res["decided"], ans)', u'            diffs = differing_fields(ans, ans)', ("score",)),
    (u"S2 採点が答え同士を比べる(守りの正しかった止め)", u'                if not differing_fields(res["cf"], ans):', u'                if not differing_fields(ans, ans):', ("score",)),
    (u"S3 正しかった止めを緩める(名だけ見る)", u'                if not differing_fields(res["cf"], ans):', u'                if res["cf"]["name"] == ans["name"]:', ("score",)),
    (u"S5 正しかった止めを守り以外の止めにも数える", u'            if res["stop"] in GUARDS:', u'            if res["stop"] in GUARDS or res["stop"] == S_MULTI:', ("score",)),
    (u"S6 守りの止めの数を数えない", u'                g[u"止めた"] += 1\n', u'', ("score",)),
    (u"S7 止めた理由を数えない", u'            why[res["stop"]] += 1\n', u'', ("score",)),
    (u"S8 違った欄を数えない", u'                for f in diffs:\n                    inner[u"欄ごと"][f] += 1\n', u'', ("score",)),
    (u"S9 符号だけ違うを緩める(値の違いなら全部)", u'                if sign_only(res["decided"], ans, diffs):', u'                if diffs == [u"値"]:', ("score",)),
    (u"S10 符号だけ違うを絶対値を見ない", u'    return diffs == [u"値"] and dec["value"].lstrip(u"-") == ans["value"].lstrip(u"-")', u'    return diffs == [u"値"]', ("pure",)),
    (u"S11 符号だけ違うを値だけの違いにしない", u'    return diffs == [u"値"] and dec["value"].lstrip(u"-") == ans["value"].lstrip(u"-")', u'    return u"値" in diffs and dec["value"].lstrip(u"-") == ans["value"].lstrip(u"-")', ("pure",)),
    (u"S12 符号だけ違うの絶対値を決めた側の符号で比べる", u'dec["value"].lstrip(u"-") == ans["value"].lstrip(u"-")', u'dec["value"] == ans["value"]', ("pure",)),
    (u"S13 答えの値が符号つきの 0 を -0 でなく 0 で見る", u'                    if ans["value"] == u"-0":', u'                    if ans["value"] == u"0":', ("score",)),
    (u"S14 答えの値が符号つきの 0 を決めた側で見る", u'                    if ans["value"] == u"-0":', u'                    if res["decided"]["value"] == u"-0":', ("score",)),
    (u"S15 去年が空で既定の順を使ったを数えない", u'                if res["default"]:\n                    inner[u"去年が空で既定の順を使った"] += 1\n', u'', ("score",)),
    (u"S16 去年が空で既定の順を使ったを違うでなく全部同じにも数える", u'                if res["default"]:\n                    inner[u"去年が空で既定の順を使った"] += 1\n', u'                if res["default"]:\n                    inner[u"去年が空で既定の順を使った"] += 1\n            if res["default"] and not diffs:\n                inner[u"去年が空で既定の順を使った"] += 1\n', ("score",)),
    (u"S17 負の印ありを空にも数える", u'        if ans["mark"] and not ans["nil"]:', u'        if ans["mark"]:', ("score",)),
    (u"S18 負の印ありを答えの値の符号で見る", u'        if ans["mark"] and not ans["nil"]:', u'        if ans["value"].startswith(u"-") and not ans["nil"]:', ("score",)),
    (u"S19 表示の数が 0 を空にも数える", u'        if (not ans["nil"]) and ans["value"].lstrip(u"-") == u"0":', u'        if ans["value"].lstrip(u"-") in (u"0", VALUE_NONE):', ("score",)),
    (u"S20 表示の数が 0 を符号つきの 0 を除く", u'        if (not ans["nil"]) and ans["value"].lstrip(u"-") == u"0":', u'        if (not ans["nil"]) and ans["value"] == u"0":', ("score",)),
    (u"S21 空を数えない", u'        if ans["nil"]:\n            sc[u"空"] += 1\n', u'', ("score",)),
    (u"S22 符号の向きが逆を空にも数える", u'        sign_rev = (not ans["nil"]) and ans["mark"] != ans["value"].startswith(u"-")', u'        sign_rev = ans["mark"] != ans["value"].startswith(u"-")', ("score",)),
    (u"S23 符号の向きが逆を逆にする(同じを数える)", u'        sign_rev = (not ans["nil"]) and ans["mark"] != ans["value"].startswith(u"-")', u'        sign_rev = (not ans["nil"]) and ans["mark"] == ans["value"].startswith(u"-")', ("score",)),
    (u"S24 符号の向きが逆を数えない", u'        if sign_rev:\n            sc[u"符号の向きが逆"] += 1\n', u'', ("score",)),
    (u"S25 表示の位が違うの分けを止めに入れない", u'            s[u"件数"] += 1\n            s[r] += 1\n', u'            s[u"件数"] += 1\n            if r != u"止めた":\n                s[r] += 1\n', ("score",)),
    (u"S26 表示の位が違うの件数を数えない", u'            s[u"件数"] += 1\n', u'', ("score",)),
    (u"S27 無くなった行を採点に入れない", u'    ent[u"無くなった行"] = received["lost"]\n', u'', ("score",)),
    (u"S28 行の数の検査を外す", u'    if len(rows) != len(answers) or len(answers) != cnt["D"]:\n        raise Stop(u"**受ける側の行の数と答えの行の数が合わない。止める**")\n', u'', ("score",)),
    (u"S29 行の数の検査を片方だけにする", u'    if len(rows) != len(answers) or len(answers) != cnt["D"]:', u'    if len(rows) != len(answers):', ("score",)),
    (u"S30 行の中の数の fact を D にする", u'    ent[u"行の中の数の fact"] = cnt["inrow"]\n', u'    ent[u"行の中の数の fact"] = cnt["D"]\n', ("score",)),
    (u"S31 突き合わせの外の file と fact を取り違える", u'od([(u"file", cnt["files_out"]), (u"ix:nonFraction の fact", cnt["ix_out"]), (u"うち行の中の数の fact", cnt["inrow_out"])])', u'od([(u"file", cnt["ix_out"]), (u"ix:nonFraction の fact", cnt["files_out"]), (u"うち行の中の数の fact", cnt["inrow_out"])])', ("score",)),
    (u"S32 組の番号を 0 始まりにする", u'    ent = od([(u"番号", n)])\n    ent.update(zero_entry())', u'    ent = od([(u"番号", n - 1)])\n    ent.update(zero_entry())', ("score",)),
    (u"S33 止めを決めたに数える", u'            r = u"止めた"\n            ent[u"止めた"] += 1\n', u'            r = u"止めた"\n            ent[u"決めたが違う"] += 1\n', ("score",)),
    (u"S34 決めて全部同じを違うに数える", u'                r = u"決めて全部同じ"\n                ent[r] += 1\n', u'                r = u"決めて全部同じ"\n                ent[u"決めたが違う"] += 1\n', ("score",)),
    (u"S35 違った欄の順を無視して先頭の欄だけ数える", u'                for f in diffs:\n                    inner[u"欄ごと"][f] += 1\n', u'                for f in diffs[:1]:\n                    inner[u"欄ごと"][f] += 1\n', ("score",)),
    (u"S36 違う欄に期の日と期の種類を入れ替える", u'u"区分", u"期の日", u"期の種類", ', u'u"区分", u"期の種類", u"期の日", ', ("seal", "pure")),
    # ---- 集計・判定(§3・§4)
    (u"J1 XE0-1 の分子を決めたが違うにする", u'put(u"XE0-1 決めて全部同じ ÷ D", [(u"率", rate_of(same, D))], rate_holds(same, D, BOUNDS["XE0-1"]))', u'put(u"XE0-1 決めて全部同じ ÷ D", [(u"率", rate_of(same, D))], rate_holds(same + diff, D, BOUNDS["XE0-1"]))', ("tot",)),
    (u"J2 XE0-1 の分母を行の中の数の fact にする", u'rate_holds(same, D, BOUNDS["XE0-1"])', u'rate_holds(same, inrow, BOUNDS["XE0-1"])', ("tot",)),
    (u"J3 XE0-2 の 1 fact 以上を見ない", u'diff >= MIN_DIFF and rate_holds(diff, D, BOUNDS["XE0-2"])', u'rate_holds(diff, D, BOUNDS["XE0-2"])', ("tot",)),
    (u"J4 XE0-2 の率を止めたにする", u'diff >= MIN_DIFF and rate_holds(diff, D, BOUNDS["XE0-2"])', u'diff >= MIN_DIFF and rate_holds(stop, D, BOUNDS["XE0-2"])', ("tot",)),
    (u"J5 XE0-3 の分子を違う全部にする", u'holds_bound(BOUNDS["XE0-3"], only_sign)', u'holds_bound(BOUNDS["XE0-3"], diff)', ("tot",)),
    (u"J6 XE0-4 の分子を決めたが違うにする", u'rate_holds(stop, D, BOUNDS["XE0-4"])', u'rate_holds(diff, D, BOUNDS["XE0-4"])', ("tot",)),
    (u"J7 XE0-4 の分母を行の中の数の fact にする", u'rate_holds(stop, D, BOUNDS["XE0-4"])', u'rate_holds(stop, inrow, BOUNDS["XE0-4"])', ("tot",)),
    (u"J8 XE0-5 の分母を止めた全部にする", u'rate_holds(g_ok, g_stop, BOUNDS["XE0-5"])', u'rate_holds(g_ok, stop, BOUNDS["XE0-5"])', ("tot",)),
    (u"J9 XE0-5 の守りから単位を外す", u'    g_stop = sum(gs[GUARD_LABEL[g]][u"止めた"] for g in GUARDS) if gs else 0\n', u'    g_stop = sum(gs[GUARD_LABEL[g]][u"止めた"] for g in GUARDS[:3]) if gs else 0\n', ("tot",)),
    (u"J10 XE0-5 の正しかった止めから番号つきを外す", u'    g_ok = sum(gs[GUARD_LABEL[g]][u"正しかった止め"] for g in GUARDS) if gs else 0\n', u'    g_ok = sum(gs[GUARD_LABEL[g]][u"正しかった止め"] for g in GUARDS if g != S_NUMBERED) if gs else 0\n', ("tot",)),
    (u"J11 XE0-6 に表の頭を入れる", u'    g12 = (gs[GUARD_LABEL[S_PERIOD]][u"止めた"] + gs[GUARD_LABEL[S_UNIT]][u"止めた"]) if gs else 0\n', u'    g12 = (gs[GUARD_LABEL[S_PERIOD]][u"止めた"] + gs[GUARD_LABEL[S_UNIT]][u"止めた"] + gs[GUARD_LABEL[S_HEAD]][u"止めた"]) if gs else 0\n', ("tot",)),
    (u"J12 XE0-6 から単位を外す", u'    g12 = (gs[GUARD_LABEL[S_PERIOD]][u"止めた"] + gs[GUARD_LABEL[S_UNIT]][u"止めた"]) if gs else 0\n', u'    g12 = gs[GUARD_LABEL[S_PERIOD]][u"止めた"] if gs else 0\n', ("tot",)),
    (u"J13 XE0-6 から期を外す", u'    g12 = (gs[GUARD_LABEL[S_PERIOD]][u"止めた"] + gs[GUARD_LABEL[S_UNIT]][u"止めた"]) if gs else 0\n', u'    g12 = gs[GUARD_LABEL[S_UNIT]][u"止めた"] if gs else 0\n', ("tot",)),
    (u"J14 XE0-6 の 1 fact 以上を見ない", u'g12 >= MIN_G12 and rate_holds(g12, D, BOUNDS["XE0-6"])', u'rate_holds(g12, D, BOUNDS["XE0-6"])', ("tot",)),
    (u"J15 XE0-6 の分母を行の中の数の fact にする", u'rate_holds(g12, D, BOUNDS["XE0-6"])', u'rate_holds(g12, inrow, BOUNDS["XE0-6"])', ("tot",)),
    (u"J16 XE0-7 から 15 桁を外す", u'    unw = (bad_unit.get(EXCLUDES[2], 0) + bad_unit.get(EXCLUDES[3], 0)) if bad_unit else 0\n', u'    unw = bad_unit.get(EXCLUDES[2], 0) if bad_unit else 0\n', ("tot",)),
    (u"J17 XE0-7 から単位を外す", u'    unw = (bad_unit.get(EXCLUDES[2], 0) + bad_unit.get(EXCLUDES[3], 0)) if bad_unit else 0\n', u'    unw = bad_unit.get(EXCLUDES[3], 0) if bad_unit else 0\n', ("tot",)),
    (u"J18 XE0-7 に行の字が空を入れる", u'    unw = (bad_unit.get(EXCLUDES[2], 0) + bad_unit.get(EXCLUDES[3], 0)) if bad_unit else 0\n', u'    unw = (bad_unit.get(EXCLUDES[2], 0) + bad_unit.get(EXCLUDES[3], 0) + bad_unit.get(EXCLUDES[0], 0)) if bad_unit else 0\n', ("tot",)),
    (u"J19 XE0-7 の分母を D にする", u'rate_holds(unw, inrow, BOUNDS["XE0-7"])', u'rate_holds(unw, D, BOUNDS["XE0-7"])', ("tot",)),
    (u"J20 XE0-8 を違いが 1 以下の書類にする", u'    no_diff = sum(1 for e in rest if e[u"決めたが違う"] == 0)\n', u'    no_diff = sum(1 for e in rest if e[u"決めたが違う"] <= 1)\n', ("tot",)),
    (u"J21 XE0-8 を違いが在る書類にする", u'    no_diff = sum(1 for e in rest if e[u"決めたが違う"] == 0)\n', u'    no_diff = sum(1 for e in rest if e[u"決めたが違う"] != 0)\n', ("tot",)),
    (u"J22 XE0-9 の 95% を 100% にする", u'(DOC_SAME_PCT, True, None, False)', u'(DOC_SAME_PCT + 5, True, None, False)', ("tot",)),
    (u"J23 XE0-9 の 95% 以上を超えるにする", u'(DOC_SAME_PCT, True, None, False)', u'(DOC_SAME_PCT, False, None, False)', ("tot",)),
    (u"J24 XE0-9 の分子を決めたが違うでなく止めたにする", u'rate_holds(e[u"決めて全部同じ"], e[u"D"], (DOC_SAME_PCT, True, None, False))', u'rate_holds(e[u"止めた"], e[u"D"], (DOC_SAME_PCT, True, None, False))', ("tot",)),
    (u"J25 XE0-9 の分母を行の中の数の fact にする", u'rate_holds(e[u"決めて全部同じ"], e[u"D"], (DOC_SAME_PCT, True, None, False))', u'rate_holds(e[u"決めて全部同じ"], e[u"行の中の数の fact"], (DOC_SAME_PCT, True, None, False))', ("tot",)),
    (u"J26 判定に訓練の 3 組を入れる", u'    rest = [e for e in entries if e[u"番号"] > SEEN_MAX_NO]\n    tot = M.sum_nested', u'    rest = [e for e in entries]\n    tot = M.sum_nested', ("tot",)),
    (u"J27 判定に番号 4 を入れない", u'    rest = [e for e in entries if e[u"番号"] > SEEN_MAX_NO]\n    tot = M.sum_nested', u'    rest = [e for e in entries if e[u"番号"] > SEEN_MAX_NO + 1]\n    tot = M.sum_nested', ("tot",)),
    (u"J28 率の分母 0 を当たりにする", u'    return d > 0 and holds_bound(b, fractions.Fraction(100 * n, d))', u'    return d == 0 or holds_bound(b, fractions.Fraction(100 * n, d))', ("pure", "tot")),
    (u"J29 率を整数の割り算にする", u'holds_bound(b, fractions.Fraction(100 * n, d))', u'holds_bound(b, 100 * n // d)', ("pure", "tot")),
    (u"J30 率を % でなく割合にする", u'holds_bound(b, fractions.Fraction(100 * n, d))', u'holds_bound(b, fractions.Fraction(n, d))', ("pure", "tot")),
    (u"J31 境の下限の比べを > にする(含まない)", u'        ok = ok and (x >= c if lo_in else x > c)', u'        ok = ok and (x > c)', ("pure", "tot")),
    (u"J32 境の下限の比べを >= にする(含む)", u'        ok = ok and (x >= c if lo_in else x > c)', u'        ok = ok and (x >= c)', ("pure",)),
    (u"J33 境の上限の比べを < にする", u'        ok = ok and (x <= c if hi_in else x < c)', u'        ok = ok and (x < c)', ("pure", "tot")),
    (u"J34 境の上限の比べを <= にする", u'        ok = ok and (x <= c if hi_in else x < c)', u'        ok = ok and (x <= c)', ("pure",)),
    (u"J35 境の値を float にする", u'        c = fractions.Fraction(str(lo))\n', u'        c = float(lo)\n', ("pure",)),
    (u"J36 旗を 1 つだけ照らす(止めた)", u'    return od([(u"訓練の 3 組の数", got), (u"封 §0 の数", od(SEAL_TRAIN)), (u"§0 と違う", dict(got) != dict(SEAL_TRAIN))])', u'    return od([(u"訓練の 3 組の数", got), (u"封 §0 の数", od(SEAL_TRAIN)), (u"§0 と違う", got[u"止めた"] != SEAL_TRAIN[u"止めた"])])', ("tot",)),
    (u"J37 旗を全部の組で照らす", u'    t = totals_of(entries)[u"訓練の 3 組"][u"数"]\n    got', u'    t = totals_of(entries)[u"全部"][u"数"]\n    got', ("tot",)),
    (u"J38 旗を判定の 60 組で照らす", u'    t = totals_of(entries)[u"訓練の 3 組"][u"数"]\n    got', u'    t = totals_of(entries)[u"判定の 60 組"][u"数"]\n    got', ("tot",)),
    (u"J39 旗を逆にする", u'(u"§0 と違う", dict(got) != dict(SEAL_TRAIN))', u'(u"§0 と違う", dict(got) == dict(SEAL_TRAIN))', ("tot", "rec")),
    (u"J40 旗を決めたが違うを見ずに照らす", u'    got = od((k, t.get(k, 0)) for k in SEAL_TRAIN)', u'    got = od((k, t.get(k, 0) if k != u"決めたが違う" else 0) for k in SEAL_TRAIN)', ("tot",)),
    (u"J41 集計の組を判定に入れない", u'               (u"全部", group(entries))])', u'               (u"全部", group([e for e in entries if e[u"番号"] > SEEN_MAX_NO]))])', ("tot",)),
    (u"J42 集計の番号を除かない(番号を足す)", u'NOT_SUMMED = (u"番号",)', u'NOT_SUMMED = ()', ("tot",)),
    (u"J43 当たりを書かない", u'        b[u"当たり"] = bool(hit)\n', u'        b[u"当たり"] = True\n', ("tot",)),
    (u"J44 当たりを逆にする", u'        b[u"当たり"] = bool(hit)\n', u'        b[u"当たり"] = not hit\n', ("tot",)),
    # ---- 記録・検査(§5)
    (u"Q1 組の数 63 の検査を外す", u'    if len(entries) != PAIRS_WANT or nos != sorted(set(nos)):\n        raise Stop(u"**組が 63 でないか番号が昇順でない。止める**")\n', u'', ("rec",)),
    (u"Q2 番号の昇順の検査を外す", u'    if len(entries) != PAIRS_WANT or nos != sorted(set(nos)):', u'    if len(entries) != PAIRS_WANT:', ("rec",)),
    (u"Q3 訓練 3・判定 60 の検査を外す", u'    if tot[u"訓練の 3 組"][u"組"] != TRAIN_WANT or tot[u"判定の 60 組"][u"組"] != JUDGE_WANT:\n        raise Stop(u"**組の数が訓練 3・判定 60・全部 63 でない。止める**")\n', u'', ("rec",)),
    (u"Q4 --check が集計を導き直さない", u'    if dumps(totals_of(docs)) != dumps(rec[u"集計"]):\n        raise Stop(u"**記録の集計が組ごとの数と合わない。止める**")\n', u'', ("rec",)),
    (u"Q5 --check が判定を導き直さない", u'    if dumps(judged(docs)) != dumps(rec[judged_key(rec)]):\n        raise Stop(u"**記録の判定の数が組ごとの数と合わない。止める**")\n', u'', ("rec",)),
    (u"Q6 --check が旗を導き直さない", u'    if dumps(seal_flag(docs)) != dumps(rec[u"§3 の旗"]):\n        raise Stop(u"**記録の旗が組ごとの数と合わない。止める**")\n', u'', ("rec",)),
    (u"Q7 --check が組の関係を見ない", u'    for d in docs:\n        why = entry_problems(d)\n        if why:\n            raise Stop(u"**記録の組の数が違う: %s。止める**" % why)\n', u'    for d in docs:\n        pass\n', ("rec",)),
    (u"Q8 --check が限界・出どころを見ない", u'    if (tot[u"訓練の 3 組"][u"組"], tot[u"判定の 60 組"][u"組"]) != (TRAIN_WANT, JUDGE_WANT) or rec[u"限界"] != list(LIMITS) or rec[u"型の欄ごとの出どころ"] != dict(ORIGIN):\n        raise Stop(u"**記録の材料・限界・出どころが違う。止める**")\n', u'', ("rec",)),
    (u"Q9 --check が禁止のものを見ない", u'    check_clean(rec, text if text is not None else dumps(rec))\n\n\ndef record_text', u'\n\ndef record_text', ("rec",)),
    (u"Q10 書く前の検査を外す", u'    text = record_text(rec, secret)\n    os.makedirs', u'    text = dumps(rec)\n    os.makedirs', ("rec",)),
    (u"Q11 書いた後の検査を外す", u'    try:\n        check_clean(rec, back, secret)\n    except SystemExit:\n        os.remove(path)\n        raise\n', u'', ("rec",)),
    (u"Q12 書いた後に禁止のものが見つかっても file を消さない", u'    except SystemExit:\n        os.remove(path)\n        raise\n', u'    except SystemExit:\n        raise\n', ("rec",)),
    (u"Q13 記録が既に在っても書く", u'    if os.path.exists(path):\n        raise Stop(u"**記録が既に在る: %s。止める**" % os.path.basename(path))\n', u'', ("rec",)),
    (u"Q14 排他で書かない", u'    with open(path, "xb") as fh:\n        fh.write(data)', u'    with open(path, "wb") as fh:\n        fh.write(data)', ("rec",)),
    (u"Q15 日付の形を検査しない", u'    if DATE_RE.search(W.HEX_RE.sub(u"", text).replace(SEAL_REL, u"")):\n        raise Stop(u"**記録に日付の形の字が在る。止める**")\n', u'', ("rec",)),
    (u"Q16 封の path の日付を除かずに検査する", u'.replace(SEAL_REL, u"")', u'', ("rec",)),
    (u"Q17 禁止のものの検査を呼ばない", u'    N.check_clean(rec, text, secret)\n', u'', ("rec",)),
    (u"Q18 記録に封の commit を書かない", u'    rec[u"封の commit"] = SEAL_COMMIT\n', u'    rec[u"封の commit"] = u""\n', ("rec",)),
    (u"Q19 記録の script の sha256 を書かない", u'    rec[u"この script の sha256"] = sha_script or sha256_file(os.path.abspath(__file__))\n', u'    rec[u"この script の sha256"] = u""\n', ("rec",)),
    (u"Q20 記録に限界を書かない", u'    rec[u"限界"] = list(LIMITS)\n', u'    rec[u"限界"] = []\n', ("rec",)),
    (u"Q21 secret に要素の局所名を入れない", u'return (set(), set(n for n in names if len(n) >= 3), [d[0] for d in docs] + [p[3] for p in pairs], ecodes, set(), set())', u'return (set(), set(), [d[0] for d in docs] + [p[3] for p in pairs], ecodes, set(), set())', ("rec",)),
    (u"Q22 secret に提出者のコードを入れない", u'    ecodes = set(p[5] for p in pairs)\n', u'    ecodes = set()\n', ("rec",)),
    (u"Q23 secret に今年の書類の docID を入れない", u'[d[0] for d in docs] + [p[3] for p in pairs]', u'[p[3] for p in pairs]', ("rec",)),
    (u"Q24 secret に前の年の docID を入れない", u'[d[0] for d in docs] + [p[3] for p in pairs]', u'[d[0] for d in docs]', ("rec",)),
    (u"Q25 材料の組の数を訓練・判定で分けない", u'(u"訓練の組の数", sum(1 for p in pairs if p[0] <= SEEN_MAX_NO)), (u"判定の組の数", sum(1 for p in pairs if p[0] > SEEN_MAX_NO)),', u'(u"訓練の組の数", 3), (u"判定の組の数", 60),', ("rec",)),
    (u"Q26 --check が記録が無いのに通る", u'    if not os.path.isfile(p):\n        raise Stop(u"**在る記録が無い。止める**")\n    with io.open(p, encoding="utf-8") as fh:\n        text = fh.read()\n    rec = json.loads(text, object_pairs_hook=od)\n    verify_record', u'    text = u"{}"\n    rec = {}\n    verify_record', ("rec",)),
    (u"Q27 記録の欄の並びを替える(出どころを先に)", u'    rec[u"書類"] = entries\n    rec[u"集計"] = tot\n', u'    rec[u"集計"] = tot\n    rec[u"書類"] = entries\n', ("rec",)),
    # ---- 工程の分け・配線
    (u"W1 受ける側が答えの folder を読む", u'    for n in sorted(prior_paths):\n        xp = os.path.join(xlsx_dir, u"%02d.xlsx" % n)\n', u'    for n in sorted(prior_paths):\n        xp = os.path.join(xlsx_dir, u"%02d.xlsx" % n)\n        open(os.path.join(os.path.dirname(xlsx_dir), u"answer", u"%02d.json" % n)).close()\n', ("iso",)),
    (u"W2 受ける側が今年の zip を開く(引数を足す)", u'def receive_folder(xlsx_dir, out_dir, prior_paths, reader=None):', u'def receive_folder(xlsx_dir, out_dir, prior_paths, reader=None, cur_zip=None):', ("iso",)),
    (u"W3 受ける側が今年の書類の読み出しを呼ぶ", u'        res = receive_pair(xp, reader(prior_paths[n]))', u'        reader(u"CUR%d" % n)\n        res = receive_pair(xp, reader(prior_paths[n]))', ("iso",)),
    (u"W4 受ける側が答えの字を持つ", u'def receive_pair(xlsx_path, prior_side):\n    u"""', u'def receive_pair(xlsx_path, prior_side):\n    answer_dir = u"answer"\n    u"""', ("iso",)),
    (u"W5 受ける側が xlsx を今年の側の分析から作る", u'    dec, rows = read_xlsx(xlsx_path)\n    tab = prior_table(prior_side)\n', u'    dec, rows = read_xlsx(xlsx_path)\n    tab = prior_table(prior_side)\n    sheet_rows_of(prior_side)\n', ("iso",)),
    (u"W6 受ける側が make_pairs を呼ぶ", u'    reader = reader or read_zip_side\n    os.makedirs(out_dir)\n', u'    reader = reader or read_zip_side\n    Y.make_pairs(DOCS_DIR, PRIOR_DIR)\n    os.makedirs(out_dir)\n', ("iso",)),
    (u"W7 受ける側が出力を答えの folder の隣に書く", u'        write_new(os.path.join(out_dir, u"%02d.json" % n), dumps(od([(u"番号", n), (u"受けた", res)])))', u'        write_new(os.path.join(out_dir, u"%02d.json" % n), dumps(od([(u"番号", n), (u"受けた", res), (u"答え", load_json(os.path.join(out_dir, u"x")))])))', ("iso",)),
    (u"W8 受ける側が出力に答えの側の欄を書く", u'        res = receive_pair(xp, reader(prior_paths[n]))\n', u'        res = receive_pair(xp, reader(prior_paths[n]))\n        res["mark"] = True\n', ("dev",)),
    (u"W9 作る側が xlsx と答えを同じ folder に書く", u'    xdir, adir = os.path.join(tmp, u"xlsx"), os.path.join(tmp, u"answer")\n    os.makedirs(xdir)\n    os.makedirs(adir)\n', u'    xdir, adir = os.path.join(tmp, u"xlsx"), os.path.join(tmp, u"xlsx")\n    os.makedirs(xdir)\n', ("dev",)),
    (u"W10 作る側が答えを書かない", u'    write_new(os.path.join(ans_dir, u"%02d.json" % n), dumps(od([(u"番号", n), (u"数", cnt), (u"答え", answers)])))\n', u'', ("dev",)),
    (u"W11 作る側が xlsx に答えの file を混ぜる", u'    write_xlsx(os.path.join(xlsx_dir, u"%02d.xlsx" % n), cur_side["dec"], rows)\n', u'    write_xlsx(os.path.join(xlsx_dir, u"%02d.xlsx" % n), cur_side["dec"], rows)\n    write_new(os.path.join(xlsx_dir, u"%02d.json" % n), u"{}")\n', ("dev",)),
    (u"W12 作る側が既に在る folder に書き直せる", u'    os.makedirs(xdir)\n    os.makedirs(adir)\n    out = od()', u'    os.makedirs(xdir, exist_ok=True)\n    os.makedirs(adir, exist_ok=True)\n    out = od()', ("dev",)),
    (u"W13 受ける側が既に在る folder に書き直せる", u'    reader = reader or read_zip_side\n    os.makedirs(out_dir)\n', u'    reader = reader or read_zip_side\n    os.makedirs(out_dir, exist_ok=True)\n', ("dev",)),
    (u"W14 dev が番号 4 以上も読む", u'    sub = [p for p in pairs if p[0] in DEV_NOS]\n', u'    sub = [p for p in pairs if p[0] in DEV_NOS or p[0] == 4]\n', ("dev",)),
    (u"W15 dev が記録を書く", u'    say(json.dumps(dev_summary(entries), ensure_ascii=False, indent=1))\n    return entries', u'    say(json.dumps(dev_summary(entries), ensure_ascii=False, indent=1))\n    write_new(os.path.join(tmp, u"rec.json"), u"{}")\n    return entries', ("dev",)),
    (u"W16 dev が 3 工程を通さず採点を省く", u'    entries, _names = score_folders(os.path.join(tmp, u"out"), os.path.join(tmp, u"answer"), [p[0] for p in sub])\n', u'    entries, _names = score_folders(os.path.join(tmp, u"out"), os.path.join(tmp, u"answer"), [p[0] for p in sub][:2])\n', ("dev",)),
    (u"W17 受ける側へ今年の path を渡す", u'    return dict((p[0], p[4]) for p in pairs if nos is None or p[0] in nos)', u'    return dict((p[0], p[2]) for p in pairs if nos is None or p[0] in nos)', ("dev",)),
    (u"W18 受ける側へ渡す組を番号でなく順で選ぶ", u'    return dict((p[0], p[4]) for p in pairs if nos is None or p[0] in nos)', u'    return dict((i, p[4]) for i, p in enumerate(pairs) if nos is None or p[0] in nos)', ("dev",)),
    (u"W19 採点が出力でなく作る側の読み出しを呼ぶ", u'        o = load_json(os.path.join(out_dir, u"%02d.json" % n))\n', u'        o = od([(u"番号", n), (u"受けた", receive_pair(os.path.join(os.path.dirname(out_dir), u"xlsx", u"%02d.xlsx" % n), read_zip_side(u"CUR%d" % n)))])\n', ("dev",)),
    (u"W20 採点の番号の検査を外す", u'        if a[u"番号"] != n or o[u"番号"] != n:\n            raise Stop(u"**組の番号が file の番号と違う。止める**")\n', u'', ("dev",)),
    (u"W21 read_zip_side が字の読み出しを呼ばない", u'    with zipfile.ZipFile(zip_path) as z:\n        texts = N.doc_texts(z)\n', u'    texts = []\n', ("wiring",)),
    (u"W22 read_zip_side が断りで止まらない", u'    except Refuse as exc:\n        raise Stop(u"**書類の分析が断りを出した(封に断った組の決めが無い)。止める: %s**" % exc.reason)\n', u'    except Refuse as exc:\n        raise\n', ("wiring",)),
    (u"W23 build_side が分析の戻りの書類の決めを使わない", u'    return od([("dec", dict(dec)), ("records", recs), ("stats", st)])', u'    return od([("dec", dict(start=u"2028-04-01", end=u"2029-03-31", filing=u"2029-06-30")), ("records", recs), ("stats", st)])', ("side",)),
    (u"W24 突き合わせで name の違いで止まらない", u'if x["attrs"].get("name") != a.get("name") or x["attrs"].get("contextRef") != a.get("contextRef"):', u'if x["attrs"].get("contextRef") != a.get("contextRef"):', ("side",)),
    (u"W25 突き合わせで contextRef の違いで止まらない", u'if x["attrs"].get("name") != a.get("name") or x["attrs"].get("contextRef") != a.get("contextRef"):', u'if x["attrs"].get("name") != a.get("name"):', ("side",)),
    (u"W26 数が合わない file を結んでしまう", u'        if len(allm) != len(xs):\n', u'        if len(allm) < len(xs):\n', ("side",)),
    (u"W27 突き合わせの外の fact の数を file の数にする", u'            st["ix_out"] += len(allm)\n', u'            st["ix_out"] += 1\n', ("side",)),
    (u"W28 突き合わせの外の行の中の数を数えない", u'            st["inrow_out"] += inrow\n', u'', ("side",)),
    (u"W29 行の中の数の fact を結べた file だけで数える", u'        st["inrow"] += inrow\n', u'        pass\n', ("side",)),
    (u"W30 隠しの fact も結ぶ", u'        if f["where"] == "F" and f["isnum"]:', u'        if f["isnum"]:', ("side",)),
    (u"W31 文の fact も結ぶ", u'        if f["where"] == "F" and f["isnum"]:', u'        if f["where"] == "F":', ("side",)),
    (u"W32 file の並びを名の昇順にしない", u'    for name, text in sorted(texts, key=lambda q: q[0]):\n        rows, _outside = Z.read_rows(text)', u'    for name, text in texts:\n        rows, _outside = Z.read_rows(text)', ("side",)),
    (u"W33 型の外の fact にも期の名を付ける", u'("pn", None if bad else M.period_name(x["period"][0], x["period"][1], dec)),', u'("pn", M.period_name(x["period"][0], x["period"][1], dec)),', ("side",)),
    (u"W34 期の名を相手の年の決めで付ける", u'("pn", None if bad else M.period_name(x["period"][0], x["period"][1], dec)),', u'("pn", None if bad else M.period_name(x["period"][0], x["period"][1], dict(start=u"2029-04-01", end=u"2030-03-31", filing=u"2030-06-30"))),', ("side",)),
    (u"W35 表の頭の印を行ごとでなく file ごとにする", u'            hm = marks.get(bisect.bisect_left(starts, m.start()), u"")\n', u'            hm = marks.get(0, u"")\n', ("side",)),
    (u"W36 表の頭の印を表の頭の行だけでなく全部の行で作る", u'        if Z.FACT_RE.search(m.group(0)):\n            closed.add(ser)\n        elif ser not in closed:\n            head_rows.setdefault(ser, []).append(m.group(0))', u'        head_rows.setdefault(ser, []).append(m.group(0))', ("side",)),
    (u"W37 表の頭の印の閉じる条件を外す(数の fact の後の行も頭)", u'        elif ser not in closed:\n            head_rows.setdefault(ser, []).append(m.group(0))', u'        else:\n            head_rows.setdefault(ser, []).append(m.group(0))', ("side",)),
    (u"W38 負の印を前の欄から読む", u'("neg", negative_mark(rowtext, fm.start())),', u'("neg", negative_mark(rowtext, 0)),', ("side",)),
    (u"W39 列の番号を 0 始まりにする(fact の欄をそのまま写さない)", u'recs.append(od([\n                    ("h", h), ("th", th), ("T", T), ("td", td),', u'recs.append(od([\n                    ("h", h), ("th", th), ("T", T), ("td", td - 1),', ("side",)),
    (u"W40 答えの側の区分を持ち越さない", u'("dims", tuple(tuple(d) for d in x["dims"])),', u'("dims", ()),', ("side",)),
    (u"W41 答えの側の sign を持ち越さない", u'("content", x["content"]), ("sign", x["attrs"].get("sign")), ("bad", bad)]))', u'("content", x["content"]), ("sign", None), ("bad", bad)]))', ("side",)),
    (u"W42 型の外を持ち越さない", u'("content", x["content"]), ("sign", x["attrs"].get("sign")), ("bad", bad)]))', u'("content", x["content"]), ("sign", x["attrs"].get("sign")), ("bad", False)]))', ("side",)),
    (u"Wi1 表の頭の印を前の便の head_mark で作らない", u'    return dict((ser, G.head_mark(r)) for ser, r in head_rows.items())', u'    return dict((ser, u"".join(r)) for ser, r in head_rows.items())', ("side", "import")),
    (u"Wi2 期の名を前の便の period_name で作らない", u'("pn", None if bad else M.period_name(x["period"][0], x["period"][1], dec)),', u'("pn", None if bad else u"CurrentYear"),', ("side",)),
    (u"Wi3 行の読み方を前の便の read_rows で作らない(行 0)", u'        rows, _outside = Z.read_rows(text)\n        inrow = sum', u'        rows, _outside = [], 0\n        inrow = sum', ("side", "import")),
    (u"Wi4 集計の足し算を前の便の sum_nested で作らない", u'(u"数", M.sum_nested(body) if body else od())', u'(u"数", od())', ("tot",)),
    (u"Wi5 材料の並びの sha256 を前の便の order_sha256 で作らない", u'(u"今年の側の書類の file 名の並びの sha256", W.order_sha256([d[0] for d in docs])),', u'(u"今年の側の書類の file 名の並びの sha256", u"0" * 64),', ("rec", "import")),
    (u"Wi6 値を前の便の number_value で作らない", u'        value = M.number_value(content, shift, u"-" if neg != flip else None)', u'        value = (u"-" if neg != flip else u"") + content', ("recv", "import")),
    (u"Wi7 突き合わせで答えの側の fact の戻り値を使わない(区分)", u'("target", x["target"]), ("dims", tuple(tuple(d) for d in x["dims"])),', u'("target", u"既定"), ("dims", tuple(tuple(d) for d in x["dims"])),', ("side",)),
    (u"Wi8 判定の戻り値を記録に入れない", u'    rec[u"予測の判定に要る数(XE0-1〜XE0-9。判定の 60 組だけ。当たり・外れ)"] = judged(entries)\n', u'    rec[u"予測の判定に要る数(XE0-1〜XE0-9。判定の 60 組だけ。当たり・外れ)"] = od()\n', ("rec",)),
    (u"Wi9 採点の戻り値を使わない(組の数)", u'        entries.append(score_pair(n, a[u"数"], a[u"答え"], o[u"受けた"]))', u'        entries.append(score_pair(n, a[u"数"], a[u"答え"], o[u"受けた"]))\n        entries[-1][u"D"] = 0', ("dev",)),
    (u"W43 空を持ち越さない", u'("nil", bool(x["nil"])),', u'("nil", False),', ("side",)),
)

#: 黙るのが設計どおりの変異(同値)。理由を書き、別の試験で「黙ること」を縛る
SILENT_BY_DESIGN = (
    (u"S1 空の fact にも 15 桁を見る", u'if not r["nil"] and sig_digits(r["content"]) > MAX_DIGITS', u'if sig_digits(r["content"] or u"") > MAX_DIGITS',
     u"空の fact の表示の字は空(有効数字 0 桁)なので、見ても書かない理由に当たらない(同値)。"),
    (u"S2 表の頭の印の空を字のまま書く", u'r["hmark"] or None', u'r["hmark"]',
     u"空の字のセルは openpyxl が空のセルに戻す(往復で同じ)。読む側は空を空の字に直す(同値)。"),
    (u"S3 float を repr でなく str で読む", u'decimal.Decimal(repr(abs(cell))) if isinstance(cell, float) else decimal.Decimal(abs(cell))', u'decimal.Decimal(str(abs(cell))) if isinstance(cell, float) else decimal.Decimal(abs(cell))',
     u"python3 では float の str と repr は同じ字(同値)。"),
    (u"S4 空の fact の単位の形を表示の位つきの字の表で引く", u'    form = LETTER_TO_FORM[row["unit"]] if nil else LETTER_TO_UNIT[row["unit"]][0]\n', u'    form = LETTER_TO_UNIT[row["unit"]][0]\n',
     u"2 つの逆引きは同じ字の表から作るので、どの字でも単位の形は同じ(同値)。"),
    (u"S5 単位の形を常に単位の形だけの逆引きで引く", u'    form = LETTER_TO_FORM[row["unit"]] if nil else LETTER_TO_UNIT[row["unit"]][0]\n', u'    form = LETTER_TO_FORM[row["unit"]]\n',
     u"S4 と同じ理由(同値)。"),
    (u"S6 候補が 1 つのとき最初の 1 つを sorted で取る", u'    (cand,) = e["cands"]\n    cf, default = decide_row(row, dec, e)\n', u'    cand = sorted(e["cands"])[0]\n    cf, default = decide_row(row, dec, e)\n',
     u"候補が 1 つのとき sorted の最初はその 1 つ(同値)。"),
    (u"S7 正しかった止めを決めた中身が無いときだけ止めの中身で見る", u'                if not differing_fields(res["cf"], ans):', u'                if not differing_fields(res["cf"] or res["decided"], ans) and res["decided"] is None:',
     u"守りの止めの行は決めた中身が None・止めずに決めた中身は None でないので、どちらも元と同じ(同値)。"),
)


def check_by_name(name, mod, src):
    table_ = {u"seal": seal_problems, u"pure": pure_problems, u"xlsx": xlsx_problems, u"side": side_build_problems, u"recv": recv_problems, u"score": score_problems, u"tot": tot_problems,
              u"rec": rec_problems, u"dev": dev_problems, u"entry": entry_wiring_problems, u"iso": iso_problems, u"wiring": wiring_problems}
    if name == u"iso":
        return iso_problems(mod) + iso_ast_problems(src)
    if name in table_:
        return table_[name](mod)
    if name == u"import":
        return import_problems(src)
    raise AssertionError(name)


ALL_CHECKS = (u"seal", u"pure", u"xlsx", u"side", u"recv", u"score", u"tot", u"rec", u"dev", u"entry", u"iso", u"wiring", u"import")


def run_mutants(table_=MUTANTS):
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
        res = []
        for c in checks:
            got = guard(check_by_name, c, mod, src)
            res.append((c, bool(got)))
            if got and len(got) == 1 and got[0] in (u"例外: NameError", u"例外: SyntaxError", u"例外: IndentationError"):
                out.append((name, [(c, False)], u"変異が自分の誤りで赤になった: %s" % got[0]))
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
                         (u"番号 1・2・3 が訓練、番号 4〜63 が判定の 60 組", u"番号 1・2・3 が訓練、番号 4〜63 が判定の 59 組"),
                         (u"決めて全部同じ ÷ D は **74.0% 以上**", u"決めて全部同じ ÷ D は **75.0% 以上**"), (u"「符号だけ違う」は **30 fact 以下**", u"「符号だけ違う」は **31 fact 以下**"),
                         (u"止めた ÷ D は **16.0% 以上 26.0% 以下**", u"止めた ÷ D は **16.0% 以上 27.0% 以下**"), (u"「正しかった止め」は **40% 以上 65% 以下**", u"「正しかった止め」は **41% 以上 65% 以下**"),
                         (u"合わせて **1 fact 以上で、D の 2.0% 以下**", u"合わせて **1 fact 以上で、D の 3.0% 以下**"), (u"合わせて **行の中の数の fact の 1.0% 以下**", u"合わせて **行の中の数の fact の 2.0% 以下**"),
                         (u"60 本のうち **35 本以上**", u"60 本のうち **36 本以上**"), (u"95% 以上の書類は **2 本以下**", u"95% 以上の書類は **3 本以下**"),
                         (u"通貨:JPY × 0 → 「円」", u"通貨:JPY × 1 → 「円」"), (u"純数 × 0 → 「数」、× −2 → 「％」", u"純数 × 0 → 「数」、× −3 → 「％」"),
                         (u"「△」「▲」「-」「－」「−」のどれか", u"「△」「▲」「-」「－」のどれか"), (u"有効数字が 15 桁を超える", u"有効数字が 16 桁を超える"),
                         (u"**去年の符号の向きが 1 つも無い(去年は空だった)ときは「順」とする。**", u"去年の符号の向きが 1 つも無いときは「逆」とする。"),
                         (u"行の中の数の fact 3434・決めて全部同じ 2636・決めたが違う 0・止めた 669", u"行の中の数の fact 3434・決めて全部同じ 2637・決めたが違う 0・止めた 669"),
                         (u"答えは提出された書類そのもので、提出された書類の誤りは見ていない。", u"答えは提出された書類そのものである。")):
            self.assertGreaterEqual(seal.count(old), 1, old)
            self.assertNotEqual([], seal_problems(seal=seal.replace(old, new)), old)

    def test_a_4_engine_is_zero_lines_from_the_seal_commit(self):
        self.assertEqual([], engine_zero_problems())

    def test_a_5_the_boundary_import_list_is_not_widened(self):
        p = os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py")
        with io.open(p, encoding="utf-8") as fh:
            body = fh.read()
        self.assertNotIn(u"company_excel", body)
        self.assertNotIn(u"xbrl_company", body)


class OrderTest(unittest.TestCase):
    def test_d_1_the_real_history_has_the_seal_before_the_script_and_the_gate(self):
        u"""script・門のどちらかが未 commit なら赤(足した commit が無い。skip にしない)。両方 commit された後で初めて緑。"""
        self.assertEqual([], order_of())

    def test_d_2_the_order_check_lists_the_script_and_the_gate_and_not_the_record(self):
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, rel)) for rel in ORDER_FILES))
        self.assertNotIn(RECORD_REL, ORDER_FILES)


class PartsTest(unittest.TestCase):
    def test_b_1_marks_digits_keys_units_exclusions_cells_and_bounds(self):
        self.assertEqual([], pure_problems())

    def test_b_2_the_xlsx_round_trip_with_the_real_openpyxl(self):
        self.assertEqual([], xlsx_problems())

    def test_b_3_the_side_reading_joins_text_and_answer_facts_one_to_one(self):
        self.assertEqual([], side_build_problems())

    def test_b_4_the_receiving_side_decides_and_stops_by_hand_in_every_order(self):
        self.assertEqual([], recv_problems())

    def test_b_5_the_scoring_by_hand(self):
        self.assertEqual([], score_problems())

    def test_b_6_totals_judgments_bounds_and_the_flag(self):
        self.assertEqual([], tot_problems())

    def test_b_7_the_hand_scene_is_not_nearby_numbers(self):
        u"""手で決めた値が互いに違う(近くの数と同じにしない): S1 の主な数。"""
        h = HAND_S1_ENTRY
        main = [h[u"D"], h[u"決めて全部同じ"], h[u"決めたが違う"], h[u"止めた"], h[u"無くなった行"]]
        self.assertEqual(len(set(main)), len(main), main)
        self.assertEqual(h[u"決めて全部同じ"] + h[u"決めたが違う"] + h[u"止めた"], h[u"D"])
        self.assertEqual(sum(h[u"止めた理由ごと"].values()), h[u"止めた"])
        self.assertEqual(len(S1_ROWS), 31)
        self.assertEqual(sum(1 for r in S1_ROWS if r[0]), h[u"止めた"])
        self.assertEqual(sum(1 for r in S1_ROWS if not r[0] and r[1]), h[u"決めたが違う"])

    def test_b_8_the_record_shape_checks_stop_every_broken_relation(self):
        self.assertEqual([], entry_shape_problems())


class RecordTest(unittest.TestCase):
    def test_c_1_the_forbidden_checks_stop_planted_content(self):
        self.assertEqual([], clean_problems())

    def test_c_2_record_build_check_and_write_without_the_real_cache(self):
        self.assertEqual([], rec_problems())

    def test_c_3_three_stages_through_separate_folders_with_made_up_pairs(self):
        self.assertEqual([], dev_problems())

    def test_c_5_the_entry_points_pass_arguments_in_order_through_the_real_main_score_run_and_check(self):
        self.assertEqual([], entry_wiring_problems())

    def test_c_4_the_real_record_when_present_is_clean(self):
        u"""記録は本番の走りの後に書かれる。在れば中身を見て、無ければ見ない(skip にしない)。"""
        p = os.path.join(ROOT, RECORD_REL)
        if os.path.exists(p):
            rec = json.loads(read(RECORD_REL), object_pairs_hook=od)
            MS.check(root=ROOT, say=lambda *a: None)
            self.assertEqual(MS.SEAL_COMMIT, rec[u"封の commit"])
            self.assertEqual(63, rec[u"材料"][u"組の数"])
            self.assertEqual(sha_of(SCRIPT_REL), rec[u"この script の sha256"])
        else:
            self.assertFalse(os.path.exists(p))


class IsolationTest(unittest.TestCase):
    def test_g_1_the_receiving_functions_never_name_the_answer_or_this_years_zip(self):
        self.assertEqual([], iso_ast_problems())

    def test_g_2_the_isolation_check_sees_planted_violations(self):
        base = read(SCRIPT_REL)
        self.assertNotEqual([], iso_ast_problems(base.replace(u"def receive_pair(xlsx_path, prior_side):", u"def receive_pair(xlsx_path, prior_side, answer_dir):")))
        self.assertNotEqual([], iso_ast_problems(base.replace(u"def receive_pair(xlsx_path, prior_side):", u"def receive_pair(xlsx_path, prior_side, cur_zip=None):")))
        self.assertNotEqual([], iso_ast_problems(base.replace(u"    dec, rows = read_xlsx(xlsx_path)\n    tab = prior_table(prior_side)\n", u"    dec, rows = read_xlsx(xlsx_path)\n    load_json(u'x')\n    tab = prior_table(prior_side)\n")))
        self.assertNotEqual([], iso_ast_problems(base.replace(u"def prior_table(side):\n", u"def prior_table(side):\n    make_pairs(1, 2)\n")))
        self.assertNotEqual([], iso_ast_problems(base.replace(u"def read_amount(cell, fmt):\n", u"def read_amount(cell, fmt):\n    s = u'answer.json'\n")))

    def test_g_3_the_receiving_side_works_where_this_years_zip_and_the_answer_do_not_exist(self):
        self.assertEqual([], iso_problems())


class WiringTest(unittest.TestCase):
    def test_e_1_imports_previous_script_calls_and_no_copies(self):
        self.assertEqual([], import_problems())

    def test_e_2_the_import_check_sees_planted_violations(self):
        base = read(SCRIPT_REL)
        self.assertNotEqual([], import_problems(base + u"\nimport socket\n"))
        self.assertNotEqual([], import_problems(base + u"\nimport urllib.request\n"))
        self.assertNotEqual([], import_problems(base + u"\nimport subprocess\n"))
        self.assertNotEqual([], import_problems(base + u"\nimport tempfile\n"))
        self.assertNotEqual([], import_problems(base + u"\nfrom adapters.xbrl import instance\n"))
        self.assertNotEqual([], import_problems(base + u"\nX = os.environ.get('A')\n"))
        self.assertNotEqual([], import_problems(base + u"\ndef analyze(a):\n    return None\n"))
        self.assertNotEqual([], import_problems(base + u"\ndef head_mark(a):\n    return None\n"))
        self.assertNotEqual([], import_problems(base + u"\ndef read_rows(a):\n    return None\n"))
        self.assertNotEqual([], import_problems(base + u"\ndef mutate(x):\n    return x\n"))
        self.assertNotEqual([], import_problems(base + u"\nX = 'run_doc('\n"))
        self.assertNotEqual([], import_problems(base + u"\nM.derive_folder(1, 2)\n"))
        self.assertNotEqual([], import_problems(base + u"\nM.process_doc(1, 2)\n"))
        self.assertNotEqual([], import_problems(base.replace(u"M.number_value(", u"number_value(")))
        self.assertNotEqual([], import_problems(base.replace(u"G.head_mark(", u"head_mark(")))
        self.assertNotEqual([], import_problems(base.replace(u"Z.read_rows(", u"read_rows(")))
        self.assertNotEqual([], import_problems(base.replace(u"M.period_name(", u"period_name(")))
        self.assertNotEqual([], import_problems(base.replace(u'"_xe0_prior_year_fact_guard_2026_11_22"', u'"xbrl_prior_year_fact_guard"')))

    def test_e_3_the_gate_does_not_use_the_reserved_names(self):
        self.assertEqual([], reserved_problems())
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("ENGINE_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rel="g.py", base=d))

    def test_e_4_the_script_leaves_sys_modules_as_it_found_them_except_its_own_sibling_names(self):
        before = dict(sys.modules)
        mod = load_module(SCRIPT_REL, "xbrl_company_excel_script_for_sysmodules_check")
        self.assertEqual([], [k for k, v in before.items() if sys.modules.get(k) is not v])
        for nm in SIBLING_NAMES:
            self.assertIn(nm, sys.modules)
        self.assertIs(mod.M, sys.modules[SIBLING_NAMES[0]])
        self.assertIs(mod.G, sys.modules[SIBLING_NAMES[1]])
        self.assertIs(mod.W, mod.M.W)
        self.assertIs(mod.Z, mod.G.Z)
        self.assertIs(mod.Refuse, mod.M.Refuse)
        del mod

    def test_e_5_loading_the_previous_scripts_and_this_one_in_any_order_works(self):
        self.assertEqual([], order_import_problems())

    def test_e_6_read_zip_side_calls_the_previous_functions_in_order_and_uses_the_result(self):
        self.assertEqual([], wiring_problems())

    def test_e_7_the_default_places_are_outside_the_repo_and_the_gate_never_opens_them(self):
        top = os.path.realpath(REPO)
        for p in (MS.DOCS_DIR, MS.PRIOR_DIR):
            self.assertFalse(os.path.realpath(p).startswith(top + os.sep), p)
        src = read(GATE_REL)
        for m in re.finditer(r"ms\.(score_run|check|dev_run|make_folders|receive_folder)\(([^)]*)\)", src):
            self.assertTrue(re.search(r"\bd\b|docs|DOCS|rec_path|prior|None|pairs|root|tmp|xdir|reader|fake_pairs|\*\*kw|xlsx|out|7", m.group(2)), m.group(0))

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
        self.assertEqual([], silent)                                                      # 黙った変異・変異自身の誤り(NameError など)で赤になった変異は無い
        self.assertEqual(len(MUTANTS), len(results))
        self.assertEqual([], [n for n, res, _w in results if not res])                   # 検査を 1 つも持たない変異は無い
        self.assertGreaterEqual(len(MUTANTS), 300)

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
            for c in (u"pure", u"xlsx", u"side", u"recv", u"score", u"tot", u"rec", u"dev", u"entry", u"iso", u"wiring"):
                self.assertEqual([], check_by_name(c, mod, base.replace(old, new)), (name, c))

    def test_f_4_the_mutant_names_are_unique_and_the_predicted_checks_exist(self):
        names = [m[0] for m in MUTANTS]
        self.assertEqual(len(names), len(set(names)))
        self.assertTrue(all(c in ALL_CHECKS for m in MUTANTS for c in m[3]))


if __name__ == "__main__":
    unittest.main()
