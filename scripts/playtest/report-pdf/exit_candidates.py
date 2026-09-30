# -*- coding: utf-8 -*-
# STEP CUSTOMER-EXIT の段 `exit-candidates`(仕様 `docs/STEP_CUSTOMER_EXIT_SPEC_2026-09-28.md` の 36 行目の表)。
# **本編の md の下書きを作る。候補を出すだけで、選ばない。**選ぶ場所は `<!-- TODO: 選ぶ -->` で残す。
#
# 【この道具が「選ばない」とはどういうことか】
# 数を 3 つに絞る・盤を 2 つに絞る・行動の本数を決める、はすべて書き手(`exit-gate`)の仕事。
# ここは**材料に在るものを、材料の言い方のまま、数えて並べる**だけ。
# **顧客の PDF にどう出るか**: この md がそのまま出るのではない。書き手が候補から選び、
# `TODO` を消し、`exit_body.py` が PDF にする。**候補の段で顧客に出る形が決まるのは「言い方」と「数の分母」**。
#
# 【人間の線を 3 つ、候補の側に固定する(司令塔の指示 2026-09-29)】
# 1. **(a) の数は局数で数え、分母の出どころを JSON に持つ。**再現の 8 種類は「同じ型が何局で起きたか」までで、
#    **型に名前を付けない・目的を書かない**(CLAUDE.md 規則 8 の (3))。「この人は〜しない」は候補にも出さない。
# 2. **(c) は `answer_menu.json` の minN を通った項目だけ + 落ちた一覧。**承認済みの表の外から行動を作らない。
# 3. **179 秒は自動判定に入れない**(人間の決定)。時間の数が出るときは「持ち時間に到達した」の語で、
#    **「時間切れ」とは書かない**(2026-09-27 `5bb7ae9` で断定をやめた語)。
#
# 【新しい判定・新しい文言を作らない】
# - 節の見出し: `check_structure.py` の `SECTIONS`(門と同じ定数)
# - 商品の範囲の 1 段落: `check_structure.scope_sentence(局数)`(ちょうど 1 か所。**局数は型に入れる** ― D1)
# - 数え方の固定文: `exit_index.COUNTING_NOTES`(`render_front.py` から移した 1 か所)
# - 行動が minN を通ったか: `check_answer.py` の `MENU_HOLDS`・`MENU_DENOMINATOR`・`menu_verify_gate_holds`
#   (検査 4・5 と**同じ判定**。二重に作らない)
# - 再現の 8 種類: `answer_facts.py` の `bullet_11` が既に印字している 8 つの数と**同じ組**
#   (第 1 候補の 打つ・捨て駒・取る・王手 = 4、側の 攻め・守り = 2、実戦の手の 打つ・捨て駒 = 2)。
#   **語は `render_direct.py` の `TAG_JP`・`SIDE_JP` と同じ**(新しい言い方を作らない)。
#   `direct_answers.json` の `counts` が持っている数なので、**局面の数は新しく数え直さない**。
#   **局数だけを `answers[]` から数える**(仕様が「局数つきで」と言う分)。
#
# 使い方:
#   python3 -X utf8 exit_candidates.py --out-md <下書き.md> --out-json <分母の出どころ.json> \
#     --kifu-dir <g01.fixed.json のあるフォルダ> [check_answer.py と同じ引数…]
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_answer as CA        # noqa: E402
import check_structure as CS     # noqa: E402
import exit_groups as EGR       # noqa: E402
import exit_index as EI          # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

TODO = "<!-- TODO: 選ぶ -->"

# **下書きにだけ在る節の見出しと、書き手への注の頭。**
# 書き手はこれらを消してから段 `exit-gate` を通す。**門(`exit_gate.py`)はここを読む** ―
# 門に文字列を写すと、見出しを直したときに**門だけが古い名前を探して黙る**。
DRAFT_ONLY_HEADINGS = (
    "### 候補 1: 発見(材料が出した 5 種類)",
    "### 候補 2: 同じ型が何局で起きたか",
    "### 下限を通った項目",
    "### 下限に届かなかった項目(何がどれだけ足りないか)",
    # 2026-09-29 に足した(5 つ目)。**使ってよい固定文の一覧** ―
    # 書き手が選んだら本文へ移し、この節は消す(門の (vi) が残りを落とす)。
    "### 使ってよい固定文(選んだら本文へ移す)",
)
NOTE_PREFIX = "<!-- 書き手へ: "


def note(text):
    """書き手への指示を注釈にする(顧客の PDF には出ない)。頭は `NOTE_PREFIX` の 1 か所。"""
    return f"{NOTE_PREFIX}{text} -->"


class ExitCandidatesError(Exception):
    pass


# ==================== 再現の 8 種類 ====================
# **8 つの組は `answer_facts.py` の `bullet_11` と同じ。**そこが既に顧客に出している数なので、
# 候補の段で新しい統計を作らない。語も `render_direct.py` の `TAG_JP`・`SIDE_JP` と同じ。
#
# **司令塔の例文は「かつ」の形だった**(「第 1 候補が打つ手で**実戦が打たない手**だった局面」)。
# それは `bullet_11` が出していない**新しい数**(同時分布)なので、**この道具は出していない。**
# 出すかどうかは司令塔の判断に委ねる(候補に無い数は書き手が足せないので、要れば言ってほしい)。
REPRO_KINDS = (
    ("top1", "drop", "第 1 候補が駒を打つ手"),
    ("top1", "sacrifice", "第 1 候補が駒を捨てる手"),
    ("top1", "capture", "第 1 候補が駒を取る手"),
    ("top1", "givesCheck", "第 1 候補が王手"),
    # 側の語は **`check_answer.SIDE_JP` の 1 か所**から作る(P-185。2026-09-29)。
    # **写した結果、ここだけ「守り」のまま残っていた** ― 既存の試験
    # (`ReproKindsTest.test_02`)が、本編の語と食い違ったことで捕まえた(5 つ目の写し)。
    ("side", "attack", f"第 1 候補の側が{CA.SIDE_JP['attack']}"),
    ("side", "defense", f"第 1 候補の側が{CA.SIDE_JP['defense']}"),
    ("actual", "drop", "実戦の手が駒を打つ手"),
    ("actual", "sacrifice", "実戦の手が駒を捨てる手"),
)


def answers_of(direct):
    """`direct_answers.json` の `answers[]`(組をまたいで全部)。

    **取り出し方は `check_answer.direct_answers_of` が正本**(2026-09-29 にそちらへ寄せた ―
    観測 1 行が同じ取り出しを要るので、ここに写しを残すと 2 か所になる)。
    """
    return CA.direct_answers_of(direct)


def matches(answer, source, key):
    if source == "top1":
        return bool(answer["top1Tags"].get(key))
    if source == "actual":
        return bool(answer["actualTags"].get(key))
    return answer["top1Side"] == key


def repro_rows(direct):
    """8 種類の行。**局面の数は `counts` から引き、局数だけを数える。**

    `counts` を使うのは、**`answer_facts.py` が顧客に出しているのと同じ数**にするため
    (自分で数え直すと、片方だけ直る道ができる)。数え直した値が `counts` と食い違えば**落ちる**。
    """
    answers = answers_of(direct)
    if not answers:
        raise ExitCandidatesError("direct_answers.json の answers が空(分かれ道の候補を作れない)")
    total_positions = direct["totalCount"]
    total_games = len({a["gameNo"] for a in answers})
    counts = {"top1": direct["top1TagCounts"], "actual": direct["actualTagCounts"],
              "side": direct["top1SideCounts"]}
    rows = []
    for source, key, phrase in REPRO_KINDS:
        hit = [a for a in answers if matches(a, source, key)]
        want = counts[source].get(key, 0)
        if len(hit) != want:
            raise ExitCandidatesError(
                f"{phrase}: 数え直した局面 {len(hit)} が counts の {want} と合わない"
                "(材料の中で食い違っている ― どちらかが古い)")
        rows.append({"phrase": phrase, "positions": want,
                     "games": len({a["gameNo"] for a in hit})})
    return {"rows": rows, "totalPositions": total_positions, "totalGames": total_games}


# **否定の型**(「〜の必要は数からは出ていない」)は**動くはずの分数を持たない**ので、
# 本編の行動に入れない(2026-09-29 の司令塔の判断)。答え合わせの表にも載らない
# ― 載せても「次の 25 局で何が動けば当たりか」を書けないので、顧客への約束にならない。
# `verifyName` が空で `MENU_FRACTIONS` にも無い項目がこれに当たる(実物では M3・M7・M8)。
NEGATIVE_TYPE_REASON = "否定の型(動くはずの分数を持たないので答え合わせができない)"


def is_negative_type(item, fractions):
    """その項目が否定の型か。**分数も承認済みの答え合わせの文も無い**なら真。"""
    return not fractions and not item["verifyName"]


# ==================== 行動(minN) ====================
def menu_rows(ctx):
    """`answer_menu.json` の項目を**通った / 落ちた**に分ける。

    判定は `check_answer.py` の検査 4・5 と**同じ関数**(`MENU_HOLDS`・`MENU_DENOMINATOR`・
    `menu_verify_gate_holds`)。**二重に作らない** ― 作れば「候補には出るのに門が落とす」道ができる。
    """
    passed, dropped = [], []
    for item_id, item in ctx["menuItemsById"].items():
        min_n = ctx["menuMinN"][item_id]
        try:
            holds = CA.MENU_HOLDS[item_id](ctx["materials"])
            denominator = CA.MENU_DENOMINATOR[item_id](ctx["materials"])
            gate = CA.menu_verify_gate_holds(item_id, ctx["materials"], ctx["menuItemsById"])
        except CA.CheckAnswerError as e:
            dropped.append({"id": item_id, "item": item, "minN": min_n,
                            "denominator": None, "why": f"材料が足りない({e})"})
            continue
        fractions = CA.menu_fractions(item_id, ctx["materials"])
        row = {"id": item_id, "item": item, "minN": min_n, "denominator": denominator,
               "fractions": fractions}
        if not holds:
            row["why"] = "条件が成り立たない"
        elif denominator is None or denominator < min_n:
            row["why"] = f"根拠の数が下限 {min_n} に届かない(いまの分母 {denominator})"
        elif not gate:
            row["why"] = "答え合わせの数が下限に届かない"
        elif is_negative_type(item, fractions):
            row["why"] = NEGATIVE_TYPE_REASON
        else:
            passed.append(row)
            continue
        dropped.append(row)
    passed.sort(key=lambda r: r["id"])
    dropped.sort(key=lambda r: r["id"])
    return passed, dropped


# ==================== 観測 1 行(第 1 候補の印 × 実戦の印) ====================
# **2026-09-29 に足した。**人間が 09-28 に「言ってよいのはここまで」と引いた線そのもの ―
# 「第 1 候補が『打つ』で実戦が『打たない』型が 103 局面のうち ○ 局面、24 局中 ○ 局」。
# **行動にはしない。観測として出すだけ**(承認済みの表に「打つ」の項目が無いので、
# 行動にすれば表の外から行動を作ることになる)。
# **語は `render_direct.py` の `TAG_JP` から取る**(「打つ」「捨て駒」)。
# **「打たない」「見落とし」「候補に入れない」は使わない**(規則 8 (3)・人間の線)。
# **出す印だけを持つ**(`check_answer.CROSS_TAGS` と同じ集合であることを試験が見る)。
# 語は本編 p1 の言い方に合わせる(`TAG_JP` の「打つ」を含む形)。
CROSS_PHRASE_JP = {"drop": "駒を打つ手"}


def cross_line(direct, tag):
    """観測の 1 行。**分子・分母を両側に出す**(局面と局の両方)。"""
    c = CA.top1_actual_cross(direct, tag)
    what = CROSS_PHRASE_JP[tag]
    return (f"第 1 候補が{what}だった分かれ道 {c['positions']} 局面({c['games']} 局)のうち、"
            f"実戦も{what}だった局面 {c['bothPositions']}({c['bothGames']} 局)、"
            f"実戦は{what}ではなかった局面 {c['otherPositions']}({c['otherGames']} 局)。")


# ==================== 行動の根拠と答え合わせの欄(分数は `check_answer.MENU_FRACTIONS` が正本) ====================
# **3 つの出口(根拠の 1 行・動くはずの事実の欄・いまの値の欄)が同じ関数を読む。**
# 判定が見た分数をそのまま出す ― **新しい分析を足すのではない**(2026-09-29 の人間の訂正:
# 「橋が無いのではない。橋は判定ロジックに存在していた。問題はその橋を本編に出していなかったこと」)。


# **表の見出しの行は定数**(2026-09-29)。試験が見出しの行を本文行から除くのに使う
# ― **写しを持たせると、見出しを変えたときに試験が黙って本文行を数え間違える**(実測でそうなった)。
VERIFY_TABLE_HEADER = "| 試したこと | 動くはずの事実 | いまの値 |"


def _pairs(row):
    """`[(見出し, 分子, 分母), ...]`。分数を持たない項目は空。"""
    return [(f["label"], f["numerator"], f["denominator"]) for f in (row.get("fractions") or [])]


def evidence_phrase(row):
    """行動の直下に出る根拠の文。**分数を持つ項目は分数で書く。**

    持たない項目(M1・M2・M9 など)は `answer_menu.json` の `evidenceName` に落ちる
    ― **あちらは承認済みの表の文なので触らない**(2026-09-29 の司令塔の判断 (A))。
    """
    fractions = row.get("fractions")
    if not fractions:
        item = row["item"]
        return f"{item['evidenceName']}({row['denominator']}・下限 {row['minN']})"
    parts = [f"{f['name']}が {f['numerator']} / {f['denominator']}" for f in fractions]
    return "、".join(parts) + " です"


def facts_cell(row):
    """答え合わせの表の「動くはずの事実」。**分数の名前をそのまま置く。**"""
    fractions = row.get("fractions")
    if not fractions:
        return row["item"]["verifyName"]
    return "と".join(f"「{f['name']}」" for f in fractions)


def values_cell(row):
    """答え合わせの表の「いまの値」。**分子 / 分母の両方を出す。**

    2026-09-29 まではここが分母 1 つ(`137`・`404`)だった ― **列名が「いまの値」なのに値が入っていなかった。**
    `M4` は分かれ道の総数(`forkTotal` = 404)を出していたが、**判定はその数で割っていない**(P-152)。
    """
    fractions = row.get("fractions")
    if not fractions:
        return str(row["denominator"])
    parts = []
    for f in fractions:
        value = f"{f['numerator']} / {f['denominator']}"
        parts.append(f"{f['label']} {value}" if f["label"] else value)
    return "、".join(parts)


# ==================== 対応表 ====================
def mapping_rows(patient, kifu_dir):
    """局番号 ↔ 棋譜のファイル名 + 先後・手数・結果。

    **名前から日付・対局 ID が取れるときだけ列に分ける**(正本 §5 の訂正)。
    取れないときは**列ごと無くす**(空欄で出さない)。
    ファイル名は `<kifu-dir>/<id>.fixed.json` の `source`。
    """
    rows = []
    for g in patient["games"]:
        path = os.path.join(kifu_dir, f"{g['id']}.fixed.json")
        if not os.path.exists(path):
            raise ExitCandidatesError(f"固定棋譜が無い: {path}(対応表のファイル名が引けない)")
        with open(path, encoding="utf-8") as f:
            fixed = json.load(f)
        source = fixed.get("source")
        if not source:
            raise ExitCandidatesError(f"{g['id']}.fixed.json に source が無い(棋譜のファイル名)")
        rows.append({"no": g["no"], "source": source, "side": g["side"],
                     "total": g["total"], "result": g["result"]})
    return rows


# ==================== 盤の候補 ====================
# **md と JSON が同じ並びを見る。**別に並べ替えると、**md に出ていない印が JSON にだけ在る**
# (= 門が通してしまう)道ができる。
def board_fraction_note(side_match, passed, answer):
    """その局面が**どの行動の根拠の分数に入るか**の注(P-164 の項目 3。2026-09-29)。

    入らなければ `None`。**書き手への注の形で出す** ― 選び終えたら消す場所であり、
    残っていれば門 (vi) が落とす(顧客の冊子に道具の覚え書きが出ない)。

    **側は `check_answer.side_match_mark_of` が決める**(`(kifuId, displayPly)` で結合。
    合算と同じ走査から来るので、分数と食い違う道が無い)。
    **行動の名は `action_fractions` の `label` で引く** ― 「M4」を写さない。
    """
    mark = CA.side_match_mark_of(side_match, answer["kifuId"], answer["displayPly"])
    if mark is None:
        return None
    hit = [f for f in action_fractions(passed) if f["label"] == mark["label"]]
    if not hit:
        return None
    f = hit[0]
    where = "分子にも入る" if mark["inNumerator"] else "分母に入るが分子ではない"
    tail = ("実戦も同じ側の手だった局面" if mark["inNumerator"]
            else "実戦は同じ側の手ではなかった局面")
    return note(f"行動 {f['id']}・{f['label']} の根拠({f['numerator']} / {f['denominator']})の"
                f"{where}({tail})")


def board_marks(direct, side_match=None, passed=()):
    """盤の候補を、**md に印字するのと同じ順**で `(行の文, 印の中身)` の対で返す。"""
    rows = sorted(answers_of(direct),
                  key=lambda x: (-(abs(x["actualGapCp"]) if x["actualGapCp"] is not None else -1),
                                 x["gameNo"], x["displayPly"]))
    out = []
    for a in rows:
        inner = f"{a['gameNo']}/{a['displayPly']} 付録3 {a['group']}"
        text = (f"- {a['group']} の {a['gameNo']} 局目 {a['displayPly']} 手目"
                f"<!-- pos: {inner} -->")
        extra = board_fraction_note(side_match, passed, a)
        if extra:
            text += extra
        out.append((text, inner))
    return out


# ==================== 行動の根拠の分数(p1 の候補。P-164・2026-09-29) ====================
# **なぜ p1 に出すか**: 4 人目(18 局版)の p1 の 3 本は、**2 本が行動の「根拠:」と同じ数・ほぼ同じ文**で、
# 3 本目が「行動にしない理由」だった(3 本とも行動に届いている)。**5 人目(25 局版)は 0 本**。
# 人間の判断「18 局版のほうが診断として一段上。理由は数字の量ではなく観測 → 解釈 → 行動のつながり」。
#
# **切れていたのは 2 か所**で、そのうち道具の側は **`MENU_FRACTIONS` を p3 の行動の下にしか出していなかった**
# こと ― 書き手が p1 に根拠の数を選べなかった。**ここに出して選べるようにする。**
#
# **単位が違う分数は出さない**(`unitMismatch`。P-165) ― p1 に出せば穴が 1 か所から 2 か所になる。
def action_fractions(passed):
    """行動の根拠の分数を、**行動ごとに平らに**並べる(`unitMismatch` は外す)。"""
    out = []
    for row in passed:
        for f in row.get("fractions") or []:
            if f.get("unitMismatch"):
                continue
            out.append({"id": row["id"], "label": f["label"], "name": f["name"],
                        "unit": f["unit"],
                        "numerator": f["numerator"], "denominator": f["denominator"]})
    return out


def action_fraction_line(f):
    """p1 の候補の 1 行。**文と数を両方出す**(書き手が文ごと選べるように)。"""
    which = f"行動 {f['id']}" + (f"・{f['label']}" if f["label"] else "")
    return f"- 行動の根拠({which}): {f['name']}が {f['numerator']} / {f['denominator']}。"


# ==================== P1 の数の候補 ====================
# **門(`exit-gate`)が「書き手が作った数」を見つけるための一覧。**
# 出どころは **md に印字したものだけ**。印字していない数を一覧に入れると、
# **顧客の冊子に、候補に出ていない数が載る道**ができる(門が通してしまう)。
#
# **言い回しの型の数(「型が N 通りあります」)は入れない** ― それは材料の作りの話で、
# この人の対局について言える数ではない。書き手が使ったら門で落ちる(それが正しい)。
def p1_numbers(patient, repro, direct=None, passed=(), thresholds=(), long_think=None,
               side_match=None):
    # **本編の形の数**(事実の本数)。実物は「数は 3 つ。」と**冊子が自分の形を言う** ―
    # 3 人目の試作の「ひとことで」の 1 文にこの言い方が在る(実測 2026-09-29)。
    # **対局の事実ではないが、書き手が書く数である。**
    # 候補に入れない作りにしたら、**実物と同じ言い方をした書き手が門で止まった**(実測 2026-09-29)。
    # なお `check_answer.py` の検査 1 は 3 を無条件に許している(`allowedNumbers` に {1,2,3,4,5,…})ので、
    # **ここで許しても検査 1 より緩くはならない。**
    out = [{"number": CS.HONBUN_P1_FACT_COUNT, "unit": "本",
            "from": "本編の形(正本 §1: 「ひとことで」の事実は 3 本)"}]
    out.append({"number": patient["summary"]["games"], "unit": "局",
                "from": "patient_report_data.json の summary.games(この報告が見た対局の数)"})
    out.append({"number": repro["totalPositions"], "unit": "局面",
                "from": "direct_answers.json の answers(再現の表の分母)"})
    out.append({"number": repro["totalGames"], "unit": "局",
                "from": "direct_answers.json の answers に出てくる局(再現の表の分母)"})
    for r in repro["rows"]:
        out.append({"number": r["positions"], "unit": "局面",
                    "from": f"再現の表「{r['phrase']}」の局面"})
        out.append({"number": r["games"], "unit": "局",
                    "from": f"再現の表「{r['phrase']}」の局"})
    # 発見の 5 種類の数は `text`(埋まった文)に出る。**その文に実際に出た数だけ**を採る
    # (`numbers` の全部ではない ― 文に出ない値を候補にすると、印字していない数を許してしまう)。
    for f in patient["findings"]:
        # **上限 0 で拾う。**既定(9 以下は単独では見ない)で拾うと、
        # **1 桁の数が候補に入らない**まま、門(`exit_gate.py` は上限 0 で数える)が
        # 「6 局が候補に無い」と言って**まともな選択を止める**(実測 2026-09-29。
        # 3 人目の実物の p1 は aheadLossGames = 6 を使っている)。
        # **数える側と候補を作る側は同じ上限**でなければならない。
        ratio, fractions, percents, plains = CA.scan_numbers(f["text"], small_max=0)
        if ratio:
            continue
        seen = []
        for a, b, _span in fractions:
            seen += [(a, "分数の左"), (b, "分数の右")]
        seen += [(n, "割合(%)") for n in percents]
        seen += [(n, "数") for n in plains]
        for number, unit in seen:
            out.append({"number": number, "unit": unit,
                        "from": f"patient_report_data.json の findings「{f['kind']}」の text"})
    # **行動の根拠の分数の数も候補に入れる**(2026-09-29。P-164) ―
    # p1 に印字するのに候補に無ければ、**書き手が根拠の数を p1 に書くと門が止める**。
    # **印字する側と数える側は同じ集合**(P-139 と同じ型の 3 度目)。
    for f in action_fractions(passed):
        out.append({"number": f["numerator"], "unit": f["unit"],
                    "from": f"行動 {f['id']} の根拠「{f['name']}」の分子"})
        out.append({"number": f["denominator"], "unit": f["unit"],
                    "from": f"行動 {f['id']} の根拠「{f['name']}」の分母"})
    # **観測 1 行の数も候補に入れる**(2026-09-29。通して見つけた ― 観測を印字しているのに
    # 候補に無かったので、**書き手が観測を p1 に使うと門が「数 32 が候補に無い」と言って止める**)。
    # **印字する側と数える側は同じ集合**でなければならない(P-139 と同じ型の 2 度目)。
    if direct is not None:
        for tag in CA.CROSS_TAGS:
            c = CA.top1_actual_cross(direct, tag)
            what = CROSS_PHRASE_JP[tag]
            for key, unit, label in (("positions", "局面", "第 1 候補が%sだった分かれ道"),
                                     ("games", "局", "第 1 候補が%sだった局"),
                                     ("bothPositions", "局面", "実戦も%sだった局面"),
                                     ("bothGames", "局", "実戦も%sだった局"),
                                     ("otherPositions", "局面", "実戦は%sではなかった局面"),
                                     ("otherGames", "局", "実戦は%sではなかった局")):
                out.append({"number": c[key], "unit": unit,
                            "from": "direct_answers.json の answers(観測: " + (label % what) + ")"})
    # **線の比べる相手の数**(2026-09-29)。印字する側と数える側は同じ集合(P-139 の型)。
    out += threshold_numbers(thresholds)
    out += long_think_fork_numbers(long_think)
    out += opposite_all_numbers((side_match or {}).get("opposite"))
    out += fork_nesting_numbers(fork_nesting_of(direct, side_match))
    return out


# ==================== 組の名と冒頭の段落(P-162・仕様 §4d) ====================
# **組の名の出どころは 1 か所。**既定は**材料そのもの**(`direct_answers` の `answers[].group`)で、
# CLI の `--group-label` があればそれを使う(人間が「3 分切れ負け」のような持ち時間の形を渡す)。
# **棋譜のヘッダから読まない**(KIF の書式が場所で違う。仕様 §4d)。
#
# **2 組以上は落とす。**この段は「今回の組の 1 つだけ」を前提に組んであり(`--patient` の番人と同じ)、
# 局番号も組ごとに 1 から振られる。**2 組の冒頭の型は `check_structure.opening_paragraph` に在るが、
# それを呼ぶには組ごとの局数が要る** ― 渡す道が無いまま黙って 1 組として書くと、
# **冒頭が「25 局」と言い、本文が別の組の数を混ぜる**冊子ができる。**止まるほうを採る。**
def group_label_of(direct, given):
    """今回の組の名。`given` があればそれ、無ければ材料の `group`。**2 種類あれば落とす。**"""
    found = sorted({a["group"] for a in answers_of(direct)})
    if len(found) != 1:
        raise ExitCandidatesError(
            f"材料の組が {len(found)} 種類({found}) ― この段は今回の組の 1 つだけを組む。"
            "2 組以上の冒頭は組ごとの局数が要るので、渡す道を作ってから呼ぶこと。")
    return given if given else found[0]


def opening_lines(patient, direct, today, group_label=None):
    """冒頭の段落。**文は `check_structure.opening_paragraph` が正本**(写しを持たない)。"""
    games = patient["summary"]["games"]
    label = group_label_of(direct, group_label)
    return CS.opening_paragraph(games, ((label, games),), today)


# ==================== 門が照合する候補の JSON ====================
# **関数にして測れるようにした**(2026-09-29)。`build()` の中に書いてあったので、
# **`p1_numbers` に `direct` を渡すのを外しても変異が黙った** ― 中を回す試験が無かった。
# §48 の「番人のある単位を関数にする」と同じ型の 2 度目。


def candidates_json(direct, patient, repro, denoms, passed, dropped, opening, groups=(), thresholds=(),
                    long_think=None, side_match=None):
    """門(`exit_gate.py`)が照合する候補。**md に印字したものと同じ値**でなければならない。"""
    return {"opening": opening, "denominators": denoms, "repro": repro,
            "actionFractions": action_fractions(passed),
            "openingGroups": list(groups),
            "unitMismatchFractions": unit_mismatch_fractions(dropped) + unit_mismatch_fractions(passed),
            "p1Numbers": p1_numbers(patient, repro, direct, passed, thresholds, long_think,
                                    side_match),
            "boards": [inner for _text, inner in board_marks(direct)],
            "menuPassed": [r["id"] for r in passed],
            "menuDropped": [{"id": r["id"], "minN": r["minN"],
                             "denominator": r["denominator"], "why": r["why"]}
                            for r in dropped]}


# ==================== 分母の出どころ ====================
# **文字列に埋めない**(仕様 §3 の 1)。「数 → その分母がどの集計から出たか」の対を JSON に出し、
# 数え方の節には**行として**印字する。**数え方の節と JSON が同じ対から作られる**ので、片方だけ直らない。
def group_denominator_rows(groups):
    """群の分母の表に流す対。**関数にして測れるようにした**(2026-09-29) ―
    `build()` の中に書いていたので、**`[]` を渡す変異が黙った**(§48 と同じ型の 3 度目)。"""
    return [(r["label"], r["games"]) for r in groups or ()]


# ==================== 分母の表の「どの集計から出たか」の語(P-172。2026-09-29) ====================
# **顧客の語で書く。**4 周目の実物は、この列に
# 「行動 M4 の根拠」「観測」「`direct_answers.json`」「`patient_report_data.json`」
# 「`opening_recognition.json` の署名」と**内部の名札と機械のファイル名**を出していた
# (席 (a) が挙げ、JSON 名は集計のときに私が測って見つけた)。
#
# **変えるのはこの列だけ。**「数」と「数えたもの」の列は変えない(司令塔の指示 ①)。
# **行動の番号(M4・M5)を出さない** ― 席 (a) は「M1〜M3 があったのか・なぜ無いのかも分からない」と書いた。
# 番号を消せば、落ちた候補の存在が表から漏れることも無くなる。
# **行動の文そのものは道具に無い**(`answer_menu.json` は `verifyName` と `minN` しか持たず、
# 行動の文は承認済みの表 = `answerMenu.ts` の側にある)。だから**分数の名前で言う** ―
# 分数の名前は「判定関数が数えている中身をそのまま日本語にしたもの」(`MENU_FRACTIONS` の注)なので、
# 顧客にとっては「何を数えた分母か」がそのまま読める。
DENOM_SECTION_ACTION = "試せること"  # 正本の節の名(`check_structure.SECTIONS` の役割名と同じ。試験で固定する)
DENOM_FORK_POSITIONS = "付録の「浅い読みで見えた分かれ道」に並べた局面"
DENOM_FORK_GAMES = "その分かれ道が出てきた局(同じ局を重ねて数えない)"
DENOM_GAMES = "この報告が見た対局の数"
DENOM_ACTION_TEMPLATE = "「{name}」の分母({section}の根拠)"
DENOM_OBSERVATION_TEMPLATE = "「第 1 候補が{what}だった{of}」の分母"
DENOM_GROUP_TEMPLATE = "群「{name}」の局数(序盤の駒の動きの型で分けたもの)"


# ==================== 判定の線を冊子に出す(2026-09-29。人間の決定「7 割の線を出す」) ====================
# **線の値は `check_answer.MENU_THRESHOLDS` の 1 か所**(判定が読んでいるのと同じ表)。
# ここは**顧客の語**だけを持つ ― 判定側に顧客向けの言い回しを置かない。
#
# 【なぜ要ったか】批評席 (a) が 3 周続けて「一致率が高いのか低いのか、**比べる相手が無い**」と書いた。
# **比べる相手は道具の中に在った**(M4 の 0.7、M5 の「0〜1 秒の崩れ率の 2 つぶん」)。
#
# 【語の制約(実測)】**「7 割」「2 倍」とは書けない** ― 検査 1 が数字 + 倍|割 を落とす。
# だから **`0.7`** と **「2 つぶん」**。**「下回った」は言わない**(それは書き手の文。
# 道具は**線の値と「今回の値」を並べるだけ**― 司令塔の指示)。
THRESHOLD_UNIT = "線"
THRESHOLD_LINE_FROM = "{what}(道具上の仮置き)"
THRESHOLD_OTHER_FROM = "「{name}」の分母(この線の比べる相手)"
THRESHOLD_SENTENCES = {
    "rate_below": "道具の仮置きの線は {line} です。今回の値は {values} でした。",
    "times_of_other_rate": ("道具の仮置きの線は「{other_name}」({other_value})の {times} つぶんです。"
                            "今回の値は {values} でした。"),
}


# ==================== 10 秒以上考えた手のうち分かれ道だった数(2026-09-29。③) ====================
# **行動 1 の条件「10 秒以上考える局面では」と、根拠の分数(全部の分かれ道)の橋にあたる数。**
# **観測として出すだけ**(行動にはしない ― 承認済みの表に無い項目を行動にしないため)。
# **判定も割合も作らない。数だけ**(人間の決定・規則 8 (3))。
#
# **「10 秒以上考えた手」は 2 通りある**ので、名前でどちらかを言う
# (`check_answer.LONG_THINK_NAME` ほか)。**同じ言い方で 2 つの数を並べない**(2026-09-24 の教訓)。
# **名前そのものが「何のうちの何か」を言う**ので、「そのうち」を重ねない
# (重ねると「そのうち 10 秒以上考えた手のうち、分かれ道だった手」と読める ― 校正で実測)。
LONG_THINK_FORK_LINE = ("- 観測(行動ではありません): {long_think_name}が {long_think} 手。"
                        "{fork_name}が {fork} 手。{opposite_name}が {opposite} 手。")
# **長考で絞らない「側が逆」**(③ の比べる相手)。**別の文にする** ― 分母の出どころが違うので、
# 1 文に混ぜると「そのうち」で繋がって読める(5 / 33 と 51 / 239 は比べられない)。
OPPOSITE_ALL_LINE = ("- 観測(行動ではありません): {all_name}が {denominator} {unit}。"
                     "{numerator_name}が {numerator} {unit}。")
# **書き手への注に数を書かない**(検査 1 と門 (ii) が偽の苦情を出す。`c6c8b5b`)。
# **数字を書かない**(半角も全角も) ― 検査 1 と門 (ii) が注の数を拾って偽の苦情を出す(`c6c8b5b`)。
# 漢数字は拾われない(`\d` に当たらない)。
LONG_THINK_TWO_COUNTS_NOTE = ("長考の手の数え方は二通りある ― 全部の手と、崩れを判定できた手だけ。"
                              "同じ言い方で並べない(分母の表の行を見ること)")


def opposite_all_line(opposite_all):
    """長考で絞らない「側が逆」の 1 行。**長考の行とは別の文**(分母の出どころが違う)。"""
    if not opposite_all:
        return None
    return OPPOSITE_ALL_LINE.format(
        all_name=CA.OPPOSITE_ALL_NAME, denominator=opposite_all["denominator"],
        numerator_name=CA.OPPOSITE_ALL_NUMERATOR_NAME, numerator=opposite_all["numerator"],
        unit=CA.OPPOSITE_ALL_UNIT)


def opposite_all_rows(opposite_all):
    """分母の表に足す行(分母は「第 1 候補の側が 1 つだった分かれ道」)。"""
    if not opposite_all:
        return []
    return [{"number": opposite_all["denominator"], "unit": CA.OPPOSITE_ALL_UNIT,
             "from": CA.OPPOSITE_ALL_NAME}]


def opposite_all_numbers(opposite_all):
    """候補の数(分子も入れる。印字する側と数える側は同じ集合。P-139)。"""
    if not opposite_all:
        return []
    return [{"number": opposite_all["denominator"], "unit": CA.OPPOSITE_ALL_UNIT,
             "from": CA.OPPOSITE_ALL_NAME},
            {"number": opposite_all["numerator"], "unit": CA.OPPOSITE_ALL_UNIT,
             "from": CA.OPPOSITE_ALL_NUMERATOR_NAME}]



# ==================== 分かれ道の数の入れ子(P-183。2026-09-29) ====================
# 5 周目の批評席 (a): 「**404・239・103・51 という分かれ道の数の関係(どれがどれの部分集合か)**が、
# 本編・付録のどちらにも整理されていません」。さらに **404 は本編に 0 件**で、付録の前文にしか無い
# (実測)― 本編だけを読む顧客には 3 つしか見えない。
#
# **実測した関係**(2026-09-29。`whatif-v2` の 404 行と `direct_answers` の 103 件を突き合わせた):
#   404 = 全部の分かれ道 / 239 ⊆ 404 / 103 ⊆ 404 / 51 ⊆ 239 /
#   **103 ⊄ 239 かつ 239 ⊄ 103**(別の絞り方。両方に当たるのは 68 局面)
# **だから「そのうち」を 404 にだけ掛け、239 と 103 の間には掛けない。**
# **68 は文に出さない** ― 新しい数を増やさずに「別の絞り方」だけを言う(司令塔の条件)。
#
# **文は司令塔が書いた**(2026-09-29)。括弧の 1 節だけ、実測に合わせて私が確定した。
# **数字を使わない**(「この二つ」は漢数字)― 検査 1 と門 (ii) が拾うため。
FORK_NESTING_SENTENCE = (
    "分かれ道は全部で {all_forks} 局面。そのうち、第 1 候補の側が攻めか自玉側のどちらか 1 つだったのが "
    "{one_side} 局面、実戦の手と第 1 候補の差が浅い読みで見えたのが {shallow} 局面です"
    "(この二つは別の絞り方で、片方がもう片方に含まれるわけではありません)。"
    "{one_side} 局面のうち、実戦が逆の側だったのが {opposite} 局面でした。")
FORK_NESTING_UNIT = "局面"
FORK_ALL_NAME = "全部の分かれ道"
FORK_SHALLOW_NAME = "浅い読みで実戦の手と第 1 候補の差が見えた分かれ道"


def fork_nesting_of(direct, side_match):
    """入れ子の 4 つの数。材料が足りなければ `None`(**数を作らない**)。"""
    opposite = (side_match or {}).get("opposite")
    all_forks = (side_match or {}).get("forkTotal")
    if not opposite or not all_forks:
        return None
    return {"all": int(all_forks), "oneSide": int(opposite["denominator"]),
            "shallow": len(answers_of(direct)), "opposite": int(opposite["numerator"])}


def fork_nesting_line(nesting):
    """**使ってよい固定文**(書き手が選ぶ)。数はすべて材料から。"""
    if nesting is None:
        return None
    return FORK_NESTING_SENTENCE.format(
        all_forks=nesting["all"], one_side=nesting["oneSide"],
        shallow=nesting["shallow"], opposite=nesting["opposite"])


def fork_nesting_rows(nesting):
    """分母の表に足す行。**全部の分かれ道(404)だけ** ― 他の 3 つは既に表に行がある。"""
    if nesting is None:
        return []
    return [{"number": nesting["all"], "unit": FORK_NESTING_UNIT, "from": FORK_ALL_NAME}]


def fork_nesting_numbers(nesting):
    """候補の数(門 (ii))。**文に出る 4 つ全部**を入れる ― 印字する側と数える側は同じ集合(P-139)。"""
    if nesting is None:
        return []
    return [{"number": nesting["all"], "unit": FORK_NESTING_UNIT, "from": FORK_ALL_NAME},
            {"number": nesting["shallow"], "unit": FORK_NESTING_UNIT, "from": FORK_SHALLOW_NAME},
            {"number": nesting["oneSide"], "unit": FORK_NESTING_UNIT, "from": CA.OPPOSITE_ALL_NAME},
            {"number": nesting["opposite"], "unit": FORK_NESTING_UNIT,
             "from": CA.OPPOSITE_ALL_NUMERATOR_NAME}]


def long_think_fork_line(counts):
    """観測の 1 行。`counts` が None なら None(材料が無ければ何も出さない)。"""
    if counts is None:
        return None
    return LONG_THINK_FORK_LINE.format(
        long_think_name=CA.LONG_THINK_NAME, long_think=counts["longThink"],
        fork_name=CA.LONG_THINK_FORK_NAME, fork=counts["fork"],
        opposite_name=CA.LONG_THINK_OPPOSITE_NAME, opposite=counts["oppositeSide"])


def long_think_fork_rows(counts):
    """分母の表に足す行。**分母になる 2 つの数**(全部の手・分かれ道だった手)。"""
    if counts is None:
        return []
    return [{"number": counts["longThink"], "unit": "手", "from": CA.LONG_THINK_NAME},
            {"number": counts["fork"], "unit": "手", "from": CA.LONG_THINK_FORK_NAME}]


def long_think_fork_numbers(counts):
    """候補の数(印字する側と数える側は同じ集合。P-139 の型)。**分子も入れる。**"""
    if counts is None:
        return []
    return [{"number": counts["longThink"], "unit": "手", "from": CA.LONG_THINK_NAME},
            {"number": counts["fork"], "unit": "手", "from": CA.LONG_THINK_FORK_NAME},
            {"number": counts["oppositeSide"], "unit": "手", "from": CA.LONG_THINK_OPPOSITE_NAME}]


def thresholds_of(passed, materials):
    """線を持つ行動の一覧。**`check_answer.menu_threshold_of` をそのまま並べる**(写しを作らない)。"""
    out = []
    for row in passed:
        threshold = CA.menu_threshold_of(row["id"], materials)
        if threshold is None:
            continue
        out.append({"id": row["id"], "threshold": threshold,
                    "fractions": [f for f in (row.get("fractions") or [])
                                  if not f.get("unitMismatch")]})
    return out


def values_phrase(fractions):
    """「攻めが 65 / 107、自玉側が 76 / 132」。**分数の名札があるときだけ名札を付ける。**"""
    parts = []
    for f in fractions:
        value = f"{f['numerator']} / {f['denominator']}"
        parts.append(f"{f['label']} {value}" if f.get("label") else value)
    return "、".join(parts)


def threshold_denominator_rows(thresholds):
    """分母の表に足す行 ― **線そのもの**と、**線の比べる相手の分母**。"""
    rows = []
    for row in thresholds:
        t = row["threshold"]
        if "line" in t:
            rows.append({"number": t["line"], "unit": THRESHOLD_UNIT,
                         "from": THRESHOLD_LINE_FROM.format(what=t["what"])})
        other = t.get("other")
        if other:
            rows.append({"number": other["denominator"], "unit": other["unit"],
                         "from": THRESHOLD_OTHER_FROM.format(name=other["name"])})
    return rows


def threshold_sentences(thresholds):
    """**使ってよい固定文**(書き手が選ぶ)。線の値と今回の値を並べるだけ。"""
    out = []
    for row in thresholds:
        t = row["threshold"]
        template = THRESHOLD_SENTENCES.get(t["kind"])
        if template is None:
            continue
        other = t.get("other") or {}
        out.append(template.format(
            line=t.get("line"), times=t.get("times"),
            other_name=other.get("name"),
            other_value=f"{other.get('numerator')} / {other.get('denominator')}",
            values=values_phrase(row["fractions"])))
    return out


def threshold_numbers(thresholds):
    """**線の周りの数を候補に入れる**(印字する側と数える側は同じ集合。P-139 の型)。

    **線の値そのものは入れない** ― `0.7` は検査 1 も門も数として拾わない(両方の桁が
    `SMALL_NUMBER_MAX` 以下)。拾われない数を候補に入れると、**候補の一覧が嘘になる**。
    """
    out = []
    for row in thresholds:
        other = row["threshold"].get("other")
        if not other:
            continue
        out.append({"number": other["numerator"], "unit": other["unit"],
                    "from": f"「{other['name']}」の分子(この線の比べる相手)"})
        out.append({"number": other["denominator"], "unit": other["unit"],
                    "from": f"「{other['name']}」の分母(この線の比べる相手)"})
    return out


def denominators(direct, patient, repro, passed=(), groups=None, thresholds=(), long_think=None,
                 side_match=None):
    """分母の出どころ。**冊子に出る分母は全部ここに行がある**(P-161)。

    2 周目の表は 3 行(103・24・25)しかなく、**行動の根拠の分母(107・132)と観測の分母(54)が
    どれも引けなかった** ― 「数の出どころを引ける」と約束して、行動の根拠の数だけが引けない形だった。

    `passed` = 下限を通った行動の行。**その行動の分数の分母**を行にする。
    `groups` = 群ごとの分母(`[(群の名, 局数), …]`)。**戦型の群の再集計を見込んで最初から受ける** ―
    後から足すと、また表が追いつかない(今回と同じ失敗になる)。

    **単位が違う分数は出さない**(`unitMismatch`)。単位の違う数を「局面」として並べれば、
    表そのものが嘘になる(P-165)。**出さない理由は書き手への注に出す**(黙って落とさない)。
    """
    out = [
        {"number": repro["totalPositions"], "unit": "局面", "from": DENOM_FORK_POSITIONS},
        {"number": repro["totalGames"], "unit": "局", "from": DENOM_FORK_GAMES},
        {"number": patient["summary"]["games"], "unit": "局", "from": DENOM_GAMES},
    ]
    # ---- 行動の根拠の分母(P-161) ----
    for row in passed:
        for f in row.get("fractions") or []:
            if f.get("unitMismatch"):
                continue
            out.append({"number": f["denominator"], "unit": f["unit"],
                        "from": DENOM_ACTION_TEMPLATE.format(name=f["name"], section=DENOM_SECTION_ACTION)})
    # ---- 観測の分母(P-161。行動ではないが冊子に出る) ----
    if direct is not None:
        for tag in CA.CROSS_TAGS:
            c = CA.top1_actual_cross(direct, tag)
            what = CROSS_PHRASE_JP[tag]
            out.append({"number": c["positions"], "unit": "局面",
                        "from": DENOM_OBSERVATION_TEMPLATE.format(what=what, of="分かれ道")})
            out.append({"number": c["games"], "unit": "局",
                        "from": DENOM_OBSERVATION_TEMPLATE.format(what=what, of="局")})
    # ---- 群ごとの分母(戦型の群の再集計。群が小さいので割合は出さない) ----
    for name, n in (groups or []):
        out.append({"number": n, "unit": "局", "from": DENOM_GROUP_TEMPLATE.format(name=name)})
    # ---- 判定の線と、線の比べる相手(2026-09-29) ----
    out += threshold_denominator_rows(thresholds)
    # ---- 10 秒以上考えた手のうち分かれ道だった数(2026-09-29。③) ----
    out += long_think_fork_rows(long_think)
    out += opposite_all_rows((side_match or {}).get("opposite"))
    out += fork_nesting_rows(fork_nesting_of(direct, side_match))
    # **同じ数と同じ出どころの行は 1 つにする**(順番は保つ)。
    seen, unique = set(), []
    for row in out:
        key = (row["number"], row["unit"], row["from"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def unit_mismatch_fractions(passed):
    """**単位が違う分数**(P-165)。門 (ix) が「顧客の本編に残っていないか」を見るのに使う。"""
    return [{"id": row["id"], "numerator": f["numerator"], "denominator": f["denominator"],
             "unitMismatch": f["unitMismatch"]}
            for row in passed for f in (row.get("fractions") or []) if f.get("unitMismatch")]


def unit_mismatch_notes(passed):
    """**分母の表に出せなかった分数**の理由(書き手への注。黙って落とさない)。"""
    return [f"行動 {row['id']} の根拠「{f['name']}」は分母の表に出していません ― {f['unitMismatch']}"
            for row in passed for f in (row.get("fractions") or []) if f.get("unitMismatch")]


# ==================== md を組む ====================
def heading_of(role, **numbers):
    """節の見出しを `check_structure.SECTIONS` から作る。**文字列を写さない。**

    `SECTIONS` は (役割, 見出しの頭, 含む語) なので、**頭をそのまま見出しにする**。
    答え合わせの節だけは局数が入るので、頭と含む語をつないで作る。
    """
    head, contains = next((h, c) for r, h, c in CS.SECTIONS if r == role)
    if contains is None:
        return head
    return f"{head} {numbers['games']} 局で、何で{contains}をするか"


def rest_games(patient, featured):
    """「そのほかの局」の数。**引き算そのものは `exit_index.rest_count` が正本**(2026-09-29)。

    以前はここ・`exit_cover.numbers_of`・`_mid.py` の 3 か所が同じ引き算を持っていた。
    **独立監査が「ここだけ変えても試験が 1 本も落ちない」を実測した**ので、`exit_index` に 1 本にした。
    """
    return EI.rest_count(patient["summary"]["games"], featured)


def build_md(direct, patient, repro, passed, dropped, mapping, denoms, fdata,
             opening, featured=0, side_match=None, groups=(), thresholds=(), long_think=None):
    # **局数は `summary.games`**(`exit_cover.numbers_of`・`check_structure` と同じ出どころ)。
    # `len(patient["games"])` でも同じ数だが(25 = 25 を実測 2026-09-29)、
    # **出どころを 2 つ持つと、片方の材料が欠けたときに数が黙って変わる。**
    games = patient["summary"]["games"]
    L = []
    L.append(f"# {games} 局で起きていたこと")
    L.append("")
    # **冒頭は 4 文**(P-162。組が 2 つ以上なら 6 文)。**1 文ずつ別の行**にする ―
    # 門は 1 文ずつ在るかを見るので、つないで 1 行にすると折り返しの照合が要る。
    for sentence in opening:
        L.append(sentence)
    L.append("")

    # ---- (a) ひとことで ----
    L.append(f"## {heading_of('ひとことで')}")
    L.append("")
    L.append(TODO)
    L.append(note("ここに残すのは、数 3 つと「ひとことで」の 1 文だけ。候補の節は消す。"
                  "**多くを行動の根拠の分数から引く**"
                  "(引けないものを置くなら、節に「無いものは無いと書きます。」を書く)"))
    L.append("")
    L.append(DRAFT_ONLY_HEADINGS[0])
    L.append("")
    for f in patient["findings"]:
        texts = fdata["findings"].get(f["kind"]) if fdata else None
        title = (texts or {}).get("title", f["kind"])
        L.append(f"- **{title}**{'(材料が出すと決めた側)' if f.get('shown') else '(材料が出さないと決めた側)'}")
        L.append(f"  - {f['oneLine']}")
        # **数の実物はこちら。**`oneLine` は数の入っていない一言で、
        # **書き手が選ぶ 3 つの数はこの `text` に出る**(2026-09-29 に門を繋いで見つけた穴 ―
        # `oneLine` だけ印字していたので、**選ぶ相手が印字されていなかった**)。
        L.append(f"  - 数: {f['text']}")
        # **`oneLineVariants` は印字しない。**材料にあるのは `{序盤|中盤|終盤}`・`{X}` のような
        # **未展開の型**で、埋めるのは `lib/reportData.ts` の仕事(埋まった文が `oneLine`)。
        # ここで埋めれば、**私が言い回しを選んだ**ことになる(候補の段の越権)。
        # 型が何通りあるかだけを伝える ― 書き手が材料を見に行けるように。
        variants = (texts or {}).get("oneLineVariants")
        if variants:
            L.append(f"  - この種類には言い回しの型が {len(variants)} 通りあります"
                     "(埋まった文は上の 1 つ。型は finding_texts.json にあります)")
    L.append("")
    L.append(DRAFT_ONLY_HEADINGS[1])
    L.append("")
    L.append(f"分母は {repro['totalPositions']} 局面・{repro['totalGames']} 局です。")
    L.append("")
    # **行動の根拠の分数**(P-164)。**これを p1 に選べば、観測 → 行動がつながる。**
    # 4 人目(18 局版)の p1 は 3 本のうち 2 本がこの形だった。
    for f in action_fractions(passed):
        L.append(action_fraction_line(f))
    # **観測 1 行(行動ではない)。**書き手が「ひとことで」の 3 本に使える候補として出す。
    for tag in CA.CROSS_TAGS:
        L.append(f"- 観測(行動ではありません): {cross_line(direct, tag)}")
    # **10 秒以上考えた手のうち分かれ道だった数**(2026-09-29。③)。行動 1 の条件との橋。
    line = long_think_fork_line(long_think)
    if line is not None:
        L.append(line)
    # **長考で絞らない「側が逆」**(③ の比べる相手)。**長考の行と分母の出どころが違う。**
    all_line = opposite_all_line((side_match or {}).get("opposite"))
    if all_line is not None:
        L.append(all_line)
    if line is not None or all_line is not None:
        L.append(note(LONG_THINK_TWO_COUNTS_NOTE))
    # **戦型の群ごとの再集計(観測。行動ではない)**(2026-09-29)。
    # **数だけ。割合・%・群どうしを比べる文・「差がある / ない」の判定は作らない**
    # (群が 4 局・3 局なので、割合を出せば 1 局の違いが 25 ポイント動く)。
    # **戦型の名前も「普段指さない戦型」も書かない** ― 顧客向けの分類としては未承認
    # (人間の決定 2026-09-29)。**顧客の表での呼び方は書き手が決める**ので、
    # ここは仮の見出し(群 A / 群 B / 群 C)で出す。
    if groups:
        L.append(note("下は戦型の群ごとの再集計(観測。行動ではない)。**戦型の名前は書かない** ― "
                      "顧客向けの分類としては未承認。**群の呼び方は書き手が決める**"
                      "(仮の見出しは 群 A / 群 B / 群 C)。**割合を出さない・群どうしを比べない**"))
        for line in EGR.lines_of(groups, CROSS_PHRASE_JP):
            L.append(line)
    L.append("")
    L.append("| どんな手だったか | 局面 | 局 |")
    L.append("|---|---|---|")
    for r in repro["rows"]:
        L.append(f"| {r['phrase']} | {r['positions']} | {r['games']} |")
    L.append("")

    # ---- (b) 局面で見る ----
    L.append(f"## {heading_of('局面で見る')}")
    L.append("")
    L.append(TODO)
    L.append(note("ここに残すのは盤 2 つ分の行だけ。残りの行は消す"))
    L.append("")
    for text, _inner in board_marks(direct, side_match, passed):
        L.append(text)
    L.append("")

    # ---- (c) 試せること ----
    L.append(f"## {heading_of('試せること')}")
    L.append("")
    L.append(TODO)
    L.append(note("下の「下限を通った項目」から本数を決め、1 行ずつ書く。この表の外から行動を作らない"))
    L.append("")
    L.append(DRAFT_ONLY_HEADINGS[2])
    L.append("")
    if not passed:
        L.append(EI.NO_ACTION_SENTENCE)
    for i, r in enumerate(passed, start=1):
        item = r["item"]
        line = (f"{i}. {item['actionCore']}<!-- menu: {r['id']} -->"
                f"　― 根拠は{evidence_phrase(r)}")
        if item.get("foundInSameData"):
            line += f"。{CA.FOUND_IN_SAME_DATA_PHRASE}。"
        L.append(line)
    L.append("")
    L.append(DRAFT_ONLY_HEADINGS[3])
    L.append("")
    L.append("| 項目 | 下限 | いまの分母 | 届かなかった理由 |")
    L.append("|---|---|---|---|")
    for r in dropped:
        den = "—" if r["denominator"] is None else r["denominator"]
        L.append(f"| {r['id']} | {r['minN']} | {den} | {r['why']} |")
    L.append("")
    # ---- 使ってよい固定文(書き手が選ぶ。2026-09-29) ----
    # **候補として出すだけ。**使う / 使わないは書き手が決める(この段は選ばない)。
    # **1 つ目**は「なぜこの N つだけなのか」の 1 文(批評席 (b) の提案文。3 席が 2 周続けて
    # 「選定の基準が読めない」を挙げた)。**2 つ目**は「無いものは無いと書きます。」
    # (4 人目の実物の型。行動にしない理由を明示した 1 本の尾)。
    # **前半の主語は道具が作らない** ― 4 人目のあの主語は書き手が数から書いたもので、
    # 材料のどこにも文として無い(`exit_index` の注記)。
    L.append(DRAFT_ONLY_HEADINGS[4])
    L.append("")
    L.append(f"- {EI.selection_sentence(games)}")
    L.append(f"- {EI.NOTHING_TO_HIDE_SENTENCE}")
    # **判定の線**(2026-09-29)。**「下回った」は書かない** ― 線と今回の値を並べるだけ。
    for sentence in threshold_sentences(thresholds):
        L.append(f"- {sentence}")
    # **分かれ道の数の入れ子**(P-183。2026-09-29)。**404 は本編に無かった数**なので、
    # この文を使えば本編に入る(使う / 使わないは書き手が決める)。
    nesting_line = fork_nesting_line(fork_nesting_of(direct, side_match))
    if nesting_line is not None:
        L.append(f"- {nesting_line}")
    negatives = [r for r in dropped if r["why"] == NEGATIVE_TYPE_REASON]
    if negatives:
        L.append(note("下は承認済みの表の「否定の型」の文。そのまま使える"
                      "(前半の主語を道具は作らない ― 数から書くのは書き手)"))
        for r in negatives:
            L.append(f"- {r['item']['actionCore']}")
    L.append("")

    # ---- (d) 答え合わせの表 ----
    L.append(f"## {heading_of('答え合わせ', games=games)}")
    L.append("")
    L.append(note("残した行動の行だけにする(器の門の項目 6 が、この表の行と本編の行動の印の"
                  "集合が一致することを見る)"))
    L.append("")
    # **列は 3 つ。道具の中の名前(`M4`・`M6`)の列は置かない**(2026-09-29。実物 2 件 ― 3 人目・
    # 4 人目 ― はどちらも「試したこと / 動くはずの事実 / 今の値」の 3 列で、**1 列目は行動の文**だった。
    # `ID` と `137`・`404` だけが並ぶ表は読者に何も渡さない。P-152)。
    L.append(VERIFY_TABLE_HEADER)
    L.append("|---|---|---|")
    for r in passed:
        # **行にメニューの印を入れる。**器の門の項目 6 が行ごとに印をちょうど 1 つ求める
        # (実測 2026-09-29。印が無いと工程の最後で 5 行ぶん落ちる)。
        L.append(f"| {r['item']['actionCore']}<!-- menu: {r['id']} --> | {facts_cell(r)} | {values_cell(r)} |")
    L.append("")

    # ---- (e) 数え方 ----
    L.append(f"## {heading_of('数え方')}")
    L.append("")
    for sentence in EI.COUNTING_NOTES:
        L.append(f"- {sentence}")
    if fdata and fdata.get("evalJitterNote"):
        L.append(f"- {fdata['evalJitterNote']}")
    L.append("")
    # ---- 付録の節を指す印(`<!-- sec: 付録N/節 -->`)----
    # **選ぶものではない。**束ねる付録(付録 1 + 付録 3)とその節は `exit_index.COVER_SECTIONS` が正本で、
    # **表紙の表の行はこの印から作られる**(`exit_cover.py` は本編が指していない節を表に載せない)。
    # ここに出さないと、**表紙が「本編が指していない節を表に載せようとした」で落ちる**
    # (実測 2026-09-29。段を繋いで初めて出た ― 候補の段だけを回している間は見えなかった)。
    # 題は `exit_index.section_title` から引く(**顧客に見せる言い方をここで作らない**)。
    L.append("### 数の出どころを引ける付録")
    L.append("")
    for appendix in EI.COVER_SECTIONS:
        for name in EI.COVER_SECTIONS[appendix]:
            title = EI.section_title(appendix, name, games=games,
                                     rest=rest_games(patient, featured))
            L.append(f"- {title}<!-- sec: {appendix}/{name} -->")
    L.append("")
    # ---- 分母の表は**付録の表紙の次のページ**へ(器の単独束 C-4。2026-09-30。司令塔の判断)----
    # 印は `exit_index.APPENDIX_TAG_RE` の文法 1 か所。読む側は 3 つ ―
    # `exit_body.py`(本編から外す)・`exit_cover.py`(付録に組む)・`check_structure.py`(両側を見る)。
    # **md 自身に「この節は付録へ行く」と書かせる** ― 印が無いと、md だけを読んだ席が
    # 「表は本編にある」と誤って読む(P-159・P-171 の家族)。
    L.append(f"<!-- appendix: {EI.APPENDIX_TAG_TITLE} -->")
    L.append(note(EI.APPENDIX_TAG_NOTE))
    L.append("")
    L.append("### 数の分母がどこから来たか")
    L.append("")
    L.append("| 数 | 数えたもの | どの集計から出たか |")
    L.append("|---|---|---|")
    for d in denoms:
        L.append(f"| {d['number']} | {d['unit']} | {d['from']} |")
    L.append("")
    # **表に出せなかった分数の理由**(黙って落とさない。P-165)。
    for why in unit_mismatch_notes(passed):
        L.append(note(why))
    if unit_mismatch_notes(passed):
        L.append("")

    # ---- (f) 対応表 ----
    L.append(f"## {heading_of('対応表')} ― 何局目が、どのファイルか(本人用)")
    L.append("")
    L.append("| 局 | ファイル名 | 先後 | 手数 | 結果 |")
    L.append("|---|---|---|---|---|")
    for r in mapping:
        L.append(f"| {r['no']} | {r['source']} | {r['side']} | {r['total']} | {r['result']} |")
    L.append("")
    return "\n".join(L)


# ==================== 本体 ====================
def parse_own_args(argv):
    # `--group-label` は**任意**(渡さなければ材料の `group` のまま。仕様 §4d「出力不変」)。
    own = {"out_md": None, "out_json": None, "kifu_dir": None, "today": None}
    optional = {"group_label": None, "opening_recognition": None}
    rest = []
    i = 0
    while i < len(argv):
        flag = argv[i]
        if flag == "--group-label":
            value = argv[i + 1] if i + 1 < len(argv) else None
            if value is None or value.startswith("--"):
                raise ExitCandidatesError(f"{flag} に値が無い")
            optional["group_label"] = value
            i += 2
            continue
        if flag == "--opening-recognition":
            value = argv[i + 1] if i + 1 < len(argv) else None
            if value is None or value.startswith("--"):
                raise ExitCandidatesError(f"{flag} に値が無い")
            optional["opening_recognition"] = value
            i += 2
            continue
        if flag in ("--out-md", "--out-json", "--kifu-dir", "--today"):
            value = argv[i + 1] if i + 1 < len(argv) else None
            if value is None or value.startswith("--"):
                raise ExitCandidatesError(f"{flag} に値が無い")
            own[flag[2:].replace("-", "_")] = value
            i += 2
            continue
        rest.append(flag)
        i += 1
    missing = [k for k, v in own.items() if v is None]
    if missing:
        raise ExitCandidatesError(
            f"足りない引数: {' '.join('--' + m.replace('_', '-') for m in sorted(missing))}")
    own.update(optional)
    return own, rest


def build(own, rest):
    # **既に在る md を上書きしない。**この md は**書き手(人)が書き換える場所**であり、
    # 上書きは**人の仕事を消す**ことになる。
    #
    # 【実際に消した(2026-09-29)】候補の JSON だけを作り直したくて JSON を消して段を回したら、
    # 段の「済みの判定」が `md と JSON の両方が在る` だったため段が走り、**書き手が書いた 92 行の md が
    # 240 行の素の下書きに戻った。**git の追跡外なので戻せなかった。
    # **「片方を消せばもう片方も作り直される」形になっていた。**
    #
    # 番人を道具の側に置くのは、**段の判定を直すだけでは手で呼んだときに消せる**ため。
    # 作り直したいときは、**呼ぶ側が md を先にどかす**(何を捨てるかを人が決める)。
    if os.path.exists(own["out_md"]):
        raise ExitCandidatesError(
            f"本編の md が既にある: {own['out_md']}\n"
            "この md は書き手が書き換える場所なので上書きしない。"
            "作り直すなら、先に別の名前へ移してから呼ぶこと(消すかどうかは人が決める)。")
    # `check_answer.parse_args` は md のパスを 1 つ要求する(B の文を検査する道具なので)。
    # **この段には入力の md が無い** ― これから書く側だから。`build_materials` は `markdown_path` を
    # 一度も読まないことを確かめたうえで、**これから書く md のパスを渡す**(別の値を作らない)。
    args = CA.parse_args(rest + [own["out_md"]])
    repo_root = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
    ctx = CA.build_materials(args, repo_root)
    direct = ctx["materials"]["direct"]
    if direct is None:
        raise ExitCandidatesError("--direct が無い(盤と再現の候補を作れない)")
    if len(args.patients) != 1:
        raise ExitCandidatesError(
            f"--patient は今回の組の 1 つだけ({len(args.patients)} 件渡された) ― "
            "本編は今回の組の話であり、局番号は組ごとに 1 から振られる")
    patient = CA.load_json(args.patients[0][0])
    fdata = None
    for name in ("finding_texts.json",):
        path = os.path.join(os.path.dirname(args.patients[0][0]), name)
        if os.path.exists(path):
            fdata = CA.load_json(path)
    repro = repro_rows(direct)
    passed, dropped = menu_rows(ctx)
    mapping = mapping_rows(patient, own["kifu_dir"])
    # **戦型の群ごとの再集計**(2026-09-29)。**渡されなければ何も変わらない。**
    # `--opening-recognition` は任意 ― 知識レーンの JSON が無い顧客でも通る。
    side_match = ctx["materials"]["sideMatch"]
    groups = ()
    if own.get("opening_recognition"):
        groups = EGR.group_rows(EGR.load(own["opening_recognition"]), patient, direct, side_match)
    # **判定の線**(2026-09-29)。`check_answer.MENU_THRESHOLDS` に在る行動だけが線を持つ。
    thresholds = thresholds_of(passed, ctx["materials"])
    # **`passed` と群と線を渡す**(P-161。行動の根拠の分母・群の分母・線を表に出すため)。
    # **10 秒以上考えた手のうち分かれ道だった数**(2026-09-29。③)。組の中だけで足す。
    # **組は材料の `group`(`group_label_of(direct, None)`)で引く** ― CLI の `--group-label`
    # (人間が渡す「3 分切れ負け」のような呼び名)では `time_cause.json` の `group`(「3 分」)に
    # **当たらず、黙って 0 件になる**。顧客に見せる呼び名と、材料を引く鍵は別物である。
    long_think = CA.long_think_fork_of(ctx["materials"].get("timeCause"),
                                       group_label_of(direct, None))
    denoms = denominators(direct, patient, repro, passed, group_denominator_rows(groups),
                          thresholds, long_think, side_match)
    # `featured` = 1 局ずつ見た局(`prose.json` の件数)。**「そのほかの局」の題に要る。**
    featured = len(CA.load_json(args.prose_paths[0])) if args.prose_paths else 0
    # **冒頭の段落は md と JSON の両方へ同じものを渡す**(門が 1 文ずつ在るかを見る)。
    opening = opening_lines(patient, direct, own["today"], own.get("group_label"))
    md = build_md(direct, patient, repro, passed, dropped, mapping, denoms, fdata,
                  opening, featured, side_match, groups, thresholds, long_think)

    with open(own["out_md"], "w", encoding="utf-8") as f:
        f.write(md + "\n")
    with open(own["out_json"], "w", encoding="utf-8") as f:
        json.dump(candidates_json(direct, patient, repro, denoms, passed, dropped, opening,
                                  groups, thresholds, long_think, side_match),
                  f, ensure_ascii=False, indent=1, sort_keys=True)
    return {"todo": md.count(TODO), "repro": len(repro["rows"]),
            "passed": len(passed), "dropped": len(dropped),
            "boards": len(answers_of(direct)), "mapping": len(mapping)}


def main(argv):
    own, rest = parse_own_args(argv)
    out = build(own, rest)
    print(f"wrote {own['out_md']}(TODO {out['todo']} 件・再現 {out['repro']} 種類・"
          f"盤の候補 {out['boards']}・行動 通った {out['passed']}/落ちた {out['dropped']}・"
          f"対応表 {out['mapping']} 行)")
    print(f"wrote {own['out_json']}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (ExitCandidatesError, CA.CheckAnswerError) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
