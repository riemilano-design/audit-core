# -*- coding: utf-8 -*-
u"""結果の門: 封 docs/UNIVERSAL_MATERIAL_SEAL_2026-11-23.md(4ef1368c)の結果の文書 docs/UNIVERSAL_MATERIAL_RESULT_2026-11-23.md(便 UM0)。

封の門 ``test_universal_material_seal.py`` の次の段。**追跡されている記録・script・定義表・指示書・封・封の門・結果の文書と git の履歴だけを読む**
(席の出力・素材・書類の置き場は読まない・通信しない・鍵は読まない・API は呼ばない)。
検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``Ctx`` の写しに当てる(木の file は変異させない。前後の sha256 を見る)。

 a sha256(字で留める)。封・script 2 本・定義表 2 つ・指示書・封の門・記録
 b 記録の数え直し: 会社ごとの数から合計・変異の足し算・資料の変異の関係・4 つの枠・B の計画を、**検査の script の関数を使わずに**数え直す
 c 予測 UM0-A1〜E1 の当たり外れを、封の字の境と記録から決め直す(``judge``)。封の予測の表の行が封にそのまま在ることを字で見る
 d 結果の文書の全部の行を、記録と字から組み直し(``render``)、文書と行ごとに照らす。数・向きの語・表のセル・限界の文・次の便の候補は全部これで縛る。
   **§3(記録に欄の無い読み)の数は、記録に縛れないので字で留めるだけ**(門の中に同じ字が在る。記録に縛るのではない)。席の出力 36 本などの司令塔の数えも同じ
 e 文書の頭の負けと限界・次の便の候補が封 §6 の (i)〜(v) だけ・言えないことを肯定で書かない・禁止語・docID と EDINET コードの形
 f 封・script・定義表・指示書・封の門・記録が commit の blob と 1 byte も違わない・engine は封の commit から 0 行・順序(封 → script など → 記録 → この文書と門)・
   限界の文の出どころ(検査の script の関数で確かめる)
この file は docID の字を持たない。
"""
import collections
import copy
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)

import importlib.util  # noqa: E402

od = collections.OrderedDict
_BEFORE_MODULES = dict(sys.modules)


def load_module(rel, name):
    u"""importlib で読み込む。読み込みの前に居た名前は全部、読み込みの後に元の object へ戻す(自分の名前 ``name`` だけ残す)。"""
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


MY_MODULE_NAME = "um0_seal_gate_for_result_gate"
SG = load_module("tests/measure/test_universal_material_seal.py", MY_MODULE_NAME)               # 封の門の部品。門としては走らせない
CHK, GEN, PR = SG.CHK, SG.GEN, SG.PR
OVERWRITTEN = sorted(k for k, v in _BEFORE_MODULES.items() if sys.modules.get(k) is not v)

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
GEN_REL, CHECK_REL, DEF_RELS, INSTR_REL = SG.GEN_REL, SG.CHECK_REL, SG.DEF_RELS, SG.INSTRUCTION_REL
SEAL_GATE_REL = SG.GATE_REL
RECORD_REL = SG.RECORD_REL
GATE_REL = "tests/measure/test_universal_material_result.py"
DOC_REL = "docs/UNIVERSAL_MATERIAL_RESULT_2026-11-23.md"
SCRIPT_COMMIT_SHORT = "a2326934"                   # script・定義表・指示書・封の門を足した commit
RECORD_COMMIT_SHORT = "be8d5981"                   # 記録を足した commit
IMPL_RELS = (GEN_REL, CHECK_REL) + tuple(DEF_RELS) + (INSTR_REL, SEAL_GATE_REL)
BLOB_AT = od([(SEAL_REL, SEAL_COMMIT_SHORT)] + [(r, SCRIPT_COMMIT_SHORT) for r in IMPL_RELS] + [(RECORD_REL, RECORD_COMMIT_SHORT)])
DOC_COMMITS = (SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT)
SHA_PIN = od([
    (SEAL_REL, "cff6ee52b5fdb7e05018f6ffa7b8c3de2ce20f8ac0034139040815856d942e26"),
    (GEN_REL, "83d5867286957dcaa09cb29132eb7c6350ef1ca49312004c2beb0f6dea00dbce"),
    (CHECK_REL, "e5d7ee37553ffd6b3ff3f43bb5cb474515344735ffdb795bbd93754153035aa0"),
    (DEF_RELS[0], "fd0e878092d106a93c0a65422c664006ac8cb7cf6428224290dab2a80e31e84b"),
    (DEF_RELS[1], "8c8bd2e2a56e159e51ba5371cd1127783b7280db9a9b08da0d627c8d2e54d39f"),
    (INSTR_REL, "eacd3c422880d458af8102b8ab3d1b59393108912b8c8f1cb0bda11452498d9b"),
    (SEAL_GATE_REL, "fe7b61c90bc377669fc9795807029ba8b65ab1faba5acca1946d31592ddafa98"),
    (RECORD_REL, "5ebe8d905221680f42693d8c62aa58991abfc8e1fdd08edb4165d9dd63eec88c")])


def read(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def sha_file(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def guard(fn, *a, **k):
    try:
        return fn(*a, **k)
    except BaseException as exc:                   # noqa: BLE001  変異で落ちた検査は「問題」として数える
        return [u"例外: %s" % type(exc).__name__]


def pct(n, d):
    u"""n/d の % を小数第 1 位まで四捨五入(0.5 は上げる)した字。整数で。"""
    return u"%.1f" % (((2000 * n + d) // (2 * d)) / 10.0)


# ================================================================== 字で決めた形
K_A, K_BC = u"段 A", u"段 B・C"
COMPANIES = tuple(range(1, 13))
MUT_CODES = tuple(u"M%d" % k for k in range(1, 12))
X_CODES = (u"X0", u"XH", u"XU", u"XM", u"XG")
DOC_CODES = (u"D1", u"D2", u"D3", u"D4", u"D5")
ROWS_PER_COMPANY = 30
MUT_KEYS = (u"作れた", u"作れなかった", u"断った", u"止めた", u"通した")
PRED_IDS = (u"UM0-A1", u"UM0-A2", u"UM0-A3", u"UM0-B1", u"UM0-B2", u"UM0-B3", u"UM0-B4", u"UM0-B5", u"UM0-B6", u"UM0-C1", u"UM0-C2", u"UM0-C3", u"UM0-C4", u"UM0-E1")
NUM_KEYS = (
    u"束が K0 で断られた社", u"表に無い言い方の行", u"表に無い言い方の行で席が正解どおり", u"B の計画:置き場に在る", u"B の計画:新しく要る", u"B の計画:計算で作る",
    u"A の資料を通した", u"A の資料の結ばれていない数", u"b01 の席の答えが正解どおり", u"B の資料を通した", u"無いの行", u"無いの行で席が無いと書いた", u"席の出力なし",
    u"通したが数値が違う", u"位置は違うが通り数値は同じ", u"正解どおりなのに止めた(表に無い言い方以外)", u"A の資料なし") + tuple(
    u"資料の変異:%s:%s%s" % (d, w, s) for d in DOC_CODES for s in (u"", u":B") for w in (u"作れた", u"作れなかった", u"通した"))
BOX_KEYS = (u"正解どおり×通した", u"正解どおり×止めた", u"正解と違う×通した", u"正解と違う×止めた")
PLAN_KEYS = (u"置き場に在る", u"新しく要る", u"計算で作る")

# 封 §3 の予測の表の行(封にそのまま在ること。境はこの字の外に無い)
SEAL_ROWS = od([
    (u"UM0-A1", (u"正解の束は、通す 329・止める 24(全部 K3 だけ)・無いを受ける 7・束ごとの断り 0", u"どれか 1 つでも違う")),
    (u"UM0-A2", (u"材料の変異で、作れたもののうち検査が通したものは 0", u"1 以上")),
    (u"UM0-A3", (u"形だけの検査は、M1〜M11 の作れた変異の全部を通す", u"1 つでも断る")),
    (u"UM0-B1", (u"席の答えが正解どおりの行は 360 のうち 342 以上(95%)", u"341 以下")),
    (u"UM0-B2", (u"検査が通した行のうち、正解と数値が違う行は 0", u"1 以上")),
    (u"UM0-B3", (u"正解どおりなのに検査が止めた行は、表に無い言い方の行だけ(ほかは 0)", u"ほかで 1 以上")),
    (u"UM0-B4", (u"無い行 7 のうち、席が `無い` と書くのは 7", u"6 以下")),
    (u"UM0-B5", (u"表に無い言い方の行 24 のうち、席が正解の位置と数値を書くのは 20 以上", u"19 以下")),
    (u"UM0-B6", (u"束が K0 で断られる社は 0", u"1 以上")),
    (u"UM0-C1", (u"A の資料(席)が資料の検査を通るのは 12 本のうち 9 以上", u"8 以下")),
    (u"UM0-C2", (u"B の資料(型)は 12 本とも通る", u"11 以下")),
    (u"UM0-C3", (u"資料の変異で、作れたもののうち通したものは 0", u"1 以上")),
    (u"UM0-C4", (u"b01 の 12 行のうち、席が正解どおりは 11 以上", u"10 以下")),
    (u"UM0-E1", (u"通しで A・B の両方が通った社は 12 のうち 9 以上", u"8 以下"))])
SEAL_EXPECT = (u"通す 329・止める 24・無いを受ける 7・束ごとの断り 0", )

# 文書が肯定で書いてはいけない言い方(出た行は「言えない」か「読まない」を持つ)
AFFIRM_PHRASES = (u"AI が材料を作れる", u"実物の会計の素材で動く", u"実物の素材で動く", u"会社の AI がこの型で書ける", u"誤りが無くなる", u"人の確かめが要らない",
                  u"開示の書類が作れる", u"専用の道具が要らない", u"XBRL を作れる", u"AI に任せられる")
FORBIDDEN_WORDS = (u"精度", u"LLM より正確", u"世界で 1 社", u"金額", u"契約", u"税", u"USD", u"保証")
DOCID_FORM = re.compile(r"(?<![0-9A-Za-z])S[0-9A-Z]{7}(?![0-9A-Za-z])")
ECODE_FORM = re.compile(r"(?<![0-9A-Za-z])E\d{5}(?![0-9A-Za-z])")
DATE_FORM = re.compile(r"(?<![0-9])(?:19|20)\d{2}[-/.]\d{1,2}[-/.]\d{1,2}(?![0-9])|(?<![0-9])(?:19|20)\d{2}年\d{1,2}月")


# ================================================================== 写し
class Ctx(object):
    u"""検査が見る写し。変異はこの写しを変える(木の file は変えない)。"""

    def __init__(self):
        self.rec = json.loads(read(RECORD_REL), object_pairs_hook=od)
        self.doc = read(DOC_REL)
        self.seal = read(SEAL_REL)
        self.defa = read(DEF_RELS[0])
        self.shas = od((rel, sha_file(rel)) for rel in SHA_PIN)
        self.msg_script = git_message(SCRIPT_COMMIT_SHORT)
        self.msg_record = git_message(RECORD_COMMIT_SHORT)
        self.seal_gate_tests = len(re.findall(r"(?m)^    def test_", read(SEAL_GATE_REL)))
        self._cache = None

    def copy(self):
        c = Ctx.__new__(Ctx)
        c.rec = copy.deepcopy(self.rec)
        c.doc, c.seal, c.defa = self.doc, self.seal, self.defa
        c.shas = od(self.shas)
        c.msg_script, c.msg_record, c.seal_gate_tests = self.msg_script, self.msg_record, self.seal_gate_tests
        c._cache = None
        return c

    def expected(self):
        key = (json.dumps(self.rec, ensure_ascii=False, sort_keys=False), self.seal, self.defa, self.msg_script, self.msg_record, self.seal_gate_tests)
        if self._cache is None or self._cache[0] != key:
            self._cache = (key, render(self))
        return self._cache[1]


def git_message(short):
    r = subprocess.run(["git", "-C", REPO, "log", "-1", "--format=%B", short], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.stdout.decode("utf-8")


# ================================================================== 記録の読み(script の関数を使わない)
def comp(rec):
    return rec[K_A][u"会社ごと"]


def mut(rec, code):
    return rec[K_A][u"変異"][code]


def num(rec, key):
    return rec[K_BC][u"数"][key]


def box(rec, key):
    return rec[K_BC][u"4 つの枠"][key]


def rule_sum(row):
    return sum(v for k, v in row.items() if k.startswith(u"規則:"))


def sum_over(rec, codes, key):
    return sum(mut(rec, c)[key] for c in codes)


def doc_pass_total(rec):
    return sum(num(rec, u"資料の変異:%s:通した%s" % (d, s)) for d in DOC_CODES for s in (u"", u":B"))


def doc_made_total(rec):
    return sum(num(rec, u"資料の変異:%s:作れた%s" % (d, s)) for d in DOC_CODES for s in (u"", u":B"))


def stop_rules(rec):
    t = collections.Counter()
    for row in comp(rec).values():
        for k, v in row[u"止めた規則"].items():
            t[k] += v
    return t


def k7(rec):
    return (sum(r[u"K7"][u"見た"] for r in comp(rec).values()), sum(r[u"K7"][u"見なかった"] for r in comp(rec).values()))


def both_bounds(rec):
    a, b = num(rec, u"A の資料を通した"), num(rec, u"B の資料を通した")
    n = len(comp(rec))
    return max(0, a + b - n), min(a, b)


def judge(rec):
    u"""封 §3 の 14 本の当たり外れ({id: True=当たり/False=外れ/None=記録では決まらない})。境は封の字。"""
    t = rec[K_A][u"合計"]
    sr = stop_rules(rec)
    out = od()
    out[u"UM0-A1"] = (t[u"通す"], t[u"止める"], t[u"無いを受ける"], t[u"束ごとの断り"]) == (329, 24, 7, 0) and set(sr) == {u"K3"} and sr[u"K3"] == 24
    out[u"UM0-A2"] = sum_over(rec, MUT_CODES, u"通した") == 0
    out[u"UM0-A3"] = all(mut(rec, c)[u"形だけの検査が通した"] == mut(rec, c)[u"作れた"] for c in MUT_CODES) and sum_over(rec, MUT_CODES, u"作れた") > 0
    right = box(rec, u"正解どおり×通した") + box(rec, u"正解どおり×止めた")
    out[u"UM0-B1"] = right >= 342
    out[u"UM0-B2"] = num(rec, u"通したが数値が違う") == 0
    out[u"UM0-B3"] = num(rec, u"正解どおりなのに止めた(表に無い言い方以外)") == 0
    out[u"UM0-B4"] = num(rec, u"無いの行") == 7 and num(rec, u"無いの行で席が無いと書いた") == 7
    out[u"UM0-B5"] = num(rec, u"表に無い言い方の行で席が正解どおり") >= 20
    out[u"UM0-B6"] = num(rec, u"束が K0 で断られた社") == 0
    out[u"UM0-C1"] = num(rec, u"A の資料を通した") >= 9
    out[u"UM0-C2"] = num(rec, u"B の資料を通した") == 12
    out[u"UM0-C3"] = doc_pass_total(rec) == 0
    out[u"UM0-C4"] = num(rec, u"b01 の席の答えが正解どおり") >= 11
    lo, hi = both_bounds(rec)
    out[u"UM0-E1"] = True if lo >= 9 else (False if hi <= 8 else None)
    return out


def verdict_word(v):
    return {True: u"当たり", False: u"外れ", None: u"記録では決まらない"}[v]


# ================================================================== 文書を記録と字から組み直す
def seal_candidates(seal):
    i = seal.index(u"## §6")
    return [l for l in seal[i:].splitlines() if re.match(r"^- \((?:i|ii|iii|iv|v|vi|vii)\) ", l)]


def plan_text(rec):
    p = [sum(comp_b[u"B の計画"][k] for comp_b in rec[K_BC][u"会社ごと"].values()) for k in PLAN_KEYS]
    return p


def rules_text(row):
    items = [(k[len(u"規則:"):], v) for k, v in row.items() if k.startswith(u"規則:")]
    return u"・".join(u"%s %d" % (k, v) for k, v in items) if items else u"―"


def render(c):
    rec = c.rec
    a = rec[K_A]
    bc = rec[K_BC]
    tot = a[u"合計"]
    n_co = len(a[u"会社ごと"])
    rows_total = sum(bc[u"4 つの枠"].values())
    j = judge(rec)
    hits = [i for i, v in j.items() if v is True]
    misses = [i for i, v in j.items() if v is False]
    sr = stop_rules(rec)
    k7s = k7(rec)
    m_made, m_pass = sum_over(rec, MUT_CODES, u"作れた"), sum_over(rec, MUT_CODES, u"通した")
    m8 = mut(rec, u"M8")
    d_made, d_pass = doc_made_total(rec), doc_pass_total(rec)
    d4_a = num(rec, u"資料の変異:D4:通した")
    n = bc[u"数"]
    boxes = bc[u"4 つの枠"]
    right = boxes[u"正解どおり×通した"] + boxes[u"正解どおり×止めた"]
    lo, hi = both_bounds(rec)
    cands = seal_candidates(c.seal)
    a11 = [r for r in json.loads(c.defa)[u"行"] if r[u"id"] == u"a11"][0][u"名"]
    L = []
    w = L.append
    w(u"# 結果: 便 UM0 ― 開示に限らない共通構造(材料の型 第 0 版)で、資料の指定から資料の生成までの 7 段を 1 本につないだ ― 作り物の素材 %d 社とこの PC の席で数えた ― 2026-11-23" % n_co)
    w(u"")
    w(u"封 `%s`(commit %s)。素材を作る script `%s`・答えを読まない検査の script `%s`・定義表 `%s`・`%s`・席への指示書 `%s`・封の門 `%s` は commit %s(独立監査 REVISE → 直し → REVISE → 直し → GO)。"
      u"記録 `%s` は commit %s(独立監査 GO)。費用は 0。API は呼んでいない。席はこの PC の subagent。engine(`core/`・`adapters/`)は 0 行。"
      % (SEAL_REL, SEAL_COMMIT_SHORT, GEN_REL, CHECK_REL, DEF_RELS[0], DEF_RELS[1], INSTR_REL, SEAL_GATE_REL, SCRIPT_COMMIT_SHORT, RECORD_REL, RECORD_COMMIT_SHORT))
    w(u"")
    w(u"この文書の §1・§2 の数は全部、記録から 1 つずつ読んだもの(結果の門が、記録の数と字で同じことを見る)。§3 は記録に欄の無い読みで、出どころを書く(結果の門は §3 の数を記録に縛らず、字で留めるだけ)。")
    w(u"")
    w(u"**先に負けと限界を書く。**")
    w(u"")
    w(u"- **予測 %d 本は外れ。** 外れは %s。判定した %d 本は 当たり %d・外れ %d。" % (len(misses), u" と ".join(misses), len(j), len(hits), len(misses)))
    w(u"- **UM0-A2 の外れ: 材料の変異で検査が通したものが在る。** 材料の変異 M1〜M11 の作れた %d のうち、検査が通したのは %d(M8「在る → 無い」が %d・M8 以外が %d)。"
      u"止めなかったのは、「在る」を「無い」にした変異を、定義表に無い言い方の行に当てたもの(§3)。通した %d は、記録の「表に無い言い方の行」%d と同じ数。"
      u"封の作りで先に決まる所(表の外の言い方は定義表に書かず、検査の規則 K3 で止まる行の裏返し)で、外れは外れのまま残す。"
      % (m_made, m_pass, m8[u"通した"], m_pass - m8[u"通した"], m8[u"通した"], n[u"表に無い言い方の行"]))
    w(u"- **UM0-C3 の外れ: 資料の変異で検査が通したものが在る。** 資料の変異 D1〜D5 の作れた %d のうち、通したのは %d(A の資料の D4「札を消す」が %d・それ以外が %d・B の資料は %d)。"
      u"通したのは、「無い」「確認待ち」の札を消しても同じ id の札が別の所に在る資料(§3)。数の札を消した変異は全部止まった。検査の欠陥か資料の作りかは、この記録では分けられない。"
      % (d_made, d_pass, d4_a, d_pass - d4_a - sum(n[u"資料の変異:%s:通した:B" % d] for d in DOC_CODES), sum(n[u"資料の変異:%s:通した:B" % d] for d in DOC_CODES)))
    w(u"- **席の誤りを検査が止める力は、本番では 1 回も試されていない。** 「正解と違う×通した」も「正解と違う×止めた」も %d で、席の答えは %d 行とも正解どおりだった。"
      u"検査が止めたのは、正解どおりだった表に無い言い方の行 %d だけで、席の誤りを止めたことは無い(試したのは変異だけ)。"
      % (boxes[u"正解と違う×通した"] + boxes[u"正解と違う×止めた"], right, boxes[u"正解どおり×止めた"]))
    w(u"- **席が全部正解どおりだったのは、素材が易しいからかもしれない。** 素材は、素材を作る script が封の決めた 3 つの形・9 つの罠の中で作った作り物で、実在の会社の素材ではない。"
      u"「AI が材料を作れる」とは言えない。「実物の会計の素材で動く」とも言えない。")
    w(u"- **席はこの PC の Claude Code の subagent で、`CLAUDE.md` と記憶の索引を文脈に持つ。** 会社の AI エージェントそのものではない。API の席・別の model では測っていない。"
      u"1 社 1 役 1 回ずつで、揺れは測っていない。")
    w(u"- **UM0-E1 の「人の手の直しなし」の側は、記録に無い数で決めた。** 記録の数では、A の資料を通したも B の資料を通したも %d 社。"
      u"席の出力は 36 本(材料 A 12・材料 B 12・資料 A 12)・1 社 1 役 1 回・取り直し 0・folder の外への読み書き 0。"
      u"この 3 つの数は、司令塔が席の会話の記録から数えたもので、記録に欄は無く、結果の門は記録に縛らない(字で留めるだけ)。数える道具は、別の folder を渡すと鳴ることを 1 本で確かめただけ。"
      % (n[u"A の資料を通した"]))
    w(u"- 定義表の a11 の名は、封の「総資産」でなく「%s」。封の中で「総資産」が定義表に書かない言い方(表の外)でもあるため、字が違う(commit %s の message)。" % (a11, SCRIPT_COMMIT_SHORT))
    w(u"- 見出しの正規化は、頭の数字の並び(「3月」の 3 など)を落とす。")
    w(u"- 検査の規則 K0 は、材料の id の昇順を見ない(重複と、頼んだ行と同じ id の集まりかだけを見る。「行の並び」の昇順は見る)。")
    w(u"- 検査の規則 K3・K4 は、席の申告でなく素材から読み直した見出しを使う(申告は K2 が別に見る)。")
    w(u"- 計算の行は、入力に「無い」と「保留」が混ざると「無い」になる(封 §1-8 の字の順)。")
    w(u"- 資料の検査は、「無い」「確認待ち」の語の食い違いを数えるだけで赤にしない(在る行に語を書いた時は赤)。")
    w(u"- 本番で負の書き方 `(1,234)` の形は 1 つも出ていない。当期純利益が負なのは 12 社のうち 2 社だけ(§3)。")
    w(u"- 開発の 3 社(101・102・103)には百万円の単位の社が無い(本番には在る)。")
    w(u"- 材料の B の依頼は、指示書が名指す定義表 A の file 名を、定義表 B に読み替えさせて渡した(席の folder の依頼の字)。")
    w(u"- 「うちパート」の行は素材に在るが、定義表も指示書も使っていない。")
    w(u"- 月の字の形(「M月」「YYYY年M月」「YYYY/MM」)を社へ割り当てる決めは封に無く、素材を作る script が決めた。")
    w(u"- 素材と検査は同じ司令塔が罠と規則を決めたので、同じ前提を共有する。ここに無い形の誤りは見えない(封 §5)。表の外で止まる数 %d は作りから決まる数で、実物でどれだけ止まるかを言わない。"
      u"期の読みが「無し」の行(a29・a30)は、素材がどの期のものかを検査が見ていない。範囲は「全社」だけ。人が確かめて見出しの表に足す所は作っていない。"
      u"札を付けずに字で書いた数は、結ばれていない数として赤にするだけで、文の意味は見ない。" % (n[u"表に無い言い方の行"]))
    w(u"")
    w(u"## §1 予測の当たり外れ(封を書いた司令塔が立てた)")
    w(u"")
    w(u"封 §3 の字の境と記録から、結果の門が UM0-A1〜UM0-E1 の当たり外れを決め直した(この表と同じ)。封も予測も結果を見てから書き換えていない。"
      u"素材・検査・表に無い言い方も同じ司令塔が決めた(封 §0)。UM0-A1〜A3 は作りから決まる所が多いと封 §4 に書いた。当たった %d 本を「未見で当てた」とは言わない。" % len(hits))
    w(u"")
    w(u"| # | 予測(封の字の要約) | 実測(記録) | 判定 |")
    w(u"|---|---|---|---|")
    form_pass = sum_over(rec, MUT_CODES, u"形だけの検査が通した")
    k3 = sr[u"K3"]
    rows = od([
        (u"UM0-A1", (u"正解の束は、通す 329・止める 24(全部 K3 だけ)・無いを受ける 7・束ごとの断り 0",
                     u"通す %d・止める %d(止めた規則 K3 %d・K3 以外 %d)・無いを受ける %d・束ごとの断り %d" % (tot[u"通す"], tot[u"止める"], k3, sum(sr.values()) - k3, tot[u"無いを受ける"], tot[u"束ごとの断り"]))),
        (u"UM0-A2", (u"材料の変異(M1〜M11)で、作れたもののうち検査が通したものは 0",
                     u"作れた %d のうち通した %d(M8 %d・M8 以外 %d)" % (m_made, m_pass, m8[u"通した"], m_pass - m8[u"通した"]))),
        (u"UM0-A3", (u"形だけの検査は、M1〜M11 の作れた変異の全部を通す", u"作れた %d のうち形だけの検査が通した %d" % (m_made, form_pass))),
        (u"UM0-B1", (u"席の答えが正解どおりの行は 360 のうち 342 以上", u"%d / %d = %s%%" % (right, rows_total, pct(right, rows_total)))),
        (u"UM0-B2", (u"検査が通した行のうち、正解と数値が違う行は 0",
                     u"通したが数値が違う %d(位置は違うが通り数値は同じ %d は別に数える)" % (n[u"通したが数値が違う"], n[u"位置は違うが通り数値は同じ"]))),
        (u"UM0-B3", (u"正解どおりなのに検査が止めた行は、表に無い言い方の行だけ(ほかは 0)",
                     u"正解どおり×止めた %d・うち表に無い言い方以外 %d" % (boxes[u"正解どおり×止めた"], n[u"正解どおりなのに止めた(表に無い言い方以外)"]))),
        (u"UM0-B4", (u"無い行 7 のうち、席が「無い」と書くのは 7", u"%d / %d" % (n[u"無いの行で席が無いと書いた"], n[u"無いの行"]))),
        (u"UM0-B5", (u"表に無い言い方の行 24 のうち、席が正解の位置と数値を書くのは 20 以上", u"%d / %d" % (n[u"表に無い言い方の行で席が正解どおり"], n[u"表に無い言い方の行"]))),
        (u"UM0-B6", (u"束が K0 で断られる社は 0", u"%d" % n[u"束が K0 で断られた社"])),
        (u"UM0-C1", (u"A の資料(席)が資料の検査を通るのは 12 本のうち 9 以上", u"%d / %d" % (n[u"A の資料を通した"], n_co))),
        (u"UM0-C2", (u"B の資料(型)は 12 本とも通る", u"%d / %d" % (n[u"B の資料を通した"], n_co))),
        (u"UM0-C3", (u"資料の変異(D1〜D5)で、作れたもののうち通したものは 0",
                     u"作れた %d のうち通した %d(A の資料の D4 %d・それ以外 %d)" % (d_made, d_pass, d4_a, d_pass - d4_a))),
        (u"UM0-C4", (u"b01 の 12 行のうち、席が正解どおりは 11 以上", u"%d / %d" % (n[u"b01 の席の答えが正解どおり"], n_co))),
        (u"UM0-E1", (u"通しで A・B の両方が通った社は 12 のうち 9 以上",
                     u"A の資料を通した %d・B の資料を通した %d(両方が通った社は少なくとも %d・多くて %d)。人の手の直しなしの側は先頭の説明" % (n[u"A の資料を通した"], n[u"B の資料を通した"], lo, hi)))])
    for i in PRED_IDS:
        w(u"| %s | %s | %s | %s |" % (i, rows[i][0], rows[i][1], verdict_word(j[i])))
    w(u"")
    w(u"- 当たり %d・外れ %d。外れは %s。" % (len(hits), len(misses), u"・".join(misses)))
    w(u"")
    w(u"## §2 数(記録)")
    w(u"")
    w(u"材料: 本番だけの %d 社(会社の番号 1〜%d)。素材の行は %d × %d = %d。" % (n_co, n_co, n_co, ROWS_PER_COMPANY, n_co * ROWS_PER_COMPANY))
    w(u"")
    w(u"**段 A(席を使わない。正解の束)**: 通す %d・止める %d(止めた規則 K3 %d)・無いを受ける %d・束ごとの断り %d。関係 K7 は %d 本(%d 社 × 3 関係)のうち、見た %d・見なかった %d。"
      % (tot[u"通す"], tot[u"止める"], k3, tot[u"無いを受ける"], tot[u"束ごとの断り"], k7s[0] + k7s[1], n_co, k7s[0], k7s[1]))
    w(u"")
    w(u"材料の変異(M1〜M11)と、検査の規則ごとに 1 つだけ破る追加の変異(X0・XH・XU・XM・XG。封の変異の表に無く、script が足したもの。予測 UM0-A2・UM0-A3 の判定には使わない):")
    w(u"")
    w(u"| 変異 | 作れた | 作れなかった | 断った | 止めた | 通した | 形だけの検査が通した | 規則ごとの止めた材料の数 |")
    w(u"|---|---|---|---|---|---|---|---|")
    for code in MUT_CODES + X_CODES:
        r = a[u"変異"][code]
        w(u"| %s | %d | %d | %d | %d | %d | %s | %s |" % (code, r[u"作れた"], r[u"作れなかった"], r[u"断った"], r[u"止めた"], r[u"通した"],
                                                          (u"%d" % r[u"形だけの検査が通した"]) if code in MUT_CODES else u"―", rules_text(r)))
    w(u"")
    m10 = mut(rec, u"M10")
    w(u"変異 M10 の規則の内訳は、止まった材料の数で、変異の数ではない(1 つの変異で 2 つの材料を入れ替えるため、止めた %d に対し規則の合計は %d)。" % (m10[u"止めた"], rule_sum(m10)))
    w(u"")
    w(u"**段 B・C(席の出力を読む)**:")
    w(u"")
    w(u"| 4 つの枠 | 行 |")
    w(u"|---|---|")
    for k in (u"正解どおり×通した", u"正解どおり×止めた", u"正解と違う×通した", u"正解と違う×止めた"):
        w(u"| %s | %d |" % (k, boxes[k]))
    w(u"")
    w(u"- 無いの行 %d のうち、席が「無い」と書いた %d。表に無い言い方の行 %d のうち、席が正解どおり %d。" % (n[u"無いの行"], n[u"無いの行で席が無いと書いた"], n[u"表に無い言い方の行"], n[u"表に無い言い方の行で席が正解どおり"]))
    w(u"- 通したが数値が違う %d・位置は違うが通り数値は同じ %d・正解どおりなのに止めた(表に無い言い方以外)%d。"
      % (n[u"通したが数値が違う"], n[u"位置は違うが通り数値は同じ"], n[u"正解どおりなのに止めた(表に無い言い方以外)"]))
    w(u"- 束が K0 で断られた社 %d・席の出力なし %d・A の資料なし %d。" % (n[u"束が K0 で断られた社"], n[u"席の出力なし"], n[u"A の資料なし"]))
    pl = plan_text(rec)
    w(u"- B の計画(作りから決まる数。予測にしない): 置き場に在る %d・新しく要る %d・計算で作る %d(%d 社とも 1 社あたり %d・%d・%d)。"
      % (pl[0], pl[1], pl[2], n_co, pl[0] // n_co, pl[1] // n_co, pl[2] // n_co))
    w(u"- A の資料を通した %d・A の資料の結ばれていない数 %d・B の資料を通した %d・b01 の席の答えが正解どおり %d(b01 は %d 行)。"
      % (n[u"A の資料を通した"], n[u"A の資料の結ばれていない数"], n[u"B の資料を通した"], n[u"b01 の席の答えが正解どおり"], n_co))
    w(u"")
    w(u"資料の変異(札の付いた数・札 1 つにつき。作れなかったは、その形が無い札):")
    w(u"")
    w(u"| 変異 | A: 作れた | A: 作れなかった | A: 通した | B: 作れた | B: 作れなかった | B: 通した |")
    w(u"|---|---|---|---|---|---|---|")
    for d in DOC_CODES:
        w(u"| %s | %d | %d | %d | %d | %d | %d |" % (
            d, n[u"資料の変異:%s:作れた" % d], n[u"資料の変異:%s:作れなかった" % d], n[u"資料の変異:%s:通した" % d],
            n[u"資料の変異:%s:作れた:B" % d], n[u"資料の変異:%s:作れなかった:B" % d], n[u"資料の変異:%s:通した:B" % d]))
    w(u"")
    w(u"## §3 記録に欄の無い読み(測った数の一部は記録に無い。出どころを書く。結果の門は記録に縛らず、字で留めるだけ)")
    w(u"")
    w(u"- **M8 の通した %d の中身。** この結果の文書を書く時に、実装担当が素材を作る script と検査の script で A の正解の束に M8 を掛け直し、通した %d を表に無い言い方の行かどうかで分けた: "
      u"表に無い言い方の行は 通した %d・止めた 0、それ以外の行は 通した 0・止めた %d。記録に欄は無い。" % (m8[u"通した"], m8[u"通した"], m8[u"通した"], m8[u"止めた"]))
    d1, d4, d5 = n[u"資料の変異:D1:作れた"], n[u"資料の変異:D4:作れた"], n[u"資料の変異:D5:作れた"]
    w(u"- **D4 の通した %d の中身。** 同じく、席の出力と素材を作る script・検査の script で数え直した: 数の札を消した変異は %d で、通したのは 0。"
      u"「無い」「確認待ち」の札を消した変異は %d で、通したのは %d。%d は D1 の作れた(札の付いた数の数)と同じ数、%d は D4 の作れた %d から %d を引いた数。"
      u"数の札を消すと数の字だけが残り、結ばれていない数として赤になる(資料の検査の規則 C4)。通したのは、置き場が「無い」か「確認待ち」の行で、同じ id の札が資料の別の所にも在る資料。記録に欄は無い。"
      % (d4_a, d1, d4 - d1, d4_a, d1, d4 - d1, d4, d1))
    w(u"- **本番の負の書き方。** 本番の %d 社の素材の全 cell を読み直して数えた: 負の字の cell は 2 つ(`-` が 1 つ・`△` が 1 つ。当期純利益だけ負にした 2 社)。`(1,234)` の形の負の値は 0。記録に欄は無い。" % n_co)
    w(u"- **独立監査が確かめたこと**(commit %s の message): 同じ命令を 2 回走らせて 1 byte も違わない・席の出力 48 file の sha256 は取る前と一致・席の材料 %d 行を別の実装で正解と比べ差は 0。"
      u"**確かめていないこと:** 資料の変異を検査に掛け直す所の独立の再現。全体の suite は未実行。" % (RECORD_COMMIT_SHORT, rows_total))
    w(u"")
    w(u"## §4 門")
    w(u"")
    w(u"- 結果の門 `%s`: 記録の数え直し(会社ごとの数から合計・変異の足し算・資料の変異の関係・4 つの枠・B の計画)・予測の当たり外れの決め直し・この文書の全部の行を記録と字から組み直して照らす・"
      u"封と script と定義表と指示書と封の門と記録が commit の blob と 1 byte も違わないこと・engine が封の commit から 0 行・順序(封 → script など → 記録 → この文書と門)・限界の文の出どころ(検査の script の関数で確かめる)。"
      u"変異で赤くなることを門の中で確かめる。" % GATE_REL)
    w(u"- 封の門 `%s` の試験は %d 本(file の中の `def test_` の数を結果の門が数える)。独立監査は REVISE の後にもう一度 REVISE が出て GO(commit %s の message)。"
      % (SEAL_GATE_REL, c.seal_gate_tests, SCRIPT_COMMIT_SHORT))
    w(u"- 全体の suite(`sh run_tests.sh`)は、この結果の文書の時点で走らせていない。")
    w(u"")
    w(u"## §5 次の便の候補(封 §6 に在るものだけ。結果の文書はここに無い候補を足さない)")
    w(u"")
    for line in cands:
        w(line)
    w(u"")
    return u"\n".join(L)


# ================================================================== 検査(問題の一覧を返す関数)
def sha_problems(c):
    out = []
    for rel, want in SHA_PIN.items():
        if c.shas[rel] != want:
            out.append(u"sha256 が字で留めた値と違う: %s" % rel)
    return out


def keys_problems(rec):
    out = []
    if list(rec) != [K_A, K_BC]:
        return [u"記録の頂の鍵"]
    a, bc = rec[K_A], rec[K_BC]
    if list(a) != [u"会社ごと", u"合計", u"変異"] or list(bc) != [u"会社ごと", u"数", u"4 つの枠"]:
        return [u"記録の 2 段目の鍵"]
    if sorted(a[u"会社ごと"], key=int) != [str(i) for i in COMPANIES] or sorted(bc[u"会社ごと"], key=int) != [str(i) for i in COMPANIES]:
        out.append(u"会社の番号が 1〜12 でない")
    if sorted(a[u"変異"]) != sorted(MUT_CODES + X_CODES):
        out.append(u"変異の名")
    if sorted(bc[u"数"]) != sorted(NUM_KEYS):
        out.append(u"数の鍵")
    if sorted(bc[u"4 つの枠"]) != sorted(BOX_KEYS):
        out.append(u"枠の鍵")
    return out


def recount_problems(c):
    u"""記録の数え直し。書類ごと・変異ごとの足し算の関係(script の関数は使わない)。"""
    rec = c.rec
    out = keys_problems(rec)
    if out:
        return out
    a, bc = rec[K_A], rec[K_BC]
    n_co = len(a[u"会社ごと"])
    tot = collections.Counter()
    for i, row in a[u"会社ごと"].items():
        for k in (u"通す", u"止める", u"無いを受ける", u"束ごとの断り"):
            tot[k] += row[k]
        if row[u"通す"] + row[u"止める"] + row[u"無いを受ける"] != ROWS_PER_COMPANY:
            out.append(u"会社 %s の行が 30 でない" % i)
        if sum(row[u"止めた規則"].values()) != row[u"止める"]:
            out.append(u"会社 %s の止めた規則の和が止めると違う" % i)
        if row[u"K7"][u"見た"] + row[u"K7"][u"見なかった"] != 3:
            out.append(u"会社 %s の K7 が 3 でない" % i)
    if dict(tot) != dict(a[u"合計"]):
        out.append(u"段 A の合計が会社ごとの足しと違う")
    for code, r in a[u"変異"].items():
        if r[u"作れた"] + r[u"作れなかった"] != (348 if code == u"M10" else n_co * ROWS_PER_COMPANY):
            out.append(u"%s の作れた+作れなかったが材料の数と違う" % code)
        if r[u"作れた"] != r[u"断った"] + r[u"止めた"] + r[u"通した"]:
            out.append(u"%s の作れたが 断った+止めた+通した と違う" % code)
        if code in MUT_CODES:
            if r[u"形だけの検査が通した"] > r[u"作れた"]:
                out.append(u"%s の形だけの検査が通したが作れたより多い" % code)
        if code != u"M10" and u"規則:" in u"".join(r):
            if rule_sum(r) != r[u"止めた"]:
                out.append(u"%s の規則の和が止めたと違う" % code)
        if code == u"M10" and rule_sum(r) != 2 * r[u"止めた"]:
            out.append(u"M10 の規則の和が止めたの 2 倍と違う")
    n = bc[u"数"]
    bx = bc[u"4 つの枠"]
    if sum(bx.values()) != n_co * ROWS_PER_COMPANY:
        out.append(u"4 つの枠の和が 360 でない")
    if n[u"無いの行"] != a[u"合計"][u"無いを受ける"]:
        out.append(u"無いの行が段 A の無いを受けると違う")
    if n[u"表に無い言い方の行"] != a[u"合計"][u"止める"]:
        out.append(u"表に無い言い方の行が段 A の止めると違う")
    plan = collections.Counter()
    for i, row in bc[u"会社ごと"].items():
        p = row[u"B の計画"]
        if sum(p.values()) != 20:
            out.append(u"会社 %s の B の計画が 20 でない" % i)
        for k in PLAN_KEYS:
            plan[k] += p[k]
    for k in PLAN_KEYS:
        if plan[k] != n[u"B の計画:" + k]:
            out.append(u"B の計画:%s が会社ごとの足しと違う" % k)
    for s in (u"", u":B"):
        def g(d, w, s=s):
            return n[u"資料の変異:%s:%s%s" % (d, w, s)]
        if g(u"D2", u"作れた") + g(u"D2", u"作れなかった") != g(u"D1", u"作れた"):
            out.append(u"D2 の作れた+作れなかったが D1 の作れたと違う(%s)" % (s or u"A"))
        if g(u"D4", u"作れた") != g(u"D1", u"作れた") + g(u"D5", u"作れた"):
            out.append(u"D4 の作れたが D1+D5 と違う(%s)" % (s or u"A"))
        if g(u"D3", u"作れた") + g(u"D3", u"作れなかった") != g(u"D1", u"作れた") - n_co:
            out.append(u"D3 の作れた+作れなかったが D1−社の数と違う(%s)" % (s or u"A"))
        for d in DOC_CODES:
            if g(d, u"通した") > g(d, u"作れた"):
                out.append(u"%s の通したが作れたより多い(%s)" % (d, s or u"A"))
    if n[u"B の資料を通した"] > n_co or n[u"A の資料を通した"] > n_co or n[u"b01 の席の答えが正解どおり"] > n_co:
        out.append(u"資料・b01 の数が社の数より多い")
    return out


def clean_problems(c):
    out = []
    try:
        out.extend(SG.record_problems(c.rec))
    except BaseException as exc:                    # noqa: BLE001
        out.append(u"記録の検査(封の門の record_problems)が止める: %s" % type(exc).__name__)
    text = json.dumps(c.rec, ensure_ascii=False)
    if DOCID_FORM.search(text) or ECODE_FORM.search(text):
        out.append(u"記録に docID か EDINET コードの形が在る")
    if DATE_FORM.search(text):
        out.append(u"記録に日付の形が在る")
    return out


def bound_problems(c):
    u"""封の字: 予測の表の 14 行・§6 の候補 (i)〜(v)・§1-1 の席の決めが封にそのまま在る。"""
    out = []
    for i, (p, o) in SEAL_ROWS.items():
        row = u"| %s | %s | %s |" % (i, p, o)
        if row not in c.seal:
            out.append(u"封に予測の行が無い: %s" % i)
    cands = seal_candidates(c.seal)
    if len(cands) != 5 or [x.split(u" ")[1] for x in cands] != [u"(i)", u"(ii)", u"(iii)", u"(iv)", u"(v)"]:
        out.append(u"封 §6 の候補が (i)〜(v) の 5 つでない")
    for must in (u"結果の文書はここに無い候補を足さない", u"1 社・1 役につき 1 回。やり直しは無い", u"表に無い言い方(罠 T5)"):
        if must not in c.seal:
            out.append(u"封に字が無い: %s" % must)
    return out


def verdict_problems(c):
    u"""judge が決めた当たり外れが、文書の頭の「予測 N 本は外れ」・§1 の表の判定列・件数と同じ。"""
    out = []
    j = judge(c.rec)
    if None in j.values():
        out.append(u"記録では決まらない予測が在る")
    miss = [i for i, v in j.items() if v is False]
    hit = [i for i, v in j.items() if v is True]
    if u"**予測 %d 本は外れ。** 外れは %s。判定した %d 本は 当たり %d・外れ %d。" % (len(miss), u" と ".join(miss), len(j), len(hit), len(miss)) not in c.doc:
        out.append(u"文書の頭の当たり外れの件数が judge と違う")
    for i in PRED_IDS:
        rows = [l for l in c.doc.splitlines() if l.startswith(u"| %s |" % i)]
        if len(rows) != 1 or not rows[0].rstrip().endswith(u"| %s |" % verdict_word(j[i])):
            out.append(u"%s の判定の欄が judge と違う" % i)
    return out


def sec5_problems(c):
    u"""§5 の次の便の候補が封 §6 の (i)〜(v) とちょうど同じ(足さない・落とさない・入れ替えない)。"""
    i = c.doc.find(u"## §5 ")
    if i < 0:
        return [u"§5 が無い"]
    body = c.doc[i:]
    cands = [l for l in body.splitlines() if l.startswith(u"- ")]
    want = seal_candidates(c.seal)
    out = []
    if cands != want:
        out.append(u"§5 の候補が封 §6 の候補と違う")
    if re.search(r"\((?:vi|vii|viii)\)", body):
        out.append(u"§5 に (vi) 以降の候補が在る")
    if len([l for l in body.splitlines() if l.strip() and not l.startswith(u"#")]) != len(cands):
        out.append(u"§5 に候補でない行が在る")
    return out


def lines_problems(c):
    u"""文書の全部の行が、記録と字から組み直した行と同じ。"""
    want = c.expected().split(u"\n")
    got = c.doc.split(u"\n")
    if got and got[-1] == u"":
        got = got[:-1]
    if want and want[-1] == u"":
        want = want[:-1]
    out = []
    if len(want) != len(got):
        out.append(u"行の数が違う: 組み直し %d・文書 %d" % (len(want), len(got)))
    for k in range(min(len(want), len(got))):
        if want[k] != got[k]:
            out.append(u"%d 行目が違う: %s" % (k + 1, got[k][:60]))
            if len(out) > 5:
                break
    return out


HEAD_FRAGS = (u"**先に負けと限界を書く。**", u"予測 2 本は外れ", u"UM0-A2 の外れ: 材料の変異で検査が通したものが在る", u"UM0-C3 の外れ: 資料の変異で検査が通したものが在る", u"席の誤りを検査が止める力", u"素材が易しいからかもしれない", u"「AI が材料を作れる」とは言えない",
              u"`CLAUDE.md` と記憶の索引", u"API の席・別の model では測っていない", u"記録に欄は無く、結果の門は記録に縛らない", u"「総資産」でなく", u"頭の数字の並び",
              u"材料の id の昇順を見ない", u"席の申告でなく素材から読み直した見出し", u"「無い」と「保留」が混ざると「無い」", u"語の食い違いを数えるだけで赤にしない",
              u"`(1,234)` の形は 1 つも出ていない", u"百万円の単位の社が無い", u"定義表 B に読み替えさせて", u"「うちパート」の行", u"割り当てる決めは封に無く",
              u"同じ前提を共有する", u"期の読みが「無し」の行(a29・a30)", u"人が確かめて見出しの表に足す所は作っていない", u"文の意味は見ない")


def head_problems(c):
    u"""負けと限界は §1 より前(頭)に在る。"""
    i = c.doc.find(u"## §1 ")
    if i < 0:
        return [u"§1 が無い"]
    head = c.doc[:i]
    return [u"頭に無い: %s" % f for f in HEAD_FRAGS if f not in head]


def sec3_problems(c):
    u"""§3 は記録に縛らない読み。見出しと「記録に欄は無い」の字が在り、§3 だけの主張が §3 の外に出ない。"""
    i, j = c.doc.find(u"## §3 "), c.doc.find(u"## §4 ")
    if i < 0 or j < 0 or j < i:
        return [u"§3 が無い"]
    s3 = c.doc[i:j]
    out = []
    for must in (u"記録に縛らず、字で留めるだけ", u"記録に欄は無い", u"実装担当が", u"独立監査が確かめたこと", u"確かめていないこと"):
        if must not in s3:
            out.append(u"§3 に字が無い: %s" % must)
    outside = c.doc[:i] + c.doc[j:]
    for must_not in (u"数の札を消した変異は %d" % 456, u"負の字の cell は 2 つ", u"席の出力 48 file"):
        if must_not in outside:
            out.append(u"§3 だけの主張が §3 の外に在る: %s" % must_not)
    return out


def affirm_problems(c):
    out = []
    for ln in c.doc.splitlines():
        for sent in re.split(u"。", ln):
            for p in AFFIRM_PHRASES:
                if p in sent and u"言えない" not in sent and u"読まない" not in sent:
                    out.append(u"言えないことを肯定で書いた: %s" % p)
    return out


def forbidden_problems(c):
    out = [u"禁止語: %s" % w for w in FORBIDDEN_WORDS if w in c.doc]
    if DOCID_FORM.search(c.doc) or ECODE_FORM.search(c.doc):
        out.append(u"docID か EDINET コードの形が在る")
    return out


def commit_problems(c):
    out = []
    for w in DOC_COMMITS:
        if w not in c.doc:
            out.append(u"文書に commit の字が無い: %s" % w)
    if not set(re.findall(r"(?<![0-9A-Za-z])[0-9a-f]{8}(?![0-9A-Za-z])", c.doc)) <= set(DOC_COMMITS):
        out.append(u"文書が知らない commit の字を書いている")
    for short, words in ((SCRIPT_COMMIT_SHORT, (u"独立監査 REVISE", u"→ 直し → REVISE", u"→ 直し → GO", u"定義表の a11 の名は封の字と違う", u"封の中で同じ字が定義表に書かない言い方でもあるため")),
                         (RECORD_COMMIT_SHORT, (u"独立監査 GO", u"同じ命令 2 回で 1 byte も違わない", u"席の出力 48 file の sha256 は取る前と一致", u"席の材料 360 行を別の実装で正解と比べ差は 0",
                                                 u"資料の変異を検査に掛け直す所は監査では再現していない", u"36 本・1 社 1 役 1 回・取り直し 0・folder の外への読み書き 0(司令塔が席の会話の記録から数えた)",
                                                 u"全体の suite は未実行"))):
        msg = c.msg_script if short == SCRIPT_COMMIT_SHORT else c.msg_record
        for w in words:
            if w not in msg:
                out.append(u"commit %s の message に「%s」が無い" % (short, w))
    return out


CHECKS = od([
    (u"sha", sha_problems), (u"recount", recount_problems), (u"clean", clean_problems), (u"bound", bound_problems), (u"verdict", verdict_problems), (u"sec5", sec5_problems),
    (u"lines", lines_problems), (u"head", head_problems), (u"sec3", sec3_problems), (u"affirm", affirm_problems), (u"forbidden", forbidden_problems), (u"commits", commit_problems)])


def all_problems(c):
    return od((k, guard(fn, c)) for k, fn in CHECKS.items())


def red_set(c, skip=()):
    return set(k for k, fn in CHECKS.items() if k not in skip and guard(fn, c))


# ================================================================== git・順序・engine
def git_in(root, *args):
    r = subprocess.run(["git", "-C", root] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.returncode, r.stdout.decode("utf-8").strip()


def blob_problems(root, prefix, at):
    out = []
    for rel, commit in at.items():
        r = subprocess.run(["git", "-C", root, "show", "%s:%s" % (commit, prefix + rel)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if r.returncode != 0:
            out.append(u"commit %s に %s が無い" % (commit, rel))
            continue
        try:
            with open(os.path.join(root, prefix, rel), "rb") as fh:
                same = fh.read() == r.stdout
        except OSError:
            same = False
        if not same:
            out.append(u"%s が commit %s の blob と違う" % (rel, commit))
    return out


def engine_zero_problems(root, seal_short):
    u"""封の commit から core/・adapters/ を触っていない(commit 済みの差も、木の未 commit の差も 0)。"""
    out = []
    rc, names = git_in(root, "diff", "--name-only", seal_short, "HEAD", "--", PREFIX + "core", PREFIX + "adapters")
    if rc != 0 or names:
        out.append(u"封の commit から engine の file が変わっている: %s" % names.replace(u"\n", u" "))
    rc, st = git_in(root, "status", "--porcelain", "--", PREFIX + "core", PREFIX + "adapters")
    if rc != 0 or st:
        out.append(u"engine の木に未 commit の差が在る")
    return out


def history_problems(root):
    u"""封・script など・記録の file が、文書の書く commit だけで足され、最後の commit もそれ(封の後で変わっていない)。"""
    out = []
    for rel, short in BLOB_AT.items():
        added = PR.added_commits(root, PREFIX + rel)
        if len(added) != 1 or not added[0].startswith(short):
            out.append(u"%s を足した commit が %s でない" % (rel, short))
        rc, last = PR.git_in(root, "log", "-1", "--format=%H", "--", PREFIX + rel)
        if not last.startswith(short):
            out.append(u"%s の最後の commit が %s でない(封・記録の後で変わった)" % (rel, short))
        rc, allc = PR.git_in(root, "log", "--format=%H", "--", PREFIX + rel)
        if len([x for x in allc.split() if x]) != 1:
            out.append(u"%s の履歴が 1 commit でない" % rel)
    return out


def order_problems(root):
    u"""封 ⊏ script など ⊏ 記録 ⊏ この文書と門。文書と門は、まだ commit されていない間は許す(commit された後は順序を見る)。"""
    out = list(PR.order_problems(root, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, list(IMPL_RELS), [RECORD_REL, DOC_REL, GATE_REL]))
    out = [x for x in out if x not in (u"UNCOMMITTED:" + DOC_REL, u"UNCOMMITTED:" + GATE_REL)]
    rec = PR.added_commits(root, PREFIX + RECORD_REL)
    for rel in IMPL_RELS:
        added = PR.added_commits(root, PREFIX + rel)
        if added and rec and not PR.is_anc(root, added[0], rec[0]):
            out.append(u"記録が %s より前" % rel)
    return out


def git_problems(root=REPO):
    return blob_problems(root, PREFIX, BLOB_AT) + engine_zero_problems(root, SEAL_COMMIT_SHORT) + history_problems(root) + order_problems(root)


# ================================================================== 限界の文の出どころ(検査の script の関数で確かめる)
def source_problems(chk=None, gen_text=None, dev=None):
    u"""文書の限界の文が、script・定義表・commit の字と関数の動きに合う。``chk`` を差し替えると赤になる(変異)。"""
    chk = chk or CHK
    gen_text = read(GEN_REL) if gen_text is None else gen_text
    out = []
    if chk.norm(u"3月") != u"月" or chk.norm(u"1. 売上高") != u"売上高":
        out.append(u"見出しの正規化が頭の数字の並びを落とさない")
    item = lambda ident: {u"id": ident, u"状態": u"無い", u"無い理由": u"素材が無い"}    # noqa: E731
    if chk.k0_bundle(None, {u"型の版": u"u0", u"材料": [item(u"a30"), item(u"a29")]}, [u"a29", u"a30"]):
        out.append(u"K0 が id の降順を断る(文書は見ないと書いた)")
    if chk.k0_bundle(None, {u"型の版": u"u0", u"材料": [item(u"a29"), item(u"a29")]}, [u"a29", u"a30"]) == []:
        out.append(u"K0 が id の重複を断らない")
    st = chk.compute_row({u"入力": [u"x", u"y"], u"式": u"和", u"単位": u"円", u"範囲": u"全社"}, {u"x": {u"状態": u"無い"}, u"y": {u"状態": u"保留"}})
    st2 = chk.compute_row({u"入力": [u"x", u"y"], u"式": u"和", u"単位": u"円", u"範囲": u"全社"}, {u"x": {u"状態": u"保留"}, u"y": {u"状態": u"保留"}})
    if st.get(u"状態") != u"無い" or st2.get(u"状態") != u"保留":
        out.append(u"計算の行が 無い+保留 → 無い になっていない")
    if u'"neg_net": i in (5, 10, 102)' not in gen_text or u'"month_form": (i // 2) % 3' not in gen_text or u'[u"うちパート"' not in gen_text:
        out.append(u"素材を作る script の字が文書の限界の文と違う(負の書き方の社・月の字の形・うちパート)")
    if u"うちパート" in read(DEF_RELS[0]) + read(DEF_RELS[1]) + read(INSTR_REL):
        out.append(u"定義表か指示書が「うちパート」を使っている")
    if [(i // 3) % 3 for i in (101, 102, 103)] != [0, 1, 1]:
        out.append(u"開発の 3 社に百万円の単位の社が在る")
    if not [i for i in range(1, 13) if (i // 3) % 3 == 2]:
        out.append(u"本番に百万円の単位の社が無い")
    if not [i for i in (5, 10) if i % 3 != 0]:
        out.append(u"負の書き方の社の番号が (1,234) の形の社に当たる")
    return out


def mini_doc_word_problems(dev):
    u"""開発の 102(人員が無い社)の資料で、「無い」を「確認待ち」に替えても通り、語の食い違いが 1 と数えられる。「在る」行に語を書けば赤。"""
    w = SG.dev_world(102)
    ra, st, plan, rb, sb = SG.run_flow(w)
    text = CHK.render_doc(w.defA, st)
    out = []
    base = CHK.check_document(w.defA, st, text)
    if not base[u"通った"]:
        return [u"開発の 102 の資料が通らない(試しの前提)"]
    word = u"無い[材料:a30]"
    if word not in text:
        return [u"試しの前提が崩れた: 102 の資料に 無い[材料:a30] が無い"]
    swapped = CHK.check_document(w.defA, st, text.replace(word, u"確認待ち[材料:a30]", 1))
    if not swapped[u"通った"] or swapped[u"語の食い違い"] != 1:
        out.append(u"語の食い違いが赤になる・または数えられない")
    ok_row = [m for m in re.finditer(u"[0-9][0-9,]*[^\\[\\n]{0,4}\\[材料:a01\\]", text)]
    if ok_row:
        bad = text.replace(ok_row[0].group(0), u"無い[材料:a01]", 1)
        if CHK.check_document(w.defA, st, bad)[u"通った"]:
            out.append(u"在る行に「無い」と書いても赤にならない")
    return out


# ================================================================== 変異(文書・記録・封の写しに当てる)
def rep(c, old, new, attr="doc", count=1):
    text = getattr(c, attr)
    if old not in text:
        raise AssertionError(u"変異の元の字が無い: %s" % old)
    setattr(c, attr, text.replace(old, new, count))
    return c


def inc(c, path, delta=1):
    node = c.rec
    for k in path[:-1]:
        node = node[k]
    node[path[-1]] += delta
    return c


def consistent_m8_all_stopped(c):
    m = c.rec[K_A][u"変異"][u"M8"]
    m[u"止めた"] += m[u"通した"]
    m[u"規則:K9"] += m[u"通した"]
    m[u"通した"] = 0
    return c


def consistent_d4_zero(c):
    c.rec[K_BC][u"数"][u"資料の変異:D4:通した"] = 0
    return c


def consistent_b2_one(c):
    n = c.rec[K_BC][u"数"]
    n[u"通したが数値が違う"] = 1
    return c


def consistent_a1_rule(c):
    row = c.rec[K_A][u"会社ごと"][u"1"][u"止めた規則"]
    row[u"K2"] = row.pop(u"K3")
    return c


def consistent_candidate(c):
    c.seal = c.seal.rstrip(u"\n") + u"\n- (vi) 新しい候補。\n"
    return c


def consistent_e1_low(c):
    n = c.rec[K_BC][u"数"]
    n[u"A の資料を通した"] = 8
    n[u"B の資料を通した"] = 8
    return c


MUTATIONS = od([
    (u"F1  記録の sha256 の写しを違う値に", (lambda c: c.shas.__setitem__(RECORD_REL, u"0" * 64) or c, (u"sha",))),
    (u"F2  封の sha256 の写しを違う値に", (lambda c: c.shas.__setitem__(SEAL_REL, u"0" * 64) or c, (u"sha",))),
    (u"F3  検査の script の sha256 の写しを違う値に", (lambda c: c.shas.__setitem__(CHECK_REL, u"0" * 64) or c, (u"sha",))),
    (u"F4  封の門の sha256 の写しを違う値に", (lambda c: c.shas.__setitem__(SEAL_GATE_REL, u"0" * 64) or c, (u"sha",))),
    (u"F5  記録の頂の鍵を消す", (lambda c: c.rec.pop(K_BC) and c, (u"recount",))),
    (u"F6  記録の会社を 1 つ消す", (lambda c: c.rec[K_A][u"会社ごと"].pop(u"12") and c, (u"recount",))),
    (u"F7  記録に docID の形を足す", (lambda c: c.rec[K_BC][u"数"].__setitem__(u"x", u"SXXXXXXX") or c, (u"clean",))),
    (u"F8  記録に日付の形を足す", (lambda c: c.rec[K_BC][u"数"].__setitem__(u"x", u"2026-11-23") or c, (u"clean",))),
    (u"F9  記録に禁止の字(見出しの字)を足す", (lambda c: c.rec[K_BC][u"数"].__setitem__(u"x", u"売上高") or c, (u"clean",))),
    (u"F10 封の予測の行を 1 つ消す(境の字)", (lambda c: rep(c, u"| UM0-B1 | 席の答えが正解どおりの行は 360 のうち 342 以上(95%) | 341 以下 |", u"", "seal"), (u"bound",))),
    (u"F11 封の予測の行の境を替える(342 → 300)", (lambda c: rep(c, u"342 以上(95%)", u"300 以上(95%)", "seal"), (u"bound",))),
    (u"F12 封 §6 に (vi) の候補を足す(封の写しだけ)", (consistent_candidate, (u"sec5", u"lines"))),
    (u"F13 封 §6 の (iv) の字を替える(封の写しだけ)", (lambda c: rep(c, u"便 XR0 の続き(経営指標の定義表)はここに入れる", u"ここに入れない", "seal"), (u"lines", u"sec5"))),
    (u"C1  UM0-A2 を当たりにする(M8 の通したを全部止めたに。足し算は合ったまま)", (consistent_m8_all_stopped, (u"verdict", u"lines"))),
    (u"C2  UM0-C3 を当たりにする(D4 の通したを 0 に。作れたの関係は合ったまま)", (consistent_d4_zero, (u"verdict", u"lines"))),
    (u"C3  UM0-B2 を外れにする(通したが数値が違う を 1 に)", (consistent_b2_one, (u"verdict", u"lines"))),
    (u"C4  UM0-A1 を外れにする(止めた規則 K3 を 1 社だけ K2 に。足し算は合ったまま)", (consistent_a1_rule, (u"verdict", u"lines"))),
    (u"C5  UM0-E1 を外れにする(A・B の資料を通したを 8 に)", (consistent_e1_low, (u"verdict", u"lines"))),
    (u"C6  UM0-B1 を外れにする(正解どおり×通したを 100 減らし 正解と違う×止めたを 100 増やす。和は合ったまま)",
     (lambda c: inc(inc(c, (K_BC, u"4 つの枠", u"正解どおり×通した"), -100), (K_BC, u"4 つの枠", u"正解と違う×止めた"), 100), (u"verdict", u"lines"))),
    (u"C7  UM0-C1 を外れにする(A の資料を通したを 8 に)", (lambda c: c.rec[K_BC][u"数"].__setitem__(u"A の資料を通した", 8) or c, (u"verdict", u"lines"))),
    (u"D1  頭の「予測 2 本は外れ」を「予測 1 本は外れ」に", (lambda c: rep(c, u"予測 2 本は外れ", u"予測 1 本は外れ"), (u"verdict", u"lines", u"head"))),
    (u"D2  頭の「当たり 12・外れ 2」を「当たり 13・外れ 1」に", (lambda c: rep(c, u"当たり 12・外れ 2", u"当たり 13・外れ 1", count=2), (u"verdict", u"lines"))),
    (u"D3  §1 の UM0-A2 の「外れ」を「当たり」に", (lambda c: rep(c, u"%s | 外れ |" % u"作れた 2895 のうち通した 24(M8 24・M8 以外 0)", u"%s | 当たり |" % u"作れた 2895 のうち通した 24(M8 24・M8 以外 0)"), (u"verdict", u"lines"))),
    (u"D4  §1 の UM0-C3 の「外れ」を「当たり」に", (lambda c: rep(c, u"A の資料の D4 77・それ以外 0) | 外れ |", u"A の資料の D4 77・それ以外 0) | 当たり |"), (u"verdict", u"lines"))),
    (u"D5  頭の「UM0-A2 の外れ」の見出しを消す", (lambda c: rep(c, u"**UM0-A2 の外れ: 材料の変異で検査が通したものが在る。**", u""), (u"lines", u"head"))),
    (u"D6  「「AI が材料を作れる」とは言えない」を肯定にする", (lambda c: rep(c, u"「AI が材料を作れる」とは言えない。", u"AI が材料を作れる。"), (u"affirm", u"lines", u"head"))),
    (u"D7  §5 に (vi) の候補を足す", (lambda c: setattr(c, "doc", c.doc.rstrip(u"\n") + u"\n- (vi) 新しい候補。\n") or c, (u"sec5", u"lines"))),
    (u"D8  §5 の (iv) の字を替える", (lambda c: rep(c, u"便 XR0 の続き(経営指標の定義表)はここに入れる", u"ここに入れない"), (u"sec5", u"lines"))),
    (u"D9  §5 の (iii) を落とす", (lambda c: setattr(c, "doc", u"\n".join(l for l in c.doc.split(u"\n") if not l.startswith(u"- (iii)"))) or c, (u"sec5", u"lines"))),
    (u"D10 限界の行(a11 の名)を消す", (lambda c: setattr(c, "doc", u"\n".join(l for l in c.doc.split(u"\n") if u"「総資産」でなく" not in l)) or c, (u"head", u"lines"))),
    (u"D11 限界の行(席は subagent)を消す", (lambda c: setattr(c, "doc", u"\n".join(l for l in c.doc.split(u"\n") if u"`CLAUDE.md` と記憶の索引" not in l)) or c, (u"head", u"lines"))),
    (u"D12 司令塔の数えの行から「結果の門は記録に縛らない」を消す", (lambda c: rep(c, u"結果の門は記録に縛らない(字で留めるだけ)。数える道具", u"数える道具"), (u"head", u"lines"))),
    (u"D13 文書の commit の字 a2326934 を 1 字替える", (lambda c: rep(c, u"a2326934", u"a2326935", count=3), (u"commits", u"lines"))),
    (u"D14 文書に知らない commit の字を足す", (lambda c: rep(c, u"費用は 0。", u"費用は 0。(commit deadbeef)", count=1), (u"commits", u"lines"))),
    (u"D15 文書に禁止語を足す", (lambda c: rep(c, u"費用は 0。", u"費用は 0。精度は高い。"), (u"forbidden", u"lines"))),
    (u"D16 文書に docID の形を足す", (lambda c: rep(c, u"費用は 0。", u"費用は 0。S100AAAA。"), (u"forbidden", u"lines"))),
    (u"D17 §3 の「記録に縛らず、字で留めるだけ」を消す", (lambda c: rep(c, u"結果の門は記録に縛らず、字で留めるだけ)\n", u")\n"), (u"sec3", u"lines"))),
    (u"D18 §3 の数え直しの数(数の札の通した 0)を替える", (lambda c: rep(c, u"通したのは 0。", u"通したのは 1。"), (u"lines",))),
    (u"D19 §2 の表の M8 の通したを替える", (lambda c: rep(c, u"| M8 | 353 | 7 | 0 | 329 | 24 |", u"| M8 | 353 | 7 | 0 | 329 | 0 |"), (u"lines",))),
    (u"D20 §3 の「確かめていないこと」を消す", (lambda c: rep(c, u"**確かめていないこと:** 資料の変異を検査に掛け直す所の独立の再現。全体の suite は未実行。", u""), (u"sec3", u"lines"))),
    (u"D21 §4 の封の門の試験の数を替える", (lambda c: rep(c, u"の試験は 95 本", u"の試験は 96 本"), (u"lines",))),
    (u"D22 「全体の suite は…走らせていない」を消す", (lambda c: setattr(c, "doc", u"\n".join(l for l in c.doc.split(u"\n") if u"走らせていない" not in l)) or c, (u"lines",))),
    (u"D23 頭の外れ 2 本の名を入れ替える(UM0-A2 と UM0-C3 → UM0-A2 と UM0-C4)", (lambda c: rep(c, u"外れは UM0-A2 と UM0-C3。", u"外れは UM0-A2 と UM0-C4。"), (u"verdict", u"lines"))),
    (u"D24 B の計画の数を替える", (lambda c: rep(c, u"置き場に在る 192・新しく要る 12・計算で作る 36", u"置き場に在る 192・新しく要る 12・計算で作る 35"), (u"lines",))),
])


def run_mutations(base):
    u"""固定の変異。戻りは (名, 赤になった検査の集合, 期待, ok)。期待の全部が赤・かつ 1 つ以上赤。"""
    res = []
    for name, (fn, expect) in MUTATIONS.items():
        c = base.copy()
        try:
            fn(c)
        except BaseException as exc:               # noqa: BLE001
            res.append((name, set([u"変異が当たらない:" + type(exc).__name__]), expect, False))
            continue
        red = red_set(c)
        res.append((name, red, expect, bool(red) and set(expect) <= red))
    return res


# ================================================================== 掃き
NUM_RE = re.compile(r"[0-9]+(?:,[0-9]{3})*")


def sweep_numbers(doc):
    u"""文書の全部の数(桁区切りを含む)を、(a) 1 増やす (b) 次の別の数に替える。"""
    spans = [(m.start(), m.end(), m.group(0)) for m in NUM_RE.finditer(doc)]
    vals = [s[2] for s in spans]
    for k, (a, b, t) in enumerate(spans):
        v = int(t.replace(u",", u""))
        yield u"数 +1 @%d(%s)" % (a, t), doc[:a] + str(v + 1) + doc[b:]
        other = next((x for x in vals[k + 1:] + vals[:k] if x != t), None)
        if other is not None:
            yield u"数 替え @%d(%s→%s)" % (a, t, other), doc[:a] + other + doc[b:]


WORD_PAIRS = ((u"当たり", u"外れ"), (u"外れ", u"当たり"), (u"通した", u"止めた"), (u"止めた", u"通した"), (u"作れなかった", u"作れた"), (u"全部", u"一部"), (u"以上", u"未満"),
              (u"在る", u"無い"), (u"無い", u"在る"), (u"見た", u"見なかった"), (u"正解どおり", u"正解と違う"), (u"言えない", u"言える"), (u"読まない", u"読む"), (u"だけ", u"も"))


def sweep_words(doc):
    for old, new in WORD_PAIRS:
        for m in re.finditer(re.escape(old), doc):
            yield u"語 %s→%s @%d" % (old, new, m.start()), doc[:m.start()] + new + doc[m.end():]


def sweep_lines(doc):
    ls = doc.split(u"\n")
    for k, l in enumerate(ls):
        if l.strip():
            yield u"行を消す @%d" % (k + 1), u"\n".join(ls[:k] + ls[k + 1:])


def sweep_sentences(doc):
    for m in re.finditer(r"[^。\n|]+。", doc):
        yield u"文を消す @%d" % m.start(), doc[:m.start()] + doc[m.end():]


def sweep_cells(doc):
    ls = doc.split(u"\n")
    tables = []
    cur = []
    for k, l in enumerate(ls):
        if l.startswith(u"|") and not re.match(r"^\|[-| ]+\|$", l):
            cur.append(k)
        else:
            if len(cur) > 2:
                tables.append(cur)
            cur = []
    for rows in tables:
        cells = [[x.strip() for x in ls[k].strip().strip(u"|").split(u"|")] for k in rows]
        for r in range(1, len(rows)):
            for col in range(len(cells[r])):
                for r2 in range(1, len(rows)):
                    if r2 != r and cells[r2][col] != cells[r][col]:
                        new = list(cells[r])
                        new[col] = cells[r2][col]
                        yield u"cell 替え 表の行 %d 列 %d ← 行 %d" % (rows[r] + 1, col, rows[r2] + 1), u"\n".join(ls[:rows[r]] + [u"| " + u" | ".join(new) + u" |"] + ls[rows[r] + 1:])
                        break


def sweep_candidates(doc):
    yield u"候補を足す", doc.rstrip(u"\n") + u"\n- (vi) 新しい候補。\n"
    ls = doc.split(u"\n")
    for k, l in enumerate(ls):
        if re.match(r"^- \((?:i|ii|iii|iv|v)\) ", l):
            yield u"候補を落とす @%d" % (k + 1), u"\n".join(ls[:k] + ls[k + 1:])
    idx = [k for k, l in enumerate(ls) if re.match(r"^- \((?:i|ii|iii|iv|v)\) ", l)]
    if len(idx) >= 2:
        sw = list(ls)
        sw[idx[0]], sw[idx[1]] = sw[idx[1]], sw[idx[0]]
        yield u"候補を入れ替える", u"\n".join(sw)


def all_doc_cases(doc):
    for gen in (sweep_numbers, sweep_words, sweep_lines, sweep_sentences, sweep_cells, sweep_candidates):
        for name, new in gen(doc):
            if new != doc:
                yield name, new


def run_doc_sweep(base):
    u"""全部の掃きの変異は、``lines`` 1 つだけでも赤。黙った名を返す(``lines`` は文書と組み直しの全文照合)。"""
    silent = []
    n = 0
    for name, new in all_doc_cases(base.doc):
        c = base.copy()
        c._cache = base._cache
        c.doc = new
        n += 1
        if not guard(lines_problems, c):
            silent.append(name)
    return n, silent


def leaf_paths(o, path=()):
    if isinstance(o, dict):
        for k, v in o.items():
            for p in leaf_paths(v, path + (k,)):
                yield p
    elif isinstance(o, list):
        for k, v in enumerate(o):
            for p in leaf_paths(v, path + (k,)):
                yield p
    elif isinstance(o, (int, bool)):
        yield path


def run_record_sweep(base):
    u"""記録の全部の整数の葉を 1 つずつ +1。``sha`` を除いた検査のどれかが赤になる(sha に頼らない)。黙った葉を返す。"""
    silent = []
    n = 0
    for path in leaf_paths(base.rec):
        c = base.copy()
        node = c.rec
        for k in path[:-1]:
            node = node[k]
        node[path[-1]] = node[path[-1]] + 1
        n += 1
        if not red_set(c, skip=(u"sha",)):
            silent.append(path)
    return n, silent


# ================================================================== 試験
_CTX = {}


def base_ctx():
    if "c" not in _CTX:
        _CTX["c"] = Ctx()
        _CTX["tree_before"] = dict((rel, sha_file(rel)) for rel in list(SHA_PIN) + [DOC_REL])
        _CTX["c"].expected()
    return _CTX["c"]


def tearDownModule():
    SG.tearDownModule()


class RealTest(unittest.TestCase):
    u"""実物(いまの木)で全部の検査が空。"""

    @classmethod
    def setUpClass(cls):
        cls.c = base_ctx()

    def test_a_1_sha256_of_the_frozen_files(self):
        self.assertEqual([], sha_problems(self.c))

    def test_a_2_the_module_names_this_gate_loaded_are_not_overwritten(self):
        self.assertEqual([], OVERWRITTEN)
        self.assertIn(MY_MODULE_NAME, sys.modules)

    def test_b_1_the_record_recounts(self):
        self.assertEqual([], recount_problems(self.c))

    def test_b_2_the_record_is_clean(self):
        self.assertEqual([], clean_problems(self.c))

    def test_c_1_the_seal_has_the_prediction_rows_and_the_candidates(self):
        self.assertEqual([], bound_problems(self.c))

    def test_c_2_the_verdicts_are_decided_again_and_equal_the_document(self):
        self.assertEqual([], verdict_problems(self.c))
        j = judge(self.c.rec)
        self.assertEqual(list(PRED_IDS), list(j))
        self.assertEqual([u"UM0-A2", u"UM0-C3"], [i for i, v in j.items() if v is False])
        self.assertEqual(12, len([1 for v in j.values() if v is True]))

    def test_c_3_the_section5_candidates_are_the_seals(self):
        self.assertEqual([], sec5_problems(self.c))

    def test_d_1_every_line_equals_the_one_built_from_the_record(self):
        self.assertEqual([], lines_problems(self.c))

    def test_d_2_the_losses_and_limits_are_at_the_head(self):
        self.assertEqual([], head_problems(self.c))

    def test_d_3_section3_is_pinned_only_by_form(self):
        self.assertEqual([], sec3_problems(self.c))

    def test_e_1_no_affirmation_no_forbidden_word_and_the_commits_named(self):
        self.assertEqual([], affirm_problems(self.c))
        self.assertEqual([], forbidden_problems(self.c))
        self.assertEqual([], commit_problems(self.c))

    def test_e_2_the_seal_gate_test_count_in_the_document(self):
        self.assertIn(u"の試験は %d 本" % self.c.seal_gate_tests, self.c.doc)
        self.assertEqual(95, self.c.seal_gate_tests)

    def test_f_1_blobs_engine_history_and_order(self):
        self.assertEqual([], git_problems())

    def test_f_2_the_blob_check_is_red_for_a_changed_file_and_a_missing_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            SG.make_repo([("x", {PREFIX + "a.txt": u"1"})], tmp)
            short = subprocess.run(["git", "-C", tmp, "log", "--format=%h", "-1"], stdout=subprocess.PIPE).stdout.decode().strip()
            os.makedirs(os.path.join(tmp, PREFIX), exist_ok=True)
            self.assertEqual([], blob_problems(tmp, PREFIX, od([("a.txt", short)])))
            with open(os.path.join(tmp, PREFIX, "a.txt"), "w") as fh:
                fh.write(u"2")
            self.assertNotEqual([], blob_problems(tmp, PREFIX, od([("a.txt", short)])))
            self.assertNotEqual([], blob_problems(tmp, PREFIX, od([("a.txt", "0000000")])))
            os.remove(os.path.join(tmp, PREFIX, "a.txt"))
            self.assertNotEqual([], blob_problems(tmp, PREFIX, od([("a.txt", short)])))

    def test_f_3_the_engine_check_is_red_when_the_engine_changed_after_the_seal(self):
        with tempfile.TemporaryDirectory() as tmp:
            SG.make_repo([("seal", {PREFIX + "docs/s.md": u"s"}), ("eng", {PREFIX + "core/e.py": u"x"})], tmp)
            seal = subprocess.run(["git", "-C", tmp, "log", "--format=%h", "--", PREFIX + "docs/s.md"], stdout=subprocess.PIPE).stdout.decode().strip()
            self.assertNotEqual([], engine_zero_problems(tmp, seal))
        with tempfile.TemporaryDirectory() as tmp:
            SG.make_repo([("eng", {PREFIX + "core/e.py": u"x"}), ("seal", {PREFIX + "docs/s.md": u"s"}), ("later", {PREFIX + "docs/t.md": u"t"})], tmp)
            seal = subprocess.run(["git", "-C", tmp, "log", "--format=%h", "--", PREFIX + "docs/s.md"], stdout=subprocess.PIPE).stdout.decode().strip()
            self.assertEqual([], engine_zero_problems(tmp, seal))
            with open(os.path.join(tmp, PREFIX, "core", "e.py"), "w") as fh:
                fh.write(u"y")
            self.assertNotEqual([], engine_zero_problems(tmp, seal))

    def test_f_4_the_order_check_is_red_when_the_record_comes_before_a_script(self):
        seal = PREFIX + SEAL_REL
        with tempfile.TemporaryDirectory() as tmp:
            SG.make_repo([("seal", {seal: u"s"}), ("rec", {PREFIX + RECORD_REL: u"{}"}), ("impl", {PREFIX + GEN_REL: u"x"})], tmp)
            short = subprocess.run(["git", "-C", tmp, "log", "--format=%h", "--", seal], stdout=subprocess.PIPE).stdout.decode().strip()
            got = PR.order_problems(tmp, PREFIX, SEAL_REL, short, [GEN_REL], [RECORD_REL])
            self.assertNotEqual([], list(got))

    def test_g_1_the_source_of_the_limit_sentences(self):
        self.assertEqual([], source_problems())
        self.assertEqual([], mini_doc_word_problems(None))

    def test_g_2_the_source_check_is_red_for_a_changed_function_or_text(self):
        class Fake(object):
            norm = staticmethod(lambda s: s)
            k0_bundle = staticmethod(lambda ctx, b, wanted: [u"x"])
            compute_row = staticmethod(lambda row, store: {u"状態": u"保留"})
        self.assertGreaterEqual(len(source_problems(chk=Fake)), 3)
        text = read(GEN_REL)
        for old in (u'"neg_net": i in (5, 10, 102)', u'"month_form": (i // 2) % 3', u'[u"うちパート"'):
            self.assertNotEqual([], source_problems(gen_text=text.replace(old, u"")))


class MutationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = base_ctx()

    def test_h_1_every_fixed_mutation_turns_its_checks_red_and_the_files_are_unchanged(self):
        before = dict((rel, sha_file(rel)) for rel in list(SHA_PIN) + [DOC_REL])
        bad = [(name, sorted(red), expect) for name, red, expect, ok in run_mutations(self.base) if not ok]
        self.assertEqual([], bad)
        self.assertEqual(before, dict((rel, sha_file(rel)) for rel in list(SHA_PIN) + [DOC_REL]))
        self.assertEqual(_CTX["tree_before"], before)

    def test_h_2_the_unmutated_copy_is_green_on_every_check(self):
        c = self.base.copy()
        self.assertEqual(set(), red_set(c))
        for k, v in all_problems(c).items():
            self.assertEqual([], v, k)

    def test_h_3_the_recount_stays_green_when_the_data_changes_consistently_but_the_document_check_does_not(self):
        for fn in (consistent_m8_all_stopped, consistent_d4_zero, consistent_b2_one, consistent_a1_rule):
            c = self.base.copy()
            fn(c)
            self.assertEqual([], recount_problems(c), fn.__name__)
            self.assertIn(u"lines", red_set(c), fn.__name__)

    def test_h_4_every_check_a_mutation_names_exists(self):
        names = set(k for _n, (_f, ex) in MUTATIONS.items() for k in ex)
        self.assertTrue(names <= set(CHECKS), names - set(CHECKS))

    def test_h_5_the_judgement_edges_at_the_seal_bounds(self):
        c = self.base.copy()
        n = c.rec[K_BC][u"数"]
        box = c.rec[K_BC][u"4 つの枠"]
        j = judge(c.rec)
        self.assertTrue(j[u"UM0-B1"] and j[u"UM0-B5"] and j[u"UM0-C1"] and j[u"UM0-C4"])
        for key, field, ok_val, ng_val in ((u"UM0-C1", u"A の資料を通した", 9, 8), (u"UM0-C4", u"b01 の席の答えが正解どおり", 11, 10), (u"UM0-B5", u"表に無い言い方の行で席が正解どおり", 20, 19),
                                           (u"UM0-C2", u"B の資料を通した", 12, 11), (u"UM0-B6", u"束が K0 で断られた社", 0, 1)):
            for val, want in ((ok_val, True), (ng_val, False)):
                d = self.base.copy()
                d.rec[K_BC][u"数"][field] = val
                self.assertEqual(want, judge(d.rec)[key], (key, val))
        d = self.base.copy()
        d.rec[K_BC][u"4 つの枠"][u"正解どおり×通した"] = 342 - box[u"正解どおり×止めた"]
        self.assertTrue(judge(d.rec)[u"UM0-B1"])
        d.rec[K_BC][u"4 つの枠"][u"正解どおり×通した"] = 341 - box[u"正解どおり×止めた"]
        self.assertFalse(judge(d.rec)[u"UM0-B1"])
        d = self.base.copy()
        d.rec[K_BC][u"数"][u"A の資料を通した"] = 12
        d.rec[K_BC][u"数"][u"B の資料を通した"] = 9
        self.assertTrue(judge(d.rec)[u"UM0-E1"])
        d.rec[K_BC][u"数"][u"B の資料を通した"] = 8
        self.assertFalse(judge(d.rec)[u"UM0-E1"])
        d.rec[K_BC][u"数"][u"A の資料を通した"] = 10
        d.rec[K_BC][u"数"][u"B の資料を通した"] = 10
        self.assertIsNone(judge(d.rec)[u"UM0-E1"])
        self.assertTrue(n[u"A の資料を通した"] >= 9)

    def test_h_6_a_changed_m_row_makes_a2_and_a3_follow(self):
        c = self.base.copy()
        c.rec[K_A][u"変異"][u"M3"][u"通した"] = 1
        self.assertFalse(judge(c.rec)[u"UM0-A2"])
        c = self.base.copy()
        consistent_m8_all_stopped(c)
        self.assertTrue(judge(c.rec)[u"UM0-A2"])
        c.rec[K_A][u"変異"][u"X0"][u"通した"] = 1
        self.assertTrue(judge(c.rec)[u"UM0-A2"])               # 追加の変異(X)は A2 の判定に使わない
        c = self.base.copy()
        c.rec[K_A][u"変異"][u"M5"][u"形だけの検査が通した"] -= 1
        self.assertFalse(judge(c.rec)[u"UM0-A3"])
        c = self.base.copy()
        c.rec[K_BC][u"数"][u"資料の変異:D2:通した:B"] = 1
        self.assertFalse(judge(c.rec)[u"UM0-C3"])

    def test_h_7_the_sweep_over_every_number_word_line_sentence_cell_and_candidate_stays_red(self):
        n, silent = run_doc_sweep(self.base)
        self.assertGreater(n, 1500)
        self.assertEqual([], silent[:20], u"黙った変異 %d 個(総数 %d)" % (len(silent), n))

    def test_h_8_the_record_leaf_sweep_stays_red_without_the_sha_pin(self):
        n, silent = run_record_sweep(self.base)
        self.assertGreater(n, 250)
        self.assertEqual([], silent[:20], u"黙った葉 %d 個(総数 %d)" % (len(silent), n))

    def test_h_9_each_mutation_is_caught_by_more_than_the_sha_pin_unless_it_is_a_sha_mutation(self):
        for name, (fn, expect) in MUTATIONS.items():
            if expect == (u"sha",):
                continue
            c = self.base.copy()
            fn(c)
            self.assertTrue(red_set(c, skip=(u"sha",)), name)


if __name__ == "__main__":
    unittest.main()
