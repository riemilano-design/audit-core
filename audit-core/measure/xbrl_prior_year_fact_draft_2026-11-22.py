# -*- coding: utf-8 -*-
u"""封 docs/XBRL_PRIOR_YEAR_FACT_DRAFT_SEAL_2026-11-22.md(XZ0 ― 同じ会社の前の年の提出書類の「表の中の置き場 → 数の fact の属性」を今年の下書きに使うと、今年の数の fact の要素・文脈・単位はどれだけ決まり、どれだけ黙って違うか)の測定。
**0 USD。LLM の席は呼ばない。鍵は使わない。通信しない。** engine(``core/``・``adapters/``)は 1 行も変えない。行の切り方(``_TR_RE``・``_row_label``)は engine の関数を呼ぶ。
便 XY0 の script の関数(組の作り方 ``make_pairs``)と、そこから届く便 XG1 の関数(見出しつきの行の切り方 ``file_rows``・書類の字の読み取り ``doc_texts``)と便 XG0 の関数(書類の選び方・記録の検査の部品)は importlib で読んで呼ぶ(写さない)。

    python3 measure/xbrl_prior_year_fact_draft_2026-11-22.py            # 置き場から数えて記録 fixtures/xbrl/cd8/prior_year_fact_draft_2026-11-22.json を排他で書く。通信しない
    python3 measure/xbrl_prior_year_fact_draft_2026-11-22.py --check    # 置き場から数え直して記録と照らす。通信しない

置き場の既定は封の字(今年の側 ``~/.cache/audit-core/edinet/``・前の年の側 ``~/.cache/audit-core/edinet-prior-2026-11-02/``)。標準ラベル・標準タクソノミ・提出者の linkbase は使わない。
**前の年の側は ``_ixbrl.htm`` だけを読む。今年の fact の属性は、類分けにだけ使い、候補(表 HT・表 H・段 HT・段 H・段 F)の作りには渡さない。**

実装の注(封の字では 1 通りに決まらなかった所の決め。実装より先に決め、結果を見て変えない。報告にも書く):
- 見出しが無い行の h は ``None``(「無し」同士で当たる。実在の見出しの字と取り違えない)。見出しの字が ``norm_label`` で空になる行の h は空の字(``None`` と別)。
- 表の通し番号は、その行の始まりの位置より前に始まる ``<table`` の開きタグ(``\\b`` 付き・大文字小文字を問わない)の数。th は同じ file の中の同じ h の行(fact の有無を問わない全部の行)の、表の通し番号の出た順の番号。
- 数の fact の開きタグは ``<ix:nonFraction\\b[^>]*>``(大文字小文字を問わない)。属性は ``名="値"`` の字そのまま(無ければ ``None``)。空の欄は ``xsi:nil`` の値が ``true`` の fact。
- セルの番号 td は、行の字の中で fact の開きタグより前に在る ``<td`` と ``<th`` の開きタグ(``\\b`` 付き)の数。
- 行の字 T は ``_row_label`` の返りに ``norm_label`` を掛けた字。空の行は類 X(分母に入る)で、前の年の表には入れない。
- 束 3 の「空の欄でない fact だけの分母で数え直した率」(XZ0-6)は、表は束 3 のまま(空の欄を含む全部の fact から作る)で、今年の側の分母だけを空の欄でない fact にする。
- 属性ごとの候補は、束 3 の候補の集まりを 1 つの属性へ射影した集まり(表を 1 つの属性で作り直した集まりと同じ)。
- 行の外の fact の数: file の中の開きタグの全部の数から、行の中の開きタグの数を引く(書類ごとの合計)。
- 率は四捨五入(0.5 は上げる)で小数第 1 位。判定に要る数は丸める前の整数も書く。
"""
from __future__ import print_function

import argparse
import bisect
import collections
import hashlib
import importlib.util
import io
import json
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)

from adapters.xbrl import instance as I                 # noqa: E402
from adapters.xbrl import verify_document as VD         # noqa: E402


def _load_prior():
    u"""便 XY0 の script を、他と重ならない一意の名で読む(関数は呼ぶだけ。写さない)。便 XY0 の script が便 XG1・XG0 の script を読む。"""
    name = "_xz0_prior_year_draft_2026_11_22"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, "xbrl_prior_year_draft_2026-11-22.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


Y = _load_prior()
N = Y.N
W = Y.W

SEAL_REL = "docs/XBRL_PRIOR_YEAR_FACT_DRAFT_SEAL_2026-11-22.md"
SEAL_COMMIT = "4ee140d2"
SCRIPT_REL = "measure/xbrl_prior_year_fact_draft_2026-11-22.py"
RECORD_REL = "fixtures/xbrl/cd8/prior_year_fact_draft_2026-11-22.json"
DOCS_DIR = Y.DOCS_DIR
PRIOR_DIR = Y.PRIOR_DIR

# ---- 封 §1・§2・§4 の決めごと(字で留める。封の門が封の字と照らす)
DOCS_WANT = Y.DOCS_WANT
PAIRS_WANT = 63
CLASSES = ("X", "U", "A", "W1", "W2", "N")
STAGES = ("HT", "H", "F")
ATTRS3 = ("name", "contextRef", "unitRef")
ATTRS5 = ATTRS3 + ("decimals", "scale")
NIL_ATTR = "xsi:nil"
BUNDLE_KEYS = ("b3", "b5", "name", "ctx", "unit", "b3nn")      # 束 3・束 5・属性ごと 3 つ・束 3(空の欄でない fact の分母)
#: 記録の欄の名(``name`` だけの欄は記録の禁止の欄に当たるので、字を足す)
RECORD_LABELS = {"b3": u"束 3", "b5": u"束 5", "name": u"属性 name だけ", "ctx": u"属性 contextRef だけ", "unit": u"属性 unitRef だけ", "b3nn": u"束 3(空の欄でない fact の分母)"}
U_DOC_HI_PCT = 95
U_DOC_LO_PCT = 80
#: 封 §4 の予測の境(記録には判定を書かない。封の門が封の表と照らす)。XZ0-1〜3・6 は (下限, 上限) の % か None。
#: XZ0-4 は (段 F の U が段 HT より高い下限のポイント, 段 F の W1 の上限 %)・XZ0-5 は (段 H の U が段 HT より低い下限のポイント)・XZ0-6 は (差の下限のポイント)・
#: XZ0-7 は 0(contextRef の U の率は name の U の率以上)・XZ0-8 は (95% 以上の書類の本数の上限, 80% 以上の書類の本数の下限, 同上限)
BOUNDS = collections.OrderedDict([
    ("XZ0-1", (70, 86)), ("XZ0-2", (None, 2.5)), ("XZ0-3", (6, 20)), ("XZ0-4", (1, 3.5)), ("XZ0-5", (15,)), ("XZ0-6", (-2,)), ("XZ0-7", (0,)), ("XZ0-8", (3, 20, 50))])
#: 封 §4 の「先に自分の欠陥を疑う場合」(止めず、記録に旗の欄として書く)。(欄の字, 比べる %)
FLAG_HT_U_OVER = 95
FLAG_HT_N_OVER = 30
FLAG_NAME_U_UNDER = 70
FLAG_OUTSIDE_OVER = 5
LIMITS = [
    u"どのセルに fact を置くか(今年の側の fact の置き場)は答えから取っている。この便が測るのは「置き場が分かっているとき、属性が前の年から決まるか」で、「どのセルが fact か」は測っていない。分母も今年の答えの fact。",
    u"前の年の書類も今年の書類も、専用の道具が組んだ後の字。同じ道具・同じ会社が 2 年続けて組んだものなので、見出し・表の並び・行の字・セルの並びが揃いやすい。原稿(Word・Excel)での率は測れない。この便の U は「上の限り」に近い読み。",
    u"文脈は contextRef の字(名)で比べる。名が同じでも、その定義(期・軸・メンバー)が 2 つの年で同じ形かは見ていない。",
    u"sign・format・空の欄か・値は引き継がない(測らない)。decimals・scale は空の欄でない fact でだけ測る。数でない fact(ix:nonNumeric)・脚注・表示の並び・計算の関係・提出者別タクソノミの file は測っていない。",
    u"前の年の XBRL が在る会社にしか使えない。前の年に置き場が無かった fact(N)は道具がいちばん要る所で、この便はそこを決めない。",
    u"63 組は無作為ではない。業種はほぼ一般商工業。年は 1 組(1 年の差)だけ。有報だけ。",
    u"「XBRL を作れる」「EDINET の検査に通る」「専用の道具が要らない」「AI が書ける」は、この便からは言えない。"]

Stop = W.Stop
od = collections.OrderedDict
sha256_bytes = W.sha256_bytes
sha256_file = W.sha256_file
dumps = W.dumps
pct1 = W.pct1
norm_label = W.norm_label
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

FACT_RE = re.compile(r"<ix:nonFraction\b[^>]*>", re.I)
ATTR_RE = re.compile(r'([^\s=/>"\']+)\s*=\s*"([^"]*)"')
TABLE_RE = re.compile(r"<table\b", re.I)
CELL_RE = re.compile(r"<t[dh]\b", re.I)


# ======================================================================================================
# 行・fact・鍵の部品(封 §2・§3)
def parse_attrs(tag):
    u"""fact の開きタグ → {属性の名: 値}(字そのまま。同じ名が 2 度出たら先の方)。"""
    out = {}
    for k, v in ATTR_RE.findall(tag):
        out.setdefault(k, v)
    return out


def is_nil(attrs):
    return attrs.get(NIL_ATTR) == "true"


def bundle3(attrs):
    return tuple(attrs.get(k) for k in ATTRS3)


def bundle5(attrs):
    return tuple(attrs.get(k) for k in ATTRS5)


def read_rows(text):
    u"""file の字 → ([(h, th, T, [(td, 属性の辞書)])], 行の外の fact の数)。行は engine の ``_TR_RE`` の全部(``file_rows`` と 1 対 1。違えば止まる)。
    h は見出しの字に ``norm_label`` を掛けたもの(見出しが無ければ ``None``)・th は同じ file の中の同じ h の行の、表の通し番号の出た順の番号・T は行の字に ``norm_label``(無ければ空の字)。"""
    matches = list(I._TR_RE.finditer(text))
    frows = N.file_rows(text)
    if len(matches) != len(frows) or any(m.group(0) != fr[0] for m, fr in zip(matches, frows)):
        raise Stop(u"**行の切り方が便 XG1 の file_rows と 1 対 1 でない。止める**")
    starts = [m.start() for m in TABLE_RE.finditer(text)]
    seen = {}
    out = []
    inside = 0
    for m, (rowtext, head) in zip(matches, frows):
        h = norm_label(head) if head is not None else None
        serial = bisect.bisect_left(starts, m.start())
        ranks = seen.setdefault(h, {})
        if serial not in ranks:
            ranks[serial] = len(ranks)
        th = ranks[serial]
        label = I._row_label(rowtext)
        T = norm_label(label) if label else u""
        facts = []
        for fm in FACT_RE.finditer(rowtext):
            td = len(CELL_RE.findall(rowtext[:fm.start()]))
            facts.append((td, parse_attrs(fm.group(0))))
        inside += len(facts)
        out.append((h, th, T, facts))
    return out, len(FACT_RE.findall(text)) - inside


def texts_rows(texts):
    u"""[(file 名, 字)] → (行の並び(file 名の昇順)・行の外の fact の数の合計)。"""
    rows, outside = [], 0
    for _n, text in sorted(texts, key=lambda q: q[0]):
        r, o = read_rows(text)
        rows.extend(r)
        outside += o
    return rows, outside


# ======================================================================================================
# 表・段・類(封 §2-4〜7)
def build_tables(rows, secret=None):
    u"""前の年の側の行の並び → {"HT3": 表 HT(束 3)・"H3": 表 H(束 3)・"HT5"・"H5"(空の欄でない fact だけ)}。T が空の行は入れない。"""
    tabs = dict((k, {}) for k in ("HT3", "H3", "HT5", "H5"))
    for h, th, T, facts in rows:
        if secret is not None:
            for _td, a in facts:
                secret[1].add((a.get("name") or u"").split(":")[-1])
                secret[1].add(a.get("contextRef") or u"")
                secret[1].add(a.get("unitRef") or u"")
        if not T:
            continue
        for td, a in facts:
            b3 = bundle3(a)
            tabs["HT3"].setdefault((h, th, T, td), set()).add(b3)
            tabs["H3"].setdefault((h, T, td), set()).add(b3)
            if not is_nil(a):
                b5 = bundle5(a)
                tabs["HT5"].setdefault((h, th, T, td), set()).add(b5)
                tabs["H5"].setdefault((h, T, td), set()).add(b5)
        if secret is not None:
            secret[0].add(T)
            if h:
                secret[4].add(h)
    return tabs


def stage_ht(tab, h, th, T, td):
    u"""段 HT: 表 HT の候補(今年の fact の属性は渡さない)。"""
    return set(tab.get((h, th, T, td), ()))


def stage_h(tab, h, T, td):
    u"""段 H: 表 H の候補。"""
    return set(tab.get((h, T, td), ()))


def stage_f(c_ht, c_h):
    u"""段 F: 段 HT の候補が 1 つ以上なら段 HT の候補。空なら段 H の候補。"""
    if c_ht:
        return set(c_ht)
    return set(c_h)


def classify6(value, cands):
    u"""類 U・A・W1・W2・N(封 §2-7。X は行の字が空の fact で、呼ぶ側が決める)。"""
    if not cands:
        return "N"
    if value not in cands:
        return "W1" if len(cands) == 1 else "W2"
    return "U" if len(cands) == 1 else "A"


def project(cands, i):
    return set(b[i] for b in cands)


def new_cells():
    return od((b, od((s, od((c, 0) for c in CLASSES)) for s in STAGES)) for b in BUNDLE_KEYS)


def new_doc():
    return od([("rows", 0), ("facts", 0), ("nil", 0), ("outside", 0), ("C", new_cells()), ("fall", 0), ("fallc", od((c, 0) for c in CLASSES))])


def count_pair(cur_texts, prior_texts, secret=None):
    u"""組 1 つ(今年の側・前の年の側の [(file 名, 字)])を数える。今年の fact の属性は類分けにだけ使い、候補の作りには渡さない。"""
    cur_rows, outside = texts_rows(cur_texts)
    prior_rows, _o = texts_rows(prior_texts)
    tabs = build_tables(prior_rows, secret)
    acc = new_doc()
    acc["rows"] = len(cur_rows)
    acc["outside"] = outside
    for h, th, T, facts in cur_rows:
        for td, a in facts:
            nil = is_nil(a)
            if secret is not None:
                secret[1].add((a.get("name") or u"").split(":")[-1])
                secret[1].add(a.get("contextRef") or u"")
                secret[1].add(a.get("unitRef") or u"")
            acc["facts"] += 1
            if nil:
                acc["nil"] += 1
            if not T:
                for b in BUNDLE_KEYS:
                    if b in ("b5", "b3nn") and nil:
                        continue
                    for s in STAGES:
                        acc["C"][b][s]["X"] += 1
                continue
            ht3 = stage_ht(tabs["HT3"], h, th, T, td)
            h3 = stage_h(tabs["H3"], h, T, td)
            by_stage3 = {"HT": ht3, "H": h3, "F": stage_f(ht3, h3)}
            b3 = bundle3(a)
            for s in STAGES:
                acc["C"]["b3"][s][classify6(b3, by_stage3[s])] += 1
                if not nil:
                    acc["C"]["b3nn"][s][classify6(b3, by_stage3[s])] += 1
                for i, key in enumerate(("name", "ctx", "unit")):
                    acc["C"][key][s][classify6(b3[i], project(by_stage3[s], i))] += 1
            if not ht3:
                acc["fall"] += 1
                acc["fallc"][classify6(b3, by_stage3["F"])] += 1
            if not nil:
                ht5 = stage_ht(tabs["HT5"], h, th, T, td)
                h5 = stage_h(tabs["H5"], h, T, td)
                by_stage5 = {"HT": ht5, "H": h5, "F": stage_f(ht5, h5)}
                b5 = bundle5(a)
                for s in STAGES:
                    acc["C"]["b5"][s][classify6(b5, by_stage5[s])] += 1
        if secret is not None:
            secret[0].add(T)
            if h:
                secret[4].add(h)
    return acc


def add_into(tot, acc):
    for k in ("rows", "facts", "nil", "outside", "fall"):
        tot[k] += acc[k]
    for b in BUNDLE_KEYS:
        for s in STAGES:
            for c in CLASSES:
                tot["C"][b][s][c] += acc["C"][b][s][c]
    for c in CLASSES:
        tot["fallc"][c] += acc["fallc"][c]


def totals(accs):
    tot = new_doc()
    for a in accs:
        add_into(tot, a)
    return tot


def rate_of(n, d):
    return od([(u"fact", n), (u"分母", d), (u"%", pct1(n, d))])


def diff_points(n1, d1, n2, d2):
    u"""n1/d1 − n2/d2 のポイント(小数第 1 位)。"""
    if not d1 or not d2:
        return None
    return pct1(n1 * d2 - n2 * d1, d1 * d2)


def doc_u_rate_ge(u, d, pct):
    return bool(d) and 100 * u >= pct * d


# ======================================================================================================
# 記録
def cells_out(cells):
    return od((RECORD_LABELS[b], od((s, od(cells[b][s])) for s in STAGES)) for b in BUNDLE_KEYS)


def build_record(docs_dir=None, prior_dir=None, want_docs=DOCS_WANT, want_pairs=PAIRS_WANT):
    u"""置き場 → (記録, 漏れの検査に使う材料)。書かない。"""
    docs, pairs, excluded = Y.make_pairs(docs_dir or DOCS_DIR, prior_dir or PRIOR_DIR, want_docs, want_pairs)
    fp = VD.engine_fingerprint()
    secret = (set(), set(), [d[0] for d in docs] + [p[3] for p in pairs], set(p[5] for p in pairs), set(), set())
    for _stem, _p, xs in docs:
        for x in xs:
            secret[3].update(re.findall(r"E\d{5}", x))
    accs, rows_out = [], []
    docs_hi = docs_lo = docs_with_facts = 0
    for n, stem, p, pstem, pp, code in pairs:
        with zipfile.ZipFile(p) as z:
            cur = N.doc_texts(z)
        with zipfile.ZipFile(pp) as z:
            prv = N.doc_texts(z)
        acc = count_pair(cur, prv, secret)
        accs.append(acc)
        u_ht = acc["C"]["b3"]["HT"]["U"]
        f = acc["facts"]
        if f:
            docs_with_facts += 1
            if doc_u_rate_ge(u_ht, f, U_DOC_HI_PCT):
                docs_hi += 1
            if doc_u_rate_ge(u_ht, f, U_DOC_LO_PCT):
                docs_lo += 1
        rows_out.append(od([
            (u"番号", n), (u"行の数", acc["rows"]), (u"行の中の数の fact の数", f), (u"空の欄の fact の数", acc["nil"]), (u"行の外の fact の数", acc["outside"]),
            (u"束と段ごとの類別", cells_out(acc["C"])),
            (u"段 F で段 H へ落ちた fact の数", acc["fall"]), (u"段 F で段 H へ落ちた fact の類別(束 3)", od(acc["fallc"])),
            (u"段 HT・束 3 の U の率(%)", pct1(u_ht, f))]))
    tot = totals(accs)
    D = tot["facts"]
    NN = D - tot["nil"]
    C = tot["C"]
    b3 = C["b3"]
    rec = od()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"XZ0(同じ会社の前の年の提出書類の「表の中の置き場 → 数の fact の属性」を今年の下書きに使うと、今年の数の fact の要素・文脈・単位はどれだけ決まり、どれだけ黙って違うか)(0 USD・engine は 0 行)"
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"engine の指紋"] = od((k, fp[k]) for k in ("adapter_xbrl_py_sha256", "adapter_xbrl_py_files", "core_py_sha256", "core_py_files"))
    rec[u"材料"] = od([
        (u"今年の側の書類の本数", len(docs)),
        (u"今年の側の書類の file 名の並びの sha256", W.order_sha256([d[0] for d in docs])),
        (u"組の数", len(pairs)),
        (u"除いた今年の書類の数", excluded),
        (u"前の年の側の組の相手の file 名の並びの sha256", sha256_bytes(u"\n".join(p[3] for p in pairs).encode("utf-8")))])
    rec[u"書類"] = rows_out
    rec[u"集計"] = od([
        (u"行の数", tot["rows"]), (u"行の中の数の fact の数", D), (u"空の欄の fact の数", tot["nil"]), (u"空の欄でない fact の数", NN), (u"行の外の fact の数", tot["outside"]),
        (u"束と段ごとの類別", cells_out(C)),
        (u"段 F で段 H へ落ちた fact の数", tot["fall"]), (u"段 F で段 H へ落ちた fact の類別(束 3)", od(tot["fallc"])),
        (u"fact が 1 つ以上在る書類の数", docs_with_facts)])
    rec[u"先に自分の欠陥を疑う旗(止めない。当たり外れではない)"] = od([
        (u"段 HT・束 3 の U が %d%% を超えた(前の年の側として今年の書類を読んでいないか)" % FLAG_HT_U_OVER,
         od([(u"fact", b3["HT"]["U"]), (u"分母", D), (u"旗", 100 * b3["HT"]["U"] > FLAG_HT_U_OVER * D)])),
        (u"段 HT・束 3 の N が %d%% を超えた(見出しか表の番号の取り違えか)" % FLAG_HT_N_OVER,
         od([(u"fact", b3["HT"]["N"]), (u"分母", D), (u"旗", 100 * b3["HT"]["N"] > FLAG_HT_N_OVER * D)])),
        (u"段 HT・name だけの U が %d%% 未満(便 XY0 の行の単位の数と合わないか)" % FLAG_NAME_U_UNDER,
         od([(u"fact", C["name"]["HT"]["U"]), (u"分母", D), (u"旗", 100 * C["name"]["HT"]["U"] < FLAG_NAME_U_UNDER * D)])),
        (u"行の外の fact が全体の %d%% を超えた(行の切り方が fact を落としていないか)" % FLAG_OUTSIDE_OVER,
         od([(u"fact", tot["outside"]), (u"分母", D + tot["outside"]), (u"旗", 100 * tot["outside"] > FLAG_OUTSIDE_OVER * (D + tot["outside"]))]))])
    ht, hh, ff = b3["HT"], b3["H"], b3["F"]
    b5ht, b3nn = C["b5"]["HT"], C["b3nn"]["HT"]
    rec[u"予測の判定に要る数(XZ0-1〜XZ0-8。当たり・外れは結果の文書で)"] = od([
        (u"XZ0-1 段 HT・束 3 の類 U / 行の中の数の fact", rate_of(ht["U"], D)),
        (u"XZ0-2 段 HT・束 3 の類 W1 / 行の中の数の fact", rate_of(ht["W1"], D)),
        (u"XZ0-2 段 HT・束 3 の類 W1 / (U + W1)", rate_of(ht["W1"], ht["U"] + ht["W1"])),
        (u"XZ0-3 段 HT・束 3 の類 N と類 X の合計 / 行の中の数の fact", rate_of(ht["N"] + ht["X"], D)),
        (u"XZ0-4 段 F・束 3 の類 U / 行の中の数の fact", od([
            (u"段 F の U の fact", ff["U"]), (u"段 HT の U の fact", ht["U"]), (u"分母", D),
            (u"段 F の U の %", pct1(ff["U"], D)), (u"段 HT の U の %", pct1(ht["U"], D)),
            (u"段 F から段 HT を引いた差(ポイント)", diff_points(ff["U"], D, ht["U"], D))])),
        (u"XZ0-4 段 F・束 3 の類 W1 / 行の中の数の fact", rate_of(ff["W1"], D)),
        (u"XZ0-4 段 F・束 3 の類 W1 / (U + W1)", rate_of(ff["W1"], ff["U"] + ff["W1"])),
        (u"XZ0-5 段 H・束 3 の類 U と段 HT の類 U", od([
            (u"段 H の U の fact", hh["U"]), (u"段 HT の U の fact", ht["U"]), (u"分母", D),
            (u"段 H の U の %", pct1(hh["U"], D)), (u"段 HT の U の %", pct1(ht["U"], D)),
            (u"段 HT から段 H を引いた差(ポイント)", diff_points(ht["U"], D, hh["U"], D))])),
        (u"XZ0-6 空の欄でない fact・段 HT の束 5 と束 3 の類 U", od([
            (u"束 5 の U の fact", b5ht["U"]), (u"束 3 の U の fact(空の欄でない fact だけ)", b3nn["U"]), (u"分母(空の欄でない fact)", NN),
            (u"束 5 の U の %", pct1(b5ht["U"], NN)), (u"束 3 の U の %", pct1(b3nn["U"], NN)),
            (u"束 5 から束 3 を引いた差(ポイント)", diff_points(b5ht["U"], NN, b3nn["U"], NN))])),
        (u"XZ0-7 段 HT の contextRef だけの類 U と name だけの類 U", od([
            (u"contextRef の U の fact", C["ctx"]["HT"]["U"]), (u"name の U の fact", C["name"]["HT"]["U"]), (u"分母", D),
            (u"contextRef の U の %", pct1(C["ctx"]["HT"]["U"], D)), (u"name の U の %", pct1(C["name"]["HT"]["U"], D)),
            (u"unitRef の U の fact", C["unit"]["HT"]["U"]), (u"unitRef の U の %", pct1(C["unit"]["HT"]["U"], D))])),
        (u"XZ0-8 段 HT・束 3 の U の率の書類ごとの本数", od([
            (u"%d%% 以上の書類" % U_DOC_HI_PCT, docs_hi), (u"%d%% 以上の書類" % U_DOC_LO_PCT, docs_lo),
            (u"fact が 1 つ以上在る書類", docs_with_facts), (u"組の数", len(pairs))]))])
    rec[u"限界"] = list(LIMITS)
    return rec, secret


def check_clean(rec, text, secret=None):
    u"""記録に書かないもの(便 XG1 の検査 + 日付の形)が無いか。在れば止める。secret = (行の字, 要素・文脈・単位の局所の字, docID(前の年の側を含む), 提出者のコード, 見出しの字, 業種の値(使わない))。"""
    N.check_clean(rec, text, secret)
    if DATE_RE.search(W.HEX_RE.sub(u"", text).replace(SEAL_REL, u"")):
        raise Stop(u"**記録に日付の形の字が在る。止める**")


def record_text(rec, secret=None):
    text = dumps(rec)
    check_clean(rec, text, secret)
    return text


def write_exclusive(path, data):
    with open(path, "xb") as fh:
        fh.write(data)


def write_record(path, rec, secret=None):
    u"""書く前と書いた後に検査する。既に在れば止める(測り直さない)。"""
    if os.path.exists(path):
        raise Stop(u"**記録が既に在る: %s。止める**" % os.path.basename(path))
    text = record_text(rec, secret)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_exclusive(path, text.encode("utf-8"))
    with io.open(path, encoding="utf-8") as fh:
        back = fh.read()
    try:
        check_clean(rec, back, secret)
    except SystemExit:
        os.remove(path)
        raise


def run(root=ROOT, docs=None, prior=None, out=None, want_docs=DOCS_WANT, want_pairs=PAIRS_WANT, say=print):
    rec, secret = build_record(docs, prior, want_docs, want_pairs)
    out = out or os.path.join(root, RECORD_REL)
    write_record(out, rec, secret)
    say(u"-> %s(組 %d)" % (os.path.basename(out), rec[u"材料"][u"組の数"]))
    return rec


def check(root=ROOT, docs=None, prior=None, rec_path=None, want_docs=DOCS_WANT, want_pairs=PAIRS_WANT, say=print):
    u"""置き場から数え直して記録と照らす。通信しない。"""
    p = rec_path or os.path.join(root, RECORD_REL)
    if not os.path.isfile(p):
        raise Stop(u"**在る記録が無い。止める**")
    with io.open(p, encoding="utf-8") as fh:
        text = fh.read()
    rec = json.loads(text, object_pairs_hook=collections.OrderedDict)
    now, secret = build_record(docs, prior, want_docs, want_pairs)
    if dumps(now) != dumps(rec):
        raise Stop(u"**置き場から数え直した記録が、今の記録と違う。止める**")
    check_clean(rec, text, secret)
    say(u"--check: 記録は置き場から数え直した数と同じ(組 %d)" % now[u"材料"][u"組の数"])
    return now


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="置き場から数え直して記録と照らす。通信しない")
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--docs", default=None, help="今年の側の置き場(既定は封の字)")
    ap.add_argument("--prior", default=None, help="前の年の側の置き場(既定は封の字)")
    a = ap.parse_args(argv)
    kw = dict(docs=a.docs, prior=a.prior)
    if a.check:
        check(root=a.root, **kw)
    else:
        run(root=a.root, **kw)


if __name__ == "__main__":
    main()
