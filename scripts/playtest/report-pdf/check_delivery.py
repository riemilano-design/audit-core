# -*- coding: utf-8 -*-
# STEP DELIVER-1(docs/STEP_DELIVER1_PLAN_2026-09-25.md §3 の 6)。納品フォルダの伏せ字・個人情報の検査。
#
# 使い方: python3 -X utf8 check_delivery.py <顧客フォルダ> [--forbid <語>]…
#
# `<顧客フォルダ>` 直下の `*.pdf`(fitz でテキスト抽出)と `*.md` のテキストに、次が無いことを確かめる。
# あれば rc=1 で、どのファイルの何ページ・何行に何があったかを標準エラーへ出す。
#
# - `--forbid <語>` で渡した語(名前など。繰り返し可)
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
    for w in list(forbid) + ALWAYS_FORBIDDEN + list(BANNED_18):
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
