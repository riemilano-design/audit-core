# -*- coding: utf-8 -*-
# ⑥ Slot filling ― 段 `exit-fill`。**⑤ が採った id から、本編のスロットを埋める。**
# 正本 docs/NEXTGEN_CONNECTION_DESIGN_2026-09-30.md の ⑥ の行、計画 docs/PLAN_EXIT_FILL_2026-10-01.md。
#
# 【顧客の PDF にどう出るか】**ここで初めて顧客の文ができる。**⑧ までの束は 1 文字も作らなかった。
# だから**作ってよい文の出どころを先に決めてある**(計画 §3 の 5 本)―
# 言い換えは ⑤ が採った `statement` だけに掛ける / 言い換えの後に必ず `check_answer` を通す /
# **⑥ は新しい固定文を作らない** / 名前は `data/` の認識を経たものだけ /
# **「普段」のような、材料の外の判断を要する語は ⑥ が決めない。**
#
# 【なぜ python か】組版と門が全部 python で、**TS で書くと `TERM_LINES` や `COUNTING_NOTES` の
# 写しが 2 か所になる**(司令塔の判断 2026-10-01)。
#
# 【⑤ の門を通っていることを前提にしない】段の順は機械で守られているが、**この道具は手でも走る。**
# **契約(`answer-selection.v0.1`)の写しを python に作らない** ― 作れば表が 2 か所になる。
# 置くのは**自分が読む欄だけの最小の検査**で、満たさなければ**止まる**
# (埋めない・既定値を入れない)。**契約を知らない読み手が、自分の使う分だけを確かめて止まる。**
# 「0 件・緑・通過は、見ている証拠ではない」を**読む側でも**守る形である(司令塔の条件)。
import hashlib
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_answer as CA  # noqa: E402
import check_structure as CS  # noqa: E402
import exit_candidates as EC  # noqa: E402
import exit_gate as EG  # noqa: E402
import exit_groups as EGR  # noqa: E402
import exit_index as EI  # noqa: E402
import board_spec as BS  # noqa: E402  ― 盤に渡す局面・向きの判断は 1 か所(exit_body と同じ)
import exit_body as EB  # noqa: E402  ― sfens.json の読み方は 1 か所
import move_text as MT  # noqa: E402  ― 指し手の字は 1 か所(renderer から移した)


class ExitFillError(Exception):
    pass


# ==================== ⑤ の出力のうち、**⑥ が読む欄だけ** ====================
#
# **契約の写しではない。**型・列挙・字の形は 1 つも見ない(それは ⑤ の門の仕事)。
# ここで見るのは「**自分が引く欄が在るか**」だけ ― 無ければ、既定値を入れずに止まる。
#
# 【なぜ `adoptedBy` を見るか】**採用の印が無い候補を冊子に出さない。**
# `exitSelect.ts` の下書きは `adoptedBy: null` を書くので、**下書きをそのまま ⑥ に通せてしまう**
# 道がある(段を飛ばして手で走らせたとき)。だから**読む側でも**空白だけでないことを見る。
SELECTION_TOP_FIELDS = ("customerRef", "packetId", "lead", "p1", "answers", "boards",
                        "actions", "adoptedBy")
# 採用の印の 3 欄(委任の条件 2「承認には根拠を書く」)。**空白だけなら止まる。**
ADOPTED_FIELDS = ("who", "at", "basis")
# 各並びの中で ⑥ が引く欄。**ここに無い欄は読まない**(読む欄が増えたらここに足す ―
# 足さなければこの検査は黙る。**床であって天井ではない**)。
SELECTION_ITEM_FIELDS = {
    "p1": ("slot", "aggregateIds", "itemRef", "readingRequired"),
    "answers": ("questionId", "status", "itemRefs", "aggregateIds"),
    "boards": ("slot", "gameId", "ply", "packetRef"),
    "actions": ("slot", "menuId", "itemRef"),
}


def _blank(value):
    """空白だけ(または文字列でない)か。**`None`・`""`・`"  "`・全角空白だけを落とす。**"""
    return not isinstance(value, str) or not value.strip()


def selection_problems(selection):
    """**⑥ が読む欄だけ**を見る。満たさないものを文字列で返す(直さない・埋めない)。"""
    out = []
    if not isinstance(selection, dict):
        return [f"⑤ の出力が object でない: {type(selection).__name__}"]
    for field in SELECTION_TOP_FIELDS:
        if field not in selection:
            out.append(f"⑥ が読む欄が無い: {field}")
    adopted = selection.get("adoptedBy")
    if not isinstance(adopted, dict):
        # **`null` の下書きがここで止まる。**
        out.append("採用の印(adoptedBy)が無い ― 採用が済むまで冊子を組まない")
    else:
        for field in ADOPTED_FIELDS:
            if _blank(adopted.get(field)):
                out.append(f"採用の印の {field} が空白だけ ― 誰が何を見て採ったかが残っていない")
    for name, fields in SELECTION_ITEM_FIELDS.items():
        rows = selection.get(name)
        if rows is None:
            continue  # 欄そのものの不在は上で言っている(二重に言わない)
        if not isinstance(rows, list):
            out.append(f"{name} が並びでない: {type(rows).__name__}")
            continue
        for i, row in enumerate(rows):
            if not isinstance(row, dict):
                out.append(f"{name}[{i}] が object でない: {type(row).__name__}")
                continue
            for field in fields:
                if field not in row:
                    out.append(f"⑥ が読む欄が無い: {name}[{i}].{field}")
    lead = selection.get("lead")
    if lead is not None and (not isinstance(lead, dict) or "itemRef" not in lead):
        out.append("⑥ が読む欄が無い: lead.itemRef")
    return out


def read_selection(path):
    """⑤ の出力を読む。**読む欄が揃っていなければ止まる**(既定値を入れない)。"""
    with io.open(path, encoding="utf-8") as f:
        selection = json.load(f)
    problems = selection_problems(selection)
    if problems:
        raise ExitFillError(
            "⑤ の出力に、⑥ が読む欄が揃っていない(" + str(len(problems)) + " 件):\n- "
            + "\n- ".join(problems))
    return selection


# ==================== `slot_map.json` の形 ====================
#
# 【何のための表か】**本編のどの文がどこから来たかを 1 行ずつ残す。**
# 顧客に見せるものではなく、**人が後から辿るため**(委任の条件 2)と、
# **組版が文を変えていないことを測るため**(`textSha256`)。
#
# 【まだ契約(schema)にしない】**記録が 3 件を超えるまで。**
# 1 件で形を決めると 2 件目で形が変わるのが分かっているため(司令塔が支持した線)。
# だから検査は**この道具の中の関数**であって、`schemas/` の JSON Schema ではない。
#
# 【`page` は ⑦ が足す】reportlab は組んだ後にしかページ番号を知らない
# (`exit_index.PageIndexRecorder` と同じ理由)。**⑥ は 6 欄で書き、⑦ が 1 欄足す。**
SLOT_MAP_COLUMNS = ("slot", "marks", "itemRef", "aggregateIds", "text", "textSha256", "page")
# **⑥ が書く欄**(`page` を除く 6 つ)。**字で持つ** ―
# 上の並びから切り出して作ると、**欄の数を変える変異が両方いっしょに動いて黙る。**
SLOT_MAP_COLUMNS_FROM_FILL = ("slot", "marks", "itemRef", "aggregateIds", "text", "textSha256")
# ⑦ が足す欄。
SLOT_MAP_COLUMNS_FROM_RENDER = ("page",)

# ⑤ がスロットの名を持たない 2 か所の名(⑤ の `slot` はそのまま使う)。
LEAD_SLOT = "lead"
ANSWER_SLOT_PREFIX = "ans."


def text_sha256(text):
    """本文の封。**本文そのものから取る**(別の字から取ると封が意味を失う)。"""
    if not isinstance(text, str):
        raise ExitFillError(f"封を取る相手が文字列でない: {type(text).__name__}")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def answer_slot(question_id):
    """問いの節の行のスロット名。**`ans.q1` の形**(⑤ の `questionId` をそのまま付ける)。"""
    if _blank(question_id):
        raise ExitFillError("問いの id が空白だけ ― スロットの名を作れない")
    return ANSWER_SLOT_PREFIX + question_id


def fill_row(slot, text, marks=(), item_ref=None, aggregate_ids=()):
    """`slot_map.json` の 1 行(**⑥ が書く 6 欄**)。封は本文から取る。"""
    if _blank(slot):
        raise ExitFillError("スロットの名が空白だけ")
    if _blank(text):
        raise ExitFillError(f"スロット {slot} の本文が空白だけ ― 空の行を表に残さない")
    return {
        "slot": slot,
        "marks": list(marks),
        "itemRef": item_ref,
        "aggregateIds": list(aggregate_ids),
        "text": text,
        "textSha256": text_sha256(text),
    }


def slot_map_problems(rows, with_page=False):
    """**表の形を見る。**`with_page` が真なら ⑦ が足した `page` も要る。"""
    out = []
    if not isinstance(rows, list):
        return [f"slot_map が並びでない: {type(rows).__name__}"]
    want = set(SLOT_MAP_COLUMNS_FROM_FILL)
    if with_page:
        want = want | set(SLOT_MAP_COLUMNS_FROM_RENDER)
    seen = {}
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            out.append(f"slot_map[{i}] が object でない: {type(row).__name__}")
            continue
        got = set(row)
        for field in sorted(want - got):
            out.append(f"slot_map[{i}] に欄が無い: {field}")
        for field in sorted(got - want):
            out.append(f"slot_map[{i}] に知らない欄が在る: {field}")
        slot = row.get("slot")
        if _blank(slot):
            out.append(f"slot_map[{i}] のスロットの名が空白だけ")
        elif slot in seen:
            out.append(f"スロット {slot} が 2 回出る(行 {seen[slot]} と {i})")
        else:
            seen[slot] = i
        if not isinstance(row.get("marks"), list):
            out.append(f"slot_map[{i}] の marks が並びでない")
        if not isinstance(row.get("aggregateIds"), list):
            out.append(f"slot_map[{i}] の aggregateIds が並びでない")
        text = row.get("text")
        if _blank(text):
            out.append(f"slot_map[{i}] の本文が空白だけ")
        elif row.get("textSha256") != text_sha256(text):
            # **封が本文と合わない = 組版か編集が文を変えた。**
            out.append(f"スロット {row.get('slot')} の封が本文と合わない")
        if with_page and "page" in row:
            # **欄の不在は上で言っている**(二重に言わない)。
            page = row["page"]
            if isinstance(page, bool) or not isinstance(page, int) or page < 1:
                out.append(f"スロット {row.get('slot')} のページが数でない: {page}")
    return out


# ==================== F-3 節「お預かりした問い」 ====================
#
# 【顧客の PDF にどう出るか】「ひとことで」の**直後**に、見出し・問いの字・答えの文・印。
# 位置と長さは ⑧ の門(G-4・G-5・G-7)が見る。**見出しの字は `check_structure` の 1 か所から**引く。
#
# 【問いを「」で囲まない】`observation-request.json` の `requestedScope.note` が
# **「人間が中継した本人の言葉。本人が書いた文字列そのものではない」**と書いている。
# 「」で囲むと**本人の字そのままだと主張する**ことになるので、囲まない。
# (`via` が「本人が書いた」に変わる日が来たら、変えるのはここ 1 か所。)
#
# 【答えの文は ⑥ が作らない】固定文は**人間が承認したものだけ**(計画 §3 の 3)。
# 下の表に無い問いは、**言い換えを通した文を呼ぶ側から渡してもらう**(⑥ は書かない)。
# **`unanswerable` の問いに渡された文は受けない** ―
# 「なぜ答えられないか」は**人間が書く文**であって、席の読みの言い換えではない。
#
# 【表の鍵は(顧客の符号, 問いの id)】**status ごとの固定文にしない。**
# この文は**その問いに固有**で、「普段と異なる戦略」「過去棋譜」と問いの中身を指している。
# 「`unanswerable` なら常にこの文」にすると、**別の問いに別の理由で答えられないときに
# 関係の無い文が出る。**承認された status と合うことも見る。
APPROVED_ANSWER_TEXTS = {
    ("c5", "q1"): ("unanswerable", EI.unanswerable_past_games),
}


def ans_mark(question_id, status):
    """検査 (x) の印。**文法は `check_answer.ANS_TAG_RE` の 1 か所**(写しを作らない)―
    組んだ字を**その正規表現に通して**確かめる。"""
    if _blank(question_id) or _blank(status):
        raise ExitFillError(f"印を組めない(問い {question_id} / 状態 {status})")
    mark = "<!-- ans: " + question_id + " " + status + " -->"
    m = CA.ANS_TAG_RE.fullmatch(mark)
    if m is None or m.group(1) != question_id or m.group(2) != status:
        raise ExitFillError(
            f"組んだ印が印の文法に合わない: {mark} ― "
            "問いの id か状態の字が、検査が読める形になっていない")
    return mark


def answer_text_of(customer_ref, question_id, status, games, supplied=None):
    """その問いの答えの文。**承認済みの表が先**。無ければ渡された文。どちらも無ければ止まる。"""
    approved = APPROVED_ANSWER_TEXTS.get((customer_ref, question_id))
    if approved is not None:
        want_status, build = approved
        if status != want_status:
            raise ExitFillError(
                f"問い {question_id} の承認済みの文は「{want_status}」のときのもので、"
                f"⑤ は「{status}」で採っている ― 人が承認した状態と合わない文を出さない")
        if supplied is not None:
            raise ExitFillError(
                f"問い {question_id} には承認済みの文が在るのに、別の文が渡された ― "
                "人間が書いた文を上書きしない")
        return build(games)
    if status == "unanswerable":
        raise ExitFillError(
            f"問い {question_id} は「answerable でない」と採られているのに、"
            "承認済みの文が無い ― **なぜ答えられないかは人間が書く文**であって、"
            "席の読みの言い換えではない(⑥ は書かない)")
    if _blank(supplied):
        raise ExitFillError(
            f"問い {question_id}({status})の文が無い ― "
            "⑥ は固定文を新しく作らない(言い換えを通した文を渡すこと)")
    return supplied


def question_section_lines(customer_ref, questions, answers, games, supplied=None):
    """節の行。**問いが 0 件なら節ごと出さない**(⑧ の G-4。「問いは無かった」とも書かない)。

    `questions` は `observation-request.json` の `customerQuestions`、
    `answers` は ⑤ の `answers`。`supplied` は 問いの id → 文(言い換えを通したもの)。
    """
    questions = list(questions or [])
    if not questions:
        return []
    by_id = {}
    for row in answers or []:
        qid = row.get("questionId")
        if qid in by_id:
            raise ExitFillError(f"⑤ の答えが問い {qid} に 2 行ある ― どちらを出すか決まらない")
        by_id[qid] = row
    out = ["## " + CS.QUESTION_HEADING, ""]
    for q in questions:
        qid = q.get("id")
        text = q.get("text")
        if _blank(qid) or _blank(text):
            raise ExitFillError(f"問いの id か字が空白だけ: {qid}")
        row = by_id.get(qid)
        if row is None:
            raise ExitFillError(
                f"問い {qid} に ⑤ の答えが無い ― 答えの無い問いを節に並べない")
        status = row.get("status")
        body = answer_text_of(customer_ref, qid, status, games,
                              (supplied or {}).get(qid))
        # **問いの字は「」で囲まない**(中継された言葉なので、本人の字だと主張しない)。
        out.append(text)
        out.append("")
        out.append(body + " " + ans_mark(qid, status))
        out.append("")
    return out


# ==================== 束 2(F-4〜F-7): 器(下書きの md)にスロットを埋める ====================
#
# 【顧客の PDF にどう出るか】「ひとことで」の太字 1 文 + 事実 3 本(読みつき)、「局面で見る」の
# 盤 2 つの見出し、「試せること」の行動の行と答え合わせの表の行が、**人が書かずに**組まれる。
# 器は段 `exit-candidates` が書いた下書きそのもので、⑥ はその**スロットの節だけ**を置き換える
# (冒頭の段落・数え方・対応表は下書きのまま。書き手への注だけ落とす)。
#
# 【文の出どころは 5 つだけ】(計画 §3 の 3)
#   packet の数 / ⑤ の `statement` の言い換え(呼ぶ側が渡す。⑥ は検査するだけ)/
#   `answer_menu.json` の行動の文(`exit_candidates` の passed 行) /
#   既存の固定文の定数(`exit_index`・`check_answer` の `name`)/ 接続の字(この module の定数)。
# **⑥ が新しく持つ字は、下の大文字の定数に全部ある**(試験が字で留める)。
#
# 【「普段」】材料の外の判定を要する語は ⑥ が決めない(人間の決定 2026-10-01)。
# 語の表は `exit_groups.LABEL_FORBIDDEN_WORDS` の 1 か所。**渡された言い換えの文の全部**に当てる
# (太字の 1 文・読みの文・答えの文)。人間が承認した固定文(`APPROVED_ANSWER_TEXTS`)は
# 人間がこの語を「判定できないもの」として使っている文なので、当てない。


def forbidden_word_problems(text, where):
    """渡された言い換えの文に ⑥ が決めてはいけない語が入っていれば 1 件ずつ返す(**検査はここ 1 か所**。
    `paraphrase_problems` が呼ぶ ― 監査の指摘 2026-10-05: 別の関数に写しがあり導線から呼ばれていなかった)。"""
    return [f"{where}: 「{word}」が入っている(⑥ が決めない語。人間の決定 2026-10-01)"
            for word in EGR.LABEL_FORBIDDEN_WORDS if word in (text or "")]


def check_supplied_words(text, where):
    """同じ検査を、止まる形で(手で呼ぶ側のため)。"""
    problems = forbidden_word_problems(text, where)
    if problems:
        raise ExitFillError(problems[0] + " ― 材料の外の判定を要する語は ⑥ が決めない")


# ---- 言い換えの検査(計画 §3 の 1 番。言い換えは `statement` だけに掛ける) ----
#
# 【何を見るか】言い換えの文に出る**数の字**と**指し手の表記**が、元の `statement` に出たものの
# **部分集合で、字も同じ**こと。値が同じでも字が違えば落とす(`3 / 4` → `75%`・`３`)。
# 【なぜ字で比べるか】値で比べると、言い換えが数を計算して別の形で書ける(割合・漢数字)。
# それは「数には掛けない」の線を越えている。字が同じなら計算は起きていない。
NUMBER_TOKEN_RE = re.compile(r"[0-9０-９]+(?:[.,][0-9０-９]+)?")


def mask_terms_and_moves(text):
    """数の字を拾う前に伏せるもの: **用語の 4 行の語**(「第 1 候補」の 1 は数の主張ではない ―
    語の表は `check_structure.TERM_LINES` の 1 か所)と**指し手の表記**(「▲３四歩」の ３ は手の一部)。

    **門 (xi) も読み部にこの 1 本を使う**(司令塔の裁定 Q1 = (イ)。2026-10-05。伏せる語の集合は
    `TERM_LINES` の 4 語だけ ― 5 語目を足すのは新しい一覧)。写しを作らない。"""
    for term, _sentence in CS.TERM_LINES:
        text = text.replace(term, " ")
    return CA.MOVE_RE.sub(" ", text)


def number_tokens(text):
    return NUMBER_TOKEN_RE.findall(mask_terms_and_moves(text))


def move_tokens(text):
    """指し手の表記。**文法は `check_answer.MOVE_RE` の 1 か所**。"""
    return [m.group(0) for m in CA.MOVE_RE.finditer(text)]


def f5_only_problems(output, statement, where):
    """**F-5 そのもの**: 言い換えの文 `output` が、元の `statement` に無い数・指し手を持っていれば 1 件ずつ返す。
    禁止語・長さは見ない(人間の GO 条件 11「F-5 通過」と「採用可能」は別項目 ― 2026-10-05)。"""
    if _blank(output):
        return [f"{where}: 言い換えの文が空白だけ"]
    if _blank(statement):
        return [f"{where}: 元の statement が無い(言い換えを照合できない)"]
    problems = []
    allowed_numbers = set(number_tokens(statement))
    for token in number_tokens(output):
        if token not in allowed_numbers:
            problems.append(
                f"{where}: 数の字「{token}」が statement に無い"
                f"(字も同じでなければ通さない。statement の数: {sorted(allowed_numbers)})")
    allowed_moves = set(move_tokens(statement))
    for move in move_tokens(output):
        if move not in allowed_moves:
            problems.append(f"{where}: 指し手「{move}」が statement に無い")
    return problems


def paraphrase_problems(output, statement, where):
    """F-5(`f5_only_problems`)+ 禁止語。⑥ の `verified_text` が通す検査(長さは `text_problems` が足す)。"""
    problems = f5_only_problems(output, statement, where)
    if _blank(output) or _blank(statement):
        return problems
    problems.extend(forbidden_word_problems(output, where))
    return problems


def item_ref_key(ref):
    if not isinstance(ref, dict) or _blank(ref.get("hypothesisId")) or \
            isinstance(ref.get("seatIndex"), bool) or not isinstance(ref.get("seatIndex"), int):
        raise ExitFillError(f"itemRef の形が違う: {ref!r}")
    return f"{ref['seatIndex']}:{ref['hypothesisId']}"


def statements_of(integration):
    """④ の統合から `itemRef → 代表の statement`。**読むのは `clusters[].itemRefs` と
    `representative.statement` だけ**(`internal` は schema に無い ― 参照できない)。"""
    out = {}
    for cluster in (integration or {}).get("clusters") or []:
        statement = ((cluster.get("representative") or {}).get("statement"))
        for ref in cluster.get("itemRefs") or []:
            out[item_ref_key(ref)] = statement
    return out


def statement_for(statements, item_ref, where):
    key = item_ref_key(item_ref)
    if key not in statements:
        raise ExitFillError(f"{where}: itemRef {key} が統合の clusters に無い")
    return statements[key]


def text_problems(text, slot, statements, item_refs, max_chars=None):
    """1 スロットの言い換えの文の問題(F-5: 数・指し手の字が statement の部分集合・禁止語。`max_chars` が在れば長さも)。
    **⑥ の `verified_text` と `--verify-texts`(言い換えの束の道具)の 1 か所。**
    `item_refs` の statement 全部を照合の母集団にする(答えは複数の候補から 1 文になる)。"""
    where = f"スロット {slot}"
    if _blank(text):
        return [f"{where}: 言い換えの文が空"]
    pool = " ".join(statement_for(statements, ref, where) or "" for ref in item_refs)
    problems = paraphrase_problems(text, pool, where)
    if max_chars is not None and len(text) > max_chars:
        problems.append(f"{where}: {len(text)} 字 ― 上限 {max_chars} 字を越えている(印の無い文なので素直に数える)")
    return problems


def verified_text(texts, slot, statements, item_refs):
    """スロット `slot` の言い換えの文。**渡されていなければ止まる**(⑥ は書かない)。"""
    text = (texts or {}).get(slot)
    if _blank(text):
        raise ExitFillError(
            f"スロット {slot} の言い換えの文が渡されていない ― "
            "⑥ は固定文を新しく作らない(言い換えを通した文を fill_texts に書くこと)")
    problems = text_problems(text, slot, statements, item_refs)
    if problems:
        raise ExitFillError("言い換えの文が statement を越えている:\n" + "\n".join(problems))
    return text


# ---- 言い換えの束の道具が呼ぶ 2 つの入口(2026-10-05。1 回限りの境界測定実験。計画 PLAN_FILL_TEXTS §7) ----
#
# 【なぜ python に入口を置くか】照合(F-5)と用語の表・禁止語の表は python の 1 か所。TS(`fillTexts.ts`)が写しを持たないように、
# **参照で渡す**(`--print-terms`)と**照合を頼む**(`--verify-texts`)の 2 つを出す。段にはしない(deliver.ts は触らない)。
PRINT_TERMS_FLAG = "--print-terms"
VERIFY_TEXTS_FLAG = "--verify-texts"


def print_terms_json():
    """用語の 4 行(`check_structure.TERM_LINES`)と禁止語(`exit_groups.LABEL_FORBIDDEN_WORDS`)を JSON で。"""
    return {"termLines": [list(pair) for pair in CS.TERM_LINES],
            "forbiddenWords": list(EGR.LABEL_FORBIDDEN_WORDS)}


def slot_item_refs(selection):
    """スロット → itemRef の一覧。lead・p1 の `readingRequired: true` の行・answers。
    **false の p1 は入れない**(読みが要らない行に文を作らせない・通さない)。"""
    out = {LEAD_SLOT: [selection["lead"]["itemRef"]]}
    for row in selection.get("p1") or []:
        if row.get("readingRequired") is True:
            out[row["slot"]] = [row["itemRef"]]
    for row in selection.get("answers") or []:
        out[answer_slot(row.get("questionId"))] = list(row.get("itemRefs") or [])
    return out


def verify_texts(texts, selection, statements, max_chars):
    """`fill_texts.json` の形の dict を照合し、スロット → 問題の一覧(空なら通過)。⑤ に無いスロットは落ちる。"""
    refs = slot_item_refs(selection)
    out = {}
    for slot, text in (texts or {}).items():
        if slot not in refs:
            out[slot] = [f"スロット {slot}: ⑤ の採用に無い(か readingRequired が false)― 文を作る場所ではない"]
            continue
        out[slot] = text_problems(text, slot, statements, refs[slot], max_chars)
    return out


def f5_verdicts(texts, selection, statements):
    """スロット → F-5 そのものを通ったか(bool)。⑤ に無いスロット・空の文は False。禁止語・長さは見ない(条件 11)。"""
    refs = slot_item_refs(selection)
    out = {}
    for slot, text in (texts or {}).items():
        if slot not in refs or _blank(text):
            out[slot] = False
            continue
        where = f"スロット {slot}"
        pool = " ".join(statement_for(statements, ref, where) or "" for ref in refs[slot])
        out[slot] = not f5_only_problems(text, pool, where)
    return out


def parse_verify_args(argv):
    """`--verify-texts <fill_texts.json> --selection <path> --seats-dir <dir> [--max-chars N]`。"""
    out = {"max-chars": None}
    i = 0
    while i < len(argv):
        flag = argv[i]
        if flag in (VERIFY_TEXTS_FLAG, "--selection", "--seats-dir", "--max-chars"):
            value = argv[i + 1] if i + 1 < len(argv) else None
            if value is None or value.startswith("--"):
                raise ExitFillError(f"{flag} に値が無い")
            out[flag[2:]] = value
            i += 2
            continue
        raise ExitFillError(f"知らない引数: {flag}")
    missing = [k for k in ("verify-texts", "selection", "seats-dir") if k not in out]
    if missing:
        raise ExitFillError("足りない引数: " + " ".join("--" + m for m in missing))
    if out["max-chars"] is not None:
        try:
            out["max-chars"] = int(out["max-chars"])
        except ValueError:
            raise ExitFillError(f"--max-chars が整数でない: {out['max-chars']!r}")
    return out


def run_verify_texts(argv, out=sys.stdout):
    own = parse_verify_args(argv)
    texts = _load(own["verify-texts"], "言い換えの文(fill_texts)")
    selection = read_selection(own["selection"])
    run_id = selection.get("runId")
    if _blank(run_id):
        raise ExitFillError("⑤ の runId が空 ― 統合の周を引けない")
    statements = statements_of(_load(os.path.join(own["seats-dir"], run_id, INTEGRATION_NAME), "統合の出力"))
    problems = verify_texts(texts, selection, statements, own["max-chars"])
    f5 = f5_verdicts(texts, selection, statements)
    json.dump({"problems": problems, "f5": f5, "checked": sorted(problems), "maxChars": own["max-chars"]}, out, ensure_ascii=False, indent=1)
    out.write("\n")
    return 1 if any(problems.values()) else 0


# ---- 太字の 1 文(F-5) ----
# **尾は封じた最終版の実物から取った字**(2026-09-29 の 9_本編_最終版.md 10 行目)。n は事実の本数。
LEAD_TAIL_TEMPLATE = " ― という読みです。数は {n} つ。"


def lead_line(lead_text, fact_count):
    if fact_count != CS.HONBUN_P1_FACT_COUNT:
        raise ExitFillError(
            f"事実が {fact_count} 本(正本は {CS.HONBUN_P1_FACT_COUNT} 本)― ⑤ の p1 を直すこと")
    return "**" + lead_text + "**" + LEAD_TAIL_TEMPLATE.format(n=fact_count)


# ---- 事実 3 本(F-4) ----
#
# 【出どころ = (D)。司令塔の判断 2026-10-01】文は `check_answer.py` の `m4_fractions`〜`m6_fractions` の
# `name`(顧客に出た審査済みの字)を、候補の JSON の `actionFractions`(= `exit_candidates.action_fractions`、
# `evidence_phrase` と同じ正本)から引く。**数は packet の集計の行から引く**(⑤ は id だけを渡す)。
# **2 つの出どころの数が食い違えば止まる**(どちらが正しいかを ⑥ が決めない)。
#
# 【接続型(「のうち、」)】`name` は「A のうち、B」の 1 本の句。封じた最終版の 3 本(M4 × 2・M5 × 1)は
# `{A} {分母} {単位}のうち、{B}が {分子}。` の形で、A の末尾が単位の語ならそれを落とす
# (「…4 秒以内だった手」+「37 手」→「…4 秒以内だった 37 手」)。**この 2 規則で 3 本が字まで再現する**
# (試験 f40〜f42 が字で留める)。
FACT_CONNECTIVE = "のうち、"
# 集計の id → (行動の id, 分数のラベル)。**数の対応は `lib/observationAggregates.ts` の booklet の期待と同じ**
# (`sideMatch.attack` ↔ M4 攻め、`sideMatch.defense` ↔ M4 自玉側、`time.quickAfterLongThink` ↔ M5)。
# ここに無い id は**印だけ**(読みの文の数の裏づけ)で、事実の文は作らない。
AGGREGATE_FRACTION_OF = {
    "sideMatch.attack": ("M4", "攻め"),
    "sideMatch.defense": ("M4", "自玉側"),
    "time.quickAfterLongThink": ("M5", ""),
}
# 【優勢後敗は別の型(司令塔の判断 (ii)。2026-10-01)】封じて送った 2 文を型として採る。
# 穴は 2 つ(packet の numerator / denominator)。**局数も閾値も値として焼かない** ―
# `+300` は字の一部(P-188 の 3 か所目。1 か所目 600・2 か所目 300 は `exit_index.COUNTING_NOTES`)。
# 「のうち、」の接続型に**乗せない**(型をそろえるために線を落とすのは逆)。
AHEAD_THEN_LOST_ID = "aheadThenLost"
AHEAD_THEN_LOST_TEMPLATE = "一度は優勢(+300 以上)になった対局が {denominator} 局。そのうち負けた対局が {numerator} 局。"
AHEAD_THEN_LOST_HOLES = 2
# 読みの尾(封じた最終版 12〜14 行目の実物の形。「。」の直後に空白無し)。
READING_PREFIX = "― 読み: "


def _int_of(row, key, where):
    value = row.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ExitFillError(f"{where} の {key} が整数でない: {value!r}")
    return value


def aggregate_rows_of(packet):
    rows = {}
    for row in (packet.get("aggregates") or []):
        if isinstance(row, dict) and isinstance(row.get("id"), str):
            rows[row["id"]] = row
    return rows


def fraction_of(candidates, menu_id, label):
    """候補の JSON の `actionFractions` から (行動の id, ラベル) の分数を**ちょうど 1 つ**引く。"""
    hits = [f for f in candidates.get("actionFractions") or []
            if f.get("id") == menu_id and (f.get("label") or "") == label]
    if len(hits) != 1:
        raise ExitFillError(
            f"候補の actionFractions に 行動 {menu_id}・ラベル「{label}」の分数が {len(hits)} 件"
            "(ちょうど 1 件が要る。候補の段を回し直す)")
    return hits[0]


def connective_fact(name, numerator, denominator, unit):
    parts = name.split(FACT_CONNECTIVE)
    if len(parts) != 2:
        raise ExitFillError(
            f"分数の名前に「{FACT_CONNECTIVE}」がちょうど 1 回でない: {name}")
    head, tail = parts
    if _blank(unit):
        raise ExitFillError(f"分数の単位が空: {name}")
    if head.endswith(unit):
        head = head[:-len(unit)]
    return f"{head} {denominator} {unit}{FACT_CONNECTIVE}{tail}が {numerator}。"


def ahead_then_lost_fact(numerator, denominator):
    return AHEAD_THEN_LOST_TEMPLATE.format(numerator=numerator, denominator=denominator)


def agg_mark(aggregate_id):
    """検査 (xi) の印。**文法は `check_answer.AGG_TAG_RE` の 1 か所**。"""
    if _blank(aggregate_id) or re.search(r"\s|-->", aggregate_id):
        raise ExitFillError(f"集計の id が印に書ける形でない: {aggregate_id!r}")
    mark = "<!-- agg: " + aggregate_id + " -->"
    m = CA.AGG_TAG_RE.fullmatch(mark)
    if m is None or m.group(1).strip() != aggregate_id:
        raise ExitFillError(f"組んだ印が印の文法に合わない: {mark}")
    return mark


def fact_text(aggregate_ids, aggregate_rows, candidates):
    """1 本の事実の文。**id ごとに型を選び、文を連ねる**(封じた 1 本目は M4 の 2 分数で 2 文)。
    返り値 = (文, 行動の根拠に届くか)。"""
    parts = []
    reaches = False
    for agg_id in aggregate_ids:
        row = aggregate_rows.get(agg_id)
        if row is None:
            raise ExitFillError(f"集計 {agg_id} が packet に無い")
        if agg_id in AGGREGATE_FRACTION_OF:
            menu_id, label = AGGREGATE_FRACTION_OF[agg_id]
            fraction = fraction_of(candidates, menu_id, label)
            numerator = _int_of(row, "numerator", f"集計 {agg_id}")
            denominator = _int_of(row, "denominator", f"集計 {agg_id}")
            if (numerator, denominator) != (int(fraction["numerator"]), int(fraction["denominator"])):
                raise ExitFillError(
                    f"集計 {agg_id} の数 {numerator} / {denominator} が、候補の分数"
                    f"(行動 {menu_id}・{label or 'ラベル無し'})の {fraction['numerator']} / "
                    f"{fraction['denominator']} と違う ― どちらが正しいかを ⑥ は決めない")
            parts.append(connective_fact(fraction["name"], numerator, denominator, fraction["unit"]))
            reaches = True
        elif agg_id == AHEAD_THEN_LOST_ID:
            parts.append(ahead_then_lost_fact(_int_of(row, "numerator", f"集計 {agg_id}"),
                                              _int_of(row, "denominator", f"集計 {agg_id}")))
    if not parts:
        raise ExitFillError(
            f"集計 {list(aggregate_ids)} から事実の文を組める型が無い"
            f"(組めるのは {sorted(AGGREGATE_FRACTION_OF)} と {AHEAD_THEN_LOST_ID})")
    return "".join(parts), reaches


def fact_bullet(fact, reading, marks=()):
    """事実の行。`reading` が None なら**事実の文だけ**(⑤ の `readingRequired: false`。P-194・司令塔の裁定 7。
    「― 読み: 」の尾を付けない ― statement が在っても付けない)。"""
    if reading is None:
        return "- " + fact + "".join(marks)
    return "- " + fact + READING_PREFIX + reading + "".join(marks)


def agg_marks_for(line, aggregate_ids, aggregate_rows, candidates=None):
    """その行に `<!-- agg: -->` を付けられるか。付けられれば印の並び、付けられなければ空と理由。

    【なぜ条件つきか(2026-10-05 に測った)】門 (xi) は**印の在る行の数の全部**が集計行の数に在ることを
    求める。ところが審査済みの事実の文は、**数の主張でない数**を持つ ― 「第 1 候補」の 1、
    「10 秒以上」「4 秒以内」「+300 以上」の閾値、読みの「(0.7)」が 7 と数えられる。
    封じた最終版の 3 本は**3 本とも**この理由で印を付けられない(測った数は試験 f60 に)。
    印を付けて門で落ちるより、**付けずに理由を声に出す** ― 集計との対応は `slot_map.json` の
    `aggregateIds` に残る。門 (xi) をどう直すかは司令塔の判断(⑥ は門を変えない)。
    """
    allowed = set()
    for agg_id in aggregate_ids:
        allowed |= EG.numbers_of_aggregate_row(aggregate_rows.get(agg_id) or {})
    # **判定は門の 1 か所**(`exit_gate.agg_line_missing`。2026-10-05: 型からの再構成 ― 型の字の中の数は主張ではない)。
    blocking = EG.agg_line_missing(line, allowed, candidates)
    if blocking:
        return [], (f"行の数 {blocking} が集計行の数 {sorted(allowed)} に無いので印を付けない"
                    "(門 (xi) が落とす。対応は slot_map の aggregateIds に残る)")
    return [agg_mark(a) for a in aggregate_ids], None


# ---- 盤 2 つ(F-6) ----
#
# 【候補に無い局面を出さない】⑤ の `packetRef` は `facts.engine[添字]` の形だけを受ける
# (文法の正本は `lib/packetRef.ts`。ここは**自分が読む列と添字だけ**を見る ― 文法の写しではない)。
# 添字の行の (gameId, ply) が ⑤ の欄と一致し、`facts.games` で局番号を引き、
# **候補の JSON の `boards` にちょうど 1 つ当たる印**を使う。当たらなければ止まる
# (= 下書きに印字されていない局面は出ない)。
# 【engine の `ply` は表示の手数】`lib/observationFacts.ts` の `engineRowsOf` は `displayPly ?? ply` を
# `ply` に置く(実測 2026-10-05: 分かれ道 404 行は `displayPly` で engine に 404 / 404 当たり、
# `branches.ply` では 141)。だから印の数は engine の `ply` そのもので、分かれ道の行は
# `displayPly == engine.ply` で引く(分かれ道であることの確認)。
#
# 【見出しの字 ― (β)。2026-10-05 の司令塔の裁定 5】送った見出しの**括弧を除いた部分列**:
#   「**11 局目 48 手目 ― 実戦 ▲４四歩打、第 1 候補は ▲８七歩成**」(穴 4・新しい語 0)。
#   束 2 の側の語の文(「実戦は自玉側の手、第 1 候補は攻めの手」)は**採られなかった**ので消した。
#   指し手の字は `move_text.py`(renderer から移した 1 か所)。局面と向きは `render_direct.py` と**同じ 3 つの判断** ―
#   局面 = `board_spec.fork_spec`(`sfens.json` の `sfens[dply-1]`。本人が指した実際の向き)、
#   向き = `board_spec.genuine_move`、字 = `move_text.mark` + `move_text.move_kanji`。USI は packet の engine 行の `actualUsi`・`top1Usi`。
# 【packet の `sfen` を字に使わない(測った 2026-10-05)】packet の局面は**本人 = 先手に正規化**されている
#   (合成の 25 局: engine 1033 行の手番は全部 b・後手の 13 局も b。USI は正規化の局面に 1582 / 1582 当たり、回した USI は 103 / 993)。
#   正規化の向きで字を組むと、後手の局で「４四」が「６六」になり、盤(`exit_body.py` は `sfens.json` の実際の向き)と食い違う。
# 【引けないとき】`REPORT_DATA_DIR` が無い / その局が `sfens.json` に無い / USI が無い → **場所だけの見出し + 注記**(黙らない)。
#   駒が局面に無い(材料の食い違い)は止まる。
# 【答え合わせ】組んだ字は `run()` の `check_answer`(検査 2: 指し手が付録 2・3 の印字に在る)を通る ―
#   renderer と同じ字になっていることの機械の照合。
ENGINE_REF_RE = re.compile(r"^facts\.engine\[(\d+)\](?:\.|$)")
BOARD_LINE_TEMPLATE = "**{game_no} 局目 {display_ply} 手目 ― 実戦 {actual_move}、第 1 候補は {top1_move}**"
BOARD_LINE_TEMPLATE_FALLBACK = "**{game_no} 局目 {display_ply} 手目**"
REPORT_DATA_DIR_ENV = "REPORT_DATA_DIR"


def move_text_for(game_id, display_ply, usi, sfens, where):
    """見出しに書く指し手の字(「▲４四歩打」)。返り値 = (字 or None, 引けなかった理由)。"""
    if not usi:
        return None, "USI が packet の行に無い"
    record = (sfens or {}).get(game_id)
    if record is None:
        return None, f"{game_id} が sfens.json に無い({REPORT_DATA_DIR_ENV} が無いか、その局が材料に無い)"
    try:
        spec = BS.fork_spec({"displayPly": display_ply, "kifuId": game_id}, record)
    except BS.BoardSpecError as e:
        return None, str(e)
    cells, turn, _hands = MT.parse_sfen(spec["sfen"])
    genuine = BS.genuine_move(usi, spec["mirrored"])
    try:
        return MT.mark(turn, spec["user_sente"]) + MT.move_kanji(cells, genuine, None), None
    except KeyError:
        raise ExitFillError(
            f"{where}: 指し手 {usi}(実際の向き {genuine})の駒が {display_ply} 手目の局面に無い ― "
            "packet と sfens.json が同じ局を見ているか確かめること")


def engine_row_of(packet, packet_ref, where):
    m = ENGINE_REF_RE.match(packet_ref if isinstance(packet_ref, str) else "")
    if m is None:
        raise ExitFillError(
            f"{where}: 盤に選べるのは facts.engine[...] の局面だけ(渡されたのは {packet_ref!r})")
    rows = (packet.get("facts") or {}).get("engine") or []
    index = int(m.group(1))
    if index >= len(rows):
        raise ExitFillError(f"{where}: facts.engine[{index}] が packet に無い(行は {len(rows)})")
    return rows[index]


def pos_mark(inner):
    mark = "<!-- pos: " + inner + " -->"
    m = CA.POS_TAG_RE.fullmatch(mark)
    if m is None or m.group(1) != inner:
        raise ExitFillError(f"組んだ印が印の文法に合わない: {mark}")
    return mark


def board_line(board, packet, candidates, sfens=None):
    """盤 1 つの見出しの行。返り値 = (行, 印の中身, 注記 or None)。"""
    where = f"盤 {board.get('slot')}"
    row = engine_row_of(packet, board.get("packetRef"), where)
    if row.get("gameId") != board.get("gameId") or row.get("ply") != board.get("ply"):
        raise ExitFillError(
            f"{where}: ⑤ の (gameId, ply) = ({board.get('gameId')}, {board.get('ply')}) が "
            f"packetRef の行 ({row.get('gameId')}, {row.get('ply')}) と違う")
    facts = packet.get("facts") or {}
    games = {g.get("gameId"): g for g in facts.get("games") or []}
    game = games.get(row["gameId"])
    if game is None:
        raise ExitFillError(f"{where}: 局 {row['gameId']} が facts.games に無い")
    display_ply = _int_of(row, "ply", f"{where} の局面")
    branch = next((b for b in facts.get("branches") or []
                   if b.get("gameId") == row["gameId"] and b.get("displayPly") == display_ply), None)
    if branch is None:
        raise ExitFillError(
            f"{where}: ({row['gameId']}, 表示の手数 {display_ply}) が facts.branches に無い ― 盤に選べるのは分かれ道")
    game_no = _int_of(game, "no", f"{where} の局")
    prefix = f"{game_no}/{display_ply} 付録3 "
    hits = [m for m in candidates.get("boards") or [] if EG.normalize_mark(m).startswith(prefix)]
    if len(hits) != 1:
        raise ExitFillError(
            f"{where}: 局面 {game_no} 局目 {display_ply} 手目 の印が候補の boards に {len(hits)} 件"
            "(ちょうど 1 件が要る ― 下書きに印字されていない局面は出さない)")
    inner = EG.normalize_mark(hits[0])
    actual, why_actual = move_text_for(row["gameId"], display_ply, row.get("actualUsi"), sfens, where)
    top1, why_top1 = move_text_for(row["gameId"], display_ply, row.get("top1Usi"), sfens, where)
    note = None
    if actual and top1:
        text = BOARD_LINE_TEMPLATE.format(game_no=game_no, display_ply=display_ply,
                                          actual_move=actual, top1_move=top1)
    else:
        text = BOARD_LINE_TEMPLATE_FALLBACK.format(game_no=game_no, display_ply=display_ply)
        note = f"{where}: 見出しに指し手を出せない({why_actual or why_top1})― 場所だけの見出しにした"
    return text + pos_mark(inner), inner, note


# ---- 数え方の群の 3 行(司令塔の裁定 3。2026-10-05) ----
#
# 【顧客の PDF にどう出るか】「数え方」の「崩れ」の定義の直後に、戦型の群ごとの行(1 群 1 行・数だけ)が入る。
# 封じた版の表(列を手で選んだもの)と読みは**書き手の字(追跡 0 件)**なので再現しない。
# 【同じ呼び出し】候補の段(`exit_candidates.build_md`)が観測の節に印字するのと**同じ** `exit_groups.lines_of` +
# `exit_candidates.CROSS_PHRASE_JP`。前置きの文は置かない(追跡された定数が無い)。読みは付けない(群の読みが ⑤ で採用されたときに決める)。
# 【置く場所】`exit_index.COUNTING_NOTES` の「崩れ」で始まる 1 本の直後。下書きに無ければ止まる(黙って節末に置かない)。
def collapse_note():
    hits = [s for s in EI.COUNTING_NOTES if s.startswith("「崩れ」")]
    if len(hits) != 1:
        raise ExitFillError(f"数え方の固定文に「崩れ」で始まる文が {len(hits)} 本(群の行を置く場所が決まらない)")
    return hits[0]


def group_lines(candidates):
    return EGR.lines_of(candidates.get("openingGroups") or [], EC.CROSS_PHRASE_JP)


def insert_group_lines(body, lines):
    """数え方の節の本文に群の行を挿す(崩れの定義の行の直後)。群が無ければそのまま。"""
    if not lines:
        return list(body)
    target = "- " + collapse_note()
    where = [i for i, line in enumerate(body) if line.strip() == target]
    if len(where) != 1:
        raise ExitFillError(f"数え方に崩れの定義の行が {len(where)} 行(群の行を置く場所が決まらない)")
    i = where[0]
    return list(body[:i + 1]) + list(lines) + list(body[i + 1:])


# ---- 試せることの固定文(司令塔の裁定 4。2026-10-05) ----
#
# 【顧客の PDF にどう出るか】見出しの直後に前文 1 文(`exit_index.selection_sentence`。**常に**)、行動の行の後に
# 線の文(`exit_candidates.threshold_sentences`。**採用された行動のうち線を持つもの**だけ、行動の順)。
# 下書きと**同じ関数呼び出し**(`exit_candidates.build_md` 969・972 行)。「行動 1 の線: 」「どちらも線を下回ったので」
# 「候補にしたものの行動にしなかったもの」「※「10秒以上」は」は**書き手の字(追跡 0 件)**なので置かない。
# 線の値そのもの(0.7)は検査 1 が数として拾わない(`threshold_numbers` の注)。
def threshold_lines(adopted, materials):
    """採用された行動の線の文。`materials` が無ければ空(試験・手回し)。判定の線は `check_answer.menu_threshold_of` の 1 か所。"""
    if materials is None:
        return []
    return EC.threshold_sentences(EC.thresholds_of([row for _slot, row in adopted], materials))


# ---- 行動と答え合わせの表(F-7) ----
#
# 文は**承認済みの表(`answer_menu.json`)の passed 行**から(`exit_candidates.menu_rows` が決めた
# 通った / 落ちた を使う ― ⑥ は判定しない)。根拠の分数は `exit_candidates.evidence_phrase` が正本。
# **passed に無い id を ⑤ が採っていれば止まる**(表に無い・下限に届かない行動は出ない)。
ACTION_SLOT_RE = re.compile(r"^act\.([1-9][0-9]*)$")
VERIFY_TABLE_SEPARATOR = "|---|---|---|"


def menu_mark(menu_id):
    mark = "<!-- menu: " + menu_id + " -->"
    m = CA.MENU_TAG_RE.fullmatch(mark)
    if m is None or m.group(1) != menu_id:
        raise ExitFillError(f"組んだ印が印の文法に合わない: {mark}")
    return mark


def adopted_action_rows(actions, passed):
    """⑤ の `actions` を slot の番号順に、passed の行と組にして返す `[(slot, 行)]`。"""
    out = []
    by_id = {r["id"]: r for r in passed}
    for action in actions or []:
        slot = action.get("slot")
        m = ACTION_SLOT_RE.match(slot if isinstance(slot, str) else "")
        if m is None:
            raise ExitFillError(f"行動のスロットの名が act.N の形でない: {slot!r}")
        menu_id = action.get("menuId")
        row = by_id.get(menu_id)
        if row is None:
            raise ExitFillError(
                f"行動 {menu_id}(スロット {slot})が下限を通った候補に無い ― "
                f"通ったのは {sorted(by_id)}(表に無い・届かない行動は出さない)")
        out.append((int(m.group(1)), slot, row))
    out.sort(key=lambda t: t[0])
    numbers = [t[0] for t in out]
    if numbers != list(range(1, len(out) + 1)):
        raise ExitFillError(f"行動のスロットの番号が 1 から連続でない: {numbers}")
    return [(slot, row) for _n, slot, row in out]


def action_line(index, row):
    """行動の 1 行。**下書きが印字する行と同じ形**(`exit_candidates.build_md` の (c))。"""
    item = row["item"]
    line = f"{index}. {item['actionCore']}{menu_mark(row['id'])}　― 根拠は{EC.evidence_phrase(row)}"
    if item.get("foundInSameData"):
        line += f"。{CA.FOUND_IN_SAME_DATA_PHRASE}。"
    return line


def verify_table_row(row):
    return f"| {row['item']['actionCore']}{menu_mark(row['id'])} | {EC.facts_cell(row)} | {EC.values_cell(row)} |"


# ---- 器 ----
def split_sections(md_text):
    """`## ` の見出しで割る。返り値 = `[(見出しの行 or None, [行…])]`。先頭の塊は見出し無し。"""
    out = [(None, [])]
    for line in md_text.split("\n"):
        if line.startswith("## "):
            out.append((line, []))
        else:
            out[-1][1].append(line)
    return out


def role_of_heading(heading_line):
    return CS.role_of(heading_line[3:].strip()) if heading_line else None


def is_note(line):
    return line.lstrip().startswith(EC.NOTE_PREFIX)


SLOT_ROLES = ("ひとことで", "局面で見る", "試せること", "答え合わせ")


def build_document(draft_md, selection, packet, candidates, questions, texts, statements, passed, games,
                   sfens=None, materials=None):
    """下書きの md のスロットの節を埋めて、(本編の md, slot_map の行, 注記) を返す。**書き込まない。**
    注記 = 落とさないが黙らない報告(印を付けなかった行・指し手を出せなかった見出しなど)。
    `sfens` = `sfens.json` の束(見出しの指し手の字。無ければ場所だけの見出し)。`materials` = 線の文の材料(無ければ線の文は無い)。"""
    sections = split_sections(draft_md)
    roles = [role_of_heading(h) for h, _ in sections]
    for role in SLOT_ROLES:
        if roles.count(role) != 1:
            raise ExitFillError(f"下書きに節「{role}」が {roles.count(role)} 個(ちょうど 1 つが要る)")

    rows = []
    notes = []
    aggregate_rows = aggregate_rows_of(packet)

    # ---- ひとことで ----
    p1 = list(selection.get("p1") or [])
    lead_ref = selection["lead"]["itemRef"]
    lead_text = verified_text(texts, LEAD_SLOT, statements, [lead_ref])
    lead = lead_line(lead_text, len(p1))
    rows.append(fill_row(LEAD_SLOT, lead, item_ref=lead_ref))
    bullets = []
    unreached = 0
    for row in p1:
        slot = row.get("slot")
        ids = list(row.get("aggregateIds") or [])
        fact, reaches = fact_text(ids, aggregate_rows, candidates)
        wants_reading = row.get("readingRequired")
        if wants_reading is True:
            reading = verified_text(texts, slot, statements, [row["itemRef"]])
        elif wants_reading is False:
            # 事実の文だけ(P-194)。**渡された文が在っても使わない** ― 黙らず注記する。
            reading = None
            if (texts or {}).get(slot) is not None:
                notes.append(f"スロット {slot}: readingRequired が false なので、渡された読みの文は使わない")
        else:
            raise ExitFillError(f"スロット {slot}: readingRequired が真偽値でない({wants_reading!r})")
        marks, why = agg_marks_for(fact_bullet(fact, reading), ids, aggregate_rows, candidates)
        if why:
            notes.append(f"スロット {slot}: {why}")
        bullet = fact_bullet(fact, reading, marks)
        bullets.append(bullet)
        rows.append(fill_row(slot, bullet, marks=marks, item_ref=row["itemRef"], aggregate_ids=ids))
        if not reaches:
            unreached += 1

    # ---- お預かりした問い(F-3。「ひとことで」の直後) ----
    answers = selection.get("answers") or []
    supplied = {}
    for row in answers:
        qid = row.get("questionId")
        slot = answer_slot(qid)
        if (texts or {}).get(slot) is not None:
            supplied[qid] = verified_text(texts, slot, statements, list(row.get("itemRefs") or []))
    question_lines = question_section_lines(selection["customerRef"], questions, answers, games, supplied)
    agg_by_qid = {row.get("questionId"): list(row.get("aggregateIds") or []) for row in answers}
    for line in question_lines:
        m = CA.ANS_TAG_RE.search(line)
        if m is not None:
            rows.append(fill_row(answer_slot(m.group(1)), line, marks=[m.group(0)],
                                 aggregate_ids=agg_by_qid.get(m.group(1), [])))

    # ---- 局面で見る ----
    boards = list(selection.get("boards") or [])
    if len(boards) != CS.BOARD_COUNT:
        raise ExitFillError(f"⑤ の盤が {len(boards)} 件(正本は {CS.BOARD_COUNT} 件)")
    board_lines = []
    for board in boards:
        line, inner, note = board_line(board, packet, candidates, sfens)
        if note:
            notes.append(note)
        board_lines.append(line)
        rows.append(fill_row(board["slot"], line, marks=[pos_mark(inner)]))

    # ---- 試せること + 答え合わせ ----
    adopted = adopted_action_rows(selection.get("actions"), passed)
    action_lines = []
    for index, (slot, row) in enumerate(adopted, start=1):
        line = action_line(index, row)
        action_lines.append(line)
        rows.append(fill_row(slot, line, marks=[menu_mark(row["id"])], item_ref=None))
    if not adopted:
        action_lines.append(EI.NO_ACTION_SENTENCE)
    table = [EC.VERIFY_TABLE_HEADER, VERIFY_TABLE_SEPARATOR] + [verify_table_row(r) for _s, r in adopted]
    selection_line = EI.selection_sentence(games)
    lines_of_threshold = threshold_lines(adopted, materials)
    lines_of_groups = group_lines(candidates)

    # ---- 組む ----
    out = []
    for heading, body in sections:
        role = role_of_heading(heading)
        if role == "ひとことで":
            out += [heading, "", lead, ""] + bullets + [""]
            if unreached:
                out += [EI.NOTHING_TO_HIDE_SENTENCE, ""]
            out += question_lines
        elif role == "局面で見る":
            out += [heading, ""]
            for line in board_lines:
                out += [line, ""]
        elif role == "試せること":
            out += [heading, "", selection_line, ""] + action_lines + [""]
            for sentence in lines_of_threshold:
                out += [sentence, ""]
        elif role == "答え合わせ":
            out += [heading, ""] + table + [""]
        else:
            if heading is not None:
                out.append(heading)
            kept = [line for line in body if not is_note(line)]
            if role == "数え方":
                kept = insert_group_lines(kept, lines_of_groups)
            out += kept
    md = "\n".join(out)
    if not md.endswith("\n"):
        md += "\n"
    problems = slot_map_problems(rows)
    if problems:
        raise ExitFillError("slot_map の形が崩れている:\n" + "\n".join(problems))
    for row in rows:
        if row["text"] not in md:
            raise ExitFillError(f"スロット {row['slot']} の本文が本編に無い(組む側の不具合)")
    return md, rows, notes


# ==================== 本体(段 `exit-fill`) ====================
#
# 使い方:
#   python3 -X utf8 exit_fill.py --selection <answer_selection.json> --packet <observation-packet.json> \
#     --request <observation-request.json> --candidates <exit_candidates.json> --md <9_本編.md> \
#     --out-slot-map <slot_map.json> --seats-dir <out/<顧客>/llm-seats> --texts <fill_texts.json> \
#     [check_answer.py と同じ材料の引数…]
#
# 【書き手の道を消さない】`--md` が在って `TODO` が無ければ、**人(か前の ⑥)が書き終えた本編**なので
# 触らずに rc=0 で退く。`TODO` が在れば下書きなので埋めて上書きする。
# 【描く前に検査】組んだ md を `check_answer.check_answer` に通し、1 件でも落ちれば**書かない**。
OWN_FLAGS = ("--selection", "--packet", "--request", "--candidates", "--md", "--out-slot-map",
             "--seats-dir", "--texts")
INTEGRATION_NAME = "integration.json"


def parse_own_args(argv):
    own = {flag[2:]: None for flag in OWN_FLAGS}
    rest = []
    i = 0
    while i < len(argv):
        flag = argv[i]
        if flag in OWN_FLAGS:
            value = argv[i + 1] if i + 1 < len(argv) else None
            if value is None or value.startswith("--"):
                raise ExitFillError(f"{flag} に値が無い")
            own[flag[2:]] = value
            i += 2
            continue
        rest.append(flag)
        i += 1
    missing = sorted(k for k, v in own.items() if v is None)
    if missing:
        raise ExitFillError("足りない引数: " + " ".join("--" + m for m in missing))
    return own, rest


def _load(path, what):
    if not os.path.exists(path):
        raise ExitFillError(f"{what}が無い: {path}")
    with io.open(path, encoding="utf-8") as f:
        return json.load(f)


def sfens_from_env(environ):
    """`REPORT_DATA_DIR`(組の順・カンマ区切り)から `sfens.json` の束を読む。無ければ空(= 見出しは場所だけ + 注記)。
    読み方は `exit_body.load_sfens` の 1 か所(監査の指摘 Mut-D。2026-10-05: この配線を試験で叩けるように関数にした)。"""
    dirs = [d for d in (environ.get(REPORT_DATA_DIR_ENV) or "").split(",") if d]
    return EB.load_sfens(dirs) if dirs else {}


def run(own, rest, out=sys.stdout):
    with io.open(own["md"], encoding="utf-8") as f:
        draft_md = f.read()
    if EC.TODO not in draft_md:
        print(f"[exit-fill] 本編の md に {EC.TODO} が無い(書き終えた本編)― 触らずに退く: {own['md']}",
              file=out)
        return 0
    selection = read_selection(own["selection"])
    packet = _load(own["packet"], "packet")
    if packet.get("packetId") != selection.get("packetId"):
        raise ExitFillError(
            f"⑤ の packetId {selection.get('packetId')} と packet の {packet.get('packetId')} が違う")
    request = _load(own["request"], "observation-request")
    candidates = _load(own["candidates"], "候補の JSON")
    texts = _load(own["texts"], "言い換えの文(fill_texts)")
    run_id = selection.get("runId")
    if _blank(run_id):
        raise ExitFillError("⑤ の runId が空 ― 統合の周を引けない")
    statements = statements_of(_load(os.path.join(own["seats-dir"], run_id, INTEGRATION_NAME), "統合の出力"))

    args = CA.parse_args(rest + [own["md"]])
    repo_root = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
    ctx = CA.build_materials(args, repo_root)
    passed, _dropped = EC.menu_rows(ctx)
    if len(args.patients) != 1:
        raise ExitFillError(f"--patient は今回の組の 1 つだけ({len(args.patients)} 件渡された)")
    games = (CA.load_json(args.patients[0][0]).get("summary") or {}).get("games")

    # 見出しの指し手の字の材料(`sfens.json`)は `exit_body.py`・`render_direct.py` と同じ `REPORT_DATA_DIR`(組の順・カンマ区切り)。
    sfens = sfens_from_env(os.environ)
    md, rows, notes = build_document(draft_md, selection, packet, candidates,
                                     request.get("customerQuestions") or [], texts, statements, passed, games,
                                     sfens=sfens, materials=ctx["materials"])
    for note in notes:
        print(f"[exit-fill] 注記: {note}", file=out)
    problems = CA.check_answer(md, ctx)
    if problems:
        raise ExitFillError("組んだ本編が check_answer を通らない(書かない):\n" + "\n".join(
            f"{line_no}: {why}: {line.strip()[:100]}" for line_no, why, line in problems))
    with io.open(own["md"], "w", encoding="utf-8") as f:
        f.write(md)
    with io.open(own["out-slot-map"], "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"wrote {own['md']}(スロット {len(rows)} 行)", file=out)
    print(f"wrote {own['out-slot-map']}", file=out)
    return 0


HERE = os.path.dirname(os.path.abspath(__file__))


def main(argv):
    if PRINT_TERMS_FLAG in argv:
        json.dump(print_terms_json(), sys.stdout, ensure_ascii=False, indent=1)
        sys.stdout.write("\n")
        return 0
    if VERIFY_TEXTS_FLAG in argv:
        return run_verify_texts(argv)
    own, rest = parse_own_args(argv)
    return run(own, rest)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (ExitFillError, CA.CheckAnswerError, EGR.ExitGroupsError) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
