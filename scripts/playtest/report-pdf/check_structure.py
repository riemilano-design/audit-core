# -*- coding: utf-8 -*-
# STEP CUSTOMER-EXIT ④(docs/STEP_CUSTOMER_EXIT_SPEC_2026-09-28.md §4)。
# **顧客向け出口の「器」の門。**承認済みの 30 ページの形(docs/GOLDEN_MASTER_CUSTOMER_EXIT.md)から外れた成果物を止める。
#
# 使い方:
#   python3 -X utf8 check_structure.py <顧客フォルダ> \
#     --honbun-md <本編.md> --honbun-personal <本人用.pdf> --honbun-sample <見本用.pdf> \
#     --appendix <付録.pdf> --page-index <束ねた付録の索引.json> \
#     --honbun-index <本編の索引.json>  (`exit_body.py` が本人用の PDF の隣に書くもの) \
#     [--source-index <組版が書いた索引.json>]…  (付録ごとに 1 本。束ねた値が書き換えられていないかを見る) \
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
import exit_index as EI

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
#
# **局数は型で持つ**(2026-09-29。司令塔の ⑥ が実物で見つけた D1)。
# 「次の **20** 局」を直書きしていたため、**同じ冊子の答え合わせの見出し「次の 25 局」と食い違っていた**
# ― 25 局を見た顧客の冊子が、1 ページ目で「次の 20 局で確かめる」と言う。
# **数は組の局数から入れる**(`patient_report_data.json` の `games`。新しい数を作らない)。
# 正本 §1 の実物が 20 局の顧客のものだったので、20 が固定値として写っていた。
SCOPE_SENTENCE_TEMPLATE = "この冊子は、エンジンの解析と機械の集計から、次の {games} 局で確かめる仮説を出すものです。"


def scope_sentence(games):
    """商品の範囲の 1 段落。**組版と門が同じここから作る**(片方だけ直らない)。"""
    return SCOPE_SENTENCE_TEMPLATE.format(games=int(games))


# ==================== 本編 p1 の冒頭の段落(P-162。2026-09-29) ====================
# **4 人目(送付済み)の実物を測って型にした。**c5 の 2 周目の冒頭は
# `SCOPE_SENTENCE_TEMPLATE` の 1 文だけで、**次の 5 つが本編に 0 件だった**(実測):
#
# 1. 「〈組の名〉〈局数〉局を、1 手ずつ将棋エンジンで調べました(日付)」
# 2. **「手の良し悪しを判定するものではありません。」**
#    ― **これが無いのがいちばん重い。**「最善手を教えるアプリではない」という
#    このプロジェクトの核心の断り書きが、付録の表紙には在るのに本編に無かった
# 3. 「数の出どころは付録で引けます。」
# 4・5. 組が 2 つ以上のときの 2 文(分けて数えている / 断りが無ければどの組か)
#
# **人の名前は入れない**(2026-09-29 に測って決めた)。4 人目の実物は
# 「〈名前〉さんの 3 分切れ負け 18 局と…」で始まるが、**あの顧客には本人用しか渡していない**
# (送付フォルダに本編が 1 本だけ)。c5 は**見本用も作る**ので、冒頭に名前を置くと
# **見本用にも載る** ― 見本用は他人に見せるものなので、名前は冒頭に入れない(P-147 の家族)。
# 名前を入れるかは人間の判断として上げる。
OPENING_ENGINE_TEMPLATE = "{groups}を、1 手ずつ将棋エンジンで調べました({today})。"
OPENING_NOT_A_JUDGE = "手の良し悪しを判定するものではありません。"
OPENING_APPENDIX = "数の出どころは付録で引けます。"
# **用語の 4 行**(器の単独束 C-3。2026-09-30。**文は人間が固定したもの**)。
#
# 【なぜ要るか】5 人目の感想が「第一候補 = ソフトの最善手か」と聞いた ―
# **冊子の中でいちばん使う語が、冊子の中で定義されていなかった。**
# 語の形は人間の言葉そのまま(`docs/NEXTGEN_CONNECTION_DESIGN_2026-09-30.md` の
# 「第 1 候補: この局面でエンジンが 1 番に挙げた手。…」)。**「最善手」の語は使わない**
# (`check_delivery.ALWAYS_FORBIDDEN_WORDS` が納品を止める)。
#
# 【なぜここ 1 か所か】`exit_candidates.build_md` が**この表から md を作り**、
# 下の `check_term_lines` が**組んだ PDF に在るか**を見る。写しを持たないので、
# 文を直せば組版と門が同時に動く(**2 か所ある欠陥は片方で閉じない**の逆 ― 元から 1 か所)。
#
# 【文は道具の言い方から採る】「分かれ道」の文は `answer_facts.py` の
# 「第 1 候補との差が大きい、または候補 5 つに入らなかった局面」から採った。
# **自分で新しい定義を書かない** ― 文と機械の数え方が食い違うと、付録で引いたときに合わない。
TERM_LINES = (
    ("第 1 候補",
     "この局面でエンジンが 1 番に挙げた手。正解と決めるものではなく、実戦の手と比べるために使っています。"),
    ("分かれ道",
     "実戦の手とエンジンの第 1 候補の差が大きかった局面、"
     "または実戦の手がエンジンの候補 5 つに入らなかった局面。"),
    ("自玉側",
     "相手の玉に向かう手を「攻め」、自分の玉のまわりを固める手を「自玉側」と数えています。"),
    ("一致率", "分かれ道のうち、実戦の手とエンジンの第 1 候補が同じ側だった割合。"),
)


def term_md_lines():
    """用語の 4 行を md の箇条書きにして返す(組版と門が同じここから作る)。"""
    return [f"- **{term}**: {sentence}" for term, sentence in TERM_LINES]


OPENING_SPLIT_TEMPLATE = ("持ち時間の違う {n} つの組は分けて数えています"
                          "(混ぜると 1 手あたりの秒が意味を失うため)。")
OPENING_PRIMARY_TEMPLATE = "以下の数は、断りが無ければ {label}の {games} 局のものです。"
# 日付の形。**ISO(YYYY-MM-DD)だけを通す** ― `check_answer.scan_numbers` は ISO 日付を
# 数の主張から外すので、**この形以外を入れると門が日付を「書き手が選んだ数」として数える**。
TODAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def opening_paragraph(games, groups, today):
    """本編 p1 の冒頭の段落を、**文の並び**で返す(組版と門が同じここから作る)。

    `games` は冊子が見た局数の合計、`groups` は `((ラベル, 局数), …)` で**先頭が今回の組**。
    組が 1 つなら 4 文、2 つ以上なら 6 文(4 人目の実物と同じ並び)。

    **合計が合わないものは落とす** ― 組ごとの局数の和が `games` と違えば、
    冒頭の「〈組の名〉〈局数〉局」と本文の分母が食い違う冊子ができる。
    """
    if not groups:
        raise CheckStructureError("組が 0 件(冒頭の段落を作れない)")
    if not TODAY_RE.match(str(today)):
        raise CheckStructureError(f"日付の形が YYYY-MM-DD でない: {today!r}")
    total = sum(int(n) for _label, n in groups)
    if total != int(games):
        raise CheckStructureError(
            f"組ごとの局数の和 {total} が冊子の局数 {int(games)} と違う"
            "(冒頭の局数と本文の分母が食い違う)")
    phrase = "と、".join(f"{label} {int(n)} 局" for label, n in groups)
    out = [OPENING_ENGINE_TEMPLATE.format(groups=phrase, today=today),
           scope_sentence(games),
           OPENING_NOT_A_JUDGE,
           OPENING_APPENDIX]
    if len(groups) > 1:
        label, n = groups[0]
        out.append(OPENING_SPLIT_TEMPLATE.format(n=len(groups)))
        out.append(OPENING_PRIMARY_TEMPLATE.format(label=label, games=int(n)))
    return out
# 上限(正本 §2。実物に合わせて 本編 ≤ 5・付録 ≤ 25・合計 ≤ 30)。
# **2026-09-29 の読み替え(司令塔・案 1。正本 §12)**: 本編の上限は
# **「4 + 対応表のページ数」** ― 対応表は分析の中身ではなく**顧客が自分の局を引く索引**で、
# **行数は局数に比例する**(実測: 節がページ先頭から始まる場合 25 行 = 1 ページ・26 行 = 2 ページ)。
# 5 に固定すると、**26 局以上の顧客の本編がこの門を通れない**(P-133)。
# **器(役割・順番)は変わらず、上限だけが局数で伸びる。**
MAX_HONBUN_PAGES = 5
HONBUN_PAGES_WITHOUT_MAPPING = 4
MAX_APPENDIX_PAGES = 25
MAX_TOTAL_PAGES = 30
# 盤の数(正本 §1「盤 2 つ」。**両方の実物で合計 2 つ**。ページ配置は固定しない)。
BOARD_COUNT = 2
# 本編の 1 ページ目に置く**事実の本数**(正本 §1「p1 数 3 つ+ひとことで」)。
#
# **「数 3 つ」は「異なる値が 3 つ」ではなく「事実が 3 本」である**(2026-09-29 に実物 2 件を数えて確定):
# - 3 人目の試作 `reedit/honbun.md` の「ひとことで」= **箇条書きちょうど 3 本**。
#   値は 14・6 / 20・46・28・4・14 / 19・52・62・99 の **11 個**
# - 4 人目の本人用 p1(fitz で読んだ)= **事実 3 本 + 1 文**。値は 5・18・79・68・66・13・51・11・21・22 /
#   53・92・34・20・277・167 / 30・3・88・17・97・10・32・0・8
#
# **最初は「異なる値でちょうど 3 つ」として実装し、書き手(司令塔)が書けなかった。**
# 人間の線「局数で数える・分母を付ける」と両立しない ― 「18 局のうち 6 局」だけで既に 2 値になる。
# 名前も `HONBUN_P1_NUMBER_COUNT` から直した(**値の数ではなく事実の数**)。
# **段 `exit-gate` がこの数で数える** ― 門と段が同じ定数を見る(写しを 2 か所に持たない)。
HONBUN_P1_FACT_COUNT = 3


def heading_matches(role, text):
    """`## <見出し>` の行が、その役割の節の見出しかどうかを `SECTIONS` の表から決める。

    **役割ごとに写しを作らない**ための 1 か所(`exit_body.py` の対応表の節・
    `exit_gate.py` の P1〜P3 の節が使う)。`contains` が None の役割は頭で決まる。
    """
    head, contains = next((h, c) for r, h, c in SECTIONS if r == role)
    body = text.strip()
    if not body.startswith(head):
        return False
    return contains is None or contains in body


# **束ねた索引の上の階層に置いてよい鍵。**正本は `exit_index.py` の 1 か所(書く側の `exit_render.py` も
# 同じものを import する)。**写しを 2 か所に持たない** ― 写しは片方だけ直る。
# `exit_index.py` は**定数だけのモジュール**なので、門が組版を import することにはならない
# (司令塔の条件 2026-09-28。`exit_render_test.py` が import 文を見て固定している)。
EXIT_RENDER_KEYS = EI.EXIT_RENDER_KEYS

class CheckStructureError(Exception):
    pass


def norm(text):
    """P-112。抽出した文字は必ず NFKC を通す(この道具は fitz なので化けないが、二重の安全)。"""
    return unicodedata.normalize("NFKC", text)


def squeeze(text):
    """空白・改行をすべて落とす。**組版は文を行に折る**ので、PDF から抜いた文字には途中に改行が入る
    (実測: 土台の 1 ページ目で商品の範囲の 1 段落が 2 行に折られ、そのままでは 0 か所と数えた)。
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
            "--appendix": None, "--page-index": None,
            # 本編の索引(`exit_body.py` が書く)。検査 4 が「差 = 対応表のページ数」を見るのに使う。
            "--honbun-index": None}
    # 組版が書いた索引(付録ごとに 1 本。繰り返せる)。
    source_indexes = []
    # **任意の引数**(渡されなければ飛ばして声に出す。⑧ の G-6 と同じ扱い)。
    # `observation-request.json`(`customerQuestions[]` の件数で節の有無が決まる)。
    optional = {"--request": None}
    rest = []
    i = 1
    while i < len(argv):
        flag = argv[i]
        if flag == "--source-index":
            if i + 1 >= len(argv):
                raise CheckStructureError("--source-index に値が無い")
            source_indexes.append(argv[i + 1])
            i += 2
            continue
        if flag in mine or flag in optional:
            if i + 1 >= len(argv):
                raise CheckStructureError(f"{flag} に値が無い")
            (mine if flag in mine else optional)[flag] = argv[i + 1]
            i += 2
            continue
        rest.append(flag)
        i += 1
    missing = [k for k, v in mine.items() if v is None]
    if missing:
        raise CheckStructureError(f"足りない引数: {' '.join(missing)}")
    if not os.path.isdir(out_dir):
        raise CheckStructureError(f"顧客フォルダが無い: {out_dir}")
    return out_dir, mine, rest, source_indexes, optional


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


def check_pages(personal, sample, appendix, honbun_index, problems):
    """検査 2(ページ数)。**本編 ≤ 4 + 対応表のページ数**・付録 ≤ 25・合計 ≤ 30。

    **2026-09-29 に「本編 ≤ 5」から読み替えた**(司令塔・案 1。正本 §12)。
    対応表のページ数は**索引から取る**(PDF の文字からは数えない ― 2 枚目に見出しの語が無い)。
    **見本用は対応表を抜いた側**なので、上限は `HONBUN_PAGES_WITHOUT_MAPPING` そのまま。
    索引が無いときは**読み替えない**(従来の 5 を使う) ― 検査 4 が別に「索引が無い」で落とすので、
    ここで黙って甘くしない。
    """
    n_personal, n_sample, n_appendix = len(personal), len(sample), len(appendix)
    mapping_pages = (honbun_index or {}).get("mappingPages") or []
    personal_limit = (HONBUN_PAGES_WITHOUT_MAPPING + len(mapping_pages)
                      if mapping_pages else MAX_HONBUN_PAGES)
    if n_personal > personal_limit:
        problems.append(f"検査 2: 本編(本人用)が {n_personal} ページ"
                        f"(上限 {personal_limit} = 4 + 対応表 {len(mapping_pages)} ページ)"
                        if mapping_pages else
                        f"検査 2: 本編(本人用)が {n_personal} ページ(上限 {personal_limit})")
    if n_sample > HONBUN_PAGES_WITHOUT_MAPPING:
        problems.append(f"検査 2: 本編(見本用)が {n_sample} ページ"
                        f"(上限 {HONBUN_PAGES_WITHOUT_MAPPING} ― 対応表を抜いた側)")
    if n_appendix > MAX_APPENDIX_PAGES:
        problems.append(f"検査 2: 付録が {n_appendix} ページ(上限 {MAX_APPENDIX_PAGES})")
    total = n_personal + n_appendix
    if total > MAX_TOTAL_PAGES:
        problems.append(f"検査 2: 本人用 + 付録が {total} ページ(上限 {MAX_TOTAL_PAGES})")


def check_sample_difference(personal, sample, honbun_index, problems):
    """検査 4(本人用と見本用の差)。**差は索引が示す対応表のページ数**(fitz で本文を比べる ― P-112)。

    **2026-09-29 に「差は 1 ページ」から変えた**(司令塔の判断・案 1。P-133)。
    対応表は分析の中身ではなく**顧客が自分の局を引く索引**で、**行数は局数に比例する**。
    実測(節がページ先頭から始まる場合): **25 行 = 1 ページ・26 行 = 2 ページ**。
    **1 に固定すると、26 局以上の顧客の本編がこの門を通れない。**

    **枚数は索引から取る。PDF の文字から数えない** ― 対応表が 2 ページに伸びたとき、
    **2 枚目には見出しの語が無い**ので、文字で数えると足りなくなる
    (ページを置いた経路が書いた索引を見る。検査 8 が `hasCover` を見るのと同じ流儀)。
    **そのうえで、抜かれたページが本当に対応表の節だったか**を文字で確かめる。
    """
    mapping_pages = (honbun_index or {}).get("mappingPages")
    if not mapping_pages:
        problems.append("検査 4: 本編の索引に mappingPages が無い"
                        "(--honbun-index が渡されていないか、exit_body が書いていない)")
        return
    want = len(mapping_pages)
    if len(personal) - len(sample) != want:
        problems.append(f"検査 4: 本人用 {len(personal)} ページ・見本用 {len(sample)} ページ"
                        f"(差は索引が示す対応表の {want} ページでなければならない)")
    mapping_word = squeeze(MAPPING_ROLE)
    # **索引が指すページの先頭に、対応表の節の語があること**(改ページしているので先頭ページに出る)。
    first = mapping_pages[0]
    if not 1 <= first <= len(personal):
        problems.append(f"検査 4: 索引が {first} ページを指しているが、本人用は {len(personal)} ページ")
        return
    if mapping_word not in squeeze(personal[first - 1]):
        problems.append(f"検査 4: 索引が指す {first} ページに対応表の節が無い")
    sample_mapping = [i + 1 for i, t in enumerate(sample) if mapping_word in squeeze(t)]
    if sample_mapping:
        problems.append(f"検査 4: 対応表のページが見本用に残っている({sample_mapping} ページ)")
    remaining = [t for i, t in enumerate(personal) if (i + 1) not in set(mapping_pages)]
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
    # **表紙の枚数**(器の単独束 C-4。2026-09-30)。付録へ回した節が表紙の次のページに付くので、
    # 真偽値では足りない。古い索引(枚数が無い)は今までどおり 1 ページとして扱う。
    cover = index.get("coverPages")
    if not isinstance(cover, int):
        cover = 1 if index.get("hasCover") else 0
    # **表紙は必須**(正本 GOLDEN_MASTER_CUSTOMER_EXIT.md §8。承認済みの 30 ページの形に表紙が入っている)。
    # 抜けると顧客は「この冊子に入っているもの」の案内を失い、**本編から付録のページを辿れなくなる**。
    if not index.get("hasCover"):
        problems.append("検査 8: 付録に表紙が無い(hasCover が真でない ― 正本 §8 の 4 要素が付かない)")
    if len(picked) + cover != len(appendix):
        problems.append(
            f"検査 8: 付録が {len(appendix)} ページだが、指しているのは {len(picked)} ページ"
            f"(表紙 {cover} ページを含めても合わない ― 指していないページが混ざっている)"
        )
    for source, pages in (index.get("sourcePages") or {}).items():
        for page in pages:
            if page < 1:
                problems.append(f"索引: {source} のページ番号が {page}(1 以上でなければならない)")
    # **`outputPositions`(束ねた後の 1 冊の中のページ)**。`付録N.positions`(元の付録のページ)とは別物
    # ― 同じ名前だと 2 つの検査がどちらも嘘になるので改名した(P-120。司令塔の判断 2026-09-28、案 1)。
    for entry, page in (index.get("outputPositions") or {}).items():
        if not isinstance(page, int) or page < 1 or page > len(appendix):
            problems.append(f"索引と PDF の整合: {entry} が付録の {page} ページを指しているが、付録は {len(appendix)} ページ")
    # **改名を慣習ではなく門にする**(司令塔の条件 2026-09-28)。旧い名前が残っていると、
    # `outputPositions` が「無い」だけになり、**この検査が黙って何も見ない**道が残る。
    if "positions" in index:
        problems.append("上の階層の positions は outputPositions に改名済み。旧い名前が残っている")


def check_bundled_index(index, source_paths, problems):
    """**束ねた索引が、組版が書いた索引の和集合と等しいか**(司令塔の条件 2026-09-28)。

    **【注意: `positions` は 1 つのファイルの中で 2 つの意味を持つ】**
    - **`index["outputPositions"]`(上の階層)** = **束ねた後の付録 1 冊の中のページ**。`check_appendix_pages` が
      「PDF のページ数を超えていないか」で見る値。**`exit-render` が新しく書く。**
    - **`index["付録N"]["positions"]`** = **元の付録の中のページ**(組版が書いた値)。この検査が見る値。
      **`exit-render` は書き換えてはいけない。**

    **この 2 つを混ぜると、どちらの検査も嘘になる**(元のページ番号を出力のページ数と比べることになる)。
    名前が同じなのは読み手に危ないので、**既知事項に登録して司令塔の判断を仰いでいる。**

    **`exit-render` が黙って書き換える道を閉じる。**「組版が書いた値は書き換えず、足すだけ」を
    **言葉ではなく機械で確かめる** ― 鍵も値も一致しなければ落とす。

    `exit-render` だけが知る値(`boardsDrawn`・`appendixPages`・`hasCover`・`sourcePages`)は
    **この検査の対象ではない**(新しく書いてよい)。見るのは `positions` と `sections` だけ。
    """
    if not source_paths:
        problems.append("束ねた索引: --source-index が 1 本も無い(組版が書いた索引と突き合わせられない)")
        return
    seen = {}
    for path in source_paths:
        try:
            with open(path, encoding="utf-8") as f:
                src = json.load(f)
        except FileNotFoundError:
            problems.append(f"束ねた索引: --source-index のファイルが無い: {path}")
            continue
        appendix = src.get("appendix")
        if appendix is None:
            problems.append(f"束ねた索引: {os.path.basename(path)} に appendix の欄が無い(どの付録のものか分からない)")
            continue
        if appendix in seen:
            problems.append(f"束ねた索引: 付録「{appendix}」の索引が 2 本渡されている({seen[appendix]} と {os.path.basename(path)})")
            continue
        seen[appendix] = os.path.basename(path)
        bundled = index.get(appendix)
        if bundled is None:
            problems.append(f"束ねた索引: 付録「{appendix}」が束ねた索引に無い(組版は書いたのに落ちている)")
            continue
        for field in ("positions", "sections"):
            want = src.get(field) or {}
            got = bundled.get(field) or {}
            if got != want:
                only_src = sorted(set(want) - set(got))
                only_bundled = sorted(set(got) - set(want))
                changed = sorted(k for k in set(want) & set(got) if want[k] != got[k])
                problems.append(
                    f"束ねた索引: 付録「{appendix}」の {field} が組版の索引と違う"
                    f"(束ねた側に無い: {only_src or 'なし'} / 組版に無い: {only_bundled or 'なし'} / 値が違う: {changed or 'なし'})"
                )
    # **許可一覧で見る。接頭辞では見ない**(司令塔の指示 2026-09-28)。
    # 「付録」で始まるかどうかで判定すると、**付録名の付け方に依存**し、**知らない鍵が黙って混ざる道**も残る。
    # 上の階層に置いてよいのは、**`exit-render` が新しく書く固定の名前**か、**渡された付録名**だけ。
    allowed = set(EXIT_RENDER_KEYS) | set(seen)
    unknown = sorted(set(index) - allowed)
    if unknown:
        problems.append(
            f"束ねた索引: 上の階層に置いてよくない鍵がある: {unknown}"
            f"(置けるのは {sorted(EXIT_RENDER_KEYS)} と、--source-index で渡された付録名 {sorted(seen) or 'なし'})"
        )


def check_name_agrees(personal, appendix, person, problems):
    """**本編と付録で名前が違うなら落とす(両方向)**(2026-09-29。D5 → P-170 で両方向にした)。

    `person` は `patient_report_data.json` の `person`(材料の中の実名)。

    【何を守るか】**見本用は本人用からページを抜いたものなので、名前を分けられない。**
    付録は 1 冊で本人用にも見本用にも付く。だから**どちらに実名が乗っても、見本用の一式に乗る。**
    実物で出た 2 つの向き:
    - **付録だけ**(2026-09-29 の D5 = P-147): 本編は `--name 〇〇さん` で組まれているのに、
      付録 1 は材料の `person` で組まれていて「上に行くほど〈実名〉が良く」と印字された。
    - **本編だけ**(2026-09-29 の P-170): 盤の名札が `--name`(実名)で組まれ、付録は「本人」だった。
      **この向きをこの検査は見ていなかったので通した** ― 下の注のとおり、
      docstring が「名前が違うこと」を禁じると書いていたのに、実装は片側だけだった。

    【禁じたいのは「本編と付録で名前が違う」こと】どちらかが匿名なら、もう一方も匿名でなければ
    意味が無い。**実名そのものを禁じるのはこの検査ではなく `check_no_real_name`**(項目 11)で、
    2026-09-29 の人間の決定「本人用でも名前で呼ばない」以降はそちらが厳しい側の規則になった。
    この検査は、**名前を出す決定に戻ったときの歯止め**として残してある。
    """
    if not person:
        return
    name = squeeze(norm(person))
    in_appendix = any(name in squeeze(norm(t)) for t in appendix)
    in_personal = any(name in squeeze(norm(t)) for t in personal)
    # **両方向を見る**(2026-09-29。P-170)。もとは「付録に在って本編に無い」だけを見ていたため、
    # **逆向き(本編に在って付録に無い)が通った** ― 実物では本編の盤の名札に実名が入り、
    # 付録は「本人」だったので、この検査は黙って通った。docstring は「名前が違うこと」を
    # 禁じると書いていたのに、実装はその片側だけだった。
    # **メッセージに名前そのものを書かない**(落ちた時ほどログに名前を残さない)。
    if in_appendix and not in_personal:
        problems.append(
            "付録に顧客の実名が出ているのに本編に出ていない(本編と付録で名前が違う。"
            "見本用は本人用からページを抜いたもので、付録は 1 冊で両方に付くため、"
            "付録の実名は見本用の一式に乗る)")
    if in_personal and not in_appendix:
        problems.append(
            "本編に顧客の実名が出ているのに付録に出ていない(本編と付録で名前が違う。"
            "見本用は本人用からページを抜いたものなので、本編の実名は見本用に乗る)")


def check_no_real_name(personal, sample, appendix, person, problems):
    """**顧客の実名が、顧客に渡す 3 冊のどのページにも無いこと**(2026-09-29 の人間の決定。P-170)。

    決定は「**本人用でも顧客を名前で呼ばない**」 ― 盤の名札も本文も「本人」。
    だから規則が 1 つに決まる: **実名は本編(本人用・見本用)・付録のどこにも無い。**

    【なぜ本人用にも掛けるか】**見本用は本人用からページを抜いたもの**なので、
    本人用に名前が在れば、抜かないページに在るかぎり見本用に乗る。
    本人用に掛ければ両方が閉じる(見本用 ⊂ 本人用)。**それでも見本用を別に見る** ―
    ページの抜き方が変わったときに黙って通らないため。

    【この検査が要る理由】`check_delivery.py --forbid` には**顧客自身の名前を渡せない**
    (フォルダ全体を対象にする道具なので、名前を禁じると本人用も落ちる…という前提で
    作られていた)。名前の規則が「どこにも出さない」に決まった今、**冊子の側で見る場所**が要る。

    **メッセージに名前そのものを書かない。**どの冊子の何ページかだけを言う。
    """
    if not person:
        return
    name = squeeze(norm(person))
    for label, pages in (("本人用", personal), ("見本用", sample), ("付録", appendix)):
        hits = [i + 1 for i, t in enumerate(pages) if name in squeeze(norm(t))]
        if hits:
            problems.append(
                f"{label}の {hits} ページ目に顧客の実名が出ている"
                "(2026-09-29 の人間の決定: 本人用でも名前で呼ばない ― 盤の名札も本文も「本人」)")


def check_one_referent(personal, sample, appendix, problems):
    """**顧客の呼び方が 1 通りであること**(項目 12。2026-09-29。P-174)。

    2026-09-29 の人間の決定は「**顧客を名前で呼ばない** ― 盤の名札も本文も「本人」」(P-170)。
    だから**「〜さん」と呼ぶ文が 1 つでも出たら、それは名前で呼んでいる**(伏せ字でも同じ)。

    【実物で出た形】4 周目の封の 4 冊で、**本編は「本人」6 か所・「さん」0 か所**なのに、
    **束ねた付録の 2 ページ目だけ「上に行くほど〇〇さんが良く」**だった(実測)。
    実名ではないので `check_no_real_name`(項目 11)では落ちない。
    **顧客には埋め忘れの穴に見え、名札が 2 通りになる**(P-176 と同じ家族)。

    【出どころ】付録 1(`_mid.py`)の呼び方は **pipeline 側の `REPORT_DISPLAY_NAME`**
    (= `deliver.ts --name` に渡した値)から来る**別の道**で、本編の名札の 1 か所
    (`exit_body.py` の既定「本人」)を通らない。**`_mid.py` は「さん」を自分で付けていない**
    (実測 2026-09-29。付けていたと私は一度書いたが誤り)― つまり「さん」が出るのは
    **流す側が `--name` に「〜さん」を渡したとき**だけである。

    【なぜ「さん」で見るか】「呼び方の語」を機械で見分けることはできないが、
    **決定が「名前で呼ばない」なので、敬称が出ていないことは機械で見られる。**
    これは床であって天井ではない ― 別の呼び方(「あなた」など)は捕まえない。
    **呼び方の決定が変わったら、この検査も変える**(決定を写している検査なので)。
    """
    for label, pages in (("本人用", personal), ("見本用", sample), ("付録", appendix)):
        hits = [i + 1 for i, t in enumerate(pages) if "さん" in squeeze(norm(t))]
        if hits:
            problems.append(
                f"{label}の {hits} ページ目が顧客を「〜さん」と呼んでいる"
                "(2026-09-29 の人間の決定: 名前で呼ばない ― 呼び方は「本人」の 1 通り。"
                "付録 1 の呼び方は pipeline の REPORT_DISPLAY_NAME = deliver の --name から来る)")


def check_scope_and_mapping(personal, games, problems):
    """商品の範囲の 1 段落が**ちょうど 1 か所**。**行の折り返しを越えて数える**(`squeeze`)。

    `games` は組の局数。**その局数で作った文**をちょうど 1 か所求める ―
    局数が違う文(例: 25 局の冊子に「次の 20 局」)は 0 か所として落ちる(D1)。
    """
    joined = squeeze("".join(personal))
    count = joined.count(squeeze(norm(scope_sentence(games))))
    if count != 1:
        problems.append(
            f"商品の範囲の 1 段落が {count} か所(ちょうど 1 か所。この冊子は {games} 局なので"
            f"「次の {games} 局で確かめる」でなければならない)")
    # **冒頭の断り書き 2 文**(P-162)。**局数も日付も組の名も入らない文**なので、
    # ここ(組版した PDF の側)でそのまま数えられる。
    # **(2) が無い版は顧客に出さない**(2026-09-29 の司令塔の判断) ―
    # 「最善手を教えるアプリではない」という核心の断り書きが、2 周目は本編に無かった。
    # 冒頭の 1 文目(組の名・局数・日付が入る)は**段 `exit-gate` の (vii)** が候補の JSON と照合する。
    for sentence in (OPENING_NOT_A_JUDGE, OPENING_APPENDIX):
        n = joined.count(squeeze(norm(sentence)))
        if n != 1:
            problems.append(f"冒頭の断り書きが {n} か所(ちょうど 1 か所): {sentence}")


def check_term_lines(personal, problems):
    """**用語の 4 文が本編にちょうど 1 回ずつ在る**(器の単独束 C-3。2026-09-30)。

    【何を数えるか】**文**(`TERM_LINES` の 2 つ目)。**語は数えない** ―
    「第 1 候補」「分かれ道」は本文に何度も出るので、語の数では定義が在るか分からない。
    【折り返し】組版は文を行に折るので `squeeze` で空白を落としてから探す(門の他の検査と同じ流儀)。
    【なぜ落とすのか】この 4 文が抜けた冊子は、**いちばん使う語が定義されないまま顧客に届く**
    (5 人目の感想「第一候補 = ソフトの最善手か」がその状態で出た)。
    """
    joined = squeeze("".join(personal))
    for term, sentence in TERM_LINES:
        n = joined.count(squeeze(norm(sentence)))
        if n != 1:
            problems.append(f"用語「{term}」の説明が {n} か所(ちょうど 1 か所)")


def check_moved_to_appendix(md_text, personal, appendix, problems):
    """検査 9(付録へ回した節)。**両側を見る** ― 印の付いた節が
    **本編の PDF に出ない**こと、かつ**付録の PDF に出る**こと(器の単独束 C-4。2026-09-30)。

    【なぜ両側か】片側だけ見ると片方が腐る(P-171 の型)。
    本編から外れたのに付録に組まれなければ、**顧客が読む表がどこにも出ない** ―
    それは「消えた」であって「移した」ではない。逆に、外れていないのに付録にも出れば**二重に出る。**
    【何を照合するか】節の**見出しの文**(`### …`)と、**表の 1 行目の左端の言葉**。
    PDF は折り返しで行が変わるので、**行ではなく語**で見る(`check_name_agrees` と同じ流儀)。
    【印が無ければ何も言わない】印を付ける段はまだ無い顧客(既に送った冊子)でも通る。
    """
    _keep, moved = EI.split_appendix_sections(md_text)
    if not moved:
        return
    # `page_texts` は**ページごとの文字列**を返す(番号は付かない)。**空白を落として**から探す ―
    # 組版は見出しも折るので、そのままでは出ているものを「無い」と数える(`squeeze` の説明のとおり)。
    personal_text = squeeze("".join(personal))
    appendix_text = squeeze("".join(appendix))
    for title, section in moved:
        words = [squeeze(line[4:]) for line in section.split("\n") if line.startswith("### ")]
        words = [w for w in words if w]
        if not words:
            problems.append(f"検査 9: 付録へ回す節「{title}」に見出し(### )が無い(照合する語が取れない)")
            continue
        for word in words:
            if word in personal_text:
                problems.append(
                    f"検査 9: 付録へ回した節の見出し「{word}」が**本編の PDF に出ている**"
                    "(印が付いているのに本編から外れていない ― 二重に出る)")
            if word not in appendix_text:
                problems.append(
                    f"検査 9: 付録へ回した節の見出し「{word}」が**付録の PDF に無い**"
                    "(本編から外したのに付録に組まれていない ― 顧客が読む文がどこにも出ない)")


# ==================== ⑧ の門: 節「お預かりした問い」(2026-10-01)====================
#
# **`SECTIONS` に足さない**(司令塔の判断 2026-10-01。計画 §6 の判断 1)。
# `check_sections` は `SECTIONS` の全行を必須にする(「減るのは落とす」)ので、
# **表に 7 行目として足すと、問いが 0 件の顧客の本編が門を通れなくなる。**
# だから**別の検査**にし、位置も `SECTIONS` ではなく**行番号で留める**
# (`role_of` が None を返す「間に増えた任意の節」の枠のまま置く)。
QUESTION_HEADING = "お預かりした問い"
# 節が座る場所(「ひとことで」の**直後** = 間に別の見出しが無い)。
QUESTION_AFTER_ROLE = "ひとことで"
# 節の長さの持ち分(司令塔の判断 2026-10-01。計画 §6 の判断 2)。
#
# **これはページ数の門(検査 2)を置き換えない。** 顧客が変われば本編の残り
# (数の個数・群の数・局数)も伸びるので、**節が 200 文字を守ってもページは増えうる** ―
# 越えたときに落ちるのは検査 2 であって、こちらではない。
# **この門の値打ちは「⑥ が文を書いた時点で落ちる = 早く分かる」ことだけ**で、安全の保証ではない。
# 実測(2026-10-01、見本用側): いまの道具の出力の余裕は 240 文字、この節を入れて 96 文字。
MAX_QUESTION_SECTION_CHARS = 200


def question_heading_lines(md_text):
    """節「お預かりした問い」の見出しの行番号(0 起算)を**全部**返す。"""
    return [line_no for line_no, text in heading_lines(md_text) if text.startswith(QUESTION_HEADING)]


def question_section_body(md_text):
    """節「お預かりした問い」の**中身**(見出しの行を含まない)を 1 本の文字列で返す。
    節が無ければ None。長さを数えるのはこの文字列(空白と改行は落とす)。

    **印(`<!-- ans: … -->` の家族)は数えない**(2026-10-05。司令塔の訂正 2026-10-01: 印は印字されないので
    文字数の門が数える理由が無い ― 顧客が 1 文字も読まない 29 文字が、顧客に出る文の枠を削っていた)。
    剥くのは `check_answer.strip_marks` の 1 か所(文法の隣)。**数える側のここだけ**を直した。
    """
    heads = question_heading_lines(md_text)
    if not heads:
        return None
    lines = md_text.split("\n")
    at = heads[0]
    end = len(lines)
    for line_no, _ in heading_lines(md_text):
        if line_no > at:
            end = line_no
            break
    return "".join(CA.strip_marks(line).strip() for line in lines[at + 1:end])


def check_question_section(md_text, question_count, problems):
    """**G-4・G-5・G-7。**節「お預かりした問い」の 有無・位置・長さ。

    `question_count` は `observation-request.json` の `customerQuestions[]` の件数。
    **`None` = 渡されていない**(件数が分からない)。そのときは**有無を判定しない** ―
    0 件だと決めつけると、問いが在る顧客の節を「余った節」として落としてしまう。
    位置と長さは、節が在るなら件数が分からなくても見られるので見る。
    """
    heads = question_heading_lines(md_text)
    if len(heads) > 1:
        problems.append(f"⑧: 節「{QUESTION_HEADING}」が {len(heads)} 個(ちょうど 1 つが要る)")
        return
    if not heads:
        # **0 = 0 で通る**(問いが無い顧客には節ごと出ない。「問いは無かった」とも書かない)。
        if question_count:
            problems.append(
                f"⑧: お預かりした問いが {question_count} 件あるのに節「{QUESTION_HEADING}」が本編に無い"
            )
        return
    if question_count == 0:
        problems.append(
            f"⑧: お預かりした問いが 0 件なのに節「{QUESTION_HEADING}」が本編に在る"
            "(問いが無い顧客には出さない)"
        )
    at = heads[0]
    # ---- 位置(G-5)。**「ひとことで」の直後** = 間に別の見出しが無い ----
    anchor = section_positions(md_text).get(QUESTION_AFTER_ROLE)
    if anchor is None:
        pass  # 「ひとことで」の不在は `check_sections` が落とす(二重に言わない)
    elif at < anchor:
        problems.append(
            f"⑧: 節「{QUESTION_HEADING}」が「{QUESTION_AFTER_ROLE}」より前に在る(直後が要る)"
        )
    else:
        between = [text for line_no, text in heading_lines(md_text) if anchor < line_no < at]
        if between:
            problems.append(
                f"⑧: 節「{QUESTION_HEADING}」が「{QUESTION_AFTER_ROLE}」の直後でない"
                f"(間に {between} が在る)"
            )
    # ---- 長さ(G-7)----
    body = question_section_body(md_text)
    if len(body) > MAX_QUESTION_SECTION_CHARS:
        problems.append(
            f"⑧: 節「{QUESTION_HEADING}」の中身が {len(body)} 文字"
            f"(上限 {MAX_QUESTION_SECTION_CHARS})"
        )


# ==================== ⑧ の門: 却下済みの用語の文が出ないこと(2026-10-01)====================
#
# **用語の表は 2 か所に在る**が、**寄せない・照合しない**(司令塔の判断 2026-10-01。計画 §6 の判断 3)。
# - TS `findingTexts.GLOSSARY`(5 項目)を描くのは `render_front.py` **1 か所だけ = 却下済みの 6 冊形**
# - 出口(30p 正本)の道は `exit_candidates` → `TERM_LINES`(4 項目)
# - **重なる 2 語(第 1 候補・分かれ道)の文は一致していない**ので、照合の試験を足せば即座に赤になり、
#   足すには顧客に出る文を書き換えることになる
#
# だから足すのは **1 本だけ**: **出口の本編に TS 側の文が出ないこと**。
# **これが赤くなる日 = `render_front` が出口に戻った日**で、そのとき 1 か所へ寄せる判断をする。
#
# 断片は **その文にしか出ない短い部分**。**TS が文を書き換えたら試験が赤くなる**
# (`check_structure_test.py` の `test_g8_fragments_are_in_ts` が `findingTexts.ts` を読んで確かめる) ―
# 写しを置いたまま黙って効き目が消える道を閉じるため。
GLOSSARY_FRAGMENTS = (
    ("第 1 候補", "エンジンが最も良いとした手"),
    ("分かれ道", "第 1 候補より 600 以上低かった"),
)


def check_no_glossary_text(md_text, problems):
    """**G-8。**却下済みの 6 冊形の用語の文が出口の本編に出ていないこと。"""
    for term, fragment in GLOSSARY_FRAGMENTS:
        if fragment in md_text:
            problems.append(
                f"⑧: 却下済みの 6 冊形の用語の文が本編に出た(「{term}」= 「{fragment}」)。"
                "出口の用語は TERM_LINES の 4 行"
            )


def main(argv):
    out_dir, mine, rest, source_indexes, optional = parse_args(argv)
    problems = []

    with open(mine["--honbun-md"], encoding="utf-8") as f:
        md_text = f.read()
    with open(mine["--page-index"], encoding="utf-8") as f:
        index = json.load(f)
    # **本編の索引**(`exit_body.py` が書く)。検査 4 が「差 = 対応表のページ数」を見るのに使う。
    # **無ければ検査 4 が落ちる**(黙って「差は 1」に戻らない ― 戻れば 26 局以上の顧客で嘘になる)。
    honbun_index = None
    if mine["--honbun-index"]:
        with open(mine["--honbun-index"], encoding="utf-8") as f:
            honbun_index = json.load(f)

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
    check_pages(personal, sample, appendix, honbun_index, problems)
    check_sample_difference(personal, sample, honbun_index, problems)
    check_boards(md_text, index, personal, problems)
    check_appendix_pages(index, appendix, problems)
    check_moved_to_appendix(md_text, personal, appendix, problems)
    check_term_lines(personal, problems)
    # ---- ⑧ の門(2026-10-01)。節「お預かりした問い」と、却下済みの用語の文 ----
    # **件数は `--request` から取る。渡されなければ有無を判定せず、黙らずに声に出す**
    # (0 件だと決めつけると、問いが在る顧客の節を「余った節」として落としてしまう)。
    if optional["--request"]:
        request = CA.load_json(optional["--request"])
        question_count = len(request.get("customerQuestions") or [])
    else:
        question_count = None
        print("注記: --request が渡されていないので、節「お預かりした問い」の有無は判定しない"
              "(位置と長さは節が在れば見る)", file=sys.stderr)
    check_question_section(md_text, question_count, problems)
    check_no_glossary_text(md_text, problems)
    # 局数は材料から取る(`check_answer` が読んだ patient の 1 本目 = 今回の組)。
    # **`summary.games` を使う** ― `exit_cover.numbers_of` が既にここを読んでいる(出どころを 2 つにしない)。
    # 実物では `len(games)` と一致するが(25 = 25 を実測)、**宣言されている数はこちら**。
    games = CA.load_json(args.patients[0][0])["summary"]["games"] if args.patients else 0
    check_scope_and_mapping(personal, games, problems)
    person = CA.load_json(args.patients[0][0]).get("person") if args.patients else None
    check_name_agrees(personal, appendix, person, problems)
    check_no_real_name(personal, sample, appendix, person, problems)
    check_one_referent(personal, sample, appendix, problems)
    check_bundled_index(index, source_indexes, problems)

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
