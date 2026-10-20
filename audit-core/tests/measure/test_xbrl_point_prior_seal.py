# -*- coding: utf-8 -*-
u"""穴 2 つ(単位語「ポイント」/ 前期の値を通す)の広さを測る封 docs/XBRL_POINT_PRIOR_SEAL_2026-10-20.md を固定する。
人間の方針の引用・予測 A-1〜A-4 / B-1〜B-5 と外れ方・§0-1 の先に測った数(字・記録の値・cache が在る機械では実走)・
§3 の「engine の直しはこの封の外」・§4 の file 一覧・封が実装より先であること(順序)を縛る。"""
import glob
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))

SEAL_REL = "docs/XBRL_POINT_PRIOR_SEAL_2026-10-20.md"
SEAL = os.path.join(ROOT, SEAL_REL)
RITUAL_JSON = os.path.join(ROOT, "fixtures", "xbrl", "ritual_2026-10-20.json")
S2_JSON = os.path.join(ROOT, "fixtures", "xbrl", "gen_c", "hybrid_s2_2026-10-20.json")
CACHE_GLOB = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet", "*.zip")
# §4 の file 一覧(この順で書かれている)
FILES = ("measure/xbrl_point_prior_2026-10-20.py",
         "fixtures/xbrl/point_prior_2026-10-20.json",
         "docs/XBRL_POINT_PRIOR_RESULT_2026-10-20.md",
         "tests/measure/test_xbrl_point_prior_result.py")
# 封より後でなければ git 履歴に現れてはならない新規 file(§4 の 4 本そのもの)
AFTER = FILES


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


def predictions(block, tag):
    ids = re.findall(r"(?m)^\| \*\*%s-(\d+)\*\* \|" % tag, block)
    lines = re.findall(r"(?m)^\| \*\*%s-\d+\*\* \|.*$" % tag, block)
    return ids, lines


def s01(t):
    return sec(t, "## §0-1", "## §1")


def s01_numbers(b):
    m0 = re.search(r"(\d+) 書類のうち経営分析の文\(`select_mdna`\)を持つ \*\*(\d+) 書類\*\*\(残り (\d+) は文が無く claim 0 件", b)
    m1 = re.search(r"`数字\+ポイント` の印字は (\d+) 件\((\d+) 書類\)", b)
    m2 = re.search(r"単位 ポイント の claim (\d+) 件は \*\*GROUNDED (\d+)・POINTER_NOT_FOUND (\d+)・UNVERIFIABLE (\d+)・VALUE_MISMATCH (\d+)\*\*", b)
    m3 = re.search(r"T6 (\d+) 件のうち (\d+) 件", b)
    assert m0 and m1 and m2 and m3, u"§0-1 の数の書き方が変わった"
    return {"cache": int(m0.group(1)), "with_text": int(m0.group(2)), "without_text": int(m0.group(3)),
            "prints": int(m1.group(1)), "docs": int(m1.group(2)),
            "claims": int(m2.group(1)),
            "states": {"GROUNDED": int(m2.group(2)), "POINTER_NOT_FOUND": int(m2.group(3)),
                       "UNVERIFIABLE": int(m2.group(4)), "VALUE_MISMATCH": int(m2.group(5))},
            "t6_total": int(m3.group(1)), "t6_grounded": int(m3.group(2))}


class SealTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = text(SEAL)

    def test_1_human_policy_is_quoted(self):
        head = self.t[:self.t.index("\n## §0 ")]
        self.assertIn(u"**人間の方針(2026-10-20)「君に任せる進めて」**。", head)
        self.assertIn(u"儀式 → 0 USD の測定 2 つ → engine の直し 1 つ(承認要)→ 技術線を止めて顧客へ", head)
        self.assertIn(u"**数を見てから封・予測を直さない。外れは外れとして残す。**", head)

    def test_2_two_holes_and_zero_cost_procedure(self):
        b = sec(self.t, "## §0 ", "## §0-1")
        for s in (u"**穴 A(単位語「ポイント」)**", u"**穴 B(前期の値を通す)**", u"`verify_document`"):
            self.assertIn(s, b, s)
        p = sec(self.t, "## §1", "## §2")
        for s in (u"engine 0 行。0 USD。通信なし", u"`measure/xbrl_point_prior_2026-10-20.py --stage a|b`",
                  u"`~/.cache/audit-core/edinet/*.zip`、281 件。鍵は要らない", u"うち経営分析の文を持つ 67 件が分母。文の無い 214 件は記録に「文なし」と残し分母から外す",
                  u"全書類 281 件のうち経営分析の文を持つ 67 件が分母", u"既定 P21 の `verify_document(zb, None, None)`",
                  u"**対照**: 同じ書類で単位が「％」の claim", u"`inject.build_t6` と同じ条件", u"25 件 batch",
                  u"`verify_document(zb, None, text)`", u"`fixtures/xbrl/point_prior_2026-10-20.json`",
                  u"`docs/XBRL_POINT_PRIOR_RESULT_2026-10-20.md`", u"`tests/measure/test_xbrl_point_prior_result.py`"):
            self.assertIn(s, p, s)

    def test_3_nine_predictions_each_with_a_way_to_fail(self):
        b = sec(self.t, "## §2", "## §3")
        ia, la = predictions(b, "A")
        ib, lb = predictions(b, "B")
        self.assertEqual(ia, ["1", "2", "3", "4"])
        self.assertEqual(ib, ["1", "2", "3", "4", "5"])
        self.assertEqual(len(la) + len(lb), 9)
        for line in la + lb:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            self.assertEqual(len(cells), 3, line)
            self.assertTrue(cells[1], u"予測が空: " + line)
            self.assertTrue(cells[2], u"外れ方が空: " + line)
        for s in (u"67 書類で単位「ポイント」の claim は **29〜45 件**", u"**10〜25%**", u"**65〜85%**", u"**ポイントより 20 pt 以上高い**", u"20 pt 未満",
                  u"**半分以下**", u"過半が正しく結べた", u"**1 書類あたり中央値 3〜15**", u"経営分析の文を持つ 67 書類で T6 が作れる site", u"合計 **200〜1,000**", u"割合は 30〜70%**",
                  u"30% 未満 / 70% 超", u"**全部 `Prior1Year…`**", u"2% 超", u"**合計 30 分以内**", u"67 書類 × verify 1.3 秒 ≈ 1.5 分", u"30 分超",
                  u"engine 0 行", u"1 行でも触る / 既存が赤",
                  u"**本当に測っているのは A-2・A-3・B-2 である**"):
            self.assertIn(s, b, s)

    def test_4_section_0_1_numbers_are_pinned_as_written(self):
        b = s01(self.t)
        n = s01_numbers(b)
        self.assertEqual(n["cache"], 281)
        self.assertEqual((n["with_text"], n["without_text"]), (67, 214))
        self.assertEqual(n["with_text"] + n["without_text"], n["cache"])
        self.assertLessEqual(n["docs"], n["with_text"])   # 印字のある 15 書類は文を持つ 67 書類の中
        self.assertEqual((n["prints"], n["docs"]), (29, 15))
        self.assertEqual(n["claims"], 29)
        self.assertEqual(n["states"], {"GROUNDED": 4, "POINTER_NOT_FOUND": 20, "UNVERIFIABLE": 4, "VALUE_MISMATCH": 1})
        self.assertEqual(sum(n["states"].values()), n["claims"])
        self.assertEqual(20 + 4 + 1, 25)   # 「正しい行も 25 / 29 を止めるか保留」
        self.assertIn(u"正しい行も 25 / 29 を止めるか保留にする", b)
        self.assertEqual((n["t6_total"], n["t6_grounded"]), (10, 6))
        for s in (u"N125 `2百万円 → 3百万円`", u"N199 `19 → 18`", u"`no_element`", u"`no_element(point without prior phrase)`",
                  u"`no_subject`", u"既定 P21", u"241"):
            self.assertIn(s, b, s)
        # §2 の A-1・A-2・B-2 が §0-1 と同じ数を言っている
        p = sec(self.t, "## §2", "## §3")
        a1 = [l for l in p.splitlines() if l.startswith("| **A-1**")][0]
        a2 = [l for l in p.splitlines() if l.startswith("| **A-2**")][0]
        b2 = [l for l in p.splitlines() if l.startswith("| **B-2**")][0]
        self.assertIn(u"印字 29 件は 281 書類のうち経営分析の文を持つ 67 書類の文で数えた数", a1)
        self.assertIn(u"15 書類", a1)
        self.assertIn(u"4 / 29 = 13.8%", a2)
        self.assertEqual(round(100.0 * 4 / 29, 1), 13.8)
        self.assertIn(u"6 / 10 = 60%", b2)

    def test_5_ritual_record_has_n125_and_n199_moved_from_current_to_prior_and_still_grounded(self):
        # §0-1 の「N125・N199 は参照先が当期 → 前期へ移って GROUNDED のまま」を儀式の記録で確かめる
        rec = jload(RITUAL_JSON)
        rows = dict((x["id"], x) for x in rec["通した の一覧"])
        self.assertIn(u"N125", self.t)
        self.assertIn(u"N199", self.t)
        for i, a, b in (("N125", u"2百万円", u"3百万円"), ("N199", u"19百万円", u"18百万円")):
            x = rows[i]
            self.assertEqual(x["結果"], "PASSED", i)           # 通した = GROUNDED のまま
            self.assertEqual((x["元の字"], x["後の字"]), (a, b), i)
            self.assertIn("@CurrentYear", x["参照先(注入前)"], i)
            self.assertIn("@Prior1Year", x["参照先(注入後)"], i)
            self.assertTrue(x["参照先が動いた"], i)
        moved = [x["id"] for x in rec["通した の一覧"] if x["参照先が動いた"]]
        self.assertEqual(sorted(moved), ["N125", "N199"])
        self.assertEqual(rec["通した のうち参照先が動いた(注入の前後で GROUNDED の参照先が違う)"], 2)

    def test_6_stage2_record_has_core_itself_grounding_t6_six_of_ten(self):
        rec = jload(S2_JSON)
        t6 = rec["集計"]["型別"]["T6_PRIOR"]["Core 自身が GROUNDED"]
        n = s01_numbers(s01(self.t))
        self.assertEqual((t6["分子"], t6["分母"]), (n["t6_grounded"], n["t6_total"]))
        self.assertEqual((t6["分子"], t6["分母"]), (6, 10))
        self.assertEqual(t6["率"], 60.0)

    def test_7_engine_fix_is_outside_this_seal(self):
        b = sec(self.t, "## §3", "## §4")
        self.assertIn(u"穴 B の直し(期間を縛る)は engine の変更で、この封の外。", b)
        self.assertIn(u"**この結果を見てから別の封(人間の承認)で決める。**", b)
        self.assertTrue(b.lstrip().startswith(u"## §3") and u"281 書類のうち経営分析の文を持つのは 67" in b.split("\n- ")[1], u"§3 の先頭の限界")
        for s in (u"文の無い 214 は提出書類の file 名が `jpsps…-asr-`、文のある 67 は `jpcrp…-asr-`", u"四半期報告書ではない",
                  u"281 書類は手元の cache の全部で、無作為ではない", u"B は「前期の値がそのまま書かれる」誤りだけ"):
            self.assertIn(s, b, s)

    def test_8_closed_file_list(self):
        b = sec(self.t, "## §4")
        first = b[:b.index(u"**これ以外に触らない。")]
        pos = []
        for rel in FILES:
            tok = "`%s`" % rel
            self.assertEqual(first.count(tok), 1, rel)
            pos.append(first.index(tok))
        self.assertEqual(pos, sorted(pos), u"file 一覧の順が変わった")
        self.assertEqual(len(FILES), 4)
        self.assertIn(u"**これ以外に触らない。engine 0 行。0 USD。**", b)
        self.assertIn(u"`tests/measure/test_xbrl_point_prior_seal.py`", b)
        self.assertIn(u"この封 + 封の門", b)
        self.assertIn(u"commit → 実装(別席)→ 凍結 → 独立監査 → commit → push", b)


class LiveReproductionTest(unittest.TestCase):
    """cache(~/.cache/audit-core/edinet/*.zip)が在る機械では §0-1 の (b)(c) を実走して封の字と一致を見る。
    cache が無い機械では skip(記録の縛りは SealTest が走る)。"""

    @staticmethod
    def _kind(zb):
        import zipfile
        zf = zipfile.ZipFile(io.BytesIO(zb))
        for n in zf.namelist():
            b = os.path.basename(n)
            m = n.endswith(".xbrl") and "PublicDoc" in n and re.match(r"(jp[a-z]+)\d+-(\w+)-", b)
            if m:
                return m.group(1) + u"…-" + m.group(2) + u"-"
        return None

    @classmethod
    def setUpClass(cls):
        cls.zips = sorted(glob.glob(CACHE_GLOB))
        if not cls.zips:
            return
        spec = importlib.util.spec_from_file_location("fp_seal_gate", os.path.join(ROOT, "measure", "false_pass_2026-10-14.py"))
        cls.fp = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.fp)
        cls.want = s01_numbers(s01(text(SEAL)))
        # (b) 経営分析の文を持つ書類だけが数えられる(select_mdna が無い書類は mdna_text が KeyError)
        rx = re.compile(r"\d+(?:\.\d+)?ポイント")
        cls.hit_docs, cls.prints = [], 0
        cls.with_text = cls.without_text = 0
        cls.kinds = {}
        for z in cls.zips:
            with open(z, "rb") as fh:
                zb = fh.read()
            try:
                t = cls.fp.mdna_text(zb)
            except KeyError:
                cls.without_text += 1
                cls.kinds[("文なし", cls._kind(zb))] = cls.kinds.get(("文なし", cls._kind(zb)), 0) + 1
                continue
            cls.with_text += 1
            cls.kinds[("文あり", cls._kind(zb))] = cls.kinds.get(("文あり", cls._kind(zb)), 0) + 1
            n = len(rx.findall(t))
            if n:
                cls.prints += n
                cls.hit_docs.append((z, zb))

    def need_cache(self):
        if not self.zips:
            self.skipTest(u"cache(~/.cache/audit-core/edinet/*.zip)が無い機械")

    def test_g1_cache_count_and_prints_match_the_seal(self):
        self.need_cache()
        self.assertEqual(len(self.zips), self.want["cache"])
        self.assertEqual(self.prints, self.want["prints"])
        self.assertEqual(len(self.hit_docs), self.want["docs"])
        # 文を持つ書類 67・文なし 214(封 §0-1 の「67 書類」「残り 214」)
        self.assertEqual((self.with_text, self.without_text), (self.want["with_text"], self.want["without_text"]))
        self.assertEqual(self.with_text + self.without_text, len(self.zips))
        # 封 §3 の file 名の事実
        self.assertEqual(self.kinds, {(u"文なし", u"jpsps…-asr-"): 214, (u"文あり", u"jpcrp…-asr-"): 67})

    def test_g2_default_verify_on_the_hit_docs_reproduces_the_point_claim_states(self):
        self.need_cache()
        from adapters.xbrl.verify_document import verify_document
        states = {}
        total = 0
        for _, zb in self.hit_docs:
            out = verify_document(zb, None, None)   # profile 省略 = 道具の既定(P21)
            for c in out["claims"]:
                if c.get("unit") == u"ポイント":
                    total += 1
                    states[c["state"]] = states.get(c["state"], 0) + 1
        self.assertEqual(total, self.want["claims"])
        self.assertEqual(states, self.want["states"])


class OrderTest(unittest.TestCase):
    @staticmethod
    def _added(rel):
        out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "--", rel],
                             cwd=ROOT, capture_output=True, text=True)
        shas = [s for s in out.stdout.split() if s]
        return shas[-1] if shas else None

    def test_9_the_seal_precedes_every_later_file(self):
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", SEAL_REL],
                                 cwd=ROOT, capture_output=True).returncode == 0
        if not tracked:
            # 封が履歴に無い間に、後の file が履歴に現れていたら赤(順序の逆転)。何も無いことは pass と言わず skip で残す。
            for rel in AFTER:
                self.assertIsNone(self._added(rel), u"封より先に履歴に現れた: " + rel)
            self.skipTest(u"封がまだ commit されていない")
        seal = self._added(SEAL_REL)
        for rel in AFTER:
            other = self._added(rel)
            if other is None:
                continue
            self.assertNotEqual(seal, other, rel)
            self.assertTrue(subprocess.run(["git", "merge-base", "--is-ancestor", seal, other],
                                           cwd=ROOT, capture_output=True).returncode == 0, rel)


if __name__ == "__main__":
    unittest.main()
