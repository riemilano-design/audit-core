# -*- coding: utf-8 -*-
# **`prose.json` の 1 場面から「盤に渡す値」を決める判断を、1 か所に置く。**
#
# 【なぜ抜き出したか】STEP CUSTOMER-EXIT の後半(本編 md → PDF)で、本編の `<!-- pos: -->` の印に
# **付録 1 と同じ盤**を出す必要がある。**写すと 1 手ずれる** ―
# 実際に自動化レーンが司令塔への報告で `type == "move"` の分岐を**逆に説明した**
# (2026-09-29。「写し間違いでも盤が 1 手ずれても試験は通る」と自分で書いた便の中で写し間違えた)。
# **ずれても試験は通ってしまう**(材料と PDF の両方が同じ写し間違いで揃うため)。
# だから**判断だけを 1 か所にし、`_mid.py` と後半の両方がここを呼ぶ**(写しを 2 か所に持たない ― P-111 の病気)。
#
# 【ここに置くのは「判断」だけ。`Board` の組み立ては呼ぶ側に残す】
# `Board`・`Legend`・色・見出しの文は `_util.py`・`_mid.py` の断片にあり、
# **`_util.py` は `build.sh` で連結される断片なので import できない**(`m`・`_data_dir` が先に要る)。
# 1 手ずれの危険は**どの添字の SFEN を渡すか・`usi` を渡すか**の側にあるので、そこだけを持つ。
#
# 【この分岐は既存のもの。新しく決めていない】`_mid.py` の 161〜169 行が持っていた形をそのまま。


class BoardSpecError(Exception):
    pass


def scene_spec(scene, sfens, moves):
    """`prose.json` の 1 場面 → 盤に渡す値。

    引数:
      scene: `{"type": …, "ply": …, "text": …}`(`prose.json` の `scenes[]` の 1 件)
      sfens: `sfens.json` の その局の `sfens`(0 件目が初期局面)
      moves: 同じ局の `moves`(USI。`moves[i]` が `sfens[i] → sfens[i+1]`)

    返り値: `{"kind", "ply", "sfen", "usi", "wants_arrows"}`
      - `kind == "move"`(本人が指した場面)  → **指す前**の局面(`sfens[ply - 1]`)・`usi` は渡さない・
        矢印は呼ぶ側が `events` から作る(実戦の手と第 1 候補)
      - `kind == "opponent"`(それ以外)      → **相手が指した後**の局面(`sfens[ply]`)・`usi = moves[ply - 1]`

    **`ply` は `len(sfens) - 1` で切り詰める**(既存の `min(...)`)。
    切り詰めを外すと、終局の直後を指す場面で添字が範囲外になる。
    """
    if not sfens:
        raise BoardSpecError("sfens が空(この局の局面が材料に無い)")
    raw_ply = scene.get("ply")
    if raw_ply is None:
        raise BoardSpecError(f"場面に ply が無い: {scene!r}")
    ply = min(int(raw_ply), len(sfens) - 1)
    if ply < 1:
        raise BoardSpecError(f"ply が 1 未満になった: {raw_ply}(局面が足りない)")
    if scene.get("type") == "move":
        return {"kind": "move", "ply": ply, "sfen": sfens[ply - 1],
                "usi": None, "wants_arrows": True}
    if ply - 1 >= len(moves):
        raise BoardSpecError(f"{ply} 手目の指し手が材料に無い(moves は {len(moves)} 件)")
    return {"kind": "opponent", "ply": ply, "sfen": sfens[ply],
            "usi": moves[ply - 1], "wants_arrows": False}


def user_sente(side):
    """盤の向き。**`_mid.py` と同じ判定**(`patient_report_data.json` の `games[].side`)。"""
    return side == "先手"


def user_sente_from_sfens(record):
    """付録 3 の材料と同じ向きの判定(`sfens.json` の `side`)。

    `_head.py`・`render_direct.py` が使っているのと同じ ― `"gote"` なら本人が後手。
    """
    return record.get("side") != "gote"


# ==================== 付録 3 の盤(分かれ道・最終局面) ====================
# **付録 3 の判断も、付録 1 と同じ理由でここに置く**(司令塔の指示 2026-09-29)。
#
# 【材料の `sfen` は盤に使わない】`render_direct.py` の 22〜26 行が理由を持っている:
# **`direct_answers.json` の `sfen`・USI は「本人 = 先手」に正規化された記録**で、
# mirrored の局は `rotate_usi` で本人が指した向きへ戻してから当てる。
# **正規化された sfen をそのまま描くと、後手の局で盤が逆になる。**
# だから盤は **`sfens.json`(本人が指した実際の向き)**から引く。
# **自動化レーンは最初「材料が SFEN を持つので `sfens.json` は要らない」と書いた** ― 間違いだった。
# **材料が値を持っていることと、組版がその値を使っていることは別**(2026-09-29 の教訓)。
#
# 【向きの規則は付録 1 と違う】付録 1 は `patient_report_data.json` の `games[].side`(「先手」/「後手」)。
# 付録 3 は **`sfens.json` の `side`**(`"gote"` なら mirrored)。**材料が別なので規則も別。**


def fork_spec(answer, sfens_record):
    """分かれ道の盤(`render_direct.py` 495〜499 行と同じ判断)。

    **`sfens[dply - 1]` ― 指す前の局面。**`dply` にすると 1 手先を見せることになり、
    「この手を指す前にどう見えていたか」という文と盤が食い違う。
    """
    sfens = sfens_record.get("sfens") or []
    if not sfens:
        raise BoardSpecError("sfens が空(この局の局面が材料に無い)")
    dply = answer.get("displayPly")
    if dply is None:
        raise BoardSpecError(f"分かれ道に displayPly が無い: {answer.get('kifuId')}")
    idx = int(dply) - 1
    if not 0 <= idx < len(sfens):
        raise BoardSpecError(
            f"{dply} 手目の 1 手前が材料に無い(sfens は {len(sfens)} 件)")
    return {"kind": "fork", "ply": int(dply), "sfen": sfens[idx],
            "mirrored": is_mirrored(sfens_record),
            "user_sente": user_sente_from_sfens(sfens_record)}


def final_spec(entry, sfens_record):
    """最終局面の盤(`render_direct.py` 560〜562 行と同じ判断)。

    **`sfens[-1]` ― 最後の局面**(本人が指した実際の向き)。
    **手数は `entries[].moves`**(`displayPly` ではない ― 検査 7 が受ける鍵もこれ)。
    """
    sfens = sfens_record.get("sfens") or []
    if not sfens:
        raise BoardSpecError("sfens が空(この局の局面が材料に無い)")
    moves = entry.get("moves")
    if moves is None:
        raise BoardSpecError(f"最終局面に moves が無い: {entry.get('kifuId')}")
    return {"kind": "final", "ply": int(moves), "sfen": sfens[-1],
            "mirrored": is_mirrored(sfens_record),
            "user_sente": user_sente_from_sfens(sfens_record)}


def is_mirrored(sfens_record):
    """本人が後手か(`render_direct.py` と同じ ― `sfens.json` の `side` が `"gote"`)。"""
    return sfens_record.get("side") == "gote"


# ==================== 盤に渡す指し手の向き ====================
# **`render_direct.py` から移した**(写していない ― 2026-09-29 の司令塔の条件 1)。
#
# 【なぜここに移すか】本編の md にも同じ盤を出す(`exit_body.py`)。矢印の USI は
# **「盤に何を渡すか」の一部**であり、`render_direct.py` は冒頭で `sys.argv` を読んで走る形なので
# **import できない**。写せば P-111 の病気(同じ関数が 2 実装)をもう 1 つ作る。
#
# 【移したのはこの 4 つ】`rotate_usi` は `rotate_square` だけに依り、`rotate_square` は `RANKS` に依る。
# **`RANKS` は `render_direct.py` の `sq()` も使っている**ので、あちらは定義を消して**ここの 1 つを束縛する**
# (定義を 2 つにしない)。**自動化レーンは最初「`rotate_square` 以外から使われていない」と書いた** ―
# 出現が 3 行であることだけを見て、内訳を確かめなかった誤り。移した直後に `NameError` で鳴って分かった。
# **数えただけで内訳を書かない**(2026-09-29 の 4 つ目の同型)。
#
# 【残る写し 1 つ】`render_whatif.py` にも `rotate_usi` の写しがある。**触らない**
# (付録 2 は正本の束に入っていない ― 司令塔の条件 2)。既知事項に 1 行残す。
#
# 【移す前の校正値(実測 2026-09-29。c5 の材料の USI 856 件)】
# 往復 856/856、打つ手 306 件・成る手 92 件、全件の写像の指紋
# sha256 = 3eae09155296e667cfd8752f9b5e030f8f233e7ff4a4bd886c84b4d2349231a3
# `3a1c+` → `7i9g+`、`B*8a` → `B*2i`、`6a7b` → `4i3h`。
# ==================== 持ち駒の語(P-176。2026-09-29) ====================
# **同じ局面の持ち駒が、本編と付録で違う書き方だった**(批評席 (a) が 4 周目に実物で挙げた) ―
# 本編「桂二 香 歩二」(`board_draw.py`)・付録 3「桂二　香一　歩二」(`render_direct.py`)。
# **1 枚のときに数を付けるかと、区切りの空白の幅**の 2 つが違っていた。
# **P-111 の家族**(同じものを 4 つの実装が別々に組んでいる: `board_draw`・`fig1`・
# `render_direct`・`render_whatif`)。**ここを 1 か所にして 4 つが呼ぶ。**
#
# **形は本編に揃えた**(1 枚は数を付けない・半角の空白)。本編は顧客が最初に読む冊子で、
# 席は付録の側を「揃っていない」と挙げた。**形を変えるならここ 1 行を変えれば 4 つとも変わる。**
HAND_KAN = "〇一二三四五六七八九"
HANDS_SEPARATOR = " "
HANDS_EMPTY = "なし"


def hand_word(piece, count):
    """持ち駒 1 種類の語。**1 枚のときは数を付けない**(将棋の持ち駒の書き方)。

    `count` が 0 以下なら `None`(呼ぶ側が落とす)。10 枚以上は算用数字
    (`HAND_KAN` が 1 桁しか持たないため。実物では歩が 18 枚まで在りうる)。
    """
    if count <= 0:
        return None
    if count == 1:
        return piece
    return piece + (HAND_KAN[count] if count < 10 else str(count))


def hands_phrase(words):
    """持ち駒の行。**空なら「なし」**(空文字にすると枠だけが残って読めない)。"""
    return HANDS_SEPARATOR.join(w for w in words if w) or HANDS_EMPTY


RANKS = "abcdefghi"


def rotate_square(token):
    f, r = int(token[0]), token[1]
    return f"{10 - f}{RANKS[len(RANKS) - 1 - RANKS.index(r)]}"


def rotate_usi(usi):
    """USI を 180 度回す(打つ手は打つ先だけ・成りの `+` は末尾に残す)。"""
    if usi[1] == "*":
        return f"{usi[0]}*{rotate_square(usi[2:4])}"
    suffix = usi[4:]
    return rotate_square(usi[0:2]) + rotate_square(usi[2:4]) + suffix


def genuine_move(usi, mirrored):
    """材料の USI(本人 = 先手に正規化された向き)を、**本人が指した実際の向き**へ戻す。"""
    return rotate_usi(usi) if mirrored and usi is not None else usi
