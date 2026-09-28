# -*- coding: utf-8 -*-
# STEP CUSTOMER-EXIT ④(docs/STEP_CUSTOMER_EXIT_SPEC_2026-09-28.md §4)。
# **顧客向け出口の「器」の門。**承認済みの 30 ページの形(docs/GOLDEN_MASTER_CUSTOMER_EXIT.md)から外れた成果物を止める。
#
# 使い方:
#   python3 -X utf8 check_structure.py <顧客フォルダ> \
#     --honbun-md <本編.md> --honbun-personal <本人用.pdf> --honbun-sample <見本用.pdf> \
#     --appendix <付録.pdf> --page-index <page_index.json> \
#     (以下は check_answer.py と同じ形。本編の md をそのまま検査に通すため)
#     [--patient <patient_report_data.json> --time-limit-sec <秒>]… --menu <answer_menu.json> \
#     [--direct <json>]… [--time-cause <json>]… [--prose <prose.json>] [--whatif-data-now <json>]…
#
# 出力: rc=0 なら通過。rc=1 なら落ちた項目の一覧(1 行 1 件)を標準エラーへ。
#
# 【役割の分け方(二重に判定しない)】
# - **文と数**(数が材料に実在するか・行動が minN を通ったか・`<!-- pos: -->` の宣言が付録の局面にあるか)は
#   **`check_answer.py` をそのまま呼ぶ**(検査 1〜7)。この道具はそれを**もう一度実装しない**。
# - **器**(節の並び・ページ数・本人用と見本用の差・盤の数・付録のページの対応・商品の範囲・対応表の場所・
#   **答え合わせの表の行数**〈項目 6。`check_verify_table`〉・索引と PDF の整合)を、この道具が見る。
#   **答え合わせの表の「今の値」が材料と合っているかは、この道具では見ない** ― `check_answer.py` の検査 1 が
#   表の行も含めて全行の数を材料と突き合わせるので、そこに任せる(二重に判定しない)。
#
# 【文字の抽出は fitz だけ】既知事項 P-112 ― `pypdf` の `extract_text()` は Chrome headless で作った PDF の
# 一部の漢字を**康熙部首**(U+2E80〜U+2FDF)で返す(実測 26 種類。「数え方」が 0 件になる)。`fitz` は返さない。
# **この道具は `pypdf` を使わない**(ページ数も fitz で取れる)。それでも **NFKC を通す**(二重の安全)。
#
# 【この道具が絶対にやらないこと】
# - 「伝わるか」を判定すること(批評席の仕事。§4 の表に入れない)
# - `check_answer.py` の判定を上書きすること・数の照合を自分で書き直すこと
# - 成果物を直すこと・ページを足すこと
import glob
import json
import os
import re
import sys
import unicodedata

import check_answer as CA

# ==================== 正本の形(docs/GOLDEN_MASTER_CUSTOMER_EXIT.md §1・§7) ====================
# **節は「役割」で見る。見出しの文字そのものでは見ない。**
# 2026-09-28 に 4 人目の送付用の実物を `fitz` で読んで数えた結果(正本 §7 の表):
# **6 節のうち 5 節は実物の見出しと前方一致し**、実物は顧客ごとに局数などを変える
# (例: 答え合わせの節は 3 人目「次の 20 局で、何で答え合わせをするか」・4 人目「次の 20 局が来たら、何で答え合わせをするか」)。
# **だから完全一致では検査できない** ― 「頭が一致し、必要なら特定の語を含む」で見る。
# 3 人目の値は司令塔が `honbun.md` の `##` から引いたもの(**PDF では未実測**。正本 §7 に印つきで明記)。
# `exit-candidates` が md の骨を作るときに**この定数を使い**、この門は**同じ定数**で見る
# (B の下書きが `answer_facts.py` の固定見出しを持つのと同じ形)。
#
# 各行は (役割, 見出しの頭, 見出しに必ず含まれる語 or None)。
SECTIONS = [
    ("ひとことで", "ひとことで", None),
    ("局面で見る", "局面で見る", None),
    ("試せること", "試せること", None),
    # 局数は顧客で変わる(「次の 20 局が来たら」「次の 20 局で」)ので、頭の「次の」と語「答え合わせ」で見る。
    ("答え合わせ", "次の", "答え合わせ"),
    ("数え方", "数え方", None),
    ("対応表", "対応表", None),
]
# 答え合わせの表の節(項目 6)。対応表の節(見本用では抜くページ)。
VERIFY_ROLE = "答え合わせ"
MAPPING_ROLE = "対応表"
# 商品の範囲の 1 段落(正本 §1。**ちょうど 1 か所**)。
SCOPE_SENTENCE = "この冊子は、エンジンの解析と機械の集計から、次の 20 局で確かめる仮説を出すものです。"
# 上限(正本 §2。実物に合わせて 本編 ≤ 5・付録 ≤ 25・合計 ≤ 30)。
MAX_HONBUN_PAGES = 5
MAX_APPENDIX_PAGES = 25
MAX_TOTAL_PAGES = 30
# 盤の数(正本 §1「盤 2 つ」。**両方の実物で合計 2 つ**。ページ配置は固定しない)。
BOARD_COUNT = 2


class CheckStructureError(Exception):
    pass


def norm(text):
    """P-112。抽出した文字は必ず NFKC を通す(この道具は fitz なので化けないが、二重の安全)。"""
    return unicodedata.normalize("NFKC", text)


def squeeze(text):
    """空白・改行をすべて落とす。**組版は文を行に折る**ので、PDF から抜いた文字には途中に改行が入る
    (実測: 土台の 1 ページ目で `SCOPE_SENTENCE` が 2 行に折られ、そのままでは 0 か所と数えた)。
    `check_answer.py` の `build_materials` が `--whatif-pdf` の本文に対して使っているのと同じ流儀
    (`re.sub(r"\s+", "", …)`)を、こちらでも使う。"""
    return re.sub(r"\s+", "", text)


def page_texts(path):
    """fitz でページごとのテキストを返す(`pypdf` は使わない ― P-112)。"""
    import fitz  # pymupdf

    doc = fitz.open(path)
    try:
        return [norm(page.get_text()) for page in doc]
    finally:
        doc.close()


def parse_args(argv):
    """自分の引数を取り、残りを check_answer.py にそのまま渡す(引数の形を二重に定義しない)。"""
    if not argv:
        raise CheckStructureError("顧客フォルダを渡してください")
    out_dir = argv[0]
    mine = {"--honbun-md": None, "--honbun-personal": None, "--honbun-sample": None,
            "--appendix": None, "--page-index": None}
    rest = []
    i = 1
    while i < len(argv):
        flag = argv[i]
        if flag in mine:
            if i + 1 >= len(argv):
                raise CheckStructureError(f"{flag} に値が無い")
            mine[flag] = argv[i + 1]
            i += 2
            continue
        rest.append(flag)
        i += 1
    missing = [k for k, v in mine.items() if v is None]
    if missing:
        raise CheckStructureError(f"足りない引数: {' '.join(missing)}")
    if not os.path.isdir(out_dir):
        raise CheckStructureError(f"顧客フォルダが無い: {out_dir}")
    return out_dir, mine, rest


def heading_lines(md_text):
    """`## ` で始まる行を (行番号〈0 起算〉, 見出しの本文) で返す。"""
    out = []
    for i, line in enumerate(md_text.split("\n")):
        stripped = line.strip()
        if stripped.startswith("## "):
            out.append((i, stripped[3:].strip()))
    return out


def role_of(heading_text):
    """見出しの本文が、どの役割に当たるかを返す(当たらなければ None = 間に増えた任意の節)。"""
    for role, prefix, must_contain in SECTIONS:
        if heading_text.startswith(prefix) and (must_contain is None or must_contain in heading_text):
            return role
    return None


def section_positions(md_text):
    """役割 → 最初に出た見出しの行番号。見つからない役割は入らない。"""
    found = {}
    for line_no, text in heading_lines(md_text):
        role = role_of(text)
        if role is not None and role not in found:
            found[role] = line_no
    return found


def check_sections(md_text, problems):
    """検査 1(節の並び)。**正本の 6 つの役割が正本の順で出ること。間に節が増えるのは許し、減るのは落とす。**
    見出しの文字は完全一致では見ない(`SECTIONS` の頭と語で見る ― 実物は顧客ごとに文字が変わる)。"""
    found = section_positions(md_text)
    positions = []
    for role, prefix, _ in SECTIONS:
        if role not in found:
            problems.append(f"検査 1: 「{role}」の節が本編に無い(見出しは「## {prefix}」で始まる。減るのは落とす)")
            continue
        positions.append((role, found[role]))
    ordered = [p for _, p in positions]
    if ordered != sorted(ordered):
        problems.append(f"検査 1: 節の並びが正本の順でない(出た順: {[r for r, _ in sorted(positions, key=lambda x: x[1])]})")


def verify_table_rows(md_text):
    """答え合わせの節(役割 `答え合わせ`)の中の markdown の表の**本文行**を返す。
    見出しから次の `## ` までを節とし、`|` で始まる行のうち**区切り行(`---`)と最初の行(列の名前)**を落とす。
    節が無ければ None(節の不在は `check_sections` が落とすので、ここでは二重に言わない)。"""
    lines = md_text.split("\n")
    found = section_positions(md_text)
    if VERIFY_ROLE not in found:
        return None
    start = found[VERIFY_ROLE] + 1
    end = len(lines)
    for line_no, _ in heading_lines(md_text):
        if line_no > found[VERIFY_ROLE]:
            end = line_no
            break
    table = [l.strip() for l in lines[start:end] if l.strip().startswith("|")]
    body = [l for l in table if set(l.replace("|", "").replace(" ", "")) - set("-:") != set()]
    return body[1:] if body else []


def check_verify_table(md_text, problems):
    """**項目 6(答え合わせの表)。**正本 §4 の 8 項目のうち、実装が抜けていた 1 項目
    (2026-09-28 の監査で発覚。冒頭のコメントは先にこの項目を数えていた)。

    **この道具が見るのは「数」だけ**: 表の本文行 1 行につきメニューの印がちょうど 1 つあり、
    **表の行の印の集合が、本編ぜんたいの行動の印の集合と一致する**こと(= 行数 = 行動の本数)。

    **「今の値」が材料と合っているかは、この道具では見ない。** `check_answer.py` の検査 1 が
    **表の行も含めて全行の数を材料と突き合わせている**ので、値を 1 つ書き換えれば検査 1 が落とす
    (実測: `check_structure_test.py` の `test_19`)。**二重に判定しない**(冒頭の役割の分け方のとおり)。"""
    rows = verify_table_rows(md_text)
    if rows is None:
        return
    if not rows:
        problems.append("項目 6: 答え合わせの節に表が無い(行動 1 本につき 1 行が要る)")
        return
    row_ids = []
    for i, row in enumerate(rows, start=1):
        ids = CA.MENU_TAG_RE.findall(row) + CA.PRIORITY_TAG_RE.findall(row)
        if len(ids) != 1:
            problems.append(f"項目 6: 答え合わせの表の {i} 行目にメニューの印が {len(ids)} 個(ちょうど 1 個が要る)")
            continue
        row_ids.append(ids[0])
    in_table = set(row_ids)
    in_body = set(CA.MENU_TAG_RE.findall(md_text) + CA.PRIORITY_TAG_RE.findall(md_text))
    if in_table != in_body:
        missing = sorted(in_body - in_table)
        extra = sorted(in_table - in_body)
        problems.append(
            f"項目 6: 答え合わせの表の行と行動の本数が合わない"
            f"(表に無い行動: {missing or 'なし'} / 本編に無い行: {extra or 'なし'})"
        )


def check_pages(personal, sample, appendix, problems):
    """検査 2(ページ数)。本編 ≤ 5・付録 ≤ 25・合計 ≤ 30。"""
    n_personal, n_sample, n_appendix = len(personal), len(sample), len(appendix)
    if n_personal > MAX_HONBUN_PAGES:
        problems.append(f"検査 2: 本編(本人用)が {n_personal} ページ(上限 {MAX_HONBUN_PAGES})")
    if n_sample > MAX_HONBUN_PAGES:
        problems.append(f"検査 2: 本編(見本用)が {n_sample} ページ(上限 {MAX_HONBUN_PAGES})")
    if n_appendix > MAX_APPENDIX_PAGES:
        problems.append(f"検査 2: 付録が {n_appendix} ページ(上限 {MAX_APPENDIX_PAGES})")
    total = n_personal + n_appendix
    if total > MAX_TOTAL_PAGES:
        problems.append(f"検査 2: 本人用 + 付録が {total} ページ(上限 {MAX_TOTAL_PAGES})")


def check_sample_difference(personal, sample, problems):
    """検査 4(本人用と見本用の差)。**差は対応表の 1 ページだけ**(fitz で本文を比べる ― P-112)。"""
    if len(personal) - len(sample) != 1:
        problems.append(f"検査 4: 本人用 {len(personal)} ページ・見本用 {len(sample)} ページ(差は 1 ページでなければならない)")
    mapping_word = squeeze(MAPPING_ROLE)
    personal_mapping = [i + 1 for i, t in enumerate(personal) if mapping_word in squeeze(t)]
    sample_mapping = [i + 1 for i, t in enumerate(sample) if mapping_word in squeeze(t)]
    if not personal_mapping:
        problems.append("検査 4: 対応表のページが本人用に無い")
    if sample_mapping:
        problems.append(f"検査 4: 対応表のページが見本用に残っている({sample_mapping} ページ)")
    remaining = [t for i, t in enumerate(personal) if (i + 1) not in personal_mapping]
    if len(remaining) == len(sample):
        for i, (a, b) in enumerate(zip(remaining, sample), start=1):
            if a != b:
                problems.append(f"検査 4: 対応表を除いた {i} ページ目の本文が本人用と見本用で違う")
                break


def check_boards(md_text, index, personal, problems):
    """検査 7(盤)。**`pos` の数 = `exit-render` が差し込んだ回数 = 2。**
    md にあって描かれなかった盤を捕まえるため、**索引に書かれた差し込みの回数**と突き合わせる
    (ページを置いた経路が書いた数。この道具は数え直さない)。**ページ配置は見ない**(実物で 2 通りある)。"""
    declared = CA.POS_TAG_RE.findall(md_text)
    if len(declared) != BOARD_COUNT:
        problems.append(f"検査 7: 本編の `<!-- pos: -->` が {len(declared)} 件(正本は {BOARD_COUNT} 件)")
    drawn = index.get("boardsDrawn")
    if drawn is None:
        problems.append("検査 7: page_index.json に boardsDrawn(差し込んだ盤の回数)が無い")
    elif drawn != len(declared):
        problems.append(f"検査 7: 宣言した盤 {len(declared)} 件と、差し込んだ盤 {drawn} 件が合わない")


def check_appendix_pages(index, appendix, problems):
    """検査 8(付録の扱い)+ 索引と PDF の整合。
    **付録のページ数 = 本編が指すページの数(表紙を除く)**。**指していないページが混ざっていない。**
    **索引の値 > PDF のページ数なら落とす**(索引が古い = PDF だけ作り直された、を捕まえる)。"""
    picked = index.get("appendixPages")
    if picked is None:
        problems.append("検査 8: page_index.json に appendixPages(抜いたページの一覧)が無い")
        return
    cover = 1 if index.get("hasCover") else 0
    if len(picked) + cover != len(appendix):
        problems.append(
            f"検査 8: 付録が {len(appendix)} ページだが、指しているのは {len(picked)} ページ"
            f"(表紙 {cover} ページを含めても合わない ― 指していないページが混ざっている)"
        )
    for source, pages in (index.get("sourcePages") or {}).items():
        for page in pages:
            if page < 1:
                problems.append(f"索引: {source} のページ番号が {page}(1 以上でなければならない)")
    for entry, page in (index.get("positions") or {}).items():
        if not isinstance(page, int) or page < 1 or page > len(appendix):
            problems.append(f"索引と PDF の整合: {entry} が付録の {page} ページを指しているが、付録は {len(appendix)} ページ")


def check_scope_and_mapping(personal, problems):
    """商品の範囲の 1 段落が**ちょうど 1 か所**。**行の折り返しを越えて数える**(`squeeze`)。"""
    joined = squeeze("".join(personal))
    count = joined.count(squeeze(norm(SCOPE_SENTENCE)))
    if count != 1:
        problems.append(f"商品の範囲の 1 段落が {count} か所(ちょうど 1 か所でなければならない)")


def main(argv):
    out_dir, mine, rest = parse_args(argv)
    problems = []

    with open(mine["--honbun-md"], encoding="utf-8") as f:
        md_text = f.read()
    with open(mine["--page-index"], encoding="utf-8") as f:
        index = json.load(f)

    # 文と数・行動の minN・`<!-- pos: -->` の宣言は check_answer.py に任せる(二重に判定しない)。
    args = CA.parse_args([mine["--honbun-md"]] + rest)
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    ctx = CA.build_materials(args, repo_root)
    for line_no, reason, line in CA.check_answer(md_text, ctx):
        problems.append(f"本編の文(check_answer){line_no}: {reason}: {line.strip()[:80]}")

    personal = page_texts(mine["--honbun-personal"])
    sample = page_texts(mine["--honbun-sample"])
    appendix = page_texts(mine["--appendix"])

    check_sections(md_text, problems)
    check_verify_table(md_text, problems)
    check_pages(personal, sample, appendix, problems)
    check_sample_difference(personal, sample, problems)
    check_boards(md_text, index, personal, problems)
    check_appendix_pages(index, appendix, problems)
    check_scope_and_mapping(personal, problems)

    if problems:
        print(f"落ちた項目 {len(problems)} 件:", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1
    print(
        f"通過(本編 {len(personal)} ページ・見本用 {len(sample)} ページ・付録 {len(appendix)} ページ・"
        f"盤 {len(CA.POS_TAG_RE.findall(md_text))} 件)"
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (CheckStructureError, CA.CheckAnswerError) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
