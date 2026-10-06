"""Data types for the Core.

The Core holds no knowledge of any particular subject matter. It only
knows about the shapes below: a claim, a pointer to evidence, a contract
that says how to check the claim, and the result of checking it.
"""

import enum
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Tuple


class Form(enum.Enum):
    """The shape of a claim's assertion."""

    DIRECT_VALUE = "direct_value"
    DERIVED_VALUE = "derived_value"
    AGGREGATE = "aggregate"
    THRESHOLD = "threshold"


class State(enum.Enum):
    """The outcome of checking a claim. Exactly four, never more."""

    GROUNDED = "GROUNDED"
    VALUE_MISMATCH = "VALUE_MISMATCH"
    POINTER_NOT_FOUND = "POINTER_NOT_FOUND"
    UNVERIFIABLE = "UNVERIFIABLE"


@dataclass(frozen=True)
class Modifiers:
    """Qualifiers on a claim.

    The Core never interprets these; it only carries them through to the
    result's provenance and lets a comparator read them if it chooses to.
    """

    population: Optional[str] = None
    time_range: Tuple[str, ...] = field(default_factory=tuple)
    normalization: Optional[str] = None


@dataclass(frozen=True)
class Pointer:
    """A reference to a piece of evidence, or to an operator.

    The Core does not interpret ``locator``. Resolution is delegated to a
    resolver function supplied by the caller.
    """

    scheme: str
    locator: str

    @staticmethod
    def parse(text: str) -> "Pointer":
        if ":" not in text:
            raise ValueError("pointer text has no scheme separator ':': %r" % (text,))
        scheme, locator = text.split(":", 1)
        return Pointer(scheme=scheme, locator=locator)

    def __str__(self) -> str:
        return "%s:%s" % (self.scheme, self.locator)


@dataclass(frozen=True)
class Claim:
    """An assertion to be checked."""

    id: str
    form: Form
    subject: Optional[str]
    value: Optional[float]
    unit: Optional[str]
    modifiers: Modifiers
    provenance: Mapping[str, Any]


@dataclass(frozen=True)
class Contract:
    """How a claim is to be checked."""

    comparator: str
    params: Mapping[str, Any]
    formula: Optional[str] = None
    reference: Optional[Pointer] = None


@dataclass(frozen=True)
class Recipe:
    """A claim bundled with the pointers and contract needed to check it.

    ``unverifiable_reason`` and ``not_found_reason`` let the recipe's
    builder short-circuit verification before any pointer is resolved or
    any comparator is run (for example, when the builder already knows the
    claim has no identifiable subject, or that a required element is
    missing from the material).
    """

    claim: Claim
    pointers: Tuple[Pointer, ...]
    contract: Optional[Contract]
    unverifiable_reason: Optional[str] = None
    not_found_reason: Optional[str] = None


@dataclass(frozen=True)
class Resolved:
    """What a resolver returns for one pointer."""

    value: Optional[float]
    unit: Optional[str]
    precision: Optional[float]
    meta: Mapping[str, Any]


@dataclass(frozen=True)
class Comparison:
    """What a registered comparator returns."""

    match: bool
    recomputed: Optional[float]
    depth: str
    detail: Mapping[str, Any]


@dataclass(frozen=True)
class Result:
    """The outcome of verifying one recipe."""

    claim_id: str
    state: State
    recomputed: Optional[float]
    achieved_depth: Optional[str]
    comparator: Optional[str]
    reason: Optional[str]
    pointers: Tuple[str, ...]
    provenance: Mapping[str, Any]
