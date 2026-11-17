# -*- coding: utf-8 -*-
"""封 docs/XBRL_ROUNDING_MIXED_ENGINE_SEAL_2026-11-04.md(RB ― 丸め方の根拠が混ざる桁は両方の帯で照らす。P30E = P29E + RB。既定にしない)の測定の門。封 §5。

**この門が縛るもの**(結果の門 ``test_xbrl_rmix_result.py`` は記録・文書・採用の判定を縛る)

1. 封の字(規則の要点): 混ざる桁の定義(round しか説明できない件と truncate しか説明できない件の両方が 1 件以上ある桁)・mode ``"both"``(梯子の先頭で ``None`` として扱う・``_mag_trunc`` は偽・
   G3 の保留は残る)・``P30E = dataclasses.replace(P29E, ...)``・旗の名前・``DEFAULT_PROFILE`` が封に在る。§3 の予測の表が D-1〜D-10 の 10 行で、どの行も予測と外れ方の欄を持つ。§4 の K-1〜K-5。§5 の script 2 本と記録 3 つ・門 2 本の path。
2. 旗・profile: 旗の位置(``numbers_man_comma_2026_11_04`` の直後・``written_precision_2026_10_27`` の前)・既定が偽・P30E = P29E + 旗・旗が真の profile は P30E だけが RB の旗を持つ(P29・P29E は持たない)・
   ``DEFAULT_PROFILE == "P27"``・梯子の関数(``vocabulary.match_value``・``comparators._match_value``)の ``"both"`` が ``None`` と同じ結果で ``"round"``・``"truncate"`` とは違う。
3. engine の変更は封の commit から engine の commit までで §2-1 の 3 file だけ・削除 0・挿入は封の見込みの範囲。
4. 前の便の script・記録(この便が importlib で読むだけのもの)は封の commit の blob と byte が同じ。
5. 順序: 封 de23edc ⊏ engine を触った commit ⊏ script 2 本・門 2 本(記録・結果の文書の順序は結果の門が見る)。engine の commit の hash を字で持たず、履歴から探す。未 commit は赤(skip にしない)。
6. 新しい門が、既存の門が行頭の名前を数える変数名を行頭に置いていない。
7. 門の変異: 封の字・profile の定義・表の行・numstat・順序を 1 つずつ壊した標本で上の検査が赤になる。

この file は docID の字を持たない(引きの門が追跡 file の docID を数える)。
"""
import dataclasses
import importlib.util
import os
import re
import subprocess
import sys
import tempfile
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))

SEAL_REL = "docs/XBRL_ROUNDING_MIXED_ENGINE_SEAL_2026-11-04.md"
SEAL_COMMIT_SHORT = "de23edc"
FLAG = "rounding_mixed_2026_11_04"
PREV_FLAG = "numbers_man_comma_2026_11_04"
NEXT_FLAG = "written_precision_2026_10_27"
ENGINE_FILES = ("adapters/xbrl/recipes.py", "adapters/xbrl/vocabulary.py", "adapters/xbrl/comparators.py")
SCRIPT_RELS = ("measure/xbrl_rmix_2026-11-04.py", "measure/xbrl_rmix_regress97_2026-11-04.py")
GATE_RELS = ("tests/measure/test_xbrl_rmix_seal.py", "tests/measure/test_xbrl_rmix_result.py")
RECORD_RELS = ("fixtures/xbrl/rmix/ai200_2026-11-04.json", "fixtures/xbrl/rmix/inject_2026-11-04.json", "fixtures/xbrl/rmix/regress97_2026-11-04.json")
DOC_REL = "docs/XBRL_ROUNDING_MIXED_ENGINE_RESULT_2026-11-04.md"
#: この便が読むだけの前の便の script・記録・門(封の commit の blob と byte が同じでなければならない)。数の読み取り N の便の seal の門は、engine の commit が profile の一覧の遷移
#: (RB の旗の位置)を足すため封の後に変わる(宣言された遷移)ので含めない
READ_ONLY_RELS = ("measure/xbrl_numfix_2026-11-04.py", "measure/xbrl_numfix_regress97_2026-11-04.py", "measure/xbrl_numfix_shapes_2026-11-04.py",
                  "fixtures/xbrl/numfix/ai200_2026-11-04.json", "fixtures/xbrl/numfix/inject_2026-11-04.json",
                  "fixtures/xbrl/numfix/regress97_2026-11-04.json", "fixtures/xbrl/numfix/shapes_2026-11-04.json",
                  "tests/measure/test_xbrl_numfix_result.py",
                  "measure/xbrl_aiforms_gen_2026-11-03.py", "measure/xbrl_aiforms_run_2026-11-03.py", "measure/xbrl_p27_tune_2026-10-27.py",
                  "measure/xbrl_p28_regress97_2026-11-02.py", "measure/xbrl_p27_regress97_2026-10-27.py", "measure/xbrl_p28_ai_prose_2026-11-02.py",
                  "fixtures/xbrl/aiforms/gen_2026-11-03.json", "fixtures/xbrl/aiforms/f5_gen_2026-11-03.json",
                  "fixtures/xbrl/aiforms/claims_2026-11-03.json", "fixtures/xbrl/aiforms/f5_claims_2026-11-03.json",
                  "fixtures/xbrl/aiforms/labels_2026-11-03.json", "fixtures/xbrl/aiforms/f5_labels_2026-11-03.json", "measure/SEED.json")
#: 既存の門が行頭の名前を数える変数名(新しい門はこれらを行頭に置かない。封 §2-3)
RESERVED_PREFIXES = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS", "LATER_FINGERPRINT",
                     "FINGERPRINT_", "LATER_TARGET", "LATER_FROZEN", "FROZEN_BUNDLE_AT_SEAL", "TARGET_AT_SEAL", "ENGINE_AT_SEAL", "ENGINE_AT_MEASURE", "ENGINE_DECLARED")
DOCID_RE = re.compile(r"S100[A-Z0-9]{4}")
PRED_IDS = tuple("D-%d" % i for i in range(1, 11))
K_IDS = tuple("K-%d" % i for i in range(1, 6))
#: 封の字の要点(封に無ければ赤)
SEAL_PHRASES = (
    u"round しか説明できない件(差 < 0)と truncate しか説明できない件(差 > 桁 / 2)の両方が 1 件以上ある桁",
    u"(mode `\"both\"` = 1 周目の梯子と同じ −桁/2 .. +桁)",
    u"`recipes._mag_trunc` は `\"both\"` で偽",
    u"G3 `rounded_diff_hold` の `rounding is not None` は `\"both\"` で真",
    u"`P30E = dataclasses.replace(P29E, name=\"P30E\", rounding_mixed_2026_11_04=True)`",
    u"旗の欄は `numbers_man_comma_2026_11_04` の直後",
    u"`DEFAULT_PROFILE` は \"P27\" のまま",
    u"`if mode == \"both\": mode = None`",
    u"既存の profile(P27〜P29E)の出力は 1 byte も変えない",
)


def load_module(rel, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PR = load_module("tests/measure/test_xbrl_p28_result.py", "p28_result_helpers_for_rmix_seal")       # 順序の部品(order_problems・Repo・added_commits・git_in)。門としては走らせない


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------- 1. 封の字
def table_ids(seal, start, end, pat):
    sec = seal[seal.index(start):seal.index(end)]
    return [m.group(1) for m in (re.match(pat, line) for line in sec.splitlines()) if m]


def seal_problems(seal):
    out = []
    try:
        ids = table_ids(seal, "## §3", "## §4", r"^\| (D-\d+) \| (.*) \|$")
        sec = seal[seal.index("## §3"):seal.index("## §4")]
        sec4 = seal[seal.index("## §4"):seal.index("## §5")]
        sec21 = seal[seal.index("### §2-1"):seal.index("### §2-2")]
    except ValueError:
        return [u"封の節(§2-1・§3・§4・§5)が揃っていない"]
    if ids != list(PRED_IDS):
        out.append(u"封 §3 の表が D-1〜D-10 の 10 行でない: %s" % ids)
    for line in sec.splitlines():
        m = re.match(r"^\| (D-\d+) \| (.*) \|$", line)
        if m:
            cells = m.group(2).split(u" | ")
            if len(cells) < 3 or any(not c.strip() for c in cells[:3]):
                out.append(u"封 §3 の %s の欄(欄・予測・外れ方)が埋まっていない" % m.group(1))
    got_k = re.findall(r"^- \*\*(K-\d)", sec4, re.M)
    if got_k != list(K_IDS):
        out.append(u"封 §4 の K-1〜K-5 が揃っていない: %s" % got_k)
    for rel in SCRIPT_RELS + GATE_RELS + (DOC_REL,):
        if rel not in seal:
            out.append(u"封に path が無い: %s" % rel)
    for rel in RECORD_RELS:                                  # 封は『`fixtures/xbrl/rmix/ai200_2026-11-04.json`・`inject_2026-11-04.json`』と 2 つ目の folder を省くので、folder と file 名で見る
        if os.path.dirname(rel) + u"/" not in seal or os.path.basename(rel) not in seal:
            out.append(u"封に記録の path が無い: %s" % rel)
    for rel in ENGINE_FILES:
        if u"`%s`" % rel not in sec21:
            out.append(u"封 §2-1 に engine の file が無い: %s" % rel)
    for ph in SEAL_PHRASES:
        if ph not in seal:
            out.append(u"封に規則の要点の字が無い: %s" % ph)
    return out


def seal_insert_ranges(seal):
    u"""封 §2-1 の表の『行数の見込み(挿入)』{engine の file: (下, 上)}。"""
    sec21 = seal[seal.index("### §2-1"):seal.index("### §2-2")]
    out = {}
    for line in sec21.splitlines():
        m = re.match(r"^\| `(adapters/xbrl/[a-z_]+\.py)` \|.*\| (\d+)〜(\d+) \|$", line)
        if m:
            out[m.group(1)] = (int(m.group(2)), int(m.group(3)))
    return out


# ---------------------------------------------------------------- 2. 旗・profile・梯子
GRID = [(fv, t, unit) for fv in (100.0, 96.0, 104.0, 108.0, 111.0, -300.0, -96.0, 95.0) for t in (100.0, -100.0, 90.0) for unit in (1.0, 10.0, 100.0)]
PROBE_BOTH_NOT_ROUND = (108.0, 100.0, 10.0)           # 切り捨てなら当たり・四捨五入なら外れ
PROBE_BOTH_NOT_TRUNCATE = (96.0, 100.0, 10.0)         # 四捨五入なら当たり・切り捨てなら外れ


def ladder_problems(fns=None):
    u"""梯子の関数(``vocabulary.match_value``・``comparators._match_value``)の mode ``"both"`` が格子の全部の点で ``None`` と同じ。
    格子が 3 つの mode を見分けられること(``"round"``・``"truncate"`` と ``None`` が違う点を含む)は ``probe_problems`` が別に見る。"""
    from adapters.xbrl import comparators as C
    from adapters.xbrl import vocabulary as VOC
    fns = fns or (("vocabulary.match_value", VOC.match_value), ("comparators._match_value", C._match_value))
    out = []
    for name, fn in fns:
        for fv, t, unit in GRID:
            if fn(fv, t, unit, "both") != fn(fv, t, unit, None):
                out.append(u"%s: mode \"both\" が None と違う: %r" % (name, (fv, t, unit)))
                break
    return out


def probe_problems(fns=None):
    u"""格子が mode を見分けられる: 本物の関数で、None(= \"both\")は切り捨ての点で四捨五入と違い、四捨五入の点で切り捨てと違う。"""
    from adapters.xbrl import comparators as C
    from adapters.xbrl import vocabulary as VOC
    fns = fns or (("vocabulary.match_value", VOC.match_value), ("comparators._match_value", C._match_value))
    out = []
    for name, fn in fns:
        if (PROBE_BOTH_NOT_ROUND not in GRID) or fn(*(PROBE_BOTH_NOT_ROUND + (None,))) == fn(*(PROBE_BOTH_NOT_ROUND + ("round",))):
            out.append(u"%s: 格子が None と \"round\" を見分けられない" % name)
        if (PROBE_BOTH_NOT_TRUNCATE not in GRID) or fn(*(PROBE_BOTH_NOT_TRUNCATE + (None,))) == fn(*(PROBE_BOTH_NOT_TRUNCATE + ("truncate",))):
            out.append(u"%s: 格子が None と \"truncate\" を見分けられない" % name)
    return out


def profile_problems(V=None, fields=None):
    u"""旗・profile の定義。V = vocabulary(試験が壊した写しを渡す)、fields = Profile の欄の名前の列。"""
    from adapters.xbrl import vocabulary as VOC
    V = V or VOC
    out = []
    names = list(fields) if fields is not None else [f.name for f in dataclasses.fields(V.Profile)]
    if FLAG not in names:
        return [u"Profile に旗 %s が無い" % FLAG]
    i = names.index(FLAG)
    # 2026-11-06: PB(封 docs/XBRL_PRIOR_CUE_BIND_ENGINE_SEAL_2026-11-06.md §1)が旗 prior_cue_bind_2026_11_06 をこの旗の直後に足した: この旗 → PB の旗 → written_precision_2026_10_27(PB の旗が在るときだけ)
    nxt = names[i + 2:i + 3] if names[i + 1:i + 2] == ["prior_cue_bind_2026_11_06"] else names[i + 1:i + 2]
    # 2026-11-09: T(封 docs/XBRL_TABLE_PERIOD_ENGINE_SEAL_2026-11-09.md §1)が旗 table_period_2026_11_09 を PB の旗の直後に足した: この旗 → PB の旗 → T の旗 → written_precision_2026_10_27(T の旗が在るときだけ)
    if names[i + 1:i + 3] == ["prior_cue_bind_2026_11_06", "table_period_2026_11_09"]:
        nxt = names[i + 3:i + 4]
    if names[i - 1] != PREV_FLAG or nxt != [NEXT_FLAG]:
        out.append(u"旗の位置が %s の直後・%s の前でない" % (PREV_FLAG, NEXT_FLAG))
    if dataclasses.fields(V.Profile)[[f.name for f in dataclasses.fields(V.Profile)].index(FLAG)].default is not False:
        out.append(u"旗の既定が偽でない")
    if V.DEFAULT_PROFILE != "P27":
        out.append(u"DEFAULT_PROFILE が P27 でない")
    p, b = V.PROFILES.get("P30E"), V.PROFILES.get("P29E")
    if p is None or b is None:
        out.append(u"P30E か P29E が PROFILES に無い")
    else:
        if p != dataclasses.replace(b, name="P30E", **{FLAG: True}):
            out.append(u"P30E が P29E + 旗 でない")
        if getattr(b, FLAG) is not False:
            out.append(u"P29E の旗が偽でない(既存の profile を変えた)")
    on = sorted(k for k, pr in V.PROFILES.items() if getattr(pr, FLAG, False))
    if on != ["P30E"] + (["P32E"] if "prior_cue_bind_2026_11_06" in names else []) + (["P33E"] if "table_period_2026_11_09" in names else []):      # 2026-11-06: P32E(= P30E + PB)も RB の旗を引き継ぐ。2026-11-09: P33E(= P32E + T)も
        out.append(u"RB の旗が真の profile が P30E だけでない: %s" % on)
    if "P30" in V.PROFILES:
        out.append(u"P30(E 系でない)が在る(封は P30E だけ)")
    return out


# ---------------------------------------------------------------- 3. engine の変更
def numstat_problems(lines, ranges=None):
    u"""``git diff --numstat <封> <engine の commit> -- adapters core`` の行 → 問題の列。ranges = 封 §2-1 の挿入の見込み {file: (下, 上)}。"""
    out = []
    paths = {}
    for ln in lines:
        ins, dele, path = ln.split("\t")
        paths[path] = int(ins)
        if dele != "0":
            out.append(u"削除が 0 でない: %s" % path)
    if sorted(paths) != sorted(PREFIX + p for p in ENGINE_FILES):
        out.append(u"engine の変更が §2-1 の 3 file だけでない: %s" % sorted(paths))
    for rel, (lo, hi) in (ranges or {}).items():
        n = paths.get(PREFIX + rel)
        if n is not None and not (lo <= n <= hi):
            out.append(u"%s の挿入 %d 行が封の見込み %d〜%d の外" % (rel, n, lo, hi))
    return out


def engine_commit(root, prefix, seal_rel, impl_files):
    u"""封の commit と engine の commit(封の後に各 file を最初に触った commit のうち、子孫にあたる最後のもの)。履歴から探す(hash を字で持たない)。"""
    s = PR.added_commits(root, prefix + seal_rel)
    if len(s) != 1:
        return None, None
    firsts = []
    for rel in impl_files:
        lst = [c for c in PR.git_in(root, "log", "--format=%H", s[0] + "..HEAD", "--", prefix + rel)[1].split() if c]
        if not lst:
            return s[0], None
        firsts.append(lst[-1])
    e = firsts[0]
    for c in firsts[1:]:
        if PR.is_anc(root, e, c):
            e = c
    return s[0], e


def real_numstat_problems(root=REPO, seal=None):
    sh, e = engine_commit(root, PREFIX, SEAL_REL, ENGINE_FILES)
    if sh is None or e is None:
        return [u"封か engine の commit が履歴に無い"]
    lines = [x for x in PR.git_in(root, "diff", "--numstat", sh, e, "--", PREFIX + "adapters", PREFIX + "core")[1].splitlines() if x]
    return numstat_problems(lines, seal_insert_ranges(seal if seal is not None else read(SEAL_REL)))


# ---------------------------------------------------------------- 4. 前の便の file は byte 不変
#: 2026-11-06(PB): 封 docs/XBRL_PRIOR_CUE_BIND_ENGINE_SEAL_2026-11-06.md §2-3 が宣言した遷移(司令塔の決定 2026-11-06)。PB の engine の commit が recipes.py に +24 行・vocabulary.py に +5 行(削除 0)を足し、
#: 束ねた指紋が PB_FP になる。engine を「封の commit から変えない」と留めた後の便の門(この file の frozen_problems・untouched の numstat・記録の頭の engine の指紋を使う便)は、この遷移だけを許す。
#: 許すのは、PB の封が履歴に 1 つ在り、numstat・sha16・指紋が下の宣言と同じときだけ。他の file・他の行数・他の値は今までどおり赤。
PB_SEAL_REL = "docs/XBRL_PRIOR_CUE_BIND_ENGINE_SEAL_2026-11-06.md"
PB_ENGINE_FILES = ("adapters/xbrl/recipes.py", "adapters/xbrl/vocabulary.py")
PB_NUMSTAT = {"adapters/xbrl/recipes.py": ("24", "0"), "adapters/xbrl/vocabulary.py": ("5", "0")}
PB_SHA16 = {"adapters/xbrl/recipes.py": "0add35e7aa77d86b", "adapters/xbrl/vocabulary.py": "e35b7fea2463818f"}
PB_FP = "dc13edfee7a9ac6b900ae610d056424b622b8447491113b78c4debf902bcfee8"


def pb_seal_in_history(root=REPO):
    return len(PR.added_commits(root, PREFIX + PB_SEAL_REL)) == 1


def pb_sha16(rel, base=ROOT):
    import hashlib
    with open(os.path.join(base, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def pb_declared_numstat(line, root=REPO, base=ROOT):
    u"""``git diff --numstat`` の 1 行が PB の宣言した遷移の行か(封が履歴に在り、行数と作業木の sha16 が宣言と同じ)。"""
    parts = line.split("\t")
    if len(parts) != 3 or not parts[2].startswith(PREFIX):
        return False
    rel = parts[2][len(PREFIX):]
    return (rel in PB_NUMSTAT and (parts[0], parts[1]) == PB_NUMSTAT[rel] and pb_sha16(rel, base) == PB_SHA16[rel] and pb_seal_in_history(root))


def pb_declared_fingerprint(value, root=REPO):
    u"""記録の頭の ``adapter_xbrl_py_sha256`` の値が PB の宣言した遷移の値か(封が履歴に在るときだけ)。"""
    return value == PB_FP and pb_seal_in_history(root)


def pb_declared_file_change(root, seal_commit, rel, base=ROOT):
    u"""封の commit から ``rel`` が変わったのが、PB の engine の commit(PB の封の後に recipes.py と vocabulary.py を最初に触った commit のうち子孫の最後。履歴から探す)だけか。
    作業木が HEAD の blob と同じ(commit 済み)ことも見る。"""
    s, e = engine_commit(root, PREFIX, PB_SEAL_REL, PB_ENGINE_FILES)
    if s is None or e is None:
        return False
    log = [c for c in PR.git_in(root, "log", "--format=%H", seal_commit + "..HEAD", "--", PREFIX + rel)[1].split() if c]
    if log != [e]:
        return False
    head = subprocess.run(["git", "show", "HEAD:%s%s" % (PREFIX, rel)], cwd=root, capture_output=True)
    if head.returncode != 0:
        return False
    with open(os.path.join(base, rel), "rb") as fh:
        return head.stdout == fh.read()


#: 2026-11-06(T5Y): 封 docs/XBRL_T5_YEN_SEAL_2026-11-06.md §2-1 が宣言した遷移(司令塔の決定 2026-11-06)。注入の仕掛けの 2 file に挿入だけを足した
#: (measure/inject.py に +30 行・measure/lib/sites.py に +81 行。削除 0。切り替え t5_yen_2026_11_06 は既定 偽で、偽のとき既存の出力は 1 byte も変わらない)。
#: 「仕掛けを封の commit から変えない」と留めた前の便の門(frozen_problems・触らない file の numstat・記録が読んだ材料の sha256)は、この遷移だけを許す。
#: 許すのは、T5Y の封が履歴に 1 つ在り、numstat・sha16 が下の宣言と同じときだけ(仕掛けの 2 file)。仕掛けの 2 file を触った commit の後に、その commit だけが
#: 触った前の便の門(T5Y の便が宣言の字を足した門)も許す(``t5y_declared_file_change``。履歴で見る)。他の file・他の行数・他の値は今までどおり赤。
T5Y_SEAL_REL = "docs/XBRL_T5_YEN_SEAL_2026-11-06.md"
T5Y_FILES = ("measure/inject.py", "measure/lib/sites.py")
T5Y_NUMSTAT = {"measure/inject.py": ("30", "0"), "measure/lib/sites.py": ("81", "0")}
T5Y_SHA16 = {"measure/inject.py": "d545f1f5a65f1c53", "measure/lib/sites.py": "f26566bda34430ac"}


def t5y_seal_in_history(root=REPO):
    return len(PR.added_commits(root, PREFIX + T5Y_SEAL_REL)) == 1


def t5y_declared_numstat(line, root=REPO, base=ROOT):
    u"""``git diff --numstat`` の 1 行が T5Y の宣言した遷移の行か(封が履歴に在り、行数と作業木の sha16 が宣言と同じ)。"""
    parts = line.split("\t")
    if len(parts) != 3 or not parts[2].startswith(PREFIX):
        return False
    rel = parts[2][len(PREFIX):]
    return (rel in T5Y_NUMSTAT and (parts[0], parts[1]) == T5Y_NUMSTAT[rel] and pb_sha16(rel, base) == T5Y_SHA16[rel] and t5y_seal_in_history(root))


def t5y_pre_transition_sha256(rel, root=REPO, base=ROOT):
    u"""仕掛けの file が T5Y の宣言した遷移の値のとき、その file の遷移の前(T5Y の封の commit の blob)の sha256。遷移していなければ None。
    記録が読んだ材料の sha256(測った時点の値)を、遷移の前の値と照らすために使う。"""
    if rel not in T5Y_FILES or not t5y_seal_in_history(root) or pb_sha16(rel, base) != T5Y_SHA16[rel]:
        return None
    import hashlib
    seal = PR.added_commits(root, PREFIX + T5Y_SEAL_REL)[0]
    blob = subprocess.run(["git", "show", "%s:%s%s" % (seal, PREFIX, rel)], cwd=root, capture_output=True)
    return hashlib.sha256(blob.stdout).hexdigest() if blob.returncode == 0 else None


def t5y_declared_file_change(root, seal_commit, rel, base=ROOT):
    u"""封の commit から ``rel`` が変わったのが、T5Y の宣言した遷移か。仕掛けの 2 file は T5Y の封が履歴に在り作業木の sha16 が宣言の値のとき(commit の前でも)。
    それ以外の file は、T5Y の便の commit(T5Y の封の後に仕掛けの 2 file を最初に触った commit のうち子孫の最後。履歴から探す)が封の commit の後に触り、触った commit が T5Y の便の commit と PB の engine の commit だけで、作業木が HEAD と同じ(commit 済み)のとき。"""
    if rel in T5Y_FILES:
        return t5y_seal_in_history(root) and pb_sha16(rel, base) == T5Y_SHA16[rel]
    s, e = engine_commit(root, PREFIX, T5Y_SEAL_REL, T5Y_FILES)
    if s is None or e is None:
        return False
    log = [c for c in PR.git_in(root, "log", "--format=%H", seal_commit + "..HEAD", "--", PREFIX + rel)[1].split() if c]
    # T5Y の便の commit のほかに、PB の engine の commit(PB の封の後に recipes.py と vocabulary.py を最初に触った commit)も触った前の便の門は、この 2 つの commit だけが触ったときに限り許す
    _pbs, pb_e = engine_commit(root, PREFIX, PB_SEAL_REL, PB_ENGINE_FILES)
    if e not in log or not set(log) <= set(c for c in (e, pb_e) if c):
        return False
    head = subprocess.run(["git", "show", "HEAD:%s%s" % (PREFIX, rel)], cwd=root, capture_output=True)
    if head.returncode != 0:
        return False
    with open(os.path.join(base, rel), "rb") as fh:
        return head.stdout == fh.read()


#: 2026-11-09(T): 封 docs/XBRL_TABLE_PERIOD_ENGINE_SEAL_2026-11-09.md §2-3 が宣言した遷移(司令塔の決定 2026-11-09)。T の engine の commit が recipes.py に +57 行・vocabulary.py に +5 行(削除 0)を足し、
#: 束ねた指紋が T_FP になる。PB の宣言(上の PB_*)と同じ形で、engine を「封の commit から変えない」と留めた後の便の門(この file の frozen_problems・untouched の numstat・記録の頭の engine の指紋を使う便)は、この遷移だけを許す。
#: 許すのは、T の封が履歴に 1 つ在り、numstat・sha16・指紋が下の宣言と同じときだけ。numstat は T だけの行数(PB の engine の commit より後の封から数えた門)と、PB と T の合計(PB より前の封から数えた門。
#: recipes.py 24 + 57、vocabulary.py 5 + 5。PB の封も履歴に在るとき)の 2 通りだけ。他の file・他の行数・他の値は今までどおり赤。
T_SEAL_REL = "docs/XBRL_TABLE_PERIOD_ENGINE_SEAL_2026-11-09.md"
T_ENGINE_FILES = ("adapters/xbrl/recipes.py", "adapters/xbrl/vocabulary.py")
T_NUMSTAT = {"adapters/xbrl/recipes.py": ("57", "0"), "adapters/xbrl/vocabulary.py": ("5", "0")}
T_NUMSTAT_WITH_PB = {"adapters/xbrl/recipes.py": ("81", "0"), "adapters/xbrl/vocabulary.py": ("10", "0")}
T_SHA16 = {"adapters/xbrl/recipes.py": "346adb0d586e3af2", "adapters/xbrl/vocabulary.py": "369891933a5876c4"}
T_FP = "5221d3c9a7bdb5c9833dee52490b0064255bdb54fb3210f1b19c1d19f28f9116"


def t_seal_in_history(root=REPO):
    return len(PR.added_commits(root, PREFIX + T_SEAL_REL)) == 1


def t_declared_numstat(line, root=REPO, base=ROOT):
    u"""``git diff --numstat`` の 1 行が T の宣言した遷移の行か(T の封が履歴に在り、行数と作業木の sha16 が宣言と同じ。PB と T の合計の行数は PB の封も履歴に在るとき)。"""
    parts = line.split("\t")
    if len(parts) != 3 or not parts[2].startswith(PREFIX):
        return False
    rel = parts[2][len(PREFIX):]
    if rel not in T_NUMSTAT or pb_sha16(rel, base) != T_SHA16[rel] or not t_seal_in_history(root):
        return False
    got = (parts[0], parts[1])
    return got == T_NUMSTAT[rel] or (got == T_NUMSTAT_WITH_PB[rel] and pb_seal_in_history(root))


def t_declared_fingerprint(value, root=REPO):
    u"""記録の頭の ``adapter_xbrl_py_sha256`` の値が T の宣言した遷移の値か(T の封が履歴に在るときだけ)。"""
    return value == T_FP and t_seal_in_history(root)


def t_declared_file_change(root, seal_commit, rel, base=ROOT):
    u"""封の commit から ``rel`` が変わったのが、T の engine の commit(T の封の後に recipes.py と vocabulary.py を最初に触った commit のうち子孫の最後。履歴から探す)を含み、
    ほかは PB の engine の commit と T5Y の便の commit だけか(前の便の門を PB・T5Y が足した宣言の字を触っているので、その 3 つの commit が触ってよい)。作業木が HEAD の blob と同じ(commit 済み)ことも見る。"""
    s, e = engine_commit(root, PREFIX, T_SEAL_REL, T_ENGINE_FILES)
    if s is None or e is None:
        return False
    log = [c for c in PR.git_in(root, "log", "--format=%H", seal_commit + "..HEAD", "--", PREFIX + rel)[1].split() if c]
    _pbs, pb_e = engine_commit(root, PREFIX, PB_SEAL_REL, PB_ENGINE_FILES)
    _t5s, t5_e = engine_commit(root, PREFIX, T5Y_SEAL_REL, T5Y_FILES)
    if e not in log or not set(log) <= set(c for c in (e, pb_e, t5_e) if c):
        return False
    head = subprocess.run(["git", "show", "HEAD:%s%s" % (PREFIX, rel)], cwd=root, capture_output=True)
    if head.returncode != 0:
        return False
    with open(os.path.join(base, rel), "rb") as fh:
        return head.stdout == fh.read()


#: 2026-11-17(NRE): 封 docs/XBRL_NIL_READ_ENGINE_SEAL_2026-11-17.md §2-3 が宣言した遷移(司令塔の決定 2026-11-17)。NRE の engine の commit が instance.py の .htm の経路の式 1 行を置き換え(+1 行・-1 行。旗なし)、
#: 束ねた指紋が NRE_FP になる。PB・T の宣言(上の PB_*・T_*)と同じ形で、engine を「封の commit から変えない」と留めた後の便の門(この file の frozen_problems・untouched の numstat・記録の頭の engine の指紋を使う便)は、
#: この遷移だけを許す。許すのは、NRE の封が履歴に 1 つ在り、numstat・sha16・指紋が下の宣言と同じときだけ。numstat は NRE だけの行数(1・1)で、PB・T の封から数えた門でも instance.py の行は 1・1 のまま。
#: 他の file・他の行数・他の値は今までどおり赤。
NRE_SEAL_REL = "docs/XBRL_NIL_READ_ENGINE_SEAL_2026-11-17.md"
NRE_ENGINE_FILES = ("adapters/xbrl/instance.py",)
NRE_NUMSTAT = {"adapters/xbrl/instance.py": ("1", "1")}
NRE_SHA16 = {"adapters/xbrl/instance.py": "1b8c00f86eafe765"}
NRE_FP = "38951626929e7d04b32b1a89586294198087f6fabded4162cd6ef2f14c9c91c0"


def nre_seal_in_history(root=REPO):
    return len(PR.added_commits(root, PREFIX + NRE_SEAL_REL)) == 1


def nre_declared_numstat(line, root=REPO, base=ROOT):
    u"""``git diff --numstat`` の 1 行が NRE の宣言した遷移の行か(NRE の封が履歴に在り、行数 1・1 と作業木の sha16 が宣言と同じ)。"""
    parts = line.split("\t")
    if len(parts) != 3 or not parts[2].startswith(PREFIX):
        return False
    rel = parts[2][len(PREFIX):]
    return (rel in NRE_NUMSTAT and (parts[0], parts[1]) == NRE_NUMSTAT[rel] and pb_sha16(rel, base) == NRE_SHA16[rel] and nre_seal_in_history(root))


def nre_declared_fingerprint(value, root=REPO):
    u"""記録の頭の ``adapter_xbrl_py_sha256`` の値が NRE の宣言した遷移の値か(NRE の封が履歴に在るときだけ)。"""
    return value == NRE_FP and nre_seal_in_history(root)


#: 封 §1 の式の前・後の字(engine の字の中の 1 行の式。literal)。直す前の欠陥の形を試験の中に残すための参照の engine(``nre_old_formula_instance``)が使う
NRE_FORMULA_BEFORE = r"r'<ix:nonFraction([^>]*)>(.*?)</ix:nonFraction>'"
NRE_FORMULA_AFTER = r"r'<ix:nonFraction([^>]*)(?<!/)>(.*?)</ix:nonFraction>'"


def nre_old_formula_instance(src=None, base=ROOT):
    u"""engine の ``instance.py`` の字の中の式を封 §1 の「前」の字に戻した module(memory の中だけ。``sys.modules`` に登録せず・file は書かない)。直す前の欠陥
    (自己閉じの空の欄が次の fact まで読まれる)の形を試験の中に残す参照。「後」の字が 1 回だけ在らなければ AssertionError(式を戻す前提が崩れた)。"""
    if src is None:
        with open(os.path.join(base, NRE_ENGINE_FILES[0]), encoding="utf-8") as fh:
            src = fh.read()
    assert src.count(NRE_FORMULA_AFTER) == 1, u"engine の字に封 §1 の「後」の式が 1 回だけ在らない"
    mod = types.ModuleType("instance_with_the_old_formula_for_nre")
    mod.__file__ = os.path.join(base, NRE_ENGINE_FILES[0])
    exec(compile(src.replace(NRE_FORMULA_AFTER, NRE_FORMULA_BEFORE), mod.__file__, "exec"), mod.__dict__)
    return mod


def nre_record_fingerprint_ok(rec_value, now_value, root=REPO):
    u"""記録の頭の ``adapter_xbrl_py_sha256``(記録を作った時の engine の値)と今の engine の値の関係。同じか、記録が NRE の前の値(T の宣言の値 ``T_FP``。T の後 NRE の前の engine)で、今の値が
    NRE の宣言した遷移の値(封が履歴に在るとき)のどちらか。記録は作り直さない(測った時の値のまま)。他の値の組は今までどおり赤。"""
    return rec_value == now_value or (rec_value == T_FP and nre_declared_fingerprint(now_value, root))


def nre_engine_commits(root=REPO):
    u"""NRE の engine の commit(NRE の封の後に instance.py を最初に触った commit。履歴から探す)を 1 つだけ入れた集合。封か engine の commit が無ければ空。"""
    s, e = engine_commit(root, PREFIX, NRE_SEAL_REL, NRE_ENGINE_FILES)
    return set([e]) if (s is not None and e is not None) else set()


def nre_explained_commit(root, commit, paths, base=ROOT):
    u"""``commit`` が NRE の engine の commit(``nre_engine_commits``)で、``paths``(repo の根からの path の列)への変更が NRE の宣言した遷移の行だけか(``git diff --numstat commit^ commit``)。
    「封の後に engine を触った commit の一覧」を見る門が、その一覧から NRE の engine の commit を外してよいかを決める。他の commit・他の行は外さない。"""
    if commit not in nre_engine_commits(root):
        return False
    rc, txt = PR.git_in(root, "diff", "--numstat", commit + "^", commit, "--", *paths)
    lines = [x for x in txt.splitlines() if x]
    return rc == 0 and bool(lines) and all(nre_declared_numstat(x, root, base) for x in lines)


def nre_declared_file_change(root, seal_commit, rel, base=ROOT):
    u"""封の commit から ``rel`` が変わったのが、NRE の engine の commit を含み、ほかは PB・T5Y・T の commit だけか(前の便の門に NRE の便が宣言の字を足したので、その commit が触ってよい)。
    作業木が HEAD の blob と同じ(commit 済み)ことも見る。"""
    nre = nre_engine_commits(root)
    if not nre:
        return False
    log = [c for c in PR.git_in(root, "log", "--format=%H", seal_commit + "..HEAD", "--", PREFIX + rel)[1].split() if c]
    _pbs, pb_e = engine_commit(root, PREFIX, PB_SEAL_REL, PB_ENGINE_FILES)
    _t5s, t5_e = engine_commit(root, PREFIX, T5Y_SEAL_REL, T5Y_FILES)
    _ts, t_e = engine_commit(root, PREFIX, T_SEAL_REL, T_ENGINE_FILES)
    if not nre <= set(log) or not set(log) <= set(c for c in (pb_e, t5_e, t_e) if c) | nre:
        return False
    head = subprocess.run(["git", "show", "HEAD:%s%s" % (PREFIX, rel)], cwd=root, capture_output=True)
    if head.returncode != 0:
        return False
    with open(os.path.join(base, rel), "rb") as fh:
        return head.stdout == fh.read()


def frozen_problems(rels=READ_ONLY_RELS, root=REPO, base=ROOT, seal_rel=SEAL_REL):
    u"""root = git の木、base = 作業木の audit-core の folder。封の commit の blob と作業木の byte を比べる。"""
    seal = PR.added_commits(root, PREFIX + seal_rel)
    if len(seal) != 1:
        return [u"封の commit が 1 つに決まらない"]
    out = []
    for rel in rels:
        blob = subprocess.run(["git", "show", "%s:%s%s" % (seal[0], PREFIX, rel)], cwd=root, capture_output=True)
        if blob.returncode != 0:
            out.append(u"封の commit に無い: %s" % rel)
            continue
        with open(os.path.join(base, rel), "rb") as fh:
            if blob.stdout != fh.read():
                if pb_declared_file_change(root, seal[0], rel, base):      # 2026-11-06(PB): PB の engine の commit だけが触った file は宣言された遷移
                    continue
                if t5y_declared_file_change(root, seal[0], rel, base):      # 2026-11-06(T5Y): 仕掛けの 2 file と、T5Y の便の commit だけが触った前の便の門は宣言された遷移
                    continue
                if t_declared_file_change(root, seal[0], rel, base):      # 2026-11-09(T): T の engine の commit が触った(PB・T5Y の commit も触ってよい)前の便の門は宣言された遷移
                    continue
                if nre_declared_file_change(root, seal[0], rel, base):      # 2026-11-17(NRE): NRE の engine の commit が触った(PB・T5Y・T の commit も触ってよい)前の便の門は宣言された遷移
                    continue
                out.append(u"封の commit の blob と byte が違う: %s" % rel)
    return out


# ---------------------------------------------------------------- 6. 行頭の名前
def reserved_problems(rels=GATE_RELS, base=ROOT):
    out = []
    for rel in rels:
        with open(os.path.join(base, rel), encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        for n, line in enumerate(lines, 1):
            if any(re.match(r"%s\w*\s*=" % re.escape(p), line) for p in RESERVED_PREFIXES):
                out.append(u"%s:%d が既存の門の数える名前を行頭に置いている" % (rel, n))
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
            mutated = self.seal.replace(ph, ph[:-1] + u"？", 1)
            self.assertNotEqual(mutated, self.seal)
            self.assertNotEqual([], seal_problems(mutated), ph)

    def test_a_3_a_broken_prediction_table_or_missing_section_turns_it_red(self):
        lines = self.seal.split("\n")
        d10 = [i for i, ln in enumerate(lines) if ln.startswith("| D-10 |")]
        self.assertEqual(1, len(d10))
        self.assertNotEqual([], seal_problems("\n".join(lines[:d10[0]] + lines[d10[0] + 1:])))                       # 10 行が 9 行
        d5 = [i for i, ln in enumerate(lines) if ln.startswith("| D-5 |")][0]
        cells = lines[d5].split(" | ")
        self.assertNotEqual([], seal_problems("\n".join(lines[:d5] + [" | ".join(cells[:2]) + " |"] + lines[d5 + 1:])))   # 外れ方の欄が無い
        self.assertNotEqual([], seal_problems("\n".join(lines[:d5] + [" | ".join(cells[:1] + [" "] + cells[2:])] + lines[d5 + 1:])))   # 予測の欄が空
        k5 = [i for i, ln in enumerate(lines) if ln.startswith("- **K-5")]
        self.assertEqual(1, len(k5))
        self.assertNotEqual([], seal_problems("\n".join(lines[:k5[0]] + lines[k5[0] + 1:])))
        self.assertNotEqual([], seal_problems(self.seal.replace("measure/xbrl_rmix_regress97_2026-11-04.py", "measure/x.py")))
        self.assertNotEqual([], seal_problems(self.seal.replace("inject_2026-11-04.json", "inject_x.json")))
        self.assertNotEqual([], seal_problems(self.seal.replace("fixtures/xbrl/rmix/", "fixtures/xbrl/x/")))
        self.assertNotEqual([], seal_problems(self.seal.replace("`adapters/xbrl/comparators.py` | 梯子", "`adapters/xbrl/x.py` | 梯子", 1)))
        self.assertNotEqual([], seal_problems(self.seal.replace("## §4", "## 四", 1)))

    def test_a_4_the_insert_ranges_are_read_from_the_seal(self):
        self.assertEqual({"adapters/xbrl/recipes.py": (12, 20), "adapters/xbrl/vocabulary.py": (6, 10), "adapters/xbrl/comparators.py": (1, 2)}, seal_insert_ranges(self.seal))


class ProfileAndLadderTest(unittest.TestCase):
    def test_b_1_flag_and_profiles(self):
        self.assertEqual([], profile_problems())

    def test_b_2_a_broken_profile_turns_it_red(self):
        from adapters.xbrl import vocabulary as VOC

        def fake(**profiles):
            v = types.SimpleNamespace(Profile=VOC.Profile, DEFAULT_PROFILE=VOC.DEFAULT_PROFILE, PROFILES=dict(VOC.PROFILES))
            v.PROFILES.update(profiles)
            return v
        self.assertEqual([], profile_problems(fake()))
        self.assertNotEqual([], profile_problems(fake(P30E=dataclasses.replace(VOC.P30E, name="P30X"))))
        self.assertNotEqual([], profile_problems(fake(P30E=dataclasses.replace(VOC.P30E, **{FLAG: False}))))
        self.assertNotEqual([], profile_problems(fake(P30E=dataclasses.replace(VOC.P30E, numbers_2026_10_21=False))))                 # P29E の旗を 1 つ外した
        self.assertNotEqual([], profile_problems(fake(P29E=dataclasses.replace(VOC.P29E, **{FLAG: True}))))                           # 既存の profile の旗を真に
        self.assertNotEqual([], profile_problems(fake(P29=dataclasses.replace(VOC.P29, **{FLAG: True}))))
        self.assertNotEqual([], profile_problems(fake(P27=dataclasses.replace(VOC.P27, **{FLAG: True}))))
        self.assertNotEqual([], profile_problems(fake(P30=VOC.P30E)))
        v = fake()
        v.DEFAULT_PROFILE = "P30E"
        self.assertNotEqual([], profile_problems(v))
        names = [f.name for f in dataclasses.fields(VOC.Profile)]
        moved = [n for n in names if n != FLAG]
        moved.insert(moved.index(NEXT_FLAG) + 1, FLAG)                                                                              # 位置が違う
        self.assertNotEqual([], profile_problems(fields=moved))
        self.assertNotEqual([], profile_problems(fields=[n for n in names if n != FLAG]))                                           # 旗の欄が無い
        early = [PREV_FLAG] + [n for n in names if n != PREV_FLAG]
        self.assertNotEqual([], profile_problems(fields=early))                                                                     # N の旗が離れた(RB の旗の直前でない)
        inserted = list(names)
        inserted.insert(inserted.index(NEXT_FLAG), "x_extra_field")
        self.assertNotEqual([], profile_problems(fields=inserted))                                                                  # 旗と written_precision の間に別の欄が入った
        swapped = [n for n in names if n not in (FLAG, PREV_FLAG)]
        swapped.insert(swapped.index(NEXT_FLAG), PREV_FLAG)
        swapped.insert(swapped.index(PREV_FLAG), FLAG)                                                                              # RB の旗が N の旗の前
        self.assertNotEqual([], profile_problems(fields=swapped))

    def test_b_3_the_ladder_treats_both_as_none_in_both_modules(self):
        self.assertEqual([], ladder_problems())
        self.assertEqual([], probe_problems())

    def test_b_3b_the_probe_sees_a_grid_that_cannot_tell_the_modes_apart(self):
        from adapters.xbrl import vocabulary as VOC
        ignore_mode = probe_problems((("v", lambda fv, t, u, mode=None: VOC.match_value(fv, t, u, None)),))                          # mode を見ない関数は None が round とも truncate とも同じ
        self.assertTrue(any(u"\"round\"" in x for x in ignore_mode) and any(u"\"truncate\"" in x for x in ignore_mode))
        round_like = probe_problems((("v", lambda fv, t, u, mode=None: VOC.match_value(fv, t, u, "round" if mode is None else mode)),))     # None を四捨五入として扱う関数: None と round が同じ
        self.assertEqual([False, True], [any(u"\"truncate\"" in x for x in round_like), any(u"\"round\"" in x for x in round_like)])
        trunc_like = probe_problems((("v", lambda fv, t, u, mode=None: VOC.match_value(fv, t, u, "truncate" if mode is None else mode)),))  # None を切り捨てとして扱う関数
        self.assertEqual([True, False], [any(u"\"truncate\"" in x for x in trunc_like), any(u"\"round\"" in x for x in trunc_like)])

    def test_b_4_a_broken_ladder_turns_it_red(self):
        from adapters.xbrl import vocabulary as VOC
        good = VOC.match_value
        self.assertNotEqual([], ladder_problems((("v", lambda fv, t, u, mode=None: good(fv, t, u, "round" if mode == "both" else mode)),)))          # "both" を round として扱う
        self.assertNotEqual([], ladder_problems((("v", lambda fv, t, u, mode=None: good(fv, t, u, "truncate" if mode == "both" else mode)),)))       # "both" を truncate として扱う
        self.assertNotEqual([], ladder_problems((("v", lambda fv, t, u, mode=None: good(fv, t, u, mode) if mode != "both" else None),)))            # "both" で何も当たらない
        self.assertEqual([], ladder_problems((("v", good),)))


class EngineAndFrozenTest(unittest.TestCase):
    def test_c_1_engine_changes_are_the_three_files_and_no_deletions(self):
        self.assertEqual([], real_numstat_problems())

    def test_c_2_numstat_mutations_turn_it_red(self):
        rng = {"adapters/xbrl/recipes.py": (12, 20), "adapters/xbrl/vocabulary.py": (6, 10), "adapters/xbrl/comparators.py": (1, 2)}
        good = ["18\t0\t%sadapters/xbrl/recipes.py" % PREFIX, "7\t0\t%sadapters/xbrl/vocabulary.py" % PREFIX, "2\t0\t%sadapters/xbrl/comparators.py" % PREFIX]
        self.assertEqual([], numstat_problems(good, rng))
        self.assertNotEqual([], numstat_problems(good[:2], rng))
        self.assertNotEqual([], numstat_problems(good + ["1\t0\t%sadapters/xbrl/extract.py" % PREFIX], rng))
        self.assertNotEqual([], numstat_problems(good + ["1\t0\t%score/py/audit_core/x.py" % PREFIX], rng))
        self.assertNotEqual([], numstat_problems(["18\t1\t%sadapters/xbrl/recipes.py" % PREFIX] + good[1:], rng))
        self.assertNotEqual([], numstat_problems(["21\t0\t%sadapters/xbrl/recipes.py" % PREFIX] + good[1:], rng))      # 封の見込みの上の外
        self.assertNotEqual([], numstat_problems(good[:2] + ["3\t0\t%sadapters/xbrl/comparators.py" % PREFIX], rng))
        self.assertNotEqual([], numstat_problems(["11\t0\t%sadapters/xbrl/recipes.py" % PREFIX] + good[1:], rng))      # 下の外

    def test_d_1_previous_scripts_and_records_are_byte_identical_to_the_seal_commit(self):
        self.assertEqual([], frozen_problems())

    def test_d_2_the_frozen_check_sees_a_changed_file_and_a_missing_one(self):
        self.assertNotEqual([], frozen_problems(rels=READ_ONLY_RELS + ("measure/xbrl_rmix_2026-11-04.py",)))     # 封の commit に無い file
        self.assertNotEqual([], frozen_problems(rels=("tests/measure/test_xbrl_rmix_seal.py",)))

    def test_d_3_the_frozen_check_goes_red_when_a_tracked_file_changes_after_the_seal(self):
        r = PR.Repo()
        r.put("measure/prev.py")
        r.put(SEAL_REL)
        r.commit("measure/prev.py", SEAL_REL)
        base = os.path.join(r.d, "audit-core")
        self.assertEqual([], frozen_problems(rels=("measure/prev.py",), root=r.d, base=base))
        with open(os.path.join(base, "measure/prev.py"), "a", encoding="utf-8") as fh:
            fh.write("x = 1\n")
        self.assertEqual([u"封の commit の blob と byte が違う: measure/prev.py"], frozen_problems(rels=("measure/prev.py",), root=r.d, base=base))
        r.put("measure/later.py")
        r.commit("measure/later.py")
        self.assertEqual(["封の commit に無い: measure/later.py"], frozen_problems(rels=("measure/later.py",), root=r.d, base=base))

    def test_e_1_gate_files_do_not_use_the_reserved_names(self):
        self.assertEqual([], reserved_problems(rels=tuple(r for r in GATE_RELS if os.path.exists(os.path.join(ROOT, r)))))

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
            self.assertIn("XBRL_ROUNDING_MIXED_ENGINE_SEAL_2026-11-04.md", read(rel), rel)


class PbTransitionTest(unittest.TestCase):
    u"""2026-11-06(PB): 後の便の門が使う「PB の宣言された遷移」の部品(``pb_declared_numstat``・``pb_declared_fingerprint``・``pb_declared_file_change``)。許すのは宣言の字だけで、他は赤。"""

    REC = "%sadapters/xbrl/recipes.py" % PREFIX
    VOC = "%sadapters/xbrl/vocabulary.py" % PREFIX

    def test_pb_1_the_declared_numstat_lines_are_accepted_in_this_repo(self):
        # 2026-11-09(T): T の engine の commit が recipes.py・vocabulary.py をもう一度動かしたので、作業木の sha16 は PB の値でなくなった。
        # PB の宣言は「PB の engine の commit の blob」で確かめる(PB の engine の commit を履歴から探し、その blob を使い捨ての folder に出す)。
        self.assertTrue(pb_seal_in_history())
        _s, e = engine_commit(REPO, PREFIX, PB_SEAL_REL, PB_ENGINE_FILES)
        self.assertTrue(e)
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            for rel in PB_ENGINE_FILES:
                blob = subprocess.run(["git", "show", "%s:%s%s" % (e, PREFIX, rel)], cwd=REPO, capture_output=True)
                self.assertEqual(0, blob.returncode)
                os.makedirs(os.path.dirname(os.path.join(d, rel)), exist_ok=True)
                with open(os.path.join(d, rel), "wb") as fh:
                    fh.write(blob.stdout)
            self.assertTrue(pb_declared_numstat("24\t0\t" + self.REC, base=d))
            self.assertTrue(pb_declared_numstat("5\t0\t" + self.VOC, base=d))
            self.assertEqual(PB_SHA16["adapters/xbrl/recipes.py"], pb_sha16("adapters/xbrl/recipes.py", base=d))
            self.assertEqual(PB_SHA16["adapters/xbrl/vocabulary.py"], pb_sha16("adapters/xbrl/vocabulary.py", base=d))
        # いまの作業木は T の値(PB の値ではない)なので、PB の宣言の行は受け入れない(T の宣言の行は下の TTransitionTest)
        self.assertFalse(pb_declared_numstat("24\t0\t" + self.REC))
        self.assertFalse(pb_declared_numstat("5\t0\t" + self.VOC))

    def test_pb_2_any_other_numstat_line_is_not_accepted(self):
        for bad in ("25\t0\t" + self.REC, "24\t1\t" + self.REC, "23\t0\t" + self.REC, "6\t0\t" + self.VOC, "5\t1\t" + self.VOC,
                    "24\t0\t%sadapters/xbrl/comparators.py" % PREFIX, "24\t0\t%sadapters/xbrl/extract.py" % PREFIX, "2\t0\t%smeasure/inject.py" % PREFIX,
                    "24\t0\t%score/py/audit_core/verify.py" % PREFIX, "24\t0\tadapters/xbrl/recipes.py", "24\t0", ""):
            self.assertFalse(pb_declared_numstat(bad), bad)

    def test_pb_3_a_file_that_is_not_the_declared_sha16_is_not_accepted(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            os.makedirs(os.path.join(d, "adapters", "xbrl"))
            for rel in PB_ENGINE_FILES:
                with open(os.path.join(d, rel), "w", encoding="utf-8") as fh:
                    fh.write("x = 1\n")
            self.assertFalse(pb_declared_numstat("24\t0\t" + self.REC, base=d))
            self.assertFalse(pb_declared_numstat("5\t0\t" + self.VOC, base=d))

    def test_pb_4_without_the_pb_seal_in_history_nothing_is_accepted(self):
        r = PR.Repo()
        r.put("measure/prev.py")
        r.commit("measure/prev.py")
        self.assertFalse(pb_seal_in_history(r.d))
        self.assertFalse(pb_declared_numstat("24\t0\t" + self.REC, root=r.d))
        self.assertFalse(pb_declared_fingerprint(PB_FP, root=r.d))

    def test_pb_5_only_the_declared_fingerprint_is_accepted(self):
        self.assertTrue(pb_declared_fingerprint(PB_FP))
        self.assertFalse(pb_declared_fingerprint(PB_FP[:-1] + "0"))
        self.assertFalse(pb_declared_fingerprint("4ea77c93b9521e634dc0ec2c445917e86793e6f6e8460ac9d69a302d925c2611"))
        self.assertFalse(pb_declared_fingerprint(None))

    def _repo(self, extra_commit=False, dirty=False, engine=True):
        u"""封(前の便の file を足す)→ PB の封 → (engine の commit = recipes・vocabulary と前の便の file を触る)→ ..."""
        r = PR.Repo()
        r.put("measure/gate.py")
        r.put(SEAL_REL)
        seal = r.commit("measure/gate.py", SEAL_REL)
        r.put(PB_SEAL_REL)
        r.commit(PB_SEAL_REL)
        r.put("adapters/xbrl/recipes.py")
        r.put("adapters/xbrl/vocabulary.py")
        r.put("measure/gate.py")
        files = ["measure/gate.py"] + (list(PB_ENGINE_FILES) if engine else [])
        e = r.commit(*files)
        if extra_commit:
            r.put("measure/gate.py")
            r.commit("measure/gate.py")
        if dirty:
            r.put("measure/gate.py")
        return r, seal, e

    def test_pb_6_a_file_changed_only_by_the_engine_commit_is_accepted(self):
        r, seal, e = self._repo()
        self.assertTrue(pb_declared_file_change(r.d, seal, "measure/gate.py", base=os.path.join(r.d, "audit-core")))
        self.assertEqual([], frozen_problems(rels=("measure/gate.py",), root=r.d, base=os.path.join(r.d, "audit-core")))

    def test_pb_7_a_file_changed_again_after_the_engine_commit_is_not_accepted(self):
        r, seal, e = self._repo(extra_commit=True)
        self.assertFalse(pb_declared_file_change(r.d, seal, "measure/gate.py", base=os.path.join(r.d, "audit-core")))
        self.assertEqual([u"封の commit の blob と byte が違う: measure/gate.py"], frozen_problems(rels=("measure/gate.py",), root=r.d, base=os.path.join(r.d, "audit-core")))

    def test_pb_8_an_uncommitted_change_is_not_accepted(self):
        r, seal, e = self._repo(dirty=True)
        self.assertFalse(pb_declared_file_change(r.d, seal, "measure/gate.py", base=os.path.join(r.d, "audit-core")))

    def test_pb_9_a_change_by_a_commit_that_does_not_touch_the_engine_is_not_accepted(self):
        r, seal, e = self._repo(engine=False)
        self.assertFalse(pb_declared_file_change(r.d, seal, "measure/gate.py", base=os.path.join(r.d, "audit-core")))
        self.assertNotEqual([], frozen_problems(rels=("measure/gate.py",), root=r.d, base=os.path.join(r.d, "audit-core")))

    def test_pb_10_a_file_changed_before_the_pb_seal_is_not_accepted(self):
        r = PR.Repo()
        r.put("measure/gate.py")
        r.put(SEAL_REL)
        seal = r.commit("measure/gate.py", SEAL_REL)
        r.put("measure/gate.py")
        r.commit("measure/gate.py")
        r.put(PB_SEAL_REL)
        r.commit(PB_SEAL_REL)
        r.put("adapters/xbrl/recipes.py")
        r.put("adapters/xbrl/vocabulary.py")
        r.commit(*PB_ENGINE_FILES)
        self.assertFalse(pb_declared_file_change(r.d, seal, "measure/gate.py", base=os.path.join(r.d, "audit-core")))


class T5yTransitionTest(unittest.TestCase):
    u"""2026-11-06(T5Y): 後の便の門が使う「T5Y の宣言された遷移」の部品(``t5y_declared_numstat``・``t5y_pre_transition_sha256``・``t5y_declared_file_change``)。許すのは宣言の字だけで、他は赤。"""

    INJ = "%smeasure/inject.py" % PREFIX
    SIT = "%smeasure/lib/sites.py" % PREFIX

    def test_t5y_1_the_declared_numstat_lines_are_accepted_in_this_repo(self):
        self.assertTrue(t5y_seal_in_history())
        self.assertTrue(t5y_declared_numstat("30\t0\t" + self.INJ))
        self.assertTrue(t5y_declared_numstat("81\t0\t" + self.SIT))
        for rel in T5Y_FILES:
            self.assertEqual(T5Y_SHA16[rel], pb_sha16(rel))

    def test_t5y_2_any_other_numstat_line_is_not_accepted(self):
        for bad in ("31\t0\t" + self.INJ, "30\t1\t" + self.INJ, "29\t0\t" + self.INJ, "82\t0\t" + self.SIT, "81\t1\t" + self.SIT,
                    "81\t0\t%smeasure/lib/numbers.py" % PREFIX, "30\t0\t%smeasure/xbrl_t5y_2026-11-06.py" % PREFIX, "24\t0\t%sadapters/xbrl/recipes.py" % PREFIX,
                    "30\t0\tmeasure/inject.py", "30\t0", ""):
            self.assertFalse(t5y_declared_numstat(bad), bad)

    def test_t5y_3_a_file_that_is_not_the_declared_sha16_is_not_accepted(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            os.makedirs(os.path.join(d, "measure", "lib"))
            for rel in T5Y_FILES:
                with open(os.path.join(d, rel), "w", encoding="utf-8") as fh:
                    fh.write("x = 1\n")
            self.assertFalse(t5y_declared_numstat("30\t0\t" + self.INJ, base=d))
            self.assertFalse(t5y_declared_numstat("81\t0\t" + self.SIT, base=d))
            for rel in T5Y_FILES:
                self.assertFalse(t5y_declared_file_change(REPO, "0" * 40, rel, base=d), rel)
                self.assertIsNone(t5y_pre_transition_sha256(rel, base=d), rel)

    def test_t5y_4_without_the_t5y_seal_in_history_nothing_is_accepted(self):
        r = PR.Repo()
        r.put("measure/prev.py")
        r.commit("measure/prev.py")
        self.assertFalse(t5y_seal_in_history(r.d))
        self.assertFalse(t5y_declared_numstat("30\t0\t" + self.INJ, root=r.d))
        for rel in T5Y_FILES:
            self.assertFalse(t5y_declared_file_change(r.d, "0" * 40, rel), rel)
            self.assertIsNone(t5y_pre_transition_sha256(rel, root=r.d), rel)

    def test_t5y_5_the_pre_transition_sha256_is_the_blob_at_the_t5y_seal_commit(self):
        import hashlib
        seal = PR.added_commits(REPO, PREFIX + T5Y_SEAL_REL)[0]
        for rel in T5Y_FILES:
            blob = subprocess.run(["git", "show", "%s:%s%s" % (seal, PREFIX, rel)], cwd=REPO, capture_output=True).stdout
            self.assertEqual(hashlib.sha256(blob).hexdigest(), t5y_pre_transition_sha256(rel))
            with open(os.path.join(ROOT, rel), "rb") as fh:
                self.assertNotEqual(hashlib.sha256(fh.read()).hexdigest(), t5y_pre_transition_sha256(rel))      # 遷移の前と後は別の byte
        self.assertIsNone(t5y_pre_transition_sha256("measure/xbrl_rmix_2026-11-04.py"))                           # 仕掛けの 2 file 以外は None

    def _repo(self, extra_commit=False, dirty=False, touch_device=True, seal_first=True):
        u"""封 → T5Y の封 → (T5Y の便の commit = 仕掛けの 2 file と前の便の門を触る)→ ..."""
        r = PR.Repo()
        r.put("measure/gate.py")
        r.put(SEAL_REL)
        seal = r.commit("measure/gate.py", SEAL_REL)
        r.put(T5Y_SEAL_REL)
        r.commit(T5Y_SEAL_REL)
        for rel in T5Y_FILES:
            r.put(rel)
        r.put("measure/gate.py")
        files = ["measure/gate.py"] + (list(T5Y_FILES) if touch_device else [])
        e = r.commit(*files)
        if extra_commit:
            r.put("measure/gate.py")
            r.commit("measure/gate.py")
        if dirty:
            r.put("measure/gate.py")
        return r, seal, e

    def test_t5y_6_a_gate_changed_only_by_the_t5y_commit_is_accepted(self):
        r, seal, e = self._repo()
        base = os.path.join(r.d, "audit-core")
        self.assertTrue(t5y_declared_file_change(r.d, seal, "measure/gate.py", base=base))
        self.assertEqual([], frozen_problems(rels=("measure/gate.py",), root=r.d, base=base))

    def test_t5y_7_a_gate_changed_again_after_the_t5y_commit_is_not_accepted(self):
        r, seal, e = self._repo(extra_commit=True)
        base = os.path.join(r.d, "audit-core")
        self.assertFalse(t5y_declared_file_change(r.d, seal, "measure/gate.py", base=base))
        self.assertEqual([u"封の commit の blob と byte が違う: measure/gate.py"], frozen_problems(rels=("measure/gate.py",), root=r.d, base=base))

    def test_t5y_8_an_uncommitted_change_is_not_accepted(self):
        r, seal, e = self._repo(dirty=True)
        self.assertFalse(t5y_declared_file_change(r.d, seal, "measure/gate.py", base=os.path.join(r.d, "audit-core")))

    def test_t5y_9_a_change_by_a_commit_that_does_not_touch_the_device_is_not_accepted(self):
        r, seal, e = self._repo(touch_device=False)
        base = os.path.join(r.d, "audit-core")
        self.assertFalse(t5y_declared_file_change(r.d, seal, "measure/gate.py", base=base))
        self.assertNotEqual([], frozen_problems(rels=("measure/gate.py",), root=r.d, base=base))

    def test_t5y_10_a_file_changed_before_the_t5y_seal_is_not_accepted(self):
        r = PR.Repo()
        r.put("measure/gate.py")
        r.put(SEAL_REL)
        seal = r.commit("measure/gate.py", SEAL_REL)
        r.put("measure/gate.py")
        r.commit("measure/gate.py")
        r.put(T5Y_SEAL_REL)
        r.commit(T5Y_SEAL_REL)
        for rel in T5Y_FILES:
            r.put(rel)
        r.commit(*T5Y_FILES)
        self.assertFalse(t5y_declared_file_change(r.d, seal, "measure/gate.py", base=os.path.join(r.d, "audit-core")))

    def _repo_pb_then_t5y(self, other_between=False, pb_after_t5y=False):
        u"""封 → PB の封 → PB の engine の commit(前の便の門を触る)→ (他の commit)→ T5Y の封 → T5Y の便の commit(同じ門を触る)。"""
        r = PR.Repo()
        r.put("measure/gate.py")
        r.put(SEAL_REL)
        seal = r.commit("measure/gate.py", SEAL_REL)
        r.put(PB_SEAL_REL)
        r.commit(PB_SEAL_REL)
        for rel in PB_ENGINE_FILES:
            r.put(rel)
        r.put("measure/gate.py")
        r.commit("measure/gate.py", *PB_ENGINE_FILES)
        if other_between:
            r.put("measure/gate.py")
            r.commit("measure/gate.py")
        r.put(T5Y_SEAL_REL)
        r.commit(T5Y_SEAL_REL)
        for rel in T5Y_FILES:
            r.put(rel)
        r.put("measure/gate.py")
        r.commit("measure/gate.py", *T5Y_FILES)
        return r, seal

    def test_t5y_11_a_gate_changed_by_the_pb_commit_and_then_the_t5y_commit_is_accepted(self):
        r, seal = self._repo_pb_then_t5y()
        base = os.path.join(r.d, "audit-core")
        self.assertTrue(t5y_declared_file_change(r.d, seal, "measure/gate.py", base=base))
        self.assertEqual([], frozen_problems(rels=("measure/gate.py",), root=r.d, base=base))

    def test_t5y_12_a_gate_also_changed_by_another_commit_between_is_not_accepted(self):
        r, seal = self._repo_pb_then_t5y(other_between=True)
        base = os.path.join(r.d, "audit-core")
        self.assertFalse(t5y_declared_file_change(r.d, seal, "measure/gate.py", base=base))
        self.assertNotEqual([], frozen_problems(rels=("measure/gate.py",), root=r.d, base=base))

    def test_t5y_12b_a_gate_changed_only_by_the_pb_commit_is_not_a_t5y_transition(self):
        r = PR.Repo()
        r.put("measure/gate.py")
        r.put(SEAL_REL)
        seal = r.commit("measure/gate.py", SEAL_REL)
        r.put(PB_SEAL_REL)
        r.commit(PB_SEAL_REL)
        for rel in PB_ENGINE_FILES:
            r.put(rel)
        r.put("measure/gate.py")
        r.commit("measure/gate.py", *PB_ENGINE_FILES)
        r.put(T5Y_SEAL_REL)
        r.commit(T5Y_SEAL_REL)
        for rel in T5Y_FILES:
            r.put(rel)
        r.commit(*T5Y_FILES)
        base = os.path.join(r.d, "audit-core")
        self.assertTrue(pb_declared_file_change(r.d, seal, "measure/gate.py", base=base))                 # PB の遷移としては許す
        self.assertFalse(t5y_declared_file_change(r.d, seal, "measure/gate.py", base=base))               # T5Y の遷移とは言わない

    def test_t5y_12c_an_uncommitted_change_after_the_pb_and_t5y_commits_is_not_accepted(self):
        r, seal = self._repo_pb_then_t5y()
        r.put("measure/gate.py")
        self.assertFalse(t5y_declared_file_change(r.d, seal, "measure/gate.py", base=os.path.join(r.d, "audit-core")))

    def test_t5y_13_the_pb_and_t5y_transitions_do_not_accept_each_other_files(self):
        self.assertFalse(t5y_declared_numstat("24\t0\t%sadapters/xbrl/recipes.py" % PREFIX))
        self.assertFalse(pb_declared_numstat("30\t0\t" + self.INJ))
        self.assertFalse(pb_declared_numstat("81\t0\t" + self.SIT))


class TTransitionTest(unittest.TestCase):
    u"""2026-11-09(T): 後の便の門が使う「T の宣言された遷移」の部品(``t_declared_numstat``・``t_declared_fingerprint``・``t_declared_file_change``)。許すのは宣言の字だけで、他は赤。"""

    REC = "%sadapters/xbrl/recipes.py" % PREFIX
    VOC = "%sadapters/xbrl/vocabulary.py" % PREFIX

    def test_t_1_the_declared_numstat_lines_are_accepted_in_this_repo(self):
        self.assertTrue(t_seal_in_history())
        self.assertTrue(pb_seal_in_history())
        for ln in ("57\t0\t" + self.REC, "5\t0\t" + self.VOC, "81\t0\t" + self.REC, "10\t0\t" + self.VOC):
            self.assertTrue(t_declared_numstat(ln), ln)
        for rel in T_ENGINE_FILES:
            self.assertEqual(T_SHA16[rel], pb_sha16(rel))

    def test_t_2_any_other_numstat_line_is_not_accepted(self):
        for bad in ("58\t0\t" + self.REC, "56\t0\t" + self.REC, "57\t1\t" + self.REC, "80\t0\t" + self.REC, "82\t0\t" + self.REC, "24\t0\t" + self.REC,
                    "6\t0\t" + self.VOC, "4\t0\t" + self.VOC, "5\t1\t" + self.VOC, "11\t0\t" + self.VOC, "57\t0\t" + self.VOC, "5\t0\t" + self.REC,
                    "57\t0\t%sadapters/xbrl/comparators.py" % PREFIX, "57\t0\t%sadapters/xbrl/extract.py" % PREFIX, "5\t0\t%smeasure/inject.py" % PREFIX,
                    "57\t0\t%score/py/audit_core/verify.py" % PREFIX, "57\t0\tadapters/xbrl/recipes.py", "57\t0", ""):
            self.assertFalse(t_declared_numstat(bad), bad)

    def test_t_3_a_file_that_is_not_the_declared_sha16_is_not_accepted(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            os.makedirs(os.path.join(d, "adapters", "xbrl"))
            for rel in T_ENGINE_FILES:
                with open(os.path.join(d, rel), "w", encoding="utf-8") as fh:
                    fh.write("x = 1\n")
            self.assertFalse(t_declared_numstat("57\t0\t" + self.REC, base=d))
            self.assertFalse(t_declared_numstat("5\t0\t" + self.VOC, base=d))
            self.assertFalse(t_declared_numstat("81\t0\t" + self.REC, base=d))

    def test_t_4_without_the_t_seal_in_history_nothing_is_accepted(self):
        r = PR.Repo()
        r.put("measure/prev.py")
        r.commit("measure/prev.py")
        self.assertFalse(t_seal_in_history(r.d))
        self.assertFalse(t_declared_numstat("57\t0\t" + self.REC, root=r.d))
        self.assertFalse(t_declared_fingerprint(T_FP, root=r.d))

    def test_t_4b_the_sum_with_pb_needs_the_pb_seal_in_history_too(self):
        r = PR.Repo()
        r.put(T_SEAL_REL)
        r.commit(T_SEAL_REL)
        self.assertTrue(t_seal_in_history(r.d))
        self.assertFalse(pb_seal_in_history(r.d))
        self.assertTrue(t_declared_numstat("57\t0\t" + self.REC, root=r.d))
        self.assertFalse(t_declared_numstat("81\t0\t" + self.REC, root=r.d))
        self.assertFalse(t_declared_numstat("10\t0\t" + self.VOC, root=r.d))

    def test_t_5_only_the_declared_fingerprint_is_accepted(self):
        self.assertTrue(t_declared_fingerprint(T_FP))
        self.assertFalse(t_declared_fingerprint(T_FP[:-1] + "0"))
        self.assertFalse(t_declared_fingerprint(PB_FP))
        self.assertFalse(t_declared_fingerprint("4ea77c93b9521e634dc0ec2c445917e86793e6f6e8460ac9d69a302d925c2611"))
        self.assertFalse(t_declared_fingerprint(None))

    def _repo(self, extra_commit=False, dirty=False, engine=True, with_pb=False, pb_gate=True, t5y_between=False, other_between=False):
        u"""封 →(PB の封 → PB の engine の commit)→(T5Y の封 → T5Y の便の commit)→ T の封 → (T の engine の commit = recipes・vocabulary と前の便の file を触る)→ ..."""
        r = PR.Repo()
        r.put("measure/gate.py")
        r.put(SEAL_REL)
        seal = r.commit("measure/gate.py", SEAL_REL)
        if with_pb:
            r.put(PB_SEAL_REL)
            r.commit(PB_SEAL_REL)
            for rel in PB_ENGINE_FILES:
                r.put(rel)
            if pb_gate:
                r.put("measure/gate.py")
            r.commit(*(list(PB_ENGINE_FILES) + (["measure/gate.py"] if pb_gate else [])))
        if t5y_between:
            r.put(T5Y_SEAL_REL)
            r.commit(T5Y_SEAL_REL)
            for rel in T5Y_FILES:
                r.put(rel)
            r.put("measure/gate.py")
            r.commit("measure/gate.py", *T5Y_FILES)
        if other_between:
            r.put("measure/gate.py")
            r.commit("measure/gate.py")
        r.put(T_SEAL_REL)
        r.commit(T_SEAL_REL)
        for rel in T_ENGINE_FILES:
            r.put(rel)
        r.put("measure/gate.py")
        files = ["measure/gate.py"] + (list(T_ENGINE_FILES) if engine else [])
        e = r.commit(*files)
        if extra_commit:
            r.put("measure/gate.py")
            r.commit("measure/gate.py")
        if dirty:
            r.put("measure/gate.py")
        return r, seal, e

    def _base(self, r):
        return os.path.join(r.d, "audit-core")

    def test_t_6_a_file_changed_only_by_the_t_engine_commit_is_accepted(self):
        r, seal, e = self._repo()
        self.assertTrue(t_declared_file_change(r.d, seal, "measure/gate.py", base=self._base(r)))
        self.assertEqual([], frozen_problems(rels=("measure/gate.py",), root=r.d, base=self._base(r)))

    def test_t_7_a_file_changed_again_after_the_t_engine_commit_is_not_accepted(self):
        r, seal, e = self._repo(extra_commit=True)
        self.assertFalse(t_declared_file_change(r.d, seal, "measure/gate.py", base=self._base(r)))
        self.assertEqual([u"封の commit の blob と byte が違う: measure/gate.py"], frozen_problems(rels=("measure/gate.py",), root=r.d, base=self._base(r)))

    def test_t_8_an_uncommitted_change_is_not_accepted(self):
        r, seal, e = self._repo(dirty=True)
        self.assertFalse(t_declared_file_change(r.d, seal, "measure/gate.py", base=self._base(r)))

    def test_t_9_a_change_by_a_commit_that_does_not_touch_the_engine_is_not_accepted(self):
        r, seal, e = self._repo(engine=False)
        self.assertFalse(t_declared_file_change(r.d, seal, "measure/gate.py", base=self._base(r)))
        self.assertNotEqual([], frozen_problems(rels=("measure/gate.py",), root=r.d, base=self._base(r)))

    def test_t_10_a_file_changed_before_the_t_seal_is_not_accepted(self):
        r = PR.Repo()
        r.put("measure/gate.py")
        r.put(SEAL_REL)
        seal = r.commit("measure/gate.py", SEAL_REL)
        r.put("measure/gate.py")
        r.commit("measure/gate.py")
        r.put(T_SEAL_REL)
        r.commit(T_SEAL_REL)
        for rel in T_ENGINE_FILES:
            r.put(rel)
        r.commit(*T_ENGINE_FILES)
        self.assertFalse(t_declared_file_change(r.d, seal, "measure/gate.py", base=self._base(r)))

    def test_t_11_a_gate_changed_by_the_pb_commit_and_then_the_t_commit_is_accepted(self):
        r, seal, e = self._repo(with_pb=True)
        self.assertTrue(t_declared_file_change(r.d, seal, "measure/gate.py", base=self._base(r)))
        self.assertEqual([], frozen_problems(rels=("measure/gate.py",), root=r.d, base=self._base(r)))

    def test_t_12_a_gate_changed_by_the_pb_t5y_and_t_commits_is_accepted(self):
        r, seal, e = self._repo(with_pb=True, t5y_between=True)
        self.assertTrue(t_declared_file_change(r.d, seal, "measure/gate.py", base=self._base(r)))
        self.assertEqual([], frozen_problems(rels=("measure/gate.py",), root=r.d, base=self._base(r)))

    def test_t_13_a_gate_also_changed_by_another_commit_between_is_not_accepted(self):
        r, seal, e = self._repo(with_pb=True, other_between=True)
        self.assertFalse(t_declared_file_change(r.d, seal, "measure/gate.py", base=self._base(r)))
        self.assertNotEqual([], frozen_problems(rels=("measure/gate.py",), root=r.d, base=self._base(r)))
        r2, seal2, e2 = self._repo(other_between=True)
        self.assertFalse(t_declared_file_change(r2.d, seal2, "measure/gate.py", base=self._base(r2)))

    def test_t_14_a_gate_changed_only_by_the_pb_commit_is_not_a_t_transition(self):
        r = PR.Repo()
        r.put("measure/gate.py")
        r.put(SEAL_REL)
        seal = r.commit("measure/gate.py", SEAL_REL)
        r.put(PB_SEAL_REL)
        r.commit(PB_SEAL_REL)
        for rel in PB_ENGINE_FILES:
            r.put(rel)
        r.put("measure/gate.py")
        r.commit("measure/gate.py", *PB_ENGINE_FILES)
        r.put(T_SEAL_REL)
        r.commit(T_SEAL_REL)
        for rel in T_ENGINE_FILES:
            r.put(rel)
        r.commit(*T_ENGINE_FILES)
        base = self._base(r)
        self.assertTrue(pb_declared_file_change(r.d, seal, "measure/gate.py", base=base))                 # PB の遷移としては許す
        self.assertFalse(t_declared_file_change(r.d, seal, "measure/gate.py", base=base))                 # T の遷移とは言わない

    def test_t_15_an_uncommitted_change_after_the_pb_and_t_commits_is_not_accepted(self):
        r, seal, e = self._repo(with_pb=True)
        r.put("measure/gate.py")
        self.assertFalse(t_declared_file_change(r.d, seal, "measure/gate.py", base=self._base(r)))

    def test_t_16_the_pb_t5y_and_t_transitions_do_not_accept_each_other_lines(self):
        self.assertFalse(pb_declared_numstat("57\t0\t" + self.REC))
        self.assertFalse(t5y_declared_numstat("57\t0\t" + self.REC))
        self.assertFalse(t_declared_numstat("30\t0\t%smeasure/inject.py" % PREFIX))
        self.assertFalse(t_declared_numstat("81\t0\t%smeasure/lib/sites.py" % PREFIX))


class NreTransitionTest(unittest.TestCase):
    u"""2026-11-17(NRE): 後の便の門が使う「NRE の宣言された遷移」の部品(``nre_declared_numstat``・``nre_declared_fingerprint``・``nre_declared_file_change``)。許すのは宣言の字だけで、他は赤。"""

    INST = "%sadapters/xbrl/instance.py" % PREFIX
    REC = "%sadapters/xbrl/recipes.py" % PREFIX

    def test_n_1_the_declared_numstat_line_is_accepted_in_this_repo(self):
        self.assertTrue(nre_seal_in_history())
        self.assertTrue(nre_declared_numstat("1\t1\t" + self.INST))
        for rel in NRE_ENGINE_FILES:
            self.assertEqual(NRE_SHA16[rel], pb_sha16(rel))

    def test_n_2_any_other_numstat_line_is_not_accepted(self):
        for bad in ("2\t1\t" + self.INST, "1\t2\t" + self.INST, "1\t0\t" + self.INST, "0\t1\t" + self.INST, "0\t0\t" + self.INST, "1\t1\t" + self.REC, "1\t1\t%sadapters/xbrl/extract.py" % PREFIX,
                    "1\t1\t%sadapters/xbrl/vocabulary.py" % PREFIX, "1\t1\t%score/py/audit_core/verify.py" % PREFIX, "1\t1\t%smeasure/inject.py" % PREFIX, "1\t1\tadapters/xbrl/instance.py", "1\t1", ""):
            self.assertFalse(nre_declared_numstat(bad), bad)

    def test_n_3_a_file_that_is_not_the_declared_sha16_is_not_accepted(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            os.makedirs(os.path.join(d, "adapters", "xbrl"))
            with open(os.path.join(d, NRE_ENGINE_FILES[0]), "w", encoding="utf-8") as fh:
                fh.write("x = 1\n")
            self.assertFalse(nre_declared_numstat("1\t1\t" + self.INST, base=d))

    def test_n_4_without_the_nre_seal_in_history_nothing_is_accepted(self):
        r = PR.Repo()
        r.put("measure/prev.py")
        r.commit("measure/prev.py")
        self.assertFalse(nre_seal_in_history(r.d))
        self.assertFalse(nre_declared_numstat("1\t1\t" + self.INST, root=r.d))
        self.assertFalse(nre_declared_fingerprint(NRE_FP, root=r.d))
        self.assertEqual(set(), nre_engine_commits(r.d))

    def test_n_5_only_the_declared_fingerprint_is_accepted(self):
        self.assertTrue(nre_declared_fingerprint(NRE_FP))
        self.assertFalse(nre_declared_fingerprint(NRE_FP[:-1] + "1"))
        self.assertFalse(nre_declared_fingerprint(T_FP))
        self.assertFalse(nre_declared_fingerprint(PB_FP))
        self.assertFalse(nre_declared_fingerprint(None))

    def _repo(self, extra_commit=False, dirty=False, engine=True, other_between=False, with_t=False):
        u"""封 →(T の封 → T の engine の commit)→ NRE の封 → (NRE の engine の commit = instance.py と前の便の file を触る)→ ..."""
        r = PR.Repo()
        r.put("measure/gate.py")
        r.put(SEAL_REL)
        seal = r.commit("measure/gate.py", SEAL_REL)
        if with_t:
            r.put(T_SEAL_REL)
            r.commit(T_SEAL_REL)
            for rel in T_ENGINE_FILES:
                r.put(rel)
            r.put("measure/gate.py")
            r.commit(*(list(T_ENGINE_FILES) + ["measure/gate.py"]))
        if other_between:
            r.put("measure/gate.py")
            r.commit("measure/gate.py")
        r.put(NRE_SEAL_REL)
        r.commit(NRE_SEAL_REL)
        for rel in NRE_ENGINE_FILES:
            r.put(rel)
        r.put("measure/gate.py")
        files = ["measure/gate.py"] + (list(NRE_ENGINE_FILES) if engine else [])
        e = r.commit(*files)
        if extra_commit:
            r.put("measure/gate.py")
            r.commit("measure/gate.py")
        if dirty:
            r.put("measure/gate.py")
        return r, seal, e

    def _base(self, r):
        return os.path.join(r.d, "audit-core")

    def test_n_6_a_file_changed_only_by_the_nre_engine_commit_is_accepted(self):
        r, seal, e = self._repo()
        self.assertEqual(set([e]), nre_engine_commits(r.d))
        self.assertTrue(nre_declared_file_change(r.d, seal, "measure/gate.py", base=self._base(r)))
        self.assertEqual([], frozen_problems(rels=("measure/gate.py",), root=r.d, base=self._base(r)))

    def test_n_7_a_file_changed_again_after_the_nre_engine_commit_is_not_accepted(self):
        r, seal, e = self._repo(extra_commit=True)
        self.assertFalse(nre_declared_file_change(r.d, seal, "measure/gate.py", base=self._base(r)))
        self.assertEqual([u"封の commit の blob と byte が違う: measure/gate.py"], frozen_problems(rels=("measure/gate.py",), root=r.d, base=self._base(r)))

    def test_n_8_an_uncommitted_change_is_not_accepted(self):
        r, seal, e = self._repo(dirty=True)
        self.assertFalse(nre_declared_file_change(r.d, seal, "measure/gate.py", base=self._base(r)))

    def test_n_9_a_change_by_a_commit_that_does_not_touch_the_engine_is_not_accepted(self):
        r, seal, e = self._repo(engine=False)
        self.assertFalse(nre_declared_file_change(r.d, seal, "measure/gate.py", base=self._base(r)))
        self.assertNotEqual([], frozen_problems(rels=("measure/gate.py",), root=r.d, base=self._base(r)))

    def test_n_10_a_file_changed_by_another_commit_between_is_not_accepted(self):
        r, seal, e = self._repo(other_between=True)
        self.assertFalse(nre_declared_file_change(r.d, seal, "measure/gate.py", base=self._base(r)))
        self.assertNotEqual([], frozen_problems(rels=("measure/gate.py",), root=r.d, base=self._base(r)))

    def test_n_11_a_gate_changed_by_the_t_commit_and_then_the_nre_commit_is_accepted(self):
        r, seal, e = self._repo(with_t=True)
        self.assertTrue(nre_declared_file_change(r.d, seal, "measure/gate.py", base=self._base(r)))
        self.assertEqual([], frozen_problems(rels=("measure/gate.py",), root=r.d, base=self._base(r)))

    def test_n_12_a_gate_changed_only_by_the_t_commit_is_not_an_nre_transition(self):
        r = PR.Repo()
        r.put("measure/gate.py")
        r.put(SEAL_REL)
        seal = r.commit("measure/gate.py", SEAL_REL)
        r.put(T_SEAL_REL)
        r.commit(T_SEAL_REL)
        for rel in T_ENGINE_FILES:
            r.put(rel)
        r.put("measure/gate.py")
        r.commit(*(list(T_ENGINE_FILES) + ["measure/gate.py"]))
        r.put(NRE_SEAL_REL)
        r.commit(NRE_SEAL_REL)
        for rel in NRE_ENGINE_FILES:
            r.put(rel)
        r.commit(*NRE_ENGINE_FILES)
        base = self._base(r)
        self.assertTrue(t_declared_file_change(r.d, seal, "measure/gate.py", base=base))                 # T の遷移としては許す
        self.assertFalse(nre_declared_file_change(r.d, seal, "measure/gate.py", base=base))              # NRE の遷移とは言わない

    def test_n_13_a_file_changed_before_the_nre_seal_is_not_accepted(self):
        r = PR.Repo()
        r.put("measure/gate.py")
        r.put(SEAL_REL)
        seal = r.commit("measure/gate.py", SEAL_REL)
        r.put("measure/gate.py")
        r.commit("measure/gate.py")
        r.put(NRE_SEAL_REL)
        r.commit(NRE_SEAL_REL)
        for rel in NRE_ENGINE_FILES:
            r.put(rel)
        r.commit(*NRE_ENGINE_FILES)
        self.assertFalse(nre_declared_file_change(r.d, seal, "measure/gate.py", base=self._base(r)))

    def _explained_repo(self, extra_engine_file=False, extra_commit_after=False):
        u"""封 → NRE の封(instance.py は 1 行)→ NRE の engine の commit(instance.py の 1 行を替える。numstat 1・1)。sha16 を見る作業木の側は実物の instance.py の写しを置いた使い捨ての folder。"""
        r = PR.Repo()
        r.put("measure/gate.py")
        r.put(SEAL_REL)
        r.put(NRE_ENGINE_FILES[0], text=u"")
        seal = r.commit("measure/gate.py", SEAL_REL, NRE_ENGINE_FILES[0])
        r.put(NRE_SEAL_REL)
        r.commit(NRE_SEAL_REL)
        r.put(NRE_ENGINE_FILES[0], text=u"")
        files = [NRE_ENGINE_FILES[0]]
        if extra_engine_file:
            r.put("adapters/xbrl/recipes.py")
            files.append("adapters/xbrl/recipes.py")
        e = r.commit(*files)
        if extra_commit_after:
            r.put("measure/gate.py")
            r.commit("measure/gate.py")
        return r, seal, e

    def test_n_15_an_explained_commit_is_the_nre_engine_commit_whose_change_to_the_paths_is_the_declared_line_only(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d:
            os.makedirs(os.path.join(d, "adapters", "xbrl"))
            with open(os.path.join(ROOT, NRE_ENGINE_FILES[0]), "rb") as src, open(os.path.join(d, NRE_ENGINE_FILES[0]), "wb") as dst:
                dst.write(src.read())                                                                       # sha16 が宣言の値の instance.py の写し
            r, seal, e = self._explained_repo()
            paths = [PREFIX + "adapters", PREFIX + "core"]
            self.assertEqual(set([e]), nre_engine_commits(r.d))
            self.assertTrue(nre_explained_commit(r.d, e, paths, base=d))                                    # 宣言の行だけ(1・1。sha16・封が履歴に在る)
            self.assertFalse(nre_explained_commit(r.d, seal, paths, base=d))                                # engine の commit でない
            with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as d2:
                os.makedirs(os.path.join(d2, "adapters", "xbrl"))
                with open(os.path.join(d2, NRE_ENGINE_FILES[0]), "w", encoding="utf-8") as fh:
                    fh.write("x = 1\n")
                self.assertFalse(nre_explained_commit(r.d, e, paths, base=d2))                              # sha16 が宣言の値でない
            r2, seal2, e2 = self._explained_repo(extra_engine_file=True)
            self.assertFalse(nre_explained_commit(r2.d, e2, paths, base=d))                                 # recipes.py も触った(宣言の行だけでない)
            self.assertFalse(nre_explained_commit(r.d, "0" * 40, paths, base=d))                            # 履歴に無い commit
            r3, seal3, e3 = self._explained_repo(extra_commit_after=True)
            self.assertTrue(nre_explained_commit(r3.d, e3, paths, base=d))                                  # 後の commit が在っても、engine の commit 自身は外れる
            r4 = PR.Repo()
            r4.put(NRE_ENGINE_FILES[0], text=u"")
            r4.commit(NRE_ENGINE_FILES[0])
            r4.put(NRE_ENGINE_FILES[0], text=u"")
            c4 = r4.commit(NRE_ENGINE_FILES[0])
            self.assertFalse(nre_explained_commit(r4.d, c4, paths, base=d))                                 # NRE の封が履歴に無い

    def test_n_16_an_explained_commit_in_this_repo_needs_the_commit_to_exist(self):
        # いまの木では instance.py は宣言の値。NRE の engine の commit が履歴に在れば、その commit だけが外れる(未 commit のうちは engine の commit が無いので何も外れない)
        e = nre_engine_commits()
        for c in e:
            self.assertTrue(nre_explained_commit(REPO, c, [PREFIX + "adapters", PREFIX + "core"]))
            self.assertFalse(nre_explained_commit(REPO, c, [PREFIX + "tests"]))                                 # 試験の file も触っているので、その path まで含めれば外さない
        self.assertFalse(nre_explained_commit(REPO, "0" * 40, [PREFIX + "adapters"]))

    def test_n_17_the_old_formula_reference_reads_the_defect_and_the_engine_does_not(self):
        import io
        import zipfile
        nil = b'<ix:nonFraction name="ex:A" contextRef="Prior" unitRef="JPY" scale="6" xsi:nil="true"/>'
        real = b'<ix:nonFraction name="ex:A" contextRef="Current" unitRef="JPY" scale="6">120</ix:nonFraction>'
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("XBRL/PublicDoc/x_ixbrl.htm", nil + b"\n" + real)
        zb = buf.getvalue()
        old = nre_old_formula_instance()
        self.assertNotIn("instance_with_the_old_formula_for_nre", sys.modules)
        self.assertEqual([("ex:A", "Prior", 120000000.0)], [(f["name"], f["context"], f["value"]) for f in old.load_instance(zb)["facts"]])
        from adapters.xbrl import instance as I
        self.assertEqual([("ex:A", "Current", 120000000.0)], [(f["name"], f["context"], f["value"]) for f in I.load_instance(zb)["facts"]])
        with open(os.path.join(ROOT, NRE_ENGINE_FILES[0]), encoding="utf-8") as fh:
            src = fh.read()
        with self.assertRaises(AssertionError):
            nre_old_formula_instance(src=src.replace(NRE_FORMULA_AFTER, NRE_FORMULA_BEFORE))        # 前の字のままの engine には戻す式が無い
        with self.assertRaises(AssertionError):
            nre_old_formula_instance(src=src + "\n" + NRE_FORMULA_AFTER + "\n")                  # 「後」の字が 2 回

    def test_n_18_a_record_fingerprint_is_ok_only_for_the_same_value_or_the_declared_pre_nre_value(self):
        self.assertTrue(nre_record_fingerprint_ok(NRE_FP, NRE_FP))
        self.assertTrue(nre_record_fingerprint_ok(T_FP, NRE_FP))                       # 記録は NRE の前の engine(T の後)で、今の engine は NRE の宣言された遷移の値
        self.assertTrue(nre_record_fingerprint_ok(T_FP, T_FP))
        self.assertFalse(nre_record_fingerprint_ok(PB_FP, NRE_FP))                    # 記録が NRE の前の値でない
        self.assertFalse(nre_record_fingerprint_ok(T_FP, NRE_FP[:-1] + "1"))          # 今の値が宣言の値でない
        self.assertFalse(nre_record_fingerprint_ok(NRE_FP, T_FP))                     # 向きが逆
        self.assertFalse(nre_record_fingerprint_ok(None, NRE_FP))
        r = PR.Repo()
        r.put("measure/prev.py")
        r.commit("measure/prev.py")
        self.assertFalse(nre_record_fingerprint_ok(T_FP, NRE_FP, root=r.d))           # NRE の封が履歴に無い

    def test_n_14_the_other_transitions_do_not_accept_the_nre_line_and_the_nre_does_not_accept_theirs(self):
        self.assertFalse(pb_declared_numstat("1\t1\t" + self.INST))
        self.assertFalse(t5y_declared_numstat("1\t1\t" + self.INST))
        self.assertFalse(t_declared_numstat("1\t1\t" + self.INST))
        self.assertFalse(nre_declared_numstat("57\t0\t" + self.REC))
        self.assertFalse(nre_declared_numstat("30\t0\t%smeasure/inject.py" % PREFIX))


class OrderTest(unittest.TestCase):
    def test_o_1_the_real_history_has_the_seal_before_the_engine_before_the_scripts(self):
        u"""script・門のどれかが未 commit なら赤(足した commit が無い)。engine の commit の hash は履歴から探す。"""
        self.assertEqual([], PR.order_problems(REPO, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, ENGINE_FILES, SCRIPT_RELS + GATE_RELS))


OTHERS = ["measure/a.py", "tests/g.py"]
IMPLS = list(ENGINE_FILES)
SEALF = "docs/seal.md"


def order_of(r, seal_short):
    return PR.order_problems(r.d, PREFIX, SEALF, seal_short, IMPLS, OTHERS)


class OrderMutationTest(unittest.TestCase):
    def _repo(self, before_impl=(), after_seal_before_impl=(), after_impl=OTHERS, seal_touches=None):
        r = PR.Repo()
        for f in before_impl:
            r.put(f)
            r.commit(f)
        if seal_touches:
            r.put(seal_touches)
        r.put(SEALF)
        s = r.commit(SEALF, *([seal_touches] if seal_touches else []))
        for f in after_seal_before_impl:
            r.put(f)
            r.commit(f)
        for f in IMPLS:
            r.put(f)
        r.commit(*IMPLS)
        for f in after_impl:
            r.put(f)
        if after_impl:
            r.commit(*after_impl)
        return r, s[:7]

    def test_p_1_a_correct_order_is_green(self):
        r, s = self._repo()
        self.assertEqual([], order_of(r, s))

    def test_p_2_a_script_before_the_engine_or_before_the_seal_is_red(self):
        r, s = self._repo(after_seal_before_impl=[OTHERS[0]], after_impl=OTHERS[1:])
        self.assertIn("BEFORE_IMPL:" + OTHERS[0], order_of(r, s))
        r2, s2 = self._repo(before_impl=[OTHERS[0]], after_impl=OTHERS[1:])
        self.assertIn("BEFORE_SEAL:" + OTHERS[0], order_of(r2, s2))

    def test_p_3_an_uncommitted_script_and_an_uncommitted_engine_are_red_not_skipped(self):
        r, s = self._repo(after_impl=OTHERS[:1])
        self.assertEqual(["UNCOMMITTED:" + OTHERS[1]], order_of(r, s))
        r2 = PR.Repo()
        r2.put(SEALF)
        s2 = r2.commit(SEALF)
        r2.put(IMPLS[0])
        r2.commit(IMPLS[0])
        self.assertTrue(any(p.startswith("IMPL_UNCOMMITTED:") for p in order_of(r2, s2[:7])))

    def test_p_4_a_wrong_seal_hash_or_a_seal_that_touches_the_engine_is_red(self):
        r, s = self._repo()
        self.assertIn("SEAL_NOT_THE_SEALED", order_of(r, "0000000"))
        r2, s2 = self._repo(before_impl=[IMPLS[0]], seal_touches=IMPLS[0])
        self.assertIn("SEAL_TOUCHES_ENGINE", order_of(r2, s2))

    def test_p_5_the_engine_commit_is_found_from_history_without_a_hash(self):
        r, s = self._repo()
        seal, e = engine_commit(r.d, PREFIX, SEALF, IMPLS)
        self.assertTrue(seal.startswith(s))
        self.assertTrue(e and e != seal)
        self.assertEqual(e, PR.git_in(r.d, "rev-parse", "HEAD~1")[1])


if __name__ == "__main__":
    unittest.main()
