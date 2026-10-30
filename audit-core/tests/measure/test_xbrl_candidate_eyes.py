# -*- coding: utf-8 -*-
u"""候補の欄(``candidate``)の正しさを、読み手の席が無改変の 10 行で 1 回だけ見た便の門。封 docs/XBRL_CANDIDATE_EYES_SEAL_2026-10-30.md §2-1〜§2-5・§3(E-1〜E-9)・§5 の 6。

記録 ``fixtures/xbrl/candidate_eyes_2026-10-30.json``(``measure/xbrl_candidate_eyes_2026-10-30.py`` の ``collect`` の出力)・文書 ``docs/XBRL_CANDIDATE_EYES_2026-10-30.md``。
**束(dossier)と返事の理由の自由文は repo に無い(scratchpad)。この門は記録の数だけを読む。**

  (a) 記録が在り、鍵が揃う(行 10・席 3・配線の門・集計)。
  (b) 配線の門 (1)〜(6) を、記録・``unnamed_candidate_2026-10-29.json``・``unnamed_fact_2026-10-29.json``・``fetched_2026-10-21.json`` から数え直す。(4) は束の sha256 の形と一意だけ(束は repo に無い)。
  (c) 文書の表(``<!-- 門:start 名前 -->``)を記録から作り直して 1 行も違わない。門の外の散文の数には【門なし】の印が要る。
  (d) E-1〜E-9 の当否を、封の字(幅)と記録から求め直す。封の字(欄・予測・外れ方)と文書の当否の表の字が一致する。
  (e) 多数決・全員一致・割れた・集計を、行の席ごとの読みから別実装で求め直して記録と一致させる。
  (f) engine の sha16(``ENGINE_AT_MEASURE``・``ENGINE_DECLARED``)。
  (g) 偽物で赤(記録の 1 席の読み・多数決の欄・配線の数・文書の当否と表の 1 字・封の幅の 1 字・文書に docID・指示文の 1 字・記録に理由の鍵・LATER_NAMING_FILES から外す)。
  (h) docID・claim の id が封と文書に無い。
  (i) 順序: 実装 ``cb8612f`` < 封 ``9d847c0`` < script・記録・文書・門の commit。追跡されていない file は『足した commit が無い』で赤(skip にしない)。
  (j) 指示文 ``READER_PROMPT``・包み ``WRAPPER`` が封 §2-4 の blockquote と 1 字も違わない。script の定数が封の位置・語と同じ。
  (k) 記録に理由の自由文・span・原文・束の見出しが無い。
  (l) 10 行の選び方(記録の id を封 §2-1 の規則で ``unnamed_candidate_2026-10-29.json`` から求め直して一致)。

**(i) は、script・記録・文書・門のどれかが commit される前は赤になる**(順序の門の「未 commit」分。skip にしない)。前例 ``test_xbrl_unnamed_candidate_result.py`` と同じ扱い。
**変数名について**: 過去の門が tests/measure の行頭の名前を数えるので、この門は ``ENGINE_AT_MEASURE``・``ENGINE_DECLARED`` 以外の engine の留めの名前を行頭に置かない。この file は docID の字を持たない。
"""
import ast
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

SEAL_REL = "docs/XBRL_CANDIDATE_EYES_SEAL_2026-10-30.md"
DOC_REL = "docs/XBRL_CANDIDATE_EYES_2026-10-30.md"
REC_REL = "fixtures/xbrl/candidate_eyes_2026-10-30.json"
SCRIPT_REL = "measure/xbrl_candidate_eyes_2026-10-30.py"
GATE_REL = "tests/measure/test_xbrl_candidate_eyes.py"
CAND_REL = "fixtures/xbrl/unnamed_candidate_2026-10-29.json"
UNNAMED_REL = "fixtures/xbrl/unnamed_fact_2026-10-29.json"
FETCHED_REL = "fixtures/xbrl/fresh/fetched_2026-10-21.json"
ROSTER_REL = "fixtures/xbrl/taxonomy_labels_sha256.txt"
FRESH_SEAL_REL = "tests/measure/test_xbrl_fresh_seal.py"
INPUT_RELS = [CAND_REL, UNNAMED_REL, FETCHED_REL, ROSTER_REL]
SEAL, DOC, REC, SCRIPT = [os.path.join(ROOT, r) for r in (SEAL_REL, DOC_REL, REC_REL, SCRIPT_REL)]
SEAL_COMMIT_SHORT = "9d847c0"
IMPL_COMMIT_SHORT = "cb8612f"
DECL_COMMIT_SHORT = "f71a9a3"
NOT_GATED = u"【門なし】"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
FORBIDDEN = (u"精度", u"ハルシネーション", u"証明した", u"LLM より正確", u"世界で 1 社", u"貴社の DB の誤り", u"取り戻す", u"勧め")
#: 文書に書いてはいけない言い方(候補を誤りと断じる・正解と断じる)。読み手は正解集合でない(封 §4)
OVERCLAIM = (u"候補は誤り", u"候補が誤り", u"候補は全部誤り", u"候補は間違い", u"候補は全部間違い", u"候補はすべて誤り", u"正解の候補", u"正しい候補", u"候補は正しい")

READINGS = (u"出所として正しい", u"別の出所", u"文から判断できない")
EXPLANATIONS = (u"単位", u"丸め", u"符号", u"率", u"文の数が違う", u"その他")
SEATS = (u"席1", u"席2", u"席3")
SPLIT = u"割れた"
NROWS = 10
NSEATS = 30
#: 追記 13 が人間の決定を写す 1 か所だけは、禁止語「勧め」の検査から外す(次の封の勧めではなく、決定の内容の引用)。他の「勧め」は禁止のまま
DECISION_QUOTE = u"司令塔の勧め(読み直さない"

#: engine の sha16(測った時点の値。字で留める ― 測った事実。封 §0 の頭の字。engine は 0 行)。変えるなら宣言された遷移として下の ENGINE_DECLARED に足す。
ENGINE_AT_MEASURE = {
    "adapters/xbrl/extract.py": "3cf55966f12919f0", "adapters/xbrl/vocabulary.py": "7fbcfbf0e472f366", "adapters/xbrl/recipes.py": "52d645e713c53c1c",
    "adapters/xbrl/resolve.py": "a41043763c1d4073", "adapters/xbrl/comparators.py": "d8706338325e725b", "adapters/xbrl/verify_document.py": "6c76c8ade6c7b1c8",
    "adapters/xbrl/report_customer.py": "bdbaa00a419219fe",
}
#: 宣言された遷移 {file: (遷移の後の sha16, その遷移を宣言した封)}。今は 0 件。足すときは、封が履歴に在り、値が宣言の値のときだけ受け入れる。測った時点の値は消さない。
ENGINE_DECLARED = {}

#: 記録から求めた当否のうち外れ・判定しないの名前(測った事実。外れは外れのまま残す。封も予測も直さない)。食い違えば d_4 が赤。
MISSES = ["E-3", "E-4", "E-5"]
UNDECIDED = ["E-6", "E-9"]

#: 行頭に置いてはいけない名前(過去の門が数える)。この file の中で行頭に出る字を d の試験が見る
RESERVED_HEADS = ("ENGINE_LATER", "UNTOUCHED", "PIN_DEF", "LATER_ENGINE_COMMITS", "FROZEN_LATER", "ENGINE_TRANSITIONS", "LATER_FINGERPRINT", "FINGERPRINT_",
                  "LATER_TARGET", "LATER_FROZEN", "FROZEN_BUNDLE_AT_SEAL", "TARGET_AT_SEAL", "ENGINE_AT_SEAL")

REC_KEYS = [u"注意", u"封", u"HEAD の commit", u"DEFAULT_PROFILE", u"engine sha16", u"engine の指紋", u"この script の sha256", u"読んだ入力の sha256", u"ラベル",
            u"選び方の規則", u"指示文と包み", u"配線の門", u"行", u"集計", u"cache", u"所要秒", u"limits", u"key_leaks"]
ROW_KEYS = [u"位置", u"書類の位置", u"doc", u"id", u"候補", u"候補の字", u"束", u"席", u"多数決", u"全員一致", u"全員一致の読み", u"診断の帯"]
SEAT_KEYS = [u"読み", u"値の違いの説明", u"失敗", u"失敗の全種類", u"入力の照合", u"道具の回数", u"返事の sha256"]
BUNDLE_HEADS = (u"# 読む行", u"## 1 文の段落", u"## 2 文の数", u"## 3 道具が示した fact")
BAD_KEYS = (u"理由", u"span", u"原文", u"subject", u"text", u"claim の value", u"束の本文")


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


def sha_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


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
    return {"cand": rload(CAND_REL), "unn": rload(UNNAMED_REL), "fetched": rload(FETCHED_REL)}


# ----------------------------------------------------------------------------------------------------------------
# 封の字を読む
def seal_predictions(seal):
    u"""封 §3 の表の行 {名前: (欄, 予測, 外れ方)}(封の字のまま)。"""
    out = collections.OrderedDict()
    for l in seal.splitlines():
        m = re.match(r"^\| \*\*(E-\d)\*\* (.*)$", l)
        if m:
            cells = [c.strip() for c in (m.group(2).rstrip()[:-1].rstrip() if m.group(2).rstrip().endswith(u"|") else m.group(2)).split(u" | ")]
            assert len(cells) == 3, l
            out[m.group(1)] = tuple(cells)
    return out


def seal_positions(seal):
    m = re.search(r"並びの位置 \*\*([0-9, ]+)\*\* の 10 行", seal)
    return [int(x) for x in m.group(1).split(u",")]


def seal_blockquotes(seal):
    u"""封 §2-4 の blockquote(連続する ``>`` の行のまとまり)を、先頭の「> 」(空行は「>」)を外した字の列で返す。"""
    a = seal.index(u"### §2-4")
    b = seal.index(u"### §2-5")
    groups, cur = [], []
    for l in seal[a:b].split(u"\n"):
        if l.startswith(u">"):
            cur.append(l[2:] if l.startswith(u"> ") else l[1:])
        elif cur:
            groups.append(u"\n".join(cur))
            cur = []
    if cur:
        groups.append(u"\n".join(cur))
    return groups


def num(s):
    return int(s.replace(u",", u""))


def rng(s):
    m = re.match(r"^(\d[\d,]*)(?:〜(\d[\d,]*))?", s.strip())
    lo = num(m.group(1))
    return (lo, num(m.group(2)) if m.group(2) else lo)


def within(v, r):
    return r[0] <= v <= r[1]


def bold_after(pred, label):
    m = re.search(u"「" + re.escape(label) + u"」\\*\\*([^*]+)\\*\\*", pred)
    return rng(m.group(1))


def first_bold(pred):
    return rng(re.search(r"\*\*([^*]+)\*\*", pred).group(1))


def span_text(r):
    return u"%d〜%d" % r


# ----------------------------------------------------------------------------------------------------------------
# 別実装: 合わせ方・数え直し(記録の「多数決」「全員一致」「集計」を読まず、席ごとの読みから求める)
def seat_reading(seat):
    return None if seat[u"失敗"] else seat[u"読み"]


def combine_ref(readings):
    ok = [r for r in readings if r is not None]
    cnt = collections.Counter(ok)
    best = max(cnt.values()) if cnt else 0
    winners = [r for r, c in cnt.items() if c == best]
    maj = winners[0] if (len(ok) >= 2 and best >= 2 and len(winners) == 1) else SPLIT
    return maj, (len(ok) == 3 and best == 3)


def band_of(inp):
    return dict(((r["doc"], r["id"]), r) for r in inp["unn"]["plain_rows"])


def counter_dict(it):
    return dict(collections.Counter(it))


def recount(rec, inp):
    rows = rec[u"行"]
    maj, unan = [], []
    for r in rows:
        m, u = combine_ref([seat_reading(r[u"席"][s]) for s in SEATS])
        maj.append(m)
        unan.append(u)
    bands = band_of(inp)
    near = []
    for r, m in zip(rows, maj):
        if m == READINGS[0]:
            b = bands[(r["doc"], r["id"])]
            near.append(b[u"帯"] == u"(15% 以内)" or bool(b[u"10 の冪に近い"]))
    seat_reads = dict((s, [seat_reading(r[u"席"][s]) for r in rows]) for s in SEATS)
    okseats = dict((s, sum(1 for x in seat_reads[s] if x == READINGS[0])) for s in SEATS)
    expl = counter_dict(r[u"席"][s][u"値の違いの説明"] for r in rows for s in SEATS if seat_reading(r[u"席"][s]) == READINGS[0])
    fails = counter_dict(r[u"席"][s][u"失敗"] for r in rows for s in SEATS if r[u"席"][s][u"失敗"])
    all3 = [r[u"位置"] for r in rows if all(seat_reading(r[u"席"][s]) for s in SEATS) and len(set(seat_reading(r[u"席"][s]) for s in SEATS)) == 3]
    return {
        "maj": maj, "unan": unan, "okseats": okseats, "expl": expl, "fails": fails, "all3": all3,
        "tools": sum(1 for r in rows for s in SEATS if (r[u"席"][s][u"道具の回数"] or 0) > 0),
        "match_false": sum(1 for r in rows for s in SEATS if r[u"席"][s][u"入力の照合"] is False),
        "match_none": sum(1 for r in rows for s in SEATS if r[u"席"][s][u"入力の照合"] is None),
        "match_true": sum(1 for r in rows for s in SEATS if r[u"席"][s][u"入力の照合"] is True),
        "reply_pass": sum(1 for r in rows for s in SEATS if not any(k in r[u"席"][s][u"失敗の全種類"] for k in (u"返事が無い", u"JSON でない", u"読みの語が外", u"説明の語が外", u"理由が無い"))),
        "fail_seats": sum(1 for r in rows for s in SEATS if r[u"席"][s][u"失敗"]),
        "full": [r[u"位置"] for r in rows if r[u"束"][u"段落は全文"]],
        "near": near,
    }


def expected_tally(rec, inp):
    c = recount(rec, inp)
    rows = rec[u"行"]
    maj_ok = [m for m in c["maj"] if m == READINGS[0]]
    return {
        u"多数決の読みごとの行数": counter_dict(c["maj"]),
        u"全員一致の読みごとの行数": counter_dict(m for m, u in zip(c["maj"], c["unan"]) if u),
        u"割れた行": sum(1 for m in c["maj"] if m == SPLIT),
        u"席ごとの読みの分布(失敗を含む)": dict((s, counter_dict(seat_reading(r[u"席"][s]) or u"失敗" for r in rows)) for s in SEATS),
        u"席ごとの「出所として正しい」の数": c["okseats"],
        u"「出所として正しい」を選んだ席の値の違いの説明(席の数)": c["expl"],
        u"3 席の読みが 3 つとも違う行(位置)": c["all3"],
        u"失敗の数(種類ごと)": c["fails"],
        u"失敗の数(全部。分母 %d)" % (len(rows) * 3): c["fail_seats"],
        u"入力の照合が未確認の席": c["match_none"],
        u"入力の照合が外れた席": c["match_false"],
        u"道具を使った席": c["tools"],
        u"段落が全文になった行(位置)": c["full"],
        u"E-9 多数決が「出所として正しい」の行": {u"行数": len(maj_ok), u"帯が 15% 以内か 10 の冪に近い": sum(1 for x in c["near"] if x),
                                         u"過半": (sum(1 for x in c["near"] if x) * 2 > len(maj_ok)) if maj_ok else u"該当なし"},
    }


# ----------------------------------------------------------------------------------------------------------------
# (a)(b)(k)(l)
def check_a(rec):
    out = []
    if list(rec) != REC_KEYS:
        out.append(u"記録の鍵が違う: %s" % list(rec))
        return out
    rows = rec[u"行"]
    if len(rows) != NROWS:
        out.append(u"行が %d でない" % NROWS)
    for r in rows:
        if list(r) != ROW_KEYS:
            out.append(u"行の鍵が違う")
            break
        if list(r[u"席"]) != list(SEATS):
            out.append(u"席が 席1・席2・席3 でない")
            break
        for s in SEATS:
            st = r[u"席"][s]
            if list(st) != SEAT_KEYS:
                out.append(u"席の鍵が違う")
                break
            if (st[u"読み"] is None) != (st[u"失敗"] is not None):
                out.append(u"読みと失敗が排他でない")
            if st[u"読み"] is not None and st[u"読み"] not in READINGS:
                out.append(u"読みの語が封の語でない")
            if st[u"読み"] == READINGS[0]:
                if st[u"値の違いの説明"] not in EXPLANATIONS:
                    out.append(u"『出所として正しい』なのに説明の語が封の語でない")
            elif st[u"値の違いの説明"] is not None:
                out.append(u"『出所として正しい』でないのに説明が付いている")
            if st[u"失敗"] is not None and (not st[u"失敗の全種類"] or st[u"失敗の全種類"][0] != st[u"失敗"]):
                out.append(u"失敗と失敗の全種類が食い違う")
            if st[u"失敗"] is None and any(k != u"入力の照合が外れた" for k in st[u"失敗の全種類"]):
                out.append(u"失敗が無いのに失敗の全種類がある")
            if st[u"返事の sha256"] is not None and not HEX64.match(st[u"返事の sha256"]):
                out.append(u"返事の sha256 の形が違う")
    g = rec[u"配線の門"]
    if g.get(u"(1)〜(4) が通った") is not True:
        out.append(u"記録の (1)〜(4) が通っていない")
    if rec[u"key_leaks"] != []:
        out.append(u"key_leaks が空でない")
    c = rec[u"cache"]
    if not (c[u"変化なし"] and c[u"開始"] == c[u"終了"] and c[u"開始"][u"edinet"][u"件数"] == 281 and c[u"開始"][u"edinet-fresh-2026-10-21"][u"件数"] == 40):
        out.append(u"cache の前後が 281 / 40 で不変でない")
    if rec[u"DEFAULT_PROFILE"] != "P27":
        out.append(u"DEFAULT_PROFILE が P27 でない")
    if rec[u"封"] != {u"file": SEAL_REL, u"commit": SEAL_COMMIT_SHORT, u"実装の commit": IMPL_COMMIT_SHORT, u"宣言の commit": DECL_COMMIT_SHORT}:
        out.append(u"記録の封の欄が封・実装・宣言の commit と違う")
    return out


def selected_rows(cand, positions):
    u"""封 §2-1 の規則を ``unnamed_candidate_2026-10-29.json`` から求め直す(script を読まない別実装)。"""
    inj = cand[u"注入の書類(出てくる順)"]
    pos = dict((d, i) for i, d in enumerate(inj))
    rows = [r for r in cand[u"候補の行(P27C。reason が no_same_value か候補が辞書の行)"] if r["doc"] in pos]
    rows.sort(key=lambda r: (pos[r["doc"]], r["id"]))
    return [(p, pos[rows[p]["doc"]], rows[p]) for p in positions], len(rows)


def check_l(rec, inp, seal):
    out = []
    positions = seal_positions(seal)
    sel, n296 = selected_rows(inp["cand"], positions)
    if n296 != 296:
        out.append(u"注入の書類の候補の行が 296 でない")
    rows = rec[u"行"]
    if [r[u"位置"] for r in rows] != positions:
        out.append(u"記録の位置が封 §2-1 の位置と違う")
    if rec[u"選び方の規則"][u"位置"] != positions:
        out.append(u"記録の選び方の規則の位置が封と違う")
    if len(rows) != len(sel):
        return out + [u"行の数が違う"]
    for r, (p, dpos, c) in zip(rows, sel):
        if (r["doc"], r["id"], r[u"書類の位置"]) != (c["doc"], c["id"], dpos):
            out.append(u"位置 %d の (doc, id, 書類の位置) が封 §2-1 の規則で求めた行と違う" % p)
        if r[u"候補"][u"pointers"] != [c["candidate"]["pointer"]] or r[u"候補"][u"値"] != c["candidate"]["value"] or r[u"候補"]["basis"] != c["candidate"]["basis"]:
            out.append(u"位置 %d の候補が R の候補と違う" % p)
    if len(set(r["doc"] for r in rows)) != NROWS:
        out.append(u"10 行が 10 の別の書類でない")
    return out


def check_b(rec, inp, seal):
    u"""配線の門 (1)〜(6) を門が自分で数え直す。"""
    out = []
    positions = seal_positions(seal)
    cand = inp["cand"]
    sel, _n = selected_rows(cand, positions)
    cand_rows = dict(((r["doc"], r["id"]), r) for r in cand[u"候補の行(P27C。reason が no_same_value か候補が辞書の行)"])
    sha30 = dict((r["docID"], r["sha256"]) for r in inp["fetched"][u"取得した書類"] if r.get(u"使う"))
    rows = rec[u"行"]
    n1 = sum(1 for r in rows if (r["doc"], r["id"]) in cand_rows)
    n2 = sum(1 for r in rows if (r["doc"], r["id"]) in cand_rows and cand_rows[(r["doc"], r["id"])]["candidate"]["pointer"] == r[u"候補"][u"pointers"][0]
             and cand_rows[(r["doc"], r["id"])]["candidate"]["value"] == r[u"候補"][u"値"])
    n3 = sum(1 for r in rows if cand[u"書類ごと"][r["doc"]][u"zip の sha256"] == sha30.get(r["doc"]))
    n4 = sum(1 for r in rows if HEX64.match(r[u"束"][u"sha256"] or u"") and r[u"束"][u"bytes"] > 0 and r[u"束"][u"字数"] > 0)
    if len(set(r[u"束"][u"sha256"] for r in rows)) != len(rows):
        n4 = 0
    c = recount(rec, inp)
    g = rec[u"配線の門"]
    want = {u"(1) 行の一致": [n1, NROWS], u"(2) 候補の pointer・value の一致": [n2, NROWS], u"(3) ZIP の sha256": [n3, NROWS], u"(4) 束の sha256": [n4, NROWS],
            u"(5) 返事の検査(§2-4)を通った席": [c["reply_pass"], NSEATS], u"(6) 入力の照合": [c["match_true"], NSEATS]}
    for k, v in want.items():
        if g.get(k) != v:
            out.append(u"配線の門『%s』の記録 %s が数え直し %s と違う" % (k, g.get(k), v))
    if [n1, n2, n3, n4] != [NROWS] * 4:
        out.append(u"(1)〜(4) が 10 / 10 でない")
    bands = band_of(inp)
    for r in rows:
        b = bands.get((r["doc"], r["id"]))
        if b is None or r[u"診断の帯"] != {u"帯": b[u"帯"], u"10 の冪に近い": b[u"10 の冪に近い"]}:
            out.append(u"位置 %d の診断の帯が診断の記録と違う" % r[u"位置"])
    return out


def check_e(rec, inp):
    u"""多数決・全員一致・割れた・集計を別実装で求め直して記録と一致させる。"""
    out = []
    c = recount(rec, inp)
    for r, m, u in zip(rec[u"行"], c["maj"], c["unan"]):
        if r[u"多数決"] != m:
            out.append(u"位置 %d の多数決が席の読みから求めた値と違う" % r[u"位置"])
        if r[u"全員一致"] != u or r[u"全員一致の読み"] != (m if u else None):
            out.append(u"位置 %d の全員一致が席の読みから求めた値と違う" % r[u"位置"])
    want = expected_tally(rec, inp)
    got = json.loads(json.dumps(rec[u"集計"]))
    for k in want:
        if got.get(k) != json.loads(json.dumps(want[k])):
            out.append(u"集計『%s』が行から数え直した値と違う" % k)
    if sorted(got) != sorted(want):
        out.append(u"集計の鍵が違う")
    return out


def walk_keys(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield k
            for x in walk_keys(v):
                yield x
    elif isinstance(o, list):
        for v in o:
            for x in walk_keys(v):
                yield x


def walk_strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            for x in walk_strings(v):
                yield x
    elif isinstance(o, list):
        for v in o:
            for x in walk_strings(v):
                yield x


def check_k(rec):
    u"""記録に理由の自由文・span・原文・束の見出しが無い。"""
    out = []
    keys = set(k for k in walk_keys(rec) if isinstance(k, str))
    for k in BAD_KEYS:
        if k in keys:
            out.append(u"記録に鍵『%s』がある" % k)
    for s in walk_strings(rec):
        for h in BUNDLE_HEADS:
            if h in s:
                out.append(u"記録の字に束の見出し『%s』がある" % h)
        if len(s) > 400:
            out.append(u"記録に 400 字を超える字がある(自由文の疑い)")
    for r in rec[u"行"]:
        if set(r[u"束"]) != set([u"bytes", u"字数", u"sha256", u"段落の注", u"段落は全文", u"補いが効いた"]):
            out.append(u"束の欄が封 §4 の入れる欄と違う")
            break
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
# (j) 指示文・包み・script の定数
def script_consts(src):
    tree = ast.parse(src)
    out = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            try:
                out[n.targets[0].id] = ast.literal_eval(n.value)
            except Exception:
                pass
    return out


def check_prompt(src, seal, rec):
    out = []
    k = script_consts(src)
    groups = seal_blockquotes(seal)
    if len(groups) != 2:
        return [u"封 §2-4 の blockquote が 2 つでない(%d)" % len(groups)]
    if k.get("READER_PROMPT") != groups[0]:
        out.append(u"READER_PROMPT が封 §2-4 の指示文の blockquote と違う")
    if k.get("WRAPPER") != groups[1]:
        out.append(u"WRAPPER が封 §2-4 の包みの blockquote と違う")
    if list(k.get("POSITIONS", ())) != seal_positions(seal):
        out.append(u"POSITIONS が封 §2-1 の位置と違う")
    if k.get("PROBE_POSITIONS") != (15, 165):
        out.append(u"PROBE_POSITIONS が封 §2-1 の 4 の位置と違う")
    if k.get("READINGS") != READINGS or k.get("EXPLANATIONS") != EXPLANATIONS or k.get("SEATS") != SEATS:
        out.append(u"READINGS・EXPLANATIONS・SEATS が封の語と違う")
    ps = rec[u"指示文と包み"]
    if ps[u"指示文の sha256"] != sha_text(groups[0]) or ps[u"包みの sha256"] != sha_text(groups[1]):
        out.append(u"記録の指示文・包みの sha256 が封の blockquote と違う")
    return out


def load_checkers(src):
    u"""script の ``validate_reply``・``combine3`` と、それが使う定数だけを取り出して実行する(重い import をしない)。"""
    tree = ast.parse(src)
    want_assign = ("READINGS", "EXPLANATIONS", "SPLIT")
    body = []
    for n in tree.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id in want_assign:
            body.append(n)
        elif isinstance(n, ast.FunctionDef) and n.name in ("validate_reply", "combine3"):
            body.append(n)
    mod = ast.Module(body=body, type_ignores=[])
    ns = {"json": json, "collections": collections}
    exec(compile(mod, "<script-checkers>", "exec"), ns)
    return ns


def good(read, expl, why=u"x"):
    return json.dumps({u"読み": read, u"値の違いの説明": expl, u"理由": why}, ensure_ascii=False)


def behaviour_problems(ns):
    u"""``validate_reply``・``combine3`` の振る舞いの表(封 §2-4・§2-5)。外れた行の説明の列。"""
    out = []
    v, c = ns["validate_reply"], ns["combine3"]
    A, B, C = READINGS
    ok_cases = [(good(A, u"単位"), (A, u"単位", u"x")), (good(A, u"文の数が違う"), (A, u"文の数が違う", u"x")),
                (good(B, None), (B, None, u"x")), (good(C, None), (C, None, u"x"))]
    def call(f, *a):
        try:
            return f(*a)
        except Exception as e:
            return ("EXC", repr(e))
    for text, want in ok_cases:
        if call(v, text) != (want, None):
            out.append(u"通るはずの返事が通らない: %s" % text)
    bad_cases = [(u"これは JSON でない", u"JSON でない"), (u"[1, 2]", u"JSON でない"), (good(u"どちらでもない", None), u"読みの語が外"),
                 (good(A, None), u"説明の語が外"), (good(A, u"謎"), u"説明の語が外"), (good(B, u"単位"), u"説明の語が外"), (good(C, u"その他"), u"説明の語が外"),
                 (good(B, None, u" "), u"理由が無い"), (json.dumps({u"読み": B, u"値の違いの説明": None}, ensure_ascii=False), u"理由が無い")]
    for text, kind in bad_cases:
        if call(v, text) != (None, kind):
            out.append(u"外れるはずの返事が %s で外れない: %s" % (kind, text))
    comb = [([A, A, A], (A, True)), ([A, A, B], (A, False)), ([A, B, C], (SPLIT, False)), ([A, A, None], (A, False)), ([A, None, None], (SPLIT, False)),
            ([None, None, None], (SPLIT, False)), ([A, B, None], (SPLIT, False)), ([B, B, B], (B, True)), ([C, B, C], (C, False))]
    for rs, want in comb:
        if call(c, rs) != want:
            out.append(u"combine3(%s) が %s でない" % (rs, want))
    return out


# ----------------------------------------------------------------------------------------------------------------
# (d) E-1〜E-9 の当否
def judge(rec, inp, seal):
    u"""{名前: (実測の字, 当たりか)}。当たりか: True / False / None(判定しない)。"""
    P = seal_predictions(seal)
    c = recount(rec, inp)
    g = rec[u"配線の門"]
    rows = rec[u"行"]
    out = collections.OrderedDict()
    # E-1
    w = [g[k] for k in (u"(1) 行の一致", u"(2) 候補の pointer・value の一致", u"(3) ZIP の sha256", u"(4) 束の sha256")]
    hit = all(x == [NROWS, NROWS] for x in w) and g[u"(1)〜(4) が通った"] is True
    out["E-1"] = (u"(1)〜(4) が %s・%s・%s・%s。script は止まらず記録を書いた: %s" % (n_of(*w[0]), n_of(*w[1]), n_of(*w[2]), n_of(*w[3]), yesno(g[u"(1)〜(4) が通った"])), hit)
    # E-2
    b = re.findall(r"\*\*([^*]+)\*\*", P["E-2"][1])
    r_fail, r_match, r_tool = rng(b[0]), rng(b[1]), rng(b[2])
    hit = within(c["fail_seats"], r_fail) and within(c["match_false"], r_match) and within(c["tools"], r_tool)
    out["E-2"] = (u"返事の検査を通らない席 %d / %d・入力の照合が外れた席 %d(未確認 %d)・道具を使った席 %d" % (c["fail_seats"], NSEATS, c["match_false"], c["match_none"], c["tools"]), hit)
    # E-3
    maj = collections.Counter(c["maj"])
    want3 = [(READINGS[1], bold_after(P["E-3"][1], READINGS[1])), (READINGS[0], bold_after(P["E-3"][1], READINGS[0])),
             (READINGS[2], bold_after(P["E-3"][1], READINGS[2])), (SPLIT, bold_after(P["E-3"][1], SPLIT))]
    outside = [k for k, r_ in want3 if not within(maj.get(k, 0), r_)]
    out["E-3"] = (u"多数決: " + u"・".join(u"%s %d 行" % (k, maj.get(k, 0)) for k, _ in want3) + u"。幅の外: " + (u"・".join(outside) if outside else u"なし"), not outside)
    # E-4
    un = collections.Counter(m for m, u in zip(c["maj"], c["unan"]) if u)
    total = sum(un.values())
    want4 = [(READINGS[1], bold_after(P["E-4"][1], READINGS[1])), (READINGS[0], bold_after(P["E-4"][1], READINGS[0])), (READINGS[2], bold_after(P["E-4"][1], READINGS[2]))]
    outside = [k for k, r_ in want4 if not within(un.get(k, 0), r_)]
    tot_ok = within(total, first_bold(P["E-4"][1]))
    out["E-4"] = (u"全員一致 %d 行(%s)。うち " % (total, u"幅の中" if tot_ok else u"幅の外") + u"・".join(u"%s %d 行" % (k, un.get(k, 0)) for k, _ in want4) + u"。幅の外: " +
                  (u"・".join(outside) if outside else u"なし"), tot_ok and not outside)
    # E-5
    m5 = re.search(r"それぞれ \*\*([^*]+) 行\*\*", P["E-5"][1])
    r5 = rng(m5.group(1))
    gap = rng(re.search(r"\*\*≤ (\d+)\*\*", P["E-5"][1]).group(1))
    oks = [c["okseats"][s] for s in SEATS]
    hit = all(within(x, r5) for x in oks) and max(oks) - min(oks) <= gap[1]
    out["E-5"] = (u"席ごとの『出所として正しい』: " + u"・".join(u"%s %d 行" % (s, c["okseats"][s]) for s in SEATS) + u"。最大と最小の差 %d" % (max(oks) - min(oks)), hit)
    # E-6
    expl = c["expl"]
    nz = sum(expl.values())
    if nz == 0:
        out["E-6"] = (u"『出所として正しい』を選んだ席が 0 席で、説明の語が 0 つ。最多が定まらず、外れ方の『単位が最多』『率 2 席以上』も起こらない(判定しない)", None)
    else:
        top = max(expl.values())
        tops = [k for k, v in expl.items() if v == top]
        r_unit = rng(re.search(r"「単位」は最多でない\*\*\(([^)]+) 席\)", P["E-6"][1]).group(1))
        r_rate = rng(re.search(r"「率」\*\*([^*]+) 席\*\*", P["E-6"][1]).group(1))
        r_sign = rng(re.search(r"「符号」([0-9〜]+) 席", P["E-6"][1]).group(1))
        r_round = rng(re.search(r"「丸め」([0-9〜]+) 席", P["E-6"][1]).group(1))
        hit = (set(tops) <= set([u"その他", u"文の数が違う"]) and within(expl.get(u"単位", 0), r_unit) and within(expl.get(u"率", 0), r_rate)
               and within(expl.get(u"符号", 0), r_sign) and within(expl.get(u"丸め", 0), r_round))
        out["E-6"] = (u"説明(席の数): " + u"・".join(u"%s %d" % (k, expl.get(k, 0)) for k in EXPLANATIONS) + u"。最多: " + u"・".join(tops), hit)
    # E-7
    r7 = rng(re.search(r"\*\*(300〜6,000) 字\*\*", P["E-7"][1]).group(1))
    rf = rng(re.search(r"全文になった行 \*\*([^*]+)\*\*", P["E-7"][1]).group(1))
    lens = [r[u"束"][u"字数"] for r in rows]
    hit = all(within(x, r7) for x in lens) and within(len(c["full"]), rf)
    out["E-7"] = (u"束の字数 %d〜%d(幅の外 %d 本)。段落が全文になった行 %d" % (min(lens), max(lens), sum(1 for x in lens if not within(x, r7)), len(c["full"])), hit)
    # E-8
    r8 = first_bold(P["E-8"][1])
    out["E-8"] = (u"3 席の読みが 3 つとも違う行 %d" % len(c["all3"]), within(len(c["all3"]), r8))
    # E-9
    n_ok = sum(1 for m in c["maj"] if m == READINGS[0])
    n_near = sum(1 for x in c["near"] if x)
    if n_ok == 0:
        out["E-9"] = (u"多数決が『出所として正しい』の行 0(該当なし。外れでも当たりでもない)", None)
    else:
        out["E-9"] = (u"多数決が『出所として正しい』の行 %d、うち帯が 15%% 以内か 10 の冪に近い行 %d" % (n_ok, n_near), n_near * 2 > n_ok)
    return out


def hit_word(b):
    return u"**判定しない**" if b is None else (u"**当たり**" if b else u"**外れ**")


# ----------------------------------------------------------------------------------------------------------------
# (c) 文書の表
def element_of(pointer):
    m = re.match(r"^xbrl:([^:@\s]+):([^@\s]+)@(\S+)$", pointer)
    if not m:
        return u"(形が違う)", u"(形が違う)"
    prefix, name, ctx = m.groups()
    el = name if re.fullmatch(r"jp[a-z]+_cor", prefix) else u"提出者独自"
    base = ctx.split(u"_")[0]
    per = {"CurrentYearDuration": u"当期(期間)", "CurrentYearInstant": u"当期末(時点)"}.get(base, u"(その他の期)")
    return el, per + (u"・区分あり" if u"_" in ctx else u"・区分なし")


def summary_line(rec):
    cs = [combine_ref([seat_reading(r[u"席"][s]) for s in SEATS]) for r in rec[u"行"]]
    maj = set(m for m, _u in cs)
    if len(maj) == 1 and all(u for _m, u in cs) and list(maj)[0] != SPLIT:
        return u"この 10 行の全部で、3 席とも「%s」と読んだ(多数決も全員一致も同じ)。" % list(maj)[0] + NOT_GATED
    return u"席の読みは行によって異なる。行ごとの読みは表 rows のとおり。" + NOT_GATED


INTERP_PREFIX = u"盲検が破れていた 1 回の読みでは、封 §0-2 の意味(この候補は"


def interp_line(rec):
    if summary_line(rec).startswith(u"この 10 行の全部で、3 席とも「%s」" % READINGS[1]):
        return (INTERP_PREFIX + u"、無改変 30 書類の 296 行で、P22 が名指して VALUE_MISMATCH にした fact と全部同じ)に照らすと、読み手はこの 10 行で、"
                u"P22 の名指しも文のその数の出所として正しいとは読まなかった。これは 10 行についての、盲検が破れていた読み手の読みで、候補の良し悪しを決める数ではない。" + NOT_GATED)
    return None


def fact_lines(rec, inp):
    u"""文書に 1 つずつ在るべき、記録から求めた事実の行(散文。数は【門なし】だが、門が字面で照らす)。"""
    c = recount(rec, inp)
    rows = rec[u"行"]
    near15 = sum(1 for r in rows if r[u"診断の帯"][u"帯"] == u"(15% 以内)")
    pow10 = sum(1 for r in rows if r[u"診断の帯"][u"10 の冪に近い"])
    lines = [summary_line(rec)]
    il = interp_line(rec)
    if il is not None:
        lines.append(il)
    lines.append(u"失敗した席は %d 席、入力の照合が外れた席は %d 席、道具を使った席は %d 席、割れた行は %d 行、3 席の読みが 3 つとも違う行は %d 行。"
                 % (c["fail_seats"], c["match_false"], c["tools"], sum(1 for m in c["maj"] if m == SPLIT), len(c["all3"])) + NOT_GATED)
    lines.append(u"この 10 行の診断の帯が「15%% 以内」の行は %d 行、「10 の冪に近い」行は %d 行。" % (near15, pow10) + NOT_GATED)
    return lines


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
    c = recount(rec, inp)
    g = rec[u"配線の門"]
    cc = rec[u"cache"]
    rows = [[k, n_of(*g[k])] for k in (u"(1) 行の一致", u"(2) 候補の pointer・value の一致", u"(3) ZIP の sha256", u"(4) 束の sha256", u"(5) 返事の検査(§2-4)を通った席", u"(6) 入力の照合")]
    rows.append([u"(1)〜(4) が通った(script は記録を書いた)", yesno(g[u"(1)〜(4) が通った"])])
    rows.append([u"cache の前後(edinet・edinet-fresh-2026-10-21)", u"%d・%d から %d・%d(変化なし: %s)" % (cc[u"開始"][u"edinet"][u"件数"], cc[u"開始"][u"edinet-fresh-2026-10-21"][u"件数"],
                                                                                        cc[u"終了"][u"edinet"][u"件数"], cc[u"終了"][u"edinet-fresh-2026-10-21"][u"件数"], yesno(cc[u"変化なし"]))])
    rows.append([u"DEFAULT_PROFILE", rec[u"DEFAULT_PROFILE"]])
    rows.append([u"読んだ行の数・席の数", u"%d 行・%d 席" % (len(rec[u"行"]), len(rec[u"行"]) * 3)])
    for rel in ENGINE_AT_MEASURE:
        rows.append([u"`%s` の sha16" % rel, u"`%s`" % rec[u"engine sha16"][rel]])
    B["wiring"] = table([u"配線の門", u"値"], rows)
    T = expected_tally(rec, inp)
    rows = []
    for k, v in T.items():
        if isinstance(v, dict) and k.startswith(u"席ごとの読みの分布"):
            for s in SEATS:
                rows.append([u"%s・%s" % (k, s), u"・".join(u"%s %d" % (x, v[s][x]) for x in sorted(v[s]))])
        elif isinstance(v, dict):
            rows.append([k, u"・".join(u"%s %s" % (x, v[x]) for x in sorted(v, key=str)) if v else u"なし"])
        elif isinstance(v, list):
            rows.append([k, u"・".join(str(x) for x in v) if v else u"なし"])
        else:
            rows.append([k, v])
    B["tally"] = table([u"集計(封 §2-5)", u"値"], rows)
    rows = []
    for r, m, u in zip(rec[u"行"], c["maj"], c["unan"]):
        el, per = element_of(r[u"候補"][u"pointers"][0])
        rows.append([r[u"位置"], r[u"書類の位置"]] + [r[u"席"][s][u"読み"] or u"失敗" for s in SEATS] +
                    [m, yesno(u), u"%s・%s" % (r[u"診断の帯"][u"帯"], u"10 の冪に近い" if r[u"診断の帯"][u"10 の冪に近い"] else u"10 の冪に近くない"), el, per,
                     r[u"束"][u"字数"], yesno(r[u"束"][u"段落は全文"]), yesno(r[u"束"][u"補いが効いた"])])
    B["rows"] = table([u"位置", u"書類の位置", u"席1", u"席2", u"席3", u"多数決", u"全員一致", u"診断の帯", u"候補の要素", u"候補の期", u"束の字数", u"段落が全文", u"NFKC の補いが効いた"], rows)
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
        return [u"文書の門の表の名前と順が違う: %s" % list(got)]
    for k, lines in B.items():
        if got[k] != lines:
            out.append(u"文書の表『%s』が記録から作った表と違う" % k)
    return out


DOC_LITERALS = (u"読み手の読み", u"正解集合", u"人の目", u"人間の読みではない", u"2026-10-30", u"edinetdb-p27", u"engine は 0 行", u"追記", u"道具が読んだ値と文の数の字が対応しない",
                u"束と返事の理由の自由文", NOT_GATED, u"1 回だけ", u"対照なし", u"盲検は破れていた", u"session_context", u"席が封の commit message を文脈に持っていた", u"--dry-run", u"盲検が破れていた旨を添える")


def check_doc_prose(rec, inp, seal, doc):
    out = []
    stripped = BLOCK_RE.sub(u"", doc)
    if [l for l in stripped.split(u"\n") if l.lstrip().startswith(u"|")]:
        out.append(u"門の外に表の行がある")
    bad = [l[:40] for l in stripped.split(u"\n") if re.search(r"\d+(?:\.\d+)?\s*(?:%|行|件|社|席|書類|試行|回|本|ポイント|USD|file|倍|桁|字|組|つ)", l) and NOT_GATED not in l]
    if bad:
        out.append(u"散文の数に【門なし】の印が無い: %s" % bad)
    heads = re.findall(r"^## (\d+)\.", doc, re.M)
    if heads != [str(i) for i in range(1, len(heads) + 1)] or len(heads) < 6:
        out.append(u"節の番号が 1 から続いていない・6 節に足りない: %s" % heads)
    if u"<!-- 門:start pred -->" not in doc or not (doc.index(u"<!-- 門:start pred -->") < doc.index(u"## 2.")):
        out.append(u"予測の当否が先頭(第 2 節より前)にない")
    J = judge(rec, inp, seal)
    missed = [k for k, v in J.items() if v[1] is False]
    undec = [k for k, v in J.items() if v[1] is None]
    want = u"外れた予測: " + (u"・".join(missed) if missed else u"なし") + u"。外れは外れのまま残す(封も予測も直さない)。" + NOT_GATED
    if sum(1 for l in doc.split(u"\n") if l.strip() == want) != 1:
        out.append(u"『外れた予測』の行が記録から求めた当否と違う(期待: %s)" % want)
    want = u"判定しない予測: " + (u"・".join(undec) if undec else u"なし") + u"。母数が 0 で、封の外れ方の字も起こらない予測は、当たりにも外れにも数えない。" + NOT_GATED
    if sum(1 for l in doc.split(u"\n") if l.strip() == want) != 1:
        out.append(u"『判定しない予測』の行が記録から求めた当否と違う(期待: %s)" % want)
    hits = [k for k, v in J.items() if v[1] is True]
    want = u"当たった予測: " + (u"・".join(hits) if hits else u"なし") + u"。当たりの数を予測の良さの証拠にしない。" + NOT_GATED
    if sum(1 for l in doc.split(u"\n") if l.strip() == want) != 1:
        out.append(u"『当たった予測』の行が記録から求めた当否と違う(期待: %s)" % want)
    for want in fact_lines(rec, inp):
        if sum(1 for l in doc.split(u"\n") if l.strip() == want) != 1:
            out.append(u"記録から求めた事実の行が文書に 1 つだけ無い(期待: %s)" % want)
    n_il = sum(1 for l in doc.split(u"\n") if l.strip().startswith(INTERP_PREFIX))
    if interp_line(rec) is None and n_il:
        out.append(u"全員が『別の出所』でないのに、P22 の名指しの解釈の行がある")
    for lit in DOC_LITERALS:
        if lit not in doc:
            out.append(u"必要な字が無い: %s" % lit)
    for w in FORBIDDEN:
        if w in doc.replace(DECISION_QUOTE, u"司令塔(読み直さない", 1):
            out.append(u"禁止語: %s" % w)
    for w in OVERCLAIM:
        if w in doc:
            out.append(u"言い過ぎ: %s" % w)
    if u"```" in doc:
        out.append(u"code fence がある")
    return out


# ----------------------------------------------------------------------------------------------------------------
# (h) docID・claim の id
def check_h(text, rec, fetched, cand=None, fence=True):
    out = []
    docs = list(fetched[u"使う書類"]) + [r["doc"] for r in rec[u"行"]]
    cids = set(r["id"] for r in rec[u"行"])
    if cand is not None:
        docs += list(cand[u"書類(出てくる順)"])
        cids |= set(r["id"] for r in cand[u"候補の行(P27C。reason が no_same_value か候補が辞書の行)"])
    for d in set(docs):
        if d in text:
            out.append(u"docID の字がある: %s" % d)
    if re.findall(r"S100[0-9A-Z]{4}", text):
        out.append(u"docID らしい字がある")
    if re.findall(r"\b[NT]\d{3}\b", text):
        out.append(u"claim の id らしい字がある")
    for cid in cids:
        if re.search(r"(?<![0-9A-Za-z])%s(?![0-9A-Za-z])" % re.escape(cid), text):
            out.append(u"記録の claim の id の字がある: %s" % cid)
            break
    if fence and u"```" in text:
        out.append(u"code fence がある")
    return out


# ----------------------------------------------------------------------------------------------------------------
# (i) 順序
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


def order_problems(run, prefix, impl, head="HEAD"):
    u"""(i) 実装 ``impl`` < 封の commit < script・記録・文書・門の commit。問題の列 [(符号, 文)]。追跡されていない file は『足した commit が無い』で赤(skip にしない)。"""
    problems = []
    seal = prefix + SEAL_REL
    s_list = added_commits(run, seal)
    if len(s_list) != 1 or not HEX40.match(s_list[0]):
        return [("SEAL_ONCE", u"封を足した commit がちょうど 1 つに決まらない(%d 行)" % len(s_list))]
    S = s_list[0]
    if not is_anc(run, S, head):
        problems.append(("SEAL<=HEAD", u"封の commit が HEAD の祖先でない"))
    if impl is None:
        problems.append(("IMPL_MISSING", u"実装の commit が無い"))
    elif not (impl != S and is_anc(run, impl, S)):
        problems.append(("IMPL_NOT_BEFORE_SEAL", u"封の commit が実装の commit の子孫でない"))
    for name, rel in (("SCRIPT", SCRIPT_REL), ("RECORD", REC_REL), ("DOC", DOC_REL), ("GATE", GATE_REL)):
        lst = added_commits(run, prefix + rel)
        if len(lst) == 0:
            problems.append((name + "_UNCOMMITTED", u"%s がまだ commit されていない(足した commit が無い)" % rel))
        elif len(lst) != 1 or not HEX40.match(lst[0]):
            problems.append((name + "_ONCE", u"%s を足した commit がちょうど 1 つに決まらない(%d 行)" % (rel, len(lst))))
        elif not (lst[0] != S and is_anc(run, S, lst[0])):
            problems.append((name + "_BEFORE_SEAL", u"%s の commit が封の commit より前か同じ" % rel))
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
        self.dir = tempfile.mkdtemp(prefix="candeyes_", dir=base)
        self.run = make_run(self.dir)
        self.impl = None
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


FILES = {"SEAL": SEAL_REL, "IMPL": "adapters/xbrl/verify_document.py", "SCRIPT": SCRIPT_REL, "RECORD": REC_REL, "DOC": DOC_REL, "GATE": GATE_REL}


def build(base, steps):
    u"""steps は 'IMPL' 'SEAL' 'SCRIPT' 'RECORD' 'DOC' 'GATE'(その file を 1 つの commit で足す)と変異の手 'SEAL_REWRITE' 'SEAL_APPEND' 'SEAL_TWICE' 'ALL4'(script・記録・文書・門を 1 commit)。"""
    t = Tmp(base)
    for s in steps:
        if s in FILES:
            t.write(FILES[s], u"# %s\n\n行 1\n行 2\n行 3\n" % s)
            h = t.commit(s, FILES[s])
            if s == "IMPL" and t.impl is None:
                t.impl = h
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
# LATER_NAMING_FILES(fresh_seal の字から読む)
def later_naming_files(src):
    tree = ast.parse(src)
    for n in tree.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "LATER_NAMING_FILES":
            return list(ast.literal_eval(n.value))
    return None


def naming_problems(src):
    got = later_naming_files(src)
    if got is None:
        return [u"LATER_NAMING_FILES が読めない"]
    return [u"LATER_NAMING_FILES に %s が無い" % rel for rel in (REC_REL, SCRIPT_REL, GATE_REL) if rel not in got]


def engine_problem(rel, got, want, declared, added_seal_commits=None):
    u"""sha16 が留めと同じか、宣言された遷移の値であれば None。"""
    if got == want:
        return None
    if rel in declared:
        later, seal_rel = declared[rel]
        if added_seal_commits is not None and not added_seal_commits:
            return u"遷移を宣言した封が履歴に無い"
        return None if got == later else u"宣言された遷移の値とも違う"
    return u"動いている"


# ----------------------------------------------------------------------------------------------------------------
class RecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.inp = inputs()
        cls.seal = jtext(SEAL)

    def test_a_1_the_record_has_the_keys_and_the_ten_rows(self):
        self.assertEqual(check_a(self.rec), [])
        self.assertEqual(len(self.rec[u"行"]), 10)

    def test_b_1_the_wiring_gates_are_recounted(self):
        self.assertEqual(check_b(self.rec, self.inp, self.seal), [])

    def test_b_2_the_record_carries_wiring_one_to_four_as_ten_of_ten_and_the_cache_is_untouched(self):
        g = self.rec[u"配線の門"]
        for k in (u"(1) 行の一致", u"(2) 候補の pointer・value の一致", u"(3) ZIP の sha256", u"(4) 束の sha256"):
            self.assertEqual(g[k], [10, 10], k)
        self.assertEqual(self.rec[u"cache"][u"開始"], self.rec[u"cache"][u"終了"])

    def test_e_1_majority_unanimity_and_the_tally_are_recounted_from_the_seats(self):
        self.assertEqual(check_e(self.rec, self.inp), [])

    def test_e_2_every_reading_is_a_word_of_the_seal_and_explanations_are_only_for_correct(self):
        for r in self.rec[u"行"]:
            for s in SEATS:
                st = r[u"席"][s]
                self.assertIn(st[u"読み"], READINGS)
                if st[u"読み"] != READINGS[0]:
                    self.assertIsNone(st[u"値の違いの説明"])

    def test_j_1_the_inputs_read_are_unchanged(self):
        self.assertEqual(check_j(self.rec), [])

    def test_k_1_the_record_has_no_free_text_span_original_or_bundle_heading(self):
        self.assertEqual(check_k(self.rec), [])
        blob = jtext(REC)
        for key in (u'"理由":', u'"span":', u'"原文":'):
            self.assertNotIn(key, blob)

    def test_k_2_the_record_has_no_bundle_text_but_names_documents_so_it_is_declared(self):
        blob = jtext(REC)
        self.assertTrue(re.search(r"S100[0-9A-Z]{4}", blob))

    def test_l_1_the_ten_rows_are_those_of_the_rule_of_the_seal(self):
        self.assertEqual(check_l(self.rec, self.inp, self.seal), [])

    def test_l_2_the_rule_is_not_a_constant(self):
        rec = copy.deepcopy(self.rec)
        rec[u"行"][0]["id"] = rec[u"行"][1]["id"]
        self.assertNotEqual(check_l(rec, self.inp, self.seal), [])
        rec = copy.deepcopy(self.rec)
        rec[u"行"][3][u"位置"] += 1
        self.assertNotEqual(check_l(rec, self.inp, self.seal), [])
        seal = self.seal.replace(u"**0, 30, 60, 90", u"**1, 30, 60, 90")
        self.assertNotEqual(seal, self.seal)
        self.assertNotEqual(check_l(self.rec, self.inp, seal), [])


class JudgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.inp = inputs()
        cls.seal = jtext(SEAL)

    def test_d_1_judgments_cover_the_nine_predictions(self):
        J = judge(self.rec, self.inp, self.seal)
        self.assertEqual(list(J), ["E-%d" % i for i in range(1, 10)])
        self.assertEqual(list(seal_predictions(self.seal)), list(J))

    def test_d_2_the_judge_is_not_a_constant(self):
        J0 = judge(self.rec, self.inp, self.seal)
        rec = copy.deepcopy(self.rec)
        for s in (u"席1", u"席2"):
            st = rec[u"行"][0][u"席"][s]
            st[u"読み"], st[u"値の違いの説明"] = READINGS[0], u"その他"
        J = judge(rec, self.inp, self.seal)
        self.assertNotEqual(J["E-3"][0], J0["E-3"][0])
        self.assertNotEqual(J["E-5"][0], J0["E-5"][0])
        self.assertIsNotNone(J["E-6"][1])                      # 説明の語が 1 つ出れば判定する
        self.assertTrue(J["E-6"][1])                           # 『その他』が最多で幅の中
        rec = copy.deepcopy(self.rec)
        rec[u"配線の門"][u"(3) ZIP の sha256"] = [9, 10]
        self.assertFalse(judge(rec, self.inp, self.seal)["E-1"][1])
        rec = copy.deepcopy(self.rec)
        rec[u"行"][0][u"席"][u"席2"][u"道具の回数"] = 3
        rec[u"行"][1][u"席"][u"席2"][u"道具の回数"] = 1
        rec[u"行"][2][u"席"][u"席2"][u"道具の回数"] = 1
        self.assertFalse(judge(rec, self.inp, self.seal)["E-2"][1])
        rec = copy.deepcopy(self.rec)
        rec[u"行"][0][u"束"][u"字数"] = 7000
        self.assertFalse(judge(rec, self.inp, self.seal)["E-7"][1])
        rec = copy.deepcopy(self.rec)
        rec[u"行"][0][u"束"][u"段落は全文"] = True
        rec[u"行"][1][u"束"][u"段落は全文"] = True
        self.assertFalse(judge(rec, self.inp, self.seal)["E-7"][1])
        rec = copy.deepcopy(self.rec)
        for k, a in enumerate((READINGS[0], READINGS[1], READINGS[2])):
            st = rec[u"行"][k][u"席"]
            st[u"席1"][u"読み"], st[u"席2"][u"読み"], st[u"席3"][u"読み"] = READINGS
            for s in SEATS:
                st[s][u"値の違いの説明"] = u"その他" if st[s][u"読み"] == READINGS[0] else None
        self.assertFalse(judge(rec, self.inp, self.seal)["E-8"][1])

    def test_d_3_e6_and_e9_judge_when_there_is_something_to_judge(self):
        rec = copy.deepcopy(self.rec)
        for k in range(3):
            for s in SEATS:
                rec[u"行"][k][u"席"][s][u"読み"], rec[u"行"][k][u"席"][s][u"値の違いの説明"] = READINGS[0], u"単位"
        J = judge(rec, self.inp, self.seal)
        self.assertFalse(J["E-6"][1])                          # 『単位』が最多
        self.assertIsNotNone(J["E-9"][1])                      # 多数決が『出所として正しい』の行が在れば判定する
        rec = copy.deepcopy(self.rec)
        for s in SEATS:
            rec[u"行"][0][u"席"][s][u"読み"], rec[u"行"][0][u"席"][s][u"値の違いの説明"] = READINGS[0], u"率"
        self.assertFalse(judge(rec, self.inp, self.seal)["E-6"][1])      # 『率』が 3 席

    def test_d_4_the_misses_and_undecided_are_kept(self):
        J = judge(self.rec, self.inp, self.seal)
        self.assertEqual([k for k, v in J.items() if v[1] is False], MISSES)
        self.assertEqual([k for k, v in J.items() if v[1] is None], UNDECIDED)

    def test_d_5_the_widths_are_read_from_the_seal_text(self):
        seal = self.seal.replace(u"「別の出所」**5〜8 行**", u"「別の出所」**5〜10 行**")
        self.assertNotEqual(seal, self.seal)
        self.assertTrue(within(10, bold_after(seal_predictions(seal)["E-3"][1], READINGS[1])))
        self.assertFalse(within(10, bold_after(seal_predictions(self.seal)["E-3"][1], READINGS[1])))
        self.assertTrue(judge(self.rec, self.inp, seal)["E-3"][0] != judge(self.rec, self.inp, self.seal)["E-3"][0])
        seal = self.seal.replace(u"**5〜8**。うち", u"**5〜10**。うち")
        self.assertNotEqual(seal, self.seal)
        self.assertNotEqual(judge(self.rec, self.inp, seal)["E-4"][0], judge(self.rec, self.inp, self.seal)["E-4"][0])
        seal = self.seal.replace(u"それぞれ **1〜4 行**", u"それぞれ **0〜4 行**")
        self.assertNotEqual(seal, self.seal)
        self.assertTrue(judge(self.rec, self.inp, seal)["E-5"][1])


class EngineTest(unittest.TestCase):
    def test_f_1_engine_sha16_are_pinned_or_declared(self):
        rec = jload(REC)
        self.assertEqual(rec[u"engine sha16"], ENGINE_AT_MEASURE)
        for rel, want in ENGINE_AT_MEASURE.items():
            added = None
            if rel in ENGINE_DECLARED:
                added = git("log", "--diff-filter=A", "--format=%H", "--", ENGINE_DECLARED[rel][1]).stdout.split()
            self.assertIsNone(engine_problem(rel, sha16(rel), want, ENGINE_DECLARED, added), rel)

    def test_f_2_the_declared_transition_form_is_red_for_an_unknown_value(self):
        rel = "adapters/xbrl/vocabulary.py"
        want = ENGINE_AT_MEASURE[rel]
        self.assertIsNone(engine_problem(rel, want, want, {}))
        self.assertIsNotNone(engine_problem(rel, "0" * 16, want, {}))
        self.assertIsNone(engine_problem(rel, "1" * 16, want, {rel: ("1" * 16, "x")}, ["abc"]))
        self.assertIsNotNone(engine_problem(rel, "2" * 16, want, {rel: ("1" * 16, "x")}, ["abc"]))
        self.assertIsNotNone(engine_problem(rel, "1" * 16, want, {rel: ("1" * 16, "x")}, []))

    def test_f_3_the_values_are_what_git_shows_for_the_seal_commit(self):
        for rel, want in ENGINE_AT_MEASURE.items():
            r = subprocess.run(["git", "show", "%s:%s%s" % (SEAL_COMMIT_SHORT, PREFIX, rel)], cwd=REPO, stdout=subprocess.PIPE)
            self.assertEqual(r.returncode, 0, rel)
            self.assertEqual(hashlib.sha256(r.stdout).hexdigest()[:16], want, rel)

    def test_f_4_no_reserved_engine_pin_name_starts_a_line_of_this_file(self):
        src = jtext(os.path.join(ROOT, GATE_REL))
        for line in src.splitlines():
            for name in RESERVED_HEADS:
                self.assertFalse(line.startswith(name), line[:40])
        heads = [l.split(u" = ")[0] for l in src.splitlines() if re.match(r"^[A-Z][A-Z_0-9]* = ", l)]
        self.assertIn("ENGINE_AT_MEASURE", heads)
        self.assertIn("ENGINE_DECLARED", heads)

    def test_f_5_the_registered_profiles_are_as_the_seal_says(self):
        import sys
        sys.path.insert(0, ROOT)
        sys.path.insert(0, os.path.join(ROOT, "core", "py"))
        from adapters.xbrl import vocabulary as V
        self.assertEqual(V.DEFAULT_PROFILE, "P27")
        self.assertTrue(V.PROFILES["P27C"].unnamed_candidate_2026_10_29)
        self.assertFalse(V.PROFILES["P27"].unnamed_candidate_2026_10_29)

    def test_f_6_the_record_engine_fields_are_the_seal_ones(self):
        rec = jload(REC)
        self.assertEqual(rec[u"engine の指紋"][u"adapter_xbrl_py_sha256"][:16], "dc7e35fbfb0f56ca")
        self.assertEqual(rec[u"engine の指紋"][u"adapter_xbrl_py_files"], 16)


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
        P = seal_predictions(self.seal)
        J = judge(self.rec, self.inp, self.seal)
        got = doc_blocks(self.doc)["pred"][2:]
        self.assertEqual(len(got), 9)
        for line, (k, (field, pred, miss)) in zip(got, P.items()):
            cells = [c.strip() for c in line.strip(u"|").split(u" | ")]
            self.assertEqual(cells[0], u"**%s**" % k)
            self.assertEqual(cells[1], field)
            self.assertEqual(cells[2], pred)
            self.assertEqual(cells[3], miss)
            self.assertEqual(cells[5], hit_word(J[k][1]))
        self.assertEqual(render_blocks(self.rec, self.inp, self.seal)["pred"][2:], got)

    def test_h_1_no_docid_and_no_claim_id_in_the_document_and_the_seal(self):
        self.assertEqual(check_h(self.doc, self.rec, self.inp["fetched"], self.inp["cand"]), [])
        self.assertEqual(check_h(self.seal, self.rec, self.inp["fetched"], self.inp["cand"]), [])

    def test_h_2_the_gate_file_has_no_docid(self):
        self.assertEqual(check_h(jtext(os.path.join(ROOT, GATE_REL)), self.rec, self.inp["fetched"], None, fence=False), [])

    def test_doc_states_the_dated_notes(self):
        self.assertIn(u"2026-10-30", self.doc)
        self.assertIn(u"candidate_eyes_2026-10-30.json", self.doc)
        lines = self.doc.split(u"\n")
        for head, needles in ((u"13. ", (u"盲検は破れていた", u"独立監査が見つけた", u"session_context", u"30 とも", u"8,766 字", SEAL_COMMIT_SHORT, u"人間の決定(決定 4 は 1 回だけ)", u"人間 2026-10-30「君に任せる」", u"読み直さない", u"開示つきで残し", u"盲検が破れていた旨を添える", u"読み直しで向きが変わる根拠を示せない", u"この文書を書いた席は理由を読んでいない。司令塔の読みで、数えていない", u"司令塔は席の返事を手渡しで受けて理由を見ており")),
                              (u"14. ", (u"(6) 入力の照合 30 / 30", u"Read の結果の字が file と一致", u"手続きが封どおりでなかった")),
                              (u"15. ", (u"--dry-run", u"validate_reply", u"combine3", u"ast"))):
            hit = [l for l in lines if l.startswith(head)]
            self.assertEqual(len(hit), 1, head)
            for n in needles:
                self.assertIn(n, hit[0], (head, n))
        self.assertEqual(sum(1 for l in lines if u"盲検は破れていた" in l and l.startswith(u"13. ")), 1)

    def test_doc_does_not_say_the_candidate_is_wrong_or_right(self):
        for w in OVERCLAIM:
            self.assertNotIn(w, self.doc)
        self.assertNotIn(u"の側として読む", self.doc)
        self.assertIn(u"側かもしれないが", self.doc)
        self.assertIn(u"席が封の commit message を文脈に持っていた(第 4 節の追記 13)ことの側", self.doc)
        il = interp_line(self.rec)
        self.assertTrue(il.startswith(u"盲検が破れていた"))
        self.assertNotIn(u"\n封 §0-2 の意味(この候補は", self.doc)

    def test_doc_names_the_seal_and_the_reader_as_an_agent(self):
        self.assertIn(u"XBRL_CANDIDATE_EYES_SEAL_2026-10-30.md", self.doc)
        self.assertIn(SEAL_COMMIT_SHORT, self.doc)

    def test_j_2_the_prompt_and_the_wrapper_are_the_blockquotes_of_the_seal(self):
        self.assertEqual(check_prompt(jtext(SCRIPT), self.seal, self.rec), [])
        k = script_consts(jtext(SCRIPT))
        self.assertTrue(k["READER_PROMPT"].startswith(u"あなたは、有価証券報告書"))
        self.assertEqual(len(seal_blockquotes(self.seal)), 2)


class ScriptTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = jtext(SCRIPT)

    def test_script_sha_in_the_record_is_the_script_that_collected(self):
        self.assertEqual(jload(REC)[u"この script の sha256"], sha64(SCRIPT_REL))

    def test_script_imports_no_network_module_and_reads_no_key(self):
        tree = ast.parse(self.src)
        mods = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                mods |= set(a.name.split(".")[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom):
                mods.add((n.module or "").split(".")[0])
        self.assertEqual(mods, set(["__future__", "argparse", "collections", "hashlib", "importlib", "io", "json", "os", "re", "subprocess", "sys", "time", "unicodedata", "adapters"]))
        self.assertFalse([n for n in ast.walk(tree) if isinstance(n, ast.Call) and ast.unparse(n.func) in ("os.getenv", "os.environ.get", "os.environ.__getitem__")])
        self.assertFalse([n for n in ast.walk(tree) if isinstance(n, ast.Subscript) and ast.unparse(n.value) == "os.environ"])

    def test_script_does_not_call_the_raw_injection_harness(self):
        self.assertNotIn(u"work_doc", self.src)

    def test_script_checkers_behave_as_the_seal_says(self):
        self.assertEqual(behaviour_problems(load_checkers(self.src)), [])

    def test_script_checker_mutations_are_red(self):
        muts = [
            (u'READINGS = (u"出所として正しい", u"別の出所", u"文から判断できない")', u'READINGS = (u"出所として正しい", u"別の出所", u"文から判断できな")'),
            (u'    elif e is not None:\n        return None, u"説明の語が外"', u'    elif False:\n        return None, u"説明の語が外"'),
            (u"    if len(ok) < 2:", u"    if len(ok) < 0:"),
            (u"    if len(ok) < 2:", u"    if False:"),
            (u"maj = c[0] if c[1] >= 2 else SPLIT", u"maj = c[0] if c[1] >= 1 else SPLIT"),
            (u"return maj, (len(ok) == 3 and c[1] == 3)", u"return maj, (len(ok) == 3 or c[1] == 3)"),
            (u'    if not isinstance(why, str) or not why.strip():', u'    if not isinstance(why, str):'),
        ]
        for old, new in muts:
            self.assertIn(old, self.src, old)
            self.assertNotEqual(behaviour_problems(load_checkers(self.src.replace(old, new, 1))), [], old)


class FalseRecordsAreRedTest(unittest.TestCase):
    u"""(g) 偽物で赤: 記録の写し・文書・封の写しを 1 か所変えると赤になる。"""

    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.inp = inputs()
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)

    def c(self, rec=None, doc=None, seal=None):
        return check_c(rec or self.rec, self.inp, seal or self.seal, doc or self.doc)

    def test_g_0_baseline_is_green(self):
        self.assertEqual(check_a(self.rec), [])
        self.assertEqual(check_b(self.rec, self.inp, self.seal), [])
        self.assertEqual(check_e(self.rec, self.inp), [])
        self.assertEqual(self.c(), [])
        self.assertEqual(check_k(self.rec), [])
        self.assertEqual(check_l(self.rec, self.inp, self.seal), [])

    def test_g_1_one_seat_reading_turned_to_correct_turns_e_c_and_the_judge_red(self):
        rec = copy.deepcopy(self.rec)
        st = rec[u"行"][0][u"席"][u"席1"]
        st[u"読み"], st[u"値の違いの説明"] = READINGS[0], u"単位"
        self.assertNotEqual(check_e(rec, self.inp), [])              # 全員一致・集計が席から数え直した値と食い違う
        self.assertNotEqual(self.c(rec=rec), [])                     # 文書の表が記録から作った表と違う
        self.assertNotEqual(check_doc_prose(rec, self.inp, self.seal, self.doc), [])
        self.assertNotEqual(judge(rec, self.inp, self.seal)["E-5"][0], judge(self.rec, self.inp, self.seal)["E-5"][0])

    def test_g_2_changing_only_the_majority_field_turns_the_recount_red(self):
        rec = copy.deepcopy(self.rec)
        rec[u"行"][0][u"多数決"] = READINGS[2]
        self.assertNotEqual(check_e(rec, self.inp), [])
        rec = copy.deepcopy(self.rec)
        rec[u"行"][0][u"全員一致"] = False
        self.assertNotEqual(check_e(rec, self.inp), [])
        rec = copy.deepcopy(self.rec)
        rec[u"集計"][u"割れた行"] = 1
        self.assertNotEqual(check_e(rec, self.inp), [])
        rec = copy.deepcopy(self.rec)
        rec[u"集計"][u"多数決の読みごとの行数"][READINGS[1]] = 9
        self.assertNotEqual(check_e(rec, self.inp), [])

    def test_g_3_wiring_five_to_twenty_nine_turns_b_red(self):
        rec = copy.deepcopy(self.rec)
        rec[u"配線の門"][u"(5) 返事の検査(§2-4)を通った席"] = [29, 30]
        self.assertNotEqual(check_b(rec, self.inp, self.seal), [])
        rec = copy.deepcopy(self.rec)
        rec[u"行"][3][u"席"][u"席2"][u"入力の照合"] = False
        self.assertNotEqual(check_b(rec, self.inp, self.seal), [])
        rec = copy.deepcopy(self.rec)
        rec[u"行"][3][u"束"][u"sha256"] = rec[u"行"][4][u"束"][u"sha256"]
        self.assertNotEqual(check_b(rec, self.inp, self.seal), [])
        rec = copy.deepcopy(self.rec)
        rec[u"行"][2][u"候補"][u"値"] += 1
        self.assertNotEqual(check_b(rec, self.inp, self.seal), [])
        self.assertNotEqual(check_l(rec, self.inp, self.seal), [])
        rec = copy.deepcopy(self.rec)
        rec[u"行"][2][u"診断の帯"][u"帯"] = u"(15% 以内)"
        self.assertNotEqual(check_b(rec, self.inp, self.seal), [])

    def test_g_4_one_character_of_the_prediction_judgment_turns_c_red(self):
        doc = self.doc.replace(u"| **外れ** |", u"| **当たり** |", 1)
        self.assertNotEqual(doc, self.doc)
        self.assertNotEqual(self.c(doc=doc), [])
        self.assertNotEqual(check_doc_prose(self.rec, self.inp, self.seal, self.doc.replace(u"外れた予測: E-3・E-4・E-5", u"外れた予測: E-3・E-4")), [])

    def test_g_5_one_character_of_a_table_turns_c_red(self):
        for name in ("wiring", "tally", "rows"):
            doc = self.doc
            i = doc.index(u"<!-- 門:start %s -->" % name)
            j = doc.index(u"|", doc.index(u"\n|", i) + 1)
            k = [m.start() for m in re.finditer(r"\d", doc[j:])][0] + j
            bad = doc[:k] + (u"9" if doc[k] != u"9" else u"8") + doc[k + 1:]
            self.assertNotEqual(self.c(doc=bad), [], name)

    def test_g_6_one_character_of_a_seal_width_turns_d_and_c_red(self):
        seal = self.seal.replace(u"「出所として正しい」**1〜4 行**", u"「出所として正しい」**0〜4 行**", 1)
        self.assertNotEqual(seal, self.seal)
        self.assertNotEqual(self.c(seal=seal), [])
        self.assertNotEqual(judge(self.rec, self.inp, seal)["E-3"][0], judge(self.rec, self.inp, self.seal)["E-3"][0])
        seal = self.seal.replace(u"| **E-8** 3 席", u"| **E-8** 4 席", 1)
        self.assertNotEqual(self.c(seal=seal), [])

    def test_g_7_a_docid_or_a_claim_id_in_the_document_turns_h_red(self):
        d0 = self.rec[u"行"][0]["doc"]
        c0 = self.rec[u"行"][0]["id"]
        self.assertNotEqual(check_h(self.doc + u"\n" + d0 + u"\n", self.rec, self.inp["fetched"], self.inp["cand"]), [])
        self.assertNotEqual(check_h(self.doc + u"\n" + c0 + u"\n", self.rec, self.inp["fetched"], self.inp["cand"]), [])
        self.assertNotEqual(check_h(self.doc + u"\n```\n", self.rec, self.inp["fetched"], self.inp["cand"]), [])
        self.assertNotEqual(check_h(self.doc + u"\nS100" + u"ABCD\n", self.rec, self.inp["fetched"], self.inp["cand"]), [])

    def test_g_8_one_character_of_the_prompt_turns_j_red(self):
        src = jtext(SCRIPT)
        bad = src.replace(u"問いは「示された fact は、", u"問いは「示された fact が、", 1)
        self.assertNotEqual(bad, src)
        self.assertNotEqual(check_prompt(bad, self.seal, self.rec), [])
        bad = src.replace(u"決まり: 渡した材料", u"決まり: 渡された材料", 1)
        self.assertNotEqual(check_prompt(bad, self.seal, self.rec), [])
        bad = src.replace(u"POSITIONS = (0, 30,", u"POSITIONS = (1, 30,", 1)
        self.assertNotEqual(check_prompt(bad, self.seal, self.rec), [])
        seal = self.seal.replace(u"> 次の 3 つから 1 つを選んでください。", u"> 次の 3 つから 1 つ選んでください。", 1)
        self.assertNotEqual(seal, self.seal)
        self.assertNotEqual(check_prompt(src, seal, self.rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"指示文と包み"][u"指示文の sha256"] = u"0" * 64
        self.assertNotEqual(check_prompt(src, self.seal, rec), [])

    def test_g_9_a_reason_key_or_a_bundle_heading_in_the_record_turns_k_red(self):
        rec = copy.deepcopy(self.rec)
        rec[u"行"][0][u"席"][u"席1"][u"理由"] = u"x"
        self.assertNotEqual(check_k(rec), [])
        self.assertNotEqual(check_a(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"行"][0][u"候補の字"] = u"## 1 文の段落"
        self.assertNotEqual(check_k(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"行"][0][u"束"][u"span"] = u"x"
        self.assertNotEqual(check_k(rec), [])
        rec = copy.deepcopy(self.rec)
        rec[u"注意"] = u"あ" * 401
        self.assertNotEqual(check_k(rec), [])

    def test_g_10_removing_the_record_from_the_naming_declaration_is_red(self):
        src = jtext(os.path.join(ROOT, FRESH_SEAL_REL))
        self.assertEqual(naming_problems(src), [])
        for rel in (REC_REL, SCRIPT_REL, GATE_REL):
            bad = src.replace(u'"%s"' % rel, u'"x/%s"' % os.path.basename(rel), 1)
            self.assertNotEqual(bad, src, rel)
            self.assertNotEqual(naming_problems(bad), [], rel)

    def test_g_11_an_unmarked_number_or_a_forbidden_phrase_in_prose_turns_the_prose_check_red(self):
        for add in (u"\n席は 30 席だった。\n", u"\n候補は誤りだった。【門なし】\n", u"\n次の封を勧めする。【門なし】\n", u"\n精度が高い。【門なし】\n", u"\n| 表 | 行 |\n"):
            self.assertNotEqual(check_doc_prose(self.rec, self.inp, self.seal, self.doc + add), [], add)

    def test_g_12_the_summary_line_follows_the_record(self):
        rec = copy.deepcopy(self.rec)
        rec[u"行"][0][u"席"][u"席3"][u"読み"] = READINGS[2]
        self.assertNotEqual(summary_line(rec), summary_line(self.rec))
        self.assertIsNone(interp_line(rec))
        self.assertIsNotNone(interp_line(self.rec))
        self.assertNotEqual(check_doc_prose(rec, self.inp, self.seal, self.doc), [])

    def test_g_13_changing_the_input_sha_turns_j_red(self):
        rec = copy.deepcopy(self.rec)
        rec[u"読んだ入力の sha256"][UNNAMED_REL] = u"0" * 64
        self.assertNotEqual(check_j(rec), [])
        rec = copy.deepcopy(self.rec)
        del rec[u"読んだ入力の sha256"][ROSTER_REL]
        self.assertNotEqual(check_j(rec), [])

    def test_g_14_the_engine_pin_is_red_for_one_character(self):
        rec = copy.deepcopy(self.rec)
        rel = "adapters/xbrl/recipes.py"
        rec[u"engine sha16"][rel] = rec[u"engine sha16"][rel][:-1] + (u"0" if rec[u"engine sha16"][rel][-1] != u"0" else u"1")
        self.assertNotEqual(rec[u"engine sha16"], ENGINE_AT_MEASURE)
        self.assertIsNotNone(engine_problem(rel, rec[u"engine sha16"][rel], ENGINE_AT_MEASURE[rel], {}))


class OrderTest(unittest.TestCase):
    u"""(i) 実装 < 封の commit < script・記録・文書・門の commit。"""

    @classmethod
    def setUpClass(cls):
        cls.base = tempfile.mkdtemp(prefix="candeyes_root_")
        cls.grun = staticmethod(make_run(REPO))

    def _p(self, steps):
        t = build(self.base, steps)
        return order_problems(t.run, "", t.impl)

    def test_i_1_the_real_history_has_the_implementation_before_the_seal_before_the_files(self):
        u"""script・記録・文書・門のどれかが未 commit なら赤(足した commit が無い)。全部 commit された後で初めて緑。"""
        rc, impl = self.grun("rev-parse", IMPL_COMMIT_SHORT + "^{commit}")
        self.assertEqual(rc, 0)
        self.assertEqual(order_problems(self.grun, PREFIX, impl), [])

    def test_i_2_the_real_seal_is_one_commit_after_the_implementation_and_an_ancestor_of_head(self):
        lst = added_commits(self.grun, PREFIX + SEAL_REL)
        self.assertEqual(len(lst), 1)
        self.assertTrue(lst[0].startswith(SEAL_COMMIT_SHORT))
        self.assertTrue(is_anc(self.grun, lst[0], "HEAD"))
        rc, impl = self.grun("rev-parse", IMPL_COMMIT_SHORT + "^{commit}")
        self.assertTrue(is_anc(self.grun, impl, lst[0]))
        rc, decl = self.grun("rev-parse", DECL_COMMIT_SHORT + "^{commit}")
        self.assertEqual(rc, 0)
        self.assertTrue(is_anc(self.grun, decl, lst[0]))

    def test_i_3_a_correct_order_is_green(self):
        self.assertEqual(self._p(["IMPL", "SEAL", "SCRIPT", "RECORD", "DOC", "GATE"]), [])
        self.assertEqual(self._p(["IMPL", "SEAL", "ALL4"]), [])
        self.assertEqual(self._p(["IMPL", "SEAL", "ALL4", "SEAL_APPEND"]), [])

    def test_i_4_a_file_before_the_seal_is_red(self):
        for first in ("SCRIPT", "RECORD", "DOC", "GATE"):
            steps = ["IMPL", first, "SEAL"] + [k for k in ("SCRIPT", "RECORD", "DOC", "GATE") if k != first]
            self.assertIn(first + "_BEFORE_SEAL", codes(self._p(steps)), first)

    def test_i_5_an_uncommitted_file_is_red_not_skipped(self):
        self.assertIn("GATE_UNCOMMITTED", codes(self._p(["IMPL", "SEAL", "SCRIPT", "RECORD", "DOC"])))
        self.assertIn("SCRIPT_UNCOMMITTED", codes(self._p(["IMPL", "SEAL"])))
        self.assertIn("RECORD_UNCOMMITTED", codes(self._p(["IMPL", "SEAL", "SCRIPT", "DOC", "GATE"])))
        self.assertIn("DOC_UNCOMMITTED", codes(self._p(["IMPL", "SEAL", "SCRIPT", "RECORD", "GATE"])))

    def test_i_6_the_seal_missing_or_added_twice_is_red(self):
        self.assertIn("SEAL_ONCE", codes(self._p(["IMPL", "ALL4"])))
        self.assertIn("SEAL_ONCE", codes(self._p(["IMPL", "SEAL", "ALL4", "SEAL_TWICE"])))

    def test_i_7_rewriting_the_seal_after_the_fact_is_red(self):
        self.assertIn("SEAL_REWRITE", codes(self._p(["IMPL", "SEAL", "ALL4", "SEAL_REWRITE"])))

    def test_i_8_the_same_commit_as_the_seal_is_red(self):
        t = Tmp(self.base)
        t.write(FILES["IMPL"], u"# IMPL\n")
        t.impl = t.commit("impl", FILES["IMPL"])
        for k in ("SEAL", "SCRIPT", "RECORD", "DOC", "GATE"):
            t.write(FILES[k], u"# %s\n" % k)
        t.commit("all", *[FILES[k] for k in ("SEAL", "SCRIPT", "RECORD", "DOC", "GATE")])
        self.assertIn("SCRIPT_BEFORE_SEAL", codes(order_problems(t.run, "", t.impl)))

    def test_i_9_the_seal_before_the_implementation_is_red(self):
        self.assertIn("IMPL_NOT_BEFORE_SEAL", codes(self._p(["SEAL", "IMPL", "ALL4"])))
        t = build(self.base, ["IMPL", "SEAL", "ALL4"])
        self.assertIn("IMPL_MISSING", codes(order_problems(t.run, "", None)))


if __name__ == "__main__":
    unittest.main()
