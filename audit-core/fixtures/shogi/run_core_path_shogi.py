# -*- coding: utf-8 -*-
"""C-2 計器 6 の Core 側(``audit-core/docs/CORE_CONNECTION_C2_PLAN_2026-10-06.md``
§5・§6): 1 顧客フォルダ(c5 の Golden Master が指す ``scripts/playtest/out/<customer>``
形)の席の封筒を Adapter + Core(``verify_all``)で回し、Claim の層・結果の層・集計を
1 本の JSON に書く計測 script。Core のコードではない。

seat run の読み方は ``scripts/playtest/goldenMasterCheck.ts``(``seat_runs`` を
作る節)と同じ規則: ``--seats-dir`` の下のディレクトリを sort し、
``run_summary.json`` が無ければ飛ばし、``seat_(gpt|gemini|claude).json`` だけを
sort して拾う。

  python3 fixtures/shogi/run_core_path_shogi.py \
      --customer-dir scripts/playtest/out/c5 --seats-dir llm-seats \
      --packet packet/observation-packet.json --out <path>

**実物(``scripts/playtest/out/``)では回さない**: 1 回目の計測は司令塔が凍結
時点で行う(C-2 計画 §6 の手順・C-1g の逸脱の教訓)。この docstring のとおりに
合成の小さな材料で動作確認するのはこの STEP の実装担当の仕事。

``statement``(文)は読み取っても出力に書かない(C-2 計画 §2)。
"""

import argparse
import collections
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))

import audit_core as core  # noqa: E402
from adapters.shogi import recipes as R  # noqa: E402
from adapters.shogi import registry_setup as RS  # noqa: E402
from adapters.shogi import resolve as RV  # noqa: E402

_SEAT_FILE_RE = re.compile(r"^seat_(gpt|gemini|claude)\.json$")


def _sha256_of_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _read_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _seat_envelopes(customer_dir, seats_dir_name):
    """Mirror ``goldenMasterCheck.ts``'s ``seat_runs`` enumeration. Returns
    ``(envelopes, seat_file_records)`` where ``envelopes`` is
    ``[(run_id, seat_file_name, envelope_dict), ...]`` and
    ``seat_file_records`` is ``[{"run_id", "file", "sha256"}, ...]``."""

    seats_dir = os.path.join(customer_dir, seats_dir_name)
    envelopes = []
    records = []
    if not os.path.isdir(seats_dir):
        return envelopes, records
    run_ids = sorted(
        name for name in os.listdir(seats_dir) if os.path.isdir(os.path.join(seats_dir, name))
    )
    for run_id in run_ids:
        run_dir = os.path.join(seats_dir, run_id)
        summary_path = os.path.join(run_dir, "run_summary.json")
        if not os.path.isfile(summary_path):
            continue
        seat_files = sorted(
            name for name in os.listdir(run_dir) if _SEAT_FILE_RE.match(name)
        )
        for seat_file in seat_files:
            seat_path = os.path.join(run_dir, seat_file)
            envelope = _read_json(seat_path)
            envelopes.append((run_id, seat_file, envelope))
            records.append({"run_id": run_id, "file": seat_file, "sha256": _sha256_of_file(seat_path)})
    return envelopes, records


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--customer-dir", required=True)
    ap.add_argument("--seats-dir", required=True)
    ap.add_argument("--packet", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    customer_dir = os.path.abspath(a.customer_dir)
    packet_path = os.path.join(customer_dir, a.packet)
    packet = _read_json(packet_path)
    packet_sha256 = _sha256_of_file(packet_path)

    envelopes, seat_file_records = _seat_envelopes(customer_dir, a.seats_dir)

    recipe_list = R.build_recipes(envelopes, packet)
    resolver = RV.make_resolver(packet)
    registry = RS.register_all(core.Registry.default())
    results = core.verify_all(recipe_list, resolver, registry)

    rows = []
    for recipe, result in zip(recipe_list, results):
        c = recipe.claim
        rows.append(
            {
                "id": c.id,
                "form": c.form.value,
                "subject": c.subject,
                "value": c.value,
                "unit": c.unit,
                "modifiers": {
                    "population": c.modifiers.population,
                    "time_range": list(c.modifiers.time_range),
                    "normalization": c.modifiers.normalization,
                },
                "pointers": list(result.pointers),
                "comparator": result.comparator,
                "state": result.state.value,
                "recomputed": result.recomputed,
                "reason": result.reason,
                "provenance": {
                    k: v
                    for k, v in c.provenance.items()
                    if k in ("hypothesis_id", "kind", "obs_id", "value_is_number", "raw_value", "at")
                },
            }
        )

    C = collections.Counter
    modifiers_nonempty = len(
        [
            r
            for r in rows
            if r["modifiers"]["population"] is not None
            or len(r["modifiers"]["time_range"]) > 0
            or r["modifiers"]["normalization"] is not None
        ]
    )
    value_is_number = len([r for r in rows if r["provenance"].get("value_is_number")])
    tally = {
        "claims": len(rows),
        "by_state": dict(C(r["state"] for r in rows)),
        "by_form": dict(C(r["form"] for r in rows)),
        "by_reason": dict(C(r["reason"] for r in rows if r["reason"])),
        "modifiers_nonempty": modifiers_nonempty,
        "value_is_number": value_is_number,
    }

    registry_counts = {
        "schemes": len(registry._schemes),
        "comparators": len(registry._comparators),
        "normalizations": len(registry._normalizations),
        "reasons": len(registry._reasons),
        "note": "register_all 後の登録簿を数えた値(Core 自身の builtin scheme と equals 比較子を含む)",
    }

    out = {
        "tool": "run_core_path_shogi",
        "inputs": {
            "packet_sha256": packet_sha256,
            "seat_files": seat_file_records,
        },
        "registry": registry_counts,
        "tally": tally,
        "claims": rows,
    }

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as handle:
        json.dump(out, handle, ensure_ascii=False, indent=1)
    print(json.dumps({"inputs": out["inputs"], "registry": registry_counts, "tally": tally}, ensure_ascii=False, indent=1))
    print("written:", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
