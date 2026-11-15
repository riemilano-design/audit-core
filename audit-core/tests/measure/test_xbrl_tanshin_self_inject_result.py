# -*- coding: utf-8 -*-
"""結果の門: 封 docs/XBRL_TANSHIN_SELF_INJECT_SEAL_2026-11-14.md §2 の 7(TSS の便 1b ― 短信の概況の文に誤りを 1 件ずつ入れ、同じ短信の財務諸表に当てて止めるかを測る)。

封の門 ``test_xbrl_tanshin_self_inject_seal.py`` の次の段。**追跡されている記録 2 つ・第 1 便と第 2 便の判定の記録・封・結果の文書だけを読む**(cache の材料が無い機械でも緑。注入を走らせ直さない)。

縛るもの(検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表で 1 本ずつ)
 a 記録 2 つと script の sha256(字で留める)
 b 記録の来歴の欄(欄の名前・script と前の便の sha256・仕掛けと lib の sha256・engine の指紋・材料・配線・切り替え・種・cap・HEAD の commit)
 c 行(3,726 行)を 1 行ずつ見て、集計・覆い・土台の確かめ・母集団を行と第 1 便・第 2 便の記録から数え直す(script の集計は呼ばない)
 d 通した行の札の記録: 行の id・型・本の # が注入の記録の「通した」の行と 1 対 1・札の集計・札の字
 e 記録に文も値も会社名も証券コードも pointer の字も無い・key_leaks が空
 f 結果の文書の 11 の塊を記録から作り直して 1 行ずつ照らす・塊の外の 2 桁以上の数は記録から作った数の集合の中にあること・予測 V-1〜V-11 の判定を記録と封の幅から作り直す
 g 封が bcc244ae から 1 字も変わっていない・順序(commit の順。未 commit は赤)・engine 0 行・script が ac10c814 から変わっていない
この file は docID の字を持たない。「2 回目の走り」の記録は追跡しない(実装の席が scratchpad に置いた 1 本)。その byte 比較は環境変数 ``AUDIT_CORE_TSS1B_RUN2`` に path を渡したときだけ走る。
"""
import collections
import copy
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
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


SG = load_module("tests/measure/test_xbrl_tanshin_self_inject_seal.py", "tanshin_self_inject_seal_gate_for_inject_result_gate")      # 封の門の部品。門としては走らせない
PR = SG.PR
MS = SG.MS

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
SCRIPT_REL = SG.SCRIPT_REL
DOC_REL = SG.DOC_REL
INJECT_REL = SG.INJECT_REL
PASSED_REL = SG.PASSED_TYPES_REL
GATE_REL = SG.LATER_GATE_REL
SEAL_GATE_REL = SG.GATE_REL
STATES_REL = SG.STATES_REL
INTERIM_REL = SG.INTERIM_REL
POP_REL = SG.POPULATION_REL
S2_REL, TSS_REL, STAGE_REL, TS_REL = SG.S2_REL, SG.TSS_REL, SG.STAGE_REL, SG.TS_REL
SITES_REL, INJECTPY_REL, NUMBERS_REL, SCALES_REL = "measure/lib/sites.py", "measure/inject.py", "measure/lib/numbers.py", "measure/lib/scales.py"
RECORD_RELS = (INJECT_REL, PASSED_REL)
SCRIPT_COMMIT = "ac10c814"                                 # script と封の門を足した commit(この commit から script は 0 行)

# ---- 字で留める(記録・script の sha256。人が決めた数は字で留める)
SHA_PIN = collections.OrderedDict([
    (INJECT_REL, "ea9a2e22932f0c5f4c8158291b0fa224c47709b07bb1fd4f61b3a64e8148b742"),
    (PASSED_REL, "6387b09d9e51f20da9e7fd8d2cf36ba5d006b7f72d93da3d56f2fe1bdb8aa01b"),
    (SCRIPT_REL, "ad33fef1537cfb7a0d866dfe38576abe0528b441f50512e03ad72232a7cc2c9a")])
RUN2_SHA = "d411966cdd392b3c8f5920e92cba72b08816fd04555905422f83553b3a59b83f"     # 2 回目の走り(追跡しない。scratchpad の 1 本)の sha256
RUN1_TIME, RUN2_TIME = 804.1, 825.6
GROUP_A, GROUP_B = u"A", u"丙"
GROUPS = (GROUP_A, GROUP_B)
BOOK_GROUP = {u"甲": GROUP_A, u"乙": GROUP_A, u"丙": GROUP_B}
TYPE_NAMES = ("T1_VALUE", "T5_COINCIDENT", "T8_REL", "T9_PRIOR_TO_CURRENT")
SHORT = {"T1_VALUE": u"T1", "T5_COINCIDENT": u"T5", "T8_REL": u"T8", "T9_PRIOR_TO_CURRENT": u"T9"}
W_PASS, W_NAMED, W_OTHER, W_PNF, W_UNV, W_UNM = SG.RESULT_WORDS
WORDS = SG.RESULT_WORDS
WORD_STATE = {W_PASS: u"GROUNDED", W_NAMED: u"VALUE_MISMATCH", W_OTHER: u"VALUE_MISMATCH", W_PNF: u"POINTER_NOT_FOUND", W_UNV: u"UNVERIFIABLE", W_UNM: None}
PRELIM_BOOKS = tuple(range(1, 13)) + tuple(range(251, 259))                  # V-1 の下調べの 20 本(封 §0-1 の 2)
PRELIM = collections.OrderedDict([                                          # 封 §0-1 の 4 の表(型 → 注入の行・通した・名指して原本・名指したが別・PNF・届いた)
    ("T1_VALUE", (16, 0, 16, 0, 0, 16)), ("T5_COINCIDENT", (22, 0, 4, 0, 18, 22)), ("T8_REL", (95, 0, 74, 3, 18, 95)), ("T9_PRIOR_TO_CURRENT", (2, 0, 1, 0, 1, 2))])
V4_BOUNDS = collections.OrderedDict([                                       # 封 §3 の V-4(群・型 → 幅)
    ((GROUP_A, "T1_VALUE"), (150, 700)), ((GROUP_A, "T5_COINCIDENT"), (150, 900)), ((GROUP_A, "T8_REL"), (900, 2000)),
    ((GROUP_B, "T1_VALUE"), (0, 150)), ((GROUP_B, "T5_COINCIDENT"), (0, 150)), ((GROUP_B, "T8_REL"), (400, 1100))])
V5_BOUNDS = collections.OrderedDict([                                       # 封 §3 の V-5(群・型 → 通した率の上限(%)。T1 は 0 件 = 上限 0)
    ((GROUP_A, "T1_VALUE"), 0.0), ((GROUP_A, "T5_COINCIDENT"), 2.0), ((GROUP_A, "T8_REL"), 1.5),
    ((GROUP_B, "T1_VALUE"), 0.0), ((GROUP_B, "T5_COINCIDENT"), 2.0), ((GROUP_B, "T8_REL"), 2.0)])
V7_T1_MIN, V7_T8_RANGE = 80.0, (60.0, 90.0)
V8_BOUNDS = {GROUP_A: (60.0, 88.0), GROUP_B: (50.0, 90.0)}
V9_MIN = 85.0
V10_ROWS, V10_PASS_MAX = (5, 80), 20.0
V6_REACHED_MIN = 98.0
V11_ROWS_MAX, V11_UNMAPPED_MAX = 10, 3.0
BOUND_PHRASES = (u"150〜700", u"150〜900", u"900〜2,000", u"0〜150", u"400〜1,100", u"0〜2.0%", u"0〜1.5%", u"80% 以上", u"60〜90%", u"60〜88%", u"50〜90%", u"85% 以上",
                 u"5〜80 行", u"20% 以下", u"98% 以上", u"10 行以下", u"3% 以下")
TOP_KEYS = (u"seal", u"封の commit", u"step", u"HEAD の commit", u"この script の sha256", u"第 2 便の script の sha256", u"TSS の script の sha256", u"置く script の sha256",
            u"2026-11-09 の便の script の sha256", u"仕掛けの 2 file の sha256", u"lib の指紋", u"engine の指紋", u"母集団の記録の sha256", u"TSS の判定の記録の sha256", u"interim の記録の sha256",
            u"profile", u"材料", u"配線", u"切り替え", u"種", u"cap", u"型", u"refs の作り", u"母集団", u"土台の確かめ", u"本ごとの数え", u"注入の行の数", u"集計", u"覆い", u"限界",
            u"欄名の注記", u"行の欄", u"時間(秒)", u"key_leaks", u"行")
PASSED_KEYS = (u"seal", u"封の commit", u"step", u"HEAD の commit", u"この script の sha256", u"inject の記録の sha256", u"札を付けた席", u"盲検", u"読む行の規則", u"札の字",
               u"札の集計", u"行の欄", u"行", u"key_leaks")
INJECT_STEP = u"TSS 便 1b(注入)― 短信の概況の文に T1・T5・T8・T9 を 1 件ずつ入れ、同じ短信の財務諸表に当てる(P33E・切り替え 2 つ 真・0 USD・通信なし)"
PASSED_STEP = u"TSS 便 1b(注入)― 通した行を読んだ札(0 USD)"
PASSED_BLIND = u"盲検ではない(封の予測を知ったうえで付けた)"
ROW_COLS = [u"本の #", u"群", u"id", u"型", u"形", u"単位", u"基準の claim", u"P32E の土台に対応", u"round-trip", u"読み直し", u"先頭の位が減った", u"engine の手がかり", u"文に前期の語",
            u"基準の pointer の期", u"r", u"r を決めた回", u"P33E", u"P33E の注入後の pointer の期", u"届いた", u"P33E の対応の条件", u"P33E の欠けた条件", u"旧の対応(P33E)",
            u"注入の前後で claim の数が同じ(P32E)", u"相手の fact の期", u"相手と同じ要素か"]
PASSED_COLS = [u"番号", u"本の #", u"id", u"型", u"札"]
ROW_ID_RE = re.compile(r"^B(\d+)-T(\d)-(\d\d)$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
FORBIDDEN_WORDS = (u"ハルシネーション", u"証明した", u"LLM より正確", u"世界で 1 社")
DOCID_RE = re.compile(r"S100[0-9A-Z]{4}")
TDNET_RE = re.compile(r"0812\d{14}")
CODE_RE = re.compile(r"(?<![0-9A-Za-z_\-])\d{3}[0-9A-Z](?![0-9A-Za-z_\-])")
POINTER_RE = re.compile(r"xbrl:|jppfs|jpcrp|jpdei|_cor:|@(Current|Prior)|formula:")
COMPANY_WORDS = (u"株式会社", u"有限会社", u"合同会社", u"㈱", u"(株)")
KANJI_NUM_RE = re.compile(u"[二三四五六七八九]百|[一二三四五六七八九]千|百[一二三四五六七八九十]|千[一二三四五六七八九百]")        # 3 桁以上の数を漢数字で逃がす字(「百万円」の単位は当たらない)
JA_RE = re.compile(u"[぀-ヿ一-鿿]")
LONG_JA = 40
FORBIDDEN_KEYS = tuple(MS.TS.RUN.FORBIDDEN_KEYS) + (u"pointers", u"pointer", u"要素", u"element", u"context", u"label", u"会社名", u"subject", u"span", u"value", u"text", u"文")
#: 規則・手順の説明を持つ header の欄(ここの下の長い日本語は文でなく説明)。行・集計・覆い・本ごとには文を置かない
LONG_TEXT_TOP = (u"step", u"型", u"土台の確かめ", u"refs の作り", u"限界", u"欄名の注記", u"材料", u"札を付けた席", u"盲検", u"札の字", u"読む行の規則")
BLOCK_NAMES = (u"wiring", u"prov", u"pred", u"cells", u"tally", u"v1", u"main", u"cover", u"passed", u"limits", u"note")
LIMIT_QUOTE_NEEDLE = u"人の目の札は無い"                        # 限界の字(記録と同じ)の中の否定の用例。この 1 文を除いた外で「人の目」を書かない


# ======================================================================================================
# 道具
def read(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def read_bytes(rel):
    with io.open(os.path.join(ROOT, rel), "rb") as fh:
        return fh.read()


def sha256_rel(rel):
    return hashlib.sha256(read_bytes(rel)).hexdigest()


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


def rate(a, b):
    return round(100.0 * a / b, 1) if b else 0.0


_TEXT = {}


def cached_text(rel):
    if rel not in _TEXT:
        _TEXT[rel] = read(rel)
    return _TEXT[rel]


_CUR = {}


def current():
    u"""今の file の sha256 と engine の指紋(1 回だけ測る。変異は ``Ctx.cur`` の写しを変える)。"""
    if not _CUR:
        _CUR.update({"script": sha256_rel(SCRIPT_REL), "s2": sha256_rel(S2_REL), "tss": sha256_rel(TSS_REL), "stage": sha256_rel(STAGE_REL), "prev": sha256_rel(TS_REL),
                     "sites": sha256_rel(SITES_REL), "injectpy": sha256_rel(INJECTPY_REL), "numbers": sha256_rel(NUMBERS_REL), "scales": sha256_rel(SCALES_REL),
                     "pop": sha256_rel(POP_REL), "states": sha256_rel(STATES_REL), "interim": sha256_rel(INTERIM_REL), "inject": sha256_rel(INJECT_REL), "fp": MS.VD.engine_fingerprint()})
    return _CUR


_SHARED = {}


def shared_json(rel):
    if rel not in _SHARED:
        _SHARED[rel] = json.loads(cached_text(rel))
    return _SHARED[rel]


class Ctx(object):
    u"""記録・封・文書・今の file の値。変異は毎回 ``Ctx()`` の新しい写しに 1 か所だけ加える。"""

    def __init__(self):
        self.R = json.loads(cached_text(INJECT_REL))
        self.P = json.loads(cached_text(PASSED_REL))
        self.S = shared_json(STATES_REL)                    # 重いので共有。この 2 つを変える変異は先に ``c.S = copy.deepcopy(c.S)`` で写しを作る(test_m_2 が共有の側が無傷かを見る)
        self.I = shared_json(INTERIM_REL)
        self.seal = cached_text(SEAL_REL)
        self.doc = cached_text(DOC_REL) if os.path.exists(os.path.join(ROOT, DOC_REL)) else u""
        self.texts = collections.OrderedDict((rel, read_bytes(rel)) for rel in SHA_PIN)
        self.cur = dict(current())


# ======================================================================================================
# a. sha256
def sha_problems(texts):
    out = []
    for rel, want in SHA_PIN.items():
        if hashlib.sha256(texts.get(rel, b"")).hexdigest() != want:
            out.append(u"sha256: %s が字で留めた値と違う" % rel)
    return out


# ======================================================================================================
# 母集団(第 1 便・第 2 便の判定の記録から数える)
def cut_books(c):
    u"""{本の #: 群の名前(甲・乙・丙)}。切れた本だけ。A は第 1 便の記録の # 250 以下・丙は第 2 便(interim)の記録。"""
    d = {}
    for b in c.S[u"本"]:
        if b[u"#"] <= 250 and b[u"切り出し"] == u"切れた":
            d[b[u"#"]] = b[u"群"]
    for b in c.I[u"本"]:
        if b[u"切り出し"] == u"切れた":
            d[b[u"#"]] = b[u"群"]
    return d


def grounded_rows(c):
    u"""{本の #: P33E が GROUNDED の行の数}(切れた本。第 1 便・第 2 便の判定の記録の行から)。"""
    d = {}
    for b in c.S[u"本"]:
        if b[u"#"] <= 250 and b[u"切り出し"] == u"切れた":
            d[b[u"#"]] = sum(1 for r in b[u"行"] if r[2] == u"GROUNDED")
    for b in c.I[u"本"]:
        if b[u"切り出し"] == u"切れた":
            d[b[u"#"]] = sum(1 for r in b[u"行"] if r[2] == u"GROUNDED")
    return d


def all_rows_count(c):
    n = sum(len(b[u"行"]) for b in c.S[u"本"] if b[u"#"] <= 250 and b[u"切り出し"] == u"切れた")
    return n + sum(len(b[u"行"]) for b in c.I[u"本"] if b[u"切り出し"] == u"切れた")


def grp_of(r):
    return BOOK_GROUP.get(r.get(u"群"), u"?")


def rows_by(c):
    d = collections.OrderedDict(((g, t), []) for g in GROUPS for t in TYPE_NAMES)
    for r in c.R[u"行"]:
        k = (grp_of(r), r.get(u"型"))
        if k in d:
            d[k].append(r)
    return d


def word_of(r):
    return r[u"P33E"][u"結果"]


def mapped(r):
    return r[u"P33E"][u"対応"] is True


# ======================================================================================================
# b. 来歴
def head_ok(root, c):
    return bool(isinstance(c, str) and HEX40.match(c)) and PR.is_anc(root, SCRIPT_COMMIT, c)


def provenance_problems(c, root=REPO):
    out = []
    R, P, cur = c.R, c.P, c.cur
    if tuple(R.keys()) != TOP_KEYS:
        out.append(u"来歴[inject]: 欄の名前・順が字で留めたものと違う")
    if tuple(P.keys()) != PASSED_KEYS:
        out.append(u"来歴[札]: 欄の名前・順が字で留めたものと違う")
    for name, rec, step in ((u"inject", R, INJECT_STEP), (u"札", P, PASSED_STEP)):
        if rec.get(u"seal") != SEAL_REL or rec.get(u"封の commit") != SEAL_COMMIT_SHORT:
            out.append(u"来歴[%s]: seal・封の commit が違う" % name)
        if rec.get(u"step") != step:
            out.append(u"来歴[%s]: step の字が違う" % name)
        if rec.get(u"key_leaks") != []:
            out.append(u"来歴[%s]: key_leaks が空でない" % name)
        if not head_ok(root, rec.get(u"HEAD の commit")):
            out.append(u"来歴[%s]: HEAD の commit が script を足した commit を含まない" % name)
        if rec.get(u"この script の sha256") != cur["script"]:
            out.append(u"来歴[%s]: この script の sha256 が今の file と違う" % name)
    if P.get(u"inject の記録の sha256") != cur["inject"]:
        out.append(u"来歴[札]: inject の記録の sha256 が今の file と違う")
    for key, k2 in ((u"第 2 便の script の sha256", "s2"), (u"TSS の script の sha256", "tss"), (u"置く script の sha256", "stage"), (u"2026-11-09 の便の script の sha256", "prev"),
                    (u"母集団の記録の sha256", "pop"), (u"TSS の判定の記録の sha256", "states"), (u"interim の記録の sha256", "interim")):
        if R.get(key) != cur[k2]:
            out.append(u"来歴[inject]: %s が今の file と違う" % key)
    if R.get(u"仕掛けの 2 file の sha256") != {SITES_REL: cur["sites"], INJECTPY_REL: cur["injectpy"]}:
        out.append(u"来歴[inject]: 仕掛けの 2 file の sha256 が今の file と違う")
    if R.get(u"lib の指紋") != {NUMBERS_REL: cur["numbers"], SCALES_REL: cur["scales"]}:
        out.append(u"来歴[inject]: lib の指紋が今の file と違う")
    fp = R.get(u"engine の指紋") or {}
    for k in (u"adapter_xbrl_py_sha256", u"core_py_sha256", u"adapter_xbrl_py_files", u"core_py_files"):
        if fp.get(k) != cur["fp"][k]:
            out.append(u"来歴[inject]: engine の指紋 %s が今の engine と違う" % k)
    if fp.get(u"git_commit") != R.get(u"HEAD の commit"):
        out.append(u"来歴[inject]: engine の指紋の git_commit が HEAD の commit と違う")
    if R.get(u"profile") != u"P33E":
        out.append(u"来歴[inject]: profile が P33E でない")
    m = R.get(u"材料") or {}
    z = m.get(u"置き場の一覧の前後") or {}
    if m.get(u"表と一致した ZIP") != 400 or z.get(u"変化なし") is not True or z.get(u"前") != z.get(u"後") or not isinstance(z.get(u"前"), list) or z[u"前"][0] != 400 \
            or not HEX64.match(str(z[u"前"][1])):
        out.append(u"来歴[inject]: 材料が「400・前後の変化なし」でない")
    if m.get(u"置き場") != u"~/.cache/audit-core/tanshin-self-2026-11-14":
        out.append(u"来歴[inject]: 材料の置き場が違う")
    w = R.get(u"配線") or {}
    pair = {u"TS.INJECT_PROFILES": [u"P33E", u"P33E"], u"TS.OLD": u"P33E", u"TS.NEW": u"P33E"}
    inside = w.get(u"with の中") or {}
    if any(inside.get(k) != v for k, v in pair.items()) or inside.get(u"切り替え yen_scan_2026_11_05") is not True or inside.get(u"切り替え t5_yen_2026_11_06") is not True:
        out.append(u"来歴[inject]: with の中の対・切り替えが「P33E の対・切り替え 2 つ 真」でない")
    if inside.get(u"RM.INJECT_PROFILES") != (w.get(u"with の前") or {}).get(u"RM.INJECT_PROFILES") or inside.get(u"RM.INJECT_PROFILES") != (w.get(u"with の後") or {}).get(u"RM.INJECT_PROFILES") \
            or not isinstance(inside.get(u"RM.INJECT_PROFILES"), list):
        out.append(u"来歴[inject]: RM.INJECT_PROFILES が with の前・中・後で同じでない")
    if w.get(u"with の中の届き方の問題") != [] or w.get(u"元に戻った") is not True or w.get(u"with の前") != w.get(u"with の後") or w.get(u"2026-11-09 の便の wiring_problems(with の外・前と後)") != []:
        out.append(u"来歴[inject]: 配線の「届き方の問題 空・元に戻った・前と後が同じ」でない")
    before = w.get(u"with の前") or {}
    if before.get(u"切り替え yen_scan_2026_11_05") is not False or before.get(u"切り替え t5_yen_2026_11_06") is not False or before.get(u"TS.INJECT_PROFILES") == [u"P33E", u"P33E"]:
        out.append(u"来歴[inject]: with の前が「偽・偽・P33E の対でない」でない")
    sw = R.get(u"切り替え") or {}
    if (sw.get(u"名前"), sw.get(u"inject の中の値"), sw.get(u"出たあとの値"), sw.get(u"T5 の切り替えの名前"), sw.get(u"T5 の切り替え inject の中の値"), sw.get(u"T5 の切り替え 出たあとの値")) != \
            (u"yen_scan_2026_11_05", True, False, u"t5_yen_2026_11_06", True, False):
        out.append(u"来歴[inject]: 切り替えの欄が違う")
    if R.get(u"種") != 20261114 or not is_int(R.get(u"種")) or R.get(u"cap") != 10 or not is_int(R.get(u"cap")):
        out.append(u"来歴[inject]: 種・cap が封の 20261114・10 でない")
    if R.get(u"限界") != list(MS.INJECT_LIMITS) or R.get(u"限界") != seal_limits(c.seal):
        out.append(u"来歴: 限界が script の字・封 §6 の字と違う")
    if R.get(u"欄名の注記") != MS.FIELD_NAME_NOTE:
        out.append(u"来歴: 欄名の注記が script の字と違う")
    if R.get(u"行の欄") != ROW_COLS or P.get(u"行の欄") != PASSED_COLS:
        out.append(u"来歴: 行の欄が封のとおりでない")
    t = R.get(u"時間(秒)")
    if isinstance(t, bool) or not isinstance(t, (int, float)) or t != RUN1_TIME:
        out.append(u"来歴[inject]: 時間(秒)が 1 回目の 804.1 でない")
    if P.get(u"札を付けた席") != MS.TYPED_BY or P.get(u"盲検") != PASSED_BLIND or P.get(u"札の字") != dict(MS.PASSED_LABELS) or list(P.get(u"札の字", {}).keys()) != [u"a", u"b", u"c", u"d"]:
        out.append(u"来歴[札]: 札を付けた席・盲検・札の字が封のとおりでない")
    return out


def seal_limits(seal):
    u"""封 §6 の限界の箇条(「- 」の後の字)。"""
    sec = seal[seal.index(u"## §6"):seal.index(u"## §7")]
    return [m.group(1) for m in re.finditer(r"^- (.*)$", sec, re.M)]


# ======================================================================================================
# c. 行・集計・覆い
def rows_problems(c):
    u"""3,726 行を 1 行ずつ。形・id・群・型・結果の語と state の対・届いた・並び。"""
    out = []
    rows = c.R.get(u"行") or []
    books = cut_books(c)
    if c.R.get(u"注入の行の数") != len(rows) or not rows:
        out.append(u"行: 注入の行の数が行の数と違う")
    seen = set()
    last = 0
    cols = set(ROW_COLS)
    for r in rows:
        if not isinstance(r, dict) or not set(r.keys()) <= cols or not set([u"本の #", u"群", u"id", u"型", u"P33E", u"届いた", u"round-trip", u"読み直し"]) <= set(r.keys()):
            return out + [u"行: 欄が封の行の欄の部分集合でない・必要な欄が無い"]
        n = r[u"本の #"]
        m = ROW_ID_RE.match(r[u"id"]) if isinstance(r[u"id"], str) else None
        if not is_int(n) or n not in books or books[n] != r[u"群"]:
            out.append(u"行: 本の # が切れた本でない・群が第 1 便・第 2 便の記録と違う(%s)" % r.get(u"id"))
        if m is None or int(m.group(1)) != n or r[u"型"] not in TYPE_NAMES or m.group(2) != SHORT[r[u"型"]][1]:
            out.append(u"行: id の形が B<本の #>-T<型>-<番号> でない・本の #・型と合わない(%s)" % r.get(u"id"))
        if r[u"id"] in seen:
            out.append(u"行: id が重なっている(%s)" % r[u"id"])
        seen.add(r[u"id"])
        if is_int(n) and n < last:
            out.append(u"行: 本の # の並びが昇順でない")
        last = n if is_int(n) else last
        p = r[u"P33E"]
        if not isinstance(p, dict) or p.get(u"結果") not in WORDS or WORD_STATE[p[u"結果"]] != p.get(u"state") or not isinstance(p.get(u"対応"), bool) or (p[u"結果"] == W_UNM) == p[u"対応"]:
            out.append(u"行: P33E の結果の語・state・対応が封の語の対応と合わない(%s)" % r[u"id"])
        elif p[u"対応"] is True and r[u"届いた"] is not True:
            out.append(u"行: 対応が付いたのに届いた でない(%s)" % r[u"id"])
        if not isinstance(r[u"届いた"], bool) or not isinstance(r[u"round-trip"], bool) or not isinstance(r[u"読み直し"], bool):
            out.append(u"行: 届いた・round-trip・読み直し が真偽でない(%s)" % r[u"id"])
    return out


def agg_want(c):
    u"""集計(群 × 型)を行から数え直す。"""
    out = collections.OrderedDict()
    by = rows_by(c)
    for g in GROUPS:
        out[g] = collections.OrderedDict()
        for t in TYPE_NAMES:
            rs = by[(g, t)]
            n = len(rs)
            cnt = collections.Counter(word_of(r) for r in rs)
            m = [r for r in rs if mapped(r)]
            rch = sum(1 for r in m if r[u"届いた"] is True)
            ps = [r for r in rs if word_of(r) == W_PASS]
            out[g][t] = collections.OrderedDict([
                (u"注入の行", n),
                (u"結果の語", collections.OrderedDict((w, collections.OrderedDict([(u"件", cnt.get(w, 0)), (u"率", rate(cnt.get(w, 0), n))])) for w in WORDS)),
                (u"対応が付いた行", len(m)),
                (u"届いた", collections.OrderedDict([(u"件", rch), (u"率(分母は対応が付いた行)", rate(rch, len(m)))])),
                (u"通した", collections.OrderedDict([(u"件", len(ps)), (u"率", rate(len(ps), n)), (u"うち届いた", sum(1 for r in ps if r[u"届いた"] is True)),
                                                  (u"うち届いていない", sum(1 for r in ps if r[u"届いた"] is not True))])),
                (u"round-trip 不一致", sum(1 for r in rs if r[u"round-trip"] is not True)),
                (u"読み直し不一致", sum(1 for r in rs if r[u"読み直し"] is not True))])
    return out


def plain(x):
    return json.loads(json.dumps(x, ensure_ascii=False))


def agg_problems(c):
    out = []
    got = c.R.get(u"集計") or {}
    if list(got.keys()) != list(GROUPS):
        return [u"集計: 群が A・丙 でない"]
    want = agg_want(c)
    for g in GROUPS:
        if list((got.get(g) or {}).keys()) != list(TYPE_NAMES):
            out.append(u"集計[%s]: 型が T1・T5・T8・T9 でない" % g)
            continue
        for t in TYPE_NAMES:
            if plain(got[g][t]) != plain(want[g][t]):
                out.append(u"集計[%s・%s]が行から数え直した値と違う" % (g, SHORT[t]))
    return out


def coverage_want(c):
    books = cut_books(c)
    gr = grounded_rows(c)
    by = rows_by(c)
    per_book = collections.Counter((r[u"本の #"], r[u"型"]) for r in c.R[u"行"])
    return books, gr, by, per_book


def coverage_problems(c):
    out = []
    cov = c.R.get(u"覆い") or {}
    grp = cov.get(u"群ごと") or {}
    bk = cov.get(u"本ごと") or []
    if list(grp.keys()) != list(GROUPS) or list(cov.keys()) != [u"群ごと", u"本ごと"]:
        return [u"覆い: 欄が 群ごと・本ごと でない・群が A・丙 でない"]
    books, gr, by, per_book = coverage_want(c)
    if [b.get(u"#") for b in bk] != sorted(books):
        return out + [u"覆い: 本ごとが切れた本の # の昇順でない"]
    rows_cnt = collections.Counter((r[u"本の #"], r[u"型"]) for r in c.R[u"行"])
    for b in bk:
        n = b[u"#"]
        if b.get(u"群") != books[n] or b.get(u"名前") != u"B%d" % n:
            out.append(u"覆い: 本 %d の群・名前が違う" % n)
        if b.get(u"P33E が GROUNDED の行") != gr[n]:
            out.append(u"覆い: 本 %d の GROUNDED の行が第 1 便・第 2 便の記録と違う" % n)
        inj = b.get(u"注入の行") or {}
        if [inj.get(SHORT[t]) for t in TYPE_NAMES] != [rows_cnt.get((n, t), 0) for t in TYPE_NAMES]:
            out.append(u"覆い: 本 %d の型ごとの注入の行が行の数と違う" % n)
        if list((b.get(u"作れる site") or {}).keys()) != [SHORT[t] for t in TYPE_NAMES] or any(not is_int(v) or v < inj.get(k, 0) for k, v in (b.get(u"作れる site") or {}).items()):
            out.append(u"覆い: 本 %d の作れる site が型ごとの数でない・注入の行より少ない" % n)
        if not is_int(b.get(u"円族の token")) or b[u"円族の token"] < 0 or not is_int(b.get(u"refs の数")) or not is_int(b.get(u"refs で飛ばした fact")) or not isinstance(b.get(u"全角の数字で注入しない"), bool):
            out.append(u"覆い: 本 %d の token・refs・全角の欄の形が違う" % n)
    for g in GROUPS:
        bs = [b for b in bk if BOOK_GROUP[books[b[u"#"]]] == g]
        got_g = grp[g]
        g1 = [b for b in bs if b[u"P33E が GROUNDED の行"] >= 1]
        inj1 = [b for b in bs if sum(b[u"注入の行"].values()) >= 1]
        want = collections.OrderedDict([
            (u"切れた本", len(bs)), (u"P33E が GROUNDED の行の合計", sum(b[u"P33E が GROUNDED の行"] for b in bs)), (u"円族の token の合計", sum(b[u"円族の token"] for b in bs)),
            (u"GROUNDED が 1 行以上の本", len(g1)), (u"注入の行が 1 行以上の本", len(inj1)),
            (u"注入の行が 1 行以上の本(分母は GROUNDED が 1 行以上の本)", collections.OrderedDict([(u"件", len(inj1)), (u"率", rate(len(inj1), len(g1)))])),
            (u"全角の数字で注入しない本", sum(1 for b in bs if b[u"全角の数字で注入しない"])),
            (u"作れる site の合計", collections.OrderedDict((SHORT[t], sum(b[u"作れる site"][SHORT[t]] for b in bs)) for t in TYPE_NAMES)),
            (u"注入の行の合計", collections.OrderedDict((SHORT[t], len(by[(g, t)])) for t in TYPE_NAMES)),
            (u"型ごとに注入の行が 1 行以上の本", collections.OrderedDict((SHORT[t], len(set(r[u"本の #"] for r in by[(g, t)]))) for t in TYPE_NAMES)),
            (u"作れる site が 0 の本", collections.OrderedDict((SHORT[t], sum(1 for b in bs if b[u"作れる site"][SHORT[t]] == 0)) for t in TYPE_NAMES)),
            (u"refs で飛ばした fact の合計", sum(b[u"refs で飛ばした fact"] for b in bs))])
        if list(got_g.keys()) != list(want.keys()):
            out.append(u"覆い[%s]: 欄の名前・順が違う" % g)
        for k in want:
            if plain(want[k]) != plain(got_g.get(k)):
                out.append(u"覆い[%s]: %s が本ごと・行から数え直した値と違う" % (g, k))
    bd = c.R.get(u"本ごとの数え") or {}
    if sorted(bd.keys()) != sorted(u"B%d" % n for n in books):
        out.append(u"本ごとの数え: 本が切れた本の B# の集合でない")
    else:
        for n in books:
            e = bd[u"B%d" % n]
            if any(((e.get(t) or {}).get(u"採った")) != rows_cnt.get((n, t), 0) for t in TYPE_NAMES[1:]):
                out.append(u"本ごとの数え: 本 %d の T5・T8・T9 の「採った」が行の数と違う" % n)
            if not is_int((e.get(TYPE_NAMES[0]) or {}).get(u"採った")) or e[TYPE_NAMES[0]][u"採った"] < rows_cnt.get((n, TYPE_NAMES[0]), 0):
                out.append(u"本ごとの数え: 本 %d の T1 の「採った」が行の数より少ない" % n)
    return out


def base_problems(c):
    u"""母集団・土台の確かめ・refs の飛ばし・全体の数を、第 1 便・第 2 便の判定の記録から数え直す。"""
    out = []
    R = c.R
    books = cut_books(c)
    nA = sum(1 for g in books.values() if BOOK_GROUP[g] == GROUP_A)
    nB = sum(1 for g in books.values() if BOOK_GROUP[g] == GROUP_B)
    allb = len(c.S[u"本"])
    if R.get(u"母集団") != {u"対象の本(切れた本)": len(books), u"切れない本": allb - len(books), u"A": nA, u"丙": nB}:
        out.append(u"母集団: 切れた・切れない・A・丙 が第 1 便・第 2 便の記録から数えた値と違う")
    t = R.get(u"土台の確かめ") or {}
    if (t.get(u"本"), t.get(u"行"), t.get(u"違う本")) != (len(books), all_rows_count(c), 0) or len(t) != 4 or t.get(u"比べた記録") != COMPARED_NOTE:
        out.append(u"土台の確かめ: 本・行・違う本 が「切れた本の数・第 1 便と第 2 便の行の数・0」でない")
    rf = R.get(u"refs の作り") or {}
    if rf.get(u"飛ばした fact の合計") != 0 or sum(b[u"refs で飛ばした fact"] for b in (R.get(u"覆い") or {}).get(u"本ごと", [])) != 0:
        out.append(u"refs: 飛ばした fact が 0 でない")
    if (R.get(u"覆い") or {}).get(u"群ごと", {}).get(GROUP_A, {}).get(u"P33E が GROUNDED の行の合計") is None:
        out.append(u"覆い: A の GROUNDED の行の合計が無い")
    return out


# ======================================================================================================
# d. 札の記録
def passed_problems(c):
    out = []
    P = c.P
    ps = [r for r in c.R[u"行"] if word_of(r) == W_PASS]
    rows = P.get(u"行") or []
    if len(rows) != len(ps):
        out.append(u"札: 行の数が注入の記録の「通した」の行の数と違う")
    for k, (r, q) in enumerate(zip(rows, ps)):
        if not (isinstance(r, list) and len(r) == 5 and r[0] == k + 1 and is_int(r[1]) and r[4] in (u"a", u"b", u"c", u"d")):
            out.append(u"札: 行 %d が「番号(1 から)・本の #・id・型・札」でない" % (k + 1))
            break
        if r[1] != q[u"本の #"] or r[2] != q[u"id"] or r[3] != q[u"型"]:
            out.append(u"札: 行 %d の本の #・id・型が注入の記録の通した行と違う" % (k + 1))
    cnt = collections.Counter(r[4] for r in rows if isinstance(r, list) and len(r) == 5)
    if P.get(u"札の集計") != collections.OrderedDict((k, cnt.get(k, 0)) for k in (u"a", u"b", u"c", u"d")) or list((P.get(u"札の集計") or {}).keys()) != [u"a", u"b", u"c", u"d"]:
        out.append(u"札: 札の集計が行から数え直した値と違う")
    rule = P.get(u"読む行の規則") or {}
    if rule.get(u"通した行の数") != len(ps) or not rule.get(u"母集団"):
        out.append(u"札: 読む行の規則の通した行の数が違う")
    if P.get(u"key_leaks") != []:
        out.append(u"札: key_leaks が空でない")
    return out


# ======================================================================================================
# e. 記録に書かないものが漏れていない
def walk(x, acc=None):
    acc = [] if acc is None else acc
    u"""(キーか・値)の列。キーは dict の key、値は葉。"""
    if isinstance(x, dict):
        for k, v in x.items():
            acc.append((True, k))
            walk(v, acc)
    elif isinstance(x, list):
        for v in x:
            walk(v, acc)
    else:
        acc.append((False, x))
    return acc


def long_ok():
    return set(MS.INJECT_LIMITS) | set(MS.PASSED_LABELS.values()) | set([MS.FIELD_NAME_NOTE, MS.TYPED_BY, INJECT_STEP, PASSED_STEP, PASSED_BLIND])


def clean_problems(c):
    out = []
    for name, rec in ((u"inject", c.R), (u"札", c.P)):
        if rec.get(u"key_leaks") != []:
            out.append(u"clean[%s]: key_leaks が空でない" % name)
        bad = sorted(set(k for is_key, k in walk(rec) if is_key and isinstance(k, str) and k in FORBIDDEN_KEYS))
        if bad:
            out.append(u"clean[%s]: repo へ入れない欄がある: %s" % (name, u",".join(bad)))
        for top, v in rec.items():
            strict = top not in LONG_TEXT_TOP
            for is_key, s in walk({top: v}):
                if s is None or isinstance(s, (bool, int, float)):
                    continue
                if not isinstance(s, str):
                    out.append(u"clean[%s]: 葉が文字・数・真偽・null のどれでもない" % name)
                    continue
                if DOCID_RE.search(s) or TDNET_RE.search(s):
                    out.append(u"clean[%s]: docID・TDnet の番号の形の字がある" % name)
                if POINTER_RE.search(s):
                    out.append(u"clean[%s]: pointer・要素名の形の字がある" % name)
                if any(w in s for w in COMPANY_WORDS):
                    out.append(u"clean[%s]: 会社名らしい字がある" % name)
                if len(s) >= LONG_JA and JA_RE.search(s) and (not is_key and s not in long_ok() and strict):
                    out.append(u"clean[%s]: 留めた字に無い長い日本語の文がある(%s)" % (name, top))
                if CODE_RE.search(s) and not HEX64.match(s) and not HEX40.match(s):
                    out.append(u"clean[%s]: 証券コードの形の字がある(%s)" % (name, s[:12]))
    for r in c.R.get(u"行") or []:                                  # 行の中の字は閉じた語彙(文が入る場所が無い)
        for k in (u"群", u"形", u"単位", u"基準の claim", u"基準の pointer の期", u"相手の fact の期"):
            v = r.get(k)
            if v is not None and (not isinstance(v, str) or len(v) > 20):
                out.append(u"clean[inject]: 行の %s が短い語彙でない" % k)
                return out
    return out


# ======================================================================================================
# f. 結果の文書
def seal_bullets(seal):
    u"""封 §3 の V-1〜V-11 の箇条(id → 本文)。"""
    sec = seal[seal.index(u"## §3"):seal.index(u"## §4")]
    out = collections.OrderedDict()
    for m in re.finditer(r"^- \*\*(V-\d+)\*\* (.*)$", sec, re.M):
        out[m.group(1)] = m.group(2).split(u" 外れ方:")[0].strip()
    return out


def seal_problems(seal):
    out = []
    try:
        b = seal_bullets(seal)
        sec = seal[seal.index(u"## §3"):seal.index(u"## §4")]
    except ValueError:
        return [u"封の節が揃っていない"]
    if list(b.keys()) != [u"V-%d" % i for i in range(1, 12)]:
        out.append(u"封 §3 が V-1〜V-11 の 11 行でない")
        return out
    for ph in BOUND_PHRASES:
        if ph not in sec:
            out.append(u"封に予測の幅の字が無い: %s" % ph)
    if u"| 丙(133 本) | 0〜150 | 0〜150 | 400〜1,100 |" not in sec or u"| A(239 本) | 150〜700 | 150〜900 | 900〜2,000 |" not in sec:
        out.append(u"封 V-4 の表の行が無い")
    if u"| A | 0 件 | 0〜2.0% | 0〜1.5% |" not in sec or u"| 丙 | 0 件(行が 0 なら「行なし」) | 0〜2.0%(同) | 0〜2.0% |" not in sec:
        out.append(u"封 V-5 の表の行が無い")
    return out


def seal_frozen_problems(seal_text, root=REPO):
    u"""封が bcc244ae の commit のときの byte と同じか(1 字も変わっていない。未 commit の編集も見る)。"""
    rc, _ = PR.git_in(root, "cat-file", "-e", SEAL_COMMIT_SHORT + "^{commit}")
    if rc != 0:
        return [u"封の commit が履歴に無い"]
    r = subprocess.run(["git", "show", "%s:%s%s" % (SEAL_COMMIT_SHORT, PREFIX, SEAL_REL)], cwd=root, capture_output=True)
    if r.returncode != 0:
        return [u"封の commit に封の file が無い"]
    if r.stdout != seal_text.encode("utf-8"):
        return [u"封が %s のときの byte から変わっている" % SEAL_COMMIT_SHORT]
    return []


def cell_rows(c):
    u"""予測 V-1〜V-11 を小項目に分け、記録から判定した行 (id, 小項目, 幅(封), 実測, 判定) の列にする。"""
    R = c.R
    by = rows_by(c)
    ag = agg_want(c)
    cov = R[u"覆い"][u"群ごと"]
    cells = []

    def add(uid, label, bound, actual, ok):
        cells.append((uid, label, bound, actual, u"当たり" if ok else u"外れ"))
    # V-1: 下調べの 20 本(# 1〜12・251〜258)に限って数えた行
    sel = [r for r in R[u"行"] if r[u"本の #"] in PRELIM_BOOKS]
    for t in TYPE_NAMES:
        rs = [r for r in sel if r[u"型"] == t]
        cn = collections.Counter(word_of(r) for r in rs)
        got = (len(rs), cn.get(W_PASS, 0), cn.get(W_NAMED, 0), cn.get(W_OTHER, 0), cn.get(W_PNF, 0), sum(1 for r in rs if r[u"届いた"] is True))
        w = PRELIM[t]
        add(u"V-1", u"%s(注入の行・通した・名指して原本・名指したが別・PNF・届いた)" % SHORT[t], u" / ".join(str(x) for x in w), u" / ".join(str(x) for x in got), got == w)
    # V-2
    tb = R[u"土台の確かめ"]
    add(u"V-2", u"土台の確かめ(違う本 / 切れた本)", u"全部で同じ(違う本 0)", u"%d / %d" % (tb[u"違う本"], tb[u"本"]), tb[u"違う本"] == 0 and tb[u"本"] == len(cut_books(c)))
    # V-3 は 2 回目の記録が追跡されないので字で留める(pred_table の V3_ACTUAL)
    # V-4・V-5
    for (g, t), (lo, hi) in V4_BOUNDS.items():
        n = len(by[(g, t)])
        add(u"V-4", u"%s・%s の注入の行" % (g, SHORT[t]), u"%s〜%s" % (fmt(lo), fmt(hi)), fmt(n), lo <= n <= hi)
    for (g, t), hi in V5_BOUNDS.items():
        a = ag[g][t]
        n, d = a[u"通した"][u"件"], a[u"注入の行"]
        bound = u"0 件" if hi == 0.0 else u"0〜%.1f%%" % hi
        add(u"V-5", u"%s・%s の通した率" % (g, SHORT[t]), bound, u"%d 件 / %s 行 = %s" % (n, fmt(d), pct(n, d)), (n == 0) if hi == 0.0 else (100.0 * n <= hi * d))
    # V-6
    ps = [r for r in R[u"行"] if word_of(r) == W_PASS]
    notr = sum(1 for r in ps if r[u"届いた"] is not True)
    add(u"V-6", u"通した行のうち届いていない行", u"0", str(notr), notr == 0)
    for g in GROUPS:
        m = sum(ag[g][t][u"対応が付いた行"] for t in TYPE_NAMES)
        rc = sum(ag[g][t][u"届いた"][u"件"] for t in TYPE_NAMES)
        low = [t for t in TYPE_NAMES if ag[g][t][u"届いた"][u"率(分母は対応が付いた行)"] < V6_REACHED_MIN]
        add(u"V-6", u"%s の届いた率(分母は対応が付いた行。型ごとの最低も見る)" % g, u"98% 以上", u"%s / %s = %s(型ごとに 98%% 未満 %d 型)" % (fmt(rc), fmt(m), pct(rc, m), len(low)), 100.0 * rc >= V6_REACHED_MIN * m and not low)
    # V-7
    for g in GROUPS:
        for t in (TYPE_NAMES[0], TYPE_NAMES[2]):
            a = ag[g][t]
            cn = dict((w, a[u"結果の語"][w][u"件"]) for w in WORDS)
            top = max(WORDS, key=lambda w: cn[w])
            r_ = a[u"結果の語"][W_NAMED][u"率"]
            ok = top == W_NAMED and (r_ >= V7_T1_MIN if t == TYPE_NAMES[0] else V7_T8_RANGE[0] <= r_ <= V7_T8_RANGE[1])
            add(u"V-7", u"%s・%s の名指して原本の値を返した率(いちばん多い語が名指して原本)" % (g, SHORT[t]), u"80% 以上" if t == TYPE_NAMES[0] else u"60〜90%", u"%.1f%%(いちばん多い語: %s)" % (r_, top), ok)
    a = ag[GROUP_A][TYPE_NAMES[1]]
    cn = dict((w, a[u"結果の語"][w][u"件"]) for w in WORDS)
    top = max(WORDS, key=lambda w: cn[w])
    add(u"V-7", u"A・T5 のいちばん多い語", W_PNF, top, top == W_PNF)
    # V-8
    for g in GROUPS:
        x = cov[g][u"注入の行が 1 行以上の本(分母は GROUNDED が 1 行以上の本)"]
        lo, hi = V8_BOUNDS[g]
        add(u"V-8", u"%s の注入の行が 1 行以上の本 / GROUNDED が 1 行以上の本" % g, u"%d〜%d%%" % (lo, hi), u"%d / %d = %.1f%%" % (x[u"件"], cov[g][u"GROUNDED が 1 行以上の本"], x[u"率"]),
            lo <= rate(x[u"件"], cov[g][u"GROUNDED が 1 行以上の本"]) <= hi)
    # V-9: 分母の読みが 2 通り(4 型の合計・主の 3 型の合計)
    nb = [len(by[(GROUP_B, t)]) for t in TYPE_NAMES]
    t8 = len(by[(GROUP_B, TYPE_NAMES[2])])
    add(u"V-9", u"丙の注入の行のうち T8(読み 1: 分母は T1・T5・T8・T9 の合計)", u"85% 以上", u"%s / %s = %s" % (fmt(t8), fmt(sum(nb)), pct(t8, sum(nb))), 100.0 * t8 >= V9_MIN * sum(nb))
    add(u"V-9", u"丙の注入の行のうち T8(読み 2: 分母は主の T1・T5・T8 の合計)", u"85% 以上", u"%s / %s = %s" % (fmt(t8), fmt(sum(nb[:3])), pct(t8, sum(nb[:3]))), 100.0 * t8 >= V9_MIN * sum(nb[:3]))
    # V-10
    t9 = [len(by[(g, TYPE_NAMES[3])]) for g in GROUPS]
    t9p = sum(ag[g][TYPE_NAMES[3]][u"通した"][u"件"] for g in GROUPS)
    add(u"V-10", u"T9 の注入の行(A と 丙)", u"5〜80 行", u"%d" % sum(t9), V10_ROWS[0] <= sum(t9) <= V10_ROWS[1])
    add(u"V-10", u"T9 の通した行 / T9 の注入の行", u"20% 以下", u"%d / %d = %s" % (t9p, sum(t9), pct(t9p, sum(t9))), 100.0 * t9p <= V10_PASS_MAX * sum(t9))
    # V-11
    rr = sum(ag[g][t][u"round-trip 不一致"] + ag[g][t][u"読み直し不一致"] for g in GROUPS for t in TYPE_NAMES)
    add(u"V-11", u"round-trip 不一致と読み直し不一致の合計", u"10 行以下", str(rr), rr <= V11_ROWS_MAX)
    worst = max((ag[g][t][u"結果の語"][W_UNM][u"率"], g, t) for g in GROUPS for t in TYPE_NAMES)
    add(u"V-11", u"対応が付かない率の最大(群 × 型。型ごとに全群をまとめても最大はこれ以下)", u"3% 以下", u"%.1f%%(%s・%s)" % (worst[0], worst[1], SHORT[worst[2]]), worst[0] <= V11_UNMAPPED_MAX)
    return cells


COMPARED_NOTE = u"A は states_2026-11-14.json・丙は states_interim_2026-11-14.json。(文の番号, 位置, state) の並びが本ごとに同じ(違えば本の job で止まる)"
UNBOUND_MUTATIONS = (u"c 覆い・本ごと refs の数",)            # 材料(ZIP)から数えるしかない欄。門は材料を読まないので縛れない(結果の文書にも数を書かない)
V3_ACTUAL = u"2 回目の走り(1 回目は時間 804.1 秒・2 回目は 825.6 秒)で、時間の欄の 1 行だけが違い、ほかは byte で同じ。2 回目の記録は追跡していない(scratchpad の 1 本。sha256 は §0 の表)"
V3_JUDGE = u"当たり(実装の席が diff して確かめた一回限りの手の実測で、門ではない。環境変数つきの試験は 2 回目の file を渡したときだけ走る)"
PRED_LABELS = collections.OrderedDict([
    (u"V-1", u"下調べの 20 本の行の数・通した"), (u"V-2", u"土台の確かめ"), (u"V-3", u"2 回走らせた記録"), (u"V-4", u"注入の行の数(群 × 型)"), (u"V-5", u"通した率(群 × 型)"),
    (u"V-6", u"通した行の届いていない数・届いた率"), (u"V-7", u"いちばん多い結果の語"), (u"V-8", u"注入の行が 1 行以上の本"), (u"V-9", u"丙の注入の行のうち T8"),
    (u"V-10", u"T9(参考)"), (u"V-11", u"round-trip・読み直しの不一致・対応が付かない")])


def pred_table(c):
    u"""封 §3 の V-1〜V-11 を (id, 欄, 予測(封), 実測の要約, 判定) の列にする。判定は小項目が全部当たりのときだけ当たり。"""
    cells = cell_rows(c)
    seal = seal_bullets(c.seal)
    out = []
    for uid in PRED_LABELS:
        if uid == u"V-3":
            out.append((uid, PRED_LABELS[uid], seal[uid], V3_ACTUAL, V3_JUDGE))
            continue
        mine = [x for x in cells if x[0] == uid]
        bad = [x for x in mine if x[4] != u"当たり"]
        if uid == u"V-9":                                         # 読みが 2 通り。どちらも外れのときだけ外れ・食い違えば「読みが 2 通り」と書く(判定を決めない)
            verdict = u"外れ(読み 1・2 とも外れ)" if len(bad) == 2 else (u"当たり(読み 1・2 とも当たり)" if not bad else u"読みが 2 通り")
        else:
            verdict = u"外れ(小項目 %d 件中 %d 件が外れ)" % (len(mine), len(bad)) if bad else u"当たり"
        out.append((uid, PRED_LABELS[uid], seal[uid], u"小項目 %d 件(§1-2 の表)" % len(mine) if uid != u"V-1" else u"20 本・4 型の行を数えて封 §0-1 の表と照らした(§1-2 の表)", verdict))
    return out


def verdict_counts(c):
    t = pred_table(c)
    return sum(1 for r in t if r[4].startswith(u"当たり")), sum(1 for r in t if r[4].startswith(u"外れ")), sum(1 for r in t if not (r[4].startswith(u"当たり") or r[4].startswith(u"外れ")))


def verdict_counts_real(c):
    u"""本物の予測(V-2〜V-11。V-1 は下調べを写しただけの予測で、封が「手柄にしない」と言っている)の当たり・外れ。"""
    t = [r for r in pred_table(c) if r[0] != u"V-1"]
    return sum(1 for r in t if r[4].startswith(u"当たり")), sum(1 for r in t if r[4].startswith(u"外れ")), len(t)


def cell_counts(c):
    u"""小項目ごとの当たり・外れ(予測 1 本の判定は「小項目が全部当たり」なので、小項目で数えると外れの数が変わる。読みが 2 通りの所)。"""
    cs = cell_rows(c)
    return sum(1 for x in cs if x[4] == u"当たり"), sum(1 for x in cs if x[4] != u"当たり"), len(cs)


def _sep(n):
    return u"|" + u"---|" * n


def cnt_cell(n, d):
    return u"%s (%s)" % (fmt(n), pct(n, d))


def build_blocks(c):
    R, P = c.R, c.P
    by = rows_by(c)
    ag = agg_want(c)
    cov = R[u"覆い"][u"群ごと"]
    blocks = collections.OrderedDict()
    lines = [u"| # | 欄 | 予測(封) | 実測 | 判定 |", _sep(5)]
    for r in pred_table(c):
        lines.append(u"| %s | %s | %s | %s | %s |" % r)
    blocks[u"pred"] = lines
    lines = [u"| # | 小項目 | 予測の幅(封) | 実測 | 判定 |", _sep(5)]
    for r in cell_rows(c):
        lines.append(u"| %s | %s | %s | %s | %s |" % r)
    blocks[u"cells"] = lines
    n_hit, n_miss, n_two = verdict_counts(c)
    r_hit, r_miss, r_all = verdict_counts_real(c)
    c_hit, c_miss, c_all = cell_counts(c)
    blocks[u"tally"] = [u"| 数え方 | 当たり | 外れ | 読みが 2 通り | 母数 |", _sep(5),
                        u"| 予測 1 本ごと(V-1〜V-11) | %d | %d | %d | %d |" % (n_hit, n_miss, n_two, n_hit + n_miss + n_two),
                        u"| 予測 1 本ごと(本物の予測 V-2〜V-11。V-1 は下調べの写し) | %d | %d | 0 | %d |" % (r_hit, r_miss, r_all),
                        u"| 小項目ごと(§1-2 の表) | %d | %d | 0 | %d |" % (c_hit, c_miss, c_all),
                        u"", u"| 外れの # |", _sep(1)] + [u"| %s |" % r[0] for r in pred_table(c) if r[4].startswith(u"外れ")]
    # V-1 の 20 本の表
    sel = [r for r in R[u"行"] if r[u"本の #"] in PRELIM_BOOKS]
    lines = [u"| 型 | 注入の行 | 通した | 名指して原本の値を返した | 名指したが別の値 | POINTER_NOT_FOUND | UNVERIFIABLE | 対応が付かない | 届いた |", _sep(9)]
    for t in TYPE_NAMES:
        rs = [r for r in sel if r[u"型"] == t]
        cn = collections.Counter(word_of(r) for r in rs)
        lines.append(u"| %s | %d | %d | %d | %d | %d | %d | %d | %d |" % (SHORT[t], len(rs), cn.get(W_PASS, 0), cn.get(W_NAMED, 0), cn.get(W_OTHER, 0), cn.get(W_PNF, 0), cn.get(W_UNV, 0), cn.get(W_UNM, 0),
                                                                          sum(1 for r in rs if r[u"届いた"] is True)))
    lines += [u"", u"| 欄 | 値 |", _sep(2), u"| 20 本のうち注入の行が在った本 | %d |" % len(set(r[u"本の #"] for r in sel))]
    blocks[u"v1"] = lines
    w = R[u"配線"]
    tb = R[u"土台の確かめ"]
    pop = R[u"母集団"]
    mt = R[u"材料"]
    lines = [u"| 欄 | 値 |", _sep(2),
             u"| profile | %s |" % R[u"profile"],
             u"| with の中の profile の対(TS.OLD・TS.NEW) | %s・%s |" % (w[u"with の中"][u"TS.OLD"], w[u"with の中"][u"TS.NEW"]),
             u"| with の中の切り替え 2 つ(yen_scan_2026_11_05・t5_yen_2026_11_06) | %s・%s |" % (u"真" if w[u"with の中"][u"切り替え yen_scan_2026_11_05"] else u"偽", u"真" if w[u"with の中"][u"切り替え t5_yen_2026_11_06"] else u"偽"),
             u"| with の後の切り替え 2 つ | %s・%s |" % (u"真" if w[u"with の後"][u"切り替え yen_scan_2026_11_05"] else u"偽", u"真" if w[u"with の後"][u"切り替え t5_yen_2026_11_06"] else u"偽"),
             u"| with の中の届き方の問題 | %d 件 |" % len(w[u"with の中の届き方の問題"]),
             u"| with の前と後が同じ(元に戻った) | %s |" % (u"真" if w[u"元に戻った"] and w[u"with の前"] == w[u"with の後"] else u"偽"),
             u"| 種・cap | %d・%d |" % (R[u"種"], R[u"cap"]),
             u"| 対象の本(切れた本)・切れない本 | %s・%s |" % (fmt(pop[u"対象の本(切れた本)"]), fmt(pop[u"切れない本"])),
             u"| 対象の本の内訳 A・丙 | %s・%s |" % (fmt(pop[u"A"]), fmt(pop[u"丙"])),
             u"| 土台の確かめ: 本・行・違う本 | %s・%s・%s |" % (fmt(tb[u"本"]), fmt(tb[u"行"]), fmt(tb[u"違う本"])),
             u"| 材料の ZIP(表と一致)・置き場の一覧の前後で変化なし | %s・%s |" % (fmt(mt[u"表と一致した ZIP"]), u"真" if mt[u"置き場の一覧の前後"][u"変化なし"] else u"偽"),
             u"| refs で飛ばした fact の合計 | %d |" % R[u"refs の作り"][u"飛ばした fact の合計"],
             u"| key_leaks | %d 件 |" % len(R[u"key_leaks"]),
             u"| 注入の行の数 | %s |" % fmt(R[u"注入の行の数"]),
             u"| 時間(秒。1 回目・2 回目) | %s・%s |" % (R[u"時間(秒)"], RUN2_TIME)]
    blocks[u"wiring"] = lines
    lines = [u"| 名前 | sha256 |", _sep(2),
             u"| inject の記録 | %s |" % hashlib.sha256(c.texts.get(INJECT_REL, b"")).hexdigest(), u"| 札の記録 | %s |" % hashlib.sha256(c.texts.get(PASSED_REL, b"")).hexdigest(),
             u"| script | %s |" % hashlib.sha256(c.texts.get(SCRIPT_REL, b"")).hexdigest(), u"| 2 回目の走りの記録(追跡しない) | %s |" % RUN2_SHA,
             u"| HEAD の commit(記録の字) | %s |" % R[u"HEAD の commit"], u"| 封の commit | %s |" % R[u"封の commit"]]
    blocks[u"prov"] = lines
    lines = [u"| 群 | 型 | 注入の行 | 通した | 名指して原本の値を返した | 名指したが別の値 | POINTER_NOT_FOUND | UNVERIFIABLE | 対応が付かない | 対応が付いた行 | 届いた | 通したうち届いていない | round-trip 不一致 | 読み直し不一致 |", _sep(14)]
    for g in GROUPS:
        for t in TYPE_NAMES:
            a = ag[g][t]
            n = a[u"注入の行"]
            cells = [cnt_cell(a[u"結果の語"][wd][u"件"], n) for wd in WORDS]
            lines.append(u"| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                g, SHORT[t] + (u"(参考)" if t == TYPE_NAMES[3] else u""), fmt(n), cells[0], cells[1], cells[2], cells[3], cells[4], cells[5],
                fmt(a[u"対応が付いた行"]), cnt_cell(a[u"届いた"][u"件"], a[u"対応が付いた行"]), fmt(a[u"通した"][u"うち届いていない"]), fmt(a[u"round-trip 不一致"]), fmt(a[u"読み直し不一致"])))
    blocks[u"main"] = lines
    lines = [u"| 欄 | A | 丙 |", _sep(3)]
    a_, b_ = cov[GROUP_A], cov[GROUP_B]

    def two(label, f):
        lines.append(u"| %s | %s | %s |" % (label, f(a_), f(b_)))
    two(u"切れた本", lambda g: fmt(g[u"切れた本"]))
    two(u"P33E が GROUNDED の行の合計", lambda g: fmt(g[u"P33E が GROUNDED の行の合計"]))
    two(u"円族の token の合計", lambda g: fmt(g[u"円族の token の合計"]))
    two(u"GROUNDED が 1 行以上の本", lambda g: fmt(g[u"GROUNDED が 1 行以上の本"]))
    two(u"注入の行が 1 行以上の本", lambda g: fmt(g[u"注入の行が 1 行以上の本"]))
    two(u"注入の行が 1 行以上の本 / GROUNDED が 1 行以上の本", lambda g: u"%s / %s = %.1f%%" % (fmt(g[u"注入の行が 1 行以上の本"]), fmt(g[u"GROUNDED が 1 行以上の本"]), g[u"注入の行が 1 行以上の本(分母は GROUNDED が 1 行以上の本)"][u"率"]))
    two(u"全角の数字で注入しない本", lambda g: fmt(g[u"全角の数字で注入しない本"]))
    two(u"refs で飛ばした fact の合計", lambda g: fmt(g[u"refs で飛ばした fact の合計"]))
    for t in TYPE_NAMES:
        s = SHORT[t]
        two(u"%s 作れる site の合計" % s, lambda g, s=s: fmt(g[u"作れる site の合計"][s]))
        two(u"%s 注入の行の合計" % s, lambda g, s=s: fmt(g[u"注入の行の合計"][s]))
        two(u"%s 注入の行が 1 行以上の本" % s, lambda g, s=s: fmt(g[u"型ごとに注入の行が 1 行以上の本"][s]))
        two(u"%s 作れる site が 0 の本" % s, lambda g, s=s: fmt(g[u"作れる site が 0 の本"][s]))
    blocks[u"cover"] = lines
    ps = [r for r in R[u"行"] if word_of(r) == W_PASS]
    lines = [u"| 番号 | 本の # | 群 | 型 | 札 |", _sep(5)]
    for r, q in zip(P[u"行"], ps):
        lines.append(u"| %d | %d | %s | %s | %s |" % (r[0], r[1], q[u"群"], SHORT[r[3]], r[4]))
    lines += [u"", u"| 札 | a | b | c | d |", _sep(5), u"| 行 | %s |" % u" | ".join(str(P[u"札の集計"][k]) for k in (u"a", u"b", u"c", u"d")),
              u"", u"| 群 | 型 | 通した行 | その本の数 |", _sep(4)]
    for g in GROUPS:
        for t in TYPE_NAMES:
            q = [r for r in ps if grp_of(r) == g and r[u"型"] == t]
            lines.append(u"| %s | %s | %d | %d |" % (g, SHORT[t], len(q), len(set(r[u"本の #"] for r in q))))
    blocks[u"passed"] = lines
    blocks[u"limits"] = [u"%d. %s" % (i + 1, s) for i, s in enumerate(R[u"限界"])]
    blocks[u"note"] = [R[u"欄名の注記"]]
    return blocks


def doc_blocks(doc):
    return collections.OrderedDict((m.group(1), m.group(2).split(u"\n")) for m in re.finditer(r"<!-- 門:start (\w+) -->\n(.*?)\n<!-- 門:end -->", doc, re.S))


def outside_blocks(doc):
    return re.sub(r"<!-- 門:start \w+ -->\n.*?\n<!-- 門:end -->", u"", doc, flags=re.S)


NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")


def numbers_of(text, min_digits=2):
    out = set()
    for m in NUM_RE.findall(text):
        s = m.rstrip(u",").replace(u",", u"")
        if len(s.split(u".")[0]) >= min_digits:
            out.add(s)
    return out


def prose_clean(line):
    t = re.sub(r"`[^`]*`", u"", line)
    t = re.sub(r"\d{4}-\d{2}-\d{2}", u"", t)
    t = re.sub(r"\b[0-9a-f]{7,}\b", u"", t)
    t = re.sub(r"https?://\S+|\S+\.(?:md|py|json)\b", u"", t)
    t = re.sub(r"\b[A-Z]+-?\d+[A-Z]*\b", u"", t)                      # V-10・P33E・B314 などの名前
    t = re.sub(u"§[0-9\\-]+", u"", t)
    return t


def derived_numbers(c):
    u"""塊に出ない、記録から作れる数(本の総数 400・A の本 250・丙の本 150 など)。"""
    pop = c.R[u"母集団"]
    allb = len(c.S[u"本"])
    nA = sum(1 for b in c.S[u"本"] if b[u"#"] <= 250)
    return set(str(x) for x in (allb, nA, allb - nA, pop[u"対象の本(切れた本)"], len(c.P[u"行"])))


def prose_number_problems(doc, blocks, c):
    u"""塊の外の散文の 2 桁以上の数は、記録から作った塊の中の数か、記録から作った数の集合に在る。"""
    allowed = set()
    for lines in blocks.values():
        allowed |= numbers_of(u"\n".join(lines))
    allowed |= derived_numbers(c)
    out = []
    for ln, line in enumerate(outside_blocks(doc).splitlines(), 1):
        bad = sorted(numbers_of(prose_clean(line)) - allowed)
        if bad:
            out.append(u"散文の数が記録から作った数の集合に無い: 行 %d %s" % (ln, u",".join(bad)))
        if KANJI_NUM_RE.search(line):
            out.append(u"散文が 3 桁以上の数を漢数字で書いている: 行 %d" % ln)
    return out


REQUIRED_PHRASES = (u"人は読んでいない", u"盲検ではない", u"AI の席", u"人間の決定", u"読んでいない", u"測っていない", u"採る・採らないの判定は無い", u"読みが 2 通り", u"封に無い決め",
                    u"名指した", u"期の名前", u"外れは外れ", u"負け")


def doc_problems(c):
    doc = c.doc
    out = []
    names = re.findall(r"<!-- 門:start (\w+) -->", doc)
    if names != list(BLOCK_NAMES) or doc.count(u"<!-- 門:end -->") != len(BLOCK_NAMES):
        out.append(u"文書: 塊の名前・数が %d 個(%s)の順でない" % (len(BLOCK_NAMES), u"・".join(BLOCK_NAMES)))
    want = build_blocks(c)
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
    if DOCID_RE.search(doc) or TDNET_RE.search(doc):
        out.append(u"文書: docID・TDnet の番号の形の字がある")
    for w in FORBIDDEN_WORDS:
        if w in doc:
            out.append(u"文書: 禁止語 %s" % w)
    stripped = doc
    for s in c.R.get(u"限界", []):                                 # 限界の字(記録と同じ)の中の「人の目の札は無い」(否定の用例)だけを除いて、「人の目」を探す
        if LIMIT_QUOTE_NEEDLE in s:
            stripped = stripped.replace(s, u"")
    if u"人の目" in stripped:
        out.append(u"文書: 「人の目」が否定の用例(限界の字)の外にある")
    for w in COMPANY_WORDS:
        if w in doc:
            out.append(u"文書: 会社名らしい字 %s" % w)
    if POINTER_RE.search(doc):
        out.append(u"文書: pointer・要素名の形の字がある")
    out += prose_number_problems(doc, want, c)
    for need in (os.path.basename(SEAL_REL), SEAL_COMMIT_SHORT, SCRIPT_COMMIT, os.path.basename(GATE_REL), os.path.basename(SCRIPT_REL)) + tuple(os.path.basename(r) for r in RECORD_RELS) + REQUIRED_PHRASES:
        if need not in doc:
            out.append(u"文書: %s を言っていない" % need)
    for sec in (u"## §0", u"## §1", u"## §2", u"## §3", u"## §4", u"## §5"):
        if sec not in doc:
            out.append(u"文書: 節 %s が無い" % sec)
    return out


# ======================================================================================================
# g. 順序・engine
def order_others():
    return list(RECORD_RELS) + [DOC_REL, GATE_REL]


def order_problems_real(root=REPO):
    return PR.order_problems(root, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, [SCRIPT_REL], order_others())


def engine_problems(root=REPO):
    u"""engine・lib・仕掛け・前の便は封の commit から 0 行。script は足した commit(ac10c814)から 0 行(未 commit の編集も見る)。"""
    out = list(SG.untouched_problems(root))
    rc, txt = PR.git_in(root, "diff", "--numstat", SCRIPT_COMMIT, "--", PREFIX + SCRIPT_REL)
    if rc != 0:
        out.append(u"engine: git diff が失敗した")
    elif txt:
        out.append(u"engine: script が %s から変わっている" % SCRIPT_COMMIT)
    return out


# ======================================================================================================
# 変異の表(ここの表の 1 行 = 1 つの検査を赤にする 1 か所の変異。木の file は変異させず、Ctx の写しを変える)
CHECKS = collections.OrderedDict([
    (u"sha", lambda c: sha_problems(c.texts)),
    (u"prov", provenance_problems),
    (u"rows", rows_problems),
    (u"agg", agg_problems),
    (u"cover", coverage_problems),
    (u"base", base_problems),
    (u"passed", passed_problems),
    (u"clean", clean_problems),
    (u"doc", doc_problems),
    (u"seal", lambda c: seal_problems(c.seal)),
    (u"frozen", lambda c: seal_frozen_problems(c.seal)),
])

MUTATIONS = []


def M(label, check, fn):
    MUTATIONS.append((label, check, fn))


def flip(s):
    return (u"0" if s[0] != u"0" else u"1") + s[1:]


def leaf_paths(x, path=()):
    u"""dict・list を歩いて、数・文字・真偽の葉までの path(key・index の並び)を返す。"""
    if isinstance(x, dict):
        for k, v in x.items():
            for p in leaf_paths(v, path + (k,)):
                yield p
    elif isinstance(x, list):
        for i, v in enumerate(x):
            for p in leaf_paths(v, path + (i,)):
                yield p
    elif x is not None:
        yield path


def at(obj, path):
    for k in path:
        obj = obj[k]
    return obj


def mutate_leaf(obj, path):
    parent, key = at(obj, path[:-1]), path[-1]
    v = parent[key]
    if isinstance(v, bool):
        parent[key] = not v
    elif isinstance(v, int):
        parent[key] = v + 1
    elif isinstance(v, float):
        parent[key] = v + 1.0
    elif isinstance(v, str):
        parent[key] = flip(v) if (HEX64.match(v) or HEX40.match(v)) else v + u"x"
    else:
        raise AssertionError(path)


def path_label(path):
    return u"/".join(str(p) for p in path)


def _doc_digit(c, name, i):
    lines = doc_blocks(c.doc)[name]
    ln = lines[i]
    m = re.search(r"\d", ln)
    idx = c.doc.index(u"\n".join(lines))
    off = idx + len(u"\n".join(lines[:i])) + (1 if i else 0) + m.start()
    ch = c.doc[off]
    c.doc = c.doc[:off] + (u"7" if ch != u"7" else u"8") + c.doc[off + 1:]


# a. sha
M(u"a1 inject の記録の 1 byte", u"sha", lambda c: c.texts.__setitem__(INJECT_REL, c.texts[INJECT_REL] + b" "))
M(u"a2 札の記録の 1 byte", u"sha", lambda c: c.texts.__setitem__(PASSED_REL, c.texts[PASSED_REL][:-2] + b" \n"))
M(u"a3 script の 1 byte", u"sha", lambda c: c.texts.__setitem__(SCRIPT_REL, c.texts[SCRIPT_REL] + b"#"))
M(u"a4 inject の記録の先頭に 1 byte", u"sha", lambda c: c.texts.__setitem__(INJECT_REL, b"x" + c.texts[INJECT_REL]))
# b. 来歴: header の葉を 1 つずつ(行・集計・覆い・本ごと・型・refs・限界以外)
for _top in (u"seal", u"封の commit", u"step", u"HEAD の commit", u"この script の sha256", u"第 2 便の script の sha256", u"TSS の script の sha256", u"置く script の sha256",
             u"2026-11-09 の便の script の sha256", u"仕掛けの 2 file の sha256", u"lib の指紋", u"engine の指紋", u"母集団の記録の sha256", u"TSS の判定の記録の sha256",
             u"interim の記録の sha256", u"profile", u"材料", u"配線", u"切り替え", u"種", u"cap", u"欄名の注記", u"時間(秒)"):
    _c0 = Ctx.__new__(Ctx)
    _c0.R = json.loads(cached_text(INJECT_REL))
    for _p in leaf_paths(_c0.R[_top], (_top,)):
        M(u"b 来歴 %s" % path_label(_p), u"prov", (lambda p: (lambda c: mutate_leaf(c.R, p)))(_p))
for _k in (u"seal", u"封の commit", u"step", u"HEAD の commit", u"この script の sha256", u"inject の記録の sha256", u"札を付けた席", u"盲検"):
    M(u"b 札の来歴 %s" % _k, u"prov", (lambda k: (lambda c: mutate_leaf(c.P, (k,))))(_k))
M(u"b 札の字を 1 つ変える", u"prov", lambda c: c.P[u"札の字"].__setitem__(u"a", u"通した"))
M(u"b 札の行の欄", u"prov", lambda c: c.P[u"行の欄"].pop())
M(u"b inject の行の欄", u"prov", lambda c: c.R[u"行の欄"].pop())
M(u"b 限界の 1 本を消す", u"prov", lambda c: c.R[u"限界"].pop())
M(u"b 限界の字を 1 つ変える", u"prov", lambda c: c.R[u"限界"].__setitem__(4, c.R[u"限界"][4] + u"。"))
M(u"b 欄が 1 つ増える(inject)", u"prov", lambda c: c.R.__setitem__(u"余分", 1))
M(u"b 欄が 1 つ増える(札)", u"prov", lambda c: c.P.__setitem__(u"余分", 1))
M(u"b 今の script が変わった(実 file 側)", u"prov", lambda c: c.cur.__setitem__("script", flip(c.cur["script"])))
M(u"b 今の TSS の判定の記録が変わった(実 file 側)", u"prov", lambda c: c.cur.__setitem__("states", flip(c.cur["states"])))
M(u"b 今の interim の記録が変わった(実 file 側)", u"prov", lambda c: c.cur.__setitem__("interim", flip(c.cur["interim"])))
M(u"b 今の population の記録が変わった(実 file 側)", u"prov", lambda c: c.cur.__setitem__("pop", flip(c.cur["pop"])))
M(u"b 今の sites.py が変わった(実 file 側)", u"prov", lambda c: c.cur.__setitem__("sites", flip(c.cur["sites"])))
M(u"b 今の inject.py が変わった(実 file 側)", u"prov", lambda c: c.cur.__setitem__("injectpy", flip(c.cur["injectpy"])))
M(u"b 今の lib/numbers.py が変わった(実 file 側)", u"prov", lambda c: c.cur.__setitem__("numbers", flip(c.cur["numbers"])))
M(u"b 今の lib/scales.py が変わった(実 file 側)", u"prov", lambda c: c.cur.__setitem__("scales", flip(c.cur["scales"])))
M(u"b 今の TSS の script が変わった(実 file 側)", u"prov", lambda c: c.cur.__setitem__("tss", flip(c.cur["tss"])))
M(u"b 今の第 2 便の script が変わった(実 file 側)", u"prov", lambda c: c.cur.__setitem__("s2", flip(c.cur["s2"])))
M(u"b 今の 2026-11-09 の script が変わった(実 file 側)", u"prov", lambda c: c.cur.__setitem__("prev", flip(c.cur["prev"])))
M(u"b 今の engine が違う(実側)", u"prov", lambda c: c.cur["fp"].__setitem__(u"core_py_sha256", flip(c.cur["fp"][u"core_py_sha256"])))
M(u"b HEAD の commit が祖先でない 40 桁", u"prov", lambda c: c.R.__setitem__(u"HEAD の commit", u"0" * 40))
M(u"b 札の HEAD の commit が祖先でない 40 桁", u"prov", lambda c: c.P.__setitem__(u"HEAD の commit", u"0" * 40))
# c. 行
M(u"c 行を 1 つ消す(注入の行の数と合わない)", u"rows", lambda c: c.R[u"行"].pop(100))
M(u"c 行を 1 つ増やす(同じ id)", u"rows", lambda c: c.R[u"行"].insert(1, dict(c.R[u"行"][0])))
M(u"c 行の群を変える", u"rows", lambda c: c.R[u"行"][0].__setitem__(u"群", u"乙"))
M(u"c 行の型を変える", u"rows", lambda c: c.R[u"行"][0].__setitem__(u"型", "T1_VALUE"))
M(u"c 行の id の本の #", u"rows", lambda c: c.R[u"行"][0].__setitem__(u"id", u"B2-T8-01"))
M(u"c 行の id の形", u"rows", lambda c: c.R[u"行"][0].__setitem__(u"id", u"x"))
M(u"c 行の本の # が切れた本でない", u"rows", lambda c: c.R[u"行"][0].__setitem__(u"本の #", 2))
M(u"c 行の並び(本の # が戻る)", u"rows", lambda c: c.R[u"行"].__setitem__(slice(0, 2), [c.R[u"行"][-1], c.R[u"行"][0]]))
M(u"c 結果の語と state が合わない", u"rows", lambda c: c.R[u"行"][0][u"P33E"].__setitem__(u"state", u"GROUNDED"))
M(u"c 結果の語が封の語でない", u"rows", lambda c: c.R[u"行"][0][u"P33E"].__setitem__(u"結果", u"通した "))
M(u"c 対応が付かない語なのに対応 真", u"rows", lambda c: [r for r in c.R[u"行"] if word_of(r) == W_UNM][0][u"P33E"].__setitem__(u"対応", True))
M(u"c 対応が付いたのに届いた 偽", u"rows", lambda c: c.R[u"行"][0].__setitem__(u"届いた", False))
M(u"c 届いたが真偽でない", u"rows", lambda c: c.R[u"行"][0].__setitem__(u"届いた", u"True"))
M(u"c 必要な欄が無い", u"rows", lambda c: c.R[u"行"][0].pop(u"id"))
M(u"c 行の欄が封の外", u"rows", lambda c: c.R[u"行"][0].__setitem__(u"文", u"x"))
M(u"c 注入の行の数", u"rows", lambda c: c.R.__setitem__(u"注入の行の数", c.R[u"注入の行の数"] + 1))
# 行の中身の変異(集計が行から数え直した値と違う)
M(u"c 行の結果を 1 つ変える(通した → 名指して原本)", u"agg", lambda c: [r for r in c.R[u"行"] if word_of(r) == W_PASS][0][u"P33E"].update({u"結果": W_NAMED, u"state": u"VALUE_MISMATCH"}))
M(u"c 行の結果を 1 つ変える(PNF → 通した)", u"agg", lambda c: [r for r in c.R[u"行"] if word_of(r) == W_PNF][0][u"P33E"].update({u"結果": W_PASS, u"state": u"GROUNDED"}))
M(u"c 行の round-trip を偽に", u"agg", lambda c: c.R[u"行"][5].__setitem__(u"round-trip", False))
M(u"c 行の読み直しを偽に", u"agg", lambda c: c.R[u"行"][5].__setitem__(u"読み直し", False))
M(u"c 通した行の届いたを偽に", u"agg", lambda c: [r for r in c.R[u"行"] if word_of(r) == W_PASS][0].__setitem__(u"届いた", False))
M(u"c 行の群を A から丙に(集計が動く)", u"agg", lambda c: [r for r in c.R[u"行"] if r[u"群"] == u"乙"][0].__setitem__(u"群", u"丙"))
M(u"c 行を 1 つ消す(集計が動く)", u"agg", lambda c: c.R[u"行"].pop(200))
# 集計の葉を 1 つずつ(群 × 型 × 欄)
_c1 = json.loads(cached_text(INJECT_REL))
for _p in leaf_paths(_c1[u"集計"], (u"集計",)):
    M(u"c 集計 %s" % path_label(_p), u"agg", (lambda p: (lambda c: mutate_leaf(c.R, p)))(_p))
# 覆いの葉を 1 つずつ(群ごと)・本ごとの欄ごと
for _p in leaf_paths(_c1[u"覆い"][u"群ごと"], (u"覆い", u"群ごと")):
    M(u"c 覆い %s" % path_label(_p), u"cover", (lambda p: (lambda c: mutate_leaf(c.R, p)))(_p))
for _k in _c1[u"覆い"][u"本ごと"][0]:
    _path = (u"覆い", u"本ごと", 7, _k)
    if isinstance(_c1[u"覆い"][u"本ごと"][7][_k], dict):
        for _p in leaf_paths(_c1[u"覆い"][u"本ごと"][7][_k], _path):
            M(u"c 覆い・本ごと %s" % path_label(_p[3:]), u"cover", (lambda p: (lambda c: mutate_leaf(c.R, p)))(_p))
    else:
        M(u"c 覆い・本ごと %s" % _k, u"cover", (lambda p: (lambda c: mutate_leaf(c.R, p)))(_path))
M(u"c 覆い・本ごとを 1 本消す", u"cover", lambda c: c.R[u"覆い"][u"本ごと"].pop(3))
M(u"c 覆い・群ごとの欄の順", u"cover", lambda c: c.R[u"覆い"][u"群ごと"].__setitem__(u"A", dict(reversed(list(c.R[u"覆い"][u"群ごと"][u"A"].items())))))
M(u"c 本ごとの数え・T8 の採った", u"cover", lambda c: c.R[u"本ごとの数え"][u"B7"][u"T8_REL"].__setitem__(u"採った", 9))
M(u"c 本ごとの数え・T5 の採った", u"cover", lambda c: c.R[u"本ごとの数え"][u"B7"][u"T5_COINCIDENT"].__setitem__(u"採った", 9))
M(u"c 本ごとの数え・T9 の採った", u"cover", lambda c: c.R[u"本ごとの数え"][u"B7"][u"T9_PRIOR_TO_CURRENT"].__setitem__(u"採った", 1))
M(u"c 本ごとの数え・T1 の採った(行より少ない)", u"cover", lambda c: c.R[u"本ごとの数え"][u"B7"][u"T1_VALUE"].__setitem__(u"採った", 1))
M(u"c 本ごとの数え・本が 1 つ消える", u"cover", lambda c: c.R[u"本ごとの数え"].pop(u"B7"))
# 土台・母集団
for _top in (u"母集団", u"土台の確かめ"):
    for _p in leaf_paths(_c1[_top], (_top,)):
        M(u"c %s" % path_label(_p), u"base", (lambda p: (lambda c: mutate_leaf(c.R, p)))(_p))
M(u"c refs で飛ばした fact(欄)", u"base", lambda c: c.R[u"refs の作り"].__setitem__(u"飛ばした fact の合計", 1))
M(u"c refs で飛ばした fact(本ごと)", u"base", lambda c: c.R[u"覆い"][u"本ごと"][0].__setitem__(u"refs で飛ばした fact", 1))
def _own_s(c):
    c.S = copy.deepcopy(c.S)


def _own_i(c):
    c.I = copy.deepcopy(c.I)


M(u"c 第 1 便の記録の行が違う(土台の行の数)", u"base", lambda c: (_own_s(c), c.S[u"本"][0][u"行"].pop()))
M(u"c 第 2 便の記録の切り出しが違う(母集団)", u"base", lambda c: (_own_i(c), [b for b in c.I[u"本"] if b[u"切り出し"] == u"切れた"][0].__setitem__(u"切り出し", u"切れない")))
M(u"c 第 1 便の記録の GROUNDED が 1 行増える(覆いの GROUNDED の行)", u"cover", lambda c: (_own_s(c), [r for b in c.S[u"本"] if b[u"#"] <= 250 and b[u"切り出し"] == u"切れた" for r in b[u"行"] if r[2] != u"GROUNDED"][0].__setitem__(2, u"GROUNDED")))
# d. 札
M(u"d 札を 1 つ変える(a → b)", u"passed", lambda c: c.P[u"行"][0].__setitem__(4, u"b"))
M(u"d 札の集計(a)", u"passed", lambda c: c.P[u"札の集計"].__setitem__(u"a", 9))
M(u"d 札の集計(b)", u"passed", lambda c: c.P[u"札の集計"].__setitem__(u"b", 1))
M(u"d 札の集計(c)", u"passed", lambda c: c.P[u"札の集計"].__setitem__(u"c", 1))
M(u"d 札の集計(d)", u"passed", lambda c: c.P[u"札の集計"].__setitem__(u"d", 1))
M(u"d 札の字でない札", u"passed", lambda c: c.P[u"行"][0].__setitem__(4, u"e"))
M(u"d 行の id", u"passed", lambda c: c.P[u"行"][2].__setitem__(2, u"B126-T5-03"))
M(u"d 行の型", u"passed", lambda c: c.P[u"行"][2].__setitem__(3, "T1_VALUE"))
M(u"d 行の本の #", u"passed", lambda c: c.P[u"行"][4].__setitem__(1, 245))
M(u"d 行を 1 つ消す", u"passed", lambda c: c.P[u"行"].pop())
M(u"d 行を 1 つ足す", u"passed", lambda c: c.P[u"行"].append([11, 314, u"B314-T9-11", "T9_PRIOR_TO_CURRENT", u"a"]))
M(u"d 番号", u"passed", lambda c: c.P[u"行"][3].__setitem__(0, 9))
M(u"d 2 行の入れ替え", u"passed", lambda c: c.P[u"行"].__setitem__(slice(0, 2), [c.P[u"行"][1], c.P[u"行"][0]]))
M(u"d 読む行の規則の通した行の数", u"passed", lambda c: c.P[u"読む行の規則"].__setitem__(u"通した行の数", 11))
M(u"d 注入の記録の通した行が 1 つ増える", u"passed", lambda c: [r for r in c.R[u"行"] if word_of(r) == W_PNF][0][u"P33E"].update({u"結果": W_PASS, u"state": u"GROUNDED"}))
M(u"d 札の key_leaks", u"passed", lambda c: c.P.__setitem__(u"key_leaks", [u"x"]))
# e. clean
M(u"e key_leaks に 1 つ(inject)", u"clean", lambda c: c.R.__setitem__(u"key_leaks", [u"x"]))
M(u"e 値の欄 value を持つ", u"clean", lambda c: c.R.__setitem__(u"value", 1))
M(u"e 行に文字の葉(文)", u"clean", lambda c: c.R[u"行"][0].__setitem__(u"形", u"売上高は1,234百万円となりました。営業利益も増加しました。通期の見通しは据え置きます。これは文です"))
M(u"e 行の欄に会社名らしい字", u"clean", lambda c: c.R[u"行"][0].__setitem__(u"単位", u"㈱x"))
M(u"e 行の葉が長い日本語の文", u"clean", lambda c: c.R[u"行"][0][u"P33E"].__setitem__(u"reason", u"当社の売上高は前期に比べて増加し、営業利益も増加しました。通期の見通しは据え置きます。これは文です"))
M(u"e 集計に pointer の字", u"clean", lambda c: c.R[u"集計"].__setitem__(u"メモ", u"jppfs_cor:NetSales"))
M(u"e 行に証券コードの形の字", u"clean", lambda c: c.R[u"行"][0].__setitem__(u"形", u"1234"))
M(u"e 行に docID の形の字", u"clean", lambda c: c.R[u"行"][0].__setitem__(u"形", u"S" + u"100ABCD"))
M(u"e 札の key_leaks", u"clean", lambda c: c.P.__setitem__(u"key_leaks", [1]))
M(u"e 札に値の欄", u"clean", lambda c: c.P.__setitem__(u"span", u"x"))
M(u"e 行の群が長い字", u"clean", lambda c: c.R[u"行"][0].__setitem__(u"群", u"x" * 30))
M(u"e 札の行に長い日本語", u"clean", lambda c: c.P[u"行"].append([u"当社の売上高は前期に比べて増加し、営業利益も増加しました。通期の見通しは据え置きます。これは文です"]))
M(u"e 本ごとの数えに TDnet の番号の形", u"clean", lambda c: c.R[u"本ごとの数え"][u"B7"].__setitem__(u"メモ", u"0812" + u"2" * 14))
# f. 文書: 塊の行ごとに 1 字(表の行ごと)
_doc0 = cached_text(DOC_REL) if os.path.exists(os.path.join(ROOT, DOC_REL)) else u""
for _name, _lines in doc_blocks(_doc0).items():
    for _i, _ln in enumerate(_lines):
        if _i >= 2 and re.search(r"\d", _ln):
            M(u"f 塊 %s の行 %d の数字 1 つ" % (_name, _i + 1), u"doc", (lambda n, i: (lambda c: _doc_digit(c, n, i)))(_name, _i))
M(u"f 塊を 1 つ消す", u"doc", lambda c: setattr(c, "doc", c.doc.replace(u"<!-- 門:start passed -->", u"<!-- 門:start passedx -->")))
M(u"f 知らない塊", u"doc", lambda c: setattr(c, "doc", c.doc + u"\n<!-- 門:start zz -->\n|a|\n<!-- 門:end -->\n"))
M(u"f 散文に記録に無い数", u"doc", lambda c: setattr(c, "doc", c.doc + u"\n散文の数 98765 件。\n"))
M(u"f 漢数字で逃がす", u"doc", lambda c: setattr(c, "doc", c.doc + u"\n三百七十二本。\n"))
M(u"f 禁止語(証明した)", u"doc", lambda c: setattr(c, "doc", c.doc + u"\n証明した。\n"))
M(u"f 禁止語(ハルシネーション)", u"doc", lambda c: setattr(c, "doc", c.doc + u"\nハルシネーション。\n"))
M(u"f 「人の目」の肯定形", u"doc", lambda c: setattr(c, "doc", c.doc + u"\n人の目で読んだ。\n"))
M(u"f docID の形", u"doc", lambda c: setattr(c, "doc", c.doc + u"\nS" + u"100ABCD\n"))
M(u"f 会社名らしい字", u"doc", lambda c: setattr(c, "doc", c.doc + u"\n株式会社\n"))
M(u"f pointer の字", u"doc", lambda c: setattr(c, "doc", c.doc + u"\njppfs_cor:NetSales\n"))
for _ph in REQUIRED_PHRASES:
    M(u"f 必要な語(%s)を消す" % _ph, u"doc", (lambda ph: (lambda c: setattr(c, "doc", c.doc.replace(ph, u"〓"))))(_ph))
M(u"f 封の commit を言わない", u"doc", lambda c: setattr(c, "doc", c.doc.replace(SEAL_COMMIT_SHORT, u"")))
M(u"f script の commit を言わない", u"doc", lambda c: setattr(c, "doc", c.doc.replace(SCRIPT_COMMIT, u"")))
M(u"f 記録の file 名を言わない", u"doc", lambda c: setattr(c, "doc", c.doc.replace(u"inject_passed_types_2026-11-14.json", u"")))
M(u"f 節 §3 が無い", u"doc", lambda c: setattr(c, "doc", c.doc.replace(u"## §3", u"## 3")))
M(u"f 記録の側を 1 つ変えると塊が違う(A・T8 の通した)", u"doc", lambda c: [r for r in c.R[u"行"] if word_of(r) == W_PASS and r[u"型"] == "T8_REL"][0][u"P33E"].update({u"結果": W_NAMED, u"state": u"VALUE_MISMATCH"}))
M(u"f 記録の側を 1 つ変えると判定が変わる(丙・T1 の注入の行を 1 つ消す)", u"doc", lambda c: c.R[u"行"].pop(len(c.R[u"行"]) - 1000))
M(u"f 札の側を 1 つ変えると塊が違う", u"doc", lambda c: c.P[u"行"][1].__setitem__(4, u"d"))
M(u"f 限界の字(記録側)を変える", u"doc", lambda c: c.R[u"限界"].__setitem__(0, c.R[u"限界"][0] + u"。"))
M(u"f 欄名の注記(記録側)を変える", u"doc", lambda c: c.R.__setitem__(u"欄名の注記", c.R[u"欄名の注記"] + u"。"))
M(u"f 封の予測の字を変える(V-3 の本文。予測の塊が違う)", u"doc", lambda c: setattr(c, "seal", c.seal.replace(u"時間の欄を除き byte で同じ", u"時間の欄を除き byte で違う")))
M(u"f 封の予測の字を変える(V-9 の本文。予測の塊が違う)", u"doc", lambda c: setattr(c, "seal", c.seal.replace(u"T8 が 85% 以上", u"T8 が 86% 以上")))
M(u"g 封の V-3 の行が消える", u"seal", lambda c: setattr(c, "seal", c.seal.replace(u"- **V-3**", u"- **V-X**")))
# g. 封
M(u"g 封の字を 1 字(V-4 の幅)", u"seal", lambda c: setattr(c, "seal", c.seal.replace(u"150〜700", u"150〜701")))
M(u"g 封の V-5 の幅", u"seal", lambda c: setattr(c, "seal", c.seal.replace(u"0〜1.5%", u"0〜1.6%")))
M(u"g 封の V-9 の幅", u"seal", lambda c: setattr(c, "seal", c.seal.replace(u"85% 以上", u"86% 以上")))
M(u"g 封の V-10 の幅", u"seal", lambda c: setattr(c, "seal", c.seal.replace(u"5〜80 行", u"5〜81 行")))
M(u"g 封の V-11 の幅", u"seal", lambda c: setattr(c, "seal", c.seal.replace(u"10 行以下", u"11 行以下")))
M(u"g 封の V-8 の幅", u"seal", lambda c: setattr(c, "seal", c.seal.replace(u"60〜88%", u"60〜89%")))
M(u"g 封の V-6 の幅", u"seal", lambda c: setattr(c, "seal", c.seal.replace(u"98% 以上", u"97% 以上")))
M(u"g 封の V-11 が消える", u"seal", lambda c: setattr(c, "seal", c.seal.replace(u"- **V-11**", u"- **V-X**")))
M(u"g 封の V-4 の表の行", u"seal", lambda c: setattr(c, "seal", c.seal.replace(u"| 丙(133 本) | 0〜150 | 0〜150 | 400〜1,100 |", u"| 丙(133 本) | 0〜150 | 0〜151 | 400〜1,100 |")))
M(u"g 封の V-5 の表の行", u"seal", lambda c: setattr(c, "seal", c.seal.replace(u"| A | 0 件 | 0〜2.0% | 0〜1.5% |", u"| A | 1 件 | 0〜2.0% | 0〜1.5% |")))
M(u"g 封が commit のときと 1 字違う", u"frozen", lambda c: setattr(c, "seal", c.seal + u"。"))
M(u"g 封の文の途中の 1 字", u"frozen", lambda c: setattr(c, "seal", c.seal.replace(u"外れうる形で", u"外れうる型で", 1)))
M(u"g 限界(封 §6)の字が記録と違う", u"prov", lambda c: setattr(c, "seal", c.seal.replace(u"上場会社全体の率ではない。", u"上場会社全体の率ではない!", 1)))


def check_problems(check, c):
    return guard(CHECKS[check], c)


# ======================================================================================================
# 試験
class RealRecordsTest(unittest.TestCase):
    def test_a_1_the_two_records_and_the_script_equal_the_pinned_sha256(self):
        self.assertEqual([], sha_problems(Ctx().texts))

    def test_a_2_the_pinned_sha256_are_the_ones_the_brief_names(self):
        self.assertEqual(["ea9a2e22932f0c5f4c8158291b0fa224c47709b07bb1fd4f61b3a64e8148b742", "6387b09d9e51f20da9e7fd8d2cf36ba5d006b7f72d93da3d56f2fe1bdb8aa01b",
                          "ad33fef1537cfb7a0d866dfe38576abe0528b441f50512e03ad72232a7cc2c9a"], list(SHA_PIN.values()))
        self.assertEqual([INJECT_REL, PASSED_REL, SCRIPT_REL], list(SHA_PIN.keys()))

    def test_b_1_the_provenance_fields_equal_the_real_files(self):
        self.assertEqual([], provenance_problems(Ctx()))

    def test_c_1_every_row_is_whole(self):
        self.assertEqual([], rows_problems(Ctx()))

    def test_c_2_the_aggregates_are_recounted_from_the_rows(self):
        self.assertEqual([], agg_problems(Ctx()))

    def test_c_3_the_coverage_is_recounted_from_the_books_and_the_first_two_stage_records(self):
        self.assertEqual([], coverage_problems(Ctx()))

    def test_c_4_the_population_the_base_check_and_the_refs_are_recounted(self):
        self.assertEqual([], base_problems(Ctx()))

    def test_c_5_the_real_numbers_are_pinned_literally(self):
        c = Ctx()
        ag = agg_want(c)
        self.assertEqual(3726, len(c.R[u"行"]))
        self.assertEqual({(GROUP_A, "T1_VALUE"): 453, (GROUP_A, "T5_COINCIDENT"): 691, (GROUP_A, "T8_REL"): 1340, (GROUP_A, "T9_PRIOR_TO_CURRENT"): 50,
                          (GROUP_B, "T1_VALUE"): 219, (GROUP_B, "T5_COINCIDENT"): 313, (GROUP_B, "T8_REL"): 637, (GROUP_B, "T9_PRIOR_TO_CURRENT"): 23},
                         dict(((g, t), ag[g][t][u"注入の行"]) for g in GROUPS for t in TYPE_NAMES))
        self.assertEqual({(GROUP_A, "T1_VALUE"): 1, (GROUP_A, "T5_COINCIDENT"): 1, (GROUP_A, "T8_REL"): 2, (GROUP_A, "T9_PRIOR_TO_CURRENT"): 1,
                          (GROUP_B, "T1_VALUE"): 0, (GROUP_B, "T5_COINCIDENT"): 0, (GROUP_B, "T8_REL"): 0, (GROUP_B, "T9_PRIOR_TO_CURRENT"): 5},
                         dict(((g, t), ag[g][t][u"通した"][u"件"]) for g in GROUPS for t in TYPE_NAMES))
        cov = c.R[u"覆い"][u"群ごと"]
        self.assertEqual((239, 5405, 233, 175), (cov[GROUP_A][u"切れた本"], cov[GROUP_A][u"P33E が GROUNDED の行の合計"], cov[GROUP_A][u"GROUNDED が 1 行以上の本"], cov[GROUP_A][u"注入の行が 1 行以上の本"]))
        self.assertEqual((133, 2152, 122, 91), (cov[GROUP_B][u"切れた本"], cov[GROUP_B][u"P33E が GROUNDED の行の合計"], cov[GROUP_B][u"GROUNDED が 1 行以上の本"], cov[GROUP_B][u"注入の行が 1 行以上の本"]))
        self.assertEqual((24531, 372, 0), (c.R[u"土台の確かめ"][u"行"], c.R[u"土台の確かめ"][u"本"], c.R[u"土台の確かめ"][u"違う本"]))

    def test_d_1_the_passed_row_labels_match_the_passed_rows_of_the_inject_record(self):
        self.assertEqual([], passed_problems(Ctx()))

    def test_d_2_the_labels_are_pinned_literally(self):
        c = Ctx()
        self.assertEqual({u"a": 10, u"b": 0, u"c": 0, u"d": 0}, c.P[u"札の集計"])
        self.assertEqual([[1, 48, "B48-T1-02", "T1_VALUE", u"a"], [2, 82, "B82-T8-01", "T8_REL", u"a"], [3, 126, "B126-T5-02", "T5_COINCIDENT", u"a"],
                          [4, 148, "B148-T9-01", "T9_PRIOR_TO_CURRENT", u"a"], [5, 244, "B244-T8-06", "T8_REL", u"a"], [6, 314, "B314-T9-04", "T9_PRIOR_TO_CURRENT", u"a"],
                          [7, 314, "B314-T9-06", "T9_PRIOR_TO_CURRENT", u"a"], [8, 314, "B314-T9-07", "T9_PRIOR_TO_CURRENT", u"a"], [9, 314, "B314-T9-08", "T9_PRIOR_TO_CURRENT", u"a"],
                          [10, 314, "B314-T9-10", "T9_PRIOR_TO_CURRENT", u"a"]], c.P[u"行"])

    def test_e_1_the_records_hold_no_sentence_no_value_no_company_no_code_no_pointer(self):
        self.assertEqual([], clean_problems(Ctx()))

    def test_f_1_the_blocks_of_the_result_document_equal_the_rebuilt_tables(self):
        self.assertEqual([], doc_problems(Ctx()))

    def test_f_2_the_prediction_judgements_are_pinned_literally(self):
        c = Ctx()
        rows = dict((r[0], r[4]) for r in pred_table(c))
        self.assertEqual({u"V-1": u"当たり", u"V-2": u"当たり", u"V-3": V3_JUDGE, u"V-4": u"外れ(小項目 6 件中 2 件が外れ)", u"V-5": u"外れ(小項目 6 件中 1 件が外れ)", u"V-6": u"当たり",
                          u"V-7": u"当たり", u"V-8": u"当たり", u"V-9": u"外れ(読み 1・2 とも外れ)", u"V-10": u"当たり", u"V-11": u"当たり"}, rows)
        self.assertEqual((8, 3, 0), verdict_counts(c))
        self.assertEqual((7, 3, 10), verdict_counts_real(c))
        self.assertEqual((28, 5, 33), cell_counts(c))
        bad = [(x[0], x[1]) for x in cell_rows(c) if x[4] != u"当たり"]
        self.assertEqual([(u"V-4", u"丙・T1 の注入の行"), (u"V-4", u"丙・T5 の注入の行"), (u"V-5", u"A・T1 の通した率"),
                          (u"V-9", u"丙の注入の行のうち T8(読み 1: 分母は T1・T5・T8・T9 の合計)"), (u"V-9", u"丙の注入の行のうち T8(読み 2: 分母は主の T1・T5・T8 の合計)")], bad)

    def test_f_3_the_seal_prediction_bounds_are_in_the_seal_and_pinned(self):
        self.assertEqual([], seal_problems(Ctx().seal))
        self.assertEqual({(GROUP_A, "T1_VALUE"): (150, 700), (GROUP_A, "T5_COINCIDENT"): (150, 900), (GROUP_A, "T8_REL"): (900, 2000),
                          (GROUP_B, "T1_VALUE"): (0, 150), (GROUP_B, "T5_COINCIDENT"): (0, 150), (GROUP_B, "T8_REL"): (400, 1100)}, dict(V4_BOUNDS))

    def test_f_4_the_second_run_is_pinned_and_differs_only_in_the_time_field(self):
        u"""2 回目の記録は追跡しない。ここで留めるのは字(sha256・時間)で、byte の比較は環境変数で file を渡したときの AUDIT_CORE_TSS1B_RUN2 の試験(下)。"""
        self.assertEqual((804.1, 825.6), (RUN1_TIME, RUN2_TIME))
        self.assertRegex(RUN2_SHA, r"^[0-9a-f]{64}$")
        self.assertIn(RUN2_SHA, Ctx().doc)

    def test_g_1_the_seal_is_the_text_of_the_sealed_commit(self):
        self.assertEqual([], seal_frozen_problems(Ctx().seal))

    def test_g_2_the_real_history_has_the_seal_before_the_script_before_the_records_the_document_and_this_gate(self):
        u"""記録 2 つ・結果の文書・この門のどれかが未 commit なら赤(足した commit が無い。skip にしない)。全部 commit された後で初めて緑。"""
        self.assertEqual([], order_problems_real())

    def test_g_3_the_real_order_failure_before_the_commit_is_only_the_uncommitted_files(self):
        got = order_problems_real()
        self.assertTrue(all(p.startswith(u"UNCOMMITTED:") for p in got), got)

    def test_g_4_the_order_check_lists_the_two_records_the_document_and_this_gate(self):
        self.assertEqual(list(RECORD_RELS) + [DOC_REL, GATE_REL], order_others())
        self.assertEqual((u"fixtures/xbrl/tanshin_self/inject_2026-11-14.json", u"fixtures/xbrl/tanshin_self/inject_passed_types_2026-11-14.json"), RECORD_RELS)
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, r)) for r in RECORD_RELS + (DOC_REL, GATE_REL, SCRIPT_REL)))

    def test_g_5_engine_lib_and_the_previous_stages_are_untouched_and_the_script_is_unchanged_since_its_commit(self):
        self.assertEqual([], engine_problems())


class MutationTest(unittest.TestCase):
    def test_m_1_every_check_is_green_on_the_real_records(self):
        c = Ctx()
        for name in CHECKS:
            self.assertEqual([], check_problems(name, c), name)

    def test_m_2_every_mutation_turns_its_check_red(self):
        silent, crashed = [], []
        for label, check, fn in MUTATIONS:
            c = Ctx()                                     # 毎回新しい写し(変異は 1 か所だけ)
            fn(c)
            got = check_problems(check, c)
            if not got:
                silent.append(label)
            elif got[0].startswith(u"例外"):
                crashed.append(label)                     # 検査が落ちて赤になったのは「狙った理由で赤」ではない
        self.assertEqual(list(UNBOUND_MUTATIONS), silent, u"赤にならなかった変異(縛れない欄は UNBOUND_MUTATIONS に字で留める): %s" % silent)
        self.assertEqual(json.loads(cached_text(STATES_REL)), shared_json(STATES_REL))        # 共有の写しが変異で変わっていない
        self.assertEqual(json.loads(cached_text(INTERIM_REL)), shared_json(INTERIM_REL))
        self.assertEqual([], crashed, u"検査が例外で落ちて赤になった変異: %s" % crashed)

    def test_m_3_each_mutation_gets_a_new_copy_and_leaves_the_real_files_alone(self):
        before = dict((rel, sha256_rel(rel)) for rel in list(SHA_PIN) + [SEAL_REL, DOC_REL, STATES_REL, INTERIM_REL])
        c = Ctx()
        c.R[u"注入の行の数"] = -1
        c.doc = u"x"
        self.assertEqual(3726, Ctx().R[u"注入の行の数"])
        self.assertNotEqual(u"x", Ctx().doc)
        self.assertEqual(before, dict((rel, sha256_rel(rel)) for rel in before))

    def test_m_4_the_mutation_table_covers_every_check_and_every_effect_named_in_the_brief(self):
        checks = set(ch for _l, ch, _f in MUTATIONS)
        self.assertEqual(set(CHECKS), checks)
        self.assertGreaterEqual(len(MUTATIONS), 300)
        labels = u"\n".join(l for l, _c, _f in MUTATIONS)
        for need in (u"c 集計 集計/A/T1_VALUE/結果の語/通した/件", u"c 覆い 覆い/群ごと/A/作れる site が 0 の本", u"f 塊 main の行", u"f 塊 passed の行", u"d 札の集計", u"f 「人の目」の肯定形", u"f 漢数字で逃がす", u"b 来歴 engine の指紋",
                     u"g 封が commit のときと 1 字違う", u"b 限界の字を 1 つ変える", u"f 塊 pred の行", u"b 来歴 配線"):
            self.assertTrue(need in labels, need)

    def test_m_5_the_prose_number_check_accepts_a_block_number_and_refuses_another(self):
        c = Ctx()
        blocks = build_blocks(c)
        self.assertEqual([], prose_number_problems(u"本文。切れた本は 372 本(A 239・丙 133)。", blocks, c))
        self.assertNotEqual([], prose_number_problems(u"本文。切れた本は 373 本。", blocks, c))
        self.assertEqual([], prose_number_problems(u"本文。封 `20261114` と `ac10c814` と 2026-11-14 と P33E と V-10 と §3-1 と B314。", blocks, c))

    def test_m_6_the_person_eye_word_is_allowed_only_inside_the_quoted_limit(self):
        c = Ctx()
        self.assertEqual([], [p for p in doc_problems(c) if u"人の目" in p])
        c.doc += u"\n人の目で見た。\n"
        self.assertNotEqual([], [p for p in doc_problems(c) if u"人の目" in p])


class WiringTest(unittest.TestCase):
    def test_n_1_this_gate_carries_no_docid_tdnet_number_known_code_or_reserved_name(self):
        self.assertEqual([], SG.name_problems(rels=(GATE_REL,)))
        self.assertEqual([], SG.reserved_problems(rels=(GATE_REL,)))

    def test_n_2_this_gate_carries_no_verify_call_and_no_closed_folder_names(self):
        src = read(GATE_REL)
        self.assertNotIn(u"verify_" + u"document(", src)
        self.assertNotIn(u"sgogi-coach" + u"-handoff", src)
        self.assertNotIn(MS.ST.SKIP_CACHES[0], src)
        self.assertNotIn(u"urllib" + u".request", src)

    def test_n_3_the_gate_calls_none_of_the_scripts_tally_functions(self):
        u"""門は script の集計・規則・標本の関数を呼ばず、自前で数え直す(構造は ast で見る)。"""
        import ast
        tree = ast.parse(read(GATE_REL))
        banned = set([u"tally", u"block", u"inject_summary", u"coverage", u"run_inject", u"run_types", u"run_sheet", u"inject_book", u"summarize", u"pct"])
        used = [(n.value.id, n.attr) for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id in (u"MS", u"SG", u"TSS", u"TS")]
        self.assertEqual([], [x for x in used if x[1] in banned])
        self.assertEqual(set([u"VD", u"INJECT_LIMITS", u"FIELD_NAME_NOTE", u"TYPED_BY", u"PASSED_LABELS", u"TS", u"ST"]), set(x[1] for x in used if x[0] == u"MS"))

    def test_n_4_the_seal_gate_helper_is_loaded_without_overwriting_the_names_that_existed(self):
        import types
        marker = types.ModuleType("pswap_for_tss1b_result")
        before = sys.modules.get("pswap_for_tss1b_result")
        sys.modules["pswap_for_tss1b_result"] = marker
        try:
            mod = load_module(SCRIPT_REL, "tanshin_self_inject_script_reload_probe_for_result_gate")
            self.assertIs(marker, sys.modules["pswap_for_tss1b_result"])
            self.assertIs(mod, sys.modules["tanshin_self_inject_script_reload_probe_for_result_gate"])
        finally:
            if before is None:
                sys.modules.pop("pswap_for_tss1b_result", None)
            else:
                sys.modules["pswap_for_tss1b_result"] = before
            sys.modules.pop("tanshin_self_inject_script_reload_probe_for_result_gate", None)


@unittest.skipUnless(os.environ.get("AUDIT_CORE_TSS1B_RUN2"), u"2 回目の走りの file の path が環境変数 AUDIT_CORE_TSS1B_RUN2 に渡されたときだけ走る")
class Run2Test(unittest.TestCase):
    def _strip(self, text):
        return re.sub(r'^ *"時間\(秒\)": .*$', u"", text, flags=re.M)

    def test_r_1_the_second_run_has_the_pinned_sha256_and_differs_only_in_the_time_field(self):
        p = os.environ["AUDIT_CORE_TSS1B_RUN2"]
        with io.open(p, "rb") as fh:
            raw = fh.read()
        self.assertEqual(RUN2_SHA, hashlib.sha256(raw).hexdigest())
        self.assertEqual(self._strip(cached_text(INJECT_REL)), self._strip(raw.decode("utf-8")))
        self.assertEqual(RUN2_TIME, json.loads(raw.decode("utf-8"))[u"時間(秒)"])


if __name__ == "__main__":
    unittest.main()
