# -*- coding: utf-8 -*-
"""結果の門: 封 docs/XBRL_TANSHIN_SELF_SEAL_2026-11-14.md §2 の 6(TSS ― 決算短信の概況の文を、同じ短信の添付の財務諸表で確かめる便)。

封の門 ``test_xbrl_tanshin_self_seal.py`` の次の段。**追跡されている記録 4 つ・封・結果の文書だけを読む**(cache の材料が無い機械でも緑。材料から測り直す試験だけ環境変数
``AUDIT_CORE_TSS_REMEASURE=1`` で走る)。

縛るもの(検査は「問題の一覧を返す関数」。実物で空・変異で空でない)
 a 母集団(封の表 400 行 = 置いた記録 = 判定の記録。群・様式の数は字で留める)  b 順序(commit の順。未 commit は赤)  c engine 0 行・script の sha256・記録の header
 d 集計を行から数え直す(script の ``block`` ・ ``tally`` は呼ばない)  e 留める字  f 標本 120 行を門の中で引き直す  g 型  h 型の細目  i 記録に文も会社名も証券コードも無い
 j 結果の文書の 8 つの塊を記録から作り直して 1 行ずつ照らす  k 予測の判定  l 切り出しの宿題  m 材料から測り直す(環境変数つき)
この file は docID の形の字を持たない。
"""
import collections
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import random
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, os.path.join(ROOT, "measure"))


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


SG = load_module("tests/measure/test_xbrl_tanshin_self_seal.py", "tanshin_self_seal_gate_for_tanshin_self_result_gate")      # 封の門の部品。門としては走らせない
PR = SG.PR
MS = SG.MS
ST = MS.ST
TS = MS.TS

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
STAGE_REL = SG.STAGE_REL
SCRIPT_REL = SG.SCRIPT_REL
GATE_REL = "tests/measure/test_xbrl_tanshin_self_result.py"
DOC_REL = "docs/XBRL_TANSHIN_SELF_RESULT_2026-11-14.md"
REC_DIR = "fixtures/xbrl/tanshin_self/"
POP_REL = REC_DIR + "population_2026-11-14.json"
STATES_REL = REC_DIR + "states_2026-11-14.json"
TYPES_REL = REC_DIR + "vm_types_2026-11-14.json"
SUB_REL = REC_DIR + "vm_types_subreading_2026-11-14.json"
RECORD_RELS = (POP_REL, STATES_REL, TYPES_REL, SUB_REL)
SCRIPT_ADDED_COMMIT = "ea3b036c"                       # script 2 本を足した commit(この commit から script は 0 行)
NOT_GATED = PR.NOT_GATED

STATES = (u"GROUNDED", u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND")
G, VM, UNV, PNF = STATES
PERIODS5 = (u"CurrentYear", u"Prior1Year", u"Prior2Year", u"他", u"なし")
FAMILIES = (u"%", u"円族", u"他")
GROUPS = (u"甲", u"乙", u"丙")
WHYS = (u"member なし", u"decode", u"始まりなし", u"終わりなし")
#: 字で留める数(封 §0-1 の 2・3)
GROUP_COUNTS = collections.OrderedDict([(u"甲", 50), (u"乙", 200), (u"丙", 150)])
KIND_COUNTS = collections.OrderedDict([(u"acedifsm", 43), (u"acedjpsm", 203), (u"anedjpsm", 4), (u"scedifsy", 29), (u"scedjpsm", 7), (u"scedjpsy", 110), (u"snedjpsy", 4)])
#: 結果の文書の 8 つの塊の名前(順)
BLOCK_NAMES = (u"pred", u"groups", u"kinds", u"books", u"reasons", u"vm", u"types", u"sub")
#: 封 §3 から読んだ幅(字で留める。封の字が変われば赤)
BOUNDS_PIN = collections.OrderedDict([(u"S-8", (66, 102)), (u"S-9", (0, 4)), (u"S-10", (0, 12))])
FORBIDDEN_WORDS = (u"精度", u"ハルシネーション", u"証明した", u"LLM より正確", u"世界で 1 社")
DOCID_RE = re.compile(r"S100[0-9A-Z]{4}")
TDNET_RE = re.compile(r"0812\d{14}")
CODE_RE = re.compile(r"(?<![0-9A-Za-z\-])\d{3}[0-9A-Z](?![0-9A-Za-z\-])")              # 4 桁 + 英数 1 字までの証券コードの形(前後が英数・- でないもの)
POINTER_RE = re.compile(r"xbrl:|jppfs|jpcrp|jpdei|_cor:|@(Current|Prior)|formula:")
COMPANY_WORDS = (u"株式会社", u"有限会社", u"合同会社", u"㈱", u"(株)")
REASON_RE = re.compile(r"^[a-z_]+(\([A-Za-z0-9_ \-]+\))?$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
JA_RE = re.compile(u"[぀-ヿ一-鿿]")
FORBIDDEN_KEYS = tuple(TS.RUN.FORBIDDEN_KEYS) + (u"pointers", u"pointer", u"要素", u"element", u"context", u"label", u"会社名", u"subject", u"span", u"value", u"text", u"文")
LONG_JA = 40                                           # 日本語を含む文字列がこの長さ以上なら「文」とみなし、留めた字の集合に無ければ赤

BOOK_KEYS = (u"#", u"群", u"様式の種類", u"ZIP の sha256", u"切り出し", u"理由", u"見出しの番号", u"字数", u"入れた iXBRL の file の数", u"fact の数", u"claim", u"対応", u"行")
ROW_COLUMNS = (u"文の番号", u"位置", u"state", u"reason", u"pointer の期", u"formula の有無", u"単位の族", u"両期の fact を引く a−b", u"span に % を含む")
BLOCK_KEYS = (u"本", u"切れた", u"切れない", u"切れない理由", u"見出しの番号の本数", u"字数の合計", u"入れた iXBRL の file の数の合計", u"fact の数の合計", u"claim", u"4 state", u"reason",
              u"VALUE_MISMATCH の内訳", u"切れた本のうち claim が 0 の本", u"切れた本のうち GROUNDED が 0 の本", u"VALUE_MISMATCH が 1 以上の本", u"claim と raw の並びが対応しなかった本")
VM_KEYS = (u"行", u"導出(formula)", u"直接", u"% の数", u"円族の数", u"両期の fact を引く a−b(円)", u"単位の族が %", u"単位の族が円族", u"単位の族が他", u"pointer の期")
TALLY_KEYS = (u"群", u"A(甲 + 乙)", u"B(丙)", u"様式の種類")
TYPE_LETTERS = u"アイウエオカキクケ"
SUB_KEYS = (u"イ1", u"イ2", u"イ3", u"オ1", u"オ2", u"カ1", u"カ2", u"カ3", u"ケ1")
SUB_TYPES = u"イオカケ"
TYPED_BY = u"司令塔(AI の席)。人は読んでいない"
STATES_STEP = u"TSS(決算短信の概況の文を同じ短信の添付の財務諸表で確かめる)― 400 本の切り出し・包み直し・判定(0 USD・通信なし)"
POP_STEP = u"TSS(決算短信の概況の文を同じ短信の添付の財務諸表で確かめる)― 材料 400 本の置き場への写し(0 USD・通信なし)"
TYPES_STEP = u"TSS ― A の VALUE_MISMATCH の標本の型分け(0 USD)"
SUB_STEP = u"TSS ― 標本の型の細目(封に無い補足。2026-11-14。0 USD)"
TYPES_BLIND = u"盲検ではない(封の予測を知ったうえで付けた)。(ク) は候補で、紙面で確かめていない"
SUB_BLIND = u"盲検ではない(封の予測と型の集計を知ったうえで付けた)"
SUB_NOTE_PIN = u"封 §2 の 3 つの記録(population・states・vm_types)には無い"
SUB_HOW = u"司令塔が読むための紙を読み直して手で付けた。細目の無い型((ア)・(ウ)・(エ)・(キ)・(ク))の行は持たない"
SAMPLE_RULE_POP = u"A(甲 + 乙)の VALUE_MISMATCH の行を、# の順・文の番号の順・位置の順に並べた"
SAMPLE_RULE_HOW = u"random.Random(種).sample(range(行の数), 標本の数) を番号の順に。行の数が標本の数に満たなければ全部"
CACHE_PLACE = u"~/.cache/audit-core/tanshin-self-2026-11-14"
CUT_PIN = collections.OrderedDict([
    (u"member", u"XBRLData/Attachment/qualitative.htm"),
    (u"始まりの規則", u"^1\\s*\\.\\s*(経営成績等の概況|当中間決算に関する定性的情報|当四半期決算に関する定性的情報)"),
    (u"終わりの規則", u"^2\\s*\\.\\s*[^\\d\\s]"),
    (u"目次の印(行に在れば始まりにしない)", [u"...", u"・・"]),
    (u"見出しの番号", [u"経営成績等の概況", u"当中間決算に関する定性的情報", u"当四半期決算に関する定性的情報"]),
    (u"NFKC", True),
    (u"行にする関数", u"2026-11-09 の便の html_to_lines(呼ぶ)")])
WRAP_PIN = collections.OrderedDict([
    (u"入れる member", u"XBRLData/Attachment/ の下で file 名が -ixbrl.htm で終わるもの(元の member 名の順)"),
    (u"新しい名前", u"XBRL/PublicDoc/<file 名の末尾を _ixbrl.htm に替えたもの>"),
    (u"文の member", u"XBRL/PublicDoc/zz_overview_ixbrl.htm"),
    (u"文の要素", u"経営分析の節の TextBlock(要素名は script の TEXTBLOCK_NAME。長い英字なので記録には書かない)"),
    (u"サマリー", u"入れない"),
    (u"包んだ ZIP", u"memory の中だけ(どこにも書かない)")])
LIMITS_PIN = (
    u"材料は英文短信を出している会社から引いた 400 本で、上場会社全体の標本ではない(封 §6)",
    u"切れない本は測れていない(見出しの書き方の違い。規則は広げない)",
    u"中間(B)は engine が中間の期(InterimInstant・InterimDuration 等)を当期・前期として読めないので、「値が違う」が出ない。B の数は限界の記録で成績ではない",
    u"文と表が同じ誤りを共有していれば、この照合では見えない(同じ文書の中の照合)",
    u"engine が見るのは添付の財務諸表の fact だけ。サマリーの数(予想・配当など)は入れていない",
    u"NFKC を掛けた文を測っている(原文の全角・半角の違いは見ていない)",
    u"行は [文の番号, 位置, state, reason, pointer の期, formula の有無, 単位の族, 両期の fact を引く a−b, span に % を含む] だけで、文・span・値・要素名は持たない")
PRED_S1_ACTUAL = u"表と一致した ZIP %d / %d・ほかの cache の一覧(比べた folder %d)は前後で%s"
S7_ACTUAL = u"(記録に在るのは 1 回目だけ。2 回目との照らしは司令塔。§3-1)"
S7_JUDGE = u"司令塔が比べた"


# ======================================================================================================
# 読み込み・小さい道具
def read(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def sha256_rel(rel):
    with io.open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def jload(rel):
    return json.loads(read(rel))


def fresh_records():
    u"""記録 4 つを file から新しく読んだ写し(変異は毎回この関数で新しい写しを作って 1 か所だけ変える)。"""
    return collections.OrderedDict([("pop", jload(POP_REL)), ("states", jload(STATES_REL)), ("types", jload(TYPES_REL)), ("sub", jload(SUB_REL))])


def guard(fn, *a, **k):
    try:
        return fn(*a, **k)
    except BaseException as exc:                   # noqa: BLE001  変異で落ちた検査は「問題」として数える
        return [u"例外: %s" % type(exc).__name__]


def is_int(x):
    return type(x) is int


def fmt(n):
    return u"{:,}".format(n)


def pct(a, b):
    return u"%.1f%%" % (100.0 * a / b) if b else u"-"


def tmpdir():
    return tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR"))


def tags(problems):
    return u"\n".join(problems)


# ======================================================================================================
# j・k. 結果の文書(8 つの塊を記録から作り直す)と予測の判定
def range_judge(n, lo, hi):
    return u"当たり" if lo <= n <= hi else u"外れ"


def pred_parts(tc, sc, bounds):
    u"""S-8・S-9・S-10 の (実測の字, 判定)。tc = 型の集計・sc = 細目の集計・bounds = 封から読んだ幅。"""
    lo, hi = bounds[u"S-8"]
    a, i, i1, total = tc[u"ア"], tc[u"イ"], sc[u"イ1"], sum(tc.values())
    x, y = a + i, a + i1
    x_in, y_in = lo <= x <= hi, lo <= y <= hi
    actual8 = u"(ア) %d + (イ) %d = %d 行(%s)。(イ) を封の字のとおりの行(細目 イ1)だけにすると %d + %d = %d 行(%s)" % (a, i, x, pct(x, total), a, i1, y, pct(y, total))
    if x_in and y_in:
        judge8 = u"当たり"
    elif not x_in and not y_in:
        judge8 = u"外れ"
    else:
        judge8 = u"読みで割れた(型の記録では幅の%s・封の字のとおりでは幅の%s)" % (u"中" if x_in else u"外", u"中" if y_in else u"外")
    return collections.OrderedDict([
        (u"S-8", (actual8, judge8)),
        (u"S-9", (u"%d 行" % tc[u"ク"], range_judge(tc[u"ク"], *bounds[u"S-9"]))),
        (u"S-10", (u"%d 行" % tc[u"ケ"], range_judge(tc[u"ケ"], *bounds[u"S-10"])))])


def pred_lines(R, seal):
    cells = seal_pred_cells(seal)
    if list(cells.keys()) != [u"S-%d" % i for i in range(1, 11)]:
        raise ValueError(u"封 §3 が S-1〜S-10 でない")
    pop, agg = R["pop"], R["states"][u"集計"]
    a, b = agg[u"A(甲 + 乙)"], agg[u"B(丙)"]
    bounds = seal_bounds(cells)
    parts = pred_parts(R["types"][u"型の集計"], R["sub"][u"細目の集計"], bounds)
    c = pop[u"ほかの cache の前後"]
    rows = collections.OrderedDict()
    s1_ok = pop[u"表と一致した ZIP"] == 400 and c[u"変化なし"] is True
    rows[u"S-1"] = (PRED_S1_ACTUAL % (pop[u"表と一致した ZIP"], len(pop[u"行"]), c[u"比べた folder の数"], u"同じ" if c[u"変化なし"] else u"違う"), u"当たり" if s1_ok else u"外れ")
    why_start = a[u"切れない理由"][u"始まりなし"] + b[u"切れない理由"][u"始まりなし"]
    not_cut = a[u"切れない"] + b[u"切れない"]
    v2 = [a[u"切れた"], a[u"切れない"], b[u"切れた"], b[u"切れない"], why_start]
    rows[u"S-2"] = (u"A %d / %d、B %d / %d。切れない %d 本のうち「始まりなし」%d" % (a[u"切れた"], a[u"切れない"], b[u"切れた"], b[u"切れない"], not_cut, why_start),
                    u"当たり" if v2 == nums_of(cells[u"S-2"][1]) and why_start == not_cut else u"外れ")
    v3 = [a[u"字数の合計"], b[u"字数の合計"]]
    rows[u"S-3"] = (u"%s、%s" % (fmt(v3[0]), fmt(v3[1])), u"当たり" if v3 == nums_of(cells[u"S-3"][1]) else u"外れ")
    for sid, blk in ((u"S-4", a), (u"S-5", b)):
        s = blk[u"4 state"]
        v = [blk[u"claim"], s[G], s[VM], s[UNV], s[PNF]]
        rows[sid] = (u"%s = %s / %s / %s / %s" % tuple(fmt(x) for x in v), u"当たり" if v == nums_of(cells[sid][1]) else u"外れ")
    v6 = [a[u"VALUE_MISMATCH の内訳"][u"% の数"], a[u"VALUE_MISMATCH の内訳"][u"導出(formula)"], a[u"VALUE_MISMATCH が 1 以上の本"]]
    rows[u"S-6"] = (u"%s / %s。%d 本" % (fmt(v6[0]), fmt(v6[1]), v6[2]), u"当たり" if v6 == nums_of(cells[u"S-6"][1]) else u"外れ")
    rows[u"S-7"] = (S7_ACTUAL, S7_JUDGE)
    for k in (u"S-8", u"S-9", u"S-10"):
        rows[k] = parts[k]
    lines = [u"| # | 欄 | 予測(封) | 実測 | 判定 |", u"|---|---|---|---|---|"]
    for k in rows:
        lines.append(u"| %s | %s | %s | %s | %s |" % (k, cells[k][0], cells[k][1], rows[k][0], rows[k][1]))
    return lines


SERIES_HEAD = u"| %s | 本 | 切れた | 切れない | 概況の字数の合計 | fact の数の合計 | 数の claim | GROUNDED | VALUE_MISMATCH | UNVERIFIABLE | POINTER_NOT_FOUND | GROUNDED / claim |"


def _series_row(name, b):
    s = b[u"4 state"]
    return u"| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
        name, fmt(b[u"本"]), fmt(b[u"切れた"]), fmt(b[u"切れない"]), fmt(b[u"字数の合計"]), fmt(b[u"fact の数の合計"]), fmt(b[u"claim"]),
        fmt(s[G]), fmt(s[VM]), fmt(s[UNV]), fmt(s[PNF]), pct(s[G], b[u"claim"]))


def _sep(n):
    return u"|" + u"---|" * n


def build_blocks(R, seal):
    agg = R["states"][u"集計"]
    grp = agg[u"群"]
    named = [(u"甲(通期)", grp[u"甲"]), (u"乙(通期)", grp[u"乙"]), (u"A(甲 + 乙)", agg[u"A(甲 + 乙)"]), (u"B(丙・中間)", agg[u"B(丙)"])]
    blocks = collections.OrderedDict()
    blocks[u"pred"] = pred_lines(R, seal)
    blocks[u"groups"] = [SERIES_HEAD % u"群", _sep(12)] + [_series_row(n, b) for n, b in named]
    blocks[u"kinds"] = [SERIES_HEAD % u"様式の種類", _sep(12)] + [_series_row(k, agg[u"様式の種類"][k]) for k in sorted(agg[u"様式の種類"])]
    lines = [u"| 群 | 切れた本 | claim が 0 の本 | GROUNDED が 0 の本 | VALUE_MISMATCH が 1 以上の本 | 見出しの番号 0 / 1 / 2 の本 |", _sep(6)]
    for n, b in named:
        h = b[u"見出しの番号の本数"]
        lines.append(u"| %s | %s | %s | %s | %s | %s |" % (n, fmt(b[u"切れた"]), fmt(b[u"切れた本のうち claim が 0 の本"]), fmt(b[u"切れた本のうち GROUNDED が 0 の本"]),
                                                     fmt(b[u"VALUE_MISMATCH が 1 以上の本"]), u" / ".join(fmt(h[k]) for k in (u"0", u"1", u"2"))))
    blocks[u"books"] = lines
    ra, rb = agg[u"A(甲 + 乙)"][u"reason"], agg[u"B(丙)"][u"reason"]
    lines = [u"| state | reason | A | B |", _sep(4)]
    for s in (UNV, PNF):
        for k in sorted(set(ra[s]) | set(rb[s])):
            lines.append(u"| %s | %s | %s | %s |" % (s, k, fmt(ra[s].get(k, 0)), fmt(rb[s].get(k, 0))))
    blocks[u"reasons"] = lines
    lines = [u"| 群 | VALUE_MISMATCH の行 | 導出(formula) | 直接 | span に % を含む | span に % を含まない | 両期の fact を引く a−b(円) | 単位の族が % | 単位の族が円族 | 単位の族が他 | pointer の期 CurrentYear | pointer の期 Prior1Year |", _sep(12)]
    for n, b in named[:3]:
        v = b[u"VALUE_MISMATCH の内訳"]
        p = v[u"pointer の期"]
        lines.append(u"| %s | %s |" % (n, u" | ".join(fmt(x) for x in (v[u"行"], v[u"導出(formula)"], v[u"直接"], v[u"% の数"], v[u"円族の数"], v[u"両期の fact を引く a−b(円)"],
                                                              v[u"単位の族が %"], v[u"単位の族が円族"], v[u"単位の族が他"], p[u"CurrentYear"], p[u"Prior1Year"]))))
    blocks[u"vm"] = lines
    tc, tt = R["types"][u"型の集計"], R["types"][u"型の字"]
    total = sum(tc.values())
    lines = [u"| 型 | 封の字 | 行 | 割合(120 行のうち) |", _sep(4)]
    for t in tt:
        lines.append(u"| (%s) | %s | %s | %s |" % (t, tt[t], fmt(tc[t]), pct(tc[t], total)))
    blocks[u"types"] = lines
    sc, st_ = R["sub"][u"細目の集計"], R["sub"][u"細目の字"]
    lines = [u"| 細目 | 型 | 細目の字 | 行 |", _sep(4)]
    for k in st_:
        lines.append(u"| %s | (%s) | %s | %s |" % (k, k[0], st_[k], fmt(sc[k])))
    blocks[u"sub"] = lines
    return blocks


def doc_blocks(doc):
    return collections.OrderedDict((m.group(1), m.group(2).split(u"\n")) for m in re.finditer(r"<!-- 門:start (\w+) -->\n(.*?)\n<!-- 門:end -->", doc, re.S))


def doc_problems(doc, R, seal):
    out = []
    names = re.findall(r"<!-- 門:start (\w+) -->", doc)
    if names != list(BLOCK_NAMES) or doc.count(u"<!-- 門:end -->") != len(BLOCK_NAMES):
        out.append(u"文書: 塊の名前・数が 8 つ(pred・groups・kinds・books・reasons・vm・types・sub)の順でない")
    want = build_blocks(R, seal)
    got = doc_blocks(doc)
    for k, lines in want.items():
        if k not in got:
            out.append(u"文書: 塊 %s が欠けている" % k)
        elif got[k] != lines:
            n = [i + 1 for i, (x, y) in enumerate(zip(got[k], lines)) if x != y]
            out.append(u"文書: 塊 %s が記録から作り直した表と違う(行の数 %d / %d・違う行 %s)" % (k, len(got[k]), len(lines), n[:5]))
    for k in got:
        if k not in want:
            out.append(u"文書: 知らない名前の塊 %s" % k)
    if DOCID_RE.search(doc):
        out.append(u"文書: docID の形の字がある")
    if TDNET_RE.search(doc):
        out.append(u"文書: TDnet の番号の形の字がある")
    for w in FORBIDDEN_WORDS:
        if w in doc:
            out.append(u"文書: 禁止語 %s" % w)
    out += [u"文書: 散文の数に【門なし】が無い(行 %d)" % ln for ln, _t in PR.prose_problems(doc)]
    for need in (os.path.basename(SEAL_REL), SEAL_COMMIT_SHORT, GATE_REL) + tuple(os.path.basename(r) for r in RECORD_RELS):
        if need not in doc:
            out.append(u"文書: %s を言っていない" % need)
    return out


# ======================================================================================================
# l. 切り出しの宿題
def cut_wins_problems(fn):
    u"""始まりの見出しに当たる行が目次の印なしで 2 行続くとき、後の行が始まりになる(script の今の振る舞い)。"""
    out = []
    lines = [u"前書き", u"1.経営成績等の概況", u"1.当中間決算に関する定性的情報", u"本文の行", u"2.次の節", u"2.さらに次"]
    text, head, why = fn(lines)
    if (text, head, why) != (u"1.当中間決算に関する定性的情報\n本文の行", 1, None):
        out.append(u"切り出し: 見出しが 2 行続くとき後の行が始まりにならない: %r" % ((text, head, why),))
    text, head, why = fn([u"1.経営成績等の概況 ......... 2", u"1.経営成績等の概況", u"甲", u"1.経営成績等の概況", u"乙", u"2.次"])
    if (text, head, why) != (u"1.経営成績等の概況\n乙", 0, None):
        out.append(u"切り出し: 同じ見出しが 2 行続くとき後の行が始まりにならない: %r" % ((text, head, why),))
    text, head, why = fn([u"1.経営成績等の概況", u"本文", u"1.当中間決算に関する定性的情報・・・2", u"2.次"])
    if (text, head, why) != (u"1.経営成績等の概況\n本文\n1.当中間決算に関する定性的情報・・・2", 0, None):
        out.append(u"切り出し: 目次の印を持つ行が始まりを奪った: %r" % ((text, head, why),))
    return out


# ======================================================================================================
# 留める字(続き)・封の読み・a〜i の検査
SUB_NOTE = u"封 §2 の 3 つの記録(population・states・vm_types)には無い。型の記録を書いた後に、(イ)・(オ)・(カ)・(ケ) の行へ細目を足した。型の記録は変えていない。S-8 の読みが (イ) の読み方で割れるので、割れ方を数で残す"
SUB_TEXT = collections.OrderedDict([
    (u"イ1", u"字のとおり(内訳・一部分・1 株当たりの数・文の中で計算した差を、全体の fact と比べた)"),
    (u"イ2", u"向きが逆(全体・合計の数や率を、同じ文に原因として出た内訳の要素の fact と比べた)"),
    (u"イ3", u"内訳の数を、となりの内訳や別の表の要素の fact と比べた"),
    (u"オ1", u"会社が定義した指標の数を、名前の近い財務諸表の項目の fact と比べた"),
    (u"オ2", u"同じ名前で別の表にある項目の fact と比べた"),
    (u"カ1", u"億と百万(千万)を続けて書いた数の、後ろの一部だけを数として読んだ"),
    (u"カ2", u"増減率を、前期に対する比率(100 を足した形)として計算した値と比べた"),
    (u"カ3", u"率の丸め(差は 0.1 ポイント)"),
    (u"ケ1", u"読めたが、封の 9 つの型に当てはまる型がない(全社の数を、文と関係のない別の要素の fact と比べた)")])
POP_BYTE_MIN = 1


def _flat_strings(x):
    if isinstance(x, dict):
        for k, v in x.items():
            for s in _flat_strings(k):
                yield s
            for s in _flat_strings(v):
                yield s
    elif isinstance(x, (list, tuple)):
        for v in x:
            for s in _flat_strings(v):
                yield s
    elif isinstance(x, str):
        yield x


#: 日本語の長い字として記録に在ってよい文字列(門が字で留めたもの + script の定数)。ここに無い長い日本語は「文」とみなして赤
LONG_OK = set(s for s in list(_flat_strings([
    STATES_STEP, POP_STEP, TYPES_STEP, SUB_STEP, TYPED_BY, TYPES_BLIND, SUB_BLIND, SUB_NOTE, SUB_HOW, SAMPLE_RULE_POP, SAMPLE_RULE_HOW, list(LIMITS_PIN),
    CUT_PIN, WRAP_PIN, dict(MS.TYPES), dict(SUB_TEXT)])) if len(s) >= LONG_JA)


def seal_pred_cells(seal):
    u"""{S-n: [欄, 予測, 外れ方]}(封 §3 の表)。"""
    sec = seal[seal.index(u"## §3"):seal.index(u"## §4")]
    return collections.OrderedDict((k, rest.split(u" | ")) for k, rest in re.findall(r"^\| (S-\d+) \| (.*) \|$", sec, re.M))


def nums_of(text):
    return [int(x.rstrip(u",").replace(u",", u"")) for x in re.findall(r"\d[\d,]*", text)]


def seal_bounds(cells):
    return collections.OrderedDict((k, tuple(nums_of(cells[k][1])[:2])) for k in (u"S-8", u"S-9", u"S-10"))


def population_problems(seal, pop, states):
    u"""封 §1 の表 400 行 = 置いた記録 = 判定の記録(同じ順・同じ #・群・様式・sha256)。群・様式の数は字で留める。封の「下見」の 2 欄と本ごとの 切り出し・claim。"""
    out = []
    table = SG.seal_table(seal)
    prow, books = pop.get(u"行"), states.get(u"本")
    if len(table) != 400 or len(prow) != 400 or len(books) != 400:
        return [u"母集団: 行の数が 400・400・400 でない(封 %d・置いた記録 %d・判定の記録 %d)" % (len(table), len(prow), len(books))]
    if collections.OrderedDict((g, sum(1 for r in table if r[1] == g)) for g in GROUPS) != GROUP_COUNTS:
        out.append(u"母集団: 封の表の群の数が 甲 50・乙 200・丙 150 でない")
    if collections.OrderedDict((k, sum(1 for r in table if r[2] == k)) for k in KIND_COUNTS) != KIND_COUNTS or sum(KIND_COUNTS.values()) != 400:
        out.append(u"母集団: 封の表の様式の種類の数が字で留めた数と違う")
    if dict(pop.get(u"群") or {}) != dict(GROUP_COUNTS) or dict(pop.get(u"様式の種類") or {}) != dict(KIND_COUNTS):
        out.append(u"母集団: 置いた記録の 群・様式の種類 の数が字で留めた数と違う")
    for t, p, b in zip(table, prow, books):
        n, grp, kind, sha = t[0], t[1], t[2], t[3]
        if list(p[:4]) != [n, grp, kind, sha]:
            out.append(u"母集団: # %d 置いた記録の行が封の表と違う" % n)
        if len(p) != 5 or not is_int(p[4]) or p[4] < POP_BYTE_MIN:
            out.append(u"母集団: # %d 置いた記録の byte 数が正の整数でない" % n)
        if [b.get(u"#"), b.get(u"群"), b.get(u"様式の種類"), b.get(u"ZIP の sha256")] != [n, grp, kind, sha]:
            out.append(u"母集団: # %d 判定の記録の本が封の表と違う" % n)
        if b.get(u"切り出し") != t[4]:
            out.append(u"母集団: # %d 切り出しが封の下見と違う(S-2 の本ごとの版)" % n)
        want_claim = 0 if t[5] == u"-" else int(t[5])
        if b.get(u"claim") != want_claim:
            out.append(u"母集団: # %d claim が封の下見と違う(S-4・S-5 の本ごとの版)" % n)
    return out


def order_others():
    return list(RECORD_RELS) + [DOC_REL, GATE_REL]


def order_problems_real(root=REPO):
    return PR.order_problems(root, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, [STAGE_REL, SCRIPT_REL], order_others())


def engine_problems(root=REPO, added=SCRIPT_ADDED_COMMIT, seal_rel=SEAL_REL, script_rels=(STAGE_REL, SCRIPT_REL)):
    out = list(SG.engine_since_seal_problems(root, seal_rel))
    rc, txt = PR.git_in(root, "diff", "--numstat", added, "--", *[PREFIX + r for r in script_rels])
    if rc != 0:
        out.append(u"engine: git diff が失敗した")
    elif txt:
        out.append(u"engine: script 2 本が %s から変わっている" % added)
    return out


def current_state(root=REPO):
    u"""header の照合に使う今の値。"""
    return {"stage_sha": sha256_rel(STAGE_REL), "script_sha": sha256_rel(SCRIPT_REL), "prev_sha": sha256_rel(MS.TS_SCRIPT_REL),
            "states_sha": sha256_rel(STATES_REL), "types_sha": sha256_rel(TYPES_REL), "fp": MS.VD.engine_fingerprint(),
            "head_ok": lambda c: bool(isinstance(c, str) and HEX40.match(c)) and PR.is_anc(root, SCRIPT_ADDED_COMMIT, c)}


POP_KEYS = (u"seal", u"封の commit", u"step", u"HEAD の commit", u"この script の sha256", u"範囲", u"置き場", u"ほかの cache の前後", u"表と一致した ZIP", u"新しく置いた ZIP",
            u"在って触らなかった ZIP(sha256 が同じ)", u"群", u"様式の種類", u"行の欄", u"行", u"key_leaks")
STATES_KEYS = (u"seal", u"封の commit", u"step", u"HEAD の commit", u"この script の sha256", u"置く script の sha256", u"2026-11-09 の便の script の sha256", u"engine の指紋", u"profile",
               u"材料", u"切り出し", u"包み直し", u"本の数", u"集計", u"限界", u"行の欄", u"時間(秒)", u"key_leaks", u"本")
TYPES_KEYS = (u"seal", u"封の commit", u"step", u"HEAD の commit", u"この script の sha256", u"states の記録の sha256", u"型を付けた席", u"盲検", u"標本の規則", u"型の字", u"型の集計",
              u"行の欄", u"行", u"key_leaks")
SUB_KEYS_TOP = (u"seal", u"封の commit", u"step", u"補足", u"型の記録の sha256", u"付けた席", u"盲検", u"作り方", u"細目の字", u"細目の集計", u"行の欄", u"行", u"key_leaks")
SAMPLE_RULE_KEYS = (u"母集団", u"種", u"引き方", u"A の VALUE_MISMATCH の行の数", u"標本の数")
PIN_VM_A = 1898


def header_problems(kind, rec, cur):
    u"""記録の header(欄の名前・seal・封の commit・step・script の sha256・HEAD の commit・留める字・key_leaks)。kind = pop / states / types / sub。"""
    out = []
    keys = {"pop": POP_KEYS, "states": STATES_KEYS, "types": TYPES_KEYS, "sub": SUB_KEYS_TOP}[kind]
    if set(rec.keys()) != set(keys) or len(rec.keys()) != len(keys):
        out.append(u"header[%s]: 欄の名前の集合が字で留めたものと違う" % kind)
    if rec.get(u"seal") != SEAL_REL or rec.get(u"封の commit") != SEAL_COMMIT_SHORT:
        out.append(u"header[%s]: seal・封の commit が違う" % kind)
    want_step = {"pop": POP_STEP, "states": STATES_STEP, "types": TYPES_STEP, "sub": SUB_STEP}[kind]
    if rec.get(u"step") != want_step:
        out.append(u"header[%s]: step の字が違う" % kind)
    if rec.get(u"key_leaks") != []:
        out.append(u"header[%s]: key_leaks が空でない" % kind)
    if kind != "sub" and not cur["head_ok"](rec.get(u"HEAD の commit")):
        out.append(u"header[%s]: HEAD の commit が script を足した commit を含まない(祖先か同じでない)" % kind)
    if kind == "pop":
        if rec.get(u"この script の sha256") != cur["stage_sha"]:
            out.append(u"header[pop]: 置く script の sha256 が今の file と違う")
        if rec.get(u"範囲") != u"封 §1 の 400 本" or rec.get(u"置き場") != CACHE_PLACE:
            out.append(u"header[pop]: 範囲・置き場が違う")
        c = rec.get(u"ほかの cache の前後")
        if not isinstance(c, dict) or set(c.keys()) != set([u"比べた folder の数", u"前の一覧の sha256", u"後の一覧の sha256", u"変化なし"]):
            out.append(u"header[pop]: ほかの cache の前後の欄が違う")
        elif c[u"変化なし"] is not True or c[u"比べた folder の数"] != 11 or c[u"前の一覧の sha256"] != c[u"後の一覧の sha256"] or not HEX64.match(str(c[u"前の一覧の sha256"])):
            out.append(u"header[pop]: ほかの cache の前後が「変化なし・folder 11・一覧の sha256 が同じ」でない")
        if rec.get(u"表と一致した ZIP") != 400 or not is_int(rec.get(u"新しく置いた ZIP")) or not is_int(rec.get(u"在って触らなかった ZIP(sha256 が同じ)")) \
                or rec[u"新しく置いた ZIP"] + rec[u"在って触らなかった ZIP(sha256 が同じ)"] != 400:
            out.append(u"header[pop]: 表と一致した ZIP が 400 でない・置いた数の和が 400 でない")
        if rec.get(u"行の欄") != [u"#", u"群", u"様式の種類", u"ZIP の sha256", u"byte 数"]:
            out.append(u"header[pop]: 行の欄が違う")
    elif kind == "states":
        if rec.get(u"この script の sha256") != cur["script_sha"] or rec.get(u"置く script の sha256") != cur["stage_sha"] or rec.get(u"2026-11-09 の便の script の sha256") != cur["prev_sha"]:
            out.append(u"header[states]: script の sha256 が今の file と違う")
        fp = rec.get(u"engine の指紋") or {}
        if fp.get(u"adapter_xbrl_py_sha256") != cur["fp"]["adapter_xbrl_py_sha256"] or fp.get(u"core_py_sha256") != cur["fp"]["core_py_sha256"]:
            out.append(u"header[states]: engine の指紋が今の engine と違う")
        if rec.get(u"profile") != u"P33E":
            out.append(u"header[states]: profile が P33E でない")
        if rec.get(u"切り出し") != dict(CUT_PIN):
            out.append(u"header[states]: 切り出しの欄が留めた字と違う")
        if rec.get(u"包み直し") != dict(WRAP_PIN):
            out.append(u"header[states]: 包み直しの欄が留めた字と違う")
        if rec.get(u"限界") != list(LIMITS_PIN) or rec.get(u"限界") != list(MS.STATES_LIMITS) or len(rec.get(u"限界")) != 7:
            out.append(u"header[states]: 限界が 7 項目の留めた字(script の STATES_LIMITS)と違う")
        m = rec.get(u"材料")
        if not isinstance(m, dict) or set(m.keys()) != set([u"置き場", u"表と一致した ZIP", u"置き場の一覧の前後"]):
            out.append(u"header[states]: 材料の欄が違う")
        else:
            z = m[u"置き場の一覧の前後"]
            if m[u"置き場"] != CACHE_PLACE or m[u"表と一致した ZIP"] != 400 or set(z.keys()) != set([u"前", u"後", u"変化なし"]) or z[u"変化なし"] is not True \
                    or z[u"前"] != z[u"後"] or z[u"前"][0] != 400 or not HEX64.match(str(z[u"前"][1])):
                out.append(u"header[states]: 材料が「400・前後の変化なし」でない")
        if rec.get(u"本の数") != 400:
            out.append(u"header[states]: 本の数が 400 でない")
        if rec.get(u"行の欄") != list(ROW_COLUMNS):
            out.append(u"header[states]: 行の欄が違う")
        t = rec.get(u"時間(秒)")
        if isinstance(t, bool) or not isinstance(t, (int, float)) or t < 0:
            out.append(u"header[states]: 時間(秒)が数でない")
    elif kind == "types":
        if rec.get(u"この script の sha256") != cur["script_sha"] or rec.get(u"states の記録の sha256") != cur["states_sha"]:
            out.append(u"header[types]: script・states の記録の sha256 が今の file と違う")
        if rec.get(u"型を付けた席") != TYPED_BY or rec.get(u"型を付けた席") != MS.TYPED_BY:
            out.append(u"header[types]: 型を付けた席の字が違う")
        if rec.get(u"盲検") != TYPES_BLIND:
            out.append(u"header[types]: 盲検の欄が違う")
        if rec.get(u"行の欄") != [u"標本の番号", u"本の #", u"文の番号", u"位置", u"型"]:
            out.append(u"header[types]: 行の欄が違う")
    else:
        if rec.get(u"型の記録の sha256") != cur["types_sha"]:
            out.append(u"header[sub]: 型の記録の sha256 が今の file と違う")
        if rec.get(u"付けた席") != TYPED_BY or rec.get(u"盲検") != SUB_BLIND or rec.get(u"作り方") != SUB_HOW:
            out.append(u"header[sub]: 付けた席・盲検・作り方の字が違う")
        if rec.get(u"補足") != SUB_NOTE or SUB_NOTE_PIN not in (rec.get(u"補足") or u""):
            out.append(u"header[sub]: 補足(封に無い補足だという字)が違う")
        if rec.get(u"行の欄") != [u"標本の番号", u"型", u"細目"]:
            out.append(u"header[sub]: 行の欄が違う")
    return out


def book_string_problems(books):
    u"""本の中の文字列は決まった語だけ(閉じた語彙)。"""
    out = []
    for b in books:
        n = b.get(u"#")
        for key, ok in ((u"群", GROUPS), (u"様式の種類", tuple(KIND_COUNTS)), (u"切り出し", (u"切れた", u"切れない"))):
            if b.get(key) not in ok:
                out.append(u"本 # %s: %s が決まった語でない" % (n, key))
        if not HEX64.match(str(b.get(u"ZIP の sha256"))):
            out.append(u"本 # %s: ZIP の sha256 が 64 字の 16 進でない" % n)
        if b.get(u"理由") is not None and b.get(u"理由") not in WHYS:
            out.append(u"本 # %s: 理由が決まった語でない" % n)
        for r in b.get(u"行") or []:
            if r[2] not in STATES:
                out.append(u"本 # %s: 行の state が 4 つの外" % n)
            if r[3] is not None and not (isinstance(r[3], str) and REASON_RE.match(r[3])):
                out.append(u"本 # %s: 行の reason が英字の短い語の形でない" % n)
            if r[4] not in PERIODS5:
                out.append(u"本 # %s: 行の pointer の期が決まった集合の外" % n)
            if r[6] not in FAMILIES:
                out.append(u"本 # %s: 行の単位の族が 3 つの外" % n)
    return out


def book_problems(states):
    out = []
    books = states.get(u"本")
    if not isinstance(books, list) or len(books) != 400:
        return [u"本: 400 本でない"]
    if [b.get(u"#") for b in books] != list(range(1, 401)):
        out.append(u"本: # が 1〜400 の順でない")
    for b in books:
        n = b.get(u"#")
        if set(b.keys()) != set(BOOK_KEYS) or len(b.keys()) != len(BOOK_KEYS):
            out.append(u"本 # %s: 欄の名前が字で留めたものと違う" % n)
            continue
        rows = b[u"行"]
        if not is_int(b[u"claim"]) or b[u"claim"] != len(rows):
            out.append(u"本 # %s: claim が行の数と違う" % n)
        if b[u"切り出し"] == u"切れない":
            if rows != [] or b[u"理由"] not in WHYS or b[u"claim"] != 0:
                out.append(u"本 # %s: 切れない本が「行 0・claim 0・理由あり」でない" % n)
            if any(b[k] is not None for k in (u"見出しの番号", u"字数", u"入れた iXBRL の file の数", u"fact の数", u"対応")):
                out.append(u"本 # %s: 切れない本に数が入っている" % n)
        else:
            if b[u"理由"] is not None or b[u"見出しの番号"] not in (0, 1, 2) or not is_int(b[u"見出しの番号"]):
                out.append(u"本 # %s: 切れた本の 理由・見出しの番号 が違う" % n)
            if not (is_int(b[u"字数"]) and b[u"字数"] >= 1 and is_int(b[u"入れた iXBRL の file の数"]) and b[u"入れた iXBRL の file の数"] >= 0 and is_int(b[u"fact の数"]) and b[u"fact の数"] >= 0):
                out.append(u"本 # %s: 切れた本の 字数・file の数・fact の数 が整数でない" % n)
            if not isinstance(b[u"対応"], bool):
                out.append(u"本 # %s: 対応が真偽でない" % n)
        for r in rows:
            if not isinstance(r, list) or len(r) != len(ROW_COLUMNS):
                out.append(u"本 # %s: 行が 9 欄でない" % n)
                continue
            if not (is_int(r[0]) and is_int(r[1]) and r[0] >= 0 and r[1] >= 0 and isinstance(r[5], bool) and isinstance(r[7], bool) and isinstance(r[8], bool)):
                out.append(u"本 # %s: 行の型(整数・真偽)が違う" % n)
    out += book_string_problems(books)
    return out


def count_books(books):
    u"""本の集まりを 1 度の走査で数える(script の block とは別の書き方)。"""
    n_cut = 0
    why = collections.OrderedDict((w, 0) for w in WHYS)
    heads = collections.OrderedDict([(u"0", 0), (u"1", 0), (u"2", 0)])
    chars = files = facts = claims = 0
    st = collections.OrderedDict((s, 0) for s in STATES)
    rs = collections.OrderedDict((s, collections.OrderedDict()) for s in STATES)
    vm = collections.OrderedDict([(k, 0) for k in VM_KEYS if k != u"pointer の期"])
    per = collections.OrderedDict((p, 0) for p in PERIODS5)
    zero_claim = zero_g = vm_books = misaligned = 0
    for b in books:
        if b[u"切り出し"] != u"切れた":
            why[b[u"理由"]] += 1
            continue
        n_cut += 1
        heads[u"%d" % b[u"見出しの番号"]] += 1
        chars += b[u"字数"]
        files += b[u"入れた iXBRL の file の数"]
        facts += b[u"fact の数"]
        if b[u"対応"] is not True:
            misaligned += 1
        g_n = v_n = 0
        for r in b[u"行"]:
            claims += 1
            st[r[2]] += 1
            key = r[3] if r[3] is not None else u"なし"
            rs[r[2]][key] = rs[r[2]].get(key, 0) + 1
            if r[2] == G:
                g_n += 1
            if r[2] == VM:
                v_n += 1
                vm[u"行"] += 1
                vm[u"導出(formula)" if r[5] else u"直接"] += 1
                vm[u"% の数" if r[8] else u"円族の数"] += 1
                vm[u"両期の fact を引く a−b(円)"] += 1 if r[7] else 0
                vm[{u"%": u"単位の族が %", u"円族": u"単位の族が円族", u"他": u"単位の族が他"}[r[6]]] += 1
                per[r[4]] += 1
        if not b[u"行"]:
            zero_claim += 1
        if g_n == 0:
            zero_g += 1
        if v_n >= 1:
            vm_books += 1
    vm[u"pointer の期"] = per
    return collections.OrderedDict([
        (u"本", len(books)), (u"切れた", n_cut), (u"切れない", len(books) - n_cut), (u"切れない理由", why), (u"見出しの番号の本数", heads), (u"字数の合計", chars),
        (u"入れた iXBRL の file の数の合計", files), (u"fact の数の合計", facts), (u"claim", claims), (u"4 state", st),
        (u"reason", collections.OrderedDict((s, collections.OrderedDict(sorted(rs[s].items()))) for s in STATES)), (u"VALUE_MISMATCH の内訳", vm),
        (u"切れた本のうち claim が 0 の本", zero_claim), (u"切れた本のうち GROUNDED が 0 の本", zero_g), (u"VALUE_MISMATCH が 1 以上の本", vm_books),
        (u"claim と raw の並びが対応しなかった本", misaligned)])


def _plain(x):
    return json.loads(json.dumps(x, ensure_ascii=False))


def block_diff(label, got, want):
    out = []
    if not isinstance(got, dict) or set(got.keys()) != set(BLOCK_KEYS):
        return [u"集計 %s: 欄の名前の集合が字で留めたものと違う" % label]
    if set(got[u"VALUE_MISMATCH の内訳"].keys()) != set(VM_KEYS):
        out.append(u"集計 %s: VALUE_MISMATCH の内訳の欄の名前が違う" % label)
    for k in BLOCK_KEYS:
        if _plain(got[k]) != _plain(want[k]):
            out.append(u"集計 %s: 欄 %s が行から数え直した数と違う" % (label, k))
    return out


def recount_problems(states):
    u"""集計の全部(群 3・A・B・様式 7)を行から数え直して記録と == で比べる。"""
    books = states[u"本"]
    got = states.get(u"集計")
    if not isinstance(got, dict) or set(got.keys()) != set(TALLY_KEYS):
        return [u"集計: 最上位の欄の名前が違う"]
    out = []
    if set(got[u"群"].keys()) != set(GROUPS) or set(got[u"様式の種類"].keys()) != set(KIND_COUNTS):
        return [u"集計: 群・様式の種類の欄の名前が違う"]
    for g in GROUPS:
        out += block_diff(u"群 %s" % g, got[u"群"][g], count_books([b for b in books if b[u"群"] == g]))
    out += block_diff(u"A", got[u"A(甲 + 乙)"], count_books([b for b in books if b[u"群"] in (u"甲", u"乙")]))
    out += block_diff(u"B", got[u"B(丙)"], count_books([b for b in books if b[u"群"] == u"丙"]))
    for k in KIND_COUNTS:
        out += block_diff(u"様式 %s" % k, got[u"様式の種類"][k], count_books([b for b in books if b[u"様式の種類"] == k]))
    return out


def vm_rows_of_a(states):
    rows = []
    for b in sorted(states[u"本"], key=lambda b: b[u"#"]):
        if b[u"群"] in (u"甲", u"乙"):
            for r in sorted((r for r in b[u"行"] if r[2] == VM), key=lambda r: (r[0], r[1])):
                rows.append((b[u"#"], r[0], r[1]))
    return rows


def draw_sample(rows, seed=20261114, k=120):
    u"""標本の行 [標本の番号(1 から), 本の #, 文の番号, 位置]。引いた番号を昇順に並べる(門の中で自前で引く)。"""
    if len(rows) <= k:
        idx = list(range(len(rows)))
    else:
        idx = sorted(random.Random(seed).sample(range(len(rows)), k))
    return [[i + 1] + list(rows[j]) for i, j in enumerate(idx)]


def sample_problems(states, types):
    out = []
    rows = vm_rows_of_a(states)
    want = draw_sample(rows)
    got = [list(r[:4]) for r in types.get(u"行") or []]
    if got != want:
        out.append(u"標本: 型の記録の 120 行の(本の #・文の番号・位置)が、自前で引いた行と違う(%d 行 / 引いた %d 行)" % (len(got), len(want)))
    rule = types.get(u"標本の規則")
    if not isinstance(rule, dict) or set(rule.keys()) != set(SAMPLE_RULE_KEYS):
        out.append(u"標本: 標本の規則の欄の名前が違う")
    else:
        if rule[u"種"] != 20261114 or rule[u"A の VALUE_MISMATCH の行の数"] != PIN_VM_A or rule[u"標本の数"] != 120:
            out.append(u"標本: 標本の規則の 種・行の数・標本の数 が 20261114・%d・120 でない" % PIN_VM_A)
        if len(rows) != PIN_VM_A or rule[u"A の VALUE_MISMATCH の行の数"] != len(rows):
            out.append(u"標本: A の VALUE_MISMATCH の行の数が記録の行から数えた数と違う")
        if rule[u"母集団"] != SAMPLE_RULE_POP or rule[u"引き方"] != SAMPLE_RULE_HOW:
            out.append(u"標本: 標本の規則の字が違う")
    return out


def types_problems(types):
    out = []
    if list(types.get(u"型の字", {}).keys()) != list(TYPE_LETTERS) or dict(types[u"型の字"]) != dict(MS.TYPES):
        out.append(u"型: 型の字が script の TYPES(ア〜ケの 9 つ)と違う")
    rows = types.get(u"行") or []
    if len(rows) != 120:
        out.append(u"型: 行が 120 でない")
    for i, r in enumerate(rows):
        if len(r) != 5 or r[0] != i + 1 or not all(is_int(x) for x in r[:4]) or not isinstance(r[4], str) or r[4] not in TYPE_LETTERS or len(r[4]) != 1:
            out.append(u"型: 行 %d の形・標本の番号・型が違う" % (i + 1))
    cnt = collections.OrderedDict((t, sum(1 for r in rows if r[4] == t)) for t in TYPE_LETTERS)
    got = types.get(u"型の集計")
    if not isinstance(got, dict) or list(got.keys()) != list(TYPE_LETTERS) or dict(got) != dict(cnt) or sum(cnt.values()) != 120:
        out.append(u"型: 型の集計が行から数え直した数(合計 120)と違う")
    return out


def sub_problems(sub, types):
    out = []
    if list(sub.get(u"細目の字", {}).keys()) != list(SUB_KEYS) or dict(sub[u"細目の字"]) != dict(SUB_TEXT):
        out.append(u"細目: 細目の字が留めた字(9 つの key)と違う")
    want = [[r[0], r[4]] for r in types[u"行"] if r[4] in SUB_TYPES]
    rows = sub.get(u"行") or []
    if [list(r[:2]) for r in rows] != want or len(want) != 34 or len(rows) != 34:
        out.append(u"細目: 行が (イ)(オ)(カ)(ケ) の行の過不足なし 34 行でない(標本の番号・型)")
    for r in rows:
        if len(r) != 3 or not isinstance(r[2], str) or r[2] not in SUB_KEYS or r[2][0] != r[1]:
            out.append(u"細目: 行 %s の細目が細目の字の key でない・型と合わない" % (r[0] if r else None))
    cnt = collections.OrderedDict((k, sum(1 for r in rows if len(r) == 3 and r[2] == k)) for k in SUB_KEYS)
    got = sub.get(u"細目の集計")
    if not isinstance(got, dict) or list(got.keys()) != list(SUB_KEYS) or dict(got) != dict(cnt):
        out.append(u"細目: 細目の集計が行から数え直した数と違う")
    return out


def _walk(x):
    if isinstance(x, dict):
        for k, v in x.items():
            for s in _walk(v):
                yield s
    elif isinstance(x, (list, tuple)):
        for v in x:
            for s in _walk(v):
                yield s
    else:
        yield x


def _all_keys(x, acc):
    if isinstance(x, dict):
        for k, v in x.items():
            acc.append(k)
            _all_keys(v, acc)
    elif isinstance(x, list):
        for v in x:
            _all_keys(v, acc)
    return acc


def clean_problems(kind, rec, text=None):
    u"""記録に文も会社名も証券コードも無い。script の check_clean とは別に、門が自前で全部の葉と key を歩く。"""
    out = []
    keys = _all_keys(rec, [])
    bad = sorted(set(k for k in keys if k in FORBIDDEN_KEYS))
    if bad:
        out.append(u"clean[%s]: repo へ入れない欄がある: %s" % (kind, u",".join(bad)))
    strs = [s for s in _walk(rec)] + keys
    for s in strs:
        if s is None or isinstance(s, (bool, int, float)):
            continue
        if not isinstance(s, str):
            out.append(u"clean[%s]: 葉が文字・数・真偽・null のどれでもない" % kind)
            continue
        if DOCID_RE.search(s):
            out.append(u"clean[%s]: docID の形の字がある" % kind)
        if TDNET_RE.search(s):
            out.append(u"clean[%s]: TDnet の番号の形の字がある" % kind)
        if CODE_RE.search(s):
            out.append(u"clean[%s]: 証券コードの形の字がある" % kind)
        if POINTER_RE.search(s):
            out.append(u"clean[%s]: pointer・要素名の形の字がある" % kind)
        if any(w in s for w in COMPANY_WORDS):
            out.append(u"clean[%s]: 会社名らしい字がある" % kind)
        if len(s) >= LONG_JA and JA_RE.search(s) and s not in LONG_OK:
            out.append(u"clean[%s]: 留めた字に無い長い日本語の文がある" % kind)
    if kind == "states":
        out += book_string_problems(rec.get(u"本") or [])
    elif kind == "types":
        for r in rec.get(u"行") or []:
            if not (len(r) == 5 and all(is_int(x) for x in r[:4]) and r[4] in TYPE_LETTERS):
                out.append(u"clean[types]: 行が「数 4 つと型の 1 字」でない")
    elif kind == "sub":
        for r in rec.get(u"行") or []:
            if not (len(r) == 3 and is_int(r[0]) and r[1] in SUB_TYPES and r[2] in SUB_KEYS):
                out.append(u"clean[sub]: 行が「数・型・細目の key」でない")
    elif kind == "pop":
        for r in rec.get(u"行") or []:
            if not (len(r) == 5 and is_int(r[0]) and r[1] in GROUPS and r[2] in KIND_COUNTS and HEX64.match(str(r[3])) and is_int(r[4])):
                out.append(u"clean[pop]: 行が「# ・群・様式・sha256・byte 数」でない")
    if text is None:
        text = json.dumps(rec, ensure_ascii=False, default=str)
    try:
        MS.check_clean(rec, text)
    except SystemExit:
        out.append(u"clean[%s]: script の check_clean が止めた" % kind)
    return out


# ======================================================================================================
# 試験の道具
class Ctx(object):
    u"""実物の封・文書・今の値(一度だけ読む)。変異は ``fresh_records()`` の新しい写しに 1 か所だけ加える。"""
    _inst = None

    @classmethod
    def get(cls):
        if cls._inst is None:
            c = cls()
            c.seal = read(SEAL_REL)
            c.doc = read(DOC_REL)
            c.cur = current_state()
            c.texts = collections.OrderedDict((k, read(r)) for k, r in zip(("pop", "states", "types", "sub"), RECORD_RELS))
            cls._inst = c
        return cls._inst


def real_head_not_descendant():
    u"""script を足した commit の祖先で、その commit ではない commit(40 字)。HEAD の commit の欄を違うものに替える変異に使う。"""
    rc, out = PR.git_in(REPO, "rev-parse", SCRIPT_ADDED_COMMIT + "^")
    assert rc == 0 and HEX40.match(out), out
    return out


def check_pop(R, c):
    return population_problems(c.seal, R["pop"], R["states"])


def check_states(R, c):
    u"""本の整合が崩れていれば本の問題だけ(数え直しは整った本にだけ掛ける)。整っていれば行から数え直した集計との照合。"""
    return book_problems(R["states"]) or recount_problems(R["states"])


def check_sample(R, c):
    return sample_problems(R["states"], R["types"])


def check_types(R, c):
    return types_problems(R["types"])


def check_sub(R, c):
    return sub_problems(R["sub"], R["types"])


def check_hdr(kind):
    return lambda R, c: header_problems(kind, R[kind], c.cur)


def check_clean(kind):
    return lambda R, c: clean_problems(kind, R[kind])


def check_doc(R, c):
    return doc_problems(c.doc, R, c.seal)


def books_of(R, groups=(u"甲", u"乙")):
    return [b for b in R["states"][u"本"] if b[u"群"] in groups]


def first_row(R, state, groups=(u"甲", u"乙"), pred=None):
    for b in books_of(R, groups):
        for r in b[u"行"]:
            if r[2] == state and (pred is None or pred(r)):
                return b, r
    raise AssertionError(u"行が見つからない")


def first_book(R, cut=True, groups=(u"甲", u"乙"), pred=None):
    for b in books_of(R, groups):
        if (b[u"切り出し"] == u"切れた") == cut and (pred is None or pred(b)):
            return b
    raise AssertionError(u"本が見つからない")


def set_key(d, path, f):
    for k in path[:-1]:
        d = d[k]
    d[path[-1]] = f(d[path[-1]])


def numeric_leaf_paths(x, path=()):
    if isinstance(x, dict):
        for k, v in x.items():
            for p in numeric_leaf_paths(v, path + (k,)):
                yield p
    elif is_int(x):
        yield path


class Mutations(object):
    u"""変異の表。(ラベル, 変異(R, c), 検査, 検査が返す問題に含まれるべき字)。"""
    rows = []

    @classmethod
    def add(cls, label, mut, check, tag):
        cls.rows.append((label, mut, check, tag))


M = Mutations.add


def _flip_char(s):
    return (u"0" if s[0] != u"0" else u"1") + s[1:]


def _swap(lst, i, j):
    lst[i], lst[j] = lst[j], lst[i]


# ---- a. 母集団
M(u"母集団: 置いた記録の 1 行の sha を 1 字替える", lambda R, c: R["pop"][u"行"][7].__setitem__(3, _flip_char(R["pop"][u"行"][7][3])), check_pop, u"母集団")
M(u"母集団: 置いた記録の 1 行の群を替える", lambda R, c: R["pop"][u"行"][0].__setitem__(1, u"乙"), check_pop, u"母集団")
M(u"母集団: 置いた記録の 1 行の様式を替える", lambda R, c: R["pop"][u"行"][100].__setitem__(2, u"anedjpsm"), check_pop, u"母集団")
M(u"母集団: 置いた記録の byte 数を 0 にする", lambda R, c: R["pop"][u"行"][5].__setitem__(4, 0), check_pop, u"byte 数")
M(u"母集団: 置いた記録の行を 1 つ消す", lambda R, c: R["pop"][u"行"].pop(), check_pop, u"母集団")
M(u"母集団: 置いた記録の 2 行の順を入れ替える", lambda R, c: _swap(R["pop"][u"行"], 3, 4), check_pop, u"母集団")
M(u"母集団: 判定の記録の 1 本の sha を 1 字替える", lambda R, c: R["states"][u"本"][200].__setitem__(u"ZIP の sha256", _flip_char(R["states"][u"本"][200][u"ZIP の sha256"])), check_pop, u"母集団")
M(u"母集団: 判定の記録の 1 本の群を替える", lambda R, c: R["states"][u"本"][60].__setitem__(u"群", u"丙"), check_pop, u"母集団")
M(u"母集団: 判定の記録の 1 本の様式を替える", lambda R, c: R["states"][u"本"][399].__setitem__(u"様式の種類", u"acedifsm"), check_pop, u"母集団")
M(u"母集団: 判定の記録の本の順を入れ替える", lambda R, c: _swap(R["states"][u"本"], 0, 1), check_pop, u"母集団")
M(u"母集団: 判定の記録の本を 1 つ消す", lambda R, c: R["states"][u"本"].pop(), check_pop, u"母集団")
M(u"母集団: 置いた記録の群の数を 1 替える", lambda R, c: R["pop"][u"群"].__setitem__(u"乙", 201), check_pop, u"群・様式の種類")
M(u"母集団: 置いた記録の様式の数を 1 替える", lambda R, c: R["pop"][u"様式の種類"].__setitem__(u"scedjpsy", 111), check_pop, u"群・様式の種類")
M(u"母集団: 切れた本の claim を 1 増やす(封の下見の本ごとの版)", lambda R, c: first_book(R, True, pred=lambda b: b[u"claim"] > 0).__setitem__(u"claim", first_book(R, True, pred=lambda b: b[u"claim"] > 0)[u"claim"] + 1),
  check_pop, u"claim")
M(u"母集団: 切れた本を切れないに替える(封の下見の本ごとの版)", lambda R, c: first_book(R, True).__setitem__(u"切り出し", u"切れない"), check_pop, u"切り出し")
M(u"母集団: 切れない本の claim を 1 にする", lambda R, c: first_book(R, False).__setitem__(u"claim", 1), check_pop, u"claim")

# ---- d. 本・集計(行から数え直す)
M(u"行: VALUE_MISMATCH の行の state を替える", lambda R, c: first_row(R, VM)[1].__setitem__(2, G), check_states, u"集計")
M(u"行: GROUNDED の行の state を替える", lambda R, c: first_row(R, G)[1].__setitem__(2, UNV), check_states, u"集計")
M(u"行: UNVERIFIABLE の行の reason を替える", lambda R, c: first_row(R, UNV)[1].__setitem__(3, u"zz_other"), check_states, u"reason")
M(u"行: VALUE_MISMATCH の行の pointer の期を替える", lambda R, c: first_row(R, VM, pred=lambda r: r[4] == u"CurrentYear")[1].__setitem__(4, u"Prior1Year"), check_states, u"VALUE_MISMATCH の内訳")
M(u"行: VALUE_MISMATCH の行の formula の有無を替える", lambda R, c: first_row(R, VM)[1].__setitem__(5, not first_row(R, VM)[1][5]), check_states, u"VALUE_MISMATCH の内訳")
M(u"行: VALUE_MISMATCH の行の単位の族を替える", lambda R, c: first_row(R, VM, pred=lambda r: r[6] == u"%")[1].__setitem__(6, u"円族"), check_states, u"VALUE_MISMATCH の内訳")
M(u"行: VALUE_MISMATCH の行の a−b の旗を替える", lambda R, c: first_row(R, VM)[1].__setitem__(7, not first_row(R, VM)[1][7]), check_states, u"VALUE_MISMATCH の内訳")
M(u"行: VALUE_MISMATCH の行の % の旗を替える", lambda R, c: first_row(R, VM)[1].__setitem__(8, not first_row(R, VM)[1][8]), check_states, u"VALUE_MISMATCH の内訳")
M(u"行: 行を 1 つ消す(claim は替えない)", lambda R, c: first_row(R, PNF)[0][u"行"].pop(), check_states, u"claim")
M(u"行: 行を 9 欄から 8 欄にする", lambda R, c: first_row(R, PNF)[0][u"行"][0].pop(), check_states, u"9 欄")
M(u"本: 字数を 1 替える", lambda R, c: first_book(R, True).__setitem__(u"字数", first_book(R, True)[u"字数"] + 1), check_states, u"字数の合計")
M(u"本: fact の数を 1 替える", lambda R, c: first_book(R, True).__setitem__(u"fact の数", first_book(R, True)[u"fact の数"] + 1), check_states, u"fact の数の合計")
M(u"本: 入れた iXBRL の file の数を 1 替える", lambda R, c: first_book(R, True).__setitem__(u"入れた iXBRL の file の数", first_book(R, True)[u"入れた iXBRL の file の数"] + 1), check_states, u"file の数の合計")
M(u"本: 見出しの番号を替える", lambda R, c: first_book(R, True).__setitem__(u"見出しの番号", 1), check_states, u"見出しの番号の本数")
M(u"本: 切れた本を切れないにする(行は残す)", lambda R, c: first_book(R, True).__setitem__(u"切り出し", u"切れない"), check_states, u"切れない本")
M(u"本: 切れない本の理由を替える", lambda R, c: first_book(R, False).__setitem__(u"理由", u"終わりなし"), check_states, u"切れない理由")
M(u"本: 切れない本の理由を決まった語の外にする", lambda R, c: first_book(R, False).__setitem__(u"理由", u"zzz"), check_states, u"理由")
M(u"本: 切れない本の理由を消す", lambda R, c: first_book(R, False).__setitem__(u"理由", None), check_states, u"切れない本")
M(u"本: claim を 1 替える", lambda R, c: first_book(R, True, pred=lambda b: b[u"claim"] > 0).__setitem__(u"claim", first_book(R, True, pred=lambda b: b[u"claim"] > 0)[u"claim"] + 1), check_states, u"claim が行の数と違う")
M(u"本: 対応を false にする", lambda R, c: first_book(R, True).__setitem__(u"対応", False), check_states, u"並びが対応しなかった本")
M(u"本: 欄の名前を 1 つ消す", lambda R, c: first_book(R, True).pop(u"fact の数"), check_states, u"欄の名前")
M(u"本: 欄の名前を 1 つ足す", lambda R, c: first_book(R, True).__setitem__(u"余り", 1), check_states, u"欄の名前")
M(u"本: 本の # を飛ばす", lambda R, c: R["states"][u"本"][10].__setitem__(u"#", 99), check_states, u"1〜400")
M(u"本: 行の state を 4 つの外にする", lambda R, c: first_row(R, PNF)[1].__setitem__(2, u"UNKNOWN"), check_states, u"4 つの外")
M(u"本: 行の pointer の期を決まった集合の外にする", lambda R, c: first_row(R, PNF)[1].__setitem__(4, u"Prior9Year"), check_states, u"決まった集合の外")
M(u"本: 行の単位の族を 3 つの外にする", lambda R, c: first_row(R, PNF)[1].__setitem__(6, u"円"), check_states, u"3 つの外")
M(u"本: 行の reason を英字の短い語の形の外にする", lambda R, c: first_row(R, UNV)[1].__setitem__(3, u"理由が長い日本語の文になっている"), check_states, u"reason")
M(u"本: 行の旗を真偽でなくす", lambda R, c: first_row(R, VM)[1].__setitem__(8, 1), check_states, u"行の型")

for _blk in ((u"群", u"甲"), (u"群", u"乙"), (u"群", u"丙"), (u"A(甲 + 乙)",), (u"B(丙)",), (u"様式の種類", u"acedifsm"), (u"様式の種類", u"acedjpsm"), (u"様式の種類", u"anedjpsm"),
             (u"様式の種類", u"scedifsy"), (u"様式の種類", u"scedjpsm"), (u"様式の種類", u"scedjpsy"), (u"様式の種類", u"snedjpsy")):
    for _field in (u"本", u"claim", u"字数の合計", u"fact の数の合計"):
        for _d in (1, -1):
            M(u"集計 %s の %s を %+d" % (u"/".join(_blk), _field, _d),
              (lambda blk, field, d: lambda R, c: set_key(R["states"][u"集計"], blk + (field,), lambda v: v + d))(_blk, _field, _d), check_states, u"集計")


def _a_leaves():
    R = fresh_records()
    return list(numeric_leaf_paths(R["states"][u"集計"][u"A(甲 + 乙)"]))


for _p in _a_leaves():
    for _d in (1, -1):
        M(u"集計 A の %s を %+d" % (u"/".join(_p), _d),
          (lambda p, d: lambda R, c: set_key(R["states"][u"集計"][u"A(甲 + 乙)"], p, lambda v: v + d))(_p, _d), check_states, u"集計 A")

M(u"集計: 欄の名前を 1 つ消す(A の fact の数の合計)", lambda R, c: R["states"][u"集計"][u"A(甲 + 乙)"].pop(u"fact の数の合計"), check_states, u"欄の名前の集合")
M(u"集計: 欄の名前を 1 つ足す(B)", lambda R, c: R["states"][u"集計"][u"B(丙)"].__setitem__(u"余り", 0), check_states, u"欄の名前の集合")
M(u"集計: VALUE_MISMATCH の内訳の欄の名前を 1 つ消す", lambda R, c: R["states"][u"集計"][u"A(甲 + 乙)"][u"VALUE_MISMATCH の内訳"].pop(u"直接"), check_states, u"内訳の欄の名前")
M(u"集計: 最上位の欄を 1 つ消す", lambda R, c: R["states"][u"集計"].pop(u"B(丙)"), check_states, u"最上位の欄の名前")
M(u"集計: 様式 1 つの欄を消す", lambda R, c: R["states"][u"集計"][u"様式の種類"].pop(u"snedjpsy"), check_states, u"群・様式の種類の欄の名前")
M(u"集計: reason の 1 つの名前を替える", lambda R, c: R["states"][u"集計"][u"A(甲 + 乙)"][u"reason"][UNV].__setitem__(u"zz_name", R["states"][u"集計"][u"A(甲 + 乙)"][u"reason"][UNV].pop(u"no_subject")), check_states, u"reason")

# ---- c・e. header・留める字
for _kind in ("pop", "states", "types", "sub"):
    M(u"header[%s]: seal の path を替える" % _kind, (lambda k: lambda R, c: R[k].__setitem__(u"seal", u"docs/other.md"))(_kind), check_hdr(_kind), u"seal")
    M(u"header[%s]: 封の commit を 1 字替える" % _kind, (lambda k: lambda R, c: R[k].__setitem__(u"封の commit", u"e56d6783"))(_kind), check_hdr(_kind), u"封の commit")
    M(u"header[%s]: step の字を替える" % _kind, (lambda k: lambda R, c: R[k].__setitem__(u"step", R[k][u"step"] + u"。"))(_kind), check_hdr(_kind), u"step")
    M(u"header[%s]: key_leaks に 1 つ足す" % _kind, (lambda k: lambda R, c: R[k].__setitem__(u"key_leaks", [u"x"]))(_kind), check_hdr(_kind), u"key_leaks")
    M(u"header[%s]: 欄の名前を 1 つ足す" % _kind, (lambda k: lambda R, c: R[k].__setitem__(u"余り", 1))(_kind), check_hdr(_kind), u"欄の名前")
    M(u"header[%s]: 行の欄を替える" % _kind, (lambda k: lambda R, c: R[k].__setitem__(u"行の欄", R[k][u"行の欄"][:-1]))(_kind), check_hdr(_kind), u"行の欄")
for _kind in ("pop", "states", "types"):
    M(u"header[%s]: HEAD の commit を script を足した commit の祖先にする" % _kind, (lambda k: lambda R, c: R[k].__setitem__(u"HEAD の commit", real_head_not_descendant()))(_kind), check_hdr(_kind), u"HEAD の commit")
    M(u"header[%s]: HEAD の commit を 40 字の 16 進でなくす" % _kind, (lambda k: lambda R, c: R[k].__setitem__(u"HEAD の commit", u"ea3b036c"))(_kind), check_hdr(_kind), u"HEAD の commit")
M(u"header[pop]: 置く script の sha256 を 1 字替える", lambda R, c: R["pop"].__setitem__(u"この script の sha256", _flip_char(R["pop"][u"この script の sha256"])), check_hdr("pop"), u"置く script の sha256")
M(u"header[pop]: ほかの cache が前後で変わった(変化なし を false)", lambda R, c: R["pop"][u"ほかの cache の前後"].__setitem__(u"変化なし", False), check_hdr("pop"), u"ほかの cache")
M(u"header[pop]: 後の一覧の sha256 を 1 字替える", lambda R, c: R["pop"][u"ほかの cache の前後"].__setitem__(u"後の一覧の sha256", _flip_char(R["pop"][u"ほかの cache の前後"][u"後の一覧の sha256"])), check_hdr("pop"), u"ほかの cache")
M(u"header[pop]: 比べた folder の数を 10 にする", lambda R, c: R["pop"][u"ほかの cache の前後"].__setitem__(u"比べた folder の数", 10), check_hdr("pop"), u"ほかの cache")
M(u"header[pop]: 表と一致した ZIP を 399 にする", lambda R, c: R["pop"].__setitem__(u"表と一致した ZIP", 399), check_hdr("pop"), u"表と一致した ZIP")
M(u"header[pop]: 範囲を替える", lambda R, c: R["pop"].__setitem__(u"範囲", u"封 §1 の 399 本"), check_hdr("pop"), u"範囲")
M(u"header[pop]: 置いた数の和を 1 ずらす", lambda R, c: R["pop"].__setitem__(u"新しく置いた ZIP", 399), check_hdr("pop"), u"和が 400")
M(u"header[states]: この script の sha256 を 1 字替える", lambda R, c: R["states"].__setitem__(u"この script の sha256", _flip_char(R["states"][u"この script の sha256"])), check_hdr("states"), u"script の sha256")
M(u"header[states]: 置く script の sha256 を 1 字替える", lambda R, c: R["states"].__setitem__(u"置く script の sha256", _flip_char(R["states"][u"置く script の sha256"])), check_hdr("states"), u"script の sha256")
M(u"header[states]: 2026-11-09 の便の script の sha256 を 1 字替える", lambda R, c: R["states"].__setitem__(u"2026-11-09 の便の script の sha256", _flip_char(R["states"][u"2026-11-09 の便の script の sha256"])), check_hdr("states"), u"script の sha256")
M(u"header[states]: engine の指紋を 1 字替える", lambda R, c: R["states"][u"engine の指紋"].__setitem__(u"adapter_xbrl_py_sha256", _flip_char(R["states"][u"engine の指紋"][u"adapter_xbrl_py_sha256"])), check_hdr("states"), u"engine の指紋")
M(u"header[states]: profile を替える", lambda R, c: R["states"].__setitem__(u"profile", u"P32E"), check_hdr("states"), u"profile")
M(u"header[states]: NFKC を false にする", lambda R, c: R["states"][u"切り出し"].__setitem__(u"NFKC", False), check_hdr("states"), u"切り出し")
M(u"header[states]: 始まりの規則を 1 字替える", lambda R, c: R["states"][u"切り出し"].__setitem__(u"始まりの規則", R["states"][u"切り出し"][u"始まりの規則"].replace(u"1", u"2", 1)), check_hdr("states"), u"切り出し")
M(u"header[states]: 終わりの規則を 1 字替える", lambda R, c: R["states"][u"切り出し"].__setitem__(u"終わりの規則", R["states"][u"切り出し"][u"終わりの規則"].replace(u"2", u"3", 1)), check_hdr("states"), u"切り出し")
M(u"header[states]: 目次の印を 1 つ消す", lambda R, c: R["states"][u"切り出し"][u"目次の印(行に在れば始まりにしない)"].pop(), check_hdr("states"), u"切り出し")
M(u"header[states]: 見出しを 1 つ消す", lambda R, c: R["states"][u"切り出し"][u"見出しの番号"].pop(), check_hdr("states"), u"切り出し")
M(u"header[states]: 包み直しのサマリーを「入れる」にする", lambda R, c: R["states"][u"包み直し"].__setitem__(u"サマリー", u"入れる"), check_hdr("states"), u"包み直し")
M(u"header[states]: 限界を 1 項目消す", lambda R, c: R["states"][u"限界"].pop(), check_hdr("states"), u"限界")
M(u"header[states]: 限界の 1 項目を替える", lambda R, c: R["states"][u"限界"].__setitem__(0, R["states"][u"限界"][0] + u"。"), check_hdr("states"), u"限界")
M(u"header[states]: 材料を 399 にする", lambda R, c: R["states"][u"材料"].__setitem__(u"表と一致した ZIP", 399), check_hdr("states"), u"材料")
M(u"header[states]: 材料の前後を違えて変化なしを false にする", lambda R, c: R["states"][u"材料"][u"置き場の一覧の前後"].__setitem__(u"変化なし", False), check_hdr("states"), u"材料")
M(u"header[states]: 材料の後の件数を 399 にする", lambda R, c: R["states"][u"材料"][u"置き場の一覧の前後"].__setitem__(u"後", [399, R["states"][u"材料"][u"置き場の一覧の前後"][u"後"][1]]), check_hdr("states"), u"材料")
M(u"header[states]: 本の数を 399 にする", lambda R, c: R["states"].__setitem__(u"本の数", 399), check_hdr("states"), u"本の数")
M(u"header[states]: 時間(秒)を負にする", lambda R, c: R["states"].__setitem__(u"時間(秒)", -1), check_hdr("states"), u"時間")
M(u"header[types]: script の sha256 を 1 字替える", lambda R, c: R["types"].__setitem__(u"この script の sha256", _flip_char(R["types"][u"この script の sha256"])), check_hdr("types"), u"sha256")
M(u"header[types]: states の記録の sha256 を 1 字替える", lambda R, c: R["types"].__setitem__(u"states の記録の sha256", _flip_char(R["types"][u"states の記録の sha256"])), check_hdr("types"), u"sha256")
M(u"header[types]: 型を付けた席を替える", lambda R, c: R["types"].__setitem__(u"型を付けた席", u"人間"), check_hdr("types"), u"席")
M(u"header[types]: 盲検の欄を替える", lambda R, c: R["types"].__setitem__(u"盲検", u"盲検"), check_hdr("types"), u"盲検")
M(u"header[sub]: 型の記録の sha256 を 1 字替える", lambda R, c: R["sub"].__setitem__(u"型の記録の sha256", _flip_char(R["sub"][u"型の記録の sha256"])), check_hdr("sub"), u"sha256")
M(u"header[sub]: 付けた席を替える", lambda R, c: R["sub"].__setitem__(u"付けた席", u"人間"), check_hdr("sub"), u"席")
M(u"header[sub]: 補足から「封に無い」の字を消す", lambda R, c: R["sub"].__setitem__(u"補足", R["sub"][u"補足"].replace(SUB_NOTE_PIN, u"")), check_hdr("sub"), u"補足")
M(u"header[sub]: 盲検の欄を替える", lambda R, c: R["sub"].__setitem__(u"盲検", u"盲検"), check_hdr("sub"), u"盲検")

# ---- f. 標本
M(u"標本: 型の記録の 1 行の本の # を替える", lambda R, c: R["types"][u"行"][10].__setitem__(1, R["types"][u"行"][10][1] + 1), check_sample, u"標本")
M(u"標本: 型の記録の 1 行の文の番号を替える", lambda R, c: R["types"][u"行"][11].__setitem__(2, R["types"][u"行"][11][2] + 1), check_sample, u"標本")
M(u"標本: 型の記録の 1 行の位置を替える", lambda R, c: R["types"][u"行"][12].__setitem__(3, R["types"][u"行"][12][3] + 1), check_sample, u"標本")
M(u"標本: 型の記録の 2 行の順を入れ替える", lambda R, c: _swap(R["types"][u"行"], 20, 21), check_sample, u"標本")
M(u"標本: 型の記録の 1 行を別の行(2 つ隣)の座標にする", lambda R, c: R["types"][u"行"][30].__setitem__(slice(1, 4), R["types"][u"行"][32][1:4]), check_sample, u"標本")
M(u"標本: 型の記録の行を 1 つ消す", lambda R, c: R["types"][u"行"].pop(), check_sample, u"標本")
M(u"標本: 標本の規則の種を替える", lambda R, c: R["types"][u"標本の規則"].__setitem__(u"種", 20261115), check_sample, u"種")
M(u"標本: 標本の規則の行の数を替える", lambda R, c: R["types"][u"標本の規則"].__setitem__(u"A の VALUE_MISMATCH の行の数", 1897), check_sample, u"行の数")
M(u"標本: 標本の規則の標本の数を替える", lambda R, c: R["types"][u"標本の規則"].__setitem__(u"標本の数", 119), check_sample, u"標本の数")
M(u"標本: 標本の規則の欄の名前を消す", lambda R, c: R["types"][u"標本の規則"].pop(u"引き方"), check_sample, u"欄の名前")
M(u"標本: states の A の VALUE_MISMATCH の行が 1 つ減る(state を替える)", lambda R, c: first_row(R, VM)[1].__setitem__(2, UNV), check_sample, u"標本")
M(u"標本: states の本の群を甲から丙へ替える(A の行が減る)", lambda R, c: first_book(R, True, groups=(u"甲",), pred=lambda b: any(r[2] == VM for r in b[u"行"])).__setitem__(u"群", u"丙"), check_sample, u"標本")

# ---- g. 型
M(u"型: 1 行の型を別の型に替える(集計はそのまま)", lambda R, c: R["types"][u"行"][0].__setitem__(4, u"ウ"), check_types, u"型の集計")
M(u"型: 型の集計を +1(行はそのまま)", lambda R, c: R["types"][u"型の集計"].__setitem__(u"ア", R["types"][u"型の集計"][u"ア"] + 1), check_types, u"型の集計")
M(u"型: 型の集計を -1(行はそのまま)", lambda R, c: R["types"][u"型の集計"].__setitem__(u"キ", -1), check_types, u"型の集計")
M(u"型: 1 行の型を 9 つの外にする", lambda R, c: R["types"][u"行"][1].__setitem__(4, u"コ"), check_types, u"形・標本の番号・型")
M(u"型: 型の字を 1 字替える", lambda R, c: R["types"][u"型の字"].__setitem__(u"ア", R["types"][u"型の字"][u"ア"] + u"。"), check_types, u"型の字")
M(u"型: 型の字を 1 つ消す", lambda R, c: R["types"][u"型の字"].pop(u"ケ"), check_types, u"型の字")
M(u"型: 行を 1 つ消す", lambda R, c: R["types"][u"行"].pop(), check_types, u"120")
M(u"型: 標本の番号を飛ばす", lambda R, c: R["types"][u"行"][5].__setitem__(0, 99), check_types, u"標本の番号")

# ---- h. 細目
M(u"細目: 細目の行を 1 つ消す", lambda R, c: R["sub"][u"行"].pop(), check_sub, u"34 行")
M(u"細目: 細目の行を 1 つ足す((ア) の行へ)", lambda R, c: R["sub"][u"行"].append([[r[0] for r in R["types"][u"行"] if r[4] == u"ア"][0], u"ア", u"イ1"]), check_sub, u"34 行")
M(u"細目: 細目の行の標本の番号を 1 つ替える", lambda R, c: R["sub"][u"行"][3].__setitem__(0, R["sub"][u"行"][3][0] + 1), check_sub, u"34 行")


def _sub_kind_mismatch(R, c):
    row = [r for r in R["sub"][u"行"] if r[2] == u"イ2"][0]
    row[2] = u"オ1"
    R["sub"][u"細目の集計"][u"イ2"] -= 1
    R["sub"][u"細目の集計"][u"オ1"] += 1


M(u"細目: 型と合わない細目(集計は合わせる)", _sub_kind_mismatch, check_sub, u"型と合わない")
M(u"細目: 細目の集計を +1", lambda R, c: R["sub"][u"細目の集計"].__setitem__(u"イ1", 6), check_sub, u"細目の集計")
M(u"細目: 細目の字を 1 つ消す", lambda R, c: R["sub"][u"細目の字"].pop(u"カ3"), check_sub, u"細目の字")
M(u"細目: 細目の字を 1 字替える", lambda R, c: R["sub"][u"細目の字"].__setitem__(u"イ1", R["sub"][u"細目の字"][u"イ1"] + u"。"), check_sub, u"細目の字")
M(u"細目: 細目の key が字の外", lambda R, c: R["sub"][u"行"][0].__setitem__(2, u"オ9"), check_sub, u"key でない")

# ---- i. 記録に文・会社名・コードが無い
M(u"clean[states]: 本の行の reason に日本語の長い文を入れる", lambda R, c: first_row(R, UNV)[1].__setitem__(3, u"決算の概況の文のような長い日本語の字がここに入ってしまった場合には止めるべきであり、記録に残してはいけない"), check_clean("states"), u"長い日本語")
M(u"clean[states]: 本の理由にコードの形の字を入れる", lambda R, c: first_book(R, False).__setitem__(u"理由", u"12" + u"3A"), check_clean("states"), u"証券コード")
M(u"clean[states]: 本に span の欄を足す", lambda R, c: first_book(R, True).__setitem__(u"span", u"x"), check_clean("states"), u"repo へ入れない欄")
M(u"clean[states]: 行に docID の形の字を入れる", lambda R, c: first_row(R, PNF)[1].__setitem__(3, u"S1" + u"00AB12"), check_clean("states"), u"docID")
M(u"clean[states]: 行に TDnet の番号の形の字を入れる", lambda R, c: first_row(R, PNF)[1].__setitem__(3, u"08" + u"12" + u"2" * 14), check_clean("states"), u"TDnet")
M(u"clean[states]: 行に pointer の形の字を入れる", lambda R, c: first_row(R, PNF)[1].__setitem__(3, u"jp" + u"pfs_cor"), check_clean("states"), u"pointer")
M(u"clean[states]: 行に会社名らしい字を入れる", lambda R, c: first_row(R, PNF)[1].__setitem__(3, u"株式" + u"会社"), check_clean("states"), u"会社名")
M(u"clean[states]: header の step を長い日本語の別の文にする", lambda R, c: R["states"].__setitem__(u"step", u"ここは留めた字ではない決算の概況の文のような長い日本語の字が入っている場合の例であり、記録に入れてはいけない文である"), check_clean("states"), u"長い日本語")
M(u"clean[states]: 欄の名前が長い日本語の文", lambda R, c: R["states"].__setitem__(u"この欄の名前は留めた字ではない決算の概況の文のような長い日本語になっていて、記録の欄の名前としては置けない", 1), check_clean("states"), u"長い日本語")
M(u"clean[states]: 字に鍵の形を入れる(script の check_clean)", lambda R, c: R["states"].__setitem__(u"profile", u"sk-" + u"a" * 20), check_clean("states"), u"check_clean")
M(u"clean[states]: 葉が文字でも数でもない(入れ子の object)", lambda R, c: R["states"].__setitem__(u"profile", object()), check_clean("states"), u"葉が")
M(u"clean[types]: 行の型の字を日本語の長い文にする", lambda R, c: R["types"][u"行"][0].__setitem__(4, u"型の字ではなく文のような長い日本語がここに入ってしまった場合の例になっていて、記録に残してはいけない文である"), check_clean("types"), u"長い日本語")
M(u"clean[types]: 行にコードの形の字を入れる", lambda R, c: R["types"][u"行"][0].__setitem__(4, u"12" + u"3A"), check_clean("types"), u"証券コード")
M(u"clean[sub]: 行の細目に文字列を入れる", lambda R, c: R["sub"][u"行"][0].__setitem__(2, u"イ" + u"9"), check_clean("sub"), u"細目の key")
M(u"clean[sub]: 補足を長い日本語の別の文にする", lambda R, c: R["sub"].__setitem__(u"補足", u"留めた字ではない決算の概況の文のような長い日本語の字がここに入っている場合の例であり、補足としては置けない文である"), check_clean("sub"), u"長い日本語")
M(u"clean[pop]: 行の様式を 7 つの外にする", lambda R, c: R["pop"][u"行"][0].__setitem__(2, u"acedxxxx"), check_clean("pop"), u"# ・群・様式")
M(u"clean[pop]: 行の sha を 64 字でなくす", lambda R, c: R["pop"][u"行"][0].__setitem__(3, u"abc"), check_clean("pop"), u"# ・群・様式")
M(u"clean[pop]: 置き場の字にコードの形を入れる", lambda R, c: R["pop"].__setitem__(u"置き場", u"12" + u"3A"), check_clean("pop"), u"証券コード")

# ---- j・k. 文書に書く数は記録から(記録側の変異で、その塊が赤になる)
M(u"文書: 型の集計 (ク) を +1(pred の S-9 と types の塊)", lambda R, c: R["types"][u"型の集計"].__setitem__(u"ク", R["types"][u"型の集計"][u"ク"] + 1), check_doc, u"塊 types")
M(u"文書: 型の集計 (ク) を +1 で S-9 の行", lambda R, c: R["types"][u"型の集計"].__setitem__(u"ク", R["types"][u"型の集計"][u"ク"] + 1), check_doc, u"塊 pred")
M(u"文書: 群 甲 の claim を +1(groups)", lambda R, c: set_key(R["states"][u"集計"], (u"群", u"甲", u"claim"), lambda v: v + 1), check_doc, u"塊 groups")
M(u"文書: 様式 acedifsm の字数の合計を +1(kinds)", lambda R, c: set_key(R["states"][u"集計"], (u"様式の種類", u"acedifsm", u"字数の合計"), lambda v: v + 1), check_doc, u"塊 kinds")
M(u"文書: A の claim が 0 の本を +1(books)", lambda R, c: set_key(R["states"][u"集計"], (u"A(甲 + 乙)", u"切れた本のうち claim が 0 の本"), lambda v: v + 1), check_doc, u"塊 books")
M(u"文書: A の reason no_subject を +1(reasons)", lambda R, c: set_key(R["states"][u"集計"], (u"A(甲 + 乙)", u"reason", UNV, u"no_subject"), lambda v: v + 1), check_doc, u"塊 reasons")
M(u"文書: B の reason に 1 つ足す(reasons の行が増える)", lambda R, c: R["states"][u"集計"][u"B(丙)"][u"reason"][UNV].__setitem__(u"zz_new", 1), check_doc, u"塊 reasons")
M(u"文書: A の VALUE_MISMATCH の行を +1(vm)", lambda R, c: set_key(R["states"][u"集計"], (u"A(甲 + 乙)", u"VALUE_MISMATCH の内訳", u"行"), lambda v: v + 1), check_doc, u"塊 vm")
M(u"文書: 乙の pointer の期 Prior1Year を +1(vm)", lambda R, c: set_key(R["states"][u"集計"], (u"群", u"乙", u"VALUE_MISMATCH の内訳", u"pointer の期", u"Prior1Year"), lambda v: v + 1), check_doc, u"塊 vm")
M(u"文書: 型の集計 (ア) を +1(types)", lambda R, c: R["types"][u"型の集計"].__setitem__(u"ア", R["types"][u"型の集計"][u"ア"] + 1), check_doc, u"塊 types")
M(u"文書: 型の字を替える(types)", lambda R, c: R["types"][u"型の字"].__setitem__(u"ウ", u"計画"), check_doc, u"塊 types")
M(u"文書: 細目の集計 イ1 を +1(sub)", lambda R, c: R["sub"][u"細目の集計"].__setitem__(u"イ1", 6), check_doc, u"塊 sub")
M(u"文書: 細目の字を替える(sub)", lambda R, c: R["sub"][u"細目の字"].__setitem__(u"カ3", u"丸め"), check_doc, u"塊 sub")
M(u"文書: 置いた記録の表と一致した ZIP を 399(pred の S-1)", lambda R, c: R["pop"].__setitem__(u"表と一致した ZIP", 399), check_doc, u"塊 pred")
M(u"文書: A の切れた本を +1(pred の S-2)", lambda R, c: set_key(R["states"][u"集計"], (u"A(甲 + 乙)", u"切れた"), lambda v: v + 1), check_doc, u"塊 pred")
M(u"文書: B の字数の合計を +1(pred の S-3)", lambda R, c: set_key(R["states"][u"集計"], (u"B(丙)", u"字数の合計"), lambda v: v + 1), check_doc, u"塊 pred")
M(u"文書: A の GROUNDED を +1(pred の S-4)", lambda R, c: set_key(R["states"][u"集計"], (u"A(甲 + 乙)", u"4 state", G), lambda v: v + 1), check_doc, u"塊 pred")
M(u"文書: B の POINTER_NOT_FOUND を -1(pred の S-5)", lambda R, c: set_key(R["states"][u"集計"], (u"B(丙)", u"4 state", PNF), lambda v: v - 1), check_doc, u"塊 pred")
M(u"文書: A の導出(formula)を +1(pred の S-6)", lambda R, c: set_key(R["states"][u"集計"], (u"A(甲 + 乙)", u"VALUE_MISMATCH の内訳", u"導出(formula)"), lambda v: v + 1), check_doc, u"塊 pred")
M(u"文書: 細目の集計 イ1 を +1(pred の S-8)", lambda R, c: R["sub"][u"細目の集計"].__setitem__(u"イ1", 6), check_doc, u"塊 pred")


# ======================================================================================================
# 試験
class RealRecordsTest(unittest.TestCase):
    u"""追跡される記録・封・文書に対する実物の検査。どれも問題の一覧が空。"""

    def test_a_1_the_population_is_the_seal_table_in_the_two_records(self):
        c = Ctx.get()
        R = fresh_records()
        self.assertEqual([], check_pop(R, c))
        self.assertEqual(400, len(SG.seal_table(c.seal)))

    def test_a_2_group_and_kind_counts_are_pinned_literally(self):
        R = fresh_records()
        self.assertEqual({u"甲": 50, u"乙": 200, u"丙": 150}, dict(GROUP_COUNTS))
        self.assertEqual({u"acedifsm": 43, u"acedjpsm": 203, u"anedjpsm": 4, u"scedifsy": 29, u"scedjpsm": 7, u"scedjpsy": 110, u"snedjpsy": 4}, dict(KIND_COUNTS))
        self.assertEqual(dict(GROUP_COUNTS), collections.Counter(b[u"群"] for b in R["states"][u"本"]))
        self.assertEqual(dict(KIND_COUNTS), collections.Counter(b[u"様式の種類"] for b in R["states"][u"本"]))

    def test_c_1_engine_zero_lines_and_the_two_scripts_are_unchanged_since_the_script_commit(self):
        self.assertEqual([], engine_problems())

    def test_c_2_headers_match_the_current_scripts_engine_and_history(self):
        c = Ctx.get()
        R = fresh_records()
        for kind in R:
            self.assertEqual([], header_problems(kind, R[kind], c.cur), kind)

    def test_d_1_books_are_whole_and_the_tally_is_recounted_from_the_rows(self):
        R = fresh_records()
        self.assertEqual([], book_problems(R["states"]))
        self.assertEqual([], recount_problems(R["states"]))

    def test_d_2_the_recount_pins_the_real_numbers_literally(self):
        u"""数え直しの自前の関数が、封の数(S-2〜S-6)と同じ数を出す(関数が恒等でないことの見張り)。"""
        R = fresh_records()
        books = R["states"][u"本"]
        a = count_books([b for b in books if b[u"群"] in (u"甲", u"乙")])
        b = count_books([b for b in books if b[u"群"] == u"丙"])
        self.assertEqual((239, 11, 133, 17), (a[u"切れた"], a[u"切れない"], b[u"切れた"], b[u"切れない"]))
        self.assertEqual((1204375, 445473), (a[u"字数の合計"], b[u"字数の合計"]))
        self.assertEqual((17697, 5405, 1898, 3980, 6414), (a[u"claim"], a[u"4 state"][G], a[u"4 state"][VM], a[u"4 state"][UNV], a[u"4 state"][PNF]))
        self.assertEqual((6834, 1229, 0, 855, 4750), (b[u"claim"], b[u"4 state"][G], b[u"4 state"][VM], b[u"4 state"][UNV], b[u"4 state"][PNF]))
        self.assertEqual((1273, 425, 220), (a[u"VALUE_MISMATCH の内訳"][u"% の数"], a[u"VALUE_MISMATCH の内訳"][u"導出(formula)"], a[u"VALUE_MISMATCH が 1 以上の本"]))
        self.assertEqual(0, b[u"VALUE_MISMATCH が 1 以上の本"])

    def test_f_1_the_sample_is_drawn_again_inside_the_gate(self):
        R = fresh_records()
        self.assertEqual([], sample_problems(R["states"], R["types"]))
        rows = vm_rows_of_a(R["states"])
        self.assertEqual(1898, len(rows))
        want = draw_sample(rows)
        self.assertEqual(120, len(want))
        self.assertEqual([r[0] for r in want], list(range(1, 121)))
        self.assertEqual(sorted(want, key=lambda r: (r[1], r[2], r[3])), want)               # 番号の昇順 = 行の順

    def test_g_1_types_are_counted_from_the_rows(self):
        R = fresh_records()
        self.assertEqual([], types_problems(R["types"]))
        self.assertEqual({u"ア": 58, u"イ": 21, u"ウ": 20, u"エ": 7, u"オ": 4, u"カ": 8, u"キ": 0, u"ク": 1, u"ケ": 1}, dict(R["types"][u"型の集計"]))

    def test_h_1_the_sub_reading_is_exactly_the_rows_of_four_types(self):
        R = fresh_records()
        self.assertEqual([], sub_problems(R["sub"], R["types"]))
        self.assertEqual(34, len(R["sub"][u"行"]))
        self.assertEqual({u"イ1": 5, u"イ2": 13, u"イ3": 3, u"オ1": 3, u"オ2": 1, u"カ1": 6, u"カ2": 1, u"カ3": 1, u"ケ1": 1}, dict(R["sub"][u"細目の集計"]))

    def test_i_1_the_records_hold_no_sentence_no_company_no_code(self):
        c = Ctx.get()
        R = fresh_records()
        for kind in R:
            self.assertEqual([], clean_problems(kind, R[kind], c.texts[kind]), kind)

    def test_j_1_the_eight_blocks_of_the_result_document_equal_the_rebuilt_tables(self):
        c = Ctx.get()
        R = fresh_records()
        self.assertEqual([], doc_problems(c.doc, R, c.seal))
        blocks = build_blocks(R, c.seal)
        self.assertEqual(list(BLOCK_NAMES), list(blocks))
        self.assertEqual([2 + 10, 2 + 4, 2 + 7, 2 + 4, 2 + 14, 2 + 3, 2 + 9, 2 + 9], [len(v) for v in blocks.values()])

    def test_k_1_the_prediction_judgements_are_pinned_literally(self):
        c = Ctx.get()
        R = fresh_records()
        lines = build_blocks(R, c.seal)[u"pred"][2:]
        judges = [ln.rstrip(u"|").rstrip().rsplit(u"| ", 1)[1] for ln in lines]
        self.assertEqual([u"当たり"] * 6 + [u"司令塔が比べた", u"読みで割れた(型の記録では幅の中・封の字のとおりでは幅の外)", u"当たり", u"当たり"], judges)
        parts = pred_parts(R["types"][u"型の集計"], R["sub"][u"細目の集計"], seal_bounds(seal_pred_cells(c.seal)))
        self.assertEqual(u"(ア) 58 + (イ) 21 = 79 行(65.8%)。(イ) を封の字のとおりの行(細目 イ1)だけにすると 58 + 5 = 63 行(52.5%)", parts[u"S-8"][0])
        self.assertEqual((u"1 行", u"当たり"), parts[u"S-9"])
        self.assertEqual((u"1 行", u"当たり"), parts[u"S-10"])
        s1 = lines[0].split(u" | ")
        self.assertEqual(u"表と一致した ZIP 400 / 400・ほかの cache の一覧(比べた folder 11)は前後で同じ", s1[3])

    def test_k_2_the_bounds_read_from_the_seal_are_pinned(self):
        c = Ctx.get()
        self.assertEqual(dict(BOUNDS_PIN), dict(seal_bounds(seal_pred_cells(c.seal))))
        self.assertEqual([u"S-%d" % i for i in range(1, 11)], list(seal_pred_cells(c.seal)))

    def test_l_1_the_cut_takes_the_later_heading_when_two_headings_follow_each_other(self):
        self.assertEqual([], cut_wins_problems(MS.cut_lines))

    def test_b_1_the_real_history_has_the_seal_before_the_scripts_before_the_records_the_document_and_this_gate(self):
        u"""記録 4 つ・結果の文書・この門のどれかが未 commit なら赤(足した commit が無い。skip にしない)。全部 commit された後で初めて緑。"""
        self.assertEqual([], order_problems_real())


class MutationTest(unittest.TestCase):
    u"""どの検査も、記録・文書・封の写しを 1 か所だけ変えた新しい写しで赤になる(実物の file は書き換えない)。"""

    def test_m_1_every_mutation_turns_its_check_red_with_the_expected_reason(self):
        c = Ctx.get()
        silent, wrong = [], []
        for check in set(m[2] for m in Mutations.rows):                          # 変異の前に、どの検査も実物で空であること
            self.assertEqual([], check(fresh_records(), c))
        for label, mut, check, tag in Mutations.rows:
            R = fresh_records()
            mut(R, c)
            got = guard(check, R, c)
            if not got:
                silent.append(label)
            elif not any(tag in p for p in got):
                wrong.append((label, tag, got[:2]))
        self.assertEqual([], silent)
        self.assertEqual([], wrong)

    def test_m_2_the_mutation_table_is_large_and_covers_every_check(self):
        n = len(Mutations.rows)
        self.assertGreaterEqual(n, 350)
        checks = set(m[2] for m in Mutations.rows)
        for fn in (check_pop, check_states, check_sample, check_types, check_sub, check_doc):
            self.assertIn(fn, checks)
        labels = [m[0] for m in Mutations.rows]
        for head in (u"header[pop]", u"header[states]", u"header[types]", u"header[sub]", u"clean[states]", u"clean[types]", u"clean[sub]", u"clean[pop]"):
            self.assertTrue(any(l.startswith(head) for l in labels), head)

    def test_m_3_each_mutation_gets_a_new_copy(self):
        R1, R2 = fresh_records(), fresh_records()
        self.assertIsNot(R1["states"], R2["states"])
        R1["states"][u"本"][0][u"字数"] += 1
        self.assertNotEqual(R1["states"][u"本"][0][u"字数"], R2["states"][u"本"][0][u"字数"])
        self.assertEqual([], check_states(R2, Ctx.get()))


def doc_lines_in_block(doc, name):
    lines = doc.split(u"\n")
    s = lines.index(u"<!-- 門:start %s -->" % name)
    e = lines.index(u"<!-- 門:end -->", s)
    return lines, s, e


def change_one_digit(line):
    i = [k for k, ch in enumerate(line) if ch.isdigit()][-1]
    return line[:i] + (u"0" if line[i] != u"0" else u"1") + line[i + 1:]


class DocMutationTest(unittest.TestCase):
    def _problems(self, doc, seal=None):
        c = Ctx.get()
        return guard(doc_problems, doc, fresh_records(), seal if seal is not None else c.seal)

    def test_j_2_one_digit_in_each_of_the_eight_blocks_turns_it_red(self):
        c = Ctx.get()
        for name in BLOCK_NAMES:
            lines, s, e = doc_lines_in_block(c.doc, name)
            for k in (s + 3, e - 1):                                    # 先頭の行(区切りの次)と最後の行
                orig = lines[k]
                self.assertEqual(1, c.doc.count(orig), (name, k))
                bad = lines[:k] + [change_one_digit(orig)] + lines[k + 1:]
                got = self._problems(u"\n".join(bad))
                self.assertTrue(any(u"塊 %s が" % name in p for p in got), (name, k, got[:2]))
                self.assertFalse(any(u"塊 %s が" % n2 in p for n2 in BLOCK_NAMES if n2 != name for p in got), (name, got))      # ほかの塊は赤にならない

    def test_j_3_a_changed_or_missing_or_unknown_block_name_turns_it_red(self):
        c = Ctx.get()
        for name in BLOCK_NAMES:
            start = u"<!-- 門:start %s -->" % name
            self.assertEqual(1, c.doc.count(start))
            got = self._problems(c.doc.replace(start, u"<!-- 門:start %sx -->" % name))
            self.assertTrue(any(u"知らない名前の塊" in p for p in got) and any(u"欠けている" in p for p in got), name)
            lines, s, e = doc_lines_in_block(c.doc, name)
            got = self._problems(u"\n".join(lines[:s] + lines[e + 1:]))
            self.assertTrue(any(u"塊 %s が欠けている" % name in p for p in got), name)
        dup = c.doc + u"\n<!-- 門:start pred -->\nx\n<!-- 門:end -->\n"
        self.assertTrue(self._problems(dup))

    def test_j_4_forbidden_words_docid_and_tdnet_numbers_turn_it_red(self):
        c = Ctx.get()
        for w in FORBIDDEN_WORDS:
            got = self._problems(c.doc + u"\n" + w + u"\n")
            self.assertTrue(any(u"禁止語 %s" % w in p for p in got), w)
        got = self._problems(c.doc + u"\n" + u"S1" + u"00AB12" + u"\n")
        self.assertTrue(any(u"docID" in p for p in got))
        got = self._problems(c.doc + u"\n" + u"08" + u"12" + u"3" * 14 + u"\n")
        self.assertTrue(any(u"TDnet" in p for p in got))

    def test_j_5_each_not_gated_mark_that_is_needed_turns_prose_red_when_removed(self):
        c = Ctx.get()
        self.assertEqual([], PR.prose_problems(c.doc))
        needed = 0
        for line in c.doc.split(u"\n"):
            if NOT_GATED in line and c.doc.count(line) == 1:
                bad = c.doc.replace(line, line.replace(NOT_GATED, u""))
                got = self._problems(bad)
                if any(u"【門なし】が無い" in p for p in got):
                    needed += 1
        self.assertGreaterEqual(needed, 3)
        sample = u"この行は 1234 の数を持つ散文。\n"                              # 外した形そのものを直接見る
        self.assertNotEqual([], PR.prose_problems(c.doc + u"\n" + sample))
        self.assertEqual([], PR.prose_problems(c.doc + u"\n" + sample.rstrip() + NOT_GATED + u"\n"))

    def test_j_6_the_document_must_name_the_seal_the_records_and_this_gate(self):
        c = Ctx.get()
        for need in (os.path.basename(SEAL_REL), SEAL_COMMIT_SHORT, GATE_REL) + tuple(os.path.basename(r) for r in RECORD_RELS):
            got = self._problems(c.doc.replace(need, u"〇"))
            self.assertTrue(any(u"%s を言っていない" % need in p for p in got), need)

    def test_j_7_a_changed_seal_prediction_turns_the_prediction_block_red(self):
        c = Ctx.get()
        sec = c.seal[c.seal.index(u"## §3"):c.seal.index(u"## §4")]
        for old, new in ((u"1,204,375", u"1,204,376"), (u"A 239 / 11", u"A 238 / 11"), (u"17,697 = 5,405", u"17,697 = 5,406"), (u"6,834 = 1,229", u"6,835 = 1,229"), (u"1,273 / 425", u"1,273 / 426"),
                         (u"66〜102 行", u"65〜102 行"), (u"0〜12 行", u"0〜11 行")):
            self.assertEqual(1, sec.count(old), old)
            seal2 = c.seal.replace(sec, sec.replace(old, new))
            self.assertNotEqual(seal2, c.seal)
            got = self._problems(c.doc, seal2)
            self.assertTrue(any(u"塊 pred が" in p for p in got), old)

    def test_k_3_the_bounds_check_goes_red_when_the_seal_bound_changes(self):
        c = Ctx.get()
        for old, new in ((u"66〜102 行", u"65〜102 行"), (u"66〜102 行", u"66〜103 行"), (u"0〜4 行", u"0〜5 行"), (u"0〜12 行", u"1〜12 行")):
            sec = c.seal[c.seal.index(u"## §3"):c.seal.index(u"## §4")]
            seal2 = c.seal.replace(sec, sec.replace(old, new))
            self.assertNotEqual(dict(BOUNDS_PIN), dict(seal_bounds(seal_pred_cells(seal2))), old)

    def test_k_4_s8_judgement_at_every_boundary_and_in_the_four_combinations(self):
        b = BOUNDS_PIN
        tc0 = collections.OrderedDict((t, 0) for t in TYPE_LETTERS)

        def run(x, y):
            tc = collections.OrderedDict(tc0)
            tc[u"ア"], tc[u"イ"] = 50, x - 50
            sc = collections.OrderedDict([(u"イ1", y - 50)])
            return pred_parts(tc, sc, b)[u"S-8"][1]
        mid = 80
        self.assertEqual(u"読みで割れた(型の記録では幅の外・封の字のとおりでは幅の中)", run(65, mid))
        self.assertEqual(u"当たり", run(66, mid))
        self.assertEqual(u"当たり", run(102, mid))
        self.assertEqual(u"読みで割れた(型の記録では幅の外・封の字のとおりでは幅の中)", run(103, mid))
        self.assertEqual(u"読みで割れた(型の記録では幅の中・封の字のとおりでは幅の外)", run(mid, 65))
        self.assertEqual(u"当たり", run(mid, 66))
        self.assertEqual(u"当たり", run(mid, 102))
        self.assertEqual(u"読みで割れた(型の記録では幅の中・封の字のとおりでは幅の外)", run(mid, 103))
        self.assertEqual(u"当たり", run(70, 90))                                   # 中中
        self.assertEqual(u"外れ", run(60, 110))                                    # 外外
        self.assertEqual(u"読みで割れた(型の記録では幅の中・封の字のとおりでは幅の外)", run(70, 60))     # 中外
        self.assertEqual(u"読みで割れた(型の記録では幅の外・封の字のとおりでは幅の中)", run(110, 90))    # 外中
        self.assertEqual(u"外れ", run(65, 65))
        self.assertEqual(u"外れ", run(103, 103))

    def test_k_5_s9_and_s10_judgement_at_the_boundaries(self):
        b = BOUNDS_PIN
        for n, want in ((0, u"当たり"), (4, u"当たり"), (5, u"外れ")):
            tc = collections.OrderedDict((t, 0) for t in TYPE_LETTERS)
            tc[u"ク"] = n
            self.assertEqual((u"%d 行" % n, want), pred_parts(tc, {u"イ1": 0}, b)[u"S-9"], n)
        for n, want in ((0, u"当たり"), (12, u"当たり"), (13, u"外れ")):
            tc = collections.OrderedDict((t, 0) for t in TYPE_LETTERS)
            tc[u"ケ"] = n
            self.assertEqual((u"%d 行" % n, want), pred_parts(tc, {u"イ1": 0}, b)[u"S-10"], n)

    def test_k_6_the_boundaries_reach_the_rendered_prediction_rows(self):
        c = Ctx.get()
        for key, n, word in ((u"ク", 4, u"当たり"), (u"ク", 5, u"外れ"), (u"ケ", 12, u"当たり"), (u"ケ", 13, u"外れ")):
            R = fresh_records()
            R["types"][u"型の集計"][key] = n
            lines = build_blocks(R, c.seal)[u"pred"]
            row = [ln for ln in lines if ln.startswith(u"| S-%d " % (9 if key == u"ク" else 10))][0]
            self.assertTrue(row.endswith(u"| %s |" % word), row)
        R = fresh_records()
        R["types"][u"型の集計"][u"ア"] = 45                                           # 45 + 21 = 66 は中・45 + 5 = 50 は外
        row = [ln for ln in build_blocks(R, c.seal)[u"pred"] if ln.startswith(u"| S-8 ")][0]
        self.assertTrue(row.endswith(u"幅の中・封の字のとおりでは幅の外) |"), row)
        R["types"][u"型の集計"][u"ア"] = 44                                           # 44 + 21 = 65 は外・44 + 5 は外
        row = [ln for ln in build_blocks(R, c.seal)[u"pred"] if ln.startswith(u"| S-8 ")][0]
        self.assertTrue(row.endswith(u"| 外れ |"), row)

    def test_k_7_s1_to_s6_judge_hit_only_when_every_number_equals_the_seal(self):
        c = Ctx.get()
        cases = collections.OrderedDict([
            (u"S-1", lambda R: R["pop"].__setitem__(u"ほかの cache の前後", dict(R["pop"][u"ほかの cache の前後"], **{u"変化なし": False}))),
            (u"S-2", lambda R: set_key(R["states"][u"集計"], (u"B(丙)", u"切れない"), lambda v: v + 1)),
            (u"S-3", lambda R: set_key(R["states"][u"集計"], (u"A(甲 + 乙)", u"字数の合計"), lambda v: v - 1)),
            (u"S-4", lambda R: set_key(R["states"][u"集計"], (u"A(甲 + 乙)", u"4 state", UNV), lambda v: v + 1)),
            (u"S-5", lambda R: set_key(R["states"][u"集計"], (u"B(丙)", u"claim"), lambda v: v + 1)),
            (u"S-6", lambda R: set_key(R["states"][u"集計"], (u"A(甲 + 乙)", u"VALUE_MISMATCH が 1 以上の本"), lambda v: v + 1))])
        for sid, mut in cases.items():
            R = fresh_records()
            mut(R)
            lines = build_blocks(R, c.seal)[u"pred"]
            for ln in lines[2:]:
                k = ln.split(u" | ")[0].lstrip(u"| ")
                if k == sid:
                    self.assertTrue(ln.endswith(u"| 外れ |"), ln)
                elif k in (u"S-1", u"S-2", u"S-3", u"S-4", u"S-5", u"S-6"):
                    self.assertTrue(ln.endswith(u"| 当たり |"), (sid, ln))

    def test_k_8_s2_is_a_miss_when_a_cut_failure_is_not_the_start_reason(self):
        c = Ctx.get()
        R = fresh_records()
        R["states"][u"集計"][u"A(甲 + 乙)"][u"切れない理由"][u"始まりなし"] -= 1
        R["states"][u"集計"][u"A(甲 + 乙)"][u"切れない理由"][u"終わりなし"] += 1
        row = [ln for ln in build_blocks(R, c.seal)[u"pred"] if ln.startswith(u"| S-2 ")][0]
        self.assertTrue(row.endswith(u"| 外れ |"), row)


class SealMutationTest(unittest.TestCase):
    u"""封の表(§1)の写しを 1 か所だけ変えると、母集団の検査が赤になる(封の file は書き換えない)。"""

    def _lines(self):
        c = Ctx.get()
        return c, [ln for ln in c.seal.split(u"\n") if SG.SEAL_TABLE_ROW.match(ln)]

    def test_a_3_one_character_in_a_seal_table_row_turns_the_population_check_red(self):
        c, rows = self._lines()
        self.assertEqual(400, len(rows))
        for k in (0, 57, 399):
            ln = rows[k]
            self.assertEqual(1, c.seal.count(ln))
            sha = re.search(r"`([0-9a-f]{64})`", ln).group(1)
            variants = [ln.replace(sha, _flip_char(sha)), ln.replace(u" | 甲 | ", u" | 乙 | ").replace(u" | 乙 | ", u" | 丙 | ") if k == 0 else ln.replace(u" | 丙 | ", u" | 甲 | ").replace(u" | 乙 | ", u" | 甲 | ")]
            for bad in variants:
                self.assertNotEqual(ln, bad)
                R = fresh_records()
                self.assertNotEqual([], guard(population_problems, c.seal.replace(ln, bad), R["pop"], R["states"]), (k, bad[:20]))

    def test_a_4_a_changed_preview_cell_in_the_seal_turns_the_per_book_check_red(self):
        c, rows = self._lines()
        for k in range(len(rows)):
            if u"| 切れた | " in rows[k]:
                ln = rows[k]
                m = re.search(r"\| 切れた \| (\d+) \|$", ln)
                bad = ln[:m.start(1)] + str(int(m.group(1)) + 1) + ln[m.end(1):]
                R = fresh_records()
                got = guard(population_problems, c.seal.replace(ln, bad), R["pop"], R["states"])
                self.assertTrue(any(u"claim が封の下見と違う" in p for p in got), got)
                bad = ln.replace(u"| 切れた |", u"| 切れない |")
                got = guard(population_problems, c.seal.replace(ln, bad), R["pop"], R["states"])
                self.assertTrue(any(u"切り出しが封の下見と違う" in p for p in got), got)
                break
        for k in range(len(rows)):
            if u"| 切れない | - |" in rows[k]:
                ln = rows[k]
                bad = ln.replace(u"| 切れない | - |", u"| 切れた | 5 |")
                R = fresh_records()
                got = guard(population_problems, c.seal.replace(ln, bad), R["pop"], R["states"])
                self.assertTrue(any(u"封の下見と違う" in p for p in got), got)
                break

    def test_a_5_a_seal_table_with_a_row_missing_is_red(self):
        c, rows = self._lines()
        R = fresh_records()
        self.assertNotEqual([], guard(population_problems, c.seal.replace(rows[10] + u"\n", u""), R["pop"], R["states"]))


def synth_repo(order):
    u"""使い捨ての repo。order = 'good' / 'records_first' / 'uncommitted' / 'scripts_first'。"""
    r = PR.Repo()
    scripts = ["measure/s1.py", "measure/s2.py"]
    others = ["fixtures/a.json", "fixtures/b.json", "docs/doc.md", "tests/gate.py"]
    if order == "scripts_first":
        for f in scripts:
            r.put(f)
        r.commit(*scripts)
    r.put("docs/seal.md")
    seal = r.commit("docs/seal.md")
    if order == "records_first":
        for f in others:
            r.put(f)
        r.commit(*others)
    if order != "scripts_first":
        for f in scripts:
            r.put(f)
        r.commit(*scripts)
    if order in ("good", "uncommitted"):
        for f in others:
            r.put(f)
        r.commit(*(others if order == "good" else others[:-1]))
        if order == "uncommitted":
            r.put(others[-1])
    return r, seal, scripts, others


class OrderTest(unittest.TestCase):
    def _run(self, order, seal_short=None):
        r, seal, scripts, others = synth_repo(order)
        return PR.order_problems(r.d, PREFIX, "docs/seal.md", seal_short or seal[:7], scripts, others)

    def test_b_2_a_good_order_is_green(self):
        self.assertEqual([], self._run("good"))

    def test_b_3_records_before_the_scripts_are_red(self):
        got = self._run("records_first")
        self.assertEqual(sorted(u"BEFORE_IMPL:" + f for f in ["fixtures/a.json", "fixtures/b.json", "docs/doc.md", "tests/gate.py"]), sorted(got))

    def test_b_4_an_uncommitted_file_is_red_not_skipped(self):
        self.assertEqual([u"UNCOMMITTED:tests/gate.py"], self._run("uncommitted"))

    def test_b_5_a_different_seal_sha_is_red(self):
        self.assertIn(u"SEAL_NOT_THE_SEALED", self._run("good", seal_short="abcdef0"))

    def test_b_6_scripts_before_the_seal_are_red(self):
        got = self._run("scripts_first")
        self.assertNotEqual([], got)
        self.assertTrue(any(p.startswith(u"IMPL_UNCOMMITTED:") or p.startswith(u"IMPL_NOT_AFTER_SEAL") for p in got), got)       # 封より後に足した script が無い

    def test_b_7_the_real_order_check_lists_the_four_records_the_document_and_this_gate(self):
        self.assertEqual(list(RECORD_RELS) + [DOC_REL, GATE_REL], order_others())
        self.assertEqual((u"fixtures/xbrl/tanshin_self/population_2026-11-14.json", u"fixtures/xbrl/tanshin_self/states_2026-11-14.json", u"fixtures/xbrl/tanshin_self/vm_types_2026-11-14.json",
                          u"fixtures/xbrl/tanshin_self/vm_types_subreading_2026-11-14.json"), RECORD_RELS)
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, r)) for r in RECORD_RELS + (DOC_REL, GATE_REL, STAGE_REL, SCRIPT_REL)))

    def test_b_8_the_real_order_failure_today_is_only_the_uncommitted_files(self):
        u"""この門を足す便の途中: 赤の理由が UNCOMMITTED だけであること(順序そのものの違反が混ざっていない)。commit の後は空。"""
        got = order_problems_real()
        self.assertTrue(all(p.startswith(u"UNCOMMITTED:") for p in got), got)


class EngineTest(unittest.TestCase):
    def _repo(self):
        r = PR.Repo()
        for rel in ("measure/s1.py", "measure/s2.py", "adapters/xbrl/x.py", "core/py/y.py", "measure/lib/z.py", "measure/inject.py", "measure/xbrl_tanshin_2026-11-09.py", "fixtures/xbrl/tanshin/a.json"):
            r.put(rel)
        added = r.commit("measure/s1.py", "measure/s2.py", "adapters/xbrl/x.py", "core/py/y.py", "measure/lib/z.py", "measure/inject.py", "measure/xbrl_tanshin_2026-11-09.py", "fixtures/xbrl/tanshin/a.json")
        r.put("docs/seal.md")
        r.commit("docs/seal.md")
        return r, added[:7]

    def _p(self, r, added):
        return engine_problems(root=r.d, added=added, seal_rel="docs/seal.md", script_rels=("measure/s1.py", "measure/s2.py"))

    def test_c_3_a_clean_range_is_green(self):
        r, added = self._repo()
        self.assertEqual([], self._p(r, added))

    def test_c_4_a_script_change_committed_or_not_is_red(self):
        r, added = self._repo()
        r.put("measure/s2.py")
        self.assertNotEqual([], self._p(r, added))                                # 未 commit の変更
        r.commit("measure/s2.py")
        self.assertNotEqual([], self._p(r, added))                                # commit 済み

    def test_c_5_an_engine_change_after_the_seal_is_red(self):
        for rel in ("adapters/xbrl/x.py", "core/py/y.py", "measure/lib/z.py", "measure/inject.py", "measure/xbrl_tanshin_2026-11-09.py", "fixtures/xbrl/tanshin/a.json"):
            r, added = self._repo()
            r.put(rel)
            r.commit(rel)
            self.assertNotEqual([], self._p(r, added), rel)

    def test_c_6_an_unknown_added_commit_is_red(self):
        r, added = self._repo()
        self.assertNotEqual([], self._p(r, u"0000000"))

    def test_c_7_the_script_added_commit_is_in_the_real_history(self):
        rc, out = PR.git_in(REPO, "rev-parse", "--verify", SCRIPT_ADDED_COMMIT + "^{commit}")
        self.assertEqual(0, rc)
        for rel in (STAGE_REL, SCRIPT_REL):
            self.assertTrue(PR.added_commits(REPO, PREFIX + rel)[-1].startswith(SCRIPT_ADDED_COMMIT), rel)


def synth_states():
    u"""A(甲・乙)の VALUE_MISMATCH が 135 行・B(丙)にも VALUE_MISMATCH を持つ使い捨ての states(本の順・行の順はわざと乱す)。"""
    def book(num, grp, n_vm, n_other):
        rows = [[s, 10 + s, VM] + [None] * 6 for s in range(n_vm)] + [[1000 + s, 5, UNV] + [None] * 6 for s in range(n_other)]
        random.Random(num).shuffle(rows)
        return {u"#": num, u"群": grp, u"行": rows}
    return {u"本": [book(3, u"甲", 50, 4), book(1, u"乙", 40, 3), book(5, u"丙", 30, 2), book(2, u"甲", 45, 5)]}


def sample_items_problems(fn):
    u"""script の sample_items(states)が、門の中で自前で引いた行と同じ(VALUE_MISMATCH が 120 行を超える合成の states)。120 行以下なら全部。"""
    out = []
    st = synth_states()
    want = draw_sample(vm_rows_of_a(st))
    if len(want) != 120 or len(vm_rows_of_a(st)) != 135:
        out.append(u"合成の states が 135 行・標本 120 行でない")
    try:
        got = [list(x) for x in fn(st)]
    except BaseException:                                                          # noqa: BLE001
        got = None
    if got != want:
        out.append(u"sample_items の出力が自前の引きと違う")
    small = {u"本": [b for b in synth_states()[u"本"] if b[u"#"] == 1]}
    want2 = draw_sample(vm_rows_of_a(small))
    try:
        got2 = [list(x) for x in fn(small)]
    except BaseException:                                                          # noqa: BLE001
        got2 = None
    if got2 != want2 or len(want2) != 40:
        out.append(u"sample_items の少ない行(全部)の出力が違う")
    return out


class SampleItemsTest(unittest.TestCase):
    def test_f_2_the_script_sample_items_equals_the_gate_own_draw_on_a_synthetic_states(self):
        self.assertEqual([], sample_items_problems(MS.sample_items))
        st = synth_states()
        got = MS.sample_items(st)
        first120 = [(i + 1,) + r for i, r in enumerate(vm_rows_of_a(st)[:120])]
        self.assertNotEqual(first120, [tuple(x) for x in got])                      # 先頭の 120 行ではない(本当に引いている)

    def test_f_3_a_wrong_sample_function_is_red(self):
        def first_rows(st):
            return [(i + 1,) + r for i, r in enumerate(vm_rows_of_a(st)[:120])]

        def other_seed(st):
            rows = vm_rows_of_a(st)
            return [(i + 1,) + rows[j] for i, j in enumerate(sorted(random.Random(1).sample(range(len(rows)), 120)))]

        def unsorted_idx(st):
            rows = vm_rows_of_a(st)
            return [(i + 1,) + rows[j] for i, j in enumerate(random.Random(20261114).sample(range(len(rows)), 120))]

        def b_included(st):
            rows = []
            for b in sorted(st[u"本"], key=lambda b: b[u"#"]):
                for r in sorted((r for r in b[u"行"] if r[2] == VM), key=lambda r: (r[0], r[1])):
                    rows.append((b[u"#"], r[0], r[1]))
            return [(i + 1,) + rows[j] for i, j in enumerate(sorted(random.Random(20261114).sample(range(len(rows)), 120)))]
        for fn in (first_rows, other_seed, unsorted_idx, b_included):
            self.assertNotEqual([], sample_items_problems(fn), fn.__name__)


class CutTest(unittest.TestCase):
    def test_l_2_a_script_that_takes_the_first_heading_is_red(self):
        def first_wins(lines):
            for i, ln in enumerate(lines):
                m = MS.HEAD_RE.match(ln)
                if m and not any(t in ln for t in MS.TOC_MARKS):
                    start, head = i, MS.HEADINGS.index(m.group(1))
                    break
            else:
                return None, None, MS.WHY_START
            for j in range(start + 1, len(lines)):
                if MS.END_RE.match(lines[j]):
                    return u"\n".join(lines[start:j]), head, None
            return None, None, MS.WHY_END
        self.assertNotEqual([], cut_wins_problems(first_wins))

        def toc_allowed(lines):
            start, head = None, None
            for i, ln in enumerate(lines):
                m = MS.HEAD_RE.match(ln)
                if m:
                    start, head = i, MS.HEADINGS.index(m.group(1))
            if start is None:
                return None, None, MS.WHY_START
            for j in range(start + 1, len(lines)):
                if MS.END_RE.match(lines[j]):
                    return u"\n".join(lines[start:j]), head, None
            return None, None, MS.WHY_END
        self.assertNotEqual([], cut_wins_problems(toc_allowed))

    def test_l_3_the_real_cut_lines_with_two_consecutive_headings_returns_the_later_one(self):
        text, head, why = MS.cut_lines([u"1.経営成績等の概況", u"1.当四半期決算に関する定性的情報", u"本文", u"2.次"])
        self.assertEqual((u"1.当四半期決算に関する定性的情報\n本文", 2, None), (text, head, why))


class WiringTest(unittest.TestCase):
    def test_n_1_this_gate_carries_no_docid_tdnet_number_known_code_or_reserved_name(self):
        self.assertEqual([], SG.name_problems(rels=(GATE_REL,)))
        self.assertEqual([], SG.reserved_problems(rels=(GATE_REL,)))

    def test_n_2_this_gate_carries_no_verify_call_and_no_closed_folder_names(self):
        src = read(GATE_REL)
        self.assertNotIn(u"verify_" + u"document(", src)
        self.assertNotIn(u"sgogi-coach" + u"-handoff", src)
        self.assertNotIn(ST.SKIP_CACHES[0], src)
        self.assertNotIn(u"urllib" + u".request", src)

    def test_n_3_names_that_existed_before_loading_are_put_back(self):
        import types
        marker = types.ModuleType("pswap_for_idmap")
        before = sys.modules.get("pswap_for_idmap")
        sys.modules["pswap_for_idmap"] = marker
        try:
            mod = load_module(SCRIPT_REL, "tanshin_self_script_reload_probe_for_result_gate")
            self.assertIs(marker, sys.modules["pswap_for_idmap"])
            self.assertIs(mod, sys.modules["tanshin_self_script_reload_probe_for_result_gate"])
        finally:
            if before is None:
                sys.modules.pop("pswap_for_idmap", None)
            else:
                sys.modules["pswap_for_idmap"] = before
            sys.modules.pop("tanshin_self_script_reload_probe_for_result_gate", None)


@unittest.skipUnless(os.environ.get("AUDIT_CORE_TSS_REMEASURE") == "1", u"材料から測り直す試験は AUDIT_CORE_TSS_REMEASURE=1 のときだけ走る")
class RemeasureTest(unittest.TestCase):
    def test_m_1_the_states_record_is_reproduced_from_the_material(self):
        u"""既定の材料(読むだけ)で ``run_states`` を走らせ、追跡の states の記録と(時間(秒)と HEAD の commit を除いて)同じ。本番の path には書かない。"""
        with tmpdir() as d:
            out = os.path.join(d, "states_remeasure.json")
            MS.run_states(out=out, say=lambda *a, **k: None)
            with io.open(out, encoding="utf-8") as fh:
                new = json.load(fh)
        old = jload(STATES_REL)
        for k in (u"時間(秒)", u"HEAD の commit"):
            new.pop(k)
            old.pop(k)
        self.assertEqual(sorted(old), sorted(new))
        for k in old:
            self.assertEqual(old[k], new[k], k)


if __name__ == "__main__":
    unittest.main()
