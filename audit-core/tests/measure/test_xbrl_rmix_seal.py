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
    if names[i - 1] != PREV_FLAG or names[i + 1:i + 2] != [NEXT_FLAG]:
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
    if on != ["P30E"]:
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
