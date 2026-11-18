# -*- coding: utf-8 -*-
"""結果の門: 封 docs/XBRL_SUMMARY_ENGINE_SEAL_2026-11-18.md(fabd87ba)の結果の文書 docs/XBRL_SUMMARY_ENGINE_RESULT_2026-11-18.md。

封の門 ``test_xbrl_summary_engine_seal.py`` の次の段。**追跡されている記録・script・封・結果の文書と git の履歴だけを読む**(材料は読まない。全数の作り直しは走らせない)。

縛るもの(検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表で 1 つずつ。木の file は変異させず、``Ctx`` の写しに当てる)
 a script・記録・封の門の sha256(字で留める)
 b 記録の中の整合: 封の門の ``record_problems``(行からの数え直し・予測の判定に要る数の作り直し・文や値の漏れ)+ 最上位の欄の一覧
 c 結果の文書の数: 数字を含む行は全部、記録から組んだ行と字で同じ(組んだ行は文書に決めた回数だけ在り、順も同じ)。そのどれにも当たらない行に数字が在れば赤
 d 予測 SE-1〜SE-7(SE-2a・SE-2b は別々。計 8 本)の判定を、封の予測の字から取った境と記録の行(段 2 の行・変わった行の一覧)から門が自分で決め直して、
   記録の「予測の判定に要る数」・文書の表と同じ・字で留めた判定と同じ。冒頭の「下に外れた」「幅の中」の向きも同じ
 e 文書に禁止語・会社名らしい字・docID・3 桁以上の漢数字・要素名や pointer の形が無い・要点の字が在る
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


SG = load_module("tests/measure/test_xbrl_summary_engine_seal.py", "se_seal_gate_for_se_result_gate")      # 封の門の部品。門としては走らせない
PR = SG.PR

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
RECORD_COMMIT_SHORT = "563369f1"                              # script・記録・封の門の commit(履歴から探した値と照らす)
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
RECORD_REL = SG.RECORD_REL
GATE_REL = "tests/measure/test_xbrl_summary_engine_result.py"
DOC_REL = "docs/XBRL_SUMMARY_ENGINE_RESULT_2026-11-18.md"

SHA_PIN = collections.OrderedDict([
    (RECORD_REL, "18111cb06db9096008dfc3416785248eedf3439fa7f2ea3dd16c8e76693b4fac"),
    (SCRIPT_REL, "1e3b2b28e21c877c62e506706f6b4e8c08fb8fa280f4824482ef92a160f54d7c"),
    (SEAL_GATE_REL, "269edeff2c60a636a25d4fb0bf05e4d24682c9055addc1cc21b5d2edb00df42e")])

STATES = SG.STATES
G, VM, UN, PN = STATES
LABELS = SG.LABELS
L_NA, L_FE, L_NS, L_OV, L_BOTH, L_VAL, L_NAME, L_NONE = LABELS
EXACT, LOOSE = SG.EXACT, SG.LOOSE
K_RT, K_S1, K_S2, K_PRED, K_FG = SG.K_RT, SG.K_S1, SG.K_S2, SG.K_PRED, SG.K_FG
K_CUT = u"切り出し"
K_DIFF = u"変わった行(state・reason・pointer のどれか。pointer だけの行も入る)"
K_TR = u"state の移り変わり(前 → 後。両方に在る行)"
K_OVER = u"読みの軸との重ね"
LIT, FAM = SG.LIT, SG.FAM
REASON_P = SG.REASON_P
IDS = (u"SE-1", u"SE-2a", u"SE-2b", u"SE-3", u"SE-4", u"SE-5", u"SE-6", u"SE-7")
HIT, MISS = u"当たり", u"**外れ**"
VERDICT_PINNED = (HIT, HIT, HIT, HIT, MISS, MISS, HIT, HIT)
TOP_KEYS = (u"seal", u"封の commit", u"step", u"この script の sha256", u"入力", u"engine の指紋(今。便 RT の記録の今と同じ)", u"profile", u"材料", K_CUT, K_RT, K_S1, K_FG,
            K_S2, K_PRED, u"限界", u"時間(秒)", u"key_leaks")

FORBIDDEN_WORDS = (u"証明" + u"した", u"ハルシ" + u"ネーション", u"精" + u"度", u"世界で 1 " + u"社")
COMPANY_WORDS = (u"株式会社", u"有限会社", u"合同会社", u"㈱", u"(株)")
DOCID_RE = re.compile(r"S100[0-9A-Z]{4}")
POINTER_RE = re.compile(r"xbrl:|jppfs|jpcrp|jpdei|_cor:|@(Current|Prior)|formula:|Summary_")
KANJI_NUM_RE = re.compile(u"[二三四五六七八九]百|[一二三四五六七八九]千|百[一二三四五六七八九十]|千[一二三四五六七八九百]")
HUMAN_EYE_RE = re.compile(u"人の" + u"目")
REQUIRED_PHRASES = (u"先に負けと限界を書く", u"外れ", u"当たり", u"追跡する記録に無い", u"監査の席の確かめ", u"人間の決定", u"限界", u"engine は 0 行", u"付けていない", u"REVISE",
                    u"引き継ぎに書く", u"値だけの行を 1 行ずつ読むまで書かない", u"つまり動いたのは、予想の枠を読んだからではない", u"判定は司令塔(盲検でない)")


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
# 記録の読み出し(門の側で独立に。段 2 は行から数える)
class Facts(object):
    u"""記録の行から数えた数。集計の欄は使わず、行(段 2 の行・変わった行の一覧・札の行)から数える。"""

    def __init__(self, c):
        rec = c.rec
        self.rec = rec
        s1 = rec[K_S1]
        self.s1 = s1
        w = s1[u"全体"]
        self.w = w
        self.diff = [tuple(x) for x in s1[K_DIFF]]
        self.only_b = len(s1[u"前にだけ在る行"])
        self.only_a = len(s1[u"後にだけ在る行"])
        self.rows = rec[K_S2][u"行"]
        self.overlay_rows = rec[K_S2][K_OVER][u"札の行"]
        self.group = dict((tuple(r[:3]), r[3]) for r in self.rows)
        self.tr = w[K_TR]
        self.n_rows = w[u"前の行"]
        self.n_both = w[u"両方に在る行"]
        self.n_state = sum(1 for x in self.diff if x[3] != x[4])
        self.n_book = len(set(x[0] for x in self.diff if x[3] != x[4]))
        self.to_un = collections.Counter((x[3], x[4]) for x in self.diff if x[3] != x[4])
        self.p_new = sum(1 for x in self.diff if x[6] == REASON_P and x[5] != REASON_P)
        self.p_before = sum(1 for x in self.diff if x[5] == REASON_P)
        self.n_g_before = sum(self.tr[u"%s → %s" % (G, b)] for b in STATES)
        self.n_g_lost = sum(1 for x in self.diff if x[3] == G and x[4] != G)
        self.n_g_new = sum(1 for x in self.diff if x[3] != G and x[4] == G)
        self.n_p_rows = len(self.rows)

    def t(self, a, b):
        return self.tr[u"%s → %s" % (a, b)]

    def before_count(self, s):
        return sum(self.t(s, b) for b in STATES)

    def after_count(self, s):
        return sum(self.t(a, s) for a in STATES)

    def lab(self, rd):
        i = 4 if rd == LIT else 8
        return collections.Counter(r[i] for r in self.rows)

    def lab_o(self, rd):
        i = 7 if rd == LIT else 11
        return collections.Counter(r[i] for r in self.rows)

    def anyv(self, rd):
        i = 5 if rd == LIT else 9
        return sum(1 for r in self.rows if r[i])

    def den12(self, rd):
        c = self.lab(rd)
        return sum(c.values()) - c[L_NA] - c[L_FE]

    def ns_ov(self, rd):
        c = self.lab(rd)
        return c[L_NS] + c[L_OV]

    def sub34(self, rd):
        i = 4 if rd == LIT else 8
        iv = 5 if rd == LIT else 9
        return collections.Counter(r[i] for r in self.rows if r[i] in (L_NS, L_OV) and r[iv])

    def ways(self, rd):
        i, ih = (4, 6) if rd == LIT else (8, 10)
        return collections.Counter(r[ih] for r in self.rows if r[i] == L_BOTH)

    def overlay_groups(self):
        u"""読みの軸の組(甲組・乙組)ごとの [行, 引けた行, 両方]。札の行は組を持たないので、記録の組別の欄を読み、合計を札の行と合わせる(judge_problems)。"""
        return collections.OrderedDict((k, [v[u"行"], v[u"引けた行"], v[u"両方"]]) for k, v in self.rec[K_S2][K_OVER][u"組別"].items())

    def overlay_labels(self):
        return collections.Counter(r[3] for r in self.overlay_rows)


# ======================================================================================================
# d. 予測の判定(封の予測の字から境を取り、記録の行から決め直す)
def seal_row(seal, pid):
    sec = seal[seal.index(u"## §4 "):] if u"## §4 " in seal else u""
    m = re.search(r"^\| %s \| (.*?) \| (.*?) \|$" % re.escape(pid), sec, re.M)
    return m.group(1) if m else u""


def pct(s):
    return fractions.Fraction(s) / 100


def seal_bounds(seal):
    u"""封の予測の字から数を取る。取れなければ例外(= 検査が赤)。"""
    r = lambda pid: seal_row(seal, pid)
    b = {}
    m = re.search(r"前にだけ在る行は (\d+)・後にだけ在る行は (\d+)", r(u"SE-1"))
    b[u"SE-1"] = (int(m.group(1)), int(m.group(2)))
    b[u"SE-2a"] = int(re.search(r"(\d+) 行以上", r(u"SE-2a")).group(1))
    b[u"SE-2b"] = pct(re.search(r"行の全部の ([\d.]+)% 以下", r(u"SE-2b")).group(1))
    b[u"SE-3"] = pct(re.search(r"の ([\d.]+)% 以下", r(u"SE-3")).group(1))
    b[u"SE-4"] = pct(re.search(r"(\d+)% 以上", r(u"SE-4")).group(1))
    m = re.search(r"(\d+)% 以上 (\d+)% 以下", r(u"SE-5"))
    b[u"SE-5"] = (pct(m.group(1)), pct(m.group(2)))
    b[u"SE-6"] = pct(re.search(r"(\d+)% 以下", r(u"SE-6")).group(1))
    m = re.search(r"(\d+)% 以上 (\d+)% 以下", r(u"SE-7"))
    b[u"SE-7"] = (pct(m.group(1)), pct(m.group(2)))
    return b


def numbers(f):
    u"""判定に使う数(行から数えた数)。"""
    c = collections.OrderedDict()
    c[u"SE-1"] = (f.only_b, f.only_a)
    c[u"SE-2a"] = f.n_state
    c[u"SE-2b"] = (f.n_state, f.n_rows)
    c[u"SE-3"] = (f.n_g_lost, f.n_g_before)
    c[u"SE-4"] = (f.ns_ov(LIT), f.den12(LIT))
    c[u"SE-4 参考"] = (f.ns_ov(FAM), f.den12(FAM))
    c[u"SE-5"] = (f.lab(LIT)[L_BOTH], f.anyv(LIT))
    c[u"SE-5 参考"] = (f.lab(FAM)[L_BOTH], f.anyv(FAM))
    c[u"SE-6"] = (f.lab_o(LIT)[L_BOTH], f.lab(LIT)[L_BOTH])
    c[u"SE-6 参考"] = (f.lab_o(FAM)[L_BOTH], f.lab(FAM)[L_BOTH])
    c[u"SE-7"] = (f.overlay_labels()[L_BOTH], len(f.overlay_rows))
    return c


def judge(c):
    u"""[(id, 当たり?)](8 本)。封の字の境と、記録の行から決める。"""
    b = seal_bounds(c.seal)
    n = numbers(Facts(c))
    q = lambda k: fractions.Fraction(n[k][0], n[k][1])
    out = []
    out.append((u"SE-1", n[u"SE-1"][0] == b[u"SE-1"][0] and n[u"SE-1"][1] == b[u"SE-1"][1]))
    out.append((u"SE-2a", n[u"SE-2a"] >= b[u"SE-2a"]))
    out.append((u"SE-2b", q(u"SE-2b") <= b[u"SE-2b"]))
    out.append((u"SE-3", q(u"SE-3") <= b[u"SE-3"]))
    out.append((u"SE-4", q(u"SE-4") >= b[u"SE-4"]))
    out.append((u"SE-5", b[u"SE-5"][0] <= q(u"SE-5") <= b[u"SE-5"][1]))
    out.append((u"SE-6", q(u"SE-6") <= b[u"SE-6"]))
    out.append((u"SE-7", b[u"SE-7"][0] <= q(u"SE-7") <= b[u"SE-7"][1]))
    return out


def verdicts(c):
    return tuple(HIT if ok else MISS for _i, ok in judge(c))


def direction(c):
    u"""冒頭の字の向き: SE-4 は幅の下・SE-5 は幅の下・SE-5 の参考(円の族)は幅の中・SE-7 は下の端から 2 ポイント以内。"""
    b = seal_bounds(c.seal)
    n = numbers(Facts(c))
    q = lambda k: fractions.Fraction(n[k][0], n[k][1])
    return (q(u"SE-4") < b[u"SE-4"], q(u"SE-5") < b[u"SE-5"][0], b[u"SE-5"][0] <= q(u"SE-5 参考") <= b[u"SE-5"][1],
            b[u"SE-7"][0] <= q(u"SE-7") < b[u"SE-7"][0] + fractions.Fraction(2, 100))


def judge_problems(c):
    out = []
    got = verdicts(c)
    if got != VERDICT_PINNED:
        out.append(u"judge: 決め直した判定が字で留めた判定と違う: %s" % (u" ".join(got),))
    if direction(c) != (True, True, True, True):
        out.append(u"judge: 冒頭の字の向き(SE-4・SE-5 は幅の下・SE-5 の参考は幅の中・SE-7 は下の端の近く)が行からの数え直しと違う")
    pr = c.rec[K_PRED]
    n = numbers(Facts(c))

    def nd(k):
        return collections.OrderedDict([(u"分子", n[k][0]), (u"分母", n[k][1])])
    want = [(u"SE-1 前にだけ在る行・後にだけ在る行", collections.OrderedDict([(u"前にだけ在る行", n[u"SE-1"][0]), (u"後にだけ在る行", n[u"SE-1"][1])])),
            (u"SE-2a state が変わった行(1 行以上か)", n[u"SE-2a"]),
            (u"SE-2b state が変わった行 / 前の行", nd(u"SE-2b")),
            (u"SE-3 前は GROUNDED で後は GROUNDED でない行(両方に在る行) / 前の GROUNDED の行", nd(u"SE-3")),
            (u"SE-4 主語なし + 語彙の外 / 札 1・2 でない行(字のとおり。主)", nd(u"SE-4")),
            (u"SE-4 参考(円の族)", nd(u"SE-4 参考")),
            (u"SE-5 両方 / F のどれかに値が合う行(字のとおり。主)", nd(u"SE-5")),
            (u"SE-5 参考(円の族)", nd(u"SE-5 参考")),
            (u"SE-6 両方(他) / 両方(字のとおり。主)", nd(u"SE-6")),
            (u"SE-6 参考(円の族)", nd(u"SE-6 参考")),
            (u"SE-7 読みの軸の甲組・乙組の行のうち円の族の読みで両方 / 甲組・乙組の行", nd(u"SE-7"))]
    og = Facts(c).overlay_groups()
    f_ = Facts(c)
    if sum(v[0] for v in og.values()) != len(f_.overlay_rows) or sum(v[1] for v in og.values()) != sum(1 for r in f_.overlay_rows if tuple(r[:3]) in f_.group) \
            or sum(v[2] for v in og.values()) != f_.overlay_labels()[L_BOTH] or list(og) != [u"甲組", u"乙組"]:
        out.append(u"judge: 読みの軸の組別の欄の合計が札の行から数えた数と違う")
    for k, v in want:
        if pr.get(k) != v:
            out.append(u"judge: 記録の「予測の判定に要る数」の欄が行から数え直した数と違う: %s" % k[:8])
    return out


# ======================================================================================================
# c. 文書の行(記録から組む)
def expected_lines(c):
    u"""[(名前, 行)]。文書の中の、数字を含む行の全部(文書の順)。"""
    f = Facts(c)
    rec = c.rec
    s1, w = f.s1, f.w
    n = numbers(f)
    b = seal_bounds(c.seal)
    vd = verdicts(c)
    ids_hit = [i for i, v in zip(IDS, vd) if v == HIT]
    ids_miss = [i for i, v in zip(IDS, vd) if v == MISS]
    wire, fg, cut = rec[K_RT], rec[K_FG], rec[K_CUT]
    p2 = lambda x: u"%d%%" % (x * 100)                        # 境(Fraction)→ 整数の %
    p1 = lambda x: u"%.1f%%" % float(x * 100)                  # 境(Fraction)→ 小数 1 桁の %
    lit_n, fam_n = f.lab(LIT), f.lab(FAM)
    lo5, hi5 = b[u"SE-5"]
    lo7, hi7 = b[u"SE-7"]
    L = []

    def add(name, line):
        L.append((name, line))

    add(u"head 封", u"封 `docs/XBRL_SUMMARY_ENGINE_SEAL_2026-11-18.md`(commit %s)。script `measure/xbrl_summary_engine_2026-11-18.py`・記録 `fixtures/xbrl/summary_engine/states_2026-11-18.json`・封の門 `tests/measure/test_xbrl_summary_engine_seal.py` は commit %s(独立監査は 1 回目 REVISE(門が黙る変異)・門を強化して 2 回目 GO)。取得 0・0 USD・通信なし・LLM の席は呼んでいない。" % (SEAL_COMMIT_SHORT, RECORD_COMMIT_SHORT))
    add(u"head 数", u"この文書の数は全部、記録から 1 つずつ読んだもの(結果の門が、記録から組み直した行と字で同じことを見る)。engine は 0 行(engine を変えた commit は無い)。")
    add(u"lead 判定", u"- 判定した %d 本(SE-2a と SE-2b を別々に数える)のうち、%s が外れ、%s が当たり(当たり %d・外れ %d)。" % (len(vd), u" と ".join(ids_miss), u"・".join(ids_hit), len(ids_hit), len(ids_miss)))
    add(u"lead SE-4", u"- SE-4 が外れ: 札 1・2 でない行 %d のうち「主語なし」と「語彙の外」を合わせた行は %d(%s)で、封の字は %s 以上。司令塔は、止めた行に主語が取れない行や語彙の外の行を多く見すぎた。"
        % (n[u"SE-4"][1], n[u"SE-4"][0], rate_text(*n[u"SE-4"]), p2(b[u"SE-4"])))
    add(u"lead SE-5", u"- SE-5 が外れ: F のどれかに値が合う行 %d のうち「両方」は %d(%s)で、封の幅(%s 以上 %s 以下)の下に外れた。司令塔は「両方」を多く見すぎた。参考の円の族の読みでは %sで幅の中だが、判定は封の主の読み(字のとおり)で付けた。"
        % (n[u"SE-5"][1], n[u"SE-5"][0], rate_text(*n[u"SE-5"]), p2(lo5), p2(hi5), fr(*n[u"SE-5 参考"])))
    add(u"lead 読み", u"- 封 §4 の読み方の決めをそのまま当てると、SE-5 が %s 未満なので「先に要るのは語彙と主語の取り方」になる。ただし SE-4 が外れた(主語が取れない行・語彙の外の行は少なかった)ので、この読みは単純には立たない。札の表で多いのは「値だけ」の %d 行(円の族の読みでは %d 行)で、札の定義の上では、主語が取れて語彙にも在るのに、名前が届く fact の中には値が合うものが無く、別の名前の fact に値が合う行である。どの読みが立つかは、値だけの行を 1 行ずつ読むまで書かない。理由を推測で書かない。"
        % (p2(lo5), lit_n[L_VAL], fam_n[L_VAL]))
    add(u"lead 段 1", u"- 段 1: サマリーを足すと state が動いた行が在った(%s・%d 本)。全部が止める側(UNVERIFIABLE)へで、GROUNDED から外れた行は %d。封 §0 の「この行は作りで動かない」は P の行には当たった(%d 行が前後で同じ)が、P でない行には当たらなかった(動いた %d 行は、前は P でない行)。"
        % (fr(f.n_state, f.n_rows), f.n_book, f.n_g_lost, wire[u"P の行のうち後でも同じ鍵・state・reason で在る行"], f.n_state))
    add(u"lead engine", u"- engine は 0 行。「両方」は engine が結べることではない(期・範囲・幅を見ていない)。AI の席の読みは付けていない。封の前に見たのは 1 本だけ。")
    # §1 表
    def row(pid, pred, meas, v):
        add(u"table " + pid, u"| %s | %s | %s | %s |" % (pid, pred, meas, v))
    v = dict(zip(IDS, vd))
    row(u"SE-1", u"段 1 で、前にだけ在る行は %d・後にだけ在る行は %d" % b[u"SE-1"], u"前にだけ在る行 %d・後にだけ在る行 %d(両方に在る行 %d)" % (f.only_b, f.only_a, f.n_both), v[u"SE-1"])
    row(u"SE-2a", u"段 1 で、state が変わった行は %d 行以上在る" % b[u"SE-2a"], u"state が変わった行 %d(fact の個数が前より増えた本 %d/%d)" % (f.n_state, fg[u"fact の個数が前より増えた本"], fg[u"切れた本"]), v[u"SE-2a"])
    row(u"SE-2b", u"段 1 で、state が変わった行は行の全部の %s 以下" % p1(b[u"SE-2b"]), u"state が変わった行 %s" % fr(f.n_state, f.n_rows), v[u"SE-2b"])
    row(u"SE-3", u"段 1 で、前は GROUNDED で後は GROUNDED でない行は、前の GROUNDED の行の %s 以下" % p1(b[u"SE-3"]),
        u"前は GROUNDED で後は GROUNDED でない行 %s(参考: 前は GROUNDED で後に無い行 %d)" % (fr(*n[u"SE-3"]), s1[u"全体"][u"前は GROUNDED で後に無い行(前にだけ在る行)"]), v[u"SE-3"])
    row(u"SE-4", u"段 2 で、札 1・2 でない行のうち「主語なし」と「語彙の外」を合わせた行は %s 以上" % p2(b[u"SE-4"]),
        u"%s(主語なし %d・語彙の外 %d。参考の円の族 %s)" % (fr(*n[u"SE-4"]), lit_n[L_NS], lit_n[L_OV], fr(*n[u"SE-4 参考"])), v[u"SE-4"])
    row(u"SE-5", u"段 2 で、「両方」の行は、F のどれかに値が合う行の %s 以上 %s 以下" % (p2(lo5), p2(hi5)), u"%s(参考の円の族 %s)" % (fr(*n[u"SE-5"]), fr(*n[u"SE-5 参考"])), v[u"SE-5"])
    row(u"SE-6", u"段 2 で、「両方(他)」の行は「両方」の行の %s 以下" % p2(b[u"SE-6"]), u"%s(参考の円の族 %s)" % (fr(*n[u"SE-6"]), fr(*n[u"SE-6 参考"])), v[u"SE-6"])
    og = f.overlay_groups()
    row(u"SE-7", u"読みの軸の %d 行のうち、円の族の読みで「両方」の行は %s 以上 %s 以下" % (n[u"SE-7"][1], p2(lo7), p2(hi7)),
        u"%s(甲組 %d/%d・乙組 %d/%d)" % (fr(*n[u"SE-7"]), og[u"甲組"][2], og[u"甲組"][0], og[u"乙組"][2], og[u"乙組"][0]), v[u"SE-7"])
    add(u"b 数", u"- 当たり %d(%s)・外れ %d(%s)。" % (len(ids_hit), u"・".join(ids_hit), len(ids_miss), u"・".join(ids_miss)))
    add(u"b ゼロ", u"- SE-1 と SE-3 は 0 の予測なので、数え漏れでないことを、独立監査が別実装で全行を数え直して確かめた(監査の席の確かめ。追跡する記録に無い)。")
    add(u"b 2a", u"- SE-2a の欠陥の確認(封 §4): fact の個数が前より増えた本は切れた本 %d のうち %d。後の ZIP に入れたサマリーは、fact の個数の上で全部の本に届いている。" % (fg[u"切れた本"], fg[u"fact の個数が前より増えた本"]))
    add(u"b 2b", u"- SE-2b は %sで、封の上限 %s の中。" % (fr(f.n_state, f.n_rows), p1(b[u"SE-2b"])))
    add(u"b 7", u"- SE-7 は %sで、封の幅(%s 以上 %s 以下)の下の端に近い。" % (fr(*n[u"SE-7"]), p2(lo7), p2(hi7)))
    # §2
    add(u"s2 本", u"- 本 %d・切れた本 %d・切れない本 %d(切れない本は数えるだけ)。" % (cut[u"本"], cut[u"切れた本"], cut[u"切れない本"]))
    add(u"s2 前", u"- 「前」の行が便 RT の記録の段 1 の行と同じ本 %d/%d。「前」の行 %d。" % (wire[u"「前」の行が便 RT の段 1 の行と同じ本"], wire[u"本"], wire[u"「前」の行"]))
    add(u"s2 P", u"- 「前」の P の行 %d・後でも同じ鍵・state・reason で在る P の行 %d。" % (wire[u"P の行(前)"], wire[u"P の行のうち後でも同じ鍵・state・reason で在る行"]))
    add(u"s2 増", u"- 後の P の行は、前の %d より %d 増える(新しく止まった行が P になるため。記録の変わった行の一覧から数えた)。配線の確認が見るのは「前の P の行が後でも同じ」まで。" % (wire[u"P の行(前)"], f.p_new))
    # §3
    add(u"s3 序", u"「前」= サマリーの入らない包んだ ZIP・「後」= そこにサマリーの member を 1 byte も変えずに足した ZIP(封 §2-1)。突き合わせの鍵は(文の番号, 位置)。片方にしか無い行は別に数えた(0 と決めつけていない)。")
    add(u"s3 行", u"- 行は前 %d・後 %d・両方に在る行 %d・前にだけ在る行 %d・後にだけ在る行 %d。" % (w[u"前の行"], w[u"後の行"], f.n_both, f.only_b, f.only_a))
    n_reason = sum(1 for x in f.diff if x[3] == x[4] and x[5] != x[6])
    n_ptr = len(f.diff) - f.n_state - n_reason
    add(u"s3 変", u"- state が変わった行 %s(%d 本)。state は同じで reason だけ変わった行 %d・state も reason も同じで pointer の並びだけ変わった行 %d・全部同じ行 %d。"
        % (fr(f.n_state, f.n_rows), f.n_book, n_reason, n_ptr, f.n_both - len(f.diff)))
    add(u"s3 G", u"- 前は GROUNDED で後は GROUNDED でない行 %d・前は GROUNDED でなく後は GROUNDED の行 %d・前は GROUNDED で後に無い行 %d。"
        % (f.n_g_lost, f.n_g_new, sum(1 for x in s1[u"前にだけ在る行"] if x[3] == G)))
    add(u"s3 UN", u"- 変わった行 %d の後の state は全部 UNVERIFIABLE(前は VALUE_MISMATCH %d・POINTER_NOT_FOUND %d)。後の reason は %d 行とも計画・予想として止める理由(P の行)で、前の reason は %d 行とも P でない。"
        % (f.n_state, f.to_un[(VM, UN)], f.to_un[(PN, UN)], sum(1 for x in f.diff if x[4] == UN and x[6] == REASON_P), sum(1 for x in f.diff if x[5] != REASON_P)))
    for a in STATES:
        add(u"s3 trans " + a, u"| %s | %s |" % (a, u" | ".join(u"%d" % f.t(a, bb) for bb in STATES)))
    for s_ in STATES:
        bc, ac = f.before_count(s_), f.after_count(s_)
        add(u"s3 count " + s_, u"| %s | %d | %d | %s |" % (s_, bc, ac, (u"%+d" % (ac - bc)) if ac != bc else u"0"))
    grp = s1[u"群別"]
    for g in (u"甲", u"乙", u"丙"):
        add(u"s3 grp " + g, u"| %s | %d | %d | %d | %d |" % (g, grp[g][u"前の行"], grp[g][u"state が変わった行"], grp[g][u"state が変わった行を持つ本"], grp[g][u"前の GROUNDED の行"]))
    add(u"s3 grp 全体", u"| 全体 | %d | %d | %d | %d |" % (w[u"前の行"], w[u"state が変わった行"], w[u"state が変わった行を持つ本"], w[u"前の GROUNDED の行"]))
    for s_ in STATES:
        d = s1[u"前の state 別"][s_]
        add(u"s3 by " + s_, u"| %s | %d | %d |" % (s_, d[u"両方に在る行"], d[u"state が変わった行"]))
    add(u"s3 fact", u"- fact の個数(SE-2a の欠陥の確認): 切れた本 %d のうち、後で前より増えた本 %d・減った本 %d。合計は前 %d・後 %d(増えた数 %d)。"
        % (fg[u"切れた本"], fg[u"fact の個数が前より増えた本"], fg[u"fact の個数が前より減った本"], fg[u"fact の個数の合計(前)"], fg[u"fact の個数の合計(後)"], fg[u"fact の個数の合計(後)"] - fg[u"fact の個数の合計(前)"]))
    # §4
    add(u"s4 序", u"この節は監査の席の確かめで、追跡する記録に無い。数は足さない(動いた行を持つ本の全部は、上の記録の %d 本)。" % f.n_book)
    add(u"s4 本", u"- 独立監査の席が、動いた行を持つ本の全部(%d 本)で確かめた型: 「前」の包んだ ZIP には、当期末の期末日の枠が無い。サマリーを足すとその枠が入り、engine の既存の規則(当期末より後の決算期の見出しの後ろの数を計画として止める規則。profile に旗が立っている)が働くようになる。" % f.n_book)
    # §5
    add(u"s5 序", u"P の行 %d のそれぞれについて、その本のサマリーの予想の枠の fact(F)に、engine 自身の語彙で届くかと、値が合うかを別々に見た(engine は動かしていない。封 §2-4)。主の読みは字のとおり・参考は円の族。" % f.n_p_rows)
    lo, fo = f.lab_o(LIT), f.lab_o(FAM)
    for lb in LABELS:
        add(u"s5 札 " + lb, u"| %s | %d | %d |" % (lb, lit_n[lb], fam_n[lb]))
    for lb in LABELS:
        add(u"s5 他 " + lb, u"| %s | %d | %d |" % (lb, lo[lb], fo[lb]))
    add(u"s5 分母", u"- 副の分母: 札 1・2 でない行は字のとおり %d・円の族 %d。F のどれかに値が合う行は字のとおり %d・円の族 %d。" % (f.den12(LIT), f.den12(FAM), f.anyv(LIT), f.anyv(FAM)))
    s34l, s34f = f.sub34(LIT), f.sub34(FAM)
    add(u"s5 34", u"- 札 3・4 の行のうち F のどれかに値が合う行: 字のとおりは主語なし %d・語彙の外 %d(円の族は主語なし %d・語彙の外 %d)。" % (s34l[L_NS], s34l[L_OV], s34f[L_NS], s34f[L_OV]))
    wl, wf = f.ways(LIT), f.ways(FAM)
    add(u"s5 5", u"- 札 5(両方)の行の届き方: 字のとおりは完全一致 %d・部分一致 %d(円の族は完全一致 %d・部分一致 %d)。" % (wl[EXACT], wl[LOOSE], wf[EXACT], wf[LOOSE]))
    add(u"s5 対照", u"- 対照: 「両方(他)」の行は字のとおり %d・円の族 %d。自分の本の「両方」は字のとおり %d・円の族 %d。" % (lo[L_BOTH], fo[L_BOTH], lit_n[L_BOTH], fam_n[L_BOTH]))
    ol = f.overlay_labels()
    add(u"s5 重 両方", u"| 両方 | %d |" % ol[L_BOTH])
    add(u"s5 重 値だけ", u"| 値だけ | %d |" % ol[L_VAL])
    add(u"s5 重 他", u"| 当てない・F が空・主語なし・語彙の外・名前だけ・どちらも無し | %d |" % sum(v_ for k, v_ in ol.items() if k not in (L_BOTH, L_VAL)))
    for nm in (u"甲組", u"乙組"):
        add(u"s5 組 " + nm, u"| %s | %d | %d | %d |" % (nm, og[nm][0], og[nm][1], og[nm][2]))
    s2 = rec[K_S2][K_OVER]
    add(u"s5 重 数", u"- 甲組・乙組の行 %d・鍵が段 2 の P の行に引けた行 %d・引けない行 %d。" % (len(f.overlay_rows), sum(1 for r in f.overlay_rows if tuple(r[:3]) in f.group), sum(1 for r in f.overlay_rows if tuple(r[:3]) not in f.group)))
    # §6
    add(u"s6 範囲", u"- 読めるのは TSS の %d 本・この 2 段に限る。上場会社全体の率ではない。" % cut[u"本"])
    add(u"s6 段 1", u"- 段 1: 動いた行は %sで、全部が止める側(UNVERIFIABLE)へ。GROUNDED から外れた行は %d・GROUNDED になった行も %d。動いた行の仕組みは §4(監査の席の確かめ)。" % (fr(f.n_state, f.n_rows), f.n_g_lost, f.n_g_new))
    add(u"s6 段 2", u"- 段 2(字のとおり): 札 1・2 でない行 %d の内訳は、両方 %d・値だけ %d・名前だけ %d・どちらも無し %d・主語なし %d・語彙の外 %d。主語が取れない行・語彙の外の行は %d のうち %d で、封の見立てより少なかった。"
        % (f.den12(LIT), lit_n[L_BOTH], lit_n[L_VAL], lit_n[L_NAME], lit_n[L_NONE], lit_n[L_NS], lit_n[L_OV], f.den12(LIT), f.ns_ov(LIT)))
    add(u"s6 届", u"- 段 2: F のどれかに値が合う行 %d のうち、名前も届く行は %d。残りの多くは、名前が届かず別の名前の fact に値が合う行(値だけ %d)。" % (f.anyv(LIT), lit_n[L_BOTH], lit_n[L_VAL]))
    add(u"s6 他", u"- 対照の別の本では「両方」は %d で、自分の本の %d と大きく違う。名前と値が合うことは、別の本ではほとんど起きていない。" % (lo[L_BOTH], lit_n[L_BOTH]))
    add(u"s6 組", u"- 読みの軸の %d 行は、甲組 %d/%d と乙組 %d/%d で「両方」の割合が大きく違う。組の差の理由は読んでいない。"
        % (len(f.overlay_rows), og[u"甲組"][2], og[u"甲組"][0], og[u"乙組"][2], og[u"乙組"][0]))
    add(u"s6 読めない", u"- 読めない事: 値だけの行の理由(1 行ずつ読んでいない)。「両方」が engine の結べることかどうか(期・範囲・幅を見ていない)。engine が label で置き換えた後の語彙で届くか。段 1 が、予想の枠を読ませたときの動きかどうか。TSS 以外の書類。")
    # §7
    add(u"s7 1 本", u"- 封じる前に見たのは 1 本だけ。予測の幅はその 1 本と前の便の記録からの見立てで、外れたのは外れとして残す(封 §5)。")
    add(u"s7 材料", u"- 材料は TSS の %d 本(決算短信)。ほかの書類には言えない。AI の席の読みは付けていない(読みの軸の %d 行は前の便の読みの鍵だけを引く)(封 §5)。" % (cut[u"本"], len(f.overlay_rows)))
    add(u"s7 値だけ", u"- 値だけの行の理由は、1 行ずつ読んでいない。冒頭の「どの読みが立つか」は、読むまで書かない。")
    add(u"s7 監査", u"- 独立監査は、script・記録・封の門について、1 回目が門が黙る変異で REVISE、門を強化して 2 回目が GO。")
    add(u"s7 出力", u"- 取り出した出力そのもの(大きい)は repo に置かない。置いたのは 1 つの記録(数・鍵・札だけ)で、文・値・要素名・主語の語・枠の id・会社名・証券コード・docID を持たない。")
    # §8
    add(u"s8 残り", u"- 司令塔に任された残り(範囲を結ぶ条件に入れる案・「見積り・計画」を属性にする案・LLM の席の取り出しの便)は、1 本ずつ封から。")
    add(u"s8 候補", u"- 次の候補(やるとは書かない): 値だけの行を 1 行ずつ読む・TSS の包みに当期末の枠が無いことの効きを測る。")
    add(u"s8 全数", u"- 全数: この便の commit の前に司令塔が全数を 1 回走らせる。結果はこの文書に書かない(引き継ぎに書く)。")
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
    (u"## §4 ", u"## §5 ", u"- **つまり動いたのは、予想の枠を読んだからではない。**"),
    (u"## §4 ", u"## §5 ", u"- 監査は、写しの中でその規則だけを切ると前後が一致し、戻すと同じ行が動くことを見た(記録なし・監査の席の確かめ)。"),
    (u"## §4 ", u"## §5 ", u"- これは、「前」の包み方(TSS の系列の全部が使う)に当期末の枠が無いことも示す。TSS の系列では、この規則が働いていなかった可能性が在る。ただし、それがどれだけ判定に効いたかはこの便では測っていない(次の候補。§8)。"),
    (u"## §7 ", u"## §8 ", u"- 予測の当たり外れの判定は司令塔(盲検でない)。"),
    (u"## §8 ", None, u"- engine を変えるか(予想の枠に当てる段・語彙。人間の決定)。"),
    (u"## §8 ", None, u"- 外に書くか(人間の決定)。"),
    (u"## §8 ", None, u"- `main` へのマージ(人間の決定)。"),
)


def limits_problems(c):
    u"""要点の行が決めた節に 1 回ずつ在る。判定の語は表の行と要約が同じ向き。"""
    out = []
    lead = section(c.doc, LEAD_HEAD, LEAD_NEXT).split(u"\n")
    exp = dict(expected_lines(c))
    for k in (u"lead 判定", u"lead SE-4", u"lead SE-5", u"lead 読み", u"lead 段 1", u"lead engine"):
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
    for need in (u"## §4 ", u"| SE-1 |", u"| SE-7 |", u"1 行以上", u"行の全部の 1.0% 以下", u"前の `GROUNDED` の行の 0.2% 以下", u"30% 以上", u"30% 以上 70% 以下", u"5% 以下", u"40% 以上 80% 以下",
                 u"SE-5 の率が 70% を超えれば", u"30% 未満なら「先に要るのは語彙と主語の取り方」", u"## §5 "):
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


def relabel_rows(src, dst, n, idx):
    u"""段 2 の行の ``idx`` 番目の札のうち ``src`` の最初の ``n`` 行を ``dst`` に変える(判定を動かす。集計の欄は触らない)。"""
    def fn(c):
        k = 0
        for r in c.rec[K_S2][u"行"]:
            if r[idx] == src and k < n:
                r[idx] = dst
                k += 1
        assert k == n, (src, k)
    return fn


def row_line(c, name):
    return dict(expected_lines(c))[name]


def doc_line_edit(name, new):
    u"""組んだ行の 1 つを丸ごと別の字にする(名前は ``expected_lines`` の名前。文書に在る字を探す)。"""
    def fn(c):
        old = row_line(Ctx(), name)
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


def drop_diff(c):
    c.rec[K_S1][K_DIFF].pop()


# a sha
M(u"a1 記録の 1 byte", u"sha", set_text(RECORD_REL, lambda t: t + b" "))
M(u"a2 script の 1 byte", u"sha", set_text(SCRIPT_REL, lambda t: t[:-1] + b"#"))
M(u"a3 封の門の 1 byte", u"sha", set_text(SEAL_GATE_REL, lambda t: t + b"\n"))
# b 記録
M(u"b1 記録の段 1 の数を 1 つ変える(後の行)", u"record", bump([K_S1, u"全体", u"後の行"]))
M(u"b2 記録の段 1 の state が変わった行を 1 つ変える", u"record", bump([K_S1, u"全体", u"state が変わった行"]))
M(u"b3 記録の段 1 の変わった行の一覧から 1 行消す", u"record", drop_diff)
M(u"b4 記録の段 1 の変わった行を持つ本を 1 つ変える", u"record", bump([K_S1, u"全体", u"state が変わった行を持つ本"]))
M(u"b5 記録の段 2 の札の数を 1 つ変える(字のとおりの両方)", u"record", bump([K_S2, u"読み", u"字のとおり", u"札", u"両方"]))
M(u"b6 記録の予測の欄(SE-5 の分子)を 1 つ変える", u"record", bump([K_PRED, u"SE-5 両方 / F のどれかに値が合う行(字のとおり。主)", u"分子"]))
M(u"b7 記録に文・値の字を足す", u"record", lambda c: c.rec.__setitem__(u"漏れ", u"売上高は前期比 12.3 億円の増加となりました。"))
M(u"b8 記録の配線の確認の数を 1 つ変える(P の行)", u"record", bump([K_RT, u"P の行(前)"]))
M(u"b9 記録の fact の個数の合計(後)を 1 つ変える(文書の数と合わなくなる)", u"doc", bump([K_FG, u"fact の個数の合計(後)"]))
M(u"b10 記録の入力の sha256 を 1 つ変える", u"record", set_at([u"入力", 0, u"sha256"], u"0" * 64))
M(u"b11 記録の読みの軸の重ねの数を 1 つ変える", u"record", bump([K_S2, K_OVER, u"組別", u"乙組", u"両方"]))
M(u"b12 記録の段 2 の行の札を 1 つ書き換える(集計と合わなくなる)", u"record", relabel_rows(L_NONE, L_NAME, 1, 4))
# c 文書の数・表・散文
M(u"c1 表の実測の分子を 1 つ変える(SE-4)", u"doc", doc_replace(u"| 50/437(11.4%)", u"| 51/437(11.4%)"))
M(u"c2 表の判定の当たりと外れを入れ替える(SE-4)", u"limits", lambda c: setattr(c, "doc", re.sub(r"(\| SE-4 \|.*?\| )\*\*外れ\*\* \|", r"\1当たり |", c.doc, count=1)))
M(u"c3 表の判定の当たりと外れを入れ替える(SE-1)", u"limits", lambda c: setattr(c, "doc", re.sub(r"(\| SE-1 \|.*?\| )当たり \|", r"\1**外れ** |", c.doc, count=1)))
M(u"c3b 表の判定の当たりと外れを入れ替える(SE-5)", u"doc", lambda c: setattr(c, "doc", re.sub(r"(\| SE-5 \|.*?\| )\*\*外れ\*\* \|", r"\1当たり |", c.doc, count=1)))
M(u"c4 要約の本数を変える(当たり 6・外れ 2)", u"doc", doc_replace(u"(当たり 6・外れ 2)", u"(当たり 7・外れ 1)"))
M(u"c5 散文に記録に無い数を足す(組んだ行にない行)", u"doc", doc_append(u"\n- 追記: 12345 行。\n"))
M(u"c5b 散文に 1 桁の数を足す(組んだ行にない行)", u"doc", doc_append(u"\n- 追記: 0 行。\n"))
M(u"c6 段 1 の移り変わりの表の数を 1 つ変える", u"doc", doc_replace(u"| VALUE_MISMATCH | 0 | 1842 | 16 | 0 |", u"| VALUE_MISMATCH | 0 | 1842 | 17 | 0 |"))
M(u"c7 state の表の差を変える", u"doc", doc_replace(u"| UNVERIFIABLE | 4945 | 4974 | +29 |", u"| UNVERIFIABLE | 4945 | 4974 | +28 |"))
M(u"c8 群別の表の数を変える", u"doc", doc_replace(u"| 乙 | 14279 | 24 | 2 | 4393 |", u"| 乙 | 14279 | 25 | 2 | 4393 |"))
M(u"c9 前の state 別の表の数を変える", u"doc", doc_replace(u"| POINTER_NOT_FOUND | 11008 | 13 |", u"| POINTER_NOT_FOUND | 11008 | 12 |"))
M(u"c10 札の表の数を変える(両方)", u"doc", doc_replace(u"| 両方 | 73 | 174 |", u"| 両方 | 74 | 174 |"))
M(u"c11 札(他)の表の数を変える(名前だけ)", u"doc", doc_replace(u"| 名前だけ | 156 | 260 |", u"| 名前だけ | 156 | 261 |"))
M(u"c12 読みの軸の表の数を変える(乙組)", u"doc", doc_replace(u"| 乙組 | 30 | 30 | 25 |", u"| 乙組 | 30 | 30 | 24 |"))
M(u"c13 読みの軸の札の表の数を変える(値だけ)", u"doc", doc_replace(u"| 値だけ | 53 |", u"| 値だけ | 52 |"))
M(u"c14 組んだ行を消す(段 1 の fact の個数)", u"doc", doc_line_edit(u"s3 fact", u""))
M(u"c15 禁止語を doc の check にも通す(証明した)", u"words", doc_append(u"\n証明" + u"した。\n"))
M(u"c16 散文の数を変える(読める事の段 1)", u"doc", doc_line_edit(u"s6 段 1", u"- 段 1: 動いた行は 30/24531(0.1%)で、全部が止める側(UNVERIFIABLE)へ。"))
M(u"c17 限界の節の途中に記録に無い数を足す", u"doc", doc_replace(u"材料は TSS の 400 本(決算短信)", u"材料は TSS の 4321 本(決算短信)"))
M(u"c18 全数の行に結果を書く", u"doc", doc_replace(u"結果はこの文書に書かない(引き継ぎに書く)。", u"結果は全部緑で 0 件だった(引き継ぎに書く)。"))
M(u"c19 表の「封の字」を変える(SE-5)", u"doc", doc_replace(u"の 30% 以上 70% 以下", u"の 30% 以上 80% 以下"))
M(u"c20 行の順を入れ替える(要約の 2 行)", u"doc", swap_lines(u"lead SE-4", u"lead SE-5"))
M(u"c21 要約の率を変える(SE-5)", u"doc", doc_replace(u"73(23.5%)", u"73(24.5%)"))
M(u"c22 要約の円の族の参考を変える", u"doc", doc_replace(u"174/447(38.9%)で幅の中", u"174/447(48.9%)で幅の中"))
M(u"c23 配線の行の数を変える(P の行)", u"doc", doc_replace(u"在る P の行 794。", u"在る P の行 793。"))
M(u"c24 仕組みの節に数を足す", u"doc", doc_replace(u"動いた行を持つ本の全部(4 本)", u"動いた行を持つ本の全部(5 本)"))
M(u"c25 SE-7 の組別の数を変える", u"doc", doc_replace(u"(甲組 12/60・乙組 25/30)", u"(甲組 13/60・乙組 25/30)"))
M(u"c26 SE-1 の分母の字を変える(両方に在る行)", u"doc", doc_replace(u"(両方に在る行 24531)", u"(両方に在る行 24530)"))
# d 判定
M(u"d1 前にだけ在る行を 1 行にして SE-1 を外れに動かす", u"judge", lambda c: c.rec[K_S1][u"前にだけ在る行"].append([1, 1, 1, G, REASON_P]))
M(u"d2 変わった行を全部 pointer だけにして SE-2a を外れに動かす", u"judge", lambda c: c.rec[K_S1].__setitem__(K_DIFF, [[x[0], x[1], x[2], x[3], x[3], x[5], x[6]] for x in c.rec[K_S1][K_DIFF]]))
M(u"d3 変わった行を 246 行に増やして SE-2b を外れに動かす", u"judge", lambda c: c.rec[K_S1][K_DIFF].extend([list(c.rec[K_S1][K_DIFF][0]) for _ in range(217)]))
M(u"d4 変わった行の 1 つを GROUNDED から外して SE-3 を外れに動かす(分母は 6720 のまま)", u"judge", lambda c: c.rec[K_S1][K_DIFF].extend([[1, 1, 1, G, UN, None, REASON_P]] * 14))
M(u"d5 札を動かして SE-4 を当たりに動かす(行の 100 行を主語なしにする)", u"judge", relabel_rows(L_VAL, L_NS, 100, 4))
M(u"d6 札を動かして SE-5 を当たりに動かす(値だけの行 50 を両方にする)", u"judge", relabel_rows(L_VAL, L_BOTH, 50, 4))
M(u"d7 札を動かして SE-5 を幅の上に動かす(値だけの行 150 を両方にする)", u"judge", relabel_rows(L_VAL, L_BOTH, 150, 4))
M(u"d8 札(他)を動かして SE-6 を外れに動かす(名前だけの行 10 を両方にする)", u"judge", relabel_rows(L_NAME, L_BOTH, 10, 7))
M(u"d9 札の行を動かして SE-7 を外れに動かす(両方の札の行 10 を値だけにする)", u"judge", lambda c: [r.__setitem__(3, L_VAL) for r in [r for r in c.rec[K_S2][K_OVER][u"札の行"] if r[3] == L_BOTH][:10]])
M(u"d10 判定の欄(SE-2b の分子)を 1 つ変える", u"judge", bump([K_PRED, u"SE-2b state が変わった行 / 前の行", u"分子"]))
M(u"d11 判定の欄(SE-1 の後にだけ在る行)を 1 つ変える", u"judge", bump([K_PRED, u"SE-1 前にだけ在る行・後にだけ在る行", u"後にだけ在る行"]))
M(u"d12 判定の欄(SE-7 の分母)を 1 つ変える", u"judge", bump([K_PRED, u"SE-7 読みの軸の甲組・乙組の行のうち円の族の読みで両方 / 甲組・乙組の行", u"分母"]))
M(u"d13 判定の欄(SE-4 の円の族の参考)を 1 つ変える", u"judge", bump([K_PRED, u"SE-4 参考(円の族)", u"分子"]))
M(u"d14 円の族の札を動かして SE-5 の参考を幅の外に動かす(両方 100 を値だけにする)", u"judge", relabel_rows(L_BOTH, L_VAL, 100, 8))
# e 語
M(u"e1 禁止語(ハルシネーション)", u"words", doc_append(u"\nハルシ" + u"ネーション\n"))
M(u"e2 会社名らしい字", u"words", doc_append(u"\n株式会社\n"))
M(u"e3 3 桁以上の漢数字", u"words", doc_append(u"\n二百社\n"))
M(u"e4 docID の形", u"words", doc_append(u"\nS100" + u"AB12\n"))
M(u"e5 要点の字を消す(付けていない)", u"words", doc_replace(u"付けていない", u"付けた", True))
M(u"e6 封の commit を言わない", u"words", doc_replace(u"fabd87ba", u"0000000", True))
M(u"e7 禁止語(人の目)", u"words", doc_append(u"\n人の" + u"目で読んだ。\n"))
M(u"e8 要点の字を消す(外れ)", u"words", doc_replace(u"外れ", u"はずれ", True))
M(u"e9 記録の commit を言わない", u"words", doc_replace(u"563369f1", u"0000000", True))
M(u"e10 要点の字を消す(REVISE)", u"words", doc_replace(u"REVISE", u"ok", True))
M(u"e11 要素名の形の字", u"words", doc_append(u"\njppfs_cor:NetSales\n"))
# 要点の文
M(u"l1 要約の SE-5 の行を変える", u"limits", doc_line_edit(u"lead SE-5", u"- SE-5 は当たり。"))
M(u"l2 §4 の要点の行を変える", u"limits", doc_replace(u"- **つまり動いたのは、予想の枠を読んだからではない。**", u"- **つまり動いたのは、予想の枠を読んだからである。**"))
M(u"l3 §4 の要点の行を消す(監査の席の確かめ)", u"limits", doc_replace(u"(記録なし・監査の席の確かめ)", u""))
M(u"l4 要約の読みの行を変える", u"limits", doc_line_edit(u"lead 読み", u"- 先に要るのは語彙と主語の取り方。"))
M(u"l5 判定は司令塔の行を変える", u"limits", doc_replace(u"- 予測の当たり外れの判定は司令塔(盲検でない)。", u"- 予測の当たり外れの判定は独立監査。"))
M(u"l6 SE-4 の表の行から外れを消す", u"limits", lambda c: setattr(c, "doc", re.sub(r"(\| SE-4 \|.*?\| )\*\*外れ\*\* \|", r"\1判定しない |", c.doc, count=1)))
M(u"l7 次の節の人間の決定の行を消す", u"limits", doc_replace(u"- 外に書くか(人間の決定)。", u"- 外に書く。"))
M(u"l8 要約の段 1 の行を変える", u"limits", doc_line_edit(u"lead 段 1", u"- 段 1: 何も動かなかった。"))
# f 封
M(u"f1 封の SE-5 の字を替える(根の字)", u"seal", seal_replace(u"30% 以上 70% 以下", u"30% 以上 90% 以下"))
M(u"f2 封の読み方の決めの字を替える", u"seal", seal_replace(u"30% 未満なら「先に要るのは語彙と主語の取り方」", u"20% 未満なら「先に要るのは語彙と主語の取り方」"))
M(u"f3 封の文の途中の 1 字", u"frozen", seal_replace(u"0 USD(LLM の席を呼ばない)", u"0 USD(LLM の席を呼ぶ)"))
M(u"f4 封の SE-4 の境を替える(判定が当たりに動く)", u"judge", seal_replace(u"札 1・2 でない行のうち「主語なし」と「語彙の外」を合わせた行は 30% 以上", u"札 1・2 でない行のうち「主語なし」と「語彙の外」を合わせた行は 10% 以上"))
M(u"f5 封の SE-5 の境を替える(判定が当たりに動く)", u"judge", seal_replace(u"30% 以上 70% 以下", u"20% 以上 70% 以下"))
M(u"f6 封の SE-2b の境を替える(判定が外れに動く)", u"judge", seal_replace(u"行の全部の 1.0% 以下", u"行の全部の 0.1% 以下"))
M(u"f7 封の SE-7 の境を替える(判定が外れに動く)", u"judge", seal_replace(u"40% 以上 80% 以下", u"42% 以上 80% 以下"))


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

    def test_b_1_the_record_equals_the_recount_from_its_rows(self):
        self.assertEqual([], record_problems(Ctx()))

    def test_c_1_the_document_lines_equal_the_lines_rebuilt_from_the_record(self):
        self.assertEqual([], doc_problems(Ctx()))

    def test_c_2_the_rebuilt_lines_are_the_ones_read_from_the_record_by_hand(self):
        c = Ctx()
        exp = dict(expected_lines(c))
        self.assertIn(u"| SE-1 | 段 1 で、前にだけ在る行は 0・後にだけ在る行は 0 | 前にだけ在る行 0・後にだけ在る行 0(両方に在る行 24531) | 当たり |", exp[u"table SE-1"])
        self.assertIn(u"state が変わった行 29(fact の個数が前より増えた本 372/372)", exp[u"table SE-2a"])
        self.assertIn(u"29/24531(0.1%)", exp[u"table SE-2b"])
        self.assertIn(u"0/6720(0.0%)", exp[u"table SE-3"])
        self.assertIn(u"50/437(11.4%)(主語なし 43・語彙の外 7。参考の円の族 54/585(9.2%)) | **外れ** |", exp[u"table SE-4"])
        self.assertIn(u"73/310(23.5%)(参考の円の族 174/447(38.9%)) | **外れ** |", exp[u"table SE-5"])
        self.assertIn(u"1/73(1.4%)(参考の円の族 1/174(0.6%))", exp[u"table SE-6"])
        self.assertIn(u"37/90(41.1%)(甲組 12/60・乙組 25/30) | 当たり |", exp[u"table SE-7"])
        self.assertIn(u"| VALUE_MISMATCH | 0 | 1842 | 16 | 0 |", exp[u"s3 trans VALUE_MISMATCH"])
        self.assertIn(u"| POINTER_NOT_FOUND | 0 | 0 | 13 | 10995 |", exp[u"s3 trans POINTER_NOT_FOUND"])
        self.assertIn(u"| UNVERIFIABLE | 4945 | 4974 | +29 |", exp[u"s3 count UNVERIFIABLE"])
        self.assertIn(u"| 乙 | 14279 | 24 | 2 | 4393 |", exp[u"s3 grp 乙"])
        self.assertIn(u"| 両方 | 73 | 174 |", exp[u"s5 札 両方"])
        self.assertIn(u"| 値だけ | 229 | 263 |", exp[u"s5 札 値だけ"])
        self.assertIn(u"| 名前だけ | 156 | 260 |", exp[u"s5 他 名前だけ"])
        self.assertIn(u"完全一致 60・部分一致 13(円の族は完全一致 147・部分一致 27)", exp[u"s5 5"])
        self.assertIn(u"| 乙組 | 30 | 30 | 25 |", exp[u"s5 組 乙組"])
        self.assertIn(u"後の P の行は、前の 794 より 29 増える", exp[u"s2 増"])
        self.assertIn(u"合計は前 165072・後 197237(増えた数 32165)", exp[u"s3 fact"])

    def test_d_1_the_judgement_is_redone_from_the_seal_text_and_the_record_rows(self):
        self.assertEqual([], judge_problems(Ctx()))

    def test_d_2_the_real_judgement_is_six_hits_and_two_misses(self):
        c = Ctx()
        self.assertEqual([i for i, v in zip(IDS, verdicts(c)) if v == MISS], [u"SE-4", u"SE-5"])
        self.assertEqual([i for i, v in zip(IDS, verdicts(c)) if v == HIT], [u"SE-1", u"SE-2a", u"SE-2b", u"SE-3", u"SE-6", u"SE-7"])

    def test_d_3_the_bounds_are_read_from_the_seal_text(self):
        F = fractions.Fraction
        self.assertEqual(seal_bounds(Ctx().seal), {
            u"SE-1": (0, 0), u"SE-2a": 1, u"SE-2b": F(1, 100), u"SE-3": F(2, 1000), u"SE-4": F(30, 100), u"SE-5": (F(30, 100), F(70, 100)),
            u"SE-6": F(5, 100), u"SE-7": (F(40, 100), F(80, 100))})

    def test_d_4_the_numbers_of_the_judgement_are_counted_from_the_rows_by_hand(self):
        n = numbers(Facts(Ctx()))
        self.assertEqual(n[u"SE-4"], (50, 437))
        self.assertEqual(n[u"SE-5"], (73, 310))
        self.assertEqual(n[u"SE-6"], (1, 73))
        self.assertEqual(n[u"SE-7"], (37, 90))
        self.assertEqual(n[u"SE-2b"], (29, 24531))
        self.assertEqual(n[u"SE-3"], (0, 6720))
        self.assertEqual(n[u"SE-5 参考"], (174, 447))

    def test_d_5_the_real_misses_are_below_the_band_and_se7_is_near_the_lower_edge(self):
        self.assertEqual(direction(Ctx()), (True, True, True, True))

    def test_d_6_the_moved_rows_are_all_to_unverifiable_and_were_not_p_rows(self):
        f = Facts(Ctx())
        self.assertEqual(f.n_state, 29)
        self.assertEqual(f.to_un[(VM, UN)] + f.to_un[(PN, UN)], 29)
        self.assertEqual(f.p_new, 29)
        self.assertEqual(f.p_before, 0)
        self.assertEqual(f.n_book, 4)

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
        self.assertGreaterEqual(len(expset), 85)

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
        c.rec[K_S1][u"全体"][u"後の行"] = 1
        c.rec[K_S2][u"行"][0][4] = u"x"
        c.doc = u"x"
        self.assertNotEqual(1, Ctx().rec[K_S1][u"全体"][u"後の行"])
        self.assertNotEqual(u"x", Ctx().rec[K_S2][u"行"][0][4])
        self.assertNotEqual(u"x", Ctx().doc)
        self.assertEqual(before, dict((rel, hashlib.sha256(read_bytes(rel)).hexdigest()) for rel in rels))

    def test_m_4_the_mutation_table_covers_every_check_and_every_effect_named_in_the_brief(self):
        self.assertEqual(set(CHECKS), set(ch for _l, ch, _f in MUTATIONS))
        labels = u"\n".join(l for l, _c, _f in MUTATIONS)
        for need in (u"記録の 1 byte", u"script の 1 byte", u"表の実測の分子", u"当たりと外れを入れ替える", u"散文に記録に無い数", u"散文の数", u"禁止語", u"漢数字", u"要点の",
                     u"封の文の途中の 1 字", u"SE-1 を外れに", u"SE-2a を外れに", u"SE-2b を外れに", u"SE-3 を外れに", u"SE-4 を当たりに", u"SE-5 を当たりに", u"SE-5 を幅の上に",
                     u"SE-6 を外れに", u"SE-7 を外れに", u"数を 1 つ変える", u"行の順を入れ替える", u"判定の欄"):
            self.assertIn(need, labels)
        self.assertGreaterEqual(len(MUTATIONS), 80)

    def test_m_5_a_hit_turned_to_a_miss_is_caught_by_the_judge_and_not_only_by_the_table(self):
        c = Ctx()
        c.rec[K_S1][u"前にだけ在る行"].append([1, 1, 1, G, REASON_P])               # SE-1 が外れに動く。文書の表は当たりのまま
        jd = dict(judge(c))
        self.assertFalse(jd[u"SE-1"])
        self.assertNotEqual([], judge_problems(c))

    def test_m_6_the_judge_follows_the_seal_bounds_not_a_pinned_number(self):
        c = Ctx()
        c.seal = c.seal.replace(u"30% 以上 70% 以下", u"20% 以上 70% 以下", 1)
        self.assertTrue(dict(judge(c))[u"SE-5"])
        c = Ctx()
        c.seal = c.seal.replace(u"30% 以上 70% 以下", u"24% 以上 70% 以下", 1)
        self.assertFalse(dict(judge(c))[u"SE-5"])                                   # 73/310 は 23.5%。24% 以上の幅では外れのまま
        c.seal = c.seal.replace(u"24% 以上 70% 以下", u"23% 以上 70% 以下", 1)
        self.assertTrue(dict(judge(c))[u"SE-5"])

    def test_m_7_the_judge_compares_exact_fractions_not_the_rounded_text(self):
        u"""境のすぐ下・すぐ上の分子で判定が変わる(SE-7 は 37/90 = 41.1%。境の 40% のすぐ上)。"""
        c = Ctx()
        rows = [r for r in c.rec[K_S2][K_OVER][u"札の行"] if r[3] == L_BOTH]
        for r in rows[:1]:
            r[3] = L_VAL                                                            # 36/90 = 40.0% は境ちょうど。当たりのまま
        self.assertTrue(dict(judge(c))[u"SE-7"])
        rows[1][3] = L_VAL                                                          # 35/90 = 38.9% は境の下
        self.assertFalse(dict(judge(c))[u"SE-7"])

    def test_m_8_the_judge_has_eight_items_and_no_system_wide_run(self):
        c = Ctx()
        self.assertEqual(len(judge(c)), 8)
        self.assertEqual([i for i, _ok in judge(c)], list(IDS))


class WiringTest(unittest.TestCase):
    def test_n_1_this_gate_carries_no_docid_and_no_key(self):
        src = read(GATE_REL)
        for bad in (u"ANTHRO" + u"PIC", u"API_" + u"KEY", u"url" + u"lib", u"sock" + u"et"):
            self.assertNotIn(bad, src)
        self.assertIsNone(DOCID_RE.search(src))

    def test_n_2_this_gate_does_not_widen_the_boundary_import_list(self):
        with io.open(os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py"), encoding="utf-8") as fh:
            t = fh.read()
        self.assertNotIn(u"summary_engine", t)

    def test_n_3_this_gate_does_not_use_the_reserved_names(self):
        self.assertEqual([], SG.reserved_problems(rel=GATE_REL))

    def test_n_4_this_gate_leaves_sys_modules_as_it_found_them(self):
        before = dict(sys.modules)
        mod = load_module(GATE_REL, "se_result_gate_sysmodules_check")
        changed = [k for k, v in before.items() if sys.modules.get(k) is not v]
        self.assertEqual([], changed)
        del mod


if __name__ == "__main__":
    unittest.main()
