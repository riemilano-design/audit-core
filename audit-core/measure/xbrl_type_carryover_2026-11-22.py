# -*- coding: utf-8 -*-
u"""封 docs/XBRL_TYPE_CARRYOVER_SEAL_2026-11-22.md(XK0 ― 同じ会社の前の年の「型」と「対応表」は、今年の型にどれだけ持ち越せるか。今年、新しく決める名・新しく入れる行はどれだけ残るか)の測定。
**0 USD。LLM の席は呼ばない。道具(Arelle)は呼ばない。鍵は使わない。通信しない。** engine(``core/``・``adapters/``)は読まない・変えない。

    python3 measure/xbrl_type_carryover_2026-11-22.py            # 63 組を数えて記録 fixtures/xbrl/cd8/type_carryover_2026-11-22.json を排他で書く(本番は 1 回)
    python3 measure/xbrl_type_carryover_2026-11-22.py --check    # 記録の形・組ごとの数からの導き直し・禁止のものを検査する。置き場は読まない
    python3 measure/xbrl_type_carryover_2026-11-22.py --dev      # 番号 1・2・3 の 3 組だけ数えて表示する。記録は書かない

組は便 XY0 の script(``measure/xbrl_prior_year_draft_2026-11-22.py``。Y)の関数 ``make_pairs`` で作る(写さない・変えない)。
型を作る分析は便 XM0 の script(``measure/xbrl_input_type_2026-11-22.py``。M)の ``analyze``・``code_maps``・``period_name`` を両方の年に同じに掛ける(写さない)。
``M.derive_folder``・``M.process_doc`` は呼ばない(folder を書き、道具を呼ぶため)。

実装の注(封の字では 1 通りに決まらなかった所の決め。実装より先に決め、結果を見て変えない。報告にも書く):
- 鍵(日)の「次元の (軸の名, member の名) の組の集まり」は、組を昇順に並べた tuple。鍵(枠)は鍵(日)の期間の日を期の名(今年の行は今年の書類の決め・前の年の行は前の年の書類の決め)に置き換えたもの。
- 期の名が付かない型の行は在りえない(型の外の fact の理由 (a))。在れば止まる。期の名が ``Prior<N>Year`` の N が 1 なら前期・2 以上ならそれより前。
- 名の接頭辞は最初の ``:`` の前の字(``:`` が無ければ空)。接頭辞が ``_cor`` で終わるかは種類(科目・軸・member)ごとに分けて数える。
- 同じ行の中身の 4 つの分けの順: 値が両側とも `無い` なら値は同じ・片方だけが `無い` なら「片方だけが `無い`」・どちらも `無い` でなく値の字が違えば「値が違う」・値が同じなら単位・表示の位・精度が全部同じなら「全部同じ」・どれか違えば「値は同じで、単位・表示の位・精度のどれかが違う」。値は便 XM0 の型の値の字のまま比べる(`-0` と `0` は違う)。
- 断った組: 今年の側を先に分析し、断りが出れば前の年の側は分析しない(断った年は先に断った側)。M.Refuse だけを断りに数える(ほかの例外は止まる)。断った組は数の全部で 0(分母にも入れない)。
- 組の分け: 番号が 3 以下の組が訓練の 3 組・4 以上の組が判定の 60 組(番号は便 XY0 の組の番号 = 今年の側の 67 本の昇順の位置。除いた書類の番号は飛ぶ)。
- 先に疑う旗: 旗 1(当期の行に同じ行(日))・旗 4(枠が在る行が名が足りる行より多い。数・文の別に比べる)・旗 6(便 XM0 の記録との型の行の数の違い。番号で照らす)は 63 組。旗 2(科目の持ち越しが全部で 100%。断った組が在れば立たない)・旗 3(同じ行(数)の合計が 0)・旗 5(断った組が 6 以上)は判定の 60 組。
- 旗 6 の照らし方: 便 XM0 の記録の書類の番号 = 組の番号(どちらも便 XG0 の ``select_docs`` の並びの位置)。記録の ``書類の file 名の並びの sha256`` と今年の側の並びの sha256 が違えば止まる。今年の側を分析できなかった組は 0 と照らす(便 XM0 で断った書類も 0)。
- 判定の数の「組の数で言う予測」(XK0-9・XK0-10)は、断った組を満たさないに数える。XK0-9 は今年の科目の名が 1 つ以上在る組だけを満たしうる。
"""
from __future__ import print_function

import argparse
import collections
import hashlib
import importlib.util
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _load_sibling(name, fname):
    u"""前の便の script を、他と重ならない一意の名で読む(関数は呼ぶだけ。写さない)。"""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, fname))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


M = _load_sibling("_xk0_input_type_2026_11_22", "xbrl_input_type_2026-11-22.py")             # 便 XM0 の script
Y = _load_sibling("_xk0_prior_year_draft_2026_11_22", "xbrl_prior_year_draft_2026-11-22.py")   # 便 XY0 の script
W = M.W                                                                                        # 便 XG0 の script

SEAL_REL = "docs/XBRL_TYPE_CARRYOVER_SEAL_2026-11-22.md"
SEAL_COMMIT = "1fc4c736"
SCRIPT_REL = "measure/xbrl_type_carryover_2026-11-22.py"
RECORD_REL = "fixtures/xbrl/cd8/type_carryover_2026-11-22.json"
XM0_RECORD_REL = "fixtures/xbrl/cd8/input_type_2026-11-22.json"
DOCS_DIR = Y.DOCS_DIR
PRIOR_DIR = Y.PRIOR_DIR

# ---- 封 §1・§2・§3・§4 の決めごと(字で留める。封の門が封の字と照らす)
DOCS_WANT = Y.DOCS_WANT
PAIRS_WANT = Y.PAIRS_WANT
SEEN_MAX_NO = 3                       # 番号がこれ以下の組が訓練の 3 組
TRAIN_WANT, JUDGE_WANT = 3, 60
DEV_NOS = (1, 2, 3)
KN, KT = M.KIND_NUM, M.KIND_TEXT      # 数・文
KINDS = (u"科目", u"軸", u"member")
SIDES = (u"今年", u"前の年")
CLASS4 = (u"当期", u"前期", u"それより前", u"提出日")
CONTENT4 = (u"全部同じ", u"値は同じで、単位・表示の位・精度のどれかが違う", u"値が違う", u"片方だけが 無い")
COR_END = "_cor"
PRIOR_N_RE = re.compile(r"^Prior([0-9]+)Year$")
REASONS = M.REASONS
VALUE_NONE = M.VALUE_NONE
FLAG_REFUSE_MIN = 6                   # 先に疑う旗: 断った組がこれ以上
#: 封 §4 の予測の境(記録には判定を書かない。封の門が封の表と照らす)。(下限, 下限を含むか, 上限, 上限を含むか)。None = 無い。率は %・組・本の数
BOUNDS = collections.OrderedDict([
    ("XK0-1", (96, True, None, False)), ("XK0-2", (97, True, None, False)), ("XK0-3", (97, True, None, False)), ("XK0-4", (96, True, 100, False)),
    ("XK0-5", (44, True, 52, False)), ("XK0-6", (95, True, None, False)), ("XK0-7", (50, False, None, False)), ("XK0-8", (None, False, 3, True)),
    ("XK0-9", (48, True, None, False)), ("XK0-10", (57, True, None, False))])
KEEP_ONE_PCT = 95                     # XK0-9: 科目の名の持ち越しがこれ以上の組
LIMITS = [
    u"どちらの年の型も対応表も答えから作った。会社が型を埋められるか・対応表を作れるか・埋めた中身が正しいかは測っていない。持ち越しは上限。",
    u"数え方と予測は頭の 3 組を見て決めた。判定の 60 組も前の便で数えた書類で、未使用ではない。63 組は無作為ではない。有報だけ。連続する 2 年だけ(3 年目以降・決算期を変えた年・様式が変わった年は見ていない)。",
    u"名は字で比べる。標準タクソノミの年の入れ替えで名が変わった科目は「新しい名」と「消えた名」に数える(同じものの改名かは見ない)。",
    u"型の外の fact は数えるだけで、持ち越しの分母に入らない。本文・置き場・脚注は見ない。",
    u"XBRL を組まない・道具に掛けない。EDINET の本物の検査とは照らさない。",
    u"予測は司令塔が立てた。盲検ではない。"]

Stop = W.Stop
Refuse = M.Refuse
od = collections.OrderedDict
sha256_bytes = W.sha256_bytes
sha256_file = W.sha256_file
dumps = W.dumps
pct1 = W.pct1
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
NOT_SUMMED = (u"番号", u"断った", u"断った年", u"断った理由", u"旗用の数")


# ======================================================================================================
# 鍵・期の区分・名(封 §1)
def name_prefix(name):
    u"""名 ``接頭辞:局所名`` の接頭辞(最初の ``:`` の前。``:`` が無ければ空)。"""
    return name.split(":", 1)[0] if ":" in name else ""


def dims_key(row):
    u"""次元の (軸の名, member の名) の組の集まり(昇順の tuple)。"""
    return tuple(sorted(tuple(x) for x in row["dims"]))


def key_day(row):
    u"""型の行の鍵(日): (種類・科目の名・期間の種類・期間の日・対象・次元の集まり)。"""
    return (row["kind"], row["name"], row["pkind"], tuple(row["period"]), row["target"], dims_key(row))


def key_frame(row, dec):
    u"""型の行の鍵(枠): 鍵(日)の期間の日を期の名(``dec`` = その行の書類の決め)に置き換えたもの。"""
    return (row["kind"], row["name"], row["pkind"], M.period_name(row["pkind"], row["period"], dec), row["target"], dims_key(row))


def period_class(row, dec):
    u"""期の区分(当期・前期・それより前・提出日)。期の名が付かない行は在りえないので止まる。"""
    pn = M.period_name(row["pkind"], row["period"], dec)
    if pn == M.PERIOD_CUR:
        return u"当期"
    if pn == M.PERIOD_FILING:
        return u"提出日"
    m = PRIOR_N_RE.match(pn or "")
    if m is None:
        raise Stop(u"**型の行に期の名が付かない。止める**")
    return u"前期" if int(m.group(1)) == 1 else u"それより前"


def content_class(row, prow):
    u"""同じ鍵(日)の数の行 2 つ(今年の行・前の年の行)の中身の 4 つの分けの 1 つ。"""
    rv, pv = row["value"], prow["value"]
    if (rv == VALUE_NONE) != (pv == VALUE_NONE):
        return CONTENT4[3]
    if rv != pv:
        return CONTENT4[2]
    if (row["unit"], row["shift"], row["prec"]) == (prow["unit"], prow["shift"], prow["prec"]):
        return CONTENT4[0]
    return CONTENT4[1]


# ======================================================================================================
# 数の欄(組 1 つ分)
def two():
    return od([(KN, 0), (KT, 0)])


def four():
    return od((c, 0) for c in CLASS4)


def by_kind_four():
    return od([(KN, four()), (KT, four())])


def zero_pair():
    u"""組 1 つの数(全部 0)。断った組はこのまま。"""
    return od([
        (u"断った", False), (u"断った年", u""), (u"断った理由", u""),
        (u"対象の fact", od((s, two()) for s in SIDES)),
        (u"型の外の fact", od((s, od([(u"理由ごと", od((r, two()) for r in REASONS)), (u"合計", two())])) for s in SIDES)),
        (u"型の行", od((s, two()) for s in SIDES)),
        (u"対応表の名", od((k, od([(u"今年", 0), (u"持ち越せる", 0), (u"新しい", 0), (u"新しい・_cor で終わる", 0), (u"新しい・_cor で終わらない", 0), (u"消えた", 0)])) for k in KINDS)),
        (u"名が足りる行", two()),
        (u"今年の行の期の区分", by_kind_four()),
        (u"同じ行(日)", by_kind_four()),
        (u"同じ行の中身(数)", od((c, 0) for c in CONTENT4)),
        (u"枠が在る行", by_kind_four()),
        (u"逆向き", od((k, od([(u"前の年の行", 0), (u"同じ鍵(日)が今年に在る", 0), (u"同じ鍵(枠)が今年に在る", 0), (u"今年、要らなくなった枠", 0)])) for k in (KN, KT)))])


def entry_tail(row_counts):
    u"""旗 6 のための数(分析できた今年の側の型の行。合計には足さない)。row_counts = (今年の側を分析できたか, 数の行, 文の行)。"""
    ok, n, t = row_counts
    return od([(u"今年の側を分析できた", bool(ok)), (u"今年の側の型の行", od([(KN, n), (KT, t)]))])


def count_types(cur, prior):
    u"""2 年分の型の分析(``analyze`` の戻り値の形: ``dec``・``facts``(``isnum``・``reasons``)・``rows``)→ 組 1 つの数(封 §2 の 1.〜7.)。
    今年の行は今年の書類の決めで・前の年の行は前の年の書類の決めで期の名を付ける。"""
    out = zero_pair()
    for side, an in zip(SIDES, (cur, prior)):
        for f in an["facts"]:
            k = KN if f["isnum"] else KT
            out[u"対象の fact"][side][k] += 1
            if f["reasons"]:
                out[u"型の外の fact"][side][u"合計"][k] += 1
                for r in f["reasons"]:
                    out[u"型の外の fact"][side][u"理由ごと"][r][k] += 1
        for r in an["rows"]:
            out[u"型の行"][side][r["kind"]] += 1
    # 1. 対応表の名
    cmaps, _ci = M.code_maps(cur["rows"])
    pmaps, _pi = M.code_maps(prior["rows"])
    cn = dict((k, set(cmaps[k].values())) for k in KINDS)
    pn = dict((k, set(pmaps[k].values())) for k in KINDS)
    for k in KINDS:
        d = out[u"対応表の名"][k]
        new = cn[k] - pn[k]
        d[u"今年"] = len(cn[k])
        d[u"持ち越せる"] = len(cn[k] & pn[k])
        d[u"新しい"] = len(new)
        d[u"新しい・_cor で終わる"] = sum(1 for n in new if name_prefix(n).endswith(COR_END))
        d[u"新しい・_cor で終わらない"] = sum(1 for n in new if not name_prefix(n).endswith(COR_END))
        d[u"消えた"] = len(pn[k] - cn[k])
    # 鍵
    pday = dict((key_day(r), r) for r in prior["rows"])
    if len(pday) != len(prior["rows"]):
        raise Stop(u"**前の年の型の行の鍵(日)が重なる。止める**")
    pframe = set(key_frame(r, prior["dec"]) for r in prior["rows"])
    cday = set(key_day(r) for r in cur["rows"])
    cframe = set(key_frame(r, cur["dec"]) for r in cur["rows"])
    # 2.〜5. 今年の行
    for r in cur["rows"]:
        k = r["kind"]
        cls = period_class(r, cur["dec"])
        out[u"今年の行の期の区分"][k][cls] += 1
        if r["name"] in pn[u"科目"] and all(ax in pn[u"軸"] and m in pn[u"member"] for ax, m in r["dims"]):
            out[u"名が足りる行"][k] += 1
        q = pday.get(key_day(r))
        if q is not None:
            out[u"同じ行(日)"][k][cls] += 1
            if k == KN:
                out[u"同じ行の中身(数)"][content_class(r, q)] += 1
        if key_frame(r, cur["dec"]) in pframe:
            out[u"枠が在る行"][k][cls] += 1
    # 6. 逆向き
    for q in prior["rows"]:
        d = out[u"逆向き"][q["kind"]]
        d[u"前の年の行"] += 1
        if key_day(q) in cday:
            d[u"同じ鍵(日)が今年に在る"] += 1
        if key_frame(q, prior["dec"]) in cframe:
            d[u"同じ鍵(枠)が今年に在る"] += 1
    for d in out[u"逆向き"].values():
        d[u"今年、要らなくなった枠"] = d[u"前の年の行"] - d[u"同じ鍵(枠)が今年に在る"]
    return out


def analyze_side(zip_path):
    u"""zip 1 本 → 型の分析。断り(``M.Refuse``。便 XB0 の断りは便 XP0 の ``peel_tables`` が ``Refuse`` にして出す)はそのまま投げる。"""
    files, _names, _tables = M.P.peel_tables(M.B.load_package(zip_path))
    return M.analyze(files)


def pair_entry(n, cur_path, prior_path, analyzer=None):
    u"""組 1 つ → (記録の書類 1 つ, 名の集まり(secret 用))。"""
    analyzer = analyzer or analyze_side
    ent = od([(u"番号", n)])
    try:
        cur = analyzer(cur_path)
    except Refuse as exc:
        ent.update(zero_pair())
        ent[u"断った"], ent[u"断った年"], ent[u"断った理由"] = True, u"今年", exc.reason
        ent[u"旗用の数"] = entry_tail((False, 0, 0))
        return ent, set()
    cur_rows = (True, sum(1 for r in cur["rows"] if r["kind"] == KN), sum(1 for r in cur["rows"] if r["kind"] == KT))
    try:
        prior = analyzer(prior_path)
    except Refuse as exc:
        ent.update(zero_pair())
        ent[u"断った"], ent[u"断った年"], ent[u"断った理由"] = True, u"前の年", exc.reason
        ent[u"旗用の数"] = entry_tail(cur_rows)
        return ent, names_in(cur)
    ent.update(count_types(cur, prior))
    ent[u"旗用の数"] = entry_tail(cur_rows)
    return ent, names_in(cur) | names_in(prior)


def names_in(an):
    u"""分析の型の行に現れた名・接頭辞・局所名(記録に書かないものの検査に使う)。"""
    out = set()
    for r in an["rows"]:
        for n in [r["name"]] + [x for pair in r["dims"] for x in pair]:
            out.add(n)
            out.add(name_prefix(n))
            out.add(n.split(":", 1)[-1])
    return out


# ======================================================================================================
# 集計・判定の数・旗
def group_total(entries):
    u"""組ごとの数の並び → 集計(組の数・断った組の数・数の合計)。"""
    body = [od((k, v) for k, v in e.items() if k not in NOT_SUMMED) for e in entries]
    return od([(u"組", len(entries)), (u"断った組", sum(1 for e in entries if e[u"断った"])), (u"数", M.sum_nested(body) if body else od())])


def totals_of(entries):
    train = [e for e in entries if e[u"番号"] <= SEEN_MAX_NO]
    rest = [e for e in entries if e[u"番号"] > SEEN_MAX_NO]
    return od([(u"訓練の 3 組", group_total(train)), (u"判定の 60 組", group_total(rest)), (u"全部の 63 組", group_total(entries))])


def rate_of(n, d):
    return od([(u"数", n), (u"分母", d), (u"%", pct1(n, d))])


def sum4(d, names=CLASS4):
    return sum(d[c] for c in names)


def keep_pct_pair(e):
    u"""XK0-9: 断っていない・今年の科目の名が 1 つ以上・持ち越しが 95% 以上の組。"""
    c = e[u"対応表の名"][u"科目"]
    return (not e[u"断った"]) and c[u"今年"] > 0 and 100 * c[u"持ち越せる"] >= KEEP_ONE_PCT * c[u"今年"]


def not_all_same_pair(e):
    u"""XK0-10: 断っていない・同じ行(数)に「全部同じ」でない行が 1 つ以上在る組。"""
    z = e[u"同じ行の中身(数)"]
    return (not e[u"断った"]) and sum(z.values()) - z[CONTENT4[0]] >= 1


def judged(judge_entries):
    u"""封 §4 の判定に要る数(判定の 60 組だけ。当たり・外れは書かない)。"""
    g = group_total(judge_entries)
    z = g[u"数"]
    sc = z[u"対応表の名"][u"科目"]
    rows_n = z[u"型の行"][u"今年"][KN]
    cls_n = z[u"今年の行の期の区分"][KN]
    same_n = z[u"同じ行(日)"][KN]
    cont = z[u"同じ行の中身(数)"]
    old = (u"前期", u"それより前")
    return od([
        (u"XK0-1 今年の科目の名のうち前の年の対応表に在る名 / 今年の科目の名", rate_of(sc[u"持ち越せる"], sc[u"今年"])),
        (u"XK0-2 名が足りる数の行 / 今年の数の型の行", rate_of(z[u"名が足りる行"][KN], rows_n)),
        (u"XK0-3 期の区分が前期かそれより前の数の行のうち、同じ行(日)が在る行 / その数の行", rate_of(sum4(same_n, old), sum4(cls_n, old))),
        (u"XK0-4 同じ行(数)のうち全部同じ / 同じ行(数)", rate_of(cont[CONTENT4[0]], sum4(same_n))),
        (u"XK0-5 今年の数の型の行のうち、同じ行で全部同じの行 / 今年の数の型の行", rate_of(cont[CONTENT4[0]], rows_n)),
        (u"XK0-6 今年の数の型の行のうち、枠が在る行 / 今年の数の型の行", rate_of(sum4(z[u"枠が在る行"][KN]), rows_n)),
        (u"XK0-7 新しい科目の名のうち、接頭辞が _cor で終わる名 / 新しい科目の名", rate_of(sc[u"新しい・_cor で終わる"], sc[u"新しい"])),
        (u"XK0-8 断った組 / 判定の組", od([(u"組", g[u"断った組"]), (u"分母", g[u"組"])])),
        (u"XK0-9 科目の名の持ち越しが 95% 以上の組 / 判定の組", od([(u"組", sum(1 for e in judge_entries if keep_pct_pair(e))), (u"分母", g[u"組"])])),
        (u"XK0-10 同じ行(数)に全部同じでない行が 1 つ以上在る組 / 判定の組", od([(u"組", sum(1 for e in judge_entries if not_all_same_pair(e))), (u"分母", g[u"組"])]))])


def flags(entries, xm0):
    u"""先に自分の欠陥を疑う旗 6 つ(立っても止めない。記録に書く)。``xm0`` = 便 XM0 の記録(の dict)。"""
    rest = [e for e in entries if e[u"番号"] > SEEN_MAX_NO]
    cur_same = sum(sum4(e[u"同じ行(日)"][k], (u"当期",)) for e in entries for k in (KN, KT))
    names_ok = [e for e in rest if not e[u"断った"] and e[u"対応表の名"][u"科目"][u"今年"] > 0 and e[u"対応表の名"][u"科目"][u"持ち越せる"] == e[u"対応表の名"][u"科目"][u"今年"]]
    same_num = sum(sum4(e[u"同じ行(日)"][KN]) for e in rest)
    frame_over = [e[u"番号"] for e in entries if any(sum4(e[u"枠が在る行"][k]) > e[u"名が足りる行"][k] for k in (KN, KT))]
    refused = sum(1 for e in rest if e[u"断った"])
    by_no = dict((d[u"番号"], d) for d in xm0[u"書類"])
    diff = 0
    for e in entries:
        x = by_no.get(e[u"番号"])
        if x is None:
            raise Stop(u"**便 XM0 の記録に同じ番号が無い。止める**")
        tail = e[u"旗用の数"][u"今年の側の型の行"]
        if (tail[KN], tail[KT]) != (x[u"型の行"][KN], x[u"型の行"][KT]):
            diff += 1
    return od([
        (u"旗 1 期の区分が当期の行に、同じ行(日)が 1 つでも在る(63 組)", od([(u"同じ行(日)の当期の行", cur_same), (u"旗", cur_same >= 1)])),
        (u"旗 2 科目の名の持ち越しが判定の 60 組の全部で 100%", od([(u"100% の組", len(names_ok)), (u"判定の組", len(rest)), (u"旗", len(names_ok) == len(rest) and len(rest) > 0)])),
        (u"旗 3 同じ行(数)が判定の 60 組の合計で 0", od([(u"同じ行(数)", same_num), (u"旗", same_num == 0)])),
        (u"旗 4 枠が在る行が名が足りる行より多い組が在る(63 組。数・文の別に比べる)", od([(u"その組", len(frame_over)), (u"旗", len(frame_over) >= 1)])),
        (u"旗 5 断った組が 6 以上(判定の 60 組)", od([(u"断った組", refused), (u"旗", refused >= FLAG_REFUSE_MIN)])),
        (u"旗 6 便 XM0 の記録の型の行の数(数・文)と、今年の側の型の行の数が違う組が在る(63 組)", od([(u"違う組", diff), (u"旗", diff >= 1)]))])


# ======================================================================================================
# 記録
def build_record(docs_dir=None, prior_dir=None, want_docs=DOCS_WANT, want_pairs=PAIRS_WANT, xm0=None, xm0_sha=None, pairs=None, docs=None, analyzer=None, progress=None):
    u"""置き場 → (記録, secret)。書かない。``pairs``・``docs``・``analyzer`` は封の門の作り物が差し込む(本番は None)。``xm0`` = 便 XM0 の記録の dict。"""
    if pairs is None:
        docs, pairs, excluded = Y.make_pairs(docs_dir or DOCS_DIR, prior_dir or PRIOR_DIR, want_docs, want_pairs)
    else:
        excluded = len(docs) - len(pairs)
    if xm0 is None:
        raise Stop(u"**便 XM0 の記録が無い。止める**")
    order_sha = W.order_sha256([d[0] for d in docs])
    if xm0[u"材料"][u"書類の file 名の並びの sha256"] != order_sha:
        raise Stop(u"**便 XM0 の記録の書類の並びが今年の側の並びと違う。止める**")
    entries, names = [], set()
    for n, _stem, p, _pstem, pp, _code in pairs:
        ent, nm = pair_entry(n, p, pp, analyzer)
        entries.append(ent)
        names |= nm
        if progress is not None:
            progress(u"組 %d" % n)
    tot = totals_of(entries)
    if len(entries) != want_pairs or tot[u"訓練の 3 組"][u"組"] != TRAIN_WANT or tot[u"判定の 60 組"][u"組"] != JUDGE_WANT:
        raise Stop(u"**組の数が訓練 3・判定 60・全部 63 でない。止める**")
    rest = [e for e in entries if e[u"番号"] > SEEN_MAX_NO]
    rec = od()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"XK0(同じ会社の前の年の型と対応表が今年の型にどれだけ持ち越せるか・今年、新しく決める名・新しく入れる行はどれだけ残るか)(0 USD・engine は 0 行)"
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"材料"] = od([
        (u"今年の側の書類の本数", len(docs)), (u"今年の側の書類の file 名の並びの sha256", order_sha),
        (u"組の数", len(pairs)), (u"訓練の組の数", tot[u"訓練の 3 組"][u"組"]), (u"判定の組の数", tot[u"判定の 60 組"][u"組"]), (u"除いた今年の書類の数", excluded),
        (u"前の年の側の組の相手の file 名の並びの sha256", sha256_bytes(u"\n".join(p[3] for p in pairs).encode("utf-8"))),
        (u"便 XM0 の記録の sha256", xm0_sha)])
    rec[u"書類"] = entries
    rec[u"集計"] = tot
    rec[u"予測の判定に要る数(XK0-1〜XK0-10。判定の 60 組だけ。当たり・外れは結果の文書で)"] = judged(rest)
    rec[u"先に自分の欠陥を疑う旗"] = flags(entries, xm0)
    rec[u"限界"] = list(LIMITS)
    ecodes = set(p[5] for p in pairs)
    for x in docs:
        for s in x[2]:
            ecodes.update(re.findall(r"E\d{5}", s))
    secret = (set(), set(n for n in names if len(n) >= 3), [d[0] for d in docs] + [p[3] for p in pairs], ecodes, set())
    return rec, secret


def check_clean(rec, text, secret=None):
    u"""記録に書かないもの(欄・docID・EDINET コード・file の名・要素の名・日付の形)が無いか。在れば止める。"""
    M.check_clean(rec, text, secret)
    if DATE_RE.search(W.HEX_RE.sub(u"", text).replace(SEAL_REL, u"")):
        raise Stop(u"**記録に日付の形の字が在る。止める**")


def entry_problems(e):
    u"""組 1 つの数の導ける関係(数の足し算)。違えば理由の字。"""
    z = zero_pair()
    if list(e) != [u"番号"] + list(z) + [u"旗用の数"]:
        return u"組の欄が違う"
    if e[u"断った"] != bool(e[u"断った年"]) or e[u"断った"] != bool(e[u"断った理由"]) or (e[u"断った"] and e[u"断った年"] not in SIDES):
        return u"断った組の欄が違う"
    if e[u"断った"]:
        body = od((k, v) for k, v in e.items() if k not in NOT_SUMMED)
        zb = od((k, v) for k, v in z.items() if k not in NOT_SUMMED)
        if dumps(body) != dumps(zb):
            return u"断った組の数が 0 でない"
        return u""
    for k in KINDS:
        d = e[u"対応表の名"][k]
        if d[u"持ち越せる"] + d[u"新しい"] != d[u"今年"] or d[u"新しい・_cor で終わる"] + d[u"新しい・_cor で終わらない"] != d[u"新しい"]:
            return u"対応表の名の数が足し算と合わない"
    for k in (KN, KT):
        rows = e[u"型の行"][u"今年"][k]
        if sum4(e[u"今年の行の期の区分"][k]) != rows or e[u"名が足りる行"][k] > rows:
            return u"今年の行の数が足し算と合わない"
        for c in CLASS4:
            if e[u"枠が在る行"][k][c] > e[u"今年の行の期の区分"][k][c] or e[u"同じ行(日)"][k][c] > e[u"今年の行の期の区分"][k][c]:
                return u"同じ行・枠が在る行が今年の行の数より多い"
        if sum4(e[u"枠が在る行"][k]) > e[u"名が足りる行"][k] or sum4(e[u"同じ行(日)"][k]) > e[u"名が足りる行"][k]:
            return u"同じ行・枠が在る行が名が足りる行より多い"
        back = e[u"逆向き"][k]
        if back[u"前の年の行"] != e[u"型の行"][u"前の年"][k] or back[u"同じ鍵(日)が今年に在る"] != sum4(e[u"同じ行(日)"][k]) or back[u"今年、要らなくなった枠"] != back[u"前の年の行"] - back[u"同じ鍵(枠)が今年に在る"]:
            return u"逆向きの数が違う"
    if sum(e[u"同じ行の中身(数)"].values()) != sum4(e[u"同じ行(日)"][KN]):
        return u"同じ行の中身の 4 つの分けの合計が同じ行(数)と違う"
    for s in SIDES:
        o = e[u"型の外の fact"][s]
        for k in (KN, KT):
            if o[u"合計"][k] > e[u"対象の fact"][s][k] or max(o[u"理由ごと"][r][k] for r in REASONS) > o[u"合計"][k] or e[u"型の行"][s][k] > e[u"対象の fact"][s][k] - o[u"合計"][k]:
                return u"型の外の fact の数が合わない"
    t = e[u"旗用の数"]
    if not t[u"今年の側を分析できた"] or (t[u"今年の側の型の行"][KN], t[u"今年の側の型の行"][KT]) != (e[u"型の行"][u"今年"][KN], e[u"型の行"][u"今年"][KT]):
        return u"旗用の数が今年の型の行の数と違う"
    return u""


def verify_record(rec, xm0, text=None, want=PAIRS_WANT):
    u"""記録の形・組ごとの数からの導き直し・禁止のものを検査する(置き場は読まない)。違えば止まる。"""
    docs = rec.get(u"書類")
    if not isinstance(docs, list) or len(docs) != want or rec[u"材料"][u"組の数"] != want:
        raise Stop(u"**記録の組が 63 でない。止める**")
    nos = [d.get(u"番号") for d in docs]
    if any(not isinstance(n, int) for n in nos) or nos != sorted(set(nos)):
        raise Stop(u"**記録の組の番号が昇順でない。止める**")
    for d in docs:
        why = entry_problems(d)
        if why:
            raise Stop(u"**記録の組の数が違う: %s。止める**" % why)
    tot = totals_of(docs)
    if dumps(tot) != dumps(rec[u"集計"]):
        raise Stop(u"**記録の集計が組ごとの数と合わない。止める**")
    rest = [d for d in docs if d[u"番号"] > SEEN_MAX_NO]
    key = [k for k in rec if k.startswith(u"予測の判定に要る数")][0]
    if dumps(judged(rest)) != dumps(rec[key]):
        raise Stop(u"**記録の判定の数が組ごとの数と合わない。止める**")
    if dumps(flags(docs, xm0)) != dumps(rec[u"先に自分の欠陥を疑う旗"]):
        raise Stop(u"**記録の旗が組ごとの数と合わない。止める**")
    mat = rec[u"材料"]
    if (mat[u"訓練の組の数"], mat[u"判定の組の数"]) != (tot[u"訓練の 3 組"][u"組"], tot[u"判定の 60 組"][u"組"]) or rec[u"限界"] != list(LIMITS):
        raise Stop(u"**記録の材料・限界が違う。止める**")
    check_clean(rec, text if text is not None else dumps(rec))


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


def load_xm0(root=ROOT, path=None):
    u"""便 XM0 の記録 → (dict, file の sha256)。無ければ止まる。"""
    p = path or os.path.join(root, XM0_RECORD_REL)
    if not os.path.isfile(p):
        raise Stop(u"**便 XM0 の記録が無い。止める**")
    with io.open(p, encoding="utf-8") as fh:
        return json.loads(fh.read(), object_pairs_hook=od), sha256_file(p)


def run(root=ROOT, docs=None, prior=None, out=None, xm0_path=None, say=print, analyzer=None, pairs=None, want_docs=DOCS_WANT, want_pairs=PAIRS_WANT, docs_list=None, progress=None):
    xm0, xm0_sha = load_xm0(root, xm0_path)
    rec, secret = build_record(docs, prior, want_docs, want_pairs, xm0, xm0_sha, pairs, docs_list, analyzer, progress)
    out = out or os.path.join(root, RECORD_REL)
    write_record(out, rec, secret)
    show_flags(rec, say)
    say(u"-> %s(組 %d)" % (os.path.basename(out), rec[u"材料"][u"組の数"]))
    return rec


def show_flags(rec, say=print):
    u"""封 §4 の旗 6 つを数えて表示する(立った/立たない)。"""
    for k, v in rec[u"先に自分の欠陥を疑う旗"].items():
        say(u"%s: %s" % (k, u"立った" if v[u"旗"] else u"立たない"))


def check(root=ROOT, rec_path=None, xm0_path=None, say=print, want=PAIRS_WANT):
    u"""記録の形・組ごとの数からの導き直し・禁止のものを検査する。置き場は読まない。"""
    p = rec_path or os.path.join(root, RECORD_REL)
    if not os.path.isfile(p):
        raise Stop(u"**在る記録が無い。止める**")
    with io.open(p, encoding="utf-8") as fh:
        text = fh.read()
    rec = json.loads(text, object_pairs_hook=od)
    xm0, _sha = load_xm0(root, xm0_path)
    verify_record(rec, xm0, text, want)
    say(u"--check: 記録の形・組ごとの数からの導き直し・禁止のものの検査は通った(組 %d)" % len(rec[u"書類"]))
    return rec


def dev_summary(tot):
    u"""封 §0 の見たものと並べて読める数(``group_total`` の戻り → 表示用)。"""
    z = tot[u"数"]
    nm = z[u"対応表の名"]
    return od([
        (u"組", tot[u"組"]), (u"断った組", tot[u"断った組"]),
        (u"科目", dict(nm[u"科目"])), (u"軸", dict(nm[u"軸"])), (u"member", dict(nm[u"member"])),
        (u"数の行", od([(u"今年", z[u"型の行"][u"今年"][KN]), (u"名が足りる", z[u"名が足りる行"][KN]), (u"同じ行(日)", sum4(z[u"同じ行(日)"][KN])),
                       (u"同じ行の中身", dict(z[u"同じ行の中身(数)"])), (u"枠が在る", sum4(z[u"枠が在る行"][KN])),
                       (u"今年の期の区分", dict(z[u"今年の行の期の区分"][KN])), (u"同じ行(日)の期の区分", dict(z[u"同じ行(日)"][KN])), (u"枠が在る行の期の区分", dict(z[u"枠が在る行"][KN])),
                       (u"前期とそれより前", sum4(z[u"今年の行の期の区分"][KN], (u"前期", u"それより前")))])),
        (u"文の行", od([(u"今年", z[u"型の行"][u"今年"][KT]), (u"名が足りる", z[u"名が足りる行"][KT]), (u"同じ行(日)", sum4(z[u"同じ行(日)"][KT])), (u"枠が在る", sum4(z[u"枠が在る行"][KT]))])),
        (u"逆向き", dict((k, dict(v)) for k, v in z[u"逆向き"].items())),
        (u"型の外の fact", dict((s, dict(z[u"型の外の fact"][s][u"合計"])) for s in SIDES)),
        (u"対象の fact", dict((s, dict(z[u"対象の fact"][s])) for s in SIDES))])


def dev_run(docs_dir=None, prior_dir=None, say=print, analyzer=None, pairs=None):
    u"""番号 1・2・3 の 3 組だけ(記録は書かない)。(組ごとの数の並び)。番号 4 以上の組は分析しない。"""
    if pairs is None:
        _docs, pairs, _ex = Y.make_pairs(docs_dir or DOCS_DIR, prior_dir or PRIOR_DIR)
    entries = []
    for n, _stem, p, _pstem, pp, _code in pairs:
        if n not in DEV_NOS:
            continue
        ent, _nm = pair_entry(n, p, pp, analyzer)
        entries.append(ent)
    tot = group_total(entries)
    say(json.dumps(dev_summary(tot), ensure_ascii=False, indent=1))
    return entries


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="記録の形・組ごとの数からの導き直し・禁止のものを検査する。置き場は読まない")
    ap.add_argument("--dev", action="store_true", help="番号 1・2・3 の 3 組だけ数えて表示する。記録は書かない")
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--docs", default=None, help="今年の側の置き場(既定は封の字)")
    ap.add_argument("--prior", default=None, help="前の年の側の置き場(既定は封の字)")
    a = ap.parse_args(argv)
    if a.check:
        check(root=a.root)
    elif a.dev:
        dev_run(a.docs, a.prior)
    else:
        run(root=a.root, docs=a.docs, prior=a.prior, progress=lambda s: print(s, file=sys.stderr))


if __name__ == "__main__":
    main()
