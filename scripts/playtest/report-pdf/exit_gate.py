# -*- coding: utf-8 -*-
# STEP CUSTOMER-EXIT の段 `exit-gate` の**検査**(docs/STEP_CUSTOMER_EXIT_SPEC_2026-09-28.md §1 の表)。
#
# 【この段は人の席】書き手が本編の md で (1) 数 3 つを選び (2) 盤 2 つを選び
# (3) 行動の本数を決めて 1 行ずつ書く。**この道具は「選び終わったか」だけを見る。**
# 何を選ぶべきかは 1 つも決めない(`prose-gate`・`answer-gate` と同型 ―
# 人が埋める場所に機械が答えを入れない)。
#
# 使い方:
#   python3 -X utf8 exit_gate.py <本編.md> --candidates <exit_candidates.json> \
#     [check_answer.py と同じ引数…]
#
# 出力: rc=0 なら通過。rc=1 なら落ちた項目の一覧(1 行 1 件)を標準エラーへ。
#
# 【Audit Core T-5/I-8(2026-10-06)】判定の機構は `exit_verification.py`(将棋・冊子の定数を持たない汎用部)へ
# **そのまま**移した。このファイルは**将棋側の Adapter** ― 正本の定数を `GateRules` に束ねて渡し、
# 材料(`check_answer.build_materials`)を組み、CLI の出口(stderr の整形・rc)を持つ。
# 公開名(`sections_of`・`check_*`・`number_claims`・`agg_line_missing`・`ExitGateError` …)は**前と同じ引数**で残す
# (試験と ⑥ が使う)。
#
# 【新しい判定・新しい文言を 1 つも作らない】
# - 数の拾い方: `check_answer.scan_numbers()` ― **検査 1 が見るのと同じ規則**。
#   別に数えると「門が数える数」と「検査 1 が見る数」が食い違う(`Board` が 4 実装に
#   散った P-111 と同じ病気)。2026-09-29 にあちらから切り出した。
# - 節の見分け: `check_structure.heading_matches()`(`SECTIONS` の表が正本)
# - 本数: `check_structure.HONBUN_P1_FACT_COUNT`・`BOARD_COUNT`(正本 §1)
# - 印の文法: `check_answer.POS_TAG_RE`・`MENU_TAG_RE`・`AGG_TAG_RE`・`ANS_TAG_RE`
# - 文の検査: `check_answer.check_answer()` をそのまま呼ぶ(禁止語・数・指し手の照合)
# - 下書きだけの見出し・書き手への注: `exit_candidates.DRAFT_ONLY_HEADINGS`・`NOTE_PREFIX`
#   (**書いた側が正本**。門に写すと、見出しを直したとき門だけが古い名前を探して黙る)
# - (xi) の型の字と伏せる語: `exit_fill.AGG_RULES`(⑥ の定数の持ち主が組む。遅延 import ― ⑥ の
#   組版の import を門の起動時に起こさない。読む時点は前と同じ「印の在る行を照合するとき」)
#
# 【候補の一覧は「md に印字したもの」と同じ】`exit_candidates.py` が md と JSON を
# **同じ値から**書く(`board_marks`・`p1_numbers`)。だから「候補 JSON に在る」は
# 「下書きに印字されていた」と同じ意味になる ― **印字していない数を門が許す道が無い。**
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_answer as CA          # noqa: E402
import check_structure as CS       # noqa: E402
import exit_candidates as EC       # noqa: E402
import exit_index as EI            # noqa: E402
import exit_verification as EV     # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# 例外は汎用部の class そのもの(別名。`except EG.ExitGateError` が今までどおり効く)。
ExitGateError = EV.ExitGateError
HOLE_RE = EV.HOLE_RE
ORDERED_ITEM_RE = EV.ORDERED_ITEM_RE

# ==================== (x) の語(この段の仕様) ====================
# **正本**: `docs/NEXTGEN_CONNECTION_DESIGN_2026-09-30.md` の ⑧ の行と §3.3。
# 【顧客の PDF にどう出るか】本編の「ひとことで」の直後に節「お預かりした問い」が増え、
# 問いごとに 1 段落が出る。**答えが出ないときも同じ場所に出る**(「明確な差は確認できませんでした」)。
# **この門は顧客の文を 1 文字も作らない** ― 場所と件数と状態の語が合っているかだけを見る。
# **印の文法は `check_answer.ANS_TAG_RE` の 1 か所**(`pos`・`menu`・`agg` と同じ家族)。
ANS_SECTION_HEAD = "お預かりした問い"
# 状態の語。**正本 §3.3.3 の 3 つだけ**(ここが語の 1 か所)。
ANS_STATUSES = ("answered", "partial", "unanswerable")


def _agg_rules():
    """(xi) の型からの再構成の規則は ⑥(`exit_fill.py`)が自分の定数から組む。
    **関数の中で読む** ― `exit_fill` は組版の module も読むので、門の起動時に起こさない(前と同じ時点)。"""
    import exit_fill as EF  # noqa: E402
    return EF.AGG_RULES


# 門の規則の束。**値はここで書かず、正本から引く**(試験 test_23/24/25・x11・a16 が見張る)。
GATE_RULES = EV.GateRules(
    strip_dev_section=CA.strip_dev_section,
    heading_matches=CS.heading_matches,
    p1_role="ひとことで",
    p2_role="局面で見る",
    p3_role="試せること",
    p1_fact_count=CS.HONBUN_P1_FACT_COUNT,
    board_count=CS.BOARD_COUNT,
    todo_marker=EC.TODO,
    draft_only_headings=EC.DRAFT_ONLY_HEADINGS,
    note_prefix=EC.NOTE_PREFIX,
    nothing_to_hide_sentence=EI.NOTHING_TO_HIDE_SENTENCE,
    ans_section_head=ANS_SECTION_HEAD,
    ans_statuses=ANS_STATUSES,
    scan_numbers=CA.scan_numbers,
    menu_tag_re=CA.MENU_TAG_RE,
    pos_tag_re=CA.POS_TAG_RE,
    agg_tag_re=CA.AGG_TAG_RE,
    ans_tag_re=CA.ANS_TAG_RE,
    ratio_word_re=CA.RATIO_WORD_RE,
    agg_rules_of=_agg_rules,
)


# ==================== 公開名(前と同じ引数。判定は `exit_verification` の 1 か所) ====================

sections_of = EV.sections_of
normalize_mark = EV.normalize_mark
check_opening = EV.check_opening
check_no_unit_mismatch = EV.check_no_unit_mismatch
question_ids_of = EV.question_ids_of
selected_statuses_of = EV.selected_statuses_of
numbers_of_aggregate_row = EV.numbers_of_aggregate_row


def without_draft_only(lines):
    return EV.without_draft_only(lines, GATE_RULES.draft_only_headings)


def section_lines(sections, role):
    return EV.section_lines(sections, role, GATE_RULES.heading_matches)


def number_claims(lines):
    return EV.number_claims(lines, GATE_RULES.scan_numbers, GATE_RULES.menu_tag_re)


def pos_marks(lines):
    return EV.pos_marks(lines, GATE_RULES.pos_tag_re)


def menu_marks(lines):
    return EV.menu_marks(lines, GATE_RULES.menu_tag_re)


def check_todo(raw_md, problems):
    return EV.check_todo(raw_md, problems, GATE_RULES.todo_marker)


def check_p1(sections, cands, problems):
    return EV.check_p1(sections, cands, problems, GATE_RULES)


def check_p1_reaches_the_actions(sections, cands, problems):
    return EV.check_p1_reaches_the_actions(sections, cands, problems, GATE_RULES)


def check_p2(sections, cands, problems):
    return EV.check_p2(sections, cands, problems, GATE_RULES)


def check_p3(sections, cands, problems):
    return EV.check_p3(sections, cands, problems, GATE_RULES)


def check_sentences(raw_md, ctx, problems):
    """(v) 文が `check_answer.py` を通るか。**判定はあちらのまま**(ここで言い換えない)。材料が要るので将棋側に残る。"""
    for line_no, why, line in CA.check_answer(raw_md, ctx):
        problems.append(f"(v) {line_no}: {why}: {line.strip()[:100]}")


def check_draft_leftovers(raw_md, problems):
    return EV.check_draft_leftovers(raw_md, problems, GATE_RULES)


def ans_tags_of(md_text):
    return EV.ans_tags_of(md_text, GATE_RULES.ans_tag_re)


def ans_section_lines(md_text):
    return EV.ans_section_lines(md_text, GATE_RULES.ans_section_head)


def check_ans_tags(md_text, request, selection, problems, notes):
    return EV.check_ans_tags(md_text, request, selection, problems, notes, GATE_RULES)


def agg_tags_of(md_text):
    return EV.agg_tags_of(md_text, GATE_RULES.agg_tag_re)


def fact_templates(cands):
    """型の表 `[(名, 正規表現)]`。**字は `exit_fill` の定数と候補の `name` から作る**(写さない)― 持ち主は ⑥。"""
    import exit_fill as EF  # noqa: E402
    return EF.fact_templates(cands)


def fact_line_holes(line, cands):
    return EV.fact_line_holes(line, cands, _agg_rules())


def agg_line_missing(line, allowed, cands):
    return EV.agg_line_missing(line, allowed, cands, _agg_rules())


def check_agg_tags(md_text, packet, problems, notes, cands=None):
    return EV.check_agg_tags(md_text, packet, problems, notes, cands, GATE_RULES)


# ==================== 本体 ====================

def parse_own_args(argv):
    own = {"candidates": None, "packet": None, "request": None, "answer-selection": None}
    rest = []
    i = 0
    while i < len(argv):
        flag = argv[i]
        # `--packet` は**任意**(検査 (xi))。渡されなければ (xi) を飛ばして「照合していない」と報告する
        # ― 印を書く段も packet を渡す段もまだ無いので、必須にすると既にある 21 段が全部止まる。
        if flag in ("--candidates", "--packet", "--request", "--answer-selection"):
            value = argv[i + 1] if i + 1 < len(argv) else None
            if value is None or value.startswith("--"):
                raise ExitGateError(f"{flag} に値が無い")
            own[flag[2:]] = value
            i += 2
            continue
        rest.append(flag)
        i += 1
    if own["candidates"] is None:
        raise ExitGateError("足りない引数: --candidates(候補の段が出した JSON)")
    return own, rest


def run(own, rest, notes=None):
    """`notes` を渡すと、**落とさないが黙らない報告**(検査 (xi))をそこへ足す。
    渡さない呼び方を壊さないために既定は None(捨てる)。"""
    if notes is None:
        notes = []
    args = CA.parse_args(rest)
    repo_root = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
    ctx = CA.build_materials(args, repo_root)
    with open(args.markdown_path, encoding="utf-8") as f:
        raw_md = f.read()
    with open(own["candidates"], encoding="utf-8") as f:
        cands = json.load(f)
    packet = None
    if own.get("packet"):
        with open(own["packet"], encoding="utf-8") as f:
            packet = json.load(f)
    # **任意の 2 つ**(検査 (x))。渡されなければ飛ばして報告する。
    request = selection = None
    if own.get("request"):
        with open(own["request"], encoding="utf-8") as f:
            request = json.load(f)
    if own.get("answer-selection"):
        with open(own["answer-selection"], encoding="utf-8") as f:
            selection = json.load(f)

    # 検査の順は汎用部の `verify` の 1 か所(stderr の並びがその順)。文の検査だけ材料つきでここから渡す。
    return EV.verify(raw_md, cands, packet, request, selection, GATE_RULES, notes,
                     lambda md, problems: check_sentences(md, ctx, problems))


def main(argv):
    own, rest = parse_own_args(argv)
    notes = []
    problems = run(own, rest, notes)
    for n in notes:
        print(f"(報告){n}", file=sys.stderr)
    if problems:
        print("書き手の席がまだ終わっていません(直したら --from exit-gate で再開):", file=sys.stderr)
        for p in problems:
            print(f"- {p}", file=sys.stderr)
        return 1
    print("通過(選ぶ場所は残っていません)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (ExitGateError, CA.CheckAnswerError) as e:
        print(str(e), file=sys.stderr)
        sys.exit(2)
