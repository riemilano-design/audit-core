# -*- coding: utf-8 -*-
u"""封 docs/XBRL_AI_TAG_PICK_SEAL_2026-11-22.md(XD0 ― 行の字と標準の表だけでは要素が 1 つに決まらない行で、表の中の位置の字を渡した LLM の席は正しい要素を選べるか。2 席の一致で通すと誤った選びはどれだけ止まるか)の封の門。

**この門は鍵を読まず、1 回も通信しない**(``urllib.request.urlopen`` を差し替えた中でだけ送る body を見る)。材料(書類・タクソノミ)は「材料の確かめ」の試験 1 つだけが読む(無ければ skip)。
ほかは作り物の行・作り物の transport(返事は実物の API の返事の形)で、札(正・誤・0・答えなし)・P1・P2・誤って通した数・やり直し・上限・番号 → 要素の名の戻しを約束の側から試す。

**この門が縛るもの**

1. 封の字: 封の commit(7bb4fa24)・封の file が commit した blob と同じ・指示文(§2-2 の code block と 1 字ずつ)・例(§2-2 の実物の 1 行。作り物の字で組んで字で一致・材料が在れば開発の材料からも)・席・
   max_tokens・temperature を送らない・思考の指定・上限・単価・行の数(326・68・394・試し 5)・8 行に 1 行・並びの向き(主は昇順・副は降順)・前の行 12 個・予測の表(XD0-1〜XD0-11 の境の数)が script の定数と同じ。
2. 便 XG1 の script の sha256(実測して留めた字)が script・門・実物で同じ。便 XG1 の script・engine は封の commit から 0 行。境界の門の import 一覧にこの便の名前を足していない。
3. 順序: 封の commit ⊏ script と この門を足した commit(未 commit は赤)。記録の順序は記録が在るときの結果の門に置く。
4. 指示文を組む(置き換えは 1 回の走査・見出しが無ければ「(なし)」・前の行が無ければ「(なし)」・番号は 1 から・席ごとの並びの向き)・答えの読み方(§2-3)・席の札・P1・P2。
5. 行を選ぶ(類 A は 8 行に 1 行・類 W は全部・書類 → file → 行の順・試しは開発の頭 5 行)・配線の確認(類の数・行の数)が違えば止まる。
6. 作り物の行と作り物の transport で、呼ぶ → 読む → 番号を要素の名に戻す → 札 → P1・P2 → 数える、を本物の関数のまま通す(手計算と照らす)。答えなし・答えのやり直し 1 回・429 の再試行・HTTP 400 で止まる・
   上限で止まる(走らせる前の見積りは試し + 本番・やり直しなし。走っている間の使った額)・返らない呼び出しも見積りの額で数える・中断した呼び出しを見積りの額に数える・試し → 本番(試しの額を引き継ぐ・試しが無ければ本番は止まる)・
   鍵の字が記録にも置き場にも出ない・``--dry-run`` が鍵を読まず通信しない・``--check`` が作り直す。
7. 記録 ``fixtures/xbrl/cd8/ai_tag_pick_2026-11-22.json`` が在るときだけ、形・書かないものが無い・行から数を作り直せる・足し合わせ、を見る(無い間は skip の分岐を明示)。
8. 行頭の名前: この門は ``ENGINE_LATER``・``UNTOUCHED``・``PIN_DEF``・``LATER_ENGINE_COMMITS``・``FROZEN_LATER``・``ENGINE_TRANSITIONS`` を行頭に置かない。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``。script の字を 1 か所替えた版を memory の中に作る。file は書き換えない)。この file は docID の字を持たない。
"""
import ast
import collections
import contextlib
import copy
import glob
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
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)
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


SEAL_REL = "docs/XBRL_AI_TAG_PICK_SEAL_2026-11-22.md"
SEAL_COMMIT_SHORT = "7bb4fa24"                # 封の commit(literal に留める。script の定数と違えば赤)
SCRIPT_REL = "measure/xbrl_ai_tag_pick_2026-11-22.py"
GATE_REL = "tests/measure/test_xbrl_ai_tag_pick_seal.py"
RECORD_REL = "fixtures/xbrl/cd8/ai_tag_pick_2026-11-22.json"
XG1_SCRIPT_REL = "measure/xbrl_tag_narrow_2026-11-21.py"
XG1_SCRIPT_SHA = "24159344be6b2ecf6957339b1356d8049bfe90cab1f4660be5b2f7151a7d6a33"      # 便 XG1 の script の実測(literal)
ORDER_FILES = (SCRIPT_REL, GATE_REL)          # 記録の順序は記録が在るときの結果の門に置く
MS = load_module(SCRIPT_REL, "ai_tag_pick_script_for_seal_gate")
PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_ai_tag_pick_seal")      # 順序・履歴の部品。門としては走らせない
XGT = load_module("tests/measure/test_xbrl_tag_narrow_seal.py", "tag_narrow_gate_helpers_for_ai_tag_pick_seal")   # 作り物の書類・タクソノミ・ラベルの部品。門としては走らせない
od = collections.OrderedDict
quiet = lambda *a: None                                                                                  # noqa: E731
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS")
DOCID_RE = re.compile(r"\bS100[A-Z0-9]{4}\b")
K_WIRE = u"配線の確認(封 §1・§2-1。予測ではない。違えば止まる)"
K_TALLY = u"数えるもの(封 §2-5 の 1〜4)"
K_LINES = u"並べる 2 行(封 §2-5 の 5。類 A)"
K_CALLS = u"呼び出しの記録(封 §2-5 の 6)"
K_TRIAL = u"試しの 10 回(封 §3。本番の数に入れない)"
K_PRED = u"予測の判定に要る数(XD0-1〜XD0-11。当たり・外れは結果の文書で)"
K_SUSPECT = u"先に自分の欠陥を疑う条件の数(封 §5)"
STDLIB_OK = ("__future__", "argparse", "collections", "hashlib", "importlib", "io", "json", "os", "re", "shutil", "sys", "tempfile", "time", "unicodedata", "urllib", "zipfile")
NETWORK_MODULES = ("http", "socket", "ssl", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx", "subprocess")
FAKE_KEY = u"FAKEKEY_zq81x7t3"                 # 試験用の作り物の鍵(本物ではない)。置き場・記録・例外に出ないことを見る
#: 封 §5 の表の境の字(literal)。封の表の行がこの字を持つ
PRED_PHRASES = (
    (u"XD0-1", u"245 行以上 310 行以下"), (u"XD0-2", u"228 行以上"), (u"XD0-3", u"1 行以上、かつ、P2 が通した行の 5% 以下"), (u"XD0-4", u"半分以上"), (u"XD0-5", u"20 行以下"),
    (u"XD0-6", u"34 行以上"), (u"XD0-7", u"70% 以上"), (u"XD0-8", u"10 ポイント以上低い"), (u"XD0-9", u"10 行以上少ない"), (u"XD0-10", u"5 行以下"), (u"XD0-11", u"3 USD 以下"))
EXAMPLE_PREV = [u"営業収益", u"営業費用", u"営業利益", u"営業外収益", u"受取利息", u"その他", u"営業外収益合計", u"営業外費用", u"支払利息", u"自己株式取得費用", u"社葬関連費用", u"支払手数料"]
EXAMPLE_CANDS = [u"OtherCOSExpOA", u"OtherEI", u"OtherEL", u"OtherNOE", u"OtherNOI", u"OtherRevOA", u"OtherSGA"]


def read(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def sha_of(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def sha_or_none(rel):
    return sha_of(rel) if os.path.exists(os.path.join(ROOT, rel)) else None


def guard(fn, *a, **kw):
    u"""fn が例外(``SystemExit`` を含む)を投げたら、その例外の型の名前の字を返す。変異で落ちた検査を赤として数えるため。"""
    try:
        return fn(*a, **kw)
    except BaseException as exc:                # noqa: BLE001
        return [u"例外: %s" % type(exc).__name__]


@contextlib.contextmanager
def patched(obj, **over):
    saved = dict((k, getattr(obj, k)) for k in over)
    for k, v in over.items():
        setattr(obj, k, v)
    try:
        yield
    finally:
        for k, v in saved.items():
            setattr(obj, k, v)


def stops(ms, fn, *a, **kw):
    u"""fn が ``ms.Stop`` を投げれば True。投げなければ False。別の例外は投げ直す。"""
    try:
        fn(*a, **kw)
    except ms.Stop:
        return True
    return False


def load_source(src):
    u"""script の字(``src``)から module を memory の中に作る。file は読み書きしない。``__file__`` は本物の script。"""
    mod = types.ModuleType("ai_tag_pick_mutant")
    mod.__file__ = os.path.join(ROOT, SCRIPT_REL)
    before = dict(sys.modules)
    try:
        exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    finally:
        for k, v in before.items():
            if sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


class Temp(object):
    def __init__(self):
        self.d = tempfile.mkdtemp(prefix="xd0_gate_")

    def p(self, *a):
        return os.path.join(self.d, *a)

    def close(self):
        shutil.rmtree(self.d, ignore_errors=True)


# ---------------------------------------------------------------- 1. 封の字
def seal_text():
    return read(SEAL_REL)


def seal_blocks(seal):
    u"""封 §2-2 の code block 2 つ(指示文・例)。"""
    m = re.search(r"### §2-2.*?```\n(.*?)\n```.*?```\n(.*?)\n```", seal, re.S)
    return (m.group(1), m.group(2)) if m else (None, None)


def seal_values(seal):
    u"""封の字から、席・呼び出しの形・上限・単価・回数を読む(読めなければ None の欄)。"""
    out = {}
    m = re.search(r"主の席 = `([^`]+)`・副の席 = `([^`]+)`", seal)
    out["seats"] = (m.group(1), m.group(2)) if m else None
    m = re.search(r"`max_tokens` (\d+)・`temperature` の欄は送らない[^\n]*?思考の指定は主の席 `(\{[^`]*\})`・副の席 `(\{[^`]*\})`", seal)
    out["shape"] = (int(m.group(1)), json.loads(m.group(2)), json.loads(m.group(3))) if m else None
    m = re.search(r"\*\*上限\*\*: (\d+) USD", seal)
    out["cap"] = int(m.group(1)) if m else None
    m = re.search(r"単価は入力 (\d+) USD・出力 (\d+) USD / 100 万 token", seal)
    out["price"] = (int(m.group(1)), int(m.group(2))) if m else None
    m = re.search(r"本番 (\d+) 行 × 2 席 = (\d+) 回・試し (\d+) 行 × 2 席 = (\d+) 回", seal)
    out["calls"] = tuple(int(x) for x in m.groups()) if m else None
    m = re.search(r"2603 行のうち (\d+) 行", seal)
    out["a_rows"] = int(m.group(1)) if m else None
    m = re.search(r"類 W の行: 本番の 62 本の全部\((\d+) 行\)", seal)
    out["w_rows"] = int(m.group(1)) if m else None
    m = re.search(r"合わせて (\d+) 行", seal)
    out["rows"] = int(m.group(1)) if m else None
    m = re.search(r"頭の (\d+) 行", seal)
    out["trial_rows"] = int(m.group(1)) if m else None
    m = re.search(r"番号が (\d+) で割り切れる", seal)
    out["step"] = int(m.group(1)) if m else None
    m = re.search(r"後ろから (\d+) 個", seal)
    out["prev_n"] = int(m.group(1)) if m else None
    m = re.search(r"開発で U (\d+)・A (\d+)・N (\d+)・W (\d+)、本番で U (\d+)・A (\d+)・N (\d+)・W (\d+)", seal)
    out["wire"] = tuple(int(x) for x in m.groups()) if m else None
    return out


def seal_problems(ms=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    out = []
    if ms.SEAL_COMMIT != SEAL_COMMIT_SHORT or ms.SEAL_REL != SEAL_REL or ms.SCRIPT_REL != SCRIPT_REL or ms.RECORD_REL != RECORD_REL:
        out.append(u"script の封の commit・path・記録の path が門と違う")
    if ms.XG1_SCRIPT_REL != XG1_SCRIPT_REL or ms.XG1_SCRIPT_SHA256 != XG1_SCRIPT_SHA:
        out.append(u"script の便 XG1 の script の path・sha256 の留めが門と違う")
    blk, example = seal_blocks(seal)
    if blk is None or ms.PROMPT_TEMPLATE != blk:
        out.append(u"script の指示文が封 §2-2 の code block と 1 字ずつ同じでない")
    if tuple(ms.PLACEHOLDERS) != (u"{HEADING}", u"{PREV}", u"{ROW}", u"{CANDS}") or any(p not in (blk or u"") for p in ms.PLACEHOLDERS):
        out.append(u"置き換える 4 つの所が封の指示文と違う")
    v = seal_values(seal)
    if v["seats"] != tuple(ms.SEATS) or tuple(ms.SEAT_TAG.items()) != (("claude-sonnet-5-5", u"主"), ("claude-haiku-5-5", u"副")) or v["seats"] != ("claude-sonnet-5-5", "claude-haiku-5-5"):
        out.append(u"席の名(主・副)が封と違う")
    if v["shape"] is None or (ms.MAX_TOKENS, ms.THINKING.get(ms.SEATS[0]), ms.THINKING.get(ms.SEATS[1])) != v["shape"] or ms.TEMPERATURE is not None:
        out.append(u"max_tokens・temperature(送らない)・思考の指定が封と違う")
    if v["cap"] is None or ms.COST_CAP_USD != float(v["cap"]):
        out.append(u"上限が封と違う")
    if v["price"] is None or (ms.PRICE_IN, ms.PRICE_OUT) != tuple(float(x) for x in v["price"]):
        out.append(u"単価が封と違う")
    if v["calls"] != (394, 788, 5, 10) or len(ms.SEATS) != 2 or ms.EXPECT_ROWS != 394:
        out.append(u"回数(394 行・788 回・試し 5 行・10 回)が封と違う")
    if (v["a_rows"], v["w_rows"], v["rows"], v["trial_rows"]) != (326, 68, 394, 5) or (ms.EXPECT_A, ms.EXPECT_W, ms.EXPECT_ROWS, ms.TRIAL_ROWS) != (326, 68, 394, 5):
        out.append(u"行の数(326・68・394・試し 5)が封と違う")
    if v["step"] != 8 or ms.PICK_STEP != 8 or v["prev_n"] != 12 or ms.PREV_N != 12:
        out.append(u"8 行に 1 行・前の行 12 個が封と違う")
    want_wire = tuple(ms.EXPECT_WIRE["dev"].values()) + tuple(ms.EXPECT_WIRE["prod"].values())
    if v["wire"] != (1033, 208, 18, 2, 12444, 2603, 387, 68) or want_wire != v["wire"] or tuple(ms.EXPECT_WIRE["dev"].keys()) != (u"U", u"A", u"N", u"W"):
        out.append(u"配線の確認の類の数が封と違う")
    if (ms.SEAT_REVERSE.get(ms.SEATS[0]), ms.SEAT_REVERSE.get(ms.SEATS[1])) != (False, True) or u"主の席には昇順・副の席には降順" not in seal:
        out.append(u"候補の並びの向き(主は昇順・副は降順)が封と違う")
    if ms.MAX_ANSWER_ATTEMPTS != 2 or tuple(ms.STOP_HTTP) != (400, 401, 403):
        out.append(u"答えのやり直し 1 回・HTTP で止める一覧が決めと違う")
    if (ms.GEN.API_VERSION, tuple(ms.GEN.RETRY_WAITS), ms.GEN.KEY_ENV) != ("2023-06-01", (2, 8), "ANTHROPIC_API_KEY") or ms.KEY_ENV != "ANTHROPIC_API_KEY":
        out.append(u"API の版・やり直しの待ち・鍵の環境変数の名が封(aiforms_gen と同じ字)と違う")
    if (ms.NO_HEADING, ms.NO_PREV, ms.NO_ANSWER, ms.L_OK, ms.L_BAD, ms.L_ZERO) != (u"(なし)", u"(なし)", u"答えなし", u"正", u"誤", u"0"):
        out.append(u"見出し・前の行が無いときの字か札の字が封と違う")
    if tuple(ms.BANDS.keys()) != (u"候補 2", u"候補 3〜6", u"候補 7 以上") or tuple(ms.KIND_NAME.values()) != (u"貸借", u"損益", u"キャッシュフロー", u"株主資本等変動", u"種類なし") or tuple(ms.KINDS_WITH) != (u"貸借", u"損益", u"キャッシュフロー"):
        out.append(u"帯・計算書の種類の分け方が決めと違う")
    if (ms.K_WIRE, ms.K_TALLY, ms.K_LINES, ms.K_CALLS, ms.K_TRIAL, ms.K_PRED, ms.K_SUSPECT) != (K_WIRE, K_TALLY, K_LINES, K_CALLS, K_TRIAL, K_PRED, K_SUSPECT):
        out.append(u"記録の欄の名が門と違う")
    for phrase in (u"本番の 62 本の類 A の行を上の順に並べ", u"返った text(type が text の block をつないだ字)を NFKC にかけ", u"答えを司令塔が手で直さない", u"通す規則 P2(2 席の一致)",
                   u"主の席が 1 以上の番号を答えた行を通す", u"誤って通した数", u"上限**: 5 USD", u"見積りの額で", u"`--dry-run` は鍵を読まず通信せず", u"試しの答えは本番の数に入れない",
                   u"指示文(§2-2)は直さない", u"2 つの類を足した率は書かない", u"同じ 67 本の有報", u"便 XG1 の script(`measure/xbrl_tag_narrow_2026-11-21.py`)を module として呼ぶ"):
        if phrase not in seal:
            out.append(u"封に要点の字が無い: %s" % phrase[:20])
    return out


def pred_problems(ms=None, seal=None):
    u"""封 §5 の表(XD0-1〜XD0-11)の境の字が門の literal と同じ。script の判定に要る数の欄が 11 個(XD0-1〜XD0-11)並ぶ。"""
    seal = seal if seal is not None else seal_text()
    out = []
    rows = dict((m.group(1), m.group(0)) for m in re.finditer(r"^\| (XD0-\d+)[^|]*\|[^\n]*$", seal, re.M))
    if sorted(rows) != sorted(k for k, _p in PRED_PHRASES):
        out.append(u"封の予測の表の行が XD0-1〜XD0-11 でない")
    for k, ph in PRED_PHRASES:
        if k not in rows or ph not in rows[k]:
            out.append(u"封の予測の表の境の字が門の字と違う: %s" % k)
    ms = ms or MS
    w = fake_world(ms)
    rec = full_run(ms, w)
    keys = list(rec[ms.K_PRED].keys())
    if len(keys) != 11 or [k.split(u" ")[0] for k in keys] != [u"XD0-%d" % i for i in range(1, 12)]:
        out.append(u"記録の判定に要る数の欄が XD0-1〜XD0-11 の順に並ばない")
    return out


def seal_history_problems(root=REPO):
    u"""封の file の履歴は 1 commit(7bb4fa24)で、今の file は commit した blob と 1 字も変わらない。"""
    c = PR.added_commits(root, PREFIX + SEAL_REL)
    if len(c) != 1 or not c[0].startswith(SEAL_COMMIT_SHORT):
        return [u"封の commit が履歴に 1 つで %s に決まらない" % SEAL_COMMIT_SHORT]
    rc, log = PR.git_in(root, "log", "--format=%H", "--", PREFIX + SEAL_REL)
    hs = [x for x in log.split() if x]
    if len(hs) != 1 or not hs[0].startswith(SEAL_COMMIT_SHORT):
        return [u"封の file の履歴が封 %s の 1 commit でない" % SEAL_COMMIT_SHORT]
    blob = subprocess.run(["git", "-C", root, "show", "%s:%s" % (hs[0], PREFIX + SEAL_REL)], stdout=subprocess.PIPE).stdout.decode("utf-8")
    if blob != seal_text():
        return [u"今の封が封の commit の blob と違う"]
    return []


# ---------------------------------------------------------------- 2. 前の便・engine・順序
def xg1_pin_problems(ms=None, root=REPO):
    u"""便 XG1 の script の sha256 が script の留め・門の literal・実物で同じ。便 XG1 の script・engine は封の commit から 0 行。script は便 XG1 の関数を写さない。"""
    ms = ms or MS
    out = []
    if sha_of(XG1_SCRIPT_REL) != XG1_SCRIPT_SHA or ms.XG1_SCRIPT_SHA256 != XG1_SCRIPT_SHA:
        out.append(u"便 XG1 の script の sha256 が留めた字と違う")
    rc, txt = PR.git_in(root, "diff", "--name-only", SEAL_COMMIT_SHORT, "--", PREFIX + XG1_SCRIPT_REL, PREFIX + "measure/xbrl_tag_wall_2026-11-21.py", PREFIX + "adapters", PREFIX + "core")
    if rc != 0:
        out.append(u"git diff が失敗した")
    out.extend(u"便 XG1・XG0 の script か engine が封の後に変わっている: %s" % ln for ln in txt.splitlines() if ln.strip())
    return out


def no_copy_problems(src=None):
    u"""便 XG1 の関数(行の切り出し・見出し・種類・業種・段・類の分け方)を script が自前で定義しない(module として呼ぶ)。"""
    src = src if src is not None else read(SCRIPT_REL)
    tree = ast.parse(src)
    names = set(n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    banned = set([u"file_rows", u"kind_of", u"industry_of", u"dei_values", u"narrow", u"stage1", u"stage2", u"stage3", u"classify_stage", u"classify", u"row_status", u"load_tax", u"label_tables", u"select_docs", u"doc_texts"])
    out = [u"便 XG1・XG0 の関数を写している: %s" % n for n in sorted(names & banned)]
    used = set(x.attr for x in ast.walk(tree) if isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name) and x.value.id in ("N", "W"))
    for need in (u"file_rows", u"kind_of", u"industry_of", u"dei_values", u"narrow", u"classify_stage", u"doc_texts", u"load_tax", u"select_docs", u"row_status", u"label_tables"):
        if need not in used:
            out.append(u"便 XG1・XG0 の関数を呼んでいない: %s" % need)
    return out


def order_of(root=REPO, seal_short=SEAL_COMMIT_SHORT, others=None):
    u"""封 ⊏ script・この門(足した commit が封の後)。未 commit は赤。"""
    others = list(ORDER_FILES) if others is None else others
    return list(PR.order_problems(root, PREFIX, SEAL_REL, seal_short, [], others))


def engine_zero_problems(root=REPO):
    rc, txt = PR.git_in(root, "diff", "--name-only", SEAL_COMMIT_SHORT, "--", PREFIX + "adapters", PREFIX + "core")
    return [u"engine が封の後に変わっている: %s" % ln for ln in txt.splitlines() if ln.strip()]


# ---------------------------------------------------------------- 3. 指示文・答えの読み方・札(純粋な関数)
def prompt_problems(ms=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    out = []
    blk, example = seal_blocks(seal)
    got = ms.build_prompt(u"損益計算書", EXAMPLE_PREV, u"その他", EXAMPLE_CANDS)
    want = blk.replace(u"{HEADING}", u"損益計算書").replace(u"{PREV}", u" / ".join(EXAMPLE_PREV)).replace(u"{ROW}", u"その他").replace(u"{CANDS}", u"\n".join(u"%d. %s" % (i + 1, c) for i, c in enumerate(EXAMPLE_CANDS)))
    if got != want:
        out.append(u"指示文の組み立てが封の code block の置き換えと違う")
    if example is None or got.split(u"\n\n")[1] != example:
        out.append(u"封 §2-2 の例(実物の 1 行)を作り物の字で組んだ字が封の例と 1 字ずつ同じでない")
    lines = got.split(u"\n")
    if u"表の見出し: 損益計算書" not in lines or u"この行: その他" not in lines or u"1. OtherCOSExpOA" not in lines or u"7. OtherSGA" not in lines or u"候補:" not in lines:
        out.append(u"見出し・この行・候補の行が封の形でない")
    if u"表の見出し: (なし)" not in ms.build_prompt(None, EXAMPLE_PREV, u"X", [u"a"]).split(u"\n"):
        out.append(u"見出しが無いとき「(なし)」にならない")
    if u"この行より前の行(上から順): (なし)" not in ms.build_prompt(u"h", [], u"X", [u"a"]).split(u"\n"):
        out.append(u"前の行が無いとき「(なし)」にならない")
    if u"表の見出し: " not in ms.build_prompt(u"", [u"p"], u"X", [u"a"]).split(u"\n"):
        out.append(u"見出しが空の字のとき「(なし)」にしてしまう(無いのは None のときだけ)")
    tricky = ms.build_prompt(u"見出し{ROW}{CANDS}", [u"前{HEADING}", u"{PREV}"], u"行{CANDS}{ROW}", [u"c{HEADING}", u"d"])
    ls = tricky.split(u"\n")
    if u"表の見出し: 見出し{ROW}{CANDS}" not in ls or u"この行より前の行(上から順): 前{HEADING} / {PREV}" not in ls or u"この行: 行{CANDS}{ROW}" not in ls or u"1. c{HEADING}" not in ls:
        out.append(u"置き換えが 1 回の走査でない(渡した字の中の {…} が再び置き換わる)")
    asc = ms.make_item(od([("doc", 1), ("cls", "A"), ("kind", None), ("heading", u"h"), ("prev", []), ("T", u"t"), ("E", u"Bbb"), ("cands", [u"Aaa", u"Bbb", u"Ccc"])]), "prod")
    if asc["cands"][ms.SEATS[0]] != [u"Aaa", u"Bbb", u"Ccc"] or asc["cands"][ms.SEATS[1]] != [u"Ccc", u"Bbb", u"Aaa"]:
        out.append(u"候補の並びが主の席は昇順・副の席は降順でない")
    if u"1. Aaa\n2. Bbb\n3. Ccc" not in asc["prompt"][ms.SEATS[0]] or u"1. Ccc\n2. Bbb\n3. Aaa" not in asc["prompt"][ms.SEATS[1]]:
        out.append(u"席ごとの指示文の番号の振り方が違う")
    if asc["sha"][ms.SEATS[0]] == asc["sha"][ms.SEATS[1]] or asc["sha"][ms.SEATS[0]] != ms.sha256_text(asc["prompt"][ms.SEATS[0]]):
        out.append(u"席ごとの指示文の sha256 が指示文のものでない")
    sh = ms.make_item(od([("doc", 1), ("cls", "A"), ("kind", None), ("heading", u"h"), ("prev", []), ("T", u"t"), ("E", u"x"), ("cands", [u"b", u"A", u"a", u"B"])]), "prod")
    if sh["cands"][ms.SEATS[0]] != [u"A", u"B", u"a", u"b"] or sh["cands"][ms.SEATS[1]] != [u"b", u"a", u"B", u"A"]:
        out.append(u"昇順・降順が字の順(コードポイントの順)でない")
    return out


READ_CASES = (
    (u"答え: 3", "end_turn", 7, 3),
    (u"答え: 0", "end_turn", 7, 0),
    (u"答え:3", "end_turn", 7, 3),
    (u"答え : 3", "end_turn", 7, 3),
    (u"答え：３", "end_turn", 7, 3),                         # 全角の : と数字は NFKC で読める
    (u"答え: 7", "end_turn", 7, 7),                          # 候補の数ちょうど
    (u"答え: 8", "end_turn", 7, None),                       # 範囲の外
    (u"答え: 03", "end_turn", 7, 3),
    (u"答え: 3.5", "end_turn", 7, 3),
    (u"答え: 3\n説明です", "end_turn", 7, 3),
    (u"前置き 答え: 2", "end_turn", 7, 2),
    (u"答え: 2 / 答え: 5", "end_turn", 7, 2),                # 答えが 2 つ以上在れば最初
    (u"答え: x 答え: 5", "end_turn", 7, None),               # 最初の 答え の後ろが読めなければ読めない
    (u"答えは 3", "end_turn", 7, None),
    (u"答え: -1", "end_turn", 7, None),
    (u"答え 3", "end_turn", 7, None),                         # : が無ければ読めない
    (u"答え３", "end_turn", 7, None),
    (u"答え: 3", "max_tokens", 7, None),
    (u"答え: 3", None, 7, None),
    (u"", "end_turn", 7, None),
    (None, "end_turn", 7, None),
    (u"3", "end_turn", 7, None),
    (u"番号は 3", "end_turn", 7, None),
    (u"答え: ", "end_turn", 7, None),
)


def read_problems(ms=None):
    ms = ms or MS
    out = []
    for text, sr, n, want in READ_CASES:
        got = ms.read_answer(text, sr, n)
        if got != want:
            out.append(u"答えの読みが違う: %r (%s・候補 %d) → %r" % (text, sr, n, got))
    return out


def label_problems(ms=None):
    u"""席の札・要素の名への戻し・2 席の一致(席ごとに並びが違っても要素の名で比べる)。"""
    ms = ms or MS
    out = []
    it = ms.make_item(od([("doc", 1), ("cls", "A"), ("kind", None), ("heading", u"h"), ("prev", []), ("T", u"t"), ("E", u"Bbb"), ("cands", [u"Aaa", u"Bbb", u"Ccc", u"Ddd"])]), "prod")
    m, s = ms.SEATS
    if [ms.pick_of(it, m, k) for k in (1, 2, 3, 4)] != [u"Aaa", u"Bbb", u"Ccc", u"Ddd"] or [ms.pick_of(it, s, k) for k in (1, 2, 3, 4)] != [u"Ddd", u"Ccc", u"Bbb", u"Aaa"]:
        out.append(u"番号 → 要素の名の戻しが席に渡した並びと違う")
    if ms.pick_of(it, m, 0) is not None or ms.pick_of(it, m, None) is not None:
        out.append(u"0・答えなしを要素に戻す")
    if [ms.seat_label(it, m, k) for k in (2, 1, 0, None)] != [u"正", u"誤", u"0", u"答えなし"] or [ms.seat_label(it, s, k) for k in (3, 4, 0, None)] != [u"正", u"誤", u"0", u"答えなし"]:
        out.append(u"席の札(正・誤・0・答えなし。副の席は降順の番号で戻す)が違う")
    w = ms.make_item(od([("doc", 1), ("cls", "W"), ("kind", None), ("heading", None), ("prev", []), ("T", u"t"), ("E", u"Zzz"), ("cands", [u"Aaa", u"Bbb"])]), "prod")
    if ms.seat_label(w, m, 1) != u"誤" or ms.seat_label(w, s, 1) != u"誤":
        out.append(u"類 W の行に「正」が出る(候補の中に書類の要素が無い)")
    if not ms.same_pick(it, 2, 3) or ms.same_pick(it, 2, 2) or ms.same_pick(it, 0, 3) or ms.same_pick(it, 2, 0) or ms.same_pick(it, None, 3) or ms.same_pick(it, 2, None):
        out.append(u"2 席の一致が要素の名で比べられていない(番号の一致でない・0・答えなしは一致でない)")
    if ms.same_pick(it, 0, 0):
        out.append(u"答えの 0 同士を 2 席の一致に数える")
    bands = dict((k, fn) for k, fn in ms.BANDS.items())
    for n in range(1, 40):
        want = u"候補 2" if n == 2 else (u"候補 3〜6" if 3 <= n <= 6 else (u"候補 7 以上" if n >= 7 else None))
        got = [k for k, fn in bands.items() if fn(n)]
        if got != ([want] if want else []):
            out.append(u"候補の数の帯が 2・3〜6・7 以上でない(候補 %d → %s)" % (n, got))
            break
    if abs(ms.estimate_usd(1000) - 0.0075) > 1e-12 or abs(ms.cost_usd(100, 20) - 0.001) > 1e-12 or ms.cost_usd(None, None) != 0:
        out.append(u"見積り・費用の計算が封の単価(入力 5・出力 25・max_tokens 100)と違う")
    return out


# ---------------------------------------------------------------- 4. 作り物の世界(材料は読まない)
TN = lambda i: u"売上その他行甲%d" % i                                                                       # noqa: E731  作り物の行の字(5 字以上。記録に入れば部分一致で止まる)
TT = lambda i: u"試験項目試行%d" % i                                                                          # noqa: E731


def fake_world(ms):
    u"""作り物の行。本番 7 行(類 A 4・類 W 3)・試し 2 行。各席が選ぶ要素(か「0」か読めない答え)を行ごとに決める。手計算の数は ``expect_*``。"""
    names = lambda *xs: [u"Elem" + x for x in xs]                                      # noqa: E731
    mk = lambda doc, cls, elems, E, kind, T: ms.make_item(od([("doc", doc), ("cls", cls), ("kind", kind), ("heading", u"表見出し項目" + T[-1]), ("prev", [u"前行項目" + T[-1]]), ("T", T), ("E", E),
                                                           ("cands", names(*elems))]), "prod")
    prod = [
        mk(1, "A", "ABC", u"ElemB", "pl", TN(0)),                      # 主 正・副 正(同じ要素)
        mk(1, "A", "ABCD", u"ElemC", None, TN(1)),                     # 主 誤・副 誤(同じ要素 ElemA)→ P2 が誤って通す
        mk(2, "A", "ABCDEFG", u"ElemA", "bs", TN(2)),                  # 主 正(ElemA)・副 誤(ElemC)。候補 7・昇順の頭が書類の要素
        mk(2, "A", "HI", u"ElemI", "cf", TN(3)),                       # 主 0・副 誤(ElemH)
        mk(3, "W", "JK", u"ElemZ", "bs", TN(4)),                       # 主 誤・副 誤(同じ要素 ElemJ)→ P2 が通す(類 W は全部誤)
        mk(3, "W", "LMN", u"ElemZ", None, TN(5)),                      # 主 読めない(答えなし)・副 0
        mk(4, "W", "PQ", u"ElemZ", "pl", TN(6))]                       # 主 0・副 誤(ElemP)
    trial = [ms.make_item(od([("doc", 1), ("cls", "A"), ("kind", None), ("heading", u"見出し試"), ("prev", []), ("T", TT(i)), ("E", u"ElemB"), ("cands", names(*"ABC"))]), "trial") for i in range(2)]
    answers = {TN(0): (u"ElemB", u"ElemB"), TN(1): (u"ElemA", u"ElemA"), TN(2): (u"ElemA", u"ElemC"), TN(3): (u"0", u"ElemH"), TN(4): (u"ElemJ", u"ElemJ"),
               TN(5): (None, u"0"), TN(6): (u"0", u"ElemP"), TT(0): (u"ElemB", u"ElemB"), TT(1): (u"0", u"ElemC")}
    base = [set(), set(), [], set(), set(), set()]
    col = od([("trial", trial), ("prod", prod), ("wire", od([(u"送る行(本番)", 7), (u"試しの行", 2)])), ("secret", ms.secret_of(base, trial + prod)), ("material", od([(u"書類の本数", 0)]))])
    return types.SimpleNamespace(ms=ms, col=col, answers=answers, prod=prod, trial=trial)


def fake_body(text, tin=100, tout=20, stop="end_turn", blocks=("thinking", "text")):
    u"""作り物の返事(実物の API の返事の形: content の block・usage・stop_reason)。入力 token は主の席 100・副の席 50(``transport`` が替える)。"""
    content = [({"type": "thinking", "thinking": u"…"} if b == "thinking" else {"type": "text", "text": text}) for b in blocks]
    return json.dumps({"content": content, "usage": {"input_tokens": tin, "output_tokens": tout}, "stop_reason": stop}).encode("utf-8")


def make_transport(w, log=None, seq=None, blocks=("thinking", "text")):
    u"""作り物の transport。指示文の「この行:」の字で行を決め、席(model)で選ぶ要素を変える。選ぶ要素の番号は、その席に渡した指示文の候補の行から探す(席ごとに並びが違う)。"""
    n_calls = []
    ms = w.ms

    def t(prompt, model, key):
        n_calls.append((model, prompt))
        if log is not None:
            log.append((model, prompt, key))
        if seq is not None:
            r = seq(len(n_calls), model, prompt)
            if r is not None:
                return r
        row = re.search(u"^この行: (.+)$", prompt, re.M).group(1)
        target = w.answers[row][0 if model == ms.SEATS[0] else 1]
        if target is None:
            text = u"読めません"
        elif target == u"0":
            text = u"答え: 0"
        else:
            num = [int(m.group(1)) for m in re.finditer(r"^(\d+)\. (.+)$", prompt, re.M) if m.group(2) == target]
            text = u"答え: %d" % num[0]
        return 200, fake_body(text, tin=100 if model == ms.SEATS[0] else 50, blocks=blocks)
    t.n = n_calls
    return t


def run_world(w, tmp, trial=False, resume=False, transport=None, sleep=quiet, say=quiet, tag=u"w", cap=None, work=None, key=FAKE_KEY, col=None):
    u"""``run`` を作り物の行・作り物の transport・使い捨ての置き場と出力先で本物のまま走らせる。"""
    ms = w.ms
    transport = transport or make_transport(w)
    kw = {} if cap is None else {"cap": cap}
    return ms.run(root=ROOT, trial=trial, resume=resume, work=work or tmp.p(tag, u"work"), out=tmp.p(tag, u"rec.json"), key=key, transport=transport, sleep=sleep,
                  collected=copy.deepcopy(col if col is not None else w.col), fp=od(), say=say, **kw)


def full_run(ms, w, tag=u"w"):
    u"""試し → 本番(作り物)。記録を返す。"""
    tmp = Temp()
    try:
        run_world(w, tmp, trial=True, tag=tag)
        return run_world(w, tmp, tag=tag)
    finally:
        tmp.close()


# 手計算(行ごとの先頭 8 欄 + 席ごとの呼び出しの数)
EXPECT_ROWS_CELLS = [
    [1, u"A", 3, u"損益", u"正", u"正", True, False, 1, 1],
    [1, u"A", 4, u"種類なし", u"誤", u"誤", True, False, 1, 1],
    [2, u"A", 7, u"貸借", u"正", u"誤", False, True, 1, 1],
    [2, u"A", 2, u"キャッシュフロー", u"0", u"誤", False, False, 1, 1],
    [3, u"W", 2, u"貸借", u"誤", u"誤", True, False, 1, 1],
    [3, u"W", 3, u"種類なし", u"答えなし", u"0", False, False, 2, 1],
    [4, u"W", 2, u"損益", u"0", u"誤", False, False, 1, 1]]
USD_PROD = 0.01325                             # 主の席 8 回 × 0.001 + 副の席 7 回 × 0.00075(主の席の行甲5 は読めない 1 回目の後にやり直し 1 回)
USD_TRIAL = 0.0035                             # 主の席 2 回 × 0.001 + 副の席 2 回 × 0.00075
USD_ALL = 0.01675


def items_problems(ms=None):
    u"""行を選ぶ(類 A は 8 行に 1 行・類 W は全部・書類 → file → 行の順・試しは開発の類 A の頭)・配線の確認が止める。"""
    ms = ms or MS
    out = []

    def row(group, doc, fi, ri, cls, ncand=3):
        return od([("group", group), ("doc", doc), ("ord", (doc, fi, ri)), ("cls", cls), ("kind", None), ("heading", u"h"), ("prev", [u"p"]), ("T", u"T%d_%d_%d" % (doc, fi, ri)), ("E", u"ElemA" if cls == "A" else u"ElemZ"),
                   ("cands", [u"Elem%s" % c for c in u"ABCDEFG"[:ncand]])])
    rows = []
    # 本番: 書類 6 に類 A 10 行(file 0・1)・書類 7 に類 A 8 行 + 類 W 2 行。わざと順を崩して渡す
    for ri in range(6):
        rows.append(row("prod", 6, 0, ri, "A"))
    for ri in range(4):
        rows.append(row("prod", 6, 1, ri, "A"))
    for ri in range(8):
        rows.append(row("prod", 7, 0, ri * 2, "A"))
    rows.append(row("prod", 7, 0, 1, "W", 2))
    rows.append(row("prod", 6, 1, 9, "W", 2))
    for ri in range(7):
        rows.append(row("dev", 1, 0, ri, "A"))
    rows.append(row("dev", 1, 0, 99, "W", 2))
    rows.reverse()
    counts = od([("dev", od([("U", 5), ("A", 7), ("N", 1), ("W", 1)])), ("prod", od([("U", 9), ("A", 18), ("N", 2), ("W", 2)]))])
    expect = od([("dev", od([("U", 5), ("A", 7), ("N", 1), ("W", 1)])), ("prod", od([("U", 9), ("A", 18), ("N", 2), ("W", 2)]))])
    t, p, wire = ms.select_items(rows, counts, expect, (3, 2, 5, 3), trial_rows=3)
    # 本番の類 A を (書類・file・行)の順に並べた番号 0・8・16: 書類 6 file 0 の 0 行目・書類 6 file 1 の 2 行目(10 行のうち 8 番目)・書類 7 file 0 の 6 行目(16 番目)。類 W は 6-1-9 と 7-0-1
    keys = [it["T"] for it in p]
    want = [u"T6_0_0", u"T6_1_2", u"T6_1_9", u"T7_0_1", u"T7_0_12"]
    if keys != want:
        out.append(u"本番の行の選び・順が手計算と違う(8 行に 1 行の類 A + 類 W の全部・書類 → file → 行の順): %s" % (keys,))
    if [it["cls"] for it in p] != [u"A", u"A", u"W", u"W", u"A"] or [it["T"] for it in t] != [u"T1_0_0", u"T1_0_1", u"T1_0_2"]:
        out.append(u"類の並び・試しの行(開発の類 A の頭)が手計算と違う")
    if any(it["group"] != "prod" for it in p) or any(it["group"] != "trial" for it in t):
        out.append(u"群の札が違う")
    if wire.get(u"本番の類 A の行(8 行に 1 行)") != 3 or wire.get(u"本番の類 W の行") != 2 or wire.get(u"送る行(本番)") != 5 or wire.get(u"試しの行") != 3 or wire.get(u"指示文の本数(本番 + 試し)") != 16:
        out.append(u"配線の確認の数が手計算と違う")
    if wire.get(u"類 W のうち候補が 1 つの行") != 0 or wire.get(u"前の行が無い行((なし))") != 0:
        out.append(u"配線の確認の「候補が 1 つの類 W」「前の行が無い」の数が違う")
    # 止める: 類の数・行の数
    bad_counts = copy.deepcopy(counts)
    bad_counts["prod"]["A"] += 1
    if stops(ms, ms.select_items, rows, bad_counts, expect, (3, 2, 5, 3), 8, 3) is not True:
        out.append(u"本番の類の数が封の字と違うのに止まらない")
    bad_dev = copy.deepcopy(counts)
    bad_dev["dev"]["W"] += 1
    if stops(ms, ms.select_items, rows, bad_dev, expect, (3, 2, 5, 3), 8, 3) is not True:
        out.append(u"開発の類の数が封の字と違うのに止まらない")
    for es in ((4, 2, 6, 3), (3, 3, 6, 3), (3, 2, 6, 3), (3, 2, 5, 4)):
        if stops(ms, ms.select_items, rows, counts, expect, es, 8, 3) is not True:
            out.append(u"行の数が封の字と違うのに止まらない: %s" % (es,))
    if stops(ms, ms.select_items, rows, counts, expect, (3, 2, 5, 3), 4, 3) is not True:
        out.append(u"8 行に 1 行の間隔を替えても止まらない")
    # 封の字の数の既定(326・68・394・試し 5・類の数)で、足りない作り物は止まる
    if stops(ms, ms.select_items, rows, counts) is not True:
        out.append(u"既定の封の字の数(類の数・行の数)で作り物の行が止まらない")
    for key in (("dev", "A"), ("prod", "W")):
        c2 = copy.deepcopy(ms.EXPECT_WIRE)
        c2["dev"] = od(c2["dev"])
        c2["prod"] = od(c2["prod"])
        c2[key[0]][key[1]] -= 1
        if stops(ms, ms.check_wire, c2) is not True:
            out.append(u"封の類の数より 1 少ないのに check_wire が止まらない: %s" % (key,))
    if stops(ms, ms.check_wire, copy.deepcopy(ms.EXPECT_WIRE)) is not False:
        out.append(u"封の類の数そのままで check_wire が止まる")
    lit = od([("dev", od([("U", 1033), ("A", 208), ("N", 18), ("W", 2)])), ("prod", od([("U", 12444), ("A", 2603), ("N", 387), ("W", 68)]))])
    if stops(ms, ms.check_wire, lit) is not False:
        out.append(u"封の字の類の数(開発 1033・208・18・2・本番 12444・2603・387・68)で check_wire が止まる")
    for g, c in (("dev", "U"), ("dev", "N"), ("prod", "U"), ("prod", "N"), ("prod", "A")):
        l2 = copy.deepcopy(lit)
        l2[g][c] += 1
        if stops(ms, ms.check_wire, l2) is not True:
            out.append(u"封の字の類の数と 1 違うのに check_wire が止まらない: %s %s" % (g, c))
    return out


def prev_label_problems(ms=None):
    u"""前の行 12 個: 同じ file の中の全部の行(類を問わない)の字のうち空でないものの後ろから 12 個。見出しをまたいでよい・file はまたがない。
    純粋な関数と、作り物の書類(便 XG1 の門の作り物)を ``read_docs`` に通した行の前の行の両方で見る。"""
    ms = ms or MS
    out = []
    labs = [u"ア%d" % i if i not in (3, 7, 11) else u"" for i in range(20)]
    nonempty = []
    prevs = []
    for lab in labs:
        prevs.append(ms.previous_labels(nonempty))
        ms.note_label(nonempty, lab)
    want_last = [u"ア5", u"ア6", u"ア8", u"ア9", u"ア10", u"ア12", u"ア13", u"ア14", u"ア15", u"ア16", u"ア17", u"ア18"]
    if prevs[19] != want_last or prevs[0] != [] or u"" in prevs[19] or prevs[4] != [u"ア0", u"ア1", u"ア2"] or prevs[13] != [u"ア0", u"ア1", u"ア2", u"ア4", u"ア5", u"ア6", u"ア8", u"ア9", u"ア10", u"ア12"]:
        out.append(u"前の行(後ろから 12 個・空の字を除く)が手計算と違う: %s" % (prevs[19],))
    tmp = Temp()
    try:
        d = os.path.join(tmp.d, "docs")
        os.makedirs(d)
        XGT.make_docs_dir(d, 5)
        zp = os.path.join(tmp.d, "tax.zip")
        XGT.make_tax_zip(zp)
        orig = XGT.patched_labels(ms.N)
        try:
            with patched(ms.N, TAXZIP_SHA256=XGT.sha_of_path(zp) if hasattr(XGT, "sha_of_path") else hashlib.sha256(open(zp, "rb").read()).hexdigest()):
                rows, counts, secret, material = ms.read_docs(d, None, zp, want=5, say=quiet)
        finally:
            ms.N.W.read_label_bytes = orig
        got = [(r["group"], r["doc"], r["cls"], r["T"], r["E"], r["heading"], r["kind"], r["prev"]) for r in rows]
        want = [
            ("dev", 1, "W", u"資産", u"AssetsAbs", u"連結貸借対照表", "bs", [u"資産"]),
            ("dev", 1, "W", u"その他", u"OthPl", u"損益計算書", "pl", [u"資産", u"資産", u"現金"]),
            ("dev", 1, "A", u"その他", u"OthPl", None, None, []),
            ("dev", 1, "W", u"その他", u"OthNone", u"連結損益計算書及び連結包括利益計算書", "pl", [u"その他"]),
            ("dev", 1, "A", u"その他", u"OthPl", u"注記事項", None, [u"その他", u"その他", u"その他"]),
            ("dev", 1, "A", u"当期変動額", u"ChgSs", u"株主資本等変動計算書", "ss", [u"当期変動額"]),
            ("dev", 1, "W", u"現金同等物", u"CfItem", u"キャッシュ・フロー計算書", "cf", [u"当期変動額", u"当期変動額", u"現金同等物"]),
            ("dev", 2, "A", u"その他", u"OthPl", u"連結損益計算書", "pl", []),
            ("dev", 2, "A", u"その他", u"OthPl", u"損益計算書", "pl", [u"その他"]),
            ("dev", 2, "W", u"その他", u"OthNone", u"損益計算書", "pl", [u"その他", u"その他"])]
        if got != want:
            out.append(u"作り物の書類を read_docs に通した行(群・類・字・見出し・種類・前の行)が手計算と違う: %s" % (got,))
        if list(counts["dev"].values()) != [22, 5, 5, 5] or sum(counts["prod"].values()) != 0:
            out.append(u"作り物の書類の類の数(段 3 の U 22・A 5・N 5・W 5)が手計算と違う: %s" % (dict(counts["dev"]),))
        if [r["ord"][0] for r in rows] != sorted(r["ord"][0] for r in rows) or any(r["cands"] != sorted(r["cands"]) for r in rows):
            out.append(u"行の並び・候補の並び(昇順)が違う")
        if material[u"書類の本数"] != 5 or len(secret[2]) != 5 or not secret[5]:
            out.append(u"材料の欄・漏れの検査の材料(docID の並び・業種の値)が違う")
    finally:
        tmp.close()
    return out


# ---------------------------------------------------------------- 5. 呼ぶ → 読む → 戻す → 札 → P1・P2 → 数える
def answers_problems(ms=None):
    ms = ms or MS
    out = []
    w = fake_world(ms)
    tmp = Temp()
    try:
        tr = make_transport(w)
        run_world(w, tmp, trial=True, transport=tr)
        n_trial = len(tr.n)
        rec = run_world(w, tmp, transport=tr)
        cells = [[r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[10], r[11]] for r in rec[u"行"]]
        if cells != EXPECT_ROWS_CELLS:
            out.append(u"記録の行(類・候補の数・種類・札・2 席の一致・昇順の頭・呼び出しの数)が手計算と違う: %s" % (cells,))
        if n_trial != 4 or len(tr.n) != 4 + 15:
            out.append(u"transport を呼んだ回数が違う(試し 4 + 本番 14 + 読めない 1 回のやり直し 1): %d" % len(tr.n))
        # 番号 → 要素の名: 行甲2 は主 ElemA(昇順の 1 番)・副 ElemC(降順の 5 番)
        st = ms.load_state(tmp.p(u"w", u"work", u"prod"))
        if ms.seat_answer(st, 2, ms.SEATS[0]) != 1 or ms.seat_answer(st, 2, ms.SEATS[1]) != 5 or ms.seat_answer(st, 3, ms.SEATS[0]) != 0 or ms.seat_answer(st, 5, ms.SEATS[0]) is not None:
            out.append(u"途中の答えの番号が手計算と違う(主 ElemA = 1・副 ElemC = 5・0・答えなし)")
        if [ms.pick_of(w.prod[2], s, ms.seat_answer(st, 2, s)) for s in ms.SEATS] != [u"ElemA", u"ElemC"]:
            out.append(u"副の席の降順の番号が要素の名に戻らない")
        T = rec[ms.K_TALLY]
        a, wc = T[u"類 A"], T[u"類 W"]
        if a[u"行"] != 4 or a[u"主の席の札"] != od([(u"正", 2), (u"誤", 1), (u"0", 1), (u"答えなし", 0)]) or a[u"副の席の札"] != od([(u"正", 1), (u"誤", 3), (u"0", 0), (u"答えなし", 0)]):
            out.append(u"類 A の席ごとの札の数が手計算と違う")
        if a[u"P1(主の席だけ)"] != od([(u"通した行", 3), (u"誤って通した行", 1), (u"止めた行", 1), (u"止めた行のうち主の席が正", 0)]):
            out.append(u"類 A の P1 の数が手計算と違う(通した 3・誤って通した 1・止めた 1)")
        if a[u"P2(2 席の一致)"] != od([(u"通した行", 2), (u"誤って通した行", 1), (u"止めた行", 2), (u"止めた行のうち主の席が正", 1)]):
            out.append(u"類 A の P2 の数が手計算と違う(通した 2・誤って通した 1・止めた 2・止めすぎ 1)")
        if (a[u"主の席が誤の行"], a[u"主の席が誤の行のうち P2 が止めた行"]) != (1, 0):
            out.append(u"類 A の「主の席が誤の行のうち P2 が止めた数」が手計算と違う(1・0)")
        if wc[u"行"] != 3 or wc[u"主の席の札"] != od([(u"正", 0), (u"誤", 1), (u"0", 1), (u"答えなし", 1)]) or wc[u"副の席の札"] != od([(u"正", 0), (u"誤", 2), (u"0", 1), (u"答えなし", 0)]):
            out.append(u"類 W の席ごとの札の数が手計算と違う(正は 0)")
        if wc[u"P1(主の席だけ)"] != od([(u"通した行", 1), (u"誤って通した行", 1), (u"止めた行", 2), (u"止めた行のうち主の席が正", 0)]) or \
                wc[u"P2(2 席の一致)"] != od([(u"通した行", 1), (u"誤って通した行", 1), (u"止めた行", 2), (u"止めた行のうち主の席が正", 0)]):
            out.append(u"類 W の P1・P2 の数が手計算と違う(類 W は通した行が全部誤)")
        bands = T[u"類 A を候補の数の帯で分けた"]
        if [bands[k][u"行"] for k in (u"候補 2", u"候補 3〜6", u"候補 7 以上")] != [1, 2, 1] or bands[u"候補 3〜6"][u"P2(2 席の一致)"][u"誤って通した行"] != 1 or bands[u"候補 7 以上"][u"主の席の札"][u"正"] != 1 \
                or bands[u"候補 2"][u"P2(2 席の一致)"][u"通した行"] != 0:
            out.append(u"候補の数の帯ごとの数が手計算と違う(2: 1 行・3〜6: 2 行・7 以上: 1 行)")
        kinds = T[u"類 A を計算書の種類で分けた"]
        if [kinds[k][u"行"] for k in (u"貸借", u"損益", u"キャッシュフロー", u"株主資本等変動", u"種類なし")] != [1, 1, 1, 0, 1] or kinds[u"貸借"][u"主の席の札"][u"正"] != 1 or kinds[u"種類なし"][u"主の席の札"][u"誤"] != 1 \
                or kinds[u"キャッシュフロー"][u"主の席の札"][u"0"] != 1:
            out.append(u"計算書の種類ごとの数が手計算と違う")
        L = rec[ms.K_LINES]
        vals = list(L.values())
        if abs(vals[0] - 1.2262) > 1e-9 or vals[1] != 1 or vals[2] != 4 or dict(vals[3]) != {u"類 A を通す": 4, u"誤って通す": 0, u"類 W を止める": 3} \
                or dict(vals[4]) != {u"類 A を通した": 2, u"誤って通した": 1, u"類 W を止めた": 2}:
            out.append(u"並べる 2 行が手計算と違う(でたらめの期待 1/3 + 1/4 + 1/7 + 1/2 = 1.2262・昇順の頭 1)")
        P = rec[ms.K_PRED]
        want_pred = {
            u"XD0-1": {u"行": 4, u"主の席の正": 2},
            u"XD0-2": {u"行": 4, u"P2 が通した行": 2},
            u"XD0-4": {u"主の席が誤の行": 1, u"P2 が止めた行": 0},
            u"XD0-5": {u"行": 3, u"主の席の 0": 1},
            u"XD0-6": {u"行": 3, u"P2 が通した行(類 W は全部誤)": 1},
            u"XD0-9": {u"副の席の正": 1, u"主の席の正": 2, u"差(主 − 副)": 1},
            u"XD0-10": {u"行": 7, u"主の席の答えなし": 1}}
        for k, v in want_pred.items():
            got = [x for kk, x in P.items() if kk.startswith(k + u" ")]
            if not got or dict(got[0]) != v:
                out.append(u"予測の判定に要る数が手計算と違う: %s → %s" % (k, got))
        g = dict((kk.split(u" ")[0], x) for kk, x in P.items())
        r3 = g[u"XD0-3"]
        if (r3[u"P2 が通した行"], r3[u"誤って通した行"], r3[u"誤って通した行 / 通した行"][u"%"]) != (2, 1, 50.0):
            out.append(u"XD0-3 の数が手計算と違う(通した 2・誤って通した 1・50.0%)")
        r7 = g[u"XD0-7"]
        if (r7[u"行"], r7[u"主の席の正"], r7[u"率"][u"%"]) != (1, 1, 100.0):
            out.append(u"XD0-7 の数が手計算と違う(候補 7 以上は 1 行・正 1・100.0%)")
        r8 = g[u"XD0-8"]
        if (r8[u"種類なし"][u"行"], r8[u"種類なし"][u"分母"], r8[u"種類の在る行(貸借・損益・キャッシュフロー)"][u"行"], r8[u"種類の在る行(貸借・損益・キャッシュフロー)"][u"分母"], r8[u"差(ポイント。種類なし − 種類の在る行)"]) != (0, 1, 2, 3, u"-66.67"):
            out.append(u"XD0-8 の数が手計算と違う(種類なし 0/1・種類の在る行 2/3・差 -66.67)")
        if abs(g[u"XD0-11"] - USD_ALL) > 1e-9:
            out.append(u"XD0-11 の使った額が手計算(試し + 本番)と違う")
        S = rec[ms.K_SUSPECT]
        if (S[u"類 A の主の席の正"], S[u"類 A の主の席の 0"], S[u"類 A の行"], S[u"主の席の答えなし(送った行の全部)"], S[u"類 A で P2 が通した行"], S[u"うち誤"]) != (2, 1, 4, 1, 2, 1) or \
                S[u"条件に当たる(正が 130 行以下)"] is not True or S[u"条件に当たる(0 が類 A の半分を超える)"] is not False or S[u"条件に当たる(答えなしが 40 行以上)"] is not False:
            out.append(u"先に自分の欠陥を疑う条件の数が手計算と違う")
        c = rec[ms.K_CALLS]
        mc, sc = c[u"主"], c[u"副"]
        if (mc[u"呼び出しの数(HTTP の再試行を除く。中断した呼び出しを除く)"], mc[u"答えのやり直し(封 §2-3)"], mc[u"答えなしの行"]) != (8, 1, 1) or \
                (sc[u"呼び出しの数(HTTP の再試行を除く。中断した呼び出しを除く)"], sc[u"答えのやり直し(封 §2-3)"], sc[u"答えなしの行"]) != (7, 0, 0):
            out.append(u"呼び出しの記録の数が手計算と違う(主の席 8 回・やり直し 1・答えなし 1・副の席 7 回)")
        if mc[u"返った block の type の並びの種類"] != [[u"thinking,text", 8]] or mc[u"stop_reason の種類"] != [[u"end_turn", 8]] or mc[u"入力 token の合計"] != 800 or sc[u"入力 token の合計"] != 350 \
                or abs(c[u"USD の全部"] - USD_PROD) > 1e-9 or abs(mc[u"USD 合計"] - 0.008) > 1e-9 or abs(sc[u"USD 合計"] - 0.00525) > 1e-9:
            out.append(u"呼び出しの記録の token・USD・block・stop_reason が手計算と違う")
        tc = rec[ms.K_TRIAL][u"呼び出し"]
        if tc[u"主"][u"呼び出しの数(HTTP の再試行を除く。中断した呼び出しを除く)"] != 2 or tc[u"副"][u"呼び出しの数(HTTP の再試行を除く。中断した呼び出しを除く)"] != 2 or abs(tc[u"USD の全部"] - USD_TRIAL) > 1e-9:
            out.append(u"試しの 4 回の記録が手計算と違う(試しは本番の数に入れない)")
        if len(rec[u"試しの行"]) != 2 or [r[4:6] for r in rec[u"試しの行"]] != [[u"正", u"正"], [u"0", u"誤"]]:
            out.append(u"試しの行の札が手計算と違う")
        if abs(rec[u"費用"][u"使った額 USD(試しを含む)"] - USD_ALL) > 1e-9:
            out.append(u"使った額が手計算(試し 0.0035 + 本番 0.01325)と違う")
        if rec.get(u"封の commit") != SEAL_COMMIT_SHORT or rec[u"呼び出しの形"].get(u"temperature") != u"送らない" or rec[u"呼び出しの形"].get(u"max_tokens") != 100:
            out.append(u"記録の封の commit・呼び出しの形が封と違う")
        if rec[u"席"][u"主の席"][u"候補の並び"] != u"昇順" or rec[u"席"][u"副の席"][u"候補の並び"] != u"降順":
            out.append(u"記録の席の並びの向きが違う")
        if rec[u"便 XG1 の script の sha256"] != XG1_SCRIPT_SHA or rec[u"この script の sha256"] != sha_of(SCRIPT_REL):
            out.append(u"記録の script の sha256 が違う")
    finally:
        tmp.close()
    return out


def trial_not_in_prod_problems(ms=None):
    u"""試しの答えは本番の数に入れない(試しの行が本番の行に混ざらない・試しの額だけ引き継ぐ)。"""
    ms = ms or MS
    out = []
    w = fake_world(ms)
    tmp = Temp()
    try:
        run_world(w, tmp, trial=True)
        pst = tmp.p(u"w", u"work", u"prod", u"progress.json")
        if os.path.exists(pst):
            out.append(u"試しが本番の置き場を作る")
        rec = run_world(w, tmp)
        if len(rec[u"行"]) != 7 or len(rec[u"試しの行"]) != 2 or any(c[0] >= 7 for c in rec[u"呼び出し"]):
            out.append(u"試しの行が本番の行に混ざる")
        base = ms.load_state(tmp.p(u"w", u"work", u"trial"))
        if abs(ms.state_cost(base) - USD_TRIAL) > 1e-9:
            out.append(u"試しの置き場の額が手計算と違う")
    finally:
        tmp.close()
    return out


def retry_problems(ms=None):
    u"""429 は最大 2 回(待ち 2 秒・8 秒)で再試行・それでも返らなければ 1 回の呼び出しとして答えのやり直し・返らない呼び出しは 1 回ごとに見積りの額で数える・HTTP 400 は全体を止める。"""
    ms = ms or MS
    out = []
    w = fake_world(ms)
    items = w.col["prod"][:1]
    est = ms.estimate_usd(len(items[0]["prompt"][ms.SEATS[0]]))
    tmp = Temp()
    try:
        waits = []
        st = ms.new_state()
        ms.run_calls(items, st, tmp.p(u"a"), FAKE_KEY, transport=make_transport(w, seq=lambda n, m, p: (429, b"") if n <= 2 else None), sleep=waits.append, say=quiet)
        first = st[u"calls"][0]
        if waits != [2, 8] or first[u"retries"] != 2 or first[u"http_status"] != 200 or first[u"answer"] is None:
            out.append(u"429 の再試行(待ち 2 秒・8 秒・最大 2 回)が違う: %s %s" % (waits, first[u"retries"]))
        if abs(first[u"est_counted_usd"] - 2 * est) > 1e-5 or abs(first[u"cost_usd"] - (2 * est + 0.001)) > 1e-5:
            out.append(u"返らなかった呼び出しを 1 回ごとに見積りの額で数えない: %s" % (first[u"est_counted_usd"],))
        st2 = ms.new_state()
        ms.run_calls(items, st2, tmp.p(u"b"), FAKE_KEY, transport=make_transport(w, seq=lambda n, m, p: (429, b"") if n <= 3 else None), sleep=quiet, say=quiet)
        c0, c1 = st2[u"calls"][0], st2[u"calls"][1]
        if c0[u"http_status"] != 429 or c0[u"retries"] != 2 or c0[u"answer"] is not None or abs(c0[u"cost_usd"] - 3 * est) > 1e-5 or c0[u"attempt"] != 1 or c1[u"attempt"] != 2 or c1[u"answer"] is None:
            out.append(u"再試行しても返らなかった呼び出しの扱いが違う(答えのやり直しへ進む・3 回分の見積りの額)")
        st3 = ms.new_state()
        seq3 = lambda n, m, p: (None, b"URLError") if n == 1 else ((200, json.dumps({"content": [{"type": "text", "text": u"答え: 1"}], "stop_reason": "end_turn"}).encode()) if n == 2 else None)   # noqa: E731
        ms.run_calls(items, st3, tmp.p(u"c"), FAKE_KEY, transport=make_transport(w, seq=seq3), sleep=quiet, say=quiet)
        if abs(st3[u"calls"][0][u"est_counted_usd"] - est) > 1e-5 or abs(st3[u"calls"][1][u"est_counted_usd"] - est) > 1e-5:
            out.append(u"通信の失敗・usage の無い返事を見積りの額で数えない")
        st4 = ms.new_state()
        n400 = []

        def t400(prompt, model, key):
            n400.append(1)
            return 400, b'{"error":"x"}'
        r = stops(ms, ms.run_calls, items, st4, tmp.p(u"d"), FAKE_KEY, t400, quiet, quiet)
        if r is not True or len(n400) != 1 or st4[u"calls"][0][u"http_status"] != 400 or not st4[u"stopped"]:
            out.append(u"HTTP 400 で全体を止めない(1 回で止まり理由を残す)")
        if FAKE_KEY in ms.dumps(st4) or FAKE_KEY in ms.dumps(st):
            out.append(u"鍵が途中の答えに出る")
    finally:
        tmp.close()
    return out


def cap_problems(ms=None):
    u"""上限: 走らせる前の見積り(試し + 本番・やり直しなし)が上限を超えたら 1 回も呼ばない・走っている間は使った額 + 次の見積りが上限を超えるなら止まる・試しの額は本番の上限に入る・本番の見積りは試しの上限に入る。"""
    ms = ms or MS
    out = []
    w = fake_world(ms)
    seats = ms.SEATS
    est = lambda its: sum(ms.estimate_usd(len(it["prompt"][s])) for it in its for s in seats)               # noqa: E731
    t_est, p_est = est(w.col["trial"]), est(w.col["prod"])
    tmp = Temp()
    try:
        # (1) 試しの前: 試し + 本番の見積りが上限を超える → 1 回も呼ばない・置き場に何も書かない
        tr = make_transport(w)
        r = stops(ms, run_world, w, tmp, True, False, tr, quiet, quiet, u"a", t_est + p_est - 1e-6)
        if r is not True or tr.n or os.path.exists(tmp.p(u"a", u"work")):
            out.append(u"試し + 本番の見積りが上限を超えるのに 1 回も呼ばずに止まらない")
        # 上限ちょうどの手前まで(超えたら、の比較)なら通る
        tr = make_transport(w)
        run_world(w, tmp, trial=True, transport=tr, tag=u"a2", cap=t_est + p_est + 1e-6)
        if len(tr.n) != 4:
            out.append(u"見積りが上限に収まるのに試しを呼べない")
        # (2) 本番の前: 試しの額(使った額)+ 本番の見積りが上限を超える → 本番は 1 回も呼ばない
        used = ms.state_cost(ms.load_state(tmp.p(u"a2", u"work", u"trial")))
        tr = make_transport(w)
        r = stops(ms, run_world, w, tmp, False, False, tr, quiet, quiet, u"a2", p_est + used - 1e-6)
        if abs(used - USD_TRIAL) > 1e-9 or r is not True or tr.n or os.path.exists(tmp.p(u"a2", u"work", u"prod")):
            out.append(u"試しの額が本番の上限に入っていない(本番の見積り + 試しの額が上限を超えるのに呼ぶ)")
        tr = make_transport(w)
        run_world(w, tmp, transport=tr, tag=u"a2", cap=p_est + used + 1e-6)
        if len(tr.n) != 15:
            out.append(u"見積りが上限に収まるのに本番を呼べない(14 回 + やり直し 1 回)")
        # (3) 走っている間: 返らない呼び出し(429)が見積りの額を積むので、走る前の見積りを通っても途中で上限に届く
        tmp_b = Temp()
        try:
            run_world(w, tmp_b, trial=True, tag=u"b")
            used_b = ms.state_cost(ms.load_state(tmp_b.p(u"b", u"work", u"trial")))
            cap = used_b + p_est * 1.2
            tr = make_transport(w, seq=lambda n, m, p: (429, b""))
            r = stops(ms, run_world, w, tmp_b, False, False, tr, quiet, quiet, u"b", cap)
            pst = ms.load_state(tmp_b.p(u"b", u"work", u"prod"))
            if r is not True or not pst[u"stopped"] or used_b + ms.state_cost(pst) > cap + 1e-9 or not tr.n:
                out.append(u"走っている間に使った額が上限に届くのに止まらない(使った額 %s・上限 %s)" % (used_b + ms.state_cost(pst), cap))
            n_stop = len(tr.n)
            r = stops(ms, run_world, w, tmp_b, False, True, tr, quiet, quiet, u"b", cap)
            if r is not True or len(tr.n) != n_stop:
                out.append(u"上限に届いたあとの続きで更に呼ぶ(使った額を引き継がない)")
        finally:
            tmp_b.close()
        # (4) 見積りはやり直しを入れない: 読めない答えのやり直しで見積りが増えない
        tmp_c = Temp()
        try:
            st = ms.new_state()
            p0 = ms.pending_estimate(w.col["prod"], st)
            if abs(p0[0] - p_est) > 1e-9 or p0[1] != 14:
                out.append(u"走らせる前の見積りが(行 × 席 × 1 回)でない(やり直しを入れている)")
            st = ms.new_state()
            ms.run_calls(w.col["prod"][:1], st, tmp_c.p(u"x"), FAKE_KEY, transport=make_transport(w), sleep=quiet, say=quiet)
            left = ms.pending_estimate(w.col["prod"], st)
            if left[1] != 12 or abs(left[0] - est(w.col["prod"][1:])) > 1e-9:
                out.append(u"済んだ(行, 席)を見積りから外していない")
            st = ms.new_state()
            ms.run_calls(w.col["prod"][:1], st, tmp_c.p(u"y"), FAKE_KEY, transport=make_transport(w, seq=lambda n, m, p: (200, fake_body(u"読めません"))), sleep=quiet, say=quiet)
            left = ms.pending_estimate(w.col["prod"], st)
            if len(st[u"calls"]) != 4 or left[1] != 12 or abs(left[0] - est(w.col["prod"][1:])) > 1e-9:
                out.append(u"読めない答えのやり直しを見積りに入れている(呼んだ(行, 席)は 1 回分も数えない)")
        finally:
            tmp_c.close()
    finally:
        tmp.close()
    return out


def resume_problems(ms=None):
    u"""試し(1 回ずつ)→ 本番(試しが無ければ止まる)→ --resume(済んだ(行, 席)は呼ばない)・中断した呼び出しは見積りの額で数える・置き場の取り違えで止まる・置き場が repo の中なら止まる。"""
    ms = ms or MS
    out = []
    w = fake_world(ms)
    tmp = Temp()
    try:
        trn = make_transport(w)
        if stops(ms, run_world, w, tmp, False, False, trn, quiet, quiet, u"w") is not True or trn.n:
            out.append(u"試しが済んでいないのに本番を呼べる")
        wt = fake_world(ms)
        wt.answers[TT(1)] = (None, u"ElemC")
        tmp_t = Temp()
        try:
            trt = make_transport(wt)
            st_t = run_world(wt, tmp_t, trial=True, transport=trt)
            if len(trt.n) != 4 or len(ms.seat_attempts(st_t, 1, ms.SEATS[0])) != 1 or ms.seat_answer(st_t, 1, ms.SEATS[0]) is not None:
                out.append(u"試しは 1 回だけ(読めない答えのやり直しは試しでしない)でない")
            run_world(wt, tmp_t, transport=make_transport(wt))
            if not os.path.exists(tmp_t.p(u"w", u"rec.json")):
                out.append(u"試しの答えが 1 つ読めなくても、呼んだ(行, 席)が済んでいれば本番へ進めるはず")
        finally:
            tmp_t.close()
        tr = make_transport(w)
        st = run_world(w, tmp, trial=True, transport=tr)
        if len(tr.n) != 4 or len(st[u"calls"]) != 4:
            out.append(u"試しが 2 行 × 2 席の 4 回でない(%d)" % len(tr.n))
        if stops(ms, run_world, w, tmp, True, False, tr, quiet, quiet, u"w") is not True:
            out.append(u"試しが済んでいるのに試しをやり直せる")
        if stops(ms, run_world, w, tmp, False, False, make_transport(w), quiet, quiet, u"w2") is not True:
            out.append(u"別の置き場(試しが無い)で本番を呼べる")
        rec = run_world(w, tmp, transport=tr)
        if len(tr.n) != 4 + 15 or ms.dumps(rec[ms.K_TALLY]) != ms.dumps(full_run(ms, w)[ms.K_TALLY]):
            out.append(u"試しの後の本番の呼び出しの数・数えた欄が通しと違う")
        if stops(ms, run_world, w, tmp, False, True, tr, quiet, quiet, u"w") is not True:
            out.append(u"記録が在るのに本番を走らせられる")
        # --resume なしで途中の答えが在れば止まる(記録の書き出しだけ失敗した後)
        tmp2 = Temp()
        try:
            tr2 = make_transport(w)
            run_world(w, tmp2, trial=True, transport=tr2)
            with patched(ms, record_text=lambda r, s=None, k=None: (_ for _ in ()).throw(ms.Stop(u"**作り物: 記録の書き出しで止まる**"))):
                try:
                    run_world(w, tmp2, transport=tr2)
                except SystemExit:
                    pass
            n1 = len(tr2.n)
            if n1 != 19 or os.path.exists(tmp2.p(u"w", u"rec.json")):
                out.append(u"記録の書き出しで止める作り物が効いていない")
            if stops(ms, run_world, w, tmp2, False, False, tr2, quiet, quiet, u"w") is not True:
                out.append(u"途中の答えが在るのに --resume なしで続けられる(有料の呼び出しを二度する)")
            rec2 = run_world(w, tmp2, resume=True, transport=tr2)
            if len(tr2.n) != n1 or not os.path.exists(tmp2.p(u"w", u"rec.json")) or ms.dumps(rec2[ms.K_TALLY]) != ms.dumps(rec[ms.K_TALLY]):
                out.append(u"呼ぶ行が残っていないのに --resume が呼ぶ・記録の数が通しと違う")
        finally:
            tmp2.close()
        # 置き場の指示文が今と違えば止まる・返った text が書き換わっていれば止まる(本番を途中で中断した置き場に --resume する)
        tmp3 = Temp()
        try:
            run_world(w, tmp3, trial=True, transport=make_transport(w))
            try:
                run_world(w, tmp3, transport=make_transport(w, seq=lambda n, m, p: (_ for _ in ()).throw(KeyboardInterrupt()) if n == 6 else None))
            except KeyboardInterrupt:
                pass
            w2 = fake_world(ms)
            w2.col["prod"][0] = ms.make_item(od([("doc", 1), ("cls", "A"), ("kind", "pl"), ("heading", u"見出し別"), ("prev", [u"前の" + TN(0)]), ("T", TN(0)), ("E", u"ElemB"), ("cands", [u"ElemA", u"ElemB", u"ElemC"])]), "prod")
            if stops(ms, run_world, w, tmp3, False, True, make_transport(w), quiet, quiet, u"w", None, None, FAKE_KEY, w2.col) is not True:
                out.append(u"途中の答えの指示文の sha256 が今と違うのに止まらない")
            w3 = fake_world(ms)
            w3.col["prod"][0]["sha"][ms.SEATS[1]] = u"0" * 64
            if stops(ms, run_world, w, tmp3, False, True, make_transport(w), quiet, quiet, u"w", None, None, FAKE_KEY, w3.col) is not True:
                out.append(u"途中の答えの副の席の指示文の sha256 が今と違うのに止まらない")
            rp = ms.reply_path(os.path.join(tmp3.p(u"w", u"work"), u"prod"), 0, ms.SEATS[0], 1)
            sp = ms.reply_path(os.path.join(tmp3.p(u"w", u"work"), u"prod"), 0, ms.SEATS[1], 1)
            if not os.path.exists(rp) or not os.path.exists(sp):
                out.append(u"返った text が置き場に置かれていない")
            else:
                with io.open(rp, "a", encoding="utf-8") as fh:
                    fh.write(u"x")
                if stops(ms, run_world, w, tmp3, False, True, make_transport(w), quiet, quiet, u"w") is not True:
                    out.append(u"返った text が書き換わっているのに止まらない")
                os.remove(rp)
                if stops(ms, run_world, w, tmp3, False, True, make_transport(w), quiet, quiet, u"w") is not True:
                    out.append(u"返った text の file が無いのに止まらない")
        finally:
            tmp3.close()
        tmp4 = Temp()
        try:
            run_world(w, tmp4, trial=True, transport=make_transport(w))
            try:
                run_world(w, tmp4, transport=make_transport(w, seq=lambda n, m, p: (_ for _ in ()).throw(KeyboardInterrupt()) if n == 3 else None))
            except KeyboardInterrupt:
                pass
            else:
                out.append(u"中断が伝わらない")
            s3 = ms.load_state(tmp4.p(u"w", u"work", u"prod"))
            if s3 is None or not s3[u"in_flight"] or len(s3[u"calls"]) != 2:
                out.append(u"呼ぶ前に残す印(in_flight)が無い")
            rec3 = run_world(w, tmp4, resume=True, transport=make_transport(w))
            ab = [c for c in ms.load_state(tmp4.p(u"w", u"work", u"prod"))[u"calls"] if c[u"aborted"]]
            if len(ab) != 1 or ab[0][u"cost_usd"] <= 0 or abs(ab[0][u"cost_usd"] - ab[0][u"est_usd"]) > 1e-9:
                out.append(u"中断した呼び出しを見積りの額で数えない")
            if abs(rec3[u"費用"][u"使った額 USD(試しを含む)"] - (USD_ALL + ab[0][u"cost_usd"])) > 1e-6:
                out.append(u"中断した呼び出しの額が使った額に入らない")
            if [r[:8] for r in rec3[u"行"]] != [r[:8] for r in rec[u"行"]]:
                out.append(u"中断の後の続きの記録の行が通しの記録と違う")
        finally:
            tmp4.close()
        # 置き場が repo の中なら、何も書かずに止まる(送った文を repo に置かない)
        inside = os.path.join(ROOT, u"xd0_gate_inside_work")
        trn = make_transport(w)
        if stops(ms, run_world, w, tmp, True, False, trn, quiet, quiet, u"x", None, inside) is not True or trn.n or os.path.exists(inside):
            out.append(u"置き場が repo の中なのに止まる・書いてしまう")
            shutil.rmtree(inside, ignore_errors=True)
    finally:
        tmp.close()
    return out


def c400_problems(ms=None):
    u"""HTTP 400(断りの文)の扱い: 本文の error.message を(鍵を含まないと確かめて)進捗に残し印字する・記録には書かない・全体を止める。
    前の走りの 400 は答えの回に数えず額を引き継ぎ、試しをもう 1 度走らせると頭の行を呼び直す(答えが 1 つも無い置き場でだけ)。"""
    ms = ms or MS
    out = []
    w = fake_world(ms)
    msg = u"`thinking` is not accepted for this model."
    tmp = Temp()
    try:
        lines = []
        t400 = lambda n, m, p: (400, json.dumps({"type": "error", "error": {"type": "invalid_request_error", "message": msg}}).encode())      # noqa: E731
        tr1 = make_transport(w, seq=t400)
        if stops(ms, run_world, w, tmp, True, False, tr1, quiet, lines.append) is not True or len(tr1.n) != 1:
            out.append(u"試しの 1 回目が 400 で全体を止めない")
        st = ms.load_state(tmp.p(u"w", u"work", u"trial"))
        c0 = st[u"calls"][0]
        est = ms.estimate_usd(len(w.col["trial"][0]["prompt"][ms.SEATS[0]]))
        if c0.get(u"error_message") != msg or not any(msg in l for l in lines) or not st[u"stopped"]:
            out.append(u"400 の断りの文を進捗と印字に残さない")
        if abs(ms.state_cost(st) - est) > 1e-6:
            out.append(u"400 の呼び出しを見積りの額で数えない")
        for bad in (u"x sk-abcdefghijklmnop1234 y", u"bad %s bad" % FAKE_KEY):
            r = ms.error_message_of(json.dumps({"error": {"message": bad}}).encode(), FAKE_KEY)
            if r is None or bad in r or FAKE_KEY in r or u"sk-abc" in r:
                out.append(u"400 の本文に鍵らしい字が在るのに残す")
        if ms.error_message_of(b"not json", FAKE_KEY) is not None or ms.error_message_of(json.dumps({"error": 1}).encode(), FAKE_KEY) is not None:
            out.append(u"形が違う本文を None にしない")
        if len(ms.error_message_of(json.dumps({"error": {"message": u"あ" * 1000}}).encode(), FAKE_KEY)) != 300:
            out.append(u"400 の本文を 300 字に切らない")
        tr2 = make_transport(w)
        st2 = run_world(w, tmp, trial=True, transport=tr2)
        if len(tr2.n) != 4 or len(st2[u"calls"]) != 5:
            out.append(u"直した後の試しが 2 行 × 2 席の 4 回を呼び直さない(呼び出し %d)" % len(tr2.n))
        retired = [c for c in st2[u"calls"] if c[u"aborted"]]
        if len(retired) != 1 or retired[0][u"config_error"] != 400 or abs(retired[0][u"cost_usd"] - est) > 1e-6 or retired[0][u"attempt"] is not None:
            out.append(u"前の走りの 400 を答えの回から外して額を残さない")
        if abs(ms.state_cost(st2) - (est + USD_TRIAL)) > 1e-6:
            out.append(u"試しの額が前の 400 の額を引き継いでいない")
        if stops(ms, run_world, w, tmp, True, False, make_transport(w), quiet, quiet, u"w") is not True:
            out.append(u"答えが返った置き場で試しをもう 1 度走らせられる")
        rec = run_world(w, tmp, transport=make_transport(w))
        if abs(rec[u"費用"][u"使った額 USD(試しを含む)"] - (USD_ALL + est)) > 1e-6:
            out.append(u"400 の後の試し → 本番の額が手計算と違う")
        if msg in ms.dumps(rec) or FAKE_KEY in ms.dumps(rec):
            out.append(u"記録に 400 の断りの文か鍵が在る")
    finally:
        tmp.close()
    return out


def dict_keys(o):
    u"""記録の中の dict の key(入れ子の全部)。"""
    if isinstance(o, dict):
        for k, v in o.items():
            yield k
            for x in dict_keys(v):
                yield x
    elif isinstance(o, list):
        for v in o:
            for x in dict_keys(v):
                yield x


def realshape_problems(ms=None):
    u"""実物と同じ形の返事(block は text だけ・stop_reason は end_turn)で、``build_record`` → ``record_text``(``check_clean`` を通る)まで本物の関数で通す。
    API の返事の字(block の type・stop_reason・HTTP の状態)が記録の dict の key になると、禁止欄(text など)に当たって記録が書けない。"""
    ms = ms or MS
    out = []
    w = fake_world(ms)
    tmp = Temp()
    try:
        tr = make_transport(w, blocks=("text",))
        try:
            run_world(w, tmp, trial=True, transport=tr)
            rec = run_world(w, tmp, transport=tr)
        except SystemExit as e:
            return [u"実物と同じ形の返事で記録が書けない(止まった): %s" % str(e)[:60]]
        c = rec[ms.K_CALLS][u"主"]
        if c[u"返った block の type の並びの種類"] != [[u"text", 8]] or c[u"stop_reason の種類"] != [[u"end_turn", 8]] or c[u"HTTP の状態の種類"] != [[u"200", 8]]:
            out.append(u"返事の字の種類が [字, 回数] の組の並びでない: %s" % (c[u"返った block の type の並びの種類"],))
        for k in dict_keys(rec):
            if k in (u"text", u"end_turn", u"200"):
                out.append(u"API の返事の字が記録の欄の名になっている: %s" % k)
        if not os.path.exists(tmp.p(u"w", u"rec.json")):
            out.append(u"記録が書かれていない")
    finally:
        tmp.close()
    return out


def leak_problems(ms=None):
    u"""鍵の字が置き場の全部の file・記録・例外・途中の答えに出ない。記録は書く前と書いた後に検査される。行の字・見出しの字・要素の名・docID が記録に入れば止まる。"""
    ms = ms or MS
    out = []
    w = fake_world(ms)
    tmp = Temp()
    try:
        log = []
        tr = make_transport(w, log=log)
        run_world(w, tmp, trial=True, transport=tr)
        rec = run_world(w, tmp, transport=tr)
        if not log or any(k != FAKE_KEY for _m, _p, k in log):
            out.append(u"transport に渡る鍵が引数の鍵でない")
        for dp, _dn, fn in os.walk(tmp.d):
            for f in fn:
                with io.open(os.path.join(dp, f), encoding="utf-8") as fh:
                    if FAKE_KEY in fh.read():
                        out.append(u"鍵の字が file に出ている: %s" % f)
        if rec[u"key_leaks"] != []:
            out.append(u"記録の key_leaks が空でない")
        text = ms.dumps(rec)
        for tok in (u"行甲", u"表見出し項目", u"前行項目", u"試験項目", u"ElemA", u"ElemB", u"ElemZ", u"読めません", FAKE_KEY):
            if tok in text:
                out.append(u"記録に行の字・見出しの字・要素の名・返った text・鍵の字が在る: %s" % tok[:3])
        bad = [k for k in dict_keys(rec) if k in (u"span", u"value", u"text", u"文", u"sentence", u"元の字", u"docID", u"name", u"label", u"row", u"element", u"tag")]
        if bad:
            out.append(u"記録に置いてはいけない欄が在る: %s" % bad[:3])
        if DOCID_RE.search(text):
            out.append(u"記録に docID の形の字が在る")
        sec = w.col["secret"]
        # 書いてはいけない字が入れば書かずに止まる(secret = 行の字・要素の名・docID・EDINET コード・見出しの字・業種の値)
        for why, mut in ((u"鍵の値", lambda r: r.__setitem__(u"step", r[u"step"] + u" " + FAKE_KEY)),
                         (u"鍵の形", lambda r: r.__setitem__(u"step", r[u"step"] + u" sk-abcdefghijklmnop1234")),
                         (u"行の字", lambda r: r.__setitem__(u"step", r[u"step"] + u" " + TN(0))),
                         (u"行の字の一部(5 字以上の字が入る)", lambda r: r.__setitem__(u"step", r[u"step"] + u" 前行項目5です")),
                         (u"要素の名", lambda r: r.__setitem__(u"step", r[u"step"] + u" ElemB")),
                         (u"候補だけの要素の名", lambda r: r.__setitem__(u"step", r[u"step"] + u" ElemD")),
                         (u"見出しの字", lambda r: r.__setitem__(u"step", r[u"step"] + u" 表見出し項目2です")),
                         (u"置いてはいけない欄", lambda r: r.__setitem__(u"label", u"x")),
                         (u"docID の形", lambda r: r.__setitem__(u"step", r[u"step"] + u" S100" + u"ABCD"))):
            r2 = copy.deepcopy(rec)
            mut(r2)
            if stops(ms, ms.record_text, r2, sec, FAKE_KEY) is not True:
                out.append(u"記録に書いてはいけないもの(%s)が入っても止まらない" % why)
        r5 = copy.deepcopy(rec)
        r5[u"行"][0][0] = u"sk-" + u"a" * 40
        if stops(ms, ms.write_record, tmp.p(u"leak.json"), r5, sec, FAKE_KEY) is not True or os.path.exists(tmp.p(u"leak.json")):
            out.append(u"鍵の形の字が行に入っても書かずに止まらない")
        if stops(ms, ms.write_record, tmp.p(u"w", u"rec.json"), rec, sec, FAKE_KEY) is not True:
            out.append(u"記録が既に在るのに書き直せる")
        saved = os.environ.pop(ms.KEY_ENV, None)
        try:
            if stops(ms, ms.get_key) is not True:
                out.append(u"環境変数が無いのに get_key が止まらない")
            os.environ[ms.KEY_ENV] = FAKE_KEY
            if ms.get_key() != FAKE_KEY:
                out.append(u"get_key が環境変数の値を返さない")
        finally:
            os.environ.pop(ms.KEY_ENV, None)
            if saved is not None:
                os.environ[ms.KEY_ENV] = saved
    finally:
        tmp.close()
    return out


class FakeResp(object):
    def __init__(self, status, data):
        self.status, self.data = status, data

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def getcode(self):
        return self.status

    def read(self):
        return self.data


def call_problems(ms=None):
    u"""``call_api`` が送る request の形(``urlopen`` を差し替える。通信しない)・HTTP 4xx は status で返す・通信の失敗は型だけ。"""
    ms = ms or MS
    out = []
    sent = []

    def fake_open(req, timeout=None):
        sent.append((req, timeout))
        return FakeResp(200, b'{"ok":1}')
    with patched(urllib.request, urlopen=fake_open):
        for model in ("claude-sonnet-5-5", "claude-haiku-5-5"):
            st, bd = ms.call_api(u"指示文 A", model, FAKE_KEY)
            req, timeout = sent[-1]
            b = json.loads(req.data.decode("utf-8"))
            want = {"model": model, "max_tokens": 100, "thinking": {"type": "between_tools"} if model == "claude-sonnet-5-5" else {"type": "disabled"},
                    "messages": [{"role": "user", "content": u"指示文 A"}]}
            if "temperature" in b:
                out.append(u"body に temperature の欄が在る(欄そのものを送らない): %s" % model)
            if st != 200 or b != want:
                out.append(u"送る body の形が封(max_tokens 100・temperature の欄なし・思考の指定・system なし・user の 1 message)と違う: %s" % model)
        if req.full_url != "https://api.anthropic.com/v1/messages" or req.get_method() != "POST" or req.get_header("Anthropic-version") != "2023-06-01":
            out.append(u"送り先・method・API の版が違う")
        if req.get_header("X-api-key") != FAKE_KEY or FAKE_KEY in req.data.decode("utf-8") or FAKE_KEY in req.full_url:
            out.append(u"鍵が header だけに入っていない(body・URL に入っている)")

    def http_error(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 429, u"x", {}, io.BytesIO(b"slow"))
    with patched(urllib.request, urlopen=http_error):
        st, bd = ms.call_api(u"x", "claude-haiku-5-5", FAKE_KEY)
        if (st, bd) != (429, b"slow"):
            out.append(u"HTTP 429 を status で返さない")

    def broken(req, timeout=None):
        raise OSError(u"鍵 %s を含む文" % FAKE_KEY)
    with patched(urllib.request, urlopen=broken):
        st, bd = ms.call_api(u"x", "claude-haiku-5-5", FAKE_KEY)
        if st is not None or FAKE_KEY.encode() in bd or bd != b"OSError":
            out.append(u"通信の失敗で例外の型以外(鍵を含む文)を返す")
    return out


def dry_problems(ms=None):
    u"""``--dry-run``: 鍵を読まず(``get_key`` を呼ばない・環境変数が無くても走る)・通信せず・記録を書かず・文を印字せず・数を出す。作り物の transport の検査が 5 つ通る。"""
    ms = ms or MS
    out = []
    w = fake_world(ms)
    lines = []
    saved = os.environ.pop(ms.KEY_ENV, None)

    def no_net(*a, **k):
        raise AssertionError(u"通信した")

    def no_key():
        raise AssertionError(u"鍵を読んだ")
    try:
        col = copy.deepcopy(w.col)
        col["wire"] = od([(u"段 3 の類の数(開発)", od([("U", 1), ("A", 2), ("N", 3), ("W", 4)])), (u"段 3 の類の数(本番)", od([("U", 5), ("A", 6), ("N", 7), ("W", 8)])),
                          (u"類 W のうち候補が 1 つの行", 0), (u"見出しが無い行(%s)" % u"(なし)", 0), (u"見出しが空の字の行(【】)", 0), (u"見出しに改行を含む行", 0), (u"前の行が無い行(%s)" % u"(なし)", 0)])
        with patched(urllib.request, urlopen=no_net), patched(ms, get_key=no_key, call_api=no_net):
            res = ms.dry_run(root=ROOT, collected=col, say=lines.append)
        text = u"\n".join(lines)
        if len(res["items"]) != 9 or res["chars"] != sum(len(it["prompt"][s]) for it in res["items"] for s in ms.SEATS):
            out.append(u"dry-run が組んだ指示文の数・字数が違う")
        if any(tok in text for tok in (u"行甲", u"表見出し項目", u"前行項目", u"試験項目", u"ElemA", u"ElemB")):
            out.append(u"dry-run が材料の字を印字する")
        for need in (u"行の数(本番)", u"席ごとの本数", u"字数の合計", u"見積り", u"配線の確認", u"通信していない", u"試し + 本番", u"上限を超えるか"):
            if need not in text:
                out.append(u"dry-run の出力に %s が無い" % need)
        if not all(res["self_test"].values()) or len(res["self_test"]) != 5:
            out.append(u"dry-run の作り物の transport の検査が 5 つ全部通らない")
        want_est = sum(ms.estimate_usd(len(it["prompt"][s])) for it in res["items"] for s in ms.SEATS)
        if abs(res["est_usd"] - want_est) > 1e-9 or abs(res["est_max_usd"] - 2 * want_est) > 1e-9:
            out.append(u"dry-run の見積り(試し + 本番・1 回ずつ。最大 = やり直しを全部入れた 2 倍)が違う")
        if ms.CACHE_DIR in text:
            out.append(u"dry-run が置き場の path を出す")
    finally:
        if saved is not None:
            os.environ[ms.KEY_ENV] = saved
    return out


def check_cmd_problems(ms=None):
    u"""``--check``: 記録の行・呼び出しの欄から数を作り直して照らし(1 つ変えれば止まる)、材料と置き場の途中の答えから行・呼び出しの欄を組み直して照らす。鍵・通信なし。"""
    ms = ms or MS
    out = []
    w = fake_world(ms)
    tmp = Temp()
    try:
        run_world(w, tmp, trial=True)
        rec = run_world(w, tmp)
        text = ms.dumps(rec)
        base = tmp.p(u"w", u"work")

        def chk(r, col=None, work=None):
            with patched(urllib.request, urlopen=lambda *a, **k: 1 / 0):
                return ms.check(root=ROOT, rec=r, collected=copy.deepcopy(col if col is not None else w.col), work=work or base, say=quiet, fp=od())
        load = lambda: json.loads(text, object_pairs_hook=collections.OrderedDict)               # noqa: E731
        try:
            chk(load())
        except BaseException as exc:                      # noqa: BLE001
            out.append(u"作った記録を --check が通さない(%s)" % type(exc).__name__)
        muts = []

        def mut(fn, why):
            r = load()
            fn(r)
            muts.append((r, why))
        mut(lambda r: r[u"行"][0].__setitem__(4, u"誤"), u"行の主の席の札を 1 つ替える")
        mut(lambda r: r[u"行"][3].__setitem__(5, u"正"), u"行の副の席の札を 1 つ替える")
        mut(lambda r: r[u"行"][5].__setitem__(4, u"0"), u"行の主の席の答えなしを 0 に替える")
        mut(lambda r: r[u"行"][1].__setitem__(6, False), u"行の「2 席が同じ要素」を替える")
        mut(lambda r: r[u"行"][2].__setitem__(7, False), u"行の「昇順の頭が書類の要素」を替える")
        mut(lambda r: r[u"行"][0].__setitem__(10, 2), u"行の呼び出しの数を替える")
        mut(lambda r: r[u"行"][1].__setitem__(8, u"0" * 64), u"行の主の席の指示文の sha256 を替える")
        mut(lambda r: r[u"行"][1].__setitem__(9, u"0" * 64), u"行の副の席の指示文の sha256 を替える")
        mut(lambda r: r[u"行"][0].__setitem__(2, 4), u"行の候補の数を替える")
        mut(lambda r: r[u"行"][0].__setitem__(3, u"貸借"), u"行の計算書の種類を替える")
        mut(lambda r: r[u"呼び出し"][0].__setitem__(2, 2), u"呼び出しの欄の答えの回を替える")
        mut(lambda r: r[u"呼び出し"][0].__setitem__(10, 0.5), u"呼び出しの欄の USD を替える")
        mut(lambda r: r[u"試しの呼び出し"][0].__setitem__(10, 0.5), u"試しの呼び出しの欄の USD を替える")
        mut(lambda r: r[u"呼び出し"][0].__setitem__(12, 999), u"呼び出しの欄の返った text の字数を替える(数えた欄に出ない欄)")
        mut(lambda r: r[u"試しの呼び出し"][1].__setitem__(12, 999), u"試しの呼び出しの欄の返った text の字数を替える")
        mut(lambda r: r[u"試しの行"][0].__setitem__(4, u"誤"), u"試しの行の札を替える")
        mut(lambda r: r[ms.K_TALLY][u"類 A"].__setitem__(u"行", 5), u"数えた欄の行の数を替える")
        mut(lambda r: r[ms.K_PRED].__setitem__(u"XD0-10 主の席の答えなし(送った行の全部)", {u"行": 7, u"主の席の答えなし": 0}), u"予測の判定に要る数を替える")
        mut(lambda r: r.__setitem__(u"この script の sha256", u"0" * 64), u"script の sha256 を替える")
        mut(lambda r: r.__setitem__(u"便 XG1 の script の sha256", u"0" * 64), u"便 XG1 の script の sha256 を替える")
        mut(lambda r: r[ms.K_WIRE].__setitem__(u"送る行(本番)", 9), u"配線の確認の数を替える")
        mut(lambda r: r[ms.K_CALLS][u"主"].__setitem__(u"答えなしの行", 0), u"呼び出しの記録の数を替える")
        for r, why in muts:
            if stops(ms, chk, r) is not True:
                out.append(u"--check が止まらない: %s" % why)
        w2 = fake_world(ms)
        w2.col["prod"][1] = ms.make_item(od([("doc", 1), ("cls", "A"), ("kind", None), ("heading", u"見出し別"), ("prev", [u"前の" + TN(1)]), ("T", TN(1)), ("E", u"ElemC"), ("cands", [u"ElemA", u"ElemB", u"ElemC", u"ElemD"])]), "prod")
        if stops(ms, chk, load(), w2.col) is not True:
            out.append(u"--check が材料の字の変更(指示文の sha256 の違い)で止まらない")
        # 置き場の途中の答えが変われば止まる(返った text の書き換え)
        rp = ms.reply_path(os.path.join(base, u"prod"), 0, ms.SEATS[0], 1)
        with io.open(rp, "a", encoding="utf-8") as fh:
            fh.write(u"x")
        if stops(ms, chk, load()) is not True:
            out.append(u"--check が返った text の書き換えで止まらない")
        if stops(ms, chk, load(), None, tmp.p(u"none")) is not True:
            out.append(u"置き場の途中の答えが無いのに --check が止まらない")
        r = load()
        r[u"行"][0][1] = u"Q"
        if stops(ms, chk, r) is not True:
            out.append(u"--check が行の類の変更で止まらない")
        if not os.path.exists(os.path.join(ROOT, RECORD_REL)) and stops(ms, ms.check, ROOT, quiet, None, copy.deepcopy(w.col), base) is not True:
            out.append(u"記録が無いのに --check が止まらない")
    finally:
        tmp.close()
    return out


# ---------------------------------------------------------------- 6. 配線(import・予約名・境界)
def import_problems(src=None):
    u"""script の import は標準ライブラリの一覧だけ(通信は ``urllib`` の 1 つだけ)。eval・exec・動的 import が無い。前の便の script は便 XG1 と aiforms_gen の 2 本だけ。
    環境変数は ``get_key`` の 1 か所だけが読む。``.env`` を読まない。0 円の経路の関数は ``get_key``・``call_api`` を呼ばない。"""
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
                out.append(u"許す一覧に無い module: %s" % nm)
    if any(isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "subprocess" for n in ast.walk(tree)):
        out.append(u"subprocess を使っている")
    loads = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "load_module"]
    if sorted(c.args[0].value for c in loads if c.args and isinstance(c.args[0], ast.Constant)) != ["xbrl_aiforms_gen_2026-11-03.py", "xbrl_tag_narrow_2026-11-21.py"]:
        out.append(u"読む前の便の script が便 XG1 と aiforms_gen の 2 本だけでない")
    env_uses = [n for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "os" and n.attr in ("environ", "getenv")]
    if len(env_uses) != 1:
        out.append(u"環境変数を読む所が 1 か所でない(%d)" % len(env_uses))
    funcs = dict((n.name, n) for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    gk = funcs.get("get_key")
    if gk is None or not any(u.lineno >= gk.lineno and u.lineno <= max(getattr(x, "lineno", 0) for x in ast.walk(gk)) for u in env_uses):
        out.append(u"環境変数を読むのが get_key の中でない")
    for fname in ("dry_run", "check", "collect_all", "read_docs", "select_items", "self_test", "build_record", "derived_sections", "build_rows", "tally", "predictions"):
        f = funcs.get(fname)
        if f is None:
            out.append(u"関数が無い: %s" % fname)
            continue
        names_used = set(x.id for x in ast.walk(f) if isinstance(x, ast.Name))
        for bad in ("get_key", "call_api", "urlopen"):
            if bad in names_used:
                out.append(u"%s が %s を使っている(鍵を読む・通信する道が 0 円の経路に在る)" % (fname, bad))
    docs = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant):
            docs.add(id(n.body[0].value))
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs and (u".env" in n.value or u"dotenv" in n.value):
            out.append(u".env を読む字が在る(説明文の外)")
    return out


def reserved_problems(rel=GATE_REL, base=ROOT):
    out = []
    with open(os.path.join(base, rel), encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    for n, line in enumerate(lines, 1):
        if any(re.match(r"%s\w*\s*=" % re.escape(p), line) for p in RESERVED_PREFIXES):
            out.append(u"%s:%d が既存の門の数える名前を行頭に置いている" % (rel, n))
    return out


# ---------------------------------------------------------------- 7. 記録が在るときだけ
REC_ALLOWED_WORDS = set([u"A", u"W", u"正", u"誤", u"0", u"答えなし", u"貸借", u"損益", u"キャッシュフロー", u"株主資本等変動", u"種類なし", u"主", u"副", u"thinking,text", u"text", u"end_turn", u"max_tokens", u"?"])


def record_problems(ms=None):
    u"""記録が在れば、記録の形・書かないものが無い・行と呼び出しの欄から数を作り直せる・足し合わせ、を見る。記録が無ければ None(検査は結果の門に置く)。"""
    ms = ms or MS
    p = os.path.join(ROOT, RECORD_REL)
    if not os.path.exists(p):
        return None
    rec = json.loads(read(RECORD_REL), object_pairs_hook=od)
    out = []
    if rec.get(u"seal") != SEAL_REL or rec.get(u"封の commit") != SEAL_COMMIT_SHORT or rec.get(u"行の欄") != ms.ROW_COLUMNS or rec.get(u"呼び出しの欄") != ms.CALL_COLUMNS:
        out.append(u"記録の封・commit・欄の形が決めと違う")
    if len(rec.get(u"行", [])) != 394 or len(rec.get(u"試しの行", [])) != 5 or rec.get(u"key_leaks") != []:
        out.append(u"記録の行の数が 394(試し 5)でないか key_leaks が空でない")
    now = ms.derived_sections(rec[u"行"], rec[u"呼び出し"], rec[u"試しの呼び出し"], len(rec[u"試しの行"]))
    for k, v in now.items():
        if ms.dumps(rec[k]) != ms.dumps(v):
            out.append(u"記録の欄が行・呼び出しの欄から作り直した数と違う: %s" % k)
    cells = [r[ms.C_CLS] for r in rec[u"行"]]
    if cells.count(u"A") != 326 or cells.count(u"W") != 68:
        out.append(u"記録の行の類が 326・68 でない")
    for r in rec[u"行"]:
        for i, cell in enumerate(r):
            if isinstance(cell, str) and cell not in REC_ALLOWED_WORDS and not re.match(r"^[0-9a-f]{64}$", cell):
                out.append(u"記録の行に決めの語・sha256 以外の字が在る(列 %d)" % i)
                break
    a = rec[ms.K_TALLY][u"類 A"]
    if sum(a[u"主の席の札"].values()) != 326 or sum(a[u"副の席の札"].values()) != 326 or sum(rec[ms.K_TALLY][u"類 W"][u"主の席の札"].values()) != 68:
        out.append(u"席ごとの札の足し合わせが 326・68 でない")
    c = rec[ms.K_CALLS]
    if abs(c[u"USD の全部"] + rec[ms.K_TRIAL][u"呼び出し"][u"USD の全部"] - rec[u"費用"][u"使った額 USD(試しを含む)"]) > 1e-6:
        out.append(u"呼び出しの USD の足し合わせが使った額と違う")
    try:
        ms.check_text(rec, ms.dumps(rec))
    except SystemExit:
        out.append(u"記録に置いてはいけない欄か鍵らしい字が在る")
    if DOCID_RE.search(read(RECORD_REL)):
        out.append(u"記録に docID の形の字が在る")
    return out


# ---------------------------------------------------------------- 8. 材料の確かめ(材料が在るときだけ)
_MAT = {}


def have_material():
    return len(glob.glob(os.path.join(MS.N.DOCS_DIR, "*.zip"))) >= MS.N.DOCS_WANT and os.path.isfile(MS.N.TAXZIP_PATH) and os.path.isdir(MS.N.TAXONOMY_DIR)


def material_problems(ms=None):
    u"""材料が無ければ None。在れば本物の材料から: 類の数(開発・本番)・行の数 326・68・394・試し 5・席ごとの並びの向き・指示文の字数の上限・封 §2-2 の例(開発の 1 行)が字で一致する。"""
    ms = ms or MS
    if not have_material():
        return None
    if "col" not in _MAT:
        _MAT["col"] = ms.collect_all(root=ROOT, say=quiet)
    col = _MAT["col"]
    out = []
    if len(col["prod"]) != 394 or len(col["trial"]) != 5 or [it["cls"] for it in col["prod"]].count("A") != 326 or [it["cls"] for it in col["prod"]].count("W") != 68:
        out.append(u"本物の材料の送る行の数が 326・68・394・試し 5 でない")
    if any(it["cands"][ms.SEATS[0]] != sorted(it["cands"][ms.SEATS[0]]) or it["cands"][ms.SEATS[1]] != sorted(it["cands"][ms.SEATS[0]], reverse=True) for it in col["prod"] + col["trial"]):
        out.append(u"本物の材料の候補の並びが主は昇順・副は降順でない")
    if any(it["group"] != "trial" for it in col["trial"]) or any(it["cls"] != "A" for it in col["trial"]):
        out.append(u"試しの行が開発の類 A でない")
    if any(it["cls"] == "A" and it["E"] not in it["cands"][ms.SEATS[0]] for it in col["prod"]) or any(it["cls"] == "W" and it["E"] in it["cands"][ms.SEATS[0]] for it in col["prod"]):
        out.append(u"類 A の候補に書類の要素が無い・類 W の候補に書類の要素が在る")
    rows, counts, _s, _m = ms.read_docs(dev_only=True, say=quiet)
    _blk, example = seal_blocks(seal_text())
    hits = [r for r in rows if ms.make_item(r, "x")["prompt"][ms.SEATS[0]].split(u"\n\n")[1] == example]
    if len(hits) != 1:
        out.append(u"封 §2-2 の例(実物の 1 行)が開発の材料から字で 1 行だけ組めない(%d 行)" % len(hits))
    if list(counts["dev"].values()) != [1033, 208, 18, 2]:
        out.append(u"開発の類の数が封と違う")
    return out


# ---------------------------------------------------------------- 変異(script)
#: (名前, script の中の字 old, new, 赤になるはずの検査の名前の並び)。old は script に 1 回だけ在る字
MUTANTS = (
    (u"M01 封の commit の定数を替える", u'SEAL_COMMIT = "7bb4fa24"', u'SEAL_COMMIT = "7bb4fa25"', ("seal",)),
    (u"M02 便 XG1 の script の sha256 の留めを替える", u'XG1_SCRIPT_SHA256 = "24159344', u'XG1_SCRIPT_SHA256 = "34159344', ("seal", "xg1")),
    (u"M03 指示文の 1 字を替える(でください → てください)", u"渡した字だけで判断し、推測で埋めないでください。", u"渡した字だけで判断し、推測で埋めてください。", ("seal", "prompt")),
    (u"M04 指示文の「答え: 0」の説明の字を替える", u"「答え: 0」と書いてください", u"「答え: 9」と書いてください", ("seal", "prompt")),
    (u"M05 指示文の置き換える所を 1 つ落とす({PREV})", u'PLACEHOLDERS = (u"{HEADING}", u"{PREV}", u"{ROW}", u"{CANDS}")', u'PLACEHOLDERS = (u"{HEADING}", u"{ROW}", u"{CANDS}")', ("seal", "prompt")),
    (u"M06 見出しが無いときの字を空にする", u'values = {u"{HEADING}": NO_HEADING if heading is None else heading,', u'values = {u"{HEADING}": u"" if heading is None else heading,', ("prompt",)),
    (u"M07 見出しが空の字のとき「(なし)」にする", u'values = {u"{HEADING}": NO_HEADING if heading is None else heading,', u'values = {u"{HEADING}": NO_HEADING if not heading else heading,', ("prompt",)),
    (u"M08 前の行が無いとき空にする", u'u"{PREV}": PREV_SEP.join(prev) if prev else NO_PREV,', u'u"{PREV}": PREV_SEP.join(prev),', ("prompt",)),
    (u"M09 前の行の区切りを替える", u'PREV_SEP = u" / "', u'PREV_SEP = u" | "', ("prompt",)),
    (u"M10 候補の番号を 0 から振る", u'u"{CANDS}": u"\\n".join(u"%d. %s" % (i + 1, c) for i, c in enumerate(cands))}', u'u"{CANDS}": u"\\n".join(u"%d. %s" % (i, c) for i, c in enumerate(cands))}', ("prompt",)),
    (u"M11 置き換えを 1 回の走査でなく順に replace", u"    return _PH_RE.sub(lambda m: values[m.group(0)], PROMPT_TEMPLATE)",
     u"    return PROMPT_TEMPLATE.replace(u\"{HEADING}\", values[u\"{HEADING}\"]).replace(u\"{PREV}\", values[u\"{PREV}\"]).replace(u\"{ROW}\", values[u\"{ROW}\"]).replace(u\"{CANDS}\", values[u\"{CANDS}\"])", ("prompt",)),
    (u"M12 副の席も昇順にする", u'SEAT_REVERSE = {"claude-sonnet-5-5": False, "claude-haiku-5-5": True}', u'SEAT_REVERSE = {"claude-sonnet-5-5": False, "claude-haiku-5-5": False}', ("seal", "prompt", "answers")),
    (u"M13 主の席を降順にする", u'SEAT_REVERSE = {"claude-sonnet-5-5": False, "claude-haiku-5-5": True}', u'SEAT_REVERSE = {"claude-sonnet-5-5": True, "claude-haiku-5-5": False}', ("seal", "prompt", "answers")),
    (u"M14 候補を昇順に並べずに渡された並びのまま", u"        cl = sorted(r[\"cands\"], reverse=SEAT_REVERSE[seat])", u"        cl = list(r[\"cands\"]) if not SEAT_REVERSE[seat] else list(reversed(r[\"cands\"]))", ("prompt",)),
    (u"M15 番号を要素の名に戻すとき主の席の並びで戻す", u'    return it["cands"][seat][num - 1]', u'    return it["cands"][SEATS[0]][num - 1]', ("label", "answers")),
    (u"M16 2 席の一致を番号で比べる", u"    return pick_of(it, SEATS[0], nm) == pick_of(it, SEATS[1], ns)", u"    return nm == ns", ("label", "answers")),
    (u"M17 2 席の一致で答えの 0 同士を一致に数える", u"    if not nm or not ns:\n        return False\n", u"    if nm is None or ns is None:\n        return False\n", ("label",)),
    (u"M18 札の 0 を誤に数える", u"    if num == 0:\n        return L_ZERO\n", u"    if num == 0:\n        return L_BAD\n", ("label", "answers")),
    (u"M19 札の答えなしを 0 に数える", u"    if num is None:\n        return NO_ANSWER\n    if num == 0:", u"    if num is None:\n        return L_ZERO\n    if num == 0:", ("label", "answers")),
    (u"M20 札の正を要素の名でなく番号 1 で決める", u'    return L_OK if pick_of(it, seat, num) == it["E"] else L_BAD', u'    return L_OK if num == 1 else L_BAD', ("label", "answers")),
    (u"M21 答えを読むとき NFKC をかけない", u'    t = unicodedata.normalize("NFKC", text)', u"    t = text", ("read",)),
    (u"M22 答えの範囲の上限を候補の数 + 1 にする", u"    return v if 0 <= v <= ncand else None", u"    return v if 0 <= v <= ncand + 1 else None", ("read",)),
    (u"M23 答えの範囲の下限を 1 にする(0 を読まない)", u"    return v if 0 <= v <= ncand else None", u"    return v if 1 <= v <= ncand else None", ("read",)),
    (u"M24 答えの最初でなく最後の「答え」を読む", u'    i = t.find(u"答え")', u'    i = t.rfind(u"答え")', ("read",)),
    (u"M25 stop_reason を見ない", u'    if stop_reason != "end_turn" or not isinstance(text, str) or not text:', u"    if not isinstance(text, str) or not text:", ("read",)),
    (u"M26 「答え」の後ろの : を要らなくする", u'_ANS_RE = re.compile(r"\\s*:\\s*([0-9]+)")', u'_ANS_RE = re.compile(r"\\s*:?\\s*([0-9]+)")', ("read",)),
    (u"M27 席を替える(副)", u'SEATS = ("claude-sonnet-5-5", "claude-haiku-5-5")', u'SEATS = ("claude-sonnet-5-5", "claude-haiku-5-4")', ("seal", "answers")),
    (u"M28 席の札を入れ替える", u'SEAT_TAG = collections.OrderedDict([("claude-sonnet-5-5", u"主"), ("claude-haiku-5-5", u"副")])', u'SEAT_TAG = collections.OrderedDict([("claude-sonnet-5-5", u"副"), ("claude-haiku-5-5", u"主")])', ("seal", "answers")),
    (u"M29 max_tokens を替える", u"MAX_TOKENS = 100\n", u"MAX_TOKENS = 200\n", ("seal", "call", "label")),
    (u"M30 temperature の定数を替える", u"TEMPERATURE = None ", u"TEMPERATURE = 0 ", ("seal",)),
    (u"M31 body に temperature を戻す", u'"max_tokens": MAX_TOKENS, "thinking": THINKING[model],', u'"max_tokens": MAX_TOKENS, "temperature": 0, "thinking": THINKING[model],', ("call",)),
    (u"M32 思考の指定(主)を替える", u'THINKING = {"claude-sonnet-5-5": {"type": "between_tools"}', u'THINKING = {"claude-sonnet-5-5": {"type": "disabled"}', ("seal", "call")),
    (u"M33 上限を替える", u"COST_CAP_USD = 5.0", u"COST_CAP_USD = 6.0", ("seal",)),
    (u"M34 出力の単価を替える", u"PRICE_OUT = 25.0", u"PRICE_OUT = 15.0", ("seal", "label")),
    (u"M35 入力の単価を替える", u"PRICE_IN = 5.0 ", u"PRICE_IN = 3.0 ", ("seal", "label")),
    (u"M36 行の数の定数を替える", u"EXPECT_ROWS = 394\n", u"EXPECT_ROWS = 393\n", ("seal",)),
    (u"M37 8 行に 1 行の間隔を替える", u"PICK_STEP = 8 ", u"PICK_STEP = 9 ", ("seal", "items")),
    (u"M38 前の行の数を替える", u"PREV_N = 12 ", u"PREV_N = 11 ", ("seal", "prev")),
    (u"M39 類の数の封の字を替える(本番の類 A)", u'("A", 2603)', u'("A", 2602)', ("seal", "items")),
    (u"M40 類 W の全部でなく先頭だけ選ぶ", u'    prod_w = [r for r in ordered if r["group"] == "prod" and r["cls"] == "W"]', u'    prod_w = [r for r in ordered if r["group"] == "prod" and r["cls"] == "W"][:1]', ("items",)),
    (u"M41 類 A の選びを割り切れる行でなく余りが 1 の行にする", u"    picked_a = [r for i, r in enumerate(prod_a) if i % step == 0]", u"    picked_a = [r for i, r in enumerate(prod_a) if i % step == 1]", ("items",)),
    (u"M42 試しの行を開発でなく本番の類 A の頭にする", u'    dev_a = [r for r in ordered if r["group"] == "dev" and r["cls"] == "A"]', u'    dev_a = [r for r in ordered if r["group"] == "prod" and r["cls"] == "A"]', ("items",)),
    (u"M43 行の順を書類・file・行でなく行の位置だけにする", u'    ordered = sorted(rows, key=lambda r: r["ord"])', u'    ordered = sorted(rows, key=lambda r: r["ord"][2])', ("items",)),
    (u"M44 本番の行の最後の並べ直しを外す(類 A の後に類 W)", u'    prod_sel = sorted(picked_a + prod_w, key=lambda r: r["ord"])', u"    prod_sel = picked_a + prod_w", ("items",)),
    (u"M45 類の数の確かめを外す", u"        if list(got.values()) != list(want.values()):", u"        if False:", ("items",)),
    (u"M46 行の数の確かめを外す", u"    if len(picked_a) != want_a or len(prod_w) != want_w or len(picked_a) + len(prod_w) != want_rows:", u"    if False:", ("items",)),
    (u"M47 試しの行の数の確かめを外す", u"    if len(trial_sel) != want_trial:", u"    if False:", ("items",)),
    (u"M48 L-P の通す規則 P1 を答え 0 も通す", u'    return v["m"] in (L_OK, L_BAD)', u'    return v["m"] in (L_OK, L_BAD, L_ZERO)', ("answers",)),
    (u"M49 P2 の通す規則を主の席だけにする", u'def p2_pass(v):\n    return v["same"]', u'def p2_pass(v):\n    return v["m"] in (L_OK, L_BAD)', ("answers",)),
    (u"M50 誤って通した数を通した行の全部にする", u'(u"P2(2 席の一致)", rule_cell(vs, p2_pass, p1_wrong))', u'(u"P2(2 席の一致)", rule_cell(vs, p2_pass, lambda v: True))', ("answers",)),
    (u"M51 止めすぎを副の席の正で数える", u'(u"止めた行のうち主の席が正", sum(1 for v in st if v["m"] == L_OK))', u'(u"止めた行のうち主の席が正", sum(1 for v in st if v["s"] == L_OK))', ("answers",)),
    (u"M52 主の席が誤の行のうち P2 が止めた数を通した数で数える", u'sum(1 for v in vs if v["m"] == L_BAD and not v["same"])', u'sum(1 for v in vs if v["m"] == L_BAD and v["same"])', ("answers",)),
    (u"M53 類 A の分母に類 W を混ぜる", u'    a = [v for v in views if v["cls"] == "A"]\n    w = [v for v in views if v["cls"] == "W"]\n    out = od()\n    out[u"類 A"] = cell(a)', u'    a = [v for v in views if v["cls"] == "A"]\n    w = [v for v in views if v["cls"] == "W"]\n    out = od()\n    out[u"類 A"] = cell(views)', ("answers",)),
    (u"M54 帯の境(7 以上)を 6 以上にする", u'(u"候補 7 以上", lambda n: n >= 7)', u'(u"候補 7 以上", lambda n: n >= 6)', ("label",)),
    (u"M55 帯の境(3〜6)を 3〜5 にする", u'(u"候補 3〜6", lambda n: 3 <= n <= 6)', u'(u"候補 3〜6", lambda n: 3 <= n <= 5)', ("label",)),
    (u"M56 でたらめの期待を 1 ÷ 候補の数でなく 1 ÷ (候補の数 + 1) にする", u'round(sum(1.0 / v["n"] for v in a), 4)', u'round(sum(1.0 / (v["n"] + 1) for v in a), 4)', ("answers",)),
    (u"M57 昇順の頭の数を降順の頭で数える", u'it["cands"][m][0] == it["E"], it["sha"][m]', u'it["cands"][s][0] == it["E"], it["sha"][m]', ("answers",)),
    (u"M58 XD0-8 の種類の在る行に種類なしを混ぜる", u'    wk = [v for v in a if v["kind"] in KINDS_WITH]', u'    wk = [v for v in a if v["kind"] != u"株主資本等変動"]', ("answers",)),
    (u"M59 XD0-9 の差の向きを逆にする", u'(u"差(主 − 副)", ok(a) - s_ok(a))', u'(u"差(主 − 副)", s_ok(a) - ok(a))', ("answers",)),
    (u"M60 XD0-11 に試しの額を入れない", u"    usd_all = usd_of(trial_call_rows, call_rows)", u"    usd_all = usd_of([], call_rows)", ("answers",)),
    (u"M61 使った額に試しの額を入れない", u'(u"使った額 USD(試しを含む)", round(state_cost(t_state) + state_cost(p_state), 6))', u'(u"使った額 USD(試しを含む)", round(state_cost(p_state), 6))', ("answers", "c400")),
    (u"M62 USD の見積りの出力を max_tokens の半分にする", u"    return (prompt_chars * PRICE_IN + MAX_TOKENS * PRICE_OUT) / 1e6", u"    return (prompt_chars * PRICE_IN + MAX_TOKENS * PRICE_OUT / 2) / 1e6", ("label",)),
    (u"M63 走っている間の上限の比較を外す", u'        if cum + meter["extra"] + est > cap:', u"        if False:", ("cap",)),
    (u"M64 走らせる前の見積りの比較を外す", u"    if base + est > cap:", u"    if False:", ("cap",)),
    (u"M65 走らせる前の見積りに試しの額(他の置き場の使った額)を入れない", u"    problem = plan_problem(other_cost + state_cost(state), est + other_est, n_pending + other_n, cap, say)", u"    problem = plan_problem(state_cost(state), est + other_est, n_pending + other_n, cap, say)", ("cap",)),
    (u"M66 走らせる前の見積りに他の置き場の残りの見積りを入れない", u"    problem = plan_problem(other_cost + state_cost(state), est + other_est, n_pending + other_n, cap, say)", u"    problem = plan_problem(other_cost + state_cost(state), est, n_pending, cap, say)", ("cap",)),
    (u"M67 走っている間の累計に他の置き場の額を入れない", u"do_call(prompt, seat, key, transport, sleep, other_cost + state_cost(state), cap, i, attempt, this_sha, it[\"ncand\"])", u"do_call(prompt, seat, key, transport, sleep, state_cost(state), cap, i, attempt, this_sha, it[\"ncand\"])", ("cap",)),
    (u"M68 見積りにやり直しを入れる(1 回目の後の席も数える)", u"            if seat_answer(state, i, seat) is None and not seat_attempts(state, i, seat):\n                total", u"            if seat_answer(state, i, seat) is None:\n                total", ("cap",)),
    (u"M69 返らなかった呼び出しを見積りの額で数えない", u'            meter["extra"] += est', u'            meter["extra"] += 0', ("retry", "cap")),
    (u"M70 中断した呼び出しを見積りの額で数えない", u'(u"est_counted_usd", f[u"est_usd"]), (u"cost_usd", f[u"est_usd"]),', u'(u"est_counted_usd", 0.0), (u"cost_usd", 0.0),', ("resume",)),
    (u"M71 呼ぶ前の in_flight を残さない", u'                state[u"in_flight"] = od([(u"row", i)', u'                state[u"in_flight_x"] = od([(u"row", i)', ("resume",)),
    (u"M72 試しが 1 回で止まらない", u"    max_attempts = 1 if one_attempt else MAX_ANSWER_ATTEMPTS", u"    max_attempts = MAX_ANSWER_ATTEMPTS", ("resume",)),
    (u"M73 済んだ(行, 席)を呼び直す", u"                if seat_answer(state, i, seat) is not None or len(att) >= max_attempts:", u"                if len(att) >= max_attempts:", ("resume", "answers", "cap")),
    (u"M74 答えの 0 を「読めた」に数えず呼び直す", u'        if c[u"answer"] is not None:\n            return c[u"answer"]\n    return None', u'        if c[u"answer"]:\n            return c[u"answer"]\n    return None', ("answers", "resume")),
    (u"M75 やり直しを 0 回にする", u"MAX_ANSWER_ATTEMPTS = 2 ", u"MAX_ANSWER_ATTEMPTS = 1 ", ("seal", "answers", "retry")),
    (u"M76 HTTP 400 で止めない", u"STOP_HTTP = (400, 401, 403)", u"STOP_HTTP = (401, 403)", ("seal", "retry")),
    (u"M77 試しが済んでいなくても本番を呼べる", u"        if not t_exists or not trial_done(t_items, t_state):", u"        if False:", ("resume",)),
    (u"M78 試しの済みを答えが読めたかで決める", u"    return state is not None and all(seat_attempts(state, i, seat) for i in range(len(items)) for seat in SEATS)", u"    return state is not None and all(seat_answer(state, i, seat) is not None for i in range(len(items)) for seat in SEATS)", ("resume",)),
    (u"M79 試しをやり直せる(答えが返った置き場でも)", u'            if any(c[u"answer"] is not None or c[u"http_status"] == 200 for c in prev[u"calls"]):', u"            if False:", ("resume", "c400")),
    (u"M80 --resume なしで続けられる", u"        if p_exists and not resume:", u"        if False:", ("resume",)),
    (u"M81 置き場が repo の中でも止めない", u"    if inside_repo(t_dir) or inside_repo(p_dir):", u"    if False:", ("resume",)),
    (u"M82 前の走りの 400 を答えの回に数えたまま", u"    if resolve_in_flight(state) | bool(retire_config_failures(state)):", u"    if resolve_in_flight(state):", ("c400",)),
    (u"M83 400 の本文の鍵の検査を外す", u"    if GEN.key_leaks(m, key, False):", u"    if False:", ("c400",)),
    (u"M84 400 の本文を残さない", u'        item[u"error_message"] = error_message_of(body, key)', u'        item[u"error_message"] = None', ("c400",)),
    (u"M85 途中の答えに鍵を書く", u'(u"script_sha256", script_sha[:16])', u'(u"script_sha256", key)', ("retry", "leak")),
    (u"M86 記録の漏れの検査を呼ばない", u"    N.check_clean(rec, scan, secret)", u"    pass", ("leak",)),
    (u"M87 記録の鍵の検査を呼ばない", u"    if GEN.key_leaks(scan, key_value, False):", u"    if False:", ("leak",)),
    (u"M88 記録に試しの行を本番の行に混ぜる", u"    rows = build_rows(items, p_state)\n    call_rows", u"    rows = build_rows(t_items + items, p_state)\n    call_rows", ("answers",)),
    (u"M89 block の type の並びを dict の key に戻す", u"pairs_of(c[K_BLOCKS] for c in real if c[K_BLOCKS] is not None)", u"od(sorted(collections.Counter(c[K_BLOCKS] for c in real if c[K_BLOCKS] is not None).items()))", ("real", "answers")),
    (u"M90 stop_reason の種類を dict の key に戻す", u"pairs_of(str(c[K_STOP]) for c in real)", u"od(sorted(collections.Counter(str(c[K_STOP]) for c in real).items()))", ("real", "answers")),
    (u"M91 記録の呼び出しの形に temperature を書く", u'(u"temperature", u"送らない")', u'(u"temperature", 0)', ("answers",)),
    (u"M92 記録に席の並びの向きを書かない(主の席を降順と書く)", u'(u"候補の並び", u"昇順")', u'(u"候補の並び", u"降順")', ("answers",)),
    (u"M93 dry-run が鍵を読む", u"    col = collected if collected is not None else collect_all(root=root, say=say)\n    t_items, p_items, wire = col[\"trial\"]", u"    get_key()\n    col = collected if collected is not None else collect_all(root=root, say=say)\n    t_items, p_items, wire = col[\"trial\"]", ("dry", "import")),
    (u"M94 dry-run の作り物の transport の検査を外す", u"    checks = self_test(say)", u'    checks = od([(u"x", True)])', ("dry",)),
    (u"M95 dry-run の見積りを 1 席分だけにする", u"    est_one = sum(estimate_usd(len(it[\"prompt\"][s])) for it in allit for s in SEATS)", u"    est_one = sum(estimate_usd(len(it[\"prompt\"][SEATS[0]])) for it in allit)", ("dry",)),
    (u"M96 --check が指示文の sha256 の組み直しを照らさない", u"    if dumps(build_rows(col[\"prod\"], p_state)) != dumps(rows) or dumps(build_rows(col[\"trial\"], t_state)) != dumps(rec[u\"試しの行\"]):", u"    if False:", ("check",)),
    (u"M97 --check が行から数を作り直して照らさない", u"        if dumps(rec[k]) != dumps(v):\n            raise Stop(u\"**記録の欄が行・呼び出しの欄から作り直した数と違う", u"        if False:\n            raise Stop(u\"**記録の欄が行・呼び出しの欄から作り直した数と違う", ("check",)),
    (u"M98 --check が置き場の呼び出しの欄を照らさない", u"    if dumps(build_call_rows(p_state)) != dumps(call_rows) or dumps(build_call_rows(t_state)) != dumps(trial_calls):", u"    if False:", ("check",)),
    (u"M99 --check が置き場の返った text を確かめない", u"    check_state(col[\"prod\"], p_state, p_dir)\n    if dumps", u"    if dumps", ("check",)),
    (u"M100 --check が script の sha256・配線の確認を照らさない", u"    if rec[u\"この script の sha256\"] != sha256_file(os.path.abspath(__file__)) or dumps(rec[K_WIRE]) != dumps(col[\"wire\"]) or rec[u\"便 XG1 の script の sha256\"] != XG1_SCRIPT_SHA256:", u"    if False:", ("check",)),
    (u"M101 便 XG1 の script の sha256 の確かめを外す", u"    if not os.path.isfile(p) or sha256_file(p) != XG1_SCRIPT_SHA256:", u"    if False:", ("xg1",)),
    (u"M102 便 XG1 の file_rows を写す(自前の関数を足す)", u"def read_docs(", u"def file_rows(text):\n    return []\n\n\ndef read_docs(", ("no_copy",)),
    (u"M103 前の行を空の字も数える", u"    if lab:\n        nonempty.append(lab)", u"    nonempty.append(lab)", ("prev",)),
    (u"M105 漏れの検査の材料に前の行の字を入れない", u'        labels.update(it["prev"])\n', u"", ("leak",)),
    (u"M106 漏れの検査の材料に見出しの字を入れない", u'            heads.add(N.norm_label(it["heading"]))', u"            pass", ("leak",)),
    (u"M107 漏れの検査の材料に候補の要素の名を入れない", u'        elems.update(it["cands"][SEATS[0]])\n', u"", ("leak",)),
    (u"M108 途中の答えの指示文の sha256 を照らさない", u'        if c[u"prompt_sha256"] != items[i]["sha"][c[u"seat"]]:', u"        if False:", ("resume",)),
    (u"M109 途中の答えの返った text の sha256 を照らさない", u'                if sha256_text(fh.read()) != c[u"reply_sha256"]:', u"                if False:", ("resume",)),
    (u"M110 途中の答えの返った text の file の有無を見ない", u'            if not os.path.exists(p):\n                raise Stop(u"**途中の答えの返った text が置き場に無い', u'            if False:\n                raise Stop(u"**途中の答えの返った text が置き場に無い', ("resume",)),
    (u"M104 前の行を先頭から 12 個にする", u"    return list(nonempty[-PREV_N:])", u"    return list(nonempty[:PREV_N])", ("prev",)),
)


def xg1_check(name_mod, src):
    return xg1_pin_problems(name_mod)


CHECKS = {u"seal": seal_problems, u"pred": pred_problems, u"prompt": prompt_problems, u"read": read_problems, u"label": label_problems, u"items": items_problems, u"prev": prev_label_problems,
          u"answers": answers_problems, u"trial": trial_not_in_prod_problems, u"retry": retry_problems, u"cap": cap_problems, u"resume": resume_problems, u"c400": c400_problems,
          u"real": realshape_problems, u"leak": leak_problems, u"call": call_problems, u"dry": dry_problems, u"check": check_cmd_problems}


def check_by_name(name, mod, src):
    if name in CHECKS:
        return CHECKS[name](mod)
    if name == u"import":
        return import_problems(src)
    if name == u"no_copy":
        return no_copy_problems(src)
    if name == u"xg1":
        return xg1_mutant_problems(mod)
    raise AssertionError(name)


def xg1_mutant_problems(mod):
    u"""便 XG1 の script の sha256 の確かめ(``collect_all``)が、違う字の script で止まる(作り物の root に 1 byte 違う複製を置く)。"""
    out = []
    tmp = Temp()
    try:
        d = os.path.join(tmp.d, "measure")
        os.makedirs(d)
        with open(os.path.join(ROOT, XG1_SCRIPT_REL), "rb") as fh:
            data = fh.read()
        with open(os.path.join(d, os.path.basename(XG1_SCRIPT_REL)), "wb") as fh:
            fh.write(data + b" ")
        if stops(mod, mod.collect_all, tmp.d) is not True:
            out.append(u"便 XG1 の script が 1 byte 違うのに collect_all が止まらない")
    finally:
        tmp.close()
    out.extend(seal_problems(mod) if mod.XG1_SCRIPT_SHA256 != XG1_SCRIPT_SHA else [])
    return out


def run_mutants():
    base = read(SCRIPT_REL)
    out = []
    for name, old, new, checks in MUTANTS:
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


# ================================================================ 試験
class SealTextTest(unittest.TestCase):
    def test_a_1_the_script_constants_equal_the_seal(self):
        self.assertEqual([], seal_problems())
        self.assertEqual([], pred_problems())

    def test_a_2_the_seal_file_is_the_sealed_commit_and_unchanged(self):
        self.assertEqual([], seal_history_problems())

    def test_a_3_a_changed_seal_character_turns_the_comparison_red(self):
        seal = seal_text()
        self.assertEqual([], seal_problems(seal=seal))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"答えは 1 行だけ", u"答えは 2 行だけ")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"`max_tokens` 100", u"`max_tokens` 101")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"**上限**: 5 USD", u"**上限**: 6 USD")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"主の席 = `claude-sonnet-5-5`", u"主の席 = `claude-sonnet-5-4`")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"頭の 5 行", u"頭の 6 行")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"2603 行のうち 326 行", u"2603 行のうち 325 行")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"番号が 8 で割り切れる", u"番号が 9 で割り切れる")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"後ろから 12 個", u"後ろから 11 個")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"開発で U 1033", u"開発で U 1034")))
        self.assertNotEqual([], pred_problems(seal=seal.replace(u"245 行以上 310 行以下", u"245 行以上 311 行以下")))
        self.assertNotEqual([], pred_problems(seal=seal.replace(u"| XD0-7 |", u"| XD0-77 |")))

    def test_a_4_the_seal_has_two_blocks_and_the_values_are_read_from_it(self):
        seal = seal_text()
        v = seal_values(seal)
        blk, example = seal_blocks(seal)
        self.assertEqual(("claude-sonnet-5-5", "claude-haiku-5-5"), v["seats"])
        self.assertEqual((100, {"type": "between_tools"}, {"type": "disabled"}), v["shape"])
        self.assertEqual((5, (5, 25), (394, 788, 5, 10)), (v["cap"], v["price"], v["calls"]))
        self.assertEqual((326, 68, 394, 5, 8, 12), (v["a_rows"], v["w_rows"], v["rows"], v["trial_rows"], v["step"], v["prev_n"]))
        self.assertEqual((1033, 208, 18, 2, 12444, 2603, 387, 68), v["wire"])
        self.assertTrue(blk.startswith(u"次は、日本の上場企業の有価証券報告書の中の表の 1 つの行です。"))
        self.assertTrue(example.startswith(u"表の見出し: 損益計算書\nこの行より前の行(上から順): 営業収益 / 営業費用"))
        self.assertEqual(1, seal.count(u"```\n次は、日本の上場企業"))


class PriorTest(unittest.TestCase):
    def test_b_1_the_xg1_script_is_pinned_unchanged_and_called_not_copied(self):
        self.assertEqual([], xg1_pin_problems())
        self.assertEqual([], no_copy_problems())

    def test_b_2_a_changed_xg1_script_or_a_copied_function_turns_it_red(self):
        self.assertNotEqual([], no_copy_problems(read(SCRIPT_REL) + u"\n\ndef kind_of(h):\n    return None\n"))
        self.assertNotEqual([], no_copy_problems(read(SCRIPT_REL).replace(u"N.file_rows(text)", u"[]")))


class EngineTest(unittest.TestCase):
    def test_c_1_the_engine_is_zero_lines_from_the_seal_commit(self):
        self.assertEqual([], engine_zero_problems())

    def test_c_2_a_made_up_repo_with_an_engine_change_is_red(self):
        r = PR.Repo()
        r.put(SEAL_REL)
        r.put("adapters/xbrl/instance.py", text=u"")
        seal = r.commit(SEAL_REL, "adapters/xbrl/instance.py")
        r.put("measure/s.py")
        r.commit("measure/s.py")
        self.assertEqual([], engine_zero_problems_in(r.d, seal))
        r.put("adapters/xbrl/instance.py", text=u"a\n")
        r.commit("adapters/xbrl/instance.py")
        self.assertNotEqual([], engine_zero_problems_in(r.d, seal))
        r2 = PR.Repo()
        r2.put(SEAL_REL)
        s2 = r2.commit(SEAL_REL)
        r2.put("core/py/audit_core/x.py")
        r2.commit("core/py/audit_core/x.py")
        self.assertNotEqual([], engine_zero_problems_in(r2.d, s2))


def engine_zero_problems_in(root, seal):
    rc, txt = PR.git_in(root, "diff", "--name-only", seal, "--", PREFIX + "adapters", PREFIX + "core")
    return [ln for ln in txt.splitlines() if ln.strip()]


class OrderTest(unittest.TestCase):
    def test_d_1_the_real_history_has_the_seal_before_the_script_and_the_gate(self):
        u"""script・門のどちらかが未 commit なら赤(足した commit が無い。skip にしない)。両方 commit された後で初めて緑。"""
        self.assertEqual([], order_of())

    def test_d_2_good_order_is_green_and_bad_orders_are_red(self):
        r = PR.Repo()
        r.put("docs/seal.md")
        s = r.commit("docs/seal.md")
        others = ["measure/s.py", "tests/g.py"]
        for f in others:
            r.put(f)
        r.commit(*others)
        self.assertEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], [], others))
        self.assertNotEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", "0000000", [], others))
        r.put("tests/new.py")
        self.assertNotEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], [], others + ["tests/new.py"]))
        r2 = PR.Repo()
        r2.put("measure/s.py")
        r2.commit("measure/s.py")
        r2.put("docs/seal.md")
        s2 = r2.commit("docs/seal.md")
        self.assertNotEqual([], PR.order_problems(r2.d, PREFIX, "docs/seal.md", s2[:7], [], ["measure/s.py"]))

    def test_d_3_the_order_check_lists_the_script_and_the_gate_and_not_the_record(self):
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, rel)) for rel in ORDER_FILES))
        self.assertNotIn(RECORD_REL, ORDER_FILES)


class PureTest(unittest.TestCase):
    def test_e_1_the_prompt_is_the_seal_block_and_reproduces_the_seal_example(self):
        self.assertEqual([], prompt_problems())

    def test_e_2_the_answer_reading_follows_the_seal(self):
        self.assertEqual([], read_problems())

    def test_e_3_labels_number_to_element_and_the_two_seat_match(self):
        self.assertEqual([], label_problems())

    def test_e_4_the_previous_rows_are_the_last_twelve_non_empty_labels(self):
        self.assertEqual([], prev_label_problems())

    def test_e_5_the_rows_are_chosen_ordered_and_the_wiring_checks_stop(self):
        self.assertEqual([], items_problems())


class PipelineTest(unittest.TestCase):
    def test_f_1_calls_reading_mapping_labels_p1_p2_and_counting_agree_with_the_hand_computation(self):
        self.assertEqual([], answers_problems())

    def test_f_2_the_trial_is_kept_out_of_the_production_numbers(self):
        self.assertEqual([], trial_not_in_prod_problems())

    def test_f_3_retries_unreturned_calls_and_http_400(self):
        self.assertEqual([], retry_problems())

    def test_f_4_the_cap_stops_before_and_while_running(self):
        self.assertEqual([], cap_problems())

    def test_f_5_trial_then_production_resume_and_interrupted_calls(self):
        self.assertEqual([], resume_problems())

    def test_f_6_the_key_never_reaches_a_file_a_record_or_an_exception(self):
        self.assertEqual([], leak_problems())

    def test_f_7_the_request_body_has_the_sealed_shape_without_any_network(self):
        self.assertEqual([], call_problems())

    def test_f_8_dry_run_reads_no_key_and_sends_nothing(self):
        self.assertEqual([], dry_problems())

    def test_f_9_check_rebuilds_the_numbers_and_the_prompt_hashes(self):
        self.assertEqual([], check_cmd_problems())

    def test_f_10_http_400_message_is_kept_outside_the_record_and_the_trial_can_be_rerun(self):
        self.assertEqual([], c400_problems())

    def test_f_11_a_real_shaped_reply_does_not_put_api_words_into_record_keys(self):
        self.assertEqual([], realshape_problems())

    def test_f_12_the_zero_cost_functions_have_no_real_call_path(self):
        saved = os.environ.pop(MS.KEY_ENV, None)
        try:
            def no_net(*a, **k):
                raise AssertionError(u"通信した")
            with patched(urllib.request, urlopen=no_net):
                self.assertEqual([], dry_problems())
                self.assertEqual([], check_cmd_problems())
        finally:
            if saved is not None:
                os.environ[MS.KEY_ENV] = saved


class RecordPresenceTest(unittest.TestCase):
    def test_g_1_the_record_checks_run_only_when_the_record_exists(self):
        u"""記録が無い間は、記録の検査(形・書かないもの・行から数の作り直し)は結果の門に置く(ここは None = 「無い」を返す分岐を明示)。記録が在れば全部見る。"""
        r = record_problems()
        if not os.path.exists(os.path.join(ROOT, RECORD_REL)):
            self.assertIsNone(r)
        else:
            self.assertEqual([], r)


class MaterialTest(unittest.TestCase):
    def test_k_1_the_real_material_gives_the_sealed_counts_and_reproduces_the_example(self):
        if not have_material():
            self.skipTest(u"材料(書類・タクソノミ)が無い環境。配線の確認は材料の在る環境で走る")
        self.assertEqual([], material_problems())


class WiringTest(unittest.TestCase):
    def test_h_1_the_script_imports_only_the_allowed_modules_and_reads_the_key_in_one_place(self):
        self.assertEqual([], import_problems())

    def test_h_2_the_boundary_import_list_is_not_widened(self):
        p = os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py")
        with open(p, encoding="utf-8") as fh:
            self.assertNotIn(u"ai_tag_pick", fh.read())

    def test_h_3_the_gate_does_not_use_the_reserved_names_and_has_no_docid(self):
        self.assertEqual([], reserved_problems())
        self.assertIsNone(DOCID_RE.search(read(GATE_REL)))
        self.assertIsNone(DOCID_RE.search(read(SCRIPT_REL)))

    def test_h_4_the_reserved_name_check_sees_a_planted_name(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("ENGINE_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rel="g.py", base=d))
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("XD0_NOTES = 1\n")
            self.assertEqual([], reserved_problems(rel="g.py", base=d))

    def test_h_5_the_script_leaves_sys_modules_as_it_found_them(self):
        u"""前の便の script を読んでも、読み込みの前に居た名前を上書きしたまま残さない(門を 2 通りの順で走らせても赤くならない)。"""
        before = dict(sys.modules)
        mod = load_module(SCRIPT_REL, "ai_tag_pick_script_for_sysmodules_check")
        changed = [k for k, v in before.items() if sys.modules.get(k) is not v]
        self.assertEqual([], changed)
        self.assertIn("ai_tag_pick_script_for_sysmodules_check", sys.modules)
        del mod

    def test_h_6_the_import_check_sees_planted_violations(self):
        base = read(SCRIPT_REL)
        self.assertNotEqual([], import_problems(base + u"\nimport socket\n"))
        self.assertNotEqual([], import_problems(base + u"\nimport subprocess\n"))
        self.assertNotEqual([], import_problems(base + u"\nX = os.environ.get('A')\n"))
        self.assertNotEqual([], import_problems(base.replace(u"def self_test(say):\n", u"def self_test(say):\n    get_key()\n")))
        self.assertNotEqual([], import_problems(base.replace(u"def check(root=ROOT", u"def check_x(root=ROOT")))

    def test_h_7_the_script_has_no_function_name_the_inject_harness_review_looks_for(self):
        src = read(SCRIPT_REL)
        for crit in (u"run_doc" + u"(", u"mutate" + u"(", u"inject" + u"(", u"apply_edits" + u"("):
            self.assertNotIn(crit, src)


class MutantTest(unittest.TestCase):
    def test_j_1_every_mutant_turns_its_checks_red_and_the_files_are_unchanged(self):
        before = (sha_of(SCRIPT_REL), sha_or_none(RECORD_REL), sha_of(XG1_SCRIPT_REL))
        modules_before = dict(sys.modules)
        results = run_mutants()
        after = (sha_of(SCRIPT_REL), sha_or_none(RECORD_REL), sha_of(XG1_SCRIPT_REL))
        self.assertEqual(before, after)
        self.assertEqual([], [k for k, v in modules_before.items() if sys.modules.get(k) is not v])
        silent = [(n, c) for n, res, _w in results for c, red in res if not red]
        self.assertEqual([], silent)
        self.assertEqual(len(MUTANTS), len(results))

    def test_j_2_the_unmutated_script_is_green_on_every_check(self):
        base = read(SCRIPT_REL)
        mod = load_source(base)
        for name in (u"seal", u"pred", u"prompt", u"read", u"label", u"items", u"prev", u"answers", u"trial", u"retry", u"cap", u"resume", u"c400", u"real", u"leak", u"call", u"dry", u"check", u"import", u"no_copy"):
            self.assertEqual([], check_by_name(name, mod, base), name)
        self.assertEqual([], xg1_mutant_problems(mod))


if __name__ == "__main__":
    unittest.main()
