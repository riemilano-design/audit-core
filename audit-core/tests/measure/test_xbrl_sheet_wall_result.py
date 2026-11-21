# -*- coding: utf-8 -*-
u"""結果の門: 封 docs/XBRL_SHEET_WALL_SEAL_2026-11-22.md(3062223e)の結果の文書 docs/XBRL_SHEET_WALL_RESULT_2026-11-22.md(便 XA0)。

封の門 ``test_xbrl_sheet_wall_seal.py`` の次の段。**追跡されている記録・script・封・封の門・結果の文書と git の履歴だけを読む**(書類の置き場も道具(Arelle)も読まない・通信しない・鍵は読まない)。
検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表で 1 つずつ(木の file は変異させず、``Ctx`` の写しに当てる)。

 a script・記録・封・封の門の sha256(字で留める)と、記録の script の sha256・封の commit の欄・記録の限界の欄
 b 記録の数え直し: 書類ごとの数から、**script の関数を使わずに**、2 群(開発の 5 本・本番だけの 62 本)の fact・表の外・全部決まる・書く欄・書類 90% を数え直し、
   群の数の間の関係(表の中 = fact - 表の外・向き A + 向き B = 表・符号と書式の合計・書く欄の項の和)と予測の判定に要る数を、群の数から作り直して記録と同じことを見る
 c 予測 XA0-1〜XA0-7 の当たり外れを、封 §4 の字から取った境(丸める前の整数で。下限は含む・上限は XA0-2・XA0-4 が含まない・XA0-5 が含む)と記録から決め直し、
   文書 §1 の表・件数・外れた向きと同じことを見る。封 §4 の自己点検の条・封 §6 の決め(XA0-2 が当たりで XA0-4 が 60% 未満なら次の便の候補を示す)と文書が合う
 d 結果の文書の数: 数字を含む行は全部、記録から組んだ数の並びの内。表の行・言い切りは記録から組んだ字とそのまま照らす。
   §3 は記録に欄の無い読みの節で、数は字で留めた小さい集合だけ(その外の節に記録に無い数が漏れていない)
 e 文書の要点の字・頭の負けと限界・禁止語・「作れる」「専用の道具が要らない」「人が書ける」を肯定で書かない・docID と EDINET コードの形
 f 封・script・記録・封の門が commit の blob と一致(結果の便で 0 行)・engine は封の commit から 0 行・順序・文書が書く commit の字が実の履歴と合う
この file は docID の字を持たない。
"""
import collections
import copy
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)


def load_module(rel, name):
    u"""importlib で読み込む。読み込みの前に居た名前は、読み込みの後に元の object へ戻す(自分の名前 ``name`` は残す)。"""
    before = dict(sys.modules)
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        for k, v in before.items():
            if k != name and sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


SG = load_module("tests/measure/test_xbrl_sheet_wall_seal.py", "xbrl_sheet_wall_seal_gate_for_result_gate")        # 封の門の部品。門としては走らせない
PR = SG.load_order_helpers()
MS = SG.MS

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
RECORD_REL = SG.RECORD_REL
GATE_REL = "tests/measure/test_xbrl_sheet_wall_result.py"
DOC_REL = "docs/XBRL_SHEET_WALL_RESULT_2026-11-22.md"
SCRIPT_COMMIT_SHORT = "f60f374b"                  # script と封の門を足した commit
RECORD_COMMIT_SHORT = "d52b2619"                  # 記録を足した commit
BLOB_AT = collections.OrderedDict([
    (SEAL_REL, SEAL_COMMIT_SHORT), (SCRIPT_REL, SCRIPT_COMMIT_SHORT), (SEAL_GATE_REL, SCRIPT_COMMIT_SHORT), (RECORD_REL, RECORD_COMMIT_SHORT)])
DOC_COMMITS = (SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT)

SHA_PIN = collections.OrderedDict([
    (RECORD_REL, "f5d45ab221809b19d87a58801127504055e45d689d48586463babf9a6dbf0a09"),
    (SCRIPT_REL, "d94b2a3efb6210c3cd00279d7bf405f233ea644ef51f4904d5bae8292714692f"),
    (SEAL_GATE_REL, "de0499b52fc56767db62fcca3ae59ff8af0ddce24ac2f2489629d6337b53988c"),
    (SEAL_REL, "6809569f290a4e4ae009a2102500c104643dc0064799afcc09188dec3202eb2d")])

DEV_COUNT = 5
DOC_COUNT = 67
PROD_COUNT = DOC_COUNT - DEV_COUNT
G_DEV, G_PROD = u"開発の 5 本", u"本番だけの 62 本"
GROUPS = (G_DEV, G_PROD)
PRED_KEY = u"予測の判定に要る数(XA0-1〜XA0-7。本番だけの 62 本のうち断らなかった書類を合わせた fact。当たり・外れは結果の文書で)"
PK = (u"XA0-1 表の中の fact / fact", u"XA0-2 全部決まる fact / fact", u"XA0-3 符号が合う fact / 表の中の空でない fact", u"XA0-4 書く欄の数 / fact の数 × 7",
      u"XA0-5 向き B の方が決まる fact が多かった表 / fact の在る表", u"XA0-6 全部決まる fact が 90% 以上の書類 / fact が 1 つ以上在る書類", u"XA0-7 書式が合う fact / 表の中の空でない fact")
REASONS = (u"name が線の決めと違う", u"contextRef が線の決めと違う", u"unitRef が線の決めと違う", u"decimals が線の決めと違う", u"scale が線の決めと違う")
REASON_KEY = u"決まらなかった理由ごとの fact の数(重ねて数える)"
CELL_KEY = u"書く欄の数(項ごと)"
CELL_ITEMS = (u"向き(表ごとに 1)", u"要素の線 × 4", u"文脈の線 × 1", u"書式の類の数", u"空の fact の数 × 1", u"表の中で全部決まらない fact × 7", u"表の外の fact × 7")
DOC90 = u"全部決まる fact が 90% 以上の書類の数"
# 封 §4 の字(封の文書にその字が在ることを見る)
BOUND_SEAL_PHRASES = (u"表の中の fact は、fact の 97% 以上", u"全部決まる fact は、fact の 75% 以上 95% 未満", u"符号が合う fact は、表の中の空でない fact の 98% 以上", u"書く欄の比は 35% 以上 60% 未満",
                      u"向き B の方が決まる fact が多かった表は 5% 以上 30% 以下", u"全部決まる fact が 90% 以上の書類は、30 本以下", u"書式が合う fact は、表の中の空でない fact の 98% 以上",
                      u"全部決まる fact がちょうど 100%・表の外の fact がちょうど 0・表の中の fact が 50% 未満・断った書類が 6 本以上",
                      u"XA0-2 が当たりで XA0-4 が 60% 未満なら、次の便の候補を人間に示す",
                      u"「XBRL を作れる」「専用の道具が要らない」は、この便からは言えない")
HEAD_PHRASES = (u"先に負けと限界を書く", u"当たり 6・外れ 1(XA0-5)", u"封は書き換えていない", u"0 USD・LLM の席も道具(Arelle)も呼んでいない", u"engine は 0 行",
                u"行・列の紙だけでは、数の fact の 20.3% が収まらない", u"全部決まる fact が 90% 以上の書類は、62 本のうち 0 本", u"「この紙だけで 1 本まるごと書ける」書類は無かった",
                u"人が紙に書く値が正しいかは測っていない", u"「人が書く量はこれだけで済む」とは読まない", u"「全部決まる fact」の率は甘く出ている", u"劇的に減るわけではない",
                u"`rowspan` を見ない", u"数の fact だけ", u"提出者別タクソノミの中身は、この便の数に入っていない", u"便 XP0 と同じ型の限界", u"67 本は無作為ではない。有報だけ",
                u"「XBRL を作れる」「専用の道具が要らない」は、この便からは言えない")
PHRASES = (u"言えること", u"言えないこと", u"人間に示す次の便の候補", u"どちらにも別の封が先", u"盲検ではない", u"記録に欄の無い読み", u"どちらの読みでも当たり外れは変わらない",
           u"実装で決めた所", u"人間に返すこと", u"紙は表ごとに向きを持たなければならない")
FORBIDDEN_WORDS = (u"精度", u"世界で 1 社", u"LLM より正確", u"保証", u"完璧")
DOCID_FORM = re.compile(r"(?<![0-9A-Za-z])S[0-9A-Z]{7}(?![0-9A-Za-z])")
ECODE_FORM = re.compile(r"(?<![0-9A-Za-z])E\d{5}(?![0-9A-Za-z])")
# 記録に欄の無い読み(§3)の、行ごとの数の並び。記録から導けない監査の席の読みなので、正本は文書の字そのもの = ここに字で留める(留め)。
# 行の鍵になる句 → その行に在るべき数の並び(文書の左から右の順。commit・`` ` `` の中・XA0-5 の名は数えない)。
SEC3_LINES = (
    (u"**最頻が並んだ線の読み**", (u"62", u"50237", u"79.4", u"200015", u"45.2", u"988", u"40.3")),
    (u"**符号が合わない 74 件の型**", (u"74", u"62", u"19", u"12", u"1")),
    (u"監査の席は、62 本のうち 2 本の表を合わせて 5 つ", (u"62", u"2", u"5")),
)
STRUCTURAL = set(str(i) for i in range(0, 11))
BOUND_NUMBERS = set([u"97", u"75", u"95", u"98", u"35", u"60", u"5", u"30", u"90", u"50", u"67", u"62", u"20", u"4", u"100"])


# ======================================================================================================
def read(rel, root=ROOT):
    with io.open(os.path.join(root, rel), encoding="utf-8") as fh:
        return fh.read()


def sha_file(rel, root=ROOT):
    with open(os.path.join(root, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def guard(fn, *a, **k):
    try:
        return fn(*a, **k)
    except BaseException as exc:                   # noqa: BLE001  変異で落ちた検査は「問題」として数える
        return [u"例外: %s" % type(exc).__name__]


def pct(n, d):
    u"""n/d の % を小数第 1 位まで四捨五入(0.5 は上げる)した字。script の関数は使わない(整数で)。"""
    return u"%.1f" % (((2000 * n + d) // (2 * d)) / 10.0)


def section(doc, head, nxt):
    i = doc.index(head)
    j = doc.index(nxt, i + len(head)) if nxt else len(doc)
    return doc[i:j]


class Ctx(object):
    u"""検査が見る写し。変異はこの写しを変える(木の file は変えない)。"""

    def __init__(self):
        self.rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        self.doc = read(DOC_REL)
        self.seal = read(SEAL_REL)
        self.shas = collections.OrderedDict((rel, sha_file(rel)) for rel in SHA_PIN)

    def copy(self):
        c = Ctx.__new__(Ctx)
        c.rec = copy.deepcopy(self.rec)
        c.doc = self.doc
        c.seal = self.seal
        c.shas = collections.OrderedDict(self.shas)
        return c


# ======================================================================================================
# b 数え直し(script の関数は使わない)
def docs_of(rec, g):
    docs = rec[u"書類"]
    return docs[:DEV_COUNT] if g == G_DEV else docs[DEV_COUNT:]


def doc90(docs):
    return sum(1 for d in docs if not d[u"断った"] and d[u"fact の数"] > 0 and 100 * d[u"全部決まる fact の数"] >= 90 * d[u"fact の数"])


def group_problems(rec, g):
    u"""群の数が、書類ごとの数と、群の数の間の関係から数え直した値と同じ。"""
    s = rec[g]
    docs = docs_of(rec, g)
    out = []
    live = [d for d in docs if not d[u"断った"]]
    sums = {u"fact の数": sum(d[u"fact の数"] for d in live), u"表の外の fact の数": sum(d[u"表の外の fact の数"] for d in live),
            u"全部決まる fact の数": sum(d[u"全部決まる fact の数"] for d in live), u"書く欄の数": sum(d[u"書く欄の数"] for d in live)}
    for k, v in sums.items():
        if s[k] != v:
            out.append(u"%s の %s が書類ごとの和 %d と違う" % (g, k, v))
    if s[u"書類の数"] != len(docs) or s[u"断った書類の数"] != len(docs) - len(live) or s[u"断らなかった書類の数"] != len(live):
        out.append(u"%s の書類の数・断った書類の数が書類ごとの行と違う" % g)
    if s[DOC90] != doc90(docs):
        out.append(u"%s の 90%% 以上の書類の数が書類ごとの数から数え直した値と違う" % g)
    if s[u"fact が 1 つ以上在る書類の数(断らなかった)"] != sum(1 for d in live if d[u"fact の数"] > 0):
        out.append(u"%s の fact が 1 つ以上在る書類の数が違う" % g)
    fact, outside, inside = s[u"fact の数"], s[u"表の外の fact の数"], s[u"表の中の fact の数"]
    if inside != fact - outside:
        out.append(u"%s の表の中の fact が fact - 表の外 と違う" % g)
    nil, tables = s[u"空の fact の数"], s[u"fact の在る表の数"]
    if tables != s[u"向き A を選んだ表の数"] + s[u"向き B を選んだ表の数"] or s[u"向き B の方が決まる fact が多かった表の数"] != s[u"向き B を選んだ表の数"]:
        out.append(u"%s の向き A + 向き B が表の数と違う・向き B の方が多かった表が向き B を選んだ表と違う" % g)
    live_inside = s[u"表の中の空でない fact の数"]
    neg, anti = s[u"符号が合わない fact の数(負と読んだが sign が - でない)"], s[u"符号が合わない fact の数(sign が - だが負と読めない)"]
    if live_inside != s[u"符号が合う fact の数"] + neg + anti or live_inside != s[u"書式が合う fact の数"] + s[u"書式が合わない fact の数"]:
        out.append(u"%s の符号・書式の合う・合わないの和が表の中の空でない fact と違う" % g)
    if live_inside > inside or inside - live_inside > nil:
        out.append(u"%s の表の中の空でない fact と空の fact の関係が合わない" % g)
    full, decided = s[u"全部決まる fact の数"], s[u"表の決めで決まる fact の数"]
    if not (full <= decided <= inside) or decided - full > neg + anti + s[u"書式が合わない fact の数"]:
        out.append(u"%s の全部決まる・表の決めで決まる・表の中の関係が合わない" % g)
    reasons = s[REASON_KEY]
    if list(reasons) != list(REASONS) or inside - decided > sum(reasons.values()) or max(reasons.values()) > inside - decided:
        out.append(u"%s の決まらなかった理由の数が、決まらなかった fact の数と合わない" % g)
    if s[u"その線の上の fact の数"] != s[u"線の上の fact が 1 つだけの要素の線の数"] or s[u"線の上の fact が 1 つだけの要素の線の数"] > s[u"要素の線の数(fact の在る)"]:
        out.append(u"%s の 1 つだけの線の数が合わない" % g)
    cells = s[CELL_KEY]
    if list(cells) != list(CELL_ITEMS):
        out.append(u"%s の書く欄の項の名が違う" % g)
        return out
    want_items = (tables, 4 * s[u"要素の線の数(fact の在る)"], s[u"文脈の線の数(fact の在る)"], None, nil, 7 * (inside - full), 7 * outside)
    for (k, w) in zip(CELL_ITEMS, want_items):
        if w is not None and cells[k] != w:
            out.append(u"%s の書く欄の項 %s が数え直した値 %d と違う" % (g, k, w))
    if s[u"書く欄の数"] != sum(cells.values()) or s[u"fact の数 × 7"] != 7 * fact:
        out.append(u"%s の書く欄の数・fact の数 × 7 が項の和と違う" % g)
    if s[u"表の中の fact が全部決まる場合の書く欄の数"] != s[u"書く欄の数"] - cells[CELL_ITEMS[5]]:
        out.append(u"%s の全部決まる場合の書く欄の数が違う" % g)
    for key, n, d in ((u"書く欄の比", s[u"書く欄の数"], 7 * fact), (u"表の中の fact が全部決まる場合の比", s[u"表の中の fact が全部決まる場合の書く欄の数"], 7 * fact)):
        r = s[key]
        if (r[u"数"], r[u"分母"]) != (n, d) or u"%.1f" % r[u"%"] != pct(n, d):
            out.append(u"%s の %s が数え直した値と違う" % (g, key))
    return out


def rate_row(n, d):
    return collections.OrderedDict([(u"数", n), (u"分母", d), (u"%", float(pct(n, d)))])


def pred_expected(rec):
    s = rec[G_PROD]
    fact = s[u"fact の数"]
    live = s[u"表の中の空でない fact の数"]
    return collections.OrderedDict([
        (PK[0], rate_row(s[u"表の中の fact の数"], fact)), (PK[1], rate_row(s[u"全部決まる fact の数"], fact)), (PK[2], rate_row(s[u"符号が合う fact の数"], live)),
        (PK[3], rate_row(s[u"書く欄の数"], 7 * fact)), (PK[4], rate_row(s[u"向き B の方が決まる fact が多かった表の数"], s[u"fact の在る表の数"])),
        (PK[5], collections.OrderedDict([(u"書類", s[DOC90]), (u"分母", s[u"fact が 1 つ以上在る書類の数(断らなかった)"])])), (PK[6], rate_row(s[u"書式が合う fact の数"], live))])


def judge(rec):
    u"""封 §4 の境(丸める前の整数)から XA0-1〜XA0-7 を決め直す。値は (当たりか, 外れた向き)。向きは ``上``・``下``・空。"""
    s = rec[G_PROD]
    fact = s[u"fact の数"]
    live = s[u"表の中の空でない fact の数"]
    full, cells, base = s[u"全部決まる fact の数"], s[u"書く欄の数"], 7 * fact
    tb, tt = s[u"向き B の方が決まる fact が多かった表の数"], s[u"fact の在る表の数"]
    out = collections.OrderedDict()

    def put(k, lo_ok, hi_ok):
        out[k] = (lo_ok and hi_ok, u"" if lo_ok and hi_ok else (u"下" if not lo_ok else u"上"))
    put(u"XA0-1", 100 * s[u"表の中の fact の数"] >= 97 * fact, True)
    put(u"XA0-2", 100 * full >= 75 * fact, 100 * full < 95 * fact)
    put(u"XA0-3", 100 * s[u"符号が合う fact の数"] >= 98 * live, True)
    put(u"XA0-4", 100 * cells >= 35 * base, 100 * cells < 60 * base)
    put(u"XA0-5", 100 * tb >= 5 * tt, 100 * tb <= 30 * tt)
    put(u"XA0-6", True, s[DOC90] <= 30)
    put(u"XA0-7", 100 * s[u"書式が合う fact の数"] >= 98 * live, True)
    return out


def sha_problems(c):
    out = []
    for rel, want in SHA_PIN.items():
        if c.shas[rel] != want:
            out.append(u"sha256 が字で留めた値と違う: %s" % rel)
    if c.rec[u"この script の sha256"] != SHA_PIN[SCRIPT_REL]:
        out.append(u"記録の script の sha256 が script と違う")
    if (c.rec[u"seal"], c.rec[u"封の commit"]) != (SEAL_REL, SEAL_COMMIT_SHORT):
        out.append(u"記録の封の欄が違う")
    if c.rec[u"限界"] != MS.LIMITS:
        out.append(u"記録の限界の欄が script の字と違う")
    return out


def recount_problems(c):
    rec = c.rec
    out = []
    docs = rec[u"書類"]
    if [d[u"番号"] for d in docs] != list(range(1, DOC_COUNT + 1)) or rec[u"材料"][u"書類の本数"] != DOC_COUNT or rec[u"材料"][u"開発の 5 本の番号"] != list(range(1, DEV_COUNT + 1)):
        out.append(u"書類の番号・材料の書類の本数・開発の 5 本の番号が違う")
    for g in GROUPS:
        out.extend(group_problems(rec, g))
    if json.loads(json.dumps(rec[PRED_KEY])) != json.loads(json.dumps(pred_expected(rec))):
        out.append(u"予測の判定に要る数が群の数から作り直した値と違う")
    return out


def record_clean_problems(c):
    text = json.dumps(c.rec, ensure_ascii=False)
    out = []
    try:
        MS.check_clean(c.rec, text)
    except SystemExit:
        out.append(u"記録の検査(欄・形・file の名)が止める")
    if DOCID_FORM.search(re.sub(r"[0-9a-fA-F]{32,}", u"", text)) or ECODE_FORM.search(text):
        out.append(u"記録に docid か EDINET コードの形が在る")
    return out


def bound_problems(c):
    out = [u"封に境の字が無い: %s" % p for p in BOUND_SEAL_PHRASES if p not in c.seal]
    sec4 = section(c.seal, u"## §4 ", u"## §5 ")
    rows = [ln for ln in sec4.splitlines() if re.match(r"^\| XA0-\d", ln)]
    if len(rows) != 7:
        out.append(u"封 §4 の表の行が 7 つでない")
    return out


# ======================================================================================================
def cell_text(rec, key):
    s = rec[G_PROD]
    if key == u"XA0-6":
        return u"%d/%d" % (s[DOC90], s[u"fact が 1 つ以上在る書類の数(断らなかった)"])
    pairs = {u"XA0-1": (s[u"表の中の fact の数"], s[u"fact の数"]), u"XA0-2": (s[u"全部決まる fact の数"], s[u"fact の数"]),
             u"XA0-3": (s[u"符号が合う fact の数"], s[u"表の中の空でない fact の数"]), u"XA0-4": (s[u"書く欄の数"], 7 * s[u"fact の数"]),
             u"XA0-5": (s[u"向き B の方が決まる fact が多かった表の数"], s[u"fact の在る表の数"]), u"XA0-7": (s[u"書式が合う fact の数"], s[u"表の中の空でない fact の数"])}
    n, d = pairs[key]
    return u"%d/%d(%s%%)" % (n, d, pct(n, d))


def expected_cells(c):
    out = collections.OrderedDict()
    for k, (ok, way) in judge(c.rec).items():
        out[k] = (cell_text(c.rec, k), u"当たり" if ok else u"**外れ**(%sに外れた)" % way)
    return out


def verdict_problems(c):
    rec = c.rec
    j = judge(rec)
    want = expected_cells(c)
    out = []
    rows = {}
    for ln in c.doc.splitlines():
        m = re.match(r"^\| (XA0-\d)(?:\(主\))? \|(.*)\|$", ln)
        if m:
            rows[m.group(1)] = [x.strip() for x in m.group(2).split(u"|")]
    if sorted(rows) != sorted(j):
        return [u"文書 §1 の表の行が XA0-1〜XA0-7 でない"]
    sec4 = section(c.seal, u"## §4 ", u"## §5 ")
    for k, cells in rows.items():
        if len(cells) != 3:
            out.append(u"%s の行の欄の数が違う" % k)
            continue
        if k == u"XA0-6":                                   # 文書の予測の字は封の字の要約。境の「30 本以下」が文書の欄と封の行の両方に在る
            if u"90% 以上" not in cells[0] or u"30 本以下" not in cells[0] or u"30 本以下" not in sec4:
                out.append(u"XA0-6 の境の字(30 本以下)が文書の欄か封の行に無い")
        elif cells[0] not in sec4:
            out.append(u"%s の予測の字が封 §4 の表に無い: %s" % (k, cells[0]))
        if cells[1] != want[k][0]:
            out.append(u"%s の実測の字が記録から組んだ字と違う: %s" % (k, cells[1]))
        if cells[2] != want[k][1]:
            out.append(u"%s の判定が決め直した判定と違う: %s(決め直し: %s)" % (k, cells[2], want[k][1]))
    hits = sum(1 for v in j.values() if v[0])
    if u"- 当たり %d・外れ %d。" % (hits, len(j) - hits) not in c.doc.splitlines():
        out.append(u"文書の件数の行が決め直した件数と違う")
    head = c.doc.split(u"## §1")[0]
    misses = u"・".join(k for k, v in j.items() if not v[0])
    if u"当たり %d・外れ %d(%s)" % (hits, len(j) - hits, misses) not in head:
        out.append(u"文書の頭の件数・外れの名が決め直した値と違う")
    sec1, sec5 = section(c.doc, u"## §1 ", u"## §2 "), section(c.doc, u"## §5 ", None)
    s = rec[G_PROD]
    suspect = [s[u"全部決まる fact の数"] == s[u"fact の数"], s[u"表の外の fact の数"] == 0, 2 * s[u"表の中の fact の数"] < s[u"fact の数"], s[u"断った書類の数"] >= 6]
    if any(suspect):
        out.append(u"封 §4 の「先に自分の欠陥を疑う場合」が発火している")
    if u"封 §4 の「先に自分の欠陥を疑う場合」" not in sec1 or u"には当たらない" not in sec1:
        out.append(u"文書 §1 に自己点検の言い切りが無い")
    # 外れた予測の外れ方の言い切り: 外れた予測は文書に外れ方が書かれている(XA0-5 は向き B の表が 3 分の 1 を超えた)
    for k, (ok, way) in j.items():
        if not ok and u"%s の外れ方" % k not in sec1:
            out.append(u"外れた %s の外れ方の言い切りが文書 §1 に無い" % k)
    if j[u"XA0-5"][0] is False and 3 * s[u"向き B の方が決まる fact が多かった表の数"] <= s[u"fact の在る表の数"]:
        out.append(u"文書の「3 分の 1 を超えた」が記録と合わない")
    # 封 §6: XA0-2 が当たりで XA0-4 が 60% 未満なら次の便の候補を示す
    cond = j[u"XA0-2"][0] and (100 * s[u"書く欄の数"] < 60 * 7 * s[u"fact の数"])
    shown = u"人間に示す次の便の候補**(封 §6。XA0-2 が当たり・XA0-4 が 60% 未満なので示す)" in sec5
    if cond != shown:
        out.append(u"封 §6 の決め(XA0-2 が当たりで XA0-4 が 60% 未満なら次の便の候補を示す)と文書 §5 が合わない")
    if cond:
        s6 = section(c.seal, u"## §6 ", u"## §7 ")
        seg = s6[s6.index(u"(i) "):s6.index(u"。どちらにも")].strip()
        if seg not in sec5:
            out.append(u"§5 の次の便の候補 (i)(ii) が封 §6 の字と違う")
    return out


# ======================================================================================================
def tbl_line(label, p, d):
    return u"| %s | %s | %s |" % (label, p, d)


def expected_lines(c):
    rec = c.rec
    p, d = rec[G_PROD], rec[G_DEV]
    out = []
    for label, key in ((u"断った書類", u"断った書類の数"), (u"fact", u"fact の数"), (u"空の fact", u"空の fact の数"), (u"表の外の fact", u"表の外の fact の数"), (u"fact の在る表", u"fact の在る表の数"),
                       (u"向き A を選んだ表", u"向き A を選んだ表の数"), (u"向き B を選んだ表", u"向き B を選んだ表の数"), (u"fact が 1 つだけの表", u"fact が 1 つだけの表の数"),
                       (u"表の決めで決まる fact", u"表の決めで決まる fact の数"), (u"全部決まる fact", u"全部決まる fact の数"), (u"要素の線(fact の在る)", u"要素の線の数(fact の在る)"),
                       (u"文脈の線(fact の在る)", u"文脈の線の数(fact の在る)"), (u"線の上の fact が 1 つだけの要素の線", u"線の上の fact が 1 つだけの要素の線の数"),
                       (u"書く欄の数", u"書く欄の数"), (u"fact の数 × 7", u"fact の数 × 7")):
        out.append(tbl_line(label, u"%d" % p[key], u"%d" % d[key]))
    out.append(tbl_line(u"書く欄の比", u"%s%%" % pct(p[u"書く欄の数"], p[u"fact の数 × 7"]), u"%s%%" % pct(d[u"書く欄の数"], d[u"fact の数 × 7"])))
    out.append(tbl_line(u"表の中の fact が全部決まる場合の比", u"%s%%(%d)" % (pct(p[u"表の中の fact が全部決まる場合の書く欄の数"], p[u"fact の数 × 7"]), p[u"表の中の fact が全部決まる場合の書く欄の数"]),
                        u"%s%%(%d)" % (pct(d[u"表の中の fact が全部決まる場合の書く欄の数"], d[u"fact の数 × 7"]), d[u"表の中の fact が全部決まる場合の書く欄の数"])))
    for r, label in zip(REASONS, (u"name", u"contextRef", u"unitRef", u"decimals", u"scale")):
        out.append(u"| `%s` | %d |" % (label, p[REASON_KEY][r]))
    return out


def expected_fragments(c):
    rec = c.rec
    s, dev = rec[G_PROD], rec[G_DEV]
    j = judge(rec)
    hits = sum(1 for v in j.values() if v[0])
    fact, full = s[u"fact の数"], s[u"全部決まる fact の数"]
    cl = s[CELL_KEY]
    f = []
    f.append(u"判定した %d 本のうち当たり %d・外れ %d" % (len(j), hits, len(j) - hits))
    f.append(u"(5 本で %s%%)" % pct(dev[u"向き B の方が決まる fact が多かった表の数"], dev[u"fact の在る表の数"]))
    f.append(u"約 %d 割までは届くが、%d 割は紙に収まらない" % (int(round(10.0 * full / fact)), int(round(10.0 * (fact - full) / fact))))
    f.append(u"数の fact の %s%% が収まらない**(%d のうち全部決まらない fact は %d)" % (pct(fact - full, fact), fact, fact - full))
    f.append(u"文脈(`contextRef`)が線の決めと違う fact で %d" % s[REASON_KEY][REASONS[1]])
    f.append(u"全部決まる fact が 90%% 以上の書類は、%d 本のうち %d 本" % (s[u"fact が 1 つ以上在る書類の数(断らなかった)"], s[DOC90]))
    f.append(u"線の上の fact が 1 つだけの要素の線が %d 在る(その線の上の fact も %d)" % (s[u"線の上の fact が 1 つだけの要素の線の数"], s[u"その線の上の fact の数"]))
    f.append(u"fact が 1 つだけの表も %d 在る" % s[u"fact が 1 つだけの表の数"])
    f.append(u"書く欄の比 %s%% は" % pct(s[u"書く欄の数"], 7 * fact))
    f.append(u"受理済みの 62 本の数の fact %d のうち" % fact)
    f.append(u"属性が全部決まる fact は %s%%。残りは %s%%" % (pct(full, fact), pct(fact - full, fact)))
    f.append(u"向き %d・要素の線 × 4 は %d・文脈の線 × 1 は %d・書式の類 %d・空の fact × 1 は %d・表の中で全部決まらない fact × 7 は %d・表の外の fact × 7 は %d。" % tuple(cl[k] for k in CELL_ITEMS))
    f.append(u"(%d)が、紙に収まらず 1 つずつ書く fact の分" % cl[CELL_ITEMS[5]])
    f.append(u"(62 本・表の中の空でない fact %d): 合わない fact は %d。" % (s[u"表の中の空でない fact の数"], s[u"符号が合わない fact の数(負と読んだが sign が - でない)"] + s[u"符号が合わない fact の数(sign が - だが負と読めない)"]))
    f.append(u"「負と読んだが `sign` が `-` でない」が %d・「`sign` が `-` だが負と読めない」が %d。書式が合わない fact は %d。" % (
        s[u"符号が合わない fact の数(負と読んだが sign が - でない)"], s[u"符号が合わない fact の数(sign が - だが負と読めない)"], s[u"書式が合わない fact の数"]))
    f.append(u"断った書類は 0。")
    return f


def sanity_problems(c):
    u"""文書の言い切り(「約 8 割」「2 割」「4 割を超える」「3 分の 1」「半分より少し下がる」)が記録の数に合う。"""
    s = c.rec[G_PROD]
    fact, full = s[u"fact の数"], s[u"全部決まる fact の数"]
    out = []
    if round(10.0 * full / fact) != 8 or round(10.0 * (fact - full) / fact) != 2:
        out.append(u"文書の「約 8 割・2 割」が記録の全部決まる fact の率と合わない")
    if 10 * s[CELL_KEY][CELL_ITEMS[5]] <= 4 * s[u"書く欄の数"]:
        out.append(u"文書の「書く欄の 4 割を超える分」が記録と合わない")
    if not (2 * s[u"書く欄の数"] < 7 * fact and 100 * s[u"書く欄の数"] >= 40 * 7 * fact):
        out.append(u"文書の「半分より少し下がる」が記録と合わない")
    if s[u"断った書類の数"] != 0:
        out.append(u"文書の「断った書類は 0」が記録と合わない")
    if s[u"その線の上の fact の数"] != s[u"線の上の fact が 1 つだけの要素の線の数"]:
        out.append(u"1 つだけの線の上の fact の数が線の数と違う")
    return out


def fragment_problems(c):
    out = []
    lines = c.doc.splitlines()
    for want in expected_lines(c):
        if want not in lines:
            out.append(u"文書に記録から組んだ行が無い: %s" % want[:40])
    for frag in expected_fragments(c):
        if frag not in c.doc:
            out.append(u"文書に記録から組んだ字が無い: %s" % frag[:40])
    return out


NUM_RE = re.compile(r"(?<![A-Za-z0-9_\-.])(\d[\d,]*(?:\.\d+)?)(?![A-Za-z0-9_])")


def doc_number_tokens(line):
    s = re.sub(r"`[^`]*`", u" ", line)
    s = re.sub(r"\b(?=[0-9]*[a-f])[0-9a-f]{8}\b", u" ", s)
    s = re.sub(r"\d{4}-\d{2}-\d{2}", u" ", s)
    s = re.sub(r"X[A-Z]\d-\d", u" ", s)
    s = re.sub(r"XB0|XG0|XG1|XV0|XT0|XA0|XA1|XP0|XS0", u" ", s)
    s = re.sub(r"EC\d{4}[A-Z]", u" ", s)
    s = re.sub(r"§\d(?:-\d)?", u" ", s)
    return [m.group(1) for m in NUM_RE.finditer(s)]


def ints_in(o, acc):
    if isinstance(o, dict):
        for v in o.values():
            ints_in(v, acc)
    elif isinstance(o, list):
        for v in o:
            ints_in(v, acc)
    elif isinstance(o, float):
        acc.add(u"%.1f" % o)
    elif isinstance(o, int) and not isinstance(o, bool):
        acc.add(str(o))


def derived_numbers(c):
    rec = c.rec
    out = set()
    for g in GROUPS:
        ints_in(rec[g], out)
    ints_in(rec[PRED_KEY], out)
    s, dev = rec[G_PROD], rec[G_DEV]
    fact, full = s[u"fact の数"], s[u"全部決まる fact の数"]
    out.add(str(fact - full))                                   # 全部決まらない fact
    out.add(pct(fact - full, fact))                              # 収まらない率
    out.add(pct(dev[u"向き B の方が決まる fact が多かった表の数"], dev[u"fact の在る表の数"]))      # 開発の 5 本の XA0-5
    out.add(str(s[u"符号が合わない fact の数(負と読んだが sign が - でない)"] + s[u"符号が合わない fact の数(sign が - だが負と読めない)"]))
    out |= set(BOUND_NUMBERS)
    return out


def doc_number_problems(c):
    allowed = set(STRUCTURAL) | derived_numbers(c)
    sec3 = section(c.doc, u"## §3 ", u"## §4 ")
    sec3_lines = sec3.splitlines()
    out = []
    for i, ln in enumerate(c.doc.splitlines(), 1):
        if ln in sec3_lines:
            continue                                       # §3 は sec3_problems が小さい集合で見る
        for tok in doc_number_tokens(ln):
            if tok.replace(u",", u"") not in allowed:
                out.append(u"文書の %d 行目の数 %s が記録から組んだ数の外: %s" % (i, tok, ln[:30]))
    return out


def sec3_problems(c):
    u"""§3 は記録に欄の無い読みの節。行(箇条)ごとの数の並びを SEC3_LINES(字で留めた)と照らす。符号の件数は記録とも合う。"""
    s = section(c.doc, u"## §3 ", u"## §4 ")
    out = []
    bullets = [ln for ln in s.splitlines()[1:] if ln.strip()]
    if len(bullets) != len(SEC3_LINES):
        out.append(u"§3 の箇条の数 %d が留めた行の数 %d と違う" % (len(bullets), len(SEC3_LINES)))
    for key, nums in SEC3_LINES:
        hit = [ln for ln in bullets if key in ln]
        if len(hit) != 1:
            out.append(u"§3 に鍵の句の行が 1 つでない(%d 行): %s" % (len(hit), key))
            continue
        got = tuple(doc_number_tokens(hit[0]))
        if got != tuple(nums):
            out.append(u"§3 の行 %s の数の並び %s が留めた並び %s と違う" % (key, u",".join(got), u",".join(nums)))
    for ln in bullets:
        if not any(key in ln for key, _ in SEC3_LINES):
            out.append(u"§3 に留めていない行: %s" % ln[:20])
    if u"記録に欄の無い読み" not in s.splitlines()[0]:
        out.append(u"§3 の見出しが「記録に欄の無い読み」でない")
    p = c.rec[G_PROD]
    neg, anti = p[u"符号が合わない fact の数(負と読んだが sign が - でない)"], p[u"符号が合わない fact の数(sign が - だが負と読めない)"]
    if (neg, anti, neg + anti) != (12, 62, 74):
        out.append(u"§3 の符号の件数(74・12・62)が記録と合わない")
    if u"どちらの読みでも当たり外れは変わらない" not in s:
        out.append(u"§3 に「どちらの読みでも当たり外れは変わらない」が無い")
    return out


QUOTED_CLAIM = re.compile(u"「[^」]*(?:作れる|専用の道具が要らない|人が書ける|人が書く量はこれだけで済む)[^」]*」")
AFFIRM_WORDS = (u"作れる(?!か)", u"作れます", u"専用の道具が要らない", u"人が書ける(?!か)", u"人が書く量はこれだけで済む", u"検査に通る(?!こと|か)")


def affirm_problems(c):
    u"""「作れる」「専用の道具が要らない」「人が書ける」は、言えないことの引用(「…」の中)にしか無い。引用の在る行には「言えない」か「読まない」か「示していない」が在る。"""
    out = []
    for i, ln in enumerate(c.doc.splitlines(), 1):
        if QUOTED_CLAIM.search(ln) and not any(w in ln for w in (u"言えない", u"読まない", u"示していない")):
            out.append(u"文書の %d 行目が引用の主張を否定の外で書いている" % i)
        rest = QUOTED_CLAIM.sub(u"", ln)
        for w in AFFIRM_WORDS:
            if re.search(w, rest):
                out.append(u"文書の %d 行目に引用の外の字: %s" % (i, w))
    return out


# ======================================================================================================
def phrase_problems(c):
    return [u"文書に要点の字が無い: %s" % p for p in PHRASES if p not in c.doc]


def head_problems(c):
    head = c.doc.split(u"## §1")[0]
    return [u"文書の頭(§1 の前)に無い: %s" % p for p in HEAD_PHRASES if p not in head]


def forbidden_problems(c):
    out = [u"文書に禁止語: %s" % w for w in FORBIDDEN_WORDS if w in c.doc]
    scan = re.sub(r"\b(?=[0-9]*[a-f])[0-9a-f]{8}\b", u" ", c.doc)
    if DOCID_FORM.search(scan):
        out.append(u"文書に docID の形が在る")
    if ECODE_FORM.search(scan):
        out.append(u"文書に EDINET コードの形が在る")
    return out


def doc_commit_problems(c):
    out = []
    for w in DOC_COMMITS:
        if w not in c.doc:
            out.append(u"文書に commit の字が無い: %s" % w)
    if not set(re.findall(r"\b(?=[0-9]*[a-f])[0-9a-f]{8}\b", c.doc)) <= set(DOC_COMMITS):
        out.append(u"文書が知らない commit の字を書いている")
    return out


CHECKS = collections.OrderedDict([
    (u"sha", sha_problems), (u"recount", recount_problems), (u"clean", record_clean_problems), (u"bound", bound_problems),
    (u"verdict", verdict_problems), (u"numbers", doc_number_problems), (u"frag", fragment_problems), (u"sanity", sanity_problems), (u"sec3", sec3_problems),
    (u"affirm", affirm_problems), (u"phrases", phrase_problems), (u"head", head_problems), (u"forbidden", forbidden_problems), (u"commits", doc_commit_problems)])


# ======================================================================================================
def blob_problems(root, prefix, at):
    out = []
    for rel, commit in at.items():
        r = subprocess.run(["git", "-C", root, "show", "%s:%s" % (commit, prefix + rel)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if r.returncode != 0:
            out.append(u"commit %s に %s が無い" % (commit, rel))
            continue
        with open(os.path.join(root, prefix, rel), "rb") as fh:
            if fh.read() != r.stdout:
                out.append(u"%s が commit %s の blob と違う" % (rel, commit))
    return out


def commit_problems(root=REPO):
    u"""文書が書く 3 つの commit が実の履歴と合う: 封は 3062223e が足し(1 commit)・script と封の門は f60f374b が足し・記録は d52b2619 が足した。"""
    out = []
    for rel, want in ((SEAL_REL, [SEAL_COMMIT_SHORT]), (SCRIPT_REL, [SCRIPT_COMMIT_SHORT]), (SEAL_GATE_REL, [SCRIPT_COMMIT_SHORT]), (RECORD_REL, [RECORD_COMMIT_SHORT])):
        r = subprocess.run(["git", "-C", root, "log", "--format=%H", "--reverse", "--", PREFIX + rel], stdout=subprocess.PIPE, universal_newlines=True)
        got = [x for x in r.stdout.split() if x]
        if len(got) != len(want) or any(not g.startswith(w) for g, w in zip(got, want)):
            out.append(u"%s の履歴が文書の書く commit %s と違う" % (rel, u"・".join(want)))
    return out


def git_problems(root=REPO):
    out = []
    out.extend(SG.seal_history_problems(root))
    out.extend(SG.engine_zero_problems(root))
    out.extend(blob_problems(root, PREFIX, BLOB_AT))
    out.extend(commit_problems(root))
    return out


def order_problems_real(root=REPO):
    u"""封 ⊏ script と封の門 ⊏ 記録 ⊏ 結果の文書と門。未 commit は赤。"""
    out = list(PR.order_problems(root, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, [SCRIPT_REL, SEAL_GATE_REL], [RECORD_REL, DOC_REL, GATE_REL]))
    for rel in (SCRIPT_REL, SEAL_GATE_REL):
        added = PR.added_commits(root, PREFIX + rel)
        if len(added) != 1 or not added[0].startswith(SCRIPT_COMMIT_SHORT):
            out.append(u"%s を足した commit が %s でない" % (rel, SCRIPT_COMMIT_SHORT))
        rc, last = PR.git_in(root, "log", "-1", "--format=%H", "--", PREFIX + rel)
        if not last.startswith(SCRIPT_COMMIT_SHORT):
            out.append(u"%s の最後の commit が %s でない(記録を書いた後に変わった)" % (rel, SCRIPT_COMMIT_SHORT))
    rec = PR.added_commits(root, PREFIX + RECORD_REL)
    if len(rec) != 1 or not rec[0].startswith(RECORD_COMMIT_SHORT):
        out.append(u"記録を足した commit が %s でない" % RECORD_COMMIT_SHORT)
    else:
        rc, lastrec = PR.git_in(root, "log", "-1", "--format=%H", "--", PREFIX + RECORD_REL)
        if not lastrec.startswith(RECORD_COMMIT_SHORT):
            out.append(u"記録の最後の commit が %s でない" % RECORD_COMMIT_SHORT)
        for rel in (SCRIPT_REL, SEAL_GATE_REL):
            added = PR.added_commits(root, PREFIX + rel)
            if added and not PR.is_anc(root, added[0], rec[0]):
                out.append(u"記録が %s より前" % rel)
    return out


# ======================================================================================================
PREDICT = u"""
(変異を実行する前に書いた予測。右 = 赤になるべき検査。「整合」= 書類ごとの数・群の数・予測の欄を直し、recount は緑のまま当たり外れだけが変わる)
M1  記録の sha256 の写しを違う値に                                                    -> sha
M2  記録の「この script の sha256」を 1 字替える                                      -> sha
M3  記録の限界の欄の 1 行を消す                                                       -> sha
M4  書類 10 の fact の数を 1 増やす(群は直さない)                                       -> recount
M5  本番の全部決まる fact 50374 → 50373(書類ごとは直さない)                            -> recount
M6  予測の欄 XA0-2 の分母を 1 増やす                                                  -> recount
M7  材料の書類の本数 67 → 68                                                          -> recount
M8  書類 10 の書く欄の数を 1 増やす                                                    -> recount
M9  本番の断った書類の数 0 → 1                                                         -> recount
M10 本番の向き B の方が多かった表 900 → 899                                            -> recount
M11 本番の符号が合う fact を 1 減らす                                                  -> recount
M12 本番の書く欄の項「文脈の線 × 1」を 1 増やす(和は直さない)                          -> recount
M13 本番の書く欄の比の % を 44.9 → 45.0                                                -> recount
M14 記録に docid の欄を足す                                                           -> clean
M15 封の写しから XA0-2 の境の字を消す                                                  -> bound
M16 封の写しから自己点検の条を消す                                                     -> bound
M17 封の写しから「XA0-2 が当たりで XA0-4 が 60% 未満なら…」を消す                      -> bound
M18 文書の XA0-5 の判定「**外れ**(上に外れた)」を「当たり」に                            -> verdict
M19 文書の件数の行 当たり 6・外れ 1 → 当たり 7・外れ 0                                  -> verdict
M20 文書の XA0-2 のセル 50374/63236(79.7%) → 50373/63236(79.7%)                        -> verdict・frag
M21 文書の XA0-5 の「上に外れた」を「下に外れた」に                                       -> verdict
M22 §5 の「人間に示す次の便の候補」の見出しの字を消す                                     -> verdict・phrases
M23 文書の予測の字 XA0-2「75% 以上 95% 未満」を「75% 以上 96% 未満」に                    -> verdict
M24 整合: 本番の書類の全部決まる fact を減らして XA0-2 が 75% 未満(下に外れ)             -> verdict
M25 整合: 本番の書類の全部決まる fact を増やして XA0-2 が 95% 以上(上に外れ)             -> verdict
M26 整合: 本番の 40 書類を 90% 以上にして XA0-6 が外れ                                    -> verdict
M27 整合: 本番の向き B を 300 表にして XA0-5 が当たり                                      -> verdict
M28 整合: 表の外の fact を増やして XA0-1 が 97% 未満                                       -> verdict
M29 整合: 符号が合う fact を減らして XA0-3 が 98% 未満                                     -> verdict
M30 整合: 書式が合わない fact を足して XA0-7 が 98% 未満                                    -> verdict
M31 整合: 書く欄の項を増やして XA0-4 が 60% 以上                                          -> verdict
M32 整合: 全部決まる fact を 100% に(表の外 0・全部決まる = fact)で自己点検が発火          -> verdict
M33 文書 §2 の本番の fact 63236 を 63237 に(表の行)                                       -> frag・numbers
M34 文書の「`contextRef` | 10609」を 10608 に                                              -> frag・numbers
M35 文書の「書く欄の比 | 44.9%」を 44.8% に                                                -> frag・numbers
M36 文書に 9999 の言い切りを足す                                                          -> numbers
M37 文書の頭の「20.3%」を 20.4% に                                                         -> frag・numbers
M38 文書の頭の「(5 本で 37.2%)」を 37.3% に                                                -> frag・numbers
M39 文書の「約 8 割」を「約 9 割」に(数字を変えずに)                                       -> numbers(予測。実測は numbers が黙り frag が赤 = 黙った変異。表は frag に直した)
M40 §3 の 50237 を 50238 に                                                               -> sec3
M41 §3 に「7 本」を足す                                                                    -> sec3
M42 §3 の行を 1 つ丸ごと消す(「符号が合わない 74 件の型」)                                 -> sec3
M43 §3 の「19 本」を 18 本に                                                               -> sec3
M44 §3 に 3 桁の数を足した行                                                                -> sec3
M45 文書に「XBRL を作れる。」を引用の外で足す                                               -> affirm
M46 文書に「専用の道具が要らない。」を足す                                                  -> affirm
M47 文書に「人が書ける。」を足す                                                            -> affirm
M48 引用の行から「言えない」「読まない」を全部消す                                           -> affirm
M49 §5 の「言えないこと」を消す                                                             -> phrases
M50 頭の「この便からは言えない」を消す                                                       -> head
M51 頭の「先に負けと限界を書く」を消す                                                       -> head
M52 頭の「人が紙に書く値が正しいかは測っていない」を消す                                      -> head
M53 頭の「LLM の席も道具(Arelle)も呼んでいない」を消す                                       -> head
M54 文書に「保証」を足す                                                                    -> forbidden
M55 文書に docID の形を足す                                                                 -> forbidden
M56 文書の commit の字 d52b2619 を 1 字替える                                                -> commits
M57 文書に知らない commit の字を足す                                                          -> commits
M58 文書の外れの数の頭の言い切り「当たり 6・外れ 1(XA0-5)」の名を替える                       -> verdict

(1 回目の実行で外れた予測 1 つ)
- M39(「約 8 割」を「約 9 割」): 予測は numbers だったが numbers は黙った(9 は数の集合に入る)。frag が「約 8 割までは届くが、2 割は…」を記録から組んで赤になる。表は frag に直した。
"""


def rebuild(rec):
    u"""書類ごとの数・群の項はそのままに、群の導ける欄(表の中・書く欄の数・比・90% 以上の書類・予測の欄)を作り直す(整合した変更)。"""
    for g in GROUPS:
        s = rec[g]
        docs = docs_of(rec, g)
        gap = s[u"表の決めで決まる fact の数"] - s[u"全部決まる fact の数"]
        s[u"全部決まる fact の数"] = sum(d[u"全部決まる fact の数"] for d in docs)
        s[u"表の外の fact の数"] = sum(d[u"表の外の fact の数"] for d in docs)
        s[u"表の中の fact の数"] = s[u"fact の数"] - s[u"表の外の fact の数"]
        s[u"表の決めで決まる fact の数"] = min(s[u"表の中の fact の数"], s[u"全部決まる fact の数"] + gap)
        und = s[u"表の中の fact の数"] - s[u"表の決めで決まる fact の数"]
        rs = s[REASON_KEY]
        for r in REASONS:
            rs[r] = min(rs[r], und)
        if sum(rs.values()) < und:
            rs[REASONS[1]] += und - sum(rs.values())
        cl = s[CELL_KEY]
        cl[CELL_ITEMS[5]] = 7 * (s[u"表の中の fact の数"] - s[u"全部決まる fact の数"])
        cl[CELL_ITEMS[6]] = 7 * s[u"表の外の fact の数"]
        s[u"書く欄の数"] = sum(cl.values())
        s[u"表の中の fact が全部決まる場合の書く欄の数"] = s[u"書く欄の数"] - cl[CELL_ITEMS[5]]
        for key, n in ((u"書く欄の比", s[u"書く欄の数"]), (u"表の中の fact が全部決まる場合の比", s[u"表の中の fact が全部決まる場合の書く欄の数"])):
            s[key] = rate_row(n, 7 * s[u"fact の数"])
        s[DOC90] = doc90(docs)
    rec[PRED_KEY] = pred_expected(rec)


def doc_cells(rec):
    u"""書類ごとの書く欄の数を、群の項から(書類ごとの按分でなく)1 つ目の書類へ寄せて合わせる。"""
    for g in GROUPS:
        docs = docs_of(rec, g)
        total = sum(d[u"書く欄の数"] for d in docs)
        docs[0][u"書く欄の数"] += rec[g][u"書く欄の数"] - total


def set_full(rec, idx, new_full):
    d = rec[u"書類"][idx]
    d[u"全部決まる fact の数"] = new_full


def m_full_low(c):
    for d in c.rec[u"書類"][DEV_COUNT:]:
        d[u"全部決まる fact の数"] = int((d[u"fact の数"] - d[u"表の外の fact の数"]) * 0.6)
    rebuild(c.rec)
    doc_cells(c.rec)


def m_full_high(c):
    for d in c.rec[u"書類"][DEV_COUNT:]:
        d[u"全部決まる fact の数"] = d[u"fact の数"] - d[u"表の外の fact の数"]
    rebuild(c.rec)
    doc_cells(c.rec)


def m_doc90(c):
    for d in c.rec[u"書類"][DEV_COUNT:DEV_COUNT + 40]:
        d[u"全部決まる fact の数"] = max(d[u"全部決まる fact の数"], (d[u"fact の数"] * 91 + 99) // 100)
    rebuild(c.rec)
    doc_cells(c.rec)


def m_b300(c):
    s = c.rec[G_PROD]
    s[u"向き B の方が決まる fact が多かった表の数"] = 300
    s[u"向き B を選んだ表の数"] = 300
    s[u"向き A を選んだ表の数"] = s[u"fact の在る表の数"] - 300
    rebuild(c.rec)


def m_outside(c):
    for d in c.rec[u"書類"][DEV_COUNT:DEV_COUNT + 20]:
        d[u"表の外の fact の数"] += 400
    sg = c.rec[G_PROD]
    for k in (u"表の中の空でない fact の数", u"符号が合う fact の数", u"書式が合う fact の数"):
        sg[k] -= 8000
    rebuild(c.rec)
    doc_cells(c.rec)


def m_sign(c):
    s = c.rec[G_PROD]
    s[u"符号が合う fact の数"] -= 2000
    s[u"符号が合わない fact の数(負と読んだが sign が - でない)"] += 2000
    rebuild(c.rec)


def m_format(c):
    s = c.rec[G_PROD]
    s[u"書式が合う fact の数"] -= 2000
    s[u"書式が合わない fact の数"] += 2000
    rebuild(c.rec)


def m_cells_high(c):
    s = c.rec[G_PROD]
    extra = 4 * 60000
    s[CELL_KEY][CELL_ITEMS[1]] += extra
    s[u"要素の線の数(fact の在る)"] += 60000
    rebuild(c.rec)
    doc_cells(c.rec)


def m_suspect(c):
    for d in c.rec[u"書類"][DEV_COUNT:]:
        d[u"表の外の fact の数"] = 0
        d[u"全部決まる fact の数"] = d[u"fact の数"]
    rebuild(c.rec)
    doc_cells(c.rec)


def rep(c, old, new, attr="doc", count=1):
    s = getattr(c, attr)
    assert old in s, old
    setattr(c, attr, s.replace(old, new, count))


def add_doc(c, text):
    c.doc = c.doc + u"\n" + text + u"\n"


def add_sec3(c, text):
    rep(c, u"## §4 ", text + u"\n\n## §4 ")


def drop_all(c, phrase):
    assert phrase in c.doc, phrase
    c.doc = c.doc.replace(phrase, u"X")


def m_drop_line(c):
    lines = c.doc.splitlines()
    i = [k for k, ln in enumerate(lines) if u"**符号が合わない 74 件の型**" in ln][0]
    del lines[i]
    c.doc = u"\n".join(lines)


def m_no_negation(c):
    lines = []
    for ln in c.doc.splitlines():
        if QUOTED_CLAIM.search(ln):
            for w in (u"言えないこと", u"言えない", u"読まない", u"示していない"):
                ln = ln.replace(w, u"X")
        lines.append(ln)
    c.doc = u"\n".join(lines)


MUTATIONS = (
    (u"M1 記録の sha256 の写しを違う値に", lambda c: c.shas.__setitem__(RECORD_REL, u"0" * 64), (u"sha",)),
    (u"M2 記録の script の sha256 を 1 字替える", lambda c: c.rec.__setitem__(u"この script の sha256", u"f" + c.rec[u"この script の sha256"][1:]), (u"sha",)),
    (u"M3 記録の限界の欄の 1 行を消す", lambda c: c.rec.__setitem__(u"限界", c.rec[u"限界"][1:]), (u"sha",)),
    (u"M4 書類 10 の fact の数を 1 増やす", lambda c: c.rec[u"書類"][9].__setitem__(u"fact の数", c.rec[u"書類"][9][u"fact の数"] + 1), (u"recount",)),
    (u"M5 本番の全部決まる fact を 1 減らす", lambda c: c.rec[G_PROD].__setitem__(u"全部決まる fact の数", c.rec[G_PROD][u"全部決まる fact の数"] - 1), (u"recount",)),
    (u"M6 予測の欄 XA0-2 の分母を 1 増やす", lambda c: c.rec[PRED_KEY][PK[1]].__setitem__(u"分母", c.rec[PRED_KEY][PK[1]][u"分母"] + 1), (u"recount",)),
    (u"M7 材料の書類の本数を 68 に", lambda c: c.rec[u"材料"].__setitem__(u"書類の本数", 68), (u"recount",)),
    (u"M8 書類 10 の書く欄の数を 1 増やす", lambda c: c.rec[u"書類"][9].__setitem__(u"書く欄の数", c.rec[u"書類"][9][u"書く欄の数"] + 1), (u"recount",)),
    (u"M9 本番の断った書類の数を 1 に", lambda c: c.rec[G_PROD].__setitem__(u"断った書類の数", 1), (u"recount",)),
    (u"M10 本番の向き B の方が多かった表を 899 に", lambda c: c.rec[G_PROD].__setitem__(u"向き B の方が決まる fact が多かった表の数", 899), (u"recount",)),
    (u"M11 本番の符号が合う fact を 1 減らす", lambda c: c.rec[G_PROD].__setitem__(u"符号が合う fact の数", c.rec[G_PROD][u"符号が合う fact の数"] - 1), (u"recount",)),
    (u"M12 本番の書く欄の項「文脈の線 × 1」を 1 増やす", lambda c: c.rec[G_PROD][CELL_KEY].__setitem__(CELL_ITEMS[2], c.rec[G_PROD][CELL_KEY][CELL_ITEMS[2]] + 1), (u"recount",)),
    (u"M13 本番の書く欄の比の % を 45.0 に", lambda c: c.rec[G_PROD][u"書く欄の比"].__setitem__(u"%", 45.0), (u"recount",)),
    (u"M14 記録に docid の欄を足す", lambda c: c.rec[u"書類"][0].__setitem__(u"docid", u"x"), (u"clean",)),
    (u"M15 封の写しから XA0-2 の境の字を消す", lambda c: rep(c, u"全部決まる fact は、fact の 75% 以上 95% 未満", u"X", attr="seal"), (u"bound",)),
    (u"M16 封の写しから自己点検の条を消す", lambda c: rep(c, u"全部決まる fact がちょうど 100%・表の外の fact がちょうど 0", u"X", attr="seal"), (u"bound",)),
    (u"M17 封の写しから次の便の候補の決めを消す", lambda c: rep(c, u"XA0-2 が当たりで XA0-4 が 60% 未満なら、次の便の候補を人間に示す", u"X", attr="seal"), (u"bound",)),
    (u"M18 XA0-5 の判定を当たりに", lambda c: rep(c, u"**外れ**(上に外れた)", u"当たり"), (u"verdict",)),
    (u"M19 件数の行を当たり 7・外れ 0 に", lambda c: rep(c, u"- 当たり 6・外れ 1。", u"- 当たり 7・外れ 0。"), (u"verdict",)),
    (u"M20 XA0-2 のセルの 50374 を 50373 に", lambda c: rep(c, u"| 50374/63236(79.7%) |", u"| 50373/63236(79.7%) |"), (u"verdict",)),
    (u"M21 XA0-5 の「上に外れた」を「下に外れた」に", lambda c: rep(c, u"(上に外れた)", u"(下に外れた)"), (u"verdict",)),
    (u"M22 §5 の次の便の候補の見出しの字を消す", lambda c: rep(c, u"人間に示す次の便の候補**(封 §6。XA0-2 が当たり・XA0-4 が 60% 未満なので示す)", u"X"), (u"verdict", u"phrases")),
    (u"M23 XA0-2 の予測の字を 96% 未満に", lambda c: rep(c, u"75% 以上 95% 未満 |", u"75% 以上 96% 未満 |"), (u"verdict",)),
    (u"M24 整合: XA0-2 が 75% 未満", m_full_low, (u"verdict", u"sanity")),
    (u"M25 整合: XA0-2 が 95% 以上", m_full_high, (u"verdict",)),
    (u"M26 整合: 40 書類を 90% 以上に(XA0-6 が外れ)", m_doc90, (u"verdict",)),
    (u"M27 整合: 向き B を 300 表に(XA0-5 が当たり)", m_b300, (u"verdict",)),
    (u"M28 整合: 表の外を増やす(XA0-1 が外れ)", m_outside, (u"verdict",)),
    (u"M29 整合: 符号が合う fact を減らす(XA0-3 が外れ)", m_sign, (u"verdict",)),
    (u"M30 整合: 書式が合わない fact を足す(XA0-7 が外れ)", m_format, (u"verdict",)),
    (u"M31 整合: 書く欄の項を増やす(XA0-4 が 60% 以上)", m_cells_high, (u"verdict",)),
    (u"M32 整合: 自己点検が発火する形", m_suspect, (u"verdict",)),
    (u"M33 §2 の本番の fact を 63237 に", lambda c: rep(c, u"| fact | 63236 |", u"| fact | 63237 |"), (u"frag", u"numbers")),
    (u"M34 「`contextRef` | 10609」を 10608 に", lambda c: rep(c, u"| `contextRef` | 10609 |", u"| `contextRef` | 10608 |"), (u"frag", u"numbers")),
    (u"M35 「書く欄の比 | 44.9%」を 44.8% に", lambda c: rep(c, u"| 書く欄の比 | 44.9% |", u"| 書く欄の比 | 44.8% |"), (u"frag", u"numbers")),
    (u"M36 文書に 9999 の言い切りを足す", lambda c: add_doc(c, u"fact の行は 9999 本に近い。"), (u"numbers",)),
    (u"M37 頭の「20.3%」を 20.4% に", lambda c: rep(c, u"の 20.3% が収まらない", u"の 20.4% が収まらない"), (u"frag", u"numbers")),
    (u"M38 頭の「(5 本で 37.2%)」を 37.3% に", lambda c: rep(c, u"(5 本で 37.2%)", u"(5 本で 37.3%)"), (u"frag", u"numbers")),
    (u"M39 頭の「約 8 割」を「約 9 割」に", lambda c: rep(c, u"約 8 割まで", u"約 9 割まで"), (u"frag",)),
    (u"M40 §3 の 50237 を 50238 に", lambda c: rep(c, u"50237", u"50238"), (u"sec3",)),
    (u"M41 §3 に「7 本」を足す", lambda c: add_sec3(c, u"- 別に 7 本で確かめた。"), (u"sec3",)),
    (u"M42 §3 の「符号が合わない 74 件の型」の行を消す", m_drop_line, (u"sec3",)),
    (u"M43 §3 の「19 本」を 18 本に", lambda c: rep(c, u"19 本", u"18 本"), (u"sec3",)),
    (u"M44 §3 に 3 桁の数を足した行", lambda c: add_sec3(c, u"- 監査の席は、62 本のうち 2 本の表を合わせて 5 つ、さらに 100 本を読んだ。"), (u"sec3",)),
    (u"M45 文書に「XBRL を作れる。」を引用の外で足す", lambda c: add_doc(c, u"XBRL を作れる。"), (u"affirm",)),
    (u"M46 文書に「専用の道具が要らない。」を足す", lambda c: add_doc(c, u"専用の道具が要らない。"), (u"affirm",)),
    (u"M47 文書に「人が書ける。」を足す", lambda c: add_doc(c, u"紙は人が書ける。"), (u"affirm",)),
    (u"M48 引用の行から「言えない」「読まない」を消す", m_no_negation, (u"affirm",)),
    (u"M49 「言えないこと」を消す", lambda c: drop_all(c, u"言えないこと"), (u"phrases",)),
    (u"M50 頭の「この便からは言えない」を消す", lambda c: rep(c, u"、この便からは言えない。**", u"、X。**"), (u"head",)),
    (u"M51 頭の「先に負けと限界を書く」を消す", lambda c: drop_all(c, u"先に負けと限界を書く"), (u"head",)),
    (u"M52 頭の「人が紙に書く値が正しいかは測っていない」を消す", lambda c: rep(c, u"人が紙に書く値が正しいかは測っていない", u"X"), (u"head",)),
    (u"M53 頭の「LLM の席も道具(Arelle)も呼んでいない」を消す", lambda c: rep(c, u"LLM の席も道具(Arelle)も呼んでいない", u"X"), (u"head",)),
    (u"M54 文書に「保証」を足す", lambda c: add_doc(c, u"保証する。"), (u"forbidden",)),
    (u"M55 文書に docID の形を足す", lambda c: add_doc(c, u"書類 S100ABCD。"), (u"forbidden",)),
    (u"M56 文書の commit の字 d52b2619 を 1 字替える", lambda c: rep(c, u"d52b2619", u"d52b2618"), (u"commits",)),
    (u"M57 文書に知らない commit の字を足す", lambda c: add_doc(c, u"commit 1a2b3c4d。"), (u"commits",)),
    (u"M58 頭の外れの名を替える", lambda c: rep(c, u"外れ 1(XA0-5)", u"外れ 1(XA0-4)"), (u"verdict",)),
)


def run_mutations(base=None):
    base = base or Ctx()
    out = []
    for name, fn, checks in MUTATIONS:
        c = base.copy()
        fn(c)
        res = [(k, bool(guard(CHECKS[k], c))) for k in checks]
        out.append((name, res))
    return out


# ======================================================================================================
class RealTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = Ctx()

    def test_a_1_sha256_and_provenance(self):
        self.assertEqual([], sha_problems(self.c))

    def test_b_1_the_record_numbers_recount_without_the_script_functions(self):
        self.assertEqual([], recount_problems(self.c))

    def test_b_2_the_record_has_no_forbidden_fields_or_forms(self):
        self.assertEqual([], record_clean_problems(self.c))

    def test_b_3_the_derived_numbers_the_document_states(self):
        s = self.c.rec[G_PROD]
        self.assertEqual((63236, 50374, 12862, 62754, 482, 0), (s[u"fact の数"], s[u"全部決まる fact の数"], s[u"fact の数"] - s[u"全部決まる fact の数"], s[u"表の中の fact の数"],
                                                             s[u"表の外の fact の数"], s[DOC90]))
        self.assertEqual((62, 62), (s[u"書類の数"], s[u"断らなかった書類の数"]))

    def test_c_1_the_seal_has_the_bound_phrases(self):
        self.assertEqual([], bound_problems(self.c))

    def test_c_2_the_verdicts_are_decided_again_and_equal_the_document(self):
        self.assertEqual([], verdict_problems(self.c))
        j = judge(self.c.rec)
        self.assertEqual(6, sum(1 for v in j.values() if v[0]))
        self.assertEqual([(u"XA0-5", u"上")], [(k, v[1]) for k, v in j.items() if not v[0]])

    def test_d_1_every_number_in_the_document_is_bound_to_the_record(self):
        self.assertEqual([], doc_number_problems(self.c))

    def test_d_2_the_table_rows_and_the_statements_equal_the_record(self):
        self.assertEqual([], fragment_problems(self.c))
        self.assertEqual([], sanity_problems(self.c))

    def test_d_3_section3_holds_only_the_pinned_small_numbers(self):
        self.assertEqual([], sec3_problems(self.c))

    def test_e_1_the_important_phrases_are_present(self):
        self.assertEqual([], phrase_problems(self.c))

    def test_e_2_the_losses_and_limits_are_at_the_head(self):
        self.assertEqual([], head_problems(self.c))

    def test_e_3_the_document_has_no_forbidden_words_or_forms_and_no_affirmation(self):
        self.assertEqual([], forbidden_problems(self.c))
        self.assertEqual([], affirm_problems(self.c))

    def test_e_4_the_commits_the_document_names(self):
        self.assertEqual([], doc_commit_problems(self.c))

    def test_f_1_the_seal_history_the_blobs_and_the_engine(self):
        self.assertEqual([], git_problems())

    def test_f_2_order_the_seal_then_script_then_record_then_the_document_and_the_gate(self):
        u"""結果の文書と門のどちらかが未 commit なら赤(足した commit が無い。skip にしない)。両方 commit された後で初めて緑。"""
        self.assertEqual([], order_problems_real())

    def test_f_3_the_order_check_is_green_for_good_history_and_red_for_bad(self):
        r = PR.Repo()
        r.put("docs/seal.md")
        s = r.commit("docs/seal.md")
        r.put("measure/s.py")
        r.commit("measure/s.py")
        others = ["fix/r.json", "docs/d.md", "tests/g.py"]
        for f in others:
            r.put(f)
        r.commit(*others)
        self.assertEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], ["measure/s.py"], others))
        r.put("docs/new.md")
        self.assertNotEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], ["measure/s.py"], others + ["docs/new.md"]))

    def test_f_4_the_blob_check_is_green_for_an_untouched_file_and_red_for_a_changed_one(self):
        r = PR.Repo()
        r.put("measure/s.py")
        c1 = r.commit("measure/s.py")
        at = {"measure/s.py": c1[:8]}
        self.assertEqual([], blob_problems(r.d, PREFIX, at))
        with open(os.path.join(r.d, PREFIX, "measure/s.py"), "a", encoding="utf-8") as fh:
            fh.write(u"# 結果の便で足した 1 行\n")
        self.assertNotEqual([], blob_problems(r.d, PREFIX, at))
        self.assertNotEqual([], blob_problems(r.d, PREFIX, {"measure/s.py": "0000000"}))

    def test_f_5_the_blob_check_lists_the_four_frozen_files_at_their_commits(self):
        self.assertEqual([SEAL_REL, SCRIPT_REL, SEAL_GATE_REL, RECORD_REL], list(BLOB_AT))
        self.assertEqual([SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT], list(BLOB_AT.values()))
        self.assertEqual((SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT), DOC_COMMITS)

    def test_f_6_the_commit_history_check_matches_the_real_history(self):
        self.assertEqual([], commit_problems())


class MutationTest(unittest.TestCase):
    def test_g_1_every_mutation_turns_its_checks_red_and_the_files_are_unchanged(self):
        before = tuple(sha_file(r) for r in list(SHA_PIN) + [DOC_REL])
        base = Ctx()
        results = run_mutations(base)
        self.assertEqual(before, tuple(sha_file(r) for r in list(SHA_PIN) + [DOC_REL]))
        self.assertEqual(len(MUTATIONS), len(results))
        silent = [(n, k) for n, res in results for k, red in res if not red]
        self.assertEqual([], silent)
        self.assertGreaterEqual(len(MUTATIONS), 40)

    def test_g_2_the_unmutated_copy_is_green_on_every_check(self):
        c = Ctx().copy()
        for k, fn in CHECKS.items():
            self.assertEqual([], fn(c), k)

    def test_g_3_the_recount_stays_green_when_the_data_changes_consistently_but_the_verdict_does_not(self):
        for fn, key in ((m_full_low, u"XA0-2"), (m_full_high, u"XA0-2"), (m_doc90, u"XA0-6"), (m_b300, u"XA0-5"), (m_outside, u"XA0-1"), (m_sign, u"XA0-3"), (m_format, u"XA0-7"),
                        (m_cells_high, u"XA0-4")):
            c = Ctx().copy()
            fn(c)
            self.assertEqual([], recount_problems(c), fn.__name__)
            self.assertNotEqual([], verdict_problems(c), fn.__name__)
            self.assertNotEqual(judge(Ctx().rec)[key][0], judge(c.rec)[key][0], (fn.__name__, key))

    def test_g_4_every_check_name_a_mutation_names_exists_and_every_check_has_a_mutation(self):
        named = set(k for _, _, ks in MUTATIONS for k in ks)
        self.assertEqual(set(CHECKS), named)

    def test_g_5_the_judgement_edges_at_the_seal_bounds(self):
        u"""境の 1 つ手前と境の数(丸める前の整数): XA0-2 は 75% ちょうどが当たり・95% ちょうどが外れ(上が含まない)。XA0-5 は 30% ちょうどが当たり(上が含む)・5% ちょうどが当たり。"""
        def with_(**kw):
            c = Ctx().copy()
            s = c.rec[G_PROD]
            s[u"fact の数"] = 1000
            s[u"表の外の fact の数"] = 0
            s[u"表の中の fact の数"] = 1000
            s[u"表の中の空でない fact の数"] = 1000
            s[u"符号が合う fact の数"] = 1000
            s[u"書式が合う fact の数"] = 1000
            s[u"fact の在る表の数"] = 100
            s[u"全部決まる fact の数"] = 800
            s[u"書く欄の数"] = 3000
            s[u"向き B の方が決まる fact が多かった表の数"] = 10
            s[DOC90] = 10
            for k, v in kw.items():
                s[k] = v
            return judge(c.rec)
        self.assertTrue(with_(**{u"全部決まる fact の数": 750})[u"XA0-2"][0])
        self.assertFalse(with_(**{u"全部決まる fact の数": 749})[u"XA0-2"][0])
        self.assertFalse(with_(**{u"全部決まる fact の数": 950})[u"XA0-2"][0])
        self.assertTrue(with_(**{u"全部決まる fact の数": 949})[u"XA0-2"][0])
        self.assertTrue(with_(**{u"向き B の方が決まる fact が多かった表の数": 30})[u"XA0-5"][0])
        self.assertFalse(with_(**{u"向き B の方が決まる fact が多かった表の数": 31})[u"XA0-5"][0])
        self.assertTrue(with_(**{u"向き B の方が決まる fact が多かった表の数": 5})[u"XA0-5"][0])
        self.assertFalse(with_(**{u"向き B の方が決まる fact が多かった表の数": 4})[u"XA0-5"][0])
        self.assertTrue(with_(**{u"表の中の fact の数": 970})[u"XA0-1"][0])
        self.assertFalse(with_(**{u"表の中の fact の数": 969})[u"XA0-1"][0])
        self.assertTrue(with_(**{u"書く欄の数": 2450})[u"XA0-4"][0])
        self.assertFalse(with_(**{u"書く欄の数": 2449})[u"XA0-4"][0])
        self.assertFalse(with_(**{u"書く欄の数": 4200})[u"XA0-4"][0])
        self.assertTrue(with_(**{u"書く欄の数": 4199})[u"XA0-4"][0])
        self.assertTrue(with_(**{DOC90: 30})[u"XA0-6"][0])
        self.assertFalse(with_(**{DOC90: 31})[u"XA0-6"][0])
        self.assertTrue(with_(**{u"符号が合う fact の数": 980})[u"XA0-3"][0])
        self.assertFalse(with_(**{u"符号が合う fact の数": 979})[u"XA0-3"][0])
        self.assertTrue(with_(**{u"書式が合う fact の数": 980})[u"XA0-7"][0])
        self.assertFalse(with_(**{u"書式が合う fact の数": 979})[u"XA0-7"][0])

    def test_g_6_the_miss_direction_follows_the_bound(self):
        u"""下限を割れば「下に外れた」・上限を超えれば「上に外れた」。"""
        c = Ctx().copy()
        m_full_low(c)
        self.assertEqual(u"下", judge(c.rec)[u"XA0-2"][1])
        c = Ctx().copy()
        m_full_high(c)
        self.assertEqual(u"上", judge(c.rec)[u"XA0-2"][1])
        self.assertEqual(u"上", judge(Ctx().rec)[u"XA0-5"][1])

    def test_g_7_the_percent_rounds_half_up_with_integers(self):
        self.assertEqual(u"0.1", pct(1, 1000 * 2))        # 0.05% は上げる
        self.assertEqual(u"79.7", pct(50374, 63236))
        self.assertEqual(u"44.9", pct(198942, 442652))


if __name__ == "__main__":
    unittest.main()
