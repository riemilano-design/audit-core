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
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_answer as CA  # noqa: E402
import check_structure as CS  # noqa: E402
import exit_index as EI  # noqa: E402


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
