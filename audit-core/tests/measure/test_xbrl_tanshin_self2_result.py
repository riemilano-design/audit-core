# -*- coding: utf-8 -*-
"""結果の門: 封 docs/XBRL_TANSHIN_SELF2_SEAL_2026-11-14.md §2 の 7(TSS の第 2 便 ― 中間の短信の期の名前を measure/ の側で写して読む・「値が違う」のうち表の値に近い行を拾って読む)。

封の門 ``test_xbrl_tanshin_self2_seal.py`` の次の段。**追跡されている記録 3 つ・第 1 便の判定の記録・封・結果の文書だけを読む**(cache の材料が無い機械でも緑。材料から測り直す試験だけ環境変数
``AUDIT_CORE_TSS2_REMEASURE=1`` で走る)。

縛るもの(検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表で 1 本ずつ)
 a 記録 3 つと script の sha256(字で留める)  b 記録の来歴の欄(script 4 本・第 1 便の判定の記録・interim の記録・near の記録の sha256 を実 file と突き合わせる)
 c interim の記録を本の行から数え直す(script の集計は呼ばない)・第 1 便の B の行との動きの表を数え直す・A の 250 本と B の 150 本の行ごとの照合の数
 d near の記録: 近い行の 1 行ずつが「値が違う」の行で、単位の族が規則と合い、並びが封どおり・集計を行から数え直す
 e near_types の記録: 標本が ``random.Random(20261115).sample(range(220), 200)`` を番号の順にしたものと 1 行ずつ同じ・型の集計の和・A と B の和
 f 記録に文も値も会社名も証券コードも pointer の字も無い・key_leaks が空・行の欄が封のとおり
 g 結果の文書の 9 つの塊を記録から作り直して 1 行ずつ照らす・塊の外の 2 桁以上の数は記録から作った数の集合の中にあること・予測の判定
 h 封が a1fd09bf から 1 字も変わっていない・順序(commit の順。未 commit は赤)・engine 0 行・script が a1fd09bf の後の commit から変わっていない
この file は docID の字を持たない。
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


SG = load_module("tests/measure/test_xbrl_tanshin_self2_seal.py", "tanshin_self2_seal_gate_for_tanshin_self2_result_gate")      # 封の門の部品。門としては走らせない
PR = SG.PR
MS = SG.MS

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
SCRIPT_REL = SG.SCRIPT_REL
TSS_REL = SG.TSS_REL
STAGE_REL = SG.STAGE_REL
SEAL_GATE_REL = SG.GATE_REL
GATE_REL = "tests/measure/test_xbrl_tanshin_self2_result.py"
DOC_REL = SG.DOC_REL
REC_DIR = "fixtures/xbrl/tanshin_self/"
INTERIM_REL, NEAR_REL, TYPES_REL = SG.RECORD_RELS
TSS_STATES_REL = SG.TSS_STATES_REL
POP_REL = SG.POPULATION_REL
RECORD_RELS = (INTERIM_REL, NEAR_REL, TYPES_REL)
SCRIPT_COMMIT = "c1c4a782"                                 # script と封の門を足した commit(この commit から script は 0 行)

# ---- 字で留める(記録・script の sha256。人が決めた数は字で留める)
SHA_PIN = collections.OrderedDict([
    (INTERIM_REL, "ef443ec1b1331fa05ca314122fe36ad28746816e890f73f27efde55738bb5e7e"),
    (NEAR_REL, "5c2b6ee418495ac184ab51eb424e2e0ef11a04b881bbf719cb31e2c3018e0952"),
    (TYPES_REL, "f59cfc68a6ddf98b9a713efdda52f8bf04d183bc9b415964bb724812810f779f"),
    (SCRIPT_REL, "7a3db37e77e8013f56668d7202dbddae023778d57fecaf7b8bc5c621a68583b8")])
STATES = (u"GROUNDED", u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND")
G, VM, UNV, PNF = STATES
RULES = (u"N-円", u"N-桁", u"N-率")
TYPE_KEYS = u"あいうえお"
SEED, SAMPLE_N, NEAR_N = 20261115, 200, 220
A_MAX = 250                                                # 本の # が 250 以下 = A(甲 + 乙)、251 以上 = B(丙)
BLOCK_NAMES = (u"pred", u"interim", u"moves", u"reasons", u"vm", u"near", u"combos", u"read", u"types")
FORBIDDEN_WORDS = (u"精度", u"ハルシネーション", u"証明した", u"LLM より正確", u"世界で 1 社", u"人の目")
DOCID_RE = re.compile(r"S100[0-9A-Z]{4}")
TDNET_RE = re.compile(r"0812\d{14}")
CODE_RE = re.compile(r"(?<![0-9A-Za-z\-])\d{3}[0-9A-Z](?![0-9A-Za-z\-])")
POINTER_RE = re.compile(r"xbrl:|jppfs|jpcrp|jpdei|_cor:|@(Current|Prior)|formula:")
COMPANY_WORDS = (u"株式会社", u"有限会社", u"合同会社", u"㈱", u"(株)")
KANJI_NUM_RE = re.compile(u"[二三四五六七八九]百|[一二三四五六七八九]千|百[一二三四五六七八九十]|千[一二三四五六七八九百]")        # 3 桁以上の数を漢数字で逃がす字(「百万円」の単位は当たらない)
JA_RE = re.compile(u"[぀-ヿ一-鿿]")
LONG_JA = 40
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
TYPED_BY = u"司令塔(AI の席)。人は読んでいない"
TYPES_BLIND = u"盲検ではない(封の予測を知ったうえで付けた)。(あ)は候補で、紙面で確かめていない"
INTERIM_STEP = u"TSS 第 2 便(一)― 中間 150 本の期の名前を写した判定(0 USD・通信なし)"
NEAR_STEP = u"TSS 第 2 便(二)― 「値が違う」のうち表の値に近い行(0 USD・通信なし)"
TYPES_STEP = u"TSS 第 2 便(二)― 近い行を読んだ型分け(0 USD)"
FORBIDDEN_KEYS = tuple(MS.TS.RUN.FORBIDDEN_KEYS) + (u"pointers", u"pointer", u"要素", u"element", u"context", u"label", u"会社名", u"subject", u"span", u"value", u"text", u"文")
INTERIM_KEYS = (u"seal", u"封の commit", u"step", u"HEAD の commit", u"この script の sha256", u"TSS の script の sha256", u"置く script の sha256", u"2026-11-09 の便の script の sha256",
                u"engine の指紋", u"profile", u"材料", u"置き換え(この順。二重引用符から始まる byte 列)", u"置き換えを掛ける member", u"名前がぶつかる印(置き換える前に在れば写さない)",
                u"本の数", u"名前がぶつかる本", u"名前がぶつかる本のうち切れた本", u"写した本", u"置き換えた回数の合計(規則 1・2・3)", u"集計", u"TSS の B(写さない)との動き", u"限界", u"行の欄",
                u"時間(秒)", u"key_leaks", u"本")
NEAR_KEYS = (u"seal", u"封の commit", u"step", u"HEAD の commit", u"この script の sha256", u"TSS の script の sha256", u"置く script の sha256", u"2026-11-09 の便の script の sha256",
             u"engine の指紋", u"profile", u"材料", u"interim の記録の sha256", u"TSS の判定の記録の sha256", u"規則", u"母集団の本", u"A の state が TSS の記録と同じか",
             u"B の state が interim の記録と同じか", u"集計", u"近い行の数(A と B)", u"読む行の規則", u"限界", u"行の欄", u"時間(秒)", u"key_leaks", u"行")
TYPES_KEYS = (u"seal", u"封の commit", u"step", u"HEAD の commit", u"この script の sha256", u"near の記録の sha256", u"型を付けた席", u"盲検", u"読む行の規則", u"型の字",
              u"型の集計", u"型の集計(A)", u"型の集計(B)", u"行の欄", u"行", u"key_leaks")
BOOK_COLS = (u"#", u"群", u"様式の種類", u"ZIP の sha256", u"切り出し", u"理由", u"見出しの番号", u"字数", u"入れた iXBRL の file の数", u"fact の数", u"claim", u"対応", u"行", u"名前がぶつかる", u"写した", u"置き換えた回数")
ROW_COLS = [u"文の番号", u"位置", u"state", u"reason", u"pointer の期", u"formula の有無", u"単位の族", u"両期の fact を引く a−b", u"span に % を含む"]
AGG_KEYS = (u"本", u"切れた", u"切れない", u"切れない理由", u"見出しの番号の本数", u"字数の合計", u"入れた iXBRL の file の数の合計", u"fact の数の合計", u"claim", u"4 state", u"reason",
            u"VALUE_MISMATCH の内訳", u"切れた本のうち claim が 0 の本", u"切れた本のうち GROUNDED が 0 の本", u"VALUE_MISMATCH が 1 以上の本", u"claim と raw の並びが対応しなかった本")
VM_KEYS = (u"行", u"導出(formula)", u"直接", u"% の数", u"円族の数", u"両期の fact を引く a−b(円)", u"単位の族が %", u"単位の族が円族", u"単位の族が他", u"pointer の期")
NEAR_AGG_KEYS = (u"本", u"VALUE_MISMATCH の行", u"うち recomputed が数でない行", u"近い行", u"規則ごとの行の数", u"規則ごとの 1 行以上持つ本の数", u"近い行を 1 行以上持つ本")
MOVE_KEYS = (u"行(写す前 → 写した後)", u"動いた行", u"GROUNDED だった行のうち GROUNDED でなくなった行", u"写す前にだけ在る行", u"写した後にだけ在る行")

# ---- 封の予測の幅(封 §3 の字に在ることを seal_problems が確かめる。判定はこの幅で作る)
BOUNDS = collections.OrderedDict([(u"U-6", (0, 60)), (u"U-7A", (60, 260)), (u"U-7B", (20, 110)), (u"U-9A", (0, 12)), (u"U-9B", (0, 8))])
BOUND_PHRASES = (u"**0〜60 行**", u"**A は 60〜260 行**", u"**B は 20〜110 行**", u"**A で 0〜12 行・B で 0〜8 行**", u"読んだ行の 10% 以下")
SEALED_NUMBERS = collections.OrderedDict([(u"U-1", (0, 133, 17)), (u"U-2", (6834, 2152, 779, 1301, 2602)), (u"U-3", (779, 541, 198, 115, 11))])
LABELS = collections.OrderedDict([
    (u"U-1", u"名前がぶつかる本・切れた本・切れない本"), (u"U-2", u"写した中間の数の claim と 4 state"), (u"U-3", u"VALUE_MISMATCH の中身・本の数"),
    (u"U-4", u"A をもう 1 回走らせた行の state"), (u"U-5", u"2 回走らせた記録"), (u"U-6", u"写す前の GROUNDED が写した後に GROUNDED でなくなった行"),
    (u"U-7", u"近い行の数"), (u"U-8", u"A の近い行でいちばん多い規則"), (u"U-9", u"読んだ行の (あ) の数・いちばん多い型"), (u"U-10", u"(お) の割合")])
U5_ACTUAL = u"追跡している記録に在るのは 1 回目だけ。実装の席が結果の段で材料から 1 回測り直し(interim と near の 2 つの記録)、時間の欄を除いて byte で同じだった"
U5_JUDGE = u"当たり(一回限りの手の実測で、門ではない。材料の在る機械でだけ走る試験は環境変数つき)"


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


def tmpdir():
    return tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR"))


_TEXT = {}


def cached_text(rel):
    if rel not in _TEXT:
        _TEXT[rel] = read(rel)
    return _TEXT[rel]


class Ctx(object):
    u"""記録・封・文書・今の file の値。変異は毎回 ``Ctx()`` の新しい写しに 1 か所だけ加える。"""

    def __init__(self):
        self.I = json.loads(cached_text(INTERIM_REL))
        self.N = json.loads(cached_text(NEAR_REL))
        self.Ty = json.loads(cached_text(TYPES_REL))
        self.T = json.loads(cached_text(TSS_STATES_REL))
        self.seal = cached_text(SEAL_REL)
        self.doc = cached_text(DOC_REL) if os.path.exists(os.path.join(ROOT, DOC_REL)) else u""
        self.texts = collections.OrderedDict((rel, read_bytes(rel)) for rel in SHA_PIN)         # sha256 を見る file の中身
        self.cur = {"script": sha256_rel(SCRIPT_REL), "tss": sha256_rel(TSS_REL), "stage": sha256_rel(STAGE_REL), "prev": sha256_rel(MS.TSS.TS_SCRIPT_REL),
                    "tss_states": sha256_rel(TSS_STATES_REL), "interim": sha256_rel(INTERIM_REL), "near": sha256_rel(NEAR_REL), "fp": MS.VD.engine_fingerprint()}


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


def provenance_problems(c, root=REPO):
    u"""3 つの記録の header: seal・封の commit・step・script の sha256 4 本・第 1 便の判定の記録の sha256・interim・near の記録の sha256・engine の指紋・HEAD の commit。"""
    out = []
    cur = c.cur
    for name, rec, keys, step in ((u"interim", c.I, INTERIM_KEYS, INTERIM_STEP), (u"near", c.N, NEAR_KEYS, NEAR_STEP), (u"types", c.Ty, TYPES_KEYS, TYPES_STEP)):
        if len(rec.keys()) != len(keys) or set(rec.keys()) != set(keys):
            out.append(u"来歴[%s]: 欄の名前の集合が字で留めたものと違う" % name)
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
    for name, rec in ((u"interim", c.I), (u"near", c.N)):
        if rec.get(u"TSS の script の sha256") != cur["tss"]:
            out.append(u"来歴[%s]: TSS の script の sha256 が今の file と違う" % name)
        if rec.get(u"置く script の sha256") != cur["stage"]:
            out.append(u"来歴[%s]: 置く script の sha256 が今の file と違う" % name)
        if rec.get(u"2026-11-09 の便の script の sha256") != cur["prev"]:
            out.append(u"来歴[%s]: 2026-11-09 の便の script の sha256 が今の file と違う" % name)
        fp = rec.get(u"engine の指紋") or {}
        if fp.get(u"adapter_xbrl_py_sha256") != cur["fp"]["adapter_xbrl_py_sha256"] or fp.get(u"core_py_sha256") != cur["fp"]["core_py_sha256"] \
                or fp.get(u"adapter_xbrl_py_files") != cur["fp"]["adapter_xbrl_py_files"] or fp.get(u"core_py_files") != cur["fp"]["core_py_files"]:
            out.append(u"来歴[%s]: engine の指紋が今の engine と違う" % name)
        if rec.get(u"profile") != u"P33E":
            out.append(u"来歴[%s]: profile が P33E でない" % name)
        m = rec.get(u"材料") or {}
        z = m.get(u"置き場の一覧の前後") or {}
        if m.get(u"表と一致した ZIP") != 400 or z.get(u"変化なし") is not True or z.get(u"前") != z.get(u"後") or not isinstance(z.get(u"前"), list) or z[u"前"][0] != 400 \
                or not HEX64.match(str(z[u"前"][1])):
            out.append(u"来歴[%s]: 材料が「400・前後の変化なし」でない" % name)
        t = rec.get(u"時間(秒)")
        if isinstance(t, bool) or not isinstance(t, (int, float)) or t < 0:
            out.append(u"来歴[%s]: 時間(秒)が数でない" % name)
    if c.N.get(u"interim の記録の sha256") != cur["interim"]:
        out.append(u"来歴[near]: interim の記録の sha256 が今の file と違う")
    if c.N.get(u"TSS の判定の記録の sha256") != cur["tss_states"]:
        out.append(u"来歴[near]: TSS の判定の記録の sha256 が今の file と違う")
    if c.Ty.get(u"near の記録の sha256") != cur["near"]:
        out.append(u"来歴[types]: near の記録の sha256 が今の file と違う")
    if c.Ty.get(u"型を付けた席") != TYPED_BY or c.Ty.get(u"型を付けた席") != MS.TYPED_BY:
        out.append(u"来歴[types]: 型を付けた席の字が違う")
    if c.Ty.get(u"盲検") != TYPES_BLIND:
        out.append(u"来歴[types]: 盲検の欄が違う")
    if c.Ty.get(u"型の字") != dict(MS.TYPES) or list(c.Ty.get(u"型の字", {}).keys()) != list(TYPE_KEYS):
        out.append(u"来歴[types]: 型の字が封の 5 つと違う")
    if c.I.get(u"行の欄") != ROW_COLS or c.N.get(u"行の欄") != list(MS.NEAR_ROW_COLUMNS) or c.Ty.get(u"行の欄") != [u"標本の番号", u"本の #", u"文の番号", u"位置", u"型"]:
        out.append(u"来歴: 行の欄が封のとおりでない")
    if c.I.get(u"限界") != list(MS.INTERIM_LIMITS) or c.N.get(u"限界") != list(MS.NEAR_LIMITS):
        out.append(u"来歴: 限界が script の字と違う")
    if c.I.get(u"置き換え(この順。二重引用符から始まる byte 列)") != [[a.decode("ascii"), b.decode("ascii")] for a, b in MS.REPLACEMENTS] \
            or c.I.get(u"名前がぶつかる印(置き換える前に在れば写さない)") != [m.decode("ascii") for m in MS.COLLISION_MARKS]:
        out.append(u"来歴[interim]: 置き換え・名前がぶつかる印が封の字と違う")
    return out


# ======================================================================================================
# c. interim
def book_cut(b):
    return b[u"切り出し"] == u"切れた"


def recount_interim(books):
    u"""interim の集計を、本の行から別の書き方で数え直す(script の ``block`` は使わない)。"""
    cut = [b for b in books if book_cut(b)]
    rows = [r for b in books for r in b[u"行"]]
    vm = [r for r in rows if r[2] == VM]
    rs = collections.OrderedDict()
    for s in STATES:
        rs[s] = collections.Counter(u"なし" if r[3] is None else r[3] for r in rows if r[2] == s)
    pk = collections.Counter(r[4] for r in vm)
    return collections.OrderedDict([
        (u"本", len(books)), (u"切れた", len(cut)), (u"切れない", len(books) - len(cut)),
        (u"切れない理由", collections.OrderedDict((k, sum(1 for b in books if not book_cut(b) and b[u"理由"] == k)) for k in (u"member なし", u"decode", u"始まりなし", u"終わりなし"))),
        (u"見出しの番号の本数", collections.OrderedDict((k, sum(1 for b in cut if b[u"見出しの番号"] == int(k))) for k in (u"0", u"1", u"2"))),
        (u"字数の合計", sum(b[u"字数"] for b in cut)), (u"入れた iXBRL の file の数の合計", sum(b[u"入れた iXBRL の file の数"] for b in cut)), (u"fact の数の合計", sum(b[u"fact の数"] for b in cut)),
        (u"claim", len(rows)), (u"4 state", collections.OrderedDict((s, sum(1 for r in rows if r[2] == s)) for s in STATES)),
        (u"reason", collections.OrderedDict((s, dict(rs[s])) for s in STATES)),
        (u"VALUE_MISMATCH の内訳", collections.OrderedDict([
            (u"行", len(vm)), (u"導出(formula)", sum(1 for r in vm if r[5])), (u"直接", sum(1 for r in vm if not r[5])), (u"% の数", sum(1 for r in vm if r[8])),
            (u"円族の数", sum(1 for r in vm if not r[8])), (u"両期の fact を引く a−b(円)", sum(1 for r in vm if r[7])),
            (u"単位の族が %", sum(1 for r in vm if r[6] == u"%")), (u"単位の族が円族", sum(1 for r in vm if r[6] == u"円族")), (u"単位の族が他", sum(1 for r in vm if r[6] == u"他")),
            (u"pointer の期", collections.OrderedDict((k, pk.get(k, 0)) for k in (u"CurrentYear", u"Prior1Year", u"Prior2Year", u"他", u"なし")))])),
        (u"切れた本のうち claim が 0 の本", sum(1 for b in cut if not b[u"行"])), (u"切れた本のうち GROUNDED が 0 の本", sum(1 for b in cut if not any(r[2] == G for r in b[u"行"]))),
        (u"VALUE_MISMATCH が 1 以上の本", sum(1 for b in cut if any(r[2] == VM for r in b[u"行"]))), (u"claim と raw の並びが対応しなかった本", sum(1 for b in cut if b[u"対応"] is not True))])


def plain(x):
    return json.loads(json.dumps(x, ensure_ascii=False))


def recount_moves(books, tss_books):
    u"""第 1 便の B の行(写さない)と、写した行を (本の #, 文の番号, 位置) で結んだ 4 × 4 の動き。"""
    tb = dict((b[u"#"], b) for b in tss_books)
    mv = collections.OrderedDict((s, collections.OrderedDict((t, 0) for t in STATES)) for s in STATES)
    only_before = only_after = 0
    for b in books:
        t = tb.get(b[u"#"])
        if t is None:
            continue
        before = dict(((r[0], r[1]), r[2]) for r in t[u"行"])
        after = dict(((r[0], r[1]), r[2]) for r in b[u"行"])
        for k in before:
            if k in after:
                mv[before[k]][after[k]] += 1
            else:
                only_before += 1
        only_after += sum(1 for k in after if k not in before)
    moved = sum(n for s in STATES for t in STATES if s != t for n in [mv[s][t]])
    lost = sum(mv[G][t] for t in STATES if t != G)
    return plain(collections.OrderedDict([(MOVE_KEYS[0], mv), (MOVE_KEYS[1], moved), (MOVE_KEYS[2], lost), (MOVE_KEYS[3], only_before), (MOVE_KEYS[4], only_after)]))


def interim_problems(c):
    I, T = c.I, c.T
    out = []
    books = I.get(u"本") or []
    tb = dict((b[u"#"], b) for b in T[u"本"] if b[u"群"] == u"丙")
    if I.get(u"本の数") != 150 or len(books) != 150 or [b[u"#"] for b in books] != list(range(A_MAX + 1, 401)) or sorted(tb) != list(range(A_MAX + 1, 401)):
        out.append(u"interim: 本が # 251〜400 の 150 本でない")
        return out
    shape_bad = False
    for b in books:
        if tuple(b.keys()) != BOOK_COLS:
            out.append(u"interim: 本の欄が違う(# %s)" % b.get(u"#"))
            shape_bad = True
            continue
        t = tb[b[u"#"]]
        for k in (u"群", u"様式の種類", u"ZIP の sha256", u"切り出し", u"理由"):
            if b[k] != t[k]:
                out.append(u"interim: 本 %d の %s が第 1 便の記録と違う(切り出しは写しても変わらない)" % (b[u"#"], k))
        cut = book_cut(b)
        if b[u"claim"] != len(b[u"行"]) or not is_int(b[u"claim"]):
            out.append(u"interim: 本 %d の claim が行の数と違う" % b[u"#"])
        if b[u"写した"] is not (cut and not b[u"名前がぶつかる"]):
            out.append(u"interim: 本 %d の「写した」が「切れた かつ ぶつからない」でない" % b[u"#"])
        sw = b[u"置き換えた回数"]
        if not (isinstance(sw, list) and len(sw) == 3 and all(is_int(x) and x >= 0 for x in sw)) or (not b[u"写した"] and sw != [0, 0, 0]):
            out.append(u"interim: 本 %d の置き換えた回数が「3 つの数・写さない本は 0」でない" % b[u"#"])
        if [(r[0], r[1]) for r in b[u"行"]] != [(r[0], r[1]) for r in t[u"行"]]:
            out.append(u"interim: 本 %d の行の並びが第 1 便の記録と違う(写す前にだけ・写した後にだけ在る行)" % b[u"#"])
        if not cut and (b[u"行"] or b[u"claim"]):
            out.append(u"interim: 切れない本 %d に行が在る" % b[u"#"])
        for r in b[u"行"]:
            if not (len(r) == 9 and is_int(r[0]) and is_int(r[1]) and r[2] in STATES and isinstance(r[5], bool) and isinstance(r[7], bool) and isinstance(r[8], bool)
                    and r[6] in (u"%", u"円族", u"他") and (r[3] is None or isinstance(r[3], str))):
                out.append(u"interim: 本 %d の行が封の形(9 欄)でない" % b[u"#"])
                shape_bad = True
                break
    if shape_bad:
        return out                                   # 形が壊れた記録は数え直さない(数え直しが例外で落ちて赤になるのを避ける)
    want = recount_interim(books)
    got = I.get(u"集計") or {}
    if tuple(got.keys()) != AGG_KEYS:
        out.append(u"interim: 集計の欄の名前が違う")
    for k in want:
        if plain(want[k]) != plain(got.get(k)):
            out.append(u"interim: 集計 %s が行から数え直した値と違う" % k)
    if tuple((got.get(u"VALUE_MISMATCH の内訳") or {}).keys()) != VM_KEYS:
        out.append(u"interim: VALUE_MISMATCH の内訳の欄の名前が違う")
    if I.get(u"名前がぶつかる本") != sum(1 for b in books if b[u"名前がぶつかる"]) or I.get(u"名前がぶつかる本のうち切れた本") != sum(1 for b in books if b[u"名前がぶつかる"] and book_cut(b)):
        out.append(u"interim: 名前がぶつかる本の数が行から数え直した値と違う")
    if I.get(u"写した本") != sum(1 for b in books if b[u"写した"]):
        out.append(u"interim: 写した本の数が数え直した値と違う")
    if I.get(u"置き換えた回数の合計(規則 1・2・3)") != [sum(b[u"置き換えた回数"][i] for b in books) for i in range(3)]:
        out.append(u"interim: 置き換えた回数の合計が本の欄の和と違う")
    mv = recount_moves(books, T[u"本"])
    if plain(I.get(u"TSS の B(写さない)との動き")) != mv:
        out.append(u"interim: 動きの表が第 1 便の B の行と写した行から数え直した値と違う")
    m = mv[MOVE_KEYS[0]]
    tssB = T[u"集計"][u"B(丙)"][u"4 state"]
    if any(sum(m[s].values()) != tssB[s] for s in STATES):
        out.append(u"interim: 動きの表の行の和が第 1 便の B の 4 state と違う")
    if any(sum(m[s][t] for s in STATES) != got.get(u"4 state", {}).get(t) for t in STATES):
        out.append(u"interim: 動きの表の列の和が写した後の 4 state と違う")
    if sum(sum(v.values()) for v in m.values()) != got.get(u"claim"):
        out.append(u"interim: 動きの表の全部の和が claim の数と違う")
    return out


# ======================================================================================================
# d. near
def vm_keys(c):
    u"""A(第 1 便の記録の # 250 以下)と B(interim の記録)の VALUE_MISMATCH の行 {(本の #, 文の番号, 位置): 単位の族}。"""
    d = {}
    for b in c.T[u"本"]:
        if b[u"#"] <= A_MAX:
            for r in b[u"行"]:
                if r[2] == VM:
                    d[(b[u"#"], r[0], r[1])] = r[6]
    for b in c.I[u"本"]:
        for r in b[u"行"]:
            if r[2] == VM:
                d[(b[u"#"], r[0], r[1])] = r[6]
    return d


def near_aggregate(rows, vmk, lo, hi):
    sel = [r for r in rows if lo <= r[0] <= hi]
    vmn = sum(1 for k in vmk if lo <= k[0] <= hi)
    rule_rows = dict((u, sum(1 for r in sel if u in r[3])) for u in RULES)
    rule_books = dict((u, len(set(r[0] for r in sel if u in r[3]))) for u in RULES)
    return vmn, len(sel), rule_rows, rule_books, len(set(r[0] for r in sel))


def near_problems(c):
    N, I, T = c.N, c.I, c.T
    out = []
    rows = N.get(u"行") or []
    vmk = vm_keys(c)
    if N.get(u"母集団の本") != {u"A": 250, u"B": 150}:
        out.append(u"near: 母集団の本が A 250・B 150 でない")
    a_rows = sum(len(b[u"行"]) for b in T[u"本"] if b[u"#"] <= A_MAX)
    b_rows = sum(len(b[u"行"]) for b in I[u"本"])
    if N.get(u"A の state が TSS の記録と同じか") != {u"本": 250, u"行": a_rows, u"違う本": 0}:
        out.append(u"near: A の照合の欄が「250 本・第 1 便の A の行の数・違う本 0」でない")
    if N.get(u"B の state が interim の記録と同じか") != {u"本": 150, u"行": b_rows, u"違う本": 0}:
        out.append(u"near: B の照合の欄が「150 本・interim の行の数・違う本 0」でない")
    keys = [(r[0], r[1], r[2]) for r in rows]
    if keys != sorted(set(keys)):
        out.append(u"near: 行が (本の #・文の番号・位置) の昇順で 1 行ずつでない")
    for r in rows:
        if not (len(r) == 5 and all(is_int(x) for x in r[:3]) and isinstance(r[3], list) and r[3] and isinstance(r[4], str)):
            out.append(u"near: 行が封の形(本の #・文の番号・位置・当たった規則・単位の族)でない")
            break
        k = (r[0], r[1], r[2])
        if k not in vmk:
            out.append(u"near: 近い行が「値が違う」の行でない(本 %d)" % r[0])
        elif vmk[k] != r[4]:
            out.append(u"near: 単位の族が判定の記録の行と違う(本 %d)" % r[0])
        if [u for u in r[3] if u in RULES] != r[3] or r[3] != sorted(set(r[3]), key=RULES.index):
            out.append(u"near: 当たった規則が封の 3 つを順に 1 回ずつでない(本 %d)" % r[0])
        elif (u"N-率" in r[3]) != (r[4] == u"%") or (u"N-率" in r[3] and len(r[3]) != 1) or (r[4] == u"円族" and u"N-率" in r[3]):
            out.append(u"near: 規則と単位の族が合わない(N-率 は %% だけ・N-円と N-桁は円族だけ。本 %d)" % r[0])
    if N.get(u"近い行の数(A と B)") != len(rows):
        out.append(u"near: 近い行の数が行の数と違う")
    agg = N.get(u"集計") or {}
    for name, lo, hi, n in ((u"A(甲 + 乙)", 1, A_MAX, 250), (u"B(丙)", A_MAX + 1, 400, 150)):
        g = agg.get(name) or {}
        vmn, nr, rr, rb, nb = near_aggregate(rows, vmk, lo, hi)
        want = collections.OrderedDict([(NEAR_AGG_KEYS[0], n), (NEAR_AGG_KEYS[1], vmn), (NEAR_AGG_KEYS[2], 0), (NEAR_AGG_KEYS[3], nr), (NEAR_AGG_KEYS[4], rr), (NEAR_AGG_KEYS[5], rb), (NEAR_AGG_KEYS[6], nb)])
        if tuple(g.keys()) != NEAR_AGG_KEYS or plain(g) != plain(want):
            out.append(u"near: 集計 %s が行から数え直した値と違う" % name)
    rule = N.get(u"読む行の規則") or {}
    if rule.get(u"種") != SEED or rule.get(u"標本の数") != SAMPLE_N or rule.get(u"近い行の数") != len(rows) or rule.get(u"読む行の数") != min(SAMPLE_N, len(rows)):
        out.append(u"near: 読む行の規則の欄(種・標本の数・近い行の数・読む行の数)が違う")
    return out


# ======================================================================================================
# e. near_types
def types_problems(c):
    Ty, N = c.Ty, c.N
    out = []
    rows = Ty.get(u"行") or []
    nrows = N.get(u"行") or []
    if len(nrows) < SAMPLE_N:
        return [u"types: 近い行が 200 行に満たない"]
    idx = sorted(random.Random(SEED).sample(range(len(nrows)), SAMPLE_N))
    if len(rows) != SAMPLE_N:
        out.append(u"types: 行の数が 200 でない")
    for k, r in enumerate(rows):
        if not (len(r) == 5 and all(is_int(x) for x in r[:4]) and r[4] in TYPE_KEYS and r[0] == k + 1):
            out.append(u"types: 行 %d が「標本の番号(1 から)・本の #・文の番号・位置・型(あ〜お)」でない" % (k + 1))
            break
    got = [tuple(r[1:4]) for r in rows]
    want = [tuple(nrows[i][:3]) for i in idx]
    if got != want:
        out.append(u"types: 標本が random.Random(20261115).sample(range(近い行の数), 200) を番号の順にした近い行と 1 行ずつ同じでない")
    rule = Ty.get(u"読む行の規則") or {}
    if rule.get(u"種") != SEED or rule.get(u"近い行の数") != len(nrows) or rule.get(u"読む行の数") != len(rows):
        out.append(u"types: 読む行の規則の欄が違う")
    cnt = collections.Counter(r[4] for r in rows)
    cnt_a = collections.Counter(r[4] for r in rows if r[1] <= A_MAX)
    cnt_b = collections.Counter(r[4] for r in rows if r[1] > A_MAX)
    for key, ct in ((u"型の集計", cnt), (u"型の集計(A)", cnt_a), (u"型の集計(B)", cnt_b)):
        g = Ty.get(key) or {}
        if list(g.keys()) != list(TYPE_KEYS) or any(g[t] != ct.get(t, 0) for t in TYPE_KEYS):
            out.append(u"types: %s が行から数え直した値と違う" % key)
    g, ga, gb = (Ty.get(u"型の集計") or {}), (Ty.get(u"型の集計(A)") or {}), (Ty.get(u"型の集計(B)") or {})
    if sum(g.values()) != len(rows) or any(ga.get(t, 0) + gb.get(t, 0) != g.get(t) for t in TYPE_KEYS) or sum(ga.values()) + sum(gb.values()) != sum(g.values()):
        out.append(u"types: 型の集計の和(全体 = 行の数・A と B の和 = 全体)が合わない")
    return out


# ======================================================================================================
# f. 記録に書かないものが漏れていない
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


def walk_kv(x, key=None, acc=None):
    u"""(直前の dict の key, 葉)の列。list の中の葉は list を持つ key を引き継ぐ。"""
    acc = [] if acc is None else acc
    if isinstance(x, dict):
        for k, v in x.items():
            acc.append((None, k))
            walk_kv(v, k, acc)
    elif isinstance(x, list):
        for v in x:
            walk_kv(v, key, acc)
    else:
        acc.append((key, x))
    return acc


#: 規則の説明(封 §0-2 の字を写した短い定義)を持つ header の欄。ここの下の長い日本語は文でなく規則の説明
RULE_TEXT_KEYS = (u"置き換えを掛ける member", u"対象", u"N-円", u"N-桁", u"N-率", u"数の比べ方", u"引き方", u"母集団")


def long_ok():
    s = set(MS.INTERIM_LIMITS) | set(MS.NEAR_LIMITS) | set(MS.TYPES.values()) | set([TYPES_BLIND, TYPED_BY, INTERIM_STEP, NEAR_STEP, TYPES_STEP])
    s |= set([u"始まりなし"])
    return s


def clean_problems(c):
    u"""記録に文・値・会社名・証券コード・pointer の字・docID・TDnet の番号が無い。門が自前で全部の key と葉を歩く(script の check_clean とは別)。"""
    out = []
    ok = long_ok()
    for name, rec in ((u"interim", c.I), (u"near", c.N), (u"types", c.Ty)):
        if rec.get(u"key_leaks") != []:
            out.append(u"clean[%s]: key_leaks が空でない" % name)
        leaves = walk(rec)
        rule_text = set(v for k, v in walk_kv(rec) if k in RULE_TEXT_KEYS and isinstance(v, str))
        bad = sorted(set(k for k in leaves if isinstance(k, str) and k in FORBIDDEN_KEYS))
        if bad:
            out.append(u"clean[%s]: repo へ入れない欄がある: %s" % (name, u",".join(bad)))
        for s in leaves:
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
            if len(s) >= LONG_JA and JA_RE.search(s) and s not in ok and s not in rule_text:
                out.append(u"clean[%s]: 留めた字に無い長い日本語の文がある" % name)
            if CODE_RE.search(s) and not HEX64.match(s) and not HEX40.match(s):
                out.append(u"clean[%s]: 証券コードの形の字がある(%s)" % (name, s[:12]))
    for b in c.I.get(u"本") or []:                         # 本の中の字は閉じた語彙(会社名・文が入る場所が無い)
        for k in (u"群", u"様式の種類", u"理由", u"切り出し"):
            v = b.get(k)
            if v is not None and (not isinstance(v, str) or len(v) > 12):
                out.append(u"clean[interim]: 本の %s が短い語彙でない" % k)
    for r in (c.N.get(u"行") or []):
        if len(r) != 5 or not (all(is_int(x) for x in r[:3]) and all(x in RULES for x in r[3]) and r[4] in (u"%", u"円族")):
            out.append(u"clean[near]: 行が「数 3 つ・規則・単位の族」だけでない")
            break
    return out


# ======================================================================================================
# g. 結果の文書
def seal_bullets(seal):
    u"""封 §3 の U-1〜U-10 の箇条(id → 本文。「外れ方」の手前まで)。"""
    sec = seal[seal.index(u"## §3"):seal.index(u"## §4")]
    out = collections.OrderedDict()
    for m in re.finditer(r"^- \*\*(U-\d+)\*\* (.*)$", sec, re.M):
        out[m.group(1)] = m.group(2).split(u" 外れ方:")[0].strip()
    return out


def seal_problems(seal):
    out = []
    try:
        b = seal_bullets(seal)
    except ValueError:
        return [u"封の節が揃っていない"]
    if list(b.keys()) != [u"U-%d" % i for i in range(1, 11)]:
        out.append(u"封 §3 が U-1〜U-10 の 10 行でない")
        return out
    for ph in BOUND_PHRASES:
        if ph not in seal:
            out.append(u"封に予測の幅の字が無い: %s" % ph)
    for uid, nums in SEALED_NUMBERS.items():
        for n in nums:
            if (fmt(n) if n >= 1000 else str(n)) not in b[uid] and str(n) not in b[uid]:
                out.append(u"封 %s に数 %d が無い" % (uid, n))
    return out


def seal_frozen_problems(seal_text, root=REPO):
    u"""封が a1fd09bf の commit のときの byte と同じか(1 字も変わっていない。未 commit の編集も見る)。"""
    rc, _ = PR.git_in(root, "cat-file", "-e", SEAL_COMMIT_SHORT + "^{commit}")
    if rc != 0:
        return [u"封の commit が履歴に無い"]
    r = subprocess.run(["git", "show", "%s:%s%s" % (SEAL_COMMIT_SHORT, PREFIX, SEAL_REL)], cwd=root, capture_output=True)
    if r.returncode != 0:
        return [u"封の commit に封の file が無い"]
    if r.stdout != seal_text.encode("utf-8"):
        return [u"封が %s のときの byte から変わっている" % SEAL_COMMIT_SHORT]
    return []


def pred_table(c):
    u"""封 §3 の U-1〜U-10 を、記録から判定した行(id, 欄, 予測(封), 実測, 判定)の列にする。"""
    I, N, Ty = c.I, c.N, c.Ty
    cells = seal_bullets(c.seal)
    ia, mv = I[u"集計"], I[u"TSS の B(写さない)との動き"]
    s4, vmb = ia[u"4 state"], ia[u"VALUE_MISMATCH の内訳"]
    na, nb = N[u"集計"][u"A(甲 + 乙)"], N[u"集計"][u"B(丙)"]
    tc, ta, tb = Ty[u"型の集計"], Ty[u"型の集計(A)"], Ty[u"型の集計(B)"]
    rows = collections.OrderedDict()

    def hit(ok):
        return u"当たり" if ok else u"外れ"

    def inb(n, key):
        lo, hi = BOUNDS[key]
        return lo <= n <= hi
    v1 = (I[u"名前がぶつかる本"], ia[u"切れた"], ia[u"切れない"])
    rows[u"U-1"] = (u"ぶつかる本 %d・切れた %d・切れない %d" % v1, hit(v1 == SEALED_NUMBERS[u"U-1"]))
    v2 = (ia[u"claim"], s4[G], s4[VM], s4[UNV], s4[PNF])
    rows[u"U-2"] = (u"%s = %s / %s / %s / %s" % tuple(fmt(x) for x in v2), hit(v2 == SEALED_NUMBERS[u"U-2"]))
    v3 = (vmb[u"行"], vmb[u"% の数"], vmb[u"導出(formula)"], ia[u"VALUE_MISMATCH が 1 以上の本"], ia[u"切れた本のうち GROUNDED が 0 の本"])
    rows[u"U-3"] = (u"VALUE_MISMATCH %d のうち span に %% %d・導出 %d。VALUE_MISMATCH が 1 以上の本 %d・GROUNDED が 0 の本 %d" % v3, hit(v3 == SEALED_NUMBERS[u"U-3"]))
    ca = N[u"A の state が TSS の記録と同じか"]
    rows[u"U-4"] = (u"A %d 本・%s 行のうち、第 1 便の記録と違う本 %d" % (ca[u"本"], fmt(ca[u"行"]), ca[u"違う本"]), hit(ca[u"違う本"] == 0 and ca[u"本"] == 250))
    rows[u"U-5"] = (U5_ACTUAL, U5_JUDGE)
    lost = mv[MOVE_KEYS[2]]
    gtot = sum(mv[MOVE_KEYS[0]][G].values())
    rows[u"U-6"] = (u"写す前の GROUNDED %s 行のうち %d 行" % (fmt(gtot), lost), hit(inb(lost, u"U-6")))
    rows[u"U-7"] = (u"A %d 行・B %d 行" % (na[u"近い行"], nb[u"近い行"]), hit(inb(na[u"近い行"], u"U-7A") and inb(nb[u"近い行"], u"U-7B")))
    rr, rb = na[u"規則ごとの行の数"], na[u"規則ごとの 1 行以上持つ本の数"]
    top = sorted(rr, key=lambda k: -rr[k])
    rows[u"U-8"] = (u"A の規則ごとの行 N-円 %d・N-桁 %d・N-率 %d(1 行以上持つ本は N-円 %d・N-桁 %d・N-率 %d)" % (rr[u"N-円"], rr[u"N-桁"], rr[u"N-率"], rb[u"N-円"], rb[u"N-桁"], rb[u"N-率"]),
                    hit(rr[top[0]] > rr[top[1]] and top[0] == u"N-率"))
    topa = sorted(TYPE_KEYS, key=lambda t: -ta[t])
    topb = sorted(TYPE_KEYS, key=lambda t: -tb[t])
    ok9 = inb(ta[u"あ"], u"U-9A") and inb(tb[u"あ"], u"U-9B") and ta[topa[0]] > ta[topa[1]] and tb[topb[0]] > tb[topb[1]] and topa[0] == u"い" and topb[0] == u"い"
    rows[u"U-9"] = (u"(あ) A %d 行・B %d 行。いちばん多い型は A (%s) %d 行・B (%s) %d 行" % (ta[u"あ"], tb[u"あ"], topa[0], ta[topa[0]], topb[0], tb[topb[0]]), hit(ok9))
    tot = sum(tc.values())
    rows[u"U-10"] = (u"(お) %d 行 / 読んだ %d 行 = %s" % (tc[u"お"], tot, pct(tc[u"お"], tot)), hit(tc[u"お"] * 10 <= tot))
    return [(uid, LABELS[uid], cells[uid], rows[uid][0], rows[uid][1]) for uid in rows]


def _sep(n):
    return u"|" + u"---|" * n


def build_blocks(c):
    I, N, Ty, T = c.I, c.N, c.Ty, c.T
    ia, mv = I[u"集計"], I[u"TSS の B(写さない)との動き"]
    tb = T[u"集計"][u"B(丙)"]
    blocks = collections.OrderedDict()
    lines = [u"| # | 欄 | 予測(封) | 実測 | 判定 |", _sep(5)]
    for r in pred_table(c):
        lines.append(u"| %s | %s | %s | %s | %s |" % r)
    blocks[u"pred"] = lines
    s_after, s_before = ia[u"4 state"], tb[u"4 state"]
    lines = [u"| 欄 | 写さない(第 1 便の B) | 期の名前を写した |", _sep(3)]
    lines.append(u"| 本 | %s | %s |" % (fmt(tb[u"本"]), fmt(ia[u"本"])))
    lines.append(u"| 切れた | %s | %s |" % (fmt(tb[u"切れた"]), fmt(ia[u"切れた"])))
    lines.append(u"| 切れない | %s | %s |" % (fmt(tb[u"切れない"]), fmt(ia[u"切れない"])))
    lines.append(u"| 名前がぶつかる本 | - | %s |" % fmt(I[u"名前がぶつかる本"]))
    lines.append(u"| 写した本 | 0 | %s |" % fmt(I[u"写した本"]))
    lines.append(u"| fact の数の合計 | %s | %s |" % (fmt(tb[u"fact の数の合計"]), fmt(ia[u"fact の数の合計"])))
    lines.append(u"| 数の claim | %s | %s |" % (fmt(tb[u"claim"]), fmt(ia[u"claim"])))
    for s in STATES:
        lines.append(u"| %s | %s | %s |" % (s, fmt(s_before[s]), fmt(s_after[s])))
    lines.append(u"| GROUNDED / claim | %s | %s |" % (pct(s_before[G], tb[u"claim"]), pct(s_after[G], ia[u"claim"])))
    lines.append(u"| claim が 0 の本(切れた本のうち) | %s | %s |" % (fmt(tb[u"切れた本のうち claim が 0 の本"]), fmt(ia[u"切れた本のうち claim が 0 の本"])))
    lines.append(u"| GROUNDED が 0 の本(切れた本のうち) | %s | %s |" % (fmt(tb[u"切れた本のうち GROUNDED が 0 の本"]), fmt(ia[u"切れた本のうち GROUNDED が 0 の本"])))
    lines.append(u"| VALUE_MISMATCH が 1 以上の本 | %s | %s |" % (fmt(tb[u"VALUE_MISMATCH が 1 以上の本"]), fmt(ia[u"VALUE_MISMATCH が 1 以上の本"])))
    sw = I[u"置き換えた回数の合計(規則 1・2・3)"]
    lines.append(u"| 置き換えた回数(規則 1・2・3 の合計。封に無い診断の欄) | - | %s |" % u" / ".join(fmt(x) for x in sw))
    blocks[u"interim"] = lines
    m = mv[MOVE_KEYS[0]]
    lines = [u"| 写す前 \\ 写した後 | GROUNDED | VALUE_MISMATCH | UNVERIFIABLE | POINTER_NOT_FOUND | 行の計 |", _sep(6)]
    for s in STATES:
        lines.append(u"| %s | %s | %s |" % (s, u" | ".join(fmt(m[s][t]) for t in STATES), fmt(sum(m[s].values()))))
    lines += [u"", u"| 欄 | 行 |", _sep(2),
              u"| 動いた行 | %s |" % fmt(mv[MOVE_KEYS[1]]),
              u"| GROUNDED だった行のうち GROUNDED でなくなった行 | %s |" % fmt(mv[MOVE_KEYS[2]]),
              u"| 写す前にだけ在る行 | %s |" % fmt(mv[MOVE_KEYS[3]]),
              u"| 写した後にだけ在る行 | %s |" % fmt(mv[MOVE_KEYS[4]])]
    blocks[u"moves"] = lines
    ra, rb = tb[u"reason"], ia[u"reason"]
    lines = [u"| state | reason | 写さない | 写した |", _sep(4)]
    for s in (UNV, PNF):
        for k in sorted(set(ra[s]) | set(rb[s])):
            lines.append(u"| %s | %s | %s | %s |" % (s, k, fmt(ra[s].get(k, 0)), fmt(rb[s].get(k, 0))))
    blocks[u"reasons"] = lines
    v = ia[u"VALUE_MISMATCH の内訳"]
    p = v[u"pointer の期"]
    lines = [u"| 欄(写した中間の VALUE_MISMATCH) | 行 |", _sep(2)]
    for k, n in ((u"VALUE_MISMATCH の行", v[u"行"]), (u"導出(formula)", v[u"導出(formula)"]), (u"直接", v[u"直接"]), (u"span に % を含む", v[u"% の数"]),
                 (u"span に % を含まない", v[u"円族の数"]), (u"両期の fact を引く a−b(円)", v[u"両期の fact を引く a−b(円)"]), (u"単位の族が %", v[u"単位の族が %"]),
                 (u"単位の族が円族", v[u"単位の族が円族"]), (u"単位の族が他", v[u"単位の族が他"]), (u"pointer の期 CurrentYear", p[u"CurrentYear"]), (u"pointer の期 Prior1Year", p[u"Prior1Year"])):
        lines.append(u"| %s | %s |" % (k, fmt(n)))
    blocks[u"vm"] = lines
    na, nb = N[u"集計"][u"A(甲 + 乙)"], N[u"集計"][u"B(丙)"]
    lines = [u"| 群 | 本 | VALUE_MISMATCH の行 | 近い行 | 近い行 / VALUE_MISMATCH の行 | N-円 の行 | N-桁 の行 | N-率 の行 | N-円 の本 | N-桁 の本 | N-率 の本 | 近い行を持つ本 |", _sep(12)]
    for name, g in ((u"A(通期。写さない)", na), (u"B(中間。期の名前を写した)", nb)):
        rr, rb_ = g[u"規則ごとの行の数"], g[u"規則ごとの 1 行以上持つ本の数"]
        lines.append(u"| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            name, fmt(g[u"本"]), fmt(g[u"VALUE_MISMATCH の行"]), fmt(g[u"近い行"]), pct(g[u"近い行"], g[u"VALUE_MISMATCH の行"]),
            fmt(rr[u"N-円"]), fmt(rr[u"N-桁"]), fmt(rr[u"N-率"]), fmt(rb_[u"N-円"]), fmt(rb_[u"N-桁"]), fmt(rb_[u"N-率"]), fmt(g[u"近い行を 1 行以上持つ本"])))
    lines.append(u"| A + B | %s | %s | %s | %s | | | | | | | |" % (fmt(na[u"本"] + nb[u"本"]), fmt(na[u"VALUE_MISMATCH の行"] + nb[u"VALUE_MISMATCH の行"]), fmt(N[u"近い行の数(A と B)"]),
                                                          pct(N[u"近い行の数(A と B)"], na[u"VALUE_MISMATCH の行"] + nb[u"VALUE_MISMATCH の行"])))
    blocks[u"near"] = lines
    combo = collections.Counter(u" + ".join(r[3]) for r in N[u"行"])
    lines = [u"| 当たった規則 | 単位の族 | 行 |", _sep(3)]
    fam = dict((u" + ".join(r[3]), r[4]) for r in N[u"行"])
    for k in sorted(combo):
        lines.append(u"| %s | %s | %s |" % (k, fam[k], fmt(combo[k])))
    blocks[u"combos"] = lines
    ta, tb2, tc = Ty[u"型の集計(A)"], Ty[u"型の集計(B)"], Ty[u"型の集計"]
    rule = Ty[u"読む行の規則"]
    lines = [u"| 群 | 近い行 | 読んだ行 | 読んでいない行 |", _sep(4)]
    ra_, rb_ = sum(ta.values()), sum(tb2.values())
    lines.append(u"| A | %s | %s | %s |" % (fmt(na[u"近い行"]), fmt(ra_), fmt(na[u"近い行"] - ra_)))
    lines.append(u"| B | %s | %s | %s |" % (fmt(nb[u"近い行"]), fmt(rb_), fmt(nb[u"近い行"] - rb_)))
    lines.append(u"| A + B | %s | %s | %s |" % (fmt(rule[u"近い行の数"]), fmt(rule[u"読む行の数"]), fmt(rule[u"近い行の数"] - rule[u"読む行の数"])))
    blocks[u"read"] = lines
    tt = Ty[u"型の字"]
    lines = [u"| 型 | 封の字 | A | B | A + B | A の読んだ行のうち | B の読んだ行のうち |", _sep(7)]
    for t in TYPE_KEYS:
        lines.append(u"| (%s) | %s | %s | %s | %s | %s | %s |" % (t, tt[t], fmt(ta[t]), fmt(tb2[t]), fmt(tc[t]), pct(ta[t], ra_), pct(tb2[t], rb_)))
    blocks[u"types"] = lines
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
    t = re.sub(r"\b[A-Z]+-?\d+[A-Z]*\b", u"", t)                      # U-10・P33E・N-円 などの名前
    t = re.sub(u"§[0-9\\-]+", u"", t)
    return t


def prose_number_problems(doc, blocks):
    u"""塊の外の散文の 2 桁以上の数は、記録から作った塊の中の数か、記録から作った数の集合に在る。"""
    allowed = set()
    for lines in blocks.values():
        allowed |= numbers_of(u"\n".join(lines))
    allowed |= DERIVED_NUMBERS(blocks)
    out = []
    for ln, line in enumerate(outside_blocks(doc).splitlines(), 1):
        bad = sorted(numbers_of(prose_clean(line)) - allowed)
        if bad:
            out.append(u"散文の数が記録から作った数の集合に無い: 行 %d %s" % (ln, u",".join(bad)))
        if KANJI_NUM_RE.search(line):
            out.append(u"散文が 3 桁以上の数を漢数字で書いている: 行 %d" % ln)
    return out


def DERIVED_NUMBERS(blocks):
    u"""塊に出ない、記録から作れる数(母集団の本 = A + B など)。"""
    return set()


REQUIRED_PHRASES = (u"封に無い診断", u"AI の席", u"人は読んでいない", u"盲検ではない", u"紙面", u"読んでいない", u"AI の席が候補とした行", u"測っていない")


def doc_problems(c):
    doc = c.doc
    out = []
    names = re.findall(r"<!-- 門:start (\w+) -->", doc)
    if names != list(BLOCK_NAMES) or doc.count(u"<!-- 門:end -->") != len(BLOCK_NAMES):
        out.append(u"文書: 塊の名前・数が 9 つ(%s)の順でない" % u"・".join(BLOCK_NAMES))
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
    if POINTER_RE.search(doc):
        out.append(u"文書: pointer・要素名の形の字がある")
    out += prose_number_problems(doc, want)
    for need in (os.path.basename(SEAL_REL), SEAL_COMMIT_SHORT, os.path.basename(GATE_REL), os.path.basename(SCRIPT_REL)) + tuple(os.path.basename(r) for r in RECORD_RELS) + REQUIRED_PHRASES:
        if need not in doc:
            out.append(u"文書: %s を言っていない" % need)
    return out


# ======================================================================================================
# h. 順序・engine
def order_others():
    return list(RECORD_RELS) + [DOC_REL, GATE_REL]


def order_problems_real(root=REPO):
    return PR.order_problems(root, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, [SCRIPT_REL], order_others())


def engine_problems(root=REPO):
    u"""engine・lib・仕掛け・前の便は封の commit から 0 行。script は足した commit(c1c4a782)から 0 行。"""
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
    (u"interim", interim_problems),
    (u"near", near_problems),
    (u"types", types_problems),
    (u"clean", clean_problems),
    (u"doc", doc_problems),
    (u"seal", lambda c: seal_problems(c.seal)),
    (u"frozen", lambda c: seal_frozen_problems(c.seal)),
])

MUTATIONS = []


def M(label, check, fn):
    MUTATIONS.append((label, check, fn))


def book(c, n):
    return [b for b in c.I[u"本"] if b[u"#"] == n][0]


def first_book(c, pred):
    return [b for b in c.I[u"本"] if pred(b)][0]


def flip(s):
    return (u"0" if s[0] != u"0" else u"1") + s[1:]


def _bump(d, k, n=1):
    d[k] = d[k] + n


def _drop_row(c):
    b = first_book(c, lambda b: len(b[u"行"]) > 3)
    b[u"行"].pop(0)


def _swap_near(c):
    r = c.N[u"行"]
    r[0], r[1] = r[1], r[0]


def _swap_two(lst, i, j):
    lst[i], lst[j] = lst[j], lst[i]


def _doc_digit(c, name):
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


# a. sha
M(u"a1 interim の記録の 1 byte", u"sha", lambda c: c.texts.__setitem__(INTERIM_REL, c.texts[INTERIM_REL] + b" "))
M(u"a2 near の記録の 1 byte", u"sha", lambda c: c.texts.__setitem__(NEAR_REL, c.texts[NEAR_REL][:-2] + b" \n"))
M(u"a3 near_types の記録の 1 byte", u"sha", lambda c: c.texts.__setitem__(TYPES_REL, b"x" + c.texts[TYPES_REL]))
M(u"a4 script の 1 byte", u"sha", lambda c: c.texts.__setitem__(SCRIPT_REL, c.texts[SCRIPT_REL] + b"#"))
# b. 来歴
M(u"b1 interim の「この script の sha256」", u"prov", lambda c: c.I.__setitem__(u"この script の sha256", flip(c.I[u"この script の sha256"])))
M(u"b2 near の「TSS の判定の記録の sha256」", u"prov", lambda c: c.N.__setitem__(u"TSS の判定の記録の sha256", flip(c.N[u"TSS の判定の記録の sha256"])))
M(u"b3 near の「interim の記録の sha256」", u"prov", lambda c: c.N.__setitem__(u"interim の記録の sha256", flip(c.N[u"interim の記録の sha256"])))
M(u"b4 near_types の「near の記録の sha256」", u"prov", lambda c: c.Ty.__setitem__(u"near の記録の sha256", flip(c.Ty[u"near の記録の sha256"])))
M(u"b5 near の「TSS の script の sha256」", u"prov", lambda c: c.N.__setitem__(u"TSS の script の sha256", flip(c.N[u"TSS の script の sha256"])))
M(u"b6 interim の「置く script の sha256」", u"prov", lambda c: c.I.__setitem__(u"置く script の sha256", flip(c.I[u"置く script の sha256"])))
M(u"b7 near の「2026-11-09 の便の script の sha256」", u"prov", lambda c: c.N.__setitem__(u"2026-11-09 の便の script の sha256", flip(c.N[u"2026-11-09 の便の script の sha256"])))
M(u"b8 今の TSS の判定の記録が変わった(実 file 側)", u"prov", lambda c: c.cur.__setitem__("tss_states", flip(c.cur["tss_states"])))
M(u"b9 今の script が変わった(実 file 側)", u"prov", lambda c: c.cur.__setitem__("script", flip(c.cur["script"])))
M(u"b10 engine の指紋が違う", u"prov", lambda c: c.I[u"engine の指紋"].__setitem__(u"adapter_xbrl_py_sha256", flip(c.I[u"engine の指紋"][u"adapter_xbrl_py_sha256"])))
M(u"b11 HEAD の commit が祖先でない 40 桁", u"prov", lambda c: c.N.__setitem__(u"HEAD の commit", u"0" * 40))
M(u"b12 near_types の盲検の欄", u"prov", lambda c: c.Ty.__setitem__(u"盲検", u"盲検"))
M(u"b13 near_types の型を付けた席", u"prov", lambda c: c.Ty.__setitem__(u"型を付けた席", u"人の確認"))
M(u"b14 profile", u"prov", lambda c: c.I.__setitem__(u"profile", u"P32E"))
M(u"b15 step の字", u"prov", lambda c: c.N.__setitem__(u"step", u"TSS"))
M(u"b16 欄が 1 つ増える", u"prov", lambda c: c.Ty.__setitem__(u"余分", 1))
M(u"b17 封の commit の欄", u"prov", lambda c: c.I.__setitem__(u"封の commit", u"e56d6782"))
M(u"b18 置き換えの字", u"prov", lambda c: c.I[u"置き換え(この順。二重引用符から始まる byte 列)"].reverse())
M(u"b19 近い行の限界の字", u"prov", lambda c: c.N[u"限界"].pop())
M(u"b20 材料の前後が違う", u"prov", lambda c: c.N[u"材料"][u"置き場の一覧の前後"].__setitem__(u"変化なし", False))
# c. interim
M(u"c1 集計の GROUNDED を 1 つ増やす", u"interim", lambda c: _bump(c.I[u"集計"][u"4 state"], G))
M(u"c2 集計の claim を 1 つ減らす", u"interim", lambda c: _bump(c.I[u"集計"], u"claim", -1))
M(u"c3 ある行の state を GROUNDED から VALUE_MISMATCH に変える", u"interim", lambda c: [r for b in c.I[u"本"] for r in b[u"行"] if r[2] == G][0].__setitem__(2, VM))
M(u"c4 行を 1 つ消す", u"interim", _drop_row)
M(u"c5 reason の内訳を 1 つ動かす", u"interim", lambda c: _bump(c.I[u"集計"][u"reason"][UNV], u"no_subject"))
M(u"c6 VALUE_MISMATCH の内訳の % の数", u"interim", lambda c: _bump(c.I[u"集計"][u"VALUE_MISMATCH の内訳"], u"% の数"))
M(u"c7 動きの表の 1 欄", u"interim", lambda c: _bump(c.I[u"TSS の B(写さない)との動き"][MOVE_KEYS[0]][PNF], G))
M(u"c8 GROUNDED でなくなった行の欄", u"interim", lambda c: c.I[u"TSS の B(写さない)との動き"].__setitem__(MOVE_KEYS[2], 0))
M(u"c9 写した本の数", u"interim", lambda c: _bump(c.I, u"写した本"))
M(u"c10 名前がぶつかる本の数", u"interim", lambda c: _bump(c.I, u"名前がぶつかる本"))
M(u"c11 置き換えた回数の合計", u"interim", lambda c: c.I[u"置き換えた回数の合計(規則 1・2・3)"].__setitem__(0, c.I[u"置き換えた回数の合計(規則 1・2・3)"][0] + 1))
M(u"c12 本の「写した」", u"interim", lambda c: first_book(c, lambda b: b[u"写した"]).__setitem__(u"写した", False))
M(u"c13 本の置き換えた回数", u"interim", lambda c: first_book(c, lambda b: b[u"写した"])[u"置き換えた回数"].__setitem__(0, -1))
M(u"c14 切り出しが第 1 便と違う本", u"interim", lambda c: first_book(c, lambda b: book_cut(b)).__setitem__(u"切り出し", u"切れない"))
M(u"c15 本の ZIP の sha256", u"interim", lambda c: book(c, 260).__setitem__(u"ZIP の sha256", flip(book(c, 260)[u"ZIP の sha256"])))
M(u"c16 行の位置を変える(第 1 便の行と並びが違う)", u"interim", lambda c: first_book(c, lambda b: b[u"行"])[u"行"][0].__setitem__(1, first_book(c, lambda b: b[u"行"])[u"行"][0][1] + 1))
M(u"c17 本が 1 本足りない", u"interim", lambda c: c.I[u"本"].pop())
M(u"c18 動きの表の行の和(切れない本の行数)", u"interim", lambda c: c.I[u"集計"].__setitem__(u"字数の合計", c.I[u"集計"][u"字数の合計"] + 1))
M(u"c19 本の claim", u"interim", lambda c: _bump(first_book(c, lambda b: b[u"行"]), u"claim"))
M(u"c20 行の state の語", u"interim", lambda c: first_book(c, lambda b: b[u"行"])[u"行"][0].__setitem__(2, u"GROUNDED "))
M(u"c21 集計の欄が 1 つ消える", u"interim", lambda c: c.I[u"集計"].pop(u"claim と raw の並びが対応しなかった本"))
M(u"c22 pointer の期の内訳", u"interim", lambda c: _bump(c.I[u"集計"][u"VALUE_MISMATCH の内訳"][u"pointer の期"], u"Prior1Year"))
M(u"c23 動いた行", u"interim", lambda c: _bump(c.I[u"TSS の B(写さない)との動き"], MOVE_KEYS[1]))
M(u"c24 切れた本のうち GROUNDED が 0 の本", u"interim", lambda c: _bump(c.I[u"集計"], u"切れた本のうち GROUNDED が 0 の本"))
# d. near
M(u"d1 近い行を 1 行消す", u"near", lambda c: c.N[u"行"].pop(5))
M(u"d2 近い行の位置を変える(値が違う行でなくなる)", u"near", lambda c: c.N[u"行"][5].__setitem__(2, c.N[u"行"][5][2] + 1))
M(u"d3 近い行の単位の族", u"near", lambda c: c.N[u"行"][0].__setitem__(4, u"円族"))
M(u"d4 近い行の並び", u"near", _swap_near)
M(u"d5 当たった規則に N-桁を足す(N-率の行へ)", u"near", lambda c: [r for r in c.N[u"行"] if r[3] == [u"N-率"]][0][3].append(u"N-桁"))
M(u"d6 当たった規則を空にする", u"near", lambda c: c.N[u"行"][0].__setitem__(3, []))
M(u"d7 集計の近い行(A)", u"near", lambda c: _bump(c.N[u"集計"][u"A(甲 + 乙)"], u"近い行"))
M(u"d8 集計の規則ごとの行(B・N-率)", u"near", lambda c: _bump(c.N[u"集計"][u"B(丙)"][u"規則ごとの行の数"], u"N-率"))
M(u"d9 集計の規則ごとの本(A・N-円)", u"near", lambda c: _bump(c.N[u"集計"][u"A(甲 + 乙)"][u"規則ごとの 1 行以上持つ本の数"], u"N-円"))
M(u"d10 近い行を持つ本(B)", u"near", lambda c: _bump(c.N[u"集計"][u"B(丙)"], u"近い行を 1 行以上持つ本"))
M(u"d11 VALUE_MISMATCH の行(A)", u"near", lambda c: _bump(c.N[u"集計"][u"A(甲 + 乙)"], u"VALUE_MISMATCH の行"))
M(u"d12 A の違う本", u"near", lambda c: c.N[u"A の state が TSS の記録と同じか"].__setitem__(u"違う本", 1))
M(u"d13 A の行の数", u"near", lambda c: _bump(c.N[u"A の state が TSS の記録と同じか"], u"行", -1))
M(u"d14 B の行の数", u"near", lambda c: _bump(c.N[u"B の state が interim の記録と同じか"], u"行"))
M(u"d15 近い行の数(A と B)", u"near", lambda c: _bump(c.N, u"近い行の数(A と B)"))
M(u"d16 読む行の数", u"near", lambda c: c.N[u"読む行の規則"].__setitem__(u"読む行の数", 199))
M(u"d17 種", u"near", lambda c: c.N[u"読む行の規則"].__setitem__(u"種", 20261114))
M(u"d18 母集団の本", u"near", lambda c: c.N[u"母集団の本"].__setitem__(u"B", 149))
M(u"d19 同じ行を 2 回", u"near", lambda c: c.N[u"行"].insert(1, list(c.N[u"行"][0])))
M(u"d20 interim の B の VALUE_MISMATCH でない行を近い行にする", u"near", lambda c: c.N[u"行"].append([400, 1, 1, [u"N-率"], u"%"]))
M(u"d21 N-率なのに円族", u"near", lambda c: [r for r in c.N[u"行"] if r[3] == [u"N-率"]][0].__setitem__(4, u"円族"))
M(u"d22 recomputed が数でない行(A)", u"near", lambda c: c.N[u"集計"][u"A(甲 + 乙)"].__setitem__(u"うち recomputed が数でない行", 1))
# e. types
M(u"e1 型を 1 つ変える(集計は変えない)", u"types", lambda c: c.Ty[u"行"][0].__setitem__(4, u"あ" if c.Ty[u"行"][0][4] != u"あ" else u"い"))
M(u"e2 型の集計(全体)", u"types", lambda c: _bump(c.Ty[u"型の集計"], u"あ"))
M(u"e3 型の集計(A)", u"types", lambda c: _bump(c.Ty[u"型の集計(A)"], u"い"))
M(u"e4 型の集計(B)", u"types", lambda c: _bump(c.Ty[u"型の集計(B)"], u"え", -1))
M(u"e5 標本の行の文の番号", u"types", lambda c: c.Ty[u"行"][10].__setitem__(2, c.Ty[u"行"][10][2] + 1))
M(u"e6 標本の 2 行の入れ替え", u"types", lambda c: _swap_two(c.Ty[u"行"], 3, 4))
M(u"e7 標本を 1 行消す", u"types", lambda c: c.Ty[u"行"].pop())
M(u"e8 標本が 200 行を超えずに引いた別の行(近い行の最初の 200 行)", u"types", lambda c: [r.__setitem__(slice(1, 4), c.N[u"行"][i][:3]) for i, r in enumerate(c.Ty[u"行"])])
M(u"e9 標本の番号", u"types", lambda c: c.Ty[u"行"][7].__setitem__(0, 9))
M(u"e10 読む行の規則の近い行の数", u"types", lambda c: c.Ty[u"読む行の規則"].__setitem__(u"近い行の数", 219))
M(u"e11 型の字(未知の型)", u"types", lambda c: c.Ty[u"行"][0].__setitem__(4, u"か"))
M(u"e12 型の集計の欄が 1 つ消える", u"types", lambda c: c.Ty[u"型の集計"].pop(u"お"))
M(u"e13 near の行の本の # を変える(標本が別の本を指す)", u"types", lambda c: c.N[u"行"][50].__setitem__(0, c.N[u"行"][50][0] + 1))
# f. clean
M(u"f1 key_leaks に 1 つ", u"clean", lambda c: c.N.__setitem__(u"key_leaks", [u"x"]))
M(u"f2 値の欄 value を持つ", u"clean", lambda c: c.N.__setitem__(u"value", 1))
M(u"f3 近い行に文字の葉", u"clean", lambda c: c.N[u"行"][0].append(u"売上高は1,234百万円となりました"))
M(u"f4 本の欄に会社名らしい字", u"clean", lambda c: c.I[u"本"][0].__setitem__(u"様式の種類", u"㈱x"))
M(u"f5 長い日本語の文", u"clean", lambda c: c.Ty.__setitem__(u"盲検", u"当社の売上高は前期に比べて増加し、営業利益も増加しました。通期の見通しは据え置きます。これは文です"))
M(u"f6 pointer の字", u"clean", lambda c: c.I[u"集計"].__setitem__(u"メモ", u"jppfs_cor:NetSales"))
M(u"f7 証券コードの形の字", u"clean", lambda c: c.I[u"本"][3].__setitem__(u"理由", u"1234"))
M(u"f8 docID の形の字", u"clean", lambda c: c.I[u"本"][3].__setitem__(u"理由", u"S" + u"100ABCD"))
M(u"f9 行の欄に要素名", u"clean", lambda c: c.N[u"行"][0].append(u"xbrl:Element"))
M(u"f10 interim の key_leaks", u"clean", lambda c: c.I.__setitem__(u"key_leaks", [1]))
# g. 文書
for _i, _n in enumerate(BLOCK_NAMES):
    M(u"g%d 塊 %s の数字 1 つ" % (_i + 1, _n), u"doc", (lambda n: (lambda c: _doc_digit(c, n)))(_n))
M(u"g10 塊を 1 つ消す", u"doc", lambda c: setattr(c, "doc", c.doc.replace(u"<!-- 門:start read -->", u"<!-- 門:start readx -->")))
M(u"g11 知らない塊", u"doc", lambda c: setattr(c, "doc", c.doc + u"\n<!-- 門:start zz -->\n|a|\n<!-- 門:end -->\n"))
M(u"g12 散文に記録に無い数", u"doc", lambda c: setattr(c, "doc", c.doc + u"\n散文の数 98765 件。\n"))
M(u"g13 散文の数を 1 つ変える(779 行出た → 778)", u"doc", lambda c: setattr(c, "doc", c.doc.replace(u"779 行出た", u"778 行出た")))
M(u"g13b 散文の数を 1 つ変える(163 行 → 164)", u"doc", lambda c: setattr(c, "doc", c.doc.replace(u"1,898 行のうち 163 行", u"1,898 行のうち 164 行")))
M(u"g13c 散文の数を 1 つ変える(31.5% → 32.5%)", u"doc", lambda c: setattr(c, "doc", c.doc.replace(u"18.0% から 31.5%", u"18.0% から 32.5%")))
M(u"g14 漢数字で逃がす", u"doc", lambda c: setattr(c, "doc", c.doc + u"\n百三十三本。\n"))
M(u"g15 禁止語", u"doc", lambda c: setattr(c, "doc", c.doc + u"\n人の目で見た。\n"))
M(u"g16 docID の形", u"doc", lambda c: setattr(c, "doc", c.doc + u"\nS" + u"100ABCD\n"))
M(u"g17 会社名らしい字", u"doc", lambda c: setattr(c, "doc", c.doc + u"\n株式会社\n"))
M(u"g18 必要な語(封に無い診断)を消す", u"doc", lambda c: setattr(c, "doc", c.doc.replace(u"封に無い診断", u"診断")))
M(u"g19 必要な語(AI の席が候補とした行)を消す", u"doc", lambda c: setattr(c, "doc", c.doc.replace(u"AI の席が候補とした行", u"候補")))
M(u"g20 必要な語(人は読んでいない)を消す", u"doc", lambda c: setattr(c, "doc", c.doc.replace(u"人は読んでいない", u"")))
M(u"g21 必要な語(盲検ではない)を消す", u"doc", lambda c: setattr(c, "doc", c.doc.replace(u"盲検ではない", u"")))
M(u"g22 封の commit を言わない", u"doc", lambda c: setattr(c, "doc", c.doc.replace(SEAL_COMMIT_SHORT, u"")))
M(u"g23 記録の file 名を言わない", u"doc", lambda c: setattr(c, "doc", c.doc.replace(u"near_types_2026-11-14.json", u"")))
M(u"g24 pointer の字", u"doc", lambda c: setattr(c, "doc", c.doc + u"\njppfs_cor:NetSales\n"))
M(u"g25 記録の側を 1 つ変えると塊が違う(U-8 の規則の行)", u"doc", lambda c: _bump(c.N[u"集計"][u"A(甲 + 乙)"][u"規則ごとの行の数"], u"N-円", 20))
M(u"g26 記録の側を 1 つ変えると判定が変わる(U-6 を 61 行に)", u"doc", lambda c: _bump(c.I[u"TSS の B(写さない)との動き"], MOVE_KEYS[2], 43))
M(u"g27 封の予測の字を変える(U-7 の幅)", u"doc", lambda c: setattr(c, "seal", c.seal.replace(u"**A は 60〜260 行**", u"**A は 60〜261 行**")))
M(u"g28 型の字(記録側)を変える", u"doc", lambda c: c.Ty[u"型の字"].__setitem__(u"お", u"読んでも分けられる"))
# h. 封
M(u"h1 封の字を 1 字", u"seal", lambda c: setattr(c, "seal", c.seal.replace(u"**0〜60 行**", u"**0〜61 行**")))
M(u"h2 封の U-9 の幅", u"seal", lambda c: setattr(c, "seal", c.seal.replace(u"B で 0〜8 行", u"B で 0〜9 行")))
M(u"h3 封の U-10 の幅", u"seal", lambda c: setattr(c, "seal", c.seal.replace(u"読んだ行の 10% 以下", u"読んだ行の 11% 以下")))
M(u"h4 封の U-2 の数", u"seal", lambda c: setattr(c, "seal", c.seal.replace(u"2,152", u"2,153")))
M(u"h5 封の U-7 の B の幅", u"seal", lambda c: setattr(c, "seal", c.seal.replace(u"**B は 20〜110 行**", u"**B は 20〜111 行**")))
M(u"h6 封の U-10 が消える", u"seal", lambda c: setattr(c, "seal", c.seal.replace(u"- **U-10**", u"- **U-X**")))
M(u"h7 封が commit のときと 1 字違う", u"frozen", lambda c: setattr(c, "seal", c.seal + u"。"))
M(u"h8 封の文の途中の 1 字", u"frozen", lambda c: setattr(c, "seal", c.seal.replace(u"外れうる形で", u"外れうる型で", 1)))


def check_problems(check, c):
    return guard(CHECKS[check], c)


# ======================================================================================================
# 試験
CTX = []


def ctx_real():
    if not CTX:
        CTX.append(Ctx())
    return CTX[0]


class RealRecordsTest(unittest.TestCase):
    def test_a_1_the_three_records_and_the_script_equal_the_pinned_sha256(self):
        self.assertEqual([], sha_problems(Ctx().texts))

    def test_a_2_the_pinned_sha256_are_the_ones_the_brief_names(self):
        self.assertEqual(["ef443ec1b1331fa05ca314122fe36ad28746816e890f73f27efde55738bb5e7e", "5c2b6ee418495ac184ab51eb424e2e0ef11a04b881bbf719cb31e2c3018e0952",
                          "f59cfc68a6ddf98b9a713efdda52f8bf04d183bc9b415964bb724812810f779f", "7a3db37e77e8013f56668d7202dbddae023778d57fecaf7b8bc5c621a68583b8"], list(SHA_PIN.values()))
        self.assertEqual([INTERIM_REL, NEAR_REL, TYPES_REL, SCRIPT_REL], list(SHA_PIN.keys()))

    def test_b_1_the_provenance_fields_equal_the_real_files(self):
        self.assertEqual([], provenance_problems(Ctx()))

    def test_c_1_the_interim_record_is_whole_and_recounted_from_its_rows(self):
        self.assertEqual([], interim_problems(Ctx()))

    def test_c_2_the_recount_pins_the_real_numbers_literally(self):
        c = Ctx()
        r = recount_interim(c.I[u"本"])
        self.assertEqual((150, 133, 17), (r[u"本"], r[u"切れた"], r[u"切れない"]))
        self.assertEqual([6834, 2152, 779, 1301, 2602], [r[u"claim"]] + [r[u"4 state"][s] for s in STATES])
        self.assertEqual((779, 541, 198, 115, 11), (r[u"VALUE_MISMATCH の内訳"][u"行"], r[u"VALUE_MISMATCH の内訳"][u"% の数"], r[u"VALUE_MISMATCH の内訳"][u"導出(formula)"],
                                                    r[u"VALUE_MISMATCH が 1 以上の本"], r[u"切れた本のうち GROUNDED が 0 の本"]))
        mv = recount_moves(c.I[u"本"], c.T[u"本"])
        self.assertEqual((2170, 18, 0, 0), (mv[MOVE_KEYS[1]], mv[MOVE_KEYS[2]], mv[MOVE_KEYS[3]], mv[MOVE_KEYS[4]]))
        self.assertEqual({G: {G: 1211, VM: 14, UNV: 0, PNF: 4}, VM: {G: 0, VM: 0, UNV: 0, PNF: 0}, UNV: {G: 0, VM: 0, UNV: 855, PNF: 0}, PNF: {G: 941, VM: 765, UNV: 446, PNF: 2598}}, mv[MOVE_KEYS[0]])
        self.assertEqual(0, c.I[u"名前がぶつかる本"])

    def test_c_3_the_a_and_b_row_by_row_checks_cover_every_row_of_the_first_stage_record(self):
        c = Ctx()
        a_rows = sum(len(b[u"行"]) for b in c.T[u"本"] if b[u"#"] <= A_MAX)
        self.assertEqual((250, 17697, 0), (c.N[u"A の state が TSS の記録と同じか"][u"本"], a_rows, c.N[u"A の state が TSS の記録と同じか"][u"違う本"]))
        self.assertEqual(a_rows, c.N[u"A の state が TSS の記録と同じか"][u"行"])
        self.assertEqual((150, 6834, 0), (c.N[u"B の state が interim の記録と同じか"][u"本"], c.N[u"B の state が interim の記録と同じか"][u"行"], c.N[u"B の state が interim の記録と同じか"][u"違う本"]))

    def test_d_1_the_near_record_is_whole_and_recounted_from_its_rows(self):
        self.assertEqual([], near_problems(Ctx()))

    def test_d_2_the_near_numbers_are_pinned_literally(self):
        c = Ctx()
        a, b = c.N[u"集計"][u"A(甲 + 乙)"], c.N[u"集計"][u"B(丙)"]
        self.assertEqual((1898, 163, {u"N-円": 77, u"N-桁": 10, u"N-率": 84}, {u"N-円": 61, u"N-桁": 10, u"N-率": 53}, 98), (a[u"VALUE_MISMATCH の行"], a[u"近い行"], a[u"規則ごとの行の数"],
                                                                                                                          a[u"規則ごとの 1 行以上持つ本の数"], a[u"近い行を 1 行以上持つ本"]))
        self.assertEqual((779, 57, {u"N-円": 25, u"N-桁": 3, u"N-率": 32}, {u"N-円": 23, u"N-桁": 3, u"N-率": 23}, 41), (b[u"VALUE_MISMATCH の行"], b[u"近い行"], b[u"規則ごとの行の数"],
                                                                                                                      b[u"規則ごとの 1 行以上持つ本の数"], b[u"近い行を 1 行以上持つ本"]))
        self.assertEqual((NEAR_N, SAMPLE_N), (c.N[u"近い行の数(A と B)"], c.N[u"読む行の規則"][u"読む行の数"]))

    def test_e_1_the_types_sample_is_drawn_again_from_the_near_rows_and_summed(self):
        self.assertEqual([], types_problems(Ctx()))

    def test_e_2_the_sample_is_a_draw_beyond_200_rows_and_the_types_are_pinned_literally(self):
        c = Ctx()
        self.assertEqual(NEAR_N, len(c.N[u"行"]))
        idx = sorted(random.Random(20261115).sample(range(220), 200))
        self.assertEqual(200, len(set(idx)))
        self.assertEqual([tuple(c.N[u"行"][i][:3]) for i in idx], [tuple(r[1:4]) for r in c.Ty[u"行"]])
        self.assertEqual({u"あ": 3, u"い": 114, u"う": 27, u"え": 52, u"お": 4}, c.Ty[u"型の集計"])
        self.assertEqual({u"あ": 3, u"い": 79, u"う": 27, u"え": 35, u"お": 4}, c.Ty[u"型の集計(A)"])
        self.assertEqual({u"あ": 0, u"い": 35, u"う": 0, u"え": 17, u"お": 0}, c.Ty[u"型の集計(B)"])
        self.assertEqual(20, len(c.N[u"行"]) - len(c.Ty[u"行"]))

    def test_f_1_the_records_hold_no_sentence_no_value_no_company_no_code_no_pointer(self):
        self.assertEqual([], clean_problems(Ctx()))

    def test_g_1_the_nine_blocks_of_the_result_document_equal_the_rebuilt_tables(self):
        self.assertEqual([], doc_problems(Ctx()))

    def test_g_2_the_prediction_judgements_are_pinned_literally(self):
        rows = dict((r[0], r[4]) for r in pred_table(Ctx()))
        self.assertEqual({u"U-1": u"当たり", u"U-2": u"当たり", u"U-3": u"当たり", u"U-4": u"当たり", u"U-5": U5_JUDGE, u"U-6": u"当たり", u"U-7": u"当たり", u"U-8": u"当たり",
                          u"U-9": u"当たり", u"U-10": u"当たり"}, rows)

    def test_g_3_the_seal_prediction_bounds_are_in_the_seal_and_pinned(self):
        self.assertEqual([], seal_problems(Ctx().seal))
        self.assertEqual({u"U-6": (0, 60), u"U-7A": (60, 260), u"U-7B": (20, 110), u"U-9A": (0, 12), u"U-9B": (0, 8)}, dict(BOUNDS))

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
        self.assertEqual((u"fixtures/xbrl/tanshin_self/states_interim_2026-11-14.json", u"fixtures/xbrl/tanshin_self/near_2026-11-14.json",
                          u"fixtures/xbrl/tanshin_self/near_types_2026-11-14.json"), RECORD_RELS)
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, r)) for r in RECORD_RELS + (DOC_REL, GATE_REL, SCRIPT_REL)))

    def test_h_5_engine_lib_and_the_previous_stages_are_untouched_and_the_script_is_unchanged_since_its_commit(self):
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
        before = dict((rel, sha256_rel(rel)) for rel in list(SHA_PIN) + [SEAL_REL, DOC_REL, TSS_STATES_REL])
        c = Ctx()
        c.I[u"集計"][u"claim"] = -1
        c.doc = u"x"
        self.assertEqual(6834, Ctx().I[u"集計"][u"claim"])
        self.assertNotEqual(u"x", Ctx().doc)
        self.assertEqual(before, dict((rel, sha256_rel(rel)) for rel in before))

    def test_m_4_the_mutation_table_covers_every_check_and_every_effect_named_in_the_brief(self):
        checks = set(ch for _l, ch, _f in MUTATIONS)
        self.assertEqual(set(CHECKS), checks)
        self.assertGreaterEqual(len(MUTATIONS), 100)
        labels = u"\n".join(l for l, _c, _f in MUTATIONS)
        for need in (u"標本が 200 行を超えずに", u"near_types の「near の記録の sha256」", u"TSS の判定の記録の sha256", u"封の字を 1 字", u"漢数字", u"同じ行を 2 回", u"型の集計(B)"):
            self.assertIn(need, labels)

    def test_m_5_the_prose_number_check_accepts_a_block_number_and_refuses_another(self):
        c = Ctx()
        blocks = build_blocks(c)
        self.assertEqual([], prose_number_problems(u"本文。A の近い行は 163 行(98 本)。", blocks))
        self.assertNotEqual([], prose_number_problems(u"本文。A の近い行は 164 行。", blocks))
        self.assertEqual([], prose_number_problems(u"本文。封 `20261115` と `a1fd09bf` と 2026-11-14 と P33E と U-10 と §3-1。", blocks))


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
        u"""門は script の集計・規則・標本の関数を呼ばず、自前で数え直す(構造は ast で見る。字面の検査は自分の説明文に当たる)。"""
        import ast
        tree = ast.parse(read(GATE_REL))
        banned = set([u"tally", u"block", u"near_rules", u"interim_block", u"moves", u"pick_sample", u"near_block", u"run_near", u"run_interim", u"digits_close"])
        used = [(n.value.id, n.attr) for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id in (u"MS", u"TSS", u"SG", u"G1")]
        self.assertEqual([], [x for x in used if x[1] in banned])

    def test_n_4_the_seal_gate_helper_is_loaded_without_overwriting_the_names_that_existed(self):
        import types
        marker = types.ModuleType("pswap_for_tss2_result")
        before = sys.modules.get("pswap_for_tss2_result")
        sys.modules["pswap_for_tss2_result"] = marker
        try:
            mod = load_module(SCRIPT_REL, "tanshin_self2_script_reload_probe_for_result_gate")
            self.assertIs(marker, sys.modules["pswap_for_tss2_result"])
            self.assertIs(mod, sys.modules["tanshin_self2_script_reload_probe_for_result_gate"])
        finally:
            if before is None:
                sys.modules.pop("pswap_for_tss2_result", None)
            else:
                sys.modules["pswap_for_tss2_result"] = before
            sys.modules.pop("tanshin_self2_script_reload_probe_for_result_gate", None)


@unittest.skipUnless(os.environ.get("AUDIT_CORE_TSS2_REMEASURE") == "1", u"材料から測り直す試験は AUDIT_CORE_TSS2_REMEASURE=1 のときだけ走る")
class RemeasureTest(unittest.TestCase):
    def _strip(self, text):
        return re.sub(r'^ *"時間\(秒\)": .*$', u"", text, flags=re.M)

    def test_r_1_the_interim_record_is_reproduced_from_the_material_byte_for_byte_except_the_time(self):
        u"""既定の材料(読むだけ)で interim を走らせ、追跡の記録と、時間の欄を除いて byte で同じ。本番の path には書かない。"""
        with tmpdir() as d:
            out = os.path.join(d, "interim_remeasure.json")
            with open(os.devnull, "w") as dn:
                r = subprocess.run([sys.executable, os.path.join(ROOT, SCRIPT_REL), "interim", "--out", out], cwd=ROOT, stdout=dn, stderr=dn)
            self.assertEqual(0, r.returncode)
            with io.open(out, encoding="utf-8") as fh:
                new = fh.read()
        self.assertEqual(self._strip(cached_text(INTERIM_REL)), self._strip(new))

    def test_r_2_the_near_record_is_reproduced_from_the_material_byte_for_byte_except_the_time(self):
        u"""near(A を写さずにもう 1 回・B を写して近い行を拾う。数分かかる)も、追跡の interim の記録を読んで、時間の欄を除いて byte で同じ。"""
        with tmpdir() as d:
            out = os.path.join(d, "near_remeasure.json")
            with open(os.devnull, "w") as dn:
                r = subprocess.run([sys.executable, os.path.join(ROOT, SCRIPT_REL), "near", "--interim", os.path.join(ROOT, INTERIM_REL), "--out", out], cwd=ROOT, stdout=dn, stderr=dn)
            self.assertEqual(0, r.returncode)
            with io.open(out, encoding="utf-8") as fh:
                new = fh.read()
        self.assertEqual(self._strip(cached_text(NEAR_REL)), self._strip(new))


if __name__ == "__main__":
    unittest.main()
