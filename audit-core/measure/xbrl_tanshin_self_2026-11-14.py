# -*- coding: utf-8 -*-
u"""封 docs/XBRL_TANSHIN_SELF_SEAL_2026-11-14.md §0-2・§2・§5 ― TSS(決算短信の概況の文を、同じ短信の添付の財務諸表(iXBRL)で確かめる)の測定。
**0 USD・通信なし・鍵は読まない・LLM は呼ばない。engine(``core/``・``adapters/``)は 1 行も変えない。**材料は置く script ``xbrl_tanshin_self_stage_2026-11-14.py`` が置いた folder の ZIP を読むだけ。

    python3 measure/xbrl_tanshin_self_2026-11-14.py states --out PATH [--material DIR] [--procs N]     # 400 本を切り出し・包み直し・P33E で判定 → fixtures/xbrl/tanshin_self/states_2026-11-14.json
    python3 measure/xbrl_tanshin_self_2026-11-14.py sample --states PATH --material DIR --sheet PATH   # A の VALUE_MISMATCH から 120 行を引き、読むための紙を repo の外に書く(標準出力は件数だけ)
    python3 measure/xbrl_tanshin_self_2026-11-14.py types --states PATH --typed PATH --out PATH        # 付けた型の file を確かめて vm_types_2026-11-14.json を書く

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない。封に無い決めは結果の報告に書いた):
- 切り出し(封 §0-2 の 3): ZIP の member が **ちょうど** ``XBRLData/Attachment/qualitative.htm`` のものを utf-8(strict)で読む → 2026-11-09 の便の ``html_to_lines`` を **呼んで**行にする → 各行に NFKC を掛け、前後の空白を落とし、
  空の行を捨てる → 始まり = 正規表現 ``^1\\s*\\.\\s*(経営成績等の概況|当中間決算に関する定性的情報|当四半期決算に関する定性的情報)`` に当たり、行の中に ``...`` も ``・・`` も無い行のうち最後 →
  終わり = 始まりより後で ``^2\\s*\\.\\s*[^\\d\\s]`` に当たる最初の行 → 文 = 始まりの行から終わりの行の手前までを ``\\n`` でつないだもの。
  切れない理由 = member なし / decode / 始まりなし / 終わりなし。ZIP として読めなければ止める(封に無い失敗の型は結果に混ぜない)。
- 包み直し(封 §0-2 の 4): 元の ZIP の member のうち ``XBRLData/Attachment/`` で始まり **file 名(最後の ``/`` の後)** が ``-ixbrl.htm`` で終わるものを、**元の member 名の順**(文字列の順)に、
  ``XBRL/PublicDoc/<file 名の末尾の -ixbrl.htm を _ixbrl.htm に替えたもの>`` として入れる(中身は 1 byte も変えない)。新しい名前が重なれば止める。サマリーは入れない。
  文は ``XBRL/PublicDoc/zz_overview_ixbrl.htm`` として **最後に** 入れる。ZIP の member の日時は固定(1980-01-01)・圧縮は deflate(包んだ ZIP の byte が決まる)。
- 判定: ``verify_document(包んだ ZIP, "P33E")``(``text`` は渡さない)。行は 2026-11-09 の便の ``profile_rows``・``row_entry`` を **呼んで**作る。
  数の claim = ``kind == "num"``。claim と raw の並びが対応したかも本ごとに ``対応`` に持つ。
- 集計は 行 から数える(切れた本だけが行を持つ)。「claim が 0 の本」「GROUNDED が 0 の本」は **切れた本のうち**(切れない本は claim が無いので別に ``切れない`` と数える)。
- 標本(封 §0-2 の 7): A(甲 + 乙)の VALUE_MISMATCH の行を (# の順・文の番号の順・位置の順)に並べ、``random.Random(20261114).sample(range(行の数), 120)`` を番号の順に。行の数が 120 に満たなければ全部。
- 記録は文・span・値・pointer の字・要素名・会社名・証券コードを持たない。時間(秒)は記録の中で 1 つの欄。ほかは 2 回走らせて byte で同じになる(本・辞書の順を固定)。
"""
from __future__ import print_function

import argparse
import collections
import importlib.util
import io
import json
import os
import random
import re
import subprocess
import sys
import time
import unicodedata
import zipfile

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


ST = load_module("xbrl_tanshin_self_stage_2026-11-14.py", "tanshin_self_stage_for_tanshin_self")      # 母集団の読み・置き場・止め方(同じ instance)
TS = load_module("xbrl_tanshin_2026-11-09.py", "tanshin_for_tanshin_self")                           # 2026-11-09 の便: html_to_lines・profile_rows・row_entry・集計の部品
Stop = ST.Stop

from adapters.xbrl import instance as I                 # noqa: E402
from adapters.xbrl import prose as PR                   # noqa: E402
from adapters.xbrl import verify_document as VD         # noqa: E402
from adapters.xbrl import vocabulary as V               # noqa: E402

SEAL_REL = ST.SEAL_REL
SEAL_COMMIT = ST.SEAL_COMMIT
SCRIPT_REL = "measure/xbrl_tanshin_self_2026-11-14.py"
STAGE_SCRIPT_REL = ST.SCRIPT_REL
TS_SCRIPT_REL = "measure/xbrl_tanshin_2026-11-09.py"
REC_DIR_REL = ST.REC_DIR_REL
POPULATION_REL = ST.POPULATION_REL
STATES_REL = REC_DIR_REL + "/states_2026-11-14.json"
TYPES_REL = REC_DIR_REL + "/vm_types_2026-11-14.json"
DOC_REL = "docs/XBRL_TANSHIN_SELF_RESULT_2026-11-14.md"

# ---- 封 §0-2 の決めごと(字で留める。門が封と照らす)
PROFILE = "P33E"
QUALITATIVE = "XBRLData/Attachment/qualitative.htm"
HEAD_RE = re.compile(u"^1\\s*\\.\\s*(経営成績等の概況|当中間決算に関する定性的情報|当四半期決算に関する定性的情報)")
END_RE = re.compile(u"^2\\s*\\.\\s*[^\\d\\s]")
HEADINGS = (u"経営成績等の概況", u"当中間決算に関する定性的情報", u"当四半期決算に関する定性的情報")
TOC_MARKS = (u"...", u"・・")
ATTACH_PREFIX = "XBRLData/Attachment/"
OLD_SUFFIX = "-ixbrl.htm"
NEW_SUFFIX = "_ixbrl.htm"
PUBLIC_DOC = "XBRL/PublicDoc/"
OVERVIEW_MEMBER = "XBRL/PublicDoc/zz_overview_ixbrl.htm"
TEXTBLOCK_NAME = "jpcrp_cor:ManagementAnalysisOfFinancialPositionOperatingResultsAndCashFlowsTextBlock"
OVERVIEW_HEAD = u'<html><body><ix:nonNumeric name="%s" contextRef="FilingDateInstant" escape="true">' % TEXTBLOCK_NAME
OVERVIEW_TAIL = u"</ix:nonNumeric></body></html>"
ZIP_DATE_TIME = (1980, 1, 1, 0, 0, 0)
SAMPLE_SEED = 20261114
SAMPLE_N = 120
A_GROUPS = (u"甲", u"乙")
B_GROUPS = (u"丙",)
WHY_MEMBER, WHY_DECODE, WHY_START, WHY_END = u"member なし", u"decode", u"始まりなし", u"終わりなし"
WHYS = (WHY_MEMBER, WHY_DECODE, WHY_START, WHY_END)
CUT_OK, CUT_NG = u"切れた", u"切れない"
STATES = TS.STATES
G, VM, UNV, PNF = STATES
#: 型(封 §0-2 の 7。字は封と同じ)
TYPES = collections.OrderedDict([
    (u"ア", u"セグメント・事業・地域・製品別の数を、全社の fact と比べた"),
    (u"イ", u"内訳・一部分・文の中で計算した率や差を、全体の fact と比べた"),
    (u"ウ", u"計画・予想・目標の数"),
    (u"エ", u"キャッシュ・フローの向き・増減の書き方"),
    (u"オ", u"定義の違い(同じ名前でも文の言う範囲が fact と違う)"),
    (u"カ", u"丸め・単位"),
    (u"キ", u"損失・マイナスの符号"),
    (u"ク", u"本当の差の候補(文が全社のその項目の当期の数を言っていて、同じ短信の財務諸表の値と違って見える)"),
    (u"ケ", u"読んでも分けられない")])
TYPED_BY = u"司令塔(AI の席)。人は読んでいない"
STATES_LIMITS = (
    u"材料は英文短信を出している会社から引いた 400 本で、上場会社全体の標本ではない(封 §6)",
    u"切れない本は測れていない(見出しの書き方の違い。規則は広げない)",
    u"中間(B)は engine が中間の期(InterimInstant・InterimDuration 等)を当期・前期として読めないので、「値が違う」が出ない。B の数は限界の記録で成績ではない",
    u"文と表が同じ誤りを共有していれば、この照合では見えない(同じ文書の中の照合)",
    u"engine が見るのは添付の財務諸表の fact だけ。サマリーの数(予想・配当など)は入れていない",
    u"NFKC を掛けた文を測っている(原文の全角・半角の違いは見ていない)",
    u"行は [文の番号, 位置, state, reason, pointer の期, formula の有無, 単位の族, 両期の fact を引く a−b, span に % を含む] だけで、文・span・値・要素名は持たない")


#: 本の ``行`` の 1 行の欄(2026-11-09 の便の ``row_entry`` の並び)
ROW_COLUMNS = (u"文の番号", u"位置", u"state", u"reason", u"pointer の期", u"formula の有無", u"単位の族", u"両期の fact を引く a−b", u"span に % を含む")


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


# ======================================================================================================
# 切り出し(封 §0-2 の 3)
def cut_lines(lines):
    u"""NFKC・strip 済みの空でない行の列から (文, 見出しの番号, 切れない理由)。始まり = 見出しに当たり ``...``・``・・`` を持たない行のうち最後。終わり = 始まりより後で最初の ``2.`` の行。"""
    start, head = None, None
    for i, ln in enumerate(lines):
        m = HEAD_RE.match(ln)
        if m and not any(t in ln for t in TOC_MARKS):
            start, head = i, HEADINGS.index(m.group(1))
    if start is None:
        return None, None, WHY_START
    for j in range(start + 1, len(lines)):
        if END_RE.match(lines[j]):
            return u"\n".join(lines[start:j]), head, None
    return None, None, WHY_END


def cut_html(h):
    u"""qualitative.htm の字から (文, 見出しの番号, 理由)。行にするのは 2026-11-09 の便の ``html_to_lines``(呼ぶ)。"""
    lines = []
    for ln in TS.html_to_lines(h):
        ln = unicodedata.normalize("NFKC", ln).strip()
        if ln:
            lines.append(ln)
    return cut_lines(lines)


def cut(zb):
    u"""ZIP の bytes から (文, 見出しの番号, 切れない理由)。member がちょうど ``QUALITATIVE`` でなければ member なし・utf-8(strict)で読めなければ decode。"""
    try:
        with zipfile.ZipFile(io.BytesIO(zb)) as z:
            if QUALITATIVE not in z.namelist():
                return None, None, WHY_MEMBER
            raw = z.read(QUALITATIVE)
    except zipfile.BadZipFile:
        raise Stop(u"**ZIP として読めない。止める**")
    try:
        h = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None, None, WHY_DECODE
    return cut_html(h)


# ======================================================================================================
# 包み直し(封 §0-2 の 4)。包んだ ZIP は memory の中だけ
def _info(name):
    zi = zipfile.ZipInfo(name, date_time=ZIP_DATE_TIME)
    zi.compress_type = zipfile.ZIP_DEFLATED
    return zi


def overview_html(text):
    return (OVERVIEW_HEAD + PR.prose_to_html(text) + OVERVIEW_TAIL).encode("utf-8")


def wrap(zb, text):
    u"""(包んだ ZIP の bytes, 入れた iXBRL の file の数)。サマリーは入れない・iXBRL の中身は 1 byte も変えない・文は最後。"""
    buf = io.BytesIO()
    names = []
    with zipfile.ZipFile(io.BytesIO(zb)) as z, zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as out:
        for info in sorted(z.infolist(), key=lambda i: i.filename):
            base = info.filename.rsplit(u"/", 1)[-1]
            if info.filename.startswith(ATTACH_PREFIX) and base.endswith(OLD_SUFFIX):
                new = PUBLIC_DOC + base[:-len(OLD_SUFFIX)] + NEW_SUFFIX
                if new in names or new == OVERVIEW_MEMBER:
                    raise Stop(u"**包み直しの名前が重なった。止める**")
                names.append(new)
                out.writestr(_info(new), z.read(info.filename))
        out.writestr(_info(OVERVIEW_MEMBER), overview_html(text))
    return buf.getvalue(), len(names)


# ======================================================================================================
# states
def judge_book(n, grp, kind, sha, zb):
    u"""1 本の記録(OrderedDict)。切れた本だけが行を持つ。"""
    book = collections.OrderedDict([(u"#", n), (u"群", grp), (u"様式の種類", kind), (u"ZIP の sha256", sha)])
    text, head, why = cut(zb)
    if text is None:
        book.update([(u"切り出し", CUT_NG), (u"理由", why), (u"見出しの番号", None), (u"字数", None), (u"入れた iXBRL の file の数", None), (u"fact の数", None),
                     (u"claim", 0), (u"対応", None), (u"行", [])])
        return book
    wrapped, nfiles = wrap(zb, text)
    nfacts = len(I.load_instance(wrapped)["facts"])
    rows, ok, ncl = TS.profile_rows(wrapped, None, wrapped, PROFILE)
    book.update([(u"切り出し", CUT_OK), (u"理由", None), (u"見出しの番号", head), (u"字数", len(text)), (u"入れた iXBRL の file の数", nfiles), (u"fact の数", nfacts),
                 (u"claim", ncl), (u"対応", bool(ok)), (u"行", [TS.row_entry(k, v) for k, v in rows.items()])])
    return book


def states_job(args):
    n, grp, kind, sha, path = args
    if not os.path.exists(path):
        raise Stop(u"**材料の ZIP が置き場に無い(# %d)。止める(置く script を先に)**" % n)
    with io.open(path, "rb") as fh:
        zb = fh.read()
    if ST.sha256_bytes(zb) != sha:
        raise Stop(u"**材料の ZIP の sha256 が封の表と違う(# %d)。止める**" % n)
    return judge_book(n, grp, kind, sha, zb)


def rows_of(books):
    return [r for b in books for r in b[u"行"]]


def block(books):
    u"""本の集まりの集計(行から数える)。「claim が 0 の本」などは切れた本のうち。"""
    cut_books = [b for b in books if b[u"切り出し"] == CUT_OK]
    rows = rows_of(cut_books)
    why = collections.Counter(b[u"理由"] for b in books if b[u"切り出し"] == CUT_NG)
    heads = collections.Counter(b[u"見出しの番号"] for b in cut_books)
    per = collections.Counter()
    for b in cut_books:
        c = collections.Counter(r[2] for r in b[u"行"])
        if not b[u"行"]:
            per[u"claim が 0 の本"] += 1
        if not c.get(G, 0):
            per[u"GROUNDED が 0 の本"] += 1
        if c.get(VM, 0) >= 1:
            per[u"VALUE_MISMATCH が 1 以上の本"] += 1
    return collections.OrderedDict([
        (u"本", len(books)), (u"切れた", len(cut_books)), (u"切れない", len(books) - len(cut_books)),
        (u"切れない理由", collections.OrderedDict((w, why.get(w, 0)) for w in WHYS)),
        (u"見出しの番号の本数", collections.OrderedDict((u"%d" % i, heads.get(i, 0)) for i in range(len(HEADINGS)))),
        (u"字数の合計", sum(b[u"字数"] for b in cut_books)),
        (u"入れた iXBRL の file の数の合計", sum(b[u"入れた iXBRL の file の数"] for b in cut_books)),
        (u"fact の数の合計", sum(b[u"fact の数"] for b in cut_books)),
        (u"claim", len(rows)), (u"4 state", TS.state_counts(rows)), (u"reason", TS.reason_counts(rows)),
        (u"VALUE_MISMATCH の内訳", TS.vm_breakdown(rows)),
        (u"切れた本のうち claim が 0 の本", per.get(u"claim が 0 の本", 0)), (u"切れた本のうち GROUNDED が 0 の本", per.get(u"GROUNDED が 0 の本", 0)),
        (u"VALUE_MISMATCH が 1 以上の本", per.get(u"VALUE_MISMATCH が 1 以上の本", 0)),
        (u"claim と raw の並びが対応しなかった本", sum(1 for b in cut_books if not b[u"対応"]))])


def tally(books):
    u"""群ごと(甲・乙・丙)・A(甲 + 乙)・B(丙)・様式の種類ごと。行から数える。"""
    out = collections.OrderedDict()
    out[u"群"] = collections.OrderedDict((g, block([b for b in books if b[u"群"] == g])) for g in ST.GROUP_COUNTS if any(b[u"群"] == g for b in books))
    out[u"A(甲 + 乙)"] = block([b for b in books if b[u"群"] in A_GROUPS])
    out[u"B(丙)"] = block([b for b in books if b[u"群"] in B_GROUPS])
    out[u"様式の種類"] = collections.OrderedDict((k, block([b for b in books if b[u"様式の種類"] == k])) for k in sorted(set(b[u"様式の種類"] for b in books)))
    return out


def check_clean(rec, text, key_value=None):
    u"""記録に repo へ入れない欄・鍵らしい字が無いか(あれば止める)。"""
    bad = sorted(set(k for k in TS.RUN.walk_keys(rec) if k in TS.RUN.FORBIDDEN_KEYS))
    if bad:
        raise Stop(u"**記録に repo へ入れない欄がある: %s。止める**" % u",".join(bad))
    leaks = ST.key_leaks(text.replace(SEAL_REL, u""), key_value)
    if leaks:
        raise Stop(u"**鍵らしい字が記録に在る(%s)。書かずに止める**" % u" / ".join(sorted(set(leaks))))


def material_dir(material, out, root=ROOT):
    u"""材料の置き場。既定は本番の folder。本番の記録(``STATES_REL``)を書くときは本番の folder でなければ止める。"""
    prod = os.path.abspath(ST.default_cache_dir())
    mat = os.path.abspath(material) if material else prod
    if os.path.abspath(out) == os.path.abspath(os.path.join(root, STATES_REL)) and mat != prod:
        raise Stop(u"**本番の記録を使い捨ての材料から作らない。止める**")
    return mat, mat == prod


def run_states(root=ROOT, procs=1, out=None, material=None, say=print, population=None, key_value=None, clock=time.time, shape=None):
    if out is None:
        raise Stop(u"**--out を指定する。止める**")
    out = os.path.abspath(out)
    mat, prod = material_dir(material, out, root)
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    n_rows, groups = shape or (ST.N_ROWS, ST.GROUP_COUNTS)               # 試験が小さい表で試すときだけ shape を渡す
    pop = ST.validate_population(population if population is not None else ST.read_population(root), n_rows, groups)
    for (n, _g, _k, sha) in pop:
        if not os.path.exists(os.path.join(mat, sha + u".zip")):
            raise Stop(u"**材料の ZIP が置き場に無い(# %d)。何も書かずに止める(置く script を先に)**" % n)
    before = ST.names_snapshot(mat)
    jobs = [(n, g, k, sha, os.path.join(mat, sha + u".zip")) for (n, g, k, sha) in pop]
    say(u"states %d 本 × %s ― procs %d" % (len(jobs), PROFILE, procs))
    t0 = clock()
    books = TS.NF.map_pool(states_job, jobs, procs)
    elapsed = clock() - t0
    after = ST.names_snapshot(mat)
    if before != after:
        raise Stop(u"**材料の置き場の件数か名前が変わった。記録を書かずに止める**")
    rec = collections.OrderedDict()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"TSS(決算短信の概況の文を同じ短信の添付の財務諸表で確かめる)― 400 本の切り出し・包み直し・判定(0 USD・通信なし)"
    rec[u"HEAD の commit"] = ST.git_head(root)
    rec[u"この script の sha256"] = ST.sha256_file(os.path.abspath(__file__))
    rec[u"置く script の sha256"] = ST.sha256_file(os.path.join(HERE, os.path.basename(STAGE_SCRIPT_REL)))
    rec[u"2026-11-09 の便の script の sha256"] = ST.sha256_file(os.path.join(HERE, os.path.basename(TS_SCRIPT_REL)))
    rec[u"engine の指紋"] = VD.engine_fingerprint()
    rec[u"profile"] = PROFILE
    rec[u"材料"] = collections.OrderedDict([
        (u"置き場", ST.display_path(mat) if prod else u"使い捨ての置き場(本番の folder ではない)"), (u"表と一致した ZIP", len(pop)),
        (u"置き場の一覧の前後", collections.OrderedDict([(u"前", list(before)), (u"後", list(after)), (u"変化なし", before == after)]))])
    rec[u"切り出し"] = collections.OrderedDict([
        (u"member", QUALITATIVE), (u"始まりの規則", HEAD_RE.pattern), (u"終わりの規則", END_RE.pattern), (u"目次の印(行に在れば始まりにしない)", list(TOC_MARKS)),
        (u"見出しの番号", list(HEADINGS)), (u"NFKC", True), (u"行にする関数", u"2026-11-09 の便の html_to_lines(呼ぶ)")])
    rec[u"包み直し"] = collections.OrderedDict([
        (u"入れる member", u"XBRLData/Attachment/ の下で file 名が -ixbrl.htm で終わるもの(元の member 名の順)"), (u"新しい名前", PUBLIC_DOC + u"<file 名の末尾を _ixbrl.htm に替えたもの>"),
        (u"文の member", OVERVIEW_MEMBER), (u"文の要素", u"経営分析の節の TextBlock(要素名は script の TEXTBLOCK_NAME。長い英字なので記録には書かない)"), (u"サマリー", u"入れない"), (u"包んだ ZIP", u"memory の中だけ(どこにも書かない)")])
    rec[u"本の数"] = len(books)
    rec[u"集計"] = tally(books)
    rec[u"限界"] = list(STATES_LIMITS)
    rec[u"行の欄"] = list(ROW_COLUMNS)
    rec[u"時間(秒)"] = round(elapsed, 1)
    rec[u"key_leaks"] = []
    rec[u"本"] = books
    text = TS.dumps_states(rec)
    check_clean(rec, text, key_value)
    ST.write_text_exclusive(out, text)
    say(u"-> %s(本 %d)" % (os.path.basename(out), len(books)))
    return rec


# ======================================================================================================
# sample(封 §0-2 の 7)
def inside_repo(path, repo=None):
    u"""path が git の木(repo の中・または git が「木の中」と答える場所)の中なら真。読むための紙(文を持つ)を repo の中に書かせない。"""
    real = os.path.realpath(path)
    top = os.path.realpath(repo or os.path.dirname(ROOT))
    if real == top or real.startswith(top + os.sep):
        return True
    d = real if os.path.isdir(real) else os.path.dirname(real)
    while d and not os.path.isdir(d):
        nd = os.path.dirname(d)
        if nd == d:
            break
        d = nd
    try:
        r = subprocess.run(["git", "-C", d, "rev-parse", "--is-inside-work-tree"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except OSError:
        return False
    return r.returncode == 0 and r.stdout.strip() == b"true"


def vm_rows_a(states):
    u"""A(甲 + 乙)の VALUE_MISMATCH の行 [(本の #, 文の番号, 位置)]。# の順・文の番号の順・位置の順。"""
    out = []
    for b in sorted(states[u"本"], key=lambda b: b[u"#"]):
        if b[u"群"] not in A_GROUPS:
            continue
        for r in sorted((r for r in b[u"行"] if r[2] == VM), key=lambda r: (r[0], r[1])):
            out.append((b[u"#"], r[0], r[1]))
    return out


def pick_sample(n_rows, seed=SAMPLE_SEED, k=SAMPLE_N):
    u"""行の数 n_rows から k 行の番号(昇順)。k に満たなければ全部。``random.Random(seed).sample(range(n_rows), k)`` を番号の順に。"""
    if n_rows <= k:
        return list(range(n_rows))
    return sorted(random.Random(seed).sample(range(n_rows), k))


def sample_items(states):
    u"""[(標本の番号(1 から), 本の #, 文の番号, 位置)]。"""
    rows = vm_rows_a(states)
    return [(i + 1,) + rows[j] for i, j in enumerate(pick_sample(len(rows)))]


def load_json(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def sheet_text(item, claim, sentence_text):
    n, num, si, pos = item
    return u"\n".join([
        u"=== 標本 %d / 本 # %d / 文 %d / 位置 %d ===" % (n, num, si, pos),
        u"文: %s" % sentence_text,
        u"span: %s" % claim["span"],
        u"読んだ値: %s %s" % (claim["value"], claim["unit"]),
        u"state: %s  reason: %s" % (claim["state"], claim["reason"]),
        u"結んだ先: %s" % u" , ".join(claim["pointers"] or []),
        u"その値: %s" % claim["recomputed"], u"", u""])


def run_sample(states_path, material, sheet, root=ROOT, say=print, repo=None, population=None):
    if inside_repo(sheet, repo):
        raise Stop(u"**--sheet が repo の中(または git の木の中)。文を持つ紙は repo の外に書く。止める**")
    sheet = os.path.abspath(sheet)
    if os.path.exists(sheet):
        raise Stop(u"**--sheet が既に在る。止める**")
    states = load_json(states_path)
    items = sample_items(states)
    pop = dict((r[0], r) for r in (population if population is not None else ST.validate_population(ST.read_population(root))))
    mat = os.path.abspath(material)
    by_book = collections.OrderedDict()
    for it in items:
        by_book.setdefault(it[1], []).append(it)
    chunks = {}
    for num, its in by_book.items():
        _n, _g, _k, sha = pop[num]
        with io.open(os.path.join(mat, sha + u".zip"), "rb") as fh:
            zb = fh.read()
        if ST.sha256_bytes(zb) != sha:
            raise Stop(u"**材料の ZIP の sha256 が封の表と違う(# %d)。止める**" % num)
        text, _h, why = cut(zb)
        if text is None:
            raise Stop(u"**標本の本が切れない(# %d)。記録と合わない。止める**" % num)
        wrapped, _nf = wrap(zb, text)
        nums, texts = TS.R.build_raw_claims(wrapped, V.PROFILES[PROFILE])
        raws = nums + texts
        cl = VD.verify_document(wrapped, PROFILE)["claims"]
        if len(cl) != len(raws) or any(c["id"] != r["id"] for c, r in zip(cl, raws)):
            raise Stop(u"**claim と raw の並びが対応しない(# %d)。止める**" % num)
        sents = TS.RUN.sentence_list(wrapped, V.PROFILES[PROFILE])
        keyed = dict(((r["sentence"], r["pos"]), c) for c, r in zip(cl, raws) if c["kind"] == "num")
        for it in its:
            c = keyed.get((it[2], it[3]))
            if c is None or c["state"] != VM:
                raise Stop(u"**標本の行が記録と合わない(標本 %d)。止める**" % it[0])
            chunks[it[0]] = sheet_text(it, c, sents[it[2]])
    d = os.path.dirname(sheet)
    if d:
        os.makedirs(d, exist_ok=True)
    with io.open(sheet, "w", encoding="utf-8", newline="") as fh:
        fh.write(u"".join(chunks[it[0]] + u"\n" for it in items))
    say(u"A の VALUE_MISMATCH の行 %d・標本 %d 行・本 %d" % (len(vm_rows_a(states)), len(items), len(by_book)))
    return items


# ======================================================================================================
# types
def read_typed(path):
    u"""1 行に「標本の番号 TAB 型の字」。{番号: 型}。形が違う・番号が重なる・型が 9 つの外なら止める。"""
    out = {}
    with io.open(path, encoding="utf-8") as fh:
        for ln in fh.read().split(u"\n"):
            if not ln.strip():
                continue
            parts = ln.rstrip(u"\r").split(u"\t")
            if len(parts) != 2 or not re.fullmatch(r"[0-9]+", parts[0]) or parts[1] not in TYPES:
                raise Stop(u"**型の file の行が「番号 TAB 型の字(ア〜ケ)」でない。止める**")
            k = int(parts[0])
            if k in out:
                raise Stop(u"**型の file に同じ標本の番号が 2 行ある。止める**")
            out[k] = parts[1]
    return out


def run_types(states_path, typed_path, out, root=ROOT, say=print, key_value=None):
    out = os.path.abspath(out)
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。止める**" % os.path.basename(out))
    states = load_json(states_path)
    items = sample_items(states)
    typed = read_typed(typed_path)
    if sorted(typed) != [it[0] for it in items]:
        raise Stop(u"**型の file の標本の番号が標本の行(%d 行)とそろわない。止める**" % len(items))
    counts = collections.Counter(typed.values())
    rec = collections.OrderedDict()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"TSS ― A の VALUE_MISMATCH の標本の型分け(0 USD)"
    rec[u"HEAD の commit"] = ST.git_head(root)
    rec[u"この script の sha256"] = ST.sha256_file(os.path.abspath(__file__))
    rec[u"states の記録の sha256"] = ST.sha256_file(os.path.abspath(states_path))
    rec[u"型を付けた席"] = TYPED_BY
    rec[u"盲検"] = u"盲検ではない(封の予測を知ったうえで付けた)。(ク) は候補で、紙面で確かめていない"
    rec[u"標本の規則"] = collections.OrderedDict([
        (u"母集団", u"A(甲 + 乙)の VALUE_MISMATCH の行を、# の順・文の番号の順・位置の順に並べた"), (u"種", SAMPLE_SEED),
        (u"引き方", u"random.Random(種).sample(range(行の数), 標本の数) を番号の順に。行の数が標本の数に満たなければ全部"),
        (u"A の VALUE_MISMATCH の行の数", len(vm_rows_a(states))), (u"標本の数", len(items))])
    rec[u"型の字"] = collections.OrderedDict(TYPES)
    rec[u"型の集計"] = collections.OrderedDict((t, counts.get(t, 0)) for t in TYPES)
    rec[u"行の欄"] = [u"標本の番号", u"本の #", u"文の番号", u"位置", u"型"]
    rec[u"行"] = [[it[0], it[1], it[2], it[3], typed[it[0]]] for it in items]
    rec[u"key_leaks"] = []
    text = ST.dumps_record(rec)
    check_clean(rec, text, key_value)
    ST.write_text_exclusive(out, text)
    say(u"-> %s(標本 %d 行)" % (os.path.basename(out), len(items)))
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    a = sub.add_parser("states")
    a.add_argument("--root", default=ROOT)
    a.add_argument("--out", required=True)
    a.add_argument("--material", default=None)
    a.add_argument("--procs", type=int, default=1)
    b = sub.add_parser("sample")
    b.add_argument("--root", default=ROOT)
    b.add_argument("--states", required=True)
    b.add_argument("--material", required=True)
    b.add_argument("--sheet", required=True)
    c = sub.add_parser("types")
    c.add_argument("--root", default=ROOT)
    c.add_argument("--states", required=True)
    c.add_argument("--typed", required=True)
    c.add_argument("--out", required=True)
    a_ = ap.parse_args(argv)
    if a_.cmd == "states":
        run_states(root=a_.root, procs=a_.procs, out=a_.out, material=a_.material)
    elif a_.cmd == "sample":
        run_sample(a_.states, a_.material, a_.sheet, root=a_.root)
    elif a_.cmd == "types":
        run_types(a_.states, a_.typed, a_.out, root=a_.root)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
