# -*- coding: utf-8 -*-
"""封 docs/XBRL_LLM_EXTRACT_SEAL_2026-11-19.md(LX ― 文の字だけを読んだ LLM の席の答え(範囲・性質)で結んだ行を止めると、語の表の規則(便 SC・便 PA の段 2)と比べて、取り違えをどれだけ止め、正しい結びをどれだけ減らすか)の封の門。封 §7。

**この門は鍵を読まず、1 回も通信しない**(``urllib.request.urlopen`` を差し替えた中でだけ送る body を見る)。材料の本も読まない(作り物の本)。

**この門が縛るもの**

1. 封の字: 封の commit(198961e6)・path・指示文(§2-2 の code block と 1 字ずつ)・席の名・max_tokens・temperature・思考の指定・上限・単価・回数・行の数 421・試しの行数・答えの語・入力の表(便 PA の表 + 2 行の sha256 の頭)が script の定数と同じ。
   封の file は commit した blob と 1 字も変わっていない。API の版・やり直しの待ちは ``xbrl_aiforms_gen_2026-11-03.py`` の字と同じ。
2. 入力 25 件の sha256 が封の表・script の表・門の表・実物で同じ。入力の確かめは 1 byte 違う複製で止まる。前の便の封・結果の文書・script・記録は封の commit から 0 行。engine は封の commit から 0 行。
3. 順序: 封の commit ⊏ script と この門を足した commit(未 commit は赤)。記録の順序は記録が在るときの結果の門に置く。
4. 指示文を組む(【 】が指した数だけに付く・見出しが無ければ「(なし)」・置き換えは 1 回の走査)・答えの読み方(§2-3)・止める条件(§2-4。L-S は member が空の行だけ・「分からない」と答えなしは止めない)。
5. 作り物の本(材料は読まない)で、行を選ぶ → 指示文を組む → 呼ぶ(作り物の transport)→ 読む → 止める → 数える、を本物の関数のまま通す。答えなし・答えのやり直し 1 回・429 の再試行・HTTP 400 で止まる・
   上限で止まる(走らせる前の見積りと走っている間の使った額)・返らない呼び出しも見積りの額で数える・中断した呼び出しを次の走りで見積りの額に数える・試し → ``--resume``・鍵の字が記録にも置き場にも出ない・``--dry-run`` が鍵を読まず通信しない・``--check`` が作り直す。
6. 記録 ``fixtures/xbrl/llm_extract/answers_2026-11-19.json`` が在るときだけ、記録の形・書かないものが無い・行から数を作り直せる、を見る(記録が無い間は、記録の検査は別の門(結果の門)に置く。この門は「在れば見る」の分岐を明示する)。
7. 行頭の名前: この門は ``ENGINE_LATER``・``UNTOUCHED``・``PIN_DEF``・``LATER_ENGINE_COMMITS``・``FROZEN_LATER``・``ENGINE_TRANSITIONS`` を行頭に置かない。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``。script の字を 1 か所替えた版を memory の中に作る。file は書き換えない)。この file は docID の字を持たない。
"""
import ast
import collections
import copy
import importlib.util
import io
import json
import os
import re
import shutil
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


PAT = load_module("tests/measure/test_xbrl_plan_attr_seal.py", "plan_attr_gate_helpers_for_llm_extract_seal")     # 便 PA の門の部品。門としては走らせない
SCT = PAT.SCT
PR = SCT.PR
MS = load_module("measure/xbrl_llm_extract_2026-11-19.py", "llm_extract_script_for_seal_gate")

SEAL_REL = "docs/XBRL_LLM_EXTRACT_SEAL_2026-11-19.md"
SEAL_COMMIT_SHORT = "198961e6"                # 封の commit(literal に留める。script の定数と違えば赤)
SEAL_ADDENDUM_SHORT = "a2ed6d0b"              # 封の §8 追記の commit(literal)
SCRIPT_REL = "measure/xbrl_llm_extract_2026-11-19.py"
GATE_REL = "tests/measure/test_xbrl_llm_extract_seal.py"
RECORD_REL = "fixtures/xbrl/llm_extract/answers_2026-11-19.json"
ORDER_FILES = (SCRIPT_REL, GATE_REL)          # 記録の順序は記録が在るときの結果の門に置く
PA_SEAL_REL = "docs/XBRL_PLAN_ATTR_SEAL_2026-11-19.md"
PA_RESULT_REL = "docs/XBRL_PLAN_ATTR_RESULT_2026-11-19.md"
PA_SCRIPT_REL = "measure/xbrl_plan_attr_2026-11-19.py"
PA_RECORD_REL = "fixtures/xbrl/plan_attr/stops_2026-11-19.json"
#: 入力の表(literal。封の表・script の表・実物と照らす。便 PA の門の表 23 行 + 便 PA の script と記録)
INPUT_SHAS = tuple(PAT.INPUT_SHAS) + (
    (PA_SCRIPT_REL, "711c6ae73538a2140610dd64485a8b5bdf00f9439905a4a9dfdc7ea690eb054d"),
    (PA_RECORD_REL, "53891449b95acaf4812cd77fbc3cb9ebc85573999df39b75f359ef87b69d5176"))
INPUT_RELS = tuple(rel for rel, _sha in INPUT_SHAS)
#: 前の便の封・結果の文書(封の commit から 0 行)
PRIOR_DOCS = tuple(PAT.PRIOR_DOCS) + (PA_SEAL_REL, PA_RESULT_REL)
STDLIB_OK = ("__future__", "argparse", "collections", "hashlib", "importlib", "io", "json", "os", "re", "shutil", "sys", "tempfile", "time", "urllib")
NETWORK_MODULES = ("http", "socket", "ssl", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx", "subprocess")
RESERVED_PREFIXES = SCT.RESERVED_PREFIXES
DOCID_RE = SCT.DOCID_RE
EXPECT_ROWS_PIN = 421
USD_ALL = 0.01225                              # 14 回の手計算(主の席 7 回 × (100 × 5 + 20 × 25)/1e6 + 副の席 7 回 × (50 × 5 + 20 × 25)/1e6)
FAKE_KEY = u"FAKEKEY_zq81x7t3"                 # 試験用の作り物の鍵(本物ではない)。置き場・記録・例外に出ないことを見る

read = SCT.read
sha_of = SCT.sha_of
sha_or_none = SCT.sha_or_none
load_json = SCT.load_json
guard = SCT.guard
patched = SCT.patched
stops = SCT.stops
walk = SCT.walk
od = collections.OrderedDict
quiet = lambda *a: None

K_WIRE = u"配線の確認(封 §2-1。予測ではない。違えば止まる)"
K_TALLY = u"数えるもの(封 §2-5 の 1〜5。束 × 便。語の表の数を隣に)"
K_CALLS = u"呼び出しの記録(封 §2-5 の 6)"
K_PRED = u"予測の判定に要る数(LX-1〜LX-11。当たり・外れは結果の文書で)"
REF_KEY = u"参考 文か見出しに元から 【 か 】 が在る行を除いた行だけの数(当たり・外れは全部の行で付ける。封 §8)"
B_SENT, B_HEAD = u"文に元から 【 か 】 が在る行(封 §8)", u"見出しに元から 【 か 】 が在る行(封 §8)"
G, VM, UN = u"GROUNDED", u"VALUE_MISMATCH", u"UNVERIFIABLE"


def load_source(src):
    u"""script の字(``src``)から module を memory の中に作る。file は読み書きしない。``__file__`` は本物の script。"""
    mod = types.ModuleType("llm_extract_mutant")
    mod.__file__ = os.path.join(ROOT, SCRIPT_REL)
    before = dict(sys.modules)
    try:
        exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    finally:
        for k, v in before.items():
            if sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


# ---------------------------------------------------------------- 1. 封の字
def seal_text():
    return read(SEAL_REL)


def seal_block(seal):
    u"""封 §2-2 の code block(指示文の字)。"""
    m = re.search(r"### §2-2.*?```\n(.*?)\n```", seal, re.S)
    return m.group(1) if m else None


def seal_values(seal):
    u"""封の字から、席・呼び出しの形・上限・単価・回数・試しの行数・答えの語・入力の頭の 2 行を読む(読めなければ None の欄)。"""
    out = {}
    m = re.search(r"主の席 = `([^`]+)`・副の席 = `([^`]+)`", seal)
    out["seats"] = (m.group(1), m.group(2)) if m else None
    m = re.search(r"`max_tokens` (\d+)・`temperature` (\d+)・思考の指定は model ごとに字で留める\(主の席 `(\{[^`]*\})`・副の席 `(\{[^`]*\})`", seal)
    out["shape"] = (int(m.group(1)), int(m.group(2)), json.loads(m.group(3)), json.loads(m.group(4))) if m else None
    m = re.search(r"\*\*上限\*\*: (\d+) USD", seal)
    out["cap3"] = int(m.group(1)) if m else None
    m8 = re.search(r"\*\*上限の替え[^*]*\*\*: (\d+) USD", seal)
    out["cap8"] = int(m8.group(1)) if m8 else None
    out["cap"] = out["cap8"] if out["cap8"] is not None else out["cap3"]          # §8 の置き換えの行が在れば §8 が勝つ
    m = re.search(r"単価は入力 (\d+) USD・出力 (\d+) USD / 100 万 token", seal)
    out["price"] = (int(m.group(1)), int(m.group(2))) if m else None
    m = re.search(r"(\d+) 行 × (\d+) 席 = (\d+) 回", seal)
    out["calls"] = tuple(int(x) for x in m.groups()) if m else None
    m = re.search(r"最大で (\d+) 回", seal)
    out["max_calls"] = int(m.group(1)) if m else None
    m = re.search(r"鍵の昇順の頭 (\d+) 行を 2 席に 1 回ずつ\((\d+) 回\)", seal)
    out["trial"] = (int(m.group(1)), int(m.group(2))) if m else None
    m = re.search(r"行の数が (\d+) と違えば", seal)
    out["rows"] = int(m.group(1)) if m else None
    blk = seal_block(seal) or u""
    bullets = re.findall(r"^- (.+)$", blk, re.M)
    out["words"] = (tuple(bullets[:3]), tuple(bullets[3:6])) if len(bullets) == 6 else None
    out["heads"] = tuple(re.findall(r"\| `[^`]+` \| `([0-9a-f]{8})` で始まる", seal))
    return out


def seal_problems(ms=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    out = []
    if ms.SEAL_ADDENDUM_COMMIT != SEAL_ADDENDUM_SHORT:
        out.append(u"script の封の追記の commit が門と違う")
    if ms.SEAL_COMMIT != SEAL_COMMIT_SHORT or ms.SEAL_REL != SEAL_REL or ms.SCRIPT_REL != SCRIPT_REL or ms.RECORD_REL != RECORD_REL:
        out.append(u"script の封の commit・path・記録の path が門と違う")
    if (ms.PA_SCRIPT_REL, ms.PA_RECORD_REL) != (PA_SCRIPT_REL, PA_RECORD_REL):
        out.append(u"script の便 PA の script・記録の path が門と違う")
    blk = seal_block(seal)
    if blk is None or ms.PROMPT_TEMPLATE != blk:
        out.append(u"script の指示文が封 §2-2 の code block と 1 字ずつ同じでない")
    v = seal_values(seal)
    if v["seats"] != tuple(ms.SEATS) or tuple(ms.SEAT_TAG.items()) != (("claude-sonnet-5-5", u"主"), ("claude-haiku-5-5", u"副")) or v["seats"] != ("claude-sonnet-5-5", "claude-haiku-5-5"):
        out.append(u"席の名(主・副)が封と違う")
    if v["shape"] is None or (ms.MAX_TOKENS, ms.TEMPERATURE, ms.THINKING.get(ms.SEATS[0]), ms.THINKING.get(ms.SEATS[1])) != v["shape"]:
        out.append(u"max_tokens・temperature・思考の指定が封と違う")
    if v["cap"] is None or ms.COST_CAP_USD != float(v["cap"]):
        out.append(u"上限が封と違う")
    if v["price"] is None or (ms.PRICE_IN, ms.PRICE_OUT) != tuple(float(x) for x in v["price"]):
        out.append(u"単価が封と違う")
    if v["calls"] is None or v["rows"] != EXPECT_ROWS_PIN or ms.EXPECT_ROWS != EXPECT_ROWS_PIN or v["calls"] != (EXPECT_ROWS_PIN, 2, EXPECT_ROWS_PIN * 2) or len(ms.SEATS) != 2:
        out.append(u"行の数 421・席 2・呼び出し 842 が封と違う")
    if v["max_calls"] != EXPECT_ROWS_PIN * 2 * ms.MAX_ANSWER_ATTEMPTS or ms.MAX_ANSWER_ATTEMPTS != 2:
        out.append(u"最大の回数(1684)・答えのやり直し 1 回が封と違う")
    if v["trial"] != (5, 10) or ms.TRIAL_ROWS != 5:
        out.append(u"試しの行数・回数が封と違う")
    if v["words"] != (tuple(ms.RANGE_WORDS), tuple(ms.NATURE_WORDS)) or (ms.F_RANGE, ms.F_NATURE) != (u"範囲", u"性質") or (ms.PART, ms.PLAN) != (u"一部分", u"計画・予想"):
        out.append(u"答えの語(範囲・性質)が封の指示文と違う")
    if (ms.NO_HEADING, ms.MARK_OPEN, ms.MARK_CLOSE) != (u"(なし)", u"【", u"】"):
        out.append(u"見出しが無いときの字・印が封と違う")
    if (ms.GEN.API_VERSION, tuple(ms.GEN.RETRY_WAITS), ms.GEN.KEY_ENV) != ("2023-06-01", (2, 8), "ANTHROPIC_API_KEY") or ms.KEY_ENV != "ANTHROPIC_API_KEY":
        out.append(u"API の版・やり直しの待ち・鍵の環境変数の名が封(aiforms_gen と同じ字)と違う")
    if tuple(ms.STOP_HTTP) != (400, 401, 403) or ms.PROFILE != u"P33E":
        out.append(u"HTTP で止める一覧か profile が決めと違う")
    if (ms.REF_KEY, ms.B_SENT, ms.B_HEAD) != (REF_KEY, B_SENT, B_HEAD):
        out.append(u"封 §8 の参考の欄・束の名が門と違う")
    if (ms.K_WIRE, ms.K_TALLY, ms.K_CALLS, ms.K_PRED) != (K_WIRE, K_TALLY, K_CALLS, K_PRED):
        out.append(u"記録の欄の名が門と違う")
    for phrase in (u"LX-1", u"LX-11", u"両方の席に答えが在る行の 85%", u"答えを司令塔が手で直さない", u"返らなかった呼び出しは見積りの額で", u"試しの 10 回の答えは、形が良ければそのまま本番の答えに使う",
                   u"`--dry-run` は鍵を読まず通信せず", u"L-S(範囲)", u"member の欄が空", u"上限の替え", u"この 2 つの束を除いた数は参考に並べる", u"便は TSS・KAM・YS の順"):
        if phrase not in seal:
            out.append(u"封に要点の字が無い: %s" % phrase[:20])
    return out


def seal_table_problems(ms=None, seal=None):
    u"""封 §1 の 2 行の頭の字が script・門の表の sha256 の頭と同じ。script の表が門の表と同じ(25 行・番号が 1〜25)。"""
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    out = []
    heads = seal_values(seal)["heads"]
    if heads != tuple(sha[:8] for _rel, sha in INPUT_SHAS[-2:]):
        out.append(u"封の入力の頭の字が門の表の最後の 2 行の sha256 の頭と違う")
    if [(rel, sha) for _no, rel, sha in ms.INPUTS] != list(INPUT_SHAS) or [no for no, _r, _s in ms.INPUTS] != list(range(1, 26)):
        out.append(u"script の入力の表が門の表と違う")
    if list(INPUT_SHAS[:23]) != list(PAT.INPUT_SHAS):
        out.append(u"門の表の頭の 23 行が便 PA の門の表と違う")
    return out


def seal_history_problems(root=REPO):
    u"""封の file の履歴は 2 commit(198961e6 が封・a2ed6d0b が §8 の追記)。封の commit の blob は今の file の頭と 1 字も変わらない(追記は §8 を足すだけ)。今の file は追記の commit の blob と同じ。"""
    c = PR.added_commits(root, PREFIX + SEAL_REL)
    if len(c) != 1 or not c[0].startswith(SEAL_COMMIT_SHORT):
        return [u"封の commit が履歴に 1 つで %s に決まらない" % SEAL_COMMIT_SHORT]
    rc, log = PR.git_in(root, "log", "--format=%H", "--reverse", "--", PREFIX + SEAL_REL)
    hs = [x for x in log.split() if x]
    if len(hs) != 2 or not hs[0].startswith(SEAL_COMMIT_SHORT) or not hs[1].startswith(SEAL_ADDENDUM_SHORT):
        return [u"封の file の履歴が(封・§8 の追記)の 2 commit でない"]
    rc, sealed = PR.git_in(root, "show", "%s:%s" % (hs[0], PREFIX + SEAL_REL))
    rc, added = PR.git_in(root, "show", "%s:%s" % (hs[1], PREFIX + SEAL_REL))
    now = seal_text().rstrip(u"\n")
    if now != added.rstrip(u"\n"):
        return [u"今の封が追記の commit の blob と違う"]
    if not now.startswith(sealed.rstrip(u"\n")) or u"## §8 追記" not in now[len(sealed.rstrip(u"\n")):]:
        return [u"封の commit の字が今の封の頭と違う(追記の外が書き換えられた)"]
    return []


# ---------------------------------------------------------------- 2. 入力・前の文書・engine・順序
def input_sha_problems(ms=None):
    ms = ms or MS
    out = []
    if [(rel, sha) for _no, rel, sha in ms.INPUTS] != list(INPUT_SHAS):
        out.append(u"script の入力の表が門の表と違う")
    out.extend(u"入力の sha256 が表と違う: %s" % rel for rel, want in INPUT_SHAS if sha_of(rel) != want)
    return out


def input_wire_problems(ms=None):
    u"""``check_inputs`` が、表のとおりの複製では通り、1 byte 違う複製では止まる(25 件のどれでも)。"""
    ms = ms or MS
    out = []
    tmp = tempfile.mkdtemp(prefix="lx_inputs_")
    try:
        for rel in INPUT_RELS:
            os.makedirs(os.path.dirname(os.path.join(tmp, rel)), exist_ok=True)
            os.symlink(os.path.join(ROOT, rel), os.path.join(tmp, rel))
        if [r[u"sha256"] for r in ms.check_inputs(tmp)] != [s for _r, s in INPUT_SHAS]:
            out.append(u"表のとおりの複製で check_inputs が表の sha256 を返さない")
        for i in range(len(INPUT_RELS)):
            p = os.path.join(tmp, INPUT_RELS[i])
            os.unlink(p)
            with open(os.path.join(ROOT, INPUT_RELS[i]), "rb") as fh:
                data = fh.read()
            with open(p, "wb") as fh:
                fh.write(data + b" ")
            if stops(ms, ms.check_inputs, tmp) is not True:
                out.append(u"入力 %d が 1 byte 違うのに止まらない" % (i + 1))
            os.unlink(p)
            os.symlink(os.path.join(ROOT, INPUT_RELS[i]), p)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def prior_problems(root=REPO):
    u"""前の便の封・結果の文書・script・記録が封の commit から 0 行(作業木の未 commit の変更も含めて見る)。"""
    s = PR.added_commits(root, PREFIX + SEAL_REL)
    if len(s) != 1:
        return [u"封の commit が履歴に 1 つで決まらない"]
    rc, txt = PR.git_in(root, "diff", "--name-only", s[0], "--", *[PREFIX + d for d in PRIOR_DOCS] + [PREFIX + r for r in INPUT_RELS])
    if rc != 0:
        return [u"git diff が失敗した"]
    return [u"前の便の文書・script・記録が封の後に変わっている: %s" % ln for ln in txt.splitlines() if ln.strip()]


def engine_zero_problems(root=REPO, seal_rel=SEAL_REL, prefix=PREFIX):
    return SCT.engine_zero_problems(root, seal_rel, prefix)


def order_of(root=REPO, seal_short=SEAL_COMMIT_SHORT, others=None):
    others = list(ORDER_FILES) if others is None else others
    return PR.order_problems(root, PREFIX, SEAL_REL, seal_short, [], others)


# ---------------------------------------------------------------- 3. 指示文・答えの読み方・止める条件(純粋な関数)
SENT = u"当連結会計年度の売上高は1,234百万円となり、前期比 5.6% 増加しました。"       # 封 §2-2 の例(作り物)


def mark_cases():
    u"""(文, 位置の字, 期待する文)。位置の字は文の中の数の始まり(空白で始まる数は空白から)。"""
    return [
        (SENT, u"1,234", u"当連結会計年度の売上高は【1,234】百万円となり、前期比 5.6% 増加しました。"),
        (SENT, u" 5.6", u"当連結会計年度の売上高は1,234百万円となり、前期比 【5.6】% 増加しました。"),
        (u"利益は△1,234百万円でした。", u"△1,234", u"利益は【△1,234】百万円でした。"),
        (u"利益は△ 12円でした。", u"△ 12", u"利益は【△ 12】円でした。"),
        (u"損失はマイナス 7 千円でした。", u"マイナス 7", u"損失は【マイナス 7】 千円でした。"),
        (u"売上は12億3,456万円でした。", u"12億", u"売上は【12億3,456万】円でした。"),
        (u"売上は1,234万円でした。", u"1,234", u"売上は【1,234万】円でした。"),
        (u"売上は1万2,345円でした。", u"1万", u"売上は【1万2,345】円でした。"),
        (u"差は-5円でした。", u"-5", u"差は【-5】円でした。"),
        (u"合計は50", u"50", u"合計は【50】"),
        (u"Aは100円、Bは200円、Cは300円です。", u"200", u"Aは100円、Bは【200】円、Cは300円です。"),
        (u"Aは100円、Bは200円、Cは300円です。", u"100", u"Aは【100】円、Bは200円、Cは300円です。"),
    ]


def mark_problems(ms=None):
    ms = ms or MS
    out = []
    for s, token, want in mark_cases():
        pos = s.index(token)
        got = ms.mark_sentence(s, pos)
        if got != want:
            out.append(u"【 】の位置が違う: %s → %s" % (token, got))
        if got.count(u"【") != 1 or got.count(u"】") != 1:
            out.append(u"【 】が指した数だけに付かない(印の数が 1 組でない): %s" % token)
    for bad in (u"数ではない文", u"あ100"):
        if stops(ms, ms.mark_sentence, bad, 0) is not True:
            out.append(u"数の字で始まらない位置に印を入れようとして止まらない")
    return out


def prompt_problems(ms=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    out = []
    blk = seal_block(seal) or u""
    h, sent = u"経営成績", ms.mark_sentence(SENT, SENT.index(u"1,234"))
    got = ms.build_prompt(h, sent)
    if got != blk.replace(u"{HEADING}", h).replace(u"{SENTENCE}", sent):
        out.append(u"指示文の組み立てが封の code block の置き換えと違う")
    lines = got.split(u"\n")
    if u"見出し: 経営成績" not in lines or (u"文: " + sent) not in lines:
        out.append(u"見出しの行・文の行が封の形でない")
    if u"見出し: (なし)" not in ms.build_prompt(None, sent).split(u"\n"):
        out.append(u"見出しが無いとき「(なし)」にならない")
    tricky = u"文に {HEADING} と {SENTENCE} が在る【100】円。"
    got2 = ms.build_prompt(u"見出し{SENTENCE}", tricky)
    if got2.count(u"{HEADING}") != 1 or got2.count(u"{SENTENCE}") != 2 or (u"文: " + tricky) not in got2.split(u"\n"):
        out.append(u"置き換えが 1 回の走査でない(文・見出しの中の {…} が再び置き換わる)")
    return out


READ_CASES = (
    (u'{"範囲": "全体", "性質": "実績"}', "end_turn", (u"全体", u"実績")),
    (u'{"範囲": "一部分", "性質": "計画・予想"}', "end_turn", (u"一部分", u"計画・予想")),
    (u'{"範囲": "分からない", "性質": "分からない"}', "end_turn", (u"分からない", u"分からない")),
    (u'答え: {"範囲": "全体", "性質": "実績"} 以上', "end_turn", (u"全体", u"実績")),
    (u'{"範囲": " 全体 ", "性質": "\\t実績\\n"}', "end_turn", (u"全体", u"実績")),
    (u'{"範囲": "全体", "性質": "実績", "余り": 1}', "end_turn", (u"全体", u"実績")),
    (u'{"範囲": "全体", "性質": "実績"}', "max_tokens", None),
    (u'{"範囲": "全体", "性質": "実績"}', None, None),
    (u"", "end_turn", None),
    (None, "end_turn", None),
    (u"読めません", "end_turn", None),
    (u'{"範囲": "全部", "性質": "実績"}', "end_turn", None),
    (u'{"範囲": "全体です", "性質": "実績"}', "end_turn", None),
    (u'{"範囲": "全体", "性質": "実績だった"}', "end_turn", None),
    (u'{"範囲": "全体", "性質": "計画"}', "end_turn", None),
    (u'{"範囲": "全体"}', "end_turn", None),
    (u'{"範囲": 1, "性質": "実績"}', "end_turn", None),
    (u'{"範囲": ["全体"], "性質": "実績"}', "end_turn", None),
    (u'} {"範囲": "全体", "性質": "実績"', "end_turn", None),
    (u'{"範囲": "全体", "性質": "実績"} と {"範囲": "全体", "性質": "実績"}', "end_turn", None),
    (u'{範囲: 全体}', "end_turn", None),
    (u'["全体", "実績"]', "end_turn", None),
)


def read_problems(ms=None):
    ms = ms or MS
    out = []
    for text, sr, want in READ_CASES:
        got = ms.read_answer(text, sr)
        if got != want:
            out.append(u"答えの読みが違う: %r (%s) → %r" % (text, sr, got))
    return out


def stops_problems(ms=None):
    ms = ms or MS
    out = []
    table = [  # (答え, member が空, (L-S, L-P, L-U))
        ((u"一部分", u"実績"), True, (True, False, True)), ((u"一部分", u"実績"), False, (False, False, False)),
        ((u"全体", u"計画・予想"), True, (False, True, True)), ((u"全体", u"計画・予想"), False, (False, True, True)),
        ((u"一部分", u"計画・予想"), True, (True, True, True)), ((u"一部分", u"計画・予想"), False, (False, True, True)),
        ((u"分からない", u"分からない"), True, (False, False, False)), ((u"全体", u"実績"), True, (False, False, False)),
        ((u"分からない", u"実績"), True, (False, False, False)), ((u"全体", u"分からない"), False, (False, False, False)),
        (None, True, (False, False, False)), (None, False, (False, False, False))]
    for ans, empty, want in table:
        got = ms.stops_of(ans, empty)
        if tuple(got) != want:
            out.append(u"止める条件が違う: %r・member が空 %s → %r" % (ans, empty, got))
    if abs(ms.estimate_usd(1000) - 0.01) > 1e-12 or abs(ms.cost_usd(100, 20) - 0.001) > 1e-12 or ms.cost_usd(None, None) != 0:
        out.append(u"見積り・費用の計算が封の単価(入力 5・出力 25・max_tokens 200)と違う")
    return out


def fake_pairs(sentences, specs):
    pairs = []
    for si, token, state, member in specs:
        s = sentences[si]
        pos = s.index(token)
        pairs.append(({u"sentence": si, u"pos": pos, u"span": s[max(0, pos - 30):pos + len(token) + 10], u"member": member}, {u"state": state, u"pointers": []}))
    return pairs


def unit_problems(ms=None):
    u"""``unit_rows``(本物): 札つきの行だけ・見出し(最も近い・数の claim を持つ文は見出しでない)・member の欄・位置の確かめ。"""
    ms = ms or MS
    out = []
    S = [u"経営成績", u"売上高は100円でした。", u"その他", u"売上高は200円でした。", u"利益は300円でした。"]
    pairs = fake_pairs(S, [(1, u"100", G, []), (3, u"200", VM, [u"x"]), (4, u"300", UN, [])])
    p1, p3 = S[1].index(u"100"), S[3].index(u"200")
    rows = ms.unit_rows(pairs, S, frozenset([(1, p1), (3, p3), (4, S[4].index(u"300"))]))
    if rows != [[1, p1, u"G", True, S[1], u"経営成績"], [3, p3, u"V", False, S[3], u"その他"]]:
        out.append(u"unit_rows の行が手計算と違う(state が UNVERIFIABLE の行は除く・member の欄・最も近い見出し): %s" % (rows,))
    if ms.unit_rows(pairs, S, frozenset([(3, p3)])) != [[3, p3, u"V", False, S[3], u"その他"]]:
        out.append(u"札の無い行も返す")
    S2 = [u"売上100円", u"利益200円。"]
    pairs2 = fake_pairs(S2, [(0, u"100", G, []), (1, u"200", G, [])])
    rows2 = ms.unit_rows(pairs2, S2, frozenset([(1, S2[1].index(u"200"))]))
    if rows2[0][5] is not None:
        out.append(u"数の claim を持つ文を見出しに選ぶ")
    bad = [({u"sentence": 1, u"pos": 0, u"span": u"x", u"member": []}, {u"state": G, u"pointers": []})]
    if stops(ms, ms.unit_rows, bad, S, frozenset()) is not True:
        out.append(u"位置の欄が数の字でないのに止まらない")
    return out


# ---------------------------------------------------------------- 4. 作り物の本(材料は読まない)
class World(object):
    u"""作り物の 3 便(TSS 1 本・KAM 1 本・YS 1 本)。札つきの行 6 つ(+ 引けない札 2 つ)。便・state・札の束・member で非対称。手計算の数は ``expect_*``。"""

    def __init__(self, ms):
        self.ms = ms
        T = [u"経営成績", u"売上高は100円でした(甲1)。", u"その他", u"売上高は200円の予定です(甲2)。", u"別", u"利益は50円でした(甲8)。"]
        K = [u"監査上の項目", u"売上高は1,000円でした(甲3)。", u"資産は【注】50円でした(甲4)。"]
        Y1 = [u"研究の項目", u"費用は10円でした(甲5)。"]
        Y2 = [u"【設備】の項目", u"投資は20円でした(甲6)。"]
        self.S = {"T": T, "K": K, "Y1": Y1, "Y2": Y2}
        ps = lambda s, si, t: s[si].index(t)
        self.pos = {1: ps(T, 1, u"100"), 2: ps(T, 3, u"200"), 3: ps(K, 1, u"1,000"), 4: ps(K, 2, u"50"), 5: ps(Y1, 1, u"10"), 6: ps(Y2, 1, u"20"), 8: ps(T, 5, u"50")}
        c1, c2 = list(ms.KAM.SIDES.keys())
        y1, y2, y3 = list(ms.YS.SECTIONS.keys())
        self.sides = {"c1": c1, "c2": c2, "y1": y1, "y2": y2, "y3": y3}
        p = self.pos
        self.books = [
            collections.OrderedDict([(u"便", u"TSS"), (u"#", 1), (u"units", [(None, [[1, p[1], u"V", True, T[1], T[0]], [3, p[2], u"V", True, T[3], T[2]], [5, p[8], u"G", True, T[5], T[4]]])])]),
            collections.OrderedDict([(u"便", u"KAM"), (u"#", 1), (u"units", [(c1, [[1, p[3], u"V", False, K[1], K[0]], [2, p[4], u"G", True, K[2], K[0]]]), (c2, [])])]),
            collections.OrderedDict([(u"便", u"YS"), (u"#", 1), (u"units", [(y1, [[1, p[5], u"G", True, Y1[1], None]]), (y2, [[1, p[6], u"V", True, Y2[1], Y2[0]]]), (y3, [])])])]
        IN, OUT, DROP = ms.AT.KIND_IN, ms.AT.KIND_OUT, ms.AT.KIND_DROP

        def lab(batch, n, side, si, pos, state, typ=None, diff=None, kind=None, name=None):
            return od([(u"便", batch), (u"#", n), (u"側", side), (u"si", si), (u"pos", pos), (u"state", state), (u"型", typ), (u"違うもの", diff), (u"種別", kind), (u"先", name)])
        self.labels = [
            lab(u"TSS", 1, None, 1, p[1], u"V", u"ア", u"", IN, u"範囲"),                    # R1 V 範囲
            lab(u"TSS", 1, None, 3, p[2], u"V", u"ウ", u"", OUT, u"見積り・計画"),            # R2 V 見積り・計画
            lab(u"KAM", 1, c1, 1, p[3], u"V", u"イ", u"", IN, u"項目"),                       # R3 V それ以外
            lab(u"KAM", 1, c1, 2, p[4], u"G", u"a", None),                                     # R4 G a
            lab(u"YS", 1, y1, 1, p[5], u"G", u"b", u"範囲"),                                   # R5 G b 範囲
            lab(u"YS", 1, y2, 1, p[6], u"V", u"ア", u"", IN, u"範囲"),                        # R6 V 範囲
            lab(u"YS", 2, y1, 1, 3, u"V", u"イ", u"", IN, u"項目"),                           # 本が無く引けない
            lab(u"TSS", 1, None, 5, p[8], u"V", u"イ", u"", IN, u"項目")]                     # 行は在るが state が違う(G)
        K_ = lambda b, n, s, si, pos, st: [b, n, s, si, pos, st]
        keys = [(u"TSS", 1, None, 1, p[1], u"V"), (u"TSS", 1, None, 3, p[2], u"V"), (u"KAM", 1, c1, 1, p[3], u"V"), (u"KAM", 1, c1, 2, p[4], u"G"),
                (u"YS", 1, y1, 1, p[5], u"G"), (u"YS", 1, y2, 1, p[6], u"V"), (u"TSS", 1, None, 5, p[8], u"G")]
        wp = (1, 2)                                   # 便 PA の段 2 で止めた行(R2・R3)
        ws = (0, 5)                                   # 便 SC の段 2 で止めた行(R1・R6)
        self.pa_rec = {u"行": [list(k) + [u"", u"P" if i in wp else u"", u""] for i, k in enumerate(keys)]}
        self.sc_rec = {u"行": [list(k) + [True, u"", u"S" if i in ws else u"", u""] for i, k in enumerate(keys)]}
        self.recs = {u"rt": {}, u"sc": self.sc_rec, u"pa": self.pa_rec}
        #: 席ごとの答え(主, 副)。None = 読めない答え(答えのやり直しの後も)
        self.answers = {1: ((u"一部分", u"実績"), (u"全体", u"実績")), 2: ((u"全体", u"計画・予想"), (u"一部分", u"計画・予想")), 3: ((u"一部分", u"計画・予想"), None),
                        4: ((u"一部分", u"実績"), (u"分からない", u"分からない")), 5: (None, (u"一部分", u"実績")), 6: ((u"全体", u"実績"), (u"全体", u"実績"))}

    def expected_rows(self):
        u"""手計算の記録の行(先頭 11 欄)。"""
        A = self.answers
        p = self.pos
        out = []
        base = [(u"TSS", 1, None, 1, p[1], u"V", True), (u"TSS", 1, None, 3, p[2], u"V", True), (u"KAM", 1, self.sides["c1"], 1, p[3], u"V", False),
                (u"KAM", 1, self.sides["c1"], 2, p[4], u"G", True), (u"YS", 1, self.sides["y1"], 1, p[5], u"G", True), (u"YS", 1, self.sides["y2"], 1, p[6], u"V", True)]
        for i, b in enumerate(base):
            m, s = A[i + 1]
            cells = list(m or (u"答えなし", u"答えなし")) + list(s or (u"答えなし", u"答えなし"))
            out.append(list(b) + cells)
        return out

    def transport(self, log=None, seq=None):
        u"""作り物の transport。指示文の中の「(甲 n)」で行を決め、席(model)で答えを変える。読めない答えは text「読めません」。"""
        n_calls = []

        def t(prompt, model, key):
            n_calls.append((model, prompt))
            if log is not None:
                log.append((model, prompt, key))
            if seq is not None:
                r = seq(len(n_calls), model, prompt)
                if r is not None:
                    return r
            row = int(re.search(u"\\(甲(\\d)\\)", prompt).group(1))
            ans = self.answers[row][0 if model == "claude-sonnet-5-5" else 1]
            if ans is None:
                text = u"読めません"
            else:
                text = u"答えです。" + json.dumps({u"範囲": ans[0], u"性質": ans[1]}, ensure_ascii=False) + u" 以上"
            return 200, body(text, tin=100 if model == "claude-sonnet-5-5" else 50)
        t.n = n_calls
        return t


def body(text, tin=100, tout=20, stop="end_turn", blocks=("thinking", "text")):
    u"""作り物の返事。入力 token は既定で 100(副の席の返事は ``World.transport`` が 50 にする)。"""
    content = [({"type": "thinking", "thinking": u"…"} if b == "thinking" else {"type": "text", "text": text}) for b in blocks]
    return json.dumps({"content": content, "usage": {"input_tokens": tin, "output_tokens": tout}, "stop_reason": stop}).encode("utf-8")


def collect(ms, world, expect=6, books=None, labels=None, pa_rec=None):
    recs = dict(world.recs)
    if pa_rec is not None:
        recs[u"pa"] = pa_rec
    with patched(ms.SC, build_labels=lambda r: list(labels if labels is not None else world.labels)), patched(ms.PA, engine_fp=lambda rt: od()), patched(ms, EXPECT_ROWS=expect):
        return ms.collect_items(root=ROOT, recs=recs, inputs=[], books=copy.deepcopy(books if books is not None else world.books), say=quiet)


class Temp(object):
    def __init__(self):
        self.d = tempfile.mkdtemp(prefix="lx_gate_")

    def p(self, *a):
        return os.path.join(self.d, *a)

    def close(self):
        shutil.rmtree(self.d, ignore_errors=True)


def run_world(ms, world, tmp, expect=6, transport=None, trial=False, resume=False, sleep=quiet, say=quiet, tag=u"w", labels=None, work=None):
    u"""``run`` を作り物の本・作り物の transport・使い捨ての置き場と出力先で本物のまま走らせる。"""
    transport = transport or world.transport()
    with patched(ms.SC, build_labels=lambda r: list(labels if labels is not None else world.labels)), patched(ms.PA, engine_fp=lambda rt: od()), patched(ms, EXPECT_ROWS=expect):
        return ms.run(root=ROOT, procs=1, say=say, trial=trial, resume=resume, work=work or tmp.p(tag, u"work"), out=tmp.p(tag, u"answers.json"), key=FAKE_KEY, transport=transport, sleep=sleep,
                      recs=copy.deepcopy(world.recs), inputs=[], books=copy.deepcopy(world.books))


def items_problems(ms=None):
    u"""送る行を選ぶ(札つきで同じ state で引けた行だけ・鍵の昇順・便の順)・指示文を組む・配線の確認が止める。"""
    ms = ms or MS
    out = []
    w = World(ms)
    items, wire, _i, _r, _fp, _l, _m = collect(ms, w)
    keys = [(it[u"batch"], it[u"book"], it[u"side"], it[u"si"], it[u"pos"], it[u"state"]) for it in items]
    p = w.pos
    c1, y1, y2 = w.sides["c1"], w.sides["y1"], w.sides["y2"]
    want = [(u"TSS", 1, None, 1, p[1], u"V"), (u"TSS", 1, None, 3, p[2], u"V"), (u"KAM", 1, c1, 1, p[3], u"V"), (u"KAM", 1, c1, 2, p[4], u"G"), (u"YS", 1, y1, 1, p[5], u"G"), (u"YS", 1, y2, 1, p[6], u"V")]
    if keys != want:
        out.append(u"送る行の鍵・順が手計算と違う(引けない札・state が違う札は送らない・便の順 TSS・KAM・YS): %s" % (keys,))
    if [it[u"empty"] for it in items] != [True, True, False, True, True, True]:
        out.append(u"member の欄が空かの読みが違う")
    blk = seal_block(seal_text())
    exp1 = blk.replace(u"{HEADING}", u"経営成績").replace(u"{SENTENCE}", u"売上高は【100】円でした(甲1)。")
    if not items or items[0][u"prompt"] != exp1:
        out.append(u"1 行目の指示文が手計算(見出し・【 】の位置)と違う")
    if len(items) == 6 and u"見出し: (なし)\n文: 費用は【10】円でした(甲5)。\n" not in items[4][u"prompt"]:
        out.append(u"見出しが無い行の指示文が「(なし)」と【 】で組まれていない")
    if len(items) == 6 and (u"文: 資産は【注】【50】円でした(甲4)。\n" not in items[3][u"prompt"] or u"見出し: 監査上の項目\n" not in items[3][u"prompt"]):
        out.append(u"4 行目の指示文が手計算と違う")
    if len(items) == 6 and any(it[u"prompt_sha256"] != ms.sha256_text(it[u"prompt"]) for it in items):
        out.append(u"指示文の sha256 が指示文のものでない")
    if wire.get(u"送る行の数(札つきで同じ state で引けた行)") != 6 or wire.get(u"引けなかった札") != 2 or wire.get(u"member の欄が空の行") != 5:
        out.append(u"配線の確認の数が手計算と違う")
    if wire.get(u"文に元から 【 か 】 が在る行(封 §8)") != 1 or wire.get(u"見出しに元から 【 か 】 が在る行(封 §8)") != 1 or wire.get(u"文か見出しに元から 【 か 】 が在る行(数えるだけ。字は変えない)") != 2:
        out.append(u"元から 【 】 が在る行の数(文 1・見出し 1)が手計算と違う")
    if [(it[u"sent_bracket"], it[u"head_bracket"]) for it in items] != [(False, False)] * 3 + [(True, False), (False, False), (False, True)]:
        out.append(u"行ごとの「文に在る・見出しに在る」の印が手計算と違う")
    if wire.get(u"見出しが無い行(%s)" % u"(なし)") != 1:
        out.append(u"見出しが無い行の数が違う")
    # 止める: 行の数が違う・便 PA の記録に行が無い・鍵が重なる・state が違う便 PA の行
    if stops(ms, collect, ms, w, 7) is not True:
        out.append(u"送る行の数が決めと違うのに止まらない")
    if stops(ms, collect, ms, w, 6, None, None, {u"行": w.pa_rec[u"行"][1:]}) is not True:
        out.append(u"送る行が便 PA の記録の行に無いのに止まらない")
    if stops(ms, collect, ms, w, 6, None, w.labels + [w.labels[0]]) is not True:
        out.append(u"札の鍵が重なるのに止まらない")
    return out


def answers_problems(ms=None):
    u"""呼ぶ → 読む → 止める → 数える を本物の関数のまま通し、手計算と合わせる(答えなし・答えのやり直し 1 回・「分からない」・member が空の行だけの L-S)。"""
    ms = ms or MS
    out = []
    w = World(ms)
    tmp = Temp()
    try:
        tr = w.transport()
        rec = run_world(ms, w, tmp, transport=tr)
        rows = [r[:11] for r in rec[u"行"]]
        if rows != w.expected_rows():
            out.append(u"記録の行(席ごとの答え)が手計算と違う: %s" % (rows,))
        if [r[12] for r in rec[u"行"]] != [1, 1, 1, 1, 2, 1] or [r[13] for r in rec[u"行"]] != [1, 1, 2, 1, 1, 1]:
            out.append(u"答えのやり直し(読めない答えは 1 回だけ)の呼び出しの数が違う")
        if len(tr.n) != 14:
            out.append(u"transport を呼んだ回数が 14 でない(12 + 読めない 2 回のやり直し): %d" % len(tr.n))
        if rec.get(u"封の commit") != SEAL_COMMIT_SHORT or rec.get(u"封の追記の commit") != SEAL_ADDENDUM_SHORT:
            out.append(u"記録の封の commit・封の追記の commit が違う")
        if [(r[14], r[15]) for r in rec[u"行"]] != [(False, False)] * 3 + [(True, False), (False, False), (False, True)]:
            out.append(u"記録の行の「元から 【 か 】 が在る」の欄が手計算と違う")
        T = rec[K_TALLY]
        g = lambda b, col=u"全体": T[b][col]
        r_, pl, ot, ga, gb = g(u"V 「範囲」の札"), g(u"V 「見積り・計画」の札"), g(u"V 「それ以外」の札(分母から除く札は除く)"), g(u"G 札 a"), g(u"G 札 b のうち「違うもの」が範囲")
        if r_[u"行"] != 2 or r_[u"主の席"][u"止めた行"] != od([(u"L-S", 1), (u"L-P", 0), (u"L-U", 1)]) or r_[u"副の席"][u"止めた行"] != od([(u"L-S", 0), (u"L-P", 0), (u"L-U", 0)]) \
                or r_[u"語の表で止めた行"][u"W-S(便 SC の段 2)"] != 2 or r_[u"主の席"][u"語の表との重なり"][u"S"] != od([(u"語の表も席も止めた", 1), (u"語の表だけが止めた", 1), (u"席だけが止めた", 0), (u"どちらも止めない", 0)]):
            out.append(u"V 「範囲」の札の数が手計算と違う")
        if pl[u"行"] != 1 or pl[u"主の席"][u"止めた行"] != od([(u"L-S", 0), (u"L-P", 1), (u"L-U", 1)]) or pl[u"副の席"][u"止めた行"] != od([(u"L-S", 1), (u"L-P", 1), (u"L-U", 1)]) or pl[u"語の表で止めた行"][u"W-P(便 PA の段 2)"] != 1:
            out.append(u"V 「見積り・計画」の札の数が手計算と違う(副の席は member が空の行の L-S も数える)")
        if ot[u"行"] != 1 or ot[u"主の席"][u"止めた行"] != od([(u"L-S", 0), (u"L-P", 1), (u"L-U", 1)]) or ot[u"副の席"][u"答えなしの行"] != 1:
            out.append(u"V 「それ以外」の札の数が手計算と違う(member の欄が空でない行の L-S は止めない)")
        if ga[u"主の席"][u"止めた行"][u"L-S"] != 1 or ga[u"副の席"][u"止めた行"][u"L-U"] != 0 or ga[u"副の席"][u"答えの分布(範囲 / 性質)"][u"分からない / 分からない"] != 1:
            out.append(u"G 札 a の数が手計算と違う(「分からない」は止めない)")
        if gb[u"主の席"][u"答えなしの行"] != 1 or gb[u"主の席"][u"止めた行"][u"L-U"] != 0 or gb[u"副の席"][u"止めた行"][u"L-S"] != 1:
            out.append(u"G 札 b の数が手計算と違う(答えなしは止めない)")
        if g(u"V 「範囲」の札", u"TSS")[u"行"] != 1 or g(u"V 「範囲」の札", u"YS")[u"行"] != 1 or g(u"V 「範囲」の札", u"KAM")[u"行"] != 0:
            out.append(u"便ごとの行の数が違う")
        bs, bh = T[B_SENT][u"全体"], T[B_HEAD][u"全体"]
        if bs[u"行"] != 1 or bs[u"主の席"][u"止めた行"] != od([(u"L-S", 1), (u"L-P", 0), (u"L-U", 1)]) or bs[u"副の席"][u"止めた行"] != od([(u"L-S", 0), (u"L-P", 0), (u"L-U", 0)]) or T[B_SENT][u"KAM"][u"行"] != 1 or T[B_SENT][u"TSS"][u"行"] != 0:
            out.append(u"文に元から 【 か 】 が在る行の束の数が手計算と違う(行 1・主の席の L-S 1)")
        if bh[u"行"] != 1 or bh[u"主の席"][u"止めた行"] != od([(u"L-S", 0), (u"L-P", 0), (u"L-U", 0)]) or bh[u"語の表で止めた行"][u"W-S(便 SC の段 2)"] != 1 or T[B_HEAD][u"YS"][u"行"] != 1:
            out.append(u"見出しに元から 【 か 】 が在る行の束の数が手計算と違う(行 1・W-S 1)")
        pr = rec[K_PRED]
        ref = pr.get(REF_KEY)
        if not ref:
            out.append(u"予測の判定に要る数に参考(2 つの束を除いた数)が無い")
        else:
            lx1 = ref[u"LX-1 L-S の止めた行 / V 「範囲」の札"]
            lx8 = ref[u"LX-8 L-U の止めた行(V 「範囲」と「見積り・計画」の合わせ / G 札 a)と W-U との差(席 − 語の表)"]
            lx9 = ref[u"LX-9 L-U の止めた行 / 行(V 「それ以外」の札と、「範囲」と「見積り・計画」の合わせ)と率の差(ポイント。合わせ − それ以外)"]
            lx10 = ref[u"LX-10 2 つの席の答えの一致(札つきの行の全部)"]
            if lx1 != od([(u"行", 1), (u"主の席", 1), (u"副の席", 0), (u"語の表", 1)]) or ref[u"LX-3 L-S の止めた行 / G 札 a"][u"行"] != 0 or ref[u"LX-11 主の席の答えなしの行"] != 1 \
                    or lx8[u"V 「範囲」と「見積り・計画」の合わせ"] != od([(u"行", 2), (u"主の席", 2), (u"副の席", 1), (u"語の表", 2)]) or lx8[u"V の差(主の席 − 語の表)"] != 0 \
                    or lx9[u"率の差(ポイント)"] != u"0.00" or (lx10[u"範囲"][u"分子"], lx10[u"範囲"][u"分母"], lx10[u"性質"][u"分子"], lx10[u"性質"][u"分母"]) != (0, 2, 2, 2) \
                    or ref[u"分母の確かめ(前の記録の数と違えば結果の文書にそう書く)"][u"札つきの行の全部"] != 4 or REF_KEY in ref:
                out.append(u"参考(2 つの束を除いた数)が手計算と違う(行 R1・R2・R3・R5 の 4 行だけ)")
            if pr[u"分母の確かめ(前の記録の数と違えば結果の文書にそう書く)"][u"札つきの行の全部"] != 6:
                out.append(u"全部の行の数が 2 つの束を除いた数に変わっている")
        want_pred = {
            u"LX-1 L-S の止めた行 / V 「範囲」の札": od([(u"行", 2), (u"主の席", 1), (u"副の席", 0), (u"語の表", 2)]),
            u"LX-2 L-S の止めた行 / V 「範囲」の札(KAM と YS)": od([(u"行", 1), (u"主の席", 0), (u"副の席", 0), (u"語の表", 1)]),
            u"LX-3 L-S の止めた行 / G 札 a": od([(u"行", 1), (u"主の席", 1), (u"副の席", 0), (u"語の表", 0)]),
            u"LX-4 L-P の止めた行 / V 「見積り・計画」の札": od([(u"行", 1), (u"主の席", 1), (u"副の席", 1), (u"語の表", 1)]),
            u"LX-5 L-P の止めた行 / V 「見積り・計画」の札(YS)": od([(u"行", 0), (u"主の席", 0), (u"副の席", 0), (u"語の表", 0)]),
            u"LX-6 L-P の止めた行 / G 札 a": od([(u"行", 1), (u"主の席", 0), (u"副の席", 0), (u"語の表", 0)]),
            u"LX-7 L-S の止めた行 / G 札 b のうち「違うもの」が範囲": od([(u"行", 1), (u"主の席", 0), (u"副の席", 1), (u"語の表", 0)])}
        for k, v in want_pred.items():
            if pr.get(k) != v:
                out.append(u"予測の判定に要る数が手計算と違う: %s → %s" % (k[:5], pr.get(k)))
        lx8 = pr[u"LX-8 L-U の止めた行(V 「範囲」と「見積り・計画」の合わせ / G 札 a)と W-U との差(席 − 語の表)"]
        if lx8[u"V 「範囲」と「見積り・計画」の合わせ"] != od([(u"行", 3), (u"主の席", 2), (u"副の席", 1), (u"語の表", 3)]) or lx8[u"V の差(主の席 − 語の表)"] != -1 or lx8[u"G 札 a の差(主の席 − 語の表)"] != 1:
            out.append(u"LX-8 の数が手計算と違う")
        lx9 = pr[u"LX-9 L-U の止めた行 / 行(V 「それ以外」の札と、「範囲」と「見積り・計画」の合わせ)と率の差(ポイント。合わせ − それ以外)"]
        if lx9[u"率の差(ポイント)"] != u"-33.33" or lx9[u"V 「それ以外」の札"][u"分子"] != 1 or lx9[u"V 「範囲」と「見積り・計画」の合わせ"][u"分子"] != 2:
            out.append(u"LX-9 の数が手計算と違う")
        lx10 = pr[u"LX-10 2 つの席の答えの一致(札つきの行の全部)"]
        if (lx10[u"範囲"][u"分子"], lx10[u"範囲"][u"分母"], lx10[u"性質"][u"分子"], lx10[u"性質"][u"分母"]) != (1, 4, 3, 4) or pr[u"LX-11 主の席の答えなしの行"] != 1:
            out.append(u"LX-10・LX-11 の数が手計算と違う")
        ag = g(u"札つきの行の全部")[u"2 つの席の一致"]
        if ag != od([(u"両方の席に答えが在る行", 4), (u"範囲が同じ答えの行", 1), (u"性質が同じ答えの行", 3), (u"範囲と性質の両方が同じ答えの行", 1), (u"どちらかの席が答えなしの行", 2), (u"両方の席が答えなしの行", 0)]):
            out.append(u"2 つの席の一致の数が手計算と違う: %s" % (ag,))
        c = rec[K_CALLS]
        if (c[u"主"][u"呼び出しの数(HTTP の再試行を除く。中断した呼び出しを除く)"], c[u"主"][u"答えのやり直し(封 §2-3)"], c[u"主"][u"答えなしの行"]) != (7, 1, 1) or \
                (c[u"副"][u"呼び出しの数(HTTP の再試行を除く。中断した呼び出しを除く)"], c[u"副"][u"答えのやり直し(封 §2-3)"], c[u"副"][u"答えなしの行"]) != (7, 1, 1):
            out.append(u"呼び出しの記録の数が手計算と違う")
        if c[u"主"][u"返った block の type の並びの種類"] != od([(u"thinking,text", 7)]) or c[u"主"][u"stop_reason の種類"] != od([(u"end_turn", 7)]) or c[u"主"][u"入力 token の合計"] != 700 or c[u"副"][u"入力 token の合計"] != 350 or abs(c[u"USD の全部"] - USD_ALL) > 1e-9 \
                or abs(c[u"主"][u"USD 合計"] - 0.007) > 1e-9 or abs(c[u"副"][u"USD 合計"] - 0.00525) > 1e-9:
            out.append(u"呼び出しの記録の token・USD・block・stop_reason が手計算と違う(主の席 7 回 × 0.001・副の席 7 回 × 0.00075)")
        if abs(rec[u"費用"][u"使った額 USD"] - USD_ALL) > 1e-9:
            out.append(u"使った額が手計算(主 0.007 + 副 0.00525)と違う")
    finally:
        tmp.close()
    return out


def retry_problems(ms=None):
    u"""429 は最大 2 回(待ち 2 秒・8 秒)で再試行・それでも返らなければ 1 回の呼び出しとして答えのやり直し・返らない呼び出しは 1 回ごとに見積りの額で数える・HTTP 400 は全体を止める。"""
    ms = ms or MS
    out = []
    w = World(ms)
    items = collect(ms, w)[0][:1]
    est = ms.estimate_usd(len(items[0][u"prompt"]))
    tmp = Temp()
    try:
        waits = []

        def seq(n, model, prompt):
            if n <= 2:
                return 429, b""
            return None
        st = ms.new_state()
        ms.run_calls(items, st, tmp.p(u"a"), FAKE_KEY, transport=w.transport(seq=seq), sleep=waits.append, say=quiet, rows_limit=1)
        first = st[u"calls"][0]
        if waits != [2, 8] or first[u"retries"] != 2 or first[u"http_status"] != 200 or first[u"answer"] is None:
            out.append(u"429 の再試行(待ち 2 秒・8 秒・最大 2 回)が違う: %s %s" % (waits, first[u"retries"]))
        if abs(first[u"est_counted_usd"] - 2 * est) > 1e-5 or abs(first[u"cost_usd"] - (2 * est + 0.001)) > 1e-5 or len(st[u"calls"]) != 2:
            out.append(u"返らなかった呼び出しを 1 回ごとに見積りの額で数えない: %s" % (first[u"est_counted_usd"],))
        # 3 回とも 429(再試行は 2 回まで)→ 返らない 1 回目。もう 1 回(答えのやり直し)は通る
        st2 = ms.new_state()
        seq2 = lambda n, model, prompt: (429, b"") if n <= 3 else None
        ms.run_calls(items, st2, tmp.p(u"b"), FAKE_KEY, transport=w.transport(seq=seq2), sleep=quiet, say=quiet, rows_limit=1)
        c0 = st2[u"calls"][0]
        if c0[u"http_status"] != 429 or c0[u"retries"] != 2 or c0[u"answer"] is not None or abs(c0[u"cost_usd"] - 3 * est) > 1e-5 or c0[u"attempt"] != 1 or st2[u"calls"][1][u"attempt"] != 2:
            out.append(u"再試行しても返らなかった呼び出しの扱いが違う(答えのやり直しへ進む・3 回分の見積りの額)")
        # 通信の失敗(status None)・usage の無い 200 も見積りの額
        st3 = ms.new_state()
        seq3 = lambda n, model, prompt: (None, b"URLError") if n == 1 else ((200, json.dumps({"content": [{"type": "text", "text": u"x"}], "stop_reason": "end_turn"}).encode()) if n == 2 else None)
        ms.run_calls(items, st3, tmp.p(u"c"), FAKE_KEY, transport=w.transport(seq=seq3), sleep=quiet, say=quiet, rows_limit=1)
        if abs(st3[u"calls"][0][u"est_counted_usd"] - est) > 1e-5 or abs(st3[u"calls"][1][u"est_counted_usd"] - est) > 1e-5:
            out.append(u"通信の失敗・usage の無い返事を見積りの額で数えない")
        # HTTP 400 で全体を止める(state に残る)
        st4 = ms.new_state()
        n400 = []

        def t400(prompt, model, key):
            n400.append(1)
            return 400, b'{"error":"x"}'
        r = stops(ms, ms.run_calls, items, st4, tmp.p(u"d"), FAKE_KEY, t400, quiet, quiet, 1)
        if r is not True or len(n400) != 1 or st4[u"calls"][0][u"http_status"] != 400 or not st4[u"stopped"]:
            out.append(u"HTTP 400 で全体を止めない(1 回で止まり理由を残す)")
        if FAKE_KEY in ms.dumps(st4) or FAKE_KEY in ms.dumps(st):
            out.append(u"鍵が途中の答えに出る")
    finally:
        tmp.close()
    return out


def cap_problems(ms=None):
    u"""上限: 走らせる前の見積り(最大の回数で)が上限を超えたら 1 回も呼ばない・走っている間は使った額 + 次の見積りが上限を超えるなら止まり、使った額は上限を超えない。"""
    ms = ms or MS
    out = []
    w = World(ms)
    items = collect(ms, w)[0]
    ests = [ms.estimate_usd(len(it[u"prompt"])) for it in items]
    max_est = sum(ests) * 2 * 2
    one_est = sum(ests) * 2
    tmp = Temp()
    try:
        if abs(ms.max_estimate(items, ms.new_state())[0] - max_est) > 1e-9 or ms.max_estimate(items, ms.new_state())[1] != 24:
            out.append(u"走らせる前の見積りが(最大の回数 = 行 × 席 × 2)でない")
        if abs(ms.max_estimate(items, ms.new_state(), 5, True)[0] - sum(ests[:5]) * 2) > 1e-9:
            out.append(u"試しの見積り(頭の行・1 回ずつ)が違う")
        # (1) 走らせる前の見積りが上限を超える → 1 回も呼ばない・置き場に何も書かない
        tr = w.transport()
        st = ms.new_state()
        r = stops(ms, ms.run_calls, items, st, tmp.p(u"a"), FAKE_KEY, tr, quiet, quiet, None, False, max_est - 1e-6)
        if r is not True or tr.n or os.path.exists(tmp.p(u"a")):
            out.append(u"走らせる前の見積りが上限を超えるのに 1 回も呼ばずに止まらない")
        # 上限ちょうどなら通る(超えたら、の比較)
        st = ms.new_state()
        tr = w.transport()
        ms.run_calls(items, st, tmp.p(u"a2"), FAKE_KEY, tr, quiet, quiet, None, False, max_est + 1e-6)
        if len(tr.n) != 14:
            out.append(u"見積りが上限に収まるのに呼べない")
        # (2) 走っている間: 返らない呼び出し(429)が見積りの額を積むので、走る前の見積りを通っても途中で上限に届く
        cap = max_est * 1.2
        st = ms.new_state()
        tr = w.transport(seq=lambda n, model, prompt: (429, b""))
        r = stops(ms, ms.run_calls, items, st, tmp.p(u"b"), FAKE_KEY, tr, quiet, quiet, None, False, cap)
        if r is not True or not st[u"stopped"] or ms.state_cost(st) > cap + 1e-9 or not tr.n:
            out.append(u"走っている間に使った額が上限に届くのに止まらない(使った額 %s・上限 %s)" % (ms.state_cost(st), cap))
        n_stop = len(tr.n)
        # 止めた後の続き(--resume)も、使った額を引き継いで上限を超えない
        r = stops(ms, ms.run_calls, items, st, tmp.p(u"b"), FAKE_KEY, tr, quiet, quiet, None, False, cap)
        if r is not True or ms.state_cost(st) > cap + 1e-9:
            out.append(u"続きが使った額を引き継がない")
        if len(tr.n) != n_stop:
            out.append(u"上限に届いたあとの続きで更に呼ぶ")
        st = ms.new_state()
        tr = w.transport()
        # 試し(1 回ずつ)の上限: 1 行目の 1 席の見積りより小さければ走る前に止まる
        r = stops(ms, ms.run_calls, items, st, tmp.p(u"d"), FAKE_KEY, tr, quiet, quiet, 1, True, ests[0] * 1.5)
        if r is not True or tr.n:
            out.append(u"試しの見積りが上限を超えるのに止まらない")
        if one_est >= max_est:
            out.append(u"門の前提(最大 = 2 倍)が崩れている")
    finally:
        tmp.close()
    return out


def resume_problems(ms=None):
    u"""試し(頭 5 行 × 2 席・1 回ずつ)→ ``--resume``(済んだ(行, 席)は呼ばない・試しの額と読めなかった 1 回目を引き継ぐ)・中断した呼び出しは見積りの額で数える・置き場の取り違えで止まる。"""
    ms = ms or MS
    out = []
    w = World(ms)
    tmp = Temp()
    try:
        tr = w.transport()
        st = run_world(ms, w, tmp, transport=tr, trial=True)
        if len(tr.n) != 10 or len(st[u"calls"]) != 10:
            out.append(u"試しが頭 5 行 × 2 席の 10 回でない(%d)" % len(tr.n))
        if any(c[u"row"] >= 5 for c in st[u"calls"]):
            out.append(u"試しが頭 5 行を越えて呼ぶ")
        # 試しは 1 回だけ: 行 3(主は 1 回目で読める)・行 2 副(読めない)は 2 回目を呼ばない
        if len(ms.seat_attempts(st, 2, ms.SEATS[1])) != 1 or ms.seat_answer(st, 2, ms.SEATS[1]) is not None or len(ms.seat_attempts(st, 4, ms.SEATS[0])) != 1:
            out.append(u"試しが 1 回より多く呼ぶ(読めない答えのやり直しは本番の続きで)")
        if stops(ms, run_world, ms, w, tmp, 6, tr, True) is not True:
            out.append(u"途中の答えが在るのに試しをやり直せる")
        if stops(ms, run_world, ms, w, tmp, 6, tr, False, False) is not True:
            out.append(u"途中の答えが在るのに --resume なしで続けられる(有料の呼び出しを二度する)")
        n_trial = len(tr.n)
        rec = run_world(ms, w, tmp, transport=tr, resume=True)
        if len(tr.n) != 14:
            out.append(u"試しの後の続きの呼び出しの数が違う(全部で 14 回のはず・試しの答えを使い回す): %d" % len(tr.n))
        if len(tr.n) - n_trial != 4:
            out.append(u"続きが済んだ(行, 席)を呼び直している")
        if [r[:11] for r in rec[u"行"]] != w.expected_rows() or abs(rec[u"費用"][u"使った額 USD"] - USD_ALL) > 1e-9:
            out.append(u"試し → 続きの記録が通しの記録(手計算)と違う")
        if stops(ms, run_world, ms, w, tmp, 6, tr, False, True) is not True:
            out.append(u"記録が在るのに本番を走らせられる")
        # 置き場の指示文が今と違えば止まる
        tmp2 = Temp()
        try:
            run_world(ms, w, tmp2, transport=w.transport(), trial=True)
            w2 = World(ms)
            w2.books[0][u"units"][0][1][0][4] = u"売上高は100円でした(甲1)別。"
            if stops(ms, run_world, ms, w2, tmp2, 6, w2.transport(), False, True) is not True:
                out.append(u"途中の答えの指示文の sha256 が今と違うのに止まらない")
            # 返った text の file が書き換わっていれば止まる
            rp = ms.reply_path(tmp2.p(u"w", u"work"), 0, ms.SEATS[0], 1)
            with io.open(rp, "a", encoding="utf-8") as fh:
                fh.write(u"x")
            if stops(ms, run_world, ms, w, tmp2, 6, w.transport(), False, True) is not True:
                out.append(u"返った text が書き換わっているのに止まらない")
        finally:
            tmp2.close()
        # 置き場が repo の中なら、何も書かずに止まる(送った文を repo に置かない)
        inside = os.path.join(ROOT, u"lx_gate_inside_work")
        trn = w.transport()
        if stops(ms, run_world, ms, w, tmp, 6, trn, False, False, quiet, quiet, u"x", None, inside) is not True or trn.n or os.path.exists(inside):
            out.append(u"置き場が repo の中なのに止まらない・書いてしまう")
            shutil.rmtree(inside, ignore_errors=True)
        # 中断した呼び出し: 3 回目の transport で中断(KeyboardInterrupt)→ 次の走りで見積りの額で数える
        tmp3 = Temp()
        try:
            def boom(n, model, prompt):
                if n == 3:
                    raise KeyboardInterrupt()
                return None
            tr3 = w.transport(seq=boom)
            try:
                run_world(ms, w, tmp3, transport=tr3)
            except KeyboardInterrupt:
                pass
            else:
                out.append(u"中断が伝わらない")
            s3 = ms.load_state(tmp3.p(u"w", u"work"))
            if s3 is None or not s3[u"in_flight"] or len(s3[u"calls"]) != 2:
                out.append(u"呼ぶ前に残す印(in_flight)が無い")
            tr3b = w.transport()
            rec3 = run_world(ms, w, tmp3, transport=tr3b, resume=True)
            ab = [c for c in ms.load_state(tmp3.p(u"w", u"work"))[u"calls"] if c[u"aborted"]]
            if len(ab) != 1 or ab[0][u"cost_usd"] <= 0 or abs(ab[0][u"cost_usd"] - ab[0][u"est_usd"]) > 1e-9:
                out.append(u"中断した呼び出しを見積りの額で数えない")
            if abs(rec3[u"費用"][u"使った額 USD"] - (USD_ALL + ab[0][u"cost_usd"])) > 1e-6:
                out.append(u"中断した呼び出しの額が使った額に入らない")
            if [r[:11] for r in rec3[u"行"]] != w.expected_rows():
                out.append(u"中断の後の続きの記録が手計算と違う")
        finally:
            tmp3.close()
    finally:
        tmp.close()
    return out


def leak_problems(ms=None):
    u"""鍵の字が置き場の全部の file・記録・例外・途中の答えに出ない。記録は書く前と書いた後に検査される。"""
    ms = ms or MS
    out = []
    w = World(ms)
    tmp = Temp()
    try:
        log = []
        tr = w.transport(log=log)
        rec = run_world(ms, w, tmp, transport=tr)
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
        for tok in (u"甲1", u"経営成績", u"監査上の項目", u"売上高", u"読めません", u"答えです", FAKE_KEY):
            if tok in text:
                out.append(u"記録に文・見出し・返った text・鍵の字が在る: %s" % tok[:2])
        bad = [k for k in walk(rec) if k in (u"span", u"value", u"recomputed", u"文", u"sentence", u"text", u"数", u"元の字", u"後の字", u"新しい値", u"docID", u"name")]
        if bad:
            out.append(u"記録に置いてはいけない欄が在る: %s" % bad[:3])
        if DOCID_RE.search(text):
            out.append(u"記録に docID の形の字が在る")
        # 鍵の検査: 値そのもの・鍵の形が記録に入れば書かずに止まる
        r2 = copy.deepcopy(rec)
        r2[u"step"] = r2[u"step"] + u" " + FAKE_KEY
        if stops(ms, ms.record_text, r2, FAKE_KEY) is not True:
            out.append(u"鍵の値が記録に入っても止まらない")
        r3 = copy.deepcopy(rec)
        r3[u"step"] = r3[u"step"] + u" sk-abcdefghijklmnop1234"
        if stops(ms, ms.record_text, r3) is not True:
            out.append(u"鍵の形の字が記録に入っても止まらない")
        r4 = copy.deepcopy(rec)
        r4[u"行"][0][0] = u"sk-" + u"a" * 40
        if stops(ms, ms.write_record, tmp.p(u"leak.json"), r4, FAKE_KEY) is not True or os.path.exists(tmp.p(u"leak.json")):
            out.append(u"鍵の形の字が行に入っても書かずに止まらない")
        r5 = copy.deepcopy(rec)
        r5[u"文"] = u"x"
        if stops(ms, ms.record_text, r5) is not True:
            out.append(u"置いてはいけない欄が入っても止まらない")
        if stops(ms, ms.write_record, tmp.p(u"w", u"answers.json"), rec) is not True:
            out.append(u"記録が既に在るのに書き直せる")
        # 鍵が無ければ(環境変数も無い)呼ぶ前に止まる
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
            want = {"model": model, "max_tokens": 200, "temperature": 0, "thinking": {"type": "between_tools"} if model == "claude-sonnet-5-5" else {"type": "disabled"},
                    "messages": [{"role": "user", "content": u"指示文 A"}]}
            if st != 200 or b != want:
                out.append(u"送る body の形が封(max_tokens 200・temperature 0・思考の指定・system なし・user の 1 message)と違う: %s" % model)
        if req.full_url != "https://api.anthropic.com/v1/messages" or req.get_method() != "POST" or req.get_header("Anthropic-version") != "2023-06-01":
            out.append(u"送り先・method・API の版が違う")
        if req.get_header("X-api-key") != FAKE_KEY or FAKE_KEY in req.data.decode("utf-8") or FAKE_KEY in req.full_url:
            out.append(u"鍵が header だけに入っていない(body・URL に入っている)")
        if "system" in json.loads(req.data.decode("utf-8")):
            out.append(u"system を送っている")

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
    u"""``--dry-run``: 鍵を読まず(``get_key`` を呼ばない・環境変数が無くても走る)・通信せず(``urlopen`` が来たら落ちる)・記録を書かず・文を印字せず・数を出す。行の数が 421 でなければ止まる。"""
    ms = ms or MS
    out = []
    w = World(ms)
    lines = []
    saved = os.environ.pop(ms.KEY_ENV, None)

    def no_net(*a, **k):
        raise AssertionError(u"通信した")

    def no_key():
        raise AssertionError(u"鍵を読んだ")
    try:
        with patched(ms.SC, build_labels=lambda r: list(w.labels)), patched(ms.PA, engine_fp=lambda rt: od()), patched(ms, EXPECT_ROWS=6), patched(urllib.request, urlopen=no_net), patched(ms, get_key=no_key, call_api=no_net):
            res = ms.dry_run(root=ROOT, recs=copy.deepcopy(w.recs), inputs=[], books=copy.deepcopy(w.books), say=lines.append)
        text = u"\n".join(lines)
        if len(res[u"items"]) != 6 or res[u"chars"] != sum(len(i[u"prompt"]) for i in res[u"items"]):
            out.append(u"dry-run が組んだ指示文の数・字数が違う")
        if any(tok in text for tok in (u"甲1", u"売上高", u"経営成績", u"監査上の項目")):
            out.append(u"dry-run が材料の文を印字する")
        for need in (u"行の数: 6", u"席ごとの本数", u"字数の合計", u"見積り", u"配線の確認", u"通信していない"):
            if need not in text:
                out.append(u"dry-run の出力に %s が無い" % need)
        if not all(res[u"self_test"].values()) or len(res[u"self_test"]) != 5:
            out.append(u"dry-run の作り物の transport の検査が 5 つ全部通らない")
        if abs(res[u"est_max_usd"] - 2 * res[u"est_usd"]) > 1e-9:
            out.append(u"dry-run の見積り(最大 = やり直しを入れた 2 倍)が違う")
        with patched(ms.SC, build_labels=lambda r: list(w.labels)), patched(ms.PA, engine_fp=lambda rt: od()), patched(urllib.request, urlopen=no_net), patched(ms, get_key=no_key):
            if stops(ms, ms.dry_run, root=ROOT, recs=copy.deepcopy(w.recs), inputs=[], books=copy.deepcopy(w.books), say=quiet) is not True:
                out.append(u"行の数が 421 でないのに dry-run が止まらない")
        if ms.CACHE_DIR in text:
            out.append(u"dry-run が置き場の path を出す")
    finally:
        if saved is not None:
            os.environ[ms.KEY_ENV] = saved
    return out


def check_cmd_problems(ms=None):
    u"""``--check``: 記録の答えから数を作り直して照らし(行・呼び出しの欄を 1 つ変えれば止まる)、材料から指示文を組み直して行ごとの sha256 を照らす(材料の字が変われば止まる)。鍵・通信なし。"""
    ms = ms or MS
    out = []
    w = World(ms)
    tmp = Temp()
    try:
        rec = run_world(ms, w, tmp)
        text = ms.dumps(rec)

        def chk(r, books=None):
            with patched(ms.SC, build_labels=lambda x: list(w.labels)), patched(ms.PA, engine_fp=lambda rt: od()), patched(ms, EXPECT_ROWS=6), patched(urllib.request, urlopen=lambda *a, **k: 1 / 0):
                return ms.check(root=ROOT, rec=r, recs=copy.deepcopy(w.recs), inputs=[], books=copy.deepcopy(books if books is not None else w.books), say=quiet)
        try:
            chk(json.loads(text, object_pairs_hook=collections.OrderedDict))
        except BaseException as exc:                      # noqa: BLE001
            out.append(u"作った記録を --check が通さない(%s)" % type(exc).__name__)
        muts = []

        def mut(fn, why):
            r = json.loads(text, object_pairs_hook=collections.OrderedDict)
            fn(r)
            muts.append((r, why))
        mut(lambda r: r[u"行"][0].__setitem__(7, u"全体"), u"行の主の席の範囲を 1 つ替える")
        mut(lambda r: r[u"行"][2].__setitem__(10, u"実績"), u"行の副の席の性質だけを 1 つ替える(答えなしの片方だけ)")
        mut(lambda r: r[u"行"][2].__setitem__(9, u"全体"), u"行の副の席の範囲を 1 つ替える(答えなし → 全体)")
        mut(lambda r: r[u"行"][0].__setitem__(12, 2), u"行の呼び出しの数を替える")
        mut(lambda r: r[u"行"][1].__setitem__(11, u"0" * 64), u"行の指示文の sha256 を替える")
        mut(lambda r: r[u"行"][3].__setitem__(14, False), u"行の「文に元から 【 か 】 が在る」の欄を替える")
        mut(lambda r: r[u"行"][5].__setitem__(15, False), u"行の「見出しに元から 【 か 】 が在る」の欄を替える")
        mut(lambda r: r[K_PRED].pop(REF_KEY), u"参考の欄を落とす")
        mut(lambda r: r[u"呼び出し"][0].__setitem__(2, 2), u"呼び出しの欄の答えの回を替える")
        mut(lambda r: r[u"呼び出し"][0].__setitem__(10, 0.5), u"呼び出しの欄の USD を替える")
        mut(lambda r: r[K_TALLY][u"V 「範囲」の札"][u"全体"].__setitem__(u"行", 3), u"数えた欄の行の数を替える")
        mut(lambda r: r[K_PRED].__setitem__(u"LX-11 主の席の答えなしの行", 0), u"予測の判定に要る数を替える")
        mut(lambda r: r.__setitem__(u"この script の sha256", u"0" * 64), u"script の sha256 を替える")
        mut(lambda r: r[K_WIRE].__setitem__(u"札の数", 9), u"配線の確認の数を替える")
        mut(lambda r: r[K_CALLS][u"主"].__setitem__(u"答えなしの行", 0), u"呼び出しの記録の数を替える")
        for r, why in muts:
            if stops(ms, chk, r) is not True:
                out.append(u"--check が止まらない: %s" % why)
        w2 = World(ms)
        w2.books[0][u"units"][0][1][1][4] = u"売上高は200円の予定です(甲2)別。"
        if stops(ms, chk, json.loads(text, object_pairs_hook=collections.OrderedDict), w2.books) is not True:
            out.append(u"--check が材料の字の変更(指示文の sha256 の違い)で止まらない")
        r = json.loads(text, object_pairs_hook=collections.OrderedDict)
        r[u"行"][0][0] = u"KAM"
        if stops(ms, chk, r) is not True:
            out.append(u"--check が行の鍵の変更で止まらない")
        if not os.path.exists(os.path.join(ROOT, RECORD_REL)) and stops(ms, ms.check, ROOT, rec=None, recs=copy.deepcopy(w.recs), inputs=[], books=copy.deepcopy(w.books), say=quiet) is not True:
            out.append(u"記録が無いのに --check が止まらない")
    finally:
        tmp.close()
    return out


# ---------------------------------------------------------------- 5. 配線(import・予約名・境界)
def import_problems(src=None):
    u"""script の import は標準ライブラリの一覧だけ(通信は ``urllib`` の 1 つだけ。subprocess・socket 等は無い)。eval・exec・動的 import が無い。前の便の script は便 PA と aiforms_gen の 2 本だけ。
    環境変数は ``get_key`` の 1 か所だけが読む。``.env`` を読まない。``dry_run``・``check``・``collect_items``・``self_test`` は ``get_key``・``call_api`` を呼ばない。"""
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
    if sorted(c.args[0].value for c in loads if c.args and isinstance(c.args[0], ast.Constant)) != ["xbrl_aiforms_gen_2026-11-03.py", "xbrl_plan_attr_2026-11-19.py"]:
        out.append(u"読む前の便の script が便 PA と aiforms_gen の 2 本だけでない")
    env_uses = [n for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "os" and n.attr in ("environ", "getenv")]
    if len(env_uses) != 1:
        out.append(u"環境変数を読む所が 1 か所でない(%d)" % len(env_uses))
    funcs = dict((n.name, n) for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    gk = funcs.get("get_key")
    if gk is None or not any(u.lineno >= gk.lineno and u.lineno <= max(getattr(x, "lineno", 0) for x in ast.walk(gk)) for u in env_uses):
        out.append(u"環境変数を読むのが get_key の中でない")
    for fname in ("dry_run", "check", "collect_items", "collect_books", "items_from_books", "self_test", "build_record", "derived_sections"):
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


# ---------------------------------------------------------------- 6. 記録が在るときだけ(結果の門の前の分岐)
def record_problems(ms=None):
    u"""記録が在れば、記録の形・書かないものが無い・行と呼び出しの欄から数を作り直せる、を見る。記録が無ければ「無い」を返す(検査は結果の門に置く)。"""
    ms = ms or MS
    p = os.path.join(ROOT, RECORD_REL)
    if not os.path.exists(p):
        return None
    rec = load_json(RECORD_REL)
    out = []
    recs = ms.load_all_records(ROOT)
    labels = ms.SC.build_labels(recs)
    if rec.get(u"seal") != SEAL_REL or rec.get(u"封の commit") != SEAL_COMMIT_SHORT or rec.get(u"行の欄") != ms.ROW_COLUMNS or rec.get(u"呼び出しの欄") != ms.CALL_COLUMNS:
        out.append(u"記録の封・commit・欄の形が決めと違う")
    if len(rec.get(u"行", [])) != EXPECT_ROWS_PIN or rec.get(u"key_leaks") != []:
        out.append(u"記録の行の数が 421 でないか key_leaks が空でない")
    now = ms.derived_sections(rec[u"行"], rec[u"呼び出し"], labels, recs[u"sc"], recs[u"pa"])
    for k, v in now.items():
        if ms.dumps(rec[k]) != ms.dumps(v):
            out.append(u"記録の欄が行・呼び出しの欄から作り直した数と違う: %s" % k)
    try:
        ms.check_text(rec, ms.dumps(rec) + u"\n")
    except SystemExit:
        out.append(u"記録に置いてはいけない欄か鍵らしい字が在る")
    if DOCID_RE.search(read(RECORD_REL)):
        out.append(u"記録に docID の形の字が在る")
    return out


# ---------------------------------------------------------------- 変異(script)
#: (名前, script の中の字 old, new, 赤になるはずの検査の名前の並び)。old は script に 1 回だけ在る字
MUTANTS = (
    (u"M01 封の commit の定数を替える", u'SEAL_COMMIT = "198961e6"', u'SEAL_COMMIT = "198961e7"', ("seal",)),
    (u"M02 指示文の 1 字を替える(でください → てください)", u"渡した字だけで判断し、推測で埋めないでください。", u"渡した字だけで判断し、推測で埋めてください。", ("seal", "prompt")),
    (u"M03 指示文の問い 2 の「実績」の字を替える", u"- 実績\n- 計画・予想", u"- 実積\n- 計画・予想", ("seal", "prompt")),
    (u"M04 【 の字を替える", u'MARK_OPEN, MARK_CLOSE = u"【", u"】"', u'MARK_OPEN, MARK_CLOSE = u"「", u"】"', ("seal", "mark", "items")),
    (u"M05 【 】が空白を含めて前に付く(span(1) → span(0))", u"    return m.span(1)", u"    return m.span(0)", ("mark",)),
    (u"M06 【 】が万億兆でつながる組を囲まない", u'u"(?:[兆億万](?:" + _X + u")?)*)")', u'u"(?:(?:" + _X + u")?)*)")', ("mark",)),
    (u"M07 【 】の後ろを数の字の後ろでなく文の終わりに入れる", u"    return s[:a] + MARK_OPEN + s[a:b] + MARK_CLOSE + s[b:]", u"    return s[:a] + MARK_OPEN + s[a:] + MARK_CLOSE", ("mark", "items")),
    (u"M08 見出しが無いときの字を空にする", u"values = {u\"{HEADING}\": NO_HEADING if heading is None else heading", u"values = {u\"{HEADING}\": u\"\" if heading is None else heading", ("prompt", "items")),
    (u"M09 置き換えを 1 回の走査でなく順に replace", u"    return _PH_RE.sub(lambda m: values[m.group(0)], PROMPT_TEMPLATE)", u"    return PROMPT_TEMPLATE.replace(u\"{HEADING}\", values[u\"{HEADING}\"]).replace(u\"{SENTENCE}\", values[u\"{SENTENCE}\"])", ("prompt",)),
    (u"M10 L-S が member の欄を問わない", u"ls = answer[0] == PART and bool(empty)", u"ls = answer[0] == PART", ("stops", "answers")),
    (u"M11 L-P が member が空の行だけ", u"lp = answer[1] == PLAN\n", u"lp = answer[1] == PLAN and bool(empty)\n", ("stops", "answers")),
    (u"M12 「分からない」も一部分として止める", u"ls = answer[0] == PART and bool(empty)", u"ls = answer[0] in (PART, u\"分からない\") and bool(empty)", ("stops", "answers")),
    (u"M13 答えなしを止めるに数える", u"    if answer is None:\n        return False, False, False", u"    if answer is None:\n        return True, True, True", ("stops", "answers")),
    (u"M14 やり直しを 0 回にする", u"MAX_ANSWER_ATTEMPTS = 2 ", u"MAX_ANSWER_ATTEMPTS = 1 ", ("seal", "answers", "cap", "resume")),
    (u"M15 席の名(副)を替える", u'SEATS = ("claude-sonnet-5-5", "claude-haiku-5-5")', u'SEATS = ("claude-sonnet-5-5", "claude-haiku-5-4")', ("seal", "answers")),
    (u"M16 席の名(主)を替える", u'SEAT_TAG = collections.OrderedDict([("claude-sonnet-5-5", u"主"), ("claude-haiku-5-5", u"副")])', u'SEAT_TAG = collections.OrderedDict([("claude-sonnet-5-5", u"副"), ("claude-haiku-5-5", u"主")])', ("seal", "answers")),
    (u"M17 max_tokens を替える", u"MAX_TOKENS = 200\n", u"MAX_TOKENS = 400\n", ("seal", "call")),
    (u"M18 temperature を替える", u"TEMPERATURE = 0\n", u"TEMPERATURE = 1\n", ("seal", "call")),
    (u"M19 思考の指定(主)を替える", u'THINKING = {"claude-sonnet-5-5": {"type": "between_tools"}', u'THINKING = {"claude-sonnet-5-5": {"type": "disabled"}', ("seal", "call")),
    (u"M20 上限を替える", u"COST_CAP_USD = 15.0 ", u"COST_CAP_USD = 20.0 ", ("seal",)),
    (u"M21 出力の単価を替える", u"PRICE_OUT = 25.0", u"PRICE_OUT = 15.0", ("seal", "stops")),
    (u"M22 行の数の定数を替える", u"EXPECT_ROWS = 421 ", u"EXPECT_ROWS = 420 ", ("seal",)),
    (u"M23 試しの行数を替える", u"TRIAL_ROWS = 5 ", u"TRIAL_ROWS = 4 ", ("seal", "resume")),
    (u"M24 走っている間の上限の比較を外す", u'        if cum + meter["extra"] + est > cap:', u"        if False:", ("cap",)),
    (u"M25 走らせる前の見積りの比較を外す", u"    if base + est > cap:", u"    if False:", ("cap",)),
    (u"M26 返らなかった呼び出しを見積りの額で数えない", u'            meter["extra"] += est', u'            meter["extra"] += 0', ("retry", "cap")),
    (u"M27 走らせる前の見積りを 1 回ずつで数える(最大の回数でない)", u"    ma = 1 if one_attempt else MAX_ANSWER_ATTEMPTS", u"    ma = 1", ("cap",)),
    (u"M28 中断した呼び出しを見積りの額で数えない", u'(u"est_counted_usd", f[u"est_usd"]), (u"cost_usd", f[u"est_usd"]),', u'(u"est_counted_usd", 0.0), (u"cost_usd", 0.0),', ("resume",)),
    (u"M29 呼ぶ前の in_flight を残さない", u'                state[u"in_flight"] = od([(u"row", i)', u'                state[u"in_flight_x"] = od([(u"row", i)', ("resume",)),
    (u"M30 試しが 1 回で止まらない", u"    max_attempts = 1 if one_attempt else MAX_ANSWER_ATTEMPTS", u"    max_attempts = MAX_ANSWER_ATTEMPTS", ("resume",)),
    (u"M31 済んだ(行, 席)を呼び直す", u"                if seat_answer(state, i, seat) is not None or len(att) >= max_attempts:", u"                if len(att) >= max_attempts:", ("resume", "answers")),
    (u"M32 HTTP 400 で止めない", u"STOP_HTTP = (400, 401, 403)", u"STOP_HTTP = (401, 403)", ("seal", "retry")),
    (u"M33 stop_reason を見ない", u'    if stop_reason != "end_turn" or not isinstance(text, str) or not text:', u"    if not isinstance(text, str) or not text:", ("read",)),
    (u"M34 答えの語の前後の空白を落とさない", u"    a, b = a.strip(), b.strip()", u"    pass", ("read",)),
    (u"M35 最後の } でなく最初の } まで読む", u'    i, j = text.find(u"{"), text.rfind(u"}")', u'    i, j = text.find(u"{"), text.find(u"}")', ("read",)),
    (u"M36 語の一致を字の一部で見る", u"    if a not in RANGE_WORDS or b not in NATURE_WORDS:", u"    if not any(w in a for w in RANGE_WORDS) or not any(w in b for w in NATURE_WORDS):", ("read",)),
    (u"M37 記録の漏れの検査を呼ばない", u"    TSS.check_clean(rec, scan, key_value)", u"    pass", ("leak",)),
    (u"M38 途中の答えに鍵を書く", u'(u"script_sha256", script_sha[:16])', u'(u"script_sha256", key)', ("retry", "leak")),
    (u"M39 行の順を位置だけにする", u"    got.sort(key=lambda g: row_order(*[g[1][i] for i in range(5)]))", u"    got.sort(key=lambda g: g[1][4])", ("items", "answers")),
    (u"M40 送る行の数の確かめを外す", u"    if len(got) != expect:", u"    if False:", ("items",)),
    (u"M41 便 PA の記録の行の確かめを外す", u"    if missing:", u"    if False:", ("items",)),
    (u"M42 L-S の member の欄の読みを逆にする", u'rows.append([si, pos, SHORT[state], not r.get("member"), s,', u'rows.append([si, pos, SHORT[state], bool(r.get("member")), s,', ("unit",)),
    (u"M43 語の表の W-S を便 SC の段 1 から読む", u"        ws = sc_by[k][SC.C_H2] != u\"\"", u"        ws = sc_by[k][SC.C_H1] != u\"\"", ("answers",)),
    (u"M44 W-P を便 SC の記録から読む", u"        wp = pa_by[k][PA.C_H2] != u\"\"", u"        wp = sc_by[k][SC.C_H2] != u\"\"", ("answers",)),
    (u"M45 席の一致の範囲を性質で数える", u'(u"範囲が同じ答えの行", sum(1 for v in both if v[u"main"][0] == v[u"sub"][0]))', u'(u"範囲が同じ答えの行", sum(1 for v in both if v[u"main"][1] == v[u"sub"][1]))', ("answers",)),
    (u"M46 率の差の向きを逆にする", u"    return RT.point_diff(b_n, b_d, a_n, a_d)", u"    return RT.point_diff(a_n, a_d, b_n, b_d)", ("answers",)),
    (u"M47 記録の呼び出しの数に HTTP の再試行を入れる", u"len(seat_attempts(state, i, m)), len(seat_attempts(state, i, s)), it[u\"sent_bracket\"]", u"len(seat_attempts(state, i, m)) + 1, len(seat_attempts(state, i, s)), it[u\"sent_bracket\"]", ("answers", "check")),
    (u"M48 --check が指示文の sha256 を照らさない", u"    if [it[u\"prompt_sha256\"] for it in items] != [r[C_SHA] for r in rows] or \\", u"    if False or \\", ("check",)),
    (u"M49 --check が行から数を作り直して照らさない", u"        if dumps(rec[k]) != dumps(v):\n            raise Stop(u\"**記録の欄が行・呼び出しの欄から作り直した数と違う", u"        if False:\n            raise Stop(u\"**記録の欄が行・呼び出しの欄から作り直した数と違う", ("check",)),
    (u"M50 dry-run が鍵を読む", u"    items, wire, inputs, recs, fp, labels, material_cell = collect_items(root=root, procs=procs, material=material, cache_base=cache_base, say=say, **kw)\n    chars", u"    get_key()\n    items, wire, inputs, recs, fp, labels, material_cell = collect_items(root=root, procs=procs, material=material, cache_base=cache_base, say=say, **kw)\n    chars", ("dry", "import")),
    (u"M51 dry-run の作り物の transport の検査を外す", u"    checks = self_test(items, say)", u"    checks = od([(u\"x\", True)])", ("dry",)),
    (u"M52 入力の表の便 PA の記録の sha256 を替える", u'"53891449b95acaf4812cd77fbc3cb9ebc85573999df39b75f359ef87b69d5176"', u'"63891449b95acaf4812cd77fbc3cb9ebc85573999df39b75f359ef87b69d5176"', ("input_sha", "seal_table", "wire_inputs")),
    (u"M53 入力の sha256 の照合を外す", u"        if not os.path.isfile(p) or ST.sha256_file(p) != want:", u"        if False:", ("wire_inputs",)),
    (u"M54 入力の表から便 PA の script の行を落とす", u'    (24, "measure/xbrl_plan_attr_2026-11-19.py", "711c6ae73538a2140610dd64485a8b5bdf00f9439905a4a9dfdc7ea690eb054d"),\n', u"", ("input_sha", "seal_table", "wire_inputs")),
    (u"M56 封の追記の commit の定数を替える", u'SEAL_ADDENDUM_COMMIT = "a2ed6d0b"', u'SEAL_ADDENDUM_COMMIT = "a2ed6d0c"', ("seal",)),
    (u"M57 記録に封の追記の commit を書かない", u"    rec[u\"封の追記の commit\"] = SEAL_ADDENDUM_COMMIT\n", u"", ("answers",)),
    (u"M58 文に在る印と見出しに在る印を取り違える", u'(u"sent_bracket", sb), (u"head_bracket", hb)', u'(u"sent_bracket", hb), (u"head_bracket", sb)', ("items", "answers")),
    (u"M59 参考が 2 つの束を除かない", u'    pred[REF_KEY] = predictions([v for v in views if not (v[u"sb"] or v[u"hb"])])', u'    pred[REF_KEY] = predictions(views)', ("answers",)),
    (u"M60 参考が見出しの束だけ除く", u'if not (v[u"sb"] or v[u"hb"])])', u'if not v[u"hb"]])', ("answers",)),
    (u"M61 見出しの束が文の印で数える", u'for name, field in ((B_SENT, u"sb"), (B_HEAD, u"hb")):', u'for name, field in ((B_SENT, u"sb"), (B_HEAD, u"sb")):', ("answers",)),
    (u"M55 置き場が repo の中でも止めない", u"    if TSS.inside_repo(work):", u"    if False:", ("resume",)),
)


def check_by_name(name, mod, src):
    table = {u"seal": seal_problems, u"seal_table": seal_table_problems, u"input_sha": input_sha_problems, u"wire_inputs": input_wire_problems, u"mark": mark_problems, u"prompt": prompt_problems,
             u"read": read_problems, u"stops": stops_problems, u"unit": unit_problems, u"items": items_problems, u"answers": answers_problems, u"retry": retry_problems,
             u"cap": cap_problems, u"resume": resume_problems, u"leak": leak_problems, u"call": call_problems, u"dry": dry_problems, u"check": check_cmd_problems}
    if name in table:
        return table[name](mod)
    if name == u"import":
        return import_problems(src)
    raise AssertionError(name)


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
        self.assertEqual([], seal_table_problems())

    def test_a_2_the_seal_file_is_the_sealed_commit_and_unchanged(self):
        self.assertEqual([], seal_history_problems())

    def test_a_3_a_changed_seal_character_turns_the_comparison_red(self):
        seal = seal_text()
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"問い 2(性質)", u"問い 2(性格)")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"- 一部分", u"- 部分")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"`max_tokens` 200", u"`max_tokens` 300")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"**: 15 USD。", u"**: 16 USD。")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"主の席 = `claude-sonnet-5-5`", u"主の席 = `claude-sonnet-5-4`")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"鍵の昇順の頭 5 行", u"鍵の昇順の頭 6 行")))
        self.assertNotEqual([], seal_table_problems(seal=seal.replace(u"`711c6ae7`", u"`711c6ae8`")))
        self.assertEqual([], seal_problems(seal=seal))

    def test_a_5_the_section_8_cap_wins_over_the_old_section_3_figure(self):
        u"""§3 の「10 USD」が残っていても門が古い方を拾わない(§8 の置き換えの行が在れば §8 が勝つ)。§8 の行が無ければ §3 に戻る。"""
        seal = seal_text()
        self.assertEqual(15, seal_values(seal)["cap"])
        self.assertEqual([], seal_problems(seal=seal.replace(u"**上限**: 10 USD", u"**上限**: 11 USD")))           # §3 の字を替えても門は §8 を読む
        self.assertEqual(11, seal_values(seal.replace(u"**上限**: 10 USD", u"**上限**: 11 USD"))["cap3"])
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"**: 15 USD。", u"**: 14 USD。")))                 # §8 の数を替える
        no8 = seal.split(u"## §8 追記")[0]
        self.assertEqual(10, seal_values(no8)["cap"])
        self.assertNotEqual([], seal_problems(seal=no8))                                                          # §8 が無ければ §3 の 10 と script の 15 が違う

    def test_a_4_the_seal_has_one_prompt_block_and_the_values_are_read_from_it(self):
        seal = seal_text()
        v = seal_values(seal)
        self.assertEqual(("claude-sonnet-5-5", "claude-haiku-5-5"), v["seats"])
        self.assertEqual((200, 0, {"type": "between_tools"}, {"type": "disabled"}), v["shape"])
        self.assertEqual((15, (5, 25), (421, 2, 842), 1684, (5, 10), 421), (v["cap"], v["price"], v["calls"], v["max_calls"], v["trial"], v["rows"]))
        self.assertEqual((10, 15), (v["cap3"], v["cap8"]))
        self.assertEqual(((u"全体", u"一部分", u"分からない"), (u"実績", u"計画・予想", u"分からない")), v["words"])
        self.assertEqual(("711c6ae7", "53891449"), v["heads"])
        self.assertEqual(1, seal.count(u"```\n次は、日本の上場企業"))


class InputTest(unittest.TestCase):
    def test_b_1_the_inputs_have_the_pinned_sha256(self):
        self.assertEqual([], input_sha_problems())
        self.assertEqual(25, len(INPUT_SHAS))

    def test_b_2_the_input_check_stops_on_a_changed_byte(self):
        self.assertEqual([], input_wire_problems())

    def test_b_3_the_prior_seals_results_scripts_and_records_are_unchanged_since_the_seal(self):
        self.assertEqual([], prior_problems())
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, d)) for d in PRIOR_DOCS))


class EngineTest(unittest.TestCase):
    def test_c_1_the_engine_is_zero_lines_from_the_seal_commit(self):
        self.assertEqual([], engine_zero_problems())

    def _repo(self):
        r = PR.Repo()
        r.put(SEAL_REL)
        r.put("adapters/xbrl/instance.py", text=u"")
        r.put(PRIOR_DOCS[0])
        seal = r.commit(SEAL_REL, "adapters/xbrl/instance.py", PRIOR_DOCS[0])
        return r, seal

    def test_c_2_a_made_up_repo_with_an_engine_change_is_red(self):
        r, seal = self._repo()
        r.put("measure/s.py")
        r.commit("measure/s.py")
        self.assertEqual([], engine_zero_problems(r.d))
        self.assertEqual([], prior_problems(r.d))
        r.put("adapters/xbrl/instance.py", text=u"a\n")
        r.commit("adapters/xbrl/instance.py")
        self.assertNotEqual([], engine_zero_problems(r.d))
        r2, _s = self._repo()
        r2.put("core/py/audit_core/x.py")
        r2.commit("core/py/audit_core/x.py")
        self.assertNotEqual([], engine_zero_problems(r2.d))
        r3, _s = self._repo()
        r3.put("adapters/xbrl/instance.py", text=u"z\n")
        self.assertNotEqual([], engine_zero_problems(r3.d))

    def test_c_3_a_made_up_repo_with_a_changed_prior_document_is_red(self):
        r, seal = self._repo()
        r.put(PRIOR_DOCS[0], text=u"changed\n")
        self.assertNotEqual([], prior_problems(r.d))
        r.commit(PRIOR_DOCS[0])
        self.assertNotEqual([], prior_problems(r.d))


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
    def test_e_1_the_marks_go_only_on_the_number_the_claim_points_at(self):
        self.assertEqual([], mark_problems())

    def test_e_2_the_prompt_is_the_seal_block_with_two_places_replaced_in_one_scan(self):
        self.assertEqual([], prompt_problems())

    def test_e_3_the_answer_reading_follows_the_seal(self):
        self.assertEqual([], read_problems())

    def test_e_4_the_stopping_conditions_and_the_cost_arithmetic(self):
        self.assertEqual([], stops_problems())

    def test_e_5_unit_rows_use_the_real_function_on_made_up_sentences(self):
        self.assertEqual([], unit_problems())

    def test_e_6_the_seal_example_is_reproduced(self):
        self.assertEqual(u"当連結会計年度の売上高は【1,234】百万円となり、前期比 5.6% 増加しました。", MS.mark_sentence(SENT, SENT.index(u"1,234")))
        self.assertIn(u"見出し: (なし)\n文: 当連結会計年度の売上高は【1,234】百万円となり、前期比 5.6% 増加しました。\n", MS.build_prompt(None, MS.mark_sentence(SENT, SENT.index(u"1,234"))))


class PipelineTest(unittest.TestCase):
    def test_f_1_the_rows_are_chosen_ordered_and_the_wiring_checks_stop(self):
        self.assertEqual([], items_problems())

    def test_f_2_calls_reading_stopping_and_counting_agree_with_the_hand_computation(self):
        self.assertEqual([], answers_problems())

    def test_f_3_retries_unreturned_calls_and_http_400(self):
        self.assertEqual([], retry_problems())

    def test_f_4_the_cap_stops_before_and_while_running(self):
        self.assertEqual([], cap_problems())

    def test_f_5_trial_then_resume_and_interrupted_calls(self):
        self.assertEqual([], resume_problems())

    def test_f_6_the_key_never_reaches_a_file_a_record_or_an_exception(self):
        self.assertEqual([], leak_problems())

    def test_f_7_the_request_body_has_the_sealed_shape_without_any_network(self):
        self.assertEqual([], call_problems())

    def test_f_8_dry_run_reads_no_key_and_sends_nothing(self):
        self.assertEqual([], dry_problems())

    def test_f_9_check_rebuilds_the_numbers_and_the_prompt_hashes(self):
        self.assertEqual([], check_cmd_problems())

    def test_f_10_the_script_has_no_real_call_path_in_the_zero_cost_functions(self):
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


class WiringTest(unittest.TestCase):
    def test_h_1_the_script_imports_only_the_allowed_modules_and_reads_the_key_in_one_place(self):
        self.assertEqual([], import_problems())

    def test_h_2_the_boundary_import_list_is_not_widened(self):
        p = os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py")
        with open(p, encoding="utf-8") as fh:
            self.assertNotIn(u"llm_extract", fh.read())

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
                fh.write("LX_NOTES = 1\n")
            self.assertEqual([], reserved_problems(rel="g.py", base=d))

    def test_h_5_the_script_leaves_sys_modules_as_it_found_them(self):
        u"""前の便の script を読んでも、読み込みの前に居た名前を上書きしたまま残さない(門を 2 通りの順で走らせても赤くならない)。"""
        before = dict(sys.modules)
        mod = load_module(SCRIPT_REL, "llm_extract_script_for_sysmodules_check")
        changed = [k for k, v in before.items() if sys.modules.get(k) is not v]
        self.assertEqual([], changed)
        self.assertIn("llm_extract_script_for_sysmodules_check", sys.modules)
        del mod

    def test_h_6_the_import_check_sees_planted_violations(self):
        base = read(SCRIPT_REL)
        self.assertNotEqual([], import_problems(base + u"\nimport socket\n"))
        self.assertNotEqual([], import_problems(base + u"\nimport subprocess\n"))
        self.assertNotEqual([], import_problems(base + u"\nX = os.environ.get('A')\n"))
        self.assertNotEqual([], import_problems(base.replace(u"def self_test(items, say):\n", u"def self_test(items, say):\n    get_key()\n")))
        self.assertNotEqual([], import_problems(base.replace(u"def check(root=ROOT", u"def check_x(root=ROOT")))


class MutantTest(unittest.TestCase):
    def test_j_1_every_mutant_turns_its_checks_red_and_the_files_are_unchanged(self):
        before = (sha_of(SCRIPT_REL), sha_or_none(RECORD_REL), tuple(sha_of(r) for r in INPUT_RELS))
        modules_before = dict(sys.modules)
        results = run_mutants()
        after = (sha_of(SCRIPT_REL), sha_or_none(RECORD_REL), tuple(sha_of(r) for r in INPUT_RELS))
        self.assertEqual(before, after)
        self.assertEqual([], [k for k, v in modules_before.items() if sys.modules.get(k) is not v])
        silent = [(n, c) for n, res, _w in results for c, red in res if not red]
        self.assertEqual([], silent)
        self.assertEqual(len(MUTANTS), len(results))

    def test_j_2_the_unmutated_script_is_green_on_every_check(self):
        base = read(SCRIPT_REL)
        mod = load_source(base)
        for name in (u"seal", u"seal_table", u"input_sha", u"mark", u"prompt", u"read", u"stops", u"unit", u"items", u"answers", u"retry", u"cap", u"resume", u"leak", u"call", u"dry", u"check", u"import"):
            self.assertEqual([], check_by_name(name, mod, base), name)


if __name__ == "__main__":
    unittest.main()
