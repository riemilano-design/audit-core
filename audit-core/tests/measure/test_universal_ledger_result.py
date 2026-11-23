# -*- coding: utf-8 -*-
u"""結果の門: 封 docs/UNIVERSAL_MATERIAL_THIRD_PARTY_SOURCE_SEAL_2026-11-23.md(0d2156e4)の結果の文書
docs/UNIVERSAL_MATERIAL_THIRD_PARTY_SOURCE_RESULT_2026-11-24.md(便 UM1)。

封の門 ``test_universal_ledger_seal.py`` の次の段。**追跡されている記録・script・定義表・読込みの定義・指示書・封・下見の封・封の門・結果の文書と git の履歴だけを読む**
(素材・席の出力・席の folder は読まない・通信しない・鍵は読まない・API は呼ばない)。
検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``Ctx`` の写しに当てる(木の file は変異させない。前後の sha256 を見る)。

 a sha256(字で留める)。封・下見の封・script 2 本・定義表・読込みの定義・指示書・封の門・記録
 b 記録の数え直し: 正解の束・検査の結果・変異・段 B の足し算(全部 = 指定ごとの和 など)を、検査と答えを知っている側の script の関数を使わずに数え直す
 c 予測 UM1-A0〜B8 の当たり外れを、封の字の境と記録から決め直す(``judge``)。封の予測の表の行が封にそのまま在ることを字で見る
 d 結果の文書の全部の行を、記録と字から組み直し(``render``)、文書と行ごとに照らす。数・向きの語・表のセル・限界の文・次の便の候補は全部これで縛る。
   **§3(記録に欄の無い読み)の数は、記録に縛れないので字で留めるだけ**(門の中に同じ字が在る。記録に縛るのではない)
 e 文書の頭の負けと限界・次の便の候補が封 §6 の (i)〜(vi) だけ・言えないことを肯定で書かない・禁止語・docID と EDINET コードの形・日付・素材の字・漢数字の逃げ
 f 封・下見の封・script・定義表・読込みの定義・指示書・封の門・記録が commit の blob と 1 byte も違わない・engine は封の commit から 0 行・
   順序(封 → script など → 記録 → この文書と門)
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


MY_MODULE_NAME = "um1_seal_gate_for_result_gate"
SG = load_module("tests/measure/test_universal_ledger_seal.py", MY_MODULE_NAME)                 # 封の門の部品。門としては走らせない
PR = SG.PR
OVERWRITTEN = sorted(k for k, v in _BEFORE_MODULES.items() if sys.modules.get(k) is not v)

SEAL_REL, PRESEAL_REL = SG.SEAL_REL, SG.PRESEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
PRESEAL_COMMIT_SHORT = "31cac8fa"                   # 下見の封を足した commit
IMPL_COMMIT_SHORT = "29f192e0"                      # script・定義表・読込みの定義・指示書・封の門を足した commit
RECORD_COMMIT_SHORT = "191bfa38"                    # 記録を足した commit
CHECK_REL, REF_REL, DEF_REL, READING_REL, INSTR_REL = SG.CHECK_REL, SG.REF_REL, SG.DEF_REL, SG.READING_REL, SG.INSTRUCTION_REL
SEAL_GATE_REL = SG.GATE_REL
RECORD_REL = SG.RECORD_REL
GATE_REL = "tests/measure/test_universal_ledger_result.py"
DOC_REL = "docs/UNIVERSAL_MATERIAL_THIRD_PARTY_SOURCE_RESULT_2026-11-24.md"
IMPL_RELS = (CHECK_REL, REF_REL, DEF_REL, READING_REL, INSTR_REL, SEAL_GATE_REL)
BLOB_AT = od([(SEAL_REL, SEAL_COMMIT_SHORT)] + [(r, IMPL_COMMIT_SHORT) for r in IMPL_RELS] + [(RECORD_REL, RECORD_COMMIT_SHORT)])
DOC_COMMITS = (SEAL_COMMIT_SHORT, PRESEAL_COMMIT_SHORT, IMPL_COMMIT_SHORT, RECORD_COMMIT_SHORT)
SHA_PIN = od([
    (SEAL_REL, "0b1153edbe2f4698bcea5f85fae54c0a8334d334b3fed6c233c0f1b023584d0a"),
    (PRESEAL_REL, "a4916ab51c8cd40c20e23406ded9b19d440f6045c0bd0f98e0107a3a44e23df1"),
    (CHECK_REL, "ee2941344ff2fbf4d88e210669010d9f83e075f0727a00ca8ce9202075e3ca7a"),
    (REF_REL, "4c76988aa34591b6411f56b215101e4d5a0187fe9aadae16c3e3126a47d67c60"),
    (DEF_REL, "d9fcf07c27671d0501e9ce0b69e9320df942ffaaae6001d1a3903fe1ba15f61e"),
    (READING_REL, "913ccced360a97c252cafe850c636ba405cddd18e9d7f8dff6c345e6542f0731"),
    (INSTR_REL, "8acb0adbdc2a8bbbe26e82c9f15d562695e9581c620c7f80466d45fc44c029ed"),
    (SEAL_GATE_REL, "f6f8c968dd398f56e7491d06645da6b87cf47bb12f63f94a5ac756b525adffcd"),
    (RECORD_REL, "3961ffa2e208f537ddb5526c155f8ad521382a17b673b49633fc7fa76d1a2d5a")])


def read(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def read_or_empty(rel):
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        return u""
    return read(rel)


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
K_A, K_B = u"段 A", u"段 B"
TOP_KEYS = [u"便", u"封", u"段 A", u"段 B", u"確かめた取り方の表の SHA-256"]
A_KEYS = [u"正解の束", u"検査の結果", u"K3の行", u"規則の持ち越し", u"変異", u"A5", u"A6", u"素材の全体"]
B_KEYS = [u"席", u"席の数", u"全部", u"汚れた席の数", u"汚れを除く", u"束が K0 で断られた数", u"指定ごと", u"暦年の指定の率", u"ずらした指定の率", u"id ごと",
          u"c08", u"ずらした指定の c26", u"c28・c29", u"3 席が 3 つとも同じ行", u"席の取り直しの数"]
MUT_CODES = tuple(u"N%d" % k for k in range(1, 13))
MUT_KEYS = [u"作れた", u"表なしが通した", u"表つきが通した", u"数値が元と同じ", u"作れなかった"]
DESIGNATIONS = (u"S1", u"S2", u"S3", u"S4", u"S5")
ROWS_PER_BUNDLE = 30
SUMMARY_KEYS = [u"行", u"正解どおり", u"数値は同じで行の集まりだけ違う", u"表なし", u"表つき"]
LABEL_KEYS = [u"通した", u"止めた", u"断り", u"通した行のうち数値が違う", u"通した行のうち状態が違う", u"通した行のうち行の集まりだけ違う", u"正しい材料を止めた"]
PRED_IDS = tuple(u"UM1-A%d" % k for k in range(0, 8)) + tuple(u"UM1-B%d" % k for k in range(1, 9))
ID_COUNT = 30

# 封 §3 の予測の表の行(封にそのまま在ること。境はこの字の外に無い)
SEAL_ROWS = od([
    (u"UM1-A0", (u"本番の全体で、貸借が合わない伝票は 0", u"1 以上")),
    (u"UM1-A1", (u"正解の束 5 つで、関係 R1〜R3 は 15 本とも成り立つ", u"14 以下")),
    (u"UM1-A2", (u"開発の年に動きが無かった 34 科目のうち、2025-01-01〜2026-12-31 に行が在るのは 1 以上 6 以下", u"0 か 7 以上")),
    (u"UM1-A3", (u"表つきの検査が正解の束 150 行で「通す」か「無いを受ける」のは 80 以上 120 以下", u"79 以下か 121 以上")),
    (u"UM1-A4", (u"表つきの検査が通す変異は、作れたもののうち 0", u"1 以上")),
    (u"UM1-A5", (u"表なしの検査は、関係に入らない `在る` の行(c02・c07・c08・c21・c22・c24・c27)の N2・N3・N10 の作れた変異を全部通す", u"1 つでも止める")),
    (u"UM1-A6", (u"表なしの検査は、関係に入る行(c01・c03〜c06・c09〜c20・c23・c25・c26)の N2・N3・N7・N10 の作れた変異のうち、数値が元と違うものを 1 つも通さない", u"1 以上通す")),
    (u"UM1-A7", (u"規則の持ち越しが正解と違う行は 150 のうち 10 以上 40 以下", u"9 以下か 41 以上")),
    (u"UM1-B1", (u"席の答えが正解どおりの行は 450 のうち 338 以上(75%)", u"337 以下")),
    (u"UM1-B2", (u"暦年の指定(S1・S2。180 行)の正解どおりの率は、ずらした指定(S3〜S5。270 行)の率より高い", u"同じか低い")),
    (u"UM1-B3", (u"表つきの検査が通した席の行のうち、正解と数値が違う行は 0", u"1 以上")),
    (u"UM1-B4", (u"表なしの検査が通した席の行のうち、正解と数値が違う行は 1 以上", u"0")),
    (u"UM1-B5", (u"c08 の 15 行のうち、席が正解どおりは 8 以上", u"7 以下")),
    (u"UM1-B6", (u"ずらした指定の c26 の 9 行のうち、席が正解どおりは 5 以上", u"4 以下")),
    (u"UM1-B7", (u"c28・c29 の 30 行のうち、席が `無い` と書くのは 27 以上", u"26 以下")),
    (u"UM1-B8", (u"束が K0 で断られるのは 15 束のうち 0", u"1 以上"))])

# 変異の中身の要約(字は封 §1-8)。要約の頭の字が封に在ること(門が見る)
VARIANTS = od([
    (u"N1", (u"数値に 0.01 を足す", u"N1 数値に 0.01 を足す")),
    (u"N2", (u"「科目番号 どれでもない」の条件を 1 つ足し、数値を合わせる", u"N2 条件に `科目番号 どれでもない [x]` を足し数値を合わせる")),
    (u"N3", (u"「どれか」の並びに、その期に行が在る別の値を 1 つ足し、数値を合わせる", u"N3 `どれか` の並び")),
    (u"N4", (u"条件の日付だけをもう一方の期へ移し、数値を合わせる(期間の欄はそのまま)", u"N4 条件の日付をもう一方の期へ移し数値を合わせる")),
    (u"N5", (u"条件の日付と期間の欄の両方をもう一方の期へ移し、数値を合わせる", u"N5 条件の日付と `期間` の欄の両方をもう一方の期へ移し数値を合わせる")),
    (u"N6", (u"時点の行に「日付 以上」を足し、数値を合わせる", u"N6 時点の行に `日付 以上`")),
    (u"N7", (u"「仕訳の種類 どれでもない」の条件を外し、数値を合わせる", u"N7 `仕訳の種類 どれでもない` の条件を外し数値を合わせる")),
    (u"N8", (u"「在る」を「無い」にする", u"N8 `在る` を `無い` にする")),
    (u"N9", (u"「無い」を「在る」にする(条件を作り、数値を合わせる)", u"N9 `無い` を `在る` にする")),
    (u"N10", (u"向きを逆にし、数値を合わせる", u"N10 向きを逆にし数値を合わせる")),
    (u"N11", (u"別の「在る」の材料と、出どころと数値を入れ替える", u"N11 id の昇順で次の `在る` の材料")),
    (u"N12", (u"「日付 以下」を 1 日前にし、数値を合わせる", u"N12 `日付 以下` を 1 日前にし数値を合わせる"))])

# 文書が肯定で書いてはいけない言い方(出た文は「言えない」か「読まない」を持つ)
AFFIRM_PHRASES = (u"AI が材料を作れる", u"実物の会計の素材で動く", u"日本の会計ソフトの素材で動く", u"実物の素材で動く", u"会社の AI がこの型で書ける", u"誤りが無くなる",
                  u"人の確かめが要らない", u"専用の道具が要らない", u"開示の書類が作れる", u"XBRL を作れる", u"AI に任せられる")
FORBIDDEN_WORDS = (u"精度", u"LLM より正確", u"世界で 1 社", u"金額", u"契約", u"税", u"USD", u"保証")
SECRET_WORDS = SG.SECRET_WORDS + (u"Year-End", u"Operating", u"Asset", u"Revenue", u"Expense", u"売上高", u"売上原価", u"法人税", u"受取利息", u"減価償却")
DOCID_FORM = re.compile(r"(?<![0-9A-Za-z])S[0-9A-Z]{7}(?![0-9A-Za-z])")
ECODE_FORM = re.compile(r"(?<![0-9A-Za-z])E\d{5}(?![0-9A-Za-z])")
DATE_FORM = re.compile(r"(?<![0-9])(?:19|20)\d{2}[-/.]\d{1,2}[-/.]\d{1,2}(?![0-9])|(?<![0-9])(?:19|20)\d{2}年\d{1,2}月")
KANJI_NUM = re.compile(u"[〇一二三四五六七八九十百千万]{2,}")
DOC_DATE = u"2026-11-24"


# ================================================================== 写し
class Ctx(object):
    u"""検査が見る写し。変異はこの写しを変える(木の file は変えない)。"""

    def __init__(self):
        self.rec = json.loads(read(RECORD_REL), object_pairs_hook=od)
        self.doc = read_or_empty(DOC_REL)
        self.seal = read(SEAL_REL)
        self.shas = od((rel, sha_file(rel)) for rel in SHA_PIN)
        self.msg_impl = git_message(IMPL_COMMIT_SHORT)
        self.msg_record = git_message(RECORD_COMMIT_SHORT)
        self.seal_gate_tests = len(re.findall(r"(?m)^    def test_", read(SEAL_GATE_REL)))
        self._cache = None

    def copy(self):
        c = Ctx.__new__(Ctx)
        c.rec = copy.deepcopy(self.rec)
        c.doc, c.seal = self.doc, self.seal
        c.shas = od(self.shas)
        c.msg_impl, c.msg_record, c.seal_gate_tests = self.msg_impl, self.msg_record, self.seal_gate_tests
        c._cache = None
        return c

    def expected(self):
        key = (json.dumps(self.rec, ensure_ascii=False, sort_keys=False), self.seal, self.msg_impl, self.msg_record, self.seal_gate_tests)
        if self._cache is None or self._cache[0] != key:
            self._cache = (key, render(self))
        return self._cache[1]


def git_message(short):
    r = subprocess.run(["git", "-C", REPO, "log", "-1", "--format=%B", short], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.stdout.decode("utf-8")


# ================================================================== 記録の読み(script の関数を使わない)
def mut(rec, code):
    return rec[K_A][u"変異"][code]


def msum(rec, key, codes=MUT_CODES):
    return sum(mut(rec, c)[key] for c in codes)


def nonzero_by_code(rec, key):
    return [(c, mut(rec, c)[key]) for c in MUT_CODES if mut(rec, c)[key]]


def dotted(pairs):
    u"""[(N2, 4), (N3, 10)] → ``N2 4・N3 10``。"""
    return u"・".join(u"%s %d" % (k, v) for k, v in pairs)


def rule_total(rec):
    return sum(rec[K_A][u"検査の結果"][u"表つき"][u"止めた規則"].values())


def judge(rec):
    u"""封 §3 の 16 本の当たり外れ({id: True=当たり/False=外れ/None=記録では決まらない})。境は封の字。"""
    a, b = rec[K_A], rec[K_B]
    f = a[u"素材の全体"]
    tabled = a[u"検査の結果"][u"表つき"][u"判定"]
    out = od()
    out[u"UM1-A0"] = f[u"貸借が合わない伝票"] == 0
    g = a[u"正解の束"]
    out[u"UM1-A1"] = g[u"関係の本数"] == 15 and g[u"関係が成り立つ本数"] == 15
    if f[u"開発の年に動きが無かった科目"] != 34:
        out[u"UM1-A2"] = None
    else:
        out[u"UM1-A2"] = 1 <= f[u"うち指定の間に行が在る科目"] <= 6
    passed = tabled.get(u"通す", 0) + tabled.get(u"無いを受ける", 0)
    out[u"UM1-A3"] = g[u"行の数"] == 150 and 80 <= passed <= 120
    out[u"UM1-A4"] = msum(rec, u"表つきが通した") == 0
    out[u"UM1-A5"] = a[u"A5"][u"作れた"] > 0 and a[u"A5"][u"表なしが通した"] == a[u"A5"][u"作れた"]
    out[u"UM1-A6"] = a[u"A6"][u"数値が違う作れた"] > 0 and a[u"A6"][u"表なしが通した"] == 0
    out[u"UM1-A7"] = g[u"行の数"] == 150 and 10 <= a[u"規則の持ち越し"][u"正解と違う行"] <= 40
    out[u"UM1-B1"] = b[u"全部"][u"行"] == 450 and b[u"全部"][u"正解どおり"] >= 338
    cal, sh = b[u"暦年の指定の率"], b[u"ずらした指定の率"]
    out[u"UM1-B2"] = cal[u"正解どおり"] * sh[u"行"] > sh[u"正解どおり"] * cal[u"行"]
    out[u"UM1-B3"] = b[u"全部"][u"表つき"][u"通した行のうち数値が違う"] == 0
    out[u"UM1-B4"] = b[u"全部"][u"表なし"][u"通した行のうち数値が違う"] >= 1
    out[u"UM1-B5"] = b[u"c08"][u"行"] == 15 and b[u"c08"][u"正解どおり"] >= 8
    out[u"UM1-B6"] = b[u"ずらした指定の c26"][u"行"] == 9 and b[u"ずらした指定の c26"][u"正解どおり"] >= 5
    out[u"UM1-B7"] = b[u"c28・c29"][u"行"] == 30 and b[u"c28・c29"][u"席が無いと書いた"] >= 27
    out[u"UM1-B8"] = b[u"束が K0 で断られた数"] == 0 and b[u"席の数"] == 15
    return out


def verdict_word(v):
    return {True: u"当たり", False: u"外れ", None: u"記録では決まらない"}[v]


# ================================================================== 文書を記録と字から組み直す
def seal_candidates(seal):
    i = seal.index(u"## §6")
    return [l for l in seal[i:].splitlines() if re.match(r"^- \((?:i|ii|iii|iv|v|vi|vii|viii)\) ", l)]


def render(c):
    rec = c.rec
    a, b = rec[K_A], rec[K_B]
    f = a[u"素材の全体"]
    g = a[u"正解の束"]
    res = a[u"検査の結果"]
    plain, tabled = res[u"表なし"], res[u"表つき"]
    carry = a[u"規則の持ち越し"]
    k3 = a[u"K3の行"]
    allr, clean = b[u"全部"], b[u"汚れを除く"]
    j = judge(rec)
    hits = [i for i, v in j.items() if v is True]
    misses = [i for i, v in j.items() if v is False]
    made, tp, pp, same = msum(rec, u"作れた"), msum(rec, u"表つきが通した"), msum(rec, u"表なしが通した"), msum(rec, u"数値が元と同じ")
    rules = tabled[u"止めた規則"]
    cal, sh = b[u"暦年の指定の率"], b[u"ずらした指定の率"]
    n_seats = b[u"席の数"]
    idrows = b[u"id ごと"]
    low = [(k, v[u"正解どおり"]) for k, v in idrows.items() if v[u"正解どおり"] < v[u"行"]]
    hole = [k for k, v in idrows.items() if v[u"正解どおり"] < v[u"行"]]
    full_ids = len(idrows) - len(low)
    k3_loss = (tabled[u"判定"].get(u"通す", 0), tabled[u"判定"].get(u"止める", 0))
    cands = seal_candidates(c.seal)
    L = []
    w = L.append
    w(u"# 結果: 便 UM1 ― 他人が公開した作り物の会社の帳簿から、この PC の AI の席が材料を作り、答えを読まない検査が通す・止める ― 席 %d・指定 %d 本で数えた ― %s" % (n_seats, len(b[u"指定ごと"]), DOC_DATE))
    w(u"")
    w(u"封 `%s`(commit %s)。下見の封 `%s`(commit %s)。検査の script `%s`・答えを知っている側の script `%s`・定義表 `%s`・読込みの定義 `%s`・席への指示書 `%s`・封の門 `%s` は "
      u"commit %s(独立監査 REVISE → 直し → REVISE → 直し → REVISE → 直し → GO)。記録 `%s` は commit %s(独立監査 GO)。"
      u"費用は 0。API は呼んでいない。席はこの PC の subagent。engine(`core/`・`adapters/`)は 0 行。"
      % (SEAL_REL, SEAL_COMMIT_SHORT, PRESEAL_REL, PRESEAL_COMMIT_SHORT, CHECK_REL, REF_REL, DEF_REL, READING_REL, INSTR_REL, SEAL_GATE_REL, IMPL_COMMIT_SHORT, RECORD_REL, RECORD_COMMIT_SHORT))
    w(u"")
    w(u"この文書の §1・§2 の数は全部、記録から 1 つずつ読んだもの(結果の門が、記録の数と字で同じことを見る)。§3 は記録に欄の無い読みで、出どころを書く(結果の門は §3 の数を記録に縛らず、字で留めるだけ)。")
    w(u"")
    w(u"**先に負けと限界を書く。**")
    w(u"")
    w(u"- **予測 %d 本は外れ。** 外れは %s。判定した %d 本は 当たり %d・外れ %d。封 §4 が「一番大きい負け」と決めた UM1-B3(表つきの検査が通した席の行のうち、正解と数値が違う行は 0)は"
      u"当たりで、記録の数は %d。" % (len(misses), u" と ".join(misses), len(j), len(hits), len(misses), allr[u"表つき"][u"通した行のうち数値が違う"]))
    w(u"- **UM1-A4 の外れ: 表つきの検査が通した変異が在る。** 変異 N1〜N12 の作れた %d のうち、表つきの検査が通したのは %d(%s・ほか 0)。表なしの検査が通したのは %d。"
      u"記録の「数値が元と同じ」は、作れた変異の全体に対する数で、%s・ほか 0(合計 %d)。これは通した %d の部分集合とは記録から言えない。"
      u"通した変異の数値が元と違ったかどうかは記録に無く、測っていない。通した理由も 1 件ずつ読んでいない。"
      u"封 §4 に書いたとおり、A4・A5・A6 は検査の作りから決まる所が多く、当たっても「司令塔が決めた壊し方を、司令塔が決めた規則で止めた」以上は言わない。"
      % (made, tp, dotted(nonzero_by_code(rec, u"表つきが通した")), pp, dotted(nonzero_by_code(rec, u"数値が元と同じ")), same, tp))
    w(u"- **表つきの検査の止めすぎ。** 正解の束 %d 行のうち、表つきの検査が止めたのは %d 行(通す %d)。席の %d 行では %d 行を止め、そのうち正しい材料を止めたのは %d。"
      u"「正しい材料を止めた」は、席の答えが正解どおりなのに止めた行の数で、「無い」と正しく書いた行も入る。残りの %d は正解どおりでない行で、表つきの検査は %d 行とも止めた"
      u"(表なしの検査は %d 行とも通した)。汚れた席を除くと、止めた %d のうち正しい材料を止めたのは %d。"
      u"UM1-A3 は当たったが、「止めた行は人が見る」以上のことは言わない(人が見る手間は測っていない)。"
      % (g[u"行の数"], k3_loss[1], k3_loss[0], allr[u"行"], allr[u"表つき"][u"止めた"], allr[u"表つき"][u"正しい材料を止めた"],
         allr[u"表つき"][u"止めた"] - allr[u"表つき"][u"正しい材料を止めた"], allr[u"表つき"][u"止めた"] - allr[u"表つき"][u"正しい材料を止めた"],
         allr[u"表なし"][u"通した行のうち行の集まりだけ違う"], clean[u"表つき"][u"止めた"], clean[u"表つき"][u"正しい材料を止めた"]))
    w(u"- **UM1-B4 の外れ: 席が数値を 1 つも誤らなかった。** 表なしの検査が通した席の行 %d のうち、正解と数値が違うのは %d(状態が違うのも %d)。"
      u"「席の誤りを検査が止める」は、席の答えでは測れていない。席の答えが正解と違ったのは、数値は同じで行の集まりだけが違う %d 行(%s の行)。"
      u"検査が止める力は、変異でしか見ていない。"
      % (allr[u"表なし"][u"通した"], allr[u"表なし"][u"通した行のうち数値が違う"], allr[u"表なし"][u"通した行のうち状態が違う"], allr[u"数値は同じで行の集まりだけ違う"], u"・".join(hole)))
    w(u"- **表なしの検査が通した変異。** 作れた %d のうち %d を通した(%s・ほか 0。全部の表は §2)。N8 の %d は、表なしの検査が「無い」と書いた行を確かめずに受ける作り(封 §1-7)から決まる。"
      u"表なしの検査は、正解の束 %d 行を 1 行も止めなかった(止めた規則の欄が空)。"
      % (made, pp, dotted(nonzero_by_code(rec, u"表なしが通した")), mut(rec, u"N8")[u"表なしが通した"], g[u"行の数"]))
    w(u"- **表が在る期では、席が無くても規則の持ち越しだけで同じ材料が出る(封 §4)。** 規則の持ち越しが正解と違う行は %d のうち %d(同じ %d。数値だけ同じ %d は「無い」同士の行を含み、行の集まりは問わない)。"
      u"席が正解どおりだった行は %d のうち %d で、持ち越しの %d / %d と並べられるが、席の値打ちとは言わない。"
      u"席の値打ちが測れるのは、表なしの検査の側(1 期目)と、確かめていない科目が出た所だけ。"
      % (g[u"行の数"], carry[u"正解と違う行"], carry[u"正解と同じ行"], carry[u"数値だけ同じ行"], allr[u"行"], allr[u"正解どおり"], carry[u"正解と同じ行"], g[u"行の数"]))
    w(u"- **汚れ: 席 %d つが、自分の folder の外の file を 1 回読んだ。** 記録の「汚れた席の数」は %d。「1 回読んだ」は司令塔が席の会話の記録から数えたもので、記録に欄は無く、結果の門は記録に縛らない。"
      u"判定は全部の席(%d 席・%d 行)で行い、汚れを除いた数(%d 席・%d 行)を §2 に並べた。汚れを除いても、正解どおり %d・表なしが通した %d・表つきが通した %d。席の取り直しは %d。"
      % (b[u"汚れた席の数"], b[u"汚れた席の数"], n_seats, allr[u"行"], n_seats - b[u"汚れた席の数"], clean[u"行"], clean[u"正解どおり"], clean[u"表なし"][u"通した"], clean[u"表つき"][u"通した"], b[u"席の取り直しの数"]))
    w(u"- **席は全部、同じ種類の AI の席(この PC の Claude Code の subagent)で、%d 席。** 互いに独立でない。公開の素材とその説明を学習で知っている可能性を除けない。"
      u"この repo の `CLAUDE.md`・記憶の索引・直近の commit の題を文脈に持つ(封 §0)ので、会社の AI エージェントそのものではない。API の席・別の model では測っていない。"
      u"1 席 1 回で、揺れは「同じ指定の 3 席が 3 つとも同じ行」%d(分母は %d = 指定 %d × id %d)で見ただけ。"
      % (n_seats, b[u"3 席が 3 つとも同じ行"], len(b[u"指定ごと"]) * ID_COUNT, len(b[u"指定ごと"]), ID_COUNT))
    w(u"- **素材は他人が公開した作り物の会社 1 社の帳簿**(英語・米国の科目)で、実在の会社の帳簿ではない。素材の形は第三者が決めたが、読込みの定義・定義表の意味の字・正解の取り方・確かめた取り方の表・検査の規則・壊し方は、"
      u"同じ司令塔が開発の年を見て決めた(封 §5)。正解は独立の正解でなく、素材の作り手が付けた分類の字に依る。分類の字が誤っていれば、正解も、止める範囲も誤る。")
    w(u"- **席の答えと正解が食い違った %d 行は、1 行ずつ読んでいない。** 封 §1-4 は 1 行ずつ読んで司令塔の型分けと書くと決めたが、記録に行ごとの欄が無い。分かるのは、全部が %s の行で、数値は正解と同じで行の集まりだけが違うところまで。"
      % (allr[u"数値は同じで行の集まりだけ違う"], u"・".join(hole)))
    w(u"- 開発の年と本番の年は、同じ会社・同じ表の形。本番で新しいのは、見ていない期の値・締めをまたぐ期・新しく動く科目・入っているかもしれない異常だけ。指定 %d 本は同じ 2 年ほどの行を重ねて使うので、互いに独立でない(封 §5)。"
      % len(b[u"指定ごと"]))
    w(u"- 材料の型 `u1` が表せるのは「仕訳の行を条件で絞った和」だけ。従業員の数・返済予定表・補助の台帳から取る行は、この便で扱わない。確かめた取り方の表は、人が確かめたものでなく、司令塔が素材の分類の字の規則で作ったもの。"
      u"人が確かめる所(確認待ち → 表に足す)は作っていないし、測っていない(封 §5)。")
    w(u"- **測っていないこと**: 人が見る手間・通した変異の数値が元と違ったかどうか・通した変異が通った理由・席の誤りを検査が止める力(席の数値の誤りが 0 のため)・別の model や API の席・"
      u"わざと入れた異常を検査や正解が見つけたか(正解表が手元に無いので「見つけた」と言わない。封 §4)。")
    w(u"- **言えないこと**: 「実物の会計の素材で動く」「日本の会計ソフトの素材で動く」「会社の AI がこの型で書ける」「誤りが無くなる」「人の確かめが要らない」「専用の道具が要らない」。")
    w(u"")
    w(u"## §1 予測の当たり外れ(封を書いた司令塔が立てた)")
    w(u"")
    w(u"封 §3 の字の境と記録から、結果の門が UM1-A0〜UM1-B8 の当たり外れを決め直した(この表と同じ)。封も予測も結果を見てから書き換えていない。"
      u"素材・検査・正解・確かめた取り方の表も同じ司令塔が決めた(封 §5)。UM1-A4・A5・A6 は検査の作りから決まる所が多いと封 §4 に書いた。当たった %d 本を「未見で当てた」とは言わない。" % len(hits))
    w(u"")
    w(u"| # | 予測(封の字の要約) | 実測(記録) | 判定 |")
    w(u"|---|---|---|---|")
    rows = od([
        (u"UM1-A0", (u"本番の全体で、貸借が合わない伝票は 0", u"貸借が合わない伝票 %d" % f[u"貸借が合わない伝票"])),
        (u"UM1-A1", (u"正解の束 5 つで、関係 R1〜R3 は 15 本とも成り立つ", u"成り立つ %d / %d 本" % (g[u"関係が成り立つ本数"], g[u"関係の本数"]))),
        (u"UM1-A2", (u"開発の年に動きが無かった 34 科目のうち、本番の期間(指定 S1 の始まりから S2 の終わりまで)に行が在るのは 1 以上 6 以下",
                     u"動きが無かった %d 科目のうち行が在る %d" % (f[u"開発の年に動きが無かった科目"], f[u"うち指定の間に行が在る科目"]))),
        (u"UM1-A3", (u"表つきの検査が正解の束 150 行で「通す」か「無いを受ける」のは 80 以上 120 以下",
                     u"通す %d・止める %d(表つきの判定の欄に「無いを受ける」は無い)" % (k3_loss[0], k3_loss[1]))),
        (u"UM1-A4", (u"表つきの検査が通す変異は、作れたもののうち 0", u"作れた %d のうち通した %d(%s)" % (made, tp, dotted(nonzero_by_code(rec, u"表つきが通した"))))),
        (u"UM1-A5", (u"表なしの検査は、関係に入らない「在る」の行の N2・N3・N10 の作れた変異を全部通す",
                     u"作れた %d のうち表なしの検査が通した %d" % (a[u"A5"][u"作れた"], a[u"A5"][u"表なしが通した"]))),
        (u"UM1-A6", (u"表なしの検査は、関係に入る行の N2・N3・N7・N10 の作れた変異のうち、数値が元と違うものを 1 つも通さない",
                     u"数値が元と違う作れた %d のうち表なしの検査が通した %d" % (a[u"A6"][u"数値が違う作れた"], a[u"A6"][u"表なしが通した"]))),
        (u"UM1-A7", (u"規則の持ち越しが正解と違う行は 150 のうち 10 以上 40 以下", u"%d / %d" % (carry[u"正解と違う行"], g[u"行の数"]))),
        (u"UM1-B1", (u"席の答えが正解どおりの行は 450 のうち 338 以上(75%)", u"%d / %d = %s%%" % (allr[u"正解どおり"], allr[u"行"], pct(allr[u"正解どおり"], allr[u"行"])))),
        (u"UM1-B2", (u"暦年の指定(S1・S2。180 行)の正解どおりの率は、ずらした指定(S3〜S5。270 行)の率より高い",
                     u"暦年の指定 %d / %d = %s%%・ずらした指定 %d / %d = %s%%" % (cal[u"正解どおり"], cal[u"行"], pct(cal[u"正解どおり"], cal[u"行"]),
                                                                                  sh[u"正解どおり"], sh[u"行"], pct(sh[u"正解どおり"], sh[u"行"])))),
        (u"UM1-B3", (u"表つきの検査が通した席の行のうち、正解と数値が違う行は 0",
                     u"表つきが通した %d 行のうち数値が違う %d" % (allr[u"表つき"][u"通した"], allr[u"表つき"][u"通した行のうち数値が違う"]))),
        (u"UM1-B4", (u"表なしの検査が通した席の行のうち、正解と数値が違う行は 1 以上",
                     u"表なしが通した %d 行のうち数値が違う %d" % (allr[u"表なし"][u"通した"], allr[u"表なし"][u"通した行のうち数値が違う"]))),
        (u"UM1-B5", (u"c08 の 15 行のうち、席が正解どおりは 8 以上", u"%d / %d" % (b[u"c08"][u"正解どおり"], b[u"c08"][u"行"]))),
        (u"UM1-B6", (u"ずらした指定の c26 の 9 行のうち、席が正解どおりは 5 以上", u"%d / %d" % (b[u"ずらした指定の c26"][u"正解どおり"], b[u"ずらした指定の c26"][u"行"]))),
        (u"UM1-B7", (u"c28・c29 の 30 行のうち、席が「無い」と書くのは 27 以上", u"%d / %d" % (b[u"c28・c29"][u"席が無いと書いた"], b[u"c28・c29"][u"行"]))),
        (u"UM1-B8", (u"束が K0 で断られるのは 15 束のうち 0", u"%d / %d 束" % (b[u"束が K0 で断られた数"], n_seats)))])
    for i in PRED_IDS:
        w(u"| %s | %s | %s | %s |" % (i, rows[i][0], rows[i][1], verdict_word(j[i])))
    w(u"")
    w(u"- 当たり %d・外れ %d。外れは %s。" % (len(hits), len(misses), u"・".join(misses)))
    w(u"- UM1-B2 の「暦年の指定の率」「ずらした指定の率」は、率でなく 2 つの数(正解どおりの行と行の数)で、% は文書で計算した。差は小さく、別の素材で同じ向きかは測っていない。")
    w(u"")
    w(u"## §2 数(記録)")
    w(u"")
    w(u"**段 A(席を使わない)**")
    w(u"")
    w(u"- 素材の全体: 貸借が合わない伝票 %d・開発の年に動きが無かった科目 %d・うち指定の間(本番の期間)に行が在る科目 %d。"
      % (f[u"貸借が合わない伝票"], f[u"開発の年に動きが無かった科目"], f[u"うち指定の間に行が在る科目"]))
    w(u"- 正解の束 %d つ(指定 %s。1 束 %d 行): 行 %d(在る %d・無い %d)・関係が成り立つ %d / %d 本(指定ごとに 在る %s・関係が成り立つ %s)。"
      % (g[u"束の数"], u"・".join(g[u"指定ごと"]), ROWS_PER_BUNDLE, g[u"行の数"], g[u"状態"][u"在る"], g[u"状態"][u"無い"], g[u"関係が成り立つ本数"], g[u"関係の本数"],
         u"・".join(str(v[u"在る"]) for v in g[u"指定ごと"].values()), u"・".join(str(v[u"関係が成り立つ"]) for v in g[u"指定ごと"].values())))
    w(u"- 規則の持ち越し(席を使わない): 正解と同じ行 %d・正解と違う行 %d・数値だけ同じ行 %d。" % (carry[u"正解と同じ行"], carry[u"正解と違う行"], carry[u"数値だけ同じ行"]))
    w(u"- K3 の行(単位は元帳の行の数。材料の数でない): 余り %d・漏れ %d。" % (k3[u"余り"], k3[u"漏れ"]))
    w(u"")
    w(u"正解の束 %d 行への検査の結果:" % g[u"行の数"])
    w(u"")
    w(u"| 検査 | 通す | 無いを受ける | 止める | 止めた規則(当たりの数) |")
    w(u"|---|---|---|---|---|")
    for label, r in ((u"表なし", plain), (u"表つき", tabled)):
        jd = r[u"判定"]
        rr = u"・".join(u"%s %d" % (k, v) for k, v in r[u"止めた規則"].items()) or u"―"
        w(u"| %s | %s | %s | %s | %s |" % (label, jd.get(u"通す", u"―"), jd.get(u"無いを受ける", u"―"), jd.get(u"止める", u"―"), rr))
    w(u"")
    w(u"変異(正解の束の材料 1 つにつき 1 か所。両方の検査に掛けた。字は封 §1-8 の要約):")
    w(u"")
    w(u"| 変異 | 中身 | 作れた | 作れなかった | 表なしが通した | 表つきが通した | 数値が元と同じ |")
    w(u"|---|---|---|---|---|---|---|")
    for code in MUT_CODES:
        r = mut(rec, code)
        w(u"| %s | %s | %d | %d | %d | %d | %d |" % (code, VARIANTS[code][0], r[u"作れた"], r[u"作れなかった"], r[u"表なしが通した"], r[u"表つきが通した"], r[u"数値が元と同じ"]))
    w(u"| 合計 | ― | %d | %d | %d | %d | %d |" % (made, msum(rec, u"作れなかった"), pp, tp, same))
    w(u"")
    w(u"- UM1-A5: 関係に入らない「在る」の行の N2・N3・N10 の作れた %d のうち、表なしの検査が通した %d。" % (a[u"A5"][u"作れた"], a[u"A5"][u"表なしが通した"]))
    w(u"- UM1-A6: 関係に入る行の N2・N3・N7・N10 の作れた変異のうち、数値が元と違う %d で、表なしの検査が通した %d。" % (a[u"A6"][u"数値が違う作れた"], a[u"A6"][u"表なしが通した"]))
    w(u"")
    w(u"**段 B(席。15 席・指定ごとに 3 席)**: 束が K0 で断られた %d・席の取り直し %d・汚れた席 %d。" % (b[u"束が K0 で断られた数"], b[u"席の取り直しの数"], b[u"汚れた席の数"]))
    w(u"")
    w(u"| 欄 | 全部(%d 席) | 汚れを除く(%d 席) |" % (n_seats, n_seats - b[u"汚れた席の数"]))
    w(u"|---|---|---|")
    for k in (u"行", u"正解どおり", u"数値は同じで行の集まりだけ違う"):
        w(u"| %s | %d | %d |" % (k, allr[k], clean[k]))
    for label in (u"表なし", u"表つき"):
        for k in LABEL_KEYS:
            w(u"| %s: %s | %d | %d |" % (label, k, allr[label][k], clean[label][k]))
    w(u"")
    w(u"指定ごと(1 指定 3 席・90 行):")
    w(u"")
    w(u"| 指定 | 行 | 正解どおり | 表なしが通した | 表つきが通した | 表つきが止めた | 正しい材料を止めた(表つき) |")
    w(u"|---|---|---|---|---|---|---|")
    for d, s in b[u"指定ごと"].items():
        w(u"| %s | %d | %d | %d | %d | %d | %d |" % (d, s[u"行"], s[u"正解どおり"], s[u"表なし"][u"通した"], s[u"表つき"][u"通した"], s[u"表つき"][u"止めた"], s[u"表つき"][u"正しい材料を止めた"]))
    w(u"")
    w(u"- 暦年の指定(S1・S2)の行 %d・正解どおり %d。ずらした指定(S3〜S5)の行 %d・正解どおり %d。" % (cal[u"行"], cal[u"正解どおり"], sh[u"行"], sh[u"正解どおり"]))
    w(u"- id ごと(%d の id・各 %d 行): 正解どおりが行の数に届かないのは %s。ほかの %d は全部、行の数と同じ。" % (len(idrows), n_seats, u"・".join(u"%s(%d)" % kv for kv in low) or u"無し", full_ids))
    w(u"- c08: %d / %d。ずらした指定の c26: %d / %d。c28・c29 で席が「無い」と書いた: %d / %d。" % (
        b[u"c08"][u"正解どおり"], b[u"c08"][u"行"], b[u"ずらした指定の c26"][u"正解どおり"], b[u"ずらした指定の c26"][u"行"], b[u"c28・c29"][u"席が無いと書いた"], b[u"c28・c29"][u"行"]))
    w(u"- 3 席が 3 つとも同じ行: %d / %d。" % (b[u"3 席が 3 つとも同じ行"], len(b[u"指定ごと"]) * ID_COUNT))
    w(u"")
    w(u"**欄の読み方(取り違えやすい所)**")
    w(u"")
    w(u"- 「止めた規則」は当たりの数で、行の数ではない。表つきの止めた行は %d、規則の当たりの合計は %d で、2 つ以上の規則に当たった行が在る。" % (k3_loss[1], rule_total(rec)))
    w(u"- 「正しい材料を止めた」は、席の答えが正解どおりなのに止めた行の数。「無い」と正しく書いた行も入る。")
    w(u"- 「K3 の行 余り %d・漏れ %d」の単位は、元帳の行の数。" % (k3[u"余り"], k3[u"漏れ"]))
    w(u"- 「正解どおり」は、状態・数値・条件が選ぶ行の集まりまで同じであること。数値と状態だけなら、%d 行とも正解と同じ(通した行のうち数値が違う %d・状態が違う %d)。違う %d 行は、%s の行の集まりだけ。"
      % (allr[u"行"], allr[u"表なし"][u"通した行のうち数値が違う"], allr[u"表なし"][u"通した行のうち状態が違う"], allr[u"数値は同じで行の集まりだけ違う"], u"・".join(hole)))
    w(u"- 「3 席が 3 つとも同じ行」の分母は %d(指定 %d × id %d)。" % (len(b[u"指定ごと"]) * ID_COUNT, len(b[u"指定ごと"]), ID_COUNT))
    w(u"- 「数値が元と同じ」は、作れた変異の全体に対する数で、通した数の部分集合とは限らない。")
    w(u"")
    w(u"## §3 記録に欄の無い読み(測った数の一部は記録に無い。出どころを書く。結果の門は記録に縛らず、字で留めるだけ)")
    w(u"")
    w(u"- **汚れた席の読み。** 席 1 つが自分の folder の外の file を 1 回読んだ。司令塔が席の会話の記録から数えた。記録に欄は無い。記録にあるのは「汚れた席の数」だけ。")
    w(u"- **席の種類。** 15 席は全部、同じ種類の AI の席(この PC の subagent)。司令塔の数えで、記録に欄は無い。")
    w(u"- **独立監査が確かめたこと**(commit %s の message): 別の実装で、素材の全体・正解の束・席の %d 行・表つきの検査・持ち越しを数え直し差は 0・集計と記録の再実行は同じ byte。"
      u"**確かめていないこと:** 変異と A5・A6 は数え直していない。全体の suite は未実行。" % (RECORD_COMMIT_SHORT, allr[u"行"]))
    w(u"")
    w(u"## §4 門")
    w(u"")
    w(u"- 結果の門 `%s`: 記録の数え直し(正解の束・検査の結果・変異・段 B の全部と指定ごとの足し算)・予測の当たり外れの決め直し・この文書の全部の行を記録と字から組み直して照らす・"
      u"封と下見の封と script と定義表と読込みの定義と指示書と封の門と記録が commit の blob と 1 byte も違わないこと・engine が封の commit から 0 行・順序(封 → script など → 記録 → この文書と門)。"
      u"変異で赤くなることを門の中で確かめる。" % GATE_REL)
    w(u"- 封の門 `%s` の試験は %d 本(file の中の `def test_` の数を結果の門が数える)。独立監査は REVISE を 3 回出してから GO(commit %s の message)。"
      % (SEAL_GATE_REL, c.seal_gate_tests, IMPL_COMMIT_SHORT))
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


def _ints(*xs):
    return all(type(x) is int and x >= 0 for x in xs)


def keys_problems(rec):
    if not isinstance(rec, dict) or list(rec) != TOP_KEYS:
        return [u"記録の頂の鍵"]
    if rec[u"便"] != u"UM1" or rec[u"封"] != SEAL_COMMIT_SHORT:
        return [u"便か封の字"]
    a, b = rec[K_A], rec[K_B]
    if list(a) != A_KEYS:
        return [u"段 A の鍵"]
    if list(b) != B_KEYS:
        return [u"段 B の鍵"]
    if sorted(a[u"変異"]) != sorted(MUT_CODES) or any(list(v) != MUT_KEYS for v in a[u"変異"].values()):
        return [u"変異の鍵"]
    if list(b[u"指定ごと"]) != list(DESIGNATIONS) or any(list(v) != SUMMARY_KEYS for v in b[u"指定ごと"].values()):
        return [u"指定ごとの鍵"]
    if list(b[u"全部"]) != SUMMARY_KEYS or list(b[u"汚れを除く"]) != SUMMARY_KEYS:
        return [u"全部か汚れを除くの鍵"]
    for s in [b[u"全部"], b[u"汚れを除く"]] + list(b[u"指定ごと"].values()):
        if list(s[u"表なし"]) != LABEL_KEYS or list(s[u"表つき"]) != LABEL_KEYS:
            return [u"表なし・表つきの鍵"]
    return []


def recount_problems(c):
    u"""記録の数え直し。足し算の関係(検査・答えを知っている側の script の関数は使わない)。"""
    rec = c.rec
    out = keys_problems(rec)
    if out:
        return out
    a, b = rec[K_A], rec[K_B]
    g = a[u"正解の束"]
    if g[u"行の数"] != sum(g[u"状態"].values()) or g[u"行の数"] != ROWS_PER_BUNDLE * g[u"束の数"]:
        out.append(u"正解の束の行の数")
    if g[u"関係の本数"] != 3 * g[u"束の数"]:
        out.append(u"関係の本数が 3 × 束の数でない")
    if list(g[u"指定ごと"]) != list(DESIGNATIONS) or len(g[u"指定ごと"]) != g[u"束の数"]:
        out.append(u"正解の束の指定ごとの鍵")
    else:
        if sum(v[u"在る"] for v in g[u"指定ごと"].values()) != g[u"状態"][u"在る"]:
            out.append(u"指定ごとの 在る の和が状態と違う")
        if sum(v[u"関係が成り立つ"] for v in g[u"指定ごと"].values()) != g[u"関係が成り立つ本数"]:
            out.append(u"指定ごとの 関係が成り立つ の和が違う")
    if g[u"関係が成り立つ本数"] > g[u"関係の本数"]:
        out.append(u"関係が成り立つ本数が関係の本数より多い")
    res = a[u"検査の結果"]
    for label in (u"表なし", u"表つき"):
        if sum(res[label][u"判定"].values()) != g[u"行の数"]:
            out.append(u"%s の判定の和が行の数と違う" % label)
        if sum(res[label][u"止めた規則"].values()) < res[label][u"判定"].get(u"止める", 0):
            out.append(u"%s の止めた規則の当たりの和が止めた行より少ない" % label)
        if (res[label][u"判定"].get(u"止める", 0) == 0) != (not res[label][u"止めた規則"]):
            out.append(u"%s の止めた行と止めた規則の有無が合わない" % label)
    if res[u"表なし"][u"判定"].get(u"無いを受ける", 0) != g[u"状態"][u"無い"]:
        out.append(u"表なしの無いを受けるが 無い の行の数と違う")
    cr = a[u"規則の持ち越し"]
    if cr[u"正解と同じ行"] + cr[u"正解と違う行"] != g[u"行の数"] or not cr[u"正解と同じ行"] <= cr[u"数値だけ同じ行"] <= g[u"行の数"]:
        out.append(u"規則の持ち越しの足し算")
    if not _ints(*a[u"K3の行"].values()):
        out.append(u"K3の行の型")
    for code, r in a[u"変異"].items():
        if r[u"作れた"] + r[u"作れなかった"] != g[u"行の数"]:
            out.append(u"%s の作れた+作れなかったが行の数と違う" % code)
        if not r[u"表つきが通した"] <= r[u"表なしが通した"] <= r[u"作れた"]:
            out.append(u"%s の 表つきが通した ≤ 表なしが通した ≤ 作れた が崩れた" % code)
        if r[u"数値が元と同じ"] > r[u"作れた"]:
            out.append(u"%s の数値が元と同じが作れたより多い" % code)
    a5, a6 = a[u"A5"], a[u"A6"]
    if not (a5[u"表なしが通した"] <= a5[u"作れた"] <= sum(mut(rec, k)[u"作れた"] for k in (u"N2", u"N3", u"N10"))):
        out.append(u"A5 の数")
    if not (a6[u"表なしが通した"] <= a6[u"数値が違う作れた"] <= sum(mut(rec, k)[u"作れた"] - mut(rec, k)[u"数値が元と同じ"] for k in (u"N2", u"N3", u"N7", u"N10"))):
        out.append(u"A6 の数")
    f = a[u"素材の全体"]
    if not _ints(*f.values()) or f[u"うち指定の間に行が在る科目"] > f[u"開発の年に動きが無かった科目"]:
        out.append(u"素材の全体の数")
    # ---- 段 B
    n_seats = b[u"席の数"]
    seats = b[u"席"]
    if n_seats != len(seats) or sorted(set(s[u"指定"] for s in seats.values())) != list(DESIGNATIONS):
        out.append(u"席の数か指定")
    elif any(sum(1 for s in seats.values() if s[u"指定"] == d) != 3 for d in DESIGNATIONS):
        out.append(u"1 指定につき 3 席でない")
    if b[u"全部"][u"行"] != ROWS_PER_BUNDLE * n_seats:
        out.append(u"全部の行が 30 × 席の数でない")
    if b[u"汚れた席の数"] > n_seats or b[u"全部"][u"行"] - b[u"汚れを除く"][u"行"] != ROWS_PER_BUNDLE * b[u"汚れた席の数"]:
        out.append(u"汚れを除くの行")
    for name, s in [(u"全部", b[u"全部"]), (u"汚れを除く", b[u"汚れを除く"])] + list(b[u"指定ごと"].items()):
        if s[u"正解どおり"] + s[u"数値は同じで行の集まりだけ違う"] > s[u"行"]:
            out.append(u"%s: 正解どおり+集まりだけ違うが行より多い" % name)
        for label in (u"表なし", u"表つき"):
            t = s[label]
            if t[u"通した"] + t[u"止めた"] + t[u"断り"] != s[u"行"]:
                out.append(u"%s %s: 通した+止めた+断り が行と違う" % (name, label))
            if max(t[u"通した行のうち数値が違う"], t[u"通した行のうち状態が違う"], t[u"通した行のうち行の集まりだけ違う"]) > t[u"通した"]:
                out.append(u"%s %s: 通した行のうち が通したより多い" % (name, label))
            if t[u"通した行のうち数値が違う"] > s[u"行"] - s[u"正解どおり"]:
                out.append(u"%s %s: 数値が違う通した行が正解どおりでない行より多い" % (name, label))
            if t[u"正しい材料を止めた"] > min(t[u"止めた"], s[u"正解どおり"]):
                out.append(u"%s %s: 正しい材料を止めたが止めた・正解どおりより多い" % (name, label))
    for key in [u"行", u"正解どおり", u"数値は同じで行の集まりだけ違う"]:
        if sum(s[key] for s in b[u"指定ごと"].values()) != b[u"全部"][key]:
            out.append(u"指定ごとの %s の和が全部と違う" % key)
    for label in (u"表なし", u"表つき"):
        for key in LABEL_KEYS:
            if sum(s[label][key] for s in b[u"指定ごと"].values()) != b[u"全部"][label][key]:
                out.append(u"指定ごとの %s: %s の和が全部と違う" % (label, key))
            if b[u"汚れを除く"][label][key] > b[u"全部"][label][key]:
                out.append(u"汚れを除く %s: %s が全部より多い" % (label, key))
    cal, sh = b[u"暦年の指定の率"], b[u"ずらした指定の率"]
    ps = b[u"指定ごと"]
    if cal[u"行"] != ps[u"S1"][u"行"] + ps[u"S2"][u"行"] or cal[u"正解どおり"] != ps[u"S1"][u"正解どおり"] + ps[u"S2"][u"正解どおり"]:
        out.append(u"暦年の指定の率の和")
    if sh[u"行"] != sum(ps[d][u"行"] for d in (u"S3", u"S4", u"S5")) or sh[u"正解どおり"] != sum(ps[d][u"正解どおり"] for d in (u"S3", u"S4", u"S5")):
        out.append(u"ずらした指定の率の和")
    idr = b[u"id ごと"]
    if len(idr) != ID_COUNT or sum(v[u"行"] for v in idr.values()) != b[u"全部"][u"行"] or sum(v[u"正解どおり"] for v in idr.values()) != b[u"全部"][u"正解どおり"]:
        out.append(u"id ごとの和")
    elif any(v[u"行"] != n_seats or v[u"正解どおり"] > v[u"行"] for v in idr.values()):
        out.append(u"id ごとの行が席の数でない")
    elif b[u"c08"] != idr[u"c08"]:
        out.append(u"c08 が id ごとの c08 と違う")
    if b[u"ずらした指定の c26"][u"行"] != sum(1 for s in seats.values() if s[u"指定"] in (u"S3", u"S4", u"S5")) or b[u"ずらした指定の c26"][u"正解どおり"] > b[u"ずらした指定の c26"][u"行"]:
        out.append(u"ずらした指定の c26")
    if b[u"c28・c29"][u"行"] != 2 * n_seats or b[u"c28・c29"][u"席が無いと書いた"] > b[u"c28・c29"][u"行"]:
        out.append(u"c28・c29")
    if not _ints(b[u"3 席が 3 つとも同じ行"], b[u"束が K0 で断られた数"], b[u"席の取り直しの数"]) or b[u"3 席が 3 つとも同じ行"] > len(DESIGNATIONS) * ID_COUNT or b[u"束が K0 で断られた数"] > n_seats:
        out.append(u"3 席が同じ行・K0 の断り・取り直し")
    if b[u"束が K0 で断られた数"] * ROWS_PER_BUNDLE > b[u"全部"][u"表なし"][u"断り"] or b[u"全部"][u"表なし"][u"断り"] != b[u"全部"][u"表つき"][u"断り"]:
        out.append(u"断りの数が束の断りと合わない")
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
    u"""封の字: 予測の表の 16 行・§6 の候補 (i)〜(vi)・変異の中身・§4 の字が封にそのまま在る。"""
    out = []
    for i, (p, o) in SEAL_ROWS.items():
        row = u"| %s | %s | %s |" % (i, p, o)
        if row not in c.seal:
            out.append(u"封に予測の行が無い: %s" % i)
    cands = seal_candidates(c.seal)
    if len(cands) != 6 or [x.split(u" ")[1] for x in cands] != [u"(i)", u"(ii)", u"(iii)", u"(iv)", u"(v)", u"(vi)"]:
        out.append(u"封 §6 の候補が (i)〜(vi) の 6 つでない")
    for code, (_summary, anchor) in VARIANTS.items():
        if anchor not in c.seal:
            out.append(u"封に変異の字が無い: %s" % code)
    for must in (u"結果の文書はここに無い候補を足さない", u"UM1-B3 が外れたら", u"表が在る期では、席が無くても規則の持ち越しだけで同じ材料が出る", u"席の値打ちが測れるのは、表なしの検査の側(1 期目)と、確かめていない科目が出た所だけ",
                 u"席は同じ種類の subagent が 15 席", u"互いに独立でない", u"公開の素材とその説明を学習で知っている可能性を除けない", u"人が確かめる所(確認待ち → 表に足す)は作っていない・測っていない",
                 u"指定 5 つは同じ 2 年ほどの行を重ねて使うので、互いに独立でない", u"司令塔が開発の年を見て決めた", u"独立の正解ではない", u"`無い` の行は確かめずに「無いを受ける」",
                 u"この repo の `CLAUDE.md`・記憶の索引・直近の commit の題を文脈に持つ", u"結果の文書で 1 行ずつ読み"):
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
    u"""§5 の次の便の候補が封 §6 の (i)〜(vi) とちょうど同じ(足さない・落とさない・入れ替えない)。"""
    i = c.doc.find(u"## §5 ")
    if i < 0:
        return [u"§5 が無い"]
    body = c.doc[i:]
    cands = [l for l in body.splitlines() if l.startswith(u"- ")]
    want = seal_candidates(c.seal)
    out = []
    if cands != want:
        out.append(u"§5 の候補が封 §6 の候補と違う")
    if re.search(r"\((?:vii|viii|ix)\)", body):
        out.append(u"§5 に (vii) 以降の候補が在る")
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


HEAD_FRAGS = (u"**先に負けと限界を書く。**", u"UM1-A4 の外れ: 表つきの検査が通した変異が在る", u"通した変異の数値が元と違ったかどうかは記録に無く、測っていない", u"表つきの検査の止めすぎ",
              u"「正しい材料を止めた」は", u"「止めた行は人が見る」以上のことは言わない", u"UM1-B4 の外れ: 席が数値を 1 つも誤らなかった", u"検査が止める力は、変異でしか見ていない", u"表なしの検査が通した変異",
              u"表が在る期では、席が無くても規則の持ち越しだけで同じ材料が出る", u"席の値打ちとは言わない", u"汚れ: 席", u"結果の門は記録に縛らない", u"同じ種類の AI の席", u"互いに独立でない",
              u"公開の素材とその説明を学習で知っている可能性を除けない", u"API の席・別の model では測っていない", u"他人が公開した作り物の会社 1 社の帳簿", u"実在の会社の帳簿ではない",
              u"同じ司令塔が開発の年を見て決めた", u"正解は独立の正解でなく", u"1 行ずつ読んでいない", u"互いに独立でない(封 §5)", u"人が確かめる所(確認待ち → 表に足す)は作っていないし、測っていない",
              u"**測っていないこと**", u"**言えないこと**")


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
    for must in (u"記録に縛らず、字で留めるだけ", u"記録に欄は無い", u"司令塔が席の会話の記録から数えた", u"独立監査が確かめたこと", u"確かめていないこと"):
        if must not in s3:
            out.append(u"§3 に字が無い: %s" % must)
    outside = c.doc[:i] + c.doc[j:]
    for must_not in (u"集計と記録の再実行は同じ byte", u"変異と A5・A6 は数え直していない", u"全部、同じ種類の AI の席(この PC の subagent)"):
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
    out += [u"素材の字: %s" % w for w in SECRET_WORDS if w in c.doc]
    if DOCID_FORM.search(c.doc) or ECODE_FORM.search(c.doc):
        out.append(u"docID か EDINET コードの形が在る")
    for d in DATE_FORM.findall(re.sub(r"`[^`]*`", u" ", c.doc)):        # file の名の中の日付は許す(code span の外だけ見る)
        if d != DOC_DATE:
            out.append(u"文書に日付が在る: %s" % d)
    if KANJI_NUM.search(c.doc):
        out.append(u"漢数字の並びが在る(数は 3 桁以上を漢数字で逃がさない): %s" % KANJI_NUM.search(c.doc).group(0))
    return out


def commit_problems(c):
    out = []
    for w in DOC_COMMITS:
        if w not in c.doc:
            out.append(u"文書に commit の字が無い: %s" % w)
    if not set(re.findall(r"(?<![0-9A-Za-z])[0-9a-f]{8}(?![0-9A-Za-z])", c.doc)) <= set(DOC_COMMITS):
        out.append(u"文書が知らない commit の字を書いている")
    for short, msg, words in (
            (IMPL_COMMIT_SHORT, c.msg_impl, (u"独立監査 REVISE", u"→ 直し → REVISE", u"→ 直し → GO", u"門は 113 本")),
            (RECORD_COMMIT_SHORT, c.msg_record, (u"独立監査 GO", u"別の実装で素材の全体・正解の束・席の 450 行・表つきの検査・持ち越しを数え直し差は 0", u"集計と記録の再実行は同じ byte",
                                                 u"変異と A5・A6 は数え直していない", u"席の取り直しは 0・汚れた席は 1"))):
        for w in words:
            if w not in msg:
                out.append(u"commit %s の message に「%s」が無い" % (short, w))
    if len(re.findall(r"→ 直し →", c.msg_impl)) != 3 or len(re.findall(r"REVISE", c.msg_impl)) != 3:
        out.append(u"実装の commit の message の REVISE の回数が 3 でない")
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
    u"""封・script など・記録の file が、文書の書く commit だけで足され、最後の commit もそれ(封の後で変わっていない)。下見の封は 2 つの commit(足した・封で追記)。"""
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
    added = PR.added_commits(root, PREFIX + PRESEAL_REL)
    if len(added) != 1 or not added[0].startswith(PRESEAL_COMMIT_SHORT):
        out.append(u"下見の封を足した commit が %s でない" % PRESEAL_COMMIT_SHORT)
    rc, hist = PR.git_in(root, "log", "--format=%h", "--", PREFIX + PRESEAL_REL)
    if [x[:8] for x in hist.split()] != [SEAL_COMMIT_SHORT, PRESEAL_COMMIT_SHORT]:
        out.append(u"下見の封の履歴が 封の commit と下見の commit の 2 つでない")
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


def setp(c, path, value):
    node = c.rec
    for k in path[:-1]:
        node = node[k]
    node[path[-1]] = value
    return c


def drop_line(c, frag):
    return setattr(c, "doc", u"\n".join(l for l in c.doc.split(u"\n") if frag not in l)) or c


def consistent_a4_zero(c):
    for code in MUT_CODES:
        c.rec[K_A][u"変異"][code][u"表つきが通した"] = 0
    return c


def consistent_b4_zero_to_one(c):
    setp(c, (K_B, u"指定ごと", u"S2", u"表なし", u"通した行のうち数値が違う"), 1)
    return setp(c, (K_B, u"全部", u"表なし", u"通した行のうち数値が違う"), 1)


def consistent_b3_one(c):
    setp(c, (K_B, u"指定ごと", u"S2", u"表つき", u"通した行のうち数値が違う"), 1)
    return setp(c, (K_B, u"全部", u"表つき", u"通した行のうち数値が違う"), 1)


def consistent_a0_one(c):
    return setp(c, (K_A, u"素材の全体", u"貸借が合わない伝票"), 1)


def consistent_a1_fourteen(c):
    setp(c, (K_A, u"正解の束", u"関係が成り立つ本数"), 14)
    return setp(c, (K_A, u"正解の束", u"指定ごと", u"S5", u"関係が成り立つ"), 2)


def consistent_a2_zero(c):
    return setp(c, (K_A, u"素材の全体", u"うち指定の間に行が在る科目"), 0)


def consistent_a3_low(c):
    j = c.rec[K_A][u"検査の結果"][u"表つき"][u"判定"]
    j[u"通す"] = 79
    j[u"止める"] = 71
    return c


def consistent_a7_low(c):
    cr = c.rec[K_A][u"規則の持ち越し"]
    cr[u"正解と同じ行"], cr[u"正解と違う行"], cr[u"数値だけ同じ行"] = 141, 9, 141
    return c


def consistent_b7_low(c):
    return setp(c, (K_B, u"c28・c29", u"席が無いと書いた"), 26)


def consistent_b8_one(c):
    return setp(c, (K_B, u"束が K0 で断られた数"), 1)


def consistent_a5_one_stopped(c):
    return setp(c, (K_A, u"A5", u"表なしが通した"), 94)


def consistent_a6_one_passed(c):
    return setp(c, (K_A, u"A6", u"表なしが通した"), 1)


MUTATIONS = od([
    (u"F1  記録の sha256 の写しを違う値に", (lambda c: c.shas.__setitem__(RECORD_REL, u"0" * 64) or c, (u"sha",))),
    (u"F2  封の sha256 の写しを違う値に", (lambda c: c.shas.__setitem__(SEAL_REL, u"0" * 64) or c, (u"sha",))),
    (u"F3  検査の script の sha256 の写しを違う値に", (lambda c: c.shas.__setitem__(CHECK_REL, u"0" * 64) or c, (u"sha",))),
    (u"F4  封の門の sha256 の写しを違う値に", (lambda c: c.shas.__setitem__(SEAL_GATE_REL, u"0" * 64) or c, (u"sha",))),
    (u"F5  下見の封の sha256 の写しを違う値に", (lambda c: c.shas.__setitem__(PRESEAL_REL, u"0" * 64) or c, (u"sha",))),
    (u"F6  記録の頂の鍵を消す", (lambda c: c.rec.pop(K_B) and c, (u"recount",))),
    (u"F7  記録の指定ごとの鍵を 1 つ消す", (lambda c: c.rec[K_B][u"指定ごと"].pop(u"S5") and c, (u"recount",))),
    (u"F8  記録に docID の形を足す", (lambda c: c.rec[K_B].__setitem__(u"x", u"SXXXXXXX") or c, (u"clean", u"recount"))),
    (u"F9  記録に日付の形を足す", (lambda c: c.rec[K_A].__setitem__(u"x", u"2026-11-24") or c, (u"clean", u"recount"))),
    (u"F10 記録に素材の字を足す", (lambda c: c.rec[K_A].__setitem__(u"x", u"売上高") or c, (u"clean", u"recount"))),
    (u"F11 封の予測の行を 1 つ消す(境の字)", (lambda c: rep(c, u"| UM1-B1 | 席の答えが正解どおりの行は 450 のうち 338 以上(75%) | 337 以下 |", u"", "seal"), (u"bound",))),
    (u"F12 封の予測の行の境を替える(338 → 300)", (lambda c: rep(c, u"338 以上(75%)", u"300 以上(75%)", "seal"), (u"bound",))),
    (u"F13 封 §6 に (vii) の候補を足す(封の写しだけ)", (lambda c: setattr(c, "seal", c.seal.rstrip(u"\n") + u"\n- (vii) 新しい候補。\n") or c, (u"bound", u"sec5", u"lines"))),
    (u"F14 封 §6 の (iv) の字を替える(封の写しだけ)", (lambda c: rep(c, u"- (iv) この便の材料から資料の生成まで", u"- (iv) 変えた字", "seal"), (u"lines", u"sec5"))),
    (u"F15 封の変異の字を替える(N8)", (lambda c: rep(c, u"N8 `在る` を `無い` にする", u"N8 変えた字", "seal"), (u"bound",))),
    (u"C1  UM1-A4 を当たりにする(表つきが通したを全部 0 に。足し算は合ったまま)", (consistent_a4_zero, (u"verdict", u"lines"))),
    (u"C2  UM1-B4 を当たりにする(表なしの通した行のうち数値が違うを 1 に)", (consistent_b4_zero_to_one, (u"verdict", u"lines"))),
    (u"C3  UM1-B3 を外れにする(表つきの通した行のうち数値が違うを 1 に)", (consistent_b3_one, (u"verdict", u"lines"))),
    (u"C4  UM1-A0 を外れにする(貸借が合わない伝票を 1 に)", (consistent_a0_one, (u"verdict", u"lines"))),
    (u"C5  UM1-A1 を外れにする(関係が成り立つを 14 に。指定ごとの和は合ったまま)", (consistent_a1_fourteen, (u"verdict", u"lines"))),
    (u"C6  UM1-A2 を外れにする(行が在る科目を 0 に)", (consistent_a2_zero, (u"verdict", u"lines"))),
    (u"C7  UM1-A3 を外れにする(表つきの通すを 79 に)", (consistent_a3_low, (u"verdict", u"lines"))),
    (u"C8  UM1-A7 を外れにする(正解と違う行を 9 に)", (consistent_a7_low, (u"verdict", u"lines"))),
    (u"C9  UM1-B7 を外れにする(席が無いと書いたを 26 に)", (consistent_b7_low, (u"verdict", u"lines"))),
    (u"C10 UM1-B8 を外れにする(束が K0 で断られた数を 1 に)", (consistent_b8_one, (u"verdict", u"lines"))),
    (u"C11 UM1-A5 を外れにする(表なしが通したを 94 に)", (consistent_a5_one_stopped, (u"verdict", u"lines"))),
    (u"C12 UM1-A6 を外れにする(表なしが通したを 1 に)", (consistent_a6_one_passed, (u"verdict", u"lines"))),
    (u"C13 UM1-B1 を外れにする(正解どおりを 全部と id ごとと指定ごとで 337 に。和は合ったまま)",
     (lambda c: inc(inc(inc(c, (K_B, u"全部", u"正解どおり"), -105), (K_B, u"指定ごと", u"S1", u"正解どおり"), -90), (K_B, u"id ごと", u"c01", u"正解どおり"), -15) and c, (u"verdict", u"lines", u"recount"))),
    (u"C14 UM1-B5 を外れにする(c08 の正解どおりを 7 に)", (lambda c: setp(c, (K_B, u"c08", u"正解どおり"), 7), (u"verdict", u"lines", u"recount"))),
    (u"C15 UM1-B6 を外れにする(ずらした指定の c26 の正解どおりを 4 に)", (lambda c: setp(c, (K_B, u"ずらした指定の c26", u"正解どおり"), 4), (u"verdict", u"lines"))),
    (u"D1  頭の「予測 2 本は外れ」を「予測 1 本は外れ」に", (lambda c: rep(c, u"予測 2 本は外れ", u"予測 1 本は外れ"), (u"verdict", u"lines"))),
    (u"D2  頭の「当たり 14・外れ 2」を「当たり 15・外れ 1」に", (lambda c: rep(c, u"当たり 14・外れ 2", u"当たり 15・外れ 1", count=2), (u"verdict", u"lines"))),
    (u"D3  §1 の UM1-A4 の「外れ」を「当たり」に", (lambda c: rep(c, u"のうち通した 65(N2 4・N3 10・N7 51) | 外れ |", u"のうち通した 65(N2 4・N3 10・N7 51) | 当たり |"), (u"verdict", u"lines"))),
    (u"D4  §1 の UM1-B4 の「外れ」を「当たり」に", (lambda c: rep(c, u"のうち数値が違う 0 | 外れ |", u"のうち数値が違う 0 | 当たり |"), (u"verdict", u"lines"))),
    (u"D5  頭の「UM1-A4 の外れ」の見出しを消す", (lambda c: rep(c, u"**UM1-A4 の外れ: 表つきの検査が通した変異が在る。**", u""), (u"lines", u"head"))),
    (u"D6  頭の「UM1-B4 の外れ」の行を消す", (lambda c: drop_line(c, u"UM1-B4 の外れ: 席が数値を 1 つも誤らなかった"), (u"lines", u"head"))),
    (u"D7  「「実物の会計の素材で動く」…」の行を肯定にする", (lambda c: rep(c, u"**言えないこと**: 「実物の会計の素材で動く」", u"**できること**: 実物の会計の素材で動く。「"), (u"affirm", u"lines", u"head"))),
    (u"D8  §5 に (vii) の候補を足す", (lambda c: setattr(c, "doc", c.doc.rstrip(u"\n") + u"\n- (vii) 新しい候補。\n") or c, (u"sec5", u"lines"))),
    (u"D9  §5 の (iv) の字を替える", (lambda c: rep(c, u"- (iv) この便の材料から資料の生成まで", u"- (iv) 変えた字"), (u"sec5", u"lines"))),
    (u"D10 §5 の (iii) を落とす", (lambda c: setattr(c, "doc", u"\n".join(l for l in c.doc.split(u"\n") if not l.startswith(u"- (iii)"))) or c, (u"sec5", u"lines"))),
    (u"D11 §5 の (vi) を落とす", (lambda c: setattr(c, "doc", u"\n".join(l for l in c.doc.split(u"\n") if not l.startswith(u"- (vi)"))) or c, (u"sec5", u"lines"))),
    (u"D12 限界の行(素材は作り物)を消す", (lambda c: drop_line(c, u"他人が公開した作り物の会社 1 社の帳簿"), (u"head", u"lines"))),
    (u"D13 限界の行(席は同じ種類の AI の席)を消す", (lambda c: drop_line(c, u"同じ種類の AI の席(この PC の Claude Code の subagent)"), (u"head", u"lines"))),
    (u"D14 汚れの行から「結果の門は記録に縛らない」を消す", (lambda c: rep(c, u"記録に欄は無く、結果の門は記録に縛らない。判定は", u"記録に欄は無い。判定は"), (u"head", u"lines"))),
    (u"D15 文書の commit の字 29f192e0 を 1 字替える", (lambda c: rep(c, u"29f192e0", u"29f192e1", count=2), (u"commits", u"lines"))),
    (u"D16 文書に知らない commit の字を足す", (lambda c: rep(c, u"費用は 0。", u"費用は 0。(commit deadbeef)", count=1), (u"commits", u"lines"))),
    (u"D17 文書に禁止語を足す", (lambda c: rep(c, u"費用は 0。", u"費用は 0。精度は高い。"), (u"forbidden", u"lines"))),
    (u"D18 文書に docID の形を足す", (lambda c: rep(c, u"費用は 0。", u"費用は 0。S100AAAA。"), (u"forbidden", u"lines"))),
    (u"D19 文書に日付を足す", (lambda c: rep(c, u"費用は 0。", u"費用は 0。(2025-01-01)"), (u"forbidden", u"lines"))),
    (u"D20 文書に漢数字の数を足す", (lambda c: rep(c, u"費用は 0。", u"費用は 0。(二百十)"), (u"forbidden", u"lines"))),
    (u"D21 文書に素材の字を足す", (lambda c: rep(c, u"費用は 0。", u"費用は 0。Operating Revenue。"), (u"forbidden", u"lines"))),
    (u"D22 §3 の「記録に縛らず、字で留めるだけ」を消す", (lambda c: rep(c, u"出どころを書く。結果の門は記録に縛らず、字で留めるだけ)", u"出どころを書く)"), (u"sec3", u"lines"))),
    (u"D23 §3 の「確かめていないこと」を消す", (lambda c: rep(c, u"**確かめていないこと:** 変異と A5・A6 は数え直していない。全体の suite は未実行。", u""), (u"sec3", u"lines"))),
    (u"D24 §2 の表の N7 の表つきが通したを替える", (lambda c: rep(c, u"| 51 | 55 |", u"| 0 | 55 |"), (u"lines",))),
    (u"D25 §4 の封の門の試験の数を替える", (lambda c: rep(c, u"の試験は 113 本", u"の試験は 114 本"), (u"lines",))),
    (u"D26 「全体の suite は…走らせていない」を消す", (lambda c: drop_line(c, u"走らせていない"), (u"lines",))),
    (u"D27 頭の外れ 2 本の名を入れ替える(UM1-A4 と UM1-B4 → UM1-A4 と UM1-B3)", (lambda c: rep(c, u"外れは UM1-A4 と UM1-B4。", u"外れは UM1-A4 と UM1-B3。"), (u"verdict", u"lines"))),
    (u"D28 「欄の読み方」の行(止めた規則は当たりの数)を消す", (lambda c: drop_line(c, u"「止めた規則」は当たりの数で、行の数ではない"), (u"lines",))),
    (u"D29 「3 席が 3 つとも同じ行」の分母を替える", (lambda c: rep(c, u"3 席が 3 つとも同じ行: 142 / 150。", u"3 席が 3 つとも同じ行: 142 / 450。"), (u"lines",))),
    (u"D30 汚れを除くの列の数を替える", (lambda c: rep(c, u"| 表つき: 正しい材料を止めた | 157 | 148 |", u"| 表つき: 正しい材料を止めた | 157 | 150 |"), (u"lines",))),
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
              (u"在る", u"無い"), (u"無い", u"在る"), (u"正解どおり", u"正解と違う"), (u"言えない", u"言える"), (u"読まない", u"読む"), (u"だけ", u"も"), (u"表なし", u"表つき"),
              (u"表つき", u"表なし"), (u"暦年", u"ずらした"), (u"汚れ", u"取り直し"))


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
    yield u"候補を足す", doc.rstrip(u"\n") + u"\n- (vii) 新しい候補。\n"
    ls = doc.split(u"\n")
    pat = r"^- \((?:i|ii|iii|iv|v|vi)\) "
    for k, l in enumerate(ls):
        if re.match(pat, l):
            yield u"候補を落とす @%d" % (k + 1), u"\n".join(ls[:k] + ls[k + 1:])
    idx = [k for k, l in enumerate(ls) if re.match(pat, l)]
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
        self.assertEqual([u"UM1-A4", u"UM1-B4"], [i for i, v in j.items() if v is False])
        self.assertEqual(14, len([1 for v in j.values() if v is True]))

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
        self.assertEqual(113, self.c.seal_gate_tests)

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
            SG.make_repo([("seal", {seal: u"s"}), ("rec", {PREFIX + RECORD_REL: u"{}"}), ("impl", {PREFIX + REF_REL: u"x"})], tmp)
            short = subprocess.run(["git", "-C", tmp, "log", "--format=%h", "--", seal], stdout=subprocess.PIPE).stdout.decode().strip()
            got = PR.order_problems(tmp, PREFIX, SEAL_REL, short, [REF_REL], [RECORD_REL])
            self.assertNotEqual([], list(got))

    def test_f_5_the_history_check_is_red_for_a_file_added_twice_or_changed_after(self):
        with tempfile.TemporaryDirectory() as tmp:
            SG.make_repo([("a", {PREFIX + "x": u"1"}), ("b", {PREFIX + "x": u"2"})], tmp)
            added = PR.added_commits(tmp, PREFIX + "x")
            self.assertEqual(1, len(added))
            rc, allc = PR.git_in(tmp, "log", "--format=%H", "--", PREFIX + "x")
            self.assertEqual(2, len([x for x in allc.split() if x]))

    def test_g_1_the_record_has_the_claims_the_document_leans_on(self):
        rec = self.c.rec
        self.assertEqual(0, rec[K_B][u"席の取り直しの数"])
        self.assertEqual(1, rec[K_B][u"汚れた席の数"])
        self.assertEqual(15, rec[K_B][u"席の数"])
        self.assertEqual(u"UM1", rec[u"便"])


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
        for fn in (consistent_a4_zero, consistent_b4_zero_to_one, consistent_b3_one, consistent_a0_one, consistent_a1_fourteen, consistent_a2_zero, consistent_a3_low,
                   consistent_a7_low, consistent_b7_low, consistent_b8_one, consistent_a5_one_stopped, consistent_a6_one_passed):
            c = self.base.copy()
            fn(c)
            if fn is consistent_b8_one:
                continue                                # 断りの数は段 B の行の数と合わせる別の検査が赤にする(下で確かめる)
            self.assertEqual([], recount_problems(c), fn.__name__)
            self.assertIn(u"lines", red_set(c), fn.__name__)
        c = self.base.copy()
        consistent_b8_one(c)
        self.assertNotEqual([], recount_problems(c))
        self.assertIn(u"verdict", red_set(c))

    def test_h_4_every_check_a_mutation_names_exists(self):
        names = set(k for _n, (_f, ex) in MUTATIONS.items() for k in ex)
        self.assertTrue(names <= set(CHECKS), names - set(CHECKS))

    def test_h_5_the_judgement_edges_at_the_seal_bounds(self):
        j0 = judge(self.base.rec)
        self.assertTrue(j0[u"UM1-A3"] and j0[u"UM1-A7"] and j0[u"UM1-B1"] and j0[u"UM1-B5"] and j0[u"UM1-B6"] and j0[u"UM1-B7"] and j0[u"UM1-A2"])

        def with_rec(fn):
            d = self.base.copy()
            fn(d.rec)
            return judge(d.rec)

        def passes(n):
            def f(rec):
                t = rec[K_A][u"検査の結果"][u"表つき"][u"判定"]
                t[u"通す"] = n
                t[u"止める"] = 150 - n
            return f
        for n, want in ((80, True), (79, False), (120, True), (121, False)):
            self.assertEqual(want, with_rec(passes(n))[u"UM1-A3"], n)

        def diff(n):
            def f(rec):
                rec[K_A][u"規則の持ち越し"][u"正解と違う行"] = n
            return f
        for n, want in ((10, True), (9, False), (40, True), (41, False)):
            self.assertEqual(want, with_rec(diff(n))[u"UM1-A7"], n)

        def moved(n):
            def f(rec):
                rec[K_A][u"素材の全体"][u"うち指定の間に行が在る科目"] = n
            return f
        for n, want in ((1, True), (0, False), (6, True), (7, False)):
            self.assertEqual(want, with_rec(moved(n))[u"UM1-A2"], n)

        def idle(n):
            def f(rec):
                rec[K_A][u"素材の全体"][u"開発の年に動きが無かった科目"] = n
            return f
        self.assertIsNone(with_rec(idle(33))[u"UM1-A2"])

        def right(n):
            def f(rec):
                rec[K_B][u"全部"][u"正解どおり"] = n
            return f
        for n, want in ((338, True), (337, False)):
            self.assertEqual(want, with_rec(right(n))[u"UM1-B1"], n)

        def field(path, v):
            def f(rec):
                node = rec
                for k in path[:-1]:
                    node = node[k]
                node[path[-1]] = v
            return f
        for key, path, ok_val, ng_val in ((u"UM1-B5", (K_B, u"c08", u"正解どおり"), 8, 7), (u"UM1-B6", (K_B, u"ずらした指定の c26", u"正解どおり"), 5, 4),
                                          (u"UM1-B7", (K_B, u"c28・c29", u"席が無いと書いた"), 27, 26), (u"UM1-B8", (K_B, u"束が K0 で断られた数"), 0, 1),
                                          (u"UM1-B3", (K_B, u"全部", u"表つき", u"通した行のうち数値が違う"), 0, 1), (u"UM1-A0", (K_A, u"素材の全体", u"貸借が合わない伝票"), 0, 1)):
            self.assertTrue(with_rec(field(path, ok_val))[key], (key, ok_val))
            self.assertFalse(with_rec(field(path, ng_val))[key], (key, ng_val))
        self.assertTrue(with_rec(field((K_B, u"全部", u"表なし", u"通した行のうち数値が違う"), 1))[u"UM1-B4"])
        self.assertFalse(with_rec(field((K_B, u"全部", u"表なし", u"通した行のうち数値が違う"), 0))[u"UM1-B4"])
        # B2 は率の比べ(同じ率は外れ)
        d = self.base.copy()
        d.rec[K_B][u"ずらした指定の率"][u"正解どおり"] = 267
        self.assertFalse(judge(d.rec)[u"UM1-B2"])
        d.rec[K_B][u"ずらした指定の率"][u"正解どおり"] = 266
        self.assertTrue(judge(d.rec)[u"UM1-B2"])
        # A4 は 1 つでも通せば外れ・A5 は 1 つでも止めれば外れ・A6 は 1 つでも通せば外れ
        d = self.base.copy()
        consistent_a4_zero(d)
        self.assertTrue(judge(d.rec)[u"UM1-A4"])
        d.rec[K_A][u"変異"][u"N12"][u"表つきが通した"] = 1
        self.assertFalse(judge(d.rec)[u"UM1-A4"])
        self.assertFalse(with_rec(field((K_A, u"A5", u"表なしが通した"), 94))[u"UM1-A5"])
        self.assertFalse(with_rec(field((K_A, u"A6", u"表なしが通した"), 1))[u"UM1-A6"])

    def test_h_6_the_a4_judgement_uses_the_twelve_mutations_only(self):
        d = self.base.copy()
        consistent_a4_zero(d)
        d.rec[K_A][u"A5"][u"表なしが通した"] = d.rec[K_A][u"A5"][u"作れた"]
        self.assertTrue(judge(d.rec)[u"UM1-A4"])
        self.assertEqual(65, msum(self.base.rec, u"表つきが通した"))
        self.assertEqual(330, msum(self.base.rec, u"表なしが通した"))
        self.assertEqual(1344, msum(self.base.rec, u"作れた"))
        self.assertEqual(78, msum(self.base.rec, u"数値が元と同じ"))

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
