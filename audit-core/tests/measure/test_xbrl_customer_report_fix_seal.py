# -*- coding: utf-8 -*-
u"""顧客向けの報告形の直し(`adapters/xbrl/report_customer.py` だけを直す)の封の門
docs/XBRL_CUSTOMER_REPORT_FIX_SEAL_2026-10-21.md を固定する。型は報告形の封の門 tests/measure/test_xbrl_customer_report_seal.py に倣う。
人間の 2 つの引用・「判定と節の割り当ては変えない」「report.py・verify_document.py・engine の他の file は 0 行」の字・
予測 R2-1〜R2-7 と外れ方と幅の算術・§0 の数の和と記録との突き合わせ・§1 の 9 項目の字(jpigp の sha256・バイト数・取得元)・
§3 の限界・§4 の file 一覧と順序・**封が実装より先であること(新しい file・`--zip`・`provenance.json`・名簿の jpigp がまだ無い)**・
**封の commit 時点の `report_customer.py` と、それ以外の adapters/xbrl 15 file の sha16・engine の束ねた指紋・frozen_bundle**を縛る。

**この門の「封の commit 時点の値」(test_9・test_11・test_12・test_13)は、実装の便で「宣言された遷移」に更新する前提である。**
実装は `report_customer.py` を書き換えるので、その sha16・`adapter_xbrl_py_sha256`・frozen_bundle の束ねた sha がその場で動く(file の数は 16・37 のまま)。
この門は封の commit 時点の値を字で留めるので、実装の便で赤くなる ― それが狙い。そのとき `LATER_*` に (後の値, この封の path) を足して宣言する
(報告形の封の門の FINGERPRINT_LATER と同じ型)。`report_customer.py` 以外の 15 file の sha16 はこの封が「0 行」と書いたもの(R2-7)で、宣言の遷移を持たない。
動いたら赤のまま。名簿 `fixtures/xbrl/taxonomy_labels_sha256.txt` と `TAXONOMY_LABELS_README.md` に jpigp が入る遷移(§1.1・§4)は
test_8 が「封の commit 時点は jpigp が無い」を字で留めるので、同じく実装の便で `LATER_ROSTER` に宣言する。

**封の数と記録の突き合わせで見つけた、この門が封を直さずに報告した点(2026-10-21 実装席。封は commit 前なので司令塔が直す)**:
(1) §0 の (a) 1,480 行(違う 83・要確認 459・判断しない 24・一致 914)は、試作の席の出力 scratchpad/report2/proto.json(追跡外)の「単位の食い違い 前」の数で、
記録 `customer_report_2026-10-21.json` には無い。記録にあるのは span の字から数えた**概数**(違う 86・要確認 466・判断しない 24・一致 924 = 1,500)で、
数え方が違う。この門は封の字 1,480 を字のまま留め、概数の各欄が封の各欄以上であること(封の数 ⊂ 概数の行)だけを記録と突き合わせる。
(2) §0 の (c) 329 も同じく proto.json の数(違う 54・一致 275)で、記録の「ラベル無しの要素を持つ行 66」(P25)とは別の指標。
(3) §0 は「試作の直し後: (c) 0」と書く。proto.json の「英字の残る行 後」は正規表現の数えで 7(会社のラベル自体の英字)、直接数えると 0。commit 前に司令塔が R2-3 に数える行の定義を足した。
(4) 4,083 は proto.json の「金額の claim で字が読めた」(違う 260・要確認 1,138・判断しない 76・一致 2,609)の和で、封には内訳が無い
(「違う」の 260 だけ、記録の「文が金額の単位で出典の値がある『違う』」P25 = 260 と一致する)。"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))

SEAL_REL = "docs/XBRL_CUSTOMER_REPORT_FIX_SEAL_2026-10-21.md"
SEAL = os.path.join(ROOT, SEAL_REL)
RECORD_JSON = os.path.join(ROOT, "fixtures", "xbrl", "customer_report_2026-10-21.json")
ROSTER = os.path.join(ROOT, "fixtures", "xbrl", "taxonomy_labels_sha256.txt")
ROSTER_README = os.path.join(ROOT, "fixtures", "xbrl", "TAXONOMY_LABELS_README.md")
# 封の commit 時点は標準の folder の外(edinet-taxonomy-ifrs)。実装の便(2026-10-21)で標準の folder に移した(名簿で読む module になったので、folder の中身が増えても報告は変わらない)。
# どちらに在っても、封の sha256 と同じ file であることを見る。
IFRS_CACHE_AT_SEAL = os.path.expanduser("~/.cache/audit-core/edinet-taxonomy-ifrs/2025-11-01/jpigp_2025-11-01_lab.xml")
IFRS_CACHE_NOW = os.path.expanduser("~/.cache/audit-core/edinet-taxonomy/2025-11-01/jpigp_2025-11-01_lab.xml")
IFRS_CACHE = IFRS_CACHE_NOW if os.path.exists(IFRS_CACHE_NOW) else IFRS_CACHE_AT_SEAL

JPIGP_NAME = "jpigp_2025-11-01_lab.xml"
JPIGP_BYTES = 2593515
JPIGP_SHA = "d45c95cc634202973557f5ed935d747ba25e751b7386c5269fe3e7bdb2c82d09"
JPIGP_URL = "http://disclosure.edinet-fsa.go.jp/taxonomy/jpigp/2025-11-01/label/jpigp_2025-11-01_lab.xml"

# 直す対象(commit c13a746 で入った module)。封の commit 時点の sha16 と、宣言された遷移(実装の便で足す): {path: (後の sha16, 遷移を宣言した封の path)}
TARGET = "adapters/xbrl/report_customer.py"
TARGET_AT_SEAL = "d82481697762d167"
# 2026-10-21 実装の便(この封が宣言した遷移): report_customer.py の中身が動いた。封の commit 時点の値(TARGET_AT_SEAL)は残す。
# 2026-10-22(P26 の段 1): 封 docs/XBRL_P26_SEAL_2026-10-21.md が report_customer.py の理由の表に 3 行を足した(+7 行・-2 行。判定と節の割り当ては変えない)。
# 715468699973cc4a(この封の実装の便の値)は残す(測った時点の値)、P26 の段 1 で 141767d189b63733。受け入れるのは、その封が履歴に在り、値が P26 の段 1 の後の値のときだけ。
SEAL_P26 = "docs/XBRL_P26_SEAL_2026-10-21.md"
SEAL_DEFAULT_P26 = "docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md"    # 2026-10-23 追記: 既定を P22 -> P26 に切り替える 段 2(下の遷移)
SEAL_P27 = "docs/XBRL_P27_SEAL_2026-10-27.md"    # 2026-10-27 追記: P27 の段 2(下の遷移)
SEAL_DEFAULT_P27 = "docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md"    # 2026-10-28 追記: 既定を P26 -> P27 に切り替える 段 2(下の遷移。vocabulary.py の DEFAULT_PROFILE の 1 行と注記 +5 行・-1 行、verify_document.py の docstring の 1 行 +1 行・-1 行だけ)
# 2026-10-27(P27 の段 2): 封 docs/XBRL_P27_SEAL_2026-10-27.md §2-3 が宣言した遷移。engine の 5 file(vocabulary・recipes・extract・registry_setup・report_customer)に挿入だけを足した(既存の行の書き換え 0)。直前の値は残す(測った時点の値)、P27 の段 2 で下の値。受け入れるのは、その封が履歴に在り、値が P27 の段 2 の後の値のときだけ。
LATER_TARGET = {TARGET: ("6679138d350ec382", SEAL_P27)}

# §4 の file 一覧。**新規**の 4 本は封の commit 時点で作業木にも履歴にも無い。既存を直す file は EXISTING_EDITED。
NEW_FILES = ("measure/xbrl_customer_report_fix_2026-10-21.py",
             "fixtures/xbrl/customer_report_fix_2026-10-21.json",
             "docs/XBRL_CUSTOMER_REPORT_FIX_RESULT_2026-10-21.md",
             "tests/measure/test_xbrl_customer_report_fix_result.py")
EXISTING_EDITED = (TARGET,
                   "fixtures/xbrl/taxonomy_labels_sha256.txt",
                   "fixtures/xbrl/TAXONOMY_LABELS_README.md",
                   "tests/adapters/xbrl/test_report_customer.py")

# 触らない file の sha256 の先頭 16 桁(封の commit 時点 = 14cdd21 の木)。report_customer.py 以外の adapters/xbrl 15 file。宣言の遷移を持たない。
UNTOUCHED = {"adapters/xbrl/__init__.py": "65474b49e6b84626",
             "adapters/xbrl/comparators.py": "d8706338325e725b",
             "adapters/xbrl/edinet.py": "e87d48d3597a4c4d",
             "adapters/xbrl/extract.py": "68a78f99f4d4c216",
             "adapters/xbrl/holds.py": "bed43d9e5c03565a",
             "adapters/xbrl/instance.py": "f2d9e040f19adebf",
             "adapters/xbrl/prose.py": "908ce389f16fac0b",
             "adapters/xbrl/recipes.py": "bff243f13429b553",
             "adapters/xbrl/registry_setup.py": "f42ffe23aaa7673b",
             "adapters/xbrl/report.py": "0d2854e659a5d8e0",              # 人間の決定 2026-10-13「判定に手を加えない・golden」
             "adapters/xbrl/resolve.py": "a41043763c1d4073",
             "adapters/xbrl/run.py": "e2192229bf2e4eff",
             "adapters/xbrl/verify_document.py": "67e7639de3f5f2ad",
             "adapters/xbrl/verify_external.py": "0ae333392551912c",
             "adapters/xbrl/vocabulary.py": "27e71e9861fc5aad"}

# 2026-10-22(P26 の段 1): 封 docs/XBRL_P26_SEAL_2026-10-21.md が engine の 4 file を書き換えた(extract.py +42・vocabulary.py +17・recipes.py +251/-1・registry_setup.py +6。
# comparators.py・report.py・verify_document.py は 0 行)。上の UNTOUCHED は「この封は触らない」の値(封の commit 時点)で消さない。
# 受け入れるのは、その封が履歴に在り、値が P26 の段 1 の後の値のときだけ(comparators.py ほかの 11 file は遷移を持たない: 動いたら赤のまま)。
UNTOUCHED_LATER = {"adapters/xbrl/extract.py": ("3cf55966f12919f0", SEAL_P27),
                   "adapters/xbrl/recipes.py": ("52d645e713c53c1c", SEAL_P27),
                   "adapters/xbrl/registry_setup.py": ("d6f25750bcd73c0a", SEAL_P27),
                   # 2026-10-23(既定を P22 -> P26 に切り替える 段 2): 封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md(engine の差分は vocabulary.py の DEFAULT_PROFILE の 1 行と決定の注記 +4 行・-1 行だけ。人間の事前承認 2026-10-21)。
                   # 83025e9c0525d08b(P26 の段 1)は残す(測った時点の値)、段 2 で e28733067b1f17f5。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
                   # 85896a67913ce1e7(P27 の段 2) は残す(測った時点の値。vocabulary.py の sha16)、既定を P26 -> P27 に切り替える 段 2(封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md)で 514ebb8104451c07。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
                   "adapters/xbrl/vocabulary.py": ("514ebb8104451c07", SEAL_DEFAULT_P27),
                   # 2026-10-28(既定を P26 -> P27 に切り替える 段 2): 封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md §1-1 が宣言した遷移。verify_document.py の docstring の 1 行(+1 行・-1 行。実行の字は変えない)。67e7639de3f5f2ad(UNTOUCHED。測った時点の値)は残す。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
                   "adapters/xbrl/verify_document.py": ("c3791080ab5aef2f", SEAL_DEFAULT_P27)}

# 封の commit 時点の engine の束ねた指紋(verify_document.engine_fingerprint())と frozen_bundle。**宣言された遷移の前の値**で、消さない。
FINGERPRINT_AT_SEAL = {"adapter_xbrl_py_sha256": "c556de1cb26e975a172d54a4e39f4971bb5c11a5fd8a02a8404b9a719eb27acb",
                       "adapter_xbrl_py_files": 16,
                       "core_py_sha256": "34e836bb39762d5af831a9aa11d4ea095e73221beb5bd4510d3b234363a2a6e8",
                       "core_py_files": 4}
FROZEN_BUNDLE_AT_SEAL = "66f906c89205f0ef361e13fe051dbdeaed75a032e0d60ca832f6d605166f3b36"   # frozen_bundle_sha.FROZEN_BUNDLE_GENERATIONS の最新(report_customer.py の段 1)
FROZEN_COUNT_AT_SEAL = 37
# 宣言された遷移(実装の便の commit で足す): {欄: (後の値, 遷移を宣言した封の path)}。封の commit 時点では空。
# 2026-10-21 実装の便: module の中身が動くので束ねた指紋が動く(file の数 16 は動かない)。封の commit 時点の値(FINGERPRINT_AT_SEAL)は残す。
# 2026-10-22(P26 の段 1): 束ねた指紋が 11840a09…(この封の実装の便の値。残す)から 498993e2… に動いた(file の数 16 は動かない)。
# 2026-10-23(既定を P22 -> P26 に切り替える 段 2): 束ねた指紋が 498993e2…(P26 の段 1。残す)から 5aba7749… に動いた(file の数 16 は動かない)。受け入れるのは、封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md が履歴に在り、値が段 2 の後の値のときだけ。
# 0e51211a8aed2151(P27 の段 2) は残す(測った時点の値。束ねた指紋 adapter_xbrl_py_sha256 の頭 16 字)、既定を P26 -> P27 に切り替える 段 2(封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md)で 92326a0f4dcefd21。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
LATER_FINGERPRINT = {"adapter_xbrl_py_sha256": ("92326a0f4dcefd21fae4393a611e4206ef174b19258ddadd0213117191e7b399", SEAL_DEFAULT_P27)}
# 2026-10-21 実装の便: frozen_bundle に新しい世代(5c4da2e2…)。本数は 37 のまま(module の中身だけが動く)。封の commit 時点の世代(FROZEN_BUNDLE_AT_SEAL)は消さない。
# 2026-10-22(P26 の段 1): frozen_bundle の世代がもう 1 つ増えた(a97ecf7c…。本数は 37 のまま)。5c4da2e2…(この封の実装の便の世代)は消さない。
# 2026-10-23(既定を P22 -> P26 に切り替える 段 2): frozen_bundle の世代がもう 1 つ増えた(26b52706…。本数は 37 のまま)。a97ecf7c…(P26 の段 1 の世代)は消さない。
# 29fd733c8988164a(P27 の段 2) は残す(測った時点の値。frozen_bundle の束ねた sha の頭 16 字)、既定を P26 -> P27 に切り替える 段 2(封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md)で 030455282c89661b。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
LATER_FROZEN = {"bundle": ("030455282c89661b4c0152498d76bc30314362b5896b15ab67a8886a6887b0f6", SEAL_DEFAULT_P27)}
FROZEN_BUNDLE_FIX = "5c4da2e2ff3f30b7dcb6ebcbc84a5c68b074e8dc495f2d260551d7e10a4ce66c"
# 名簿に jpigp が入る遷移: 封の commit 時点は名簿 2 行・README に jpigp 無し。後は {"roster": (行, 封の path), "readme_has_jpigp": True}
# 2026-10-21 実装の便: 名簿に jpigp の 1 行、README に jpigp の取り方。封の commit 時点(名簿 2 行・README に jpigp 無し)は test_8 の docstring と上の定数が残す。
LATER_ROSTER = {"roster": ("d45c95cc634202973557f5ed935d747ba25e751b7386c5269fe3e7bdb2c82d09  jpigp_2025-11-01_lab.xml", SEAL_REL), "readme_has_jpigp": True}


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def jload(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def sec(t, start, end=None):
    i = t.index("\n" + start)
    j = t.index("\n" + end, i + 1) if end else len(t)
    return t[i:j]


def num(s):
    return int(s.replace(",", ""))


def sha16(rel):
    with io.open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)


def rows(block, tag):
    """予測の表の行を ``[(id, 行)]`` で返す。順序は書かれた順。"""
    return [(m.group(1), m.group(0)) for m in re.finditer(r"(?m)^\| \*\*%s-(\w+)\*\* \|.*$" % tag, block)]


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def rng(line, label):
    m = re.search(re.escape(label) + r"\*\*([\d,]+)〜([\d,]+)\*\*", line)
    assert m, (label, line)
    return num(m.group(1)), num(m.group(2))


def one(pattern, b, label):
    m = re.search(pattern, b)
    assert m, u"§0 の書き方が変わった: " + label
    return m


def s0_numbers(b):
    """§0 の数を、書かれた字のまま取り出す(書き方が変わったら落ちる)。"""
    m_a = one(r"\*\*([\d,]+) 行\*\*\(違う (\d+)・要確認 (\d+)・判断しない (\d+)・一致 (\d+)。試作の数え方[^)]*\)。語の主張の出典の値が円: ([\d,]+) 行", b, "(a) 1,480 行の内訳")
    m_c = one(r"\(c\) 要素名・区分名が英字で残る行\(違う・一致\): \*\*(\d+)\*\*", b, "(c) 329")
    m_e = one(r"\(e\) 本文に 64 桁の hex: \*\*(\d+)\*\*、指紋の行 (\d+)", b, "(e) 201")
    m_after = one(r"試作の直し後: \(a\) 0・読み取れない 0 / ([\d,]+)、\(c\) 0、\(e\) 0、同じ入力から同じバイト列 (\d+) / (\d+)", b, "試作の直し後")
    return {"a_total": num(m_a.group(1)), "a_wrong": int(m_a.group(2)), "a_check": int(m_a.group(3)), "a_nojudge": int(m_a.group(4)),
            "a_match": num(m_a.group(5)), "a_word": num(m_a.group(6)),
            "c": int(m_c.group(1)), "e_hex": int(m_e.group(1)), "e_lines": int(m_e.group(2)),
            "after_den": num(m_after.group(1)), "same_bytes": int(m_after.group(2)), "docs": int(m_after.group(3))}


def record_sections():
    r = jload(RECORD_JSON)["集計"]
    order = ("違う", "要確認", "対象外", "判断しない", "一致")
    return {p: [r[p]["節"][k] for k in order] for p in ("P22", "P25")}, r


class SealTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = text(SEAL)

    def test_1_human_quotes_and_the_two_declarations(self):
        head = self.t[:self.t.index("\n## §0 ")]
        self.assertTrue(head.startswith(u"# 封: 顧客向けの報告形の直し(単位・英字・但し書き・指紋・表題・桁)― 2026-10-21"))
        # 人間の 2 つの引用(「」の中を一字も変えない)
        self.assertIn(u"**人間(2026-10-21 朝)「報告形の問題はきちんと解決して」「あとは全て任せる」。", head)
        self.assertEqual(head.count(u"「報告形の問題はきちんと解決して」"), 1)
        self.assertEqual(head.count(u"「あとは全て任せる」"), 1)
        # 直すのは report_customer.py だけ / 判定と節の割り当ては変えない / 他は 0 行
        self.assertIn(u"直すのは `adapters/xbrl/report_customer.py`(commit c13a746)だけ。", head)
        self.assertIn(u"判定(state・reason・pointer)は足さず変えず、節の割り当ても変えない。", head)
        self.assertIn(u"`report.py`・`verify_document.py`・engine の他の file は 0 行。**", head)
        self.assertIn(u"作法は変えない(封 → 実装 → 凍結 → 独立監査 GO → commit)。数を見てから封・予測を直さない。", head)
        self.assertEqual(git("cat-file", "-e", "c13a746^{commit}").returncode, 0, u"封が名指す commit c13a746 が無い")

    def test_2_seven_predictions_each_with_a_way_to_fail(self):
        b = sec(self.t, "## §2", "## §3")
        rs = rows(b, "R2")
        self.assertEqual([i for i, _ in rs], ["1", "2", "3", "4", "5", "6", "7"])
        by = dict(rs)
        for i, line in rs:
            cs = cells(line)
            self.assertEqual(len(cs), 3, line)
            self.assertTrue(cs[1], u"予測が空: " + line)
            self.assertTrue(cs[2], u"外れ方が空: " + line)
        # 行ごとに、予測の字と外れ方(第 3 欄)を縛る
        spec = {"1": ((u"**節の件数は c13a746 の記録 `fixtures/xbrl/customer_report_2026-10-21.json` と全く同じ**",
                       u"(P22: 1,410 / 915 / 151 / 1,081 / 4,242、P25: 626 / 1,571 / 151 / 1,069 / 4,382)", u"行の節の割り当ても全行同じ"),
                      u"1 行でも違う"),
                "2": ((u"P25 明示で (a) の単位の食い違い **0**(前 1,480)、読み取れない **0〜20 / 4,083**",), u"幅の外"),
                "3": ((u"(c) 英字の要素名・区分名が残る行(違う・一致)**0〜5**(前 329)。数えるのは**ラベルが引けず要素名・区分名の字のまま出た行**",), u"6 以上"),
                "4": ((u"(e) 本文の 64 桁の hex **0**(前 201)。同じ入力から同じバイト列(本文・json)67 / 67 × 2 profile",), u"1 以上 / 違う"),
                "5": ((u"ラベルの名簿の外の file を folder に置いても、本文のバイト列が変わらない(試験で)",), u"変わる"),
                "6": ((u"客 A の 5 件は先頭の「違う」に 5 / 5 のまま、文の値の字が文と同じ(「40,480百万円」の文は「40,480 百万円」)",), u"5 / 5 でない"),
                "7": ((u"`report.py`・`verify_document.py`・vocabulary・recipes・registry_setup・comparators・`core/` は 0 行。"
                       u"engine の指紋は report_customer.py の分だけ動く(宣言された遷移)",), u"1 行でも")}
        for i, (ss, fail) in sorted(spec.items()):
            cs = cells(by[i])
            for s in ss:
                self.assertIn(s, cs[1], u"R2-%s: %s" % (i, s))
            self.assertEqual(cs[2], fail, u"R2-%s の外れ方" % i)
        # 外れうる所の書き方
        self.assertIn(u"**本当に外れうるのは R2-2 の読み取れない数と R2-3(会社ごとのラベルが ZIP に無い書類がありうる)。** "
                      u"R2-1 は判定を変えていないことの確認。", b)

    def test_3_ranges_and_before_numbers_agree_with_section_0(self):
        """R2-2 の「前 1,480」・R2-3 の「前 329」・R2-4 の「前 201」は §0 の数と同じ。幅の端の算術(0 ≤ 上限 < 分母、外れ方は上限 + 1)。"""
        n = s0_numbers(sec(self.t, "## §0 ", "## §1"))
        by = dict(rows(sec(self.t, "## §2", "## §3"), "R2"))
        # R2-2
        r2 = cells(by["2"])[1]
        self.assertEqual(num(re.search(r"\(前 ([\d,]+)\)", r2).group(1)), n["a_total"])
        m2 = re.search(r"読み取れない \*\*([\d,]+)〜([\d,]+) / ([\d,]+)\*\*", r2)
        self.assertIsNotNone(m2, r2)
        lo, hi, den = num(m2.group(1)), num(m2.group(2)), num(m2.group(3))
        self.assertEqual((lo, hi, den), (0, 20, n["after_den"]))
        self.assertIn(u"(a) の単位の食い違い **0**", r2)
        self.assertTrue(lo <= hi < den)
        # R2-3: 幅 0〜5、外れ方は上限 + 1
        r3 = by["3"]
        lo3, hi3 = rng(cells(r3)[1], u"(違う・一致)")
        self.assertEqual((lo3, hi3), (0, 5))
        self.assertEqual(num(re.search(r"(\d+) 以上", cells(r3)[2]).group(1)), hi3 + 1)
        self.assertEqual(num(re.search(r"\(前 ([\d,]+)\)", cells(r3)[1]).group(1)), n["c"])
        self.assertLess(hi3, n["c"])
        # R2-4
        self.assertEqual(num(re.search(r"\(前 ([\d,]+)\)", cells(by["4"])[1]).group(1)), n["e_hex"])
        m = re.search(r"(\d+) / (\d+) × 2 profile", cells(by["4"])[1])
        self.assertEqual((int(m.group(1)), int(m.group(2))), (n["same_bytes"], n["docs"]))
        # R2-6: 客 A の 5 件
        self.assertIn(u"5 / 5", cells(by["6"])[1])

    def test_4_section_0_numbers_are_pinned_as_written_and_sum(self):
        n = s0_numbers(sec(self.t, "## §0 ", "## §1"))
        # (a): 83 + 459 + 24 + 914 = 1,480
        self.assertEqual((n["a_wrong"], n["a_check"], n["a_nojudge"], n["a_match"]), (83, 459, 24, 914))
        self.assertEqual(n["a_wrong"] + n["a_check"] + n["a_nojudge"] + n["a_match"], n["a_total"])
        self.assertEqual(n["a_total"], 1480)
        self.assertEqual(n["a_word"], 1466)
        # (c) 329、(e) 201 = 67 書類 × 3、指紋の行 67、4,083、同じバイト列 67 / 67
        self.assertEqual((n["c"], n["e_hex"], n["e_lines"], n["after_den"], n["same_bytes"], n["docs"]), (329, 201, 67, 4083, 67, 67))
        self.assertEqual(n["e_hex"], 3 * n["docs"])
        self.assertEqual(n["e_lines"], n["docs"])
        # 4,083 > 1,480(単位の食い違い行は読み取れた金額の claim の部分集合)、7,799 の部分
        self.assertGreater(n["after_den"], n["a_total"])
        b = sec(self.t, "## §0 ", "## §1")
        # §0 の他の字
        for s in (u"独立監査(c13a746 の 1 回目)が顧客の目で読んだ気づきと、試作の席の診断(`scratchpad/report2/proto.json`、67 書類 P25 明示、module だけの試作)",
                  u"(d) 「違う」の意味の欄に、当てた出典の誤りかは決めないの但し書きが無い。",
                  u"客 B「sha256 が混じり会員に出せない」",
                  u"試作の席の気づき(直した後の報告を読んで): 表題が XBRL の file 名、出典の値の小数が読みにくい(「61.274 百万円」)、"
                  u"支出の符号(文「支出112百万円」に「−111.15」)、対象外・判断しないの抜粋が数の途中で切れる。",
                  u"**司令塔の失敗(2026-10-21)**: IFRS のラベルを標準ラベルの folder に置いたら、`load_labels(dir)` が `*_lab.xml` を全部読むので 2 書類の報告が変わり、"
                  u"記録の門が赤になるところだった",
                  u"file を `~/.cache/audit-core/edinet-taxonomy-ifrs/2025-11-01/` に移して戻した",
                  u"= ラベルは folder の中身でなく、sha256 で照合した名簿で読む。"):
            self.assertIn(s, b, s)

    def test_5_section_0_numbers_match_the_record(self):
        """R2-1 の 10 個の数が記録 `customer_report_2026-10-21.json` の節の件数と同じ(P22 と P25 の 5 節ずつ)。各 profile で節の和は 7,799。
        §0 の (a)(概数)は記録の「文の字に百万円・千円・億円・兆円があるが claim の単位が円の行(概数)」の各欄以下(封の数 ⊂ 概数の行。等号ではない = docstring (1))。"""
        by = dict(rows(sec(self.t, "## §2", "## §3"), "R2"))
        r21 = cells(by["1"])[1]
        m = re.search(r"\(P22: ([\d, /]+)、P25: ([\d, /]+)\)", r21)
        self.assertIsNotNone(m, r21)
        sealed = {"P22": [num(x) for x in m.group(1).split(" / ")], "P25": [num(x) for x in m.group(2).split(" / ")]}
        self.assertEqual([len(v) for v in sealed.values()], [5, 5])
        recs, r = record_sections()
        for p in ("P22", "P25"):
            self.assertEqual(sealed[p], recs[p], u"R2-1 の %s の 5 つの数が記録と違う" % p)
            self.assertEqual(sum(recs[p]), 7799)
            self.assertEqual(r[p]["claims"], 7799)
            self.assertEqual(r[p]["書類数"], 67)
        # 記録の概数(P25)との突き合わせ
        n = s0_numbers(sec(self.t, "## §0 ", "## §1"))
        approx = r["P25"]["文の字に百万円・千円・億円・兆円があるが claim の単位が円の行(span の字から数えた概数)"]
        self.assertEqual((approx["違う"], approx["要確認"], approx["判断しない"], approx["一致"], approx["対象外"]), (86, 466, 24, 924, 0))
        self.assertLessEqual(n["a_wrong"], approx["違う"])
        self.assertLessEqual(n["a_check"], approx["要確認"])
        self.assertLessEqual(n["a_nojudge"], approx["判断しない"])
        self.assertLessEqual(n["a_match"], approx["一致"])
        # 4,083 の「違う」の部分(proto.json で 260)は、記録の「文が金額の単位で出典の値がある『違う』」(P25)と同じ数(封の字には 260 は無く、記録側の確認)
        self.assertEqual(r["P25"]["単位の検査"]["文が金額の単位で出典の値がある「違う」"], 260)
        self.assertEqual(r["P25"]["単位の検査"]["出典の値の単位が文と違う"], 0)
        # 書類は 67、(e) の hex 3 本 × 67(記録の「入力の sha256」の書類数)
        self.assertEqual(len(jload(RECORD_JSON)["入力の sha256"][u"書類 67 の docID\\tsha256(point_prior の記録の「文あり」)"]), n["docs"])

    def test_6_section_1_nine_items(self):
        b = sec(self.t, "## §1", "## §2")
        items = re.findall(r"(?m)^(\d)\. (\*\*[^*]+\*\*.*)$", b)
        self.assertEqual([i for i, _ in items], [str(k) for k in range(1, 10)])
        starts = {"1": u"**ラベルの読み方**: ", "2": u"**(a) 単位**: ", "3": u"**桁**: ", "4": u"**符号**: ", "5": u"**(c) 英字**: ",
                  "6": u"**(d)** ", "7": u"**(e) 指紋**: ", "8": u"**表題**: ", "9": u"**抜粋**: "}
        body = dict(items)
        for k, s in starts.items():
            self.assertTrue(body[k].startswith(s), (k, body[k][:20]))
        self.assertIn(u"## §1 中身(`report_customer.py` だけ)", b)
        # 1 ラベル: 名簿に名前・バイト・sha256・取得元・人間の許可、README に取り方 1 行、名簿の file だけを読む、sha が合わない file は使わない
        for s in (u"`fixtures/xbrl/taxonomy_labels_sha256.txt` に `%s`(2,593,515 バイト、sha256 `%s`、取得元 `%s`、人間の許可 2026-10-21「取って良い」)を足し、"
                  % (JPIGP_NAME, JPIGP_SHA, JPIGP_URL),
                  u"`TAXONOMY_LABELS_README.md` に取り方を 1 行。",
                  u"module は**名簿に在る file 名だけ**を読み、sha256 が合わない file は使わない(使わなかったことを provenance に書く)。",
                  u"名簿に無い file は folder に在っても読まない。",
                  u"jpigp の file は実装の便で標準の folder に戻す。"):
            self.assertIn(s, body["1"], s)
        # 2 単位
        for s in (u"文の値は span の中で claim の値と同じ金額の字をそのまま出し、出典の値は同じ単位・同じ書き方に直す。",
                  u"語の主張は span の中でいちばん近い金額の字の単位、無ければ書類で最も多い単位。",
                  u"同じ金額の字が無い行は claim の単位のまま出し、読み取れない行として数える。"):
            self.assertIn(s, body["2"], s)
        # 3 桁 / 4 符号
        self.assertIn(u"出典の値は文の書いた桁に丸めた字を先に、丸める前の値を括弧で後に(例「61 百万円(61.274)」)。", body["3"])
        self.assertIn(u"出典の値が負なら「△」で書く(日本の財務諸表の書き方)。符号の判定は変えない。", body["4"])
        # 5 英字
        for s in (u"名簿の標準ラベル(jpcrp・jppfs・jpigp)と書類の ZIP の `XBRL/PublicDoc/*_lab.xml`(書類自身のラベル)から引く。", u"CLI に `--zip`。"):
            self.assertIn(s, body["5"], s)
        # 6 但し書き
        self.assertIn(u"「違う」の意味の欄に「文の誤りか、当てた出典の誤りかは決めない」。", body["6"])
        # 7 指紋
        for s in (u"sha256・engine の指紋・profile・道具・ラベルの sha256 は本文から外し、同じ名前の `.provenance.json`(本文の sha256 を含む、key を並べ時刻なし)に出す。",
                  u"本文の末尾は「…は同じ名前の `.provenance.json`(機械用)に置いた。」の 1 行だけ。",
                  u"本文と json のどちらも同じ入力から同じバイト列。"):
            self.assertIn(s, body["7"], s)
        # 8 表題 / 9 抜粋
        for s in (u"`--zip` があれば書類の DEI(提出者名・書類の種類・当期の期末日)から「<提出者名> <書類の種類>(<期末日>)の数の点検」。", u"無ければ今の字。"):
            self.assertIn(s, body["8"], s)
        self.assertIn(u"対象外・判断しないの抜粋は数の字の途中で切らない(切るなら数の前か後)。", body["9"])

    def test_7_jpigp_facts_are_written_once_and_agree(self):
        """jpigp の sha256・バイト数・取得元の字。封の中で 1 通り(§1.1 だけ)。sha256 は 64 桁の hex。"""
        t = self.t
        self.assertEqual(t.count(JPIGP_SHA), 1)
        self.assertEqual(len(JPIGP_SHA), 64)
        self.assertRegex(JPIGP_SHA, r"^[0-9a-f]{64}$")
        self.assertEqual(t.count(JPIGP_URL), 1)
        self.assertEqual(t.count(u"2,593,515 バイト"), 1)
        self.assertEqual(JPIGP_BYTES, 2593515)
        # 取得元は金融庁の taxonomy の jpigp の 2025-11-01 の label(jppfs・jpcrp の取り方と同じ host・同じ版)
        self.assertTrue(JPIGP_URL.startswith("http://disclosure.edinet-fsa.go.jp/taxonomy/jpigp/2025-11-01/label/"))
        readme = text(ROSTER_README)
        self.assertIn("http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/2025-11-01/label/jppfs_2025-11-01_lab.xml", readme)

    def test_8_the_roster_has_no_jpigp_yet(self):
        """封が先: 封の commit 時点の名簿は jppfs・jpcrp の 2 行だけ、README に jpigp は無い。後は LATER_ROSTER で宣言する。"""
        lines = [l for l in text(ROSTER).splitlines() if l.strip() and not l.startswith("#")]
        if not LATER_ROSTER:
            self.assertEqual(len(lines), 2, lines)
            self.assertEqual(sorted(l.split()[-1] for l in lines), ["jpcrp_2025-11-01_lab.xml", "jppfs_2025-11-01_lab.xml"])
            self.assertNotIn("jpigp", text(ROSTER))
            self.assertNotIn("jpigp", text(ROSTER_README))
            self.assertNotIn(JPIGP_SHA, text(ROSTER))
        else:
            line, seal_rel = LATER_ROSTER["roster"]
            self.assertTrue(git("log", "--diff-filter=A", "--format=%H", "--", seal_rel).stdout.split(), u"遷移を宣言した封が履歴に無い")
            self.assertIn(line, text(ROSTER))
            self.assertEqual(line, "%s  %s" % (JPIGP_SHA, JPIGP_NAME))
            if LATER_ROSTER.get("readme_has_jpigp"):
                self.assertIn(JPIGP_NAME, text(ROSTER_README))
                self.assertIn(JPIGP_SHA, text(ROSTER_README))
                self.assertIn(JPIGP_URL, text(ROSTER_README))
            self.assertEqual(len(lines), 3, lines)
        # 2 行の sha256 は封の外の正本(README の表)と同じ
        for l in lines:
            if "jppfs" in l:
                self.assertTrue(l.startswith("bf56ea1585afe426b398a9053ec4de4dbeafc211a53675b5d6d19453e4e04bf4"))
            if "jpcrp" in l:
                self.assertTrue(l.startswith("df9c23764ec9a63cb65b5ef62e79a2907c590523797421442ea2a60e334cd684"))

    @unittest.skipUnless(os.path.exists(IFRS_CACHE), u"jpigp の file がこの機械の ~/.cache/audit-core/edinet-taxonomy-ifrs/ に無い")
    def test_8b_the_cached_jpigp_file_is_the_sealed_one(self):
        with io.open(IFRS_CACHE, "rb") as fh:
            data = fh.read()
        self.assertEqual(len(data), JPIGP_BYTES)
        self.assertEqual(hashlib.sha256(data).hexdigest(), JPIGP_SHA)

    def test_9_the_target_module_is_the_one_at_the_seal_and_has_no_zip_or_provenance_yet(self):
        got = sha16(TARGET)
        if got != TARGET_AT_SEAL:
            self.assertIn(TARGET, LATER_TARGET, u"**%s が動いている(実装の便の commit で LATER_TARGET に遷移を宣言する)**" % TARGET)
            later, seal_rel = LATER_TARGET[TARGET]
            self.assertTrue(git("log", "--diff-filter=A", "--format=%H", "--", seal_rel).stdout.split(), u"遷移を宣言した封が履歴に無い")
            self.assertEqual(got, later, u"**%s が、宣言された遷移の値とも違う**" % TARGET)
            return
        src = text(os.path.join(ROOT, TARGET))
        for s in ("--zip", "provenance", "jpigp", "△"):
            self.assertNotIn(s, src, u"封より先に実装が入っている: " + s)
        # 試験側にも、封より先の試験が無い
        tt = text(os.path.join(ROOT, "tests", "adapters", "xbrl", "test_report_customer.py"))
        for s in ("--zip", "provenance.json", "jpigp"):
            self.assertNotIn(s, tt, u"封より先の試験が入っている: " + s)

    def test_10_new_files_do_not_exist_yet(self):
        """封が実装より先であること。§4 の新規 4 本は作業木にも履歴にも無い(実装の便で「在る」に直す。順序は test_14 が縛る)。"""
        if LATER_TARGET:
            self.skipTest(u"実装の便の後(LATER_TARGET が宣言されている)。順序は test_14")
        for rel in NEW_FILES:
            self.assertFalse(os.path.exists(os.path.join(ROOT, rel)), u"封より先に在る: " + rel)
            self.assertEqual(git("log", "--format=%H", "--", rel).stdout.strip(), "", u"封より先に履歴に現れた: " + rel)
        for rel in EXISTING_EDITED:
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), u"直す対象の既存 file が無い: " + rel)

    def test_11_untouched_files_keep_their_sha(self):
        """R2-7: `report.py`(人間の決定 2026-10-13)・`verify_document.py`・vocabulary・recipes・registry_setup・comparators を含む、
        report_customer.py 以外の adapters/xbrl 15 file は 0 行。宣言の遷移を持たない: 動いたら赤のまま。"""
        py = sorted(f for f in os.listdir(os.path.join(ROOT, "adapters", "xbrl")) if f.endswith(".py"))
        self.assertEqual(["adapters/xbrl/" + f for f in py], sorted(list(UNTOUCHED) + [TARGET]), u"adapters/xbrl の file の集合が変わった")
        self.assertEqual(len(UNTOUCHED), 15)
        for rel, want in sorted(UNTOUCHED.items()):
            got = sha16(rel)
            if got != want and rel in UNTOUCHED_LATER:
                later, seal_rel = UNTOUCHED_LATER[rel]
                self.assertTrue(git("log", "--diff-filter=A", "--format=%H", "--", seal_rel).stdout.split(),
                                u"**%s が動いているのに、遷移を宣言した封 %s が履歴に無い**" % (rel, seal_rel))
                self.assertEqual(got, later, u"**%s が、宣言された遷移の値とも違う**" % rel)
                continue
            self.assertEqual(got, want, u"**%s が動いている(この封は触らない)**" % rel)
        # 遷移を持つのは P26 の封が書き換えた engine の 4 file だけ(comparators.py・report.py・verify_document.py ほかは遷移を持たない)
        # 2026-10-28(既定を P26 -> P27 に切り替える 段 2): verify_document.py だけは docstring の 1 行の直しとして封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md が遷移を宣言した
        self.assertEqual(sorted(UNTOUCHED_LATER), ["adapters/xbrl/extract.py", "adapters/xbrl/recipes.py", "adapters/xbrl/registry_setup.py", "adapters/xbrl/verify_document.py", "adapters/xbrl/vocabulary.py"])
        self.assertEqual(UNTOUCHED_LATER["adapters/xbrl/verify_document.py"], ("c3791080ab5aef2f", SEAL_DEFAULT_P27))
        for rel in ("comparators", "report"):
            self.assertNotIn("adapters/xbrl/%s.py" % rel, UNTOUCHED_LATER)
        # R2-7 が名指す 7 つ(core/ は fingerprint の core_py_sha256 が縛る)
        for rel in ("report", "verify_document", "vocabulary", "recipes", "registry_setup", "comparators"):
            self.assertIn("adapters/xbrl/%s.py" % rel, UNTOUCHED)
        # report.py の golden の試験が在る(R2-7 の「不変」の相手)
        t = text(os.path.join(ROOT, "tests", "adapters", "xbrl", "test_report.py"))
        self.assertEqual(len(re.findall(r"(?m)^    def test_", t)), 13)

    def test_12_engine_fingerprint_is_the_one_at_the_seal_or_a_declared_transition(self):
        """`adapter_xbrl_py_sha256` は report_customer.py の中身で動く(file の数 16 は動かない)。封の commit 時点の値を字で留め、
        後は `LATER_FINGERPRINT` に宣言された値(と、宣言した封が履歴に在ること)だけを受け入れる。core の指紋は動かない。"""
        from adapters.xbrl import verify_document as VD
        fp = VD.engine_fingerprint()
        for k, want in sorted(FINGERPRINT_AT_SEAL.items()):
            got = fp[k]
            if got != want and k in LATER_FINGERPRINT:
                later, seal_rel = LATER_FINGERPRINT[k]
                self.assertTrue(git("log", "--diff-filter=A", "--format=%H", "--", seal_rel).stdout.split(),
                                u"**%s が動いているのに、遷移を宣言した封 %s が履歴に無い**" % (k, seal_rel))
                self.assertEqual(got, later, u"**%s が、宣言された遷移の値とも違う**" % k)
                continue
            self.assertEqual(got, want, u"**%s が動いている(実装の便の commit で LATER_FINGERPRINT に遷移を宣言する)**" % k)
        # 指紋が動くのは report_customer.py が動いたときだけ(別の file が動いていたら test_11 が赤)
        if fp["adapter_xbrl_py_sha256"] != FINGERPRINT_AT_SEAL["adapter_xbrl_py_sha256"]:
            self.assertNotEqual(sha16(TARGET), TARGET_AT_SEAL)
        self.assertEqual(fp["core_py_sha256"], FINGERPRINT_AT_SEAL["core_py_sha256"])

    def test_13_frozen_bundle_is_the_one_at_the_seal_or_a_declared_transition(self):
        src = text(os.path.join(ROOT, "fixtures", "frozen_bundle_sha.py"))
        count = int(re.search(r"(?m)^FROZEN_COUNT = (\d+)", src).group(1))
        gens = re.findall(r'\("([0-9a-f]{64})",\n', src)
        self.assertEqual(count, FROZEN_COUNT_AT_SEAL)
        r = subprocess.run([sys.executable, os.path.join(ROOT, "fixtures", "frozen_bundle_sha.py")], cwd=REPO, capture_output=True, text=True)
        out = r.stdout
        m = re.search(r"対象 (\d+) 本 @ ", out)
        self.assertIsNotNone(m, out)
        self.assertEqual(int(m.group(1)), FROZEN_COUNT_AT_SEAL)
        self.assertIn(FROZEN_BUNDLE_AT_SEAL, gens, u"封の commit 時点の世代は消さない")
        if "bundle" in LATER_FROZEN:
            later, seal_rel = LATER_FROZEN["bundle"]
            self.assertTrue(git("log", "--diff-filter=A", "--format=%H", "--", seal_rel).stdout.split(), u"遷移を宣言した封が履歴に無い")
            self.assertEqual(r.returncode, 0, out)
            self.assertIn(later, out)
            self.assertEqual(gens[-1], later)
            self.assertIn(FROZEN_BUNDLE_FIX, gens, u"この封の実装の便の世代は消さない")
        else:
            self.assertEqual(r.returncode, 0, u"**frozen_bundle が動いている(実装の便の commit で LATER_FROZEN に遷移を宣言する)**\n" + out)
            self.assertIn(FROZEN_BUNDLE_AT_SEAL, out)
            self.assertEqual(gens[-1], FROZEN_BUNDLE_AT_SEAL)

    def test_14_limits_are_written(self):
        b = sec(self.t, "## §3", "## §4")
        for s in (u"文の数の読み取りの崩れ(「2兆3,471億円」→ 3,471億円 等)は engine(extract)の側で、報告では直せない(P26 の封で扱う)。",
                  u"「違う」に出る正しい文の主因(丸めた差・増減要因の語・区分の取り違え)は engine の側(P26)。報告の形は空振りを減らさない。",
                  u"`no_same_value` の名指した当期の値は `verify_document` の出力に欄が無く出さない(変わらず)。",
                  u"語の主張の単位を書類の単位に落とした行は、文から読み取っていない(試作で 444 行)。"):
            self.assertIn(s, b, s)
        self.assertEqual(len(re.findall(r"(?m)^- ", b)), 4)

    def test_15_closed_file_list_and_order(self):
        b = sec(self.t, "## §4")
        first = b[:b.index(u"\n順序:")]
        chain_files = ["adapters/xbrl/report_customer.py",
                       "fixtures/xbrl/taxonomy_labels_sha256.txt", "fixtures/xbrl/TAXONOMY_LABELS_README.md",
                       "tests/adapters/xbrl/test_report_customer.py",
                       "measure/xbrl_customer_report_fix_2026-10-21.py",
                       "fixtures/xbrl/customer_report_fix_2026-10-21.json",
                       "docs/XBRL_CUSTOMER_REPORT_FIX_RESULT_2026-10-21.md",
                       "tests/measure/test_xbrl_customer_report_fix_result.py"]
        pos = []
        for rel in chain_files:
            tk = "`%s`" % rel
            self.assertEqual(first.count(tk), 1, rel)
            pos.append(first.index(tk))
        self.assertEqual(pos, sorted(pos), u"file 一覧の順が変わった")
        # 新規 4 本と既存の直し 4 本(module・名簿・README・既存の試験)が一覧の全部
        self.assertEqual(set(chain_files), set(NEW_FILES) | set(EXISTING_EDITED) | {"fixtures/xbrl/TAXONOMY_LABELS_README.md"})
        self.assertEqual(len(NEW_FILES), 4)
        for s in (u"`tests/adapters/xbrl/test_report_customer.py`(golden・単位・名簿・指紋・表題・抜粋・決定論)",
                  u"README の入口の CLI(`--zip`)",
                  u"pin の遷移(engine の指紋・frozen_bundle の新世代・point_prior B-5・ritual R-8・c13a746 の結果門の記録の読み方)",
                  u"→ 覆い。"):
            self.assertIn(s, first, s)
        p = [first.index(s) for s in (u"`tests/measure/test_xbrl_customer_report_fix_result.py`", u"README の入口の CLI", u"pin の遷移", u"→ 覆い。")]
        self.assertEqual(p, sorted(p))
        # 順序の字
        order = b[b.index(u"\n順序:"):]
        self.assertIn(u"順序: 人間の方針(2026-10-21 朝)→ **この封 + 封の門を commit** → 実装(別席)→ 凍結 → 独立監査 → commit → axis3 の宣言。", order)
        # 直す既存 file は在る
        for rel in EXISTING_EDITED:
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)


class OrderTest(unittest.TestCase):
    @staticmethod
    def _added(rel):
        shas = [s for s in git("log", "--diff-filter=A", "--format=%H", "--", rel).stdout.split() if s]
        return shas[-1] if shas else None

    def test_16_the_seal_precedes_every_later_file_and_edit(self):
        tracked = git("ls-files", "--error-unmatch", SEAL_REL).returncode == 0
        edited = list(EXISTING_EDITED[:3])   # module・名簿・名簿の README(c13a746 の後に触った commit)
        if not tracked:
            # 封が履歴に無い間に、後の file が履歴に現れる・既存の直しの commit が c13a746 の後に在れば赤(順序の逆転)。
            for rel in NEW_FILES:
                self.assertIsNone(self._added(rel), u"封より先に履歴に現れた: " + rel)
            for rel in edited:
                self.assertEqual(git("log", "--format=%H", "c13a746..HEAD", "--", rel).stdout.strip(), "", u"封より先に直した: " + rel)
            self.skipTest(u"封がまだ commit されていない(後の file が履歴に無いことだけ確かめた)")
        seal = self._added(SEAL_REL)
        for rel in NEW_FILES:
            other = self._added(rel)
            if other is None:
                continue
            self.assertNotEqual(seal, other, rel)
            self.assertTrue(git("merge-base", "--is-ancestor", seal, other).returncode == 0, rel)
        for rel in edited:
            for c in git("log", "--format=%H", "c13a746..HEAD", "--", rel).stdout.split():
                if c == seal:
                    continue
                self.assertTrue(git("merge-base", "--is-ancestor", seal, c).returncode == 0, u"封より先に直した: %s @ %s" % (rel, c))


if __name__ == "__main__":
    unittest.main()
