# -*- coding: utf-8 -*-
"""結果の門: 封 docs/XBRL_NIL_READ_SEAL_2026-11-17.md(720a473d)の結果の文書 docs/XBRL_NIL_READ_RESULT_2026-11-17.md。

封の門 ``test_xbrl_nil_read_seal.py`` の次の段。**追跡されている記録・script・封・結果の文書だけを読む**(材料は読まない。数秒で終わる。全数の作り直しは走らせない)。

縛るもの(検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表で 1 本ずつ。木の file は変異させず、``Ctx`` の写しに当てる)
 a script・states の記録・便 PS の states の記録の sha256(字で留める)
 b 記録の中の整合: 封の門の ``record_problems``(行・本ごとの欄からの数え直し・TSS の記録との対応・文や値の漏れ)
 c 結果の文書の数: 表の行も散文の行も、記録から組んだ 1 行と字で同じ(1 行ずつ。文書の行が 1 回ずつ在る)。そのどれにも当たらない行の 2 桁以上の数は、組んだ行の数の集合に在るものだけ
 d 予測 NR-1〜NR-6 の判定を、封の予測の字から取った境と記録の行・本ごとの欄から門が自分で決め直して、文書の表と同じ・字で留めた判定(NR-1 外れ・NR-3 外れ・ほか当たり)と同じ
 e 文書に「証明した」「ハルシネーション」・会社名らしい字・3 桁以上の漢数字が無い・要点の字が在る
 f 封が commit から 1 字も変わっていない・順序(commit の順。未 commit は赤)・engine 0 行
この file は docID の字を持たない。
"""
import collections
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
sys.path.insert(0, os.path.join(ROOT, "measure"))


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


SG = load_module("tests/measure/test_xbrl_nil_read_seal.py", "nr_seal_gate_for_nr_result_gate")      # 封の門の部品。門としては走らせない
PR = SG.PR

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
STATES_REL = SG.RECORD_REL
PS_STATES_REL = "fixtures/xbrl/plan_source/states_2026-11-17.json"
GATE_REL = "tests/measure/test_xbrl_nil_read_result.py"
DOC_REL = "docs/XBRL_NIL_READ_RESULT_2026-11-17.md"
IMPL_COMMIT = "44ba3e61"                                     # script・封の門・states の記録を足した commit

SHA_PIN = collections.OrderedDict([
    (STATES_REL, "16c07159f88973932f70e9c422734330dcdf7893b6ca26ed2898623b614c3864"),
    (SCRIPT_REL, "f1489d091a55d420052b8f208d344d237b7f168ac0d66b6f2170b7d5f35e7ac4"),
    (PS_STATES_REL, "d007b1454c0b4c6f30b3627d54221376767d0f0a1233578dbd37bcfe2df51424")])

K_FACT, K_JUDGE, K_KEYS, K_PRED, K_INV, K_TB, K_BOOKS = SG.K_FACT, SG.K_JUDGE, SG.K_KEYS, SG.K_PRED, SG.K_INV, SG.K_TB, SG.K_BOOKS
K_ROUTES_V = u"verify_document に渡す ZIP の経路"
K_ROUTES_B = u"build_raw_claims に渡す ZIP の経路"
K_TB_ROWS = u"本ごと([その便の表の行番号, verify_document の経路, build_raw_claims の経路, 自己閉じの数])"
K_SELF_PS = u"自己閉じの tag から始まる読み取り(engine と同じ正規表現の一致のうち属性の列が / で終わるもの)"
STATES = SG.STATES
ROUTES = SG.ROUTES
NR_IDS = (u"NR-1", u"NR-2", u"NR-3", u"NR-4", u"NR-5", u"NR-6")
HIT, MISS = u"当たり", u"**外れ**"
NR_VERDICT_PINNED = (MISS, HIT, MISS, HIT, HIT, HIT)

FORBIDDEN_WORDS = (u"証明" + u"した", u"ハルシ" + u"ネーション", u"精" + u"度", u"世界で 1 " + u"社")
COMPANY_WORDS = (u"株式会社", u"有限会社", u"合同会社", u"㈱", u"(株)")
DOCID_RE = re.compile(r"S100[0-9A-Z]{4}")
POINTER_RE = re.compile(r"xbrl:|jppfs|jpcrp|jpdei|_cor:|@(Current|Prior)|formula:")
KANJI_NUM_RE = re.compile(u"[二三四五六七八九]百|[一二三四五六七八九]千|百[一二三四五六七八九十]|千[一二三四五六七八九百]")
HUMAN_EYE_RE = re.compile(u"人の" + u"目")
REQUIRED_PHRASES = (u"先に負けと限界を書く", u"外れ", u"当たり", u"広すぎ", u"直していない", u"確かめていない", u"人間の決定", u"限界", u"期の取り違え", u"偽の一致", u"engine は 0 行",
                    u"監査では走らせていない", u"数える対象が違う")


# ======================================================================================================
# 道具
def read(rel, root=ROOT):
    with io.open(os.path.join(root, rel), encoding="utf-8") as fh:
        return fh.read()


def read_bytes(rel, root=ROOT):
    with io.open(os.path.join(root, rel), "rb") as fh:
        return fh.read()


def guard(fn, *a, **k):
    try:
        return fn(*a, **k)
    except BaseException as exc:                   # noqa: BLE001  変異で落ちた検査は「問題」として数える
        return [u"例外: %s" % type(exc).__name__]


def rate_text(n, d):
    u"""小数 1 桁の %(四捨五入は整数の計算。script の ``rate`` と同じ決め方を門の側で独立に書く)。"""
    return u"分母 0" if d == 0 else u"%d.%d%%" % divmod((n * 2000 + d) // (2 * d), 10)


def frac(n, d):
    return u"%d/%d(%s)" % (n, d, rate_text(n, d))


class Ctx(object):
    u"""記録・封・文書・字の写し。変異は毎回 ``Ctx()`` の新しい写しに 1 か所だけ加える。"""

    def __init__(self):
        self.st = json.loads(read(STATES_REL), object_pairs_hook=collections.OrderedDict)
        self.ps = json.loads(read(PS_STATES_REL), object_pairs_hook=collections.OrderedDict)
        self.seal = read(SEAL_REL)
        self.doc = read(DOC_REL)
        self.texts = collections.OrderedDict((rel, read_bytes(rel)) for rel in SHA_PIN)


# ======================================================================================================
# 行・本ごとの欄からの数え直し(門の側で独立に)
def counts(c):
    rows = c.st[u"行"]
    books = c.st[K_BOOKS]
    tb = c.st[K_TB]
    tb_rows = tb[K_TB_ROWS]
    trans = collections.Counter((r[3], r[4]) for r in rows)
    changed = [r for r in rows if r[3] != r[4]]
    return {
        u"rows": len(rows), u"books": len(books), u"trans": trans,
        u"changed": len(changed), u"changed_books": len(set(r[0] for r in changed)),
        u"same_reason_diff": sum(1 for r in rows if r[3] == r[4] and not r[5]),
        u"only_as": sum(1 for r in rows if r[3] == u"GROUNDED" and r[4] != u"GROUNDED"),
        u"only_fx": sum(1 for r in rows if r[3] != u"GROUNDED" and r[4] == u"GROUNDED"),
        u"nil": sum(b[1] for b in books), u"nil_books": sum(1 for b in books if b[1] > 0),
        u"made": sum(b[2] for b in books), u"made_books": sum(1 for b in books if b[2] > 0),
        u"gone": sum(b[3] for b in books), u"gone_books": sum(1 for b in books if b[3] > 0),
        u"either_books": sum(1 for b in books if b[2] > 0 or b[3] > 0), u"swap": sum(b[4] for b in books),
        u"tb_n": len(tb_rows), u"tb_htm_nil": sum(1 for r in tb_rows if (r[1] == u".htm の経路" or r[2] == u".htm の経路") and r[3] > 0),
        u"tb_htm": sum(1 for r in tb_rows if r[1] == u".htm の経路" or r[2] == u".htm の経路"),
    }


# ======================================================================================================
# a. sha256
def sha_problems(texts, pin=None):
    pin = SHA_PIN if pin is None else pin
    return [u"sha256: %s が字で留めた値と違う" % rel for rel, want in pin.items() if hashlib.sha256(texts.get(rel, b"")).hexdigest() != want]


TOP_KEYS = (u"seal", u"封の commit", u"step", u"この script の sha256", u"入力", u"engine の指紋", u"profile", u"材料", u"棚卸し(封 §1 の 1)", u"2026-11-09 の便の ZIP(封 §1 の 3)",
            u"直した入力の規則(封 §2-2)", u"独立の読みの確認(封 §2-1)", u"作り直しの確認", u"fact の差(封 §2-3)", u"判定の差(封 §2-4)", SG.K_KEYS, SG.K_PRED, u"本ごとの欄",
            SG.K_BOOKS, u"限界", u"行の欄", u"時間(秒)", u"key_leaks", u"行")


# ======================================================================================================
# b. 記録の中の整合(封の門の部品。行・本ごとの欄からの数え直し・TSS の記録との対応・文や値の漏れ・script の集計関数)
def record_problems(c):
    out = list(SG.record_problems(text=json.dumps(c.st, ensure_ascii=False)))
    if tuple(c.st) != TOP_KEYS:
        out.append(u"記録の最上位の欄が決めた一覧と違う(文・値などの足された欄の疑い)")
    ps_sc = c.ps[u"サマリーの fact"].get(K_SELF_PS)
    if not isinstance(ps_sc, dict) or u"短信の本体(Attachment の側の .htm)" not in ps_sc:
        out.append(u"便 PS の記録に自己閉じの読み取りの欄が無い")
    return out


# ======================================================================================================
# d. 予測の判定(封の予測の字から境を取り、記録の行・本ごとの欄から決め直す)
def seal_row(seal, pid):
    sec = seal[seal.index(u"## §3"):] if u"## §3" in seal else u""
    m = re.search(r"^\| %s \| (.*?) \| (.*?) \|$" % re.escape(pid), sec, re.M)
    return m.group(1) if m else u""


def seal_bounds(seal):
    u"""封の予測の字(太字の境)から数を取る。取れなければ例外(= 検査が赤)。"""
    r1 = re.search(r"\*\*(\d+)% 以上 (\d+)% 以下\*\*", seal_row(seal, u"NR-1"))
    r2 = re.search(r"\*\*(\d+) 倍以上\*\*.*?前者が (\d+) 行以上", seal_row(seal, u"NR-2"))
    r3 = re.search(r"\*\*(\d+) 行以上 (\d+) 行以下\*\*", seal_row(seal, u"NR-3"))
    r4 = re.search(r"\*\*(\d+) 割以上\*\*", seal_row(seal, u"NR-4"))
    r5 = re.search(r"\*\*(\d+) 割以上\*\*", seal_row(seal, u"NR-5"))
    r6 = re.search(r"\.htm` の経路で自己閉じを持つ本は (\d+)", seal_row(seal, u"NR-6"))
    return {u"NR-1": (int(r1.group(1)), int(r1.group(2))), u"NR-2": (int(r2.group(1)), int(r2.group(2))), u"NR-3": (int(r3.group(1)), int(r3.group(2))),
            u"NR-4": int(r4.group(1)), u"NR-5": int(r5.group(1)), u"NR-6": int(r6.group(1))}


def nr_judge(c):
    u"""[(id, 当たり?)]。封の字の境と、行・本ごとの欄からの数え直し(counts)から決める。"""
    b = seal_bounds(c.seal)
    n = counts(c)
    lo1, hi1 = b[u"NR-1"]
    ok1 = lo1 * n[u"rows"] <= n[u"changed"] * 100 <= hi1 * n[u"rows"]
    mult, minrows = b[u"NR-2"]
    ok2 = (n[u"only_fx"] >= minrows) if n[u"only_as"] == 0 else (n[u"only_fx"] >= mult * n[u"only_as"])
    lo3, hi3 = b[u"NR-3"]
    ok3 = lo3 <= n[u"only_as"] <= hi3
    ok4 = n[u"made"] > 0 and n[u"swap"] * 10 >= n[u"made"] * b[u"NR-4"]
    ok5 = n[u"nil_books"] > 0 and n[u"changed_books"] * 10 >= n[u"nil_books"] * b[u"NR-5"]
    ok6 = n[u"tb_htm_nil"] <= b[u"NR-6"]
    return [(u"NR-1", ok1), (u"NR-2", ok2), (u"NR-3", ok3), (u"NR-4", ok4), (u"NR-5", ok5), (u"NR-6", ok6)]


def verdicts(c):
    return tuple(HIT if ok else MISS for _i, ok in nr_judge(c))


def judge_problems(c):
    out = []
    got = verdicts(c)
    if got != NR_VERDICT_PINNED:
        out.append(u"judge: 決め直した判定が字で留めた判定と違う: %s" % (u" ".join(got),))
    pr = c.st[K_PRED]
    n = counts(c)
    # 記録の予測の欄(script が書いた分子・分母)と門の数え直しが同じ
    if pr.get(u"NR-1 state が変わった行 / 全部の行") != collections.OrderedDict([(u"分子", n[u"changed"]), (u"分母", n[u"rows"]), (u"率", rate_text(n[u"changed"], n[u"rows"]))]):
        out.append(u"judge: NR-1 の欄が数え直しと違う")
    if pr.get(u"NR-3 そのままでだけ値が合う行") != n[u"only_as"]:
        out.append(u"judge: NR-3 の欄が数え直しと違う")
    return out


# ======================================================================================================
# c. 結果の文書の行(記録から組む)
def expected_lines(c):
    u"""[(名前, 文書に 1 回ずつ在るはずの 1 行)]。数は全部ここで記録から組む。"""
    n = counts(c)
    b = seal_bounds(c.seal)
    fb, jb, inv, tb = c.st[K_FACT], c.st[K_JUDGE], c.st[K_INV], c.st[K_TB]
    ps_sc = c.ps[u"サマリーの fact"][K_SELF_PS][u"短信の本体(Attachment の側の .htm)"]
    vd = verdicts(c)
    meas = collections.OrderedDict([
        (u"NR-1", frac(n[u"changed"], n[u"rows"])),
        (u"NR-2", u"直した入力でだけ %d 行・そのままでだけ %d 行" % (n[u"only_fx"], n[u"only_as"])),
        (u"NR-3", u"%d 行" % n[u"only_as"]),
        (u"NR-4", frac(n[u"swap"], n[u"made"])),
        (u"NR-5", frac(n[u"changed_books"], n[u"nil_books"])),
        (u"NR-6", frac(n[u"tb_htm_nil"], n[u"tb_n"]))])
    E = []
    hits = [i for i, v in zip(NR_IDS, vd) if v == HIT]
    misses = [i for i, v in zip(NR_IDS, vd) if v == MISS]
    E.append((u"lead 予測", u"- 予測 %d 本のうち、%s が外れ・%s が当たり(当たり %d・外れ %d)。" % (len(NR_IDS), u" と ".join(misses), u"・".join(hits), len(hits), len(misses))))
    E.append((u"lead 効き", u"- **司令塔は欠陥の効きを大きく見すぎていた。** state が変わった行は %s で、全部の行の %d%% に届かない(NR-1 の下の線は %d%%)。変わった行を持つ本は %d 本(自己閉じを持つ本 %d 本のうち)。" % (
        meas[u"NR-1"], b[u"NR-1"][0], b[u"NR-1"][0], n[u"changed_books"], n[u"nil_books"])))
    E.append((u"lead 偽の一致", u"- **偽の一致(そのままでだけ値が合う行 = 作られた fact に頼っていた一致)は %d 行だった。** 直した入力でだけ値が合う行は %d 行(欠陥は一致を減らす向きに効いていた)。" % (n[u"only_as"], n[u"only_fx"])))
    E.append((u"lead 幅", u"- NR-4 は %s で当たったが、全部(%s)になったので、封の幅(%d 割以上)が広すぎた。当たりの判定が 5 割でも 10 割でも変わらない。" % (meas[u"NR-4"], rate_text(n[u"swap"], n[u"made"]), b[u"NR-4"])))
    E.append((u"table head", u"| # | 予測(封の字) | 実測(記録の分子・分母) | 判定 |"))
    for i, v in zip(NR_IDS, vd):
        E.append((u"table " + i, u"| %s | %s | %s | %s |" % (i, seal_row(c.seal, i), meas[i], v)))
    E.append((u"pred_count", u"- 当たり %d(%s)・外れ %d(%s)。外れの NR-1 は下の線(%d%%)に届かず、NR-3 は下の線(%d 行)に届かなかった。" % (
        len(hits), u"・".join(hits), len(misses), u"・".join(misses), b[u"NR-1"][0], b[u"NR-3"][0])))
    # 棚卸し
    names = inv[u"封が字で書いた数と一致した folder"]
    per = inv[u"folder ごと"]
    with_zip = sorted(k for k, v in per.items() if v[u"ZIP として読める file"] > 0)
    same_set = u"(封が字で書いた folder %d と同じ)" % len(names) if with_zip == sorted(names) else u"(封が字で書いた folder %d とは違う)" % len(names)
    E.append((u"inv 概要", u"- `~/.cache/audit-core/` の folder は %d・うち ZIP として読める file が在るもの %d%s。ZIP として読める file の合計は %d。" % (
        len(per), len(with_zip), same_set, inv[u"ZIP として読める file の合計"])))
    E.append((u"inv head", u"| folder | `.xbrl` の経路 | `.htm` の経路 | どちらも無い | ZIP として読める file |"))
    for nm in names:
        v = per[nm]
        E.append((u"inv " + nm, u"| `%s` | %d | %d | %d | %d |" % (nm, v[ROUTES[0]], v[ROUTES[1]], v[ROUTES[2]], v[u"ZIP として読める file"])))
    tot = inv[u"経路ごとの合計"]
    E.append((u"inv 合計", u"| 合計 | %d | %d | %d | %d |" % (tot[ROUTES[0]], tot[ROUTES[1]], tot[ROUTES[2]], inv[u"ZIP として読める file の合計"])))
    # fact の差
    uncut = c.st[u"作り直しの確認"][u"本"] - fb[u"切れた本"]
    E.append((u"fact 本", u"- 切れた本 %d(TSS の 400 本のうち。切れない本 %d は fact も行も無く、数に入らない)。独立の読みと直した入力の engine の fact が同じだった本は %d/%d。" % (
        fb[u"切れた本"], uncut, c.st[u"独立の読みの確認(封 §2-1)"][u"直した入力の engine の fact と要素名・context・単位・decimals・値の多重集合が同じ本"], c.st[u"独立の読みの確認(封 §2-1)"][u"確かめた本"])))
    E.append((u"fact 自己閉じ", u"- 自己閉じの tag(消した数): %d 個・%d 本(切れた本のうち)。" % (n[u"nil"], n[u"nil_books"])))
    E.append((u"fact engine", u"- engine の読み取りのうち自己閉じの tag から始まるもの: %d。" % fb[u"engine の読み取りのうち自己閉じの tag から始まるもの"]))
    E.append((u"fact 作られた", u"- 作られた fact(そのままに在って直した入力に無い): %d・作られた fact を持つ本 %d。" % (n[u"made"], n[u"made_books"])))
    E.append((u"fact 消えた", u"- 消えた fact(直した入力に在ってそのままに無い): %d・消えた fact を持つ本 %d。" % (n[u"gone"], n[u"gone_books"])))
    E.append((u"fact どちらか", u"- 作られた fact か消えた fact が 1 つ以上の本: %d%s。" % (
        n[u"either_books"], u"(自己閉じを持つ本と同じ数)" if n[u"either_books"] == n[u"nil_books"] else u"(自己閉じを持つ本 %d と違う)" % n[u"nil_books"])))
    E.append((u"fact 期", u"- 期の取り違えの形(作られた fact のうち、同じ要素名で context が違う fact が消えた側に在るもの): %s。" % frac(n[u"swap"], n[u"made"])))
    # 判定の差
    E.append((u"judge 行", u"- 行の数(切れた本の全部): %d。「そのまま」の行は TSS の記録の行と本ごとに全部同じ(%d/%d 本)。" % (
        n[u"rows"], c.st[u"作り直しの確認"][u"「そのまま」の本が TSS の記録の本と全部同じ本"], c.st[u"作り直しの確認"][u"本"])))
    E.append((u"trans head", u"| そのまま \\ 直した入力 | " + u" | ".join(STATES) + u" |"))
    for a in STATES:
        E.append((u"trans " + a, u"| %s | " % a + u" | ".join(u"%d" % n[u"trans"].get((a, z), 0) for z in STATES) + u" |"))
    E.append((u"st head", u"| state | そのまま | 直した入力 | 差 |"))
    for s in STATES:
        a = sum(v for (x, _y), v in n[u"trans"].items() if x == s)
        z = sum(v for (_x, y), v in n[u"trans"].items() if y == s)
        E.append((u"st " + s, u"| %s | %d | %d | %+d |" % (s, a, z, z - a)))
    E.append((u"judge 変わった", u"- state が変わった行: %s・変わった行を持つ本 %d(自己閉じを持つ本 %d 本の %s)。" % (
        meas[u"NR-1"], n[u"changed_books"], n[u"nil_books"], rate_text(n[u"changed_books"], n[u"nil_books"]))))
    E.append((u"judge 向き", u"- そのままで GROUNDED だった行のうち、直した入力で GROUNDED でなくなった行(偽の一致): %d。直した入力でだけ GROUNDED の行: %d。" % (n[u"only_as"], n[u"only_fx"])))
    E.append((u"judge reason", u"- state は同じで reason だけ変わった行: %d。" % n[u"same_reason_diff"]))
    keys = c.st[K_KEYS]
    E.append((u"judge 鍵", u"- 集計の鍵(TSS の記録の集計の数の葉の全部): %d・そのうち直した入力で差が 0 でないもの %d。" % (len(keys), sum(1 for k in keys if k[3] != 0))))
    # 便 2026-11-09
    E.append((u"便 0911", u"- 便 2026-11-09 の短信の本 %d。verify_document に渡す ZIP の経路: `.xbrl` %d・`.htm` %d・どちらも無い %d。build_raw_claims に渡す ZIP の経路: `.xbrl` %d・`.htm` %d・どちらも無い %d。" % (
        tb[u"本"], tb[K_ROUTES_V][ROUTES[0]], tb[K_ROUTES_V][ROUTES[1]], tb[K_ROUTES_V][ROUTES[2]], tb[K_ROUTES_B][ROUTES[0]], tb[K_ROUTES_B][ROUTES[1]], tb[K_ROUTES_B][ROUTES[2]])))
    E.append((u"便 0911 自己閉じ", u"- `.htm` の経路を通る本 %d・`.htm` の経路で自己閉じを持つ本 %d・その本の自己閉じの数の合計 %d。NR-6 は %s。" % (
        tb[u".htm の経路を通る本"], tb[u".htm の経路で自己閉じを持つ本"], tb[u".htm の経路の本の自己閉じの数の合計"], meas[u"NR-6"])))
    # 便 PS の数との違い
    E.append((u"ps 数", u"- 便 PS の記録の短信の本体の欄: %d 個・%d 本(本は 400 本の全部。数えた物 = engine と同じ正規表現の一致のうち属性の列が / で終わるもの)。" % (
        ps_sc[u"読み取りの数"], ps_sc[u"その読み取りを持つ本"])))
    E.append((u"ps この便", u"- この便の記録: %d 個・%d 本(本は切れた %d 本。数えた物 = `<ix:nonFraction[^>]*/>` に当たる自己閉じの tag の全部)。" % (n[u"nil"], n[u"nil_books"], fb[u"切れた本"])))
    E.append((u"ps 同じ種類", u"- この便にも便 PS と同じ種類の数が在る: %d(engine の読み取りのうち自己閉じの tag から始まるもの。切れた %d 本)。" % (fb[u"engine の読み取りのうち自己閉じの tag から始まるもの"], fb[u"切れた本"])))
    # 読める事・次
    E.append((u"read 向き", u"- TSS の states の数は、この欠陥で「合った」が増える向きには動いていない(GROUNDED から出た行は %d)。直した入力でだけ合う行は %d。" % (n[u"only_as"], n[u"only_fx"])))
    E.append((u"read 消えた", u"- 消えた fact は %d と多いが、判定に届いたのは一部(state が変わった行 %d・変わった行を持つ本 %d)。" % (n[u"gone"], n[u"changed"], n[u"changed_books"])))
    E.append((u"next", u"- engine の読み取りを直すか(人間の決定)。直すなら別の封で、この便と同じ数(state が変わった行 %d/%d・直した入力でだけ合う行 %d)が出ることを確かめる。" % (n[u"changed"], n[u"rows"], n[u"only_fx"])))
    E.append((u"limit reason", u"- state が同じでも、engine が選んだ fact が違う行は reason の字でしか見えない(reason だけ変わった行 %d)。" % n[u"same_reason_diff"]))
    return E


NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")


def numbers_of(text, min_digits=2):
    out = set()
    for m in NUM_RE.findall(text):
        s = m.rstrip(u",").replace(u",", u"")
        if len(s.split(u".")[0]) >= min_digits:
            out.add(s)
    return out


def prose_clean(line):
    t = re.sub(r"`[^`]*`", u"", line)
    t = t.replace(u"sha256", u"")
    t = re.sub(r"\d{4}-\d{2}-\d{2}", u"", t)
    t = re.sub(r"\b[0-9a-f]{7,}\b", u"", t)
    t = re.sub(r"https?://\S+|\S+\.(?:md|py|json)\b", u"", t)
    t = re.sub(r"\b[A-Z]+-?\d+[A-Z]*\b", u"", t)
    t = re.sub(u"§[0-9\\-]+", u"", t)
    return t


def doc_problems(c):
    doc = c.doc
    out = []
    lines = doc.split(u"\n")
    exp = expected_lines(c)
    names = [n for n, _l in exp]
    if len(set(names)) != len(names):
        out.append(u"文書: 組んだ行の名前が重なる")
    for n, line in exp:
        k = lines.count(line)
        if k != 1:
            out.append(u"文書: 記録から組んだ行「%s」が文書に 1 回ずつ無い(%d 回): %s" % (n, k, line[:40]))
    expset = set(l for _n, l in exp)
    allowed = set()
    for _n, line in exp:
        allowed |= numbers_of(line)
    for ln, line in enumerate(lines, 1):
        if line in expset:
            continue
        bad = sorted(numbers_of(prose_clean(line)) - allowed)
        if bad:
            out.append(u"文書: 組んだ行の外の数が記録から作った数の集合に無い: 行 %d %s" % (ln, u",".join(bad)))
    return out + words_problems(c)


def words_problems(c):
    doc = c.doc
    out = []
    for w in FORBIDDEN_WORDS:
        if w in doc:
            out.append(u"words: 禁止語 %s" % w)
    if HUMAN_EYE_RE.search(doc):
        out.append(u"words: 禁止語(人の目)")
    for w in COMPANY_WORDS:
        if w in doc:
            out.append(u"words: 会社名らしい字 %s" % w)
    if DOCID_RE.search(doc) or POINTER_RE.search(doc):
        out.append(u"words: docID・pointer の形の字がある")
    for ln, line in enumerate(doc.split(u"\n"), 1):
        if KANJI_NUM_RE.search(line):
            out.append(u"words: 3 桁以上の数を漢数字で書いている: 行 %d" % ln)
    for need in (os.path.basename(SEAL_REL), SEAL_COMMIT_SHORT, IMPL_COMMIT, os.path.basename(SCRIPT_REL), os.path.basename(STATES_REL)) + REQUIRED_PHRASES:
        if need not in doc:
            out.append(u"words: 要点の字が無い: %s" % need)
    return out


LEAD_HEAD = u"**先に負けと限界を書く。**"
LEAD_NEXT = u"## §1 "
LIMIT_HEAD = u"## §8 "
LIMIT_NEXT = u"## §9 "
LEAD_ENGINE_LINE = u"- engine の読み取りは直していない(engine は 0 行)。直すかどうかは人間の決定。"
LIMIT_SCOPE_LINE = u"- この結果は、`--check` の全数の作り直し(材料の 400 本を作り直す重い走らせ直し)を監査では走らせていない。監査が見たのは記録の行からの数え直しだけ。"
LIMIT_GATE_LINE = u"- 封の門が縛っていない小さな所が 2 つ在る(監査が挙げた): 外の部品に渡す引数の一部・守りの止めの呼び。"


def section(doc, head, nxt=None):
    if head not in doc:
        return u""
    t = doc[doc.index(head):]
    if nxt is not None and nxt in t[len(head):]:
        t = t[:len(head) + t[len(head):].index(nxt)]
    return t


def limits_problems(c):
    u"""要点の行(負けの節・限界の節)が決めた節に 1 回ずつ在る。"""
    out = []
    lead = section(c.doc, LEAD_HEAD, LEAD_NEXT).split(u"\n")
    lim = section(c.doc, LIMIT_HEAD, LIMIT_NEXT).split(u"\n")
    exp = dict(expected_lines(c))
    for name, line, where in ((u"lead 予測", exp[u"lead 予測"], lead), (u"lead 効き", exp[u"lead 効き"], lead), (u"lead 偽の一致", exp[u"lead 偽の一致"], lead), (u"lead 幅", exp[u"lead 幅"], lead),
                              (u"engine 直していない", LEAD_ENGINE_LINE, lead), (u"限界 reason", exp[u"limit reason"], lim), (u"限界 全数", LIMIT_SCOPE_LINE, lim), (u"限界 門", LIMIT_GATE_LINE, lim)):
        if where.count(line) != 1:
            out.append(u"limits: 要点の行が決めた節に 1 回ずつ無い: %s" % name)
    return out


# ======================================================================================================
# f. 封・順序・engine
def frozen_problems(text, commit, rel, root=REPO):
    rc, _ = PR.git_in(root, "cat-file", "-e", commit + "^{commit}")
    if rc != 0:
        return [u"封の commit が履歴に無い"]
    r = subprocess.run(["git", "show", "%s:%s%s" % (commit, PREFIX, rel)], cwd=root, capture_output=True)
    if r.returncode != 0:
        return [u"封の commit に封の file が無い"]
    if r.stdout != text.encode("utf-8"):
        return [u"封が %s のときの byte から変わっている" % commit]
    return []


def seal_frozen_problems(c):
    return frozen_problems(c.seal, SEAL_COMMIT_SHORT, SEAL_REL)


def seal_text_problems(c):
    u"""封に文書が根にする字が在る(予測の境の字)。"""
    out = []
    for need in (u"**1% 以上 8% 以下**", u"**3 倍以上**", u"**1 行以上 30 行以下**", u"**5 割以上**", u"**3 割以上**", u"自己閉じを持つ本は 0", u"## §3 予測", u"後者が 0 なら前者が 3 行以上"):
        if need not in c.seal:
            out.append(u"seal: 封に %s が無い" % need)
    try:
        seal_bounds(c.seal)
    except (AttributeError, ValueError):
        out.append(u"seal: 予測の境が取れない")
    return out


def order_problems_real(root=REPO):
    u"""封 ⊏ script・記録・封の門 ⊑ 結果の文書・この門(未 commit は赤)。"""
    return PR.order_problems(root, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, [SCRIPT_REL, STATES_REL, SEAL_GATE_REL], [DOC_REL, GATE_REL])


def engine_problems(root=REPO):
    u"""engine・lib・入力は封の commit から 0 行(未 commit も)。"""
    return list(SG.engine_since_seal_problems(root)) + list(SG.engine_worktree_problems(root))


# ======================================================================================================
# 変異の表(1 行 = 1 つの検査を赤にする 1 か所の変異。木の file は変異させず、Ctx の写しを変える)
CHECKS = collections.OrderedDict([
    (u"sha", lambda c: sha_problems(c.texts)),
    (u"record", record_problems),
    (u"doc", doc_problems),
    (u"judge", judge_problems),
    (u"limits", limits_problems),
    (u"words", words_problems),
    (u"seal", seal_text_problems),
    (u"frozen", seal_frozen_problems),
])

MUTATIONS = []


def M(label, check, fn):
    MUTATIONS.append((label, check, fn))


def doc_replace(old, new, every=False):
    def fn(c):
        assert old in c.doc, old
        c.doc = c.doc.replace(old, new) if every else c.doc.replace(old, new, 1)
    return fn


def seal_replace(old, new):
    def fn(c):
        assert old in c.seal, old
        c.seal = c.seal.replace(old, new, 1)
    return fn


def doc_append(text):
    return lambda c: setattr(c, "doc", c.doc + text)


def set_text(rel, fn):
    return lambda c: c.texts.__setitem__(rel, fn(c.texts[rel]))


def st_row(i, col, value):
    def fn(c):
        c.st[u"行"][i][col] = value
    return fn


def bump(path, delta=1):
    u"""記録(c.st)の入れ子の dict の数を ``delta`` 変える。path は key の並び。"""
    def fn(c):
        node = c.st
        for k in path[:-1]:
            node = node[k]
        node[path[-1]] += delta
    return fn


def mut_many_rows(n, a, z):
    u"""行のうち state がそのままで ``a``・直した入力で ``z`` でない最初の n 行を (a, z) に書き換える(行の数は変わらない)。"""
    def fn(c):
        k = 0
        for r in c.st[u"行"]:
            if r[3] == r[4] and r[3] == a and k < n:
                r[4] = z
                k += 1
        assert k == n
    return fn


def mut_book_swap(c):
    for b in c.st[K_BOOKS]:
        if b[2] > 0:
            b[4] = 0
            break


# a sha
M(u"a1 states の記録の 1 byte", u"sha", set_text(STATES_REL, lambda t: t + b" "))
M(u"a2 script の 1 byte", u"sha", set_text(SCRIPT_REL, lambda t: t[:-1] + b"#"))
M(u"a3 便 PS の記録の 1 byte", u"sha", set_text(PS_STATES_REL, lambda t: t.replace(b"5588", b"5589", 1)))
# b 記録
M(u"b1 記録の fact の差の数を 1 つ変える(作られた fact)", u"record", bump([K_FACT, u"作られた fact"]))
M(u"b2 記録の行の state を 1 つ変える", u"record", st_row(0, 4, u"VALUE_MISMATCH"))
M(u"b3 記録の判定の差の数を 1 つ変える", u"record", bump([K_JUDGE, u"state は同じで reason だけ変わった行"]))
M(u"b4 記録の予測の欄(NR-3)を 1 つ変える", u"record", bump([K_PRED, u"NR-3 そのままでだけ値が合う行"]))
M(u"b5 記録の棚卸しの数を 1 つ変える", u"record", bump([K_INV, u"folder ごと", u"edinet", u".xbrl の経路"]))
M(u"b6 記録の本ごとの欄の数を 1 つ変える", u"record", lambda c: c.st[K_BOOKS][0].__setitem__(1, c.st[K_BOOKS][0][1] + 1))
M(u"b7 記録の集計の鍵の差を 1 つ変える", u"record", lambda c: c.st[K_KEYS][0].__setitem__(3, c.st[K_KEYS][0][3] + 1))
M(u"b8 記録に文・値の字を足す", u"record", lambda c: c.st.__setitem__(u"漏れ", u"売上高は前期比 12.3 億円の増加となりました。"))
M(u"b9 便 2026-11-09 の経路の数を 1 つ変える", u"record", bump([K_TB, u".htm の経路で自己閉じを持つ本"]))
M(u"b10 便 PS の記録から自己閉じの欄を消す", u"record", lambda c: c.ps[u"サマリーの fact"].pop(K_SELF_PS))
# c 文書の数・表・散文
M(u"c1 表の実測の分子を 1 つ変える(NR-1 の行)", u"doc", doc_replace(u"207/24531(0.8%)", u"208/24531(0.8%)"))
M(u"c2 表の判定の当たりと外れを入れ替える(NR-1)", u"doc", doc_replace(u"| 207/24531(0.8%) | **外れ** |", u"| 207/24531(0.8%) | 当たり |"))
M(u"c3 表の判定の当たりと外れを入れ替える(NR-2)", u"doc", doc_replace(u"| 直した入力でだけ 86 行・そのままでだけ 0 行 | 当たり |", u"| 直した入力でだけ 86 行・そのままでだけ 0 行 | **外れ** |"))
M(u"c4 表の NR-4 の割合を 1 字変える", u"doc", doc_replace(u"| 128/128(100.0%) | 当たり |", u"| 128/128(10.0%) | 当たり |"))
M(u"c5 散文の数を変える(自己閉じを持つ本)", u"doc", doc_replace(u"自己閉じを持つ本 184 本のうち", u"自己閉じを持つ本 185 本のうち"))
M(u"c6 散文に記録に無い数を足す", u"doc", doc_append(u"\n- 追記: 12345 行。\n"))
M(u"c7 散文の率を変える", u"doc", doc_replace(u"自己閉じを持つ本 184 本の 44.0%", u"自己閉じを持つ本 184 本の 45.0%"))
M(u"c8 移り変わりの表の数を 1 つ変える", u"doc", doc_replace(u"| GROUNDED | 6634 | 0 | 0 | 0 |", u"| GROUNDED | 6635 | 0 | 0 | 0 |"))
M(u"c9 state の表の差を変える", u"doc", doc_replace(u"| GROUNDED | 6634 | 6720 | +86 |", u"| GROUNDED | 6634 | 6720 | +85 |"))
M(u"c10 棚卸しの表の数を 1 つ変える", u"doc", doc_replace(u"| `edinet` | 281 | 0 | 0 | 281 |", u"| `edinet` | 280 | 0 | 0 | 281 |"))
M(u"c11 便 PS の数の行を変える", u"doc", doc_replace(u"5588 個・192 本", u"5588 個・191 本"))
M(u"c12 便 2026-11-09 の行の数を変える", u"doc", doc_replace(u"自己閉じを持つ本 0・その本の自己閉じの数の合計 0", u"自己閉じを持つ本 1・その本の自己閉じの数の合計 0"))
M(u"c13 記録から組んだ行を消す(切れない本の行の一部)", u"doc", doc_replace(u"切れない本 28", u"切れない本"))
M(u"c14 禁止語を doc の check にも通す(証明した)", u"doc", doc_append(u"\n証明" + u"した。\n"))
M(u"c15 文書の NR-4 の幅の文を変える", u"doc", doc_replace(u"封の幅(5 割以上)が広すぎた", u"封の幅(5 割以上)が適切だった"))
M(u"c16 散文の数を変える(限界の節の 400 本)", u"doc", doc_replace(u"材料の 400 本を作り直す", u"材料の 401 本を作り直す"))
M(u"c17 散文の数を変える(棚卸しの節の 400 本)", u"doc", doc_replace(u"TSS の 400 本と便", u"TSS の 401 本と便"))
M(u"c18 散文に記録に無い数を足す(限界の節の途中)", u"doc", doc_replace(u"切れない本は測れていない", u"切れない本は測れていない 4321"))
# d 判定
M(u"d1 行を 40 行書き換えて NR-3 を当たりに動かす", u"judge", mut_many_rows(40, u"GROUNDED", u"UNVERIFIABLE"))
M(u"d2 本ごとの欄の期の取り違えを 0 にして NR-4 を外れに動かす", u"judge", lambda c: [b.__setitem__(4, 0) for b in c.st[K_BOOKS]])
M(u"d3 便 2026-11-09 の本に .htm の経路で自己閉じを足して NR-6 を外れに動かす", u"judge", lambda c: c.st[K_TB][K_TB_ROWS][0].__setitem__(2, u".htm の経路") or c.st[K_TB][K_TB_ROWS][0].__setitem__(3, 5))
M(u"d4 行を直した入力側だけ 1000 行書き換えて NR-1 を当たりに動かす", u"judge", mut_many_rows(1000, u"UNVERIFIABLE", u"VALUE_MISMATCH"))
M(u"d5 自己閉じを持つ本を増やして NR-5 を外れに動かす(本ごとの欄の自己閉じを全部 1 以上に)", u"judge", lambda c: [b.__setitem__(1, max(b[1], 1)) for b in c.st[K_BOOKS]])
M(u"d6 判定の欄(NR-1)を 1 つ変える", u"judge", bump([K_PRED, u"NR-1 state が変わった行 / 全部の行", u"分子"]))
# e 語
M(u"e1 禁止語(ハルシネーション)", u"words", doc_append(u"\nハルシ" + u"ネーション\n"))
M(u"e2 会社名らしい字", u"words", doc_append(u"\n株式会社\n"))
M(u"e3 3 桁以上の漢数字", u"words", doc_append(u"\n二百社\n"))
M(u"e4 docID の形", u"words", doc_append(u"\nS100" + u"AB12\n"))
M(u"e5 要点の字を消す(確かめていない)", u"words", doc_replace(u"確かめていない", u"確かめた", True))
M(u"e6 封の commit を言わない", u"words", doc_replace(u"720a473d", u"0000000", True))
M(u"e7 禁止語(人の目)", u"words", doc_append(u"\n人の" + u"目で読んだ。\n"))
M(u"e8 要点の字を消す(偽の一致)", u"words", doc_replace(u"偽の一致", u"ニセの一致", True))
# 要点の文
M(u"l1 負けの節の要点の文を消す(engine は直していない)", u"limits", doc_replace(LEAD_ENGINE_LINE, u"- engine の読み取りは直した。"))
M(u"l2 限界の節の要点の文を消す(全数)", u"limits", doc_replace(LIMIT_SCOPE_LINE, u"- 全数は走らせた。"))
M(u"l3 限界の節の要点の文を消す(門)", u"limits", doc_replace(LIMIT_GATE_LINE, u"- 封の門は全部を縛っている。"))
M(u"l4 負けの節の最初の文を 1 字変える", u"limits", doc_replace(u"**司令塔は欠陥の効きを大きく見すぎていた。**", u"**司令塔は欠陥の効きを見すぎていた。**"))
# f 封
M(u"f1 封の NR-1 の字を替える(根の字)", u"seal", seal_replace(u"**1% 以上 8% 以下**", u"**1% 以上 9% 以下**"))
M(u"f2 封の NR-3 の字を替える", u"seal", seal_replace(u"**1 行以上 30 行以下**", u"**0 行以上 30 行以下**"))
M(u"f3 封の文の途中の 1 字", u"frozen", seal_replace(u"司令塔がこの封を書く前に見た数", u"司令塔がこの封を書く前に見た数字"))
M(u"f4 封の NR-4 の境を替える(判定が動く)", u"judge", seal_replace(u"**5 割以上**", u"**11 割以上**"))


def check_problems(check, c):
    return guard(CHECKS[check], c)


# ======================================================================================================
# 試験
class RealRecordsTest(unittest.TestCase):
    def test_a_1_the_records_and_the_script_equal_the_pinned_sha256(self):
        self.assertEqual([], sha_problems(Ctx().texts))

    def test_a_2_the_pinned_sha256_equal_the_record_headers(self):
        c = Ctx()
        self.assertEqual(SHA_PIN[SCRIPT_REL], c.st[u"この script の sha256"])
        self.assertEqual(SHA_PIN[PS_STATES_REL], hashlib.sha256(read_bytes(PS_STATES_REL)).hexdigest())

    def test_b_1_the_record_equals_the_recount_from_its_rows(self):
        self.assertEqual([], record_problems(Ctx()))

    def test_c_1_the_document_lines_equal_the_lines_rebuilt_from_the_records(self):
        self.assertEqual([], doc_problems(Ctx()))

    def test_c_2_the_rebuilt_lines_are_the_ones_the_brief_names(self):
        c = Ctx()
        exp = dict(expected_lines(c))
        self.assertIn(u"207/24531(0.8%)", exp[u"table NR-1"])
        self.assertIn(u"直した入力でだけ 86 行・そのままでだけ 0 行", exp[u"table NR-2"])
        self.assertIn(u"| 0 行 |", exp[u"table NR-3"])
        self.assertIn(u"128/128(100.0%)", exp[u"table NR-4"])
        self.assertIn(u"81/184(44.0%)", exp[u"table NR-5"])
        self.assertIn(u"0/17(0.0%)", exp[u"table NR-6"])
        self.assertIn(u"9166 個・184 本", exp[u"ps この便"])
        self.assertIn(u"5588 個・192 本", exp[u"ps 数"])
        self.assertIn(u"5323", exp[u"fact engine"])
        self.assertIn(u"| POINTER_NOT_FOUND | 81 | 10 | 65 | 11008 |", exp[u"trans POINTER_NOT_FOUND"])

    def test_d_1_the_judgement_is_redone_from_the_seal_text_and_the_records(self):
        self.assertEqual([], judge_problems(Ctx()))

    def test_d_2_the_real_judgement_is_two_misses_and_four_hits(self):
        c = Ctx()
        self.assertEqual([i for i, v in zip(NR_IDS, verdicts(c)) if v == MISS], [u"NR-1", u"NR-3"])
        self.assertEqual([i for i, v in zip(NR_IDS, verdicts(c)) if v == HIT], [u"NR-2", u"NR-4", u"NR-5", u"NR-6"])

    def test_d_3_the_bounds_are_read_from_the_seal_text(self):
        self.assertEqual(seal_bounds(Ctx().seal), {u"NR-1": (1, 8), u"NR-2": (3, 3), u"NR-3": (1, 30), u"NR-4": 5, u"NR-5": 3, u"NR-6": 0})

    def test_e_1_the_words_are_clean(self):
        self.assertEqual([], words_problems(Ctx()))

    def test_e_2_the_seal_has_the_texts_the_document_roots_on(self):
        self.assertEqual([], seal_text_problems(Ctx()))

    def test_e_3_the_lead_and_the_limits_have_their_lines(self):
        self.assertEqual([], limits_problems(Ctx()))

    def test_f_1_the_seal_is_the_text_of_the_sealed_commit(self):
        self.assertEqual([], seal_frozen_problems(Ctx()))

    def test_f_2_the_real_history_has_the_seal_before_the_script_the_record_the_document_and_this_gate(self):
        u"""文書・この門のどれかが未 commit なら赤(足した commit が無い。skip にしない)。全部 commit された後で初めて緑。"""
        self.assertEqual([], order_problems_real())

    def test_f_3_the_real_order_failure_before_the_commit_is_only_the_uncommitted_files(self):
        got = order_problems_real()
        self.assertTrue(all(p.startswith(u"UNCOMMITTED:") for p in got), got)

    def test_f_4_the_order_check_names_exist(self):
        for rel in (SCRIPT_REL, STATES_REL, SEAL_GATE_REL, DOC_REL, GATE_REL, PS_STATES_REL):
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)

    def test_f_5_engine_lib_inputs_are_untouched(self):
        self.assertEqual([], engine_problems())


class OrderGateTest(unittest.TestCase):
    u"""順序の検査自体が、悪い順を赤にできること(使い捨ての git で)。"""

    def test_o_1_good_and_bad_orders(self):
        r = PR.Repo()
        r.put("docs/seal.md")
        s = r.commit("docs/seal.md")
        r.put("measure/s.py")
        r.put("fixtures/a.json")
        r.commit("measure/s.py", "fixtures/a.json")
        others = ["docs/r.md", "tests/g.py"]
        for o in others:
            r.put(o)
        self.assertEqual([u"UNCOMMITTED:" + o for o in others], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], ["measure/s.py", "fixtures/a.json"], others))
        r.commit(*others)
        self.assertEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], ["measure/s.py", "fixtures/a.json"], others))
        r2 = PR.Repo()
        r2.put("docs/seal.md")
        s2 = r2.commit("docs/seal.md")
        r2.put("docs/r.md")
        r2.commit("docs/r.md")
        r2.put("measure/s.py")
        r2.commit("measure/s.py")
        self.assertNotEqual([], PR.order_problems(r2.d, PREFIX, "docs/seal.md", s2[:7], ["measure/s.py"], ["docs/r.md"]))      # 文書が script より前


class MutationTest(unittest.TestCase):
    def test_m_1_every_check_is_green_on_the_real_records(self):
        c = Ctx()
        for name in CHECKS:
            self.assertEqual([], check_problems(name, c), name)

    def test_m_2_every_mutation_turns_its_check_red(self):
        silent, crashed = [], []
        for label, check, fn in MUTATIONS:
            c = Ctx()                                     # 毎回新しい写し(変異は 1 か所だけ)
            fn(c)
            got = check_problems(check, c)
            if not got:
                silent.append(label)
            elif got[0].startswith(u"例外"):
                crashed.append(label)
        self.assertEqual([], silent, u"赤にならなかった変異: %s" % silent)
        self.assertEqual([], crashed, u"検査が例外で落ちて赤になった変異: %s" % crashed)

    def test_m_3_each_mutation_gets_a_new_copy_and_leaves_the_real_files_alone(self):
        rels = (STATES_REL, SCRIPT_REL, PS_STATES_REL, SEAL_REL, DOC_REL)
        before = dict((rel, hashlib.sha256(read_bytes(rel)).hexdigest()) for rel in rels)
        c = Ctx()
        c.st[u"行"][0][4] = u"x"
        c.doc = u"x"
        self.assertNotEqual(u"x", Ctx().st[u"行"][0][4])
        self.assertNotEqual(u"x", Ctx().doc)
        self.assertEqual(before, dict((rel, hashlib.sha256(read_bytes(rel)).hexdigest()) for rel in rels))

    def test_m_4_the_mutation_table_covers_every_check_and_every_effect_named_in_the_brief(self):
        self.assertEqual(set(CHECKS), set(ch for _l, ch, _f in MUTATIONS))
        labels = u"\n".join(l for l, _c, _f in MUTATIONS)
        for need in (u"states の記録の 1 byte", u"script の 1 byte", u"表の実測の分子", u"当たりと外れを入れ替える", u"散文の数", u"散文に記録に無い数", u"禁止語", u"漢数字",
                     u"要点の文", u"封の文の途中の 1 字", u"NR-3 を当たりに動かす", u"NR-4 を外れに動かす", u"NR-6 を外れに動かす", u"記録の行の state"):
            self.assertIn(need, labels)

    def test_m_5_a_hit_turned_to_a_miss_is_caught_by_the_judge_and_not_only_by_the_table(self):
        c = Ctx()
        for b in c.st[K_BOOKS]:
            b[4] = 0                                       # NR-4 が外れに動く。文書の表は当たりのまま
        jd = dict(nr_judge(c))
        self.assertFalse(jd[u"NR-4"])
        self.assertNotEqual([], judge_problems(c))

    def test_m_6_the_judge_follows_the_seal_bounds_not_a_pinned_number(self):
        c = Ctx()
        c.seal = c.seal.replace(u"**1% 以上 8% 以下**", u"**0% 以上 8% 以下**", 1)
        self.assertTrue(dict(nr_judge(c))[u"NR-1"])
        c2 = Ctx()
        c2.seal = c2.seal.replace(u"**1 行以上 30 行以下**", u"**0 行以上 30 行以下**", 1)
        self.assertTrue(dict(nr_judge(c2))[u"NR-3"])


class WiringTest(unittest.TestCase):
    def test_n_1_this_gate_carries_no_docid_and_no_key(self):
        src = read(GATE_REL)
        for bad in (u"ANTHRO" + u"PIC", u"API_" + u"KEY", u"url" + u"lib", u"sock" + u"et"):
            self.assertNotIn(bad, src)

    def test_n_2_this_gate_does_not_widen_the_boundary_import_list(self):
        self.assertEqual([], SG.boundary_problems())


if __name__ == "__main__":
    unittest.main()
