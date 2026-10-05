# -*- coding: utf-8 -*-
# 段 `exit-gate` の**検査の汎用部**(Audit Core T-5/I-8。2026-10-06 に `exit_gate.py` から**そのまま写して**移した)。
#
# 【この module が持たないもの】将棋・冊子の定数を 1 つも持たない ― 節の役割名・本数(3・2)・
#   `<!-- TODO: 選ぶ -->`・下書きだけの見出し・固定文・印の文法・数の拾い方・型の字・伏せる語は、
#   **全部 `GateRules` / `AggRules` で呼ぶ側から渡される**(将棋側 `exit_gate.py`・`exit_fill.py` が
#   `check_answer`・`check_structure`・`exit_candidates`・`exit_index`・`exit_fill` の正本から組む)。
#   ここに写しを置かない(置けば、正本を直したとき門だけが古い値を探して黙る)。
# 【この module が持つもの】判定の機構だけ ― `## ` で節に割る、数の主張を数える、印を拾う、
#   「渡された集合に在るか」「本数が合うか」「問いごとに印が 1 つか」「集計行の数と合うか」。
#   **文言(問題の 1 行)は `exit_gate.py` 時代の字のまま**(G-9 の記録がこの字で固定されている)。
# 【判定を 2 つにしない】⑥(`exit_fill.agg_marks_for`)もこの module の `agg_line_missing` を呼ぶ。
# 【依存】標準ライブラリだけ(`lib/core_boundary.test.ts` が走査する)。
import re
from collections import namedtuple


class ExitGateError(Exception):
    """名前は `exit_gate.py` 時代のまま。`exit_gate.ExitGateError` はこの class そのもの(別名)。"""


# 門の規則の束。**欠けた欄は namedtuple が組み立てで落とす**(黙って既定値を入れない)。
GateRules = namedtuple("GateRules", [
    "strip_dev_section",        # callable(md) -> md。書いた側の記録の節を落とす
    "heading_matches",          # callable(role, heading) -> bool。節の見分け
    "p1_role", "p2_role", "p3_role",   # 節の役割名(数・盤・行動)
    "p1_fact_count", "board_count",    # 本数
    "todo_marker", "draft_only_headings", "note_prefix",   # 下書きの印・見出し・書き手への注
    "nothing_to_hide_sentence",        # (viii) 行動にしないものを 1 本置くときの固定文
    "ans_section_head", "ans_statuses",   # (x) 節の見出しの頭・状態の語
    "scan_numbers",             # callable(line, small_max) -> (倍割, 分数, 割合, 単独)
    "menu_tag_re", "pos_tag_re", "agg_tag_re", "ans_tag_re", "ratio_word_re",
    "agg_rules_of",             # callable() -> AggRules。(xi) の型からの再構成に要る(遅延)
])

# (xi) の型からの再構成の規則。型の表は ⑥ の定数の持ち主(`exit_fill.py`)が組む。
AggRules = namedtuple("AggRules", [
    "strip_marks",      # callable(text) -> text。印を剥く
    "reading_prefix",   # 事実部と読み部の区切りの字
    "templates_of",     # callable(cands) -> [(名, 正規表現)]
    "mask_reading",     # callable(text) -> text。読み部で伏せるもの(用語の語・指し手の字)
    "scan_numbers",     # callable(line, small_max)
    "menu_tag_re",
])


def sections_of(md_text):
    """`## ` ごとに `(見出し, 行の一覧)` へ割る。

    `# ` の表題と、最初の `## ` より前の行(商品の範囲の 1 段落など)は**どの節にも入れない**
    ― 節の中身を数えるための割り方であって、文書全体の検査ではない
    (文書全体は呼ぶ側の文の検査が見る)。
    """
    out = []
    current = None
    for line in md_text.split("\n"):
        if line.startswith("## "):
            current = (line[3:], [])
            out.append(current)
            continue
        if current is not None:
            current[1].append(line)
    return out


def without_draft_only(lines, draft_only_headings):
    """節の中の**下書きだけの小節**(`### 候補 1: …` など)を落とす。

    **検査 (vi) がこれらの節の削除を求めているので、(ii) が中の数に苦情を言うのは無駄である** ―
    実物で **「数 5 が候補に無い」「数 2 が候補に無い」** が出た(見出し「候補 1: 発見(材料が出した 5 種類)」
    「候補 2: 同じ型が何局で起きたか」の中の数字)。**書き手の一覧に、消せば消える苦情を混ぜない。**
    見出しの一覧は呼ぶ側が渡す(写さない)。
    """
    out = []
    skipping = False
    for line in lines:
        if line.startswith("#"):
            # **見出しの行そのものも落ちる**(下の `if not skipping` で外れる)。
            # 2026-09-29: ここに `continue` を置いていたが**等価**だった(変異が黙って気づいた)。
            skipping = any(line.strip() == h.strip() for h in draft_only_headings)
        if not skipping:
            out.append(line)
    return out


def section_lines(sections, role, heading_matches):
    for heading, lines in sections:
        if heading_matches(role, heading):
            return lines
    return None


# ==================== 数を数える ====================

# 番号つき箇条書きの頭(「1. 」)。**これは書き手が選んだ数ではない**ので数から外す。
ORDERED_ITEM_RE = re.compile(r"^\s*\d+\.\s")


def number_claims(lines, scan_numbers, menu_tag_re):
    """行の一覧から「書き手が書いた数」を**異なる値**で拾う(出た順)。

    **拾い方は渡された `scan_numbers` の 1 か所**(印の中の数字と ISO 日付は外れる)。
    ただし**上限は 0 を渡す** ― あちらの既定(9 以下は単独では見ない)は検査 1 の都合で、
    こちらは「書き手が選んだ数がちょうど 3 つか」を数える。実物の p1 は「6 局」のような
    **1 桁を含む**ので、9 以下を見ないと**4 つ目の数が門をすり抜ける**。
    **上限を持たない代わりに、数えたものを全部報告する。**多く数えたときは書き手が一覧を見て
    言い換えられる(見える形で止まる)。少なく数えるほうが危ない ― 黙って通るため。

    数に入れないもの: 番号つき箇条書きの頭(`1. `)と、行動の印(`<!-- menu: M3 -->` の 3)。
    どちらも書き手が選んだ数ではない。
    分数(「68 局のうち 5 局」)は**左右の両方を数える** ― どちらも書き手が選んだ数であり、
    片方だけ照合すると、もう片方に材料に無い数を書ける。
    **異なる値**で数える理由: 「ひとことで」の 1 文が、上に挙げた 3 つの数のどれかを
    もう一度使うのは自然な書き方である。出た回数で数えると、**まともな文が落ちる**。
    逆に、**候補に無い 4 つ目の数**と**3 つ未満**はどちらもこの数え方で捕まる。
    """
    values, seen = [], set()

    def add(n):
        if n not in seen:
            seen.add(n)
            values.append(n)

    for raw in lines:
        line = menu_tag_re.sub(lambda m: " " * len(m.group(0)), raw)
        line = ORDERED_ITEM_RE.sub(" ", line)
        ratio, fractions, percents, plains = scan_numbers(line, small_max=0)
        if ratio:
            # 「倍」「割」は文の検査が落とす。ここで二重に言わない。
            continue
        for a, b, _span in fractions:
            add(a)
            add(b)
        for n in percents:
            add(n)
        for n in plains:
            add(n)
    return values


# ==================== 印を拾う ====================

def normalize_mark(inner):
    """印の中身の空白を 1 つに詰める(PDF の本文に使うのと同じ流儀)。

    組のラベルに空白が入る(「3 分」)ので、**空白を消すのではなく詰める**。
    """
    return re.sub(r"\s+", " ", inner).strip()


def pos_marks(lines, pos_tag_re):
    return [normalize_mark(m.group(1)) for line in lines for m in pos_tag_re.finditer(line)]


def menu_marks(lines, menu_tag_re):
    return [m.group(1) for line in lines for m in menu_tag_re.finditer(line)]


# ==================== 検査 ====================

def check_todo(raw_md, problems, todo_marker):
    """(i) 選ぶ場所が残っていないか。
    **書いた側の記録の節も含めて**見る(`strip_dev_section` を通さない)。
    あちらに残った `TODO` も「まだ選んでいない」であり、**顧客に見えないから良い話ではない**。
    """
    count = raw_md.count(todo_marker)
    if count:
        problems.append(f"(i) 選ぶ場所が {count} か所残っている({todo_marker})")


def check_opening(raw_md, cands, problems):
    """(vii) 冒頭の段落の文が**1 文ずつ、ちょうど 1 回**在るか(P-162)。
    **候補の JSON の `opening` と突き合わせる** ― 文の型は候補を作る側の正本で、ここに写しを持たない。
    **なぜ門にするか**: 2 周目の冊子は冒頭が 1 文だけで、
    **「手の良し悪しを判定するものではありません。」が本編に無いまま顧客に出た**
    (付録の表紙には在った)。書き手が消せる場所なので、**消えたら止まる**形にする。
    """
    opening = cands.get("opening")
    if not opening:
        problems.append("(vii) 候補の JSON に opening が無い(候補の段を回し直す)")
        return
    for sentence in opening:
        count = raw_md.count(sentence)
        if count != 1:
            problems.append(f"(vii) 冒頭の文が {count} か所(ちょうど 1 か所): {sentence[:40]}")


def check_p1(sections, cands, problems, rules):
    """(ii) P1 が**事実ちょうど N 本**で、**節の中の数が全部候補に在る**か。
    【なぜ「事実の本数」で数えるか】最初は「異なる値でちょうど 3 つ」にしたが、
    **書き手がそれでは書けなかった**(2026-09-29)。人間の線「局数で数える・**分母を付ける**」と
    両立しない ― 「18 局のうち 6 局」だけで既に 2 値になり、3 本目の事実が書けない。
    分母を落とせば、封をした読みが弱点に挙げた「分母の無い見出し」を作り直すことになる。
    **実物 2 件(3 人目の試作・4 人目の本人用 p1)は、どちらも「事実 3 本」で値は 10 個以上**だった。
    本数は `rules.p1_fact_count`(正本は呼ぶ側)。
    【「箇条書き以外の行の数は箇条書きの部分集合」は入れない】司令塔の提案に入っていたが、
    **その根拠として引かれた実物そのものが落ちる** ― 3 人目の 1 文は「2 局ありました」「97 / 236」を
    使っており、どれも箇条書きに出ていない(実測 2026-09-29)。
    **守りたい 2 つ(候補に無い数・事実が足りない)は、下の 2 つの検査でどちらも捕まる。**
    """
    lines = section_lines(sections, rules.p1_role, rules.heading_matches)
    if lines is None:
        problems.append(f"(ii) 「{rules.p1_role}」の節が無い")
        return
    # **事実 = 箇条書きの行**(`- `)。表の行・1 文の解説・空行は事実として数えない。
    facts = [line for line in lines if line.lstrip().startswith("- ")]
    want = rules.p1_fact_count
    if len(facts) != want:
        problems.append(f"(ii) 「{rules.p1_role}」の事実(箇条書き)が {len(facts)} 本(ちょうど {want} 本にする)")
    # **節の中のすべての数**を照合する(箇条書きでも 1 文でも。分数は左右とも)。
    # **下書きだけの節は外す** ― (vi) が削除を求めている節の数に苦情を言わない(2026-09-29)。
    claims = number_claims(without_draft_only(lines, rules.draft_only_headings), rules.scan_numbers, rules.menu_tag_re)
    allowed = {int(x["number"]) for x in cands.get("p1Numbers") or []}
    if not allowed:
        problems.append("(ii) 候補の JSON に p1Numbers が無い(候補の段を回し直す)")
        return
    for n in claims:
        if n not in allowed:
            problems.append(f"(ii) 数 {n} が候補に無い(下書きに印字された数から選ぶ)")


def check_p1_reaches_the_actions(sections, cands, problems, rules):
    """(viii) **P1 の事実が、行動のページに届いているか**(P-164。2026-09-29 の司令塔の判断)。
    【なぜ門にするか】4 人目(18 局版)と 5 人目(25 局版)の実物を突き合わせて測った ―
    **18 局版は p1 の 3 本すべてが p3 に届いている**(2 本は行動の「根拠:」に**同じ数・ほぼ同じ文**で
    引かれ、3 本目は「長く考えた手で崩れる形は出ていません」= **行動にしない理由**として明示)。
    **25 局版は 3 本のうち 0 本。** 人間の判断「18 局版のほうが診断として一段上。理由は数字の量ではなく
    **観測 → 解釈 → 行動のつながり**」。2 周目の批評でも 2 席が「p1 と行動の断絶」を挙げた。
    【どう測るか】**書き手が何を選ぶかは強制しない。選んだものがつながっているかだけを見る。**
    - 事実の数に**行動の根拠の分数の分子と分母の両方**が出ていれば「届いている」。
    - 届いていない事実は **1 本まで**許す。ただし**節に固定文(`rules.nothing_to_hide_sentence`)が在るときだけ**
      (= 18 局版の 3 本目の型。**行動にしない理由を書いた**ことの印)。
    【なぜ「事実ごとに固定文」ではなく「節に 1 つ」か】**実物を読んで決めた** ― 4 人目のあの尾の文は
    **3 本目の箇条書きの中ではなく、その後の別の段落**に在る(実測 2026-09-29)。
    事実の行の中に求めると、**手本にした実物そのものが落ちる。**
    """
    lines = section_lines(sections, rules.p1_role, rules.heading_matches)
    if lines is None:
        return  # 節が無いことは (ii) が言う
    body = without_draft_only(lines, rules.draft_only_headings)
    facts = [line for line in body if line.lstrip().startswith("- ")]
    fractions = cands.get("actionFractions")
    if fractions is None:
        problems.append("(viii) 候補の JSON に actionFractions が無い(候補の段を回し直す)")
        return
    pairs = [(int(f["numerator"]), int(f["denominator"])) for f in fractions]
    unreached = []
    for fact in facts:
        nums = set(number_claims([fact], rules.scan_numbers, rules.menu_tag_re))
        if any(a in nums and b in nums for a, b in pairs):
            continue
        unreached.append(fact)
    sentence = rules.nothing_to_hide_sentence
    allowance = 1 if any(sentence in line for line in body) else 0
    if len(unreached) > allowance:
        heads = "・".join(f.lstrip("- ").strip()[:30] for f in unreached)
        problems.append(
            f"(viii) 行動の根拠につながらない事実が {len(unreached)} 本"
            f"(許されるのは {allowance} 本): {heads}"
            + ("" if allowance else " ― 行動にしないものを 1 本置くなら、節に"
                                    f"「{sentence}」を書く"))


def check_no_unit_mismatch(raw_md, cands, problems):
    """(ix) **単位が違う分数が顧客の本編に残っていないか**(P-165。2026-09-29)。
    実物の M6 の分数「50 / 137」は、**分子が局面の数・分母が印の組の数**である
    (`read` の局面行から数え直すと、第 1 候補が捨て駒だった局面は 107。137 はその 107 局面の
    「実戦の手に付いた印」の総数)。**顧客に送った 2 周目の冊子にこの数が出ている。**
    **判定(`m6_holds`)と答え合わせの表の作りは動かさない**(判断的知識 ― 人間の承認事項)。
    **3 周目は書き手がこの行動を落とす**(司令塔の判断「(ウ)」)。
    **その落としを書き手の記憶に頼らない** ― 忘れれば、単位の違う数がまた顧客に出る。
    **候補の段が印が付いた分数を知っているのだから、門が機械で確かめられる。**
    """
    for f in cands.get("unitMismatchFractions") or []:
        pair = f"{f['numerator']} / {f['denominator']}"
        if pair in raw_md:
            problems.append(
                f"(ix) 単位が違う分数が本編に残っている: {pair}"
                f"(行動 {f['id']}) ― {f['unitMismatch']}。"
                "この行動の行と答え合わせの行を落とすこと")


def check_p2(sections, cands, problems, rules):
    """(iii) P2 の盤の印がちょうど N 個・全部が候補に在るか。"""
    lines = section_lines(sections, rules.p2_role, rules.heading_matches)
    if lines is None:
        problems.append(f"(iii) 「{rules.p2_role}」の節が無い")
        return
    marks = pos_marks(lines, rules.pos_tag_re)
    want = rules.board_count
    if len(marks) != want:
        problems.append(f"(iii) 盤の印が {len(marks)} 個(ちょうど {want} 個にする)")
    allowed = {normalize_mark(m) for m in cands.get("boards") or []}
    if not allowed:
        problems.append("(iii) 候補の JSON に boards が無い(候補の段を回し直す)")
        return
    for mark in marks:
        if mark not in allowed:
            problems.append(f"(iii) 盤の印「{mark}」が候補に無い")


def check_p3(sections, cands, problems, rules):
    """(iv) P3 の行動が、下限を通った候補の中だけか。"""
    lines = section_lines(sections, rules.p3_role, rules.heading_matches)
    if lines is None:
        problems.append(f"(iv) 「{rules.p3_role}」の節が無い")
        return
    marks = menu_marks(lines, rules.menu_tag_re)
    if not marks:
        problems.append("(iv) 行動の印(<!-- menu: M… -->)が 1 つも無い")
    passed = set(cands.get("menuPassed") or [])
    if not passed:
        problems.append("(iv) 候補の JSON に menuPassed が無い(候補の段を回し直す)")
        return
    for mark in marks:
        if mark not in passed:
            problems.append(f"(iv) 行動 {mark} は下限を通っていない(通ったのは {sorted(passed)})")


def check_draft_leftovers(raw_md, problems, rules):
    """(vi) 候補の節・落ちた一覧・書き手への注が消えているか。"""
    for heading in rules.draft_only_headings:
        if heading in raw_md:
            problems.append(f"(vi) 下書きだけの節が残っている: {heading}")
    notes = raw_md.count(rules.note_prefix)
    if notes:
        problems.append(f"(vi) 書き手への注が {notes} か所残っている({rules.note_prefix}…)")


# ==================== (x) 顧客の問いの答えの場所(2026-10-01) ====================
# 【見る 3 つ】(1) request の問いごとに印が**ちょうど 1 つ**。(2) その印が**節の中**に在る。
# (3) 印の**状態の語**が `answer_selection` と一致。
# 【無いものは飛ばして報告する】`--request` も `--answer-selection` も**任意**。
# **ただし「渡されたのに形が違う」は飛ばさず落とす** ― 無いことと壊れていることは別である。
# 印の文法・節の見出しの頭・状態の語は `rules` で渡される(写さない)。

def ans_tags_of(md_text, ans_tag_re):
    """印の一覧 `[(行番号, 問いの id, 状態の語)]`(1 起算)。"""
    out = []
    for line_no, line in enumerate(md_text.split("\n"), start=1):
        for m in ans_tag_re.finditer(line):
            out.append((line_no, m.group(1), m.group(2)))
    return out


def ans_section_lines(md_text, ans_section_head):
    """節「お預かりした問い」の**行番号の集合**(1 起算)。節が無ければ空集合。
    節の切り出しは `sections_of` と同じ流儀(`## ` の見出しから次の `## ` の直前まで)だが、
    **行番号が要る**のでここで数える ― 印がその節の中に在るかを行番号で見る。
    """
    inside, lines = False, set()
    for line_no, line in enumerate(md_text.split("\n"), start=1):
        if line.startswith("## "):
            inside = line[3:].strip().startswith(ans_section_head)
            continue
        if inside:
            lines.add(line_no)
    return lines


def question_ids_of(request):
    """request の問いの id の並び。**原文は読まない**(門は文を見ない)。
    形が違えば落とす(`ExitGateError`)― 「無い」と「壊れている」を同じに扱わない。
    """
    if not isinstance(request, dict):
        raise ExitGateError("--request の中身が object でない")
    questions = request.get("customerQuestions")
    if questions is None:
        return []
    if not isinstance(questions, list):
        raise ExitGateError("--request の customerQuestions が配列でない")
    ids = []
    for q in questions:
        if not isinstance(q, dict) or not isinstance(q.get("id"), str):
            raise ExitGateError("--request の customerQuestions に id の無い行がある")
        ids.append(q["id"])
    return ids


def selected_statuses_of(selection):
    """`answer_selection` の `{問いの id: 状態の語}`。
    **形は ⑤ の契約**(`answers[]` に問いごとにちょうど 1 行。`questionId` と `status`)。
    **形が違えば落とす** ― 黙って飛ばすと、⑤ が別の形で書いたときに**門が何も見ないまま緑になる**(いちばん危ない形)。
    """
    if not isinstance(selection, dict):
        raise ExitGateError("--answer-selection の中身が object でない")
    answers = selection.get("answers")
    if not isinstance(answers, list):
        raise ExitGateError("--answer-selection の answers が配列でない")
    out = {}
    for a in answers:
        if not isinstance(a, dict) or not isinstance(a.get("questionId"), str) \
                or not isinstance(a.get("status"), str):
            raise ExitGateError("--answer-selection の answers に questionId か status の無い行がある")
        if a["questionId"] in out:
            raise ExitGateError(f"--answer-selection の answers に同じ問い {a['questionId']} が 2 行ある")
        out[a["questionId"]] = a["status"]
    return out


def check_ans_tags(md_text, request, selection, problems, notes, rules):
    """(x) 問いごとに印がちょうど 1 つ・節の中に在る・状態の語が採用と一致。
    **問いが 0 件なら何も言わない**(0 = 0 で通る ― 「問いは無かった」と冊子に書かない顧客でも通る)。
    """
    tags = ans_tags_of(md_text, rules.ans_tag_re)
    if request is None:
        notes.append(f"(x) --request が渡されていないので問いの照合をしていない(印 {len(tags)} 件)")
        return
    ids = question_ids_of(request)
    in_section = ans_section_lines(md_text, rules.ans_section_head)
    seen = {}
    for line_no, qid, status in tags:
        seen.setdefault(qid, []).append((line_no, status))
        if qid not in ids:
            problems.append(f"(x) {line_no} 行目の印の問い「{qid}」は request に無い")
        if line_no not in in_section:
            problems.append(
                f"(x) {line_no} 行目の印が節「{rules.ans_section_head}」の外に在る"
                "(顧客は答えをその節で探す)")
        if status not in rules.ans_statuses:
            problems.append(
                f"(x) {line_no} 行目の印の状態「{status}」が決めた語でない"
                f"({'・'.join(rules.ans_statuses)})")
    for qid in ids:
        n = len(seen.get(qid, []))
        if n != 1:
            problems.append(f"(x) 問い「{qid}」の印が {n} 件(ちょうど 1 件)")
    if selection is None:
        if ids:
            notes.append(f"(x) --answer-selection が渡されていないので状態の語を照合していない(問い {len(ids)} 件)")
        return
    chosen = selected_statuses_of(selection)
    for qid in ids:
        want = chosen.get(qid)
        if want is None:
            problems.append(f"(x) 問い「{qid}」が answer_selection に無い(採用が済んでいない)")
            continue
        for line_no, status in seen.get(qid, []):
            if status != want:
                problems.append(
                    f"(x) {line_no} 行目の状態「{status}」が採用「{want}」と違う(問い {qid})")


# ==================== (xi) 本編の数の id 照合(2026-09-30) ====================
# 【何のために在るか】本編の数の行に、書き手が `<!-- agg: <集計の id> -->` の印を付ける。
# **顧客に見える文字は 1 文字も増えない**(md のコメント)。増えるのは「その数がどの集計から来たか」を
# 機械が辿れること ― 今までは「材料のどこかに在る同じ数」で通っていたので、**別の集計の同じ数**が通った。
# 【この検査が決めないこと】どの数を選ぶか・何と書くかは 1 つも決めない。
# 見るのは「印の id が packet に在るか」と「その行の数が、その集計行の数と合うか」だけ。
# 【印を書く段が無くても】**印が 0 件でも落とさない**(報告だけ)。packet が渡されなければ**飛ばすが黙らない**。

def agg_tags_of(md_text, agg_tag_re):
    """本編から `<!-- agg: <id> -->` を拾う。返り値 = `[(行番号, [id…], 行の文)]`(印が在る行だけ)。
    **1 行に複数の印を許す** ― 1 つの文が 2 つの集計の数を言うことがある
    (「25 局のうち 18 局」の 25 と 18 が別の集計行から来る場合)。
    許される数は**その行の印ぜんぶの合併**にする(片方だけの印で他方の数を苦情にしない)。
    """
    out = []
    for line_no, line in enumerate(md_text.split("\n"), 1):
        ids = [m.group(1).strip() for m in agg_tag_re.finditer(line)]
        if ids:
            out.append((line_no, ids, line))
    return out


def numbers_of_aggregate_row(row):
    """集計の 1 行が持つ「文に書ける数」= `value`・`numerator`・`denominator` の整数。
    **この 3 つの名前は packet の schema(`observation-packet.v0.1.schema.json`)の欄の名前**で、
    ここで新しい欄を作っていない。真偽値は数として数えない(python では `True` が 1 になる)。
    """
    out = set()
    for key in ("value", "numerator", "denominator"):
        v = row.get(key)
        if isinstance(v, int) and not isinstance(v, bool):
            out.add(v)
    return out


# ==================== (xi) 型からの再構成(門の数え方の束。2026-10-05)====================
# 【なぜ】審査済みの事実の文は**数の主張でない数**を持つ ― 「第 1 候補」の 1・「10 秒以上」「4 秒以内」「+300 以上」の閾値。
# 行の数を全部集計行と比べると、封じた形の 3 本は 3 本とも印を付けられない(実測 2026-10-05、0 / 3。P-192)。
# **用語・閾値・小数を「例外の一覧」で外す道は採らない**(司令塔の裁定。表から作った出力を同じ表と比べる家族)。
# 採るのは**型からの再構成**: 行を ⑥ の型(追跡された定数 1 か所 = `exit_fill`)に当て、**穴に入った数だけ**を照合する。
# 型の字の中の数は主張ではない。**型に当たらない行は今までどおり `number_claims`**。`slot_map.json` は読まない(信じずに再構成)。
# 型の表・読み部の区切り・伏せ字は `AggRules` で渡される(この module は型の字を 1 字も持たない)。
HOLE_RE = r"(\d+)"


def fact_line_holes(line, cands, agg_rules):
    """印を剥いた行を**型の連結**に当てる。返り値 = `(当たったか, 穴の数 [int], 読み部の字)`。

    事実部 = 読み部の区切り(`agg_rules.reading_prefix`)の手前(無ければ全体)。先頭の `- ` は落とす。
    **型の連結でちょうど尽きる**(余り 0 文字)ときだけ当たり。1 本以上・順は任意。
    """
    text = agg_rules.strip_marks(line).strip()
    if text.startswith("- "):
        text = text[2:]
    prefix = agg_rules.reading_prefix
    fact, reading = (text.split(prefix, 1) + [""])[:2] if prefix in text else (text, "")
    templates = agg_rules.templates_of(cands or {})
    holes = []
    rest = fact
    while rest:
        for _name, pattern in templates:
            m = re.match(pattern, rest)
            if m:
                holes.extend(int(g) for g in m.groups())
                rest = rest[m.end():]
                break
        else:
            return False, [], reading
    if not holes:
        return False, [], reading
    return True, holes, reading


def agg_line_missing(line, allowed, cands, agg_rules):
    """その行の数のうち、集計行の数 `allowed` に無いもの(昇順)。**型に当たれば穴の数 + 読み部の数、当たらなければ行全体**。
    ⑥(`exit_fill.agg_marks_for`)と門(`check_agg_tags`)が**同じこの 1 か所**で決める。"""
    matched, holes, reading = fact_line_holes(line, cands, agg_rules)
    if matched:
        # 読み部は型ではないので `number_claims` のまま。ただし**用語の語と指し手の字は伏せる**
        # (F-5 の照合と同じ 1 本 `agg_rules.mask_reading`。司令塔の裁定 Q1 = (イ)、2026-10-05)。
        # 線の値「(0.7)」は集計行の数ではないので、ここでは伏せない(⑥ は付けずに注記する)。
        claims = set(holes) | (set(number_claims([agg_rules.mask_reading(reading)], agg_rules.scan_numbers, agg_rules.menu_tag_re)) if reading else set())
    else:
        claims = set(number_claims([line], agg_rules.scan_numbers, agg_rules.menu_tag_re))
    return sorted(n for n in claims if n not in allowed)


def check_agg_tags(md_text, packet, problems, notes, cands, rules):
    """(xi) 印の id が packet の集計に在り、その行の数がその集計行の数と合うか。

    【拾い方は写さない】数は **この門の `number_claims()` の 1 か所**。
    【拾えないもの(測って書く)】
    - **0** は拾えない(共通の規則が「上限より大きい数」で、この門は上限 0)。
      0 を言う行の照合は効かない。**規則を 2 本に分けないためにここは直さない。**
    - **割合(%)** は照合しない ― 分数から計算した数で、集計行の欄には無い(検査 1 が見る)。
    - **倍割の語**が在る行は、共通の規則がその行の数を見ないので照合できない(報告する)。
    - **閾値(300 cp・10 秒)と局数**は集計行ではなく `provenance.thresholds`・`facts` に在るので、
      その数を言う行に印は付けられない(実測: 実物の本編で 59 行)。
    """
    tags = agg_tags_of(md_text, rules.agg_tag_re)
    if packet is None:
        notes.append(f"(xi) packet が渡されていないので id の照合をしていない(印 {len(tags)} 件)")
        return
    rows = {}
    for row in (packet.get("aggregates") or []):
        if isinstance(row, dict) and isinstance(row.get("id"), str):
            rows[row["id"]] = row
    if not tags:
        notes.append(f"(xi) 本編に集計の印が 0 件(packet の集計は {len(rows)} 行)")
        return
    for line_no, ids, line in tags:
        allowed = set()
        known = []
        for agg_id in ids:
            row = rows.get(agg_id)
            if row is None:
                problems.append(f"(xi) {line_no} 行目の印の id「{agg_id}」が packet の集計に無い")
                continue
            known.append(agg_id)
            allowed |= numbers_of_aggregate_row(row)
        if not known:
            continue
        if rules.ratio_word_re.search(line):
            notes.append(f"(xi) {line_no} 行目は倍割の語があるので数を照合していない")
            continue
        # **型からの再構成**(2026-10-05): 候補が渡されていれば型に当て、穴の数だけを照合する。
        missing = agg_line_missing(line, allowed, cands, rules.agg_rules_of())
        if missing:
            problems.append(
                f"(xi) {line_no} 行目の数 {missing} が印の集計行({'・'.join(known)})の数 "
                f"{sorted(allowed)} に無い")


# ==================== 本体(検査の順) ====================

def verify(raw_md, cands, packet, request, selection, rules, notes, check_sentences):
    """検査を**固定の順**で回し、問題の一覧を返す(`exit_gate.run` の本体。順を変えると stderr の並びが変わる)。
    `check_sentences(raw_md, problems)` は文の検査(材料が要るので呼ぶ側が渡す)。`notes` は**落とさないが黙らない報告**の受け皿。
    """
    # 節に割るのは**顧客が読む側だけ**(書いた側の記録の節は節の中身に混ぜない)。
    sections = sections_of(rules.strip_dev_section(raw_md))

    problems = []
    check_todo(raw_md, problems, rules.todo_marker)
    check_opening(raw_md, cands, problems)
    check_p1(sections, cands, problems, rules)
    check_p1_reaches_the_actions(sections, cands, problems, rules)
    check_no_unit_mismatch(raw_md, cands, problems)
    check_p2(sections, cands, problems, rules)
    check_p3(sections, cands, problems, rules)
    check_sentences(raw_md, problems)
    check_draft_leftovers(raw_md, problems, rules)
    check_agg_tags(raw_md, packet, problems, notes, cands, rules)
    # **顧客が読む側だけ**を渡す(書いた側の記録の節に印が残っていても顧客には出ない)。
    check_ans_tags(rules.strip_dev_section(raw_md), request, selection, problems, notes, rules)
    return problems
