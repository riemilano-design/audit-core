# -*- coding: utf-8 -*-
"""Inject errors of known type and location into a prepared document.

Four of the human decision's six error types are built here by machine
(数字の置換 / 単位のずれ / 原文に無い数 / 値が偶然一致して参照先が違う).
The remaining two (期間・母集団の入れ替え) are written to a task list for a
person, because choosing which period or population a sentence inherits is a
reading of the text rather than a transformation of it.

Three rules are enforced by the code, not by discipline:

1. **The seed is sealed before the run.** ``--seed-file`` must be tracked by
   git and identical to its committed content. A dirty or untracked seed file
   is a hard error, so the seed cannot be chosen after seeing a result.
2. **The injection record leaves the repository.** It is written under
   ``--record-dir`` (default ``~/.audit-core-measure/injection-records``),
   outside the working tree, and only its sha256 is written back into the
   repo. A session working in the repo cannot read which errors were injected
   before scoring, and the sha256 still proves the record was not rewritten
   afterwards.
3. **Every run round-trips.** The edits are reverted and compared against the
   original before anything is written. A span bug fails the run instead of
   producing a record that does not describe the document.

Usage::

    python3 inject.py --doc shogi-c5 --kind shogi --material out/material \\
        --seed-file SEED.json --count 12 --out out/documents
"""

import argparse
import hashlib
import io
import json
import os
import random
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import numbers as N  # noqa: E402
from lib import sites as S  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RECORD_DIR = os.path.join(os.path.expanduser("~"), ".audit-core-measure", "injection-records")
MACHINE_TYPES = ["T1_VALUE", "T2_UNIT", "T3_ABSENT", "T5_COINCIDENT"]

# Which types a machine may build, per corpus. Not a tuning knob: 型 1 and
# 型 5 need to know that a prose number is a measured quantity and, for 型 5,
# which fact it refers to. In a filing that means reading amounts written in
# mixed Japanese numerals ("394億1千9百万円") and reconciling 円 / 千円 /
# 百万円 / 億円 against the facts -- which is exactly what the extractor and
# the Adapter do, and this package may not use them.
#
# Measured 2026-10-08 after four screening passes: XBRL 型 5 fell to 1-2
# sites per filing, and the 型 1 pool was still mostly section numbers, note
# indices and per-unit denominators ("1株当たり", "1ドル＝").
#
# The booklet writes plain numbers next to Japanese labels, so all four work
# there. Override with --types when measuring the boundary itself.
#
# **Human decision 2026-10-08, option (b):** 型 5 is measured on the shogi
# booklet only, and the filings are written up as "機械で作れず未測定" rather
# than as a measured zero. The hole is real in a filing -- the 60-item blind
# confirmation found three instances of it (T008 / T022 / T031, see
# material/xbrl/observed_t5.json) -- but a machine in this layer cannot
# synthesise one, so no rate may be quoted for filings.
TYPE_POLICY = {
    "shogi": ["T1_VALUE", "T2_UNIT", "T3_ABSENT", "T5_COINCIDENT"],
    "xbrl": ["T2_UNIT", "T3_ABSENT"],
}
TOL = 1e-9


class SealError(RuntimeError):
    pass


def _git(repo, *args):
    p = subprocess.run(["git", "-C", repo] + list(args), capture_output=True, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def verify_seed_sealed(seed_path):
    """Return (seed, meta) only if the seed file is committed and unmodified."""
    # realpath on both sides: on macOS a temp dir is reached through a
    # symlink (/var -> /private/var) and git reports the resolved form, so
    # relpath against the unresolved path walks out of the repository.
    seed_path = os.path.realpath(seed_path)
    repo = os.path.dirname(seed_path)
    rc, top, _ = _git(repo, "rev-parse", "--show-toplevel")
    if rc != 0:
        raise SealError("not inside a git repository: %s" % seed_path)
    top = os.path.realpath(top)
    rel = os.path.relpath(seed_path, top)
    if rel.startswith(".."):
        raise SealError("seed file is outside the repository: %s" % seed_path)

    rc, _, err = _git(top, "ls-files", "--error-unmatch", rel)
    if rc != 0:
        raise SealError(
            "seed file is not tracked by git: %s\n"
            "The seed must be committed before the script runs, so that it cannot "
            "be chosen after seeing a result. Commit it and re-run." % rel
        )
    rc, out, _ = _git(top, "diff", "--name-only", "HEAD", "--", rel)
    if rc != 0 or out:
        raise SealError(
            "seed file differs from its committed content: %s\n"
            "Commit the change (or restore it) before running." % rel
        )
    rc, commit, _ = _git(top, "log", "-1", "--format=%H", "--", rel)
    if rc != 0 or not commit:
        raise SealError("seed file has no commit touching it: %s" % rel)

    with io.open(seed_path, encoding="utf-8") as fh:
        data = json.load(fh)
    if "seed" not in data:
        raise SealError("seed file has no 'seed' key: %s" % rel)
    with io.open(seed_path, "rb") as fh:
        seed_sha = hashlib.sha256(fh.read()).hexdigest()
    meta = {
        "seed_file": rel,
        "seed_file_sha256": seed_sha,
        "sealed_in_commit": commit,
    }
    return data["seed"], meta


def load_material(material_dir, doc_id):
    tpath = os.path.join(material_dir, "%s.original.txt" % doc_id)
    rpath = os.path.join(material_dir, "%s.reference_numbers.json" % doc_id)
    with io.open(tpath, encoding="utf-8", newline="") as fh:
        text = fh.read()
    with io.open(rpath, encoding="utf-8") as fh:
        refs = json.load(fh)["refs"]
    with io.open(rpath, "rb") as fh:
        refs_sha = hashlib.sha256(fh.read()).hexdigest()
    return text, refs, {
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "reference_numbers_sha256": refs_sha,
    }


def _ref_values(refs):
    return {round(r["value"], 6) for r in refs}


def build_t1(site, refs, rng):
    """数字の置換: a replacement that no reference number carries.

    No ``true_ref_key`` is recorded. T1 does not need to know which fact the
    sentence refers to: a value that appears nowhere in the data is wrong
    whatever the subject. Claiming a reference here is what produced records
    naming a fact the sentence was not about, so the record lists the
    candidates and says how many there were instead.
    """
    t = site["token"]
    present = _ref_values(refs)
    cand_keys = sorted({r["key"] for r in site["candidates"]})
    for mult in (2, 3, 5, 7, 11):
        for delta in (1, 2, 3, 4, 6, 9, 13):
            for cand in (t.value + delta * mult, t.value - delta * mult):
                if cand <= 0 or abs(cand - t.value) <= TOL:
                    continue
                if round(cand, 6) in present:
                    continue
                return {
                    "new_value": cand,
                    "replacement": N.render_value(cand, t),
                    "span": [t.start, t.end],
                    "detail": {
                        "original_value": t.value,
                        "replacement_value": cand,
                        "replacement_absent_from_reference_numbers": True,
                        "identification": "not required for this type",
                        "candidate_ref_keys": cand_keys[:8],
                        "candidate_ref_count": len(cand_keys),
                    },
                    "expected": "判定の核が GROUNDED にしてはいけない(値が元データのどこにも無い)",
                }
    return None


def build_t5(site, refs, rng):
    """値が偶然一致して参照先が違う: the replacement is another fact's value."""
    t = site["token"]
    others = site["others"]
    # t5_sites has already screened for unit compatibility, a different
    # label and a comparable magnitude; prefer an exact unit match among
    # what is left. No fallback to "any reference": that fallback is what
    # borrowed a cash-flow amount for a subsidiary count.
    pool = [o for o in others if o.get("unit") == site["ref"].get("unit")] or others
    other = pool[rng.randrange(len(pool))]
    cand = other["value"]
    return {
        "new_value": cand,
        "replacement": N.render_value(cand, t),
        "span": [t.start, t.end],
        "detail": {
            "true_ref_key": site["ref"]["key"],
            "true_ref_label": site["ref"].get("label"),
            "true_value": t.value,
            "replacement_value": cand,
            "coincident_ref_key": other["key"],
            "coincident_ref_label": other.get("label"),
            "replacement_absent_from_reference_numbers": False,
        },
        "expected": (
            "値だけを探す照合は通る(別の事実が同じ値を持つ)。"
            "参照先を解いてから比べる照合だけが止める ― 既知の一番の穴"
        ),
    }


def build_t2(site, refs, rng):
    """単位のずれ: digits untouched, unit swapped inside its family."""
    t = site["token"]
    sib = site["siblings"][rng.randrange(len(site["siblings"]))]
    ustart = N.unit_start_of(t)
    return {
        "new_value": t.value,
        "replacement": sib,
        "span": [ustart, t.unit_end],
        "detail": {
            "digits_unchanged": t.text,
            "unit_before": t.unit,
            "unit_after": sib,
            "unit_family": N.unit_family(t.unit) or "count",
        },
        "expected": "数は同じで、数えている対象が違う(scale の事故と同じ形)",
    }


def build_t3(site, refs, rng, used_subjects=None, used_values=None):
    """原文に無い数: insert a sentence about a subject the data lacks.

    Each injection gets its own subject and its own value. Two identical
    fabricated sentences in one document test one thing twice and read as a
    copy-paste tell.
    """
    used_subjects = used_subjects if used_subjects is not None else set()
    used_values = used_values if used_values is not None else set()
    pool = [(sj, tp) for sj, tp in site["templates"] if sj not in used_subjects]
    if not pool:
        return None
    subj, tpl = pool[rng.randrange(len(pool))]
    present = _ref_values(refs)
    val = None
    for cand in range(37, 400, 7):
        if round(float(cand), 6) not in present and cand not in used_values:
            val = cand
            break
    if val is None:
        return None
    used_subjects.add(subj)
    used_values.add(val)
    sentence = tpl % (subj, val)
    return {
        "new_value": float(val),
        "replacement": sentence,
        "span": [site["at"], site["at"]],
        "detail": {
            "inserted_sentence": sentence,
            "fabricated_subject": subj,
            "subject_absent_from_reference_numbers": True,
            "value_absent_from_reference_numbers": True,
        },
        "expected": "参照先が解けない(POINTER_NOT_FOUND)。分解層が claim にしなければ「止めなかった」に数える",
    }


BUILDERS = {
    "T1_VALUE": build_t1,
    "T2_UNIT": build_t2,
    "T3_ABSENT": build_t3,
    "T5_COINCIDENT": build_t5,
}


def _overlaps(span, chosen):
    a, b = span
    for c, d in chosen:
        if a == b and c == d:
            if a == c:
                return True
            continue
        if a == b:
            if c < a < d:
                return True
            continue
        if c == d:
            if a < c < b:
                return True
            continue
        if a < d and c < b:
            return True
    return False


def select(text, refs, kind, seed, doc_id, count, types=None):
    """Choose ``count`` injections, spread as evenly as the catalogue allows.

    The RNG is seeded from (sealed seed, document id) so each document draws
    its own sites and a re-run reproduces them exactly.
    """
    rng = random.Random("%s|%s" % (seed, doc_id))
    catalog = {
        "T1_VALUE": S.t1_sites(text, refs),
        "T2_UNIT": S.t2_sites(text, refs),
        "T3_ABSENT": S.t3_sites(text, refs, kind),
        "T5_COINCIDENT": S.t5_sites(text, refs),
    }
    for v in catalog.values():
        rng.shuffle(v)

    counts = {t: len(catalog[t]) for t in MACHINE_TYPES}
    allowed = list(types or TYPE_POLICY[kind])
    withheld = {t: counts[t] for t in MACHINE_TYPES if t not in allowed}
    chosen, spans, cursor = [], [], {t: 0 for t in MACHINE_TYPES}
    # One injection per number token. A value substitution and a unit shift on
    # the same number do not overlap as spans, but together they make the
    # record unattributable: a detection could not be credited to either type.
    claimed_tokens = set()
    used_subjects, used_values = set(), set()
    # Round-robin so no type is starved, then keep going while anything is left.
    while len(chosen) < count:
        progressed = False
        for t in allowed:
            if len(chosen) >= count:
                break
            pool = catalog[t]
            while cursor[t] < len(pool):
                site = pool[cursor[t]]
                cursor[t] += 1
                tok = site.get("token")
                tok_id = (tok.start, tok.end) if tok is not None else None
                if tok_id is not None and tok_id in claimed_tokens:
                    continue
                if t == "T3_ABSENT":
                    built = build_t3(site, refs, rng, used_subjects, used_values)
                else:
                    built = BUILDERS[t](site, refs, rng)
                if built is None:
                    continue
                if _overlaps(built["span"], spans):
                    continue
                if tok_id is not None:
                    claimed_tokens.add(tok_id)
                built["type"] = t
                built["id"] = "%s-%s-%02d" % (doc_id, t.split("_")[0], sum(1 for c in chosen if c["type"] == t) + 1)
                chosen.append(built)
                spans.append(tuple(built["span"]))
                progressed = True
                break
        if not progressed:
            break
    return chosen, counts, allowed, withheld


def apply_edits(text, chosen):
    """Apply the edits and return (tampered_text, placements).

    ``placements`` records each edit's span in the *tampered* text as well,
    so the record describes both documents and the revert can be checked.
    """
    out = text
    placements = {}
    shift_sorted = sorted(chosen, key=lambda c: (-c["span"][0], -c["span"][1]))
    for c in shift_sorted:
        a, b = c["span"]
        out = out[:a] + c["replacement"] + out[b:]
    # Second pass: offsets in the tampered text, computed left to right.
    delta = 0
    for c in sorted(chosen, key=lambda c: c["span"][0]):
        a, b = c["span"]
        na = a + delta
        nb = na + len(c["replacement"])
        placements[c["id"]] = [na, nb]
        delta += len(c["replacement"]) - (b - a)
    return out, placements


def revert(tampered, chosen, placements, original_text):
    """Rebuild the original from the tampered text using the record alone."""
    out = tampered
    for c in sorted(chosen, key=lambda c: -placements[c["id"]][0]):
        na, nb = placements[c["id"]]
        a, b = c["span"]
        out = out[:na] + original_text[a:b] + out[nb:]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--doc", required=True)
    ap.add_argument("--kind", required=True, choices=["shogi", "xbrl"])
    ap.add_argument("--material", required=True)
    ap.add_argument("--seed-file", required=True)
    ap.add_argument("--count", type=int, required=True)
    ap.add_argument("--out", required=True, help="where the tampered document is written (handed to the decomposition side)")
    ap.add_argument("--record-dir", default=DEFAULT_RECORD_DIR, help="where the injection record is written (outside the repo)")
    ap.add_argument("--types", nargs="+", choices=MACHINE_TYPES, default=None,
                    help="override the per-corpus policy (see TYPE_POLICY)")
    args = ap.parse_args(argv)

    seed, seal = verify_seed_sealed(args.seed_file)
    text, refs, mat = load_material(args.material, args.doc)

    chosen, counts, allowed, withheld = select(
        text, refs, args.kind, seed, args.doc, args.count, args.types
    )
    if not chosen:
        raise SystemExit("no injectable site found for %s" % args.doc)
    tampered, placements = apply_edits(text, chosen)

    back = revert(tampered, chosen, placements, text)
    if back != text:
        raise SystemExit(
            "round-trip failed for %s: reverting the record did not reproduce the original. "
            "Nothing was written." % args.doc
        )

    human = S.human_sites(text, args.kind)
    unident = S.unidentified_sites(text, refs)

    os.makedirs(args.out, exist_ok=True)
    tpath = os.path.join(args.out, "%s.tampered.txt" % args.doc)
    with io.open(tpath, "w", encoding="utf-8", newline="") as fh:
        fh.write(tampered)

    record = {
        "note": "混入の記録。採点までは分解側に渡さない。リポジトリの外に置いてある。",
        "document_id": args.doc,
        "kind": args.kind,
        "seed": seed,
        "seal": seal,
        "material": mat,
        "tampered_sha256": hashlib.sha256(tampered.encode("utf-8")).hexdigest(),
        "catalog_site_counts": counts,
        "types_built_by_machine": allowed,
        "types_withheld_for_a_person": withheld,
        "data_bearing_but_unidentifiable": len(unident),
        "requested_count": args.count,
        "injected_count": len(chosen),
        "injections": [
            {
                "id": c["id"],
                "type": c["type"],
                "original_span": c["span"],
                "tampered_span": placements[c["id"]],
                "original_text": text[c["span"][0]:c["span"][1]],
                "replacement_text": c["replacement"],
                "detail": c["detail"],
                "expected": c["expected"],
            }
            for c in sorted(chosen, key=lambda c: c["span"][0])
        ],
        "round_trip_verified": True,
    }

    os.makedirs(args.record_dir, exist_ok=True)
    rpath = os.path.join(args.record_dir, "%s.record.json" % args.doc)
    blob = json.dumps(record, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    with io.open(rpath, "w", encoding="utf-8") as fh:
        fh.write(blob)
    rsha = hashlib.sha256(blob.encode("utf-8")).hexdigest()

    # Only the digest comes back into the repo.
    os.makedirs(args.out, exist_ok=True)
    with io.open(os.path.join(args.out, "%s.record.sha256" % args.doc), "w", encoding="utf-8") as fh:
        fh.write("%s  %s.record.json\n" % (rsha, args.doc))

    hpath = os.path.join(args.out, "%s.human_tasks.json" % args.doc)
    with io.open(hpath, "w", encoding="utf-8") as fh:
        json.dump({
            "note": (
                "機械で作れない誤りの型 ― 期間の入れ替え・母集団の入れ替え・"
                "別の文のものへの付け替え。どの期間/母集団を文が引き継いでいるかの判断は"
                "測る対象そのものなので、機械が決めると自分の答えを自分で書くことになる。"
                "人がここから選んで作り、同じ形で混入の記録に足す。"
            ),
            "document_id": args.doc,
            "candidate_count": len(human),
            "candidates": human,
            "types_withheld_for_a_person": sorted(withheld),
            "types_withheld_note": (
                "この文書では機械で作らない型。参照先の同定に抽出器/Adapter の"
                "読み(混在した和数字・円/千円/百万円の換算)が要るため。人が作る。"
            ),
            "unidentifiable_numbers_note": (
                "値は元データに在るが、どの事実を指しているか機械では決められなかった数。"
                "型 5(値が偶然一致して参照先が違う)をここに作るには人の読みが要る。"
            ),
            "unidentifiable_numbers_count": len(unident),
            "unidentifiable_numbers": unident,
        }, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    by_type = {}
    for c in chosen:
        by_type[c["type"]] = by_type.get(c["type"], 0) + 1
    print("%s: injected %d  %s" % (args.doc, len(chosen), by_type))
    print("  catalog     : %s" % counts)
    if withheld:
        print("  withheld    : %s  (型として人に回す ― TYPE_POLICY)" % withheld)
    print("  tampered    -> %s" % tpath)
    print("  record      -> %s  (outside the repo)" % rpath)
    print("  record sha  -> %s" % rsha[:16])
    print("  human tasks -> %s (%d candidates, %d unidentifiable numbers)" % (hpath, len(human), len(unident)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
