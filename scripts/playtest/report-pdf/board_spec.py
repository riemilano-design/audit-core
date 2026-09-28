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
