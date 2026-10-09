# -*- coding: utf-8 -*-
"""**他の席が封じた材料を取らないための、唯一の関門。**

EDINET から ZIP を取る道具は **4 つ**ある(2026-10-09 に数えた):

    fixtures/xbrl/fetch_new_draw_2026-10-09.py   名前で選ぶ(記録の picked)
    fixtures/xbrl/fetch_allocated_2026-10-08.py  名前で選ぶ(記録の assigned)
    fixtures/xbrl/xbrl_probe.py                  **日付で選ぶ**(docID 順に 1 件ずつ取る)
    fixtures/xbrl/select_third_2026-10-01.py     **日付で選ぶ**(共有キャッシュに書く)

**名前の一覧だけでは、日付で選ぶ 2 つを原理的に守れない。**
だから関門は **docID と日付の両方**を持ち、**取る直前に呼ぶ。**

**import は呼び出しではない**(本線の席の指摘、2026-10-09)。
この module を import しただけでは何も守られない ―
``refuse_if_sealed()`` を **urlopen の前に呼ぶ**こと。
呼んでいるかは ``tests/adapters/xbrl/test_fetch_gate.py`` が木を歩いて照合する。

通信しない。ファイルを書かない。
"""

# 外すときは、**その封を持っている席からの依頼**と理由を行に書くこと。
SEALED_DOCS = {
    "S100Z3JY": "本線 封A(正規化方式 round/truncate)の独立確認。抽選 341e079",
    "S100Z35K": "本線 封A(正規化方式 round/truncate)の独立確認。抽選 341e079",
    "S100Z3V1": "本線 封B(符号 abs)の独立確認・引き直し後。抽選 0fc7ec1",
    "S100Z3HP": "本線 封B(符号 abs)の独立確認・引き直し後。抽選 0fc7ec1",
}

# **日付で選ぶ道具のための錠。**
# 封B の 2 件は S100Z3V1 = 2026-09-25、S100Z3HP = 2026-09-24。
# この 2 日を渡すと、名前を指定しなくても到達しうる(docID 順に 1 件ずつ取るので)。
SEALED_DATES = {
    "2026-09-24": "本線 封B の S100Z3HP がこの日の提出。日付で選ぶ道具から到達しうる",
    "2026-09-25": "本線 封B の S100Z3V1 がこの日の提出。日付で選ぶ道具から到達しうる",
}


class SealedMaterial(Exception):
    """封じた材料に触ろうとした。**取得は起きていない。**"""


def refuse_if_sealed(doc_id=None, date=None, where=""):
    """封じた材料なら **例外で止める**。取る直前に呼ぶこと。

    ``doc_id`` も ``date`` も省略可。**両方 None で呼ぶのは誤り**
    (守っているつもりで何も見ていない形になるので、それも止める)。
    """

    if doc_id is None and date is None:
        raise SealedMaterial(
            "refuse_if_sealed() を doc_id も date も無しで呼んでいる(%s)― "
            "何も照合していない" % (where or "呼び出し元不明",))
    if doc_id is not None and doc_id in SEALED_DOCS:
        raise SealedMaterial(
            "**取らない**: %s は他の席が封じた材料(%s)。呼び出し元 %s。"
            "席の間で承認は渡せない" % (doc_id, SEALED_DOCS[doc_id], where or "不明"))
    if date is not None:
        d = str(date)[:10].replace("/", "-")
        if d in SEALED_DATES:
            raise SealedMaterial(
                "**取らない**: %s は封じた日付(%s)。呼び出し元 %s。"
                "日付で選ぶ道具は名前を指定しなくても封じた材料に到達しうる"
                % (d, SEALED_DATES[d], where or "不明"))
    return None
