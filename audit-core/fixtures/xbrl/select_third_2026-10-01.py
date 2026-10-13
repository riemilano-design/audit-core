# -*- coding: utf-8 -*-
"""3 社目の選定と取得(人間が鍵のある環境で 1 回だけ回す)。Core のコードではない。

規則(予測 CORE_CONNECTION_THIRD_PREDICTION_2026-10-06.md §1 で封じたもの、探り 1 本目と同じ):
  提出日 = 2026-10-01(候補 0 件だったので、追記 ADDENDUM で決めた予備の順 10-02 → 10-05 → 09-28 → 09-25 を、候補が 1 件以上ある最初の日まで進む)、docTypeCode 120(有価証券報告書)、xbrlFlag 1、docDescription に「投資信託」を含まない、
  docID 昇順に ZIP を取り、連結(plain context)の jppfs の fact が 1 つ以上ある最初の書類。
出力: ~/.cache/audit-core/edinet/<docID>.zip(試した書類は全部置く)と fixtures/xbrl/third_selection.json(試した一覧・選ばれた docID・sha256)。
鍵は環境変数 EDINET_API_KEY からだけ読む。repo には書かない。
"""
import hashlib, json, os, sys, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))          # audit-core/
from adapters.xbrl import instance as I, edinet as E
import os as _os_gate
import sys as _sys_gate
_sys_gate.path.insert(0, _os_gate.path.dirname(_os_gate.path.abspath(__file__)))
from sealed_material import refuse_if_sealed  # noqa: E402  **取る直前に呼ぶ**

DATES = ["2026-10-01", "2026-10-02", "2026-10-05", "2026-09-28", "2026-09-25"]   # 封じた日 + 追記で決めた予備の順(土日を除く)
API = "https://api.edinet-fsa.go.jp/api/v2/"


def api(path, **params):
    key = os.environ.get("EDINET_API_KEY")
    if not key:
        print("EDINET_API_KEY が環境に無い"); sys.exit(2)
    params["Subscription-Key"] = key
    # **封じた材料への関門。**この道具は日付で選び、**共有キャッシュに書く。**
    if path.startswith("documents/") and not path.endswith(".json"):
        refuse_if_sealed(doc_id=path.split("/", 1)[1], where="select_third.api")
    return urllib.request.urlopen(API + path + "?" + urllib.parse.urlencode(params), timeout=120).read()


def main():
    dates_tried = []
    for DATE in DATES:
        lst = json.loads(api("documents.json", date=DATE, type=2).decode("utf-8"))
        allc = sorted([d for d in lst.get("results", []) if d.get("docTypeCode") == "120" and d.get("xbrlFlag") == "1"], key=lambda d: d["docID"])
        cands = [d for d in allc if "投資信託" not in (d.get("docDescription") or "")]
        print(f"[{DATE}] 有報(120,xbrl) {len(allc)} 件、うち投資信託を除く {len(cands)} 件")
        dates_tried.append({"date": DATE, "candidates_total": len(allc), "candidates_after_filter": len(cands)})
        if cands:
            break
    tried, chosen, sha = [], None, None
    os.makedirs(E.CACHE_DIR, exist_ok=True)
    for d in cands:
        zb = api(f"documents/{d['docID']}", type=1)
        path = E.cache_path(d["docID"])
        open(path, "wb").write(zb)
        inst = I.load_instance(zb)
        cons = [f for f in inst["facts"] if f["name"].startswith("jppfs") and I.plain_context(f["context"], inst["contexts"])]
        tried.append({"docID": d["docID"], "filer": d.get("filerName"), "consolidated_jppfs_facts": len(cons), "facts": len(inst["facts"])})
        print(" ", d["docID"], d.get("filerName"), "連結 jppfs", len(cons))
        if cons:
            chosen, sha = d, hashlib.sha256(zb).hexdigest(); break
    out = {"date_listed": DATE, "dates_tried": dates_tried, "selection_rule": "docTypeCode 120, xbrlFlag 1, not 投資信託, consolidated jppfs facts > 0, min docID; dates in sealed order until one has a candidate",
           "candidates_total": len(allc), "candidates_after_filter": len(cands), "tried": tried,
           "document": ({k: chosen.get(k) for k in ("docID", "filerName", "docDescription", "submitDateTime", "periodStart", "periodEnd", "edinetCode", "secCode")} if chosen else None),
           "zip_sha256": sha}
    json.dump(out, open(os.path.join(HERE, "third_selection.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("chosen:", chosen["docID"] if chosen else None, "sha256:", sha)
    print("written:", os.path.join(HERE, "third_selection.json"))
    return 0 if chosen else 3


if __name__ == "__main__":
    sys.exit(main())
