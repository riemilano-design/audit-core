# -*- coding: utf-8 -*-
"""欠陥 A(文の「差」を「水準」と比べて VALUE_MISMATCH にしている)の**共通構造と例外**を数える。

人間の指示(2026-10-14): 「欠陥 A の修正を先に設計する。まだ実装はしない」
「30 件すべてが同じ修正で直るとはまだ限らない。まず 30 件の共通構造と例外を明らかにし、
修正の適用条件を定義する」「対象・期間・単位・集計範囲が一致していると確認できる場合に限る。
**数値が近いという理由だけで一致扱いにしない**」。

**実装ではない。`adapters/` を 1 行も触らない。**新しい標本も引いていない。
使うのは取得済み ZIP(2026-10-14 に 1 度だけ取得)と commit 済みの facts だけ。通信しない。

====================================================================
2 つの規則を区別する
====================================================================
``diagnostic``(2026-10-14 の調査で 30 件を数えたときの規則。**仕様には使わない**)
    文の数と「当期・前期の水準の差」が、**文の数の末尾の 0 の桁の 2 倍**以内で一致する。
    これは「数値が近い」だけの規則で、**偶然を拾う**(実際に 2 件拾っていた)。

``spec``(修正の適用条件。**こちらが仕様**)
    次の**全部**を満たすときに限り「文の数は差である」と扱う。
      S1 書かれた桁   文に書かれた金額の表記を読み、**最小の書かれた桁** w を得る
                     (「2億59百万円」は百万円の桁、「6,000千円」は千円の桁)。読めなければ対象外。
      S2 対象の一致   比べる 2 件は**同じ要素**で、**context の member 集合が同じ**。
      S3 期間の隣接   当期と**1 期前**(``CurrentYear`` ↔ ``Prior1Year``)。2 期前は対象外。
      S4 単位の一致   2 件の単位が同じ(いずれも ``JPY``)。
      S5 桁での一致   |文の数 − |当期 − 前期|| ≤ **2 × w**。
                     書類は両方の水準を丸めて書くので、差は最大 2 桁ぶんずれうる。
                     **w は書かれた桁であり、数の大きさから作らない**(ここが diagnostic との違い)。
      S6 文の手がかり 文が、その数を**変化として**述べている(``change_cue`` が「無し」でない)。

S5 と S6 の両方を要求するのが要点である。S5 だけなら偶然を拾い(例 ``S100Z3CI:N088``
「主な内訳は支払利息13,043千円、震災復興支援金6,000千円」の 6,000千円)、
S6 だけなら「差だが水準の差とは一致しない」ものを拾う(例 ``S100Z4R8:N050``
「短期借入金の純減額100百万円」― 残高の差は 110 百万円で、**別の出どころ(CF 計算書)の数**)。

====================================================================
確定した現象(2026-10-14 の実測。**最初の下書きは原因を誤っていた**)
====================================================================
engine は**すでに差を試している**(``recipes.py`` の ``_direct_value_claim`` の差の枝。
``form="derived_value"``・``pointer=[a, b, "formula:a-b"]``)。落ちていたのは帯である。

  * 差の照合は ``V.match_value(fa − fb, target, scale, ...)`` を**水準 1 件ぶんの帯**で呼ぶ
    (``round`` なら ±scale/2、``truncate`` なら 0..scale)。
  * しかし差は**丸めた値 2 件の差**なので、誤差は最大 2 単位ぶん積む
    (書類は水準も差も丸めて書き、差は丸める前の値から計算される)。
  * 実測: 下の ``spec`` が認めた 26 件は、**26 件すべてが +1.000 単位ちょうど**。
    ``truncate`` の帯 ``0 ≤ lo − hi < scale`` の**境界**に落ちていた。
  * engine の ``claim_scale`` は 26 件すべてで「書かれた桁」と**一致**した
    (「2億59百万円」は単位が円と読まれるが ``claim_scale`` は 10^6)。**切り出しの直しは要らない。**

したがって修正は 1 か所である: **差の枝の帯だけを 2 倍にする。**
``change_cue``(文が変化として述べているか)は**仕様には入れない** ― 帯だけで足り、
偽の一致はいずれも帯で落ちる(100百万円 対 110百万円 = 10 単位、6,000千円 対 7,010千円 = 1,010 単位)。
``change_cue`` は**例外を読むための道具**として残す。

``change_cue`` の 3 つの形(**この順に最初に当たったもの**):
  ``compare``   数より前に「比べ/比し/対し」が在り、数の後 12 字以内に増減の語が在る
  ``after``     数の直後 8 字以内に増減の語が在る
  ``noun``      数の直前 10 字以内に「増加額/減少額/増減額/純増額/純減額/純増減額」が在る
  ``none``      どれでもない
"""
import collections
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

BASE = os.environ.get("FINAL8_BASE") or os.path.join(ROOT, "fixtures", "xbrl", "final8")
SPLIT = os.path.join(ROOT, "fixtures", "xbrl", "holdout_p17", "split_2026-10-14.json")
PROFILE = "P16"
RAW = os.path.join(BASE, "defect_a_rows_2026-10-14.json")
OUT = os.path.join(BASE, "defect_a_structure_2026-10-14.json")

SCALES = {"兆": 10 ** 12, "億": 10 ** 8, "百万": 10 ** 6, "万": 10 ** 4, "千": 10 ** 3}
AMOUNT = re.compile(r"((?:\d[\d,]*(?:兆|億|百万|万|千))+|\d[\d,]*)(百万|千)?円")
UP_DOWN = ("増加", "減少", "増", "減")
CHANGE_NOUNS = ("増加額", "減少額", "増減額", "純増額", "純減額", "純増減額")
MONEY_UNITS = {"百万円": 10 ** 6, "千円": 10 ** 3, "円": 1, "億円": 10 ** 8}


def written_amounts(text):
    """文に書かれた金額を ``[(表記, 円の値, 最小の書かれた桁)]`` で返す。"""
    out = []
    for m in AMOUNT.finditer(text):
        parts = re.findall(r"(\d[\d,]*)(兆|億|百万|万|千)?", m.group(1))
        value, last = 0.0, None
        for digits, unit in parts:
            if not digits:
                continue
            n = float(digits.replace(",", ""))
            if unit:
                value += n * SCALES[unit]
                last = SCALES[unit]
            else:
                value += n
                last = 1
        tail = m.group(2)
        if tail and last == 1:
            value *= SCALES[tail]
            last = SCALES[tail]
        out.append((m.group(0), value, last))
    return out


def written_precision(text, stated):
    """``stated``(円)に当たる表記を文から探し、最小の書かれた桁を返す。無ければ None。"""
    for _, value, last in written_amounts(text):
        if abs(value - abs(stated)) < 0.5:
            return last
    return None


def change_cue(text, stated):
    """その数を文が**変化として**述べているか。docstring の順で最初に当たったもの。"""
    pos = None
    for token, value, _ in written_amounts(text):
        if abs(value - abs(stated)) < 0.5:
            pos = text.find(token)
            end = pos + len(token)
            break
    if pos is None:
        return "none"
    before, after = text[:pos], text[end:end + 12]
    if any(w in before for w in ("比べ", "比し", "対し")) and any(w in after for w in UP_DOWN):
        return "compare"
    if any(w in text[end:end + 8] for w in UP_DOWN):
        return "after"
    if any(w in text[max(0, pos - 10):pos] for w in CHANGE_NOUNS):
        return "noun"
    return "none"


def diagnostic_precision(stated):
    """2026-10-14 の調査で使った規則(数の末尾の 0 の桁)。**仕様には使わない。**"""
    n = int(round(abs(stated)))
    if n == 0:
        return 1
    p = 1
    while n % (p * 10) == 0 and p < 10 ** 9:
        p *= 10
    return p


def band_match(diff, target, unit, k, truncate_only=False):
    """``V.match_value`` と同じ符号の扱いで、帯を ``k`` 倍にした照合。

    写し元は ``round`` が ``abs(fv - t) <= unit/2``、``truncate`` が ``0 <= |fv| - |t| < unit``。
    ``k=1`` のとき写し元と同じ判定になる(``mode=None``・``magnitude_truncate=True`` 相当)。

    ``truncate_only=True`` なら **``round`` の帯は写し元のまま**にして ``truncate`` の帯だけ広げる。
    **仕様はこちら。**丸めた値 2 件を引くと誤差は**切り捨ての向きにだけ**積むので、
    ``round`` を広げる理由が無い。実測でも、両側を広げると
    ``S100Z38F:N015``(ずれ −0.893 単位)が入ってきて、これは丸めで説明できない。
    """
    for sign, v in (("", diff), ("abs", abs(diff))):
        t = abs(target) if sign else target
        rk = 1 if truncate_only else k
        if abs(v - t) <= rk * unit / 2.0:
            return (sign + "+round").strip("+")
        if 0 <= abs(v) - abs(t) < k * unit:
            return (sign + "+truncate").strip("+")
    return None


def members(contexts, cid):
    c = contexts.get(cid) or {}
    return frozenset(m.split(":")[-1] for m in (c.get("members") or []))


def spec_verdict(row, contexts):
    """S1〜S6 を順に見て、落ちた最初の条件名を返す。全部通れば "OK"。"""
    w = written_precision(row["span"], row["stated"])
    if w is None:
        return "S1 書かれた桁が読めない"
    if members(contexts, row["ctx"]) != members(contexts, row["ctx_other"]):
        return "S2 member が違う"
    if not ({"CurrentYear", "Prior1Year"} <= {row["period"], row["period_other"]}):
        return "S3 期間が隣接でない"
    if row["unit"] != row["unit_other"]:
        return "S4 単位が違う"
    if row["delta"] is None or abs(row["stated"] - row["delta"]) > 2 * w:
        return "S5 書かれた桁で差に一致しない"
    if change_cue(row["sentence"], row["stated"]) == "none":
        return "S6 文が変化として述べていない"
    return "OK"


def docs_list():
    return json.load(io.open(SPLIT, encoding="utf-8"))["final_eval_sealed"]


def stage_extract():
    from adapters.xbrl import recipes as R, vocabulary as V, edinet, instance as I, extract as E
    rows, money = [], []
    for d in docs_list():
        zb = io.open(edinet.cache_path(d), "rb").read()
        num, _ = R.build_raw_claims(zb, V.PROFILES[PROFILE])
        inst = I.load_instance(zb)
        mdna = I.select_mdna(inst["textblocks"])
        sentences = E.split_sentences(I.strip_html(inst["textblocks"][mdna]), V.PROFILES[PROFILE].paren_sentence)
        vals, units = {}, {}
        for f in json.load(io.open(os.path.join(BASE, "seat", "facts_%s.json" % d), encoding="utf-8")):
            k = (f["要素"].split(":")[-1], f["context"])
            vals[k], units[k] = f["値"], f["単位"]
        byname = {}
        for f in inst["facts"]:
            if (f.get("unit") or "").upper().startswith("JPY"):
                byname.setdefault(f["name"].split(":")[-1], []).append(f)
        for x in num:
            if x.get("unit") not in MONEY_UNITS:
                continue
            # 金額の主張すべて(差の枝の帯を測るため)
            tgt = x["value"] * MONEY_UNITS[x["unit"]]
            pp = x.get("pointer")
            pl = [q for q in ([pp] if isinstance(pp, str) else (pp or [])) if q.startswith("xbrl:")]
            el = pl[0].split("@")[0].split(":")[-1] if pl else None
            cand = byname.get(el, []) if el else []
            diffs = sorted(
                (a["value"] - b["value"]
                 for a in cand if a["context"].startswith("CurrentYear")
                 for b in cand if b["context"].startswith("Prior1Year")),
                key=lambda v: abs(abs(v) - abs(tgt)))[:20]
            money.append({"docID": d, "id": x["id"], "result": x.get("result"),
                          "stated": tgt, "claim_scale": x.get("claim_scale"),
                          "written": written_precision(x.get("span") or "", tgt),
                          "element": el, "pointer_count": len(pl), "diffs": diffs})
            if x.get("result") != "VALUE_MISMATCH":
                continue
            p = x.get("pointer")
            ps = [q for q in ([p] if isinstance(p, str) else (p or [])) if q.startswith("xbrl:")]
            if len(ps) != 1:
                continue
            elem = ps[0].split("@")[0].split(":")[-1]
            ctx = ps[0].split("@", 1)[1]
            period = "CurrentYear" if "CurrentYear" in ctx else ("Prior1Year" if "Prior1Year" in ctx else "?")
            other = (ctx.replace("CurrentYear", "Prior1Year") if period == "CurrentYear"
                     else ctx.replace("Prior1Year", "CurrentYear"))
            a, b = vals.get((elem, ctx)), vals.get((elem, other))
            stated = x["value"] * MONEY_UNITS[x["unit"]]
            rows.append({
                "docID": d, "id": x["id"], "element": elem, "ctx": ctx, "ctx_other": other,
                "period": period,
                "period_other": ("Prior1Year" if period == "CurrentYear" else "CurrentYear"),
                "stated": stated, "level": a, "level_other": b,
                "delta": (abs(a - b) if a is not None and b is not None else None),
                "unit": units.get((elem, ctx)), "unit_other": units.get((elem, other)),
                "span": x.get("span") or "", "sentence": sentences[x["sentence"]],
                "subject": x.get("subject")})
    rows.sort(key=lambda r: (r["docID"], r["id"]))
    money.sort(key=lambda r: (r["docID"], r["id"]))
    out = {"purpose": "8 書類の金額の num 主張(rows は VALUE_MISMATCH で pointer が 1 件のもの、"
                      "money は金額の主張すべてと差の候補)",
           "profile": PROFILE, "how": "取得済み ZIP から build_raw_claims を回し直した。通信しない",
           "rows": rows, "money": money}
    with io.open(RAW, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("%d 件 -> %s" % (len(rows), RAW))


def stage_classify():
    raw = json.load(io.open(RAW, encoding="utf-8"))["rows"]
    ctxs = {d: json.load(io.open(os.path.join(BASE, "seat", "contexts_%s.json" % d), encoding="utf-8"))
            for d in docs_list()}
    diag, spec, cues, dropped = [], [], collections.Counter(), collections.Counter()
    spec_set = set()
    for r in raw:
        if r["delta"] is not None and abs(r["stated"] - r["delta"]) <= 2 * diagnostic_precision(r["stated"]):
            diag.append(r["docID"] + ":" + r["id"])
        v = spec_verdict(r, ctxs[r["docID"]])
        if v == "OK":
            spec.append(r["docID"] + ":" + r["id"])
            spec_set.add(r["docID"] + ":" + r["id"])
            cues[change_cue(r["sentence"], r["stated"])] += 1
    for rid in diag:
        if rid not in spec:
            r = [x for x in raw if x["docID"] + ":" + x["id"] == rid][0]
            dropped[spec_verdict(r, ctxs[r["docID"]])] += 1
    added = [rid for rid in spec if rid not in diag]

    money = json.load(io.open(RAW, encoding="utf-8"))["money"]
    band, offsets, scale_agree = collections.Counter(), collections.Counter(), collections.Counter()
    for mo in money:
        u = mo["claim_scale"]
        if not u:
            band[(str(mo["result"]), "帯が決まらない")] += 1
            continue
        now = any(band_match(v, mo["stated"], u, 1) for v in mo["diffs"])
        both = any(band_match(v, mo["stated"], u, 2) for v in mo["diffs"])
        spec_band = any(band_match(v, mo["stated"], u, 2, truncate_only=True) for v in mo["diffs"])
        band[(str(mo["result"]), "今も当たる" if now else
              ("仕様(切り捨てだけ 2 倍)で当たる" if spec_band else
               ("両側 2 倍でだけ当たる" if both else "2 倍でも当たらない")))] += 1
        if mo["written"] is not None:
            scale_agree["claim_scale == 書かれた桁" if u == mo["written"] else "違う"] += 1
    for r in raw:
        rid = r["docID"] + ":" + r["id"]
        if rid not in spec_set or r["delta"] is None:
            continue
        w = written_precision(r["span"], r["stated"])
        offsets[round((r["delta"] - r["stated"]) / float(w), 3)] += 1

    print("金額の VALUE_MISMATCH(pointer 1 件): %d 件" % len(raw))
    print("diagnostic 規則で A と数えた件数 : %d" % len(diag))
    print("spec 規則で A と認める件数        : %d" % len(spec))
    print("\n[diagnostic が拾って spec が落とす行の理由]")
    for k, n in sorted(dropped.items()):
        print("  %-34s %d" % (k, n))
    print("\n[spec が認めた行の、文の手がかりの形]")
    for k, n in sorted(cues.items(), key=lambda kv: -kv[1]):
        print("  %-10s %d" % (k, n))
    print("\n[spec だけが拾う行] %s" % (added or "無し"))
    print("\n[spec の行の『差 − 文の数』を書かれた桁で割った値]")
    for k, n in sorted(offsets.items()):
        print("  %+.3f 単位  %d 件" % (k, n))
    print("\n[差の枝の帯を 2 倍にしたら何が動くか(金額の主張すべて)]")
    for k, n in sorted(band.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        print("  %-16s %-26s %3d" % (k[0], k[1], n))
    print("  %-43s %3d" % ("合計", sum(band.values())))
    print("\n[engine の claim_scale と書かれた桁]")
    for k, n in sorted(scale_agree.items()):
        print("  %-28s %d" % (k, n))
    out = {"purpose": "欠陥 A の共通構造と例外(設計のための数。合否の判定ではない)",
           "profile": PROFILE, "money_mismatch_rows": len(raw),
           "diagnostic_count": len(diag), "spec_count": len(spec),
           "dropped_reasons": dict(dropped), "cue_counts": dict(cues),
           "spec_only": added, "diagnostic_ids": diag, "spec_ids": spec,
           "offset_units": {"%+.3f" % k: v for k, v in sorted(offsets.items())},
           "band_counts": {" | ".join(k): v for k, v in sorted(band.items())},
           "scale_agreement": dict(scale_agree)}
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("\n->", OUT)
    return out


def stage_check():
    out = stage_classify()
    rec = json.load(io.open(OUT, encoding="utf-8"))
    assert rec == json.loads(json.dumps(out, ensure_ascii=False)), "fixture が再現しない"
    print("再現 OK")


def main():
    stage = sys.argv[1] if len(sys.argv) > 1 else "classify"
    {"extract": stage_extract, "classify": stage_classify, "check": stage_check}[stage]()


if __name__ == "__main__":
    main()
