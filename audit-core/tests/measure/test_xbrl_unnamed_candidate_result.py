# -*- coding: utf-8 -*-
u"""候補の欄(``candidate``)の測定の門。封 docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md §3(CA-1〜CA-11)・§4(K-1〜K-4)・§7-5 の (a)〜(j)。

記録 ``fixtures/xbrl/unnamed_candidate_2026-10-29.json``(``measure/xbrl_unnamed_candidate_2026-10-29.py`` の出力)・文書 ``docs/XBRL_UNNAMED_CANDIDATE_RESULT_2026-10-29.md``。

  (a) 記録の書類(97 = 67 + 30)が ``regress97``・``fetched`` の書類と同じ、注入 741 行の id が ``fresh_2026-10-21.json`` の ``注入の行`` と集合も型別の数も同じ。
  (b) 配線の門(97 書類・741 行)を門が自分で ``regress97``・``stop_reason_2026-10-29.json``・``fetched`` から数え直して、記録の数と一致する。
  (c) 文書の表を記録から作り直して 1 行も違わない(``<!-- 門:start 名前 -->`` の中)。門の外の散文の数には【門なし】の印が要る。
  (d) CA-1〜CA-11 の当否と K-1〜K-4 の判定を記録から求める(幅・数は封の表の字から読む。CA-9・CA-11 は段 1 の試験の結果を写した事実で、CA-9 は golden の定数が比べる側の commit と同じ字かを門が見る)。
      封の字(欄・予測・外れ方)と、文書の当否の表の字が一致する。K の判定は記録から機械で求め、記録の ``採用`` の欄と一致する。
  (e) 記録の中の数の整合: 書類ごとの数と行の一覧(候補の行・P27EC の行・741 行)から数え直した数が一致する。候補の中身(pointer・value)を診断の記録 ``unnamed_fact_2026-10-29.json`` と引き直す。
  (f) engine の sha16 を ``ENGINE_AT_MEASURE``(測った時点の値。段 1 の後)と ``ENGINE_DECLARED``(宣言された遷移。今は空)で留める。比べる側の値は ``git show`` で引き直す。
  (g) 偽物で赤: 記録の写しを 1 か所変えると (b)(c)(d)(e) が赤。文書の表の 1 字で (c)、封の幅の 1 字で (d)、文書に docID を足すと (h) が赤。
  (h) 文書に docID・記録の claim の id・提出者別の接頭辞の字が無い。
  (i) 順序: 封の commit < 実装(engine の候補の欄)の commit <= 記録の commit(script・記録・文書・門)。追跡されていない file は『足した commit が無い』で赤(skip にしない)。
  (j) 記録が持つ読んだ入力の sha256 がいまの file と一致する。

**(i) は、実装・script・記録・文書・門のどれかが commit される前は赤になる**(順序の門の「未 commit」分。skip にしない)。前例 ``test_xbrl_unnamed_fact.py`` と同じ扱い。
**変数名について**: 過去の門が tests/measure の行頭の名前を数えるので、この門は ``ENGINE_AT_MEASURE``・``ENGINE_DECLARED`` 以外の留めの名前を行頭に置かない。この file は docID の字を持たない(``fetched_2026-10-21.json`` から読む)。
"""
import collections
import copy
import hashlib
import io
import json
import os
import re
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"

SEAL_REL = "docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md"
DOC_REL = "docs/XBRL_UNNAMED_CANDIDATE_RESULT_2026-10-29.md"
REC_REL = "fixtures/xbrl/unnamed_candidate_2026-10-29.json"
SCRIPT_REL = "measure/xbrl_unnamed_candidate_2026-10-29.py"
GATE_REL = "tests/measure/test_xbrl_unnamed_candidate_result.py"
IMPL_REL = "adapters/xbrl/verify_document.py"
STOP_REL = "fixtures/xbrl/stop_reason_2026-10-29.json"
FRESH_REL = "fixtures/xbrl/fresh/fresh_2026-10-21.json"
FETCHED_REL = "fixtures/xbrl/fresh/fetched_2026-10-21.json"
REGRESS_REL = "fixtures/xbrl/p27/regress97_2026-10-27.json"
UNNAMED_REL = "fixtures/xbrl/unnamed_fact_2026-10-29.json"
P26_REL = "fixtures/xbrl/p26_2026-10-21.json"
DEFAULT27_REL = "fixtures/xbrl/default_p27_2026-10-28.json"
ROSTER_REL = "fixtures/xbrl/taxonomy_labels_sha256.txt"
INPUT_RELS = [P26_REL, FETCHED_REL, REGRESS_REL, STOP_REL, UNNAMED_REL, FRESH_REL, DEFAULT27_REL, ROSTER_REL]
SEAL, DOC, REC = [os.path.join(ROOT, r) for r in (SEAL_REL, DOC_REL, REC_REL)]
SCRIPT = os.path.join(ROOT, SCRIPT_REL)
SEAL_COMMIT_SHORT = "0df5222"
APPROVAL_COMMIT_SHORT = "db68a2c"
BASE_COMMIT = "020ffc0"
MAIN_TYPES = ("T1_VALUE", "T2_UNIT", "T5_COINCIDENT")
TSHORT = {"T1_VALUE": u"T1", "T2_UNIT": u"T2", "T5_COINCIDENT": u"T5", "T3_ABSENT": u"T3"}
NOT_GATED = u"【門なし】"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
FORBIDDEN = (u"精度", u"ハルシネーション", u"証明した", u"LLM より正確", u"世界で 1 社", u"貴社の DB の誤り", u"取り戻す")
STATES4 = ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND")
NSV = "no_same_value"
CAND_MARK = u"。候補: "
CLAIM_KEYS = ("id", "kind", "form", "value", "unit", "span", "state", "reason", "pointers", "recomputed")

#: engine の sha16(測った時点の値。字で留める ― 測った事実。段 1 の実装の後の 7 本 = 封 §2-1 の 3 file のうち 2 つ(vocabulary・verify_document)と report_customer が 020ffc0 から動いた値)。
#: 変えるなら宣言された遷移として下の ENGINE_DECLARED に足す。
ENGINE_AT_MEASURE = {
    "adapters/xbrl/extract.py": "3cf55966f12919f0", "adapters/xbrl/vocabulary.py": "7fbcfbf0e472f366", "adapters/xbrl/recipes.py": "52d645e713c53c1c",
    "adapters/xbrl/resolve.py": "a41043763c1d4073", "adapters/xbrl/comparators.py": "d8706338325e725b", "adapters/xbrl/verify_document.py": "6c76c8ade6c7b1c8",
    "adapters/xbrl/report_customer.py": "bdbaa00a419219fe",
}
#: 比べる側(020ffc0)の値。門が ``git show 020ffc0:...`` で引き直して照らす(字で留める ― 測った事実)。
BASE_ENGINE = {
    "adapters/xbrl/extract.py": "3cf55966f12919f0", "adapters/xbrl/vocabulary.py": "514ebb8104451c07", "adapters/xbrl/recipes.py": "52d645e713c53c1c",
    "adapters/xbrl/resolve.py": "a41043763c1d4073", "adapters/xbrl/comparators.py": "d8706338325e725b", "adapters/xbrl/verify_document.py": "c3791080ab5aef2f",
    "adapters/xbrl/report_customer.py": "6679138d350ec382",
}
#: 宣言された遷移 {file: (遷移の後の sha16, その遷移を宣言した封)}。今は 0 件。足すときは、封が履歴に在り、値が宣言の値のときだけ受け入れる。測った時点の値は消さない。
ENGINE_DECLARED = {}

#: CA-9・CA-11 は engine を走らせる測定でなく、段 1 の試験の結果(db68a2c の試験 + 段 1 の engine)を測り直した事実。字で留める(出どころは文書の第 6 節)。
#: CA-9 の「緑」の側は門が測れない(golden の定数が HEAD と同じ字であることだけ門が見る)。値は (当たりか, 実測の字)。
STAGE1_FACTS = {
    "CA-9": (True, u"既存の golden の試験(db68a2c の test_report_customer.py に段 1 の engine を当てた)は赤 0 本。SMALL_GOLDEN・UNITS_GOLDEN・GOLDEN_SHA256 の 4 値は今の値のまま緑(段 1 の席と、使い捨て clone での測り直し)"),
    "CA-11": (False, u"tests/adapters/xbrl(db68a2c の試験に段 1 の engine を当てた。test_mutations は別に走らせた)の赤は 21 本: test_verify_entry の本体の sha256 が 5 本(予測どおり)・"
                     u"test_vocabulary が 3 本(予測は 2 本)・test_recipes_p27 が 2 本(予測は 0 本)・旗の継承の一覧を字で持つ別の file の試験が 11 本(test_p17 1・test_p20 1・test_recipes_p21 1・p22 2・p23 2・p24 1・p25 2・p26 1。予測に無い file)。"
                     u"test_report_customer は 0 本(予測どおり)。"
                     u"tests/measure(同じ条件。使い捨て clone で全部走らせた)の赤は 37 file・91 本で、file の集合は封 §2-3 の和集合と同じ(予測どおり。本数は予測しなかった)"),
}
#: 記録から求めた当否のうち外れ・判定しないの名前(測った事実。外れは外れのまま残す。封も予測も直さない)。食い違えば d_5 が赤。
MISSES = ["CA-2", "CA-11"]
UNDECIDED = []
GOLDEN_FILE = "tests/adapters/xbrl/test_report_customer.py"
GOLDEN_NAMES = ("SMALL_GOLDEN", "UNITS_GOLDEN", "GOLDEN_SHA256")


def jtext(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def jload(p):
    return json.loads(jtext(p))


def rload(rel):
    return jload(os.path.join(ROOT, rel))


def sha16(rel):
    with io.open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def sha64(rel):
    with io.open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)


def yesno(b):
    return u"はい" if b else u"いいえ"


def n_of(n, d):
    return u"%d / %d" % (n, d)


def table(head, rows):
    lines = [u"| " + u" | ".join(head) + u" |", u"|" + u"|".join(u"---" for _ in head) + u"|"]
    for r in rows:
        lines.append(u"| " + u" | ".join(str(c) for c in r) + u" |")
    return lines


def inputs():
    u"""門が読む入力(記録以外)。"""
    return {"fresh": rload(FRESH_REL), "fetched": rload(FETCHED_REL), "stop": rload(STOP_REL), "reg": rload(REGRESS_REL), "unn": rload(UNNAMED_REL),
            "p26": rload(P26_REL)}


def dumps(v):
    return json.dumps(v, sort_keys=True, ensure_ascii=False)


# ----------------------------------------------------------------------------------------------------------------
# 記録の読み出し
def doc_split(rec):
    per = rec[u"書類ごと"]
    docs = rec[u"書類(出てくる順)"]
    return [d for d in docs if per[d][u"標本"] == u"手元の 67"], [d for d in docs if per[d][u"標本"] == u"新しい標本 30"]


def reg_states(reg):
    return dict((x["docID"], x[u"4 state"]) for x in reg[u"書類"])


def full4(s):
    return dict((k, s.get(k, 0)) for k in STATES4)


# ----------------------------------------------------------------------------------------------------------------
# (a)(b)(e)(j)
def check_a(rec, inp):
    out = []
    reg = inp["reg"]
    v67, v30 = doc_split(rec)
    regd = dict((x["docID"], x) for x in reg[u"書類"])
    if sorted(v67) != sorted(d for d, x in regd.items() if x[u"標本"] == u"手元の 67"):
        out.append(u"手元の 67 の書類が regress97 と違う")
    if v30 != list(inp["fetched"][u"使う書類"]) and sorted(v30) != sorted(inp["fetched"][u"使う書類"]):
        out.append(u"新しい標本 30 の書類が fetched の使う書類と違う")
    if rec[u"書類(出てくる順)"] != v67 + v30:
        out.append(u"書類の並びが 67 → 30 でない")
    if len(v67) != 67 or len(v30) != 30:
        out.append(u"書類の数が 67 + 30 でない")
    fresh_ids = [r["id"] for r in inp["fresh"][u"注入の行"]]
    mine = [r["id"] for r in rec[u"注入 741 行"]]
    if sorted(mine) != sorted(fresh_ids):
        out.append(u"注入 741 行の id の集合が fresh と違う")
    tf = collections.Counter(r[u"型"] for r in inp["fresh"][u"注入の行"])
    tm = collections.Counter(r[u"型"] for r in rec[u"注入 741 行"])
    if tf != tm:
        out.append(u"注入 741 行の型別の数が fresh と違う")
    return out


def check_b(rec, inp):
    u"""配線の門を門が自分で数え直す。"""
    out = []
    reg, fetched, stop = inp["reg"], inp["fetched"], inp["stop"]
    rs = reg_states(reg)
    regd = dict((x["docID"], x) for x in reg[u"書類"])
    per = rec[u"書類ごと"]
    sha30 = dict((r["docID"], r["sha256"]) for r in fetched[u"取得した書類"] if r.get(u"使う"))
    sha67 = inp["p26"][u"入力の sha256"][u"書類 67(経営分析の文を持つ)の sha256"]
    for d in rec[u"書類(出てくる順)"]:
        if per[d][u"zip の sha256"] != regd[d][u"zip の sha256"] or per[d][u"zip の sha256"] != (sha67.get(d) or sha30.get(d)):
            out.append(u"ZIP の sha256 が記録と違う")
            break
    bad_b = bad_n = bad_e = 0
    for d in rec[u"書類(出てくる順)"]:
        for p in ("P22", "P27"):
            if per[d][u"比べる側"][p][u"4 state"] != full4(rs[d][p]):
                bad_b += 1
            if per[d][u"profiles"][p][u"4 state"] != full4(rs[d][p]):
                bad_n += 1
        if per[d][u"profiles"]["P27C"][u"4 state"] != full4(rs[d]["P27"]):
            bad_n += 1
        if per[d][u"標本"] == u"新しい標本 30":
            for p in ("P27E", "P27EC"):
                if per[d][u"profiles"][p][u"4 state"] != full4(rs[d]["P27E"]):
                    bad_e += 1
            if per[d][u"比べる側"]["P27E"][u"4 state"] != full4(rs[d]["P27E"]):
                bad_b += 1
    if bad_b:
        out.append(u"比べる側の 4 state が regress97 と違う書類・profile が %d" % bad_b)
    if bad_n:
        out.append(u"いまの engine の 4 state が regress97 と違う書類・profile が %d" % bad_n)
    if bad_e:
        out.append(u"P27E・P27EC の 4 state が regress97 の P27E と違う書類が %d" % bad_e)
    meta = rec[u"ラベル"][u"読んだ file"]
    roster = [l.split(None, 1)[1].strip() for l in jtext(os.path.join(ROOT, ROSTER_REL)).splitlines() if l.strip() and not l.startswith("#")]
    if sorted(m["file"] for m in meta) != sorted(roster) or any(m["status"] != "used" for m in meta):
        out.append(u"標準ラベルが名簿どおりに全部読まれていない")
    # 741 行
    srow = dict((r["id"], r) for r in stop[u"rows"])
    n = 0
    for r in rec[u"注入 741 行"]:
        o = srow[r["id"]]
        oc = o[u"profile"]["P27"]["claim"] if r[u"型"] == "T3_ABSENT" else o[u"profile"]["P27"][u"注入後"]["claim"]
        if oc is None:
            n += int(r["state"] is None and r["reason"] is None and r["pointers"] is None)
        else:
            n += int(r["state"] == oc["state"] and r["reason"] == oc["reason"] and r["pointers"] == oc["pointers"])
        if r[u"P27(旗が偽)の candidate"] is not None or r[u"P27(旗が偽)の candidate の欄が在る"] is not True and oc is not None:
            out.append(u"旗が偽の P27 の注入後の claim に候補が在る・欄が無い")
            break
        if not r[u"state・reason・pointers が stop_reason の P27 と同じ"] or not r[u"claim の 10 欄が stop_reason の P27 と同じ"]:
            out.append(u"741 行の一致の旗が偽")
            break
    if n != len(rec[u"注入 741 行"]):
        out.append(u"741 行の state・reason・pointers が stop_reason と %d / %d" % (n, len(rec[u"注入 741 行"])))
    g = rec[u"配線の門"]
    if not (g[u"通った"] and g[u"97 書類"][u"通った"] and g[u"741 行"][u"通った"]):
        out.append(u"記録の配線の門が通っていない")
    if rec[u"全書類"] is not True:
        out.append(u"全書類の記録でない")
    if rec[u"key_leaks"] != []:
        out.append(u"key_leaks が空でない")
    c = rec[u"cache"]
    if not (c[u"変化なし"] and c[u"開始"] == c[u"終了"] and c[u"開始"][u"edinet"][u"件数"] == 281 and c[u"開始"][u"edinet-fresh-2026-10-21"][u"件数"] == 40):
        out.append(u"cache の前後が 281 / 40 で不変でない")
    if rec[u"DEFAULT_PROFILE"] != "P27":
        out.append(u"DEFAULT_PROFILE が P27 でない")
    return out


def check_e(rec, inp):
    u"""記録の数の整合: 書類ごとの数と行の一覧から数え直した数が一致する。候補の中身を診断の記録から引き直す。"""
    out = []
    per = rec[u"書類ごと"]
    cand = rec[u"候補の行(P27C。reason が no_same_value か候補が辞書の行)"]
    by_doc = collections.defaultdict(list)
    for x in cand:
        by_doc[x["doc"]].append(x)
    for d in rec[u"書類(出てくる順)"]:
        rows = by_doc.get(d, [])
        pc = per[d][u"profiles"]["P27C"]
        if pc[u"候補が辞書の行"] != sum(1 for x in rows if x["candidate"] is not None):
            out.append(u"書類ごとの候補が辞書の行が行の一覧と違う")
        if pc[u"reason が no_same_value の行"] != sum(1 for x in rows if x["reason"] == NSV):
            out.append(u"書類ごとの no_same_value の行が行の一覧と違う")
        for p in ("P22", "P27", "P27E"):
            if p in per[d][u"profiles"] and per[d][u"profiles"][p][u"候補が辞書の行"] != 0:
                out.append(u"旗が偽の profile に候補が辞書の行がある")
        for x in rows:
            c = x["candidate"]
            if c is not None and (list(c.keys()) != ["pointer", "value", "basis"] or c["basis"] != NSV or not str(c["pointer"]).startswith("xbrl:")):
                out.append(u"候補の鍵の並び・basis・pointer の形が違う")
        # 4 state の和 = claims
        for p, it in per[d][u"profiles"].items():
            if sum(it[u"4 state"].values()) != it[u"claims"]:
                out.append(u"4 state の和が claims と違う")
        if per[d][u"profiles"]["P27C"][u"欄の並び"][-1] != "candidate" or len(per[d][u"profiles"]["P27C"][u"欄の並び"]) != 13:
            out.append(u"出力の欄が 13 で末尾が candidate でない")
    # 診断の記録から候補の中身を引き直す
    named = dict(((x["doc"], x["id"]), x) for x in inp["unn"][u"plain_rows"])
    v67, v30 = doc_split(rec)
    for x in cand:
        if x["doc"] in v30 and x["candidate"] is not None:
            u = named.get((x["doc"], x["id"]))
            if u is None or u[u"named"] != x["candidate"]["pointer"] or u[u"named の value"] != x["candidate"]["value"]:
                out.append(u"候補の中身が診断の記録の named と違う")
                break
    # 741 行
    urow = dict((x["id"], x) for x in inp["unn"][u"rows"])
    for r in rec[u"注入 741 行"]:
        u = urow[r["id"]]
        if (r["candidate"] is not None) != (r["reason"] == NSV):
            out.append(u"741 行で候補が辞書の行と no_same_value の行が違う")
            break
        if r["candidate"] is not None and r["candidate"]["pointer"] != u[u"named"]:
            out.append(u"741 行の候補が診断の named と違う")
            break
        if r[u"型"] != "T3_ABSENT" and r[u"基準の先頭(P27C の無改変。この process で引いた)"] != u[u"基準の先頭"]:
            out.append(u"基準の先頭がこの process で引いた値と診断の記録で違う")
            break
        if r[u"P22 の注入後の先頭(この process で引いた)"] != u[u"P22 の注入後の先頭"]:
            out.append(u"P22 の注入後の先頭がこの process で引いた値と診断の記録で違う")
            break
    # P27EC の行
    e = rec[u"P27EC の行(30 書類。P27・P27EC のどちらかで reason が no_same_value か候補が辞書の行)"]
    for d in v30:
        mine = [x for x in e if x["doc"] == d]
        if per[d][u"profiles"]["P27EC"][u"候補が辞書の行"] != sum(1 for x in mine if x["candidate"] is not None):
            out.append(u"P27EC の書類ごとの候補が辞書の行が一覧と違う")
        if per[d][u"profiles"]["P27EC"][u"reason が no_same_value の行"] != sum(1 for x in mine if x["reason"] == NSV):
            out.append(u"P27EC の書類ごとの no_same_value の行が一覧と違う")
        if per[d][u"profiles"]["P27"][u"reason が no_same_value の行"] != sum(1 for x in mine if x[u"P27 の reason"] == NSV):
            out.append(u"P27 の書類ごとの no_same_value の行が P27EC の一覧と違う")
    return out


def check_j(rec):
    out = []
    got = rec[u"読んだ入力の sha256"]
    if sorted(got) != sorted(INPUT_RELS):
        out.append(u"読んだ入力の sha256 の file が %d 個でない" % len(INPUT_RELS))
    for rel in INPUT_RELS:
        if got.get(rel) != sha64(rel):
            out.append(u"%s の sha256 が記録の写しと違う(読み直しの元が動いた)" % rel)
    return out


# ----------------------------------------------------------------------------------------------------------------
# (d) CA-1〜CA-11 の当否を記録から求める(幅・数は封の表の字から読む)
BOLD = re.compile(r"\*\*(.+?)\*\*")
RANGE_RE = re.compile(r"^(\d[\d,]*) 以上 (\d[\d,]*) 以下$")
FRAC_RE = re.compile(r"^(\d[\d,]*) / (\d[\d,]*)(?: × (\d+))?$")


def seal_predictions(seal):
    u"""封 §3 の表の行 {名前: (欄, 予測, 外れ方)}(封の字のまま)。"""
    out = collections.OrderedDict()
    for l in seal.splitlines():
        m = re.match(r"^\| \*\*(CA-\d+)\*\* \| (.*) \|$", l)
        if m:
            cells = m.group(2).split(u" | ")
            assert len(cells) == 3, l
            out[m.group(1)] = tuple(c.strip() for c in cells)
    return out


def seal_criteria(seal):
    u"""封 §4 の K-1〜K-4 の行 {名前: (見出し, 字)}。"""
    out = collections.OrderedDict()
    for l in seal.splitlines():
        m = re.match(r"^- \*\*(K-\d)\((.*?)\)\*\*: (.*)$", l)
        if m:
            out[m.group(1)] = (m.group(2), m.group(3))
    return out


def num(s):
    return int(s.replace(u",", u""))


def bolds(cell):
    return BOLD.findall(cell)


def frac(b):
    m = FRAC_RE.match(b)
    return (num(m.group(1)), num(m.group(2)), int(m.group(3) or 1))


def window(b):
    m = RANGE_RE.match(b)
    return num(m.group(1)), num(m.group(2))


def hit_word(b):
    return u"**判定しない**" if b is None else (u"**当たり**" if b else u"**外れ**")


def counts_of(rec):
    u"""行の一覧から数え直した数(書類ごとの数に頼らない)。"""
    v67, v30 = doc_split(rec)
    s30, s67 = set(v30), set(v67)
    cand = rec[u"候補の行(P27C。reason が no_same_value か候補が辞書の行)"]
    def blk(ss):
        rows = [x for x in cand if x["doc"] in ss]
        dr = [x for x in rows if x["candidate"] is not None]
        nr = [x for x in rows if x["reason"] == NSV]
        return {"dict": len(dr), "nsv": len(nr), "both": sum(1 for x in rows if x["candidate"] is not None and x["reason"] == NSV),
                "nsv_none": sum(1 for x in nr if x["candidate"] is None), "dict_notnsv": sum(1 for x in dr if x["reason"] != NSV)}
    return blk(s30), blk(s67)


def judge(rec, inp, seal):
    u"""{名前: (実測の字, 当たりか)}。当たりか: True / False / None(判定しない)。"""
    P = seal_predictions(seal)
    per = rec[u"書類ごと"]
    docs = rec[u"書類(出てくる順)"]
    v67, v30 = doc_split(rec)
    rs = reg_states(inp["reg"])
    out = collections.OrderedDict()
    # CA-1
    b = bolds(P["CA-1"][1])
    a1, b1, _ = frac(b[0])
    zero = num(b[1])
    rows_want = num(re.search(r"= ([\d,]+) 行", P["CA-1"][1]).group(1))
    sh = dict((p, sum(1 for d in docs if per[d][u"profiles"][p][u"sha256(§3 の字: candidate・engine を除く)"] == per[d][u"比べる側"][p][u"sha256"])) for p in ("P22", "P27"))
    dict_off = sum(per[d][u"profiles"][p][u"候補が辞書の行"] for d in docs for p in per[d][u"profiles"] if p in ("P22", "P27", "P27E"))
    rows_off = sum(per[d][u"profiles"]["P27"][u"claims"] for d in docs)
    hit = sh["P22"] == a1 and sh["P27"] == a1 and len(docs) == b1 and dict_off == zero and rows_off == rows_want
    out["CA-1"] = (u"欄を落とした出力の sha256 が比べる側と一致: P22 %s・P27 %s。旗が偽の profile(P22・P27・30 書類は P27E も)の辞書の行 %d。P27 の claims %d" %
                   (n_of(sh["P22"], len(docs)), n_of(sh["P27"], len(docs)), dict_off, rows_off), hit)
    # CA-2
    b = bolds(P["CA-2"][1])
    s_a, s_b, _ = frac(b[0])
    r_a, r_b, _ = frac(b[1])
    h_a, h_b, _ = frac(b[2])
    st = sum(1 for d in docs if per[d][u"profiles"]["P27C"][u"4 state"] == full4(rs[d]["P27"]))
    claims = sum(per[d][u"claims"] for d in docs)
    r1 = sum(per[d][u"行ごとの一致(5 欄)"][u"P27C と P27(旗が偽。いまの engine)"] for d in docs)
    r2 = sum(per[d][u"行ごとの一致(5 欄)"][u"P27C と 比べる側の P27"] for d in docs)
    sa = sum(1 for d in docs if per[d][u"profiles"]["P27C"][u"sha256(§3 の字: candidate・engine を除く)"] == per[d][u"比べる側"]["P27"][u"sha256"])
    sb = sum(1 for d in docs if per[d][u"profiles"]["P27C"][u"sha256(profile も除く)"] == per[d][u"比べる側"]["P27"][u"sha256(profile も除く)"])
    hit = (st, len(docs)) == (s_a, s_b) and r1 == r2 == r_a == r_b == claims and (sa, len(docs)) == (h_a, h_b)
    out["CA-2"] = (u"4 state が regress97 の P27 と %s。行ごと(5 欄)が旗が偽の P27 と %s・比べる側の P27 と %s。欄を落とした出力の sha256(§3 の字)が比べる側の P27 と %s"
                   u"(`profile` も除くと %s。封 §6-4 の補い。判定は §3 の字)" % (n_of(st, len(docs)), n_of(r1, claims), n_of(r2, claims), n_of(sa, len(docs)), n_of(sb, len(docs))), hit)
    # CA-3
    b = bolds(P["CA-3"][1])
    c30, c67 = counts_of(rec)
    w = [num(x) for x in b]
    hit = c30["dict"] == w[0] and c30["nsv"] == w[1] and c30["both"] == c30["dict"] == c30["nsv"] and c30["nsv_none"] == w[2] and c30["dict_notnsv"] == w[3]
    out["CA-3"] = (u"新しい標本 30: 辞書の行 %d・no_same_value の行 %d・両方 %d。no_same_value で候補が None の行 %d・no_same_value でなく辞書の行 %d" %
                   (c30["dict"], c30["nsv"], c30["both"], c30["nsv_none"], c30["dict_notnsv"]), hit)
    # CA-4
    b = bolds(P["CA-4"][1])
    lo, hi = window(b[0])
    mism = num(b[1])
    hit = lo <= c67["dict"] <= hi and c67["dict"] == c67["nsv"] == c67["both"] and c67["nsv_none"] + c67["dict_notnsv"] == mism
    out["CA-4"] = (u"手元の 67: 辞書の行 %d・no_same_value の行 %d・両方 %d。食い違う行 %d" % (c67["dict"], c67["nsv"], c67["both"], c67["nsv_none"] + c67["dict_notnsv"]), hit)
    # CA-5
    b = bolds(P["CA-5"][1])
    named = dict(((x["doc"], x["id"]), x) for x in inp["unn"][u"plain_rows"])
    dr = [x for x in rec[u"候補の行(P27C。reason が no_same_value か候補が辞書の行)"] if x["doc"] in set(v30) and x["candidate"] is not None]
    ptr = sum(1 for x in dr if (x["doc"], x["id"]) in named and named[(x["doc"], x["id"])][u"named"] == x["candidate"]["pointer"])
    val = sum(1 for x in dr if (x["doc"], x["id"]) in named and named[(x["doc"], x["id"])][u"named の value"] == x["candidate"]["value"])
    basis = sum(1 for x in dr if x["candidate"]["basis"] == NSV)
    f1, f2 = frac(b[0]), frac(b[1])
    hit = (ptr, len(dr)) == f1[:2] and (val, len(dr)) == f2[:2] and basis == len(dr)
    out["CA-5"] = (u"pointer が診断の named と %s・value が named の value と %s・basis が no_same_value %s" % (n_of(ptr, len(dr)), n_of(val, len(dr)), n_of(basis, len(dr))), hit)
    # CA-6
    b = bolds(P["CA-6"][1])
    r741 = rec[u"注入 741 行"]
    urow = dict((x["id"], x) for x in inp["unn"][u"rows"])
    srow = dict((x["id"], x) for x in inp["stop"][u"rows"])
    same = 0
    for r in r741:
        o = srow[r["id"]]
        oc = o[u"profile"]["P27"]["claim"] if r[u"型"] == "T3_ABSENT" else o[u"profile"]["P27"][u"注入後"]["claim"]
        same += int(oc is not None and (r["state"], r["reason"], r["pointers"]) == (oc["state"], oc["reason"], oc["pointers"]) or (oc is None and r["state"] is None))
    dr = [r for r in r741 if r["candidate"] is not None]
    mains = [r for r in dr if r[u"型"] != "T3_ABSENT"]
    t3 = [r for r in dr if r[u"型"] == "T3_ABSENT"]
    ptr6 = sum(1 for r in dr if urow[r["id"]][u"named"] == r["candidate"]["pointer"])
    p_main = sum(1 for r in mains if urow[r["id"]][u"基準の先頭"] == r["candidate"]["pointer"])
    p_t3 = sum(1 for r in t3 if urow[r["id"]][u"P22 の注入後の先頭"] == r["candidate"]["pointer"])
    types = dict(collections.Counter(r[u"型"] for r in dr))
    want_types = dict(collections.Counter(x[u"型"] for x in inp["unn"][u"rows"] if x["reason"] == NSV))
    f_same, f_ptr, f_main, f_t3 = frac(b[0]), num(b[1]), frac(b[2]), frac(b[3])
    f_t3b = frac(b[4])
    none_want = num(b[5])
    hit = ((same, len(r741)) == f_same[:2] and len(dr) == f_ptr and (ptr6, len(dr)) == f_main[:2] and (p_main, len(mains)) == f_t3[:2] and (p_t3, len(t3)) == f_t3b[:2]
           and len(r741) - len(dr) == none_want and types == want_types)
    out["CA-6"] = (u"state・reason・pointers が stop_reason の P27 と %s。候補が辞書の行 %d(%s)で、pointer が診断の named と %s・原本の基準の先頭と %s(T1・T2・T5)・P22 の注入後の先頭と %s(T3)。候補が None の行 %d" %
                   (n_of(same, len(r741)), len(dr), u"・".join(u"%s %d" % (TSHORT[t], types.get(t, 0)) for t in ("T1_VALUE", "T2_UNIT", "T5_COINCIDENT", "T3_ABSENT")),
                    n_of(ptr6, len(dr)), n_of(p_main, len(mains)), n_of(p_t3, len(t3)), len(r741) - len(dr)), hit)
    # CA-7
    e = rec[u"P27EC の行(30 書類。P27・P27EC のどちらかで reason が no_same_value か候補が辞書の行)"]
    m = re.search(r"= (\d+)", bolds(P["CA-7"][1])[0])
    want7 = int(m.group(1))
    prod_want = num(bolds(P["CA-7"][1])[1])
    dict7 = sum(1 for x in e if x["candidate"] is not None)
    nsv7 = sum(1 for x in e if x["reason"] == NSV)
    moved = [x for x in e if x[u"P27 の reason"] == NSV and x["reason"] != NSV]
    prod7 = sum(1 for x in moved if x["candidate"] is not None)
    hit = dict7 == nsv7 == want7 and prod7 == prod_want and sum(1 for x in e if (x["candidate"] is not None) != (x["reason"] == NSV)) == 0
    out["CA-7"] = (u"P27EC(30 書類): 候補が辞書の行 %d・no_same_value の行 %d(P27 の no_same_value は %d)。B が動かした行 %d(うち VALUE_MISMATCH %d)。候補が付く行と B が動かした行の積 %d" %
                   (dict7, nsv7, sum(1 for x in e if x[u"P27 の reason"] == NSV), len(moved), sum(1 for x in moved if x["state"] == "VALUE_MISMATCH"), prod7), hit)
    # CA-8
    f8 = frac(bolds(P["CA-8"][1])[0])
    m8 = dict((k, sum(1 for d in docs if per[d][u"客向けの報告"][k][u"旗が偽の本文が比べる側と byte 一致"])) for k in (u"既定", u"--full"))
    hit = all((m8[k], len(docs)) == f8[:2] for k in m8) and f8[2] == 2
    out["CA-8"] = (u"旗が偽の本文が比べる側と byte 一致: 既定 %s・--full %s" % (n_of(m8[u"既定"], len(docs)), n_of(m8[u"--full"], len(docs))), hit)
    # CA-9(段 1 の試験の結果を写した事実 + golden の定数が HEAD と同じ字か)
    g_same = golden_unchanged()
    sf = STAGE1_FACTS.get("CA-9", (None, u"(未記入)"))
    out["CA-9"] = (sf[1] + u"。golden の 3 定数の字が比べる側の commit と同じ: " + yesno(g_same), None if sf[0] is None else bool(sf[0] and g_same))
    # CA-10
    want10 = num(bolds(P["CA-10"][1])[0])
    fresh = v30
    got10 = {}
    for mode in (u"既定", u"--full"):
        R = [per[d][u"客向けの報告"][mode] for d in fresh]
        got10[mode] = {"diff": sum(x[u"違う行"] for x in R), "once": sum(x[u"違う行のうち「。候補: 」を 1 回だけ持つ行"] for x in R),
                       "strip": sum(x[u"違う行のうち、候補の節を除くと比べる側の行と同じ行"] for x in R), "table": sum(x[u"違う行のうち、表の行(「| 」で始まる)"] for x in R),
                       "rev": sum(n for x in R for h, n in x[u"違う行の見出し"].items() if u"要確認" in h), "same_lines": all(x[u"行数が同じ"] for x in R)}
    per_doc_eq = sum(1 for d in fresh if per[d][u"客向けの報告"][u"既定"][u"違う行"] == per[d][u"客向けの報告"][u"--full"][u"違う行"] == per[d][u"profiles"]["P27C"][u"候補が辞書の行"])
    hit = all(g_["diff"] == want10 == g_["once"] == g_["strip"] == g_["table"] == g_["rev"] and g_["same_lines"] for g_ in got10.values()) and per_doc_eq == len(fresh)
    out["CA-10"] = (u"違う行: 既定 %d・--full %d(「。候補: 」を 1 回だけ持つ行 %d・%d、候補の節を除くと比べる側の行と同じ行 %d・%d、「要確認」の見出しの下の表の行 %d・%d)。書類ごとに 候補が辞書の行と同じ数: %s" %
                    (got10[u"既定"]["diff"], got10[u"--full"]["diff"], got10[u"既定"]["once"], got10[u"--full"]["once"], got10[u"既定"]["strip"], got10[u"--full"]["strip"],
                     min(got10[u"既定"]["table"], got10[u"既定"]["rev"]), min(got10[u"--full"]["table"], got10[u"--full"]["rev"]), n_of(per_doc_eq, len(fresh))), hit)
    # CA-11
    sf = STAGE1_FACTS.get("CA-11", (None, u"(未記入)"))
    out["CA-11"] = (sf[1], sf[0])
    return out


def judge_k(rec, inp, seal):
    u"""K-1〜K-4(封 §4)を記録から機械で求める。{名前: (実測の字, 満たすか)}。"""
    J = judge(rec, inp, seal)
    per = rec[u"書類ごと"]
    docs = rec[u"書類(出てくる順)"]
    rs = reg_states(inp["reg"])
    c30, c67 = counts_of(rec)
    claims = sum(per[d][u"claims"] for d in docs)
    r1 = sum(per[d][u"行ごとの一致(5 欄)"][u"P27C と P27(旗が偽。いまの engine)"] for d in docs)
    r2 = sum(per[d][u"行ごとの一致(5 欄)"][u"P27C と 比べる側の P27"] for d in docs)
    st = sum(1 for d in docs if per[d][u"profiles"]["P27C"][u"4 state"] == full4(rs[d]["P27"]))
    k = collections.OrderedDict()
    k["K-1"] = (u"行ごとの一致 %s(旗が偽の P27 と)・%s(比べる側の P27 と)。4 state が regress97 の P27 と %s" % (n_of(r1, claims), n_of(r2, claims), n_of(st, len(docs))),
                r1 == claims and r2 == claims and st == len(docs))
    r741 = rec[u"注入 741 行"]
    srow = dict((x["id"], x) for x in inp["stop"][u"rows"])
    same = 0
    for r in r741:
        o = srow[r["id"]]
        oc = o[u"profile"]["P27"]["claim"] if r[u"型"] == "T3_ABSENT" else o[u"profile"]["P27"][u"注入後"]["claim"]
        same += int((oc is None and r["state"] is None) or (oc is not None and (r["state"], r["reason"], r["pointers"]) == (oc["state"], oc["reason"], oc["pointers"])))
    k["K-2"] = (u"741 行の state・reason・pointers が stop_reason の P27 と %s" % n_of(same, len(r741)), same == len(r741))
    sh = [sum(1 for d in docs if per[d][u"profiles"][p][u"sha256(§3 の字: candidate・engine を除く)"] == per[d][u"比べる側"][p][u"sha256"]) for p in ("P22", "P27")]
    rep = [sum(1 for d in docs if per[d][u"客向けの報告"][m][u"旗が偽の本文が比べる側と byte 一致"]) for m in (u"既定", u"--full")]
    dict_off = sum(per[d][u"profiles"][p][u"候補が辞書の行"] for d in docs for p in per[d][u"profiles"] if p in ("P22", "P27", "P27E"))
    k["K-3"] = (u"欄を落とした出力の sha256 が比べる側と一致: P22 %s・P27 %s。旗が偽の辞書の行 %d。報告の本文が byte 一致: 既定 %s・--full %s" %
                (n_of(sh[0], len(docs)), n_of(sh[1], len(docs)), dict_off, n_of(rep[0], len(docs)), n_of(rep[1], len(docs))),
                sh[0] == len(docs) and sh[1] == len(docs) and dict_off == 0 and rep[0] == len(docs) and rep[1] == len(docs))
    k["K-4"] = (u"食い違う行: 新しい標本 30 で %d(no_same_value で候補が None %d・no_same_value でなく辞書 %d)、手元の 67 で %d(%d・%d)" %
                (c30["nsv_none"] + c30["dict_notnsv"], c30["nsv_none"], c30["dict_notnsv"], c67["nsv_none"] + c67["dict_notnsv"], c67["nsv_none"], c67["dict_notnsv"]),
                c30["nsv_none"] + c30["dict_notnsv"] == 0 and c67["nsv_none"] + c67["dict_notnsv"] == 0)
    return k


def adopted(rec, inp, seal):
    return all(v[1] for v in judge_k(rec, inp, seal).values())


def golden_unchanged():
    u"""CA-9 の necessary 側: golden の 3 定数(``SMALL_GOLDEN``・``UNITS_GOLDEN``・``GOLDEN_SHA256``)の字が比べる側の commit と同じ。"""
    r = subprocess.run(["git", "show", BASE_COMMIT + ":" + PREFIX + GOLDEN_FILE], cwd=REPO, capture_output=True, text=True)
    if r.returncode != 0:
        return False
    return consts_text(r.stdout) == consts_text(jtext(os.path.join(ROOT, GOLDEN_FILE)))


def consts_text(src):
    import ast
    tree = ast.parse(src)
    out = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id in GOLDEN_NAMES:
            out[n.targets[0].id] = ast.dump(n.value)
    return out if sorted(out) == sorted(GOLDEN_NAMES) else None


# ----------------------------------------------------------------------------------------------------------------
# (c) 文書の表
def render_blocks(rec, inp, seal):
    u"""文書の門の表 {名前: 行の列}。"""
    B = collections.OrderedDict()
    P = seal_predictions(seal)
    J = judge(rec, inp, seal)
    rows = []
    for k, (field, pred, miss) in P.items():
        text, hit = J[k]
        rows.append([u"**%s**" % k, field, pred, miss, text, hit_word(hit)])
    B["pred"] = table([u"#", u"欄", u"予測(封の字)", u"外れ方(封の字)", u"実測(記録から)", u"当たり外れ"], rows)
    C = seal_criteria(seal)
    K = judge_k(rec, inp, seal)
    rows = [[u"**%s**" % k, C[k][0], C[k][1], K[k][0], yesno(K[k][1])] for k in K]
    rows.append([u"**採用**", u"K-1〜K-4 の全部", u"全部を満たすとき(封 §4)", u"", yesno(all(v[1] for v in K.values()))])
    B["adopt"] = table([u"#", u"基準(封 §4 の見出し)", u"基準(封 §4 の字)", u"実測(記録から)", u"満たすか"], rows)
    g = rec[u"配線の門"]
    a, b = g[u"97 書類"], g[u"741 行"]
    rows = [[u"ZIP の sha256 が p26・fetched・regress97 と一致(97 書類)", yesno(a[u"ZIP の sha256 が p26・fetched・regress97 と一致"])]]
    for k in (u"比べる側の P22・P27 の 4 state が regress97 と一致した書類", u"いまの engine の P22・P27(旗が偽)の 4 state が regress97 と一致した書類",
              u"いまの engine の P27E(旗が偽。30 書類)の 4 state が regress97 と一致した書類", u"標準ラベルを名簿どおりに読んだ file"):
        rows.append([k, n_of(*a[k])])
    for k in (u"前の便の門(4 欄とも一致)", u"注入の件数の組", u"P27(旗が偽)の claim が stop_reason と一致した行", u"P27C の claim が stop_reason の P27 と一致した行(10 欄)",
              u"P27C の state・reason・pointers が stop_reason の P27 と一致した行"):
        rows.append([u"741 行: " + k, n_of(*b[k])])
    rows.append([u"741 行: id の集合が記録と同じ", yesno(b[u"id の集合が記録と同じ"])])
    rows.append([u"全書類の記録", yesno(rec[u"全書類"])])
    rows.append([u"配線の門が通った", yesno(g[u"通った"])])
    B["wiring"] = table([u"配線の門", u"値"], rows)
    rows = []
    for rel in ENGINE_AT_MEASURE:
        rows.append([u"`%s` の sha16(いまの engine)" % rel, u"`%s`" % rec[u"engine sha16"][rel]])
        rows.append([u"`%s` の sha16(比べる側 %s)" % (rel, BASE_COMMIT), u"`%s`" % rec[u"比べる側"][u"engine sha16"][rel]])
    rows.append([u"DEFAULT_PROFILE", rec[u"DEFAULT_PROFILE"]])
    B["engine"] = table([u"項目", u"値"], rows)
    c30, c67 = counts_of(rec)
    per = rec[u"書類ごと"]
    docs = rec[u"書類(出てくる順)"]
    v67, v30 = doc_split(rec)
    rows = []
    for name, c in ((u"新しい標本 30", c30), (u"手元の 67", c67)):
        rows.append([name + u" の候補が辞書の行", c["dict"]])
        rows.append([name + u" の reason が no_same_value の行", c["nsv"]])
        rows.append([name + u" の no_same_value で候補が None の行", c["nsv_none"]])
        rows.append([name + u" の no_same_value でなく候補が辞書の行", c["dict_notnsv"]])
    rows.append([u"97 書類の P27 の claims(7,799 + 3,923)", sum(per[d][u"claims"] for d in docs)])
    for p in ("P22", "P27", "P27C"):
        rows.append([u"4 state の和 %s(GROUNDED・VALUE_MISMATCH・UNVERIFIABLE・POINTER_NOT_FOUND)" % p,
                     u"・".join(str(sum(per[d][u"profiles"][p][u"4 state"][s] for d in docs)) for s in STATES4)])
    rows.append([u"P27C の出力の profile の字が P27C の書類", n_of(sum(1 for d in docs if per[d][u"profiles"]["P27C"][u"出力の profile の字"] == "P27C"), len(docs))])
    rows.append([u"P27C の欄の並びが 13 欄で末尾が candidate の書類", n_of(sum(1 for d in docs if len(per[d][u"profiles"]["P27C"][u"欄の並び"]) == 13 and per[d][u"profiles"]["P27C"][u"欄の並び"][-1] == "candidate"), len(docs))])
    r741 = rec[u"注入 741 行"]
    rows.append([u"注入 741 行で候補が辞書の行(型別 T1・T2・T5・T3)", u"%d(%s)" % (sum(1 for r in r741 if r["candidate"] is not None),
                                                                  u"・".join(str(sum(1 for r in r741 if r["candidate"] is not None and r[u"型"] == t)) for t in ("T1_VALUE", "T2_UNIT", "T5_COINCIDENT", "T3_ABSENT")))])
    rows.append([u"注入 741 行で候補が None の行", sum(1 for r in r741 if r["candidate"] is None)])
    B["counts"] = table([u"項目", u"値"], rows)
    rows = []
    for mode in (u"既定", u"--full"):
        R = [per[d][u"客向けの報告"][mode] for d in v30]
        rows.append([u"旗が偽の本文が比べる側と byte 一致(97 書類)・%s" % mode, n_of(sum(1 for d in docs if per[d][u"客向けの報告"][mode][u"旗が偽の本文が比べる側と byte 一致"]), len(docs))])
        rows.append([u"旗が真(案 A)で本文の違う行(新しい標本 30 の和)・%s" % mode, sum(x[u"違う行"] for x in R)])
        rows.append([u"うち「。候補: 」を 1 回だけ持つ行・%s" % mode, sum(x[u"違う行のうち「。候補: 」を 1 回だけ持つ行"] for x in R)])
        rows.append([u"うち候補の節を除くと比べる側の行と同じ行・%s" % mode, sum(x[u"違う行のうち、候補の節を除くと比べる側の行と同じ行"] for x in R)])
        rows.append([u"うち「要確認」の見出しの下の行・%s" % mode, sum(n for x in R for h, n in x[u"違う行の見出し"].items() if u"要確認" in h)])
        rows.append([u"行数が同じ書類・%s" % mode, n_of(sum(1 for x in R if x[u"行数が同じ"]), len(v30))])
    rows.append([u"手元の 67(参考。判定に使わない)で本文の違う行・既定", sum(per[d][u"客向けの報告"][u"既定"][u"違う行"] for d in v67)])
    rows.append([u"標準ラベルを渡したか", u"標準ラベル 3 file(名簿の sha256 で照合。書類自身のラベルは渡していない)"])
    B["report"] = table([u"項目", u"値"], rows)
    return B


BLOCK_RE = re.compile(r"<!-- 門:start (\S+) -->\n(.*?)\n<!-- 門:end -->", re.S)


def doc_blocks(doc):
    out = collections.OrderedDict()
    for m in BLOCK_RE.finditer(doc):
        if m.group(1) in out:
            raise AssertionError(u"同じ名前の門の表が 2 つ: " + m.group(1))
        out[m.group(1)] = m.group(2).split(u"\n")
    return out


def check_c(rec, inp, seal, doc):
    u"""文書の表を記録から作り直して比べる。問題の列。"""
    out = []
    try:
        B = render_blocks(rec, inp, seal)
    except Exception as e:      # 記録が壊れていれば作り直せない(それも赤)
        return [u"記録から表を作れない: %r" % (e,)]
    got = doc_blocks(doc)
    if list(got) != list(B):
        out.append(u"文書の門の表の名前と順が違う: %s" % list(got))
        return out
    for k, lines in B.items():
        if got[k] != lines:
            out.append(u"文書の表『%s』が記録から作った表と違う" % k)
    return out


DOC_LITERALS = (u"候補の正しさは測っていない", u"測っていない", NOT_GATED, u"edinetdb-p27", u"engine は 0 行", u"段 1", u"この便で決めない", u"2026-10-30")


def check_doc_prose(rec, inp, seal, doc):
    out = []
    stripped = BLOCK_RE.sub(u"", doc)
    if [l for l in stripped.split(u"\n") if l.lstrip().startswith(u"|")]:
        out.append(u"門の外に表の行がある")
    bad = [l[:40] for l in stripped.split(u"\n") if re.search(r"\d+(?:\.\d+)?\s*(?:%|行|件|社|席|書類|試行|回|本|ポイント|USD|file|倍|桁|字|組|つ)", l) and NOT_GATED not in l]
    if bad:
        out.append(u"散文の数に【門なし】の印が無い: %s" % bad)
    heads = re.findall(r"^## (\d+)\.", doc, re.M)
    if heads != [str(i) for i in range(1, len(heads) + 1)] or len(heads) < 7:
        out.append(u"節の番号が 1 から続いていない・7 節に足りない: %s" % heads)
    if not (doc.index(u"<!-- 門:start pred -->") < doc.index(u"## 2.")):
        out.append(u"予測の当否が先頭(第 2 節より前)にない")
    J = judge(rec, inp, seal)
    missed = [k for k, v in J.items() if v[1] is False]
    want = u"外れた予測: " + (u"・".join(missed) if missed else u"なし") + u"。外れは外れのまま残す(封も予測も直さない)。" + NOT_GATED
    if sum(1 for l in doc.split(u"\n") if l.strip() == want) != 1:
        out.append(u"『外れた予測』の行が記録から求めた当否と違う(期待: %s)" % want)
    undecided = [k for k, v in J.items() if v[1] is None]
    if undecided:
        out.append(u"判定しない予測がある(CA-9・CA-11 は字で留めた事実で判定する): %s" % undecided)
    ad = adopted(rec, inp, seal)
    want2 = (u"採用する。K-1〜K-4 が全部満たされた(候補の欄を engine に残す。旗が偽なら何も変わらない。実装の commit は独立監査の GO の後)。" if ad
             else u"採用しない。K-1〜K-4 のどれかが満たされなかった(欄と旗は engine に残さず、実装の commit をしない。直すなら新しい封)。") + NOT_GATED
    if sum(1 for l in doc.split(u"\n") if l.strip() == want2) != 1:
        out.append(u"『採用』の行が記録から求めた判定と違う(期待: %s)" % want2)
    for lit in DOC_LITERALS:
        if lit not in doc:
            out.append(u"必要な字が無い: %s" % lit)
    for w in FORBIDDEN:
        if w in doc:
            out.append(u"禁止語: %s" % w)
    if u"```" in doc:
        out.append(u"code fence がある")
    return out


# ----------------------------------------------------------------------------------------------------------------
# (h)(i)
FILER_PTR = re.compile(r"xbrl:([^:@\s]+):")


def filer_prefixes(rec):
    u"""記録のどこかの pointer(候補・741 行)に出る、標準でない接頭辞の字の集合(文書に書いてはいけない字)。"""
    out = set()

    def add(ptr):
        m = FILER_PTR.match(ptr) if isinstance(ptr, str) else None
        if m and not re.fullmatch(r"jp[a-z]+_cor", m.group(1)):
            out.add(m.group(1))
    for r in rec[u"候補の行(P27C。reason が no_same_value か候補が辞書の行)"]:
        add((r["candidate"] or {}).get("pointer"))
    for r in rec[u"P27EC の行(30 書類。P27・P27EC のどちらかで reason が no_same_value か候補が辞書の行)"]:
        add((r["candidate"] or {}).get("pointer"))
    for r in rec[u"注入 741 行"]:
        add((r["candidate"] or {}).get("pointer"))
        for ptr in r["pointers"] or []:
            add(ptr)
    return out


def check_h(doc, fetched, rec=None):
    out = []
    docs = list(fetched[u"使う書類"])
    if rec is not None:
        docs += list(rec[u"書類(出てくる順)"])
    cids, fprefs = set(), set()
    if rec is not None:
        fprefs = filer_prefixes(rec)
        for r in rec[u"候補の行(P27C。reason が no_same_value か候補が辞書の行)"]:
            cids.add(r["id"])
        for r in rec[u"注入 741 行"]:
            cids.add(r["id"])
    if True:
        t = doc
        for d in docs:
            if d in t:
                out.append(u"文書に docID の字がある: %s" % d)
        if re.findall(r"S100[0-9A-Z]{4}", t):
            out.append(u"文書に docID らしい字がある")
        if re.findall(r"\b[NT]\d{3}\b", t):
            out.append(u"文書に claim の id らしい字がある")
        for cid in cids:
            if re.search(r"(?<![0-9A-Za-z])%s(?![0-9A-Za-z])" % re.escape(cid), t):
                out.append(u"文書に記録の claim の id の字がある: %s" % cid)
                break
        for fp in sorted(fprefs):
            if fp in t:
                out.append(u"文書に提出者別の接頭辞の字がある")
                break
        if u"```" in t:
            out.append(u"文書に code fence がある")
        for w in FORBIDDEN:
            if w in t:
                out.append(u"文書に禁止語: %s" % w)
    return out


def make_run(repo_dir):
    def run(*args):
        r = subprocess.run(["git", "-C", repo_dir] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return r.returncode, r.stdout.decode("utf-8", "replace").strip()
    return run


def added_commits(run, path):
    rc, out = run("log", "--diff-filter=A", "--format=%H", "--", path)
    return [l for l in out.splitlines() if l.strip()] if rc == 0 else []


def is_anc(run, a, b):
    return a is not None and b is not None and run("merge-base", "--is-ancestor", a, b)[0] == 0


def impl_commit(run, prefix):
    u"""実装の commit: ``verify_document.py`` の履歴で、``"candidate"`` の字が入った一番古い commit(無ければ None)。"""
    rc, out = run("log", "--format=%H", "-S" + '"candidate"', "--", prefix + IMPL_REL)
    lst = [l for l in out.splitlines() if l.strip()] if rc == 0 else []
    return lst[-1] if lst else None


def order_problems(run, prefix, head="HEAD"):
    u"""(i) 封の commit < 実装の commit <= script・記録・文書・門の commit。問題の列 [(符号, 文)]。追跡されていない file は『足した commit が無い』で赤(skip にしない)。"""
    problems = []
    seal = prefix + SEAL_REL
    s_list = added_commits(run, seal)
    if len(s_list) != 1 or not HEX40.match(s_list[0]):
        problems.append(("SEAL_ONCE", u"封を足した commit がちょうど 1 つに決まらない(%d 行)" % len(s_list)))
        return problems
    S = s_list[0]
    if not is_anc(run, S, head):
        problems.append(("SEAL<=HEAD", u"封の commit が HEAD の祖先でない"))
    impl = impl_commit(run, prefix)
    if impl is None:
        problems.append(("IMPL_UNCOMMITTED", u"実装(候補の欄)がまだ commit されていない"))
    elif not (impl != S and is_anc(run, S, impl)):
        problems.append(("IMPL_BEFORE_SEAL", u"実装の commit が封の commit より前か同じ"))
    for name, rel in (("SCRIPT", SCRIPT_REL), ("RECORD", REC_REL), ("DOC", DOC_REL), ("GATE", GATE_REL)):
        lst = added_commits(run, prefix + rel)
        if len(lst) == 0:
            problems.append((name + "_UNCOMMITTED", u"%s がまだ commit されていない(足した commit が無い)" % rel))
        elif len(lst) != 1 or not HEX40.match(lst[0]):
            problems.append((name + "_ONCE", u"%s を足した commit がちょうど 1 つに決まらない(%d 行)" % (rel, len(lst))))
        else:
            if not (lst[0] != S and is_anc(run, S, lst[0])):
                problems.append((name + "_BEFORE_SEAL", u"%s の commit が封の commit より前か同じ" % rel))
            if impl is not None and not is_anc(run, impl, lst[0]):
                problems.append((name + "_BEFORE_IMPL", u"%s の commit が実装の commit より前" % rel))
    # 封を後から直していない(削除の行が 0 = 日付つきの追記だけ)
    rc, txt = run("log", "--format=%H", "%s..%s" % (S, head), "--", seal)
    for h in [l for l in txt.splitlines() if l.strip()]:
        rc2, parent = run("rev-parse", h + "^")
        base = parent if rc2 == 0 else EMPTY_TREE
        rc3, numstat = run("diff", "--numstat", base, h, "--", seal)
        for line in numstat.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2 and parts[1] != "0":
                problems.append(("SEAL_REWRITE", u"封の commit より後の commit %s が封の行を消している" % h[:7]))
    return problems


def codes(problems):
    return sorted(set(c for c, _m in problems))


class Tmp(object):
    def __init__(self, base):
        self.dir = tempfile.mkdtemp(prefix="unnamedcand_", dir=base)
        self.run = make_run(self.dir)
        self._g("init", "-q")

    def _g(self, *args):
        r = subprocess.run(["git", "-C", self.dir, "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false"] + list(args),
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert r.returncode == 0, (args, r.stderr[:300])
        return r.stdout.decode("utf-8").strip()

    def write(self, rel, text):
        p = os.path.join(self.dir, rel)
        if os.path.dirname(p) and not os.path.isdir(os.path.dirname(p)):
            os.makedirs(os.path.dirname(p))
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)

    def commit(self, msg, *paths):
        self._g("add", "--", *paths)
        self._g("commit", "-q", "-m", msg)
        return self._g("rev-parse", "HEAD")


FILES = {"SEAL": SEAL_REL, "IMPL": IMPL_REL, "SCRIPT": SCRIPT_REL, "RECORD": REC_REL, "DOC": DOC_REL, "GATE": GATE_REL}


def build(base, steps):
    u"""steps は 'SEAL' 'IMPL' 'SCRIPT' 'RECORD' 'DOC' 'GATE'(その file を 1 つの commit で足す。IMPL は \"candidate\" の字を持つ版)と変異の手
    'SEAL_REWRITE' 'SEAL_APPEND' 'SEAL_TWICE' 'ALL4'(script・記録・文書・門を 1 commit)'IMPL_PLAIN'(\"candidate\" の字の無い版を足す)。"""
    t = Tmp(base)
    for s in steps:
        if s == "IMPL":
            t.write(FILES[s], u"# IMPL\nCLAIM_FIELDS = (\"a\", \"candidate\")\n")
            t.commit(s, FILES[s])
        elif s == "IMPL_PLAIN":
            t.write(FILES["IMPL"], u"# IMPL\nCLAIM_FIELDS = (\"a\",)\n")
            t.commit(s, FILES["IMPL"])
        elif s in FILES:
            t.write(FILES[s], u"# %s\n\n行 1\n行 2\n行 3\n" % s)
            t.commit(s, FILES[s])
        elif s == "ALL4":
            for k in ("SCRIPT", "RECORD", "DOC", "GATE"):
                t.write(FILES[k], u"# %s\n" % k)
            t.commit("ALL4", *[FILES[k] for k in ("SCRIPT", "RECORD", "DOC", "GATE")])
        elif s == "SEAL_REWRITE":
            t.write(FILES["SEAL"], u"# SEAL\n\n行 1\n行 3\n")
            t.commit("封を書き換える", FILES["SEAL"])
        elif s == "SEAL_APPEND":
            with open(os.path.join(t.dir, FILES["SEAL"]), "a", encoding="utf-8") as f:
                f.write(u"\n## 追記\n行 4\n")
            t.commit("封に追記", FILES["SEAL"])
        elif s == "SEAL_TWICE":
            t._g("rm", "-q", "--", FILES["SEAL"])
            t._g("commit", "-q", "-m", "封を消す")
            t.write(FILES["SEAL"], u"# SEAL\n")
            t.commit("封を足し直す", FILES["SEAL"])
        else:
            raise AssertionError(s)
    return t


# ----------------------------------------------------------------------------------------------------------------
class RecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.inp = inputs()
        cls.seal = jtext(SEAL)

    def test_a_1_the_documents_and_the_injected_ids_are_the_recorded_ones(self):
        self.assertEqual(check_a(self.rec, self.inp), [])

    def test_a_2_the_sets_are_read_from_the_records_not_hardcoded(self):
        rec = copy.deepcopy(self.rec)
        rec[u"注入 741 行"].pop()
        self.assertNotEqual(check_a(rec, self.inp), [])
        rec = copy.deepcopy(self.rec)
        rec[u"書類(出てくる順)"] = rec[u"書類(出てくる順)"][:-1]
        self.assertNotEqual(check_a(rec, self.inp), [])

    def test_b_1_the_wiring_gates_pass_and_the_gate_recounts_them(self):
        self.assertEqual(check_b(self.rec, self.inp), [])

    def test_b_2_the_record_is_the_full_run_and_the_cache_is_untouched(self):
        self.assertTrue(self.rec[u"全書類"])
        self.assertEqual(self.rec[u"key_leaks"], [])
        self.assertEqual(self.rec[u"cache"][u"開始"][u"edinet"][u"件数"], 281)
        self.assertEqual(self.rec[u"cache"][u"開始"][u"edinet-fresh-2026-10-21"][u"件数"], 40)
        self.assertEqual(self.rec[u"cache"][u"開始"], self.rec[u"cache"][u"終了"])

    def test_e_1_the_counts_are_recounted_from_the_lists(self):
        self.assertEqual(check_e(self.rec, self.inp), [])

    def test_e_2_every_candidate_has_the_three_keys_in_order_and_no_text(self):
        for x in self.rec[u"候補の行(P27C。reason が no_same_value か候補が辞書の行)"]:
            self.assertEqual(sorted(x.keys()), ["candidate", "doc", "id", "reason", "state"])
            if x["candidate"] is not None:
                self.assertEqual(list(x["candidate"].keys()), ["pointer", "value", "basis"])
                self.assertEqual(x["reason"], NSV)
        blob = jtext(REC)
        for key in (u'"span":', u'"原文":'):
            self.assertNotIn(key, blob)

    def test_e_3_flagged_off_profiles_never_carry_a_candidate(self):
        for d, v in self.rec[u"書類ごと"].items():
            for p in ("P22", "P27", "P27E"):
                if p in v[u"profiles"]:
                    self.assertEqual(v[u"profiles"][p][u"候補が辞書の行"], 0, p)
                    self.assertEqual(v[u"profiles"][p][u"出力の profile の字"], p)
            self.assertEqual(v[u"profiles"]["P27C"][u"出力の profile の字"], "P27C")
        self.assertTrue(all(r[u"P27(旗が偽)の candidate"] is None for r in self.rec[u"注入 741 行"]))

    def test_e_4_candidate_rows_are_no_same_value_rows_in_the_741_too(self):
        r741 = self.rec[u"注入 741 行"]
        self.assertEqual(sum(1 for r in r741 if r["candidate"] is not None), sum(1 for r in r741 if r["reason"] == NSV))

    def test_j_1_the_inputs_read_are_unchanged(self):
        self.assertEqual(check_j(self.rec), [])

    def test_k_1_the_record_adoption_field_is_what_the_gate_derives(self):
        K = judge_k(self.rec, self.inp, self.seal)
        for name, (_text, ok) in K.items():
            self.assertEqual(self.rec[u"採用"][name], ok, name)
        self.assertEqual(self.rec[u"採用"][u"全部"], adopted(self.rec, self.inp, self.seal))

    def test_k_2_the_record_ca_field_is_what_the_gate_derives_for_the_counts(self):
        c30, c67 = counts_of(self.rec)
        self.assertEqual(self.rec[u"CA の数"]["CA-3"][u"候補が辞書の行"], c30["dict"])
        self.assertEqual(self.rec[u"CA の数"]["CA-3"][u"reason が no_same_value の行"], c30["nsv"])
        self.assertEqual(self.rec[u"CA の数"]["CA-4"][u"候補が辞書の行"], c67["dict"])
        self.assertEqual(self.rec[u"CA の数"]["CA-4"][u"reason が no_same_value の行"], c67["nsv"])
        self.assertEqual(self.rec[u"CA の数"]["CA-6"][u"候補が辞書の行"], sum(1 for r in self.rec[u"注入 741 行"] if r["candidate"] is not None))


class JudgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.inp = inputs()
        cls.seal = jtext(SEAL)

    def test_d_1_judgments_cover_the_eleven_predictions(self):
        J = judge(self.rec, self.inp, self.seal)
        self.assertEqual(list(J), ["CA-%d" % i for i in range(1, 12)])
        self.assertEqual(list(seal_predictions(self.seal)), list(J))
        self.assertEqual(list(judge_k(self.rec, self.inp, self.seal)), ["K-1", "K-2", "K-3", "K-4"])

    def test_d_2_the_judge_is_not_a_constant(self):
        J0 = judge(self.rec, self.inp, self.seal)
        rec = copy.deepcopy(self.rec)
        v30 = doc_split(rec)[1]
        x = [x for x in rec[u"候補の行(P27C。reason が no_same_value か候補が辞書の行)"] if x["candidate"] is not None and x["doc"] in v30][0]
        x["candidate"]["pointer"] = x["candidate"]["pointer"] + "X"
        self.assertNotEqual(judge(rec, self.inp, self.seal)["CA-5"][0], J0["CA-5"][0])
        self.assertFalse(judge(rec, self.inp, self.seal)["CA-5"][1])
        rec = copy.deepcopy(self.rec)
        x = [x for x in rec[u"候補の行(P27C。reason が no_same_value か候補が辞書の行)"] if x["candidate"] is not None][0]
        x["candidate"] = None
        J = judge(rec, self.inp, self.seal)
        self.assertFalse(J["CA-3"][1] and J["CA-4"][1])
        self.assertFalse(judge_k(rec, self.inp, self.seal)["K-4"][1])

    def test_d_3_the_widths_are_read_from_the_seal_text(self):
        seal = self.seal.replace(u"**560 以上 590 以下**", u"**%d 以上 %d 以下**" % (counts_of(self.rec)[1]["dict"] + 1, counts_of(self.rec)[1]["dict"] + 5))
        self.assertNotEqual(seal, self.seal)
        self.assertTrue(judge(self.rec, self.inp, self.seal)["CA-4"][1] in (True, False))
        self.assertFalse(judge(self.rec, self.inp, seal)["CA-4"][1])
        seal = self.seal.replace(u"**296 − 24 = 272**", u"**296 − 24 = 273**")
        if seal != self.seal:
            self.assertFalse(judge(self.rec, self.inp, seal)["CA-7"][1])

    def test_d_4_the_misses_are_kept_as_misses(self):
        J = judge(self.rec, self.inp, self.seal)
        self.assertEqual([k for k, v in J.items() if v[1] is False], MISSES)
        self.assertEqual([k for k, v in J.items() if v[1] is None], UNDECIDED)

    def test_d_5_golden_constants_are_those_of_the_base_commit(self):
        self.assertTrue(golden_unchanged())
        self.assertEqual(sorted(consts_text(jtext(os.path.join(ROOT, GOLDEN_FILE)))), sorted(GOLDEN_NAMES))
        self.assertFalse(consts_text("SMALL_GOLDEN = 1\n") is not None)


class EngineTest(unittest.TestCase):
    def test_f_1_engine_sha16_are_pinned_or_declared(self):
        rec = jload(REC)
        self.assertEqual(rec[u"engine sha16"], ENGINE_AT_MEASURE)
        self.assertEqual(rec[u"比べる側"][u"engine sha16"], BASE_ENGINE)
        for rel, want in ENGINE_AT_MEASURE.items():
            got = sha16(rel)
            if got != want and rel in ENGINE_DECLARED:
                later, seal_rel = ENGINE_DECLARED[rel]
                added = git("log", "--diff-filter=A", "--format=%H", "--", seal_rel).stdout.split()
                self.assertTrue(added, u"**%s が動いているのに、遷移を宣言した封 %s が履歴に無い**" % (rel, seal_rel))
                self.assertEqual(got, later, u"**%s が、宣言された遷移の値とも違う**" % rel)
                continue
            self.assertEqual(got, want, u"**%s が動いている**" % rel)

    def test_f_2_the_declared_transition_form_is_red_for_an_unknown_value(self):
        def accepts(got, rel, want, declared):
            if got != want and rel in declared:
                return got == declared[rel][0]
            return got == want
        rel = "adapters/xbrl/vocabulary.py"
        want = ENGINE_AT_MEASURE[rel]
        self.assertTrue(accepts(want, rel, want, {}))
        self.assertFalse(accepts("0" * 16, rel, want, {}))
        self.assertTrue(accepts("1" * 16, rel, want, {rel: ("1" * 16, "x")}))
        self.assertFalse(accepts("2" * 16, rel, want, {rel: ("1" * 16, "x")}))

    def test_f_3_the_base_values_are_what_git_shows_for_the_base_commit(self):
        for rel, want in BASE_ENGINE.items():
            r = subprocess.run(["git", "show", "%s:%s%s" % (BASE_COMMIT, PREFIX, rel)], cwd=REPO, stdout=subprocess.PIPE)
            self.assertEqual(r.returncode, 0, rel)
            self.assertEqual(hashlib.sha256(r.stdout).hexdigest()[:16], want, rel)

    def test_f_4_core_and_the_unchanged_adapters_are_untouched_from_the_base(self):
        r = git("diff", "--numstat", BASE_COMMIT, "--", "core")
        self.assertEqual(r.stdout.strip(), u"", u"core/ に差分がある")
        for rel in ("adapters/xbrl/extract.py", "adapters/xbrl/recipes.py", "adapters/xbrl/resolve.py", "adapters/xbrl/comparators.py"):
            self.assertEqual(sha16(rel), BASE_ENGINE[rel], rel)

    def test_f_5_the_registered_profiles_are_as_the_seal_says(self):
        import sys
        sys.path.insert(0, ROOT)
        sys.path.insert(0, os.path.join(ROOT, "core", "py"))
        from adapters.xbrl import vocabulary as V
        self.assertTrue(V.PROFILES["P27C"].unnamed_candidate_2026_10_29)
        self.assertFalse(V.PROFILES["P27"].unnamed_candidate_2026_10_29)
        self.assertFalse(V.PROFILES["P27E"].unnamed_candidate_2026_10_29)
        self.assertEqual(V.DEFAULT_PROFILE, "P27")
        self.assertNotIn("P27EC", V.PROFILES)


class SealAndDocTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.inp = inputs()
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)

    def test_c_1_the_tables_equal_the_ones_rebuilt_from_the_record(self):
        self.assertEqual(check_c(self.rec, self.inp, self.seal, self.doc), [])

    def test_c_2_the_prose_outside_the_tables_is_in_order(self):
        self.assertEqual(check_doc_prose(self.rec, self.inp, self.seal, self.doc), [])

    def test_d_6_the_prediction_table_copies_the_seal_and_the_judgments(self):
        B = render_blocks(self.rec, self.inp, self.seal)
        P = seal_predictions(self.seal)
        J = judge(self.rec, self.inp, self.seal)
        got = doc_blocks(self.doc)["pred"][2:]
        self.assertEqual(len(got), 11)
        for line, (k, (field, pred, miss)) in zip(got, P.items()):
            cells = line.strip(u"|").split(u" | ")
            cells = [c.strip() for c in cells]
            self.assertEqual(cells[0], u"**%s**" % k)
            self.assertEqual(cells[1], field)
            self.assertEqual(cells[2], pred)
            self.assertEqual(cells[3], miss)
            self.assertEqual(cells[5], hit_word(J[k][1]))
        self.assertEqual(B["pred"][2:], got)

    def test_h_1_no_docid_no_claim_id_and_no_filer_prefix_in_the_document(self):
        self.assertEqual(check_h(self.doc, self.inp["fetched"], self.rec), [])

    def test_h_2_the_filer_prefix_collector_works_on_a_made_up_pointer(self):
        rec = {u"候補の行(P27C。reason が no_same_value か候補が辞書の行)": [{"candidate": {"pointer": "xbrl:jpcrp030000-asr_E00000-000:Foo@Ctx"}}, {"candidate": {"pointer": "xbrl:jppfs_cor:Bar@Ctx"}}, {"candidate": None}],
               u"P27EC の行(30 書類。P27・P27EC のどちらかで reason が no_same_value か候補が辞書の行)": [],
               u"注入 741 行": [{"candidate": None, "pointers": ["xbrl:jpcrp030000-asr_E11111-000:Baz@Ctx", None]}]}
        self.assertEqual(filer_prefixes(rec), set(["jpcrp030000-asr_E00000-000", "jpcrp030000-asr_E11111-000"]))

    def test_h_3_the_record_names_the_documents_and_that_is_why_it_is_declared(self):
        blob = jtext(REC)
        self.assertTrue(re.search(r"S100[0-9A-Z]{4}", blob))
        self.assertTrue(re.search(r"\"id\": \"S100|\"id\": \"N\d{3}\"", blob))

    def test_doc_states_the_dated_notes(self):
        self.assertIn(u"2026-10-30", self.doc)
        self.assertIn(u"stop_reason_2026-10-29.json", self.doc)
        self.assertIn(u"unnamed_fact_2026-10-29.json", self.doc)

    def test_doc_does_not_say_the_candidate_is_correct(self):
        for w in (u"正しい候補", u"正解の候補", u"候補は正しい", u"原本の fact だと確かめた"):
            self.assertNotIn(w, self.doc)


class ScriptTest(unittest.TestCase):
    def test_script_does_not_remeasure_when_the_output_exists(self):
        before = hashlib.sha256(open(REC, "rb").read()).hexdigest()
        env = dict((k, v) for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY", "EDINET_API_KEY", "EDINETDB_API_KEY"))
        r = subprocess.run(["python3", SCRIPT, "--out", REC], cwd=ROOT, capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr[-400:])
        self.assertIn(u"測り直さない", r.stdout)
        self.assertEqual(hashlib.sha256(open(REC, "rb").read()).hexdigest(), before)

    def test_script_touches_the_previous_module_only_through_obs_allp_and_claim_keys(self):
        import ast
        tree = ast.parse(jtext(SCRIPT))
        sets = sorted(ast.unparse(n.targets[0]) for n in ast.walk(tree) if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Attribute) and ast.unparse(n.targets[0]).startswith("RE."))
        self.assertEqual(sets, ["RE.ALLP", "RE.CLAIM_KEYS", "RE.OBS"])
        self.assertEqual(sum(1 for n in ast.walk(tree) if isinstance(n, ast.Call) and ast.unparse(n.func) == "WIRING['RE'].work_doc"), 1)

    def test_script_registers_the_extra_profile_only_inside_try_finally(self):
        import ast
        tree = ast.parse(jtext(SCRIPT))
        regs = [n for n in ast.walk(tree) if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == "V.PROFILES['P27EC']"]
        self.assertEqual(len(regs), 1)
        tries = [n for n in ast.walk(tree) if isinstance(n, ast.Try) and any(ast.unparse(s).startswith("V.PROFILES.pop('P27EC'") for s in n.finalbody)]
        self.assertEqual(len(tries), 1)

    def test_script_imports_no_network_module_and_reads_no_key(self):
        import ast
        tree = ast.parse(jtext(SCRIPT))
        mods = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                mods |= set(a.name.split(".")[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom):
                mods.add((n.module or "").split(".")[0])
        self.assertEqual(mods, set(["__future__", "argparse", "collections", "concurrent", "dataclasses", "hashlib", "importlib", "io", "json", "multiprocessing", "os", "shutil",
                                    "subprocess", "sys", "tempfile", "time", "adapters"]))
        consts = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        self.assertIn([c for c in consts if "API_KEY" in c], ([], ["API_KEY"]))               # 後者は書き出す前の鍵らしい字の検査の針(鍵を読む字ではない)
        env_args = sorted(set(ast.unparse(n.args[0]) for n in ast.walk(tree) if isinstance(n, ast.Call) and ast.unparse(n.func) == "os.environ.get"))
        self.assertEqual(env_args, ["'CAND_ENGINE_ROOT'", "'TMPDIR'"])
        self.assertFalse([n for n in ast.walk(tree) if isinstance(n, ast.Call) and ast.unparse(n.func) in ("os.getenv", "os.environ.__getitem__")])
        self.assertFalse([n for n in ast.walk(tree) if isinstance(n, ast.Subscript) and ast.unparse(n.value) == "os.environ"])

    def test_script_sha_in_the_record_is_the_script_that_measured(self):
        self.assertEqual(jload(REC)[u"この script の sha256"], sha64(SCRIPT_REL))

class FalseRecordsAreRedTest(unittest.TestCase):
    u"""(g) 偽物で赤: 記録の写しを 1 か所変えると (b)(c)(d)(e) が赤になる(変異)。"""

    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.inp = inputs()
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)

    def b(self, rec):
        return check_b(rec, self.inp)

    def c(self, rec, doc=None, seal=None):
        return check_c(rec, self.inp, seal or self.seal, doc or self.doc)

    def e(self, rec):
        return check_e(rec, self.inp)

    def test_g_0_baseline_is_green(self):
        self.assertEqual(self.b(self.rec), [])
        self.assertEqual(self.c(self.rec), [])
        self.assertEqual(self.e(self.rec), [])
        self.assertEqual(check_a(self.rec, self.inp), [])

    def test_g_1_changing_one_judgment_of_k_turns_the_adoption_red(self):
        rec = copy.deepcopy(self.rec)
        d = rec[u"書類(出てくる順)"][0]
        rec[u"書類ごと"][d][u"行ごとの一致(5 欄)"][u"P27C と P27(旗が偽。いまの engine)"] -= 1
        self.assertFalse(judge_k(rec, self.inp, self.seal)["K-1"][1])
        self.assertNotEqual(self.c(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"書類ごと"][d][u"客向けの報告"][u"既定"][u"旗が偽の本文が比べる側と byte 一致"] = False
        self.assertFalse(judge_k(rec, self.inp, self.seal)["K-3"][1])
        self.assertFalse(adopted(rec, self.inp, self.seal))
        self.assertNotEqual(self.c(rec), [])

    def test_g_2_changing_the_number_of_candidate_rows_turns_e_and_c_red(self):
        rec = copy.deepcopy(self.rec)
        d = doc_split(rec)[1][0]
        rec[u"書類ごと"][d][u"profiles"]["P27C"][u"候補が辞書の行"] += 1
        self.assertNotEqual(self.e(rec), [])
        self.assertNotEqual(self.c(rec), [])
        rec = copy.deepcopy(self.rec)
        x = [x for x in rec[u"候補の行(P27C。reason が no_same_value か候補が辞書の行)"] if x["candidate"] is not None][0]
        x["candidate"] = None
        self.assertNotEqual(self.e(rec), [])
        self.assertNotEqual(self.c(rec), [])

    def test_g_3_changing_one_row_of_the_741_turns_b_and_c_red(self):
        rec = copy.deepcopy(self.rec)
        r = [r for r in rec[u"注入 741 行"] if r["state"] is not None][0]
        r["state"] = "GROUNDED" if r["state"] != "GROUNDED" else "VALUE_MISMATCH"
        self.assertNotEqual(self.b(rec), [])
        self.assertNotEqual(self.c(rec), [])
        rec = copy.deepcopy(self.rec)
        r = [r for r in rec[u"注入 741 行"] if r["candidate"] is not None][0]
        r["candidate"]["pointer"] += "Z"
        self.assertNotEqual(self.e(rec), [])
        self.assertNotEqual(self.c(rec), [])

    def test_g_4_changing_the_candidate_content_turns_e_and_c_red(self):
        rec = copy.deepcopy(self.rec)
        x = [x for x in rec[u"候補の行(P27C。reason が no_same_value か候補が辞書の行)"] if x["candidate"] is not None and x["doc"] in doc_split(rec)[1]][0]
        x["candidate"]["value"] = x["candidate"]["value"] + 1
        self.assertNotEqual(self.e(rec), [])
        self.assertNotEqual(self.c(rec), [])

    def test_g_5_the_wiring_flag_and_the_record_flags_turn_b_red(self):
        rec = copy.deepcopy(self.rec)
        rec[u"配線の門"][u"通った"] = False
        self.assertNotEqual(self.b(rec), [])
        rec = copy.deepcopy(self.rec)
        d = rec[u"書類(出てくる順)"][0]
        rec[u"書類ごと"][d][u"比べる側"]["P27"][u"4 state"]["GROUNDED"] += 1
        self.assertNotEqual(self.b(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"cache"][u"終了"][u"edinet"][u"件数"] = 282
        self.assertNotEqual(self.b(rec), [])

    def test_g_6_one_character_of_the_document_table_turns_c_red(self):
        doc = self.doc
        i = doc.index(u"<!-- 門:start counts -->")
        j = doc.index(u"|", doc.index(u"\n|", i) + 1)
        k = [m.start() for m in re.finditer(r"\d", doc[j:])][0] + j
        bad = doc[:k] + (u"9" if doc[k] != u"9" else u"8") + doc[k + 1:]
        self.assertNotEqual(self.c(self.rec, doc=bad), [])

    def test_g_7_changing_a_prediction_character_of_the_seal_turns_d_and_c_red(self):
        seal = self.seal.replace(u"**296 / 296**", u"**295 / 296**", 1)
        self.assertNotEqual(seal, self.seal)
        self.assertNotEqual(self.c(self.rec, seal=seal), [])
        self.assertNotEqual(judge(self.rec, self.inp, seal)["CA-5"][1], judge(self.rec, self.inp, self.seal)["CA-5"][1])

    def test_g_8_a_docid_a_claim_id_or_a_filer_prefix_in_the_document_turns_h_red(self):
        fetched = self.inp["fetched"]
        d0 = fetched[u"使う書類"][0]
        self.assertNotEqual(check_h(self.doc + u"\n" + d0 + u"\n", fetched, self.rec), [])
        cid = self.rec[u"候補の行(P27C。reason が no_same_value か候補が辞書の行)"][0]["id"]
        self.assertNotEqual(check_h(self.doc + u"\n" + cid + u"\n", fetched, self.rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"候補の行(P27C。reason が no_same_value か候補が辞書の行)"].append({"doc": "x", "id": "x", "state": "x", "reason": NSV,
                                                                    "candidate": {"pointer": "xbrl:jpcrp030000-asr_E99999-000:Foo@Ctx", "value": 1, "basis": NSV}})
        self.assertEqual(check_h(self.doc, fetched, rec), [])
        self.assertNotEqual(check_h(self.doc + u"\njpcrp030000-asr_E99999-000\n", fetched, rec), [])
        self.assertNotEqual(check_h(self.doc + u"\n" + u"```\n", fetched, self.rec), [])

    def test_g_9_an_unmarked_number_in_prose_turns_the_prose_check_red(self):
        bad = self.doc + u"\n候補が付いた行は 300 行だった。\n"
        self.assertNotEqual(check_doc_prose(self.rec, self.inp, self.seal, bad), [])

    def test_g_10_changing_the_adoption_sentence_turns_the_prose_check_red(self):
        bad = self.doc.replace(u"採用する。K-1〜K-4 が全部満たされた", u"採用しない。K-1〜K-4 が全部満たされた")
        if bad != self.doc:
            self.assertNotEqual(check_doc_prose(self.rec, self.inp, self.seal, bad), [])
        else:
            bad = self.doc.replace(u"採用しない。K-1〜K-4 のどれかが", u"採用する。K-1〜K-4 のどれかが")
            self.assertNotEqual(bad, self.doc)
            self.assertNotEqual(check_doc_prose(self.rec, self.inp, self.seal, bad), [])

    def test_g_11_changing_the_input_sha_turns_j_red(self):
        rec = copy.deepcopy(self.rec)
        rec[u"読んだ入力の sha256"][STOP_REL] = u"0" * 64
        self.assertNotEqual(check_j(rec), [])
        rec = copy.deepcopy(self.rec)
        del rec[u"読んだ入力の sha256"][ROSTER_REL]
        self.assertNotEqual(check_j(rec), [])


class OrderTest(unittest.TestCase):
    u"""(i) 封の commit < 実装の commit <= script・記録・文書・門の commit。"""

    @classmethod
    def setUpClass(cls):
        cls.base = tempfile.mkdtemp(prefix="unnamedcand_root_")
        cls.grun = staticmethod(make_run(REPO))

    def _p(self, steps):
        t = build(self.base, steps)
        return order_problems(t.run, "")

    def test_i_1_the_real_history_has_the_seal_before_the_implementation_before_the_files(self):
        u"""実装・script・記録・文書・門のどれかが未 commit なら赤(足した commit が無い)。全部 commit された後で初めて緑。"""
        p = order_problems(self.grun, PREFIX)
        self.assertEqual(p, [])

    def test_i_2_the_real_seal_is_one_commit_and_an_ancestor_of_head(self):
        lst = added_commits(self.grun, PREFIX + SEAL_REL)
        self.assertEqual(len(lst), 1)
        self.assertTrue(lst[0].startswith(SEAL_COMMIT_SHORT))
        self.assertTrue(is_anc(self.grun, lst[0], "HEAD"))
        self.assertTrue(is_anc(self.grun, lst[0], "HEAD"))
        rc, approval = self.grun("rev-parse", APPROVAL_COMMIT_SHORT)
        self.assertEqual(rc, 0)
        self.assertTrue(is_anc(self.grun, approval, "HEAD"))

    def test_i_3_a_correct_order_is_green(self):
        self.assertEqual(self._p(["SEAL", "IMPL", "SCRIPT", "RECORD", "DOC", "GATE"]), [])
        self.assertEqual(self._p(["SEAL", "IMPL", "ALL4"]), [])
        self.assertEqual(self._p(["SEAL", "IMPL", "ALL4", "SEAL_APPEND"]), [])

    def test_i_4_a_file_before_the_seal_is_red(self):
        for first in ("SCRIPT", "RECORD", "DOC", "GATE", "IMPL"):
            steps = [first, "SEAL"] + [k for k in ("IMPL", "SCRIPT", "RECORD", "DOC", "GATE") if k != first]
            self.assertIn(first + "_BEFORE_SEAL", codes(self._p(steps)), first)

    def test_i_5_an_uncommitted_file_is_red_not_skipped(self):
        self.assertIn("GATE_UNCOMMITTED", codes(self._p(["SEAL", "IMPL", "SCRIPT", "RECORD", "DOC"])))
        self.assertIn("SCRIPT_UNCOMMITTED", codes(self._p(["SEAL", "IMPL"])))
        self.assertIn("IMPL_UNCOMMITTED", codes(self._p(["SEAL", "ALL4"])))
        self.assertIn("IMPL_UNCOMMITTED", codes(self._p(["SEAL", "IMPL_PLAIN", "ALL4"])))

    def test_i_6_the_seal_missing_or_added_twice_is_red(self):
        self.assertIn("SEAL_ONCE", codes(self._p(["ALL4"])))
        self.assertIn("SEAL_ONCE", codes(self._p(["SEAL", "IMPL", "ALL4", "SEAL_TWICE"])))

    def test_i_7_rewriting_the_seal_after_the_fact_is_red(self):
        self.assertIn("SEAL_REWRITE", codes(self._p(["SEAL", "IMPL", "ALL4", "SEAL_REWRITE"])))

    def test_i_8_the_same_commit_as_the_seal_is_red(self):
        t = Tmp(self.base)
        for k in ("SEAL", "SCRIPT", "RECORD", "DOC", "GATE"):
            t.write(FILES[k], u"# %s\n" % k)
        t.write(FILES["IMPL"], u"CLAIM_FIELDS = (\"candidate\",)\n")
        t.commit("all", *FILES.values())
        self.assertIn("SCRIPT_BEFORE_SEAL", codes(order_problems(t.run, "")))

    def test_i_9_the_files_before_the_implementation_are_red(self):
        for first in ("SCRIPT", "RECORD", "DOC", "GATE"):
            steps = ["SEAL", first, "IMPL"] + [k for k in ("SCRIPT", "RECORD", "DOC", "GATE") if k != first]
            self.assertIn(first + "_BEFORE_IMPL", codes(self._p(steps)), first)


if __name__ == "__main__":
    unittest.main()
