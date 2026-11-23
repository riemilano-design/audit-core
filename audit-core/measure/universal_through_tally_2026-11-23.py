# -*- coding: utf-8 -*-
u"""封 docs/UNIVERSAL_THROUGH_SEAL_2026-11-23.md(便 UM2)の「答えを知っている側」。

正解の file(``<company-dir>/<i>/正解/正解.json``)を読み、席の束・席の資料を、確かめる側(``universal_through_check_2026-11-23.py``。importlib で関数を呼ぶ)に掛けた結果と
突き合わせる。「確かめた取り方」の印を付ける(正解と同じ数値の材料。確かめる側は印だけを読む)・変異・集計・記録を作る。**費用は 0・API は呼ばない。席は呼ばない。**

    python3 universal_through_tally_2026-11-23.py --company-dir <dir> --seat-dir <dir> --companies 101 [--out <file>]       # 集計を JSON で出す(出力の folder に置き場などを書く)
    python3 universal_through_tally_2026-11-23.py --company-dir <dir> --seat-dir <dir> --record [--out <file>]              # 本番の 4 社(1〜4)がそろった時だけ記録を書く

folder の形(会社の番号 ``i`` ごと):
    ``<company-dir>/<i>/期1/``・``期2/``(素材)・``正解/正解.json``
    ``<seat-dir>/<i>/``: 司令塔が書く ``指定_期1_A.json``・``指定_期1_B.json``・``指定_期2_A.json``・``指定_期2_B.json``、席の出力 ``材料_期1_A.json``・``材料_期1_B.json``(b01 だけ)・
    ``資料_期1_A.md``・``資料_期2_A.md``。この script は ``出力/`` に判定・置き場・印・持ち越し・B の資料・人が読む版を書く。

実装の注(封の字では 1 通りに決まらなかった所の素直な読み。結果を見て変えない。報告にも書く):
- 正解の項目の名と定義表の id の対応は、定義表の名の字から決めて ``GOLD_KEYS`` に字で持つ(月次の売上高は 12 個の並びの k 番目が ``a(16+k)``)。値が整数でない項目は null と同じに扱い、数を残す。
- 正解の file で、鍵が無い・月次の並びが 12 に足りない・値が整数でも null でもない項目は ``正解が読めない項目`` に数える(null の行に入れない・
  「席の答えが正解と同じ」にならない・印を付けない)。素材から出せない項目として書かれた ``null`` だけを ``正解が null の行`` に数える。
- 「席の答えが正解と同じ」は、状態が同じで、在るなら数値が同じ(正解が null の行は、席が ``無い`` と書いた時だけ同じ)。束が断られた・材料が束に無い行は違う。
- 「確かめた取り方」の印は、1 期目に検査を通った(通す・通す(取り方は未確認))材料で、席が ``在る`` と書き、正解が null でなく、数値が正解と同じものに付ける。
- 「仕訳の行の数」は、素材の folder の中の CSV の最大の行の数(頭の行を除く。仕訳帳とみなす)。数だけを持ち、file の名は持たない。
- 変異 V2 は ``どれか`` の並びが 2 つ以上の条件だけ(``等しい`` は値が 1 つなので作れなかったに数える)。外す値は、外すと数値が変わる最初の値(どれも変わらなければ最初の値で、数値が同じに数える)。
  V3 は日付でない条件の最初の 1 つを外す。V4・V5 は日付の条件を全部 1 年前へ(月の末日は末日へ)。V6 は向き(か符号)を逆にする。
- 変異の材料は、1 期目の A の束(30 行)と B の束(b01)のうち、検査を通った(通す・通す(取り方は未確認))材料。
"""
from __future__ import print_function

import collections
import importlib.util
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CHECK_REL = "measure/universal_through_check_2026-11-23.py"
DEFS_REL = "fixtures/universal/um0"
RECORD_REL = "fixtures/universal/um2/record.json"

DEV = (101,)
PROD = (1, 2, 3, 4)
od = collections.OrderedDict

#: 正解の項目の名 → 定義表の id(当期末などの付いた名は素材を作る席への頼みの紙のとおり)
GOLD_KEYS = [
    (u"a01", u"売上高_当期"), (u"a02", u"売上高_前期"), (u"a03", u"売上総利益_当期"), (u"a04", u"営業利益_当期"), (u"a05", u"営業利益_前期"),
    (u"a06", u"経常利益_当期"), (u"a07", u"当期純利益_当期"), (u"a08", u"減価償却費_当期"), (u"a09", u"現金及び預金_当期末"),
    (u"a10", u"流動資産合計_当期末"), (u"a11", u"資産合計_当期末"), (u"a12", u"短期借入金_当期末"), (u"a13", u"長期借入金_当期末"),
    (u"a14", u"負債合計_当期末"), (u"a15", u"純資産合計_当期末"), (u"a16", u"純資産合計_前期末"),
    (u"a29", u"借入の残高の合計_当期末"), (u"a30", u"期末の従業員数_当期末"), (u"b01", u"人件費_当期"),
]
MONTH_KEY = u"月次の売上高_当期"
MONTH_IDS = [u"a%d" % (16 + k) for k in range(1, 13)]
A_IDS = [u"a%02d" % k for k in range(1, 31)]
ROW_IDS = A_IDS + [u"b01"]
RELATIONS = [(u"R1", MONTH_IDS, [u"a01"]), (u"R2", [u"a11"], [u"a14", u"a15"]), (u"R3", [u"a29"], [u"a12", u"a13"])]
RELATION_IDS = set(x for _n, l, r in RELATIONS for x in l + r)
MUT_PLAIN = (u"M1", u"M2", u"M4", u"M8")
MUT_ROWS = (u"V1", u"V2", u"V3", u"V4", u"V5", u"V6")
DOC_CODES = (u"D1", u"D4")
PERIODS = (u"期1", u"期2")


# ============================================================ 検査の file を読む
def load_check():
    spec = importlib.util.spec_from_file_location("universal_through_check_for_tally", os.path.join(ROOT, CHECK_REL))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def defn_of(chk, product):
    got, _err = chk.load_def(os.path.join(ROOT, DEFS_REL, "definition_%s.json" % product))
    return got


# ============================================================ 正解
#: 正解の file で読めなかった項目(鍵が無い・月次が足りない・値が整数でも null でもない)の値。null(素材から出せない)とは別の物
UNREADABLE = object()


def read_gold(path):
    u"""正解の file → ({期1: {id: 値か None か UNREADABLE}, 期2: ...}, 値が整数でなかった項目の数, {期1: 読めなかった id の集合, 期2: ...})。
    読めなければ (None, 0, None)。``None`` は正解の file が ``null`` と書いた項目だけ。"""
    try:
        with io.open(path, encoding="utf-8") as fh:
            obj = json.load(fh)
    except (OSError, ValueError, UnicodeDecodeError):
        return None, 0, None
    if not isinstance(obj, dict):
        return None, 0, None
    bad = 0
    out = {}
    unread = {}
    for per in PERIODS:
        body = obj.get(per)
        vals = dict((i, UNREADABLE) for i in ROW_IDS)
        if isinstance(body, dict):
            for ident, key in GOLD_KEYS:
                if key not in body:
                    continue
                v = body[key]
                if v is None:
                    vals[ident] = None
                elif isinstance(v, int) and not isinstance(v, bool):
                    vals[ident] = v
                else:
                    bad += 1
            if MONTH_KEY in body:
                months = body[MONTH_KEY]
                if isinstance(months, list):
                    for k in range(min(12, len(months))):
                        v = months[k]
                        if v is None:
                            vals[MONTH_IDS[k]] = None
                        elif isinstance(v, int) and not isinstance(v, bool):
                            vals[MONTH_IDS[k]] = v
                        else:
                            bad += 1
                elif months is None:
                    for ident in MONTH_IDS:
                        vals[ident] = None
                else:
                    bad += 1
        out[per] = vals
        unread[per] = set(i for i, v in vals.items() if v is UNREADABLE)
    return out, bad, unread


def relation_holds(vals, left, right):
    xs = [vals.get(i) for i in left + right]
    if any(not isinstance(x, int) or isinstance(x, bool) for x in xs):
        return False
    return sum(vals[i] for i in left) == sum(vals[i] for i in right)


# ============================================================ 席の出力の読み
def items_of(bundle):
    out = {}
    if isinstance(bundle, dict) and isinstance(bundle.get(u"材料"), list):
        for m in bundle[u"材料"]:
            if isinstance(m, dict) and isinstance(m.get(u"id"), str):
                out[m[u"id"]] = m
    return out


def same_answer(gold_value, m):
    u"""席の答えが正解と同じか。``m`` は席の材料(無ければ None)。"""
    if not isinstance(m, dict) or gold_value is UNREADABLE:
        return False
    if gold_value is None:
        return m.get(u"状態") == u"無い"
    if m.get(u"状態") != u"在る":
        return False
    try:
        return int(m.get(u"数値")) == gold_value
    except (TypeError, ValueError):
        return False


def value_equal(gold_value, m):
    if gold_value is None or gold_value is UNREADABLE or not isinstance(m, dict) or m.get(u"状態") != u"在る":
        return False
    try:
        return int(m.get(u"数値")) == gold_value
    except (TypeError, ValueError):
        return False


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False, indent=1) + u"\n")


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


# ============================================================ 変異
def judge_mutant(chk, res, ident, counter=None):
    u"""変異した材料 ``ident`` を検査がどう扱ったか。``断った``(束ごと)・``止めた``・``通した``(通す・通す(取り方は未確認))。"""
    if res[u"束"][u"状態"] != u"受理":
        return u"断った"
    row = [x for x in res[u"材料"] if x[u"id"] == ident]
    if not row or row[0][u"判定"] == chk.JUDGE_STOP:
        if counter is not None and row:
            counter[u"規則:" + u"+".join(row[0][u"規則"])] += 1
        return u"止めた"
    return u"通した"


def replace_item(bundle, ident, new):
    out = json.loads(json.dumps(bundle))
    out[u"材料"] = [new if m.get(u"id") == ident else m for m in out[u"材料"]]
    return out


def mutant_plain(chk, src, defn, spec, m, code):
    u"""素材・素材の和の材料の変異 M1・M2・M4・M8。作れなければ None。"""
    new = json.loads(json.dumps(m))
    if code == u"M1":
        new[u"数値"] = str(int(m[u"数値"]) + 1)
    elif code == u"M2":
        new[u"数値"] = str(int(m[u"数値"]) * 1000)
    elif code == u"M8":
        new = od([(u"id", m[u"id"]), (u"状態", u"無い"), (u"無い理由", u"素材が無い")])
    elif code == u"M4":
        s = m[u"出どころ"]
        d = defn.by_id.get(m[u"id"])
        f = src.file(s.get(u"file"))
        if d is None or s.get(u"種類") != u"素材" or f is None or f[0] != "xlsx" or d.get(u"期の読み") != u"要る":
            return None
        p = s.get(u"位置")
        grid = f[1].get(p.get(u"sheet")) if isinstance(p, dict) else None
        pos = chk.parse_addr(p.get(u"セル")) if isinstance(p, dict) else None
        exp = chk.expected_period(d, spec)
        if grid is None or pos is None or exp is None:
            return None
        r, c = pos
        for cc in range(1, grid.maxc + 1):
            if cc == c:
                continue
            v = grid.get(r, cc)
            n = chk.cell_number(v)
            if n is None:
                continue
            ch = chk.col_heading(grid, r, cc)
            per = chk.read_period(ch, exp[0], spec)
            if per is None or per == exp:
                continue
            val = n * s[u"表示の倍率"]
            if val.denominator != 1:
                continue
            new[u"出どころ"][u"位置"] = {u"sheet": p[u"sheet"], u"セル": u"%s%d" % (chk.index_letters(cc), r)}
            new[u"数値"] = str(int(val))
            new[u"出どころ"][u"列の見出し"] = chk.head_text(ch)
            break
        else:
            return None
    else:
        return None
    return new if new != m else None


def _recompute(chk, src, new):
    u"""``表の行の和`` の材料 ``new`` の 数値を、条件が選ぶ行から足し直す。足せなければ False。"""
    s = new[u"出どころ"]
    res, _g = chk.select_file(src, s)
    if not res[0]:
        return False
    val = res[3] * s[u"表示の倍率"]
    if val.denominator != 1:
        return False
    new[u"数値"] = str(int(val))
    return True


def mutant_rows(chk, src, m, code):
    u"""``表の行の和`` の材料の変異 V1〜V6。戻りは (材料 か None, 数値が元と同じか)。"""
    new = json.loads(json.dumps(m))
    s = new[u"出どころ"]
    conds = s[u"条件"]
    if code == u"V1":
        new[u"数値"] = str(int(m[u"数値"]) + 1)
        return new, False
    if code == u"V2":
        k = next((x for x, c in enumerate(conds) if c[u"比べ方"] == u"どれか" and len(c[u"値"]) >= 2), None)
        if k is None:
            return None, False
        first = None
        for drop in range(len(conds[k][u"値"])):
            trial = json.loads(json.dumps(new))
            trial[u"出どころ"][u"条件"][k][u"値"] = [v for x, v in enumerate(conds[k][u"値"]) if x != drop]
            if not _recompute(chk, src, trial):
                continue
            if first is None:
                first = trial
            if trial[u"数値"] != m[u"数値"]:
                return trial, False
        return (first, True) if first is not None else (None, False)
    if code == u"V3":
        k = next((x for x, c in enumerate(conds) if c[u"比べ方"] not in (u"以上", u"以下")), None)
        if k is None:
            return None, False
        s[u"条件"] = [c for x, c in enumerate(conds) if x != k]
    elif code in (u"V4", u"V5"):
        moved = False
        for c in s[u"条件"]:
            if c[u"比べ方"] in (u"以上", u"以下"):
                d = chk.parse_date(c[u"値"])
                if d is None:
                    return None, False
                c[u"値"] = chk.shift_year(d, -1).isoformat()
                moved = True
        if not moved:
            return None, False
        if code == u"V5":
            per = chk.mat_period(m.get(u"期間"))
            if per is None:
                return None, False
            if per[0] == u"時点":
                new[u"期間"] = {u"時点": chk.shift_year(per[1], -1).isoformat()}
            else:
                new[u"期間"] = {u"始まり": chk.shift_year(per[1], -1).isoformat(), u"終わり": chk.shift_year(per[2], -1).isoformat()}
    elif code == u"V6":
        a = s[u"額"]
        if u"符号" in a:
            a[u"符号"] = u"逆" if a[u"符号"] == u"そのまま" else u"そのまま"
        else:
            a[u"向き"] = chk.DIRECTIONS[1] if a[u"向き"] == chk.DIRECTIONS[0] else chk.DIRECTIONS[0]
    else:
        return None, False
    if not _recompute(chk, src, new):
        return None, False
    if new == m:
        return None, False
    return new, new[u"数値"] == m[u"数値"]


def tally_mutants(chk, defn, spec, bundle, res, src, counters):
    u"""1 期目の 1 つの束(検査を通した材料)に変異を 1 つずつ当てる。``counters`` は ``コード → Counter``。"""
    items = items_of(bundle)
    for r in res[u"材料"]:
        ident = r[u"id"]
        m = items.get(ident)
        if r[u"判定"] not in chk.PASS_JUDGES or m is None or m.get(u"状態") != u"在る":
            continue
        kind = m[u"出どころ"][u"種類"]
        codes = MUT_ROWS if kind == chk.KIND_ROWS else MUT_PLAIN
        for code in codes:
            row = counters[code]
            if kind == chk.KIND_ROWS:
                new, same_value = mutant_rows(chk, src, m, code)
            else:
                new, same_value = mutant_plain(chk, src, defn, spec, m, code), False
            if new is None:
                row[u"作れなかった"] += 1
                continue
            if same_value:
                row[u"数値が同じ"] += 1
                continue
            row[u"作れた"] += 1
            where = u"関係に入る" if ident in RELATION_IDS else u"関係に入らない"
            if code in (u"V2", u"V3", u"V6"):
                row[u"作れた:" + where] += 1
            rr = chk.check_bundle(spec, defn, replace_item(bundle, ident, new), src, ids=sorted(items))
            verdict = judge_mutant(chk, rr, ident, row)
            row[verdict] += 1
            if code in (u"V2", u"V3", u"V6") and verdict == u"通した":
                row[u"通した:" + where] += 1


_NUMTAG = re.compile(u"(?P<neg>[-△▲])?(?<![0-9])(?P<num>[0-9][0-9,]*(?:\\.[0-9]+)?)(?P<unit>%|百万円|千円|円|年|人)?\\[材料:(?P<id>[^\\]]*)\\]")
_WORDTAG = re.compile(u"(?P<word>無い|確認待ち)\\[材料:(?P<id>[^\\]]*)\\]")


def doc_mutants(text):
    u"""資料の変異 D1(数字 1 つを別の数字に)・D4(札を消す)。``(コード, 通し番号, 変異した字)`` の並び。"""
    out = []
    nums = list(_NUMTAG.finditer(text))
    words = list(_WORDTAG.finditer(text))
    for k, m in enumerate(nums):
        a, b = m.span(u"num")
        s = text[a:b]
        pos = next((x for x, ch in enumerate(s) if ch.isdigit()), None)
        new = None
        if pos is not None:
            new = text[:a] + s[:pos] + str((int(s[pos]) + 1) % 10) + s[pos + 1:] + text[b:]
        out.append((u"D1", k, new if new != text else None))
    for k, m in enumerate(nums + words):
        mm = re.search(u"\\[材料:%s\\]" % re.escape(m.group(u"id")), text[m.start():])
        a = m.start() + mm.start()
        b = m.start() + mm.end()
        out.append((u"D4", k, text[:a] + text[b:]))
    return out


# ============================================================ 1 社ぶんの流れ
def refused_result(chk, reason):
    return chk.refuse(u"K0", reason)


def read_bundle(chk, path):
    u"""席の束 → (束, 検査に掛ける束, 席の出力が在ったか)。読めなければ束は {} で、検査は断る。"""
    if not os.path.exists(path):
        return None, None, False
    obj, err = chk.read_json(path)
    if err:
        return None, None, True
    return obj, obj, True


def count_files(chk, folder):
    src = chk.Source(folder)
    names = src.names()
    kinds = collections.Counter()
    most = 0
    for n in names:
        low = n.lower()
        kinds[u"CSV" if low.endswith(".csv") else (u"xlsx" if low.endswith(".xlsx") else u"その他")] += 1
        if low.endswith(".csv"):
            f = src.file(n)
            if f is not None:
                most = max(most, f[1].maxr - 1)
    return len(names), kinds, most


class CompanyRun(object):
    u"""会社 1 社の流れの途中の物(置き場・判定・束)。"""


def run_company(chk, i, company_dir, seat_dir, c, mut, per_company):
    u"""会社 ``i`` を流して数を ``c``(Counter)と ``mut``(変異の Counter の辞書)へ足す。出力の folder へ中間の file を書く。"""
    cdir = os.path.join(company_dir, str(i))
    sdir = os.path.join(seat_dir, str(i))
    odir = os.path.join(sdir, u"出力")
    defA, defB = defn_of(chk, u"A"), defn_of(chk, u"B")
    gold, bad, unread = read_gold(os.path.join(cdir, u"正解", u"正解.json"))
    c[u"正解の値が整数でない項目"] += bad
    if gold is None:
        c[u"正解が読めない社"] += 1
        return
    pc = per_company.setdefault(str(i), collections.Counter())
    # ---- 段 0
    for name, left, right in RELATIONS:
        for per in PERIODS:
            c[u"関係の本数"] += 1
            if relation_holds(gold[per], left, right):
                c[u"関係が成り立つ本数"] += 1
    for per in PERIODS:
        c[u"正解が null の行:" + per] += sum(1 for k in ROW_IDS if gold[per][k] is None)
        c[u"正解が読めない項目:" + per] += len(unread[per])
        n, kinds, most = count_files(chk, os.path.join(cdir, per))
        c[u"素材の file の数:" + per] += n
        for k, v in kinds.items():
            c[u"素材の file の形式:" + k + u":" + per] += v
        c[u"最大の CSV の行の数:" + per] = max(c.get(u"最大の CSV の行の数:" + per, 0), most)
    src = {}
    specs = {}
    for per in PERIODS:
        src[per] = chk.Source(os.path.join(cdir, per))
        for prod in (u"A", u"B"):
            sp, _e = chk.load_spec(os.path.join(sdir, u"指定_%s_%s.json" % (per, prod)))
            specs[(per, prod)] = sp
            if sp is None:
                c[u"指定なし"] += 1
    if any(v is None for v in specs.values()):
        return
    material_ids = chk.material_ids(defA)
    # ---- 段 1(1 期目)
    bundleA, _x, haveA = read_bundle(chk, os.path.join(sdir, u"材料_期1_A.json"))
    bundleB, _y, haveB = read_bundle(chk, os.path.join(sdir, u"材料_期1_B.json"))
    if not haveA:
        c[u"席の出力なし:材料_期1_A"] += 1
    if not haveB:
        c[u"席の出力なし:材料_期1_B"] += 1
    resA1 = chk.check_bundle(specs[(u"期1", u"A")], defA, bundleA, src[u"期1"]) if bundleA is not None else refused_result(chk, u"束が無いか読めない")
    storeA1 = chk.build_store(defA, resA1, bundleA, u"A")
    plan1 = chk.make_plan(defB, storeA1)
    new_ids = plan1[u"新しく要る"]
    resB1 = chk.check_bundle(specs[(u"期1", u"B")], defB, bundleB, src[u"期1"], ids=new_ids) if bundleB is not None else refused_result(chk, u"束が無いか読めない")
    storeB1 = chk.build_store(defB, resB1, bundleB, u"B", prior=storeA1, ids=new_ids)
    write_json(os.path.join(odir, u"判定_期1_A.json"), resA1)
    write_json(os.path.join(odir, u"判定_期1_B.json"), resB1)
    write_json(os.path.join(odir, u"置き場_期1_A.json"), storeA1)
    write_json(os.path.join(odir, u"置き場_期1_B.json"), storeB1)
    seat_items = {}
    seat_items.update(items_of(bundleA))
    seat_items.update(items_of(bundleB))
    verd1 = {}
    for r in resA1[u"材料"] + resB1[u"材料"]:
        verd1[r[u"id"]] = r
    refused_ids = set()
    if resA1[u"束"][u"状態"] != u"受理":
        c[u"束が K0 で断られた束"] += 1
        refused_ids |= set(A_IDS)
    if resB1[u"束"][u"状態"] != u"受理":
        c[u"束が K0 で断られた束"] += 1
        refused_ids.add(u"b01")
    marks = []
    for k in ROW_IDS:
        g = gold[u"期1"][k]
        m = seat_items.get(k) if k not in refused_ids else None
        c[u"段 1:行の数"] += 1
        same = same_answer(g, m)
        c[u"段 1:席の答えが正解と同じ"] += 1 if same else 0
        r = verd1.get(k) if k not in refused_ids else None
        if r is None:
            c[u"段 1:検査の結果:束ごとの断り"] += 1
            passed = False
        else:
            c[u"段 1:検査の結果:" + r[u"判定"]] += 1
            passed = r[u"判定"] in chk.PASS_JUDGES or r[u"判定"] == chk.JUDGE_NONE_OK
            for rule in r[u"規則"]:
                c[u"段 1:止めた行の規則:" + rule] += 1
            if r[u"判定"] == chk.JUDGE_STOP:
                c[u"段 1:止めた行の規則の組:" + u"+".join(r[u"規則"])] += 1
        c[u"段 1:4 つの枠:" + (u"正解どおり" if same else u"正解と違う") + u"×" + (u"通した" if passed else u"止めた")] += 1
        if m is not None and m.get(u"状態") == u"在る":
            c[u"段 1:席が在ると書いた行"] += 1
            kind = (m.get(u"出どころ") or {}).get(u"種類") if isinstance(m.get(u"出どころ"), dict) else None
            c[u"段 1:出どころの種類:" + (kind if kind in (u"素材", u"素材の和", chk.KIND_ROWS) else u"その他")] += 1
        elif m is not None and m.get(u"状態") == u"無い":
            c[u"段 1:席が無いと書いた行"] += 1
        if r is not None and r[u"判定"] in chk.PASS_JUDGES and m is not None and m.get(u"状態") == u"在る":
            if g is None:
                c[u"段 1:通したが正解が null"] += 1
            elif g is UNREADABLE:
                c[u"段 1:通したが正解が読めない"] += 1
            elif not value_equal(g, m):
                c[u"段 1:通したが数値が違う"] += 1
            else:
                marks.append(k)
        if r is not None and r[u"判定"] == chk.JUDGE_STOP and same:
            c[u"段 1:正解どおりなのに止めた"] += 1
    c[u"段 1:K3 で止まった行"] += sum(1 for r in verd1.values() if r[u"判定"] == chk.JUDGE_STOP and u"K3" in r[u"規則"])
    marks = sorted(marks)
    write_json(os.path.join(odir, u"印_期1.json"), {u"確かめた取り方": marks})
    confirmed = set(marks)
    # ---- 変異(1 期目の席の束のうち検査を通った材料)
    if bundleA is not None and resA1[u"束"][u"状態"] == u"受理":
        tally_mutants(chk, defA, specs[(u"期1", u"A")], bundleA, resA1, src[u"期1"], mut)
    if bundleB is not None and resB1[u"束"][u"状態"] == u"受理":
        tally_mutants(chk, defB, specs[(u"期1", u"B")], bundleB, resB1, src[u"期1"], mut)
    # ---- 段 2(2 期目。席を使わない)
    c[u"段 2:確かめた取り方の行"] += len(marks)
    carriedA = chk.carry(defA, specs[(u"期2", u"A")], bundleA, resA1, confirmed, src[u"期2"], ids=material_ids)
    bundleA2 = carriedA[u"束"]
    idsA2 = [x[u"id"] for x in bundleA2[u"材料"]]
    resA2 = chk.check_bundle(specs[(u"期2", u"A")], defA, bundleA2, src[u"期2"], ids=idsA2, confirmed=confirmed, prev_src=src[u"期1"])
    storeA2 = chk.build_store(defA, resA2, bundleA2, u"A", ids=material_ids, waiting=carriedA[u"確認待ち"])
    plan2 = chk.make_plan(defB, storeA2)
    new2 = plan2[u"新しく要る"]
    carriedB = chk.carry(defB, specs[(u"期2", u"B")], bundleB, resB1, confirmed, src[u"期2"], ids=new2)
    bundleB2 = carriedB[u"束"]
    idsB2 = [x[u"id"] for x in bundleB2[u"材料"]]
    resB2 = chk.check_bundle(specs[(u"期2", u"B")], defB, bundleB2, src[u"期2"], ids=idsB2, confirmed=confirmed, prev_src=src[u"期1"])
    storeB2 = chk.build_store(defB, resB2, bundleB2, u"B", prior=storeA2, ids=new2, waiting=carriedB[u"確認待ち"])
    write_json(os.path.join(odir, u"持ち越し_A.json"), carriedA)
    write_json(os.path.join(odir, u"持ち越し_B.json"), carriedB)
    write_json(os.path.join(odir, u"判定_期2_A.json"), resA2)
    write_json(os.path.join(odir, u"判定_期2_B.json"), resB2)
    write_json(os.path.join(odir, u"置き場_期2_A.json"), storeA2)
    write_json(os.path.join(odir, u"置き場_期2_B.json"), storeB2)
    gold2 = gold[u"期2"]
    stopped_k11 = 0
    for carried, res, bundle in ((carriedA, resA2, bundleA2), (carriedB, resB2, bundleB2)):
        items2 = items_of(bundle)
        if res[u"束"][u"状態"] != u"受理":
            c[u"段 2:束が K0 で断られた束"] += 1
        c[u"段 2:持ち越した行"] += len(carried[u"持ち越した"])
        c[u"段 2:無いを持ち越した行"] += len(carried[u"無い"])
        for why in carried[u"確認待ち"].values():
            c[u"段 2:持ち越せなかった行:" + why] += 1
            c[u"段 2:持ち越せなかった行"] += 1
        for r in res[u"材料"]:
            k = r[u"id"]
            if k in carried[u"持ち越した"]:
                c[u"段 2:検査の結果:" + r[u"判定"]] += 1
                if r[u"判定"] in chk.PASS_JUDGES:
                    c[u"段 2:持ち越して検査を通った行"] += 1
                    g = gold2[k]
                    if g is None:
                        c[u"段 2:持ち越して通したが正解が null"] += 1
                    elif g is UNREADABLE:
                        c[u"段 2:持ち越して通したが正解が読めない"] += 1
                    elif value_equal(g, items2.get(k)):
                        c[u"段 2:持ち越して通して正解と数値が同じ"] += 1
                    else:
                        c[u"段 2:持ち越して通したが数値が違う"] += 1
                else:
                    for rule in r[u"規則"]:
                        c[u"段 2:止めた行の規則:" + rule] += 1
                if u"K11" in r[u"規則"]:
                    stopped_k11 += 1
            elif k in carried[u"無い"]:
                c[u"段 2:検査の結果:" + r[u"判定"] + u":無いの行"] += 1
    c[u"段 2:K11 で止めた行"] += stopped_k11
    pc[u"K11 で止めた行"] += stopped_k11
    if stopped_k11:
        c[u"段 2:K11 で止めた社"] += 1
    # ---- 段 3(資料と人が読む版)
    built = collections.Counter()
    docs = [(u"期1", u"A", storeA1, defA), (u"期1", u"B", storeB1, defB), (u"期2", u"A", storeA2, defA), (u"期2", u"B", storeB2, defB)]
    for per, prod, store, defn in docs:
        tag = u"%s・%s" % (per, prod)
        if prod == u"A":
            text, err = chk.read_text(os.path.join(sdir, u"資料_%s_A.md" % per))
            if err is not None:
                c[u"段 3:資料なし:" + tag] += 1
                continue
        else:
            text = chk.render_doc(defn, store)
            write_text(os.path.join(odir, u"資料_%s_B.md" % per), text)
        res = chk.check_document(defn, store, text)
        c[u"段 3:資料の検査を通した:" + tag] += 1 if res[u"通った"] else 0
        c[u"段 3:結ばれていない数:" + tag] += res[u"結ばれていない数"]
        # 数える単位は 2 つ。札の出現の数(同じ id が資料に何度出ても数える)と、定義表の行(id)の数(重複を除く)。
        # 封 UM2-D2 の「行」は定義表の行(id)。1 つの id が数と確認待ち・無いの両方に出る場合は、封の字
        # 「確認待ち・無い でない行」に沿い、数の札が 1 つでも在れば「数が出ている」、無ければ確認待ちの札が在れば「確認待ち」、
        # どちらも無ければ「無い」に 1 回だけ入れる(1 つの id は 3 つのうち 1 つにしか入らない)。
        # 定義表に無い id の札は定義表の行に数えず、別の欄に数える。3 つの和が定義表の行の数になること(閉じること)は記録の欄で見る。
        nums_m = list(_NUMTAG.finditer(text))
        words_m = list(_WORDTAG.finditer(text))
        def_ids = set(r[u"id"] for r in defn.rows)
        s_num = set(m.group(u"id") for m in nums_m)
        s_wait = set(m.group(u"id") for m in words_m if m.group(u"word") == u"確認待ち") - s_num
        s_none = set(m.group(u"id") for m in words_m if m.group(u"word") == u"無い") - s_num - s_wait
        c[u"段 3:数の札の出現の数:" + tag] += len(nums_m)
        c[u"段 3:確認待ちの札の出現の数:" + tag] += sum(1 for w in words_m if w.group(u"word") == u"確認待ち")
        c[u"段 3:無いの札の出現の数:" + tag] += sum(1 for w in words_m if w.group(u"word") == u"無い")
        c[u"段 3:定義表の行:" + tag] += len(def_ids)
        c[u"段 3:数が出ている定義表の行:" + tag] += len(s_num & def_ids)
        c[u"段 3:確認待ちの定義表の行:" + tag] += len(s_wait & def_ids)
        c[u"段 3:無いの定義表の行:" + tag] += len(s_none & def_ids)
        c[u"段 3:定義表の行のうち数・確認待ち・無いのどれにも入らない行:" + tag] += len(def_ids - s_num - s_wait - s_none)
        c[u"段 3:定義表に無い id の札の id の数:" + tag] += len((s_num | s_wait | s_none) - def_ids)
        if prod == u"A" and per == u"期2":
            c[u"段 3:A の 2 期目の資料で数が出ている行"] += len(s_num & def_ids)
            c[u"段 3:A の 2 期目の資料で数の札の出現の数"] += len(nums_m)
        if not res[u"通った"]:
            continue
        page, _r = chk.make_human(defn, store, text)
        if page is None:
            continue
        c[u"段 3:人が読む版が組めた:" + tag] += 1
        write_text(os.path.join(odir, u"人が読む版_%s_%s.html" % (per, prod)), page)
        hc = chk.check_human(text, page)
        if hc[u"通った"]:
            c[u"段 3:人が読む版の検査を通した:" + tag] += 1
            built[(per, prod)] = 1
        for code, k, new in doc_mutants(text):
            if new is None:
                mut[code][u"作れなかった"] += 1
                continue
            mut[code][u"作れた"] += 1
            if chk.check_document(defn, store, new)[u"通った"]:
                mut[code][u"通した"] += 1
            else:
                mut[code][u"止めた"] += 1
    ok1 = built[(u"期1", u"A")] and built[(u"期1", u"B")]
    ok2 = built[(u"期2", u"A")] and built[(u"期2", u"B")]
    c[u"通し:期1"] += 1 if ok1 else 0
    c[u"通し:期2"] += 1 if ok2 else 0
    c[u"通し:期1・期2とも"] += 1 if (ok1 and ok2) else 0
    pc[u"通し:期1"] += 1 if ok1 else 0
    pc[u"通し:期2"] += 1 if ok2 else 0


FIXED_COUNTS = (
    u"関係の本数", u"関係が成り立つ本数", u"正解の値が整数でない項目", u"正解が読めない社", u"指定なし", u"束が K0 で断られた束",
    u"段 1:行の数", u"段 1:席の答えが正解と同じ", u"段 1:席が在ると書いた行", u"段 1:席が無いと書いた行", u"段 1:通したが数値が違う", u"段 1:通したが正解が null", u"段 1:通したが正解が読めない",
    u"段 1:正解どおりなのに止めた", u"段 1:K3 で止まった行",
    u"段 1:検査の結果:通す", u"段 1:検査の結果:通す(取り方は未確認)", u"段 1:検査の結果:止める", u"段 1:検査の結果:無いを受ける", u"段 1:検査の結果:束ごとの断り",
    u"段 1:出どころの種類:素材", u"段 1:出どころの種類:素材の和", u"段 1:出どころの種類:表の行の和",
    u"段 1:4 つの枠:正解どおり×通した", u"段 1:4 つの枠:正解どおり×止めた", u"段 1:4 つの枠:正解と違う×通した", u"段 1:4 つの枠:正解と違う×止めた",
    u"段 2:確かめた取り方の行", u"段 2:束が K0 で断られた束", u"段 2:持ち越した行", u"段 2:無いを持ち越した行", u"段 2:持ち越せなかった行", u"段 2:持ち越して検査を通った行",
    u"段 2:持ち越して通して正解と数値が同じ", u"段 2:持ち越して通したが数値が違う", u"段 2:持ち越して通したが正解が null", u"段 2:持ち越して通したが正解が読めない", u"段 2:K11 で止めた行", u"段 2:K11 で止めた社",
    u"段 3:A の 2 期目の資料で数が出ている行", u"段 3:A の 2 期目の資料で数の札の出現の数", u"通し:期1", u"通し:期2", u"通し:期1・期2とも",
) + tuple(u"%s:%s" % (a, p) for a in (u"段 3:資料の検査を通した", u"段 3:人が読む版が組めた", u"段 3:人が読む版の検査を通した") for p in (u"期1・A", u"期1・B", u"期2・A", u"期2・B")) + tuple(
    u"段 3:%s:%s" % (a, p) for a in (u"結ばれていない数", u"数の札の出現の数", u"確認待ちの札の出現の数", u"無いの札の出現の数", u"定義表の行", u"数が出ている定義表の行", u"確認待ちの定義表の行", u"無いの定義表の行", u"定義表の行のうち数・確認待ち・無いのどれにも入らない行", u"定義表に無い id の札の id の数") for p in (u"期1・A", u"期1・B", u"期2・A", u"期2・B")) + tuple(
    u"%s:%s" % (a, p) for a in (u"正解が null の行", u"正解が読めない項目", u"素材の file の数") for p in PERIODS)


def tally(companies, company_dir, seat_dir, chk=None):
    u"""集計(数だけ)。出力の folder(``<seat-dir>/<i>/出力/``)に中間の file を書く。"""
    chk = chk or load_check()
    c = collections.Counter()
    mut = od((code, collections.Counter()) for code in MUT_PLAIN + MUT_ROWS + DOC_CODES)
    per_company = od()
    for i in companies:
        run_company(chk, i, company_dir, seat_dir, c, mut, per_company)
    for key in FIXED_COUNTS:
        c.setdefault(key, 0)
    for code, row in mut.items():
        # 資料の変異(D1・D4)は作れた = 通した + 止めた を数える。断る段は無いので「断った」は出さない(数えていない 0 を記録に出さない)。
        keys = (u"作れた", u"作れなかった", u"止めた", u"通した") if code in DOC_CODES else (u"作れた", u"作れなかった", u"断った", u"止めた", u"通した")
        for key in keys + ((u"数値が同じ",) if code in MUT_ROWS else ()):
            row.setdefault(key, 0)
        if code in (u"V2", u"V3", u"V6"):
            for key in (u"作れた:関係に入る", u"作れた:関係に入らない", u"通した:関係に入る", u"通した:関係に入らない"):
                row.setdefault(key, 0)
    for per in PERIODS:
        for k in (u"最大の CSV の行の数:" + per,):
            c.setdefault(k, 0)
    return od([(u"会社の数", len(list(companies))), (u"数", dict(sorted(c.items()))), (u"変異", od((k, dict(sorted(v.items()))) for k, v in mut.items())),
               (u"会社ごと", od((k, dict(sorted(v.items()))) for k, v in per_company.items()))])


#: 封 §3 の表の境の数(字で持つ。結果を見て動かさない)。``(下限, 上限)``。None は境が無い。
BOUNDS = od([
    (u"UM2-S1", {u"関係が成り立つ本数": (22, None), u"関係の本数": (24, 24)}),
    (u"UM2-S2", {u"正解が null の行:期1": (4, 30)}),
    (u"UM2-P1", {u"段 1:席の答えが正解と同じ": (93, None), u"段 1:行の数": (124, 124)}),
    (u"UM2-P2", {u"割合の下限(百分率)": (30, None)}),
    (u"UM2-P3", {u"段 1:通したが数値が違う": (1, None)}),
    (u"UM2-P4", {u"段 1:K3 で止まった行": (10, None)}),
    (u"UM2-P5", {u"束が K0 で断られた束": (0, 0)}),
    (u"UM2-Q1", {u"割合の下限(百分率)": (80, None)}),
    (u"UM2-Q2", {u"段 2:持ち越して通したが数値が違う": (0, 0)}),
    (u"UM2-Q3", {u"段 2:K11 で止めた社": (1, None)}),
    (u"UM2-D1", {u"資料の検査を通した本数": (13, 16)}),
    (u"UM2-D2", {u"割合の下限(百分率)": (60, None), u"段 3:A の 2 期目の資料で数が出ている行": (None, 132)}),
    (u"UM2-E1", {u"通し:期1・期2とも": (3, 4)}),
    (u"UM2-V1", {u"通した = 作れた(関係に入らない行)": (None, None)}),
    (u"UM2-V2", {u"V1・V4 で作れたもののうち通した": (0, 0)}),
])


def judge(rec):
    u"""記録の ``数``・``変異`` から予測の当たり外れを境の数で決める。戻りは ``id → {当たり: True/False/None, 数: ...}``(None は判定できない)。"""
    c = rec.get(u"数", {})
    m = rec.get(u"変異", {})
    out = od()

    def put(key, ok, **detail):
        out[key] = od([(u"当たり", ok)] + list(detail.items()))

    put(u"UM2-S1", c.get(u"関係の本数") == 24 and c.get(u"関係が成り立つ本数", 0) >= 22, 数=c.get(u"関係が成り立つ本数", 0))
    nul = c.get(u"正解が null の行:期1", 0)
    put(u"UM2-S2", 4 <= nul <= 30, 数=nul)
    put(u"UM2-P1", c.get(u"段 1:席の答えが正解と同じ", 0) >= 93, 数=c.get(u"段 1:席の答えが正解と同じ", 0), 分母=c.get(u"段 1:行の数", 0))
    ok_rows = c.get(u"段 1:出どころの種類:表の行の和", 0)
    present = c.get(u"段 1:席が在ると書いた行", 0)
    put(u"UM2-P2", (10 * ok_rows >= 3 * present) if present else None, 数=ok_rows, 分母=present)
    put(u"UM2-P3", c.get(u"段 1:通したが数値が違う", 0) >= 1, 数=c.get(u"段 1:通したが数値が違う", 0),
        **{u"正解が null の行を通した数": c.get(u"段 1:通したが正解が null", 0)})
    put(u"UM2-P4", c.get(u"段 1:K3 で止まった行", 0) >= 10, 数=c.get(u"段 1:K3 で止まった行", 0))
    put(u"UM2-P5", c.get(u"束が K0 で断られた束", 0) == 0, 数=c.get(u"束が K0 で断られた束", 0))
    marks = c.get(u"段 2:確かめた取り方の行", 0)
    carried = c.get(u"段 2:持ち越した行", 0)
    put(u"UM2-Q1", (5 * carried >= 4 * marks) if marks else None, 数=carried, 分母=marks)
    put(u"UM2-Q2", c.get(u"段 2:持ち越して通したが数値が違う", 0) == 0, 数=c.get(u"段 2:持ち越して通したが数値が違う", 0),
        **{u"正解が null の行を通した数": c.get(u"段 2:持ち越して通したが正解が null", 0)})
    put(u"UM2-Q3", c.get(u"段 2:K11 で止めた社", 0) >= 1, 数=c.get(u"段 2:K11 で止めた社", 0))
    docs = sum(v for k, v in c.items() if k.startswith(u"段 3:資料の検査を通した:"))
    put(u"UM2-D1", docs >= 13, 数=docs)
    nums = c.get(u"段 3:A の 2 期目の資料で数が出ている行", 0)
    put(u"UM2-D2", 100 * nums >= 60 * 132, 数=nums, 分母=132)
    put(u"UM2-E1", c.get(u"通し:期1・期2とも", 0) >= 3, 数=c.get(u"通し:期1・期2とも", 0))
    made = sum(m.get(k, {}).get(u"作れた:関係に入らない", 0) for k in (u"V2", u"V3", u"V6"))
    passed = sum(m.get(k, {}).get(u"通した:関係に入らない", 0) for k in (u"V2", u"V3", u"V6"))
    put(u"UM2-V1", (passed == made) if made else None, 作れた=made, 通した=passed)
    made2 = sum(m.get(k, {}).get(u"作れた", 0) for k in (u"V1", u"V4"))
    passed2 = sum(m.get(k, {}).get(u"通した", 0) for k in (u"V1", u"V4"))
    put(u"UM2-V2", passed2 == 0, 作れた=made2, 通した=passed2)
    return out


def build_record(company_dir, seat_dir, chk=None):
    u"""記録(数だけ。本番の 4 社がそろってから 1 回だけ)。会社の名・file の名・列の名・科目の字・額は持たない。"""
    res = tally(PROD, company_dir, seat_dir, chk)
    return res


# ============================================================ 命令
def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    opt, flags, k = {}, [], 0
    while k < len(argv):
        a = argv[k]
        if a == "--companies":
            vals = []
            k += 1
            while k < len(argv) and not argv[k].startswith("--"):
                vals.append(int(argv[k]))
                k += 1
            opt[a] = vals
        elif a.startswith("--") and k + 1 < len(argv) and not argv[k + 1].startswith("--"):
            opt[a] = argv[k + 1]
            k += 2
        else:
            flags.append(a)
            k += 1
    if "--company-dir" not in opt or "--seat-dir" not in opt:
        print(u"命令の形", file=sys.stderr)
        return 2
    if "--record" in flags:
        for i in PROD:
            if not os.path.isdir(os.path.join(opt["--company-dir"], str(i))) or not os.path.isdir(os.path.join(opt["--seat-dir"], str(i))):
                print(u"本番の 4 社(1〜4)がそろっていないので記録は書かない", file=sys.stderr)
                return 2
        res = build_record(opt["--company-dir"], opt["--seat-dir"])
        out = opt.get("--out", os.path.join(ROOT, RECORD_REL))
    else:
        res = tally(opt.get("--companies", list(DEV)), opt["--company-dir"], opt["--seat-dir"])
        out = opt.get("--out")
    body = json.dumps(res, ensure_ascii=False, indent=1) + u"\n"
    if out:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        with io.open(out, "w", encoding="utf-8") as fh:
            fh.write(body)
    else:
        sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
