# -*- coding: utf-8 -*-
"""封(docs/HOLDOUT_P17_SEAL_2026-10-14.md §3)の算法どおりに書類を引き、ZIP を取る。

**算法は封の字のまま。**ここで選択の余地を作らない::

    pool    = 母集団 215 件の docID を昇順
    rng     = random.Random(int("6a24d72", 16))
    order   = pool のコピーを rng.shuffle した並び
    drawn   = order の先頭 6 件     (第 1 段)
    labeled = drawn の先頭 3 件     (第 2 段)

ZIP が取れない・XBRL の経営分析の節が無い書類は外し、``order`` の次を繰り上げる。
繰り上げた件数と理由を出力に書く(**外した書類の中身は読まない**)。

鍵は環境変数 ``EDINET_API_KEY`` から読む。**値には触れない**(印字・保存しない)。
"""

import io
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))

from adapters.xbrl import edinet as ED  # noqa: E402
from adapters.xbrl import instance as I  # noqa: E402

SEED_HEX = "6a24d72"          # main の HEAD。**封の字のまま**
N_DRAWN = 6
N_LABELED = 3
OUT = os.path.join(ROOT, "fixtures", "xbrl", "holdout_p17")
# **第 2 版の母集団**(封 §9-1)。第 1 版は ``pool_meta_2026-10-14.json`` の 215 件だったが、
# docTypeCode=120 に投資信託の有報(jpsps070000、経営分析の節が無い)が混ざっていて
# 214 件が外れた。第 2 版は ordinanceCode=010 / formCode=030000 で絞った 256 件。
POOL = os.path.join(OUT, "pool2_clean_2026-10-14.json")
POOL_META = os.path.join(OUT, "pool2_meta_2026-10-14.json")
DRAW_OUT = "drawn2_2026-10-14.json"


def pool_ids():
    with io.open(POOL, encoding="utf-8") as fh:
        clean = json.load(fh)
    with io.open(POOL_META, encoding="utf-8") as fh:
        meta = json.load(fh)
    return sorted(clean["pool_clean"]), meta


def order_of(ids):
    rng = random.Random(int(SEED_HEX, 16))
    shuffled = list(ids)
    rng.shuffle(shuffled)
    return shuffled


def has_mdna(zip_bytes):
    """経営分析の節が在るか。**中身は読まない**(節の名前が在るかだけ)。"""

    inst = I.load_instance(zip_bytes)
    try:
        name = I.select_mdna(inst["textblocks"])
    except Exception:
        return False, None
    return bool(name), name


def run():
    ids, meta = pool_ids()
    order = order_of(ids)
    by_id = {r["docID"]: r for r in meta["rows"]}
    drawn, skipped = [], []
    for doc_id in order:
        if len(drawn) >= N_DRAWN:
            break
        try:
            path = ED.fetch(doc_id)
        except Exception as exc:
            skipped.append({"docID": doc_id, "why": "取得できない: %s" % type(exc).__name__})
            continue
        with open(path, "rb") as fh:
            zb = fh.read()
        try:
            ok, name = has_mdna(zb)
        except Exception as exc:
            skipped.append({"docID": doc_id, "why": "XBRL を読めない: %s" % type(exc).__name__})
            continue
        if not ok:
            skipped.append({"docID": doc_id, "why": "経営分析の節が無い"})
            continue
        drawn.append({"docID": doc_id, "sha256": ED.sha256_of(path), "bytes": len(zb),
                      "mdna_element": name,
                      "filerName": by_id[doc_id].get("filerName"),
                      "date": by_id[doc_id].get("date"),
                      "periodEnd": by_id[doc_id].get("periodEnd")})
        print("引いた %d/%d: %s %s" % (len(drawn), N_DRAWN, doc_id, by_id[doc_id].get("filerName")))
    rec = {"seal": "docs/HOLDOUT_P17_SEAL_2026-10-14.md", "seed_hex": SEED_HEX,
           "pool": len(ids), "order_head": order[:12],
           "drawn": drawn, "labeled": [d["docID"] for d in drawn[:N_LABELED]],
           "skipped": skipped}
    p = os.path.join(OUT, DRAW_OUT)
    with io.open(p, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
    print("\n引いた 6 件:", [d["docID"] for d in drawn])
    print("ラベルを取る 3 件:", rec["labeled"])
    print("繰り上げ(外した)件数:", len(skipped), skipped if skipped else "")
    print("->", p)


if __name__ == "__main__":
    run()
