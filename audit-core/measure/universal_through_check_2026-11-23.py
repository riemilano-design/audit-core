# -*- coding: utf-8 -*-
u"""封 docs/UNIVERSAL_THROUGH_SEAL_2026-11-23.md(便 UM2)の「確かめる側」。**答えを読まない側。**

素材を作る側・答えを知っている側(``universal_through_tally_2026-11-23.py``)を import しない。読むのは指定・定義表・材料の束・素材の folder・置き場・資料・
(2 期目だけ)1 期目の置き場・1 期目の素材の folder・印の file だけ。**正解の file は開かない。**
使う library は標準だけ(xlsx は zipfile と xml で読む。``python3 -I`` で動く)。**どんな入力でも例外で落ちず、rc 0 で結果の JSON を返す。**
便 UM0 の検査 ``universal_check_2026-11-23.py`` は import せず、要る所を写して持つ(前の便の file は 0 行)。

    python3 -I universal_through_check_2026-11-23.py material --spec <指定.json> --def <定義表> --bundle <束> --src <素材の folder> [--ids a01,a02]
                                                      [--confirmed <印の file>] [--prev-src <1 期目の素材の folder>] [--form-only] [--out <file>]
    python3 -I universal_through_check_2026-11-23.py store    --def <定義表> --result <material の結果> --bundle <束> --product A [--prior <置き場>] [--ids ..] [--waiting <carry の結果>] --out <file>
    python3 -I universal_through_check_2026-11-23.py plan     --def <定義表 B> --store <置き場> --out <file>
    python3 -I universal_through_check_2026-11-23.py render   --def <定義表> --store <置き場> --out <markdown>
    python3 -I universal_through_check_2026-11-23.py document --def <定義表> --store <置き場> --doc <markdown> --out <file>
    python3 -I universal_through_check_2026-11-23.py carry    --def <定義表> --spec <2 期目の指定> --prev-spec <1 期目の指定> --prev-bundle <束> --prev-result <material の結果>
                                                      --marks <印の file> --src <2 期目の素材の folder> [--ids ..] [--out-bundle <file>] --out <file>
    python3 -I universal_through_check_2026-11-23.py human    --def <定義表> --store <置き場> --doc <markdown> --out <html>
    python3 -I universal_through_check_2026-11-23.py human-check --doc <markdown> --html <html> --out <file>

実装の注(封の字では 1 通りに決まらなかった所の素直な読み。結果を見て変えない。報告にも書く):
- 便 UM0 の注と同じ: 期の読みの正規化・K3 と K4 は素材から読み直した見出しで見る・K0 は id が頼まれた行とちょうど同じだけを見て並びの昇順は見ない・計算の行の入力に ``無い`` と ``確認待ち``・``保留`` が混ざれば ``無い``。
- ``素材``・``素材の和`` の CSV の文字コードは ``表の行の和`` と同じに UTF-8(BOM 可)→ CP932 の順で読む(UM0 の検査は UTF-8 だけ)。素材の folder の中の file は、folder の下の相対 path(``/`` 区切り。``..``・絶対 path・空の部分は読まない)で指せる。
- ``表の行の和`` の列の見出しは、頭の行の cell の字(前後の空白を取る)とちょうど 1 つの列に当たる時だけ決まる(0 個・2 個以上は K1 で止める)。条件が選んだ行が 0 行でも K1 で止める。
- ``表の行の和`` に K2・K3・K6 は掛けない(見出しの申告・見出しの表・行の並びが無い)。K9 は ``無い`` の行だけ。
- K11 は、``表の行の和`` の材料ごとに、``期2/`` の file の 2 期目の当期(期間の行は当期の始まりから当期の終わりまで・時点の行は当期の始まりからその時点まで)の行の中で、日付を読む列は ``以下`` の条件の列。
  列の見出しが ``期1/`` の同じ file の頭の行で決まらなければ新しい値が在る扱い。``期1/`` に同じ file が無ければ新しい値が在る扱い。空の cell も値として数える。新しい値が在る (file, 列) に条件(``どれか``・``どれでもない``・``等しい``・``頭が同じ``)を持つ材料は全部 K11 で止める。K7 より先に掛ける。
- 持ち越しの ``素材`` は、1 期目の行の見出し(正規化の後)と同じ行の見出しを持つ数の cell のうち列の見出しが 2 期目のその行の期に読めるもの(期の読みが ``無し`` の行は、同じ列の見出しの cell)がちょうど 1 つの時に作る。期が行の見出しの側に在る表(月が行に並ぶ表)は探さない(封の字のとおり)。
- 持ち越しの ``表の行の和`` は、日付の条件と ``期間`` を 1 年後へ移し(月の末日は末日へ)、2 期目の素材から数値を足し直す。足せなければ ``確認待ち``。
- 人が読む版は ``<main id="body">`` の中が本文・``<section id="sources">`` の中が数の出どころの表。人が読む版の検査は、封の字の「数の字の並びが同じ」に、「札が残っていない」を足す。
"""
from __future__ import print_function

import calendar
import csv
import datetime
import decimal
import functools
import html as html_lib
import io
import json
import os
import re
import sys
import unicodedata
import zipfile
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from xml.etree import ElementTree as ET

RULES = ("K0", "K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8", "K9", "K11")
TYPE_VERSION = u"u2"
KIND_ROWS = u"表の行の和"
JUDGE_PASS, JUDGE_UNCONF, JUDGE_STOP, JUDGE_NONE_OK = u"通す", u"通す(取り方は未確認)", u"止める", u"無いを受ける"
PASS_JUDGES = (JUDGE_PASS, JUDGE_UNCONF)
COMPARES = (u"等しい", u"どれか", u"どれでもない", u"頭が同じ", u"以上", u"以下")
LIST_COMPARES = (u"どれか", u"どれでもない")
VALUE_COMPARES = (u"等しい", u"どれか", u"どれでもない", u"頭が同じ")
STATE_OK, STATE_NONE = u"在る", u"無い"
NONE_REASON = u"素材が無い"
UNITS = (u"円", u"人", u"純数", u"年")
MULTS = (1, 1000, 1000000)
DOC_UNIT_DIV = {u"円": 1, u"千円": 1000, u"百万円": 1000000}
BIGCTX = decimal.Context(prec=500, rounding=ROUND_HALF_UP)


# ============================================================ 読む・字
def dump_json(obj):
    try:
        body = json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=False)
        body.encode("utf-8")
        return body
    except (UnicodeEncodeError, ValueError):
        return json.dumps(obj, ensure_ascii=True, indent=1, sort_keys=False)


def read_json(path):
    u"""(object, None) か (None, 理由)。"""
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
        text = raw.decode("utf-8")

        def bad(_c):
            raise ValueError(_c)
        return json.loads(text, parse_constant=bad), None
    except BaseException as exc:                 # noqa: BLE001
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        return None, type(exc).__name__


def read_text(path):
    try:
        with open(path, "rb") as fh:
            return fh.read().decode("utf-8"), None
    except BaseException as exc:                 # noqa: BLE001
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        return None, type(exc).__name__


def light(s):
    u"""NFKC と空白の除去だけ。"""
    if not isinstance(s, str):
        return u""
    t = unicodedata.normalize("NFKC", s)
    return u"".join(ch for ch in t if not ch.isspace())


_LEAD = re.compile(u"[IVX0-9]+[.、)]?")


def strip_lead(t):
    m = _LEAD.match(t)
    if m and len(t) > m.end():
        return t[m.end():]
    return t


def norm(s):
    u"""封 §1-7 の見出しの正規化: NFKC → 空白を全部取る → 頭の番号を、取った後に 1 字以上残る時だけ取る。"""
    return strip_lead(light(s))


def cell_number(v):
    u"""封 §1-7 の「cell の数」。数なら Fraction、数でなければ None。"""
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, int):
        return Fraction(v)
    if isinstance(v, float):
        if v != v or v in (float("inf"), float("-inf")):
            return None
        try:
            return Fraction(Decimal(repr(v)))
        except (decimal.InvalidOperation, ValueError):
            return None
    if not isinstance(v, str):
        return None
    t = v.strip().replace(u",", u"")
    neg = False
    if t[:1] in (u"-", u"△", u"▲"):
        neg, t = True, t[1:]
    elif len(t) >= 2 and t[0] == u"(" and t[-1] == u")":
        neg, t = True, t[1:-1]
    if not t or not (t.isascii() and t.isdigit()):
        return None
    try:
        n = int(t)
    except ValueError:
        return None
    return Fraction(-n if neg else n)


def is_empty(v):
    return v is None or (isinstance(v, str) and v.strip() == u"")


def head_text(v):
    return v if isinstance(v, str) else str(v)


def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


# ============================================================ 素材の読み(標準の library だけ)
class Grid(object):
    def __init__(self, rows):
        self.cells = {}
        self.maxr = 0
        self.maxc = 0
        for r, row in enumerate(rows, 1):
            for c, v in enumerate(row, 1):
                if v is None or v == u"":
                    continue
                self.cells[(r, c)] = v
                self.maxr = max(self.maxr, r)
                self.maxc = max(self.maxc, c)

    def get(self, r, c):
        return self.cells.get((r, c))

    def strings(self):
        for v in self.cells.values():
            if isinstance(v, str):
                yield v


def col_letters_to_index(s):
    n = 0
    for ch in s:
        n = n * 26 + (ord(ch) - 64)
    return n


def parse_addr(s):
    if not isinstance(s, str):
        return None
    m = re.fullmatch(u"([A-Z]{1,3})([1-9][0-9]*)", s)
    if not m:
        return None
    return int(m.group(2)), col_letters_to_index(m.group(1))


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def read_xlsx(path):
    u"""{sheet 名: Grid}。読めなければ None。"""
    try:
        zf = zipfile.ZipFile(path)
        total = sum(i.file_size for i in zf.infolist())
        if total > 200 * 1024 * 1024:
            return None
        names = set(zf.namelist())
        shared = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in root:
                if _local(si.tag) != "si":
                    continue
                parts = []
                for el in si.iter():
                    if _local(el.tag) == "t":
                        parts.append(el.text or u"")
                # 読み仮名(rPh)の字を除く
                rph = []
                for ph in si.iter():
                    if _local(ph.tag) == "rPh":
                        for t in ph.iter():
                            if _local(t.tag) == "t":
                                rph.append(t.text or u"")
                text = u"".join(parts)
                if rph:
                    text = text[:len(text) - len(u"".join(rph))]
                shared.append(text)
        wb = ET.fromstring(zf.read("xl/workbook.xml"))
        rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        rid_target = {}
        for rel in rels:
            rid_target[rel.get("Id")] = rel.get("Target")
        out = {}
        for sh in wb.iter():
            if _local(sh.tag) != "sheet":
                continue
            name = sh.get("name")
            rid = None
            for k, v in sh.attrib.items():
                if _local(k) == "id":
                    rid = v
            target = rid_target.get(rid)
            if not name or not target:
                continue
            target = target.lstrip("/")
            if not target.startswith("xl/"):
                target = "xl/" + target
            root = ET.fromstring(zf.read(target))
            cells = {}
            maxr = 0
            for c in root.iter():
                if _local(c.tag) != "c":
                    continue
                pos = parse_addr(c.get("r"))
                if pos is None:
                    continue
                t = c.get("t")
                v = None
                vel = None
                for ch in c:
                    if _local(ch.tag) == "v":
                        vel = ch.text
                    elif _local(ch.tag) == "is":
                        v = u"".join((x.text or u"") for x in ch.iter() if _local(x.tag) == "t")
                if t == "s":
                    try:
                        v = shared[int(vel)]
                    except (TypeError, ValueError, IndexError):
                        v = None
                elif t in ("str", "e"):
                    v = vel
                elif t == "b":
                    v = (vel == "1")
                elif t == "inlineStr":
                    pass
                else:
                    if vel is not None:
                        try:
                            d = Decimal(vel)
                            v = int(d) if d == d.to_integral_value() and abs(d) < Decimal(10) ** 30 else float(d)
                        except (decimal.InvalidOperation, ValueError):
                            v = None
                if v is None or v == u"":
                    continue
                cells[pos] = v
                maxr = max(maxr, pos[0])
            g = Grid([])
            g.cells = cells
            g.maxr = maxr
            g.maxc = max([p[1] for p in cells] or [0])
            out[name] = g
        return out
    except BaseException as exc:                 # noqa: BLE001
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        return None


def decode_text(raw):
    u"""UTF-8(BOM 可)で読めなければ CP932。どちらも読めなければ None。"""
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        pass
    try:
        return raw.decode("cp932")
    except UnicodeDecodeError:
        return None


def read_csv(path):
    try:
        with open(path, "rb") as fh:
            text = decode_text(fh.read())
        if text is None:
            return None
        rows = list(csv.reader(io.StringIO(text, newline=u"")))
        return Grid(rows)
    except BaseException as exc:                 # noqa: BLE001
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        return None


def safe_rel(name):
    u"""folder の下の相対 path として読んでよい字か(``/`` 区切り・``..`` と絶対 path と空の部分を含まない)。"""
    if not isinstance(name, str) or not name or name.startswith(u"/") or u"\\" in name or u"\x00" in name:
        return False
    parts = name.split(u"/")
    return all(x not in (u"", u".", u"..") for x in parts)


class Source(object):
    u"""素材の folder。folder の下の file(相対 path で指す。folder の外へ出る指定は読まない)。"""

    def __init__(self, folder):
        self.folder = folder
        self._names = None
        self._cache = {}
        self._texts = None

    def names(self):
        if self._names is None:
            out = []
            try:
                for root, dirs, files in os.walk(self.folder):
                    dirs.sort()
                    for fn in sorted(files):
                        rel = os.path.relpath(os.path.join(root, fn), self.folder).replace(os.sep, u"/")
                        out.append(rel)
            except OSError:
                out = []
            self._names = sorted(out)
        return self._names

    def file(self, name):
        u"""('xlsx', {sheet: Grid}) か ('csv', Grid) か None。"""
        if not safe_rel(name) or name not in self.names():
            return None
        if name in self._cache:
            return self._cache[name]
        path = os.path.join(self.folder, *name.split(u"/"))
        res = None
        if os.path.isfile(path) and not os.path.islink(path):
            low = name.lower()
            if low.endswith(".xlsx"):
                g = read_xlsx(path)
                res = ("xlsx", g) if g is not None else None
            elif low.endswith(".csv"):
                g = read_csv(path)
                res = ("csv", g) if g is not None else None
        self._cache[name] = res
        return res

    def texts(self):
        u"""素材の全部の cell の字(正規化の後)。"""
        if self._texts is None:
            out = set()
            for n in self.names():
                f = self.file(n)
                if f is None:
                    continue
                grids = list(f[1].values()) if f[0] == "xlsx" else [f[1]]
                for g in grids:
                    for s in g.strings():
                        out.add(norm(s))
            self._texts = out
        return self._texts


def row_heading(g, r, c):
    for cc in range(min(c - 1, g.maxc), 0, -1):
        v = g.get(r, cc)
        if not is_empty(v) and cell_number(v) is None:
            return head_text(v)
    return u""


def col_heading(g, r, c):
    for rr in range(min(r - 1, g.maxr), 0, -1):
        v = g.get(rr, c)
        if not is_empty(v) and cell_number(v) is None:
            return head_text(v)
    return u""


_UNIT_RE = re.compile(u"\\(?単位:(百万円|千円|円)\\)?")


def sheet_unit(g):
    u"""表示の倍率。0 個なら 1・1 個ならその倍率・2 個以上なら None。"""
    found = []
    for s in g.strings():
        m = _UNIT_RE.fullmatch(light(s))
        if m:
            found.append(DOC_UNIT_DIV[m.group(1)])
    if not found:
        return 1
    return found[0] if len(found) == 1 else None


# ============================================================ 指定・定義表・期
def parse_date(s):
    if not isinstance(s, str) or not re.fullmatch(u"[0-9]{4}-[0-9]{2}-[0-9]{2}", s):
        return None
    try:
        return datetime.date(int(s[:4]), int(s[5:7]), int(s[8:]))
    except ValueError:
        return None


def add_months(d, n):
    y, m = divmod(d.year * 12 + d.month - 1 + n, 12)
    day = min(d.day, calendar.monthrange(y, m + 1)[1])
    return datetime.date(y, m + 1, day)


def month_end(y, mo):
    if not (1 <= mo <= 12):
        return None
    return datetime.date(y, mo, calendar.monthrange(y, mo)[1])


class Spec(object):
    pass


def load_spec(path):
    obj, err = read_json(path)
    if err or not isinstance(obj, dict):
        return None, u"指定が読めない"
    if set(obj) != {u"成果物", u"当期の始まり", u"当期の終わり"}:
        return None, u"指定の鍵"
    if obj[u"成果物"] not in (u"A", u"B"):
        return None, u"指定の成果物"
    cs, ce = parse_date(obj[u"当期の始まり"]), parse_date(obj[u"当期の終わり"])
    if cs is None or ce is None or cs > ce:
        return None, u"指定の日"
    try:
        sp = Spec()
        sp.product, sp.cs, sp.ce = obj[u"成果物"], cs, ce
        sp.pe = cs - datetime.timedelta(days=1)
        sp.ps = add_months(cs, -12)
    except (OverflowError, ValueError):
        return None, u"指定の日"
    return sp, None


class Def(object):
    pass


def load_def(path):
    obj, err = read_json(path)
    if err or not isinstance(obj, dict):
        return None, u"定義表が読めない"
    rows = obj.get(u"行")
    if not isinstance(rows, list) or not all(isinstance(r, dict) and isinstance(r.get(u"id"), str) for r in rows):
        return None, u"定義表の行"
    ids = [r[u"id"] for r in rows]
    if len(set(ids)) != len(ids):
        return None, u"定義表の id"
    d = Def()
    d.raw = obj
    d.rows = rows
    d.by_id = dict((r[u"id"], r) for r in rows)
    d.product = obj.get(u"成果物")
    rel = obj.get(u"関係")
    d.relations = [x for x in rel if isinstance(x, dict)] if isinstance(rel, list) else []
    return d, None


def material_ids(d):
    return [r[u"id"] for r in d.rows if r.get(u"取り方") in (u"素材", u"素材の和")]


def expected_period(row, sp):
    k = row.get(u"期")
    if k == u"当期":
        return (u"期間", sp.cs, sp.ce)
    if k == u"前期":
        return (u"期間", sp.ps, sp.pe)
    if k == u"当期末":
        return (u"時点", sp.ce)
    if k == u"前期末":
        return (u"時点", sp.pe)
    if isinstance(k, str):
        m = re.fullmatch(u"当期の月:([0-9]{1,2})", k)
        if m and 1 <= int(m.group(1)) <= 12:
            n = int(m.group(1))
            try:
                return (u"期間", add_months(sp.cs, n - 1), add_months(sp.cs, n) - datetime.timedelta(days=1))
            except (OverflowError, ValueError):
                return None
    return None


def mat_period(p):
    if not isinstance(p, dict):
        return None
    if set(p) == {u"時点"}:
        d = parse_date(p[u"時点"])
        return (u"時点", d) if d else None
    if set(p) == {u"始まり", u"終わり"}:
        a, b = parse_date(p[u"始まり"]), parse_date(p[u"終わり"])
        return (u"期間", a, b) if a and b else None
    return None


def _read_period1(c, kind, sp):
    try:
        if c == u"当期":
            return (u"期間", sp.cs, sp.ce) if kind == u"期間" else (u"時点", sp.ce)
        if c == u"前期":
            return (u"期間", sp.ps, sp.pe) if kind == u"期間" else (u"時点", sp.pe)
        if c == u"当期末":
            return (u"時点", sp.ce)
        if c == u"前期末":
            return (u"時点", sp.pe)
        m = re.fullmatch(u"([0-9]{4})年([0-9]{1,2})月期", c)
        if m:
            end = month_end(int(m.group(1)), int(m.group(2)))
            if end is None:
                return None
            if kind == u"期間":
                return (u"期間", add_months(end + datetime.timedelta(days=1), -12), end)
            return (u"時点", end)
        m = re.fullmatch(u"([0-9]{4})年([0-9]{1,2})月末", c)
        if m:
            end = month_end(int(m.group(1)), int(m.group(2)))
            return (u"時点", end) if end else None
        m = re.fullmatch(u"([0-9]{4})年([0-9]{1,2})月", c) or re.fullmatch(u"([0-9]{4})/([0-9]{2})", c)
        if m:
            y, mo = int(m.group(1)), int(m.group(2))
            end = month_end(y, mo)
            return (u"期間", datetime.date(y, mo, 1), end) if end else None
        m = re.fullmatch(u"([0-9]{1,2})月", c)
        if m:
            mo = int(m.group(1))
            for k in range(1, 13):
                ms = add_months(sp.cs, k - 1)
                if ms.month == mo:
                    return (u"期間", ms, add_months(sp.cs, k) - datetime.timedelta(days=1))
            return None
    except (OverflowError, ValueError):
        return None
    return None


def read_period(h, kind, sp):
    u"""見出しの字 → 期。読めなければ None。(NFKC と空白の除去 → 読めなければ頭の番号を取って読む)"""
    if not isinstance(h, str):
        return None
    s = light(h)
    for cand in (s, strip_lead(s)):
        r = _read_period1(cand, kind, sp)
        if r is not None:
            return r
    return None


# ============================================================ K0 形
_NUM_RE = re.compile(u"-?(0|[1-9][0-9]*)")
SRC_KEYS = {u"素材": {u"種類", u"file", u"位置", u"行の見出し", u"列の見出し", u"表示の倍率"},
            u"素材の和": {u"種類", u"file", u"列", u"行の並び", u"列の見出し", u"表示の倍率"},
            KIND_ROWS: {u"種類", u"file", u"頭の行", u"額", u"条件", u"表示の倍率"}}
AMOUNT_SINGLE = {u"列", u"符号"}
AMOUNT_PAIR = {u"借方の列", u"貸方の列", u"向き"}
SIGNS = (u"そのまま", u"逆")
DIRECTIONS = (u"借方\u2212貸方", u"貸方\u2212借方")


def k0_amount(a):
    if not isinstance(a, dict):
        return [u"額の形"]
    if set(a) == AMOUNT_SINGLE:
        ok = isinstance(a[u"列"], str) and a[u"符号"] in SIGNS and isinstance(a[u"符号"], str)
    elif set(a) == AMOUNT_PAIR:
        ok = isinstance(a[u"借方の列"], str) and isinstance(a[u"貸方の列"], str) and isinstance(a[u"向き"], str) and a[u"向き"] in DIRECTIONS
    else:
        ok = False
    return [] if ok else [u"額の形"]


def k0_condition(c):
    if not isinstance(c, dict) or set(c) != {u"列", u"比べ方", u"値"}:
        return [u"条件の形"]
    out = []
    if not isinstance(c[u"列"], str):
        out.append(u"条件の列")
    how, val = c[u"比べ方"], c[u"値"]
    if not isinstance(how, str) or how not in COMPARES:
        return out + [u"比べ方"]
    if how in LIST_COMPARES:
        if not (isinstance(val, list) and 1 <= len(val) <= 200 and all(isinstance(x, str) for x in val)):
            out.append(u"値の並び")
    elif not isinstance(val, str):
        out.append(u"値の字")
    elif how in (u"以上", u"以下") and parse_date(val) is None:
        out.append(u"日付の値")
    return out


def k0_item(m):
    u"""材料 1 つの形の理由(無ければ空)。"""
    if not isinstance(m, dict):
        return [u"材料が object でない"]
    out = []
    st = m.get(u"状態")
    if not isinstance(m.get(u"id"), str):
        out.append(u"id が字でない")
    if st == STATE_NONE:
        if set(m) != {u"id", u"状態", u"無い理由"}:
            out.append(u"無いの鍵")
        elif m.get(u"無い理由") != NONE_REASON:
            out.append(u"無い理由")
        return out
    if st != STATE_OK:
        return out + [u"状態"]
    if set(m) != {u"id", u"状態", u"数値", u"単位", u"期間", u"範囲", u"出どころ"}:
        return out + [u"在るの鍵"]
    v = m[u"数値"]
    if not (isinstance(v, str) and _NUM_RE.fullmatch(v)):
        out.append(u"数値の形")
    if not isinstance(m[u"単位"], str):
        out.append(u"単位の形")
    if mat_period(m[u"期間"]) is None:
        out.append(u"期間の形")
    if not isinstance(m[u"範囲"], str):
        out.append(u"範囲の形")
    s = m[u"出どころ"]
    if not isinstance(s, dict) or s.get(u"種類") not in SRC_KEYS:
        return out + [u"出どころの種類"]
    if set(s) != SRC_KEYS[s[u"種類"]]:
        return out + [u"出どころの鍵"]
    if not isinstance(s[u"file"], str):
        out.append(u"出どころの字")
    if s[u"種類"] != KIND_ROWS and not isinstance(s[u"列の見出し"], str):
        out.append(u"出どころの字")
    if not (is_int(s[u"表示の倍率"]) and s[u"表示の倍率"] in MULTS):
        out.append(u"表示の倍率")
    if s[u"種類"] == KIND_ROWS:
        if not (is_int(s[u"頭の行"]) and s[u"頭の行"] >= 1):
            out.append(u"頭の行の形")
        out.extend(k0_amount(s[u"額"]))
        conds = s[u"条件"]
        if not (isinstance(conds, list) and 1 <= len(conds) <= 8):
            out.append(u"条件の数")
        else:
            for c in conds:
                out.extend(k0_condition(c))
    elif s[u"種類"] == u"素材":
        if not isinstance(s[u"行の見出し"], str):
            out.append(u"行の見出しの字")
        p = s[u"位置"]
        if isinstance(p, dict) and set(p) == {u"sheet", u"セル"}:
            if not isinstance(p[u"sheet"], str) or parse_addr(p[u"セル"]) is None:
                out.append(u"位置の形")
        elif isinstance(p, dict) and set(p) == {u"行", u"列"}:
            if not (is_int(p[u"行"]) and is_int(p[u"列"]) and p[u"行"] >= 1 and p[u"列"] >= 1):
                out.append(u"位置の形")
        else:
            out.append(u"位置の形")
    else:
        rows = s[u"行の並び"]
        if not (is_int(s[u"列"]) and s[u"列"] >= 1):
            out.append(u"列の形")
        if not (isinstance(rows, list) and rows and all(is_int(x) and x >= 1 for x in rows)
                and all(rows[k] < rows[k + 1] for k in range(len(rows) - 1))):
            out.append(u"行の並びの形")
    return out


def k0_bundle(ctx, bundle, wanted):
    u"""束の形の理由の並び(空なら通す)。"""
    if not isinstance(bundle, dict) or set(bundle) != {u"型の版", u"材料"}:
        return [u"頂の鍵"]
    out = []
    if bundle[u"型の版"] != TYPE_VERSION:
        out.append(u"型の版")
    items = bundle[u"材料"]
    if not isinstance(items, list):
        return out + [u"材料が並びでない"]
    ids = []
    for m in items:
        out.extend(k0_item(m))
        if isinstance(m, dict) and isinstance(m.get(u"id"), str):
            ids.append(m[u"id"])
    if len(set(ids)) != len(ids):
        out.append(u"id の重複")
    if sorted(set(ids)) != sorted(set(wanted)) or len(ids) != len(set(ids)):
        out.append(u"id が頼んだ行と違う")
    return out


# ============================================================ 表の行の和(CSV の仕訳の行を条件で選んで足す)
@functools.lru_cache(maxsize=300000)
def parse_cell_date(text):
    u"""日付の cell(``YYYY-MM-DD``・``YYYY/M/D``・``YYYYMMDD``・``YYYY年M月D日``)→ date。読めなければ None。前後の空白は取る。"""
    if not isinstance(text, str):
        return None
    t = text.strip()
    for pat in (u"([0-9]{4})-([0-9]{2})-([0-9]{2})", u"([0-9]{4})/([0-9]{1,2})/([0-9]{1,2})", u"([0-9]{4})([0-9]{2})([0-9]{2})",
                u"([0-9]{4})年([0-9]{1,2})月([0-9]{1,2})日"):
        m = re.fullmatch(pat, t)
        if m:
            try:
                return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                return None
    return None


def cell_text(v):
    if v is None:
        return u""
    return v.strip() if isinstance(v, str) else str(v).strip()


def header_column(g, head, text):
    u"""頭の行の cell の字(前後の空白を取る)がちょうど 1 つの列に当たる時だけ、その列(1 始まり)。"""
    if not isinstance(text, str):
        return None
    want = text.strip()
    hits = [c for c in range(1, g.maxc + 1) if cell_text(g.get(head, c)) == want]
    return hits[0] if len(hits) == 1 else None


def prep_cond(c):
    u"""条件 1 つ → (比べ方, 比べる値)。値は前後の空白を取り、日付は date にする。"""
    how, val = c[u"比べ方"], c[u"値"]
    if how in LIST_COMPARES:
        return how, frozenset(x.strip() for x in val)
    if how in (u"以上", u"以下"):
        return how, parse_date(val)
    return how, val.strip()


def cond_match(cell, how, val):
    u"""条件 1 つ(封 §1-4)。``cell`` は前後の空白を取った字。``val`` は ``prep_cond`` の値。"""
    if how == u"等しい":
        return cell != u"" and cell == val
    if how == u"どれか":
        return cell != u"" and cell in val
    if how == u"どれでもない":
        return cell == u"" or cell not in val
    if how == u"頭が同じ":
        return cell != u"" and cell.startswith(val)
    d = parse_cell_date(cell)
    if d is None or val is None:
        return False
    return d >= val if how == u"以上" else d <= val


def select_rows(g, s):
    u"""``表の行の和`` の出どころ ``s`` が選ぶ行と額の和。戻りは (ok, 理由, 行の数, 和(Fraction), 条件の列の並び)。"""
    head = s.get(u"頭の行")
    if not is_int(head) or head < 1 or head > g.maxr:
        return False, u"頭の行が無い", 0, None, []
    conds = s.get(u"条件")
    amt = s.get(u"額")
    if not isinstance(conds, list) or not isinstance(amt, dict):
        return False, u"形", 0, None, []
    cols = []
    for c in conds:
        col = header_column(g, head, c.get(u"列")) if isinstance(c, dict) else None
        if col is None:
            return False, u"列が決まらない", 0, None, []
        cols.append(col)
    pair = set(amt) == AMOUNT_PAIR
    if pair:
        dcol, ccol = header_column(g, head, amt.get(u"借方の列")), header_column(g, head, amt.get(u"貸方の列"))
        if dcol is None or ccol is None:
            return False, u"額の列が決まらない", 0, None, cols
        sign = 1 if amt.get(u"向き") == DIRECTIONS[0] else -1
    else:
        acol = header_column(g, head, amt.get(u"列"))
        if acol is None:
            return False, u"額の列が決まらない", 0, None, cols
        sign = -1 if amt.get(u"符号") == u"逆" else 1
    total = Fraction(0)
    n = 0
    prepared = [prep_cond(c) for c in conds]
    for r in range(head + 1, g.maxr + 1):
        okrow = True
        for (how, val), col in zip(prepared, cols):
            if not cond_match(cell_text(g.get(r, col)), how, val):
                okrow = False
                break
        if not okrow:
            continue
        n += 1
        if pair:
            parts = []
            for col in (dcol, ccol):
                v = g.get(r, col)
                if is_empty(v):
                    parts.append(Fraction(0))
                else:
                    x = cell_number(v)
                    if x is None:
                        return False, u"額が数でない", n, None, cols
                    parts.append(x)
            total += sign * (parts[0] - parts[1])
        else:
            v = g.get(r, acol)
            if is_empty(v):
                continue
            x = cell_number(v)
            if x is None:
                return False, u"額が数でない", n, None, cols
            total += sign * x
    if n == 0:
        return False, u"選んだ行が 0", 0, None, cols
    return True, u"", n, total, cols


def select_file(src, s):
    u"""``file`` を CSV として読んで ``select_rows``。戻りは ((ok, 理由, 行の数, 和, 列), grid か None)。

    同じ素材の folder・同じ条件の選び直しは 1 回だけ数える(``Source`` の中に覚える。結果は同じ)。
    """
    f = src.file(s.get(u"file")) if isinstance(s, dict) else None
    if f is None or f[0] != "csv":
        return (False, u"file が CSV でない", 0, None, []), None
    try:
        key = (s.get(u"file"), json.dumps([s.get(u"頭の行"), s.get(u"額"), s.get(u"条件")], ensure_ascii=True, sort_keys=True))
    except (TypeError, ValueError):
        return select_rows(f[1], s), f[1]
    memo = src.__dict__.setdefault("_selected", {})
    if key not in memo:
        memo[key] = select_rows(f[1], s)
    return memo[key], f[1]


def last_day(d):
    return d.day == calendar.monthrange(d.year, d.month)[1]


def shift_year(d, years=1):
    u"""同じ月日で ``years`` 年後(負なら前)。月の末日は末日へ。"""
    y = d.year + years
    if last_day(d):
        return datetime.date(y, d.month, calendar.monthrange(y, d.month)[1])
    return add_months(d, 12 * years)


# ============================================================ 材料 1 つの読み直し
def analyse(ctx, m, d):
    info = {u"cell": None, u"num": None, u"rowh": None, u"colh": None, u"unit": None, u"k3": u"neither", u"grid": None}
    s = m.get(u"出どころ")
    if not isinstance(s, dict):
        return info
    f = ctx.src.file(s.get(u"file"))
    kind = s.get(u"種類")
    grid = None
    r = c = None
    if kind == u"素材":
        p = s.get(u"位置")
        if f is not None and isinstance(p, dict):
            if f[0] == "xlsx" and set(p) == {u"sheet", u"セル"} and isinstance(p.get(u"sheet"), str):
                grid = f[1].get(p[u"sheet"])
                pos = parse_addr(p.get(u"セル"))
                if grid is not None and pos:
                    r, c = pos
            elif f[0] == "csv" and set(p) == {u"行", u"列"} and is_int(p.get(u"行")) and is_int(p.get(u"列")) \
                    and p[u"行"] >= 1 and p[u"列"] >= 1:
                grid, r, c = f[1], p[u"行"], p[u"列"]
        if grid is not None and r is not None:
            info[u"grid"] = grid
            info[u"cell"] = grid.get(r, c)
            info[u"num"] = cell_number(info[u"cell"])
            info[u"rowh"] = row_heading(grid, r, c)
            info[u"colh"] = col_heading(grid, r, c)
            info[u"unit"] = sheet_unit(grid)
    elif kind == u"素材の和":
        rows = s.get(u"行の並び")
        col = s.get(u"列")
        if f is not None and f[0] == "csv" and is_int(col) and col >= 1 and isinstance(rows, list) and rows \
                and all(is_int(x) and x >= 1 for x in rows):
            grid = f[1]
            info[u"grid"] = grid
            nums = [cell_number(grid.get(n, col)) for n in rows]
            info[u"num"] = None if any(x is None for x in nums) else sum(nums, Fraction(0))
            info[u"colh"] = col_heading(grid, min(rows), col)
            info[u"unit"] = sheet_unit(grid)
    elif kind == KIND_ROWS:
        res, grid = select_file(ctx.src, s)
        info[u"sel"] = res
        if grid is not None:
            info[u"grid"] = grid
            info[u"unit"] = sheet_unit(grid)
        info[u"num"] = res[3] if res[0] else None
    table = set(norm(x) for x in d.get(u"見出し", []) if isinstance(x, str)) if isinstance(d.get(u"見出し"), list) else set()
    info[u"table"] = table
    if kind == u"素材":
        rin = info[u"rowh"] is not None and norm(info[u"rowh"]) in table
        cin = info[u"colh"] is not None and norm(info[u"colh"]) in table
        info[u"k3"] = u"both" if (rin and cin) else (u"row" if rin else (u"col" if cin else u"neither"))
    elif kind == u"素材の和":
        cin = info[u"colh"] is not None and norm(info[u"colh"]) in table
        info[u"k3"] = u"col" if cin else u"neither"
    return info


def rule_k1(ctx, m, d, info):
    s = m[u"出どころ"]
    if info[u"num"] is None:
        return True
    mult = s.get(u"表示の倍率")
    if not is_int(mult):
        return True
    try:
        return info[u"num"] * mult != int(m[u"数値"])
    except (TypeError, ValueError):
        return True


def rule_k2(ctx, m, d, info):
    s = m[u"出どころ"]
    if s.get(u"種類") == KIND_ROWS:
        return False
    if info[u"colh"] is None or norm(s.get(u"列の見出し")) != norm(info[u"colh"]):
        return True
    if s.get(u"種類") == u"素材" and (info[u"rowh"] is None or norm(s.get(u"行の見出し")) != norm(info[u"rowh"])):
        return True
    return False


def rule_k3(ctx, m, d, info):
    kind = m[u"出どころ"].get(u"種類")
    if kind == KIND_ROWS:
        return False
    if kind != d.get(u"取り方"):
        return True
    if kind == u"素材":
        return info[u"k3"] not in (u"row", u"col")
    return info[u"k3"] != u"col"


def rule_k4(ctx, m, d, info):
    exp = expected_period(d, ctx.spec)
    if exp is None or mat_period(m.get(u"期間")) != exp:
        return True
    if m[u"出どころ"].get(u"種類") == KIND_ROWS:
        conds = m[u"出どころ"][u"条件"]
        ge = [c for c in conds if c[u"比べ方"] == u"以上"]
        le = [c for c in conds if c[u"比べ方"] == u"以下"]
        if exp[0] == u"期間":
            if len(ge) != 1 or len(le) != 1 or ge[0][u"列"] != le[0][u"列"]:
                return True
            return parse_date(ge[0][u"値"]) != exp[1] or parse_date(le[0][u"値"]) != exp[2]
        return len(le) != 1 or parse_date(le[0][u"値"]) != exp[1]
    mode = d.get(u"期の読み")
    if mode == u"無し":
        return False
    if mode != u"要る":
        return True
    if info[u"k3"] in (u"row", u"col"):
        other = info[u"colh"] if info[u"k3"] == u"row" else info[u"rowh"]
        if other is None:
            return False
        return read_period(other, exp[0], ctx.spec) != exp
    return False


def rule_k5(ctx, m, d, info):
    if m.get(u"単位") != d.get(u"単位"):
        return True
    mult = m[u"出どころ"].get(u"表示の倍率")
    if d.get(u"単位") == u"円":
        return info[u"unit"] is None or mult != info[u"unit"]
    return mult != 1


def rule_k6(ctx, m, d, info):
    s = m[u"出どころ"]
    if s.get(u"種類") != u"素材の和":
        return False
    g = info[u"grid"]
    if g is None:
        return True
    col = s.get(u"列")
    want = []
    for n in range(1, g.maxr + 1):
        if cell_number(g.get(n, col)) is not None and norm(head_text(g.get(n, 1)) if g.get(n, 1) is not None else u"") not in (u"合計", u"計"):
            want.append(n)
    return list(s.get(u"行の並び")) != want


def rule_k8(ctx, m, d, info):
    return m.get(u"範囲") != d.get(u"範囲")


def rule_k9(ctx, d):
    table = set(norm(x) for x in d.get(u"見出し", []) if isinstance(x, str)) if isinstance(d.get(u"見出し"), list) else set()
    return bool(table & ctx.src.texts())


def rule_k7(ctx, results, bundle_items):
    u"""関係。戻りは (止める id の集合, 見た数, 見なかった数)。"""
    passed = {}
    for r in results:
        if r[u"状態"] == STATE_OK and not [x for x in r[u"規則"] if x in ("K1", "K2", "K3", "K4", "K5", "K6", "K11")]:
            passed[r[u"id"]] = bundle_items[r[u"id"]]
    stop, seen, unseen = set(), 0, 0
    for rel in ctx.defn.relations:
        left, right = rel.get(u"左"), rel.get(u"右")
        if not (isinstance(left, list) and isinstance(right, list)) or not all(isinstance(x, str) for x in left + right):
            unseen += 1
            continue
        allids = left + right
        if not allids or not all(i in passed for i in allids):
            unseen += 1
            continue
        seen += 1
        try:
            lv = sum(int(passed[i][u"数値"]) for i in left)
            rv = sum(int(passed[i][u"数値"]) for i in right)
        except (TypeError, ValueError):
            stop.update(allids)
            continue
        if lv != rv:
            stop.update(allids)
    return stop, seen, unseen


def k11_window(ctx, m):
    u"""K11 が見る 2 期目の日付の窓。期間の行は当期の始まりから当期の終わり・時点の行は当期の始まりからその時点まで。"""
    p = mat_period(m.get(u"期間"))
    if p is None:
        return None
    if p[0] == u"期間":
        return ctx.spec.cs, ctx.spec.ce
    return ctx.spec.cs, p[1]


def k11_flags(ctx, m):
    u"""``表の行の和`` の材料 1 つが、新しい値が在ると見た (file, 列の字) の集合と、条件を持つ (file, 列の字) の集合。"""
    s = m[u"出どころ"]
    conds = [c for c in s[u"条件"] if c[u"比べ方"] in VALUE_COMPARES]
    keys = set((s[u"file"], c[u"列"].strip()) for c in conds)
    if not conds:
        return set(), keys
    prev = getattr(ctx, "prev_src", None)
    win = k11_window(ctx, m)
    cur = ctx.src.file(s[u"file"])
    old = prev.file(s[u"file"]) if prev is not None else None
    if win is None or cur is None or cur[0] != "csv":
        return set(), keys
    if old is None or old[0] != "csv":
        return set(keys), keys
    g, h = cur[1], old[1]
    head = s[u"頭の行"]
    les = [c for c in s[u"条件"] if c[u"比べ方"] == u"以下"] or [c for c in s[u"条件"] if c[u"比べ方"] == u"以上"]
    dcol = header_column(g, head, les[0][u"列"]) if les else None
    if dcol is None:
        return set(), keys
    flagged = set()
    for c in conds:
        col = header_column(g, head, c[u"列"])
        if col is None:
            continue
        ocol = header_column(h, head, c[u"列"])
        key = (s[u"file"], c[u"列"].strip())
        if ocol is None:
            flagged.add(key)
            continue
        olds = set(cell_text(h.get(r, ocol)) for r in range(head + 1, h.maxr + 1))
        for r in range(head + 1, g.maxr + 1):
            d = parse_cell_date(cell_text(g.get(r, dcol)))
            if d is None or d < win[0] or d > win[1]:
                continue
            if cell_text(g.get(r, col)) not in olds:
                flagged.add(key)
                break
    return flagged, keys


def rule_k11(ctx, results, bundle_items):
    u"""新しい値。戻りは止める id の集合。``期1/`` の素材の folder(``ctx.prev_src``)が無い時は何も止めない。"""
    if getattr(ctx, "prev_src", None) is None:
        return set()
    flagged, per = set(), {}
    for r in results:
        m = bundle_items.get(r[u"id"])
        if r[u"状態"] != STATE_OK or not isinstance(m, dict) or m.get(u"出どころ", {}).get(u"種類") != KIND_ROWS:
            continue
        f, keys = k11_flags(ctx, m)
        flagged |= f
        per[r[u"id"]] = keys
    return set(i for i, keys in per.items() if keys & flagged)


#: 差し替えられる規則の関数(変異の門が 1 つずつ差し替える。戻しは try/finally)
RULE_FUNCS = {u"K0": k0_bundle, u"K1": rule_k1, u"K2": rule_k2, u"K3": rule_k3, u"K4": rule_k4,
              u"K5": rule_k5, u"K6": rule_k6, u"K7": rule_k7, u"K8": rule_k8, u"K9": rule_k9, u"K11": rule_k11}


class Ctx(object):
    pass


def check_bundle(spec, defn, bundle, src, ids=None, form_only=False, confirmed=None, prev_src=None):
    u"""材料の検査。例外を出さない。戻りは dict(``束`` ・ ``材料`` ・ ``K7``)。

    ``confirmed`` は取り方を確かめた id の集合(``表の行の和`` の材料がこの中に無ければ ``通す(取り方は未確認)``)。
    ``prev_src`` は 1 期目の素材の folder(K11 が使う。無ければ K11 は何も止めない)。
    """
    try:
        return _check_bundle(spec, defn, bundle, src, ids, form_only, confirmed, prev_src)
    except RecursionError:
        return refuse(u"K0", u"入れ子が深い")
    except (KeyError, TypeError, AttributeError, ValueError, IndexError) as exc:
        return refuse(u"K0", u"形が読めない: " + type(exc).__name__)


def _final_judge(r, m, confirmed):
    if r[u"規則"]:
        return JUDGE_STOP
    if isinstance(m.get(u"出どころ"), dict) and m[u"出どころ"].get(u"種類") == KIND_ROWS and m[u"id"] not in (confirmed or ()):
        return JUDGE_UNCONF
    return JUDGE_PASS


def _check_bundle(spec, defn, bundle, src, ids, form_only, confirmed=None, prev_src=None):
    ctx = Ctx()
    ctx.spec, ctx.defn, ctx.src, ctx.prev_src = spec, defn, src, prev_src
    wanted = list(ids) if ids is not None else material_ids(defn)
    reasons = RULE_FUNCS[u"K0"](ctx, bundle, wanted)
    if reasons:
        return {u"束": {u"状態": u"断り", u"規則": [u"K0"], u"理由": reasons}, u"材料": [], u"K7": {u"見た": 0, u"見なかった": 0}}
    items = bundle[u"材料"]
    results = []
    by_id = {}
    for m in items:
        by_id[m[u"id"]] = m
        d = defn.by_id.get(m[u"id"])
        if form_only:
            results.append({u"id": m[u"id"], u"状態": m[u"状態"], u"判定": JUDGE_PASS if m[u"状態"] == STATE_OK else JUDGE_NONE_OK, u"規則": []})
            continue
        if d is None:
            results.append({u"id": m[u"id"], u"状態": m[u"状態"], u"判定": JUDGE_STOP, u"規則": [u"K0"]})
            continue
        stops = []
        if m[u"状態"] == STATE_NONE:
            if RULE_FUNCS[u"K9"](ctx, d):
                stops.append(u"K9")
            results.append({u"id": m[u"id"], u"状態": STATE_NONE, u"判定": JUDGE_STOP if stops else JUDGE_NONE_OK, u"規則": stops})
            continue
        info = analyse(ctx, m, d)
        for name in (u"K1", u"K2", u"K3", u"K4", u"K5", u"K6", u"K8"):
            try:
                hit = RULE_FUNCS[name](ctx, m, d, info)
            except BaseException as exc:          # noqa: BLE001
                if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                    raise
                hit = True
            if hit:
                stops.append(name)
        results.append({u"id": m[u"id"], u"状態": STATE_OK, u"判定": JUDGE_PASS, u"規則": stops})
    k7 = {u"見た": 0, u"見なかった": 0}
    if not form_only:
        try:
            stop11 = RULE_FUNCS[u"K11"](ctx, results, by_id)
        except BaseException as exc:              # noqa: BLE001
            if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                raise
            stop11 = set(r[u"id"] for r in results if by_id[r[u"id"]].get(u"出どころ", {}).get(u"種類") == KIND_ROWS)
        for r in results:
            if r[u"id"] in stop11 and r[u"状態"] == STATE_OK:
                r[u"規則"] = r[u"規則"] + [u"K11"]
        stop7, seen, unseen = RULE_FUNCS[u"K7"](ctx, results, by_id)
        k7 = {u"見た": seen, u"見なかった": unseen}
        for r in results:
            if r[u"id"] in stop7 and r[u"状態"] == STATE_OK:
                r[u"規則"] = r[u"規則"] + [u"K7"]
        for r in results:
            if r[u"状態"] == STATE_OK:
                r[u"規則"] = [x for x in RULES if x in r[u"規則"]]
                r[u"判定"] = _final_judge(r, by_id[r[u"id"]], confirmed)
    return {u"束": {u"状態": u"受理", u"規則": [], u"理由": []}, u"材料": results, u"K7": k7}


def refuse(rule, reason):
    return {u"束": {u"状態": u"断り", u"規則": [rule], u"理由": [reason]}, u"材料": [], u"K7": {u"見た": 0, u"見なかった": 0}}


def read_marks(path):
    u"""印の file ``{"確かめた取り方": [id, ...]}`` → id の集合。読めなければ None。"""
    obj, err = read_json(path)
    if err or not isinstance(obj, dict) or set(obj) != {u"確かめた取り方"} or not isinstance(obj[u"確かめた取り方"], list):
        return None
    if not all(isinstance(x, str) for x in obj[u"確かめた取り方"]):
        return None
    return set(obj[u"確かめた取り方"])


def check_files(spec_path, def_path, bundle_path, src_dir, ids=None, form_only=False, confirmed_path=None, prev_src_dir=None):
    spec, err = load_spec(spec_path)
    if spec is None:
        return refuse(u"入力", err)
    defn, err = load_def(def_path)
    if defn is None:
        return refuse(u"入力", err)
    bundle, err = read_json(bundle_path)
    if err:
        return refuse(u"K0", u"束が読めない: " + err)
    confirmed = None
    if confirmed_path is not None:
        confirmed = read_marks(confirmed_path)
        if confirmed is None:
            return refuse(u"入力", u"印が読めない")
    prev = Source(prev_src_dir) if prev_src_dir is not None else None
    return check_bundle(spec, defn, bundle, Source(src_dir), ids=ids, form_only=form_only, confirmed=confirmed, prev_src=prev)


# ============================================================ 6 段目 置き場・計算・計画
def round_dec(x, places):
    q = Decimal(1).scaleb(-places)
    return x.quantize(q, rounding=ROUND_HALF_UP, context=BIGCTX)


def dec_text(x):
    t = format(x, "f")
    if re.fullmatch(u"-0(\\.0*)?", t):
        t = t[1:]
    return t


def compute_row(row, store_rows):
    u"""計算の行 1 つを置き場の行から作る。戻りは置き場の行(dict)。"""
    ins = row.get(u"入力")
    base = {u"種類": u"計算"}
    if not isinstance(ins, list) or not all(isinstance(i, str) for i in ins):
        base.update({u"状態": STATE_NONE, u"理由": u"計算できない"})
        return base
    states = [store_rows.get(i, {}).get(u"状態") for i in ins]
    if all(s == STATE_OK for s in states):
        try:
            vals = [Decimal(store_rows[i][u"値"]) for i in ins]
            f = row.get(u"式")
            places = row.get(u"桁", 0)
            if not is_int(places) or places < 0:
                raise ValueError("桁")
            with decimal.localcontext(BIGCTX):
                if f == u"和":
                    res = sum(vals, Decimal(0))
                elif f == u"比":
                    if vals[1] == 0:
                        raise ZeroDivisionError
                    res = round_dec(vals[0] / vals[1], places)
                elif f == u"比の分母和":
                    den = vals[1] + vals[2]
                    if den <= 0:
                        raise ZeroDivisionError
                    res = round_dec(vals[0] / den, places)
                elif f == u"増減率":
                    if vals[1] == 0:
                        raise ZeroDivisionError
                    res = round_dec((vals[0] - vals[1]) / vals[1], places)
                else:
                    raise ValueError("式")
            base.update({u"状態": STATE_OK, u"値": dec_text(res), u"単位": row.get(u"単位"), u"範囲": row.get(u"範囲")})
            return base
        except (ZeroDivisionError, ValueError, IndexError, KeyError, decimal.DecimalException, TypeError):
            base.update({u"状態": STATE_NONE, u"理由": u"計算できない"})
            return base
    if any(s == STATE_NONE for s in states):
        base.update({u"状態": STATE_NONE, u"理由": u"入力の材料が無い"})
        return base
    base.update({u"状態": u"保留"})
    return base


def build_store(defn, result, bundle, product, prior=None, ids=None, waiting=None):
    u"""置き場。通った材料(取り方が未確認のものは ``未確認`` の印つき)・無いを受けた行・止まった行(確認待ち)・計算の行。

    ``waiting`` は ``id → 理由`` の辞書(持ち越せなかった行。検査の結果に無い id は、この理由つきの ``確認待ち`` になる)。
    """
    rows = {}
    if isinstance(prior, dict) and isinstance(prior.get(u"行"), dict):
        rows = json.loads(json.dumps(prior[u"行"]))
    wanted = list(ids) if ids is not None else material_ids(defn)
    refused = isinstance(result, dict) and isinstance(result.get(u"束"), dict) and result[u"束"].get(u"状態") != u"受理"
    items = {}
    if isinstance(bundle, dict) and isinstance(bundle.get(u"材料"), list):
        for m in bundle[u"材料"]:
            if isinstance(m, dict) and isinstance(m.get(u"id"), str):
                items[m[u"id"]] = m
    verdict = {}
    if isinstance(result, dict) and isinstance(result.get(u"材料"), list):
        for r in result[u"材料"]:
            if isinstance(r, dict) and isinstance(r.get(u"id"), str):
                verdict[r[u"id"]] = r
    for i in wanted:
        if i in rows:
            continue
        r = verdict.get(i)
        m = items.get(i, {})
        if isinstance(waiting, dict) and i in waiting and (refused or r is None):
            rows[i] = {u"状態": u"確認待ち", u"規則": [], u"理由": waiting[i], u"入った成果物": product}
        elif refused or r is None:
            rows[i] = {u"状態": u"確認待ち", u"規則": [u"K0"], u"入った成果物": product}
        elif r.get(u"判定") in PASS_JUDGES:
            rows[i] = {u"状態": STATE_OK, u"値": m.get(u"数値"), u"単位": m.get(u"単位"), u"期間": m.get(u"期間"),
                       u"範囲": m.get(u"範囲"), u"出どころ": m.get(u"出どころ"), u"入った成果物": product}
            if r.get(u"判定") == JUDGE_UNCONF:
                rows[i][u"未確認"] = True
        elif r.get(u"判定") == u"無いを受ける":
            rows[i] = {u"状態": STATE_NONE, u"理由": NONE_REASON, u"入った成果物": product}
        else:
            rows[i] = {u"状態": u"確認待ち", u"規則": list(r.get(u"規則", [])), u"入った成果物": product}
    for row in defn.rows:
        if row.get(u"取り方") == u"計算":
            new = compute_row(row, rows)
            new[u"入った成果物"] = product
            rows[row[u"id"]] = new
    used = [r[u"id"] for r in defn.rows]
    for i in used:
        if i in rows:
            rows[i].setdefault(u"使われた成果物", [])
            if product not in rows[i][u"使われた成果物"]:
                rows[i][u"使われた成果物"].append(product)
    return {u"版": u"u2-store", u"行": rows}


def make_plan(defn, store):
    srows = store.get(u"行", {}) if isinstance(store, dict) and isinstance(store.get(u"行"), dict) else {}
    out = {u"置き場に在る": [], u"新しく要る": [], u"計算で作る": []}
    for row in defn.rows:
        if row.get(u"取り方") == u"計算":
            out[u"計算で作る"].append(row[u"id"])
        elif row[u"id"] in srows:
            out[u"置き場に在る"].append(row[u"id"])
        else:
            out[u"新しく要る"].append(row[u"id"])
    return out


# ============================================================ 7 段目 資料
def group3(n):
    return u"{:,}".format(n)


def round_int(x, div):
    with decimal.localcontext(BIGCTX):
        return int((x / Decimal(div)).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def render_value(row, srow):
    u"""置き場の行 → 資料の字(数の字と単位の字)。"""
    unit = row.get(u"単位")
    v = Decimal(srow[u"値"])
    if unit == u"円" or row[u"id"] == u"b04":
        ch, div = (u"百万円", 1000000) if unit == u"円" else (u"円", 1)
        n = round_int(v, div)
        return (u"-" if n < 0 else u"") + group3(abs(n)) + ch
    if unit == u"純数":
        with decimal.localcontext(BIGCTX):
            q = (v * 100).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        return dec_text(q) + u"%"
    if unit == u"年":
        with decimal.localcontext(BIGCTX):
            q = v.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        return dec_text(q) + u"年"
    if unit == u"人":
        n = round_int(v, 1)
        return (u"-" if n < 0 else u"") + group3(abs(n)) + u"人"
    return dec_text(v)


def render_doc(defn, store):
    srows = store.get(u"行", {})
    lines = [u"# " + str(defn.raw.get(u"題", u"資料")), u"", u"## 数値", u""]
    for row in defn.rows:
        i = row[u"id"]
        s = srows.get(i, {})
        st = s.get(u"状態")
        if st == STATE_OK:
            body = render_value(row, s)
        elif st == STATE_NONE:
            body = u"無い"
        else:
            body = u"確認待ち"
        lines.append(u"- %s: %s[材料:%s]" % (row.get(u"名", i), body, i))
    return u"\n".join(lines) + u"\n"


TAG_NUM = re.compile(u"(?P<neg>[-△▲])?(?<![0-9])(?P<num>[0-9][0-9,]*(?:\\.[0-9]+)?)(?P<unit>%|百万円|千円|円|年|人)?\\[材料:(?P<id>[^\\]]*)\\]")
TAG_WORD = re.compile(u"(?P<word>無い|確認待ち)\\[材料:(?P<id>[^\\]]*)\\]")
TAG_ANY = re.compile(u"\\[材料:[^\\]]*\\]")
DATE_PATS = re.compile(u"[0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日|[0-9]{4}年[0-9]{1,2}月期|[0-9]{4}年[0-9]{1,2}月|[0-9]{1,2}月|[0-9]{4}/[0-9]{2}|[0-9]{4}-[0-9]{2}-[0-9]{2}")
HEAD_NUM = re.compile(u"^(?:#+\\s*)?[0-9]+[.)]?(?=\\s|$)")


def expected_text_parts(row, srow):
    u"""置き場の値から出る (数の字, 単位の字の許す集合, 小数の桁)。"""
    unit = row.get(u"単位")
    v = Decimal(srow[u"値"])
    if unit == u"円" or row[u"id"] == u"b04":
        return {ch: round_int(v, div) for ch, div in DOC_UNIT_DIV.items()}, 0
    if unit == u"純数":
        with decimal.localcontext(BIGCTX):
            return {u"%": (v * 100).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)}, 1
    if unit == u"年":
        with decimal.localcontext(BIGCTX):
            return {u"年": v.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)}, 1
    if unit == u"人":
        return {u"人": round_int(v, 1)}, 0
    return {}, 0


class DocCtx(object):
    pass


def doc_parse(defn, store, text):
    c = DocCtx()
    c.defn, c.text = defn, text
    c.srows = store.get(u"行", {}) if isinstance(store, dict) and isinstance(store.get(u"行"), dict) else {}
    c.num_tags = list(TAG_NUM.finditer(text))
    c.word_tags = list(TAG_WORD.finditer(text))
    c.spans = [m.span() for m in c.num_tags] + [m.span() for m in c.word_tags]
    c.tagged_ids = [m.group(u"id") for m in c.num_tags] + [m.group(u"id") for m in c.word_tags]
    covered = set()
    for a, b in c.spans:
        covered.update(range(a, b))
    c.bare = [m for m in TAG_ANY.finditer(text) if not any(k in covered for k in range(m.start(), m.end()))]
    for m in c.bare:
        c.tagged_ids.append(m.group(0)[len(u"[材料:"):-1])
    c.mism_words = 0
    return c


def doc_c1(c):
    u"""札の網羅: 定義表の行の全部が札で出る・定義表に無い id の札が無い・札の前に数も語も無い札が無い。"""
    reds = []
    for m in c.bare:
        reds.append({u"種類": u"札の前に数も語も無い", u"id": m.group(0)})
    for i in c.tagged_ids:
        if i not in c.defn.by_id:
            reds.append({u"種類": u"定義表に無い札", u"id": i})
    for row in c.defn.rows:
        if row[u"id"] not in c.tagged_ids:
            reds.append({u"種類": u"札が無い行", u"id": row[u"id"]})
    return reds


def doc_c2(c):
    u"""数の字: 単位の字・小数の桁・値が置き場の値から出る数と同じ。"""
    reds = []
    for m in c.num_tags:
        i = m.group(u"id")
        row = c.defn.by_id.get(i)
        s = c.srows.get(i, {})
        if row is None or s.get(u"状態") != STATE_OK:
            continue
        try:
            allowed, places = expected_text_parts(row, s)
        except (decimal.DecimalException, KeyError, ValueError, TypeError):
            reds.append({u"種類": u"置き場の値が読めない", u"id": i})
            continue
        unit = m.group(u"unit")
        if unit not in allowed:
            reds.append({u"種類": u"単位の字", u"id": i})
            continue
        digits = m.group(u"num")
        has_dec = u"." in digits
        if (places == 0 and has_dec) or (places == 1 and (not has_dec or len(digits.split(u".")[1]) != 1)):
            reds.append({u"種類": u"小数の桁", u"id": i})
            continue
        try:
            claimed = Decimal(digits.replace(u",", u""))
        except decimal.DecimalException:
            reds.append({u"種類": u"数の字", u"id": i})
            continue
        if m.group(u"neg"):
            claimed = -claimed
        if claimed != Decimal(allowed[unit]):
            reds.append({u"種類": u"値", u"id": i})
    return reds


def doc_c3(c):
    u"""置き場の状態: 在るでない行に数が在れば赤・在る行に無い・確認待ちと書けば赤(語の食い違いは数だけ)。"""
    reds = []
    for m in c.num_tags:
        i = m.group(u"id")
        if i in c.defn.by_id and c.srows.get(i, {}).get(u"状態") != STATE_OK:
            reds.append({u"種類": u"在るでない行に数", u"id": i})
    for m in c.word_tags:
        i = m.group(u"id")
        if i not in c.defn.by_id:
            continue
        st = c.srows.get(i, {}).get(u"状態")
        if st == STATE_OK:
            reds.append({u"種類": u"在る行に語", u"id": i})
        elif (st == STATE_NONE) != (m.group(u"word") == u"無い"):
            c.mism_words += 1
    return reds


def doc_c4(c):
    u"""結ばれていない数: 札の付いた数・日付・見出しの頭の番号を除いて数字が残れば赤。"""
    rest = []
    pos = 0
    for a, b in sorted(set(c.spans)):
        if a >= pos:
            rest.append(c.text[pos:a])
            pos = b
    rest.append(c.text[pos:])
    rest_text = DATE_PATS.sub(u"", TAG_ANY.sub(u"", u"".join(rest)))
    lines = [HEAD_NUM.sub(u"", ln) for ln in rest_text.split(u"\n")]
    free = re.findall(u"\\d+(?:[,.]\\d+)*", u"\n".join(lines))
    c.free = len(free)
    return [{u"種類": u"結ばれていない数", u"数": len(free)}] if free else []


#: 資料の検査の条(変異の門が 1 つずつ差し替える。戻しは try/finally)
DOC_RULES = {u"C1": doc_c1, u"C2": doc_c2, u"C3": doc_c3, u"C4": doc_c4}


def check_document(defn, store, text):
    u"""資料の検査。置き場と定義表と資料だけを読む。例外を出さない。"""
    if not isinstance(text, str):
        return {u"通った": False, u"赤": [{u"種類": u"資料が読めない"}], u"札の数": 0, u"結ばれていない数": 0, u"語の食い違い": 0}
    try:
        c = doc_parse(defn, store, text)
        c.free = 0
        reds = []
        for name in (u"C1", u"C2", u"C3", u"C4"):
            for r in DOC_RULES[name](c):
                r = dict(r)
                r[u"条"] = name
                reds.append(r)
        return {u"通った": not reds, u"赤": reds, u"札の数": len(c.tagged_ids), u"結ばれていない数": c.free, u"語の食い違い": c.mism_words}
    except (KeyError, TypeError, AttributeError, ValueError, RecursionError):
        return {u"通った": False, u"赤": [{u"種類": u"資料が読めない"}], u"札の数": 0, u"結ばれていない数": 0, u"語の食い違い": 0}


# ============================================================ 持ち越し(2 期目。席を使わない)
def index_letters(n):
    out = u""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        out = chr(65 + rem) + out
    return out


def period_json(exp):
    if exp[0] == u"時点":
        return {u"時点": exp[1].isoformat()}
    return {u"始まり": exp[1].isoformat(), u"終わり": exp[2].isoformat()}


def shift_period_json(p):
    u"""材料の ``期間`` を 1 年後へ(月の末日は末日へ)。読めなければ None。"""
    mp = mat_period(p)
    if mp is None:
        return None
    if mp[0] == u"時点":
        return {u"時点": shift_year(mp[1]).isoformat()}
    return {u"始まり": shift_year(mp[1]).isoformat(), u"終わり": shift_year(mp[2]).isoformat()}


def _carry_cell(src2, d, spec2, m):
    u"""``素材`` 1 つの持ち越し。戻りは (材料 か None, 理由)。"""
    s = m[u"出どころ"]
    f = src2.file(s.get(u"file"))
    if f is None:
        return None, u"file が無い"
    p = s.get(u"位置")
    if f[0] == "xlsx":
        if not isinstance(p, dict) or not isinstance(p.get(u"sheet"), str):
            return None, u"位置の形"
        grid = f[1].get(p[u"sheet"])
    else:
        grid = f[1]
    if grid is None:
        return None, u"sheet が無い"
    exp = expected_period(d, spec2)
    if exp is None:
        return None, u"期が決まらない"
    rowh = norm(s.get(u"行の見出し"))
    colh = norm(s.get(u"列の見出し"))
    mode = d.get(u"期の読み")
    hits = []
    for (r, c), v in sorted(grid.cells.items()):
        if cell_number(v) is None:
            continue
        rh, ch = row_heading(grid, r, c), col_heading(grid, r, c)
        if norm(rh) != rowh:
            continue
        if mode == u"要る":
            if read_period(ch, exp[0], spec2) != exp:
                continue
        elif norm(ch) != colh:
            continue
        hits.append((r, c, v, rh, ch))
    if not hits:
        return None, u"同じ見出しの数の cell が 0"
    if len(hits) > 1:
        return None, u"同じ見出しの数の cell が 2 つ以上"
    r, c, v, rh, ch = hits[0]
    mult = s.get(u"表示の倍率")
    val = cell_number(v) * mult
    if val.denominator != 1:
        return None, u"整数でない"
    pos = {u"sheet": p[u"sheet"], u"セル": u"%s%d" % (index_letters(c), r)} if f[0] == "xlsx" else {u"行": r, u"列": c}
    out = {u"id": m[u"id"], u"状態": STATE_OK, u"数値": str(int(val)), u"単位": m.get(u"単位"), u"期間": period_json(exp), u"範囲": m.get(u"範囲"),
           u"出どころ": {u"種類": u"素材", u"file": s[u"file"], u"位置": pos, u"行の見出し": head_text(rh), u"列の見出し": head_text(ch), u"表示の倍率": mult}}
    return out, u""


def _carry_sum(src2, d, spec2, m):
    s = m[u"出どころ"]
    f = src2.file(s.get(u"file"))
    if f is None or f[0] != "csv":
        return None, u"file が CSV でない"
    g = f[1]
    want_head = norm(s.get(u"列の見出し"))
    cands = []
    for c in range(1, g.maxc + 1):
        rows = [n for n in range(1, g.maxr + 1) if cell_number(g.get(n, c)) is not None
                and norm(head_text(g.get(n, 1)) if g.get(n, 1) is not None else u"") not in (u"合計", u"計")]
        if rows and norm(col_heading(g, rows[0], c)) == want_head:
            cands.append((c, rows))
    if not cands:
        return None, u"同じ列の見出しの列が 0"
    if len(cands) > 1:
        return None, u"同じ列の見出しの列が 2 つ以上"
    c, rows = cands[0]
    mult = s.get(u"表示の倍率")
    val = sum((cell_number(g.get(n, c)) for n in rows), Fraction(0)) * mult
    if val.denominator != 1:
        return None, u"整数でない"
    exp = expected_period(d, spec2)
    if exp is None:
        return None, u"期が決まらない"
    out = {u"id": m[u"id"], u"状態": STATE_OK, u"数値": str(int(val)), u"単位": m.get(u"単位"), u"期間": period_json(exp), u"範囲": m.get(u"範囲"),
           u"出どころ": {u"種類": u"素材の和", u"file": s[u"file"], u"列": c, u"行の並び": rows, u"列の見出し": head_text(col_heading(g, rows[0], c)), u"表示の倍率": mult}}
    return out, u""


def _carry_rows(src2, d, spec2, m):
    s = m[u"出どころ"]
    ns = json.loads(json.dumps(s))
    for c in ns[u"条件"]:
        if c[u"比べ方"] in (u"以上", u"以下"):
            dt = parse_date(c[u"値"])
            if dt is None:
                return None, u"日付の条件が読めない"
            c[u"値"] = shift_year(dt).isoformat()
    per = shift_period_json(m.get(u"期間"))
    if per is None:
        return None, u"期間が読めない"
    res, _g = select_file(src2, ns)
    if not res[0]:
        return None, res[1]
    val = res[3] * ns[u"表示の倍率"]
    if val.denominator != 1:
        return None, u"整数でない"
    out = {u"id": m[u"id"], u"状態": STATE_OK, u"数値": str(int(val)), u"単位": m.get(u"単位"), u"期間": per, u"範囲": m.get(u"範囲"), u"出どころ": ns}
    return out, u""


def carry(defn, spec2, prev_bundle, prev_result, marks, src2, ids=None):
    u"""1 期目の材料の束・検査の結果・印と ``期2/`` の素材から、2 期目の材料の束を作る。席を使わない。

    戻りは ``束``(型 u2)・``確認待ち``(id → 理由)・``持ち越した``・``無い``。作れない束(1 期目の束が読めない)は ``断り`` を返す。
    """
    items = {}
    if isinstance(prev_bundle, dict) and isinstance(prev_bundle.get(u"材料"), list):
        for m in prev_bundle[u"材料"]:
            if isinstance(m, dict) and isinstance(m.get(u"id"), str):
                items[m[u"id"]] = m
    verdict = {}
    if isinstance(prev_result, dict) and isinstance(prev_result.get(u"材料"), list):
        for r in prev_result[u"材料"]:
            if isinstance(r, dict) and isinstance(r.get(u"id"), str):
                verdict[r[u"id"]] = r
    want = sorted(ids) if ids is not None else sorted(items)
    out_items, waiting, carried, nones = [], {}, [], []
    for i in want:
        m, r, d = items.get(i), verdict.get(i), defn.by_id.get(i)
        if m is None or r is None or d is None:
            waiting[i] = u"1 期目の材料か検査の結果か定義表の行が無い"
            continue
        j = r.get(u"判定")
        if j == JUDGE_NONE_OK:
            out_items.append({u"id": i, u"状態": STATE_NONE, u"無い理由": NONE_REASON})
            nones.append(i)
            continue
        if j not in PASS_JUDGES:
            waiting[i] = u"1 期目で止まった"
            continue
        if i not in marks:
            waiting[i] = u"確かめた取り方の印が無い"
            continue
        if m.get(u"状態") != STATE_OK or not isinstance(m.get(u"出どころ"), dict):
            waiting[i] = u"1 期目の材料の形"
            continue
        try:
            kind = m[u"出どころ"].get(u"種類")
            if kind == u"素材":
                new, why = _carry_cell(src2, d, spec2, m)
            elif kind == u"素材の和":
                new, why = _carry_sum(src2, d, spec2, m)
            elif kind == KIND_ROWS:
                new, why = _carry_rows(src2, d, spec2, m)
            else:
                new, why = None, u"出どころの種類"
        except (KeyError, TypeError, AttributeError, ValueError, IndexError):
            new, why = None, u"1 期目の材料の形"
        if new is None:
            waiting[i] = why
        else:
            out_items.append(new)
            carried.append(i)
    out_items.sort(key=lambda x: x[u"id"])
    return {u"束": {u"型の版": TYPE_VERSION, u"材料": out_items}, u"確認待ち": waiting, u"持ち越した": carried, u"無い": nones}


# ============================================================ 人が読む版(7 段目の出口)
DIGITS = re.compile(u"[0-9\uff10-\uff19]+(?:[,.][0-9\uff10-\uff19]+)*")
HTML_BODY = re.compile(u"<main id=\"body\">(.*?)</main>", re.S)


def source_text(srow):
    u"""置き場の行の出どころを、file と位置か条件の数の字にする。"""
    s = srow.get(u"出どころ")
    if not isinstance(s, dict):
        return u"-"
    kind = s.get(u"種類")
    f = str(s.get(u"file"))
    if kind == u"素材":
        p = s.get(u"位置")
        if isinstance(p, dict) and u"セル" in p:
            return u"%s / %s!%s" % (f, p.get(u"sheet"), p.get(u"セル"))
        if isinstance(p, dict):
            return u"%s / %s 行 %s 列" % (f, p.get(u"行"), p.get(u"列"))
    if kind == u"素材の和":
        return u"%s / %s 列 の %d 行の和" % (f, s.get(u"列"), len(s.get(u"行の並び") or []))
    if kind == KIND_ROWS:
        return u"%s / 条件 %d 個" % (f, len(s.get(u"条件") or []))
    return u"-"


def period_text(row, srow):
    p = srow.get(u"期間")
    mp = mat_period(p) if isinstance(p, dict) else None
    label = str(row.get(u"期", u""))
    if mp is None:
        return label
    if mp[0] == u"時点":
        return u"%s(%s)" % (label, mp[1].isoformat())
    return u"%s(%s〜%s)" % (label, mp[1].isoformat(), mp[2].isoformat())


def build_html(defn, store, text):
    u"""札を外した本文と、数の出どころの表の HTML。資料の検査を通った資料からだけ組む(呼ぶ側が見る)。"""
    esc = html_lib.escape
    srows = store.get(u"行", {}) if isinstance(store, dict) and isinstance(store.get(u"行"), dict) else {}
    body, in_list = [], False
    for line in TAG_ANY.sub(u"", text).split(u"\n"):
        raw = line.rstrip()
        if raw.startswith(u"- "):
            if not in_list:
                body.append(u"<ul>")
                in_list = True
            body.append(u"<li>%s</li>" % esc(raw[2:]))
            continue
        if in_list:
            body.append(u"</ul>")
            in_list = False
        m = re.match(u"^(#{1,6})\\s+(.*)$", raw)
        if m:
            n = len(m.group(1))
            body.append(u"<h%d>%s</h%d>" % (n, esc(m.group(2)), n))
        elif raw.strip():
            body.append(u"<p>%s</p>" % esc(raw))
    if in_list:
        body.append(u"</ul>")
    rows = []
    for row in defn.rows:
        i = row[u"id"]
        sr = srows.get(i, {})
        st = sr.get(u"状態")
        if st == STATE_OK:
            val = render_value(row, sr)
            src = source_text(sr)
        elif st == STATE_NONE:
            val, src = u"無い", u"-"
        elif row.get(u"取り方") == u"計算" and st == u"保留":
            val, src = u"確認待ち", u"計算(%s)" % u"・".join(row.get(u"入力") or [])
        else:
            val, src = u"確認待ち", u"-"
        if row.get(u"取り方") == u"計算" and st == STATE_OK:
            src = u"計算(%s)" % u"・".join(row.get(u"入力") or [])
        rows.append(u"<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            esc(i), esc(str(row.get(u"名", i))), esc(val), esc(period_text(row, sr)), esc(str(st)), esc(src), u"未確認" if sr.get(u"未確認") else u"-"))
    head = u"<tr><th>id</th><th>名</th><th>値</th><th>期</th><th>状態</th><th>出どころ</th><th>未確認か</th></tr>"
    return (u"<!DOCTYPE html>\n<html lang=\"ja\"><head><meta charset=\"utf-8\"><title>%s</title></head><body>\n<main id=\"body\">\n%s\n</main>\n"
            u"<section id=\"sources\"><h2>数の出どころ</h2><table>%s%s</table></section>\n</body></html>\n") % (
        esc(str(defn.raw.get(u"題", u"資料"))), u"\n".join(body), head, u"".join(rows))


def make_human(defn, store, text):
    u"""戻りは (html か None, 資料の検査の結果)。資料の検査を通っていない資料からは組まない。"""
    res = check_document(defn, store, text)
    if not res[u"通った"]:
        return None, res
    return build_html(defn, store, text), res


def check_human(text, html_text):
    u"""人が読む版の検査: 本文の数の字の並びが札つきの資料と同じ・札が残っていない。"""
    if not isinstance(text, str) or not isinstance(html_text, str):
        return {u"通った": False, u"赤": [{u"種類": u"読めない"}]}
    m = HTML_BODY.search(html_text)
    if m is None:
        return {u"通った": False, u"赤": [{u"種類": u"本文が無い"}]}
    body = html_lib.unescape(re.sub(u"<[^>]*>", u"", m.group(1)))
    want = DIGITS.findall(TAG_ANY.sub(u"", text))
    got = DIGITS.findall(body)
    reds = []
    if want != got:
        reds.append({u"種類": u"数の字の並びが違う", u"札つきの資料": len(want), u"人が読む版": len(got)})
    if u"[材料:" in body:
        reds.append({u"種類": u"札が残っている"})
    return {u"通った": not reds, u"赤": reds}


# ============================================================ 命令
def parse_args(argv):
    opts, flags, i = {}, set(), 0
    while i < len(argv):
        a = argv[i]
        if a in ("--form-only",):
            flags.add(a)
            i += 1
        elif a.startswith("--") and i + 1 < len(argv):
            opts[a] = argv[i + 1]
            i += 2
        else:
            return None, None
    return opts, flags


def run(argv):
    if not argv:
        return {u"断り": u"命令が無い"}
    cmd = argv[0]
    opts, flags = parse_args(argv[1:])
    if opts is None:
        return {u"断り": u"命令の形"}
    if cmd == "material":
        if not all(k in opts for k in ("--spec", "--def", "--bundle", "--src")):
            return {u"断り": u"命令の形"}
        ids = [x for x in opts["--ids"].split(",") if x] if "--ids" in opts else None
        return check_files(opts["--spec"], opts["--def"], opts["--bundle"], opts["--src"], ids=ids, form_only="--form-only" in flags,
                           confirmed_path=opts.get("--confirmed"), prev_src_dir=opts.get("--prev-src"))
    defn = None
    if "--def" in opts:
        defn, err = load_def(opts["--def"])
        if defn is None:
            return {u"断り": err}
    if cmd == "store":
        if defn is None or "--result" not in opts or "--bundle" not in opts or "--product" not in opts:
            return {u"断り": u"命令の形"}
        result, _e1 = read_json(opts["--result"])
        bundle, _e2 = read_json(opts["--bundle"])
        prior = None
        if "--prior" in opts:
            prior, _e3 = read_json(opts["--prior"])
        ids = [x for x in opts["--ids"].split(",") if x] if "--ids" in opts else None
        waiting = None
        if "--waiting" in opts:
            wobj, _e4 = read_json(opts["--waiting"])
            if isinstance(wobj, dict) and isinstance(wobj.get(u"確認待ち"), dict):
                waiting = wobj[u"確認待ち"]
        return build_store(defn, result, bundle, opts["--product"], prior=prior, ids=ids, waiting=waiting)
    if cmd == "carry":
        need = ("--spec", "--prev-spec", "--prev-bundle", "--prev-result", "--marks", "--src")
        if defn is None or not all(k in opts for k in need):
            return {u"断り": u"命令の形"}
        spec2, err = load_spec(opts["--spec"])
        if spec2 is None:
            return {u"断り": err}
        spec1, err = load_spec(opts["--prev-spec"])
        if spec1 is None:
            return {u"断り": err}
        pb, e1 = read_json(opts["--prev-bundle"])
        pr, e2 = read_json(opts["--prev-result"])
        marks = read_marks(opts["--marks"])
        if e1 or e2 or marks is None:
            return {u"断り": u"1 期目の束・結果・印が読めない"}
        ids = [x for x in opts["--ids"].split(",") if x] if "--ids" in opts else None
        res = carry(defn, spec2, pb, pr, marks, Source(opts["--src"]), ids=ids)
        if "--out-bundle" in opts:
            try:
                with open(opts["--out-bundle"], "wb") as fh:
                    fh.write(dump_json(res[u"束"]).encode("utf-8", "backslashreplace"))
            except OSError:
                return {u"断り": u"出力先に書けない"}
        return res
    if cmd == "human-check":
        if "--doc" not in opts or "--html" not in opts:
            return {u"断り": u"命令の形"}
        text, e1 = read_text(opts["--doc"])
        page, e2 = read_text(opts["--html"])
        if e1 or e2:
            return {u"通った": False, u"赤": [{u"種類": u"読めない"}]}
        return check_human(text, page)
    if cmd in ("plan", "render", "document", "human"):
        if defn is None or "--store" not in opts:
            return {u"断り": u"命令の形"}
        store, err = read_json(opts["--store"])
        if err or not isinstance(store, dict):
            return {u"断り": u"置き場が読めない"}
        if cmd == "plan":
            return make_plan(defn, store)
        if cmd == "human":
            if "--doc" not in opts:
                return {u"断り": u"命令の形"}
            text, err = read_text(opts["--doc"])
            if err:
                return {u"組めた": False, u"赤": [{u"種類": u"資料が読めない"}]}
            page, res = make_human(defn, store, text)
            if page is None:
                return {u"組めた": False, u"赤": res[u"赤"]}
            return {u"組めた": True, u"html": page}
        if cmd == "render":
            return {u"markdown": render_doc(defn, store)}
        if "--doc" not in opts:
            return {u"断り": u"命令の形"}
        text, err = read_text(opts["--doc"])
        if err:
            return {u"通った": False, u"赤": [{u"種類": u"資料が読めない"}], u"札の数": 0, u"結ばれていない数": 0, u"語の食い違い": 0}
        return check_document(defn, store, text)
    return {u"断り": u"命令の名"}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    out_path = None
    if u"--out" in argv:
        k = argv.index(u"--out")
        if k + 1 < len(argv):
            out_path = argv[k + 1]
            del argv[k:k + 2]
    try:
        res = run(argv)
    except BaseException as exc:                 # noqa: BLE001
        if isinstance(exc, (KeyboardInterrupt,)):
            raise
        res = {u"内部の例外": type(exc).__name__}
    if out_path and isinstance(res, dict) and u"markdown" in res and argv and argv[0] == "render":
        body = res[u"markdown"]
    elif out_path and isinstance(res, dict) and res.get(u"組めた") is True and argv and argv[0] == "human":
        body = res[u"html"]
    else:
        body = dump_json(res)
    if out_path:
        try:
            with open(out_path, "wb") as fh:
                fh.write(body.encode("utf-8", "backslashreplace"))
        except OSError:
            sys.stdout.buffer.write(dump_json({u"断り": u"出力先に書けない"}).encode("utf-8", "backslashreplace") + b"\n")
    else:
        sys.stdout.buffer.write(body.encode("utf-8", "backslashreplace") + b"\n")
        sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
