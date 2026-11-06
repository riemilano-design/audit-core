# -*- coding: utf-8 -*-
"""封 docs/XBRL_INJECT_SCAN_FIX_SEAL_2026-11-05.md(H ― 注入の仕掛けの数の読みに「万円」と「億+万の複合」を足す。追記 1 まで)の測定の門。封 §5。

**この門が縛るもの**(結果の門 ``test_xbrl_nscan_result.py`` は記録・文書・採用の判定を縛る)

1. 封の字(規則の要点): 切り替えの名前 ``yen_scan_2026_11_05``(追記 1 の 1 が正)・既定 偽・複合の走査の正規表現・作る条件(万の group があるか、group が 2 つ以上)・
   ``万円`` = 10000・位の指数(兆 12・億 8・万 4)・封 §3 の予測の表が H-1〜H-10 の 10 行でどの行も予測と外れ方の欄を持つ・§4 の K-1〜K-4・§5 の path。
2. 封の字と lib の現物が同じ: 切り替えの既定(ファイルの字と module の値)・正規表現・``MONEY_SCALE`` の ``万円`` の行(字で 10000)・位の指数。
3. lib の変更は封の commit から ``measure/lib/numbers.py``・``measure/lib/scales.py`` の 2 file だけで削除 0。``measure/inject.py``・``measure/lib/sites.py``・``core/``・``adapters/`` は封の commit から 0 行。
4. 前の便(RB・N)の script・記録・門と、この便が読むだけの script・記録は封の commit の blob と byte が同じ。
5. 順序: 封 89afc79 ⊏ lib を触った commit ⊏ script・門 2 本(記録・結果の文書の順序は結果の門が見る)。未 commit は赤(skip にしない)。
6. 配線: この script が引く ``lib.numbers`` が RM・RUN・IJ・TUNE・``lib.sites`` の使う N と同じ instance。切り替えを with の中だけ真にし、出るとき(例外のときも)偽に戻す。
   K-4 の変異の名前が封の字と同じ。
7. 新しい門が、既存の門が行頭の名前を数える変数名を行頭に置いていない。script・門に docID の字が無い。
8. 門の変異: 封の字・lib の字・numstat・順序・配線を 1 つずつ壊した標本で上の検査が赤になる。

この file は docID の字を持たない(引きの門が追跡 file の docID を数える)。
"""
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
sys.path.insert(0, os.path.join(ROOT, "measure"))


def load_module(rel, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SGR = load_module("tests/measure/test_xbrl_rmix_seal.py", "rmix_seal_gate_for_nscan_seal")       # 前の便の封の門の部品(frozen_problems・RESERVED_PREFIXES)。門としては走らせない
PR = SGR.PR                                                                                      # order_problems・Repo・added_commits・git_in
NS = load_module("measure/xbrl_nscan_2026-11-05.py", "nscan_script_for_seal_gate")
N, SC = NS.N, NS.SC

SEAL_REL = NS.SEAL_REL
SEAL_COMMIT_SHORT = NS.SEAL_COMMIT
FLAG = NS.FLAG
LIB_RELS = NS.LIB_RELS
SCRIPT_RELS = ("measure/xbrl_nscan_2026-11-05.py",)
GATE_RELS = ("tests/measure/test_xbrl_nscan_seal.py", "tests/measure/test_xbrl_nscan_result.py")
RECORD_RELS = tuple(NS.REC_REL.values())
DOC_REL = NS.DOC_REL
#: 触らない file(封の commit から 0 行)
NOT_TOUCHED_RELS = ("measure/inject.py", "measure/lib/sites.py", "adapters", "core")
#: この便が読むだけの前の便の script・記録・門(封の commit の blob と byte が同じでなければならない)。RB の便の封の門・結果の門も含む(RB の engine の commit は封 89afc79 より前)
READ_ONLY_RELS = (
    "measure/xbrl_rmix_2026-11-04.py", "measure/xbrl_rmix_regress97_2026-11-04.py",
    "fixtures/xbrl/rmix/ai200_2026-11-04.json", "fixtures/xbrl/rmix/inject_2026-11-04.json", "fixtures/xbrl/rmix/regress97_2026-11-04.json",
    "tests/measure/test_xbrl_rmix_seal.py", "tests/measure/test_xbrl_rmix_result.py",
    "measure/xbrl_numfix_2026-11-04.py", "measure/xbrl_numfix_regress97_2026-11-04.py", "measure/xbrl_numfix_shapes_2026-11-04.py",
    "fixtures/xbrl/numfix/ai200_2026-11-04.json", "fixtures/xbrl/numfix/inject_2026-11-04.json",
    "fixtures/xbrl/numfix/regress97_2026-11-04.json", "fixtures/xbrl/numfix/shapes_2026-11-04.json",
    "tests/measure/test_xbrl_numfix_result.py",
    "measure/xbrl_aiforms_gen_2026-11-03.py", "measure/xbrl_aiforms_run_2026-11-03.py", "measure/xbrl_p27_tune_2026-10-27.py",
    "fixtures/xbrl/aiforms/gen_2026-11-03.json", "fixtures/xbrl/aiforms/f5_gen_2026-11-03.json",
    "fixtures/xbrl/aiforms/claims_2026-11-03.json", "fixtures/xbrl/aiforms/f5_claims_2026-11-03.json",
    "fixtures/xbrl/aiforms/labels_2026-11-03.json", "fixtures/xbrl/aiforms/f5_labels_2026-11-03.json", "measure/SEED.json",
    "measure/inject.py", "measure/lib/sites.py", "measure/tests/test_inject.py")
#: 既存の門が行頭の名前を数える変数名(新しい門はこれらを行頭に置かない。前の便の封の門と同じ一覧)
RESERVED_PREFIXES = SGR.RESERVED_PREFIXES
DOCID_RE = SGR.DOCID_RE
PRED_IDS = tuple("H-%d" % i for i in range(1, 11))
K_IDS = tuple("K-%d" % i for i in range(1, 5))
#: 封の字の要点(封に無ければ赤)
SEAL_PHRASES = (
    u"切り替え `yen_scan_2026_11_05 = False`(`measure/lib/numbers.py` の module の変数。既定 偽)",
    u"`(?<![0-9.,])(?=\\d)(?:(X)兆)?(?:(X)億)?(?:(X)万)?円`(X = `\\d{1,3}(?:,\\d{3})+|\\d+`)",
    u"**万の group があるか、group が 2 つ以上**のものを 1 つの `NumberToken` にする",
    u"(億だけ・兆だけの 1 group は作らない = 既存の token のまま)",
    u"`value` = 各 group の数 × 10^(その位の指数 − 最小の位の指数)の和(兆 12・億 8・万 4。整数で足して float)",
    u"`measure/lib/scales.py` の `MONEY_SCALE` に `\"万円\": 10000,` を字で足す",
    u"先頭の 0 の group は落とす。先頭以外の 0 の group は「0」で描く(keep)",
    u"切り替えの名前**: §1 の `yen_scan_2026_11_05` が正",
    u"測定 script は `N.yen_scan_2026_11_05 = True` を立てる",
    u"`measure/inject.py`・`measure/lib/sites.py` は触らない",
    u"切り替えは既定 偽のまま lib に残し",
)
#: 切り替えの名前の書き損じ(封の追記 1 の 1 が正としない名前)は、測定の路で使わない
WRONG_FLAG = "compound_yen_2026_11_05"
FLAG_PATTERN_IN_SEAL = u"(?<![0-9.,])(?=\\d)(?:(X)兆)?(?:(X)億)?(?:(X)万)?円"
X_IN_SEAL = u"\\d{1,3}(?:,\\d{3})+|\\d+"


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
        ids = table_ids(seal, "## §3", "## §4", r"^\| (H-\d+) \| (.*) \|$")
        sec = seal[seal.index("## §3"):seal.index("## §4")]
        sec4 = seal[seal.index("## §4"):seal.index("## §5")]
        sec5 = seal[seal.index("## §5"):seal.index("## §6")]
    except ValueError:
        return [u"封の節(§3・§4・§5・§6)が揃っていない"]
    if ids != list(PRED_IDS):
        out.append(u"封 §3 の表が H-1〜H-10 の 10 行でない: %s" % ids)
    for line in sec.splitlines():
        m = re.match(r"^\| (H-\d+) \| (.*) \|$", line)
        if m:
            cells = m.group(2).split(u" | ")
            if len(cells) < 3 or any(not c.strip() for c in cells[:3]):
                out.append(u"封 §3 の %s の欄(欄・予測・外れ方)が埋まっていない" % m.group(1))
    got_k = re.findall(r"^- (K-\d):", sec4, re.M)
    if got_k != list(K_IDS):
        out.append(u"封 §4 の K-1〜K-4 が揃っていない: %s" % got_k)
    for rel in (SCRIPT_RELS[0],) + GATE_RELS + (DOC_REL,):
        if rel not in sec5:
            out.append(u"封 §5 に path が無い: %s" % rel)
    for rel in RECORD_RELS:
        if rel not in sec5:
            out.append(u"封 §5 に記録の path が無い: %s" % rel)
    for ph in SEAL_PHRASES:
        if ph not in seal:
            out.append(u"封に規則の要点の字が無い: %s" % ph)
    return out


def seal_regex(seal):
    u"""封 §1 の 1 の正規表現の字(X を書いた形)を、lib の字(X を `(...)` で展開した形)にする。"""
    if FLAG_PATTERN_IN_SEAL not in seal or u"(X = `%s`)" % X_IN_SEAL not in seal:
        return None
    return FLAG_PATTERN_IN_SEAL.replace(u"(X)", u"(" + X_IN_SEAL + u")")


def seal_exponents(seal):
    m = re.search(r"兆 (\d+)・億 (\d+)・万 (\d+)", seal)
    return {u"兆": int(m.group(1)), u"億": int(m.group(2)), u"万": int(m.group(3))} if m else None


def seal_scale(seal):
    m = re.search(r"`MONEY_SCALE` に `\"万円\": (\d+),` を字で足す", seal)
    return int(m.group(1)) if m else None


# ---------------------------------------------------------------- 2. 封の字と lib の現物
def lib_problems(seal, nm=None, sm=None, numbers_src=None, scales_src=None):
    u"""封の字と lib の現物が同じか。nm = numbers の module(試験が壊した写しを渡す)、sm = scales の module、*_src = file の字。"""
    nm = nm or N
    sm = sm or SC
    numbers_src = numbers_src if numbers_src is not None else read("measure/lib/numbers.py")
    scales_src = scales_src if scales_src is not None else read("measure/lib/scales.py")
    out = []
    if not re.search(r"^%s = False$" % re.escape(FLAG), numbers_src, re.M):
        out.append(u"numbers.py に『%s = False』の行が無い(既定が偽でない)" % FLAG)
    if getattr(nm, FLAG, None) is not False:
        out.append(u"切り替え %s がいま偽でない(または無い)" % FLAG)
    if WRONG_FLAG in numbers_src or WRONG_FLAG in read("measure/xbrl_nscan_2026-11-05.py"):
        out.append(u"封の追記 1 が書き損じとした名前 %s が lib か script に在る" % WRONG_FLAG)
    want = seal_regex(seal)
    if want is None:
        out.append(u"封から正規表現を読めない")
    elif getattr(nm, "YEN_SCAN_RE", None) is None or nm.YEN_SCAN_RE.pattern != want:
        out.append(u"複合の走査の正規表現が封の字と違う")
    exp = seal_exponents(seal)
    if exp is None or dict(getattr(nm, "_YEN_SCAN_EXP", {})) != exp:
        out.append(u"位の指数が封の字(兆 12・億 8・万 4)と違う")
    scale = seal_scale(seal)
    if scale is None or sm.MONEY_SCALE.get(u"万円") != scale or not isinstance(sm.MONEY_SCALE.get(u"万円"), int):
        out.append(u"MONEY_SCALE の 万円 が封の字(10000)と違う")
    if scale is not None and not re.search(r"^\s*\"万円\": %d,$" % scale, scales_src, re.M):
        out.append(u"scales.py に『\"万円\": %d,』の行が字で無い(計算にしてはならない)" % scale)
    return out


def behaviour_problems(nm=None, sm=None):
    u"""封 §1 の 4・5 の当たる例と当たらない例を、lib の現物に当てる(切り替えを with の中だけ真にする)。"""
    nm = nm or N
    sm = sm or SC
    out = []
    old = getattr(nm, FLAG)
    setattr(nm, FLAG, True)
    try:
        t = nm.scan(u"売上高は12億3,456万円でした。")
        if len(t) != 1 or (t[0].text, t[0].unit, t[0].value) != (u"12億3,456", u"万円", 123456.0) or t[0].groups != ((u"億", False), (u"万", True)):
            out.append(u"『12億3,456万円』が封の例の token 1 つ(text 12億3,456・unit 万円・value 123456・groups ((億, 偽), (万, 真)))でない")
        t = nm.scan(u"利益は1,234万円。")
        if len(t) != 1 or (t[0].text, t[0].unit, t[0].value) != (u"1,234", u"万円", 1234.0):
            out.append(u"『1,234万円』が封の例の token でない")
        t = nm.scan(u"負債は5兆1,234億円。")
        if len(t) != 1 or (t[0].text, t[0].unit, t[0].value) != (u"5兆1,234", u"億円", 51234.0):
            out.append(u"『5兆1,234億円』が封の例の token でない")
        like_c = nm.scan(u"売上高は12億3,456万円でした。")[0]
        if [nm.render_value(v, like_c) for v in (123458.0, 9700.0)] != [u"12億3,458", u"9,700"]:
            out.append(u"描きが封の例(12億3,458・9,700)と違う")
        like_p = nm.scan(u"売上高は1億500万円でした。")[0]
        if [nm.render_value(v, like_p) for v in (9700.0, 10000.0)] != [u"9700", u"1億0"]:
            out.append(u"描きが封の例(コンマ無しの 9700・1億0)と違う")
        for text in (u"10億円", u"1,234億円", u"1,234百万円", u"105,873千円", u"1,234万人", u"3万株", u"2026年"):
            if any(x.groups is not None for x in nm.scan(text)):
                out.append(u"当たらない例に複合 token が出た: %s" % text)
        if sm.scaled_value(1234.0, u"万円") != 12340000.0:
            out.append(u"万円 の倍率が 10000 でない")
        if nm.unit_family(u"万円") != "money":
            out.append(u"真のとき 万円 が金額の族でない")
    except Exception as e:                                     # noqa: BLE001  壊れた規則は例外で落とさず問題に数える
        out.append(u"例に当てて例外(%s)" % type(e).__name__)
    finally:
        setattr(nm, FLAG, old)
    if nm.unit_family(u"万円") is not None and not getattr(nm, FLAG):
        out.append(u"偽のとき 万円 が族に数えられている")
    return out


# ---------------------------------------------------------------- 3. lib の変更
def lib_numstat_problems(lines):
    u"""``git diff --numstat <封> -- audit-core/measure/lib`` の行 → 問題の列。"""
    out = []
    paths = {}
    for ln in lines:
        ins, dele, path = ln.split("\t")
        paths[path] = int(ins)
        if dele != "0":
            out.append(u"削除が 0 でない: %s" % path)
        if int(ins) <= 0:
            out.append(u"挿入が 0 行: %s" % path)
    if sorted(paths) != sorted(PREFIX + p for p in LIB_RELS):
        out.append(u"lib の変更が numbers.py・scales.py の 2 file だけでない: %s" % sorted(paths))
    return out


def seal_commit(root=REPO):
    s = PR.added_commits(root, PREFIX + SEAL_REL)
    return s[0] if len(s) == 1 else None


def real_numstat_problems(root=REPO):
    sh = seal_commit(root)
    if sh is None:
        return [u"封の commit が履歴に 1 つに決まらない"]
    lines = [x for x in PR.git_in(root, "diff", "--numstat", sh, "--", PREFIX + "measure/lib")[1].splitlines() if x]
    return lib_numstat_problems(lines)


def untouched_problems(lines):
    u"""``git diff --numstat <封> -- <触らない path>`` の行が 0 本か。"""
    return [u"封の commit から変わった(触らない file): %s" % ln.split("\t")[2] for ln in lines if ln]


def real_untouched_problems(root=REPO):
    sh = seal_commit(root)
    if sh is None:
        return [u"封の commit が履歴に 1 つに決まらない"]
    paths = [PREFIX + p for p in NOT_TOUCHED_RELS]
    # 2026-11-06(PB): 封 docs/XBRL_PRIOR_CUE_BIND_ENGINE_SEAL_2026-11-06.md §2-3 が宣言した遷移(recipes.py +24・vocabulary.py +5。削除 0)だけは触らない file から外す(SGR.pb_declared_numstat。他の行・他の値は赤のまま)
    return untouched_problems([x for x in PR.git_in(root, "diff", "--numstat", sh, "--", *paths)[1].splitlines() if x and not SGR.pb_declared_numstat(x, root)])


# ---------------------------------------------------------------- 7. 行頭の名前
def reserved_problems(rels=GATE_RELS, base=ROOT):
    out = []
    for rel in rels:
        with open(os.path.join(base, rel), encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        for n, line in enumerate(lines, 1):
            if any(re.match(r"%s\w*\s*=" % re.escape(p), line) for p in RESERVED_PREFIXES):
                out.append(u"%s:%d が既存の門の数える名前を行頭に置いている" % (rel, n))
    return out


# ---------------------------------------------------------------- 6. 配線
def wiring_problems(script=None):
    return (script or NS).wiring_problems()


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
        d10 = [i for i, ln in enumerate(lines) if ln.startswith("| H-10 |")]
        self.assertEqual(1, len(d10))
        self.assertNotEqual([], seal_problems("\n".join(lines[:d10[0]] + lines[d10[0] + 1:])))                       # 10 行が 9 行
        d5 = [i for i, ln in enumerate(lines) if ln.startswith("| H-5 |")][0]
        cells = lines[d5].split(" | ")
        self.assertNotEqual([], seal_problems("\n".join(lines[:d5] + [" | ".join(cells[:2]) + " |"] + lines[d5 + 1:])))   # 外れ方の欄が無い
        self.assertNotEqual([], seal_problems("\n".join(lines[:d5] + [" | ".join(cells[:1] + [" "] + cells[2:])] + lines[d5 + 1:])))   # 予測の欄が空
        k4 = [i for i, ln in enumerate(lines) if ln.startswith("- K-4:")]
        self.assertEqual(1, len(k4))
        self.assertNotEqual([], seal_problems("\n".join(lines[:k4[0]] + lines[k4[0] + 1:])))
        self.assertNotEqual([], seal_problems(self.seal.replace("measure/xbrl_nscan_2026-11-05.py", "measure/x.py")))
        self.assertNotEqual([], seal_problems(self.seal.replace("inject_2026-11-05.json", "inject_x.json")))
        self.assertNotEqual([], seal_problems(self.seal.replace("offcheck_2026-11-05.json", "offcheck_x.json")))
        self.assertNotEqual([], seal_problems(self.seal.replace("fixtures/xbrl/nscan/", "fixtures/xbrl/x/")))
        self.assertNotEqual([], seal_problems(self.seal.replace("## §4", "## 四", 1)))

    def test_a_4_the_regex_exponents_and_scale_are_read_from_the_seal(self):
        self.assertEqual(N.YEN_SCAN_RE.pattern, seal_regex(self.seal))
        self.assertEqual({u"兆": 12, u"億": 8, u"万": 4}, seal_exponents(self.seal))
        self.assertEqual(10000, seal_scale(self.seal))
        self.assertIsNone(seal_regex(self.seal.replace(u"(?:(X)億)?", u"(?:(X)千)?", 1)))
        self.assertIsNone(seal_regex(self.seal.replace(u"(X = `\\d{1,3}", u"(X = `\\d{1,4}", 1)))
        self.assertEqual({u"兆": 12, u"億": 9, u"万": 4}, seal_exponents(self.seal.replace(u"億 8", u"億 9", 1)))
        self.assertEqual(1000, seal_scale(self.seal.replace(u"\"万円\": 10000,", u"\"万円\": 1000,", 1)))


class LibMatchesSealTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seal = read(SEAL_REL)

    def test_b_1_the_lib_agrees_with_the_seal(self):
        self.assertEqual([], lib_problems(self.seal))
        self.assertEqual([], behaviour_problems())
        self.assertIs(False, getattr(N, FLAG))                                       # 他の試験が真のまま残していない

    def _fake(self, **ov):
        d = {FLAG: False, "YEN_SCAN_RE": N.YEN_SCAN_RE, "_YEN_SCAN_EXP": dict(N._YEN_SCAN_EXP)}
        d.update(ov)
        return types.SimpleNamespace(**d)

    def test_b_2_a_broken_lib_literal_turns_it_red(self):
        src = read("measure/lib/numbers.py")
        sc_src = read("measure/lib/scales.py")
        self.assertEqual([], lib_problems(self.seal, self._fake(), SC, src, sc_src))
        self.assertNotEqual([], lib_problems(self.seal, self._fake(**{FLAG: True}), SC, src, sc_src))                              # 既定が真
        self.assertNotEqual([], lib_problems(self.seal, self._fake(), SC, src.replace("%s = False" % FLAG, "%s = True" % FLAG), sc_src))
        self.assertNotEqual([], lib_problems(self.seal, self._fake(YEN_SCAN_RE=re.compile(N.YEN_SCAN_RE.pattern.replace(u"兆", u"京", 1))), SC, src, sc_src))
        self.assertNotEqual([], lib_problems(self.seal, self._fake(YEN_SCAN_RE=re.compile(N.YEN_SCAN_RE.pattern.replace(u"+|", u"*|", 1))), SC, src, sc_src))
        bad_exp = dict(N._YEN_SCAN_EXP)
        bad_exp[u"万"] = 3
        self.assertNotEqual([], lib_problems(self.seal, self._fake(_YEN_SCAN_EXP=bad_exp), SC, src, sc_src))
        bad_exp = dict(N._YEN_SCAN_EXP)
        bad_exp[u"兆"] = 11
        self.assertNotEqual([], lib_problems(self.seal, self._fake(_YEN_SCAN_EXP=bad_exp), SC, src, sc_src))
        self.assertNotEqual([], lib_problems(self.seal, self._fake(), types.SimpleNamespace(MONEY_SCALE=dict(SC.MONEY_SCALE, **{u"万円": 1000})), src, sc_src))   # 倍率が 1e3
        self.assertNotEqual([], lib_problems(self.seal, self._fake(), types.SimpleNamespace(MONEY_SCALE=dict(SC.MONEY_SCALE, **{u"万円": 10000.0})), src, sc_src))   # 字でなく float
        self.assertNotEqual([], lib_problems(self.seal, self._fake(), SC, src, sc_src.replace(u"\"万円\": 10000,", u"\"万円\": 1000000 // 100,")))          # 計算にした
        self.assertNotEqual([], lib_problems(self.seal, self._fake(), SC, src + u"\n# " + WRONG_FLAG + u"\n", sc_src))                                # 書き損じの名前
        self.assertNotEqual([], lib_problems(self.seal.replace(u"(?:(X)億)?", u"(?:(X)千)?", 1), self._fake(), SC, src, sc_src))                      # 封の字の側を変えた

    def test_b_3_the_behaviour_check_sees_a_changed_rule(self):
        # 規則を 1 つ壊した numbers の写し(正規表現の group を 億だけ 1 つも作らない条件に変える)で赤
        real_scan = N.scan
        old = getattr(N, FLAG)

        def scan_no_compound(text):
            return [t for t in real_scan(text) if t.groups is None]
        N.scan = scan_no_compound
        try:
            self.assertNotEqual([], behaviour_problems())
        finally:
            N.scan = real_scan
            setattr(N, FLAG, old)
        real_unit_family = N.unit_family
        N.unit_family = lambda u: None
        try:
            self.assertNotEqual([], behaviour_problems())
        finally:
            N.unit_family = real_unit_family
        self.assertEqual([], behaviour_problems())
        self.assertIs(False, getattr(N, FLAG))


class LibAndFrozenTest(unittest.TestCase):
    def test_c_1_lib_changes_are_the_two_files_and_no_deletions(self):
        self.assertEqual([], real_numstat_problems())

    def test_c_2_numstat_mutations_turn_it_red(self):
        good = ["113\t0\t%smeasure/lib/numbers.py" % PREFIX, "3\t0\t%smeasure/lib/scales.py" % PREFIX]
        self.assertEqual([], lib_numstat_problems(good))
        self.assertNotEqual([], lib_numstat_problems(good[:1]))
        self.assertNotEqual([], lib_numstat_problems(good + ["1\t0\t%smeasure/lib/sites.py" % PREFIX]))
        self.assertNotEqual([], lib_numstat_problems(["113\t1\t%smeasure/lib/numbers.py" % PREFIX] + good[1:]))
        self.assertNotEqual([], lib_numstat_problems(["0\t0\t%smeasure/lib/numbers.py" % PREFIX] + good[1:]))

    def test_c_3_inject_sites_and_engine_are_untouched_since_the_seal(self):
        self.assertEqual([], real_untouched_problems())
        self.assertNotEqual([], untouched_problems(["1\t0\t%smeasure/inject.py" % PREFIX]))
        self.assertNotEqual([], untouched_problems(["0\t2\t%sadapters/xbrl/extract.py" % PREFIX]))
        self.assertNotEqual([], untouched_problems(["3\t0\t%score/py/audit_core/verify.py" % PREFIX]))

    def test_d_1_previous_scripts_records_and_gates_are_byte_identical_to_the_seal_commit(self):
        self.assertEqual([], SGR.frozen_problems(rels=READ_ONLY_RELS, root=REPO, base=ROOT, seal_rel=SEAL_REL))

    def test_d_2_the_frozen_check_sees_a_changed_file_and_a_missing_one(self):
        self.assertNotEqual([], SGR.frozen_problems(rels=READ_ONLY_RELS + (SCRIPT_RELS[0],), root=REPO, base=ROOT, seal_rel=SEAL_REL))      # 封の commit に無い file
        self.assertNotEqual([], SGR.frozen_problems(rels=("measure/lib/numbers.py",), root=REPO, base=ROOT, seal_rel=SEAL_REL))            # 封の後に変えた file

    def test_d_3_the_frozen_check_goes_red_when_a_tracked_file_changes_after_the_seal(self):
        r = PR.Repo()
        r.put("measure/prev.py")
        r.put(SEAL_REL)
        r.commit("measure/prev.py", SEAL_REL)
        base = os.path.join(r.d, "audit-core")
        self.assertEqual([], SGR.frozen_problems(rels=("measure/prev.py",), root=r.d, base=base, seal_rel=SEAL_REL))
        with open(os.path.join(base, "measure/prev.py"), "a", encoding="utf-8") as fh:
            fh.write("x = 1\n")
        self.assertEqual([u"封の commit の blob と byte が違う: measure/prev.py"], SGR.frozen_problems(rels=("measure/prev.py",), root=r.d, base=base, seal_rel=SEAL_REL))

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
            self.assertIn("XBRL_INJECT_SCAN_FIX_SEAL_2026-11-05.md", read(rel), rel)


class WiringTest(unittest.TestCase):
    def test_w_1_the_script_reaches_the_users_of_the_scan(self):
        self.assertEqual([], wiring_problems())
        self.assertIs(NS.RUN.N, N)
        self.assertIs(NS.IJ.N, N)
        self.assertIs(NS.TUNE.N, N)
        self.assertIs(NS.S.N, N)

    def test_w_2_a_user_with_another_n_turns_the_wiring_check_red(self):
        for holder, name in ((NS.RUN, "N"), (NS.IJ, "N"), (NS.TUNE, "N"), (NS.S, "N")):
            old = getattr(holder, name)
            setattr(holder, name, types.SimpleNamespace(__file__=N.__file__))
            try:
                self.assertNotEqual([], wiring_problems(), holder)
            finally:
                setattr(holder, name, old)
        for holder in (NS.TUNE, NS.S):
            old = holder.SC
            holder.SC = types.SimpleNamespace()
            try:
                self.assertNotEqual([], wiring_problems(), holder)
            finally:
                holder.SC = old
        old = NS.IJ.S
        NS.IJ.S = types.SimpleNamespace()
        try:
            self.assertNotEqual([], wiring_problems())
        finally:
            NS.IJ.S = old
        old = NS.GEN.key_leaks
        NS.GEN.key_leaks = NS.NF.ORIG_KEY_LEAKS
        try:
            self.assertNotEqual([], wiring_problems())
        finally:
            NS.GEN.key_leaks = old
        self.assertEqual([], wiring_problems())

    def test_w_3_a_swapped_numbers_file_turns_the_wiring_check_red(self):
        old = N.__file__
        N.__file__ = os.path.join(tempfile.gettempdir(), "numbers.py")
        try:
            self.assertNotEqual([], wiring_problems())
        finally:
            N.__file__ = old
        self.assertEqual([], wiring_problems())

    def test_w_4_the_switch_is_on_only_inside_the_with_and_goes_back_even_on_an_exception(self):
        self.assertFalse(getattr(N, FLAG))
        with NS.yen_scan_on():
            self.assertTrue(getattr(N, FLAG))
        self.assertFalse(getattr(N, FLAG))
        try:
            with NS.yen_scan_on():
                raise RuntimeError("x")
        except RuntimeError:
            pass
        self.assertFalse(getattr(N, FLAG))
        setattr(N, FLAG, True)                                           # すでに真だったら真のまま戻す(入れ子)
        try:
            with NS.yen_scan_on():
                pass
            self.assertTrue(getattr(N, FLAG))
        finally:
            setattr(N, FLAG, False)

    def test_w_5_the_mutation_names_are_the_ones_the_seal_names_and_each_one_is_put_back(self):
        names = NS.seal_mutation_names(read(SEAL_REL))
        self.assertEqual(list(NS.MUTATIONS), names)
        self.assertEqual(5, len(names))
        before = NS.lib_state()
        for n in names:
            with NS.MUTATIONS[n]():
                self.assertNotEqual(before, NS.lib_state(), n)             # 変異が実際に lib の何かを替える
            self.assertEqual(before, NS.lib_state(), n)                    # 出たら戻る
        self.assertIs(False, getattr(N, FLAG))

    def test_w_6_the_only_new_site_filter_keeps_only_compound_tokens_and_is_put_back(self):
        text = u"売上高は12億3,456万円、利益は10億円、費用は1,234万円でした。"
        orig = NS.S.t1_sites
        refs = [{"value": 123456.0, "unit": u"万円"}, {"value": 1234.0, "unit": u"万円"}, {"value": 10.0, "unit": u"億円"}]
        with NS.yen_scan_on():
            self.assertEqual({u"12億3,456", u"10", u"1,234"}, set(s["token"].text for s in orig(text, refs)))
            with NS.t1_sites_only_new() as o:
                self.assertIs(o, orig)
                self.assertIsNot(NS.S.t1_sites, orig)
                got = NS.S.t1_sites(text, refs)
                self.assertEqual({u"12億3,456", u"1,234"}, set(s["token"].text for s in got))
            self.assertIs(NS.S.t1_sites, orig)
            try:
                with NS.t1_sites_only_new():
                    raise RuntimeError("x")
            except RuntimeError:
                pass
            self.assertIs(NS.S.t1_sites, orig)


class OrderTest(unittest.TestCase):
    def test_o_1_the_real_history_has_the_seal_before_the_lib_before_the_scripts(self):
        u"""script・門のどれかが未 commit なら赤(足した commit が無い)。"""
        self.assertEqual([], PR.order_problems(REPO, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, LIB_RELS, SCRIPT_RELS + GATE_RELS))


OTHERS = ["measure/a.py", "tests/g.py"]
IMPLS = list(LIB_RELS)
SEALF = "docs/seal.md"


def order_of(r, seal_short):
    return PR.order_problems(r.d, PREFIX, SEALF, seal_short, IMPLS, OTHERS)


class OrderMutationTest(unittest.TestCase):
    def _repo(self, before_impl=(), after_seal_before_impl=(), after_impl=OTHERS):
        r = PR.Repo()
        for f in before_impl:
            r.put(f)
            r.commit(f)
        r.put(SEALF)
        s = r.commit(SEALF)
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

    def test_p_2_a_script_before_the_lib_or_before_the_seal_is_red(self):
        r, s = self._repo(after_seal_before_impl=[OTHERS[0]], after_impl=OTHERS[1:])
        self.assertIn("BEFORE_IMPL:" + OTHERS[0], order_of(r, s))
        r2, s2 = self._repo(before_impl=[OTHERS[0]], after_impl=OTHERS[1:])
        self.assertIn("BEFORE_SEAL:" + OTHERS[0], order_of(r2, s2))

    def test_p_3_an_uncommitted_script_and_an_uncommitted_lib_are_red_not_skipped(self):
        r, s = self._repo(after_impl=OTHERS[:1])
        self.assertEqual(["UNCOMMITTED:" + OTHERS[1]], order_of(r, s))
        r2 = PR.Repo()
        r2.put(SEALF)
        s2 = r2.commit(SEALF)
        r2.put(IMPLS[0])
        r2.commit(IMPLS[0])
        self.assertTrue(any(p.startswith("IMPL_UNCOMMITTED:") for p in order_of(r2, s2[:7])))

    def test_p_4_a_wrong_seal_hash_is_red(self):
        r, _s = self._repo()
        self.assertIn("SEAL_NOT_THE_SEALED", order_of(r, "0000000"))


if __name__ == "__main__":
    unittest.main()
