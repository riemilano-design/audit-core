# -*- coding: utf-8 -*-
u"""結果の門: 封 docs/UNIVERSAL_PROCESS_SEAL_2026-11-24.md(6c4457fe)の結果の文書 docs/UNIVERSAL_PROCESS_RESULT_2026-11-24.md(便 UM3)。

封の門 ``test_universal_process_seal.py`` の次の段。**追跡されている記録・script・封・頼みの紙・封の門・結果の文書・便 UM2 の記録と git の履歴だけを読む**
(席の folder・会話の記録・素材・正解は読まない・通信しない・鍵は読まない・API は呼ばない)。
検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``Ctx`` の写しに当てる(木の file は変異させない。前後の sha256 を見る)。

 a sha256(字で留める)。封・頼みの紙・script・封の門・記録
 b 記録の数え直し: 足し算・分母・恒等式を、**集計の script の関数を使わずに**数え直す(結果の名の和・会社ごと・席ごと・掛け合わせ・自信・揺れ・関係・資料・過程・B の席・汚れを外した数)
 c 予測 UM3-A1〜UM3-D1 の当たり外れを、封の字の境と記録の数から決め直し(``judge``)、記録の ``予測`` の欄・集計の script の judge・文書の表と同じことを見る。
   封の予測の表の行(予測の字・外れ方の字)は封から読んで文書の表に使う
 d 結果の文書の全部の行を、記録と字から組み直し(``render``)、文書と行ごとに照らす。§1・§2 の数と、頭・§3 の中で記録に在る数は全部これで縛る。
   **頭と §3 の、記録に欄の無い読み(監査の席の読み・司令塔の数え・席の申告)の数は、記録に縛れないので字で留めるだけ**(門の中に同じ字が在る。記録に縛るのではない)
 e 封 §3 の決め(勝ち負けの文が無い・A3 か A6 が当たりなら A の負けが頭に・A2 か A5 が当たりなら B の負けが頭に・言えないこと)・
   文書の字が記録の数と結ぶ主張(「全部」「2 席とも 2 期目」など)・§5 が封 §5 の (i)〜(v) だけ・禁止語・docID と EDINET コードの形・「人の目」と書かない
 f 封・頼みの紙・script・封の門・記録が commit の blob と 1 byte も違わない・engine は封の commit から 0 行・順序(封 → 実装 → 記録 → この文書と門)
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
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)

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


SEAL_REL = "docs/UNIVERSAL_PROCESS_SEAL_2026-11-24.md"
BRIEF_REL = "docs/UNIVERSAL_PROCESS_BRIEF_2026-11-24.md"
TALLY_REL = "measure/universal_process_tally_2026-11-24.py"
SEAL_GATE_REL = "tests/measure/test_universal_process_seal.py"
RECORD_REL = "fixtures/universal/um3/record.json"
UM2_RECORD_REL = "fixtures/universal/um2/record.json"
DEF_RELS = ("fixtures/universal/um0/definition_A.json", "fixtures/universal/um0/definition_B.json")
GATE_REL = "tests/measure/test_universal_process_result.py"
DOC_REL = "docs/UNIVERSAL_PROCESS_RESULT_2026-11-24.md"
SEAL_COMMIT = "6c4457fe"                          # 封と頼みの紙の commit
IMPL_COMMIT = "fb0ee282"                          # script と封の門を足した commit
FIX_COMMIT = "fe217c50"                           # 数えの直し(script と封の門)
RECORD_COMMIT = "8156e02b"                        # 記録を足した commit
DOC_COMMITS = (SEAL_COMMIT, IMPL_COMMIT, FIX_COMMIT, RECORD_COMMIT)
#: file → (足した commit, 最後の commit)
BLOB_AT = od([
    (SEAL_REL, (SEAL_COMMIT, SEAL_COMMIT)),
    (BRIEF_REL, (SEAL_COMMIT, SEAL_COMMIT)),
    (TALLY_REL, (IMPL_COMMIT, FIX_COMMIT)),
    (SEAL_GATE_REL, (IMPL_COMMIT, FIX_COMMIT)),
    (RECORD_REL, (RECORD_COMMIT, RECORD_COMMIT)),
])
SHA_PIN = od([
    (SEAL_REL, "40ec5672357e952411736be137551c43c7f7da0075cd1eca8532899eb2160ca4"),
    (BRIEF_REL, "76aaa2077cf7d3b726b8f05617e23ee6024b0d6b8926685192dbac188347ded8"),
    (TALLY_REL, "58fc2640cdfbb9b273a0bea1612f10dcf494e4798ae01a80a9c48e346c90c50d"),
    (SEAL_GATE_REL, "5a4f18697a68f48261e96c6fa7797a86a3a9855d99852c9f70863bdfc02d4f7c"),
    (RECORD_REL, "d43405cff3065989015ee2134cfbdff742e9716ff595627c7b49f61a47226be8"),
])

MY_TALLY_NAME = "um3_tally_for_result_gate"
MY_PR_NAME = "p28_result_helpers_for_um3_result_gate"
TAL = load_module(TALLY_REL, MY_TALLY_NAME)
PR = load_module("tests/measure/test_xbrl_p28_result.py", MY_PR_NAME)         # 順序の部品。門としては走らせない
OVERWRITTEN = sorted(k for k, v in _BEFORE_MODULES.items() if sys.modules.get(k) is not v)


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


# ================================================================== 字で決めた形
PRED_IDS = (u"UM3-A1", u"UM3-A2", u"UM3-A3", u"UM3-A4", u"UM3-A5", u"UM3-A6", u"UM3-A7", u"UM3-A8", u"UM3-A9",
            u"UM3-L1", u"UM3-L2", u"UM3-L3", u"UM3-L4", u"UM3-L5", u"UM3-L6", u"UM3-D1")
TOP_KEYS = (u"会社の数", u"回", u"数", u"会社ごと", u"席ごと", u"B の席ごと", u"読んだ便 UM2 の出力の sha256 の束ね", u"限界", u"欄の説明", u"予測")
RESULT_NAMES = (u"同じ", u"違う", u"無いのに在る", u"無いで同じ", u"無いで違う", u"分からない", u"答えなし", u"形が読めない")
CALC_NAMES = (u"同じ", u"違う", u"無い", u"分からない", u"答えなし", u"形が読めない", u"分母から外した")
CONF_NAMES = (u"高", u"中", u"低", u"読めない", u"なし")
B1_LABELS = (u"通す", u"通す(取り方は未確認)", u"止める", u"無いを受ける", u"B なし")
B2_LABELS = (u"在る", u"確認待ち", u"無い", u"保留", u"B なし")
#: 封 §5 の次の便の候補(封にそのまま在る。結果の文書はここに無い候補を足さない)
SEAL_CANDIDATE_COUNT = 5

#: 文書が肯定で書いてはいけない言い方。出た文は「言えない」の側に在る時だけ許す(言えないこと の段落の中の「」は許す)
AFFIRM_PHRASES = (u"実物の会計の素材で", u"普通の AI で足りる", u"Audit Core の方が正しい", u"人の確かめが要らない", u"型も検査も要らない", u"別の種類の AI でも同じ",
                  u"手がかりで良くなる", u"安定している", u"速い", u"安い")
NEGATIONS = (u"言えない", u"言わない", u"読まない", u"測れていない", u"測れなかった", u"確かめていない", u"書かない", u"並べるだけ")
WIN_WORDS = (u"勝ち", u"勝った", u"勝つ", u"圧勝", u"優れ", u"劣る", u"上回")
FORBIDDEN_WORDS = (u"精度", u"LLM より正確", u"世界で 1 社", u"金額", u"契約", u"税", u"USD", u"保証")
DOCID_FORM = re.compile(r"(?<![0-9A-Za-z])S[0-9A-Z]{7}(?![0-9A-Za-z])")
ECODE_FORM = re.compile(r"(?<![0-9A-Za-z])E\d{5}(?![0-9A-Za-z])")
DATE_FORM = re.compile(r"(?<![0-9])(?:19|20)\d{2}[-/.]\d{1,2}[-/.]\d{1,2}(?![0-9])|(?<![0-9])(?:19|20)\d{2}年\d{1,2}月")
SEAL_LOSS_SENTENCE = u"**先に負けと限界を書く。勝ち負けの文は書かない(封 §3)。**"


# ================================================================== 写し
def git_message(short):
    r = subprocess.run(["git", "-C", REPO, "log", "-1", "--format=%B", short], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.stdout.decode("utf-8")


class Ctx(object):
    u"""検査が見る写し。変異はこの写しを変える(木の file は変えない)。"""

    def __init__(self):
        self.rec = json.loads(read(RECORD_REL), object_pairs_hook=od)
        self.um2 = json.loads(read(UM2_RECORD_REL), object_pairs_hook=od)
        self.doc = read(DOC_REL)
        self.seal = read(SEAL_REL)
        self.defs = [json.loads(read(r), object_pairs_hook=od) for r in DEF_RELS]
        self.shas = od((rel, sha_file(rel)) for rel in SHA_PIN)
        self.msg_record = git_message(RECORD_COMMIT)
        self._cache = None

    def copy(self):
        c = Ctx.__new__(Ctx)
        c.rec = copy.deepcopy(self.rec)
        c.um2, c.doc, c.seal, c.defs = self.um2, self.doc, self.seal, self.defs
        c.shas = od(self.shas)
        c.msg_record = self.msg_record
        c._cache = None
        return c

    def expected(self):
        key = (json.dumps(self.rec, ensure_ascii=False, sort_keys=False), json.dumps(self.um2, ensure_ascii=False), self.seal)
        if self._cache is None or self._cache[0] != key:
            self._cache = (key, render(self))
        return self._cache[1]


# ================================================================== 記録の読み(script の関数を使わない)
def N(rec, key):
    return rec[u"数"][key]


def seat_key(k):
    i, r, p = k.split(u":")
    return i, r, int(p)


def seats_of(rec, period):
    return [(k, v) for k, v in rec[u"席ごと"].items() if seat_key(k)[2] == period]


def dirty_seats(rec):
    return [k for k, v in rec[u"席ごと"].items() if v[u"汚れの席"]]


def seal_pred_rows(seal):
    u"""封の予測の表の行 → {id: (予測, 外れ方)}。"""
    out = od()
    for ln in seal.splitlines():
        m = re.match(r"^\| (UM3-[A-Z][0-9]) \| (.*) \| (.*) \|$", ln)
        if m:
            out[m.group(1)] = (m.group(2), m.group(3))
    return out


def seal_candidates(seal):
    i = seal.index(u"## §5")
    return [l for l in seal[i:].splitlines() if re.match(r"^- \((?:i|ii|iii|iv|v|vi|vii)\) ", l)]


def judge(rec):
    u"""封 §2 の 16 本の当たり外れ({id: True=当たり/False=外れ/None=記録では決まらない})。境は封の字。集計の script の judge を使わずに決める。"""
    n = lambda k: N(rec, k)                                   # noqa: E731
    out = od()
    out[u"UM3-A1"] = n(u"期1:結果:同じ") + n(u"期1:結果:無いで同じ") >= 216 if n(u"期1:行の数") == 240 else None
    stopped = sum(n(u"掛け合わせ1:止める×" + x) for x in RESULT_NAMES)
    present = sum(n(u"掛け合わせ1:止める×" + x) for x in (u"同じ", u"違う", u"無いのに在る"))
    same = n(u"掛け合わせ1:止める×同じ")
    out[u"UM3-A2"] = (100 * present >= 90 * stopped and 100 * same >= 85 * present) if stopped else None
    wrong = n(u"期1:結果:違う") + n(u"期2:結果:違う") + n(u"期1:結果:無いのに在る") + n(u"期2:結果:無いのに在る")
    out[u"UM3-A3"] = wrong >= 1
    out[u"UM3-A4"] = n(u"期2:結果:同じ") + n(u"期2:結果:無いで同じ") >= 216 if n(u"期2:行の数") == 240 else None
    waiting = sum(n(u"掛け合わせ2:確認待ち×" + x) for x in RESULT_NAMES)
    out[u"UM3-A5"] = (100 * n(u"掛け合わせ2:確認待ち×同じ") >= 80 * waiting) if waiting else None
    out[u"UM3-A6"] = n(u"期1:結果:無いのに在る") + n(u"期2:結果:無いのに在る") >= 1
    out[u"UM3-A7"] = n(u"揺れ:期1:数値が違う行が在る社") >= 2
    high = n(u"自信:高×違う") + n(u"自信:高×無いのに在る")
    out[u"UM3-A8"] = (2 * high >= wrong) if wrong else None
    out[u"UM3-A9"] = (100 * n(u"関係:成り立つ本数") >= 95 * n(u"関係:見られる本数")) if n(u"関係:見られる本数") else None
    out[u"UM3-L1"] = n(u"過程:期1:最大の file に触れた席") >= 6
    out[u"UM3-L2"] = n(u"過程:期1:script を書いた席") >= 6
    out[u"UM3-L3"] = n(u"過程:期2:前の期の成果の道具を走らせた席") <= 3
    out[u"UM3-L4"] = n(u"過程:期2:道具の呼び出しの中央値の 2 倍") < n(u"過程:期1:道具の呼び出しの中央値の 2 倍")
    out[u"UM3-L5"] = n(u"過程:値の表を 2 回以上書いた席") >= 4
    out[u"UM3-L6"] = n(u"過程:汚れの席") == 0
    out[u"UM3-D1"] = n(u"資料:当たらない数の字が 1 つ以上の資料") >= 8
    return out


def verdict_word(v):
    return {True: u"当たり", False: u"外れ", None: u"記録では決まらない"}[v]


# ================================================================== 文書を記録と字から組み直す
def measured(rec):
    u"""§1 の表の実測の列(記録の数だけから組む)。"""
    n = lambda k: N(rec, k)                                   # noqa: E731
    stopped = sum(n(u"掛け合わせ1:止める×" + x) for x in RESULT_NAMES)
    present = sum(n(u"掛け合わせ1:止める×" + x) for x in (u"同じ", u"違う", u"無いのに在る"))
    waiting = sum(n(u"掛け合わせ2:確認待ち×" + x) for x in RESULT_NAMES)
    wrong = n(u"期1:結果:違う") + n(u"期2:結果:違う") + n(u"期1:結果:無いのに在る") + n(u"期2:結果:無いのに在る")
    ghost = n(u"期1:結果:無いのに在る") + n(u"期2:結果:無いのに在る")
    high = n(u"自信:高×違う") + n(u"自信:高×無いのに在る")
    seats1, seats2 = n(u"過程:期1:席の数"), n(u"過程:期2:席の数")
    return od([
        (u"UM3-A1", u"%d / %d" % (n(u"期1:結果:同じ") + n(u"期1:結果:無いで同じ"), n(u"期1:行の数"))),
        (u"UM3-A2", u"止めた行 %d・在る %d・同じ %d" % (stopped, present, n(u"掛け合わせ1:止める×同じ"))),
        (u"UM3-A3", u"%d / %d" % (wrong, n(u"期1:行の数") + n(u"期2:行の数"))),
        (u"UM3-A4", u"%d / %d" % (n(u"期2:結果:同じ") + n(u"期2:結果:無いで同じ"), n(u"期2:行の数"))),
        (u"UM3-A5", u"確認待ち %d・同じ %d" % (waiting, n(u"掛け合わせ2:確認待ち×同じ"))),
        (u"UM3-A6", u"%d(正解に `null` の行が無く、測れなかった)" % ghost),
        (u"UM3-A7", u"%d 社" % n(u"揺れ:期1:数値が違う行が在る社")),
        (u"UM3-A8", u"高 %d / %d" % (high, wrong)),
        (u"UM3-A9", u"成り立つ %d / 見られる %d" % (n(u"関係:成り立つ本数"), n(u"関係:見られる本数"))),
        (u"UM3-L1", u"%d / %d" % (n(u"過程:期1:最大の file に触れた席"), seats1)),
        (u"UM3-L2", u"%d / %d" % (n(u"過程:期1:script を書いた席"), seats1)),
        (u"UM3-L3", u"%d / %d" % (n(u"過程:期2:前の期の成果の道具を走らせた席"), seats2)),
        (u"UM3-L4", u"中央の値の 2 倍 1 期目 %d・2 期目 %d" % (n(u"過程:期1:道具の呼び出しの中央値の 2 倍"), n(u"過程:期2:道具の呼び出しの中央値の 2 倍"))),
        (u"UM3-L5", u"%d / %d" % (n(u"過程:値の表を 2 回以上書いた席"), seats1 + seats2)),
        (u"UM3-L6", u"%d / %d" % (n(u"過程:汚れの席"), seats1 + seats2)),
        (u"UM3-D1", u"%d / %d 本" % (n(u"資料:当たらない数の字が 1 つ以上の資料"), n(u"資料:本数"))),
    ])


def cross_row(rec, prefix, label):
    u"""掛け合わせの 1 行 → (同じ, 違う, ほか, 行の合計)。"""
    vals = od((x, rec[u"数"][u"%s:%s×%s" % (prefix, label, x)]) for x in RESULT_NAMES)
    total = sum(vals.values())
    return vals[u"同じ"], vals[u"違う"], total - vals[u"同じ"] - vals[u"違う"], total


def render(c):
    rec = c.rec
    n = lambda k: N(rec, k)                                   # noqa: E731
    j = judge(rec)
    hits = [i for i, v in j.items() if v is True]
    misses = [i for i, v in j.items() if v is False]
    pred = seal_pred_rows(c.seal)
    cands = seal_candidates(c.seal)
    meas = measured(rec)
    n_co, n_rounds = rec[u"会社の数"], len(rec[u"回"])
    s1, s2 = n(u"過程:期1:席の数"), n(u"過程:期2:席の数")
    S = s1 + s2
    n1, n2 = n(u"期1:行の数"), n(u"期2:行の数")
    wrong1, wrong2 = n(u"期1:結果:違う"), n(u"期2:結果:違う")
    wrong = wrong1 + wrong2
    ghost = n(u"期1:結果:無いのに在る") + n(u"期2:結果:無いのに在る")
    dirty = dirty_seats(rec)
    dirty_txt = u"・".join(u"社 %s・回 %s・%s 期目" % (seat_key(k)[0], seat_key(k)[1], seat_key(k)[2]) for k in dirty)
    stopped = cross_row(rec, u"掛け合わせ1", u"止める")[3]
    thru = [cross_row(rec, u"掛け合わせ1", x) for x in (u"通す", u"通す(取り方は未確認)")]
    thru_n = sum(r[3] for r in thru)
    thru_same, thru_wrong = sum(r[0] for r in thru), sum(r[1] for r in thru)
    no_row = cross_row(rec, u"掛け合わせ1", u"無いを受ける")
    waiting = cross_row(rec, u"掛け合わせ2", u"確認待ち")
    calc1 = sum(n(u"期1:計算:" + x) for x in CALC_NAMES)
    calc_bad = n(u"期1:計算:形が読めない") + n(u"期2:計算:形が読めない")
    uncovered = n(u"資料:当たらない数の字の数")
    middle1 = n(u"自信:中×同じ") + n(u"自信:中×違う")
    L = []
    w = L.append
    w(u"# 結果: 便 UM3 ― 便 UM2 と同じ素材を、型も検査も持たない普通の AI の席に資料まで作らせ、作る過程を便 UM2 の過程と並べた ― 作り物の素材 %d 社・2 期・この PC の席 %d で数えた ― 2026-11-24" % (n_co, S))
    w(u"")
    w(u"封 `%s`(commit %s)。頼みの紙 `%s`(封と同じ commit)。script `%s`・封の門 `%s`(commit %s。数えの直し %s)。"
      u"記録 `%s`(commit %s)。API は呼んでいない(費用は 0)。engine(`core/`・`adapters/`)は 0 行。"
      % (SEAL_REL, SEAL_COMMIT, BRIEF_REL, TALLY_REL, SEAL_GATE_REL, IMPL_COMMIT, FIX_COMMIT, RECORD_REL, RECORD_COMMIT))
    w(u"")
    w(u"この文書の §1・§2 の数は全部、記録から 1 つずつ読んだもの(結果の門が、記録の数と字で同じことを見る)。§3 は記録に欄の無い読みで、**司令塔(AI)の読み**。人の目ではない。"
      u"席の申告から取った所は「席の申告」、記録の独立監査の席(AI)が別の実装で数えた所は「監査の席の読み」と書く。結果の門は §3 の数を記録に縛らず、字で留めるだけ。")
    w(u"")
    w(u"台帳の番号(L-105・D-82・P-90)と試験の数は、別の枝に在る便 UM1 の結果と当たる。枝を寄せる時に、番号と試験の数を直す。")
    w(u"")
    w(SEAL_LOSS_SENTENCE)
    w(u"")
    w(u"- **A(型も検査も持たない席)が出して、正解と違った行は %d(%d 行のうち)。誰も止めていない。** 1 期目 %d・2 期目 %d。%d 行とも席の `自信` は `中` で、`高` と書いた行に「違う」は無い"
      u"(高×同じ %d・中×同じ %d・中×違う %d)。「無いのに在る」は %d。"
      % (wrong, n1 + n2, wrong1, wrong2, n(u"自信:中×違う"), n(u"自信:高×同じ"), n(u"自信:中×同じ"), n(u"自信:中×違う"), ghost))
    w(u"- **B(便 UM2)が 1 期目に止めた行(回ごとに数え、%d 回ぶんで %d。K3 %d・K4 %d)は、A が全部 `在る` と書き、%d 行とも正解と同じだった。** B の 2 期目の置き場が確認待ちの %d 行も、A は %d 行とも正解と同じ。"
      u"B は止めすぎて、普通の席が出せる数を資料に出せていない(封 §3 の決めで、B の負けとして頭に書く)。"
      % (n_rounds, stopped, n(u"掛け合わせ1:止める:K3×同じ"), n(u"掛け合わせ1:止める:K4×同じ"), cross_row(rec, u"掛け合わせ1", u"止める")[0], waiting[3], waiting[0]))
    w(u"- **同じ表に並べる(1 期目。%d 行 = %d 社 × %d 回 × 30 行)。** B が通した行(未確認を含む)%d: A は 同じ %d・違う %d。B が止めた行 %d: A は 同じ %d・違う %d。"
      u"B が止めた行のうち B の席の答えが正解どおりの行は 1 回ぶんで %d・正解と違う行 %d(便 UM2 の記録。%d 回ぶんに掛けた数は %d)。"
      u"B が「無い」を受けた行 %d: A は 同じ %d・違う %d。A が出して正しかった行 %d・A が出して違った行 %d。"
      u"B が通して数値が違った行は便 UM2 の記録で %d(B が「無い」を受けた行は、正解に値が在った行 ― 便 UM2 の結果の文書の頭)。"
      % (n1, n_co, n_rounds, thru_n, thru_same, thru_wrong, stopped, cross_row(rec, u"掛け合わせ1", u"止める")[0], cross_row(rec, u"掛け合わせ1", u"止める")[1],
         c.um2[u"数"][u"段 1:4 つの枠:正解どおり×止めた"], c.um2[u"数"][u"段 1:4 つの枠:正解と違う×止めた"], n_rounds,
         c.um2[u"数"][u"段 1:4 つの枠:正解どおり×止めた"] * n_rounds,
         no_row[3], no_row[0], no_row[1], n(u"期1:結果:同じ"), n(u"期1:結果:違う"), c.um2[u"数"][u"段 1:通したが数値が違う"]))
    w(u"- **予測 %d 本は 当たり %d・外れ %d。** 外れは %s。封も予測も、結果を見てから書き換えていない。司令塔は便 UM2 の結果を知って予測を書いた(封 §0)。"
      % (len(j), len(hits), len(misses), u"・".join(misses)))
    w(u"- **UM3-A6 は測れなかった。** 正解に `null` の行が 1 つも無く、「無いのに在る」「無いで同じ」は作りから 0 になる。封の字では外れ。「A は無い行に数を書かなかった」とは言えない。")
    w(u"- **記録は 1 度作り直した。** 1 回目の記録は独立監査で差し戻された: 席の発言の回が上限切れの合成メッセージを数え、汚れが席の最後の報告の中の字を path と数えていた。"
      u"数えを直し(%s)、記録を作り直した。行の照合・掛け合わせ・予測の当たり外れは 1 回目と同じ。封は直していない。" % FIX_COMMIT)
    w(u"- **UM3-L6 は外れ(汚れの席 %d / %d)。** %d 席とも 2 期目。汚れた呼び出し %d つは、席が自分の道具の出力の続き(この PC の道具が folder の外に置いた file)を読んだもの"
      u"(司令塔の読みと監査の席の読み。§3)。席が自分から外へ出た形ではないが、封の決め(渡した folder の外の path)では汚れ。正解の file・別の席の folder を開いた呼び出しは、%d つの中に無かった。"
      u"汚れの席を外した数も並べる(§2)。"
      % (n(u"過程:汚れの席"), S, len(dirty), n(u"過程:汚れた呼び出し"), n(u"過程:汚れた呼び出し")))
    w(u"- **計算の 3 行(a31〜a33)は、期ごとに %d 個のうち 同じ %d・形が読めない %d。** 形が読めない %d 個は、席が頼みの紙の「小数の字」でなく JSON の数で書いたもの(司令塔の数え。§3)。"
      u"封の決めで、直して読まない。記録は値が合うかを見ていない。監査の席の読みでは、数として読めば %d 個とも正解と同じ。"
      % (calc1, n(u"期1:計算:同じ"), n(u"期1:計算:形が読めない"), calc_bad, calc_bad))
    w(u"- **資料の中の数の字 %d のうち、値の表のどれにも当たらない数の字は %d。%d 本の資料の全部に 1 つ以上在る。** 粗い数。1 つずつ読んでいない。「資料が正しい」「資料が誤っている」のどちらも言わない。"
      % (n(u"資料:数の字の数"), uncovered, n(u"資料:本数")))
    w(u"- **過程の数は、会話の記録に残った道具の呼び出しだけ。** 汚れの数えには取りこぼす形と数え過ぎる形の両方が在り、実際の席の数は記録の数より多いとも少ないとも言えない(記録の `限界` の欄)。"
      u"素材の file に「触れた」は呼び出しに path の字が出たかで数える下限で、席が script の中で開いた file は拾わない。")
    w(u"- **「前の期の成果の道具を走らせた席 %d / %d」は、封の字(その path のまま走らせる)での数。** 監査の席の読みでは、2 期目の 8 席とも前の期と同じ名の道具を自分の folder に持ち、"
      u"うち 2 席は前の期の道具を写した、中身が byte で同じ file を走らせた。写して走らせた席を数えに入れるかは封に無く、入れていない。"
      % (n(u"過程:期2:前の期の成果の道具を走らせた席"), s2))
    w(u"- **席。** A の席 %d(%d 社 × %d 回 × 2 期)・取り直し 0。2 期目の 8 席のうち 6 席は、成果を書き終えた後、最後の返事の前に session の上限で切れた(司令塔の数えと監査の席の読み。記録に欄は無い)。"
      u"6 席とも `値の表.json`・`資料.md`・`作業の記録.md` は在り、封の決め(値の表を書かずに終わった時だけ取り直す)で取り直していない。全部同じ種類の subagent で、互いに独立ではない(model の名は書かない)。"
      % (S, n_co, n_rounds))
    w(u"- **素材と正解。** 素材は便 UM2 の作り物の 4 社・2 期。正解は素材を作った席が書いたもので、独立に確かめていない。A の席はこの repo の文脈を持ち、頼みの紙で値の表・自信・作業の記録を書かされた。何も言われない席の振る舞いではない。")
    w(u"- **言えないこと。** 「実物の会計の素材で」「普通の AI で足りる」「Audit Core の方が正しい」「人の確かめが要らない」「別の種類の AI でも同じ」「手がかりで良くなる」(手がかりは確かめていない)。"
      u"「A は安定している/いない」(2 回だけ)。「速い」「安い」(秒は並べるだけ)。")
    w(u"")
    w(u"## §1 予測の当たり外れ(封を書いた司令塔が立てた)")
    w(u"")
    w(u"当たり外れは記録の数だけで決め、境の数は結果を見て動かしていない。")
    w(u"")
    w(u"| # | 予測(封の字) | 封の外れ方 | 実測(記録) | 判定 |")
    w(u"|---|---|---|---|---|")
    for i in PRED_IDS:
        p, o = pred[i]
        w(u"| %s | %s | %s | %s | %s |" % (i, p, o, meas[i], verdict_word(j[i])))
    w(u"")
    w(u"## §2 数(記録)")
    w(u"")
    w(u"### 行ごとの照合(A の結果)")
    w(u"")
    w(u"| 期 | 行の数 | 同じ | 違う | 無いのに在る | 無いで同じ | 無いで違う | 分からない | 答えなし | 形が読めない |")
    w(u"|---|---|---|---|---|---|---|---|---|---|")
    for p, name in ((1, u"1 期目"), (2, u"2 期目")):
        w(u"| %s | %d | %s |" % (name, n(u"期%d:行の数" % p), u" | ".join(u"%d" % n(u"期%d:結果:%s" % (p, x)) for x in RESULT_NAMES)))
    w(u"")
    w(u"- 汚れの席を外した数: 1 期目 行の数 %d・同じ %d・違う %d。2 期目 行の数 %d・同じ %d・違う %d。"
      % (n(u"汚れの席を外した:期1:行の数"), n(u"汚れの席を外した:期1:結果:同じ"), n(u"汚れの席を外した:期1:結果:違う"),
         n(u"汚れの席を外した:期2:行の数"), n(u"汚れの席を外した:期2:結果:同じ"), n(u"汚れの席を外した:期2:結果:違う")))
    w(u"- 会社ごと(1 期目の 同じ / 行の数・2 期目の 同じ / 行の数): %s。"
      % u"。".join(u"社 %s %d / %d・%d / %d" % (i, r[u"期1:結果:同じ"], r[u"期1:行の数"], r[u"期2:結果:同じ"], r[u"期2:行の数"]) for i, r in rec[u"会社ごと"].items()))
    w(u"- 値の表: 読めた %d・読めない %d・無し %d・重複の行 %d。正解が読めない行 %d。"
      % (n(u"値の表:読めた"), n(u"値の表:読めない"), n(u"値の表:無し"), n(u"値の表:重複の行"), n(u"正解が読めない行")))
    w(u"")
    w(u"### B との掛け合わせ")
    w(u"")
    w(u"| 1 期目の B の判定 | A 同じ | A 違う | A ほか |")
    w(u"|---|---|---|---|")
    for label, shown in ((u"通す", u"通す"), (u"通す(取り方は未確認)", u"通す(取り方は未確認)"),
                         (u"止める", u"止める(K3 %d・K4 %d)" % (n(u"掛け合わせ1:止める:K3×同じ"), n(u"掛け合わせ1:止める:K4×同じ"))), (u"無いを受ける", u"無いを受ける")):
        r = cross_row(rec, u"掛け合わせ1", label)
        w(u"| %s | %d | %d | %d |" % (shown, r[0], r[1], r[2]))
    w(u"")
    w(u"| 2 期目の B の置き場 | A 同じ | A 違う | A ほか |")
    w(u"|---|---|---|---|")
    for label in (u"在る", u"確認待ち", u"無い", u"保留"):
        r = cross_row(rec, u"掛け合わせ2", label)
        w(u"| %s | %d | %d | %d |" % (label, r[0], r[1], r[2]))
    w(u"")
    w(u"- 読んだ便 UM2 の出力の file は %d 個。" % n(u"読んだ便 UM2 の出力の file の数"))
    w(u"")
    w(u"### 揺れ・自信・計算・関係・資料")
    w(u"")
    w(u"- 揺れ(回 a と回 b。期ごとに %d 行): %s。"
      % (n(u"揺れ:期1:行の数"), u"。".join(u"%d 期目 結果の名が同じ %d・`在る` どうし %d・そのうち数値が同じ %d・違う %d・数値が違う行が在る社 %d"
                                         % (p, n(u"揺れ:期%d:結果の名が同じ" % p), n(u"揺れ:期%d:在るどうし" % p), n(u"揺れ:期%d:在るどうしで数値が同じ" % p),
                                            n(u"揺れ:期%d:在るどうしで数値が違う" % p), n(u"揺れ:期%d:数値が違う行が在る社" % p)) for p in (1, 2))))
    w(u"- 自信 × 結果: 高×同じ %d・中×同じ %d・中×違う %d。低・読めない・なしは 0。" % (n(u"自信:高×同じ"), n(u"自信:中×同じ"), n(u"自信:中×違う")))
    w(u"- 計算の 3 行: %s。"
      % u"。".join(u"%d 期目 同じ %d・形が読めない %d・違う %d・分母から外した %d"
                   % (p, n(u"期%d:計算:同じ" % p), n(u"期%d:計算:形が読めない" % p), n(u"期%d:計算:違う" % p), n(u"期%d:計算:分母から外した" % p)) for p in (1, 2)))
    w(u"- 関係: R1 成り立つ %d / 見られる %d・R2 %d / %d・R3 %d / %d。見られない本数 %d。"
      % (n(u"関係:R1:成り立つ本数"), n(u"関係:R1:見られる本数"), n(u"関係:R2:成り立つ本数"), n(u"関係:R2:見られる本数"),
         n(u"関係:R3:成り立つ本数"), n(u"関係:R3:見られる本数"), n(u"関係:見られない本数")))
    w(u"- 資料: 本数 %d・字の数 %d・数の字の数 %d・当たらない数の字の数 %d・当たらない数の字が 1 つ以上の資料 %d。"
      % (n(u"資料:本数"), n(u"資料:字の数"), n(u"資料:数の字の数"), uncovered, n(u"資料:当たらない数の字が 1 つ以上の資料")))
    w(u"")
    w(u"### 作る過程(A の %d 席。会話の記録から)" % S)
    w(u"")
    w(u"| | 1 期目の %d 席 | 2 期目の %d 席 |" % (s1, s2))
    w(u"|---|---|---|")
    for label, key in ((u"道具の呼び出しの数", u"道具の呼び出しの数"), (u"道具の呼び出しの中央値の 2 倍", u"道具の呼び出しの中央値の 2 倍"),
                       (u"script を書いた席", u"script を書いた席"), (u"最大の file に触れた席", u"最大の file に触れた席"),
                       (u"前の期の成果の道具を走らせた席", u"前の期の成果の道具を走らせた席")):
        shown = {u"道具の呼び出しの中央値の 2 倍": u"道具の呼び出しの中央の値の 2 倍", u"前の期の成果の道具を走らせた席": u"前の期の成果の道具をその path のまま走らせた席"}.get(label, label)
        w(u"| %s | %d | %d |" % (shown, n(u"過程:期1:" + key), n(u"過程:期2:" + key)))
    w(u"")
    w(u"- %d 席の合計: 道具 Bash %d・Read %d・SubagentHandback %d。script を書いた数 %d・python を走らせた数 %d・道具が誤りを返した数 %d・値の表を 2 回以上書いた席 %d。"
      % (S, n(u"過程:道具:Bash"), n(u"過程:道具:Read"), n(u"過程:道具:SubagentHandback"), n(u"過程:script を書いた数"), n(u"過程:python を走らせた数"),
         n(u"過程:道具が誤りを返した数"), n(u"過程:値の表を 2 回以上書いた席")))
    w(u"- 2 期目: 前の期の成果の path が出た呼び出し %d・前の期の素材の path が出た呼び出し %d。" % (n(u"過程:前の期の成果の path が出た呼び出し"), n(u"過程:前の期の素材の path が出た呼び出し")))
    w(u"- 汚れ: 汚れの席 %d・汚れた呼び出し %d。席の発言の回は %d 席とも 0。" % (n(u"過程:汚れの席"), n(u"過程:汚れた呼び出し"), len(rec[u"席ごと"])))
    w(u"- 秒の合計 %d(秒が無い席 %d)。数えた席 %d・数えられない席 %d。" % (n(u"過程:秒の合計"), n(u"過程:秒が無い席"), n(u"過程:数えた席"), n(u"過程:数えられない席")))
    w(u"")
    w(u"### B の 1 期目の席(便 UM2 の材料を書く席 %d。同じ script で数えた)" % n(u"B の席:席の数"))
    w(u"")
    w(u"- 席の数 %d・数えた席 %d・道具の呼び出しの数 %d・script を書いた席 %d・python を走らせた数 %d・道具が誤りを返した数 %d・最大の file に触れた席 %d・汚れの席 %d・秒の合計 %d。"
      % (n(u"B の席:席の数"), n(u"B の席:数えた席"), n(u"B の席:道具の呼び出しの数"), n(u"B の席:script を書いた席"), n(u"B の席:python を走らせた数"),
         n(u"B の席:道具が誤りを返した数"), n(u"B の席:最大の file に触れた席"), n(u"B の席:汚れの席"), n(u"B の席:秒の合計")))
    w(u"- B の席は型と指示書を渡されて材料の束だけを書く。A の席は資料・値の表・作業の記録まで書く。作りが違うので、呼び出しの数と秒は並べるだけで、比べる文は書かない。B の 2 期目は script で、過程の数は無い。")
    w(u"")
    w(u"## §3 記録に欄の無い読み(司令塔(AI)の読み。結果の門は記録に縛らず、字で留めるだけ)")
    w(u"")
    w(u"出どころは、script の `--digest` が書いた抜き書き(席ごとの道具の呼び出しの順・席の発言・`作業の記録.md`・値の表の `出どころ`)と、席の値の表。"
      u"手がかりは、この 4 社では確かめていない(封 §1-7)。手がかりごとに (a) 見た席 (b) 当たる §1・§2 の数 (c) 1〜7 段のどこの話か を書く。")
    w(u"")
    w(u"### 違った行・止めた行の型分け(司令塔の型分け)")
    w(u"")
    w(u"- **A が正解と違う %d 行: 「正解の側の誤りか決めの違い」%d・「席の誤り」0・「どちらとも決められない」0。** 2 行とも社 1・回 b の a30(期末の従業員数)で、1 期目と 2 期目。"
      u"回 b の席は役員を含めて数え、回 a の席と正解は役員を除いて数えた。定義表は役員を数えるかを書いていない。回 b の席は両方の数を資料に書き、`自信` を `中` にした。"
      u"2 期目の席は、1 期目の数え方を「年をまたいで変えない」として引き継いだ(席の申告)。" % (wrong, wrong))
    w(u"- **B が止めて A が出した %d 行: A の結果は %d 行とも「同じ」で、違いの型分けの対象が無い。** B が止めた理由は便 UM2 の規則の名(K3 %d・K4 %d)まで。%d 行を 1 行ずつは読んでいない(未了)。"
      % (stopped, cross_row(rec, u"掛け合わせ1", u"止める")[0], n(u"掛け合わせ1:止める:K3×同じ"), n(u"掛け合わせ1:止める:K4×同じ"), stopped))
    w(u"")
    w(u"### 手がかり")
    w(u"")
    w(u"1. **定義表に書いていない決め(誰を数えるか)が、ただ 1 つの違いとただ 1 つの揺れを作った。** (a) 社 1・回 a と回 b・1 期目と 2 期目。(b) 違う %d / %d・揺れ 期ごとに %d / %d・中×違う %d。"
      u"司令塔の数え: %d 枚の値の表の全部が a30 を `中` と書いた。(c) 段 2(定義): 人の数・件数の行に「誰を数えるか」を書く。"
      % (wrong, n1 + n2, n(u"揺れ:期1:在るどうしで数値が違う"), n(u"揺れ:期1:行の数"), n(u"自信:中×違う"), n(u"値の表:読めた")))
    w(u"2. **席の `自信` は、違った 2 行を 2 行とも `中` の側に置いた。** (a) %d 席。(b) 高×同じ %d・中×同じ %d・中×違う %d。`中` の %d 行は a30 が 16・a08 が 4(司令塔の数え)。"
      u"(c) 段 5(照合): 席が `中` と書いた行を、止めるのでなく「人が先に見る行」に回す。2 回・4 社だけの数で、`高` に違いが出ないとは言えない。"
      % (S, n(u"自信:高×同じ"), n(u"自信:中×同じ"), n(u"自信:中×違う"), middle1))
    w(u"3. **B が型(見出し・期の読み)で止めた行を、A は帳票どうしの突き合わせで出していた。** (a) %d 席の `作業の記録.md`(席の申告): 全部の席が決算書を数の出どころに選び、"
      u"仕訳帳・試算表・月次・台帳・名簿などを「照らす側」に使った。(b) 止める×同じ %d・関係 %d / %d・script を書いた席 %d / %d。"
      u"(c) 段 5(照合): 素材の中の別の帳票と合うことを、検査の規則として持つ(型で止めた行を、突き合わせが合えば通す道)。席の突き合わせが正しかったかは、正解との一致でしか見ていない。"
      % (S, cross_row(rec, u"掛け合わせ1", u"止める")[0], n(u"関係:成り立つ本数"), n(u"関係:見られる本数"),
         n(u"過程:期1:script を書いた席") + n(u"過程:期2:script を書いた席"), S))
    w(u"4. **2 期目の席は、前の期の道具をそのままは走らせず、自分の folder に写すか書き直して使った。道具は持ち越せたが、手で直す形だった。** (a) 2 期目の %d 席。"
      u"席の申告: 道具に年・日付・借入の番号が字で入っていた。出どころの選び・数え方・章立ては前の期から引き継ぎ、前の期の数は今年の素材の前期の欄から取り直して、前の期の成果と照らした。"
      u"監査の席の読み: 8 席とも前の期と同じ名の道具を持ち、うち 2 席(社 2 の回 a・回 b)は写した中身が同じ道具を走らせた。"
      u"(b) 前の期の成果の道具をその path のまま走らせた席 %d / %d・script を書いた席 %d / %d・前の期の成果の path が出た呼び出し %d・道具の呼び出し %d → %d(UM3-L4 外れ。呼び出しは減っていない)。"
      u"(c) 段 6(蓄積): 持ち越す道具は期・日付・番号を字で持たず引数にする。あわせて「どの帳票のどの行を・どう数えるか」の決めを、道具と別に持ち越す。"
      % (s2, n(u"過程:期2:前の期の成果の道具を走らせた席"), s2, n(u"過程:期2:script を書いた席"), s2, n(u"過程:前の期の成果の path が出た呼び出し"),
         n(u"過程:期1:道具の呼び出しの数"), n(u"過程:期2:道具の呼び出しの数")))
    w(u"5. **決めの持ち越しは、違いも運んだ。** (a) 社 1・回 b・2 期目。(b) 2 期目の 違う %d。便 UM2 の UM2-Q2(持ち越して通した行の 1 行が違った)と同じ向き。"
      u"(c) 段 6(蓄積): 持ち越す決めに「人が確かめたか」の札を持たせ、確かめていない決めは 2 期目も「人が先に見る行」に置く。" % wrong2)
    w(u"6. **新しい出来事が在った年に、前の期の作りの穴が表に出た。** (a) 社 2・回 a・2 期目: 新しい科目が出て、前の期の道具の分類の誤りに席が気づいた。"
      u"社 3・回 a・2 期目: 前の期の列の並びを使い回して、照らす所が 1 度壊れた(どちらも席の申告)。(b) 読みだけ。"
      u"(c) 段 6・段 5: 持ち越した取り方に、前の期に無かった科目・行が当たった時は止める。")
    w(u"7. **小数の行は、頼みの紙に「小数の字」と書いても、3 席が JSON の数で書いた。** (a) 社 2・回 a、社 3・回 a、社 4・回 b の 1 期目と 2 期目(6 枚の値の表)。"
      u"(b) 計算の 形が読めない 期ごとに %d。司令塔の数え: a32・a33 が数の %d 個。a31 は整数の数が 6 枚で、読めた。"
      u"(c) 段 3(読み込み): 受け口は、形で断った行を理由つきで席に返す。A には受け口が無く、席は断られないまま終えた。" % (n(u"期1:計算:形が読めない"), calc_bad))
    w(u"8. **資料には、値の表の外の数が多い。** (a) %d 本。(b) 当たらない数の字 %d / %d・%d / %d 本。席の申告では、差・比・前の期の数・内訳を資料に書いた。1 つずつ読んでいない。"
      u"(c) 段 7(生成): 資料に出す数は、値の表の行か、行から式で出した数に限る(B の作り)。A の作りでは、資料の数のどれが確かめた数かを、資料の側から辿れない。"
      % (n(u"資料:本数"), uncovered, n(u"資料:数の字の数"), n(u"資料:当たらない数の字が 1 つ以上の資料"), n(u"資料:本数")))
    w(u"9. **席は、確かめた範囲を自分で書いた。** (a) 複数の席の `作業の記録.md`(席の申告): 「帳票どうしは合うが、帳簿の外では確かめていない」。(b) 読みだけ。"
      u"(c) 段 7(生成): 資料に「何と何を照らしたか」の欄を持つ。")
    w(u"")
    w(u"### 測り方の読み")
    w(u"")
    w(u"- 汚れの %d つ: %sは、長い道具の出力の続きを、この PC の道具が folder の外に置いた file から読んだ(司令塔の読みと監査の席の読み)。"
      % (len(dirty), dirty_txt.replace(u"・社", u"と社")))
    w(u"- UM3-L5(値の表を 2 回以上書く席)は %d。数えは script を走らせ直して書いた回を拾わない(記録の `限界`)。監査の席の読みでは、script の走らせ直しで値の表を 2 回書いた席が 1 つ在り、"
      u"もう 1 つは疑い。どちらを入れても封の境(4 以上)に届かない。" % n(u"過程:値の表を 2 回以上書いた席"))
    w(u"- 2 期目に「最大の file に触れた席」が %d / %d なのは、path の字が呼び出しに出たかの数え(下限)。監査の席の読みでは、残りの 2 席も script の中で仕訳帳を読んでいて、8 / 8。"
      % (n(u"過程:期2:最大の file に触れた席"), s2))
    w(u"- script を書いた数 %d は、sed の出力を道具の file へ流して作った 1 つを拾っていない(監査の席の読みでは 66)。" % n(u"過程:script を書いた数"))
    w(u"- 道具の呼び出しの数は、席の最後の報告(SubagentHandback)も 1 と数える。監査の席の読みでは、これを外しても中央の値は 1 期目 8・2 期目 10 で、UM3-L4 は外れのまま。")
    w(u"- 資料の「当たらない数の字」は、数の字と月・日の字の間に空白が在る形を月日として外さず数える(記録の `限界`)。監査の席の読みでは、これを外すと数の字 1383・当たらない数の字 565。UM3-D1 は変わらない。")
    w(u"")
    w(u"## §4 門")
    w(u"")
    w(u"- 封の門 `%s`。結果の門 `%s`(この文書の全部の行を、記録と字から組み直して照らす。変異で赤くなることを見た)。" % (SEAL_GATE_REL, GATE_REL))
    w(u"- 全体の suite は、この枝の頭では走らせていない。")
    w(u"")
    w(u"## §5 次の便の候補(封 §5 に在るものだけ。結果の文書はここに無い候補を足さない)")
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


def recount_problems(c):
    u"""記録の足し算・分母・恒等式を、集計の script の関数を使わずに数え直す。"""
    rec = c.rec
    if list(rec) != list(TOP_KEYS):
        return [u"記録の頂の鍵が違う: %s" % list(rec)]
    out = []
    n = rec[u"数"]
    g = lambda k: n[k]                                        # noqa: E731

    def eq(a, b, what):
        if a != b:
            out.append(u"%s: %r と %r" % (what, a, b))

    nco = rec[u"会社の数"]
    eq(nco, 4, u"会社の数")
    eq(rec[u"回"], [u"a", u"b"], u"回")
    eq(sorted(rec[u"会社ごと"]), [u"1", u"2", u"3", u"4"], u"会社ごとの鍵")
    seats = rec[u"席ごと"]
    eq(len(seats), nco * 2 * 2, u"席ごとの本数 = 社 × 回 × 期")
    eq(sorted(seats), sorted(u"%d:%s:%d" % (i, r, p) for i in range(1, nco + 1) for r in (u"a", u"b") for p in (1, 2)), u"席ごとの鍵")
    # 結果の名の和・会社ごと
    for p in (1, 2):
        eq(g(u"期%d:行の数" % p), nco * len(rec[u"回"]) * 30, u"期%d の行の数 = 社 × 回 × 30" % p)
        eq(sum(g(u"期%d:結果:%s" % (p, x)) for x in RESULT_NAMES), g(u"期%d:行の数" % p), u"期%d の結果の名の和 = 行の数" % p)
        for x in RESULT_NAMES:
            eq(sum(r.get(u"期%d:結果:%s" % (p, x), 0) for r in rec[u"会社ごと"].values()), g(u"期%d:結果:%s" % (p, x)), u"会社ごとの和 期%d %s" % (p, x))
            eq(sum(v[u"結果:" + x] for k, v in seats_of(rec, p)), g(u"期%d:結果:%s" % (p, x)), u"席ごとの和 期%d %s" % (p, x))
    for i, r in rec[u"会社ごと"].items():
        eq(r[u"期1:行の数"], 60, u"会社 %s の期1 の行の数" % i)
        eq(r[u"期2:行の数"], 60, u"会社 %s の期2 の行の数" % i)
    for x in CONF_NAMES:
        for y in RESULT_NAMES:
            eq(sum(r.get(u"自信:%s×%s" % (x, y), 0) for r in rec[u"会社ごと"].values()), g(u"自信:%s×%s" % (x, y)), u"会社ごとの自信 %s×%s" % (x, y))
    for y in RESULT_NAMES:
        eq(sum(g(u"自信:%s×%s" % (x, y)) for x in CONF_NAMES), g(u"期1:結果:" + y) + g(u"期2:結果:" + y), u"自信の和 = 結果の名の和 %s" % y)
    eq(sum(r.get(u"自信:高×同じ", 0) + r.get(u"自信:中×同じ", 0) + r.get(u"自信:中×違う", 0) for r in rec[u"会社ごと"].values()), g(u"期1:行の数") + g(u"期2:行の数"), u"会社ごとの自信の和 = 行の数")
    # B との掛け合わせ
    for pfx, labels, period, extra in ((u"掛け合わせ1", B1_LABELS, 1, u"止める"), (u"掛け合わせ2", B2_LABELS, 2, None)):
        for y in RESULT_NAMES:
            eq(sum(g(u"%s:%s×%s" % (pfx, lab, y)) for lab in labels), g(u"期%d:結果:%s" % (period, y)), u"%s の和 = 期%d %s" % (pfx, period, y))
    eq(g(u"掛け合わせ1:止める:K3×同じ") + g(u"掛け合わせ1:止める:K4×同じ"), g(u"掛け合わせ1:止める×同じ"), u"止める K3 + K4 = 止める×同じ")
    # 揺れ
    for p in (1, 2):
        eq(g(u"揺れ:期%d:行の数" % p), nco * 30, u"揺れ期%d の行の数" % p)
        eq(g(u"揺れ:期%d:在るどうしで数値が同じ" % p) + g(u"揺れ:期%d:在るどうしで数値が違う" % p), g(u"揺れ:期%d:在るどうし" % p), u"揺れ期%d: 同じ + 違う = 在るどうし" % p)
        if g(u"揺れ:期%d:在るどうしで数値が違う" % p) < g(u"揺れ:期%d:数値が違う行が在る社" % p):
            out.append(u"数値が違う行が在る社が違う行の数より多い: 期%d" % p)
        eq(sum(1 for r in rec[u"会社ごと"].values() if r.get(u"期%d:結果:違う" % p, 0)), g(u"揺れ:期%d:数値が違う行が在る社" % p), u"期%d の違う行が在る社" % p)
    # 計算・関係・資料
    for p in (1, 2):
        eq(sum(g(u"期%d:計算:%s" % (p, x)) for x in CALC_NAMES), nco * 2 * 3, u"期%d の計算の和 = 社 × 回 × 3" % p)
    for r in (u"R1", u"R2", u"R3"):
        eq(g(u"関係:%s:見られる本数" % r), nco * 2 * 2, u"関係 %s の見られる本数 = 社 × 回 × 期" % r)
        if g(u"関係:%s:成り立つ本数" % r) > g(u"関係:%s:見られる本数" % r):
            out.append(u"関係 %s: 成り立つが見られるより多い" % r)
    eq(sum(g(u"関係:%s:成り立つ本数" % r) for r in (u"R1", u"R2", u"R3")), g(u"関係:成り立つ本数"), u"関係の成り立つ本数の和")
    eq(sum(g(u"関係:%s:見られる本数" % r) for r in (u"R1", u"R2", u"R3")), g(u"関係:見られる本数"), u"関係の見られる本数の和")
    eq(g(u"関係:見られる本数") + g(u"関係:見られない本数"), nco * 2 * 2 * 3, u"関係の本数 = 社 × 回 × 期 × 3")
    eq(g(u"値の表:読めた") + g(u"値の表:読めない") + g(u"値の表:無し"), len(seats), u"値の表の和 = 席")
    eq(g(u"資料:本数") + g(u"資料:なし") + g(u"資料:値の表が読めない資料"), len(seats), u"資料の和 = 席")
    if not g(u"資料:当たらない数の字の数") <= g(u"資料:数の字の数") <= g(u"資料:字の数"):
        out.append(u"資料の字の数の大小が合わない")
    if g(u"資料:当たらない数の字が 1 つ以上の資料") > g(u"資料:本数"):
        out.append(u"当たらない数の字が在る資料が本数より多い")
    # 過程(席ごと → 数)
    eq(g(u"過程:数えた席") + g(u"過程:数えられない席"), len(seats), u"過程の席の和")
    eq(sum(v[u"数えた"] for v in seats.values()), g(u"過程:数えた席"), u"席ごとの数えた席")
    for p in (1, 2):
        ss = seats_of(rec, p)
        eq(g(u"過程:期%d:席の数" % p), len(ss), u"期%d の席の数" % p)
        eq(sum(v[u"道具の呼び出し"] for k, v in ss), g(u"過程:期%d:道具の呼び出しの数" % p), u"期%d の道具の呼び出しの和" % p)
        eq(sum(v[u"最大の file に触れた"] for k, v in ss), g(u"過程:期%d:最大の file に触れた席" % p), u"期%d の最大の file に触れた席" % p)
        eq(sum(1 for k, v in ss if v[u"script を書いた数"] > 0), g(u"過程:期%d:script を書いた席" % p), u"期%d の script を書いた席" % p)
        eq(sum(v[u"前の期の成果の道具を走らせた"] for k, v in ss), g(u"過程:期%d:前の期の成果の道具を走らせた席" % p), u"期%d の前の期の成果の道具を走らせた席" % p)
        calls = sorted(v[u"道具の呼び出し"] for k, v in ss)
        if len(calls) % 2 == 0:
            eq(calls[len(calls) // 2 - 1] + calls[len(calls) // 2], g(u"過程:期%d:道具の呼び出しの中央値の 2 倍" % p), u"期%d の中央値の 2 倍" % p)
        eq(g(u"過程:期%d:数えられない席" % p), 0, u"期%d の数えられない席" % p)
        eq(g(u"過程:期%d:資料:なし" % p), 0, u"期%d の資料なし" % p)
    for key_n, key_s in ((u"過程:script を書いた数", u"script を書いた数"), (u"過程:python を走らせた数", u"python を走らせた数"), (u"過程:道具が誤りを返した数", u"道具が誤りを返した数"),
                         (u"過程:前の期の成果の path が出た呼び出し", u"前の期の成果の path が出た呼び出し"), (u"過程:前の期の素材の path が出た呼び出し", u"前の期の素材の path が出た呼び出し"),
                         (u"過程:汚れた呼び出し", u"汚れた呼び出し"), (u"過程:汚れの席", u"汚れの席"), (u"過程:秒の合計", u"秒")):
        eq(sum(v[key_s] for v in seats.values()), g(key_n), u"席ごとの和 " + key_n)
    eq(g(u"過程:道具:Bash") + g(u"過程:道具:Read") + g(u"過程:道具:SubagentHandback"), g(u"過程:期1:道具の呼び出しの数") + g(u"過程:期2:道具の呼び出しの数"), u"道具の名ごとの和 = 呼び出しの数")
    eq(sum(1 for v in seats.values() if v[u"値の表を書いた回数"] >= 2), g(u"過程:値の表を 2 回以上書いた席"), u"値の表を 2 回以上書いた席")
    eq(sum(v[u"書き直した"] for v in seats.values()), g(u"過程:値の表を 2 回以上書いた席"), u"書き直した席 = 値の表を 2 回以上書いた席")
    for k, v in seats.items():
        if v[u"汚れた呼び出し"] and not v[u"汚れの席"]:
            out.append(u"汚れた呼び出しが在るのに汚れの席でない: " + k)
        if v[u"汚れの席"] and not v[u"汚れた呼び出し"]:
            out.append(u"汚れの席なのに汚れた呼び出しが無い: " + k)
        if not v[u"素材の file のうち 2 回以上の数"] <= v[u"素材の file のうち path が出た数"] <= v[u"素材の file の数"]:
            out.append(u"素材の file の数の大小が合わない: " + k)
    for i in range(1, nco + 1):
        eq(len(set(seats[u"%d:%s:%d" % (i, r, p)][u"素材の file の数"] for r in (u"a", u"b") for p in (1, 2))), 1, u"社 %d の素材の file の数は席が違っても同じ" % i)
    # 汚れの席を外した数 = 全体 - 汚れの席の分
    for p in (1, 2):
        dirty_p = [v for k, v in seats_of(rec, p) if v[u"汚れの席"]]
        eq(g(u"汚れの席を外した:期%d:行の数" % p), g(u"期%d:行の数" % p) - 30 * len(dirty_p), u"汚れの席を外した期%d の行の数" % p)
        for x in RESULT_NAMES:
            eq(g(u"汚れの席を外した:期%d:結果:%s" % (p, x)), g(u"期%d:結果:%s" % (p, x)) - sum(v[u"結果:" + x] for v in dirty_p), u"汚れの席を外した期%d %s" % (p, x))
    # B の席
    bs = rec[u"B の席ごと"]
    eq(sorted(bs), [u"1", u"2", u"3", u"4"], u"B の席ごとの鍵")
    eq(g(u"B の席:席の数"), len(bs), u"B の席の数")
    eq(g(u"B の席:数えた席") + g(u"B の席:数えられない席") + g(u"B の席:記録が無い席"), len(bs), u"B の席の和")
    for key_n, key_s in ((u"B の席:道具の呼び出しの数", u"道具の呼び出し"), (u"B の席:python を走らせた数", u"python を走らせた数"), (u"B の席:道具が誤りを返した数", u"道具が誤りを返した数"),
                         (u"B の席:最大の file に触れた席", u"最大の file に触れた"), (u"B の席:汚れの席", u"汚れの席"), (u"B の席:秒の合計", u"秒")):
        eq(sum(v[key_s] for v in bs.values()), g(key_n), u"B の席ごとの和 " + key_n)
    eq(sum(1 for v in bs.values() if v[u"script を書いた数"] > 0), g(u"B の席:script を書いた席"), u"B の script を書いた席")
    for key_n in (u"B の席:秒が無い席", u"定義表が読めない", u"正解が読めない社", u"正解が読めない行"):
        eq(g(key_n), 0, key_n)
    for i, v in bs.items():
        eq(v[u"数えた"], 1, u"B の席 %s の数えた" % i)
        eq(v[u"最初に値の表を書くまでの呼び出しが無い"], 1, u"B の席 %s は値の表を書かない" % i)
        for zero in (u"席の発言の回", u"値の表を書いた回数", u"書き直した", u"資料を書いた回数", u"前の期の成果の path が出た呼び出し", u"前の期の成果の道具を走らせた",
                     u"前の期の素材の path が出た呼び出し", u"汚れた呼び出し"):
            eq(v[zero], 0, u"B の席 %s の %s" % (i, zero))
        eq(v[u"素材の file の数"], seats[u"%s:a:1" % i][u"素材の file の数"], u"B の席 %s の素材の file の数は同じ社の A の席と同じ" % i)
    # 予測の欄(記録の欄が judge と同じ)
    eq(list(rec[u"予測"]), list(PRED_IDS), u"記録の予測の鍵")
    eq(g(u"読んだ便 UM2 の出力の file の数"), 12, u"読んだ便 UM2 の出力の file の数")
    return out


def clean_problems(c):
    u"""記録の形(葉の型・字の場所)・禁止の字が無い。"""
    out = []
    rec = c.rec

    def walk(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                if not isinstance(k, str):
                    out.append(u"鍵が字でない")
                walk(v, path + (k,))
        elif isinstance(o, bool):
            if path[0] != u"予測":
                out.append(u"予測の外に真偽の葉: %s" % u"/".join(path))
        elif isinstance(o, int):
            if o < 0:
                out.append(u"負の葉: %s" % u"/".join(path))
        else:
            out.append(u"整数でない葉: %s" % u"/".join(path))

    for k, v in rec.items():
        if k in (u"限界", u"欄の説明", u"読んだ便 UM2 の出力の sha256 の束ね", u"回"):
            continue
        walk(v, (k,))
    if not all(isinstance(x, str) for x in rec[u"限界"]) or not all(isinstance(x, str) for x in rec[u"欄の説明"].values()):
        out.append(u"限界・欄の説明が字でない")
    if not re.match(r"^[0-9a-f]{64}$", rec[u"読んだ便 UM2 の出力の sha256 の束ね"]):
        out.append(u"束ねの sha256 の形が違う")
    text = json.dumps(rec, ensure_ascii=False)
    if DOCID_FORM.search(text) or ECODE_FORM.search(text):
        out.append(u"記録に docID か EDINET コードの形が在る")
    if DATE_FORM.search(text):
        out.append(u"記録に日付の形が在る")
    heads = set()
    for d in c.defs:
        for r in d[u"行"]:
            heads.update(x for x in [r.get(u"名")] if isinstance(x, str) and len(x) >= 3)
    for h in heads:
        if h in text:
            out.append(u"記録に定義表の名の字が在る: %s" % h)
    return out


def claim_problems(c):
    u"""文書の字が「全部」「2 席とも 2 期目」「0 席」など、記録の数どうしの関係として言っていること。数は render が記録から出すので、関係の方をここで見る。"""
    rec, um2 = c.rec, c.um2
    n = lambda k: N(rec, k)                                   # noqa: E731
    out = []

    def need(ok, what):
        if not ok:
            out.append(what)

    stopped = [n(u"掛け合わせ1:止める×" + x) for x in RESULT_NAMES]
    need(sum(stopped) == n(u"掛け合わせ1:止める×同じ") > 0, u"B が止めた行が全部「同じ」でない(頭の「全部在る・92 行とも同じ」)")
    need(sum(n(u"掛け合わせ2:確認待ち×" + x) for x in RESULT_NAMES) == n(u"掛け合わせ2:確認待ち×同じ") > 0, u"確認待ちの行が全部「同じ」でない")
    for x in RESULT_NAMES:
        need(n(u"掛け合わせ1:B なし×" + x) == 0 and n(u"掛け合わせ2:B なし×" + x) == 0, u"B なしの行が在る(表に出ていない行)")
    nonzero = sorted(k for k, v in rec[u"数"].items() if k.startswith(u"自信:") and v)
    need(nonzero == sorted([u"自信:高×同じ", u"自信:中×同じ", u"自信:中×違う"]), u"自信の 0 でない欄が文書に並べた 3 つと違う: %s" % nonzero)
    need(n(u"自信:高×違う") == 0 and n(u"自信:高×無いのに在る") == 0, u"高と書いた違う行が在る")
    need(n(u"自信:中×違う") == n(u"期1:結果:違う") + n(u"期2:結果:違う") > 0, u"違った行が全部 `中` でない")
    need(n(u"期1:結果:違う") == 1 and n(u"期2:結果:違う") == 1, u"1 期目 1・2 期目 1 でない(手がかり 1・5 が 1 社の 1 行ずつ)")
    need(list(c.rec[u"会社ごと"][u"1"]).count(u"期1:結果:違う") == 1 and all(u"期1:結果:違う" not in r for i, r in rec[u"会社ごと"].items() if i != u"1"), u"違った行が社 1 だけでない")
    need(n(u"自信:中×同じ") + n(u"自信:中×違う") == 20, u"`中` の行が 20 でない(手がかり 2 の「a30 が 16・a08 が 4」)")
    need(sum(n(u"期%d:計算:%s" % (p, x)) for p in (1, 2) for x in CALC_NAMES if x not in (u"同じ", u"形が読めない")) == 0, u"計算に同じ・形が読めない以外が在る")
    need(n(u"期1:計算:形が読めない") == n(u"期2:計算:形が読めない") == 6 and n(u"期1:計算:同じ") == n(u"期2:計算:同じ") == 18, u"計算の期ごとの数が揃わない")
    need(n(u"資料:当たらない数の字が 1 つ以上の資料") == n(u"資料:本数") == 16, u"当たらない数の字が全部の資料に無い")
    need(all(v[u"席の発言の回"] == 0 for v in rec[u"席ごと"].values()) and len(rec[u"席ごと"]) == 16, u"席の発言の回が 16 席とも 0 でない")
    need(len(dirty_seats(rec)) == n(u"過程:汚れの席") == n(u"過程:汚れた呼び出し") == 2 and all(seat_key(k)[2] == 2 for k in dirty_seats(rec)), u"汚れの席 2 が 2 期目の 2 席でない")
    need(sorted(dirty_seats(rec)) == [u"2:b:2", u"3:b:2"], u"汚れた席が社 2・回 b・2 期目と社 3・回 b・2 期目でない")
    need(n(u"過程:期1:前の期の成果の道具を走らせた席") == 0 and n(u"過程:期2:前の期の成果の道具を走らせた席") == 0, u"前の期の成果の道具を走らせた席が 0 でない")
    need(n(u"過程:期2:script を書いた席") == n(u"過程:期2:席の数") == 8 and n(u"過程:期1:script を書いた席") == n(u"過程:期1:席の数") == 8, u"script を書いた席が全部でない")
    need(n(u"関係:成り立つ本数") == n(u"関係:見られる本数") == 48 and n(u"関係:見られない本数") == 0, u"関係が全部成り立つでない")
    need(n(u"値の表:読めた") == 16, u"値の表が 16 枚読めていない(手がかり 1 の「16 枚の全部」)")
    need(n(u"過程:前の期の成果の path が出た呼び出し") == sum(v[u"前の期の成果の path が出た呼び出し"] for k, v in seats_of(rec, 2)), u"前の期の成果の path が出た呼び出しが 2 期目だけでない")
    need(sum(v[u"前の期の成果の path が出た呼び出し"] for k, v in seats_of(rec, 1)) == 0, u"前の期の成果の path が出た呼び出しが 1 期目に在る")
    need(sum(n(u"期%d:結果:%s" % (p, x)) for p in (1, 2) for x in (u"無いのに在る", u"無いで同じ", u"無いで違う")) == 0, u"null の行に関わる結果が 0 でない(UM3-A6 は測れなかった)")
    need(um2[u"数"][u"正解が null の行:期1"] == 0 and um2[u"数"][u"正解が null の行:期2"] == 0, u"便 UM2 の記録に正解が null の行が在る")
    need(um2[u"数"][u"段 1:通したが数値が違う"] == 0, u"便 UM2 の記録で B が通して数値が違った行が 0 でない")
    need(n(u"期1:結果:違う") == n(u"掛け合わせ1:無いを受ける×違う") and n(u"掛け合わせ1:無いを受ける×違う") == 1, u"1 期目の違った行が B の「無いを受ける」の行と違う")
    need(rec[u"数"][u"過程:期1:道具の呼び出しの数"] < rec[u"数"][u"過程:期2:道具の呼び出しの数"], u"2 期目の呼び出しが減っている(手がかり 4「呼び出しは減っていない」)")
    need(n(u"過程:期2:最大の file に触れた席") == 6 and n(u"過程:期2:席の数") == 8, u"2 期目に最大の file に触れた席が 6 / 8 でない")
    need(n(u"B の席:席の数") == 4 and n(u"B の席:汚れの席") == 0, u"B の席の数・汚れが違う")
    return out


def bound_problems(c):
    u"""封の字: 予測の表の 16 行・§5 の候補 (i)〜(v)・結果の文書が引く決めが封にそのまま在る。"""
    out = []
    rows = seal_pred_rows(c.seal)
    if list(rows) != list(PRED_IDS):
        out.append(u"封の予測の表の id が違う: %s" % list(rows))
    cands = seal_candidates(c.seal)
    if len(cands) != SEAL_CANDIDATE_COUNT or [x.split(u" ")[1] for x in cands] != [u"(i)", u"(ii)", u"(iii)", u"(iv)", u"(v)"]:
        out.append(u"封 §5 の候補が (i)〜(v) の 5 つでない")
    for must in (u"結果の文書はここに無い候補を足さない", u"UM3-A3・UM3-A6 が当たったら", u"UM3-A2・UM3-A5 が当たったら", u"勝ち負けの文は書かない", u"言えないこと",
                 u"手がかりは**司令塔(AI)の読み**と書く。人の目ではない"):
        if must not in c.seal:
            out.append(u"封に字が無い: %s" % must)
    return out


def verdict_problems(c):
    u"""judge が決めた当たり外れが、記録の ``予測`` の欄・集計の script の judge・文書の頭の件数・§1 の表の判定列と同じ。"""
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
        if c.rec[u"予測"].get(i, {}).get(u"当たり") != j.get(i):
            out.append(u"記録の予測の欄と食い違う: %s" % i)
        if dict(c.rec[u"予測"].get(i, {})) != dict(tj.get(i, {})):
            out.append(u"記録の予測の欄が集計の script の judge の出力と違う: %s" % i)
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
    u"""§5 の次の便の候補が封 §5 の (i)〜(v) とちょうど同じ(足さない・落とさない・入れ替えない)。"""
    i = c.doc.find(u"## §5 ")
    if i < 0:
        return [u"§5 が無い"]
    body = c.doc[i:]
    cands = [l for l in body.splitlines() if l.startswith(u"- ")]
    out = []
    if cands != seal_candidates(c.seal):
        out.append(u"§5 の候補が封 §5 の候補と違う")
    if re.search(r"\((?:vi|vii|viii|ix)\)", body):
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


def head_of(doc):
    i = doc.find(u"## §1 ")
    return doc[:i] if i >= 0 else None


def seal3_problems(c):
    u"""封 §3 の決め: 勝ち負けの文が無い・A3 か A6 が当たりなら A の負けが頭に・A2 か A5 が当たりなら B の負けが頭に・同じ表に 4 つを並べる・揺れは違った行の数だけ・言えないこと。"""
    out = []
    head = head_of(c.doc)
    if head is None:
        return [u"§1 が無い"]
    rest = c.doc.replace(SEAL_LOSS_SENTENCE, u"")
    if SEAL_LOSS_SENTENCE not in c.doc:
        out.append(u"頭に封 §3 の「勝ち負けの文は書かない」が無い")
    for wd in WIN_WORDS:
        if wd in rest:
            out.append(u"勝ち負けの語が在る: %s" % wd)
    j = judge(c.rec)
    n = lambda k: N(c.rec, k)                                 # noqa: E731
    wrong = n(u"期1:結果:違う") + n(u"期2:結果:違う") + n(u"期1:結果:無いのに在る") + n(u"期2:結果:無いのに在る")
    if j[u"UM3-A3"] or j[u"UM3-A6"]:
        want = u"- **A(型も検査も持たない席)が出して、正解と違った行は %d(%d 行のうち)。誰も止めていない。**" % (wrong, n(u"期1:行の数") + n(u"期2:行の数"))
        if want not in head:
            out.append(u"UM3-A3 か UM3-A6 が当たりなのに、頭に A の負けが無い")
    if j[u"UM3-A6"]:
        if u"「無いのに在る」は %d" % (n(u"期1:結果:無いのに在る") + n(u"期2:結果:無いのに在る")) not in head:
            out.append(u"UM3-A6 が当たりなのに、頭に「無いのに在る」の数が無い")
    if j[u"UM3-A2"] or j[u"UM3-A5"]:
        stopped = sum(n(u"掛け合わせ1:止める×" + x) for x in RESULT_NAMES)
        waiting = sum(n(u"掛け合わせ2:確認待ち×" + x) for x in RESULT_NAMES)
        if u"- **B(便 UM2)が 1 期目に止めた行(" not in head or u"%d 回ぶんで %d。" % (len(c.rec[u"回"]), stopped) not in head:
            out.append(u"UM3-A2 が当たりなのに、頭に B が止めた行の数が無い")
        if u"B の 2 期目の置き場が確認待ちの %d 行も" % waiting not in head or u"B は止めすぎて" not in head or u"B の負けとして頭に書く" not in head:
            out.append(u"UM3-A5 が当たりなのに、頭に B の負けが無い")
    for must in (u"A が出して正しかった行 %d" % n(u"期1:結果:同じ"), u"A が出して違った行 %d" % n(u"期1:結果:違う"), u"B が止めた行 ", u"B が通して数値が違った行"):
        if must not in head:
            out.append(u"頭の「同じ表に並べる」に無い: %s" % must)
    # 揺れは違った行の数だけ書く(安定している/いないは言えないこと の中だけ)
    if u"「A は安定している/いない」(2 回だけ)" not in head:
        out.append(u"言えないことに「A は安定している/いない」が無い")
    # 言えないこと: 封の字の「」の全部が頭の言えないことの段落に在る
    sealed = re.search(r"\*\*言えないこと\*\*: (.*)", c.seal)
    bullet = [l for l in head.splitlines() if l.startswith(u"- **言えないこと。**")]
    if not sealed or len(bullet) != 1:
        out.append(u"言えないこと の段落が 1 つでない")
    else:
        for q in re.findall(u"「[^」]*」", sealed.group(1)):
            if q not in bullet[0]:
                out.append(u"言えないことに封の字が無い: %s" % q)
    return out


HEAD_FRAGS = (u"**A(型も検査も持たない席)が出して、正解と違った行は", u"誰も止めていない", u"**B(便 UM2)が 1 期目に止めた行", u"B は止めすぎて", u"**UM3-A6 は測れなかった。**",
              u"「A は無い行に数を書かなかった」とは言えない", u"**記録は 1 度作り直した。**", u"封は直していない", u"**UM3-L6 は外れ", u"封の決め(渡した folder の外の path)では汚れ",
              u"汚れの席を外した数も並べる", u"**計算の 3 行(a31〜a33)", u"直して読まない", u"記録は値が合うかを見ていない", u"粗い数。1 つずつ読んでいない", u"「資料が正しい」「資料が誤っている」のどちらも言わない",
              u"**過程の数は、会話の記録に残った道具の呼び出しだけ。**", u"取りこぼす形と数え過ぎる形の両方が在り", u"写して走らせた席を数えに入れるかは封に無く、入れていない",
              u"取り直し 0", u"互いに独立ではない", u"model の名は書かない", u"**素材と正解。**", u"独立に確かめていない", u"何も言われない席の振る舞いではない",
              u"司令塔は便 UM2 の結果を知って予測を書いた", u"封も予測も、結果を見てから書き換えていない", u"**言えないこと。**")


def head_problems(c):
    u"""負けと限界は §1 より前(頭)に在る。"""
    head = head_of(c.doc)
    if head is None:
        return [u"§1 が無い"]
    return [u"頭に無い: %s" % f for f in HEAD_FRAGS if f not in head]


def sec3_problems(c):
    u"""§3 は記録に縛らない読み。封 §1-7 の形(手がかりごとの (a)(b)(c)・(b) が無ければ「読みだけ」・司令塔(AI)の読み・型分けの 3 つの名)を見る。"""
    i, j = c.doc.find(u"## §3 "), c.doc.find(u"## §4 ")
    if i < 0 or j < 0 or j < i:
        return [u"§3 が無い"]
    s3 = c.doc[i:j]
    out = []
    for must in (u"司令塔(AI)の読み", u"記録に縛らず、字で留めるだけ", u"手がかりは、この 4 社では確かめていない", u"(a) 見た席 (b) 当たる §1・§2 の数 (c) 1〜7 段のどこの話か",
                 u"(司令塔の型分け)", u"「正解の側の誤りか決めの違い」", u"「席の誤り」", u"「どちらとも決められない」", u"席の申告", u"監査の席の読み", u"司令塔の数え"):
        if must not in s3 and must not in c.doc[:i]:
            out.append(u"§3 に字が無い: %s" % must)
    items = re.findall(r"(?m)^(\d+)\. \*\*(.*)$", s3)
    if [k for k, _t in items] != [str(x) for x in range(1, 10)]:
        out.append(u"手がかりが 1〜9 の 9 つでない")
    for m in re.finditer(r"(?m)^(\d+)\. (\*\*.*)$", s3):
        t = m.group(2)
        a, b, cc = t.find(u"(a)"), t.find(u"(b)"), t.find(u"(c)")
        if not (0 < a < b < cc):
            out.append(u"手がかり %s に (a)(b)(c) が順に無い" % m.group(1))
            continue
        btext = t[b:cc]
        if not re.search(r"[0-9]", btext) and u"読みだけ" not in btext:
            out.append(u"手がかり %s: (b) に数が無いのに「読みだけ」の札が無い" % m.group(1))
    return out


def eye_problems(c):
    u"""「人の目」は「人の目ではない」の形でだけ出る(司令塔の読みは AI の読み)。"""
    out = []
    for m in re.finditer(u"人の目", c.doc):
        if not c.doc.startswith(u"人の目ではない", m.start()):
            out.append(u"「人の目」と書いている @%d" % m.start())
    if u"人の目ではない" not in c.doc:
        out.append(u"「人の目ではない」が無い")
    return out


def affirm_problems(c):
    u"""言えないことを肯定で書かない。出た語は「言えないこと」の段落の「」の中か、否定の語を持つ文の中だけ。"""
    out = []
    for ln in c.doc.splitlines():
        if ln.startswith(u"- **言えないこと。**"):
            continue
        for sent in re.split(u"。", ln):
            for p in AFFIRM_PHRASES:
                if p in sent and not any(x in sent for x in NEGATIONS):
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
    for w in (u"1 回目 REVISE(発言の回・汚れの数え過ぎ)", u"script の直し", u"作り直し", u"GO", u"予測 16 本を判定し直して一致", u"全体の suite は未実行"):
        if w not in c.msg_record:
            out.append(u"commit %s の message に「%s」が無い" % (RECORD_COMMIT, w))
    return out


CHECKS = od([
    (u"sha", sha_problems), (u"recount", recount_problems), (u"clean", clean_problems), (u"claims", claim_problems), (u"bound", bound_problems),
    (u"verdict", verdict_problems), (u"sec5", sec5_problems), (u"lines", lines_problems), (u"seal3", seal3_problems), (u"head", head_problems),
    (u"sec3", sec3_problems), (u"eye", eye_problems), (u"affirm", affirm_problems), (u"forbidden", forbidden_problems), (u"commits", commit_problems)])


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
    u"""封 ⊏ 実装(script・封の門)⊏ 記録 ⊏ この文書と門。文書と門は、まだ commit されていない間は許す(commit された後は順序を見る)。"""
    impl = [TALLY_REL, SEAL_GATE_REL]
    out = list(PR.order_problems(root, PREFIX, SEAL_REL, SEAL_COMMIT, impl, [RECORD_REL, DOC_REL, GATE_REL]))
    out = [x for x in out if x not in (u"UNCOMMITTED:" + DOC_REL, u"UNCOMMITTED:" + GATE_REL)]
    rec = PR.added_commits(root, PREFIX + RECORD_REL)
    for rel in (TALLY_REL, SEAL_GATE_REL):
        last = [x for x in PR.git_in(root, "log", "-1", "--format=%H", "--", PREFIX + rel)[1].split() if x]
        if last and rec and not PR.is_anc(root, last[0], rec[0]):
            out.append(u"記録が %s の最後の commit より前" % rel)
    return out


def git_problems(root=REPO):
    at = od((rel, last) for rel, (_a, last) in BLOB_AT.items())
    return blob_problems(root, PREFIX, at) + engine_zero_problems(root, SEAL_COMMIT) + history_problems(root) + order_problems(root)


# ================================================================== 変異
def rep(c, old, new, field="doc", count=None):
    u"""写しの field の字の ``old`` を ``new`` に替える(無ければ「当たらない」として例外)。"""
    text = getattr(c, field)
    if old not in text:
        raise KeyError(u"変異が当たらない: " + old[:30])
    setattr(c, field, text.replace(old, new) if count is None else text.replace(old, new, count))
    return c


def set_leaf(c, path, value):
    node = c.rec
    for k in path[:-1]:
        node = node[k]
    node[path[-1]] = value
    return c


def inc(c, path, delta=1):
    node = c.rec
    for k in path[:-1]:
        node = node[k]
    node[path[-1]] += delta
    return c


def flip_hit(c, key, path, value):
    u"""記録の 1 つの数を、判定が反対になる値にする(ほかの欄は合わせない。判定・文書・記録の食い違いを見る)。"""
    return set_leaf(c, path, value)


def drop_line(c, startswith):
    c.doc = u"\n".join(l for l in c.doc.split(u"\n") if not l.startswith(startswith))
    return c


MUTATIONS = od([
    (u"F1  記録の sha256 の写しを違う値に", (lambda c: c.shas.__setitem__(RECORD_REL, u"0" * 64) or c, (u"sha",))),
    (u"F2  封の sha256 の写しを違う値に", (lambda c: c.shas.__setitem__(SEAL_REL, u"0" * 64) or c, (u"sha",))),
    (u"F3  集計の script の sha256 の写しを違う値に", (lambda c: c.shas.__setitem__(TALLY_REL, u"0" * 64) or c, (u"sha",))),
    (u"F4  記録の頂の鍵を消す(数)", (lambda c: c.rec.pop(u"数") and c, (u"recount",))),
    (u"F5  記録の会社を 1 つ消す", (lambda c: c.rec[u"会社ごと"].pop(u"4") and c, (u"recount",))),
    (u"F6  記録に docID の形を足す", (lambda c: c.rec[u"数"].__setitem__(u"SXXXXXXX", 0) or c, (u"clean",))),
    (u"F7  記録の数の欄に文字の葉を足す", (lambda c: c.rec[u"数"].__setitem__(u"x", u"売上高") or c, (u"clean",))),
    (u"F8  記録に日付の形を足す", (lambda c: c.rec[u"限界"].append(u"2026-11-24 に走らせた") or c, (u"clean",))),
    (u"F9  封の予測の行の境を替える(216 → 200)", (lambda c: rep(c, u"240 のうち 216 以上(90%)", u"240 のうち 200 以上(90%)", "seal"), (u"lines",))),
    (u"F10 封 §5 に (vi) の候補を足す(封の写しだけ)", (lambda c: setattr(c, "seal", c.seal.rstrip(u"\n") + u"\n- (vi) 新しい候補。\n") or c, (u"sec5", u"lines", u"bound"))),
    (u"F11 封の予測の行を 1 つ消す", (lambda c: rep(c, u"| UM3-D1 |", u"| UM3-Dx |", "seal"), (u"bound", u"lines"))),
    (u"C1  UM3-A8 を当たりにする(高×違う を 1 に)", (lambda c: flip_hit(c, u"A8", (u"数", u"自信:高×違う"), 1), (u"verdict", u"lines", u"claims"))),
    (u"C2  UM3-A6 を当たりにする(期2 の無いのに在る を 1 に)", (lambda c: flip_hit(c, u"A6", (u"数", u"期2:結果:無いのに在る"), 1), (u"verdict", u"lines", u"recount"))),
    (u"C3  UM3-L6 を当たりにする(汚れの席を 0 に)", (lambda c: flip_hit(c, u"L6", (u"数", u"過程:汚れの席"), 0), (u"verdict", u"lines", u"recount"))),
    (u"C4  UM3-L4 を当たりにする(2 期目の中央値の 2 倍を 10 に)", (lambda c: flip_hit(c, u"L4", (u"数", u"過程:期2:道具の呼び出しの中央値の 2 倍"), 10), (u"verdict", u"lines", u"recount"))),
    (u"C5  UM3-L5 を当たりにする(値の表を 2 回以上書いた席を 4 に)", (lambda c: flip_hit(c, u"L5", (u"数", u"過程:値の表を 2 回以上書いた席"), 4), (u"verdict", u"lines", u"recount"))),
    (u"C6  UM3-A7 を当たりにする(期1 の数値が違う行が在る社を 2 に)", (lambda c: flip_hit(c, u"A7", (u"数", u"揺れ:期1:数値が違う行が在る社"), 2), (u"verdict", u"lines", u"recount"))),
    (u"C7  UM3-A1 を外れにする(期1 の同じを 215 に)", (lambda c: flip_hit(c, u"A1", (u"数", u"期1:結果:同じ"), 215), (u"verdict", u"lines", u"recount"))),
    (u"C8  記録の予測の欄の UM3-A1 を外れに", (lambda c: set_leaf(c, (u"予測", u"UM3-A1", u"当たり"), False), (u"verdict",))),
    (u"D1  頭の「当たり 10・外れ 6」を「当たり 11・外れ 5」に", (lambda c: rep(c, u"当たり 10・外れ 6", u"当たり 11・外れ 5"), (u"verdict", u"lines"))),
    (u"D2  §1 の UM3-L6 の「外れ」を「当たり」に", (lambda c: rep(c, u"2 / 16 | 外れ |", u"2 / 16 | 当たり |"), (u"verdict", u"lines"))),
    (u"D3  §1 の UM3-A1 の「当たり」を「外れ」に", (lambda c: rep(c, u"239 / 240 | 当たり |", u"239 / 240 | 外れ |", count=1), (u"verdict", u"lines"))),
    (u"D4  頭の A の負けの行を消す", (lambda c: drop_line(c, u"- **A(型も検査も持たない席)が出して"), (u"seal3", u"lines", u"head"))),
    (u"D5  頭の B の負けの行を消す", (lambda c: drop_line(c, u"- **B(便 UM2)が 1 期目に止めた行"), (u"seal3", u"lines", u"head"))),
    (u"D6  頭の「B は止めすぎて」を消す", (lambda c: rep(c, u"B は止めすぎて、", u""), (u"seal3", u"lines", u"head"))),
    (u"D7  頭に勝ち負けの文を足す(A の方が勝った)", (lambda c: rep(c, u"誰も止めていない。**", u"誰も止めていない。** A の方が勝った。"), (u"seal3", u"lines"))),
    (u"D8  頭の「勝ち負けの文は書かない」を消す", (lambda c: rep(c, SEAL_LOSS_SENTENCE, u"**先に負けと限界を書く。**"), (u"seal3", u"lines"))),
    (u"D9  言えないことに肯定を足す(普通の AI で足りる)", (lambda c: rep(c, u"| UM3-L4 |", u"普通の AI で足りる。\n| UM3-L4 |"), (u"affirm", u"lines"))),
    (u"D10 言えないことの段落から「A は安定している/いない」を消す", (lambda c: rep(c, u"「A は安定している/いない」(2 回だけ)。", u""), (u"seal3", u"lines"))),
    (u"D11 言えないことの段落から「手がかりで良くなる」を消す", (lambda c: rep(c, u"「手がかりで良くなる」(手がかりは確かめていない)。", u""), (u"seal3", u"lines"))),
    (u"D12 「人の目ではない」を「人の目」に", (lambda c: rep(c, u"人の目ではない", u"人の目"), (u"eye", u"lines"))),
    (u"D13 §5 に (vi) の候補を足す", (lambda c: setattr(c, "doc", c.doc.rstrip(u"\n") + u"\n- (vi) 新しい候補。\n") or c, (u"sec5", u"lines"))),
    (u"D14 §5 の (iv) の字を替える", (lambda c: rep(c, u"(iv) 成果物を大きくする", u"(iv) 何もしない"), (u"sec5", u"lines"))),
    (u"D15 §5 の (iii) を落とす", (lambda c: drop_line(c, u"- (iii)"), (u"sec5", u"lines"))),
    (u"D16 文書の commit の字 8156e02b を 1 字替える", (lambda c: rep(c, u"8156e02b", u"8156e02a"), (u"commits", u"lines"))),
    (u"D17 文書に知らない commit の字を足す", (lambda c: rep(c, u"費用は 0)。", u"費用は 0)。(commit deadbeef)", count=1), (u"commits", u"lines"))),
    (u"D18 文書に禁止語を足す", (lambda c: rep(c, u"費用は 0)。", u"費用は 0)。精度は高い。"), (u"forbidden", u"lines"))),
    (u"D19 文書に docID の形を足す", (lambda c: rep(c, u"費用は 0)。", u"費用は 0)。S100AAAA。"), (u"forbidden", u"lines"))),
    (u"D20 §3 の「読みだけ」(手がかり 6)を消す", (lambda c: rep(c, u"(b) 読みだけ。(c) 段 6・段 5", u"(b) (c) 段 6・段 5"), (u"sec3", u"lines"))),
    (u"D21 §3 の手がかり 9 を消す", (lambda c: drop_line(c, u"9. **席は、確かめた範囲を自分で書いた。**"), (u"sec3", u"lines"))),
    (u"D22 §3 の(司令塔の型分け)の字を消す", (lambda c: rep(c, u"(司令塔の型分け)", u""), (u"sec3", u"lines"))),
    (u"D23 §3 の字で留めた数(監査の席の読み 66)を替える", (lambda c: rep(c, u"監査の席の読みでは 66", u"監査の席の読みでは 67"), (u"lines",))),
    (u"D24 §3 の字で留めた数(a30 が 16・a08 が 4)を替える", (lambda c: rep(c, u"a30 が 16・a08 が 4", u"a30 が 15・a08 が 5"), (u"lines",))),
    (u"D25 §3 の字で留めた数(数の字 1383)を替える", (lambda c: rep(c, u"数の字 1383", u"数の字 1384"), (u"lines",))),
    (u"D26 頭の字で留めた数(6 席が上限で切れた)を替える", (lambda c: rep(c, u"2 期目の 8 席のうち 6 席は", u"2 期目の 8 席のうち 5 席は"), (u"lines",))),
    (u"D27 頭の字で留めた「うち 2 席は前の期の道具を写した」を替える", (lambda c: rep(c, u"うち 2 席は前の期の道具を写した", u"うち 3 席は前の期の道具を写した"), (u"lines",))),
    (u"D28 §2 の表の判定の字(通す)の行の数を替える", (lambda c: rep(c, u"| 通す | 136 | 0 | 0 |", u"| 通す | 135 | 1 | 0 |"), (u"lines",))),
    (u"D29 §2 の表の行を消す", (lambda c: drop_line(c, u"| 確認待ち | 116 |"), (u"lines",))),
    (u"D30 §2 の表に行を足す", (lambda c: rep(c, u"| 保留 | 0 | 0 | 0 |", u"| 保留 | 0 | 0 | 0 |\n| 新しい | 1 | 0 | 0 |"), (u"lines",))),
    (u"D31 §4 の「走らせていない」を消す", (lambda c: drop_line(c, u"- 全体の suite は"), (u"lines",))),
    (u"D32 算用数字を漢数字に逃がす(480 → 四百八十)", (lambda c: rep(c, u"(480 行のうち)", u"(四百八十行のうち)"), (u"lines",))),
    (u"D33 頭の予測の件数の数字を字に逃がす(16 本 → 十六本)", (lambda c: rep(c, u"**予測 16 本は", u"**予測 十六本は"), (u"verdict", u"lines"))),
    (u"D34 汚れの席の名(社 2・回 b)を替える", (lambda c: rep(c, u"社 2・回 b・2 期目と社 3", u"社 2・回 a・2 期目と社 3"), (u"lines",))),
    (u"R1  記録: 席ごとの 1 席の結果(同じ)を 1 つ下げて違うを 1 つ上げる", (lambda c: inc(inc(c, (u"席ごと", u"1:a:1", u"結果:同じ"), -1), (u"席ごと", u"1:a:1", u"結果:違う"), 1), (u"recount",))),
    (u"R2  記録: 汚れの席の席ごとの汚れた呼び出しを 0 に", (lambda c: set_leaf(c, (u"席ごと", u"2:b:2", u"汚れた呼び出し"), 0), (u"recount",))),
    (u"R3  記録: 席の発言の回を 1 に", (lambda c: set_leaf(c, (u"席ごと", u"1:a:1", u"席の発言の回"), 1), (u"claims",))),
    (u"R4  記録: B なしの行に 1 つ足す(表に出ない行)", (lambda c: inc(inc(c, (u"数", u"掛け合わせ1:B なし×同じ")), (u"数", u"掛け合わせ1:通す×同じ"), -1), (u"claims",))),
    (u"R5  記録: 自信の高×違うに 1 つ移す(3 つの欄だけの主張)", (lambda c: inc(inc(c, (u"数", u"自信:高×違う")), (u"数", u"自信:中×違う"), -1), (u"claims", u"lines"))),
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


WORD_PAIRS = ((u"当たり", u"外れ"), (u"外れ", u"当たり"), (u"通す", u"止める"), (u"止める", u"通す"), (u"同じ", u"違う"), (u"違う", u"同じ"), (u"全部", u"一部"),
              (u"在る", u"無い"), (u"無い", u"在る"), (u"言えない", u"言える"), (u"読まない", u"読む"), (u"未了", u"済み"), (u"確かめていない", u"確かめた"),
              (u"独立ではない", u"独立である"), (u"以上", u"以下"), (u"申告", u"確認"), (u"0 行", u"1 行"), (u"期目", u"回目"), (u"1 期目", u"2 期目"), (u"2 期目", u"1 期目"),
              (u"高", u"低"), (u"中", u"低"), (u"社 1", u"社 2"), (u"回 a", u"回 b"), (u"回 b", u"回 a"), (u"読みだけ", u"確かめた"), (u"監査の席の読み", u"司令塔の読み"),
              (u"司令塔の数え", u"席の申告"), (u"下限", u"上限"), (u"B の", u"A の"), (u"A の", u"B の"))


def sweep_words(doc):
    for old, new in WORD_PAIRS:
        for m in re.finditer(re.escape(old), doc):
            yield u"語 %s→%s @%d" % (old, new, m.start()), doc[:m.start()] + new + doc[m.end():]


def sweep_lines(doc):
    ls = doc.split(u"\n")
    for k, l in enumerate(ls):
        if l.strip():
            yield u"行を消す @%d" % (k + 1), u"\n".join(ls[:k] + ls[k + 1:])
    for k, l in enumerate(ls):
        if l.strip():
            yield u"行を足す(同じ行の複製) @%d" % (k + 1), u"\n".join(ls[:k + 1] + [l] + ls[k + 1:])


def sweep_sentences(doc):
    for m in re.finditer(r"[^。\n|]+。", doc):
        yield u"文を消す @%d" % m.start(), doc[:m.start()] + doc[m.end():]


def sweep_candidates(doc):
    yield u"候補を足す", doc.rstrip(u"\n") + u"\n- (vi) 新しい候補。\n"
    ls = doc.split(u"\n")
    idx = [k for k, l in enumerate(ls) if re.match(r"^- \((?:i|ii|iii|iv|v)\) ", l)]
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
    u"""記録の全部の整数の葉を 1 つずつ +1(真偽は反転)。``sha`` を除いた検査のどれかが赤になる(sha に頼らない)。黙った葉を返す。"""
    silent = []
    n = 0
    for path in leaf_paths(base.rec):
        c = base.copy()
        node = c.rec
        for k in path[:-1]:
            node = node[k]
        node[path[-1]] = (not node[path[-1]]) if isinstance(node[path[-1]], bool) else node[path[-1]] + 1
        n += 1
        if not red_set(c, skip=(u"sha",)):
            silent.append(path)
    return n, silent


# ================================================================== 試験
_CTX = {}


def base_ctx():
    if "c" not in _CTX:
        _CTX["c"] = Ctx()
        _CTX["tree_before"] = dict((rel, sha_file(rel)) for rel in list(SHA_PIN) + [DOC_REL, UM2_RECORD_REL])
        _CTX["c"].expected()
    return _CTX["c"]


def make_repo(files_by_commit, root):
    subprocess.run(["git", "init", "-q", root], check=True)
    for msg, files in files_by_commit:
        for rel, body in files.items():
            p = os.path.join(root, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "wb") as fh:
                fh.write(body.encode("utf-8"))
        subprocess.run(["git", "-C", root, "add", "-A"], check=True)
        subprocess.run(["git", "-C", root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", msg], check=True)


class RealTest(unittest.TestCase):
    u"""実物(いまの木)で全部の検査が空。"""

    @classmethod
    def setUpClass(cls):
        cls.c = base_ctx()

    def test_a_1_sha256_of_the_frozen_files(self):
        self.assertEqual([], sha_problems(self.c))

    def test_a_2_the_module_names_this_gate_loaded_are_not_overwritten(self):
        self.assertEqual([], OVERWRITTEN)
        self.assertIn(MY_TALLY_NAME, sys.modules)
        self.assertIn(MY_PR_NAME, sys.modules)

    def test_b_1_the_record_recounts(self):
        self.assertEqual([], recount_problems(self.c))

    def test_b_2_the_record_is_clean(self):
        self.assertEqual([], clean_problems(self.c))

    def test_b_3_the_claims_between_numbers_hold(self):
        self.assertEqual([], claim_problems(self.c))

    def test_c_1_the_seal_has_the_prediction_rows_and_the_candidates(self):
        self.assertEqual([], bound_problems(self.c))
        self.assertEqual(16, len(seal_pred_rows(self.c.seal)))
        self.assertEqual(5, len(seal_candidates(self.c.seal)))

    def test_c_2_the_verdicts_are_decided_again_and_equal_the_record_the_tally_judge_and_the_document(self):
        self.assertEqual([], verdict_problems(self.c))
        j = judge(self.c.rec)
        self.assertEqual(list(PRED_IDS), list(j))
        self.assertEqual([u"UM3-A6", u"UM3-A7", u"UM3-A8", u"UM3-L4", u"UM3-L5", u"UM3-L6"], [i for i, v in j.items() if v is False])
        self.assertEqual(10, len([1 for v in j.values() if v is True]))

    def test_c_3_the_section5_candidates_are_the_seals(self):
        self.assertEqual([], sec5_problems(self.c))

    def test_d_1_every_line_equals_the_one_built_from_the_record(self):
        self.assertEqual([], lines_problems(self.c))

    def test_d_2_the_losses_and_limits_are_at_the_head(self):
        self.assertEqual([], head_problems(self.c))

    def test_d_3_section3_is_pinned_by_form_and_the_seal_section3_decisions_hold(self):
        self.assertEqual([], sec3_problems(self.c))
        self.assertEqual([], seal3_problems(self.c))

    def test_e_1_no_affirmation_no_forbidden_word_no_human_eye_and_the_commits_named(self):
        self.assertEqual([], affirm_problems(self.c))
        self.assertEqual([], forbidden_problems(self.c))
        self.assertEqual([], eye_problems(self.c))
        self.assertEqual([], commit_problems(self.c))

    def test_f_1_blobs_engine_history_and_order(self):
        self.assertEqual([], git_problems())

    def test_f_2_the_blob_check_is_red_for_a_changed_file_and_a_missing_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_repo([("x", {PREFIX + "a.txt": u"1"})], tmp)
            short = subprocess.run(["git", "-C", tmp, "log", "--format=%h", "-1"], stdout=subprocess.PIPE).stdout.decode().strip()
            self.assertEqual([], blob_problems(tmp, PREFIX, od([("a.txt", short)])))
            with open(os.path.join(tmp, PREFIX, "a.txt"), "w") as fh:
                fh.write(u"2")
            self.assertNotEqual([], blob_problems(tmp, PREFIX, od([("a.txt", short)])))
            self.assertNotEqual([], blob_problems(tmp, PREFIX, od([("a.txt", "0000000")])))
            os.remove(os.path.join(tmp, PREFIX, "a.txt"))
            self.assertNotEqual([], blob_problems(tmp, PREFIX, od([("a.txt", short)])))

    def test_f_3_the_engine_check_is_red_when_the_engine_changed_after_the_seal(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_repo([("seal", {PREFIX + "docs/s.md": u"s"}), ("eng", {PREFIX + "core/e.py": u"x"})], tmp)
            seal = subprocess.run(["git", "-C", tmp, "log", "--format=%h", "--", PREFIX + "docs/s.md"], stdout=subprocess.PIPE).stdout.decode().strip()
            self.assertNotEqual([], engine_zero_problems(tmp, seal))
        with tempfile.TemporaryDirectory() as tmp:
            make_repo([("eng", {PREFIX + "core/e.py": u"x"}), ("seal", {PREFIX + "docs/s.md": u"s"}), ("later", {PREFIX + "docs/t.md": u"t"})], tmp)
            seal = subprocess.run(["git", "-C", tmp, "log", "--format=%h", "--", PREFIX + "docs/s.md"], stdout=subprocess.PIPE).stdout.decode().strip()
            self.assertEqual([], engine_zero_problems(tmp, seal))
            with open(os.path.join(tmp, PREFIX, "core", "e.py"), "w") as fh:
                fh.write(u"y")
            self.assertNotEqual([], engine_zero_problems(tmp, seal))

    def test_f_4_the_order_check_is_red_when_the_record_comes_before_a_script(self):
        seal = PREFIX + SEAL_REL
        with tempfile.TemporaryDirectory() as tmp:
            make_repo([("seal", {seal: u"s"}), ("rec", {PREFIX + RECORD_REL: u"{}"}), ("impl", {PREFIX + TALLY_REL: u"x"})], tmp)
            short = subprocess.run(["git", "-C", tmp, "log", "--format=%h", "--", seal], stdout=subprocess.PIPE).stdout.decode().strip()
            got = PR.order_problems(tmp, PREFIX, SEAL_REL, short, [TALLY_REL], [RECORD_REL])
            self.assertNotEqual([], list(got))

    def test_f_5_the_order_check_allows_a_not_yet_committed_document_and_gate_and_reads_them_when_committed(self):
        got = order_problems(REPO)
        self.assertEqual([], got)
        for rel in (DOC_REL, GATE_REL):
            added = PR.added_commits(REPO, PREFIX + rel)
            for commit in added:
                self.assertTrue(PR.is_anc(REPO, RECORD_COMMIT, commit), rel)


class MutationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = base_ctx()

    def test_h_1_every_fixed_mutation_turns_its_checks_red_and_the_files_are_unchanged(self):
        before = dict((rel, sha_file(rel)) for rel in list(SHA_PIN) + [DOC_REL, UM2_RECORD_REL])
        bad = [(name, sorted(red), expect) for name, red, expect, ok in run_mutations(self.base) if not ok]
        self.assertEqual([], bad)
        self.assertEqual(before, dict((rel, sha_file(rel)) for rel in list(SHA_PIN) + [DOC_REL, UM2_RECORD_REL]))
        self.assertEqual(_CTX["tree_before"], before)

    def test_h_2_the_unmutated_copy_is_green_on_every_check(self):
        c = self.base.copy()
        self.assertEqual(set(), red_set(c))
        for k, v in all_problems(c).items():
            self.assertEqual([], v, k)

    def test_h_3_the_recount_stays_green_when_the_data_changes_consistently_but_the_document_check_does_not(self):
        c = self.base.copy()
        c.rec[u"数"][u"期1:結果:同じ"] -= 1
        c.rec[u"数"][u"期1:結果:無いで同じ"] += 1
        c.rec[u"会社ごと"][u"1"][u"期1:結果:同じ"] -= 1
        self.assertIn(u"lines", red_set(c))

    def test_h_4_every_check_a_mutation_names_exists(self):
        names = set(k for _n, (_f, ex) in MUTATIONS.items() for k in ex)
        self.assertTrue(names <= set(CHECKS), names - set(CHECKS))

    def test_h_5_the_judgement_edges_at_the_seal_bounds(self):
        edges = (
            (u"UM3-A1", u"期1:結果:同じ", 216, 215), (u"UM3-A4", u"期2:結果:同じ", 216, 215), (u"UM3-A7", u"揺れ:期1:数値が違う行が在る社", 2, 1),
            (u"UM3-A9", u"関係:成り立つ本数", 46, 45), (u"UM3-L1", u"過程:期1:最大の file に触れた席", 6, 5), (u"UM3-L2", u"過程:期1:script を書いた席", 6, 5),
            (u"UM3-L3", u"過程:期2:前の期の成果の道具を走らせた席", 3, 4), (u"UM3-L5", u"過程:値の表を 2 回以上書いた席", 4, 3),
            (u"UM3-D1", u"資料:当たらない数の字が 1 つ以上の資料", 8, 7), (u"UM3-L6", u"過程:汚れの席", 0, 1))
        for key, field, ok_val, ng_val in edges:
            for val, want in ((ok_val, True), (ng_val, False)):
                c = self.base.copy()
                c.rec[u"数"][field] = val
                if key == u"UM3-A1":
                    c.rec[u"数"][u"期1:結果:無いで同じ"] = 0
                if key == u"UM3-A4":
                    c.rec[u"数"][u"期2:結果:無いで同じ"] = 0
                if key == u"UM3-A9":
                    c.rec[u"数"][u"関係:見られる本数"] = 48
                self.assertEqual(want, judge(c.rec)[key], (key, field, val))
                self.assertEqual(want, TAL.judge(c.rec)[key][u"当たり"], (u"tally", key, field, val))
        # A2: 止めた行のうち 在る 90%・同じ 85%。止めた 20 → 在る 18 / 17、同じ 17 / 16(在る 18 の 85% = 15.3)
        for same, present, want in ((18, 18, True), (17, 18, False)):
            c = self.base.copy()
            for x in RESULT_NAMES:
                c.rec[u"数"][u"掛け合わせ1:止める×" + x] = 0
            c.rec[u"数"][u"掛け合わせ1:止める×同じ"] = same
            c.rec[u"数"][u"掛け合わせ1:止める×答えなし"] = 20 - same
            self.assertEqual(want, judge(c.rec)[u"UM3-A2"], (same, present))
            self.assertEqual(want, TAL.judge(c.rec)[u"UM3-A2"][u"当たり"], (u"tally", same, present))
        # A5: 確認待ちのうち 同じ 80%。10 のうち 8 / 7
        for same, want in ((8, True), (7, False)):
            c = self.base.copy()
            for x in RESULT_NAMES:
                c.rec[u"数"][u"掛け合わせ2:確認待ち×" + x] = 0
            c.rec[u"数"][u"掛け合わせ2:確認待ち×同じ"] = same
            c.rec[u"数"][u"掛け合わせ2:確認待ち×違う"] = 10 - same
            self.assertEqual(want, judge(c.rec)[u"UM3-A5"], same)
            self.assertEqual(want, TAL.judge(c.rec)[u"UM3-A5"][u"当たり"], (u"tally", same))
        # A3・A6: 1 以上
        for field, key in ((u"期1:結果:違う", u"UM3-A3"), (u"期2:結果:無いのに在る", u"UM3-A3"), (u"期1:結果:無いのに在る", u"UM3-A6"), (u"期2:結果:無いのに在る", u"UM3-A6")):
            c = self.base.copy()
            for f in (u"期1:結果:違う", u"期2:結果:違う", u"期1:結果:無いのに在る", u"期2:結果:無いのに在る"):
                c.rec[u"数"][f] = 0
            self.assertFalse(judge(c.rec)[key])
            c.rec[u"数"][field] = 1
            self.assertTrue(judge(c.rec)[key])
            self.assertEqual(judge(c.rec)[key], TAL.judge(c.rec)[key][u"当たり"])
        # A8: 高の割合は半分以上。違う 2 のうち 高 1 / 0
        for high, want in ((1, True), (0, False)):
            c = self.base.copy()
            c.rec[u"数"][u"自信:高×違う"] = high
            self.assertEqual(want, judge(c.rec)[u"UM3-A8"], high)
            self.assertEqual(want, TAL.judge(c.rec)[u"UM3-A8"][u"当たり"], high)
        # L4: 2 期目の中央値の 2 倍が 1 期目より小さい(18 に対して 17 / 18)
        for v, want in ((17, True), (18, False)):
            c = self.base.copy()
            c.rec[u"数"][u"過程:期2:道具の呼び出しの中央値の 2 倍"] = v
            self.assertEqual(want, judge(c.rec)[u"UM3-L4"], v)
            self.assertEqual(want, TAL.judge(c.rec)[u"UM3-L4"][u"当たり"], v)

    def test_h_6_the_sweep_over_every_number_word_line_sentence_and_candidate_stays_red(self):
        n, silent = run_doc_sweep(self.base)
        self.assertGreater(n, 1000)
        self.assertEqual([], silent[:20], u"黙った変異 %d 個(総数 %d)" % (len(silent), n))

    def test_h_7_the_record_leaf_sweep_stays_red_without_the_sha_pin(self):
        n, silent = run_record_sweep(self.base)
        self.assertGreater(n, 500)
        keys = sorted(set(silent_key(p) for p in silent))
        self.assertEqual(sorted(SILENT_LEAF_KEYS), keys, u"黙った葉 %d 個(総数 %d)" % (len(silent), n))

    def test_h_8_each_mutation_is_caught_by_more_than_the_sha_pin_unless_it_is_a_sha_mutation(self):
        for name, (fn, expect) in MUTATIONS.items():
            if expect == (u"sha",):
                continue
            c = self.base.copy()
            fn(c)
            self.assertTrue(red_set(c, skip=(u"sha",)), name)


#: 記録の葉の掃き(+1)で、sha を外すと黙る葉の欄(文書にも足し算にも出ず、席の間の恒等式も無い欄)。黙る欄の全部をここに字で並べる。
#: ここに無い葉が黙ったら赤・ここに在る欄が黙らなくなったら赤(並べた欄が実際に黙ることを留める)。黙る理由は報告に書く
SILENT_LEAF_KEYS = (
    u"席ごと/*/素材の file のうち path が出た数", u"席ごと/*/素材の file のうち 2 回以上の数", u"席ごと/*/最初に値の表を書くまでの呼び出し", u"席ごと/*/資料を書いた回数",
    u"B の席ごと/*/素材の file のうち path が出た数", u"B の席ごと/*/素材の file のうち 2 回以上の数", u"B の席ごと/*/script を書いた数")


def silent_key(path):
    return u"%s/*/%s" % (path[0], path[2]) if path[0] in (u"席ごと", u"B の席ごと") else u"/".join(path)


if __name__ == "__main__":
    unittest.main()
