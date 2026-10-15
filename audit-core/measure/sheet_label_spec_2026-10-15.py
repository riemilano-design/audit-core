# -*- coding: utf-8 -*-
"""正解ラベルの定義を**ただ 1 か所**に置く(人間の指示 2026-10-15 の ①)。

> 正解ラベルの定義を**単一の構造化データ**に置き、そこから採点用の問いを生成するか、
> 少なくとも両者の必須条件を機械的に比較してください。
> **規則と問いの対応が一つでも不一致なら、ラベル材料を生成できない。**

段 5 の失敗は、封 §1-1 に「会計は総括の表記」と書いたのに、
**席に渡す問いへその規則を写していなかった**ことだった(誤受理 5 件 = 失敗の全部)。
だからこの file では:

  `SPEC`            正解の定義(欄・空欄になる層・正本の規則・例・保留の選択肢)
  `question_text()` **`SPEC` から問いの字を組み立てる**(手書きしない)
  `check_question()` 問いに `SPEC` の必須条件が全部載っているかを機械で確かめる
  `normalize_answer()` 席の回答を `SPEC` の規則で同じ形に正規化する

`check_question` が落ちたら材料は作れない(呼び出し側が例外で止まる)。
"""
import importlib.util
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

_spec = importlib.util.spec_from_file_location(
    "m2_for_spec", os.path.join(HERE, "sheet_m2_structure_2026-10-15.py"))
M2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M2)
norm = M2.norm

LEVELS = ("会計", "合計", "款", "項", "目")
PARENT_SEP = " > "

# --------------------------------------------------------------- 正解の定義
# **表の構造で確かめた列の別名**(明細の字 -> 正本)。`SPEC` の R-列-2 と対応していること
# を門で確かめる。値の一致だけで足してはいけない。
COLUMN_ALIAS = {"計": "予算現額"}

SPEC = {
    "version": "2026-10-15/m6",
    "fields": [
        {"key": "会計", "from": "scope", "blank_at": (),
         "says": "表 1 の「会計別」に在る名前(総括の表記)",
         "rules": ("R-会計-1", "R-会計-2")},
        {"key": "階層", "from": "level", "blank_at": (),
         "says": "会計 / 合計 / 款 / 項 / 目 のどれか 1 つ",
         "rules": ("R-階層-1",)},
        {"key": "親", "from": "parent", "blank_at": ("会計", "合計", "款"),
         "says": "その行の親の科目名。項なら款名、目なら「款名%s項名」" % PARENT_SEP,
         "rules": ("R-親-1", "R-親-2", "R-親-3")},
        {"key": "科目名", "from": "name", "blank_at": ("会計", "合計"),
         "says": "款名・項名・目名",
         "rules": ("R-科目名-1",)},
        {"key": "列", "from": "column", "blank_at": (),
         "says": "表の列の見出し",
         "rules": ("R-列-1", "R-列-2")},
        {"key": "値", "from": "value", "blank_at": (),
         "says": "表に書かれているその数(カンマ無しの整数)",
         "rules": ("R-値-1",)},
    ],
    # **ここが正本。問いの字はここから作る**
    "rules": {
        "R-会計-1": "会計の欄は、**表 1(総括)に書かれている名前**で書いてください。",
        "R-会計-2": "表 3(明細)の「会計」欄に `東京都○○会計` と書かれていても、"
                    "**`東京都` を外した表 1 の名前**で答えてください"
                    "(例: 表 3 が `東京都一般会計` なら `一般会計` と書く)。",
        "R-階層-1": "階層の欄は %s のどれか 1 つだけを書いてください。"
                    "他の語(会計別・款別 など)は書かないでください。" % " / ".join(LEVELS),
        "R-親-1": "親の欄は、**項なら款名**、**目なら「款名%s項名」**(間は半角の > と空白)"
                  "で書いてください。" % PARENT_SEP,
        "R-親-2": "会計・合計・款 の行は、親の欄を**空欄**にしてください。",
        "R-親-3": "親を表から読み取れないときは、**推測で埋めず**「判定不能」を選んでください。",
        "R-科目名-1": "会計・合計 の行は、科目名の欄を**空欄**にしてください。",
        "R-列-1": "列の欄は、表の列の見出しをそのまま書いてください。",
        # この組は**表の構造(明細の見出しが予算現額の下に在る)**で同一と確かめた。
        # 値が一致しただけの組は入れない。門 ColumnAliasTest が材料と突き合わせる。
        "R-列-2": "表 2 の `予算現額` と表 3 の `計` は**同じ列として採点します**"
                  "(明細の見出しが `予算現額` の下に在るため)。どちらの字で書いても構いません。",
        "R-値-1": "値の欄は、表に書かれている数をカンマ無しの整数で書いてください。",
    },
    "verdicts": {
        "根拠なし": "その金額が表に見当たらない",
        "判定不能": "文からはどれを指すか決められない(複数に当たる / 親が決まらない など)",
    },
    "examples": [
        {"id": "R001", "会計": "一般会計", "階層": "款", "親": "", "科目名": "福祉費",
         "列": "支出済額", "値": 1066495914576},
        {"id": "R002", "会計": "一般会計", "階層": "目",
         "親": "福祉費%s子供・子育て支援費" % PARENT_SEP,
         "科目名": "児童福祉施設費", "列": "支出済額", "値": 219337467055},
        {"id": "R003", "会計": "合計", "階層": "合計", "親": "", "科目名": "",
         "列": "歳入決算額", "値": 15769405199513},
        {"id": "R004", "verdict": "判定不能"},
    ],
}
FIELDS = tuple(f["key"] for f in SPEC["fields"])


# --------------------------------------------------------- 問いを SPEC から作る
def question_text(spec=None):
    """**手書きしない。**`SPEC` から組み立てる。"""
    s = spec or SPEC
    out = [u"以下に (A) 自治体の令和６年度決算の表の抜粋と、"
           u"(B) ある報告文から抜き出した金額の一覧があります。",
           u"(B) の各行について、その金額が (A) の表のどこの数かを答えてください。",
           u"",
           u"答える欄は %d つです。" % len(s["fields"])]
    for f in s["fields"]:
        out.append(field_line(f))
    out += [u"", u"**守ってほしい書き方(この規則で採点します)**"]
    for rid in _rule_order(s):
        out.append(u"  [%s] %s" % (rid, s["rules"][rid]))
    out += [u"", u"表のどこの数とも決められない場合は、次のどちらかを書いてください。"]
    for k, v in s["verdicts"].items():
        out.append(verdict_line(k, v))
    out += [u"", u"出力は JSON の配列だけにしてください。説明や前置きは書かないこと。",
            u"各要素は次の形です。"]
    for ex in s["examples"]:
        out.append(u"  " + json.dumps(ex, ensure_ascii=False))
    return u"\n".join(out)


def verdict_line(k, v):
    """保留の選択肢 1 つの行(生成と検査で同じ字)。"""
    return u"  %s … %s" % (k, v)


def field_line(f):
    """欄 1 つの行。**`question_text` と `check_question` が同じこの関数を使う。**"""
    line = u"  %s … %s" % (f["key"], f["says"])
    if f["blank_at"]:
        line += u"(%s の行は空欄)" % " ・ ".join(f["blank_at"])
    return line


def _rule_order(s):
    seen = []
    for f in s["fields"]:
        for rid in f["rules"]:
            if rid not in seen:
                seen.append(rid)
    for rid in s["rules"]:
        if rid not in seen:
            seen.append(rid)
    return seen


def check_question(text, spec=None):
    """問いに `SPEC` の必須条件が全部載っているかを確かめる。

    **一つでも欠けたら例外。**呼び出し側はこれで材料を作れなくなる。
    """
    s = spec or SPEC
    missing = []
    for f in s["fields"]:
        # **欄は「生成したその行そのもの」が在ることを要求する**(語が別の所に在っても通さない)
        if field_line(f) not in text:
            missing.append("欄 %s の行" % f["key"])
    if ("答える欄は %d つです。" % len(s["fields"])) not in text:
        missing.append("欄の数の行")
    for rid, body in s["rules"].items():
        if body not in text:
            missing.append("規則 %s の字" % rid)
        if rid not in text:
            missing.append("規則 %s の記号" % rid)
    for k, v in s["verdicts"].items():
        if verdict_line(k, v) not in text:
            missing.append("保留の選択肢 %s の行" % k)
    for ex in s["examples"]:
        if json.dumps(ex, ensure_ascii=False) not in text:
            missing.append("例 %s" % ex.get("id") or "verdict")
    if missing:
        raise AssertionError(
            "問いが SPEC と一致しない(材料を作れない): %s" % "・".join(missing))
    return True


# ------------------------------------------------- 席の回答を同じ形に正規化する
def normalize_answer(ans, alias=None):
    """`SPEC` の規則で席の回答を揃える。

    **文字列が似ているだけで同一と決めない**(人間の指示)。
    会計の欄は、**材料から独立した裏づけ 3 本で確かめた別名表**だけを使って直す。
    裏づけが無い `東京都○○会計` は**直さない**(直したら「表記が違うだけで同一」になる)。
    """
    if ans.get("verdict"):
        return {"verdict": norm(ans["verdict"])}
    out = {}
    for f in SPEC["fields"]:
        v = ans.get(f["key"])
        out[f["key"]] = _norm_field(f["key"], v, alias)
    return out


def _norm_field(key, v, alias):
    if v is None:
        return ""
    if key == "値":
        if isinstance(v, (int, float)):
            return str(int(v))
        t = norm(v).replace(",", "").replace("円", "")
        return t
    if key == "親":
        parts = [p.strip() for p in norm(v).replace(">", ">").split(">") if p.strip()]
        return ">".join(parts)
    if key == "列":
        n = norm(v)
        for written, canon in COLUMN_ALIAS.items():
            if n == norm(written):
                return norm(canon)
        return n
    if key == "会計" and alias:
        n = norm(v)
        for written, rec in alias.items():
            if norm(written) == n:
                return norm(rec["canonical"])
        return n
    return norm(v) or ""


def engine_label(bind, alias=None):
    """engine の接続先を**席と同じ形**にする(欄の対応は SPEC が持つ)。"""
    if bind["state"] != "GROUNDED":
        return None
    e = bind["evidence"] or {}
    lv = norm(e.get("level")) or ""
    raw = {}
    for f in SPEC["fields"]:
        if lv in tuple(norm(x) for x in f["blank_at"]):
            raw[f["key"]] = ""
        else:
            raw[f["key"]] = e.get(f["from"])
    return {k: _norm_field(k, v, alias) for k, v in raw.items()}
