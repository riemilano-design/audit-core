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
# 【新しい判定・新しい文言を 1 つも作らない】
# - 数の拾い方: `check_answer.scan_numbers()` ― **検査 1 が見るのと同じ規則**。
#   別に数えると「門が数える数」と「検査 1 が見る数」が食い違う(`Board` が 4 実装に
#   散った P-111 と同じ病気)。2026-09-29 にあちらから切り出した。
# - 節の見分け: `check_structure.heading_matches()`(`SECTIONS` の表が正本)
# - 本数: `check_structure.HONBUN_P1_FACT_COUNT`・`BOARD_COUNT`(正本 §1)
# - 印の文法: `check_answer.POS_TAG_RE`・`MENU_TAG_RE`
# - 文の検査: `check_answer.check_answer()` をそのまま呼ぶ(禁止語・数・指し手の照合)
# - 下書きだけの見出し・書き手への注: `exit_candidates.DRAFT_ONLY_HEADINGS`・`NOTE_PREFIX`
#   (**書いた側が正本**。門に写すと、見出しを直したとき門だけが古い名前を探して黙る)
#
# 【候補の一覧は「md に印字したもの」と同じ】`exit_candidates.py` が md と JSON を
# **同じ値から**書く(`board_marks`・`p1_numbers`)。だから「候補 JSON に在る」は
# 「下書きに印字されていた」と同じ意味になる ― **印字していない数を門が許す道が無い。**
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_answer as CA          # noqa: E402
import check_structure as CS       # noqa: E402
import exit_candidates as EC       # noqa: E402
import exit_index as EI            # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


class ExitGateError(Exception):
    pass


# ==================== 本編を節に割る ====================
def sections_of(md_text):
    """`## ` の見出しで割る。返り値 = `[(見出しの文, [その節の行…])]`。

    `# ` の表題と、最初の `## ` より前の行(商品の範囲の 1 段落など)は**どの節にも入れない**
    ― 節の中身を数えるための割り方であって、文書全体の検査ではない
    (文書全体は `check_answer.check_answer()` が見る)。
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


def without_draft_only(lines):
    """下書きだけの節(`### 候補 …`・`### 下限 …`)の中の行を落とす(2026-09-29)。

    **検査 (vi) がこれらの節の削除を求めているので、(ii) が中の数に苦情を言うのは無駄である** ―
    実物で **「数 5 が候補に無い」「数 2 が候補に無い」** が出た(見出し「候補 1: 発見(材料が出した 5 種類)」
    「候補 2: 同じ型が何局で起きたか」の中の数字)。**書き手の一覧に、消せば消える苦情を混ぜない。**
    見出しの一覧は `exit_candidates.DRAFT_ONLY_HEADINGS` が正本(写さない)。
    """
    out = []
    skipping = False
    for line in lines:
        if line.startswith("#"):
            # **見出しの行そのものも落ちる**(下の `if not skipping` で外れる)。
            # 2026-09-29: ここに `continue` を置いていたが**等価**だった(変異が黙って気づいた)。
            skipping = any(line.strip() == h.strip() for h in EC.DRAFT_ONLY_HEADINGS)
        if not skipping:
            out.append(line)
    return out


def section_lines(sections, role):
    """その役割の節の行。無ければ None(節が無いこと自体は器の門〈項目 1〉の仕事)。"""
    for heading, lines in sections:
        if CS.heading_matches(role, heading):
            return lines
    return None


# ==================== 数を数える ====================
# 番号つき箇条書きの頭(「1. 」)。**これは書き手が選んだ数ではない**ので数から外す。
ORDERED_ITEM_RE = re.compile(r"^\s*\d+\.\s")


def number_claims(lines):
    """行の並びから「文中の数の主張」の**異なる値**を、出た順に返す。

    **拾い方は `check_answer.scan_numbers()` の 1 か所**(印の中の数字と ISO 日付は外れる)。
    ただし**上限は 0 を渡す** ― あちらの既定(9 以下は単独では見ない)は検査 1 の都合で、
    こちらは「書き手が選んだ数がちょうど 3 つか」を数える。実物の p1 は「6 局」のような
    **1 桁を含む**ので、9 以下を見ないと**4 つ目の数が門をすり抜ける**。

    **上限を持たない代わりに、数えたものを全部報告する。**多く数えたときは書き手が一覧を見て
    言い換えられる(見える形で止まる)。少なく数えるほうが危ない ― 黙って通るため。

    数に入れないもの: 番号つき箇条書きの頭(`1. `)と、行動の印(`<!-- menu: M3 -->` の 3)。
    どちらも書き手が選んだ数ではない。**`check_answer.py` 側は触っていない** ―
    あちらは 9 以下を見ないので、この 2 つがもともと問題にならない。

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
        line = CA.MENU_TAG_RE.sub(lambda m: " " * len(m.group(0)), raw)
        line = ORDERED_ITEM_RE.sub(" ", line)
        ratio, fractions, percents, plains = CA.scan_numbers(line, small_max=0)
        if ratio:
            # 「倍」「割」は `check_answer.check_answer()` が落とす。ここで二重に言わない。
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
    """印の中身の空白を 1 つに詰める(`check_answer.py` が PDF の本文に使うのと同じ流儀)。

    組のラベルに空白が入る(「3 分」)ので、**空白を消すのではなく詰める**。
    """
    return re.sub(r"\s+", " ", inner).strip()


def pos_marks(lines):
    return [normalize_mark(m.group(1)) for line in lines for m in CA.POS_TAG_RE.finditer(line)]


def menu_marks(lines):
    return [m.group(1) for line in lines for m in CA.MENU_TAG_RE.finditer(line)]


# ==================== 検査 ====================
def check_todo(raw_md, problems):
    """(i) 選ぶ場所が残っていないか。

    **書いた側の記録の節も含めて**見る(`strip_dev_section` を通さない)。
    あちらに残った `TODO` も「まだ選んでいない」であり、**顧客に見えないから良い話ではない**。
    """
    count = raw_md.count(EC.TODO)
    if count:
        problems.append(f"(i) 選ぶ場所が {count} か所残っている({EC.TODO})")


def check_opening(raw_md, cands, problems):
    """(vii) 冒頭の段落の文が**1 文ずつ、ちょうど 1 回**在るか(P-162)。

    **候補の JSON の `opening` と突き合わせる** ― 文の型は
    `check_structure.opening_paragraph` が正本で、ここに写しを持たない。

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


def check_p1(sections, cands, problems):
    """(ii) P1 が**事実ちょうど 3 本**で、**節の中の数が全部候補に在る**か。

    【なぜ「事実の本数」で数えるか】最初は「異なる値でちょうど 3 つ」にしたが、
    **書き手がそれでは書けなかった**(2026-09-29)。人間の線「局数で数える・**分母を付ける**」と
    両立しない ― 「18 局のうち 6 局」だけで既に 2 値になり、3 本目の事実が書けない。
    分母を落とせば、封をした読みが弱点に挙げた「分母の無い見出し」を作り直すことになる。
    **実物 2 件(3 人目の試作・4 人目の本人用 p1)は、どちらも「事実 3 本」で値は 10 個以上**だった。
    本数は `check_structure.HONBUN_P1_FACT_COUNT` が正本。

    【「箇条書き以外の行の数は箇条書きの部分集合」は入れない】司令塔の提案に入っていたが、
    **その根拠として引かれた実物そのものが落ちる** ― 3 人目の 1 文は「2 局ありました」「97 / 236」を
    使っており、どれも箇条書きに出ていない(実測 2026-09-29)。
    **守りたい 2 つ(候補に無い数・事実が足りない)は、下の 2 つの検査でどちらも捕まる。**
    """
    lines = section_lines(sections, "ひとことで")
    if lines is None:
        problems.append("(ii) 「ひとことで」の節が無い")
        return
    # **事実 = 箇条書きの行**(`- `)。表の行・1 文の解説・空行は事実として数えない。
    facts = [line for line in lines if line.lstrip().startswith("- ")]
    want = CS.HONBUN_P1_FACT_COUNT
    if len(facts) != want:
        problems.append(f"(ii) 「ひとことで」の事実(箇条書き)が {len(facts)} 本(ちょうど {want} 本にする)")
    # **節の中のすべての数**を照合する(箇条書きでも 1 文でも。分数は左右とも)。
    # **下書きだけの節は外す** ― (vi) が削除を求めている節の数に苦情を言わない(2026-09-29)。
    claims = number_claims(without_draft_only(lines))
    allowed = {int(x["number"]) for x in cands.get("p1Numbers") or []}
    if not allowed:
        problems.append("(ii) 候補の JSON に p1Numbers が無い(候補の段を回し直す)")
        return
    for n in claims:
        if n not in allowed:
            problems.append(f"(ii) 数 {n} が候補に無い(下書きに印字された数から選ぶ)")


def check_p1_reaches_the_actions(sections, cands, problems):
    """(viii) **P1 の事実が、行動のページに届いているか**(P-164。2026-09-29 の司令塔の判断)。

    【なぜ門にするか】4 人目(18 局版)と 5 人目(25 局版)の実物を突き合わせて測った ―
    **18 局版は p1 の 3 本すべてが p3 に届いている**(2 本は行動の「根拠:」に**同じ数・ほぼ同じ文**で
    引かれ、3 本目は「長く考えた手で崩れる形は出ていません」= **行動にしない理由**として明示)。
    **25 局版は 3 本のうち 0 本。** 人間の判断「18 局版のほうが診断として一段上。理由は数字の量ではなく
    **観測 → 解釈 → 行動のつながり**」。2 周目の批評でも 2 席が「p1 と行動の断絶」を挙げた。

    【どう測るか】**書き手が何を選ぶかは強制しない。選んだものがつながっているかだけを見る。**
    - 事実の数に**行動の根拠の分数の分子と分母の両方**が出ていれば「届いている」。
    - 届いていない事実は **1 本まで**許す。ただし**節に「無いものは無いと書きます。」が在るときだけ**
      (= 18 局版の 3 本目の型。**行動にしない理由を書いた**ことの印)。

    【なぜ「事実ごとに固定文」ではなく「節に 1 つ」か】**実物を読んで決めた** ― 4 人目のあの尾の文は
    **3 本目の箇条書きの中ではなく、その後の別の段落**に在る(実測 2026-09-29)。
    事実の行の中に求めると、**手本にした実物そのものが落ちる。**
    """
    lines = section_lines(sections, "ひとことで")
    if lines is None:
        return  # 節が無いことは (ii) が言う
    body = without_draft_only(lines)
    facts = [line for line in body if line.lstrip().startswith("- ")]
    fractions = cands.get("actionFractions")
    if fractions is None:
        problems.append("(viii) 候補の JSON に actionFractions が無い(候補の段を回し直す)")
        return
    pairs = [(int(f["numerator"]), int(f["denominator"])) for f in fractions]
    unreached = []
    for fact in facts:
        nums = set(number_claims([fact]))
        if any(a in nums and b in nums for a, b in pairs):
            continue
        unreached.append(fact)
    allowance = 1 if any(EI.NOTHING_TO_HIDE_SENTENCE in line for line in body) else 0
    if len(unreached) > allowance:
        heads = "・".join(f.lstrip("- ").strip()[:30] for f in unreached)
        problems.append(
            f"(viii) 行動の根拠につながらない事実が {len(unreached)} 本"
            f"(許されるのは {allowance} 本): {heads}"
            + ("" if allowance else " ― 行動にしないものを 1 本置くなら、節に"
                                    f"「{EI.NOTHING_TO_HIDE_SENTENCE}」を書く"))


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


def check_p2(sections, cands, problems):
    """(iii) P2 の盤の印がちょうど 2 つ・全部が候補に在るか。"""
    lines = section_lines(sections, "局面で見る")
    if lines is None:
        problems.append("(iii) 「局面で見る」の節が無い")
        return
    marks = pos_marks(lines)
    want = CS.BOARD_COUNT
    if len(marks) != want:
        problems.append(f"(iii) 盤の印が {len(marks)} 個(ちょうど {want} 個にする)")
    allowed = {normalize_mark(m) for m in cands.get("boards") or []}
    if not allowed:
        problems.append("(iii) 候補の JSON に boards が無い(候補の段を回し直す)")
        return
    for mark in marks:
        if mark not in allowed:
            problems.append(f"(iii) 盤の印「{mark}」が候補に無い")


def check_p3(sections, cands, problems):
    """(iv) P3 の行動が、下限を通った候補の中だけか。"""
    lines = section_lines(sections, "試せること")
    if lines is None:
        problems.append("(iv) 「試せること」の節が無い")
        return
    marks = menu_marks(lines)
    if not marks:
        problems.append("(iv) 行動の印(<!-- menu: M… -->)が 1 つも無い")
    passed = set(cands.get("menuPassed") or [])
    if not passed:
        problems.append("(iv) 候補の JSON に menuPassed が無い(候補の段を回し直す)")
        return
    for mark in marks:
        if mark not in passed:
            problems.append(f"(iv) 行動 {mark} は下限を通っていない(通ったのは {sorted(passed)})")


def check_sentences(raw_md, ctx, problems):
    """(v) 文が `check_answer.py` を通るか。**判定はあちらのまま**(ここで言い換えない)。"""
    for line_no, why, line in CA.check_answer(raw_md, ctx):
        problems.append(f"(v) {line_no}: {why}: {line.strip()[:100]}")


def check_draft_leftovers(raw_md, problems):
    """(vi) 候補の節・落ちた一覧・書き手への注が消えているか。"""
    for heading in EC.DRAFT_ONLY_HEADINGS:
        if heading in raw_md:
            problems.append(f"(vi) 下書きだけの節が残っている: {heading}")
    notes = raw_md.count(EC.NOTE_PREFIX)
    if notes:
        problems.append(f"(vi) 書き手への注が {notes} か所残っている({EC.NOTE_PREFIX}…)")


# ==================== 本体 ====================
def parse_own_args(argv):
    own = {"candidates": None}
    rest = []
    i = 0
    while i < len(argv):
        flag = argv[i]
        if flag == "--candidates":
            value = argv[i + 1] if i + 1 < len(argv) else None
            if value is None or value.startswith("--"):
                raise ExitGateError("--candidates に値が無い")
            own["candidates"] = value
            i += 2
            continue
        rest.append(flag)
        i += 1
    if own["candidates"] is None:
        raise ExitGateError("足りない引数: --candidates(候補の段が出した JSON)")
    return own, rest


def run(own, rest):
    args = CA.parse_args(rest)
    repo_root = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
    ctx = CA.build_materials(args, repo_root)
    with open(args.markdown_path, encoding="utf-8") as f:
        raw_md = f.read()
    with open(own["candidates"], encoding="utf-8") as f:
        cands = json.load(f)

    # 節に割るのは**顧客が読む側だけ**(書いた側の記録の節は節の中身に混ぜない)。
    sections = sections_of(CA.strip_dev_section(raw_md))

    problems = []
    check_todo(raw_md, problems)
    check_opening(raw_md, cands, problems)
    check_p1(sections, cands, problems)
    check_p1_reaches_the_actions(sections, cands, problems)
    check_no_unit_mismatch(raw_md, cands, problems)
    check_p2(sections, cands, problems)
    check_p3(sections, cands, problems)
    check_sentences(raw_md, ctx, problems)
    check_draft_leftovers(raw_md, problems)
    return problems


def main(argv):
    own, rest = parse_own_args(argv)
    problems = run(own, rest)
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
