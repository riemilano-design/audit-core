# -*- coding: utf-8 -*-
u"""封 docs/XBRL_KAM_SEAL_2026-11-15.md §0-2・§1・§2・§5 ― KAM(有価証券報告書の監査報告書の「監査上の主要な検討事項」の文を、同じ有報の fact で確かめる)の測定。
**0 USD・通信なし・鍵は読まない・LLM は呼ばない。engine(``core/``・``adapters/``)と ``measure/lib/`` は 1 行も変えない。**材料は ``~/.cache/audit-core/`` の 3 つの folder の ``.zip`` を読むだけ(1 file も足さない・写さない)。
母集団の読み・止め方・書き方・標本の引き方・紙の置き場の検査は、TSS の script ``xbrl_tanshin_self_2026-11-14.py``(以下 TSS)と 2026-11-09 の便の関数を **呼ぶ**(書き写さない)。

    python3 measure/xbrl_kam_2026-11-15.py population [--out PATH] [--cache-base DIR]                    # 封 §1 の 201 本を 3 つの folder から sha256 で探し、母集団の記録を書く
    python3 measure/xbrl_kam_2026-11-15.py states [--out PATH] [--cache-base DIR] [--procs N]             # 201 本の連結・単体の KAM の文を切り出し、P33E で判定して記録を書く
    python3 measure/xbrl_kam_2026-11-15.py sheet --states PATH --sheet PATH [--cache-base DIR]            # 読む行の文・span・値・結んだ先を repo の外の紙に書く(標準出力は件数だけ)
    python3 measure/xbrl_kam_2026-11-15.py types --states PATH --typed PATH [--out PATH]                  # 司令塔が付けた型の file を確かめて read_types_2026-11-15.json を書く

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない。封に無い決めはここに書き、報告にも書いた):
- 材料の探し方(封 §0-2 の 6): 3 つの folder(甲 = ``edinet``・乙 = ``edinet-fresh-2026-10-21``・丙 = ``edinet-prior-2026-11-02``)の直下の ``*.zip`` を名前の順に読み、byte の sha256 が封の表に在るものを選ぶ。
  file 名(docID)は使わず、記録にも標準出力にも書かない。201 本そろわなければ止める。同じ sha256 が 2 か所に在る(封 §0-1 の 1 は重なり 0)・表の群と違う folder に在る本が 1 本でも在れば止める(封に無い守り。止めるだけで数は変えない)。
  3 つの folder の一覧(件数と名前の sha256)の前後が違えば、記録を書かずに止める。
- 切り出し(封 §0-2 の 3): 名前に ``/AuditDoc/`` を含み ``.htm`` で終わる member を名前の順に utf-8(strict)で全部読む(1 つでも読めなければ 切れない(decode))→ 各 file で
  ``<ix:nonNumeric\\b[^>]*\\bname="<札の名前>"[^>]*>`` の最初の一致 → 一致の在る file が 0 = 札なし・2 以上 = 札が複数 → 始まりの札に ``continuedAt`` = 続きあり →
  深さを数えて終わりを探し、閉じなければ 閉じない → 塊を 2026-11-09 の便の ``html_to_lines`` で行にし、NFKC・前後の空白を落とし・空の行を捨てて ``\\n`` でつなぐ → 空なら 空。
  member が 1 つも無い本は「一致の在る file が 0」なので 札なし。ZIP として読めなければ止める(封に無い失敗の型は結果に混ぜない)。
- 判定(封 §0-2 の 4): ``verify_document(元の ZIP, "P33E", text=文)``。連結の文と単体の文は別々に 1 回ずつ。行は 2026-11-09 の便の ``profile_rows``・``row_entry`` を **呼んで**作り、10 欄目
  「pointer の字のどれかに ``NonConsolidatedMember`` を含む(真偽)」を足す。数の claim = ``kind == "num"``。claim と raw の並びが対応したかも側ごとに ``対応`` に持つ。
  raw との対応を取るために、文を差し替えた ZIP を ``adapters.xbrl.prose.build_modified_zip``(engine の入口。memory の中だけ)で作って ``profile_rows`` に渡す(2026-11-09 の便と同じ)。
- 集計は 行 から数える(切れた側だけが行を持つ)。「claim が 0 の本」「GROUNDED が 0 の本」は切れた本のうち。連結と単体は足さない。
- 読む行(封 §0-2 の 7): V 連結・V 単体・G 単体は全部の行、G 連結は (# の順・文の番号の順・位置の順)に並べた行から ``random.Random(20261115).sample(range(行の数), 60)`` を番号の順に(TSS の ``pick_sample``)。
  読む行は組ごとの通し番号(1 から)で呼ぶ。型の file は 1 行に「組 TAB 通し番号 TAB 型」、型が (b) の行だけ「TAB 違うもの(項目 / 範囲 / 側 / 期)」を足す。
- 記録は文・span・値・pointer の字・要素名・会社名・証券コード・docID を持たない。時間(秒)は記録の中で 1 つの欄。ほかは 2 回走らせて byte で同じになる(本・辞書の順を固定)。
"""
from __future__ import print_function

import argparse
import collections
import importlib.util
import io
import os
import re
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


TSS = load_module("xbrl_tanshin_self_2026-11-14.py", "tanshin_self_for_kam")                           # TSS の script(標本の引き方・紙の置き場の検査・止め方)
ST = TSS.ST                                                                                              # 置く script(同じ instance。止め方・書き方・sha256・一覧の前後)
TS = TSS.TS                                                                                              # 2026-11-09 の便(html_to_lines・profile_rows・row_entry・集計の部品)
Stop = ST.Stop

from adapters.xbrl import prose as PR                   # noqa: E402
from adapters.xbrl import recipes as R                  # noqa: E402
from adapters.xbrl import verify_document as VD         # noqa: E402
from adapters.xbrl import vocabulary as V               # noqa: E402

SEAL_REL = "docs/XBRL_KAM_SEAL_2026-11-15.md"
SEAL_COMMIT = "497a4661"
SCRIPT_REL = "measure/xbrl_kam_2026-11-15.py"
TSS_SCRIPT_REL = TSS.SCRIPT_REL
TS_SCRIPT_REL = TSS.TS_SCRIPT_REL
REC_DIR_REL = "fixtures/xbrl/kam"
POPULATION_REL = REC_DIR_REL + "/population_2026-11-15.json"
STATES_REL = REC_DIR_REL + "/states_2026-11-15.json"
TYPES_REL = REC_DIR_REL + "/read_types_2026-11-15.json"
DOC_REL = "docs/XBRL_KAM_RESULT_2026-11-15.md"

# ---- 封 §0-1・§0-2 の決めごと(字で留める。門が封と照らす)
PROFILE = "P33E"
N_ROWS = 201
GROUP_COUNTS = collections.OrderedDict([(u"甲", 67), (u"乙", 40), (u"丙", 94)])
#: 群と cache の folder(封 §0-1 の 2)。folder の名前は記録に書かない
CACHES = collections.OrderedDict([(u"甲", "edinet"), (u"乙", "edinet-fresh-2026-10-21"), (u"丙", "edinet-prior-2026-11-02")])
#: 文の種類 → 札の名前(封 §0-2 の 3)
SIDES = collections.OrderedDict([
    (u"連結", "jpcrp_cor:KeyAuditMattersConsolidatedTextBlock"),
    (u"単体", "jpcrp_cor:KeyAuditMattersNonConsolidatedTextBlock")])
AUDIT_MARK = "/AuditDoc/"
AUDIT_SUFFIX = ".htm"
START_RE = r'<ix:nonNumeric\b[^>]*\bname="%s"[^>]*>'
DEPTH_RE = re.compile(r'<ix:nonNumeric\b[^>]*?(/?)>|</ix:nonNumeric>')
CONTINUED = "continuedAt"
NONCONSOLIDATED_MARK = "NonConsolidatedMember"
WHY_DECODE, WHY_NOTAG, WHY_MANY, WHY_CONT, WHY_OPEN, WHY_EMPTY = u"decode", u"札なし", u"札が複数", u"続きあり", u"閉じない", u"空"
WHYS = (WHY_DECODE, WHY_NOTAG, WHY_MANY, WHY_CONT, WHY_OPEN, WHY_EMPTY)
CUT_OK, CUT_NG = u"切れた", u"切れない"
STATES = TS.STATES
G, VM, UNV, PNF = STATES
#: 読む行(封 §0-2 の 7)
READ_SEED = 20261115
READ_N = 60
V_CONS, V_NON, G_CONS, G_NON = u"V 連結", u"V 単体", u"G 連結", u"G 単体"
#: 読みの組 → (文の種類, state, 引くか)
READ_SETS = collections.OrderedDict([
    (V_CONS, (u"連結", VM, False)), (V_NON, (u"単体", VM, False)), (G_CONS, (u"連結", G, True)), (G_NON, (u"単体", G, False))])
#: V の行の型(封 §0-2 の 7。字は封と同じ)
TYPES_V = collections.OrderedDict([
    (u"ア", u"一部分の数(セグメント・子会社・事業・資産のグループ・相手先・内訳)を、全体の fact と比べた"),
    (u"イ", u"見積り・仮定・将来の数・計画の数"),
    (u"ウ", u"連結と単体の取り違え(文の言う側と結んだ fact の側が違う)"),
    (u"エ", u"期の取り違え(文の言う期と結んだ fact の期が違う)"),
    (u"オ", u"定義の違い(同じ名前でも文の言う範囲が fact と違う。(ア)〜(エ) に入らないもの)"),
    (u"カ", u"丸め・単位"),
    (u"キ", u"損失・マイナスの符号"),
    (u"ク", u"本当の差の候補(文がその項目・その側・その期の全体の数を言っていて、同じ有報の fact の値と違って見える)"),
    (u"ケ", u"読んでも分けられない")])
#: G の行の型
TYPES_G = collections.OrderedDict([
    (u"a", u"文の言う項目・範囲・側(連結 / 単体)・期が、結んだ fact と合う"),
    (u"b", u"値は同じだが、項目・範囲・側・期のどれかが結んだ fact と違う(違うものを 1 つ書く: 項目 / 範囲 / 側 / 期)"),
    (u"c", u"読んでも分けられない")])
DIFFS = (u"項目", u"範囲", u"側", u"期")
DIFF_TYPE = u"b"
TYPED_BY = u"司令塔(AI の席 1 席)。人は読んでいない"
SHEET_NOTE_TYPES = (u"V の行の型は ア〜ケ、G の行の型は a・b・c。b の行だけ最後に違うもの(項目 / 範囲 / 側 / 期)を足す")
STATES_LIMITS = (
    u"材料は過去の便で取った有報 201 本(提出者 108。同じ会社の 2 つの年度が入る)で、上場会社全体の標本ではない。本と本は独立でない(封 §6)",
    u"切れない本は測れていない。「札なし」が「KAM が無い」「連結財務諸表が無い」「札の付け方が違う」のどれかは分けない",
    u"engine は渡された文を経営者による分析の塊として読む。監査報告書の文であること・単体の文であることを知らない。単体の数は限界の記録で、成績ではない",
    u"文と fact が同じ誤りを共有していれば、この照合では見えない(同じ有報の中の照合)",
    u"KAM の数の多くは見積りの前提・一部分の残高で、fact の表に相手が無い。「見つからない」「止まった」が多いのはその形のため",
    u"NFKC を掛けた文を測っている(原文の全角・半角の違いは見ていない)",
    u"注入はしていないので、誤りを通す率は言えない",
    u"行は [文の番号, 位置, state, reason, pointer の期, formula の有無, 単位の族, 両期の fact を引く a−b, span に % を含む, pointer の字のどれかに NonConsolidatedMember を含む] だけで、文・span・値・要素名は持たない")

#: 本の側の 1 行の欄(2026-11-09 の便の ``row_entry`` の並び + 10 欄目)
ROW_COLUMNS = (u"文の番号", u"位置", u"state", u"reason", u"pointer の期", u"formula の有無", u"単位の族", u"両期の fact を引く a−b", u"span に % を含む",
               u"pointer の字のどれかに NonConsolidatedMember を含む")
DOCID_RE = re.compile(r"S100[A-Z0-9]{4}")
SEAL_ROW = re.compile(r"^\| (\d+) \| (甲|乙|丙) \| `([0-9a-f]{64})` \| (切れた|札なし) \| (\d+|―) \| (切れた|札なし) \| (\d+|―) \|$", re.M)


# ======================================================================================================
# 母集団(封 §1。封の file から読む)
def seal_table(seal):
    u"""封 §1 の表 [(#, 群, sha256, 連結の切り出し(下見), 連結の claim(下見), 単体の切り出し(下見), 単体の claim(下見))]。claim が ― の行は None。"""
    try:
        sec = seal[seal.index(u"## §1"):seal.index(u"## §2")]
    except ValueError:
        raise Stop(u"**封の節(§1・§2)が読めない。止める**")
    return [(int(m[0]), m[1], m[2], m[3], (int(m[4]) if m[4].isdigit() else None), m[5], (int(m[6]) if m[6].isdigit() else None)) for m in SEAL_ROW.findall(sec)]


def population_from_text(seal):
    u"""[(#, 群, sha256)]。"""
    return [(r[0], r[1], r[2]) for r in seal_table(seal)]


def validate_population(rows, n=N_ROWS, groups=GROUP_COUNTS):
    u"""201 行・番号が 1 から続く・sha256 の重なり 0・群が 甲 67 / 乙 40 / 丙 94・並びが 群(甲・乙・丙)→ sha256 の順。違えば止める。(n・groups は試験が小さい表で試すための引数)"""
    if len(rows) != n:
        raise Stop(u"**母集団の行が %d(%d でない)。止める**" % (len(rows), n))
    if [r[0] for r in rows] != list(range(1, len(rows) + 1)):
        raise Stop(u"**母集団の番号が 1 から続いていない。止める**")
    if len(set(r[2] for r in rows)) != len(rows):
        raise Stop(u"**母集団の sha256 に重なりがある。止める**")
    c = collections.Counter(r[1] for r in rows)
    if [(g, c.get(g, 0)) for g in groups] != list(groups.items()) or sum(c.values()) != len(rows):
        raise Stop(u"**母集団の群が 甲 67 / 乙 40 / 丙 94 でない。止める**")
    order = [(list(groups).index(r[1]), r[2]) for r in rows]
    if order != sorted(order):
        raise Stop(u"**母集団の並びが 群 → sha256 の順でない。止める**")
    return rows


def table_digest(pop):
    u"""母集団の表(# TAB 群 TAB sha256 を行ごとに ``\\n`` でつないだ字)の sha256。"""
    return ST.sha256_text(u"\n".join(u"%d\t%s\t%s" % (r[0], r[1], r[2]) for r in pop))


def seal_text(root=ROOT):
    with io.open(os.path.join(root, SEAL_REL), encoding="utf-8") as fh:
        return fh.read()


def read_population(root=ROOT):
    return validate_population(population_from_text(seal_text(root)))


# ======================================================================================================
# 材料を探す(封 §0-2 の 6)。file 名は使わず、どこにも書かない
def default_base():
    return ST.cache_base()


def folder_snapshots(base, caches=CACHES):
    u"""3 つの folder の (件数, 名前の一覧の sha256)。folder の名前も file 名も返さない。"""
    return [list(ST.names_snapshot(os.path.join(base, f))) for f in caches.values()]


def scan_material(base, pop, caches=CACHES):
    u"""{sha256: (path, byte 数)}。3 つの folder の直下の ``*.zip`` を名前の順に読み、表に在る本だけを選ぶ。重なり・群の違い・欠けは止める。path は返り値の中だけ(書かない)。"""
    want = dict((r[2], r) for r in pop)
    found = collections.OrderedDict()
    for grp, folder in caches.items():
        d = os.path.join(base, folder)
        if not os.path.isdir(d):
            raise Stop(u"**材料の folder が無い(群 %s)。止める**" % grp)
        for f in sorted(os.listdir(d)):
            p = os.path.join(d, f)
            if not f.endswith(".zip") or not os.path.isfile(p):
                continue
            with io.open(p, "rb") as fh:
                b = fh.read()
            s = ST.sha256_bytes(b)
            if s not in want:
                continue
            if s in found:
                raise Stop(u"**同じ sha256 の ZIP が 2 か所に在る(# %d)。止める**" % want[s][0])
            if want[s][1] != grp:
                raise Stop(u"**表の群と違う folder に在る(# %d)。止める**" % want[s][0])
            found[s] = (p, len(b))
    if len(found) != len(pop):
        raise Stop(u"**表の ZIP が %d 本しかそろわない(%d 本要る)。何も書かずに止める**" % (len(found), len(pop)))
    return found


def is_production_out(out, base, root, rel):
    u"""本番の記録の path に書くのに、既定でない材料の置き場を使おうとしているなら真(止める)。"""
    return os.path.abspath(out) == os.path.abspath(os.path.join(root, rel)) and os.path.abspath(base) != os.path.abspath(default_base())


# ======================================================================================================
# 切り出し(封 §0-2 の 3)
def cut_inner(t, start_end):
    u"""文字列 ``t`` の ``start_end``(始まりの札の直後)から、深さを数えて塊の字を返す。閉じなければ None。"""
    tail = t[start_end:]
    depth = 1
    for mm in DEPTH_RE.finditer(tail):
        if mm.group(0).startswith("</"):
            depth -= 1
        elif mm.group(1) != "/":
            depth += 1
        if depth == 0:
            return tail[:mm.start()]
    return None


def lines_to_text(inner):
    u"""塊の字 → 文。``html_to_lines``(呼ぶ)→ NFKC → 前後の空白を落とす → 空の行を捨てる → ``\\n`` でつなぐ。"""
    out = []
    for ln in TS.html_to_lines(inner):
        ln = unicodedata.normalize("NFKC", ln).strip()
        if ln:
            out.append(ln)
    return u"\n".join(out)


def cut_kam(zb, side):
    u"""ZIP の bytes と文の種類(連結 / 単体)から (文, 切れない理由)。切れたなら理由は None。"""
    pat = re.compile(START_RE % re.escape(SIDES[side]))
    try:
        with zipfile.ZipFile(io.BytesIO(zb)) as z:
            members = sorted(n for n in z.namelist() if AUDIT_MARK in n and n.endswith(AUDIT_SUFFIX))
            raws = [z.read(n) for n in members]
    except zipfile.BadZipFile:
        raise Stop(u"**ZIP として読めない。止める**")
    texts = []
    for raw in raws:
        try:
            texts.append(raw.decode("utf-8"))
        except UnicodeDecodeError:
            return None, WHY_DECODE
    hits = []
    for t in texts:
        m = pat.search(t)
        if m:
            hits.append((t, m))
    if not hits:
        return None, WHY_NOTAG
    if len(hits) >= 2:
        return None, WHY_MANY
    t, m = hits[0]
    if CONTINUED in m.group(0):
        return None, WHY_CONT
    inner = cut_inner(t, m.end())
    if inner is None:
        return None, WHY_OPEN
    text = lines_to_text(inner)
    if not text:
        return None, WHY_EMPTY
    return text, None


# ======================================================================================================
# 判定(封 §0-2 の 4)
def row10(key, v):
    u"""記録の行(10 欄)。``row_entry`` の 9 欄 + pointer の字のどれかに ``NonConsolidatedMember`` を含む(真偽)。"""
    return TS.row_entry(key, v) + [any(isinstance(p, str) and NONCONSOLIDATED_MARK in p for p in v[2])]


def judge_side(zb, side):
    u"""1 本の 1 つの文の種類の記録(OrderedDict)。切れなければ行を持たない。"""
    text, why = cut_kam(zb, side)
    if text is None:
        return collections.OrderedDict([(u"切り出し", CUT_NG), (u"理由", why), (u"字数", None), (u"claim", 0), (u"対応", None), (u"行", [])])
    zm = PR.build_modified_zip(zb, text)[0]
    rows, ok, ncl = TS.profile_rows(zb, text, zm, PROFILE)
    return collections.OrderedDict([(u"切り出し", CUT_OK), (u"理由", None), (u"字数", len(text)), (u"claim", ncl), (u"対応", bool(ok)), (u"行", [row10(k, v) for k, v in rows.items()])])


def judge_book(n, grp, sha, zb):
    book = collections.OrderedDict([(u"#", n), (u"群", grp), (u"ZIP の sha256", sha)])
    for side in SIDES:
        book[side] = judge_side(zb, side)
    return book


def read_zip(path, n):
    u"""材料の ZIP の bytes。読めなければ止める(文言に path・file 名を入れない)。"""
    try:
        with io.open(path, "rb") as fh:
            return fh.read()
    except OSError:
        raise Stop(u"**材料の ZIP が読めない(# %d)。止める**" % n)


def states_job(args):
    n, grp, sha, path = args
    zb = read_zip(path, n)
    if ST.sha256_bytes(zb) != sha:
        raise Stop(u"**材料の ZIP の sha256 が封の表と違う(# %d)。止める**" % n)
    return judge_book(n, grp, sha, zb)


# ======================================================================================================
# 集計(行から数える)
def block(sides):
    u"""1 つの文の種類の記録(``judge_side`` の返り値)の集まりの集計。「claim が 0 の本」などは切れた本のうち。"""
    cut_sides = [s for s in sides if s[u"切り出し"] == CUT_OK]
    rows = [r for s in cut_sides for r in s[u"行"]]
    why = collections.Counter(s[u"理由"] for s in sides if s[u"切り出し"] == CUT_NG)
    per = collections.Counter()
    for s in cut_sides:
        c = collections.Counter(r[2] for r in s[u"行"])
        if not s[u"行"]:
            per[u"claim が 0 の本"] += 1
        if not c.get(G, 0):
            per[u"GROUNDED が 0 の本"] += 1
        if c.get(VM, 0) >= 1:
            per[u"VALUE_MISMATCH が 1 以上の本"] += 1
    ten = collections.OrderedDict()
    for st in STATES:
        sub = [r for r in rows if r[2] == st]
        ten[st] = collections.OrderedDict([(u"真", sum(1 for r in sub if r[9])), (u"偽", sum(1 for r in sub if not r[9]))])
    return collections.OrderedDict([
        (u"本", len(sides)), (u"切れた", len(cut_sides)), (u"切れない", len(sides) - len(cut_sides)),
        (u"切れない理由", collections.OrderedDict((w, why.get(w, 0)) for w in WHYS)),
        (u"字数の合計", sum(s[u"字数"] for s in cut_sides)),
        (u"claim", len(rows)), (u"4 state", TS.state_counts(rows)), (u"reason", TS.reason_counts(rows)),
        (u"VALUE_MISMATCH の内訳", TS.vm_breakdown(rows)),
        (u"10 欄目(pointer の字のどれかに NonConsolidatedMember を含む)の数", ten),
        (u"切れた本のうち claim が 0 の本", per.get(u"claim が 0 の本", 0)), (u"切れた本のうち GROUNDED が 0 の本", per.get(u"GROUNDED が 0 の本", 0)),
        (u"VALUE_MISMATCH が 1 以上の本", per.get(u"VALUE_MISMATCH が 1 以上の本", 0)),
        (u"claim と raw の並びが対応しなかった本", sum(1 for s in cut_sides if not s[u"対応"]))])


def tally(books):
    u"""文の種類(連結・単体)ごと → 群ごと(甲・乙・丙)と計。連結と単体は足さない。"""
    out = collections.OrderedDict()
    for side in SIDES:
        sub = collections.OrderedDict()
        for g in GROUP_COUNTS:
            if any(b[u"群"] == g for b in books):
                sub[g] = block([b[side] for b in books if b[u"群"] == g])
        sub[u"計"] = block([b[side] for b in books])
        out[side] = sub
    return out


def check_clean(rec, text, key_value=None):
    u"""記録に repo へ入れない欄・鍵らしい字・docID の字が無いか(あれば止める)。"""
    bad = sorted(set(k for k in TS.RUN.walk_keys(rec) if k in TS.RUN.FORBIDDEN_KEYS))
    if bad:
        raise Stop(u"**記録に repo へ入れない欄がある: %s。止める**" % u",".join(bad))
    leaks = ST.key_leaks(text.replace(SEAL_REL, u""), key_value)
    if leaks:
        raise Stop(u"**鍵らしい字が記録に在る(%s)。書かずに止める**" % u" / ".join(sorted(set(leaks))))
    if DOCID_RE.search(text):
        raise Stop(u"**docID の字が記録に在る。書かずに止める**")


def header(root, step, script_sha):
    rec = collections.OrderedDict()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = step
    rec[u"HEAD の commit"] = ST.git_head(root)
    rec[u"この script の sha256"] = script_sha
    return rec


def material_block(mat_before, mat_after, n_found):
    return collections.OrderedDict([
        (u"置き場", u"~/.cache/audit-core の 3 つの folder(甲・乙・丙。名前は書かない)"), (u"表と一致した ZIP", n_found),
        (u"3 つの folder の一覧の前後(件数・名前の sha256)", collections.OrderedDict([(u"前", mat_before), (u"後", mat_after), (u"変化なし", mat_before == mat_after)]))])


# ======================================================================================================
# population
def run_population(root=ROOT, out=None, cache_base=None, say=print, population=None, key_value=None, shape=None):
    out = os.path.abspath(out or os.path.join(root, POPULATION_REL))
    base = cache_base or default_base()
    if is_production_out(out, base, root, POPULATION_REL):
        raise Stop(u"**本番の記録を使い捨ての材料から作らない。止める**")
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    n_rows, groups = shape or (N_ROWS, GROUP_COUNTS)               # 試験が小さい表で試すときだけ shape を渡す
    pop = validate_population(population if population is not None else read_population(root), n_rows, groups)
    before = folder_snapshots(base)
    found = scan_material(base, pop)
    after = folder_snapshots(base)
    if before != after:
        raise Stop(u"**材料の folder の件数か名前が変わった。記録を書かずに止める**")
    rec = header(root, u"KAM(監査報告書の KAM の文を同じ有報の fact で確かめる)― 母集団 201 本の記録(0 USD・通信なし)", ST.sha256_file(os.path.abspath(__file__)))
    rec[u"封の表の sha256"] = ST.sha256_file(os.path.join(root, SEAL_REL))
    rec[u"母集団の表(# TAB 群 TAB sha256 の行)の sha256"] = table_digest(pop)
    rec[u"範囲"] = u"封 §1 の 201 本"
    rec[u"材料"] = material_block(before, after, len(found))
    rec[u"群"] = collections.OrderedDict((g, sum(1 for r in pop if r[1] == g)) for g in groups)
    rec[u"byte 数の合計"] = sum(found[r[2]][1] for r in pop)
    rec[u"行の欄"] = [u"#", u"群", u"ZIP の sha256", u"byte 数"]
    rec[u"行"] = [[r[0], r[1], r[2], found[r[2]][1]] for r in pop]
    rec[u"key_leaks"] = []
    text = ST.dumps_record(rec)
    check_clean(rec, text, key_value)
    ST.write_text_exclusive(out, text)
    say(u"-> %s(本 %d)" % (os.path.basename(out), len(pop)))
    return rec


# ======================================================================================================
# states
def run_states(root=ROOT, procs=1, out=None, cache_base=None, say=print, population=None, key_value=None, clock=time.time, shape=None):
    out = os.path.abspath(out or os.path.join(root, STATES_REL))
    base = cache_base or default_base()
    if is_production_out(out, base, root, STATES_REL):
        raise Stop(u"**本番の記録を使い捨ての材料から作らない。止める**")
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    n_rows, groups = shape or (N_ROWS, GROUP_COUNTS)
    pop = validate_population(population if population is not None else read_population(root), n_rows, groups)
    before = folder_snapshots(base)
    found = scan_material(base, pop)
    jobs = [(n, g, sha, found[sha][0]) for (n, g, sha) in pop]
    say(u"states %d 本 × 連結・単体 × %s ― procs %d" % (len(jobs), PROFILE, procs))
    t0 = clock()
    books = TS.NF.map_pool(states_job, jobs, procs)
    elapsed = clock() - t0
    after = folder_snapshots(base)
    if before != after:
        raise Stop(u"**材料の folder の件数か名前が変わった。記録を書かずに止める**")
    rec = header(root, u"KAM(監査報告書の KAM の文を同じ有報の fact で確かめる)― 201 本の切り出し・判定(0 USD・通信なし)", ST.sha256_file(os.path.abspath(__file__)))
    rec[u"2026-11-09 の便の script の sha256"] = ST.sha256_file(os.path.join(HERE, os.path.basename(TS_SCRIPT_REL)))
    rec[u"TSS の script の sha256"] = ST.sha256_file(os.path.join(HERE, os.path.basename(TSS_SCRIPT_REL)))
    rec[u"封の表の sha256"] = ST.sha256_file(os.path.join(root, SEAL_REL))
    rec[u"母集団の表(# TAB 群 TAB sha256 の行)の sha256"] = table_digest(pop)
    rec[u"engine の指紋"] = VD.engine_fingerprint()
    rec[u"profile"] = PROFILE
    rec[u"材料"] = material_block(before, after, len(found))
    rec[u"切り出し"] = collections.OrderedDict([
        (u"member", u"名前に /AuditDoc/ を含み .htm で終わるもの(名前の順に utf-8 strict で全部読む)"),
        (u"札の名前", u"連結と単体で別(要素名は script の SIDES。長い英字なので記録には書かない)"),
        (u"始まりの規則", START_RE), (u"深さの規則", DEPTH_RE.pattern), (u"続きありの印", CONTINUED),
        (u"NFKC", True), (u"行にする関数", u"2026-11-09 の便の html_to_lines(呼ぶ)"), (u"切れない理由", list(WHYS))])
    rec[u"判定"] = collections.OrderedDict([
        (u"呼び方", u"verify_document(元の ZIP, P33E, text=文)。連結の文と単体の文は別々に 1 回ずつ。数は連結と単体を足さない"),
        (u"10 欄目", u"pointer の字のどれかに %s を含む(真偽)" % NONCONSOLIDATED_MARK)])
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
# 読む行(封 §0-2 の 7)
def side_rows(states, side, state):
    u"""[(本の #, 文の番号, 位置)]。# の順・文の番号の順・位置の順。"""
    out = []
    for b in sorted(states[u"本"], key=lambda b: b[u"#"]):
        for r in sorted((r for r in b[side][u"行"] if r[2] == state), key=lambda r: (r[0], r[1])):
            out.append((b[u"#"], r[0], r[1]))
    return out


def reading_items(states):
    u"""{読みの組: [(組の通し番号(1 から), 本の #, 文の番号, 位置)]}。V・G 単体は全部、G 連結は 60 行を引く。"""
    out = collections.OrderedDict()
    for label, (side, state, draw) in READ_SETS.items():
        rows = side_rows(states, side, state)
        if draw:
            rows = [rows[j] for j in TSS.pick_sample(len(rows), seed=READ_SEED, k=READ_N)]
        out[label] = [(i + 1,) + r for i, r in enumerate(rows)]
    return out


def sheet_text(label, item, claim, sentence_text, ten):
    k, num, si, pos = item
    return u"\n".join([
        u"=== %s %d / 本 # %d / 文 %d / 位置 %d ===" % (label, k, num, si, pos),
        u"文: %s" % sentence_text,
        u"span: %s" % claim["span"],
        u"読んだ値: %s %s" % (claim["value"], claim["unit"]),
        u"state: %s  reason: %s" % (claim["state"], claim["reason"]),
        u"結んだ先: %s" % u" , ".join(claim["pointers"] or []),
        u"その値: %s" % claim["recomputed"],
        u"10 欄目(pointer の字のどれかに %s を含む): %s" % (NONCONSOLIDATED_MARK, u"真" if ten else u"偽"),
        u"型: ", u"", u""])


def sheet_intro():
    return u"\n".join([
        u"# KAM の便 ― 読むための紙(repo の外。追跡しない)",
        u"型の file は 1 行に「組 TAB 通し番号 TAB 型」。%s" % SHEET_NOTE_TYPES,
        u"V の型: " + u" / ".join(u"(%s) %s" % kv for kv in TYPES_V.items()),
        u"G の型: " + u" / ".join(u"(%s) %s" % kv for kv in TYPES_G.items()),
        u"", u""])


def run_sheet(states_path, sheet, cache_base=None, root=ROOT, say=print, repo=None, population=None, shape=None):
    if TSS.inside_repo(sheet, repo):
        raise Stop(u"**--sheet が repo の中(または git の木の中)。文を持つ紙は repo の外に書く。止める**")
    sheet = os.path.abspath(sheet)
    if os.path.exists(sheet):
        raise Stop(u"**--sheet が既に在る。止める**")
    states = TSS.load_json(states_path)
    items = reading_items(states)
    n_rows, groups = shape or (N_ROWS, GROUP_COUNTS)
    pop = validate_population(population if population is not None else read_population(root), n_rows, groups)
    byn = dict((r[0], r) for r in pop)
    base = cache_base or default_base()
    found = scan_material(base, pop)
    need = collections.OrderedDict()                                     # (本の #, 側) → [(組, 通し番号, 文の番号, 位置)]
    for label, its in items.items():
        side = READ_SETS[label][0]
        for it in its:
            need.setdefault((it[1], side), []).append((label, it))
    chunks = {}
    for (num, side), lst in sorted(need.items(), key=lambda kv: (kv[0][0], list(SIDES).index(kv[0][1]))):
        sha = byn[num][2]
        zb = read_zip(found[sha][0], num)
        if ST.sha256_bytes(zb) != sha:
            raise Stop(u"**材料の ZIP の sha256 が封の表と違う(# %d)。止める**" % num)
        text, why = cut_kam(zb, side)
        if text is None:
            raise Stop(u"**読む行の本が切れない(# %d)。記録と合わない。止める**" % num)
        zm = PR.build_modified_zip(zb, text)[0]
        rows, ok, _n = TS.profile_rows(zb, text, zm, PROFILE)
        nums, texts = R.build_raw_claims(zm, V.PROFILES[PROFILE])
        raws = nums + texts
        cl = VD.verify_document(zb, PROFILE, text)["claims"]
        if not ok or len(cl) != len(raws) or any(c["id"] != r["id"] for c, r in zip(cl, raws)):
            raise Stop(u"**claim と raw の並びが対応しない(# %d)。止める**" % num)
        sents = TS.RUN.sentence_list(zm, V.PROFILES[PROFILE])
        keyed = dict(((r["sentence"], r["pos"]), c) for c, r in zip(cl, raws) if c["kind"] == "num")
        rec_rows = dict(((r[0], r[1]), r) for r in next(b for b in states[u"本"] if b[u"#"] == num)[side][u"行"])
        for label, it in lst:
            key = (it[2], it[3])
            c = keyed.get(key)
            want_state = READ_SETS[label][1]
            if c is None or c["state"] != want_state or key not in rows or row10(key, rows[key]) != rec_rows.get(key):
                raise Stop(u"**読む行が記録と合わない(%s %d)。止める**" % (label, it[0]))
            chunks[(label, it[0])] = sheet_text(label, it, c, sents[it[2]], row10(key, rows[key])[9])
    d = os.path.dirname(sheet)
    if d:
        os.makedirs(d, exist_ok=True)
    body = sheet_intro() + u"".join(chunks[(label, it[0])] + u"\n" for label, its in items.items() for it in its)
    with io.open(sheet, "w", encoding="utf-8", newline="") as fh:
        fh.write(body)
    say(u"読む行 %s・本 %d" % (u"・".join(u"%s %d" % (label, len(its)) for label, its in items.items()), len(set(k[0] for k in need))))
    return items


# ======================================================================================================
# types
def types_of(label):
    return TYPES_G if label in (G_CONS, G_NON) else TYPES_V


def read_typed(path):
    u"""1 行に「組 TAB 通し番号 TAB 型」(型が b の行だけ TAB 違うもの)。{(組, 通し番号): (型, 違うもの)}。形が違う・重なる・型が組の外・違うものの有無が型と合わなければ止める。"""
    out = {}
    with io.open(path, encoding="utf-8") as fh:
        for ln in fh.read().split(u"\n"):
            if not ln.strip():
                continue
            parts = ln.rstrip(u"\r").split(u"\t")
            if len(parts) not in (3, 4) or parts[0] not in READ_SETS or not re.fullmatch(r"[0-9]+", parts[1]) or parts[2] not in types_of(parts[0]):
                raise Stop(u"**型の file の行が「組 TAB 通し番号 TAB 型」でない。止める**")
            if (len(parts) == 4) != (parts[2] == DIFF_TYPE) or (len(parts) == 4 and parts[3] not in DIFFS):
                raise Stop(u"**違うもの(項目 / 範囲 / 側 / 期)は型が b の行にだけ 1 つ付ける。止める**")
            k = (parts[0], int(parts[1]))
            if k in out:
                raise Stop(u"**型の file に同じ行が 2 行ある。止める**")
            out[k] = (parts[2], parts[3] if len(parts) == 4 else None)
    return out


def run_types(states_path, typed_path, out=None, root=ROOT, say=print, key_value=None):
    out = os.path.abspath(out or os.path.join(root, TYPES_REL))
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。止める**" % os.path.basename(out))
    states = TSS.load_json(states_path)
    items = reading_items(states)
    typed = read_typed(typed_path)
    if sorted(typed) != sorted((label, it[0]) for label, its in items.items() for it in its):
        raise Stop(u"**型の file の行が読む行(%d 行)とそろわない。止める**" % sum(len(v) for v in items.values()))
    rec = header(root, u"KAM ― 読む行の型分け(0 USD)", ST.sha256_file(os.path.abspath(__file__)))
    rec[u"states の記録の sha256"] = ST.sha256_file(os.path.abspath(states_path))
    rec[u"型を付けた席"] = TYPED_BY
    rec[u"盲検"] = u"盲検ではない(封の予測を知ったうえで付けた)。(ク) は候補で、紙面で確かめていない"
    rec[u"読む行の規則"] = collections.OrderedDict([
        (u"V 連結・V 単体", u"連結・単体の VALUE_MISMATCH の全部の行"), (u"G 単体", u"単体の GROUNDED の全部の行"),
        (u"G 連結", u"連結の GROUNDED の行を # の順・文の番号の順・位置の順に並べ、random.Random(種).sample(range(行の数), 引く数) を番号の順に。行の数が引く数に満たなければ全部"),
        (u"種", READ_SEED), (u"引く数", READ_N),
        (u"G 連結の行の数", len(side_rows(states, u"連結", G))),
        (u"読む行の数", collections.OrderedDict((label, len(its)) for label, its in items.items())),
        (u"読む行の数の合計", sum(len(its) for its in items.values()))])
    rec[u"型の字"] = collections.OrderedDict([(u"V", collections.OrderedDict(TYPES_V)), (u"G", collections.OrderedDict(TYPES_G)), (u"違うもの", list(DIFFS))])
    counts = collections.OrderedDict()
    for label, its in items.items():
        c = collections.Counter(typed[(label, it[0])][0] for it in its)
        counts[label] = collections.OrderedDict((t, c.get(t, 0)) for t in types_of(label))
    rec[u"型の集計"] = counts
    diffs = collections.OrderedDict()
    for label in (G_CONS, G_NON):
        c = collections.Counter(typed[(label, it[0])][1] for it in items[label] if typed[(label, it[0])][0] == DIFF_TYPE)
        diffs[label] = collections.OrderedDict((d, c.get(d, 0)) for d in DIFFS)
    rec[u"b の違うものの集計"] = diffs
    rec[u"行の欄"] = [u"読みの組", u"本の #", u"文の番号", u"位置", u"型", u"違うもの"]
    rec[u"行"] = [[label, it[1], it[2], it[3], typed[(label, it[0])][0], typed[(label, it[0])][1]] for label, its in items.items() for it in its]
    rec[u"key_leaks"] = []
    text = ST.dumps_record(rec)
    check_clean(rec, text, key_value)
    ST.write_text_exclusive(out, text)
    say(u"-> %s(読む行 %d)" % (os.path.basename(out), len(rec[u"行"])))
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    a = sub.add_parser("population")
    a.add_argument("--root", default=ROOT)
    a.add_argument("--out", default=None)
    a.add_argument("--cache-base", default=None)
    b = sub.add_parser("states")
    b.add_argument("--root", default=ROOT)
    b.add_argument("--out", default=None)
    b.add_argument("--cache-base", default=None)
    b.add_argument("--procs", type=int, default=1)
    c = sub.add_parser("sheet")
    c.add_argument("--root", default=ROOT)
    c.add_argument("--states", default=None)
    c.add_argument("--sheet", required=True)
    c.add_argument("--cache-base", default=None)
    d = sub.add_parser("types")
    d.add_argument("--root", default=ROOT)
    d.add_argument("--states", default=None)
    d.add_argument("--typed", required=True)
    d.add_argument("--out", default=None)
    a_ = ap.parse_args(argv)
    if a_.cmd == "population":
        run_population(root=a_.root, out=a_.out, cache_base=a_.cache_base)
    elif a_.cmd == "states":
        run_states(root=a_.root, procs=a_.procs, out=a_.out, cache_base=a_.cache_base)
    elif a_.cmd == "sheet":
        run_sheet(a_.states or os.path.join(a_.root, STATES_REL), a_.sheet, cache_base=a_.cache_base, root=a_.root)
    elif a_.cmd == "types":
        run_types(a_.states or os.path.join(a_.root, STATES_REL), a_.typed, out=a_.out, root=a_.root)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
