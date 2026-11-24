# -*- coding: utf-8 -*-
u"""封 docs/UNIVERSAL_PROCESS_SEAL_2026-11-24.md(便 UM3)の道具。**費用は 0・API は呼ばない・席は呼ばない。**

型も検査も持たない AI の席(A)が素材の folder から作った ``値の表.json``・``資料.md`` を、便 UM2 の正解と行ごとに照合し、席の会話の記録から作る過程を数える。

    python3 -I universal_process_tally_2026-11-24.py --hand    --co <dir> --seat <dir> --definition <file> --brief <file> --root <dir> --company N --round a|b --period 1|2
    python3 -I universal_process_tally_2026-11-24.py --process  --transcripts <dir> (--folder <dir> ... | --root <dir> [--companies N ...] [--rounds a b]) [--out <file>]
    python3 -I universal_process_tally_2026-11-24.py --tally    --co <dir> --seat <dir> --root <dir> --transcripts <dir> [--um2-hand <dir>] [--companies N ...] [--rounds a b] [--out <file>]
    python3 -I universal_process_tally_2026-11-24.py --tally --record ...     # 本番の 4 社(1〜4)がそろった時だけ fixtures/universal/um3/record.json を書く
    python3 -I universal_process_tally_2026-11-24.py --digest   --root <dir> --transcripts <dir> --out-dir <dir> [--um2-hand <dir>]

folder の形:
    ``<co>/<社>/正解/正解.json``・``<co>/<社>/期1/``・``期2/``(便 UM2 の素材と正解)
    ``<seat>/<社>/指定_期1_A.json``・``指定_期2_A.json``・``出力/判定_期1_A.json``・``出力/置き場_期2_A.json``(便 UM2 の出力。読むだけ)
    ``<root>/<社>/<回>/期1|期2/``(席の folder。``--hand`` が作る。席が ``値の表.json``・``資料.md`` などを書く)。回は ``a`` か ``b``
    ``<um2-hand>/<社>/A/``(便 UM2 の 1 期目の B の席の folder。会話の記録の数だけを数える)

実装の注(封の字では 1 通りに決まらなかった所の素直な読み。結果を見て変えない。報告にも書く):
- 行ごとの結果の名は封 §1-4 のとおり 8 つ(同じ・違う・無いのに在る・無いで同じ・無いで違う・分からない・答えなし・形が読めない)。
  値の表の file が無い→全行 ``答えなし``。file が在るが JSON として読めない・``行`` が並びでない→全行 ``形が読めない``。file は読めるが id の行が無い→その行は ``答えなし``。
  行が dict でない・``状態`` が 3 つのどれでもない・``在る`` なのに ``数値`` の字が符号つきの整数の字でない→``形が読めない``。
  ``数値`` が JSON の整数(真偽値でない)なら、その 10 進の字を数値の字とみなす(JSON の小数・真偽値・null は ``形が読めない``)。字は NFC にそろえ前後の空白を取り、ASCII の 0〜9 だけを数字とする。字が 4000 を超える数は形が読めない(Python の版で変わらないための上限)。
  同じ id の行が 2 つ以上なら最初の 1 つを読み、重複の数を数える。正解の file の項目が読めない(UNREADABLE)行は結果の名に入れず ``正解が読めない行`` に数える。
- 計算の 3 行は、定義表(``fixtures/universal/um0/definition_A.json``)の ``式``(和・比・比の分母和)・``入力``・``桁`` を読んで正解の値から出す。入力に null や読めない正解が在る・割る数が 0 以下の行は ``分母から外した``。
  席の値は符号つきの 10 進の字(小数点つきを許す)だけを読み、10 進の四捨五入(0.5 は 0 から遠い側)で ``桁`` へ丸めて、正解から出した値の同じ丸めと同じなら ``同じ``。
- 関係 R1・R2・R3 は席の値の表の中の ``在る`` の整数だけで見る(入力のどれかが ``在る`` の整数でなければ ``見られない``)。
- 掛け合わせの B は便 UM2 の ``判定_期1_A.json``(止めた行は ``止める`` と ``止める:<規則>`` の 2 つの名に数える。和は 1 つの行に 2 回入る)。
  B の判定に行が無い・file が無い行は ``B なし``。2 期目は ``置き場_期2_A.json`` の ``状態``(在る・確認待ち・保留・無い)。
- 揺れ・自信・資料の数の字: 揺れは回 a と回 b の両方を数える時だけ。``在る`` どうし = 両方の結果が 同じ・違う・無いのに在る のどれか。自信は 高・中・低・``読めない``(行は在るが自信が 3 つのどれでもない)・``なし``(行が無い)。
  資料の数の字は、資料の字を NFKC にそろえ、日付(ISO・スラッシュ)と ``(19|20)ddd 年``・``31 以下の整数 月/日`` を外し、桁区切りのコンマを取り、数字が 2 つ以上並ぶ数(小数点を含み、数字の数が 2 以上)を数える。
  値の表の ``在る`` の整数 v の 4 つの見え方(v・v÷1000・v÷1000000 を表記の小数の桁で四捨五入したもの・v×100)のどれかの絶対値と同じなら当たり。当たらない数の字の数を数える。粗い数で、資料が正しいとは言わない。
- 過程の数えは会話の記録(JSONL)の ``tool_use``・``tool_result`` から(``tool_use`` の id で重ねを除く)。入力は文字列の値を連ねた字(NFC)で見る。素材の file は folder の中身から取り、``素材/`` 無ければ ``期1/`` の中の file。
  file の名が入力に出た(2 期目で ``前の期の素材`` も出る呼び出しは ``素材/<名>`` の形だけ)呼び出しの数を数える。書き込みは Write・Edit・MultiEdit・NotebookEdit の path か、
  Bash などの入力に名と書き込みの形(``>``・``json.dump``・``write``・``open(..,'w')``・``tee``・``cp``・``mv``)が在るもの、または前に書いた .py に名と書き込みの形が在りそれを python で走らせたもの。粗い数。
- 汚れは、入力の絶対の path(``/private``・``/Users``・``/tmp`` など。便 UM2 の dirty2 と同じ根)が席の folder の外、または ``../``・``~/``・``$HOME``。
  根は path の先頭でだけ読む(直前が行頭・空白・引用符・``=``・``(``・``:``・``,``・``;``・``<``・``>``・``file://`` などの時)。``/usr/bin/``・``/usr/local/bin/`` の下は道具の置き場なので数えない。
- 「前の期の成果の道具を走らせた」は粗い数で、走らせた席は下限(`ran_prev_tool`)。

限界(結果の文書はここから写す。どれも「汚れ」「走らせた」を少なく数える側。測っていないことは書かない):
- 汚れ: 根は便 UM2 と同じ 11 個だけ。``/root``・``/bin``・``/dev``・``/System``・``/mnt`` などの根と、根の無い裸の ``/`` は数えない。
- 汚れ: ``cd ..``・``ls ..``・``ls ~``・``${HOME}``・``$PWD/..`` は数えない(数えるのは ``../``・``~/``・``$HOME`` の字)。
- 汚れ: ``//tmp``・``/./tmp``・大文字の根(``/TMP``)は数えない。変数に組み立てた path(``a=/t; b=$a/x`` など)は数えない。
- 走らせた: ``python3 -c`` の中で runpy・exec・import で読む形、``-m pdb`` などの module 経由、``xargs``・``find -exec``・``time``・``nohup`` 越しは数えない(数えない側が下限)。
  python・sh が命令の位置に無い形(``echo python3 <道具>``・``grep sh <道具>``)は数えない。
"""
from __future__ import print_function

import collections
import datetime
import hashlib
import io
import json
import os
import re
import shutil
import sys
import unicodedata
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFS_REL = "fixtures/universal/um0/definition_A.json"
RECORD_REL = "fixtures/universal/um3/record.json"
od = collections.OrderedDict

DEV = (101,)
PROD = (1, 2, 3, 4)
ROUNDS = ("a", "b")
PERIODS = (1, 2)

RESULT_NAMES = (u"同じ", u"違う", u"無いのに在る", u"無いで同じ", u"無いで違う", u"分からない", u"答えなし", u"形が読めない")
STATES = (u"在る", u"無い", u"分からない")
CONF_NAMES = (u"高", u"中", u"低", u"読めない", u"なし")
GOLD_KEYS = [
    (u"a01", u"売上高_当期"), (u"a02", u"売上高_前期"), (u"a03", u"売上総利益_当期"), (u"a04", u"営業利益_当期"), (u"a05", u"営業利益_前期"),
    (u"a06", u"経常利益_当期"), (u"a07", u"当期純利益_当期"), (u"a08", u"減価償却費_当期"), (u"a09", u"現金及び預金_当期末"),
    (u"a10", u"流動資産合計_当期末"), (u"a11", u"資産合計_当期末"), (u"a12", u"短期借入金_当期末"), (u"a13", u"長期借入金_当期末"),
    (u"a14", u"負債合計_当期末"), (u"a15", u"純資産合計_当期末"), (u"a16", u"純資産合計_前期末"),
    (u"a29", u"借入の残高の合計_当期末"), (u"a30", u"期末の従業員数_当期末"),
]
MONTH_KEY = u"月次の売上高_当期"
MONTH_IDS = [u"a%d" % (16 + k) for k in range(1, 13)]
A_IDS = [u"a%02d" % k for k in range(1, 31)]
CALC_IDS = [u"a31", u"a32", u"a33"]
RELATIONS = [(u"R1", MONTH_IDS, [u"a01"]), (u"R2", [u"a11"], [u"a14", u"a15"]), (u"R3", [u"a29"], [u"a12", u"a13"])]
FORBIDDEN_NAMES = (u"正解", u"作り方")       # 席の folder の中に在ってはいけない名(--hand が確かめる)
HAND_OUTPUTS = (u"資料.md", u"値の表.json", u"作業の記録.md", u"道具")
BRIEF_NAME = u"頼み.md"
UNREADABLE = object()
#: 絶対 path の根は path の先頭でだけ読む(直前が path の字・``/``・``.``・``-`` なら相対 path の途中なので根としない。``file://`` の直後の根は根)
FOLDER_ROOTS = r"(?:(?<![\w.\-/])|(?<=file://))/(?:private|Users|tmp|var|etc|home|opt|usr|Library|Applications|Volumes)[^\s\"'\\)]*"
#: 前の期の成果の道具の path(の字)
PREV_TOOL_DIR = u"前の期の成果/道具"
_CMD_SEPS = u";&|\n"


def _split_commands(text):
    u"""引用符の外の ``;``・``&``・``|``・改行で命令に分ける(引用符の中の区切りでは分けない)。"""
    out, cur, q = [], [], None
    for ch in text:
        if q is not None:
            cur.append(ch)
            if ch == q:
                q = None
        elif ch in u"\"'":
            q = ch
            cur.append(ch)
        elif ch in _CMD_SEPS:
            out.append(u"".join(cur))
            cur = []
        else:
            cur.append(ch)
    out.append(u"".join(cur))
    return out
_PY_CMD = re.compile(r"^python[0-9.]*$")
_SH_CMD = re.compile(r"^(?:ba|z)?sh$")
_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_PY_VALUE_FLAGS = (u"-W", u"-X")
_SH_VALUE_FLAGS = (u"-o", u"-O")


def _unq(tok):
    return tok.strip(u"\"'()")


def _is_tool_cwd(target):
    t = _unq(target).rstrip(u"/")
    return t == PREV_TOOL_DIR or t.endswith(u"/" + PREV_TOOL_DIR)


def ran_prev_tool(raw):
    u"""Bash の入力の字 → 前の期の成果の道具を走らせた形が在るか(粗い数。走らせた席は下限)。

    命令の位置(行頭・``;``・``&``・``|``・改行の直後。``env``・``VAR=…`` と絶対 path の命令名を許す)に
    python* / sh / bash / zsh が在りその最初の引数(``-u`` などの旗・値を取る ``-W``・``-X`` を挟んでよい)が道具の path、
    道具の path そのものが命令、``source``・``.`` の引数が道具の path、または同じ Bash の中で ``cd`` の先が前の期の成果/道具の後に
    python* / sh / bash / zsh か ``./x`` を走らせた形。``python3 -c`` の中の runpy・exec・import、``-m pdb`` など module 経由は数えない。
    """
    text = re.sub(r"[0-9]?>&[0-9]?", u" ", raw.replace(u"\\\n", u" "))
    cwd_tool = False
    for seg in _split_commands(text):
        toks = [_unq(t) for t in seg.split()]
        toks = [t for t in toks if t != u""]
        k = 0
        if k < len(toks) and toks[k].rsplit(u"/", 1)[-1] == u"env":
            k += 1
        while k < len(toks) and _ASSIGN.match(toks[k]):
            k += 1
        if k >= len(toks):
            continue
        cmd = toks[k]
        base = cmd.rsplit(u"/", 1)[-1]
        rest = toks[k + 1:]
        if cmd == u"cd":
            cwd_tool = bool(rest) and _is_tool_cwd(rest[0])
            continue
        if cmd in (u"source", u".") and rest and PREV_TOOL_DIR in rest[0]:
            return True
        if _PY_CMD.match(base) or _SH_CMD.match(base):
            flags = _PY_VALUE_FLAGS if _PY_CMD.match(base) else _SH_VALUE_FLAGS
            j = 0
            script = None
            while j < len(rest):
                t = rest[j]
                if t in (u"-c", u"-m"):
                    break
                if t in flags:
                    j += 2
                    continue
                if t.startswith(u"-"):
                    j += 1
                    continue
                script = t
                break
            if script is not None and (PREV_TOOL_DIR in script or cwd_tool):
                return True
            continue
        if PREV_TOOL_DIR in cmd or (cwd_tool and cmd.startswith(u"./")):
            return True
    return False


WRITE_TOOLS = (u"Write", u"Edit", u"MultiEdit", u"NotebookEdit")


def nfc(s):
    try:
        return unicodedata.normalize("NFC", s)
    except Exception:
        return s


# ============================================================ 小さな部品(どんな入力でも落ちない)
def read_json(path):
    u"""→ (obj, 誤り)。落ちない。"""
    try:
        with io.open(path, encoding="utf-8") as fh:
            return json.load(fh), None
    except (OSError, ValueError, UnicodeError, RecursionError, MemoryError) as exc:
        return None, type(exc).__name__


def read_text(path):
    try:
        with io.open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read(), None
    except (OSError, MemoryError) as exc:
        return None, type(exc).__name__


def sha256_file(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
    except OSError:
        return None
    return h.hexdigest()


def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def int_text(v):
    u"""席の ``数値`` → 整数 か None(形が読めない)。"""
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if not isinstance(v, str):
        return None
    t = nfc(v).strip()
    if not re.match(r"^[+-]?[0-9]+\Z", t) or len(t) > 4000:
        return None
    try:
        return int(t)
    except ValueError:
        return None


def dec_text(v):
    u"""席の計算の行の ``数値`` → Fraction か None。"""
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return Fraction(v)
    if not isinstance(v, str):
        return None
    t = nfc(v).strip()
    if not re.match(r"^[+-]?[0-9]+(?:\.[0-9]+)?\Z", t):
        return None
    try:
        return Fraction(t)
    except (ValueError, ZeroDivisionError):
        return None


def round_half_away(x, places):
    u"""10 進の四捨五入(0.5 は 0 から遠い側)。Fraction → Fraction。"""
    scale = 10 ** places
    y = x * scale
    n = (2 * abs(y).numerator + abs(y).denominator) // (2 * abs(y).denominator)
    return Fraction(n if y >= 0 else -n, scale)


def write_json(path, obj):
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False, indent=1) + u"\n")


# ============================================================ 正解・定義表
def read_gold(path):
    u"""正解の file → {1: {id: 値か None か UNREADABLE}, 2: ...}。読めなければ None。便 UM2 の集計 script の読み方を写した(id と鍵の対応は GOLD_KEYS)。"""
    obj, err = read_json(path)
    if err or not isinstance(obj, dict):
        return None
    out = {}
    for p in PERIODS:
        body = obj.get(u"期%d" % p)
        vals = dict((i, UNREADABLE) for i in A_IDS)
        if isinstance(body, dict):
            for ident, key in GOLD_KEYS:
                if key in body:
                    v = body[key]
                    if v is None:
                        vals[ident] = None
                    elif is_int(v):
                        vals[ident] = v
            if MONTH_KEY in body:
                months = body[MONTH_KEY]
                if isinstance(months, list):
                    for k in range(min(12, len(months))):
                        v = months[k]
                        if v is None:
                            vals[MONTH_IDS[k]] = None
                        elif is_int(v):
                            vals[MONTH_IDS[k]] = v
                elif months is None:
                    for ident in MONTH_IDS:
                        vals[ident] = None
        out[p] = vals
    return out


def load_calc_defs(path):
    u"""定義表 → [(id, 式, 入力, 桁)]。読めなければ None。"""
    obj, err = read_json(path)
    if err or not isinstance(obj, dict) or not isinstance(obj.get(u"行"), list):
        return None
    out = []
    for r in obj[u"行"]:
        if isinstance(r, dict) and r.get(u"取り方") == u"計算" and isinstance(r.get(u"id"), str):
            ins = r.get(u"入力")
            places = r.get(u"桁", 0)
            if isinstance(ins, list) and all(isinstance(x, str) for x in ins) and is_int(places) and 0 <= places <= 12:
                out.append((r[u"id"], r.get(u"式"), ins, places))
    return out


def expected_calc(defs, gold):
    u"""正解の値から計算の行の値を出す。→ {id: (Fraction か None(分母から外す), 桁)}。"""
    memo = {}
    table = dict((d[0], d) for d in defs)

    def val(i):
        if i in memo:
            return memo[i]
        memo[i] = None
        if i in table:
            _i, f, ins, places = table[i]
            xs = [val(x) for x in ins]
            if any(x is None for x in xs):
                res = None
            elif f == u"和":
                res = round_half_away(sum(xs, Fraction(0)), places)
            elif f == u"比" and len(xs) == 2 and xs[1] != 0:
                res = round_half_away(xs[0] / xs[1], places)
            elif f == u"比の分母和" and len(xs) == 3 and xs[1] + xs[2] > 0:
                res = round_half_away(xs[0] / (xs[1] + xs[2]), places)
            else:
                res = None
        else:
            g = gold.get(i)
            res = Fraction(g) if is_int(g) else None
        memo[i] = res
        return res
    return dict((d[0], (val(d[0]), d[3])) for d in defs)


# ============================================================ 値の表の読み・行ごとの結果
def read_table(path):
    u"""→ (状態, {id: 行}, 重複の数)。状態は ``無し``(file が無い)・``読めない``・``読めた``。"""
    if not os.path.exists(path):
        return u"無し", {}, 0
    obj, err = read_json(path)
    if err or not isinstance(obj, dict) or not isinstance(obj.get(u"行"), list):
        return u"読めない", {}, 0
    rows = {}
    dup = 0
    for r in obj[u"行"]:
        if isinstance(r, dict) and isinstance(r.get(u"id"), str):
            if r[u"id"] in rows:
                dup += 1
            else:
                rows[r[u"id"]] = r
    return u"読めた", rows, dup


def classify(gold_v, tstate, row):
    u"""1 行の結果の名(封 §1-4)。正解が読めない行は None。"""
    if gold_v is UNREADABLE:
        return None
    if tstate == u"無し":
        return u"答えなし"
    if tstate == u"読めない":
        return u"形が読めない"
    if row is None:
        return u"答えなし"
    st = row.get(u"状態")
    if st not in STATES:
        return u"形が読めない"
    if st == u"分からない":
        return u"分からない"
    if st == u"在る":
        n = int_text(row.get(u"数値"))
        if n is None:
            return u"形が読めない"
        if gold_v is None:
            return u"無いのに在る"
        return u"同じ" if n == gold_v else u"違う"
    return u"無いで同じ" if gold_v is None else u"無いで違う"


def conf_name(row):
    if row is None:
        return u"なし"
    c = row.get(u"自信")
    return c if c in (u"高", u"中", u"低") else u"読めない"


def present_value(name, row):
    u"""``在る`` と書いた行(結果が 同じ・違う・無いのに在る)の整数。"""
    if name in (u"同じ", u"違う", u"無いのに在る"):
        return int_text(row.get(u"数値"))
    return None


def calc_result(exp, places, tstate, row):
    u"""計算の行 → 結果の名 か ``分母から外した``。"""
    if exp is None:
        return u"分母から外した"
    if tstate == u"読めない":
        return u"形が読めない"
    if tstate == u"無し" or row is None:
        return u"答えなし"
    st = row.get(u"状態")
    if st == u"分からない":
        return u"分からない"
    if st == u"無い":
        return u"無い"
    if st != u"在る":
        return u"形が読めない"
    v = dec_text(row.get(u"数値"))
    if v is None:
        return u"形が読めない"
    return u"同じ" if round_half_away(v, places) == exp else u"違う"


def relation_counts(table_rows, tstate):
    u"""→ (見られる, 成り立つ, 見られない, {R: (見られる, 成り立つ)})。"""
    seen = hold = unseen = 0
    per = {}
    for name, left, right in RELATIONS:
        vals = []
        ok = tstate == u"読めた"
        for i in left + right:
            row = table_rows.get(i)
            n = int_text(row.get(u"数値")) if isinstance(row, dict) and row.get(u"状態") == u"在る" else None
            if n is None:
                ok = False
                break
            vals.append(n)
        if not ok:
            unseen += 1
            per[name] = (0, 0)
            continue
        seen += 1
        h = sum(vals[:len(left)]) == sum(vals[len(left):])
        hold += 1 if h else 0
        per[name] = (1, 1 if h else 0)
    return seen, hold, unseen, per


# ============================================================ 資料の数の字
_DATE = re.compile(r"[0-9]{4}[-/][0-9]{1,2}[-/][0-9]{1,2}")
_NUM = re.compile(r"(?<![0-9.])([0-9]+(?:\.[0-9]+)?)")


def doc_numbers(text):
    u"""資料の字 → 数の字(文字列)の並び。年・月・日の形・日付を外し、桁区切りを取り、数字が 2 つ以上並ぶ数だけ。"""
    try:
        t = unicodedata.normalize("NFKC", text)
    except Exception:
        t = text
    t = _DATE.sub(u" ", t)
    t = re.sub(r"(?<=[0-9]),(?=[0-9]{3}(?![0-9]))", u"", t)
    out = []
    for m in _NUM.finditer(t):
        s = m.group(1)
        after = t[m.end():m.end() + 1]
        if re.match(r"^(?:19|20)[0-9]{2}\Z", s) and after == u"年":
            continue
        if re.match(r"^[0-9]{1,2}\Z", s) and 1 <= int(s) <= 31 and after in (u"月", u"日"):
            continue
        if len(s.replace(u".", u"")) < 2:
            continue
        out.append(s)
    return out


def unmatched_numbers(text, values):
    u"""資料の数の字のうち、値の表の数値(円・千・百万・百分率)のどれにも当たらない数。→ (数の字の数, 当たらない数)。"""
    nums = doc_numbers(text)
    cache = {}
    bad = 0
    for s in nums:
        if len(s) > 40:
            bad += 1
            continue
        d = len(s.split(u".")[1]) if u"." in s else 0
        if d not in cache:
            c = set()
            for v in values:
                for x in (v, v / 1000, v / 1000000, v * 100):
                    c.add(abs(round_half_away(x, d)))
            cache[d] = c
        if Fraction(s) not in cache[d]:
            bad += 1
    return len(nums), bad


# ============================================================ --hand
def hand(opt):
    u"""席の folder を作る(写すだけ)。→ (rc, 報告)。出す先が既に在れば何もしない。"""
    need = ("--co", "--seat", "--definition", "--brief", "--root", "--company", "--round", "--period")
    if any(k not in opt for k in need):
        return 2, od([(u"誤り", u"命令の形")])
    try:
        i = int(opt["--company"])
        p = int(opt["--period"])
    except ValueError:
        return 2, od([(u"誤り", u"社か期が整数でない")])
    r = opt["--round"]
    if r not in ROUNDS or p not in PERIODS:
        return 2, od([(u"誤り", u"回か期の値")])
    base = os.path.join(opt["--root"], str(i), r)
    dest = os.path.join(base, u"期%d" % p)
    if os.path.exists(dest):
        return 3, od([(u"誤り", u"出す先が既に在る(何もしない)")])
    src_mat = os.path.join(opt["--co"], str(i), u"期%d" % p)
    spec = os.path.join(opt["--seat"], str(i), u"指定_期%d_A.json" % p)
    srcs = [src_mat, spec, opt["--definition"], opt["--brief"]]
    prev_src = prev_mat = None
    if p == 2:
        prev_mat = os.path.join(opt["--co"], str(i), u"期1")
        srcs.append(prev_mat)
        prev_src = os.path.join(base, u"期1")
        srcs.append(prev_src)
    missing = [x for x in srcs if not os.path.exists(x)]
    if missing:
        return 4, od([(u"誤り", u"写す元が無い"), (u"無い数", len(missing))])
    for root_dir in (src_mat, prev_mat):
        if root_dir and has_forbidden(root_dir):
            return 5, od([(u"誤り", u"素材の元に正解・作り方の名が在る(何も作らない)")])
    os.makedirs(dest)
    shutil.copytree(src_mat, os.path.join(dest, u"素材"))
    shutil.copyfile(spec, os.path.join(dest, u"指定.json"))
    shutil.copyfile(opt["--definition"], os.path.join(dest, u"definition_A.json"))
    shutil.copyfile(opt["--brief"], os.path.join(dest, BRIEF_NAME))
    absent = 0
    copied = 0
    if p == 2:
        shutil.copytree(prev_mat, os.path.join(dest, u"前の期の素材"))
        out_dir = os.path.join(dest, u"前の期の成果")
        os.makedirs(out_dir)
        for name in HAND_OUTPUTS:
            s = os.path.join(prev_src, name)
            if os.path.isdir(s):
                shutil.copytree(s, os.path.join(out_dir, name))
                copied += 1
            elif os.path.isfile(s):
                shutil.copyfile(s, os.path.join(out_dir, name))
                copied += 1
            else:
                absent += 1
    problems = hand_problems(dest, opt["--brief"])
    rep = od([(u"出した先の folder の数", 1), (u"前の期の成果を写した数", copied), (u"前の期の成果が無かった数", absent), (u"禁止の名の問題", len(problems))])
    return (6 if problems else 0), rep


def has_forbidden(folder):
    for _d, dirs, files in os.walk(folder):
        for n in dirs + files:
            if nfc(n) in FORBIDDEN_NAMES or nfc(n) == BRIEF_NAME:
                return True
    return False


def hand_problems(dest, brief_path):
    u"""出す先に 正解・作り方・便 UM2 の 頼み.md が 1 つも無いことを自分で確かめる。"""
    out = []
    try:
        with open(brief_path, "rb") as fh:
            brief = fh.read()
    except OSError:
        return [u"頼みの紙が読めない"]
    for d, dirs, files in os.walk(dest):
        for n in dirs + files:
            nn = nfc(n)
            if nn in FORBIDDEN_NAMES:
                out.append(u"禁止の名: " + nn)
            if nn == BRIEF_NAME:
                full = os.path.join(d, n)
                try:
                    with open(full, "rb") as fh:
                        ok = fh.read() == brief and os.path.abspath(d) == os.path.abspath(dest)
                except OSError:
                    ok = False
                if not ok:
                    out.append(u"頼みの紙でない頼み.md")
    return out


# ============================================================ --process
def blocks_of(obj):
    msg = obj.get(u"message") if isinstance(obj, dict) else None
    c = msg.get(u"content") if isinstance(msg, dict) else None
    if isinstance(c, str):
        return [{u"type": u"text", u"text": c}]
    return [b for b in c if isinstance(b, dict)] if isinstance(c, list) else []


def input_text(inp):
    u"""tool_use の入力 → 文字列の値を連ねた字(NFC)。"""
    parts = []

    def walk(x, depth):
        if depth > 20:
            return
        if isinstance(x, str):
            parts.append(x)
        elif isinstance(x, dict):
            for v in x.values():
                walk(v, depth + 1)
        elif isinstance(x, list):
            for v in x:
                walk(v, depth + 1)
    walk(inp, 0)
    return nfc(u"\n".join(parts))


def read_lines(path):
    u"""会話の記録の行 → obj(読めない行は飛ばす)。巨大な行・読めない file でも落ちない。"""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    o = json.loads(line)
                except (ValueError, RecursionError, MemoryError):
                    continue
                if isinstance(o, dict):
                    yield o
    except OSError:
        return


def first_user_text(path):
    for o in read_lines(path):
        if o.get(u"type") == u"user" and not o.get(u"isMeta"):
            t = u"\n".join(b.get(u"text", u"") for b in blocks_of(o) if b.get(u"type") == u"text" and isinstance(b.get(u"text"), str))
            return nfc(t)
    return None


def list_transcripts(tdir):
    try:
        names = sorted(n for n in os.listdir(tdir) if n.endswith(".output") or n.endswith(".jsonl"))
    except (OSError, TypeError):
        return []
    return [os.path.join(tdir, n) for n in names]


class Transcripts(object):
    def __init__(self, tdir):
        self.first = od()
        for p in list_transcripts(tdir):
            self.first[p] = first_user_text(p)

    def match(self, folder):
        u"""席の folder の path が最初の user の文に在る記録。"""
        f = nfc(os.path.abspath(folder))
        variants = set([f])
        if f.startswith(u"/private/"):
            variants.add(f[len(u"/private"):])
        else:
            variants.add(u"/private" + f)
        pat = re.compile(u"(?:" + u"|".join(re.escape(v) for v in sorted(variants)) + u")(?![A-Za-z0-9_\\-.])")
        return [p for p, t in self.first.items() if t and pat.search(t)]


def material_files(folder):
    u"""素材の file(``素材/`` 無ければ ``期1/``)→ [(名, 大きさ)]。名は NFC の basename の重複を除いた並び。"""
    for sub in (u"素材", u"期1"):
        d = os.path.join(folder, sub)
        if os.path.isdir(d):
            out = []
            for dd, _ds, fs in os.walk(d):
                for n in fs:
                    try:
                        out.append((nfc(n), os.path.getsize(os.path.join(dd, n))))
                    except OSError:
                        pass
            return sorted(out)
    return []


def folder_variants(folder):
    f = nfc(os.path.abspath(folder))
    vs = [f]
    vs.append(f[len(u"/private"):] if f.startswith(u"/private/") else u"/private" + f)
    return tuple(vs)


def is_dirty(raw, variants):
    u"""入力の字 → 席の folder の外の path か相対の path が在るか。"""
    if re.search(r"\.\./|~/|\$HOME", raw):
        return True
    for p in re.findall(FOLDER_ROOTS, raw):
        if p.startswith(u"/usr/bin/") or p.startswith(u"/usr/local/bin/"):
            continue
        if not any(p == v or p.startswith(v + u"/") or (p.startswith(v) and not re.match(r"[A-Za-z0-9_\-.]", p[len(v):len(v) + 1])) for v in variants):
            return True
    return False


_PY = re.compile(r"\bpython[0-9.]*\b")
_PY_BODY = re.compile(r"<<|\bpython[0-9.]*\s+-c\b|\bpython[0-9.]*\s+-\s")
_WRITE = [
    re.compile(r">>?\s*['\"]?[^\s'\"|&;]*{N}"),
    re.compile(r"json\.dump\("), re.compile(r"write_text\(|write_bytes\(|\.write\("),
    re.compile(r"open\([^\n]{0,300}?,\s*['\"][wax][bt+]*['\"]"), re.compile(r"\btee\b"),
    re.compile(r"\b(?:cp|mv)\b[^|;&\n]*{N}"),
]


def writes_name(raw, name):
    if name not in raw:
        return False
    for pat in _WRITE:
        src = pat.pattern
        if u"{N}" in src:
            if re.search(src.replace(u"{N}", re.escape(name)), raw):
                return True
        elif pat.search(raw):
            return True
    return False


def count_seat(path, folder):
    u"""会話の記録 1 本 → 過程の数(封 §1-5)。tool_use が 1 つも無ければ None。"""
    variants = folder_variants(folder)
    files = material_files(folder)
    names = [n for n, _s in files]
    journal = max(files, key=lambda x: (x[1], x[0]))[0] if files else None
    has_prev = os.path.isdir(os.path.join(folder, u"前の期の素材")) or os.path.isdir(os.path.join(folder, u"前の期の成果"))
    seen_use = set()
    seen_res = set()
    calls = []                     # (name, raw, input, ts)
    texts = 0
    errors = 0
    first_ts = last_ts = None
    for o in read_lines(path):
        ts = o.get(u"timestamp")
        for b in blocks_of(o):
            t = b.get(u"type")
            if t == u"tool_use":
                k = b.get(u"id")
                if isinstance(k, str):
                    if k in seen_use:
                        continue
                    seen_use.add(k)
                inp = b.get(u"input")
                calls.append((b.get(u"name") if isinstance(b.get(u"name"), str) else u"", input_text(inp), inp, ts))
                first_ts = first_ts or ts
                last_ts = ts
            elif t == u"tool_result":
                k = b.get(u"tool_use_id")
                if isinstance(k, str):
                    if k in seen_res:
                        continue
                    seen_res.add(k)
                if b.get(u"is_error") is True:
                    errors += 1
                if calls:
                    last_ts = ts
            elif t == u"text" and o.get(u"type") == u"assistant" and isinstance(b.get(u"text"), str) and b[u"text"].strip():
                texts += 1
    if not calls:
        return None
    n = od()
    by_name = collections.Counter(c[0] for c in calls)
    n[u"道具の呼び出し"] = len(calls)
    n[u"道具の名ごと"] = dict(sorted(by_name.items()))
    n[u"席の発言の回"] = texts
    sec = None
    try:
        a = datetime.datetime.fromisoformat(first_ts.replace(u"Z", u"+00:00"))
        z = datetime.datetime.fromisoformat(last_ts.replace(u"Z", u"+00:00"))
        sec = int((z - a).total_seconds())
    except (AttributeError, ValueError, TypeError):
        sec = None
    n[u"秒"] = sec
    n[u"素材の file の数"] = len(names)
    per_file = dict((m, 0) for m in names)
    for _nm, raw, _inp, _ts in calls:
        for m in names:
            if m in raw:
                if has_prev and u"前の期の素材" in raw and (u"素材/" + m) not in raw.replace(u"前の期の素材/" + m, u""):
                    continue
                per_file[m] += 1
    n[u"素材の file のうち path が出た数"] = sum(1 for v in per_file.values() if v >= 1)
    n[u"素材の file のうち 2 回以上の数"] = sum(1 for v in per_file.values() if v >= 2)
    n[u"最大の file に触れた"] = 1 if journal is not None and per_file.get(journal, 0) >= 1 else 0
    script_writes = {}
    table_w = doc_w = 0
    first_table = None
    scripts = pyruns = 0
    prev_asset = prev_tool_run = prev_mat_calls = dirty = 0
    for k, (nm, raw, inp, _ts) in enumerate(calls, 1):
        pth = None
        if isinstance(inp, dict):
            for key in (u"file_path", u"notebook_path", u"path"):
                if isinstance(inp.get(key), str):
                    pth = nfc(inp[key])
                    break
        is_write_tool = nm in WRITE_TOOLS and pth is not None
        is_py_write = is_write_tool and pth.endswith(u".py")
        is_py_run = nm == u"Bash" and bool(_PY.search(raw))
        if is_py_write:
            scripts += 1
            for target in (u"値の表.json", u"資料.md"):
                if writes_name(raw, target):
                    script_writes.setdefault(os.path.basename(pth), set()).add(target)
        elif is_py_run and _PY_BODY.search(raw):
            scripts += 1
        if is_py_run:
            pyruns += 1
        for target, which in ((u"値の表.json", u"t"), (u"資料.md", u"d")):
            hit = False
            if is_write_tool and os.path.basename(pth) == target:
                hit = True
            elif not is_write_tool and writes_name(raw, target):
                hit = True
            elif is_py_run and any(target in ts_ and sb in raw for sb, ts_ in script_writes.items()):
                hit = True
            if hit:
                if which == u"t":
                    table_w += 1
                    if first_table is None:
                        first_table = k
                else:
                    doc_w += 1
        if u"前の期の成果" in raw:
            prev_asset += 1
        if u"前の期の成果/道具" in raw and nm == u"Bash" and ran_prev_tool(raw):
            prev_tool_run = 1
        if u"前の期の素材" in raw:
            prev_mat_calls += 1
        if is_dirty(raw, variants):
            dirty += 1
    n[u"最初に値の表を書くまでの呼び出し"] = first_table
    n[u"値の表を書いた回数"] = table_w
    n[u"書き直した"] = 1 if table_w >= 2 else 0
    n[u"資料を書いた回数"] = doc_w
    n[u"script を書いた数"] = scripts
    n[u"python を走らせた数"] = pyruns
    n[u"道具が誤りを返した数"] = errors
    n[u"前の期の成果の path が出た呼び出し"] = prev_asset
    n[u"前の期の成果の道具を走らせた"] = prev_tool_run
    n[u"前の期の素材の path が出た呼び出し"] = prev_mat_calls
    n[u"汚れた呼び出し"] = dirty
    n[u"汚れの席"] = 1 if dirty >= 1 else 0
    return n


def process_seat(index, folder):
    u"""席の folder → 過程の数か ``過程が数えられない``(理由つき)。"""
    if index is None:
        return od([(u"状態", u"過程が数えられない"), (u"理由", u"記録の folder が無い")])
    m = index.match(folder)
    if len(m) == 0:
        return od([(u"状態", u"過程が数えられない"), (u"理由", u"記録が 0 本")])
    if len(m) >= 2:
        return od([(u"状態", u"過程が数えられない"), (u"理由", u"記録が 2 本以上"), (u"本数", len(m))])
    got = count_seat(m[0], folder)
    if got is None:
        return od([(u"状態", u"過程が数えられない"), (u"理由", u"tool_use が無い")])
    out = od([(u"状態", u"数えた")])
    out.update(got)
    return out


def seat_folders(root, companies, rounds):
    return [(i, r, p, os.path.join(root, str(i), r, u"期%d" % p)) for i in companies for r in rounds for p in PERIODS]


def median2(xs):
    u"""中央値の 2 倍(整数)。"""
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return None
    return 2 * s[n // 2] if n % 2 else s[n // 2 - 1] + s[n // 2]


# ============================================================ --tally
BOUNDS = od([
    (u"UM3-A1", {u"同じ+無いで同じ": 216, u"行の数": 240}),
    (u"UM3-A2", {u"在るの百分率": 90, u"同じの百分率": 85}),
    (u"UM3-A3", {u"違う+無いのに在る": 1, u"行の数": 480}),
    (u"UM3-A4", {u"同じ+無いで同じ": 216, u"行の数": 240}),
    (u"UM3-A5", {u"同じの百分率": 80}),
    (u"UM3-A6", {u"無いのに在る": 1}),
    (u"UM3-A7", {u"数値が違う行が在る社": 2, u"会社の数": 4}),
    (u"UM3-A8", {u"高の割合の分子": 1, u"高の割合の分母": 2}),
    (u"UM3-A9", {u"成り立つ百分率": 95}),
    (u"UM3-L1", {u"席": 6, u"席の数": 8}),
    (u"UM3-L2", {u"席": 6, u"席の数": 8}),
    (u"UM3-L3", {u"席": 3, u"席の数": 8}),
    (u"UM3-L4", {u"中央値の 2 倍の差": 1}),
    (u"UM3-L5", {u"席": 4, u"席の数": 16}),
    (u"UM3-L6", {u"席": 0, u"席の数": 16}),
    (u"UM3-D1", {u"資料": 8, u"席の数": 16}),
])


def B(pid, key):
    return BOUNDS[pid][key]


def _new_counters():
    return collections.Counter()


def tally_company_round(c, pc, co, seat, root, i, r, gold, calc_defs, results, tables, tindex, per_seat, with_dirty=None):
    u"""会社 i・回 r の 2 期を数える。``results[(i, r, p)] = {id: (名, 整数か None, 自信)}``。"""
    for p in PERIODS:
        folder = os.path.join(root, str(i), r, u"期%d" % p)
        tstate, rows, dup = read_table(os.path.join(folder, u"値の表.json"))
        tables[(i, r, p)] = (tstate, rows)
        c[u"値の表:%s" % tstate] += 1
        c[u"値の表:重複の行"] += dup
        res = {}
        for ident in A_IDS:
            g = gold[p][ident]
            row = rows.get(ident)
            name = classify(g, tstate, row)
            if name is None:
                c[u"正解が読めない行"] += 1
                continue
            n = present_value(name, row) if isinstance(row, dict) else None
            res[ident] = (name, n, conf_name(row))
            for tgt in (c, pc):
                tgt[u"期%d:行の数" % p] += 1
                tgt[u"期%d:結果:%s" % (p, name)] += 1
            c[u"自信:%s×%s" % (conf_name(row), name)] += 1
            pc[u"自信:%s×%s" % (conf_name(row), name)] += 1
        results[(i, r, p)] = res
        # 計算の 3 行
        if calc_defs is not None:
            exp = expected_calc(calc_defs, gold[p])
            for ident in CALC_IDS:
                if ident not in exp:
                    continue
                name = calc_result(exp[ident][0], exp[ident][1], tstate, rows.get(ident))
                c[u"期%d:計算:%s" % (p, name)] += 1
        # 関係
        seen, hold, unseen, per = relation_counts(rows, tstate)
        c[u"関係:見られる本数"] += seen
        c[u"関係:成り立つ本数"] += hold
        c[u"関係:見られない本数"] += unseen
        for k, (s_, h_) in per.items():
            c[u"関係:%s:見られる本数" % k] += s_
            c[u"関係:%s:成り立つ本数" % k] += h_
        # 資料
        text, err = read_text(os.path.join(folder, u"資料.md"))
        if err is not None:
            c[u"資料:なし"] += 1
            c[u"期%d:資料:なし" % p] += 1
        else:
            values = []
            for ident, row in rows.items():
                if isinstance(row, dict) and row.get(u"状態") == u"在る":
                    n = int_text(row.get(u"数値"))
                    if n is not None and abs(n) < 10 ** 40:
                        values.append(Fraction(n))
            for ident in CALC_IDS:
                row = rows.get(ident)
                if isinstance(row, dict) and row.get(u"状態") == u"在る":
                    v = dec_text(row.get(u"数値"))
                    if v is not None and abs(v) < 10 ** 40:
                        values.append(v)
            total, bad = unmatched_numbers(text, values)
            c[u"資料:本数"] += 1
            c[u"資料:字の数"] += len(text)
            c[u"資料:数の字の数"] += total
            c[u"資料:当たらない数の字の数"] += bad
            c[u"資料:当たらない数の字が 1 つ以上の資料"] += 1 if bad >= 1 else 0
            if tstate != u"読めた":
                c[u"資料:値の表が読めない資料"] += 1
        # 過程
        proc = process_seat(tindex, folder)
        per_seat[(i, r, p)] = proc


def cross_b(c, seat, i, results_by_round, rounds):
    u"""B との行ごとの掛け合わせ(1 期目は判定_期1_A・2 期目は置き場_期2_A)。"""
    j1, e1 = read_json(os.path.join(seat, str(i), u"出力", u"判定_期1_A.json"))
    b1 = {}
    if not e1 and isinstance(j1, dict) and isinstance(j1.get(u"材料"), list):
        for m in j1[u"材料"]:
            if isinstance(m, dict) and isinstance(m.get(u"id"), str):
                rules = m.get(u"規則")
                b1[m[u"id"]] = (m.get(u"判定"), u"+".join(x for x in rules if isinstance(x, str)) if isinstance(rules, list) else u"")
    j2, e2 = read_json(os.path.join(seat, str(i), u"出力", u"置き場_期2_A.json"))
    b2 = {}
    if not e2 and isinstance(j2, dict) and isinstance(j2.get(u"行"), dict):
        for k, v in j2[u"行"].items():
            if isinstance(v, dict) and isinstance(v.get(u"状態"), str):
                b2[k] = v[u"状態"]
    for r in rounds:
        for ident, (name, _n, _cf) in results_by_round.get((i, r, 1), {}).items():
            b = b1.get(ident)
            label = b[0] if b and isinstance(b[0], str) else u"B なし"
            c[u"掛け合わせ1:%s×%s" % (label, name)] += 1
            if label == u"止める":
                c[u"掛け合わせ1:止める:%s×%s" % (b[1], name)] += 1
        for ident, (name, _n, _cf) in results_by_round.get((i, r, 2), {}).items():
            st = b2.get(ident, u"B なし")
            c[u"掛け合わせ2:%s×%s" % (st, name)] += 1


def fluctuation(c, i, results, rounds):
    if len(rounds) < 2:
        return
    for p in PERIODS:
        ra, rb = results.get((i, rounds[0], p), {}), results.get((i, rounds[1], p), {})
        diff = 0
        for ident in A_IDS:
            if ident not in ra or ident not in rb:
                continue
            c[u"揺れ:期%d:行の数" % p] += 1
            na, nb = ra[ident], rb[ident]
            if na[0] == nb[0]:
                c[u"揺れ:期%d:結果の名が同じ" % p] += 1
            if na[1] is not None and nb[1] is not None:
                c[u"揺れ:期%d:在るどうし" % p] += 1
                if na[1] == nb[1]:
                    c[u"揺れ:期%d:在るどうしで数値が同じ" % p] += 1
                else:
                    c[u"揺れ:期%d:在るどうしで数値が違う" % p] += 1
                    diff += 1
        if diff >= 1:
            c[u"揺れ:期%d:数値が違う行が在る社" % p] += 1


def process_totals(c, per_seat, seat_results, b_seats):
    for key, proc in per_seat.items():
        i, r, p = key
        c[u"過程:期%d:席の数" % p] += 1
        if proc[u"状態"] != u"数えた":
            c[u"過程:期%d:数えられない席" % p] += 1
            c[u"過程:数えられない席"] += 1
            continue
        c[u"過程:数えた席"] += 1
        c[u"過程:期%d:最大の file に触れた席" % p] += proc[u"最大の file に触れた"]
        c[u"過程:期%d:script を書いた席" % p] += 1 if proc[u"script を書いた数"] >= 1 else 0
        c[u"過程:期%d:前の期の成果の道具を走らせた席" % p] += proc[u"前の期の成果の道具を走らせた"]
        c[u"過程:期%d:道具の呼び出しの数" % p] += proc[u"道具の呼び出し"]
        c[u"過程:値の表を 2 回以上書いた席"] += proc[u"書き直した"]
        c[u"過程:汚れの席"] += proc[u"汚れの席"]
        c[u"過程:汚れた呼び出し"] += proc[u"汚れた呼び出し"]
        c[u"過程:道具が誤りを返した数"] += proc[u"道具が誤りを返した数"]
        c[u"過程:python を走らせた数"] += proc[u"python を走らせた数"]
        c[u"過程:script を書いた数"] += proc[u"script を書いた数"]
        c[u"過程:前の期の成果の path が出た呼び出し"] += proc[u"前の期の成果の path が出た呼び出し"]
        c[u"過程:前の期の素材の path が出た呼び出し"] += proc[u"前の期の素材の path が出た呼び出し"]
        for nm, k in proc[u"道具の名ごと"].items():
            c[u"過程:道具:%s" % nm] += k
        if proc[u"秒"] is None:
            c[u"過程:秒が無い席"] += 1
        else:
            c[u"過程:秒の合計"] += proc[u"秒"]
    for p in PERIODS:
        xs = [per_seat[k][u"道具の呼び出し"] for k in per_seat if k[2] == p and per_seat[k][u"状態"] == u"数えた"]
        m = median2(xs)
        if m is not None:
            c[u"過程:期%d:道具の呼び出しの中央値の 2 倍" % p] = m
    # 汚れの席を外した結果の数(外さない数と並べる)
    clean = collections.Counter()
    for (i, r, p), proc in per_seat.items():
        if proc.get(u"汚れの席") == 1:
            continue
        for ident, (name, _n, _cf) in seat_results.get((i, r, p), {}).items():
            clean[u"汚れの席を外した:期%d:行の数" % p] += 1
            clean[u"汚れの席を外した:期%d:結果:%s" % (p, name)] += 1
    c.update(clean)
    # B の 1 期目の席
    for i, proc in b_seats.items():
        c[u"B の席:席の数"] += 1
        if proc[u"状態"] != u"数えた":
            c[u"B の席:数えられない席"] += 1
            if proc.get(u"理由") == u"記録が 0 本":
                c[u"B の席:記録が無い席"] += 1
            continue
        c[u"B の席:数えた席"] += 1
        c[u"B の席:最大の file に触れた席"] += proc[u"最大の file に触れた"]
        c[u"B の席:script を書いた席"] += 1 if proc[u"script を書いた数"] >= 1 else 0
        c[u"B の席:道具の呼び出しの数"] += proc[u"道具の呼び出し"]
        c[u"B の席:汚れの席"] += proc[u"汚れの席"]
        c[u"B の席:python を走らせた数"] += proc[u"python を走らせた数"]
        c[u"B の席:道具が誤りを返した数"] += proc[u"道具が誤りを返した数"]
        if proc[u"秒"] is None:
            c[u"B の席:秒が無い席"] += 1
        else:
            c[u"B の席:秒の合計"] += proc[u"秒"]


FIXED_COUNTS = tuple(
    [u"期%d:行の数" % p for p in PERIODS]
    + [u"期%d:結果:%s" % (p, n) for p in PERIODS for n in RESULT_NAMES]
    + [u"期%d:計算:%s" % (p, n) for p in PERIODS for n in (u"同じ", u"違う", u"無い", u"分からない", u"答えなし", u"形が読めない", u"分母から外した")]
    + [u"値の表:無し", u"値の表:読めない", u"値の表:読めた", u"値の表:重複の行", u"正解が読めない行", u"正解が読めない社", u"定義表が読めない",
       u"関係:見られる本数", u"関係:成り立つ本数", u"関係:見られない本数",
       u"資料:なし", u"資料:本数", u"資料:字の数", u"資料:数の字の数", u"資料:当たらない数の字の数", u"資料:当たらない数の字が 1 つ以上の資料", u"資料:値の表が読めない資料",
       u"過程:数えた席", u"過程:数えられない席", u"過程:値の表を 2 回以上書いた席", u"過程:汚れの席", u"過程:汚れた呼び出し", u"過程:道具が誤りを返した数",
       u"過程:python を走らせた数", u"過程:script を書いた数", u"過程:秒が無い席", u"過程:秒の合計",
       u"B の席:席の数", u"B の席:数えた席", u"B の席:数えられない席", u"B の席:記録が無い席", u"B の席:最大の file に触れた席", u"B の席:script を書いた席",
       u"B の席:道具の呼び出しの数", u"B の席:汚れの席", u"B の席:python を走らせた数", u"B の席:道具が誤りを返した数", u"B の席:秒が無い席", u"B の席:秒の合計",
       u"読んだ便 UM2 の出力の file の数"]
    + [u"過程:期%d:%s" % (p, k) for p in PERIODS for k in (u"席の数", u"数えられない席", u"最大の file に触れた席", u"script を書いた席", u"前の期の成果の道具を走らせた席", u"道具の呼び出しの数", u"資料:なし")]
    + [u"揺れ:期%d:%s" % (p, k) for p in PERIODS for k in (u"行の数", u"結果の名が同じ", u"在るどうし", u"在るどうしで数値が同じ", u"在るどうしで数値が違う", u"数値が違う行が在る社")]
    + [u"関係:%s:%s" % (k, w) for k in (u"R1", u"R2", u"R3") for w in (u"見られる本数", u"成り立つ本数")]
    + [u"自信:%s×%s" % (cf, n) for cf in CONF_NAMES for n in RESULT_NAMES]
    + [u"掛け合わせ1:%s×%s" % (b, n) for b in (u"通す", u"通す(取り方は未確認)", u"止める", u"無いを受ける", u"B なし") for n in RESULT_NAMES]
    + [u"掛け合わせ2:%s×%s" % (b, n) for b in (u"在る", u"確認待ち", u"保留", u"無い", u"B なし") for n in RESULT_NAMES]
    + [u"汚れの席を外した:期%d:行の数" % p for p in PERIODS]
    + [u"汚れの席を外した:期%d:結果:%s" % (p, n) for p in PERIODS for n in RESULT_NAMES]
)


def read_um2_digest(co, seat, companies):
    u"""読んだ便 UM2 の出力の sha256 の束ね(相対の名と sha256 の並びを sha256 したもの)と、読んだ file の数。"""
    entries = []
    for i in companies:
        for label, base, rel in ((u"co", co, os.path.join(str(i), u"正解", u"正解.json")), (u"seat", seat, os.path.join(str(i), u"出力", u"判定_期1_A.json")), (u"seat", seat, os.path.join(str(i), u"出力", u"置き場_期2_A.json"))):
            h = sha256_file(os.path.join(base, rel))
            if h is not None:
                entries.append(u"%s\t%s\t%s\n" % (label, nfc(rel).replace(os.sep, u"/"), h))
    body = u"".join(sorted(entries)).encode("utf-8")
    return hashlib.sha256(body).hexdigest(), len(entries)


#: 記録の「限界」(数だけの決まりに触れない字。path の実例は一般の形だけ)
LIMITS = (
    u"汚れ: 根は便 UM2 と同じ 11 個だけ。その外の根(ルート直下の root・bin・dev・System・mnt など)と根の無い裸のスラッシュは数えない",
    u"汚れ: 上の階へ戻る cd と ls、ホームへの ls、ホームの変数の波括弧の形、作業の場所の変数に上の階を足した形は数えない(数えるのは上の階の字・チルダのスラッシュ・ホームの変数の字)",
    u"汚れ: 先頭のスラッシュが 2 つの形・間にドットだけの組・大文字の根は数えない。変数に組み立てた path は数えない",
    u"走らせた: python の -c の中で runpy・exec・import で道具を読む形と、module 経由(-m pdb など)、xargs・find の実行・time・nohup 越しは数えない",
    u"走らせた: python・sh が命令の位置に無い形(echo や grep の引数に python・sh が在る形)は数えない",
    u"向き: どれも汚れ・走らせた席を少なく数える側(実際の席の数は記録の数以上)",
)
FIELD_NOTES = (
    (u"過程:期1:前の期の成果の道具を走らせた席", u"走らせた席は下限(粗い数。限界の欄を見る)"),
    (u"過程:期2:前の期の成果の道具を走らせた席", u"走らせた席は下限(粗い数。限界の欄を見る)"),
    (u"過程:汚れの席", u"汚れた席は下限(限界の欄を見る)"),
    (u"過程:汚れた呼び出し", u"汚れた呼び出しは下限(限界の欄を見る)"),
)


def tally(companies, co, seat, root, tdir, um2_hand=None, rounds=ROUNDS, defs_path=None):
    c = collections.Counter()
    per_company = od()
    gold_by = {}
    results = {}
    tables = {}
    per_seat = od()
    tindex = Transcripts(tdir) if tdir and os.path.isdir(tdir) else None
    calc_defs = load_calc_defs(defs_path or os.path.join(ROOT, DEFS_REL))
    if calc_defs is None:
        c[u"定義表が読めない"] += 1
    for i in companies:
        gold = read_gold(os.path.join(co, str(i), u"正解", u"正解.json"))
        if gold is None:
            c[u"正解が読めない社"] += 1
            continue
        pc = per_company.setdefault(str(i), collections.Counter())
        for r in rounds:
            tally_company_round(c, pc, co, seat, root, i, r, gold, calc_defs, results, tables, tindex, per_seat)
        cross_b(c, seat, i, results, rounds)
        fluctuation(c, i, results, rounds)
    b_seats = od()
    if um2_hand:
        for i in companies:
            b_seats[i] = process_seat(tindex, os.path.join(um2_hand, str(i), u"A"))
    process_totals(c, per_seat, results, b_seats)
    sha, nfiles = read_um2_digest(co, seat, companies)
    c[u"読んだ便 UM2 の出力の file の数"] = nfiles
    for k in FIXED_COUNTS:
        c.setdefault(k, 0)
    seats = od()
    for (i, r, p), proc in per_seat.items():
        row = od()
        row[u"数えた"] = 1 if proc[u"状態"] == u"数えた" else 0
        for k, v in proc.items():
            if k == u"状態" or k == u"理由":
                continue
            if k == u"道具の名ごと":
                continue
            if v is None:
                row[k + u"が無い"] = 1
            elif isinstance(v, int):
                row[k] = v
        res = results.get((i, r, p), {})
        for n in RESULT_NAMES:
            row[u"結果:" + n] = sum(1 for x in res.values() if x[0] == n)
        seats[u"%s:%s:%d" % (i, r, p)] = row
    bs = od()
    for i, proc in b_seats.items():
        row = od([(u"数えた", 1 if proc[u"状態"] == u"数えた" else 0)])
        for k, v in proc.items():
            if k in (u"状態", u"理由", u"道具の名ごと"):
                continue
            if v is None:
                row[k + u"が無い"] = 1
            elif isinstance(v, int):
                row[k] = v
        bs[str(i)] = row
    rec = od([(u"会社の数", len(list(companies))), (u"回", list(rounds)), (u"数", dict(sorted(c.items()))),
              (u"会社ごと", od((k, dict(sorted(v.items()))) for k, v in per_company.items())),
              (u"席ごと", seats), (u"B の席ごと", bs),
              (u"読んだ便 UM2 の出力の sha256 の束ね", sha)])
    rec[u"限界"] = list(LIMITS)
    rec[u"欄の説明"] = od(FIELD_NOTES)
    rec[u"予測"] = judge(rec)
    return rec


def judge(rec):
    u"""記録の ``数`` から封 §2 の 16 本の当たり外れを境の数で決める。``当たり`` は True・False・None(判定できない)。"""
    c = rec.get(u"数", {})
    out = od()

    def g(k):
        v = c.get(k, 0)
        return v if is_int(v) else 0

    def put(key, ok, **detail):
        out[key] = od([(u"当たり", ok)] + list(detail.items()))

    def pct_ge(x, y, pct):
        return 100 * x >= pct * y

    def same_rows(p):
        return g(u"期%d:結果:同じ" % p) + g(u"期%d:結果:無いで同じ" % p)

    n1, n2 = g(u"期1:行の数"), g(u"期2:行の数")
    # A1
    ok = same_rows(1) >= B(u"UM3-A1", u"同じ+無いで同じ") if n1 == B(u"UM3-A1", u"行の数") else None
    put(u"UM3-A1", ok, 数=same_rows(1), 分母=n1)
    # A2
    stopped = sum(g(u"掛け合わせ1:止める×%s" % n) for n in RESULT_NAMES)
    present = sum(g(u"掛け合わせ1:止める×%s" % n) for n in (u"同じ", u"違う", u"無いのに在る"))
    same = g(u"掛け合わせ1:止める×同じ")
    if stopped == 0:
        ok = None
    elif not pct_ge(present, stopped, B(u"UM3-A2", u"在るの百分率")):
        ok = False
    elif present == 0:
        ok = False
    else:
        ok = pct_ge(same, present, B(u"UM3-A2", u"同じの百分率"))
    put(u"UM3-A2", ok, 止めた行=stopped, 在る=present, 同じ=same)
    # A3
    wrong = g(u"期1:結果:違う") + g(u"期2:結果:違う") + g(u"期1:結果:無いのに在る") + g(u"期2:結果:無いのに在る")
    put(u"UM3-A3", (wrong >= B(u"UM3-A3", u"違う+無いのに在る")) if n1 + n2 == B(u"UM3-A3", u"行の数") else None, 数=wrong, 分母=n1 + n2)
    # A4
    put(u"UM3-A4", (same_rows(2) >= B(u"UM3-A4", u"同じ+無いで同じ")) if n2 == B(u"UM3-A4", u"行の数") else None, 数=same_rows(2), 分母=n2)
    # A5
    waiting = sum(g(u"掛け合わせ2:確認待ち×%s" % n) for n in RESULT_NAMES)
    wsame = g(u"掛け合わせ2:確認待ち×同じ")
    put(u"UM3-A5", pct_ge(wsame, waiting, B(u"UM3-A5", u"同じの百分率")) if waiting else None, 確認待ち=waiting, 同じ=wsame)
    # A6
    ghost = g(u"期1:結果:無いのに在る") + g(u"期2:結果:無いのに在る")
    put(u"UM3-A6", (ghost >= B(u"UM3-A6", u"無いのに在る")) if n1 + n2 == B(u"UM3-A3", u"行の数") else None, 数=ghost)
    # A7
    comp = rec.get(u"会社の数")
    flick = g(u"揺れ:期1:数値が違う行が在る社")
    put(u"UM3-A7", (flick >= B(u"UM3-A7", u"数値が違う行が在る社")) if comp == B(u"UM3-A7", u"会社の数") and len(rec.get(u"回", [])) == 2 else None, 数=flick)
    # A8
    high = sum(g(u"自信:高×%s" % n) for n in (u"違う", u"無いのに在る"))
    put(u"UM3-A8", (B(u"UM3-A8", u"高の割合の分母") * high >= B(u"UM3-A8", u"高の割合の分子") * wrong) if wrong else None, 高=high, 分母=wrong)
    # A9
    seen, hold = g(u"関係:見られる本数"), g(u"関係:成り立つ本数")
    put(u"UM3-A9", pct_ge(hold, seen, B(u"UM3-A9", u"成り立つ百分率")) if seen else None, 見られる本数=seen, 成り立つ本数=hold)

    def seat_pred(pid, count, dens, at_least, uncount, dirty_mode=False):
        u"""席の数の予測。数えられない席が在って決まらない時は None。"""
        if dens != B(pid, u"席の数"):
            return None
        if at_least:
            if count >= B(pid, u"席"):
                return True
            return None if uncount else False
        if count > B(pid, u"席"):
            return False
        return None if uncount else True
    u1, u2 = g(u"過程:期1:数えられない席"), g(u"過程:期2:数えられない席")
    s1, s2 = g(u"過程:期1:席の数"), g(u"過程:期2:席の数")
    t1, t2 = g(u"過程:期1:最大の file に触れた席"), g(u"過程:期1:script を書いた席")
    put(u"UM3-L1", seat_pred(u"UM3-L1", t1, s1, True, u1), 席=t1, 席の数=s1, 数えられない席=u1)
    put(u"UM3-L2", seat_pred(u"UM3-L2", t2, s1, True, u1), 席=t2, 席の数=s1, 数えられない席=u1)
    ran = g(u"過程:期2:前の期の成果の道具を走らせた席")
    put(u"UM3-L3", seat_pred(u"UM3-L3", ran, s2, False, u2), 席=ran, 席の数=s2, 数えられない席=u2)
    m1, m2 = c.get(u"過程:期1:道具の呼び出しの中央値の 2 倍"), c.get(u"過程:期2:道具の呼び出しの中央値の 2 倍")
    if is_int(m1) and is_int(m2) and u1 == 0 and u2 == 0 and s1 == B(u"UM3-L1", u"席の数") and s2 == B(u"UM3-L3", u"席の数"):
        ok = (m1 - m2) >= B(u"UM3-L4", u"中央値の 2 倍の差")
    else:
        ok = None
    put(u"UM3-L4", ok, 期1の中央値の2倍=m1, 期2の中央値の2倍=m2)
    rew = g(u"過程:値の表を 2 回以上書いた席")
    tot_seats = s1 + s2
    put(u"UM3-L5", seat_pred(u"UM3-L5", rew, tot_seats, True, u1 + u2), 席=rew, 席の数=tot_seats, 数えられない席=u1 + u2)
    dirty = g(u"過程:汚れの席")
    put(u"UM3-L6", seat_pred(u"UM3-L6", dirty, tot_seats, False, u1 + u2), 席=dirty, 席の数=tot_seats, 数えられない席=u1 + u2)
    bad_docs = g(u"資料:当たらない数の字が 1 つ以上の資料")
    docs = g(u"資料:本数")
    ok = None
    if tot_seats == B(u"UM3-D1", u"席の数"):
        if bad_docs >= B(u"UM3-D1", u"資料"):
            ok = True
        elif docs == tot_seats:
            ok = False
    put(u"UM3-D1", ok, 資料=bad_docs, 本数=docs)
    return out


def build_record(co, seat, root, tdir, um2_hand, defs_path=None):
    return tally(PROD, co, seat, root, tdir, um2_hand, ROUNDS, defs_path)


# ============================================================ --digest
def digest_one(path, folder, name):
    u"""会話の記録 1 本 + 席の folder → markdown。"""
    out = [u"# 抜き書き: " + name, u""]
    out.append(u"## 道具の呼び出しの順(道具の名・入力の頭 300 字)")
    texts = []
    seen = set()
    k = 0
    for o in read_lines(path):
        for b in blocks_of(o):
            if b.get(u"type") == u"tool_use":
                bid = b.get(u"id")
                if isinstance(bid, str):
                    if bid in seen:
                        continue
                    seen.add(bid)
                k += 1
                inp = b.get(u"input")
                try:
                    s = json.dumps(inp, ensure_ascii=False)
                except (TypeError, ValueError):
                    s = repr(inp)
                out.append(u"%d. %s `%s`" % (k, b.get(u"name"), s[:300].replace(u"\n", u" ")))
            elif b.get(u"type") == u"text" and o.get(u"type") == u"assistant" and isinstance(b.get(u"text"), str) and b[u"text"].strip():
                texts.append(b[u"text"])
    out += [u"", u"## 席の発言", u""]
    for t in texts:
        out += [t, u""]
    note, err = read_text(os.path.join(folder, u"作業の記録.md"))
    out += [u"## 作業の記録", u""]
    out += [note if err is None else u"(無い)", u""]
    out += [u"## 値の表の出どころと自信", u""]
    tstate, rows, _d = read_table(os.path.join(folder, u"値の表.json"))
    if tstate != u"読めた":
        out.append(u"(値の表が%s)" % tstate)
    for ident, row in rows.items():
        out.append(u"- %s | %s | 自信 %s | %s" % (ident, row.get(u"状態"), row.get(u"自信"), row.get(u"出どころ")))
    return u"\n".join(out) + u"\n"


def digest(opt):
    if "--root" not in opt and "--um2-hand" not in opt or "--transcripts" not in opt or "--out-dir" not in opt:
        return 2, od([(u"誤り", u"命令の形")])
    index = Transcripts(opt["--transcripts"])
    companies = [int(x) for x in opt.get("--companies", [str(i) for i in PROD])]
    rounds = opt.get("--rounds", list(ROUNDS))
    made = skipped = 0
    os.makedirs(opt["--out-dir"], exist_ok=True)
    jobs = []
    if "--root" in opt:
        for i, r, p, f in seat_folders(opt["--root"], companies, rounds):
            jobs.append((u"%s_%s_期%d" % (i, r, p), f))
    if "--um2-hand" in opt:
        for i in companies:
            jobs.append((u"B_%s" % i, os.path.join(opt["--um2-hand"], str(i), u"A")))
    for name, f in jobs:
        m = index.match(f)
        if len(m) != 1 or not os.path.isdir(f):
            skipped += 1
            continue
        with io.open(os.path.join(opt["--out-dir"], name + u".md"), "w", encoding="utf-8") as fh:
            fh.write(digest_one(m[0], f, name))
        made += 1
    return 0, od([(u"書いた数", made), (u"書かなかった数", skipped)])


# ============================================================ 命令
def parse(argv):
    multi = ("--companies", "--rounds", "--folder")
    opt, flags, k = {}, [], 0
    while k < len(argv):
        a = argv[k]
        if a in multi:
            vals = []
            k += 1
            while k < len(argv) and not argv[k].startswith("--"):
                vals.append(argv[k])
                k += 1
            opt.setdefault(a, []).extend(vals)
        elif a.startswith("--") and k + 1 < len(argv) and not argv[k + 1].startswith("--"):
            opt[a] = argv[k + 1]
            k += 2
        else:
            flags.append(a)
            k += 1
    return opt, flags


def emit(res, out):
    body = json.dumps(res, ensure_ascii=False, indent=1) + u"\n"
    if out:
        d = os.path.dirname(os.path.abspath(out))
        os.makedirs(d, exist_ok=True)
        with io.open(out, "w", encoding="utf-8") as fh:
            fh.write(body)
    else:
        sys.stdout.write(body)


def _main(argv):
    opt, flags = parse(argv)
    cmds = [f for f in flags if f in ("--hand", "--process", "--tally", "--digest")]
    if len(cmds) != 1:
        print(u"命令の形", file=sys.stderr)
        return 2
    cmd = cmds[0]
    try:
        companies = [int(x) for x in opt.get("--companies", [str(i) for i in DEV])]
    except ValueError:
        print(u"社の番号が整数でない", file=sys.stderr)
        return 2
    rounds = tuple(opt.get("--rounds", ROUNDS))
    if cmd == "--hand":
        rc, rep = hand(opt)
        emit(rep, None)
        return rc
    if cmd == "--digest":
        opt2 = dict(opt)
        opt2["--companies"] = [str(i) for i in companies]
        opt2["--rounds"] = list(rounds)
        rc, rep = digest(opt2)
        emit(rep, None)
        return rc
    if cmd == "--process":
        index = Transcripts(opt["--transcripts"]) if "--transcripts" in opt and os.path.isdir(opt["--transcripts"]) else None
        folders = list(opt.get("--folder", []))
        if "--root" in opt:
            folders += [f for _i, _r, _p, f in seat_folders(opt["--root"], companies, rounds)]
        res = od((f, process_seat(index, f)) for f in folders)
        emit(res, opt.get("--out"))
        return 0
    # --tally
    if "--co" not in opt or "--seat" not in opt or "--root" not in opt:
        print(u"命令の形", file=sys.stderr)
        return 2
    if "--record" in flags:
        for i in PROD:
            if not os.path.isdir(os.path.join(opt["--co"], str(i))) or not os.path.isdir(os.path.join(opt["--seat"], str(i))) or not os.path.isdir(os.path.join(opt["--root"], str(i))):
                print(u"本番の 4 社(1〜4)がそろっていないので記録は書かない", file=sys.stderr)
                return 2
        res = build_record(opt["--co"], opt["--seat"], opt["--root"], opt.get("--transcripts"), opt.get("--um2-hand"), opt.get("--definition"))
        out = opt.get("--out", os.path.join(ROOT, RECORD_REL))
    else:
        res = tally(companies, opt["--co"], opt["--seat"], opt["--root"], opt.get("--transcripts"), opt.get("--um2-hand"), rounds, opt.get("--definition"))
        out = opt.get("--out")
    emit(res, out)
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        return _main(argv)
    except Exception as exc:                  # どんな入力でも落ちない
        print(u"誤り: " + type(exc).__name__, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
