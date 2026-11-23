# -*- coding: utf-8 -*-
u"""結果の門: 封 docs/UNIVERSAL_THROUGH_SEAL_2026-11-23.md(9ff5af9e)の結果の文書 docs/UNIVERSAL_THROUGH_RESULT_2026-11-24.md(便 UM2)。

封の門 ``test_universal_through_seal.py`` の次の段。**追跡されている記録・script・定義表・指示書・封・封の門・結果の文書と git の履歴だけを読む**
(席の出力・素材・書類の置き場は読まない・通信しない・鍵は読まない・API は呼ばない)。
検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``Ctx`` の写しに当てる(木の file は変異させない。前後の sha256 を見る)。

 a sha256(字で留める)。封・brief・script 2 本・定義表 2 つ・指示書・封の門・記録
 b 記録の数え直し: 足し算・分母・恒等式を、**検査の script の関数を使わずに**数え直す(4 つの枠・段 1 の結果・段 2 の持ち越し・段 3 の定義表の行 = 数 + 確認待ち + 無い・変異)
 c 予測 UM2-S1〜V2 の当たり外れを、封の字の境と記録から決め直す(``judge``)。集計の script の judge の出力と同じことを見る。封の予測の表の行が封にそのまま在ることを字で見る
 d 結果の文書の全部の行を、記録と字から組み直し(``render``)、文書と行ごとに照らす。数・向きの語・表のセル・限界の文・次の便の候補は全部これで縛る。
   **§3(記録に欄の無い読み)の数は、記録に縛れないので字で留めるだけ**(門の中に同じ字が在る。記録に縛るのではない)
 e 文書の頭の負けと限界・次の便の候補が封 §6 の (i)〜(vi) だけ・言えないことを肯定で書かない・禁止語・docID と EDINET コードの形
 f 封・script・定義表・指示書・封の門・記録が commit の blob と 1 byte も違わない・engine は封の commit から 0 行・順序(封 → script など → 記録 → この文書と門)・
   限界の文の出どころ(検査と集計の script で確かめる)
 g 集計の script の「定義表の行で重複を除く」所(同じ id が資料に複数回出る・数 > 確認待ち > 無い の優先・定義表に無い id が行に入らない)を、作り物の標本で縛る。
   重複を除く所を外す変異(集計の script の字を替えて読み込む)で赤になる
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
import types
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


MY_MODULE_NAME = "um2_seal_gate_for_result_gate"
SG = load_module("tests/measure/test_universal_through_seal.py", MY_MODULE_NAME)               # 封の門の部品。門としては走らせない
CHK, TAL, PR = SG.CHK, SG.TAL, SG.PR
OVERWRITTEN = sorted(k for k, v in _BEFORE_MODULES.items() if sys.modules.get(k) is not v)

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
CHECK_REL, TALLY_REL, DEF_RELS = SG.CHECK_REL, SG.TALLY_REL, SG.DEF_RELS
INSTR_REL, BRIEF_REL = SG.INSTRUCTION_REL, SG.BRIEF_REL
SEAL_GATE_REL = SG.GATE_REL
RECORD_REL = SG.RECORD_REL
GATE_REL = "tests/measure/test_universal_through_result.py"
DOC_REL = "docs/UNIVERSAL_THROUGH_RESULT_2026-11-24.md"
BRIEF_COMMIT = "f2b35597"                        # 素材を作る席への頼みの紙を足した commit
IMPL_COMMIT = "7eaa548e"                         # check・tally・指示書・封の門を足した commit
RECORD_COMMIT = "a0b7ab6f"                       # 記録を足し、tally と封の門を直した commit
DEF_COMMIT = "a2326934"                          # 便 UM0 の定義表を足した commit(そのまま使う)
DOC_COMMITS = (SEAL_COMMIT_SHORT, BRIEF_COMMIT, IMPL_COMMIT, RECORD_COMMIT)
#: file → (足した commit, 最後の commit)
BLOB_AT = od([
    (SEAL_REL, (SEAL_COMMIT_SHORT, SEAL_COMMIT_SHORT)),
    (BRIEF_REL, (BRIEF_COMMIT, BRIEF_COMMIT)),
    (CHECK_REL, (IMPL_COMMIT, IMPL_COMMIT)),
    (INSTR_REL, (IMPL_COMMIT, IMPL_COMMIT)),
    (TALLY_REL, (IMPL_COMMIT, RECORD_COMMIT)),
    (SEAL_GATE_REL, (IMPL_COMMIT, RECORD_COMMIT)),
    (RECORD_REL, (RECORD_COMMIT, RECORD_COMMIT)),
])
SHA_PIN = od([
    (SEAL_REL, "bcbfd4a5447d30e8f8ae818bd3dfe6e08d8cfe76457257e7417484d8ea0a4d98"),
    (BRIEF_REL, "09b7f9fd79d1c21c966cd0ec2760588483aeefc091ed9d2afcfdf02254cdaa95"),
    (CHECK_REL, "35f16c6f75f96ca3e2b6c28bde497efba74d57a881dd5e081ce612f6e120dbbf"),
    (TALLY_REL, "81e8530500e69081e05d09289fdc6d457b24ec7da9ab7714f8317d875f66b85f"),
    (INSTR_REL, "03d1c4545ab80a4f1fa18de01a5a4b24c28e16756330007489d4758469dd9bb8"),
    (SEAL_GATE_REL, "6ed269ebaaaec7406f1e175c793579ce8e7b4ddfa9e5a39d51cc3f4dcd86d143"),
    (RECORD_REL, "f9f526eaa3638c3e9248446c1821785bfd95c05a72f10372e2f0cbb1f5d56a92"),
    (DEF_RELS[0], "fd0e878092d106a93c0a65422c664006ac8cb7cf6428224290dab2a80e31e84b"),
    (DEF_RELS[1], "8c8bd2e2a56e159e51ba5371cd1127783b7280db9a9b08da0d627c8d2e54d39f")])


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
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        return [u"例外: %s" % type(exc).__name__]


def pct(n, d):
    u"""n/d の % を小数第 1 位まで四捨五入(0.5 は上げる)した字。整数で。"""
    return u"%.1f" % (((2000 * n + d) // (2 * d)) / 10.0)


# ================================================================== 字で決めた形
TAGS = (u"期1・A", u"期1・B", u"期2・A", u"期2・B")
PRED_IDS = (u"UM2-S1", u"UM2-S2", u"UM2-P1", u"UM2-P2", u"UM2-P3", u"UM2-P4", u"UM2-P5", u"UM2-Q1", u"UM2-Q2", u"UM2-Q3", u"UM2-D1", u"UM2-D2", u"UM2-E1", u"UM2-V1", u"UM2-V2")
MUT_CODES = (u"M1", u"M2", u"M4", u"M8", u"V1", u"V2", u"V3", u"V4", u"V5", u"V6", u"D1", u"D4")
TOP_KEYS = (u"会社の数", u"数", u"変異", u"会社ごと")
#: 封 §6 の次の便の候補(封にそのまま在る。結果の文書はここに無い候補を足さない)
SEAL_CANDIDATE_COUNT = 6

# 文書が肯定で書いてはいけない言い方(出た文は「言えない」か「読まない」を持つ)
AFFIRM_PHRASES = (u"実物の会計の素材で動く", u"実物の会計ソフトの出力で動く", u"会社の AI がこの型で書ける", u"誤りが無くなる", u"人の確かめが要らない", u"人が確かめる手間が減る",
                  u"開示の書類が作れる", u"専用の道具が要らない", u"既存の道具に代わる", u"席の誤りを止める", u"AI が材料を作れる")
FORBIDDEN_WORDS = (u"精度", u"LLM より正確", u"世界で 1 社", u"金額", u"契約", u"税", u"USD", u"保証")
DOCID_FORM = re.compile(r"(?<![0-9A-Za-z])S[0-9A-Z]{7}(?![0-9A-Za-z])")
ECODE_FORM = re.compile(r"(?<![0-9A-Za-z])E\d{5}(?![0-9A-Za-z])")
DATE_FORM = re.compile(r"(?<![0-9])(?:19|20)\d{2}[-/.]\d{1,2}[-/.]\d{1,2}(?![0-9])|(?<![0-9])(?:19|20)\d{2}年\d{1,2}月")

#: 封 §3 の V1・V2 の行(封の予測の表。封の門の写しには無い)
SEAL_V_ROWS = (
    u"| UM2-V1 | `表の行の和` の変異 V2・V3・V6 のうち、関係に入らない行(a02・a05・a08・a09・a10・a16・a30・b01 など、R1〜R3 のどれにも出ない id)で作れたものは、検査が全部通す | 1 つでも止める |",
    u"| UM2-V2 | 変異 V1 と V4 は、作れたもののうち検査が通すもの 0 | 1 以上 |",
)


# ================================================================== 写し
class Ctx(object):
    u"""検査が見る写し。変異はこの写しを変える(木の file は変えない)。"""

    def __init__(self):
        self.rec = json.loads(read(RECORD_REL), object_pairs_hook=od)
        self.doc = read(DOC_REL)
        self.seal = read(SEAL_REL)
        self.defa = json.loads(read(DEF_RELS[0]), object_pairs_hook=od)
        self.defb = json.loads(read(DEF_RELS[1]), object_pairs_hook=od)
        self.shas = od((rel, sha_file(rel)) for rel in SHA_PIN)
        self.msg_impl = git_message(IMPL_COMMIT)
        self.msg_record = git_message(RECORD_COMMIT)
        self.seal_gate_tests = len(re.findall(r"(?m)^    def test_", read(SEAL_GATE_REL)))
        self._cache = None

    def copy(self):
        c = Ctx.__new__(Ctx)
        c.rec = copy.deepcopy(self.rec)
        c.doc, c.seal = self.doc, self.seal
        c.defa, c.defb = self.defa, self.defb
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
def N(rec, key):
    return rec[u"数"][key]


def M(rec, code, key):
    return rec[u"変異"][code].get(key, 0)


def tag_sum(rec, prefix):
    return sum(N(rec, u"%s:%s" % (prefix, t)) for t in TAGS)


def seal_pred_rows(seal):
    u"""封の予測の表の行 → {id: (予測, 外れ方)}。"""
    out = od()
    for ln in seal.splitlines():
        m = re.match(r"^\| (UM2-[A-Z][0-9]) \| (.*) \| (.*) \|$", ln)
        if m:
            out[m.group(1)] = (m.group(2), m.group(3))
    return out


def seal_candidates(seal):
    i = seal.index(u"## §6")
    return [l for l in seal[i:].splitlines() if re.match(r"^- \((?:i|ii|iii|iv|v|vi|vii)\) ", l)]


def judge(rec):
    u"""封 §3 の 15 本の当たり外れ({id: True=当たり/False=外れ/None=記録では決まらない})。境は封の字。集計の script の judge を使わずに決める。"""
    out = od()
    out[u"UM2-S1"] = N(rec, u"関係の本数") == 24 and N(rec, u"関係が成り立つ本数") >= 22
    out[u"UM2-S2"] = 4 <= N(rec, u"正解が null の行:期1") <= 30
    out[u"UM2-P1"] = N(rec, u"段 1:行の数") == 124 and N(rec, u"段 1:席の答えが正解と同じ") >= 93
    present = N(rec, u"段 1:席が在ると書いた行")
    out[u"UM2-P2"] = (10 * N(rec, u"段 1:出どころの種類:表の行の和") >= 3 * present) if present else None
    out[u"UM2-P3"] = N(rec, u"段 1:通したが数値が違う") >= 1
    out[u"UM2-P4"] = N(rec, u"段 1:K3 で止まった行") >= 10
    out[u"UM2-P5"] = N(rec, u"束が K0 で断られた束") == 0 and N(rec, u"段 2:束が K0 で断られた束") == 0
    marks = N(rec, u"段 2:確かめた取り方の行")
    out[u"UM2-Q1"] = (5 * N(rec, u"段 2:持ち越した行") >= 4 * marks) if marks else None
    out[u"UM2-Q2"] = N(rec, u"段 2:持ち越して通したが数値が違う") == 0
    out[u"UM2-Q3"] = N(rec, u"段 2:K11 で止めた社") >= 1
    out[u"UM2-D1"] = tag_sum(rec, u"段 3:資料の検査を通した") >= 13
    out[u"UM2-D2"] = 100 * N(rec, u"段 3:A の 2 期目の資料で数が出ている行") >= 60 * (33 * 4)
    out[u"UM2-E1"] = N(rec, u"通し:期1・期2とも") >= 3
    made = sum(M(rec, k, u"作れた:関係に入らない") for k in (u"V2", u"V3", u"V6"))
    passed = sum(M(rec, k, u"通した:関係に入らない") for k in (u"V2", u"V3", u"V6"))
    out[u"UM2-V1"] = (passed == made) if made else None
    made2 = sum(M(rec, k, u"作れた") for k in (u"V1", u"V4"))
    out[u"UM2-V2"] = (sum(M(rec, k, u"通した") for k in (u"V1", u"V4")) == 0) if made2 else None
    return out


def verdict_word(v):
    return {True: u"当たり", False: u"外れ", None: u"記録では決まらない"}[v]


# ================================================================== 文書を記録と字から組み直す
def measured(rec):
    u"""§1 の表の実測の列(記録の数だけから組む)。"""
    n = lambda k: N(rec, k)                                   # noqa: E731
    present = n(u"段 1:席が在ると書いた行")
    docs = tag_sum(rec, u"段 3:資料の検査を通した")
    made_in = sum(M(rec, k, u"作れた:関係に入らない") for k in (u"V2", u"V3", u"V6"))
    pass_in = sum(M(rec, k, u"通した:関係に入らない") for k in (u"V2", u"V3", u"V6"))
    return od([
        (u"UM2-S1", u"関係が成り立つ %d / %d 本" % (n(u"関係が成り立つ本数"), n(u"関係の本数"))),
        (u"UM2-S2", u"正解が null の行 期1 %d・期2 %d" % (n(u"正解が null の行:期1"), n(u"正解が null の行:期2"))),
        (u"UM2-P1", u"席の答えが正解と同じ %d / %d = %s%%" % (n(u"段 1:席の答えが正解と同じ"), n(u"段 1:行の数"), pct(n(u"段 1:席の答えが正解と同じ"), n(u"段 1:行の数")))),
        (u"UM2-P2", u"表の行の和で書いた %d / 在ると書いた %d = %s%%" % (n(u"段 1:出どころの種類:表の行の和"), present, pct(n(u"段 1:出どころの種類:表の行の和"), present))),
        (u"UM2-P3", u"通したが数値が違う %d(別に、正解と違う×通した %d は下の注)" % (n(u"段 1:通したが数値が違う"), n(u"段 1:4 つの枠:正解と違う×通した"))),
        (u"UM2-P4", u"K3 で止まった行 %d" % n(u"段 1:K3 で止まった行")),
        (u"UM2-P5", u"K0 で断られた束 1 期目 %d・2 期目 %d" % (n(u"束が K0 で断られた束"), n(u"段 2:束が K0 で断られた束"))),
        (u"UM2-Q1", u"持ち越した %d / 確かめた取り方 %d = %s%%" % (n(u"段 2:持ち越した行"), n(u"段 2:確かめた取り方の行"), pct(n(u"段 2:持ち越した行"), n(u"段 2:確かめた取り方の行")))),
        (u"UM2-Q2", u"持ち越して通したが数値が違う %d(通した %d のうち)" % (n(u"段 2:持ち越して通したが数値が違う"), n(u"段 2:持ち越して検査を通った行"))),
        (u"UM2-Q3", u"K11 で止めた社 %d(止めた行 %d)" % (n(u"段 2:K11 で止めた社"), n(u"段 2:K11 で止めた行"))),
        (u"UM2-D1", u"資料の検査を通した %d / 16 本" % docs),
        (u"UM2-D2", u"数が出ている定義表の行 %d / 132 = %s%%" % (n(u"段 3:A の 2 期目の資料で数が出ている行"), pct(n(u"段 3:A の 2 期目の資料で数が出ている行"), 132))),
        (u"UM2-E1", u"期1・期2とも通った社 %d / %d" % (n(u"通し:期1・期2とも"), rec[u"会社の数"])),
        (u"UM2-V1", u"V2・V3・V6 の関係に入らない行 作れた %d・通した %d" % (made_in, pass_in)),
        (u"UM2-V2", u"V1・V4 の作れた %d・通した %d" % (sum(M(rec, k, u"作れた") for k in (u"V1", u"V4")), sum(M(rec, k, u"通した") for k in (u"V1", u"V4")))),
    ])


def num_group_rows(rec, prefix_test):
    return [(k, v) for k, v in rec[u"数"].items() if prefix_test(k)]


def render(c):
    rec = c.rec
    n = lambda k: N(rec, k)                                   # noqa: E731
    j = judge(rec)
    hits = [i for i, v in j.items() if v is True]
    misses = [i for i, v in j.items() if v is False]
    pred = seal_pred_rows(c.seal)
    cands = seal_candidates(c.seal)
    meas = measured(rec)
    n_co = rec[u"会社の数"]
    docs = tag_sum(rec, u"段 3:資料の検査を通した")
    human = tag_sum(rec, u"段 3:人が読む版が組めた")
    human_ok = tag_sum(rec, u"段 3:人が読む版の検査を通した")
    rows124 = n(u"段 1:行の数")
    d2_num, d2_occ = n(u"段 3:A の 2 期目の資料で数が出ている行"), n(u"段 3:A の 2 期目の資料で数の札の出現の数")
    d2_rows = n(u"段 3:定義表の行:期2・A")
    word_occ = sum(n(u"段 3:%s:%s" % (k, t)) for k in (u"確認待ちの札の出現の数", u"無いの札の出現の数") for t in TAGS)
    num_occ = tag_sum(rec, u"段 3:数の札の出現の数")
    V = lambda code, key: M(rec, code, key)                   # noqa: E731
    L = []
    w = L.append
    w(u"# 結果: 便 UM2 ― 別の席が形を決めた架空の会計ソフトの file 一式から、資料の指定から人が読む版の資料までの 7 段を 2 期ぶん通した ― 作り物の素材 %d 社とこの PC の席で数えた ― 2026-11-24" % n_co)
    w(u"")
    w(u"封 `%s`(commit %s)。素材を作る席への頼みの紙 `%s`(commit %s)。確かめる側の script `%s`・答えを知っている側の script `%s`・指示書 `%s`・封の門 `%s` は commit %s"
      u"(独立監査 REVISE(門の穴)→ 直し → REVISE(門の穴 5 つ)→ 直し → GO)。記録 `%s` と、集計の script・封の門の直し 2 点は commit %s(最初の記録は独立監査 REVISE で、直しの後に GO)。"
      u"定義表は便 UM0 の `%s`・`%s` をそのまま使った(0 行)。費用は 0。API は呼んでいない。席はこの PC の subagent。engine(`core/`・`adapters/`)は 0 行。"
      % (SEAL_REL, SEAL_COMMIT_SHORT, BRIEF_REL, BRIEF_COMMIT, CHECK_REL, TALLY_REL, INSTR_REL, SEAL_GATE_REL, IMPL_COMMIT, RECORD_REL, RECORD_COMMIT, DEF_RELS[0], DEF_RELS[1]))
    w(u"")
    w(u"この文書の §1・§2 の数は全部、記録から 1 つずつ読んだもの(結果の門が、記録の数と字で同じことを見る。§2 は記録の数の全部を載せる)。"
      u"§3 は記録に欄の無い読みで、出どころ(司令塔の数え・監査の席の読み・実装担当が見たもの)を書く。結果の門は §3 の数を記録に縛らず、字で留めるだけ。")
    w(u"")
    w(u"台帳の番号(L-104・D-81・P-89)と試験の数は、別の枝に在る便 UM1 の結果と当たる。枝を寄せる時に、番号と試験の数を直す。")
    w(u"")
    w(u"**先に負けと限界を書く。**")
    w(u"")
    w(u"- **通し: 本番の %d 社 × 2 期とも、段 1〜7 が資料の生成まで通った。** 1 期目を通った社 %d・2 期目を通った社 %d・両方を通った社 %d。"
      u"資料の検査を通した資料は %d 本(A・B × 2 期 × %d 社 = 16 本のうち)・人が読む版が組めたのは %d 本・人が読む版の検査を通したのは %d 本。"
      u"素材は作り物(別の席が作った架空の会計ソフトの出力。%d 社の合計で 1 期目 %d file(CSV %d・xlsx %d)・2 期目 %d file(CSV %d・xlsx %d))。"
      u"通ったのは作り物の素材でのことで、実物の会計ソフトの出力では測っていない。"
      % (n_co, n(u"通し:期1"), n(u"通し:期2"), n(u"通し:期1・期2とも"), docs, n_co, human, human_ok, n_co,
         n(u"素材の file の数:期1"), n(u"素材の file の形式:CSV:期1"), n(u"素材の file の形式:xlsx:期1"),
         n(u"素材の file の数:期2"), n(u"素材の file の形式:CSV:期2"), n(u"素材の file の形式:xlsx:期2")))
    w(u"- **予測 %d 本は 当たり %d・外れ %d。** 外れは %s。判定は封の「外れ方」の字で 1 本ずつ決め直した(§1 の表。結果の門が封の字の境から決め直し、集計の script の judge の出力と同じことを見る)。"
      u"封も予測も、結果を見てから書き換えていない。素材も検査も同じ司令塔が決め、予測も封を書いた司令塔が立てた(盲検でない)。"
      % (len(j), len(hits), len(misses), u"・".join(misses)))
    w(u"- **UM2-D2 は外れ(%d / %d = %s%%)。** 当初の集計の script は、分子に札の出現の数(%d)を置いていた。出現の数は同じ id が資料に何度出ても数え、封の分母(定義表の行 %d)と単位が合わない。"
      u"独立監査の指摘で、分子を定義表の行(id の重複を除く)に直した(commit %s の message)。**直す前は %d / %d = %s%% で、当たりと出ていた。これは結果を見た後の直しで、判定は不利な側に動いた。**"
      u"境・予測・封は動かしていない。2 期目の A の資料は、札の出現の数 %d に対し、定義表の行 %d(数が出ている %d・確認待ち %d・無い %d)。"
      u"優先の規則(数 > 確認待ち > 無い。1 つの id が複数の種類に出た時は 1 つにだけ入れる)は、種類をまたぐ id が 0 で、この数には効いていない(§3)。"
      % (d2_num, 132, pct(d2_num, 132), d2_occ, d2_rows, RECORD_COMMIT, d2_occ, 132, pct(d2_occ, 132), d2_occ, d2_rows,
         n(u"段 3:数が出ている定義表の行:期2・A"), n(u"段 3:確認待ちの定義表の行:期2・A"), n(u"段 3:無いの定義表の行:期2・A")))
    w(u"- **一番大きい負けは UM2-Q2。** 2 期目に持ち越して検査を通した %d 行のうち、%d 行の値が正解と違った(封は 0 と予測した。封 §4 の決めで、これを先に書く)。"
      u"1 期目の取り方の条件をそのまま 2 期目に使うと、対象の行を 1 本落とした。K11(新しい値)にも掛からなかった(司令塔の読み。記録に欄は無い。§3)。"
      u"「確かめた取り方」は、1 期目の正解との一致で置いた代用で、人の確かめではない。K11 が止めた %d 行は、%d 社で 1 行ずつ、4 つとも正解と同じ値だった(止めすぎ。実装担当が席の出力と正解を読み直して見た。記録に欄は無い。§3)。"
      u"額と科目の字は書かない。"
      % (n(u"段 2:持ち越して検査を通った行"), n(u"段 2:持ち越して通したが数値が違う"), n(u"段 2:K11 で止めた行"), n(u"段 2:K11 で止めた社")))
    w(u"- **1 期目に止めた %d 行は全部、席の答えが正解どおりだった(正解どおり×止めた %d・正解と違う×止めた %d。席の誤り %d)。** 止めた理由は K4 %d・K3 %d。"
      u"司令塔は 1 行ずつ読んでいない。監査の席の読みは、期の見出しの形を検査が読めないこと・定義表に無い見出し、の 2 つ(どの規則にどれだけ当たるかの対応づけは確かめていない。§3)。"
      u"席の誤りが %d なので、「席の誤りを検査が止める」は測れていない。止めた行は、正解どおりなのに止めた(止めすぎ)側の数である。"
      % (n(u"段 1:検査の結果:止める"), n(u"段 1:4 つの枠:正解どおり×止めた"), n(u"段 1:4 つの枠:正解と違う×止めた"), n(u"段 1:4 つの枠:正解と違う×止めた"),
         n(u"段 1:止めた行の規則:K4"), n(u"段 1:止めた行の規則:K3"), n(u"段 1:4 つの枠:正解と違う×止めた")))
    w(u"- **正解と違う×通した %d。** %d 社とも 1 項目を、席が「無い」と書いた。正解には値が在り、検査は「無いを受ける」として受けた(無いを受ける %d 行)。"
      u"UM2-P3 の定義(通した行のうち数値が違う)には入らず、P3 は %d で外れだが、負けとして書く。席が「無い」と書いた理由は、型の「表の行の和」が行を数えて出す値を書けないこと(監査の席の読み。記録に欄は無い。§3)。"
      % (n(u"段 1:4 つの枠:正解と違う×通した"), n_co, n(u"段 1:検査の結果:無いを受ける"), n(u"段 1:通したが数値が違う")))
    w(u"- **資料は薄い。** 2 期目の A の資料で、数が出ている定義表の行は %d(確認待ち %d・無い %d)。数が出ている行・確認待ち・無いは、期ごと・A・B ごとに §2 に出す"
      u"(数が出ている行 1 期目の A %d・B %d、2 期目の A %d・B %d)。A の人が読む版 8 本は、表が `| … |` の字のまま段落として出る(司令塔が画面で見た・実装担当が html で確かめた。記録に欄は無い。§3)。"
      u"結果を見た後なので、この便では直していない。資料が組めた本数(%d 本)は、確認待ち・無いが多くても組めるので、UM2-D2(数が出ている行の割合)と並べて読む。"
      % (n(u"段 3:数が出ている定義表の行:期2・A"), n(u"段 3:確認待ちの定義表の行:期2・A"), n(u"段 3:無いの定義表の行:期2・A"),
         n(u"段 3:数が出ている定義表の行:期1・A"), n(u"段 3:数が出ている定義表の行:期1・B"), n(u"段 3:数が出ている定義表の行:期2・A"), n(u"段 3:数が出ている定義表の行:期2・B"), docs))
    w(u"- **変異(作れた・通した・止めた)。** M1 %d・%d・%d / M2 %d・%d・%d / M4 %d・%d・%d(作れなかった %d)/ M8 %d・%d・%d / V1 %d・%d・%d / V2 %d・%d・%d / V3 %d・%d・%d / V4 %d・%d・%d / V5 %d・%d・%d / V6 %d・%d・%d / D1 %d・%d・%d / D4 %d・%d・%d。"
      u"M4 は作れなかったが作れたより多い(xlsx で期の読みが要る行だけが対象の script の決め)。"
      % tuple([x for code in (u"M1", u"M2") for x in (V(code, u"作れた"), V(code, u"通した"), V(code, u"止めた"))]
              + [V(u"M4", u"作れた"), V(u"M4", u"通した"), V(u"M4", u"止めた"), V(u"M4", u"作れなかった")]
              + [x for code in (u"M8", u"V1", u"V2", u"V3", u"V4", u"V5", u"V6", u"D1", u"D4") for x in (V(code, u"作れた"), V(code, u"通した"), V(code, u"止めた"))]))
    w(u"- **V2・V3・V6 が通したことの読み。** 封 UM2-V1 は、関係に入らない行の V2・V3・V6 を検査が全部通すと予測した(通した %d / 作れた %d で当たり)。K3(意味)は 1 期目に掛けず、仕訳の行の和の取り方を人が確かめる所は作っていない(封 §1-5・§5)。"
      u"通したのは、検査が意味を見ない所を変異が突いたものである。V6 の関係に入る行 %d は予測の対象の外で、通した理由は 1 行ずつ読んでいない。"
      % (sum(V(k, u"通した:関係に入らない") for k in (u"V2", u"V3", u"V6")), sum(V(k, u"作れた:関係に入らない") for k in (u"V2", u"V3", u"V6")), V(u"V6", u"通した:関係に入る")))
    w(u"- **D4 が通した %d。** 監査の席の読みでは、全部「確認待ち」「無い」の札を消した行(§3)。記録の数では、D4 の作れた %d から D1 の作れた %d を引いた %d が、確認待ち・無いの札の出現の合計 %d と同じ。"
      % (V(u"D4", u"通した"), V(u"D4", u"作れた"), V(u"D1", u"作れた"), V(u"D4", u"作れた") - V(u"D1", u"作れた"), word_occ))
    w(u"- **席。** 材料を書く席 8・資料を書く席 8・取り直し 0(司令塔の数え。記録に欄は無い。§3)。全部同じ種類の subagent で、互いに独立ではない(model の名は書かない)。"
      u"1 社・1 役・1 期につき 1 回。汚れ(席が folder の外を読み書きした件など)は §3 に別に数える。席ごとの読みは揃わない(§3)。")
    w(u"- **実装の限界。** 封が決めていない読み 2 つ: 正解の月次の欄が丸ごと null なら 12 個の null として読み、月次が 13 個以上なら先頭の 12 個だけ読む(commit %s の message・§3 の確認)。"
      u"CSV の大きさに上限を置く行は script に無い(§3 の確認)。`表の行の和` は xlsx の file を指せないので、xlsx の仕訳帳しか無い社ではこの種類が使えない(封 §1-4)。"
      u"時点の行の `以上` の有無を検査は決めない(封 §5)。CP932 への落とし込み・12 か月を超える期の読み・HTML の丸め・N7 の等価な変異は、司令塔の申告で、実装担当は確かめていない。"
      % IMPL_COMMIT)
    w(u"- **言えないこと。** 「実物の会計ソフトの出力で動く」とは言えない。「人が確かめる手間が減る」とは言えない(人が確かめる所は作っていない)。「既存の道具に代わる」とは言えない。"
      u"「席の誤りを止める」とは言えない(席の誤りが 0 で試されていない)。「会社の AI がこの型で書ける」とは言えない。「誤りが無くなる」とは言えない。"
      u"「人の確かめが要らない」とは言えない。「開示の書類が作れる」とは言えない。「専用の道具が要らない」とは言えない。素材を作った席と読む席は同じ種類の AI で、「ありそうな形」の考えを共有する。当たっても「別の席が形を決めた作り物で」までしか言わない。")
    w(u"")
    w(u"## §1 予測の当たり外れ(封を書いた司令塔が立てた)")
    w(u"")
    w(u"封 §3 の字の境と記録から、結果の門が UM2-S1〜UM2-V2 の当たり外れを決め直した(この表と同じ)。当たり外れは記録の数だけで決め、境の数は結果を見て動かしていない。")
    w(u"")
    w(u"| # | 予測(封の字) | 封の外れ方 | 実測(記録) | 判定 |")
    w(u"|---|---|---|---|---|")
    for i in PRED_IDS:
        p, o = pred[i]
        w(u"| %s | %s | %s | %s | %s |" % (i, p, o, meas[i], verdict_word(j[i])))
    w(u"")
    w(u"- 当たり %d・外れ %d。外れは %s。" % (len(hits), len(misses), u"・".join(misses)))
    w(u"- UM2-P3 の注: 「通した行のうち数値が違う」の定義に入らない正解と違う×通した %d は、頭に負けとして書いた。" % n(u"段 1:4 つの枠:正解と違う×通した"))
    w(u"- UM2-D2 の注: 分子は定義表の行(id の重複を除く)で、結果を見た後に直した(頭)。出現の数 %d を分子にすると %s%% で当たりになる。" % (d2_occ, pct(d2_occ, 132)))
    w(u"")
    w(u"## §2 数(記録)")
    w(u"")
    w(u"記録 `%s` の数を全部、記録の並びのまま載せる。本番の %d 社(会社の番号 1〜4)× 2 期。素材の行は 4 × 30 = 120(A)と b01 の 4(分母 %d)。" % (RECORD_REL, n_co, rows124))
    w(u"")
    groups = od([(u"段 0(素材)", lambda k: not k.startswith(u"段 ") and not k.startswith(u"通し") and k != u"束が K0 で断られた束"),
                 (u"段 1(1 期目)", lambda k: k.startswith(u"段 1:") or k == u"束が K0 で断られた束"),
                 (u"段 2(2 期目)", lambda k: k.startswith(u"段 2:")),
                 (u"段 3(資料)", lambda k: k.startswith(u"段 3:")),
                 (u"通し", lambda k: k.startswith(u"通し"))])
    for title, test in groups.items():
        w(u"### %s" % title)
        w(u"")
        w(u"| 項目 | 数 |")
        w(u"|---|---|")
        for k, v in num_group_rows(rec, test):
            w(u"| %s | %d |" % (k, v))
        w(u"")
    w(u"### 変異(作れた・作れなかった・断った・止めた・通した など。記録の並びのまま)")
    w(u"")
    for code, row in rec[u"変異"].items():
        w(u"- **%s**: %s" % (code, u"・".join(u"%s %d" % (k, v) for k, v in row.items())))
    w(u"")
    w(u"### 会社ごと")
    w(u"")
    for ident, row in rec[u"会社ごと"].items():
        w(u"- 会社 %s: %s" % (ident, u"・".join(u"%s %d" % (k, v) for k, v in row.items())))
    w(u"")
    w(u"- 資料の数え方: 札の出現の数は、同じ id が資料に何度出ても数える。定義表の行は、id の重複を除き、1 つの id を 数 > 確認待ち > 無い の順に 1 つにだけ入れる。"
      u"3 つの和が定義表の行(A %d・B %d。1 社の定義表の行 × %d 社)になること、数・確認待ち・無いのどれにも入らない行・定義表に無い id が 0 であることを、結果の門が見る。"
      % (n(u"段 3:定義表の行:期1・A"), n(u"段 3:定義表の行:期1・B"), n_co))
    w(u"- 札の出現の数の合計 %d は、資料の変異 D1 の作れた(数の札を消す)と同じ。" % num_occ)
    w(u"")
    w(u"## §3 記録に欄の無い読み(出どころを書く。結果の門は記録に縛らず、字で留めるだけ)")
    w(u"")
    w(u"- **優先の規則の確認(実装担当が席の資料 16 本を読み直して数えた。記録に欄は無い)。** 同じ id が 数と確認待ち・数と無い・確認待ちと無い のどれかに出る資料は 0 本(16 本の全部で 0)。"
      u"定義表の行 = 数 + 確認待ち + 無い の分け方に、優先の規則は効いていない。優先の規則そのものは、結果の門が作り物の標本で縛る(§4)。")
    w(u"- **K11 の 4 行と持ち越した行の値(実装担当が席の出力と正解を読み直して見た。記録に欄は無い)。** K11 が止めた 4 行は、4 社に 1 行ずつで、4 つとも持ち越した値が正解と同じだった。"
      u"2 期目に持ち越して通して値が違った 1 行は、1 社の A の束の 1 行(司令塔の読みでは、1 期目の取り方の条件をそのまま 2 期目に使ったため対象の行を 1 本落とした。条件の読みは司令塔の読みで、実装担当は確かめていない)。")
    w(u"- **1 期目に止めた 46 行の理由。** 司令塔は 1 行ずつ読んでいない。監査の席の読み(記録に欄は無い)は、期の見出しの形を検査が読めない行と、定義表に無い見出しの行が在る、というもの。")
    w(u"- **正解と違う×通した 4 行の理由。** 監査の席の読み(記録に欄は無い)は、型の「表の行の和」が、行を数えて出す値を書けない型であること。")
    w(u"- **D4 の通した 23。** 監査の席の読み(記録に欄は無い)は、全部「確認待ち」「無い」の札を消した行。数の札を消した変異は 269(D1 の作れたと同じ)で、D1 の通したは 0。")
    w(u"- **A の人が読む版。** 司令塔が画面で見た(記録に欄は無い)。実装担当が人が読む版の html を読み直し、A の 8 本の全部に、`|` で始まる段落(表が表にならず字のまま出たもの)が在ることを確かめた。B の 8 本には無い。")
    w(u"- **席の数(司令塔の数え。記録に欄は無い)。** 材料を書く席は本番の 4 社 × 1 期目 × 成果物 A で 4・B の「新しく要る」行で 4 の 8 席。資料を書く席は 4 社 × 2 期の 8 席。取り直し 0。"
      u"素材を作る席のうち 2 席は、中断して再開した(司令塔の記録)。")
    w(u"- **汚れ(封 §1-9。司令塔の数えで、記録に欄は無い)。** 席が自分で folder の外を読み書きした件は、16 席で 0(席の会話の記録の tool_use の入力の絶対 path だけを見た数え。相対 path と実行時に組む path は見えない。"
      u"正の対照: 席の鍵を取り違えて数えると 6)。道具の自動保存で folder の外に出力が書かれた席が 5(席は読んでいない。監査の席が確かめた)。")
    w(u"- **席ごとの読みの違い(席の報告から。記録に欄は無い)。** B の席は 4 社とも、該当の見出しを見つけられず、自分で選んだ科目を仕訳から足した。選んだ科目の組は席ごとに違う。"
      u"A の席は、1 項目を定義表の取り方と違う取り方で書いた。")
    w(u"- **実装の限界の確かめ。** 月次の欄の読み(丸ごと null → 12 個の null・13 個以上 → 先頭の 12 個)と、CSV の大きさの上限が無いこと・UTF-8 → CP932 の順の読みは、結果の門が script の関数と字で確かめる(§4)。"
      u"CP932 への落とし込み・12 か月を超える期の読み・HTML の丸め・N7 の等価な変異は、司令塔の申告で、確かめていない。")
    w(u"- **独立監査が確かめたこと(commit の message から)。** commit %s は、独立監査 REVISE → 直し → GO。別の実装で数え直し差は 0・記録は作り直して byte で同じ・凍結は前後で一致。"
      u"最初の記録は独立監査 REVISE で、指摘は 2 つ(UM2-D2 の分子の単位・資料の変異 D1 と D4 の止めた・断ったの 0 が数えていない 0)。**確かめていないこと:** 全体の suite。" % RECORD_COMMIT)
    w(u"")
    w(u"## §4 門")
    w(u"")
    w(u"- 結果の門 `%s`: 記録の数え直し(4 つの枠・段 1 の結果・段 2 の持ち越し・段 3 の定義表の行 = 数 + 確認待ち + 無い・変異の足し算)・予測の当たり外れの決め直しと集計の script の judge との一致・この文書の全部の行を記録と字から組み直して照らす・"
      u"封と script と定義表と指示書と封の門と記録が commit の blob と 1 byte も違わないこと・engine が封の commit から 0 行・順序(封 → script など → 記録 → この文書と門)・限界の文の出どころ・"
      u"集計の script の「定義表の行で重複を除く」所を作り物の標本で縛る試験(同じ id が資料に複数回出る・数 > 確認待ち > 無い の優先・定義表に無い id が行に入らない)と、重複を除く所を外す変異で赤になること。変異で赤くなることを門の中で確かめる。"
      % GATE_REL)
    w(u"- 重複を除く所を外す変異を縛る門は、commit %s の時点で無かった(commit の message)。この結果の門が足した。" % RECORD_COMMIT)
    w(u"- 封の門 `%s` の試験は %d 本(file の中の `def test_` の数を結果の門が数える)。" % (SEAL_GATE_REL, c.seal_gate_tests))
    w(u"- 全体の suite(`sh run_tests.sh`)は、この結果の文書の時点で走らせていない。")
    w(u"")
    w(u"## §5 次の便の候補(封 §6 に在るものだけ。結果の文書はここに無い候補を足さない)")
    w(u"")
    for ln in cands:
        w(ln)
    w(u"")
    return u"\n".join(L)


# ================================================================== 検査(問題の一覧を返す)
def sha_problems(c):
    out = []
    for rel, want in SHA_PIN.items():
        if c.shas.get(rel) != want:
            out.append(u"sha256 が違う: %s" % rel)
    return out


def defn_rows(d):
    return len(d[u"行"])


def recount_problems(c):
    u"""記録の足し算・分母・恒等式を、検査の script の関数を使わずに数え直す。"""
    rec = c.rec
    out = []
    if list(rec) != list(TOP_KEYS):
        return [u"記録の頂の鍵が違う: %s" % list(rec)]
    n = rec[u"数"]
    m = rec[u"変異"]
    co = rec[u"会社ごと"]
    nco = rec[u"会社の数"]
    if nco != 4 or sorted(co) != [u"1", u"2", u"3", u"4"]:
        out.append(u"会社の数・会社ごとの鍵が 4 社でない")

    def eq(a, b, what):
        if a != b:
            out.append(u"%s: %r と %r" % (what, a, b))

    g = lambda k: n[k]                                        # noqa: E731
    rows = g(u"段 1:行の数")
    eq(rows, nco * 31, u"段 1 の行の数 = 社 × 31")
    boxes = [g(u"段 1:4 つの枠:" + k) for k in (u"正解どおり×通した", u"正解どおり×止めた", u"正解と違う×通した", u"正解と違う×止めた")]
    eq(sum(boxes), rows, u"4 つの枠の和 = 行の数")
    eq(g(u"段 1:席が在ると書いた行") + g(u"段 1:席が無いと書いた行"), rows, u"在る + 無い = 行の数")
    eq(g(u"段 1:出どころの種類:素材") + g(u"段 1:出どころの種類:素材の和") + g(u"段 1:出どころの種類:表の行の和"), g(u"段 1:席が在ると書いた行"), u"出どころの種類の和 = 在ると書いた行")
    res = [g(u"段 1:検査の結果:" + k) for k in (u"通す", u"通す(取り方は未確認)", u"止める", u"無いを受ける", u"束ごとの断り")]
    eq(sum(res), rows, u"検査の結果の和 = 行の数")
    eq(boxes[0] + boxes[2], g(u"段 1:検査の結果:通す") + g(u"段 1:検査の結果:通す(取り方は未確認)") + g(u"段 1:検査の結果:無いを受ける"), u"通した枠 = 通す + 未確認 + 無いを受ける")
    eq(boxes[1] + boxes[3], g(u"段 1:検査の結果:止める") + g(u"段 1:検査の結果:束ごとの断り"), u"止めた枠 = 止める + 束ごとの断り")
    eq(g(u"段 1:席の答えが正解と同じ"), boxes[0] + boxes[1], u"席の答えが正解と同じ = 正解どおりの 2 枠")
    eq(g(u"段 1:止めた行の規則:K3") + g(u"段 1:止めた行の規則:K4"), g(u"段 1:検査の結果:止める"), u"止めた行の規則の和 = 止める")
    eq(g(u"段 1:止めた行の規則の組:K3") + g(u"段 1:止めた行の規則の組:K4"), g(u"段 1:検査の結果:止める"), u"止めた行の規則の組の和 = 止める")
    eq(g(u"段 1:K3 で止まった行"), g(u"段 1:止めた行の規則:K3"), u"K3 で止まった行 = 規則 K3")
    eq(g(u"段 1:正解どおりなのに止めた"), boxes[1], u"正解どおりなのに止めた = 枠")
    # 段 2
    eq(g(u"段 2:確かめた取り方の行"), g(u"段 1:検査の結果:通す") + g(u"段 1:検査の結果:通す(取り方は未確認)"), u"確かめた取り方 = 1 期目に通した行")
    eq(g(u"段 2:持ち越した行") + g(u"段 2:持ち越せなかった行") + g(u"段 2:無いを持ち越した行"), rows, u"持ち越した + 持ち越せなかった + 無い = 行の数")
    eq(g(u"段 2:持ち越せなかった行"), g(u"段 2:持ち越せなかった行:1 期目で止まった") + g(u"段 2:持ち越せなかった行:同じ見出しの数の cell が 2 つ以上"), u"持ち越せなかった行の理由の和")
    eq(g(u"段 2:持ち越せなかった行:1 期目で止まった"), g(u"段 1:検査の結果:止める"), u"1 期目で止まった = 段 1 の止める")
    eq(g(u"段 2:持ち越した行") + g(u"段 2:持ち越せなかった行:同じ見出しの数の cell が 2 つ以上"), g(u"段 2:確かめた取り方の行"), u"確かめた取り方 = 持ち越した + 見出しの cell が 2 つ以上")
    eq(g(u"段 2:持ち越した行"), g(u"段 2:検査の結果:止める") + g(u"段 2:検査の結果:通す"), u"持ち越した = 止める + 通す")
    eq(g(u"段 2:持ち越して検査を通った行"), g(u"段 2:検査の結果:通す"), u"持ち越して検査を通った = 検査の結果の通す")
    eq(g(u"段 2:持ち越して検査を通った行"),
       g(u"段 2:持ち越して通して正解と数値が同じ") + g(u"段 2:持ち越して通したが数値が違う") + g(u"段 2:持ち越して通したが正解が null") + g(u"段 2:持ち越して通したが正解が読めない"), u"通った行の内訳の和")
    eq(g(u"段 2:止めた行の規則:K11"), g(u"段 2:K11 で止めた行"), u"規則 K11 = K11 で止めた行")
    eq(g(u"段 2:検査の結果:止める"), g(u"段 2:K11 で止めた行"), u"2 期目に止めたのは K11 だけ")
    eq(g(u"段 2:無いを持ち越した行"), g(u"段 2:検査の結果:無いを受ける:無いの行"), u"無いを持ち越した = 無いを受ける")
    eq(sum(r[u"K11 で止めた行"] for r in co.values()), g(u"段 2:K11 で止めた行"), u"会社ごとの K11 の和")
    eq(sum(1 for r in co.values() if r[u"K11 で止めた行"]), g(u"段 2:K11 で止めた社"), u"K11 で止めた社 = 止めた行が在る社")
    for key, want in ((u"通し:期1", u"通し:期1"), (u"通し:期2", u"通し:期2")):
        eq(sum(r[want] for r in co.values()), g(key), u"会社ごとの " + key)
    eq(sum(1 for r in co.values() if r[u"通し:期1"] and r[u"通し:期2"]), g(u"通し:期1・期2とも"), u"通し:期1・期2とも = 両方の社")
    # 段 3
    defrows = {u"A": defn_rows(c.defa) * nco, u"B": defn_rows(c.defb) * nco}
    for t in TAGS:
        prod = t[-1]
        eq(g(u"段 3:定義表の行:" + t), defrows[prod], u"定義表の行 %s = 定義表の行数 × 社" % t)
        eq(g(u"段 3:数が出ている定義表の行:" + t) + g(u"段 3:確認待ちの定義表の行:" + t) + g(u"段 3:無いの定義表の行:" + t)
           + g(u"段 3:定義表の行のうち数・確認待ち・無いのどれにも入らない行:" + t), g(u"段 3:定義表の行:" + t), u"数 + 確認待ち + 無い + 入らない = 定義表の行 %s" % t)
        eq(g(u"段 3:定義表の行のうち数・確認待ち・無いのどれにも入らない行:" + t), 0, u"どれにも入らない行 %s" % t)
        eq(g(u"段 3:定義表に無い id の札の id の数:" + t), 0, u"定義表に無い id %s" % t)
        for a, b in ((u"数が出ている定義表の行", u"数の札の出現の数"), (u"確認待ちの定義表の行", u"確認待ちの札の出現の数"), (u"無いの定義表の行", u"無いの札の出現の数")):
            if g(u"段 3:%s:%s" % (a, t)) > g(u"段 3:%s:%s" % (b, t)) and a != u"確認待ちの定義表の行" and a != u"無いの定義表の行":
                out.append(u"行の数が札の出現の数より多い: %s %s" % (a, t))
        if g(u"段 3:人が読む版が組めた:" + t) > g(u"段 3:資料の検査を通した:" + t):
            out.append(u"人が読む版が資料の検査を通した数より多い: " + t)
        if g(u"段 3:人が読む版の検査を通した:" + t) > g(u"段 3:人が読む版が組めた:" + t):
            out.append(u"人が読む版の検査を通した数が組めた数より多い: " + t)
        if g(u"段 3:資料の検査を通した:" + t) > nco:
            out.append(u"資料の検査を通した数が社の数より多い: " + t)
    eq(g(u"段 3:A の 2 期目の資料で数が出ている行"), g(u"段 3:数が出ている定義表の行:期2・A"), u"A の 2 期目の数が出ている行 = 期2・A の欄")
    eq(g(u"段 3:A の 2 期目の資料で数の札の出現の数"), g(u"段 3:数の札の出現の数:期2・A"), u"A の 2 期目の札の出現 = 期2・A の欄")
    eq(g(u"通し:期1"), min(g(u"段 3:人が読む版が組めた:期1・A"), g(u"段 3:人が読む版が組めた:期1・B")), u"通し:期1 は人が読む版の組めた社(A・B)")
    # 変異
    eq(m[u"M1"][u"作れた"], g(u"段 1:検査の結果:通す"), u"M の作れた = 検査の結果の通す(素材・素材の和の材料)")
    eq(m[u"V1"][u"作れた"], g(u"段 1:検査の結果:通す(取り方は未確認)"), u"V の作れた = 通す(取り方は未確認)(表の行の和の材料)")
    for code, row in m.items():
        if code in (u"D1", u"D4"):
            eq(row[u"作れた"], row[u"止めた"] + row[u"通した"], u"%s 作れた = 止めた + 通した" % code)
            if u"断った" in row:
                out.append(u"資料の変異に「断った」の欄が在る: " + code)
        else:
            eq(row[u"作れた"], row.get(u"断った", 0) + row[u"止めた"] + row[u"通した"], u"%s 作れた = 断った + 止めた + 通した" % code)
            eq(sum(v for k, v in row.items() if k.startswith(u"規則:")), row[u"止めた"], u"%s 規則の和 = 止めた" % code)
        if code in (u"V2", u"V3", u"V6"):
            eq(row[u"作れた:関係に入る"] + row[u"作れた:関係に入らない"], row[u"作れた"], u"%s 作れた:関係の和" % code)
            eq(row[u"通した:関係に入る"] + row[u"通した:関係に入らない"], row[u"通した"], u"%s 通した:関係の和" % code)
    eq(m[u"D1"][u"作れた"], tag_sum(rec, u"段 3:数の札の出現の数"), u"D1 の作れた = 数の札の出現の数の合計")
    word_occ = sum(g(u"段 3:%s:%s" % (k, t)) for k in (u"確認待ちの札の出現の数", u"無いの札の出現の数") for t in TAGS)
    eq(m[u"D4"][u"作れた"], m[u"D1"][u"作れた"] + word_occ, u"D4 の作れた = D1 の作れた + 確認待ち・無いの札の出現")
    return out


def clean_problems(c):
    u"""記録の形(整数だけ・鍵の字・禁止の字が無い)。"""
    out = []

    def walk(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                if not isinstance(k, str):
                    out.append(u"鍵が字でない")
                walk(v, path + (k,))
        elif isinstance(o, bool) or not isinstance(o, int):
            out.append(u"整数でない葉: %s" % u"/".join(path))
        elif o < 0:
            out.append(u"負の葉: %s" % u"/".join(path))

    walk(c.rec, ())
    text = json.dumps(c.rec, ensure_ascii=False)
    if DOCID_FORM.search(text) or ECODE_FORM.search(text):
        out.append(u"記録に docID か EDINET コードの形が在る")
    if DATE_FORM.search(text):
        out.append(u"記録に日付の形が在る")
    heads = set()
    for d in (c.defa, c.defb):
        for r in d[u"行"]:
            heads.update(x for x in [r.get(u"名")] if isinstance(x, str) and len(x) >= 3)
    for h in heads:
        if h in text:
            out.append(u"記録に定義表の名の字が在る: %s" % h)
    return out


def bound_problems(c):
    u"""封の字: 予測の表の 15 行・§6 の候補 (i)〜(vi)・結果の文書が足さない決めが封にそのまま在る。"""
    out = []
    want = list(SG.SEAL_PREDICTION_ROWS) + list(SEAL_V_ROWS)
    for row in want:
        if row not in c.seal:
            out.append(u"封に予測の行が無い: %s" % row[:20])
    if list(seal_pred_rows(c.seal)) != list(PRED_IDS):
        out.append(u"封の予測の表の id が違う: %s" % list(seal_pred_rows(c.seal)))
    cands = seal_candidates(c.seal)
    if len(cands) != SEAL_CANDIDATE_COUNT or [x.split(u" ")[1] for x in cands] != [u"(i)", u"(ii)", u"(iii)", u"(iv)", u"(v)", u"(vi)"]:
        out.append(u"封 §6 の候補が (i)〜(vi) の 6 つでない")
    for must in (u"結果の文書はここに無い候補を足さない", u"UM2-Q2 が外れたら", u"言えないこと"):
        if must not in c.seal:
            out.append(u"封に字が無い: %s" % must)
    return out


def verdict_problems(c):
    u"""judge が決めた当たり外れが、集計の script の judge・文書の頭の件数・§1 の表の判定列と同じ。"""
    out = []
    j = judge(c.rec)
    if list(j) != list(PRED_IDS):
        out.append(u"judge の予測の並びが違う")
    if None in j.values():
        out.append(u"記録では決まらない予測が在る")
    tj = TAL.judge(c.rec)
    for i in PRED_IDS:
        if tj.get(i, {}).get(u"当たり") != j.get(i):
            out.append(u"集計の script の judge と食い違う: %s" % i)
    miss = [i for i, v in j.items() if v is False]
    hit = [i for i, v in j.items() if v is True]
    if u"**予測 %d 本は 当たり %d・外れ %d。** 外れは %s。" % (len(j), len(hit), len(miss), u"・".join(miss)) not in c.doc:
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
    out = []
    if cands != seal_candidates(c.seal):
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


HEAD_FRAGS = (u"**先に負けと限界を書く。**", u"**通し: 本番の", u"段 1〜7 が資料の生成まで通った", u"UM2-D2 は外れ", u"直す前は", u"結果を見た後の直し", u"判定は不利な側に動いた",
              u"種類をまたぐ id が 0", u"**一番大きい負けは UM2-Q2。**", u"人の確かめではない", u"止めすぎ", u"席の誤り 0", u"司令塔は 1 行ずつ読んでいない", u"監査の席の読み",
              u"席の誤りを検査が止める」は測れていない", u"**正解と違う×通した", u"P3 の定義", u"**資料は薄い。**", u"`| … |` の字のまま", u"この便では直していない", u"**変異",
              u"V2・V3・V6 が通したことの読み", u"**D4 が通した", u"**席。**", u"互いに独立ではない", u"model の名は書かない", u"**実装の限界。**", u"司令塔の申告",
              u"**言えないこと。**", u"実物の会計ソフトの出力で動く」とは言えない", u"人が確かめる手間が減る」とは言えない", u"既存の道具に代わる」とは言えない", u"席の誤りを止める」とは言えない",
              u"別の席が形を決めた作り物で」までしか言わない", u"盲検でない", u"記録に欄は無い")


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
    for must in (u"記録に縛らず、字で留めるだけ", u"記録に欄は無い", u"実装担当が", u"司令塔の数え", u"監査の席の読み", u"司令塔の申告", u"確かめていないこと", u"席の報告から", u"正の対照"):
        if must not in s3:
            out.append(u"§3 に字が無い: %s" % must)
    outside = c.doc[:i] + c.doc[j:]
    for must_not in (u"16 席で 0", u"正の対照", u"道具の自動保存", u"16 本の全部で 0", u"中断して再開"):
        if must_not in outside:
            out.append(u"§3 だけの主張が §3 の外に在る: %s" % must_not)
    return out


def affirm_problems(c):
    out = []
    for ln in c.doc.splitlines():
        for sent in re.split(u"。", ln):
            for p in AFFIRM_PHRASES:
                if p in sent and u"言えない" not in sent and u"読まない" not in sent and u"測れていない" not in sent and u"作っていない" not in sent:
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
    for short, msg, words in ((IMPL_COMMIT, c.msg_impl, (u"独立監査 REVISE(門の穴)→ 直し → REVISE(門の穴 5 つ)→ 直し → GO", u"全体の suite は未実行", u"月次の欄が丸ごと null なら 12 個の null", u"月次が 13 個以上なら先頭の 12 個だけ読む")),
                              (RECORD_COMMIT, c.msg_record, (u"独立監査 REVISE → 直し → GO", u"UM2-D2 の分子は 90(出現の数)→ 64(定義表の行)", u"結果を見た後の直し", u"判定は不利な側に動く",
                                                            u"種類をまたぐ id は 0", u"重複を除く所を外す変異を縛る門は、この commit には無い", u"別の実装で数え直し差は 0", u"全体の suite は未実行",
                                                            u"最初の記録は独立監査 REVISE"))):
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
    u"""``at``: {rel: commit}。file が commit の blob と 1 byte も違わない。"""
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
    u"""各 file が、文書の書く commit で足され(1 回だけ)、最後の commit も文書の書く commit。"""
    out = []
    for rel, (added_at, last_at) in BLOB_AT.items():
        added = PR.added_commits(root, PREFIX + rel)
        if len(added) != 1 or not added[0].startswith(added_at):
            out.append(u"%s を足した commit が %s でない" % (rel, added_at))
        rc, last = PR.git_in(root, "log", "-1", "--format=%H", "--", PREFIX + rel)
        if not last.startswith(last_at):
            out.append(u"%s の最後の commit が %s でない(その後で変わった)" % (rel, last_at))
    return out


def order_problems(root):
    u"""封 ⊏ script など ⊏ 記録 ⊏ この文書と門。文書と門は、まだ commit されていない間は許す(commit された後は順序を見る)。"""
    impl = [CHECK_REL, TALLY_REL, INSTR_REL, SEAL_GATE_REL, BRIEF_REL]
    out = list(PR.order_problems(root, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, impl, [RECORD_REL, DOC_REL, GATE_REL]))
    out = [x for x in out if x not in (u"UNCOMMITTED:" + DOC_REL, u"UNCOMMITTED:" + GATE_REL)]
    rec = PR.added_commits(root, PREFIX + RECORD_REL)
    for rel in (CHECK_REL, INSTR_REL, SEAL_GATE_REL):
        added = PR.added_commits(root, PREFIX + rel)
        if added and rec and not PR.is_anc(root, added[0], rec[0]):
            out.append(u"記録が %s より前" % rel)
    return out


def git_problems(root=REPO):
    at = od((rel, last) for rel, (_a, last) in BLOB_AT.items())
    at[DEF_RELS[0]] = DEF_COMMIT
    at[DEF_RELS[1]] = DEF_COMMIT
    return blob_problems(root, PREFIX, at) + engine_zero_problems(root, SEAL_COMMIT_SHORT) + history_problems(root) + order_problems(root)


# ================================================================== 限界の文の出どころ
def source_problems(check_text=None, tal=None):
    u"""文書の限界の文が、script の字と関数の動きに合う。``check_text``・``tal`` を差し替えると赤になる(変異)。"""
    check_text = read(CHECK_REL) if check_text is None else check_text
    tal = tal or TAL
    out = []
    if re.search(r"(?m)^\s*(?:MAX|LIMIT)[A-Z_]*\s*=", check_text):
        out.append(u"検査の script に大きさの上限の定数が在る(文書は上限が無いと書いた)")
    if u'raw.decode("cp932")' not in check_text or u'raw.decode("utf-8-sig")' not in check_text:
        out.append(u"検査の script が UTF-8(BOM 可)→ CP932 の順で読まない")
    with tempfile.TemporaryDirectory() as tmp:
        def gold(months):
            body = od([(k, 0) for _i, k in tal.GOLD_KEYS])
            body[tal.MONTH_KEY] = months
            path = os.path.join(tmp, u"g.json")
            with io.open(path, "w", encoding="utf-8") as fh:
                fh.write(json.dumps({u"期1": body, u"期2": body}, ensure_ascii=False))
            return tal.read_gold(path)[0][u"期1"]
        v = gold(None)
        if any(v[i] is not None for i in tal.MONTH_IDS):
            out.append(u"月次が丸ごと null でも 12 個の null にならない")
        v = gold(list(range(1, 14)))
        if [v[i] for i in tal.MONTH_IDS] != list(range(1, 13)):
            out.append(u"月次が 13 個以上のとき先頭の 12 個だけを読まない")
    return out


# ================================================================== 集計の「定義表の行で重複を除く」所(作り物の標本)
def load_tally_from(text, name):
    u"""集計の script の字(変異つきでもよい)から module を作る。script の置き場の参照は本物の measure/ へ向ける。"""
    src = text.replace(u"HERE = os.path.dirname(os.path.abspath(__file__))", u"HERE = %r" % os.path.join(ROOT, "measure"), 1)
    if src == text:
        raise AssertionError(u"HERE の行が無い")
    mod = types.ModuleType(name)
    mod.__file__ = os.path.join(ROOT, TALLY_REL)
    exec(compile(src, os.path.join(ROOT, TALLY_REL), "exec"), mod.__dict__)
    return mod


DEDUP_EXPECT = od([
    (u"段 3:数の札の出現の数:期2・A", 4), (u"段 3:確認待ちの札の出現の数:期2・A", 4), (u"段 3:無いの札の出現の数:期2・A", 5),
    (u"段 3:数が出ている定義表の行:期2・A", 1), (u"段 3:確認待ちの定義表の行:期2・A", 1), (u"段 3:無いの定義表の行:期2・A", 1),
    (u"段 3:定義表に無い id の札の id の数:期2・A", 3),
    (u"段 3:A の 2 期目の資料で数が出ている行", 1), (u"段 3:A の 2 期目の資料で数の札の出現の数", 4)])


def dedup_text(ids):
    x, y, z = ids[0], ids[1], ids[2]
    return (u"数が出る行 12円[材料:%s] 12円[材料:%s] 12円[材料:%s]\n確認待ち[材料:%s] 無い[材料:%s]\n"
            u"確認待ち[材料:%s] 確認待ち[材料:%s] 無い[材料:%s]\n"
            u"無い[材料:%s] 無い[材料:%s]\n"
            u"7円[材料:zz99] 確認待ち[材料:zz98] 無い[材料:zz97]\n") % (x, x, x, x, x, y, y, y, z, z)


def dedup_problems(tal):
    u"""同じ id が資料に複数回出る作り物の 2 期目の A の資料を集計に掛け、定義表の行・札の出現の数が手で数えた数と同じか見る。
    x: 数の札 3 回 + 確認待ち 1 回 + 無い 1 回 → 数の行 1(数 > 確認待ち > 無い)。y: 確認待ち 2 回 + 無い 1 回 → 確認待ちの行 1。z: 無い 2 回 → 無いの行 1。
    定義表に無い id(zz99 は数の札・zz98 は確認待ちの札・zz97 は無いの札)は行に入らず、別の欄に数える。"""
    w = SG.world()
    ids = [r[u"id"] for r in w.defA.rows]
    with tempfile.TemporaryDirectory() as tmp:
        cdir, sdir = SG.make_company(tmp, 101, w)
        root_c, root_s = os.path.join(tmp, u"会社"), os.path.join(tmp, u"席")
        tal.tally([101], root_c, root_s, CHK)                       # 1 回目: 置き場を出力の folder に書く
        SG.seat_docs(CHK, w, sdir)
        SG.wbytes(os.path.join(sdir, u"資料_期2_A.md"), dedup_text(ids).encode("utf-8"))
        res = tal.tally([101], root_c, root_s, CHK)
    c = res[u"数"]
    out = []
    for k, want in DEDUP_EXPECT.items():
        if c.get(k) != want:
            out.append(u"%s: %r(手で数えた数 %r)" % (k, c.get(k), want))
    rows = len(ids)
    if c.get(u"段 3:定義表の行:期2・A") != rows:
        out.append(u"定義表の行が定義表の行数と違う")
    if c.get(u"段 3:定義表の行のうち数・確認待ち・無いのどれにも入らない行:期2・A") != rows - 3:
        out.append(u"どれにも入らない行が 定義表の行 - 3 でない")
    if sum(c.get(u"段 3:%s:期2・A" % k, 0) for k in (u"数が出ている定義表の行", u"確認待ちの定義表の行", u"無いの定義表の行", u"定義表の行のうち数・確認待ち・無いのどれにも入らない行")) != rows:
        out.append(u"4 つの欄の和が定義表の行に閉じない")
    return out


def dedup_mutants():
    u"""(名, 変異した集計の script の字)。重複を除く所・優先・定義表の絞りを 1 か所ずつ外す。"""
    src = read(TALLY_REL)
    reps = [
        (u"数の行 = 札の出現の数(重複を除かない)", u'c[u"段 3:数が出ている定義表の行:" + tag] += len(s_num & def_ids)', u'c[u"段 3:数が出ている定義表の行:" + tag] += len(nums_m)'),
        (u"A の 2 期目の数が出ている行 = 札の出現の数", u'c[u"段 3:A の 2 期目の資料で数が出ている行"] += len(s_num & def_ids)', u'c[u"段 3:A の 2 期目の資料で数が出ている行"] += len(nums_m)'),
        (u"確認待ちの行 = 札の出現の数", u'c[u"段 3:確認待ちの定義表の行:" + tag] += len(s_wait & def_ids)', u'c[u"段 3:確認待ちの定義表の行:" + tag] += sum(1 for w_ in words_m if w_.group(u"word") == u"確認待ち")'),
        (u"無いの行 = 札の出現の数", u'c[u"段 3:無いの定義表の行:" + tag] += len(s_none & def_ids)', u'c[u"段 3:無いの定義表の行:" + tag] += sum(1 for w_ in words_m if w_.group(u"word") == u"無い")'),
        (u"確認待ちから数の id を除かない(優先 数 > 確認待ち を外す)", u'u"確認待ち") - s_num\n', u'u"確認待ち")\n'),
        (u"無いから数・確認待ちの id を除かない(優先 > 無い を外す)", u'u"無い") - s_num - s_wait\n', u'u"無い")\n'),
        (u"数の id から確認待ち・無いの id を除く(優先を逆にする)", u's_num = set(m.group(u"id") for m in nums_m)\n', u's_num = set(m.group(u"id") for m in nums_m) - set(m.group(u"id") for m in words_m)\n'),
        (u"数の行に定義表に無い id も入れる(絞りを外す)", u'c[u"段 3:数が出ている定義表の行:" + tag] += len(s_num & def_ids)', u'c[u"段 3:数が出ている定義表の行:" + tag] += len(s_num)'),
        (u"A の 2 期目の数が出ている行に定義表に無い id も入れる", u'c[u"段 3:A の 2 期目の資料で数が出ている行"] += len(s_num & def_ids)', u'c[u"段 3:A の 2 期目の資料で数が出ている行"] += len(s_num)'),
        (u"確認待ちの行に定義表に無い id も入れる", u'c[u"段 3:確認待ちの定義表の行:" + tag] += len(s_wait & def_ids)', u'c[u"段 3:確認待ちの定義表の行:" + tag] += len(s_wait)'),
        (u"無いの行に定義表に無い id も入れる", u'c[u"段 3:無いの定義表の行:" + tag] += len(s_none & def_ids)', u'c[u"段 3:無いの定義表の行:" + tag] += len(s_none)'),
        (u"定義表の行 = 3 つの id の和集合", u'c[u"段 3:定義表の行:" + tag] += len(def_ids)', u'c[u"段 3:定義表の行:" + tag] += len(s_num | s_wait | s_none)'),
        (u"定義表に無い id の数を数えない", u'c[u"段 3:定義表に無い id の札の id の数:" + tag] += len((s_num | s_wait | s_none) - def_ids)', u'c[u"段 3:定義表に無い id の札の id の数:" + tag] += 0'),
    ]
    for name, old, new in reps:
        if src.count(old) != 1:
            raise AssertionError(u"集計の script に変異の元の字が 1 つでない(%d): %s" % (src.count(old), name))
        yield name, src.replace(old, new, 1)


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


def consistent_d2_hit(c):
    u"""D2 を当たりにする: 数が出ている行を 80 に(分母 132 の 60% = 79.2)。ほかの欄は合わせない(判定と文書の食い違いを見る)。"""
    c.rec[u"数"][u"段 3:A の 2 期目の資料で数が出ている行"] = 80
    return c


def consistent_q2_zero(c):
    u"""Q2 を当たりにする: 持ち越して通したが数値が違う 1 を 0 に、同じを 1 つ増やす(通った行の内訳の和は合ったまま)。"""
    n = c.rec[u"数"]
    n[u"段 2:持ち越して通したが数値が違う"] = 0
    n[u"段 2:持ち越して通して正解と数値が同じ"] += 1
    return c


def consistent_p3_hit(c):
    u"""P3 を当たりにする(通したが数値が違う を 1 に)。"""
    c.rec[u"数"][u"段 1:通したが数値が違う"] = 1
    return c


def consistent_candidate(c):
    c.seal = c.seal.rstrip(u"\n") + u"\n- (vii) 新しい候補。\n"
    return c


MUTATIONS = od([
    (u"F1  記録の sha256 の写しを違う値に", (lambda c: c.shas.__setitem__(RECORD_REL, u"0" * 64) or c, (u"sha",))),
    (u"F2  封の sha256 の写しを違う値に", (lambda c: c.shas.__setitem__(SEAL_REL, u"0" * 64) or c, (u"sha",))),
    (u"F3  集計の script の sha256 の写しを違う値に", (lambda c: c.shas.__setitem__(TALLY_REL, u"0" * 64) or c, (u"sha",))),
    (u"F4  記録の頂の鍵を消す", (lambda c: c.rec.pop(u"数") and c, (u"recount",))),
    (u"F5  記録の会社を 1 つ消す", (lambda c: c.rec[u"会社ごと"].pop(u"4") and c, (u"recount",))),
    (u"F6  記録に docID の形を足す", (lambda c: c.rec[u"数"].__setitem__(u"x", 0) or c.rec[u"数"].__setitem__(u"SXXXXXXX", 0) or c, (u"clean",))),
    (u"F7  記録に文字の葉を足す", (lambda c: c.rec[u"数"].__setitem__(u"x", u"売上高") or c, (u"clean",))),
    (u"F8  封の予測の行を 1 つ消す(境の字)", (lambda c: rep(c, u"| UM2-P1 | 1 期目、席の答えが正解と同じ行は 124 のうち 93 以上(75%) | 92 以下 |", u"", "seal"), (u"bound",))),
    (u"F9  封の予測の行の境を替える(93 → 90)", (lambda c: rep(c, u"124 のうち 93 以上", u"124 のうち 90 以上", "seal"), (u"bound",))),
    (u"F10 封 §6 に (vii) の候補を足す(封の写しだけ)", (consistent_candidate, (u"sec5", u"lines", u"bound"))),
    (u"C1  UM2-D2 を当たりにする(数が出ている行を 80 に)", (consistent_d2_hit, (u"verdict", u"lines"))),
    (u"C2  UM2-Q2 を当たりにする(通したが数値が違う を 0 に。内訳の和は合ったまま)", (consistent_q2_zero, (u"verdict", u"lines"))),
    (u"C3  UM2-P3 を当たりにする(通したが数値が違う を 1 に)", (consistent_p3_hit, (u"verdict", u"lines"))),
    (u"D1  頭の「当たり 10・外れ 5」を「当たり 11・外れ 4」に", (lambda c: rep(c, u"当たり 10・外れ 5", u"当たり 11・外れ 4", count=2), (u"verdict", u"lines"))),
    (u"D2  §1 の UM2-Q2 の「外れ」を「当たり」に", (lambda c: rep(c, u"持ち越して通したが数値が違う 1(通した 58 のうち) | 外れ |", u"持ち越して通したが数値が違う 1(通した 58 のうち) | 当たり |"), (u"verdict", u"lines"))),
    (u"D3  頭の「一番大きい負けは UM2-Q2」の見出しを消す", (lambda c: rep(c, u"**一番大きい負けは UM2-Q2。**", u""), (u"lines", u"head"))),
    (u"D4  頭の「直す前は」の文を消す", (lambda c: rep(c, u"**直す前は 90 / 132 = 68.2% で、当たりと出ていた。これは結果を見た後の直しで、判定は不利な側に動いた。**", u""), (u"lines", u"head"))),
    (u"D5  「実物の会計ソフトの出力で動く」とは言えない → 肯定", (lambda c: rep(c, u"「実物の会計ソフトの出力で動く」とは言えない。", u"実物の会計ソフトの出力で動く。"), (u"affirm", u"lines", u"head"))),
    (u"D6  「席の誤りを止める」とは言えない → 肯定", (lambda c: rep(c, u"「席の誤りを止める」とは言えない(席の誤りが 0 で試されていない)。", u"席の誤りを止める。"), (u"affirm", u"lines", u"head"))),
    (u"D7  §5 に (vii) の候補を足す", (lambda c: setattr(c, "doc", c.doc.rstrip(u"\n") + u"\n- (vii) 新しい候補。\n") or c, (u"sec5", u"lines"))),
    (u"D8  §5 の (iv) の字を替える", (lambda c: rep(c, u"(iv) 便 UM1 の第三者の帳簿で、資料の生成までつなぐ。", u"(iv) 何もしない。"), (u"sec5", u"lines"))),
    (u"D9  §5 の (iii) を落とす", (lambda c: setattr(c, "doc", u"\n".join(l for l in c.doc.split(u"\n") if not l.startswith(u"- (iii)"))) or c, (u"sec5", u"lines"))),
    (u"D10 限界(席は全部同じ種類)の語を消す", (lambda c: rep(c, u"互いに独立ではない", u""), (u"head", u"lines"))),
    (u"D11 文書の commit の字 a0b7ab6f を 1 字替える", (lambda c: rep(c, u"a0b7ab6f", u"a0b7ab6e", count=3), (u"commits", u"lines"))),
    (u"D12 文書に知らない commit の字を足す", (lambda c: rep(c, u"費用は 0。", u"費用は 0。(commit deadbeef)", count=1), (u"commits", u"lines"))),
    (u"D13 文書に禁止語を足す", (lambda c: rep(c, u"費用は 0。", u"費用は 0。精度は高い。"), (u"forbidden", u"lines"))),
    (u"D14 文書に docID の形を足す", (lambda c: rep(c, u"費用は 0。", u"費用は 0。S100AAAA。"), (u"forbidden", u"lines"))),
    (u"D15 §3 の「記録に縛らず、字で留めるだけ」を消す", (lambda c: rep(c, u"結果の門は記録に縛らず、字で留めるだけ)", u")"), (u"sec3", u"lines"))),
    (u"D16 §3 の数(16 席で 0)を替える", (lambda c: rep(c, u"16 席で 0", u"16 席で 1"), (u"lines",))),
    (u"D17 §4 の封の門の試験の数を替える", (lambda c: rep(c, u"の試験は 146 本", u"の試験は 147 本"), (u"lines",))),
    (u"D18 「全体の suite は…走らせていない」を消す", (lambda c: setattr(c, "doc", u"\n".join(l for l in c.doc.split(u"\n") if u"走らせていない" not in l)) or c, (u"lines",))),
    (u"D19 算用数字を漢数字に逃がす(124 → 百二十四)", (lambda c: rep(c, u"| 段 1:行の数 | 124 |", u"| 段 1:行の数 | 百二十四 |"), (u"lines",))),
    (u"D20 頭の予測の件数の数字を字に逃がす(15 本 → 十五本)", (lambda c: rep(c, u"**予測 15 本は", u"**予測 十五本は"), (u"verdict", u"lines"))),
    (u"D21 注の「P3 の定義」を消す", (lambda c: rep(c, u"UM2-P3 の定義(通した行のうち数値が違う)には入らず、", u""), (u"lines", u"head"))),
])


def run_mutations(base):
    u"""固定の変異。戻りは (名, 赤になった検査の集合, 期待, ok)。期待の全部が赤・かつ 1 つ以上赤。"""
    res = []
    for name, (fn, expect) in MUTATIONS.items():
        c = base.copy()
        try:
            fn(c)
        except BaseException as exc:               # noqa: BLE001
            if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                raise
            res.append((name, set([u"変異が当たらない:" + type(exc).__name__]), expect, False))
            continue
        red = red_set(c)
        res.append((name, red, expect, bool(red) and set(expect) <= red))
    return res


# ================================================================== 掃き
NUM_RE = re.compile(r"[0-9]+(?:,[0-9]{3})*")
KANJI = u"〇一二三四五六七八九"


def sweep_numbers(doc):
    u"""文書の全部の数を、(a) 1 増やす (b) 次の別の数に替える (c) 漢数字の字に替える。"""
    spans = [(m.start(), m.end(), m.group(0)) for m in NUM_RE.finditer(doc)]
    vals = [s[2] for s in spans]
    for k, (a, b, t) in enumerate(spans):
        v = int(t.replace(u",", u""))
        yield u"数 +1 @%d(%s)" % (a, t), doc[:a] + str(v + 1) + doc[b:]
        other = next((x for x in vals[k + 1:] + vals[:k] if x != t), None)
        if other is not None:
            yield u"数 替え @%d(%s→%s)" % (a, t, other), doc[:a] + other + doc[b:]
        yield u"漢数字 @%d(%s)" % (a, t), doc[:a] + u"".join(KANJI[int(ch)] if ch.isdigit() else ch for ch in t) + doc[b:]


WORD_PAIRS = ((u"当たり", u"外れ"), (u"外れ", u"当たり"), (u"通した", u"止めた"), (u"止めた", u"通した"), (u"作れなかった", u"作れた"), (u"全部", u"一部"),
              (u"在る", u"無い"), (u"無い", u"在る"), (u"正解どおり", u"正解と違う"), (u"言えない", u"言える"), (u"読まない", u"読む"), (u"未実行", u"実行済み"),
              (u"測れていない", u"測れている"), (u"確かめていない", u"確かめた"), (u"不利な側", u"有利な側"), (u"独立ではない", u"独立である"), (u"以上", u"以下"),
              (u"申告", u"確認"), (u"0 行", u"1 行"), (u"席の誤りが 0", u"席の誤りが 1"))


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


def sweep_candidates(doc):
    yield u"候補を足す", doc.rstrip(u"\n") + u"\n- (vii) 新しい候補。\n"
    ls = doc.split(u"\n")
    idx = [k for k, l in enumerate(ls) if re.match(r"^- \((?:i|ii|iii|iv|v|vi)\) ", l)]
    for k in idx:
        yield u"候補を落とす @%d" % (k + 1), u"\n".join(ls[:k] + ls[k + 1:])
    if len(idx) >= 2:
        sw = list(ls)
        sw[idx[0]], sw[idx[1]] = sw[idx[1]], sw[idx[0]]
        yield u"候補を入れ替える", u"\n".join(sw)


def all_doc_cases(doc):
    for gen in (sweep_numbers, sweep_words, sweep_lines, sweep_sentences, sweep_candidates):
        for name, new in gen(doc):
            if new != doc:
                yield name, new


def run_doc_sweep(base):
    u"""全部の掃きの変異は、``lines`` 1 つだけでも赤。黙った名を返す。"""
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

    def test_c_2_the_verdicts_are_decided_again_and_equal_the_tally_judge_and_the_document(self):
        self.assertEqual([], verdict_problems(self.c))
        j = judge(self.c.rec)
        self.assertEqual(list(PRED_IDS), list(j))
        self.assertEqual([u"UM2-S2", u"UM2-P2", u"UM2-P3", u"UM2-Q2", u"UM2-D2"], [i for i, v in j.items() if v is False])
        self.assertEqual(10, len([1 for v in j.values() if v is True]))

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
        self.assertEqual(146, self.c.seal_gate_tests)

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
            SG.make_repo([("seal", {seal: u"s"}), ("rec", {PREFIX + RECORD_REL: u"{}"}), ("impl", {PREFIX + CHECK_REL: u"x"})], tmp)
            short = subprocess.run(["git", "-C", tmp, "log", "--format=%h", "--", seal], stdout=subprocess.PIPE).stdout.decode().strip()
            got = PR.order_problems(tmp, PREFIX, SEAL_REL, short, [CHECK_REL], [RECORD_REL])
            self.assertNotEqual([], list(got))

    def test_g_1_the_source_of_the_limit_sentences(self):
        self.assertEqual([], source_problems())

    def test_g_2_the_source_check_is_red_for_a_changed_script_text_or_function(self):
        text = read(CHECK_REL)
        self.assertNotEqual([], source_problems(check_text=text + u"\nMAX_BYTES = 10\n"))
        self.assertNotEqual([], source_problems(check_text=text.replace(u'raw.decode("cp932")', u"raw")))
        self.assertNotEqual([], source_problems(check_text=text.replace(u'raw.decode("utf-8-sig")', u"raw")))

        class Fake(object):
            GOLD_KEYS = TAL.GOLD_KEYS
            MONTH_KEY = TAL.MONTH_KEY
            MONTH_IDS = TAL.MONTH_IDS

            @staticmethod
            def read_gold(path):
                return ({u"期1": dict((i, 0) for i in TAL.MONTH_IDS)},)
        self.assertGreaterEqual(len(source_problems(tal=Fake)), 1)


class DedupTest(unittest.TestCase):
    u"""集計の script の「定義表の行で重複を除く」所。実物は手で数えた数と同じ・外す変異は全部赤。"""

    def test_k_1_the_real_tally_counts_ids_not_occurrences_with_the_priority(self):
        self.assertEqual([], dedup_problems(TAL))

    def test_k_2_every_mutation_of_the_dedup_and_the_priority_turns_the_sample_red(self):
        silent = []
        n = 0
        for name, src in dedup_mutants():
            mod = load_tally_from(src, "um2_tally_mut_%d" % n)
            n += 1
            if not dedup_problems(mod):
                silent.append(name)
        self.assertGreaterEqual(n, 13)
        self.assertEqual([], silent)

    def test_k_3_the_sample_is_a_real_duplicate_case(self):
        w = SG.world()
        ids = [r[u"id"] for r in w.defA.rows]
        text = dedup_text(ids)
        nums = list(TAL._NUMTAG.finditer(text))
        words = list(TAL._WORDTAG.finditer(text))
        self.assertEqual(4, len(nums))
        self.assertEqual(9, len(words))
        self.assertGreater(len(nums), len(set(m.group(u"id") for m in nums)))
        self.assertIn(u"zz99", [m.group(u"id") for m in nums])
        for fake in (u"zz99", u"zz98", u"zz97"):
            self.assertNotIn(fake, ids)
        self.assertEqual(3, len(set(ids[:3])))

    def test_k_4_the_mutated_script_is_the_real_one_except_for_the_changed_text(self):
        src = read(TALLY_REL)
        for name, new in dedup_mutants():
            self.assertNotEqual(src, new, name)
        mod = load_tally_from(src, "um2_tally_same")
        self.assertEqual(TAL.GOLD_KEYS, mod.GOLD_KEYS)


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
        for fn in (consistent_q2_zero, consistent_p3_hit):
            c = self.base.copy()
            fn(c)
            self.assertIn(u"lines", red_set(c), fn.__name__)
        c = self.base.copy()
        consistent_q2_zero(c)
        self.assertEqual([], recount_problems(c))

    def test_h_4_every_check_a_mutation_names_exists(self):
        names = set(k for _n, (_f, ex) in MUTATIONS.items() for k in ex)
        self.assertTrue(names <= set(CHECKS), names - set(CHECKS))

    def test_h_5_the_judgement_edges_at_the_seal_bounds(self):
        edges = (
            (u"UM2-S1", u"関係が成り立つ本数", 22, 21), (u"UM2-P1", u"段 1:席の答えが正解と同じ", 93, 92), (u"UM2-P3", u"段 1:通したが数値が違う", 1, 0),
            (u"UM2-P4", u"段 1:K3 で止まった行", 10, 9), (u"UM2-Q3", u"段 2:K11 で止めた社", 1, 0), (u"UM2-E1", u"通し:期1・期2とも", 3, 2),
            (u"UM2-D2", u"段 3:A の 2 期目の資料で数が出ている行", 80, 79), (u"UM2-Q2", u"段 2:持ち越して通したが数値が違う", 0, 1), (u"UM2-S2", u"正解が null の行:期1", 4, 3),
            (u"UM2-S2", u"正解が null の行:期1", 30, 31), (u"UM2-P5", u"束が K0 で断られた束", 0, 1))
        for key, field, ok_val, ng_val in edges:
            for val, want in ((ok_val, True), (ng_val, False)):
                c = self.base.copy()
                c.rec[u"数"][field] = val
                self.assertEqual(want, judge(c.rec)[key], (key, field, val))
                self.assertEqual(want, TAL.judge(c.rec)[key][u"当たり"], (u"tally", key, field, val))
        # D1: 資料の検査を通した 13 / 12(期ごとの欄の和)
        for total, want in ((13, True), (12, False)):
            c = self.base.copy()
            for t in TAGS:
                c.rec[u"数"][u"段 3:資料の検査を通した:" + t] = 0
            c.rec[u"数"][u"段 3:資料の検査を通した:期1・A"] = 4
            c.rec[u"数"][u"段 3:資料の検査を通した:期1・B"] = 4
            c.rec[u"数"][u"段 3:資料の検査を通した:期2・A"] = 4
            c.rec[u"数"][u"段 3:資料の検査を通した:期2・B"] = total - 12
            self.assertEqual(want, judge(c.rec)[u"UM2-D1"], total)
            self.assertEqual(want, TAL.judge(c.rec)[u"UM2-D1"][u"当たり"], total)
        # P2: 表の行の和 / 在ると書いた(30%)。在るが 120 → 36 / 35
        for val, want in ((36, True), (35, False)):
            c = self.base.copy()
            c.rec[u"数"][u"段 1:出どころの種類:表の行の和"] = val
            self.assertEqual(want, judge(c.rec)[u"UM2-P2"], val)
            self.assertEqual(want, TAL.judge(c.rec)[u"UM2-P2"][u"当たり"], val)
        # Q1: 持ち越した / 確かめた取り方(80%)。74 → 59.2 なので 60 / 59
        for val, want in ((60, True), (59, False)):
            c = self.base.copy()
            c.rec[u"数"][u"段 2:持ち越した行"] = val
            self.assertEqual(want, judge(c.rec)[u"UM2-Q1"], val)
            self.assertEqual(want, TAL.judge(c.rec)[u"UM2-Q1"][u"当たり"], val)
        # V1: 関係に入らない行で通した = 作れた。V2: V1・V4 の通したが 0
        c = self.base.copy()
        c.rec[u"変異"][u"V3"][u"通した:関係に入らない"] -= 1
        self.assertFalse(judge(c.rec)[u"UM2-V1"])
        self.assertFalse(TAL.judge(c.rec)[u"UM2-V1"][u"当たり"])
        c = self.base.copy()
        c.rec[u"変異"][u"V4"][u"通した"] = 1
        self.assertFalse(judge(c.rec)[u"UM2-V2"])
        self.assertFalse(TAL.judge(c.rec)[u"UM2-V2"][u"当たり"])
        # 作れた:関係に入る の通した(V6)は V1 の予測に入らない(通しても外れにならない)
        c = self.base.copy()
        c.rec[u"変異"][u"V6"][u"通した:関係に入る"] = 0
        self.assertTrue(judge(c.rec)[u"UM2-V1"])

    def test_h_5b_the_tally_judge_ignores_the_second_term_k0_bundles_but_this_gate_does(self):
        u"""集計の script の judge(UM2-P5)は 1 期目の「束が K0 で断られた束」だけを見る。封は「8 束のうち 0」(2 期目の束も入る)。
        記録では 2 期目も 0 なので結果は同じ。食い違いは script に在り(0 行の約束で直さない)、この試験が現状を留める。"""
        c = self.base.copy()
        c.rec[u"数"][u"段 2:束が K0 で断られた束"] = 1
        self.assertFalse(judge(c.rec)[u"UM2-P5"])
        self.assertTrue(TAL.judge(c.rec)[u"UM2-P5"][u"当たり"])
        self.assertEqual(0, N(self.base.rec, u"段 2:束が K0 で断られた束"))
        self.assertEqual(0, N(self.base.rec, u"束が K0 で断られた束"))

    def test_h_6_the_d2_unit_is_the_definition_rows_not_the_occurrences(self):
        c = self.base.copy()
        self.assertFalse(judge(c.rec)[u"UM2-D2"])
        c.rec[u"数"][u"段 3:A の 2 期目の資料で数の札の出現の数"] = 9999          # 出現の数は判定に使わない
        self.assertFalse(judge(c.rec)[u"UM2-D2"])
        self.assertFalse(TAL.judge(c.rec)[u"UM2-D2"][u"当たり"])
        self.assertGreaterEqual(100 * N(self.base.rec, u"段 3:A の 2 期目の資料で数の札の出現の数"), 60 * 132)       # 出現の数なら当たりと出た

    def test_h_7_the_sweep_over_every_number_word_line_sentence_and_candidate_stays_red(self):
        n, silent = run_doc_sweep(self.base)
        self.assertGreater(n, 1500)
        self.assertEqual([], silent[:20], u"黙った変異 %d 個(総数 %d)" % (len(silent), n))

    def test_h_8_the_record_leaf_sweep_stays_red_without_the_sha_pin(self):
        n, silent = run_record_sweep(self.base)
        self.assertGreater(n, 150)
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
