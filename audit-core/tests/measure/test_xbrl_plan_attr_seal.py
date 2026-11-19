# -*- coding: utf-8 -*-
"""封 docs/XBRL_PLAN_ATTR_SEAL_2026-11-19.md(PA ― 「実績の数でない(見積り・計画の数)のに実績の fact に結んだ行」を文の字で止める後付けの規則が、取り違えをどれだけ止め、正しい結びをどれだけ減らすか)の門。封 §6。

**この門が縛るもの**

1. 封の字: 封の commit(e69b733c)・path・手がかりの語の表(§2-3)・段の字・予測 PA-1〜PA-8 が script の定数と同じ。封の file は commit した blob と 1 字も変わっていない。
2. 入力 23 件(便 SC の封の表 21 + 2)の sha256 が封の表・script の表・門の表・実物で同じ。入力の確かめは 1 byte 違う複製で止まる。前の便の封・結果の文書は封の commit から 0 行。
3. engine は封の commit から 0 行(``core/``・``adapters/``)。作業木にも engine の未 commit の変更が無い。
4. 順序: 封の commit ⊏ script・この門・記録を足した commit(未 commit は赤)。
5. **止める条件**(封 §2-4): 語の表(1 語ずつ)・段 1 は前の字の P だけ・段 2 の F と見出し(P か F だけ。E は入れない)・段 3 の文の全部と E(E は前の字だけ)・W の決め・member を問わない・段の包含を、
   作り物の入力で本物のまま走らせる。
6. **札の引き方**: 同じ state で引けた行だけが分母。引けなかった行は分母に入れず、理由別に数える。「見積り・計画」の札は便ごとに型の字が違う(KAM・YS = イ、TSS = ウ)。
7. **つなぐ配線**: ``book_job`` と ``orchestrate`` を作り物の本で本物のまま走らせ、便・state・段で非対称な手計算と合わせる。引数を明示で渡さない本番の既定の経路も通す。
   便 SC の記録の行との(鍵, state)の照合・位置の読み方・「当たるはずの行」の率 95% を止める条件として縛る。
8. 記録 ``fixtures/xbrl/plan_attr/stops_2026-11-19.json``: 封の字・script の sha256・入力・指紋・集計が行から数え直せる・予測の判定に要る数が作り直せる・文や値や要素名や主語の語を持たない。
9. 行頭の名前: この門は ``ENGINE_LATER``・``UNTOUCHED``・``PIN_DEF``・``LATER_ENGINE_COMMITS``・``FROZEN_LATER``・``ENGINE_TRANSITIONS`` を行頭に置かない。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``。script の字を 1 か所替えた版を memory の中に作る。file は書き換えない)。
全数の作り直しは門の中では走らせない(重い)。この file は docID の字を持たない。
"""
import ast
import collections
import contextlib
import copy
import importlib.util
import json
import os
import re
import shutil
import tempfile
import types
import unittest
import sys

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


SCT = load_module("tests/measure/test_xbrl_scope_cond_seal.py", "scope_cond_gate_helpers_for_pa_seal")      # 便 SC の門の部品(順序・履歴・作り物の部品)。門としては走らせない
PR = SCT.PR
MS = load_module("measure/xbrl_plan_attr_2026-11-19.py", "plan_attr_script_for_seal_gate")

SEAL_REL = "docs/XBRL_PLAN_ATTR_SEAL_2026-11-19.md"
SC_SEAL_REL = "docs/XBRL_SCOPE_COND_SEAL_2026-11-19.md"
SEAL_COMMIT_SHORT = "e69b733c"                # 封の commit(literal に留める。script の定数と違えば赤)
SCRIPT_REL = "measure/xbrl_plan_attr_2026-11-19.py"
GATE_REL = "tests/measure/test_xbrl_plan_attr_seal.py"
RECORD_REL = "fixtures/xbrl/plan_attr/stops_2026-11-19.json"
SC_SCRIPT_REL = "measure/xbrl_scope_cond_2026-11-19.py"
SC_RECORD_REL = "fixtures/xbrl/scope_cond/stops_2026-11-19.json"
ORDER_FILES = (SCRIPT_REL, GATE_REL, RECORD_REL)
#: 入力の表(literal。封の表(便 SC の封の表 + 2 行)・script の表・実物と照らす)
INPUT_SHAS = tuple(SCT.INPUT_SHAS) + (
    (SC_SCRIPT_REL, "c7ec858ea9523ede23ab2da6d16b53ec338d50cb35899ecac66705e16919e065"),
    (SC_RECORD_REL, "d938942bffb39176464f3c644932cf53258f84676aacdbbbc421de74d4dc08a7"))
INPUT_RELS = tuple(rel for rel, _sha in INPUT_SHAS)
#: 前の便の封・結果の文書(封の commit から 0 行)
PRIOR_DOCS = tuple(SCT.PRIOR_DOCS) + (SC_SEAL_REL, "docs/XBRL_SCOPE_COND_RESULT_2026-11-19.md")
STDLIB_OK = ("__future__", "argparse", "collections", "importlib", "json", "os", "sys", "time")
NETWORK_MODULES = SCT.NETWORK_MODULES
RESERVED_PREFIXES = SCT.RESERVED_PREFIXES
DOCID_RE = SCT.DOCID_RE
STATES = SCT.STATES
G, VM, UN, PN = STATES
REASON_P = u"target_or_plan"
#: 封 §2-3 の手がかりの語の表(literal。封の字・script の表と照らす)
WORD_TABLE = collections.OrderedDict([
    (u"P", (u"目標", u"計画", u"見込", u"見通")),
    (u"F", (u"予想", u"予定", u"予測", u"想定", u"次期", u"翌期", u"来期", u"翌事業年度", u"翌連結会計年度", u"方針")),
    (u"E", (u"見積", u"仮定", u"試算"))])
K_WIRE = u"配線の確認(封 §2-2。予測ではない。違えば止まる)"
K_ALL = u"結んだ行の全部(封 §2-5 の 1)"
K_P = u"engine が止めた行(P の行。封 §2-5 の 1)"
K_LABEL = u"読みの札つきの行(封 §2-5 の 2)"
K_CLASS = u"当たった類ごとの数(封 §2-5 の 3)"
K_OVER = u"便 SC の段 2 との重なり(封 §2-5 の 4)"
K_PRED = u"予測の判定に要る数(PA-1〜PA-8。当たり・外れは結果の文書で)"
K_W_SC = u"結んだ行の(鍵, state)と便 SC の記録の行の照合(違えば止まる)"
K_W_POS = u"位置の確かめ(便ごと。便 SC の関数)"
K_W_P = u"当たるはずの行に当たるか(P の行から future_period を除いた行に文の全部の類 P の語。95% 未満なら止まる)"
S1, S2, S3 = u"段 1", u"段 2", u"段 3"
NONE = None

read = SCT.read
sha_of = SCT.sha_of
sha_or_none = SCT.sha_or_none
load_json = SCT.load_json
guard = SCT.guard
patched = SCT.patched
stops = SCT.stops
walk = SCT.walk
fake_rt_rec = SCT.fake_rt_rec
fbook = SCT.fbook
fake_read_rec = SCT.fake_read_rec
leak_problems_base = SCT.leak_problems

_REAL = {}


def real_recs():
    u"""本物の入力の記録(大きい。1 度だけ読む。便 SC の記録も)。"""
    if "recs" not in _REAL:
        _REAL["recs"] = MS.load_records(ROOT)
    return _REAL["recs"]


def load_source(src):
    u"""script の字(``src``)から module を memory の中に作る。file は読み書きしない。``__file__`` は本物の script。"""
    mod = types.ModuleType("plan_attr_mutant")
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


def seal_words(seal):
    u"""封 §2-3 の表から {類: (語の並び)}。"""
    out = collections.OrderedDict()
    for m in re.finditer(r"^\| ([PFE])\([^)]*\) \| (.*) \|$", seal, re.M):
        out[m.group(1)] = tuple(re.findall(u"「([^」]+)」", m.group(2)))
    return out


def seal_problems(ms=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    out = []
    if ms.SEAL_COMMIT != SEAL_COMMIT_SHORT or ms.SEAL_REL != SEAL_REL or ms.SCRIPT_REL != SCRIPT_REL or ms.RECORD_REL != RECORD_REL:
        out.append(u"script の封の commit・path・記録の path が門と違う")
    for phrase in (u"PA-1", u"PA-2", u"PA-3", u"PA-4", u"PA-5", u"PA-6", u"PA-7a", u"PA-7b", u"PA-8", u"fixtures/xbrl/plan_attr/stops_2026-11-19.json", u"measure/xbrl_plan_attr_2026-11-19.py",
                   u"長さが 40 字以下・「。」で終わらない・数の claim を 1 つも持たない文", u"最も近い見出し", u"profile は 3 便とも `P33E`", u"当たる率が 95% 未満", u"15 行未満", u"future_period",
                   u"member の欄が空かどうかは問わない"):
        if phrase not in seal:
            out.append(u"封に要点の字が無い: %s" % phrase[:20])
    if seal_words(seal) != WORD_TABLE:
        out.append(u"封の手がかりの語の表が門の表と違う")
    if tuple(ms.WORDS.items()) != tuple(WORD_TABLE.items()):
        out.append(u"script の手がかりの語の表が封の表と違う")
    if (tuple(ms.STAGES), ms.CLASS_ORDER, ms.FUTURE_GATE, ms.REASON_P, ms.PLAN_CAT) != ((1, 2, 3), u"PFEHW", u"future_period", REASON_P, u"外(見積り・計画)"):
        out.append(u"段・類の順・future_period・reason・見積り・計画の札の名が封と違う")
    if (ms.HIT_FLOOR_NUM, ms.HIT_FLOOR_DEN) != (95, 100):
        out.append(u"当たる率の下限が 95% でない")
    if (ms.PROFILE, tuple(ms.STATES)) != (u"P33E", STATES):
        out.append(u"profile か state の名が違う")
    if (ms.K_WIRE, ms.K_ALL, ms.K_P, ms.K_LABEL, ms.K_CLASS, ms.K_OVER, ms.K_PRED) != (K_WIRE, K_ALL, K_P, K_LABEL, K_CLASS, K_OVER, K_PRED):
        out.append(u"記録の欄の名が門と違う")
    if (ms.SC_SCRIPT_REL, ms.SC_RECORD_REL) != (SC_SCRIPT_REL, SC_RECORD_REL):
        out.append(u"便 SC の script・記録の path が違う")
    if ms.ROW_COLUMNS[:6] != SCT.MS.ROW_COLUMNS[:6] or (ms.C_BATCH, ms.C_BOOK, ms.C_SIDE, ms.C_SI, ms.C_POS, ms.C_STATE) != (SCT.MS.C_BATCH, SCT.MS.C_BOOK, SCT.MS.C_SIDE, SCT.MS.C_SI, SCT.MS.C_POS, SCT.MS.C_STATE):
        out.append(u"行の先頭 6 欄が便 SC と違う(札の引き方は便 SC の関数を呼ぶ)")
    return out


def seal_table_problems(ms=None, seal=None):
    u"""封 §1 の表(2 行)+ 便 SC の封 §1 の表(21 行)の (path, sha256) が門・script の表と同じ。"""
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    rows = re.findall(r"\| `([^`]+)` \| `([0-9a-f]{64})` \|", seal)
    sc_rows = re.findall(r"\| `([^`]+)` \| `([0-9a-f]{64})` \|", read(SC_SEAL_REL))
    out = []
    if sc_rows + rows != list(INPUT_SHAS) or len(rows) != 2 or len(sc_rows) != 21:
        out.append(u"封の入力の表(便 SC の封の表 + 2 行)が門の表と違う")
    if [(rel, sha) for _no, rel, sha in ms.INPUTS] != list(INPUT_SHAS) or [no for no, _r, _s in ms.INPUTS] != list(range(1, 24)):
        out.append(u"script の入力の表が門の表と違う")
    return out


def seal_history_problems(root=REPO):
    u"""封の file の履歴は 1 commit(e69b733c)で、今の file はその commit の blob と 1 字も変わらない。"""
    c = PR.added_commits(root, PREFIX + SEAL_REL)
    if len(c) != 1 or not c[0].startswith(SEAL_COMMIT_SHORT):
        return [u"封の commit が履歴に 1 つで %s に決まらない" % SEAL_COMMIT_SHORT]
    rc, log = PR.git_in(root, "log", "--format=%H", "--", PREFIX + SEAL_REL)
    if len([x for x in log.split() if x]) != 1:
        return [u"封の file の履歴が 1 commit でない(封の後に封が書き換えられた)"]
    rc, blob = PR.git_in(root, "show", "%s:%s" % (c[0], PREFIX + SEAL_REL))
    if seal_text().rstrip(u"\n") != blob.rstrip(u"\n"):
        return [u"今の封が封の commit の blob と違う"]
    return []


# ---------------------------------------------------------------- 2. 入力・前の文書
def input_sha_problems(ms=None):
    ms = ms or MS
    out = []
    if [(rel, sha) for _no, rel, sha in ms.INPUTS] != list(INPUT_SHAS):
        out.append(u"script の入力の表が門の表と違う")
    out.extend(u"入力の sha256 が表と違う: %s" % rel for rel, want in INPUT_SHAS if sha_of(rel) != want)
    return out


def input_wire_problems(ms=None):
    u"""``check_inputs`` が、表のとおりの複製では通り、1 byte 違う複製では止まる(23 件のどれでも)。"""
    ms = ms or MS
    out = []
    tmp = tempfile.mkdtemp(prefix="pa_inputs_")
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


def prior_docs_problems(root=REPO):
    s = PR.added_commits(root, PREFIX + SEAL_REL)
    if len(s) != 1:
        return [u"封の commit が履歴に 1 つで決まらない"]
    rc, txt = PR.git_in(root, "diff", "--name-only", s[0], "HEAD", "--", *[PREFIX + d for d in PRIOR_DOCS])
    if rc != 0:
        return [u"git diff が失敗した"]
    return [u"前の便の文書が封の後に変わっている: %s" % ln for ln in txt.splitlines() if ln.strip()]


def prior_scripts_problems(root=REPO):
    u"""前の便の script と記録(便 SC のものを含む)が封の commit から 0 行(入力の sha256 とは別に履歴で見る)。"""
    s = PR.added_commits(root, PREFIX + SEAL_REL)
    if len(s) != 1:
        return [u"封の commit が履歴に 1 つで決まらない"]
    rc, txt = PR.git_in(root, "diff", "--name-only", s[0], "HEAD", "--", *[PREFIX + r for r in INPUT_RELS])
    if rc != 0:
        return [u"git diff が失敗した"]
    return [u"前の便の script・記録が封の後に変わっている: %s" % ln for ln in txt.splitlines() if ln.strip()]


# ---------------------------------------------------------------- 3. engine は 0 行・順序
def engine_zero_problems(root=REPO, seal_rel=SEAL_REL, prefix=PREFIX):
    return SCT.engine_zero_problems(root, seal_rel, prefix)


def order_of(root=REPO, seal_short=SEAL_COMMIT_SHORT, others=None):
    others = list(ORDER_FILES) if others is None else others
    return PR.order_problems(root, PREFIX, SEAL_REL, seal_short, [], others)


# ---------------------------------------------------------------- 4. 規則(封 §2-3・§2-4)
def rule_problems(ms=None):
    u"""語の表(1 語ずつ・その類だけ)・部分一致。"""
    ms = ms or MS
    out = []
    for cls, words in WORD_TABLE.items():
        for w in words:
            got = [c for c in u"PFE" if ms.has_word(u"前" + w + u"後", c)]
            if got != [cls]:
                out.append(u"語「%s」が類 %s だけに当たらない: %s" % (w, cls, got))
            if ms.has_pf(u"前" + w + u"後") is not (cls in u"PF"):
                out.append(u"has_pf が語「%s」(類 %s)で違う(P か F だけ。E は含めない)" % (w, cls))
    if ms.has_word(u"売上高は増加した", u"P") or ms.has_word(u"売上高は増加した", u"F") or ms.has_word(u"売上高は増加した", u"E") or ms.has_pf(u"売上高は増加した"):
        out.append(u"語の無い字が当たる")
    if not ms.has_word(u"来期の売上は", u"F") or ms.has_word(u"来期", u"P") or not ms.has_word(u"見込みです", u"P"):
        out.append(u"部分一致(語が字の並びに含まれるか)でない")
    if ms.has_word(u"見 込", u"P") or ms.has_word(u"込見", u"P"):
        out.append(u"語の途中に字が入る・並びが逆でも当たる")
    return out


def stage_problems(ms=None):
    u"""段の包含・前の字と文の全部・見出しは P か F だけ・E は前の字だけ・W の決め。(hits は段 1・2・3 の字)"""
    ms = ms or MS
    out = []

    def sh(prefix, whole, heading=None):
        return ms.stage_hits(prefix, whole, heading)
    cases = [
        ((u"売上高は", u"売上高は100円", None), (u"", u"", u"")),
        ((u"計画では売上高は", u"計画では売上高は100円", None), (u"P", u"P", u"P")),                       # 段 1 は前の字の P
        ((u"予想では", u"予想では100円", None), (u"", u"F", u"F")),                                       # F は段 2 から
        ((u"売上高は", u"売上高は100円", u"業績予想"), (u"", u"H", u"H")),                                  # 見出しの F
        ((u"売上高は", u"売上高は100円", u"来期の見通し"), (u"", u"H", u"H")),                              # 見出しの P と F は H 1 つ
        ((u"売上高は", u"売上高は100円", u"見積りの前提"), (u"", u"", u"")),                               # 見出しの E は入れない
        ((u"売上高は", u"売上高は100円", u"その他"), (u"", u"", u"")),
        ((u"売上高は", u"売上高は100円の見込みです", None), (u"", u"", u"W")),                              # 数の後ろの P は段 3 の W
        ((u"売上高は", u"売上高は100円で予定です", None), (u"", u"", u"W")),                                # 数の後ろの F も W
        ((u"見積りの売上高は", u"見積りの売上高は100円", None), (u"", u"", u"E")),                          # E は前の字なら段 3
        ((u"売上高は", u"売上高は100円で試算", None), (u"", u"", u"")),                                      # E は文の全部では見ない
        ((u"計画の", u"計画の100円で、予定", None), (u"P", u"P", u"P")),                                    # 前の字で当たれば W は付けない
        ((u"予定の", u"予定の100円で、見込", None), (u"", u"F", u"F")),
        ((u"予定の計画", u"予定の計画100円", None), (u"P", u"PF", u"PF")),
        ((u"見積りで", u"見積りで100円の見通し", None), (u"", u"", u"EW")),                                  # 前の字の E と後ろの P の両方
        ((u"見積りの予想", u"見積りの予想100円", u"計画"), (u"", u"FH", u"FEH")),
    ]
    for (args, want) in cases:
        got = sh(*args)
        if got != want:
            out.append(u"stage_hits が手計算と違う: %s → %s(手計算 %s)" % (args[0], got, want))
    for (args, _w) in cases:
        a, b, c = sh(*args)
        if not (set(a) <= set(b) <= set(c)):
            out.append(u"段の包含が成り立たない: %s" % ((a, b, c),))
        if set(a) - set(u"P") or set(b) - set(u"PFH") or set(c) - set(u"PFEHW"):
            out.append(u"段が許さない類が入る: %s" % ((a, b, c),))
    return out


def hh(ms, sentences, specs):
    u"""作り物の [(raw, verify)] と文の列から unit_digest。specs = [(文の番号, 数の字, state, reason, p27_gate)]。raw に p27_gate・verify に reason を置く(本物と同じ側)。"""
    pairs = []
    for spec in specs:
        si, token, state = spec[0], spec[1], spec[2]
        reason = spec[3] if len(spec) > 3 else None
        gate = spec[4] if len(spec) > 4 else None
        s = sentences[si]
        pos = s.index(token)
        raw = {u"sentence": si, u"pos": pos, u"span": s[max(0, pos - 30):pos + len(token) + 10]}
        if gate is not None:
            raw[u"p27_gate"] = gate
        pairs.append((raw, {u"state": state, u"reason": reason, u"pointers": []}))
    return ms.unit_digest(pairs, sentences), pairs


def digest_problems(ms=None):
    u"""見出し・最も近い見出し・member を問わない・段・P の行の数え方・位置の確かめを unit_digest で。"""
    ms = ms or MS
    out = []
    sent = [u"経営成績の見通し", u"売上高は100円となりました。", u"その他", u"売上高は200円でした。", u"来期の売上高は300円で、前期の400円です。", u"売上高は500円の見込みです。",
            u"見積りの売上高は600円。", u"当社の売上は700円でした。", u"計画800円。", u"売上高は900円で試算。", u"売上高は1000円で予定。", u"売上高は5円予定"]
    specs = [(1, u"100", G), (3, u"200", VM), (4, u"300", G), (4, u"400", VM), (5, u"500", G), (6, u"600", VM), (7, u"700", G), (8, u"800", G), (9, u"900", VM), (10, u"1000", G), (11, u"5", G)]
    d, pairs = hh(ms, sent, specs)
    rows = dict(((r[0], r[1]), r[2:]) for r in d[u"rows"])
    pos = lambda si, tok: sent[si].index(tok)
    want = {
        (1, pos(1, u"100")): [u"G", u"", u"H", u"H"],                                    # 最も近い見出し 0(見通 = P)→ H
        (3, pos(3, u"200")): [u"V", u"", u"", u""],                                      # 最も近い見出し 2(語なし)。0 の P は見ない
        (4, pos(4, u"300")): [u"G", u"", u"F", u"F"],                                    # 前の字に来期
        (4, pos(4, u"400")): [u"V", u"", u"F", u"F"],                                    # 前の字は文の頭から数の手前まで(前の数の後ろも入る)
        (5, pos(5, u"500")): [u"G", u"", u"", u"W"],                                     # 数の後ろの見込み → W
        (6, pos(6, u"600")): [u"V", u"", u"", u"E"],
        (7, pos(7, u"700")): [u"G", u"", u"", u""],
        (8, pos(8, u"800")): [u"G", u"P", u"P", u"P"],                                   # 前の字が「計画」で終わる(位置の 1 字前では当たらない)
        (9, pos(9, u"900")): [u"V", u"", u"", u""],                                      # E は数の後ろ(文の全部)では見ない
        (10, pos(10, u"1000")): [u"G", u"", u"", u"W"],                                  # 数の後ろの F(予定)も W
        (11, pos(11, u"5")): [u"G", u"", u"", u"W"],                                     # 前の字は位置の手前まで(数の直後の予定は前の字に入らない)
    }
    for k, v in want.items():
        if rows.get(k) != v:
            out.append(u"unit_digest の行 %s が手計算と違う: %s(手計算 %s)" % (k, rows.get(k), v))
    if len(d[u"rows"]) != 11 or [(r[0], r[1]) for r in d[u"rows"]] != sorted((r[0], r[1]) for r in d[u"rows"]):
        out.append(u"unit_digest の行が結んだ行 11 個・(文の番号, 位置)の順でない")
    if any(len(r) != 6 for r in d[u"rows"]):
        out.append(u"unit_digest の行が 6 欄でない")
    # 数の claim を持つ短い文は見出しでない(後ろの行の最も近い見出しにならない)
    sent2 = [u"その他", u"計画は5円", u"売上高は6円。"]
    d2, _p = hh(ms, sent2, [(1, u"5", G), (2, u"6", VM)])
    if [r[2:] for r in d2[u"rows"]] != [[u"G", u"P", u"P", u"P"], [u"V", u"", u"", u""]]:
        out.append(u"数の claim を持つ短い文が見出しに数えられる: %s" % ([r[2:] for r in d2[u"rows"]],))
    # 見出しの E は入れない・F は入れる
    sent3 = [u"見積りの前提", u"売上高は50円。", u"予定の前提", u"売上高は60円。"]
    d3, _p = hh(ms, sent3, [(1, u"50", G), (3, u"60", VM)])
    if [r[2:] for r in d3[u"rows"]] != [[u"G", u"", u"", u""], [u"V", u"", u"H", u"H"]]:
        out.append(u"見出しの E が入る・F が入らない: %s" % ([r[2:] for r in d3[u"rows"]],))
    # 結んだ行でない state は行に入らない・triples には入る。member の欄の有無は行に効かない
    d4, _p = hh(ms, sent, [(1, u"100", UN), (3, u"200", PN), (5, u"500", G)])
    if len(d4[u"rows"]) != 1 or [t[2] for t in d4[u"triples"]] != [UN, PN, G]:
        out.append(u"結んだ行でない state が行に入る・triples に入らない")
    raw_m = {u"sentence": 4, u"pos": sent[4].index(u"300"), u"span": sent[4][:40], u"member": u"jpcrp:XMember"}
    d5 = ms.unit_digest([(raw_m, {u"state": G, u"reason": None, u"pointers": []})], sent)
    if [r[2:] for r in d5[u"rows"]] != [[u"G", u"", u"F", u"F"]]:
        out.append(u"member が入っている行が止められない(member は問わない): %s" % ([r[2:] for r in d5[u"rows"]],))
    # P の行の数え方: P の行(reason が target_or_plan の UNVERIFIABLE)・future_period は raw の欄・文の全部に類 P の語
    sent6 = [u"来期の計画では売上高は100円。", u"予定の売上は5円。", u"売上高は7円。", u"計画の費用は8円。", u"売上高は9円で見通し。", u"予定の売上は11円。", u"計画の売上は12円。"]
    d6, _p = hh(ms, sent6, [(0, u"100", UN, REASON_P, None), (1, u"5", UN, REASON_P, u"future_period"), (2, u"7", UN, REASON_P, None), (3, u"8", UN, u"no_fact", None),
                            (4, u"9", UN, REASON_P, None), (5, u"11", UN, REASON_P, None), (6, u"12", G, REASON_P, None)])
    c = d6[u"counts"]
    got = dict((k, v) for k, v in c.items() if k.startswith((u"P の行", u"当たる", u"当たらなかった")))
    wantc = {u"P の行": 5, u"P の行のうち決算期の字の規則(future_period)で止まった行": 1, u"P の行のうち future_period 以外(当たるはずの行)": 4,
             u"当たるはずの行のうち文の全部に類 P の語が在る": 2, u"当たるはずの行のうち文の全部に類 P の語が無い": 2, u"当たらなかった行の p27_gate: None": 2}
    if got != wantc:
        out.append(u"P の行の数え方が手計算(P 5・future 1・以外 4・当たる 2・当たらない 2。reason が違う行と G の行は P に数えない・F だけの文は当たらない)と違う: %s" % (got,))
    pc = ms.p_cells(collections.Counter(wantc))
    if (pc[ms.P_KEYS[0]], pc[ms.P_KEYS[2]], pc[ms.P_KEYS[3]], pc[ms.P_KEYS[4]], dict(pc[u"当たる率(当たるはずの行のうち)"]), dict(pc[u"当たらなかった行の p27_gate の内訳"])) \
            != (5, 4, 2, 2, {u"分子": 2, u"分母": 4, u"率": u"50.0%"}, {u"None": 2}):
        out.append(u"p_cells が手計算と違う")
    # 位置の確かめ(便 SC の関数)
    if stops(ms, ms.unit_digest, [({u"sentence": 0, u"pos": 1, u"span": None}, {u"state": G, u"pointers": []})], [u"売上高は100円"]) is not True:
        out.append(u"位置が数の字で始まらない行が止まらない")
    if stops(ms, ms.unit_digest, [({u"sentence": 0, u"pos": 4, u"span": u"売上高は101円"}, {u"state": G, u"pointers": []})], [u"売上高は100円"]) is not True:
        out.append(u"span が位置の前後と合わない行が止まらない")
    if stops(ms, ms.unit_digest, [({u"sentence": 3, u"pos": 0, u"span": None}, {u"state": G, u"pointers": []})], [u"1"]) is not True:
        out.append(u"文の番号が文の列の外の行が止まらない")
    s5 = u"利益は 1,060百万円"
    d7 = ms.unit_digest([({u"sentence": 0, u"pos": s5.index(u" "), u"span": s5}, {u"state": G, u"pointers": []})], [s5])
    if d7[u"counts"].get(u"位置: 符号か空白から") != 1:
        out.append(u"数の字の手前の空白から始まる位置が通らない")
    # 前の字は位置の手前まで(数の後ろの字は前の字に入らない)
    d8, _p = hh(ms, [u"売上高は100円で、計画は5円"], [(0, u"100", G)])
    if d8[u"rows"][0][3:] != [u"", u"", u"W"]:
        out.append(u"前の字が位置の手前まででない(数の後ろの P が段 1 に入る)")
    if ms.empty_digest()[u"cut"] is not False:
        out.append(u"切れない単位の結果が切れたになっている")
    return out


# ---------------------------------------------------------------- 5. 札の引き方(封 §2-5 の 2)
def label_problems(ms=None):
    u"""札の読みの検査(本物の読みの記録)・「見積り・計画」の札は便ごとに型の字が違う・同じ state で引けた行だけ。"""
    ms = ms or MS
    out = []
    recs = real_recs()
    labels = ms.SC.build_labels(recs)
    cnt = collections.Counter((lab[u"便"], lab[u"state"]) for lab in labels)
    if len(labels) != 133 + 169 + 120 or cnt.get((u"TSS", u"G"), 0) != 0:
        out.append(u"札つきの行の数が(KAM 133・YS 169・TSS 120・TSS の G は 0)でない: %s" % (dict(cnt),))
    plan = collections.Counter(lab[u"便"] for lab in labels if lab[u"state"] == u"V" and ms.is_plan(lab))
    if dict(plan) != {u"YS": 7, u"TSS": 20}:
        out.append(u"「見積り・計画」の札の V の行が(YS 7・TSS 20・KAM 0)でない: %s" % (dict(plan),))
    ga = collections.Counter(lab[u"便"] for lab in labels if lab[u"state"] == u"G" and lab[u"型"] == u"a")
    if dict(ga) != {u"KAM": 89, u"YS": 125}:
        out.append(u"札 a の G の行が(KAM 89・YS 125)でない: %s" % (dict(ga),))
    if u"見積り・計画" not in ms.AT.out_reasons(u"KAM") or u"見積り・計画" not in ms.AT.out_reasons(u"TSS") or ms.PLAN_CAT != u"外(%s)" % u"見積り・計画":
        out.append(u"便 AT の写しの表の「見積り・計画」の名前が PLAN_CAT と違う")
    lk = lambda b: ms.AT.table_lookup(b)
    L = lambda batch, key: ms.SC.label_row(batch, 1, None, 1, 1, u"V", key, None, lk(batch))
    for batch, key, want in ((u"KAM", u"イ", True), (u"YS", u"イ", True), (u"TSS", u"ウ", True), (u"KAM", u"ウ", False), (u"YS", u"ウ", False), (u"TSS", u"イ1", False), (u"TSS", u"イ3", False),
                             (u"KAM", u"キ", False), (u"TSS", u"キ", False), (u"KAM", u"ア", False), (u"KAM", u"ク", False), (u"TSS", u"ク", False)):
        if ms.is_plan(L(batch, key)) is not want:
            out.append(u"「見積り・計画」の札の判定が違う: %s %s" % (batch, key))
    if not ms.is_drop(L(u"KAM", u"ク")) or ms.is_drop(L(u"KAM", u"イ")) or not ms.is_drop(L(u"TSS", u"ク")):
        out.append(u"分母から除く札の判定が違う")
    return out


def R(batch, n, side, si, pos, state, h1, h2, h3):
    return [batch, n, side, si, pos, state, h1, h2, h3]


def hand_labels():
    u"""札つきの行(作り物)。"""
    ms = MS
    lk = lambda b: ms.AT.table_lookup(b)
    L = lambda batch, n, side, si, pos, state, key, diff=None: ms.SC.label_row(batch, n, side, si, pos, state, key, diff, lk(batch))
    K, Y, T = u"KAM", u"YS", u"TSS"
    return [
        L(K, 1, u"連結", 1, 1, u"V", u"イ"), L(K, 1, u"連結", 2, 1, u"V", u"イ"), L(K, 1, u"連結", 3, 1, u"V", u"ア"), L(K, 1, u"連結", 4, 1, u"V", u"ク"), L(K, 1, u"連結", 5, 1, u"V", u"キ"),
        L(Y, 5, u"研究開発活動", 1, 1, u"V", u"イ"), L(Y, 5, u"研究開発活動", 2, 1, u"V", u"イ"), L(Y, 5, u"研究開発活動", 3, 1, u"V", u"ア"),
        L(T, 7, None, 1, 1, u"V", u"ウ"), L(T, 7, None, 2, 1, u"V", u"イ1"), L(T, 7, None, 3, 1, u"V", u"ウ"), L(T, 7, None, 4, 1, u"V", u"ク"),
        L(K, 1, u"連結", 10, 1, u"G", u"a"), L(K, 1, u"連結", 11, 1, u"G", u"a"), L(K, 1, u"連結", 12, 1, u"G", u"a"), L(K, 1, u"連結", 13, 1, u"G", u"b", u"範囲"), L(K, 1, u"連結", 14, 1, u"G", u"c"),
        L(Y, 5, u"配当政策", 10, 1, u"G", u"a"), L(Y, 5, u"配当政策", 11, 1, u"G", u"b", u"範囲")]


def hand_rows():
    u"""札つきの行・札なしの行を持つ、手計算の作り物の結んだ行(便・state・段で非対称。止めた段が 1・2・3 に分かれる)。"""
    K, Y, T = u"KAM", u"YS", u"TSS"
    return [
        R(K, 1, u"連結", 1, 1, u"V", u"P", u"PF", u"PF"), R(K, 1, u"連結", 2, 1, u"G", u"", u"", u""), R(K, 1, u"連結", 3, 1, u"V", u"", u"", u"E"), R(K, 1, u"連結", 4, 1, u"V", u"", u"", u""),
        R(K, 1, u"連結", 10, 1, u"G", u"P", u"P", u"P"), R(K, 1, u"連結", 11, 1, u"G", u"", u"", u""), R(K, 1, u"連結", 12, 1, u"V", u"", u"H", u"H"),
        R(K, 1, u"連結", 13, 1, u"G", u"", u"", u"W"), R(K, 1, u"連結", 14, 1, u"G", u"", u"F", u"F"), R(K, 2, u"単体", 1, 1, u"G", u"", u"", u"E"),
        R(Y, 5, u"研究開発活動", 1, 1, u"V", u"P", u"P", u"P"), R(Y, 5, u"研究開発活動", 2, 1, u"V", u"", u"", u""), R(Y, 5, u"研究開発活動", 3, 1, u"V", u"", u"", u"W"),
        R(Y, 5, u"配当政策", 10, 1, u"G", u"", u"F", u"F"), R(Y, 5, u"配当政策", 11, 1, u"G", u"", u"", u""), R(Y, 5, u"配当政策", 20, 1, u"G", u"", u"H", u"H"),
        R(T, 7, None, 1, 1, u"V", u"", u"F", u"F"), R(T, 7, None, 2, 1, u"V", u"", u"", u""), R(T, 7, None, 3, 1, u"V", u"", u"", u"E"), R(T, 7, None, 4, 1, u"V", u"", u"", u""),
        R(T, 7, None, 10, 1, u"G", u"P", u"P", u"P"), R(T, 7, None, 11, 1, u"G", u"", u"H", u"H"), R(T, 7, None, 12, 1, u"G", u"", u"", u""), R(T, 7, None, 13, 1, u"G", u"", u"", u"W")]


#: 便 SC の段 2 で止めた行(手計算の作り物。便 SC の記録の「段 2 の当たりの類」の欄が空でない行)
SC_STOPS = ((u"KAM", 1, u"連結", 1, 1), (u"KAM", 1, u"連結", 3, 1), (u"YS", 5, u"研究開発活動", 1, 1), (u"TSS", 7, None, 3, 1), (u"KAM", 1, u"連結", 10, 1), (u"TSS", 7, None, 10, 1))


def sc_rec_of(rows, stop_keys):
    u"""作り物の便 SC の記録(行の欄は便 SC の行の欄)。``stop_keys`` の行だけ「段 2 の当たりの類」に S を入れる。"""
    return {u"行": [[r[0], r[1], r[2], r[3], r[4], r[5], True, u"", u"S" if tuple(r[:5]) in stop_keys else u"", u""] for r in rows]}


def fr_of(n, d):
    return MS.rate(n, d)


def tally_problems(ms=None):
    u"""引けた行だけが分母・「見積り・計画」/「それ以外」/ 除く・G の a・b・c・全体の便ごと・類ごとの数・P の行・重なり・予測の数を、手計算の作り物で。"""
    ms = ms or MS
    out = []
    labels = hand_labels()
    rows = hand_rows()
    idx = ms.index_rows(rows)
    sc_idx = ms.sc_index(sc_rec_of(rows, SC_STOPS))
    # --- match: 同じ state で引けた行だけ
    m = ms.match(labels, idx)
    got = [(x[1] is not None, x[2]) for x in m[:5]]
    if got != [(True, None), (False, u"state が違う"), (True, None), (True, None), (False, u"行が無い")]:
        out.append(u"match の引けた・引けなかった理由が手計算と違う: %s" % (got,))
    # --- V の札
    vms, gms = ms.split_labels(labels, idx)
    if [len(vms[b]) for b in (u"TSS", u"KAM", u"YS")] != [4, 5, 3] or [len(gms[b]) for b in (u"KAM", u"YS")] != [5, 2]:
        out.append(u"split_labels の便ごとの札の数が(V: TSS 4・KAM 5・YS 3 / G: KAM 5・YS 2)でない")
    vt = ms.v_tally(vms)

    def cl(c):
        return (c[u"札の行"], c[u"引けた行(分母)"], dict(c[u"止めた行"]))
    k = vt[u"KAM"]
    c = k[u"全体"]
    if (cl(c), c[u"引けなかった行"], dict(c[u"引けなかった理由"])) != ((5, 3, {S1: 1, S2: 1, S3: 2}), 2, {u"行が無い": 1, u"state が違う": 1}):
        out.append(u"V の札 KAM の全体の数が手計算(5・3・止めた 1/1/2・理由 1+1)と違う: %s" % (dict(c),))
    if cl(k[u"見積り・計画"]) != (2, 1, {S1: 1, S2: 1, S3: 1}) or dict(k[u"見積り・計画"][u"引けなかった理由"]) != {u"行が無い": 0, u"state が違う": 1}:
        out.append(u"V の札 KAM の見積り・計画が手計算(2・1・止めた 1/1/1・state が違う 1)と違う")
    if cl(k[u"それ以外(分母から除く札は除く)"]) != (2, 1, {S1: 0, S2: 0, S3: 1}) or cl(k[u"分母から除く札"]) != (1, 1, {S1: 0, S2: 0, S3: 0}):
        out.append(u"V の札 KAM のそれ以外・分母から除く札が手計算と違う")
    a = k[u"属性ごと"]
    if cl(a[u"外(見積り・計画)"]) != (2, 1, {S1: 1, S2: 1, S3: 1}) or cl(a[u"範囲"]) != (1, 1, {S1: 0, S2: 0, S3: 1}) or cl(a[u"外(符号)"]) != (1, 0, {S1: 0, S2: 0, S3: 0}):
        out.append(u"V の札 KAM の属性ごとの数が手計算と違う")
    if a[u"1 株あたり"][u"札の行"] != 0:
        out.append(u"1 株あたりの札の行が 0 でない(作りで 0)")
    y = vt[u"YS"]
    if cl(y[u"全体"]) != (3, 3, {S1: 1, S2: 1, S3: 2}) or cl(y[u"見積り・計画"]) != (2, 2, {S1: 1, S2: 1, S3: 1}) or cl(y[u"それ以外(分母から除く札は除く)"]) != (1, 1, {S1: 0, S2: 0, S3: 1}):
        out.append(u"V の札 YS の数が手計算と違う")
    t = vt[u"TSS"]
    if cl(t[u"全体"]) != (4, 4, {S1: 0, S2: 1, S3: 2}) or cl(t[u"見積り・計画"]) != (2, 2, {S1: 0, S2: 1, S3: 2}) or cl(t[u"それ以外(分母から除く札は除く)"]) != (1, 1, {S1: 0, S2: 0, S3: 0}) \
            or cl(t[u"属性ごと"][u"範囲"]) != (1, 1, {S1: 0, S2: 0, S3: 0}) or cl(t[u"分母から除く札"]) != (1, 1, {S1: 0, S2: 0, S3: 0}):
        out.append(u"V の札 TSS の数が手計算(TSS の イ1 は範囲・ウ が見積り・計画)と違う")
    tt = vt[u"合計"]
    if cl(tt[u"見積り・計画"]) != (6, 5, {S1: 2, S2: 3, S3: 4}) or cl(tt[u"それ以外(分母から除く札は除く)"]) != (4, 3, {S1: 0, S2: 0, S3: 2}) or cl(tt[u"分母から除く札"]) != (2, 2, {S1: 0, S2: 0, S3: 0}):
        out.append(u"V の札の合計が手計算(見積り・計画 6・5・2/3/4、それ以外 4・3・0/0/2、除く 2・2)と違う: %s" % (cl(tt[u"見積り・計画"]),))
    # --- G の札
    gt = ms.g_tally(gms)
    kk = gt[u"KAM"]
    if cl(kk[u"全体"]) != (5, 4, {S1: 1, S2: 2, S3: 3}) or dict(kk[u"全体"][u"引けなかった理由"]) != {u"行が無い": 0, u"state が違う": 1}:
        out.append(u"G の札 KAM の全体が手計算(5・4・1/2/3・state が違う 1)と違う")
    if cl(kk[u"型ごと"][u"a"]) != (3, 2, {S1: 1, S2: 1, S3: 1}) or cl(kk[u"型ごと"][u"b"]) != (1, 1, {S1: 0, S2: 0, S3: 1}) or cl(kk[u"型ごと"][u"c"]) != (1, 1, {S1: 0, S2: 1, S3: 1}):
        out.append(u"G の札 KAM の a・b・c が手計算と違う")
    if cl(gt[u"YS"][u"型ごと"][u"a"]) != (1, 1, {S1: 0, S2: 1, S3: 1}) or cl(gt[u"YS"][u"型ごと"][u"b"]) != (1, 1, {S1: 0, S2: 0, S3: 0}):
        out.append(u"G の札 YS の a・b が手計算と違う")
    if cl(gt[u"合計"][u"型ごと"][u"a"]) != (4, 3, {S1: 1, S2: 2, S3: 2}):
        out.append(u"G の札の合計の a が手計算(4・3・1/2/2)と違う")
    # --- 結んだ行の全部
    ta = ms.tally_all(rows)
    kv, kg = ta[u"KAM"][u"全体"][u"V"], ta[u"KAM"][u"全体"][u"G"]
    if (kv[u"結んだ行"], dict(kv[u"止めた行"]), kg[u"結んだ行"], dict(kg[u"止めた行"])) != (4, {S1: 1, S2: 2, S3: 3}, 6, {S1: 1, S2: 2, S3: 4}):
        out.append(u"結んだ行 KAM が手計算(V 4・1/2/3、G 6・1/2/4)と違う: %s %s" % (dict(kv[u"止めた行"]), dict(kg[u"止めた行"])))
    if dict(ta[u"KAM"][u"文の種類別"][u"連結"][u"G"][u"止めた行"]) != {S1: 1, S2: 2, S3: 3} or ta[u"KAM"][u"文の種類別"][u"単体"][u"G"][u"結んだ行"] != 1 \
            or dict(ta[u"KAM"][u"文の種類別"][u"単体"][u"G"][u"止めた行"]) != {S1: 0, S2: 0, S3: 1} or ta[u"KAM"][u"文の種類別"][u"単体"][u"V"][u"結んだ行"] != 0:
        out.append(u"結んだ行 KAM の文の種類別が手計算と違う")
    yv, yg = ta[u"YS"][u"全体"][u"V"], ta[u"YS"][u"全体"][u"G"]
    if (yv[u"結んだ行"], dict(yv[u"止めた行"]), yg[u"結んだ行"], dict(yg[u"止めた行"])) != (3, {S1: 1, S2: 1, S3: 2}, 3, {S1: 0, S2: 2, S3: 2}):
        out.append(u"結んだ行 YS が手計算(V 3・1/1/2、G 3・0/2/2)と違う")
    if ta[u"YS"][u"節別"][u"研究開発活動"][u"V"][u"結んだ行"] != 3 or ta[u"YS"][u"節別"][u"配当政策"][u"G"][u"結んだ行"] != 3 or ta[u"YS"][u"節別"][u"設備投資等の概要"][u"V"][u"結んだ行"] != 0:
        out.append(u"結んだ行 YS の節別が手計算と違う")
    tv, tg = ta[u"TSS"][u"全体"][u"V"], ta[u"TSS"][u"全体"][u"G"]
    if (tv[u"結んだ行"], dict(tv[u"止めた行"]), tg[u"結んだ行"], dict(tg[u"止めた行"])) != (4, {S1: 0, S2: 1, S3: 2}, 4, {S1: 1, S2: 2, S3: 3}):
        out.append(u"結んだ行 TSS が手計算(V 4・0/1/2、G 4・1/2/3)と違う")
    if u"文の種類別" in ta[u"TSS"] or u"節別" in ta[u"TSS"]:
        out.append(u"TSS に文の種類別・節別が在る")
    # --- 当たった類
    tc = ms.tally_class(rows)
    g3, g2, g1 = tc[u"合計"][S3][u"G"], tc[u"合計"][S2][u"G"], tc[u"合計"][S1][u"G"]
    if dict(g3) != {u"止めた行": 9, u"P": 2, u"F": 2, u"E": 1, u"H": 2, u"W": 2} or dict(g2) != {u"止めた行": 6, u"P": 2, u"F": 2, u"E": 0, u"H": 2, u"W": 0} \
            or dict(g1) != {u"止めた行": 2, u"P": 2, u"F": 0, u"E": 0, u"H": 0, u"W": 0}:
        out.append(u"当たった類 合計・G が手計算(段 3: 9・P2 F2 E1 H2 W2 / 段 2: 6 / 段 1: 2)と違う: %s" % (dict(g3),))
    v3 = tc[u"合計"][S3][u"V"]
    if dict(v3) != {u"止めた行": 7, u"P": 2, u"F": 2, u"E": 2, u"H": 1, u"W": 1}:
        out.append(u"当たった類 合計・段 3・V が手計算と違う: %s" % (dict(v3),))
    if dict(tc[u"TSS"][S3][u"G"]) != {u"止めた行": 3, u"P": 1, u"F": 0, u"E": 0, u"H": 1, u"W": 1} or dict(tc[u"YS"][S3][u"V"]) != {u"止めた行": 2, u"P": 1, u"F": 0, u"E": 0, u"H": 0, u"W": 1}:
        out.append(u"当たった類の便ごとの数が手計算と違う")
    # --- P の行の数(便ごと・文の種類ごと・合計)
    pb = [fbook(u"TSS", 1, [(None, fdig_c({u"P の行": 4, ms.P_KEYS[1]: 1, ms.P_KEYS[2]: 3, ms.P_KEYS[3]: 3, u"位置: 数字から": 9}))]),
          fbook(u"TSS", 2, [(None, fdig_c({u"P の行": 2, ms.P_KEYS[2]: 2, ms.P_KEYS[3]: 1, ms.P_KEYS[4]: 1, u"当たらなかった行の p27_gate: None": 1}))]),
          fbook(u"KAM", 1, [(u"連結", fdig_c({u"P の行": 5, ms.P_KEYS[2]: 5, ms.P_KEYS[3]: 5})), (u"単体", fdig_c({u"P の行": 1, ms.P_KEYS[1]: 1}))]),
          fbook(u"YS", 1, [(u"研究開発活動", fdig_c({u"P の行": 7, ms.P_KEYS[1]: 3, ms.P_KEYS[2]: 4, ms.P_KEYS[3]: 4})), (u"設備投資等の概要", fdig_c({})), (u"配当政策", fdig_c({u"P の行": 1, ms.P_KEYS[2]: 1, ms.P_KEYS[4]: 1}))])]
    tp = ms.tally_p(pb)
    z = lambda c: tuple(c[k] for k in ms.P_KEYS)
    if z(tp[u"TSS"][u"全体"]) != (6, 1, 5, 4, 1) or z(tp[u"KAM"][u"全体"]) != (6, 1, 5, 5, 0) or z(tp[u"YS"][u"全体"]) != (8, 3, 5, 4, 1) or z(tp[u"合計"][u"全体"]) != (20, 5, 15, 13, 2):
        out.append(u"tally_p の便ごと・合計が手計算(TSS 6・1・5・4・1 / KAM 6・1・5・5・0 / YS 8・3・5・4・1 / 合計 20・5・15・13・2)と違う: %s" % (z(tp[u"合計"][u"全体"]),))
    if z(tp[u"KAM"][u"文の種類別"][u"連結"]) != (5, 0, 5, 5, 0) or z(tp[u"KAM"][u"文の種類別"][u"単体"]) != (1, 1, 0, 0, 0) or z(tp[u"YS"][u"節別"][u"研究開発活動"]) != (7, 3, 4, 4, 0) \
            or z(tp[u"YS"][u"節別"][u"配当政策"]) != (1, 0, 1, 0, 1) or z(tp[u"YS"][u"節別"][u"設備投資等の概要"]) != (0, 0, 0, 0, 0):
        out.append(u"tally_p の文の種類別・節別が手計算と違う")
    if dict(tp[u"合計"][u"全体"][u"当たる率(当たるはずの行のうち)"]) != {u"分子": 13, u"分母": 15, u"率": u"86.7%"}:
        out.append(u"tally_p の合計の当たる率が手計算(13/15 = 86.7%)と違う")
    if dict(tp[u"TSS"][u"全体"][u"当たらなかった行の p27_gate の内訳"]) != {u"None": 1} or u"文の種類別" in tp[u"TSS"] or u"節別" in tp[u"TSS"]:
        out.append(u"tally_p の TSS の内訳・文の種類別が違う")
    # --- 重なり(便 SC の段 2 × この便の段 2)
    to = ms.tally_over(rows, labels, sc_idx)
    oc = lambda c: (c[u"行"], c[u"両方で止めた"], c[u"便 SC だけが止めた"], c[u"この便だけが止めた"], c[u"どちらも止めない"])
    if oc(to[u"V の札(引けた行)"][u"合計"][u"札つきの V の行(分母から除く札は除く)"]) != (8, 2, 2, 1, 3) or oc(to[u"V の札(引けた行)"][u"合計"][u"見積り・計画"]) != (5, 2, 1, 1, 1) \
            or oc(to[u"V の札(引けた行)"][u"合計"][u"それ以外"]) != (3, 0, 1, 0, 2) or oc(to[u"V の札(引けた行)"][u"合計"][u"分母から除く札"]) != (2, 0, 0, 0, 2):
        out.append(u"重なり V の札の合計が手計算(8・2/2/1/3、見積り・計画 5・2/1/1/1、それ以外 3・0/1/0/2、除く 2)と違う: %s" % (oc(to[u"V の札(引けた行)"][u"合計"][u"札つきの V の行(分母から除く札は除く)"]),))
    if oc(to[u"V の札(引けた行)"][u"KAM"][u"札つきの V の行(分母から除く札は除く)"]) != (2, 1, 1, 0, 0) or oc(to[u"V の札(引けた行)"][u"TSS"][u"札つきの V の行(分母から除く札は除く)"]) != (3, 0, 1, 1, 1):
        out.append(u"重なり V の札の便ごとが手計算と違う")
    if oc(to[u"G の札(KAM・YS。引けた行)"][u"合計"][u"a"]) != (3, 1, 0, 1, 1) or oc(to[u"G の札(KAM・YS。引けた行)"][u"KAM"][u"全体"]) != (4, 1, 0, 1, 2):
        out.append(u"重なり G の札が手計算(a 3・1/0/1/1、KAM 4・1/0/1/2)と違う: %s" % (oc(to[u"G の札(KAM・YS。引けた行)"][u"合計"][u"a"]),))
    if oc(to[u"結んだ行の全部"][u"KAM"][u"V"]) != (4, 1, 1, 1, 1) or oc(to[u"結んだ行の全部"][u"合計"][u"G"]) != (13, 2, 0, 4, 7) or oc(to[u"結んだ行の全部"][u"合計"][u"V"]) != (11, 2, 2, 2, 5):
        out.append(u"重なり 結んだ行の全部が手計算と違う: %s %s" % (oc(to[u"結んだ行の全部"][u"合計"][u"G"]), oc(to[u"結んだ行の全部"][u"合計"][u"V"])))
    if stops(ms, ms.sc_stopped, sc_idx, R(u"KAM", 9, u"連結", 1, 1, u"V", u"", u"", u"")) is not True:
        out.append(u"便 SC の記録に無い行で重なりの計算が止まらない")
    # --- 予測の数
    p = ms.predictions(rows, labels, sc_idx)
    keys = list(p.keys())
    pv = list(p.values())
    for i, pre in enumerate((u"分母の確かめ", u"PA-1", u"PA-2", u"PA-3", u"PA-4", u"PA-5", u"PA-5", u"PA-6", u"PA-7a", u"PA-7b", u"PA-8", u"PA-8")):
        if not keys[i].startswith(pre):
            out.append(u"予測の欄の順・名前が違う: %s" % keys[i][:8])
    nd = lambda n_, d_: (n_, d_)
    flat = lambda f: dict((s, (f[s][u"分子"], f[s][u"分母"])) for s in (S1, S2, S3))
    last = pv[0]
    if (last[u"「見積り・計画」の札の V の行(札)"], last[u"「見積り・計画」の札の V の行(引けた行)"], last[u"15 行未満"], last[u"V の札の行(札)"], last[u"V の札の行(引けた)"], last[u"G の札の行(札)"], last[u"G の札の行(引けた)"]) \
            != (6, 5, True, 12, 10, 7, 6):
        out.append(u"分母の確かめが手計算(見積り・計画 6・5・15 行未満 / V 12・10 / G 7・6)と違う: %s" % (dict(last),))
    if flat(pv[1][u"YS と TSS の合計"]) != {S1: nd(1, 4), S2: nd(2, 4), S3: nd(3, 4)} or flat(pv[1][u"3 便の合計"]) != {S1: nd(2, 5), S2: nd(3, 5), S3: nd(4, 5)} \
            or flat(pv[1][u"KAM"]) != {S1: nd(1, 1), S2: nd(1, 1), S3: nd(1, 1)} or flat(pv[1][u"YS"]) != {S1: nd(1, 2), S2: nd(1, 2), S3: nd(1, 2)} or flat(pv[1][u"TSS"]) != {S1: nd(0, 2), S2: nd(1, 2), S3: nd(2, 2)}:
        out.append(u"PA-1 の分子・分母が手計算(YS と TSS 1・2・3 / 4、3 便 2・3・4 / 5)と違う")
    if dict(pv[2][u"YS と TSS の合計"]) != dict(pv[1][u"YS と TSS の合計"][S1]):
        out.append(u"PA-2 の欄が PA-1 の段 1 と違う")
    if flat(pv[3][u"KAM と YS の合計"]) != {S1: nd(1, 3), S2: nd(2, 3), S3: nd(2, 3)} or flat(pv[3][u"KAM"]) != {S1: nd(1, 2), S2: nd(1, 2), S3: nd(1, 2)} or flat(pv[3][u"YS"]) != {S1: nd(0, 1), S2: nd(1, 1), S3: nd(1, 1)}:
        out.append(u"PA-3 の分子・分母が手計算(KAM と YS 1・2・2 / 3)と違う")
    if flat(pv[4]) != {S1: nd(1, 2), S2: nd(1, 2), S3: nd(1, 2)}:
        out.append(u"PA-4 の分子・分母が手計算(KAM の a 1・1・1 / 2)と違う")
    if flat(pv[5][u"3 便の合計"]) != {S1: nd(0, 3), S2: nd(0, 3), S3: nd(2, 3)}:
        out.append(u"PA-5 の分子・分母が手計算(それ以外 0・0・2 / 3)と違う")
    if dict(pv[6]) != {S1: u"40.00", S2: u"60.00", S3: u"13.33"}:
        out.append(u"PA-5 の率の差が手計算(見積り・計画 − それ以外 = 40.00・60.00・13.33)と違う: %s" % (dict(pv[6]),))
    if pv[7][S2][u"見積り・計画の札の V の行"] != pv[1][u"3 便の合計"][S2] or pv[7][S3][u"札 a の G の行"] != pv[3][u"KAM と YS の合計"][S3] or pv[7][S1][u"札 a の G の行"][u"分子"] != 1:
        out.append(u"PA-6 の欄が PA-1・PA-3 の合計と合わない")
    if flat(pv[8]) != {S1: nd(1, 4), S2: nd(2, 4), S3: nd(3, 4)} or flat(pv[9]) != {S1: nd(0, 4), S2: nd(1, 4), S3: nd(2, 4)}:
        out.append(u"PA-7a・PA-7b の分子・分母が手計算(TSS の G 1・2・3 / 4、V 0・1・2 / 4)と違う")
    if oc(pv[10]) != (8, 2, 2, 1, 3) or oc(pv[11]) != (2, 0, 0, 0, 2):
        out.append(u"PA-8 の重なりが手計算(札つきの V 8・両方 2・便 SC だけ 2・この便だけ 1・どちらも 3)と違う")
    # 引けなかった行は分母に入れない(同じ札で、行を足すと分母が増える)
    more = rows + [R(u"KAM", 1, u"連結", 5, 1, u"V", u"", u"", u"")]
    p2 = ms.predictions(more, labels, ms.sc_index(sc_rec_of(more, SC_STOPS)))
    if list(p2.values())[0][u"「見積り・計画」の札の V の行(引けた行)"] != 5 or list(p2.values())[0][u"V の札の行(引けた)"] != 11:
        out.append(u"引けなかった札が行を足すと引ける・分母に入る数が手計算(V の引けた 10 → 11)と違う")
    # 15 行の境(見積り・計画の札の V の行の引けた行が 14 のとき測れていない・15 のとき測れている)
    for extra, want_flag in ((9, True), (10, False)):
        ls, rs = list(labels), list(rows)
        for i in range(extra):
            ls.append(ms.SC.label_row(u"TSS", 7, None, 100 + i, 1, u"V", u"ウ", None, ms.AT.table_lookup(u"TSS")))
            rs.append(R(u"TSS", 7, None, 100 + i, 1, u"V", u"", u"", u""))
        pe = ms.predictions(rs, ls, ms.sc_index(sc_rec_of(rs, SC_STOPS)))
        d0 = list(pe.values())[0]
        if (d0[u"「見積り・計画」の札の V の行(引けた行)"], d0[u"15 行未満"]) != (5 + extra, want_flag):
            out.append(u"15 行の境の判定が違う(引けた行 %d のとき 15 行未満は %s)" % (5 + extra, want_flag))
    lt = ms.tally_label(labels, rows)
    if lt[u"V の札"][u"合計"][u"見積り・計画"][u"引けた行(分母)"] != 5 or lt[u"G の札(KAM・YS)"][u"合計"][u"型ごと"][u"a"][u"引けた行(分母)"] != 3:
        out.append(u"tally_label の合計が手計算と違う")
    return out


def fdig_c(counts):
    return collections.OrderedDict([(u"cut", True), (u"triples", []), (u"rows", []), (u"counts", dict(counts)), (u"claims", 0)])


def fdig(triples, cut=True, counts=None, rows=None):
    return collections.OrderedDict([(u"cut", cut), (u"triples", list(triples)), (u"rows", list(rows or [])), (u"counts", counts or {}), (u"claims", len(triples))])


# ---------------------------------------------------------------- 6. 配線の確認(封 §2-2)
def wire_problems(ms=None):
    u"""配線の確認 3 つ: 便 SC の記録の行との(鍵, state)の照合・位置・「当たるはずの行」の率 95%。"""
    ms = ms or MS
    out = []
    K, Y, T = u"KAM", u"YS", u"TSS"
    rows = [R(T, 1, None, 1, 1, u"G", u"", u"", u""), R(T, 1, None, 2, 5, u"V", u"", u"", u""), R(K, 2, u"連結", 1, 3, u"V", u"", u"", u""), R(Y, 3, u"配当政策", 4, 4, u"G", u"", u"", u"")]
    books = [fbook(T, 1, [(None, fdig([]))]), fbook(K, 2, [(u"連結", fdig([])), (u"単体", fdig([]))]), fbook(Y, 3, [(u"研究開発活動", fdig([])), (u"設備投資等の概要", fdig([])), (u"配当政策", fdig([]))])]
    sc_rows = [r[:6] + [True, u"", u"", u""] for r in rows]
    w = ms.wire_sc(rows, {u"行": sc_rows}, books)
    if (w[u"TSS"][u"引き直した結んだ行"], w[u"TSS"][u"鍵と state が同じ行"], w[u"KAM"][u"便 SC の記録の結んだ行(同じ本)"], w[u"YS"][u"鍵と state が同じ行"], w[u"TSS"][u"今にだけ在る行"]) != (2, 2, 1, 1, 0):
        out.append(u"wire_sc の数が手計算と違う")
    # 便 SC の記録に別の本の行が在っても、引き直した本に無ければ数えない
    other = sc_rows + [[T, 99, None, 1, 1, u"G", True, u"", u"", u""]]
    if stops(ms, ms.wire_sc, rows, {u"行": other}, books) is not False:
        out.append(u"引き直していない本の便 SC の行で止まる")
    for name, bad_now, bad_sc in (
            (u"行が 1 つ足りない", rows[:-1], sc_rows), (u"行が 1 つ多い", rows + [R(T, 1, None, 9, 9, u"G", u"", u"", u"")], sc_rows),
            (u"state が違う", [rows[0][:5] + [u"V"] + rows[0][6:]] + rows[1:], sc_rows), (u"位置が違う", [rows[0][:4] + [2] + rows[0][5:]] + rows[1:], sc_rows),
            (u"文の種類が違う", rows[:2] + [rows[2][:2] + [u"単体"] + rows[2][3:]] + rows[3:], sc_rows), (u"本の # が違う", [rows[0][:1] + [5] + rows[0][2:]] + rows[1:], sc_rows),
            (u"便 SC の記録に 1 行多い", rows, sc_rows + [[T, 1, None, 7, 7, u"G", True, u"", u"", u""]]), (u"便が違う", [[Y] + rows[0][1:]] + rows[1:], sc_rows)):
        if stops(ms, ms.wire_sc, bad_now, {u"行": bad_sc}, books) is not True:
            out.append(u"結んだ行の(鍵, state)が便 SC の記録と違う(%s)のに止まらない" % name)
    if stops(ms, ms.wire_sc, rows + [rows[0]], {u"行": sc_rows + [sc_rows[0]]}, books) is not True:
        out.append(u"結んだ行の鍵が重なるのに止まらない")
    # 位置の数
    cnt = [fbook(T, 1, [(None, fdig([], counts={u"位置: 数字から": 5, u"位置: 符号か空白から": 2}))]), fbook(T, 2, [(None, fdig([], counts={u"位置: 数字から": 1}))]),
           fbook(K, 1, [(u"連結", fdig([], counts={u"位置: 数字から": 3})), (u"単体", fdig([], cut=False))])]
    wc = ms.wiring_counts(cnt)
    if (wc[T][u"位置を確かめた数の claim(state を問わない)"], wc[T][u"うち pos の字が数字"], wc[T][u"うち pos の字が符号か空白"], wc[K][u"うち pos の字が数字"], wc[Y][u"うち pos の字が数字"]) != (8, 6, 2, 3, 0):
        out.append(u"wiring_counts が手計算(TSS 8・6・2、KAM 3、YS 0)と違う: %s" % (dict(wc[T]),))
    # 当たるはずの行の率(3 便の合計。95% 未満なら止まる)
    def hit_books(total, hit, batches=(T,)):
        bs = []
        for i, b in enumerate(batches):
            t_, h_ = (total, hit) if i == 0 else (0, 0)
            c = {u"P の行": t_ + 3, ms.P_KEYS[1]: 3, ms.P_KEYS[2]: t_, ms.P_KEYS[3]: h_, ms.P_KEYS[4]: t_ - h_}
            bs.append(fbook(b, 1, [(None if b == T else (u"連結" if b == K else u"研究開発活動"), fdig_c(c))]))
        return bs
    if stops(ms, ms.check_p_hit, hit_books(100, 95)) is not False:
        out.append(u"当たる率がちょうど 95% で止まる(95% 未満が止まる)")
    if stops(ms, ms.check_p_hit, hit_books(100, 94)) is not True:
        out.append(u"当たる率が 94% なのに止まらない")
    if stops(ms, ms.check_p_hit, hit_books(20, 19)) is not False or stops(ms, ms.check_p_hit, hit_books(20, 18)) is not True:
        out.append(u"当たる率 19/20 で止まる・18/20 で止まらない")
    if stops(ms, ms.check_p_hit, hit_books(0, 0)) is not False:
        out.append(u"当たるはずの行が 0 のとき止まる")
    # 3 便の合計に掛ける(便ごとでない)
    mix = [fbook(T, 1, [(None, fdig_c({u"P の行": 100, ms.P_KEYS[2]: 100, ms.P_KEYS[3]: 100}))]),
           fbook(K, 1, [(u"連結", fdig_c({u"P の行": 10, ms.P_KEYS[2]: 10, ms.P_KEYS[3]: 4, ms.P_KEYS[4]: 6}))]),
           fbook(Y, 1, [(u"研究開発活動", fdig_c({}))])]
    mix2 = [fbook(T, 1, [(None, fdig_c({u"P の行": 100, ms.P_KEYS[2]: 100, ms.P_KEYS[3]: 100}))]),
            fbook(K, 1, [(u"連結", fdig_c({u"P の行": 10, ms.P_KEYS[2]: 10, ms.P_KEYS[3]: 5, ms.P_KEYS[4]: 5}))]),
            fbook(Y, 1, [(u"研究開発活動", fdig_c({u"P の行": 5, ms.P_KEYS[2]: 5, ms.P_KEYS[3]: 5}))])]
    r2 = ms.check_p_hit(mix2)
    if (r2[u"当たるはずの行(3 便の合計)"], r2[u"当たった"], r2[u"当たらなかった"]) != (115, 110, 5):
        out.append(u"check_p_hit が 3 便の合計(115・110・5)でない: %s" % (dict(r2),))
    if stops(ms, ms.check_p_hit, mix) is not True:
        out.append(u"便ごとには 95% を超えるが合計は 94.5% のとき止まらない(3 便の合計に掛ける)")
    return out


# ---------------------------------------------------------------- 7. 1 本の job(本物のまま。重い道具だけ作り物)
def make_book_args(tmp, batch, n, data=b"fake-material"):
    p = os.path.join(tmp, u"%s_%d.zip" % (batch, n))
    with open(p, "wb") as fh:
        fh.write(data)
    return (batch, n, u"甲", MS.ST.sha256_bytes(data), p)


def job_problems(ms=None):
    u"""``book_job`` を、材料の ZIP の字と重い道具(切り出し・engine)を作り物にして本物のまま走らせる。便・側・節を取り違えない。"""
    ms = ms or MS
    out = []
    tmp = tempfile.mkdtemp(prefix="pa_job_")
    try:
        sentences = {u"zT": [u"売上高は100円でした。", u"来期の売上は10円。"], u"zK1": [u"監査上の項目", u"見積りの売上は20円。"], u"zK2": [u"売上は30円の予定。"],
                     u"zY1": [u"研究の項目", u"計画の費用は40円。"], u"zY2": [u"設備の予定", u"売上は50円。"], u"zY3": [u"配当の項目", u"売上は60円。"]}
        specs = {u"zW": (u"zT", [(0, u"100", G), (1, u"10", VM)]), u"zK1": (u"zK1", [(1, u"20", G)]), u"zK2": (u"zK2", [(0, u"30", VM)]),
                 u"zY1": (u"zY1", [(1, u"40", G)]), u"zY2": (u"zY2", [(1, u"50", VM)]), u"zY3": (u"zY3", [(1, u"60", G), (1, u"60", UN, REASON_P, u"future_period")])}
        pairs = dict((z, hh(ms, sentences[s], sp)[1]) for z, (s, sp) in specs.items())
        sent_of = {b"zW": sentences[u"zT"], b"zK1": sentences[u"zK1"], b"zK2": sentences[u"zK2"], b"zY1": sentences[u"zY1"], b"zY2": sentences[u"zY2"], b"zY3": sentences[u"zY3"]}
        seen = []

        def fake_claims(z):
            seen.append(z)
            return pairs[z.decode()]
        texts = {u"連結": u"TK1", u"単体": u"TK2"}
        sections = {u"研究開発活動": u"TY1", u"設備投資等の概要": u"TY2", u"配当政策": u"TY3"}
        zm = {u"TK1": b"zK1", u"TK2": b"zK2", u"TY1": b"zY1", u"TY2": b"zY2", u"TY3": b"zY3"}
        fake_zip = lambda zb, text: (zm[text], u"e", u"m")
        with patched(ms.TSS, cut=lambda z: (u"TXT", 0, None), wrap=lambda z, t: (b"zW", 1)), patched(ms.PS, claims_of=fake_claims), patched(ms.SC, sentences_of=lambda z: sent_of[z]), \
                patched(ms.KAM, cut_kam=lambda z, side: (texts[side], None)), patched(ms.YS, cut_section=lambda z, sec: (sections[sec], None)), patched(ms.KAM.PR, build_modified_zip=fake_zip):
            b = ms.book_job(make_book_args(tmp, u"TSS", 7))
            if b[u"便"] != u"TSS" or b[u"#"] != 7 or [s for s, _u in b[u"units"]] != [None]:
                out.append(u"TSS の book_job の便・#・単位が違う")
            u = b[u"units"][0][1]
            if [(r[0], r[2]) for r in u[u"rows"]] != [(0, u"G"), (1, u"V")] or u[u"rows"][1][3:] != [u"", u"F", u"F"] or u[u"rows"][0][3:] != [u"", u"", u""]:
                out.append(u"TSS の book_job の行が手計算(0 は G・止めない / 1 は V・来期 F)と違う: %s" % (u[u"rows"],))
            b = ms.book_job(make_book_args(tmp, u"KAM", 3))
            if [s for s, _u in b[u"units"]] != [u"連結", u"単体"]:
                out.append(u"KAM の book_job が文の種類を 連結・単体 の順で返さない")
            k1, k2 = b[u"units"][0][1], b[u"units"][1][1]
            if [r[2] for r in k1[u"rows"]] != [u"G"] or [r[2] for r in k2[u"rows"]] != [u"V"] or k1[u"rows"][0][3:] != [u"", u"", u"E"] or k2[u"rows"][0][3:] != [u"", u"", u"W"]:
                out.append(u"KAM の book_job が連結と単体を取り違える(連結は G・E / 単体は V・W): %s" % ([k1[u"rows"], k2[u"rows"]],))
            b = ms.book_job(make_book_args(tmp, u"YS", 4))
            if [s for s, _u in b[u"units"]] != [u"研究開発活動", u"設備投資等の概要", u"配当政策"]:
                out.append(u"YS の book_job が節を決めた順で返さない")
            y = [x[1][u"rows"] for x in b[u"units"]]
            if [len(r) for r in y] != [1, 1, 1] or y[0][0][3:] != [u"P", u"P", u"P"] or y[1][0][2] != u"V" or y[1][0][3:] != [u"", u"H", u"H"] or y[2][0][3:] != [u"", u"", u""]:
                out.append(u"YS の book_job が節を取り違える(研究は G・P / 設備は V・見出し H / 配当は止めない): %s" % (y,))
            if b[u"units"][2][1][u"counts"].get(u"P の行のうち決算期の字の規則(future_period)で止まった行") != 1:
                out.append(u"YS の配当の P の行(future_period)が数えられない")
            with patched(ms.KAM, cut_kam=lambda z, side: (None, u"x")):
                nb = ms.book_job(make_book_args(tmp, u"KAM", 3))
                if any(un[u"cut"] or un[u"rows"] for _s, un in nb[u"units"]) or len(nb[u"units"]) != 2:
                    out.append(u"切れない KAM の側が空の単位でない")
            a = make_book_args(tmp, u"TSS", 8)
            if stops(ms, ms.book_job, (a[0], a[1], a[2], u"0" * 64, a[4])) is not True:
                out.append(u"材料の ZIP の sha256 が表と違うのに止まらない")
            if stops(ms, ms.book_job, (a[0], a[1], a[2], a[3], a[4] + u"x")) is not True:
                out.append(u"材料の ZIP が無いのに止まらない")
        if seen != [b"zW", b"zK1", b"zK2", b"zY1", b"zY2", b"zY3"]:
            out.append(u"PS.claims_of に渡る ZIP が(TSS は包んだ ZIP・KAM と YS は書き換えた ZIP)の順でない: %s" % (seen,))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


# ---------------------------------------------------------------- 8. つなぐ配線(orchestrate を作り物の本で本物のまま走らせる)
class FakeWorld(object):
    u"""作り物の 3 便。TSS 3 本・KAM 2 本・YS 2 本。便・state・段・文の種類・節で非対称。手計算は ``orchestrate_problems``。"""

    def __init__(self, ms):
        self.ms = ms
        A = [u"経営成績の見通し", u"売上高は100円となりました。", u"その他", u"売上高は200円でした。", u"来期の売上高は300円で、前期の400円です。", u"売上高は500円の見込みです。"]
        B = [u"売上高は100円でした。", u"見積りの利益は30円でした。", u"予定の計画は5円"]
        K1 = [u"監査上の主要な検討事項", u"売上高は1,000円の見込み。", u"仮定の資産は50円。"]
        K2 = [u"売上高は2,000円。"]
        Y1 = [u"研究開発活動", u"次期の研究開発費は10円で、計画は3円。"]
        Y2 = [u"設備投資の予定", u"設備投資は20円。"]
        hh_ = lambda s, specs: hh(ms, s, specs)[0]
        self.tss1 = hh_(A, [(1, u"100", G), (3, u"200", VM), (4, u"300", G), (4, u"400", VM), (5, u"500", UN, REASON_P, None)])
        self.tss3 = hh_(B, [(0, u"100", VM), (1, u"30", G), (2, u"5", UN, REASON_P, u"future_period")])
        self.kam1 = hh_(K1, [(1, u"1,000", VM), (2, u"50", G)])
        self.kam2 = hh_(K2, [(0, u"2,000", VM)])
        self.ys1 = hh_(Y1, [(1, u"10", G), (1, u"3", UN, REASON_P, None)])
        self.ys2 = hh_(Y2, [(1, u"20", VM)])
        pos = lambda s, si, t: s[si].index(t)
        self.pos = {u"t100": pos(A, 1, u"100"), u"t200": pos(A, 3, u"200"), u"t300": pos(A, 4, u"300"), u"t400": pos(A, 4, u"400"), u"b100": pos(B, 0, u"100"), u"b30": pos(B, 1, u"30"),
                    u"k1000": pos(K1, 1, u"1,000"), u"k50": pos(K1, 2, u"50"), u"k2000": pos(K2, 0, u"2,000"), u"y10": pos(Y1, 1, u"10"), u"y20": pos(Y2, 1, u"20")}
        E = ms.empty_digest
        self.books = {
            (u"TSS", 1): fbook(u"TSS", 1, [(None, self.tss1)]), (u"TSS", 2): fbook(u"TSS", 2, [(None, E())]), (u"TSS", 3): fbook(u"TSS", 3, [(None, self.tss3)]),
            (u"KAM", 1): fbook(u"KAM", 1, [(u"連結", self.kam1), (u"単体", E())]), (u"KAM", 2): fbook(u"KAM", 2, [(u"連結", E()), (u"単体", self.kam2)]),
            (u"YS", 1): fbook(u"YS", 1, [(u"研究開発活動", self.ys1), (u"設備投資等の概要", self.ys2), (u"配当政策", E())]),
            (u"YS", 2): fbook(u"YS", 2, [(u"研究開発活動", E()), (u"設備投資等の概要", E()), (u"配当政策", E())])}
        p = self.pos
        #: 手計算の結んだ行(便, 本の #, 文の種類か節, 文の番号, 位置, state, 段 1, 段 2, 段 3)
        self.want = [
            (u"TSS", 1, None, 1, p[u"t100"], u"G", u"", u"H", u"H"), (u"TSS", 1, None, 3, p[u"t200"], u"V", u"", u"", u""), (u"TSS", 1, None, 4, p[u"t300"], u"G", u"", u"F", u"F"),
            (u"TSS", 1, None, 4, p[u"t400"], u"V", u"", u"F", u"F"), (u"TSS", 3, None, 0, p[u"b100"], u"V", u"", u"", u""), (u"TSS", 3, None, 1, p[u"b30"], u"G", u"", u"", u"E"),
            (u"KAM", 1, u"連結", 1, p[u"k1000"], u"V", u"", u"", u"W"), (u"KAM", 1, u"連結", 2, p[u"k50"], u"G", u"", u"", u"E"), (u"KAM", 2, u"単体", 0, p[u"k2000"], u"V", u"", u"", u""),
            (u"YS", 1, u"研究開発活動", 1, p[u"y10"], u"G", u"", u"F", u"F"), (u"YS", 1, u"設備投資等の概要", 1, p[u"y20"], u"V", u"", u"H", u"H")]
        self.sc_stops = ((u"TSS", 1, None, 4, p[u"t400"]), (u"KAM", 1, u"連結", 1, p[u"k1000"]), (u"TSS", 3, None, 1, p[u"b30"]))
        sc_rows = [list(w[:6]) + [True, u"", u"S" if tuple(w[:5]) in self.sc_stops else u"", u""] for w in self.want]
        kam_rows = [[u"V 連結", 1, 1, p[u"k1000"], u"イ", None], [u"V 単体", 2, 0, p[u"k2000"], u"ア", None], [u"V 単体", 2, 5, 1, u"ア", None], [u"G 連結", 1, 2, p[u"k50"], u"a", None],
                    [u"G 連結", 1, 1, p[u"k1000"], u"a", None]]
        ys_rows = [[u"V 設備", 1, 1, p[u"y20"], u"ア", None], [u"G 研究", 1, 1, p[u"y10"], u"b", u"範囲"]]
        self.recs = {
            u"rt": fake_rt_rec(rows=7, states={G: 4, VM: 3, UN: 1, PN: 0}), u"sc": {u"行": sc_rows},
            u"kam_read": fake_read_rec(u"KAM", kam_rows), u"ys_read": fake_read_rec(u"YS", ys_rows),
            u"tss_vm": {u"行の欄": list(ms.AT.VM_FIELDS), u"標本の規則": {u"標本の数": 3}, u"行": [[1, 1, 3, p[u"t200"], u"ア"], [2, 1, 4, p[u"t400"], u"ウ"], [3, 3, 0, p[u"b100"], u"ク"]]},
            u"tss_sub": {u"行の欄": list(ms.AT.SUB_FIELDS), u"細目の字": [u"カ1", u"カ2", u"カ3"], u"行": []}}
        self.pops = {u"TSS": [(1, u"甲", u"k", u"t1"), (2, u"甲", u"k", u"t2"), (3, u"甲", u"k", u"t3")], u"KAM": [(1, u"甲", u"kam1"), (2, u"甲", u"kam2")], u"YS": [(1, u"甲", u"ys1"), (2, u"甲", u"ys2")]}


def run_orchestrate(ms, world=None, hook=None, hook_cache=None, mutate=None, rt_rec=None, sc_rows=None, procs=1):
    u"""``mutate`` は books(作り物の job の返り値の表)を書き換える関数。材料の置き場は使い捨て。"""
    world = world or FakeWorld(ms)
    books = copy.deepcopy(world.books)
    if mutate:
        mutate(books)
    recs = copy.deepcopy(world.recs)
    if rt_rec is not None:
        recs[u"rt"] = rt_rec
    if sc_rows is not None:
        recs[u"sc"] = {u"行": sc_rows}
    tmp = tempfile.mkdtemp(prefix="pa_orch_")
    tmp2 = tempfile.mkdtemp(prefix="pa_orch_cache_")
    calls = []
    try:
        for (_n, _g, _k, sha) in world.pops[u"TSS"]:
            open(os.path.join(tmp, sha + u".zip"), "w").close()
        for r in world.pops[u"KAM"] + world.pops[u"YS"]:
            open(os.path.join(tmp2, r[2] + u".zip"), "w").close()

        def fake_job(args):
            calls.append(args)
            if hook is not None and len(calls) == 1:
                hook(tmp)
            if hook_cache is not None and len(calls) == 1:
                hook_cache(tmp2)
            return copy.deepcopy(books[(args[0], args[1])])
        fake_scan = lambda base, pop: dict((r[2], (os.path.join(base, r[2] + u".zip"), 0)) for r in pop)
        snap = lambda base: [[len(os.listdir(base)), u"|".join(sorted(os.listdir(base)))]]
        with patched(ms, book_job=fake_job, scan_material=fake_scan, folder_snapshots=snap):
            rec = ms.orchestrate(root=ROOT, procs=procs, material=tmp, cache_base=tmp2, say=lambda *a: None, populations=world.pops, recs=recs)
        return rec, calls
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(tmp2, ignore_errors=True)


def run_stops(ms, **kw):
    try:
        run_orchestrate(ms, **kw)
    except ms.Stop:
        return True
    except BaseException as exc:                   # noqa: BLE001
        return type(exc).__name__
    return False


def orchestrate_problems(ms=None):
    u"""作り物の 3 便(TSS 3・KAM 2・YS 2 本)で ``orchestrate`` を本物のまま走らせ、手計算と合わせる。便・state・段・文の種類・節で非対称。"""
    ms = ms or MS
    out = []
    world = FakeWorld(ms)
    rec, calls = run_orchestrate(ms, world=world)
    if [(c[0], c[1]) for c in calls] != [(u"TSS", 1), (u"TSS", 2), (u"TSS", 3), (u"KAM", 1), (u"KAM", 2), (u"YS", 1), (u"YS", 2)]:
        out.append(u"orchestrate が(TSS・KAM・YS の順・母集団の順)に本ごとの job を呼んでいない: %s" % ([(c[0], c[1]) for c in calls],))
    rows = rec[u"行"]
    if [tuple(r) for r in rows] != world.want:
        out.append(u"orchestrate の行が手計算(便 → 本の # → 文の種類か節の順・段の当たり)と違う: %s" % ([tuple(r[:2]) + tuple(r[3:]) for r in rows if tuple(r) not in world.want],))
    ta = rec[K_ALL]
    if (ta[u"TSS"][u"全体"][u"G"][u"結んだ行"], ta[u"TSS"][u"全体"][u"V"][u"結んだ行"], ta[u"KAM"][u"全体"][u"V"][u"結んだ行"], ta[u"KAM"][u"全体"][u"G"][u"結んだ行"],
            ta[u"YS"][u"全体"][u"V"][u"結んだ行"], ta[u"YS"][u"全体"][u"G"][u"結んだ行"]) != (3, 3, 2, 1, 1, 1):
        out.append(u"結んだ行の便ごと・state ごとの数が手計算(TSS G 3・V 3 / KAM V 2・G 1 / YS V 1・G 1)と違う")
    if dict(ta[u"TSS"][u"全体"][u"G"][u"止めた行"]) != {S1: 0, S2: 2, S3: 3} or dict(ta[u"TSS"][u"全体"][u"V"][u"止めた行"]) != {S1: 0, S2: 1, S3: 1}:
        out.append(u"結んだ行 TSS の止めた行が手計算(G 0/2/3、V 0/1/1)と違う")
    if ta[u"KAM"][u"文の種類別"][u"連結"][u"V"][u"結んだ行"] != 1 or ta[u"KAM"][u"文の種類別"][u"単体"][u"V"][u"結んだ行"] != 1 or ta[u"YS"][u"節別"][u"設備投資等の概要"][u"V"][u"結んだ行"] != 1:
        out.append(u"結んだ行の文の種類別・節別が手計算と違う")
    # 配線の確認
    wire = rec[K_WIRE]
    w = wire[K_W_SC]
    if [(w[b][u"引き直した結んだ行"], w[b][u"鍵と state が同じ行"], w[b][u"今にだけ在る行"], w[b][u"便 SC の記録にだけ在る行"]) for b in (u"TSS", u"KAM", u"YS")] != [(6, 6, 0, 0), (3, 3, 0, 0), (2, 2, 0, 0)]:
        out.append(u"便 SC の記録との照合の数が手計算(TSS 6・KAM 3・YS 2)と違う: %s" % (dict(w),))
    wc = wire[K_W_POS]
    if (wc[u"TSS"][u"位置を確かめた数の claim(state を問わない)"], wc[u"KAM"][u"位置を確かめた数の claim(state を問わない)"], wc[u"YS"][u"位置を確かめた数の claim(state を問わない)"]) != (8, 3, 3):
        out.append(u"位置の確かめの数が手計算(TSS 8・KAM 3・YS 3)と違う: %s" % (dict(wc),))
    hw = wire[K_W_P]
    if (hw[u"当たるはずの行(3 便の合計)"], hw[u"当たった"], hw[u"当たらなかった"], hw[u"止まらなかった"]) != (2, 2, 0, True):
        out.append(u"当たるはずの行の数が手計算(2・2・0)と違う: %s" % (dict(hw),))
    if wire[u"本の数"] != collections.OrderedDict([(u"TSS", 3), (u"KAM", 2), (u"YS", 2)]):
        out.append(u"配線の本の数が(3・2・2)でない")
    tp = rec[K_P]
    if (tp[u"TSS"][u"全体"][ms.P_KEYS[0]], tp[u"TSS"][u"全体"][ms.P_KEYS[1]], tp[u"TSS"][u"全体"][ms.P_KEYS[2]], tp[u"YS"][u"節別"][u"研究開発活動"][ms.P_KEYS[3]], tp[u"KAM"][u"全体"][ms.P_KEYS[0]]) != (2, 1, 1, 1, 0):
        out.append(u"P の行の数が手計算(TSS 2・future 1・以外 1、YS 研究の当たる 1、KAM 0)と違う")
    cut = rec[u"切り出し"]
    if (cut[u"TSS"][u"(文の種類なし)"][u"切れた"], cut[u"TSS"][u"(文の種類なし)"][u"切れない"], cut[u"KAM"][u"連結"][u"切れた"], cut[u"KAM"][u"単体"][u"切れた"], cut[u"YS"][u"配当政策"][u"切れた"]) != (2, 1, 1, 1, 0):
        out.append(u"切り出しの数が手計算と違う")
    # 札(作り物の読みの記録から)
    lb = rec[K_LABEL][u"V の札"]
    cl = lambda c: (c[u"札の行"], c[u"引けた行(分母)"], dict(c[u"止めた行"]))
    if cl(lb[u"KAM"][u"見積り・計画"]) != (1, 1, {S1: 0, S2: 0, S3: 1}) or cl(lb[u"KAM"][u"それ以外(分母から除く札は除く)"]) != (2, 1, {S1: 0, S2: 0, S3: 0}) \
            or dict(lb[u"KAM"][u"それ以外(分母から除く札は除く)"][u"引けなかった理由"]) != {u"行が無い": 1, u"state が違う": 0}:
        out.append(u"V の札 KAM が手計算(見積り・計画 1・1・0/0/1、それ以外 2・1・行が無い 1)と違う")
    if cl(lb[u"YS"][u"見積り・計画"]) != (0, 0, {S1: 0, S2: 0, S3: 0}) or cl(lb[u"YS"][u"それ以外(分母から除く札は除く)"]) != (1, 1, {S1: 0, S2: 1, S3: 1}):
        out.append(u"V の札 YS が手計算(見積り・計画 0、それ以外 1・1・0/1/1)と違う")
    if cl(lb[u"TSS"][u"見積り・計画"]) != (1, 1, {S1: 0, S2: 1, S3: 1}) or cl(lb[u"TSS"][u"それ以外(分母から除く札は除く)"]) != (1, 1, {S1: 0, S2: 0, S3: 0}) or cl(lb[u"TSS"][u"分母から除く札"]) != (1, 1, {S1: 0, S2: 0, S3: 0}):
        out.append(u"V の札 TSS が手計算(ウ が見積り・計画 1・1・0/1/1、ア が それ以外、ク が除く)と違う")
    gl = rec[K_LABEL][u"G の札(KAM・YS)"]
    ga = gl[u"KAM"][u"型ごと"][u"a"]
    if cl(ga) != (2, 1, {S1: 0, S2: 0, S3: 1}) or dict(ga[u"引けなかった理由"]) != {u"行が無い": 0, u"state が違う": 1} or cl(gl[u"YS"][u"型ごと"][u"b"]) != (1, 1, {S1: 0, S2: 1, S3: 1}):
        out.append(u"G の札が手計算(KAM の a 2・1・0/0/1・state が違う 1、YS の b 1・1・0/1/1)と違う")
    # 重なり: V の札の合計(札つき・除く札は除く): KAM 見積り・計画(SC 止める・この便 止めない)・KAM それ以外(どちらも止めない)・YS それ以外(この便だけ)・TSS 見積り・計画(両方)・TSS それ以外(どちらも)
    ov = rec[K_OVER][u"V の札(引けた行)"][u"合計"][u"札つきの V の行(分母から除く札は除く)"]
    if (ov[u"行"], ov[u"両方で止めた"], ov[u"便 SC だけが止めた"], ov[u"この便だけが止めた"], ov[u"どちらも止めない"]) != (5, 1, 1, 1, 2):
        out.append(u"重なりが手計算(5・両方 1・便 SC だけ 1・この便だけ 1・どちらも 2)と違う: %s" % (dict(ov),))
    pr = rec[K_PRED]
    sc1 = list(pr.values())[1]
    if dict((k_, (v_[u"分子"], v_[u"分母"])) for k_, v_ in sc1[u"3 便の合計"].items()) != {S1: (0, 2), S2: (1, 2), S3: (2, 2)}:
        out.append(u"PA-1 の 3 便の合計が手計算(分母 2・止めた 0/1/2)と違う: %s" % (dict(sc1[u"3 便の合計"]),))
    if dict((k_, (v_[u"分子"], v_[u"分母"])) for k_, v_ in sc1[u"YS と TSS の合計"].items()) != {S1: (0, 1), S2: (1, 1), S3: (1, 1)}:
        out.append(u"PA-1 の YS と TSS の合計が手計算(分母 1・止めた 0/1/1。YS に見積り・計画の札は無く TSS に 1 行)と違う")
    # 予測の数・当たった類が行・札から作り直せる
    labels = ms.SC.build_labels(world.recs)
    sci = ms.sc_index(world.recs[u"sc"])
    if rec[K_PRED] != ms.predictions(rec[u"行"], labels, sci) or rec[K_CLASS] != ms.tally_class(rec[u"行"]) or rec[K_OVER] != ms.tally_over(rec[u"行"], labels, sci):
        out.append(u"予測・当たった類・重なりの数が行・札から作り直したものと違う")
    if rec[u"seal"] != SEAL_REL or rec[u"封の commit"] != SEAL_COMMIT_SHORT or rec[u"profile"] != u"P33E" or rec[u"key_leaks"] != [] or rec[u"行の欄"] != list(ms.ROW_COLUMNS):
        out.append(u"記録の封の path・commit・profile・key_leaks・行の欄が違う")
    if rec[u"手がかりの語の表"] != collections.OrderedDict((c, list(w_)) for c, w_ in WORD_TABLE.items()):
        out.append(u"記録の手がかりの語の表が封の表と違う")
    text = ms.record_text(rec)
    if json.loads(text, object_pairs_hook=collections.OrderedDict) != json.loads(ms.dumps(rec), object_pairs_hook=collections.OrderedDict) or leak_problems(text):
        out.append(u"作り物の記録が記録の字にならない・漏れの検査を通らない: %s" % (leak_problems(text),))
    # ---- 止める条件
    bad = fake_rt_rec(rows=7, states={G: 4, VM: 3, UN: 1, PN: 0}, fp=collections.OrderedDict((k_, u"x-" + k_) for k_ in ms.FP_KEYS))
    if run_stops(ms, world=world, rt_rec=bad) is not True:
        out.append(u"engine の指紋が便 RT の記録の今と違うのに止まらない")
    if run_stops(ms, world=world, hook=lambda d: open(os.path.join(d, u"added.zip"), "w").close()) is not True:
        out.append(u"材料の置き場に file が増えたのに止まらない")
    if run_stops(ms, world=world, hook=lambda d: None, hook_cache=lambda d: None) is not False:
        out.append(u"置き場が変わらないのに止まる")
    if run_stops(ms, world=world, hook_cache=lambda d: open(os.path.join(d, u"added.zip"), "w").close()) is not True:
        out.append(u"KAM・YS の置き場に file が増えたのに止まらない")
    if run_stops(ms, world=world, hook_cache=lambda d: os.rename(os.path.join(d, u"kam1.zip"), os.path.join(d, u"renamed.zip"))) is not True:
        out.append(u"KAM・YS の置き場の名前が変わった(件数は同じ)のに止まらない")
    sc_ok = world.recs[u"sc"][u"行"]
    if run_stops(ms, world=world, sc_rows=sc_ok[:-1]) is not True:
        out.append(u"便 SC の記録の行が 1 行少ない(今の引き直しにだけ在る行)のに止まらない")
    if run_stops(ms, world=world, sc_rows=sc_ok + [[u"TSS", 1, None, 7, 7, u"G", True, u"", u"", u""]]) is not True:
        out.append(u"便 SC の記録の行が 1 行多いのに止まらない")
    flipped = [list(r) for r in sc_ok]
    flipped[0][5] = u"V" if flipped[0][5] == u"G" else u"G"
    if run_stops(ms, world=world, sc_rows=flipped) is not True:
        out.append(u"便 SC の記録の行の state が違うのに止まらない")

    def miss(books):
        c = books[(u"TSS", 1)][u"units"][0][1][u"counts"]
        c[ms.P_KEYS[3]] = 0
        c[ms.P_KEYS[4]] = c[ms.P_KEYS[2]]
    if run_stops(ms, world=world, mutate=miss) is not True:
        out.append(u"当たるはずの行に類 P の語が 1 つも当たらないのに止まらない")

    def bad_pos(books):
        books[(u"TSS", 1)][u"units"][0][1][u"counts"][u"位置: 数字から"] = 0
    if run_stops(ms, world=world, mutate=bad_pos) is not False:
        out.append(u"位置の数の欄を書き換えただけで止まる(位置の確かめは unit_digest の中で止まる)")
    return out


def default_path_problems(ms=None):
    u"""引数を明示で渡さない本番の既定の経路: 入力の確かめ・記録の読み(便 SC の記録を含む)・3 便の母集団・便 SC の記録の行との照合を本物のまま通す。"""
    ms = ms or MS
    out = []
    pops = {u"TSS": ms.ST.read_population(ROOT), u"KAM": ms.KAM.read_population(ROOT), u"YS": ms.YS.read_population(ROOT)}
    if (len(pops[u"TSS"]), len(pops[u"KAM"]), len(pops[u"YS"])) != (400, 201, 201):
        out.append(u"封の表から読んだ母集団が(400・201・201)でない")
    sc = real_recs()[u"sc"]
    by = collections.defaultdict(list)
    for r in sc[u"行"]:
        by[(r[0], r[1])].append(r)
    tmp = tempfile.mkdtemp(prefix="pa_default_")
    calls = []
    try:
        for (_n, _g, _k, sha) in pops[u"TSS"]:
            open(os.path.join(tmp, sha + u".zip"), "w").close()

        def replay(args, drop=None, flip=None, extra=None):
            batch, n = args[0], args[1]
            units = []
            for side in ms.SIDE_ORDER[batch]:
                rs = [r for r in by.get((batch, n), []) if r[2] == side]
                rows_ = [[r[3], r[4], r[5], u"", u"", u""] for r in rs]
                if drop is not None and (batch, n, side) == drop[:3]:
                    rows_ = rows_[:-1]
                if flip is not None and (batch, n, side) == flip[:3]:
                    rows_[0][2] = u"V" if rows_[0][2] == u"G" else u"G"
                units.append((side, fdig([(r[0], r[1], u"GROUNDED" if r[2] == u"G" else u"VALUE_MISMATCH") for r in rows_], rows=rows_, counts={u"位置: 数字から": len(rows_)})))
            return collections.OrderedDict([(u"便", batch), (u"#", n), (u"units", units)])

        def fake_job(args):
            calls.append(args)
            return replay(args)
        fake_scan = lambda base, pop: dict((r[2], (os.path.join(base, r[2] + u".zip"), 0)) for r in pop)
        run_kw = dict(root=ROOT, procs=1, material=tmp, cache_base=tmp, say=lambda *a: None)
        with patched(ms, book_job=fake_job, scan_material=fake_scan, folder_snapshots=lambda base: [[0, u"x"]]):
            rec = ms.orchestrate(**run_kw)
        n = collections.Counter(c[0] for c in calls)
        if dict(n) != {u"TSS": 400, u"KAM": 201, u"YS": 201} or [c[0] for c in calls] != [u"TSS"] * 400 + [u"KAM"] * 201 + [u"YS"] * 201:
            out.append(u"既定の経路の job が(TSS 400・KAM 201・YS 201 の順)でない: %s" % (dict(n),))
        if [c[1] for c in calls[:400]] != list(range(1, 401)) or [c[1] for c in calls[400:601]] != list(range(1, 202)):
            out.append(u"既定の経路の job の本の # が母集団の表の順でない")
        if [(i[u"path"], i[u"sha256"]) for i in rec[u"入力"]] != list(INPUT_SHAS):
            out.append(u"既定の経路の記録の入力が表と違う")
        if rec[u"材料"][u"表と一致した ZIP"] != collections.OrderedDict([(u"TSS", 400), (u"KAM", 201), (u"YS", 201)]):
            out.append(u"既定の経路の記録の ZIP の数が(400・201・201)でない")
        if len(rec[u"行"]) != len(sc[u"行"]) or [r[:6] for r in rec[u"行"]] != [r[:6] for r in sc[u"行"]]:
            out.append(u"既定の経路の記録の行が便 SC の記録の行(鍵と state)と違う")
        if rec[u"engine の指紋(今。便 RT の記録の今と同じ)"] != collections.OrderedDict((k, ms.VD.engine_fingerprint()[k]) for k in ms.FP_KEYS):
            out.append(u"既定の経路の記録の指紋が違う")
        # 便 SC の記録の行と違えば本物の wire_sc で止まる
        victim = [k for k, v in by.items() if k[0] == u"KAM" and len(v) > 0][0]
        side0 = by[victim][0][2]
        for name, fj in ((u"1 行足りない", lambda a: replay(a, drop=victim + (side0,))), (u"state が違う", lambda a: replay(a, flip=victim + (side0,)))):
            with patched(ms, book_job=fj, scan_material=fake_scan, folder_snapshots=lambda base: [[0, u"x"]]):
                if stops(ms, ms.orchestrate, **run_kw) is not True:
                    out.append(u"400 本の経路で行が便 SC の記録と違う(%s)のに止まらない" % name)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def fingerprint_problems(ms=None):
    u"""engine の指紋は 4 欄のどれが違っても止まる。"""
    ms = ms or MS
    out = []
    base = collections.OrderedDict((k, ms.VD.engine_fingerprint()[k]) for k in ms.FP_KEYS)
    if run_stops(ms, rt_rec=fake_rt_rec(rows=7, states={G: 4, VM: 3, UN: 1, PN: 0}, fp=base)) is not False:
        out.append(u"engine の指紋が同じなのに止まる")
    for k in ms.FP_KEYS:
        fp = collections.OrderedDict(base)
        fp[k] = u"x-%s" % (base[k],)
        if run_stops(ms, rt_rec=fake_rt_rec(rows=7, states={G: 4, VM: 3, UN: 1, PN: 0}, fp=fp)) is not True:
            out.append(u"engine の指紋の欄 %s だけが違うのに止まらない" % k)
    return out


def check_text_problems(ms=None):
    u"""``check_text`` が漏れ(repo へ入れない欄・鍵の形・環境の鍵の値)を止める。封の path・入力の path は漏れに数えない。"""
    ms = ms or MS
    out = []
    if stops(ms, ms.check_text, {}, u"ok") is not False:
        out.append(u"漏れの無い字が止まる")
    if stops(ms, ms.check_text, collections.OrderedDict([(u"value", 1)]), u"ok") is not True:
        out.append(u"repo へ入れない欄が在るのに check_text が止まらない")
    if stops(ms, ms.check_text, {}, u"Zz" * 20) is not True:
        out.append(u"32 字以上の英数字の連なりが在るのに check_text が止まらない")
    if stops(ms, ms.check_text, {}, u"a secretvalue b", u"secretvalue") is not True:
        out.append(u"環境の鍵の値が在るのに check_text が止まらない")
    if stops(ms, ms.check_text, {}, u" ".join([SEAL_REL] + list(INPUT_RELS))) is not False:
        out.append(u"封・入力の path が漏れに数えられている")
    if stops(ms, ms.record_text, collections.OrderedDict([(u"value", 1)])) is not True:
        out.append(u"record_text が漏れを止めない")
    return out


# ---------------------------------------------------------------- 9. 記録
FORBIDDEN_KEYS = SCT.FORBIDDEN_KEYS


def leak_problems(text):
    u"""記録に文・値・要素名・主語の語・枠の id・pointer の字・会社名・docID が無い。手がかりの語の表の語は書いてよい(封 §2-6)。便 SC の門の検査をそのまま呼ぶ(語の表は便 SC の表の語を許す)。"""
    out = []
    try:
        rec = json.loads(text)
    except ValueError:
        return [u"記録が JSON でない"]
    for p, v in walk(rec):
        if p and isinstance(p[-1], str) and p[-1] in FORBIDDEN_KEYS:
            out.append(u"記録に持たない欄が在る: %s" % (p[-1],))
    if DOCID_RE.search(text) or re.search(r"0812\d{14}", text):
        out.append(u"docID・TDnet の番号らしい字が在る")
    table_words = set(w for ws in WORD_TABLE.values() for w in ws)
    body = json.dumps(rec, ensure_ascii=False)
    for word, elems in MS.V.PROFILES[u"P33E"].subjects:
        if len(word) >= 2 and word not in table_words and u'"%s"' % word in body:
            out.append(u"記録に主語の語が在る")
        for e in elems:
            if e in body:
                out.append(u"記録に要素名が在る")
    if re.search(r"xbrl:[A-Za-z]", body) or u"@Current" in body or u"@Prior" in body:
        out.append(u"記録に pointer の字が在る")
    return list(sorted(set(out)))


def recount_problems(rec, ms=None):
    u"""記録の行から集計を数え直して、記録と合わせる(札は本物の読みの記録から。便 SC の記録は本物)。"""
    ms = ms or MS
    out = []
    rows = rec[u"行"]
    if rec[u"行の欄"] != list(ms.ROW_COLUMNS) or any(len(r) != 9 for r in rows):
        return [u"記録の行の欄・行の欄の数が違う"]
    keys = [tuple(r[:5]) for r in rows]
    if len(set(keys)) != len(keys):
        out.append(u"記録の行の鍵が重なる")
    order = lambda r: (ms.BATCHES.index(r[0]), r[1], ms.SIDE_ORDER[r[0]].index(r[2]), r[3], r[4])
    if rows != sorted(rows, key=order):
        out.append(u"記録の行が(便 → 本の # → 文の種類か節 → 文の番号 → 位置)の順でない")
    for r in rows:
        if r[0] not in ms.BATCHES or r[2] not in ms.SIDE_ORDER[r[0]] or r[5] not in (u"G", u"V") or not isinstance(r[3], int) or not isinstance(r[4], int):
            out.append(u"記録の行の形が違う: %s" % (r[:5],))
            break
        if not (set(r[6]) <= set(r[7]) <= set(r[8])) or set(r[6]) - set(u"P") or set(r[7]) - set(u"PFH") or set(r[8]) - set(u"PFEHW") or (r[8] == u"" and (r[6] or r[7])):
            out.append(u"当たった類の字が段の包含・各段の許す類に合わない: %s" % (r[:5],))
            break
        if any(r[i] != u"".join(c for c in u"PFEHW" if c in r[i]) for i in (6, 7, 8)):
            out.append(u"当たった類の字が決めた順(PFEHW)でない: %s" % (r[:5],))
            break
        if (u"W" in r[8]) and (u"P" in r[6] or u"F" in r[7]):
            out.append(u"W が前の字の P か F で止まった行に付いている: %s" % (r[:5],))
            break
    recs = real_recs()
    sci = ms.sc_index(recs[u"sc"])
    labels = ms.SC.build_labels(recs)
    if rec[K_ALL] != ms.tally_all(rows):
        out.append(u"結んだ行の全部の数が行から数え直した数と違う")
    if rec[K_CLASS] != ms.tally_class(rows):
        out.append(u"当たった類ごとの数が行から数え直した数と違う")
    if rec[K_LABEL] != ms.tally_label(labels, rows):
        out.append(u"札つきの行の数が行・札から数え直した数と違う")
    if rec[K_OVER] != ms.tally_over(rows, labels, sci):
        out.append(u"便 SC の段 2 との重なりの数が行・札・便 SC の記録から数え直した数と違う")
    if rec[K_PRED] != ms.predictions(rows, labels, sci):
        out.append(u"予測の判定に要る数が行・札・便 SC の記録から数え直した数と違う")
    return out


def record_problems(ms=None, text=None):
    ms = ms or MS
    out = []
    p = os.path.join(ROOT, RECORD_REL)
    if text is None:
        if not os.path.isfile(p):
            return [u"記録が無い"]
        with open(p, encoding="utf-8", newline="") as fh:
            text = fh.read()
    out.extend(leak_problems(text))
    try:
        rec = json.loads(text, object_pairs_hook=collections.OrderedDict)
    except ValueError:
        return out + [u"記録が JSON でない"]
    if rec.get(u"seal") != SEAL_REL or rec.get(u"封の commit") != SEAL_COMMIT_SHORT:
        out.append(u"記録の封の path・commit が違う")
    if rec.get(u"この script の sha256") != sha_of(SCRIPT_REL):
        out.append(u"記録の script の sha256 が実物と違う")
    if [(i[u"path"], i[u"sha256"]) for i in rec.get(u"入力", [])] != list(INPUT_SHAS) or any(sha_of(rel) != sha for rel, sha in INPUT_SHAS):
        out.append(u"記録の入力が表・実物と違う")
    if rec.get(u"profile") != u"P33E" or rec.get(u"key_leaks") != []:
        out.append(u"profile か key_leaks が違う")
    rt = load_json(u"fixtures/xbrl/tss_retake/retake_2026-11-18.json")
    fp_rt = collections.OrderedDict((k, rt[u"engine の指紋(今。便 NRE の記録の直した後と同じ)"][k]) for k in ms.FP_KEYS)
    now = rec.get(u"engine の指紋(今。便 RT の記録の今と同じ)")
    if now != fp_rt or now != collections.OrderedDict((k, ms.VD.engine_fingerprint()[k]) for k in ms.FP_KEYS):
        out.append(u"記録の engine の指紋が便 RT の記録の今・今の engine と合わない")
    for k in (K_WIRE, K_ALL, K_P, K_LABEL, K_CLASS, K_OVER, K_PRED, u"切り出し", u"手がかりの語の表", u"段の定義", u"限界", u"行"):
        if k not in rec:
            return out + [u"記録に欄が無い: %s" % k]
    if rec[u"手がかりの語の表"] != collections.OrderedDict((c, list(w)) for c, w in WORD_TABLE.items()) or rec[u"限界"] != list(ms.LIMITS) or rec[u"段の定義"] != ms.STAGE_DEFS:
        out.append(u"記録の手がかりの語の表・限界・段の定義が script・封の字と違う")
    out.extend(recount_problems(rec, ms))
    # ---- 配線: 便 SC の記録の行と同じ・便ごとの結んだ行の数は便 SC の記録の行の数
    sc = load_json(SC_RECORD_REL)
    w = rec[K_WIRE][K_W_SC]
    for batch in ms.BATCHES:
        n_sc = sum(1 for r in sc[u"行"] if r[0] == batch)
        n_me = sum(1 for r in rec[u"行"] if r[0] == batch)
        c = w[batch]
        if (c[u"引き直した結んだ行"], c[u"便 SC の記録の結んだ行(同じ本)"], c[u"鍵と state が同じ行"], c[u"今にだけ在る行"], c[u"便 SC の記録にだけ在る行"]) != (n_me, n_sc, n_sc, 0, 0) or n_me != n_sc:
            out.append(u"記録の照合の数が便 SC の記録の行の数と違う: %s" % batch)
    if [r[:6] for r in rec[u"行"]] != [r[:6] for r in sc[u"行"]]:
        out.append(u"記録の行の(鍵, state)が便 SC の記録の行と違う")
    if rec[K_WIRE][u"本の数"] != collections.OrderedDict([(u"TSS", 400), (u"KAM", 201), (u"YS", 201)]):
        out.append(u"記録の本の数が(400・201・201)でない")
    pos = rec[K_WIRE][K_W_POS]
    for batch in ms.BATCHES:
        b = pos[batch]
        if b[u"位置を確かめた数の claim(state を問わない)"] != b[u"うち pos の字が数字"] + b[u"うち pos の字が符号か空白"]:
            out.append(u"位置の確かめの数が合わない: %s" % batch)
    if pos[u"TSS"][u"位置を確かめた数の claim(state を問わない)"] != 24531:
        out.append(u"TSS で位置を確かめた数が便 RT の記録の行(後)24531 でない(全部の数の claim で確かめる)")
    # ---- P の行: 3 便の合計 = 便ごとの合計・文の種類ごと・節ごとの合計 = 便ごと・当たるはずの行 = P の行 − future_period・当たった + 当たらなかった = 当たるはずの行・95% 以上
    tp = rec[K_P]
    for f in ms.P_KEYS:
        if sum(tp[b][u"全体"][f] for b in ms.BATCHES) != tp[u"合計"][u"全体"][f]:
            out.append(u"P の行の合計が便ごとの合計と違う: %s" % f[:12])
    for batch in (u"KAM", u"YS"):
        key = u"文の種類別" if batch == u"KAM" else u"節別"
        for f in ms.P_KEYS:
            if sum(tp[batch][key][s][f] for s in ms.SIDE_ORDER[batch]) != tp[batch][u"全体"][f]:
                out.append(u"%s の P の行の文の種類・節ごとの合計が全体と違う: %s" % (batch, f[:12]))
    for batch in list(ms.BATCHES) + [u"合計"]:
        c = tp[batch][u"全体"]
        if c[ms.P_KEYS[2]] != c[ms.P_KEYS[0]] - c[ms.P_KEYS[1]] or c[ms.P_KEYS[3]] + c[ms.P_KEYS[4]] != c[ms.P_KEYS[2]] or sum(c[u"当たらなかった行の p27_gate の内訳"].values()) != c[ms.P_KEYS[4]]:
            out.append(u"P の行の数が内訳と合わない: %s" % batch)
    hw = rec[K_WIRE][K_W_P]
    t = tp[u"合計"][u"全体"]
    if (hw[u"当たるはずの行(3 便の合計)"], hw[u"当たった"], hw[u"当たらなかった"]) != (t[ms.P_KEYS[2]], t[ms.P_KEYS[3]], t[ms.P_KEYS[4]]) or hw[u"当たった"] * 100 < 95 * hw[u"当たるはずの行(3 便の合計)"] or hw[u"止まらなかった"] is not True:
        out.append(u"当たるはずの行の確かめが P の行の数と合わない・95% 未満")
    # ---- 切り出しの数: 便 SC の記録と同じ
    if rec[u"切り出し"] != sc[u"切り出し"]:
        out.append(u"切り出しの数が便 SC の記録の切り出しと違う")
    return out


# ---------------------------------------------------------------- 10. 配線(import・予約名)
def import_problems(src=None):
    u"""script の import は標準ライブラリの一覧だけ。通信・subprocess・exec・eval を持たない(ast)。前の便の script は便 SC の 1 本だけを load_module で読む。"""
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
                out.append(u"通信の module を import している: %s" % nm)
            elif top not in STDLIB_OK:
                out.append(u"許す一覧に無い module: %s" % nm)
    if any(isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "subprocess" for n in ast.walk(tree)):
        out.append(u"subprocess を使っている")
    loads = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "load_module"]
    if sorted(c.args[0].value for c in loads if c.args and isinstance(c.args[0], ast.Constant)) != ["xbrl_scope_cond_2026-11-19.py"]:
        out.append(u"読む前の便の script が便 SC の 1 本だけでない")
    return out


def reserved_problems(rel=GATE_REL, base=ROOT):
    out = []
    with open(os.path.join(base, rel), encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    for n, line in enumerate(lines, 1):
        if any(re.match(r"%s\w*\s*=" % re.escape(p), line) for p in RESERVED_PREFIXES):
            out.append(u"%s:%d が既存の門の数える名前を行頭に置いている" % (rel, n))
    return out


# ---------------------------------------------------------------- 変異(script)
#: (名前, script の中の字 old, new, 赤になるはずの検査の名前の並び)。old は script に 1 回だけ在る字
MUTANTS = (
    (u"M01 封の commit の定数を替える", u'SEAL_COMMIT = "e69b733c"', u'SEAL_COMMIT = "e69b733d"', ("seal",)),
    (u"M02 記録の path の定数を替える", u'RECORD_REL = REC_DIR_REL + "/stops_2026-11-19.json"', u'RECORD_REL = REC_DIR_REL + "/stops_2026-11-20.json"', ("seal",)),
    (u"M03 入力の表の便 SC の記録の sha256 を替える", u'"d938942bffb39176464f3c644932cf53258f84676aacdbbbc421de74d4dc08a7"', u'"e938942bffb39176464f3c644932cf53258f84676aacdbbbc421de74d4dc08a7"', ("input_sha", "seal_table", "wire_inputs")),
    (u"M04 入力の表の便 SC の script の sha256 を替える", u'"c7ec858ea9523ede23ab2da6d16b53ec338d50cb35899ecac66705e16919e065"', u'"d7ec858ea9523ede23ab2da6d16b53ec338d50cb35899ecac66705e16919e065"', ("input_sha", "seal_table", "wire_inputs")),
    (u"M05 入力の sha256 の照合を外す", u"if not os.path.isfile(p) or ST.sha256_file(p) != want:", u"if False:", ("wire_inputs",)),
    (u"M06 入力の表から最後の 1 行を落とす", u'    (23, "fixtures/xbrl/scope_cond/stops_2026-11-19.json", "d938942bffb39176464f3c644932cf53258f84676aacdbbbc421de74d4dc08a7"),\n', u"", ("input_sha", "seal_table", "wire_inputs")),
    (u"M07 手がかりの語を 1 つ抜く(目標)", u'(u"P", (u"目標", u"計画", u"見込", u"見通")),', u'(u"P", (u"計画", u"見込", u"見通")),', ("seal", "rules")),
    (u"M08 手がかりの語を 1 つ抜く(見通)", u'(u"P", (u"目標", u"計画", u"見込", u"見通")),', u'(u"P", (u"目標", u"計画", u"見込")),', ("seal", "rules")),
    (u"M09 手がかりの語を 1 つ抜く(予測)", u'u"予想", u"予定", u"予測", u"想定",', u'u"予想", u"予定", u"想定",', ("seal", "rules")),
    (u"M10 手がかりの語を 1 つ抜く(翌連結会計年度)", u'u"翌事業年度", u"翌連結会計年度", u"方針")),', u'u"翌事業年度", u"方針")),', ("seal", "rules")),
    (u"M11 手がかりの語を 1 つ抜く(方針)", u'u"翌連結会計年度", u"方針")),', u'u"翌連結会計年度")),', ("seal", "rules")),
    (u"M12 手がかりの語を 1 つ抜く(仮定)", u'(u"E", (u"見積", u"仮定", u"試算"))])', u'(u"E", (u"見積", u"試算"))])', ("seal", "rules")),
    (u"M13 手がかりの語を P と F で取り違える(予測を P へ)", u'(u"P", (u"目標", u"計画", u"見込", u"見通")),', u'(u"P", (u"目標", u"計画", u"見込", u"見通", u"予測")),', ("seal", "rules")),
    (u"M14 語の一致が前方一致", u"    return any(w in text for w in WORDS[cls])", u"    return any(text.startswith(w) for w in WORDS[cls])", ("rules", "stage", "digest")),
    (u"M15 has_pf が E も数える", u"    return has_word(text, u\"P\") or has_word(text, u\"F\")", u"    return has_word(text, u\"P\") or has_word(text, u\"F\") or has_word(text, u\"E\")", ("rules", "stage", "digest")),
    (u"M16 段 1 が前の字でなく文の全部の P を見る", u'    h1 = set(u"P") if p_pre else set()', u'    h1 = set(u"P") if has_word(whole, u"P") else set()', ("stage", "digest")),
    (u"M17 段 1 が F も止める", u'    h1 = set(u"P") if p_pre else set()', u'    h1 = set(u"P") if p_pre or f_pre else set()', ("stage", "digest")),
    (u"M18 段 2 から F を抜く", u'    if f_pre:\n        h2.add(u"F")', u'    if False:\n        h2.add(u"F")', ("stage", "digest", "orch")),
    (u"M19 段 2 から見出しを抜く", u"    if heading is not None and has_pf(heading):", u"    if False:", ("stage", "digest", "orch")),
    (u"M20 見出しを P だけで見る", u"    if heading is not None and has_pf(heading):", u"    if heading is not None and has_word(heading, u\"P\"):", ("stage", "digest")),
    (u"M21 見出しを F だけで見る", u"    if heading is not None and has_pf(heading):", u"    if heading is not None and has_word(heading, u\"F\"):", ("stage", "digest", "orch")),
    (u"M22 見出しに E も入れる", u"    if heading is not None and has_pf(heading):", u"    if heading is not None and (has_pf(heading) or has_word(heading, u\"E\")):", ("stage", "digest")),
    (u"M23 段 3 から E を抜く", u'    if e_pre:\n        h3.add(u"E")', u'    if False:\n        h3.add(u"E")', ("stage", "digest", "orch")),
    (u"M24 E を文の全部で見る", u'    if e_pre:\n        h3.add(u"E")', u'    if has_word(whole, u"E"):\n        h3.add(u"E")', ("stage", "digest")),
    (u"M25 段 3 から文の全部(W)を抜く", u"    if has_pf(whole) and not (p_pre or f_pre):", u"    if False:", ("stage", "digest", "orch")),
    (u"M26 文の全部を P だけで見る", u"    if has_pf(whole) and not (p_pre or f_pre):", u"    if has_word(whole, u\"P\") and not (p_pre or f_pre):", ("stage", "digest")),
    (u"M27 W を前の字で当たった行にも付ける", u"    if has_pf(whole) and not (p_pre or f_pre):", u"    if has_pf(whole):", ("stage", "digest")),
    (u"M28 W の条件が前の字の P だけ", u"    if has_pf(whole) and not (p_pre or f_pre):", u"    if has_pf(whole) and not p_pre:", ("stage", "digest")),
    (u"M29 段 3 が段 2 を含まない", u"    h3 = set(h2)\n", u"    h3 = set()\n", ("stage", "digest")),
    (u"M30 段 2 が段 1 を含まない", u"    h2 = set(h1)\n    if f_pre:", u"    h2 = set()\n    if f_pre:", ("stage", "digest")),
    (u"M31 当たった類の字の順を取り違える", u'CLASS_ORDER = u"PFEHW"', u'CLASS_ORDER = u"WHEFP"', ("seal", "stage")),
    (u"M32 段 1 の前の字が文の全部", u"stage_hits(s[:pos], s,", u"stage_hits(s, s,", ("digest", "orch")),
    (u"M33 前の字が位置の 1 字前まで", u"stage_hits(s[:pos], s,", u"stage_hits(s[:pos - 1], s,", ("digest",)),
    (u"M34 前の字が位置の 4 字後まで", u"stage_hits(s[:pos], s,", u"stage_hits(s[:pos + 4], s,", ("digest",)),
    (u"M35 近い見出しでなく最初の見出しを見る", u"        nh = SC.nearest_heading(heads, si)", u"        nh = heads[0] if heads else None", ("digest", "orch")),
    (u"M36 見出しを見ない", u"sentences[nh] if nh is not None else None)", u"None)", ("digest", "orch")),
    (u"M37 見出しが数の claim を持つ文も数える", u"    heads = SC.heading_indices(sentences, num_sentences)", u"    heads = SC.heading_indices(sentences, set())", ("digest",)),
    (u"M38 結んだ行に G だけ入れる", u"        if state not in SHORT:\n            continue", u"        if state != G_STATE:\n            continue", ("digest", "orch")),
    (u"M39 結んだ行に G・V でない state も入れる", u"        if state not in SHORT:\n            continue", u"        if False:\n            continue", ("digest",)),
    (u"M40 G と V を取り違える", u"SHORT = SC.SHORT", u"SHORT = {SC.G_STATE: u\"V\", SC.V_STATE: u\"G\"}", ("digest", "orch", "job")),
    (u"M41 member の欄が入っている行を行から外す", u"        state = c[\"state\"]\n        triples.append((si, pos, state))", u"        state = c[\"state\"]\n        triples.append((si, pos, state))\n        if r.get(u\"member\"):\n            continue", ("digest",)),
    (u"M42 P の行が reason を見ない", u'        if state == UN_STATE and c.get("reason") == REASON_P:', u"        if state == UN_STATE:", ("digest",)),
    (u"M43 P の行が state を見ない", u'        if state == UN_STATE and c.get("reason") == REASON_P:', u'        if c.get("reason") == REASON_P:', ("digest",)),
    (u"M44 future_period を verify の claim から読む", u'            if r.get("p27_gate") == FUTURE_GATE:', u'            if c.get("p27_gate") == FUTURE_GATE:', ("digest", "orch", "job")),
    (u"M45 future_period を除かずに当たるはずの行にする", u'            if r.get("p27_gate") == FUTURE_GATE:', u"            if False:", ("digest", "orch", "job")),
    (u"M46 当たるはずの行の当て方が P か F", u'                if has_word(s, u"P"):', u"                if has_pf(s):", ("digest",)),
    (u"M47 当たるはずの行の当て方が前の字", u'                if has_word(s, u"P"):', u'                if has_word(s[:pos], u"P"):', ("digest",)),
    (u"M48 位置の確かめを外す(数の字で始まるか)", u"        kind = SC.number_start_kind(s, pos, r.get(\"span\"))", u"        kind = 0", ("digest",)),
    (u"M49 位置の確かめの span の照合を外す", u"        kind = SC.number_start_kind(s, pos, r.get(\"span\"))", u"        kind = SC.number_start_kind(s, pos, None)", ("digest",)),
    (u"M50 文の番号が文の列の外でも止めない", u"        if not isinstance(si, int) or not 0 <= si < len(sentences):\n            raise Stop(", u"        if False:\n            raise Stop(", ("digest",)),
    (u"M51 当たるはずの行の下限を 90% にする", u"HIT_FLOOR_NUM, HIT_FLOOR_DEN = 95, 100", u"HIT_FLOOR_NUM, HIT_FLOOR_DEN = 90, 100", ("seal", "wire")),
    (u"M52 当たるはずの行の判定が 95% を含めて止める", u"    if total > 0 and hit * HIT_FLOOR_DEN < HIT_FLOOR_NUM * total:", u"    if total > 0 and hit * HIT_FLOOR_DEN <= HIT_FLOOR_NUM * total:", ("wire",)),
    (u"M53 当たるはずの行の判定を確かめない", u"    if total > 0 and hit * HIT_FLOOR_DEN < HIT_FLOOR_NUM * total:", u"    if False:", ("wire", "orch")),
    (u"M54 当たるはずの行の判定が KAM と YS の行を数えない", u"    for batch in BATCHES:\n        c.update(p_counts(books, batch))\n    total, hit", u"    for batch in BATCHES[:1]:\n        c.update(p_counts(books, batch))\n    total, hit", ("wire",)),
    (u"M55 当たるはずの行の判定の合計を便ごとの判定にする", u"    total, hit = c.get(P_KEYS[2], 0), c.get(P_KEYS[3], 0)", u"    total, hit = c.get(P_KEYS[2], 0), c.get(P_KEYS[3], 0) + c.get(P_KEYS[4], 0)", ("wire",)),
    (u"M56 「見積り・計画」の札の判定を符号にする", u"    return SC.cat_name(lab) == PLAN_CAT", u"    return SC.cat_name(lab) == u\"外(符号)\"", ("label", "tally", "orch")),
    (u"M57 「見積り・計画」の札の名前を替える", u'PLAN_CAT = u"外(見積り・計画)"', u'PLAN_CAT = u"外(分けられない)"', ("seal", "label", "tally")),
    (u"M58 それ以外に分母から除く札を入れる", u"    other = [m for m in ms if not is_plan(m[0]) and not is_drop(m[0])]", u"    other = [m for m in ms if not is_plan(m[0])]", ("tally", "orch")),
    (u"M59 見積り・計画とそれ以外を取り違える", u"    plan = [m for m in ms if is_plan(m[0])]\n    other = [m for m in ms if not is_plan(m[0]) and not is_drop(m[0])]",
     u"    other = [m for m in ms if is_plan(m[0])]\n    plan = [m for m in ms if not is_plan(m[0]) and not is_drop(m[0])]", ("tally", "orch")),
    (u"M60 分母から除く札の判定を外す", u"    return SC.is_drop(lab)", u"    return False", ("label", "tally", "orch")),
    (u"M61 引けなかった行を分母に入れる", u"    got = [m[1] for m in matched if m[1] is not None]\n    why =", u"    got = [m[1] for m in matched]\n    why =", ("tally", "orch")),
    (u"M62 札の引き方が本の # を見ない", u"    return SC.index_rows(rows)", u"    return dict(((r[0], 0, r[2], r[3], r[4]), r) for r in rows)", ("tally", "orch")),
    (u"M63 段の列の取り違え(段 2 と段 3)", u"C_HIT = {1: C_H1, 2: C_H2, 3: C_H3}", u"C_HIT = {1: C_H1, 2: C_H3, 3: C_H2}", ("tally", "orch")),
    (u"M64 V の札と G の札を取り違える", u"    return SC.split_labels(labels, index)", u"    a, b = SC.split_labels(labels, index)\n    return b, a", ("tally", "orch")),
    (u"M65 結んだ行の便ごとの数が state を取り違える", u"        b = od([(u\"全体\", od((s, stage_cells([r for r in br if r[C_STATE] == s])) for s in GV))])", u"        b = od([(u\"全体\", od((s, stage_cells([r for r in br if r[C_STATE] != s])) for s in GV))])", ("tally",)),
    (u"M66 結んだ行の文の種類別が側を取り違える", u"(side, od((s, stage_cells([r for r in br if r[C_SIDE] == side and r[C_STATE] == s])) for s in GV)) for side in SIDE_ORDER[batch])",
     u"(side, od((s, stage_cells([r for r in br if r[C_SIDE] != side and r[C_STATE] == s])) for s in GV)) for side in SIDE_ORDER[batch])", ("tally",)),
    (u"M67 当たった類の数が止めた行でなく段 1 の行", u"    hit = [r for r in rows if stopped(r, t)]", u"    hit = [r for r in rows if stopped(r, 1)]", ("tally",)),
    (u"M68 当たった類が複数でも 1 つにしか数えない", u"[(c, sum(1 for r in hit if c in r[C_HIT[t]])) for c in CLASS_ORDER]", u"[(c, sum(1 for r in hit if r[C_HIT[t]][:1] == c)) for c in CLASS_ORDER]", ("tally",)),
    (u"M69 当たった類の state を取り違える", u"od((s, class_counts([r for r in br if r[C_STATE] == s], t)) for s in GV)) for t in STAGES)", u"od((s, class_counts([r for r in br if r[C_STATE] != s], t)) for s in GV)) for t in STAGES)", ("tally",)),
    (u"M70 P の行の合計を足さない", u"        total.update(c)\n", u"", ("tally",)),
    (u"M71 P の行の数が当たらなかった行を数えない", u'k.startswith((u"P の行", u"当たる", u"当たらなかった"))', u'k.startswith((u"P の行", u"当たる"))', ("tally",)),
    (u"M72 P の行の当たる率の分母が P の行", u"rate(counts.get(P_KEYS[3], 0), counts.get(P_KEYS[2], 0))", u"rate(counts.get(P_KEYS[3], 0), counts.get(P_KEYS[0], 0))", ("digest", "tally")),
    (u"M73 P の行の便ごとが便を取り違える", u"        if b[u\"便\"] != batch:\n            continue\n        for s, u in b[u\"units\"]:\n            if side is False", u"        if b[u\"便\"] == batch:\n            continue\n        for s, u in b[u\"units\"]:\n            if side is False", ("tally",)),
    (u"M74 重なりが便 SC の段 3 の列を読む", u"SC_C_H2 = SC.C_H2", u"SC_C_H2 = SC.C_H3", ("tally", "orch")),
    (u"M75 重なりの便 SC の側の判定を逆にする", u'    return sc_idx[k][SC_C_H2] != u""', u'    return sc_idx[k][SC_C_H2] == u""', ("tally", "orch")),
    (u"M76 重なりがこの便の段 3 を見る", u"        a[(sc_stopped(sc_idx, r), stopped(r, 2))] += 1", u"        a[(sc_stopped(sc_idx, r), stopped(r, 3))] += 1", ("tally", "orch")),
    (u"M77 重なりの「便 SC だけ」と「この便だけ」を取り違える", u"(u\"便 SC だけが止めた\", a[(True, False)]),\n               (u\"この便だけが止めた\", a[(False, True)])", u"(u\"便 SC だけが止めた\", a[(False, True)]),\n               (u\"この便だけが止めた\", a[(True, False)])", ("tally",)),
    (u"M78 重なりが便 SC の記録に無い行を黙って数える", u"    if k not in sc_idx:\n        raise Stop(", u"    if False:\n        raise Stop(", ("tally",)),
    (u"M79 PA-1 が YS だけ", u'    plan_ys_tss = plan_b[u"YS"] + plan_b[u"TSS"]', u'    plan_ys_tss = plan_b[u"YS"]', ("tally", "orch")),
    (u"M80 PA-4 が KAM でなく YS の札 a", u"    out[u\"PA-4 KAM の札 a の G の行の止めた行 / 引けた行(段 1・2・3。主は段 3)\"] = fr(a_b[u\"KAM\"])", u"    out[u\"PA-4 KAM の札 a の G の行の止めた行 / 引けた行(段 1・2・3。主は段 3)\"] = fr(a_b[u\"YS\"])", ("tally",)),
    (u"M81 PA-3 が札 a でなく b を見る", u"a_b = dict((b, [m for m in gms[b] if m[0][u\"型\"] == u\"a\"]) for b in (u\"KAM\", u\"YS\"))", u"a_b = dict((b, [m for m in gms[b] if m[0][u\"型\"] == u\"b\"]) for b in (u\"KAM\", u\"YS\"))", ("tally",)),
    (u"M82 PA-5 の率の差が逆向き", u"    return RT.point_diff(cb[t], db, ca[t], da)", u"    return RT.point_diff(ca[t], da, cb[t], db)", ("tally",)),
    (u"M83 PA-7a が G でなく V の行", u'    tss_g = [r for r in tss if r[C_STATE] == u"G"]', u'    tss_g = [r for r in tss if r[C_STATE] == u"V"]', ("tally",)),
    (u"M84 PA-7b が V でなく G の行", u'    tss_v = [r for r in tss if r[C_STATE] == u"V"]', u'    tss_v = [r for r in tss if r[C_STATE] == u"G"]', ("tally",)),
    (u"M85 PA-8 が分母から除く札も入れる", u"over_cell(ms_rows(v_kept), sc_idx)", u"over_cell(ms_rows(v_all), sc_idx)", ("tally",)),
    (u"M86 PA-8 の札つきの V の行が見積り・計画だけ", u"    v_kept = plan + other", u"    v_kept = plan", ("tally",)),
    (u"M87 15 行の境が 15 行を含めて測れていない", u"(u\"15 行未満\", den_plan < 15)", u"(u\"15 行未満\", den_plan <= 15)", ("tally",)),
    (u"M88 15 行の境が 14 行", u"(u\"15 行未満\", den_plan < 15)", u"(u\"15 行未満\", den_plan < 14)", ("tally",)),
    (u"M89 見積り・計画の分母が引けなかった札も入れる", u"    den_plan = ms_counts(plan)[0]", u"    den_plan = len(plan)", ("tally",)),
    (u"M90 link_rows が文の種類か節を落とす", u"            rows.append([b[u\"便\"], b[u\"#\"], side] + list(r))", u"            rows.append([b[u\"便\"], b[u\"#\"], None] + list(r))", ("orch",)),
    (u"M91 link_rows が便の順を取り違える", u"    for b in sorted(books, key=lambda b: (BATCHES.index(b[u\"便\"]), b[u\"#\"])):", u"    for b in sorted(books, key=lambda b: (-BATCHES.index(b[u\"便\"]), b[u\"#\"])):", ("orch",)),
    (u"M92 job が KAM と YS の切り出しを取り違える", u'UNITS_OF = {u"TSS": tss_units, u"KAM": kam_units, u"YS": ys_units}', u'UNITS_OF = {u"TSS": tss_units, u"KAM": ys_units, u"YS": kam_units}', ("job",)),
    (u"M93 KAM の job が連結と単体の順を取り違える", u"    for side in KAM.SIDES:\n        text = KAM.cut_kam(zb, side)[0]", u"    for side in reversed(list(KAM.SIDES)):\n        text = KAM.cut_kam(zb, side)[0]", ("job",)),
    (u"M94 TSS の job が包んだ ZIP でなく元の ZIP を渡す", u"    return [(None, unit_digest(PS.claims_of(wrapped), SC.sentences_of(wrapped)))]", u"    return [(None, unit_digest(PS.claims_of(zb), SC.sentences_of(zb)))]", ("job",)),
    (u"M95 KAM の job が書き換えた ZIP でなく元の ZIP を渡す", u"        out.append((side, unit_digest(PS.claims_of(zm), SC.sentences_of(zm))))\n    return out\n\n\ndef ys_units", u"        out.append((side, unit_digest(PS.claims_of(zb), SC.sentences_of(zb))))\n    return out\n\n\ndef ys_units", ("job",)),
    (u"M96 job が材料の sha256 を確かめない", u"    zb = SC.read_bytes(path, sha, n)", u"    zb = open(path, \"rb\").read()", ("job",)),
    (u"M97 便 SC の記録の照合を外す", u"    if set(now) != set(want) or len(now) != len(want):", u"    if False:", ("wire", "orch", "default")),
    (u"M98 便 SC の記録の照合が state を見ない", u"    now = [tuple(r[:6]) for r in rows]\n    want = [tuple(r[:6]) for r in sc_rec[u\"行\"] if (r[0], r[1]) in present]", u"    now = [tuple(r[:5]) for r in rows]\n    want = [tuple(r[:5]) for r in sc_rec[u\"行\"] if (r[0], r[1]) in present]", ("wire", "orch", "default")),
    (u"M99 便 SC の記録の照合が引き直していない本も数える", u'    want = [tuple(r[:6]) for r in sc_rec[u"行"] if (r[0], r[1]) in present]', u'    want = [tuple(r[:6]) for r in sc_rec[u"行"]]', ("wire",)),
    (u"M100 便 SC の記録の照合が鍵の重なりを止めない", u"    if len(set(now)) != len(now) or len(set(want)) != len(want):", u"    if False:", ("wire",)),
    (u"M101 便 SC の記録の照合の便ごとの数が便を取り違える", u"        n_ = set(x for x in now if x[0] == batch)", u"        n_ = set(x for x in now if x[0] != batch)", ("wire", "orch")),
    (u"M102 orchestrate が便 SC の記録の照合を呼ばない", u"wire[u\"結んだ行の(鍵, state)と便 SC の記録の行の照合(違えば止まる)\"] = wire_sc(rows, recs[u\"sc\"], books)", u"wire[u\"結んだ行の(鍵, state)と便 SC の記録の行の照合(違えば止まる)\"] = od()", ("orch", "default")),
    (u"M103 orchestrate が当たるはずの行の判定を呼ばない", u"check_p_hit(books)\n    wire[u\"本の数\"]", u"od()\n    wire[u\"本の数\"]", ("orch",)),
    (u"M104 便 SC の記録を読まない", u"    recs[u\"sc\"] = load_json(os.path.join(root, SC_RECORD_REL))", u"    recs[u\"sc\"] = od([(u\"行\", [])])", ("default",)),
    (u"M105 engine の指紋が違っても止めない", u"    return SC.engine_fp(rt_rec)", u"    return od((k, rt_rec[u\"engine の指紋(今。便 NRE の記録の直した後と同じ)\"][k]) for k in FP_KEYS)", ("fp", "orch")),
    (u"M106 材料の置き場の変化を見ない", u"    if before_tss != ST.names_snapshot(mat) or before_cache != folder_snapshots(base):", u"    if False:", ("orch",)),
    (u"M107 KAM・YS の置き場の変化を見ない", u"    if before_tss != ST.names_snapshot(mat) or before_cache != folder_snapshots(base):", u"    if before_tss != ST.names_snapshot(mat):", ("orch",)),
    (u"M108 job の順が YS・KAM", u'    jobs += [(u"KAM", n, g, sha, kam_found[sha][0]) for (n, g, sha) in kam_pop]\n    jobs += [(u"YS", n, g, sha, ys_found[sha][0]) for (n, g, sha) in ys_pop]',
     u'    jobs += [(u"YS", n, g, sha, ys_found[sha][0]) for (n, g, sha) in ys_pop]\n    jobs += [(u"KAM", n, g, sha, kam_found[sha][0]) for (n, g, sha) in kam_pop]', ("orch", "default")),
    (u"M109 重なりを記録しない", u"    rec[K_OVER] = tally_over(rows, labels, sc_idx)", u"    rec[K_OVER] = od()", ("orch",)),
    (u"M110 通信の module を import する(行を足す)", u"import argparse\n", u"import argparse\nimport urllib.request\n", ("import",)),
    (u"M111 許す一覧の外の module を import する(行を足す)", u"import argparse\n", u"import argparse\nimport shutil\n", ("import",)),
    (u"M112 前の便の script を 1 本足して読む(行を足す)", u"SC = load_module(", u"def unused_loader():\n    return load_module(\"xbrl_nil_read_2026-11-17.py\", \"nr_for_pa\")\n\n\nSC = load_module(", ("import",)),
    (u"M113 check_text が漏れの検査を呼ばない", u"    TSS.check_clean(rec, scan, key_value)", u"    pass", ("clean",)),
)


def check_by_name(name, mod, src):
    table = {u"seal": seal_problems, u"seal_table": seal_table_problems, u"input_sha": input_sha_problems, u"wire_inputs": input_wire_problems, u"rules": rule_problems, u"stage": stage_problems,
             u"digest": digest_problems, u"label": label_problems, u"tally": tally_problems, u"wire": wire_problems, u"job": job_problems, u"orch": orchestrate_problems,
             u"default": default_path_problems, u"fp": fingerprint_problems, u"clean": check_text_problems}
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
    def test_a_1_the_script_tables_equal_the_seal(self):
        self.assertEqual([], seal_problems())
        self.assertEqual([], seal_table_problems())

    def test_a_2_the_seal_file_is_the_sealed_commit_and_unchanged(self):
        self.assertEqual([], seal_history_problems())

    def test_a_3_a_changed_seal_character_turns_the_comparison_red(self):
        seal = seal_text()
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"PA-6", u"PA-9")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"「予測」", u"「予側」")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"「見積」", u"「見績」")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"「方針」", u"「方計」")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"当たる率が 95% 未満", u"当たる率が 90% 未満")))
        self.assertNotEqual([], seal_problems(seal=seal.replace(u"長さが 40 字以下", u"長さが 41 字以下")))
        self.assertNotEqual([], seal_table_problems(seal=seal.replace(INPUT_SHAS[-1][1], u"0" * 64)))


class InputTest(unittest.TestCase):
    def test_b_1_the_inputs_have_the_pinned_sha256(self):
        self.assertEqual([], input_sha_problems())

    def test_b_2_the_input_check_stops_on_a_changed_byte(self):
        self.assertEqual([], input_wire_problems())

    def test_b_3_the_prior_seal_result_documents_and_scripts_are_unchanged_since_the_seal(self):
        self.assertEqual([], prior_docs_problems())
        self.assertEqual([], prior_scripts_problems())
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
        self.assertEqual([], prior_docs_problems(r.d))
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
        r.commit(PRIOR_DOCS[0])
        self.assertNotEqual([], prior_docs_problems(r.d))


class OrderTest(unittest.TestCase):
    def test_d_1_the_real_history_has_the_seal_before_the_script_the_gate_and_the_record(self):
        u"""script・門・記録のどれかが未 commit なら赤(足した commit が無い。skip にしない)。全部 commit された後で初めて緑。"""
        self.assertEqual([], order_of())

    def test_d_2_good_order_is_green_and_bad_orders_are_red(self):
        r = PR.Repo()
        r.put("docs/seal.md")
        s = r.commit("docs/seal.md")
        others = ["measure/s.py", "tests/g.py", "fixtures/r.json"]
        for f in others:
            r.put(f)
        r.commit(*others)
        self.assertEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], [], others))
        self.assertNotEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", "0000000", [], others))
        r.put("fixtures/new.json")
        self.assertNotEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], [], others + ["fixtures/new.json"]))
        r2 = PR.Repo()
        r2.put("measure/s.py")
        r2.commit("measure/s.py")
        r2.put("docs/seal.md")
        s2 = r2.commit("docs/seal.md")
        self.assertNotEqual([], PR.order_problems(r2.d, PREFIX, "docs/seal.md", s2[:7], [], ["measure/s.py"]))

    def test_d_3_the_order_check_lists_the_script_the_gate_and_the_record(self):
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, rel)) for rel in ORDER_FILES))


class RuleTest(unittest.TestCase):
    def test_e_1_the_words_and_the_substring_match(self):
        self.assertEqual([], rule_problems())

    def test_e_2_the_three_stages_include_each_other_and_use_the_right_text(self):
        self.assertEqual([], stage_problems())

    def test_e_3_the_digest_headings_nearest_heading_member_p_rows_and_position(self):
        self.assertEqual([], digest_problems())


class LabelTest(unittest.TestCase):
    def test_f_1_the_labels_come_from_the_real_read_records_and_the_plan_label_differs_by_batch(self):
        self.assertEqual([], label_problems())

    def test_f_2_the_tallies_use_only_the_rows_found_in_the_same_state(self):
        self.assertEqual([], tally_problems())


class WireTest(unittest.TestCase):
    def test_g_1_the_three_wiring_checks_stop(self):
        self.assertEqual([], wire_problems())

    def test_g_2_the_book_job_keeps_the_batches_sides_and_sections_apart(self):
        self.assertEqual([], job_problems())

    def test_g_3_orchestrate_on_made_up_books_equals_the_hand_computation_and_stops(self):
        u"""作り物の本(TSS 3・KAM 2・YS 2)で ``orchestrate`` を本物のまま走らせる。便・state・段・文の種類・節で非対称。"""
        self.assertEqual([], orchestrate_problems())

    def test_g_4_the_default_path_without_explicit_arguments(self):
        self.assertEqual([], default_path_problems())

    def test_g_5_the_engine_fingerprint_stops_on_any_of_its_four_fields(self):
        self.assertEqual([], fingerprint_problems())

    def test_g_6_check_text_stops_on_a_leak(self):
        self.assertEqual([], check_text_problems())


class RecordTest(unittest.TestCase):
    def test_h_1_the_record_has_the_sealed_fields_and_equals_the_recount_from_its_rows(self):
        self.assertEqual([], record_problems())

    def test_h_2_a_record_with_one_number_changed_is_red(self):
        text = read(RECORD_REL)

        def changed(fn):
            r = json.loads(text, object_pairs_hook=collections.OrderedDict)
            fn(r)
            return record_problems(text=json.dumps(r, ensure_ascii=False))

        self.assertNotEqual([], changed(lambda r: r[u"入力"][0].__setitem__(u"sha256", u"0" * 64)))
        self.assertNotEqual([], changed(lambda r: r.__setitem__(u"この script の sha256", u"0" * 64)))
        self.assertNotEqual([], changed(lambda r: r[K_WIRE][K_W_SC][u"TSS"].__setitem__(u"鍵と state が同じ行", r[K_WIRE][K_W_SC][u"TSS"][u"鍵と state が同じ行"] - 1)))
        self.assertNotEqual([], changed(lambda r: r[K_WIRE][K_W_P].__setitem__(u"当たった", r[K_WIRE][K_W_P][u"当たった"] - 1)))
        self.assertNotEqual([], changed(lambda r: r[K_P][u"合計"][u"全体"].__setitem__(MS.P_KEYS[0], r[K_P][u"合計"][u"全体"][MS.P_KEYS[0]] + 1)))
        self.assertNotEqual([], changed(lambda r: r[K_ALL][u"TSS"][u"全体"][u"V"].__setitem__(u"結んだ行", r[K_ALL][u"TSS"][u"全体"][u"V"][u"結んだ行"] + 1)))
        self.assertNotEqual([], changed(lambda r: r[K_ALL][u"KAM"][u"全体"][u"G"][u"止めた行"].__setitem__(S2, r[K_ALL][u"KAM"][u"全体"][u"G"][u"止めた行"][S2] + 1)))
        self.assertNotEqual([], changed(lambda r: r[K_CLASS][u"合計"][S3][u"G"].__setitem__(u"W", r[K_CLASS][u"合計"][S3][u"G"][u"W"] + 1)))
        self.assertNotEqual([], changed(lambda r: r[K_LABEL][u"V の札"][u"合計"][u"見積り・計画"][u"止めた行"].__setitem__(S2, r[K_LABEL][u"V の札"][u"合計"][u"見積り・計画"][u"止めた行"][S2] + 1)))
        self.assertNotEqual([], changed(lambda r: r[K_LABEL][u"G の札(KAM・YS)"][u"合計"][u"型ごと"][u"a"].__setitem__(u"引けた行(分母)", 0)))
        self.assertNotEqual([], changed(lambda r: r[K_OVER][u"V の札(引けた行)"][u"合計"][u"見積り・計画"].__setitem__(u"両方で止めた", r[K_OVER][u"V の札(引けた行)"][u"合計"][u"見積り・計画"][u"両方で止めた"] + 1)))
        self.assertNotEqual([], changed(lambda r: list(r[K_PRED].values())[1][u"3 便の合計"][S2].__setitem__(u"分子", 0)))
        self.assertNotEqual([], changed(lambda r: r[u"行"].pop()))
        self.assertNotEqual([], changed(lambda r: r[u"行"][0].__setitem__(7, u"PFEHW")))
        self.assertNotEqual([], changed(lambda r: r[u"engine の指紋(今。便 RT の記録の今と同じ)"].__setitem__(u"core_py_sha256", u"0" * 64)))
        self.assertNotEqual([], changed(lambda r: r.__setitem__(u"限界", r[u"限界"][:-1])))
        self.assertNotEqual([], changed(lambda r: r[u"手がかりの語の表"][u"F"].pop()))
        self.assertNotEqual([], changed(lambda r: r[u"切り出し"][u"TSS"][u"(文の種類なし)"].__setitem__(u"切れた", r[u"切り出し"][u"TSS"][u"(文の種類なし)"][u"切れた"] + 1)))

    def test_h_3_a_record_with_a_sentence_a_value_an_element_name_or_a_subject_word_is_red(self):
        rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        rec[u"要素名"] = u"jppfs_cor:NetSales"
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        rec[u"材料"][u"文"] = u"売上高は増加した"
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        rec[u"材料"][u"TSS の置き場"] = u"S100" + u"ABCD"
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        rec[u"材料"][u"x"] = u"売上高"
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        rec[u"材料"][u"x"] = u"xbrl:jppfs_cor:Assets@CurrentYearInstant"
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        rec[u"pointers"] = []
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        rec[u"member"] = u"x"
        self.assertNotEqual([], leak_problems(json.dumps(rec, ensure_ascii=False)))
        self.assertEqual([], leak_problems(read(RECORD_REL)))
        self.assertFalse(DOCID_RE.search(read(RECORD_REL)))


class WiringTest(unittest.TestCase):
    def test_i_1_the_script_imports_only_the_allowed_modules(self):
        self.assertEqual([], import_problems())

    def test_i_2_the_boundary_import_list_is_not_widened(self):
        p = os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py")
        with open(p, encoding="utf-8") as fh:
            self.assertNotIn(u"plan_attr", fh.read())

    def test_i_3_the_script_has_no_network_key_or_llm(self):
        src = read(SCRIPT_REL)
        for bad in (u"socket", u"urllib", u"ANTHROPIC", u"API_KEY", u"requests"):
            self.assertNotIn(bad, src)

    def test_i_4_the_gate_does_not_use_the_reserved_names_and_has_no_docid(self):
        self.assertEqual([], reserved_problems())
        self.assertIsNone(DOCID_RE.search(read(GATE_REL)))
        self.assertIsNone(DOCID_RE.search(read(SCRIPT_REL)))

    def test_i_5_the_reserved_name_check_sees_a_planted_name(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("ENGINE_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rel="g.py", base=d))
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("PA_NOTES = 1\n")
            self.assertEqual([], reserved_problems(rel="g.py", base=d))

    def test_i_6_the_script_leaves_sys_modules_as_it_found_them(self):
        u"""前の便の script を読んでも、読み込みの前に居た名前を上書きしたまま残さない(門を 2 通りの順で走らせても赤くならない)。"""
        before = dict(sys.modules)
        mod = load_module(SCRIPT_REL, "plan_attr_script_for_sysmodules_check")
        changed = [k for k, v in before.items() if sys.modules.get(k) is not v]
        self.assertEqual([], changed)
        self.assertIn("plan_attr_script_for_sysmodules_check", sys.modules)
        del mod


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
        for name in (u"seal", u"seal_table", u"input_sha", u"wire_inputs", u"rules", u"stage", u"digest", u"label", u"tally", u"wire", u"job", u"orch", u"default", u"fp", u"clean", u"import"):
            self.assertEqual([], check_by_name(name, mod, base), name)


if __name__ == "__main__":
    unittest.main()
