# -*- coding: utf-8 -*-
"""結果の門: 封 docs/XBRL_NIL_READ_ENGINE_SEAL_2026-11-17.md(36ca78f1)の結果の文書 docs/XBRL_NIL_READ_ENGINE_RESULT_2026-11-17.md。

封の門 ``test_xbrl_nil_read_engine_seal.py`` の次の段。**追跡されている記録・script・封・結果の文書と git の履歴だけを読む**(材料は読まない。全数の作り直しは走らせない)。

縛るもの(検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表で 1 本ずつ。木の file は変異させず、``Ctx`` の写しに当てる)
 a script・states の記録・便 NR の記録の sha256(字で留める)
 b 記録の中の整合: 封の門の ``record_problems``(行・本ごとの欄からの数え直し・TSS の記録・NR の記録との対応・文や値の漏れ)
 c 結果の文書の数: 表の行も散文の行も、記録から組んだ 1 行と字で同じ(1 行ずつ。文書の行が 1 回ずつ在る)。そのどれにも当たらない行の 2 桁以上の数は、組んだ行の数の集合に在るものだけ
 d 予測 NRE-1〜NRE-6 の判定を、封の予測の字から取った境と記録の行・本ごとの欄(NRE-6 は engine の commit の差分)から門が自分で決め直して、文書の表と同じ・字で留めた判定と同じ。
   NRE-7 は記録に無いので、文書が外れと書き、出どころの但し書き(追跡していない)を持つことだけを縛る
 e 文書に禁止語・会社名らしい字・docID・3 桁以上の漢数字が無い・要点の字が在る
 f 封が commit から 1 字も変わっていない・順序(commit の順。未 commit は赤)・engine は engine の commit から 0 行
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


SG = load_module("tests/measure/test_xbrl_nil_read_engine_seal.py", "nre_seal_gate_for_nre_result_gate")      # 封の門の部品。門としては走らせない
PR = SG.PR

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
ENGINE_COMMIT_SHORT = "d86c5506"                              # engine の commit(封の門・script・記録・留めの連動と同じ commit。履歴から探した値と照らす)
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
STATES_REL = SG.RECORD_REL
NR_STATES_REL = SG.NR_RECORD_REL
INSTANCE_REL = SG.INSTANCE_REL
GATE_REL = "tests/measure/test_xbrl_nil_read_engine_result.py"
DOC_REL = "docs/XBRL_NIL_READ_ENGINE_RESULT_2026-11-17.md"

SHA_PIN = collections.OrderedDict([
    (STATES_REL, "13674c80a367e2c54889cccce0c59418891c8ad66dc10bf52f5744e4697900a0"),
    (SCRIPT_REL, "e20123a485153384f37162e04a5382d65656b568ec41b6359213113052505775"),
    (NR_STATES_REL, "16c07159f88973932f70e9c422734330dcdf7893b6ca26ed2898623b614c3864")])

K_NRE1, K_NRE2, K_NRE3, K_NRE4, K_NRE5, K_PRED, K_BOOKS = SG.K_NRE1, SG.K_NRE2, SG.K_NRE3, SG.K_NRE4, SG.K_NRE5, SG.K_PRED, SG.K_BOOKS
K_TRANS3 = u"state の移り変わり(TSS の記録 → 直した engine)"
K_TRANS_NR = u"state の移り変わり(そのまま → 直した入力)"
K_NR_JUDGE = u"判定の差(封 §2-4)"
STATES = SG.STATES
NRE_IDS = (u"NRE-1", u"NRE-2", u"NRE-3", u"NRE-4", u"NRE-5", u"NRE-6", u"NRE-7")
HIT, MISS = u"当たり", u"**外れ**"
NRE_VERDICT_PINNED = (HIT, HIT, HIT, HIT, HIT, HIT, MISS)

FORBIDDEN_WORDS = (u"証明" + u"した", u"ハルシ" + u"ネーション", u"精" + u"度", u"世界で 1 " + u"社")
COMPANY_WORDS = (u"株式会社", u"有限会社", u"合同会社", u"㈱", u"(株)")
DOCID_RE = re.compile(r"S100[0-9A-Z]{4}")
POINTER_RE = re.compile(r"xbrl:|jppfs|jpcrp|jpdei|_cor:|@(Current|Prior)|formula:")
KANJI_NUM_RE = re.compile(u"[二三四五六七八九]百|[一二三四五六七八九]千|百[一二三四五六七八九十]|千[一二三四五六七八九百]")
HUMAN_EYE_RE = re.compile(u"人の" + u"目")
REQUIRED_PHRASES = (u"先に負けと限界を書く", u"外れ", u"当たり", u"追跡していない", u"確かめていない", u"人間の決定", u"限界", u"旗なし", u"engine は 0 行",
                    u"恒等に近い", u"直す前の engine の数のまま", u"弱い", u"割れ")


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


def nre6_count(root=REPO):
    u"""engine の commit の差分で、既存の試験 file(変更 M)のうち ``.py`` の本数。engine の commit は履歴から探す(封の門の部品)。"""
    _s, e = SG.engine_commit(root, PREFIX, SEAL_REL, SG.ENGINE_FILES)
    if e is None:
        raise ValueError(u"engine の commit が履歴に無い")
    rc, txt = PR.git_in(root, "show", "--name-only", "--format=", "--diff-filter=M", e, "--", PREFIX + "tests")
    if rc != 0:
        raise ValueError(u"git show が失敗した")
    return sum(1 for x in txt.splitlines() if x.endswith(u".py"))


NRE6_REAL = nre6_count()


class Ctx(object):
    u"""記録・封・文書・字の写し。変異は毎回 ``Ctx()`` の新しい写しに 1 か所だけ加える。"""

    def __init__(self):
        self.st = json.loads(read(STATES_REL), object_pairs_hook=collections.OrderedDict)
        self.nr = json.loads(read(NR_STATES_REL), object_pairs_hook=collections.OrderedDict)
        self.seal = read(SEAL_REL)
        self.doc = read(DOC_REL)
        self.nre6 = NRE6_REAL
        self.texts = collections.OrderedDict((rel, read_bytes(rel)) for rel in SHA_PIN)


# ======================================================================================================
# 行・本ごとの欄からの数え直し(門の側で独立に)
def counts(c):
    rows = c.st[u"行"]
    books = c.st[K_BOOKS]
    per4 = c.st[K_NRE4][u"群ごと"]
    G = u"GROUNDED"
    trans = collections.Counter((r[5], r[3]) for r in rows)
    changed = [r for r in rows if r[5] != r[3]]
    diff = [r for r in rows if not r[4]]
    return {
        u"rows": len(rows), u"books": len(books), u"trans": trans,
        u"diff_rows": len(diff), u"diff_books": len(set(r[0] for r in diff)),
        u"changed": len(changed), u"changed_books": len(set(r[0] for r in changed)),
        u"only_new": sum(1 for r in rows if r[5] != G and r[3] == G), u"only_old": sum(1 for r in rows if r[5] == G and r[3] != G),
        u"made": sum(b[2] for b in books), u"gone": sum(b[3] for b in books),
        u"made_books": sum(1 for b in books if b[2] > 0), u"gone_books": sum(1 for b in books if b[3] > 0),
        u"st_before": sum(b[4] for b in books), u"st_after": sum(b[5] for b in books), u"pos_diff_books": sum(b[6] for b in books),
        u"cnt_diff_books": sum(1 for b in books if b[4] != b[5]), u"finditer": sum(b[7] for b in books),
        u"zip_total": sum(v[u"読んだ ZIP"] for v in per4.values()), u"zip_diff": sum(v[u"facts の列が違う ZIP"] for v in per4.values()),
        u"zip_whole": sum(v[u"返り値の全体が違う ZIP"] for v in per4.values()), u"zip_nonx": sum(v[u".xbrl の経路でない ZIP"] for v in per4.values()),
    }


# ======================================================================================================
# a. sha256
def sha_problems(texts, pin=None):
    pin = SHA_PIN if pin is None else pin
    return [u"sha256: %s が字で留めた値と違う" % rel for rel, want in pin.items() if hashlib.sha256(texts.get(rel, b"")).hexdigest() != want]


TOP_KEYS = (u"seal", u"封の commit", u"step", u"この script の sha256", u"入力", u"engine の指紋(直した後)", u"engine の指紋(直す前。TSS の記録のもの)", u"profile", u"材料",
            u"直した式(封 §1)", K_NRE1, K_NRE2, K_NRE3, K_NRE4, K_NRE5, K_PRED, u"本ごとの欄", K_BOOKS, u"限界", u"行の欄", u"時間(秒)", u"key_leaks", u"行")


# ======================================================================================================
# b. 記録の中の整合(封の門の部品)
def record_problems(c):
    out = list(SG.record_problems(text=json.dumps(c.st, ensure_ascii=False)))
    if tuple(c.st) != TOP_KEYS:
        out.append(u"記録の最上位の欄が決めた一覧と違う(文・値などの足された欄の疑い)")
    return out


# ======================================================================================================
# d. 予測の判定(封の予測の字から境を取り、記録の行・本ごとの欄・engine の commit の差分から決め直す)
def seal_row(seal, pid):
    sec = seal[seal.index(u"## §3"):] if u"## §3" in seal else u""
    m = re.search(r"^\| %s \| (.*?) \| (.*?) \|$" % re.escape(pid), sec, re.M)
    return m.group(1) if m else u""


def ints(s):
    return [int(x.replace(u",", u"")) for x in re.findall(r"\d[\d,]*", s)]


def seal_bounds(seal):
    u"""封の予測の字(太字の境)から数を取る。取れなければ例外(= 検査が赤)。"""
    r1 = re.search(r"\*\*(\d+) 本の全部\*\*(?:.*?)行 ([\d,]+)", seal_row(seal, u"NRE-1"))
    r2 = re.search(r"作られた fact \*\*(\d+)\*\*・消えた fact \*\*(\d+)\*\*", seal_row(seal, u"NRE-2"))
    r3 = re.search(r"\*\*(\d+)\*\*\((\d+) 本\).*?値が合う行 \*\*(\d+)\*\*.*?値が合う行 \*\*(\d+)\*\*", seal_row(seal, u"NRE-3"))
    r4 = re.search(r"違う本 (\d+)\)", seal_row(seal, u"NRE-4"))
    r5 = re.search(r"落ちる fact\)は \*\*(\d+)\*\*", seal_row(seal, u"NRE-5"))
    r6 = re.search(r"\*\*(\d+) 本以上 (\d+) 本以下\*\*", seal_row(seal, u"NRE-6"))
    return {u"NRE-1": (int(r1.group(1)), int(r1.group(2).replace(u",", u""))), u"NRE-2": (int(r2.group(1)), int(r2.group(2))),
            u"NRE-3": tuple(int(r3.group(i)) for i in (1, 2, 3, 4)), u"NRE-4": int(r4.group(1)), u"NRE-5": int(r5.group(1)),
            u"NRE-6": (int(r6.group(1)), int(r6.group(2)))}


def nre_judge(c):
    u"""[(id, 当たり?)](NRE-1〜NRE-6)。封の字の境と、行・本ごとの欄・engine の commit の差分から決める。"""
    b = seal_bounds(c.seal)
    n = counts(c)
    books1, rows1 = b[u"NRE-1"]
    ok1 = n[u"diff_books"] == 0 and n[u"diff_rows"] == 0 and n[u"books"] == books1 and n[u"rows"] == rows1
    ok2 = n[u"made"] == b[u"NRE-2"][0] and n[u"gone"] == b[u"NRE-2"][1] and n[u"books"] == books1
    ch, chb, fx, old = b[u"NRE-3"]
    ok3 = n[u"changed"] == ch and n[u"changed_books"] == chb and n[u"only_new"] == fx and n[u"only_old"] == old
    ok4 = n[u"zip_total"] > 0 and n[u"zip_diff"] == b[u"NRE-4"]
    ok5 = n[u"st_before"] > 0 and n[u"st_before"] - n[u"st_after"] == b[u"NRE-5"] and n[u"st_before"] == n[u"finditer"] and n[u"pos_diff_books"] == 0 and n[u"cnt_diff_books"] == 0
    lo6, hi6 = b[u"NRE-6"]
    ok6 = lo6 <= c.nre6 <= hi6
    return [(u"NRE-1", ok1), (u"NRE-2", ok2), (u"NRE-3", ok3), (u"NRE-4", ok4), (u"NRE-5", ok5), (u"NRE-6", ok6)]


def verdicts(c):
    return tuple(HIT if ok else MISS for _i, ok in nre_judge(c)) + (MISS,)         # NRE-7 は記録に無い。字のとおりに読むと外れ(文書の但し書きを別に縛る)


def judge_problems(c):
    out = []
    got = verdicts(c)
    if got != NRE_VERDICT_PINNED:
        out.append(u"judge: 決め直した判定が字で留めた判定と違う: %s" % (u" ".join(got),))
    n = counts(c)
    pr = c.st[K_PRED]
    if pr.get(u"NRE-1 NR の直した入力の行と違う行 / 行") != collections.OrderedDict([(u"分子", n[u"diff_rows"]), (u"分母", n[u"rows"]), (u"率", rate_text(n[u"diff_rows"], n[u"rows"]))]):
        out.append(u"judge: NRE-1 の欄が数え直しと違う")
    if pr.get(u"NRE-4 facts の列が違う ZIP / 読んだ ZIP") != collections.OrderedDict([(u"分子", n[u"zip_diff"]), (u"分母", n[u"zip_total"])]):
        out.append(u"judge: NRE-4 の欄が数え直しと違う")
    if pr.get(u"NRE-3 直した engine でだけ値が合う行・直す前でだけ値が合う行") != collections.OrderedDict([(u"直した engine でだけ", n[u"only_new"]), (u"直す前でだけ", n[u"only_old"])]):
        out.append(u"judge: NRE-3 の欄が数え直しと違う")
    if not n[u"changed"] * 100 < n[u"rows"]:
        out.append(u"judge: 変わった行が行の 1% に満たない(要約の字)に反する")
    return out


# ======================================================================================================
# c. 結果の文書の行(記録から組む)
NRE7_MEAS = u"記録に無い(`tests/measure` の全数で赤 1。実装の席の走らせた記録・追跡していない)"

FIXED = collections.OrderedDict([
    (u"lead engine", u"- **engine を 1 行直した(旗なし)。** `.htm` の経路は全部の profile で fact が変わる。元に戻す道は commit を戻すことだけ。"),
    (u"lead 過去", u"- 過去の便の記録(TSS・第 2 便・1b・PS・NR ほか)は直す前の engine の数のまま残っていて、直した engine では取り直していない。"),
    (u"lead 弱い", u"- NRE-1・NRE-2・NRE-3 は下調べで見た値を予測に置いたので、予測として弱い(当たっても見立ての強さにならない)。"),
    (u"lead nre7", u"- NRE-7 は字のとおりに読むと外れ。封の書き方の欠陥(封 §2-3 の 7 が予告した赤を、NRE-7 の字が数えなかった)。"),
    (u"pred nre7 割れ", u"- NRE-7: 封の字は「実装と留めの連動の後、全数は赤 0」。実装の席が clone で走らせた全数は `tests/measure` で赤 1(`test_xbrl_axis3_decision.py` の `test_9`。"
                      u"封 §2-3 の 7 が「次の便」と予告していた一覧の行が無いための赤)。封 §2-3 の 7 と NRE-7 の字が食い違っていた = 封の書き方の欠陥。字のとおりに読むと外れ。"
                      u"「予告した赤を除けば 0」という読みも在る(割れを隠さない)。"),
    (u"pred nre7 出どころ", u"- NRE-7 の「型に入らない赤で実装の席が止まる回数」は 1(封の字は 0 回か 1 回で範囲内)。赤 1 とこの 1 は追跡する記録に無い数で、"
                       u"出どころは実装の席の走らせた記録(追跡していない)。axis3 の一覧の行はこの便で足した。この便の commit の前に走らせる全数の結果はこの文書に書かない(書くなら日付つきの追記)。"),
    (u"pred nre5", u"- NRE-5 は当たりだが、数え方が式の写し 2 本で始まりを数える形なので恒等に近い(監査の所見)。"
                   u"直した式が正しい tag を落としていないことの実質の裏づけは NRE-1・NRE-2 の側(直した engine の行・fact が、自己閉じを消した入力と同じ)。"),
    (u"detect", u"- 0 の欄(NRE-1 の違う行・NRE-2 の作られた fact と消えた fact)は、式を戻した engine で同じ道を通すと 0 でなくなることを、"
                u"実装の席と監査の席がそれぞれ使い捨ての写しで見た(数は記録に無いので書かない)。"),
    (u"limit 1", u"- 直すのは自己閉じの読み方だけ。`.htm` の経路のほかの読み取り(入れ子・継続・負の表記の format・属性の値の中の `>`)は見ていない。"),
    (u"limit 2", u"- 効きを数えたのは TSS の states だけ。型の読み・注入(1b)・near・第 2 便・便 PS のサマリーの数は、直した engine で取り直していない。"
                 u"それらの記録は直す前の engine の数のまま残る(門は「記録の指紋 = 記録を作った時の engine・今の engine はそこから宣言された遷移 1 つだけ離れている」で留めた)。"),
    (u"limit 3", u"- 旗なしなので、`.htm` の経路は全部の profile で fact が変わる。元に戻す道は commit を戻すことだけ。"),
    (u"limit 4", u"- 空白の入った自己閉じ(`/ >`)は、直した式でも始まりと読む。手元の TSS の `.htm` に在るかは記録に無い(監査の席が 0 個と数えた。記録なし)。"),
    (u"limit 5", u"- この直しで「短信の概況の文を engine が正しく結べる」とは言えない。変わるのは行の 1% に満たない。英文短信の側(`sales/`)は `load_instance` を呼ばないことを grep で見ただけで、数は測らない。"),
    (u"limit 6", u"- 新しい封の門は、script の中の止める守り(母集団・sha256 の照合・件数の比べ・出力の拒否・`--check` の比べ など)の変異を、script の sha256 の門でしか赤にしない(数を作る配線は赤にする)。"),
    (u"limit 7", u"- `--check` の全数の作り直し(材料の本を作り直す重い走らせ直し)を監査で走らせたかは確かめていない。"),
    (u"limit 8", u"- 直す前の「そのまま」の行は TSS の記録と便 NR の記録を字で読んだもので、engine を戻して作り直していない。NRE-4 と NRE-5 の「直す前」だけは旧い engine の blob・式の写しで走らせた。"),
    (u"limit 9", u"- NRE-1 の reason の比べは、便 NR の記録が直した入力の reason の字を持たないため、TSS の記録の reason と同じかの比べで置いた(字そのものの一致ではない)。"),
    (u"limit 10", u"- 予測の当たり外れの判定は司令塔(盲検でない)。"),
    (u"next 1", u"- TSS の系列(第 2 便・1b・PS)を直した engine で取り直すか(人間の決定)。"),
    (u"next 2", u"- この直しを外の紙に書くか(人間の決定)。"),
    (u"next 3", u"- `main` へのマージ(人間の決定)。"),
])


def expected_lines(c):
    u"""[(名前, 文書に 1 回ずつ在るはずの 1 行)]。数は全部ここで記録から組む。"""
    n = counts(c)
    b = seal_bounds(c.seal)
    st = c.st
    b1, b2, b3, b4, b5 = st[K_NRE1], st[K_NRE2], st[K_NRE3], st[K_NRE4], st[K_NRE5]
    vd = verdicts(c)
    per4 = b4[u"群ごと"]
    names4 = list(per4)
    grp = [per4[k][u"読んだ ZIP"] for k in names4]
    E = []
    hits = [i for i, v in zip(NRE_IDS, vd) if v == HIT]
    misses = [i for i, v in zip(NRE_IDS, vd) if v == MISS]
    E.append((u"lead 予測", u"- 予測 %d 本のうち、%s が外れ・%s が当たり(当たり %d・外れ %d)。" % (len(NRE_IDS), u"・".join(misses), u"・".join(hits), len(hits), len(misses))))
    E.append((u"lead 小さい", u"- 変わるのは行の 1%% に満たない(state が変わった行は %s)。" % frac(n[u"changed"], n[u"rows"])))
    for k in (u"lead engine", u"lead 過去", u"lead 弱い", u"lead nre7"):
        E.append((k, FIXED[k]))
    # 材料
    mat = st[u"材料"][u"表と一致した ZIP"]
    E.append((u"材料", u"- 材料: TSS の %d 本(置き場の ZIP が表と一致した本 %d)。切れた本 %d(切れない本 %d は fact も行も無く、数に入らない)・行 %d・profile %s。" % (
        mat, mat, n[u"books"], mat - n[u"books"], n[u"rows"], st[u"profile"])))
    fp_new, fp_old = st[u"engine の指紋(直した後)"], st[u"engine の指紋(直す前。TSS の記録のもの)"]
    same_core = fp_new[u"core_py_sha256"] == fp_old[u"core_py_sha256"]
    diff_ad = fp_new[u"adapter_xbrl_py_sha256"] != fp_old[u"adapter_xbrl_py_sha256"]
    E.append((u"指紋", u"- 記録の engine の指紋: adapters の束ねた指紋は直す前と直した後で%s・core の束ねた指紋は%s。" % (u"違う" if diff_ad else u"同じ", u"同じ" if same_core else u"違う")))
    # §1 予測の表
    meas = collections.OrderedDict([
        (u"NRE-1", u"直した engine のそのままの行が NR の「直した入力」の行と違う行 %s・違う本 %s" % (frac(n[u"diff_rows"], n[u"rows"]), frac(n[u"diff_books"], n[u"books"]))),
        (u"NRE-2", u"作られた fact %d・消えた fact %d(%d 本)" % (n[u"made"], n[u"gone"], n[u"books"])),
        (u"NRE-3", u"state が変わった行 %s(%d 本)・直した engine でだけ合う行 %d・直す前でだけ合う行 %d" % (frac(n[u"changed"], n[u"rows"]), n[u"changed_books"], n[u"only_new"], n[u"only_old"])),
        (u"NRE-4", u"違う ZIP %s(封の字の本数は %d + %d = %d)" % (frac(n[u"zip_diff"], n[u"zip_total"]), sum(grp[:4]), grp[4], sum(grp[:4]) + grp[4])),
        (u"NRE-5", u"直す前の式の始まり %d・直した式が拾う始まり %d・始まりの位置が違う本 %d・始まりの数が違う本 %d" % (n[u"st_before"], n[u"st_after"], n[u"pos_diff_books"], n[u"cnt_diff_books"])),
        (u"NRE-6", u"触った既存の試験 file %d 本(engine の commit の差分)" % c.nre6),
        (u"NRE-7", NRE7_MEAS)])
    E.append((u"table head", u"| # | 予測(封の字) | 実測(記録の分子・分母) | 判定 |"))
    for i, v in zip(NRE_IDS, vd):
        E.append((u"table " + i, u"| %s | %s | %s | %s |" % (i, seal_row(c.seal, i), meas[i], v)))
    E.append((u"pred_count", u"- 当たり %d(%s)・外れ %d(%s)。" % (len(hits), u"・".join(hits), len(misses), u"・".join(misses))))
    E.append((u"pred nre4", u"- NRE-4: 封の字は %d + %d = %d 本。記録の分母は %d(便 2026-11-09 の入口 2 つ(`verify_document`・`build_raw_claims`)が各 %d 本を渡すので %d が 2 回)。"
                            u"封は書き換えず、ずれとして残す。違う ZIP は %d で、%d の全部で 0 なので %d の部分集合でも 0。" % (
        sum(grp[:4]), grp[4], sum(grp[:4]) + grp[4], n[u"zip_total"], grp[4], grp[4], n[u"zip_diff"], n[u"zip_total"], sum(grp[:4]) + grp[4])))
    E.append((u"pred nre6", u"- NRE-6: 触った既存の試験 file は %d 本(出どころは engine の commit の差分で、記録には無い。新しく足した試験 file は数えない。封の字は %d 本以上 %d 本以下)。" % (
        c.nre6, b[u"NRE-6"][0], b[u"NRE-6"][1])))
    for k in (u"pred nre5", u"pred nre7 割れ", u"pred nre7 出どころ"):
        E.append((k, FIXED[k]))
    # §2 測った数
    E.append((u"n1 行", u"- 切れた本 %d・行 %d。直した engine にそのままの入力を渡した行が、便 NR の記録の「直した入力」の行と違う行: %s・違う本: %s。" % (
        n[u"books"], n[u"rows"], frac(n[u"diff_rows"], n[u"rows"]), frac(n[u"diff_books"], n[u"books"]))))
    E.append((u"n1 同じ本", u"- 「直した入力」の行と全部同じだった本: %d/%d。" % (b1[u"NR の直した入力の行と同じ本"], n[u"books"])))
    E.append((u"n2 fact", u"- 自己閉じの tag(消した数): %d 個。直した engine の fact の差(そのまま 対 自己閉じを消した入力): 作られた fact %d・消えた fact %d・作られた fact を持つ本 %d・消えた fact を持つ本 %d(切れた本 %d)。" % (
        b2[u"自己閉じの数(消した数)"], n[u"made"], n[u"gone"], n[u"made_books"], n[u"gone_books"], n[u"books"])))
    E.append((u"n2 独立", u"- 独立の読みと直した engine の fact が同じ本: %d/%d。" % (b2[u"独立の読みと直した engine の fact が同じ本"], n[u"books"])))
    E.append((u"n3 行", u"- 直した engine のそのままの行を TSS の記録(直す前)の行と比べた: 行 %d・state が変わった行 %s・変わった行を持つ本 %d。" % (
        n[u"rows"], frac(n[u"changed"], n[u"rows"]), n[u"changed_books"])))
    E.append((u"trans head", u"| TSS の記録(直す前) \\ 直した engine | " + u" | ".join(STATES) + u" |"))
    for a in STATES:
        E.append((u"trans " + a, u"| %s | " % a + u" | ".join(u"%d" % n[u"trans"].get((a, z), 0) for z in STATES) + u" |"))
    E.append((u"st head", u"| state | TSS の記録(直す前) | 直した engine | 差 |"))
    for s in STATES:
        a = sum(v for (x, _y), v in n[u"trans"].items() if x == s)
        z = sum(v for (_x, y), v in n[u"trans"].items() if y == s)
        E.append((u"st " + s, u"| %s | %d | %d | %+d |" % (s, a, z, z - a)))
    E.append((u"n3 向き", u"- 直した engine でだけ値が合う行: %d。直す前でだけ値が合う行(作られた fact に頼っていた一致): %d。" % (n[u"only_new"], n[u"only_old"])))
    nr_t = c.nr[K_NR_JUDGE][K_TRANS_NR]
    my_t = b3[K_TRANS3]
    same = sum(1 for k in my_t if nr_t.get(k) == my_t[k])
    E.append((u"n3 NR", u"- 移り変わりの表は、便 NR の記録の移り変わりの表(そのまま × 直した入力)と同じ欄が %d/%d。" % (same, len(my_t))))
    E.append((u"n4 head", u"| 群 | 読んだ ZIP | facts の列が違う ZIP | 返り値の全体が違う ZIP | `.xbrl` の経路でない ZIP |"))
    for i, k in enumerate(names4):
        v = per4[k]
        label = u"`%s`" % k if i < 4 else k
        E.append((u"n4 " + k, u"| %s | %d | %d | %d | %d |" % (label, v[u"読んだ ZIP"], v[u"facts の列が違う ZIP"], v[u"返り値の全体が違う ZIP"], v[u".xbrl の経路でない ZIP"])))
    E.append((u"n4 合計", u"| 合計 | %d | %d | %d | %d |" % (n[u"zip_total"], n[u"zip_diff"], n[u"zip_whole"], n[u"zip_nonx"])))
    E.append((u"n4 比べ", u"- 比べたのは旧い engine の blob の `load_instance` と今の `load_instance`(読んだ ZIP の合計 %d・facts の列が違う ZIP %d)。" % (n[u"zip_total"], n[u"zip_diff"])))
    E.append((u"n5", u"- 包んだ本 %d。直す前の式の始まり(自己閉じでない)の合計 %d・直した式が拾う始まりの合計 %d・直した式が `finditer` で拾う数 %d。始まりの位置の集合が違う本 %d・始まりの数が違う本 %d。" % (
        b5[u"包んだ本"], n[u"st_before"], n[u"st_after"], n[u"finditer"], n[u"pos_diff_books"], n[u"cnt_diff_books"])))
    E.append((u"detect", FIXED[u"detect"]))
    # §3 読める事
    E.append((u"read 効き", u"- 直した engine にそのままの入力を渡した行は、便 NR の「直した入力」の行と全部同じだった(%d/%d 本)。便 NR の数(state が変わった行 %s・直した側でだけ合う行 %d・直す前でだけ合う行 %d)は、"
                          u"engine の直しの効きとして読める。読めるのは TSS の %d 本のうち切れた %d 本の states に限る。" % (
        n[u"books"] - n[u"diff_books"], n[u"books"], frac(n[u"changed"], n[u"rows"]), n[u"only_new"], n[u"only_old"], mat, n[u"books"])))
    E.append((u"read xbrl", u"- `.xbrl` の経路は、読んだ ZIP の全部(%d)で fact の列が同じだった。" % n[u"zip_total"]))
    for k in (u"limit 1", u"limit 2", u"limit 3", u"limit 4", u"limit 5", u"limit 6", u"limit 7", u"limit 8", u"limit 9", u"limit 10", u"next 1", u"next 2", u"next 3"):
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
    for need in (os.path.basename(SEAL_REL), SEAL_COMMIT_SHORT, ENGINE_COMMIT_SHORT, os.path.basename(SCRIPT_REL), os.path.basename(STATES_REL)) + REQUIRED_PHRASES:
        if need not in doc:
            out.append(u"words: 要点の字が無い: %s" % need)
    return out


LEAD_HEAD = u"**先に負けと限界を書く。**"
LEAD_NEXT = u"## §1 "
LIMIT_HEAD = u"## §4 "
LIMIT_NEXT = u"## §5 "
NRE7_HEAD = u"- NRE-7: "


def section(doc, head, nxt=None):
    if head not in doc:
        return u""
    t = doc[doc.index(head):]
    if nxt is not None and nxt in t[len(head):]:
        t = t[:len(head) + t[len(head):].index(nxt)]
    return t


def limits_problems(c):
    u"""要点の行(負けの節・限界の節)が決めた節に 1 回ずつ在る。NRE-7 の但し書きが外れと出どころを持つ。"""
    out = []
    lead = section(c.doc, LEAD_HEAD, LEAD_NEXT).split(u"\n")
    lim = section(c.doc, LIMIT_HEAD, LIMIT_NEXT).split(u"\n")
    exp = dict(expected_lines(c))
    want = [(k, exp[k], lead) for k in (u"lead 予測", u"lead 小さい", u"lead engine", u"lead 過去", u"lead 弱い", u"lead nre7")]
    want += [(k, exp[k], lim) for k in (u"limit 1", u"limit 2", u"limit 3", u"limit 4", u"limit 5", u"limit 6", u"limit 7", u"limit 8", u"limit 9", u"limit 10")]
    for name, line, where in want:
        if where.count(line) != 1:
            out.append(u"limits: 要点の行が決めた節に 1 回ずつ無い: %s" % name)
    row7 = [l for l in c.doc.split(u"\n") if l.startswith(u"| NRE-7 |")]
    if len(row7) != 1 or MISS not in row7[0] or u"追跡していない" not in row7[0]:
        out.append(u"limits: NRE-7 の表の行が外れと追跡していないという出どころを持たない")
    pr7 = [l for l in c.doc.split(u"\n") if l.startswith(NRE7_HEAD)]
    if len(pr7) != 1 or u"字のとおりに読むと外れ" not in pr7[0] or u"割れ" not in pr7[0]:
        out.append(u"limits: NRE-7 の説明の行が外れと読みの割れを持たない")
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
    for need in (u"**372 本の全部**", u"作られた fact **0**・消えた fact **0**", u"**207**(81 本)", u"違う本 0", u"**44 本以上 56 本以下**", u"## §3 事前予測", u"418", u"17"):
        if need not in c.seal:
            out.append(u"seal: 封に %s が無い" % need)
    try:
        seal_bounds(c.seal)
    except (AttributeError, ValueError, TypeError, IndexError):
        out.append(u"seal: 予測の境が取れない")
    return out


def order_problems_real(root=REPO):
    u"""封 ⊏ engine・script・記録・封の門 ⊑ 結果の文書・この門(未 commit は赤)。"""
    return PR.order_problems(root, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, [INSTANCE_REL, SCRIPT_REL, STATES_REL, SEAL_GATE_REL], [DOC_REL, GATE_REL])


def engine_commit_problems(root=REPO):
    u"""engine の commit が履歴から見つかり、字で持つ短い hash で始まり、差分が instance.py の挿入 1・削除 1 だけ。"""
    _s, e = SG.engine_commit(root, PREFIX, SEAL_REL, SG.ENGINE_FILES)
    if e is None:
        return [u"engine の commit が履歴に無い"]
    out = []
    if not e.startswith(ENGINE_COMMIT_SHORT):
        out.append(u"engine の commit が字で持つ hash と違う")
    return out + list(SG.real_numstat_problems(root))


def engine_problems(root=REPO):
    u"""engine は engine の commit から 0 行(未 commit も)。"""
    _s, e = SG.engine_commit(root, PREFIX, SEAL_REL, SG.ENGINE_FILES)
    if e is None:
        return [u"engine の commit が履歴に無い"]
    rc, txt = PR.git_in(root, "diff", "--numstat", e, "HEAD", "--", PREFIX + "adapters", PREFIX + "core")
    out = [] if rc == 0 and not txt else [u"engine が engine の commit から変わっている: %s" % txt[:60]]
    return out + list(SG.engine_worktree_problems(root)) + list(SG.sha16_problems())


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


def mut_book(col, delta=1, which=0):
    def fn(c):
        c.st[K_BOOKS][which][col] += delta
    return fn


def mut_rows_state(n, col, value):
    u"""最初の n 行の ``col`` を value に書き換える(行の数は変わらない)。"""
    def fn(c):
        for r in c.st[u"行"][:n]:
            r[col] = value
    return fn


# a sha
M(u"a1 states の記録の 1 byte", u"sha", set_text(STATES_REL, lambda t: t + b" "))
M(u"a2 script の 1 byte", u"sha", set_text(SCRIPT_REL, lambda t: t[:-1] + b"#"))
M(u"a3 便 NR の記録の 1 byte", u"sha", set_text(NR_STATES_REL, lambda t: t.replace(b"24531", b"24532", 1)))
# b 記録
M(u"b1 記録の fact の差の数を 1 つ変える(作られた fact)", u"record", bump([K_NRE2, u"作られた fact"]))
M(u"b2 記録の行の state を 1 つ変える", u"record", st_row(0, 3, u"VALUE_MISMATCH"))
M(u"b3 記録の NRE-3 の数を 1 つ変える", u"record", bump([K_NRE3, u"直した engine でだけ値が合う行"]))
M(u"b4 記録の予測の欄(NRE-4)を 1 つ変える", u"record", bump([K_PRED, u"NRE-4 facts の列が違う ZIP / 読んだ ZIP", u"分子"]))
M(u"b5 記録の NRE-4 の群の数を 1 つ変える", u"record", bump([K_NRE4, u"群ごと", u"edinet", u"読んだ ZIP"]))
M(u"b6 記録の本ごとの欄の数を 1 つ変える", u"record", mut_book(2))
M(u"b7 記録の NRE-5 の数を 1 つ変える", u"record", bump([K_NRE5, u"直した式が拾う始まりの合計"]))
M(u"b8 記録に文・値の字を足す", u"record", lambda c: c.st.__setitem__(u"漏れ", u"売上高は前期比 12.3 億円の増加となりました。"))
M(u"b9 記録の NRE-1 の数を 1 つ変える", u"record", bump([K_NRE1, u"NR の直した入力の行と同じ本"], -1))
# c 文書の数・表・散文
M(u"c1 表の実測の分子を 1 つ変える(NRE-3 の行)", u"doc", doc_replace(u"207/24531(0.8%)(81 本)", u"208/24531(0.8%)(81 本)"))
M(u"c2 表の判定の当たりと外れを入れ替える(NRE-1)", u"doc", lambda c: setattr(c, "doc", re.sub(r"(\| NRE-1 \|.*?\| )当たり \|", r"\1**外れ** |", c.doc, count=1)))
M(u"c3 表の判定の当たりと外れを入れ替える(NRE-7)", u"doc", lambda c: setattr(c, "doc", re.sub(r"(\| NRE-7 \|.*?\| )\*\*外れ\*\* \|", r"\1当たり |", c.doc, count=1)))
M(u"c4 表の分母 452 を 435 にする", u"doc", doc_replace(u"違う ZIP 0/452(0.0%)", u"違う ZIP 0/435(0.0%)"))
M(u"c5 散文の数を変える(要約の行の本数)", u"doc", doc_replace(u"(当たり 6・外れ 1)", u"(当たり 5・外れ 2)"))
M(u"c6 散文に記録に無い数を足す", u"doc", doc_append(u"\n- 追記: 12345 行。\n"))
M(u"c7 散文の数を変える(ずれの行の 435)", u"doc", doc_replace(u"418 + 17 = 435 本", u"418 + 17 = 436 本"))
M(u"c8 移り変わりの表の数を 1 つ変える", u"doc", doc_replace(u"| GROUNDED | 6634 | 0 | 0 | 0 |", u"| GROUNDED | 6635 | 0 | 0 | 0 |"))
M(u"c9 state の表の差を変える", u"doc", doc_replace(u"| GROUNDED | 6634 | 6720 | +86 |", u"| GROUNDED | 6634 | 6720 | +85 |"))
M(u"c10 NRE-4 の表の数を 1 つ変える", u"doc", doc_replace(u"| `edinet` | 281 | 0 | 0 | 0 |", u"| `edinet` | 280 | 0 | 0 | 0 |"))
M(u"c11 NRE-5 の数を変える", u"doc", doc_replace(u"直す前の式の始まり(自己閉じでない)の合計 172602", u"直す前の式の始まり(自己閉じでない)の合計 172603"))
M(u"c12 NRE-6 の本数を変える(表)", u"doc", doc_replace(u"触った既存の試験 file 51 本(engine の commit の差分)", u"触った既存の試験 file 50 本(engine の commit の差分)"))
M(u"c13 NRE-6 の本数を変える(散文)", u"doc", doc_replace(u"触った既存の試験 file は 51 本", u"触った既存の試験 file は 52 本"))
M(u"c14 記録から組んだ行を消す(切れない本の数)", u"doc", doc_replace(u"切れない本 28 は", u"切れない本 は"))
M(u"c15 禁止語を doc の check にも通す(証明した)", u"doc", doc_append(u"\n証明" + u"した。\n"))
M(u"c16 散文の数を変える(読める事の 400 本)", u"doc", doc_replace(u"TSS の 400 本のうち切れた", u"TSS の 401 本のうち切れた"))
M(u"c17 散文に記録に無い数を足す(限界の節の途中)", u"doc", doc_replace(u"英文短信の側(`sales/`)は", u"英文短信の側 4321 (`sales/`)は"))
M(u"c18 NRE-7 の「赤 1」の字を変える", u"doc", doc_replace(u"全数は `tests/measure` で赤 1(`test_xbrl_axis3_decision.py`", u"全数は `tests/measure` で赤 0(`test_xbrl_axis3_decision.py`"))
M(u"c19 便 NR と同じ欄の数を変える(移り変わりが同じ欄の数)", u"doc", doc_replace(u"同じ欄が 16/16", u"同じ欄が 15/16"))
# d 判定
M(u"d1 行 1 つの「同じか」を False にして NRE-1 を外れに動かす", u"judge", st_row(0, 4, False))
M(u"d2 本ごとの欄の作られた fact を 1 にして NRE-2 を外れに動かす", u"judge", mut_book(2))
M(u"d3 行の直した engine の state を 1 行だけ変えて NRE-3 を外れに動かす", u"judge", st_row(0, 3, u"POINTER_NOT_FOUND"))
M(u"d4 NRE-4 の群の違う ZIP を 1 にして NRE-4 を外れに動かす", u"judge", bump([K_NRE4, u"群ごと", u"edinet", u"facts の列が違う ZIP"]))
M(u"d5 本ごとの欄の直した式の始まりを 1 変えて NRE-5 を外れに動かす", u"judge", mut_book(5))
M(u"d6 触った試験 file の数を 57 にして NRE-6 を外れに動かす", u"judge", lambda c: setattr(c, "nre6", 57))
M(u"d7 触った試験 file の数を 43 にして NRE-6 を外れに動かす", u"judge", lambda c: setattr(c, "nre6", 43))
M(u"d8 判定の欄(NRE-1)を 1 つ変える", u"judge", bump([K_PRED, u"NRE-1 NR の直した入力の行と違う行 / 行", u"分子"]))
M(u"d9 変わった行を行の 1% 以上にして要約の字を偽にする", u"judge", mut_rows_state(300, 3, u"VALUE_MISMATCH"))
# e 語
M(u"e1 禁止語(ハルシネーション)", u"words", doc_append(u"\nハルシ" + u"ネーション\n"))
M(u"e2 会社名らしい字", u"words", doc_append(u"\n株式会社\n"))
M(u"e3 3 桁以上の漢数字", u"words", doc_append(u"\n二百社\n"))
M(u"e4 docID の形", u"words", doc_append(u"\nS100" + u"AB12\n"))
M(u"e5 要点の字を消す(確かめていない)", u"words", doc_replace(u"確かめていない", u"確かめた", True))
M(u"e6 封の commit を言わない", u"words", doc_replace(u"36ca78f1", u"0000000", True))
M(u"e7 禁止語(人の目)", u"words", doc_append(u"\n人の" + u"目で読んだ。\n"))
M(u"e8 要点の字を消す(恒等に近い)", u"words", doc_replace(u"恒等に近い", u"恒等ではない", True))
M(u"e9 engine の commit を言わない", u"words", doc_replace(u"d86c5506", u"0000000", True))
# 要点の文
M(u"l1 負けの節の要点の文を変える(旗なし)", u"limits", doc_replace(FIXED[u"lead engine"], u"- engine を直した。"))
M(u"l2 限界の節の要点の文を変える(全数)", u"limits", doc_replace(FIXED[u"limit 7"], u"- 全数は走らせた。"))
M(u"l3 限界の節の要点の文を変える(門)", u"limits", doc_replace(FIXED[u"limit 6"], u"- 封の門は全部を縛っている。"))
M(u"l4 負けの節の NRE-7 の文を変える", u"limits", doc_replace(FIXED[u"lead nre7"], u"- NRE-7 は当たり。"))
M(u"l5 NRE-7 の表の行から出どころを消す", u"limits", doc_replace(u"実装の席の走らせた記録・追跡していない)", u"実装の席の走らせた記録)"))
M(u"l6 NRE-7 の説明から読みの割れを消す", u"limits", doc_replace(u"(割れを隠さない)", u"(隠さない)"))
M(u"l7 限界の節の過去の記録の文を変える", u"limits", doc_replace(FIXED[u"limit 2"], u"- 取り直した。"))
# f 封
M(u"f1 封の NRE-3 の字を替える(根の字)", u"seal", seal_replace(u"**207**(81 本)", u"**208**(81 本)"))
M(u"f2 封の NRE-6 の字を替える", u"seal", seal_replace(u"**44 本以上 56 本以下**", u"**44 本以上 57 本以下**"))
M(u"f3 封の文の途中の 1 字", u"frozen", seal_replace(u"同じ数が出ることを予測に置いて", u"同じ数が出ることを予測に置いた"))
M(u"f4 封の NRE-6 の境を替える(判定が動く)", u"judge", seal_replace(u"**44 本以上 56 本以下**", u"**44 本以上 50 本以下**"))
M(u"f5 封の NRE-3 の境を替える(判定が動く)", u"judge", seal_replace(u"**207**(81 本)", u"**208**(81 本)"))


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
        self.assertEqual(SHA_PIN[NR_STATES_REL], [i for i in c.st[u"入力"] if i[u"path"] == NR_STATES_REL][0][u"sha256"])

    def test_b_1_the_record_equals_the_recount_from_its_rows(self):
        self.assertEqual([], record_problems(Ctx()))

    def test_c_1_the_document_lines_equal_the_lines_rebuilt_from_the_records(self):
        self.assertEqual([], doc_problems(Ctx()))

    def test_c_2_the_rebuilt_lines_are_the_ones_the_brief_names(self):
        c = Ctx()
        exp = dict(expected_lines(c))
        self.assertIn(u"0/24531(0.0%)", exp[u"table NRE-1"])
        self.assertIn(u"作られた fact 0・消えた fact 0(372 本)", exp[u"table NRE-2"])
        self.assertIn(u"207/24531(0.8%)(81 本)・直した engine でだけ合う行 86・直す前でだけ合う行 0", exp[u"table NRE-3"])
        self.assertIn(u"0/452(0.0%)", exp[u"table NRE-4"])
        self.assertIn(u"418 + 17 = 435", exp[u"table NRE-4"])
        self.assertIn(u"172602", exp[u"table NRE-5"])
        self.assertIn(u"51 本", exp[u"table NRE-6"])
        self.assertIn(u"| POINTER_NOT_FOUND | 81 | 10 | 65 | 11008 |", exp[u"trans POINTER_NOT_FOUND"])
        self.assertIn(u"435", exp[u"pred nre4"])
        self.assertIn(u"452", exp[u"pred nre4"])

    def test_d_1_the_judgement_is_redone_from_the_seal_text_the_records_and_the_engine_commit(self):
        self.assertEqual([], judge_problems(Ctx()))

    def test_d_2_the_real_judgement_is_six_hits_and_one_miss(self):
        c = Ctx()
        self.assertEqual([i for i, v in zip(NRE_IDS, verdicts(c)) if v == MISS], [u"NRE-7"])
        self.assertEqual([i for i, v in zip(NRE_IDS, verdicts(c)) if v == HIT], [u"NRE-1", u"NRE-2", u"NRE-3", u"NRE-4", u"NRE-5", u"NRE-6"])

    def test_d_3_the_bounds_are_read_from_the_seal_text(self):
        self.assertEqual(seal_bounds(Ctx().seal), {u"NRE-1": (372, 24531), u"NRE-2": (0, 0), u"NRE-3": (207, 81, 86, 0), u"NRE-4": 0, u"NRE-5": 0, u"NRE-6": (44, 56)})

    def test_d_4_the_nre6_count_comes_from_the_engine_commit_diff(self):
        self.assertEqual(51, NRE6_REAL)
        self.assertEqual(51, nre6_count())

    def test_e_1_the_words_are_clean(self):
        self.assertEqual([], words_problems(Ctx()))

    def test_e_2_the_seal_has_the_texts_the_document_roots_on(self):
        self.assertEqual([], seal_text_problems(Ctx()))

    def test_e_3_the_lead_and_the_limits_have_their_lines(self):
        self.assertEqual([], limits_problems(Ctx()))

    def test_e_4_the_nre4_divergence_is_in_the_record_groups_and_the_seal_is_not_rewritten(self):
        c = Ctx()
        grp = [v[u"読んだ ZIP"] for v in c.st[K_NRE4][u"群ごと"].values()]
        self.assertEqual(grp, [281, 3, 40, 94, 17, 17])
        self.assertEqual(sum(grp[:4]) + grp[4], 435)
        self.assertEqual(sum(grp), 452)
        self.assertIn(u"EDINET 418 本・便 2026-11-09 の 17 本", seal_row(c.seal, u"NRE-4"))

    def test_f_1_the_seal_is_the_text_of_the_sealed_commit(self):
        self.assertEqual([], seal_frozen_problems(Ctx()))

    def test_f_2_the_real_history_has_the_seal_before_the_engine_before_the_document_and_this_gate(self):
        u"""文書・この門のどれかが未 commit なら赤(足した commit が無い。skip にしない)。全部 commit された後で初めて緑。"""
        self.assertEqual([], order_problems_real())

    def test_f_3_the_real_order_failure_before_the_commit_is_only_the_uncommitted_files(self):
        got = order_problems_real()
        self.assertTrue(all(p.startswith(u"UNCOMMITTED:") for p in got), got)

    def test_f_4_the_order_check_names_exist(self):
        for rel in (SCRIPT_REL, STATES_REL, SEAL_GATE_REL, DOC_REL, GATE_REL, NR_STATES_REL, INSTANCE_REL):
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)

    def test_f_5_engine_is_untouched_since_the_engine_commit(self):
        self.assertEqual([], engine_problems())

    def test_f_6_the_engine_commit_is_the_one_in_the_history(self):
        self.assertEqual([], engine_commit_problems())


class OrderGateTest(unittest.TestCase):
    u"""順序の検査自体が、悪い順を赤にできること(使い捨ての git で)。"""

    def test_o_1_good_and_bad_orders(self):
        r = PR.Repo()
        r.put("docs/seal.md")
        s = r.commit("docs/seal.md")
        r.put("adapters/xbrl/instance.py")
        r.put("measure/s.py")
        r.commit("adapters/xbrl/instance.py", "measure/s.py")
        others = ["docs/r.md", "tests/g.py"]
        for o in others:
            r.put(o)
        impls = ["adapters/xbrl/instance.py", "measure/s.py"]
        self.assertEqual([u"UNCOMMITTED:" + o for o in others], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], impls, others))
        r.commit(*others)
        self.assertEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], impls, others))
        r2 = PR.Repo()
        r2.put("docs/seal.md")
        s2 = r2.commit("docs/seal.md")
        r2.put("docs/r.md")
        r2.commit("docs/r.md")
        r2.put("adapters/xbrl/instance.py")
        r2.commit("adapters/xbrl/instance.py")
        self.assertNotEqual([], PR.order_problems(r2.d, PREFIX, "docs/seal.md", s2[:7], ["adapters/xbrl/instance.py"], ["docs/r.md"]))      # 文書が engine より前


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
        rels = (STATES_REL, SCRIPT_REL, NR_STATES_REL, SEAL_REL, DOC_REL)
        before = dict((rel, hashlib.sha256(read_bytes(rel)).hexdigest()) for rel in rels)
        c = Ctx()
        c.st[u"行"][0][3] = u"x"
        c.doc = u"x"
        self.assertNotEqual(u"x", Ctx().st[u"行"][0][3])
        self.assertNotEqual(u"x", Ctx().doc)
        self.assertEqual(before, dict((rel, hashlib.sha256(read_bytes(rel)).hexdigest()) for rel in rels))

    def test_m_4_the_mutation_table_covers_every_check_and_every_effect_named_in_the_brief(self):
        self.assertEqual(set(CHECKS), set(ch for _l, ch, _f in MUTATIONS))
        labels = u"\n".join(l for l, _c, _f in MUTATIONS)
        for need in (u"states の記録の 1 byte", u"script の 1 byte", u"表の実測の分子", u"当たりと外れを入れ替える", u"散文の数", u"散文に記録に無い数", u"禁止語", u"漢数字",
                     u"要点の文", u"封の文の途中の 1 字", u"NRE-1 を外れに動かす", u"NRE-4 を外れに動かす", u"NRE-6 を外れに動かす", u"分母 452 を 435", u"NRE-7"):
            self.assertIn(need, labels)

    def test_m_5_a_hit_turned_to_a_miss_is_caught_by_the_judge_and_not_only_by_the_table(self):
        c = Ctx()
        bump([K_NRE4, u"群ごと", u"edinet", u"facts の列が違う ZIP"])(c)               # NRE-4 が外れに動く。文書の表は当たりのまま
        jd = dict(nre_judge(c))
        self.assertFalse(jd[u"NRE-4"])
        self.assertNotEqual([], judge_problems(c))

    def test_m_6_the_judge_follows_the_seal_bounds_not_a_pinned_number(self):
        c = Ctx()
        c.nre6 = 60
        self.assertFalse(dict(nre_judge(c))[u"NRE-6"])
        c.seal = c.seal.replace(u"**44 本以上 56 本以下**", u"**44 本以上 60 本以下**", 1)
        self.assertTrue(dict(nre_judge(c))[u"NRE-6"])

    def test_m_7_the_nre7_miss_is_not_decided_by_the_records(self):
        c = Ctx()
        self.assertEqual(verdicts(c)[-1], MISS)
        self.assertEqual(len(nre_judge(c)), 6)


class WiringTest(unittest.TestCase):
    def test_n_1_this_gate_carries_no_docid_and_no_key(self):
        src = read(GATE_REL)
        for bad in (u"ANTHRO" + u"PIC", u"API_" + u"KEY", u"url" + u"lib", u"sock" + u"et"):
            self.assertNotIn(bad, src)
        self.assertIsNone(DOCID_RE.search(src))

    def test_n_2_this_gate_does_not_widen_the_boundary_import_list(self):
        with io.open(os.path.join(ROOT, "tests", "adapters", "xbrl", "test_boundary.py"), encoding="utf-8") as fh:
            t = fh.read()
        self.assertNotIn(u"nil_read_engine", t)
        self.assertNotIn(u"nre_result", t)

    def test_n_3_this_gate_does_not_use_the_reserved_names(self):
        self.assertEqual([], SG.reserved_problems(rel=GATE_REL))


if __name__ == "__main__":
    unittest.main()
