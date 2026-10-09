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
FROZEN_COUNT = 22

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
)

# 字で留めるのは**いまの世代**。--expect を値なしで渡したときの既定。
FROZEN_BUNDLE_SHA = FROZEN_BUNDLE_GENERATIONS[-1][0]


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
    print("束ねた sha: %s" % sha)
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
    print("不一致: 期待 %s" % a.expect)
    print("(既知の世代のどれにも当たらない。記録と突き合わせる前に、"
          "どのファイルが違うかを下で見る)")
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
