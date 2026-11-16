# -*- coding: utf-8 -*-
u"""封 docs/XBRL_YUHO_SECTIONS_SEAL_2026-11-16.md §0-2・§1・§2・§5 ― YS(有価証券報告書の「経営者による分析」以外の 3 つの節 = 研究開発活動・設備投資等の概要・配当政策の文を、同じ有報の fact で確かめる)の測定。
**0 USD・通信なし・鍵は読まない・LLM は呼ばない。engine(``core/``・``adapters/``)と ``measure/lib/`` は 1 行も変えない。**材料は ``~/.cache/audit-core/`` の 3 つの folder の ``.zip`` を読むだけ(1 file も足さない・写さない)。
母集団の検査・材料の探し方・folder の一覧・切り出しの部品(深さを数える・行にする)・10 欄目・集計・紙の 1 ブロック・止め方・書き方は、KAM の script ``xbrl_kam_2026-11-15.py``(以下 KAM)と、
KAM が読む TSS の script・2026-11-09 の便の関数を **呼ぶ**(書き写さない)。この script に書いたのは、KAM の関数が札の名前・member の場所・組の字を中に持っていて呼べない部分だけ。

    python3 measure/xbrl_yuho_sections_2026-11-16.py population [--out PATH] [--cache-base DIR]            # 封 §1 の 201 本を 3 つの folder から sha256 で探し、母集団の記録を書く
    python3 measure/xbrl_yuho_sections_2026-11-16.py states [--out PATH] [--cache-base DIR] [--procs N]     # 201 本 × 3 つの節の文を切り出し、P33E で判定して記録を書く
    python3 measure/xbrl_yuho_sections_2026-11-16.py sheet --states PATH --sheet PATH [--cache-base DIR]    # 読む行の文・span・値・結んだ先を repo の外の紙に書く(標準出力は件数だけ)
    python3 measure/xbrl_yuho_sections_2026-11-16.py types --states PATH --typed PATH [--out PATH]          # 司令塔が付けた型の file を確かめて read_types_2026-11-16.json を書く

実装の注(封の字の解釈。実装より先に決め、結果を見て変えない。封に無い決めはここに書き、報告にも書いた):
- 材料の探し方(封 §0-2 の 6): KAM の ``scan_material`` を呼ぶ(3 つの folder の直下の ``*.zip`` を名前の順に読み、byte の sha256 が封の表に在るものを選ぶ。file 名は使わず記録にも書かない。201 本そろわなければ止める。
  同じ sha256 が 2 か所・表の群と違う folder は止める = 封に無い守り。止めるだけで数は変えない)。3 つの folder の一覧(件数と名前の sha256)の前後が違えば、記録を書かずに止める。
- 切り出し(封 §0-2 の 3): 名前に ``/PublicDoc/`` を含み ``.htm`` で終わる member を名前の順に utf-8(strict)で全部読む(1 つでも読めなければ 切れない(decode))→ 各 file で
  ``<ix:nonNumeric\\b[^>]*\\bname="<札の名前>"[^>]*>`` の最初の一致 → 一致の在る file が 0 = 札なし・2 以上 = 札が複数 → 始まりの札に ``continuedAt`` = 続きあり →
  深さを数えて終わりを探し(KAM の ``cut_inner``)、閉じなければ 閉じない → 塊を行にして NFKC・前後の空白を落とし・空の行を捨てて ``\\n`` でつなぐ(KAM の ``lines_to_text``)→ 空なら 空。
  member が 1 つも無い本は「一致の在る file が 0」なので 札なし。ZIP として読めなければ止める(封に無い失敗の型は結果に混ぜない)。3 つの節は札の名前だけが違う。
- 判定(封 §0-2 の 4): 節ごとに別々に 1 回、``PR.build_modified_zip``(engine の入口。memory の中だけ)で文を差し替えた ZIP を作り、2026-11-09 の便の ``profile_rows(元の ZIP, 文, 差し替えた ZIP, "P33E")`` を **呼んで** 行を作り、
  KAM の ``row10`` で 10 欄目「pointer の字のどれかに ``NonConsolidatedMember`` を含む(真偽)」を足す。数の claim = ``kind == "num"``。claim と raw の並びが対応したかも節ごとに ``対応`` に持つ。
- 集計は 行 から数える(KAM の ``block``。切れた側だけが行を持つ)。「claim が 0 の本」「GROUNDED が 0 の本」は切れた本のうち。3 つの節は足さない。
- 読む行(封 §0-2 の 7): V 研究・V 設備・V 配当・G 配当は全部の行、G 研究・G 設備は (# の順・文の番号の順・位置の順)に並べた行から、節ごとに新しい ``random.Random(20261116).sample(range(行の数), 60)`` を番号の順に
  (TSS の ``pick_sample`` は呼ぶたびに新しい Random を作る。60 に満たなければ全部)。組の並びは V 研究・V 設備・V 配当・G 研究・G 設備・G 配当(封は組の並びを決めていない。通し番号は組ごとに 1 から)。
  型の file は 1 行に「組 TAB 通し番号 TAB 型」、型が (b) の行だけ「TAB 違うもの(項目 / 範囲 / 側 / 期)」を足す。
- 記録は文・span・値・pointer の字・要素名・会社名・証券コード・docID を持たない(封に書いた 3 つの札の名前だけは、切り出しの規則の字として持つ)。時間(秒)は記録の中で 1 つの欄。ほかは 2 回走らせて byte で同じになる(本・辞書の順を固定)。
  2 回走らせて比べる入口は KAM と同じ形(``states`` を別の ``--out`` で 2 回走らせ、時間の欄を除いて byte を比べる。比べるのは門の試験)。
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


KAM = load_module("xbrl_kam_2026-11-15.py", "kam_for_yuho_sections")                                     # KAM の script(部品を呼ぶ)
TSS = KAM.TSS                                                                                             # TSS の script(標本の引き方・紙の置き場の検査)
ST = KAM.ST                                                                                               # 置く script(同じ instance。止め方・書き方・sha256・一覧の前後)
TS = KAM.TS                                                                                               # 2026-11-09 の便(html_to_lines・profile_rows・row_entry・集計の部品)
Stop = ST.Stop

from adapters.xbrl import prose as PR                   # noqa: E402
from adapters.xbrl import recipes as R                  # noqa: E402
from adapters.xbrl import verify_document as VD         # noqa: E402
from adapters.xbrl import vocabulary as V               # noqa: E402

SEAL_REL = "docs/XBRL_YUHO_SECTIONS_SEAL_2026-11-16.md"
SEAL_COMMIT = "e7754d70"
SCRIPT_REL = "measure/xbrl_yuho_sections_2026-11-16.py"
KAM_SCRIPT_REL = KAM.SCRIPT_REL
TSS_SCRIPT_REL = TSS.SCRIPT_REL
TS_SCRIPT_REL = TSS.TS_SCRIPT_REL
REC_DIR_REL = "fixtures/xbrl/yuho_sections"
POPULATION_REL = REC_DIR_REL + "/population_2026-11-16.json"
STATES_REL = REC_DIR_REL + "/states_2026-11-16.json"
TYPES_REL = REC_DIR_REL + "/read_types_2026-11-16.json"
DOC_REL = "docs/XBRL_YUHO_SECTIONS_RESULT_2026-11-16.md"

# ---- 封 §0-1・§0-2 の決めごと(字で留める。門が封と照らす)
PROFILE = "P33E"
N_ROWS = 201
GROUP_COUNTS = collections.OrderedDict([(u"甲", 67), (u"乙", 40), (u"丙", 94)])
#: 群と cache の folder(封 §0-1 の 1・§0-2 の 6。KAM と同じ。folder の名前は記録に書かない)
CACHES = KAM.CACHES
#: 節 → 札の名前(封 §0-1 の 4・§0-2 の 3)
SECTIONS = collections.OrderedDict([
    (u"研究開発活動", "jpcrp_cor:ResearchAndDevelopmentActivitiesTextBlock"),
    (u"設備投資等の概要", "jpcrp_cor:OverviewOfCapitalExpendituresEtcTextBlock"),
    (u"配当政策", "jpcrp_cor:DividendPolicyTextBlock")])
PUBLIC_MARK = "/PublicDoc/"
PUBLIC_SUFFIX = ".htm"
START_RE = r'<ix:nonNumeric\b[^>]*\bname="%s"[^>]*>'
DEPTH_RE = KAM.DEPTH_RE                                 # 深さを数える規則(KAM の cut_inner が使う。封 §0-2 の 3 と同じ字)
CONTINUED = "continuedAt"
NONCONSOLIDATED_MARK = KAM.NONCONSOLIDATED_MARK
WHY_DECODE, WHY_NOTAG, WHY_MANY, WHY_CONT, WHY_OPEN, WHY_EMPTY = KAM.WHY_DECODE, KAM.WHY_NOTAG, KAM.WHY_MANY, KAM.WHY_CONT, KAM.WHY_OPEN, KAM.WHY_EMPTY
WHYS = KAM.WHYS
CUT_OK, CUT_NG = KAM.CUT_OK, KAM.CUT_NG
STATES = TS.STATES
G, VM, UNV, PNF = STATES
#: 読む行(封 §0-2 の 7)
READ_SEED = 20261116
READ_N = 60
V_RD, V_EQ, V_DV, G_RD, G_EQ, G_DV = u"V 研究", u"V 設備", u"V 配当", u"G 研究", u"G 設備", u"G 配当"
#: 読みの組 → (節, state, 引くか)
READ_SETS = collections.OrderedDict([
    (V_RD, (u"研究開発活動", VM, False)), (V_EQ, (u"設備投資等の概要", VM, False)), (V_DV, (u"配当政策", VM, False)),
    (G_RD, (u"研究開発活動", G, True)), (G_EQ, (u"設備投資等の概要", G, True)), (G_DV, (u"配当政策", G, False))])
G_LABELS = (G_RD, G_EQ, G_DV)
#: V の行の型(封 §0-2 の 7。字は封と同じ)
TYPES_V = collections.OrderedDict([
    (u"ア", u"一部分の数(セグメント・子会社・事業・拠点・内訳)を、全体の fact と比べた"),
    (u"イ", u"見積り・仮定・将来の数・計画の数・目標の数"),
    (u"ウ", u"連結と単体の取り違え(文の言う側と結んだ fact の側が違う)"),
    (u"エ", u"期の取り違え(文の言う期と結んだ fact の期が違う)"),
    (u"オ", u"定義の違い(同じ名前でも文の言う範囲・計算の仕方が fact と違う。(ア)〜(エ) に入らないもの)"),
    (u"カ", u"丸め・単位"),
    (u"キ", u"損失・マイナスの符号"),
    (u"ク", u"本当の差の候補(文がその項目・その側・その期の全体の数を言っていて、同じ有報の fact の値と違って見える)"),
    (u"ケ", u"読んでも分けられない")])
#: G の行の型
TYPES_G = collections.OrderedDict([
    (u"a", u"文の言う項目・範囲・側(連結 / 単体)・期が、結んだ fact と合う"),
    (u"b", u"値は同じだが、項目・範囲・側・期のどれかが結んだ fact と違う(違うものを 1 つ書く: 項目 / 範囲 / 側 / 期。2 つ以上違えばこの並びで先のもの)"),
    (u"c", u"読んでも分けられない")])
DIFFS = (u"項目", u"範囲", u"側", u"期")
DIFF_TYPE = u"b"
TYPED_BY = u"司令塔(AI の席 1 席)。人は読んでいない"
SHEET_NOTE_TYPES = u"V の行の型は ア〜ケ、G の行の型は a・b・c。b の行だけ最後に違うもの(項目 / 範囲 / 側 / 期)を足す"
STATES_LIMITS = (
    u"材料は過去の便で取った有報 201 本(提出者 108。同じ会社の 2 つの年度が入る)で、上場会社全体の標本ではない。本と本は独立でない(封 §6)",
    u"節は下調べの数を見てから選んだ。選ばなかった節(事業等のリスク・経営方針、経営環境及び対処すべき課題等・重要な会計上の見積り・従業員の状況)は測らない。この数を有報の全部の節での成績と読まない",
    u"engine は渡された文を経営者による分析の塊として読む。どの節の文かを知らない。連結と単体の側も見分けない",
    u"文と fact が同じ誤りを共有していれば、この照合では見えない(同じ有報の中の照合)",
    u"配当政策の節の主題の数(1 株当たり配当額)は、engine が決めとして止める形(per_unit_counter)。止まった数が多いのは engine の決めで、文の誤りでも材料の欠けでもない",
    u"研究開発活動の節は、半分より多い本が「該当事項はありません」の形で、数は残りの本に集まる",
    u"NFKC を掛けた文を測っている(原文の全角・半角の違いは見ていない)",
    u"注入はしていないので、誤りを通す率は言えない",
    u"行は [文の番号, 位置, state, reason, pointer の期, formula の有無, 単位の族, 両期の fact を引く a−b, span に % を含む, pointer の字のどれかに NonConsolidatedMember を含む] だけで、文・span・値・要素名は持たない")

#: 本の側の 1 行の欄(2026-11-09 の便の ``row_entry`` の並び + 10 欄目。KAM と同じ)
ROW_COLUMNS = KAM.ROW_COLUMNS
DOCID_RE = KAM.DOCID_RE
SEAL_ROW = re.compile(r"^\| (\d+) \| (甲|乙|丙) \| `([0-9a-f]{64})` \| (\d+) \| (\d+) \| (\d+) \|$", re.M)


# ======================================================================================================
# 母集団(封 §1。封の file から読む)
def seal_table(seal):
    u"""封 §1 の表 [(#, 群, sha256, 研究の claim(下見), 設備の claim(下見), 配当の claim(下見))]。"""
    try:
        sec = seal[seal.index(u"## §1"):seal.index(u"## §2")]
    except ValueError:
        raise Stop(u"**封の節(§1・§2)が読めない。止める**")
    return [(int(m[0]), m[1], m[2], int(m[3]), int(m[4]), int(m[5])) for m in SEAL_ROW.findall(sec)]


def population_from_text(seal):
    u"""[(#, 群, sha256)]。"""
    return [(r[0], r[1], r[2]) for r in seal_table(seal)]


def seal_text(root=ROOT):
    with io.open(os.path.join(root, SEAL_REL), encoding="utf-8") as fh:
        return fh.read()


def read_population(root=ROOT):
    return KAM.validate_population(population_from_text(seal_text(root)), N_ROWS, GROUP_COUNTS)


# ======================================================================================================
# 切り出し(封 §0-2 の 3)
def cut_section(zb, section):
    u"""ZIP の bytes と節の名前から (文, 切れない理由)。切れたなら理由は None。"""
    pat = re.compile(START_RE % re.escape(SECTIONS[section]))
    try:
        with zipfile.ZipFile(io.BytesIO(zb)) as z:
            members = sorted(n for n in z.namelist() if PUBLIC_MARK in n and n.endswith(PUBLIC_SUFFIX))
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
    inner = KAM.cut_inner(t, m.end())
    if inner is None:
        return None, WHY_OPEN
    text = KAM.lines_to_text(inner)
    if not text:
        return None, WHY_EMPTY
    return text, None


# ======================================================================================================
# 判定(封 §0-2 の 4)
def judge_section(zb, section):
    u"""1 本の 1 つの節の記録(OrderedDict)。切れなければ行を持たない。"""
    text, why = cut_section(zb, section)
    if text is None:
        return collections.OrderedDict([(u"切り出し", CUT_NG), (u"理由", why), (u"字数", None), (u"claim", 0), (u"対応", None), (u"行", [])])
    zm = PR.build_modified_zip(zb, text)[0]
    rows, ok, ncl = TS.profile_rows(zb, text, zm, PROFILE)
    return collections.OrderedDict([(u"切り出し", CUT_OK), (u"理由", None), (u"字数", len(text)), (u"claim", ncl), (u"対応", bool(ok)), (u"行", [KAM.row10(k, v) for k, v in rows.items()])])


def judge_book(n, grp, sha, zb):
    book = collections.OrderedDict([(u"#", n), (u"群", grp), (u"ZIP の sha256", sha)])
    for section in SECTIONS:
        book[section] = judge_section(zb, section)
    return book


def states_job(args):
    n, grp, sha, path = args
    zb = KAM.read_zip(path, n)
    if ST.sha256_bytes(zb) != sha:
        raise Stop(u"**材料の ZIP の sha256 が封の表と違う(# %d)。止める**" % n)
    return judge_book(n, grp, sha, zb)


# ======================================================================================================
# 集計(行から数える。節ごと → 群ごとと計。3 つの節は足さない)
def tally(books):
    out = collections.OrderedDict()
    for section in SECTIONS:
        sub = collections.OrderedDict()
        for g in GROUP_COUNTS:
            if any(b[u"群"] == g for b in books):
                sub[g] = KAM.block([b[section] for b in books if b[u"群"] == g])
        sub[u"計"] = KAM.block([b[section] for b in books])
        out[section] = sub
    return out


def check_clean(rec, text, key_value=None):
    u"""記録に repo へ入れない欄・鍵らしい字・docID の字が無いか(あれば止める)。封の file 名と、封に書いた 3 つの札の名前(どちらも英字の連なりが 32 字を超える)は鍵の検査の前に除く。"""
    bad = sorted(set(k for k in TS.RUN.walk_keys(rec) if k in TS.RUN.FORBIDDEN_KEYS))
    if bad:
        raise Stop(u"**記録に repo へ入れない欄がある: %s。止める**" % u",".join(bad))
    scrubbed = text.replace(SEAL_REL, u"")
    for name in SECTIONS.values():
        scrubbed = scrubbed.replace(name, u"")
    leaks = ST.key_leaks(scrubbed, key_value)
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


# ======================================================================================================
# population
def run_population(root=ROOT, out=None, cache_base=None, say=print, population=None, key_value=None, shape=None):
    out = os.path.abspath(out or os.path.join(root, POPULATION_REL))
    base = cache_base or KAM.default_base()
    if KAM.is_production_out(out, base, root, POPULATION_REL):
        raise Stop(u"**本番の記録を使い捨ての材料から作らない。止める**")
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    n_rows, groups = shape or (N_ROWS, GROUP_COUNTS)               # 試験が小さい表で試すときだけ shape を渡す
    pop = KAM.validate_population(population if population is not None else read_population(root), n_rows, groups)
    before = KAM.folder_snapshots(base)
    found = KAM.scan_material(base, pop)
    after = KAM.folder_snapshots(base)
    if before != after:
        raise Stop(u"**材料の folder の件数か名前が変わった。記録を書かずに止める**")
    rec = header(root, u"YS(有報の 3 つの節の文を同じ有報の fact で確かめる)― 母集団 201 本の記録(0 USD・通信なし)", ST.sha256_file(os.path.abspath(__file__)))
    rec[u"封の表の sha256"] = ST.sha256_file(os.path.join(root, SEAL_REL))
    rec[u"母集団の表(# TAB 群 TAB sha256 の行)の sha256"] = KAM.table_digest(pop)
    rec[u"範囲"] = u"封 §1 の 201 本"
    rec[u"材料"] = KAM.material_block(before, after, len(found))
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
    base = cache_base or KAM.default_base()
    if KAM.is_production_out(out, base, root, STATES_REL):
        raise Stop(u"**本番の記録を使い捨ての材料から作らない。止める**")
    if os.path.exists(out):
        raise Stop(u"**出力が既に在る: %s。測り直さない。止める**" % os.path.basename(out))
    n_rows, groups = shape or (N_ROWS, GROUP_COUNTS)
    pop = KAM.validate_population(population if population is not None else read_population(root), n_rows, groups)
    before = KAM.folder_snapshots(base)
    found = KAM.scan_material(base, pop)
    jobs = [(n, g, sha, found[sha][0]) for (n, g, sha) in pop]
    say(u"states %d 本 × 3 つの節 × %s ― procs %d" % (len(jobs), PROFILE, procs))
    t0 = clock()
    books = TS.NF.map_pool(states_job, jobs, procs)
    elapsed = clock() - t0
    after = KAM.folder_snapshots(base)
    if before != after:
        raise Stop(u"**材料の folder の件数か名前が変わった。記録を書かずに止める**")
    rec = header(root, u"YS(有報の 3 つの節の文を同じ有報の fact で確かめる)― 201 本の切り出し・判定(0 USD・通信なし)", ST.sha256_file(os.path.abspath(__file__)))
    rec[u"KAM の script の sha256"] = ST.sha256_file(os.path.join(HERE, os.path.basename(KAM_SCRIPT_REL)))
    rec[u"2026-11-09 の便の script の sha256"] = ST.sha256_file(os.path.join(HERE, os.path.basename(TS_SCRIPT_REL)))
    rec[u"TSS の script の sha256"] = ST.sha256_file(os.path.join(HERE, os.path.basename(TSS_SCRIPT_REL)))
    rec[u"封の表の sha256"] = ST.sha256_file(os.path.join(root, SEAL_REL))
    rec[u"母集団の表(# TAB 群 TAB sha256 の行)の sha256"] = KAM.table_digest(pop)
    rec[u"engine の指紋"] = VD.engine_fingerprint()
    rec[u"profile"] = PROFILE
    rec[u"材料"] = KAM.material_block(before, after, len(found))
    rec[u"切り出し"] = collections.OrderedDict([
        (u"member", u"名前に /PublicDoc/ を含み .htm で終わるもの(名前の順に utf-8 strict で全部読む)"),
        (u"札の名前", collections.OrderedDict((s, nm) for s, nm in SECTIONS.items())),
        (u"始まりの規則", START_RE), (u"深さの規則", DEPTH_RE.pattern), (u"続きありの印", CONTINUED),
        (u"NFKC", True), (u"行にする関数", u"2026-11-09 の便の html_to_lines(KAM の lines_to_text が呼ぶ)"), (u"切れない理由", list(WHYS))])
    rec[u"判定"] = collections.OrderedDict([
        (u"呼び方", u"build_modified_zip で文を差し替えた ZIP を作り、profile_rows(元の ZIP, 文, 差し替えた ZIP, P33E)。節ごとに別々に 1 回。数は 3 つの節を足さない"),
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
def section_rows(states, section, state):
    u"""[(本の #, 文の番号, 位置)]。# の順・文の番号の順・位置の順。"""
    out = []
    for b in sorted(states[u"本"], key=lambda b: b[u"#"]):
        for r in sorted((r for r in b[section][u"行"] if r[2] == state), key=lambda r: (r[0], r[1])):
            out.append((b[u"#"], r[0], r[1]))
    return out


def reading_items(states):
    u"""{読みの組: [(組の通し番号(1 から), 本の #, 文の番号, 位置)]}。V・G 配当は全部、G 研究・G 設備は節ごとに 60 行を引く。"""
    out = collections.OrderedDict()
    for label, (section, state, draw) in READ_SETS.items():
        rows = section_rows(states, section, state)
        if draw:
            rows = [rows[j] for j in TSS.pick_sample(len(rows), seed=READ_SEED, k=READ_N)]
        out[label] = [(i + 1,) + r for i, r in enumerate(rows)]
    return out


def sheet_intro():
    return u"\n".join([
        u"# YS の便 ― 読むための紙(repo の外。追跡しない)",
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
    pop = KAM.validate_population(population if population is not None else read_population(root), n_rows, groups)
    byn = dict((r[0], r) for r in pop)
    base = cache_base or KAM.default_base()
    found = KAM.scan_material(base, pop)
    need = collections.OrderedDict()                                     # (本の #, 節) → [(組, 通し番号, 文の番号, 位置)]
    for label, its in items.items():
        section = READ_SETS[label][0]
        for it in its:
            need.setdefault((it[1], section), []).append((label, it))
    chunks = {}
    for (num, section), lst in sorted(need.items(), key=lambda kv: (kv[0][0], list(SECTIONS).index(kv[0][1]))):
        sha = byn[num][2]
        zb = KAM.read_zip(found[sha][0], num)
        if ST.sha256_bytes(zb) != sha:
            raise Stop(u"**材料の ZIP の sha256 が封の表と違う(# %d)。止める**" % num)
        text, why = cut_section(zb, section)
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
        rec_rows = dict(((r[0], r[1]), r) for r in next(b for b in states[u"本"] if b[u"#"] == num)[section][u"行"])
        for label, it in lst:
            key = (it[2], it[3])
            c = keyed.get(key)
            want_state = READ_SETS[label][1]
            if c is None or c["state"] != want_state or key not in rows or KAM.row10(key, rows[key]) != rec_rows.get(key):
                raise Stop(u"**読む行が記録と合わない(%s %d)。止める**" % (label, it[0]))
            chunks[(label, it[0])] = KAM.sheet_text(label, it, c, sents[it[2]], KAM.row10(key, rows[key])[9])
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
    return TYPES_G if label in G_LABELS else TYPES_V


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
    rec = header(root, u"YS ― 読む行の型分け(0 USD)", ST.sha256_file(os.path.abspath(__file__)))
    rec[u"states の記録の sha256"] = ST.sha256_file(os.path.abspath(states_path))
    rec[u"型を付けた席"] = TYPED_BY
    rec[u"盲検"] = u"盲検ではない(封の予測を知ったうえで付けた)。(ク) は候補で、紙面で確かめていない"
    rec[u"読む行の規則"] = collections.OrderedDict([
        (u"V 研究・V 設備・V 配当", u"その節の VALUE_MISMATCH の全部の行"), (u"G 配当", u"配当政策の GROUNDED の全部の行"),
        (u"G 研究・G 設備", u"その節の GROUNDED の行を # の順・文の番号の順・位置の順に並べ、節ごとに新しい random.Random(種).sample(range(行の数), 引く数) を番号の順に。行の数が引く数に満たなければ全部"),
        (u"種", READ_SEED), (u"引く数", READ_N),
        (u"G 研究の行の数", len(section_rows(states, u"研究開発活動", G))), (u"G 設備の行の数", len(section_rows(states, u"設備投資等の概要", G))),
        (u"読む行の数", collections.OrderedDict((label, len(its)) for label, its in items.items())),
        (u"読む行の数の合計", sum(len(its) for its in items.values()))])
    rec[u"型の字"] = collections.OrderedDict([(u"V", collections.OrderedDict(TYPES_V)), (u"G", collections.OrderedDict(TYPES_G)), (u"違うもの", list(DIFFS))])
    counts = collections.OrderedDict()
    for label, its in items.items():
        c = collections.Counter(typed[(label, it[0])][0] for it in its)
        counts[label] = collections.OrderedDict((t, c.get(t, 0)) for t in types_of(label))
    rec[u"型の集計"] = counts
    diffs = collections.OrderedDict()
    for label in G_LABELS:
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
