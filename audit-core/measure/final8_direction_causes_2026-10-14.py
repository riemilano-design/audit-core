# -*- coding: utf-8 -*-
"""Q1(最終評価用 8 書類)の「方向の主張」の E2 20 件の**原因を分ける**。

人間の指示(2026-10-14): 「既存の 20 件を固定する。Q1 の確定ラベルと dump を使い、
対象を追加・除外しない」「原因を 3 候補に分ける」「1 件ごとに証拠を記録する。主原因・根拠・
複数原因の可能性・判定不能を区別する」「無理に 20 件すべてを分類しない」。

**これは合否の判定ではない。**合格線は無い。新しい標本も取らない。
対象は docs/FINAL_EVAL_8_RESULT_2026-10-14.md §1-3 の「方向の形 E2 = 20 件」そのもの
(= 席 1 の形が「符号・方向」で、P16 が GROUNDED にし、厳密一致しなかった行)。

人間が挙げた 3 候補(docs/DIRECTION_CLAIMS_OPEN_ISSUE_2026-10-14.md §2):
  (a) 対の取り方      「増収」が当期と前期のどの 2 つの fact の差を指すか
  (b) member の選び方  セグメントの文を全社の数に(あるいは逆に)結ぶ
  (c) 語の掛かり先    「増収増益」の「増収」がどの主語に掛かるか

====================================================================
段 1: 機械で決まる分け方(**文を読む前に書いた**)
====================================================================
``arm``(engine が結んだ fact 集合)と ``label``(2 席が一致した fact 集合)だけで決める。
比べる単位は ``(canon した要素名, context)``。上から最初に当たったものを採る。

  0. ``alias``    canon 要素名の集合が同じ かつ context の集合が同じ
                  → **3 候補のどれでもない**。同値類 v0 の表記違いが厳密一致で落ちただけ。
  1. ``member``   canon 要素名の集合が同じ かつ context の member の集合が違う
                  → **(b)**。これは機械で確定する。
  2. ``overlap``  arm と label が fact を 1 件以上共有する(かつ集合は違う)
                  → **(a) が主**。engine は label の fact の一部を当てており、
                     相手(もう一方の fact)の取り方が違う。
  3. ``disjoint`` arm と label が 1 件も共有しない
                  → **機械では決まらない。(c) か、3 候補の外か、判定不能。段 2 へ。**

当たる例・当たらない例(**先に書く**):
  * arm {GrossProfit CY, GrossProfit PY} / label {GrossProfit CY, GrossProfit PY,
    SGA CY, SGA PY} → ``overlap``。共有 2 件・差 2 件。(a)。
  * arm {OperatingIncome CY, PY(全社)} / label 同要素の Segment member → ``member``。(b)。
  * arm {AdvancePayments CF} / label {Inventories CF} → ``disjoint``。これだけでは
    「語の掛かり先を間違えた」とは言えない(文に主語候補が 1 つしか無いなら別の誤り)。段 2。

====================================================================
段 2: 文を読んで決める分け方(**読む前に書いた**)
====================================================================
``disjoint`` の行だけ、材料の ``文``(席に見せた文そのもの)を読んで次を割り当てる。
``overlap`` の行は主原因を (a) で固定し、(c) の**併存の可能性**だけを見る。

  (c) 語の掛かり先 … 文に**金額項目を指す語が 2 つ以上**在り、arm の要素はその一方に、
      label の要素は**別の**一方に対応する。
  3 候補の外(``no_word``) … arm の要素に対応する語が**文に無い**。
      語の掛かり先ではなく、要素の同定そのものの誤り。
  判定不能(``undecided``) … 上のどちらとも言えない。

**根拠の書き方の縛り**: 1 行ごとに、arm 側に対応する語 ``arm_word`` と label 側に対応する語
``label_word`` を**文に実在する部分文字列として**引く。``build`` 段がこれを機械で検査し、
文に無い語を引いたら落ちる(``no_word`` の行は ``arm_word`` を空にする)。
これで「自分の読みに都合のよい語を作る」道を塞ぐ。

====================================================================
段 3: 読みに依らず機械で測る 3 つの軸(**読んだ後に足した。読みの結果は使わない**)
====================================================================
  軸 1 「主張に付いた数」   材料の ``対象の数(文中の表記)`` が null かどうか。
        方向の形は定義上すべて null になるはずで、それ自体が「値で反証できない」ことの意味。
  軸 2 「文に在る金額」     文の ``9,648百万円`` のような表記を円に直し、arm 側・label 側の
        fact の値が当たるかを見る。書類は下位桁を切り捨てて書くので**切り捨てでも四捨五入でも
        当たりとする**(この許容を入れないと 53,021.694 百万円が 53,021 に当たらず、
        自分の照合の穴で 0 を作る)。
  軸 3 「同じ量か」         arm が同一要素の当期・前期 2 件なら差を取り、label 側の量と一致するか。
        「engine は同じ量を別の経路で出しただけ」という弁護が成り立つ行を数える。

====================================================================
開示: この規則を書く前に見てしまったもの
====================================================================
fixture ``e2_types_2026-10-14.json`` の先頭 8 行の ``arm``/``label`` を、形を調べる段で
印字して見た(S100Z4LC:H-017/H-031/H-055/H-092, S100Z40H:H-019/H-024/H-053/H-055)。
**文は読んでいない**が、段 1 の例に挙げた 3 つはこの 8 行から採った。
段 1 の規則はこの 8 行に合わせて作ったのではなく、人間の 3 候補を機械で書ける形に落としたものだが、
**この開示をもって偏りの可能性を記録する**。
"""
import collections
import io
import math
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import grounds_eval as GE  # noqa: E402

BASE = os.environ.get("FINAL8_BASE") or os.path.join(ROOT, "fixtures", "xbrl", "final8")
SPLIT = os.path.join(ROOT, "fixtures", "xbrl", "holdout_p17", "split_2026-10-14.json")
PROFILE = "P16"
OUT = os.path.join(BASE, "direction_causes_2026-10-14.json")
READING = os.path.join(BASE, "direction_reading_2026-10-14.json")

BUCKETS = ("alias", "member", "overlap", "disjoint")
VERDICTS = ("c_word", "no_word", "undecided")


def members(contexts, cid):
    c = contexts.get(cid) or {}
    return frozenset(m.split(":")[-1] for m in (c.get("members") or []))


def key(pairs):
    return {(GE.canon(e), c) for e, c in pairs}


def machine_bucket(row, contexts):
    """段 1。arm/label だけで決まる分け方(文は見ない)。"""
    ka, kl = key(row["arm"]), key(row["label"])
    ea = {GE.canon(e) for e, _ in row["arm"]}
    el = {GE.canon(e) for e, _ in row["label"]}
    ca = {c for _, c in row["arm"]}
    cl = {c for _, c in row["label"]}
    ma = {members(contexts, c) for _, c in row["arm"]}
    ml = {members(contexts, c) for _, c in row["label"]}
    if ea == el and ca == cl:
        return BUCKETS[0]
    if ea == el and ma != ml:
        return BUCKETS[1]
    if ka & kl:
        return BUCKETS[2]
    return BUCKETS[3]


def load():
    docs = json.load(io.open(SPLIT, encoding="utf-8"))["final_eval_sealed"]
    labels = GE.load_labels(os.path.join(BASE, "labels_final8_2026-10-14.json"))
    dump = {}
    for d in docs:
        dump.update(json.load(io.open(
            os.path.join(BASE, "commander_only", "dump_%s_%s.json" % (PROFILE, d)), encoding="utf-8")))
    ctx = {d: json.load(io.open(os.path.join(BASE, "seat", "contexts_%s.json" % d), encoding="utf-8"))
           for d in docs}
    sent = {}
    for d in docs:
        mat = json.load(io.open(os.path.join(BASE, "seat", "material_%s.json" % d), encoding="utf-8"))
        for r in mat["行"]:
            sent["%s:%s" % (d, r["行の鍵"])] = r["文"]
    return docs, labels, dump, ctx, sent


def extra(docs):
    """fact の値、2 席の形、主張に付いた数。どれも席に見せた材料か書類そのもの。"""
    vals, forms, nums = {}, {}, {}
    for d in docs:
        for f in json.load(io.open(os.path.join(BASE, "seat", "facts_%s.json" % d), encoding="utf-8")):
            vals[(d, f["要素"].split(":")[-1], f["context"])] = f["値"]
        for r in json.load(io.open(os.path.join(BASE, "seat", "material_%s.json" % d), encoding="utf-8"))["行"]:
            nums["%s:%s" % (d, r["行の鍵"])] = r["対象の数(文中の表記)"]
    lab = json.load(io.open(os.path.join(BASE, "labels_final8_2026-10-14.json"), encoding="utf-8"))
    for row in lab["labels"]:
        forms[row["id"]] = row.get("形") or []
    return vals, forms, nums


def direction_e2(dump, labels, ctx):
    """Q1 の定義そのままの「方向の形の E2」。追加も除外もしない。"""
    out = []
    for r in GE.score(dump, labels):
        if r["state"] != "GROUNDED" or r["strict"] or not r["direction"]:
            continue
        d = r["id"].split(":", 1)[0]
        out.append({"id": r["id"], "docID": d, "bucket": machine_bucket(r, ctx[d]),
                    "arm": [list(x) for x in r["arm"]], "label": [list(x) for x in r["label"]]})
    out.sort(key=lambda x: x["id"])
    return out


def stage_rows():
    docs, labels, dump, ctx, sent = load()
    rows = direction_e2(dump, labels, ctx)
    print("方向の形の E2: %d 件(Q1 の記録は 20 件)" % len(rows))
    c = collections.Counter(r["bucket"] for r in rows)
    for b in BUCKETS:
        print("  %-9s %2d" % (b, c[b]))
    print()
    for r in rows:
        print("%-18s %-9s arm=%s" % (r["id"], r["bucket"], r["arm"]))
        print("%-18s %-9s lab=%s" % ("", "", r["label"]))
    return rows


def stage_read():
    docs, labels, dump, ctx, sent = load()
    rows = direction_e2(dump, labels, ctx)
    for r in rows:
        print("### %s  [%s]" % (r["id"], r["bucket"]))
        print("文: %s" % sent[r["id"]])
        print("arm  : %s" % r["arm"])
        print("label: %s" % r["label"])
        for e, cid in r["arm"] + r["label"]:
            m = sorted(members(ctx[r["docID"]], cid))
            print("   ctx %-70s members=%s" % (cid, m))
        print()


def amounts(sentence):
    """文の中の金額表記を ``(数, 桁)`` で返す。"""
    out = set()
    for m in re.finditer(r"([0-9][0-9,]*(?:\.[0-9]+)?)\s*(百万円|千円|円)", sentence):
        out.add((float(m.group(1).replace(",", "")), {"百万円": 10 ** 6, "千円": 10 ** 3, "円": 1}[m.group(2)]))
    return out


def in_sentence(value, amts):
    """fact の値が文の金額表記に当たるか(切り捨て・四捨五入のどちらでも当たり)。"""
    if value is None:
        return False
    a = abs(value)
    for num, sc in amts:
        if abs(math.floor(a / sc) - num) < 0.5 or abs(round(a / sc) - num) < 0.5:
            return True
    return False


def number_axis(row, vals, sentence):
    """軸 2。label 側だけが文に在れば「数を付ければ落ちた」。"""
    amts = amounts(sentence)
    if not amts:
        return "文に金額が無い"
    ap = any(in_sentence(vals.get((row["docID"], e, c)), amts) for e, c in row["arm"])
    lp = any(in_sentence(vals.get((row["docID"], e, c)), amts) for e, c in row["label"])
    if lp and not ap:
        return "ラベルの数だけ文に在る(数を付ければ落ちた)"
    if lp and ap:
        return "両方の数が文に在る(どちらの数かを決める必要)"
    if ap and not lp:
        return "engine の数だけ文に在る"
    return "どちらの数も文に無い"


def same_quantity(row, vals):
    """軸 3。arm が同一要素の 2 件なら差を取り、label 側の量と比べる。"""
    def delta(pairs):
        xs = [vals.get((row["docID"], e, c)) for e, c in pairs]
        if len(pairs) == 2 and len({e for e, _ in pairs}) == 1 and all(x is not None for x in xs):
            return abs(xs[0] - xs[1])
        return None
    da = delta(row["arm"])
    if da is None:
        return None
    dl = delta(row["label"])
    if dl is not None:
        return abs(da - dl) < 1.0
    if len(row["label"]) == 1:
        lv = vals.get((row["docID"],) + tuple(row["label"][0]))
        if lv is not None:
            return abs(da - abs(lv)) < 1.0
    return None


def stage_build():
    docs, labels, dump, ctx, sent = load()
    vals, forms, nums = extra(docs)
    rows = direction_e2(dump, labels, ctx)
    reading = json.load(io.open(READING, encoding="utf-8"))["rows"]
    need = {r["id"] for r in rows if r["bucket"] in ("overlap", "disjoint")}
    have = set(reading)
    if need != have:
        raise AssertionError("読む対象が合わない: 足りない %s / 余分 %s"
                             % (sorted(need - have), sorted(have - need)))
    for rid, rd in sorted(reading.items()):
        s = sent[rid]
        for fld in ("arm_word", "label_word"):
            w = rd.get(fld) or ""
            if w and w not in s:
                raise AssertionError("%s の %s %r は文に無い" % (rid, fld, w))
        if rd["verdict"] not in VERDICTS and rd["verdict"] != "":
            raise AssertionError("%s の verdict が enum 外: %r" % (rid, rd["verdict"]))

    out_rows = []
    counts = collections.Counter()
    axis2 = collections.Counter()
    cross = collections.Counter()
    for r in rows:
        rd = reading.get(r["id"]) or {}
        if r["bucket"] == "alias":
            cause = "3 候補の外(同値類の表記違い)"
        elif r["bucket"] == "member":
            cause = "(b) member の選び方"
        elif r["bucket"] == "overlap":
            cause = "(a) 対の取り方"
        else:
            cause = {"c_word": "(c) 語の掛かり先",
                     "no_word": "3 候補の外(要素の同定の誤り)",
                     "undecided": "判定不能"}[rd.get("verdict")]
        co = []
        if r["bucket"] == "overlap" and rd.get("verdict") == "c_word":
            co.append("(c) 語の掛かり先")
        if r["bucket"] == "disjoint" and len(r["arm"]) != len(r["label"]):
            co.append("(a) 対の取り方(結んだ fact の数が違う)")
        a2 = number_axis(r, vals, sent[r["id"]])
        sq = same_quantity(r, vals)
        counts[cause] += 1
        axis2[a2] += 1
        cross[(cause, a2)] += 1
        out_rows.append(dict(r, cause=cause, co_causes=co, number_axis=a2, same_quantity=sq,
                             claim_number=nums[r["id"]],
                             seat2_direction=forms[r["id"]][1] == "符号・方向" if len(forms[r["id"]]) > 1 else None,
                             arm_word=rd.get("arm_word", ""), label_word=rd.get("label_word", ""),
                             reason=rd.get("reason", "")))

    # 軸 1: GROUNDED 全体で「主張に付いた数」の有無 x 形 x E1'/E2
    axis1 = collections.Counter()
    for r in GE.score(dump, labels):
        if r["state"] != "GROUNDED":
            continue
        axis1[("方向" if r["direction"] else "値の形",
               "数あり" if nums[r["id"]] is not None else "数なし",
               "E1'" if r["strict"] else "E2")] += 1

    # 止める枝の費用: 方向の E1' 32 件に「文の金額で照合する」を当てたら何件が止まるか
    cost = collections.Counter()
    for r in GE.score(dump, labels):
        if r["state"] != "GROUNDED" or not r["strict"] or not r["direction"]:
            continue
        d = r["id"].split(":", 1)[0]
        amts = amounts(sent[r["id"]])
        if not amts:
            cost["文に金額が無い(影響なし)"] += 1
        elif any(in_sentence(vals.get((d, e, c)), amts) for e, c in r["arm"]):
            cost["結んだ fact の値が文に在る(通る)"] += 1
        else:
            cost["結んだ fact の値が文に無い(止まる恐れ)"] += 1

    co_counts = collections.Counter()
    for r in out_rows:
        for c in r["co_causes"]:
            co_counts[c] += 1
    sq_counts = collections.Counter(str(r["same_quantity"]) for r in out_rows)
    seat2 = sum(1 for r in out_rows if r["seat2_direction"])

    def table(title, c, total=None):
        print("\n[%s]" % title)
        for k, n in sorted(c.items(), key=lambda kv: (-kv[1], str(kv[0]))):
            print("  %-56s %3d" % (k if isinstance(k, str) else " / ".join(map(str, k)), n))
        if total is not None:
            print("  %-56s %3d" % ("合計", sum(c.values())))

    print("方向の形の E2 = %d 件(分母。Q1 の記録と同じ)" % len(out_rows))
    table("段 1+2: 主原因(1 件 1 つ)", counts, True)
    table("併存の可能性(重複計上。上の表には足さない)", co_counts)
    table("軸 2: 文に在る金額との関係", axis2, True)
    table("軸 2 x 主原因", cross, True)
    table("軸 3: engine と label が同じ量か(True/False/None=判定の形に無い)", sq_counts, True)
    table("軸 1: GROUNDED 全体 — 主張に付いた数 x 形 x 判定", axis1, True)
    table("止める枝の費用: 方向の E1' 32 件に文の金額照合を当てたら", cost, True)
    print("\n席 2 の形でも「符号・方向」だった行: %d / %d" % (seat2, len(out_rows)))

    out = {"purpose": "Q1 の方向の形の E2 20 件の原因分け(合否の判定ではない)",
           "profile": PROFILE, "total": len(out_rows),
           "bucket_counts": {b: sum(1 for r in out_rows if r["bucket"] == b) for b in BUCKETS},
           "cause_counts": dict(counts), "co_cause_counts": dict(co_counts),
           "number_axis_counts": dict(axis2),
           "cross_counts": {" | ".join(k): v for k, v in sorted(cross.items())},
           "same_quantity_counts": dict(sq_counts),
           "axis1_counts": {" | ".join(k): v for k, v in sorted(axis1.items())},
           "stop_cost_counts": dict(cost),
           "seat2_direction_rows": seat2,
           "rows": out_rows}
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("\n->", OUT)
    return out


def stage_check():
    out = stage_build()
    rec = json.load(io.open(OUT, encoding="utf-8"))
    assert rec == json.loads(json.dumps(out, ensure_ascii=False)), "fixture が再現しない"
    print("再現 OK")


def main():
    stage = sys.argv[1] if len(sys.argv) > 1 else "rows"
    {"rows": stage_rows, "read": stage_read, "build": stage_build, "check": stage_check}[stage]()


if __name__ == "__main__":
    main()
