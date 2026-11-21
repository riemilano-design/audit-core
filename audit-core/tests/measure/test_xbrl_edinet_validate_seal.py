# -*- coding: utf-8 -*-
u"""封 docs/XBRL_EDINET_VALIDATE_SEAL_2026-11-21.md(XV0 ― 公開の検査の道具 Arelle の EDINET の規則を、提出済みの有報 67 本に掛けると、どの規則がどれだけ鳴るか)の封の門。

**この門は置き場も道具も読まない**(書類の置き場 ``~/.cache/audit-core/edinet/``・道具の venv は 1 度も開かない。道具が無い機械でも緑)。通信しない。
subprocess を実際に呼ぶのは、``sys.executable`` で字を出すだけの短い 1 行(``exec_cmd`` の shell を通さない・出力の合流・時間の上限の確かめ)だけ。道具の呼び出しは作り物の runner に差し替える。

**この門が縛るもの**

1. 封の字: 封の commit(1bda1997)・封の file が commit した blob と同じ・版の字・``ModelValue.py`` の sha256 2 つ・掛け方の引数・3 通り・67・符号の読み方の決め・止まる/走らなかった/走ったの字・
   34・予測の境の数・時間の上限 600 秒・限界の字が script の定数と同じ。
2. engine は読まない・封の commit から 0 行。境界の門の import 一覧にこの便の名前を足していない。
3. 作り物の出力の字で、符号の切り方・E と包みの形・1 回の類(Traceback が在れば 2 つの行の有無によらず止まった)・止まった回の指摘も数える・34 本以上の数え方(33 と 34 の境)・
   合計・記録の検査が禁止のものを断る、を本物の関数のまま通す(手で数えた値と照らす)。
4. 道具の確かめ(版・sha256 2 つ・実行 file)・3 通りを 1 本ずつ順に・``.xbrl`` を除いた写しを使い捨てて消す・置き場の zip を変えない・時間の上限を超えた回の数え方を、作り物の runner で通す。
5. script の import は標準ライブラリと importlib だけ(engine を読まない)。前の便の script は importlib で一意の名で読み、関数を呼ぶ(写さない)。便 XG1 の script と互いに読まない。
6. 行頭の名前: この門は ``ENGINE_LATER``・``UNTOUCHED``・``PIN_DEF``・``LATER_ENGINE_COMMITS``・``FROZEN_LATER``・``ENGINE_TRANSITIONS`` を行頭に置かない。

**どの検査も、変異で赤になることを 1 つずつ確かめる**(``MUTANTS``。script の字を 1 か所替えた版を memory の中に作る。file は書き換えない)。
"""
import ast
import collections
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
import zipfile

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
    mod = types.ModuleType("xbrl_edinet_validate_mutant")
    mod.__file__ = os.path.join(ROOT, SCRIPT_REL)
    before = dict(sys.modules)
    try:
        exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    finally:
        for k, v in before.items():
            if sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


SEAL_REL = "docs/XBRL_EDINET_VALIDATE_SEAL_2026-11-21.md"
SEAL_COMMIT_SHORT = "1bda1997"
SCRIPT_REL = "measure/xbrl_edinet_validate_2026-11-21.py"
GATE_REL = "tests/measure/test_xbrl_edinet_validate_seal.py"
RECORD_REL = "fixtures/xbrl/cd8/edinet_validate_2026-11-21.json"
OTHER_SCRIPT_NAME = "xbrl_tag_narrow"                 # 便 XG1 の script の名(互いに読まない)
MS = load_module(SCRIPT_REL, "xbrl_edinet_validate_script_for_seal_gate")
PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_edinet_validate_seal")
ORDER_FILES = (SCRIPT_REL, GATE_REL)
od = collections.OrderedDict
WALL_NAME = "_xv0_tag_wall_2026_11_21"


def read(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def sha_of(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def sha_or_none(rel):
    return sha_of(rel) if os.path.exists(os.path.join(ROOT, rel)) else None


def guard(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except BaseException as exc:                # noqa: BLE001
        return [u"例外: %s" % type(exc).__name__]


def stops(ms, fn, *a, **kw):
    try:
        fn(*a, **kw)
    except ms.Stop:
        return True
    return False


class Temp(object):
    def __enter__(self):
        self.d = tempfile.mkdtemp(prefix="xv0_gate_")
        return self.d

    def __exit__(self, *a):
        shutil.rmtree(self.d, ignore_errors=True)


# ======================================================================== 作り物の出力の字
ACT = u"Activation of plug-in Validate EDINET successful"
FMT = u"Identified filing format"


def out(lines, act=True, fmt=True, tb=False):
    parts = []
    if act:
        parts.append(u"[info] " + ACT)
    if fmt:
        parts.append(u"[info] " + FMT + u": EDINET")
    parts.extend(lines)
    if tb:
        parts.append(u"Traceback (most recent call last):\n  File \"x.py\", line 1, in <module>\nTypeError: boom")
    return u"\n".join(parts) + u"\n"


def ln(code, n=1):
    return [u"[%s] 本文の字 %d" % (code, i) for i in range(n)]


E_ = u"EDINET."
EC5611W, EC0121E, EC0130E, EC1001E, EC1057E, EC8054W, EC8070W = (E_ + c for c in (u"EC5611W", u"EC0121E", u"EC0130E", u"EC1001E", u"EC1057E", u"EC8054W", u"EC8070W"))
XB_MISSING = u"xbrl.3.5.2.4:missingRoleRef"
XB1 = u"xbrl.1:x"
#: 書類 1〜3 x 3 通りの作り物の出力の字(runner が返す)。値は手で決めた。(字, 時間の上限を超えたか)
FAKE_OUT = {
    (1, 0): (out(ln(EC5611W + u".GFM.1.1.3", 2) + ln(EC0121E + u".GFM.1", 1), tb=True), False),
    (1, 1): (out(ln(EC5611W + u".GFM.1", 3) + ln(EC0121E, 1) + ln(EC0130E, 2) + ln(EC1001E + u".GFM.2.2", 1) + ln(XB_MISSING, 1), tb=True), False),
    (1, 2): (out(ln(EC8054W, 4) + ln(EC5611W, 1) + ln(EC0121E, 1) + ln(EC1001E, 2)), False),
    (2, 0): (out(ln(XB1, 1), act=False, fmt=False), False),
    (2, 1): (out([u"[info] 何も出ない a", u"[info] 何も出ない b"], act=False, fmt=False), False),
    (2, 2): (u"途中の出力\n" + u"\n".join(ln(EC0130E + u".GFM.1", 1)) + u"\n", True),
    (3, 0): (out(ln(EC0121E, 1)), False),
    (3, 1): (out(ln(EC5611W, 1) + ln(EC1057E, 1), tb=True), False),
    (3, 2): (out(ln(EC5611W, 1) + ln(EC8070W, 1)), False)}
#: 手で数えた 1 回分: (類, 時間の上限を超えた, {符号: 行})
HAND_RUN = {
    (1, 0): (MS.CLS_STOPPED, False, 8, {EC0121E: 1, EC5611W: 2}),
    (1, 1): (MS.CLS_STOPPED, False, 13, {EC0121E: 1, EC0130E: 2, EC1001E: 1, EC5611W: 3, XB_MISSING: 1}),
    (1, 2): (MS.CLS_RAN, False, 10, {EC0121E: 1, EC1001E: 2, EC5611W: 1, EC8054W: 4}),
    (2, 0): (MS.CLS_NOT_RUN, False, 1, {XB1: 1}),
    (2, 1): (MS.CLS_NOT_RUN, False, 2, {}),
    (2, 2): (MS.CLS_STOPPED, True, 2, {EC0130E: 1}),
    (3, 0): (MS.CLS_RAN, False, 3, {EC0121E: 1}),
    (3, 1): (MS.CLS_STOPPED, False, 7, {EC1057E: 1, EC5611W: 1}),
    (3, 2): (MS.CLS_RAN, False, 4, {EC5611W: 1, EC8070W: 1})}
#: 手で数えた合計(3 通りそれぞれ): (類別 ran/stopped/not_run, 超えた数, 符号ごと {符号: (書類, 行)}, other_e, no_e, no_line, 種類(EDINET., ほか), 34 本以上, EC0121E か EC0130E)
HAND_TOTALS = [
    ((1, 1, 1), 0, {EC0121E: (2, 2), EC5611W: (1, 2), XB1: (1, 1)}, 0, 1, 0, (2, 1), 0, 2),
    ((0, 2, 1), 0, {EC5611W: (2, 4), EC0121E: (1, 1), EC0130E: (1, 2), EC1001E: (1, 1), XB_MISSING: (1, 1), EC1057E: (1, 1)}, 2, 1, 1, (5, 1), 0, 1),
    ((2, 1, 0), 1, {EC8054W: (1, 4), EC5611W: (2, 2), EC0121E: (1, 1), EC1001E: (1, 2), EC0130E: (1, 1), EC8070W: (1, 1)}, 1, 1, 0, (6, 0), 0, 2)]
HAND_JUDGED = [1, 3, 2, 2, 5, (1, 2, -1), 1, 1]                      # XV0-1 … 補

STEMS = ["S2FAKE01", "S2FAKE02", "S2FAKE03"]
ORDER_SHA = hashlib.sha256(u"\n".join(STEMS).encode("utf-8")).hexdigest()
MV_R, MV_P = b"model value R content", b"model value P content"
FREEZE = u"foo==1.0\narelle-cmdline==0.1.2\narelle-release==2.47.5\nzzz==0.1\n"
PYVER = u"Python 3.11.17\n"


def make_doc_zip(path, no):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("XBRL/PublicDoc/jpcrp030000-asr-001_E9999%d-000_2026-03-31_01_2026-06-30.xsd" % no, b"<schema/>")
        z.writestr("XBRL/PublicDoc/0101010_honbun_E9999%d-000_ixbrl.htm" % no, b"<html/>")
        z.writestr("XBRL/PublicDoc/api_added_E9999%d-000.xbrl" % no, b"<xbrl/>")             # API が足した file(写しでは除く)
        z.writestr("XBRL/AuditDoc/audit.xml", b"<a/>")


def make_docs(d, count=3):
    for i in range(count):
        make_doc_zip(os.path.join(d, STEMS[i] + ".zip"), i + 1)
    other = os.path.join(d, "S2OTHER1.zip")
    with zipfile.ZipFile(other, "w") as z:
        z.writestr("XBRL/PublicDoc/jpsps070000-xxx-001_E99999-000.xsd", b"<schema/>")
    return d


def make_tools(d):
    u"""作り物の道具 2 つ(実行 file と ModelValue.py の字だけ。実行はしない)。(R の場所, P の場所, ModelValue の path 2 つ)"""
    out_ = []
    mvs = []
    for nm, content in (("tool_r", MV_R), ("tool_p", MV_P)):
        t = os.path.join(d, nm)
        os.makedirs(os.path.join(t, "bin"))
        with open(os.path.join(t, "bin", "arelleCmdLine"), "w") as fh:
            fh.write("#!/bin/sh\n")
        mv = os.path.join(t, "ModelValue.py")
        with open(mv, "wb") as fh:
            fh.write(content)
        out_.append(t)
        mvs.append(mv)
    return out_[0], out_[1], mvs


class FakeRunner(object):
    u"""道具の呼び出しの作り物。呼ばれた順・写しの zip の中身・写しが在ったか・時間の上限を覚える。"""

    def __init__(self, mvs, freeze=FREEZE, pyver=PYVER, table=None):
        self.mvs, self.freeze, self.pyver, self.table = mvs, freeze, pyver, table or FAKE_OUT
        self.calls = []
        self.docs = []
        self.paths = []

    def __call__(self, cmd, timeout):
        cmd = list(cmd)
        exe = os.path.basename(cmd[0])
        if exe == "arelleCmdLine":
            tool = os.path.basename(os.path.dirname(os.path.dirname(cmd[0])))
            zp = cmd[cmd.index("-f") + 1]
            with zipfile.ZipFile(zp) as z:
                names = z.namelist()
            no = int(re.search(r"E9999(\d)-000_2026", [n for n in names if n.endswith(".xsd")][0]).group(1))
            run_no = {("tool_r", "EDINET-2026"): 0, ("tool_p", "EDINET-2026"): 1, ("tool_p", "EDINET-2025"): 2}[(tool, cmd[cmd.index("--disclosureSystem") + 1])]
            self.calls.append(dict(cmd=cmd, timeout=timeout, doc=no, run=run_no, names=names, existed=os.path.exists(zp)))
            self.paths.append(zp)
            return self.table[(no, run_no)]
        tool = os.path.basename(os.path.dirname(os.path.dirname(cmd[0])))
        if cmd[1:] == ["-m", "pip", "freeze"]:
            return self.freeze, False
        if cmd[1] == "-c":
            name = re.search(r"'([^']+\.py)'", cmd[2]).group(1)                 # -c の字が出す file の名(作り物の runner は、その名の file を道具の場所に探す)
            return os.path.join(os.path.dirname(self.mvs[0 if tool == "tool_r" else 1]), name) + u"\n", False
        if cmd[1:] == ["--version"]:
            return self.pyver, False
        raise AssertionError(cmd)


def all_runs(d, ms, runner=None, **kw):
    u"""作り物の置き場・道具で build_record を通す。(記録, secret, runner, tool_r, tool_p, 置き場, 一時の場所)。"""
    docs = os.path.join(d, "docs")
    os.makedirs(docs)
    make_docs(docs)
    tr, tp, mvs = make_tools(os.path.join(d, "tools"))
    tmp = os.path.join(d, "tmp")
    os.makedirs(tmp)
    runner = runner or FakeRunner([ms_mv(x) for x in mvs])
    args = dict(want=3, runner=runner, tmp_root=tmp, want_r=hashlib.sha256(MV_R).hexdigest(), want_p=hashlib.sha256(MV_P).hexdigest())
    args.update(kw)
    rec, secret = ms.build_record(tr, tp, docs, **args)
    return rec, secret, runner, tr, tp, docs, tmp


def ms_mv(path):
    return path


# ======================================================================== 1. 封の字
def seal_text():
    return read(SEAL_REL)


EXPECT_BOUNDS = od([("XV0-1", (60, None)), ("XV0-2", (None, 3)), ("XV0-3", (None, 33)), ("XV0-4", (40, None)), ("XV0-5", (8, 30)), ("XV0-6", (10, None)), ("XV0-7", (65, None))])
SEAL_BOUND_TEXT = od([("XV0-1", u"60 本以上"), ("XV0-2", u"3 本以下"), ("XV0-3", u"33 本以下"), ("XV0-4", u"40 本以上"), ("XV0-5", u"8 以上 30 以下"), ("XV0-6", u"10 本以上多い"), ("XV0-7", u"65 本以上")])
SEAL_SHA_R = u"3d108b7764e01306e032f78def4036813c74d32d0e27c3a684a9df4f8f376ff0"
SEAL_SHA_P = u"fd9b0d08bf283452fe4ebd6ec9de2f273010de0420b70e61c993a6c033814635"


def seal_problems(ms=None, seal=None):
    ms = ms or MS
    seal = seal if seal is not None else seal_text()
    out_ = []
    if ms.SEAL_COMMIT != SEAL_COMMIT_SHORT or ms.SEAL_REL != SEAL_REL or ms.SCRIPT_REL != SCRIPT_REL or ms.RECORD_REL != RECORD_REL:
        out_.append(u"script の封の commit・path・記録の path が門と違う")
    if ms.TOOL_VERSION != u"2.47.5" or u"版の字が `2.47.5`" not in seal or u"`arelle-release` の版 `2.47.5`" not in seal:
        out_.append(u"版の字が封と違う")
    if ms.SHA_R != SEAL_SHA_R or ms.SHA_P != SEAL_SHA_P or (u"`%s`" % SEAL_SHA_R) not in seal or (u"`%s`" % SEAL_SHA_P) not in seal \
            or seal.index(SEAL_SHA_R) > seal.index(SEAL_SHA_P) or u"道具 R(手を入れない)" not in seal or u"道具 P(1 行の直し)" not in seal:
        out_.append(u"ModelValue.py の sha256 2 つ(R・P の対応)が封と違う")
    if ms.PLUGINS != u"validate/EDINET|inlineXbrlDocumentSet" or u"`arelleCmdLine --plugins 'validate/EDINET|inlineXbrlDocumentSet' --disclosureSystem <年> -f <写しの zip> --validate`" not in seal:
        out_.append(u"掛け方の引数が封と違う")
    if tuple(ms.RUNS) != ((u"R", u"EDINET-2026"), (u"P", u"EDINET-2026"), (u"P", u"EDINET-2025")) or u"道具 R × `EDINET-2026`・道具 P × `EDINET-2026`・道具 P × `EDINET-2025` の 3 通り(67 本 × 3 = 201 回)" not in seal:
        out_.append(u"3 通りが封と違う")
    if ms.DOCS_WANT != 67 or u"どれも 67 本" not in seal:
        out_.append(u"67 が封と違う")
    if ms.STRIP_SUFFIX != u".xbrl" or u"名が `.xbrl` で終わる file を除いた写し" not in seal:
        out_.append(u".xbrl を除く決めが封と違う")
    if ms.MARK_ACTIVATION != ACT or ms.MARK_FORMAT != FMT or (u"`%s`" % ACT) not in seal or (u"`%s`" % FMT) not in seal or ms.TRACEBACK != u"Traceback" or u"`Traceback` の字が在れば **止まった**" not in seal:
        out_.append(u"1 回の類の字が封と違う")
    if (ms.CLS_STOPPED, ms.CLS_NOT_RUN, ms.CLS_RAN) != (u"止まった", u"走らなかった", u"走った") or u"**走った**" not in seal or u"の両方が無ければ **走らなかった**" not in seal:
        out_.append(u"類の名が封と違う")
    if ms.INFO_CODE != u"info" or u"符号 `info` は数えない" not in seal or ms.EDINET_PREFIX != u"EDINET." or u"符号が `EDINET.` で始まるものは、続く `EC` と数字 4 つと `E` か `W` の 1 字までを符号とする" not in seal:
        out_.append(u"符号の読み方が封と違う")
    if ms.EDINET_CODE_RE.pattern != u"^EDINET\\.EC\\d{4}[EW]" or ms.ENVELOPE_DIGIT != u"0" or u"数字の頭が `0` のもの(`EC0xxxE`)" not in seal:
        out_.append(u"E の符号・包みの形の決めが封と違う")
    if ms.BIG_DOCS != 34 or u"34 本以上で鳴った符号の種類の数" not in seal:
        out_.append(u"34 本が封と違う")
    if ms.TIMEOUT_SEC != 600:
        out_.append(u"時間の上限が 600 秒でない(依頼文の決め)")
    if dict(ms.BOUNDS) != dict(EXPECT_BOUNDS):
        out_.append(u"予測の境の数が門と違う")
    for k, t in SEAL_BOUND_TEXT.items():
        row_ = [x for x in seal.splitlines() if x.startswith(u"| %s" % k)]
        if len(row_) != 1 or t not in row_[0]:
            out_.append(u"封の予測の行の字が違う: %s" % k)
    for rel in (SCRIPT_REL, RECORD_REL, GATE_REL):
        if rel not in seal:
            out_.append(u"封に path が無い: %s" % rel)
    if u"docID・会社の名・EDINET コード・file の名・指摘の行の本文は書かない" not in seal:
        out_.append(u"封の記録の禁止の字が違う")
    sec7 = seal.split(u"## §7", 1)[-1]
    want_phrases = (u"提出の包みそのものではない", u"規則の年は 2 つとも", u"版の字が 0.0.1", u"道具 P は司令塔が 1 行を直した", u"無作為ではない", u"「EDINET の検査に通る」")
    if any(p not in sec7 for p in want_phrases) or any(k not in u"".join(ms.LIMITS) for k in (u"提出の包みそのものではない", u"規則の年は 2 つとも", u"0.0.1", u"1 行を直した", u"無作為ではない", u"「EDINET の検査に通る」")):
        out_.append(u"限界の字が封 §7 と違う")
    return out_


def seal_history_problems(root=REPO):
    rc = subprocess.run(["git", "-C", root, "log", "--format=%H", "--", PREFIX + SEAL_REL], stdout=subprocess.PIPE, universal_newlines=True)
    hs = [x for x in rc.stdout.split() if x]
    if len(hs) != 1 or not hs[0].startswith(SEAL_COMMIT_SHORT):
        return [u"封の file の履歴が封 %s の 1 commit でない" % SEAL_COMMIT_SHORT]
    blob = subprocess.run(["git", "-C", root, "show", "%s:%s" % (hs[0], PREFIX + SEAL_REL)], stdout=subprocess.PIPE).stdout.decode("utf-8")
    if blob != seal_text():
        return [u"今の封が封の commit の blob と違う"]
    return []


def order_of(root=REPO, seal_short=SEAL_COMMIT_SHORT, others=None):
    others = list(ORDER_FILES) if others is None else others
    return list(PR.order_problems(root, PREFIX, SEAL_REL, seal_short, [], others))


def engine_zero_problems(root=REPO):
    rc = subprocess.run(["git", "-C", root, "diff", "--name-only", SEAL_COMMIT_SHORT, "--", PREFIX + "adapters", PREFIX + "core"], stdout=subprocess.PIPE, universal_newlines=True)
    return [u"engine が封の後に変わっている: %s" % x for x in rc.stdout.splitlines() if x.strip()]


# ======================================================================== 2. 符号・類
def codes_problems(ms=None):
    ms = ms or MS
    out_ = []
    cases = [
        (u"[EDINET.EC5700W.GFM.1.1.3] 本文", [u"EDINET.EC5700W"]),
        (u"[info] 本文", []), (u"[] 本文", []), (u"本文 [EDINET.EC5700W] 途中", []), (u" [EDINET.EC5700W] 先頭に空白", []),
        (u"[xbrl.3.5.2.4:missingRoleRef] 本文", [u"xbrl.3.5.2.4:missingRoleRef"]),
        (u"[EDINET.EC0121E] a\n[info] b\n[EDINET.EC0121E.GFM.2] c\n[]\n[xbrl.1:x] d", [u"EDINET.EC0121E", u"EDINET.EC0121E", u"xbrl.1:x"]),
        (u"[EDINET.EC123W] 数字が 3 つ", [u"EDINET.EC123W"]), (u"[EDINET.EC12345E] 数字が 5 つ(形に当たらないのでそのまま)", [u"EDINET.EC12345E"]), (u"[EDINET.EC1234X] 末尾が E でも W でもない", [u"EDINET.EC1234X"]),
        (u"[EDINET.other.thing] EDINET の別の形", [u"EDINET.other.thing"]), (u"[info:x] 本文", [u"info:x"]), (u"[INFO] 本文", [u"INFO"]), (u"[nobracket", []), (u"", []),
        (u"[a][b] 2 つ目は数えない", [u"a"]),
        (u"[ EDINET.EC5700W ] 符号の前後の空白はそのまま", [u" EDINET.EC5700W "]), (u"[ info ] 空白つきは info ではない", [u" info "])]
    for text, want in cases:
        if ms.codes_of(text) != want:
            out_.append(u"codes_of(%r) が %r(手で決めた値は %r)" % (text[:40], ms.codes_of(text), want))
    for code, e, env, oth, edi in ((EC0121E, True, True, False, True), (EC1001E, True, False, True, True), (u"EDINET.EC5611W", False, False, False, True), (EC1057E, True, False, True, True),
                                   (u"EDINET.EC0100E", True, True, False, True), (u"EDINET.EC0100W", False, False, False, True), (u"xbrl.3.5.2.4:missingRoleRef", False, False, False, False),
                                   (u"EDINET.EC8054W", False, False, False, True), (u"EDINET.other.thing", False, False, False, True), (u"EDINET.EC01210E", False, False, False, True), (u"EDINET.EC1234E.GFM.E", False, False, False, True)):
        if (ms.is_e_code(code), ms.is_envelope(code), ms.is_other_e(code), ms.is_edinet(code)) != (e, env, oth, edi):
            out_.append(u"%s の E・包みの形・包みの形のほかの E・EDINET. が %s(手で決めた値は %s)" % (code, (ms.is_e_code(code), ms.is_envelope(code), ms.is_other_e(code), ms.is_edinet(code)), (e, env, oth, edi)))
    return out_


def class_problems(ms=None):
    ms = ms or MS
    out_ = []
    tb = u"Traceback (most recent call last):\nboom"
    for text, to, want in ((out([]), False, ms.CLS_RAN), (out([], act=False), False, ms.CLS_RAN), (out([], fmt=False), False, ms.CLS_RAN), (out([], act=False, fmt=False), False, ms.CLS_NOT_RUN),
                           (out([], tb=True), False, ms.CLS_STOPPED), (out([], act=False, fmt=False, tb=True), False, ms.CLS_STOPPED), (out([], act=False, tb=True), False, ms.CLS_STOPPED),
                           (tb, False, ms.CLS_STOPPED), (out([]), True, ms.CLS_STOPPED), (u"", True, ms.CLS_STOPPED), (u"", False, ms.CLS_NOT_RUN), (out(ln(EC0121E, 3)), False, ms.CLS_RAN)):
        if ms.run_class(text, to) != want:
            out_.append(u"run_class(%r, %s) が %s(手で決めた値は %s)" % (text[:30], to, ms.run_class(text, to), want))
    for key, (text, to) in sorted(FAKE_OUT.items()):
        c = ms.count_one(text, to)
        want = HAND_RUN[key]
        if (c[u"類"], c[u"時間の上限を超えた"], c[u"出力の行の数"], dict(c[u"符号ごとの行"])) != want:
            out_.append(u"count_one(%s) が手で数えた値と違う: %s" % (key, (c[u"類"], c[u"時間の上限を超えた"], c[u"出力の行の数"], dict(c[u"符号ごとの行"]))))
    c = ms.count_one(out(ln(EC5611W, 2), tb=True))
    if c[u"類"] != ms.CLS_STOPPED or c[u"符号ごとの行"] != {EC5611W: 2}:
        out_.append(u"止まった回の指摘を数えていない(止まるまでに出た分)")
    return out_


def totals_problems(ms=None):
    ms = ms or MS
    out_ = []
    runs = [[ms.count_one(*FAKE_OUT[(d, r)]) for d in (1, 2, 3)] for r in range(3)]
    for r in range(3):
        t = ms.run_totals(runs[r])
        h = HAND_TOTALS[r]
        got = (tuple(t[u"類別"].values()), t[u"時間の上限を超えた数"], dict((c, (v[u"書類"], v[u"行"])) for c, v in t[u"符号ごと"].items()), t[u"包みの形のほかの E が 1 行以上在る書類"],
               t[u"E の符号が 1 行も無い書類"], t[u"指摘の行が 1 行も無い書類"], tuple(t[u"鳴った符号の種類"].values()), t[u"34 本以上で鳴った符号の種類"], t[u"EC0121E か EC0130E が鳴る書類"])
        if got != h:
            out_.append(u"通り %d の合計が手で数えた値と違う: %s" % (r, got))
        if list(t[u"符号ごと"]) != sorted(t[u"符号ごと"]):
            out_.append(u"符号の並びが整っていない")
    # 34 本の境: 40 本のうち符号 A が 34 本・B が 33 本・C が 35 本で鳴る
    ents = []
    for i in range(40):
        codes = {}
        if i < 34:
            codes[EC5611W] = 1
        if i < 33:
            codes[EC8054W] = 2
        if i < 35:
            codes[EC0121E] = 1
        ents.append(ms.count_one(out(sum((ln(c, n) for c, n in codes.items()), [])), False))
    t = ms.run_totals(ents)
    if t[u"34 本以上で鳴った符号の種類"] != 2 or t[u"符号ごと"][EC5611W][u"書類"] != 34 or t[u"符号ごと"][EC8054W][u"書類"] != 33 or t[u"符号ごと"][EC8054W][u"行"] != 66:
        out_.append(u"34 本の境(33 と 34 と 35)が違う: %s" % t[u"34 本以上で鳴った符号の種類"])
    if t[u"指摘の行が 1 行も無い書類"] != 5 or t[u"E の符号が 1 行も無い書類"] != 5:
        out_.append(u"指摘の行が 1 行も無い書類・E の符号が 1 行も無い書類が違う")
    j = ms.judged(od(zip(ms.RUN_KEYS, [ms.run_totals(r) for r in runs])), 3)
    jv = list(j.values())
    got = [jv[0][u"書類"], jv[1][u"書類"], jv[2][u"書類"], jv[3][u"書類"], jv[4], (jv[5][u"2025"], jv[5][u"2026"], jv[5][u"差"]), jv[6][u"書類"], jv[7]]
    if got != HAND_JUDGED or jv[0][u"分母"] != 3:
        out_.append(u"予測の判定に要る数が手で数えた値と違う: %s" % got)
    return out_


# ======================================================================== 3. 道具の確かめ・掛ける
def tools_problems(ms=None):
    ms = ms or MS
    out_ = []
    wr, wp = hashlib.sha256(MV_R).hexdigest(), hashlib.sha256(MV_P).hexdigest()
    with Temp() as d:
        tr, tp, mvs = make_tools(d)
        r = FakeRunner(mvs)
        seen = []
        ir, ip = ms.check_tools(tr, tp, r, lambda path: (seen.append(path), hashlib.sha256(open(path, "rb").read()).hexdigest())[1], want_r=wr, want_p=wp)
        if len(seen) != 2 or any(not x.endswith("/ModelValue.py") for x in seen):
            out_.append(u"sha256 を読む file が ModelValue.py でない: %s" % seen)
        if (ir[u"版"], ir[u"ModelValue.py の sha256"], ip[u"ModelValue.py の sha256"], ir[u"Python の版"]) != (u"2.47.5", wr, wp, u"Python 3.11.17") or ir[u"package の一覧の sha256"] != hashlib.sha256(FREEZE.encode("utf-8")).hexdigest():
            out_.append(u"道具の情報が違う: %s" % dict(ir))
        if stops(ms, ms.check_tools, tr, tp, r, want_r=wr, want_p=wp, want_version=u"2.47.5") or not stops(ms, ms.check_tools, tr, tp, r, want_r=wr, want_p=wp, want_version=u"2.47.6"):
            out_.append(u"版が違うとき止まらない(か合うとき止まる)")
        if not stops(ms, ms.check_tools, tr, tp, FakeRunner(mvs, freeze=u"arelle-release==2.40.0\n"), want_r=wr, want_p=wp):
            out_.append(u"道具の版が 2.47.5 でないのに止まらない")
        if not stops(ms, ms.check_tools, tr, tp, FakeRunner(mvs, freeze=u"foo==1\narelle-cmdline==2.47.5\n"), want_r=wr, want_p=wp):
            out_.append(u"arelle-release の行が無いのに止まらない")
        if not stops(ms, ms.check_tools, tr, tp, r, want_r=wr, want_p=wr) or not stops(ms, ms.check_tools, tr, tp, r, want_r=wp, want_p=wp):
            out_.append(u"ModelValue.py の sha256 が R か P の字と違うのに止まらない(R と P の取り違えを含む)")
        if not stops(ms, ms.check_tools, tp, tr, r, want_r=wr, want_p=wp):
            out_.append(u"R と P の場所を入れ替えても止まらない")
        if not stops(ms, ms.check_tools, tr, tp, r):
            out_.append(u"封の sha256(既定)と違うのに止まらない")
        os.remove(os.path.join(tp, "bin", "arelleCmdLine"))
        if not stops(ms, ms.check_tools, tr, tp, r, want_r=wr, want_p=wp):
            out_.append(u"実行 file が無いのに止まらない")
        if not stops(ms, ms.check_tools, tr, os.path.join(d, "none"), r, want_r=wr, want_p=wp):
            out_.append(u"道具の場所が無いのに止まらない")
    cmd = ms.command(u"/t", u"EDINET-2026", u"/x/doc.zip")
    if cmd != [u"/t/bin/arelleCmdLine", u"--plugins", u"validate/EDINET|inlineXbrlDocumentSet", u"--disclosureSystem", u"EDINET-2026", u"-f", u"/x/doc.zip", u"--validate"]:
        out_.append(u"掛け方の引数の並びが封と違う: %s" % cmd)
    return out_


def exec_problems(ms=None):
    u"""``exec_cmd`` は shell を通さず・標準の出力と標準のエラーを 1 つにし・時間の上限を超えたら超えたと返す(``sys.executable`` で字を出すだけの短い呼び出し。道具は呼ばない)。"""
    ms = ms or MS
    out_ = []
    t, to = ms.exec_cmd([sys.executable, "-c", "import sys; print('[a] out'); print('[b] err', file=sys.stderr)"], 60)
    if to or u"[a] out" not in t or u"[b] err" not in t:
        out_.append(u"標準の出力と標準のエラーが 1 つになっていない: %r" % t)
    t, to = ms.exec_cmd([sys.executable, "-c", "import sys; print(sys.argv[1])", "a;echo shell $HOME"], 60)
    if to or t.strip() != u"a;echo shell $HOME":
        out_.append(u"shell を通している(引数がそのまま渡っていない): %r" % t)
    t, to = ms.exec_cmd([sys.executable, "-c", "import time, sys; print('[partial] x'); sys.stdout.flush(); time.sleep(8)"], 1)
    if not to or u"[partial] x" not in t:
        out_.append(u"時間の上限を超えたことと、超えるまでの出力を返していない: %r %r" % (to, t))
    t, to = ms.exec_cmd([sys.executable, "-c", "print('quick')"], 60)
    if to or t.strip() != u"quick":
        out_.append(u"短い呼び出しが超えた扱いになる")
    return out_


def run_problems(ms=None):
    ms = ms or MS
    out_ = []
    with Temp() as d:
        docs_before = None
        rec, secret, runner, tr, tp, docs, tmp = all_runs(d, ms)
        docs_before = dict((n, hashlib.sha256(open(os.path.join(docs, n), "rb").read()).hexdigest()) for n in sorted(os.listdir(docs)))
        # 順: 書類 1 の 3 通り → 書類 2 の 3 通り → 書類 3 の 3 通り(道具 R・2026 → P・2026 → P・2025)。1 回ずつ。時間の上限は 600 秒
        if [(c["doc"], c["run"]) for c in runner.calls] != [(n, r) for n in (1, 2, 3) for r in (0, 1, 2)]:
            out_.append(u"掛ける順が違う: %s" % [(c["doc"], c["run"]) for c in runner.calls])
        if any(c["timeout"] != 600 for c in runner.calls) or any(not c["existed"] for c in runner.calls):
            out_.append(u"時間の上限が 600 秒でない・写しが無い")
        if any(any(n.endswith(".xbrl") for n in c["names"]) for c in runner.calls) or any(len([n for n in c["names"] if n.endswith(".htm")]) != 1 or u"XBRL/AuditDoc/audit.xml" not in c["names"] for c in runner.calls):
            out_.append(u"写しの中身が違う(.xbrl が残っているか、ほかの file が消えている)")
        if any(os.path.exists(p) for p in runner.paths) or os.listdir(tmp):
            out_.append(u"使い捨ての写しが消えていない")
        if any(c["cmd"][0] != os.path.join(tr if c["run"] == 0 else tp, "bin", "arelleCmdLine") for c in runner.calls):
            out_.append(u"R・P の道具の選びが違う")
        if len(runner.calls) != 9 or len(set(os.path.dirname(p) for p in runner.paths)) != 3:
            out_.append(u"呼び出しが 9 回でない")
        if any(zipfile.ZipFile(os.path.join(docs, n)).namelist().count("XBRL/PublicDoc/api_added_E9999%s-000.xbrl" % n[-5]) != 1 for n in STEMS_ZIPS()):
            out_.append(u"置き場の zip の .xbrl が消えている(置き場を変えた)")
        for i, n in enumerate(STEMS_ZIPS(), 1):
            if hashlib.sha256(open(os.path.join(docs, n), "rb").read()).hexdigest() != docs_before[n]:
                out_.append(u"置き場の zip が変わった")
        mat = rec[u"材料"]
        if (mat[u"書類の本数"], mat[u"書類の file 名の並びの sha256"], mat[u"道具の版"], mat[u"道具 R の ModelValue.py の sha256"], mat[u"道具 P の ModelValue.py の sha256"], mat[u"Python の版(道具 R)"],
                mat[u"3 通り"], mat[u"時間の上限(秒)"], mat[u"道具 R の package の一覧の sha256"]) != (3, ORDER_SHA, u"2.47.5", hashlib.sha256(MV_R).hexdigest(), hashlib.sha256(MV_P).hexdigest(), u"Python 3.11.17",
                                                                                      list(ms.RUN_KEYS), 600, hashlib.sha256(FREEZE.encode("utf-8")).hexdigest()):
            out_.append(u"材料の欄が手で数えた値と違う: %s" % dict(mat))
        for i in (1, 2, 3):
            d_ = rec[u"書類"][i - 1]
            if d_[u"番号"] != i:
                out_.append(u"書類の番号が違う")
            for r, k in enumerate(ms.RUN_KEYS):
                e = d_[k]
                if (e[u"類"], e[u"時間の上限を超えた"], e[u"出力の行の数"], dict(e[u"符号ごとの行"])) != HAND_RUN[(i, r)]:
                    out_.append(u"書類 %d の %s が手で数えた値と違う: %s" % (i, k, dict(e)))
        for r, k in enumerate(ms.RUN_KEYS):
            t = rec[u"集計"][k]
            if (tuple(t[u"類別"].values()), t[u"時間の上限を超えた数"]) != (HAND_TOTALS[r][0], HAND_TOTALS[r][1]):
                out_.append(u"集計 %s が手で数えた値と違う" % k)
        text = dumps_(ms, rec)
        for leak in STEMS + [u"E9999", u"S2OTHER1", u"本文の字", u".xbrl", u".htm", u"audit", u"途中の出力"]:
            if leak in text:
                out_.append(u"記録に材料の字が在る: %s" % leak)
        if set(secret[3]) != set([u"E9999%d" % i for i in (1, 2, 3)]) or list(secret[2]) != STEMS or not any(u"本文の字" in x for x in secret[4]):
            out_.append(u"secret の docID・EDINET コード・出力の行が違う")
        # 67 本でない置き場・道具の確かめの失敗では 1 回も掛けない
        runner2 = FakeRunner([os.path.join(d, "tools", "tool_r", "ModelValue.py"), os.path.join(d, "tools", "tool_p", "ModelValue.py")])
        if not stops(ms, ms.build_record, tr, tp, docs, runner=runner2, tmp_root=tmp) or runner2.calls:
            out_.append(u"書類が 67 本でないのに止まらない(か掛けた)")
        runner3 = FakeRunner(runner2.mvs)
        if not stops(ms, ms.build_record, tr, tp, docs, want=3, runner=runner3, tmp_root=tmp) or runner3.calls:
            out_.append(u"道具の sha256 が封と違うのに止まらない(か掛けた)")
        # 掛けている途中の失敗でも写しは消える
        class Boom(FakeRunner):
            def __call__(self, cmd, timeout):
                if os.path.basename(cmd[0]) == "arelleCmdLine" and len(self.calls) == 2:
                    self.calls.append(1)
                    raise RuntimeError("boom")
                return FakeRunner.__call__(self, cmd, timeout)
        runner4 = Boom(runner2.mvs)
        try:
            ms.build_record(tr, tp, docs, want=3, runner=runner4, tmp_root=tmp, want_r=hashlib.sha256(MV_R).hexdigest(), want_p=hashlib.sha256(MV_P).hexdigest())
        except RuntimeError:
            pass
        if os.listdir(tmp):
            out_.append(u"途中で落ちたとき使い捨ての写しが残る")
    return out_


def STEMS_ZIPS():
    return [s + ".zip" for s in STEMS]


def dumps_(ms, rec):
    return ms.dumps(rec)


# ======================================================================== 4. 記録
def verify_problems(ms=None):
    ms = ms or MS
    out_ = []
    with Temp() as d:
        rec, secret, runner, tr, tp, docs, tmp = all_runs(d, ms)
        p = os.path.join(d, "r.json")
        ms.write_record(p, rec, secret)
        if stops(ms, ms.check, rec_path=p, want=3, say=lambda *a: None):
            out_.append(u"きれいな記録で --check が止まる")
        if not stops(ms, ms.check, rec_path=p, say=lambda *a: None):
            out_.append(u"書類が 67 本でない記録で --check が止まらない")
        if not stops(ms, ms.check, rec_path=os.path.join(d, "none.json"), want=3, say=lambda *a: None):
            out_.append(u"記録が無いのに --check が止まらない")
        base = ms.dumps(rec)
        text = io.open(p, encoding="utf-8").read()
        if text != base:
            out_.append(u"書いた字が dumps と違う")
        run_key = ms.RUN_KEYS[1]
        def refresh_after(fn):
            def go(r):
                fn(r)
                r[u"集計"] = od((k, ms.run_totals([x[k] for x in r[u"書類"]])) for k in ms.RUN_KEYS)
                r[[k for k in r if k.startswith(u"予測の判定に要る数")][0]] = ms.judged(r[u"集計"], len(r[u"書類"]))
            return go
        tampers = [
            (u"集計の数を変える", lambda r: r[u"集計"][run_key][u"類別"].__setitem__(u"走った", 99)),
            (u"書類ごとの類を変える(合計と合わない)", lambda r: r[u"書類"][0][ms.RUN_KEYS[2]].__setitem__(u"類", u"止まった")),
            (u"書類ごとの符号の行を変える", lambda r: r[u"書類"][0][run_key][u"符号ごとの行"].__setitem__(EC5611W, 9)),
            (u"書類を 1 本消す", lambda r: r[u"書類"].pop()),
            (u"3 通りの 1 つが無い", lambda r: r[u"書類"][1].pop(ms.RUN_KEYS[2])),
            (u"類の字が違う", lambda r: r[u"書類"][0][run_key].__setitem__(u"類", u"壊れた")),
            (u"時間の上限を超えたのに「走った」", lambda r: r[u"書類"][0][run_key].__setitem__(u"時間の上限を超えた", True)),
            (u"判定の数を変える", lambda r: [r[k] for k in r if k.startswith(u"予測の判定に要る数")][0][u"XV0-5 道具 P・2026: 鳴った EDINET. の符号の種類"].__class__),
            (u"書類の番号を変える", lambda r: r[u"書類"][0].__setitem__(u"番号", 7)),
            (u"出力の行の数を指摘の行の数より少なくする", lambda r: r[u"書類"][0][run_key].__setitem__(u"出力の行の数", 1)),
            (u"出力の行の数の欄を消す", lambda r: r[u"書類"][0][run_key].pop(u"出力の行の数")),
            (u"出力の行の数が整数でない", lambda r: r[u"書類"][0][run_key].__setitem__(u"出力の行の数", u"13")),
            (u"材料の書類の本数だけを変える", lambda r: r[u"材料"].__setitem__(u"書類の本数", 5)),
            (u"時間の上限を超えたのに「走った」(集計も判定も合わせ直す)", refresh_after(lambda r: r[u"書類"][0][ms.RUN_KEYS[2]].__setitem__(u"時間の上限を超えた", True)))]
        for what, fn in tampers:
            r2 = json.loads(base, object_pairs_hook=od)
            fn(r2)
            if what == u"判定の数を変える":
                key = [k for k in r2 if k.startswith(u"予測の判定に要る数")][0]
                r2[key][u"XV0-5 道具 P・2026: 鳴った EDINET. の符号の種類"] = 99
            if ms.dumps(r2) == base or not stops(ms, ms.verify_record, r2, None, 3):
                out_.append(u"記録を変えても検査が止まらない: %s" % what)
        # 本物の合計の形: 67 本の記録(作り物の 3 本を 67 本に増やす)は 67 のとき通る
        r67 = json.loads(base, object_pairs_hook=od)
        r67[u"書類"] = [od([(u"番号", i)] + [(k, r67[u"書類"][0][k]) for k in ms.RUN_KEYS]) for i in range(1, 68)]
        r67[u"材料"][u"書類の本数"] = 67
        r67[u"集計"] = od((k, ms.run_totals([x[k] for x in r67[u"書類"]])) for k in ms.RUN_KEYS)
        r67[[k for k in r67 if k.startswith(u"予測の判定に要る数")][0]] = ms.judged(r67[u"集計"], 67)
        if stops(ms, ms.verify_record, r67, None, 67) or not stops(ms, ms.verify_record, r67, None, 3):
            out_.append(u"67 本の記録の検査が違う(67 で通り、3 では止まる)")
    return out_


def clean_problems(ms=None):
    ms = ms or MS
    out_ = []
    ok = od([(u"書類", [od([(u"番号", 1), (u"符号ごとの行", od([(u"EDINET.EC5611W", 3), (u"xbrl.3.5.2.4:missingRoleRef", 1)])), (u"材料の sha256", u"a" * 64)])])])
    secret = (set(), set(), [u"zzdoc"], {u"E99991"}, {u"[EDINET.EC5611W] ある指摘の行の本文"})
    if stops(ms, ms.check_clean, ok, ms.dumps(ok), secret):
        out_.append(u"符号を欄に持つきれいな記録で止まる")
    cases = [
        (u"禁止の欄(docid)", od([(u"DocID", 1)])), (u"禁止の欄(company)", od([(u"company", 1)])), (u"禁止の欄(label)", od([(u"label", 1)])), (u"禁止の欄(会社の名)", od([(u"会社の名", 1)])),
        (u"EDINET コードの形", od([(u"x", u"id E12345 x")])), (u"docID の形", od([(u"x", u"S100ABCD")])),
        (u"材料の docID", od([(u"x", u"id zzdoc.")])), (u"材料の EDINET コード", od([(u"x", u"E99991")])),
        (u"file の名(xsd)", od([(u"x", u"jpcrp030000-asr-001.xsd")])), (u"file の名(zip)", od([(u"x", u"a.zip")])), (u"file の名(PublicDoc)", od([(u"x", u"XBRL/PublicDoc/x")])),
        (u"指摘の行の本文", od([(u"x", u"文 [EDINET.EC5611W] ある指摘の行の本文 文")]))]
    for what, rec in cases:
        if not stops(ms, ms.check_clean, rec, ms.dumps(rec), secret):
            out_.append(u"%s が止まらない" % what)
        if not stops(ms, ms.record_text, rec, secret):
            out_.append(u"%s が record_text で止まらない" % what)
    with Temp() as d:
        p = os.path.join(d, "r.json")
        bad = od([(u"x", u"E12345")])
        if not stops(ms, ms.write_record, p, bad) or os.path.exists(p):
            out_.append(u"禁止の字が在る記録を書いた(書く前の検査)")
        good = od([(u"x", 1)])
        ms.write_record(p, good)
        if not stops(ms, ms.write_record, p, good):
            out_.append(u"記録が既に在るのに書き直せる")
        orig = ms.write_exclusive
        q = os.path.join(d, "q.json")
        ms.write_exclusive = lambda path, data: orig(path, data + b" E12345")
        try:
            stopped = stops(ms, ms.write_record, q, good)
        finally:
            ms.write_exclusive = orig
        if not stopped or os.path.exists(q):
            out_.append(u"書いた後の検査が止めない(か file を消さない)")
        w = os.path.join(d, "w.json")
        ms.write_exclusive = lambda path, data: orig(path, b"{}")
        try:
            stopped = stops(ms, ms.write_record, w, bad)
        finally:
            ms.write_exclusive = orig
        if not stopped:
            out_.append(u"書く前の検査が止めない(書いた後の検査だけで止まっている)")
    return out_


def e2e_problems(ms=None):
    u"""``run`` → 記録 → ``--check`` を作り物の置き場と道具で通す(置き場も道具も開かない)。"""
    ms = load_source(read(SCRIPT_REL)) if ms is None or ms is MS else ms
    out_ = []
    with Temp() as d:
        docs = os.path.join(d, "docs")
        os.makedirs(docs)
        make_docs(docs)
        tr, tp, mvs = make_tools(os.path.join(d, "tools"))
        tmp = os.path.join(d, "tmp")
        os.makedirs(tmp)
        rp = os.path.join(d, "rec", "r.json")
        kw = dict(docs=docs, out=rp, runner=FakeRunner(mvs), tmp_root=tmp, say=lambda *a: None, want_r=hashlib.sha256(MV_R).hexdigest(), want_p=hashlib.sha256(MV_P).hexdigest())
        if not stops(ms, ms.run, tr, tp, **kw) or os.path.exists(rp):
            out_.append(u"書類が 67 本でないのに run が止まらない(か記録を書いた)")
        kw["runner"] = FakeRunner(mvs)
        rec = ms.run(tr, tp, want=3, **kw)
        if not os.path.exists(rp) or ms.dumps(rec) != io.open(rp, encoding="utf-8").read():
            out_.append(u"記録が書かれていない・字が違う")
        if not stops(ms, ms.run, tr, tp, want=3, **kw):
            out_.append(u"記録が既に在るのに run が止まらない")
        ms.check(rec_path=rp, want=3, say=lambda *a: None)
        # 道具の確かめに通らないときは記録を書かない
        rp2 = os.path.join(d, "rec", "r2.json")
        kw2 = dict(kw, out=rp2, runner=FakeRunner(mvs), want_r=u"0" * 64)
        if not stops(ms, ms.run, tr, tp, want=3, **kw2) or os.path.exists(rp2):
            out_.append(u"道具の sha256 が違うのに記録を書いた")
    return out_


# ======================================================================== 5. 配線
STDLIB_OK = ("__future__", "argparse", "collections", "hashlib", "importlib", "io", "json", "os", "re", "shutil", "subprocess", "sys", "tempfile", "zipfile")
NETWORK_MODULES = ("http", "socket", "ssl", "urllib", "requests", "ftplib", "smtplib", "xmlrpc", "telnetlib", "asyncio", "aiohttp", "httpx", "adapters", "core", "audit_core")
WALL_CALLED = ("select_docs", "order_sha256", "check_clean", "Stop", "sha256_file", "sha256_bytes", "dumps")
WALL_NOT_COPIED = ("select_docs", "order_sha256", "doc_xsd_names", "sha256_file")
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS")


def import_problems(src=None):
    u"""script の import は標準ライブラリと importlib だけ(engine を読まない)。前の便の script は ``W.`` から呼び写さない。subprocess は shell を通さない(``shell=False`` と引数の並び)。"""
    src = src if src is not None else read(SCRIPT_REL)
    tree = ast.parse(src)
    out_ = []
    for n in ast.walk(tree):
        names = []
        if isinstance(n, ast.Import):
            names = [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            names = [(n.module or u"")]
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("__import__", "eval", "exec"):
            out_.append(u"動的な import・eval・exec の呼び出し")
        for nm in names:
            top = nm.split(".")[0]
            if top in NETWORK_MODULES:
                out_.append(u"許さない module を import している: %s" % nm)
            elif top not in STDLIB_OK:
                out_.append(u"許す一覧に無い module: %s" % nm)
    attrs = [(n.value.id, n.attr) for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)]
    if ("os", "environ") in attrs or ("os", "getenv") in attrs or ("os", "system") in attrs or ("os", "popen") in attrs:
        out_.append(u"環境変数・shell を読んで/呼んでいる")
    for fn in WALL_CALLED:
        if ("W", fn) not in attrs:
            out_.append(u"便 XG0 の %s を W から呼んでいない" % fn)
    funcs = set(n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    for fn in WALL_NOT_COPIED:
        if fn in funcs:
            out_.append(u"便 XG0 の %s を script が自分で定義している(写している)" % fn)
    runs = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id == "subprocess" and n.func.attr == "run"]
    if len(runs) != 1:
        out_.append(u"subprocess.run が 1 か所でない")
    for c in runs:
        kws = dict((k.arg, k.value) for k in c.keywords)
        if not (isinstance(kws.get("shell"), ast.Constant) and kws["shell"].value is False) or "timeout" not in kws or not isinstance(c.args[0], ast.Call):
            out_.append(u"subprocess.run が shell=False・timeout・引数の並び(list(...))でない")
    if any(isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "subprocess" and n.attr in ("Popen", "call", "check_output", "check_call", "getoutput") for n in ast.walk(tree)):
        out_.append(u"subprocess.run のほかの呼び方を使っている")
    consts = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    if WALL_NAME not in consts:
        out_.append(u"前の便の script を読む名が一意の名(%s)でない" % WALL_NAME)
    doc = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant):
            doc.add(id(n.body[0].value))
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc:
            if u".env" in n.value or u"dotenv" in n.value or u"API_KEY" in n.value:
                out_.append(u"鍵・.env の字が在る")
            if OTHER_SCRIPT_NAME in n.value:
                out_.append(u"便 XG1 の script の名が在る(互いに読まない)")
    return out_


def reserved_problems(rel=GATE_REL, base=ROOT):
    out_ = []
    with open(os.path.join(base, rel), encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    for n, line in enumerate(lines, 1):
        if any(line.startswith(p) for p in RESERVED_PREFIXES):
            out_.append(u"%s:%d" % (rel, n))
    return out_


# ======================================================================== 変異
#: (名前, 置き換え前(script の中でちょうど 1 回)・置き換え後・赤になるべき検査の名前)。**予測は「その検査が赤になる」。** この表は実行より先に書いた。
MUTANTS = (
    # ---- 符号の切り方
    (u"V1 info を数える", u"        if not code or code == INFO_CODE:", u"        if not code:", ("codes", "class", "totals")),
    (u"V2 空の [] を数える", u"        if not code or code == INFO_CODE:", u"        if code == INFO_CODE:", ("codes",)),
    (u"V3 行の途中の [ も指摘の行に数える", u'        if not line.startswith("["):\n            continue\n        end = line.find("]")', u'        if "[" not in line:\n            continue\n        end = line.find("]", line.find("["))\n        line = line[line.find("["):]', ("codes",)),
    (u"V4 EDINET. の符号の後ろ(.GFM...)を落とさない", u"            if m:\n                code = m.group(0)", u"            if False:\n                code = m.group(0)", ("codes", "class")),
    (u"V5 符号の前後の空白を落とす(strip)", u"        code = line[1:end]\n", u"        code = line[1:end].strip()\n        line = line.strip()\n", ("codes",)),
    (u"V6 EDINET の符号の数字を 3 つまでにする", u'EDINET_CODE_RE = re.compile(r"^EDINET\\.EC\\d{4}[EW]")', u'EDINET_CODE_RE = re.compile(r"^EDINET\\.EC\\d{3}[EW]")', ("seal", "codes")),
    (u"V7 EDINET の符号が W 以外を落とす", u'EDINET_CODE_RE = re.compile(r"^EDINET\\.EC\\d{4}[EW]")', u'EDINET_CODE_RE = re.compile(r"^EDINET\\.EC\\d{4}[E]")', ("seal", "codes")),
    (u"V8 最初の ] でなく最後の ] までを符号にする", u'        end = line.find("]")', u'        end = line.rfind("]")', ("codes",)),
    # ---- E・包みの形
    (u"V9 包みの形を数字の頭が 1 にする", u'ENVELOPE_DIGIT = "0"', u'ENVELOPE_DIGIT = "1"', ("seal", "codes", "totals")),
    (u"V10 E の符号に W も入れる", u'    return bool(m) and m.group(0) == code and code.endswith("E")', u"    return bool(m) and m.group(0) == code", ("codes", "totals")),
    (u"V11 包みの形のほかの E が包みの形も含む", u"    return is_e_code(code) and not is_envelope(code)", u"    return is_e_code(code)", ("codes", "totals")),
    (u"V12 E の符号の判定が接頭辞の一致だけ(余分な字を許す)", u"    return bool(m) and m.group(0) == code and code.endswith(\"E\")", u"    return bool(m) and code.endswith(\"E\")", ("codes",)),
    # ---- 1 回の類
    (u"V13 時間の上限を超えた回を止まったにしない", u"    if timed_out or TRACEBACK in text:", u"    if TRACEBACK in text:", ("class", "totals", "run")),
    (u"V14 Traceback で止まったにしない", u"    if timed_out or TRACEBACK in text:", u"    if timed_out:", ("class",)),
    (u"V15 「両方が無い」を「どちらかが無い」にする(and → or。封の字から離れる向き)", u"    if MARK_ACTIVATION not in text and MARK_FORMAT not in text:", u"    if MARK_ACTIVATION not in text or MARK_FORMAT not in text:", ("class",)),
    (u"V16 走らなかったの判定を Traceback より先にする", u"    if timed_out or TRACEBACK in text:\n        return CLS_STOPPED\n    if MARK_ACTIVATION not in text and MARK_FORMAT not in text:\n        return CLS_NOT_RUN\n",
     u"    if MARK_ACTIVATION not in text and MARK_FORMAT not in text:\n        return CLS_NOT_RUN\n    if timed_out or TRACEBACK in text:\n        return CLS_STOPPED\n", ("class", "totals")),
    (u"V17 止まった回の指摘を数えない", u"    cnt = collections.Counter(codes_of(text))", u"    cnt = collections.Counter(codes_of(text) if run_class(text, timed_out) != CLS_STOPPED else [])", ("class", "totals", "run")),
    (u"V18 走らなかった回の指摘を数えない", u"    cnt = collections.Counter(codes_of(text))", u"    cnt = collections.Counter(codes_of(text) if run_class(text, timed_out) == CLS_RAN else [])", ("class", "totals")),
    # ---- 数え方
    (u"V19 34 本以上を 33 本以上にする", u"BIG_DOCS = 34", u"BIG_DOCS = 33", ("seal", "totals")),
    (u"V20 34 本以上を「より多い」にする", u"if docs_by[c] >= BIG_DOCS)", u"if docs_by[c] > BIG_DOCS)", ("totals",)),
    (u"V21 包みの形のほかの E の書類を E の符号全部で数える", u"        if any(is_other_e(c) for c in codes):", u"        if any(is_e_code(c) for c in codes):", ("totals",)),
    (u"V22 E の符号が 1 行も無い書類を指摘が無い書類で数える", u"        if not any(is_e_code(c) for c in codes):", u"        if not codes:", ("totals",)),
    (u"V23 時間の上限を超えた数を数えない", u'        if e[u"時間の上限を超えた"]:\n            timeouts += 1', u'        if False:\n            timeouts += 1', ("totals", "run")),
    (u"V24 EC0121E か EC0130E の片方だけ数える", u"        if any(c in codes for c in ENVELOPE_PAIR):", u"        if ENVELOPE_PAIR[0] in codes:", ("totals",)),
    (u"V25 符号の行の数を書類の数にする", u"            lines_by[c] += n", u"            lines_by[c] += 1", ("totals",)),
    (u"V26 XV0-6 の差の向きを逆にする", u'(u"差", p25[u"包みの形のほかの E が 1 行以上在る書類"] - p26[u"包みの形のほかの E が 1 行以上在る書類"])', u'(u"差", p26[u"包みの形のほかの E が 1 行以上在る書類"] - p25[u"包みの形のほかの E が 1 行以上在る書類"])', ("totals",)),
    (u"V27 XV0-2 を止まったの数だけにする", u'p26[u"類別"][CLS_STOPPED] + p26[u"類別"][CLS_NOT_RUN]', u'p26[u"類別"][CLS_STOPPED]', ("totals",)),
    # ---- 道具の確かめ・掛け方
    (u"V28 版の照合を外す", u"    if info_r[u\"版\"] != want_version or info_p[u\"版\"] != want_version:", u"    if False:", ("tools",)),
    (u"V29 道具 R の sha256 の照合を外す", u'    if info_r[u"ModelValue.py の sha256"] != want_r:', u"    if False:", ("tools",)),
    (u"V30 道具 P の sha256 の照合を外す", u'    if info_p[u"ModelValue.py の sha256"] != want_p:', u"    if False:", ("tools",)),
    (u"V31 R と P の sha256 を取り違える", u'    if info_r[u"ModelValue.py の sha256"] != want_r:', u'    if info_r[u"ModelValue.py の sha256"] != want_p:', ("tools",)),
    (u"V32 実行 file の在るかの確かめを外す", u"        if not os.path.isfile(os.path.join(t, EXE_REL)):", u"        if False:", ("tools",)),
    (u"V33 sha256 の封の字を 1 字替える", u'SHA_P = "fd9b0d08', u'SHA_P = "ed9b0d08', ("seal",)),
    (u"V34 掛け方の引数の --validate を落とす", u'"-f", zip_path, "--validate"]', u'"-f", zip_path]', ("tools",)),
    (u"V35 規則の年の引数の位置を替える(--disclosureSystem の後に年が来ない)", u'"--disclosureSystem", year, "-f"', u'"--disclosureSystem", "-f", year', ("tools", "run")),
    (u"V36 3 通りの順を入れ替える", u'RUNS = (("R", "EDINET-2026"), ("P", "EDINET-2026"), ("P", "EDINET-2025"))', u'RUNS = (("P", "EDINET-2026"), ("R", "EDINET-2026"), ("P", "EDINET-2025"))', ("seal", "run")),
    (u"V37 3 通りの 3 つ目を道具 R にする", u'("P", "EDINET-2026"), ("P", "EDINET-2025"))', u'("P", "EDINET-2026"), ("R", "EDINET-2025"))', ("seal", "run")),
    (u"V38 時間の上限を 60 秒にする", u"TIMEOUT_SEC = 600", u"TIMEOUT_SEC = 60", ("seal", "run")),
    (u"V39 .xbrl を除かない", u"            if not info.filename.endswith(STRIP_SUFFIX):", u"            if True:", ("run",)),
    (u"V40 除く file の名の字を替える(.xml を除く)", u'STRIP_SUFFIX = ".xbrl"', u'STRIP_SUFFIX = ".xml"', ("seal", "run")),
    (u"V41 使い捨ての写しを消さない", u"        shutil.rmtree(d, ignore_errors=True)", u"        pass", ("run",)),
    (u"V42 使い捨ての写しを try の外で消す(途中で落ちると残る)", u"    finally:\n        shutil.rmtree(d, ignore_errors=True)", u"    finally:\n        pass\n", ("run",)),
    (u"V43 shell を通す", u"shell=False)", u"shell=True)", ("exec", "wiring")),
    (u"V44 標準のエラーを合流させない", u"stderr=subprocess.STDOUT", u"stderr=subprocess.DEVNULL", ("exec",)),
    (u"V45 時間の上限を渡さない", u"timeout=timeout, shell=False", u"timeout=None, shell=False", ("exec",)),
    (u"V46 時間の上限を超えたときの出力を捨てる", u'        return (exc.output or b"").decode("utf-8", "replace"), True', u'        return u"", True', ("exec",)),
    (u"V47 時間の上限を超えたことを返さない", u'        return (exc.output or b"").decode("utf-8", "replace"), True', u'        return (exc.output or b"").decode("utf-8", "replace"), False', ("exec",)),
    (u"V48 書類を 1 本ずつでなく道具ごとにまとめて回す(写しを使い回す)", u"        out = []\n        for t, year in RUNS:", u"        out = []\n        for t, year in sorted(RUNS):", ("run",)),
    (u"V49 前の便の script を他と重なる名で読む", u'    name = "_xv0_tag_wall_2026_11_21"', u'    name = "_xg1_tag_wall_2026_11_21"', ("wiring",)),
    (u"V50 engine を読む", u"import zipfile\n\nHERE", u"import zipfile\nfrom adapters.xbrl import instance as I\n\nHERE", ("wiring",)),
    # ---- 記録の検査
    (u"V51 file の名の形の検査を外す", u"    if FILE_FORM_RE.search(scan):", u"    if False:", ("clean",)),
    (u"V52 指摘の行の本文の検査を外す", u"            if len(line) >= BODY_MIN and line in scan:", u"            if False:", ("clean",)),
    (u"V53 便 XG0 の検査(欄・形・docID)を呼ばない", u"    W.check_clean(rec, text, secret[:4] if secret else None)", u"    pass", ("clean",)),
    (u"V54 書いた後の検査を外す", u"        check_clean(rec, back, secret)\n    except SystemExit:", u"        pass\n    except SystemExit:", ("clean",)),
    (u"V55 書く前の検査を外す", u"    text = record_text(rec, secret)\n    os.makedirs", u"    text = dumps(rec)\n    os.makedirs", ("clean",)),
    (u"V56 --check が合計を照らさない", u'    if dumps(totals) != dumps(rec[u"集計"]) or', u'    if False or', ("verify",)),
    (u"V57 --check が判定の数を照らさない", u'or dumps(judged(totals, len(docs))) != dumps(rec[[k for k in rec if k.startswith(u"予測の判定に要る数")][0]]):', u":", ("verify",)),
    (u"V58 --check が書類の本数を問わない", u"len(docs) != want or rec[u\"材料\"][u\"書類の本数\"] != want:", u"False:", ("verify",)),
    (u"V59 --check が時間の上限と類の食い違いを見ない", u'            if e[u"時間の上限を超えた"] and e[u"類"] != CLS_STOPPED:', u"            if False:", ("verify",)),
    (u"V60 --check が 3 通りの形を見ない", u"        if d.get(u\"番号\") != i or any(k not in d for k in RUN_KEYS):", u"        if False:", ("verify",)),
    (u"V65 XV0-5 が 2026 でなく 2025 の種類を読む", u'(u"XV0-5 道具 P・2026: 鳴った EDINET. の符号の種類", p26[u"鳴った符号の種類"][u"EDINET. の符号"])', u'(u"XV0-5 道具 P・2026: 鳴った EDINET. の符号の種類", p25[u"鳴った符号の種類"][u"EDINET. の符号"])', ("totals",)),
    (u"V66 ModelValue.py でない file の sha256 を読む", u"os.path.dirname(arelle.__file__), 'ModelValue.py'", u"os.path.dirname(arelle.__file__), 'ModelValue2.py'", ("tools",)),
    (u"V67 版の字を arelle で始まる行の全部から読む", u'r"^arelle-release==(\S+)\s*$"', u'r"^arelle\S*==(\S+)\s*$"', ("tools",)),
    (u"V68 出力の行の数を字の数にする", u'(u"出力の行の数", len(text.splitlines()))', u'(u"出力の行の数", len(text))', ("class", "run")),
    (u"V69 出力の行の数の欄を持たない", u'(u"出力の行の数", len(text.splitlines())), ', u"", ("class", "run", "verify")),
    (u"V70 --check が出力の行の数を見ない", u'            if not isinstance(nl, int) or isinstance(nl, bool) or nl < sum(e[u"符号ごとの行"].values()):', u"            if False:", ("verify",)),
    (u"V71 --check が出力の行の数と指摘の行の数の前後を見ない", u"or nl < sum(e[u\"符号ごとの行\"].values()):", u":", ("verify",)),
    (u"V61 出力の行の本文を集めない", u"            if sink is not None:\n                sink.update", u"            if False:\n                sink.update", ("run",)),
    (u"V62 EDINET コードを secret に集めない", u'            ecodes.update(re.findall(r"E\\d{5}", x))', u"            pass", ("run",)),
    (u"V63 道具の確かめの前に掛ける(確かめを飛ばす)", u"    info_r, info_p = check_tools(tool_r, tool_p, runner, sha_reader, want_version, want_r, want_p)\n    tool_dirs", u"    info_r = info_p = od([(u\"版\", u\"\"), (u\"ModelValue.py の sha256\", u\"\"), (u\"package の一覧の sha256\", u\"\"), (u\"Python の版\", u\"\")])\n    tool_dirs", ("run", "e2e")),
)
#: 黙ることが分かっている変異(理由つき)
SILENT_BY_DESIGN = ()


def check_by_name(name, mod, src):
    table = {u"seal": seal_problems, u"codes": codes_problems, u"class": class_problems, u"totals": totals_problems, u"tools": tools_problems, u"exec": exec_problems, u"run": run_problems,
             u"verify": verify_problems, u"clean": clean_problems, u"e2e": e2e_problems}
    if name in table:
        return table[name](mod)
    if name == u"wiring":
        return import_problems(src)
    raise AssertionError(name)


ALL_CHECKS = (u"seal", u"codes", u"class", u"totals", u"tools", u"exec", u"run", u"verify", u"clean", u"e2e", u"wiring")


def run_mutants(table=MUTANTS):
    base = read(SCRIPT_REL)
    out_ = []
    for name, old, new, checks in table:
        assert base.count(old) == 1, (name, base.count(old))
        src = base.replace(old, new)
        try:
            mod = load_source(src)
        except BaseException as exc:                # noqa: BLE001
            out_.append((name, [(c, True) for c in checks], u"読めない: %s" % type(exc).__name__))
            continue
        res = [(c, bool(guard(check_by_name, c, mod, src))) for c in checks]
        out_.append((name, res, u""))
    return out_


# ======================================================================== 試験
class SealTextTest(unittest.TestCase):
    def test_a_1_the_script_constants_equal_the_seal(self):
        self.assertEqual([], seal_problems())

    def test_a_2_the_seal_file_is_the_sealed_commit_and_unchanged(self):
        self.assertEqual([], seal_history_problems())

    def test_a_3_a_changed_seal_character_turns_the_comparison_red(self):
        seal = seal_text()
        for old, new in ((u"版の字が `2.47.5`", u"版の字が `2.47.6`"), (SEAL_SHA_R, SEAL_SHA_R[:-1] + u"1"), (u"34 本以上で鳴った符号の種類の数", u"33 本以上で鳴った符号の種類の数"),
                         (u"| XV0-3(主) | 道具 P・2026: 包みの形のほかの E が 1 行以上在る書類は 33 本以下", u"| XV0-3(主) | 道具 P・2026: 包みの形のほかの E が 1 行以上在る書類は 34 本以下"),
                         (u"`Traceback` の字が在れば **止まった**", u"`Traceback` の字が在れば **走った**"), (u"数字の頭が `0` のもの(`EC0xxxE`)", u"数字の頭が `1` のもの(`EC0xxxE`)"),
                         (u"道具 R × `EDINET-2026`・道具 P × `EDINET-2026`・道具 P × `EDINET-2025` の 3 通り", u"道具 R × `EDINET-2026`・道具 P × `EDINET-2025`・道具 P × `EDINET-2026` の 3 通り"),
                         (u"符号 `info` は数えない", u"符号 `debug` は数えない")):
            self.assertEqual(1, seal.count(old), old)
            self.assertNotEqual([], seal_problems(seal=seal.replace(old, new)), old)

    def test_a_4_engine_is_zero_lines_from_the_seal_commit(self):
        self.assertEqual([], engine_zero_problems())

    def test_a_5_the_boundary_import_list_is_not_widened(self):
        p = os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py")
        with io.open(p, encoding="utf-8") as fh:
            body = fh.read()
        self.assertNotIn(u"edinet_validate", body)


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

    def test_d_3_the_order_check_lists_the_script_and_the_gate_and_not_the_record(self):
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, rel)) for rel in ORDER_FILES))
        self.assertNotIn(RECORD_REL, ORDER_FILES)


class PureTest(unittest.TestCase):
    def test_b_1_codes_and_the_e_and_envelope_shapes(self):
        self.assertEqual([], codes_problems())

    def test_b_2_the_class_of_one_run_and_stopped_runs_are_counted(self):
        self.assertEqual([], class_problems())

    def test_b_3_totals_and_the_34_boundary(self):
        self.assertEqual([], totals_problems())

    def test_b_4_the_hand_counts_are_not_the_same_as_nearby_numbers(self):
        u"""手で決めた値が互いに違い、3 通りで違う・33 と 34 の境の手前と上が在る。"""
        self.assertEqual(len(set(t[2][EC5611W][1] for t in HAND_TOTALS[:3] if EC5611W in t[2])), 2)
        self.assertEqual(len(set(HAND_TOTALS[r][0] for r in range(3))), 3)
        self.assertTrue(all(sum(t[0]) == 3 for t in HAND_TOTALS))
        self.assertEqual(HAND_TOTALS[0][4], 1)
        self.assertNotEqual(HAND_TOTALS[1][3], HAND_TOTALS[2][3])
        self.assertEqual(sorted(HAND_RUN), [(d, r) for d in (1, 2, 3) for r in range(3)])
        self.assertEqual(len(set(len(v[3]) for v in HAND_RUN.values())) >= 4, True)
        self.assertNotEqual(HAND_TOTALS[1][6][0], HAND_TOTALS[2][6][0])                       # 2026 と 2025 で EDINET. の符号の種類が違う(XV0-5 の読み先を縛る)


class RunTest(unittest.TestCase):
    def test_c_1_the_tool_check_and_the_command(self):
        self.assertEqual([], tools_problems())

    def test_c_2_exec_cmd_has_no_shell_merges_output_and_reports_the_timeout(self):
        self.assertEqual([], exec_problems())

    def test_c_3_three_runs_per_document_in_order_with_throwaway_copies(self):
        self.assertEqual([], run_problems())

    def test_c_4_run_record_check_with_fake_tools_and_a_fake_cache(self):
        self.assertEqual([], e2e_problems())

    def test_c_5_the_record_check_catches_tampering(self):
        self.assertEqual([], verify_problems())

    def test_c_6_the_forbidden_checks_stop_planted_content(self):
        self.assertEqual([], clean_problems())

    def test_c_7_the_real_record_when_present_is_clean_and_consistent(self):
        p = os.path.join(ROOT, RECORD_REL)
        if not os.path.exists(p):
            self.skipTest(u"記録は本番の走りの後に書かれる。記録の中身の検査は結果の門に置く")
        text = read(RECORD_REL)
        MS.verify_record(json.loads(text, object_pairs_hook=od), text)


class WiringTest(unittest.TestCase):
    def test_e_1_imports_and_the_wall_functions_are_called_not_copied(self):
        self.assertEqual([], import_problems())

    def test_e_2_the_import_check_sees_planted_violations(self):
        base = read(SCRIPT_REL)
        self.assertNotEqual([], import_problems(base + u"\nimport socket\n"))
        self.assertNotEqual([], import_problems(base + u"\nimport urllib.request\n"))
        self.assertNotEqual([], import_problems(base + u"\nfrom adapters.xbrl import instance\n"))
        self.assertNotEqual([], import_problems(base + u"\nX = os.system('a')\n"))
        self.assertNotEqual([], import_problems(base + u"\nX = subprocess.Popen(['a'])\n"))
        self.assertNotEqual([], import_problems(base + u"\ndef select_docs(a, b):\n    return None\n"))
        self.assertNotEqual([], import_problems(base.replace(u"shell=False", u"shell=True")))
        self.assertNotEqual([], import_problems(base + u"\nX = 'measure/xbrl_tag_narrow_2026-11-21.py'\n"))
        self.assertNotEqual([], import_problems(base.replace(u"W.order_sha256(", u"order_sha256(")))

    def test_e_3_the_gate_does_not_use_the_reserved_names(self):
        self.assertEqual([], reserved_problems())
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "g.py"), "w", encoding="utf-8") as fh:
                fh.write("ENGINE_LATER_X = 1\n")
            self.assertNotEqual([], reserved_problems(rel="g.py", base=d))

    def test_e_4_the_script_leaves_sys_modules_as_it_found_them_except_its_own_wall_name(self):
        before = dict(sys.modules)
        mod = load_module(SCRIPT_REL, "xbrl_edinet_validate_script_for_sysmodules_check")
        self.assertEqual([], [k for k, v in before.items() if sys.modules.get(k) is not v])
        self.assertEqual(mod.W.__name__, WALL_NAME)
        self.assertNotEqual(WALL_NAME, "_xg1_tag_wall_2026_11_21")
        del mod

    def test_e_5_the_default_place_is_outside_the_repo_and_the_gate_never_opens_it(self):
        top = os.path.realpath(REPO)
        self.assertFalse(os.path.realpath(MS.DOCS_DIR).startswith(top + os.sep))
        src = read(GATE_REL)
        for m in re.finditer(r"ms\.(select_docs|run|check|build_record)\(([^)]*)\)", src):
            self.assertTrue(re.search(r"docs|rec_path|\*\*kw|rp", m.group(2)), m.group(0))

    def test_e_6_the_two_scripts_do_not_read_each_other(self):
        self.assertNotIn(u"xbrl_edinet_validate", read("measure/xbrl_tag_narrow_2026-11-21.py"))
        self.assertNotIn(OTHER_SCRIPT_NAME, read(SCRIPT_REL).split(u'"""', 2)[2])


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
        self.assertGreaterEqual(len(MUTANTS), 25)

    def test_f_2_the_unmutated_script_is_green_on_every_check(self):
        base = read(SCRIPT_REL)
        mod = load_source(base)
        for name in ALL_CHECKS:
            self.assertEqual([], check_by_name(name, mod, base), name)


if __name__ == "__main__":
    unittest.main()
