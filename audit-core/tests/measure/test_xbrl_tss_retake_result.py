# -*- coding: utf-8 -*-
"""結果の門: 封 docs/XBRL_TSS_RETAKE_SEAL_2026-11-18.md(b4c08fc6)の結果の文書 docs/XBRL_TSS_RETAKE_RESULT_2026-11-18.md。

封の門 ``test_xbrl_tss_retake_seal.py`` の次の段。**追跡されている記録・script・封・結果の文書と git の履歴だけを読む**(材料は読まない。全数の作り直しは走らせない)。

縛るもの(検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表で 1 本ずつ。木の file は変異させず、``Ctx`` の写しに当てる)
 a script・記録・封の門の sha256(字で留める)
 b 記録の中の整合: 封の門の ``record_problems``(前の記録からの数え直し・行の一覧・文や値の漏れ)+ 最上位の欄の一覧
 c 結果の文書の数: 表の行も散文の行も、記録から組んだ 1 行と字で同じ(1 行ずつ。文書の行が 1 回ずつ在る)。そのどれにも当たらない行の 2 桁以上の数は、組んだ行の数の集合に在るものだけ
 d 予測 RT-1〜RT-6 の判定を、封の予測の字から取った境と記録の段の欄から門が自分で決め直して、文書の表と同じ・字で留めた判定と同じ。RT-7 は文書に当たり外れの字が無いことだけを縛る
 e 文書に禁止語・会社名らしい字・docID・3 桁以上の漢数字が無い・要点の字が在る
 f 封が commit から 1 字も変わっていない・順序(commit の順。未 commit は赤)・engine は封の commit から 0 行
この file は docID の字を持たない。
"""
import collections
import fractions
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


SG = load_module("tests/measure/test_xbrl_tss_retake_seal.py", "tss_retake_seal_gate_for_rt_result_gate")      # 封の門の部品。門としては走らせない
PR = SG.PR

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
RECORD_COMMIT_SHORT = "a581a17e"                              # script・記録・封の門の commit(履歴から探した値と照らす)
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
RECORD_REL = SG.RECORD_REL
GATE_REL = "tests/measure/test_xbrl_tss_retake_result.py"
DOC_REL = "docs/XBRL_TSS_RETAKE_RESULT_2026-11-18.md"

SHA_PIN = collections.OrderedDict([
    (RECORD_REL, "34845f1b3772993aebc0a48d1cec0f6ee5889f9f66843a88f94e572392263cd7"),
    (SCRIPT_REL, "4d1c4276f67f2fd5551ba0372b2a09c07a2ee4c493b09942e3f360ee35e5b82e"),
    (SEAL_GATE_REL, "525570819a21d8e7f8bfa1520b3dc7d77187f943d3522f69f6735befdeb497f7")])

STATES = SG.STATES
G, VM, UN, PN = STATES
K1, K2, K3, K4, K5 = SG.K_STAGES
K_RT1, K_PRED = SG.K_RT1, SG.K_PRED
K_TRANS = u"両方に在る行の state の移り変わり(前 → 後)"
K_TRANS4 = u"両方に在る行の結果の語の移り変わり(前 → 後)"
K_CELLS = u"升ごとの「名指して原本の値を返した」"
K_RT6 = u"RT-6 AI の席が読んだ行のうち前提が変わった行"
K_PS_NOW = u"サマリーの fact(後)"
K_PS_WAS = u"サマリーの fact(前)"
K_PS_AGG_WAS = u"集計(前。便 PS の記録の集計の欄)"
K_PS_AGG_NOW = u"集計(後)"
K_PS_FLAG_CHG = u"読みごとの札が変わった行"
K_PS_EMPTY = u"空の欄を除く読み(封の後・監査の数え直しを見た後に足した読み(封 §8。あと知恵))"
PRED_IDS = (u"RT-1", u"RT-2a", u"RT-2b", u"RT-3a", u"RT-3b", u"RT-4a", u"RT-4b", u"RT-4c", u"RT-5a", u"RT-5b", u"RT-6")
ALL_IDS = PRED_IDS + (u"RT-7",)
HIT, MISS, NOJ = u"当たり", u"**外れ**", u"判定しない"
VERDICT_PINNED = (HIT, HIT, HIT, HIT, HIT, HIT, HIT, MISS, HIT, HIT, HIT)
WORDS = (u"通した", u"名指して原本の値を返した", u"名指したが別の値", u"止めたが名指さない(POINTER_NOT_FOUND)", u"止めたが名指さない(UNVERIFIABLE)", u"対応が付かない")
READINGS = (u"字のとおりの読み(主)", u"円の族の読み", u"字のとおり × 空の欄を除く読み", u"円の族 × 空の欄を除く読み")
CELL_KEYS = ((u"A", u"T1_VALUE"), (u"A", u"T5_COINCIDENT"), (u"A", u"T8_REL"), (u"丙", u"T1_VALUE"), (u"丙", u"T5_COINCIDENT"), (u"丙", u"T8_REL"))

FORBIDDEN_WORDS = (u"証明" + u"した", u"ハルシ" + u"ネーション", u"精" + u"度", u"世界で 1 " + u"社")
COMPANY_WORDS = (u"株式会社", u"有限会社", u"合同会社", u"㈱", u"(株)")
DOCID_RE = re.compile(r"S100[0-9A-Z]{4}")
POINTER_RE = re.compile(r"xbrl:|jppfs|jpcrp|jpdei|_cor:|@(Current|Prior)|formula:")
KANJI_NUM_RE = re.compile(u"[二三四五六七八九]百|[一二三四五六七八九]千|百[一二三四五六七八九十]|千[一二三四五六七八九百]")
HUMAN_EYE_RE = re.compile(u"人の" + u"目")
REQUIRED_PHRASES = (u"先に負けと限界を書く", u"外れ", u"当たり", u"追跡する記録に無い", u"監査の席が数えた(記録なし)", u"人間の決定", u"限界", u"engine は 0 行",
                    u"恒等に近い", u"付け直していない", u"弱い", u"REVISE", u"判定しない", u"引き継ぎに書く", u"行と行の比べになっていない")


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


def points(n1, d1, n2, d2):
    u"""(n2/d2 − n1/d1) × 100 の厳密な値(Fraction)。"""
    return fractions.Fraction(n2 * 100, d2) - fractions.Fraction(n1 * 100, d1)


def point_text(x):
    u"""小数 2 桁の字(0 から遠い側へ丸める。script の ``point_diff`` と同じ決め方を門の側で独立に書く)。"""
    k = int(abs(x) * 100 + fractions.Fraction(1, 2))
    return u"%s%d.%02d" % (u"-" if x < 0 and k else u"", k // 100, k % 100)


def record_commit_full(root=REPO):
    c = PR.added_commits(root, PREFIX + RECORD_REL)
    return c[0] if len(c) == 1 else None


class Ctx(object):
    u"""記録・封・文書・字の写し。変異は毎回 ``Ctx()`` の新しい写しに 1 か所だけ加える。"""

    def __init__(self):
        self.rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        self.seal = read(SEAL_REL)
        self.doc = read(DOC_REL)
        self.texts = collections.OrderedDict((rel, read_bytes(rel)) for rel in SHA_PIN)


# ======================================================================================================
# 記録の読み出し(門の側で独立に)
def st(c, k):
    return c.rec[k]


def trans_table(s):
    u"""{(前, 後): 行数}(state)。"""
    t = s[K_TRANS]
    return dict(((a, b), t[u"%s → %s" % (a, b)]) for a in STATES for b in STATES)


def trans_table4(s):
    t = s[K_TRANS4]
    return dict(((a, b), t[u"%s → %s" % (a, b)]) for a in WORDS for b in WORDS)


def cells_of(s4):
    return dict(((x[u"群"], x[u"型"]), x) for x in s4[K_CELLS])


def cell_shift(x):
    return points(x[u"前の分子"], x[u"前の分母"], x[u"後の分子"], x[u"後の分母"])


def pass_flow(s4):
    u"""id の鍵の上の「通した」の動き: (前も後も通した, 前は通して後は通さない, 前は通さず後は通した)。"""
    t = trans_table4(s4)
    w = WORDS[0]
    stay = t[(w, w)]
    out = sum(v for (a, b), v in t.items() if a == w and b != w)
    inn = sum(v for (a, b), v in t.items() if b == w and a != w)
    return stay, out, inn


def ps_read(agg, i):
    u"""集計の ``i`` 番目の読みの P の欄(全体)。"""
    key = list(agg)[i]
    return agg[key][u"全体"][u"P"]


# ======================================================================================================
# a. sha256
def sha_problems(texts, pin=None):
    pin = SHA_PIN if pin is None else pin
    return [u"sha256: %s が字で留めた値と違う" % rel for rel, want in pin.items() if hashlib.sha256(texts.get(rel, b"")).hexdigest() != want]


TOP_KEYS = (u"seal", u"封の commit", u"step", u"この script の sha256", u"入力", u"engine の指紋(今。便 NRE の記録の直した後と同じ)", u"engine の指紋(直す前。TSS の記録のもの)", u"profile",
            u"材料", u"段の順", K_RT1, K1, K2, K3, K4, K5, K_PRED, u"読み替えた所", u"限界", u"時間(秒)", u"key_leaks")


# ======================================================================================================
# b. 記録の中の整合(封の門の部品)
def record_problems(c):
    out = list(SG.record_problems(text=json.dumps(c.rec, ensure_ascii=False)))
    if tuple(c.rec) != TOP_KEYS:
        out.append(u"記録の最上位の欄が決めた一覧と違う(文・値などの足された欄の疑い)")
    return out


# ======================================================================================================
# d. 予測の判定(封の予測の字から境を取り、記録の段の欄から決め直す)
def seal_row(seal, pid):
    sec = seal[seal.index(u"## 3. 予測"):] if u"## 3. 予測" in seal else u""
    m = re.search(r"^\| %s \| (.*?) \| (.*?) \|$" % re.escape(pid), sec, re.M)
    return m.group(1) if m else u""


def to_int(s):
    return int(s.replace(u",", u""))


def seal_bounds(seal):
    u"""封の予測の字(太字の境)から数を取る。取れなければ例外(= 検査が赤)。"""
    r = lambda pid: seal_row(seal, pid)
    b = {}
    b[u"RT-1"] = int(re.search(r"違う行 (\d+)\)", r(u"RT-1")).group(1))
    m = re.search(r"([\d,]+) 行のうち \*\*(\d+) 行以上 (\d+) 行以下\*\*", r(u"RT-2a"))
    b[u"RT-2a"] = (to_int(m.group(1)), int(m.group(2)), int(m.group(3)))
    b[u"RT-2b"] = int(re.search(r"\*\*(\d+)\*\*", r(u"RT-2b")).group(1))
    m = re.search(r"\*\*(\d+) 以上 (\d+) 以下\*\*", r(u"RT-3a"))
    b[u"RT-3a"] = (int(m.group(1)), int(m.group(2)))
    m = re.search(r"前の近い行 (\d+) のうち.*?\*\*(\d+) 行以上\*\*", r(u"RT-3b"))
    b[u"RT-3b"] = (int(m.group(1)), int(m.group(2)))
    m = re.search(r"\*\*([\d,]+) 以上 ([\d,]+) 以下\*\*", r(u"RT-4a"))
    b[u"RT-4a"] = (to_int(m.group(1)), to_int(m.group(2)))
    m = re.search(r"\*\*(\d+) 以上 (\d+) 以下\*\*.*?\*\*(\d+) 以上 (\d+) 以下\*\*", r(u"RT-4b"))
    b[u"RT-4b"] = tuple(int(m.group(i)) for i in (1, 2, 3, 4))
    m = re.search(r"\*\*どれも ([\d.]+) ポイント未満\*\*", r(u"RT-4c"))
    b[u"RT-4c"] = fractions.Fraction(m.group(1))
    m = re.search(r"\*\*(\d+) 以上 (\d+) 以下\*\*", r(u"RT-5a"))
    b[u"RT-5a"] = (int(m.group(1)), int(m.group(2)))
    b[u"RT-5b"] = int(re.search(r"違う行は \*\*(\d+)\*\*", r(u"RT-5b")).group(1))
    m = re.search(r"\*\*(\d+) 行以下\*\*.*?\*\*(\d+) 行以下\*\*.*?\*\*(\d+) 行以下\*\*.*?\*\*(\d+)% 以下\*\*", r(u"RT-6"))
    b[u"RT-6"] = tuple(int(m.group(i)) for i in (1, 2, 3, 4))
    return b


def judge(c):
    u"""[(id, 当たり?)](RT-1〜RT-6。11 本)。封の字の境と、記録の段の欄から決める。"""
    b = seal_bounds(c.seal)
    rt1, s1, s2, s3, s4, s5 = c.rec[K_RT1], st(c, K1), st(c, K2), st(c, K3), st(c, K4), st(c, K5)
    out = []
    out.append((u"RT-1", rt1[u"state が違う行"][u"分子"] == b[u"RT-1"] and rt1[u"便 NRE の記録にだけ在る行"] == 0 and rt1[u"取り直しにだけ在る行"] == 0
                and rt1[u"両方に在る行"] == rt1[u"行(便 NRE の記録)"] == s1[u"行(前)"]))
    n2 = len(s2[u"変わった行"])
    d2, lo2, hi2 = b[u"RT-2a"]
    out.append((u"RT-2a", s2[u"行(前)"] == d2 and lo2 <= n2 <= hi2))
    lost = sum(1 for x in s2[u"変わった行"] if x[3] == G and x[4] != G) + sum(1 for x in s2[u"消えた行"] if x[3] == G)
    out.append((u"RT-2b", lost == b[u"RT-2b"]))
    lo3, hi3 = b[u"RT-3a"]
    out.append((u"RT-3a", lo3 <= s3[u"近い行(後)"] <= hi3))
    d3, lo3b = b[u"RT-3b"]
    out.append((u"RT-3b", s3[u"近い行(前)"] == d3 and s3[u"前の近い行のうち後も近い行"] >= lo3b))
    lo4, hi4 = b[u"RT-4a"]
    out.append((u"RT-4a", lo4 <= s4[u"注入の行(後)"] <= hi4))
    a1, a2, p1, p2 = b[u"RT-4b"]
    out.append((u"RT-4b", a1 <= s4[u"通した行(後)"][u"通した行の合計"] <= a2 and p1 <= s4[u"通した行(後)"][u"うち丙の期の入れ替えの型"] <= p2))
    cells = cells_of(s4)
    out.append((u"RT-4c", all(abs(cell_shift(cells[k])) < b[u"RT-4c"] for k in CELL_KEYS)))
    lo5, hi5 = b[u"RT-5a"]
    out.append((u"RT-5a", lo5 <= s5[u"P の行(後)"] <= hi5))
    out.append((u"RT-5b", s5[u"両方に在る P の行のうち後の字のとおりの読みの自・実・他が前の字のとおり × 空の欄を除く読みの自・実・他と違う行"] == b[u"RT-5b"]))
    r6 = c.rec[K_PRED][K_RT6]
    k1, k3, k4, kp = b[u"RT-6"]
    v1, v3, v4, v5 = [r6[k][u"分子"] for k in (u"第 1 便の標本(state が「値が違う」でなくなった行)", u"近い行の読み(近い行でなくなった行)", u"通した行の札(通した行でなくなった行)", u"便 PS の読みの行(P か W でなくなった行)")]
    d5 = r6[u"便 PS の読みの行(P か W でなくなった行)"][u"分母"]
    out.append((u"RT-6", v1 <= k1 and v3 <= k3 and v4 <= k4 and v5 * 100 <= kp * d5))
    return out


def verdicts(c):
    return tuple(HIT if ok else MISS for _i, ok in judge(c))


def judge_problems(c):
    out = []
    got = verdicts(c)
    if got != VERDICT_PINNED:
        out.append(u"judge: 決め直した判定が字で留めた判定と違う: %s" % (u" ".join(got),))
    pr = c.rec[K_PRED]
    s1, s2, s3, s4, s5 = [st(c, k) for k in (K1, K2, K3, K4, K5)]
    if pr.get(u"RT-2a 段 2 で state が変わった行 / 両方に在る行") != collections.OrderedDict(
            [(u"分子", len(s2[u"変わった行"])), (u"分母", s2[u"両方に在る行"]), (u"率", rate_text(len(s2[u"変わった行"]), s2[u"両方に在る行"]))]):
        out.append(u"judge: RT-2a の欄が数え直しと違う")
    if pr.get(u"RT-3a 段 3 の近い行の数(後)") != s3[u"近い行(後)"]:
        out.append(u"judge: RT-3a の欄が段 3 と違う")
    if pr.get(u"RT-4a 段 4 の注入の行の数(後)") != s4[u"注入の行(後)"]:
        out.append(u"judge: RT-4a の欄が段 4 と違う")
    if pr.get(u"RT-5a 段 5 の P の行の数(後)") != s5[u"P の行(後)"]:
        out.append(u"judge: RT-5a の欄が段 5 と違う")
    cells = cells_of(s4)
    want4c = collections.OrderedDict((u"%s × %s" % k, point_text(cell_shift(cells[k]))) for k in CELL_KEYS)
    if pr.get(u"RT-4c 群 × 型の 6 つの升の「名指して原本の値を返した」の率の差(ポイント。後 − 前)") != want4c:
        out.append(u"judge: RT-4c の升の差が分子・分母からの数え直しと違う")
    stay, left, came = pass_flow(s4)
    if stay + left != s4[u"通した行(前)"][u"通した行の合計"] or stay + came != s4[u"通した行(後)"][u"通した行の合計"]:
        out.append(u"judge: 通した行の動き(id の鍵の上)が前・後の合計と合わない")
    if sum(v for (a, b), v in trans_table4(s4).items() if a != b) != s4[u"結果の語が変わった行"][u"分子"]:
        out.append(u"judge: 結果の語が変わった行が移り変わりの表の対角でない升の和と違う")
    by_pair = collections.Counter((x[3], x[4]) for x in s4[u"変わった行"])
    if any(by_pair.get((a, b), 0) != v for (a, b), v in trans_table4(s4).items() if a != b) or len(s4[u"変わった行"]) != s4[u"結果の語が変わった行"][u"分子"]:
        out.append(u"judge: 移り変わりの表の対角でない升が変わった行の一覧の数え直しと違う")
    if ps_read(s5[K_PS_AGG_NOW], 0) != ps_read(s5[K_PS_AGG_NOW], 2) or ps_read(s5[K_PS_AGG_NOW], 1) != ps_read(s5[K_PS_AGG_NOW], 3):
        out.append(u"judge: 後の字のとおりの読みが後の空の欄を除く読みと同じでない(文書の「同じ」に反する)")
    if s5[u"どれかの欄が変わった行"] != len(s5[u"変わった行"]):
        out.append(u"judge: 段 5 の変わった行の数が一覧と違う")
    return out


# ======================================================================================================
# c. 結果の文書の行(記録から組む)
RT7_MEAS = u"この便の commit の前に司令塔が全数を 1 回走らせる。結果はこの文書に書かない(引き継ぎに書く)"

FIXED = collections.OrderedDict([
    (u"title", u"# 結果: 便 RT ― TSS の系列(第 1 便・第 2 便・便 1b・便 PS)を、直した engine で取り直して前の記録と並べた ― 2026-11-18"),
    (u"lead head", u"**先に負けと限界を書く。**"),
    (u"lead 読み", u"- AI の席の読みは付け直していない。取り直しで新しく「値が違う」「近い」「通した」「P」になった行は誰も読んでいない。"),
    (u"lead 取り直し", u"- 新しい測定ではなく取り直し(前の 4 便の script の関数を、直した engine で同じ材料に当てた)。engine は 0 行で、この便に採用の判定は無い。"),
    (u"h1", u"## §1 予測の当たり外れ(司令塔。盲検ではない)"),
    (u"pred head", u"封 §3 の字の境と記録の段の欄から、結果の門が RT-1〜RT-6 の当たり外れを決め直した(この表と同じ)。RT-7 は記録に無く、この文書は当たり外れを書かない。"
                   u"封も予測も、結果を見てから書き換えていない。"),
    (u"table head", u"| # | 予測(封の字) | 実測(記録の分子・分母) | 判定 |"),
    (u"pred rt1", u"- RT-1 は恒等に近い配線の確かめ(便 NRE の記録と同じ engine・同じ入力を通した行の比べ)。当たっても見立ての強さにはしない。"),
    (u"pred rt7", u"- RT-7: この便の commit の前に司令塔が全数を 1 回走らせる。結果はこの文書に書かない(引き継ぎに書く)。"),
    (u"h2", u"## §2 段ごとの前と後の数(記録の集計と移り変わりの表から)"),
    (u"s2 head", u"前 = 前の便の記録の欄をそのまま読んだ数・後 = 直した engine での取り直し。突き合わせの鍵は段ごとに本の # と文の番号と位置(注入は本の # と行の id)。"
                 u"片方にしか無い行は「消えた行」「増えた行」として別に数えた(0 と決めつけていない)。"),
    (u"h s1", u"### 段 1(第 1 便の判定。便 NRE の記録と同じ段)"),
    (u"h s2", u"### 段 2(第 2 便(一)。中間の期の名前を写した判定)"),
    (u"h s3", u"### 段 3(第 2 便(二)。近い行)"),
    (u"h s4", u"### 段 4(便 1b。注入)"),
    (u"h s5", u"### 段 5(便 PS。サマリーの当てる先)"),
    (u"s4 鍵", u"- 注入の行は文の番号・位置を持たないので、前後の突き合わせの鍵は (本の #, 行の id)。同じ id が前と後で別の注入を指していても、鍵の上では同じ行として並ぶ(次の §3)。"),
    (u"h3", u"## §3 注入の行の鍵(独立監査の所見)"),
    (u"key 比べ", u"- 結果の語が変わった行は、**同じ注入の前後の比べではない**。鍵が同じでも注入の中身(型・形・単位・基準の claim)が前後で違う行が在るので、行と行の比べになっていない。"),
    (u"key 升", u"- 升の集計(RT-4a〜RT-4c)は行の鍵に依らない(前と後でそれぞれ数えた升ごとの件数の比べ)。"),
    (u"key 記録なし", u"- 結果の語が変わった行のうち、型・形・単位・基準の claim が前後で同じ行の数は、監査の席が数えた(記録なし)。この文書には書かない。"),
    (u"h4", u"## §4 読んだ行の前提(RT-6 の 4 つ)"),
    (u"p head", u"| 読んだ行の集まり | 前提が変わった行(記録の分子・分母) | 封の幅 |"),
    (u"p note", u"- 前提が変わった行は、AI の席の読みが取り直した数の上でそのまま使えない行。付け直した読みではなく、前の読みの行が今も同じ前提(state・近い行・通した行・P か W)に在るかを数えただけ。"
                u"通した行の札は 1 行で率が 10.0% でも、封の字は行数(2 行以下)なので幅の中。"),
    (u"h5", u"## §5 読み替えた所(記録の欄を写す)"),
    (u"h6", u"## §6 読める事(控えめに)"),
    (u"read 範囲", u"- 読めるのは TSS の 400 本・この 5 段に限る。上場会社全体の率ではない。数の向きは段ごとに並べるだけにして、「変わらなかった」とは丸めない(RT-4c の升は動いた・段 5 の字のとおりの読みの率は大きく動いた)。"),
    (u"h7", u"## §7 限界"),
    (u"lim 1", u"- 標本は英文短信を出している会社の 400 本。上場会社全体の率ではない(前の 4 便と同じ)。"),
    (u"lim 2", u"- AI の席の読み(型・札・2 軸)は付け直していない。取り直しで新しく「値が違う」「近い」「通した」「P」になった行は誰も読んでいない(封 §6 の 2)。"),
    (u"lim 3", u"- 丙は期の名前を `measure/` の側で写した読みの上の数で、engine の読みそのものではない(第 2 便と同じ)。"),
    (u"lim 4", u"- 便 KAM・便 YS・英文短信の側・2026-11-09 の短信の便は取り直していない(前の 2 つと 2026-11-09 の便は `.xbrl` の経路。英文短信の側は別のセッション)。"),
    (u"lim 5", u"- 便 AT(型の読みの数え直し)は取り直していない(型を付け直さないので数は変わらない。ただし土台の state は一部変わる。RT-6 の数で大きさだけ分かる)。"),
    (u"lim 6", u"- 空白入りの自己閉じの形は直した式でも始まりと読む(便 NRE の限界のまま)。"),
    (u"lim 鍵", u"- 注入の前後の突き合わせは行の id の鍵で、同じ id が前後で同じ注入を指さない行が在る。結果の語が変わった行の数は、行と行の比べでない数として読む(§3)。"),
    (u"lim 読み", u"- 取り直した数の上で、AI の席の読みを付け直していない(上の 2)。新しい読みは作っていない。"),
    (u"lim 門", u"- 封の門と結果の門は、作り物の例が無くて黙る変異がいくつか残る(2 回目の監査の所見。数は追跡する記録に無いので書かない)。"),
    (u"lim 監査", u"- 独立監査は、script・記録・封の門について、1 回目が門の配線の変異で REVISE、門を強化して 2 回目が GO。"),
    (u"lim 判定", u"- 予測の当たり外れの判定は司令塔(盲検でない)。RT-7 は判定しない。"),
    (u"lim 縛り", u"- 記録の欄のうち一覧の行から数え直せないもの(fact の数の合計・母集団・reason だけ変わった行の数・結果の語の移り変わりの対角など)は、記録の sha256 の字留めでだけ縛られる。"),
    (u"lim 出力", u"- 取り直した出力そのもの(大きい)は repo に置かない。置いたのは 1 つの記録(段ごとの集計・移り変わりの表・変わった行の一覧)だけで、記録は行の番号と記号だけを持ち、文・値・要素名・会社名・docID を持たない。"),
    (u"h8", u"## §8 次(人間の決定)"),
    (u"next 1", u"- 取り直した数を外の紙に書くか(人間の決定)。"),
    (u"next 2", u"- 取り直した state の上で AI の席の読みを付け直すか(付け直すなら別の封。人間の決定)。"),
    (u"next 3", u"- `main` へのマージ(人間の決定)。"),
])


def meas_texts(c):
    u"""予測の表の「実測」の欄(RT-1〜RT-7)。"""
    rt1, s1, s2, s3, s4, s5 = c.rec[K_RT1], st(c, K1), st(c, K2), st(c, K3), st(c, K4), st(c, K5)
    r6 = c.rec[K_PRED][K_RT6]
    cells = cells_of(s4)
    n2, d2 = len(s2[u"変わった行"]), s2[u"両方に在る行"]
    lost = sum(1 for x in s2[u"変わった行"] if x[3] == G and x[4] != G)
    gone = sum(1 for x in s2[u"消えた行"] if x[3] == G)
    big = [u"%s × %s" % k for k in CELL_KEYS if abs(cell_shift(cells[k])) >= seal_bounds(c.seal)[u"RT-4c"]]
    shifts = u"・".join(u"%s × %s %s" % (k[0], k[1], point_text(cell_shift(cells[k]))) for k in CELL_KEYS)
    r6k = (u"第 1 便の標本(state が「値が違う」でなくなった行)", u"近い行の読み(近い行でなくなった行)", u"通した行の札(通した行でなくなった行)", u"便 PS の読みの行(P か W でなくなった行)")
    names = (u"第 1 便の標本", u"近い行の読み", u"通した行の札", u"便 PS の読み")
    m = collections.OrderedDict()
    m[u"RT-1"] = u"段 1 の行の state が便 NRE の記録と違う行 %s・片方にだけ在る行 %d" % (frac(rt1[u"state が違う行"][u"分子"], rt1[u"state が違う行"][u"分母"]),
                                                                   rt1[u"便 NRE の記録にだけ在る行"] + rt1[u"取り直しにだけ在る行"])
    m[u"RT-2a"] = u"段 2 で state が変わった行 %s(%d 本)" % (frac(n2, d2), s2[u"state が変わった行を持つ本"])
    m[u"RT-2b"] = u"前は GROUNDED で後は GROUNDED でない行 %d・前は GROUNDED で消えた行 %d" % (lost, gone)
    m[u"RT-3a"] = u"段 3 の近い行(後)%d" % s3[u"近い行(後)"]
    m[u"RT-3b"] = u"前の近い行 %d のうち後も近い行 %s" % (s3[u"近い行(前)"], frac(s3[u"前の近い行のうち後も近い行"], s3[u"近い行(前)"]))
    m[u"RT-4a"] = u"段 4 の注入の行(後)%d" % s4[u"注入の行(後)"]
    m[u"RT-4b"] = u"通した行の合計は前 %d・後 %d・うち丙の期の入れ替えの型は前 %d・後 %d" % (
        s4[u"通した行(前)"][u"通した行の合計"], s4[u"通した行(後)"][u"通した行の合計"], s4[u"通した行(前)"][u"うち丙の期の入れ替えの型"], s4[u"通した行(後)"][u"うち丙の期の入れ替えの型"])
    m[u"RT-4c"] = u"6 つの升の動き(ポイント。後 − 前): %s。封の幅を超えた升 %d(%s)" % (shifts, len(big), u"・".join(big))
    m[u"RT-5a"] = u"段 5 の P の行(後)%d(前 %d)" % (s5[u"P の行(後)"], s5[u"P の行(前)"])
    pb = s5[u"両方に在る P の行のうち後の字のとおりの読みの自・実・他が前の字のとおり × 空の欄を除く読みの自・実・他と違う行"]
    m[u"RT-5b"] = u"前の字のとおり × 空の欄を除く読みの旗と違う行 %s(参考: 後の空の欄を除く読みと違う行 %s)" % (
        frac(pb, s5[u"両方に在る P の行"]), frac(s5[u"参考: 後の P の行のうち字のとおりの読みの自・実・他が空の欄を除く読みの自・実・他と違う行"], s5[u"P の行(後)"]))
    m[u"RT-6"] = u"・".join(u"%s %s" % (n, frac(r6[k][u"分子"], r6[k][u"分母"])) for n, k in zip(names, r6k))
    m[u"RT-7"] = RT7_MEAS
    return m


def stage_lines(c):
    u"""§2 の段ごとの行(名前, 字)。"""
    s1, s2, s3, s4, s5 = [st(c, k) for k in (K1, K2, K3, K4, K5)]
    E = []

    def trans_rows(prefix, s):
        t = trans_table(s)
        E.append((prefix + u" trans head", u"| 前 \\ 後 | " + u" | ".join(STATES) + u" |"))
        for a in STATES:
            E.append((prefix + u" trans " + a, u"| %s | " % a + u" | ".join(u"%d" % t[(a, z)] for z in STATES) + u" |"))
        E.append((prefix + u" st head", u"| state | 前 | 後 | 差 |"))
        for s_ in STATES:
            a = sum(t[(s_, z)] for z in STATES)
            z = sum(t[(x, s_)] for x in STATES)
            E.append((prefix + u" st " + s_, u"| %s | %d | %d | %+d |" % (s_, a, z, z - a)))

    for prefix, s in ((u"s1", s1), (u"s2", s2)):
        ch = s[u"state が変わった行"]
        E.append((prefix + u" 行", u"- 行は前 %d・後 %d・両方に在る行 %d・消えた行 %d・増えた行 %d。" % (
            s[u"行(前)"], s[u"行(後)"], s[u"両方に在る行"], s[u"前にだけ在る行(消えた行)"], s[u"後にだけ在る行(増えた行)"])))
        E.append((prefix + u" 変わった", u"- state が変わった行 %s(%d 本)。前は GROUNDED でなく後は GROUNDED の行 %d・前は GROUNDED で後は GROUNDED でない行 %d・前は GROUNDED で消えた行 %d・state は同じで reason だけ変わった行 %d。" % (
            frac(ch[u"分子"], ch[u"分母"]), s[u"state が変わった行を持つ本"], s[u"前は GROUNDED でなく後は GROUNDED の行(両方に在る行)"],
            s[u"前は GROUNDED で後は GROUNDED でない行(両方に在る行)"], s[u"前は GROUNDED で消えた行"], s[u"state は同じで reason だけ変わった行"])))
        trans_rows(prefix, s)
        if prefix == u"s1":
            rt1 = c.rec[K_RT1]
            E.append((u"s1 NRE", u"- 便 NRE の記録の「直した engine の state」と比べて違う行 %s(RT-1。恒等に近い配線の確かめ)。" % frac(rt1[u"state が違う行"][u"分子"], rt1[u"state が違う行"][u"分母"])))
    # 段 2
    was, now = s2[u"集計(前)"], s2[u"集計(後)"]
    same_rep = s2[u"置き換えた回数の合計(規則 1・2・3)(前)"] == s2[u"置き換えた回数の合計(規則 1・2・3)(後)"] and s2[u"写した本(前)"] == s2[u"写した本(後)"]
    E.append((u"s2 fact", u"- 写した本 %d・置き換えた回数の合計(規則 1・2・3)は前後で%s。fact の数の合計は前 %d・後 %d。" % (
        s2[u"写した本(後)"], u"同じ" if same_rep else u"違う", was[u"fact の数の合計"], now[u"fact の数の合計"])))
    bw, bn = s2[u"TSS の B(写さない)との動き(前)"], s2[u"TSS の B(写さない)との動き(後)"]
    E.append((u"s2 B", u"- 第 2 便の「写す前 → 写した後」の動いた行は前 %d・後 %d。写す前は GROUNDED だった行のうち写した後に GROUNDED でなくなった行は前 %d・後 %d。" % (
        bw[u"動いた行"], bn[u"動いた行"], bw[u"GROUNDED だった行のうち GROUNDED でなくなった行"], bn[u"GROUNDED だった行のうち GROUNDED でなくなった行"])))
    # 段 3
    gone3, new3 = s3[u"前にだけ在る行(消えた行)"], s3[u"後にだけ在る行(増えた行)"]
    E.append((u"s3 近い", u"- 近い行は前 %d・後 %d。前の近い行のうち後も近い行 %s・消えた行 %d・増えた行 %d。当たった規則が変わった行 %d・単位の族が変わった行 %d。" % (
        s3[u"近い行(前)"], s3[u"近い行(後)"], frac(s3[u"前の近い行のうち後も近い行"], s3[u"近い行(前)"]), gone3, new3,
        s3[u"両方に在る行のうち当たった規則が変わった行"], s3[u"両方に在る行のうち単位の族が変わった行"])))
    E.append((u"s3 head", u"| 群 | 「値が違う」の行(前 → 後) | 近い行(前 → 後) | N-円(前 → 後) | N-桁(前 → 後) | N-率(前 → 後) |"))
    for g, label in ((u"A(甲 + 乙)", u"A(甲 + 乙)"), (u"B(丙)", u"B(丙)")):
        a, b = s3[u"集計(前)"][g], s3[u"集計(後)"][g]
        rule = lambda r: u"%d → %d" % (a[u"規則ごとの行の数"][r], b[u"規則ごとの行の数"][r])
        E.append((u"s3 " + g, u"| %s | %d → %d | %d → %d | %s | %s | %s |" % (label, a[u"VALUE_MISMATCH の行"], b[u"VALUE_MISMATCH の行"], a[u"近い行"], b[u"近い行"],
                                                                   rule(u"N-円"), rule(u"N-桁"), rule(u"N-率"))))
    # 段 4
    ch4 = s4[u"結果の語が変わった行"]
    E.append((u"s4 行", u"- 注入の行は前 %d・後 %d・両方に在る行 %d・消えた行 %d・増えた行 %d。結果の語が変わった行 %s。" % (
        s4[u"注入の行(前)"], s4[u"注入の行(後)"], s4[u"両方に在る行"], s4[u"前にだけ在る行(消えた行)"], s4[u"後にだけ在る行(増えた行)"], frac(ch4[u"分子"], ch4[u"分母"]))))
    pf, pn = s4[u"通した行(前)"], s4[u"通した行(後)"]
    E.append((u"s4 通した", u"- 通した行の合計は前 %d・後 %d。うち丙の期の入れ替えの型は前 %d・後 %d。型ごと(前 → 後): %s。" % (
        pf[u"通した行の合計"], pn[u"通した行の合計"], pf[u"うち丙の期の入れ替えの型"], pn[u"うち丙の期の入れ替えの型"],
        u"・".join(u"%s %d → %d" % (t, pf[u"型ごと"][t], pn[u"型ごと"][t]) for t in pf[u"型ごと"]))))
    stay, left, came = pass_flow(s4)
    E.append((u"s4 流れ", u"- 行の id の鍵の上で、前も後も通した行 %d・前は通して後は通さない行 %d・前は通さず後は通した行 %d。合計が前後で同じでも、同じ行が通したとは限らない(RT-4b)。" % (stay, left, came)))
    E.append((u"s4 cell head", u"| 群 × 型 | 前(名指して原本の値を返した) | 後 | 動き(ポイント。後 − 前) | 封の幅 |"))
    lim = seal_bounds(c.seal)[u"RT-4c"]
    cells = cells_of(s4)
    for k in CELL_KEYS:
        x = cells[k]
        E.append((u"s4 cell %s %s" % k, u"| %s × %s | %s | %s | %s | %s |" % (
            k[0], k[1], frac(x[u"前の分子"], x[u"前の分母"]), frac(x[u"後の分子"], x[u"後の分母"]), point_text(cell_shift(x)), u"超えた" if abs(cell_shift(x)) >= lim else u"未満")))
    E.append((u"s4 trans head", u"| 前の結果の語 \\ 後 | " + u" | ".join(WORDS) + u" |"))
    t4 = trans_table4(s4)
    for a in WORDS:
        E.append((u"s4 trans " + a, u"| %s | " % a + u" | ".join(u"%d" % t4[(a, z)] for z in WORDS) + u" |"))
    pop_was, pop_now = s4[u"母集団(前)"], s4[u"母集団(後)"]
    E.append((u"s4 母集団", u"- 母集団は前後で%s: 対象の本(切れた本)%d・切れない本 %d・A %d・丙 %d。" % (
        u"同じ" if pop_was == pop_now else u"違う", pop_now[u"対象の本(切れた本)"], pop_now[u"切れない本"], pop_now[u"A"], pop_now[u"丙"])))
    # 段 5
    E.append((u"s5 行", u"- P の行は前 %d・後 %d。W の行は前 %d・後 %d。両方に在る行 %d・消えた行 %d・増えた行 %d。どれかの欄が変わった行 %s。" % (
        s5[u"P の行(前)"], s5[u"P の行(後)"], s5[u"W の行(前)"], s5[u"W の行(後)"], s5[u"両方に在る行"], s5[u"前にだけ在る行(消えた行)"], s5[u"後にだけ在る行(増えた行)"],
        frac(s5[u"どれかの欄が変わった行"], s5[u"両方に在る行"]))))
    E.append((u"s5 head", u"| 読み | 札が変わった行 | 前の自・実・他 | 後の自・実・他 | 自 / 行の全部(前 → 後) |"))
    chg = list(s5[K_PS_FLAG_CHG].values())
    for i, name in enumerate(READINGS):
        a, b = ps_read(s5[K_PS_AGG_WAS], i), ps_read(s5[K_PS_AGG_NOW], i)
        E.append((u"s5 read %d" % i, u"| %s | %d | %d / %d / %d | %d / %d / %d | %s → %s |" % (
            name, chg[i], a[u"自"], a[u"実"], a[u"他"], b[u"自"], b[u"実"], b[u"他"], rate_text(a[u"自"], a[u"行"]), rate_text(b[u"自"], b[u"行"]))))
    E.append((u"s5 参考", u"- 参考(RT-5b): 後の P の行のうち字のとおりの読みの自・実・他が後の空の欄を除く読みの自・実・他と違う行 %s。前の記録の「字のとおりの読み × 空の欄を除く読み」の旗と違う行 %s。" % (
        frac(s5[u"参考: 後の P の行のうち字のとおりの読みの自・実・他が空の欄を除く読みの自・実・他と違う行"], s5[u"P の行(後)"]),
        frac(s5[u"両方に在る P の行のうち後の字のとおりの読みの自・実・他が前の字のとおり × 空の欄を除く読みの自・実・他と違う行"], s5[u"両方に在る P の行"]))))
    pw, pn_ = s5[K_PS_WAS], s5[K_PS_NOW]
    ew = pw[K_PS_EMPTY]
    E.append((u"s5 fact", u"- サマリーの fact は前 F %d・R %d・F が空の本 %d(切れた本 %d のうち)、後 F %d・R %d・F が空の本 %d。前の記録の「空の欄を除く読み」(F %d・R %d・F が空の本 %d)は後の数と%s。" % (
        pw[u"F の fact の数の合計"], pw[u"R の fact の数の合計"], pw[u"F が空の本の数(切れた本のうち)"], pw[u"切れた本"],
        pn_[u"F の fact の数の合計"], pn_[u"R の fact の数の合計"], pn_[u"F が空の本の数(切れた本のうち)"],
        ew[u"F の fact の数の合計"], ew[u"R の fact の数の合計"], ew[u"F が空の本の数(切れた本のうち)"],
        u"同じ" if (ew[u"F の fact の数の合計"], ew[u"R の fact の数の合計"], ew[u"F が空の本の数(切れた本のうち)"]) == (
            pn_[u"F の fact の数の合計"], pn_[u"R の fact の数の合計"], pn_[u"F が空の本の数(切れた本のうち)"]) else u"違う")))
    return E


def with_sep(E):
    u"""表の見出しの行の次に、列の数と同じ区切りの行を入れる。"""
    out = []
    for i, (n, line) in enumerate(E):
        out.append((n, line))
        if n.endswith(u"head") and line.startswith(u"|") and i + 1 < len(E) and E[i + 1][1].startswith(u"|"):
            out.append((n + u" sep", u"|" + u"---|" * (line.count(u"|") - 1)))
    return out


def expected_lines(c):
    return with_sep(expected_lines_raw(c))


def expected_lines_raw(c):
    u"""[(名前, 文書に 1 回ずつ在るはずの 1 行)]。数は全部ここで記録から組む。"""
    s1, s2, s3, s4, s5 = [st(c, k) for k in (K1, K2, K3, K4, K5)]
    vd = verdicts(c)
    meas = meas_texts(c)
    b = seal_bounds(c.seal)
    cells = cells_of(s4)
    E = [(k, FIXED[k]) for k in (u"title",)]
    E.append((u"hdr 封", u"封 `%s`(commit %s)。script `%s`・記録 `%s`・封の門 `%s` は commit %s(独立監査は 1 回目 REVISE・門を強化して 2 回目 GO)。"
                        u"取得 0・0 USD・通信なし・LLM の席は呼んでいない。" % (SEAL_REL, SEAL_COMMIT_SHORT, SCRIPT_REL, RECORD_REL, SEAL_GATE_REL, RECORD_COMMIT_SHORT)))
    E.append((u"hdr 数", u"この文書の数は全部、記録から 1 つずつ読んだもの(結果の門が、記録から組み直した行と字で同じことを見る)。engine は 0 行(engine を変えた commit は無い)。"))
    E.append((u"lead head", FIXED[u"lead head"]))
    hits = [i for i, v in zip(PRED_IDS, vd) if v == HIT]
    misses = [i for i, v in zip(PRED_IDS, vd) if v == MISS]
    E.append((u"lead 予測", u"- 判定した %d 本(RT-7 を除く)のうち、%s が外れ・%s が当たり(当たり %d・外れ %d)。RT-7 は判定しない(この便の commit の前に司令塔が全数を 1 回走らせる)。" % (
        len(PRED_IDS), u"・".join(misses), u"・".join(hits), len(hits), len(misses))))
    big = [k for k in CELL_KEYS if abs(cell_shift(cells[k])) >= b[u"RT-4c"]]
    E.append((u"lead 4c", u"- RT-4c が外れ: 偶然の一致の型の升 %d つ(%s)で、「名指して原本の値を返した」の率の動きが封の幅以上(%s)。司令塔は動きを小さく見すぎた。" % (
        len(big), u"・".join(u"%s × %s" % k for k in big), u"・".join(point_text(cell_shift(cells[k])) for k in big))))
    chg_keys = s4[u"両方に在る行のうち型・形・単位・基準の claim のどれかが違う行"]
    E.append((u"lead 鍵", u"- 注入の行の前後の突き合わせは、同じ id が前後で同じ注入を指さない行が在り(両方に在る行 %d のうち %d 行は型・形・単位・基準の claim のどれかが違う)、行と行の比べになっていない。" % (
        s4[u"両方に在る行"], chg_keys)))
    E.append((u"lead 読み", FIXED[u"lead 読み"]))
    E.append((u"lead 取り直し", FIXED[u"lead 取り直し"]))
    E.append((u"h1", FIXED[u"h1"]))
    E.append((u"pred head", FIXED[u"pred head"]))
    E.append((u"table head", FIXED[u"table head"]))
    for i in ALL_IDS:
        v = vd[ALL_IDS.index(i)] if i != u"RT-7" else NOJ
        E.append((u"table " + i, u"| %s | %s | %s | %s |" % (i, seal_row(c.seal, i), meas[i], v)))
    E.append((u"pred_count", u"- 当たり %d(%s)・外れ %d(%s)・判定しない 1(RT-7)。" % (len(hits), u"・".join(hits), len(misses), u"・".join(misses))))
    E.append((u"pred rt1", FIXED[u"pred rt1"]))
    stay, left, came = pass_flow(s4)
    E.append((u"pred rt4b", u"- RT-4b は合計が前後とも %d で同じ数だが、中身は入れ替わっている。行の id の鍵の上で、前も後も通した行 %d・前は通して後は通さない行 %d・前は通さず後は通した行 %d。"
                            u"「同じ行が通した」とは読まない(§2 の段 4・§3)。" % (s4[u"通した行(後)"][u"通した行の合計"], stay, left, came)))
    sh = [(k, cells[k]) for k in big]
    E.append((u"pred rt4c", u"- RT-4c は外れ。封の幅を超えた升は %s で、向きは逆。ほかの升の動きは %s。分子・分母は %s。" % (
        u"・".join(u"%s × %s は %s" % (k[0], k[1], point_text(cell_shift(x))) for k, x in sh),
        u"・".join(point_text(cell_shift(cells[k])) for k in CELL_KEYS if k not in big),
        u"・".join(u"%s × %s は %d/%d → %d/%d" % (k[0], k[1], x[u"前の分子"], x[u"前の分母"], x[u"後の分子"], x[u"後の分母"]) for k, x in sh))))
    lo5, hi5 = b[u"RT-5a"]
    E.append((u"pred rt5a", u"- RT-5a は前も後も %d で同じ数。封の幅(%d 以上 %d 以下)は前の数の ± %d で、幅が効いていない = 当たっても弱い。" % (
        s5[u"P の行(後)"], lo5, hi5, hi5 - s5[u"P の行(前)"])))
    pb = s5[u"両方に在る P の行のうち後の字のとおりの読みの自・実・他が前の字のとおり × 空の欄を除く読みの自・実・他と違う行"]
    E.append((u"pred rt5b", u"- RT-5b は %s。後の字のとおりの読みの旗は、前の記録の「字のとおりの読み × 空の欄を除く読み」の旗と全部同じ。後の字のとおりの読み 対 後の空の欄を除く読みも同じで、"
                            u"こちらは恒等に近い(配線の確かめ)。" % frac(pb, s5[u"両方に在る P の行"])))
    k1, k3, k4, kp = b[u"RT-6"]
    r6 = c.rec[K_PRED][K_RT6]
    E.append((u"pred rt6", u"- RT-6 は 4 つとも封の幅の中: 第 1 便の標本 %d 行(幅 %d 行以下)・近い行の読み %d 行(%d 行以下)・通した行の札 %d 行(%d 行以下)・便 PS の読み %d 行(読んだ行の %d%% 以下)。" % (
        r6[u"第 1 便の標本(state が「値が違う」でなくなった行)"][u"分子"], k1, r6[u"近い行の読み(近い行でなくなった行)"][u"分子"], k3,
        r6[u"通した行の札(通した行でなくなった行)"][u"分子"], k4, r6[u"便 PS の読みの行(P か W でなくなった行)"][u"分子"], kp)))
    E.append((u"pred rt7", FIXED[u"pred rt7"]))
    E.append((u"h2", FIXED[u"h2"]))
    E.append((u"s2 head", FIXED[u"s2 head"]))
    st_lines = dict(stage_lines(c))
    order = [n for n, _l in stage_lines(c)]
    head_of = {u"s1": u"h s1", u"s2": u"h s2", u"s3": u"h s3", u"s4": u"h s4", u"s5": u"h s5"}
    seen = set()
    for n in order:
        p = n.split(u" ")[0]
        if p not in seen:
            seen.add(p)
            E.append((head_of[p], FIXED[head_of[p]]))
            if p == u"s4":
                E.append((u"s4 鍵", FIXED[u"s4 鍵"]))
        E.append((n, st_lines[n]))
    E.append((u"h3", FIXED[u"h3"]))
    E.append((u"key 数", u"- 記録は、両方に在る行ごとの「型・形・単位・基準の claim が前後で同じか」の数を 1 つだけ持つ。両方に在る行 %d のうち、どれかが違う行 %s。"
                         u"結果の語が変わった行 %s。" % (s4[u"両方に在る行"], frac(chg_keys, s4[u"両方に在る行"]), frac(s4[u"結果の語が変わった行"][u"分子"], s4[u"結果の語が変わった行"][u"分母"]))))
    for k in (u"key 比べ", u"key 升", u"key 記録なし"):
        E.append((k, FIXED[k]))
    E.append((u"h4", FIXED[u"h4"]))
    E.append((u"p head", FIXED[u"p head"]))
    names = (u"第 1 便の標本(state が「値が違う」でなくなった行)", u"近い行の読み(近い行でなくなった行)", u"通した行の札(通した行でなくなった行)", u"便 PS の読みの行(P か W でなくなった行)")
    bound_txt = (u"%d 行以下" % k1, u"%d 行以下" % k3, u"%d 行以下" % k4, u"読んだ行の %d%% 以下" % kp)
    for i, (nm, bt) in enumerate(zip(names, bound_txt)):
        E.append((u"p %d" % i, u"| %s | %s | %s |" % (nm, frac(r6[nm][u"分子"], r6[nm][u"分母"]), bt)))
    E.append((u"p note", FIXED[u"p note"]))
    E.append((u"h5", FIXED[u"h5"]))
    for i, t in enumerate(c.rec[u"読み替えた所"]):
        E.append((u"swap %d" % i, u"- " + t))
    E.append((u"h6", FIXED[u"h6"]))
    E.append((u"read 範囲", FIXED[u"read 範囲"]))
    s1c, s2c = s1[u"state が変わった行"], s2[u"state が変わった行"]
    E.append((u"read 1", u"- 段 1: state が変わった行は %s。前は GROUNDED でなく後は GROUNDED の行 %d・その逆 %d。便 NRE の記録の数と同じ(RT-1)。" % (
        frac(s1c[u"分子"], s1c[u"分母"]), s1[u"前は GROUNDED でなく後は GROUNDED の行(両方に在る行)"], s1[u"前は GROUNDED で後は GROUNDED でない行(両方に在る行)"])))
    E.append((u"read 2", u"- 段 2: state が変わった行は %s。GROUNDED になった行 %d・GROUNDED でなくなった行 %d。" % (
        frac(s2c[u"分子"], s2c[u"分母"]), s2[u"前は GROUNDED でなく後は GROUNDED の行(両方に在る行)"], s2[u"前は GROUNDED で後は GROUNDED でない行(両方に在る行)"])))
    E.append((u"read 3", u"- 段 3: 近い行は %d → %d(消えた行 %d・増えた行 %d)。当たった規則・単位の族が変わった行は 0。" % (
        s3[u"近い行(前)"], s3[u"近い行(後)"], s3[u"前にだけ在る行(消えた行)"], s3[u"後にだけ在る行(増えた行)"])))
    small = [point_text(cell_shift(cells[k])) for k in CELL_KEYS if k not in big]
    E.append((u"read 4", u"- 段 4: 注入の行は %d → %d。通した行の合計は %d → %d。6 つの升のうち %d つは動きが封の幅の中(%s)・%d つ(偶然の一致の型)は封の幅以上に動いた(%s)。" % (
        s4[u"注入の行(前)"], s4[u"注入の行(後)"], s4[u"通した行(前)"][u"通した行の合計"], s4[u"通した行(後)"][u"通した行の合計"], len(small), u"・".join(small), len(big),
        u"・".join(point_text(cell_shift(cells[k])) for k in big))))
    a0, b0 = ps_read(s5[K_PS_AGG_WAS], 0), ps_read(s5[K_PS_AGG_NOW], 0)
    E.append((u"read 5", u"- 段 5: P の行は %d → %d。字のとおりの読み(主)の自は %d → %d(自 / 行の全部は %s → %s)・他は %d → %d。"
                         u"前の主の数は、直す前の engine が壊した fact に当てた数だった(便 PS の限界)。後の数は便 PS の「空の欄を除く」読みの数と同じ。" % (
        s5[u"P の行(前)"], s5[u"P の行(後)"], a0[u"自"], b0[u"自"], rate_text(a0[u"自"], a0[u"行"]), rate_text(b0[u"自"], b0[u"行"]), a0[u"他"], b0[u"他"])))
    E.append((u"read PS", u"- 便 PS の「空の欄を除く」読みは、直した engine の字のとおりの読みと、P の行 %d の全部で同じ旗だった(違う行 %d)。" % (
        s5[u"P の行(後)"], s5[u"参考: 後の P の行のうち字のとおりの読みの自・実・他が空の欄を除く読みの自・実・他と違う行"])))
    E.append((u"h7", FIXED[u"h7"]))
    for k in (u"lim 1", u"lim 2", u"lim 3", u"lim 4", u"lim 5", u"lim 6", u"lim 鍵", u"lim 読み", u"lim 門", u"lim 監査", u"lim 判定", u"lim 縛り", u"lim 出力"):
        E.append((k, FIXED[k]))
    E.append((u"h8", FIXED[u"h8"]))
    for k in (u"next 1", u"next 2", u"next 3"):
        E.append((k, FIXED[k]))
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
    want_count = collections.Counter(l for _n, l in exp)
    for n, line in exp:
        k = lines.count(line)
        if k != want_count[line]:
            out.append(u"文書: 記録から組んだ行「%s」が文書に決めた回数(%d 回)だけ無い(%d 回): %s" % (n, want_count[line], k, line[:40]))
    # 組んだ行が文書の中で組んだ順に並ぶ(1 回しか無い行だけ)
    pos = [lines.index(line) for _n, line in exp if want_count[line] == 1 and lines.count(line) == 1]
    if pos != sorted(pos):
        out.append(u"文書: 組んだ行の順が決めた順と違う")
    expset = set(l for _n, l in exp)
    allowed = set()
    for _n, line in exp:
        allowed |= numbers_of(line)
    for ln, line in enumerate(lines, 1):
        if line in expset or not line.strip():
            continue
        out.append(u"文書: 組んだ行にない行が在る: 行 %d %s" % (ln, line[:30]))
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
    for need in (os.path.basename(SEAL_REL), SEAL_COMMIT_SHORT, RECORD_COMMIT_SHORT, os.path.basename(SCRIPT_REL), os.path.basename(RECORD_REL)) + REQUIRED_PHRASES:
        if need not in doc:
            out.append(u"words: 要点の字が無い: %s" % need)
    return out


LEAD_HEAD = u"**先に負けと限界を書く。**"
LEAD_NEXT = u"## §1 "
LIMIT_HEAD = u"## §7 "
LIMIT_NEXT = u"## §8 "


def section(doc, head, nxt=None):
    if head not in doc:
        return u""
    t = doc[doc.index(head):]
    if nxt is not None and nxt in t[len(head):]:
        t = t[:len(head) + t[len(head):].index(nxt)]
    return t


def limits_problems(c):
    u"""要点の行(負けの節・限界の節)が決めた節に 1 回ずつ在る。RT-7 は当たり外れの字を持たない。RT-4c は外れ。"""
    out = []
    lead = section(c.doc, LEAD_HEAD, LEAD_NEXT).split(u"\n")
    lim = section(c.doc, LIMIT_HEAD, LIMIT_NEXT).split(u"\n")
    exp = dict(expected_lines(c))
    want = [(k, exp[k], lead) for k in (u"lead 予測", u"lead 4c", u"lead 鍵", u"lead 読み", u"lead 取り直し")]
    want += [(k, exp[k], lim) for k in (u"lim 1", u"lim 2", u"lim 3", u"lim 4", u"lim 5", u"lim 6", u"lim 鍵", u"lim 読み", u"lim 門", u"lim 監査", u"lim 判定", u"lim 縛り", u"lim 出力")]
    for name, line, where in want:
        if where.count(line) != 1:
            out.append(u"limits: 要点の行が決めた節に 1 回ずつ無い: %s" % name)
    lines = c.doc.split(u"\n")
    row7 = [l for l in lines if l.startswith(u"| RT-7 |")]
    if len(row7) != 1 or u"当たり" in row7[0] or u"外れ" in row7[0] or NOJ not in row7[0] or RT7_MEAS not in row7[0]:
        out.append(u"limits: RT-7 の表の行が「判定しない」と司令塔が走らせる字だけを持つ形でない")
    pr7 = [l for l in lines if l.startswith(u"- RT-7: ")]
    if len(pr7) != 1 or u"当たり" in pr7[0] or u"外れ" in pr7[0] or u"引き継ぎに書く" not in pr7[0]:
        out.append(u"limits: RT-7 の説明の行が当たり外れの字を持たない形でない")
    row4c = [l for l in lines if l.startswith(u"| RT-4c |")]
    if len(row4c) != 1 or MISS not in row4c[0]:
        out.append(u"limits: RT-4c の表の行が外れを持たない")
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
    for need in (u"**1 行以上 137 行以下**", u"**205 以上 235 以下**", u"**200 行以上**", u"**3,726 以上 3,800 以下**", u"**どれも 1.5 ポイント未満**", u"**784 以上 804 以下**",
                 u"**6 行以下**", u"**5% 以下**", u"## 3. 予測", u"RT-7"):
        if need not in c.seal:
            out.append(u"seal: 封に %s が無い" % need)
    try:
        seal_bounds(c.seal)
    except (AttributeError, ValueError, TypeError, IndexError):
        out.append(u"seal: 予測の境が取れない")
    return out


def order_problems_real(root=REPO):
    u"""封 ⊏ script・記録・封の門 ⊑ 結果の文書・この門(未 commit は赤)。"""
    return PR.order_problems(root, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, [SCRIPT_REL, RECORD_REL, SEAL_GATE_REL], [DOC_REL, GATE_REL])


def record_commit_problems(root=REPO):
    u"""script・記録・封の門を足した commit が履歴に 1 つで、字で持つ短い hash で始まる(3 つとも同じ commit)。"""
    out = []
    firsts = set()
    for rel in (SCRIPT_REL, RECORD_REL, SEAL_GATE_REL):
        c = PR.added_commits(root, PREFIX + rel)
        if len(c) != 1:
            out.append(u"%s を足した commit が履歴に 1 つで決まらない" % rel)
        else:
            firsts.add(c[0])
    if len(firsts) != 1:
        out.append(u"script・記録・封の門が同じ commit で足されていない")
    elif not list(firsts)[0].startswith(RECORD_COMMIT_SHORT):
        out.append(u"記録の commit が字で持つ hash と違う")
    return out


def engine_problems(root=REPO):
    u"""engine は封の commit から 0 行(未 commit も)。"""
    return list(SG.engine_zero_problems(root))


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


def bump(path, delta=1):
    u"""記録(c.rec)の入れ子の dict の数を ``delta`` 変える。path は key の並び。"""
    def fn(c):
        node = c.rec
        for k in path[:-1]:
            node = node[k]
        node[path[-1]] += delta
    return fn


def set_at(path, value):
    def fn(c):
        node = c.rec
        for k in path[:-1]:
            node = node[k]
        node[path[-1]] = value
    return fn


def cell_edit(i, key, delta):
    def fn(c):
        c.rec[K4][K_CELLS][i][key] += delta
    return fn


def doc_line_edit(name, new):
    u"""組んだ行の 1 つを丸ごと別の字にする(名前は ``expected_lines`` の名前。文書に在る字を探す)。"""
    def fn(c):
        old = dict(expected_lines(Ctx()))[name]
        assert old in c.doc, name
        c.doc = c.doc.replace(old, new, 1)
    return fn


R4C = u"RT-4c 群 × 型の 6 つの升の「名指して原本の値を返した」の率の差(ポイント。後 − 前)"
KB = K_PRED

# a sha
M(u"a1 記録の 1 byte", u"sha", set_text(RECORD_REL, lambda t: t + b" "))
M(u"a2 script の 1 byte", u"sha", set_text(SCRIPT_REL, lambda t: t[:-1] + b"#"))
M(u"a3 封の門の 1 byte", u"sha", set_text(SEAL_GATE_REL, lambda t: t + b"\n"))
# b 記録
M(u"b1 記録の段 1 の数を 1 つ変える(行(後))", u"record", bump([K1, u"行(後)"]))
M(u"b2 記録の段 2 の変わった行の数を 1 つ変える(分子)", u"record", bump([K2, u"state が変わった行", u"分子"]))
M(u"b3 記録の段 3 の近い行(後)を 1 つ変える", u"record", bump([K3, u"近い行(後)"]))
M(u"b4 記録の段 4 の升の分子を 1 つ変える", u"record", cell_edit(4, u"後の分子", 1))
M(u"b5 記録の段 5 の P の行(後)を 1 つ変える", u"record", bump([K5, u"P の行(後)"]))
M(u"b6 記録の予測の欄(RT-3a)を 1 つ変える", u"record", bump([KB, u"RT-3a 段 3 の近い行の数(後)"]))
M(u"b7 記録に文・値の字を足す", u"record", lambda c: c.rec.__setitem__(u"漏れ", u"売上高は前期比 12.3 億円の増加となりました。"))
M(u"b8 記録の RT-6 の数を 1 つ変える", u"record", bump([KB, K_RT6, u"通した行の札(通した行でなくなった行)", u"分子"]))
M(u"b9 記録の段 5 の変わった行の数を 1 つ変える", u"record", bump([K5, u"どれかの欄が変わった行"]))
M(u"b11 記録の段 1 の変わった行を持つ本の数を 1 つ変える", u"record", bump([K1, u"state が変わった行を持つ本"]))
M(u"b10 記録の入力の sha256 を 1 つ変える", u"record", set_at([u"入力", 0, u"sha256"], u"0" * 64))
# c 文書の数・表・散文
M(u"c1 表の実測の分子を 1 つ変える(RT-2a)", u"doc", doc_replace(u"段 2 で state が変わった行 107/6834(1.6%)", u"段 2 で state が変わった行 108/6834(1.6%)"))
M(u"c2 表の判定の当たりと外れを入れ替える(RT-4c)", u"doc", lambda c: setattr(c, "doc", re.sub(r"(\| RT-4c \|.*?\| )\*\*外れ\*\* \|", r"\1当たり |", c.doc, count=1)))
M(u"c3 表の判定の当たりと外れを入れ替える(RT-1)", u"doc", lambda c: setattr(c, "doc", re.sub(r"(\| RT-1 \|.*?\| )当たり \|", r"\1**外れ** |", c.doc, count=1)))
M(u"c4 RT-7 の判定に当たりを書く", u"limits", lambda c: setattr(c, "doc", re.sub(r"(\| RT-7 \|.*?\| )判定しない \|", r"\1当たり |", c.doc, count=1)))
M(u"c5 散文の数を変える(要約の行の本数)", u"doc", doc_replace(u"(当たり 10・外れ 1)", u"(当たり 9・外れ 2)"))
M(u"c6 散文に記録に無い数を足す(組んだ行にない行)", u"doc", doc_append(u"\n- 追記: 12345 行。\n"))
M(u"c7 散文の数を変える(段 4 の通した行の流れ)", u"doc", doc_line_edit(u"s4 流れ", u"- 行の id の鍵の上で、前も後も通した行 8・前は通して後は通さない行 1・前は通さず後は通した行 1。合計が前後で同じでも、同じ行が通したとは限らない(RT-4b)。"))
M(u"c8 移り変わりの表の数を 1 つ変える(段 1)", u"doc", doc_replace(u"| GROUNDED | 6634 | 0 | 0 | 0 |", u"| GROUNDED | 6635 | 0 | 0 | 0 |"))
M(u"c9 state の表の差を変える(段 2)", u"doc", doc_replace(u"| GROUNDED | 2152 | 2177 | +25 |", u"| GROUNDED | 2152 | 2177 | +24 |"))
M(u"c10 段 4 の結果の語の表の数を 1 つ変える", u"doc", doc_replace(u"| 通した | 9 | 1 | 0 | 0 | 0 | 0 |", u"| 通した | 9 | 2 | 0 | 0 | 0 | 0 |"))
M(u"c11 段 4 の升の表の数を変える(丙 × T5_COINCIDENT)", u"doc", doc_replace(u"| 丙 × T5_COINCIDENT | 40/313(12.8%) | 45/314(14.3%) | 1.55 | 超えた |", u"| 丙 × T5_COINCIDENT | 40/313(12.8%) | 45/314(14.3%) | 1.45 | 未満 |"))
M(u"c12 段 5 の表の数を変える(字のとおりの読み(主)の後の自)", u"doc", doc_replace(u"193 / 71 / 8 | 310 / 88 / 16 | 24.3% → 39.0% |", u"193 / 71 / 8 | 311 / 88 / 16 | 24.3% → 39.0% |"))
M(u"c13 段 3 の表の数を変える", u"doc", doc_replace(u"| A(甲 + 乙) | 1898 → 1858 | 163 → 159 |", u"| A(甲 + 乙) | 1898 → 1858 | 163 → 158 |"))
M(u"c14 組んだ行を消す(材料に当たる行 = 段 3 の近い行)", u"doc", doc_line_edit(u"s3 近い", u""))
M(u"c15 禁止語を doc の check にも通す(証明した)", u"doc", doc_append(u"\n証明" + u"した。\n"))
M(u"c16 散文の数を変える(読める事の段 1)", u"doc", doc_line_edit(u"read 1", u"- 段 1: state が変わった行は 207/24531(0.8%)。前は GROUNDED でなく後は GROUNDED の行 85・その逆 0。便 NRE の記録の数と同じ(RT-1)。"))
M(u"c17 限界の節の途中に記録に無い数を足す", u"doc", doc_replace(u"英文短信の側は別のセッション", u"英文短信の側 4321 は別のセッション"))
M(u"c18 RT-7 の文を変える(結果を書く)", u"limits", doc_replace(u"- RT-7: この便の commit の前に司令塔が全数を 1 回走らせる。結果はこの文書に書かない(引き継ぎに書く)。", u"- RT-7: 全数の赤は 0 で当たり。"))
M(u"c19 表の「封の字」を変える(RT-4c)", u"doc", doc_replace(u"どれも 1.5 ポイント未満", u"どれも 2.5 ポイント未満"))
M(u"c20 行の順を入れ替える(要約の 2 行)", u"doc", lambda c: setattr(c, "doc", _swap_lines(c.doc, u"lead 予測", u"lead 4c")))
M(u"c21 読み替えた所の 1 つを変える(文書の字)", u"doc", doc_replace(u"- 前の記録の取り出し", u"- 前の記録の取り出しを変えた"))
M(u"c22 鍵の数(472)を変える", u"doc", doc_replace(u"472/3705", u"471/3705"))
M(u"c23 RT-5a の行の幅を変える", u"doc", doc_replace(u"(784 以上 804 以下)は前の数の ± 10", u"(784 以上 804 以下)は前の数の ± 11"))
# d 判定
M(u"d1 RT-1 の違う行を 1 にして外れに動かす", u"judge", set_at([K_RT1, u"state が違う行", u"分子"], 1))
M(u"d2 段 2 の変わった行を 138 行にして RT-2a を外れに動かす", u"judge", lambda c: c.rec[K2][u"変わった行"].extend([c.rec[K2][u"変わった行"][0]] * 31))
M(u"d3 段 2 の変わった行の 1 つを GROUNDED から外して RT-2b を外れに動かす", u"judge", lambda c: c.rec[K2][u"変わった行"].__setitem__(0, [1, 1, 1, G, UN]))
M(u"d4 段 3 の近い行(後)を 236 にして RT-3a を外れに動かす", u"judge", set_at([K3, u"近い行(後)"], 236))
M(u"d5 段 3 の後も近い行を 199 にして RT-3b を外れに動かす", u"judge", set_at([K3, u"前の近い行のうち後も近い行"], 199))
M(u"d6 段 4 の注入の行(後)を 3801 にして RT-4a を外れに動かす", u"judge", set_at([K4, u"注入の行(後)"], 3801))
M(u"d7 段 4 の通した行(後)の合計を 13 にして RT-4b を外れに動かす", u"judge", set_at([K4, u"通した行(後)", u"通した行の合計"], 13))
M(u"d8 段 4 の丙の期の入れ替えの型(後)を 7 にして RT-4b を外れに動かす", u"judge", set_at([K4, u"通した行(後)", u"うち丙の期の入れ替えの型"], 7))
M(u"d9 外れの升を動かして当たりにする(RT-4c が当たりに動く)", u"judge", lambda c: (c.rec[K4][K_CELLS][1].__setitem__(u"後の分子", 115), c.rec[K4][K_CELLS][1].__setitem__(u"後の分母", 691),
                                                           c.rec[K4][K_CELLS][4].__setitem__(u"後の分子", 40), c.rec[K4][K_CELLS][4].__setitem__(u"後の分母", 313)))
M(u"d10 段 5 の P の行(後)を 805 にして RT-5a を外れに動かす", u"judge", set_at([K5, u"P の行(後)"], 805))
M(u"d11 RT-5b の違う行を 1 にして外れに動かす", u"judge", set_at([K5, u"両方に在る P の行のうち後の字のとおりの読みの自・実・他が前の字のとおり × 空の欄を除く読みの自・実・他と違う行"], 1))
M(u"d12 RT-6 の第 1 便の標本を 7 行にして外れに動かす", u"judge", set_at([KB, K_RT6, u"第 1 便の標本(state が「値が違う」でなくなった行)", u"分子"], 7))
M(u"d13 RT-6 の通した行の札を 3 行にして外れに動かす", u"judge", set_at([KB, K_RT6, u"通した行の札(通した行でなくなった行)", u"分子"], 3))
M(u"d14 RT-6 の便 PS の読みを 6 行(読んだ行の 5% を超える)にして外れに動かす", u"judge", set_at([KB, K_RT6, u"便 PS の読みの行(P か W でなくなった行)", u"分子"], 6))
M(u"d15 判定の欄(RT-4c の差の字)を 1 つ変える", u"judge", set_at([KB, R4C, u"A × T1_VALUE"], u"0.55"))
M(u"d18 結果の語の移り変わりの対角でない升を 1 つ変える(一覧と合わない)", u"judge", bump([K4, K_TRANS4, u"名指して原本の値を返した → 名指したが別の値"]))
M(u"d16 通した行の流れが合計と合わない(移り変わりの表の通した → 通した)", u"judge", bump([K4, K_TRANS4, u"通した → 通した"]))
M(u"d17 判定の欄(RT-2a)を 1 つ変える", u"judge", bump([KB, u"RT-2a 段 2 で state が変わった行 / 両方に在る行", u"分子"]))
# e 語
M(u"e1 禁止語(ハルシネーション)", u"words", doc_append(u"\nハルシ" + u"ネーション\n"))
M(u"e2 会社名らしい字", u"words", doc_append(u"\n株式会社\n"))
M(u"e3 3 桁以上の漢数字", u"words", doc_append(u"\n二百社\n"))
M(u"e4 docID の形", u"words", doc_append(u"\nS100" + u"AB12\n"))
M(u"e5 要点の字を消す(付け直していない)", u"words", doc_replace(u"付け直していない", u"付け直した", True))
M(u"e6 封の commit を言わない", u"words", doc_replace(u"b4c08fc6", u"0000000", True))
M(u"e7 禁止語(人の目)", u"words", doc_append(u"\n人の" + u"目で読んだ。\n"))
M(u"e8 要点の字を消す(恒等に近い)", u"words", doc_replace(u"恒等に近い", u"恒等ではない", True))
M(u"e9 記録の commit を言わない", u"words", doc_replace(u"a581a17e", u"0000000", True))
M(u"e10 要点の字を消す(判定しない)", u"words", doc_replace(u"判定しない", u"判定した", True))
# 要点の文
M(u"l1 負けの節の要点の文を変える(RT-4c)", u"limits", doc_line_edit(u"lead 4c", u"- RT-4c は当たり。"))
M(u"l2 限界の節の要点の文を変える(門)", u"limits", doc_line_edit(u"lim 門", u"- 門は全部を縛っている。"))
M(u"l3 限界の節の要点の文を変える(読みを付け直した)", u"limits", doc_line_edit(u"lim 読み", u"- 付け直した。"))
M(u"l4 負けの節の鍵の文を変える", u"limits", doc_line_edit(u"lead 鍵", u"- 注入の行の比べは行と行の比べ。"))
M(u"l5 限界の節の監査の文を変える", u"limits", doc_line_edit(u"lim 監査", u"- 独立監査は 1 回で GO。"))
M(u"l6 RT-4c の表の行から外れを消す", u"limits", lambda c: setattr(c, "doc", re.sub(r"(\| RT-4c \|.*?\| )\*\*外れ\*\* \|", r"\1判定しない |", c.doc, count=1)))
# f 封
M(u"f1 封の RT-2a の字を替える(根の字)", u"seal", seal_replace(u"**1 行以上 137 行以下**", u"**1 行以上 138 行以下**"))
M(u"f2 封の RT-4c の字を替える", u"seal", seal_replace(u"**どれも 1.5 ポイント未満**", u"**どれも 1.6 ポイント未満**"))
M(u"f3 封の文の途中の 1 字", u"frozen", seal_replace(u"取得 0・0 USD・通信なし", u"取得 0・0 USD・通信あり"))
M(u"f4 封の RT-3a の境を替える(判定が動く)", u"judge", seal_replace(u"**205 以上 235 以下**", u"**205 以上 213 以下**"))
M(u"f5 封の RT-4c の境を替える(判定が当たりに動く)", u"judge", seal_replace(u"**どれも 1.5 ポイント未満**", u"**どれも 1.9 ポイント未満**"))
M(u"f6 封の RT-6 の境を替える(判定が動く)", u"judge", seal_replace(u"**6 行以下**", u"**0 行以下**"))
M(u"f7 封の RT-5a の境を替える(判定が動く)", u"judge", seal_replace(u"**784 以上 804 以下**", u"**784 以上 790 以下**"))


def _swap_lines(doc, a, b):
    ctx = Ctx()
    ctx.doc = doc
    exp = dict(expected_lines(Ctx()))
    la, lb = exp[a], exp[b]
    assert la in doc and lb in doc
    return doc.replace(la, u"\x00A").replace(lb, la).replace(u"\x00A", lb)


def check_problems(check, c):
    return guard(CHECKS[check], c)


# ======================================================================================================
# 試験
class RealRecordsTest(unittest.TestCase):
    def test_a_1_the_record_the_script_and_the_seal_gate_equal_the_pinned_sha256(self):
        self.assertEqual([], sha_problems(Ctx().texts))

    def test_a_2_the_pinned_sha256_equal_the_record_header(self):
        c = Ctx()
        self.assertEqual(SHA_PIN[SCRIPT_REL], c.rec[u"この script の sha256"])
        self.assertEqual(SEAL_COMMIT_SHORT, c.rec[u"封の commit"])

    def test_b_1_the_record_equals_the_recount_from_the_old_records_and_its_rows(self):
        self.assertEqual([], record_problems(Ctx()))

    def test_c_1_the_document_lines_equal_the_lines_rebuilt_from_the_record(self):
        self.assertEqual([], doc_problems(Ctx()))

    def test_c_2_the_rebuilt_lines_are_the_ones_read_from_the_record_by_hand(self):
        c = Ctx()
        exp = dict(expected_lines(c))
        self.assertIn(u"0/24531(0.0%)", exp[u"table RT-1"])
        self.assertIn(u"107/6834(1.6%)(43 本)", exp[u"table RT-2a"])
        self.assertIn(u"前は GROUNDED で後は GROUNDED でない行 0・前は GROUNDED で消えた行 0", exp[u"table RT-2b"])
        self.assertIn(u"段 3 の近い行(後)214", exp[u"table RT-3a"])
        self.assertIn(u"212/220(96.4%)", exp[u"table RT-3b"])
        self.assertIn(u"段 4 の注入の行(後)3746", exp[u"table RT-4a"])
        self.assertIn(u"前 10・後 10・うち丙の期の入れ替えの型は前 5・後 5", exp[u"table RT-4b"])
        self.assertIn(u"A × T5_COINCIDENT -1.86", exp[u"table RT-4c"])
        self.assertIn(u"丙 × T5_COINCIDENT 1.55", exp[u"table RT-4c"])
        self.assertIn(u"段 5 の P の行(後)794(前 794)", exp[u"table RT-5a"])
        self.assertIn(u"0/794(0.0%)", exp[u"table RT-5b"])
        self.assertIn(u"第 1 便の標本 1/120(0.8%)・近い行の読み 8/200(4.0%)・通した行の札 1/10(10.0%)・便 PS の読み 0/109(0.0%)", exp[u"table RT-6"])
        self.assertIn(u"| POINTER_NOT_FOUND | 81 | 10 | 65 | 11008 |", exp[u"s1 trans POINTER_NOT_FOUND"])
        self.assertIn(u"| 丙 × T5_COINCIDENT | 40/313(12.8%) | 45/314(14.3%) | 1.55 | 超えた |", exp[u"s4 cell 丙 T5_COINCIDENT"])
        self.assertIn(u"| A × T5_COINCIDENT | 115/691(16.6%) | 103/697(14.8%) | -1.86 | 超えた |", exp[u"s4 cell A T5_COINCIDENT"])
        self.assertIn(u"472", exp[u"lead 鍵"])
        self.assertIn(u"3705", exp[u"lead 鍵"])
        self.assertIn(u"| 字のとおりの読み(主) | 139 | 193 / 71 / 8 | 310 / 88 / 16 | 24.3% → 39.0% |", exp[u"s5 read 0"])
        self.assertIn(u"| 通した | 9 | 1 | 0 | 0 | 0 | 0 |", exp[u"s4 trans 通した"])
        self.assertIn(u"前も後も通した行 9・前は通して後は通さない行 1・前は通さず後は通した行 1", exp[u"s4 流れ"])

    def test_d_1_the_judgement_is_redone_from_the_seal_text_and_the_record(self):
        self.assertEqual([], judge_problems(Ctx()))

    def test_d_2_the_real_judgement_is_ten_hits_and_one_miss(self):
        c = Ctx()
        self.assertEqual([i for i, v in zip(PRED_IDS, verdicts(c)) if v == MISS], [u"RT-4c"])
        self.assertEqual([i for i, v in zip(PRED_IDS, verdicts(c)) if v == HIT], [u"RT-1", u"RT-2a", u"RT-2b", u"RT-3a", u"RT-3b", u"RT-4a", u"RT-4b", u"RT-5a", u"RT-5b", u"RT-6"])

    def test_d_3_the_bounds_are_read_from_the_seal_text(self):
        self.assertEqual(seal_bounds(Ctx().seal), {
            u"RT-1": 0, u"RT-2a": (6834, 1, 137), u"RT-2b": 0, u"RT-3a": (205, 235), u"RT-3b": (220, 200), u"RT-4a": (3726, 3800), u"RT-4b": (8, 12, 4, 6),
            u"RT-4c": fractions.Fraction(3, 2), u"RT-5a": (784, 804), u"RT-5b": 0, u"RT-6": (6, 10, 2, 5)})

    def test_d_4_the_two_cells_over_the_bound_are_the_coincident_type_cells(self):
        c = Ctx()
        cells = cells_of(st(c, K4))
        over = [k for k in CELL_KEYS if abs(cell_shift(cells[k])) >= fractions.Fraction(3, 2)]
        self.assertEqual(over, [(u"A", u"T5_COINCIDENT"), (u"丙", u"T5_COINCIDENT")])

    def test_d_5_the_pass_rows_total_is_the_same_but_the_rows_are_swapped(self):
        s4 = st(Ctx(), K4)
        self.assertEqual(pass_flow(s4), (9, 1, 1))
        self.assertEqual((s4[u"通した行(前)"][u"通した行の合計"], s4[u"通した行(後)"][u"通した行の合計"]), (10, 10))

    def test_e_1_the_words_are_clean(self):
        self.assertEqual([], words_problems(Ctx()))

    def test_e_2_the_seal_has_the_texts_the_document_roots_on(self):
        self.assertEqual([], seal_text_problems(Ctx()))

    def test_e_3_the_lead_and_the_limits_have_their_lines(self):
        self.assertEqual([], limits_problems(Ctx()))

    def test_e_4_the_document_swap_notes_are_the_record_notes_and_the_count_is_read_from_the_record(self):
        c = Ctx()
        self.assertEqual(len(c.rec[u"読み替えた所"]), 7)
        self.assertEqual(sum(1 for n, _l in expected_lines(c) if n.startswith(u"swap ")), 7)

    def test_f_1_the_seal_is_the_text_of_the_sealed_commit(self):
        self.assertEqual([], seal_frozen_problems(Ctx()))

    def test_f_2_the_real_history_has_the_seal_before_the_record_before_the_document_and_this_gate(self):
        u"""文書・この門のどれかが未 commit なら赤(足した commit が無い。skip にしない)。全部 commit された後で初めて緑。"""
        self.assertEqual([], order_problems_real())

    def test_f_3_the_real_order_failure_before_the_commit_is_only_the_uncommitted_files(self):
        got = order_problems_real()
        self.assertTrue(all(p.startswith(u"UNCOMMITTED:") for p in got), got)

    def test_f_4_the_order_check_names_exist(self):
        for rel in (SCRIPT_REL, RECORD_REL, SEAL_GATE_REL, DOC_REL, GATE_REL):
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)

    def test_f_5_engine_is_untouched_since_the_seal_commit(self):
        self.assertEqual([], engine_problems())

    def test_f_6_the_record_commit_is_the_one_in_the_history(self):
        self.assertEqual([], record_commit_problems())


class OrderGateTest(unittest.TestCase):
    u"""順序の検査自体が、悪い順を赤にできること(使い捨ての git で)。"""

    def test_o_1_good_and_bad_orders(self):
        r = PR.Repo()
        r.put("docs/seal.md")
        s = r.commit("docs/seal.md")
        r.put("measure/s.py")
        r.put("fixtures/r.json")
        r.commit("measure/s.py", "fixtures/r.json")
        others = ["docs/r.md", "tests/g.py"]
        for o in others:
            r.put(o)
        impls = ["measure/s.py", "fixtures/r.json"]
        self.assertEqual([u"UNCOMMITTED:" + o for o in others], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], impls, others))
        r.commit(*others)
        self.assertEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], impls, others))
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
        rels = (RECORD_REL, SCRIPT_REL, SEAL_REL, DOC_REL, SEAL_GATE_REL)
        before = dict((rel, hashlib.sha256(read_bytes(rel)).hexdigest()) for rel in rels)
        c = Ctx()
        c.rec[K1][u"行(後)"] = 1
        c.doc = u"x"
        self.assertNotEqual(1, Ctx().rec[K1][u"行(後)"])
        self.assertNotEqual(u"x", Ctx().doc)
        self.assertEqual(before, dict((rel, hashlib.sha256(read_bytes(rel)).hexdigest()) for rel in rels))

    def test_m_4_the_mutation_table_covers_every_check_and_every_effect_named_in_the_brief(self):
        self.assertEqual(set(CHECKS), set(ch for _l, ch, _f in MUTATIONS))
        labels = u"\n".join(l for l, _c, _f in MUTATIONS)
        for need in (u"記録の 1 byte", u"script の 1 byte", u"表の実測の分子", u"当たりと外れを入れ替える", u"散文の数", u"散文に記録に無い数", u"禁止語", u"漢数字", u"要点の文",
                     u"封の文の途中の 1 字", u"RT-1 の違う行を 1", u"RT-2a を外れに", u"RT-2b を外れに", u"RT-3a を外れに", u"RT-3b を外れに", u"RT-4a を外れに", u"RT-4b を外れに",
                     u"RT-4c が当たりに動く", u"RT-5a を外れに", u"RT-5b の違う行", u"RT-6", u"RT-7", u"数を 1 つ変える", u"行の順を入れ替える"):
            self.assertIn(need, labels)
        self.assertGreaterEqual(len(MUTATIONS), 70)

    def test_m_5_a_hit_turned_to_a_miss_is_caught_by_the_judge_and_not_only_by_the_table(self):
        c = Ctx()
        set_at([K3, u"近い行(後)"], 236)(c)                                          # RT-3a が外れに動く。文書の表は当たりのまま
        jd = dict(judge(c))
        self.assertFalse(jd[u"RT-3a"])
        self.assertNotEqual([], judge_problems(c))

    def test_m_6_the_judge_follows_the_seal_bounds_not_a_pinned_number(self):
        c = Ctx()
        c.seal = c.seal.replace(u"**205 以上 235 以下**", u"**205 以上 213 以下**", 1)
        self.assertFalse(dict(judge(c))[u"RT-3a"])
        c.seal = c.seal.replace(u"**205 以上 213 以下**", u"**205 以上 214 以下**", 1)
        self.assertTrue(dict(judge(c))[u"RT-3a"])
        c = Ctx()
        c.seal = c.seal.replace(u"**どれも 1.5 ポイント未満**", u"**どれも 1.9 ポイント未満**", 1)
        self.assertTrue(dict(judge(c))[u"RT-4c"])

    def test_m_7_the_rt4c_judge_does_not_use_the_rounded_text(self):
        u"""差の字(小数 2 桁)でなく分子・分母の厳密な値で境と比べる。境のすぐ下・すぐ上の分子で判定が変わる。"""
        c = Ctx()
        x = cells_of(st(c, K4))[(u"丙", u"T5_COINCIDENT")]
        self.assertTrue(abs(cell_shift(x)) >= fractions.Fraction(3, 2))
        x[u"後の分子"] -= 1
        self.assertTrue(abs(cell_shift(x)) < fractions.Fraction(3, 2))

    def test_m_8_the_rt7_has_no_verdict_in_the_judge(self):
        c = Ctx()
        self.assertEqual(len(judge(c)), 11)
        self.assertNotIn(u"RT-7", [i for i, _ok in judge(c)])


class WiringTest(unittest.TestCase):
    def test_n_1_this_gate_carries_no_docid_and_no_key(self):
        src = read(GATE_REL)
        for bad in (u"ANTHRO" + u"PIC", u"API_" + u"KEY", u"url" + u"lib", u"sock" + u"et"):
            self.assertNotIn(bad, src)
        self.assertIsNone(DOCID_RE.search(src))

    def test_n_2_this_gate_does_not_widen_the_boundary_import_list(self):
        with io.open(os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py"), encoding="utf-8") as fh:
            t = fh.read()
        self.assertNotIn(u"tss_retake", t)

    def test_n_3_this_gate_does_not_use_the_reserved_names(self):
        self.assertEqual([], SG.reserved_problems(rel=GATE_REL))


if __name__ == "__main__":
    unittest.main()
