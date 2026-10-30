# -*- coding: utf-8 -*-
u"""既定の profile を P22 から P26 に切り替える(段 2)の封の門 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md を固定する。
型は P26 の段 1 の封の門 tests/measure/test_xbrl_p26_seal.py と、新しい標本の封の門 tests/measure/test_xbrl_fresh_seal.py に倣う。

縛るもの: 人間の引用(2 つ)と「この封の commit 時点では DEFAULT_PROFILE = "P22" のまま」・判定の根拠(commit 52289c4 と記録 `fresh_2026-10-21.json` の
`判定` が P26。**門が別の関数で K-1・K-2・K-3 を候補ごとに数え直して**同じ順・同じ既定になる)・§0 の数(記録と字で一致)・§1 の区分表
(**`git grep -c DEFAULT_PROFILE 52289c4` を門が数え直して**区分ごとの file 数と字の数が一致)・HUMAN の残り項目(verify_document.py の docstring が実物で
まだ P20 と書いていること)・予測 S-1〜S-12 の行と外れ方と幅の算術(数は記録から)・§3 の限界(行の一覧を記録から数え直す。K-3 の転び方の 74 は記録、59 は
commit の説明)・§4 の pin の遷移の一覧(**`git grep -l` で 52289c4 の木から数え直して**一覧と一致)・§5 の file と順序・
**封が実装より先であること**(DEFAULT_PROFILE がまだ P22・新しい file が無い・vocabulary.py が封の commit 時点の sha16・束ねた指紋と frozen_bundle の世代が封の commit 時点)を縛る。

**数は commit 52289c4 の木から読む**(`git show 52289c4:...` / `git grep ... 52289c4`)。作業木の記録は段 2 の便で動かす(儀式の記録など)ので、封の数を作業木の
file に結ぶと段 2 の便で赤くなる。段 2 の便で動かさない記録(`fresh_2026-10-21.json`・`p26_2026-10-21.json`・`customer_report_2026-10-21.json`)は、作業木の file が
52289c4 の blob と同じであることも見る。

**この門の「封の commit 時点の値」(test_20 から test_21)は、段 2 の commit で「宣言された遷移」に更新する前提である。**
段 2 は vocabulary.py の 1 行を書き換えるので、その file の sha16・束ねた指紋 `adapter_xbrl_py_sha256`・frozen_bundle の束ねた sha がその場で動く。
この門は封の commit 時点の値を字で留めるので段 2 で赤くなる ― それが狙い。そのとき `DECLARED` に (後の値, この封の path) を足して宣言する
(P26 の封の門の ENGINE_TRANSITIONS と同じ型)。宣言を足したら test_20 の「既定がまだ P22」は skip に切り替わる。
**変数名について**: 過去の門が tests/measure の行頭の名前を数える(`ENGINE_LATER = {` を P25 の封の門 test_10 が、PIN_DEF の名前を P26 の封の門 test_16 が数える)ので、
この門の定義には `ENGINE_LATER`・`ENGINE_AT_SEAL`・`UNTOUCHED`・`FROZEN_LATER`・`LATER_ENGINE_COMMITS`・`LATER_FINGERPRINT`・`FINGERPRINT_*`・`LATER_TARGET`・`LATER_FROZEN`・
`FROZEN_BUNDLE_AT_SEAL`・`TARGET_AT_SEAL` を使わない(行頭に置かない)。"""
import glob
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

SEAL_REL = "docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md"
SEAL_P27 = "docs/XBRL_P27_SEAL_2026-10-27.md"    # 2026-10-27 追記: P27 の段 2(下の遷移)
SEAL_DEFAULT_P27 = "docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md"    # 2026-10-28 追記: 既定を P26 -> P27 に切り替える 段 2(下の遷移。vocabulary.py の DEFAULT_PROFILE の 1 行と注記 +5 行・-1 行、verify_document.py の docstring の 1 行 +1 行・-1 行だけ)
SEAL_CAND = "docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md"    # 2026-10-30 追記: 候補の欄を足す(下の遷移)
SEAL = os.path.join(ROOT, SEAL_REL)
BASE = "52289c46acdb60b450c71c5bf80774eccdb91fd7"        # 判定の commit。封の数はこの木の記録
BASE7 = "52289c4"
FRESH_SEAL_REL = "docs/XBRL_FRESH_SAMPLE_SEAL_2026-10-21.md"
FRESH_SEAL_COMMIT = "14cdd21"
P26_STAGE1_COMMIT = "b778dd9"
GATE_REL = "tests/measure/test_xbrl_default_p26_seal.py"

FRESH_REL = "fixtures/xbrl/fresh/fresh_2026-10-21.json"
P26_REL = "fixtures/xbrl/p26_2026-10-21.json"
CUSTOMER_REL = "fixtures/xbrl/customer_report_2026-10-21.json"
RITUAL_REL = "fixtures/xbrl/ritual_2026-10-20.json"
PERIOD_BIND_REL = "fixtures/xbrl/period_bind_2026-10-20.json"
# 段 2 の便で動かさない記録(作業木が 52289c4 と同じ blob)
UNMOVED_RECORDS = (FRESH_REL, P26_REL, CUSTOMER_REL, PERIOD_BIND_REL)

# §5 の file 一覧(この順)。封の後でなければ履歴に現れてはならない
STAGE2_NEW_FILES = ("measure/xbrl_default_p26_2026-10-23.py",
                    "fixtures/xbrl/default_p26_2026-10-23.json",
                    "docs/XBRL_DEFAULT_P26_RESULT_2026-10-23.md",
                    "tests/measure/test_xbrl_default_p26_result.py",
                    "fixtures/xbrl/ritual_2026-10-20_p22.json")
VOCAB_REL = "adapters/xbrl/vocabulary.py"

# 封の commit 時点(52289c4 の木)の adapters/xbrl 16 file の sha256 の先頭 16 桁。**宣言された遷移の前の値**で、消さない。
# 段 2 が書き換えるのは vocabulary.py だけ。残りの 15 file は動いたら赤のまま(遷移を持たない)。
ADAPTERS_AT_BASE = {"adapters/xbrl/__init__.py": "65474b49e6b84626",
                    "adapters/xbrl/comparators.py": "d8706338325e725b",
                    "adapters/xbrl/edinet.py": "e87d48d3597a4c4d",
                    "adapters/xbrl/extract.py": "9982599fc31cbab3",
                    "adapters/xbrl/holds.py": "bed43d9e5c03565a",
                    "adapters/xbrl/instance.py": "f2d9e040f19adebf",
                    "adapters/xbrl/prose.py": "908ce389f16fac0b",
                    "adapters/xbrl/recipes.py": "181b370420ab751b",
                    "adapters/xbrl/registry_setup.py": "7f2cbded9c830211",
                    "adapters/xbrl/report.py": "0d2854e659a5d8e0",
                    "adapters/xbrl/report_customer.py": "141767d189b63733",
                    "adapters/xbrl/resolve.py": "a41043763c1d4073",
                    "adapters/xbrl/run.py": "e2192229bf2e4eff",
                    "adapters/xbrl/verify_document.py": "67e7639de3f5f2ad",
                    "adapters/xbrl/verify_external.py": "0ae333392551912c",
                    "adapters/xbrl/vocabulary.py": "83025e9c0525d08b"}
VOCAB_SHA16_AT_BASE = ADAPTERS_AT_BASE[VOCAB_REL]
FINGERPRINT_AT_BASE = {"adapter_xbrl_py_sha256": "498993e29055472aaf2e691758e62c02a41cd291654cf205ae0a55a9e55df318",
                       "adapter_xbrl_py_files": 16,
                       "core_py_sha256": "34e836bb39762d5af831a9aa11d4ea095e73221beb5bd4510d3b234363a2a6e8",
                       "core_py_files": 4}
FROZEN_AT_BASE = "a97ecf7c44e60c45bf6e6c23439c59955aad8bddf26b1174ee1e0ebabfd59c7c"
FROZEN_COUNT_AT_BASE = 37
# 宣言された遷移(段 2 の commit で足す): {欄: (後の値, 遷移を宣言した封の path)}。封の commit 時点では空だった。
# 2026-10-23(段 2 の実装の便): vocabulary.py の DEFAULT_PROFILE の 1 行と決定の注記(+4 行・-1 行)だけが動いた。上の ADAPTERS_AT_BASE・FINGERPRINT_AT_BASE・FROZEN_AT_BASE は
# 封の commit 時点の値で消さない。受け入れるのは、この封が履歴に在り、値が段 2 の後の値のときだけ。
# 2026-10-27(P27 の段 2): vocabulary_sha16 は段 2 の値 e28733067b1f17f5 から、P27 の封の遷移の値に動いた(下の P27_LATER も同じ封)。段 2 の値は残す(この封が測った時点の値)。
# 85896a67913ce1e7(P27 の段 2) は残す(測った時点の値。vocabulary.py の sha16)、既定を P26 -> P27 に切り替える 段 2(封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md)で 514ebb8104451c07。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
# 2026-10-30(候補の欄を足す): 封 docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md §2-3 が宣言した遷移(人間の承認 2026-10-30)。vocabulary.py に旗 1 つ・P27C・PROFILES の登録、verify_document.py に Claim の欄 candidate(CLAIM_FIELDS の末尾)、report_customer.py に candidate_ja(案 A)を足した。直前の値(vocabulary.py 514ebb8104451c07・verify_document.py c3791080ab5aef2f・report_customer.py 6679138d350ec382・束ねた指紋 92326a0f4dcefd21・frozen_bundle 030455282c89661b)は残す(測った時点の値)。受け入れるのは、その封が履歴に在り、値が候補の欄の後の値のときだけ。
DECLARED = {"vocabulary_sha16": ("7fbcfbf0e472f366", SEAL_CAND),
            # 2026-10-27(P27 の段 2): 封 docs/XBRL_P27_SEAL_2026-10-27.md §2-3 が宣言した遷移。engine の 5 file(vocabulary・recipes・extract・registry_setup・report_customer)に挿入だけを足した(既存の行の書き換え 0)。直前の値は残す(測った時点の値)、P27 の段 2 で下の値。受け入れるのは、その封が履歴に在り、値が P27 の段 2 の後の値のときだけ。
            # 0e51211a8aed2151(P27 の段 2) は残す(測った時点の値。束ねた指紋 adapter_xbrl_py_sha256 の頭 16 字)、既定を P26 -> P27 に切り替える 段 2(封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md)で 92326a0f4dcefd21。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
            # 2026-10-30(候補の欄を足す): 封 docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md §2-3 が宣言した遷移(人間の承認 2026-10-30)。vocabulary.py に旗 1 つ・P27C・PROFILES の登録、verify_document.py に Claim の欄 candidate(CLAIM_FIELDS の末尾)、report_customer.py に candidate_ja(案 A)を足した。直前の値(vocabulary.py 514ebb8104451c07・verify_document.py c3791080ab5aef2f・report_customer.py 6679138d350ec382・束ねた指紋 92326a0f4dcefd21・frozen_bundle 030455282c89661b)は残す(測った時点の値)。受け入れるのは、その封が履歴に在り、値が候補の欄の後の値のときだけ。
            "adapter_xbrl_py_sha256": ("dc7e35fbfb0f56ca6410bb7bfa8b8a366cc3ec19d6614c4cb866400cd9994ff6", SEAL_CAND),
            # 29fd733c8988164a(P27 の段 2) は残す(測った時点の値。frozen_bundle の束ねた sha の頭 16 字)、既定を P26 -> P27 に切り替える 段 2(封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md)で 030455282c89661b。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
            # 2026-10-30(候補の欄を足す): 封 docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md §2-3 が宣言した遷移(人間の承認 2026-10-30)。vocabulary.py に旗 1 つ・P27C・PROFILES の登録、verify_document.py に Claim の欄 candidate(CLAIM_FIELDS の末尾)、report_customer.py に candidate_ja(案 A)を足した。直前の値(vocabulary.py 514ebb8104451c07・verify_document.py c3791080ab5aef2f・report_customer.py 6679138d350ec382・束ねた指紋 92326a0f4dcefd21・frozen_bundle 030455282c89661b)は残す(測った時点の値)。受け入れるのは、その封が履歴に在り、値が候補の欄の後の値のときだけ。
            "frozen_bundle": ("864b1f96292f1615c7e5b7e3bbd6924ebd9955b8354b3c5d51400ba9a01fb054", SEAL_CAND)}

# 2026-10-27(P27 の段 2): 封 docs/XBRL_P27_SEAL_2026-10-27.md §2-3 が宣言した遷移。ADAPTERS_AT_BASE の「vocabulary.py 以外は動いたら赤」は、engine の 4 file
# (recipes・extract・registry_setup・report_customer)に挿入だけを足した P27 の封の遷移の値に限って受け入れる(封が履歴に在り、値が下の値のときだけ)。
P27_LATER = {"adapters/xbrl/recipes.py": ("52d645e713c53c1c", SEAL_P27),
             "adapters/xbrl/extract.py": ("3cf55966f12919f0", SEAL_P27),
             "adapters/xbrl/registry_setup.py": ("d6f25750bcd73c0a", SEAL_P27),
             # 2026-10-30(候補の欄を足す): 封 docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md §2-3 が宣言した遷移(人間の承認 2026-10-30)。vocabulary.py に旗 1 つ・P27C・PROFILES の登録、verify_document.py に Claim の欄 candidate(CLAIM_FIELDS の末尾)、report_customer.py に candidate_ja(案 A)を足した。直前の値(vocabulary.py 514ebb8104451c07・verify_document.py c3791080ab5aef2f・report_customer.py 6679138d350ec382・束ねた指紋 92326a0f4dcefd21・frozen_bundle 030455282c89661b)は残す(測った時点の値)。受け入れるのは、その封が履歴に在り、値が候補の欄の後の値のときだけ。
             "adapters/xbrl/report_customer.py": ("bdbaa00a419219fe", SEAL_CAND),
             # 2026-10-28(既定を P26 -> P27 に切り替える 段 2): 封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md §1-1・§4 (a′) が宣言した遷移。verify_document.py の docstring の 1 行(+1 行・-1 行。実行の字は変えない)。
             # 封の commit 時点の 67e7639de3f5f2ad(ADAPTERS_AT_BASE)は残す(測った時点の値)。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
             # 2026-10-30(候補の欄を足す): 封 docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md §2-3 が宣言した遷移(人間の承認 2026-10-30)。vocabulary.py に旗 1 つ・P27C・PROFILES の登録、verify_document.py に Claim の欄 candidate(CLAIM_FIELDS の末尾)、report_customer.py に candidate_ja(案 A)を足した。直前の値(vocabulary.py 514ebb8104451c07・verify_document.py c3791080ab5aef2f・report_customer.py 6679138d350ec382・束ねた指紋 92326a0f4dcefd21・frozen_bundle 030455282c89661b)は残す(測った時点の値)。受け入れるのは、その封が履歴に在り、値が候補の欄の後の値のときだけ。
             "adapters/xbrl/verify_document.py": ("6c76c8ade6c7b1c8", SEAL_CAND)}
#: 2026-10-28: ``verify_document.py`` の docstring の 1 行の、封の commit 時点の字(P26 の段 2 の封 §1-3 の HUMAN)と、既定を P27 に切り替える段 2 の後の字(封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md §1-1)。
VD_DOC_LINE_AT_BASE = u"``--profile`` を省くと ``vocabulary.DEFAULT_PROFILE``(= P20。2026-10-14 の人間の決定)。"
VD_DOC_LINE_LATER = (u"``--profile`` を省くと ``vocabulary.DEFAULT_PROFILE``(いまは P27。P20 → P21 → P22 → P26 → P27 の履歴と根拠は vocabulary.py の注記。"
                     u"この行は 2026-10-28 の人間の委任「君に任せるよ」で直した)。", "6c76c8ade6c7b1c8", SEAL_CAND)    # 2026-10-30: 候補の欄を足す(封 docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md §2-3)。この 1 行の字は動かず verify_document.py の sha16 だけが動く。直前の値 c3791080ab5aef2f(封 SEAL_DEFAULT_P27)は残す

CRITERIA_ORDER = ("P26", "P25", "P24")
STATES = ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND")
PROFILE_COLS = ("P22", "P23", "P24", "P25", "P26")      # 記録の claims[...]["states"] の並び


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)


def base_text(rel):
    r = git("show", "%s:./%s" % (BASE, rel))
    assert r.returncode == 0, u"52289c4 の木に %s が無い: %s" % (rel, r.stderr[:200])
    return r.stdout


def base_json(rel):
    return json.loads(base_text(rel))


def sec(t, start, end=None):
    i = t.index("\n" + start)
    j = t.index("\n" + end, i + 1) if end else len(t)
    return t[i:j]


def n(x):
    return "{:,}".format(x)


def sha16(rel):
    with io.open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def prediction_rows(block):
    return re.findall(r"(?m)^\| \*\*S-\d+\*\* \|.*$", block)


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def judge(fresh):
    """記録の claims・読み・注入の行から、封 §3 の基準 K-1・K-2・K-3 を候補ごとに数え直す(記録の `判定` を読まない)。"""
    claims = fresh["claims"]
    passed = dict((p, 0) for p in PROFILE_COLS)
    for row in fresh["注入の行"]:
        for p in PROFILE_COLS:
            if row["結果"][p] and row["結果"][p][0] == "GROUNDED":
                passed[p] += 1
    out = {}
    for cand in CRITERIA_ORDER:
        ci = PROFILE_COLS.index(cand)
        new_g = [(d, c["id"]) for d, cl in claims.items() for c in cl if c["states"][0] != "GROUNDED" and c["states"][ci] == "GROUNDED"]
        weak = [(d, c["id"]) for d, cl in claims.items() for c in cl if c["states"][0] == "VALUE_MISMATCH" and c["states"][ci] in ("POINTER_NOT_FOUND", "UNVERIFIABLE")]
        reads_b = fresh["B"][cand]
        reads_c = fresh["C"][cand]
        false_b = sum(1 for x in reads_b if x["読み"] in (u"偽", u"準偽"))
        wrong = sum(1 for x in reads_c if x["読み"] == u"文が本当に違う")
        unsure = sum(1 for x in reads_c if x["読み"] == u"分からない")
        k1 = passed[cand] <= passed["P22"]
        k2 = (len(new_g) == 0) or (false_b * 100.0 <= 3.0 * len(new_g))
        k3 = (len(weak) == 0) or ((wrong + 0.5 * unsure) * 100.0 <= 2.0 * len(weak))
        out[cand] = {"new_g": len(new_g), "weak": len(weak), "false_b": false_b, "wrong": wrong, "unsure": unsure,
                     "passed": passed[cand], "passed_p22": passed["P22"], "ok": bool(k1 and k2 and k3),
                     "reads_b": len(reads_b), "reads_c": len(reads_c)}
    default = None
    for cand in CRITERIA_ORDER:
        if out[cand]["ok"]:
            default = cand
            break
    return out, default


class SealTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = text(SEAL)
        cls.fresh = base_json(FRESH_REL)
        cls.p26 = base_json(P26_REL)
        cls.cust = base_json(CUSTOMER_REL)

    # ------------------------------------------------------------------ 頭
    def test_1_head_quotes_the_human_and_does_not_switch_yet(self):
        head = self.t[:self.t.index("\n## §0 ")]
        self.assertTrue(head.startswith(u"# 封: 既定の profile を P22 から P26 に切り替える(段 2)― 2026-10-23"))
        for s in (u"**人間(2026-10-21 朝)「新しい標本取り、テストしてP25にするか判断したらどう?」「取って良い あとは全て任せる」。",
                  u"engine の事前承認(2026-10-21)「engine に触るので承認が要る 先に承認しておくので好きに進めて これをもって承認とする」。**",
                  u"封 `docs/XBRL_FRESH_SAMPLE_SEAL_2026-10-21.md`(commit `14cdd21`)§3 の基準で決め、",
                  u"判定は結果 `docs/XBRL_FRESH_SAMPLE_RESULT_2026-10-21.md`(commit `52289c4`)で **P26**。",
                  u"作法(封 → 実装 → 凍結 → 独立監査 GO → commit)のまま",
                  u"数を見てから封・予測を直さない。外れは外れとして残す。",
                  u"**この封の commit 時点では `DEFAULT_PROFILE = \"P22\"` のまま。**",
                  u"0 USD・通信なし・鍵の値は読まない。",
                  u"人間の確認が要りうる点は §1-4 に列挙した(この封は勝手に直さない)。"):
            self.assertIn(s, head, s)
        # 引用している封が在り、その字が引用と同じ(字の食い違いを避ける)
        fresh_seal = base_text(FRESH_SEAL_REL)
        self.assertIn(u"人間(2026-10-21 朝)「新しい標本取り、テストしてP25にするか判断したらどう?」「取って良い あとは全て任せる」", fresh_seal)
        self.assertIn(u"- 判定は記録の数から機械で(門で縛る)。司令塔は判定を覆さない。", fresh_seal)
        self.assertIn(u"**P26(封 `docs/XBRL_P26_SEAL_*`、「違う」に出る正しい文の主因を減らす直し)の段 1 が取得より前に commit されていれば、候補は P26 → P25 → P24 の順**。"
                      u"P26 も K-1〜K-3(P22 → P26 で同じ定義)で判定し、満たせば P26 を既定にする。", fresh_seal)
        self.assertIn(u"**K-1・K-2・K-3 を全部満たす → 既定を P25 にする**(段 2: `DEFAULT_PROFILE = \"P25\"`・既定の字の試験・儀式の走らせ直し・README・pin。"
                      u"封 → 実装 → 凍結 → 独立監査 GO → commit の作法のまま)。", fresh_seal)
        # 事前承認の言葉は P26 の封(段 1)に「engine の事前承認 2026-10-21」として引かれている
        p26_seal = base_text("docs/XBRL_P26_SEAL_2026-10-21.md")
        self.assertIn(u"「報告形の問題はきちんと解決して」「あとは全て任せる」", p26_seal)

    def test_2_section_headings_are_the_six_in_order(self):
        heads = re.findall(r"(?m)^## (§\d)[^\n]*", self.t)
        self.assertEqual(heads, [u"§0", u"§1", u"§2", u"§3", u"§4", u"§5"])
        self.assertEqual(re.findall(r"(?m)^### (§1-\d)", self.t), [u"§1-1", u"§1-2", u"§1-3", u"§1-4"])

    # ------------------------------------------------------------------ 判定(K-1〜K-3 を門が数え直す)
    def test_3_the_judgement_is_recomputed_from_the_record_and_is_p26(self):
        out, default = judge(self.fresh)
        self.assertEqual(default, "P26")
        self.assertEqual(self.fresh[u"判定"][u"既定"], default)
        self.assertEqual(self.fresh[u"判定"][u"候補の順"], list(CRITERIA_ORDER))
        # 記録の `判定` の数と、門が数え直した数が同じ(記録の取り違えを避ける)
        for cand in CRITERIA_ORDER:
            rec = self.fresh[u"判定"][u"候補ごと"][cand]
            mine = out[cand]
            self.assertEqual((rec["K-1"][u"候補が通した"], rec["K-1"][u"P22 が通した"]), (mine["passed"], mine["passed_p22"]))
            self.assertEqual((rec["K-2"][u"新 GROUNDED"], rec["K-2"][u"偽"] + rec["K-2"][u"準偽"]), (mine["new_g"], mine["false_b"]))
            self.assertEqual((rec["K-3"][u"弱まった行"], rec["K-3"][u"文が本当に違う"], rec["K-3"][u"分からない"]), (mine["weak"], mine["wrong"], mine["unsure"]))
            self.assertTrue(rec[u"全部満たす"] and mine["ok"], cand)
            self.assertEqual(mine["reads_b"], mine["new_g"], cand)         # 読みの行と数えた行が同じ本数
            self.assertEqual(mine["reads_c"], mine["weak"], cand)
        # §0 の字
        b = sec(self.t, "## §0 ", "## §1")
        p26, p25, p24 = out["P26"], out["P25"], out["P24"]
        self.assertIn(u"- 判定(記録 `fixtures/xbrl/fresh/fresh_2026-10-21.json` の `判定`): 候補の順は P26 → P25 → P24、既定は **P26**。", b)
        self.assertIn(u"P26 は K-1(通した %d 対 P22 の %d)・K-2(偽 %d / 新 GROUNDED %d)・K-3(文が本当に違う %d・分からない %d / 「違う」が弱まった行 %d)を全部満たし、"
                      % (p26["passed"], p26["passed_p22"], p26["false_b"], p26["new_g"], p26["wrong"], p26["unsure"], p26["weak"]), b)
        self.assertIn(u"P25(K-3 は %d / %d)・P24(%d / %d)も全部満たす。先頭の候補が P26。"
                      % (p25["wrong"], p25["weak"], p24["wrong"], p24["weak"]), b)
        self.assertEqual((p26["passed"], p26["passed_p22"], p26["false_b"], p26["new_g"], p26["wrong"], p26["unsure"], p26["weak"]), (5, 5, 0, 59, 0, 0, 436))
        self.assertEqual((p25["wrong"], p25["weak"], p24["wrong"], p24["weak"]), (0, 361, 0, 64))
        # 順序の事実: P26 の段 1 の commit が取得より前(記録の `順序`)
        o = self.fresh[u"順序"]
        self.assertTrue(o[u"P26 の commit は HEAD の祖先"] and o[u"P26 は候補"])
        self.assertTrue(o[u"P26 の commit"].startswith(P26_STAGE1_COMMIT))
        self.assertLess(o[u"最初に置いた ZIP の mtime(UTC)"], "2026-10-22T15:16:00Z")
        self.assertIn(u"P26 の段 1 `b778dd9` は取得の最初の ZIP(2026-10-22T15:15:15Z)より前(記録の `順序`)。", b)
        self.assertEqual(o[u"最初に置いた ZIP の mtime(UTC)"], "2026-10-22T15:15:15Z")
        self.assertEqual(git("merge-base", "--is-ancestor", P26_STAGE1_COMMIT, BASE).returncode, 0)
        # 封 14cdd21 §3 の字が、いま追跡されている封と判定の commit の木で同じ
        self.assertEqual(git("merge-base", "--is-ancestor", FRESH_SEAL_COMMIT, BASE).returncode, 0)
        self.assertEqual(git("merge-base", "--is-ancestor", BASE, "HEAD").returncode, 0, u"判定の commit 52289c4 が HEAD の祖先に無い")

    def test_4_section_0_numbers_equal_the_records(self):
        b = sec(self.t, "## §0 ", "## §1")
        A = self.fresh["A"]
        p22 = self.cust[u"集計"]["P22"][u"state"]
        agg = self.p26["Q1"][u"集計"]
        p26_67 = dict((s, agg[u"%s の合計 P26" % s]) for s in STATES)
        self.assertEqual(sum(p22.values()), 7799)
        self.assertEqual(sum(p26_67.values()), 7799)
        self.assertEqual(agg[u"総 claim"], 7799)
        self.assertEqual(self.cust[u"集計"]["P22"][u"書類数"], 67)
        self.assertIn(u"- 無改変の 4 state、67 書類(claim 7,799)、いまの既定 P22 → P26: GROUNDED %s → %s・VALUE_MISMATCH %s → %s・UNVERIFIABLE %s → %s・POINTER_NOT_FOUND %s → %s"
                      % (n(p22["GROUNDED"]), n(p26_67["GROUNDED"]), n(p22["VALUE_MISMATCH"]), n(p26_67["VALUE_MISMATCH"]), n(p22["UNVERIFIABLE"]),
                         n(p26_67["UNVERIFIABLE"]), n(p22["POINTER_NOT_FOUND"]), n(p26_67["POINTER_NOT_FOUND"])), b)
        self.assertEqual((p22["GROUNDED"], p26_67["GROUNDED"]), (4242, 4371))
        self.assertEqual((p22["VALUE_MISMATCH"], p26_67["VALUE_MISMATCH"]), (1410, 433))
        self.assertEqual((p22["UNVERIFIABLE"], p26_67["UNVERIFIABLE"]), (1323, 1579))
        self.assertEqual((p22["POINTER_NOT_FOUND"], p26_67["POINTER_NOT_FOUND"]), (824, 1416))
        a22, a26 = A["P22"], A["P26"]
        self.assertEqual((A[u"書類"], A["claim"]), (30, 3923))
        self.assertIn(u"- 無改変の 4 state、新しい標本 30 書類(claim 3,923)、P22 → P26: GROUNDED %s → %s・VALUE_MISMATCH %s → %s・UNVERIFIABLE %s → %s・POINTER_NOT_FOUND %s → %s(記録の `A`)。"
                      % (n(a22["GROUNDED"][u"件"]), n(a26["GROUNDED"][u"件"]), n(a22["VALUE_MISMATCH"][u"件"]), n(a26["VALUE_MISMATCH"][u"件"]),
                         n(a22["UNVERIFIABLE"][u"件"]), n(a26["UNVERIFIABLE"][u"件"]), n(a22["POINTER_NOT_FOUND"][u"件"]), n(a26["POINTER_NOT_FOUND"][u"件"])), b)
        self.assertEqual(sum(a26[s][u"件"] for s in STATES), 3923)
        self.assertEqual(sum(a22[s][u"件"] for s in STATES), 3923)
        self.assertIn(u"state の違う行は %d(記録の `動いた行`)。" % len(self.fresh[u"動いた行"]), b)
        self.assertEqual(len(self.fresh[u"動いた行"]), 507)
        # 誤りを通す側
        q3 = self.p26["Q3"]
        hole = q3[u"穴 B"][u"集計"][u"P26 で通した(GROUNDED のまま)"]
        rit = q3[u"儀式"][u"通した P26"]
        s2 = q3[u"段 2"][u"集計"][u"全注入で Core 自身 P26 が GROUNDED"]
        self.assertIn(u"穴 B の注入 %d / %d、儀式 %d / %d、段 2 の材料の注入 %d / %d" % (hole[u"件"], hole[u"分母"], rit[u"件"], rit[u"分母"], s2[u"件"], s2[u"分母"]), b)
        self.assertEqual((hole[u"件"], hole[u"分母"], rit[u"件"], rit[u"分母"], s2[u"件"], s2[u"分母"]), (0, 485, 2, 243, 0, 64))
        d = self.fresh["D"]
        self.assertEqual(d[u"注入"], 741)
        self.assertEqual(set(d[p][u"通した"] for p in PROFILE_COLS), set([5]))
        self.assertIn(u"新しい標本の注入 741 回で通したのは P22 から P26 まで同じ 5 件。", b)
        # 読みの断りと試作の位置づけ
        for s in (u"- **読みはエージェントの読みで、人間の読みではない**(K-2・K-3 は読みに依る)。監査が示した K-3 の転び方は §3。",
                  u"- **試作(scratchpad の clone。正本でない。`scratchpad/default_p26/`)**: `DEFAULT_PROFILE` の 1 行だけを P26 にした clone で、",
                  u"試作の数は §2 の幅に写したもので、記録(fixtures)に無い。実装席が同じ測定を記録に残す。"):
            self.assertIn(s, b, s)

    # ------------------------------------------------------------------ §1
    def test_5_section_1_engine_is_one_line_and_the_other_files_are_untouched(self):
        b = sec(self.t, "## §1 ", "## §2")
        self.assertTrue(b.startswith(u"\n## §1 変えるもの(engine 1 file の 1 行。残りは試験・記録・文書)"))
        for s in (u"- `adapters/xbrl/vocabulary.py`: `DEFAULT_PROFILE = \"P22\"` を `DEFAULT_PROFILE = \"P26\"` に(1 行)。日付つきの決定の注記を足す",
                  u"(P16・P20・P21・P22 の注記は消さない。前例は a516288・d0b544c とも +5/−1)。**他の engine の行は 1 字も変えない。**",
                  u"`recipes.py`・`extract.py`・`registry_setup.py`・`report_customer.py`・`comparators.py` ほか adapters/xbrl の 15 file と `core/` は 0 行(sha16 が封の commit 時点と同じ)。",
                  u"`run.py` と `verify_document.py` は既定の名前を `V.DEFAULT_PROFILE` から引くので、実行の字は変えない。",
                  u"- P22 以前の profile の字、`PROFILES` の行、P26 の定義は変えない。P16〜P25 を明示した呼び出しと試験の数は 1 つも変えない。"):
            self.assertIn(s, b, s)
        # 実物: いまの vocabulary.py の既定の行は 1 行で P22。run.py・verify_document.py は名前を V.DEFAULT_PROFILE から引く(52289c4 の木)
        voc = base_text(VOCAB_REL)
        self.assertEqual(len(re.findall(r'(?m)^DEFAULT_PROFILE = "P22"$', voc)), 1)
        self.assertEqual(len(re.findall(r"(?m)^DEFAULT_PROFILE = ", voc)), 1)
        self.assertIn(u"profile_name = profile_name or V.DEFAULT_PROFILE", base_text("adapters/xbrl/verify_document.py"))
        self.assertIn(u"default=V.DEFAULT_PROFILE", base_text("adapters/xbrl/run.py"))
        # 前例: a516288 と d0b544c の vocabulary.py は +5/-1
        for c in ("a516288", "d0b544c"):
            stat = git("show", "--numstat", "--format=", c, "--", VOCAB_REL).stdout.split()
            self.assertEqual(stat[:2], ["5", "1"], c)

    def test_6_section_1_2_table_equals_the_grep_at_the_base_commit(self):
        """区分ごとの file 数と字の数を、`git grep -c DEFAULT_PROFILE 52289c4` から門が数え直して表と突き合わせる。"""
        b = sec(self.t, "### §1-2 ", "### §1-3")
        out = git("grep", "-c", "DEFAULT_PROFILE", BASE, "--", ".").stdout.splitlines()
        per = {}
        for line in out:
            path, _, cnt = line.rpartition(":")
            path = path[len(BASE) + 1:]
            per[path] = int(cnt)
        groups = {"engine": ("adapters/xbrl/",), "frozen_bundle": ("fixtures/frozen_bundle_sha.py",), "tests/adapters/xbrl": ("tests/adapters/xbrl/",),
                  "tests/measure": ("tests/measure/",), "measure": ("measure/",), "fixtures/xbrl": ("fixtures/xbrl/",), "docs": ("docs/",)}
        got = {}
        for name, prefixes in groups.items():
            files = [p for p in per if any(p.startswith(x) for x in prefixes)]
            got[name] = (len(files), sum(per[p] for p in files))
        self.assertEqual(sum(v[0] for v in got.values()), len(per))
        self.assertEqual((len(per), sum(per.values())), (94, 303))
        self.assertEqual(got, {"engine": (3, 8), "frozen_bundle": (1, 8), "tests/adapters/xbrl": (10, 22), "tests/measure": (30, 159),
                               "measure": (14, 42), "fixtures/xbrl": (13, 23), "docs": (23, 41)})
        self.assertIn(u"`git grep -c DEFAULT_PROFILE 52289c4` で 94 file・303 か所を数えた", self.t)
        rows = [cells(l) for l in re.findall(r"(?m)^\|(?!---)(?! 区分).*$", b)]
        self.assertEqual(len(rows), 7)
        for row in rows:
            name = {u"engine": "engine", u"frozen_bundle": "frozen_bundle", u"tests/adapters/xbrl": "tests/adapters/xbrl", u"tests/measure": "tests/measure",
                    u"measure": "measure", u"fixtures/xbrl": "fixtures/xbrl", u"docs": "docs"}[row[0]]
            nfile = int(re.match(r"(\d+) file", row[1].replace(u"`fixtures/frozen_bundle_sha.py` ", "")).group(1))
            self.assertEqual((nfile, int(row[2])), got[name], row[0])
        # engine の内訳: vocabulary.py 2(行と注記の字)・verify_document.py 3・run.py 3
        self.assertEqual((per["adapters/xbrl/vocabulary.py"], per["adapters/xbrl/verify_document.py"], per["adapters/xbrl/run.py"]), (2, 3, 3))
        self.assertIn(u"`run.py`(3)", b)
        self.assertIn(u"`verify_document.py`(3)", b)
        # README は DEFAULT_PROFILE の字が無いが既定の名前 P22 を書いている(= 直す)。FACTS は P22・P26 の字が 0(= 触らない)
        for rel in ("README.md", "README.en.md"):
            self.assertNotIn("DEFAULT_PROFILE", base_text(rel))
            self.assertIn("P22", base_text(rel))
        facts = base_text("docs/FACTS_FOR_BUYERS_2026-10-20.md")
        self.assertEqual((len(re.findall(r"P22", facts)), len(re.findall(r"P26", facts))), (0, 0))
        for s in (u"`README.md`(「いまの段」と「10 分の再現」の節)・`README.en.md`(同じ節)= **直す**",
                  u"`docs/FACTS_FOR_BUYERS_2026-10-20.md` は P22・P26 の字が 0 = **触らない**(§6 の覆いの 4 行だけ直す)。"):
            self.assertIn(s, b, s)
        # 儀式
        for s in (u"guard「既定が P22」を P26 に直し、記録 `fixtures/xbrl/ritual_2026-10-20.json` を P26(既定)で採り直す。",
                  u"P22 の記録は byte 一致の写し `fixtures/xbrl/ritual_2026-10-20_p22.json` と履歴に残す(前例: `ritual_2026-10-20_p21.json`)。"):
            self.assertIn(s, b, s)
        self.assertIn(u'if V.DEFAULT_PROFILE != "P22":', base_text("measure/ritual_2026-10-20.py"))
        self.assertTrue(git("cat-file", "-e", "%s:./fixtures/xbrl/ritual_2026-10-20_p21.json" % BASE).returncode == 0)
        self.assertTrue(git("cat-file", "-e", "%s:./fixtures/xbrl/ritual_2026-10-20_p22.json" % BASE).returncode != 0)

    def test_7_hum_the_docstring_is_still_p20_in_the_actual_file(self):
        """HUMAN の残り項目(§1-3)は実物の字とまだ食い違っている。ここが直ると封の前提が変わる(= 別便で人間が直した)ので赤で気づく。"""
        b = sec(self.t, "### §1-3 ", "### §1-4")
        vd = base_text("adapters/xbrl/verify_document.py")
        line = [l for l in vd.splitlines() if l.startswith(u"``--profile`` を省くと ``vocabulary.DEFAULT_PROFILE``")]
        self.assertEqual(line, [u"``--profile`` を省くと ``vocabulary.DEFAULT_PROFILE``(= P20。2026-10-14 の人間の決定)。"])
        self.assertIn(u"「`--profile` を省くと `vocabulary.DEFAULT_PROFILE`(= P20。2026-10-14 の人間の決定)」", b)
        self.assertIn(u"**この封も直さない。**", b)
        self.assertIn(u"食い違いは 4 つめ(P20・P21・P22 に続く)になる。", b)
        # 前例: 儀式の封・P22 の段 2 の結果が HUMAN として残した
        self.assertIn(u"**HUMAN**: 1 行の docstring の直しの承認", base_text("docs/XBRL_RITUAL_SEAL_2026-10-20.md"))
        self.assertIn(u"HUMAN の残り一点(承認待ち)", base_text("docs/XBRL_PERIOD_BIND_RESULT_2026-10-20.md"))
        # verify_document.py の sha16 は封の commit 時点のまま(別便で直したら赤になる)。
        # 2026-10-28(既定を P26 -> P27 に切り替える 段 2): 封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md §1-1 がこの 1 行を直した。前提が変わったことを、宣言された遷移(docstring の後の字・sha16)で残す。
        # 封の commit 時点の字(上の base_text の 1 行)は消さない。受け入れるのは、その封が履歴に在り、実物の字と sha16 が段 2 の後の値のときだけ。
        got = sha16("adapters/xbrl/verify_document.py")
        if got != ADAPTERS_AT_BASE["adapters/xbrl/verify_document.py"]:
            line_later, sha_later, seal_rel = VD_DOC_LINE_LATER
            self.assertTrue(git("log", "--diff-filter=A", "--format=%H", "--", seal_rel).stdout.split(), u"**docstring が直っているのに、遷移を宣言した封が履歴に無い**")
            self.assertEqual(got, sha_later, u"**verify_document.py が、宣言された遷移の値とも違う**")
            now = [l for l in text(os.path.join(ROOT, "adapters/xbrl/verify_document.py")).splitlines() if l.startswith(u"``--profile`` を省くと ``vocabulary.DEFAULT_PROFILE``")]
            self.assertEqual(now, [line_later])
            self.assertNotEqual(now, [VD_DOC_LINE_AT_BASE])

    def test_8_the_human_confirmation_points_are_listed_and_match_the_facts(self):
        b = sec(self.t, "### §1-4 ", "## §2")
        items = re.findall(r"(?m)^(\d)\. \*\*([^*]+)\*\*", b)
        self.assertEqual([i for i, _ in items], ["1", "2", "3", "4", "5"])
        self.assertEqual([t for _, t in items], [u"engine の承認の範囲", u"DECISION_LOG", u"verify_document.py の docstring", u"段 2 と無関係の赤が 1 本、既に在る", u"K-3 の読み"])
        # (2) DECISION_LOG: 最後の更新は 2026-10-13 で、P20・P21・P22 の切り替えの項目は無い
        dl = git("-C", REPO, "show", "%s:docs/DECISION_LOG.md" % BASE).stdout
        self.assertEqual(len(re.findall(r"既定 profile", dl)) >= 1, True)
        self.assertIn(u"2026-10-13", git("-C", REPO, "log", "-1", "--format=%ci", BASE, "--", "docs/DECISION_LOG.md").stdout)
        self.assertNotIn(u"P22", dl)
        self.assertNotIn(u"P21", dl)
        self.assertIn(u"変えるときは人間の決定と DECISION_LOG の項目が要る", base_text(VOCAB_REL))
        # (4) 既に赤の 1 本は実物の字(鍵の字の型)で 2 file に当たる。門は赤を再現しない(木の状態に依る)ので、当たる 2 file の字だけ縛る
        pat = re.compile(r"EDINET_API_KEY\s*[:=]\s*\S{8,}")
        hits = [rel for rel in ("measure/xbrl_fresh_fetch_2026-10-21.py", "tests/measure/test_xbrl_fresh_fetch.py") if pat.search(base_text(rel))]
        self.assertEqual(hits, ["measure/xbrl_fresh_fetch_2026-10-21.py", "tests/measure/test_xbrl_fresh_fetch.py"])
        self.assertIn(u"test_no_edinet_api_key_value_anywhere_under_audit_core", b)
        self.assertIn("test_no_edinet_api_key_value_anywhere_under_audit_core", base_text("tests/core/test_boundary.py"))
        # この封と門自身は、その字の型に当たらない(新しい赤を作らない)
        for p in (SEAL, os.path.join(ROOT, GATE_REL)):
            self.assertIsNone(pat.search(text(p)), p)

    # ------------------------------------------------------------------ §2
    def test_9_twelve_predictions_each_with_a_way_to_fail(self):
        b = sec(self.t, "## §2 ", "## §3")
        rows = prediction_rows(b)
        ids = re.findall(r"(?m)^\| \*\*S-(\d+)\*\* \|", b)
        self.assertEqual(ids, [str(i) for i in range(1, 13)])
        self.assertEqual(len(rows), 12)
        for line in rows:
            c = cells(line)
            self.assertEqual(len(c), 3, line)
            self.assertTrue(c[1], u"予測が空: " + line)
            self.assertTrue(c[2], u"外れ方が空: " + line)
        by_id = dict((re.match(r"\| \*\*S-(\d+)\*\*", l).group(1), cells(l)) for l in rows)
        # 行ごとに外れ方の字を縛る(外れ方を消す・緩めると赤)
        self.assertEqual(by_id["1"][2], u"1 書類でも違う / 対照が 97 / 97 でない")
        self.assertEqual(by_id["2"][2], u"4 state のどれか 1 つでも違う / 幅の外")
        self.assertEqual(by_id["3"][2], u"1 つでも違う")
        self.assertEqual(by_id["4"][2], u"1 つでも違う / 写しが byte 一致でない")
        self.assertEqual(by_id["5"][2], u"1 つでも違う / 「違う」の節と VALUE_MISMATCH が食い違う")
        self.assertEqual(by_id["6"][2], u"通した 1 以上 / 違う行がある")
        self.assertEqual(by_id["7"][2], u"超える / 他の file が動く")
        self.assertEqual(by_id["10"][2], u"1 つでも違う")
        self.assertEqual(by_id["11"][2], u"数が違う")
        self.assertEqual(by_id["12"][2], u"違う")
        # 本当に外れうる予測と当たって当然の予測の区別(正直に書く)
        self.assertIn(u"予測 S-1・S-2・S-3・S-4・S-5・S-6 の数の多くは P26 明示の記録の写しで、**当たって当然の再現**", b)
        self.assertIn(u"本当に外れうるのは S-1(配線)・S-2 の幅(P22 から動く行)・S-8(赤の数と種類)・S-9(重い走らせ直し)・S-11(覆い)である。", b)

    def test_10_prediction_numbers_equal_the_records(self):
        b = sec(self.t, "## §2 ", "## §3")
        by_id = dict((re.match(r"\| \*\*S-(\d+)\*\*", l).group(1), l) for l in prediction_rows(b))
        # S-1
        self.assertIn(u"手元の 67 書類(claim 7,799)で違った書類 **0 / 67**、新しい標本 30 書類(claim 3,923)で **0 / 30**。対照(既定を実行中だけ P22 に戻す)で違う書類は **97 / 97**", by_id["1"])
        self.assertEqual(67 + 30, 97)
        self.assertEqual(len(self.fresh["docs"]), 30)
        # S-2: P26 の 4 state は P26 の記録、いまの P22 は報告形の記録。P22 → P26 の動く行の幅
        agg = self.p26["Q1"][u"集計"]
        p22 = self.cust[u"集計"]["P22"][u"state"]
        self.assertIn(u"GROUNDED **%s**・VALUE_MISMATCH **%s**・UNVERIFIABLE **%s**・POINTER_NOT_FOUND **%s**(合計 7,799)"
                      % tuple(n(agg[u"%s の合計 P26" % s]) for s in STATES), by_id["2"])
        self.assertIn(u"(%s / %s / %s / %s)" % (n(p22["GROUNDED"]), n(p22["VALUE_MISMATCH"]), n(p22["UNVERIFIABLE"]), n(p22["POINTER_NOT_FOUND"])), by_id["2"])
        self.assertIn(u"GROUNDED を離れる行 **15〜23**(うち VALUE_MISMATCH に **5〜9**)、新しい GROUNDED **140〜156**", by_id["2"])
        # 幅の算術: 4,242 − 離れる + 新しい = 4,371 が幅の中で成り立つ(中心 19・148 で成り立ち、幅の端でも負にならない)
        self.assertEqual(p22["GROUNDED"] - 19 + 148, agg[u"GROUNDED の合計 P26"])
        lo_leave, hi_leave, lo_new, hi_new = 15, 23, 140, 156
        self.assertTrue(lo_new - hi_leave <= agg[u"GROUNDED の合計 P26"] - p22["GROUNDED"] <= hi_new - lo_leave)
        # S-3: 新しい標本の 4 state と動いた行の向き(記録の claims から門が数える)
        a26 = self.fresh["A"]["P26"]
        self.assertIn(u"GROUNDED **%s**・VALUE_MISMATCH **%s**・UNVERIFIABLE **%s**・POINTER_NOT_FOUND **%s**(合計 3,923)"
                      % tuple(n(a26[s][u"件"]) for s in STATES), by_id["3"])
        moves = {}
        for cl in self.fresh["claims"].values():
            for c in cl:
                if c["states"][0] != c["states"][4]:
                    moves[(c["states"][0], c["states"][4])] = moves.get((c["states"][0], c["states"][4]), 0) + 1
        self.assertEqual(sum(moves.values()), 507)
        self.assertEqual(moves, {("VALUE_MISMATCH", "POINTER_NOT_FOUND"): 297, ("VALUE_MISMATCH", "UNVERIFIABLE"): 139, ("UNVERIFIABLE", "GROUNDED"): 54,
                                 ("POINTER_NOT_FOUND", "GROUNDED"): 5, ("GROUNDED", "VALUE_MISMATCH"): 5, ("UNVERIFIABLE", "VALUE_MISMATCH"): 4,
                                 ("GROUNDED", "UNVERIFIABLE"): 2, ("POINTER_NOT_FOUND", "UNVERIFIABLE"): 1})
        for (a, c), k in sorted(moves.items(), key=lambda kv: -kv[1]):
            self.assertIn(u"%s → %s **%d**" % (a, c, k), by_id["3"], (a, c))
        self.assertIn(u"P22 と state の違う行は **507**", by_id["3"])
        # S-4: 儀式。P26 の数は P26 の記録、P22 の数は 52289c4 の儀式の記録(動かす前)
        q3r = self.p26["Q3"][u"儀式"]
        base_rit = base_json(RITUAL_REL)
        self.assertEqual(base_rit[u"入力"][u"profile"], "P22")
        pr, st = q3r[u"通した P26"], q3r[u"止めた P26"]
        rest = q3r[u"その他 P26"]
        plain = q3r[u"素の書類 P26"]
        self.assertIn(u"通した **%d / %d = %.1f%%**・止めた(VALUE_MISMATCH)**%d / %d = %.1f%%**・結べない(POINTER_NOT_FOUND)**%d**"
                      % (pr[u"件"], pr[u"分母"], pr[u"率"], st[u"件"], st[u"分母"], st[u"率"], rest["detected:POINTER_NOT_FOUND"]), by_id["4"])
        self.assertEqual((pr[u"件"], pr[u"分母"], st[u"件"], rest["detected:POINTER_NOT_FOUND"]), (2, 243, 210, 31))
        self.assertEqual(pr[u"件"] + st[u"件"] + rest["detected:POINTER_NOT_FOUND"], pr[u"分母"])
        self.assertIn(u"素の書類(claim 412)は GROUNDED **%d**・POINTER_NOT_FOUND **%d**・UNVERIFIABLE **%d**・VALUE_MISMATCH **%d**"
                      % tuple(plain[u"state の分布"][s] for s in ("GROUNDED", "POINTER_NOT_FOUND", "UNVERIFIABLE", "VALUE_MISMATCH")), by_id["4"])
        self.assertEqual(sum(plain[u"state の分布"].values()), plain["claim"])
        bp, bs = base_rit[u"通した"], base_rit[u"素の書類"][u"state の分布"]
        self.assertIn(u"いまの P22 の記録(%d / %d = %.1f%%、素の書類 %d / %d / %d / %d)" % (bp[u"件"], bp[u"分母"], bp[u"率"], bs["GROUNDED"], bs["POINTER_NOT_FOUND"], bs["UNVERIFIABLE"], bs["VALUE_MISMATCH"]), by_id["4"])
        self.assertEqual((bp[u"件"], bp[u"分母"]), (15, 240))
        # S-5: 報告形の節(67 書類の P26 は P26 の記録 Q7、P22 は報告形の記録)
        q7 = self.p26["Q7"][u"書類別"]
        tot = {}
        for r in q7:
            for k, v in r.items():
                if k != "doc":
                    tot[k] = tot.get(k, 0) + v
        sections = self.cust[u"集計"]["P22"][u"節"]
        self.assertEqual(tot[u"違う(節の件数)"], tot[u"VALUE_MISMATCH(state)"])
        self.assertEqual((tot[u"違う(節の件数)"], tot[u"要確認(節の件数)"], tot[u"対象外"], tot[u"判断しない"], tot[u"一致(節の件数)"]), (433, 1775, 151, 1069, 4371))
        self.assertEqual(433 + 1775 + 151 + 1069 + 4371, 7799)
        self.assertEqual(tot["claims"], 7799)
        self.assertIn(u"違う **433**・要確認 **1,775**・対象外 **151**・判断しない **1,069**・一致 **4,371**(合計 7,799)", by_id["5"])
        self.assertIn(u"(P22 の節は %s / %s / %s / %s / %s)" % (n(sections[u"違う"]), n(sections[u"要確認"]), n(sections[u"対象外"]), n(sections[u"判断しない"]), n(sections[u"一致"])), by_id["5"])
        self.assertEqual(sum(sections.values()), 7799)
        # 要確認 + 対象外 + 判断しない = UNVERIFIABLE + POINTER_NOT_FOUND(節の割り当ての閉じ方)
        self.assertEqual(tot[u"要確認(節の件数)"] + tot[u"対象外"] + tot[u"判断しない"], agg[u"UNVERIFIABLE の合計 P26"] + agg[u"POINTER_NOT_FOUND の合計 P26"])
        # S-6: 穴 B・段 2 の材料。いまの P22 は期の縛りの段 2 の記録
        hole = self.p26["Q3"][u"穴 B"][u"集計"]
        self.assertEqual(hole[u"P26 の結果"], {u"その他": 5, u"止めた": 480})
        self.assertEqual(hole[u"P26 で通した(GROUNDED のまま)"][u"件"], 0)
        e1 = base_json(PERIOD_BIND_REL)["stage2_default_2026-10-20"]["E1"]
        self.assertEqual((e1[u"通した(GROUNDED のまま)"][u"件"], e1[u"通した(GROUNDED のまま)"][u"分母"]), (1, 485))
        self.assertIn(u"通した(GROUNDED のまま)**0 / 485**(いまの P22 は 1 / 485)・止めた **480**・その他 **5**、段 2 の材料の注入 64 件で Core 自身が GROUNDED にした **0 / 64**。"
                      u"P26 の記録の P26 の欄と 1 行ずつ比べて違う行 **0**", by_id["6"])
        self.assertEqual(len(self.p26["Q3"][u"穴 B"][u"行"]), 485)
        # S-7: engine の差分の幅と、動く欄・動かない欄
        for s in (u"`vocabulary.py` の挿入 **≤ 8**・削除 **1**", u"adapters/xbrl の他の 15 file の sha16 と `core/` は 0 行",
                  u"`adapter_xbrl_py_sha256` と frozen_bundle の世代は動き、`adapter_xbrl_py_files` 16・`core_py_sha256`・frozen_bundle の本数 37 は動かない"):
            self.assertIn(s, by_id["7"], s)
        self.assertEqual((FINGERPRINT_AT_BASE["adapter_xbrl_py_files"], FROZEN_COUNT_AT_BASE), (16, 37))
        # S-10: README と FACTS
        self.assertIn(u"README.md と README.en.md の儀式の節の数は P26 の記録(S-4)と 1 対 1(門が節の全文を縛る)。`docs/FACTS_FOR_BUYERS_2026-10-20.md` の P22・P26 の字は 0 のまま", by_id["10"])
        # S-11: 覆い。52289c4 の記録は 220
        cov = base_json("fixtures/suite_coverage_2026-10-16.json")
        self.assertEqual(cov["test_files_on_disk"], 220)
        self.assertIn(u"いま(`52289c4`)の 220 から、この封の commit で **221**", by_id["11"])
        self.assertIn(u"段 2 の commit で **222**", by_id["11"])
        # S-12
        self.assertIn(u"記録から門が別の関数で求め直しても **P26**", by_id["12"])

    # ------------------------------------------------------------------ §3
    def test_11_limits_are_written_and_their_rows_are_recomputed_from_the_record(self):
        b = sec(self.t, "## §3 ", "## §4")
        bullets = re.findall(r"(?m)^- ", b)
        self.assertEqual(len(bullets), 10)
        docs = self.fresh["docs"]
        claims = self.fresh["claims"]

        def rows_of(first, last):
            out = []
            for i, d in enumerate(docs):
                for c in claims[d]:
                    if c["states"][0] == first and c["states"][4] == last:
                        out.append((i, c["id"]))
            return out
        # P22 GROUNDED → P26 VALUE_MISMATCH: 5 行(位置と id)。P23 の時点で既に VALUE_MISMATCH
        g_vm = rows_of("GROUNDED", "VALUE_MISMATCH")
        self.assertEqual(g_vm, [(5, "N008"), (5, "N056"), (10, "N056"), (18, "N050"), (20, "N016")])
        for i, cid in g_vm:
            c = [x for x in claims[docs[i]] if x["id"] == cid][0]
            self.assertEqual(c["states"][1], "VALUE_MISMATCH")       # P23 で既に
        self.assertIn(u"**5 行**(新しい標本。`docs` の 0 起点の位置と claim id で 5・N008、5・N056、10・N056、18・N050、20・N016)", b)
        self.assertIn(u"原因は P23 の `pct_tolerance_from_decimals`(率の帯を書かれた桁から)。", b)
        self.assertIn("pct_tolerance_from_decimals=True", [l for l in base_text(VOCAB_REL).splitlines() if l.startswith("P23 = ")][0])
        # P22 UNVERIFIABLE(no_subject)→ P26 VALUE_MISMATCH: 4 行
        u_vm = rows_of("UNVERIFIABLE", "VALUE_MISMATCH")
        self.assertEqual(u_vm, [(3, "T018"), (9, "N042"), (26, "T076"), (26, "T092")])
        for i, cid in u_vm:
            c = [x for x in claims[docs[i]] if x["id"] == cid][0]
            self.assertEqual((c["reasons"][0], c["states"][2]), ("no_subject", "VALUE_MISMATCH"))      # P24 で VALUE_MISMATCH
        self.assertIn(u"**4 行**(3・T018、9・N042、26・T076、26・T092)。原因は P24 の資金の語彙(`vocab_2026_10_21`)。読んでいない(文が正しいかは未確認)。", b)
        # P26 だけ GROUNDED → UNVERIFIABLE: 2 行 direction_on_cause_item
        g_u = rows_of("GROUNDED", "UNVERIFIABLE")
        self.assertEqual(g_u, [(4, "T001"), (23, "T020")])
        for i, cid in g_u:
            c = [x for x in claims[docs[i]] if x["id"] == cid][0]
            self.assertEqual((c["states"][3], c["reasons"][4]), ("GROUNDED", "direction_on_cause_item"))
        self.assertIn(u"P26 だけ GROUNDED → UNVERIFIABLE(`direction_on_cause_item`)になる **2 行**(4・T001、23・T020)。", b)
        # K-3 の転び方: 74 は記録から(P26 だけの弱まった行で reason が rounded_diff_within_double_band)、59 は 52289c4 の commit の説明
        p25_keys = set((x["doc"], x["id"]) for x in self.fresh["C"]["P25"])
        extra = [x for x in self.fresh["C"]["P26"] if (x["doc"], x["id"]) not in p25_keys]
        self.assertEqual(len(extra), 75)
        self.assertEqual(sum(1 for x in extra if x["reason"] == "rounded_diff_within_double_band"), 74)
        msg = git("log", "-1", "--format=%B", BASE).stdout
        for s in (u"P26 だけの丸めの 74 行", u"1 小さい行 0・1 大きい行 74", u"文の数に合う fact が書類に無い 59 行", u"既定は P25", u"既定は P24"):
            self.assertIn(s, msg, s)
        self.assertIn(u"P26 だけの丸めの 74 行(名指した前期と当期の差 a−b が文の数より 1 単位大きい。192 件のうち 1 単位小さい行 0・1 単位大きい行 74 で、切り捨て表示の形)を「分からない」と読むと "
                      u"P26 は K-3 を満たさず、既定は P25 になる。", b)
        self.assertIn(u"文の数に合う fact が書類に無い 59 行(部門・区分・予想・合計)を「分からない」と読むと P26・P25 とも満たさず、既定は P24 になる。", b)
        self.assertIn(u"封と前例の語義ではどちらも採らない", b)
        self.assertIn(u"**判定は覆さない**が、この読みを人間が採るなら既定は変わる。", b)
        # 代価: 報告形の節と注入
        self.assertIn(u"報告形の節で 67 書類の「違う」は 1,410 → 433、「要確認」は 915 → 1,775。", b)
        d = self.fresh["D"]
        self.assertIn(u"止めのうち「違う」が %.1f%% → %.1f%%、「要確認」が %.1f%% → %.1f%%"
                      % (d["P22"][u"止めのうち違う"][u"率"], d["P26"][u"止めのうち違う"][u"率"], d["P22"][u"止めのうち要確認"][u"率"], d["P26"][u"止めのうち要確認"][u"率"]), b)
        t5_22, t5_26 = d["P22"][u"型別"]["T5_COINCIDENT"], d["P26"][u"型別"]["T5_COINCIDENT"]
        self.assertIn(u"値が偶然別の fact と一致する T5 は、P22 は %d 回とも「違う」、P26 は %d 回を「違う」・%d 回を「要確認」" % (t5_22[u"違う"], t5_26[u"違う"], t5_26[u"要確認"]), b)
        self.assertEqual((t5_22[u"違う"], t5_26[u"違う"], t5_26[u"要確認"]), (103, 11, 92))
        # 注入で通した 5 件: 5 つの profile で同じ一覧、全部 T2
        passed = [r for r in self.fresh[u"注入の行"] if r[u"結果"]["P22"] and r[u"結果"]["P22"][0] == "GROUNDED"]
        self.assertEqual(len(passed), 5)
        self.assertEqual(set(r[u"型"] for r in passed), set(["T2_UNIT"]))
        for r in passed:
            self.assertEqual(set(r[u"結果"][p][0] for p in PROFILE_COLS if r[u"結果"][p]), set(["GROUNDED"]))
        self.assertIn(u"**注入で通した 5 件は 5 つの profile で同じ一覧**(全部 T2 の単位の差し替え)で、**原因は調べていない**。", b)
        self.assertIn(u"**通した数は 5 のまま**", b)
        # 67 書類の P22 → 試作 19 の字(試作の数。記録に無い)
        self.assertIn(u"試作で 19(VALUE_MISMATCH 7・UNVERIFIABLE 12)。S-2 の幅。", b)
        for s in (u"30 書類は 1 つの母集団(封 `431f436` の 256 件)からの引き。注入は 4 型だけ。読みはエージェントで人間ではない。席は 1 回も呼んでいない。",
                  u"区分の取り違えの疑い・向きの語の残りなど、「違う」に残る正しい文の主因は P26 では直っていない(P26 の封 §3)。"):
            self.assertIn(s, b, s)
        self.assertEqual(self.fresh["環境"]["DEFAULT_PROFILE"], "P22")

    def test_12_the_records_the_seal_reads_are_not_moved_by_stage_2(self):
        """段 2 の便で動かさない記録は、作業木の file が 52289c4 の blob と同じ(封の数の出どころが動かない)。儀式の記録だけは段 2 で採り直す(S-4)ので入れない。"""
        for rel in UNMOVED_RECORDS:
            with io.open(os.path.join(ROOT, rel), "rb") as fh:
                work = fh.read()
            r = subprocess.run(["git", "show", "%s:./%s" % (BASE, rel)], cwd=ROOT, capture_output=True)
            self.assertEqual(r.returncode, 0, rel)
            self.assertEqual(hashlib.sha256(work).hexdigest(), hashlib.sha256(r.stdout).hexdigest(), u"**%s が 52289c4 から動いている**" % rel)
        self.assertNotIn(RITUAL_REL, UNMOVED_RECORDS)

    def test_13_s8_and_s9_counts_close(self):
        """S-8・S-9 の数は試作の実測の写し(記録に無い)なので、字の内訳の和と一覧の本数だけを縛る。"""
        b = sec(self.t, "## §2 ", "## §3")
        by_id = dict((re.match(r"\| \*\*S-(\d+)\*\*", l).group(1), l) for l in prediction_rows(b))
        m = re.search(r"赤 \*\*(\d+) 本\*\*\(\*\*(\d+) file\*\* = §4 \(a\) の (\d+) file \+ `test_xbrl_naming_fix_result.py`\)・`tests/adapters/xbrl` の赤 \*\*(\d+) 本\*\*\((\d+) file\)", by_id["8"])
        self.assertTrue(m, u"S-8 の書き方が変わった")
        meas, meas_files, a_files, ad, ad_files = [int(x) for x in m.groups()]
        self.assertEqual((meas, meas_files, a_files, ad, ad_files), (66, 24, 23, 15, 10))
        self.assertEqual(a_files + 1, meas_files)
        lo, hi = [int(x) for x in re.search(r"幅は合計 \*\*(\d+)〜(\d+)\*\*", by_id["8"]).groups()]
        self.assertTrue(lo <= meas + ad <= hi, (lo, hi, meas + ad))
        self.assertEqual((lo, hi), (78, 84))
        m9 = re.search(r"増えた赤は \*\*(\d+) 本\*\*\(新しい標本 (\d+)・報告形 (\d+)・報告形の直し (\d+)・期の縛り (\d+)・儀式 (\d+)\)", by_id["9"])
        self.assertTrue(m9, u"S-9 の書き方が変わった")
        tot, parts = int(m9.group(1)), [int(x) for x in m9.groups()[1:]]
        self.assertEqual(sum(parts), tot)
        self.assertEqual(tot, 6)
        f_block = sec(self.t, "## §4 ", "## §5")
        f_block = f_block[f_block.index(u"**(f) "):f_block.index(u"**(g) ")]
        self.assertIn(u"**(f) 重い走らせ直しだけで赤になる %d 本**" % tot, f_block)
        self.assertEqual(len(re.findall(r"`AUDIT_CORE_[A-Z_]+=1`", f_block)), 5)      # 5 つの環境変数(儀式は 2 本)
        self.assertIn(u"`RerunHeavyTest.test_4`・`test_6`", f_block)

    # ------------------------------------------------------------------ §4 pin の遷移の一覧
    def _paths_after(self, block, start, end):
        i = block.index(start)
        j = block.index(end, i + 1) if end else len(block)
        return set(re.findall(r"`(tests/[A-Za-z0-9_./-]+\.py)`", block[i:j]))

    @staticmethod
    def _grep_base(lit, pathspec):
        out = git("grep", "-l", "-F", lit, BASE, "--", pathspec).stdout.splitlines()
        return set(x[len(BASE) + 1:] for x in out)

    def test_16_pin_lists_equal_the_git_grep_at_the_base_commit(self):
        b = sec(self.t, "## §4 ", "## §5")
        a_set = self._paths_after(b, u"**(a) ", u"**(b) ")
        b_set = self._paths_after(b, u"**(b) ", u"**(c) ")
        c_set = self._paths_after(b, u"**(c) ", u"**(d) ")
        e_set = self._paths_after(b, u"**(e) ", u"**(f) ")
        self.assertEqual(a_set, self._grep_base("83025e9c0525d08b", "tests"), u"(a) の一覧が git grep と違う")
        self.assertEqual(b_set, self._grep_base("498993e29055472a", "tests"))
        self.assertEqual(c_set, self._grep_base("a97ecf7c44e60c45", "tests"))
        self.assertEqual(self._grep_base("a97ecf7c44e60c45", "."), c_set | set(["fixtures/frozen_bundle_sha.py"]))
        self.assertEqual(self._grep_base("498993e29055472a", "."), b_set)
        self.assertTrue(b_set <= a_set and c_set <= a_set)
        self.assertEqual((len(a_set), len(b_set), len(c_set)), (23, 5, 3))
        self.assertTrue(all(p.startswith("tests/measure/") for p in a_set))
        self.assertEqual(e_set, self._grep_base("DEFAULT_PROFILE", "tests/adapters/xbrl"))
        self.assertEqual(len(e_set), 10)
        for s in (u"**(a) `adapters/xbrl/vocabulary.py` の sha16 `83025e9c0525d08b` を字で留める門 23 本**", u"試作ではこの 23 本が全部赤になった",
                  u"**(b) 束ねた指紋 `adapter_xbrl_py_sha256` の `498993e29055472a…` を字で留める門 5 本**",
                  u"**(c) frozen_bundle の世代 `a97ecf7c44e60c45…` を字で留める所**", u"`fixtures/frozen_bundle_sha.py` の世代の一覧に新しい世代を足す。",
                  u"**(d) 既定の字だけで赤になる `tests/measure`**: `tests/measure/test_xbrl_naming_fix_result.py`", u"(a) と合わせて試作の赤の 24 file。",
                  u"**(f) 重い走らせ直しだけで赤になる 6 本**", u"**(g) 軽い門で赤になる「既定を前提に走らせ直す」所**", u"**(h) 新しい門の名前**",
                  u"**(i) axis3** の `LATER_ENGINE_COMMITS` に段 2 の commit を宣言するのは次の便"):
            self.assertIn(s, b, s)
        # (d) は sha の字を持たず、既定の字を持つ。(a) の外
        nf = "tests/measure/test_xbrl_naming_fix_result.py"
        self.assertNotIn(nf, a_set)
        self.assertIn("DEFAULT_PROFILE", base_text(nf))
        self.assertNotIn("83025e9c0525d08b", base_text(nf))
        # (f)(g) が名指す file は実在する
        for rel in ("test_xbrl_fresh_result", "test_xbrl_customer_report_result", "test_xbrl_customer_report_fix_result", "test_xbrl_period_bind_result", "test_xbrl_ritual_result", "test_xbrl_point_prior_result"):
            self.assertIn(rel + ".py", b, rel)
            self.assertEqual(git("cat-file", "-e", "%s:./tests/measure/%s.py" % (BASE, rel)).returncode, 0, rel)
        # 重い走らせ直しの環境変数(実物)
        for var in ("AUDIT_CORE_FRESH", "AUDIT_CORE_CUSTOMER_REPORT", "AUDIT_CORE_CUSTOMER_REPORT_FIX", "AUDIT_CORE_PERIOD_BIND", "AUDIT_CORE_RITUAL"):
            self.assertIn("`%s=1`" % var, b, var)
            self.assertTrue(self._grep_base(var, "tests/measure"), var)
        # 既存の門が行頭の名前を数えること(新しい門の名前の制約)の根拠
        self.assertRegex(base_text("tests/measure/test_xbrl_lastbranch_seal.py"), r"(?m)^ENGINE_LATER = \{")
        self.assertIn("PIN_DEF", base_text("tests/measure/test_xbrl_p26_seal.py"))
        # 前例 d0b544c: 同じ型の遷移を 10 門で宣言した
        self.assertIn(u"vocabulary の sha16 25a3c0992e10daaa を 10 門で宣言", git("log", "-1", "--format=%B", "d0b544c").stdout)

    def test_17_live_pin_set_only_grows_by_the_named_new_gates(self):
        """作業木で vocabulary.py の旧 sha16 を字で持つ tests/measure の file は、52289c4 の 23 本 + この門 + 結果の門だけ(新しい門が黙って engine の留めを増やしたら赤)。"""
        base = self._grep_base("83025e9c0525d08b", "tests")
        live = set()
        for p in glob.glob(os.path.join(ROOT, "tests", "**", "*.py"), recursive=True):
            if "83025e9c0525d08b" in text(p):
                live.add(os.path.relpath(p, ROOT))
        self.assertTrue(base <= live, sorted(base - live))
        self.assertTrue(live - base <= set([GATE_REL, "tests/measure/test_xbrl_default_p26_result.py"]), sorted(live - base))

    # ------------------------------------------------------------------ §5
    def test_18_file_list_and_order(self):
        b = sec(self.t, "## §5 ")
        first = b[:b.index(u"\n順序:")]
        self.assertTrue(first.startswith(u"\n## §5 触る file と順序"))
        toks = [u"`adapters/xbrl/vocabulary.py`", u"`measure/ritual_2026-10-20.py`", u"`fixtures/xbrl/ritual_2026-10-20.json`", u"`fixtures/xbrl/ritual_2026-10-20_p22.json`",
                u"`README.md`", u"`README.en.md`", u"`docs/XBRL_RITUAL_RESULT_2026-10-20.md`", u"`measure/xbrl_default_p26_2026-10-23.py`",
                u"`fixtures/xbrl/default_p26_2026-10-23.json`", u"`docs/XBRL_DEFAULT_P26_RESULT_2026-10-23.md`", u"`tests/measure/test_xbrl_default_p26_result.py`",
                u"`measure/suite_coverage_2026-10-16.py --write`", u"`fixtures/frozen_bundle_sha.py`"]
        pos = []
        for tk in toks:
            self.assertGreaterEqual(first.count(tk), 1, tk)
            pos.append(first.index(tk))
        self.assertEqual(pos, sorted(pos), u"file 一覧の順が変わった")
        self.assertIn(u"→ 既定の字を見る試験と pin の遷移(§4)→", first)
        order = b[b.index(u"\n順序:"):]
        self.assertIn(u"順序: 人間の方針(2026-10-21 朝)→ 新しい標本の判定の commit(`52289c4`)→ **この封 + 封の門を commit** → 段 2 実装(別席)→ 凍結 → 独立監査 → commit → "
                      u"axis3 の `LATER_ENGINE_COMMITS` に段 2 の commit を宣言(次の便。", order)
        self.assertEqual(len(STAGE2_NEW_FILES), 5)
        for rel in STAGE2_NEW_FILES:
            self.assertIn("`%s`" % rel, first, rel)
        # 実在する既存 file
        for rel in ("measure/ritual_2026-10-20.py", "README.md", "README.en.md", "fixtures/frozen_bundle_sha.py", "measure/suite_coverage_2026-10-16.py"):
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)


class EngineAtBaseTest(unittest.TestCase):
    """封の commit 時点(52289c4 の木)の engine を字で留め、段 2 の後は「宣言された遷移」の値だけを受け入れる(docstring)。"""

    def test_19_adapters_file_set_and_the_fifteen_untouched_files(self):
        py = sorted(f for f in os.listdir(os.path.join(ROOT, "adapters", "xbrl")) if f.endswith(".py"))
        self.assertEqual(["adapters/xbrl/" + f for f in py], sorted(ADAPTERS_AT_BASE), u"adapters/xbrl の file の集合が変わった")
        self.assertEqual(len(ADAPTERS_AT_BASE), 16)
        for rel, want in sorted(ADAPTERS_AT_BASE.items()):
            if rel == VOCAB_REL:
                continue
            got = sha16(rel)
            if got != want and rel in P27_LATER:
                later, seal_rel = P27_LATER[rel]
                self.assertTrue(git("log", "--diff-filter=A", "--format=%H", "--", seal_rel).stdout.split(), u"**%s が動いているのに、遷移を宣言した封が履歴に無い**" % rel)
                self.assertEqual(got, later, u"**%s が、宣言された遷移の値とも違う**" % rel)
                continue
            self.assertEqual(got, want, u"**%s が動いている(この封は触らない。vocabulary.py の 1 行だけ)**" % rel)
        # 52289c4 の木の sha16 と、字で留めた値が同じ(留めの取り違えを避ける)
        for rel, want in sorted(ADAPTERS_AT_BASE.items()):
            self.assertEqual(hashlib.sha256(base_text(rel).encode("utf-8")).hexdigest()[:16], want, rel)

    def test_20_vocabulary_sha_and_default_are_the_ones_at_the_seal_or_a_declared_transition(self):
        got = sha16(VOCAB_REL)
        from adapters.xbrl import vocabulary as V
        if got != VOCAB_SHA16_AT_BASE:
            self.assertIn("vocabulary_sha16", DECLARED, u"**vocabulary.py が動いているのに、遷移が宣言されていない(段 2 の commit で DECLARED に足す)**")
            later, seal_rel = DECLARED["vocabulary_sha16"]
            self.assertTrue(git("log", "--diff-filter=A", "--format=%H", "--", seal_rel).stdout.split(), u"遷移を宣言した封が履歴に無い")
            self.assertEqual(got, later, u"**vocabulary.py が、宣言された遷移の値とも違う**")
            self.assertEqual(V.DEFAULT_PROFILE, "P27")      # 2026-10-28: 既定を P26 -> P27 に切り替える 段 2 の後の既定(封の commit 時点は P22。段 2 の後 P26 だった)
            return
        # 実装前: 既定はまだ P22、P26 は登録済み(段 1)
        self.assertEqual(V.DEFAULT_PROFILE, "P22")
        self.assertIn("P26", V.PROFILES)
        self.assertEqual(len(re.findall(r'(?m)^DEFAULT_PROFILE = "P22"$', text(os.path.join(ROOT, VOCAB_REL)))), 1)

    def test_21_fingerprint_and_frozen_bundle_are_the_ones_at_the_seal_or_a_declared_transition(self):
        from adapters.xbrl import verify_document as VD
        fp = VD.engine_fingerprint()
        key = "adapter_xbrl_py_sha256"
        if fp[key] != FINGERPRINT_AT_BASE[key]:
            self.assertIn(key, DECLARED, u"**束ねた指紋が動いているのに、遷移が宣言されていない**")
            later, seal_rel = DECLARED[key]
            self.assertTrue(git("log", "--diff-filter=A", "--format=%H", "--", seal_rel).stdout.split())
            self.assertEqual(fp[key], later)
        for k in ("adapter_xbrl_py_files", "core_py_sha256", "core_py_files"):
            self.assertEqual(fp[k], FINGERPRINT_AT_BASE[k], k)
        # 指紋が動くのは vocabulary.py が動いたときだけ
        if fp[key] != FINGERPRINT_AT_BASE[key]:
            self.assertNotEqual(sha16(VOCAB_REL), VOCAB_SHA16_AT_BASE)
        src = text(os.path.join(ROOT, "fixtures", "frozen_bundle_sha.py"))
        count = int(re.search(r"(?m)^FROZEN_COUNT = (\d+)", src).group(1))
        gens = re.findall(r'\("([0-9a-f]{64})",\n', src)
        self.assertEqual(count, FROZEN_COUNT_AT_BASE)
        self.assertIn(FROZEN_AT_BASE, gens, u"封の commit 時点の世代は消さない")
        r = subprocess.run([sys.executable, os.path.join(ROOT, "fixtures", "frozen_bundle_sha.py")], cwd=REPO, capture_output=True, text=True)
        m = re.search(r"対象 (\d+) 本 @ ", r.stdout)
        self.assertIsNotNone(m, r.stdout)
        self.assertEqual(int(m.group(1)), FROZEN_COUNT_AT_BASE)
        if "frozen_bundle" in DECLARED:
            later, seal_rel = DECLARED["frozen_bundle"]
            self.assertTrue(git("log", "--diff-filter=A", "--format=%H", "--", seal_rel).stdout.split())
            self.assertEqual(r.returncode, 0, r.stdout)
            self.assertIn(later, r.stdout)
            self.assertEqual(gens[-1], later)
        else:
            self.assertEqual(r.returncode, 0, u"**frozen_bundle が動いている(段 2 の commit で DECLARED に遷移を宣言する)**\n" + r.stdout)
            self.assertEqual(gens[-1], FROZEN_AT_BASE)

    def test_22_the_stage_2_files_do_not_exist_yet(self):
        """封が実装より先であること。vocabulary.py が封の commit 時点のうちは、段 2 の新しい file が作業木にも履歴にも無い。段 2 の commit で DECLARED を足したら skip に切り替わる。"""
        if DECLARED:
            self.skipTest(u"段 2 の後(DECLARED が宣言されている)。順序は test_23")
        for rel in STAGE2_NEW_FILES:
            self.assertFalse(os.path.exists(os.path.join(ROOT, rel)), u"封より先に在る: " + rel)
            self.assertEqual(git("log", "--format=%H", "--", rel).stdout.strip(), "", u"封より先に履歴に現れた: " + rel)


class OrderTest(unittest.TestCase):
    @staticmethod
    def _added(rel):
        shas = [s for s in git("log", "--diff-filter=A", "--format=%H", "--", rel).stdout.split() if s]
        return shas[-1] if shas else None

    def test_23_the_seal_follows_the_base_commit_and_precedes_every_later_file(self):
        self.assertEqual(git("cat-file", "-e", BASE + "^{commit}").returncode, 0)
        self.assertEqual(git("merge-base", "--is-ancestor", BASE, "HEAD").returncode, 0, u"判定の commit 52289c4 が HEAD の祖先に無い")
        tracked = git("ls-files", "--error-unmatch", SEAL_REL).returncode == 0
        if not tracked:
            for rel in STAGE2_NEW_FILES:
                self.assertIsNone(self._added(rel), u"封より先に履歴に現れた: " + rel)
            self.assertEqual(git("log", "--format=%H", BASE + "..HEAD", "--", VOCAB_REL).stdout.strip(), "", u"封より先に vocabulary.py を直した")
            self.skipTest(u"封がまだ commit されていない(後の file が履歴に無いことだけ確かめた)")
        seal = self._added(SEAL_REL)
        self.assertNotEqual(seal, BASE)
        self.assertEqual(git("merge-base", "--is-ancestor", BASE, seal).returncode, 0, u"封が判定の commit 52289c4 より前にある")
        for rel in STAGE2_NEW_FILES:
            other = self._added(rel)
            if other is None:
                continue
            self.assertNotEqual(seal, other, rel)
            self.assertTrue(git("merge-base", "--is-ancestor", seal, other).returncode == 0, rel)
        for c in git("log", "--format=%H", BASE + "..HEAD", "--", VOCAB_REL).stdout.split():
            if c == seal:
                continue
            self.assertTrue(git("merge-base", "--is-ancestor", seal, c).returncode == 0, u"封より先に vocabulary.py を直した: %s" % c)


if __name__ == "__main__":
    unittest.main()
