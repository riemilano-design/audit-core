# -*- coding: utf-8 -*-
# STEP DELIVER-1(docs/STEP_DELIVER1_PLAN_2026-09-25.md §3 の 6)。納品フォルダの伏せ字・個人情報の検査。
#
# 使い方: python3 -X utf8 check_delivery.py <顧客フォルダ> [--forbid <語>]…
#
# `<顧客フォルダ>` 直下の `*.pdf`(fitz でテキスト抽出)と `*.md` のテキストに、次が無いことを確かめる。
# あれば rc=1 で、どのファイルの何ページ・何行に何があったかを標準エラーへ出す。
#
# - `--forbid <語>` で渡した語(名前など。繰り返し可)
# - `ALWAYS_FORBIDDEN_WORDS`(冊子に出さない語。いまは「最善手」の 1 語)
# - `@`、`/Users/`、`水匠`、`None`(python の None がそのまま印字された跡。凍結の例外 12 件目)
# - 禁止語は無し(2026-09-25 の人間の決定、凍結の例外 14 件目 ― 冊子の禁止語はすべて使ってよい)。
#   `check_answer.py` の `BANNED_WORDS` は import のまま(空)。語のリストを二重に持たないため、この道具は
#   自分で語を持たない(司令塔の指示)。
#
# 検査の対象は `<顧客フォルダ>` 直下の `*.pdf` と `*.md` だけ(`direct/` の JSON は対象外)。
#
# 【この道具が絶対にやらないこと】将棋の判断。PDF・md を書き換えること(落ちた場所の一覧を返すだけ)。
# 語のリストを自分で持つこと(禁止語は check_answer.py から import する ― 2026-09-25 から空)。
import glob
import os
import sys

from check_answer import BANNED_WORDS

# `check_answer.py` の `BANNED_WORDS` の先頭 18 語(2026-09-25 の人間の決定で `BANNED_WORDS` が空になったため、
# ここも空になる)。コードは変えていない(語が無いので何も探さない)。
BANNED_18 = BANNED_WORDS[:18]

# 語以外の、常に伏せるもの(計画 §3 の 6)。
ALWAYS_FORBIDDEN = ["@", "/Users/", "水匠", "None"]

# **顧客の冊子に出さない語**(2026-09-30。器の単独束 C-2。正本は
# `docs/NEXTGEN_CONNECTION_DESIGN_2026-09-30.md` §4 の H-4)。
# 「最善手」は**人間が固定した用語の決定** ― 冊子は「第 1 候補」と書く。
#
# 【なぜ `ALWAYS_FORBIDDEN` と分けるか】あちらは「語以外の、常に伏せるもの」(記号・パス・道具の名・None)で、
# 意味が違う。混ぜると、片方を直すときにもう片方の理由が読めなくなる。
# 【なぜ `check_answer.BANNED_WORDS` に足さないか】あの表は **2026-09-25 の人間の決定で空にした**もので、
# 足すと**席の文の検査(H-5)まで動く**。ここに置けば効くのは納品の走査だけ。
# 【なぜ `--forbid` の固定引数にしないか】`--forbid` の値は顧客の実名なので**記録に書かない決まり**があり
# (`lib/deliver.ts` の 929〜938 行)、固定語をそこに乗せると**記録から見えない語**になる。
# ここに書けば、道具の出力(「語 N 個」)と原本の両方から誰でも読める。
# 【実測(2026-09-30)】5 人目の納品フォルダ(13 本)で、この語を足しても**通過**(語 4 個 → 5 個)。
# 封じた最終版の本編にも 0 件(司令塔が確認)。**既存の道を赤くしない。**
#
# 【ここに「普段」を足さないこと(2026-10-01。司令塔が実物で確かめた)】
# 足すと**2 か所が壊れる**: (1) **顧客の問いの字** ― `observation-request.json` の q1 は
# 「…何局かは**普段**指さない戦型を採用している…」で、節「お預かりした問い」がこれを引く。
# (2) **人間が書いた 80 文字の文** ― `exit_index.UNANSWERABLE_PAST_GAMES` は
# 「『**普段**と異なる戦略…』」「『**普段**』を判定するには…」と、
# **判定できないものとして**この語を使っている。
# 止めたいのは**群のラベルに使うこと**だけなので、守りは `exit_groups.LABEL_FORBIDDEN_WORDS`
# (ラベルと群の表の行の見出しの 2 か所)に置いてある。**文書全体の黒名簿にしない。**
ALWAYS_FORBIDDEN_WORDS = ["最善手"]

USAGE = "使い方: python3 -X utf8 check_delivery.py <顧客フォルダ> [--forbid <語>]…"


class CheckDeliveryError(Exception):
    pass


def parse_args(argv):
    out_dir = None
    forbid = []
    i = 0
    while i < len(argv):
        flag = argv[i]
        if flag == "--forbid":
            value = argv[i + 1] if i + 1 < len(argv) else None
            if value is None or value.startswith("--"):
                raise CheckDeliveryError("--forbid に値が無い")
            forbid.append(value)
            i += 2
            continue
        if flag.startswith("--"):
            raise CheckDeliveryError(f"知らない引数: {flag}")
        if out_dir is not None:
            raise CheckDeliveryError("顧客フォルダは 1 つだけ指定する")
        out_dir = flag
        i += 1
    if out_dir is None:
        raise CheckDeliveryError(USAGE)
    return out_dir, forbid


def words_of(forbid):
    """探す語の一覧(重複は 1 つにまとめ、渡された順・18 語の順を保つ)。"""
    words = []
    for w in list(forbid) + ALWAYS_FORBIDDEN + ALWAYS_FORBIDDEN_WORDS + list(BANNED_18):
        if w not in words:
            words.append(w)
    return words


def pages_of_pdf(path):
    """PDF の 1 ページごとのテキスト(1 始まりのページ番号つき)。"""
    import fitz  # pymupdf

    doc = fitz.open(path)
    try:
        return [(index + 1, page.get_text()) for index, page in enumerate(doc)]
    finally:
        doc.close()


def pages_of_md(path):
    """md はページの無い 1 枚として扱う(ページ番号 None)。"""
    with open(path, encoding="utf-8") as f:
        return [(None, f.read())]


def findings_of(path, pages, words):
    """(ページ, 行番号, 語, 行の抜粋)の一覧。1 行に複数の語があればそれぞれ 1 件。"""
    found = []
    for page_no, text in pages:
        for line_no, line in enumerate(text.split("\n"), start=1):
            for word in words:
                if word in line:
                    found.append((path, page_no, line_no, word, line.strip()[:120]))
    return found


def main(argv):
    out_dir, forbid = parse_args(argv)
    if not os.path.isdir(out_dir):
        raise CheckDeliveryError(f"顧客フォルダが無い: {out_dir}")
    words = words_of(forbid)

    targets = sorted(glob.glob(os.path.join(out_dir, "*.pdf"))) + sorted(glob.glob(os.path.join(out_dir, "*.md")))
    if not targets:
        raise CheckDeliveryError(f"検査する *.pdf・*.md が無い: {out_dir}")

    findings = []
    for path in targets:
        pages = pages_of_pdf(path) if path.lower().endswith(".pdf") else pages_of_md(path)
        findings.extend(findings_of(path, pages, words))

    if findings:
        for path, page_no, line_no, word, line in findings:
            where = f"{os.path.basename(path)}" + (f" p.{page_no}" if page_no is not None else "") + f" {line_no} 行目"
            print(f"{where}: 「{word}」: {line}", file=sys.stderr)
        print(f"落ちた箇所 {len(findings)} 件(検査したファイル {len(targets)} 本・語 {len(words)} 個)", file=sys.stderr)
        return 1
    print(f"通過(検査したファイル {len(targets)} 本・語 {len(words)} 個)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except CheckDeliveryError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
