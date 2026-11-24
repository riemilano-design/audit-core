# -*- coding: utf-8 -*-
"""便 TR1: 基準 A(生の XBRL から engine の読み方で作る facts)と、取り出しの誤りを入れた材料・基準 B を作る(封 §1・§2)。

使い方: python3 -I build_tr1.py <audit-core の folder> <RD2 の根> <TR0 の根> <TR1 の根>
書くもの:
  <TR1 の根>/A/{n}.json   基準 A: zip の fact 全部と、項目の鍵 → 要素・枠・値・精度(AI を使わない)
  <TR1 の根>/mat/{n}.json 書く席に渡す材料(TR0 の材料の 2 項目を取り出しの誤りの形に替えたもの)
  <TR1 の根>/B/{n}.json   基準 B: 誤りを入れた材料から TR0 と同じ作り方の facts と状態
  <TR1 の根>/corrupt/{n}.json 入れた誤り(項目・期・形。集計だけが読む)
zip は信頼しない data として読むだけ。誤りの形を選ぶのに RD2 の正解の folder の 他の読み.json を読む(基準には使わない)。
"""
import copy
import hashlib
import json
import os
import sys

AC, RD2, TR0, OUT = sys.argv[1:5]
sys.path.insert(0, AC)
sys.path.insert(0, os.path.join(AC, "core", "py"))
from adapters.xbrl import vocabulary as V  # noqa: E402  (表を読むだけ)
from adapters.xbrl.instance import load_instance  # noqa: E402  (読むだけ)

CACHE = os.path.expanduser("~/.cache/audit-core")
ROWS = {str(31 + i): str(7 + i) for i in range(11)}
CTX = {"当期": "CurrentYearDuration", "前期": "Prior1YearDuration", "当期末": "CurrentYearInstant", "前期末": "Prior1YearInstant"}
NONCON = "_NonConsolidatedMember"
SCOPE = ["売上高_当期", "売上高_前期", "営業利益_当期", "営業利益_前期", "経常利益_当期", "当期純利益_当期",
         "減価償却費_当期", "現金及び預金_当期末", "流動資産合計_当期末", "資産合計_当期末", "短期借入金_当期末",
         "長期借入金_当期末", "負債合計_当期末", "純資産合計_当期末", "純資産合計_前期末", "期末の従業員数_当期末"]
WORD = {"売上高": "売上高", "営業利益": "営業利益", "経常利益": "経常利益", "減価償却費": "減価償却費",
        "現金及び預金": "現金及び預金", "資産合計": "資産合計", "長期借入金": "長期借入金", "負債合計": "負債合計",
        "純資産合計": "純資産", "期末の従業員数": "従業員数"}
ADDED = {"流動資産合計": ["CurrentAssets"], "短期借入金": ["ShortTermLoansPayable"]}  # 封 §1 で固定した 2 行


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def dump(obj, *parts):
    p = os.path.join(OUT, *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def vocab():
    first = {}
    for s in V.PROFILES["P33E"].subjects:
        first.setdefault(s[0], list(s[1]))
    return first


def elements(label, scope, table):
    if label in ADDED:
        return ADDED[label]
    if label == "当期純利益":
        return table["親会社株主に帰属する当期純利益" if scope == "連結" else "当期純利益"]
    return table[WORD[label]]


def main():
    table = vocab()
    d = load(os.path.join(AC, "fixtures/xbrl/tanshin/fetched_2026-11-09.json"))
    rows = {str(r["#"]): r for r in d["行"]}
    sha2path = {}
    for sub in ("edinet", "edinet-fresh-2026-10-21", "edinet-prior-2026-11-02"):
        for f in os.listdir(os.path.join(CACHE, sub)):
            p = os.path.join(CACHE, sub, f)
            sha2path[hashlib.sha256(open(p, "rb").read()).hexdigest()] = p
    for n, key in ROWS.items():
        # ---- 基準 A(AI を使わない)
        inst = load_instance(open(sha2path[rows[key]["有報の ZIP の sha256"]], "rb").read())
        facts = [{"name": f["name"], "context": f["context"], "unit": f.get("unit"), "decimals": f.get("decimals"),
                  "value": f["value"]} for f in inst["facts"] if isinstance(f.get("value"), (int, float))]
        state0 = load(os.path.join(TR0, "state", n + ".json"))
        scope = state0.get("範囲")
        amap = {}
        for item in SCOPE:
            label, period = item.split("_")
            ctx = CTX[period] + ("" if scope == "連結" else NONCON)
            if label == "期末の従業員数" and scope != "連結":
                if any(f["context"] == CTX[period] and f["name"].split(":")[-1] == "NumberOfEmployees" for f in facts):
                    ctx = CTX[period]
            hit = None
            for el in elements(label, scope, table):
                hit = next((f for f in facts if f["name"].split(":")[-1] == el and f["context"] == ctx), None)
                if hit:
                    break
            if hit:
                amap["%s@%s" % (label, CTX[period])] = {"pointer": "%s@%s" % (hit["name"], hit["context"]),
                                                        "要素": hit["name"].split(":")[-1], "枠": hit["context"],
                                                        "期": period, "範囲": scope, "値": hit["value"],
                                                        "decimals": hit.get("decimals"), "unit": hit.get("unit")}
        dump({"範囲": scope, "facts": facts, "map": amap}, "A", n + ".json")
        # ---- 取り出しの誤りを入れた材料と基準 B
        mat = load(os.path.join(TR0, "mat", n + ".json"))
        other = load(os.path.join(RD2, "co" + n, "正解", "他の読み.json"))
        state = copy.deepcopy(state0)
        idx = {(m["項目"], m["期"]): m for m in mat["項目"]}
        chosen = []
        for item in SCOPE:
            label, period = item.split("_")
            m = idx.get((label, period))
            if m is None or m["単位"] != "円" or len(chosen) >= 2:
                continue
            alt = next((a for a in other.get(item) or [] if round(a / 1e6) != round(m["値"] / 1e6)), None)
            if alt is not None:
                chosen.append((m, alt, "別の読み(単体か前期)"))
        for item in SCOPE:
            if len(chosen) >= 2:
                break
            label, period = item.split("_")
            m = idx.get((label, period))
            if m is None or m["単位"] != "円" or any(c[0] is m for c in chosen):
                continue
            chosen.append((m, int(round(m["値"] / 1000)), "千円の表を円と読んだ形"))
        corrupt = []
        for m, v, kind in chosen:
            corrupt.append({"項目": m["項目"], "期": m["期"], "形": kind})
            m["値"] = v
            k = "%s@%s" % (m["項目"], CTX[m["期"]])
            state["状態"][k]["値"] = v
            for f in state["facts"]:
                if f["name"] == m["項目"] and f["context"] == CTX[m["期"]]:
                    f["value"] = float(v)
        dump(mat, "mat", n + ".json")
        dump(state, "B", n + ".json")
        dump(corrupt, "corrupt", n + ".json")
        print(n, "範囲", scope, "基準 A の項目", len(amap), "fact", len(facts), "誤り", [c["形"][:4] for c in corrupt])


if __name__ == "__main__":
    main()
