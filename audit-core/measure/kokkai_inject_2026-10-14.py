# -*- coding: utf-8 -*-
"""国会会議録デモ: 席の claims に 4 型の誤りを機械で混ぜる(種は固定)。
計画 ``docs/KOKKAI_DEMO_PLAN_2026-10-14.md`` §5。既存の ``measure/inject.py`` は触らない。

T1 発言番号 → 別の実在する発言番号 / T2 発言者 → 同じ会議の別の発言者 /
T3 引用の漢字 1 字 → 同じ発言に出る別の漢字 / T4 数の値 ×10(text と value の両方)。
1 claim に 1 型、重ならない。混ぜた後の claim が元と同じ(= 混ぜたことにならない)なら
その claim は捨てて次の候補へ。

使い方::

    python3 measure/kokkai_inject_2026-10-14.py --meeting <meeting.json> --summary <summary.json> \
        --seed 20261014 --per-type 5 --out <tampered.json> --record <record.json>
"""

import argparse
import copy
import io
import json
import random
import re
import sys
import unicodedata

_KANJI_RE = re.compile(r"[一-鿿]")
_WS_RE = re.compile(r"[\s　]+")

TYPES = ("T1_order", "T2_speaker", "T3_quote", "T4_number")


def _norm(s):
    return _WS_RE.sub("", unicodedata.normalize("NFKC", s or ""))


def _speeches(meeting):
    m = meeting["meetingRecord"][0]
    return {int(s["speechOrder"]): s for s in m["speechRecord"]}


def inject(meeting, summary, seed, per_type):
    rng = random.Random(seed)
    speeches = _speeches(meeting)
    orders = sorted(o for o in speeches if o != 0)
    speakers = sorted({s["speaker"] for o, s in speeches.items() if o != 0 and s.get("speaker")})

    claims = copy.deepcopy(summary["claims"])
    by_id = {c["id"]: c for c in claims}
    pool = [c["id"] for c in claims]
    rng.shuffle(pool)
    used = set()
    record = []

    for t in TYPES:
        done = 0
        for cid in pool:
            if done >= per_type:
                break
            if cid in used:
                continue
            c = by_id[cid]
            before = copy.deepcopy(c)
            if t == "T1_order":
                others = [o for o in orders if o != c.get("speech_order")]
                c["speech_order"] = rng.choice(others)
            elif t == "T2_speaker":
                others = [s for s in speakers if s != c.get("speaker")]
                if not others:
                    continue
                c["speaker"] = rng.choice(others)
            elif t == "T3_quote":
                q = c.get("quote")
                if not q:
                    continue
                speech = speeches[c["speech_order"]]["speech"]
                positions = [i for i, ch in enumerate(q) if _KANJI_RE.match(ch)]
                if not positions:
                    continue
                rng.shuffle(positions)
                candidates = sorted({ch for ch in speech if _KANJI_RE.match(ch)})
                new_q = None
                for i in positions:
                    alts = [ch for ch in candidates if ch != q[i]]
                    rng.shuffle(alts)
                    for ch in alts:
                        cand = q[:i] + ch + q[i + 1:]
                        if _norm(cand) not in _norm(speech):
                            new_q = cand
                            break
                    if new_q:
                        break
                if new_q is None:
                    continue
                c["quote"] = new_q
            elif t == "T4_number":
                n = c.get("number")
                if not isinstance(n, dict) or n.get("value") is None:
                    continue
                v = n["value"] * 10
                n["value"] = v
                new_text = ("%d" % v if float(v).is_integer() else "%s" % v) + (n.get("unit") or "")
                if n.get("text") and n["text"] in (c.get("text") or ""):
                    c["text"] = c["text"].replace(n["text"], new_text, 1)
                n["text"] = new_text
            if c == before:
                continue
            used.add(cid)
            done += 1
            record.append({"id": cid, "type": t, "before": before, "after": copy.deepcopy(c)})
        if done < per_type:
            raise SystemExit("型 %s は %d 件しか混ぜられなかった(要求 %d)" % (t, done, per_type))

    out = copy.deepcopy(summary)
    out["claims"] = claims
    out["written_by"] = (summary.get("written_by") or "") + " + 機械で誤りを混ぜた(kokkai_inject_2026-10-14, seed=%d)" % seed
    return out, record


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--meeting", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--per-type", type=int, default=5)
    ap.add_argument("--out", required=True)
    ap.add_argument("--record", required=True)
    a = ap.parse_args(argv)
    with io.open(a.meeting, encoding="utf-8") as fh:
        meeting = json.load(fh)
    with io.open(a.summary, encoding="utf-8") as fh:
        summary = json.load(fh)
    out, record = inject(meeting, summary, a.seed, a.per_type)
    with io.open(a.out, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    with io.open(a.record, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"seed": a.seed, "per_type": a.per_type, "rows": record}, ensure_ascii=False, indent=1) + "\n")
    counts = {}
    for r in record:
        counts[r["type"]] = counts.get(r["type"], 0) + 1
    print("injected:", counts, "->", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
