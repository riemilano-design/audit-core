# -*- coding: utf-8 -*-
"""独立判定の母集団(1B×P1・5F×P5F)の全 Claim について、エンジンの状態・pointer・reason を JSON に落とす。
使い方: python3 dump_engine_populations_2026-10-12.py <audit-core の道> <出力 JSON>
形: {docID: {Claim id: {state, pointers, reason}}}。採点は score_blind51 / score_round2 に --engine で渡す。"""
import json, sys
HERE, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, HERE)
from tests.golden import _instrument as INS
from tests.adapters.xbrl import _material as M
from adapters.xbrl import vocabulary as V

out = {}
for doc, prof in ((M.DOC_1, V.P1), (M.DOC_5, V.P5F)):
    zb = M.load_zip_bytes(doc["docID"], doc["sha256"])
    _recs, res, _meta = INS.run_verification(doc["docID"], prof, lambda: zb)
    out[doc["docID"]] = {i: {"state": r.state.value, "pointers": list(r.pointers), "reason": r.reason}
                         for i, r in res.items()}
json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1, sort_keys=True)
print({k: len(v) for k, v in out.items()})
