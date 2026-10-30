# -*- coding: utf-8 -*-
"""比較実験2a §4 の採点器(腕の engine 出力 vs 確定ラベル)。仕様を固定した後に書く。
回答(engineの実行結果)を1件も読む前に、この仕様とテスト(本ファイル末尾のidentity/mutation)を書いた。
sha256はこの後に別途記録する。

定義(後から変えない。experiment_2a_preregistration_draft.md §3・§4 と
experiment_2a_preflight_audit_2026-10-13.md 項目4の指摘を反映):

* 入力1(腕の出力): {"<id>": {"state": "<GROUNDED|VALUE_MISMATCH|UNVERIFIABLE|POINTER_NOT_FOUND>",
                           "pointers": ["xbrl:<prefix>:<local>@<context>", "builtin:...", "formula:...", ...]}}
  pointers は tests.golden._instrument.run_verification が返す形そのもの(リストの各要素が1本の文字列)。
  "xbrl:" で始まらない要素(builtin:/formula:)は fact ではないので候補集合には入れない。
* 入力2(確定ラベル): e2_labels_P_merged_2026-10-13.json の labels 配列。"分類"が"確定"で始まる行だけを対象にする
  (不一致・判定不能は L から除く。登録した分母の定義のとおり)。
  各行の "fact" フィールドは2席の独立判定が一致した**厳密**(接頭辞を除いた局所名。SummaryOfBusinessResults等の
  接尾辞は除去していない)の (要素, context) 集合。"同値の他の候補" は型5露出の記録であり、
  一致判定には使わない(preflight項目4の指摘どおり、同値類はこの採点器のcanon()だけで適用する)。
* pointer の解析: "xbrl:" を取り、残りを最初の ":" で (接頭辞, 残り) に分け、残りを "@" で (局所名, context) に分ける。
  接頭辞は数字・ハイフンを含みうる(例 "jpcrp030000-asr_E36539-000")が、局所名自体に ":" は出現しないので
  この分割で一意に決まる。**解析できないトークン(xbrl:で始まるが上記の形に当たらないもの)が1件でもあれば、
  件数を標準エラーに印字してからAssertionErrorで停止する(0件と数えない)。**
* 厳密一致: 腕のpointerから作った (局所名, context) の集合が、ラベルの "fact" の集合と**集合として完全一致**。
* 同値類v0一致: 両方の集合に canon() (接頭辞除去は済み。接尾辞 "SummaryOfBusinessResults" を除去し、
  {"TotalAssets": "Assets"} の別名表を適用) を要素にだけ適用した集合が完全一致。
  厳密一致は同値類v0一致を含む(厳密ならv0も必ず一致)。
* L(分母) = 確定ラベルの件数。G(腕) = 腕がGROUNDEDにしたClaimのうちLに含まれる件数。
* E2-件数(規則) = GROUNDED ∩ L のうち、その規則で不一致の件数。分母はLで固定。
* E2-率(規則) = E2-件数(規則) / G(腕)。
* **厳密と同値類v0の両方を必ず併記する**(どちらか一方だけを「E2」として出さない)。
* 型5露出 = ラベル行の "同値の他の候補" が空でないこと(記録のみ。一致判定には使わない)。
* audit_core / adapters は import しない(測る対象の外)。

恒等の予測(読む前に書く): ラベルの "fact" をそのまま腕のpointerとして渡せば、
厳密E2-件数=0・同値類v0 E2-件数=0・G(腕)=L・E1'(一致件数)=L。外れたら採点器の欠陥。
変異の予測(3本、全部1件ずつ変える):
  (1) 1行のcontextを変える(当期→前期) → その行だけ厳密・v0とも不一致になり、両方のE2-件数が+1。
  (2) 1行のpointerを1本消す(対のfactの片方を欠落させる) → その行の集合が小さくなり不一致、両方+1。
  (3) 1行の要素名にSummaryOfBusinessResults接尾辞を足す(canon同値のまま) → 厳密E2-件数のみ+1、
      同値類v0 E2-件数は変わらない(canon()が吸収する)。この3本目が「両方を併記する」設計の確認になる。
"""
import json, sys, os, collections

XBRL_PREFIX = "xbrl:"


def canon(local_name):
    e = local_name
    if e.endswith("SummaryOfBusinessResults"):
        e = e[: -len("SummaryOfBusinessResults")]
    return {"TotalAssets": "Assets"}.get(e, e)


def parse_pointer(p):
    """'xbrl:<prefix>:<local>@<context>' -> (local, context)。fact を表さないものは None。"""
    if not p.startswith(XBRL_PREFIX):
        return None
    rest = p[len(XBRL_PREFIX):]
    if ":" not in rest or "@" not in rest:
        raise ValueError(p)
    _prefix, rest2 = rest.split(":", 1)
    if "@" not in rest2:
        raise ValueError(p)
    local, context = rest2.split("@", 1)
    return (local, context)


def facts_from_pointers(pointers):
    out = set()
    bad = []
    for p in pointers:
        if not p.startswith(XBRL_PREFIX):
            continue  # builtin:/formula: は fact ではない
        try:
            out.add(parse_pointer(p))
        except ValueError:
            bad.append(p)
    if bad:
        sys.stderr.write("UNPARSEABLE_POINTERS=%d %r\n" % (len(bad), bad))
        raise AssertionError("unparseable pointer tokens: %d" % len(bad))
    return out


def load_labels(label_path):
    d = json.load(open(label_path))
    out = {}
    for row in d["labels"]:
        if not row["分類"].startswith("確定"):
            continue
        fact_set = set(tuple(x) for x in row["fact"])
        exposure = bool(row.get("同値の他の候補"))
        out[row["id"]] = {"fact": fact_set, "exposure": exposure}
    return out


def score(arm_results, labels):
    """arm_results: {"<id>": {"state":..., "pointers":[...]}}。labels: load_labels() の出力。"""
    L = len(labels)
    rows = []
    for cid, lab in labels.items():
        r = arm_results.get(cid)
        state = r["state"] if r else None
        arm_facts = facts_from_pointers(r["pointers"]) if r else set()
        strict_ok = (arm_facts == lab["fact"])
        label_canon = {(canon(e), c) for e, c in lab["fact"]}
        arm_canon = {(canon(e), c) for e, c in arm_facts}
        v0_ok = (arm_canon == label_canon)
        rows.append({
            "id": cid, "state": state, "strict_match": strict_ok, "v0_match": v0_ok,
            "type5_exposure": lab["exposure"],
        })
    g = sum(1 for r in rows if r["state"] == "GROUNDED")
    e2_strict = sum(1 for r in rows if r["state"] == "GROUNDED" and not r["strict_match"])
    e2_v0 = sum(1 for r in rows if r["state"] == "GROUNDED" and not r["v0_match"])
    e1_strict = sum(1 for r in rows if r["state"] == "GROUNDED" and r["strict_match"])
    report = {
        "L": L, "G": g,
        "E2_count_strict": e2_strict, "E2_count_v0": e2_v0,
        "E2_rate_strict": (e2_strict / g) if g else None,
        "E2_rate_v0": (e2_v0 / g) if g else None,
        "E1prime_strict": e1_strict,
        "rows": rows,
    }
    return report


def main(label_path, arm_json_path, out_path):
    labels = load_labels(label_path)
    arm_results = json.load(open(arm_json_path))
    rep = score(arm_results, labels)
    json.dump(rep, open(out_path, "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k != "rows"}, ensure_ascii=False))


if __name__ == "__main__":
    main(*sys.argv[1:4])
