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
from lib import scales as SC  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RECORD_DIR = os.path.join(os.path.expanduser("~"), ".audit-core-measure", "injection-records")
MACHINE_TYPES = ["T1_VALUE", "T2_UNIT", "T3_ABSENT", "T5_COINCIDENT"]
# 2026-10-20 段 2(封 docs/XBRL_HYBRID_TRUST_SEAL_2026-10-20.md §2): 席が通しうる 2 型。
# MACHINE_TYPES・TYPE_POLICY・--types の choices には**入れない**(既存の型と既定の一覧は 1 字も変えない)。
# ``select(..., types=[...])`` に名前を明示したときだけ使われる。
EXTRA_TYPES = ["T6_PRIOR", "T7_ROUND"]

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


def t6_sites(text, refs, diag=None):
    """前期の値への置換(T6_PRIOR)の site. 段 2(2026-10-20)。

    Site = 参照先が 1 つに決まる数(``sites.identified_sites``)のうち、参照先の枠が ``CurrentYear...`` で、
    同じ要素・同じ枠の ``Prior1Year...`` の fact(1 件・同じ単位・値が違う・どちらも正)が refs に在り、
    その値を数の字面の単位に戻して**元の字の形で 1 字違わず書ける**もの。置き換え後の値は書類の中に実在する。

    ``diag`` (dict)を渡すと、絞り込みの各段の件数を足す(site が 0 のとき理由を 1 段ずつ読むため)。
    """
    def bump(k):
        if diag is not None:
            diag[k] = diag.get(k, 0) + 1

    by_key = {}
    for r in refs:
        by_key.setdefault(r["key"], []).append(r)
    out = []
    for t, ref in S.identified_sites(text, refs):
        bump("1 参照先が 1 つに決まる数")
        elem, _, ctx = ref["key"].partition("@")
        if not ctx.startswith("CurrentYear"):
            continue
        bump("2 参照先の枠が CurrentYear で始まる")
        pk = "%s@%s" % (elem, "Prior1Year" + ctx[len("CurrentYear"):])
        cands = by_key.get(pk, [])
        if len(cands) != 1:
            continue
        prior = cands[0]
        bump("3 同じ要素の Prior1Year の fact が 1 件在る")
        if prior.get("unit") != ref.get("unit"):
            continue
        bump("4 単位が同じ")
        if not (prior["value"] > 0 and ref["value"] > 0 and abs(prior["value"] - ref["value"]) > TOL):
            continue
        bump("5 どちらも正で値が違う")
        factor = SC.scale_of(t.unit) or 1
        cand = prior["value"] / float(factor)
        rendered = N.render_value(cand, t)
        try:
            back = float(rendered.replace(",", "")) * factor
        except ValueError:
            continue
        if abs(back - prior["value"]) > max(TOL, abs(prior["value"]) * 1e-9) or rendered == t.text:
            continue
        bump("6 元の字の形で 1 字違わず書ける")
        out.append({"type": "T6_PRIOR", "token": t, "ref": ref, "prior": prior, "prior_key": pk,
                    "element": elem, "new_value": cand, "rendered": rendered})
    return out


def build_t6(site, refs, rng):
    """前期の値への置換: the replacement is the same element's Prior1Year value."""
    t = site["token"]
    return {
        "new_value": site["new_value"],
        "replacement": site["rendered"],
        "span": [t.start, t.end],
        "detail": {
            "element": site["element"],
            "original_value": t.value,
            "prior_value": site["new_value"],
            "prior_value_in_reference_units": site["prior"]["value"],
            "true_ref_key": site["ref"]["key"],
            "prior_ref_key": site["prior_key"],
            "replacement_present_in_reference_numbers": True,
        },
        "expected": (
            "値は書類の中に実在する(同じ要素の前期の値)。値だけを探す照合は通りうる。"
            "参照先の期間まで解いて比べる照合だけが止める"
        ),
    }


def _bump_last_digit(token, delta):
    """``token`` の字面の**最後の桁**を delta(+1 / -1)する。繰り上がり・繰り下がりで桁数が変わる値、
    0 以下になる値は None。位取りの区切りと小数点の位置は元の字のまま。"""
    s = token.text.replace(",", "")
    ip, _dot, fp = s.partition(".")
    digits = ip + fp
    n = int(digits)
    m = n + delta
    if m <= 0 or len(str(m)) != len(str(n)):
        return None
    nd = str(m).zfill(len(digits))
    nip, nfp = nd[:len(ip)], nd[len(ip):]
    if token.has_comma:
        chunks, body = [], nip
        while len(body) > 3:
            chunks.insert(0, body[-3:])
            body = body[:-3]
        chunks.insert(0, body)
        nip = ",".join(chunks)
    out = nip + (("." + nfp) if fp else "")
    return out


def t7_sites(text, refs, rng, diag=None):
    """有効数字の最後の桁を ±1 する(T7_ROUND)の site. 段 2(2026-10-20)。封の意図は 2,206 -> 2,207 = 丸めの帯の中。

    Site = 値が refs のどこかに在る数(``sites.data_bearing_sites``。T1 と同じ「データを運ぶ数」)のうち、次を全部満たすもの。

    1. 最後の桁を +1 か -1 しても桁数が変わらず 0 以下にならない
    2. (a) 字面の桁(区切りと小数点を除いた数字の並びを整数にしたもの)が 3 桁以上 = ±1 が 1% 以下
    3. (b) 後の値が refs のどの fact の値とも一致しない(偶然一致は T5 の型であって丸めではない)

    符号は ``rng``(select が T7 専用に用意した乱数。主の乱数は使わない)で先に選び、選んだ側が作れなければ逆側。
    ``diag`` (dict)を渡すと、各段を通った site の数を足す(1 つの数は 1 段に 1 回だけ数える)。
    """
    def bump(seen, k):
        if k not in seen:
            seen.add(k)
            if diag is not None:
                diag[k] = diag.get(k, 0) + 1

    vindex = S._value_index(refs)
    out = []
    for t, cands in S.data_bearing_sites(text, refs):
        seen = set()
        bump(seen, "1 データを運ぶ数(値が refs に在る)")
        if t.value == 0:
            continue
        order = [1, -1]
        rng.shuffle(order)
        for delta in order:
            rendered = _bump_last_digit(t, delta)
            if rendered is None or rendered == t.text:
                continue
            bump(seen, "2 最後の桁 ±1 で桁数が変わらず正")
            if len(str(int(t.text.replace(",", "").replace(".", "")))) < 3:
                continue
            bump(seen, "3 (a) 字面の桁が 3 桁以上(±1 が 1% 以下)")
            new = float(rendered.replace(",", ""))
            if S._matches(new, t.unit, vindex):
                continue
            bump(seen, "4 (b) 後の値が refs のどの fact の値とも一致しない")
            out.append({"type": "T7_ROUND", "token": t, "candidates": cands, "delta": delta,
                        "new_value": new, "rendered": rendered, "new_value_present_in_refs": False})
            break
    return out


def build_t7(site, refs, rng):
    """最後の桁 ±1: the digits keep their length, the last digit moves by one."""
    t = site["token"]
    return {
        "new_value": site["new_value"],
        "replacement": site["rendered"],
        "span": [t.start, t.end],
        "detail": {
            "original_value": t.value,
            "replacement_value": site["new_value"],
            "difference": site["new_value"] - t.value,
            "last_digit_delta": site["delta"],
            "replacement_present_in_reference_numbers": site["new_value_present_in_refs"],
            "candidate_ref_keys": sorted({r["key"] for r in site["candidates"]})[:8],
            "candidate_ref_count": len({r["key"] for r in site["candidates"]}),
        },
        "expected": "最後の桁だけ違う。丸めの帯の中に入りうる(許容帯で通る照合は通す)。帯の外へ出す照合だけが止める",
    }


BUILDERS = {
    "T1_VALUE": build_t1,
    "T2_UNIT": build_t2,
    "T3_ABSENT": build_t3,
    "T5_COINCIDENT": build_t5,
    "T6_PRIOR": build_t6,
    "T7_ROUND": build_t7,
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


def select(text, refs, kind, seed, doc_id, count, types=None, quota=None, fallback=None):
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
    # 段 2 の 2 型は、名前で明示されたときだけ catalog に足す。上の 4 型の shuffle と builder が使う主の乱数 ``rng``
    # には触れない(型ごとの別の乱数)ので、types を明示しない呼び出しの結果は 1 字も変わらない。
    for et in EXTRA_TYPES:
        if et in allowed:
            erng = random.Random("%s|%s|%s" % (seed, doc_id, et))
            if et == "T6_PRIOR":
                catalog[et] = t6_sites(text, refs)
            else:
                catalog[et] = t7_sites(text, refs, erng)
            erng.shuffle(catalog[et])
            counts[et] = len(catalog[et])
    withheld = {t: counts[t] for t in MACHINE_TYPES if t not in allowed}
    chosen, spans, cursor = [], [], {t: 0 for t in MACHINE_TYPES + EXTRA_TYPES}
    # One injection per number token. A value substitution and a unit shift on
    # the same number do not overlap as spans, but together they make the
    # record unattributable: a detection could not be credited to either type.
    claimed_tokens = set()
    used_subjects, used_values = set(), set()
    # Round-robin so no type is starved, then keep going while anything is left.
    # ``quota`` (型 -> 件数)を渡したときだけ、まず各型を quota まで採り(phase 0)、足りない分を
    # quota を外して同じ順で埋める(phase 1)。渡さなければ phase 1 だけ = 従来どおり。
    # ``fallback`` (型の並び)を渡したときだけ、phase 1 でも誰も採れなくなってから、その型を最後の手段として
    # ``allowed`` の後ろに足して続ける(既存の型 T1_VALUE などで埋めるとき)。渡さなければ従来どおり。
    order = list(allowed)
    pending = [t for t in (fallback or []) if t not in order]
    phase = 0 if quota else 1
    while len(chosen) < count:
        progressed = False
        for t in order:
            if len(chosen) >= count:
                break
            if phase == 0 and sum(1 for c in chosen if c["type"] == t) >= quota.get(t, count):
                continue
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
            if phase == 0:
                phase = 1
                continue
            if pending:
                order += pending
                pending = []
                continue
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
