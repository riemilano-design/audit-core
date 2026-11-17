# -*- coding: utf-8 -*-
"""結果の門: 封 docs/XBRL_YUHO_SECTIONS_SEAL_2026-11-16.md §3・§6(YS ― 有価証券報告書の 3 つの節 = 研究開発活動・設備投資等の概要・配当政策の文を、同じ有報の fact で確かめる便の結果)。

封の門 ``test_xbrl_yuho_sections_seal.py`` の次の段。**追跡されている記録 3 つ・封・結果の文書だけを読む**(cache の材料が無い機械でも緑。材料から測り直す試験だけ環境変数
``AUDIT_CORE_YS_REMEASURE=1`` で走る)。

縛るもの(検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表で 1 本ずつ。木の file は変異させず、``Ctx`` の写しに当てる。
``Ctx(root)`` は別の folder の写しも読めるので、file の字を変えた写しを使い捨ての folder に作る試験もある)
 a 記録 3 つと script の sha256(字で留める)  b 記録の来歴の欄(script・前の便の script・封の表・母集団の表・engine の指紋・states の記録の sha256 を実物と突き合わせる)
 c 母集団の記録が封 §1 の表の 201 行と同じ・3 つの記録の # の集合が合う
 d 判定の記録を本の行から数え直す(script の集計は呼ばない。集計の欄と両方に当てる)
 e 読みの記録: 行の数・組ごとの数・型の集計を行から数え直す・読む行が判定の記録の行と合う・G 研究と G 設備の 60 行を種から引き直す
 f 記録に文も値も会社名も証券コードも docID も pointer の字も無い(封の門が見ている欄・docID は重ねない)
 g 結果の文書の塊 16 個を記録から作り直して 1 行ずつ照らす・塊の外の 2 桁以上の数・予測の当たり外れ・封 §6 の 11 項の字
 h 封が e7754d70 から 1 字も変わっていない・順序(commit の順。未 commit は赤)・engine 0 行・script が 3b9c54bc から変わっていない
この file は docID の字を持たない。
"""
import collections
import hashlib
import importlib.util
import io
import json
import os
import random
import re
import shutil
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


SG = load_module("tests/measure/test_xbrl_yuho_sections_seal.py", "ys_seal_gate_for_ys_result_gate")      # 封の門の部品。門としては走らせない
PR = SG.PR
MS = SG.MS

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
GATE_REL = SG.LATER_GATE_REL
DOC_REL = SG.DOC_REL
POP_REL, STATES_REL, TYPES_REL = SG.RECORD_RELS
RECORD_RELS = (POP_REL, STATES_REL, TYPES_REL)
SCRIPT_COMMIT = "3b9c54bc"                                  # script と封の門を足した commit(この commit から script は 0 行)

# ---- 字で留める(記録・script の sha256。人が決めた数は字で留める)
SHA_PIN = collections.OrderedDict([
    (POP_REL, "7264bd201eeff1f2b011e783fe26ae4b9435ca7e3fb0436f148a662ff16a3374"),
    (STATES_REL, "130498b4781160154210cacd31d35a8498e4d460f7d3ac88968bf21a7aae4ac5"),
    (TYPES_REL, "9087a95d0f51e559012b72a9f5f2af7c9575e57589120b50b7ba1d93f46fd3bb"),
    (SCRIPT_REL, "23162fa9221aaa7a71e2ab602c46ac92cb473bb85d3fdeef75ba4c2d22373191")])
STATES = (u"GROUNDED", u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND")
G, VM, UNV, PNF = STATES
RD, EQ, DV = SG.SECTIONS
SECS = (RD, EQ, DV)
GROUPS = (u"甲", u"乙", u"丙")
WHYS = (u"decode", u"札なし", u"札が複数", u"続きあり", u"閉じない", u"空")
LABELS = (u"V 研究", u"V 設備", u"V 配当", u"G 研究", u"G 設備", u"G 配当")
V_LABELS, G_LABELS = LABELS[:3], LABELS[3:]
LABEL_SEC = collections.OrderedDict(zip(LABELS, (RD, EQ, DV, RD, EQ, DV)))
V_TYPES = tuple(u"アイウエオカキクケ")
G_TYPES = (u"a", u"b", u"c")
DIFFS = (u"項目", u"範囲", u"側", u"期")
SEED, DRAW_N = 20261116, 60
N_BOOKS = 201
PERIODS = (u"CurrentYear", u"Prior1Year", u"Prior2Year")
FAMILIES = (u"%", u"円族", u"他")
BLOCK_NAMES = (u"pred", u"width", u"sec_rd", u"sec_capex", u"sec_div", u"ten", u"reasons", u"mech", u"read", u"types_v", u"types_g", u"types_b", u"cross", u"rows_v", u"rows_g", u"sha")
NO_NUMBER_BLOCKS = (u"sha",)                                # sha256 の字は数の集合に入れない
FORBIDDEN_WORDS = (u"精" + u"度", u"ハルシ" + u"ネーション", u"証明" + u"した", u"LLM より" + u"正確", u"世界で 1 " + u"社", u"人の" + u"目")
DOCID_RE = re.compile(r"S100[0-9A-Z]{4}")
TDNET_RE = re.compile(r"0812\d{14}")
CODE_RE = re.compile(r"(?<![0-9A-Za-z\-])\d{3}[0-9A-Z](?![0-9A-Za-z\-])")
POINTER_RE = re.compile(r"xbrl:|jppfs|jpcrp|jpdei|_cor:|@(Current|Prior)|formula:")
COMPANY_WORDS = (u"株式会社", u"有限会社", u"合同会社", u"㈱", u"(株)")
AUDITOR_RE = re.compile(u"あずさ|トーマツ|新日本|太陽有限|PwC|仰星|三優|東陽|アーク有限|ひびき|KPMG|Deloitte|EY ")
KANJI_NUM_RE = re.compile(u"[二三四五六七八九]百|[一二三四五六七八九]千|百[一二三四五六七八九十]|千[一二三四五六七八九百]")        # 3 桁以上の数を漢数字で逃がす字(「百万円」の単位は当たらない)
JA_RE = re.compile(u"[぀-ヿ一-鿿]")
LONG_JA = 40
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
TYPED_BY = u"司令塔(AI の席 1 席)。人は読んでいない"
TYPES_BLIND = u"盲検ではない(封の予測を知ったうえで付けた)。(ク) は候補で、紙面で確かめていない"
POP_STEP = u"YS(有報の 3 つの節の文を同じ有報の fact で確かめる)― 母集団 201 本の記録(0 USD・通信なし)"
STATES_STEP = u"YS(有報の 3 つの節の文を同じ有報の fact で確かめる)― 201 本の切り出し・判定(0 USD・通信なし)"
TYPES_STEP = u"YS ― 読む行の型分け(0 USD)"
MATERIAL_PLACE = u"~/.cache/audit-core の 3 つの folder(甲・乙・丙。名前は書かない)"
RULE_V = u"その節の VALUE_MISMATCH の全部の行"
RULE_G_DV = u"配当政策の GROUNDED の全部の行"
RULE_G_DRAW = u"その節の GROUNDED の行を # の順・文の番号の順・位置の順に並べ、節ごとに新しい random.Random(種).sample(range(行の数), 引く数) を番号の順に。行の数が引く数に満たなければ全部"
ROW_COLS = [u"文の番号", u"位置", u"state", u"reason", u"pointer の期", u"formula の有無", u"単位の族", u"両期の fact を引く a−b", u"span に % を含む",
            u"pointer の字のどれかに NonConsolidatedMember を含む"]
POP_KEYS = (u"seal", u"封の commit", u"step", u"HEAD の commit", u"この script の sha256", u"封の表の sha256", u"母集団の表(# TAB 群 TAB sha256 の行)の sha256", u"範囲", u"材料", u"群",
            u"byte 数の合計", u"行の欄", u"行", u"key_leaks")
STATES_KEYS = (u"seal", u"封の commit", u"step", u"HEAD の commit", u"この script の sha256", u"KAM の script の sha256", u"2026-11-09 の便の script の sha256", u"TSS の script の sha256",
               u"封の表の sha256", u"母集団の表(# TAB 群 TAB sha256 の行)の sha256", u"engine の指紋", u"profile", u"材料", u"切り出し", u"判定", u"本の数", u"集計", u"限界", u"行の欄", u"時間(秒)",
               u"key_leaks", u"本")
TYPES_KEYS = (u"seal", u"封の commit", u"step", u"HEAD の commit", u"この script の sha256", u"states の記録の sha256", u"型を付けた席", u"盲検", u"読む行の規則", u"型の字", u"型の集計",
              u"b の違うものの集計", u"行の欄", u"行", u"key_leaks")
RULE_KEYS = (u"V 研究・V 設備・V 配当", u"G 配当", u"G 研究・G 設備", u"種", u"引く数", u"G 研究の行の数", u"G 設備の行の数", u"読む行の数", u"読む行の数の合計")
BOOK_KEYS = (u"#", u"群", u"ZIP の sha256") + SECS
SIDE_KEYS = (u"切り出し", u"理由", u"字数", u"claim", u"対応", u"行")
TEN_KEY = u"10 欄目(pointer の字のどれかに NonConsolidatedMember を含む)の数"
AGG_KEYS = (u"本", u"切れた", u"切れない", u"切れない理由", u"字数の合計", u"claim", u"4 state", u"reason", u"VALUE_MISMATCH の内訳", TEN_KEY,
            u"切れた本のうち claim が 0 の本", u"切れた本のうち GROUNDED が 0 の本", u"VALUE_MISMATCH が 1 以上の本", u"claim と raw の並びが対応しなかった本")
VM_KEYS = (u"行", u"導出(formula)", u"直接", u"% の数", u"円族の数", u"両期の fact を引く a−b(円)", u"単位の族が %", u"単位の族が円族", u"単位の族が他", u"pointer の期")
VM_PERIOD_KEYS = (u"CurrentYear", u"Prior1Year", u"Prior2Year", u"他", u"なし")
TRUE, FALSE = u"真", u"偽"
PRED_IDS = SG.PRED_IDS
Y6_ACTUAL = u"追跡している記録に在るのは 1 回目だけ。2 回目の判定の記録(scratchpad に置き、追跡していない)と追跡の states の記録は、時間の欄を除いて byte で同じだった"
Y6_JUDGE = u"当たり(一回限りの手の実測で、門ではない。材料から測り直す試験は環境変数 `AUDIT_CORE_YS_REMEASURE=1` のときだけ走る)"
Y6_PRED = u"byte で同じ"
BOUND_PHRASES = collections.OrderedDict([(u"Y-7", u"0〜2 行"), (u"Y-8", u"4 行以上"), (u"Y-9", u"3 行以上"), (u"Y-10", u"0〜4 行"), (u"Y-11", u"0〜6 行"), (u"Y-12", u"0〜5 行"), (u"Y-13", u"0〜17 行")])
REQUIRED_PHRASES = (u"AI の席", u"人は読んでいない", u"盲検ではない", u"紙面", u"候補", u"測っていない", u"読んでいない", u"足さない", u"採用 / 不採用の判定は無い", u"食い違い")
PER_UNIT = u"per_unit_counter"
PER_UNIT_SEALED = 351                                        # 封 Y-5(配当政策の UNVERIFIABLE のうち per_unit_counter の行)


# ======================================================================================================
# 道具
def read(rel, root=ROOT):
    with io.open(os.path.join(root, rel), encoding="utf-8") as fh:
        return fh.read()


def read_bytes(rel, root=ROOT):
    with io.open(os.path.join(root, rel), "rb") as fh:
        return fh.read()


def sha256_rel(rel, root=ROOT):
    return hashlib.sha256(read_bytes(rel, root)).hexdigest()


def sha256_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


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


def plain(x):
    return json.loads(json.dumps(x, ensure_ascii=False))


def tmpdir():
    return tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR"))


_TEXT = {}


def cached_text(rel, root=ROOT):
    if (root, rel) not in _TEXT:
        _TEXT[(root, rel)] = read(rel, root)
    return _TEXT[(root, rel)]


_CUR = {}


def current_values():
    u"""今の file・engine の値(1 回だけ数える。Ctx は写しを持つ)。"""
    if not _CUR:
        _CUR.update({"script": sha256_rel(SCRIPT_REL), "kam": sha256_rel(MS.KAM_SCRIPT_REL), "tss": sha256_rel(MS.TSS_SCRIPT_REL), "ts": sha256_rel(MS.TS_SCRIPT_REL),
                     "seal": sha256_rel(SEAL_REL), "states": sha256_rel(STATES_REL), "fp": MS.VD.engine_fingerprint()})
    return dict(_CUR)


class Ctx(object):
    u"""記録・封・文書・今の file の値。変異は毎回 ``Ctx()`` の新しい写しに 1 か所だけ加える。``root`` を渡すと別の folder の写し(使い捨ての folder)を読む。"""

    def __init__(self, root=ROOT):
        self.root = root
        self.P = json.loads(cached_text(POP_REL, root))
        self.S = json.loads(cached_text(STATES_REL, root))
        self.R = json.loads(cached_text(TYPES_REL, root))
        self.seal = cached_text(SEAL_REL, root)
        self.doc = cached_text(DOC_REL, root) if os.path.exists(os.path.join(root, DOC_REL)) else u""
        self.texts = collections.OrderedDict((rel, read_bytes(rel, root)) for rel in SHA_PIN if os.path.exists(os.path.join(root, rel)))
        self.cur = current_values()
        if root != ROOT:
            self.cur["seal"] = sha256_rel(SEAL_REL, root)
            self.cur["states"] = sha256_rel(STATES_REL, root)


# ======================================================================================================
# 封から読む字
def seal_y_rows(seal):
    u"""封 §3 の Y-1〜Y-13(id → (欄, 予測, 外れ方))。"""
    sec = seal[seal.index(u"## §3"):seal.index(u"## §4")]
    out = collections.OrderedDict()
    for m in re.finditer(r"^\| (Y-\d+) \| (.*?) \| (.*?) \| (.*?) \|$", sec, re.M):
        out[m.group(1)] = (m.group(2), m.group(3), m.group(4))
    return out


def seal_limits(seal):
    u"""封 §6 の 11 項(字のまま)。"""
    sec = seal[seal.index(u"## §6"):]
    return [m.group(1) for m in re.finditer(r"^- (.*)$", sec, re.M)]


def seal_type_texts(seal):
    u"""封 §0-2 の 7 の型の字({V: {ア: 字}, G: {a: 字}})。太字の印は外す。"""
    sec = seal[seal.index(u"7. **読む行**"):seal.index(u"8. **注入")]
    v, g = collections.OrderedDict(), collections.OrderedDict()
    for m in re.finditer(r"^\s+- \(([アイウエオカキクケ])\) (.*)$", sec, re.M):
        v.setdefault(m.group(1), m.group(2).replace(u"**", u""))                 # 最初の行だけ(あとの「(ク) は候補で…」は型の字でない)
    for m in re.finditer(r"^\s+- \(([abc])\) (.*)$", sec, re.M):
        g.setdefault(m.group(1), m.group(2).replace(u"**", u""))
    return v, g


def table_sha(seal):
    return sha256_text(u"\n".join(u"%d\t%s\t%s" % (r[0], r[1], r[2]) for r in SG.seal_table(seal)))


# ======================================================================================================
# a. sha256
def sha_problems(texts):
    out = []
    for rel, want in SHA_PIN.items():
        if hashlib.sha256(texts.get(rel, b"")).hexdigest() != want:
            out.append(u"sha256: %s が字で留めた値と違う" % rel)
    return out


# ======================================================================================================
# b. 来歴
def head_ok(root, c):
    return bool(isinstance(c, str) and HEX40.match(c)) and PR.is_anc(root, SCRIPT_COMMIT, c)


def material_problems(rec, name):
    out = []
    m = rec.get(u"材料") or {}
    z = m.get(u"3 つの folder の一覧の前後(件数・名前の sha256)") or {}
    pre = z.get(u"前")
    if m.get(u"置き場") != MATERIAL_PLACE or m.get(u"表と一致した ZIP") != N_BOOKS or z.get(u"変化なし") is not True or pre != z.get(u"後") or not isinstance(pre, list) or len(pre) != 3 \
            or any(not (isinstance(x, list) and len(x) == 2 and is_int(x[0]) and HEX64.match(str(x[1]))) for x in pre) or [x[0] for x in pre] != [281, 40, 94]:
        out.append(u"来歴[%s]: 材料が「201 本そろった・3 つの folder の一覧の前後が同じ」でない" % name)
    return out


def provenance_problems(c, root=REPO):
    u"""3 つの記録の header: seal・封の commit・step・script の sha256・HEAD の commit・key_leaks・封の表・母集団の表・engine の指紋・states の記録の sha256。"""
    out = []
    cur = c.cur
    seal_table_rows = SG.seal_table(c.seal)
    for name, rec, keys, step in ((u"population", c.P, POP_KEYS, POP_STEP), (u"states", c.S, STATES_KEYS, STATES_STEP), (u"read_types", c.R, TYPES_KEYS, TYPES_STEP)):
        if tuple(rec.keys()) != keys:
            out.append(u"来歴[%s]: 欄の名前・並びが字で留めたものと違う" % name)
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
    for name, rec in ((u"population", c.P), (u"states", c.S)):
        if rec.get(u"封の表の sha256") != cur["seal"]:
            out.append(u"来歴[%s]: 封の表の sha256 が今の封と違う" % name)
        if rec.get(u"母集団の表(# TAB 群 TAB sha256 の行)の sha256") != table_sha(c.seal) or len(seal_table_rows) != N_BOOKS:
            out.append(u"来歴[%s]: 母集団の表の sha256 が封の表から作り直した値と違う" % name)
        out += material_problems(rec, name)
    S = c.S
    if S.get(u"KAM の script の sha256") != cur["kam"] or S.get(u"2026-11-09 の便の script の sha256") != cur["ts"] or S.get(u"TSS の script の sha256") != cur["tss"]:
        out.append(u"来歴[states]: 前の便の script の sha256 が今の file と違う")
    fp = S.get(u"engine の指紋") or {}
    # 2026-11-17(NRE): 記録の指紋 = 記録を作った時の engine(T の後・NRE の前)で、今の engine はそこから NRE の宣言された遷移だけ離れている(封 docs/XBRL_NIL_READ_ENGINE_SEAL_2026-11-17.md §2-3。SGR.nre_record_fingerprint_ok)。記録は作り直さない。他の値の組は今までどおり赤
    if not SG.SGR.nre_record_fingerprint_ok(fp.get(u"adapter_xbrl_py_sha256"), cur["fp"]["adapter_xbrl_py_sha256"]) or fp.get(u"core_py_sha256") != cur["fp"]["core_py_sha256"] \
            or fp.get(u"adapter_xbrl_py_files") != cur["fp"]["adapter_xbrl_py_files"] or fp.get(u"core_py_files") != cur["fp"]["core_py_files"] or not head_ok(root, fp.get(u"git_commit")):
        out.append(u"来歴[states]: engine の指紋が今の engine と違う")
    if S.get(u"profile") != u"P33E":
        out.append(u"来歴[states]: profile が P33E でない")
    t = S.get(u"時間(秒)")
    if isinstance(t, bool) or not isinstance(t, (int, float)) or t < 0:
        out.append(u"来歴[states]: 時間(秒)が数でない")
    if c.R.get(u"states の記録の sha256") != cur["states"]:
        out.append(u"来歴[read_types]: states の記録の sha256 が今の file と違う")
    if c.R.get(u"型を付けた席") != TYPED_BY or c.R.get(u"盲検") != TYPES_BLIND:
        out.append(u"来歴[read_types]: 型を付けた席・盲検の字が違う")
    if c.R.get(u"行の欄") != [u"読みの組", u"本の #", u"文の番号", u"位置", u"型", u"違うもの"]:
        out.append(u"来歴[read_types]: 行の欄が封のとおりでない")
    if c.S.get(u"行の欄") != ROW_COLS:
        out.append(u"来歴[states]: 行の欄が封の 10 欄でない")
    if c.S.get(u"限界") != list(SG.LIMITS_PINNED):
        out.append(u"来歴[states]: 限界の字が封の門で留めた字と違う")
    if c.S.get(u"切り出し") != dict(SG.CUT_RECORD_PINNED) or c.S.get(u"判定") != dict(SG.JUDGE_RECORD_PINNED):
        out.append(u"来歴[states]: 切り出し・判定の欄が封の門で留めた字と違う")
    return out


# ======================================================================================================
# c. 母集団の記録・3 つの記録の # の集合
def population_problems(c):
    P = c.P
    out = []
    want = [(r[0], r[1], r[2]) for r in SG.seal_table(c.seal)]
    rows = P.get(u"行") or []
    if len(want) != N_BOOKS or [tuple(r[:3]) for r in rows] != want:
        out.append(u"population: 行が封 §1 の表の 201 行(# ・群・sha256 の順)と違う")
    if any(not (len(r) == 4 and is_int(r[3]) and r[3] > 0) for r in rows):
        out.append(u"population: 行が「# ・群・sha256・byte 数(正の整数)」でない")
    elif P.get(u"byte 数の合計") != sum(r[3] for r in rows):
        out.append(u"population: byte 数の合計が行の和と違う")
    if P.get(u"群") != dict((g, sum(1 for r in rows if r[1] == g)) for g in GROUPS) or P.get(u"群") != {u"甲": 67, u"乙": 40, u"丙": 94}:
        out.append(u"population: 群ごとの本の数が 甲 67・乙 40・丙 94 でない")
    if P.get(u"行の欄") != [u"#", u"群", u"ZIP の sha256", u"byte 数"] or P.get(u"範囲") != u"封 §1 の 201 本":
        out.append(u"population: 行の欄・範囲が違う")
    return out


def keys_problems(c):
    u"""記録 3 つの # の集合: population の # と states の # が同じ 201 本・read_types の本の # は states に在る(その行の節・文の番号・位置・state は types_problems が見る)。"""
    out = []
    pop = [r[0] for r in c.P.get(u"行") or []]
    books = [b.get(u"#") for b in c.S.get(u"本") or []]
    if len(pop) != N_BOOKS or len(set(pop)) != N_BOOKS or sorted(pop) != list(range(1, N_BOOKS + 1)):
        out.append(u"keys: population の # が 1〜201 の 201 本でない")
    if len(books) != N_BOOKS or len(set(books)) != N_BOOKS:
        out.append(u"keys: states の本が 201 本でない・# が重なる")
    if set(pop) != set(books):
        out.append(u"keys: population の # の集合と states の # の集合が違う")
    if any(r[1] not in set(books) for r in c.R.get(u"行") or []):
        out.append(u"keys: read_types の本の # が states に無い")
    return out


# ======================================================================================================
# d. 判定の記録
def cut_of(b, sec):
    return b[sec][u"切り出し"] == u"切れた"


def recount_sec(books, sec, grp=None):
    u"""判定の集計を、本の行から別の書き方で数え直す(script の ``block``・``tally`` は使わない)。"""
    bs = [b for b in books if grp is None or b[u"群"] == grp]
    cut = [b for b in bs if cut_of(b, sec)]
    rows = [r for b in bs for r in b[sec][u"行"]]
    vm = [r for r in rows if r[2] == VM]
    rs = collections.OrderedDict()
    for s in STATES:
        rs[s] = collections.Counter(u"なし" if r[3] is None else r[3] for r in rows if r[2] == s)
    pk = collections.Counter(r[4] for r in vm)
    ten = collections.OrderedDict((s, collections.OrderedDict([(TRUE, sum(1 for r in rows if r[2] == s and r[9] is True)), (FALSE, sum(1 for r in rows if r[2] == s and r[9] is False))])) for s in STATES)
    period = collections.OrderedDict((k, pk.get(k, 0)) for k in PERIODS)
    period[u"他"] = sum(n for k, n in pk.items() if k not in PERIODS and k != u"なし")
    period[u"なし"] = pk.get(u"なし", 0)
    return collections.OrderedDict([
        (u"本", len(bs)), (u"切れた", len(cut)), (u"切れない", len(bs) - len(cut)),
        (u"切れない理由", collections.OrderedDict((k, sum(1 for b in bs if not cut_of(b, sec) and b[sec][u"理由"] == k)) for k in WHYS)),
        (u"字数の合計", sum(b[sec][u"字数"] for b in cut)),
        (u"claim", len(rows)), (u"4 state", collections.OrderedDict((s, sum(1 for r in rows if r[2] == s)) for s in STATES)),
        (u"reason", collections.OrderedDict((s, dict(rs[s])) for s in STATES)),
        (u"VALUE_MISMATCH の内訳", collections.OrderedDict([
            (u"行", len(vm)), (u"導出(formula)", sum(1 for r in vm if r[5])), (u"直接", sum(1 for r in vm if not r[5])), (u"% の数", sum(1 for r in vm if r[8])),
            (u"円族の数", sum(1 for r in vm if not r[8])), (u"両期の fact を引く a−b(円)", sum(1 for r in vm if r[7])),
            (u"単位の族が %", sum(1 for r in vm if r[6] == u"%")), (u"単位の族が円族", sum(1 for r in vm if r[6] == u"円族")), (u"単位の族が他", sum(1 for r in vm if r[6] == u"他")),
            (u"pointer の期", period)])),
        (TEN_KEY, ten),
        (u"切れた本のうち claim が 0 の本", sum(1 for b in cut if not b[sec][u"行"])), (u"切れた本のうち GROUNDED が 0 の本", sum(1 for b in cut if not any(r[2] == G for r in b[sec][u"行"]))),
        (u"VALUE_MISMATCH が 1 以上の本", sum(1 for b in cut if any(r[2] == VM for r in b[sec][u"行"]))), (u"claim と raw の並びが対応しなかった本", sum(1 for b in cut if b[sec][u"対応"] is not True))])


def mech_rows(books, sec, state):
    u"""節 ``sec`` の ``state`` の行(全部の本。3 つの節は足さない)。"""
    return [r for b in books for r in b[sec][u"行"] if r[2] == state]


def row_shape_ok(r):
    return (len(r) == 10 and is_int(r[0]) and is_int(r[1]) and r[2] in STATES and (r[3] is None) == (r[2] in (G, VM)) and (r[3] is None or isinstance(r[3], str))
            and isinstance(r[4], str) and isinstance(r[5], bool) and r[6] in FAMILIES and isinstance(r[7], bool) and isinstance(r[8], bool) and isinstance(r[9], bool))


def states_problems(c):
    S = c.S
    out = []
    books = S.get(u"本") or []
    want = [(r[0], r[1], r[2]) for r in SG.seal_table(c.seal)]
    if S.get(u"本の数") != N_BOOKS or len(books) != N_BOOKS or [(b.get(u"#"), b.get(u"群"), b.get(u"ZIP の sha256")) for b in books] != want:
        out.append(u"states: 本が封 §1 の表の 201 本(# ・群・sha256 の順)でない")
        return out
    shape_bad = False
    for b in books:
        if tuple(b.keys()) != BOOK_KEYS:
            out.append(u"states: 本の欄が違う(# %s)" % b.get(u"#"))
            shape_bad = True
            continue
        for sec in SECS:
            d = b[sec]
            if tuple(d.keys()) != SIDE_KEYS:
                out.append(u"states: 本 %d の %s の欄が違う" % (b[u"#"], sec))
                shape_bad = True
                continue
            cut = d[u"切り出し"] == u"切れた"
            if d[u"切り出し"] not in (u"切れた", u"切れない") or cut != (d[u"理由"] is None) or (not cut and d[u"理由"] not in WHYS):
                out.append(u"states: 本 %d の %s の切り出しと理由が合わない" % (b[u"#"], sec))
            if not is_int(d[u"claim"]) or d[u"claim"] != len(d[u"行"]):
                out.append(u"states: 本 %d の %s の claim が行の数と違う" % (b[u"#"], sec))
            if cut and (not is_int(d[u"字数"]) or d[u"字数"] <= 0 or d[u"対応"] is not True):
                out.append(u"states: 本 %d の %s が切れたのに字数・対応が正でない" % (b[u"#"], sec))
            if not cut and (d[u"字数"] is not None or d[u"対応"] is not None or d[u"行"] or d[u"claim"]):
                out.append(u"states: 切れない本 %d の %s に字数・行が在る" % (b[u"#"], sec))
            keys = [(r[0], r[1]) for r in d[u"行"]]
            if keys != sorted(set(keys)):
                out.append(u"states: 本 %d の %s の行が (文の番号, 位置) の昇順で 1 行ずつでない" % (b[u"#"], sec))
            for r in d[u"行"]:
                if not row_shape_ok(r):
                    out.append(u"states: 本 %d の %s の行が封の 10 欄でない" % (b[u"#"], sec))
                    shape_bad = True
                    break
    if shape_bad:
        return out                                   # 形が壊れた記録は数え直さない(数え直しが例外で落ちて赤になるのを避ける)
    agg = S.get(u"集計") or {}
    if tuple(agg.keys()) != SECS:
        out.append(u"states: 集計の節が 研究開発活動・設備投資等の概要・配当政策 でない")
    for sec in SECS:
        a = agg.get(sec) or {}
        if tuple(a.keys()) != GROUPS + (u"計",):
            out.append(u"states: 集計[%s]の群が 甲・乙・丙・計 でない" % sec)
        for g in GROUPS + (None,):
            name = g or u"計"
            got = a.get(name) or {}
            w = recount_sec(books, sec, g)
            if tuple(got.keys()) != AGG_KEYS:
                out.append(u"states: 集計[%s][%s]の欄の名前が違う" % (sec, name))
            for k in w:
                if plain(w[k]) != plain(got.get(k)):
                    out.append(u"states: 集計[%s][%s]の %s が行から数え直した値と違う" % (sec, name, k))
            if tuple((got.get(u"VALUE_MISMATCH の内訳") or {}).keys()) != VM_KEYS:
                out.append(u"states: 集計[%s][%s]の VALUE_MISMATCH の内訳の欄の名前が違う" % (sec, name))
    return out


# ======================================================================================================
# e. 読みの記録
def state_index(S):
    u"""{(節, 本の #, 文の番号, 位置): 行}。"""
    d = {}
    for b in S[u"本"]:
        for sec in SECS:
            for r in b[sec][u"行"]:
                d[(sec, b[u"#"], r[0], r[1])] = r
    return d


def expected_reading(S):
    u"""読む行(封 §0-2 の 7)を判定の記録から引き直す。({組: [(本の #, 文の番号, 位置)]}, {組: 母の行の数})。G 研究・G 設備は節ごとに新しい Random(種) の sample で 60 行。"""
    def rows_of(sec, state):
        out = []
        for b in sorted(S[u"本"], key=lambda b: b[u"#"]):
            for r in sorted((r for r in b[sec][u"行"] if r[2] == state), key=lambda r: (r[0], r[1])):
                out.append((b[u"#"], r[0], r[1]))
        return out
    items, mother = collections.OrderedDict(), collections.OrderedDict()
    for lab in LABELS:
        rows = rows_of(LABEL_SEC[lab], VM if lab.startswith(u"V") else G)
        mother[lab] = len(rows)
        if lab in (u"G 研究", u"G 設備") and len(rows) > DRAW_N:
            idx = sorted(random.Random(SEED).sample(range(len(rows)), DRAW_N))
            rows = [rows[i] for i in idx]
        items[lab] = rows
    return items, mother


def type_set(label):
    return V_TYPES if label.startswith(u"V") else G_TYPES


def types_problems(c):
    R, S = c.R, c.S
    out = []
    rows = R.get(u"行") or []
    sidx = state_index(S)
    exp, mother = expected_reading(S)
    for r in rows:
        if not (len(r) == 6 and r[0] in LABELS and all(is_int(x) for x in r[1:4]) and r[4] in type_set(r[0]) and ((r[4] == u"b") == (r[5] is not None)) and (r[5] is None or r[5] in DIFFS)):
            out.append(u"types: 行が「組・本の #・文の番号・位置・型(組に合う)・違うもの(b のときだけ)」でない")
            return out
    if [r[0] for r in rows] != [lab for lab in LABELS for _r in exp[lab]]:
        out.append(u"types: 行の組の並び・数が、読む行の規則から引き直した並び・数と違う")
    for lab in LABELS:
        got = [tuple(r[1:4]) for r in rows if r[0] == lab]
        if got != exp[lab]:
            out.append(u"types: 組 %s の行が、判定の記録から引き直した読む行と 1 行ずつ同じでない" % lab)
        for r in rows:
            if r[0] == lab:
                s = sidx.get((LABEL_SEC[lab], r[1], r[2], r[3]))
                if s is None or s[2] != (VM if lab.startswith(u"V") else G):
                    out.append(u"types: 組 %s の行が判定の記録の行と合わない(節か state か位置)" % lab)
                    break
    rule = R.get(u"読む行の規則") or {}
    cnt = collections.OrderedDict((lab, len(exp[lab])) for lab in LABELS)
    if tuple(rule.keys()) != RULE_KEYS or rule.get(u"V 研究・V 設備・V 配当") != RULE_V or rule.get(u"G 配当") != RULE_G_DV or rule.get(u"G 研究・G 設備") != RULE_G_DRAW:
        out.append(u"types: 読む行の規則の欄の名前・字が違う")
    if rule.get(u"種") != SEED or rule.get(u"引く数") != DRAW_N or rule.get(u"G 研究の行の数") != mother[u"G 研究"] or rule.get(u"G 設備の行の数") != mother[u"G 設備"] \
            or rule.get(u"読む行の数") != dict(cnt) or rule.get(u"読む行の数の合計") != sum(cnt.values()) or len(rows) != sum(cnt.values()):
        out.append(u"types: 読む行の規則の欄(種・引く数・G の行の数・組ごとの数・合計)が違う")
    if mother[u"G 研究"] != 85 or mother[u"G 設備"] != 150 or cnt[u"G 研究"] != DRAW_N or cnt[u"G 設備"] != DRAW_N:
        out.append(u"types: G 研究・G 設備が「母 85・150 行から 60 行ずつ」でない")
    if [mother[lab] for lab in (u"V 研究", u"V 設備", u"V 配当", u"G 配当")] != [cnt[lab] for lab in (u"V 研究", u"V 設備", u"V 配当", u"G 配当")]:
        out.append(u"types: V の 3 組と G 配当が「母の全部」でない")
    v_txt, g_txt = seal_type_texts(c.seal)
    tt = R.get(u"型の字") or {}
    if tt != {u"V": dict(v_txt), u"G": dict(g_txt), u"違うもの": list(DIFFS)} or list(tt.get(u"V", {}).keys()) != list(V_TYPES) or list(tt.get(u"G", {}).keys()) != list(G_TYPES):
        out.append(u"types: 型の字が封 §0-2 の 7 の字と違う")
    want_cnt = collections.OrderedDict((lab, collections.OrderedDict((t, sum(1 for r in rows if r[0] == lab and r[4] == t)) for t in type_set(lab))) for lab in LABELS)
    got_cnt = R.get(u"型の集計") or {}
    if plain(want_cnt) != plain(got_cnt) or list(got_cnt.keys()) != list(LABELS):
        out.append(u"types: 型の集計が行から数え直した値と違う")
    want_d = collections.OrderedDict((lab, collections.OrderedDict((d, sum(1 for r in rows if r[0] == lab and r[4] == u"b" and r[5] == d)) for d in DIFFS)) for lab in G_LABELS)
    if plain(want_d) != plain(R.get(u"b の違うものの集計")):
        out.append(u"types: b の違うものの集計が行から数え直した値と違う")
    return out


def read_join(c):
    u"""読んだ行 [(組, 本の #, 文の番号, 位置, 型, 違うもの, 判定の行)]。"""
    sidx = state_index(c.S)
    return [tuple(r) + (sidx[(LABEL_SEC[r[0]], r[1], r[2], r[3])],) for r in c.R[u"行"]]


# ======================================================================================================
# f. 記録に書かないものが漏れていない(封の門の ``record_problems`` が見る欄・docID は重ねない。ここは葉の字)
def walk(x, acc=None):
    acc = [] if acc is None else acc
    if isinstance(x, dict):
        for k, v in x.items():
            acc.append(k)
            walk(v, acc)
    elif isinstance(x, list):
        for v in x:
            walk(v, acc)
    else:
        acc.append(x)
    return acc


def walk_keys(x, acc=None):
    acc = [] if acc is None else acc
    if isinstance(x, dict):
        for k, v in x.items():
            acc.append(k)
            walk_keys(v, acc)
    elif isinstance(x, list):
        for v in x:
            walk_keys(v, acc)
    return acc


def long_ok(seal):
    v_txt, g_txt = seal_type_texts(seal)
    s = set(SG.LIMITS_PINNED) | set(x for x in walk(dict(SG.CUT_RECORD_PINNED)) if isinstance(x, str)) | set(SG.JUDGE_RECORD_PINNED.values())
    s |= set(v_txt.values()) | set(g_txt.values()) | set(ROW_COLS)
    s |= set([TEN_KEY, TYPED_BY, TYPES_BLIND, POP_STEP, STATES_STEP, TYPES_STEP, MATERIAL_PLACE, RULE_V, RULE_G_DV, RULE_G_DRAW, u"封 §1 の 201 本"])
    return s


def clean_problems(c):
    u"""記録に文・値・会社名・証券コード・pointer の字・docID・TDnet の番号・監査法人の名が無い。門が自前で全部の key と葉を歩く(封に書いた 3 つの札の名前だけは別)。"""
    out = []
    ok = long_ok(c.seal)
    tags = set(SG.CUT_RECORD_PINNED[u"札の名前"].values())
    for name, rec in ((u"population", c.P), (u"states", c.S), (u"read_types", c.R)):
        if rec.get(u"key_leaks") != []:
            out.append(u"clean[%s]: key_leaks が空でない" % name)
        bad = sorted(set(k for k in walk_keys(rec) if isinstance(k, str) and k in SG.TS.RUN.FORBIDDEN_KEYS))
        if bad:
            out.append(u"clean[%s]: repo へ入れない欄がある: %s" % (name, u",".join(bad)))
        for k in walk_keys(rec):
            if isinstance(k, str) and len(k) > 60:
                out.append(u"clean[%s]: 長い欄の名前がある(文が欄の名前に入っていないか)" % name)
        for s in walk(rec):
            if s is None or isinstance(s, (bool, int, float)):
                continue
            if not isinstance(s, str):
                out.append(u"clean[%s]: 葉が文字・数・真偽・null のどれでもない" % name)
                continue
            if s in tags:
                continue                                    # 封に書いた 3 つの札の名前(切り出しの規則の字)
            if DOCID_RE.search(s) or TDNET_RE.search(s):
                out.append(u"clean[%s]: docID・TDnet の番号の形の字がある" % name)
            if POINTER_RE.search(s):
                out.append(u"clean[%s]: pointer・要素名の形の字がある" % name)
            if any(w in s for w in COMPANY_WORDS) or AUDITOR_RE.search(s):
                out.append(u"clean[%s]: 会社名・監査法人の名らしい字がある" % name)
            if len(s) >= LONG_JA and JA_RE.search(s) and s not in ok:
                out.append(u"clean[%s]: 留めた字に無い長い日本語の文がある" % name)
            if CODE_RE.search(s) and not HEX64.match(s) and not HEX40.match(s):
                out.append(u"clean[%s]: 証券コードの形の字がある(%s)" % (name, s[:12]))
    for b in c.S.get(u"本") or []:                          # 本の中の字は閉じた語彙(会社名・文が入る場所が無い)
        for sec in SECS:
            for k in (u"切り出し", u"理由"):
                v = b[sec].get(k)
                if v is not None and (not isinstance(v, str) or len(v) > 6):
                    out.append(u"clean[states]: 本の %s が短い語彙でない" % k)
            for r in b[sec][u"行"]:
                for x in (r[3], r[4], r[6]):
                    if x is not None and (not isinstance(x, str) or len(x) > 40):
                        out.append(u"clean[states]: 行の字が短い語彙でない")
    for r in (c.R.get(u"行") or []):
        if len(r) != 6 or any(isinstance(x, str) and len(x) > 6 for x in r):
            out.append(u"clean[read_types]: 行が短い語彙・数だけでない")
            break
    return out


# ======================================================================================================
# g. 結果の文書
def seal_problems(seal):
    out = []
    try:
        y = seal_y_rows(seal)
        lim = seal_limits(seal)
    except ValueError:
        return [u"封の節が揃っていない"]
    if list(y.keys()) != list(PRED_IDS):
        return [u"封 §3 が Y-1〜Y-13 の 13 行でない"]
    for yid, ph in BOUND_PHRASES.items():
        if ph not in y[yid][1]:
            out.append(u"封 %s の予測に幅の字が無い: %s" % (yid, ph))
    for yid, nums in ((u"Y-2", (80998, 39975, 110509)), (u"Y-3", (175, 85, 2, 43, 45, 124)), (u"Y-4", (509, 150, 6, 146, 207, 25)), (u"Y-5", (957, 31, 10, 418, 498, 42, 351))):
        for n in nums:
            if (fmt(n) if n >= 1000 else str(n)) not in y[yid][1]:
                out.append(u"封 %s に数 %d が無い" % (yid, n))
    try:
        if bound_of(y[u"Y-8"][1]) != (4, None) or bound_of(y[u"Y-7"][1]) != (0, 2) or bound_of(y[u"Y-12"][1]) != (0, 5):
            out.append(u"封 Y-7・Y-8・Y-12 の幅が字と違う")
    except ValueError:
        out.append(u"封の幅が読めない")
    if len(lim) != 11:
        out.append(u"封 §6 が 11 項でない")
    elif u"型分けは司令塔" not in lim[6] or u"G 研究・G 設備は 60 行の標本" not in lim[7] or u"甲の 67 本" not in lim[10]:
        out.append(u"封 §6 の 7・8・11 番目の字が違う")
    return out


def seal_frozen_problems(seal_text, root=REPO):
    u"""封が e7754d70 の commit のときの byte と同じか(1 字も変わっていない。未 commit の編集も見る)。"""
    rc, _ = PR.git_in(root, "cat-file", "-e", SEAL_COMMIT_SHORT + "^{commit}")
    if rc != 0:
        return [u"封の commit が履歴に無い"]
    r = subprocess.run(["git", "show", "%s:%s%s" % (SEAL_COMMIT_SHORT, PREFIX, SEAL_REL)], cwd=root, capture_output=True)
    if r.returncode != 0:
        return [u"封の commit に封の file が無い"]
    if r.stdout != seal_text.encode("utf-8"):
        return [u"封が %s のときの byte から変わっている" % SEAL_COMMIT_SHORT]
    return []


def bound_of(pred):
    u"""封 §3 の予測の字から幅(下, 上)を読む。「4 行以上」は (4, None)。"""
    m = re.search(r"(\d+)〜(\d+) 行", pred)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r"(\d+) 行以上", pred)
    if m:
        return int(m.group(1)), None
    raise ValueError(u"幅が読めない")


def in_bound(n, lo, hi):
    return n >= lo and (hi is None or n <= hi)


def position(n, lo, hi):
    if n < lo:
        return u"幅の外(下端まで %d 行)" % (lo - n)
    if hi is not None and n > hi:
        return u"幅の外(上端から %d 行上)" % (n - hi)
    if n == lo:
        return u"下端そのもの"
    if hi is not None and n == hi:
        return u"上端そのもの"
    return u"内(下端から %d 行上%s)" % (n - lo, u"・上端まで %d 行" % (hi - n) if hi is not None else u"")


def type_counts(c):
    return dict((lab, collections.Counter(r[4] for r in c.R[u"行"] if r[0] == lab)) for lab in LABELS)


def y_actuals(c):
    u"""Y-7〜Y-13 の実測の数(記録の読みの行から)。{id: 数}。"""
    cnt = type_counts(c)
    return collections.OrderedDict([
        (u"Y-7", sum(cnt[lab][u"ク"] for lab in V_LABELS)), (u"Y-8", cnt[u"V 配当"][u"ウ"]), (u"Y-9", cnt[u"V 設備"][u"ア"]),
        (u"Y-10", cnt[u"G 研究"][u"b"]), (u"Y-11", cnt[u"G 設備"][u"b"]), (u"Y-12", cnt[u"G 配当"][u"b"]),
        (u"Y-13", sum(cnt[lab][u"ケ"] for lab in V_LABELS) + sum(cnt[lab][u"c"] for lab in G_LABELS))])


def pred_table(c):
    u"""封 §3 の Y-1〜Y-13 を、記録から判定した行(id, 欄, 予測(封), 実測, 判定)の列にする。数は本の行から数え直す(states の集計の欄は見ない)。"""
    books = c.S[u"本"]
    cells = seal_y_rows(c.seal)
    w = dict((sec, recount_sec(books, sec)) for sec in SECS)
    cnt = type_counts(c)
    act = y_actuals(c)
    n_read = len(c.R[u"行"])
    rows = collections.OrderedDict()

    def hit(ok):
        return u"当たり" if ok else u"外れ"
    v1 = [(w[s][u"切れた"], w[s][u"切れない"]) for s in SECS]
    rows[u"Y-1"] = (u"、".join(u"%s 切れた %d・切れない %d" % (s, a, b) for s, (a, b) in zip(SECS, v1)), hit(v1 == [(201, 0)] * 3))
    v2 = tuple(w[s][u"字数の合計"] for s in SECS)
    rows[u"Y-2"] = (u"%s %s・%s %s・%s %s" % (RD, fmt(v2[0]), EQ, fmt(v2[1]), DV, fmt(v2[2])), hit(v2 == (80998, 39975, 110509)))

    for yid, sec in ((u"Y-3", RD), (u"Y-4", EQ), (u"Y-5", DV)):
        s4 = w[sec][u"4 state"]
        v = (w[sec][u"claim"], s4[G], s4[VM], s4[UNV], s4[PNF])
        z = w[sec][u"切れた本のうち claim が 0 の本"]
        actual = u"%s = %s / %s / %s / %s。claim が 0 の本 %d" % ((fmt(v[0]),) + tuple(fmt(x) for x in v[1:]) + (z,))
        ok = v == tuple(SG.SIX_TOTALS[sec][2:]) and z == SG.ZERO_CLAIM_BOOKS[sec]
        if yid == u"Y-5":
            pu = w[sec][u"reason"][UNV].get(PER_UNIT, 0)
            actual += u"。`%s` %d 行" % (PER_UNIT, pu)
            ok = ok and pu == PER_UNIT_SEALED
        rows[yid] = (actual, hit(ok))
    rows[u"Y-6"] = (Y6_ACTUAL, Y6_JUDGE)
    n_v = sum(sum(cnt[lab].values()) for lab in V_LABELS)
    rows[u"Y-7"] = (u"V の全部 %d 行のうち (ク) %d 行" % (n_v, act[u"Y-7"]), hit(in_bound(act[u"Y-7"], *bound_of(cells[u"Y-7"][1]))))
    rows[u"Y-8"] = (u"V 配当 %d 行のうち (ウ) %d 行" % (sum(cnt[u"V 配当"].values()), act[u"Y-8"]), hit(in_bound(act[u"Y-8"], *bound_of(cells[u"Y-8"][1]))))
    rows[u"Y-9"] = (u"V 設備 %d 行のうち (ア) %d 行" % (sum(cnt[u"V 設備"].values()), act[u"Y-9"]), hit(in_bound(act[u"Y-9"], *bound_of(cells[u"Y-9"][1]))))
    rows[u"Y-10"] = (u"G 研究 %d 行のうち (b) %d 行" % (sum(cnt[u"G 研究"].values()), act[u"Y-10"]), hit(in_bound(act[u"Y-10"], *bound_of(cells[u"Y-10"][1]))))
    rows[u"Y-11"] = (u"G 設備 %d 行のうち (b) %d 行" % (sum(cnt[u"G 設備"].values()), act[u"Y-11"]), hit(in_bound(act[u"Y-11"], *bound_of(cells[u"Y-11"][1]))))
    rows[u"Y-12"] = (u"G 配当 %d 行のうち (b) %d 行" % (sum(cnt[u"G 配当"].values()), act[u"Y-12"]), hit(in_bound(act[u"Y-12"], *bound_of(cells[u"Y-12"][1]))))
    rows[u"Y-13"] = (u"読んだ %d 行のうち (ケ) + (c) %d 行" % (n_read, act[u"Y-13"]), hit(in_bound(act[u"Y-13"], *bound_of(cells[u"Y-13"][1]))))
    return [(yid, cells[yid][0], cells[yid][1], rows[yid][0], rows[yid][1]) for yid in PRED_IDS]


def _sep(n):
    return u"|" + u"---|" * n


def sec_block(c, sec):
    books = c.S[u"本"]
    lines = [u"| 群 | 本 | 切れた | 切れない | 字数の合計 | 数の claim | GROUNDED | VALUE_MISMATCH | UNVERIFIABLE | POINTER_NOT_FOUND | GROUNDED / claim | UNVERIFIABLE / claim | "
             u"POINTER_NOT_FOUND / claim | claim が 0 の本 | GROUNDED が 0 の本 | VALUE_MISMATCH が 1 以上の本 |", _sep(16)]
    for g in GROUPS + (None,):
        w = recount_sec(books, sec, g)
        s = w[u"4 state"]
        lines.append(u"| %s | %s |" % (g or u"**計**", u" | ".join([
            fmt(w[u"本"]), fmt(w[u"切れた"]), fmt(w[u"切れない"]), fmt(w[u"字数の合計"]), fmt(w[u"claim"]),
            fmt(s[G]), fmt(s[VM]), fmt(s[UNV]), fmt(s[PNF]), pct(s[G], w[u"claim"]), pct(s[UNV], w[u"claim"]), pct(s[PNF], w[u"claim"]),
            fmt(w[u"切れた本のうち claim が 0 の本"]), fmt(w[u"切れた本のうち GROUNDED が 0 の本"]), fmt(w[u"VALUE_MISMATCH が 1 以上の本"])])))
    return lines


def width_lines(c):
    u"""Y-7〜Y-13 の実測が封の幅のどこに在ったか(幅は封の字から・実測は記録から)。"""
    cells = seal_y_rows(c.seal)
    lines = [u"| # | 封の幅 | 実測 = 幅の中の位置 |", _sep(3)]
    for yid, n in y_actuals(c).items():
        lo, hi = bound_of(cells[yid][1])
        wtxt = u"%d〜%d 行" % (lo, hi) if hi is not None else u"%d 行以上" % lo
        lines.append(u"| %s | %s | %d 行 = %s |" % (yid, wtxt, n, position(n, lo, hi)))
    return lines


def cross_keys(lab):
    u"""読みの組の型の並び [(型, 違うもの or None, 文書の字)]。"""
    if lab.startswith(u"V"):
        return [(t, None, u"(%s)" % t) for t in V_TYPES]
    return [(u"a", None, u"(a)")] + [(u"b", d, u"(b)・%s" % d) for d in DIFFS] + [(u"c", None, u"(c)")]


def rows_type_text(r):
    return u"(%s)" % r[4] if r[5] is None else u"(%s)・%s" % (r[4], r[5])


def build_blocks(c):
    S, R = c.S, c.R
    books = S[u"本"]
    blocks = collections.OrderedDict()
    lines = [u"| # | 欄 | 予測(封) | 実測 | 判定 |", _sep(5)]
    for r in pred_table(c):
        lines.append(u"| %s | %s | %s | %s | %s |" % r)
    blocks[u"pred"] = lines
    blocks[u"width"] = width_lines(c)
    blocks[u"sec_rd"] = sec_block(c, RD)
    blocks[u"sec_capex"] = sec_block(c, EQ)
    blocks[u"sec_div"] = sec_block(c, DV)
    lines = [u"| 節 | 群 | GROUNDED 真 | GROUNDED 偽 | VALUE_MISMATCH 真 | VALUE_MISMATCH 偽 | UNVERIFIABLE 真 | UNVERIFIABLE 偽 | POINTER_NOT_FOUND 真 | POINTER_NOT_FOUND 偽 |", _sep(10)]
    for sec in SECS:
        for g in GROUPS + (None,):
            t = recount_sec(books, sec, g)[TEN_KEY]
            lines.append(u"| %s | %s | %s |" % (sec, g or u"**計**", u" | ".join(fmt(t[s][v]) for s in STATES for v in (TRUE, FALSE))))
    blocks[u"ten"] = lines
    w = dict((sec, recount_sec(books, sec)) for sec in SECS)
    lines = [u"| state | reason | 研究開発活動(計) | 設備投資等の概要(計) | 配当政策(計) |", _sep(5)]
    for s in (UNV, PNF):
        for k in sorted(set(k for sec in SECS for k in w[sec][u"reason"][s])):
            lines.append(u"| %s | %s | %s |" % (s, k, u" | ".join(fmt(w[sec][u"reason"][s].get(k, 0)) for sec in SECS)))
    blocks[u"reasons"] = lines
    lines = [u"| 欄 | 研究開発活動 VALUE_MISMATCH | 設備投資等の概要 VALUE_MISMATCH | 配当政策 VALUE_MISMATCH | 研究開発活動 GROUNDED | 設備投資等の概要 GROUNDED | 配当政策 GROUNDED |", _sep(7)]
    cols = [mech_rows(books, sec, st) for st in (VM, G) for sec in SECS]
    mech = [(u"行", lambda rs: len(rs)), (u"導出(formula)", lambda rs: sum(1 for r in rs if r[5])), (u"直接", lambda rs: sum(1 for r in rs if not r[5])),
            (u"span に % を含む", lambda rs: sum(1 for r in rs if r[8])), (u"両期の fact を引く a−b", lambda rs: sum(1 for r in rs if r[7])),
            (u"単位の族が %", lambda rs: sum(1 for r in rs if r[6] == u"%")), (u"単位の族が円族", lambda rs: sum(1 for r in rs if r[6] == u"円族")),
            (u"単位の族が他", lambda rs: sum(1 for r in rs if r[6] == u"他"))]
    mech += [(u"pointer の期 %s" % k, (lambda k: lambda rs: sum(1 for r in rs if (r[4] == k if k in PERIODS + (u"なし",) else (r[4] not in PERIODS and r[4] != u"なし"))))(k)) for k in VM_PERIOD_KEYS]
    for name, fn in mech:
        lines.append(u"| %s | %s |" % (name, u" | ".join(fmt(fn(rs)) for rs in cols)))
    blocks[u"mech"] = lines
    exp, mother = expected_reading(S)
    lines = [u"| 読みの組 | 引き方 | 母の行 | 読んだ行 |", _sep(4)]
    for lab in LABELS:
        sec = LABEL_SEC[lab]
        if lab.startswith(u"V"):
            how = u"%sの VALUE_MISMATCH の全部" % sec
        elif lab == u"G 配当":
            how = u"%sの GROUNDED の全部" % sec
        else:
            how = u"%sの GROUNDED から種 `%d` で %d 行を引く" % (sec, SEED, DRAW_N)
        lines.append(u"| %s | %s | %s | %s |" % (lab, how, fmt(mother[lab]), fmt(len(exp[lab]))))
    lines.append(u"| **計** | | | %s |" % fmt(sum(len(v) for v in exp.values())))
    blocks[u"read"] = lines
    tt = R[u"型の字"]
    cnt = type_counts(c)
    nv = dict((lab, sum(cnt[lab].values())) for lab in LABELS)
    lines = [u"| 型 | 封の字 | V 研究 | V 設備 | V 配当 | V の計 |", _sep(6)]
    for t in V_TYPES:
        lines.append(u"| (%s) | %s | %s | %s |" % (t, tt[u"V"][t], u" | ".join(fmt(cnt[lab][t]) for lab in V_LABELS), fmt(sum(cnt[lab][t] for lab in V_LABELS))))
    lines.append(u"| **計** | | %s | %s |" % (u" | ".join(fmt(nv[lab]) for lab in V_LABELS), fmt(sum(nv[lab] for lab in V_LABELS))))
    blocks[u"types_v"] = lines
    lines = [u"| 型 | 封の字 | G 研究 | G 設備 | G 配当 | G 研究の読んだ行のうち | G 設備の読んだ行のうち | G 配当の読んだ行のうち |", _sep(8)]
    for t in G_TYPES:
        lines.append(u"| (%s) | %s | %s | %s |" % (t, tt[u"G"][t], u" | ".join(fmt(cnt[lab][t]) for lab in G_LABELS), u" | ".join(pct(cnt[lab][t], nv[lab]) for lab in G_LABELS)))
    lines.append(u"| **計** | | %s | | | |" % u" | ".join(fmt(nv[lab]) for lab in G_LABELS))
    blocks[u"types_g"] = lines
    lines = [u"| (b) の違うもの | G 研究 | G 設備 | G 配当 |", _sep(4)]
    for d in DIFFS:
        lines.append(u"| %s | %s |" % (d, u" | ".join(fmt(sum(1 for r in R[u"行"] if r[0] == lab and r[4] == u"b" and r[5] == d)) for lab in G_LABELS)))
    blocks[u"types_b"] = lines
    j = read_join(c)
    lines = [u"| 読みの組 | 型 | 行 | 10 欄目が真 | 10 欄目が偽 | 結んだ先が導出の行 | pointer の期が前期の行 | pointer の期が他の行 |", _sep(8)]
    for lab in LABELS:
        for t, d, txt in cross_keys(lab):
            sel = [r for r in j if r[0] == lab and r[4] == t and (d is None or r[5] == d)]
            if sel:
                lines.append(u"| %s | %s | %s | %s | %s | %s | %s | %s |" % (lab, txt, fmt(len(sel)), fmt(sum(1 for r in sel if r[6][9] is True)), fmt(sum(1 for r in sel if r[6][9] is False)),
                                                                            fmt(sum(1 for r in sel if r[6][5] is True)), fmt(sum(1 for r in sel if r[6][4] == u"Prior1Year")),
                                                                            fmt(sum(1 for r in sel if r[6][4] not in (u"CurrentYear", u"Prior1Year")))))
    blocks[u"cross"] = lines
    head = u"| 読みの組 | 通し番号 | 本の # | 文の番号 | 位置 | 型 |"
    lines = [head, _sep(6)]
    for lab in V_LABELS:
        for k, r in enumerate([r for r in R[u"行"] if r[0] == lab], 1):
            lines.append(u"| %s | %d | %d | %d | %d | %s |" % (lab, k, r[1], r[2], r[3], rows_type_text(r)))
    blocks[u"rows_v"] = lines
    lines = [head, _sep(6)]
    for lab in G_LABELS:
        for k, r in enumerate([r for r in R[u"行"] if r[0] == lab], 1):
            if r[4] != u"a":
                lines.append(u"| %s | %d | %d | %d | %d | %s |" % (lab, k, r[1], r[2], r[3], rows_type_text(r)))
    blocks[u"rows_g"] = lines
    lines = [u"| 記録 | sha256 |", _sep(2)]
    for rel in RECORD_RELS:
        lines.append(u"| `%s` | `%s` |" % (rel, hashlib.sha256(c.texts[rel]).hexdigest()))
    blocks[u"sha"] = lines
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
    t = t.replace(u"sha256", u"")                                    # 名前の中の 256
    t = re.sub(r"\d{4}-\d{2}-\d{2}", u"", t)
    t = re.sub(r"\b[0-9a-f]{7,}\b", u"", t)
    t = re.sub(r"https?://\S+|\S+\.(?:md|py|json)\b", u"", t)
    t = re.sub(r"\b[A-Z]+-?\d+[A-Z]*\b", u"", t)                      # Y-10・P33E などの名前
    t = re.sub(u"§[0-9\\-]+", u"", t)
    return t


def derived_numbers(seal):
    u"""記録の塊に出ない数のうち、封の字から作れるもの(封 §6 の 11 項に出る数)。"""
    out = set()
    for ln in seal_limits(seal):
        out |= numbers_of(ln)
    return out


def prose_number_problems(doc, blocks, seal):
    u"""塊の外の散文の 2 桁以上の数は、記録から作った塊の中の数か、封 §6 の字に在る数。"""
    allowed = set()
    for name, lines in blocks.items():
        if name not in NO_NUMBER_BLOCKS:
            allowed |= numbers_of(u"\n".join(lines))
    allowed |= derived_numbers(seal)
    out = []
    for ln, line in enumerate(outside_blocks(doc).splitlines(), 1):
        bad = sorted(numbers_of(prose_clean(line)) - allowed)
        if bad:
            out.append(u"散文の数が記録から作った数の集合に無い: 行 %d %s" % (ln, u",".join(bad)))
        if KANJI_NUM_RE.search(line):
            out.append(u"散文が 3 桁以上の数を漢数字で書いている: 行 %d" % ln)
    return out


def doc_problems(c):
    doc = c.doc
    out = []
    names = re.findall(r"<!-- 門:start (\w+) -->", doc)
    if names != list(BLOCK_NAMES) or doc.count(u"<!-- 門:end -->") != len(BLOCK_NAMES):
        out.append(u"文書: 塊の名前・数が 16 個(%s)の順でない" % u"・".join(BLOCK_NAMES))
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
    for w in COMPANY_WORDS:
        if w in doc:
            out.append(u"文書: 会社名らしい字 %s" % w)
    if AUDITOR_RE.search(doc):
        out.append(u"文書: 監査法人の名らしい字")
    if POINTER_RE.search(doc):
        out.append(u"文書: pointer・要素名の形の字がある")
    out += prose_number_problems(doc, want, c.seal)
    for need in (os.path.basename(SEAL_REL), SEAL_COMMIT_SHORT, SCRIPT_COMMIT, os.path.basename(GATE_REL), os.path.basename(SEAL_GATE_REL), os.path.basename(SCRIPT_REL)) \
            + tuple(os.path.basename(r) for r in RECORD_RELS) + REQUIRED_PHRASES:
        if need not in doc:
            out.append(u"文書: %s を言っていない" % need)
    for i, ln in enumerate(seal_limits(c.seal), 1):
        if u"封 §6-%d: %s" % (i, ln) not in doc:
            out.append(u"文書: 封 §6 の %d 番目の字を「封 §6-%d:」で写していない" % (i, i))
    if u"AUDIT_CORE_YS_REMEASURE=1" not in doc:
        out.append(u"文書: 測り直しの環境変数を言っていない")
    out += fragment_problems(c)
    return out


DOC_SECS = collections.OrderedDict([(u"s0", (u"## §0", u"## §1")), (u"s1", (u"## §1", u"## §2")), (u"s2", (u"## §2", u"## §3")), (u"s3", (u"## §3", u"## §4")), (u"s4", (u"## §4", u"## §5")),
                                    (u"s5", (u"## §5", u"## §6")), (u"s6", (u"## §6", u"## §7"))])
STALE_PHRASES = (u"KAM の便で (エ)", u"外れは 0 行", u"理由は記録に無く")
NOT_CALLED_RE = re.compile(u"\\(ク\\)[^。\n]{0,8}(?:は|が|を|=|＝) *「?食い違い")


def section_of(doc, key):
    a, b = DOC_SECS[key]
    return doc[doc.index(a):doc.index(b)] if a in doc and b in doc else u""


def prose_fragments(c):
    u"""本文の中の数を持つ文の断片(節 → 断片)。数は記録の行から数え直した値で作る。字と数の両方が合わなければ赤。"""
    books = c.S[u"本"]
    w = dict((sec, recount_sec(books, sec)) for sec in SECS)
    wr, we, wd = (w[s] for s in SECS)
    cnt = type_counts(c)
    j = read_join(c)
    exp, mother = expected_reading(c.S)
    preds = pred_table(c)
    act = y_actuals(c)
    cells = seal_y_rows(c.seal)
    real = [r for r in preds if r[0] not in (u"Y-1", u"Y-2", u"Y-3", u"Y-4", u"Y-5")]
    n_hit = sum(1 for r in real if r[4].startswith(u"当たり"))
    miss = [r[0] for r in real if r[4].startswith(u"外れ")]
    gd = [r for r in j if r[0] == u"G 配当"]
    gd_b_range = [r for r in gd if r[4] == u"b" and r[5] == u"範囲"]
    not_cur = sum(1 for r in gd_b_range if r[6][4] != u"CurrentYear")
    prior1 = sum(1 for r in gd_b_range if r[6][4] == u"Prior1Year")
    vd_i = [r for r in j if r[0] == u"V 配当" and r[4] == u"イ"]
    n_vm = sum(w[s][u"4 state"][VM] for s in SECS)
    used = [t for t in V_TYPES if sum(cnt[lab][t] for lab in V_LABELS) > 0]
    n_vd, n_gd = sum(cnt[u"V 配当"].values()), sum(cnt[u"G 配当"].values())
    n_gr, n_ge = sum(cnt[u"G 研究"].values()), sum(cnt[u"G 設備"].values())
    sg = lambda s, k: w[s][u"4 state"][k]
    lo9 = bound_of(cells[u"Y-9"][1])[0]
    hi10 = bound_of(cells[u"Y-10"][1])[1]
    under3 = [s for s in SECS if 10.0 * sg(s, G) < 3.0 * w[s][u"claim"]]
    a_share = (cnt[u"G 研究"][u"a"] + cnt[u"G 設備"][u"a"]) / float(n_gr + n_ge)
    f = collections.OrderedDict((k, []) for k in DOC_SECS)
    f[u"s1"] += [u"本当の予測 %d 本のうち、当たり %d・**外れ %d(%s)**。" % (len(real), n_hit, len(miss), u"・".join(miss)),
                 u"読んだ %d 行のうち %d 行は、文が目標・目安の率を言い、engine が実績の率と比べた行((イ))" % (n_vd, len(vd_i)),
                 u"読んだ %d 行(全部)のうち %d 行が、値は同じだが項目か範囲が結んだ fact と違う行((b))" % (n_gd, act[u"Y-12"]),
                 u"Y-9 は下端そのもので、余裕は %d 行だった。" % (act[u"Y-9"] - lo9),
                 u"**Y-12 は (b) の多いほうへ外れた = 3 回目。**",
                 u"Y-10 の %d 行は、(b)・範囲 に当たりうる行を (c) に入れた決め(§4)の上の数。文 1 つだけではどの事業か読めない %d 行を (c) にした。%d 行の全部を (b) と読んでも Y-10 は外れ方(%d 行以上)に入る" % (
                     act[u"Y-10"], cnt[u"G 研究"][u"c"], cnt[u"G 研究"][u"c"], hi10 + 1)]
    f[u"s2"] += [u"数の claim は %s、結べた(GROUNDED)は %s(%s)。ただし claim が 0 の本が %d(%d 本のうち)で、数は残りの本に集まる。GROUNDED が 0 の本は %d。" % (
                     fmt(wr[u"claim"]), fmt(sg(RD, G)), pct(sg(RD, G), wr[u"claim"]), wr[u"切れた本のうち claim が 0 の本"], wr[u"本"], wr[u"切れた本のうち GROUNDED が 0 の本"]),
                 u"数の claim は %s、結べたのは %s(%s)で 3 割に届かない。いちばん多い state は POINTER_NOT_FOUND の %s(%s)。GROUNDED が 0 の本は %d。" % (
                     fmt(we[u"claim"]), fmt(sg(EQ, G)), pct(sg(EQ, G), we[u"claim"]), fmt(sg(EQ, PNF)), pct(sg(EQ, PNF), we[u"claim"]), we[u"切れた本のうち GROUNDED が 0 の本"]),
                 u"数の claim は %s、結べたのは %s(%s)。GROUNDED が 0 の本は %d(%d 本のうち)。止まった(UNVERIFIABLE)%s のうち %d が reason `%s`" % (
                     fmt(wd[u"claim"]), fmt(sg(DV, G)), pct(sg(DV, G), wd[u"claim"]), wd[u"切れた本のうち GROUNDED が 0 の本"], wd[u"本"], fmt(sg(DV, UNV)), wd[u"reason"][UNV][PER_UNIT], PER_UNIT),
                 u"配当政策の GROUNDED %d 行は全部が真" % wd[TEN_KEY][G][TRUE],
                 u"「値が違う」は 3 つの節で %s。全部が直接(導出は %d)で、結んだ先の期は全部が当期。" % (u"・".join(u"%d 行" % sg(s, VM) for s in SECS), sum(w[s][u"VALUE_MISMATCH の内訳"][u"導出(formula)"] for s in SECS))]
    f[u"s3"] += [u"(ク) 本当の差の候補は %d 行。使われた型は %s の %d つだけ。" % (act[u"Y-7"], u"・".join(u"(%s)" % t for t in used), len(used)),
                 u"**配当政策の「結べた」%d 行のうち、(a) と読めたのは %d 行(%s)で、%d 行(%s)は値が同じだけ**(違うものは範囲 %d・項目 %d)。研究開発活動は読んだ %d 行のうち (a) %d・(c) %d、設備投資等の概要は (a) %d・(b) %d。" % (
                     n_gd, cnt[u"G 配当"][u"a"], pct(cnt[u"G 配当"][u"a"], n_gd), cnt[u"G 配当"][u"b"], pct(cnt[u"G 配当"][u"b"], n_gd),
                     len(gd_b_range), sum(1 for r in gd if r[4] == u"b" and r[5] == u"項目"), n_gr, cnt[u"G 研究"][u"a"], cnt[u"G 研究"][u"c"], cnt[u"G 設備"][u"a"], cnt[u"G 設備"][u"b"]),
                 u"G 配当の (b)・範囲 の %d 行のうち、結んだ先の期が当期でない行が %d 行(前期 %d・他 %d)。" % (len(gd_b_range), not_cur, prior1, not_cur - prior1),
                 u"V 配当の (イ) の %d 行は全部 10 欄目が%s。" % (len(vd_i), u"真" if all(r[6][9] is True for r in vd_i) else u"?")]
    f[u"s4"] += [u"(ウ)・(エ)・(カ)・(キ)・(ク)・(ケ) は %d 行。" % sum(cnt[lab][t] for lab in V_LABELS for t in u"ウエカキクケ")]
    f[u"s5"] += [u"**結べた(GROUNDED)が claim の 3 割に届かない節が %d つ**(%s。§2-2・§2-3)。研究開発活動は %s だが、claim が 0 の本が %d(%d 本のうち)。" % (
                     len(under3), u"・".join(u"%s %s" % (s, pct(sg(s, G), w[s][u"claim"])) for s in under3), pct(sg(RD, G), wr[u"claim"]), wr[u"切れた本のうち claim が 0 の本"], wr[u"本"]),
                 u"止まった %d のうち %d が `%s`" % (sg(DV, UNV), wd[u"reason"][UNV][PER_UNIT], PER_UNIT),
                 u"結べた %d 行も、読むと %d 行(%s)は値が同じだけ" % (n_gd, cnt[u"G 配当"][u"b"], pct(cnt[u"G 配当"][u"b"], n_gd)),
                 u"(a) と読めたのは %d 行 = claim %d のうちの数として読む" % (cnt[u"G 配当"][u"a"], wd[u"claim"]),
                 u"同じ向きに 3 回目の外れ",
                 u"V の行に本当の差の候補 (ク) は %d 行 = この便は" % act[u"Y-7"],
                 u"「値が違う」%d 行は全部" % n_vm, u"この 3 つの節では %d 行のうち %d 行が偽の警報" % (n_vm, n_vm - act[u"Y-7"]),
                 u"**G 研究・G 設備は 60 行ずつの標本**(%d 行・%d 行のうち)" % (mother[u"G 研究"], mother[u"G 設備"])]
    f[u"s6"] += [u"採用 / 不採用の判定は無い", u"人間が決める", u"読んだ「結べた」の %d 割ほどを (a) と読めた(§3-3)" % int(round(a_share * 10))]
    return f


def fragment_problems(c):
    doc = c.doc
    out = []
    for key, frs in prose_fragments(c).items():
        sec = section_of(doc, key)
        if not sec:
            out.append(u"文書: 節 %s が無い" % key)
            continue
        for fr in frs:
            if fr not in sec:
                out.append(u"文書: 節 %s に、記録から作った文の断片が無い: %s" % (key, fr[:30]))
    for ph in STALE_PHRASES:
        if ph in doc:
            out.append(u"文書: 古い字が残っている: %s" % ph)
    if NOT_CALLED_RE.search(doc):
        out.append(u"文書: (ク) を食い違いと呼んでいる")
    if u"採用" in doc.replace(u"採用 / 不採用の判定は無い", u""):
        out.append(u"文書: 採用の字が「採用 / 不採用の判定は無い」の外にある")
    return out


# ======================================================================================================
# h. 順序・engine
def order_others():
    return list(RECORD_RELS) + [DOC_REL, GATE_REL]


def order_problems_real(root=REPO):
    return PR.order_problems(root, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, [SCRIPT_REL], order_others())


def engine_problems(root=REPO):
    u"""engine・lib・仕掛け・前の便は封の commit から 0 行(作業木と index の未 commit も)。script は足した commit(3b9c54bc)から 0 行(未 commit の編集も見る)。"""
    out = list(SG.engine_since_seal_problems(root)) + list(SG.engine_worktree_problems(root))
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
    (u"keys", keys_problems),
    (u"pop", population_problems),
    (u"states", states_problems),
    (u"types", types_problems),
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


def bump(d, k, n=1):
    d[k] = d[k] + n


def book(c, n):
    return [b for b in c.S[u"本"] if b[u"#"] == n][0]


def first_row(c, sec, pred):
    for b in c.S[u"本"]:
        for r in b[sec][u"行"]:
            if pred(r):
                return b, r
    raise AssertionError(u"該当する行が無い")


def types_row(c, lab, pred=lambda r: True):
    return [r for r in c.R[u"行"] if r[0] == lab and pred(r)][0]


def doc_digit(c, name):
    u"""塊 ``name`` の 2 行目より下の最初の「数の字」(1 つ目の欄は読まない。sha の塊は 16 進の最初の 1 字)を別の字に替える。"""
    lines = doc_blocks(c.doc)[name]
    pat = re.compile(r"[0-9a-f]" if name == u"sha" else r"[1-9]")
    for i, ln in enumerate(lines):
        if i < 2:
            continue
        cell2 = ln.index(u"|", 2) + 1 if name != u"sha" else ln.index(u"|", 2) + 3
        m = pat.search(ln, cell2)
        if m:
            idx = c.doc.index(u"\n".join(lines))
            off = idx + len(u"\n".join(lines[:i])) + 1 + m.start()
            ch = c.doc[off]
            c.doc = c.doc[:off] + (u"7" if ch != u"7" else u"8") + c.doc[off + 1:]
            return
    raise AssertionError(name)


def doc_replace(old, new):
    def fn(c):
        assert old in c.doc, old
        c.doc = c.doc.replace(old, new, 1)
    return fn


def doc_sub(pattern, new, flags=0):
    def fn(c):
        out, n = re.subn(pattern, new, c.doc, count=1, flags=flags)
        assert n == 1, pattern
        c.doc = out
    return fn


def seal_replace(old, new):
    def fn(c):
        assert old in c.seal, old
        c.seal = c.seal.replace(old, new, 1)
    return fn


def set_texts(rel, fn):
    return lambda c: c.texts.__setitem__(rel, fn(c.texts[rel]))


def doc_append(text):
    return lambda c: setattr(c, "doc", c.doc + text)


# a. sha
M(u"a1 母集団の記録の 1 byte", u"sha", set_texts(POP_REL, lambda t: t + b" "))
M(u"a2 判定の記録の 1 byte", u"sha", set_texts(STATES_REL, lambda t: t[:-2] + b" \n"))
M(u"a3 読みの記録の 1 byte", u"sha", set_texts(TYPES_REL, lambda t: b"x" + t))
M(u"a4 script の 1 byte", u"sha", set_texts(SCRIPT_REL, lambda t: t + b"#"))
# b. 来歴
M(u"b1 states の「この script の sha256」", u"prov", lambda c: c.S.__setitem__(u"この script の sha256", flip(c.S[u"この script の sha256"])))
M(u"b2 population の「この script の sha256」", u"prov", lambda c: c.P.__setitem__(u"この script の sha256", flip(c.P[u"この script の sha256"])))
M(u"b3 read_types の「states の記録の sha256」", u"prov", lambda c: c.R.__setitem__(u"states の記録の sha256", flip(c.R[u"states の記録の sha256"])))
M(u"b4 states の「封の表の sha256」", u"prov", lambda c: c.S.__setitem__(u"封の表の sha256", flip(c.S[u"封の表の sha256"])))
M(u"b5 population の「母集団の表の sha256」", u"prov", lambda c: c.P.__setitem__(u"母集団の表(# TAB 群 TAB sha256 の行)の sha256", flip(c.P[u"母集団の表(# TAB 群 TAB sha256 の行)の sha256"])))
M(u"b6 states の「TSS の script の sha256」", u"prov", lambda c: c.S.__setitem__(u"TSS の script の sha256", flip(c.S[u"TSS の script の sha256"])))
M(u"b7 states の「2026-11-09 の便の script の sha256」", u"prov", lambda c: c.S.__setitem__(u"2026-11-09 の便の script の sha256", flip(c.S[u"2026-11-09 の便の script の sha256"])))
M(u"b8 engine の指紋", u"prov", lambda c: c.S[u"engine の指紋"].__setitem__(u"adapter_xbrl_py_sha256", flip(c.S[u"engine の指紋"][u"adapter_xbrl_py_sha256"])))
M(u"b9 HEAD の commit が祖先でない 40 桁", u"prov", lambda c: c.R.__setitem__(u"HEAD の commit", u"0" * 40))
M(u"b10 型を付けた席", u"prov", lambda c: c.R.__setitem__(u"型を付けた席", u"人の確認"))
M(u"b11 盲検の欄", u"prov", lambda c: c.R.__setitem__(u"盲検", u"盲検"))
M(u"b12 profile", u"prov", lambda c: c.S.__setitem__(u"profile", u"P32E"))
M(u"b13 step の字", u"prov", lambda c: c.P.__setitem__(u"step", u"YS"))
M(u"b14 欄が 1 つ増える", u"prov", lambda c: c.R.__setitem__(u"余分", 1))
M(u"b15 封の commit の欄", u"prov", lambda c: c.S.__setitem__(u"封の commit", u"e56d6782"))
M(u"b16 材料の前後が違う", u"prov", lambda c: c.S[u"材料"][u"3 つの folder の一覧の前後(件数・名前の sha256)"].__setitem__(u"変化なし", False))
M(u"b17 材料の一致した ZIP", u"prov", lambda c: c.P[u"材料"].__setitem__(u"表と一致した ZIP", 200))
M(u"b18 時間(秒)が数でない", u"prov", lambda c: c.S.__setitem__(u"時間(秒)", u"74.5"))
M(u"b19 今の script が変わった(実 file 側)", u"prov", lambda c: c.cur.__setitem__("script", flip(c.cur["script"])))
M(u"b20 今の states の記録が変わった(実 file 側)", u"prov", lambda c: c.cur.__setitem__("states", flip(c.cur["states"])))
M(u"b21 今の封が変わった(実 file 側)", u"prov", lambda c: c.cur.__setitem__("seal", flip(c.cur["seal"])))
M(u"b22 限界の字", u"prov", lambda c: c.S[u"限界"].pop())
M(u"b23 切り出しの欄の字", u"prov", lambda c: c.S[u"切り出し"].__setitem__(u"NFKC", False))
M(u"b24 判定の欄の字", u"prov", lambda c: c.S[u"判定"].__setitem__(u"10 欄目", u"x"))
M(u"b25 行の欄", u"prov", lambda c: c.S[u"行の欄"].pop())
M(u"b26 読みの記録の行の欄", u"prov", lambda c: c.R[u"行の欄"].reverse())
M(u"b27 population の key_leaks", u"prov", lambda c: c.P.__setitem__(u"key_leaks", [u"x"]))
M(u"b28 states の「KAM の script の sha256」", u"prov", lambda c: c.S.__setitem__(u"KAM の script の sha256", flip(c.S[u"KAM の script の sha256"])))
# c. 母集団・# の集合
M(u"c1 母集団の行を 1 つ消す", u"pop", lambda c: c.P[u"行"].pop())
M(u"c2 母集団の行の入れ替え", u"pop", lambda c: c.P[u"行"].insert(0, c.P[u"行"].pop(1)))
M(u"c3 母集団の sha256", u"pop", lambda c: c.P[u"行"][5].__setitem__(2, flip(c.P[u"行"][5][2])))
M(u"c4 母集団の byte 数", u"pop", lambda c: c.P[u"行"][5].__setitem__(3, c.P[u"行"][5][3] + 1))
M(u"c5 母集団の群の欄", u"pop", lambda c: c.P[u"行"][5].__setitem__(1, u"乙"))
M(u"c6 byte 数の合計", u"pop", lambda c: bump(c.P, u"byte 数の合計"))
M(u"c7 群の本の数", u"pop", lambda c: c.P[u"群"].__setitem__(u"丙", 93))
M(u"c8 母集団の行の欄", u"pop", lambda c: c.P[u"行の欄"].reverse())
M(u"c9 byte 数が 0", u"pop", lambda c: c.P[u"行"][5].__setitem__(3, 0))
M(u"c10 母集団の # が 1 つ違う(# の集合)", u"keys", lambda c: c.P[u"行"][5].__setitem__(0, 999))
M(u"c11 states の # が 1 つ違う(# の集合)", u"keys", lambda c: book(c, 60).__setitem__(u"#", 999))
M(u"c12 読みの記録の本の # が states に無い", u"keys", lambda c: c.R[u"行"][0].__setitem__(1, 999))
M(u"c13 states の本が 1 本足りない(# の集合)", u"keys", lambda c: c.S[u"本"].pop())
# d. 判定の記録
M(u"d1 集計の研究計の GROUNDED", u"states", lambda c: bump(c.S[u"集計"][RD][u"計"][u"4 state"], G))
M(u"d2 集計の配当計の claim", u"states", lambda c: bump(c.S[u"集計"][DV][u"計"], u"claim", -1))
M(u"d3 ある行の state を GROUNDED から VALUE_MISMATCH に変える(reason は None のまま)", u"states", lambda c: first_row(c, RD, lambda r: r[2] == G)[1].__setitem__(2, VM))
M(u"d4 行を 1 つ消す(claim も 1 減らす)", u"states", lambda c: (lambda b: (b[EQ][u"行"].pop(0), bump(b[EQ], u"claim", -1)))(first_row(c, EQ, lambda r: True)[0]))
M(u"d5 reason の内訳を 1 つ動かす", u"states", lambda c: bump(c.S[u"集計"][DV][u"計"][u"reason"][UNV], PER_UNIT))
M(u"d6 VALUE_MISMATCH の内訳の % の数", u"states", lambda c: bump(c.S[u"集計"][DV][u"計"][u"VALUE_MISMATCH の内訳"], u"% の数"))
M(u"d7 10 欄目の数(配当の GROUNDED の真)", u"states", lambda c: bump(c.S[u"集計"][DV][u"計"][TEN_KEY][G], TRUE))
M(u"d8 切れた本のうち claim が 0 の本", u"states", lambda c: bump(c.S[u"集計"][RD][u"計"], u"切れた本のうち claim が 0 の本"))
M(u"d9 切れた本のうち GROUNDED が 0 の本", u"states", lambda c: bump(c.S[u"集計"][EQ][u"丙"], u"切れた本のうち GROUNDED が 0 の本"))
M(u"d10 VALUE_MISMATCH が 1 以上の本", u"states", lambda c: bump(c.S[u"集計"][DV][u"乙"], u"VALUE_MISMATCH が 1 以上の本"))
M(u"d11 字数の合計", u"states", lambda c: bump(c.S[u"集計"][RD][u"甲"], u"字数の合計"))
M(u"d12 切れない理由", u"states", lambda c: bump(c.S[u"集計"][RD][u"計"][u"切れない理由"], u"札なし", -1))
M(u"d13 pointer の期の内訳", u"states", lambda c: bump(c.S[u"集計"][DV][u"計"][u"VALUE_MISMATCH の内訳"][u"pointer の期"], u"Prior1Year"))
M(u"d14 集計の欄が 1 つ消える", u"states", lambda c: c.S[u"集計"][RD][u"計"].pop(u"claim と raw の並びが対応しなかった本"))
M(u"d15 集計の群が消える", u"states", lambda c: c.S[u"集計"][EQ].pop(u"丙"))
M(u"d16 本の ZIP の sha256", u"states", lambda c: book(c, 60).__setitem__(u"ZIP の sha256", flip(book(c, 60)[u"ZIP の sha256"])))
M(u"d17 本が 1 本足りない", u"states", lambda c: c.S[u"本"].pop())
M(u"d18 本の群", u"states", lambda c: book(c, 60).__setitem__(u"群", u"乙"))
M(u"d19 本の claim", u"states", lambda c: bump(first_row(c, DV, lambda r: True)[0][DV], u"claim"))
M(u"d20 切れない本に行を入れる(切り出しを落とす)", u"states", lambda c: (book(c, 6)[EQ].__setitem__(u"切り出し", u"切れない"), book(c, 6)[EQ].__setitem__(u"理由", u"札なし")))
M(u"d21 切れた本の理由に字を入れる", u"states", lambda c: book(c, 60)[RD].__setitem__(u"理由", u"札なし"))
M(u"d22 切れない本の理由が語彙の外", u"states", lambda c: (book(c, 6)[RD].__setitem__(u"切り出し", u"切れない"), book(c, 6)[RD].__setitem__(u"理由", u"その他")))
M(u"d23 行が 9 欄", u"states", lambda c: first_row(c, RD, lambda r: True)[1].pop())
M(u"d24 行の単位の族が語彙の外", u"states", lambda c: first_row(c, EQ, lambda r: True)[1].__setitem__(6, u"ドル"))
M(u"d25 10 欄目を反転(配当の GROUNDED)", u"states", lambda c: (lambda r: r.__setitem__(9, not r[9]))(first_row(c, DV, lambda r: r[2] == G)[1]))
M(u"d26 GROUNDED の行に reason を入れる", u"states", lambda c: first_row(c, RD, lambda r: r[2] == G)[1].__setitem__(3, u"no_subject"))
M(u"d27 UNVERIFIABLE の行の reason を None にする", u"states", lambda c: first_row(c, DV, lambda r: r[2] == UNV)[1].__setitem__(3, None))
M(u"d28 行の並び(同じ位置を 2 回)", u"states", lambda c: (lambda b: b[EQ][u"行"].insert(1, list(b[EQ][u"行"][0])))(first_row(c, EQ, lambda r: True)[0]))
M(u"d29 本の欄が 1 つ増える", u"states", lambda c: book(c, 3).__setitem__(u"余分", 1))
M(u"d30 本の数の欄", u"states", lambda c: bump(c.S, u"本の数", -1))
M(u"d31 字数が 0", u"states", lambda c: book(c, 60)[DV].__setitem__(u"字数", 0))
M(u"d32 対応が真でない", u"states", lambda c: book(c, 60)[EQ].__setitem__(u"対応", False))
M(u"d33 行の state の語", u"states", lambda c: first_row(c, RD, lambda r: r[2] == G)[1].__setitem__(2, u"GROUNDED "))
M(u"d34 集計の VALUE_MISMATCH の内訳の欄の名前", u"states", lambda c: c.S[u"集計"][DV][u"計"][u"VALUE_MISMATCH の内訳"].pop(u"単位の族が他"))
M(u"d35 集計の節の順", u"states", lambda c: c.S.__setitem__(u"集計", collections.OrderedDict(reversed(list(c.S[u"集計"].items())))))
# e. 読みの記録
M(u"e1 型を 1 つ変える(集計は変えない)", u"types", lambda c: types_row(c, u"V 配当").__setitem__(4, u"オ" if types_row(c, u"V 配当")[4] != u"オ" else u"ア"))
M(u"e2 型の集計(V 設備の ア)", u"types", lambda c: bump(c.R[u"型の集計"][u"V 設備"], u"ア"))
M(u"e3 型の集計(G 配当の b)", u"types", lambda c: bump(c.R[u"型の集計"][u"G 配当"], u"b", -1))
M(u"e4 b の違うものの集計", u"types", lambda c: bump(c.R[u"b の違うものの集計"][u"G 配当"], u"範囲", -1))
M(u"e5 行を 1 つ消す", u"types", lambda c: c.R[u"行"].pop(50))
M(u"e6 行の入れ替え(組の順)", u"types", lambda c: c.R[u"行"].insert(0, c.R[u"行"].pop()))
M(u"e7 G 研究の標本の行の位置を変える", u"types", lambda c: types_row(c, u"G 研究").__setitem__(3, types_row(c, u"G 研究")[3] + 1))
M(u"e8 G 設備の標本が先頭から 60 行", u"types", lambda c: [r.__setitem__(slice(1, 4), s) for r, s in zip([r for r in c.R[u"行"] if r[0] == u"G 設備"], (lambda rows: [list(x) for x in rows[:60]])(
    [(b[u"#"], r[0], r[1]) for b in c.S[u"本"] for r in b[EQ][u"行"] if r[2] == G]))])
M(u"e9 引く数", u"types", lambda c: c.R[u"読む行の規則"].__setitem__(u"引く数", 59))
M(u"e10 種", u"types", lambda c: c.R[u"読む行の規則"].__setitem__(u"種", 20261115))
M(u"e11 読む行の数の合計", u"types", lambda c: bump(c.R[u"読む行の規則"], u"読む行の数の合計"))
M(u"e12 G 研究の行の数", u"types", lambda c: bump(c.R[u"読む行の規則"], u"G 研究の行の数"))
M(u"e13 b なのに違うものが無い", u"types", lambda c: types_row(c, u"G 配当", lambda r: r[4] == u"b").__setitem__(5, None))
M(u"e14 a に違うものが付く", u"types", lambda c: types_row(c, u"G 配当", lambda r: r[4] == u"a").__setitem__(5, u"側"))
M(u"e15 違うものが 4 つの外", u"types", lambda c: types_row(c, u"G 配当", lambda r: r[4] == u"b").__setitem__(5, u"色"))
M(u"e16 G の行に V の型", u"types", lambda c: types_row(c, u"G 配当", lambda r: r[4] == u"a").__setitem__(4, u"ア"))
M(u"e17 V の行に G の型", u"types", lambda c: types_row(c, u"V 配当").__setitem__(4, u"a"))
M(u"e18 組の取り違え(V 設備の行を V 配当にする)", u"types", lambda c: types_row(c, u"V 設備").__setitem__(0, u"V 配当"))
M(u"e19 V の行の位置(VALUE_MISMATCH でない行を指す)", u"types", lambda c: types_row(c, u"V 配当").__setitem__(3, types_row(c, u"V 配当")[3] + 1))
M(u"e20 型の字(V の オ)", u"types", lambda c: c.R[u"型の字"][u"V"].__setitem__(u"オ", u"読んでも分けられる"))
M(u"e21 読む行の数(V 設備)", u"types", lambda c: c.R[u"読む行の規則"][u"読む行の数"].__setitem__(u"V 設備", 7))
M(u"e22 型の集計の欄が 1 つ消える", u"types", lambda c: c.R[u"型の集計"][u"G 研究"].pop(u"c"))
M(u"e23 G 配当の行を 1 つ消す", u"types", lambda c: c.R[u"行"].remove(types_row(c, u"G 配当")))
M(u"e24 V 研究の行を 1 つ消す(集計も)", u"types", lambda c: (c.R[u"行"].remove(types_row(c, u"V 研究")), bump(c.R[u"型の集計"][u"V 研究"], u"オ", -1)))
M(u"e25 G 配当の行が節の取り違え(研究の GROUNDED の行を指す)", u"types", lambda c: types_row(c, u"G 配当").__setitem__(1, types_row(c, u"G 研究")[1]))
M(u"e26 読む行の規則の字(G 研究・G 設備)", u"types", lambda c: c.R[u"読む行の規則"].__setitem__(u"G 研究・G 設備", u"x"))
M(u"e27 型の字の「違うもの」", u"types", lambda c: c.R[u"型の字"][u"違うもの"].reverse())
# g. clean
M(u"g1 key_leaks に 1 つ", u"clean", lambda c: c.S.__setitem__(u"key_leaks", [u"x"]))
M(u"g2 値の欄 value を持つ", u"clean", lambda c: c.S.__setitem__(u"value", 1))
M(u"g3 span の欄", u"clean", lambda c: c.R.__setitem__(u"span", u"x"))
M(u"g4 読みの行に文字の葉", u"clean", lambda c: c.R[u"行"][0].append(u"売上高は1,234百万円となりました"))
M(u"g5 本の欄に会社名らしい字", u"clean", lambda c: book(c, 3)[RD].__setitem__(u"理由", u"㈱x"))
M(u"g6 長い日本語の文", u"clean", lambda c: c.R.__setitem__(u"盲検", u"当社の売上高は前期に比べて増加し、営業利益も増加しました。通期の見通しは据え置きます。これは文です"))
M(u"g7 pointer の字", u"clean", lambda c: c.S[u"集計"].__setitem__(u"メモ", u"jppfs_cor:NetSales"))
M(u"g8 証券コードの形の字", u"clean", lambda c: book(c, 3)[RD].__setitem__(u"理由", u"1234"))
M(u"g9 docID の形の字", u"clean", lambda c: c.P.__setitem__(u"範囲", u"S" + u"100ABCD"))
M(u"g10 監査法人の名らしい字", u"clean", lambda c: c.P.__setitem__(u"範囲", u"あずさ"))
M(u"g11 行の欄に要素名", u"clean", lambda c: first_row(c, RD, lambda r: True)[1].append(u"xbrl:Element"))
M(u"g12 長い欄の名前", u"clean", lambda c: c.S.__setitem__(u"あ" * 61, 1))
M(u"g13 states の行の字が長い", u"clean", lambda c: first_row(c, DV, lambda r: r[3] is not None)[1].__setitem__(3, u"x" * 41))
M(u"g14 札の名前でない要素名", u"clean", lambda c: c.S[u"切り出し"][u"札の名前"].__setitem__(u"別", u"jpcrp_cor:SomethingElseTextBlock"))
# h. 文書
for _i, _n in enumerate(BLOCK_NAMES):
    M(u"h%d 塊 %s の数字 1 つ" % (_i + 1, _n), u"doc", (lambda n: (lambda c: doc_digit(c, n)))(_n))
M(u"h17 塊の名前を変える", u"doc", doc_replace(u"<!-- 門:start read -->", u"<!-- 門:start readx -->"))
M(u"h18 知らない塊", u"doc", doc_append(u"\n<!-- 門:start zz -->\n|a|\n<!-- 門:end -->\n"))
M(u"h19 散文に記録に無い数", u"doc", doc_append(u"\n散文の数 98765 件。\n"))
M(u"h20 漢数字で逃がす", u"doc", doc_append(u"\n百三十三本。\n"))
M(u"h21 禁止語", u"doc", doc_append(u"\n人の" + u"目で見た。\n"))
M(u"h22 docID の形", u"doc", doc_append(u"\nS" + u"100ABCD\n"))
M(u"h23 会社名らしい字", u"doc", doc_append(u"\n株式会社\n"))
M(u"h24 監査法人の名らしい字", u"doc", doc_append(u"\nあずさ\n"))
M(u"h25 pointer の字", u"doc", doc_append(u"\njppfs_cor:NetSales\n"))
for _j, _ph in enumerate((u"AI の席", u"人は読んでいない", u"盲検ではない", u"紙面", u"候補", u"測っていない", u"足さない", u"採用 / 不採用の判定は無い", u"食い違い")):
    M(u"h%d 必要な語(%s)を消す" % (26 + _j, _ph), u"doc", (lambda ph: (lambda c: setattr(c, "doc", c.doc.replace(ph, u""))))(_ph))
M(u"h35 封の commit を言わない", u"doc", lambda c: setattr(c, "doc", c.doc.replace(SEAL_COMMIT_SHORT, u"")))
M(u"h36 script の commit を言わない", u"doc", lambda c: setattr(c, "doc", c.doc.replace(SCRIPT_COMMIT, u"")))
M(u"h37 記録の file 名を言わない", u"doc", lambda c: setattr(c, "doc", c.doc.replace(u"read_types_2026-11-16.json", u"")))
M(u"h38 測り直しの環境変数を言わない", u"doc", lambda c: setattr(c, "doc", c.doc.replace(u"AUDIT_CORE_YS_REMEASURE=1", u"")))
for _k in (1, 2, 7, 8, 11):
    M(u"h%d 封 §6 の %d 項を 1 字変える(文書の写し)" % (38 + _k, _k), u"doc", (lambda k: (lambda c: setattr(c, "doc", c.doc.replace(seal_limits(c.seal)[k - 1], seal_limits(c.seal)[k - 1][:6] + u"×" + seal_limits(c.seal)[k - 1][7:]))))(_k))
M(u"h52 封 §6 の 3 項の「封 §6-3:」の印を消す", u"doc", doc_replace(u"封 §6-3: ", u"- "))
M(u"h53 封 §6 の 6 項を落とす(文書の写し)", u"doc", lambda c: setattr(c, "doc", c.doc.replace(seal_limits(c.seal)[5], u"")))
M(u"h54 予測の判定の字(Y-8 を当たりにする)", u"doc", doc_sub(u"(\\| Y-8 \\|[^\n]*\\| )外れ( \\|)", u"\\1当たり\\2"))
M(u"h55 予測の判定の字(Y-7 を外れにする)", u"doc", doc_sub(u"(\\| Y-7 \\|[^\n]*\\| )当たり( \\|)", u"\\1外れ\\2"))
M(u"h56 予測の判定の字(Y-12 を当たりにする)", u"doc", doc_sub(u"(\\| Y-12 \\|[^\n]*\\| )外れ( \\|)", u"\\1当たり\\2"))
M(u"h57 Y-6 の実測の字", u"doc", doc_replace(u"時間の欄を除いて byte で同じだった", u"時間の欄を除いて byte で違った"))
M(u"h58 Y-6 の判定の字(環境変数の名)", u"doc", doc_replace(u"環境変数 `AUDIT_CORE_YS_REMEASURE=1` のときだけ走る)", u"環境変数 `AUDIT_CORE_YS_REMEASURE=0` のときだけ走る)"))
M(u"h59 予測(封)の列の字(Y-5 の 351 を 350 に)", u"doc", doc_replace(u"42 本。351 行 |", u"42 本。350 行 |"))
M(u"h60 width の位置の字(Y-8 の幅の外)", u"doc", doc_replace(u"0 行 = 幅の外(下端まで 4 行)", u"0 行 = 幅の外(下端まで 3 行)"))
M(u"h61 width の位置の字(Y-11 の内)", u"doc", doc_replace(u"4 行 = 内(下端から 4 行上・上端まで 2 行)", u"4 行 = 内(下端から 4 行上・上端まで 3 行)"))
M(u"h62 width の位置の字(Y-12 の幅の外)", u"doc", doc_replace(u"16 行 = 幅の外(上端から 11 行上)", u"16 行 = 幅の内(上端から 11 行上)"))
M(u"h63 width の位置の字(Y-9 の下端そのもの)", u"doc", doc_replace(u"3 行 = 下端そのもの", u"3 行 = 上端そのもの"))
M(u"h64 rows_v の通し番号を 1 つずらす", u"doc", doc_replace(u"| V 設備 | 3 | 87 |", u"| V 設備 | 4 | 87 |"))
M(u"h65 rows_g の通し番号を 1 つずらす", u"doc", doc_replace(u"| G 配当 | 21 | 135 |", u"| G 配当 | 22 | 135 |"))
M(u"h66 rows_g の型の字", u"doc", doc_replace(u"| G 設備 | 28 | 94 | 1 | 21 | (b)・項目 |", u"| G 設備 | 28 | 94 | 1 | 21 | (b)・範囲 |"))
M(u"h67 rows_v の行を落とす", u"doc", doc_sub(u"\\| V 研究 \\| 2 \\| 149 \\|[^\n]*\n", u""))
M(u"h68 sha の 1 字", u"doc", doc_replace(u"`7264bd20", u"`7264bd21"))
M(u"h69 sha の 1 字(read_types)", u"doc", doc_replace(u"`9087a95d", u"`9087a95e"))
M(u"h70 types_g の率の字", u"doc", doc_replace(u"| 54 | 56 | 15 | 90.0% | 93.3% | 48.4% |", u"| 54 | 56 | 15 | 90.0% | 93.3% | 48.5% |"))
M(u"h71 types_v の封の字", u"doc", doc_replace(u"| (カ) | 丸め・単位 |", u"| (カ) | 丸め・単位・符号 |"))
M(u"h72 cross の行", u"doc", doc_replace(u"| G 配当 | (b)・範囲 | 13 | 13 | 0 | 0 | 1 | 7 |", u"| G 配当 | (b)・範囲 | 13 | 13 | 0 | 0 | 2 | 6 |"))
M(u"h73 reasons の行", u"doc", doc_replace(u"| UNVERIFIABLE | per_unit_counter | 0 | 0 | 351 |", u"| UNVERIFIABLE | per_unit_counter | 0 | 0 | 352 |"))
M(u"h74 mech の行", u"doc", doc_replace(u"| 導出(formula) | 0 | 0 | 0 | 0 | 1 | 2 |", u"| 導出(formula) | 0 | 0 | 0 | 0 | 2 | 2 |"))
M(u"h75 ten の行", u"doc", doc_replace(u"| 配当政策 | **計** | 31 | 0 | 9 | 1 |", u"| 配当政策 | **計** | 31 | 0 | 10 | 0 |"))
M(u"h76 read の行", u"doc", doc_replace(u"| 配当政策の GROUNDED の全部 | 31 | 31 |", u"| 配当政策の GROUNDED の全部 | 31 | 30 |"))
# h. 散文の断片(数と字)
M(u"h77 §1 の当たり外れの数の字", u"doc", doc_replace(u"当たり 6・**外れ 2(Y-8・Y-12)**", u"当たり 7・**外れ 1(Y-8)**"))
M(u"h78 §1 の Y-9 の余裕の字", u"doc", doc_replace(u"余裕は 0 行だった", u"余裕は 1 行だった"))
M(u"h79 §1 の「3 回目」を消す", u"doc", doc_replace(u"**Y-12 は (b) の多いほうへ外れた = 3 回目。**", u"Y-12 は外れた。"))
M(u"h80 §1 の Y-10 の外れ方の字", u"doc", doc_replace(u"Y-10 は外れ方(5 行以上)に入る", u"Y-10 は外れ方(6 行以上)に入る"))
M(u"h81 §2 の GROUNDED が 0 の本の字", u"doc", doc_replace(u"GROUNDED が 0 の本は 135。", u"GROUNDED が 0 の本は 78。"))
M(u"h82 §2 の「3 割に届かない」を消す", u"doc", doc_replace(u"で 3 割に届かない。", u"。"))
M(u"h83 §2 の per_unit_counter の数", u"doc", doc_replace(u"止まった(UNVERIFIABLE)418 のうち 351 が", u"止まった(UNVERIFIABLE)418 のうち 282 が"))
M(u"h84 §2 の「値が違う」の行の字", u"doc", doc_replace(u"3 つの節で 2 行・6 行・10 行", u"3 つの節で 2 行・6 行・9 行"))
M(u"h85 §3 の配当の (a) の字", u"doc", doc_replace(u"(a) と読めたのは 15 行(48.4%)", u"(a) と読めたのは 16 行(48.4%)"))
M(u"h86 §3 の期の字(前期 1・他 7)", u"doc", doc_replace(u"(前期 1・他 7)", u"(前期 2・他 6)"))
M(u"h87 §3 の使われた型", u"doc", doc_replace(u"使われた型は (ア)・(イ)・(オ) の 3 つだけ", u"使われた型は (ア)・(イ)・(ウ) の 3 つだけ"))
M(u"h88 §5 の節の数の字", u"doc", doc_replace(u"3 割に届かない節が 2 つ**", u"3 割に届かない節が 3 つ**"))
M(u"h89 §5 の偽の警報の字", u"doc", doc_replace(u"18 行のうち 18 行が偽の警報", u"18 行のうち 17 行が偽の警報"))
M(u"h90 §5 の (ク) の字", u"doc", doc_replace(u"(ク) は 0 行 = この便は", u"(ク) は 1 行 = この便は"))
M(u"h91 §5 の標本の字", u"doc", doc_replace(u"(85 行・150 行のうち)", u"(85 行・149 行のうち)"))
M(u"h92 §6 の「9 割ほど」の字", u"doc", doc_replace(u"結べた」の 9 割ほどを", u"結べた」の 5 割ほどを"))
M(u"h93 §6 の採用の字を足す", u"doc", doc_replace(u"人間が決める)。この結果は", u"人間が決める)。採用とする。この結果は"))
M(u"h94 (ク) を食い違いと呼ぶ", u"doc", doc_append(u"\n(ク) は食い違い\n"))
M(u"h95 古い字を足す", u"doc", doc_append(u"\n外れは 0 行。\n"))
M(u"h96 §5 の「同じ向きに 3 回目の外れ」を消す", u"doc", doc_replace(u"同じ向きに 3 回目の外れ", u"同じ向きの外れ"))
# 記録の側を 1 つ変えると文書の塊が違う(判定の移動・塊の数)
M(u"h97 記録の側: V 設備の (ア) を 1 行 (オ) に(Y-9 が外れる)", u"doc", lambda c: types_row(c, u"V 設備", lambda r: r[4] == u"ア").__setitem__(4, u"オ"))
M(u"h98 記録の側: G 配当の (b) を 1 行 (a) に", u"doc", lambda c: (lambda r: (r.__setitem__(4, u"a"), r.__setitem__(5, None)))(types_row(c, u"G 配当", lambda r: r[4] == u"b")))
M(u"h99 記録の側: V 配当の (イ) を (ウ) に(Y-8 の数)", u"doc", lambda c: types_row(c, u"V 配当", lambda r: r[4] == u"イ").__setitem__(4, u"ウ"))
M(u"h100 記録の側: 研究の claim の行を state ごと動かす", u"doc", lambda c: first_row(c, RD, lambda r: r[2] == UNV)[1].__setitem__(2, PNF))
M(u"h101 封の側: Y-7 の幅", u"doc", seal_replace(u"| 0〜2 行 | 3 行以上", u"| 0〜3 行 | 3 行以上"))
M(u"h102 記録の側: G 研究の (c) を 1 行 (b)・範囲 に(Y-10 の数)", u"doc", lambda c: (lambda r: (r.__setitem__(4, u"b"), r.__setitem__(5, u"範囲")))(types_row(c, u"G 研究", lambda r: r[4] == u"c")))
M(u"h103 記録の側: V 研究の 1 行目の位置を 2 行目と同じにする(rows_v)", u"doc", lambda c: [r for r in c.R[u"行"] if r[0] == u"V 研究"][0].__setitem__(slice(1, 4), [r for r in c.R[u"行"] if r[0] == u"V 研究"][1][1:4]))
# i. 封
M(u"i1 封の Y-9 の幅", u"seal", seal_replace(u"| 3 行以上 | 2 行以下", u"| 4 行以上 | 2 行以下"))
M(u"i2 封の Y-11 の幅", u"seal", seal_replace(u"| 0〜6 行 | 7 行以上", u"| 0〜7 行 | 7 行以上"))
M(u"i3 封の Y-13 の幅", u"seal", seal_replace(u"| 0〜17 行 |", u"| 0〜18 行 |"))
M(u"i4 封の Y-3 の数", u"seal", seal_replace(u"175 = 85 / 2 / 43 / 45", u"175 = 86 / 2 / 43 / 45"))
M(u"i5 封の Y-13 が消える", u"seal", seal_replace(u"| Y-13 |", u"| Y-X |"))
M(u"i6 封 §6 の 1 項が消える", u"seal", seal_replace(u"- 注入をしていないので、「誤りを通す率」はこの便では言えない。\n", u""))
M(u"i7 封が commit のときと 1 字違う", u"frozen", lambda c: setattr(c, "seal", c.seal + u"。"))
M(u"i8 封の文の途中の 1 字", u"frozen", seal_replace(u"同じ有報の中の照合", u"同じ有報の中の照会"))
M(u"i9 封の Y-8 の幅(4 行以上 → 5 行以上)", u"seal", seal_replace(u"| 4 行以上 | 3 行以下", u"| 5 行以上 | 3 行以下"))
M(u"i10 封の型の字(V の (ア))", u"types", seal_replace(u"- (ア) 一部分の数", u"- (ア) 全部の数"))


def check_problems(check, c):
    return guard(CHECKS[check], c)


# ======================================================================================================
# 試験
class RealRecordsTest(unittest.TestCase):
    def test_a_1_the_three_records_and_the_script_equal_the_pinned_sha256(self):
        self.assertEqual([], sha_problems(Ctx().texts))

    def test_a_2_the_pinned_sha256_are_the_ones_the_brief_names(self):
        self.assertEqual(["7264bd201eeff1f2b011e783fe26ae4b9435ca7e3fb0436f148a662ff16a3374", "130498b4781160154210cacd31d35a8498e4d460f7d3ac88968bf21a7aae4ac5",
                          "9087a95d0f51e559012b72a9f5f2af7c9575e57589120b50b7ba1d93f46fd3bb", "23162fa9221aaa7a71e2ab602c46ac92cb473bb85d3fdeef75ba4c2d22373191"], list(SHA_PIN.values()))
        self.assertEqual([POP_REL, STATES_REL, TYPES_REL, SCRIPT_REL], list(SHA_PIN.keys()))
        self.assertEqual((u"fixtures/xbrl/yuho_sections/population_2026-11-16.json", u"fixtures/xbrl/yuho_sections/states_2026-11-16.json",
                          u"fixtures/xbrl/yuho_sections/read_types_2026-11-16.json"), RECORD_RELS)

    def test_b_1_the_provenance_fields_equal_the_real_files(self):
        self.assertEqual([], provenance_problems(Ctx()))

    def test_c_1_the_population_record_is_the_seal_table(self):
        self.assertEqual([], population_problems(Ctx()))

    def test_c_2_the_three_records_share_the_same_201_numbers(self):
        c = Ctx()
        self.assertEqual([], keys_problems(c))
        self.assertEqual(201, len(c.S[u"本"]))
        self.assertEqual(201, c.S[u"本の数"])
        self.assertEqual(sorted(r[0] for r in c.P[u"行"]), sorted(b[u"#"] for b in c.S[u"本"]))
        self.assertTrue(set(r[1] for r in c.R[u"行"]) <= set(b[u"#"] for b in c.S[u"本"]))

    def test_d_1_the_states_record_is_whole_and_recounted_from_its_rows(self):
        self.assertEqual([], states_problems(Ctx()))

    def test_d_2_the_recount_pins_the_real_numbers_literally(self):
        c = Ctx()
        w = dict((sec, recount_sec(c.S[u"本"], sec)) for sec in SECS)
        self.assertEqual([(201, 201, 0)] * 3, [(w[s][u"本"], w[s][u"切れた"], w[s][u"切れない"]) for s in SECS])
        self.assertEqual([80998, 39975, 110509], [w[s][u"字数の合計"] for s in SECS])
        self.assertEqual([175, 509, 957], [w[s][u"claim"] for s in SECS])
        self.assertEqual([[85, 2, 43, 45], [150, 6, 146, 207], [31, 10, 418, 498]], [[w[s][u"4 state"][x] for x in STATES] for s in SECS])
        self.assertEqual([124, 25, 42], [w[s][u"切れた本のうち claim が 0 の本"] for s in SECS])
        self.assertEqual([135, 78, 183], [w[s][u"切れた本のうち GROUNDED が 0 の本"] for s in SECS])
        self.assertEqual([2, 6, 9], [w[s][u"VALUE_MISMATCH が 1 以上の本"] for s in SECS])
        self.assertEqual(351, w[DV][u"reason"][UNV][PER_UNIT])
        self.assertEqual([0, 0, 0], [w[s][u"claim と raw の並びが対応しなかった本"] for s in SECS])
        self.assertEqual([2, 6, 10], [w[s][u"VALUE_MISMATCH の内訳"][u"行"] for s in SECS])
        self.assertEqual([0, 0, 0], [w[s][u"VALUE_MISMATCH の内訳"][u"導出(formula)"] for s in SECS])
        self.assertEqual({G: {TRUE: 31, FALSE: 0}, VM: {TRUE: 9, FALSE: 1}, UNV: {TRUE: 0, FALSE: 418}, PNF: {TRUE: 0, FALSE: 498}}, plain(w[DV][TEN_KEY]))

    def test_d_3_the_group_rows_pin_the_real_numbers_literally(self):
        c = Ctx()
        want = {(RD, u"甲"): (67, 63, [30, 1, 16, 16]), (RD, u"乙"): (40, 22, [14, 0, 7, 1]), (RD, u"丙"): (94, 90, [41, 1, 20, 28]),
                (EQ, u"甲"): (67, 172, [52, 2, 48, 70]), (EQ, u"乙"): (40, 99, [29, 2, 26, 42]), (EQ, u"丙"): (94, 238, [69, 2, 72, 95]),
                (DV, u"甲"): (67, 355, [12, 1, 156, 186]), (DV, u"乙"): (40, 154, [7, 2, 73, 72]), (DV, u"丙"): (94, 448, [12, 7, 189, 240])}
        for (sec, g), w in want.items():
            r = recount_sec(c.S[u"本"], sec, g)
            self.assertEqual(w, (r[u"本"], r[u"claim"], [r[u"4 state"][s] for s in STATES]), (sec, g))

    def test_e_1_the_read_types_record_is_whole_and_redrawn_from_the_states_record(self):
        self.assertEqual([], types_problems(Ctx()))

    def test_e_2_the_read_types_numbers_are_pinned_literally(self):
        c = Ctx()
        self.assertEqual(169, len(c.R[u"行"]))
        self.assertEqual({u"V 研究": 2, u"V 設備": 6, u"V 配当": 10, u"G 研究": 60, u"G 設備": 60, u"G 配当": 31}, dict((lab, sum(1 for r in c.R[u"行"] if r[0] == lab)) for lab in LABELS))
        cnt = type_counts(c)
        self.assertEqual({u"オ": 2}, dict(cnt[u"V 研究"]))
        self.assertEqual({u"ア": 3, u"オ": 3}, dict(cnt[u"V 設備"]))
        self.assertEqual({u"ア": 1, u"イ": 7, u"オ": 2}, dict(cnt[u"V 配当"]))
        self.assertEqual({u"a": 54, u"c": 6}, dict(cnt[u"G 研究"]))
        self.assertEqual({u"a": 56, u"b": 4}, dict(cnt[u"G 設備"]))
        self.assertEqual({u"a": 15, u"b": 16}, dict(cnt[u"G 配当"]))
        for lab in G_LABELS:
            self.assertEqual(dict(collections.Counter()), dict(collections.Counter(r[5] for r in c.R[u"行"] if r[0] == lab and r[4] != u"b" and r[5] is not None)))
        self.assertEqual({u"項目": 2, u"範囲": 2}, dict(collections.Counter(r[5] for r in c.R[u"行"] if r[0] == u"G 設備" and r[4] == u"b")))
        self.assertEqual({u"項目": 3, u"範囲": 13}, dict(collections.Counter(r[5] for r in c.R[u"行"] if r[0] == u"G 配当" and r[4] == u"b")))
        for t in (u"ウ", u"エ", u"カ", u"キ", u"ク", u"ケ"):
            self.assertEqual(0, sum(cnt[lab][t] for lab in V_LABELS), t)

    def test_e_3_the_g_samples_are_draws_of_60_from_85_and_150_and_are_not_the_first_60(self):
        c = Ctx()
        exp, mother = expected_reading(c.S)
        self.assertEqual((85, 150, 31), (mother[u"G 研究"], mother[u"G 設備"], mother[u"G 配当"]))
        for lab, n in ((u"G 研究", 85), (u"G 設備", 150)):
            idx = sorted(random.Random(20261116).sample(range(n), 60))
            self.assertEqual(60, len(set(idx)))
            self.assertNotEqual(list(range(60)), idx)
            sec = LABEL_SEC[lab]
            allg = [(b[u"#"], r[0], r[1]) for b in sorted(c.S[u"本"], key=lambda b: b[u"#"]) for r in sorted(b[sec][u"行"], key=lambda r: (r[0], r[1])) if r[2] == G]
            self.assertEqual([allg[i] for i in idx], [tuple(r[1:4]) for r in c.R[u"行"] if r[0] == lab])
        self.assertEqual([tuple(r[1:4]) for r in c.R[u"行"] if r[0] == u"G 配当"], exp[u"G 配当"])

    def test_e_4_the_record_gate_of_the_seal_gate_is_green_on_the_real_records(self):
        u"""封の門が見ている欄・docID・行の形・本の順(重ねて書かず、封の門の検査を呼ぶ)。"""
        self.assertEqual([], SG.record_problems())

    def test_f_1_the_records_hold_no_sentence_no_value_no_company_no_code_no_pointer(self):
        self.assertEqual([], clean_problems(Ctx()))

    def test_g_1_the_blocks_of_the_result_document_equal_the_rebuilt_tables(self):
        self.assertEqual([], doc_problems(Ctx()))

    def test_g_2_the_prediction_judgements_are_pinned_literally(self):
        rows = dict((r[0], r[4]) for r in pred_table(Ctx()))
        want = dict((yid, u"当たり") for yid in PRED_IDS)
        want[u"Y-6"] = Y6_JUDGE
        want[u"Y-8"] = u"外れ"
        want[u"Y-12"] = u"外れ"
        self.assertEqual(want, rows)

    def test_g_3_the_prediction_actuals_are_pinned_literally(self):
        rows = dict((r[0], r[3]) for r in pred_table(Ctx()))
        self.assertEqual(u"研究開発活動 切れた 201・切れない 0、設備投資等の概要 切れた 201・切れない 0、配当政策 切れた 201・切れない 0", rows[u"Y-1"])
        self.assertEqual(u"研究開発活動 80,998・設備投資等の概要 39,975・配当政策 110,509", rows[u"Y-2"])
        self.assertEqual(u"175 = 85 / 2 / 43 / 45。claim が 0 の本 124", rows[u"Y-3"])
        self.assertEqual(u"509 = 150 / 6 / 146 / 207。claim が 0 の本 25", rows[u"Y-4"])
        self.assertEqual(u"957 = 31 / 10 / 418 / 498。claim が 0 の本 42。`per_unit_counter` 351 行", rows[u"Y-5"])
        self.assertEqual(u"V の全部 18 行のうち (ク) 0 行", rows[u"Y-7"])
        self.assertEqual(u"V 配当 10 行のうち (ウ) 0 行", rows[u"Y-8"])
        self.assertEqual(u"V 設備 6 行のうち (ア) 3 行", rows[u"Y-9"])
        self.assertEqual(u"G 研究 60 行のうち (b) 0 行", rows[u"Y-10"])
        self.assertEqual(u"G 設備 60 行のうち (b) 4 行", rows[u"Y-11"])
        self.assertEqual(u"G 配当 31 行のうち (b) 16 行", rows[u"Y-12"])
        self.assertEqual(u"読んだ 169 行のうち (ケ) + (c) 6 行", rows[u"Y-13"])

    def test_g_4_the_seal_prediction_bounds_are_in_the_seal_and_pinned(self):
        self.assertEqual([], seal_problems(Ctx().seal))
        y = seal_y_rows(Ctx().seal)
        self.assertEqual(13, len(y))
        self.assertEqual(11, len(seal_limits(Ctx().seal)))
        self.assertEqual({u"Y-7": (0, 2), u"Y-8": (4, None), u"Y-9": (3, None), u"Y-10": (0, 4), u"Y-11": (0, 6), u"Y-12": (0, 5), u"Y-13": (0, 17)},
                         dict((k, bound_of(y[k][1])) for k in BOUND_PHRASES))
        self.assertEqual((Y6_PRED, u"違う = 辞書の順か file の並びが結果を動かしている"), (y[u"Y-6"][1], y[u"Y-6"][2]))

    def test_g_5_the_width_positions_are_pinned_literally(self):
        lines = width_lines(Ctx())
        self.assertEqual([u"| Y-7 | 0〜2 行 | 0 行 = 下端そのもの |", u"| Y-8 | 4 行以上 | 0 行 = 幅の外(下端まで 4 行) |", u"| Y-9 | 3 行以上 | 3 行 = 下端そのもの |",
                          u"| Y-10 | 0〜4 行 | 0 行 = 下端そのもの |", u"| Y-11 | 0〜6 行 | 4 行 = 内(下端から 4 行上・上端まで 2 行) |", u"| Y-12 | 0〜5 行 | 16 行 = 幅の外(上端から 11 行上) |",
                          u"| Y-13 | 0〜17 行 | 6 行 = 内(下端から 6 行上・上端まで 11 行) |"], lines[2:])

    def test_g_6_the_six_numbers_of_the_seal_equal_the_records(self):
        u"""封 §0-1 の 6 の表(下調べの数)と、記録から数えた節 × 群の数が同じ(Y-3〜Y-5 は下調べの数をそのまま置いた予測)。"""
        six = SG.seal_six(Ctx().seal)
        c = Ctx()
        for sec in SECS:
            for g in GROUPS + (None,):
                w = recount_sec(c.S[u"本"], sec, g)
                s = w[u"4 state"]
                self.assertEqual(six[(sec, g or u"計")], (w[u"本"], w[u"切れた"], w[u"claim"], s[G], s[VM], s[UNV], s[PNF]), (sec, g))

    def test_h_1_the_seal_is_the_text_of_the_sealed_commit(self):
        self.assertEqual([], seal_frozen_problems(Ctx().seal))

    def test_h_2_the_real_history_has_the_seal_before_the_script_before_the_records_the_document_and_this_gate(self):
        u"""記録 3 つ・結果の文書・この門のどれかが未 commit なら赤(足した commit が無い。skip にしない)。全部 commit された後で初めて緑。"""
        self.assertEqual([], order_problems_real())

    def test_h_3_the_real_order_failure_before_the_commit_is_only_the_uncommitted_files(self):
        got = order_problems_real()
        self.assertTrue(all(p.startswith(u"UNCOMMITTED:") for p in got), got)

    def test_h_4_the_order_check_lists_the_three_records_the_document_and_this_gate(self):
        self.assertEqual(list(RECORD_RELS) + [DOC_REL, GATE_REL], order_others())
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, r)) for r in RECORD_RELS + (DOC_REL, GATE_REL, SCRIPT_REL, SEAL_GATE_REL)))

    def test_h_5_engine_lib_and_the_previous_stages_are_untouched_and_the_script_is_unchanged_since_its_commit(self):
        self.assertEqual([], engine_problems())


class OrderGateTest(unittest.TestCase):
    u"""順序の検査自体が、悪い順を赤にできること(使い捨ての git で)。"""

    def test_o_1_good_and_bad_orders(self):
        r = PR.Repo()
        r.put("docs/seal.md")
        s = r.commit("docs/seal.md")
        r.put("measure/s.py")
        r.commit("measure/s.py")
        for o in ("fixtures/a.json", "docs/r.md", "tests/g.py"):
            r.put(o)
        others = ["fixtures/a.json", "docs/r.md", "tests/g.py"]
        self.assertEqual([u"UNCOMMITTED:" + o for o in others], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], ["measure/s.py"], others))
        r.commit(*others)
        self.assertEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], ["measure/s.py"], others))
        r2 = PR.Repo()
        r2.put("measure/s.py")
        r2.commit("measure/s.py")
        r2.put("docs/seal.md")
        s2 = r2.commit("docs/seal.md")
        self.assertNotEqual([], PR.order_problems(r2.d, PREFIX, "docs/seal.md", s2[:7], ["measure/s.py"], []))     # script が封より前


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
        self.assertEqual([], silent, u"赤にならなかった変異: %s" % silent)
        self.assertEqual([], crashed, u"検査が例外で落ちて赤になった変異: %s" % crashed)

    def test_m_3_each_mutation_gets_a_new_copy_and_leaves_the_real_files_alone(self):
        before = dict((rel, sha256_rel(rel)) for rel in list(SHA_PIN) + [SEAL_REL, DOC_REL])
        c = Ctx()
        c.S[u"集計"][RD][u"計"][u"claim"] = -1
        c.doc = u"x"
        c.cur["script"] = u"x"
        self.assertEqual(175, Ctx().S[u"集計"][RD][u"計"][u"claim"])
        self.assertNotEqual(u"x", Ctx().doc)
        self.assertNotEqual(u"x", Ctx().cur["script"])
        self.assertEqual(before, dict((rel, sha256_rel(rel)) for rel in before))

    def test_m_4_the_mutation_table_covers_every_check_and_every_effect_named_in_the_brief(self):
        checks = set(ch for _l, ch, _f in MUTATIONS)
        self.assertEqual(set(CHECKS), checks)
        self.assertGreaterEqual(len(MUTATIONS), 200)
        labels = u"\n".join(l for l, _c, _f in MUTATIONS)
        for need in (u"の数字 1 つ", u"散文に記録に無い数", u"漢数字", u"Y-8 を当たりにする", u"Y-7 を外れにする", u"width の位置の字", u"通し番号を 1 つずらす", u"sha の 1 字", u"封 §6 の", u"型を 1 つ変える",
                     u"記録の側", u"states の「この script の sha256」", u"封の文の途中の 1 字", u"行を 1 つ消す", u"本の ZIP の sha256", u"Y-6 の実測の字", u"組の取り違え", u"型の集計",
                     u"違うものが 4 つの外", u"b なのに違うものが無い", u"# の集合", u"G 設備の標本が先頭から 60 行", u"節の取り違え", u"禁止語", u"採用の字"):
            self.assertIn(need, labels)

    def test_m_5_the_prose_number_check_accepts_a_block_number_and_refuses_another(self):
        c = Ctx()
        blocks = build_blocks(c)
        self.assertEqual([], prose_number_problems(u"本文。配当政策の claim は 957 行(31 行が GROUNDED)。", blocks, c.seal))
        self.assertNotEqual([], prose_number_problems(u"本文。配当政策の claim は 958 行。", blocks, c.seal))
        self.assertEqual([], prose_number_problems(u"本文。封 `e7754d70` と `3b9c54bc` と 2026-11-16 と P33E と Y-10 と §6-10。", blocks, c.seal))
        self.assertNotEqual([], prose_number_problems(u"本文。三百本。", blocks, c.seal))

    def test_m_6_a_changed_read_type_reddens_the_type_blocks_the_cross_block_and_the_types_check(self):
        u"""読みの記録の型を 1 行変えると、types_v・types_g・types_b・cross・rows_g(または rows_v)の塊と、型の集計の検査が、それぞれ別の理由で赤になる。"""
        c = Ctx()
        types_row(c, u"G 配当", lambda r: r[4] == u"b" and r[5] == u"範囲")[5] = u"項目"
        got = u"\n".join(doc_problems(c))
        for name in (u"types_b", u"cross", u"rows_g"):
            self.assertIn(u"塊 %s が記録から作り直した表と違う" % name, got, name)
        self.assertNotEqual([], types_problems(c))
        c2 = Ctx()
        types_row(c2, u"G 研究", lambda r: r[4] == u"a")[4] = u"c"
        got2 = u"\n".join(doc_problems(c2))
        for name in (u"types_g", u"cross", u"rows_g", u"pred"):
            self.assertIn(u"塊 %s が記録から作り直した表と違う" % name, got2, name)
        c3 = Ctx()
        types_row(c3, u"V 設備", lambda r: r[4] == u"ア")[4] = u"オ"
        got3 = u"\n".join(doc_problems(c3))
        for name in (u"types_v", u"cross", u"rows_v", u"pred", u"width"):
            self.assertIn(u"塊 %s が記録から作り直した表と違う" % name, got3, name)

    def test_m_7_the_sealed_text_a_record_and_a_script_byte_change_are_caught_in_a_throwaway_folder(self):
        u"""file の字を変えた写しを使い捨ての folder に作り、``Ctx(root)`` で読む(追跡している file は変えない)。"""
        before = dict((rel, sha256_rel(rel)) for rel in list(SHA_PIN) + [SEAL_REL, DOC_REL])
        with tmpdir() as d:
            for rel in list(RECORD_RELS) + [DOC_REL, SEAL_REL, SCRIPT_REL]:
                os.makedirs(os.path.dirname(os.path.join(d, rel)), exist_ok=True)
                shutil.copyfile(os.path.join(ROOT, rel), os.path.join(d, rel))
            self.assertEqual([], sha_problems(Ctx(d).texts))
            self.assertEqual([], doc_problems(Ctx(d)))
            self.assertEqual([], states_problems(Ctx(d)))
            p = os.path.join(d, DOC_REL)
            text = read(DOC_REL, d)
            for old, new in ((u"| 研究開発活動 | **計** | 7 | 78 |", u"| 研究開発活動 | **計** | 8 | 77 |"), (u"| Y-8 |", u"| Y-9 |"), (u"6 行の全部を (b)", u"7 行の全部を (b)")):
                self.assertIn(old, text)
                with io.open(p, "w", encoding="utf-8") as fh:
                    fh.write(text.replace(old, new, 1))
                _TEXT.pop((d, DOC_REL), None)
                self.assertNotEqual([], doc_problems(Ctx(d)), old)
            with io.open(p, "w", encoding="utf-8") as fh:
                fh.write(text)
            _TEXT.pop((d, DOC_REL), None)
            self.assertEqual([], doc_problems(Ctx(d)))
            for rel, fn in ((STATES_REL, lambda t: t.replace(u'"GROUNDED"', u'"GROUNDEd"', 1)), (TYPES_REL, lambda t: (lambda d: (d[u"行"][0].__setitem__(4, u"ア"), json.dumps(d, ensure_ascii=False, indent=1))[1])(json.loads(t))), (POP_REL, lambda t: t.replace(u'"甲"', u'"乙"', 1))):
                q = os.path.join(d, rel)
                t0 = read(rel, d)
                with io.open(q, "w", encoding="utf-8") as fh:
                    fh.write(fn(t0))
                _TEXT.pop((d, rel), None)
                c = Ctx(d)
                self.assertNotEqual([], sha_problems(c.texts), rel)
                self.assertNotEqual([], (states_problems(c) + types_problems(c) + population_problems(c) + doc_problems(c) + provenance_problems(c)), rel)
                with io.open(q, "w", encoding="utf-8") as fh:
                    fh.write(t0)
                _TEXT.pop((d, rel), None)
            self.assertEqual([], sha_problems(Ctx(d).texts))
        self.assertEqual(before, dict((rel, sha256_rel(rel)) for rel in before))


class JudgementTest(unittest.TestCase):
    u"""予測の判定の関数が「外れ」と「当たり」の両方を出せること(全部が同じ字の記録でだけ緑になる関数は、当たりの字を黙って書ける)。"""

    @staticmethod
    def judged(fn):
        c = Ctx()
        fn(c)
        return dict((r[0], r[4]) for r in pred_table(c))

    @staticmethod
    def retype(c, lab, old, new, n, diff=None):
        rows = [r for r in c.R[u"行"] if r[0] == lab and r[4] == old][:n]
        assert len(rows) == n, (lab, old, n)
        for r in rows:
            r[4] = new
            r[5] = diff if new == u"b" else None

    def test_j_1_y7_turns_to_a_miss_beyond_the_sealed_width(self):
        self.assertEqual(u"当たり", self.judged(lambda c: self.retype(c, u"V 設備", u"ア", u"ク", 2))[u"Y-7"])
        self.assertEqual(u"外れ", self.judged(lambda c: self.retype(c, u"V 設備", u"ア", u"ク", 3))[u"Y-7"])

    def test_j_2_y8_is_a_hit_at_four_and_a_miss_below(self):
        self.assertEqual(u"外れ", self.judged(lambda c: self.retype(c, u"V 配当", u"イ", u"ウ", 3))[u"Y-8"])
        self.assertEqual(u"当たり", self.judged(lambda c: self.retype(c, u"V 配当", u"イ", u"ウ", 4))[u"Y-8"])

    def test_j_3_y9_turns_to_a_miss_below_three(self):
        self.assertEqual(u"外れ", self.judged(lambda c: self.retype(c, u"V 設備", u"ア", u"オ", 1))[u"Y-9"])
        self.assertEqual(u"当たり", self.judged(lambda c: self.retype(c, u"V 設備", u"オ", u"ア", 1))[u"Y-9"])

    def test_j_4_y10_y11_y12_turn_at_the_sealed_upper_ends(self):
        self.assertEqual(u"当たり", self.judged(lambda c: self.retype(c, u"G 研究", u"c", u"b", 4, u"範囲"))[u"Y-10"])
        self.assertEqual(u"外れ", self.judged(lambda c: self.retype(c, u"G 研究", u"c", u"b", 5, u"範囲"))[u"Y-10"])
        self.assertEqual(u"当たり", self.judged(lambda c: self.retype(c, u"G 設備", u"a", u"b", 2, u"範囲"))[u"Y-11"])
        self.assertEqual(u"外れ", self.judged(lambda c: self.retype(c, u"G 設備", u"a", u"b", 3, u"範囲"))[u"Y-11"])
        self.assertEqual(u"当たり", self.judged(lambda c: self.retype(c, u"G 配当", u"b", u"a", 11))[u"Y-12"])
        self.assertEqual(u"外れ", self.judged(lambda c: self.retype(c, u"G 配当", u"b", u"a", 10))[u"Y-12"])

    def test_j_5_y13_turns_at_17_and_18(self):
        self.assertEqual(u"当たり", self.judged(lambda c: self.retype(c, u"G 設備", u"a", u"c", 11))[u"Y-13"])
        self.assertEqual(u"外れ", self.judged(lambda c: self.retype(c, u"G 設備", u"a", u"c", 12))[u"Y-13"])

    def test_j_6_y1_to_y5_each_turn_to_a_miss_when_the_states_record_differs_from_the_sealed_numbers(self):
        self.assertEqual(u"外れ", self.judged(lambda c: (book(c, 6)[RD].__setitem__(u"切り出し", u"切れない"), book(c, 6)[RD].__setitem__(u"理由", u"空")))[u"Y-1"])
        self.assertEqual(u"外れ", self.judged(lambda c: bump(book(c, 60)[EQ], u"字数"))[u"Y-2"])
        self.assertEqual(u"外れ", self.judged(lambda c: first_row(c, RD, lambda r: r[2] == G)[1].__setitem__(2, VM))[u"Y-3"])
        self.assertEqual(u"外れ", self.judged(lambda c: first_row(c, EQ, lambda r: r[2] == G)[1].__setitem__(2, VM))[u"Y-4"])
        self.assertEqual(u"外れ", self.judged(lambda c: first_row(c, DV, lambda r: r[2] == UNV and r[3] == PER_UNIT)[1].__setitem__(3, u"other_frame"))[u"Y-5"])

    def test_j_7_the_real_records_judge_five_sealed_plus_five_real_as_hits_two_misses_and_y6_as_pinned(self):
        got = self.judged(lambda c: None)
        self.assertEqual(list(PRED_IDS), list(got.keys()))
        self.assertEqual(11, sum(1 for v in got.values() if v.startswith(u"当たり")))
        self.assertEqual([u"Y-8", u"Y-12"], [k for k, v in got.items() if v.startswith(u"外れ")])
        self.assertEqual(Y6_JUDGE, got[u"Y-6"])
        self.assertEqual((4, None), bound_of(seal_y_rows(Ctx().seal)[u"Y-8"][1]))
        self.assertEqual(u"下端そのもの", position(0, 0, 2))
        self.assertEqual(u"上端そのもの", position(2, 0, 2))
        self.assertEqual(u"幅の外(下端まで 4 行)", position(0, 4, None))
        self.assertEqual(u"幅の外(上端から 1 行上)", position(6, 0, 5))
        self.assertEqual(u"内(下端から 3 行上)", position(6, 3, None))


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
        self.assertEqual([], [w for w in (u"人の" + u"目", u"証明" + u"した", u"ハルシ" + u"ネーション") if w in src])

    def test_n_3_the_gate_calls_none_of_the_scripts_tally_functions(self):
        u"""門は script の集計・判定・標本の関数を呼ばず、自前で数え直す(構造は ast で見る。字面の検査は自分の説明文に当たる)。"""
        import ast
        tree = ast.parse(read(GATE_REL))
        banned = set([u"tally", u"block", u"judge_book", u"judge_section", u"cut_section", u"row10", u"reading_items", u"run_states", u"run_population", u"run_types", u"pick_sample",
                      u"state_counts", u"reason_counts", u"vm_breakdown", u"states_job"])
        used = [(n.value.id, n.attr) for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id in (u"MS", u"TSS", u"TS", u"ST", u"KAM")]
        self.assertEqual([], [x for x in used if x[1] in banned])

    def test_n_4_the_script_is_loaded_without_overwriting_the_names_that_existed(self):
        import types
        marker = types.ModuleType("pswap_for_ys_result")
        before = sys.modules.get("pswap_for_ys_result")
        sys.modules["pswap_for_ys_result"] = marker
        try:
            mod = load_module(SCRIPT_REL, "ys_script_reload_probe_for_result_gate")
            self.assertIs(marker, sys.modules["pswap_for_ys_result"])
            self.assertIs(mod, sys.modules["ys_script_reload_probe_for_result_gate"])
        finally:
            if before is None:
                sys.modules.pop("pswap_for_ys_result", None)
            else:
                sys.modules["pswap_for_ys_result"] = before
            sys.modules.pop("ys_script_reload_probe_for_result_gate", None)

    def test_n_5_the_pinned_literals_equal_the_script_constants(self):
        self.assertEqual(MS.SEAL_COMMIT, SEAL_COMMIT_SHORT)
        self.assertEqual(MS.READ_SEED, SEED)
        self.assertEqual(MS.READ_N, DRAW_N)
        self.assertEqual(list(MS.SECTIONS), list(SECS))
        self.assertEqual(MS.TYPED_BY, TYPED_BY)
        self.assertEqual(MS.POPULATION_REL, POP_REL)
        self.assertEqual(MS.STATES_REL, STATES_REL)
        self.assertEqual(MS.TYPES_REL, TYPES_REL)
        self.assertEqual(MS.DOC_REL, DOC_REL)
        self.assertEqual(list(MS.TYPES_V), list(V_TYPES))
        self.assertEqual(list(MS.TYPES_G), list(G_TYPES))
        self.assertEqual(tuple(MS.DIFFS), DIFFS)
        self.assertEqual(list(MS.READ_SETS), list(LABELS))


@unittest.skipUnless(os.environ.get("AUDIT_CORE_YS_REMEASURE") == "1", u"材料から測り直す試験は AUDIT_CORE_YS_REMEASURE=1 のときだけ走る")
class RemeasureTest(unittest.TestCase):
    def _strip(self, text):
        return re.sub(r'^ *"時間\(秒\)": .*$', u"", text, flags=re.M)

    def _run(self, sub, name):
        with tmpdir() as d:
            out = os.path.join(d, name)
            with open(os.devnull, "w") as dn:
                r = subprocess.run([sys.executable, os.path.join(ROOT, SCRIPT_REL), sub, "--out", out], cwd=ROOT, stdout=dn, stderr=dn, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
            self.assertEqual(0, r.returncode)
            with io.open(out, encoding="utf-8") as fh:
                return fh.read()

    def test_r_1_the_states_record_is_reproduced_from_the_material_byte_for_byte_except_the_time(self):
        u"""既定の材料(読むだけ)で states を走らせ、追跡の記録と、時間の欄を除いて byte で同じ。本番の path には書かない。"""
        self.assertEqual(self._strip(cached_text(STATES_REL)), self._strip(self._run("states", "states_remeasure.json")))

    def test_r_2_the_population_record_is_reproduced_from_the_material_byte_for_byte(self):
        self.assertEqual(self._strip(cached_text(POP_REL)), self._strip(self._run("population", "population_remeasure.json")))


if __name__ == "__main__":
    unittest.main()
