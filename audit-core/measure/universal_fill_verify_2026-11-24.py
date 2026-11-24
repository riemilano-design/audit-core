# -*- coding: utf-8 -*-
u"""封 docs/UNIVERSAL_FILL_VERIFY_SEAL_2026-11-24.md(便 UM4)の道具。**費用は 0・API は呼ばない・席は呼ばない。**

先に普通の AI の席が全部の数を埋め(段 1)、後から別の席が根拠を調べる(段 2)作り方を、便 UM2 の作り方(型の席 + 検査)と並べて数える。

    python3 -I universal_fill_verify_2026-11-24.py --material <社の folder>                       # 素材の形の検査(封 §1-1)。出力は規則の名と OK/NG だけ
    python3 -I universal_fill_verify_2026-11-24.py --hand    --co <dir> --root <dir> --company N --kind fill --round a|b | --kind check-orig | check-broken | type
    python3 -I universal_fill_verify_2026-11-24.py --mutate  --co <dir> --root <dir> --company N [--changes-out <file>]
    python3 -I universal_fill_verify_2026-11-24.py --status  --co <dir> --root <dir> --company N --which orig|broken [--rows-out <file>] [--doc-out <file>]
    python3 -I universal_fill_verify_2026-11-24.py --through --root <dir> --company N [--out <file>]
    python3 -I universal_fill_verify_2026-11-24.py --process --transcripts <dir> (--folder <dir> ... | --root <dir> [--companies N ...]) [--out <file>]
    python3 -I universal_fill_verify_2026-11-24.py --tally   --co <dir> --root <dir> [--transcripts <dir>] [--companies N ...] [--material-first-ng N ...] [--out <file>]
    python3 -I universal_fill_verify_2026-11-24.py --tally --record ...     # 本番の 4 社(5〜8)がそろった時だけ fixtures/universal/um4/record.json を書く
    python3 -I universal_fill_verify_2026-11-24.py --digest  --co <dir> --root <dir> --transcripts <dir> --out-dir <dir> [--companies N ...]

folder の形(``<root>/<社>/`` の下):
    ``fill/a``・``fill/b``(埋める席。素材/・指定.json・definition_A.json・頼み.md。席が 値の表・資料・作業の記録 を書く)
    ``check/orig``・``check/broken``(確かめる席。素材/・指定.json・definition_A.json・出どころの書き方.md・確かめる表・頼み.md。席が 根拠の表 を書く)
    ``type``(型の席。期1/・指定.json・definition_A.json・指示書.md。席が 材料_期1_A を書く)
    席の folder の外(``<root>/<社>/`` の直下)に 壊し方の表・判定・段 3 の資料を書く(席の folder には置かない)。
    ``<co>/<社>/期1/``(素材)・``正解/正解.json``・``正解/罠.json``・``正解/期.json``(素材を作った席が書いたもの。席には渡さない)

実装の注(封の字では 1 通りに決まらなかった所の素直な読み。結果を見て変えない。報告にも書く):
- 素材の形の検査の「罠の値が升に在る」は、CSV(UTF-8 の BOM 可 → CP932 の順に読む)の ``行``・``列``(1 から。頭の行が 1 行目)の cell の前後の空白と桁区切りのコンマを取った字が、
  負は ``-`` だけを許す整数の字で、罠の値と同じ数の時。``file`` は ``期1/`` の下の相対 path(``..``・絶対 path・空の部分は読まない)。「期.json に始まりと終わりが在る」は、2 つの鍵の字が ISO の日付として読める時。
  「無い の項目だけ正解が null」は 18 個について見る(月次の売上高と人件費は見ない)。
- 確かめの状態: 表に行が無い id・見立てが表の状態の組に無い字(``在る`` の行に ``無いで合う`` など)・根拠の表の file が無いか読めない時は ``答えなし``。
  ``合う`` の出どころは、種類が 3 つのどれかで ``表示の倍率`` が整数のものだけ計算し直す(便 UM2 の検査の ``analyse`` で出どころの cell・明細・条件の和を出し倍率を掛ける。見出し・期・単位・範囲の規則は当てない)。
  倍率が整数でない・出どころが読めない・計算できない・表の数が整数の字でない・計算が違う → ``根拠なし``。``別の道`` は同じ計算で表の数と同じになり ``file`` が違う時だけ 2 道。
  同じ id の行が 2 つ以上なら最初の 1 つを読む。表の ``状態`` が ``在る`` でない行の表の数は無いものとする。
- 直せた: ``正しいと見る数値`` が整数の字で正解と同じ → 直せた・違う → 直しが違う・無い(null・読めない字) → 直しなし。出どころは見ない。正解が null の行は、どんな数でも「直しが違う」。
- 型の席の判定: 便 UM2 の検査を ``check_files`` で当てる(印の file は渡さない。1 期目と同じ)。表の行の和の材料は「通す(取り方は未確認)」になり、通すに数えない(封のとおり)。
  束が断りの時は全行を ``断り`` と数える(束の中の答えは正解と照合する)。
- 壊し方 §1-4: 「回 α が違う数」の判定は 罠の行の回 α の ``状態`` が ``在る`` で整数の字なら数が罠の値と違う時・``在る`` でなければ当たる。
  3 の「値を借りた行」は 隣 の行(借りた側)。5 はその次の普通の行。4 の「切り捨て」は 0 の側。数値は 10 進の字で書く。壊した後の ``状態``・``数値`` が正解と同じになった行は壊した行から外す(表は壊したまま)。
  「壊していない行」は 1 社 30 行から、表を変えた行(外した行を含む)を除いた行。
- 行の種類: 罠.json の 決め の項目 → 決め・罠 の項目 → 罠・正解が null → 無い・ほかは普通(月次の売上高 12 行は普通)。
  決めの行の名は ``決め:1つ目``・``決め:2つ目``・``決め:どちらでもない``・``決め:分からない``・``決め:無い``・``決め:答えなし``・``決め:形が読めない``(同じ・違うには入れない)。
  罠を取った = 罠の行で結果が 違う かつ数が罠の値と同じ(違うにも数える)。
- 揺れ: 回 α が違った行 = 決め以外で 違う・無いのに在る・無いで違う。回 β も同じ答え = 同じ結果の名で、違う・無いのに在る の時は数も同じ。
- 過程の数: 便 UM3 の数え方を写した(道具の呼び出し・秒・汚れ・書き込み・script)。前の期の成果に触れる数は無い(1 期だけ)。席と会話の記録の対応は最初の user の文に席の folder の path が在る 1 本。
- 外した社(封 §1-1): ``--tally`` の ``--exclude N ...`` に渡した社は全部の分母に入れず、記録の ``外した社の数`` に数だけ持つ(番号は書かない)。``会社の数`` は数えた社。
  ``--record`` は 5〜8 のうち外していない社が全部そろった時だけ書く(外す社は 5〜8 の中・数える社が 1 つ以上)。
- 確かめる席の folder(``--hand --kind check-orig|check-broken``)は、回 α の値の表が無い・読めない・行が 0 の時は何も作らず rc 7。
- 素材の形の検査の「罠の値が書かれた升に在る」は、罠の file が symlink なら NG(封の字に無い厳しい側の読み。path の途中の folder の symlink は見ない)。
- ``表示の倍率`` は 0 や負でも整数なら受ける(封は範囲を決めていない。限界)。
- 素材の形の検査で最初に落ちた社は ``--material-first-ng`` で渡す(司令塔が記録する。script は最初の検査の結果を知らない)。

限界(結果の文書はここから写す。測っていないことは書かない):
- 機械が計算し直すのは確かめる席の出どころの数だけ。出どころが項目の意味・期・範囲に合うかは見ない。
- ``表示の倍率`` が 0 や負の整数でも出どころの計算をそのまま受ける(封が範囲を決めていない)。
- 汚れ・書き込み・script の数えは便 UM3 と同じ限界(取りこぼす形と数え過ぎる形が両方在る)。
"""
from __future__ import print_function

import collections
import csv
import datetime
import hashlib
import importlib.util
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
UM2_CHECK_REL = "measure/universal_through_check_2026-11-23.py"
INSTR_REL = "docs/UNIVERSAL_THROUGH_INSTRUCTION_2026-11-23.md"
FILL_BRIEF_REL = "docs/UNIVERSAL_PROCESS_BRIEF_2026-11-24.md"
CHECK_BRIEF_REL = "docs/UNIVERSAL_FILL_VERIFY_CHECK_BRIEF_2026-11-24.md"
RECORD_REL = "fixtures/universal/um4/record.json"
od = collections.OrderedDict

DEV = (102,)
PROD = (5, 6, 7, 8)
ROUNDS = ("a", "b")

RESULT_NAMES = ("同じ", "違う", "無いのに在る", "無いで同じ", "無いで違う", "分からない", "答えなし", "形が読めない")
DECIDE_NAMES = ("決め:1つ目", "決め:2つ目", "決め:どちらでもない", "決め:分からない", "決め:無い", "決め:答えなし", "決め:形が読めない")
ALL_NAMES = RESULT_NAMES + DECIDE_NAMES
KINDS = ("普通", "無い", "罠", "決め")
STATES = ("在る", "無い", "分からない")
GOLD_KEYS = [
    ("a01", "売上高_当期"), ("a02", "売上高_前期"), ("a03", "売上総利益_当期"), ("a04", "営業利益_当期"), ("a05", "営業利益_前期"),
    ("a06", "経常利益_当期"), ("a07", "当期純利益_当期"), ("a08", "減価償却費_当期"), ("a09", "現金及び預金_当期末"),
    ("a10", "流動資産合計_当期末"), ("a11", "資産合計_当期末"), ("a12", "短期借入金_当期末"), ("a13", "長期借入金_当期末"),
    ("a14", "負債合計_当期末"), ("a15", "純資産合計_当期末"), ("a16", "純資産合計_前期末"),
    ("a29", "借入の残高の合計_当期末"), ("a30", "期末の従業員数_当期末"),
]
NAME_TO_ID = dict((k, i) for i, k in GOLD_KEYS)
MONTH_KEY = "月次の売上高_当期"
MONTH_IDS = ["a%d" % (16 + k) for k in range(1, 13)]
A_IDS = ["a%02d" % k for k in range(1, 31)]
FORBIDDEN_NAMES = ("正解", "作り方")       # 席の folder の中に在ってはいけない名(--hand が確かめる)
UNREADABLE = object()
SPEC_FILES = ("正解/正解.json", "正解/罠.json", "正解/期.json")

# 確かめの状態(封 §1-3)
S_2, S_OK, S_NOBASIS, S_MISMATCH, S_REVIEW, S_NONE_OK, S_NONE_OBJ, S_NA = (
    "確認済み(2 道)", "確認済み", "根拠なし", "不一致", "要確認", "無いを確かめた", "無いに異議", "答えなし")
STATUS_NAMES = (S_2, S_OK, S_NOBASIS, S_MISMATCH, S_REVIEW, S_NONE_OK, S_NONE_OBJ, S_NA)
PASS_STATUSES = (S_2, S_OK, S_NONE_OK)
VIEW_PRESENT = ("合う", "合わない", "見つからない", "決めが要る")
VIEW_ABSENT = ("無いで合う", "在るはず", "決めが要る")
MUT_KINDS = ("罠の値", "桁", "隣", "無いのに在る", "在るのに無い")
MUT_EXPECT = {"罠の値": 2, "桁": 1, "隣": 1, "無いのに在る": 1, "在るのに無い": 1}
WRONG_NAMES = ("違う", "無いのに在る", "無いで違う")
SAME_NAMES = ("同じ", "無いで同じ")
JUDGES = ("通す", "通す(取り方は未確認)", "止める", "無いを受ける", "断り", "判定なし")
JUDGE_PASS = ("通す", "無いを受ける")
METHODS = ("埋めのみ", "埋め+確かめ", "型+検査")
METRICS = ("取得", "止めすぎ", "通した誤り", "決めを通した", "通さなかった誤り")
RULE_NAMES = ("K0", "K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8", "K9", "K11")
SEAT_KINDS = ("fill-a", "fill-b", "check-orig", "check-broken", "type")
SEAT_LABEL = {"fill-a": "埋めa", "fill-b": "埋めb", "check-orig": "確かめ原", "check-broken": "確かめ壊", "type": "型"}

#: 絶対 path の根は path の先頭でだけ読む(直前が path の字・``/``・``.``・``-`` なら相対 path の途中なので根としない。``file://`` の直後の根は根)
FOLDER_ROOTS = r"(?:(?<![\w.\-/])|(?<=file://))/(?:private|Users|tmp|var|etc|home|opt|usr|Library|Applications|Volumes)[^\s\"'\\)]*"
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

def write_json(path, obj):
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False, indent=1) + u"\n")



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


def is_synthetic(o):
    u"""会話の記録の 1 行が上限切れなどの合成メッセージか(席の発言に数えない)。"""
    if not isinstance(o, dict):
        return False
    msg = o.get(u"message")
    return o.get(u"isApiErrorMessage") is True or (isinstance(msg, dict) and msg.get(u"model") == u"<synthetic>")



# ============================================================ 素材の形の検査(--material)
def read_gold1(path):
    u"""正解の file → {id: 値か None か UNREADABLE}(期1 だけ)。読めなければ None。"""
    obj, err = read_json(path)
    if err or not isinstance(obj, dict):
        return None
    body = obj.get(u"期1")
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
    return vals


def read_forms(path):
    u"""罠.json → {"無い": [id], "罠": {id: 罠の値}, "決め": {id: (値1, 値2)}, "行": 項目の数の形の問題なし} 。読めなければ None。
    形が崩れた所は黙って飛ばす(形の検査は ``--material`` が別に見る)。"""
    obj, err = read_json(path)
    if err or not isinstance(obj, dict):
        return None
    out = {u"無い": [], u"罠": {}, u"決め": {}}
    for nm in obj.get(u"無い") if isinstance(obj.get(u"無い"), list) else []:
        if isinstance(nm, str) and nm in NAME_TO_ID:
            out[u"無い"].append(NAME_TO_ID[nm])
    for t in obj.get(u"罠") if isinstance(obj.get(u"罠"), list) else []:
        if isinstance(t, dict) and isinstance(t.get(u"項目"), str) and t[u"項目"] in NAME_TO_ID and is_int(t.get(u"罠の値")):
            out[u"罠"][NAME_TO_ID[t[u"項目"]]] = t[u"罠の値"]
    for t in obj.get(u"決め") if isinstance(obj.get(u"決め"), list) else []:
        if isinstance(t, dict) and isinstance(t.get(u"項目"), str) and t[u"項目"] in NAME_TO_ID and isinstance(t.get(u"読み"), list):
            vs = [x.get(u"値") for x in t[u"読み"] if isinstance(x, dict)]
            if len(vs) == 2 and all(is_int(v) for v in vs):
                out[u"決め"][NAME_TO_ID[t[u"項目"]]] = (vs[0], vs[1])
    return out


def row_kinds(gold, forms):
    u"""→ {id: 種類}。決め → 罠 → 正解が null なら 無い → 普通。"""
    out = {}
    for i in A_IDS:
        if forms is not None and i in forms[u"決め"]:
            out[i] = u"決め"
        elif forms is not None and i in forms[u"罠"]:
            out[i] = u"罠"
        elif gold.get(i, UNREADABLE) is None:
            out[i] = u"無い"
        else:
            out[i] = u"普通"
    return out


def safe_rel(name):
    if not isinstance(name, str) or not name or name.startswith(u"/") or u"\\" in name or u"\x00" in name:
        return False
    return all(x not in (u"", u".", u"..") for x in name.split(u"/"))


def read_csv_rows(path):
    u"""CSV(UTF-8 の BOM 可 → CP932)→ 行の並び。読めなければ None。"""
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError:
        return None
    for enc in ("utf-8-sig", "cp932"):
        try:
            text = raw.decode(enc)
        except UnicodeDecodeError:
            continue
        try:
            return list(csv.reader(io.StringIO(text)))
        except (csv.Error, MemoryError):
            return None
    return None


def cell_int(text):
    u"""cell の字 → 整数か None(前後の空白とコンマを取る。負は ``-`` だけ)。"""
    if not isinstance(text, str):
        return None
    t = nfc(text).strip().replace(u",", u"")
    if not re.match(r"^-?[0-9]+\Z", t) or len(t) > 4000:
        return None
    try:
        return int(t)
    except ValueError:
        return None


def iso_date(s):
    if not isinstance(s, str) or not re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}\Z", s):
        return None
    try:
        return datetime.date(int(s[:4]), int(s[5:7]), int(s[8:10]))
    except ValueError:
        return None


MATERIAL_RULES = ("罠が 4 つ", "無いが 3 つ", "決めが 2 つ", "9 項目が別", "9 項目が 18 個の中", "無いの項目だけ正解が null",
                  "罠の値が正解と違う整数", "罠の値が書かれた升に在る", "決めの 2 つの値が違う", "期の始まりと終わりが在る", "素材の file が在る")


def material_rules(folder):
    u"""社の folder(``期1/`` と ``正解/``)→ OrderedDict(規則の名 → True(OK)/False(NG))。落ちない。"""
    res = od((k, False) for k in MATERIAL_RULES)
    try:
        obj, err = read_json(os.path.join(folder, u"正解", u"罠.json"))
        gold = read_gold1(os.path.join(folder, u"正解", u"正解.json"))
        if err is None and isinstance(obj, dict):
            traps = obj.get(u"罠")
            nones = obj.get(u"無い")
            decs = obj.get(u"決め")
            res[u"罠が 4 つ"] = isinstance(traps, list) and len(traps) == 4 and all(isinstance(t, dict) for t in traps)
            res[u"無いが 3 つ"] = isinstance(nones, list) and len(nones) == 3 and all(isinstance(x, str) for x in nones)
            res[u"決めが 2 つ"] = isinstance(decs, list) and len(decs) == 2 and all(isinstance(t, dict) for t in decs)
            names = []
            if res[u"罠が 4 つ"] and res[u"無いが 3 つ"] and res[u"決めが 2 つ"]:
                names = list(nones) + [t.get(u"項目") for t in traps] + [t.get(u"項目") for t in decs]
                res[u"9 項目が別"] = all(isinstance(x, str) for x in names) and len(set(names)) == 9
                res[u"9 項目が 18 個の中"] = all(isinstance(x, str) and x in NAME_TO_ID for x in names)
            if gold is not None and res[u"無いが 3 つ"] and all(x in NAME_TO_ID for x in nones):
                want = set(NAME_TO_ID[x] for x in nones)
                res[u"無いの項目だけ正解が null"] = all(gold[i] is not UNREADABLE and ((gold[i] is None) == (i in want)) for i, _k in GOLD_KEYS)
            if res[u"罠が 4 つ"] and gold is not None:
                ok = True
                ok2 = True
                for t in traps:
                    nm, v = t.get(u"項目"), t.get(u"罠の値")
                    g = gold.get(NAME_TO_ID.get(nm), UNREADABLE) if isinstance(nm, str) else UNREADABLE
                    if not (is_int(v) and is_int(g) and v != g):
                        ok = False
                    f, r, c = t.get(u"file"), t.get(u"行"), t.get(u"列")
                    cell = None
                    if safe_rel(f) and is_int(r) and is_int(c) and r >= 1 and c >= 1:
                        path = os.path.join(folder, u"期1", *f.split(u"/"))
                        if os.path.isfile(path) and not os.path.islink(path):
                            rows = read_csv_rows(path)
                            if rows is not None and r <= len(rows) and c <= len(rows[r - 1]):
                                cell = cell_int(rows[r - 1][c - 1])
                    if not (is_int(v) and cell is not None and cell == v):
                        ok2 = False
                res[u"罠の値が正解と違う整数"] = ok
                res[u"罠の値が書かれた升に在る"] = ok2
            if res[u"決めが 2 つ"]:
                ok = True
                for t in decs:
                    rd = t.get(u"読み")
                    vs = [x.get(u"値") for x in rd if isinstance(x, dict)] if isinstance(rd, list) else []
                    if not (isinstance(rd, list) and len(rd) == 2 and len(vs) == 2 and all(is_int(v) for v in vs) and vs[0] != vs[1]):
                        ok = False
                res[u"決めの 2 つの値が違う"] = ok
        per, perr = read_json(os.path.join(folder, u"正解", u"期.json"))
        if perr is None and isinstance(per, dict):
            res[u"期の始まりと終わりが在る"] = iso_date(per.get(u"当期の始まり")) is not None and iso_date(per.get(u"当期の終わり")) is not None
        n = 0
        for _d, _ds, fs in os.walk(os.path.join(folder, u"期1")):
            n += len(fs)
        res[u"素材の file が在る"] = n >= 1
    except Exception:                            # どんな入力でも落ちない
        pass
    return res


def material_report(folder):
    rules = material_rules(folder)
    return od([(u"規則", od((k, u"OK" if v else u"NG") for k, v in rules.items())), (u"全部", u"OK" if all(rules.values()) else u"NG")])


# ============================================================ 席の出力の読み・行ごとの結果
def read_table(path):
    u"""→ (状態, {id: 行}, 重複の数)。状態は ``無し``・``読めない``・``読めた``。"""
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
    u"""1 行の結果の名(便 UM3 と同じ 8 つ)。正解が読めない行は None。"""
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
    if not isinstance(row, dict):
        return u"なし"
    c = row.get(u"自信")
    return c if c in (u"高", u"中", u"低") else u"読めない"


def answer_name(kind, gold_v, tstate, row, trap_val, readings):
    u"""席の答え 1 行 → (結果の名, 数(在ると書いた時の整数か None), 罠を取ったか)。正解が読めない行は (None, None, False)。"""
    base = classify(gold_v, tstate, row)
    if base is None:
        return None, None, False
    n = int_text(row.get(u"数値")) if isinstance(row, dict) and row.get(u"状態") == u"在る" else None
    if kind == u"決め":
        if base in (u"答えなし", u"形が読めない"):
            return u"決め:" + base, None, False
        st = row.get(u"状態")
        if st == u"在る":
            if n is None:
                return u"決め:形が読めない", None, False
            r1 = readings[0] if readings else gold_v
            r2 = readings[1] if readings else None
            if n == r1:
                return u"決め:1つ目", n, False
            if r2 is not None and n == r2:
                return u"決め:2つ目", n, False
            return u"決め:どちらでもない", n, False
        return (u"決め:分からない" if st == u"分からない" else u"決め:無い"), None, False
    trapped = kind == u"罠" and base == u"違う" and trap_val is not None and n == trap_val
    if base not in (u"同じ", u"違う", u"無いのに在る"):
        n = None
    return base, n, trapped


def fill_answers(gold, forms, tstate, rows):
    u"""埋める席の表 → {id: (名, 数, 罠を取った, 自信, 種類)}(正解が読めない行は入れない)。"""
    kinds = row_kinds(gold, forms)
    out = od()
    for i in A_IDS:
        g = gold.get(i, UNREADABLE)
        row = rows.get(i)
        tv = forms[u"罠"].get(i) if forms is not None else None
        rd = forms[u"決め"].get(i) if forms is not None else None
        name, n, trapped = answer_name(kinds[i], g, tstate, row, tv, rd)
        if name is None:
            continue
        out[i] = (name, n, trapped, conf_name(row), kinds[i])
    return out


def is_wrong(name):
    return name in WRONG_NAMES


def is_same(name):
    return name in SAME_NAMES


# ============================================================ 壊した表(--mutate。封 §1-4)
def _alpha_state_int(row):
    u"""回 α の行 → 整数(``在る`` で整数の字の時)か None。"""
    if isinstance(row, dict) and row.get(u"状態") == u"在る":
        return int_text(row.get(u"数値"))
    return None


def _trunc_div(n, d):
    return n // d if n >= 0 else -((-n) // d)


def make_broken(rows, gold, forms):
    u"""回 α の表の行({id: 行})・正解・罠.json → 変えた行の並び と 作れなかった数。

    変えた行 = {"id", "種類", "状態", "数値"(整数か None), "外した"(壊した後が正解と同じ)}。落ちない。"""
    kinds = row_kinds(gold, forms)
    changes = []
    if forms is None:
        return changes, dict(MUT_EXPECT)
    ids = sorted(A_IDS)
    # 1 罠の値 ×2
    picked = 0
    for i in ids:
        if picked >= 2:
            break
        if kinds[i] != u"罠":
            continue
        tv = forms[u"罠"].get(i)
        if tv is None:
            continue
        if _alpha_state_int(rows.get(i)) != tv:
            changes.append({u"id": i, u"種類": u"罠の値", u"状態": u"在る", u"数値": tv})
            picked += 1
    normal = [i for i in ids if kinds[i] == u"普通" and _alpha_state_int(rows.get(i)) is not None]
    num = dict((i, _alpha_state_int(rows.get(i))) for i in normal)
    # 2 桁 ×1
    pos = None
    for k, i in enumerate(normal):
        if abs(num[i]) >= 1000:
            pos = k
            break
    if pos is not None:
        i = normal[pos]
        s = str(abs(num[i]))
        s2 = s[0] + str((int(s[1]) + 1) % 10) + s[2:]
        v = int(s2)
        changes.append({u"id": i, u"種類": u"桁", u"状態": u"在る", u"数値": -v if num[i] < 0 else v})
        # 3 隣 ×1
        if pos + 1 < len(normal):
            j = normal[pos + 1]
            lender = None
            for k in range(pos + 2, len(normal)):
                if num[normal[k]] != num[j]:
                    lender = normal[k]
                    break
            if lender is not None:
                changes.append({u"id": j, u"種類": u"隣", u"状態": u"在る", u"数値": num[lender]})
                # 5 在るのに無い ×1(借りた行の次の普通の行)
                if pos + 2 < len(normal):
                    changes.append({u"id": normal[pos + 2], u"種類": u"在るのに無い", u"状態": u"無い", u"数値": None})
    # 4 無いのに在る ×1
    a01 = _alpha_state_int(rows.get(u"a01"))
    if a01 is not None:
        for i in ids:
            r_ = rows.get(i)
            if kinds[i] == u"無い" and not (isinstance(r_, dict) and r_.get(u"状態") == u"在る"):
                changes.append({u"id": i, u"種類": u"無いのに在る", u"状態": u"在る", u"数値": _trunc_div(a01, 10)})
                break
    made = collections.Counter(c[u"種類"] for c in changes)
    for c in changes:
        g = gold.get(c[u"id"], UNREADABLE)
        if c[u"状態"] == u"在る":
            c[u"外した"] = is_int(g) and c[u"数値"] == g
        else:
            c[u"外した"] = g is None
    not_made = dict((k, MUT_EXPECT[k] - made.get(k, 0)) for k in MUT_KINDS)
    changes.sort(key=lambda c: (MUT_KINDS.index(c[u"種類"]), c[u"id"]))
    return changes, not_made


def given_table_rows(rows):
    u"""回 α の表の行 → 確かめる表の行(id・状態・数値だけ)。"""
    out = []
    for i, r in rows.items():
        out.append(od([(u"id", i), (u"状態", r.get(u"状態")), (u"数値", r.get(u"数値"))]))
    return out


def broken_table_rows(rows, changes):
    u"""確かめる表の行(原)に変えた行を当てる。"""
    out = given_table_rows(rows)
    index = dict((r[u"id"], k) for k, r in enumerate(out))
    for c in changes:
        row = od([(u"id", c[u"id"]), (u"状態", c[u"状態"]), (u"数値", None if c[u"数値"] is None else str(c[u"数値"]))])
        if c[u"id"] in index:
            out[index[c[u"id"]]] = row
        else:
            out.append(row)
    return out


def mutate_report(changes, not_made):
    rep = od()
    for k in MUT_KINDS:
        mine = [c for c in changes if c[u"種類"] == k]
        rep[k] = od([(u"作った", len(mine)), (u"作れなかった", not_made.get(k, MUT_EXPECT[k])), (u"外した", sum(1 for c in mine if c[u"外した"]))])
    rep[u"作れなかった数"] = sum(not_made.values())
    rep[u"外した数"] = sum(1 for c in changes if c[u"外した"])
    rep[u"壊した行の数"] = sum(1 for c in changes if not c[u"外した"])
    return rep


# ============================================================ 確かめの状態(--status。封 §1-3)
def load_check_module():
    u"""便 UM2 の検査を file の path から読み込む(字は変えない)。"""
    spec = importlib.util.spec_from_file_location("um4_through_check_by_path", os.path.join(ROOT, UM2_CHECK_REL))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _Ctx(object):
    pass


def source_value(chk, src, s):
    u"""出どころ → 計算し直した数(Fraction)か None。出どころから数を出す所だけ(見出し・期・単位・範囲の規則は当てない)。"""
    try:
        if not isinstance(s, dict):
            return None
        mult = s.get(u"表示の倍率")
        if not is_int(mult):
            return None
        ctx = _Ctx()
        ctx.src = src
        info = chk.analyse(ctx, {u"出どころ": s}, {})
        num = info.get(u"num")
        if num is None:
            return None
        return num * mult
    except Exception:
        return None


def judge_status(trow, orow, chk, src):
    u"""表の行 1 つ・確かめる席の行 1 つ → 状態の名(封 §1-3 の表)。落ちない。"""
    try:
        if not isinstance(trow, dict) or trow.get(u"状態") not in STATES or not isinstance(orow, dict):
            return S_NA
        present = trow.get(u"状態") == u"在る"
        view = orow.get(u"見立て")
        if not isinstance(view, str) or view not in (VIEW_PRESENT if present else VIEW_ABSENT):
            return S_NA
        if not present:
            return {u"無いで合う": S_NONE_OK, u"在るはず": S_NONE_OBJ}.get(view, S_REVIEW)
        if view == u"見つからない":
            return S_NOBASIS
        if view == u"合わない":
            return S_MISMATCH
        if view == u"決めが要る":
            return S_REVIEW
        tn = int_text(trow.get(u"数値"))
        s = orow.get(u"出どころ")
        if tn is None:
            return S_NOBASIS
        v = source_value(chk, src, s)
        if v is None or v != tn:
            return S_NOBASIS
        alt = orow.get(u"別の道")
        if isinstance(alt, dict) and isinstance(alt.get(u"file"), str) and isinstance(s.get(u"file"), str) \
                and nfc(alt[u"file"]) != nfc(s[u"file"]):
            v2 = source_value(chk, src, alt)
            if v2 is not None and v2 == tn:
                return S_2
        return S_OK
    except Exception:
        return S_NA


def fix_name(status, orow, gold_v):
    u"""不一致・無いに異議 の行 → 直せた・直しが違う・直しなし。ほかは None。"""
    if status not in (S_MISMATCH, S_NONE_OBJ):
        return None
    n = int_text(orow.get(u"正しいと見る数値")) if isinstance(orow, dict) else None
    if n is None:
        return u"直しなし"
    return u"直せた" if (is_int(gold_v) and n == gold_v) else u"直しが違う"


def status_rows(chk, src, given, ostate, orows, gold):
    u"""→ od({id: (状態, 直し)})。正解が読めない行は入れない。"""
    out = od()
    for i in A_IDS:
        g = gold.get(i, UNREADABLE)
        if g is UNREADABLE:
            continue
        if ostate != u"読めた":
            out[i] = (S_NA, None)
            continue
        st = judge_status(given.get(i), orows.get(i), chk, src)
        out[i] = (st, fix_name(st, orows.get(i), g))
    return out


def given_rows_of(folder, fallback_rows):
    u"""席の folder の 確かめる表(席に渡したもの)→ {id: 行}。読めなければ fallback。"""
    st, rows, _d = read_table(os.path.join(folder, u"確かめる表.json"))
    if st == u"読めた":
        return rows
    return dict((r[u"id"], r) for r in fallback_rows)


# ============================================================ --hand
def seat_dir(root, i, kind):
    i = str(i)
    if kind == u"fill-a":
        return os.path.join(root, i, u"fill", u"a")
    if kind == u"fill-b":
        return os.path.join(root, i, u"fill", u"b")
    if kind == u"check-orig":
        return os.path.join(root, i, u"check", u"orig")
    if kind == u"check-broken":
        return os.path.join(root, i, u"check", u"broken")
    return os.path.join(root, i, u"type")


def has_forbidden(folder):
    for _d, dirs, files in os.walk(folder):
        for n in dirs + files:
            if nfc(n) in FORBIDDEN_NAMES or nfc(n) == u"頼み.md":
                return True
    return False


def hand_problems(dest):
    u"""出す先に 正解・作り方 の名が 1 つも無いことを自分で確かめる。"""
    out = []
    for _d, dirs, files in os.walk(dest):
        for n in dirs + files:
            if nfc(n) in FORBIDDEN_NAMES:
                out.append(u"禁止の名: " + nfc(n))
    return out


def read_period(co_company):
    per, err = read_json(os.path.join(co_company, u"正解", u"期.json"))
    if err or not isinstance(per, dict) or iso_date(per.get(u"当期の始まり")) is None or iso_date(per.get(u"当期の終わり")) is None:
        return None
    return od([(u"成果物", u"A"), (u"当期の始まり", per[u"当期の始まり"]), (u"当期の終わり", per[u"当期の終わり"])])


def hand(opt):
    u"""席の folder を作る(写すだけ)。→ (rc, 報告)。出す先が既に在れば何もしない。"""
    need = ("--co", "--root", "--company", "--kind")
    if any(k not in opt for k in need):
        return 2, od([(u"誤り", u"命令の形")])
    try:
        i = int(opt["--company"])
    except ValueError:
        return 2, od([(u"誤り", u"社の番号が整数でない")])
    kind = opt["--kind"]
    if kind == u"fill":
        r = opt.get("--round")
        if r not in ROUNDS:
            return 2, od([(u"誤り", u"回の値")])
        kind = u"fill-" + r
    if kind not in SEAT_KINDS:
        return 2, od([(u"誤り", u"種類の値")])
    dest = seat_dir(opt["--root"], i, kind)
    if os.path.exists(dest):
        return 3, od([(u"誤り", u"出す先が既に在る(何もしない)")])
    co_company = os.path.join(opt["--co"], str(i))
    mat = os.path.join(co_company, u"期1")
    spec = read_period(co_company)
    defn = opt.get("--definition", os.path.join(ROOT, DEFS_REL))
    fill_brief = opt.get("--brief", os.path.join(ROOT, FILL_BRIEF_REL))
    check_brief = opt.get("--brief", os.path.join(ROOT, CHECK_BRIEF_REL))
    instr = opt.get("--instruction", os.path.join(ROOT, INSTR_REL))
    srcs = [mat, defn, instr if kind in (u"type", u"check-orig", u"check-broken") else defn,
            fill_brief if kind.startswith(u"fill") else (check_brief if kind.startswith(u"check") else defn)]
    if spec is None or any(not os.path.exists(x) for x in srcs):
        return 4, od([(u"誤り", u"写す元が無いか読めない")])
    if has_forbidden(mat):
        return 5, od([(u"誤り", u"素材の元に正解・作り方の名が在る(何も作らない)")])
    rows_n = None
    table_rows = []
    if kind.startswith(u"check"):
        ast, arows, _d = read_table(os.path.join(seat_dir(opt["--root"], i, u"fill-a"), u"値の表.json"))
        if ast != u"読めた" or not arows:
            return 7, od([(u"誤り", u"回 α の値の表が無い・読めない・行が 0(席の folder は作らない)")])
        table_rows = given_table_rows(arows)
        if kind == u"check-broken":
            gold = read_gold1(os.path.join(co_company, u"正解", u"正解.json"))
            forms = read_forms(os.path.join(co_company, u"正解", u"罠.json"))
            if gold is not None:
                changes, _nm = make_broken(arows, gold, forms)
                table_rows = broken_table_rows(arows, changes)
        rows_n = len(table_rows)
    os.makedirs(dest)
    if kind == u"type":
        shutil.copytree(mat, os.path.join(dest, u"期1"))
        write_json(os.path.join(dest, u"指定.json"), spec)
        shutil.copyfile(defn, os.path.join(dest, u"definition_A.json"))
        shutil.copyfile(instr, os.path.join(dest, u"指示書.md"))
    else:
        shutil.copytree(mat, os.path.join(dest, u"素材"))
        write_json(os.path.join(dest, u"指定.json"), spec)
        shutil.copyfile(defn, os.path.join(dest, u"definition_A.json"))
        if kind.startswith(u"fill"):
            shutil.copyfile(fill_brief, os.path.join(dest, u"頼み.md"))
        else:
            shutil.copyfile(instr, os.path.join(dest, u"出どころの書き方.md"))
            write_json(os.path.join(dest, u"確かめる表.json"), od([(u"行", table_rows)]))
            shutil.copyfile(check_brief, os.path.join(dest, u"頼み.md"))
    problems = hand_problems(dest)
    rep = od([(u"出した先の folder の数", 1), (u"禁止の名の問題", len(problems))])
    if rows_n is not None:
        rep[u"確かめる表の行の数"] = rows_n
    return (6 if problems else 0), rep


# ============================================================ --through(型の席の束に便 UM2 の検査を当てる)
def type_data(chk, folder, gold, forms):
    u"""型の席の folder → (束の状態, {id: (判定, 規則の並び)}, {id: (名, 数, 罠を取った, 自信, 種類)}, 検査の結果)。
    束の状態: 無し(束の file が無い)・読めない・受理・断り。"""
    bundle_path = os.path.join(folder, u"材料_期1_A.json")
    obj, err = read_json(bundle_path) if os.path.exists(bundle_path) else (None, u"無し")
    rows = {}
    if err is None and isinstance(obj, dict) and isinstance(obj.get(u"材料"), list):
        tstate = u"読めた"
        for r in obj[u"材料"]:
            if isinstance(r, dict) and isinstance(r.get(u"id"), str) and r[u"id"] not in rows:
                rows[r[u"id"]] = r
    else:
        tstate = u"無し" if err == u"無し" else u"読めない"
    ans = fill_answers(gold, forms, tstate, rows)
    res = None
    state = tstate if tstate != u"読めた" else u"受理"
    if tstate == u"読めた" or tstate == u"読めない":
        try:
            res = chk.check_files(os.path.join(folder, u"指定.json"), os.path.join(folder, u"definition_A.json"), bundle_path, os.path.join(folder, u"期1"))
        except Exception:
            res = None
        if res is not None and isinstance(res.get(u"束"), dict) and res[u"束"].get(u"状態") == u"断り":
            state = u"断り"
    judged = {}
    if res is not None and isinstance(res.get(u"材料"), list):
        for m in res[u"材料"]:
            if isinstance(m, dict) and isinstance(m.get(u"id"), str) and m[u"id"] not in judged:
                judged[m[u"id"]] = (m.get(u"判定"), list(m.get(u"規則")) if isinstance(m.get(u"規則"), list) else [])
    return state, judged, ans, res


def type_row_judge(state, judged, ident):
    u"""→ (判定の名, 規則の並び)。"""
    if state in (u"無し", u"読めない"):
        return u"判定なし", []
    if state == u"断り":
        return u"断り", []
    j = judged.get(ident)
    if j is None or j[0] not in JUDGES:
        return u"判定なし", []
    return j[0], j[1]


def through_report(chk, root, i, co=None):
    u"""--through の出力(判定ごとの行の数・規則ごとの行の数)。co が在れば正解と照合しない(答えを読まない側)。"""
    folder = seat_dir(root, i, u"type")
    state, judged, _ans, res = type_data(chk, folder, dict((a, UNREADABLE) for a in A_IDS), None)
    rep = od([(u"束", state)])
    cnt = collections.Counter()
    rules = collections.Counter()
    for ident in A_IDS:
        j, rs = type_row_judge(state, judged, ident)
        cnt[j] += 1
        for r in rs:
            rules[r] += 1
    rep[u"判定"] = od((k, cnt.get(k, 0)) for k in JUDGES)
    rep[u"止めた規則"] = dict(sorted(rules.items()))
    if isinstance(res, dict) and isinstance(res.get(u"束"), dict):
        rep[u"束の規則"] = list(res[u"束"].get(u"規則", [])) if isinstance(res[u"束"].get(u"規則"), list) else []
    return rep, res


# ============================================================ --process(便 UM3 の数え方を写した)
def count_seat(path, folder, outs):
    u"""会話の記録 1 本 → 過程の数(封 §1-5)。tool_use が 1 つも無ければ None。``outs`` = 席が書く file の名の並び(最初が主の出力)。"""
    variants = folder_variants(folder)
    files = material_files(folder)
    names = [n for n, _s in files]
    journal = max(files, key=lambda x: (x[1], x[0]))[0] if files else None
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
            elif t == u"text" and o.get(u"type") == u"assistant" and not is_synthetic(o) and isinstance(b.get(u"text"), str) and b[u"text"].strip():
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
                per_file[m] += 1
    n[u"素材の file のうち path が出た数"] = sum(1 for v in per_file.values() if v >= 1)
    n[u"素材の file のうち 2 回以上の数"] = sum(1 for v in per_file.values() if v >= 2)
    n[u"最大の file に触れた"] = 1 if journal is not None and per_file.get(journal, 0) >= 1 else 0
    script_writes = {}
    out_w = doc_w = 0
    first_out = None
    scripts = pyruns = dirty = 0
    main_out = outs[0]
    doc_name = outs[1] if len(outs) > 1 else None
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
            for target in outs:
                if writes_name(raw, target):
                    script_writes.setdefault(os.path.basename(pth), set()).add(target)
        elif is_py_run and _PY_BODY.search(raw):
            scripts += 1
        if is_py_run:
            pyruns += 1
        for target, which in [(main_out, u"t")] + ([(doc_name, u"d")] if doc_name else []):
            hit = False
            if is_write_tool and os.path.basename(pth) == target:
                hit = True
            elif not is_write_tool and writes_name(raw, target):
                hit = True
            elif is_py_run and any(target in ts_ and sb in raw for sb, ts_ in script_writes.items()):
                hit = True
            if hit:
                if which == u"t":
                    out_w += 1
                    if first_out is None:
                        first_out = k
                else:
                    doc_w += 1
        if nm != u"SubagentHandback" and is_dirty(raw, variants):
            dirty += 1
    n[u"最初に出力を書くまでの呼び出し"] = first_out
    n[u"出力を書いた回数"] = out_w
    n[u"書き直した"] = 1 if out_w >= 2 else 0
    n[u"資料を書いた回数"] = doc_w
    n[u"script を書いた数"] = scripts
    n[u"python を走らせた数"] = pyruns
    n[u"道具が誤りを返した数"] = errors
    n[u"汚れた呼び出し"] = dirty
    n[u"汚れの席"] = 1 if dirty >= 1 else 0
    return n


OUT_NAMES = {u"fill": (u"値の表.json", u"資料.md"), u"check": (u"根拠の表.json",), u"type": (u"材料_期1_A.json",)}


def process_seat(index, folder, kind):
    u"""席の folder → 過程の数か ``過程が数えられない``(理由つき)。"""
    if index is None:
        return od([(u"状態", u"過程が数えられない"), (u"理由", u"記録の folder が無い")])
    m = index.match(folder)
    if len(m) == 0:
        return od([(u"状態", u"過程が数えられない"), (u"理由", u"記録が 0 本")])
    if len(m) >= 2:
        return od([(u"状態", u"過程が数えられない"), (u"理由", u"記録が 2 本以上"), (u"本数", len(m))])
    got = count_seat(m[0], folder, OUT_NAMES[kind.split(u"-")[0]])
    if got is None:
        return od([(u"状態", u"過程が数えられない"), (u"理由", u"tool_use が無い")])
    out = od([(u"状態", u"数えた")])
    out.update(got)
    return out


def seat_list(root, companies):
    return [(i, k, seat_dir(root, i, k)) for i in companies for k in SEAT_KINDS]


# ============================================================ --tally
BOUNDS = od([
    (u"UM4-M1", {u"直しなしで通る社": 3, u"会社の数": 4}),
    (u"UM4-F1", {u"同じの百分率": 95, u"普通の行": 168}),
    (u"UM4-F2", {u"罠を取った行": 2, u"罠の行": 32}),
    (u"UM4-F3", {u"無いのに在る": 2, u"無いの行": 24}),
    (u"UM4-F4", {u"高で数を出した行の分子": 1, u"分母": 2, u"決めの行": 16}),
    (u"UM4-F5", {u"回βも同じ答えの分子": 1, u"分母": 2, u"判定する分母の下限": 3}),
    (u"UM4-V1", {u"通した誤り": 1}),
    (u"UM4-V2", {u"通す百分率": 85}),
    (u"UM4-V3", {u"要確認": 4, u"決めの行": 8}),
    (u"UM4-V4", {u"通す": 1, u"行": 8}),
    (u"UM4-V5", {u"通す": 0, u"行": 8}),
    (u"UM4-V6", {u"通す": 0, u"行": 4}),
    (u"UM4-V7", {u"無いに異議": 3, u"行": 4}),
    (u"UM4-V8", {u"直せたの百分率": 80}),
    (u"UM4-V9", {u"状態が違う行": 10, u"行": 96}),
    (u"UM4-T1", {u"通す行": 84, u"行": 120, u"百分率": 70}),
    (u"UM4-T2", {u"通した誤り": 0}),
    (u"UM4-G1", {u"取得の差": 15}),
    (u"UM4-G2", {u"差": 1}),
    (u"UM4-P1", {u"社": 4}),
    (u"UM4-P2", {u"席": 1, u"席の数": 20}),
])


def B(pid, key):
    return BOUNDS[pid][key]


def metric_counts(items):
    u"""items = [(結果の名, 種類, 通したか)] → 5 つの数。"""
    m = collections.Counter()
    for name, kind, passed in items:
        if name in SAME_NAMES and kind != u"決め":
            m[u"取得" if passed else u"止めすぎ"] += 1
        if name in WRONG_NAMES:
            m[u"通した誤り" if passed else u"通さなかった誤り"] += 1
        if kind == u"決め" and passed:
            m[u"決めを通した"] += 1
    return m


def gold_digest(co, root, companies):
    u"""読んだ正解・席の出力の sha256 の束ね(相対の名と sha256 の並びを sha256 したもの)と、読んだ file の数。"""
    entries = []
    for i in companies:
        for rel in SPEC_FILES:
            h = sha256_file(os.path.join(co, str(i), *rel.split(u"/")))
            if h is not None:
                entries.append(u"co\t%s/%s\t%s\n" % (i, rel, h))
        for k in SEAT_KINDS:
            for name in (u"値の表.json", u"確かめる表.json", u"根拠の表.json", u"材料_期1_A.json"):
                h = sha256_file(os.path.join(seat_dir(root, i, k), name))
                if h is not None:
                    entries.append(u"seat\t%s/%s/%s\t%s\n" % (i, k, name, h))
    return hashlib.sha256(u"".join(sorted(entries)).encode("utf-8")).hexdigest(), len(entries)


def seat_row(proc):
    row = od([(u"数えた", 1 if proc[u"状態"] == u"数えた" else 0)])
    for k, v in proc.items():
        if k in (u"状態", u"理由", u"道具の名ごと"):
            continue
        if v is None:
            row[k + u"が無い"] = 1
        elif isinstance(v, int):
            row[k] = v
    return row


def tally_company(c, pc, i, co, root, index, chk, first_ng, rows_out=None):
    u"""会社 ``i`` を数える。``c``・``pc`` は Counter。``rows_out`` が dict なら行ごとの表を入れる(digest 用。記録には入れない)。"""
    def bump(key, n=1):
        c[key] += n
        pc[key] += n

    cdir = os.path.join(co, str(i))
    rules = material_rules(cdir)
    ok = all(rules.values())
    bump(u"素材:社の数")
    bump(u"素材:形の検査に通った社" if ok else u"素材:形の検査に通らなかった社")
    if i in first_ng:
        bump(u"素材:最初に落ちた社")
    if ok and i not in first_ng:
        bump(u"素材:直しなしで通った社")
    for k, v in rules.items():
        if not v:
            bump(u"素材:規則 NG:" + k)
    gold = read_gold1(os.path.join(cdir, u"正解", u"正解.json"))
    if gold is None:
        bump(u"正解が読めない社")
        return
    forms = read_forms(os.path.join(cdir, u"正解", u"罠.json"))
    if forms is None:
        bump(u"罠の file が読めない社")
    kinds = row_kinds(gold, forms)
    for ident, k in kinds.items():
        if gold[ident] is UNREADABLE:
            bump(u"正解が読めない行")
        else:
            bump(u"行の種類:" + k)
    # ---------------- 段 1: 埋める席
    answers = {}
    for r in ROUNDS:
        tstate, rows, dup = read_table(os.path.join(seat_dir(root, i, u"fill-" + r), u"値の表.json"))
        bump(u"埋め:回%s:表:%s" % (r, tstate))
        bump(u"埋め:回%s:表:重複の行" % r, dup)
        ans = fill_answers(gold, forms, tstate, rows)
        answers[r] = (ans, tstate, rows)
        for ident, (name, n, trapped, conf, kind) in ans.items():
            bump(u"埋め:回%s:%s:行の数" % (r, kind))
            bump(u"埋め:回%s:%s:%s" % (r, kind, name))
            if trapped:
                bump(u"埋め:回%s:罠を取った" % r)
            if kind == u"決め" and conf == u"高" and name in (u"決め:1つ目", u"決め:2つ目", u"決め:どちらでもない"):
                bump(u"埋め:回%s:決め:自信高で数を出した" % r)
    a_ans, a_state, a_rows = answers[u"a"]
    b_ans = answers[u"b"][0]
    for ident, (na, nn, _t, _cf, kind) in a_ans.items():
        if ident not in b_ans:
            continue
        nb, mm = b_ans[ident][0], b_ans[ident][1]
        bump(u"埋め:揺れ:行の数")
        if na == nb:
            bump(u"埋め:揺れ:結果の名が同じ")
        if nn is not None and mm is not None:
            bump(u"埋め:揺れ:在るどうし")
            if nn == mm:
                bump(u"埋め:揺れ:在るどうしで数が同じ")
        if kind != u"決め" and na in WRONG_NAMES:
            bump(u"埋め:揺れ:回αが違った行")
            if na == nb and (na == u"無いで違う" or nn == mm):
                bump(u"埋め:揺れ:回αが違った行のうち回βも同じ答え")
    # ---------------- 段 2: 確かめる席
    src = None
    statuses = {}
    changes, not_made = [], dict(MUT_EXPECT)
    if a_state == u"読めた":
        changes, not_made = make_broken(a_rows, gold, forms)
    orig_fallback = given_table_rows(a_rows) if a_state == u"読めた" else []
    broken_fallback = broken_table_rows(a_rows, changes) if a_state == u"読めた" else []
    if chk is not None:
        src = chk.Source(os.path.join(cdir, u"期1"))
        for which, fb in ((u"orig", orig_fallback), (u"broken", broken_fallback)):
            folder = seat_dir(root, i, u"check-" + which)
            ostate, orows, odup = read_table(os.path.join(folder, u"根拠の表.json"))
            bump(u"確かめ:%s:表:%s" % (which, ostate))
            bump(u"確かめ:%s:表:重複の行" % which, odup)
            given = given_rows_of(folder, fb)
            statuses[which] = (status_rows(chk, src, given, ostate, orows, gold), orows)
    else:
        bump(u"検査が読めない社")
    fill_items, orig_items = [], []
    if u"orig" in statuses:
        st = statuses[u"orig"][0]
        for ident, (name, _n, _t, _cf, kind) in a_ans.items():
            fill_items.append((name, kind, True))
            if ident not in st:
                continue
            status = st[ident][0]
            passed = status in PASS_STATUSES
            orig_items.append((name, kind, passed))
            bump(u"原:行の数")
            bump(u"原:%s×%s" % (name, status))
            bump(u"原:状態:" + status)
            if kind == u"決め":
                bump(u"原:決め:状態:" + status)
            if passed:
                bump(u"原:通した")
        m = metric_counts(orig_items)
        for k in METRICS:
            bump(u"並べる:埋め+確かめ:" + k, m.get(k, 0))
        bump(u"原:同じの行", m.get(u"取得", 0) + m.get(u"止めすぎ", 0))
        bump(u"原:誤りの行", m.get(u"通した誤り", 0) + m.get(u"通さなかった誤り", 0))
        bump(u"原:決めの行", sum(1 for x in orig_items if x[1] == u"決め"))
        m0 = metric_counts(fill_items)
        for k in METRICS:
            bump(u"並べる:埋めのみ:" + k, m0.get(k, 0))
    if u"broken" in statuses and u"orig" in statuses:
        stb = statuses[u"broken"][0]
        sto = statuses[u"orig"][0]
        orows_b = statuses[u"broken"][1]
        changed_ids = set(x[u"id"] for x in changes)
        for k in MUT_KINDS:
            bump(u"壊:作れなかった:" + k, not_made.get(k, 0))
        bump(u"壊:作れなかった数", sum(not_made.values()))
        for ch in changes:
            k = ch[u"種類"]
            bump(u"壊:%s:作った" % k)
            if ch[u"外した"]:
                bump(u"壊:%s:外した" % k)
                continue
            if ch[u"id"] not in stb:
                continue
            status, fix = stb[ch[u"id"]]
            bump(u"壊:%s:行の数" % k)
            bump(u"壊:%s:状態:%s" % (k, status))
            bump(u"壊:%s:%s" % (k, u"通した" if status in PASS_STATUSES else u"通さなかった"))
            if fix is not None:
                bump(u"壊:%s:%s" % (k, fix))
        for ident, (status, _f) in stb.items():
            if ident in changed_ids:
                continue
            bump(u"壊:壊していない行")
            if sto.get(ident, (None,))[0] != status:
                bump(u"壊:壊していない行で状態が違う")
    # ---------------- 型の席 + 検査
    if chk is not None:
        state, judged, t_ans, _res = type_data(chk, seat_dir(root, i, u"type"), gold, forms)
        bump(u"型:束:" + state)
        if state == u"断り":
            bump(u"型:束ごとの断り")
        t_items = []
        for ident, (name, _n, trapped, _cf, kind) in t_ans.items():
            j, rs = type_row_judge(state, judged, ident)
            passed = j in JUDGE_PASS
            t_items.append((name, kind, passed))
            bump(u"型:行の数")
            bump(u"型:判定:" + j)
            for r_ in rs:
                bump(u"型:止める:" + r_)
            bump(u"型:%s×%s" % (name, j))
            if trapped:
                bump(u"型:罠を取った×" + j)
            if passed:
                bump(u"型:通した")
        mt = metric_counts(t_items)
        for k in METRICS:
            bump(u"並べる:型+検査:" + k, mt.get(k, 0))
    # ---------------- 過程
    procs = od()
    for kind in SEAT_KINDS:
        proc = process_seat(index, seat_dir(root, i, kind), kind)
        procs[kind] = proc
        lab = SEAT_LABEL[kind]
        bump(u"過程:席の数")
        bump(u"過程:%s:席の数" % lab)
        if proc[u"状態"] != u"数えた":
            bump(u"過程:数えられない席")
            bump(u"過程:%s:数えられない席" % lab)
            continue
        bump(u"過程:数えた席")
        for key in (u"汚れの席", u"汚れた呼び出し", u"道具が誤りを返した数", u"python を走らせた数", u"script を書いた数", u"書き直した"):
            bump(u"過程:" + key, proc[key])
        bump(u"過程:%s:道具の呼び出しの数" % lab, proc[u"道具の呼び出し"])
        bump(u"過程:%s:汚れの席" % lab, proc[u"汚れの席"])
        if proc[u"秒"] is None:
            bump(u"過程:秒が無い席")
        else:
            bump(u"過程:秒の合計", proc[u"秒"])
    for label, kinds_ in ((u"埋め+確かめ", (u"fill-a", u"check-orig")), (u"型", (u"type",))):
        ps = [procs[k] for k in kinds_]
        if all(p[u"状態"] == u"数えた" for p in ps):
            bump(u"P1:%s:数えた" % label)
            bump(u"P1:%s:道具の呼び出し" % label, sum(p[u"道具の呼び出し"] for p in ps))
            bump(u"過程:作り方:%s:道具の呼び出し" % label, sum(p[u"道具の呼び出し"] for p in ps))
            bump(u"過程:作り方:%s:汚れた呼び出し" % label, sum(p[u"汚れた呼び出し"] for p in ps))
            secs = [p[u"秒"] for p in ps]
            if all(s is not None for s in secs):
                bump(u"過程:作り方:%s:秒の合計" % label, sum(secs))
        else:
            bump(u"P1:%s:数えられない" % label)
    if rows_out is not None:
        rows_out[i] = od([(u"種類", kinds), (u"回α", a_ans), (u"原", statuses.get(u"orig", (od(), None))[0]),
                          (u"壊", statuses.get(u"broken", (od(), None))[0]), (u"変えた行", changes),
                          (u"型", None if chk is None else type_data(chk, seat_dir(root, i, u"type"), gold, forms)[:3]), (u"gold", gold)])


def fixed_counts():
    out = [u"読んだ file の数", u"素材:社の数", u"素材:形の検査に通った社", u"素材:形の検査に通らなかった社", u"素材:最初に落ちた社", u"素材:直しなしで通った社",
           u"正解が読めない社", u"罠の file が読めない社", u"正解が読めない行", u"検査が読めない社"]
    out += [u"行の種類:" + k for k in KINDS]
    for r in ROUNDS:
        out += [u"埋め:回%s:表:%s" % (r, t) for t in (u"無し", u"読めない", u"読めた", u"重複の行")]
        out += [u"埋め:回%s:%s:行の数" % (r, k) for k in KINDS]
        out += [u"埋め:回%s:%s:%s" % (r, k, n) for k in KINDS for n in (ALL_NAMES if k == u"決め" else RESULT_NAMES)]
        out += [u"埋め:回%s:罠を取った" % r, u"埋め:回%s:決め:自信高で数を出した" % r]
    out += [u"埋め:揺れ:" + k for k in (u"行の数", u"結果の名が同じ", u"在るどうし", u"在るどうしで数が同じ", u"回αが違った行", u"回αが違った行のうち回βも同じ答え")]
    for w in (u"orig", u"broken"):
        out += [u"確かめ:%s:表:%s" % (w, t) for t in (u"無し", u"読めない", u"読めた", u"重複の行")]
    out += [u"原:行の数", u"原:通した", u"原:同じの行", u"原:誤りの行", u"原:決めの行"]
    out += [u"原:状態:" + s for s in STATUS_NAMES] + [u"原:決め:状態:" + s for s in STATUS_NAMES]
    out += [u"原:%s×%s" % (n, s) for n in ALL_NAMES for s in STATUS_NAMES]
    for k in MUT_KINDS:
        out += [u"壊:%s:%s" % (k, w) for w in (u"作った", u"外した", u"行の数", u"通した", u"通さなかった", u"直せた", u"直しが違う", u"直しなし")]
        out += [u"壊:%s:状態:%s" % (k, s) for s in STATUS_NAMES]
        out.append(u"壊:作れなかった:" + k)
    out += [u"壊:作れなかった数", u"壊:壊していない行", u"壊:壊していない行で状態が違う"]
    out += [u"型:束:" + s for s in (u"無し", u"読めない", u"受理", u"断り")] + [u"型:束ごとの断り", u"型:行の数", u"型:通した"]
    out += [u"型:判定:" + j for j in JUDGES] + [u"型:止める:" + r for r in RULE_NAMES] + [u"型:罠を取った×" + j for j in JUDGES]
    out += [u"型:%s×%s" % (n, j) for n in ALL_NAMES for j in JUDGES]
    out += [u"並べる:%s:%s" % (m, k) for m in METHODS for k in METRICS]
    out += [u"過程:席の数", u"過程:数えた席", u"過程:数えられない席", u"過程:汚れの席", u"過程:汚れた呼び出し", u"過程:道具が誤りを返した数",
            u"過程:python を走らせた数", u"過程:script を書いた数", u"過程:書き直した", u"過程:秒が無い席", u"過程:秒の合計"]
    for k in SEAT_KINDS:
        lab = SEAT_LABEL[k]
        out += [u"過程:%s:%s" % (lab, w) for w in (u"席の数", u"数えられない席", u"道具の呼び出しの数", u"汚れの席")]
    for label in (u"埋め+確かめ", u"型"):
        out += [u"P1:%s:数えた" % label, u"P1:%s:数えられない" % label, u"P1:%s:道具の呼び出し" % label,
                u"過程:作り方:%s:道具の呼び出し" % label, u"過程:作り方:%s:汚れた呼び出し" % label, u"過程:作り方:%s:秒の合計" % label]
    return tuple(out)


FIXED_COUNTS = fixed_counts()

#: 記録の「限界」(数だけの決まりに触れない字)
LIMITS = (
    u"機械が計算し直すのは確かめる席の出どころの数だけ。出どころが項目の意味・期・範囲に合うかは機械では見ていない(確かめる席の見立てに任せている)",
    u"汚れ・書き込み・script の数えは便 UM3 と同じ数え方で、取りこぼす形と数え過ぎる形が両方在る。汚れた席は下限とは言えない",
    u"過程の秒は会話の記録の最初と最後の時刻の差。時刻が無い席は秒が無い",
    u"型の席の判定は便 UM2 の 1 期目の形(人が見出しの表に足す段は無し)。表の行の和の材料は取り方が未確認のまま通す側に数えない",
    u"壊した表の数は司令塔が決めた 5 種類の壊し方に対する数で、席が自分で作る誤りに対する数ではない",
    u"素材の中身(罠が紛らわしいか・無いが本当に出せないか・正解が素材と合うか)は機械では見ていない",
    u"最初の形の検査で落ちた社は、司令塔が渡した番号だけを数える(script は最初の検査の結果を知らない)",
    u"表示の倍率が 0 や負の整数でも、出どころの計算はそのまま受ける(封が範囲を決めていない)",
    u"素材の形の検査は罠の file が symlink なら NG にする(封の字に無い厳しい側の読み)。path の途中の folder の symlink は見ない",
)
FIELD_NOTES = (
    (u"過程:汚れの席", u"汚れた席は取りこぼしと数え過ぎの両方が在る(限界の欄を見る)"),
    (u"過程:汚れた呼び出し", u"汚れた呼び出しは取りこぼしと数え過ぎの両方が在る(限界の欄を見る)"),
    (u"素材:直しなしで通った社", u"最初の検査で落ちた社として渡された番号に無い社のうち、いまの検査に通った社"),
)


def tally(companies, co, root, tdir, first_ng=(), rows_out=None, excluded=0):
    c = collections.Counter()
    per_company = od()
    index = Transcripts(tdir) if tdir and os.path.isdir(tdir) else None
    try:
        chk = load_check_module()
    except Exception:
        chk = None
    for i in companies:
        pc = per_company.setdefault(str(i), collections.Counter())
        tally_company(c, pc, i, co, root, index, chk, set(first_ng), rows_out)
    sha, nfiles = gold_digest(co, root, companies)
    c[u"読んだ file の数"] = nfiles
    for k in FIXED_COUNTS:
        c.setdefault(k, 0)
    seats = od()
    for i in companies:
        for kind in SEAT_KINDS:
            proc = process_seat(index, seat_dir(root, i, kind), kind)
            seats[u"%s:%s" % (i, SEAT_LABEL[kind])] = seat_row(proc)
    rec = od([(u"会社の数", len(list(companies))), (u"外した社の数", excluded), (u"数", dict(sorted(c.items()))),
              (u"会社ごと", od((k, dict(sorted(v.items()))) for k, v in per_company.items())),
              (u"席ごと", seats), (u"読んだ file の sha256 の束ね", sha)])
    rec[u"限界"] = list(LIMITS)
    rec[u"欄の説明"] = od(FIELD_NOTES)
    rec[u"予測"] = judge(rec)
    return rec


def judge(rec):
    u"""記録の ``数`` から封 §2 の 21 本の当たり外れを境の数で決める。``当たり`` は True・False・None(判定できない)。
    人数・本数の境は数のまま、割合の境は割合で当てる。対象の行が 1 つも無い時は None。"""
    c = rec.get(u"数", {})
    out = od()

    def g(k):
        v = c.get(k, 0)
        return v if is_int(v) else 0

    def put(key, ok, **detail):
        out[key] = od([(u"当たり", ok)] + list(detail.items()))

    def both(fmt):
        return sum(g(fmt % r) for r in ROUNDS)

    n_co = rec.get(u"会社の数", 0) if is_int(rec.get(u"会社の数")) else 0
    put(u"UM4-M1", None if n_co == 0 else g(u"素材:直しなしで通った社") >= B(u"UM4-M1", u"直しなしで通る社"), 社=g(u"素材:直しなしで通った社"), 会社の数=n_co)
    x, y = both(u"埋め:回%s:普通:同じ"), both(u"埋め:回%s:普通:行の数")
    put(u"UM4-F1", None if y == 0 else 100 * x >= B(u"UM4-F1", u"同じの百分率") * y, 同じ=x, 普通の行=y)
    x, y = both(u"埋め:回%s:罠を取った"), both(u"埋め:回%s:罠:行の数")
    put(u"UM4-F2", None if y == 0 else x >= B(u"UM4-F2", u"罠を取った行"), 罠を取った=x, 罠の行=y)
    x, y = both(u"埋め:回%s:無い:無いのに在る"), both(u"埋め:回%s:無い:行の数")
    put(u"UM4-F3", None if y == 0 else x >= B(u"UM4-F3", u"無いのに在る"), 無いのに在る=x, 無いの行=y)
    x, y = both(u"埋め:回%s:決め:自信高で数を出した"), both(u"埋め:回%s:決め:行の数")
    put(u"UM4-F4", None if y == 0 else B(u"UM4-F4", u"分母") * x >= y, 高で数を出した=x, 決めの行=y)
    x, y = g(u"埋め:揺れ:回αが違った行のうち回βも同じ答え"), g(u"埋め:揺れ:回αが違った行")
    put(u"UM4-F5", None if y < B(u"UM4-F5", u"判定する分母の下限") else B(u"UM4-F5", u"分母") * x >= y, 回βも同じ=x, 回αが違った行=y)
    x, y = g(u"並べる:埋め+確かめ:通した誤り") , g(u"原:誤りの行")
    put(u"UM4-V1", None if y == 0 else x >= B(u"UM4-V1", u"通した誤り"), 通した誤り=x, 回αが違った行=y)
    x, y = g(u"並べる:埋め+確かめ:取得"), g(u"原:同じの行")
    put(u"UM4-V2", None if y == 0 else 100 * x >= B(u"UM4-V2", u"通す百分率") * y, 通す=x, 同じの行=y)
    x, y = g(u"原:決め:状態:" + S_REVIEW), g(u"原:決めの行")
    put(u"UM4-V3", None if y == 0 else x >= B(u"UM4-V3", u"要確認"), 要確認=x, 決めの行=y)
    y = g(u"壊:罠の値:行の数")
    x = g(u"壊:罠の値:通した")
    put(u"UM4-V4", None if y == 0 else x >= B(u"UM4-V4", u"通す"), 通す=x, 行=y)
    y = g(u"壊:桁:行の数") + g(u"壊:隣:行の数")
    x = g(u"壊:桁:通した") + g(u"壊:隣:通した")
    put(u"UM4-V5", None if y == 0 else x == B(u"UM4-V5", u"通す"), 通す=x, 行=y)
    y, x = g(u"壊:無いのに在る:行の数"), g(u"壊:無いのに在る:通した")
    put(u"UM4-V6", None if y == 0 else x == B(u"UM4-V6", u"通す"), 通す=x, 行=y)
    y, x = g(u"壊:在るのに無い:行の数"), g(u"壊:在るのに無い:状態:" + S_NONE_OBJ)
    put(u"UM4-V7", None if y == 0 else x >= B(u"UM4-V7", u"無いに異議"), 無いに異議=x, 行=y)
    den = sum(g(u"壊:%s:状態:%s" % (k, s)) for k in MUT_KINDS for s in (S_MISMATCH, S_NONE_OBJ))
    x = sum(g(u"壊:%s:直せた" % k) for k in MUT_KINDS)
    put(u"UM4-V8", None if den == 0 else 100 * x >= B(u"UM4-V8", u"直せたの百分率") * den, 直せた=x, 不一致と異議=den)
    y, x = g(u"壊:壊していない行"), g(u"壊:壊していない行で状態が違う")
    put(u"UM4-V9", None if y == 0 else x <= B(u"UM4-V9", u"状態が違う行"), 状態が違う行=x, 行=y)
    y, x = g(u"型:行の数"), g(u"型:通した")
    put(u"UM4-T1", None if y == 0 else 100 * x <= B(u"UM4-T1", u"百分率") * y, 通す行=x, 行=y)
    x = g(u"並べる:型+検査:通した誤り")
    put(u"UM4-T2", None if g(u"型:行の数") == 0 else x == B(u"UM4-T2", u"通した誤り"), 通した誤り=x)
    ready = g(u"型:行の数") > 0 and g(u"原:行の数") > 0
    d = g(u"並べる:埋め+確かめ:取得") - g(u"並べる:型+検査:取得")
    put(u"UM4-G1", None if not ready else d >= B(u"UM4-G1", u"取得の差"), 取得の差=d)
    fv = g(u"並べる:埋め+確かめ:通した誤り") + g(u"並べる:埋め+確かめ:決めを通した")
    tv = g(u"並べる:型+検査:通した誤り") + g(u"並べる:型+検査:決めを通した")
    put(u"UM4-G2", None if not ready else fv > tv, 埋め確かめ=fv, 型検査=tv)
    # P1: 社ごと(会社ごと の欄を読む)
    pcs = rec.get(u"会社ごと", {}) if isinstance(rec.get(u"会社ごと"), dict) else {}
    viol = False
    counted = 0
    for v in pcs.values():
        if not isinstance(v, dict):
            continue
        if v.get(u"P1:埋め+確かめ:数えた", 0) >= 1 and v.get(u"P1:型:数えた", 0) >= 1:
            counted += 1
            if not v.get(u"P1:埋め+確かめ:道具の呼び出し", 0) > v.get(u"P1:型:道具の呼び出し", 0):
                viol = True
    ok = False if viol else (True if (counted == n_co and n_co > 0) else None)
    put(u"UM4-P1", ok, 数えた社=counted, 会社の数=n_co)
    dirty, seats, unc = g(u"過程:汚れの席"), g(u"過程:席の数"), g(u"過程:数えられない席")
    ok = True if dirty >= B(u"UM4-P2", u"席") else (False if (unc == 0 and seats > 0) else None)
    put(u"UM4-P2", ok, 席=dirty, 席の数=seats, 数えられない席=unc)
    return out


# ============================================================ --digest
def digest_one(path, folder, name, outs):
    u"""会話の記録 1 本 + 席の folder → markdown(司令塔が 1 行ずつ読むための抜き書き)。"""
    out = [u"# 抜き書き: " + name, u"", u"## 道具の呼び出しの順(道具の名・入力の頭 300 字)"]
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
                try:
                    s = json.dumps(b.get(u"input"), ensure_ascii=False)
                except (TypeError, ValueError):
                    s = repr(b.get(u"input"))
                out.append(u"%d. %s `%s`" % (k, b.get(u"name"), s[:300].replace(u"\n", u" ")))
            elif b.get(u"type") == u"text" and o.get(u"type") == u"assistant" and isinstance(b.get(u"text"), str) and b[u"text"].strip():
                texts.append(b[u"text"])
    out += [u"", u"## 席の発言", u""]
    for t in texts:
        out += [t, u""]
    note, err = read_text(os.path.join(folder, u"作業の記録.md"))
    out += [u"## 作業の記録", u"", note if err is None else u"(無い)", u"", u"## 出力の行(出どころ・見立て・自信・注)", u""]
    tstate, rows, _d = read_table(os.path.join(folder, outs[0]))
    if tstate != u"読めた":
        out.append(u"(出力が%s)" % tstate)
    for ident, row in rows.items():
        out.append(u"- %s | %s | %s | %s | %s" % (ident, row.get(u"状態", row.get(u"見立て")), row.get(u"自信"), row.get(u"出どころ"), row.get(u"注")))
    return u"\n".join(out) + u"\n"


def rows_digest(i, info):
    u"""会社 1 社の行の読み(正解を含む。司令塔が本番の席が終わった後に読む)。"""
    out = [u"# 行の読み: 社 %s" % i, u"", u"| id | 種類 | 回α | 数 | 正解 | 原の状態 | 壊した表の状態 | 型の判定 |", u"| --- | --- | --- | --- | --- | --- | --- | --- |"]
    changed = dict((x[u"id"], x[u"種類"]) for x in info[u"変えた行"])
    t = info[u"型"]
    for ident in A_IDS:
        g = info[u"gold"].get(ident)
        a = info[u"回α"].get(ident)
        so = info[u"原"].get(ident)
        sb = info[u"壊"].get(ident)
        tj = type_row_judge(t[0], t[1], ident)[0] if t else u"-"
        out.append(u"| %s | %s | %s | %s | %s | %s | %s%s | %s |" % (
            ident, info[u"種類"].get(ident), a[0] if a else u"-", a[1] if a else u"-", u"?" if g is UNREADABLE else g,
            so[0] if so else u"-", sb[0] if sb else u"-", u"(壊した: %s)" % changed[ident] if ident in changed else u"", tj))
    return u"\n".join(out) + u"\n"


def digest(opt):
    if "--root" not in opt or "--transcripts" not in opt or "--out-dir" not in opt or "--co" not in opt:
        return 2, od([(u"誤り", u"命令の形")])
    index = Transcripts(opt["--transcripts"])
    companies = [int(x) for x in opt.get("--companies", [str(i) for i in DEV])]
    made = skipped = 0
    os.makedirs(opt["--out-dir"], exist_ok=True)
    for i, kind, f in seat_list(opt["--root"], companies):
        m = index.match(f)
        if len(m) != 1 or not os.path.isdir(f):
            skipped += 1
            continue
        outs = OUT_NAMES[kind.split(u"-")[0]]
        with io.open(os.path.join(opt["--out-dir"], u"%s_%s.md" % (i, SEAT_LABEL[kind])), "w", encoding="utf-8") as fh:
            fh.write(digest_one(m[0], f, u"%s_%s" % (i, SEAT_LABEL[kind]), outs))
        made += 1
    info = {}
    try:
        chk = load_check_module()
    except Exception:
        chk = None
    scratch = collections.Counter()
    for i in companies:
        tally_company(scratch, collections.Counter(), i, opt["--co"], opt["--root"], index, chk, set(), info)
        if i in info:
            with io.open(os.path.join(opt["--out-dir"], u"行の読み_%s.md" % i), "w", encoding="utf-8") as fh:
                fh.write(rows_digest(i, info[i]))
            made += 1
    return 0, od([(u"書いた数", made), (u"書かなかった数", skipped)])


# ============================================================ 命令
def _alpha_rows(root, i):
    st, rows, _d = read_table(os.path.join(seat_dir(root, i, u"fill-a"), u"値の表.json"))
    return st, rows


def mutate_command(opt):
    if any(k not in opt for k in ("--co", "--root", "--company")):
        return 2, od([(u"誤り", u"命令の形")])
    try:
        i = int(opt["--company"])
    except ValueError:
        return 2, od([(u"誤り", u"社の番号が整数でない")])
    cdir = os.path.join(opt["--co"], str(i))
    gold = read_gold1(os.path.join(cdir, u"正解", u"正解.json"))
    forms = read_forms(os.path.join(cdir, u"正解", u"罠.json"))
    st, rows = _alpha_rows(opt["--root"], i)
    changes, not_made = ([], dict(MUT_EXPECT))
    if gold is not None and st == u"読めた":
        changes, not_made = make_broken(rows, gold, forms)
    out = opt.get("--changes-out", os.path.join(opt["--root"], str(i), u"壊し方_表.json"))
    write_json(out, od([(u"変えた行", changes)]))
    return 0, mutate_report(changes, not_made)


def status_command(opt):
    if any(k not in opt for k in ("--co", "--root", "--company", "--which")) or opt["--which"] not in (u"orig", u"broken"):
        return 2, od([(u"誤り", u"命令の形")])
    try:
        i = int(opt["--company"])
    except ValueError:
        return 2, od([(u"誤り", u"社の番号が整数でない")])
    which = opt["--which"]
    cdir = os.path.join(opt["--co"], str(i))
    gold = read_gold1(os.path.join(cdir, u"正解", u"正解.json"))
    if gold is None:
        return 4, od([(u"誤り", u"正解が読めない")])
    forms = read_forms(os.path.join(cdir, u"正解", u"罠.json"))
    ast, arows = _alpha_rows(opt["--root"], i)
    changes = make_broken(arows, gold, forms)[0] if ast == u"読めた" else []
    fb = (given_table_rows(arows) if which == u"orig" else broken_table_rows(arows, changes)) if ast == u"読めた" else []
    chk = load_check_module()
    folder = seat_dir(opt["--root"], i, u"check-" + which)
    ostate, orows, _dup = read_table(os.path.join(folder, u"根拠の表.json"))
    given = given_rows_of(folder, fb)
    st = status_rows(chk, chk.Source(os.path.join(cdir, u"期1")), given, ostate, orows, gold)
    cnt = collections.Counter(s for s, _f in st.values())
    fixes = collections.Counter(f for _s, f in st.values() if f is not None)
    rep = od([(u"根拠の表", ostate), (u"行の数", len(st)), (u"状態", od((s, cnt.get(s, 0)) for s in STATUS_NAMES)),
              (u"直し", od((k, fixes.get(k, 0)) for k in (u"直せた", u"直しが違う", u"直しなし")))])
    if "--rows-out" in opt:
        write_json(opt["--rows-out"], od((ident, od([(u"状態", s), (u"直し", f)])) for ident, (s, f) in st.items()))
    # 段 3: 回 α の資料の写しの末尾に、行ごとの状態の表(資料の中の文は直さない)
    doc, derr = read_text(os.path.join(seat_dir(opt["--root"], i, u"fill-a"), u"資料.md"))
    names = {}
    defobj, _e = read_json(opt.get("--definition", os.path.join(ROOT, DEFS_REL)))
    if isinstance(defobj, dict) and isinstance(defobj.get(u"行"), list):
        for r in defobj[u"行"]:
            if isinstance(r, dict) and isinstance(r.get(u"id"), str):
                names[r[u"id"]] = r.get(u"名")
    body = (doc if derr is None else u"") .rstrip(u"\n") + u"\n\n## 確かめの状態\n\n| id | 項目 | 状態 |\n| --- | --- | --- |\n"
    for ident, (s, _f) in st.items():
        body += u"| %s | %s | %s |\n" % (ident, names.get(ident, u""), s)
    path = opt.get("--doc-out", os.path.join(opt["--root"], str(i), u"段3_%s.md" % which))
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    return 0, rep


def through_command(opt):
    if "--root" not in opt or "--company" not in opt:
        return 2, od([(u"誤り", u"命令の形")])
    try:
        i = int(opt["--company"])
    except ValueError:
        return 2, od([(u"誤り", u"社の番号が整数でない")])
    chk = load_check_module()
    rep, res = through_report(chk, opt["--root"], i)
    if res is not None:
        write_json(os.path.join(opt["--root"], str(i), u"判定_型.json"), res)
    return 0, rep


def parse(argv):
    multi = ("--companies", "--rounds", "--folder", "--material-first-ng", "--exclude")
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


COMMANDS = ("--material", "--hand", "--mutate", "--status", "--through", "--process", "--tally", "--digest")


def _main(argv):
    opt, flags = parse(argv)
    cmds = [f for f in flags if f in COMMANDS] + [k for k in opt if k == "--material"]
    if len(cmds) != 1:
        print(u"命令の形", file=sys.stderr)
        return 2
    cmd = cmds[0]
    try:
        companies = [int(x) for x in opt.get("--companies", [str(i) for i in DEV])]
        first_ng = [int(x) for x in opt.get("--material-first-ng", [])]
        exclude = set(int(x) for x in opt.get("--exclude", []))
    except ValueError:
        print(u"社の番号が整数でない", file=sys.stderr)
        return 2
    if cmd == "--material":
        if "--material" not in opt:
            print(u"命令の形", file=sys.stderr)
            return 2
        emit(material_report(opt["--material"]), opt.get("--out"))
        return 0
    if cmd in ("--hand", "--mutate", "--status", "--through"):
        fn = {"--hand": hand, "--mutate": mutate_command, "--status": status_command, "--through": through_command}[cmd]
        rc, rep = fn(opt)
        emit(rep, opt.get("--out") if cmd in ("--mutate", "--status", "--through") else None)
        return rc
    if cmd == "--digest":
        opt2 = dict(opt)
        opt2["--companies"] = [str(i) for i in companies]
        rc, rep = digest(opt2)
        emit(rep, None)
        return rc
    if cmd == "--process":
        index = Transcripts(opt["--transcripts"]) if "--transcripts" in opt and os.path.isdir(opt["--transcripts"]) else None
        folders = [(f, u"fill") for f in opt.get("--folder", [])]
        if "--root" in opt:
            folders += [(f, k) for _i, k, f in seat_list(opt["--root"], companies)]
        res = od((f, process_seat(index, f, k)) for f, k in folders)
        emit(res, opt.get("--out"))
        return 0
    # --tally
    if "--co" not in opt or "--root" not in opt:
        print(u"命令の形", file=sys.stderr)
        return 2
    if "--record" in flags:
        if not exclude <= set(PROD):
            print(u"外す社は本番の 4 社(5〜8)の中から", file=sys.stderr)
            return 2
        counted = [i for i in PROD if i not in exclude]
        for i in counted:
            if not os.path.isdir(os.path.join(opt["--co"], str(i))) or not os.path.isdir(os.path.join(opt["--root"], str(i))):
                print(u"本番の 4 社(5〜8)のうち外していない社がそろっていないので記録は書かない", file=sys.stderr)
                return 2
        if not counted:
            print(u"数える社が無い", file=sys.stderr)
            return 2
        res = tally(counted, opt["--co"], opt["--root"], opt.get("--transcripts"), first_ng, None, len(PROD) - len(counted))
        out = opt.get("--out", os.path.join(ROOT, RECORD_REL))
    else:
        counted = [i for i in companies if i not in exclude]
        res = tally(counted, opt["--co"], opt["--root"], opt.get("--transcripts"), first_ng, None, len(companies) - len(counted))
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
