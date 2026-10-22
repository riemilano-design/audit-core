# -*- coding: utf-8 -*-
"""入口(``adapters/xbrl/verify_document.py``)の golden を、**入口ではなく
試験の補助(``tests/golden/_instrument.run_verification``)から**作る。

開発書類の AI 文(S100Z4Q1 の経営分析の節を ``ai_prose_2026-10-09.txt`` で
差し替えたもの)を P7・P13・P16 で回し、Claim id ごとに
``(state, pointers, reason, subject)`` を書く。これが入口の意味の一致の
期待値になる(**入口の出力から作らない** ― 作ると同語反復になる)。

出力: ``fixtures/xbrl/entry_golden_ai_prose_2026-10-13.json``(在れば上書きしない)
通信しない。
"""

import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))

from adapters.xbrl import prose as PR            # noqa: E402
from adapters.xbrl import vocabulary as V        # noqa: E402
from tests.golden import _instrument as INS      # noqa: E402

DOC = "S100Z4Q1"
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
PROSE = os.path.join(HERE, "ai_prose_2026-10-09.txt")
OUT = os.path.join(HERE, "entry_golden_ai_prose_2026-10-13.json")
PROFILES = ("P7", "P13", "P16")


def main():
    if os.path.exists(OUT):
        raise SystemExit("既に在る。上書きしない: %s" % OUT)
    zb = open(os.path.join(CACHE, DOC + ".zip"), "rb").read()
    text = io.open(PROSE, encoding="utf-8").read()
    zb2, element, member = PR.build_modified_zip(zb, text)
    got = hashlib.sha256(zb2).hexdigest()
    if got != PR.AI_PROSE_ZIP_SHA256:
        raise SystemExit("差し替えた ZIP の sha256 が封と違う: %s" % got)
    out = {
        "purpose": "入口の意味の一致の期待値。tests/golden/_instrument.run_verification で作った(入口の出力からは作っていない)",
        "document": DOC, "replaced_element": element, "replaced_member": member,
        "modified_zip_sha256": got,
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "profiles": {},
    }
    for name in PROFILES:
        recs, res, _metas = INS.run_verification(DOC, V.PROFILES[name], lambda: zb2)
        rows = {}
        for r in recs:
            x = res[r.claim.id]
            rows[r.claim.id] = {
                "state": x.state.name,
                "pointers": [(p if isinstance(p, str) else p.scheme + ":" + p.locator)
                             for p in x.pointers],
                "reason": x.reason,
                "subject": r.claim.subject,
            }
        out["profiles"][name] = {"claims": len(rows), "rows": rows}
        print(name, len(rows))
    with io.open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
        fh.write(u"\n")
    print("written:", OUT, hashlib.sha256(open(OUT, "rb").read()).hexdigest()[:16])


if __name__ == "__main__":
    main()
