"""Registries of schemes, comparators, normalizations and reasons.

The Core ships with almost nothing registered. Everything that knows
about a particular kind of evidence or a particular way of comparing
values is registered by the caller at startup.
"""

from dataclasses import dataclass
from typing import Callable, Dict, Sequence

from .model import Claim, Comparison, Contract, Resolved, State


class UnknownRegistration(KeyError):
    """Raised when something asks for a name that was never registered."""


@dataclass(frozen=True)
class SchemeInfo:
    kind: str  # "evidence" or "operator"
    trust: str
    carries_approval: bool = False


ComparatorFn = Callable[[Sequence[Resolved], Claim, Contract], Comparison]


class Registry:
    """A mutable table of names a caller has registered.

    Lookups for a name that was never registered raise
    :class:`UnknownRegistration` rather than falling back to a default.
    """

    def __init__(self) -> None:
        self._schemes = {}  # type: Dict[str, SchemeInfo]
        self._comparators = {}  # type: Dict[str, ComparatorFn]
        self._normalizations = set()  # type: set
        self._reasons = {}  # type: Dict[str, State]

    def register_scheme(self, name, kind, trust, carries_approval=False):
        if kind not in ("evidence", "operator"):
            raise ValueError("scheme kind must be 'evidence' or 'operator', got %r" % (kind,))
        if name in self._schemes:
            raise ValueError("scheme %r is already registered" % (name,))
        self._schemes[name] = SchemeInfo(kind=kind, trust=trust, carries_approval=carries_approval)

    def register_comparator(self, name, fn):
        if name in self._comparators:
            raise ValueError("comparator %r is already registered" % (name,))
        self._comparators[name] = fn

    def register_normalization(self, name):
        if name in self._normalizations:
            raise ValueError("normalization %r is already registered" % (name,))
        self._normalizations.add(name)

    def register_reason(self, name, state):
        if state not in (State.UNVERIFIABLE, State.POINTER_NOT_FOUND):
            raise ValueError(
                "reason %r may only be registered as UNVERIFIABLE or POINTER_NOT_FOUND, got %r"
                % (name, state)
            )
        if name in self._reasons:
            raise ValueError("reason %r is already registered" % (name,))
        self._reasons[name] = state

    def scheme(self, name):
        try:
            return self._schemes[name]
        except KeyError:
            raise UnknownRegistration(name)

    def comparator(self, name):
        try:
            return self._comparators[name]
        except KeyError:
            raise UnknownRegistration(name)

    def normalization(self, name):
        if name not in self._normalizations:
            raise UnknownRegistration(name)
        return name

    def reason_state(self, name):
        try:
            return self._reasons[name]
        except KeyError:
            raise UnknownRegistration(name)

    @staticmethod
    def default():
        """A registry with only the Core's own built-ins registered.

        Everything else (additional schemes, comparators, normalizations,
        reasons) is the caller's responsibility to register.
        """

        registry = Registry()
        registry.register_scheme("builtin", kind="operator", trust="structural")
        registry.register_comparator("equals", _equals_comparator)
        return registry


def _equals_comparator(resolved, claim, contract):
    value = resolved[0].value
    return Comparison(
        match=(value == claim.value),
        recomputed=value,
        depth="value_match",
        detail={},
    )
