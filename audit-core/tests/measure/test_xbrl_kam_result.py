# -*- coding: utf-8 -*-
"""結果の門: 封 docs/XBRL_KAM_SEAL_2026-11-15.md §2 の 4・5・6(KAM ― 有価証券報告書の監査報告書の「監査上の主要な検討事項」の文を、同じ有報の fact で確かめる便の結果)。

封の門 ``test_xbrl_kam_seal.py`` の次の段。**追跡されている記録 3 つ・封・結果の文書だけを読む**(cache の材料が無い機械でも緑。材料から測り直す試験だけ環境変数
``AUDIT_CORE_KAM_REMEASURE=1`` で走る)。

縛るもの(検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表で 1 本ずつ)
 a 記録 3 つと script の sha256(字で留める)  b 記録の来歴の欄(script・前の便の script・封の表・母集団の表・engine の指紋・states の記録の sha256 を実物と突き合わせる)
 c 母集団の記録が封 §1 の表の 201 行と同じ  d 判定の記録を本の行から数え直す(script の集計は呼ばない。集計の欄と両方に当てる)
 e 読みの記録: 行の数・組ごとの数・型の集計を行から数え直す・読む行が判定の記録の行と合う・G 連結の 60 行を種から引き直す・b と違うものの対応
 f 型と 10 欄目の交差(G 単体の b = 10 欄目が偽の行・V 単体の (ウ) = 10 欄目が偽の行 など)
 g 記録に文も値も会社名も証券コードも docID も pointer の字も無い・key_leaks が空
 h 結果の文書の塊を記録から作り直して 1 行ずつ照らす・塊の外の 2 桁以上の数・予測の当たり外れ・封 §6 の 10 項の字
 i 封が 497a4661 から 1 字も変わっていない・順序(commit の順。未 commit は赤)・engine 0 行・script が e6f01e24 から変わっていない
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


SG = load_module("tests/measure/test_xbrl_kam_seal.py", "kam_seal_gate_for_kam_result_gate")      # 封の門の部品。門としては走らせない
PR = SG.PR
MS = SG.MS

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
GATE_REL = "tests/measure/test_xbrl_kam_result.py"
DOC_REL = SG.DOC_REL
POP_REL, STATES_REL, TYPES_REL = SG.RECORD_RELS
RECORD_RELS = (POP_REL, STATES_REL, TYPES_REL)
SCRIPT_COMMIT = "e6f01e24"                                  # script と封の門を足した commit(この commit から script は 0 行)

# ---- 字で留める(記録・script の sha256。人が決めた数は字で留める)
SHA_PIN = collections.OrderedDict([
    (POP_REL, "86e31ca230850d9a13061a18f647c17dea2b95a76927d2587374978af2aef410"),
    (STATES_REL, "3ba57f55e62a29e20578b87f527de35d9bc3d2310cbba232d9311c9b187103e7"),
    (TYPES_REL, "8c9fe6b8def7430908bf925f697ea5a1b1d634dd754933aab7c71b0a913c964a"),
    (SCRIPT_REL, "cc2aab3029ef76d91e73aceae562370d3e74a58f51d90cecfb6153e28259aa4a")])
STATES = (u"GROUNDED", u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND")
G, VM, UNV, PNF = STATES
CONS, NON = u"連結", u"単体"
SIDES = (CONS, NON)
GROUPS = (u"甲", u"乙", u"丙")
WHYS = (u"decode", u"札なし", u"札が複数", u"続きあり", u"閉じない", u"空")
SETS = (u"V 連結", u"V 単体", u"G 連結", u"G 単体")
V_TYPES = tuple(u"アイウエオカキクケ")
G_TYPES = (u"a", u"b", u"c")
DIFFS = (u"項目", u"範囲", u"側", u"期")
SEED, DRAW_N = 20261115, 60
N_BOOKS = 201
PERIODS = (u"CurrentYear", u"Prior1Year", u"Prior2Year")
FAMILIES = (u"%", u"円族", u"他")
BLOCK_NAMES = (u"pred", u"width", u"cons", u"non", u"ten", u"reasons", u"vm", u"read", u"types_v", u"types_g", u"types_b", u"cross", u"hesitant", u"serials", u"alt", u"sha")
NO_NUMBER_BLOCKS = (u"sha",)                                # sha256 の字は数の集合に入れない
FORBIDDEN_WORDS = (u"精度", u"ハルシネーション", u"証明した", u"LLM より正確", u"世界で 1 社", u"人の目")
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
POP_STEP = u"KAM(監査報告書の KAM の文を同じ有報の fact で確かめる)― 母集団 201 本の記録(0 USD・通信なし)"
STATES_STEP = u"KAM(監査報告書の KAM の文を同じ有報の fact で確かめる)― 201 本の切り出し・判定(0 USD・通信なし)"
TYPES_STEP = u"KAM ― 読む行の型分け(0 USD)"
MATERIAL_PLACE = u"~/.cache/audit-core の 3 つの folder(甲・乙・丙。名前は書かない)"
G_RULE_TEXT = u"連結の GROUNDED の行を # の順・文の番号の順・位置の順に並べ、random.Random(種).sample(range(行の数), 引く数) を番号の順に。行の数が引く数に満たなければ全部"
ROW_COLS = [u"文の番号", u"位置", u"state", u"reason", u"pointer の期", u"formula の有無", u"単位の族", u"両期の fact を引く a−b", u"span に % を含む",
            u"pointer の字のどれかに NonConsolidatedMember を含む"]
FORBIDDEN_KEYS = tuple(MS.TS.RUN.FORBIDDEN_KEYS) + (u"pointers", u"pointer", u"要素", u"element", u"context", u"label", u"会社名", u"subject", u"span", u"value", u"text", u"文", u"sentence", u"recomputed")
POP_KEYS = (u"seal", u"封の commit", u"step", u"HEAD の commit", u"この script の sha256", u"封の表の sha256", u"母集団の表(# TAB 群 TAB sha256 の行)の sha256", u"範囲", u"材料", u"群",
            u"byte 数の合計", u"行の欄", u"行", u"key_leaks")
STATES_KEYS = (u"seal", u"封の commit", u"step", u"HEAD の commit", u"この script の sha256", u"2026-11-09 の便の script の sha256", u"TSS の script の sha256", u"封の表の sha256",
               u"母集団の表(# TAB 群 TAB sha256 の行)の sha256", u"engine の指紋", u"profile", u"材料", u"切り出し", u"判定", u"本の数", u"集計", u"限界", u"行の欄", u"時間(秒)", u"key_leaks", u"本")
TYPES_KEYS = (u"seal", u"封の commit", u"step", u"HEAD の commit", u"この script の sha256", u"states の記録の sha256", u"型を付けた席", u"盲検", u"読む行の規則", u"型の字", u"型の集計",
              u"b の違うものの集計", u"行の欄", u"行", u"key_leaks")
BOOK_KEYS = (u"#", u"群", u"ZIP の sha256", u"連結", u"単体")
SIDE_KEYS = (u"切り出し", u"理由", u"字数", u"claim", u"対応", u"行")
AGG_KEYS = (u"本", u"切れた", u"切れない", u"切れない理由", u"字数の合計", u"claim", u"4 state", u"reason", u"VALUE_MISMATCH の内訳", u"10 欄目(pointer の字のどれかに NonConsolidatedMember を含む)の数",
            u"切れた本のうち claim が 0 の本", u"切れた本のうち GROUNDED が 0 の本", u"VALUE_MISMATCH が 1 以上の本", u"claim と raw の並びが対応しなかった本")
TEN_KEY = AGG_KEYS[9]
VM_KEYS = (u"行", u"導出(formula)", u"直接", u"% の数", u"円族の数", u"両期の fact を引く a−b(円)", u"単位の族が %", u"単位の族が円族", u"単位の族が他", u"pointer の期")
VM_PERIOD_KEYS = (u"CurrentYear", u"Prior1Year", u"Prior2Year", u"他", u"なし")
TRUE, FALSE = u"真", u"偽"
LABELS = collections.OrderedDict([
    (u"K-1", u"切り出し"), (u"K-2", u"字数の合計"), (u"K-3", u"連結の数の claim と 4 state"), (u"K-4", u"単体の数の claim と 4 state"), (u"K-5", u"2 回走らせた記録"),
    (u"K-6", u"V 連結の (ア)"), (u"K-7", u"V の (ク)"), (u"K-8", u"V 単体の (ウ)"), (u"K-9", u"G 連結の (b)"), (u"K-10", u"G 単体の (b) と「側」"), (u"K-11", u"読んでも分けられない")])
SEALED_NUMBERS = collections.OrderedDict([
    (u"K-1", (151, 50, 192, 9, 59)), (u"K-2", (244159, 147934)), (u"K-3", (480, 136, 29, 72, 243, 26)), (u"K-4", (308, 36, 8, 50, 214, 30, 6))])
BOUND_PHRASES = collections.OrderedDict([
    (u"K-6", u"18 行以上(行の数の 62% 以上)"), (u"K-7", u"0〜1 行"), (u"K-8", u"1〜4 行"), (u"K-9", u"0〜3 行"), (u"K-10", u"(b) 1〜6 行。「側」1〜6 行"), (u"K-11", u"0〜13 行")])
K5_ACTUAL = (u"追跡している記録に在るのは 1 回目だけ。2 回走らせた判定の記録 2 つ(scratchpad に置き、追跡していない)と追跡の states の記録は、時間の欄を除いて byte で同じだった")
K5_JUDGE = u"当たり(一回限りの手の実測で、門ではない。材料から測り直す試験は環境変数 `AUDIT_CORE_KAM_REMEASURE=1` のときだけ走る)"
# ---- 別の読みが成り立つ行の通し番号(組の中の読んだ行の並びの 1 から数えた番号。人が決めた数は字で留める。司令塔の決め 2026-11-15)
ALT_G_CONS = (9, 11, 13, 26, 37, 44, 50, 58)                # (a) の決めで入れた行。字どおりに読めば (b)・違うものは「範囲」
ALT_V_CONS = (2, 13, 22)                                   # 結んだ先が前期の fact の行(V 連結)。記録では (オ)・(エ) と読めば (エ)
ALT_V_NON = (5, 7)                                         # 同(V 単体)
HES_V_CONS = (3, 21)                                       # 迷った行。3 は (ク) とも読める
ALT_K = (u"G 連結", ALT_G_CONS), (u"V 連結", ALT_V_CONS), (u"V 単体", ALT_V_NON)
SERIAL_PHRASES = (u"G 連結の通し番号 9・11・13・26・37・44・50・58", u"V 連結の通し番号 2・13・22", u"V 単体の通し番号 5・7", u"V 連結の通し番号 3", u"V 連結の通し番号 21")
SERIAL_RE = re.compile(u"(?:V 連結|V 単体|G 連結)の通し番号 [0-9・]+(?![0-9])")
REQUIRED_PHRASES = (u"AI の席", u"人は読んでいない", u"盲検ではない", u"紙面", u"候補", u"測っていない", u"読んでいない", u"足さない", u"採用 / 不採用の判定は無い", u"食い違い")


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


def cached_text(rel):
    if rel not in _TEXT:
        _TEXT[rel] = read(rel)
    return _TEXT[rel]


_CUR = {}


def current_values():
    u"""今の file・engine の値(1 回だけ数える。Ctx は写しを持つ)。"""
    if not _CUR:
        _CUR.update({"script": sha256_rel(SCRIPT_REL), "tss": sha256_rel(MS.TSS_SCRIPT_REL), "ts": sha256_rel(MS.TS_SCRIPT_REL), "seal": sha256_rel(SEAL_REL),
                     "pop": sha256_rel(POP_REL), "states": sha256_rel(STATES_REL), "types": sha256_rel(TYPES_REL), "fp": MS.VD.engine_fingerprint()})
    return dict(_CUR)


class Ctx(object):
    u"""記録・封・文書・今の file の値。変異は毎回 ``Ctx()`` の新しい写しに 1 か所だけ加える。"""

    def __init__(self):
        self.P = json.loads(cached_text(POP_REL))
        self.S = json.loads(cached_text(STATES_REL))
        self.R = json.loads(cached_text(TYPES_REL))
        self.seal = cached_text(SEAL_REL)
        self.doc = cached_text(DOC_REL) if os.path.exists(os.path.join(ROOT, DOC_REL)) else u""
        self.texts = collections.OrderedDict((rel, read_bytes(rel)) for rel in SHA_PIN)         # sha256 を見る file の中身
        self.cur = current_values()


# ======================================================================================================
# 封から読む字
def seal_k_rows(seal):
    u"""封 §3 の K-1〜K-11(id → (欄, 予測, 外れ方))。"""
    sec = seal[seal.index(u"## §3"):seal.index(u"## §4")]
    out = collections.OrderedDict()
    for m in re.finditer(r"^\| (K-\d+) \| (.*?) \| (.*?) \| (.*?) \|$", sec, re.M):
        out[m.group(1)] = (m.group(2), m.group(3), m.group(4))
    return out


def seal_limits(seal):
    u"""封 §6 の 10 項(字のまま)。"""
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
    if S.get(u"2026-11-09 の便の script の sha256") != cur["ts"] or S.get(u"TSS の script の sha256") != cur["tss"]:
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
# c. 母集団の記録
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


# ======================================================================================================
# d. 判定の記録
def cut_of(b, side):
    return b[side][u"切り出し"] == u"切れた"


def recount_side(books, side, grp=None):
    u"""判定の集計を、本の行から別の書き方で数え直す(script の ``block``・``tally`` は使わない)。"""
    bs = [b for b in books if grp is None or b[u"群"] == grp]
    cut = [b for b in bs if cut_of(b, side)]
    rows = [r for b in bs for r in b[side][u"行"]]
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
        (u"切れない理由", collections.OrderedDict((k, sum(1 for b in bs if not cut_of(b, side) and b[side][u"理由"] == k)) for k in WHYS)),
        (u"字数の合計", sum(b[side][u"字数"] for b in cut)),
        (u"claim", len(rows)), (u"4 state", collections.OrderedDict((s, sum(1 for r in rows if r[2] == s)) for s in STATES)),
        (u"reason", collections.OrderedDict((s, dict(rs[s])) for s in STATES)),
        (u"VALUE_MISMATCH の内訳", collections.OrderedDict([
            (u"行", len(vm)), (u"導出(formula)", sum(1 for r in vm if r[5])), (u"直接", sum(1 for r in vm if not r[5])), (u"% の数", sum(1 for r in vm if r[8])),
            (u"円族の数", sum(1 for r in vm if not r[8])), (u"両期の fact を引く a−b(円)", sum(1 for r in vm if r[7])),
            (u"単位の族が %", sum(1 for r in vm if r[6] == u"%")), (u"単位の族が円族", sum(1 for r in vm if r[6] == u"円族")), (u"単位の族が他", sum(1 for r in vm if r[6] == u"他")),
            (u"pointer の期", period)])),
        (TEN_KEY, ten),
        (u"切れた本のうち claim が 0 の本", sum(1 for b in cut if not b[side][u"行"])), (u"切れた本のうち GROUNDED が 0 の本", sum(1 for b in cut if not any(r[2] == G for r in b[side][u"行"]))),
        (u"VALUE_MISMATCH が 1 以上の本", sum(1 for b in cut if any(r[2] == VM for r in b[side][u"行"]))), (u"claim と raw の並びが対応しなかった本", sum(1 for b in cut if b[side][u"対応"] is not True))])


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
        for side in SIDES:
            d = b[side]
            if tuple(d.keys()) != SIDE_KEYS:
                out.append(u"states: 本 %d の %s の欄が違う" % (b[u"#"], side))
                shape_bad = True
                continue
            cut = d[u"切り出し"] == u"切れた"
            if d[u"切り出し"] not in (u"切れた", u"切れない") or cut != (d[u"理由"] is None) or (not cut and d[u"理由"] not in WHYS):
                out.append(u"states: 本 %d の %s の切り出しと理由が合わない" % (b[u"#"], side))
            if not is_int(d[u"claim"]) or d[u"claim"] != len(d[u"行"]):
                out.append(u"states: 本 %d の %s の claim が行の数と違う" % (b[u"#"], side))
            if cut and (not is_int(d[u"字数"]) or d[u"字数"] <= 0 or d[u"対応"] is not True):
                out.append(u"states: 本 %d の %s が切れたのに字数・対応が正でない" % (b[u"#"], side))
            if not cut and (d[u"字数"] is not None or d[u"対応"] is not None or d[u"行"] or d[u"claim"]):
                out.append(u"states: 切れない本 %d の %s に字数・行が在る" % (b[u"#"], side))
            keys = [(r[0], r[1]) for r in d[u"行"]]
            if keys != sorted(set(keys)):
                out.append(u"states: 本 %d の %s の行が (文の番号, 位置) の昇順で 1 行ずつでない" % (b[u"#"], side))
            for r in d[u"行"]:
                if not row_shape_ok(r):
                    out.append(u"states: 本 %d の %s の行が封の 10 欄でない" % (b[u"#"], side))
                    shape_bad = True
                    break
    if shape_bad:
        return out                                   # 形が壊れた記録は数え直さない(数え直しが例外で落ちて赤になるのを避ける)
    agg = S.get(u"集計") or {}
    if tuple(agg.keys()) != SIDES:
        out.append(u"states: 集計の文の種類が 連結・単体 でない")
    for side in SIDES:
        a = agg.get(side) or {}
        if tuple(a.keys()) != GROUPS + (u"計",):
            out.append(u"states: 集計[%s]の群が 甲・乙・丙・計 でない" % side)
        for g in GROUPS + (None,):
            name = g or u"計"
            got = a.get(name) or {}
            w = recount_side(books, side, g)
            if tuple(got.keys()) != AGG_KEYS:
                out.append(u"states: 集計[%s][%s]の欄の名前が違う" % (side, name))
            for k in w:
                if plain(w[k]) != plain(got.get(k)):
                    out.append(u"states: 集計[%s][%s]の %s が行から数え直した値と違う" % (side, name, k))
            if tuple((got.get(u"VALUE_MISMATCH の内訳") or {}).keys()) != VM_KEYS:
                out.append(u"states: 集計[%s][%s]の VALUE_MISMATCH の内訳の欄の名前が違う" % (side, name))
    return out


# ======================================================================================================
# e. 読みの記録
def state_index(S):
    u"""{(文の種類, 本の #, 文の番号, 位置): 行}。"""
    d = {}
    for b in S[u"本"]:
        for side in SIDES:
            for r in b[side][u"行"]:
                d[(side, b[u"#"], r[0], r[1])] = r
    return d


def set_side(label):
    return CONS if label.endswith(CONS) else NON


def expected_reading(S):
    u"""読む行(封 §0-2 の 7)を判定の記録から引き直す。{組: [(本の #, 文の番号, 位置)]}。G 連結は種 20261115 の random.Random.sample で 60 行。"""
    def rows_of(side, state):
        out = []
        for b in sorted(S[u"本"], key=lambda b: b[u"#"]):
            for r in sorted((r for r in b[side][u"行"] if r[2] == state), key=lambda r: (r[0], r[1])):
                out.append((b[u"#"], r[0], r[1]))
        return out
    v_c, v_n = rows_of(CONS, VM), rows_of(NON, VM)
    g_c, g_n = rows_of(CONS, G), rows_of(NON, G)
    idx = sorted(random.Random(SEED).sample(range(len(g_c)), DRAW_N)) if len(g_c) > DRAW_N else list(range(len(g_c)))
    return collections.OrderedDict([(u"V 連結", v_c), (u"V 単体", v_n), (u"G 連結", [g_c[i] for i in idx]), (u"G 単体", g_n)]), len(g_c)


def type_set(label):
    return V_TYPES if label.startswith(u"V") else G_TYPES


def types_problems(c):
    R, S = c.R, c.S
    out = []
    rows = R.get(u"行") or []
    sidx = state_index(S)
    exp, n_g = expected_reading(S)
    for r in rows:
        if not (len(r) == 6 and r[0] in SETS and all(is_int(x) for x in r[1:4]) and r[4] in type_set(r[0]) and ((r[4] == u"b") == (r[5] is not None)) and (r[5] is None or r[5] in DIFFS)):
            out.append(u"types: 行が「組・本の #・文の番号・位置・型(組に合う)・違うもの(b のときだけ)」でない")
            return out
    if [r[0] for r in rows] != [lab for lab in SETS for _r in exp[lab]]:
        out.append(u"types: 行の組の並び・数が、読む行の規則から引き直した並び・数と違う")
    for lab in SETS:
        got = [tuple(r[1:4]) for r in rows if r[0] == lab]
        if got != exp[lab]:
            out.append(u"types: 組 %s の行が、判定の記録から引き直した読む行と 1 行ずつ同じでない" % lab)
        for r in rows:
            if r[0] == lab:
                s = sidx.get((set_side(lab), r[1], r[2], r[3]))
                if s is None or s[2] != (VM if lab.startswith(u"V") else G):
                    out.append(u"types: 組 %s の行が判定の記録の行と合わない(state か文の種類か位置)" % lab)
                    break
    rule = R.get(u"読む行の規則") or {}
    cnt = collections.OrderedDict((lab, len(exp[lab])) for lab in SETS)
    if rule.get(u"種") != SEED or rule.get(u"引く数") != DRAW_N or rule.get(u"G 連結の行の数") != n_g or rule.get(u"読む行の数") != dict(cnt) or rule.get(u"読む行の数の合計") != sum(cnt.values()) \
            or rule.get(u"G 連結") != G_RULE_TEXT or len(rows) != sum(cnt.values()):
        out.append(u"types: 読む行の規則の欄(種・引く数・G 連結の行の数・組ごとの数・合計)が違う")
    v_txt, g_txt = seal_type_texts(c.seal)
    tt = R.get(u"型の字") or {}
    if tt != {u"V": dict(v_txt), u"G": dict(g_txt), u"違うもの": list(DIFFS)} or list(tt.get(u"V", {}).keys()) != list(V_TYPES) or list(tt.get(u"G", {}).keys()) != list(G_TYPES):
        out.append(u"types: 型の字が封 §0-2 の 7 の字と違う")
    want_cnt = collections.OrderedDict((lab, collections.OrderedDict((t, sum(1 for r in rows if r[0] == lab and r[4] == t)) for t in type_set(lab))) for lab in SETS)
    got_cnt = R.get(u"型の集計") or {}
    if plain(want_cnt) != plain(got_cnt) or list(got_cnt.keys()) != list(SETS):
        out.append(u"types: 型の集計が行から数え直した値と違う")
    want_d = collections.OrderedDict((lab, collections.OrderedDict((d, sum(1 for r in rows if r[0] == lab and r[4] == u"b" and r[5] == d)) for d in DIFFS)) for lab in (u"G 連結", u"G 単体"))
    if plain(want_d) != plain(R.get(u"b の違うものの集計")):
        out.append(u"types: b の違うものの集計が行から数え直した値と違う")
    return out


# ======================================================================================================
# f. 型と 10 欄目の交差・側
def read_join(c):
    u"""読んだ行 [(組, 本の #, 文の番号, 位置, 型, 違うもの, 判定の行)]。"""
    sidx = state_index(c.S)
    return [tuple(r) + (sidx[(set_side(r[0]), r[1], r[2], r[3])],) for r in c.R[u"行"]]


def cross_problems(c):
    out = []
    j = read_join(c)
    cons_cut = dict((b[u"#"], cut_of(b, CONS)) for b in c.S[u"本"])
    for lab, n, sent, pos, t, d, s in j:
        ten = s[9]
        if lab in (u"V 連結", u"G 連結") and ten is not False:
            out.append(u"cross: 連結の行の 10 欄目が偽でない")
        if lab == u"V 単体" and ((t == u"ウ") != (ten is False)):
            out.append(u"cross: V 単体の (ウ) と 10 欄目が偽の行が 1 対 1 でない")
        if lab == u"G 単体" and ((t == u"b") != (ten is False) or (t == u"b" and d != u"側")):
            out.append(u"cross: G 単体の b(違うもの = 側)と 10 欄目が偽の行が 1 対 1 でない")
        if lab in (u"V 単体", u"G 単体") and ten is False and not cons_cut.get(n):
            out.append(u"cross: 10 欄目が偽の単体の行の本に、連結の切り出しが無い")
    if sum(1 for r in j if r[0] == u"G 単体" and r[4] == u"b" and r[6][5] is True and r[6][7] is True) != 1:
        out.append(u"cross: G 単体の b のうち導出(両期の差)の行が 1 行でない")
    out += alt_serial_problems(c, j)
    return out


def alt_serial_problems(c, j):
    u"""字で留めた通し番号の行が、記録の行から数えて言うとおりか(通し番号は組の中の読んだ行の並びの 1 から数えた番号)。pointer の字は見ない(記録の「pointer の期」の欄で判じる)。"""
    out = []
    by = dict((lab, [r for r in j if r[0] == lab]) for lab in SETS)
    if (len(ALT_G_CONS), len(ALT_V_CONS), len(ALT_V_NON)) != (8, 3, 2) or len(set(ALT_G_CONS)) != 8 or list(ALT_G_CONS) != sorted(ALT_G_CONS):
        out.append(u"cross: 通し番号の一覧の本数が字で留めた 8・3・2 と違う")
    for n in ALT_G_CONS:
        if not (1 <= n <= len(by[u"G 連結"]) and by[u"G 連結"][n - 1][4] == u"a"):
            out.append(u"cross: G 連結の通し番号 %d が記録で型 a の行でない" % n)
    for lab, ns in ((u"V 連結", ALT_V_CONS), (u"V 単体", ALT_V_NON)):
        for n in ns:
            if not (1 <= n <= len(by[lab]) and by[lab][n - 1][4] == u"オ" and by[lab][n - 1][6][4] == u"Prior1Year"):
                out.append(u"cross: %s の通し番号 %d が記録で型 オ・結んだ先の期が前期の行でない" % (lab, n))
        prior = [i + 1 for i, r in enumerate(by[lab]) if r[6][4] == u"Prior1Year"]
        if prior != list(ns):
            out.append(u"cross: %s の、結んだ先の期が前期の行の通し番号が字で留めた一覧と違う" % lab)
    vc = by[u"V 連結"]
    if len(vc) < 21 or vc[2][4] != u"オ" or vc[20][4] != u"ア":
        out.append(u"cross: V 連結の通し番号 3 が (オ)・21 が (ア) でない")
    return out


# ======================================================================================================
# g. 記録に書かないものが漏れていない
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
    s = set(SG.LIMITS_PINNED) | set(v for v in SG.CUT_RECORD_PINNED.values() if isinstance(v, str)) | set(SG.JUDGE_RECORD_PINNED.values())
    s |= set(v_txt.values()) | set(g_txt.values()) | set(ROW_COLS)
    s |= set([TEN_KEY, TYPED_BY, TYPES_BLIND, POP_STEP, STATES_STEP, TYPES_STEP, MATERIAL_PLACE, G_RULE_TEXT, u"封 §1 の 201 本"])
    return s


def clean_problems(c):
    u"""記録に文・値・会社名・証券コード・pointer の字・docID・TDnet の番号・監査法人の名が無い。門が自前で全部の key と葉を歩く(script の check_clean とは別)。"""
    out = []
    ok = long_ok(c.seal)
    for name, rec in ((u"population", c.P), (u"states", c.S), (u"read_types", c.R)):
        if rec.get(u"key_leaks") != []:
            out.append(u"clean[%s]: key_leaks が空でない" % name)
        bad = sorted(set(k for k in walk_keys(rec) if isinstance(k, str) and k in FORBIDDEN_KEYS))
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
        for side in SIDES:
            for k in (u"切り出し", u"理由"):
                v = b[side].get(k)
                if v is not None and (not isinstance(v, str) or len(v) > 6):
                    out.append(u"clean[states]: 本の %s が短い語彙でない" % k)
            for r in b[side][u"行"]:
                for x in (r[3], r[4], r[6]):
                    if x is not None and (not isinstance(x, str) or len(x) > 40):
                        out.append(u"clean[states]: 行の字が短い語彙でない")
    for r in (c.R.get(u"行") or []):
        if len(r) != 6 or any(isinstance(x, str) and len(x) > 6 for x in r):
            out.append(u"clean[read_types]: 行が短い語彙・数だけでない")
            break
    return out


# ======================================================================================================
# h. 結果の文書
def seal_problems(seal):
    out = []
    try:
        k = seal_k_rows(seal)
        lim = seal_limits(seal)
    except ValueError:
        return [u"封の節が揃っていない"]
    if list(k.keys()) != list(LABELS.keys()):
        return [u"封 §3 が K-1〜K-11 の 11 行でない"]
    for kid, ph in BOUND_PHRASES.items():
        if ph not in k[kid][1]:
            out.append(u"封 %s の予測に幅の字が無い: %s" % (kid, ph))
    for kid, nums in SEALED_NUMBERS.items():
        for n in nums:
            if (fmt(n) if n >= 1000 else str(n)) not in k[kid][1]:
                out.append(u"封 %s に数 %d が無い" % (kid, n))
    try:
        lo9, hi9 = bound_of(k[u"K-9"][1])
        if (lo9, hi9) != (0, 3) or (u"%d 行以上" % (hi9 + 1)) not in k[u"K-9"][2]:
            out.append(u"封 K-9 の幅 0〜3 行・外れ方 4 行以上が字と違う")
    except ValueError:
        out.append(u"封 K-9 の幅が読めない")
    if len(lim) != 10:
        out.append(u"封 §6 が 10 項でない")
    elif u"型分けは司令塔" not in lim[5] or u"G 連結は 60 行の標本" not in lim[6] or u"甲の 67 本" not in lim[9]:
        out.append(u"封 §6 の 6・7・10 番目の字が違う")
    return out


def seal_frozen_problems(seal_text, root=REPO):
    u"""封が 497a4661 の commit のときの byte と同じか(1 字も変わっていない。未 commit の編集も見る)。"""
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
    u"""封 §3 の予測の字から幅(下, 上)を読む。「18 行以上」は (18, None)。"""
    m = re.search(r"(\d+)〜(\d+) 行", pred)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r"(\d+) 行以上", pred)
    if m:
        return int(m.group(1)), None
    raise ValueError(u"幅が読めない")


def in_bound(n, lo, hi):
    return n >= lo and (hi is None or n <= hi)


def split_judge(rec_in, alt_in):
    u"""記録の読みと封の字どおりの読み(別の読み)の両方の判定。どちらも幅の内 = 当たり・どちらも外 = 外れ・割れたら「読みで割れた」。"""
    if rec_in and alt_in:
        return u"当たり"
    if not rec_in and not alt_in:
        return u"外れ"
    return u"読みで割れた(記録の読みでは幅の%s・封の字どおりの読みでは幅の%s)" % (u"中" if rec_in else u"外", u"中" if alt_in else u"外")


def serial_type(c, lab, n):
    return [r for r in c.R[u"行"] if r[0] == lab][n - 1][4]


def alt_counts(c):
    u"""別の読みの数。記録の型が (a)・(オ) の行だけを、字で留めた通し番号の行から数える(型が違う行は数えない)。"""
    cnt = dict((lab, collections.Counter(r[4] for r in c.R[u"行"] if r[0] == lab)) for lab in SETS)
    narrow = sum(1 for n in ALT_G_CONS if serial_type(c, u"G 連結", n) == u"a")
    e_c = sum(1 for n in ALT_V_CONS if serial_type(c, u"V 連結", n) == u"オ")
    e_n = sum(1 for n in ALT_V_NON if serial_type(c, u"V 単体", n) == u"オ")
    k3 = 1 if serial_type(c, u"V 連結", 3) == u"オ" else 0
    return collections.OrderedDict([
        (u"G 連結 b", (cnt[u"G 連結"][u"b"], cnt[u"G 連結"][u"b"] + narrow)), (u"G 連結 a", (cnt[u"G 連結"][u"a"], cnt[u"G 連結"][u"a"] - narrow)),
        (u"範囲が狭い行", narrow), (u"G 連結 60 行", sum(cnt[u"G 連結"].values())),
        (u"V 連結 オ", (cnt[u"V 連結"][u"オ"], cnt[u"V 連結"][u"オ"] - e_c)), (u"V 連結 エ", (cnt[u"V 連結"][u"エ"], cnt[u"V 連結"][u"エ"] + e_c)),
        (u"V 単体 オ", (cnt[u"V 単体"][u"オ"], cnt[u"V 単体"][u"オ"] - e_n)), (u"V 単体 エ", (cnt[u"V 単体"][u"エ"], cnt[u"V 単体"][u"エ"] + e_n)),
        (u"V 連結 ク", (cnt[u"V 連結"][u"ク"], cnt[u"V 連結"][u"ク"] + k3))])


def position(n, lo, hi):
    if not in_bound(n, lo, hi):
        return u"幅の外"
    if n == lo:
        return u"下端そのもの"
    if hi is not None and n == hi:
        return u"上端そのもの"
    return u"内(下端から %d 行上%s)" % (n - lo, u"・上端まで %d 行" % (hi - n) if hi is not None else u"")


def pred_table(c):
    u"""封 §3 の K-1〜K-11 を、記録から判定した行(id, 欄, 予測(封), 実測, 判定)の列にする。数は本の行から数え直す(states の集計の欄は見ない)。"""
    S, R = c.S, c.R
    books = S[u"本"]
    cells = seal_k_rows(c.seal)
    a, b = recount_side(books, CONS), recount_side(books, NON)
    rows = collections.OrderedDict()

    def hit(ok):
        return u"当たり" if ok else u"外れ"
    cnt = dict((lab, collections.Counter(r[4] for r in R[u"行"] if r[0] == lab)) for lab in SETS)
    gd = collections.Counter(r[5] for r in R[u"行"] if r[0] == u"G 単体" and r[4] == u"b")
    notag = a[u"切れない理由"][u"札なし"] + b[u"切れない理由"][u"札なし"]
    v1 = (a[u"切れた"], a[u"切れない"], b[u"切れた"], b[u"切れない"], notag)
    all_notag = v1[4] == v1[1] + v1[3]
    rows[u"K-1"] = (u"連結 切れた %d・切れない %d、単体 切れた %d・切れない %d。" % v1[:4]
                    + (u"切れない %d 本の理由は全部「札なし」" % v1[4] if all_notag else u"切れない %d 本のうち「札なし」は %d 本" % (v1[1] + v1[3], v1[4])),
                    hit(v1 == (151, 50, 192, 9, 59) and all_notag))
    v2 = (a[u"字数の合計"], b[u"字数の合計"])
    rows[u"K-2"] = (u"連結 %s・単体 %s" % (fmt(v2[0]), fmt(v2[1])), hit(v2 == SEALED_NUMBERS[u"K-2"]))
    s4 = a[u"4 state"]
    v3 = (a[u"claim"], s4[G], s4[VM], s4[UNV], s4[PNF], a[u"VALUE_MISMATCH が 1 以上の本"])
    rows[u"K-3"] = (u"%s = %s / %s / %s / %s。VALUE_MISMATCH が 1 以上の本 %d" % ((fmt(v3[0]),) + tuple(fmt(x) for x in v3[1:5]) + (v3[5],)), hit(v3 == SEALED_NUMBERS[u"K-3"]))
    t4 = b[u"4 state"]
    ten = b[TEN_KEY][G]
    v4 = (b[u"claim"], t4[G], t4[VM], t4[UNV], t4[PNF], ten[TRUE], ten[FALSE])
    rows[u"K-4"] = (u"%s = %s / %s / %s / %s。GROUNDED のうち 10 欄目が真 %d・偽 %d" % ((fmt(v4[0]),) + tuple(fmt(x) for x in v4[1:5]) + (v4[5], v4[6])), hit(v4 == SEALED_NUMBERS[u"K-4"]))
    rows[u"K-5"] = (K5_ACTUAL, K5_JUDGE)
    n_vc = sum(cnt[u"V 連結"].values())
    a_n = cnt[u"V 連結"][u"ア"]
    rows[u"K-6"] = (u"V 連結 %d 行のうち (ア) %d 行(%s)" % (n_vc, a_n, pct(a_n, n_vc)), hit(a_n >= 18 and a_n * 100 >= 62 * n_vc))
    ku = cnt[u"V 連結"][u"ク"] + cnt[u"V 単体"][u"ク"]
    n_v = n_vc + sum(cnt[u"V 単体"].values())
    rows[u"K-7"] = (u"V 連結 + V 単体 %d 行のうち (ク) %d 行" % (n_v, ku), hit(0 <= ku <= 1))
    n_vn = sum(cnt[u"V 単体"].values())
    u_n = cnt[u"V 単体"][u"ウ"]
    rows[u"K-8"] = (u"V 単体 %d 行のうち (ウ) %d 行" % (n_vn, u_n), hit(1 <= u_n <= 4))
    n_gc = sum(cnt[u"G 連結"].values())
    gcb = cnt[u"G 連結"][u"b"]
    lo9, hi9 = bound_of(cells[u"K-9"][1])
    ac = alt_counts(c)
    gb_alt = ac[u"G 連結 b"][1]
    rows[u"K-9"] = (u"G 連結 %d 行のうち (b) %d 行。封の字どおりに読む別の読みでは (b) %d 行(%d + %d。§3-6)" % (n_gc, gcb, gb_alt, gcb, ac[u"範囲が狭い行"]),
                    split_judge(in_bound(gcb, lo9, hi9), in_bound(gb_alt, lo9, hi9)))
    n_gn = sum(cnt[u"G 単体"].values())
    gnb = cnt[u"G 単体"][u"b"]
    side = gd.get(u"側", 0)
    rows[u"K-10"] = (u"G 単体 %d 行のうち (b) %d 行・違うものが「側」%d 行" % (n_gn, gnb, side), hit(1 <= gnb <= 6 and 1 <= side <= 6))
    ck = cnt[u"V 連結"][u"ケ"] + cnt[u"V 単体"][u"ケ"] + cnt[u"G 連結"][u"c"] + cnt[u"G 単体"][u"c"]
    n_all = n_vc + n_vn + n_gc + n_gn
    rows[u"K-11"] = (u"読んだ %d 行のうち (ケ) + (c) %d 行" % (n_all, ck), hit(0 <= ck <= 13))
    return [(kid, cells[kid][0], cells[kid][1], rows[kid][0], rows[kid][1]) for kid in rows]


def _sep(n):
    return u"|" + u"---|" * n


def side_block(c, side):
    books = c.S[u"本"]
    lines = [u"| 群 | 本 | 切れた | 切れない | うち「札なし」 | うち他の理由 | 字数の合計 | 数の claim | GROUNDED | VALUE_MISMATCH | UNVERIFIABLE | POINTER_NOT_FOUND | GROUNDED / claim | "
             u"POINTER_NOT_FOUND / claim | claim が 0 の本(切れた本のうち) | GROUNDED が 0 の本(切れた本のうち) | VALUE_MISMATCH が 1 以上の本 |", _sep(17)]
    for g in GROUPS + (None,):
        w = recount_side(books, side, g)
        s = w[u"4 state"]
        why = w[u"切れない理由"]
        lines.append(u"| %s | %s |" % (g or u"**計**", u" | ".join([
            fmt(w[u"本"]), fmt(w[u"切れた"]), fmt(w[u"切れない"]), fmt(why[u"札なし"]), fmt(w[u"切れない"] - why[u"札なし"]), fmt(w[u"字数の合計"]), fmt(w[u"claim"]),
            fmt(s[G]), fmt(s[VM]), fmt(s[UNV]), fmt(s[PNF]), pct(s[G], w[u"claim"]), pct(s[PNF], w[u"claim"]),
            fmt(w[u"切れた本のうち claim が 0 の本"]), fmt(w[u"切れた本のうち GROUNDED が 0 の本"]), fmt(w[u"VALUE_MISMATCH が 1 以上の本"])])))
    return lines


def width_lines(c):
    u"""K-6〜K-11 の実測が封の幅のどこに在ったか(幅は封の字から・実測は記録から)。"""
    cells = seal_k_rows(c.seal)
    cnt = dict((lab, collections.Counter(r[4] for r in c.R[u"行"] if r[0] == lab)) for lab in SETS)
    ac = alt_counts(c)
    act = collections.OrderedDict([
        (u"K-6", (cnt[u"V 連結"][u"ア"], None, u"なし")), (u"K-7", (cnt[u"V 連結"][u"ク"] + cnt[u"V 単体"][u"ク"], ac[u"V 連結 ク"][1] + cnt[u"V 単体"][u"ク"], u"V 連結の通し番号 3 を (ク) と読む")),
        (u"K-8", (cnt[u"V 単体"][u"ウ"], None, u"なし")), (u"K-9", (cnt[u"G 連結"][u"b"], ac[u"G 連結 b"][1], u"(a) の決めで入れた 8 行を (b) と読む")),
        (u"K-10", (cnt[u"G 単体"][u"b"], None, u"なし")),
        (u"K-11", (cnt[u"V 連結"][u"ケ"] + cnt[u"V 単体"][u"ケ"] + cnt[u"G 連結"][u"c"] + cnt[u"G 単体"][u"c"], None, u"なし"))])
    lines = [u"| # | 封の幅 | 記録の読みの実測 = 幅の中の位置 | 別の読みの実測 = 幅の中の位置 | 別の読み |", _sep(5)]
    for kid, (n, alt, why) in act.items():
        lo, hi = bound_of(cells[kid][1])
        wtxt = u"%d〜%d 行" % (lo, hi) if hi is not None else u"%d 行以上" % lo
        lines.append(u"| %s | %s | %d 行 = %s | %s | %s |" % (kid, wtxt, n, position(n, lo, hi), (u"%d 行 = %s" % (alt, position(alt, lo, hi)) if alt is not None else u"-"), why))
    return lines


def serial_lines(c):
    lines = [u"| 読みの組 | 通し番号 | 本の # | 文の番号 | 位置 | 記録の型 | 別の読み |", _sep(7)]
    items = [(u"V 連結", n, u"(ク)" if n == 3 else u"(エ)") for n in (2, 3, 13, 22)] + [(u"V 単体", n, u"(エ)") for n in ALT_V_NON] + [(u"G 連結", n, u"(b)・違うものは範囲") for n in ALT_G_CONS]
    for lab, n, alt in items:
        r = [r for r in c.R[u"行"] if r[0] == lab][n - 1]
        lines.append(u"| %s | %d | %d | %d | %d | (%s) | %s |" % (lab, n, r[1], r[2], r[3], r[4], alt))
    return lines


def alt_lines(c):
    ac = alt_counts(c)
    n60 = ac[u"G 連結 60 行"]
    lines = [u"| 欄 | 記録の読み | 別の読み |", _sep(3)]
    lines.append(u"| G 連結の (b)(%d 行のうち) | %d | %d |" % (n60, ac[u"G 連結 b"][0], ac[u"G 連結 b"][1]))
    lines.append(u"| G 連結の (b) の割合 | %s | %s |" % (pct(ac[u"G 連結 b"][0], n60), pct(ac[u"G 連結 b"][1], n60)))
    lines.append(u"| G 連結の (a) | %d | %d |" % ac[u"G 連結 a"])
    lines.append(u"| 値が同じで、文の言う範囲が科目の全体より狭い行(G 連結 %d 行のうち) | - | %d 行(%s) |" % (n60, ac[u"範囲が狭い行"], pct(ac[u"範囲が狭い行"], n60)))
    for lab, key in ((u"V 連結の (オ)", u"V 連結 オ"), (u"V 連結の (エ)", u"V 連結 エ"), (u"V 単体の (オ)", u"V 単体 オ"), (u"V 単体の (エ)", u"V 単体 エ"), (u"V 連結の (ク)", u"V 連結 ク")):
        lines.append(u"| %s | %d | %d |" % ((lab,) + ac[key]))
    return lines


def build_blocks(c):
    S, R = c.S, c.R
    books = S[u"本"]
    blocks = collections.OrderedDict()
    lines = [u"| # | 欄 | 予測(封) | 実測 | 判定 |", _sep(5)]
    for r in pred_table(c):
        lines.append(u"| %s | %s | %s | %s | %s |" % r)
    blocks[u"pred"] = lines
    blocks[u"width"] = width_lines(c)
    blocks[u"cons"] = side_block(c, CONS)
    blocks[u"non"] = side_block(c, NON)
    lines = [u"| 文 | 群 | GROUNDED 真 | GROUNDED 偽 | VALUE_MISMATCH 真 | VALUE_MISMATCH 偽 | UNVERIFIABLE 真 | UNVERIFIABLE 偽 | POINTER_NOT_FOUND 真 | POINTER_NOT_FOUND 偽 |", _sep(10)]
    for side in SIDES:
        for g in GROUPS + (None,):
            t = recount_side(books, side, g)[TEN_KEY]
            lines.append(u"| %s | %s | %s |" % (side, g or u"**計**", u" | ".join(fmt(t[s][v]) for s in STATES for v in (TRUE, FALSE))))
    blocks[u"ten"] = lines
    wc, wn = recount_side(books, CONS), recount_side(books, NON)
    lines = [u"| state | reason | 連結(計) | 単体(計) |", _sep(4)]
    for s in (UNV, PNF):
        for k in sorted(set(wc[u"reason"][s]) | set(wn[u"reason"][s])):
            lines.append(u"| %s | %s | %s | %s |" % (s, k, fmt(wc[u"reason"][s].get(k, 0)), fmt(wn[u"reason"][s].get(k, 0))))
    blocks[u"reasons"] = lines
    vc, vn = wc[u"VALUE_MISMATCH の内訳"], wn[u"VALUE_MISMATCH の内訳"]
    lines = [u"| 欄(VALUE_MISMATCH の行) | 連結(計) | 単体(計) |", _sep(3)]
    for k, f in ((u"VALUE_MISMATCH の行", u"行"), (u"導出(formula)", u"導出(formula)"), (u"直接", u"直接"), (u"span に % を含む", u"% の数"), (u"span に % を含まない", u"円族の数"),
                 (u"両期の fact を引く a−b(円)", u"両期の fact を引く a−b(円)"), (u"単位の族が %", u"単位の族が %"), (u"単位の族が円族", u"単位の族が円族"), (u"単位の族が他", u"単位の族が他")):
        lines.append(u"| %s | %s | %s |" % (k, fmt(vc[f]), fmt(vn[f])))
    for k in VM_PERIOD_KEYS:
        lines.append(u"| pointer の期 %s | %s | %s |" % (k, fmt(vc[u"pointer の期"][k]), fmt(vn[u"pointer の期"][k])))
    blocks[u"vm"] = lines
    exp, n_g = expected_reading(S)
    lines = [u"| 読みの組 | 引き方 | 母の行 | 読んだ行 |", _sep(4)]
    lines.append(u"| V 連結 | 連結の VALUE_MISMATCH の全部 | %s | %s |" % (fmt(wc[u"4 state"][VM]), fmt(len(exp[u"V 連結"]))))
    lines.append(u"| V 単体 | 単体の VALUE_MISMATCH の全部 | %s | %s |" % (fmt(wn[u"4 state"][VM]), fmt(len(exp[u"V 単体"]))))
    lines.append(u"| G 連結 | 連結の GROUNDED から種 `%d` で %d 行を引く | %s | %s |" % (SEED, DRAW_N, fmt(n_g), fmt(len(exp[u"G 連結"]))))
    lines.append(u"| G 単体 | 単体の GROUNDED の全部 | %s | %s |" % (fmt(wn[u"4 state"][G]), fmt(len(exp[u"G 単体"]))))
    lines.append(u"| **計** | | | %s |" % fmt(sum(len(v) for v in exp.values())))
    blocks[u"read"] = lines
    tt = R[u"型の字"]
    cnt = dict((lab, collections.Counter(r[4] for r in R[u"行"] if r[0] == lab)) for lab in SETS)
    nv = dict((lab, sum(cnt[lab].values())) for lab in SETS)
    lines = [u"| 型 | 封の字 | V 連結 | V 単体 | V 連結の読んだ行のうち | V 単体の読んだ行のうち |", _sep(6)]
    for t in V_TYPES:
        lines.append(u"| (%s) | %s | %s | %s | %s | %s |" % (t, tt[u"V"][t], fmt(cnt[u"V 連結"][t]), fmt(cnt[u"V 単体"][t]), pct(cnt[u"V 連結"][t], nv[u"V 連結"]), pct(cnt[u"V 単体"][t], nv[u"V 単体"])))
    lines.append(u"| **計** | | %s | %s | | |" % (fmt(nv[u"V 連結"]), fmt(nv[u"V 単体"])))
    blocks[u"types_v"] = lines
    lines = [u"| 型 | 封の字 | G 連結 | G 単体 | G 連結の読んだ行のうち | G 単体の読んだ行のうち |", _sep(6)]
    for t in G_TYPES:
        lines.append(u"| (%s) | %s | %s | %s | %s | %s |" % (t, tt[u"G"][t], fmt(cnt[u"G 連結"][t]), fmt(cnt[u"G 単体"][t]), pct(cnt[u"G 連結"][t], nv[u"G 連結"]), pct(cnt[u"G 単体"][t], nv[u"G 単体"])))
    lines.append(u"| **計** | | %s | %s | | |" % (fmt(nv[u"G 連結"]), fmt(nv[u"G 単体"])))
    blocks[u"types_g"] = lines
    lines = [u"| (b) の違うもの | G 連結 | G 単体 |", _sep(3)]
    for d in DIFFS:
        lines.append(u"| %s | %s | %s |" % (d, fmt(sum(1 for r in R[u"行"] if r[0] == u"G 連結" and r[4] == u"b" and r[5] == d)), fmt(sum(1 for r in R[u"行"] if r[0] == u"G 単体" and r[4] == u"b" and r[5] == d))))
    blocks[u"types_b"] = lines
    j = read_join(c)
    lines = [u"| 読みの組 | 型 | 行 | 10 欄目が真 | 10 欄目が偽 | 結んだ先が導出の行 | pointer の期が前期の行 |", _sep(7)]
    for lab in SETS:
        for t in type_set(lab):
            sel = [r for r in j if r[0] == lab and r[4] == t]
            if sel:
                lines.append(u"| %s | (%s) | %s | %s | %s | %s | %s |" % (lab, t, fmt(len(sel)), fmt(sum(1 for r in sel if r[6][9] is True)), fmt(sum(1 for r in sel if r[6][9] is False)),
                                                                     fmt(sum(1 for r in sel if r[6][5] is True)), fmt(sum(1 for r in sel if r[6][4] == u"Prior1Year"))))
    blocks[u"cross"] = lines
    lines = [u"| 読みの組 | 読んだ行の通し番号 | 本の # | 文の番号 | 位置 | 型 |", _sep(6)]
    vrows = [r for r in R[u"行"] if r[0] == u"V 連結"]
    for k in (3, 21):
        r = vrows[k - 1]
        lines.append(u"| V 連結 | %d | %d | %d | %d | (%s) |" % (k, r[1], r[2], r[3], r[4]))
    blocks[u"hesitant"] = lines
    blocks[u"serials"] = serial_lines(c)
    blocks[u"alt"] = alt_lines(c)
    lines = [u"| 記録 | sha256 |", _sep(2)]
    for rel in RECORD_RELS:
        lines.append(u"| `%s` | `%s` |" % (rel, sha256_text_of_record(c, rel)))
    blocks[u"sha"] = lines
    return blocks


def sha256_text_of_record(c, rel):
    return hashlib.sha256(c.texts[rel]).hexdigest()


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
    t = re.sub(r"\b[A-Z]+-?\d+[A-Z]*\b", u"", t)                      # K-10・P33E などの名前
    t = re.sub(u"§[0-9\\-]+", u"", t)
    return t


def derived_numbers(seal):
    u"""記録の塊に出ない数のうち、封の字から作れるもの(封 §6 の 10 項に出る数)。"""
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
        out.append(u"文書: 塊の名前・数が 13 個(%s)の順でない" % u"・".join(BLOCK_NAMES))
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
        if ln not in doc:
            out.append(u"文書: 封 §6 の %d 番目の字を写していない" % i)
    k5 = u"AUDIT_CORE_KAM_REMEASURE=1"
    if k5 not in doc:
        out.append(u"文書: 測り直しの環境変数を言っていない")
    out += fragment_problems(c)
    return out


SECTIONS = collections.OrderedDict([(u"s1", (u"## §1", u"## §2")), (u"s2", (u"## §2", u"## §3")), (u"s3", (u"## §3", u"## §4")), (u"s4", (u"## §4", u"## §5")), (u"s5", (u"## §5", u"## §6")),
                                    (u"s6", (u"## §6", u"## §7"))])
STALE_PHRASES = (u"11 行とも当たり", u"11 本とも当たり", u"外れは 0 行", u"(エ) は 0 行", u"理由は記録に無く", u"外れは 0")
NOT_CALLED_RE = re.compile(u"\\(ク\\)[^。\n]{0,8}(?:は|が|を|=|＝) *「?食い違い")


def section_of(doc, key):
    a, b = SECTIONS[key]
    return doc[doc.index(a):doc.index(b)] if a in doc and b in doc else u""


def prose_fragments(c):
    u"""本文の中の数を持つ文の断片(節 → 断片)。数は記録の行から数え直した値で作る。字と数の両方が合わなければ赤。"""
    books = c.S[u"本"]
    a, b = recount_side(books, CONS), recount_side(books, NON)
    sa, sb = a[u"4 state"], b[u"4 state"]
    cnt = dict((lab, collections.Counter(r[4] for r in c.R[u"行"] if r[0] == lab)) for lab in SETS)
    ac = alt_counts(c)
    j = read_join(c)
    narrow, n60 = ac[u"範囲が狭い行"], ac[u"G 連結 60 行"]
    tb = b[TEN_KEY]
    g_false = [r for r in j if r[0] == u"G 単体" and r[6][9] is False]
    g_false_ok = [r for r in g_false if r[4] == u"b" and r[5] == u"側"]
    v_false = [r for r in j if r[0] == u"V 単体" and r[6][9] is False]
    prior_c = sum(1 for r in j if r[0] == u"V 連結" and r[6][4] == u"Prior1Year")
    prior_n = sum(1 for r in j if r[0] == u"V 単体" and r[6][4] == u"Prior1Year")
    used = [tt for tt in V_TYPES if cnt[u"V 連結"][tt] + cnt[u"V 単体"][tt] > 0]
    preds = pred_table(c)
    n_hit = sum(1 for r in preds if r[4].startswith(u"当たり"))
    n_split = sum(1 for r in preds if r[4].startswith(u"読みで割れた"))
    n_miss = sum(1 for r in preds if r[4].startswith(u"外れ"))
    hi9 = bound_of(seal_k_rows(c.seal)[u"K-9"][1])[1]
    F = collections.OrderedDict((k, []) for k in SECTIONS)
    F[u"s1"] += [u"当たり %d・読みで割れた %d・外れ %d。" % (n_hit, n_split, n_miss), u"**K-9 は当たりとも外れとも書かない**", u"外れ方の「%d 行以上」に当たる" % (hi9 + 1),
                 u"**読みを結果の後に選んで当たりにした、と読める余地がある**", u"同じ偏りが 2 回目」に当たる", u"記録の型は結果を見てから付け直していない"]
    F[u"s2"] += [u"連結の文で数の claim は %s、結べた(GROUNDED)は %s(%s)で、いちばん多い state は POINTER_NOT_FOUND の %s(%s)。切れない %d 本は全部「札なし」" % (
                     fmt(a[u"claim"]), fmt(sa[G]), pct(sa[G], a[u"claim"]), fmt(sa[PNF]), pct(sa[PNF], a[u"claim"]), a[u"切れない"]),
                 u"切れた %d 本のうち、claim が 0 の本は %d、GROUNDED が 0 の本は %d、VALUE_MISMATCH が 1 以上の本は %d" % (
                     a[u"切れた"], a[u"切れた本のうち claim が 0 の本"], a[u"切れた本のうち GROUNDED が 0 の本"], a[u"VALUE_MISMATCH が 1 以上の本"]),
                 u"単体の文で数の claim は %s、結べたのは %s(%s)、POINTER_NOT_FOUND は %s(%s)。切れない %d 本は全部「札なし」。切れた %d 本のうち、claim が 0 の本は %d、GROUNDED が 0 の本は %d、VALUE_MISMATCH が 1 以上の本は %d" % (
                     fmt(b[u"claim"]), fmt(sb[G]), pct(sb[G], b[u"claim"]), fmt(sb[PNF]), pct(sb[PNF], b[u"claim"]), b[u"切れない"], b[u"切れた"],
                     b[u"切れた本のうち claim が 0 の本"], b[u"切れた本のうち GROUNDED が 0 の本"], b[u"VALUE_MISMATCH が 1 以上の本"]),
                 u"GROUNDED の %d 行のうち %d 行が真・%d 行が偽、VALUE_MISMATCH の %d 行のうち %d 行が真・%d 行が偽" % (
                     sb[G], tb[G][TRUE], tb[G][FALSE], sb[VM], tb[VM][TRUE], tb[VM][FALSE]),
                 u"「値が違う」は連結 %d 行・単体 %d 行で、全部が直接(導出は %d)" % (sa[VM], sb[VM], a[u"VALUE_MISMATCH の内訳"][u"導出(formula)"] + b[u"VALUE_MISMATCH の内訳"][u"導出(formula)"])]
    F[u"s3"] += [u"(ク) 本当の差の候補は、記録の読みでは連結 %d 行・単体 %d 行" % (cnt[u"V 連結"][u"ク"], cnt[u"V 単体"][u"ク"]),
                 u"記録の読みで使われた型は %s の %d つだけ" % (u"・".join(u"(%s)" % tt for tt in used), len(used)),
                 u"(エ) は記録の読みでは %d 行" % (cnt[u"V 連結"][u"エ"] + cnt[u"V 単体"][u"エ"]),
                 u"pointer の期が前期の「値が違う」%d 行(連結 %d 行・単体 %d 行)は、記録では全部 (オ)" % (prior_c + prior_n, prior_c, prior_n),
                 u"(オ) に入れた理由は §4、(エ) と読んだ数は §3-6",
                 u"(b) は記録の読みでは連結 %d 行(違うものは「項目」)・単体 %d 行(違うものは全部「側」)" % (cnt[u"G 連結"][u"b"], cnt[u"G 単体"][u"b"]),
                 u"G 連結の (a) %d 行のうち %d 行" % (cnt[u"G 連結"][u"a"], narrow),
                 u"(b) は %d + %d = %d 行" % (cnt[u"G 連結"][u"b"], narrow, ac[u"G 連結 b"][1]),
                 u"(エ) が V 連結 %d 行・V 単体 %d 行" % (ac[u"V 連結 エ"][1], ac[u"V 単体 エ"][1]),
                 u"(ク) は %d 行" % ac[u"V 連結 ク"][1]]
    F[u"s4"] += [u"V 連結の通し番号 3 は、全体の数を言う文がセグメントの側の fact に結んだ", u"V 連結の通し番号 21 は、その企業結合の分を言う数と読んで (ア)", u"側の違い (ウ) を先に取った",
                 u"(a) の決めで入れた行は %d 行(G 連結の通し番号 9・11・13・26・37・44・50・58)" % narrow,
                 u"字どおりに範囲の違いと読めば %d 行とも (b)・違うものは「範囲」で、(b) は %d + %d = %d 行(%d 行のうち)" % (narrow, cnt[u"G 連結"][u"b"], narrow, ac[u"G 連結 b"][1], n60),
                 u"どちらの読みが封の字に合うかは司令塔が決めきれない", u"記録の型は付け直していない",
                 u"(V 連結の通し番号 2・13・22、V 単体の通し番号 5・7)は、記録では (オ)",
                 u"文の数は「繰延税金資産の総額(評価性引当額を引く前)」で、結んだ fact は引当を引いた後の額の科目", u"ただし結んだ fact の期は前期で、(エ) の字にも当たる",
                 u"(エ) と読めば V 連結は (オ) %d・(エ) %d、V 単体は (オ) %d・(エ) %d" % (ac[u"V 連結 オ"][1], ac[u"V 連結 エ"][1], ac[u"V 単体 オ"][1], ac[u"V 単体 エ"][1]),
                 u"K-6〜K-8 はどちらの読みでも動かない", u"(ク)・(ケ)・(c) は記録の読みでは 0 行"]
    F[u"s5"] += [u"(連結 %s・単体 %s。§2-1・§2-2)" % (pct(sa[G], a[u"claim"]), pct(sb[G], b[u"claim"])), u"(連結 %s・単体 %s)で、止まった理由" % (pct(sa[PNF], a[u"claim"]), pct(sb[PNF], b[u"claim"])),
                 u"G 単体で 10 欄目が偽の %d 行は、読んだ全部が連結の側の fact に結んでいた(%d 行のうち %d 行。" % (len(g_false), len(g_false), len(g_false_ok)),
                 u"V 単体の 10 欄目が偽の %d 行も、全部 (ウ)" % len(v_false),
                 u"単体の「結べた」%d 行のうち、側が合うと読んだのは %d 行" % (sum(cnt[u"G 単体"].values()), cnt[u"G 単体"][u"a"]),
                 u"「監査報告書の文と同じ有報の fact の食い違い」を 1 件も見つけていない", u"(ク) は候補であり、食い違いとは呼ばない",
                 u"V 連結の通し番号 3 は、文が当期の全体の数を言っているように読め", u"(ク) と読めば (ク) は %d 行で、K-7 は幅の内のまま" % ac[u"V 連結 ク"][1],
                 u"「(ク) 0 行 = 候補を 1 件も見つけていない」は記録の読みでの話", u"この 1 行は候補になり得る(紙面でも前後の文でも確かめていない)",
                 u"(%d 行のうち %d 行。種で引いた)" % (len([1 for b_ in books for r in b_[CONS][u"行"] if r[2] == G]), n60),
                 u"値が同じで、文の言う範囲が科目の全体より狭い行が %d 行 = %s" % (narrow, pct(narrow, n60)), u"engine は範囲を見分けていない",
                 u"切れない本(連結 %d・単体 %d)は測れていない" % (a[u"切れない"], b[u"切れない"])]
    F[u"s6"] += [u"採用 / 不採用の判定は無い", u"人間が決める", u"(連結は読んだ %d 行のうち %d 行・単体は読んだ %d 行のうち %d 行)" % (n60, cnt[u"G 連結"][u"b"], sum(cnt[u"G 単体"].values()), cnt[u"G 単体"][u"b"]),
                 u"(別の読みでは連結 %d 行。§3-6)" % ac[u"G 連結 b"][1]]
    return F


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
    if re.search(u"(?<!記録の読みで)使われた型は", doc):
        out.append(u"文書: 「使われた型は」に「記録の読みで」が付いていない")
    if NOT_CALLED_RE.search(doc):
        out.append(u"文書: (ク) を食い違いと呼んでいる")
    if u"採用" in doc.replace(u"採用 / 不採用の判定は無い", u""):
        out.append(u"文書: 採用の字が「採用 / 不採用の判定は無い」の外にある")
    found = SERIAL_RE.findall(doc)
    if any(f not in SERIAL_PHRASES for f in found):
        out.append(u"文書: 字で留めた一覧に無い通し番号がある: %s" % u",".join(sorted(set(f for f in found if f not in SERIAL_PHRASES))))
    s4 = section_of(doc, u"s4")
    for ph in SERIAL_PHRASES:
        if ph not in s4:
            out.append(u"文書: §4 が通し番号の一覧を言っていない: %s" % ph)
    return out


# ======================================================================================================
# i. 順序・engine
def order_others():
    return list(RECORD_RELS) + [DOC_REL, GATE_REL]


def order_problems_real(root=REPO):
    return PR.order_problems(root, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, [SCRIPT_REL], order_others())


def engine_problems(root=REPO):
    u"""engine・lib・仕掛け・前の便は封の commit から 0 行。script は足した commit(e6f01e24)から 0 行(未 commit の編集も見る)。"""
    out = list(SG.engine_since_seal_problems(root))
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
    (u"pop", population_problems),
    (u"states", states_problems),
    (u"types", types_problems),
    (u"cross", cross_problems),
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


def first_row(c, side, pred):
    for b in c.S[u"本"]:
        for r in b[side][u"行"]:
            if pred(r):
                return b, r
    raise AssertionError(u"該当する行が無い")


def types_row(c, lab, pred=lambda r: True):
    return [r for r in c.R[u"行"] if r[0] == lab and pred(r)][0]


def doc_digit(c, name):
    lines = doc_blocks(c.doc)[name]
    for i, ln in enumerate(lines):
        m = re.search(r"\d", ln) if i >= 2 else None
        if m:
            idx = c.doc.index(u"\n".join(lines))
            off = idx + len(u"\n".join(lines[:i])) + (1 if i else 0) + m.start()
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
M(u"b13 step の字", u"prov", lambda c: c.P.__setitem__(u"step", u"KAM"))
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
# c. 母集団
M(u"c1 母集団の行を 1 つ消す", u"pop", lambda c: c.P[u"行"].pop())
M(u"c2 母集団の行の入れ替え", u"pop", lambda c: c.P[u"行"].insert(0, c.P[u"行"].pop(1)))
M(u"c3 母集団の sha256", u"pop", lambda c: c.P[u"行"][5].__setitem__(2, flip(c.P[u"行"][5][2])))
M(u"c4 母集団の byte 数", u"pop", lambda c: c.P[u"行"][5].__setitem__(3, c.P[u"行"][5][3] + 1))
M(u"c5 母集団の群の欄", u"pop", lambda c: c.P[u"行"][5].__setitem__(1, u"乙"))
M(u"c6 byte 数の合計", u"pop", lambda c: bump(c.P, u"byte 数の合計"))
M(u"c7 群の本の数", u"pop", lambda c: c.P[u"群"].__setitem__(u"丙", 93))
M(u"c8 母集団の行の欄", u"pop", lambda c: c.P[u"行の欄"].reverse())
M(u"c9 byte 数が 0", u"pop", lambda c: c.P[u"行"][5].__setitem__(3, 0))
# d. 判定の記録
M(u"d1 集計の連結計の GROUNDED", u"states", lambda c: bump(c.S[u"集計"][CONS][u"計"][u"4 state"], G))
M(u"d2 集計の単体計の claim", u"states", lambda c: bump(c.S[u"集計"][NON][u"計"], u"claim", -1))
M(u"d3 ある行の state を GROUNDED から VALUE_MISMATCH に変える(reason は None のまま)", u"states", lambda c: first_row(c, CONS, lambda r: r[2] == G)[1].__setitem__(2, VM))
M(u"d4 行を 1 つ消す(claim も 1 減らす)", u"states", lambda c: (lambda b: (b[CONS][u"行"].pop(0), bump(b[CONS], u"claim", -1)))(first_row(c, CONS, lambda r: True)[0]))
M(u"d5 reason の内訳を 1 つ動かす", u"states", lambda c: bump(c.S[u"集計"][CONS][u"計"][u"reason"][UNV], u"no_subject"))
M(u"d6 VALUE_MISMATCH の内訳の % の数", u"states", lambda c: bump(c.S[u"集計"][CONS][u"計"][u"VALUE_MISMATCH の内訳"], u"% の数"))
M(u"d7 10 欄目の数(単体の GROUNDED の真)", u"states", lambda c: bump(c.S[u"集計"][NON][u"計"][TEN_KEY][G], TRUE))
M(u"d8 切れた本のうち claim が 0 の本", u"states", lambda c: bump(c.S[u"集計"][NON][u"計"], u"切れた本のうち claim が 0 の本"))
M(u"d9 切れた本のうち GROUNDED が 0 の本", u"states", lambda c: bump(c.S[u"集計"][CONS][u"丙"], u"切れた本のうち GROUNDED が 0 の本"))
M(u"d10 VALUE_MISMATCH が 1 以上の本", u"states", lambda c: bump(c.S[u"集計"][NON][u"乙"], u"VALUE_MISMATCH が 1 以上の本"))
M(u"d11 字数の合計", u"states", lambda c: bump(c.S[u"集計"][CONS][u"甲"], u"字数の合計"))
M(u"d12 切れない理由", u"states", lambda c: bump(c.S[u"集計"][CONS][u"計"][u"切れない理由"], u"札なし", -1))
M(u"d13 pointer の期の内訳", u"states", lambda c: bump(c.S[u"集計"][CONS][u"計"][u"VALUE_MISMATCH の内訳"][u"pointer の期"], u"Prior1Year"))
M(u"d14 集計の欄が 1 つ消える", u"states", lambda c: c.S[u"集計"][CONS][u"計"].pop(u"claim と raw の並びが対応しなかった本"))
M(u"d15 集計の群が消える", u"states", lambda c: c.S[u"集計"][NON].pop(u"丙"))
M(u"d16 本の ZIP の sha256", u"states", lambda c: book(c, 60).__setitem__(u"ZIP の sha256", flip(book(c, 60)[u"ZIP の sha256"])))
M(u"d17 本が 1 本足りない", u"states", lambda c: c.S[u"本"].pop())
M(u"d18 本の群", u"states", lambda c: book(c, 60).__setitem__(u"群", u"乙"))
M(u"d19 本の claim", u"states", lambda c: bump(first_row(c, NON, lambda r: True)[0][NON], u"claim"))
M(u"d20 切れない本に行を入れる", u"states", lambda c: (lambda b: b[CONS][u"行"].append([1, 1, G, None, u"CurrentYear", False, u"円族", False, False, False]))(book(c, 6)))
M(u"d21 切れた本の理由に字を入れる", u"states", lambda c: book(c, 60)[CONS].__setitem__(u"理由", u"札なし"))
M(u"d22 切れない本の理由が語彙の外", u"states", lambda c: book(c, 6)[CONS].__setitem__(u"理由", u"その他"))
M(u"d23 行が 9 欄", u"states", lambda c: first_row(c, CONS, lambda r: True)[1].pop())
M(u"d24 行の単位の族が語彙の外", u"states", lambda c: first_row(c, CONS, lambda r: True)[1].__setitem__(6, u"ドル"))
M(u"d25 10 欄目を反転(単体の GROUNDED)", u"states", lambda c: (lambda r: r.__setitem__(9, not r[9]))(first_row(c, NON, lambda r: r[2] == G and r[9] is True)[1]))
M(u"d26 GROUNDED の行に reason を入れる", u"states", lambda c: first_row(c, CONS, lambda r: r[2] == G)[1].__setitem__(3, u"no_subject"))
M(u"d27 VALUE_MISMATCH でない行の reason を None にする", u"states", lambda c: first_row(c, CONS, lambda r: r[2] == UNV)[1].__setitem__(3, None))
M(u"d28 行の並び(同じ位置を 2 回)", u"states", lambda c: (lambda b: b[CONS][u"行"].insert(1, list(b[CONS][u"行"][0])))(first_row(c, CONS, lambda r: True)[0]))
M(u"d29 本の欄が 1 つ増える", u"states", lambda c: book(c, 3).__setitem__(u"余分", 1))
M(u"d30 本の数の欄", u"states", lambda c: bump(c.S, u"本の数", -1))
M(u"d31 字数が 0", u"states", lambda c: book(c, 60)[CONS].__setitem__(u"字数", 0))
M(u"d32 対応が真でない", u"states", lambda c: book(c, 60)[CONS].__setitem__(u"対応", False))
M(u"d33 行の state の語", u"states", lambda c: first_row(c, CONS, lambda r: r[2] == G)[1].__setitem__(2, u"GROUNDED "))
M(u"d34 集計の VALUE_MISMATCH の内訳の欄の名前", u"states", lambda c: c.S[u"集計"][NON][u"計"][u"VALUE_MISMATCH の内訳"].pop(u"単位の族が他"))
# e. 読みの記録
M(u"e1 型を 1 つ変える(集計は変えない)", u"types", lambda c: types_row(c, u"V 連結").__setitem__(4, u"オ" if types_row(c, u"V 連結")[4] != u"オ" else u"ア"))
M(u"e2 型の集計(V 連結の ア)", u"types", lambda c: bump(c.R[u"型の集計"][u"V 連結"], u"ア"))
M(u"e3 型の集計(G 単体の b)", u"types", lambda c: bump(c.R[u"型の集計"][u"G 単体"], u"b", -1))
M(u"e4 b の違うものの集計", u"types", lambda c: bump(c.R[u"b の違うものの集計"][u"G 単体"], u"側", -1))
M(u"e5 行を 1 つ消す", u"types", lambda c: c.R[u"行"].pop(50))
M(u"e6 行の入れ替え(組の順)", u"types", lambda c: c.R[u"行"].insert(0, c.R[u"行"].pop()))
M(u"e7 G 連結の標本の行の位置を変える", u"types", lambda c: types_row(c, u"G 連結").__setitem__(3, types_row(c, u"G 連結")[3] + 1))
M(u"e8 G 連結の標本が先頭から 60 行", u"types", lambda c: [r.__setitem__(slice(1, 4), s) for r, s in zip([r for r in c.R[u"行"] if r[0] == u"G 連結"], (lambda rows: [list(x) for x in rows[:60]])(
    [(b[u"#"], r[0], r[1]) for b in c.S[u"本"] for r in b[CONS][u"行"] if r[2] == G]))])
M(u"e9 引く数", u"types", lambda c: c.R[u"読む行の規則"].__setitem__(u"引く数", 59))
M(u"e10 種", u"types", lambda c: c.R[u"読む行の規則"].__setitem__(u"種", 20261114))
M(u"e11 読む行の数の合計", u"types", lambda c: bump(c.R[u"読む行の規則"], u"読む行の数の合計"))
M(u"e12 G 連結の行の数", u"types", lambda c: bump(c.R[u"読む行の規則"], u"G 連結の行の数"))
M(u"e13 b なのに違うものが無い", u"types", lambda c: types_row(c, u"G 単体", lambda r: r[4] == u"b").__setitem__(5, None))
M(u"e14 a に違うものが付く", u"types", lambda c: types_row(c, u"G 単体", lambda r: r[4] == u"a").__setitem__(5, u"側"))
M(u"e15 違うものが 4 つの外", u"types", lambda c: types_row(c, u"G 単体", lambda r: r[4] == u"b").__setitem__(5, u"色"))
M(u"e16 G の行に V の型", u"types", lambda c: types_row(c, u"G 単体", lambda r: r[4] == u"a").__setitem__(4, u"ア"))
M(u"e17 V の行に G の型", u"types", lambda c: types_row(c, u"V 連結").__setitem__(4, u"a"))
M(u"e18 組の取り違え(V 連結の行を V 単体にする)", u"types", lambda c: types_row(c, u"V 連結").__setitem__(0, u"V 単体"))
M(u"e19 V の行の本の #(VALUE_MISMATCH でない行を指す)", u"types", lambda c: types_row(c, u"V 連結").__setitem__(3, types_row(c, u"V 連結")[3] + 1))
M(u"e20 型の字(V 連結の オ)", u"types", lambda c: c.R[u"型の字"][u"V"].__setitem__(u"オ", u"読んでも分けられる"))
M(u"e21 読む行の数(V 単体)", u"types", lambda c: c.R[u"読む行の規則"][u"読む行の数"].__setitem__(u"V 単体", 7))
M(u"e22 型の集計の欄が 1 つ消える", u"types", lambda c: c.R[u"型の集計"][u"G 連結"].pop(u"c"))
M(u"e23 G 単体の行を 1 つ消す", u"types", lambda c: c.R[u"行"].remove(types_row(c, u"G 単体")))
M(u"e24 V 単体の行を 1 つ消す(集計も)", u"types", lambda c: (c.R[u"行"].remove(types_row(c, u"V 単体")), bump(c.R[u"型の集計"][u"V 単体"], u"ア", -1)))
# f. 交差
M(u"f1 G 単体の b を a にする", u"cross", lambda c: types_row(c, u"G 単体", lambda r: r[4] == u"b").__setitem__(4, u"a") or types_row(c, u"G 単体", lambda r: r[4] == u"a" and r[5] is None).__setitem__(5, None))
M(u"f2 G 単体の b の違うものを範囲にする", u"cross", lambda c: types_row(c, u"G 単体", lambda r: r[4] == u"b").__setitem__(5, u"範囲"))
M(u"f3 V 単体の (ウ) を (ア) にする", u"cross", lambda c: types_row(c, u"V 単体", lambda r: r[4] == u"ウ").__setitem__(4, u"ア"))
M(u"f4 V 単体の (ア) を (ウ) にする", u"cross", lambda c: types_row(c, u"V 単体", lambda r: r[4] == u"ア").__setitem__(4, u"ウ"))
M(u"f5 10 欄目が偽の単体の行の本の連結の切り出しを落とす", u"cross", lambda c: (lambda n: book(c, n)[CONS].__setitem__(u"切り出し", u"切れない"))(types_row(c, u"V 単体", lambda r: r[4] == u"ウ")[1]))
M(u"f6 連結の行の 10 欄目を真にする", u"cross", lambda c: (lambda r: r.__setitem__(9, True))(first_row(c, CONS, lambda r: r[2] == G and (r[0], r[1]) == (types_row(c, u"G 連結")[2], types_row(c, u"G 連結")[3]))[1]))
M(u"f7 G 単体の b の導出の欄", u"cross", lambda c: [r.__setitem__(5, False) for b in c.S[u"本"] for r in b[NON][u"行"] if r[2] == G and r[5] is True])
# g. clean
M(u"g1 key_leaks に 1 つ", u"clean", lambda c: c.S.__setitem__(u"key_leaks", [u"x"]))
M(u"g2 値の欄 value を持つ", u"clean", lambda c: c.S.__setitem__(u"value", 1))
M(u"g3 span の欄", u"clean", lambda c: c.R.__setitem__(u"span", u"x"))
M(u"g4 読みの行に文字の葉", u"clean", lambda c: c.R[u"行"][0].append(u"売上高は1,234百万円となりました"))
M(u"g5 本の欄に会社名らしい字", u"clean", lambda c: book(c, 3)[CONS].__setitem__(u"理由", u"㈱x"))
M(u"g6 長い日本語の文", u"clean", lambda c: c.R.__setitem__(u"盲検", u"当社の売上高は前期に比べて増加し、営業利益も増加しました。通期の見通しは据え置きます。これは文です"))
M(u"g7 pointer の字", u"clean", lambda c: c.S[u"集計"].__setitem__(u"メモ", u"jppfs_cor:NetSales"))
M(u"g8 証券コードの形の字", u"clean", lambda c: book(c, 3)[CONS].__setitem__(u"理由", u"1234"))
M(u"g9 docID の形の字", u"clean", lambda c: c.P.__setitem__(u"範囲", u"S" + u"100ABCD"))
M(u"g10 監査法人の名らしい字", u"clean", lambda c: c.P.__setitem__(u"範囲", u"あずさ"))
M(u"g11 行の欄に要素名", u"clean", lambda c: first_row(c, CONS, lambda r: True)[1].append(u"xbrl:Element"))
M(u"g12 長い欄の名前", u"clean", lambda c: c.S.__setitem__(u"あ" * 61, 1))
M(u"g13 states の行の字が長い", u"clean", lambda c: first_row(c, CONS, lambda r: r[3] is not None)[1].__setitem__(3, u"x" * 41))
# h. 文書
for _i, _n in enumerate(BLOCK_NAMES):
    M(u"h%d 塊 %s の数字 1 つ" % (_i + 1, _n), u"doc", (lambda n: (lambda c: doc_digit(c, n)))(_n))
M(u"h14 塊の名前を変える", u"doc", doc_replace(u"<!-- 門:start read -->", u"<!-- 門:start readx -->"))
M(u"h15 知らない塊", u"doc", lambda c: setattr(c, "doc", c.doc + u"\n<!-- 門:start zz -->\n|a|\n<!-- 門:end -->\n"))
M(u"h16 散文に記録に無い数", u"doc", lambda c: setattr(c, "doc", c.doc + u"\n散文の数 98765 件。\n"))
M(u"h17 漢数字で逃がす", u"doc", lambda c: setattr(c, "doc", c.doc + u"\n百三十三本。\n"))
M(u"h18 禁止語", u"doc", lambda c: setattr(c, "doc", c.doc + u"\n人の目で見た。\n"))
M(u"h19 docID の形", u"doc", lambda c: setattr(c, "doc", c.doc + u"\nS" + u"100ABCD\n"))
M(u"h20 会社名らしい字", u"doc", lambda c: setattr(c, "doc", c.doc + u"\n株式会社\n"))
M(u"h21 監査法人の名らしい字", u"doc", lambda c: setattr(c, "doc", c.doc + u"\nあずさ\n"))
M(u"h22 pointer の字", u"doc", lambda c: setattr(c, "doc", c.doc + u"\njppfs_cor:NetSales\n"))
for _j, _ph in enumerate((u"AI の席", u"人は読んでいない", u"盲検ではない", u"紙面", u"候補", u"測っていない", u"足さない", u"採用 / 不採用の判定は無い", u"食い違い")):
    M(u"h%d 必要な語(%s)を消す" % (23 + _j, _ph), u"doc", (lambda ph: (lambda c: setattr(c, "doc", c.doc.replace(ph, u"")))) (_ph))
M(u"h32 封の commit を言わない", u"doc", lambda c: setattr(c, "doc", c.doc.replace(SEAL_COMMIT_SHORT, u"")))
M(u"h33 script の commit を言わない", u"doc", lambda c: setattr(c, "doc", c.doc.replace(SCRIPT_COMMIT, u"")))
M(u"h34 記録の file 名を言わない", u"doc", lambda c: setattr(c, "doc", c.doc.replace(u"read_types_2026-11-15.json", u"")))
M(u"h35 測り直しの環境変数を言わない", u"doc", lambda c: setattr(c, "doc", c.doc.replace(u"AUDIT_CORE_KAM_REMEASURE=1", u"")))
M(u"h36 封 §6 の 6 番目の字を落とす", u"doc", lambda c: setattr(c, "doc", c.doc.replace(seal_limits(c.seal)[5], u"")))
M(u"h37 封 §6 の 7 番目の字を落とす", u"doc", lambda c: setattr(c, "doc", c.doc.replace(seal_limits(c.seal)[6], u"")))
M(u"h38 封 §6 の 10 番目の字を落とす", u"doc", lambda c: setattr(c, "doc", c.doc.replace(seal_limits(c.seal)[9], u"")))
M(u"h39 封 §6 の 1 番目の字を 1 字変える", u"doc", lambda c: setattr(c, "doc", c.doc.replace(seal_limits(c.seal)[0], seal_limits(c.seal)[0][:6] + u"×" + seal_limits(c.seal)[0][7:])))
M(u"h40 予測の判定の字(K-9 を外れにする)", u"doc", lambda c: setattr(c, "doc", re.sub(r"(\| K-9 \|.*?\| )当たり( \|)", r"\1外れ\2", c.doc, count=1, flags=re.S)))
M(u"h41 K-5 の実測の字", u"doc", doc_replace(u"時間の欄を除いて byte で同じだった", u"時間の欄を除いて byte で違った"))
M(u"h42 記録の側を 1 つ変えると判定が変わる(V 連結の ア を 17 に)", u"doc", lambda c: [r.__setitem__(4, u"オ") for r in [r for r in c.R[u"行"] if r[0] == u"V 連結" and r[4] == u"ア"][:2]])
M(u"h43 記録の側を 1 つ変えると塊が違う(G 単体の a を c に)", u"doc", lambda c: types_row(c, u"G 単体", lambda r: r[4] == u"a").__setitem__(4, u"c"))
M(u"h44 states の側を 1 つ変えると塊が違う(連結の claim の行を state ごと動かす)", u"doc", lambda c: first_row(c, CONS, lambda r: r[2] == UNV)[1].__setitem__(2, PNF))
M(u"h45 封の予測の字を変える(K-7 の幅)", u"doc", seal_replace(u"| 0〜1 行 |", u"| 0〜2 行 |"))
M(u"h46 §4 の迷いの通し番号の入れ替え(3 → 21)", u"doc", doc_replace(u"V 連結の通し番号 3 は、全体の数を言う文", u"V 連結の通し番号 21 は、全体の数を言う文"))
M(u"h47 §4 の G 連結の通し番号の 1 つを変える", u"doc", doc_replace(u"(G 連結の通し番号 9・11・13・26・37・44・50・58)", u"(G 連結の通し番号 9・11・13・26・37・44・50・59)"))
M(u"h48 §4 の V 単体の「側を先に取った」決めを消す", u"doc", doc_sub(u"- V 単体: 結んだ fact が連結の側だった行[^\n]*\n", u""))
M(u"h49 §4 の G 連結の (a) の決めの段を消す", u"doc", doc_sub(u"\\(a\\) の決めで入れた行は 8 行.*?記録の型は付け直していない。", u"", re.S))
M(u"h50 §5 の「6 行のうち 6 行」を 5 行に", u"doc", doc_replace(u"(6 行のうち 6 行。", u"(6 行のうち 5 行。"))
M(u"h51 散文の数の入れ替え(連結 切れない 50 → 60)", u"doc", doc_replace(u"切れない 50 本は全部「札なし」で、測れていない", u"切れない 60 本は全部「札なし」で、測れていない"))
M(u"h52 散文の数の入れ替え(単体の側が合うと読んだ 30 → 31)", u"doc", doc_replace(u"側が合うと読んだのは 30 行", u"側が合うと読んだのは 31 行"))
M(u"h53 §5 の「見つけていない」を「見つけた」に(1 つ目)", u"doc", doc_replace(u"fact の食い違い」を 1 件も見つけていない", u"fact の食い違い」を 1 件見つけた"))
M(u"h54 §5 の「見つけていない」を「見つけた」に(2 つ目)", u"doc", doc_replace(u"候補を 1 件も見つけていない」は記録の読みでの話", u"候補を 1 件見つけた」は記録の読みでの話"))
M(u"h55 §6 に採用の字を足す", u"doc", doc_replace(u"人間が決める)。この結果は", u"人間が決める)。採用とする。この結果は"))
M(u"h56 §1 の当たり外れの数の字", u"doc", doc_replace(u"当たり 10・読みで割れた 1・外れ 0。", u"当たり 11・読みで割れた 0・外れ 0。"))
M(u"h57 §1 の K-9 の外れ方の字", u"doc", doc_replace(u"外れ方の「4 行以上」に当たる", u"外れ方の「5 行以上」に当たる"))
M(u"h58 K-9 の幅の位置の字(幅の表)", u"doc", doc_replace(u"| 1 行 = 内(下端から 1 行上・上端まで 2 行) |", u"| 1 行 = 内(下端から 1 行上・上端まで 3 行) |"))
M(u"h59 (ク) を食い違いと呼ぶ", u"doc", doc_replace(u"(ク) は候補であり、食い違いとは呼ばない", u"(ク) は食い違い"))
M(u"h60 §3 の「(オ) に入れた理由は §4」を消す", u"doc", doc_replace(u"(オ) に入れた理由は §4、(エ) と読んだ数は §3-6", u""))
M(u"h61 「(エ) は記録の読みでは 0 行」から「記録の読みでは」を消す", u"doc", doc_replace(u"(エ) は記録の読みでは 0 行", u"(エ) は 0 行"))
M(u"h62 「記録の読みで使われた型は」から「記録の読みで」を消す", u"doc", doc_replace(u"記録の読みで使われた型は", u"使われた型は"))
M(u"h63 §4 の (エ)/(オ) の境の理由を消す", u"doc", doc_replace(u"文の数は「繰延税金資産の総額(評価性引当額を引く前)」で、結んだ fact は引当を引いた後の額の科目。期が合っても値は合わない定義の違いなので (オ) を取った。", u""))
M(u"h64 §4 の (エ) と読んだ数の字", u"doc", doc_replace(u"(エ) と読めば V 連結は (オ) 7・(エ) 3", u"(エ) と読めば V 連結は (オ) 8・(エ) 2"))
M(u"h65 §3-6 の (b) の足し算の字", u"doc", doc_replace(u"(b) は 1 + 8 = 9 行。", u"(b) は 1 + 7 = 8 行。"))
M(u"h66 §5 の 13.3% を別の数に", u"doc", doc_replace(u"8 行 = 13.3%", u"8 行 = 15.0%"))
M(u"h67 K-9 の判定の字を当たりに", u"doc", doc_replace(u"| 読みで割れた(記録の読みでは幅の中", u"| 当たり(記録の読みでは幅の中"))
M(u"h68 古い字(11 行とも当たりで、外れは 0 行)を足す", u"doc", lambda c: setattr(c, "doc", c.doc + u"\n11 行とも当たりで、外れは 0 行。\n"))
M(u"h69 §6 の別の読みの字を消す", u"doc", doc_replace(u"(別の読みでは連結 9 行。§3-6)", u""))
M(u"h70 §4 の記録の型は付け直していない を消す(§1 側)", u"doc", doc_replace(u"記録の型は結果を見てから付け直していない", u"記録の型を付け直した"))
M(u"h71 §4 の「司令塔が決めきれない」を消す", u"doc", doc_replace(u"どちらの読みが封の字に合うかは司令塔が決めきれない", u"封の字に合うのは記録の読み"))
# e. 追加(通し番号の一覧と記録)
M(u"e25 G 連結の通し番号 9 の型を a から b に(集計も合わせる)", u"cross", lambda c: (types_row(c, u"G 連結", lambda r: True), [r for r in c.R[u"行"] if r[0] == u"G 連結"][8].__setitem__(4, u"b"), [r for r in c.R[u"行"] if r[0] == u"G 連結"][8].__setitem__(5, u"範囲")))
M(u"e26 V 連結の通し番号 2 の型を オ から エ に", u"cross", lambda c: [r for r in c.R[u"行"] if r[0] == u"V 連結"][1].__setitem__(4, u"エ"))
M(u"e27 前期でない V 連結の行を前期にする(states 側)", u"cross", lambda c: first_row(c, CONS, lambda r: r[2] == VM and r[4] == u"CurrentYear")[1].__setitem__(4, u"Prior1Year"))
M(u"e28 V 単体の通し番号 5 の型を ア に", u"cross", lambda c: [r for r in c.R[u"行"] if r[0] == u"V 単体"][4].__setitem__(4, u"ア"))
M(u"e29 V 連結の通し番号 3 の型を ア に", u"cross", lambda c: [r for r in c.R[u"行"] if r[0] == u"V 連結"][2].__setitem__(4, u"ア"))
M(u"e30 V 連結の通し番号 21 の型を ア から オ に", u"cross", lambda c: [r for r in c.R[u"行"] if r[0] == u"V 連結"][20].__setitem__(4, u"オ"))
# i. 封
M(u"i9 封の K-9 の外れ方(4 行以上 → 5 行以上)", u"seal", seal_replace(u"4 行以上 = 「結べた」の中に", u"5 行以上 = 「結べた」の中に"))
M(u"i10 封の K-9 の幅(0〜3 行 → 0〜4 行)", u"seal", seal_replace(u"| 0〜3 行 | 4 行以上", u"| 0〜4 行 | 4 行以上"))
# i. 封
M(u"i1 封の K-6 の幅", u"seal", seal_replace(u"18 行以上(行の数の 62% 以上)", u"17 行以上(行の数の 58% 以上)"))
M(u"i2 封の K-10 の幅", u"seal", seal_replace(u"(b) 1〜6 行。「側」1〜6 行", u"(b) 1〜7 行。「側」1〜7 行"))
M(u"i3 封の K-11 の幅", u"seal", seal_replace(u"0〜13 行", u"0〜14 行"))
M(u"i4 封の K-3 の数", u"seal", seal_replace(u"480 = 136 / 29 / 72 / 243", u"480 = 137 / 29 / 72 / 243"))
M(u"i5 封の K-11 が消える", u"seal", seal_replace(u"| K-11 |", u"| K-X |"))
M(u"i6 封 §6 の 1 項が消える", u"seal", seal_replace(u"- 注入をしていないので、「誤りを通す率」はこの便では言えない。\n", u""))
M(u"i7 封が commit のときと 1 字違う", u"frozen", lambda c: setattr(c, "seal", c.seal + u"。"))
M(u"i8 封の文の途中の 1 字", u"frozen", seal_replace(u"測った事実は増やして", u"測った事実を増やして"))


def check_problems(check, c):
    return guard(CHECKS[check], c)


# ======================================================================================================
# 試験
class RealRecordsTest(unittest.TestCase):
    def test_a_1_the_three_records_and_the_script_equal_the_pinned_sha256(self):
        self.assertEqual([], sha_problems(Ctx().texts))

    def test_a_2_the_pinned_sha256_are_the_ones_the_brief_names(self):
        self.assertEqual(["86e31ca230850d9a13061a18f647c17dea2b95a76927d2587374978af2aef410", "3ba57f55e62a29e20578b87f527de35d9bc3d2310cbba232d9311c9b187103e7",
                          "8c9fe6b8def7430908bf925f697ea5a1b1d634dd754933aab7c71b0a913c964a", "cc2aab3029ef76d91e73aceae562370d3e74a58f51d90cecfb6153e28259aa4a"], list(SHA_PIN.values()))
        self.assertEqual([POP_REL, STATES_REL, TYPES_REL, SCRIPT_REL], list(SHA_PIN.keys()))
        self.assertEqual((u"fixtures/xbrl/kam/population_2026-11-15.json", u"fixtures/xbrl/kam/states_2026-11-15.json", u"fixtures/xbrl/kam/read_types_2026-11-15.json"), RECORD_RELS)

    def test_b_1_the_provenance_fields_equal_the_real_files(self):
        self.assertEqual([], provenance_problems(Ctx()))

    def test_c_1_the_population_record_is_the_seal_table(self):
        self.assertEqual([], population_problems(Ctx()))

    def test_d_1_the_states_record_is_whole_and_recounted_from_its_rows(self):
        self.assertEqual([], states_problems(Ctx()))

    def test_d_2_the_recount_pins_the_real_numbers_literally(self):
        c = Ctx()
        a, b = recount_side(c.S[u"本"], CONS), recount_side(c.S[u"本"], NON)
        self.assertEqual((201, 151, 50, 244159), (a[u"本"], a[u"切れた"], a[u"切れない"], a[u"字数の合計"]))
        self.assertEqual((201, 192, 9, 147934), (b[u"本"], b[u"切れた"], b[u"切れない"], b[u"字数の合計"]))
        self.assertEqual({u"decode": 0, u"札なし": 50, u"札が複数": 0, u"続きあり": 0, u"閉じない": 0, u"空": 0}, a[u"切れない理由"])
        self.assertEqual({u"decode": 0, u"札なし": 9, u"札が複数": 0, u"続きあり": 0, u"閉じない": 0, u"空": 0}, b[u"切れない理由"])
        self.assertEqual([480, 136, 29, 72, 243], [a[u"claim"]] + [a[u"4 state"][s] for s in STATES])
        self.assertEqual([308, 36, 8, 50, 214], [b[u"claim"]] + [b[u"4 state"][s] for s in STATES])
        self.assertEqual((26, 10, 61), (a[u"VALUE_MISMATCH が 1 以上の本"], a[u"切れた本のうち claim が 0 の本"], a[u"切れた本のうち GROUNDED が 0 の本"]))
        self.assertEqual((8, 83, 164), (b[u"VALUE_MISMATCH が 1 以上の本"], b[u"切れた本のうち claim が 0 の本"], b[u"切れた本のうち GROUNDED が 0 の本"]))
        self.assertEqual({G: {TRUE: 0, FALSE: 136}, VM: {TRUE: 0, FALSE: 29}, UNV: {TRUE: 0, FALSE: 72}, PNF: {TRUE: 0, FALSE: 243}}, plain(a[TEN_KEY]))
        self.assertEqual({G: {TRUE: 30, FALSE: 6}, VM: {TRUE: 5, FALSE: 3}, UNV: {TRUE: 0, FALSE: 50}, PNF: {TRUE: 0, FALSE: 214}}, plain(b[TEN_KEY]))
        self.assertEqual((0, 0), (a[u"claim と raw の並びが対応しなかった本"], b[u"claim と raw の並びが対応しなかった本"]))
        self.assertEqual((29, 27, 2, 26, 3), (a[u"VALUE_MISMATCH の内訳"][u"行"], a[u"VALUE_MISMATCH の内訳"][u"円族の数"], a[u"VALUE_MISMATCH の内訳"][u"% の数"],
                                              a[u"VALUE_MISMATCH の内訳"][u"pointer の期"][u"CurrentYear"], a[u"VALUE_MISMATCH の内訳"][u"pointer の期"][u"Prior1Year"]))
        self.assertEqual((8, 8, 0, 6, 2), (b[u"VALUE_MISMATCH の内訳"][u"行"], b[u"VALUE_MISMATCH の内訳"][u"円族の数"], b[u"VALUE_MISMATCH の内訳"][u"% の数"],
                                          b[u"VALUE_MISMATCH の内訳"][u"pointer の期"][u"CurrentYear"], b[u"VALUE_MISMATCH の内訳"][u"pointer の期"][u"Prior1Year"]))

    def test_d_3_the_group_rows_pin_the_real_numbers_literally(self):
        c = Ctx()
        want = {(CONS, u"甲"): (67, 51, 16, 161, [48, 9, 23, 81]), (CONS, u"乙"): (40, 29, 11, 83, [24, 6, 12, 41]), (CONS, u"丙"): (94, 71, 23, 236, [64, 14, 37, 121]),
                (NON, u"甲"): (67, 64, 3, 96, [15, 2, 17, 62]), (NON, u"乙"): (40, 38, 2, 63, [8, 3, 9, 43]), (NON, u"丙"): (94, 90, 4, 149, [13, 3, 24, 109])}
        for (side, g), w in want.items():
            r = recount_side(c.S[u"本"], side, g)
            self.assertEqual(w, (r[u"本"], r[u"切れた"], r[u"切れない"], r[u"claim"], [r[u"4 state"][s] for s in STATES]), (side, g))

    def test_e_1_the_read_types_record_is_whole_and_redrawn_from_the_states_record(self):
        self.assertEqual([], types_problems(Ctx()))

    def test_e_2_the_read_types_numbers_are_pinned_literally(self):
        c = Ctx()
        self.assertEqual(133, len(c.R[u"行"]))
        self.assertEqual({u"V 連結": 29, u"V 単体": 8, u"G 連結": 60, u"G 単体": 36}, dict((lab, sum(1 for r in c.R[u"行"] if r[0] == lab)) for lab in SETS))
        cnt = dict((lab, collections.Counter(r[4] for r in c.R[u"行"] if r[0] == lab)) for lab in SETS)
        self.assertEqual({u"ア": 19, u"オ": 10}, dict(cnt[u"V 連結"]))
        self.assertEqual({u"ア": 3, u"ウ": 3, u"オ": 2}, dict(cnt[u"V 単体"]))
        self.assertEqual({u"a": 59, u"b": 1}, dict(cnt[u"G 連結"]))
        self.assertEqual({u"a": 30, u"b": 6}, dict(cnt[u"G 単体"]))
        self.assertEqual({u"項目": 1}, dict(collections.Counter(r[5] for r in c.R[u"行"] if r[0] == u"G 連結" and r[4] == u"b")))
        self.assertEqual({u"側": 6}, dict(collections.Counter(r[5] for r in c.R[u"行"] if r[0] == u"G 単体" and r[4] == u"b")))
        for t in (u"イ", u"エ", u"カ", u"キ", u"ク", u"ケ"):
            self.assertEqual(0, cnt[u"V 連結"][t] + cnt[u"V 単体"][t], t)
        self.assertEqual(0, cnt[u"G 連結"][u"c"] + cnt[u"G 単体"][u"c"])

    def test_e_3_the_g_cons_sample_is_a_draw_of_60_from_136_and_is_not_the_first_60(self):
        c = Ctx()
        exp, n_g = expected_reading(c.S)
        self.assertEqual(136, n_g)
        idx = sorted(random.Random(20261115).sample(range(136), 60))
        self.assertEqual(60, len(set(idx)))
        self.assertNotEqual(list(range(60)), idx)
        allg = [(b[u"#"], r[0], r[1]) for b in sorted(c.S[u"本"], key=lambda b: b[u"#"]) for r in sorted(b[CONS][u"行"], key=lambda r: (r[0], r[1])) if r[2] == G]
        self.assertEqual([allg[i] for i in idx], [tuple(r[1:4]) for r in c.R[u"行"] if r[0] == u"G 連結"])

    def test_f_1_the_types_and_the_ten_th_column_cross_as_the_document_says(self):
        self.assertEqual([], cross_problems(Ctx()))

    def test_f_2_the_cross_numbers_are_pinned_literally(self):
        c = Ctx()
        j = read_join(c)
        self.assertEqual(3, sum(1 for r in j if r[0] == u"V 単体" and r[4] == u"ウ" and r[6][9] is False))
        self.assertEqual(6, sum(1 for r in j if r[0] == u"G 単体" and r[4] == u"b" and r[6][9] is False))
        self.assertEqual(30, sum(1 for r in j if r[0] == u"G 単体" and r[4] == u"a" and r[6][9] is True))
        self.assertEqual(1, sum(1 for r in j if r[0] == u"G 単体" and r[4] == u"b" and r[6][5] is True and r[6][7] is True))
        self.assertEqual((3, 2), (sum(1 for r in j if r[0] == u"V 連結" and r[4] == u"オ" and r[6][4] == u"Prior1Year"), sum(1 for r in j if r[0] == u"V 単体" and r[4] == u"オ" and r[6][4] == u"Prior1Year")))
        vrows = [r for r in c.R[u"行"] if r[0] == u"V 連結"]
        self.assertEqual((u"オ", u"ア"), (vrows[2][4], vrows[20][4]))
        self.assertEqual(((9, 11, 13, 26, 37, 44, 50, 58), (2, 13, 22), (5, 7)), (ALT_G_CONS, ALT_V_CONS, ALT_V_NON))
        ac = alt_counts(c)
        self.assertEqual((1, 9), ac[u"G 連結 b"])
        self.assertEqual((59, 51), ac[u"G 連結 a"])
        self.assertEqual((8, 60), (ac[u"範囲が狭い行"], ac[u"G 連結 60 行"]))
        self.assertEqual(u"13.3%", pct(8, 60))
        self.assertEqual(((10, 7), (0, 3), (2, 0), (0, 2), (0, 1)), (ac[u"V 連結 オ"], ac[u"V 連結 エ"], ac[u"V 単体 オ"], ac[u"V 単体 エ"], ac[u"V 連結 ク"]))
        self.assertEqual([], alt_serial_problems(c, j))
        self.assertEqual([], [x for lab, ns in ((u"G 連結", ALT_G_CONS), (u"V 連結", ALT_V_CONS), (u"V 単体", ALT_V_NON)) for x in ns if serial_type(c, lab, x) not in (u"a", u"オ")])

    def test_g_1_the_records_hold_no_sentence_no_value_no_company_no_code_no_pointer(self):
        self.assertEqual([], clean_problems(Ctx()))

    def test_h_1_the_blocks_of_the_result_document_equal_the_rebuilt_tables(self):
        self.assertEqual([], doc_problems(Ctx()))

    def test_h_2_the_prediction_judgements_are_pinned_literally(self):
        rows = dict((r[0], r[4]) for r in pred_table(Ctx()))
        self.assertEqual({u"K-1": u"当たり", u"K-2": u"当たり", u"K-3": u"当たり", u"K-4": u"当たり", u"K-5": K5_JUDGE, u"K-6": u"当たり", u"K-7": u"当たり", u"K-8": u"当たり",
                          u"K-9": u"読みで割れた(記録の読みでは幅の中・封の字どおりの読みでは幅の外)", u"K-10": u"当たり", u"K-11": u"当たり"}, rows)

    def test_h_3_the_prediction_actuals_are_pinned_literally(self):
        rows = dict((r[0], r[3]) for r in pred_table(Ctx()))
        self.assertEqual(u"V 連結 29 行のうち (ア) 19 行(65.5%)", rows[u"K-6"])
        self.assertEqual(u"V 連結 + V 単体 37 行のうち (ク) 0 行", rows[u"K-7"])
        self.assertEqual(u"V 単体 8 行のうち (ウ) 3 行", rows[u"K-8"])
        self.assertEqual(u"G 連結 60 行のうち (b) 1 行。封の字どおりに読む別の読みでは (b) 9 行(1 + 8。§3-6)", rows[u"K-9"])
        self.assertEqual(u"G 単体 36 行のうち (b) 6 行・違うものが「側」6 行", rows[u"K-10"])
        self.assertEqual(u"読んだ 133 行のうち (ケ) + (c) 0 行", rows[u"K-11"])
        self.assertEqual(u"G 単体 36 行のうち (b) 6 行・違うものが「側」6 行", rows[u"K-10"])
        self.assertEqual(u"連結 切れた 151・切れない 50、単体 切れた 192・切れない 9。切れない 59 本の理由は全部「札なし」", rows[u"K-1"])

    def test_h_4_the_seal_prediction_bounds_are_in_the_seal_and_pinned(self):
        self.assertEqual([], seal_problems(Ctx().seal))
        k = seal_k_rows(Ctx().seal)
        self.assertEqual(11, len(k))
        self.assertEqual(10, len(seal_limits(Ctx().seal)))

    def test_i_1_the_seal_is_the_text_of_the_sealed_commit(self):
        self.assertEqual([], seal_frozen_problems(Ctx().seal))

    def test_i_2_the_real_history_has_the_seal_before_the_script_before_the_records_the_document_and_this_gate(self):
        u"""記録 3 つ・結果の文書・この門のどれかが未 commit なら赤(足した commit が無い。skip にしない)。全部 commit された後で初めて緑。"""
        self.assertEqual([], order_problems_real())

    def test_i_3_the_real_order_failure_before_the_commit_is_only_the_uncommitted_files(self):
        got = order_problems_real()
        self.assertTrue(all(p.startswith(u"UNCOMMITTED:") for p in got), got)

    def test_i_4_the_order_check_lists_the_three_records_the_document_and_this_gate(self):
        self.assertEqual(list(RECORD_RELS) + [DOC_REL, GATE_REL], order_others())
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, r)) for r in RECORD_RELS + (DOC_REL, GATE_REL, SCRIPT_REL, SEAL_GATE_REL)))

    def test_i_5_engine_lib_and_the_previous_stages_are_untouched_and_the_script_is_unchanged_since_its_commit(self):
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
        self.assertEqual([], silent, u"赤にならなかった変異: %s" % silent)
        self.assertEqual([], crashed, u"検査が例外で落ちて赤になった変異: %s" % crashed)

    def test_m_3_each_mutation_gets_a_new_copy_and_leaves_the_real_files_alone(self):
        before = dict((rel, sha256_rel(rel)) for rel in list(SHA_PIN) + [SEAL_REL, DOC_REL])
        c = Ctx()
        c.S[u"集計"][CONS][u"計"][u"claim"] = -1
        c.doc = u"x"
        c.cur["script"] = u"x"
        self.assertEqual(480, Ctx().S[u"集計"][CONS][u"計"][u"claim"])
        self.assertNotEqual(u"x", Ctx().doc)
        self.assertNotEqual(u"x", Ctx().cur["script"])
        self.assertEqual(before, dict((rel, sha256_rel(rel)) for rel in before))

    def test_m_4_the_mutation_table_covers_every_check_and_every_effect_named_in_the_brief(self):
        checks = set(ch for _l, ch, _f in MUTATIONS)
        self.assertEqual(set(CHECKS), checks)
        self.assertGreaterEqual(len(MUTATIONS), 150)
        labels = u"\n".join(l for l, _c, _f in MUTATIONS)
        for need in (u"通し番号の入れ替え", u"側を先に取った", u"(a) の決めの段を消す", u"6 行のうち 6 行", u"見つけていない", u"採用の字", u"外れの数の字", u"K-9 の幅", u"食い違いと呼ぶ",
                     u"理由は §4", u"散文の数の入れ替え", u"G 連結の標本が先頭から 60 行", u"states の記録の sha256", u"封の文の途中の 1 字", u"漢数字", u"組の取り違え", u"型の集計", u"違うものが 4 つの外",
                     u"b なのに違うものが無い", u"封 §6 の 6 番目", u"封 §6 の 7 番目", u"封 §6 の 10 番目", u"予測の判定の字", u"行を 1 つ消す", u"本の ZIP の sha256", u"K-5 の実測の字"):
            self.assertIn(need, labels)

    def test_m_5_the_prose_number_check_accepts_a_block_number_and_refuses_another(self):
        c = Ctx()
        blocks = build_blocks(c)
        self.assertEqual([], prose_number_problems(u"本文。連結の GROUNDED は 136 行(480 行のうち)。", blocks, c.seal))
        self.assertNotEqual([], prose_number_problems(u"本文。連結の GROUNDED は 137 行。", blocks, c.seal))
        self.assertEqual([], prose_number_problems(u"本文。封 `497a4661` と `e6f01e24` と 2026-11-15 と P33E と K-10 と §6-10。", blocks, c.seal))
        self.assertNotEqual([], prose_number_problems(u"本文。三百本。", blocks, c.seal))

    def test_m_6_the_g_single_side_check_distinguishes_a_side_swap(self):
        c = Ctx()
        types_row(c, u"G 単体", lambda r: r[4] == u"b")[5] = u"項目"
        self.assertNotEqual([], types_problems(c) + cross_problems(c))


class JudgementTest(unittest.TestCase):
    u"""予測の判定の関数が「外れ」を出せること(全部が当たりの記録でだけ緑になる関数は、当たりの字を黙って書ける)。"""

    @staticmethod
    def judged(fn):
        c = Ctx()
        fn(c)
        return dict((r[0], r[4]) for r in pred_table(c))

    @staticmethod
    def retype(c, lab, old, new, n):
        rows = [r for r in c.R[u"行"] if r[0] == lab and r[4] == old][:n]
        assert len(rows) == n, (lab, old, n)
        for r in rows:
            r[4] = new

    def test_j_1_k6_is_a_hit_at_the_floor_of_18_rows_and_a_miss_below(self):
        self.assertEqual(u"当たり", self.judged(lambda c: self.retype(c, u"V 連結", u"ア", u"オ", 1))[u"K-6"])
        self.assertEqual(u"外れ", self.judged(lambda c: self.retype(c, u"V 連結", u"ア", u"オ", 2))[u"K-6"])

    def test_j_2_k7_k8_k9_k10_k11_each_turn_to_a_miss_beyond_the_sealed_width(self):
        self.assertEqual(u"外れ", self.judged(lambda c: self.retype(c, u"V 連結", u"ア", u"ク", 2))[u"K-7"])
        self.assertEqual(u"当たり", self.judged(lambda c: self.retype(c, u"V 連結", u"ア", u"ク", 1))[u"K-7"])
        self.assertEqual(u"外れ", self.judged(lambda c: self.retype(c, u"V 単体", u"ウ", u"ア", 3))[u"K-8"])
        self.assertEqual(u"外れ", self.judged(lambda c: self.retype(c, u"V 単体", u"ア", u"ウ", 3) or self.retype(c, u"V 単体", u"オ", u"ウ", 1) or 0)[u"K-8"])
        self.assertEqual(u"外れ", self.judged(lambda c: self.retype(c, u"G 連結", u"a", u"b", 3))[u"K-9"])
        self.assertEqual(u"読みで割れた(記録の読みでは幅の中・封の字どおりの読みでは幅の外)", self.judged(lambda c: self.retype(c, u"G 連結", u"a", u"b", 2))[u"K-9"])
        self.assertEqual(u"読みで割れた(記録の読みでは幅の中・封の字どおりの読みでは幅の外)", self.judged(lambda c: self.retype(c, u"G 連結", u"b", u"a", 1))[u"K-9"])
        self.assertEqual(u"外れ", self.judged(lambda c: self.retype(c, u"G 単体", u"b", u"a", 6))[u"K-10"])
        self.assertEqual(u"外れ", self.judged(lambda c: self.retype(c, u"V 連結", u"ア", u"ケ", 14))[u"K-11"])
        self.assertEqual(u"当たり", self.judged(lambda c: self.retype(c, u"V 連結", u"ア", u"ケ", 13))[u"K-11"])

    def test_j_3_k1_to_k4_each_turn_to_a_miss_when_the_states_record_differs_from_the_sealed_numbers(self):
        self.assertEqual(u"外れ", self.judged(lambda c: book(c, 6)[CONS].__setitem__(u"理由", u"空"))[u"K-1"])
        self.assertEqual(u"外れ", self.judged(lambda c: bump(book(c, 60)[CONS], u"字数"))[u"K-2"])
        self.assertEqual(u"外れ", self.judged(lambda c: first_row(c, CONS, lambda r: r[2] == G)[1].__setitem__(2, VM))[u"K-3"])
        self.assertEqual(u"外れ", self.judged(lambda c: (lambda r: r.__setitem__(9, not r[9]))(first_row(c, NON, lambda r: r[2] == G and r[9] is True)[1]))[u"K-4"])

    def test_j_4_the_real_records_judge_ten_as_hits_and_k9_as_split(self):
        got = self.judged(lambda c: None)
        self.assertEqual([u"K-%d" % i for i in range(1, 12)], list(got.keys()))
        self.assertEqual(10, sum(1 for v in got.values() if v.startswith(u"当たり")))
        self.assertEqual([u"K-9"], [k for k, v in got.items() if v.startswith(u"読みで割れた")])
        self.assertEqual(0, sum(1 for v in got.values() if v.startswith(u"外れ")))
        self.assertEqual(u"当たり", split_judge(True, True))
        self.assertEqual(u"外れ", split_judge(False, False))
        self.assertEqual(u"読みで割れた(記録の読みでは幅の中・封の字どおりの読みでは幅の外)", split_judge(True, False))
        self.assertEqual(u"読みで割れた(記録の読みでは幅の外・封の字どおりの読みでは幅の中)", split_judge(False, True))
        self.assertEqual((0, 3), bound_of(seal_k_rows(Ctx().seal)[u"K-9"][1]))
        self.assertEqual((18, None), bound_of(seal_k_rows(Ctx().seal)[u"K-6"][1]))


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
        u"""門は script の集計・判定・標本の関数を呼ばず、自前で数え直す(構造は ast で見る。字面の検査は自分の説明文に当たる)。"""
        import ast
        tree = ast.parse(read(GATE_REL))
        banned = set([u"tally", u"block", u"judge_book", u"judge_side", u"cut_kam", u"row10", u"reading_items", u"side_rows", u"run_states", u"run_population", u"run_types", u"pick_sample",
                      u"state_counts", u"reason_counts", u"vm_breakdown"])
        used = [(n.value.id, n.attr) for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id in (u"MS", u"TSS", u"SG", u"TS", u"ST")]
        self.assertEqual([], [x for x in used if x[1] in banned])

    def test_n_4_the_script_is_loaded_without_overwriting_the_names_that_existed(self):
        import types
        marker = types.ModuleType("pswap_for_kam_result")
        before = sys.modules.get("pswap_for_kam_result")
        sys.modules["pswap_for_kam_result"] = marker
        try:
            mod = load_module(SCRIPT_REL, "kam_script_reload_probe_for_result_gate")
            self.assertIs(marker, sys.modules["pswap_for_kam_result"])
            self.assertIs(mod, sys.modules["kam_script_reload_probe_for_result_gate"])
        finally:
            if before is None:
                sys.modules.pop("pswap_for_kam_result", None)
            else:
                sys.modules["pswap_for_kam_result"] = before
            sys.modules.pop("kam_script_reload_probe_for_result_gate", None)


@unittest.skipUnless(os.environ.get("AUDIT_CORE_KAM_REMEASURE") == "1", u"材料から測り直す試験は AUDIT_CORE_KAM_REMEASURE=1 のときだけ走る")
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
        u"""既定の材料(読むだけ)で states を走らせ、追跡の記録と、時間の欄を除いて byte で同じ。本番の path には書かない(約 75 秒)。"""
        self.assertEqual(self._strip(cached_text(STATES_REL)), self._strip(self._run("states", "states_remeasure.json")))

    def test_r_2_the_population_record_is_reproduced_from_the_material_byte_for_byte(self):
        self.assertEqual(self._strip(cached_text(POP_REL)), self._strip(self._run("population", "population_remeasure.json")))


if __name__ == "__main__":
    unittest.main()
