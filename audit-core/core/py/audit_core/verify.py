"""The recipe executor.

``verify`` takes one :class:`Recipe`, a resolver function supplied by the
caller, and a :class:`Registry`, and returns one :class:`Result`. It does
not compute anything about the subject matter itself: resolving a
pointer's value is the resolver's job, and comparing values is the
registered comparator's job. The Core only sequences the two and records
what happened.
"""

from typing import Any, Callable, List, Mapping, Optional, Sequence, Tuple

from .model import Pointer, Recipe, Resolved, Result, State
from .registry import Registry

Resolver = Callable[[Pointer], Optional[Resolved]]


def _base_provenance(recipe):
    # type: (Recipe) -> dict
    claim = recipe.claim
    provenance = dict(claim.provenance)
    provenance["modifiers"] = {
        "population": claim.modifiers.population,
        "time_range": claim.modifiers.time_range,
        "normalization": claim.modifiers.normalization,
    }
    return provenance


def _pointer_strings(recipe):
    # type: (Recipe) -> Tuple[str, ...]
    return tuple(str(pointer) for pointer in recipe.pointers)


def verify(recipe, resolver, registry):
    # type: (Recipe, Resolver, Registry) -> Result
    claim = recipe.claim
    pointers = _pointer_strings(recipe)
    provenance = _base_provenance(recipe)

    if recipe.unverifiable_reason is not None:
        state = registry.reason_state(recipe.unverifiable_reason)
        if state is not State.UNVERIFIABLE:
            raise ValueError(
                "reason %r is registered as %s, not UNVERIFIABLE"
                % (recipe.unverifiable_reason, state)
            )
        return Result(
            claim_id=claim.id,
            state=State.UNVERIFIABLE,
            recomputed=None,
            achieved_depth=None,
            comparator=None,
            reason=recipe.unverifiable_reason,
            pointers=pointers,
            provenance=provenance,
        )

    if recipe.not_found_reason is not None:
        state = registry.reason_state(recipe.not_found_reason)
        if state is not State.POINTER_NOT_FOUND:
            raise ValueError(
                "reason %r is registered as %s, not POINTER_NOT_FOUND"
                % (recipe.not_found_reason, state)
            )
        return Result(
            claim_id=claim.id,
            state=State.POINTER_NOT_FOUND,
            recomputed=None,
            achieved_depth=None,
            comparator=None,
            reason=recipe.not_found_reason,
            pointers=pointers,
            provenance=provenance,
        )

    resolved_so_far = []  # type: List[Mapping[str, Any]]
    evidence = []  # type: List[Resolved]
    for pointer in recipe.pointers:
        info = registry.scheme(pointer.scheme)
        if info.kind != "evidence":
            continue
        resolved = resolver(pointer)
        if resolved is None:
            provenance_with_partial = dict(provenance)
            provenance_with_partial["resolved_pointers"] = tuple(resolved_so_far)
            return Result(
                claim_id=claim.id,
                state=State.POINTER_NOT_FOUND,
                recomputed=None,
                achieved_depth=None,
                comparator=None,
                reason="unresolved:" + str(pointer),
                pointers=pointers,
                provenance=provenance_with_partial,
            )
        evidence.append(resolved)
        resolved_so_far.append({"pointer": str(pointer), "meta": resolved.meta})

    if not evidence:
        provenance_with_partial = dict(provenance)
        provenance_with_partial["resolved_pointers"] = tuple(resolved_so_far)
        return Result(
            claim_id=claim.id,
            state=State.POINTER_NOT_FOUND,
            recomputed=None,
            achieved_depth=None,
            comparator=None,
            reason="no_pointer",
            pointers=pointers,
            provenance=provenance_with_partial,
        )

    if recipe.contract is None:
        raise ValueError("recipe %r has no contract" % (claim.id,))

    comparator_fn = registry.comparator(recipe.contract.comparator)
    comparison = comparator_fn(tuple(evidence), claim, recipe.contract)

    provenance["resolved_pointers"] = tuple(resolved_so_far)
    provenance["comparison"] = comparison.detail

    state = State.GROUNDED if comparison.match else State.VALUE_MISMATCH
    return Result(
        claim_id=claim.id,
        state=state,
        recomputed=comparison.recomputed,
        achieved_depth=comparison.depth,
        comparator=recipe.contract.comparator,
        reason=None,
        pointers=pointers,
        provenance=provenance,
    )


def verify_all(recipes, resolver, registry):
    # type: (Sequence[Recipe], Resolver, Registry) -> List[Result]
    return [verify(recipe, resolver, registry) for recipe in recipes]
