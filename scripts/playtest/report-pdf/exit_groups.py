# -*- coding: utf-8 -*-
# STEP CUSTOMER-EXIT の**戦型の群ごとの再集計**(2026-09-29。人間の決定 + 司令塔の条件 5 つ)。
#
# 【顧客の PDF にどう出るか】本編の**観測の欄**に、群ごとの既存指標が**数だけ**並ぶ。
# **割合(%・率)は出さない。群どうしを比べる文も、「差がある / ない」の判定も作らない。**
# **戦型の名前は出さない**(顧客向けの分類としては未承認 ― 人間の決定 2026-09-29)。
# **顧客の表での呼び方は `GROUP_LABELS` の 1 か所**(人間の決定 2026-10-01。それまでは書き手が決めていた)。
#
# 【なぜ「数だけ」か】群が小さい(実物で 18 / 4 / 3)。4 局・3 局で割合を出せば、
# **1 局の違いが 25 ポイント動く**。同じ基底でない率を並べない(`compare-rates-need-same-base` の型)。
#
# 【新しい判定・閾値を作らない】`opening_recognition.json` の `useOfThisFile` のとおり
# **判定・分類には使わない**。ここでやるのは「既存の数え方を群で割る」だけである。
#
# 【合わなければ止まる】群に割った数の合計が、**材料がすでに持っている合計と違えば落とす。**
# 黙って違う数を出すより止まるほうがよい(`stopping-beats-deleting` の型)。
# とくに「一度は優勢になった局 / そのうち負けた局」は、+300 の規則をここで局ごとに当て直しているので、
# **合計が `findings.aheadLoss.numbers` と一致することを毎回確かめる** ―
# 一致しなければ、規則の写しがずれたということである。
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_answer as CA  # noqa: E402


class ExitGroupsError(Exception):
    pass


# 群の機械の名(`proposalSignatureClass` → 鍵)。**局数を鍵に入れない** ―
# 入れると材料が変わるたびに鍵が変わり、読む側が壊れる。
CLASS_KEYS = {
    "多数の核": "core",
    "それ以外": "other",
    "署名なし": "noSignature",
}
# 出す順。
GROUP_ORDER = ("core", "other", "noSignature")

# ==================== 顧客の冊子での群の呼び方(人間の決定 2026-10-01)====================
#
# **packet の群 ↔ 冊子のラベルの対応表は、リポジトリでここだけ。**
# packet 側は内部の名を持っている(`observationAggregates.ts` の「群 A の局数」など)が、
# **それを冊子へ写さない。** packet は封がしてあって直せない(ラベルを変えると `packetId` が
# 変わる)ので、**翻訳はこちら側の仕事**である。
#
# 【「普段」を使わない】人間の決定 2026-10-01。人間の言葉:
#   **「25 局内で多かった」≠「本人が普段指している」。**
#   根拠(2026-10-01 の実測): 1 回だけ出た型が 7 件 / 25 局では「珍しい」と「指さない」を
#   区別できない / 「多数の核」はこの 25 局内の上位 3 件をそう呼んでいた。
#   **外部基準(普段)を内部頻度で代用する根拠が無い。**
#   封じた最終版は「普段の型 18 局・普段と違う型 4 局」と書いている(「普段」が 5 行・9 か所)。
#   **そのまま写すと、人間が却下した代用を焼き付ける**ことになる。だから写さない。
#   **送った冊子は直さない**(封の後は触らない)。言い換えるのは**次の冊子から**。
#
# 【「型」ではなく「分類」】人間の理由: 「この 25 局で多かった**型**」と**型そのものとして
#   確定表示してよいか**は、戦型名の認識基盤とは別問題。**戦型の定義・認識が知識レーンで
#   承認された後に、必要なら「戦型」へ昇格できる。**いまは「分類」が最も安全。
#   3 つ目も「分類」で揃えたのは司令塔の判断 ― 人間の一覧は「型が取れない局」だったが、
#   **他の 2 つが「分類」で 3 つ目だけ「型」だと、最初の 2 つが型であることを含意してしまう。**
#
# 【局数は値で持たない】ラベルに局数が入るので**型で持つ**(`exit_index.SECTION_TITLES` と同じ扱い)。
#   値で焼くと**別の顧客の冊子に 25 が出る** ― 2026-09-30 に顧客に見える名前で実際に起きた型である。
GROUP_LABELS = {
    "core": "この {games} 局で多かった分類",
    "other": "この {games} 局でそれ以外だった分類",
    "noSignature": "分類が取れない局",
}
# **ラベルに出てはいけない語。**
# **文書全体の黒名簿にはしない**(司令塔が実物で確かめた 2 か所が壊れる ― 顧客の問いの字
# `observation-request.json` の q1「**普段**指さない戦型を採用している…」と、人間が書いた
# 80 文字の文 `exit_index.UNANSWERABLE_PAST_GAMES`。どちらにも「普段」が**正しく**出る)。
# **守るのは「群のラベル」と「群の表の行の見出し」の 2 か所だけ。**
LABEL_FORBIDDEN_WORDS = ("普段",)
# 優勢の閾値。**新しい閾値ではない** ― 顧客に出る「数え方」の節が既に
# 「一度でも評価が +300 以上」と書いている(`exit_index.COUNTING_NOTES`)。
AHEAD_CP = 300


def check_label_words(text):
    """**ラベルに「普段」が入っていたら落とす。**黙って却下済みの代用を顧客に出さない。"""
    for word in LABEL_FORBIDDEN_WORDS:
        if word in text:
            raise ExitGroupsError(
                f"群のラベルに「{word}」が入っている: {text} ― "
                "「この局数の中で多かった」は「普段指している」ではない(人間の決定 2026-10-01)。"
                "外部の棋譜との比較ができるまで、この語をラベルに使わない")
    return text


def label_of(key, games):
    """群の鍵 → **冊子のラベル**。局数は**材料から渡す**(ここで数えない・既定値を入れない)。"""
    template = GROUP_LABELS.get(key)
    if template is None:
        raise ExitGroupsError(
            f"群の鍵「{key}」のラベルが無い ― 群が増えたら、顧客に出す呼び方を人が決めてから足すこと")
    if "{games}" in template and (isinstance(games, bool) or not isinstance(games, int)
                                  or games <= 0):
        raise ExitGroupsError(
            f"ラベルに入れる局数が数でない: {games} ― "
            "局数は材料(`summary.games`)から渡す(既定値を入れない)")
    return check_label_words(template.format(games=games))


def load(path):
    with io.open(path, encoding="utf-8") as f:
        data = json.load(f)
    rows = data.get("rows")
    if not rows:
        raise ExitGroupsError(f"戦型の認識に rows が無い: {path}")
    return data


def class_key_of(cls):
    key = CLASS_KEYS.get(cls)
    if key is None:
        raise ExitGroupsError(
            f"知らない群「{cls}」(CLASS_KEYS に無い) ― 群の名が増えたら、"
            "顧客に出す呼び方を人が決めてから足すこと")
    return key


def is_ahead(game):
    """その局で一度でも +300 以上になったか。**`scores` に `None` が混じる**(実物で 4 件)。"""
    return any(s is not None and s >= AHEAD_CP for s in game.get("scores") or [])


def band_of(value):
    """評価の区分(2 = 優勢・1 = 互角・0 = 劣勢)。

    **新しい閾値ではない** ― 顧客に出る「数え方」の節が既に
    「+300 以上を優勢、−300 以下を劣勢、その間を互角」と書いている(`exit_index.COUNTING_NOTES`)。
    """
    if value is None:
        return None
    if value >= AHEAD_CP:
        return 2
    if value <= -AHEAD_CP:
        return 0
    return 1


def collapses_of(game):
    """その局の**崩れの回数**。`scores` の**隣り合う組**に「数え方」の規則を当てる。

    **局ごとの欄は材料に無い。**実物で 3 つの数が並んでいて、どれも冊子の 79 ではなかった ―
    `overview.fell` = **79**(冊子に出る数)・`len(events)` = **155**・
    `sum(games[].events)` = `sum(len(games[].marks))` = **133**。
    **はじめ `games[].events` を崩れとして使い、合計の番人が 133 ≠ 79 で落とした**(2026-09-29)。
    `events` の一覧に規則を当てても **53** で合わない(あの一覧は崩れの全部ではない)。
    **`scores` の隣り合う組に当てると 79 で一致した**(既知の正解で校正した)。
    合計は毎回 `overview.fell` と突き合わせる ― **写しがずれたらそこで止まる。**
    """
    scores = game.get("scores") or []
    n = 0
    for before, after in zip(scores, scores[1:]):
        a, b = band_of(before), band_of(after)
        if a in (1, 2) and b is not None and b < a:
            n += 1
    return n


def group_rows(recognition, patient, direct=None, side_match=None):
    """群ごとの既存指標(**数だけ**)。合計が材料の合計と違えば落とす。"""
    rows = recognition["rows"]
    games = patient["games"]
    ids = {g["id"] for g in games}
    if ids != set(rows):
        missing = sorted(ids - set(rows))
        extra = sorted(set(rows) - ids)
        raise ExitGroupsError(
            f"局の集合が合わない(認識に無い局 {missing} / 報告に無い局 {extra}) ― "
            "戦型の認識と今回の報告が同じ 25 局を見ているか確かめること")
    key_of_game = {gid: class_key_of(rows[gid]["proposalSignatureClass"]) for gid in ids}
    # ラベルに入れる局数。**材料の合計をそのまま使う**(群に割った合計との一致は `_check_totals`)。
    total_games = (patient.get("summary") or {}).get("games")

    out = []
    for key in GROUP_ORDER:
        members = sorted(g["id"] for g in games if key_of_game[g["id"]] == key)
        if not members:
            continue
        mine = [g for g in games if g["id"] in set(members)]
        ahead = [g for g in mine if is_ahead(g)]
        row = {
            "key": key,
            # **ラベルは 1 か所の対応表から**(局数は材料の合計 ― ここで数え直さない)。
            "label": label_of(key, total_games),
            "gameNos": [g["no"] for g in mine],
            "gameIds": members,
            "games": len(mine),
            "aheadGames": len(ahead),
            "aheadLossGames": sum(1 for g in ahead if g["result"] == "負け"),
            # **崩れは局ごとの欄が材料に無い**(`collapses_of` の注のとおり 3 つの数が全部違った)。
            "collapses": sum(collapses_of(g) for g in mine),
        }
        if side_match is not None:
            row["sideMatch"] = _side_of(side_match, set(members))
        if direct is not None:
            row["cross"] = _cross_of(direct, set(members))
        out.append(row)

    _check_totals(out, patient, direct, side_match)
    return out


def _side_of(side_match, member_ids):
    """群の中の**側の一致**(攻め・自玉側それぞれ 分子 / 分母)。

    **`side_match_of` が返した局面ごとの欄をそのまま振り分ける**(数え直さない)。
    鍵は `(kifuId, displayPly)` なので `kifuId` で群に割れる。
    **重複で捨てた局面(`None`)は分母にも分子にも入れない。**
    """
    buckets = {"attack": {"n": 0, "collapsed": 0}, "defense": {"n": 0, "collapsed": 0}}
    for (kifu_id, _ply), row in (side_match.get("rows") or {}).items():
        if kifu_id not in member_ids or not row:
            continue
        side = row["top1Side"]
        if side not in buckets:
            continue
        buckets[side]["n"] += 1
        if row["actualSide"] in (side, "both"):
            buckets[side]["collapsed"] += 1
    return buckets


def _cross_of(direct, member_ids):
    """群の中の**第 1 候補の印 × 実戦の印**(`check_answer.CROSS_TAGS` の印だけ)。

    **`sacrifice` は入れない** ― `CROSS_TAGS` が `drop` だけなのは
    「同じ言葉に 2 つの分母が付く」を避けた決定(P-156)で、**ここで広げない**。
    """
    answers = [a for a in CA.direct_answers_of(direct) if a["kifuId"] in member_ids]
    out = {}
    for tag in CA.CROSS_TAGS:
        hit = [a for a in answers if (a.get("top1Tags") or {}).get(tag)]
        both = [a for a in hit if (a.get("actualTags") or {}).get(tag)]
        out[tag] = {"positions": len(hit), "bothPositions": len(both),
                    "games": len({a["gameNo"] for a in hit})}
    return out


def _check_totals(out, patient, direct, side_match):
    """**群に割った数の合計が、材料がすでに持っている合計と同じか。**違えば落とす。"""
    def same(what, got, want):
        if got != want:
            raise ExitGroupsError(
                f"群に割った {what} の合計 {got} が材料の {want} と違う ― "
                "数え方の写しがずれている(黙って違う数を出さない)")

    same("局数", sum(r["games"] for r in out), patient["summary"]["games"])

    numbers = next((f["numbers"] for f in patient["findings"] if f["kind"] == "aheadLoss"), None)
    if numbers:
        same("優勢になった局", sum(r["aheadGames"] for r in out), numbers["aheadGames"])
        same("うち負けた局", sum(r["aheadLossGames"] for r in out), numbers["aheadLossGames"])

    fell = (patient.get("overview") or {}).get("fell")
    if fell is not None:
        same("崩れ", sum(r["collapses"] for r in out), fell)

    if side_match is not None:
        for side in ("attack", "defense"):
            same(f"側の一致({side})の分母",
                 sum(r["sideMatch"][side]["n"] for r in out), side_match[side]["n"])
            same(f"側の一致({side})の分子",
                 sum(r["sideMatch"][side]["collapsed"] for r in out),
                 side_match[side]["collapsed"])

    if direct is not None:
        for tag in CA.CROSS_TAGS:
            c = CA.top1_actual_cross(direct, tag)
            same(f"観測({tag})の分母", sum(r["cross"][tag]["positions"] for r in out),
                 c["positions"])
            same(f"観測({tag})の分子", sum(r["cross"][tag]["bothPositions"] for r in out),
                 c["bothPositions"])


# ==================== 顧客に出す行(数だけ・割合を出さない) ====================
# **語は既存から。**「攻め」「自玉側」は `check_answer.SIDE_LABEL_JP`、
# 「駒を打つ手」は `exit_candidates.CROSS_PHRASE_JP` から引く(写さない)。
def lines_of(rows, cross_phrase):
    """観測の欄に置く行。**1 群 1 行。割合・%・比べる語を入れない。**"""
    out = []
    for r in rows:
        # **行の見出しに「普段」が出ないこと**(司令塔が名指しした 2 本目の守り)。
        # `label_of` とは別にここでも見る ― ラベルを別の道で入れた行が、**印字の手前で止まる。**
        check_label_words(r["label"])
        parts = [f"{r['games']} 局"]
        parts.append(f"一度は優勢になった局 {r['aheadGames']}(うち負けた局 {r['aheadLossGames']})")
        parts.append(f"崩れ {r['collapses']} 回")
        sm = r.get("sideMatch")
        if sm:
            for side in ("attack", "defense"):
                label = CA.SIDE_LABEL_JP[side]
                b = sm[side]
                parts.append(f"第 1 候補が{label}の手だった分かれ道 {b['n']}"
                             f"(実戦も{label}の手 {b['collapsed']})")
        cross = r.get("cross")
        if cross:
            for tag, c in cross.items():
                what = cross_phrase[tag]
                parts.append(f"第 1 候補が{what}だった分かれ道 {c['positions']}"
                             f"(実戦も{what} {c['bothPositions']})")
        out.append(f"- {r['label']}: " + "、".join(parts) + "。")
    return out
