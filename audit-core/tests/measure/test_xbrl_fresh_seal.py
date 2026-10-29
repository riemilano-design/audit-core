# -*- coding: utf-8 -*-
u"""新しい標本 30 書類で P22・P24・P25 を並べ、既定を決める封の門(docs/XBRL_FRESH_SAMPLE_SEAL_2026-10-21.md)。

人間の 2 つの引用・§3 の基準 K-1〜K-3 の字と「数を見てから変えない」・§4 の事前予測 F-1〜F-5 の行と幅の算術・§0 の数が記録と一致すること・
**§1 の引きを門の中で 1 から再計算して draw の記録 `fixtures/xbrl/fresh/draw_2026-10-21.json` の 40 件と一致すること**・
引いた 40 件が手元の cache に無いこと(取得の記録 `fixtures/xbrl/fresh/fetched_2026-10-21.json` が出来た後は在ってよい)・
§6 の file 一覧と順序・後の file(取得・測定・結果)が封より先に無いことを縛る。

**引きの再計算は、記録の draw の `飛ばした件` を信じない。** 母集団の名簿と seed から order を作り直し、order の再現を封じた 3 群
(`docs/HOLDOUT_SPLIT_SEAL_2026-10-14.md`)と cd8・gen_c の draw の位置で先に確かめ、order[67:] を順に見て「名簿以外の追跡 file に名前が出た」
「cache に在る」で飛ばし、先頭 40 件を取り直す。cache は repo の外なので、cache が無い機(別の clone)では記録の「cache に在って飛ばした件」を使う。
名簿の file の一覧(封 §1-2)は ROSTER_PATTERNS で、後の file(この封・結果文書・取得・測定の script・記録・門)は名簿に入る(名前が出ても飛ばさない)。

**67 書類は order[:67] だけから来たのではない。** 記録 `lastbranch_2026-10-21.json` の「書類 67 の sha256」の docID を order と突き合わせると、
order[:67] の中に在るのは 50、母集団の外が 16、order[67:] に在るのが 1(位置 160。cache に在るので規則で飛ばされる)。
封 §1 の「order[67:]」は「位置で 67 以降」であって「67 書類以降」ではない。この数は draw の記録に残してあり、門が実物から数え直す。"""
import fnmatch
import glob
import io
import json
import os
import random
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

SEAL_REL = "docs/XBRL_FRESH_SAMPLE_SEAL_2026-10-21.md"
SEAL = os.path.join(ROOT, SEAL_REL)
DRAW_REL = "fixtures/xbrl/fresh/draw_2026-10-21.json"
DRAW = os.path.join(ROOT, DRAW_REL)
GATE_REL = "tests/measure/test_xbrl_fresh_seal.py"
POOL = os.path.join(ROOT, "fixtures", "xbrl", "holdout_p17", "pool2_clean_2026-10-14.json")
CD8_DRAW = os.path.join(ROOT, "fixtures", "xbrl", "cd8", "draw_2026-10-17.json")
GENC_DRAW = os.path.join(ROOT, "fixtures", "xbrl", "gen_c", "draw_2026-10-20.json")
SPLIT_SEAL = os.path.join(ROOT, "docs", "HOLDOUT_SPLIT_SEAL_2026-10-14.md")
LASTBRANCH = os.path.join(ROOT, "fixtures", "xbrl", "lastbranch_2026-10-21.json")
ROUNDING = os.path.join(ROOT, "fixtures", "xbrl", "rounding_2026-10-21.json")
VOCAB = os.path.join(ROOT, "fixtures", "xbrl", "vocab_2026-10-21.json")
CACHE = os.path.expanduser("~/.cache/audit-core/edinet")
FETCHED_REL = "fixtures/xbrl/fresh/fetched_2026-10-21.json"

SEED_HEX = "6a24d72"
START = 67
WANT = 40

# 封 §1-2 の名簿(名前が出ても飛ばさない)。cd8 の封 §1-2 の 4 file + この便で作る file(封 §1-2「この便で作る file」)
ROSTER_PATTERNS = ("fixtures/xbrl/holdout_p17/pool2_clean_2026-10-14.json",
                   "fixtures/xbrl/holdout_p17/fetched_not_read_2026-10-14.json",
                   "fixtures/xbrl/holdout_p17/pool_meta_2026-10-14.json",
                   "fixtures/xbrl/holdout_p17/pool2_meta_2026-10-14.json",
                   "docs/XBRL_FRESH_SAMPLE_*",
                   "fixtures/xbrl/fresh/*",
                   "measure/xbrl_fresh_*",
                   "tests/measure/test_xbrl_fresh_*")

# 封 §6 の順(この封 + draw + 封の門 の後)
FILES_AFTER = ("measure/xbrl_fresh_fetch_2026-10-21.py",
               "fixtures/xbrl/fresh/fetched_2026-10-21.json",
               "measure/xbrl_fresh_2026-10-21.py",
               "fixtures/xbrl/fresh/fresh_2026-10-21.json",
               "docs/XBRL_FRESH_SAMPLE_RESULT_2026-10-21.md",
               "tests/measure/test_xbrl_fresh_result.py")
FILES_WITH_SEAL = (DRAW_REL, GATE_REL)


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


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)


def rows(block, tag):
    return re.findall(r"(?m)^\| \*\*%s-\d+\*\* \|.*$" % tag, block)


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


# ---------------------------------------------------------------- 引きの再計算(封 §1)
def make_order():
    ids = sorted(jload(POOL)["pool_clean"])
    order = list(ids)
    random.Random(int(SEED_HEX, 16)).shuffle(order)
    return order


def is_roster(path):
    return any(fnmatch.fnmatch(path, pat) for pat in ROSTER_PATTERNS)


#: 2026-10-21 追記(pin の遷移。顧客向けの報告形の直し、封 docs/XBRL_CUSTOMER_REPORT_FIX_SEAL_2026-10-21.md): draw の commit の**後**に追跡された file で、docID を名指すもの。
#: draw の再計算(test_23)は『draw の commit 時点で名前が出ていた file』と記録を比べるので、後の file は数えない。ここに足してよいのは、
#: **draw の commit より後に足された file**だけ(追跡されているときは git の履歴で確かめる。draw は動かさない)。
# 2026-10-22 追記(P26 の段 1): 結果の記録 fixtures/xbrl/p26_2026-10-21.json も docID を名指す(書類 67 本の sha256 の一覧)。前例と同じ扱いで、追跡された後も引きを動かさない。
# 2026-10-23 追記(既定を P22 -> P26 に切り替える 段 2): 結果の記録 fixtures/xbrl/default_p26_2026-10-23.json は書類 97 本の sha256 の一覧で docID を名指す。測定の script と
# 結果の門は軽い走らせ直しの書類 1 本(S100YXFQ)の docID を字で持つ。どれも draw の commit(14cdd21)より後に足した file で、前例と同じ扱い(引きは動かさない)。
# 2026-10-27 追記(P27 の段 2): 新しい記録 3 つ(97 書類の後退の測定 regress97、調整用 10 社の再現の判定 tune_p27 と注入 tune_p27_inject)は書類の docID を名指す。前例と同じ扱い(引きは動かさない)。
# 2026-10-28 追記(既定を P26 -> P27 に切り替える 段 2): 新しい記録 default_p27_2026-10-28.json(97 書類の docID を持つ)と結果の門・測定の script(軽い走らせ直しの書類の docID を字で持つ。script は docstring の使い方の行)。前例(917157c の 3 file)と同じ扱い(引きは動かさない)。
# 2026-10-28 追記(注入 T2 で通した 5 行の診断): 新しい記録 t2_pass_diag_2026-10-28.json(通した 5 行が載る 3 書類の docID を持つ)と、測定の script・門(docstring の使い方の行に docID を字で持つ)。封 docs/XBRL_T2_PASS_DIAG_SEAL_2026-10-28.md の §5。前例(917157c の 3 file、default_p27 の 3 file)と同じ扱い(引きは動かさない)。封と診断の文書は docID を書かない(門 (h) が見る)。
# 2026-10-28 追記(注入 741 行の全部で「差し替えが基準の claim に届いたか」を数える診断): 新しい記録 inject_reach_2026-10-28.json(30 書類の docID を持つ)と、測定の script・門(script は docstring の使い方の行に docID を字で持つ。門は docID を持たないが、前の便と同じ 3 つ組で宣言する)。封 docs/XBRL_INJECT_REACH_DIAG_SEAL_2026-10-28.md の §5。前例(fbdcaaa の 3 file)と同じ扱い(引きは動かさない)。封と診断の文書は docID を書かない(門 (h) が見る)。
# 2026-10-29 追記(評価用・調整用 P27 の注入で「差し替えが基準の claim に届いたか」を数える診断): 新しい記録 p27/inject_reach_2026-10-29.json(評価用 10 書類・調整用 10 書類の docID を持つ)と、測定の script・門(script と門は docID を字で持たないが、前の便と同じ 3 つ組で宣言する)。封 docs/XBRL_P27_INJECT_REACH_SEAL_2026-10-29.md の §5。前例(inject_reach_2026-10-28 の 3 file)と同じ扱い(引きは動かさない)。封と診断の文書は docID を書かない(門 (h) が見る)。
# 2026-10-29 追記(注入 741 行で「止めた理由」と「名指し」を分類し、P27E を同じ 741 行で測る診断): 新しい記録 stop_reason_2026-10-29.json(30 書類の docID を持つ)と、測定の script・門(script は docstring に docID を持たない。門も持たないが、前の便と同じ 3 つ組で宣言する)。封 docs/XBRL_STOP_REASON_DIAG_SEAL_2026-10-29.md の §5。前例(a7ceb29 の 3 file)と同じ扱い(引きは動かさない)。封と診断の文書は docID を書かない(門 (h) が見る)。
LATER_NAMING_FILES = ("fixtures/xbrl/customer_report_fix_2026-10-21.json", "fixtures/xbrl/p26_2026-10-21.json",
                      "fixtures/xbrl/default_p26_2026-10-23.json", "measure/xbrl_default_p26_2026-10-23.py", "tests/measure/test_xbrl_default_p26_result.py",
                      "docs/XBRL_P27_SAMPLE_SEAL_2026-10-27.md",
                      "fixtures/xbrl/p27/dbfetch_2026-10-27.json", "fixtures/xbrl/p27/reports_2026-10-27.json",
                      "fixtures/xbrl/p27/tune_2026-10-27.json", "fixtures/xbrl/p27/tune_readings_2026-10-27.json",
                      "fixtures/xbrl/p27/tune_inject_2026-10-27.json", "docs/XBRL_P27_TUNE_DIAG_2026-10-27.md",
                      "measure/xbrl_p27_tune_2026-10-27.py", "tests/measure/test_xbrl_p27_tune_result.py",
                      "fixtures/xbrl/p27/regress97_2026-10-27.json", "fixtures/xbrl/p27/tune_p27_2026-10-27.json",
                      "fixtures/xbrl/p27/tune_p27_inject_2026-10-27.json",
                      "fixtures/xbrl/p27/eval_2026-10-27.json", "fixtures/xbrl/p27/eval_inject_2026-10-27.json",
                      "fixtures/xbrl/p27/eval_readings_2026-10-27.json", "docs/XBRL_P27_RESULT_2026-10-27.md",
                      "tests/measure/test_xbrl_p27_result.py",
                      "fixtures/xbrl/default_p27_2026-10-28.json", "tests/measure/test_xbrl_default_p27_result.py",
                      "measure/xbrl_default_p27_2026-10-28.py",
                      "fixtures/xbrl/t2_pass_diag_2026-10-28.json", "measure/xbrl_t2_pass_diag_2026-10-28.py",
                      "tests/measure/test_xbrl_t2_pass_diag.py",
                      "fixtures/xbrl/inject_reach_2026-10-28.json", "measure/xbrl_inject_reach_2026-10-28.py",
                      "tests/measure/test_xbrl_inject_reach.py",
                      "fixtures/xbrl/p27/inject_reach_2026-10-29.json", "measure/xbrl_p27_inject_reach_2026-10-29.py",
                      "tests/measure/test_xbrl_p27_inject_reach.py",
                      "fixtures/xbrl/stop_reason_2026-10-29.json", "measure/xbrl_stop_reason_2026-10-29.py",
                      "tests/measure/test_xbrl_stop_reason.py")


def drop_later_naming_files(named):
    """``names_in_tracked_files`` の結果から、宣言された後の file を除く(空になった docID は消す)。"""
    out = {}
    for doc, files in named.items():
        keep = [f for f in files if f not in LATER_NAMING_FILES]
        if keep:
            out[doc] = keep
    return out


def names_in_tracked_files(docs):
    """{docID: [名前が出た追跡 file(名簿を除く)]}。repo 全体(git grep。作業木の追跡 file)。名簿の除外は Python 側で(pathspec の癖に頼らない)。"""
    args = ["grep", "-o", "-F"]
    for d in docs:
        args += ["-e", d]
    out = git(*args).stdout
    found = {}
    for line in out.splitlines():
        path, _, hit = line.rpartition(":")
        if hit in docs and path and not is_roster(path):
            found.setdefault(hit, set()).add(path)
    return dict((k, sorted(v)) for k, v in found.items())


def cache_set():
    if not os.path.isdir(CACHE):
        return None
    return set(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(CACHE, "*.zip")))


def redraw(order, cached, named):
    """封 §1-2 の規則: order[67:] を順に見て、名前が出ている・cache に在る docID を飛ばし、先頭 40 件。"""
    taken, pos, skipped = [], [], []
    for i in range(START, len(order)):
        d = order[i]
        why = []
        if d in named:
            why.append("named")
        if d in cached:
            why.append("cache")
        if why:
            skipped.append((i, d, tuple(why)))
            continue
        taken.append(d)
        pos.append(i)
        if len(taken) == WANT:
            break
    return taken, pos, skipped


def effective_cache(draw):
    """cache が在る機: 現在の cache から「引いた 40 件」を除いたもの(取得の後は 40 件が在ってよい)。無い機: 記録の cache に在って飛ばした件。"""
    cur = cache_set()
    drawn = set(draw[u"引いた 40 件"])
    if cur is None or not cur:
        return set(s[u"docID"] for s in draw[u"飛ばした件"] if s[u"cache に在る"])
    return cur - drawn


class HumanQuotesAndHeadTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = text(SEAL)

    def test_1_head_quotes_the_human_and_names_the_delegation(self):
        head = self.t[:self.t.index("\n## §0 ")]
        self.assertTrue(head.startswith(u"# 封: 新しい標本 30 書類で P22・P24・P25 を並べ、既定を決める ― 2026-10-21"))
        self.assertIn(u"**人間(2026-10-21 朝)「新しい標本取り、テストしてP25にするか判断したらどう?」「取って良い あとは全て任せる」。**", head)
        self.assertIn(u"既定の切り替え(段 2)の判断を、**この封に書いた基準**で司令塔が下す(人間の委任)。", head)
        self.assertIn(u"基準は標本を取る前に固定し、数を見てから変えない。外れは外れとして残す。", head)
        self.assertIn(u"費用 0 USD(EDINET は無料。鍵 `EDINET_API_KEY` は人間が渡し、値は読まない・印字しない・記録しない)。", head)

    def test_2_section_headings_are_the_six_in_order(self):
        heads = re.findall(r"(?m)^## (§\d) ", self.t)
        self.assertEqual(heads, [u"§0", u"§1", u"§2", u"§3", u"§4", u"§5", u"§6"])


class CriteriaTest(unittest.TestCase):
    """§3 の基準。数を見てから変えないので、字を 1 つずつ縛る(幅・しきい値を直すと赤くなる)。"""

    @classmethod
    def setUpClass(cls):
        cls.t = text(SEAL)
        cls.b = sec(cls.t, "## §3", "## §4")

    def test_3_k1_k2_k3_rows_are_exactly_as_sealed(self):
        ks = rows(self.b, "K")
        self.assertEqual(len(ks), 3)
        self.assertEqual([re.match(r"\| \*\*(K-\d)\*\*", l).group(1) for l in ks], ["K-1", "K-2", "K-3"])
        for l in ks:
            self.assertEqual(len(cells(l)), 3, l)
        self.assertEqual(ks[0], u"| **K-1** | 注入で P25 が誤りを通す数 ≤ P22 が通す数 | (D) |")
        self.assertEqual(ks[1], u"| **K-2** | P22 → P25 の新 GROUNDED の**偽**が新 GROUNDED の **3% 以下**(新 GROUNDED が 0 なら満たす) | (B) |")
        self.assertEqual(ks[2], u"| **K-3** | 「違う」が弱まった行のうち**文が本当に違う**が **2% 以下**(「分からない」は半分を違うに数える) | (C) |")

    def test_4_the_title_says_the_numbers_may_not_change_the_criteria(self):
        self.assertIn(u"## §3 既定を決める基準(**この封の中心。数を見てから変えない**)", self.t)

    def test_5_decision_rule_has_three_branches_and_is_mechanical(self):
        for s in (u"- **K-1・K-2・K-3 を全部満たす → 既定を P25 にする**(段 2: `DEFAULT_PROFILE = \"P25\"`・既定の字の試験・儀式の走らせ直し・README・pin。"
                  u"封 → 実装 → 凍結 → 独立監査 GO → commit の作法のまま)。",
                  u"- P25 で満たさず、P24 で K-1〜K-3(P22 → P24 で同じ定義)を全部満たす → 既定を P24 にする。",
                  u"- どちらも満たさない → 既定は P22 のまま。満たさなかった基準と行を人間に報告する。",
                  u"- 判定は記録の数から機械で(門で縛る)。司令塔は判定を覆さない。"):
            self.assertIn(s, self.b, s)
        # 順序: P25 → P24 → P22 のまま。上から順に判定する書き方
        i25 = self.b.index(u"既定を P25 にする")
        i24 = self.b.index(u"既定を P24 にする")
        i22 = self.b.index(u"既定は P22 のまま")
        self.assertTrue(i25 < i24 < i22)

    def test_6_measure_items_a_to_d_and_the_reader_caveat(self):
        b = sec(self.t, "## §2", "## §3")
        for s in (u"(A) 無改変: 30 書類の全 claim を P22・P23・P24・P25(と §3 の P26)で。4 state の数と率。",
                  u"(B) 新 GROUNDED(P22 → P25 で非 GROUNDED → GROUNDED)を**全部読む**: 正 / 偽(間違った fact に結んだ)/ 準偽。",
                  u"(C) 「違う」が弱まった行(P22 で VALUE_MISMATCH、P25 で POINTER_NOT_FOUND か UNVERIFIABLE)を**全部読む**: "
                  u"正しい文(VM が偽だった)/ 文が本当に違う / 分からない。",
                  u"(D) 注入: 30 書類の素の書類で P22 が GROUNDED の claim に、`measure/inject.py` の 4 型(種は `measure/SEED.json`)で 1 回に 1 件。",
                  u"各 profile で GROUNDED にした数(= 誤りを通した数)と、止めのうち「違う」/「要確認」の数。",
                  u"読みは席(エージェント)の読みで人間の読みではないことを記録と文書に書く。"):
            self.assertIn(s, b, s)
        self.assertIn(u"## §2 測るもの(`measure/xbrl_fresh_2026-10-21.py` → `fixtures/xbrl/fresh/fresh_2026-10-21.json`)", self.t)

    def test_7_limits_are_written(self):
        b = sec(self.t, "## §5", "## §6")
        for s in (u"30 書類は 1 つの母集団(封 431f436 の 256 件)からの引き。母集団の偏り(提出時期・業種)は引き継ぐ。",
                  u"読みはエージェントで人間ではない。K-2・K-3 の判定はその読みに依る。",
                  u"注入は 4 型だけ。実際の LLM の誤りの分布ではない。"):
            self.assertIn(s, b, s)


class PredictionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = text(SEAL)
        cls.b = sec(cls.t, "## §4", "## §5")

    def test_8_five_predictions_each_with_a_way_to_fail(self):
        fs = rows(self.b, "F")
        self.assertEqual([re.match(r"\| \*\*(F-\d)\*\*", l).group(1) for l in fs], ["F-1", "F-2", "F-3", "F-4", "F-5"])
        for l in fs:
            c = cells(l)
            self.assertEqual(len(c), 3, l)
            self.assertTrue(c[1] and c[2], l)
        self.assertEqual(fs[0], u"| **F-1** | 30 書類の無改変で P22 の「違う」率 **12〜25%**、P25 の「違う」率 **5〜13%** | 幅の外 |")
        self.assertEqual(fs[1], u"| **F-2** | P25 の結べない(PNF)率 **13〜24%** | 幅の外 |")
        self.assertEqual(fs[2], u"| **F-3** | K-1・K-2・K-3 を全部満たす(= P25 になる) | どれか 1 つでも満たさない |")
        self.assertEqual(fs[3], u"| **F-4** | P23 → P25 の新 GROUNDED は claim あたり 67 書類(148 / 7,799 = 1.9%)の **0.3〜1.5 倍** | 幅の外 |")
        self.assertEqual(fs[4], u"| **F-5** | (D) の注入で P25 が誤りを通す率 **0〜4%** | 4% 超 |")

    def test_9_judgement_is_separate_from_the_predictions(self):
        self.assertIn(u"## §4 事前予測(当たり外れは既定の判定と別。外れても判定は §3 のとおり)", self.t)
        self.assertIn(u"司令塔の偏り: 67 書類での数は規則を作った材料なので、F-1 の P25 の幅は 67 の 8.0% より上に寄せた。", self.b)
        self.assertIn(u"F-3 は当たると見ているが、外れる見込みも小さくない(新しい言い回しで P24 の語彙の偽が出うる)。", self.b)

    def test_10_prediction_arithmetic_against_the_67_document_numbers(self):
        """幅が §0 の 67 書類の数と整合する: P25 の幅は 8.0% より上に寄せてある(幅の中心 > 8.0)。P22 の幅は 18.1% を含む。F-4 の幅の算術。"""
        n = s0_numbers(sec(self.t, "## §0 ", "## §1"))
        fs = rows(self.b, "F")
        lo, hi = [int(x) for x in re.search(r"P22 の「違う」率 \*\*(\d+)〜(\d+)%\*\*", fs[0]).groups()]
        self.assertTrue(lo <= n["p22_vm_pct"] <= hi, (lo, n["p22_vm_pct"], hi))
        lo25, hi25 = [int(x) for x in re.search(r"P25 の「違う」率 \*\*(\d+)〜(\d+)%\*\*", fs[0]).groups()]
        self.assertTrue(lo25 <= n["p25_vm_pct"] <= hi25)
        self.assertGreater((lo25 + hi25) / 2.0, n["p25_vm_pct"], u"幅の中心が 67 の 8.0% より上に寄っている(司令塔の偏りの字)")
        self.assertTrue(lo25 < lo and hi25 < hi)                   # P25 の幅は P22 の幅より下(順序が逆転しない。幅は重なってよい)
        lo2, hi2 = [int(x) for x in re.search(r"結べない\(PNF\)率 \*\*(\d+)〜(\d+)%\*\*", fs[1]).groups()]
        self.assertTrue(lo2 <= n["p25_pnf_pct"] <= hi2)
        m = re.search(r"67 書類\(([\d,]+) / ([\d,]+) = ([\d.]+)%\)の \*\*([\d.]+)〜([\d.]+) 倍\*\*", fs[3])
        self.assertEqual((num(m.group(1)), num(m.group(2))), (n["new_g"], n["claims"]))
        self.assertEqual(round(100.0 * n["new_g"] / n["claims"], 1), float(m.group(3)))
        self.assertEqual((float(m.group(4)), float(m.group(5))), (0.3, 1.5))
        # F-5 の上限 4% は K-1(P25 ≤ P22)と別の予測であり、誤りを通す率の上限
        self.assertEqual(re.search(r"通す率 \*\*(\d+)〜(\d+)%\*\*", fs[4]).groups(), ("0", "4"))


def s0_numbers(b):
    m = re.search(r"67 書類での数\(claim ([\d,]+)\): P22 違う ([\d,]+)\(([\d.]+)%\)・GROUNDED ([\d,]+)。"
                  r"P25 違う ([\d,]+)\(([\d.]+)%\)・GROUNDED ([\d,]+)・PNF ([\d,]+)\(([\d.]+)%\)。"
                  r"誤りの通過: 穴 B P22 (\d+) / (\d+) → P25 (\d+)、儀式 P22 (\d+) / (\d+) → P25 (\d+) / (\d+)。", b)
    assert m, u"§0 の書き方が変わった"
    g = [num(x) if re.match(r"^[\d,]+$", x) else float(x) for x in m.groups()]
    keys = ("claims", "p22_vm", "p22_vm_pct", "p22_g", "p25_vm", "p25_vm_pct", "p25_g", "p25_pnf", "p25_pnf_pct",
            "hb22", "hb_den", "hb25", "rt22", "rt22_den", "rt25", "rt25_den")
    n = dict(zip(keys, g))
    n["new_g"] = 148                                              # 封 §4 F-4 の字(「148 / 7,799」)。test_10 が F-4 の字と、test_11 が vocab の記録と突き合わせる
    n["outside_214"] = bool(re.search(r"手元の cache の 67 の外 214 書類は全部 jpsps", b))
    return n


class Section0Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = text(SEAL)
        cls.b = sec(cls.t, "## §0 ", "## §1")

    def test_11_section_0_numbers_equal_the_records(self):
        n = s0_numbers(self.b)
        lb, rd, vc = jload(LASTBRANCH), jload(ROUNDING), jload(VOCAB)
        # 全部が 7,799 claim の上で、率は書かれた字(小数 1 桁)と一致する
        self.assertEqual(n["claims"], 7799)
        for k, pct in (("p22_vm", "p22_vm_pct"), ("p25_vm", "p25_vm_pct"), ("p25_pnf", "p25_pnf_pct")):
            self.assertEqual(round(100.0 * n[k] / n["claims"], 1), n[pct], k)
        # P22: rounding の R2(P22 の合計)
        r2 = rd["R2"]["集計"]
        self.assertEqual((n["p22_vm"], n["p22_g"]), (r2["VALUE_MISMATCH の合計 P22"], r2["GROUNDED の合計 P22"]))
        # P25: lastbranch の L1
        l1 = lb["L1"]["集計"]
        self.assertEqual(l1["総 claim"], n["claims"])
        self.assertEqual((n["p25_vm"], n["p25_g"], n["p25_pnf"]),
                         (l1["VALUE_MISMATCH の合計 P25"], l1["GROUNDED の合計 P25"], l1["POINTER_NOT_FOUND の合計 P25"]))
        # 穴 B: P22 の通した(rounding R3 の対照)と P25(lastbranch L4)
        hb22 = rd["R3"]["集計"]["P22(対照)で通した"]
        hb25 = lb["L4"]["集計"]["P25 で通した(GROUNDED のまま)"]
        self.assertEqual((n["hb22"], n["hb_den"]), (hb22["件"], hb22["分母"]))
        self.assertEqual((n["hb25"], n["hb_den"]), (hb25["件"], hb25["分母"]))
        # 儀式: P22 の通した(rounding R1 の対照)と P25(lastbranch L5)
        rt22 = rd["R1"]["通した P22(対照)"]
        rt25 = lb["L5"]["通した P25"]
        self.assertEqual((n["rt22"], n["rt22_den"]), (rt22["件"], rt22["分母"]))
        self.assertEqual((n["rt25"], n["rt25_den"]), (rt25["件"], rt25["分母"]))
        # F-4 の 148(新 GROUNDED)は P23 → P24 の記録
        self.assertEqual(vc["W1W2W3"]["集計"]["GROUNDED でない → GROUNDED(新 GROUNDED)"], n["new_g"])
        self.assertEqual(vc["W1W2W3"]["集計"]["総 claim"], n["claims"])

    def test_12_cache_outside_the_67_is_214_jpsps_and_the_67_is_recorded(self):
        self.assertTrue(s0_numbers(self.b)["outside_214"])
        lb = jload(LASTBRANCH)
        self.assertEqual(lb[u"書類の数"], {u"経営分析の文を持つ": 67, u"67 の外": 214})
        self.assertIn(u"規則を作った材料での増分は新しい標本で 0 になりうる(過去に 14 pt → 0.0 pt)。", self.b)
        self.assertIn(u"P23・P24・P25 の規則は無改変の 67 書類を読んで作り、同じ 67 書類で測った", self.b)


class SampleRuleTest(unittest.TestCase):
    """§1 の字(引く規則・40 件・30 件・取得の条件)。"""

    @classmethod
    def setUpClass(cls):
        cls.t = text(SEAL)
        cls.b = sec(cls.t, "## §1", "## §2")

    def test_13_rule_text_is_as_sealed(self):
        for s in (u"1. 母集団は封 `431f436`(`docs/HOLDOUT_SPLIT_SEAL_2026-10-14.md`)の 256 件、並びは `sorted(pool_clean)` を "
                  u"`random.Random(int(\"6a24d72\", 16)).shuffle` した `order`(封 `docs/XBRL_CD_SEAL_2026-10-17.md` §1 と同じ)。",
                  u"2. `order[67:]` を順に見て、**docID が名簿の file 以外のどこか(repo の追跡された file)で名前が出ていたら飛ばす**、"
                  u"**手元の cache に在ったら飛ばす**(飛ばした理由を記録)。名簿の file は封 `docs/XBRL_CD_SEAL_2026-10-17.md` §1-2 の 4 file と、この便で作る file。",
                  u"3. 残った先頭 **40 件**を引く(`fixtures/xbrl/fresh/draw_2026-10-21.json`。この封と同じ commit)。取得して、`verify_document` の既定の抽出で"
                  u" claim が 1 以上の書類を引いた順に **30 件**使う。30 に届かなければ届いた数で測り、その数を記録(足りない分を引き直さない)。",
                  u"4. 取得は `measure/xbrl_fresh_fetch_2026-10-21.py`(取得前に cache に無いこと・応答が ZIP であること・記録に鍵らしい字が無いことを確かめる。"
                  u"前例 `measure/xbrl_gen_c_fetch_2026-10-20.py`)。"):
            self.assertIn(s, self.b, s)
        self.assertIn(u"## §1 標本(機械で 1 通りに決まる。私は選ばない)", self.t)

    def test_14_the_roster_in_the_seal_is_the_cd8_four_files(self):
        cd8 = text(os.path.join(ROOT, "docs", "XBRL_CD_SEAL_2026-10-17.md"))
        s = sec(cd8, "### §1-2", "---")
        for rel in ROSTER_PATTERNS[:4]:
            base = os.path.basename(rel)
            self.assertIn(base, s, base)
        for rel in ROSTER_PATTERNS[:4]:
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)
        # この便で作る file は、封の字(§6)に出る file の名簿パターンに全部当たる
        for rel in (SEAL_REL,) + FILES_WITH_SEAL + FILES_AFTER:
            self.assertTrue(is_roster(rel), rel)

    def test_15_roster_filter_leaves_other_tracked_files(self):
        self.assertTrue(is_roster("fixtures/xbrl/fresh/draw_2026-10-21.json"))
        self.assertTrue(is_roster("docs/XBRL_FRESH_SAMPLE_RESULT_2026-10-21.md"))
        self.assertTrue(is_roster("fixtures/xbrl/holdout_p17/pool_meta_2026-10-14.json"))
        self.assertFalse(is_roster("fixtures/xbrl/candidates_2026-09.json"))
        self.assertFalse(is_roster("docs/HOLDOUT_P17_SEAL_2026-10-14.md"))
        self.assertFalse(is_roster("fixtures/xbrl/cd8/draw_2026-10-17.json"))
        self.assertFalse(is_roster("docs/XBRL_FRESH_OTHER.md"))
        self.assertFalse(is_roster("fixtures/xbrl/fresh_other/x.json"))


class OrderReproductionTest(unittest.TestCase):
    """order の再現: 封じた 3 群・cd8 の draw・gen_c の draw の位置が、作り直した order と一致する(引きの前提)。"""

    @classmethod
    def setUpClass(cls):
        cls.order = make_order()

    def test_16_pool_is_256_and_seed_is_the_sealed_one(self):
        self.assertEqual(len(self.order), 256)
        self.assertEqual(len(set(self.order)), 256)
        self.assertEqual(self.order[:6], ["S100YYQX", "S100Z3LJ", "S100Z3IZ", "S100Z3H2", "S100YXLE", "S100Z3L6"])

    def test_17_the_three_sealed_groups_are_reproduced(self):
        t = text(SPLIT_SEAL)
        want = {}
        for name, lo, hi in (u"使用済み", 0, 6), (u"直し用(開発)", 6, 14), (u"最終評価用", 14, 22):
            m = re.search(r"(?m)^\| \*\*%s\*\* \| `order\[%d:%d\]` \| \d+ \| (.*?) \|" % (re.escape(name), lo, hi), t)
            self.assertTrue(m, name)
            ids = re.findall(r"`(S100[0-9A-Z]{4})`", m.group(1))
            self.assertEqual(len(ids), hi - lo, name)
            want[(lo, hi)] = ids
        for (lo, hi), ids in sorted(want.items()):
            self.assertEqual(self.order[lo:hi], ids, "order[%d:%d]" % (lo, hi))

    def test_18_cd8_draw_positions_and_skipped_are_reproduced(self):
        d = jload(CD8_DRAW)
        self.assertEqual(len(d[u"位置"]), 8)
        for p, doc in zip(d[u"位置"], d[u"引いた 8 件"]):
            self.assertEqual(self.order[p], doc, p)
        self.assertGreater(len(d[u"飛ばした件"]), 20)
        for s in d[u"飛ばした件"]:
            self.assertEqual(self.order[s[u"位置"]], s["docID"], s)

    def test_19_gen_c_draw_positions_are_reproduced(self):
        d = jload(GENC_DRAW)
        self.assertEqual(d[u"位置"], list(range(59, 67)))
        self.assertEqual(self.order[59:67], d[u"引いた 8 件"])
        self.assertEqual(d[u"開始の位置"], 59)


class DrawRecordTest(unittest.TestCase):
    """draw の記録そのものの整合(記録の中の矛盾)と、封 §1 の字との一致。"""

    @classmethod
    def setUpClass(cls):
        cls.d = jload(DRAW)
        cls.order = make_order()

    def test_20_record_header_matches_the_seal(self):
        d = self.d
        self.assertEqual(d["seal"], SEAL_REL)
        self.assertEqual((d["seed_hex"], d["pool"], d[u"開始の位置"], d[u"引く件数"]), (SEED_HEX, 256, START, WANT))
        self.assertEqual(len(d[u"引いた 40 件"]), WANT)
        self.assertEqual(len(set(d[u"引いた 40 件"])), WANT)
        self.assertEqual(len(d[u"位置"]), WANT)
        self.assertEqual(d[u"位置"], sorted(d[u"位置"]))
        self.assertGreaterEqual(d[u"位置"][0], START)
        self.assertTrue(d[u"取得"].startswith(u"**していない**"))
        self.assertEqual(d[u"名簿の file(名前が出ていても飛ばさない)"][:4], list(ROSTER_PATTERNS[:4]))

    def test_21_positions_match_order_and_positions_are_exactly_taken_plus_skipped(self):
        d, order = self.d, self.order
        for p, doc in zip(d[u"位置"], d[u"引いた 40 件"]):
            self.assertEqual(order[p], doc, p)
        skipped = d[u"飛ばした件"]
        for s in skipped:
            self.assertEqual(order[s[u"位置"]], s["docID"], s)
            self.assertTrue(s[u"名前が出た file"] or s[u"cache に在る"], s)
            self.assertFalse(any(is_roster(f) for f in s[u"名前が出た file"]), s)
        covered = sorted(d[u"位置"] + [s[u"位置"] for s in skipped])
        self.assertEqual(covered, list(range(START, d[u"位置"][-1] + 1)), u"引いた件と飛ばした件が order[67:] の連続した区間を過不足なく覆う")
        self.assertEqual(d[u"引いた 40 件の位置の幅"], [d[u"位置"][0], d[u"位置"][-1]])
        br = d[u"飛ばした件の内訳"]
        self.assertEqual(br[u"合計"], len(skipped))
        self.assertEqual(br[u"cache に在る"], sum(1 for s in skipped if s[u"cache に在る"]))
        self.assertEqual(br[u"名前が出ている"], sum(1 for s in skipped if not s[u"cache に在る"]))

    def test_22_the_67_documents_against_order(self):
        """67 書類(lastbranch の記録の docID)を order と突き合わせた数が、draw の記録と一致する。"""
        ids67 = sorted(jload(LASTBRANCH)[u"入力の sha256"][u"書類 67(経営分析の文を持つ)の sha256"])
        self.assertEqual(len(ids67), 67)
        pos = dict((d, i) for i, d in enumerate(self.order))
        inside = [d for d in ids67 if d in pos and pos[d] < START]
        outside = [d for d in ids67 if d not in pos]
        late = [(d, pos[d]) for d in ids67 if d in pos and pos[d] >= START]
        rec = self.d[u"67 書類と order[:67]"]
        self.assertEqual(rec[u"67 書類の数"], 67)
        self.assertEqual((len(inside), len(outside), len(late)), (rec[u"order[:67] の中に在る"], rec[u"母集団 256 の外"], rec[u"母集団の中で order[67:] に在る"]))
        self.assertEqual(len(inside) + len(outside) + len(late), 67)
        self.assertEqual(sorted(outside), sorted(rec[u"母集団の外の docID"]))
        self.assertEqual(sorted((x[u"docID"], x[u"位置"]) for x in rec[u"order[67:] に在る(位置)"]), sorted(late))
        self.assertEqual(rec[u"order[:67] の中に在る"], 50)
        # order[67:] に在る 67 書類は、規則で飛ばされる(draw に入らない)
        for d, p in late:
            self.assertNotIn(d, self.d[u"引いた 40 件"])
            self.assertTrue(any(s[u"docID"] == d and s[u"cache に在る"] for s in self.d[u"飛ばした件"]), d)
        # 67 書類のどれも引かれていない
        self.assertFalse(set(ids67) & set(self.d[u"引いた 40 件"]))

    def test_23_the_draw_is_recomputed_from_scratch_and_equals_the_record(self):
        order = self.order
        window = order[START:]
        named = drop_later_naming_files(names_in_tracked_files(set(window)))
        cached = effective_cache(self.d)
        taken, pos, skipped = redraw(order, cached, named)
        self.assertEqual(taken, self.d[u"引いた 40 件"])
        self.assertEqual(pos, self.d[u"位置"])
        self.assertEqual([(s[0], s[1]) for s in skipped], [(s[u"位置"], s["docID"]) for s in self.d[u"飛ばした件"]])
        # 理由も一致(名前が出た = 名簿以外の追跡 file の一覧が記録と同じ、cache に在る = 記録と同じ)
        for (i, doc, why), rec in zip(skipped, self.d[u"飛ばした件"]):
            self.assertEqual("named" in why, bool(rec[u"名前が出た file"]), doc)
            self.assertEqual("cache" in why, rec[u"cache に在る"], doc)
            self.assertEqual(sorted(named.get(doc, [])), sorted(rec[u"名前が出た file"]), doc)

    def test_23b_the_later_naming_files_were_added_after_the_draw_commit(self):
        """宣言された後の file は、draw の commit より後に足されたものだけ(追跡されているとき)。draw の commit より前から在る file を宣言して名前を隠すことはできない。"""
        draw_commit = [c for c in git("log", "--diff-filter=A", "--format=%H", "--", DRAW_REL).stdout.split() if c]
        if not draw_commit:
            self.skipTest(u"draw がまだ commit されていない")
        for rel in LATER_NAMING_FILES:
            added = [c for c in git("log", "--diff-filter=A", "--format=%H", "--", rel).stdout.split() if c]
            if not added:
                continue                                    # まだ追跡されていない(commit の前)
            self.assertEqual(git("merge-base", "--is-ancestor", draw_commit[-1], added[-1]).returncode, 0, rel)
            self.assertNotEqual(draw_commit[-1], added[-1], rel)

    def test_24_drawn_documents_are_not_cached_until_fetched(self):
        cur = cache_set()
        if cur is None:
            return                                                  # cache の無い機(別の clone)。取得前の事実は記録の「在った: []」で
        inside = sorted(cur & set(self.d[u"引いた 40 件"]))
        self.assertEqual(self.d[u"**cache に在るか(引いた 40 件)**"][u"在った"], [])
        if inside:
            fetched = os.path.join(ROOT, FETCHED_REL)
            self.assertTrue(os.path.exists(fetched), u"**引いた書類が cache に在るのに取得の記録が無い(未使用でなくなった): %s**" % inside)

    def test_25_cached_skips_are_in_the_cache_where_a_cache_exists(self):
        cur = cache_set()
        if not cur:
            return
        for s in self.d[u"飛ばした件"]:
            if s[u"cache に在る"]:
                self.assertIn(s["docID"], cur, s)

    def test_26_the_drawn_documents_are_in_the_pool_and_never_used_before(self):
        pool = set(jload(POOL)["pool_clean"])
        for doc in self.d[u"引いた 40 件"]:
            self.assertIn(doc, pool)
        # 使用済みの群(order[0:67])の誰も入らない
        self.assertFalse(set(self.order[:START]) & set(self.d[u"引いた 40 件"]))
        # cd8 と gen_c の引いた件も入らない
        used = set(jload(CD8_DRAW)[u"引いた 8 件"]) | set(jload(GENC_DRAW)[u"引いた 8 件"])
        self.assertFalse(used & set(self.d[u"引いた 40 件"]))


class FileListAndOrderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = text(SEAL)

    def test_27_section_6_lists_files_in_the_sealed_order(self):
        b = sec(self.t, "## §6")
        pos = []
        for rel in FILES_WITH_SEAL + tuple(f for f in FILES_AFTER if "fresh_2026-10-21.json" not in f):
            tok = "`%s`" % rel
            self.assertEqual(b.count(tok), 1, rel)
            pos.append(b.index(tok))
        self.assertEqual(pos, sorted(pos), u"file 一覧の順が変わった")
        self.assertIn(u"この封 + `fixtures/xbrl/fresh/draw_2026-10-21.json` + 封の門 `tests/measure/test_xbrl_fresh_seal.py` を commit → "
                      u"(鍵が入ったら)取得 `measure/xbrl_fresh_fetch_2026-10-21.py` → `fixtures/xbrl/fresh/fetched_2026-10-21.json` → "
                      u"測定 `measure/xbrl_fresh_2026-10-21.py` → 記録 → `docs/XBRL_FRESH_SAMPLE_RESULT_2026-10-21.md` → "
                      u"`tests/measure/test_xbrl_fresh_result.py` → 監査 → commit → §3 の判定 → 段 2 の封(判定が P25 か P24 なら)。", b)
        # 測定の script と記録は §2 の見出しにも在る
        self.assertIn("`measure/xbrl_fresh_2026-10-21.py`", sec(self.t, "## §2", "## §3"))
        self.assertIn("`fixtures/xbrl/fresh/fresh_2026-10-21.json`", sec(self.t, "## §2", "## §3"))

    def test_28_the_previous_commit_is_in_history(self):
        self.assertEqual(git("merge-base", "--is-ancestor", "001b77a", "HEAD").returncode, 0)

    def test_29_later_files_do_not_exist_before_the_seal_is_committed(self):
        """順序(封の commit の前): 封が履歴に無い間は、後の file(取得・測定・結果)が作業木にも履歴にも無い。
        封の commit の後は、後の file が在るなら封より後の commit で足されている(祖先関係)。draw と封の門は封と同じ commit。"""
        tracked = git("ls-files", "--error-unmatch", SEAL_REL).returncode == 0

        def added(rel):
            shas = [s for s in git("log", "--diff-filter=A", "--format=%H", "--", rel).stdout.split() if s]
            return shas[-1] if shas else None
        if not tracked:
            for rel in FILES_AFTER:
                self.assertFalse(os.path.exists(os.path.join(ROOT, rel)), u"封より先に作業木に在る: " + rel)
                self.assertIsNone(added(rel), u"封より先に履歴に現れた: " + rel)
            return
        seal = added(SEAL_REL)
        for rel in FILES_WITH_SEAL:
            self.assertEqual(added(rel), seal, u"**%s は封と同じ commit で足す(封 §1-3・§6)**" % rel)
        for rel in FILES_AFTER:
            other = added(rel)
            if other is None:
                continue
            self.assertNotEqual(seal, other, rel)
            self.assertEqual(git("merge-base", "--is-ancestor", seal, other).returncode, 0, rel)

    def test_30_no_fetch_script_or_record_has_a_key_like_string(self):
        """取得の script・記録が後で出来たら、鍵らしい字(32 桁の 16 進・Subscription-Key・EDINET_API_KEY=)が無い(封 §1-4)。"""
        for rel in (FETCHED_REL, FILES_AFTER[0]):
            p = os.path.join(ROOT, rel)
            if not os.path.exists(p):
                continue
            t = text(p)
            self.assertIsNone(re.search(r"\b[0-9a-f]{32}\b", t), rel)
            self.assertIsNone(re.search(r"EDINET_API_KEY\s*=\s*['\"]?\w{8,}", t), rel)
        # draw の記録と封にも鍵らしい字は無い
        for p in (DRAW, SEAL):
            t = text(p)
            self.assertIsNone(re.search(r"\b[0-9a-f]{32}\b", t), p)


if __name__ == "__main__":
    unittest.main()
