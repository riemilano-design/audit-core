# -*- coding: utf-8 -*-
u"""封 docs/XBRL_EDINET_VALIDATE_SEAL_2026-11-21.md(XV0 ― 公開の検査の道具 Arelle の EDINET の規則を、提出済みの有報 67 本に掛けると、どの規則がどれだけ鳴るか)の測定。
**0 USD。LLM の席は呼ばない。鍵は使わない。** engine(``core/``・``adapters/``)は読まない・変えない。書類は便 XG0 の script の選び方の関数を importlib で呼ぶ(写さない。名は他と重ならない一意の名)。

    python3 measure/xbrl_edinet_validate_2026-11-21.py --tool-r <venv の場所> --tool-p <venv の場所>   # 道具を確かめて 67 本 x 3 通り(201 回)を 1 回ずつ順に掛け、記録を書く
    python3 measure/xbrl_edinet_validate_2026-11-21.py --check                                        # 記録の形・合計・禁止のものを検査する。道具は呼ばない・掛け直さない

道具の実行 file は ``<venv>/bin/arelleCmdLine``、道具に入っている package の一覧は ``<venv>/bin/python -m pip freeze`` の出力の sha256。
subprocess は shell を通さない(引数の並びで呼ぶ)。1 回ごとに時間の上限 600 秒。超えたら「止まった」に数え、超えた数は別に書く。
``.xbrl`` で終わる file を除いた写しは ``tempfile`` の使い捨ての場所に 1 本ごとに作り、3 通りを掛けたら消す。置き場の zip は開くだけ。

実装の注(封の字では 1 通りに決まらなかった所の決め。実装より先に決め、結果を見て変えない。報告にも書く):
- 順は書類の順に 1 本ずつ、その書類に 3 通り(道具 R × 2026 → 道具 P × 2026 → 道具 P × 2025)を掛ける。
- 符号の行: 行の頭が ``[`` で、最初の ``]`` が在り、その間の字が空でないもの。``]`` の無い行は指摘の行に数えない。符号の字は前後の空白を落とさずそのまま使う。
- ``EDINET.`` で始まるが ``EDINET.EC`` + 数字 4 つ + ``E``/``W`` の形に当たらない符号は、字をそのまま符号とし、``EDINET.`` の符号の側に数える(E でも包みの形でもない)。
- 版は ``pip freeze`` の ``arelle-release==<版>`` の行で読む。``ModelValue.py`` の場所は道具の python に ``arelle`` を import させて得る。
- 時間の上限を超えた回の出力は、超えるまでに読めた分(無ければ空)で符号を数え、類は「止まった」。
"""
from __future__ import print_function

import argparse
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
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _load_wall():
    u"""便 XG0 の script を、他と重ならない一意の名で読む(関数は呼ぶだけ。写さない)。"""
    name = "_xv0_tag_wall_2026_11_21"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, "xbrl_tag_wall_2026-11-21.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


W = _load_wall()

SEAL_REL = "docs/XBRL_EDINET_VALIDATE_SEAL_2026-11-21.md"
SEAL_COMMIT = "1bda1997"
SCRIPT_REL = "measure/xbrl_edinet_validate_2026-11-21.py"
RECORD_REL = "fixtures/xbrl/cd8/edinet_validate_2026-11-21.json"
DOCS_DIR = W.DOCS_DIR
DOCS_WANT = W.DOCS_WANT

# ---- 封 §1 の決めごと(字で留める。封の門が封の字と照らす)
TOOL_VERSION = "2.47.5"
SHA_R = "3d108b7764e01306e032f78def4036813c74d32d0e27c3a684a9df4f8f376ff0"
SHA_P = "fd9b0d08bf283452fe4ebd6ec9de2f273010de0420b70e61c993a6c033814635"
PLUGINS = "validate/EDINET|inlineXbrlDocumentSet"
#: 3 通り(道具, 規則の年)。順もこの並び
RUNS = (("R", "EDINET-2026"), ("P", "EDINET-2026"), ("P", "EDINET-2025"))
RUN_KEYS = tuple(u"道具 %s × %s" % (t, y) for t, y in RUNS)
TIMEOUT_SEC = 600
EXE_REL = os.path.join("bin", "arelleCmdLine")
PY_REL = os.path.join("bin", "python")
STRIP_SUFFIX = ".xbrl"
MARK_ACTIVATION = "Activation of plug-in Validate EDINET successful"
MARK_FORMAT = "Identified filing format"
TRACEBACK = "Traceback"
INFO_CODE = "info"
EDINET_PREFIX = "EDINET."
EDINET_CODE_RE = re.compile(r"^EDINET\.EC\d{4}[EW]")
ENVELOPE_DIGIT = "0"
CLS_RAN, CLS_STOPPED, CLS_NOT_RUN = u"走った", u"止まった", u"走らなかった"
CLASSES = (CLS_RAN, CLS_STOPPED, CLS_NOT_RUN)
BIG_DOCS = 34
EC5611W = "EDINET.EC5611W"
ENVELOPE_PAIR = ("EDINET.EC0121E", "EDINET.EC0130E")
PRINT_MV_PATH = "import arelle, os; print(os.path.join(os.path.dirname(arelle.__file__), 'ModelValue.py'))"
#: 封 §4 の予測の境(記録には判定を書かない。封の門が封の表と照らす)。(下限, 上限) か None
BOUNDS = collections.OrderedDict([
    ("XV0-1", (60, None)), ("XV0-2", (None, 3)), ("XV0-3", (None, 33)), ("XV0-4", (40, None)), ("XV0-5", (8, 30)), ("XV0-6", (10, None)), ("XV0-7", (65, None))])
LIMITS = [
    u"掛けたのは API から取った zip(拡張子 xbrl の file を除いた写し)で、提出の包みそのものではない。包みの形の符号はこの違いで鳴りうる。",
    u"規則の年は 2 つとも全部の書類に掛ける。書類ごとに正しい年は決めていない。",
    u"道具の EDINET の規則は版の字が 0.0.1 で、EDINET の本物の検査の全部を写したものとは言えない。本物の検査の結果とは照らしていない。",
    u"道具 P は 1 行を直したもので、本家の版ではない。直しがほかの規則の鳴り方を変えていないことは、見た 1 本で「止まるまでの符号の数が同じ」ことしか確かめていない。",
    u"67 本は無作為ではない。有報だけ。",
    u"鳴ったことは、規則の誤りとも書類の誤りとも読まない。鳴らなかった符号は、正しく黙ったのか効いていないのかを測っていない。",
    u"「EDINET の検査に通る」「XBRL を作れる」は、この便からは言えない。"]

Stop = W.Stop
od = collections.OrderedDict
sha256_bytes = W.sha256_bytes
sha256_file = W.sha256_file
dumps = W.dumps

# ---- 記録に書かないもの(封 §5): docID・会社の名・EDINET コード・file の名・指摘の行の本文
FILE_FORM_RE = re.compile(r"\.(?:xsd|htm|html|zip|xbrl|xml|csv|txt|log)\b|PublicDoc|AuditDoc|XBRL/", re.I)
BODY_MIN = 12


# ======================================================================================================
# 出力の字 → 符号(封 §1 の符号の読み方)
def codes_of(text):
    u"""出力の字 → 指摘の行の符号の並び(行ごと 1 つ)。行の頭が ``[`` で、最初の ``]`` までの中身が空でないもの。``info`` は数えない。``EDINET.`` の符号は ``EDINET.EC`` + 数字 4 つ + ``E``/``W`` まで。"""
    out = []
    for line in text.splitlines():
        if not line.startswith("["):
            continue
        end = line.find("]")
        if end < 0:
            continue
        code = line[1:end]
        if not code or code == INFO_CODE:
            continue
        if code.startswith(EDINET_PREFIX):
            m = EDINET_CODE_RE.match(code)
            if m:
                code = m.group(0)
        out.append(code)
    return out


def is_edinet(code):
    return code.startswith(EDINET_PREFIX)


def is_e_code(code):
    u"""E の符号: ``EDINET.EC`` + 数字 4 つ + ``E``。"""
    m = EDINET_CODE_RE.match(code)
    return bool(m) and m.group(0) == code and code.endswith("E")


def is_envelope(code):
    u"""包みの形の符号: E の符号のうち、数字の頭が ``0`` のもの。"""
    return is_e_code(code) and code[len(EDINET_PREFIX) + 2] == ENVELOPE_DIGIT


def is_other_e(code):
    u"""包みの形のほかの E: E の符号のうち、包みの形でないもの。"""
    return is_e_code(code) and not is_envelope(code)


def run_class(text, timed_out=False):
    u"""1 回の類(封 §1 の字どおり)。時間の上限を超えたか ``Traceback`` が在れば止まった・``Activation…`` の行と ``Identified filing format`` の行の **両方が無い** ときだけ走らなかった・
    どちらでもなければ(片方だけ在る出力も)走った。"""
    if timed_out or TRACEBACK in text:
        return CLS_STOPPED
    if MARK_ACTIVATION not in text and MARK_FORMAT not in text:
        return CLS_NOT_RUN
    return CLS_RAN


def count_one(text, timed_out=False):
    u"""1 回分を数える。出力の行の数(``splitlines`` の数。本文は持たない)は、指摘が 0 のときに出力が空だったのかを後から読むため。"""
    cnt = collections.Counter(codes_of(text))
    return od([(u"類", run_class(text, timed_out)), (u"時間の上限を超えた", bool(timed_out)), (u"出力の行の数", len(text.splitlines())), (u"符号ごとの行", od(sorted(cnt.items())))])


def run_totals(entries):
    u"""1 通りの書類ごとの数([count_one の返り値] 67 本分)→ 合計。"""
    cls = od((c, 0) for c in CLASSES)
    docs_by = collections.Counter()
    lines_by = collections.Counter()
    other_e = no_e = no_line = timeouts = pair = 0
    for e in entries:
        cls[e[u"類"]] += 1
        if e[u"時間の上限を超えた"]:
            timeouts += 1
        codes = e[u"符号ごとの行"]
        for c, n in codes.items():
            docs_by[c] += 1
            lines_by[c] += n
        if any(is_other_e(c) for c in codes):
            other_e += 1
        if not any(is_e_code(c) for c in codes):
            no_e += 1
        if not codes:
            no_line += 1
        if any(c in codes for c in ENVELOPE_PAIR):
            pair += 1
    kinds_e = sum(1 for c in docs_by if is_edinet(c))
    return od([
        (u"類別", cls), (u"時間の上限を超えた数", timeouts),
        (u"符号ごと", od((c, od([(u"書類", docs_by[c]), (u"行", lines_by[c])])) for c in sorted(docs_by))),
        (u"包みの形のほかの E が 1 行以上在る書類", other_e), (u"E の符号が 1 行も無い書類", no_e), (u"指摘の行が 1 行も無い書類", no_line),
        (u"鳴った符号の種類", od([(u"EDINET. の符号", kinds_e), (u"ほかの符号", len(docs_by) - kinds_e)])),
        (u"%d 本以上で鳴った符号の種類" % BIG_DOCS, sum(1 for c in docs_by if docs_by[c] >= BIG_DOCS)),
        (u"EC0121E か EC0130E が鳴る書類", pair)])


def judged(totals, n=DOCS_WANT):
    u"""封 §4 の判定に要る数(当たり・外れは書かない)。totals = {RUN_KEYS の 1 つ: run_totals}。"""
    r26, p26, p25 = (totals[k] for k in RUN_KEYS)
    return od([
        (u"XV0-1 道具 R・2026: 止まった書類", od([(u"書類", r26[u"類別"][CLS_STOPPED]), (u"分母", n)])),
        (u"XV0-2 道具 P・2026: 止まった + 走らなかった書類", od([(u"書類", p26[u"類別"][CLS_STOPPED] + p26[u"類別"][CLS_NOT_RUN]), (u"分母", n)])),
        (u"XV0-3 道具 P・2026: 包みの形のほかの E が 1 行以上在る書類", od([(u"書類", p26[u"包みの形のほかの E が 1 行以上在る書類"]), (u"分母", n)])),
        (u"XV0-4 道具 P・2026: EC5611W が鳴る書類", od([(u"書類", p26[u"符号ごと"].get(EC5611W, {}).get(u"書類", 0)), (u"分母", n)])),
        (u"XV0-5 道具 P・2026: 鳴った EDINET. の符号の種類", p26[u"鳴った符号の種類"][u"EDINET. の符号"]),
        (u"XV0-6 道具 P: 包みの形のほかの E が在る書類(2025・2026・2025 から 2026 を引いた差)", od([
            (u"2025", p25[u"包みの形のほかの E が 1 行以上在る書類"]), (u"2026", p26[u"包みの形のほかの E が 1 行以上在る書類"]),
            (u"差", p25[u"包みの形のほかの E が 1 行以上在る書類"] - p26[u"包みの形のほかの E が 1 行以上在る書類"])])),
        (u"XV0-7 道具 P・2026: EC0121E か EC0130E が鳴る書類", od([(u"書類", p26[u"EC0121E か EC0130E が鳴る書類"]), (u"分母", n)])),
        (u"補 道具 P・2026: 指摘の行が 1 行も無い書類(5 本以上なら先に自分の欠陥を疑う)", p26[u"指摘の行が 1 行も無い書類"])])


# ======================================================================================================
# 道具の確かめ・掛ける(封 §1)
def exec_cmd(cmd, timeout):
    u"""引数の並びで呼ぶ(shell を通さない)。(出力の字, 時間の上限を超えたか)。標準の出力と標準のエラーは 1 つにする。"""
    try:
        p = subprocess.run(list(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, shell=False)
    except subprocess.TimeoutExpired as exc:
        return (exc.output or b"").decode("utf-8", "replace"), True
    return p.stdout.decode("utf-8", "replace"), False


def command(tool, year, zip_path):
    return [os.path.join(tool, EXE_REL), "--plugins", PLUGINS, "--disclosureSystem", year, "-f", zip_path, "--validate"]


def tool_info(tool, runner=exec_cmd, sha_reader=sha256_file):
    u"""道具 1 つの (版, ModelValue.py の sha256, package の一覧の sha256, Python の版)。"""
    py = os.path.join(tool, PY_REL)
    freeze, to1 = runner([py, "-m", "pip", "freeze"], 300)
    path, to2 = runner([py, "-c", PRINT_MV_PATH], 120)
    pyver, to3 = runner([py, "--version"], 60)
    if to1 or to2 or to3:
        raise Stop(u"**道具の確かめが時間の上限を超えた。止める**")
    m = re.search(r"^arelle-release==(\S+)\s*$", freeze, re.M)
    version = m.group(1) if m else u""
    try:
        mv = sha_reader(path.strip())
    except OSError:
        raise Stop(u"**道具の ModelValue.py を読めない。止める**")
    return od([(u"版", version), (u"ModelValue.py の sha256", mv), (u"package の一覧の sha256", sha256_bytes(freeze.encode("utf-8"))), (u"Python の版", pyver.strip())])


def check_tools(tool_r, tool_p, runner=exec_cmd, sha_reader=sha256_file, want_version=TOOL_VERSION, want_r=SHA_R, want_p=SHA_P):
    u"""実行 file が在り、版・ModelValue.py の sha256 が封の字と同じであること。違えば止まる。(道具 R の情報, 道具 P の情報)。"""
    for t in (tool_r, tool_p):
        if not os.path.isfile(os.path.join(t, EXE_REL)):
            raise Stop(u"**道具の実行 file が無い。止める**")
    info_r = tool_info(tool_r, runner, sha_reader)
    info_p = tool_info(tool_p, runner, sha_reader)
    if info_r[u"版"] != want_version or info_p[u"版"] != want_version:
        raise Stop(u"**道具の版が %s でない。止める**" % want_version)
    if info_r[u"ModelValue.py の sha256"] != want_r:
        raise Stop(u"**道具 R の ModelValue.py の sha256 が封と違う。止める**")
    if info_p[u"ModelValue.py の sha256"] != want_p:
        raise Stop(u"**道具 P の ModelValue.py の sha256 が封と違う。止める**")
    return info_r, info_p


def strip_copy(src, dst):
    u"""名が ``.xbrl`` で終わる file を除いた写しを作る。置き場の zip は開くだけ。"""
    with zipfile.ZipFile(src) as zi, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zo:
        for info in zi.infolist():
            if not info.filename.endswith(STRIP_SUFFIX):
                zo.writestr(info, zi.read(info.filename))


def run_doc(tool_dirs, zip_path, runner=exec_cmd, tmp_root=None, sink=None):
    u"""書類 1 本を 3 通り順に掛ける。写しは使い捨ての場所に作り、終わったら(例外でも)消す。[count_one の返り値] を RUNS の順に。"""
    d = tempfile.mkdtemp(prefix="xv0_", dir=tmp_root)
    try:
        copy = os.path.join(d, "doc.zip")
        strip_copy(zip_path, copy)
        out = []
        for t, year in RUNS:
            text, timed_out = runner(command(tool_dirs[t], year, copy), TIMEOUT_SEC)
            out.append(count_one(text, timed_out))
            if sink is not None:
                sink.update(ln.strip() for ln in text.splitlines() if len(ln.strip()) >= BODY_MIN)
        return out
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ======================================================================================================
# 記録
def build_record(tool_r, tool_p, docs_dir=None, want=DOCS_WANT, runner=exec_cmd, sha_reader=sha256_file, tmp_root=None, want_version=TOOL_VERSION, want_r=SHA_R, want_p=SHA_P):
    u"""道具を確かめてから、書類 x 3 通りを 1 回ずつ順に掛ける。(記録, secret)。書かない。"""
    docs = W.select_docs(docs_dir or DOCS_DIR, want)
    info_r, info_p = check_tools(tool_r, tool_p, runner, sha_reader, want_version, want_r, want_p)
    tool_dirs = {"R": tool_r, "P": tool_p}
    per_doc = []
    lines = set()
    for n, (_stem, p, _xs) in enumerate(docs, 1):
        res = run_doc(tool_dirs, p, runner, tmp_root, lines)
        per_doc.append(od([(u"番号", n)] + [(k, r) for k, r in zip(RUN_KEYS, res)]))
    ecodes = set()
    for _stem, _p, xs in docs:
        for x in xs:
            ecodes.update(re.findall(r"E\d{5}", x))
    secret = (set(), set(), [d[0] for d in docs], ecodes, lines)
    return assemble(per_doc, W.order_sha256([d[0] for d in docs]), info_r, info_p), secret


def assemble(per_doc, order_sha, info_r, info_p):
    u"""書類ごとの数 → 記録。"""
    totals = od((k, run_totals([d[k] for d in per_doc])) for k in RUN_KEYS)
    rec = od()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"XV0(公開の検査の道具 Arelle の EDINET の規則を、提出済みの有報 67 本に掛けると、どの規則がどれだけ鳴るか)(0 USD・engine は読まない)"
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"材料"] = od([
        (u"書類の本数", len(per_doc)), (u"書類の file 名の並びの sha256", order_sha),
        (u"道具の版", info_r[u"版"]),
        (u"道具 R の ModelValue.py の sha256", info_r[u"ModelValue.py の sha256"]), (u"道具 P の ModelValue.py の sha256", info_p[u"ModelValue.py の sha256"]),
        (u"道具 R の package の一覧の sha256", info_r[u"package の一覧の sha256"]), (u"道具 P の package の一覧の sha256", info_p[u"package の一覧の sha256"]),
        (u"Python の版(道具 R)", info_r[u"Python の版"]), (u"Python の版(道具 P)", info_p[u"Python の版"]),
        (u"3 通り", list(RUN_KEYS)), (u"時間の上限(秒)", TIMEOUT_SEC)])
    rec[u"書類"] = per_doc
    rec[u"集計"] = totals
    rec[u"予測の判定に要る数(XV0-1〜XV0-7。当たり・外れは結果の文書で)"] = judged(totals, len(per_doc))
    rec[u"限界"] = list(LIMITS)
    return rec


def check_clean(rec, text, secret=None):
    u"""記録に書かないもの(docID・EDINET コード・file の名・指摘の行の本文)が無いか。在れば止める。secret = (行の字, 要素の名, docID の並び, EDINET コードの集まり, 出力の行の集まり)。"""
    W.check_clean(rec, text, secret[:4] if secret else None)
    scan = W.HEX_RE.sub(u"", text)
    if FILE_FORM_RE.search(scan):
        raise Stop(u"**記録に file の名の形の字が在る。止める**")
    if secret and len(secret) > 4:
        for line in secret[4]:
            if len(line) >= BODY_MIN and line in scan:
                raise Stop(u"**記録に指摘の行の本文が在る。止める**")


def verify_record(rec, text=None, want=DOCS_WANT):
    u"""記録の形・合計・禁止のものを検査する(道具は呼ばない・掛け直さない)。違えば止まる。"""
    docs = rec.get(u"書類")
    if not isinstance(docs, list) or len(docs) != want or rec[u"材料"][u"書類の本数"] != want:
        raise Stop(u"**記録の書類が 67 本でない。止める**")
    for i, d in enumerate(docs, 1):
        if d.get(u"番号") != i or any(k not in d for k in RUN_KEYS):
            raise Stop(u"**記録の書類の形が違う。止める**")
        for k in RUN_KEYS:
            e = d[k]
            if e.get(u"類") not in CLASSES or not isinstance(e.get(u"符号ごとの行"), dict) or not isinstance(e.get(u"時間の上限を超えた"), bool):
                raise Stop(u"**記録の 1 回分の形が違う。止める**")
            nl = e.get(u"出力の行の数")
            if not isinstance(nl, int) or isinstance(nl, bool) or nl < sum(e[u"符号ごとの行"].values()):
                raise Stop(u"**出力の行の数が無い・整数でない・指摘の行の数より少ない。止める**")
            if e[u"時間の上限を超えた"] and e[u"類"] != CLS_STOPPED:
                raise Stop(u"**時間の上限を超えた回が「止まった」でない。止める**")
    totals = od((k, run_totals([d[k] for d in docs])) for k in RUN_KEYS)
    if dumps(totals) != dumps(rec[u"集計"]) or dumps(judged(totals, len(docs))) != dumps(rec[[k for k in rec if k.startswith(u"予測の判定に要る数")][0]]):
        raise Stop(u"**記録の合計が書類ごとの数と合わない。止める**")
    for k in RUN_KEYS:
        if sum(rec[u"集計"][k][u"類別"].values()) != want:
            raise Stop(u"**類別の合計が 67 でない。止める**")
    check_clean(rec, text if text is not None else dumps(rec))


def record_text(rec, secret=None):
    text = dumps(rec)
    check_clean(rec, text, secret)
    return text


def write_exclusive(path, data):
    with open(path, "xb") as fh:
        fh.write(data)


def write_record(path, rec, secret=None):
    u"""書く前と書いた後に検査する。既に在れば止める(測り直さない)。"""
    if os.path.exists(path):
        raise Stop(u"**記録が既に在る: %s。止める**" % os.path.basename(path))
    text = record_text(rec, secret)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_exclusive(path, text.encode("utf-8"))
    with io.open(path, encoding="utf-8") as fh:
        back = fh.read()
    try:
        check_clean(rec, back, secret)
    except SystemExit:
        os.remove(path)
        raise


def run(tool_r, tool_p, root=ROOT, docs=None, out=None, want=DOCS_WANT, runner=exec_cmd, sha_reader=sha256_file, tmp_root=None, want_version=TOOL_VERSION, want_r=SHA_R, want_p=SHA_P, say=print):
    rec, secret = build_record(tool_r, tool_p, docs, want, runner, sha_reader, tmp_root, want_version, want_r, want_p)
    out = out or os.path.join(root, RECORD_REL)
    write_record(out, rec, secret)
    say(u"-> %s(書類 %d)" % (os.path.basename(out), rec[u"材料"][u"書類の本数"]))
    return rec


def check(root=ROOT, rec_path=None, say=print, want=DOCS_WANT):
    u"""記録の形・合計・禁止のものを検査する。置き場も道具も読まない。"""
    p = rec_path or os.path.join(root, RECORD_REL)
    if not os.path.isfile(p):
        raise Stop(u"**在る記録が無い。止める**")
    with io.open(p, encoding="utf-8") as fh:
        text = fh.read()
    rec = json.loads(text, object_pairs_hook=collections.OrderedDict)
    verify_record(rec, text, want)
    say(u"--check: 記録の形・合計・禁止のものの検査は通った(書類 %d)" % len(rec[u"書類"]))
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="記録の形・合計・禁止のものを検査する。道具は呼ばない")
    ap.add_argument("--tool-r", default=None, help="道具 R(手を入れない)の venv の場所")
    ap.add_argument("--tool-p", default=None, help="道具 P(1 行の直し)の venv の場所")
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--docs", default=None, help="書類の置き場(既定は封の字)")
    a = ap.parse_args(argv)
    if a.check:
        check(root=a.root)
        return
    if not a.tool_r or not a.tool_p:
        raise Stop(u"**--tool-r と --tool-p が要る。止める**")
    run(a.tool_r, a.tool_p, root=a.root, docs=a.docs)


if __name__ == "__main__":
    main()
