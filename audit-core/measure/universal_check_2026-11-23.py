# -*- coding: utf-8 -*-
u"""封 docs/UNIVERSAL_MATERIAL_SEAL_2026-11-23.md(便 UM0)の「確かめる側」。**答えを読まない側。**

素材を作る側(``universal_source_gen_2026-11-23.py``)を import しない。読むのは指定・定義表・材料の束・素材の folder・置き場・資料だけ。
使う library は標準だけ(xlsx は zipfile と xml で読む。``python3 -I`` で動く)。**どんな入力でも例外で落ちず、rc 0 で結果の JSON を返す。**

    python3 -I universal_check_2026-11-23.py material --spec <指定.json> --def <定義表> --bundle <束> --src <素材の folder> [--ids a01,a02] [--form-only] [--out <file>]
    python3 -I universal_check_2026-11-23.py store    --def <定義表> --result <material の結果> --bundle <束> --product A [--prior <置き場>] [--ids ..] --out <file>
    python3 -I universal_check_2026-11-23.py plan     --def <定義表 B> --store <置き場> --out <file>
    python3 -I universal_check_2026-11-23.py render   --def <定義表> --store <置き場> --out <markdown>
    python3 -I universal_check_2026-11-23.py document --def <定義表> --store <置き場> --doc <markdown> --out <file>

実装の注(封の字では 1 通りに決まらなかった所の素直な読み。結果を見て変えない。報告にも書く):
- 期の読み(見出しの字 → 期)の「正規化」は、NFKC と空白の除去だけを先に掛けて読み、読めなければ頭の番号を取ってから読む(「2025年4月」の頭の数字を番号と取り違えない)。
- K3・K4 は素材から読み直した見出しで見る(申告の見出しで見ない。申告は K2 だけが見る)。
- K0 は id が頼まれた行とちょうど同じ(重複なし)だけを見て、並びの昇順は見ない。出どころの鍵は出どころ自身の種類で見て、定義表の取り方との食い違いは K3 で止める。
- 計算の行の入力に ``無い`` と ``確認待ち``・``保留`` が混ざれば ``無い``。資料の検査で ``無い`` の行が ``確認待ち`` と書かれていても(逆も)赤にしない(数を ``語の食い違い`` に残す)。
"""
from __future__ import print_function

import calendar
import csv
import datetime
import decimal
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

RULES = ("K0", "K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8", "K9")
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


def read_csv(path):
    try:
        with open(path, "rb") as fh:
            text = fh.read().decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(text, newline=u"")))
        return Grid(rows)
    except BaseException as exc:                 # noqa: BLE001
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        return None


class Source(object):
    u"""素材の folder。folder の直下の file だけ(名前に区切りを含む指定は読まない)。"""

    def __init__(self, folder):
        self.folder = folder
        self._names = None
        self._cache = {}
        self._texts = None

    def names(self):
        if self._names is None:
            try:
                self._names = sorted(os.listdir(self.folder))
            except OSError:
                self._names = []
        return self._names

    def file(self, name):
        u"""('xlsx', {sheet: Grid}) か ('csv', Grid) か None。"""
        if not isinstance(name, str) or name not in self.names():
            return None
        if name in self._cache:
            return self._cache[name]
        path = os.path.join(self.folder, name)
        res = None
        if os.path.isfile(path):
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
            u"素材の和": {u"種類", u"file", u"列", u"行の並び", u"列の見出し", u"表示の倍率"}}


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
    if not isinstance(s[u"file"], str) or not isinstance(s[u"列の見出し"], str):
        out.append(u"出どころの字")
    if not (is_int(s[u"表示の倍率"]) and s[u"表示の倍率"] in MULTS):
        out.append(u"表示の倍率")
    if s[u"種類"] == u"素材":
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
    if bundle[u"型の版"] != u"u0":
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
    if info[u"colh"] is None or norm(s.get(u"列の見出し")) != norm(info[u"colh"]):
        return True
    if s.get(u"種類") == u"素材" and (info[u"rowh"] is None or norm(s.get(u"行の見出し")) != norm(info[u"rowh"])):
        return True
    return False


def rule_k3(ctx, m, d, info):
    kind = m[u"出どころ"].get(u"種類")
    if kind != d.get(u"取り方"):
        return True
    if kind == u"素材":
        return info[u"k3"] not in (u"row", u"col")
    return info[u"k3"] != u"col"


def rule_k4(ctx, m, d, info):
    exp = expected_period(d, ctx.spec)
    if exp is None or mat_period(m.get(u"期間")) != exp:
        return True
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
        if r[u"状態"] == STATE_OK and not [x for x in r[u"規則"] if x in ("K1", "K2", "K3", "K4", "K5", "K6")]:
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


#: 差し替えられる規則の関数(変異の門が 1 つずつ差し替える。戻しは try/finally)
RULE_FUNCS = {u"K0": k0_bundle, u"K1": rule_k1, u"K2": rule_k2, u"K3": rule_k3, u"K4": rule_k4,
              u"K5": rule_k5, u"K6": rule_k6, u"K7": rule_k7, u"K8": rule_k8, u"K9": rule_k9}


class Ctx(object):
    pass


def check_bundle(spec, defn, bundle, src, ids=None, form_only=False):
    u"""材料の検査。例外を出さない。戻りは dict(``束`` ・ ``材料`` ・ ``K7``)。"""
    try:
        return _check_bundle(spec, defn, bundle, src, ids, form_only)
    except RecursionError:
        return refuse(u"K0", u"入れ子が深い")
    except (KeyError, TypeError, AttributeError, ValueError, IndexError) as exc:
        return refuse(u"K0", u"形が読めない: " + type(exc).__name__)


def _check_bundle(spec, defn, bundle, src, ids, form_only):
    ctx = Ctx()
    ctx.spec, ctx.defn, ctx.src = spec, defn, src
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
            results.append({u"id": m[u"id"], u"状態": m[u"状態"], u"判定": u"通す" if m[u"状態"] == STATE_OK else u"無いを受ける", u"規則": []})
            continue
        if d is None:
            results.append({u"id": m[u"id"], u"状態": m[u"状態"], u"判定": u"止める", u"規則": [u"K0"]})
            continue
        stops = []
        if m[u"状態"] == STATE_NONE:
            if RULE_FUNCS[u"K9"](ctx, d):
                stops.append(u"K9")
            results.append({u"id": m[u"id"], u"状態": STATE_NONE, u"判定": u"止める" if stops else u"無いを受ける", u"規則": stops})
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
        results.append({u"id": m[u"id"], u"状態": STATE_OK, u"判定": u"通す", u"規則": stops})
    k7 = {u"見た": 0, u"見なかった": 0}
    if not form_only:
        stop7, seen, unseen = RULE_FUNCS[u"K7"](ctx, results, by_id)
        k7 = {u"見た": seen, u"見なかった": unseen}
        for r in results:
            if r[u"id"] in stop7 and r[u"状態"] == STATE_OK:
                r[u"規則"] = r[u"規則"] + [u"K7"]
        for r in results:
            if r[u"状態"] == STATE_OK:
                r[u"規則"] = [x for x in RULES if x in r[u"規則"]]
                r[u"判定"] = u"止める" if r[u"規則"] else u"通す"
    return {u"束": {u"状態": u"受理", u"規則": [], u"理由": []}, u"材料": results, u"K7": k7}


def refuse(rule, reason):
    return {u"束": {u"状態": u"断り", u"規則": [rule], u"理由": [reason]}, u"材料": [], u"K7": {u"見た": 0, u"見なかった": 0}}


def check_files(spec_path, def_path, bundle_path, src_dir, ids=None, form_only=False):
    spec, err = load_spec(spec_path)
    if spec is None:
        return refuse(u"入力", err)
    defn, err = load_def(def_path)
    if defn is None:
        return refuse(u"入力", err)
    bundle, err = read_json(bundle_path)
    if err:
        return refuse(u"K0", u"束が読めない: " + err)
    return check_bundle(spec, defn, bundle, Source(src_dir), ids=ids, form_only=form_only)


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


def build_store(defn, result, bundle, product, prior=None, ids=None):
    u"""置き場。通った材料・無いを受けた行・止まった行(確認待ち)・計算の行。"""
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
        if refused or r is None:
            rows[i] = {u"状態": u"確認待ち", u"規則": [u"K0"], u"入った成果物": product}
        elif r.get(u"判定") == u"通す":
            rows[i] = {u"状態": STATE_OK, u"値": m.get(u"数値"), u"単位": m.get(u"単位"), u"期間": m.get(u"期間"),
                       u"範囲": m.get(u"範囲"), u"出どころ": m.get(u"出どころ"), u"入った成果物": product}
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
    return {u"版": u"u0-store", u"行": rows}


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


TAG_NUM = re.compile(u"(?P<neg>[-△▲])?(?P<num>[0-9][0-9,]*(?:\\.[0-9]+)?)(?P<unit>%|百万円|千円|円|年|人)?\\[材料:(?P<id>[^\\]]*)\\]")
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
        return check_files(opts["--spec"], opts["--def"], opts["--bundle"], opts["--src"], ids=ids, form_only="--form-only" in flags)
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
        return build_store(defn, result, bundle, opts["--product"], prior=prior, ids=ids)
    if cmd in ("plan", "render", "document"):
        if defn is None or "--store" not in opts:
            return {u"断り": u"命令の形"}
        store, err = read_json(opts["--store"])
        if err or not isinstance(store, dict):
            return {u"断り": u"置き場が読めない"}
        if cmd == "plan":
            return make_plan(defn, store)
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
