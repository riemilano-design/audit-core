# -*- coding: utf-8 -*-
"""結果の門: 封 docs/XBRL_PLAN_SOURCE_SEAL_2026-11-17.md(a080ce5f・追記 5b38862e・3e8a722d)と読みの軸の封 docs/XBRL_PLAN_SOURCE_READ_AXES_SEAL_2026-11-17.md(06d7b8a7)の結果の文書。

封の門 ``test_xbrl_plan_source_seal.py`` の次の段。**追跡されている記録・script・封・結果の文書だけを読む**(材料は読まない。数秒で終わる)。

縛るもの(検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表で 1 本ずつ。木の file は変異させず、``Ctx`` の写しに当てる)
 a script・states の記録・read_types の記録の sha256(字で留める)
 b 記録の中の整合: states の集計が行からの数え直しと一致(4 通りの読みの全部)・読みの軸の記録(read_types)の不変(行が 109・組 60/30/19・集計が行からの数え直しと一致・
   字が封 §2-3 の決め方と一致・states の sha256 と一致・key_leaks)
 c 結果の文書の数: 表の行も散文の行も、記録から組んだ 1 行と字で同じ(1 行ずつ。文書の行が 1 回ずつ在る)。そのどれにも当たらない行の 2 桁以上の数は、組んだ行の数の集合に在るものだけ
 d 予測 PS-1〜PS-7 と RA-1〜RA-4 の結果の欄と判定を、封の予測の字から取った境と記録の数から門が自分で判定し直して、文書の表と同じ・字で留めた判定と同じ
   (PS は 4 通りの読みで判定が割れたら「割れ」・PS-6 は封のとおりには測っていない)
 e 文書に「証明した」「ハルシネーション」・会社名らしい字・3 桁以上の漢数字が無い・要点の字が在る
 f 封 2 本が commit から 1 字も変わっていない・順序(commit の順。未 commit は赤)・engine 0 行
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
from fractions import Fraction

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


SG = load_module("tests/measure/test_xbrl_plan_source_seal.py", "ps_seal_gate_for_ps_result_gate")      # 封の門の部品。門としては走らせない
PR = SG.PR

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
AXES_SEAL_REL = SG.AXES_SEAL_REL
AXES_SEAL_COMMIT_SHORT = SG.AXES_SEAL_COMMIT_SHORT
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
STATES_REL = SG.RECORD_REL
TYPES_REL = SG.TYPES_REL
GATE_REL = "tests/measure/test_xbrl_plan_source_result.py"
DOC_REL = "docs/XBRL_PLAN_SOURCE_RESULT_2026-11-17.md"
IMPL_COMMIT = "e023e3b4"                                     # 最初の script・封の門・states の記録を足した commit(この後の変更は sha256 で留める)

SHA_PIN = collections.OrderedDict([
    (STATES_REL, "d007b1454c0b4c6f30b3627d54221376767d0f0a1233578dbd37bcfe2df51424"),
    (TYPES_REL, "c244d1bf51e7867e1772f98bd6d4c0085fa816faf1ec09f7855050aa99fe5e56"),
    (SCRIPT_REL, "0617d75a98e9aca390426b2751bed5ae40a8aa8759b3e80bffab163e1abeb8ea")])

# ---- 4 通りの読み(記録の集計の塊の順。行の札の列の番号は封の門の ``RD_IDX``)
RN = (u"字のとおり × そのまま(主)", u"円の族 × そのまま(封 §7。あと知恵)", u"字のとおり × 空の欄を除く(封 §8。あと知恵)", u"円の族 × 空の欄を除く(封 §7・§8。あと知恵)")
RD_IDX = SG.RD_IDX                     # (当てない, F が空, 自, 実, 他)
C_FAM, C_NOSCALE, C_SET, C_BOOK = 4, 14, 3, 0
GROUPS = (u"甲", u"乙", u"丙")
FAMS = (u"円", u"%", u"他")
SETS_TYPES = (u"甲組", u"乙組", u"W組")
ATTRS = (u"項目", u"期", u"範囲", u"予想の種類", u"1 株あたり")

PS_IDS = (u"PS-1", u"PS-2", u"PS-3", u"PS-4", u"PS-5", u"PS-6", u"PS-7")
RA_IDS = (u"RA-1", u"RA-2", u"RA-3", u"RA-4")
PS_CELLS = collections.OrderedDict([
    (u"PS-1", u"P の主の率(自 / 行の全部)は 20% 以上 50% 以下"), (u"PS-2", u"P の他の率は 5% 以下で、自は他の 5 倍以上"),
    (u"PS-3", u"P の実の率は自の率より低い"), (u"PS-4", u"W の自は 20 行のうち 6 以上 14 以下"),
    (u"PS-5", u"N の自の率は P の主の率の半分以下"), (u"PS-6", u"読んだ行のうち あ が 70% 以上"),
    (u"PS-7", u"P の行を持つ本のうち、自の行を持つ本は 40% 以上")])
RA_CELLS = collections.OrderedDict([
    (u"RA-1", u"甲組で値の軸の 3 は 3 行以下"), (u"RA-2", u"甲組で身元に 違 が在る行のうちいちばん多い属性は「期」(同数なら外れ)"),
    (u"RA-3", u"甲組で「1 株あたり」が 違 の行は 2 行以下"), (u"RA-4", u"甲組で値の軸の 2 は 6 行以下")])
HIT, MISS, SPLIT, NOT_MEASURED = u"当たり", u"外れ", u"**割れ**", u"測っていない"
PS_VERDICT_PINNED = (SPLIT, HIT, HIT, SPLIT, HIT, NOT_MEASURED, SPLIT)
PS_MAIN_PINNED = (HIT, HIT, HIT, MISS, HIT, None, MISS)
RA_VERDICT_PINNED = (HIT, HIT, HIT, HIT)

READ_BASIS = (
    u"- 期: 文が年度を名指す(「2027年3月期」など)か「次期」「翌事業年度」「次期連結会計年度」と書いていれば、翌期の fact に 合。年度の字も「次期」も無い文(「通期」だけの文を含む)は 不。中間の累計と名指した文が中間の予想の fact に当たれば 合。",
    u"- 範囲: 封のとおり(手がかりが無く fact が連結なら 合・単体の fact なら 不)。配当の fact は全部が単体の member だったので、配当の行は 不 になる。",
    u"- 同じ値の fact が 2 つ以上当たった行は、違 がいちばん少ない fact を選び、同数なら紙に先に出るほう。",
    u"- 予想の種類: 幅で書いた文が上限・下限の fact に当たれば 合。見出しだけの行(予想とも読めない)は 不。",
    u"- 値の軸の 2 と、身元の 違 は、甲組の同じ 1 行(複数年の計画の期間についての方針の率が、翌期 1 年の予想の率の fact に帯の中で当たった行。期を 違 とした。方針の数を「予想」と数えるかは封の属性の外なので 予想の種類 は 合 のまま)。")

FORBIDDEN_WORDS = (u"証明" + u"した", u"ハルシ" + u"ネーション", u"精" + u"度", u"世界で 1 " + u"社")
COMPANY_WORDS = (u"株式会社", u"有限会社", u"合同会社", u"㈱", u"(株)")
DOCID_RE = re.compile(r"S100[0-9A-Z]{4}")
POINTER_RE = re.compile(r"xbrl:|jppfs|jpcrp|jpdei|_cor:|@(Current|Prior)|formula:")
KANJI_NUM_RE = re.compile(u"[二三四五六七八九]百|[一二三四五六七八九]千|百[一二三四五六七八九十]|千[一二三四五六七八九百]")
HUMAN_EYE_RE = re.compile(u"人の" + u"目")
REQUIRED_PHRASES = (u"AI の席 1 席", u"人は読んでいない", u"盲検でな", u"あと知恵", u"測っていない", u"割れ", u"外れ", u"言えないこと", u"人間の決定", u"限界", u"直していない",
                    u"壊れた fact", u"線が広すぎた")


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


def ratio_text(a, b):
    return u"他は 0" if b == 0 else u"%d.%d" % divmod((a * 20 + b) // (2 * b), 10)


class Ctx(object):
    u"""記録・封・文書・字の写し。変異は毎回 ``Ctx()`` の新しい写しに 1 か所だけ加える。"""

    def __init__(self):
        self.st = json.loads(read(STATES_REL), object_pairs_hook=collections.OrderedDict)
        self.ty = json.loads(read(TYPES_REL), object_pairs_hook=collections.OrderedDict)
        self.seal = read(SEAL_REL)
        self.axes = read(AXES_SEAL_REL)
        self.doc = read(DOC_REL)
        self.texts = collections.OrderedDict((rel, read_bytes(rel)) for rel in SHA_PIN)


_GRP = []


def grp_map():
    if not _GRP:
        _GRP.append(SG.group_map())
    return _GRP[0]


# ======================================================================================================
# 行からの数え直し(門の側で独立に)
def p_rows(c):
    return [r for r in c.st[u"行"] if r[C_SET] == u"P"]


def w_rows(c):
    return [r for r in c.st[u"行"] if r[C_SET] == u"W"]


def pc(rows, ri, group=None, fam=None):
    u"""P の行(rows)を読み ri で数える。{n, na, ns(scale が無い), s, re, ot, fe, applied, books, books_s, top}。"""
    iNA, iFE, iS, iR, iO = RD_IDX[ri]
    g = grp_map()
    sel = [r for r in rows if (group is None or g[r[C_BOOK]] == group) and (fam is None or r[C_FAM] == fam)]
    per_s = collections.Counter(r[C_BOOK] for r in sel if r[iS])
    return {u"n": len(sel), u"na": sum(1 for r in sel if r[iNA]), u"ns": sum(1 for r in sel if r[C_NOSCALE]), u"s": sum(1 for r in sel if r[iS]),
            u"re": sum(1 for r in sel if r[iR]), u"ot": sum(1 for r in sel if r[iO]), u"fe": sum(1 for r in sel if r[iFE]),
            u"applied": sum(1 for r in sel if not r[iNA] and not r[iFE]), u"books": len(set(r[C_BOOK] for r in sel)), u"books_s": len(per_s),
            u"top": max(per_s.values()) if per_s else 0}


def wc(rows, ri):
    iNA, _iFE, iS, iR, iO = RD_IDX[ri]
    return {u"n": len(rows), u"na": sum(1 for r in rows if r[iNA]), u"s": sum(1 for r in rows if r[iS]), u"re": sum(1 for r in rows if r[iR]), u"ot": sum(1 for r in rows if r[iO])}


def labels_of(c):
    return list(c.st[u"集計"])


def n_of(c, ri):
    return c.st[u"集計"][labels_of(c)[ri]][u"全体"][u"N"]


# ======================================================================================================
# a. sha256
def sha_problems(texts, pin=None):
    pin = SHA_PIN if pin is None else pin
    return [u"sha256: %s が字で留めた値と違う" % rel for rel, want in pin.items() if hashlib.sha256(texts.get(rel, b"")).hexdigest() != want]


# ======================================================================================================
# b. 記録の中の整合
def states_problems(c):
    u"""states の集計(4 通りの読み・全体・群)が行からの数え直しと一致。F・R の数の整合。作り直しの確認。"""
    out = []
    rows_p, rows_w = p_rows(c), w_rows(c)
    labs = labels_of(c)
    if len(labs) != 4 or len(rows_p) != 794 or len(rows_w) != 20 or c.st[u"P の行の数"] != 794 or c.st[u"W の行の数"] != 20:
        return [u"states: 読みが 4 通り・P が 794 行・W が 20 行でない"]
    for ri, lab in enumerate(labs):
        sect = c.st[u"集計"][lab]
        for gname, blk in [(None, sect[u"全体"])] + [(g, sect[u"群"][g]) for g in GROUPS]:
            w = pc(rows_p, ri, gname)
            p = blk[u"P"]
            got = {u"n": p[u"行"], u"na": p[u"当てない"], u"ns": p[u"うち scale が無い行"], u"s": p[u"自"], u"re": p[u"実"], u"ot": p[u"他"], u"fe": p[u"F が空の本の行"],
                   u"applied": p[u"当てた行で F が空でない本のもの"], u"books": p[u"本"][u"P の行を持つ本"], u"books_s": p[u"本"][u"自の行を持つ本"], u"top": p[u"本"][u"いちばん多い 1 本が持つ自の行の数"]}
            if got != w:
                out.append(u"states: P の集計が行の数え直しと違う: 読み %d %s" % (ri, gname))
            if p[u"主の率(自 / 行の全部)"][u"率"] != rate_text(w[u"s"], w[u"n"]) or p[u"並べる率(自 / 当てた行で F が空でない本のもの)"][u"率"] != rate_text(w[u"s"], w[u"applied"]):
                out.append(u"states: 率の字が分子・分母から出る字と違う: 読み %d %s" % (ri, gname))
            for fam in FAMS:
                wf = pc(rows_p, ri, gname, fam)
                pf = p[u"単位別"][fam]
                if (pf[u"行"], pf[u"自"], pf[u"当てない"], pf[u"他"], pf[u"実"]) != (wf[u"n"], wf[u"s"], wf[u"na"], wf[u"ot"], wf[u"re"]):
                    out.append(u"states: 単位別の数が行の数え直しと違う: 読み %d %s %s" % (ri, gname, fam))
            ww = wc([r for r in rows_w if gname is None or grp_map()[r[C_BOOK]] == gname], ri)
            wr = blk[u"W"]
            if (wr[u"行"], wr[u"当てない"], wr[u"自"], wr[u"実"], wr[u"他"]) != (ww[u"n"], ww[u"na"], ww[u"s"], ww[u"re"], ww[u"ot"]):
                out.append(u"states: W の集計が行の数え直しと違う: 読み %d %s" % (ri, gname))
    nrows = set(c.st[u"集計"][l][u"全体"][u"N"][u"行"] for l in labs)
    if len(nrows) != 1:
        out.append(u"states: N の行の数が読みで違う")
    for ri in range(4):
        n = n_of(c, ri)
        if n[u"自の率(自 / 行の全部)"][u"率"] != rate_text(n[u"自"], n[u"行"]) or n[u"他の率(他 / 行の全部)"][u"率"] != rate_text(n[u"他"], n[u"行"]):
            out.append(u"states: N の率の字が違う: 読み %d" % ri)
    fs = c.st[u"サマリーの fact"]
    nn = [v for k, v in fs.items() if k.startswith(u"空の欄を除く読み(")]
    sc = [v for k, v in fs.items() if k.startswith(u"自己閉じの tag から始まる読み取り")]
    if len(nn) != 1 or len(sc) != 1:
        return out + [u"states: サマリーの fact の欄に空の欄を除く読み・自己閉じの数が無い"]
    for name, d in ((u"そのまま", fs), (u"空の欄を除く", nn[0])):
        if sum(d[u"F の単位別の数"].values()) != d[u"F の fact の数の合計"] or sum(d[u"R の単位別の数"].values()) != d[u"R の fact の数の合計"]:
            out.append(u"states: F・R の単位別の和が合計と違う: %s" % name)
        if sum(d[u"F が空の本の数の群別"].values()) != d[u"F が空の本の数(切れた本のうち)"]:
            out.append(u"states: F が空の本の群別の和が違う: %s" % name)
    if c.st[u"作り直しの確認"][u"本"] != 400 or fs[u"切れた本"] > 400:
        out.append(u"states: 本の数が決めと違う")
    return out


def types_problems(c):
    items = SG.MS.sample_items(c.st)
    sha = hashlib.sha256(c.texts[STATES_REL]).hexdigest() if STATES_REL in c.texts else u""
    text = json.dumps(c.ty, ensure_ascii=False)
    out = list(SG.types_rec_problems(c.ty, text, sha, items))
    st_rows = c.st[u"行"]
    rule = c.ty[u"標本の規則"]
    kou = sum(1 for r in st_rows if r[C_SET] == u"P" and r[RD_IDX[2][2]])
    otsu = sum(1 for r in st_rows if r[C_SET] == u"P" and r[RD_IDX[3][2]] and not r[RD_IDX[2][2]])
    wn = sum(1 for r in st_rows if r[C_SET] == u"W" and r[RD_IDX[3][2]])
    if (rule[u"甲組の行の数"], rule[u"乙組の行の数"], rule[u"W組の行の数"]) != (kou, otsu, wn):
        out.append(u"types: 標本の母の行の数が states の行の数え直しと違う")
    if (rule[u"甲組の標本の数"], rule[u"乙組の標本の数"], rule[u"W組の標本の数"]) != (min(60, kou), min(30, otsu), wn):
        out.append(u"types: 標本の数が封の決めと違う")
    return out


def record_problems(c):
    return states_problems(c) + types_problems(c)


# ======================================================================================================
# d. 予測の判定
def seal_row(seal, pid):
    sec = seal[seal.index(u"## §4"):]
    m = re.search(r"^\| %s \| (.*?) \| .*? \|$" % re.escape(pid), sec, re.M)
    return m.group(1) if m else u""


def ps_bounds(seal):
    u"""封 §4 の予測の字から境の数を取る。"""
    r = dict((p, seal_row(seal, p)) for p in PS_IDS)
    out = {}
    m = re.search(r"\*\*(\d+)% 以上 (\d+)% 以下\*\*", r[u"PS-1"])
    out[u"PS-1"] = (int(m.group(1)), int(m.group(2)))
    m = re.search(r"\*\*(\d+)% 以下\*\*.*?\*\*(\d+) 倍以上\*\*", r[u"PS-2"])
    out[u"PS-2"] = (int(m.group(1)), int(m.group(2)))
    m = re.search(r"\*\*(\d+) 行のうち (\d+) 以上 (\d+) 以下\*\*", r[u"PS-4"])
    out[u"PS-4"] = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    out[u"PS-5"] = (2 if u"半分以下" in r[u"PS-5"] else 0,)
    m = re.search(r"(\d+)% 以上", r[u"PS-6"])
    out[u"PS-6"] = (int(m.group(1)),)
    m = re.search(r"本 (\d+) のうち、自の行を持つ本は \*\*(\d+)% 以上\*\*", r[u"PS-7"])
    out[u"PS-7"] = (int(m.group(1)), int(m.group(2)))
    return out


def ra_bounds(axes):
    sec = axes[axes.index(u"## §4"):]
    rows = collections.OrderedDict((m.group(1), m.group(2)) for m in re.finditer(r"^\| (RA-\d) \| (.*?) \| .*? \|$", sec, re.M))
    out = {}
    out[u"RA-1"] = (int(re.search(r"\*\*3 は (\d+) 行以下\*\*", rows[u"RA-1"]).group(1)),)
    out[u"RA-3"] = (int(re.search(r"\*\*「1 株あたり」が 違 の行は (\d+) 行以下\*\*", rows[u"RA-3"]).group(1)),)
    out[u"RA-4"] = (int(re.search(r"\*\*値の軸の 2 は (\d+) 行以下\*\*", rows[u"RA-4"]).group(1)),)
    return out


def ps_judge(c):
    u"""[(id, 主の結果の字, 4 通りの結果の字, 主の判定, 4 通りの判定の並び)]。境は封の字から、数は記録の行から。PS-6 は測っていない。"""
    bd = ps_bounds(c.seal)
    rows_p, rows_w = p_rows(c), w_rows(c)
    P = [pc(rows_p, ri) for ri in range(4)]
    W = [wc(rows_w, ri) for ri in range(4)]
    N = [n_of(c, ri) for ri in range(4)]
    out = []
    lo, hi = bd[u"PS-1"]
    out.append((u"PS-1", [rate_text(p[u"s"], p[u"n"]) for p in P], [Fraction(lo, 100) <= Fraction(p[u"s"], p[u"n"]) <= Fraction(hi, 100) for p in P]))
    lim, times = bd[u"PS-2"]
    out.append((u"PS-2", [u"%s(%s 倍)" % (rate_text(p[u"ot"], p[u"n"]), ratio_text(p[u"s"], p[u"ot"])) for p in P],
                [Fraction(p[u"ot"], p[u"n"]) * 100 <= lim and p[u"s"] >= times * p[u"ot"] for p in P]))
    out.append((u"PS-3", [u"実 %s 対 自 %s" % (rate_text(p[u"re"], p[u"n"]), rate_text(p[u"s"], p[u"n"])) for p in P], [p[u"re"] < p[u"s"] for p in P]))
    wn, wlo, whi = bd[u"PS-4"]
    out.append((u"PS-4", [u"%d/%d" % (w[u"s"], wn) for w in W], [w[u"n"] == wn and wlo <= w[u"s"] <= whi for w in W]))
    out.append((u"PS-5", [u"N の自 %s 対 P の主 %s" % (rate_text(n[u"自"], n[u"行"]), rate_text(p[u"s"], p[u"n"])) for n, p in zip(N, P)],
                [Fraction(n[u"自"], n[u"行"]) * bd[u"PS-5"][0] <= Fraction(p[u"s"], p[u"n"]) for n, p in zip(N, P)]))
    out.append((u"PS-6", None, None))
    books_all, pct_lim = bd[u"PS-7"]
    out.append((u"PS-7", [frac(p[u"books_s"], p[u"books"]) for p in P], [p[u"books"] == books_all and p[u"books_s"] * 100 >= pct_lim * p[u"books"] for p in P]))
    return out


def verdict_of(oks):
    u"""4 通りが全部同じならその判定、割れたら 割れ。PS-6 は None。"""
    if oks is None:
        return NOT_MEASURED, None
    main = HIT if oks[0] else MISS
    return (main if len(set(oks)) == 1 else SPLIT), main


def ra_judge(c):
    u"""[(id, 結果の字, 当たりか)]。境は読みの軸の封の字から、数は read_types の行から。"""
    bd = ra_bounds(c.axes)
    rows = [r for r in c.ty[u"行"] if r[4] == u"甲組"]
    ax3 = sum(1 for r in rows if r[5] == 3)
    ax2 = sum(1 for r in rows if r[5] == 2)
    d = [r for r in rows if u"違" in r[6]]
    by = [sum(1 for r in d if r[6][i] == u"違") for i in range(5)]
    top = max(by)
    sole_top = [ATTRS[i] for i in range(5) if by[i] == top]
    one = sum(1 for r in rows if r[6][4] == u"違")
    out = [(u"RA-1", u"%d 行" % ax3, ax3 <= bd[u"RA-1"][0]),
           (u"RA-2", u"違 の在る行 %d 行・いちばん多い属性 %s %d" % (len(d), u"・".join(sole_top), top), len(d) > 0 and sole_top == [u"期"]),
           (u"RA-3", u"%d 行" % one, one <= bd[u"RA-3"][0]),
           (u"RA-4", u"%d 行" % ax2, ax2 <= bd[u"RA-4"][0])]
    return out


def judge_problems(c):
    out = []
    for pid in PS_IDS:
        if not seal_row(c.seal, pid):
            return [u"judge: 封 §4 に %s の行が無い" % pid]
    if tuple(ps_bounds(c.seal).items()) != (
            (u"PS-1", (20, 50)), (u"PS-2", (5, 5)), (u"PS-4", (20, 6, 14)), (u"PS-5", (2,)), (u"PS-6", (70,)), (u"PS-7", (176, 40))):
        out.append(u"judge: 封の PS の予測の境が字で留めた値と違う")
    if tuple(ra_bounds(c.axes).items()) != ((u"RA-1", (3,)), (u"RA-3", (2,)), (u"RA-4", (6,))):
        out.append(u"judge: 読みの軸の封の RA の予測の境が字で留めた値と違う")
    for pid in PS_IDS:
        if not seal_row(c.seal, pid):
            return out + [u"judge: 封 §4 に %s の行が無い" % pid]
    ps = ps_judge(c)
    vs = [verdict_of(oks) for _i, _t, oks in ps]
    if tuple(v for v, _m in vs) != PS_VERDICT_PINNED or tuple(m for _v, m in vs) != PS_MAIN_PINNED:
        out.append(u"judge: PS の判定が字で留めた「割れ 3・当たり 3・測っていない 1」と違う")
    ra = ra_judge(c)
    if tuple(HIT if ok else MISS for _i, _t, ok in ra) != RA_VERDICT_PINNED:
        out.append(u"judge: RA の判定が字で留めた「当たり 4」と違う")
    lines = c.doc.split(u"\n")
    for line in ps_table_lines(c):
        if lines.count(line) != 1:
            out.append(u"judge: 文書の PS の予測の表の行が門の判定し直しと違う: %s" % line[:12])
    for line in ra_table_lines(c):
        if lines.count(line) != 1:
            out.append(u"judge: 文書の RA の予測の表の行が門の判定し直しと違う: %s" % line[:12])
    for name, line in read_table_lines(c):
        if lines.count(line) != 1:
            out.append(u"judge: 文書の「予測 × 読み 4 通りの当たり外れ」の表の行が門の判定し直しと違う: %s" % name)
    return out


def ps_table_lines(c):
    out = []
    for (pid, texts, oks) in ps_judge(c):
        v, main = verdict_of(oks)
        if texts is None:
            out.append(u"| %s | %s | 測っていない(封 §8 の 5。引き直した標本での あ の率は下の表) | ― | %s |" % (pid, PS_CELLS[pid], NOT_MEASURED))
        else:
            out.append(u"| %s | %s | %s(%s) | %s | %s |" % (pid, PS_CELLS[pid], texts[0], HIT if oks[0] else MISS, u"・".join(texts), v))
    return out


READ_TABLE_INTRO = u"予測ごと × 読み 4 通りの当たり外れ(封の境と記録から結果の門が決めた。PS-6 は測っていない):"
READ_TABLE_HEADER = u"| # | 字のとおり × そのまま(主) | 円の族 × そのまま | 字のとおり × 空の欄を除く | 円の族 × 空の欄を除く |"


def read_table_lines(c):
    u"""予測 × 読み 4 通りの当たり外れの表(PS-6 は除く)。当たり外れは封の境と記録の行から門が決める。[(名前, 行)]"""
    out = [(u"rt intro", READ_TABLE_INTRO), (u"rt header", READ_TABLE_HEADER)]
    for (pid, _t, oks) in ps_judge(c):
        if oks is not None:
            out.append((u"rt %s" % pid, u"| %s | %s |" % (pid, u" | ".join(HIT if ok else MISS for ok in oks))))
    return out


def ra_table_lines(c):
    return [u"| %s | %s | %s | %s |" % (i, RA_CELLS[i], t, HIT if ok else MISS) for i, t, ok in ra_judge(c)]


# ======================================================================================================
# c. 文書の行
def cond(ok, text):
    return text if ok else u"【条件が合わない】" + text


def types_counts(c):
    u"""read_types の行から組ごとに数え直す(記録の集計は使わない)。{組: {...}}。"""
    res = collections.OrderedDict()
    for g in SETS_TYPES:
        rows = [r for r in c.ty[u"行"] if r[4] == g]
        d = [r for r in rows if u"違" in r[6]]
        d12 = [r for r in d if r[5] in (1, 2)]
        res[g] = {u"n": len(rows), u"ax": [sum(1 for r in rows if r[5] == a) for a in (1, 2, 3, 4)],
                  u"at": dict((ATTRS[i], [sum(1 for r in rows if r[6][i] == ch) for ch in u"合違不"]) for i in range(5)),
                  u"lt": [sum(1 for r in rows if r[7] == ch) for ch in u"あいう"],
                  u"cross": [[sum(1 for r in rows if r[5] == a and r[7] == ch) for ch in u"あいう"] for a in (1, 2, 3, 4)],
                  u"d": [len(d)] + [sum(1 for r in d if r[6][i] == u"違") for i in range(5)],
                  u"d12": [len(d12)] + [sum(1 for r in d12 if r[6][i] == u"違") for i in range(5)]}
    return res


def expected_lines(c):
    u"""結果の文書の数を持つ行を、記録から 1 行ずつ組む。[(名前, 行)]。"""
    E = []
    rows_p, rows_w = p_rows(c), w_rows(c)
    P = [pc(rows_p, ri) for ri in range(4)]
    n794 = P[0][u"n"]
    fs = c.st[u"サマリーの fact"]
    nn = [v for k, v in fs.items() if k.startswith(u"空の欄を除く読み(")][0]
    sc = [v for k, v in fs.items() if k.startswith(u"自己閉じの tag から始まる読み取り")][0]
    E.append((u"材料", u"- 材料は TSS の置き場の ZIP %d 本(切れた本 %d・数の claim の合計 %d)。P は %d 行・W は %d 行。" % (
        c.st[u"作り直しの確認"][u"本"], fs[u"切れた本"], c.st[u"作り直しの確認"][u"数の claim の合計"], n794, len(rows_w))))
    # §1 の表
    E.append((u"t1 header", u"| 読み | 当てない | うち scale が無い | 自 | 実 | 他 | 主の率(自 / 行の全部) | 並べる率(自 / 当てた行で F が空でない本のもの) | 実の率 | 他の率 | 自 ÷ 他 |"))
    for ri in range(4):
        p = P[ri]
        E.append((u"t1 %d" % ri, u"| %s | %d | %d | %d | %d | %d | %s | %s | %s | %s | %s |" % (
            RN[ri], p[u"na"], p[u"ns"], p[u"s"], p[u"re"], p[u"ot"], frac(p[u"s"], p[u"n"]), frac(p[u"s"], p[u"applied"]), frac(p[u"re"], p[u"n"]), frac(p[u"ot"], p[u"n"]),
            ratio_text(p[u"s"], p[u"ot"]))))
    gn = [pc(rows_p, 0, g)[u"n"] for g in GROUPS]
    E.append((u"t2 header", u"| 読み | 甲(%d 行) | 乙(%d 行) | 丙(%d 行) |" % tuple(gn)))
    for ri in range(4):
        E.append((u"t2 %d" % ri, u"| %s | %s |" % (RN[ri], u" | ".join(frac(pc(rows_p, ri, g)[u"s"], pc(rows_p, ri, g)[u"n"]) for g in GROUPS))))
    fnn = [pc(rows_p, 0, None, f)[u"n"] for f in FAMS]
    E.append((u"t3 header", u"| 読み | 円(%d 行) | %%(%d 行) | 他(%d 行) |" % tuple(fnn)))
    for ri in range(4):
        E.append((u"t3 %d" % ri, u"| %s | %s |" % (RN[ri], u" | ".join(frac(pc(rows_p, ri, None, f)[u"s"], pc(rows_p, ri, None, f)[u"n"]) for f in FAMS))))
    E.append((u"t4 header", u"| 読み | 自の行を持つ本(P の行を持つ本のうち) | いちばん多い 1 本が持つ自の行の数 |"))
    for ri in range(4):
        E.append((u"t4 %d" % ri, u"| %s | %s | %d |" % (RN[ri], frac(P[ri][u"books_s"], P[ri][u"books"]), P[ri][u"top"])))
    E.append((u"t5 header", u"| 読み | W の行 | 当てない | 自 | 実 | 他 |"))
    for ri in range(4):
        w = wc(rows_w, ri)
        E.append((u"t5 %d" % ri, u"| %s | %d | %d | %d | %d | %d |" % (RN[ri], w[u"n"], w[u"na"], w[u"s"], w[u"re"], w[u"ot"])))
    E.append((u"t6 header", u"| 読み | N の行 | 当てない | 自 | 他 | 自の率 | 他の率 |"))
    for ri in range(4):
        n = n_of(c, ri)
        E.append((u"t6 %d" % ri, u"| %s | %d | %d | %d | %d | %s | %s |" % (RN[ri], n[u"行"], n[u"当てない"], n[u"自"], n[u"他"], frac(n[u"自"], n[u"行"]), frac(n[u"他"], n[u"行"]))))
    # 当てない行・丙
    noscale = P[1][u"ns"]
    other_fam = sum(1 for r in rows_p if r[C_FAM] == u"他")
    pct_na = sum(1 for r in rows_p if r[C_FAM] == u"%" and r[RD_IDX[1][0]])
    E.append((u"当てない", cond(noscale + other_fam + pct_na == P[1][u"na"] and P[0][u"na"] >= P[1][u"na"] and all(r[RD_IDX[1][0]] for r in rows_p if r[C_NOSCALE]),
                           u"- 当てない行は、字のとおりの読みで %d、円の族の読みで %d。円の族の読みの %d は、scale が無い %d・単位が円でも %% でもない %d・%% で値が 0 の %d。" % (
                               P[0][u"na"], P[1][u"na"], P[1][u"na"], noscale, other_fam, pct_na))))
    g3 = [r for r in rows_p if grp_map()[r[C_BOOK]] == u"丙"]
    g3_yen = [r for r in g3 if r[C_FAM] == u"円"]
    g3_pct = [r for r in g3 if r[C_FAM] == u"%"]
    g3_oth = [r for r in g3 if r[C_FAM] == u"他"]
    ok3 = (all(r[C_NOSCALE] for r in g3_yen) and all(not r[RD_IDX[ri][0]] for r in g3_pct for ri in range(4)) and all(not r[RD_IDX[ri][2]] for r in g3 for ri in range(4))
           and all(r[RD_IDX[ri][0]] for r in g3_yen + g3_oth for ri in range(4)) and len(g3_yen) + len(g3_pct) + len(g3_oth) == len(g3))
    E.append((u"丙", cond(ok3, u"- 丙の P の行 %d の自は、4 通りの読みの全部で 0。内訳は、scale が無い円の行 %d(当てない・作り)・単位が円でも %% でもない行 %d(当てない・作り)・%% の行 %d(当てたが自は 0。作りではない)。" % (
        len(g3), len(g3_yen), len(g3_oth), len(g3_pct)))))
    E.append((u"サマリー fact", u"- サマリーの fact は、そのままの読みで F %d・R %d、空の欄を除く読みで F %d・R %d。F が空の本(切れた本 %d のうち)は、そのままで %d・空の欄を除いて %d。" % (
        fs[u"F の fact の数の合計"], fs[u"R の fact の数の合計"], nn[u"F の fact の数の合計"], nn[u"R の fact の数の合計"], fs[u"切れた本"], fs[u"F が空の本の数(切れた本のうち)"], nn[u"F が空の本の数(切れた本のうち)"])))
    E.append((u"自己閉じ", u"- 自己閉じの tag から始まる読み取り(engine と同じ正規表現の一致のうち属性の列が / で終わるもの)は、サマリーで %d 個・%d 本、短信の本体(Attachment の側の .htm)で %d 個・%d 本(%d 本のうち)。" % (
        sc[u"サマリー"][u"読み取りの数"], sc[u"サマリー"][u"その読み取りを持つ本"], sc[u"短信の本体(Attachment の側の .htm)"][u"読み取りの数"], sc[u"短信の本体(Attachment の側の .htm)"][u"その読み取りを持つ本"],
        sc[u"サマリー"][u"本"])))
    # 予測
    E.append((u"ps header", u"| # | 予測 | 主の結果(字のとおり × そのまま) | 4 通りの結果(主・円の族・空の欄を除く・円の族 × 空の欄を除く の順) | 判定 |"))
    for line in ps_table_lines(c):
        E.append((u"ps %s" % line.split(u" | ")[0][2:], line))
    vs = [verdict_of(oks) for _i, _t, oks in ps_judge(c)]
    hit_ids = [i for (i, _t, _o), (v, _m) in zip(ps_judge(c), vs) if v == HIT]
    split_ids = [i for (i, _t, _o), (v, _m) in zip(ps_judge(c), vs) if v == SPLIT]
    miss_ids = [i for (i, _t, _o), (v, _m) in zip(ps_judge(c), vs) if v == MISS]
    E.extend(read_table_lines(c))
    E.append((u"ps 当たり割れ", u"- 当たり %d(%s)・割れ %d(%s)・測っていない 1(PS-6)・4 通りとも外れ %d。" % (
        len(hit_ids), u"・".join(hit_ids), len(split_ids), u"・".join(split_ids), len(miss_ids))))
    # 読みの軸
    T = types_counts(c)
    kou, otsu, wn = c.ty[u"標本の規則"][u"甲組の行の数"], c.ty[u"標本の規則"][u"乙組の行の数"], c.ty[u"標本の規則"][u"W組の行の数"]
    E.append((u"標本", u"- 読んだ標本は %d 行。甲組は空の欄を除く読みで字のとおりに「自」が真の P %d 行から 60・乙組は円の族の読みでだけ「自」が真の P %d 行から 30・W 組は円の族の読みで「自」が真の W %d 行の全部。" % (
        sum(t[u"n"] for t in T.values()), kou, otsu, wn)))
    E.append((u"ra1 header", u"| 組 | 読んだ行 | 値の軸 1 | 値の軸 2 | 値の軸 3 | 値の軸 4 |"))
    for g in SETS_TYPES:
        E.append((u"ra1 %s" % g, u"| %s | %d | %s |" % (g, T[g][u"n"], u" | ".join(str(x) for x in T[g][u"ax"]))))
    E.append((u"ra2 header", u"| 組 | 属性 | 合 | 違 | 不 |"))
    for g in SETS_TYPES:
        for a in ATTRS:
            E.append((u"ra2 %s %s" % (g, a), u"| %s | %s | %s |" % (g, a, u" | ".join(str(x) for x in T[g][u"at"][a]))))
    E.append((u"ra3 header", u"| 組 | あ | い | う |"))
    for g in SETS_TYPES:
        E.append((u"ra3 %s" % g, u"| %s | %s |" % (g, u" | ".join(frac(x, T[g][u"n"]) for x in T[g][u"lt"]))))
    E.append((u"ra4 header", u"| 組 | 値の軸 | あ | い | う |"))
    for g in SETS_TYPES:
        for i, a in enumerate((1, 2, 3, 4)):
            E.append((u"ra4 %s %d" % (g, a), u"| %s | %d | %s |" % (g, a, u" | ".join(str(x) for x in T[g][u"cross"][i]))))
    E.append((u"ra5 header", u"| 組 | 身元に 違 が在る行 | 項目 | 期 | 範囲 | 予想の種類 | 1 株あたり |"))
    for g in SETS_TYPES:
        E.append((u"ra5 %s" % g, u"| %s | %s |" % (g, u" | ".join(str(x) for x in T[g][u"d"]))))
    E.append((u"ra6 header", u"| 組 | 値の軸が 1 か 2 で身元に 違 が在る行 | 項目 | 期 | 範囲 | 予想の種類 | 1 株あたり |"))
    for g in SETS_TYPES:
        E.append((u"ra6 %s" % g, u"| %s(値の軸が 1 か 2) | %s |" % (g, u" | ".join(str(x) for x in T[g][u"d12"]))))
    for line in ra_table_lines(c):
        E.append((u"ra %s" % line.split(u" | ")[0][2:], line))
    ra = ra_judge(c)
    E.append((u"ra header", u"| # | 予測(甲組) | 結果 | 判定 |"))
    d_kou = T[u"甲組"][u"d"]
    ax_kou = T[u"甲組"][u"ax"]
    both = d_kou[0] == 1 and T[u"甲組"][u"d12"][0] == 1 and ax_kou[1] == 1 and T[u"甲組"][u"d"][2] == 1
    E.append((u"ra2 1 行", cond(both, u"- RA-2 は、違 の在る行が甲組で %d 行だけで、その 1 行は値の軸が 2 の行(期が 違)。字のうえでは当たりだが 1 行の判断に依る。" % d_kou[0])))
    E.append((u"ra 当たり", cond(all(ok for _i, _t, ok in ra), u"- RA は当たり %d・外れ %d。RA-1・RA-3・RA-4 は、線が広すぎた(甲組の値の軸の 3 は %d 行・「1 株あたり」の 違 は %d 行・値の軸の 2 は %d 行で、どの境にも遠い)。" % (
        sum(1 for _i, _t, ok in ra if ok), sum(1 for _i, _t, ok in ra if not ok), T[u"甲組"][u"ax"][2], T[u"甲組"][u"d"][5], T[u"甲組"][u"ax"][1]))))
    all_a = sum(T[g][u"lt"][0] for g in SETS_TYPES)
    all_n = sum(T[g][u"n"] for g in SETS_TYPES)
    ax3 = sum(T[g][u"ax"][2] for g in SETS_TYPES)
    dtot = sum(T[g][u"d"][0] for g in SETS_TYPES)
    E.append((u"ra 全体", cond(ax3 == 0 and dtot == 1 and T[u"甲組"][u"d"][0] == 1,
                           u"- 値の軸の 3(engine の読み取りの取り違え)は、甲組・乙組・W 組の全部で %d 行。身元に 違 が在る行は、全部の組で %d 行(甲組の期の 違 の 1 行だけ)。" % (ax3, dtot))))
    wu = [r for r in c.ty[u"行"] if r[4] == u"W組" and r[7] == u"う"]
    E.append((u"W う", cond(len(wu) > 0 and all(r[6][1] == u"不" for r in wu) and T[u"W組"][u"lt"][0] * 100 < 70 * T[u"W組"][u"n"],
                         u"- W 組は あ が 70%% に届かず、う の %d 行は全部が期の 不(年度の字も「次期」も無い文)。" % len(wu))))
    E.append((u"PS-6 参考", u"- 参考(PS-6 の当たり外れではない。標本は引き直したもの): あ は、甲組 %s・乙組 %s・W 組 %s・全部で %s。" % (
        frac(T[u"甲組"][u"lt"][0], T[u"甲組"][u"n"]), frac(T[u"乙組"][u"lt"][0], T[u"乙組"][u"n"]), frac(T[u"W組"][u"lt"][0], T[u"W組"][u"n"]), frac(all_a, all_n))))
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
    t = re.sub(r"20\d\d年\d月期", u"", t)
    return t


def table_numbers(c, exp):
    allowed = set()
    for _n, line in exp:
        allowed |= numbers_of(line)
    return allowed


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
    for line in READ_BASIS:
        if lines.count(line) != 1:
            out.append(u"文書: 読みの基準の行が 1 回ずつ無い: %s" % line[:14])
    expset = set(l for _n, l in exp) | set(READ_BASIS)
    allowed = table_numbers(c, exp)
    for ln, line in enumerate(lines, 1):
        if line in expset:
            continue
        bad = sorted(numbers_of(prose_clean(line)) - allowed)
        if bad:
            out.append(u"文書: 組んだ行の外の数が記録から作った数の集合に無い: 行 %d %s" % (ln, u",".join(bad)))
    out += words_problems(c)
    return out


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
    for need in (os.path.basename(SEAL_REL), os.path.basename(AXES_SEAL_REL), SEAL_COMMIT_SHORT, SG.ADDENDUM_COMMIT_SHORT, SG.ADDENDUM8_COMMIT_SHORT, AXES_SEAL_COMMIT_SHORT, IMPL_COMMIT,
                 os.path.basename(SCRIPT_REL), os.path.basename(STATES_REL), os.path.basename(TYPES_REL)) + REQUIRED_PHRASES:
        if need not in doc:
            out.append(u"words: 要点の字が無い: %s" % need)
    return out


# 要点の文(負けと限界)。文書の決まった節に 1 回ずつ在ること
LEAD_HEAD = u"**先に負けと限界を書く。**"
LEAD_NEXT = u"## §1 "
LIMIT_HEAD = u"## §7 "
LEAD_MAIN_LINE = u"- **主の数(字のとおり × そのまま。封の字のとおりの数)は、「同じ短信のサマリーの予想の fact に当たった率」としては読めない。engine の読み取りが壊した fact に当てた数である。** 4 通りの読みを 1 つの表(§1)に並べた。主以外の 3 つは「封の後に足した読み(あと知恵)」で、そう書いて添える。"
LEAD_ENGINE_LINE = u"- engine は動かしていない。サマリーの fact を engine に渡したときに結べるかは測っていない。"
LIMIT_ENGINE_LINE = u"2. engine は動かしていない。サマリーの予想の context を期として扱えるか・実績の行の結びを壊さないかは測っていない。"


def section(doc, head, nxt=None):
    if head not in doc:
        return u""
    t = doc[doc.index(head):]
    if nxt is not None and nxt in t[len(head):]:
        t = t[:len(head) + t[len(head):].index(nxt)]
    return t


def limits_problems(c):
    u"""「主の数は壊れた fact に当てた数」の文と「engine は動かしていない」の行が、文書の負けと限界の節・限界の節に 1 回ずつ在る。"""
    out = []
    lead = section(c.doc, LEAD_HEAD, LEAD_NEXT).split(u"\n")
    lim = section(c.doc, LIMIT_HEAD).split(u"\n")
    for name, line, where in ((u"主の数の文", LEAD_MAIN_LINE, lead), (u"engine は動かしていない(負けと限界)", LEAD_ENGINE_LINE, lead), (u"engine は動かしていない(限界)", LIMIT_ENGINE_LINE, lim)):
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
    u"""封の本体は最初の追記 §8 の commit の byte のまま(追記の履歴は封の門が縛る)・読みの軸の封は 06d7b8a7 の byte のまま。"""
    return frozen_problems(c.seal, SG.ADDENDUM8_COMMIT_SHORT, SEAL_REL) + frozen_problems(c.axes, AXES_SEAL_COMMIT_SHORT, AXES_SEAL_REL)


def seal_text_problems(c):
    u"""封に文書が根にする字が在る。"""
    out = []
    for need in (u"**20% 以上 50% 以下**", u"**5% 以下**", u"**5 倍以上**", u"**20 行のうち 6 以上 14 以下**", u"半分以下", u"**40% 以上**", u"本 176 のうち"):
        if need not in c.seal:
            out.append(u"seal: 封に %s が無い" % need)
    for need in (u"**3 は 3 行以下**", u"**値の軸の 2 は 6 行以下**", u"違 の行は 2 行以下**", u"## §4 予測", u"期"):
        if need not in c.axes:
            out.append(u"axes: 読みの軸の封に %s が無い" % need)
    return out


def order_others():
    return [STATES_REL, TYPES_REL, SEAL_GATE_REL, DOC_REL, GATE_REL]


def order_problems_real(root=REPO):
    u"""最初の封 ⊏ script ⊑ 記録・封の門・結果の文書・この門。読みの軸の封 ⊏ read_types・結果の文書・この門(未 commit は赤)。"""
    return (PR.order_problems(root, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, [SCRIPT_REL], order_others())
            + PR.order_problems(root, PREFIX, AXES_SEAL_REL, AXES_SEAL_COMMIT_SHORT, [], [TYPES_REL, DOC_REL, GATE_REL]))


def engine_problems(root=REPO):
    u"""engine・lib・入力は最初の封の commit から 0 行(未 commit も)。"""
    return list(SG.engine_since_seal_problems(root)) + list(SG.engine_worktree_problems(root))


# ======================================================================================================
# 変異の表(1 行 = 1 つの検査を赤にする 1 か所の変異。木の file は変異させず、Ctx の写しを変える)
CHECKS = collections.OrderedDict([
    (u"sha", lambda c: sha_problems(c.texts)),
    (u"states", states_problems),
    (u"types", types_problems),
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


def seal_replace(old, new, every=False):
    def fn(c):
        assert old in c.seal, old
        c.seal = c.seal.replace(old, new) if every else c.seal.replace(old, new, 1)
    return fn


def axes_replace(old, new):
    def fn(c):
        assert old in c.axes, old
        c.axes = c.axes.replace(old, new, 1)
    return fn


def doc_append(text):
    return lambda c: setattr(c, "doc", c.doc + text)


def set_text(rel, fn):
    return lambda c: c.texts.__setitem__(rel, fn(c.texts[rel]))


def st_row(i, col, value):
    def fn(c):
        c.st[u"行"][i][col] = value
    return fn


def ty_row(i, col, value):
    def fn(c):
        c.ty[u"行"][i][col] = value
    return fn


def first_row(c, pred, rows_key=u"行", store=None):
    rows = (store or c.st)[rows_key]
    return next(i for i, r in enumerate(rows) if pred(r))


def mut_flip_st(col, pred, label_set=None):
    u"""states の行の札を 1 つ反転する(最初に当たる行)。"""
    def fn(c):
        i = first_row(c, pred)
        c.st[u"行"][i][col] = not c.st[u"行"][i][col]
    return fn


def mut_ty_value_axis(c):
    i = first_row(c, lambda r: r[4] == u"甲組" and r[5] == 1, store=c.ty)
    c.ty[u"行"][i][5] = 3


def mut_ty_ident(c):
    i = first_row(c, lambda r: r[4] == u"甲組" and r[6] == u"合合合合合", store=c.ty)
    c.ty[u"行"][i][6] = u"合違合合合"                                  # 字(あ)は変えない: 字が身元から決めた字と食い違う


def mut_ty_ident_and_letter(c):
    i = first_row(c, lambda r: r[4] == u"甲組" and r[6] == u"合合合合合", store=c.ty)
    c.ty[u"行"][i][6] = u"合違合合合"
    c.ty[u"行"][i][7] = u"い"                                           # 身元と字は食い違わないが、集計が行の数え直しと違う


def mut_ty_letter(c):
    i = first_row(c, lambda r: r[4] == u"甲組" and r[7] == u"あ", store=c.ty)
    c.ty[u"行"][i][7] = u"う"


def mut_ty_period_to_item(c):
    for r in c.ty[u"行"]:
        if r[4] == u"甲組" and r[6][1] == u"違":
            r[6] = u"違合" + r[6][2:]


def mut_ty_group(c):
    i = first_row(c, lambda r: r[4] == u"甲組", store=c.ty)
    c.ty[u"行"][i][4] = u"乙組"


def mut_ty_drop_row(c):
    c.ty[u"行"].pop()


def mut_ty_sha(c):
    c.ty[u"states の記録の sha256"] = u"0" * 64


def mut_ty_leak(c):
    c.ty[u"行"][0].append(u"売上高")


def mut_ty_keyleaks(c):
    c.ty[u"key_leaks"] = [u"x"]


def mut_ty_agg(c):
    c.ty[u"集計"][u"甲組"][u"値の軸ごとの行の数"][u"2"][u"分子"] = 2


def mut_ty_rate_text(c):
    c.ty[u"集計"][u"甲組"][u"あ・い・う の行の数"][u"あ"][u"率"] = u"90.1%"


def mut_ty_seat(c):
    c.ty[u"型を付けた席"] = u"司令塔"


M(u"a1 states の記録の 1 byte", u"sha", set_text(STATES_REL, lambda t: t + b" "))
M(u"a2 read_types の記録の 1 byte", u"sha", set_text(TYPES_REL, lambda t: t + b" "))
M(u"a3 script の 1 byte", u"sha", set_text(SCRIPT_REL, lambda t: t + b" "))
# b states の整合
M(u"b1 states の P の自(字のとおり)を 1 つ変える", u"states", lambda c: c.st[u"集計"][labels_of(c)[0]][u"全体"][u"P"].__setitem__(u"自", 194))
M(u"b2 states の行の自の札を 1 つ反転する(字のとおり)", u"states", mut_flip_st(7, lambda r: r[3] == u"P" and r[7]))
M(u"b3 states の行の他の札(円の族 × 空の欄を除く)を 1 つ反転する", u"states", mut_flip_st(21, lambda r: r[3] == u"P" and not r[21]))
M(u"b4 states の主の率の字を変える", u"states", lambda c: c.st[u"集計"][labels_of(c)[0]][u"全体"][u"P"][u"主の率(自 / 行の全部)"].__setitem__(u"率", u"24.4%"))
M(u"b5 states の N の自を変える(円の族 × 空の欄を除く)", u"states", lambda c: c.st[u"集計"][labels_of(c)[3]][u"全体"][u"N"].__setitem__(u"自の率(自 / 行の全部)", {u"分子": 21, u"分母": 6634, u"率": u"0.4%"}))
M(u"b6 states の W の自を変える(円の族)", u"states", lambda c: c.st[u"集計"][labels_of(c)[1]][u"全体"][u"W"].__setitem__(u"自", 12))
M(u"b7 states の単位別の自を変える(丙の読み 2)", u"states", lambda c: c.st[u"集計"][labels_of(c)[2]][u"群"][u"乙"][u"P"][u"単位別"][u"%"].__setitem__(u"自", 1))
M(u"b8 states の F の単位別の和を崩す", u"states", lambda c: c.st[u"サマリーの fact"][u"F の単位別の数"].__setitem__(u"JPY", 1))
M(u"b9 states の自の行を持つ本の数を変える", u"states", lambda c: c.st[u"集計"][labels_of(c)[0]][u"全体"][u"P"][u"本"].__setitem__(u"自の行を持つ本", 64))
# b types の整合(read_types の記録の不変)
M(u"b10 read_types の値の軸を 1 つ変える(集計が行の数え直しと違う)", u"types", mut_ty_value_axis)
M(u"b11 read_types の身元を 1 字変える(字が §2-3 の決め方と違う)", u"types", mut_ty_ident)
M(u"b12 read_types の身元と字を変える(集計が行の数え直しと違う)", u"types", mut_ty_ident_and_letter)
M(u"b13 read_types の字を 1 つ変える(字が §2-3 の決め方と違う)", u"types", mut_ty_letter)
M(u"b14 read_types の組を 1 つ変える(行が標本と違う)", u"types", mut_ty_group)
M(u"b15 read_types の行を 1 つ消す(109 行でない)", u"types", mut_ty_drop_row)
M(u"b16 read_types の states の sha256 を変える", u"types", mut_ty_sha)
M(u"b17 read_types の行に文を足す(文や値が在る)", u"types", mut_ty_leak)
M(u"b18 read_types の key_leaks を空でなくする", u"types", mut_ty_keyleaks)
M(u"b19 read_types の集計の値の軸の分子を変える", u"types", mut_ty_agg)
M(u"b20 read_types の率の字を変える", u"types", mut_ty_rate_text)
M(u"b21 read_types の席の字から「人は読んでいない」を落とす", u"types", mut_ty_seat)
M(u"b22 read_types の標本の母の行の数を変える", u"types", lambda c: c.ty[u"標本の規則"].__setitem__(u"甲組の行の数", 311))
# c 文書の行(表の数 1 つ・散文の数 1 つ)
M(u"c1 表 t1 の主の自の数字 1 つ", u"doc", doc_replace(u"| 355 | 168 | 193 | 71 | 8 |", u"| 355 | 168 | 194 | 71 | 8 |"))
M(u"c2 表 t1 の率の字 1 つ", u"doc", doc_replace(u"193/794(24.3%)", u"193/794(24.4%)"))
M(u"c3 表 t1 の 円の族 × 空の欄を除く の自", u"doc", doc_replace(u"| 207 | 168 | 447 |", u"| 207 | 168 | 446 |"))
M(u"c4 表 t1 の 自 ÷ 他 の字", u"doc", doc_replace(u"| 24.1 |", u"| 24.2 |"))
M(u"c5 表 t2 の群別の自", u"doc", doc_replace(u"34/129(26.4%)", u"35/129(26.4%)"))
M(u"c6 表 t2 の見出しの行の数", u"doc", doc_replace(u"| 読み | 甲(129 行) | 乙(632 行) | 丙(33 行) |", u"| 読み | 甲(129 行) | 乙(632 行) | 丙(34 行) |"))
M(u"c7 表 t3 の円の自", u"doc", doc_replace(u"105/510(20.6%)", u"106/510(20.6%)"))
M(u"c8 表 t4 の本", u"doc", doc_replace(u"63/176(35.8%) | 11 |", u"64/176(35.8%) | 11 |"))
M(u"c9 表 t5 の W の自(字のとおり)", u"doc", doc_replace(u"| 20 | 7 | 5 | 3 | 0 |", u"| 20 | 7 | 6 | 3 | 0 |"))
M(u"c10 表 t6 の N の自", u"doc", doc_replace(u"| 6634 | 2902 | 12 | 8 |", u"| 6634 | 2902 | 13 | 8 |"))
M(u"c11 当てないの散文の数", u"doc", doc_replace(u"字のとおりの読みで 355、円の族の読みで 207。", u"字のとおりの読みで 355、円の族の読みで 206。"))
M(u"c12 丙の散文の数", u"doc", doc_replace(u"scale が無い円の行 21(", u"scale が無い円の行 22("))
M(u"c13 サマリーの fact の散文の数", u"doc", doc_replace(u"F 4853・R 24886", u"F 4854・R 24886"))
M(u"c14 自己閉じの散文の数", u"doc", doc_replace(u"サマリーで 4418 個・202 本", u"サマリーで 4418 個・203 本"))
M(u"c15 本体の自己閉じの散文の数", u"doc", doc_replace(u"5588 個・192 本", u"5588 個・193 本"))
M(u"c16 F が空の本の散文の数", u"doc", doc_replace(u"そのままで 7・空の欄を除いて 5。", u"そのままで 7・空の欄を除いて 4。"))
M(u"c17 材料の散文の数", u"doc", doc_replace(u"切れた本 372", u"切れた本 373"))
M(u"c18 標本の散文の数(甲組の母)", u"doc", doc_replace(u"P 310 行から 60", u"P 311 行から 60"))
M(u"c19 軸の表(甲組の値の軸の 2)", u"doc", doc_replace(u"| 甲組 | 60 | 59 | 1 | 0 | 0 |", u"| 甲組 | 60 | 58 | 2 | 0 | 0 |"))
M(u"c20 身元の属性の表(甲組の期の不)", u"doc", doc_replace(u"| 甲組 | 期 | 54 | 1 | 5 |", u"| 甲組 | 期 | 54 | 1 | 6 |"))
M(u"c21 あいうの表(甲組のあの率)", u"doc", doc_replace(u"54/60(90.0%)", u"54/60(90.1%)"))
M(u"c22 値の軸 × あいうの表(甲組の 1 のあ)", u"doc", doc_replace(u"| 甲組 | 1 | 54 | 0 | 5 |", u"| 甲組 | 1 | 53 | 0 | 5 |"))
M(u"c23 違の属性の表(甲組の期)", u"doc", doc_replace(u"| 甲組 | 1 | 0 | 1 | 0 | 0 | 0 |", u"| 甲組 | 1 | 0 | 0 | 0 | 0 | 0 |"))
M(u"c24 PS の当たり割れの散文", u"doc", doc_replace(u"- 当たり 3(PS-2・PS-3・PS-5)・割れ 3(PS-1・PS-4・PS-7)", u"- 当たり 4(PS-2・PS-3・PS-5)・割れ 3(PS-1・PS-4・PS-7)"))
M(u"c25 RA-2 の散文の数", u"doc", doc_replace(u"違 の在る行が甲組で 1 行だけで", u"違 の在る行が甲組で 2 行だけで"))
M(u"c26 RA の当たりの散文の数", u"doc", doc_replace(u"- RA は当たり 4・外れ 0。", u"- RA は当たり 3・外れ 1。"))
M(u"c27 PS-6 の参考の散文の数", u"doc", doc_replace(u"W 組 9/19(47.4%)", u"W 組 10/19(47.4%)"))
M(u"c28 散文に記録に無い数を足す(組んだ行の外)", u"doc", doc_append(u"\n- 新しい行が 123 行ある。\n"))
M(u"c29 組んだ行を重ねる(1 回でなく 2 回)", u"doc", doc_append(u"\n| 甲組 | 60 | 59 | 1 | 0 | 0 |\n"))
M(u"c30 組んだ行を 1 つ消す(材料)", u"doc", doc_replace(u"- 材料は TSS の置き場の ZIP", u"- 材料は置き場の ZIP"))
M(u"c31 読みの基準の行の字を 1 つ変える", u"doc", doc_replace(u"配当の fact は全部が単体の member だったので", u"配当の fact は全部が連結の member だったので"))
M(u"c32 読みの基準の行を 1 つ消す", u"doc", doc_replace(u"- 予想の種類: 幅で書いた文が上限・下限の fact に当たれば 合。", u"- 予想の種類: "))
M(u"c33 表 t1 の名前の行を替える", u"doc", doc_replace(u"| 字のとおり × そのまま(主) | 355 |", u"| 字のとおり × そのまま | 355 |"))
M(u"c34 PS の表の主の結果の字", u"doc", doc_replace(u"24.3%(当たり)", u"24.3%(外れ)"))
M(u"c35 PS の表の 4 通りの字", u"doc", doc_replace(u"24.3%・33.9%・39.0%・56.3%", u"24.3%・33.9%・39.0%・56.2%"))
M(u"c36 全体の散文の数(値の軸の 3)", u"doc", doc_replace(u"全部の組で 1 行(甲組の期の 違 の 1 行だけ)", u"全部の組で 2 行(甲組の期の 違 の 1 行だけ)"))
# d 判定
M(u"d1 PS-1 の判定を 割れ → 当たり にする", u"judge", doc_replace(u"56.3% | **割れ** |", u"56.3% | 当たり |"))
M(u"d2 PS-2 の判定を 当たり → 外れ にする", u"judge", doc_replace(u"| 当たり |\n| PS-3 |", u"| 外れ |\n| PS-3 |"))
M(u"d3 PS-4 の判定を 割れ → 外れ にする", u"judge", doc_replace(u"5/20・11/20・12/20・19/20 | **割れ** |", u"5/20・11/20・12/20・19/20 | 外れ |"))
M(u"d4 PS-7 の判定を 割れ → 当たり にする", u"judge", doc_replace(u"・103/176(58.5%) | **割れ** |", u"・103/176(58.5%) | 当たり |"))
M(u"d5 PS-6 を測ったことにする(判定を 当たり)", u"judge", doc_replace(u"| 測っていない |\n", u"| 当たり |\n"))
M(u"d6 封の PS-1 の上限を替える(境が字で留めた値と違う)", u"judge", seal_replace(u"20% 以上 50% 以下", u"20% 以上 60% 以下"))
M(u"d7 封の PS-4 の境を替える(PS-4 の判定が動く)", u"judge", seal_replace(u"6 以上 14 以下", u"6 以上 4 以下"))
M(u"d8 封の PS-7 の境を替える", u"judge", seal_replace(u"**40% 以上**", u"**60% 以上**"))
M(u"d9 封の PS-2 の倍率を替える", u"judge", seal_replace(u"**5 倍以上**", u"**50 倍以上**"))
M(u"d10 読みの軸の封の RA-1 の境を替える", u"judge", axes_replace(u"**3 は 3 行以下**", u"**3 は 0 行以下**"))
M(u"d11 読みの軸の封の RA-4 の境を替える", u"judge", axes_replace(u"**値の軸の 2 は 6 行以下**", u"**値の軸の 2 は 0 行以下**"))
M(u"d12 RA-1 の判定を 当たり → 外れ にする(文書)", u"judge", doc_replace(u"| 甲組で値の軸の 3 は 3 行以下 | 0 行 | 当たり |", u"| 甲組で値の軸の 3 は 3 行以下 | 0 行 | 外れ |"))
M(u"d13 RA-2 の結果の字", u"judge", doc_replace(u"違 の在る行 1 行・いちばん多い属性 期 1", u"違 の在る行 2 行・いちばん多い属性 期 1"))
M(u"d14 記録の甲組の値の軸 3 を 4 行にする(RA-1 が外れに動く)", u"judge", lambda c: [c.ty[u"行"][i].__setitem__(5, 3) for i in range(4)])
M(u"d15 記録の甲組の 違 を期から項目にする(RA-2 が外れに動く)", u"judge", mut_ty_period_to_item)
M(u"d16 states の W の自を変える(PS-4 が当たりに動く)", u"judge", lambda c: [r.__setitem__(7, True) for r in [r for r in c.st[u"行"] if r[3] == u"W" and not r[7]][:2]])
M(u"d17 states の P の自を増やす(PS-1 が主で外れに動く)", u"judge", lambda c: [r.__setitem__(7, True) for r in [r for r in c.st[u"行"] if r[3] == u"P" and not r[7] and not r[5] and not r[6]][:244]])
M(u"d18 PS の予測の行を 1 つ消す", u"judge", seal_replace(u"| PS-7 |", u"| PS-8 |"))
M(u"d19 PS-4 の読みごとの当たり外れの表の行を逆の意味にする", u"judge", doc_replace(u"| PS-4 | 外れ | 当たり | 当たり | 外れ |", u"| PS-4 | 当たり | 外れ | 外れ | 当たり |"))
M(u"d20 PS-7 の読みごとの当たり外れの表の行を逆の意味にする", u"judge", doc_replace(u"| PS-7 | 外れ | 当たり | 当たり | 当たり |", u"| PS-7 | 当たり | 外れ | 外れ | 外れ |"))
M(u"d21 読みごとの当たり外れの表の行を消す", u"judge", doc_replace(u"| PS-5 | 当たり | 当たり | 当たり | 当たり |\n", u""))
M(u"d22 読みごとの当たり外れの表の行を doc の check にも通す", u"doc", doc_replace(u"| PS-4 | 外れ | 当たり | 当たり | 外れ |", u"| PS-4 | 当たり | 外れ | 外れ | 当たり |"))
M(u"d23 記録の W の自を変える(読みごとの表の PS-4 が動く)", u"judge", lambda c: [r.__setitem__(7, True) for r in [r for r in c.st[u"行"] if r[3] == u"W" and not r[7]][:2]])
M(u"l1 要点の文(主の数は壊れた fact に当てた数)を別の文に置き換える", u"limits", doc_replace(LEAD_MAIN_LINE, u"- 主の数は、同じ短信のサマリーの予想の fact に当たった率である。"))
M(u"l2 限界の「engine は動かしていない」の行(負けと限界の節)を消す", u"limits", doc_replace(LEAD_ENGINE_LINE + u"\n", u""))
M(u"l3 限界の節の「engine は動かしていない」の行を消す", u"limits", doc_replace(LIMIT_ENGINE_LINE + u"\n", u""))
M(u"l4 要点の文を節の外へ動かす", u"limits", lambda c: setattr(c, "doc", c.doc.replace(LEAD_MAIN_LINE + u"\n", u"", 1) + u"\n" + LEAD_MAIN_LINE + u"\n"))
# e 文書の字
M(u"e1 禁止語(証明した)", u"words", doc_append(u"\n証明" + u"した。\n"))
M(u"e2 禁止語(ハルシネーション)", u"words", doc_append(u"\nハルシ" + u"ネーション。\n"))
M(u"e3 禁止語(人の目)", u"words", doc_append(u"\n人の" + u"目。\n"))
M(u"e4 会社名らしい字(株式会社)", u"words", doc_append(u"\n株式会社。\n"))
M(u"e5 3 桁以上の漢数字", u"words", doc_append(u"\n三百行。\n"))
M(u"e6 docID の形の字", u"words", doc_append(u"\nS100" + u"ABCD\n"))
M(u"e7 要点の字(盲検でな)を落とす", u"words", doc_replace(u"盲検でな", u"盲検", True))
M(u"e8 要点の字(あと知恵)を落とす", u"words", doc_replace(u"あと知恵", u"後知恵", True))
M(u"e9 要点の字(直していない)を落とす", u"words", doc_replace(u"直していない", u"直した", True))
M(u"e10 要点の字(線が広すぎた)を落とす", u"words", doc_replace(u"線が広すぎた", u"線が狭かった", True))
M(u"e11 読みの軸の封の commit を言わない", u"words", doc_replace(u"06d7b8a7", u"0000000", True))
M(u"e12 禁止語を doc の check にも通す(doc の中の証明した)", u"doc", doc_append(u"\n証明" + u"した。\n"))
# f 封
M(u"f1 封の PS-1 の字を替える(根の字)", u"seal", seal_replace(u"**20% 以上 50% 以下**", u"**20% 以上 55% 以下**"))
M(u"f2 読みの軸の封の根の字を替える", u"seal", axes_replace(u"**3 は 3 行以下**", u"**3 は 4 行以下**"))
M(u"f3 封の文の途中の 1 字", u"frozen", seal_replace(u"結果が出たあと", u"結果が出たあ"))
M(u"f4 読みの軸の封の文の途中の 1 字", u"frozen", axes_replace(u"人間の指示", u"人間の指"))


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
        self.assertEqual(SHA_PIN[SCRIPT_REL], c.ty[u"この script の sha256"])
        self.assertEqual(SHA_PIN[STATES_REL], c.ty[u"states の記録の sha256"])

    def test_b_1_the_states_record_equals_the_recount_from_its_rows(self):
        self.assertEqual([], states_problems(Ctx()))

    def test_b_2_the_read_types_record_has_the_form_and_equals_the_recount_from_its_rows(self):
        self.assertEqual([], types_problems(Ctx()))

    def test_c_1_the_document_lines_equal_the_lines_rebuilt_from_the_records(self):
        self.assertEqual([], doc_problems(Ctx()))

    def test_c_2_the_rebuilt_lines_are_the_ones_the_brief_names(self):
        c = Ctx()
        exp = dict(expected_lines(c))
        self.assertIn(u"193/794(24.3%)", exp[u"t1 0"])
        self.assertIn(u"447/794(56.3%)", exp[u"t1 3"])
        self.assertIn(u"63/176(35.8%)", exp[u"t4 0"])
        self.assertIn(u"| 355 | 168 | 193 | 71 | 8 |", exp[u"t1 0"])
        self.assertIn(u"F 4853・R 24886", exp[u"サマリー fact"])
        self.assertIn(u"サマリーで 4418 個・202 本", exp[u"自己閉じ"])
        self.assertIn(u"| 甲組 | 60 | 59 | 1 | 0 | 0 |", exp[u"ra1 甲組"])
        self.assertIn(u"| 甲組 | 1 | 0 | 1 | 0 | 0 | 0 |", exp[u"ra5 甲組"])
        self.assertNotIn(u"【条件が合わない】", u"\n".join(l for _n, l in expected_lines(c)))

    def test_d_1_the_judgement_is_redone_from_the_seal_text_and_the_records(self):
        self.assertEqual([], judge_problems(Ctx()))

    def test_d_2_the_real_judgement_is_three_hits_three_splits_and_one_not_measured_and_four_ra_hits(self):
        c = Ctx()
        vs = [verdict_of(oks)[0] for _i, _t, oks in ps_judge(c)]
        self.assertEqual([i for i, v in zip(PS_IDS, vs) if v == SPLIT], [u"PS-1", u"PS-4", u"PS-7"])
        self.assertEqual([i for i, v in zip(PS_IDS, vs) if v == HIT], [u"PS-2", u"PS-3", u"PS-5"])
        self.assertEqual(vs[5], NOT_MEASURED)
        self.assertTrue(all(ok for _i, _t, ok in ra_judge(c)))

    def test_d_3_a_split_prediction_has_a_hit_and_a_miss_among_the_four_readings(self):
        for pid, _t, oks in ps_judge(Ctx()):
            if oks is not None and verdict_of(oks)[0] == SPLIT:
                self.assertTrue(any(oks) and not all(oks), pid)

    def test_e_1_the_words_are_clean(self):
        self.assertEqual([], words_problems(Ctx()))

    def test_e_2_the_seals_have_the_texts_the_document_roots_on(self):
        self.assertEqual([], seal_text_problems(Ctx()))

    def test_f_1_the_seals_are_the_text_of_the_sealed_commits(self):
        self.assertEqual([], seal_frozen_problems(Ctx()))

    def test_f_2_the_real_history_has_the_seals_before_the_script_the_records_the_document_and_this_gate(self):
        u"""記録・文書・この門のどれかが未 commit なら赤(足した commit が無い。skip にしない)。全部 commit された後で初めて緑。"""
        self.assertEqual([], order_problems_real())

    def test_f_3_the_real_order_failure_before_the_commit_is_only_the_uncommitted_files(self):
        got = order_problems_real()
        self.assertTrue(all(p.startswith(u"UNCOMMITTED:") for p in got), got)

    def test_f_4_the_order_check_lists_the_records_the_gates_and_the_document(self):
        self.assertEqual([STATES_REL, TYPES_REL, SEAL_GATE_REL, DOC_REL, GATE_REL], order_others())
        self.assertTrue(all(os.path.exists(os.path.join(ROOT, r)) for r in order_others() + [SCRIPT_REL]))

    def test_f_5_engine_lib_inputs_are_untouched(self):
        self.assertEqual([], engine_problems())


class OrderGateTest(unittest.TestCase):
    u"""順序の検査自体が、悪い順を赤にできること(使い捨ての git で)。読みの軸の封が記録より後なら赤。"""

    def test_o_1_good_and_bad_orders(self):
        r = PR.Repo()
        r.put("docs/seal.md")
        s = r.commit("docs/seal.md")
        r.put("docs/axes.md")
        a = r.commit("docs/axes.md")
        r.put("measure/s.py")
        r.commit("measure/s.py")
        others = ["fixtures/a.json", "docs/r.md", "tests/g.py"]
        for o in others:
            r.put(o)
        self.assertEqual([u"UNCOMMITTED:" + o for o in others], PR.order_problems(r.d, PREFIX, "docs/axes.md", a[:7], [], others))
        r.commit(*others)
        self.assertEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], ["measure/s.py"], others))
        self.assertEqual([], PR.order_problems(r.d, PREFIX, "docs/axes.md", a[:7], [], others))
        r2 = PR.Repo()
        r2.put("docs/seal.md")
        r2.commit("docs/seal.md")
        r2.put("fixtures/a.json")
        r2.commit("fixtures/a.json")
        r2.put("docs/axes.md")
        a2 = r2.commit("docs/axes.md")
        self.assertNotEqual([], PR.order_problems(r2.d, PREFIX, "docs/axes.md", a2[:7], [], ["fixtures/a.json"]))      # 記録が読みの軸の封より前


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
        before = dict((rel, hashlib.sha256(read_bytes(rel)).hexdigest()) for rel in (STATES_REL, TYPES_REL, SCRIPT_REL, SEAL_REL, AXES_SEAL_REL, DOC_REL))
        c = Ctx()
        c.st[u"行"][0][7] = None
        c.ty[u"行"][0][5] = 9
        c.doc = u"x"
        self.assertNotEqual(9, Ctx().ty[u"行"][0][5])
        self.assertNotEqual(u"x", Ctx().doc)
        self.assertEqual(before, dict((rel, hashlib.sha256(read_bytes(rel)).hexdigest()) for rel in before))

    def test_m_4_the_mutation_table_covers_every_check_and_every_effect_named_in_the_brief(self):
        self.assertEqual(set(CHECKS), set(ch for _l, ch, _f in MUTATIONS))
        labels = u"\n".join(l for l, _c, _f in MUTATIONS)
        for need in (u"states の記録の 1 byte", u"read_types の記録の 1 byte", u"値の軸を 1 つ変える", u"身元を 1 字変える", u"字を 1 つ変える", u"表 t1", u"散文の数", u"禁止語", u"漢数字",
                     u"判定を", u"当たり外れの表", u"要点の文", u"封の文の途中の 1 字", u"読みの軸の封の文の途中の 1 字", u"読みの基準", u"PS-6 を測ったことにする"):
            self.assertIn(need, labels)

    def test_m_5_a_hit_turned_to_a_miss_is_caught_by_the_judge_and_not_only_by_the_table(self):
        c = Ctx()
        for i in range(4):
            c.ty[u"行"][i][5] = 3                          # RA-1 が外れに動く。文書の表は当たりのまま
        jd = dict((i, ok) for i, _t, ok in ra_judge(c))
        self.assertFalse(jd[u"RA-1"])


class WiringTest(unittest.TestCase):
    def test_n_1_this_gate_carries_no_docid_and_no_key(self):
        src = read(GATE_REL)
        for bad in (u"ANTHRO" + u"PIC", u"API_" + u"KEY", u"url" + u"lib", u"sock" + u"et"):
            self.assertNotIn(bad, src)

    def test_n_2_this_gate_does_not_widen_the_boundary_import_list(self):
        self.assertEqual([], SG.boundary_problems())


if __name__ == "__main__":
    unittest.main()
