# -*- coding: utf-8 -*-
"""封 docs/CTGOV_WALL_SEAL_2026-11-21.md(CT0 ― 治験の公開データで、いまの engine の数の読み取りが英語の論文の要旨の数をどれだけ拾うか)の封の門。

**この門は 1 回も通信しない**(取る関数には作り物の transport を渡す。``urllib.request.urlopen`` は 0 円の経路を走らせる間だけ「呼ばれたら失敗」に差し替える)。材料は取らない・読まない(作り物の登録の JSON と作り物の要旨だけ)。

**この門が縛るもの**

1. 封の字: 封の commit(9e41971b)・封の file が commit した blob と同じ・分母の正規表現・類の順と語と窓・対の本数 10・止め 400・間隔 1 秒・tool・置き場・記録の path・profile・限界の 4 行が script の定数と同じ。
2. engine は封の commit から 0 行。境界の門の import 一覧にこの便の名前を足していない。
3. 作り物の要旨(数の類が全部出る短い作り物。実在の論文の字ではない)で、分母の類分け → engine の読み取り(本物の関数)→ 位置の照らし → 数える、を通す(手で数えた値と照らす)。「分母の外で拾った」も作り物で出す。
4. 作り物の登録の JSON で、値の読める行の数え方と、0 行のときの理由(欄の名)を通す。
5. 作り物の transport で、取る関数の条件の当て方(結果が在る・介入・Phase 3・RESULT の文献・要旨に登録番号が在る・題だけに在るのは対にしない)・10 対で止める・400 試験で止める・
   呼び出しの間 1 秒以上・``tool`` を付け ``email`` を付けない・200 でない返事で止まる・置き場が repo の中か空でなければ止まる、を本物の関数のまま通す。
6. 記録: 禁止の検査(登録番号の形・PMID の形・要旨の字・禁止の欄の名)が作り物で止まる。置き場 → 記録 → ``--check`` が通る(作り物の置き場)。0 円の経路は通信しない。
7. 行頭の名前: この門は ``ENGINE_LATER``・``UNTOUCHED``・``PIN_DEF``・``LATER_ENGINE_COMMITS``・``FROZEN_LATER``・``ENGINE_TRANSITIONS`` を行頭に置かない。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``。script の字を 1 か所替えた版を memory の中に作る。file は書き換えない)。
黙る変異は ``SILENT_BY_DESIGN`` に理由とともに置き、「黙ること」自体を別の試験で縛る。
"""
import ast
import collections
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
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)


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


def load_source(src):
    u"""script の字(``src``)から module を memory の中に作る。file は読み書きしない。``__file__`` は本物の script。"""
    mod = types.ModuleType("ctgov_wall_mutant")
    mod.__file__ = os.path.join(ROOT, SCRIPT_REL)
    before = dict(sys.modules)
    try:
        exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    finally:
        for k, v in before.items():
            if sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


SEAL_REL = "docs/CTGOV_WALL_SEAL_2026-11-21.md"
SEAL_COMMIT_SHORT = "9e41971b"                # 封の commit(literal に留める。script の定数と違えば赤)
SEAL_ADDENDUM_SHORT = "455c77a6"              # 封の §8 追記の commit(literal)
SCRIPT_REL = "measure/ctgov_wall_2026-11-21.py"
GATE_REL = "tests/measure/test_ctgov_wall_seal.py"
RECORD_REL = "fixtures/ctgov/wall_2026-11-21.json"
MS = load_module(SCRIPT_REL, "ctgov_wall_script_for_seal_gate")
PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_ctgov_seal")       # 順序・履歴の部品。門としては走らせない
ORDER_FILES = (SCRIPT_REL, GATE_REL)          # 記録の順序は記録が在るときの結果の門に置く
od = collections.OrderedDict


def read(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def sha_of(rel):
    import hashlib
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def sha_or_none(rel):
    return sha_of(rel) if os.path.exists(os.path.join(ROOT, rel)) else None


def guard(fn, *a, **kw):
    u"""fn が例外(``SystemExit`` を含む)を投げたら、その例外の型の名前の字を返す。何も投げなければ None の代わりに []。違いを見るための道具。"""
    try:
        return fn(*a, **kw)
    except BaseException as exc:                # noqa: BLE001
        return [u"例外: %s" % type(exc).__name__]


def stops(ms, fn, *a, **kw):
    u"""fn が ``ms.Stop`` を投げれば True。投げなければ False。別の例外は投げ直す。"""
    try:
        fn(*a, **kw)
    except ms.Stop:
        return True
    return False


# ---------------------------------------------------------------- 作り物の要旨
#: 数の類が全部出る短い作り物(実在の論文の字ではない。登録番号の字は作り物)
TEMPLATE = (u"A total of n = 120 patients were enrolled between 2019 and 2021. Response occurred in 45.5% of participants (95% CI 38.2 to 52.9%). "
            u"The effect was HR 0.80 (CI 0.65 to 0.99; p = 0.04) and OR 2.5 in 33 women. Median duration was 12.5 months. A hazard ratio 0.71 was seen. "
            u"Study {NCT} gave 1,234万円 and a dose x12% with lot B7 and 5mg, 77 events (−4.5 points) and a change of −5.0%.")
#: 上の字を手で数えた値(P: 45.5・95・52.9・−5.0 / C: 38.2・0.65・0.99 / N: 120・33 / R: 0.80・2.5・0.71(hazard ratio と数の間に空白 1 つ) / V: 0.04 / Y: 2019・2021 / O: 12.5・1,234・77・−4.5)。
#: engine が拾うのは「45.5%」「95%」「52.9%」「5.0%」(符号の U+2212 は読まない)で、分母に重ならない「12%」が分母の外 1 つ
HAND = od([("P", (4, 4)), ("C", (3, 0)), ("N", (2, 0)), ("R", (3, 0)), ("V", (1, 0)), ("Y", (2, 0)), ("O", (4, 0))])
HAND_OUTSIDE = 1
HAND_DEN, HAND_PICK = 19, 4


def fake_text(nct=u"NCT00000001"):
    return TEMPLATE.replace(u"{NCT}", nct)


def tally_cells(per):
    return od((c, (per[c][u"分母"], per[c][u"拾った"])) for c in per)


# ---------------------------------------------------------------- 1. 封の字
def seal_text():
    return read(SEAL_REL)


def seal_class_lines(seal):
    u"""封 §2-1 の類の行(``- **P**: …`` の形)。{類: 行の字}。"""
    return dict((m.group(1), m.group(2)) for m in re.finditer(r"^\s+- \*\*([PCNRVYO])\*\*: (.*)$", seal, re.M))


def ticks(line):
    return re.findall(r"`([^`]*)`", line)


def seal_problems(ms=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    out = []
    if ms.SEAL_ADDENDUM_COMMIT != SEAL_ADDENDUM_SHORT:
        out.append(u"script の封の追記の commit が門と違う")
    if ms.SEAL_COMMIT != SEAL_COMMIT_SHORT or ms.SEAL_REL != SEAL_REL or ms.SCRIPT_REL != SCRIPT_REL or ms.RECORD_REL != RECORD_REL:
        out.append(u"script の封の commit・path・記録の path が門と違う")
    m = re.search(r"`(\(\?<!\[A-Za-z0-9\.\]\)[^`]*)`", seal)
    if m is None or ms.DENOM_PATTERN != m.group(1):
        out.append(u"分母の正規表現が封の字と違う")
    if ms.DENOM_RE.pattern != ms.DENOM_PATTERN:
        out.append(u"分母の正規表現を compile した字が定数と違う")
    lines = seal_class_lines(seal)
    if sorted(lines) != sorted(ms.CLASSES) or list(ms.CLASSES) != [u"P", u"C", u"N", u"R", u"V", u"Y", u"O"] or [n for n, _f in ms.CLASS_TESTS] + [u"O"] != list(ms.CLASSES):
        out.append(u"類の名・順が封と違う(上から先に当たった類)")
    elif list(lines) != list(ms.CLASSES):
        out.append(u"封の類の行の並びが P・C・N・R・V・Y・O の順でない")
    else:
        if ticks(lines["P"]) != [u"%"]:
            out.append(u"封の類 P の字が読めない")
        if ticks(lines["C"]) != list(ms.C_WORDS) or u"直前 %d 字" % ms.C_WINDOW not in lines["C"]:
            out.append(u"類 C の語・窓が封と違う")
        if ticks(lines["N"]) != list(ms.N_BEFORE) + list(ms.N_AFTER) or u"直前 %d 字" % ms.N_WINDOW not in lines["N"]:
            out.append(u"類 N の語・窓が封と違う")
        m8 = re.search(r"## §8 追記.*?類 R の窓を 12 字から (\d+) 字に替える", seal, re.S)          # §8 が在れば §2 の 12 より勝つ
        r_window = int(m8.group(1)) if m8 else 12
        if ticks(lines["R"]) != list(ms.R_ABBR) + list(ms.R_WORDS) or u"直前 12 字" not in lines["R"] or ms.R_WINDOW != r_window or r_window != 16:
            out.append(u"類 R の語・窓が封(§2 と §8 の追記)と違う")
        if ticks(lines["V"]) != [u"p", u"P", u"<", u"=", u">"] or u"直前 %d 字" % ms.V_WINDOW not in lines["V"] or ms.V_BEFORE_RE.pattern != u"[pP]\\s*[<=>]":
            out.append(u"類 V の字・窓が封と違う")
        if u"1900〜2099" not in lines["Y"] or tuple(ms.Y_RANGE) != (1900, 2099):
            out.append(u"類 Y の範囲が封と違う")
    if (ms.PAIRS_WANT, ms.STUDIES_STOP, ms.MIN_GAP_SECONDS) != (10, 400, 1.0) or u"**10 対**" not in seal or u"400 に達したら止め" not in seal or u"1 回ごとに 1 秒以上あける" not in seal:
        out.append(u"対の本数 10・止め 400・間隔 1 秒が封と違う")
    if ms.TOOL not in (u"audit-core-ct0",) or u"`tool` と `email`" not in seal or u"付けない形で断られたらそこで止めて" not in seal:
        out.append(u"tool か email の扱いが封と違う")
    if ms.CACHE_DIR != os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "ctgov_2026-11-21") or u"`~/.cache/audit-core/ctgov_2026-11-21/`" not in seal:
        out.append(u"置き場が封と違う")
    if ms.PROFILE != u"P27" or u"既定の profile(`P27`)" not in seal or ms.V.DEFAULT_PROFILE != u"P27":
        out.append(u"profile が封か engine の既定と違う")
    for rel in (SCRIPT_REL, RECORD_REL, GATE_REL):
        if rel not in seal:
            out.append(u"封に path が無い: %s" % rel)
    sec7 = seal.split(u"## §7", 1)[-1].split(u"## §8", 1)[0]
    bullets = [ln[2:].strip() for ln in sec7.splitlines() if ln.startswith(u"- ")]
    if bullets != list(ms.LIMITS):
        out.append(u"限界の 4 行が封 §7 と違う")
    if u"## §8 追記" not in seal or u"**類 R の窓を 12 字から 16 字に替える**" not in seal:
        out.append(u"封に §8 の追記が無い")
    for k in (u"CT0-1", u"CT0-7"):
        if k not in seal:
            out.append(u"封に予測が無い: %s" % k)
    if u"engine の指紋" not in seal or u"材料の sha256" not in seal:
        out.append(u"封に記録の項目が無い")
    return out


def seal_history_problems(root=REPO):
    rc = subprocess.run(["git", "-C", root, "log", "--format=%H", "--", PREFIX + SEAL_REL], stdout=subprocess.PIPE, universal_newlines=True)
    hs = [x for x in rc.stdout.split() if x]
    hs = list(reversed(hs))                                   # git log は新しい順
    if len(hs) != 2 or not hs[0].startswith(SEAL_COMMIT_SHORT) or not hs[1].startswith(SEAL_ADDENDUM_SHORT):
        return [u"封の file の履歴が(封 %s・§8 の追記 %s)の 2 commit でない" % (SEAL_COMMIT_SHORT, SEAL_ADDENDUM_SHORT)]
    blobs = [subprocess.run(["git", "-C", root, "show", "%s:%s" % (h, PREFIX + SEAL_REL)], stdout=subprocess.PIPE).stdout.decode("utf-8") for h in hs]
    if blobs[1] != seal_text():
        return [u"今の封が最後の追記の commit の blob と違う"]
    if not blobs[1].startswith(blobs[0].rstrip(u"\n")) or u"## §8 追記" not in blobs[1][len(blobs[0].rstrip(u"\n")):]:
        return [u"封の commit の字が追記の commit の頭と違う(追記の外が書き換えられた)"]
    return []


def order_of(root=REPO, seal_short=SEAL_COMMIT_SHORT, others=None):
    u"""封 ⊏ 追記 ⊏ script・この門(足した commit が封と追記の後)。未 commit は赤。"""
    others = list(ORDER_FILES) if others is None else others
    out = list(PR.order_problems(root, PREFIX, SEAL_REL, seal_short, [], others))
    for rel in others:
        a = PR.added_commits(root, PREFIX + rel)
        if not a:
            continue                                           # 未 commit は上の order_problems が赤にする
        rc = subprocess.run(["git", "-C", root, "merge-base", "--is-ancestor", SEAL_ADDENDUM_SHORT, a[-1]]).returncode
        if rc != 0 or a[-1].startswith(SEAL_ADDENDUM_SHORT):
            out.append(u"%s が封の追記の後でない" % rel)
    return out


def engine_zero_problems(root=REPO):
    rc = subprocess.run(["git", "-C", root, "diff", "--name-only", SEAL_COMMIT_SHORT, "--", PREFIX + "adapters", PREFIX + "core"], stdout=subprocess.PIPE, universal_newlines=True)
    return [u"engine が封の後に変わっている: %s" % ln for ln in rc.stdout.splitlines() if ln.strip()]


# ---------------------------------------------------------------- 2. 分母・engine・照らし
def tally_problems(ms=None):
    u"""作り物の要旨で、分母の類分け・engine の読み取り・位置の照らし・数える、を本物の関数のまま通し、手で数えた値と照らす。"""
    ms = ms or MS
    out = []
    per, outside = ms.tally_text(fake_text())
    if tally_cells(per) != HAND:
        out.append(u"類別の (分母, 拾った) が手で数えた値と違う: %s" % dict(tally_cells(per)))
    if outside != HAND_OUTSIDE:
        out.append(u"分母の外で拾った数が %d(手で数えた値は %d)" % (outside, HAND_OUTSIDE))
    if sum(v[0] for v in tally_cells(per).values()) != HAND_DEN or sum(v[1] for v in tally_cells(per).values()) != HAND_PICK:
        out.append(u"分母の合計か拾った合計が手で数えた値と違う")
    if ms.R is not sys.modules.get("adapters.xbrl.recipes") or ms.engine_picks.__code__.co_names.count("_numbers_of") != 1:
        out.append(u"engine の読み取りが recipes の _numbers_of を呼んでいない")
    text = ms.nfkc(fake_text())
    picks = [text[a:b].strip() for a, b in ms.engine_picks(text)]
    if picks != [u"45.5%", u"95%", u"52.9%", u"12%", u"5.0%"]:
        out.append(u"engine が返した字が想定と違う: %s" % picks)
    return out


def class_cases_problems(ms=None):
    u"""類の優先順位(上から先に当たった類)を 1 つずつ。P と C が重なれば P・N と R が重なれば N。型番・単位の字(前後に英字)は数えない・NCT の字の中の数字は数えない・全角は NFKC。"""
    ms = ms or MS
    out = []

    def classes_of(t):
        t = ms.nfkc(t)
        return [(t[a:b], c) for a, b, c in ms.denominator(t)]
    want = [
        (u"The rate was 12% (95% CI 3 to 9%).", [(u"12", u"P"), (u"95", u"P"), (u"3", u"C"), (u"9", u"P")]),
        (u"hazard ratio 0.8 and Hazard ratio, 0.9", [(u"0.8", u"R"), (u"0.9", u"R")]),
        (u"HR 1.2 in 33 women", [(u"1.2", u"R"), (u"33", u"N")]),
        (u"p < 0.05 and P=0.2", [(u"0.05", u"V"), (u"0.2", u"V")]),
        (u"in 2019, 1899 and 2100 and 2019.5 and 1,999", [(u"2019", u"Y"), (u"1899", u"O"), (u"2100", u"O"), (u"2019.5", u"O"), (u"1,999", u"O")]),
        (u"5mg, B7, HbA1c 7 and ab12cd", [(u"7", u"O")]),
        (u"NCT00000001 and NCT12345678 gave 3", [(u"3", u"O")]),
        (u"１２％ of men", [(u"12", u"P")]),
        (u"odds ratio 2 with n=5 and N = 6 in 7 subjects", [(u"2", u"R"), (u"5", u"N"), (u"6", u"N"), (u"7", u"N")]),
    ]
    for t, expect in want:
        got = classes_of(t)
        if got != expect:
            out.append(u"類分けが想定と違う: %s -> %s" % (t[:30], got))
    return out


# ---------------------------------------------------------------- 3. 登録の側
def fake_results():
    return {"resultsSection": {
        "outcomeMeasuresModule": {"outcomeMeasures": [
            {"classes": [{"categories": [{"measurements": [{"value": "12.5"}, {"value": "NA"}, {"value": "1,234"}, {"value": "-3"}, {"value": ""}, {"value": None}]}]}]},
            {"classes": [{"categories": [{"measurements": [{"value": True}]}]}]}]},
        "adverseEventsModule": {"seriousEvents": [{"stats": [{"numAffected": 3}, {"numAffected": None}, {"numAffected": "4"}]}],
                                "otherEvents": [{"stats": [{"numAffected": "x"}, {"numAffected": False}]}]}}}


def registry_problems(ms=None):
    ms = ms or MS
    out = []
    rows, reasons = ms.registry_rows(fake_results())
    if (rows, reasons) != (5, []):                       # 12.5・1,234・-3(評価項目 3)+ 3・"4"(有害事象 2)
        out.append(u"値の読める行の数が手で数えた 5 でない: %s %s" % (rows, reasons))
    rows0, reasons0 = ms.registry_rows({"protocolSection": {}})
    if rows0 != 0 or reasons0 != [u"resultsSection が無い"]:
        out.append(u"結果の欄が無いときの行数・理由が違う: %s %s" % (rows0, reasons0))
    rows1, reasons1 = ms.registry_rows({"resultsSection": {"outcomeMeasuresModule": {"outcomeMeasures": [{"classes": [{"categories": [{"measurements": [{"value": "NA"}]}]}]}]}}})
    if rows1 != 0 or len(reasons1) != 2 or not reasons1[0].startswith(u"outcomeMeasuresModule.outcomeMeasures") or not reasons1[1].startswith(u"adverseEventsModule"):
        out.append(u"読める行が 0 のときの理由(欄の名)が違う: %s" % reasons1)
    for v, want in ((u"12", True), (u" -1,234.5 ", True), (u"1,23", False), (u"1e3", False), (u"NA", False), (u"", False), (None, False), (True, False), (7, True), (3.5, False)):
        if ms.readable(v) is not want:
            out.append(u"readable(%r) が %s でない" % (v, want))
    return out


# ---------------------------------------------------------------- 4. 取る関数(作り物の transport)
class FakeClock(object):
    def __init__(self):
        self.t = 1000.0

    def now(self):
        return self.t

    def sleep(self, s):
        self.t += s


def make_study(i, results=True, stype="INTERVENTIONAL", phases=("PHASE3",), refs=((u"RESULT", u"90000%02d"),), nct=None):
    nct = nct or u"NCT%08d" % (i + 1)
    reflist = []
    for typ, pm in refs:
        r = {"type": typ, "citation": "x"}
        if pm:
            r["pmid"] = pm % i if u"%" in pm else pm
        reflist.append(r)
    st = {"protocolSection": {"identificationModule": {"nctId": nct}, "designModule": {"studyType": stype, "phases": list(phases)},
                              "referencesModule": {"references": reflist}}, "hasResults": results}
    if results:
        st.update(fake_results())
    return st


def abstract_xml(pmid, body, title=u"Fake title"):
    esc = lambda s: s.replace(u"&", u"&amp;").replace(u"<", u"&lt;")

    def cut(at):
        i = body.find(u" ", at)
        return len(body) if i < 0 else i
    i, j = cut(40), cut(80)
    parts = (body[:i], body[i + 1:j], body[j + 1:])        # 空白で切って、その空白を落とす(空白 1 つで連ねると元の字に戻る)
    return (u'<?xml version="1.0"?><PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>%s</PMID><Article><ArticleTitle>%s</ArticleTitle><Abstract>'
            u'<AbstractText Label="METHODS">%s</AbstractText><AbstractText Label="RESULTS">%s <i>%s</i></AbstractText></Abstract></Article></MedlineCitation></PubmedArticle></PubmedArticleSet>'
            % (pmid, esc(title), esc(parts[0]), esc(parts[1]), esc(parts[2]))).encode("utf-8")


class FakeTransport(object):
    u"""作り物の API。``studies``(JSON の並び)を 10 件ずつのページで返す。``abstracts`` = {pmid: bytes}。呼び出しの URL と時刻を覚える。"""

    def __init__(self, ms, studies, abstracts, clock, version_status=200, studies_status=200, efetch_status=200, efetch_body=None):
        self.ms = ms
        self.studies = studies
        self.abstracts = abstracts
        self.clock = clock
        self.log = []
        self.version_status, self.studies_status, self.efetch_status, self.efetch_body = version_status, studies_status, efetch_status, efetch_body

    def __call__(self, url):
        self.log.append((url, self.clock.now()))
        if url == self.ms.VERSION_URL:
            return self.version_status, json.dumps({"apiVersion": "2.0.5", "dataTimestamp": "2026-01-01T00:00:00"}).encode("utf-8")
        if url.startswith(self.ms.STUDIES_URL + "?"):
            if self.studies_status != 200:
                return self.studies_status, b""
            q = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
            start = int(q["pageToken"][0][1:]) if "pageToken" in q else 0
            page = {"studies": self.studies[start:start + 10]}
            if start + 10 < len(self.studies):
                page["nextPageToken"] = "t%d" % (start + 10)
            return 200, json.dumps(page).encode("utf-8")
        if url.startswith(self.ms.EFETCH_URL + "?"):
            if self.efetch_status != 200:
                return self.efetch_status, b""
            if self.efetch_body is not None:
                return 200, self.efetch_body
            pmid = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)["id"][0]
            return 200, self.abstracts.get(pmid, b"<PubmedArticleSet></PubmedArticleSet>")
        raise AssertionError(u"想定外の URL: %s" % url[:60])

    def kinds(self):
        out = []
        for url, _t in self.log:
            out.append("v" if url == self.ms.VERSION_URL else "s" if url.startswith(self.ms.STUDIES_URL) else "e")
        return out


class Temp(object):
    def __enter__(self):
        self.d = tempfile.mkdtemp(prefix="ct0_gate_")
        return self.d

    def __exit__(self, *a):
        shutil.rmtree(self.d, ignore_errors=True)


def run_fetch(ms, studies, abstracts, cache, **kw):
    clock = FakeClock()
    tr = FakeTransport(ms, studies, abstracts, clock, **kw)
    log = ms.fetch(cache=cache, transport=tr, sleep=clock.sleep, clock=clock.now, today=u"2026-11-21", say=lambda *a: None)
    return log, tr


def good_abstracts(studies, ms=None):
    u"""各試験の最初の RESULT の PMID に、その試験の登録番号を入れた作り物の要旨を対応させる。"""
    out = {}
    for st in studies:
        nct = st["protocolSection"]["identificationModule"]["nctId"]
        for r in st["protocolSection"]["referencesModule"]["references"]:
            if r.get("type") == "RESULT" and r.get("pmid"):
                out.setdefault(r["pmid"], abstract_xml(r["pmid"], fake_text(nct)))
    return out


def conditions_problems(ms=None):
    u"""封 §1 の条件の当て方を 1 つずつ。"""
    ms = ms or MS
    out = []
    studies = [
        make_study(0, results=False),                                                                    # 結果が無い
        make_study(1, phases=("PHASE2",)),                                                               # Phase 3 でない
        make_study(2, stype="OBSERVATIONAL"),                                                            # 介入でない
        make_study(3, refs=((u"BACKGROUND", u"8000003"),)),                                              # RESULT が無い
        make_study(4, refs=((u"RESULT", None),)),                                                        # RESULT だが PMID が無い
        make_study(5, refs=((u"BACKGROUND", u"8000005"), (u"RESULT", u"9000005"), (u"RESULT", u"9000555"))),   # 要旨に登録番号が無い(題にだけ在る)
        make_study(6, refs=((u"DERIVED", u"8000006"), (u"RESULT", u"9000006"))),                         # 対 1
        make_study(7, refs=((u"RESULT", u"9000007"), (u"RESULT", u"9000777"))),                          # 対 2(頭の RESULT だけ使う)
        make_study(8, phases=("PHASE2", "PHASE3")),                                                      # 対 3(Phase 2/3 は Phase 3 を含む)
    ]
    ab = good_abstracts(studies)
    ab[u"9000005"] = abstract_xml(u"9000005", u"Short text without the number.", title=u"Title NCT00000006 only")
    ab[u"9000555"] = abstract_xml(u"9000555", fake_text(u"NCT00000006"))                                   # 使わない(頭の RESULT は 9000005)
    ab[u"9000777"] = abstract_xml(u"9000777", u"no number here")
    with Temp() as d:
        cache = os.path.join(d, "c")
        log, tr = run_fetch(ms, studies, ab, cache)
        got = [(p[u"n"], p[u"nct"], p[u"pmid"]) for p in log[u"pairs"]]
        if got != [(1, u"NCT00000007", u"9000006"), (2, u"NCT00000008", u"9000007"), (3, u"NCT00000009", u"9000008")]:
            out.append(u"対の付き方が想定と違う: %s" % got)
        if log[u"seen"] != 9 or log[u"stop"] != u"候補が尽きた":
            out.append(u"見た試験・止めた理由が違う: %s %s" % (log[u"seen"], log[u"stop"]))
        sk = dict(log[u"skips"])
        if sk != {u"条件(結果が在る・介入・Phase 3)に合わない": 3, u"RESULT の文献(番号つき)が無い": 2, u"要旨に登録番号が無い": 1}:
            out.append(u"飛ばした理由の数が違う: %s" % sk)
        efetched = [urllib.parse.parse_qs(urllib.parse.urlsplit(u).query)["id"][0] for u, _t in tr.log if u.startswith(ms.EFETCH_URL)]
        if efetched != [u"9000005", u"9000006", u"9000007", u"9000008"]:
            out.append(u"efetch した PMID が(試験の並びの順・頭の RESULT だけ)でない: %s" % efetched)
        names = sorted(os.listdir(cache))
        if names != sorted([u"pairs.json", u"study_1.json", u"study_2.json", u"study_3.json", u"abstract_1.xml", u"abstract_2.xml", u"abstract_3.xml"]):
            out.append(u"置き場の file が想定と違う: %s" % names)
        if log[u"date"] != u"2026-11-21" or log[u"api"][u"apiVersion"] != u"2.0.5":
            out.append(u"取った日付・API の版が違う")
    return out


def ten_problems(ms=None):
    u"""10 対そろったらその場で止める(次の試験を見ない・次のページも呼ばない)。"""
    ms = ms or MS
    studies = [make_study(i) for i in range(25)]
    with Temp() as d:
        log, tr = run_fetch(ms, studies, good_abstracts(studies), os.path.join(d, "c"))
        out = []
        if len(log[u"pairs"]) != 10 or log[u"seen"] != 10 or log[u"stop"] != u"10 対そろった":
            out.append(u"10 対で止まらない: 対 %d・見た %d・%s" % (len(log[u"pairs"]), log[u"seen"], log[u"stop"]))
        if tr.kinds() != ["v", "s"] + ["e"] * 10:
            out.append(u"10 対の後に呼び出しが続いている: %s" % u"".join(tr.kinds()))
    return out


def c400_problems(ms=None):
    u"""見た試験が 400 に達したら、対が 10 に届かなくても止める(届いた数で続ける)。400 本目は調べ終える・401 本目は見ない。"""
    ms = ms or MS
    studies = [make_study(i, results=False) for i in range(1000)]
    for i in (50, 150, 399, 400):                                                                     # 400 本目(0 始まりの 399)は対になる・401 本目は見ない
        studies[i] = make_study(i)
    out = []
    with Temp() as d:
        log, tr = run_fetch(ms, studies, good_abstracts(studies), os.path.join(d, "c"))
        if log[u"seen"] != 400 or len(log[u"pairs"]) != 3 or log[u"stop"] != u"見た試験が 400 に達した":
            out.append(u"400 で止まらない: 見た %d・対 %d・%s" % (log[u"seen"], len(log[u"pairs"]), log[u"stop"]))
        if tr.kinds().count("s") != 40 or tr.kinds().count("e") != 3:
            out.append(u"400 の後に呼び出しが続いている: studies %d・efetch %d" % (tr.kinds().count("s"), tr.kinds().count("e")))
    studies2 = [make_study(i, results=False) for i in range(1000)]
    with Temp() as d:
        log, tr = run_fetch(ms, studies2, {}, os.path.join(d, "c"))
        if log[u"seen"] != 400 or log[u"pairs"] != []:
            out.append(u"対が 0 のまま 400 で止まらない")
    return out


def gap_problems(ms=None):
    u"""呼び出しの間が 1 回ごとに 1 秒以上(両方の出所の全部の隣り合う 2 回)。"""
    ms = ms or MS
    studies = [make_study(i) for i in range(25)]
    out = []
    with Temp() as d:
        _log, tr = run_fetch(ms, studies, good_abstracts(studies), os.path.join(d, "c"))
        ts = [t for _u, t in tr.log]
        gaps = [b - a for a, b in zip(ts, ts[1:])]
        if len(gaps) < 10 or min(gaps) < 1.0 - 1e-9:
            out.append(u"呼び出しの間が 1 秒未満の所が在る(最小 %.3f)" % (min(gaps) if gaps else -1))
    return out


def url_problems(ms=None):
    u"""問い合わせの字: studies の引数・efetch に tool を付け email を付けない・次のページは pageToken だけ足す。"""
    ms = ms or MS
    out = []
    q1 = urllib.parse.parse_qsl(urllib.parse.urlsplit(ms.studies_url()).query)
    if q1 != [("aggFilters", "results:with,studyType:int,phase:3"), ("pageSize", "10"), ("format", "json")]:
        out.append(u"studies の引数が決めと違う: %s" % q1)
    q2 = urllib.parse.parse_qsl(urllib.parse.urlsplit(ms.studies_url("abc")).query)
    if q2 != q1 + [("pageToken", "abc")]:
        out.append(u"次のページの引数が(同じ引数 + pageToken)でない")
    if not ms.studies_url().startswith("https://clinicaltrials.gov/api/v2/studies?") or ms.VERSION_URL != "https://clinicaltrials.gov/api/v2/version":
        out.append(u"API の送り先が違う")
    u = urllib.parse.urlsplit(ms.efetch_url("123"))
    qe = urllib.parse.parse_qsl(u.query)
    if u.scheme + "://" + u.netloc + u.path != "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi" or sorted(k for k, _v in qe) != ["db", "id", "retmode", "tool"]:
        out.append(u"efetch の引数が(db・id・retmode・tool だけ)でない: %s" % qe)
    if dict(qe).get("tool") != ms.TOOL or dict(qe).get("db") != "pubmed" or dict(qe).get("retmode") != "xml":
        out.append(u"efetch の tool・db・retmode が違う")
    return out


def stop_problems(ms=None):
    u"""止まる条件: 置き場が repo の中・置き場が空でない・200 でない返事(両方の出所)・E-utilities のエラーの形・何も書かずに止まる(repo の中)。"""
    ms = ms or MS
    out = []
    studies = [make_study(i) for i in range(3)]
    ab = good_abstracts(studies)
    probe = os.path.join(ROOT, "ct0_gate_probe_cache")
    stopped = stops(ms, lambda: run_fetch(ms, studies, ab, probe))
    made = os.path.exists(probe)
    if made:
        shutil.rmtree(probe, ignore_errors=True)               # 変異が repo の中に作った物を残さない
    if not stopped or made:
        out.append(u"置き場が repo の中なのに止まらないか、repo の中に何かが出来た")
    with Temp() as d:
        c = os.path.join(d, "c")
        os.makedirs(c)
        with open(os.path.join(c, "x"), "w") as fh:
            fh.write("x")
        if not stops(ms, lambda: run_fetch(ms, studies, ab, c)):
            out.append(u"置き場に何かが在るのに止まらない")
    for kw, what in (({"version_status": 500}, u"version が 500"), ({"studies_status": 429}, u"studies が 429"), ({"efetch_status": 429}, u"efetch が 429"), ({"efetch_status": 400}, u"efetch が 400")):
        with Temp() as d:
            if not stops(ms, lambda: run_fetch(ms, studies, ab, os.path.join(d, "c"), **kw)):
                out.append(u"%s なのに止まらない" % what)
    for body, what in ((b'{"error":"x"}', u"JSON のエラー"), (b"<eFetchResult><ERROR>x</ERROR></eFetchResult>", u"ERROR 要素")):
        with Temp() as d:
            if not stops(ms, lambda: run_fetch(ms, studies, ab, os.path.join(d, "c"), efetch_body=body)):
                out.append(u"efetch が %s なのに止まらない" % what)
    return out


# ---------------------------------------------------------------- 5. 記録の禁止の検査
def clean_problems(ms=None):
    ms = ms or MS
    out = []
    ok = od([(u"対", [od([(u"番号", 1), (u"材料の sha256", od([(u"登録の JSON", u"a" * 64)]))])]), (u"git", u"b" * 40)])
    okt = ms.dumps(ok)
    if stops(ms, ms.check_clean, ok, okt, [(u"NCT00000001", u"12345678", fake_text())]):
        out.append(u"きれいな記録で止まる(sha256 の 16 進を含む)")
    secret = [(u"NCT00000001", u"12345678", fake_text())]
    cases = [
        (u"禁止の欄(nct)", od([(u"nct", 1)]), None),
        (u"禁止の欄(PMID・大文字)", od([(u"対", [od([(u"PMID", 1)])])]), None),
        (u"禁止の欄(要旨)", od([(u"要旨", 1)]), None),
        (u"禁止の欄(text)", od([(u"text", 1)]), None),
        (u"登録番号の形", od([(u"x", u"NCT00000099")]), None),
        (u"登録番号の形(空白)", od([(u"x", u"nct 123")]), None),
        (u"PMID の字", od([(u"x", u"PMID: 1")]), None),
        (u"8 桁の数", od([(u"x", u"id 12345678 x")]), None),
        (u"7 桁の数", od([(u"x", u"id 1234567 x")]), None),
        (u"材料の登録番号", od([(u"x", u"NCT00000001")]), secret),
        (u"材料の PMID(桁が短い)", od([(u"x", u"id 4242 x")]), [(u"NCT00000001", u"4242", u"abc def ghi jkl mno pqr")]),
        (u"要旨の字の 16 字", od([(u"x", u"the " + fake_text()[30:60])]), secret),
    ]
    for what, rec, sec in cases:
        text = ms.dumps(rec)
        if not stops(ms, ms.check_clean, rec, text, sec):
            out.append(u"%s が止まらない" % what)
        if not stops(ms, ms.record_text, rec, sec):
            out.append(u"%s が record_text で止まらない" % what)
    with Temp() as d:
        p = os.path.join(d, "r.json")
        bad = od([(u"x", u"NCT00000099")])
        if not stops(ms, ms.write_record, p, bad) or os.path.exists(p):
            out.append(u"禁止の字が在る記録を書いた(書く前の検査)")
        good = od([(u"x", 1)])
        ms.write_record(p, good)
        if not stops(ms, ms.write_record, p, good):
            out.append(u"記録が既に在るのに書き直せる")
    return out


# ---------------------------------------------------------------- 6. 置き場 → 記録 → --check
class NoNetwork(object):
    u"""0 円の経路を走らせる間、``urllib.request.urlopen`` が呼ばれたら失敗にする。"""

    def __enter__(self):
        self.old = urllib.request.urlopen
        self.called = 0

        def boom(*a, **kw):
            self.called += 1
            raise AssertionError(u"通信しようとした")
        urllib.request.urlopen = boom
        return self

    def __exit__(self, *a):
        urllib.request.urlopen = self.old


def nfkc_problems(ms=None):
    u"""NFKC で変わる字(全角の数字と ％・NBSP)を作り物の要旨に入れて ``tally_text`` に直接渡す。NFKC を掛けないと類が変わる。"""
    ms = ms or MS
    out = []
    per, outside = ms.tally_text(u"Rate \uff12\uff15\uff05; n\u00a0=\u00a030.")
    if tally_cells(per) != od([("P", (1, 1)), ("C", (0, 0)), ("N", (1, 0)), ("R", (0, 0)), ("V", (0, 0)), ("Y", (0, 0)), ("O", (0, 0))]) or outside != 0:
        out.append(u"NFKC で変わる字の類・拾った数が想定と違う: %s %s" % (dict(tally_cells(per)), outside))
    return out


def zero_rows_problems(ms=None):
    u"""登録の側で値の読める行が 0 の対を 1 つ混ぜる。CT0-7 の 0 の対の数が 1・理由の欄の名が記録に出る。置き場の表が古い名(PMID の語を含む)の飛ばした理由を持っていても、記録を書ける。"""
    ms = ms or MS
    out = []
    studies = [make_study(0), make_study(1), make_study(2), make_study(3, refs=((u"BACKGROUND", u"8000003"),))]
    studies[1]["resultsSection"] = {"outcomeMeasuresModule": {"outcomeMeasures": [{"classes": [{"categories": [{"measurements": [{"value": "NA"}]}]}]}]}}
    with Temp() as d:
        cache, rec_path = os.path.join(d, "c"), os.path.join(d, "r.json")
        run_fetch(ms, studies, good_abstracts(studies), cache)
        pp = os.path.join(cache, "pairs.json")
        with io.open(pp, encoding="utf-8") as fh:
            raw = fh.read()
        old_name = u"RESULT の文献(PMID つき)が無い"
        if u"RESULT の文献(番号つき)が無い" not in raw:
            out.append(u"取る関数の飛ばした理由の名が想定と違う")
        with io.open(pp, "w", encoding="utf-8") as fh:                       # 古い置き場(PMID の語を含む名)の再現
            fh.write(raw.replace(u"RESULT の文献(番号つき)が無い", old_name))
        rec = guard(ms.run, root=d, cache=cache, out=rec_path, say=lambda *a: None)
        if isinstance(rec, list):
            return out + [u"古い名の置き場から記録を書けない: %s" % rec]
        text = io.open(rec_path, encoding="utf-8").read()
        if u"PMID" in text or u"RESULT の文献(番号つき)が無い" not in text:
            out.append(u"記録の欄の名に PMID の語が残るか、替えた名が無い")
        pred = rec[u"予測の判定に要る数(CT0-1〜CT0-7。当たり・外れは結果の文書で)"]
        if pred[u"CT0-7 登録の側の値の読める行が 0 の対の数"] != 1:
            out.append(u"CT0-7 の 0 の対の数が 1 でない: %s" % pred[u"CT0-7 登録の側の値の読める行が 0 の対の数"])
        rows = rec[u"対"]
        if [r[u"登録の側の値の読める行の数"] for r in rows] != [5, 0, 5]:
            out.append(u"対ごとの行の数が想定と違う: %s" % [r[u"登録の側の値の読める行の数"] for r in rows])
        if len(rows[1][u"登録の側が 0 行の理由(欄の名)"]) != 2 or u"outcomeMeasuresModule.outcomeMeasures" not in text:
            out.append(u"0 行の対の理由の欄の名が記録に出ていない")
    return out


def keyname_problems(ms=None):
    u"""欄の名に PMID の語を入れた作り物の記録を本番と同じ道(build_record → write_record)で通すと止まる(書かれない)。いまの build_record が作る記録の欄の名は検査を通る。"""
    ms = ms or MS
    out = []
    studies = [make_study(i) for i in range(2)] + [make_study(2, refs=((u"BACKGROUND", u"8000003"),))]
    ab = dict((u"90000%02d" % i, abstract_xml(u"90000%02d" % i, fake_text(u"NCT%08d" % (i + 1)) + u" Registered at ClinicalTrials.gov API v2 with apiVersion and dataTimestamp.")) for i in range(2))
    with Temp() as d:
        cache = os.path.join(d, "c")
        run_fetch(ms, studies, ab, cache)                      # 要旨が出どころの名(ClinicalTrials.gov API v2・apiVersion)を持っていても、記録の欄の名が要旨の字に当たらない
        log, mats = ms.load_cache(cache)
        rec, secret = ms.build_record(log, mats)
        keys = [str(k) for k in ms.walk_keys(rec)]
        if any(re.search(r"PMID|NCT", k, re.I) for k in keys):
            out.append(u"いまの build_record の欄の名に PMID・NCT の語が在る")
        p = os.path.join(d, "ok.json")
        if guard(ms.write_record, p, rec, secret) is not None or not os.path.exists(p):
            out.append(u"いまの build_record の記録が write_record を通らない")
        for bad_key in (u"RESULT の文献(PMID つき)が無い", u"pmid の数"):
            bad, secret2 = ms.build_record(log, mats)
            bad[u"取り方の数"][u"飛ばした試験の理由別"][bad_key] = 1
            q = os.path.join(d, "bad.json")
            if not stops(ms, ms.write_record, q, bad, secret2) or os.path.exists(q):
                out.append(u"欄の名に %s を入れた記録が止まらないか書かれた" % bad_key[:8])
    return out


def leak_gram_problems(ms=None):
    u"""要旨の字の検査の境目: 16 字ちょうどは止まり、15 字は止まらない。"""
    ms = ms or MS
    out = []
    sec = lambda a: [(u"NCT00000001", u"4242", a)]
    rec = od([(u"x", u"zz abcdefghijklmnop zz")])
    if not stops(ms, ms.check_clean, rec, ms.dumps(rec), sec(u"abcdefghijklmnop")):
        out.append(u"16 字ちょうどの要旨の字が止まらない")
    rec2 = od([(u"x", u"zz abcdefghijklmno zz")])
    if stops(ms, ms.check_clean, rec2, ms.dumps(rec2), sec(u"abcdefghijklmno")):
        out.append(u"15 字の要旨の字で止まる(窓は 16 字)")
    return out


def e2e_problems(ms=None):
    ms = ms or MS
    out = []
    studies = [make_study(i) for i in range(3)]
    ab = good_abstracts(studies)
    with Temp() as d:
        cache, rec_path = os.path.join(d, "c"), os.path.join(d, "rec", "r.json")
        run_fetch(ms, studies, ab, cache)
        with NoNetwork() as nn:
            rec = ms.run(root=d, cache=cache, out=rec_path, say=lambda *a: None)
            now = ms.check(root=d, cache=cache, rec_path=rec_path, say=lambda *a: None)
            if nn.called:
                out.append(u"0 円の経路が通信しようとした")
        if ms.dumps(rec) != ms.dumps(now):
            out.append(u"記録と --check の数え直しが違う")
        agg = rec[u"集計"]
        if (agg[u"対の数"], agg[u"数の字の数"], agg[u"拾った数"], agg[u"分母の外で拾った数"]) != (3, 3 * HAND_DEN, 3 * HAND_PICK, 3 * HAND_OUTSIDE):
            out.append(u"集計が手で数えた値の 3 倍と違う: %s" % dict((k, v) for k, v in agg.items() if k != u"類別"))
        if [(c, v[u"分母"], v[u"拾った"]) for c, v in agg[u"類別"].items()] != [(c, 3 * a, 3 * b) for c, (a, b) in HAND.items()]:
            out.append(u"類別の集計が手で数えた値の 3 倍と違う")
        pred = rec[u"予測の判定に要る数(CT0-1〜CT0-7。当たり・外れは結果の文書で)"]
        if pred[u"CT0-2 拾った / 数の字の全部"] != od([(u"拾った", 12), (u"分母", 57), (u"%", 21.1)]) or pred[u"CT0-3 類 P で拾った / 類 P"][u"%"] != 100.0:
            out.append(u"予測の判定に要る数(CT0-2・CT0-3)が手で数えた値と違う")
        if pred[u"CT0-4 類 N・R・V の合計で拾った / 合計"] != od([(u"拾った", 0), (u"分母", 18), (u"%", 0.0)]) or pred[u"CT0-5 類 C で拾った / 類 C"][u"分母"] != 9:
            out.append(u"予測の判定に要る数(CT0-4・CT0-5)が手で数えた値と違う")
        if pred[u"CT0-6 分母の外で拾った(10 対の合計)"] != 3 or pred[u"CT0-7 登録の側の値の読める行が 0 の対の数"] != 0:
            out.append(u"予測の判定に要る数(CT0-6・CT0-7)が違う")
        rows = rec[u"対"]
        if [r[u"番号"] for r in rows] != [1, 2, 3] or any(r[u"登録の側の値の読める行の数"] != 5 for r in rows):
            out.append(u"対の番号か登録の側の行の数が違う")
        text = io.open(rec_path, encoding="utf-8").read()
        if rec[u"対"][0][u"材料の sha256"][u"要旨の XML"] != ms.sha256_file(os.path.join(cache, "abstract_1.xml")):
            out.append(u"材料の sha256 が置き場の file と違う")
        for must in (u"封の commit", u"この script の sha256", u"engine の指紋", u"profile", u"取った日付", u"取り方の数", u"限界"):
            if must not in rec:
                out.append(u"記録に項目が無い: %s" % must)
        if rec[u"engine の指紋"][u"adapter_xbrl_py_sha256"] != ms.VD.engine_fingerprint()[u"adapter_xbrl_py_sha256"]:
            out.append(u"engine の指紋が今の engine と違う")
        for nct in (u"NCT0000000", u"90000"):
            if nct in text:
                out.append(u"記録に登録番号か PMID の字が在る")
        if not stops(ms, ms.run, root=d, cache=cache, out=rec_path, say=lambda *a: None):
            out.append(u"記録が既に在るのに run が止まらない")
        # --check が数を変えた記録・変えた置き場で止まる
        bad = text.replace(u'"拾った数": 4', u'"拾った数": 5', 1)
        bp = os.path.join(d, "bad.json")
        with io.open(bp, "w", encoding="utf-8") as fh:
            fh.write(bad)
        if bad == text or not stops(ms, ms.check, root=d, cache=cache, rec_path=bp, say=lambda *a: None):
            out.append(u"数を変えた記録で --check が止まらない")
        with open(os.path.join(cache, "abstract_2.xml"), "ab") as fh:
            fh.write(b" ")
        if not stops(ms, ms.check, root=d, cache=cache, rec_path=rec_path, say=lambda *a: None):
            out.append(u"置き場の材料を変えても --check が止まらない")
        if not stops(ms, ms.run, root=d, cache=os.path.join(d, "none"), out=os.path.join(d, "o.json"), say=lambda *a: None):
            out.append(u"置き場が無いのに run が止まらない")
    return out


# ---------------------------------------------------------------- 7. 配線
STDLIB_OK = ("__future__", "argparse", "collections", "hashlib", "io", "json", "os", "re", "sys", "time", "unicodedata", "urllib", "xml", "adapters")
NETWORK_MODULES = ("http", "socket", "ssl", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx", "subprocess", "importlib")
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS")


def import_problems(src=None):
    u"""script の import は標準ライブラリと engine の 3 module(recipes・verify_document・vocabulary)だけ。通信は ``urllib_transport`` の 1 か所だけ。0 円の経路(run・check・build_record・load_cache・tally_text)は通信の道を使わない。
    環境変数・鍵・``.env`` を読まない。"""
    src = src if src is not None else read(SCRIPT_REL)
    tree = ast.parse(src)
    out = []
    for n in ast.walk(tree):
        names = []
        if isinstance(n, ast.Import):
            names = [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            names = [(n.module or u"")] + [u"%s.%s" % (n.module, a.name) for a in n.names] if n.module == "adapters.xbrl" else [(n.module or u"")]
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("__import__", "eval", "exec"):
            out.append(u"動的な import・eval・exec の呼び出し")
        for nm in names:
            top = nm.split(".")[0]
            if top in NETWORK_MODULES:
                out.append(u"許さない module を import している: %s" % nm)
            elif top not in STDLIB_OK:
                out.append(u"許す一覧に無い module: %s" % nm)
    eng = sorted(a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module == "adapters.xbrl" for a in n.names)
    if eng != ["recipes", "verify_document", "vocabulary"]:
        out.append(u"engine から読む module が recipes・verify_document・vocabulary の 3 つだけでない: %s" % eng)
    attrs = [(n.value.id, n.attr) for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)]
    if ("os", "environ") in attrs or ("os", "getenv") in attrs:
        out.append(u"環境変数を読んでいる")
    opens = [n for n in ast.walk(tree) if isinstance(n, ast.Attribute) and n.attr == "urlopen"]
    if len(opens) != 1:
        out.append(u"urlopen を使う所が 1 か所でない(%d)" % len(opens))
    funcs = dict((n.name, n) for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    uo = funcs.get("urllib_transport")
    if uo is None or not any(isinstance(x, ast.Attribute) and x.attr == "urlopen" for x in ast.walk(uo)):
        out.append(u"urlopen が urllib_transport の中でない")
    for fname in ("run", "check", "build_record", "load_cache", "tally_text", "denominator", "engine_picks", "registry_rows", "check_clean", "write_record", "main"):
        f = funcs.get(fname)
        if f is None:
            out.append(u"関数が無い: %s" % fname)
            continue
        used = set(x.id for x in ast.walk(f) if isinstance(x, ast.Name))
        if fname != "main":
            for bad in ("urllib_transport", "fetch", "Throttle", "get_json"):
                if bad in used:
                    out.append(u"%s が %s を使っている(通信する道が 0 円の経路に在る)" % (fname, bad))
    doc = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant):
            doc.add(id(n.body[0].value))
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc and (u".env" in n.value or u"dotenv" in n.value or u"API_KEY" in n.value):
            out.append(u"鍵・.env の字が在る")
    return out


def reserved_problems(rel=GATE_REL, base=ROOT):
    out = []
    with open(os.path.join(base, rel), encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    for n, line in enumerate(lines, 1):
        if any(line.startswith(p) for p in RESERVED_PREFIXES):
            out.append(u"%s:%d" % (rel, n))
    return out


# ---------------------------------------------------------------- 変異
#: (名前, 置き換え前(script の中でちょうど 1 回)・置き換え後・赤になるべき検査の名前)。予測は「その検査が赤になる」
MUTANTS = (
    (u"M1 類 P の判定を外す", u'    return text[b:b + 1] == u"%"', u"    return False", ("tally", "cases")),
    (u"M2 類 C の判定を外す", u'    return C_WORDS[0] in before or C_WORDS[1] in before.lower()', u"    return False", ("tally", "cases")),
    (u"M3 類 N の判定を外す", u'    return any(t in before for t in N_BEFORE) or N_AFTER_RE.match(text, b) is not None', u"    return False", ("tally", "cases")),
    (u"M4 類 N の直後の語を外す", u'or N_AFTER_RE.match(text, b) is not None', u"or False", ("tally", "cases")),
    (u"M5 類 R の判定を外す", u'    return any(t in before for t in R_ABBR) or any(t in before.lower() for t in R_WORDS)', u"    return False", ("tally", "cases")),
    (u"M6 類 V の判定を外す", u'    return V_BEFORE_RE.search(text[max(0, a - V_WINDOW):a]) is not None', u"    return False", ("tally", "cases")),
    (u"M7 類 Y の判定を外す", u'    return re.fullmatch(r"\\d{4}", s) is not None and Y_RANGE[0] <= int(s) <= Y_RANGE[1]', u"    return False", ("tally", "cases")),
    (u"M8 類の順 P と C を入れ替える", u'CLASS_TESTS = (("P", is_p), ("C", is_c),', u'CLASS_TESTS = (("C", is_c), ("P", is_p),', ("tally", "cases", "seal")),
    (u"M9 類の順 N と R を入れ替える", u'("N", is_n), ("R", is_r),', u'("R", is_r), ("N", is_n),', ("tally", "cases", "seal")),
    (u"M10 前後に英字が接した字の除きを外す", u"        if (a > 0 and ALPHA_RE.match(text[a - 1])) or (b < len(text) and ALPHA_RE.match(text[b])):", u"        if False:", ("tally", "cases")),
    (u"M12 engine の読み取りを別の profile のものに替える", u'PROFILE = "P27"', u'PROFILE = "P29"', ("tally", "seal")),
    (u"M13 位置の照らしを緩める(重ならなくても拾った)", u"    return engine_span[0] < den_span[1] and den_span[0] < engine_span[1]", u"    return True", ("tally",)),
    (u"M14 位置の照らしを含むだけに締める", u"    return engine_span[0] < den_span[1] and den_span[0] < engine_span[1]", u"    return engine_span[0] <= den_span[0] and den_span[1] <= engine_span[1]", ("tally",)),
    (u"M15 10 対の止めを 11 にする", u"PAIRS_WANT = 10 ", u"PAIRS_WANT = 11 ", ("ten", "seal")),
    (u"M16 400 の止めを 401 にする", u"STUDIES_STOP = 400 ", u"STUDIES_STOP = 401 ", ("c400", "seal")),
    (u"M17 間隔を 0.5 秒にする", u"MIN_GAP_SECONDS = 1.0 ", u"MIN_GAP_SECONDS = 0.5 ", ("gap", "seal")),
    (u"M18 efetch の tool を外す", u'("retmode", "xml"), ("tool", TOOL)', u'("retmode", "xml")', ("url",)),
    (u"M19 置き場が repo の中でも止めない", u"    if inside_repo(cache):", u"    if False:", ("stop",)),
    (u"M20 禁止の欄の検査を外す", u"    if bad:", u"    if False:", ("clean",)),
    (u"M21 登録番号の形の検査を外す", u"    if NCT_FORM_RE.search(scan):", u"    if False:", ("clean",)),
    (u"M22 PMID の形の検査を外す", u"    if PMID_FORM_RE.search(scan):", u"    if False:", ("clean",)),
    (u"M23 材料の字の検査を外す", u"    for nct, pmid, abstract in (secret or ()):", u"    for nct, pmid, abstract in ():", ("clean",)),
    (u"M24 RESULT の型を問わずに文献を選ぶ", u'        if r.get("type") == "RESULT" and r.get("pmid"):', u'        if r.get("pmid"):', ("conditions",)),
    (u"M25 要旨に登録番号が無くても対にする", u"                elif nct not in text:", u"                elif False:", ("conditions",)),
    (u"M26 結果が在るの確かめを外す", u'    return st.get("hasResults") is True and dm.get("studyType")', u'    return dm.get("studyType")', ("conditions",)),
    (u"M27 Phase 3 の確かめを外す", u' and "PHASE3" in (dm.get("phases") or [])', u"", ("conditions",)),
    (u"M28 値が数として読めるの確かめを外す(字なら全部)", u"    return isinstance(v, str) and NUM_READABLE_RE.fullmatch(v.strip()) is not None", u"    return isinstance(v, str)", ("registry",)),
    (u"M29 E-utilities の 200 でない返事で止めない", u"                if status != 200:\n                    raise Stop(u\"**E-utilities", u"                if False:\n                    raise Stop(u\"**E-utilities", ("stop",)),
    (u"M30 置き場が空でなくても取る", u"    if os.path.exists(cache) and os.listdir(cache):", u"    if False:", ("stop",)),
    (u"M31 登録の側の値を評価項目の値だけ数える", u"    rows = n_om + n_ae", u"    rows = n_om", ("registry",)),
    (u"M34 NFKC を掛けずに字を読む", u"    text = nfkc(raw)", u"    text = raw", ("nfkc",)),
    (u"M35 読める行が 0 の対を数えない(reg == 0 → reg < 0)", u"zero_pairs += 1 if reg == 0 else 0", u"zero_pairs += 1 if reg < 0 else 0", ("zero",)),
    (u"M36 要旨の字の窓を 20 字にする", u"LEAK_GRAM = 16", u"LEAK_GRAM = 20", ("leakgram",)),
    (u"M37 記録に入れる飛ばした理由の名を替えない", u'k.replace(u"PMID つき", u"番号つき").replace(u"PMID", u"番号").replace(u"NCT", u"登録番号")', u"k", ("zero",)),
    (u"M38 出どころの版の欄の名を公開の名に戻す", u'(u"登録側の API の版", log[u"api"].get(u"apiVersion")), (u"登録側のデータの時刻", log[u"api"].get(u"dataTimestamp"))',
     u'(u"ClinicalTrials.gov API v2 の apiVersion", log[u"api"].get(u"apiVersion")), (u"ClinicalTrials.gov のデータの時刻", log[u"api"].get(u"dataTimestamp"))', ("keyname",)),
    (u"M33 類 R の窓を 12 字に戻す", u"R_WINDOW = 16 ", u"R_WINDOW = 12 ", ("tally", "cases", "seal")),
    (u"M32 題を要旨の本文に入れる", u'    for el in root.iter("AbstractText"):', u'    for el in root.iter():', ("conditions",)),
)
#: 黙ることが分かっている変異(理由つき)。黙ること自体を ``SilentTest`` が縛る
SILENT_BY_DESIGN = (
    (u"M11 登録番号の字の中の除き(a)を外す",
     u"        if any(x <= a and b <= y for x, y in nct):", u"        if False:",
     u"登録番号の字 NCT+数字の連なりの数字は、直前が英字 T か数字なので分母の正規表現の lookbehind で先に落ちる。(a) は (b) と lookbehind と二重。外しても数は変わらない"),
)


def check_by_name(name, mod, src):
    table = {u"seal": seal_problems, u"tally": tally_problems, u"cases": class_cases_problems, u"registry": registry_problems, u"conditions": conditions_problems,
             u"ten": ten_problems, u"c400": c400_problems, u"gap": gap_problems, u"url": url_problems, u"stop": stop_problems, u"clean": clean_problems, u"e2e": e2e_problems,
             u"nfkc": nfkc_problems, u"zero": zero_rows_problems, u"keyname": keyname_problems, u"leakgram": leak_gram_problems}
    if name in table:
        return table[name](mod)
    if name == u"import":
        return import_problems(src)
    raise AssertionError(name)


ALL_CHECKS = (u"seal", u"tally", u"cases", u"registry", u"conditions", u"ten", u"c400", u"gap", u"url", u"stop", u"clean", u"e2e", u"nfkc", u"zero", u"keyname", u"leakgram", u"import")


def run_mutants(table=MUTANTS):
    base = read(SCRIPT_REL)
    out = []
    for name, old, new, checks in table:
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

    def test_a_2_the_seal_file_is_the_sealed_commit_and_unchanged(self):
        self.assertEqual([], seal_history_problems())

    def test_a_3_a_changed_seal_character_turns_the_comparison_red(self):
        seal = seal_text()
        for old, new in ((u"**10 対**", u"**9 対**"), (u"見た試験が 400 に達したら止め", u"見た試験が 399 に達したら止め"), (u"類 R の窓を 12 字から 16 字に替える", u"類 R の窓を 12 字から 15 字に替える"),
                         (u"- **Y**: 4 桁の 1900〜2099", u"- **Y**: 4 桁の 1900〜2098"), (u"直後が `%`", u"直後が `％`"), (u"`patients`・`participants`", u"`patients`・`partners`")):
            self.assertEqual(1, seal.count(old), old)
            self.assertNotEqual([], seal_problems(seal=seal.replace(old, new)), old)

    def test_a_4_engine_is_zero_lines_from_the_seal_commit(self):
        self.assertEqual([], engine_zero_problems())

    def test_a_5_the_boundary_import_list_is_not_widened(self):
        p = os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py")
        with io.open(p, encoding="utf-8") as fh:
            body = fh.read()
        self.assertNotIn(u"ctgov", body)


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
    def test_b_1_the_made_up_abstract_goes_through_the_real_functions_and_equals_the_hand_count(self):
        self.assertEqual([], tally_problems())

    def test_b_2_the_class_precedence_and_exclusions(self):
        self.assertEqual([], class_cases_problems())

    def test_b_3_the_hand_count_is_not_the_same_as_nearby_numbers(self):
        u"""手で数えた値が互いに違う(全部同じ数で偶然一致しない)・拾った数が分母の数と違う。"""
        dens = [v[0] for v in HAND.values()]
        self.assertGreater(len(set(dens)), 3)
        self.assertNotEqual(HAND_DEN, HAND_PICK)
        self.assertEqual(HAND_DEN, sum(dens))
        self.assertEqual(HAND_PICK, sum(v[1] for v in HAND.values()))

    def test_b_4_a_minus_sign_the_engine_does_not_read_still_counts_as_picked_by_overlap(self):
        per, outside = MS.tally_text(u"a change of −5.0%")
        self.assertEqual((1, 1), (per["P"][u"分母"], per["P"][u"拾った"]))
        self.assertEqual(0, outside)

    def test_b_5_the_registry_rows(self):
        self.assertEqual([], registry_problems())


class FetchTest(unittest.TestCase):
    def test_c_1_conditions(self):
        self.assertEqual([], conditions_problems())

    def test_c_2_ten_pairs_stop(self):
        self.assertEqual([], ten_problems())

    def test_c_3_four_hundred_studies_stop(self):
        self.assertEqual([], c400_problems())

    def test_c_4_one_second_between_calls(self):
        self.assertEqual([], gap_problems())

    def test_c_5_urls(self):
        self.assertEqual([], url_problems())

    def test_c_6_stops(self):
        self.assertEqual([], stop_problems())

    def test_c_7_the_throttle_waits_only_the_remainder(self):
        c = FakeClock()
        th = MS.Throttle(lambda u: (200, b""), sleep=c.sleep, clock=c.now)
        th("a")
        c.t += 0.4
        th("b")
        self.assertAlmostEqual(1.0, c.t - 1000.0, places=6)
        c.t += 5
        t0 = c.t
        th("c")
        self.assertEqual(t0, c.t)


class RecordTest(unittest.TestCase):
    def test_d_1_the_forbidden_checks_stop_planted_content(self):
        self.assertEqual([], clean_problems())

    def test_d_2_cache_to_record_to_check_without_network(self):
        self.assertEqual([], e2e_problems())

    def test_d_4_nfkc_changed_characters_are_normalised_before_the_classes(self):
        self.assertEqual([], nfkc_problems())

    def test_d_5_a_pair_with_zero_readable_registry_rows_and_an_old_cache_key_name(self):
        self.assertEqual([], zero_rows_problems())

    def test_d_6_record_key_names_pass_and_planted_pmid_nct_key_names_stop(self):
        self.assertEqual([], keyname_problems())

    def test_d_7_the_leak_window_edge(self):
        self.assertEqual([], leak_gram_problems())

    def test_d_3_the_real_record_when_present_is_clean_and_has_no_secret_form(self):
        p = os.path.join(ROOT, RECORD_REL)
        if not os.path.exists(p):
            self.skipTest(u"記録は本番の走りの後に書かれる。記録の中身の検査は結果の門に置く")
        text = read(RECORD_REL)
        rec = json.loads(text, object_pairs_hook=collections.OrderedDict)
        MS.check_clean(rec, text)


class WiringTest(unittest.TestCase):
    def test_e_1_imports_and_the_one_network_place(self):
        self.assertEqual([], import_problems())

    def test_e_2_the_import_check_sees_planted_violations(self):
        base = read(SCRIPT_REL)
        self.assertNotEqual([], import_problems(base + u"\nimport socket\n"))
        self.assertNotEqual([], import_problems(base + u"\nimport subprocess\n"))
        self.assertNotEqual([], import_problems(base + u"\nX = os.environ.get('A')\n"))
        self.assertNotEqual([], import_problems(base.replace(u"def run(root=ROOT", u"def run_x(root=ROOT")))
        self.assertNotEqual([], import_problems(base.replace(u"def check_clean(rec, text, secret=None):\n", u"def check_clean(rec, text, secret=None):\n    fetch()\n")))
        self.assertNotEqual([], import_problems(base.replace(u"from adapters.xbrl import recipes as R", u"from adapters.xbrl import recipes as R\nfrom adapters.xbrl import instance as I")))

    def test_e_3_the_gate_does_not_use_the_reserved_names(self):
        self.assertEqual([], reserved_problems())
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("ENGINE_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rel="g.py", base=d))

    def test_e_4_the_script_leaves_sys_modules_as_it_found_them(self):
        before = dict(sys.modules)
        mod = load_module(SCRIPT_REL, "ctgov_wall_script_for_sysmodules_check")
        self.assertEqual([], [k for k, v in before.items() if sys.modules.get(k) is not v])
        del mod

    def test_e_5_the_script_writes_nothing_inside_the_repo_by_default(self):
        self.assertFalse(MS.inside_repo(MS.CACHE_DIR))
        self.assertTrue(MS.inside_repo(os.path.join(ROOT, "x")))
        self.assertTrue(MS.inside_repo(os.path.join(REPO, "y", "z")))


class MutantTest(unittest.TestCase):
    def test_f_1_every_mutant_turns_its_checks_red_and_the_files_are_unchanged(self):
        before = (sha_of(SCRIPT_REL), sha_or_none(RECORD_REL))
        modules_before = dict(sys.modules)
        results = run_mutants()
        self.assertEqual(before, (sha_of(SCRIPT_REL), sha_or_none(RECORD_REL)))
        self.assertEqual([], [k for k, v in modules_before.items() if sys.modules.get(k) is not v])
        silent = [(n, c) for n, res, _w in results for c, red in res if not red]
        self.assertEqual([], silent)
        self.assertEqual(len(MUTANTS), len(results))

    def test_f_2_the_unmutated_script_is_green_on_every_check(self):
        base = read(SCRIPT_REL)
        mod = load_source(base)
        for name in ALL_CHECKS:
            self.assertEqual([], check_by_name(name, mod, base), name)

    def test_f_3_the_silent_mutants_are_silent_for_the_stated_reason(self):
        u"""(a) の除きは (b)・lookbehind と二重なので、外しても作り物の要旨の数も、登録番号の字の変形(NCT の後ろの数字の連なり)を足した字の分母も変わらない。"""
        base = read(SCRIPT_REL)
        for name, old, new, _why in SILENT_BY_DESIGN:
            self.assertEqual(1, base.count(old), name)
            mod = load_source(base.replace(old, new))
            for t in (fake_text(), u"NCT00000001 NCT-00000002 (NCT00000003) x NCT123 5 and NCT 9"):
                t = MS.nfkc(t)
                self.assertEqual(MS.denominator(t), mod.denominator(t), name)
            for c in (u"tally", u"cases", u"registry", u"conditions", u"clean", u"e2e"):
                self.assertEqual([], check_by_name(c, mod, None), (name, c))


if __name__ == "__main__":
    unittest.main()
