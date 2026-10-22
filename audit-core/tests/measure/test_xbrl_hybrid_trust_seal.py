# -*- coding: utf-8 -*-
u"""席と Core の一致の信頼(3 群)の封 docs/XBRL_HYBRID_TRUST_SEAL_2026-10-20.md を固定する。
先に分かっている事実 1〜3(席の字・Core 自身(P16)・α 型(P20))は記録・材料から数え直して封の字と一致させ、
段 1 の予測 H-1〜H-8・段 2 の予測 P-1〜P-7 が測る前に固定されていることを順序で見る。"""
import io
import json
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEAL_REL = "docs/XBRL_HYBRID_TRUST_SEAL_2026-10-20.md"
SEAL = os.path.join(ROOT, SEAL_REL)
AFTER_S1 = ("measure/xbrl_hybrid_trust_2026-10-20.py",
            "fixtures/xbrl/gen_c/hybrid_trust_2026-10-20.json",
            "docs/XBRL_HYBRID_TRUST_RESULT_2026-10-20.md",
            "tests/measure/test_xbrl_hybrid_trust_result.py")
AFTER_S2 = ("measure/xbrl_hybrid_s2_2026-10-20.py",
            "fixtures/xbrl/gen_c/hybrid_s2_material_2026-10-20.json",
            "fixtures/xbrl/gen_c/hybrid_s2_2026-10-20.json",
            "docs/XBRL_HYBRID_S2_RESULT_2026-10-20.md",
            "tests/measure/test_xbrl_hybrid_s2_result.py")
SETS = {"gen_c": ("fixtures/xbrl/gen_c/c1_2026-10-20.json", "fixtures/xbrl/gen_c/material_2026-10-20.json"),
        "cd8": ("fixtures/xbrl/cd8/score_2026-10-17.json", "fixtures/xbrl/cd8/material_2026-10-17.json")}
ALPHA = "fixtures/xbrl/gen_c/alpha_2026-10-20.json"


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sec(t, start, end=None):
    i = t.index("\n" + start)
    j = t.index("\n" + end, i) if end else len(t)
    return t[i:j]


def load(rel):
    return json.load(io.open(os.path.join(ROOT, rel), encoding="utf-8"))


def seat_facts(rows):
    inj = [r for r in rows if r[u"注入か"]]
    unc = [r for r in rows if not r[u"注入か"]]
    v = lambda rs, w: sum(1 for r in rs if r[u"席"][u"判定"] == w)
    return [len(rows), len(inj), len(unc), v(inj, u"確認済み"), v(inj, u"判定できない"),
            v(unc, u"確認済み"), v(unc, u"判定できない"), v(unc, u"誤りが在る")]


def core_state(c):
    s = c.get("state")
    if s:
        return s
    t = c[u"言うこと"]
    if t == u"確認済み":
        return "GROUNDED"
    if t == u"対応が付かない":
        return u"対応なし"
    return t


def core_facts(rows, mat):
    seat = {(r["doc"], r["id"]): r for r in rows}
    n = {}
    for doc in mat[u"書類ごと"]:
        for rid, r in doc[u"席の前に出せる分"].items():
            sr = seat[(doc["docID"], rid)]
            k = (bool(sr[u"注入か"]), sr[u"席"][u"判定"], core_state(r["Core"]))
            n[k] = n.get(k, 0) + 1
    g = lambda inj, s, c: n.get((inj, s, c), 0)
    return [g(False, u"確認済み", "GROUNDED"), g(False, u"確認済み", u"対応なし"),
            g(False, u"確認済み", "POINTER_NOT_FOUND"), g(False, u"確認済み", "VALUE_MISMATCH"),
            g(False, u"確認済み", "UNVERIFIABLE"),
            g(True, u"判定できない", "VALUE_MISMATCH"), g(True, u"判定できない", u"対応なし"),
            g(True, u"判定できない", "POINTER_NOT_FOUND"),
            sum(v for k, v in n.items() if k[0] and k[2] == "GROUNDED")]


def table_row(block, prefix):
    line = [l for l in block.splitlines() if l.startswith(prefix)][0]
    return [int(c.strip().strip("*")) for c in line.strip("|").split("|")[1:]]


def predictions(block, tag):
    ids = re.findall(r"(?m)^\| \*\*%s-(\d+)\*\* \|" % tag, block)
    lines = re.findall(r"(?m)^\| \*\*%s-\d+\*\* \|.*$" % tag, block)
    return ids, lines


class SealTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_1_human_instructions_and_the_three_groups(self):
        head = self.t[:self.t.index("\n## §0")]
        self.assertIn(u"「3 なんだけど、止めた件数も重要だし、LLM と core が同じを示し故に信頼が高いってなるのも大切では。そのためには 2 の精度が保証されなければだが」", head)
        self.assertIn(u"「P21 で 3 群を測る。LLM 単独が支持した群・LLM と Core が一致した群・LLM が支持し Core が拒否・保留した群。これで精度を比較したらどう？」", head)
        self.assertIn(u"「全て君に任せるし承認する」(段 2 の有料の席を含む承認)", head)
        b = sec(self.t, "## §0", "## §1")
        self.assertEqual(re.findall(r"(?m)^\| \*\*G(\d)\*\* \|", b), ["1", "2", "3"])
        self.assertIn(u"精度の物差しは **「注入した誤りか」**(行の `注入か`)だけ。", b)
        self.assertIn(u"**つまり、いまの材料では G1 に注入が 1 件も無く、3 群の精度は全部 100% で差が出ない(段 1 はこれを数で確定する)。差を出すには、席が通しうる誤りを作る段 2 が要る。**", b)
        self.assertIn(u"**既存の腕 D′ は Core 単独ではない**", b)
        self.assertIn(u"**「止めた」のではなく「見ていない」**", b)

    def test_2_seat_facts_match_the_records(self):
        b = sec(self.t, "## §0", "## §1")
        for name, (rec, _mat) in SETS.items():
            f = seat_facts(load(rec)["rows"])
            self.assertEqual(table_row(b, u"| %s" % name), f, name)
            self.assertEqual(f[3], 0, u"席 A が通した注入が 0 でない: " + name)

    def test_3_core_p16_facts_match_the_material(self):
        b = sec(self.t, "## §0", "## §1")
        for name, (rec, mat) in SETS.items():
            m = load(mat)
            self.assertEqual(m.get("profile"), "P16", name)
            f = core_facts(load(rec)["rows"], m)
            self.assertEqual(table_row(b, u"| %s(P16)" % name), f, name)
            self.assertEqual(f[-1], 0, u"注入で Core GROUNDED が 0 でない: " + name)

    def test_4_alpha_facts_match_the_record(self):
        b = sec(self.t, "## §0", "## §1")
        a = load(ALPHA)
        g = a[u"α-1"][u"state の分布"]
        self.assertIn(u"gen_c は GROUNDED **%d / %d**(UNPROVABLE %d・VALUE_MISMATCH %d)" % (
            g["GROUNDED"], a[u"α-1"][u"分母(席 A が 確認済み + 参照先の無改変の行)"], g["UNPROVABLE"], g["VALUE_MISMATCH"]), b)
        c = a[u"cd8(S-C2)"][u"α-1: 確認済み + 参照先の無改変の行"]
        self.assertIn(u"cd8 は **%d / %d**(UNPROVABLE %d・VALUE_MISMATCH %d)" % (
            c[u"state の分布"]["GROUNDED"], c[u"行"], c[u"state の分布"]["UNPROVABLE"], c[u"state の分布"]["VALUE_MISMATCH"]), b)
        inj = a[u"α-1(注入 25 行)"]
        self.assertEqual(inj[u"席が 参照先を出した注入の行"], 25)
        self.assertEqual(inj[u"state の分布(この script で当て直した)"].get("GROUNDED", 0), 0)
        self.assertIn(u"席が参照先を名指した注入の行(gen_c 25)で GROUNDED 0", b)

    def test_5_stage_1_procedure_and_eight_predictions(self):
        b = sec(self.t, "## §1", "## §2")
        for s in (u"**1 文字も直さない。**", u"**既定の profile(P21)**", u"全 384 行一致",
                  u"**誤りを通す = 注入の行が 二重確認 か Core のみ確認 になること。**",
                  u"**段 1 で本当に測っているのは H-2・H-3・H-8 である**"):
            self.assertIn(s, b, s)
        self.assertEqual(b.count(u"席を上書きしない"), 1)
        ids, lines = predictions(b, "H")
        self.assertEqual(ids, [str(i) for i in range(1, 9)])
        for line in lines:
            cells = [c.strip() for c in line.strip("|").split("|")]
            self.assertEqual(len(cells), 3, line)
            self.assertTrue(cells[2], u"外れ方が空: " + line)
        self.assertIn(u"**100 / 100 / 100**", b)
        self.assertIn(u"gen_c **44〜50 / 77**(P20 で 46)、cd8 **30〜35 / 41**(P20 で 32)", b)
        self.assertIn(u"gen_c **0 / 64**、cd8 **0 / 64**", b)
        self.assertIn(u"gen_c **0〜3 / 39**、cd8 **0〜2 / 13**", b)

    def test_6_stage_2_seats_cap_dryrun_and_seven_predictions(self):
        b = sec(self.t, "## §2", "## §3")
        for s in (u"**人間の承認(2026-10-20)「全て君に任せるし承認する」**", u"`model=sonnet`", u"**8 便**",
                  u"**上限 1,600,000 トークン(合計)・1 便 250,000**", u"**下見(0 USD)を先に**",
                  u"下見が赤なら段 2 はやらない", u"**T6_PRIOR**", u"**T7_ROUND**", u"**T2_UNIT**",
                  u"engine 0 行", u"**段 2 で本当に測っているのは P-1・P-3 である**"):
            self.assertIn(s, b, s)
        ids, lines = predictions(b, "P")
        self.assertEqual(ids, [str(i) for i in range(1, 8)])
        for line in lines:
            cells = [c.strip() for c in line.strip("|").split("|")]
            self.assertEqual(len(cells), 3, line)
            self.assertTrue(cells[2], u"外れ方が空: " + line)
        self.assertIn(u"**6〜20 / 64**", b)
        self.assertIn(u"G2 の精度 ≥ G1 の精度 + **5 pt**、G3 の精度 ≤ G1 の精度 − **10 pt**", b)
        self.assertIn(u"**0〜6 / 64**", b)

    def test_7_limits_and_closed_file_list(self):
        self.assertIn(u"精度の物差しは「注入か」だけ。", sec(self.t, "## §3", "## §4"))
        b = sec(self.t, "## §4")
        for rel in AFTER_S1 + AFTER_S2 + ("measure/inject.py",):
            self.assertIn("`%s`" % rel, b, rel)
        self.assertIn(u"**これ以外に触らない。engine 0 行。席の答えは 1 文字も直さない。**", b)
        self.assertIn(u"**数を見てから封・予測を直さない。外れは外れとして残す。**", b)


class OrderTest(unittest.TestCase):
    @staticmethod
    def _added(rel):
        out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "--", rel],
                             cwd=ROOT, capture_output=True, text=True)
        shas = [s for s in out.stdout.split() if s]
        return shas[-1] if shas else None

    def test_8_the_seal_precedes_every_later_file(self):
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", SEAL_REL],
                                 cwd=ROOT, capture_output=True).returncode == 0
        if not tracked:
            self.skipTest(u"封がまだ commit されていない")
        seal = self._added(SEAL_REL)
        for rel in AFTER_S1 + AFTER_S2:
            other = self._added(rel)
            if other is None:
                continue
            self.assertNotEqual(seal, other, rel)
            self.assertTrue(subprocess.run(["git", "merge-base", "--is-ancestor", seal, other],
                                           cwd=ROOT, capture_output=True).returncode == 0, rel)
        # inject.py は変更。封より後の commit でしか変わっていないこと(封の commit 以前の最終変更は封の親より前)
        out = subprocess.run(["git", "log", "--format=%H", "--", "measure/inject.py"],
                             cwd=ROOT, capture_output=True, text=True)
        for c in [s for s in out.stdout.split() if s]:
            anc = subprocess.run(["git", "merge-base", "--is-ancestor", c, seal],
                                 cwd=ROOT, capture_output=True).returncode == 0
            if anc:
                break
            self.assertTrue(subprocess.run(["git", "merge-base", "--is-ancestor", seal, c],
                                           cwd=ROOT, capture_output=True).returncode == 0,
                            u"封より前に inject.py が変わっている: " + c)


if __name__ == "__main__":
    unittest.main()
