# -*- coding: utf-8 -*-
"""封 docs/XBRL_NONFUNCTIONAL_SEAL_2026-11-10.md(非機能の実測 NF ― verify_document 1 回の時間とメモリ。engine は変えない)の測定の門。封 §0-2・§1・§2・§4・§5・§6。

**この門が縛るもの**(結果の門 ``test_xbrl_nonfunc_result.py`` は記録・文書・N-1〜N-9 の判定・記録の形を縛る)

1. 封の字: §2 の予測の表が N-1〜N-9 の 9 行でどの行も欄・予測・外れ方を持つ・§4 の path(script・門 2 本・結果の文書)・§0-2 の記録の path・決めの要点(測るのは verify_document 1 回・子 process 1 つずつ並行なし・
   入力の読み込みは時計の外・門は時間を測り直さない・§1 の字)。封の字を 1 字変えると赤。
2. 封の字と script の定数が同じ: 封の path と commit(封 abe8f4d)・profile(P27・P33E)・回数 3・import の回数 5・記録と結果の文書の path・予測の幅(封の字から読んだ値を literal に留めた値と照らす)。
3. 触らない file は **封の commit の blob と同じ**: engine(``core/``・``adapters/``)・``measure/``(この便の script だけ新しい)・``fixtures/xbrl``(この便の記録だけ新しい)。未 commit の変更・追加も赤。
4. 順序: 封 abe8f4d ⊏ script・門 2 本(記録・結果の文書の順序は結果の門が見る)。未 commit は赤(skip にしない)。
5. 配線(ast と振る舞い): 時計の内側は ``verify_document`` の呼び出し 1 つだけ・入力の読み込みは時計の外・``Pool(1, maxtasksperchild=1)`` が 1 本・並行なし(1 回 = 子 process 1 つ・区間が重ならない)・
   ``run`` の順は (回, 材料の種類, 本, profile)・本番は ``--only``・``--reps`` 3 以外で記録を作らない・前の便の関数(``R97.make_jobs``・``RM.load_jobs``)を呼び同名を定義しない・
   script が読み込む前の便の script が ``sys.modules`` の名前を上書きしても、読み込みの前に居た名前は元の object へ戻る。
6. 新しい門が、既存の門が行頭の名前を数える変数名を行頭に置いていない。script・門に docID の字が無い。
7. 門の変異: 封の字・script の定数・順序・触らない file・配線を 1 つずつ壊した標本で上の検査が赤になる。

この file は docID の字を持たない(引きの門が追跡 file の docID を数える)。
"""
import ast
import collections
import importlib.util
import os
import re
import subprocess
import sys
import tempfile
import time
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, os.path.join(ROOT, "measure"))


def load_module(rel, name):
    u"""importlib で読み込む。読み込んだ file が中で読む前の便の script は、決まった名前で ``sys.modules`` に登録し直して**先に居た module を上書きする**。
    読み込みの前に居た名前は、読み込みの後に元の object へ戻す(さもないと pytest の引数で前の便の結果の門を先に並べたとき、先に読まれた門が持つ object と ``sys.modules`` の object が別になって赤くなる。7109c97 の直しと同じ形)。
    読み込んだ module 自身の名前 ``name`` は残す。"""
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


SGR = load_module("tests/measure/test_xbrl_rmix_seal.py", "rmix_seal_gate_for_nonfunc_seal")      # 順序・禁止名の部品。門としては走らせない
PR = SGR.PR
SC = load_module("measure/xbrl_nonfunc_2026-11-10.py", "nonfunc_script_for_seal_gate")

SEAL_REL = SC.SEAL_REL
SEAL_COMMIT_SHORT = "abe8f4d"                     # 封の最初の commit(literal に留める。script の定数と違えば script_problems が赤)
DOC_REL = SC.DOC_REL
SCRIPT_RELS = ("measure/xbrl_nonfunc_2026-11-10.py",)
GATE_RELS = ("tests/measure/test_xbrl_nonfunc_seal.py", "tests/measure/test_xbrl_nonfunc_result.py")
RECORD_REL = "fixtures/xbrl/nonfunc/timing_2026-11-10.json"
#: 封の commit から 0 行でなければならない path(engine・measure 全部・既存の記録)と、そこに新しく足してよい file(この便の script と記録)
NOT_TOUCHED_RELS = ("adapters", "core", "measure", "fixtures/xbrl")
ALLOWED_NEW = (SCRIPT_RELS[0], RECORD_REL)
#: 封の後の便が、日付と理由を書いて届けた新しい file(字で留める。``later_declared_problems`` が、engine の path でない・封の commit の木に無い(在る file の変更ではない)・
#: 届けを外すと「封の後に足された」と出る file とちょうど同じ、を見る。届けていない新しい file・在る file の変更は今も赤。この便が読む file は READ_ONLY_RELS の byte の一致で別に守る)
DECLARED_NEW_AFTER_SEAL = (
    # 2026-11-10: LB(札のある行だけの率。封 docs/XBRL_LABEL_ONLY_RATES_SEAL_2026-11-10.md 9ad2c7d0)の script。e91b48f9 で足されたときこの門への届けが漏れ、test_c_1 が赤のままだった(2026-11-12 に届けた)
    "measure/xbrl_labelonly_2026-11-10.py",
    # 2026-11-12: 止まった数字の「見る順」の診断(docs/XBRL_STOP_TRIAGE_DIAG_2026-11-12.md。封なし)。既に在る記録を数え直すだけで engine を呼ばない script 1 本と記録 1 つ
    "measure/xbrl_stop_triage_2026-11-12.py", "fixtures/xbrl/aiforms/stop_triage_2026-11-12.json",
)
#: 届けてよい file の置き場(engine の ``core/``・``adapters/`` は届けられない)
DECLARABLE_PREFIXES = ("measure/", "fixtures/xbrl/")
#: この便が読み込む前の便の script・読むだけの記録(封の commit の blob と byte が同じでなければならない)
READ_ONLY_RELS = (
    "measure/xbrl_pbind_2026-11-06.py", "measure/xbrl_rmix_2026-11-04.py", "measure/xbrl_rmix_regress97_2026-11-04.py", "measure/xbrl_pswap_idmap_2026-11-06.py", "measure/xbrl_pswap_2026-11-06.py",
    "measure/xbrl_numfix_2026-11-04.py", "measure/xbrl_p28_regress97_2026-11-02.py", "measure/inject.py", "measure/lib/numbers.py", "measure/lib/sites.py",
    "adapters/xbrl/verify_document.py", "adapters/xbrl/recipes.py", "adapters/xbrl/vocabulary.py",
    "fixtures/xbrl/pbind/regress97_2026-11-06.json", "fixtures/xbrl/tperiod/moves_200_2026-11-09.json", "fixtures/xbrl/numfix/ai200_2026-11-04.json")
RESERVED_PREFIXES = SGR.RESERVED_PREFIXES
DOCID_RE = SGR.DOCID_RE
PRED_IDS = tuple("N-%d" % i for i in range(1, 10))
#: 前の便の関数(この script は同名の関数を定義せず、前の便の module の関数を呼ぶ)。(module の別名, 関数名)
REUSED_FUNCS = (("R97", "make_jobs"), ("RM", "load_jobs"), ("RM", "caches_all"), ("GEN", "caches_snapshot"), ("GEN", "read_zip"), ("RUN", "read_text"), ("RUN", "write_record"), ("D", "record_key_leaks"))
#: 封の字の要点(封に無ければ赤)
SEAL_PHRASES = (
    u"測るのは `verify_document` 1 回(読み込み済みの入力に対する照合)",
    u"全部を 3 回ずつ、子 process 1 つずつ、並行なし(1 本の Pool(1))",
    u"入力の読み込み・ZIP の展開の外側・report の組版は時計の外",
    u"門は「文書の数が記録と同じ」を縛るだけで、時間を測り直して照らすことはしない",
    u"`time.perf_counter()` の差(秒)",
    u"1 回の時間 ÷ その回の claim の数",
    u"呼び出しの後の子 process の `ru_maxrss`",
    u"(最大 − 最小) ÷ 中央値",
    u"採用 / 不採用の判定は無い便",
    u"1 でも違えば材料か配線が違う",
    u"Pool(1, maxtasksperchild=1)",
    u"前から在る sys.modules の名前は戻す",
    u"並行の処理(何書類を同時に回せるか・throughput)は測らない",
)
#: 封 §2 の予測の幅(封の字を門が読み、ここに留めた値と照らす。留めた値が封の字と違えば赤)
BOUNDS_PIN = collections.OrderedDict([
    ("N-1", (0.4, 1.0)), ("N-2", (0.9, 1.15)), ("N-3", 2.0), ("N-4", (3.0, 9.0)),
    ("N-5", collections.OrderedDict([(u"中央値", (0.4, 1.0)), (u"最大", 2.5)])),
    ("N-6", collections.OrderedDict([(u"中央値", (70.0, 150.0)), (u"最大", 250.0)])),
    ("N-7", 10.0), ("N-8", 1.5), ("N-9", collections.OrderedDict([(u"書類", 11722), (u"AI の文", 16588)]))])


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------- 1. 封の字
def seal_paths(seal):
    u"""封 §4 に書かれた ``measure/...py``・``tests/measure/test_xbrl_nonfunc_*.py``・``docs/XBRL_NONFUNCTIONAL_RESULT_...md`` の path。無ければ空。"""
    try:
        sec4 = seal[seal.index("## §4"):seal.index("## §5")]
    except ValueError:
        return []
    return re.findall(r"`((?:measure|tests/measure|docs)/[A-Za-z0-9_./-]*?(?:\.py|\.md))`", sec4)


def seal_record_path(seal):
    u"""封 §0-2 の 5 の新しい記録の path(``fixtures/xbrl/nonfunc/<名前>.json``)。ちょうど 1 つ。"""
    try:
        sec = seal[seal.index("### §0-2"):seal.index("## §1")]
    except ValueError:
        return []
    return re.findall(r"`(fixtures/xbrl/nonfunc/[a-z0-9_.-]+\.json)`", sec)


def seal_problems(seal):
    out = []
    try:
        ids = SGR.table_ids(seal, "## §2", "## §3", r"^\| (N-\d+) \| (.*) \|$")
        sec = seal[seal.index("## §2"):seal.index("## §3")]
        seal[seal.index("## §4"):seal.index("## §5")]
        seal[seal.index("## §6"):]
    except ValueError:
        return [u"封の節(§0-2・§1・§2・§3・§4・§5・§6)が揃っていない"]
    if ids != list(PRED_IDS):
        out.append(u"封 §2 の表が N-1〜N-9 の 9 行でない: %s" % ids)
    for line in sec.splitlines():
        m = re.match(r"^\| (N-\d+) \| (.*) \|$", line)
        if m:
            cells = m.group(2).split(u" | ")
            if len(cells) < 3 or any(not c.strip() for c in cells[:3]):
                out.append(u"封 §2 の %s の欄(欄・予測・外れ方)が埋まっていない" % m.group(1))
    paths = seal_paths(seal)
    for rel in SCRIPT_RELS + GATE_RELS + (DOC_REL,):
        if rel not in paths:
            out.append(u"封 §4 に path が無い: %s" % rel)
    if seal_record_path(seal) != [RECORD_REL]:
        out.append(u"封 §0-2 の記録の path が script・門の持つ 1 つと違う: %s" % seal_record_path(seal))
    for ph in SEAL_PHRASES:
        if ph not in seal:
            out.append(u"封に決めの要点の字が無い: %s" % ph)
    return out


# ---------------------------------------------------------------- 2. 封の字と script の定数
def script_problems(seal, sc=None):
    u"""封の字と script の定数が同じか。sc = script の module(試験が壊した写しを渡す)。"""
    sc = sc or SC
    out = []
    if sc.SEAL_REL != SEAL_REL or sc.SEAL_COMMIT != SEAL_COMMIT_SHORT:
        out.append(u"封の path・commit が違う")
    if tuple(sc.PROFILES) != ("P27", "P33E"):
        out.append(u"profile が (P27, P33E) でない")
    if sc.REPS_PROD != 3 or sc.IMPORT_REPS != 5:
        out.append(u"回数(本番 3・import 5)が封の字と違う")
    if tuple(sc.KINDS) != (u"書類", u"AI の文") or (sc.KIND_DOC, sc.KIND_AI) != (u"書類", u"AI の文"):
        out.append(u"材料の種類が 書類・AI の文 でない")
    if [sc.REC_REL] != seal_record_path(seal):
        out.append(u"記録の path が封 §0-2 と違う")
    if sc.DOC_REL != DOC_REL or sc.SCRIPT_REL != SCRIPT_RELS[0] or DOC_REL not in seal_paths(seal) or sc.SCRIPT_REL not in seal_paths(seal):
        out.append(u"結果の文書・script の path が封 §4 と違う")
    if sc.MB != 1048576:
        out.append(u"MB が 2 の 20 乗 byte でない")
    try:
        got = sc.seal_bounds(seal)
    except Exception as e:                                   # noqa: BLE001  壊れた封は読めない = 赤
        return out + [u"封から幅を読めない(%s)" % type(e).__name__]
    for k, v in BOUNDS_PIN.items():
        if repr(got.get(k)) != repr(v):
            out.append(u"%s: 封の字から読んだ幅 %r と留めた値 %r が違う" % (k, got.get(k), v))
    if list(sc.seal_pred_rows(seal)) != list(PRED_IDS):
        out.append(u"封の予測の行が N-1〜N-9 でない")
    return out


# ---------------------------------------------------------------- 3. 触らない file(封の commit の blob と byte が同じ)
def seal_commit_of(root=REPO, seal_rel=SEAL_REL):
    u"""封の file を足した commit(ちょうど 1 つ)。履歴から探す。"""
    s = PR.added_commits(root, PREFIX + seal_rel)
    return s[0] if len(s) == 1 else None


def untouched_problems(rels=NOT_TOUCHED_RELS, root=REPO, seal_rel=SEAL_REL, allowed_new=ALLOWED_NEW):
    u"""封の commit の木と作業木の差(未 commit の変更・追加と、封の後の commit の変更・追加の両方)が、許した新しい file だけか。"""
    s = seal_commit_of(root, seal_rel)
    if s is None:
        return [u"封の commit が履歴から 1 つに決まらない"]
    out = []
    paths = [PREFIX + r for r in rels]
    rc, txt = PR.git_in(root, "diff", "--numstat", s, "--", *paths)
    if rc != 0:
        return [u"git diff が失敗した"]
    for line in [x for x in txt.splitlines() if x]:
        rel = line.split("\t")[2][len(PREFIX):]
        if rel not in allowed_new:
            out.append(u"封の commit の後に変わった: %s" % rel)
    rc2, txt2 = PR.git_in(root, "ls-files", "--others", "--exclude-standard", "--", *paths)
    for line in [x for x in txt2.splitlines() if x]:
        rel = line[len(PREFIX):]
        if rel not in allowed_new:
            out.append(u"封の commit の後に足された(未追跡): %s" % rel)
    return out


def later_declared_problems(declared=DECLARED_NEW_AFTER_SEAL, allowed_new=ALLOWED_NEW, rels=NOT_TOUCHED_RELS, root=REPO, seal_rel=SEAL_REL):
    u"""後の便が届けた file の一覧が、重なりが無く・この便の新しい file と別で・engine の path でなく・封の commit の木に無く(在る file の変更は届けられない)、
    届けを外したときに「封の後に変わった / 足された」と出る file とちょうど同じか(届けたのに木に無い・届けずに足した、のどちらも赤)。"""
    s = seal_commit_of(root, seal_rel)
    if s is None:
        return [u"封の commit が履歴から 1 つに決まらない"]
    out = []
    if len(set(declared)) != len(declared):
        out.append(u"届けた file に重なりがある")
    for rel in declared:
        if rel in allowed_new:
            out.append(u"この便の新しい file を届けに書いている: %s" % rel)
        if not rel.startswith(DECLARABLE_PREFIXES):
            out.append(u"届けられない置き場: %s" % rel)
        if PR.git_in(root, "cat-file", "-e", "%s:%s%s" % (s, PREFIX, rel))[0] == 0:
            out.append(u"封の commit の木に在る file は届けられない(変更になる): %s" % rel)
    seen = set(p.split(u": ", 1)[1] for p in untouched_problems(rels=rels, root=root, seal_rel=seal_rel, allowed_new=allowed_new) if u": " in p)
    for rel in sorted(set(declared) - seen):
        out.append(u"届けたのに封の後に足されていない: %s" % rel)
    for rel in sorted(seen - set(declared)):
        out.append(u"届けていない: %s" % rel)
    return out


def frozen_problems(rels=READ_ONLY_RELS, root=REPO, base=ROOT, seal_rel=SEAL_REL):
    u"""読むだけの file が封の commit の blob と byte が同じか(root = git の木、base = 作業木の audit-core の folder)。"""
    s = seal_commit_of(root, seal_rel)
    if s is None:
        return [u"封の commit が履歴から 1 つに決まらない"]
    out = []
    for rel in rels:
        blob = subprocess.run(["git", "show", "%s:%s%s" % (s, PREFIX, rel)], cwd=root, capture_output=True)
        if blob.returncode != 0:
            out.append(u"封の commit に無い: %s" % rel)
            continue
        p = os.path.join(base, rel)
        if not os.path.exists(p):
            out.append(u"作業木に無い: %s" % rel)
            continue
        with open(p, "rb") as fh:
            if fh.read() != blob.stdout:
                out.append(u"封の commit の blob と byte が違う: %s" % rel)
    return out


reserved_problems = SGR.reserved_problems


# ---------------------------------------------------------------- 5. 配線(ast)
def own_calls(src, attr):
    u"""``<何か>.<attr>(...)`` の呼び出しの node の列(関数の中を含む全部)。"""
    return [n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == attr]


def _func(src, name):
    for n in ast.parse(src).body:
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    return None


def _has_call(node, attr):
    return any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == attr for n in ast.walk(node))


def timed_region_problems(src):
    u"""``measure_call`` の時計の内側(perf_counter を読む最初の文と最後の文の間)が、process_time の読みと ``verify_document`` の呼び出し 1 つだけか。
    ``verify_document`` を呼ぶのは script 全体で 1 か所だけ。入力を読む関数(read_input・read_zip・read_text・open)を ``measure_call`` の中で呼ばない。"""
    out = []
    if len(own_calls(src, "verify_document")) != 1:
        out.append(u"verify_document を呼ぶのが script 全体で 1 か所でない")
    fn = _func(src, "measure_call")
    if fn is None:
        return out + [u"measure_call が無い"]
    body = fn.body
    clock = [i for i, st in enumerate(body) if _has_call(st, "perf_counter")]
    if len(clock) != 2 or len(sum([[n for n in ast.walk(st) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "perf_counter"] for st in body], [])) != 2:
        return out + [u"measure_call の perf_counter の読みが 2 回(前と後)でない"]
    inside = body[clock[0] + 1:clock[1]]
    calls_inside = [st for st in inside if _has_call(st, "verify_document")]
    if len(calls_inside) != 1:
        out.append(u"時計の内側に verify_document の呼び出しが 1 つでない")
    for st in inside:
        if _has_call(st, "verify_document"):
            if not (isinstance(st, ast.Assign) and isinstance(st.value, ast.Call) and isinstance(st.value.func, ast.Attribute) and st.value.func.attr == "verify_document"):
                out.append(u"時計の内側の verify_document の文が `x = VD.verify_document(...)` の形でない")
        elif not (isinstance(st, ast.Assign) and isinstance(st.value, ast.Call) and isinstance(st.value.func, ast.Attribute) and st.value.func.attr == "process_time"):
            out.append(u"時計の内側に verify_document と process_time の読み以外の文がある(行 %d)" % st.lineno)
    for bad in ("read_input", "read_zip", "read_text", "open", "read"):
        if any(isinstance(n, ast.Call) and ((isinstance(n.func, ast.Attribute) and n.func.attr == bad) or (isinstance(n.func, ast.Name) and n.func.id == bad)) for n in ast.walk(fn)):
            out.append(u"measure_call の中で入力を読んでいる(%s)" % bad)
    cj = _func(src, "child_job")
    if cj is None:
        out.append(u"child_job が無い")
    else:
        line = dict((n.func.id, n.lineno) for n in ast.walk(cj) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name))
        if "read_input" not in line or "measure_call" not in line or line["read_input"] >= line["measure_call"]:
            out.append(u"child_job が入力を読んでから measure_call を呼ぶ順でない")
    return out


def pool_problems(src):
    u"""``Pool(1, maxtasksperchild=1)`` がちょうど 1 本・fork・``map`` の chunksize 1・並行の道具(Process・ThreadPool・concurrent・apply_async・imap_unordered・procs)が無い。"""
    out = []
    pools = own_calls(src, "Pool")
    if len(pools) != 1:
        return [u"Pool の呼び出しが 1 本でない(%d)" % len(pools)]
    p = pools[0]
    kws = dict((k.arg, k.value) for k in p.keywords)
    if len(p.args) != 1 or not (isinstance(p.args[0], ast.Constant) and p.args[0].value == 1) or set(kws) != {"maxtasksperchild"} or not (isinstance(kws["maxtasksperchild"], ast.Constant) and kws["maxtasksperchild"].value == 1):
        out.append(u"Pool が Pool(1, maxtasksperchild=1) でない")
    ctx = own_calls(src, "get_context")
    if len(ctx) != 1 or not (ctx[0].args and isinstance(ctx[0].args[0], ast.Constant) and ctx[0].args[0].value == "fork"):
        out.append(u"get_context(\"fork\") が 1 つでない")
    maps = own_calls(src, "map")
    if len(maps) != 1 or dict((k.arg, k.value) for k in maps[0].keywords).get("chunksize") is None or getattr(dict((k.arg, k.value) for k in maps[0].keywords)["chunksize"], "value", None) != 1:
        out.append(u"pool.map が 1 本で chunksize=1 でない")
    code = ast.dump(ast.parse(src))
    for w in ("ThreadPool", "concurrent", "apply_async", "imap_unordered", "Thread", "Process", "procs", "starmap"):
        if re.search(r"(id|attr|arg|value|s)='%s'" % w, code):
            out.append(u"並行の道具か引数がある: %s" % w)
    return out


def own_function_problems(src):
    u"""前の便の関数と同じ名前を、script 自身が定義・代入していないか(差し替えていない)。"""
    names = set()
    for n in ast.parse(src).body:
        if isinstance(n, ast.FunctionDef):
            names.add(n.name)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    names.add(t.id)
    return [u"前の便の関数 %s をこの script が自分で定義している" % f for _m, f in REUSED_FUNCS if f in names]


def calls_problems(src):
    u"""script の本文が ``<module>.<関数>`` を呼んでいる(または引いている)か。"""
    return [u"この script が %s.%s を使っていない" % (m, f) for m, f in REUSED_FUNCS if u"%s.%s" % (m, f) not in src]


def wiring_problems(sc=None):
    u"""この script が前の便の script の同じ instance を使っているか。問題の列。"""
    sc = sc or SC
    out = []
    missing = object()
    checks = (("RM", sc.PB, "RM"), ("R97", sc.PB, "R97"), ("D", sc.PB, "D"), ("NF", sc.PB, "NF"), ("GEN", sc.PB, "GEN"), ("RUN", sc.PB, "RUN"), ("GEN", sc.RM, "GEN"), ("RUN", sc.RM, "RUN"))
    for mine, holder, theirs in checks:
        if getattr(sc, mine, missing) is missing or getattr(sc, mine, missing) is not getattr(holder, theirs, missing):
            out.append(u"%s がこの script と前の便の script で同じ instance でない" % mine)
    return out


# ================================================================ 試験
class SealTextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_a_1_the_seal_tables_paths_and_key_phrases_are_complete(self):
        self.assertEqual([], seal_problems(self.seal))

    def test_a_2_a_changed_key_phrase_turns_the_seal_check_red(self):
        for ph in SEAL_PHRASES:
            self.assertIn(ph, self.seal)
            mutated = self.seal.replace(ph, ph[:-1] + u"？")                       # 同じ字が 2 か所に在る要点も全部壊す
            self.assertNotEqual(mutated, self.seal)
            self.assertNotEqual([], seal_problems(mutated), ph)

    def test_a_3_a_broken_prediction_table_or_missing_section_turns_it_red(self):
        lines = self.seal.split("\n")
        n9 = [i for i, ln in enumerate(lines) if ln.startswith("| N-9 |")]
        self.assertEqual(1, len(n9))
        self.assertNotEqual([], seal_problems("\n".join(lines[:n9[0]] + lines[n9[0] + 1:])))                       # 9 行が 8 行
        n5 = [i for i, ln in enumerate(lines) if ln.startswith("| N-5 |")][0]
        cells = lines[n5].split(" | ")
        self.assertNotEqual([], seal_problems("\n".join(lines[:n5] + [" | ".join(cells[:2]) + " |"] + lines[n5 + 1:])))   # 外れ方の欄が無い
        self.assertNotEqual([], seal_problems("\n".join(lines[:n5] + [" | ".join(cells[:1] + [" "] + cells[2:])] + lines[n5 + 1:])))   # 予測の欄が空
        self.assertNotEqual([], seal_problems(self.seal.replace("`measure/xbrl_nonfunc_2026-11-10.py`", "`measure/x.py`")))
        self.assertNotEqual([], seal_problems(self.seal.replace("`tests/measure/test_xbrl_nonfunc_result.py`", "`tests/measure/x.py`")))
        self.assertNotEqual([], seal_problems(self.seal.replace("`tests/measure/test_xbrl_nonfunc_seal.py`", "`tests/measure/x.py`")))
        self.assertNotEqual([], seal_problems(self.seal.replace("`docs/XBRL_NONFUNCTIONAL_RESULT_2026-11-10.md`", "`docs/x.md`")))
        self.assertNotEqual([], seal_problems(self.seal.replace("`fixtures/xbrl/nonfunc/timing_2026-11-10.json`", "`fixtures/xbrl/nonfunc/x.json`")))
        self.assertNotEqual([], seal_problems(self.seal.replace("## §4", "## 四", 1)))
        self.assertNotEqual([], seal_problems(self.seal.replace("## §2", "## 二", 1)))

    def test_a_4_the_record_path_and_the_paths_are_read_from_the_seal(self):
        self.assertEqual([RECORD_REL], seal_record_path(self.seal))
        self.assertTrue(set(SCRIPT_RELS + GATE_RELS + (DOC_REL,)) <= set(seal_paths(self.seal)))              # §4 は読む前の便の script の path も書く
        self.assertEqual([], seal_record_path(self.seal.replace("### §0-2", "### 0-2", 1)))
        self.assertEqual([], seal_paths(self.seal.replace("## §4", "## 四", 1)))


class ScriptMatchesSealTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_b_1_the_script_agrees_with_the_seal(self):
        self.assertEqual([], script_problems(self.seal))

    def _fake(self, **ov):
        d = dict((k, getattr(SC, k)) for k in ("SEAL_REL", "SEAL_COMMIT", "PROFILES", "REPS_PROD", "IMPORT_REPS", "KINDS", "KIND_DOC", "KIND_AI", "REC_REL", "DOC_REL", "SCRIPT_REL", "MB",
                                               "seal_bounds", "seal_pred_rows"))
        d.update(ov)
        return types.SimpleNamespace(**d)

    def test_b_2_a_changed_script_constant_turns_it_red(self):
        self.assertEqual([], script_problems(self.seal, self._fake()))
        for ov in (dict(SEAL_COMMIT="0000000"), dict(SEAL_REL="docs/XBRL_PRIOR_CUE_BIND_ENGINE_SEAL_2026-11-06.md"), dict(PROFILES=("P27", "P32E")), dict(PROFILES=("P27",)), dict(REPS_PROD=1),
                   dict(IMPORT_REPS=3), dict(KINDS=(u"書類",)), dict(KIND_AI=u"AI"), dict(REC_REL="fixtures/xbrl/nonfunc/x.json"), dict(DOC_REL="docs/x.md"), dict(SCRIPT_REL="measure/x.py"),
                   dict(MB=1000000)):
            self.assertNotEqual([], script_problems(self.seal, self._fake(**ov)), sorted(ov))
        self.assertNotEqual([], script_problems(self.seal.replace("| 0.4〜1.0 秒 | 幅の外 = 外れ |", "| 0.4〜1.1 秒 | 幅の外 = 外れ |", 1), self._fake()))
        self.assertNotEqual([], script_problems(self.seal.replace("2.0 秒以下", "2.5 秒以下", 1), self._fake()))
        self.assertNotEqual([], script_problems(self.seal.replace("11,722 / 16,588", "11,722 / 16,589", 1), self._fake()))
        self.assertNotEqual([], script_problems(self.seal.replace("| N-8 |", "| N-8x |", 1), self._fake()))

    def test_b_3_the_bounds_are_read_from_the_seal_not_copied(self):
        self.assertEqual(repr(BOUNDS_PIN), repr(SC.seal_bounds(self.seal)))
        changed = self.seal.replace("70〜150 MB / 250 MB 以下", "70〜150 MB / 260 MB 以下", 1)
        self.assertNotEqual(repr(BOUNDS_PIN), repr(SC.seal_bounds(changed)))


class NotTouchedAndFrozenTest(unittest.TestCase):
    def test_c_1_engine_measure_and_the_records_are_untouched_since_the_seal_commit(self):
        self.assertEqual([], untouched_problems(allowed_new=ALLOWED_NEW + DECLARED_NEW_AFTER_SEAL))
        self.assertEqual([], later_declared_problems())
        self.assertEqual((SCRIPT_RELS[0], RECORD_REL), ALLOWED_NEW)

    def test_c_1a_a_later_declared_file_must_be_new_outside_the_engine_and_exactly_what_was_added(self):
        def repo():
            r = self._repo()
            r.put("measure/later.py")
            r.commit("measure/later.py")                                             # 後の便が足した script(commit 済み)
            r.put("fixtures/xbrl/a/later.json")                                      # 後の便が足した記録(未追跡)
            return r
        good = ("measure/later.py", "fixtures/xbrl/a/later.json")
        kw = dict(allowed_new=("measure/new.py",), rels=self.RELS)
        self.assertEqual([], later_declared_problems(declared=good, root=repo().d, **kw))
        self.assertEqual([], untouched_problems(rels=self.RELS, root=repo().d, allowed_new=("measure/new.py",) + good))
        self.assertNotEqual([], later_declared_problems(declared=good[:1], root=repo().d, **kw))                    # 届けずに足した file
        self.assertNotEqual([], later_declared_problems(declared=good + ("measure/ghost.py",), root=repo().d, **kw))  # 届けたのに木に無い
        self.assertNotEqual([], later_declared_problems(declared=good + good[:1], root=repo().d, **kw))             # 重なり
        self.assertNotEqual([], later_declared_problems(declared=good + ("measure/new.py",), root=repo().d, **kw))  # この便の新しい file
        r2 = repo()
        r2.put("measure/prev.py")                                                    # 封の木に在る file の変更は届けても赤
        self.assertNotEqual([], later_declared_problems(declared=good + ("measure/prev.py",), root=r2.d, **kw))
        r3 = repo()
        r3.put("adapters/xbrl/later.py")                                             # engine の置き場の新しい file は届けても赤
        self.assertNotEqual([], later_declared_problems(declared=good + ("adapters/xbrl/later.py",), root=r3.d, **kw))
        r4 = repo()
        r4.put("measure/undeclared.py")                                              # 届けの外の新しい file は、届けを足した検査でも赤
        self.assertNotEqual([], untouched_problems(rels=self.RELS, root=r4.d, allowed_new=("measure/new.py",) + good))
        self.assertNotEqual([], later_declared_problems(declared=good, root=r4.d, **kw))
        r5 = PR.Repo()                                                               # 封が無い repo
        r5.put("measure/prev.py")
        r5.commit("measure/prev.py")
        self.assertNotEqual([], later_declared_problems(declared=(), root=r5.d, **kw))

    def test_c_1b_the_seal_commit_is_found_from_history(self):
        s = seal_commit_of()
        self.assertTrue(s and s.startswith(SEAL_COMMIT_SHORT))

    def test_c_1c_the_read_only_files_are_byte_identical_to_the_seal_commit(self):
        self.assertEqual([], frozen_problems())
        self.assertEqual(len(READ_ONLY_RELS), len(set(READ_ONLY_RELS)))
        for rel in READ_ONLY_RELS:
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)

    def _repo(self):
        r = PR.Repo()
        for f in ("measure/lib/x.py", "measure/prev.py", "adapters/xbrl/recipes.py", "fixtures/xbrl/a/rec.json"):
            r.put(f)
        r.put(SEAL_REL)
        r.commit("measure/lib/x.py", "measure/prev.py", "adapters/xbrl/recipes.py", "fixtures/xbrl/a/rec.json", SEAL_REL)
        return r

    RELS = ("adapters", "measure", "fixtures/xbrl")

    def test_c_2_the_untouched_check_sees_a_changed_line_even_uncommitted_and_a_new_file(self):
        r = self._repo()
        self.assertEqual([], untouched_problems(rels=self.RELS, root=r.d, allowed_new=("measure/new.py",)))
        for rel in ("measure/prev.py", "adapters/xbrl/recipes.py", "fixtures/xbrl/a/rec.json"):
            r2 = self._repo()
            r2.put(rel)                                                              # 未 commit の変更
            self.assertNotEqual([], untouched_problems(rels=self.RELS, root=r2.d, allowed_new=("measure/new.py",)), rel)
        r3 = self._repo()
        r3.put("measure/prev.py")
        r3.commit("measure/prev.py")                                                 # 封の後に commit された変更
        self.assertNotEqual([], untouched_problems(rels=self.RELS, root=r3.d, allowed_new=("measure/new.py",)))
        r4 = self._repo()
        r4.put("measure/other_new.py")                                               # 許していない新しい file(未追跡)
        self.assertNotEqual([], untouched_problems(rels=self.RELS, root=r4.d, allowed_new=("measure/new.py",)))
        r5 = self._repo()
        r5.put("measure/other_new.py")
        r5.commit("measure/other_new.py")                                            # 許していない新しい file(commit 済み)
        self.assertNotEqual([], untouched_problems(rels=self.RELS, root=r5.d, allowed_new=("measure/new.py",)))
        r6 = self._repo()
        r6.put("measure/new.py")                                                     # 許した新しい file は赤にならない
        self.assertEqual([], untouched_problems(rels=self.RELS, root=r6.d, allowed_new=("measure/new.py",)))
        r6.commit("measure/new.py")
        self.assertEqual([], untouched_problems(rels=self.RELS, root=r6.d, allowed_new=("measure/new.py",)))
        r7 = PR.Repo()                                                               # 封が無い repo
        r7.put("measure/prev.py")
        r7.commit("measure/prev.py")
        self.assertNotEqual([], untouched_problems(rels=self.RELS, root=r7.d))

    def test_c_3_the_frozen_check_sees_a_changed_file_a_missing_one_and_a_file_without_the_seal_commit(self):
        r = self._repo()
        base = os.path.join(r.d, "audit-core")
        self.assertEqual([], frozen_problems(rels=("measure/prev.py",), root=r.d, base=base))
        with open(os.path.join(base, "measure/prev.py"), "a", encoding="utf-8") as fh:
            fh.write("x = 1\n")
        self.assertEqual([u"封の commit の blob と byte が違う: measure/prev.py"], frozen_problems(rels=("measure/prev.py",), root=r.d, base=base))
        self.assertEqual([u"封の commit に無い: measure/later.py"], frozen_problems(rels=("measure/later.py",), root=r.d, base=base))
        os.remove(os.path.join(base, "measure/prev.py"))
        self.assertEqual([u"作業木に無い: measure/prev.py"], frozen_problems(rels=("measure/prev.py",), root=r.d, base=base))
        self.assertNotEqual([], frozen_problems(rels=READ_ONLY_RELS + ("measure/nonexistent_file.py",)))

    def test_e_1_gate_files_do_not_use_the_reserved_names(self):
        self.assertEqual([], reserved_problems(rels=tuple(r for r in GATE_RELS if os.path.exists(os.path.join(ROOT, r))), base=ROOT))

    def test_e_2_the_reserved_name_check_sees_a_planted_name(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("ENGINE_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rels=("g.py",), base=d))
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("ENGINE_NOTES = 1\n")
            self.assertEqual([], reserved_problems(rels=("g.py",), base=d))

    def test_f_1_scripts_and_gates_carry_no_docid(self):
        for rel in SCRIPT_RELS + GATE_RELS:
            if os.path.exists(os.path.join(ROOT, rel)):
                self.assertIsNone(DOCID_RE.search(read(rel)), rel)

    def test_f_2_scripts_name_the_seal(self):
        for rel in SCRIPT_RELS:
            self.assertIn("XBRL_NONFUNCTIONAL_SEAL_2026-11-10.md", read(rel), rel)


class TimedRegionTest(unittest.TestCase):
    u"""時計の内側は verify_document の呼び出し 1 つだけ。入力の読み込みは時計の外。字(ast)と振る舞いの両方で縛る。"""

    @classmethod
    def setUpClass(cls):
        cls.src = read(SCRIPT_RELS[0])

    def test_t_1_the_clock_region_holds_only_one_verify_document_call(self):
        self.assertEqual([], timed_region_problems(self.src))

    def test_t_2_a_statement_inside_the_clock_or_a_second_call_or_a_read_in_measure_call_turns_it_red(self):
        src = self.src
        call = u"    out = VD.verify_document(zb, prof, text)\n"
        self.assertEqual(1, src.count(call))
        for ins in (u"    zb = bytes(zb)\n", u"    x = len(zb)\n", u"    zb2, text2 = read_input(None, None)\n"):
            self.assertNotEqual([], timed_region_problems(src.replace(call, ins + call)), ins)                    # 時計の内側に別の文
        self.assertNotEqual([], timed_region_problems(src.replace(call, call + call)), u"2 回呼ぶ")
        self.assertNotEqual([], timed_region_problems(src.replace(call, call + u"    out2 = VD.verify_document(zb, prof, None)\n")))
        t0 = u"\n    t0 = time.perf_counter()\n"
        self.assertEqual(1, src.count(t0))
        for ins in (u"    zb = open(\"x\", \"rb\").read()\n", u"    zb, text = read_input(KIND_DOC, None)\n"):
            self.assertNotEqual([], timed_region_problems(src.replace(t0, u"\n" + ins + t0[1:])), ins)                       # measure_call の中で入力を読む(時計の前でも赤)
        self.assertNotEqual([], timed_region_problems(src.replace(t0, u"\n")), u"前の読みが無い")
        self.assertNotEqual([], timed_region_problems(src.replace(u"\n    t1 = time.perf_counter()\n", u"\n")), u"後の読みが無い")
        c0 = u"\n    c0 = time.process_time()\n"
        self.assertEqual(1, src.count(c0))
        self.assertEqual([], timed_region_problems(src.replace(c0, u"\n")))                                          # process_time の読みは外してよい(時計の内側の許した文)
        self.assertNotEqual([], timed_region_problems(src.replace(u"def measure_call(", u"def measure_call2(")))
        # child_job が先に measure_call を呼ぶ順
        cj = src.replace(u"    zb, text = read_input(kind, ref)\n    res = measure_call(zb, text, prof)\n", u"    res = measure_call(None, None, prof)\n    zb, text = read_input(kind, ref)\n")
        self.assertNotEqual(src, cj)
        self.assertNotEqual([], timed_region_problems(cj))

    def test_t_3_behaviour_the_slow_read_is_outside_the_clock_and_the_call_inside(self):
        u"""読み込み(0.4 秒眠る)を時計の外、verify_document(0.1 秒眠る)を内側にした偽の部品で、記録される時間が 0.1 秒の近くで 0.4 秒に届かない。"""
        calls = []

        class FakeVD(object):
            @staticmethod
            def verify_document(zb, prof, text):
                calls.append((zb, prof, text))
                time.sleep(0.1)
                return {"claims": [{"kind": "num"}, {"kind": "num"}, {"kind": "text"}]}

        def slow_read(kind, ref):
            time.sleep(0.4)
            return b"abc", u"文"
        saved = (SC.VD, SC.read_input)
        SC.VD, SC.read_input = FakeVD, slow_read
        try:
            t0 = time.perf_counter()
            res = SC.child_job((SC.KIND_AI, None, "P27"))
            total = time.perf_counter() - t0
        finally:
            SC.VD, SC.read_input = saved
        self.assertEqual([(b"abc", "P27", u"文")], calls)
        self.assertGreaterEqual(total, 0.5)
        self.assertGreaterEqual(res["wall"], 0.1)
        self.assertLess(res["wall"], 0.3)                                        # 読み込みの 0.4 秒は入らない
        self.assertLess(res["cpu"], 0.05)                                        # 眠っている間は CPU 時間が増えない
        self.assertEqual((3, 2, 3, len(u"文".encode("utf-8"))), (res["claims"], res["num"], res["zip_bytes"], res["text_bytes"]))
        self.assertGreaterEqual(res["rss_after"], res["rss_before"])

    def test_t_4_behaviour_the_read_happens_before_the_call_and_a_doc_has_no_text(self):
        order = []

        class FakeVD(object):
            @staticmethod
            def verify_document(zb, prof, text):
                order.append("call")
                return {"claims": []}

        def rd(kind, ref):
            order.append("read")
            return b"z", None
        saved = (SC.VD, SC.read_input)
        SC.VD, SC.read_input = FakeVD, rd
        try:
            res = SC.child_job((SC.KIND_DOC, None, "P33E"))
        finally:
            SC.VD, SC.read_input = saved
        self.assertEqual(["read", "call"], order)
        self.assertEqual((0, 0, 1, None), (res["claims"], res["num"], res["zip_bytes"], res["text_bytes"]))

    def test_t_5_the_rss_unit_is_bytes_on_macos_and_kilobytes_elsewhere(self):
        self.assertEqual(1 if sys.platform == "darwin" else 1024, SC.RSS_UNIT)
        self.assertGreater(SC.rss_bytes(), 1000000)                                # 呼ぶ process は 1 MB より大きい(byte の単位)


class MeasureFieldsTest(unittest.TestCase):
    u"""測った値が行の正しい欄に入る(変異で見つけた穴を塞ぐ試験): ru_maxrss の前後を読む順・行の欄の対応・import の時間を 5 回測ること。"""

    def test_u_1_rss_before_is_read_before_the_call_and_rss_after_after_it(self):
        seq = iter([111, 222, 333])
        seen = []

        class FakeVD(object):
            @staticmethod
            def verify_document(zb, prof, text):
                seen.append(len(seen))
                return {"claims": []}
        saved = (SC.VD, SC.rss_bytes)
        SC.VD, SC.rss_bytes = FakeVD, lambda: next(seq)
        try:
            res = SC.measure_call(b"z", None, "P27")
        finally:
            SC.VD, SC.rss_bytes = saved
        self.assertEqual((111, 222), (res["rss_before"], res["rss_after"]))           # 呼ぶ前に 1 回・呼んだ後に 1 回(ちょうど 2 回読む)
        self.assertEqual([0], seen)

    def test_u_2_make_row_puts_each_measured_value_in_its_own_field(self):
        res = {"wall": 1.5, "cpu": 1.25, "rss_before": 111, "rss_after": 222, "claims": 33, "num": 22, "zip_bytes": 444, "text_bytes": 555}
        row = SC.make_row((u"AI の文", "id1", "P33E", 2), res)
        self.assertEqual([(u"材料の種類", u"AI の文"), (u"本の id", "id1"), (u"profile", "P33E"), (u"回", 2), (u"時間", 1.5), (u"CPU 時間", 1.25), (u"ru_maxrss の前", 111), (u"ru_maxrss の後", 222),
                          (u"claim の数", 33), (u"数の claim の数", 22), (u"zip の byte 数", 444), (u"文の byte 数", 555)], list(row.items()))
        row2 = SC.make_row((u"書類", "d", "P27", 1), dict(res, text_bytes=None))
        self.assertIsNone(row2[u"文の byte 数"])
        self.assertEqual(list(SC.ROW_KEYS), list(row2))

    def test_u_3_import_times_starts_five_fresh_python_processes_and_returns_five_seconds(self):
        calls = []
        real = SC.subprocess.run

        def spy(cmd, *a, **kw):
            calls.append(list(cmd))
            return real(cmd, *a, **kw)
        SC.subprocess.run = spy
        try:
            got = SC.import_times(ROOT)
        finally:
            SC.subprocess.run = real
        self.assertEqual(5, SC.IMPORT_REPS)
        self.assertEqual(5, len(calls))
        for c in calls:
            self.assertEqual(sys.executable, c[0])
            self.assertIn("import adapters.xbrl.verify_document", c)
        self.assertEqual(5, len(got))
        self.assertTrue(all(isinstance(x, float) and 0.02 < x < 120 for x in got), got)                # 新しい python の起動 + import は 20 ms より長い


# 並行なしの試験で、子の中で呼ばれる偽の job(この門の module の関数 = fork の子が名前で引ける)。区間(開始・終了)と pid を返す
def _fake_child(arg):
    t0 = time.perf_counter()
    time.sleep(0.15)
    return (os.getpid(), t0, time.perf_counter())


class PoolTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = read(SCRIPT_RELS[0])

    def test_p_1_the_pool_is_pool_1_maxtasksperchild_1_with_fork_and_chunksize_1(self):
        self.assertEqual([], pool_problems(self.src))

    def test_p_2_a_wider_pool_or_another_parallel_tool_turns_it_red(self):
        src = self.src
        ctx = u'ctx.Pool(1, maxtasksperchild=1)'
        self.assertEqual(1, src.count(ctx))
        for bad in (u"ctx.Pool(2, maxtasksperchild=1)", u"ctx.Pool(1)", u"ctx.Pool(1, maxtasksperchild=2)", u"ctx.Pool(processes=1, maxtasksperchild=1)", u"ctx.Pool(1, maxtasksperchild=1, initializer=None)"):
            self.assertNotEqual([], pool_problems(src.replace(ctx, bad)), bad)
        self.assertNotEqual([], pool_problems(src.replace(u"get_context(\"fork\")", u"get_context(\"spawn\")")))
        self.assertNotEqual([], pool_problems(src.replace(u"chunksize=1", u"chunksize=2")))
        self.assertNotEqual([], pool_problems(src.replace(u"pool.map(child_job, args, chunksize=1)", u"pool.map(child_job, args)")))
        self.assertNotEqual([], pool_problems(src + u"\n\ndef extra(args):\n    with multiprocessing.get_context(\"fork\").Pool(1, maxtasksperchild=1) as pool:\n        return pool.map(child_job, args, chunksize=1)\n"))
        self.assertNotEqual([], pool_problems(src + u"\n\ndef extra2(args):\n    return multiprocessing.pool.ThreadPool(2)\n"))
        self.assertNotEqual([], pool_problems(src.replace(u"return pool.map(child_job, args, chunksize=1)", u"return pool.imap_unordered(child_job, args)")))
        self.assertNotEqual([], pool_problems(src + u"\n\ndef extra3(args):\n    return multiprocessing.Process(target=child_job)\n"))
        self.assertNotEqual([], pool_problems(src.replace(u"def run_pool(args):", u"def run_pool(args, procs=1):")))

    def test_p_3_behaviour_each_call_is_its_own_child_process_and_the_calls_do_not_overlap(self):
        saved = SC.child_job
        SC.child_job = _fake_child
        try:
            res = SC.run_pool([1, 2, 3, 4])
        finally:
            SC.child_job = saved
        self.assertEqual(4, len(res))
        pids = [r[0] for r in res]
        self.assertEqual(4, len(set(pids)))                                        # 1 回 = 子 process 1 つ(使い回さない)
        self.assertNotIn(os.getpid(), pids)                                        # 親では測らない
        ivs = sorted((r[1], r[2]) for r in res)
        for (a0, a1), (b0, b1) in zip(ivs, ivs[1:]):
            self.assertLessEqual(a1, b0 + 0.001)                                   # 区間が重ならない = 並行なし

    def test_p_4_the_checks_see_a_pool_of_two_in_the_behaviour_too(self):
        u"""Pool を 2 にした版の run_pool は区間が重なる(= p_3 が赤になる形)。同じ file の字から作って走らせる。"""
        src = self.src
        i = src.index(u"def run_pool(")
        j = src.index(u"\n\n\n", i)
        fn = src[i:j].replace(u"Pool(1, maxtasksperchild=1)", u"Pool(2, maxtasksperchild=1)")
        self.assertIn(u"Pool(2", fn)
        import multiprocessing
        ns = {"multiprocessing": multiprocessing, "child_job": _fake_child}
        exec(compile(fn, "<wide_pool>", "exec"), ns)
        res = ns["run_pool"]([1, 2, 3, 4])
        ivs = sorted((r[1], r[2]) for r in res)
        overlap = any(a1 > b0 + 0.001 for (a0, a1), (b0, b1) in zip(ivs, ivs[1:]))
        self.assertTrue(overlap)


class WiringTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = read(SCRIPT_RELS[0])

    def test_w_1_the_script_uses_the_same_instances_as_the_previous_scripts(self):
        self.assertEqual([], wiring_problems())
        self.assertIs(SC.RM, SC.PB.RM)
        self.assertIs(SC.R97, SC.PB.R97)
        self.assertIs(SC.GEN, SC.RM.GEN)
        self.assertIs(SC.RUN, SC.RM.RUN)

    def test_w_2_another_instance_turns_the_wiring_check_red(self):
        for name in ("RM", "R97", "D", "NF", "GEN", "RUN"):
            fake = types.SimpleNamespace(**dict((k, getattr(SC, k)) for k in dir(SC) if not k.startswith("__")))
            setattr(fake, name, types.SimpleNamespace())
            self.assertNotEqual([], wiring_problems(fake), name)
        self.assertEqual([], wiring_problems())

    def test_w_3_the_script_defines_none_of_the_previous_functions_and_uses_them(self):
        src = self.src
        self.assertEqual([], own_function_problems(src))
        self.assertEqual([], calls_problems(src))
        for m, f in REUSED_FUNCS:
            self.assertTrue(callable(getattr(getattr(SC, m), f)), (m, f))
            self.assertFalse(hasattr(SC, f), f)                                   # この script の名前空間に同名の関数を持たない
            self.assertNotEqual([], own_function_problems(src + u"\n\ndef %s(*a):\n    return None\n" % f), f)
            self.assertNotEqual([], own_function_problems(src + u"\n%s = None\n" % f), f)
            self.assertNotEqual([], calls_problems(src.replace(u"%s.%s" % (m, f), u"X.%s" % f)), (m, f))

    def test_w_4_the_script_loads_the_pb_script_with_importlib_once(self):
        self.assertIn(u'load_module("xbrl_pbind_2026-11-06.py"', self.src)
        self.assertEqual(1, self.src.count(u"load_module(\"xbrl_"))

    def test_w_5_the_loader_puts_back_the_names_that_were_there_before_and_keeps_its_own(self):
        before = dict(sys.modules)
        probe = "nonfunc_script_loader_probe"
        try:
            mod = SC.load_module("xbrl_pbind_2026-11-06.py", probe)
            self.assertIsNot(mod.XR, SC.PB.XR)                                    # 前提: 読み直しは別の object を作る(上書きの機会がある)
            self.assertEqual([], sorted(k for k, v in before.items() if sys.modules.get(k) is not v))
            self.assertIs(sys.modules.get(probe), mod)
        finally:
            sys.modules.pop(probe, None)

    def test_w_6_a_loader_without_the_restore_lines_overwrites_the_names(self):
        u"""戻す行(``finally`` の中)を外した版の loader を同じ file の字から作って走らせると、先に居た名前が上書きされる(= w_5 が赤になる)。"""
        src = self.src
        i = src.index(u"def load_module(")
        j = src.index(u"\n\n\n", i)
        fn = src[i:j]
        self.assertIn(u"finally:", fn)
        k = fn.index(u"    finally:")
        broken = fn[:k].rstrip() + u"\n    except ZeroDivisionError:\n        pass\n    return mod\n"
        self.assertNotIn(u"sys.modules[k] = v", broken)
        ns = {"importlib": importlib, "os": os, "sys": sys, "HERE": os.path.join(ROOT, "measure")}
        exec(compile(u"import importlib.util\n" + broken, "<broken_loader>", "exec"), ns)
        before = dict(sys.modules)
        probe = "nonfunc_script_broken_loader_probe"
        try:
            ns["load_module"]("xbrl_pbind_2026-11-06.py", probe)
            changed = sorted(k for k, v in before.items() if sys.modules.get(k) is not v)
            self.assertNotEqual([], changed)                                      # 上書きされた名前が在る(w_5 が赤になる形)
        finally:
            for k, v in before.items():
                sys.modules[k] = v
            for k in list(sys.modules):
                if k not in before:
                    sys.modules.pop(k, None)


class RunWiringTest(unittest.TestCase):
    u"""``run`` の順・本番の守り・出力が既に在れば止まる・回数。入力と時計は偽の部品(通信も cache の読みも要らない)。"""

    def _fakes(self, docs, books, reps_seen=None):
        saved = dict((k, getattr(SC, k)) for k in ("doc_items", "book_items", "run_pool", "import_times", "job_args"))
        SC.doc_items = lambda only=None: [(d, "/nope/%s.zip" % d, "0" * 64) for d in docs]
        SC.book_items = lambda root=SC.ROOT, only=None: [(b, (b, {}, {}, "/nope", {})) for b in books]
        SC.import_times = lambda root=SC.ROOT, reps=SC.IMPORT_REPS: [0.1] * SC.IMPORT_REPS

        def fake_pool(args):
            if reps_seen is not None:
                reps_seen.append(list(args))
            return [{"wall": 0.5, "cpu": 0.4, "rss_before": 10, "rss_after": 100, "claims": 5, "num": 4, "zip_bytes": 7, "text_bytes": (None if a[0] == SC.KIND_DOC else 3)} for a in args]
        SC.run_pool = fake_pool
        return saved

    def _restore(self, saved):
        for k, v in saved.items():
            setattr(SC, k, v)

    def test_r_1_the_order_is_rep_then_kind_then_book_then_profile(self):
        docs, books = ["D1", "D2"], ["B1", "B2", "B3"]
        seen = []
        saved = self._fakes(docs, books, seen)
        try:
            with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
                rec = SC.run(root=SC.ROOT, only="x", out=os.path.join(d, "t.json"), reps=2, say=lambda *a: None)
        finally:
            self._restore(saved)
        want = []
        for rep in (1, 2):
            for doc in docs:
                for p in ("P27", "P33E"):
                    want.append((u"書類", doc, p, rep))
            for b in books:
                for p in ("P27", "P33E"):
                    want.append((u"AI の文", b, p, rep))
        got = [(r[u"材料の種類"], r[u"本の id"], r[u"profile"], r[u"回"]) for r in rec[u"行"]]
        self.assertEqual(want, got)
        self.assertEqual(2 * (2 + 3) * 2, len(rec[u"行"]))
        self.assertEqual(list(SC.ROW_KEYS), list(rec[u"行"][0]))
        self.assertEqual(len(want), len(seen[0]))                                   # 全部の回が 1 本の pool に渡る
        self.assertEqual([u"書類", u"書類", u"AI の文", u"AI の文"], [a[0] for a in seen[0][:2]] + [a[0] for a in seen[0][4:6]])

    def test_r_2_production_needs_the_default_count_and_no_only(self):
        saved = self._fakes(["D1"], ["B1"])
        try:
            with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
                for kw in (dict(only="x"), dict(reps=1), dict(reps=2), dict(only="x", reps=3)):
                    with self.assertRaises(SC.Stop):
                        SC.run(root=d, say=lambda *a: None, **kw)                    # out なし = 本番の記録の path
                self.assertFalse(os.path.exists(os.path.join(d, SC.REC_REL)))
        finally:
            self._restore(saved)

    def test_r_3_an_existing_output_stops_the_run_and_a_bad_rep_count_stops_it(self):
        seen = []
        saved = self._fakes(["D1"], ["B1"], seen)
        try:
            with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
                out = os.path.join(d, "t.json")
                with open(out, "w", encoding="utf-8") as fh:
                    fh.write("{}")
                with self.assertRaises(SC.Stop):
                    SC.run(root=SC.ROOT, out=out, reps=1, say=lambda *a: None)
                self.assertEqual([], seen)                                                   # 測る前に止まる(出力が在るのに何十分も測らない)
                with open(out, encoding="utf-8") as fh:
                    self.assertEqual("{}", fh.read())                                        # 既に在る出力は書き換えない
                for bad in (0, -1):
                    with self.assertRaises(SC.Stop):
                        SC.run(root=SC.ROOT, out=os.path.join(d, "u.json"), reps=bad, say=lambda *a: None)
                    self.assertEqual([], seen)
        finally:
            self._restore(saved)

    def test_r_4_the_default_run_count_is_three_for_each_book_and_profile(self):
        docs, books = ["D1"], ["B1"]
        saved = self._fakes(docs, books)
        try:
            with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
                rec = SC.run(root=SC.ROOT, only="x", out=os.path.join(d, "t.json"), reps=SC.REPS_PROD, say=lambda *a: None)
        finally:
            self._restore(saved)
        self.assertEqual(3 * 2 * 2, len(rec[u"行"]))
        self.assertEqual(3, rec[u"回数"])
        self.assertEqual({1, 2, 3}, set(r[u"回"] for r in rec[u"行"]))

    def test_r_5_job_args_is_a_single_ordered_list_not_split_by_profile_or_kind(self):
        args, heads = SC.job_args([("D1", "p", "s")], [("B1", "ref")], 1)
        self.assertEqual([(u"書類", "D1", "P27", 1), (u"書類", "D1", "P33E", 1), (u"AI の文", "B1", "P27", 1), (u"AI の文", "B1", "P33E", 1)], heads)
        self.assertEqual(len(args), len(heads))
        self.assertEqual(["P27", "P33E", "P27", "P33E"], [a[2] for a in args])

    def test_r_6_the_main_cli_has_no_procs_option_and_the_tally_has_no_write(self):
        src = read(SCRIPT_RELS[0])
        self.assertNotIn(u"--procs", src)
        self.assertEqual(1, src.count(u"add_argument(\"--reps\""))
        i = src.index(u"def run_tally(")
        j = src.index(u"\n\n\n", i)
        self.assertNotIn(u"open(", src[i:j])
        self.assertNotIn(u"write", src[i:j])


class OrderTest(unittest.TestCase):
    def test_o_1_the_real_history_has_the_seal_before_the_scripts_and_gates(self):
        u"""script・門のどれかが未 commit なら赤(足した commit が無い)。この便は engine を変えないので実装の commit は無い。"""
        self.assertEqual([], PR.order_problems(REPO, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, [], SCRIPT_RELS + GATE_RELS))


OTHERS = ["measure/a.py", "tests/g.py"]
SEALF = "docs/seal.md"


def order_of(r, seal_short):
    return PR.order_problems(r.d, PREFIX, SEALF, seal_short, [], OTHERS)


class OrderMutationTest(unittest.TestCase):
    def _repo(self, before_seal=(), after=OTHERS, seal_touches=None):
        r = PR.Repo()
        for f in before_seal:
            r.put(f)
            r.commit(f)
        if seal_touches:
            r.put(seal_touches)
        r.put(SEALF)
        s = r.commit(SEALF, *([seal_touches] if seal_touches else []))
        for f in after:
            r.put(f)
        if after:
            r.commit(*after)
        return r, s[:7]

    def test_p_1_a_correct_order_is_green(self):
        r, s = self._repo()
        self.assertEqual([], order_of(r, s))

    def test_p_2_a_script_before_the_seal_is_red(self):
        r, s = self._repo(before_seal=[OTHERS[0]], after=OTHERS[1:])
        self.assertIn("BEFORE_SEAL:" + OTHERS[0], order_of(r, s))

    def test_p_3_an_uncommitted_script_is_red_not_skipped(self):
        r, s = self._repo(after=OTHERS[:1])
        self.assertEqual(["UNCOMMITTED:" + OTHERS[1]], order_of(r, s))
        r2, s2 = self._repo(after=[])
        self.assertEqual(sorted("UNCOMMITTED:" + o for o in OTHERS), sorted(order_of(r2, s2)))

    def test_p_4_a_wrong_seal_hash_or_a_seal_that_touches_the_engine_is_red(self):
        r, s = self._repo()
        self.assertIn("SEAL_NOT_THE_SEALED", order_of(r, "0000000"))
        r2, s2 = self._repo(before_seal=["adapters/xbrl/recipes.py"], seal_touches="adapters/xbrl/recipes.py")
        self.assertIn("SEAL_TOUCHES_ENGINE", order_of(r2, s2))

    def test_p_5_the_seal_is_found_by_the_commit_that_added_it(self):
        r, s = self._repo()
        self.assertTrue(seal_commit_of(r.d, SEALF).startswith(s))
        r2 = PR.Repo()
        r2.put("measure/x.py")
        r2.commit("measure/x.py")
        self.assertIsNone(seal_commit_of(r2.d, SEALF))


if __name__ == "__main__":
    unittest.main()
