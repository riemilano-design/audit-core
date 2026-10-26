# -*- coding: utf-8 -*-
"""凍結対象(判定の核と接続部分の 22 ファイル)の束ねた sha を測る。Core のコードではない。

セッション A の 2026-10-08 の申し送り: 「凍結対象は、判定の核と接続部分のコミット済み
22 ファイル(束ねた sha 950ebc91…0cda)。0d54c9a と 9226a3d で同一」。
**2026-10-09、本線 5b0f356(案ア)により 490888d4… へ移行した**(本線の承認済み)。
基準は世代で伸びる ― ``FROZEN_BUNDLE_GENERATIONS`` を見ること。古い値は消さない。
**束ね方はこの script で再現できる**(当て直して一致を確認済み):

    対象 = git ls-files audit-core/core audit-core/adapters  (= 22 本)
    各ファイルについて "<内容の sha256>  <repo 相対パス>\\n" を作り、
    パスの昇順で連結し、その全体の sha256 を取る。

通信はしない。ファイルを書き換えない。費用 0 円。

    python3 audit-core/fixtures/frozen_bundle_sha.py                 # 作業ツリーの現状
    python3 audit-core/fixtures/frozen_bundle_sha.py --rev 9226a3d   # そのコミットの中身
    python3 audit-core/fixtures/frozen_bundle_sha.py --rev 0d54c9a --expect 950ebc91f2cce10f9a22f9e3defe769c3396c264ab1da8ab8c1d99aee0a78cda

``--expect`` を渡すと、一致しなければ終了コード 1 と、**どのファイルが違うか**を印字する
(束ねた sha だけでは「変わった」しか分からないので、個別の sha も必ず出す)。
"""

import argparse
import hashlib
import os
import subprocess
import sys

FROZEN_PATHS = ("audit-core/core", "audit-core/adapters")
# 2026-10-19: 22 → 36。**22 は 2026-10-09 の数で、その後 shogi(2026-10-06 の adapters/shogi 7 本)と
# kokkai(2026-10-14、adapters/kokkai 9 本)が足されても誰もこの定数を直していなかった**(封
# docs/XBRL_HOLDS_PRODUCT_PATH_SEAL_2026-10-19.md の予測 F-10「22 → 24」は、この取りこぼしで外れた)。
# 2026-10-19 に holds.py・verify_external.py を足して 36 本。
# 2026-10-21 に report_customer.py(顧客向けの日本語の報告形。封 docs/XBRL_CUSTOMER_REPORT_SEAL_2026-10-21.md)を足して 37 本。
FROZEN_COUNT = 37

# 凍結の基準は**世代で伸びる**。古い値は消さない ― その日の記録はその値で正しい。
# (本線の共通規則、2026-10-09: 「封じた値は上書きしない。訂正は日付つきの追記で」)
#
#   (束ねた sha, いつ・何によって・誰の承認で動いたか)
#
# 「不一致」と「世代が 1 つ古い」は別のことなので、下の main() は言い分ける ―
# 前者は**ずれ**かもしれないが、後者は**宣言された遷移**である。
FROZEN_BUNDLE_GENERATIONS = (
    ("950ebc91f2cce10f9a22f9e3defe769c3396c264ab1da8ab8c1d99aee0a78cda",
     "2026-10-08 セッション A が凍結(0d54c9a と 9226a3d で同一)"),
    ("490888d46d034ca9eaae8e4b4d01f494919abf21a8b057e87c835d25256d7116",
     "2026-10-09 本線 5b0f356(案ア ― 主語の無い数の主張を束縛しない)により移行。"
     "人間の決定 2026-10-08 + 独立監査 GO。本線が独立に 22 本を測って一致。"
     "基準の更新は本線(司令塔)が 2026-10-09 に承認"),
    ("2617c963207541f69a3f0087916d8c96d483a5dd6ad0db84b143c91601a2d088",
     "2026-10-19 feature/audit-core-final-eval-8: (d)・P・U を製品の経路へ(adapters/xbrl/holds.py・"
     "verify_external.py)、instance.py に枠の軸 axes を足した。封 docs/XBRL_HOLDS_PRODUCT_PATH_SEAL_2026-10-19.md。"
     "対象 36 本(22 本は 2026-10-09 の数。shogi・kokkai の adapter が足されたのに定数が直っていなかった)"),
    ("a21202f81a3bc0bc4af64d2b1c0d982185ba9efcb3317b070d4a055ecc5edca3",
     "2026-10-19 feature/audit-core-final-eval-8(段 2): PP(期間の対)を製品の経路へ。"
     "adapters/xbrl/holds.py に prior_siblings・pp_pick、verify_external.py に PP の入口分岐"
     "(derived_pointers・direction_checked・period_pair 引数)を足した。instance.py・core/py は 0 行。"
     "封 docs/XBRL_PERIOD_PAIR_SEAL_2026-10-19.md(commit 790a5c5 + 追記 1 78a04f5)。対象 36 本(本数は変わらない ―"
     "ファイルを増やしていない)。独立監査 GO の前に測った値(commit 前)"),
    ("4e5bc8a8fe7667914c16d7765a6faa0a78cabcf617f29bfb55c65088dc158613",
     "2026-10-20 feature/audit-core-final-eval-8(名指しの直し P21 の段 1): recipes.py の _direct_value_claim の最後の枝に"
     "旗 last_branch_cues の後ろの 3 つの直し(F1′・F2′・F3b)を足し(+30 行・既存の行は 1 つも変えない。§1b の止めの後ろ)、vocabulary.py に旗 1 つ・"
     "P21・PROFILES の登録を足した。DEFAULT_PROFILE は P20 のまま。core/py・instance.py・extract.py は 0 行。"
     "封 docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md(commit 5c267df)。対象 36 本(本数は変わらない)。"
     "独立監査 GO の前に測った値(commit 前)"),
    ("bb55b75285ec33603985c5cc95dd2b391986e1f86c338aed4a7d54c4e63e69f0",
     "2026-10-20 feature/audit-core-final-eval-8(名指しの直し P21 の段 2): vocabulary.py の DEFAULT_PROFILE を P20 -> P21 にし、"
     "決定の注記に日付と根拠を足した(vocabulary.py だけ。他の file は 0 行)。人間の指示(2026-10-20)「アダプターの問題か。"
     "とにかく精度を改善して。何してもいいから」の委任のもと、封 docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md の段 2 の条件"
     "(N-4・N-5)が当たったとき。対象 36 本(本数は変わらない)。独立監査 GO の前に測った値(commit 前)"),
    ("b71e69601d8c5b4541958072f2b55197125f7d132c1d4ec14771815c9d9e11f6",
     "2026-10-20 feature/audit-core-final-eval-8(期を縛る P22 の段 1): recipes.py の _direct_value_claim の最初の枝に"
     "旗 period_bind の塊(+4 行・既存の行は 1 つも変えない。C2 の並べ替えの後ろ・if hits and not (is_diff and subj) の前。条件に subj and を含む = 主語なしは案アのまま。独立監査の指摘で足した)を足し、"
     "vocabulary.py に旗 1 つ・P22(= P21 + period_bind)・PROFILES の登録を足した(+4 行・-1 行)。DEFAULT_PROFILE は P21 のまま。"
     "core/py・instance.py・extract.py は 0 行。人間の承認 2026-10-20「君に任せる」、"
     "封 docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md(commit 4953a4f)。対象 36 本(本数は変わらない)。"
     "独立監査 GO の前に測った値(commit 前)"),
    ("98862539ac6e61f2fdaeeb7e3965bbfea40064bd8abfffa77662b6a98cf4e950",
     "2026-10-20 feature/audit-core-final-eval-8(期を縛る P22 の段 2): vocabulary.py の DEFAULT_PROFILE を P21 -> P22 にし、"
     "決定の注記に日付と根拠を足した(vocabulary.py だけ。recipes.py・他の file は 0 行)。人間の決定 2026-10-20「任せる」"
     "(段 1 3320c8c の結果と客の席の回し直しを見てから)、封 docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md の段 2(E-8)。"
     "対象 36 本(本数は変わらない)。独立監査 GO の前に測った値(commit 前)"),
    ("e308c7f78ee225e2f65d13f07885630969b5e4d86180a2748038036cf3552f04",
     "2026-10-21 feature/audit-core-final-eval-8(丸めの帯 P23 の段 1): vocabulary.py に旗 truncate_abs_band(書類の丸め方が切り捨てと判定されたとき、"
     "照合の帯だけを絶対値で片側にする。decide_rounding の判定の軸は変えない)・P23(= P22 + 率の旗 pct_tolerance_from_decimals + truncate_abs_band)・"
     "PROFILES の登録を足し(+7 行・-1 行)、recipes.py に _mag_trunc(profile, rounding) を足して 3 か所の呼び出しを置き換えた(旗の受け渡しだけ)。"
     "comparators.py・core/py・instance.py・extract.py は 0 行(切り捨ての帯の絶対値の枝は P19 で入っており、検証時の照合へは params[\"magnitude_truncate\"] で既に届く)。"
     "DEFAULT_PROFILE は P22 のまま。人間の事前承認 2026-10-21、封 docs/XBRL_ROUNDING_SEAL_2026-10-21.md(commit 5008985)。"
     "対象 36 本(本数は変わらない)。独立監査 GO の前に測った値(commit 前)"),
    ("a3eef997e567dd5cb41c2a0066c8e7997cbfbf3e90e8b506919183127e2a1284",
     "2026-10-21 feature/audit-core-final-eval-8(語彙の登録と枠の取り直し P24 の段 1): vocabulary.py に旗 vocab_2026_10_21・frame_rebind・"
     "資金の主語の句の表 CF_FUND_SUBJECTS_2026_10_21・P24(= P23 + 旗 2 つ)・PROFILES の登録を足し(+27 行・-1 行)、recipes.py に旗 2 つの塊を足し"
     "(+224 行・-0 行。既存の行は 1 つも書き換えない。ポイントの前期の語・前期の手がかり語・資金の主語の句・CF 合計の符号・枠の取り直しの 5 か所)、"
     "registry_setup.py に理由 other_frame を足した(+2 行)。comparators.py・core/py・instance.py・extract.py は 0 行。"
     "DEFAULT_PROFILE は P22 のまま。人間の事前承認 2026-10-21、封 docs/XBRL_VOCAB_SEAL_2026-10-21.md(commit 08987d0)。"
     "対象 36 本(本数は変わらない)。独立監査 GO の前に測った値(commit 前)"),
    ("8ffdc9177cdc4be7c059e5bd0a6f6e5b8466215918077591eb64371b7c69304a",
     "2026-10-21 feature/audit-core-final-eval-8(最後の枝 P25 の段 1): vocabulary.py に旗 last_branch_names_only_if_evidence・P25(= P24 + 旗 1 つ)・"
     "PROFILES の登録を足し(+7 行・-0 行)、recipes.py に最後の枝の証拠の判定の塊を足し(+72 行・-0 行。既存の行は 1 つも書き換えない。"
     "証拠 (i) 同じ要素・同じ枠の別の期・(ii) 桁の打ち間違い・(iii) 桁・単位の取り違え。無ければ POINTER_NOT_FOUND no_same_value)、"
     "registry_setup.py に理由 no_same_value を足した(+2 行)。comparators.py・core/py・instance.py・extract.py は 0 行。"
     "DEFAULT_PROFILE は P22 のまま。人間の事前承認 2026-10-21、封 docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md(commit 80ca08d)。"
     "対象 36 本(本数は変わらない)。独立監査 GO の前に測った値(commit 前)"),
    ("66f906c89205f0ef361e13fe051dbdeaed75a032e0d60ca832f6d605166f3b36",
     "2026-10-21 feature/audit-core-final-eval-8(顧客向けの日本語の報告形): 新しい module adapters/xbrl/report_customer.py を足した(既存の file は 1 字も触らない。"
     "report.py・verify_document.py・vocabulary.py・recipes.py・registry_setup.py・comparators.py・core/py は 0 行)。"
     "人間の事前承認 2026-10-21、封 docs/XBRL_CUSTOMER_REPORT_SEAL_2026-10-21.md(commit 6b724ad)。"
     "対象 36 本 → 37 本(FROZEN_COUNT 36 → 37)。独立監査 GO の前に測った値(commit 前。新しい file は git add 済みの状態で測った)"),
    ("5c4da2e2ff3f30b7dcb6ebcbc84a5c68b074e8dc495f2d260551d7e10a4ce66c",
     "2026-10-21 feature/audit-core-final-eval-8(顧客向けの報告形の直し ― 単位・桁・符号・英字・但し書き・指紋・表題・抜粋): 既存の module adapters/xbrl/report_customer.py の中身だけを直した"
     "(判定と節の割り当ては変えない。report.py・verify_document.py・vocabulary.py・recipes.py・registry_setup.py・comparators.py・core/py は 0 行)。"
     "人間の事前承認 2026-10-21 朝「報告形の問題はきちんと解決して」「あとは全て任せる」、封 docs/XBRL_CUSTOMER_REPORT_FIX_SEAL_2026-10-21.md(commit 9dfb608)。"
     "対象 37 本のまま(FROZEN_COUNT 37)。独立監査 GO の前に測った値(commit 前)"),
    ("a97ecf7c44e60c45bf6e6c23439c59955aad8bddf26b1174ee1e0ebabfd59c7c",
     "2026-10-22 feature/audit-core-final-eval-8(「違う」に出る正しい文の主因を減らす P26 の段 1): vocabulary.py に旗 5 つ(concept_gate・last_branch_digit_needs_size・"
     "rounded_diff_hold・cause_item_direction・numbers_2026_10_21)・P26(= P25 + 旗 5 つ)・PROFILES の登録を足し(+17 行・-0 行)、recipes.py に G1〜G5 の塊を足し"
     "(+251 行・-1 行。既存の行の書き換えは数の読み取りの for 文 1 行だけ)、extract.py に新しい関数 iter_numbers_2026_10_21 を足し(+42 行・-0 行。iter_numbers の字は変えない)、"
     "registry_setup.py に理由 3 つを足し(+6 行)、report_customer.py の理由の表に 3 行を足した(+7 行・-2 行。判定と節の割り当ては変えない)。"
     "comparators.py・report.py・verify_document.py・core/py は 0 行。DEFAULT_PROFILE は P22 のまま。"
     "人間の事前承認 2026-10-21、封 docs/XBRL_P26_SEAL_2026-10-21.md(commit a8d8099)。"
     "対象 37 本のまま(FROZEN_COUNT 37)。独立監査 GO の前に測った値(commit 前)"),
    ("26b5270646f2d8d8fcb7ca829f5f36066f9e2e9a1c3d1f0e4cdde1822e5d6fb6",
     "2026-10-23 feature/audit-core-final-eval-8(既定を P22 -> P26 に切り替える 段 2): vocabulary.py の DEFAULT_PROFILE を P22 -> P26 にし、"
     "決定の注記に日付と根拠を足した(vocabulary.py だけ。+4 行・-1 行。recipes.py・extract.py・registry_setup.py・report_customer.py・comparators.py・core/py ほか他の file は 0 行)。"
     "判定は封 docs/XBRL_FRESH_SAMPLE_SEAL_2026-10-21.md §3(commit 14cdd21)の基準を記録の数から機械で求めた結果(commit 52289c4)で P26。"
     "人間の方針 2026-10-21「あとは全て任せる」・engine の事前承認 2026-10-21、封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md(commit 6a78b42)。"
     "対象 37 本のまま(FROZEN_COUNT 37)。独立監査 GO の前に測った値(commit 前)"),
)

# 字で留めるのは**いまの世代**。--expect を値なしで渡したときの既定。
FROZEN_BUNDLE_SHA = FROZEN_BUNDLE_GENERATIONS[-1][0]

# **この枝そのものの既知の値。**
#
# 上の世代は**本線の**保護面の値である。作業用の枝は保護面を**意図して**変えて
# いるので、--expect を回すと毎回「不一致」が出る。それを放置すると
# **警報に慣れてしまい、本当のずれを読み飛ばす**(2026-10-09 に 1 回、
# 宣言された遷移を「凍結の束が動いた」と誤って書いた)。
#
# だから枝の値も名前つきで持つ。意味が逆であることに注意 ―
# 本線の値は「**変わっていないこと**」を確かめる値、
# 枝の値は「**意図した変更のぶんだけ変わっていること**」を確かめる値。
KNOWN_BRANCH_BUNDLES = {
    "5873ac7803adfa9de22195943b552e5f9d829611e1404f247a2397e629734f3d":
        "feature/audit-core-xbrl-fix5 ― 主語の規則の直し(S1〜S4)と A1 の実装を"
        "含む。本線 490888d4… から意図して分かれている。合流は truncate の封と"
        "監査の後に rebase 1 回(本線の席と合意、2026-10-09)",
}


def _git(args):
    out = subprocess.run(["git"] + args, capture_output=True)
    if out.returncode != 0:
        raise SystemExit("git %s failed: %s" % (" ".join(args), out.stderr.decode("utf-8", "replace")))
    return out.stdout


def frozen_files(rev=None):
    args = ["ls-files"]
    if rev:
        args += ["--with-tree", rev]
    args += list(FROZEN_PATHS)
    names = _git(args).decode("utf-8").split()
    return sorted(names)


def file_sha(path, rev=None):
    if rev:
        return hashlib.sha256(_git(["show", "%s:%s" % (rev, path)])).hexdigest()
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def bundle(rev=None):
    files = frozen_files(rev)
    rows = [(f, file_sha(f, rev)) for f in files]
    text = "".join("%s  %s\n" % (sha, f) for f, sha in rows)
    return hashlib.sha256(text.encode("utf-8")).hexdigest(), rows


def _dirty_count():
    """凍結対象のうち**未コミット**のファイル数。0 でなければ測った値は作業中のもの。"""

    try:
        out = _git(["status", "--porcelain", "--"] + list(FROZEN_PATHS))
    except SystemExit:
        return -1
    return len([l for l in out.decode("utf-8", "replace").splitlines() if l.strip()])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rev", default=None, help="このコミットの中身を測る(省略すると作業ツリーの現状)")
    ap.add_argument("--expect", nargs="?", const=FROZEN_BUNDLE_SHA, default=None,
                    help="期待する束ねた sha。値を省くと字で留めた凍結の値を使う")
    ap.add_argument("--verbose", action="store_true", help="22 本の個別の sha も印字する")
    a = ap.parse_args(argv)

    sha, rows = bundle(a.rev)
    where = a.rev or "(作業ツリー)"
    print("対象 %d 本 @ %s" % (len(rows), where))
    if len(rows) != FROZEN_COUNT:
        # **本数が違うときは束ねた sha を印字しない。**
        #
        # 2026-10-09 に実測した穴: ``audit-core/`` の中から回すと
        # ``git ls-files audit-core/core/py audit-core/adapters`` が **0 本**を返し、
        # それでも「束ねた sha: e3b0c442…」(= 空文字列の sha256)を印字していた。
        # **0 本の測定の sha は、記録に写せる形で画面に出てはいけない** ―
        # 「保護面が変わった」と読める値が、ただの cwd の誤りから生まれる。
        # (本線の席も同じ型を踏みかけた。あちらは相対の道で ``shasum`` が
        #  各行に道を印字するため、中身が同じでも別の値になる形だった。)
        print("**止まる**: 本数が %d 本で、凍結時の %d 本と違う。束ねた sha は印字しない。"
              % (len(rows), FROZEN_COUNT))
        if not rows:
            print("  0 本なら、ほぼ cwd の誤り ― **repo の根から回すこと**"
                  "(この道具は repo 相対の道で git に問うので、"
                  "audit-core/ の中から回すと 0 本になる)。")
        print("  いまの cwd: %s" % os.getcwd())
        return 2
    if a.verbose:
        for f, s in rows:
            print("  %s  %s" % (s, f))
    # **sha を単独で印字しない。**(本線の席の形、2026-10-09)
    # 「sha が出たから測れた」と読める行を作らない ― 1 行を記録に写したときに
    # **何を何本測った値なのかが一緒に付いてくる**ようにする。
    # こちらは本数が合わなければ上で rc=2 で止めるが、**止まらなかったときに
    # 本数を読む習慣**は、同じ行に並んでいないと身につかない。
    print("束ねた sha: %s  (対象 %d 本 / %s / 未コミット %d 件)"
          % (sha, len(rows), where, _dirty_count()))
    if a.expect is None:
        return 0
    if sha == a.expect:
        print("一致: 凍結対象は変わっていない")
        return 0
    for i, (gen_sha, why) in enumerate(FROZEN_BUNDLE_GENERATIONS[:-1]):
        if sha == gen_sha:
            print("**世代が %d つ古い**(ずれではない): この束は第 %d 世代 ― %s"
                  % (len(FROZEN_BUNDLE_GENERATIONS) - 1 - i, i + 1, why))
            print("いまの世代は %s ― %s"
                  % (FROZEN_BUNDLE_GENERATIONS[-1][0], FROZEN_BUNDLE_GENERATIONS[-1][1]))
            print("(測った対象が古いコミット・古い枝なら、これが正しい。"
                  "本線の現状を測ったのにこれが出たなら、そのときは調べる)")
            return 1
    if sha in KNOWN_BRANCH_BUNDLES:
        print("**この枝の既知の値と一致**(本線の基準とは意図して違う): %s"
              % KNOWN_BRANCH_BUNDLES[sha])
        print("  本線のいまの世代は %s" % FROZEN_BUNDLE_GENERATIONS[-1][0])
        print("  (枝の値は『変わっていないこと』ではなく"
              "『意図した変更のぶんだけ変わっていること』を確かめる値)")
        return 0
    print("不一致: 期待 %s" % a.expect)
    print("(既知の世代にも、この枝の既知の値にも当たらない。"
          "記録と突き合わせる前に、どのファイルが違うかを下で見る)")
    base = os.environ.get("FROZEN_BASE_REV", "0d54c9a")
    try:
        _, base_rows = bundle(base)
    except SystemExit:
        print("(個別の照合先 %s が読めないので、どのファイルが違うかは出せない)" % base)
        return 1
    bysha = dict(base_rows)
    print("個別の差(照合先 %s):" % base)
    for f, s in rows:
        if bysha.get(f) != s:
            print("  変わった: %s" % f)
    for f, _s in base_rows:
        if f not in dict(rows):
            print("  消えた  : %s" % f)
    return 1


if __name__ == "__main__":
    sys.exit(main())
