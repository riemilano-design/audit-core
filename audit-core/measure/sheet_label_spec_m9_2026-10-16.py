# -*- coding: utf-8 -*-
"""段 9 の正解ラベルの定義。**会計の 2 本だけを差し替える薄い層。**

封 docs/DOMAIN1_M9_SEAL_2026-10-16.md §3-4。

段 6〜段 8 の採点器が読む `sheet_label_spec_2026-10-15.py` は**凍結したまま**にする
(凍結した結果が再現できなくなるため)。だからこの file は

  * 凍結した `SPEC` を読み込み、**version と会計の 2 本だけ**を差し替える
  * 問いの**生成器と検査器は凍結した側のものをそのまま使う**
    (`question_text(spec)` / `check_question(text, spec)` は spec を引数に取る)

直す理由(封 §3-4 に実測つきで書いた)。旧の R-会計-2 は

  > 表 3(明細)の「会計」欄に `東京都○○会計` と書かれていても、
  > **`東京都` を外した表 1 の名前**で答えてください。

と**無条件に**指示していた。一方 `normalize_answer` は**裏づけの在る別名だけ**を畳む。
だから裏づけの無い `東京都と場会計` では、**問いに従った席の回答(と場会計)と
engine の答え(東京都と場会計)が食い違う。**
③が 3 段続けて発火していなかったので、この食い違いも発火していなかった。

新しい規則は **6 欄の答えを「抜粋の行の住所」にする**。
会計の欄は**指している行に書かれている字のまま**。これで席と engine が同じ規則で書く。
"""
import copy
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))

_sp = importlib.util.spec_from_file_location(
    "label_spec_frozen", os.path.join(HERE, "sheet_label_spec_2026-10-15.py"))
L = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(L)

M2 = L.M2
norm = L.norm
FIELDS = L.FIELDS
PARENT_SEP = L.PARENT_SEP
COLUMN_ALIAS = L.COLUMN_ALIAS
normalize_answer = L.normalize_answer
engine_label = L.engine_label
field_line = L.field_line
verdict_line = L.verdict_line

VERSION = "2026-10-16/m9"

# **差し替えるのはこの 2 本だけ。**他の規則・欄・保留の選択肢・例は触らない。
# 欄の説明も旧の意味のままだった(「表 1 の「会計別」に在る名前」)。**ここも直す。**
SAYS_REPLACED = {
    "会計": "指している行の「会計」欄に書かれている字(表 1 の名前に直さない)",
}

RULES_REPLACED = {
    "R-会計-1": "会計の欄は、**指している行の「会計」欄に書かれている字をそのまま**"
                "書いてください。",
    # **規則は 1 通りに読める字で書く**(記憶 `seal-rule-wording-must-be-executable.md`)。
    # 当たる例と当たらない例を両方添える。
    "R-会計-2": "表 1 は会計の名前の一覧です。**表 1 の名前に直したり、"
                "`東京都` を付けたり外したりしないでください。**"
                "(例: 表の「会計」欄が `東京都と場会計` なら `東京都と場会計` と書く。"
                "`一般会計` と書かれていれば `一般会計` と書く。"
                "`東京都と場会計` を `と場会計` に直してはいけない)",
}


def verify(spec, frozen=None):
    """**差し替えたのが会計の 2 本と会計の欄の説明だけ**であることを確かめる。

    `_build` から切り出してある。正常な入力では発火しない守りなので、
    試験が**壊した spec を食わせて赤を確かめられる**ようにする
    (記憶 `guard-that-only-fires-on-failure.md`)。
    """
    f0 = frozen or L.SPEC
    for rid, body in RULES_REPLACED.items():
        if rid not in f0["rules"]:
            raise AssertionError("差し替える規則が凍結した SPEC に無い: %s" % rid)
        if spec["rules"].get(rid) != body:
            raise AssertionError("規則 %s が差し替わっていない" % rid)
        if body == f0["rules"][rid]:
            raise AssertionError("規則 %s が旧と同じ字になっている(直っていない)" % rid)
    for rid, body in f0["rules"].items():
        if rid in RULES_REPLACED:
            continue
        if spec["rules"].get(rid) != body:
            raise AssertionError("差し替えていない規則が動いた: %s" % rid)
    if sorted(spec["rules"]) != sorted(f0["rules"]):
        raise AssertionError("規則の本数が動いた")
    if tuple(f["key"] for f in spec["fields"]) != FIELDS:
        raise AssertionError("欄が動いた")
    frozen_fields = {f["key"]: f for f in f0["fields"]}
    for f in spec["fields"]:
        g = frozen_fields[f["key"]]
        if f["key"] in SAYS_REPLACED:
            if f["says"] != SAYS_REPLACED[f["key"]]:
                raise AssertionError("欄 %s の説明が差し替わっていない" % f["key"])
            if f["says"] == g["says"]:
                raise AssertionError("欄 %s の説明が旧と同じ(直っていない)" % f["key"])
        elif f["says"] != g["says"]:
            raise AssertionError("差し替えていない欄の説明が動いた: %s" % f["key"])
        if tuple(f["blank_at"]) != tuple(g["blank_at"]):
            raise AssertionError("欄 %s の空欄の層が動いた" % f["key"])
        if tuple(f["rules"]) != tuple(g["rules"]):
            raise AssertionError("欄 %s の規則の対応が動いた" % f["key"])
    if spec["verdicts"] != f0["verdicts"]:
        raise AssertionError("保留の選択肢が動いた")
    if spec["examples"] != f0["examples"]:
        raise AssertionError("例が動いた")
    if spec["version"] == f0["version"]:
        raise AssertionError("version を上げていない")
    return True


def _build():
    spec = copy.deepcopy(L.SPEC)
    spec["version"] = VERSION
    for rid, body in RULES_REPLACED.items():
        spec["rules"][rid] = body
    for f in spec["fields"]:
        if f["key"] in SAYS_REPLACED:
            f["says"] = SAYS_REPLACED[f["key"]]
    verify(spec)
    return spec


SPEC = _build()


def question_text(spec=None):
    """**手書きしない。**凍結した生成器に段 9 の `SPEC` を渡す。"""
    return L.question_text(spec or SPEC)


def check_question(text, spec=None):
    """**凍結した検査器**で、問いに `SPEC` の必須条件が全部在るか確かめる。"""
    return L.check_question(text, spec or SPEC)


def diff_from_frozen():
    """旧との差を**字で**出す(記録に書くため)。"""
    out = {rid: {"旧": L.SPEC["rules"][rid], "新": SPEC["rules"][rid]}
           for rid in sorted(RULES_REPLACED)}
    frozen = {f["key"]: f["says"] for f in L.SPEC["fields"]}
    now = {f["key"]: f["says"] for f in SPEC["fields"]}
    for k in sorted(SAYS_REPLACED):
        out["欄 %s の説明" % k] = {"旧": frozen[k], "新": now[k]}
    return out


if __name__ == "__main__":
    import hashlib
    import json
    q = question_text()
    old = L.question_text()
    check_question(q)
    print("段 9 の問い: sha256 %s / %d 字 / version %s"
          % (hashlib.sha256(q.encode("utf-8")).hexdigest()[:16], len(q),
             SPEC["version"]))
    print("段 8 の問い: sha256 %s / %d 字 / version %s"
          % (hashlib.sha256(old.encode("utf-8")).hexdigest()[:16], len(old),
             L.SPEC["version"]))
    print("差し替えた規則:", json.dumps(diff_from_frozen(), ensure_ascii=False,
                                        indent=1))
    # **旧の問いは段 9 の検査器を通ってはいけない**(直しが効いている証拠)
    try:
        check_question(old)
        print("**旧の問いが段 9 の検査器を通った ― 直しが効いていない**")
        raise SystemExit(1)
    except AssertionError as e:
        print("旧の問いは段 9 の検査器で落ちる(正しい):", str(e)[:90])
