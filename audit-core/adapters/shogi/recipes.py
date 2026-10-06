# -*- coding: utf-8 -*-
"""Build Core ``Recipe`` objects from the shogi Golden Master's seat
envelopes + packet (C-2 plan §2's "4 層への写し" table).

``build_recipes(seat_envelopes, packet)``: ``seat_envelopes`` is a list
of ``(run_id, seat_file_name, envelope_dict)``. For every hypothesis
line (``envelope["items"][i]``, matching ``goldenMasterCheck.ts``'s
``items.map((line) => validateHypothesisLine(line, ...))``):

  (a) every ``observations[j]`` that has a ``packetRef.path`` becomes
      one bound Claim (``id`` ``"<run_id>/<seat_file>#<hypothesis_id>/
      observations[<j>]"``). An observation **without** a
      ``packetRef.path`` is not H-9's concern (``packetRefObservations``
      in ``hypothesis.ts`` never collects it either) and is not built
      into a Recipe at all -- it is simply absent from the Claim
      population, not represented as any kind of failure.
  (b) every ``counterEvidence.items[k].observations[j]`` becomes one
      ``UNVERIFIABLE`` Claim regardless of whether it has a
      ``packetRef.path`` (C-2 plan §2/§4.2, human decision 8.4: the
      counter-evidence observations are counted in the input
      population, but ruled out of H-9's scope by construction, not
      verified).

The **value → Pointer binding is resolved at build time** (mirrors the
XBRL Adapter's ``no_element`` short-circuit pattern, C-2 plan §2's
closing paragraph): a (a)-Claim whose path does not resolve gets
``Recipe.not_found_reason`` set to one of :mod:`resolve`'s 5 kinds
(the Core never calls the resolver for it); a path that does resolve
gets a full ``Contract`` (``comparator="canonical_json_equals"``,
``params={"expected": <the observation's own value>}``) and the Core's
resolver (:func:`resolve.make_resolver`) re-resolves the same pointer
when ``verify_all`` runs (redundant with the build-time check, but
harmless -- same function, same packet).

``statement`` (the hypothesis line's natural-language sentence) is
never read here, matching C-2 plan §2's "文は Claim に入れない・出力にも
書かない".
"""

import audit_core as core

from . import resolve as RV

NO_PACKET_REF_REASON = "no_packet_ref(H-9 out of scope)"


def _value_of(obs):
    value = obs.get("value") if isinstance(obs, dict) else None
    is_number = isinstance(value, (int, float)) and not isinstance(value, bool)
    return value, is_number


def _form_of(subject):
    if isinstance(subject, str) and subject.startswith("aggregates."):
        return core.Form.AGGREGATE
    return core.Form.DIRECT_VALUE


def _packet_ref_path_of(obs):
    packet_ref = obs.get("packetRef") if isinstance(obs, dict) else None
    path = packet_ref.get("path") if isinstance(packet_ref, dict) else None
    return path if isinstance(path, str) else None


def _primary_recipe(run_id, seat_file, hypothesis_id, kind, obs, j, packet):
    if not isinstance(obs, dict):
        return None
    path = _packet_ref_path_of(obs)
    if path is None:
        return None  # (a): no packetRef.path -> not H-9's concern, no Claim at all.

    value, is_number = _value_of(obs)
    at = "observations[%d]" % (j,)
    claim_id = "%s/%s#%s/%s" % (run_id, seat_file, hypothesis_id, at)
    claim = core.Claim(
        id=claim_id,
        form=_form_of(path),
        subject=path,
        value=float(value) if is_number else None,
        unit=obs.get("unit"),
        modifiers=core.Modifiers(),
        provenance={
            "hypothesis_id": hypothesis_id,
            "kind": kind,
            "obs_id": obs.get("obsId"),
            "value_is_number": is_number,
            "raw_value": value,
            "at": at,
        },
    )
    pointers = (core.Pointer("packet", path),)
    ok, kind_or_value, _reason_text = RV.resolve_packet_path(packet, path)
    if not ok:
        return core.Recipe(claim=claim, pointers=pointers, contract=None, not_found_reason=kind_or_value)
    contract = core.Contract(comparator="canonical_json_equals", params={"expected": value})
    return core.Recipe(claim=claim, pointers=pointers, contract=contract)


def _counter_evidence_recipe(run_id, seat_file, hypothesis_id, kind, obs, k, j):
    if not isinstance(obs, dict):
        obs = {}
    path = _packet_ref_path_of(obs)
    subject = path if path is not None else obs.get("path")
    if not isinstance(subject, str):
        subject = None
    value, is_number = _value_of(obs)
    at = "counterEvidence.items[%d].observations[%d]" % (k, j)
    claim_id = "%s/%s#%s/%s" % (run_id, seat_file, hypothesis_id, at)
    claim = core.Claim(
        id=claim_id,
        form=_form_of(subject),
        subject=subject,
        value=float(value) if is_number else None,
        unit=obs.get("unit"),
        modifiers=core.Modifiers(),
        provenance={
            "hypothesis_id": hypothesis_id,
            "kind": kind,
            "obs_id": obs.get("obsId"),
            "value_is_number": is_number,
            "raw_value": value,
            "at": at,
        },
    )
    return core.Recipe(claim=claim, pointers=(), contract=None, unverifiable_reason=NO_PACKET_REF_REASON)


def build_recipes(seat_envelopes, packet):
    """``seat_envelopes``: iterable of ``(run_id, seat_file_name,
    envelope_dict)``. Returns a flat ``list[core.Recipe]``."""

    recipes = []
    for run_id, seat_file, envelope in seat_envelopes:
        items = envelope.get("items") if isinstance(envelope, dict) else None
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            hypothesis_id = item.get("hypothesisId")
            kind = item.get("kind")

            observations = item.get("observations")
            if isinstance(observations, list):
                for j, obs in enumerate(observations):
                    recipe = _primary_recipe(run_id, seat_file, hypothesis_id, kind, obs, j, packet)
                    if recipe is not None:
                        recipes.append(recipe)

            counter_evidence = item.get("counterEvidence")
            ce_items = counter_evidence.get("items") if isinstance(counter_evidence, dict) else None
            if isinstance(ce_items, list):
                for k, ce_item in enumerate(ce_items):
                    if not isinstance(ce_item, dict):
                        continue
                    ce_observations = ce_item.get("observations")
                    if not isinstance(ce_observations, list):
                        continue
                    for j, obs in enumerate(ce_observations):
                        recipes.append(
                            _counter_evidence_recipe(run_id, seat_file, hypothesis_id, kind, obs, k, j)
                        )
    return recipes
