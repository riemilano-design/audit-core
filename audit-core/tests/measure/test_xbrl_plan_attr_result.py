# -*- coding: utf-8 -*-
"""結果の門: 封 docs/XBRL_PLAN_ATTR_SEAL_2026-11-19.md(e69b733c)の結果の文書 docs/XBRL_PLAN_ATTR_RESULT_2026-11-19.md。

封の門 ``test_xbrl_plan_attr_seal.py`` の次の段。**追跡されている記録・script・封・結果の文書と git の履歴だけを読む**(材料は読まない。全数の作り直しは走らせない)。

縛るもの(検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表で 1 つずつ。木の file は変異させず、``Ctx`` の写しに当てる)
 a script・記録・封の門の sha256(字で留める)
 b 記録の中の整合: 封の門の ``record_problems``(行からの数え直し・予測の判定に要る数の作り直し・文や値の漏れ)+ 最上位の欄の一覧
 c 結果の文書の数: 数字を含む行は全部、記録から組んだ行と字で同じ(組んだ行は文書に決めた回数だけ在り、順も同じ)。そのどれにも当たらない行に数字が在れば赤
 d 予測 PA-1〜PA-8(PA-7 は a・b。計 9 本)の判定を、封の予測の字から取った境と記録の行・読みの札(止めた行を行から数える。便 SC の段 2 の側は便 SC の記録の行から)から
   門が自分で決め直して、記録の「予測の判定に要る数」・文書の表と同じ・字で留めた判定と同じ。境への近さの向き・あと何行で境をまたぐかも同じ
 e 文書に禁止語・会社名らしい字・docID・3 桁以上の漢数字・要素名や pointer の形・封 §2 の表の語が無い・要点の字が在る
 f 封が commit から 1 字も変わっていない・順序(commit の順。未 commit は赤)・engine は封の commit から 0 行
この file は docID の字を持たない。
"""
import collections
import copy
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


SG = load_module("tests/measure/test_xbrl_plan_attr_seal.py", "pa_seal_gate_for_pa_result_gate")      # 封の門の部品。門としては走らせない
MS = SG.MS
PR = SG.PR
AT = MS.AT

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
RECORD_COMMIT_SHORT = "9736eae1"                              # script・記録・封の門の commit(履歴から探した値と照らす)
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
RECORD_REL = SG.RECORD_REL
SC_RECORD_REL = SG.SC_RECORD_REL
GATE_REL = "tests/measure/test_xbrl_plan_attr_result.py"
DOC_REL = "docs/XBRL_PLAN_ATTR_RESULT_2026-11-19.md"

SHA_PIN = collections.OrderedDict([
    (RECORD_REL, "53891449b95acaf4812cd77fbc3cb9ebc85573999df39b75f359ef87b69d5176"),
    (SCRIPT_REL, "711c6ae73538a2140610dd64485a8b5bdf00f9439905a4a9dfdc7ea690eb054d"),
    (SEAL_GATE_REL, "2a8bf1c2372189c13b53e56b08e4b673393213df7621ba004c78a9bac2d62b51")])

K_WIRE, K_ALL, K_P, K_LABEL, K_CLASS, K_OVER, K_PRED = SG.K_WIRE, SG.K_ALL, SG.K_P, SG.K_LABEL, SG.K_CLASS, SG.K_OVER, SG.K_PRED
K_W_SC, K_W_POS, K_W_P = SG.K_W_SC, SG.K_W_POS, SG.K_W_P
K_CUT = u"切り出し"
TOP_KEYS = (u"seal", u"封の commit", u"step", u"この script の sha256", u"入力", u"engine の指紋(今。便 RT の記録の今と同じ)", u"profile", u"材料", u"手がかりの語の表",
            u"段の定義", K_CUT, K_WIRE, K_ALL, K_P, K_LABEL, K_CLASS, K_OVER, K_PRED, u"限界", u"時間(秒)", u"key_leaks", u"行の欄", u"行")
BATCHES = (u"TSS", u"KAM", u"YS")
GBATCHES = (u"KAM", u"YS")
STAGES = (1, 2, 3)
SN = dict((t, u"段 %d" % t) for t in STAGES)
CLASSES = (u"P", u"F", u"E", u"H", u"W")
IDS = (u"PA-1", u"PA-2", u"PA-3", u"PA-4", u"PA-5", u"PA-6", u"PA-7a", u"PA-7b", u"PA-8")
HIT, MISS, UNMEASURED = u"当たり", u"**外れ**", u"測れていない"
VERDICT_PINNED = (HIT,) * 9
UNIT_NAMES = collections.OrderedDict([(u"TSS", [u"(文の種類なし)"]), (u"KAM", [u"連結", u"単体"]), (u"YS", [u"研究開発活動", u"設備投資等の概要", u"配当政策"])])
PLAN = u"見積り・計画"
V_PLAN, V_OTHER, V_DROP = u"見積り・計画", u"それ以外(分母から除く札は除く)", u"分母から除く札"

FORBIDDEN_WORDS = (u"証明" + u"した", u"ハルシ" + u"ネーション", u"精" + u"度", u"世界で 1 " + u"社")
COMPANY_WORDS = (u"株式会社", u"有限会社", u"合同会社", u"㈱", u"(株)")
DOCID_RE = re.compile(r"S100[0-9A-Z]{4}")
POINTER_RE = re.compile(r"xbrl:|jppfs|jpcrp|jpdei|_cor:|@(Current|Prior)|formula:|Summary_|NonConsolidated|ConsolidatedMember")
KANJI_NUM_RE = re.compile(u"[二三四五六七八九]百|[一二三四五六七八九]千|百[一二三四五六七八九十]|千[一二三四五六七八九百]")
HUMAN_EYE_RE = re.compile(u"人の" + u"目")
#: 封 §2-3 の表の語は書かない(表を指すときは「封 §2 の表」)。次の字だけは使う: 札の名前(「見積り・計画」)・予測の語(封の予測 PA-1〜PA-8 の呼び名)・封 §4 の読み方の決めの字。
#: 使う字の分を先に除いてから探す(ほかの字で表の語が出れば赤)。封 §4 の予測の行(封の字を写した行)は、写しが封の字と同じことを組んだ行の検査が見る
TABLE_WORDS = tuple(w for ws in SG.WORD_TABLE.values() for w in ws)
ALLOWED_USES = (u"実績か計画かを結ぶ条件に入れる案", u"見積り・計画", u"予測")
REQUIRED_PHRASES = (u"先に負けと限界を書く", u"全部当たったことは規則の良さの証拠ではない", u"盲検でない", u"前の便(AT・PS・SC)の数を見てから幅を書いた", u"追跡する記録に無い",
                    u"監査の席の確かめ", u"人間の決定", u"限界", u"engine は 0 行", u"封 §2 の表", u"引き継ぎに書く", u"判定は司令塔(盲検でない)", u"engine を変えるかは人間が決める",
                    u"別の封(未使用の材料で・盲検の語の表で)", u"封も予測も、結果を見てから書き換えていない")


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


def frz(n, d):
    u"""分母 0 の字を「分母 0」だけにする分数の字。"""
    return u"分母 0" if d == 0 else fr(n, d)


def point_text(n1, d1, n2, d2):
    u"""(n1/d1 − n2/d2)× 100 を小数 2 桁(四捨五入)の字で。"""
    x = (fractions.Fraction(n1, d1) - fractions.Fraction(n2, d2)) * 100
    q = int(math.floor(x * 100 + fractions.Fraction(1, 2)))
    return u"%d.%02d" % divmod(q, 100)


_LABELS = []
_SC_STOP = {}


def labels():
    u"""札つきの行(読みの記録から。止めた行の数え直しの材料)。``Ctx`` は深い写しを持つ。"""
    if not _LABELS:
        _LABELS.extend(MS.SC.build_labels(SG.real_recs()))
    return _LABELS


def sc_stop_map():
    u"""便 SC の記録の行 → {鍵: 便 SC の段 2 で止めたか}(追跡されている便 SC の記録から。1 度だけ読む)。"""
    if not _SC_STOP:
        sc = json.loads(read(SC_RECORD_REL))
        for r in sc[u"行"]:
            _SC_STOP[tuple(r[:5])] = r[MS.SC_C_H2] != u""
    return _SC_STOP


class Ctx(object):
    u"""記録・封・文書・字の写し。変異は毎回 ``Ctx()`` の新しい写しに 1 か所だけ加える。"""

    def __init__(self):
        self.rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        self.seal = read(SEAL_REL)
        self.doc = read(DOC_REL)
        self.texts = collections.OrderedDict((rel, read_bytes(rel)) for rel in SHA_PIN)
        self.labs = copy.deepcopy(labels())
        self.sc_stop = dict(sc_stop_map())


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
    return row[5 + t] != u""


class Facts(object):
    u"""記録の行と読みの札から数えた数。集計の欄は使わず、行(止めた行)・札から数える。"""

    def __init__(self, c):
        self.rec = c.rec
        self.rows = c.rec[u"行"]
        self.sc_stop = c.sc_stop
        self.index = dict((tuple(r[:5]), r) for r in self.rows)
        self.v = dict((b, []) for b in BATCHES)               # 引けた V の札: (札, 行)
        self.g = dict((b, []) for b in GBATCHES)
        self.v_label_n = dict((b, 0) for b in BATCHES)
        self.g_label_n = dict((b, 0) for b in GBATCHES)
        for lab in c.labs:
            row = self.index.get((lab[u"便"], lab[u"#"], lab[u"側"], lab[u"si"], lab[u"pos"]))
            if lab[u"state"] == u"V":
                self.v_label_n[lab[u"便"]] += 1
                if row is not None and row[5] == u"V":
                    self.v[lab[u"便"]].append((lab, row))
            else:
                self.g_label_n[lab[u"便"]] += 1
                if row is not None and row[5] == u"G":
                    self.g[lab[u"便"]].append((lab, row))
        plan = lambda lab: lab[u"種別"] == AT.KIND_OUT and lab[u"先"] == PLAN
        drop = lambda lab: lab[u"種別"] == AT.KIND_DROP
        self.plan = dict((b, [r for lab, r in self.v[b] if plan(lab)]) for b in BATCHES)
        self.other = dict((b, [r for lab, r in self.v[b] if not plan(lab) and not drop(lab)]) for b in BATCHES)
        self.drop = dict((b, [r for lab, r in self.v[b] if drop(lab)]) for b in BATCHES)
        self.plan_sides = collections.Counter(lab[u"側"] for lab, _r in self.v[u"YS"] if plan(lab))
        self.a = dict((b, [r for lab, r in self.g[b] if lab[u"型"] == u"a"]) for b in GBATCHES)
        self.gt = dict((t, dict((b, [r for lab, r in self.g[b] if lab[u"型"] == t]) for b in GBATCHES)) for t in (u"a", u"b", u"c"))
        self.tss_g = [r for r in self.rows if r[0] == u"TSS" and r[5] == u"G"]
        self.tss_v = [r for r in self.rows if r[0] == u"TSS" and r[5] == u"V"]

    @staticmethod
    def cat(rs):
        u"""行の集まり → (分母, {段: 止めた行})。"""
        return len(rs), dict((t, sum(1 for r in rs if is_stop(r, t))) for t in STAGES)

    def sum_of(self, d, bs):
        return [r for b in bs for r in d[b]]

    def over(self, rs):
        u"""行の集まり → (行, 両方で止めた, 便 SC だけ, この便だけ, どちらも止めない)。便 SC の側は便 SC の記録の行から。"""
        a = collections.Counter((self.sc_stop[tuple(r[:5])], is_stop(r, 2)) for r in rs)
        return (len(rs), a[(True, True)], a[(True, False)], a[(False, True)], a[(False, False)])


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
    both = lambda pid: re.search(r"(\d+)% 以上 (\d+)% 以下", r(pid)[0])
    m = both(u"PA-1")
    b[u"PA-1"] = (pct(m.group(1)), pct(m.group(2)))
    b[u"PA-2"] = pct(re.search(r"止めるのは (\d+)% 以下", r(u"PA-2")[0]).group(1))
    m = both(u"PA-3")
    b[u"PA-3"] = (pct(m.group(1)), pct(m.group(2)))
    b[u"PA-4"] = pct(re.search(r"止めるのは (\d+)% 以上", r(u"PA-4")[0]).group(1))
    b[u"PA-5"] = int(re.search(r"より (\d+) ポイント以上低い", r(u"PA-5")[0]).group(1))
    m = re.search(r"を (\d+)% 以上止め、かつ、札 a の G の行を止めるのは (\d+)% 以下", r(u"PA-6")[0])
    b[u"PA-6"] = (pct(m.group(1)), pct(m.group(2)))
    b[u"PA-7a"] = pct(re.search(r"止めるのは (\d+)% 以下", r(u"PA-7a")[0]).group(1))
    m = both(u"PA-7b")
    b[u"PA-7b"] = (pct(m.group(1)), pct(m.group(2)))
    b[u"PA-8"] = int(re.search(r"両方で止める行は (\d+) 行以下", r(u"PA-8")[0]).group(1))
    sec = seal[seal.index(u"## §4 "):seal.index(u"## §5 ")]
    b[u"測れない"] = int(re.search(r"の引けた分母が (\d+) 行未満", sec).group(1))
    return b


def numbers(f):
    u"""判定に使う数(行・札から数えた数)。"""
    c = collections.OrderedDict()
    plan3 = f.sum_of(f.plan, BATCHES)
    other3 = f.sum_of(f.other, BATCHES)
    aT = f.sum_of(f.a, GBATCHES)
    c[u"plan"] = f.cat(plan3)
    c[u"plan_ys_tss"] = f.cat(f.plan[u"YS"] + f.plan[u"TSS"])
    c[u"other"] = f.cat(other3)
    c[u"a"] = f.cat(aT)
    c[u"a_kam"] = f.cat(f.a[u"KAM"])
    c[u"tss_g"] = f.cat(f.tss_g)
    c[u"tss_v"] = f.cat(f.tss_v)
    c[u"over"] = f.over(plan3 + other3)
    return c


def judge(c):
    u"""[(id, 当たりか(測れなければ None))](9 本)。封の字の境と、記録の行・札から決める。"""
    b = seal_bounds(c.seal)
    n = numbers(Facts(c))
    q = lambda d, s, t: fractions.Fraction(s[t], d) if d else None
    pd, ps = n[u"plan"]
    yd, ys = n[u"plan_ys_tss"]
    od, os_ = n[u"other"]
    ad, as_ = n[u"a"]
    kd, ks = n[u"a_kam"]
    thin = pd < b[u"測れない"]
    out = []
    lo, hi = b[u"PA-1"]
    out.append((u"PA-1", None if thin else lo <= q(yd, ys, 2) <= hi))
    out.append((u"PA-2", None if thin else q(yd, ys, 1) <= b[u"PA-2"]))
    lo, hi = b[u"PA-3"]
    out.append((u"PA-3", lo <= q(ad, as_, 2) <= hi))
    out.append((u"PA-4", q(kd, ks, 3) >= b[u"PA-4"]))
    out.append((u"PA-5", None if thin else (q(pd, ps, 2) - q(od, os_, 2)) * 100 >= b[u"PA-5"]))
    lo6, hi6 = b[u"PA-6"]
    sat = [t for t in STAGES if q(pd, ps, t) >= lo6 and q(ad, as_, t) <= hi6]
    out.append((u"PA-6", None if thin else len(sat) >= 1))
    gd, gs = n[u"tss_g"]
    out.append((u"PA-7a", q(gd, gs, 2) <= b[u"PA-7a"]))
    vd, vs = n[u"tss_v"]
    lo, hi = b[u"PA-7b"]
    out.append((u"PA-7b", lo <= q(vd, vs, 2) <= hi))
    out.append((u"PA-8", n[u"over"][1] <= b[u"PA-8"]))
    return out


def verdicts(c):
    return tuple(UNMEASURED if ok is None else (HIT if ok else MISS) for _i, ok in judge(c))


def satisfied_stages(c):
    b = seal_bounds(c.seal)
    n = numbers(Facts(c))
    pd, ps = n[u"plan"]
    ad, as_ = n[u"a"]
    lo6, hi6 = b[u"PA-6"]
    return [t for t in STAGES if fractions.Fraction(ps[t], pd) >= lo6 and fractions.Fraction(as_[t], ad) <= hi6]


def slacks(c):
    u"""境までの余りの行数(あと何行で境をまたぐかは余り + 1): 辞書。
    pa3 = 段 2 の止めた行 − 2% に要る行 / pa4 = 段 3 の止めた行 − 25% に要る行 / pa7b = 20% で許す行 − 段 2 の止めた行 /
    pa6v = 段 2 の止めた行 − 50% に要る行 / pa6g = 5% で許す行 − 段 2 の止めた行。"""
    b = seal_bounds(c.seal)
    n = numbers(Facts(c))
    pd, ps = n[u"plan"]
    ad, as_ = n[u"a"]
    kd, ks = n[u"a_kam"]
    vd, vs = n[u"tss_v"]
    return collections.OrderedDict([
        (u"pa3", as_[2] - int(math.ceil(b[u"PA-3"][0] * ad))),
        (u"pa4", ks[3] - int(math.ceil(b[u"PA-4"] * kd))),
        (u"pa7b", int(math.floor(b[u"PA-7b"][1] * vd)) - vs[2]),
        (u"pa6v", ps[2] - int(math.ceil(b[u"PA-6"][0] * pd))),
        (u"pa6g", int(math.floor(b[u"PA-6"][1] * ad)) - as_[2])])


def direction(c):
    u"""(PA-7b は段 2 で上の境(20%)の 1 ポイント内・PA-3 は段 2 で下の境(2%)の 1 ポイント内・PA-4 は段 3 で下の境(25%)の 5 ポイント内・
    PA-6 の満たす段は段 2 だけ・PA-1 は段 2 で両端から 5 ポイント以上離れている・段 1 は「見積り・計画」の V が 50% 未満・段 3 は札 a の G が 5% 超)。"""
    b = seal_bounds(c.seal)
    n = numbers(Facts(c))
    pd, ps = n[u"plan"]
    yd, ys = n[u"plan_ys_tss"]
    ad, as_ = n[u"a"]
    kd, ks = n[u"a_kam"]
    vd, vs = n[u"tss_v"]
    one = fractions.Fraction(1, 100)
    five = fractions.Fraction(5, 100)
    lo7, hi7 = b[u"PA-7b"]
    lo3, _hi3 = b[u"PA-3"]
    lo1, hi1 = b[u"PA-1"]
    lo6, hi6 = b[u"PA-6"]
    x1 = fractions.Fraction(ys[2], yd)
    return (hi7 - one < fractions.Fraction(vs[2], vd) <= hi7,
            lo3 <= fractions.Fraction(as_[2], ad) < lo3 + one,
            b[u"PA-4"] <= fractions.Fraction(ks[3], kd) < b[u"PA-4"] + five,
            satisfied_stages(c) == [2],
            x1 - lo1 >= five and hi1 - x1 >= five,
            fractions.Fraction(ps[1], pd) < lo6,
            fractions.Fraction(as_[3], ad) > hi6)


def pk(pr, prefix):
    ks = [k for k in pr if k.startswith(prefix)]
    return pr[ks[0]] if len(ks) == 1 else None


def bias_problems(c):
    u"""要約の偏りの行の言い分: 「見積り・計画」の札の V の分母は TSS が過半・KAM は 0・YS は 1 つの節だけ・段 2 の率は TSS が 50% 以上・YS は 50% 未満(段 1 と段 2 は止めた行が 0)。"""
    f = Facts(c)
    b = seal_bounds(c.seal)
    lo6 = b[u"PA-6"][0]
    d = dict((bb, f.cat(f.plan[bb])) for bb in BATCHES)
    out = []
    pd = sum(d[bb][0] for bb in BATCHES)
    if not (d[u"TSS"][0] * 2 > pd and d[u"KAM"][0] == 0 and len(f.plan_sides) == 1):
        out.append(u"bias: 「見積り・計画」の札の V の分母が TSS 過半・KAM 0・YS 1 つの節 でない")
    if not (d[u"TSS"][0] and d[u"YS"][0] and fractions.Fraction(d[u"TSS"][1][2], d[u"TSS"][0]) >= lo6 and fractions.Fraction(d[u"YS"][1][2], d[u"YS"][0]) < lo6
            and d[u"YS"][1][1] == 0 and d[u"YS"][1][2] == 0):
        out.append(u"bias: 段 2 の率が「TSS は 50% 以上・YS は 50% 未満で段 1・段 2 の止めた行が 0」でない")
    return out


def judge_problems(c):
    out = []
    got = verdicts(c)
    if got != VERDICT_PINNED:
        out.append(u"judge: 決め直した判定が字で留めた判定と違う: %s" % (u" ".join(got),))
    if direction(c) != (True,) * 7:
        out.append(u"judge: 境への近さの向き(PA-7b・PA-3・PA-4・満たす段は段 2 だけ・PA-1 は端から離れている・段 1・段 3)が行からの数え直しと違う")
    pr = c.rec[K_PRED]
    f = Facts(c)
    n = numbers(f)

    def nd(t, x):
        return collections.OrderedDict([(u"分子", x[1][t]), (u"分母", x[0]), (u"率", rate_text(x[1][t], x[0]))])

    def cells(x):
        return collections.OrderedDict((SN[t], nd(t, x)) for t in STAGES)

    def by_batch(d, bs):
        return collections.OrderedDict([(b, cells(f.cat(d[b]))) for b in bs])

    def over_cell(x):
        return collections.OrderedDict(zip((u"行", u"両方で止めた", u"便 SC だけが止めた", u"この便だけが止めた", u"どちらも止めない"), x))
    want = [(u"PA-1 ", collections.OrderedDict([(u"YS と TSS の合計", cells(n[u"plan_ys_tss"])), (u"3 便の合計", cells(n[u"plan"]))] + list(by_batch(f.plan, BATCHES).items()))),
            (u"PA-2 ", collections.OrderedDict([(u"YS と TSS の合計", nd(1, n[u"plan_ys_tss"]))])),
            (u"PA-3 ", collections.OrderedDict([(u"KAM と YS の合計", cells(n[u"a"]))] + list(by_batch(f.a, GBATCHES).items()))),
            (u"PA-4 ", cells(n[u"a_kam"])),
            (u"PA-5 「それ以外」", collections.OrderedDict([(u"3 便の合計", cells(n[u"other"]))] + list(by_batch(f.other, BATCHES).items()))),
            (u"PA-7a ", cells(n[u"tss_g"])),
            (u"PA-7b ", cells(n[u"tss_v"])),
            (u"PA-8 札つき", over_cell(n[u"over"])),
            (u"PA-8 参考", over_cell(f.over(f.sum_of(f.drop, BATCHES))))]
    for p, v in want:
        if pk(pr, p) != v:
            out.append(u"judge: 記録の「予測の判定に要る数」の欄が行・札から数え直した数と違う: %s" % p)
    d5 = pk(pr, u"PA-5 率の差")
    pd, ps = n[u"plan"]
    od, os_ = n[u"other"]
    if d5 is None or [d5[SN[t]] for t in STAGES] != [point_text(ps[t], pd, os_[t], od) for t in STAGES]:
        out.append(u"judge: PA-5 の率の差の欄が行・札から数え直した数と違う")
    d6 = pk(pr, u"PA-6 ")
    ad, as_ = n[u"a"]
    if d6 is None or any(d6[SN[t]][u"見積り・計画の札の V の行"] != nd(t, n[u"plan"]) or d6[SN[t]][u"札 a の G の行"] != nd(t, n[u"a"]) for t in STAGES):
        out.append(u"judge: PA-6 の欄が行・札から数え直した数と違う")
    out.extend(bias_problems(c))
    d0 = pk(pr, u"分母の確かめ")
    thin = pd < seal_bounds(c.seal)[u"測れない"]
    if d0 is None or (d0[u"「見積り・計画」の札の V の行(札)"], d0[u"「見積り・計画」の札の V の行(引けた行)"], d0[u"15 行未満"], d0[u"V の札の行(札)"], d0[u"V の札の行(引けた)"],
                      d0[u"G の札の行(札)"], d0[u"G の札の行(引けた)"]) != (
            sum(1 for lab in c.labs if lab[u"state"] == u"V" and lab[u"種別"] == AT.KIND_OUT and lab[u"先"] == PLAN), pd, thin, sum(f.v_label_n.values()),
            sum(len(f.v[b]) for b in BATCHES), sum(f.g_label_n.values()), sum(len(f.g[b]) for b in GBATCHES)):
        out.append(u"judge: 分母の確かめの欄が札・行から数え直した数と違う")
    return out


# ======================================================================================================
# c. 文書の行(記録から組む)
def c5(x):
    return u"%d | %d | %d | %d | %d" % ((x[u"札の行"], x[u"引けた行(分母)"]) + tuple(x[u"止めた行"][SN[t]] for t in STAGES))


def over5(x):
    return u"%d | %d | %d | %d | %d" % (x[u"行"], x[u"両方で止めた"], x[u"便 SC だけが止めた"], x[u"この便だけが止めた"], x[u"どちらも止めない"])


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
    wire, allr, tp, lab, cls, ov, pr = rec[K_WIRE], rec[K_ALL], rec[K_P], rec[K_LABEL], rec[K_CLASS], rec[K_OVER], rec[K_PRED]
    pos = wire[K_W_POS]
    cut = rec[K_CUT]
    L = []

    def add(name, line):
        L.append((name, line))

    p2 = lambda x: u"%d%%" % (x * 100)                        # 境(Fraction)→ 整数の %
    pd, ps = n[u"plan"]
    yd, ys = n[u"plan_ys_tss"]
    od, os_ = n[u"other"]
    ad, as_ = n[u"a"]
    kd, ks = n[u"a_kam"]
    gd, gs = n[u"tss_g"]
    vd_, vs = n[u"tss_v"]
    ovr = n[u"over"]
    q = lambda d, s, t: fr(s[t], d)
    sat = satisfied_stages(c)
    sl = slacks(c)
    planB = dict((bb, f.cat(f.plan[bb])) for bb in BATCHES)
    otherB = dict((bb, f.cat(f.other[bb])) for bb in BATCHES)
    aB = dict((bb, f.cat(f.a[bb])) for bb in GBATCHES)
    pr5 = pk(pr, u"PA-5 率の差")
    lo6, hi6 = b[u"PA-6"]
    tssv_rows = [r for r in f.tss_v if is_stop(r, 2)]
    h_rows = [r for r in tssv_rows if u"H" in r[7]]
    h_only = [r for r in tssv_rows if r[7] == u"H"]
    h_books = len(set(r[1] for r in h_rows))
    h_sents = len(set((r[1], r[3]) for r in h_rows))
    ys_side = list(f.plan_sides)[0] if len(f.plan_sides) == 1 else u"?"

    # ---- 頭
    add(u"head 封", u"封 `docs/XBRL_PLAN_ATTR_SEAL_2026-11-19.md`(commit %s)。script `measure/xbrl_plan_attr_2026-11-19.py`・記録 `fixtures/xbrl/plan_attr/stops_2026-11-19.json`・封の門 `tests/measure/test_xbrl_plan_attr_seal.py` は commit %s(独立監査 GO)。取得 0・0 USD・通信なし・LLM の席は呼んでいない。" % (SEAL_COMMIT_SHORT, RECORD_COMMIT_SHORT))
    add(u"head 数", u"この文書の数は全部、記録から 1 つずつ読んだもの(結果の門が、記録の行・読みの札・便 SC の記録の行から数え直した数と字で同じことを見る)。engine は 0 行(engine を変えた commit は無い)。")
    # ---- 要約
    add(u"lead 判定", u"- 判定した %d 本(PA-7 を a と b に分けて数える)は全部が当たり(当たり %d・外れ %d)。外れた予測は無い。" % (len(vd), len(ids_hit), len(ids_miss)))
    add(u"lead 証拠", u"- 全部当たったことは規則の良さの証拠ではない。語の表は盲検でなく、司令塔は前の便(AT・PS・SC)の数を見てから幅を書いた(封 §0 の申告)。外れうる形で書いた %d 本の幅の中に %d 本とも入ったのは、幅を数を見てから置いた結果でもある。" % (len(vd), len(ids_hit)))
    add(u"lead 境", u"- 境に近いもの: PA-7b は段 2 の %s で上の境 %s の際(あと %d 行多ければ外れ)・PA-3 は段 2 の %s で下の境 %s に近い(あと %d 行少なければ外れ)・PA-4 は段 3 の %s で下の境 %s に近い(あと %d 行少なければ外れ)。"
        % (q(vd_, vs, 2), p2(b[u"PA-7b"][1]), sl[u"pa7b"] + 1, q(ad, as_, 2), p2(b[u"PA-3"][0]), sl[u"pa3"] + 1, q(kd, ks, 3), p2(b[u"PA-4"]), sl[u"pa4"] + 1))
    add(u"lead 分母", u"- 「見積り・計画」の札の V の引けた行は %d で小さく、TSS %d・KAM %d・YS %d と TSS に偏る(TSS・YS・KAM を分けると、段 2 は TSS %s・YS %s・KAM は分母 %d)。YS は段 1 と段 2 で止めた行が %d・%d で、段 3 で %s。段 2 が満たした(PA-1・PA-6)のは TSS の数で、YS だけでは満たさない。"
        % (pd, planB[u"TSS"][0], planB[u"KAM"][0], planB[u"YS"][0], q(planB[u"TSS"][0], planB[u"TSS"][1], 2), q(planB[u"YS"][0], planB[u"YS"][1], 2), planB[u"KAM"][0],
           planB[u"YS"][1][1], planB[u"YS"][1][2], q(planB[u"YS"][0], planB[u"YS"][1], 3)))
    add(u"lead H", u"- TSS の V の段 2 で止めた %s のうち、見出しの類 H に当たった行は %d 行(%d 本の %d 文に在る)で、H だけで止まった行は %d 行。見出し 1 つが多くの行に当たる形で、見出しの数そのものは記録に無い(文の数までしか数えられない)。TSS の G の行に読みの札は無く、TSS の G の段 2 で止めた %s と V の段 2 で止めた行の中身は誰も読んでいない。"
        % (fr(vs[2], vd_), len(h_rows), h_books, h_sents, len(h_only), fr(gs[2], gd)))
    add(u"lead engine", u"- 後付けの規則であり engine は 0 行。engine に入れたときに同じ数になるとは測っていない。止めた G の行は正しい結びを減らした可能性を含む(KAM と YS の札 a の G は段 2 で %s)。" % q(ad, as_, 2))
    add(u"lead 読み", u"- 封 §4 の読み方の決めどおり、PA-6 が当たりなので「実績か計画かを結ぶ条件に入れる案」を人間に上げる材料にする(満たす段は段 %s だけ)。engine を変えるかは人間が決める。入れるなら別の封(未使用の材料で・盲検の語の表で)が先に要る。"
        % u"・".join(str(t) for t in sat))
    # ---- §1 予測の表
    def row(pid, meas):
        add(u"table " + pid, u"| %s | %s | %s | %s |" % (pid, seal_row(c.seal, pid)[0], meas, v[pid]))
    row(u"PA-1", u"%s(段 1 %s・段 3 %s。TSS %s・KAM %s・YS %s)" % (q(yd, ys, 2), q(yd, ys, 1), q(yd, ys, 3), frz(planB[u"TSS"][1][2], planB[u"TSS"][0]), frz(planB[u"KAM"][1][2], planB[u"KAM"][0]), frz(planB[u"YS"][1][2], planB[u"YS"][0])))
    row(u"PA-2", u"%s(段 2 %s・段 3 %s)" % (q(yd, ys, 1), q(yd, ys, 2), q(yd, ys, 3)))
    row(u"PA-3", u"%s(KAM %s・YS %s。段 1 %s・段 3 %s)" % (q(ad, as_, 2), q(aB[u"KAM"][0], aB[u"KAM"][1], 2), q(aB[u"YS"][0], aB[u"YS"][1], 2), q(ad, as_, 1), q(ad, as_, 3)))
    row(u"PA-4", u"段 3 %s(段 1 %s・段 2 %s)" % (q(kd, ks, 3), q(kd, ks, 1), q(kd, ks, 2)))
    row(u"PA-5", u"それ以外 %s・見積り・計画 %s・差 %s ポイント" % (q(od, os_, 2), q(pd, ps, 2), pr5[SN[2]]))
    row(u"PA-6", u"満たす段は段 %s(%s と %s)" % (u"・".join(str(t) for t in sat), q(pd, ps, 2), q(ad, as_, 2)))
    row(u"PA-7a", u"%s(段 1 %s・段 3 %s)" % (q(gd, gs, 2), q(gd, gs, 1), q(gd, gs, 3)))
    row(u"PA-7b", u"%s(段 1 %s・段 3 %s)" % (q(vd_, vs, 2), q(vd_, vs, 1), q(vd_, vs, 3)))
    row(u"PA-8", u"両方で止めた行 %d(札つきの V %d 行。便 SC だけ %d・この便だけ %d・どちらも止めない %d)" % (ovr[1], ovr[0], ovr[2], ovr[3], ovr[4]))
    add(u"b 数", u"- 当たり %d(%s)・外れ %d。" % (len(ids_hit), u"・".join(ids_hit), len(ids_miss)))
    add(u"b 測れる", u"- 「見積り・計画」の札の V の引けた行は %d で、封の「%d 行未満なら測れていない」に当たらないので、PA-1・PA-5・PA-6 は判定した。" % (pd, b[u"測れない"]))
    add(u"b PA-1", u"- PA-1 は段 2 の %sで、封の幅(%s 以上 %s 以下)の中。段 1 は %s・段 3 は %s。内訳は TSS %s・YS %s で KAM は分母 %d(合計の率は TSS の行が引き上げている)。"
        % (fr(ys[2], yd), p2(b[u"PA-1"][0]), p2(b[u"PA-1"][1]), rate_text(ys[1], yd), rate_text(ys[3], yd), fr(planB[u"TSS"][1][2], planB[u"TSS"][0]), fr(planB[u"YS"][1][2], planB[u"YS"][0]), planB[u"KAM"][0]))
    add(u"b PA-2", u"- PA-2 は段 1 の %sで、封の上限 %s の中。段 1 は engine の語のままで窓を文頭まで広げた形で、止めた行は %d。" % (fr(ys[1], yd), p2(b[u"PA-2"]), ys[1]))
    add(u"b PA-3", u"- PA-3 は段 2 の %sで、封の幅(%s 以上 %s 以下)の中。下の境に近く、止めた行があと %d 行少なければ外れ(分母 %d)。" % (fr(as_[2], ad), p2(b[u"PA-3"][0]), p2(b[u"PA-3"][1]), sl[u"pa3"] + 1, ad))
    add(u"b PA-4", u"- PA-4 は KAM の段 3 の %sで、封の下限 %s の上。下の境に近く、止めた行があと %d 行少なければ外れ(分母 %d)。" % (fr(ks[3], kd), p2(b[u"PA-4"]), sl[u"pa4"] + 1, kd))
    add(u"b PA-5", u"- PA-5 は段 2 の差が %s ポイントで、封の %d ポイント以上の中。それ以外の札の V の止めた行 %d は、TSS %d・KAM %d・YS %d。" % (pr5[SN[2]], b[u"PA-5"], os_[2], otherB[u"TSS"][1][2], otherB[u"KAM"][1][2], otherB[u"YS"][1][2]))
    add(u"b PA-6", u"- PA-6 は満たす段が段 %s だけで当たり。段 1 は「見積り・計画」の札の V が %s で %s 未満・段 3 は札 a の G が %s で %s 超なので満たさない。"
        % (u"・".join(str(t) for t in sat), q(pd, ps, 1), p2(lo6), q(ad, as_, 3), p2(hi6)))
    add(u"b PA-7", u"- PA-7a は %sで封の上限 %s の中・PA-7b は %sで封の幅(%s 以上 %s 以下)の中。PA-7b は上の境の際で、止めた行があと %d 行多ければ外れ(分母 %d)。"
        % (fr(gs[2], gd), p2(b[u"PA-7a"]), fr(vs[2], vd_), p2(b[u"PA-7b"][0]), p2(b[u"PA-7b"][1]), sl[u"pa7b"] + 1, vd_))
    add(u"b PA-8", u"- PA-8 は両方で止めた行 %d で、封の上限 %d 行の中。" % (ovr[1], b[u"PA-8"]))
    add(u"b 欠陥", u"- 封 §4 の「PA-1 か PA-7b が下に外れたときは先に自分の欠陥を疑う」は、どちらも下に外れていないので発火しない。当たった類は 0 でない(§5)。")
    # PA-6 の段ごとの表
    for t in STAGES:
        ok = (fractions.Fraction(ps[t], pd) >= lo6) and (fractions.Fraction(as_[t], ad) <= hi6)
        add(u"s6 段 %d" % t, u"| 段 %d | %s | %s | %s |" % (t, q(pd, ps, t), q(ad, as_, t), u"満たす" if ok else u"満たさない"))
    add(u"s6 近さ", u"- PA-6 の段 2 は、「見積り・計画」の札の V の止めた行があと %d 行少なければ %s を下回り、札 a の G の止めた行があと %d 行多ければ %s を超える。" % (sl[u"pa6v"] + 1, p2(lo6), sl[u"pa6g"] + 1, p2(hi6)))
    # ---- §2 配線
    for bb in BATCHES:
        x = wire[K_W_SC][bb]
        add(u"w " + bb, u"- %s: 引き直した結んだ行 %d・便 SC の記録の結んだ行(同じ本)%d・鍵と state が同じ行 %d・今にだけ在る行 %d・便 SC の記録にだけ在る行 %d。"
            % (bb, x[u"引き直した結んだ行"], x[u"便 SC の記録の結んだ行(同じ本)"], x[u"鍵と state が同じ行"], x[u"今にだけ在る行"], x[u"便 SC の記録にだけ在る行"]))
    for bb in BATCHES:
        x = pos[bb]
        add(u"pos " + bb, u"- %s: 位置を確かめた数の claim %d(state を問わない)・位置の字が数字 %d・符号か空白 %d。"
            % (bb, x[u"位置を確かめた数の claim(state を問わない)"], x[u"うち pos の字が数字"], x[u"うち pos の字が符号か空白"]))
    hw = wire[K_W_P]
    add(u"w 当たる", u"- 当たるはずの行(engine が止めた行のうち、決算期の字の規則で止まった行を除いた行)は 3 便の合計 %d・文の全部に類 P の語が当たった行 %d・当たらなかった行 %d(%s)。止める条件(95%% 未満)に当たらず、止まらなかった。"
        % (hw[u"当たるはずの行(3 便の合計)"], hw[u"当たった"], hw[u"当たらなかった"], hw[u"率"][u"率"]))
    add(u"w 理屈", u"- **この確かめ(当たるはずの行の全部が当たった)が縛るのは `p27_gate` の読み(決算期の字の規則で止まった行の除き方)であって、規則の効きではない。** engine の語の窓は文の中に入るので、全部当たるのは作りから理屈どおりである。")
    bk = wire[u"本の数"]
    add(u"w 本", u"- 本の数は TSS %d・KAM %d・YS %d。" % (bk[u"TSS"], bk[u"KAM"], bk[u"YS"]))
    for bb in BATCHES:
        for s_ in UNIT_NAMES[bb]:
            x = cut[bb][s_ if s_ != u"(文の種類なし)" else MS.NO_SIDE]
            add(u"cut %s %s" % (bb, s_), u"| %s | %s | %d | %d | %d | %d |" % (bb, s_, x[u"本"], x[u"切れた"], x[u"切れない"], x[u"数の claim"]))
    # ---- §3 結んだ行の全部・engine が止めた行
    add(u"t3 全部", u"- 結んだ行は state が G か V の数の claim の全部で、member の欄は問わない。結んだ行の合計は TSS %d・KAM %d・YS %d(記録の行 %d)。"
        % (tuple(sum(allr[bb][u"全体"][s_][u"結んだ行"] for s_ in (u"G", u"V")) for bb in BATCHES) + (len(rec[u"行"]),)))
    def t3(name, label, d):
        for s_ in (u"G", u"V"):
            x = d[s_]
            add(u"t3 %s %s" % (name, s_), u"| %s | %s | %d | %d | %d | %d |" % ((label, s_, x[u"結んだ行"]) + tuple(x[u"止めた行"][SN[t]] for t in STAGES)))
    t3(u"TSS", u"TSS", allr[u"TSS"][u"全体"])
    t3(u"KAM", u"KAM 全体", allr[u"KAM"][u"全体"])
    for s_ in UNIT_NAMES[u"KAM"]:
        t3(u"KAM " + s_, u"KAM %s" % s_, allr[u"KAM"][u"文の種類別"][s_])
    t3(u"YS", u"YS 全体", allr[u"YS"][u"全体"])
    for s_ in UNIT_NAMES[u"YS"]:
        t3(u"YS " + s_, u"YS %s" % s_, allr[u"YS"][u"節別"][s_])
    pk_ = MS.P_KEYS

    def tpl(name, label, x):
        add(u"p %s" % name, u"| %s | %d | %d | %d | %d | %d |" % ((label,) + tuple(x[k] for k in pk_)))
    tpl(u"TSS", u"TSS", tp[u"TSS"][u"全体"])
    tpl(u"KAM", u"KAM 全体", tp[u"KAM"][u"全体"])
    for s_ in UNIT_NAMES[u"KAM"]:
        tpl(u"KAM " + s_, u"KAM %s" % s_, tp[u"KAM"][u"文の種類別"][s_])
    tpl(u"YS", u"YS 全体", tp[u"YS"][u"全体"])
    for s_ in UNIT_NAMES[u"YS"]:
        tpl(u"YS " + s_, u"YS %s" % s_, tp[u"YS"][u"節別"][s_])
    tpl(u"合計", u"合計", tp[u"合計"][u"全体"])
    # ---- §4 札つきの行
    V, G = lab[u"V の札"], lab[u"G の札(KAM・YS)"]
    for bb in list(BATCHES) + [u"合計"]:
        for key, nmk in ((V_PLAN, u"見積り・計画"), (V_OTHER, u"それ以外"), (V_DROP, u"分母から除く札")):
            add(u"v %s %s" % (bb, nmk), u"| %s | %s | %s |" % (bb, nmk, c5(V[bb][key])))
    add(u"v 引けない", u"- 引けなかった札の行(分母に入れない): V の札は TSS %d(行が無い %d・state が違う %d)・KAM %d・YS %d。G の札は KAM %d・YS %d。"
        % (V[u"TSS"][u"全体"][u"引けなかった行"], V[u"TSS"][u"全体"][u"引けなかった理由"][u"行が無い"], V[u"TSS"][u"全体"][u"引けなかった理由"][u"state が違う"],
           V[u"KAM"][u"全体"][u"引けなかった行"], V[u"YS"][u"全体"][u"引けなかった行"], G[u"KAM"][u"全体"][u"引けなかった行"], G[u"YS"][u"全体"][u"引けなかった行"]))
    add(u"v 除く", u"- 分母から除く札は TSS に %d 行(引けた行 %d)で、それ以外の札の V の分母に入れない。" % (V[u"TSS"][V_DROP][u"札の行"], V[u"TSS"][V_DROP][u"引けた行(分母)"]))
    add(u"v YS", u"- YS の「見積り・計画」の札の V %d 行は、全部が 1 つの節(%s)に在る。" % (planB[u"YS"][0], ys_side))
    for bb in list(BATCHES) + [u"合計"]:
        for nmk, x in V[bb][u"属性ごと"].items():
            add(u"v 属性 %s %s" % (bb, nmk), u"| %s | %s | %s |" % (bb, nmk, c5(x)))
    add(u"v 株", u"- 属性「1 株あたり」は、この属性に写る型が便 AT の写しの表に無い。表の 0 は作りで、測った 0 ではない。")
    for bb in (u"KAM", u"YS", u"合計"):
        for t_ in (u"a", u"b", u"c"):
            add(u"g %s %s" % (bb, t_), u"| %s | %s | %s |" % (bb, t_, c5(G[bb][u"型ごと"][t_])))
    # ---- §5 類ごと
    for bb in list(BATCHES) + [u"合計"]:
        for t in STAGES:
            for s_ in (u"G", u"V"):
                x = cls[bb][SN[t]][s_]
                add(u"c %s %d %s" % (bb, t, s_), u"| %s | 段 %d | %s | %d | %s |" % (bb, t, s_, x[u"止めた行"], u" | ".join(u"%d" % x[k] for k in CLASSES)))
    tg, tv = cls[u"TSS"][SN[2]][u"G"], cls[u"TSS"][SN[2]][u"V"]
    add(u"c 見出し", u"- TSS の段 2 で止めた行のうち、見出しの類 H に当たった行は G で %d/%d・V で %d/%d。V の H は %d 本の %d 文に在り、H だけで止まった行は %d 行。" % (tg[u"H"], tg[u"止めた行"], tv[u"H"], tv[u"止めた行"], h_books, h_sents, len(h_only)))
    add(u"c W", u"- 類 W は段 3 だけ。段 3 で W に当たった行は、全部の便の合計で G %d・V %d。類 E は段 3 の G %d・V %d。" % (cls[u"合計"][SN[3]][u"G"][u"W"], cls[u"合計"][SN[3]][u"V"][u"W"], cls[u"合計"][SN[3]][u"G"][u"E"], cls[u"合計"][SN[3]][u"V"][u"E"]))
    # ---- §6 重なり
    for bb in list(BATCHES) + [u"合計"]:
        for s_ in (u"G", u"V"):
            add(u"o 全部 %s %s" % (bb, s_), u"| %s | %s | %s |" % (bb, s_, over5(ov[u"結んだ行の全部"][bb][s_])))
    for bb in list(BATCHES) + [u"合計"]:
        for key, nmk in ((u"札つきの V の行(分母から除く札は除く)", u"札つきの V"), (u"見積り・計画", u"見積り・計画"), (u"それ以外", u"それ以外"), (u"分母から除く札", u"分母から除く札")):
            add(u"o V %s %s" % (bb, nmk), u"| %s | %s | %s |" % (bb, nmk, over5(ov[u"V の札(引けた行)"][bb][key])))
    for bb in (u"KAM", u"YS", u"合計"):
        for key, nmk in ((u"全体", u"全体"), (u"a", u"a"), (u"b", u"b"), (u"c", u"c")):
            add(u"o G %s %s" % (bb, nmk), u"| %s | %s | %s |" % (bb, nmk, over5(ov[u"G の札(KAM・YS。引けた行)"][bb][key])))
    ovp = ov[u"V の札(引けた行)"][u"合計"]
    add(u"o 言い分", u"- 札つきの V %d 行のうち、便 SC の段 2 とこの便の段 2 の両方で止めた行は %d・便 SC だけ %d・この便だけ %d。「見積り・計画」の札の V %d 行では、便 SC の段 2 が止めた行は %d・この便の段 2 が止めた行は %d。結んだ行の G の全部では、両方で止めた行は %d。"
        % (ovp[u"札つきの V の行(分母から除く札は除く)"][u"行"], ovp[u"札つきの V の行(分母から除く札は除く)"][u"両方で止めた"], ovp[u"札つきの V の行(分母から除く札は除く)"][u"便 SC だけが止めた"],
           ovp[u"札つきの V の行(分母から除く札は除く)"][u"この便だけが止めた"], ovp[u"見積り・計画"][u"行"], ovp[u"見積り・計画"][u"両方で止めた"] + ovp[u"見積り・計画"][u"便 SC だけが止めた"],
           ovp[u"見積り・計画"][u"両方で止めた"] + ovp[u"見積り・計画"][u"この便だけが止めた"], ov[u"結んだ行の全部"][u"合計"][u"G"][u"両方で止めた"]))
    # ---- §7 封との差
    allG = allr
    add(u"d1", u"- (1) 類 W の読み: 封は W を「文の全部(前の字では当たらず、数の後ろの字で当たった)」と書いた。script は「前の字に類 P も類 F も無く、文の全部に類 P か類 F が在るときだけ」W を付けた(前の字に類 P か類 F が在る行は段 1・段 2 で既に止まっているので付けない)。止めた行の数には効かず、類の内訳にだけ効く。")
    add(u"d2", u"- (2) 決算期の字の規則で止まった行は、raw の claim の `p27_gate` から読んだ(verify の claim からではない)。engine が止めた行 %d のうち、決算期の字の規則で止まった行は %d・当たるはずの行は %d(§3)。"
        % (tp[u"合計"][u"全体"][pk_[0]], tp[u"合計"][u"全体"][pk_[1]], tp[u"合計"][u"全体"][pk_[2]]))
    add(u"d3", u"- (3) 95%% の確かめは 3 便の合計に掛けた(当たるはずの行 %d・当たった %d)。便ごとの数は TSS %d/%d・KAM %d/%d・YS %d/%d(§3)。封は便ごとか 3 便の合計かを書いていない。"
        % (hw[u"当たるはずの行(3 便の合計)"], hw[u"当たった"], tp[u"TSS"][u"全体"][pk_[3]], tp[u"TSS"][u"全体"][pk_[2]], tp[u"KAM"][u"全体"][pk_[3]], tp[u"KAM"][u"全体"][pk_[2]],
           tp[u"YS"][u"全体"][pk_[3]], tp[u"YS"][u"全体"][pk_[2]]))
    add(u"d4", u"- (4) 行の欄は便 SC の欄から「member が空」を除いた形(便・本の #・文の種類か節・文の番号・位置・state・段 1 から段 3 の当たりの類の 9 欄)。記録の行は %d で、(鍵, state)は便 SC の記録の行と同じ(TSS %d・KAM %d・YS %d)。"
        % ((len(rec[u"行"]),) + tuple(wire[K_W_SC][bb][u"鍵と state が同じ行"] for bb in BATCHES)))
    add(u"d5", u"- (5) 段 1 は KAM・YS の結んだ行で、G も V も止めた行が 0(KAM の G %d・V %d・YS の G %d・V %d)。独立監査の席が別の道で全行の前の字を見て 0 と確かめた(記録なし・監査の席の確かめ)。engine の既存の規則が同じ語を数の近くで既に止めているので、残るのは窓の外(文頭側の遠い所)に語が在る行だけ、という作りと合う。"
        % (allG[u"KAM"][u"全体"][u"G"][u"止めた行"][SN[1]], allG[u"KAM"][u"全体"][u"V"][u"止めた行"][SN[1]], allG[u"YS"][u"全体"][u"G"][u"止めた行"][SN[1]], allG[u"YS"][u"全体"][u"V"][u"止めた行"][SN[1]]))
    add(u"d6", u"- (6) 便 SC の段 2 との重なりは、結んだ行の G の全部で両方で止めた行が 0(TSS %d・KAM %d・YS %d)。独立監査の席は「この便が止めた G の行は便 SC の段 2 の対象と重ならない」と報告した(記録なし・監査の席の確かめ)。記録の 2×2 の数は、合計の G で便 SC だけが止めた行 %d・この便だけが止めた行 %d・両方で止めた行 %d(§6)。理由は記録の数で言える範囲に留め、これ以上は書かない。"
        % (ov[u"結んだ行の全部"][u"TSS"][u"G"][u"両方で止めた"], ov[u"結んだ行の全部"][u"KAM"][u"G"][u"両方で止めた"], ov[u"結んだ行の全部"][u"YS"][u"G"][u"両方で止めた"],
           ov[u"結んだ行の全部"][u"合計"][u"G"][u"便 SC だけが止めた"], ov[u"結んだ行の全部"][u"合計"][u"G"][u"この便だけが止めた"], ov[u"結んだ行の全部"][u"合計"][u"G"][u"両方で止めた"]))
    # ---- §8 読める事
    add(u"r 範囲", u"- 読めるのは TSS の %d 本・KAM と YS の %d 本・この 3 段に限る。上場会社全体の率ではない。" % (bk[u"TSS"], bk[u"KAM"]))
    add(u"r 段 2", u"- 段 2 は、「見積り・計画」の札の V %d 行のうち %d 行・それ以外の札の V %d 行のうち %d 行・札 a の G %d 行のうち %d 行を止めた。2 つの V の止める率の差は %s ポイント。"
        % (pd, ps[2], od, os_[2], ad, as_[2], pr5[SN[2]]))
    add(u"r 段の増え", u"- 段 1 → 段 2 → 段 3 で止めた行の増え: 「見積り・計画」の札の V は %d → %d → %d・札 a の G は %d → %d → %d。段 3 は「見積り・計画」の札の V を段 2 より %d 行多く止めるが、札 a の G も段 2 より %d 行多く止める。"
        % (ps[1], ps[2], ps[3], as_[1], as_[2], as_[3], ps[3] - ps[2], as_[3] - as_[2]))
    add(u"r PA-6", u"- PA-6 の満たす段は段 %s だけ。段 2 が境をまたぐまでの行数は、「見積り・計画」の札の V があと %d 行少なければ %s 未満・札 a の G があと %d 行多ければ %s 超。分母が小さいので、率は 1 行で %s ポイントほど動く。"
        % (u"・".join(str(t) for t in sat), sl[u"pa6v"] + 1, p2(lo6), sl[u"pa6g"] + 1, p2(hi6), rate_text(1, pd)[:-1]))
    add(u"r 偏り", u"- 段 2 が満たしたのは TSS の数(「見積り・計画」の札の V は TSS %s・YS %s・KAM は分母 %d)。YS だけでは満たさず、YS と KAM の「見積り・計画」の札の V は段 2 で %d 行止めた。"
        % (fr(planB[u"TSS"][1][2], planB[u"TSS"][0]), fr(planB[u"YS"][1][2], planB[u"YS"][0]), planB[u"KAM"][0], planB[u"YS"][1][2] + planB[u"KAM"][1][2]))
    add(u"r 重なり", u"- 便 SC の段 2 とこの便の段 2 は、札つきの V %d 行のうち両方で止めた行が %d で、ほとんど重ならない。2 つの規則は別の取り違えを止めている、と数の範囲では言える(札の読みが正しければ)。それ以上は言えない。"
        % (ovr[0], ovr[1]))
    add(u"r TSS", u"- TSS の全部の行(札は無い)の段 2 では、V の %s・G の %s を止めた。止めた行が正しい結びだったかは読んでいない。" % (fr(vs[2], vd_), fr(gs[2], gd)))
    add(u"r 読めない", u"- 読めない事: 札の正しさ(札は AI の席 1 席が付けた)。止めた行が「止めて正しかった」か(札の在る行でしか言えない)。止めたあとに正しい fact へ結び直せるか。TSS の G・V で止めた行の中身。engine に入れたときの数。別の語の表での数。類 E が何かを正しく止めるか。KAM・YS・TSS 以外の書類。")
    # ---- §9 限界
    add(u"m 1", u"- engine は変えていない。止めた数は engine の外の後付けの規則の数で、engine の旗にしたときの数ではない(engine の中では止めたあとに別の枠へ結び直す道が在りうる。それは測らない)(封 §5)。")
    add(u"m 2", u"- 読みの札は AI の席(司令塔)1 席が付けた。盲検でなく、人は読んでいない。この便は札の正しさを 1 つも確かめない。TSS の札は便 NRE の直しの前の engine の行に付けたもので、いまの engine で同じ state で引けた行だけを数えた(TSS の V の札で引けなかった行は %d)(封 §5)。"
        % V[u"TSS"][u"全体"][u"引けなかった行"])
    add(u"m 3", u"- 「見積り・計画」の札の V の引けた行は %d で、KAM は %d 行。YS の %d 行は 1 つの節。率は粗い(封 §5)。" % (pd, planB[u"KAM"][0], planB[u"YS"][0]))
    add(u"m 4", u"- TSS の G の行には札が無い。「正しい結びの減り」を札で言えるのは KAM と YS だけ(札 a の G は %d 行)(封 §5)。" % ad)
    add(u"m 5", u"- 手がかりの語の表は司令塔が書いた。盲検でない。別の語の表なら数は変わる(封 §5)。")
    add(u"m 見出し", u"- この便で分かったこと: TSS の V の段 2 で止めた %d 行のうち、見出しの類 H に当たった行は %d で、%d 文に在る(§5)。見出し 1 つが多くの行に当たる形で、別の見出しの決め・別の語の表での数は測っていない。" % (vs[2], len(h_rows), h_sents))
    add(u"m 6", u"- 止めた行が「止めて正しかった」かは札の在る行でしか言えない。止めたあとに結べる出所が在るかは測らない(封 §5)。")
    add(u"m 7", u"- 類 E は類 P・類 F と性質が違う。KAM の V の札に「見積り・計画」は %d 行で、類 E が何かを正しく止めるかはこの便の札では言えない。数えるのは副作用の側だけ(類 E は段 3 の G %d・V %d)(封 §5)。"
        % (planB[u"KAM"][0], cls[u"合計"][SN[3]][u"G"][u"E"], cls[u"合計"][SN[3]][u"V"][u"E"]))
    add(u"m 8", u"- 材料は決算短信の概況の文(TSS %d 本)と有報の KAM・3 つの節(%d 本)。ほかの書類には言えない(封 §5)。" % (bk[u"TSS"], bk[u"KAM"]))
    add(u"m 9", u"- 判定は司令塔(盲検でない)。封の予測も司令塔(AI の席 1 席)が書いた。封も予測も、結果を見てから書き換えていない。")
    add(u"m 10", u"- 独立監査は、script・記録・封の門について GO。監査の席の確かめ(記録なし)は §7 に分けて書いた。")
    add(u"m 11", u"- 取り出した出力そのもの(大きい)は repo に置かない。置いたのは 1 つの記録(数・鍵・札・当たった類だけ)で、文・値・要素名・主語の語・枠の id・pointer の字・会社名・証券コード・docID を持たない。")
    # ---- §10 次
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
    scan = doc
    for a in ALLOWED_USES:
        scan = scan.replace(a, u"")
    for w in TABLE_WORDS:
        if w in scan:
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
LEAD_NAMES = (u"lead 判定", u"lead 証拠", u"lead 境", u"lead 分母", u"lead H", u"lead engine", u"lead 読み")
#: 組んだ行を決めた節に置く(名前, 節の頭, 次の節の頭)
SECTION_PINS = (
    (u"w 理屈", u"## §2 ", u"## §3 "), (u"d1", u"## §7 ", u"## §8 "), (u"d5", u"## §7 ", u"## §8 "), (u"d6", u"## §7 ", u"## §8 "),
    (u"r 重なり", u"## §8 ", u"## §9 "), (u"r PA-6", u"## §8 ", u"## §9 "), (u"m 9", u"## §9 ", u"## §10 "), (u"n 全数", u"## §10 ", None),
    (u"b PA-6", u"## §1 ", u"## §2 "), (u"s6 近さ", u"## §1 ", u"## §2 "), (u"b 測れる", u"## §1 ", u"## §2 "))
#: 数を持たない要点の行(字で決めた節に 1 回ずつ)
PINNED_SECTIONS = (
    (u"## §10 ", None, u"- engine を変えるか(実績か計画かを結ぶ条件に入れる案。人間の決定)。入れるなら別の封(未使用の材料で・盲検の語の表で)が先に要る。"),
    (u"## §10 ", None, u"- 外に書くか(人間の決定)。"),
    (u"## §10 ", None, u"- `main` へのマージ(人間の決定)。"),
    (u"## §10 ", None, u"- 司令塔に任された残り(LLM の席の取り出しの便)は、別の封から始める。"),
)


def limits_problems(c):
    u"""要点の行が決めた節に 1 回ずつ在る。判定の語は表の行と要約が同じ向き。"""
    out = []
    lead = section(c.doc, LEAD_HEAD, LEAD_NEXT).split(u"\n")
    exp = dict(expected_lines(c))
    for k in LEAD_NAMES:
        if lead.count(exp[k]) != 1:
            out.append(u"limits: 要点の行が冒頭に 1 回ずつ無い: %s" % k)
    for name, head, nxt in SECTION_PINS:
        if section(c.doc, head, nxt).split(u"\n").count(exp[name]) != 1:
            out.append(u"limits: 組んだ行が決めた節に 1 回ずつ無い: %s" % name)
    for head, nxt, line in PINNED_SECTIONS:
        if section(c.doc, head, nxt).split(u"\n").count(line) != 1:
            out.append(u"limits: 決めた節に決めた行が 1 回ずつ無い: %s" % line[:20])
    lines = c.doc.split(u"\n")
    vd = verdicts(c)
    for pid, v in zip(IDS, vd):
        rows = [l for l in lines if l.startswith(u"| %s |" % pid)]
        if len(rows) != 1 or not rows[0].endswith(u"| %s |" % v) or (v == HIT and MISS in rows[0]):
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
    for need in (u"## §4 ", u"| PA-1 |", u"| PA-8 |", u"50% 以上 90% 以下", u"40% 以下", u"2% 以上 10% 以下", u"25% 以上", u"30 ポイント以上低い", u"50% 以上止め", u"5% 以下",
                 u"3% 以上 20% 以下", u"5 行以下", u"PA-6 が当たり(満たす段が在る)のときだけ", u"15 行未満", u"## §5 "):
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


def pred_key(c, prefix):
    ks = [k for k in c.rec[K_PRED] if k.startswith(prefix)]
    assert len(ks) == 1, prefix
    return ks[0]


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


def pool_of(c, which):
    f = Facts(c)
    return {
        u"plan": f.sum_of(f.plan, BATCHES), u"plan_ys_tss": f.plan[u"YS"] + f.plan[u"TSS"], u"other": f.sum_of(f.other, BATCHES), u"a": f.sum_of(f.a, GBATCHES),
        u"a_kam": f.a[u"KAM"], u"tss_g": f.tss_g, u"tss_v": f.tss_v, u"plan_tss": f.plan[u"TSS"], u"plan_ys": f.plan[u"YS"],
        u"v_kept": f.sum_of(f.plan, BATCHES) + f.sum_of(f.other, BATCHES)}[which]


def pick(c, which, n, stopped, stage=None):
    u"""判定の行の集まり(``which``)のうち、止めている(``stopped`` が True)か止めていない行を先頭から ``n`` 行返す。"""
    rows = [r for r in pool_of(c, which) if is_stop(r, stage) == stopped]
    assert len(rows) >= n, (which, stopped, stage, len(rows), n)
    return rows[:n]


def unstop(which, stage, n):
    u"""段 ``stage`` の止めを ``n`` 行はずす(段の包含のため、段 ``stage`` 以下も空にする)。記録の行を直接変える(Ctx の写しの行は ``Facts`` の行と同じ object)。"""
    def fn(c):
        for r in pick(c, which, n, True, stage):
            for t in range(1, stage + 1):
                r[5 + t] = u""
    return fn


def stop(which, stage, n):
    u"""段 ``stage`` で止めていない行を ``n`` 行止める(段 ``stage`` 以上にも同じ類の字を置く)。"""
    def fn(c):
        for r in pick(c, which, n, False, stage):
            for t in range(stage, 4):
                r[5 + t] = u"P"
    return fn


def sc_stop_more(n):
    u"""札つきの V の行のうち、この便の段 2 で止めていて便 SC の段 2 で止めていない行の ``n`` 行を、便 SC の側も止めた行にする(PA-8 の両方で止める行を増やす)。"""
    def fn(c):
        f = Facts(c)
        rows = [r for r in pool_of(c, u"v_kept") if is_stop(r, 2) and not f.sc_stop[tuple(r[:5])]]
        assert len(rows) >= n, (len(rows), n)
        for r in rows[:n]:
            c.sc_stop[tuple(r[:5])] = True
    return fn


def check_problems(check, c):
    return guard(CHECKS[check], c)


def relabel_ys_plan_side(c):
    u"""YS の「見積り・計画」の札の 1 行の「側」を別の節に変える(1 つの節の言い分を壊す)。行の鍵が合わなくなって引けない行になるため、行の側も同じに直す。"""
    lab = [l for l in c.labs if l[u"便"] == u"YS" and l[u"state"] == u"V" and l[u"種別"] == AT.KIND_OUT and l[u"先"] == PLAN][0]
    old_key = (lab[u"便"], lab[u"#"], lab[u"側"], lab[u"si"], lab[u"pos"])
    lab[u"側"] = u"研究開発活動"
    for r in c.rec[u"行"]:
        if tuple(r[:5]) == old_key:
            r[2] = u"研究開発活動"
    new_key = old_key[:2] + (u"研究開発活動",) + old_key[3:]
    c.sc_stop[new_key] = c.sc_stop.pop(old_key)


# a sha
M(u"a1 記録の 1 byte", u"sha", set_text(RECORD_REL, lambda t: t + b" "))
M(u"a2 script の 1 byte", u"sha", set_text(SCRIPT_REL, lambda t: t[:-1] + b"#"))
M(u"a3 封の門の 1 byte", u"sha", set_text(SEAL_GATE_REL, lambda t: t + b"\n"))
# b 記録
M(u"b1 記録の結んだ行の数を 1 つ変える(TSS の G の段 2)", u"record", bump([K_ALL, u"TSS", u"全体", u"G", u"止めた行", u"段 2"]))
M(u"b2 記録の予測の欄(PA-7b の分子)を 1 つ変える", u"record", lambda c: bump([K_PRED, pred_key(c, u"PA-7b "), u"段 2", u"分子"])(c))
M(u"b3 記録の行の 1 つの当たった類を空にする", u"record", lambda c: [r for r in c.rec[u"行"] if r[8] != u""][0].__setitem__(8, u""))
M(u"b4 記録に文・値の字を足す", u"record", lambda c: c.rec.__setitem__(u"漏れ", u"売上高は前期比 12.3 億円の増加となりました。"))
M(u"b5 記録の配線の確認の数を 1 つ変える(TSS の鍵と state が同じ行)", u"record", bump([K_WIRE, K_W_SC, u"TSS", u"鍵と state が同じ行"]))
M(u"b6 記録の入力の sha256 を 1 つ変える", u"record", set_at([u"入力", 0, u"sha256"], u"0" * 64))
M(u"b7 記録の札つきの行の数を 1 つ変える(「見積り・計画」の札の V の止めた行)", u"record", bump([K_LABEL, u"V の札", u"合計", V_PLAN, u"止めた行", u"段 2"]))
M(u"b8 記録の当たった類の数を 1 つ変える(段 2 の H)", u"record", bump([K_CLASS, u"TSS", u"段 2", u"V", u"H"]))
M(u"b9 記録の位置の確かめの数を 1 つ変える(符号か空白)", u"doc", bump([K_WIRE, K_W_POS, u"TSS", u"うち pos の字が符号か空白"]))
M(u"b10 記録の最上位に欄を足す", u"record", lambda c: c.rec.__setitem__(u"追記", 1))
M(u"b11 記録の行の鍵を 1 つ重ねる", u"record", lambda c: c.rec[u"行"].append(list(c.rec[u"行"][-1])))
M(u"b12 記録の便 SC との重なりの数を 1 つ変える(札つきの V の両方で止めた行)", u"record", bump([K_OVER, u"V の札(引けた行)", u"合計", u"札つきの V の行(分母から除く札は除く)", u"両方で止めた"]))
M(u"b13 記録の engine が止めた行の数を 1 つ変える(当たるはずの行)", u"record", bump([K_P, u"合計", u"全体", MS.P_KEYS[2]]))
# c 文書の数・表・散文
M(u"c1 表の実測の分子を 1 つ変える(PA-1)", u"doc", line_mut(u"table PA-1", u"18/27", u"19/27"))
M(u"c2 表の判定の当たりと外れを入れ替える(PA-6)", u"limits", lambda c: setattr(c, "doc", re.sub(r"(\| PA-6 \|.*?\| )当たり \|", r"\1**外れ** |", c.doc, count=1)))
M(u"c3 表の判定の当たりと外れを入れ替える(PA-1)", u"limits", lambda c: setattr(c, "doc", re.sub(r"(\| PA-1 \|.*?\| )当たり \|", r"\1**外れ** |", c.doc, count=1)))
M(u"c3b 表の判定の当たりと外れを入れ替える(PA-7b)", u"limits", lambda c: setattr(c, "doc", re.sub(r"(\| PA-7b \|.*?\| )当たり \|", r"\1**外れ** |", c.doc, count=1)))
M(u"c3c 表の判定の当たりと外れを入れ替える(PA-8)", u"limits", lambda c: setattr(c, "doc", re.sub(r"(\| PA-8 \|.*?\| )当たり \|", r"\1測れていない |", c.doc, count=1)))
M(u"c3d 表の判定の当たりと外れを入れ替える(PA-3)", u"limits", lambda c: setattr(c, "doc", re.sub(r"(\| PA-3 \|.*?\| )当たり \|", r"\1**外れ** |", c.doc, count=1)))
M(u"c3e 表の判定の当たりと外れを入れ替える(PA-4)", u"limits", lambda c: setattr(c, "doc", re.sub(r"(\| PA-4 \|.*?\| )当たり \|", r"\1**外れ** |", c.doc, count=1)))
M(u"c4 要約の本数を変える(当たり 9・外れ 0)", u"doc", doc_replace(u"(当たり 9・外れ 0)", u"(当たり 8・外れ 1)"))
M(u"c5 散文に記録に無い数を足す(組んだ行にない行)", u"doc", doc_append(u"\n- 追記: 12345 行。\n"))
M(u"c5b 散文に 1 桁の数を足す(組んだ行にない行)", u"doc", doc_append(u"\n- 追記: 0 行。\n"))
M(u"c6 結んだ行の表の数を 1 つ変える(TSS の V の段 2)", u"doc", line_mut(u"t3 TSS V", u"| 360 |", u"| 361 |"))
M(u"c7 結んだ行の表の結んだ行の数を変える(KAM 全体の G)", u"doc", line_mut(u"t3 KAM G", u"| 172 |", u"| 171 |"))
M(u"c8 札の表の数を変える(「見積り・計画」の札の V の合計)", u"doc", line_mut(u"v 合計 見積り・計画", u"| 27 | 27 |", u"| 27 | 26 |"))
M(u"c9 札の表の止めた行を変える(KAM のそれ以外)", u"doc", line_mut(u"v KAM それ以外", u"| 37 | 37 | 0 | 0 | 7 |", u"| 37 | 37 | 0 | 1 | 7 |"))
M(u"c10 G の札の表の数を変える(a の合計)", u"doc", line_mut(u"g 合計 a", u"| 214 | 214 | 0 | 6 | 34 |", u"| 214 | 214 | 0 | 6 | 35 |"))
M(u"c11 G の札の表の数を変える(b の合計)", u"doc", line_mut(u"g 合計 b", u"| 27 | 27 | 0 | 4 | 15 |", u"| 27 | 27 | 0 | 3 | 15 |"))
M(u"c12 類の表の数を変える(TSS の段 2 の V の H)", u"doc", line_mut(u"c TSS 2 V", u"| 360 | 77 | 184 | 0 | 311 | 0 |", u"| 360 | 77 | 184 | 0 | 310 | 0 |"))
M(u"c13 属性の表の数を変える(合計の「見積り・計画」)", u"doc", line_mut(u"v 属性 合計 外(見積り・計画)", u"| 27 | 27 | 4 | 18 | 25 |", u"| 27 | 27 | 4 | 17 | 25 |"))
M(u"c14 組んだ行を消す(位置の確かめ KAM)", u"doc", doc_line_edit(u"pos KAM", u""))
M(u"c15 禁止語を doc の check にも通す(証明した)", u"words", doc_append(u"\n証明" + u"した。\n"))
M(u"c16 散文の数を変える(読める事の段 2)", u"doc", line_mut(u"r 段 2", u"札 a の G 214 行のうち 6 行", u"札 a の G 214 行のうち 7 行"))
M(u"c17 限界の節の数を変える(材料の本数)", u"doc", line_mut(u"m 8", u"TSS 400 本", u"TSS 401 本"))
M(u"c18 全数の行に結果を書く", u"doc", doc_replace(u"結果はこの文書に書かない(引き継ぎに書く)。", u"結果は全部緑で 0 件だった(引き継ぎに書く)。"))
M(u"c19 表の「封の字」を変える(PA-1 の幅)", u"doc", doc_replace(u"50% 以上 90% 以下", u"50% 以上 95% 以下"))
M(u"c20 行の順を入れ替える(要約の 2 行)", u"doc", swap_lines(u"lead 境", u"lead 分母"))
M(u"c21 要約の率を変える(PA-7b の段 2)", u"doc", line_mut(u"lead 境", u"360/1858(19.4%)", u"360/1858(19.5%)"))
M(u"c22 要約の偏りの数を変える(YS の分母)", u"doc", line_mut(u"lead 分母", u"YS 7", u"YS 8"))
M(u"c23 配線の行の数を変える(KAM の行)", u"doc", line_mut(u"w KAM", u"引き直した結んだ行 209", u"引き直した結んだ行 208"))
M(u"c24 近さの行の数を変える(PA-7b)", u"doc", line_mut(u"lead 境", u"あと 12 行多ければ", u"あと 13 行多ければ"))
M(u"c25 PA-5 の差の字を変える", u"doc", line_mut(u"table PA-5", u"差 64.61 ポイント", u"差 64.60 ポイント"))
M(u"c26 PA-8 の字を変える(両方で止めた行)", u"doc", line_mut(u"table PA-8", u"両方で止めた行 1", u"両方で止めた行 0"))
M(u"c27 PA-6 の段の表の数を変える(段 2)", u"doc", line_mut(u"s6 段 2", u"18/27(66.7%)", u"18/27(66.8%)"))
M(u"c28 切り出しの表の数を変える(KAM の単体)", u"doc", line_mut(u"cut KAM 単体", u"| 192 | 9 |", u"| 191 | 9 |"))
M(u"c29 封との差の数を変える((1)でなく(5)の KAM)", u"doc", line_mut(u"d5", u"KAM の G 0", u"KAM の G 1"))
M(u"c30 封との差の数を変える((6)の便 SC だけ)", u"doc", line_mut(u"d6", u"便 SC だけが止めた行 288", u"便 SC だけが止めた行 289"))
M(u"c31 PA-3 の行の数を変える(KAM)", u"doc", line_mut(u"table PA-3", u"KAM 2/89", u"KAM 2/90"))
M(u"c32 PA-7a の行の数を変える", u"doc", line_mut(u"table PA-7a", u"96/6720", u"96/6721"))
M(u"c33 PA-4 の行の数を変える(段 3)", u"doc", line_mut(u"table PA-4", u"25/89", u"24/89"))
M(u"c34 結んだ行の合計の数を変える", u"doc", line_mut(u"t3 全部", u"YS 284", u"YS 283"))
M(u"c35 引けなかった札の行の数を変える", u"doc", line_mut(u"v 引けない", u"V の札は TSS 1", u"V の札は TSS 2"))
M(u"c36 見出しの類の数を変える", u"doc", line_mut(u"c 見出し", u"V で 311/360", u"V で 312/360"))
M(u"c37 engine が止めた行の表の数を変える(合計)", u"doc", line_mut(u"p 合計", u"| 859 | 560 | 299 | 299 | 0 |", u"| 859 | 560 | 299 | 298 | 1 |"))
M(u"c38 重なりの表の数を変える(札つきの V の合計)", u"doc", line_mut(u"o V 合計 札つきの V", u"| 173 | 1 | 54 | 20 | 98 |", u"| 173 | 1 | 54 | 21 | 97 |"))
M(u"c39 重なりの表の数を変える(結んだ行の TSS の V)", u"doc", line_mut(u"o 全部 TSS V", u"| 1858 | 15 | 601 | 345 | 897 |", u"| 1858 | 14 | 601 | 345 | 898 |"))
M(u"c40 重なりの G の札の表の数を変える(a)", u"doc", line_mut(u"o G 合計 a", u"| 214 | 0 | 9 | 6 | 199 |", u"| 214 | 0 | 9 | 7 | 198 |"))
M(u"c41 当たった類の言い分の数を変える(W)", u"doc", line_mut(u"c W", u"G 49", u"G 48"))
M(u"c42 限界の数を変える(類 E)", u"doc", line_mut(u"m 7", u"G 42・V 8", u"G 42・V 9"))
M(u"c43 当たるはずの行の行の数を変える", u"doc", line_mut(u"w 当たる", u"当たった行 299", u"当たった行 298"))
M(u"c44 YS の節の言い分を変える", u"doc", line_mut(u"v YS", u"1 つの節(配当政策)", u"1 つの節(研究開発活動)"))
M(u"c45 PA-6 の近さの数を変える", u"doc", line_mut(u"s6 近さ", u"あと 5 行少なければ", u"あと 4 行少なければ"))
M(u"c46 PA-1 の内訳の数を変える(TSS)", u"doc", line_mut(u"b PA-1", u"TSS 18/20(90.0%)", u"TSS 17/20(85.0%)"))
M(u"c47 PA-3 の近さの行の数を変える", u"doc", line_mut(u"b PA-3", u"あと 2 行少なければ", u"あと 3 行少なければ"))
M(u"c48 重なりの言い分の数を変える", u"doc", line_mut(u"r 重なり", u"両方で止めた行が 1 で", u"両方で止めた行が 2 で"))
M(u"c49 PA-6 の「測れる」の行の数を変える", u"doc", line_mut(u"b 測れる", u"「見積り・計画」の札の V の引けた行は 27", u"「見積り・計画」の札の V の引けた行は 26"))
M(u"c50 要約の読みの行を数の側から変える(満たす段)", u"limits", line_mut(u"lead 読み", u"満たす段は段 2 だけ", u"満たす段は段 3 だけ"))
M(u"c51 限界の節の数を変える(この便で分かったこと)", u"doc", line_mut(u"m 見出し", u"107 文", u"108 文"))
M(u"c52 要約の見出しの行の数を変える(H だけの行)", u"doc", line_mut(u"lead H", u"H だけで止まった行は 132 行", u"H だけで止まった行は 131 行"))
M(u"c53 §1 の「測れる」の行を節の外へ動かす", u"limits", lambda c: setattr(c, "doc", c.doc.replace(dict(expected_lines(Ctx()))[u"b 測れる"] + u"\n", u"", 1) + u"\n" + dict(expected_lines(Ctx()))[u"b 測れる"] + u"\n"))
# d 判定(記録の行を変えて、判定を動かす。集計の欄は触らない)
M(u"d1 「見積り・計画」の札の V の止めを 6 行はずして PA-1 を幅の下に動かす", u"judge", unstop(u"plan", 2, 6))
M(u"d2 「見積り・計画」の札の V の止めを 7 行足して PA-1 を幅の上に動かす", u"judge", stop(u"plan", 2, 7))
M(u"d3 「見積り・計画」の札の V の段 1 の止めを 7 行足して PA-2 を外れに動かす", u"judge", stop(u"plan", 1, 7))
M(u"d4 札 a の G の止めを 16 行足して PA-3 を外れに動かす(段 2 が 10% を超える)", u"judge", stop(u"a", 2, 16))
M(u"d5 札 a の G の止めを 2 行はずして PA-3 を外れに動かす(段 2 が 2% を割る)", u"judge", unstop(u"a", 2, 2))
M(u"d6 KAM の札 a の G の段 3 の止めを 3 行はずして PA-4 を外れに動かす", u"judge", unstop(u"a_kam", 3, 3))
M(u"d7 それ以外の札の V の段 2 の止めを 60 行足して PA-5 を外れに動かす", u"judge", stop(u"other", 2, 60))
M(u"d8 「見積り・計画」の札の V の止めを 5 行はずして PA-6 を外れに動かす(段 2 が 50% を割る)", u"judge", unstop(u"plan", 2, 5))
M(u"d9 札 a の G の段 2 の止めを 5 行足して PA-6 を外れに動かす(段 2 が 5% を超える)", u"judge", stop(u"a", 2, 5))
M(u"d10 TSS の G の段 2 の止めを 600 行足して PA-7a を外れに動かす", u"judge", stop(u"tss_g", 2, 600))
M(u"d11 TSS の V の段 2 の止めを 12 行足して PA-7b を外れに動かす(上の境)", u"judge", stop(u"tss_v", 2, 12))
M(u"d12 TSS の V の段 2 の止めを 310 行はずして PA-7b を外れに動かす(下の境)", u"judge", unstop(u"tss_v", 2, 310))
M(u"d13 便 SC の段 2 で止めた行を 5 行増やして PA-8 を外れに動かす", u"judge", sc_stop_more(5))
M(u"d14 判定の欄(PA-1 の分子)を 1 つ変える", u"judge", lambda c: bump([K_PRED, pred_key(c, u"PA-1 "), u"3 便の合計", u"段 2", u"分子"])(c))
M(u"d15 判定の欄(PA-5 の率の差)を変える", u"judge", lambda c: set_at([K_PRED, pred_key(c, u"PA-5 率の差"), u"段 2"], u"64.62")(c))
M(u"d16 判定の欄(PA-8 の参考の行)を 1 つ変える", u"judge", lambda c: bump([K_PRED, pred_key(c, u"PA-8 参考"), u"行"])(c))
M(u"d17 判定の欄(分母の確かめ)を 1 つ変える", u"judge", lambda c: bump([K_PRED, pred_key(c, u"分母の確かめ"), u"G の札の行(引けた)"])(c))
M(u"d18 判定の欄(PA-6 の札 a の G の分子)を 1 つ変える", u"judge", lambda c: bump([K_PRED, pred_key(c, u"PA-6 "), u"段 2", u"札 a の G の行", u"分子"])(c))
M(u"d19 YS の「見積り・計画」の札の 1 行を別の節に動かす(1 つの節の言い分)", u"judge", relabel_ys_plan_side)
# e 語
M(u"e1 禁止語(ハルシネーション)", u"words", doc_append(u"\nハルシ" + u"ネーション\n"))
M(u"e2 会社名らしい字", u"words", doc_append(u"\n株式会社\n"))
M(u"e3 3 桁以上の漢数字", u"words", doc_append(u"\n二百社\n"))
M(u"e4 docID の形", u"words", doc_append(u"\nS100" + u"AB12\n"))
M(u"e5 要点の字を消す(全部当たったことは規則の良さの証拠ではない)", u"words", doc_replace(u"全部当たったことは規則の良さの証拠ではない", u"全部当たった", True))
M(u"e6 封の commit を言わない", u"words", doc_replace(u"e69b733c", u"0000000", True))
M(u"e7 禁止語(人の目)", u"words", doc_append(u"\n人の" + u"目で読んだ。\n"))
M(u"e8 要点の字を消す(前の便の数を見てから幅を書いた)", u"words", doc_replace(u"前の便(AT・PS・SC)の数を見てから幅を書いた", u"幅を書いた", True))
M(u"e9 記録の commit を言わない", u"words", doc_replace(u"9736eae1", u"0000000", True))
M(u"e10 要点の字を消す(別の封)", u"words", doc_replace(u"別の封(未使用の材料で・盲検の語の表で)", u"別の封", True))
M(u"e11 要素名の形の字", u"words", doc_append(u"\njppfs_cor:NetSales\n"))
M(u"e12 封 §2 の表の語を書く(類 P の語)", u"words", doc_append(u"\n" + u"見" + u"込" + u"\n"))
M(u"e13 封 §2 の表の語を書く(類 F の語)", u"words", doc_append(u"\n" + u"翌" + u"期" + u"\n"))
M(u"e14 封 §2 の表の語を書く(類 E の語)", u"words", doc_append(u"\n" + u"仮" + u"定" + u"\n"))
M(u"e15 封 §2 の表の語を書く(札の名前の外の「計画」)", u"words", doc_append(u"\n" + u"計" + u"画" + u"\n"))
M(u"e16 pointer の字を書く", u"words", doc_append(u"\n" + u"NonConsol" + u"idated" + u"\n"))
M(u"e17 要点の字を消す(盲検でない)", u"words", doc_replace(u"盲検でない", u"盲検", True))
# 要点の文
M(u"l1 要約の判定の行を変える", u"limits", doc_line_edit(u"lead 判定", u"- 判定は全部当たり。"))
M(u"l2 §7 の要点の行を変える((5))", u"limits", doc_line_edit(u"d5", u"- (5) 段 1 は KAM・YS で 0 行。"))
M(u"l3 §2 の要点の行を変える(縛るのは読みであって効きではない)", u"limits", doc_line_edit(u"w 理屈", u"- この確かめは規則の効きを縛る。"))
M(u"l4 要約の読みの行を変える", u"limits", doc_line_edit(u"lead 読み", u"- 規則を engine に入れる。"))
M(u"l5 判定は司令塔の行を変える", u"limits", doc_line_edit(u"m 9", u"- 判定は独立監査。"))
M(u"l6 PA-6 の表の行から当たりを消す", u"limits", lambda c: setattr(c, "doc", re.sub(r"(\| PA-6 \|.*?\| )当たり \|", r"\1判定しない |", c.doc, count=1)))
M(u"l7 次の節の人間の決定の行を消す", u"limits", doc_replace(u"- 外に書くか(人間の決定)。", u"- 外に書く。"))
M(u"l8 要約の境の行を変える", u"limits", doc_line_edit(u"lead 境", u"- 境から遠い。"))
M(u"l9 要約の分母の行を変える", u"limits", doc_line_edit(u"lead 分母", u"- 偏りは無い。"))
M(u"l10 要約の見出しの行を変える", u"limits", doc_line_edit(u"lead H", u"- 見出しは関係ない。"))
M(u"l11 要約の証拠の行を変える", u"limits", doc_line_edit(u"lead 証拠", u"- 全部当たったので規則は良い。"))
M(u"l12 司令塔に任された残りの行を変える", u"limits", doc_replace(u"- 司令塔に任された残り(LLM の席の取り出しの便)は、別の封から始める。", u"- 残りは無い。"))
M(u"l13 重なりの言い分の行を節の外へ動かす", u"limits", lambda c: setattr(c, "doc", c.doc.replace(dict(expected_lines(Ctx()))[u"r 重なり"] + u"\n", u"", 1) + u"\n" + dict(expected_lines(Ctx()))[u"r 重なり"] + u"\n"))
# f 封
M(u"f1 封の PA-1 の字を替える(根の字)", u"seal", seal_replace(u"50% 以上 90% 以下", u"50% 以上 95% 以下"))
M(u"f2 封の読み方の決めの字を替える", u"seal", seal_replace(u"PA-6 が当たり(満たす段が在る)のときだけ", u"PA-6 が外れたときだけ"))
M(u"f3 封の文の途中の 1 字", u"frozen", seal_replace(u"0 USD(LLM の席を呼ばない)", u"0 USD(LLM の席を呼ぶ)"))
M(u"f4 封の PA-1 の境を替える(判定が外れに動く)", u"judge", seal_replace(u"50% 以上 90% 以下", u"70% 以上 90% 以下"))
M(u"f5 封の PA-6 の境を替える(判定が外れに動く)", u"judge", seal_replace(u"を 50% 以上止め", u"を 70% 以上止め"))
M(u"f6 封の PA-2 の境を替える(判定が外れに動く)", u"judge", seal_replace(u"のうち止めるのは 40% 以下", u"のうち止めるのは 10% 以下"))
M(u"f7 封の測れない境を替える(判定が測れていないに動く)", u"judge", seal_replace(u"の引けた分母が 15 行未満", u"の引けた分母が 40 行未満"))
M(u"f8 封の PA-7b の境を替える(判定が外れに動く)", u"judge", seal_replace(u"3% 以上 20% 以下", u"3% 以上 19% 以下"))
M(u"f9 封の PA-5 の境を替える(判定が外れに動く)", u"judge", seal_replace(u"より 30 ポイント以上低い", u"より 70 ポイント以上低い"))
M(u"f10 封の PA-3 の境を替える(判定が外れに動く)", u"judge", seal_replace(u"2% 以上 10% 以下", u"3% 以上 10% 以下"))
M(u"f11 封の PA-7a の境を替える(判定が外れに動く)", u"judge", seal_replace(u"止めるのは 10% 以下 | 10% を超えたら外れ", u"止めるのは 1% 以下 | 10% を超えたら外れ"))
M(u"f12 封の PA-6 の G の境を替える(判定が外れに動く)", u"judge", seal_replace(u"札 a の G の行を止めるのは 5% 以下", u"札 a の G の行を止めるのは 2% 以下"))
M(u"f13 封の PA-8 の境を替える(判定が外れに動く)", u"judge", seal_replace(u"両方で止める行は 5 行以下", u"両方で止める行は 0 行以下"))
M(u"f14 封の PA-4 の境を替える(判定が外れに動く)", u"judge", seal_replace(u"止めるのは 25% 以上", u"止めるのは 30% 以上"))


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
        self.assertIn(u"18/27(66.7%)(段 1 4/27(14.8%)・段 3 25/27(92.6%)。TSS 18/20(90.0%)・KAM 分母 0・YS 0/7(0.0%)) | 当たり |", exp[u"table PA-1"])
        self.assertIn(u"4/27(14.8%)(段 2 18/27(66.7%)・段 3 25/27(92.6%)) | 当たり |", exp[u"table PA-2"])
        self.assertIn(u"6/214(2.8%)(KAM 2/89(2.2%)・YS 4/125(3.2%)。段 1 0/214(0.0%)・段 3 34/214(15.9%)) | 当たり |", exp[u"table PA-3"])
        self.assertIn(u"段 3 25/89(28.1%)(段 1 0/89(0.0%)・段 2 2/89(2.2%)) | 当たり |", exp[u"table PA-4"])
        self.assertIn(u"それ以外 3/146(2.1%)・見積り・計画 18/27(66.7%)・差 64.61 ポイント | 当たり |", exp[u"table PA-5"])
        self.assertIn(u"満たす段は段 2(18/27(66.7%) と 6/214(2.8%)) | 当たり |", exp[u"table PA-6"])
        self.assertIn(u"96/6720(1.4%)(段 1 35/6720(0.5%)・段 3 124/6720(1.8%)) | 当たり |", exp[u"table PA-7a"])
        self.assertIn(u"360/1858(19.4%)(段 1 77/1858(4.1%)・段 3 377/1858(20.3%)) | 当たり |", exp[u"table PA-7b"])
        self.assertIn(u"両方で止めた行 1(札つきの V 173 行。便 SC だけ 54・この便だけ 20・どちらも止めない 98) | 当たり |", exp[u"table PA-8"])
        self.assertIn(u"| TSS | V | 1858 | 77 | 360 | 377 |", exp[u"t3 TSS V"])
        self.assertIn(u"| KAM 全体 | G | 172 | 0 | 2 | 44 |", exp[u"t3 KAM G"])
        self.assertIn(u"| YS 全体 | G | 266 | 0 | 10 | 26 |", exp[u"t3 YS G"])
        self.assertIn(u"| 合計 | 見積り・計画 | 27 | 27 | 4 | 18 | 25 |", exp[u"v 合計 見積り・計画"])
        self.assertIn(u"| 合計 | a | 214 | 214 | 0 | 6 | 34 |", exp[u"g 合計 a"])
        self.assertIn(u"| 合計 | 段 2 | V | 361 | 77 | 185 | 0 | 311 | 0 |", exp[u"c 合計 2 V"])
        self.assertIn(u"あと 5 行少なければ 50% を下回り", exp[u"s6 近さ"])
        self.assertIn(u"あと 5 行多ければ 5% を超える", exp[u"s6 近さ"])
        self.assertIn(u"| 合計 | 859 | 560 | 299 | 299 | 0 |", exp[u"p 合計"])
        self.assertIn(u"311 行(75 本の 107 文に在る)", exp[u"lead H"])
        self.assertIn(u"H だけで止まった行は 132 行", exp[u"lead H"])

    def test_d_1_the_judgement_is_redone_from_the_seal_text_and_the_record_rows(self):
        self.assertEqual([], judge_problems(Ctx()))

    def test_d_2_the_real_judgement_is_nine_hits(self):
        c = Ctx()
        self.assertEqual(verdicts(c), (HIT,) * 9)
        self.assertEqual([i for i, v in zip(IDS, verdicts(c)) if v == MISS], [])

    def test_d_3_the_bounds_are_read_from_the_seal_text(self):
        F = fractions.Fraction
        self.assertEqual(dict(seal_bounds(Ctx().seal)), {
            u"PA-1": (F(50, 100), F(90, 100)), u"PA-2": F(40, 100), u"PA-3": (F(2, 100), F(10, 100)), u"PA-4": F(25, 100), u"PA-5": 30, u"PA-6": (F(50, 100), F(5, 100)),
            u"PA-7a": F(10, 100), u"PA-7b": (F(3, 100), F(20, 100)), u"PA-8": 5, u"測れない": 15})

    def test_d_4_the_numbers_of_the_judgement_are_counted_from_the_rows_and_labels_by_hand(self):
        n = numbers(Facts(Ctx()))
        self.assertEqual(n[u"plan"], (27, {1: 4, 2: 18, 3: 25}))
        self.assertEqual(n[u"plan_ys_tss"], (27, {1: 4, 2: 18, 3: 25}))
        self.assertEqual(n[u"other"], (146, {1: 2, 2: 3, 3: 11}))
        self.assertEqual(n[u"a"], (214, {1: 0, 2: 6, 3: 34}))
        self.assertEqual(n[u"a_kam"], (89, {1: 0, 2: 2, 3: 25}))
        self.assertEqual(n[u"tss_g"], (6720, {1: 35, 2: 96, 3: 124}))
        self.assertEqual(n[u"tss_v"], (1858, {1: 77, 2: 360, 3: 377}))
        self.assertEqual(n[u"over"], (173, 1, 54, 20, 98))

    def test_d_5_pa6_is_met_by_stage_two_only_and_the_near_edges_are_counted(self):
        c = Ctx()
        self.assertEqual(direction(c), (True,) * 7)
        self.assertEqual(satisfied_stages(c), [2])
        self.assertEqual(bias_problems(c), [])
        self.assertEqual(dict(slacks(c)), {u"pa3": 1, u"pa4": 2, u"pa7b": 11, u"pa6v": 4, u"pa6g": 4})

    def test_d_6_the_labels_are_422_rows_and_the_unmatched_one_is_a_tss_v(self):
        f = Facts(Ctx())
        self.assertEqual(sum(f.v_label_n.values()), 175)
        self.assertEqual(sum(f.g_label_n.values()), 247)
        self.assertEqual(sum(len(f.v[b]) for b in BATCHES), 174)
        self.assertEqual(len(f.v[u"TSS"]), 119)

    def test_d_7_the_plan_rows_are_tss_20_ys_7_kam_0_and_the_ys_ones_are_in_one_section(self):
        f = Facts(Ctx())
        self.assertEqual((len(f.plan[u"TSS"]), len(f.plan[u"KAM"]), len(f.plan[u"YS"])), (20, 0, 7))
        self.assertEqual(len(f.plan_sides), 1)

    def test_d_8_the_stage_one_of_kam_and_ys_is_zero_in_every_joined_row(self):
        rows = Ctx().rec[u"行"]
        self.assertEqual(sum(1 for r in rows if r[0] in (u"KAM", u"YS") and r[6] != u""), 0)

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
        self.assertGreaterEqual(len(expset), 200)

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
        rels = (RECORD_REL, SCRIPT_REL, SEAL_REL, DOC_REL, SEAL_GATE_REL, SC_RECORD_REL)
        before = dict((rel, hashlib.sha256(read_bytes(rel)).hexdigest()) for rel in rels)
        c = Ctx()
        c.rec[K_ALL][u"TSS"][u"全体"][u"G"][u"結んだ行"] = 1
        c.rec[u"行"][0][8] = u"x"
        c.doc = u"x"
        c.labs[0][u"側"] = u"x"
        key = next(iter(c.sc_stop))
        c.sc_stop[key] = not c.sc_stop[key]
        self.assertNotEqual(1, Ctx().rec[K_ALL][u"TSS"][u"全体"][u"G"][u"結んだ行"])
        self.assertNotEqual(u"x", Ctx().rec[u"行"][0][8])
        self.assertNotEqual(u"x", Ctx().doc)
        self.assertNotEqual(u"x", Ctx().labs[0][u"側"])
        self.assertNotEqual(c.sc_stop[key], Ctx().sc_stop[key])
        self.assertNotEqual(u"x", labels()[0][u"側"])
        self.assertEqual(before, dict((rel, hashlib.sha256(read_bytes(rel)).hexdigest()) for rel in rels))

    def test_m_4_the_mutation_table_covers_every_check_and_every_effect_named_in_the_brief(self):
        self.assertEqual(set(CHECKS), set(ch for _l, ch, _f in MUTATIONS))
        labels_ = u"\n".join(l for l, _c, _f in MUTATIONS)
        for need in (u"記録の 1 byte", u"script の 1 byte", u"表の実測の分子", u"当たりと外れを入れ替える", u"散文に記録に無い数", u"散文の数", u"禁止語", u"漢数字", u"要点の",
                     u"封の文の途中の 1 字", u"PA-1 を幅の下", u"PA-1 を幅の上", u"PA-2 を外れに", u"PA-3 を外れに", u"PA-4 を外れに", u"PA-5 を外れに", u"PA-6 を外れに",
                     u"PA-7a を外れに", u"PA-7b を外れに", u"PA-8 を外れに", u"測れていないに動く", u"行の順を入れ替える", u"判定の欄", u"封 §2 の表の語", u"当たった類",
                     u"1 つの節"):
            self.assertIn(need, labels_)
        self.assertGreaterEqual(len(MUTATIONS), 120)

    def test_m_5_a_hit_turned_to_a_miss_is_caught_by_the_judge_and_not_only_by_the_table(self):
        c = Ctx()
        unstop(u"plan", 2, 5)(c)                                                   # PA-6 が外れに動く。文書の表は当たりのまま
        jd = dict(judge(c))
        self.assertFalse(jd[u"PA-6"])
        self.assertNotEqual([], judge_problems(c))

    def test_m_6_the_judge_follows_the_seal_bounds_not_a_pinned_number(self):
        c = Ctx()
        c.seal = c.seal.replace(u"50% 以上 90% 以下", u"70% 以上 90% 以下", 1)
        self.assertFalse(dict(judge(c))[u"PA-1"])                                  # 18/27 は 66.7%。70% 以上の幅では外れ
        c.seal = c.seal.replace(u"70% 以上 90% 以下", u"66% 以上 90% 以下", 1)
        self.assertTrue(dict(judge(c))[u"PA-1"])
        c.seal = c.seal.replace(u"66% 以上 90% 以下", u"50% 以上 66% 以下", 1)
        self.assertFalse(dict(judge(c))[u"PA-1"])                                  # 上の境 66% も 66.7% は超える

    def test_m_7_the_judge_compares_exact_fractions_at_the_edges(self):
        u"""PA-3(段 2 の札 a の G 6/214): 1 行はずして 5/214=2.34% は当たり・2 行はずして 4/214=1.87% は外れ。PA-4(KAM 段 3 の 25/89): 2 行はずして 23/89 は当たり・3 行で 22/89 は外れ。
        PA-7b(360/1858): 11 行足して 371/1858=19.97% は当たり・12 行で 372/1858=20.02% は外れ。PA-6: 「見積り・計画」の V は 4 行はずして 14/27 は満たす・5 行で 13/27 は満たさない。札 a の G は 4 行足して 10/214 は満たす・5 行で 11/214 は満たさない。"""
        def j(c, pid):
            return dict(judge(c))[pid]
        c = Ctx()
        unstop(u"a", 2, 1)(c)
        self.assertTrue(j(c, u"PA-3"))
        unstop(u"a", 2, 1)(c)
        self.assertFalse(j(c, u"PA-3"))
        c = Ctx()
        unstop(u"a_kam", 3, 2)(c)
        self.assertTrue(j(c, u"PA-4"))
        unstop(u"a_kam", 3, 1)(c)
        self.assertFalse(j(c, u"PA-4"))
        c = Ctx()
        stop(u"tss_v", 2, 11)(c)
        self.assertTrue(j(c, u"PA-7b"))
        stop(u"tss_v", 2, 1)(c)
        self.assertFalse(j(c, u"PA-7b"))
        c = Ctx()
        unstop(u"plan", 2, 4)(c)
        self.assertEqual(satisfied_stages(c), [2])
        self.assertTrue(j(c, u"PA-6"))
        unstop(u"plan", 2, 1)(c)
        self.assertEqual(satisfied_stages(c), [])
        self.assertFalse(j(c, u"PA-6"))
        c = Ctx()
        stop(u"a", 2, 4)(c)
        self.assertEqual(satisfied_stages(c), [2])
        self.assertTrue(j(c, u"PA-6"))
        stop(u"a", 2, 1)(c)
        self.assertEqual(satisfied_stages(c), [])
        self.assertFalse(j(c, u"PA-6"))

    def test_m_8_the_judge_has_nine_items_in_the_seal_order(self):
        c = Ctx()
        self.assertEqual(len(judge(c)), 9)
        self.assertEqual([i for i, _ok in judge(c)], list(IDS))

    def test_m_9_a_small_plan_denominator_is_not_measured_and_gets_no_hit_or_miss(self):
        c = Ctx()
        c.seal = c.seal.replace(u"の引けた分母が 15 行未満", u"の引けた分母が 40 行未満", 1)
        v = verdicts(c)
        self.assertEqual((v[0], v[1], v[4], v[5]), (UNMEASURED,) * 4)               # PA-1・PA-2・PA-5・PA-6
        self.assertEqual((v[2], v[3], v[6], v[7], v[8]), (HIT,) * 5)

    def test_m_10_the_bias_claims_turn_red_when_ys_reaches_half_or_tss_falls_below(self):
        c = Ctx()
        self.assertEqual([], bias_problems(c))
        stop(u"plan_ys", 2, 4)(c)                                                  # YS は 4/7 = 57.1%(50% 以上)
        self.assertNotEqual([], bias_problems(c))
        c = Ctx()
        unstop(u"plan_tss", 2, 10)(c)                                              # TSS は 8/20 = 40.0%(50% 未満)
        self.assertNotEqual([], bias_problems(c))

    def test_m_11_the_overlap_is_read_from_the_sc_record_not_from_the_pa_record(self):
        c = Ctx()
        f = Facts(c)
        rows = pool_of(c, u"v_kept")
        self.assertEqual(f.over(rows)[1], 1)
        both = [r for r in rows if is_stop(r, 2) and c.sc_stop[tuple(r[:5])]]
        self.assertEqual(len(both), 1)
        c.sc_stop[tuple(both[0][:5])] = False
        self.assertEqual(Facts(c).over(pool_of(c, u"v_kept"))[1], 0)


class WiringTest(unittest.TestCase):
    def test_n_1_this_gate_carries_no_docid_and_no_key(self):
        src = read(GATE_REL)
        for bad in (u"ANTHRO" + u"PIC", u"API_" + u"KEY", u"url" + u"lib", u"sock" + u"et"):
            self.assertNotIn(bad, src)
        self.assertIsNone(DOCID_RE.search(src))

    def test_n_2_this_gate_does_not_widen_the_boundary_import_list(self):
        with io.open(os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py"), encoding="utf-8") as fh:
            t = fh.read()
        self.assertNotIn(u"plan_attr", t)

    def test_n_3_this_gate_does_not_use_the_reserved_names(self):
        self.assertEqual([], SG.reserved_problems(rel=GATE_REL))

    def test_n_4_this_gate_leaves_sys_modules_as_it_found_them(self):
        before = dict(sys.modules)
        mod = load_module(GATE_REL, "pa_result_gate_sysmodules_check")
        changed = [k for k, v in before.items() if sys.modules.get(k) is not v]
        self.assertEqual([], changed)
        del mod


if __name__ == "__main__":
    unittest.main()
