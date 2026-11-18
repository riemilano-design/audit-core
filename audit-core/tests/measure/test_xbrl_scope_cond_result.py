# -*- coding: utf-8 -*-
"""結果の門: 封 docs/XBRL_SCOPE_COND_SEAL_2026-11-19.md(5b77133b)の結果の文書 docs/XBRL_SCOPE_COND_RESULT_2026-11-19.md。

封の門 ``test_xbrl_scope_cond_seal.py`` の次の段。**追跡されている記録・script・封・結果の文書と git の履歴だけを読む**(材料は読まない。全数の作り直しは走らせない)。

縛るもの(検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表で 1 つずつ。木の file は変異させず、``Ctx`` の写しに当てる)
 a script・記録・封の門の sha256(字で留める)
 b 記録の中の整合: 封の門の ``record_problems``(行からの数え直し・予測の判定に要る数の作り直し・文や値の漏れ)+ 最上位の欄の一覧
 c 結果の文書の数: 数字を含む行は全部、記録から組んだ行と字で同じ(組んだ行は文書に決めた回数だけ在り、順も同じ)。そのどれにも当たらない行に数字が在れば赤
 d 予測 SC-1〜SC-7(SC-4 は a・b。計 8 本)の判定を、封の予測の字から取った境と記録の行・読みの札(止めた行を行から数える)から門が自分で決め直して、
   記録の「予測の判定に要る数」・文書の表と同じ・字で留めた判定と同じ。SC-6 の段 2 の境への近さの向きも同じ
 e 文書に禁止語・会社名らしい字・docID・3 桁以上の漢数字・要素名や pointer の形・封 §2 の表の語が無い・要点の字が在る
 f 封が commit から 1 字も変わっていない・順序(commit の順。未 commit は赤)・engine は封の commit から 0 行
この file は docID の字を持たない。
"""
import collections
import fractions
import hashlib
import importlib.util
import io
import json
import math
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


SG = load_module("tests/measure/test_xbrl_scope_cond_seal.py", "sc_seal_gate_for_sc_result_gate")      # 封の門の部品。門としては走らせない
MS = SG.MS
PR = SG.PR
AT = MS.AT

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
RECORD_COMMIT_SHORT = "5b7c7339"                              # script・記録・封の門の commit(履歴から探した値と照らす)
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
RECORD_REL = SG.RECORD_REL
GATE_REL = "tests/measure/test_xbrl_scope_cond_result.py"
DOC_REL = "docs/XBRL_SCOPE_COND_RESULT_2026-11-19.md"

SHA_PIN = collections.OrderedDict([
    (RECORD_REL, "d938942bffb39176464f3c644932cf53258f84676aacdbbbc421de74d4dc08a7"),
    (SCRIPT_REL, "c7ec858ea9523ede23ab2da6d16b53ec338d50cb35899ecac66705e16919e065"),
    (SEAL_GATE_REL, "239a59a3a887ccac950b32ecf7e8eea1055057c372e77a1baef53c0b6e2a5a52")])

K_WIRE, K_ALL, K_LABEL, K_CLASS, K_PRED = SG.K_WIRE, SG.K_ALL, SG.K_LABEL, SG.K_CLASS, SG.K_PRED
K_POS = u"位置の確かめ・member の欄・「事業」で終わる前の字(便ごと)"
K_CUT = u"切り出し"
TOP_KEYS = (u"seal", u"封の commit", u"step", u"この script の sha256", u"入力", u"engine の指紋(今。便 RT の記録の今と同じ)", u"profile", u"材料", u"手がかりの語の表", u"事業の形",
            u"段の定義", K_CUT, K_WIRE, K_ALL, K_LABEL, K_CLASS, K_PRED, u"限界", u"時間(秒)", u"key_leaks", u"行の欄", u"行")
BATCHES = (u"TSS", u"KAM", u"YS")
STAGES = (1, 2, 3)
SN = dict((t, u"段 %d" % t) for t in STAGES)
CLASSES = (u"S", u"N", u"U", u"R", u"K", u"H")
IDS = (u"SC-1", u"SC-2", u"SC-3", u"SC-4a", u"SC-4b", u"SC-5", u"SC-6", u"SC-7")
HIT, MISS, UNMEASURED = u"当たり", u"**外れ**", u"測れていない"
VERDICT_PINNED = (HIT, HIT, HIT, HIT, HIT, HIT, MISS, MISS)
UNIT_NAMES = collections.OrderedDict([(u"TSS", [u"(文の種類なし)"]), (u"KAM", [u"連結", u"単体"]), (u"YS", [u"研究開発活動", u"設備投資等の概要", u"配当政策"])])

FORBIDDEN_WORDS = (u"証明" + u"した", u"ハルシ" + u"ネーション", u"精" + u"度", u"世界で 1 " + u"社")
COMPANY_WORDS = (u"株式会社", u"有限会社", u"合同会社", u"㈱", u"(株)")
DOCID_RE = re.compile(r"S100[0-9A-Z]{4}")
POINTER_RE = re.compile(r"xbrl:|jppfs|jpcrp|jpdei|_cor:|@(Current|Prior)|formula:|Summary_|NonConsolidated|ConsolidatedMember")
KANJI_NUM_RE = re.compile(u"[二三四五六七八九]百|[一二三四五六七八九]千|百[一二三四五六七八九十]|千[一二三四五六七八九百]")
HUMAN_EYE_RE = re.compile(u"人の" + u"目")
#: 封 §2-3 の表の語は書かない(表を指すときは「封 §2 の表」)。「うち」は普通の文に出る・「単体」は KAM の文の種類の名前なので除く
TABLE_WORDS = tuple(w for ws in SG.WORD_TABLE.values() for w in ws if w not in (u"うち", u"単体"))
REQUIRED_PHRASES = (u"先に負けと限界を書く", u"外れ", u"当たり", u"追跡する記録に無い", u"監査の席の確かめ", u"人間の決定", u"限界", u"engine は 0 行", u"封 §2 の表",
                    u"引き継ぎに書く", u"判定は司令塔(盲検でない)", u"engine を変えるかは人間が決める", u"別の封(未使用の材料で・盲検の語の表で)", u"外れは外れとして残す")


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


def fr(n, d):
    return u"%d/%d(%s)" % (n, d, rate_text(n, d))


def point_text(n1, d1, n2, d2):
    u"""(n1/d1 − n2/d2)× 100 を小数 2 桁(四捨五入)の字で。"""
    x = (fractions.Fraction(n1, d1) - fractions.Fraction(n2, d2)) * 100
    q = int(math.floor(x * 100 + fractions.Fraction(1, 2)))
    return u"%d.%02d" % divmod(q, 100)


_LABELS = []


def labels():
    u"""札つきの行(読みの記録から。止めた行の数え直しの材料。変異で変えない)。"""
    if not _LABELS:
        _LABELS.extend(MS.build_labels(SG.real_recs()))
    return _LABELS


class Ctx(object):
    u"""記録・封・文書・字の写し。変異は毎回 ``Ctx()`` の新しい写しに 1 か所だけ加える。"""

    def __init__(self):
        self.rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        self.seal = read(SEAL_REL)
        self.doc = read(DOC_REL)
        self.texts = collections.OrderedDict((rel, read_bytes(rel)) for rel in SHA_PIN)


# ======================================================================================================
# a. sha256
def sha_problems(texts, pin=None):
    pin = SHA_PIN if pin is None else pin
    return [u"sha256: %s が字で留めた値と違う" % rel for rel, want in pin.items() if hashlib.sha256(texts.get(rel, b"")).hexdigest() != want]


# ======================================================================================================
# b. 記録の中の整合(封の門の部品)
def record_problems(c):
    out = list(SG.record_problems(text=json.dumps(c.rec, ensure_ascii=False)))
    if tuple(c.rec) != TOP_KEYS:
        out.append(u"記録の最上位の欄が決めた一覧と違う(文・値などの足された欄の疑い)")
    return out


# ======================================================================================================
# 記録の読み出し(門の側で独立に。止めた行は記録の行から数える)
def is_stop(row, t):
    return row[6 + t] != u""


class Facts(object):
    u"""記録の行と読みの札から数えた数。集計の欄は使わず、行(止めた行・member が空か)・札から数える。"""

    def __init__(self, c):
        self.rec = c.rec
        self.rows = c.rec[u"行"]
        self.index = dict((tuple(r[:5]), r) for r in self.rows)
        self.v = dict((b, []) for b in BATCHES)               # 引けた V の札: (札, 行)
        self.g = dict((b, []) for b in (u"KAM", u"YS"))
        self.v_label_n = dict((b, 0) for b in BATCHES)
        self.g_label_n = dict((b, 0) for b in (u"KAM", u"YS"))
        for lab in labels():
            row = self.index.get((lab[u"便"], lab[u"#"], lab[u"側"], lab[u"si"], lab[u"pos"]))
            if lab[u"state"] == u"V":
                self.v_label_n[lab[u"便"]] += 1
                if row is not None and row[5] == u"V":
                    self.v[lab[u"便"]].append((lab, row))
            else:
                self.g_label_n[lab[u"便"]] += 1
                if row is not None and row[5] == u"G":
                    self.g[lab[u"便"]].append((lab, row))
        rng = lambda lab: lab[u"種別"] == AT.KIND_IN and lab[u"先"] == u"範囲"
        drop = lambda lab: lab[u"種別"] == AT.KIND_DROP
        self.rng = dict((b, [r for lab, r in self.v[b] if rng(lab)]) for b in BATCHES)
        self.non = dict((b, [r for lab, r in self.v[b] if not rng(lab) and not drop(lab)]) for b in BATCHES)
        self.drop = dict((b, [r for lab, r in self.v[b] if drop(lab)]) for b in BATCHES)
        self.a = dict((b, [r for lab, r in self.g[b] if lab[u"型"] == u"a"]) for b in self.g)
        self.bb = dict((b, [(lab, r) for lab, r in self.g[b] if lab[u"型"] == u"b"]) for b in self.g)
        self.b_rng = dict((b, [r for lab, r in self.bb[b] if lab[u"違うもの"] == u"範囲"]) for b in self.g)
        self.b_side = dict((b, [r for lab, r in self.bb[b] if AT.DIFF_TO_ATTR[lab[u"違うもの"]] == u"範囲"]) for b in self.g)
        self.tss_g = [r for r in self.rows if r[0] == u"TSS" and r[5] == u"G"]
        self.tss_v = [r for r in self.rows if r[0] == u"TSS" and r[5] == u"V"]

    @staticmethod
    def cat(rs):
        u"""行の集まり → (分母, {段: 止めた行})。"""
        return len(rs), dict((t, sum(1 for r in rs if is_stop(r, t))) for t in STAGES)

    def sum_of(self, d, bs):
        return [r for b in bs for r in d[b]]


# ======================================================================================================
# d. 予測の判定(封の予測の字から境を取り、記録の行・札から決め直す)
def seal_row(seal, pid):
    sec = seal[seal.index(u"## §4 "):] if u"## §4 " in seal else u""
    m = re.search(r"^\| %s \| (.*?) \| (.*?) \|$" % re.escape(pid), sec, re.M)
    return (m.group(1), m.group(2)) if m else (u"", u"")


def pct(s):
    return fractions.Fraction(s) / 100


def seal_bounds(seal):
    u"""封の予測の字から数を取る。取れなければ例外(= 検査が赤)。"""
    r = lambda pid: seal_row(seal, pid)
    b = collections.OrderedDict()
    m = re.search(r"(\d+)% 以上 (\d+)% 以下", r(u"SC-1")[0])
    b[u"SC-1"] = (pct(m.group(1)), pct(m.group(2)))
    b[u"SC-2"] = pct(re.search(r"止めるのは (\d+)% 以下", r(u"SC-2")[0]).group(1))
    b[u"SC-3"] = int(re.search(r"段 1 の率の (\d+) 倍以上", r(u"SC-3")[0]).group(1))
    b[u"SC-3 段 1 が 0"] = int(re.search(r"段 3 が (\d+) 行以上", r(u"SC-3")[0]).group(1))
    b[u"SC-4a"] = pct(re.search(r"止めるのは (\d+)% 以下", r(u"SC-4a")[0]).group(1))
    b[u"SC-4b"] = pct(re.search(r"止めるのは (\d+)% 以上", r(u"SC-4b")[0]).group(1))
    b[u"SC-5"] = int(re.search(r"より (\d+) ポイント以上低い", r(u"SC-5")[0]).group(1))
    m = re.search(r"を (\d+)% 以上止め、かつ、札 a の G の行を止めるのは (\d+)% 以下", r(u"SC-6")[0])
    b[u"SC-6"] = (pct(m.group(1)), pct(m.group(2)))
    b[u"SC-7"] = int(re.search(r"段 3 は (\d+) 行以上止める", r(u"SC-7")[0]).group(1))
    b[u"SC-7 測れない"] = int(re.search(r"分母が (\d+) 行未満", r(u"SC-7")[1]).group(1))
    return b


def numbers(f):
    u"""判定に使う数(行・札から数えた数)。"""
    c = collections.OrderedDict()
    rngT = f.sum_of(f.rng, BATCHES)
    nonT = f.sum_of(f.non, BATCHES)
    aT = f.sum_of(f.a, (u"KAM", u"YS"))
    bT = f.sum_of(f.b_rng, (u"KAM", u"YS"))
    bS = f.sum_of(f.b_side, (u"KAM", u"YS"))
    c[u"rng"] = f.cat(rngT)
    c[u"non"] = f.cat(nonT)
    c[u"a"] = f.cat(aT)
    c[u"tss_g"] = f.cat(f.tss_g)
    c[u"tss_v"] = f.cat(f.tss_v)
    c[u"b_rng"] = f.cat(bT)
    c[u"b_side"] = f.cat(bS)
    return c


def judge(c):
    u"""[(id, 判定の字)](8 本)。封の字の境と、記録の行・札から決める。"""
    b = seal_bounds(c.seal)
    n = numbers(Facts(c))
    q = lambda d, s, t: fractions.Fraction(s[t], d)
    rd, rs = n[u"rng"]
    ad, as_ = n[u"a"]
    out = []
    lo, hi = b[u"SC-1"]
    out.append((u"SC-1", lo <= q(rd, rs, 2) <= hi))
    out.append((u"SC-2", q(ad, as_, 1) <= b[u"SC-2"]))
    s1, s3 = as_[1], as_[3]
    out.append((u"SC-3", (s3 >= b[u"SC-3 段 1 が 0"]) if s1 == 0 else (fractions.Fraction(s3, ad) >= b[u"SC-3"] * fractions.Fraction(s1, ad))))
    gd, gs = n[u"tss_g"]
    out.append((u"SC-4a", q(gd, gs, 2) <= b[u"SC-4a"]))
    vd, vs = n[u"tss_v"]
    out.append((u"SC-4b", q(vd, vs, 2) >= b[u"SC-4b"]))
    nd, ns = n[u"non"]
    out.append((u"SC-5", (q(rd, rs, 2) - q(nd, ns, 2)) * 100 >= b[u"SC-5"]))
    lo6, hi6 = b[u"SC-6"]
    sat = [t for t in STAGES if q(rd, rs, t) >= lo6 and q(ad, as_, t) <= hi6]
    out.append((u"SC-6", len(sat) == 0))
    td, ts = n[u"b_rng"]
    out.append((u"SC-7", None if td < b[u"SC-7 測れない"] else ts[3] >= b[u"SC-7"]))
    return out


def verdicts(c):
    return tuple(UNMEASURED if ok is None else (HIT if ok else MISS) for _i, ok in judge(c))


def satisfied_stages(c):
    b = seal_bounds(c.seal)
    n = numbers(Facts(c))
    rd, rs = n[u"rng"]
    ad, as_ = n[u"a"]
    lo6, hi6 = b[u"SC-6"]
    return [t for t in STAGES if fractions.Fraction(rs[t], rd) >= lo6 and fractions.Fraction(as_[t], ad) <= hi6]


def slack(c):
    u"""SC-6 の段 2 の余り: (止めた行 − 50% に要る行、5% で許す行 − 止めた行)。"""
    b = seal_bounds(c.seal)
    n = numbers(Facts(c))
    rd, rs = n[u"rng"]
    ad, as_ = n[u"a"]
    lo6, hi6 = b[u"SC-6"]
    need = int(math.ceil(lo6 * rd))
    allow = int(math.floor(hi6 * ad))
    return rs[2] - need, allow - as_[2]


def direction(c):
    u"""(SC-6 の段 2 の範囲の札の V は 50% の境のすぐ上(2 ポイント未満)・札 a の G は 5% の境のすぐ下・SC-1 は両端から 5 ポイント以上離れている・SC-6 の満たす段は段 2 だけ・
    段 1 は範囲の札の V が 50% 未満・段 3 は札 a の G が 5% 超)。"""
    b = seal_bounds(c.seal)
    n = numbers(Facts(c))
    rd, rs = n[u"rng"]
    ad, as_ = n[u"a"]
    lo6, hi6 = b[u"SC-6"]
    lo1, hi1 = b[u"SC-1"]
    x = fractions.Fraction(rs[2], rd)
    y = fractions.Fraction(as_[2], ad)
    two = fractions.Fraction(2, 100)
    five = fractions.Fraction(5, 100)
    return (lo6 <= x < lo6 + two, hi6 - two < y <= hi6, x - lo1 >= five and hi1 - x >= five, satisfied_stages(c) == [2],
            fractions.Fraction(rs[1], rd) < lo6, fractions.Fraction(as_[3], ad) > hi6)


def pk(pr, prefix):
    ks = [k for k in pr if k.startswith(prefix)]
    return pr[ks[0]] if len(ks) == 1 else None


def bias_problems(c):
    u"""要約の偏りの行の言い分: 範囲の札の V の分母は TSS が過半・YS は分母が 5 未満・KAM 単独と KAM + YS は段 2 で 50% 未満・TSS は 50% 以上。"""
    f = Facts(c)
    b = seal_bounds(c.seal)
    lo6 = b[u"SC-6"][0]
    d = dict((bb, f.cat(f.rng[bb])) for bb in BATCHES)
    out = []
    rd = sum(d[bb][0] for bb in BATCHES)
    if not (d[u"TSS"][0] * 2 > rd and d[u"YS"][0] < b[u"SC-7 測れない"]):
        out.append(u"bias: 範囲の札の V の分母が TSS 過半でない・YS が 5 未満でない")
    if not (fractions.Fraction(d[u"KAM"][1][2], d[u"KAM"][0]) < lo6 and fractions.Fraction(d[u"KAM"][1][2] + d[u"YS"][1][2], d[u"KAM"][0] + d[u"YS"][0]) < lo6
            and fractions.Fraction(d[u"TSS"][1][2], d[u"TSS"][0]) >= lo6):
        out.append(u"bias: 段 2 の率が「TSS は 50% 以上・KAM 単独と KAM + YS は 50% 未満」でない")
    return out


def judge_problems(c):
    out = []
    got = verdicts(c)
    if got != VERDICT_PINNED:
        out.append(u"judge: 決め直した判定が字で留めた判定と違う: %s" % (u" ".join(got),))
    if direction(c) != (True,) * 6:
        out.append(u"judge: SC-6 の段 2 の境への近さの向き(50% のすぐ上・5% のすぐ下・SC-1 は端から離れている・満たす段は段 2 だけ)が行からの数え直しと違う")
    pr = c.rec[K_PRED]
    f = Facts(c)
    n = numbers(f)

    def nd(t, x):
        return collections.OrderedDict([(u"分子", x[1][t]), (u"分母", x[0]), (u"率", rate_text(x[1][t], x[0]))])

    def cells(x):
        return collections.OrderedDict((SN[t], nd(t, x)) for t in STAGES)

    def by_batch(d, bs):
        return collections.OrderedDict([(b, cells(f.cat(d[b]))) for b in bs])
    want = [(u"SC-1 ", collections.OrderedDict([(u"3 便の合計", cells(n[u"rng"]))] + list(by_batch(f.rng, BATCHES).items()))),
            (u"SC-2 ", collections.OrderedDict([(u"KAM と YS の合計", cells(n[u"a"]))] + list(by_batch(f.a, (u"KAM", u"YS")).items()))),
            (u"SC-4a ", cells(n[u"tss_g"])),
            (u"SC-4b ", cells(n[u"tss_v"])),
            (u"SC-5 段 2 ", collections.OrderedDict([(u"3 便の合計", cells(n[u"non"]))] + list(by_batch(f.non, BATCHES).items()))),
            (u"SC-7 札 b", cells(n[u"b_rng"])),
            (u"SC-7 参考", cells(n[u"b_side"]))]
    for p, v in want:
        if pk(pr, p) != v:
            out.append(u"judge: 記録の「予測の判定に要る数」の欄が行・札から数え直した数と違う: %s" % p)
    d3 = pk(pr, u"SC-3 ")
    ad, as_ = n[u"a"]
    if d3 is None or (d3[u"引けた行"], d3[u"段 1 の止めた行"], d3[u"段 3 の止めた行"]) != (ad, as_[1], as_[3]):
        out.append(u"judge: SC-3 の欄が行・札から数え直した数と違う")
    d5 = pk(pr, u"SC-5 率の差")
    rd, rs = n[u"rng"]
    nd_, ns_ = n[u"non"]
    if d5 is None or [d5[SN[t]] for t in STAGES] != [point_text(rs[t], rd, ns_[t], nd_) for t in STAGES]:
        out.append(u"judge: SC-5 の率の差の欄が行・札から数え直した数と違う")
    d6 = pk(pr, u"SC-6 ")
    if d6 is None or any(d6[SN[t]][u"範囲の札の V の行"] != nd(t, n[u"rng"]) or d6[SN[t]][u"札 a の G の行"] != nd(t, n[u"a"]) for t in STAGES):
        out.append(u"judge: SC-6 の欄が行・札から数え直した数と違う")
    out.extend(bias_problems(c))
    td, ts = n[u"b_rng"]
    sd, ss = n[u"b_side"]
    if sum(ts.values()) != 0 or sum(ss.values()) != 0:
        out.append(u"judge: SC-7 の札 b の範囲の行が(字のとおり・便 AT の写しとも)3 段とも 0 でない")
    d0 = pk(pr, u"分母の確かめ")
    if d0 is None or (d0[u"V の札の行(札)"], d0[u"V の札の行(引けた)"], d0[u"G の札の行(札)"], d0[u"G の札の行(引けた)"]) != (
            sum(f.v_label_n.values()), sum(len(f.v[b]) for b in BATCHES), sum(f.g_label_n.values()), sum(len(f.g[b]) for b in f.g)):
        out.append(u"judge: 分母の確かめの欄が札・行から数え直した数と違う")
    return out


# ======================================================================================================
# c. 文書の行(記録から組む)
def stage_vals(cell):
    return [cell[u"止めた行"][SN[t]] for t in STAGES]


def expected_lines(c):
    u"""[(名前, 行)]。文書の中の、数字を含む行の全部(文書の順)。"""
    f = Facts(c)
    rec = c.rec
    n = numbers(f)
    b = seal_bounds(c.seal)
    vd = verdicts(c)
    v = dict(zip(IDS, vd))
    ids_hit = [i for i, x in zip(IDS, vd) if x == HIT]
    ids_miss = [i for i, x in zip(IDS, vd) if x == MISS]
    wire, allr, lab, cls, pr = rec[K_WIRE], rec[K_ALL], rec[K_LABEL], rec[K_CLASS], rec[K_PRED]
    pos = wire[K_POS]
    cut = rec[K_CUT]
    L = []

    def add(name, line):
        L.append((name, line))

    p2 = lambda x: u"%d%%" % (x * 100)                        # 境(Fraction)→ 整数の %
    rd, rs = n[u"rng"]
    ad, as_ = n[u"a"]
    nd, ns = n[u"non"]
    gd, gs = n[u"tss_g"]
    vd_, vs = n[u"tss_v"]
    td, ts = n[u"b_rng"]
    sd, ss = n[u"b_side"]
    lo6, hi6 = b[u"SC-6"]
    q = lambda d, s, t: fr(s[t], d)
    sat = satisfied_stages(c)
    slv, slg = slack(c)
    rngB = dict((bb, f.cat(f.rng[bb])) for bb in BATCHES)
    nonB = dict((bb, f.cat(f.non[bb])) for bb in BATCHES)
    aB = dict((bb, f.cat(f.a[bb])) for bb in (u"KAM", u"YS"))
    kam_ys = (rs[2] - rngB[u"TSS"][1][2], rd - rngB[u"TSS"][0])

    # ---- 頭
    add(u"head 封", u"封 `docs/XBRL_SCOPE_COND_SEAL_2026-11-19.md`(commit %s)。script `measure/xbrl_scope_cond_2026-11-19.py`・記録 `fixtures/xbrl/scope_cond/stops_2026-11-19.json`・封の門 `tests/measure/test_xbrl_scope_cond_seal.py` は commit %s(独立監査 GO)。取得 0・0 USD・通信なし・LLM の席は呼んでいない。" % (SEAL_COMMIT_SHORT, RECORD_COMMIT_SHORT))
    add(u"head 数", u"この文書の数は全部、記録から 1 つずつ読んだもの(結果の門が、記録の行・読みの札から数え直した数と字で同じことを見る)。engine は 0 行(engine を変えた commit は無い)。")
    # ---- 要約
    add(u"lead 判定", u"- 判定した %d 本(SC-4 を a と b に分けて数える)のうち、%s が外れ、%s が当たり(当たり %d・外れ %d)。" % (len(vd), u" と ".join(ids_miss), u"・".join(ids_hit), len(ids_hit), len(ids_miss)))
    add(u"lead SC-6", u"- SC-6 が外れ: 封の字は「満たす段は 1 つも無い」だが、段 %s が満たした(範囲の札の V の行 %s で %s 以上・札 a の G の行 %s で %s 以下)。司令塔は規則の効きを小さく見すぎた。外れは外れとして残す。段 1 は範囲の札の V が %s で %s 未満・段 3 は札 a の G が %s で %s 超なので満たさない。"
        % (u"・".join(str(t) for t in sat), q(rd, rs, 2), p2(lo6), q(ad, as_, 2), p2(hi6), q(rd, rs, 1), p2(lo6), q(ad, as_, 3), p2(hi6)))
    add(u"lead SC-7", u"- SC-7 が外れ: 札 b のうち「違うもの」が範囲の行は %d 行(KAM と YS の合計)で、止めた行は段 1 が %d・段 2 が %d・段 3 が %d。便 AT の写しの読み(%d 行)でも 3 段とも %d。"
        % (td, ts[1], ts[2], ts[3], sd, sum(ss.values())))
    add(u"lead 近さ", u"- SC-6 の段 2 は境に近い: 範囲の札の V の止めた行があと %d 行少なければ %s を下回り、札 a の G の止めた行があと %d 行多ければ %s を超える。" % (slv + 1, p2(lo6), slg + 1, p2(hi6)))
    add(u"lead 偏り", u"- 範囲の札の V の分母は TSS に偏る(引けた行は TSS %d・KAM %d・YS %d)。段 2 の率は TSS %s・KAM %s・YS %s で、YS は分母が 5 未満。KAM と YS の合計は %s で、%s に届かない。KAM だけでも届かない。"
        % (rngB[u"TSS"][0], rngB[u"KAM"][0], rngB[u"YS"][0], q(*[rngB[u"TSS"][0], rngB[u"TSS"][1], 2]), q(*[rngB[u"KAM"][0], rngB[u"KAM"][1], 2]), q(*[rngB[u"YS"][0], rngB[u"YS"][1], 2]),
           fr(kam_ys[0], kam_ys[1]), p2(lo6)))
    add(u"lead 盲検", u"- 手がかりの語の表は盲検でない(封 §0 の申告)。段 2 が満たした数には、封じる前に形を見た便の材料(TSS の 1 本)を含む。札 a の G の分母は KAM と YS だけの %d 行(TSS に G の読みの札は無い)。" % ad)
    add(u"lead engine", u"- 後付けの規則であり engine は 0 行。engine に入れたときに同じ数になるとは測っていない。止めた G の行は正しい結びを減らした可能性を含む。TSS の G で止めた行(段 2 で %s)の中身は誰も読んでいない。" % q(gd, gs, 2))
    add(u"lead 読み", u"- 封 §4 の読み方の決めどおり、SC-6 が外れたので「段 2 の規則を engine に入れる案」を人間に上げる材料にする。engine を変えるかは人間が決める。入れるなら別の封(未使用の材料で・盲検の語の表で)が先に要る。")
    # ---- §1 予測の表
    def row(pid, meas):
        add(u"table " + pid, u"| %s | %s | %s | %s |" % (pid, seal_row(c.seal, pid)[0], meas, v[pid]))
    row(u"SC-1", u"%s(段 1 %s・段 3 %s)" % (q(rd, rs, 2), q(rd, rs, 1), q(rd, rs, 3)))
    row(u"SC-2", u"%s(KAM %s・YS %s。段 2 %s・段 3 %s)" % (q(ad, as_, 1), q(aB[u"KAM"][0], aB[u"KAM"][1], 1), q(aB[u"YS"][0], aB[u"YS"][1], 1), q(ad, as_, 2), q(ad, as_, 3)))
    row(u"SC-3", u"段 3 %s・段 1 %s" % (q(ad, as_, 3), q(ad, as_, 1)))
    row(u"SC-4a", q(gd, gs, 2))
    row(u"SC-4b", q(vd_, vs, 2))
    row(u"SC-5", u"範囲でない %s・範囲 %s・差 %s ポイント" % (q(nd, ns, 2), q(rd, rs, 2), pk(pr, u"SC-5 率の差")[SN[2]]))
    row(u"SC-6", u"満たす段は段 %s(%s と %s)" % (u"・".join(str(t) for t in sat), q(rd, rs, 2), q(ad, as_, 2)))
    row(u"SC-7", u"段 3 %s(段 1 %s・段 2 %s。便 AT の写しの読みは段 3 %s)" % (q(td, ts, 3), q(td, ts, 1), q(td, ts, 2), q(sd, ss, 3)))
    add(u"b 数", u"- 当たり %d(%s)・外れ %d(%s)。" % (len(ids_hit), u"・".join(ids_hit), len(ids_miss), u"・".join(ids_miss)))
    lo1, hi1 = b[u"SC-1"]
    add(u"b SC-1", u"- SC-1 は段 2 の %sで、封の幅(%s 以上 %s 以下)の中。幅の端から 5 ポイント以上離れている。" % (fr(rs[2], rd), p2(lo1), p2(hi1)))
    add(u"b SC-2", u"- SC-2 は段 1 の %sで、封の上限 %s の中。段 3 では %s に上がる。" % (fr(as_[1], ad), p2(b[u"SC-2"]), rate_text(as_[3], ad)))
    add(u"b SC-3", u"- SC-3 は段 3 の %s が段 1 の %s の %d 倍以上(分子は段 3 が %d・段 1 が %d)。" % (rate_text(as_[3], ad), rate_text(as_[1], ad), b[u"SC-3"], as_[3], as_[1]))
    add(u"b SC-4", u"- SC-4a は %sで封の上限 %s の中・SC-4b は %sで封の下限 %s の上。" % (fr(gs[2], gd), p2(b[u"SC-4a"]), fr(vs[2], vd_), p2(b[u"SC-4b"])))
    add(u"b SC-5", u"- SC-5 は段 2 の差が %s ポイントで、封の %d ポイント以上の中。範囲でない札の V の止めた行 %d は、TSS %d・KAM %d・YS %d(YS は %s)。"
        % (pk(pr, u"SC-5 率の差")[SN[2]], b[u"SC-5"], ns[2], nonB[u"TSS"][1][2], nonB[u"KAM"][1][2], nonB[u"YS"][1][2], fr(nonB[u"YS"][1][2], nonB[u"YS"][0])))
    add(u"b SC-7", u"- SC-7 の分母 %d は 5 以上なので判定した(封の「測れていない」には当たらない)。" % td)
    add(u"b 欠陥", u"- 封 §4 の「SC-1 か SC-4b が下に外れたときは先に自分の欠陥を疑う」は、どちらも下に外れていないので発火しない。当たった類は 0 でない(§5)。")
    # SC-6 の段ごとの表
    for t in STAGES:
        ok = (fractions.Fraction(rs[t], rd) >= lo6) and (fractions.Fraction(as_[t], ad) <= hi6)
        add(u"s6 段 %d" % t, u"| 段 %d | %s | %s | %s |" % (t, q(rd, rs, t), q(ad, as_, t), u"満たす" if ok else u"満たさない"))
    # ---- §2 配線
    w = wire[u"TSS の行(便 RT の記録との確かめ)"]
    st = w[u"TSS の state ごとの行"]
    add(u"w TSS", u"- TSS: 引き直しの行 %d(GROUNDED %d・VALUE_MISMATCH %d・UNVERIFIABLE %d・POINTER_NOT_FOUND %d)は、便 RT の記録の段 1(後)の行 %d・state ごとの数と同じ。400 本の確かめを掛けた。"
        % (w[u"TSS の引き直しの行"], st[u"GROUNDED"], st[u"VALUE_MISMATCH"], st[u"UNVERIFIABLE"], st[u"POINTER_NOT_FOUND"], w[u"便 RT の記録の段 1(後)の行"]))
    for bb, key in ((u"KAM", u"KAM の行(前の記録との突き合わせ。止めない)"), (u"YS", u"YS の行(前の記録との突き合わせ。止めない)")):
        x = wire[key][u"全体"]
        add(u"w " + bb, u"- %s: 前の記録の行 %d・今の引き直しの行 %d・同じ鍵で同じ state の行 %d・同じ鍵で state が違う行 %d・今の引き直しにだけ在る行 %d・前の記録にだけ在る行 %d・切り出しの成否が前と違う本 × 側 %d。"
            % (bb, x[u"前の記録の行"], x[u"今の引き直しの行"], x[u"同じ鍵で同じ state の行"], x[u"同じ鍵で state が違う行"], x[u"今の引き直しにだけ在る行"], x[u"前の記録にだけ在る行"], x[u"切り出しの成否が前と違う本 × 側"]))
    bk = wire[u"本の数"]
    add(u"w 本", u"- 本の数は TSS %d・KAM %d・YS %d。" % (bk[u"TSS"], bk[u"KAM"], bk[u"YS"]))
    for bb in BATCHES:
        for s_ in UNIT_NAMES[bb]:
            x = cut[bb][s_ if s_ != u"(文の種類なし)" else MS.NO_SIDE]
            add(u"cut %s %s" % (bb, s_), u"| %s | %s | %d | %d | %d | %d |" % (bb, s_, x[u"本"], x[u"切れた"], x[u"切れない"], x[u"数の claim"]))
    for bb in BATCHES:
        x = pos[bb]
        add(u"pos " + bb, u"- %s: 位置を確かめた数の claim %d(state を問わない)・位置の字が数字 %d・符号か空白 %d・raw の claim に member の欄が在る %d・無い %d。"
            % (bb, x[u"位置を確かめた数の claim(state を問わない)"], x[u"うち pos の字が数字"], x[u"うち pos の字が符号か空白"], x[u"raw の claim に member の欄が在る"], x[u"raw の claim に member の欄が無い"]))
    # ---- §3 結んだ行の全部
    def t3(name, label, d):
        for s_ in (u"G", u"V"):
            x = d[s_]
            add(u"t3 %s %s" % (name, s_), u"| %s | %s | %d | %d | %d | %d | %d |" % ((label, s_, x[u"結んだ行"], x[u"member が空の行"]) + tuple(x[u"止めた行"][SN[t]] for t in STAGES)))
    t3(u"TSS", u"TSS", allr[u"TSS"][u"全体"])
    t3(u"KAM", u"KAM 全体", allr[u"KAM"][u"全体"])
    for s_ in UNIT_NAMES[u"KAM"]:
        t3(u"KAM " + s_, u"KAM %s" % s_, allr[u"KAM"][u"文の種類別"][s_])
    t3(u"YS", u"YS 全体", allr[u"YS"][u"全体"])
    for s_ in UNIT_NAMES[u"YS"]:
        t3(u"YS " + s_, u"YS %s" % s_, allr[u"YS"][u"節別"][s_])
    nm = dict((bb, sum(allr[bb][u"全体"][s_][u"結んだ行"] - allr[bb][u"全体"][s_][u"member が空の行"] for s_ in (u"G", u"V"))) for bb in BATCHES)
    add(u"t3 member", u"- member が入っている行(どの段でも止めない)は、結んだ行のうち TSS %d・KAM %d・YS %d。" % (nm[u"TSS"], nm[u"KAM"], nm[u"YS"]))
    # ---- §4 札つきの行
    V, G = lab[u"V の札"], lab[u"G の札(KAM・YS)"]

    def c5(x):
        return u"%d | %d | %d | %d | %d" % ((x[u"札の行"], x[u"引けた行(分母)"]) + tuple(x[u"止めた行"][SN[t]] for t in STAGES))
    for bb in list(BATCHES) + [u"合計"]:
        for key, nmk in ((u"範囲", u"範囲"), (u"範囲でない(分母から除く札は除く)", u"範囲でない"), (u"分母から除く札", u"分母から除く札")):
            add(u"v %s %s" % (bb, nmk), u"| %s | %s | %s |" % (bb, nmk, c5(V[bb][key])))
    add(u"v 引けない", u"- 引けなかった札の行(分母に入れない): V の札は TSS %d(行が無い %d・state が違う %d)・KAM %d・YS %d。G の札は KAM %d・YS %d。"
        % (V[u"TSS"][u"全体"][u"引けなかった行"], V[u"TSS"][u"全体"][u"引けなかった理由"][u"行が無い"], V[u"TSS"][u"全体"][u"引けなかった理由"][u"state が違う"],
           V[u"KAM"][u"全体"][u"引けなかった行"], V[u"YS"][u"全体"][u"引けなかった行"], G[u"KAM"][u"全体"][u"引けなかった行"], G[u"YS"][u"全体"][u"引けなかった行"]))
    add(u"v 除く", u"- 分母から除く札は TSS に %d 行(引けた行 %d)で、範囲でない札の V の分母に入れない。" % (V[u"TSS"][u"分母から除く札"][u"札の行"], V[u"TSS"][u"分母から除く札"][u"引けた行(分母)"]))
    for nmk, x in V[u"合計"][u"属性ごと"].items():
        add(u"v 属性 " + nmk, u"| %s | %s |" % (nmk, c5(x)))
    add(u"v 株", u"- 属性「1 株あたり」は、この属性に写る型が便 AT の写しの表に無い。表の 0 は作りで、測った 0 ではない。")
    for bb in (u"KAM", u"YS", u"合計"):
        for t_ in (u"a", u"b", u"c"):
            add(u"g %s %s" % (bb, t_), u"| %s | %s | %s |" % (bb, t_, c5(G[bb][u"型ごと"][t_])))
    for d_, x in G[u"合計"][u"b の違うものごと"].items():
        add(u"g 違う " + d_, u"| 違うもの | %s | %s |" % (d_, c5(x)))
    for bb in (u"KAM", u"YS", u"合計"):
        for key, nmk in ((u"b の違うものが範囲(字のとおり)", u"字のとおり"), (u"b の違うものが範囲か側(便 AT の写し)", u"便 AT の写し")):
            add(u"g 範囲 %s %s" % (bb, nmk), u"| %s | 範囲(%s) | %s |" % (bb, nmk, c5(G[bb][key])))
    # ---- §5 類ごと
    for bb in list(BATCHES) + [u"合計"]:
        for t in STAGES:
            for s_ in (u"G", u"V"):
                x = cls[bb][SN[t]][s_]
                add(u"c %s %d %s" % (bb, t, s_), u"| %s | 段 %d | %s | %d | %s |" % (bb, t, s_, x[u"止めた行"], u" | ".join(u"%d" % x[k] for k in CLASSES)))
    tg, tv = cls[u"TSS"][SN[2]][u"G"], cls[u"TSS"][SN[2]][u"V"]
    add(u"c 見出し", u"- TSS の段 2 で止めた行のうち、見出しの類 H に当たった行は G で %d/%d・V で %d/%d。段 1 から段 2 への増えは、段の決めのとおり見出しの類による。"
        % (tg[u"H"], tg[u"止めた行"], tv[u"H"], tv[u"止めた行"]))
    # ---- §6 封との差
    add(u"d1", u"- (1) 位置の欄の確かめ: 封 §2-2 は「文の字をその位置から読むと、その claim の数の字で始まる」と書いた。script は、engine の数の読みが符号と空白を数の一部に読むため、「位置から符号・空白のあとに数字が来る」ことと span の一致に読み替えた。位置の字が符号か空白の claim(state を問わない)は TSS %d・KAM %d・YS %d(§2)。当たりへの影響は、独立監査の席が別実装で全行を比べて 0 と確かめた(記録なし・監査の席の確かめ)。"
        % tuple(pos[bb][u"うち pos の字が符号か空白"] for bb in BATCHES))
    add(u"d2", u"- (2) 事業の形の「文の終わり」: 封は「文の終わり」と書いた。script は「探す字(前の字・見出し・文の全部)の終わり」と読んだ。前の字の終わりが「事業」の結んだ行(member が空)は TSS %d・KAM %d・YS %d(記録)。見出し・文の全部の終わりが「事業」の行は記録に無い。独立監査の席は該当 0 行を確かめた(記録なし・監査の席の確かめ)。"
        % tuple(pos[bb][u"前の字の終わりが「事業」の結んだ行(member が空)"] for bb in BATCHES))
    add(u"d3", u"- (3) 類 N のただし書き(N の語だけで当たった行は、pointer の字を見る条件を満たすときだけ止める)は 1 行も働かなかった(記録なし・監査の席の確かめ)。")
    add(u"d4", u"- (4) 札 b の「範囲」を 2 通り並べた: 字のとおり(違うものが範囲)は引けた行 %d で止めた行は 3 段とも %d・便 AT の写し(違うものが範囲か側)は引けた行 %d で 3 段とも %d。どちらも 0。"
        % (td, sum(ts.values()), sd, sum(ss.values())))
    add(u"d5", u"- (5) 札 b の範囲が 0 なのは語の表の結果: 行の前の字に封 §2 の表の語が無いか、「事業」の直後が封 §2 の事業の形の表に無い字だった(型。独立監査の席の確かめ・記録なし)。")
    # ---- §7 読める事
    add(u"r 範囲", u"- 読めるのは TSS の %d 本・KAM と YS の %d 本・この 3 段に限る。上場会社全体の率ではない。" % (bk[u"TSS"], bk[u"KAM"]))
    add(u"r 段 2", u"- 段 2 は、範囲の札の V %d 行のうち %d 行・範囲でない札の V %d 行のうち %d 行・札 a の G %d 行のうち %d 行を止めた。範囲と範囲でないの止める率の差は %s ポイント。"
        % (rd, rs[2], nd, ns[2], ad, as_[2], pk(pr, u"SC-5 率の差")[SN[2]]))
    add(u"r 段の増え", u"- 段 1 → 段 2 → 段 3 で止めた行の増え: 範囲の札の V は %d → %d → %d・札 a の G は %d → %d → %d。段 3 は範囲の札の V を段 2 より %d 行多く止めるが、札 a の G も段 2 より %d 行多く止める。"
        % (rs[1], rs[2], rs[3], as_[1], as_[2], as_[3], rs[3] - rs[2], as_[3] - as_[2]))
    add(u"r TSS", u"- TSS の全部の行(札は無い)の段 2 では、V の %s・G の %s を止めた。G で止めた行が正しい結びだったかは読んでいない。" % (fr(vs[2], vd_), fr(gs[2], gd)))
    add(u"r 範囲外", u"- 範囲でない札の V は段 3 まで広げても止めた行は %d(分母 %d)で、止めた行の分かれ方は YS %d・TSS %d・KAM %d。" % (ns[3], nd, nonB[u"YS"][1][3], nonB[u"TSS"][1][3], nonB[u"KAM"][1][3]))
    add(u"r 読めない", u"- 読めない事: 札の正しさ(札は AI の席 1 席が付けた)。止めた行が「止めて正しかった」か(札の在る行でしか言えない)。止めたあとに正しい fact へ結び直せるか。TSS の G で止めた行の中身。engine に入れたときの数。別の語の表での数。KAM・YS・TSS 以外の書類。")
    # ---- §8 限界
    add(u"m 1", u"- engine は変えていない。止めた数は engine の外の後付けの規則の数で、engine の旗にしたときの数ではない(engine の中では止めたあとに別の枠へ結び直す道が在りうる。それは測らない)(封 §5)。")
    add(u"m 2", u"- 読みの札は AI の席(司令塔)1 席が付けた。盲検でなく、人は読んでいない。この便は札の正しさを 1 つも確かめない。TSS の札は便 NRE の直しの前の engine の行に付けたもので、いまの engine で同じ state で引けた行だけを数えた(TSS の V の札で引けなかった行は %d)(封 §5)。"
        % V[u"TSS"][u"全体"][u"引けなかった行"])
    add(u"m 3", u"- TSS の G の行には札が無い。「正しい結びの減り」を札で言えるのは KAM と YS だけ(札 a の G は %d 行)(封 §5)。" % ad)
    add(u"m 4", u"- 手がかりの語の表は司令塔が書いた。盲検でない。別の語の表なら数は変わる(封 §5)。")
    add(u"m 5", u"- 材料は決算短信の概況の文(TSS %d 本)と有報の KAM・3 つの節(%d 本)。ほかの書類には言えない(封 §5)。" % (bk[u"TSS"], bk[u"KAM"]))
    add(u"m 6", u"- 範囲の札の V の分母 %d は TSS %d・KAM %d・YS %d で TSS に偏る。YS の %d は分母が 5 未満で率を言わない。" % (rd, rngB[u"TSS"][0], rngB[u"KAM"][0], rngB[u"YS"][0], rngB[u"YS"][0]))
    add(u"m 7", u"- 位置の欄は数の字の手前の空白・符号から始まることがある(engine の数の読みが符号と空白を数の一部に読むため)。前の字はその手前までで、空白を含まない(記録の限界)。")
    add(u"m 8", u"- 判定は司令塔(盲検でない)。封の予測も司令塔(AI の席 1 席)が書いた。")
    add(u"m 9", u"- 独立監査は、script・記録・封の門について GO。監査の席の確かめ(記録なし)は §6 に分けて書いた。")
    add(u"m 10", u"- 取り出した出力そのもの(大きい)は repo に置かない。置いたのは 1 つの記録(数・鍵・札・当たった類だけ)で、文・値・要素名・主語の語・枠の id・pointer の字・会社名・証券コード・docID を持たない。")
    # ---- §9 次
    add(u"n 全数", u"- 全数: この便の commit の前に司令塔が全数を 1 回走らせる。結果はこの文書に書かない(引き継ぎに書く)。")
    return L


NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")


def prose_clean(line):
    t = re.sub(r"`[^`]*`", u"", line)
    t = t.replace(u"sha256", u"")
    t = re.sub(r"\d{4}-\d{2}-\d{2}", u"", t)
    t = re.sub(r"\b[0-9a-f]{7,}\b", u"", t)
    t = re.sub(r"https?://\S+|\S+\.(?:md|py|json)\b", u"", t)
    t = re.sub(r"\b[A-Z]+-?\d+[A-Za-z]*\b", u"", t)
    t = re.sub(u"§[0-9\\-]+", u"", t)
    t = re.sub(u"段 \\d+", u"", t)
    t = re.sub(u"札 \\d+(・\\d+)?", u"", t)
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
    pos = [lines.index(line) for _n, line in exp if want_count[line] == 1 and lines.count(line) == 1]
    if pos != sorted(pos):
        out.append(u"文書: 組んだ行の順が決めた順と違う")
    expset = set(l for _n, l in exp)
    for ln, line in enumerate(lines, 1):
        if line in expset or not line.strip():
            continue
        if NUM_RE.search(prose_clean(line)):
            out.append(u"文書: 組んだ行にない行に数字が在る: 行 %d %s" % (ln, line[:30]))
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
    for w in TABLE_WORDS:
        if w in doc:
            out.append(u"words: 封 §2 の表の語を書いている(「封 §2 の表」と指す): %s" % w)
    for ln, line in enumerate(doc.split(u"\n"), 1):
        if KANJI_NUM_RE.search(line):
            out.append(u"words: 3 桁以上の数を漢数字で書いている: 行 %d" % ln)
    for need in (os.path.basename(SEAL_REL), SEAL_COMMIT_SHORT, RECORD_COMMIT_SHORT, os.path.basename(SCRIPT_REL), os.path.basename(RECORD_REL)) + REQUIRED_PHRASES:
        if need not in doc:
            out.append(u"words: 要点の字が無い: %s" % need)
    return out


def section(doc, head, nxt=None):
    if head not in doc:
        return u""
    t = doc[doc.index(head):]
    if nxt is not None and nxt in t[len(head):]:
        t = t[:len(head) + t[len(head):].index(nxt)]
    return t


LEAD_HEAD = u"**先に負けと限界を書く。**"
LEAD_NEXT = u"## §1 "
PINNED_SECTIONS = (
    (u"## §6 ", u"## §7 ", u"- (3) 類 N のただし書き(N の語だけで当たった行は、pointer の字を見る条件を満たすときだけ止める)は 1 行も働かなかった(記録なし・監査の席の確かめ)。"),
    (u"## §6 ", u"## §7 ", u"- (5) 札 b の範囲が 0 なのは語の表の結果: 行の前の字に封 §2 の表の語が無いか、「事業」の直後が封 §2 の事業の形の表に無い字だった(型。独立監査の席の確かめ・記録なし)。"),
    (u"## §8 ", u"## §9 ", u"- 判定は司令塔(盲検でない)。封の予測も司令塔(AI の席 1 席)が書いた。"),
    (u"## §9 ", None, u"- engine を変えるか(段 2 の規則を入れる案。人間の決定)。入れるなら別の封(未使用の材料で・盲検の語の表で)が先に要る。"),
    (u"## §9 ", None, u"- 外に書くか(人間の決定)。"),
    (u"## §9 ", None, u"- `main` へのマージ(人間の決定)。"),
)


def limits_problems(c):
    u"""要点の行が決めた節に 1 回ずつ在る。判定の語は表の行と要約が同じ向き。"""
    out = []
    lead = section(c.doc, LEAD_HEAD, LEAD_NEXT).split(u"\n")
    exp = dict(expected_lines(c))
    for k in (u"lead 判定", u"lead SC-6", u"lead SC-7", u"lead 近さ", u"lead 偏り", u"lead 盲検", u"lead engine", u"lead 読み"):
        if lead.count(exp[k]) != 1:
            out.append(u"limits: 要点の行が冒頭に 1 回ずつ無い: %s" % k)
    for head, nxt, line in PINNED_SECTIONS:
        if section(c.doc, head, nxt).split(u"\n").count(line) != 1:
            out.append(u"limits: 決めた節に決めた行が 1 回ずつ無い: %s" % line[:20])
    lines = c.doc.split(u"\n")
    vd = verdicts(c)
    for pid, v in zip(IDS, vd):
        rows = [l for l in lines if l.startswith(u"| %s |" % pid)]
        if len(rows) != 1 or not rows[0].endswith(u"| %s |" % v) or (v == HIT and MISS in rows[0]) or (v == MISS and rows[0].count(u"外れ") != 1):
            out.append(u"limits: 表の %s の行の判定の字が決め直した判定と違う" % pid)
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
    for need in (u"## §4 ", u"| SC-1 |", u"| SC-7 |", u"30% 以上 65% 以下", u"10% 以下", u"2 倍以上", u"15% 以下", u"20% 以上", u"10 ポイント以上低い", u"50% 以上止め", u"5% 以下",
                 u"1 行以上止める", u"5 行未満", u"SC-6 が外れた(満たす段が在る)ときだけ", u"## §5 "):
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


def at(c, path):
    node = c.rec
    for k in path[:-1]:
        node = node[k]
    return node, path[-1]


def bump(path, delta=1):
    u"""記録(c.rec)の入れ子の数を ``delta`` 変える。path は key の並び。"""
    def fn(c):
        node, k = at(c, path)
        node[k] += delta
    return fn


def set_at(path, value):
    def fn(c):
        node, k = at(c, path)
        node[k] = value
    return fn


def line_mut(name, old, new):
    u"""組んだ行 ``name`` の字の ``old`` を ``new`` に変えて文書に戻す(行の字は記録から組み直して探す)。"""
    def fn(c):
        line = dict(expected_lines(Ctx()))[name]
        assert old in line, (name, old)
        assert line in c.doc, name
        c.doc = c.doc.replace(line, line.replace(old, new, 1), 1)
    return fn


def doc_line_edit(name, new):
    def fn(c):
        old = dict(expected_lines(Ctx()))[name]
        assert old in c.doc, name
        c.doc = c.doc.replace(old, new, 1)
    return fn


def swap_lines(a, b):
    def fn(c):
        exp = dict(expected_lines(Ctx()))
        la, lb = exp[a], exp[b]
        assert la in c.doc and lb in c.doc
        c.doc = c.doc.replace(la, u"\x00A").replace(lb, la).replace(u"\x00A", lb)
    return fn


def pick(c, which, n, stopped, stage=None):
    u"""判定の行の集まり(``which``)のうち、止めている(``stopped`` が True)か止めていない行を先頭から ``n`` 行返す。"""
    f = Facts(c)
    pools = {
        u"rng": f.sum_of(f.rng, BATCHES), u"non": f.sum_of(f.non, BATCHES), u"a": f.sum_of(f.a, (u"KAM", u"YS")),
        u"tss_g": f.tss_g, u"tss_v": f.tss_v, u"b_rng": f.sum_of(f.b_rng, (u"KAM", u"YS")),
        u"rng_kam": f.rng[u"KAM"], u"rng_ys": f.rng[u"YS"], u"rng_tss": f.rng[u"TSS"]}
    rows = [r for r in pools[which] if is_stop(r, stage) == stopped]
    assert len(rows) >= n, (which, stopped, stage, len(rows), n)
    return rows[:n]


def unstop_first_at(which, stage, n):
    u"""段 ``stage`` で初めて止まる行(段 ``stage - 1`` では止まらない行)の止めを ``n`` 行はずす(段 1 の数を動かさず段 ``stage`` だけを減らす)。"""
    def fn(c):
        f = Facts(c)
        pools = {u"a": f.sum_of(f.a, (u"KAM", u"YS"))}
        rows = [r for r in pools[which] if is_stop(r, stage) and not is_stop(r, stage - 1)]
        assert len(rows) >= n, (which, stage, len(rows), n)
        for r in rows[:n]:
            r[6 + stage] = u""
    return fn


def unstop(which, stage, n):
    u"""段 ``stage`` の止めを ``n`` 行はずす(段の包含のため、段 ``stage`` 以下も空にする)。記録の行を直接変える(Ctx の写しの行は ``Facts`` の行と同じ object)。"""
    def fn(c):
        for r in pick(c, which, n, True, stage):
            for t in range(1, stage + 1):
                r[6 + t] = u""
    return fn


def stop(which, stage, n):
    u"""段 ``stage`` で止めていない行を ``n`` 行止める(段 ``stage`` 以上にも同じ類の字を置く)。"""
    def fn(c):
        for r in pick(c, which, n, False, stage):
            for t in range(stage, 4):
                r[6 + t] = u"S"
    return fn


def check_problems(check, c):
    return guard(CHECKS[check], c)


# a sha
M(u"a1 記録の 1 byte", u"sha", set_text(RECORD_REL, lambda t: t + b" "))
M(u"a2 script の 1 byte", u"sha", set_text(SCRIPT_REL, lambda t: t[:-1] + b"#"))
M(u"a3 封の門の 1 byte", u"sha", set_text(SEAL_GATE_REL, lambda t: t + b"\n"))
# b 記録
M(u"b1 記録の結んだ行の数を 1 つ変える(TSS の G の段 2)", u"record", lambda c: bump([K_ALL, u"TSS", u"全体", u"G", u"止めた行", u"段 2"])(c))
M(u"b2 記録の予測の欄(SC-4b の分子)を 1 つ変える", u"record", lambda c: bump([K_PRED, [k for k in c.rec[K_PRED] if k.startswith(u"SC-4b ")][0], u"段 2", u"分子"])(c))
M(u"b3 記録の行の 1 つの当たった類を空にする", u"record", lambda c: [r for r in c.rec[u"行"] if r[8] != u""][0].__setitem__(8, u""))
M(u"b4 記録に文・値の字を足す", u"record", lambda c: c.rec.__setitem__(u"漏れ", u"売上高は前期比 12.3 億円の増加となりました。"))
M(u"b5 記録の配線の確認の数を 1 つ変える(TSS の引き直しの行)", u"record", lambda c: bump([K_WIRE, u"TSS の行(便 RT の記録との確かめ)", u"TSS の引き直しの行"])(c))
M(u"b6 記録の入力の sha256 を 1 つ変える", u"record", set_at([u"入力", 0, u"sha256"], u"0" * 64))
M(u"b7 記録の札つきの行の数を 1 つ変える(範囲の札の V の止めた行)", u"record", lambda c: bump([K_LABEL, u"V の札", u"合計", u"範囲", u"止めた行", u"段 2"])(c))
M(u"b8 記録の当たった類の数を 1 つ変える(段 2 の H)", u"record", lambda c: bump([K_CLASS, u"TSS", u"段 2", u"V", u"H"])(c))
M(u"b9 記録の位置の確かめの数を 1 つ変える(符号か空白)", u"doc", lambda c: bump([K_WIRE, K_POS, u"TSS", u"うち pos の字が符号か空白"])(c))
M(u"b10 記録の最上位に欄を足す", u"record", lambda c: c.rec.__setitem__(u"追記", 1))
M(u"b11 記録の行の鍵を 1 つ重ねる", u"record", lambda c: c.rec[u"行"].append(list(c.rec[u"行"][-1])))
# c 文書の数・表・散文
M(u"c1 表の実測の分子を 1 つ変える(SC-1)", u"doc", line_mut(u"table SC-1", u"53/104", u"54/104"))
M(u"c2 表の判定の当たりと外れを入れ替える(SC-6)", u"limits", lambda c: setattr(c, "doc", re.sub(r"(\| SC-6 \|.*?\| )\*\*外れ\*\* \|", r"\1当たり |", c.doc, count=1)))
M(u"c3 表の判定の当たりと外れを入れ替える(SC-1)", u"limits", lambda c: setattr(c, "doc", re.sub(r"(\| SC-1 \|.*?\| )当たり \|", r"\1**外れ** |", c.doc, count=1)))
M(u"c3b 表の判定の当たりと外れを入れ替える(SC-7)", u"limits", lambda c: setattr(c, "doc", re.sub(r"(\| SC-7 \|.*?\| )\*\*外れ\*\* \|", r"\1当たり |", c.doc, count=1)))
M(u"c3c 表の判定の当たりと外れを入れ替える(SC-4b)", u"limits", lambda c: setattr(c, "doc", re.sub(r"(\| SC-4b \|.*?\| )当たり \|", r"\1**外れ** |", c.doc, count=1)))
M(u"c4 要約の本数を変える(当たり 6・外れ 2)", u"doc", doc_replace(u"(当たり 6・外れ 2)", u"(当たり 7・外れ 1)"))
M(u"c5 散文に記録に無い数を足す(組んだ行にない行)", u"doc", doc_append(u"\n- 追記: 12345 行。\n"))
M(u"c5b 散文に 1 桁の数を足す(組んだ行にない行)", u"doc", doc_append(u"\n- 追記: 0 行。\n"))
M(u"c6 結んだ行の表の数を 1 つ変える(TSS の V の段 2)", u"doc", line_mut(u"t3 TSS V", u"| 616 |", u"| 617 |"))
M(u"c7 結んだ行の表の member が空の数を変える(KAM 全体の G)", u"doc", line_mut(u"t3 KAM G", u"| 172 | 164 |", u"| 172 | 163 |"))
M(u"c8 札の表の数を変える(範囲の札の V の合計)", u"doc", line_mut(u"v 合計 範囲", u"| 105 | 104 |", u"| 105 | 103 |"))
M(u"c9 札の表の止めた行を変える(KAM の範囲でない)", u"doc", line_mut(u"v KAM 範囲でない", u"| 12 | 12 | 0 | 0 | 0 |", u"| 12 | 12 | 1 | 0 | 0 |"))
M(u"c10 G の札の表の数を変える(a の合計)", u"doc", line_mut(u"g 合計 a", u"| 214 | 214 | 7 | 9 | 33 |", u"| 214 | 214 | 7 | 9 | 34 |"))
M(u"c11 G の札の表の数を変える(b の合計)", u"doc", line_mut(u"g 合計 b", u"| 27 | 27 | 0 | 1 | 1 |", u"| 27 | 27 | 0 | 0 | 1 |"))
M(u"c12 類の表の数を変える(TSS の段 2 の V の H)", u"doc", line_mut(u"c TSS 2 V", u"| 616 | 377 | 8 | 29 | 0 | 0 | 414 |", u"| 616 | 377 | 8 | 29 | 0 | 0 | 413 |"))
M(u"c13 属性の表の数を変える(範囲)", u"doc", line_mut(u"v 属性 範囲", u"| 105 | 104 | 38 | 53 | 61 |", u"| 105 | 104 | 38 | 52 | 61 |"))
M(u"c14 組んだ行を消す(位置の確かめ KAM)", u"doc", doc_line_edit(u"pos KAM", u""))
M(u"c15 禁止語を doc の check にも通す(証明した)", u"words", doc_append(u"\n証明" + u"した。\n"))
M(u"c16 散文の数を変える(読める事の段 2)", u"doc", line_mut(u"r 段 2", u"範囲の札の V 104 行のうち 53 行", u"範囲の札の V 104 行のうち 54 行"))
M(u"c17 限界の節の数を変える(材料の本数)", u"doc", line_mut(u"m 5", u"TSS 400 本", u"TSS 401 本"))
M(u"c18 全数の行に結果を書く", u"doc", doc_replace(u"結果はこの文書に書かない(引き継ぎに書く)。", u"結果は全部緑で 0 件だった(引き継ぎに書く)。"))
M(u"c19 表の「封の字」を変える(SC-1 の幅)", u"doc", doc_replace(u"30% 以上 65% 以下", u"30% 以上 80% 以下"))
M(u"c20 行の順を入れ替える(要約の 2 行)", u"doc", swap_lines(u"lead SC-6", u"lead SC-7"))
M(u"c21 要約の率を変える(SC-6 の段 2)", u"doc", line_mut(u"lead SC-6", u"53/104(51.0%)", u"53/104(52.0%)"))
M(u"c22 要約の偏りの数を変える(YS)", u"doc", line_mut(u"lead 偏り", u"YS 4", u"YS 5"))
M(u"c23 配線の行の数を変える(KAM の行)", u"doc", line_mut(u"w KAM", u"今の引き直しの行 788", u"今の引き直しの行 787"))
M(u"c24 近さの行の数を変える", u"doc", line_mut(u"lead 近さ", u"あと 2 行少なければ", u"あと 3 行少なければ"))
M(u"c25 SC-5 の差の字を変える", u"doc", line_mut(u"table SC-5", u"差 48.06 ポイント", u"差 48.60 ポイント"))
M(u"c26 SC-7 の分母の字を変える", u"doc", line_mut(u"table SC-7", u"段 3 0/15(0.0%)", u"段 3 0/14(0.0%)"))
M(u"c27 SC-6 の段の表の数を変える(段 2)", u"doc", line_mut(u"s6 段 2", u"53/104(51.0%)", u"53/104(51.1%)"))
M(u"c28 切り出しの表の数を変える(KAM の単体)", u"doc", line_mut(u"cut KAM 単体", u"| 192 | 9 |", u"| 191 | 9 |"))
M(u"c29 封との差の数を変える((1) の TSS)", u"doc", line_mut(u"d1", u"TSS 716", u"TSS 715"))
M(u"c30 封との差の数を変える((4) の分母)", u"doc", line_mut(u"d4", u"引けた行 15", u"引けた行 14"))
M(u"c31 SC-2 の行の数を変える(KAM)", u"doc", line_mut(u"table SC-2", u"KAM 5/89", u"KAM 5/90"))
M(u"c32 SC-4a の行の数を変える", u"doc", line_mut(u"table SC-4a", u"275/6720", u"275/6721"))
M(u"c33 SC-3 の行の数を変える(段 3)", u"doc", line_mut(u"table SC-3", u"33/214", u"32/214"))
M(u"c34 member が入っている行の数を変える", u"doc", line_mut(u"t3 member", u"YS 54", u"YS 53"))
M(u"c35 引けなかった札の行の数を変える", u"doc", line_mut(u"v 引けない", u"V の札は TSS 1", u"V の札は TSS 2"))
M(u"c36 見出しの類の数を変える", u"doc", line_mut(u"c 見出し", u"V で 414/616", u"V で 415/616"))
# d 判定(記録の行を変えて、判定を動かす。集計の欄は触らない)
M(u"d1 範囲の札の V の止めを 30 行はずして SC-1 を幅の下に動かす", u"judge", unstop(u"rng", 2, 30))
M(u"d2 範囲の札の V の止めを 16 行足して SC-1 を幅の上に動かす", u"judge", stop(u"rng", 2, 16))
M(u"d3 札 a の G の止めを 20 行足して SC-2 を外れに動かす", u"judge", stop(u"a", 1, 20))
M(u"d4 札 a の G の段 3 で初めて止まる行 24 行の止めをはずして SC-3 を外れに動かす(段 1 は 7 のまま)", u"judge", unstop_first_at(u"a", 3, 24))
M(u"d5 TSS の G の段 2 の止めを 800 行足して SC-4a を外れに動かす", u"judge", stop(u"tss_g", 2, 800))
M(u"d6 TSS の V の段 2 の止めを 300 行はずして SC-4b を外れに動かす", u"judge", unstop(u"tss_v", 2, 300))
M(u"d7 範囲でない札の V の段 2 の止めを 30 行足して SC-5 を外れに動かす", u"judge", stop(u"non", 2, 30))
M(u"d8 範囲の札の V の止めを 2 行はずして SC-6 を当たりに動かす(段 2 が 50% を割る)", u"judge", unstop(u"rng", 2, 2))
M(u"d9 札 a の G の段 2 の止めを 2 行足して SC-6 を当たりに動かす(段 2 が 5% を超える)", u"judge", stop(u"a", 2, 2))
M(u"d10 札 b の範囲の行を 1 行止めて SC-7 を当たりに動かす", u"judge", stop(u"b_rng", 3, 1))
M(u"d11 判定の欄(SC-1 の分子)を 1 つ変える", u"judge", lambda c: bump([K_PRED, [k for k in c.rec[K_PRED] if k.startswith(u"SC-1 ")][0], u"3 便の合計", u"段 2", u"分子"])(c))
M(u"d12 判定の欄(SC-5 の率の差)を変える", u"judge", set_at([K_PRED, u"SC-5 率の差(ポイント。範囲の率 − 範囲でない率。小数 2 桁の字)", u"段 2"], u"48.07"))
M(u"d13 判定の欄(SC-7 の参考の分母)を 1 つ変える", u"judge", lambda c: bump([K_PRED, u"SC-7 参考(違うものが範囲か側。便 AT の写し)", u"段 3", u"分母"])(c))
M(u"d14 判定の欄(分母の確かめ)を 1 つ変える", u"judge", bump([K_PRED, u"分母の確かめ(V の札 3 便の合計・G の札 KAM と YS の合計・札の行の数)", u"G の札の行(引けた)"]))
# e 語
M(u"e1 禁止語(ハルシネーション)", u"words", doc_append(u"\nハルシ" + u"ネーション\n"))
M(u"e2 会社名らしい字", u"words", doc_append(u"\n株式会社\n"))
M(u"e3 3 桁以上の漢数字", u"words", doc_append(u"\n二百社\n"))
M(u"e4 docID の形", u"words", doc_append(u"\nS100" + u"AB12\n"))
M(u"e5 要点の字を消す(外れは外れとして残す)", u"words", doc_replace(u"外れは外れとして残す", u"外れを残す", True))
M(u"e6 封の commit を言わない", u"words", doc_replace(u"5b77133b", u"0000000", True))
M(u"e7 禁止語(人の目)", u"words", doc_append(u"\n人の" + u"目で読んだ。\n"))
M(u"e8 要点の字を消す(外れ)", u"words", doc_replace(u"外れ", u"はずれ", True))
M(u"e9 記録の commit を言わない", u"words", doc_replace(u"5b7c7339", u"0000000", True))
M(u"e10 要点の字を消す(別の封)", u"words", doc_replace(u"別の封(未使用の材料で・盲検の語の表で)", u"別の封", True))
M(u"e11 要素名の形の字", u"words", doc_append(u"\njppfs_cor:NetSales\n"))
M(u"e12 封 §2 の表の語を書く(S の類)", u"words", doc_append(u"\n" + u"セグ" + u"メント" + u"\n"))
M(u"e13 封 §2 の表の語を書く(K の類)", u"words", doc_append(u"\n" + u"子" + u"会社" + u"\n"))
M(u"e14 pointer の字を書く", u"words", doc_append(u"\n" + u"NonConsol" + u"idated" + u"\n"))
# 要点の文
M(u"l1 要約の SC-6 の行を変える", u"limits", doc_line_edit(u"lead SC-6", u"- SC-6 は当たり。"))
M(u"l2 §6 の要点の行を変える((3))", u"limits", doc_replace(u"は 1 行も働かなかった(記録なし・監査の席の確かめ)。", u"は 1 行だけ働いた(記録なし・監査の席の確かめ)。"))
M(u"l3 §6 の要点の行を変える((5)の型の字)", u"limits", doc_replace(u"(型。独立監査の席の確かめ・記録なし)", u""))
M(u"l4 要約の読みの行を変える", u"limits", doc_line_edit(u"lead 読み", u"- 段 2 の規則を engine に入れる。"))
M(u"l5 判定は司令塔の行を変える", u"limits", doc_replace(u"- 判定は司令塔(盲検でない)。封の予測も司令塔(AI の席 1 席)が書いた。", u"- 判定は独立監査。"))
M(u"l6 SC-6 の表の行から外れを消す", u"limits", lambda c: setattr(c, "doc", re.sub(r"(\| SC-6 \|.*?\| )\*\*外れ\*\* \|", r"\1判定しない |", c.doc, count=1)))
M(u"l7 次の節の人間の決定の行を消す", u"limits", doc_replace(u"- 外に書くか(人間の決定)。", u"- 外に書く。"))
M(u"l8 要約の近さの行を変える", u"limits", doc_line_edit(u"lead 近さ", u"- SC-6 の段 2 は境から遠い。"))
M(u"l9 要約の偏りの行を変える", u"limits", doc_line_edit(u"lead 偏り", u"- 偏りは無い。"))
M(u"l10 要約の盲検の行を変える", u"limits", doc_line_edit(u"lead 盲検", u"- 語の表は盲検である。"))
# f 封
M(u"f1 封の SC-1 の字を替える(根の字)", u"seal", seal_replace(u"30% 以上 65% 以下", u"30% 以上 90% 以下"))
M(u"f2 封の読み方の決めの字を替える", u"seal", seal_replace(u"SC-6 が外れた(満たす段が在る)ときだけ", u"SC-6 が当たったときだけ"))
M(u"f3 封の文の途中の 1 字", u"frozen", seal_replace(u"0 USD(LLM の席を呼ばない)", u"0 USD(LLM の席を呼ぶ)"))
M(u"f4 封の SC-1 の境を替える(判定が外れに動く)", u"judge", seal_replace(u"30% 以上 65% 以下", u"52% 以上 65% 以下"))
M(u"f5 封の SC-6 の境を替える(判定が当たりに動く)", u"judge", seal_replace(u"を 50% 以上止め", u"を 52% 以上止め"))
M(u"f6 封の SC-2 の境を替える(判定が外れに動く)", u"judge", seal_replace(u"のうち止めるのは 10% 以下", u"のうち止めるのは 3% 以下"))
M(u"f7 封の SC-7 の測れない境を替える(判定が測れていないに動く)", u"judge", seal_replace(u"分母が 5 行未満", u"分母が 20 行未満"))
M(u"f8 封の SC-4b の境を替える(判定が外れに動く)", u"judge", seal_replace(u"止めるのは 20% 以上", u"止めるのは 40% 以上"))
M(u"f9 封の SC-5 の境を替える(判定が外れに動く)", u"judge", seal_replace(u"10 ポイント以上低い", u"50 ポイント以上低い"))
M(u"f10 封の SC-3 の倍の境を替える(判定が外れに動く)", u"judge", seal_replace(u"段 1 の率の 2 倍以上", u"段 1 の率の 9 倍以上"))
M(u"f11 封の SC-4a の境を替える(判定が外れに動く)", u"judge", seal_replace(u"止めるのは 15% 以下", u"止めるのは 3% 以下"))
M(u"f12 封の SC-6 の G の境を替える(判定が当たりに動く)", u"judge", seal_replace(u"札 a の G の行を止めるのは 5% 以下", u"札 a の G の行を止めるのは 4% 以下"))
M(u"f13 封の SC-7 の止める行の境を替える(判定が当たりに動く)", u"judge", seal_replace(u"段 3 は 1 行以上止める", u"段 3 は 0 行以上止める"))


# ======================================================================================================
# 試験
class RealRecordsTest(unittest.TestCase):
    def test_a_1_the_record_the_script_and_the_seal_gate_equal_the_pinned_sha256(self):
        self.assertEqual([], sha_problems(Ctx().texts))

    def test_a_2_the_pinned_sha256_equal_the_record_header(self):
        c = Ctx()
        self.assertEqual(SHA_PIN[SCRIPT_REL], c.rec[u"この script の sha256"])
        self.assertEqual(SEAL_COMMIT_SHORT, c.rec[u"封の commit"])

    def test_b_1_the_record_equals_the_recount_from_its_rows(self):
        self.assertEqual([], record_problems(Ctx()))

    def test_c_1_the_document_lines_equal_the_lines_rebuilt_from_the_record(self):
        self.assertEqual([], doc_problems(Ctx()))

    def test_c_2_the_rebuilt_lines_are_the_ones_read_from_the_record_by_hand(self):
        c = Ctx()
        exp = dict(expected_lines(c))
        self.assertIn(u"53/104(51.0%)(段 1 38/104(36.5%)・段 3 61/104(58.7%)) | 当たり |", exp[u"table SC-1"])
        self.assertIn(u"7/214(3.3%)(KAM 5/89(5.6%)・YS 2/125(1.6%)", exp[u"table SC-2"])
        self.assertIn(u"段 3 33/214(15.4%)・段 1 7/214(3.3%) | 当たり |", exp[u"table SC-3"])
        self.assertIn(u"275/6720(4.1%) | 当たり |", exp[u"table SC-4a"])
        self.assertIn(u"616/1858(33.2%) | 当たり |", exp[u"table SC-4b"])
        self.assertIn(u"範囲でない 2/69(2.9%)・範囲 53/104(51.0%)・差 48.06 ポイント | 当たり |", exp[u"table SC-5"])
        self.assertIn(u"満たす段は段 2(53/104(51.0%) と 9/214(4.2%)) | **外れ** |", exp[u"table SC-6"])
        self.assertIn(u"段 3 0/15(0.0%)(段 1 0/15(0.0%)・段 2 0/15(0.0%)。便 AT の写しの読みは段 3 0/21(0.0%)) | **外れ** |", exp[u"table SC-7"])
        self.assertIn(u"| TSS | V | 1858 | 1858 | 402 | 616 | 724 |", exp[u"t3 TSS V"])
        self.assertIn(u"| KAM 全体 | G | 172 | 164 | 7 | 7 | 34 |", exp[u"t3 KAM G"])
        self.assertIn(u"| YS 全体 | G | 266 | 212 | 2 | 6 | 26 |", exp[u"t3 YS G"])
        self.assertIn(u"| 合計 | 範囲 | 105 | 104 | 38 | 53 | 61 |", exp[u"v 合計 範囲"])
        self.assertIn(u"| 合計 | a | 214 | 214 | 7 | 9 | 33 |", exp[u"g 合計 a"])
        self.assertIn(u"| 合計 | 段 2 | V | 629 | 381 | 8 | 38 | 0 | 0 | 416 |", exp[u"c 合計 2 V"])
        self.assertIn(u"あと 2 行少なければ 50% を下回り", exp[u"lead 近さ"])
        self.assertIn(u"あと 2 行多ければ 5% を超える", exp[u"lead 近さ"])
        self.assertIn(u"TSS 716・KAM 8・YS 25", exp[u"d1"])

    def test_d_1_the_judgement_is_redone_from_the_seal_text_and_the_record_rows(self):
        self.assertEqual([], judge_problems(Ctx()))

    def test_d_2_the_real_judgement_is_six_hits_and_two_misses(self):
        c = Ctx()
        self.assertEqual([i for i, v in zip(IDS, verdicts(c)) if v == MISS], [u"SC-6", u"SC-7"])
        self.assertEqual([i for i, v in zip(IDS, verdicts(c)) if v == HIT], [u"SC-1", u"SC-2", u"SC-3", u"SC-4a", u"SC-4b", u"SC-5"])

    def test_d_3_the_bounds_are_read_from_the_seal_text(self):
        F = fractions.Fraction
        self.assertEqual(dict(seal_bounds(Ctx().seal)), {
            u"SC-1": (F(30, 100), F(65, 100)), u"SC-2": F(10, 100), u"SC-3": 2, u"SC-3 段 1 が 0": 1, u"SC-4a": F(15, 100), u"SC-4b": F(20, 100),
            u"SC-5": 10, u"SC-6": (F(50, 100), F(5, 100)), u"SC-7": 1, u"SC-7 測れない": 5})

    def test_d_4_the_numbers_of_the_judgement_are_counted_from_the_rows_and_labels_by_hand(self):
        n = numbers(Facts(Ctx()))
        self.assertEqual(n[u"rng"], (104, {1: 38, 2: 53, 3: 61}))
        self.assertEqual(n[u"non"], (69, {1: 2, 2: 2, 3: 3}))
        self.assertEqual(n[u"a"], (214, {1: 7, 2: 9, 3: 33}))
        self.assertEqual(n[u"tss_g"], (6720, {1: 241, 2: 275, 3: 434}))
        self.assertEqual(n[u"tss_v"], (1858, {1: 402, 2: 616, 3: 724}))
        self.assertEqual(n[u"b_rng"], (15, {1: 0, 2: 0, 3: 0}))
        self.assertEqual(n[u"b_side"], (21, {1: 0, 2: 0, 3: 0}))

    def test_d_5_sc6_is_met_by_stage_two_only_and_stage_two_is_close_to_both_edges(self):
        c = Ctx()
        self.assertEqual(direction(c), (True,) * 6)
        self.assertEqual(satisfied_stages(c), [2])
        self.assertEqual(bias_problems(c), [])
        self.assertEqual(slack(c), (1, 1))

    def test_d_6_the_labels_are_422_rows_and_the_unmatched_one_is_a_tss_v(self):
        f = Facts(Ctx())
        self.assertEqual(sum(f.v_label_n.values()), 175)
        self.assertEqual(sum(f.g_label_n.values()), 247)
        self.assertEqual(sum(len(f.v[b]) for b in BATCHES), 174)
        self.assertEqual(len(f.v[u"TSS"]), 119)

    def test_e_1_the_words_are_clean(self):
        self.assertEqual([], words_problems(Ctx()))

    def test_e_2_the_seal_has_the_texts_the_document_roots_on(self):
        self.assertEqual([], seal_text_problems(Ctx()))

    def test_e_3_the_lead_and_the_pinned_lines_are_in_their_sections(self):
        self.assertEqual([], limits_problems(Ctx()))

    def test_e_4_every_line_with_a_digit_is_a_rebuilt_line_and_the_free_lines_have_no_digit(self):
        c = Ctx()
        expset = set(l for _n, l in expected_lines(c))
        free = [l for l in c.doc.split(u"\n") if l.strip() and l not in expset]
        self.assertTrue(all(not NUM_RE.search(prose_clean(l)) for l in free))
        self.assertGreaterEqual(len(expset), 150)

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
        c.rec[K_ALL][u"TSS"][u"全体"][u"G"][u"結んだ行"] = 1
        c.rec[u"行"][0][8] = u"x"
        c.doc = u"x"
        self.assertNotEqual(1, Ctx().rec[K_ALL][u"TSS"][u"全体"][u"G"][u"結んだ行"])
        self.assertNotEqual(u"x", Ctx().rec[u"行"][0][8])
        self.assertNotEqual(u"x", Ctx().doc)
        self.assertEqual(before, dict((rel, hashlib.sha256(read_bytes(rel)).hexdigest()) for rel in rels))

    def test_m_4_the_mutation_table_covers_every_check_and_every_effect_named_in_the_brief(self):
        self.assertEqual(set(CHECKS), set(ch for _l, ch, _f in MUTATIONS))
        labels = u"\n".join(l for l, _c, _f in MUTATIONS)
        for need in (u"記録の 1 byte", u"script の 1 byte", u"表の実測の分子", u"当たりと外れを入れ替える", u"散文に記録に無い数", u"散文の数", u"禁止語", u"漢数字", u"要点の",
                     u"封の文の途中の 1 字", u"SC-1 を幅の下", u"SC-1 を幅の上", u"SC-2 を外れに", u"SC-3 を外れに", u"SC-4a を外れに", u"SC-4b を外れに", u"SC-5 を外れに",
                     u"SC-6 を当たりに", u"SC-7 を当たりに", u"測れていないに動く", u"行の順を入れ替える", u"判定の欄", u"封 §2 の表の語", u"当たった類"):
            self.assertIn(need, labels)
        self.assertGreaterEqual(len(MUTATIONS), 90)

    def test_m_5_a_miss_turned_to_a_hit_is_caught_by_the_judge_and_not_only_by_the_table(self):
        c = Ctx()
        unstop(u"rng", 2, 2)(c)                                                    # SC-6 が当たりに動く。文書の表は外れのまま
        jd = dict(judge(c))
        self.assertTrue(jd[u"SC-6"])
        self.assertNotEqual([], judge_problems(c))

    def test_m_6_the_judge_follows_the_seal_bounds_not_a_pinned_number(self):
        c = Ctx()
        c.seal = c.seal.replace(u"30% 以上 65% 以下", u"20% 以上 65% 以下", 1)
        self.assertTrue(dict(judge(c))[u"SC-1"])
        c = Ctx()
        c.seal = c.seal.replace(u"30% 以上 65% 以下", u"52% 以上 65% 以下", 1)
        self.assertFalse(dict(judge(c))[u"SC-1"])                                  # 53/104 は 51.0%。52% 以上の幅では外れ
        c.seal = c.seal.replace(u"52% 以上 65% 以下", u"50% 以上 65% 以下", 1)
        self.assertTrue(dict(judge(c))[u"SC-1"])

    def test_m_7_the_judge_compares_exact_fractions_at_the_sc6_edges(self):
        u"""段 2 の範囲の札の V は 53/104。1 行はずして 52/104 は 50% ちょうど(満たす)・2 行はずして 51/104 は 50% 未満(満たさない)。札 a の G は 9/214: 10/214 は 5% 以下・11/214 は 5% 超。"""
        c = Ctx()
        unstop(u"rng", 2, 1)(c)
        self.assertEqual(satisfied_stages(c), [2])
        self.assertFalse(dict(judge(c))[u"SC-6"])
        unstop(u"rng", 2, 1)(c)
        self.assertEqual(satisfied_stages(c), [])
        self.assertTrue(dict(judge(c))[u"SC-6"])
        c = Ctx()
        stop(u"a", 2, 1)(c)
        self.assertEqual(satisfied_stages(c), [2])
        self.assertFalse(dict(judge(c))[u"SC-6"])
        stop(u"a", 2, 1)(c)
        self.assertEqual(satisfied_stages(c), [])
        self.assertTrue(dict(judge(c))[u"SC-6"])

    def test_m_8_the_judge_has_eight_items_and_no_system_wide_run(self):
        c = Ctx()
        self.assertEqual(len(judge(c)), 8)
        self.assertEqual([i for i, _ok in judge(c)], list(IDS))

    def test_m_9_sc7_with_a_small_denominator_is_not_measured_and_gets_no_hit_or_miss(self):
        c = Ctx()
        c.seal = c.seal.replace(u"分母が 5 行未満", u"分母が 20 行未満", 1)
        self.assertEqual(verdicts(c)[7], UNMEASURED)

    def test_m_10_sc3_with_a_zero_stage_one_uses_the_row_count_rule(self):
        c = Ctx()
        for r in pick(c, u"a", 7, True, 1):
            r[7] = u""
        self.assertEqual(numbers(Facts(c))[u"a"][1][1], 0)
        self.assertTrue(dict(judge(c))[u"SC-3"])                                   # 段 1 が 0 なら段 3 が 1 行以上
        for r in pick(c, u"a", 33, True, 3):
            r[9] = u""
        self.assertFalse(dict(judge(c))[u"SC-3"])


    def test_m_11_the_bias_claims_are_checked_and_turn_red_when_kam_alone_reaches_half(self):
        c = Ctx()
        self.assertEqual([], bias_problems(c))
        stop(u"rng_kam", 2, 4)(c)                                                  # KAM は 13/25 = 52.0%(50% 以上)
        self.assertNotEqual([], bias_problems(c))
        c = Ctx()
        unstop(u"rng_tss", 2, 20)(c)                                               # TSS は 22/75 = 29.3%(50% 未満)
        self.assertNotEqual([], bias_problems(c))


class WiringTest(unittest.TestCase):
    def test_n_1_this_gate_carries_no_docid_and_no_key(self):
        src = read(GATE_REL)
        for bad in (u"ANTHRO" + u"PIC", u"API_" + u"KEY", u"url" + u"lib", u"sock" + u"et"):
            self.assertNotIn(bad, src)
        self.assertIsNone(DOCID_RE.search(src))

    def test_n_2_this_gate_does_not_widen_the_boundary_import_list(self):
        with io.open(os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py"), encoding="utf-8") as fh:
            t = fh.read()
        self.assertNotIn(u"scope_cond", t)

    def test_n_3_this_gate_does_not_use_the_reserved_names(self):
        self.assertEqual([], SG.reserved_problems(rel=GATE_REL))

    def test_n_4_this_gate_leaves_sys_modules_as_it_found_them(self):
        before = dict(sys.modules)
        mod = load_module(GATE_REL, "sc_result_gate_sysmodules_check")
        changed = [k for k, v in before.items() if sys.modules.get(k) is not v]
        self.assertEqual([], changed)
        del mod


if __name__ == "__main__":
    unittest.main()
