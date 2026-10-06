import unittest

from audit_core import (
    Claim,
    Comparison,
    Contract,
    Form,
    Modifiers,
    Pointer,
    Recipe,
    Registry,
    Resolved,
    Result,
    State,
    UnknownRegistration,
    verify,
    verify_all,
)


def _make_claim(claim_id, provenance=None, modifiers=None, value=7.0):
    return Claim(
        id=claim_id,
        form=Form.DIRECT_VALUE,
        subject="subject-" + claim_id,
        value=value,
        unit="unit-x",
        modifiers=modifiers if modifiers is not None else Modifiers(),
        provenance=provenance if provenance is not None else {},
    )


class _RecordingResolver(object):
    """A resolver stand-in that records every pointer it was asked about."""

    def __init__(self, answers):
        self.answers = answers  # mapping of str(pointer) -> Resolved or None
        self.calls = []

    def __call__(self, pointer):
        self.calls.append(pointer)
        return self.answers.get(str(pointer))


def _make_registry(with_evidence_scheme="ev", with_operator_scheme="op"):
    registry = Registry.default()
    registry.register_scheme(with_evidence_scheme, kind="evidence", trust="high")
    registry.register_scheme(with_operator_scheme, kind="operator", trust="structural")
    return registry


class UnverifiablePathTest(unittest.TestCase):
    def test_unverifiable_reason_short_circuits_before_any_pointer_work(self):
        registry = _make_registry()
        registry.register_reason("cannot-identify", State.UNVERIFIABLE)
        claim = _make_claim("claim-u1")
        resolver = _RecordingResolver({})
        recipe = Recipe(
            claim=claim,
            pointers=(Pointer("ev", "loc-1"),),
            contract=None,
            unverifiable_reason="cannot-identify",
        )
        result = verify(recipe, resolver, registry)
        self.assertEqual(result.state, State.UNVERIFIABLE)
        self.assertEqual(result.reason, "cannot-identify")
        self.assertEqual(result.claim_id, "claim-u1")
        self.assertEqual(resolver.calls, [])

    def test_unverifiable_reason_registered_as_wrong_state_raises(self):
        registry = _make_registry()
        registry.register_reason("actually-not-found", State.POINTER_NOT_FOUND)
        claim = _make_claim("claim-u2")
        recipe = Recipe(
            claim=claim, pointers=(), contract=None, unverifiable_reason="actually-not-found"
        )
        with self.assertRaises(ValueError):
            verify(recipe, _RecordingResolver({}), registry)

    def test_unverifiable_takes_priority_over_not_found(self):
        registry = _make_registry()
        registry.register_reason("reason-un", State.UNVERIFIABLE)
        registry.register_reason("reason-nf", State.POINTER_NOT_FOUND)
        claim = _make_claim("claim-u3")
        recipe = Recipe(
            claim=claim,
            pointers=(),
            contract=None,
            unverifiable_reason="reason-un",
            not_found_reason="reason-nf",
        )
        result = verify(recipe, _RecordingResolver({}), registry)
        self.assertEqual(result.state, State.UNVERIFIABLE)
        self.assertEqual(result.reason, "reason-un")


class NotFoundReasonPathTest(unittest.TestCase):
    def test_not_found_reason_short_circuits_before_pointer_work(self):
        registry = _make_registry()
        registry.register_reason("element-absent", State.POINTER_NOT_FOUND)
        claim = _make_claim("claim-n1")
        resolver = _RecordingResolver({})
        recipe = Recipe(
            claim=claim,
            pointers=(Pointer("ev", "loc-2"),),
            contract=None,
            not_found_reason="element-absent",
        )
        result = verify(recipe, resolver, registry)
        self.assertEqual(result.state, State.POINTER_NOT_FOUND)
        self.assertEqual(result.reason, "element-absent")
        self.assertEqual(resolver.calls, [])

    def test_not_found_reason_registered_as_wrong_state_raises(self):
        registry = _make_registry()
        registry.register_reason("actually-unverifiable", State.UNVERIFIABLE)
        claim = _make_claim("claim-n2")
        recipe = Recipe(
            claim=claim, pointers=(), contract=None, not_found_reason="actually-unverifiable"
        )
        with self.assertRaises(ValueError):
            verify(recipe, _RecordingResolver({}), registry)


class PointerResolutionTest(unittest.TestCase):
    def test_unknown_scheme_raises_unknown_registration_not_a_result(self):
        registry = _make_registry()
        claim = _make_claim("claim-p1")
        recipe = Recipe(claim=claim, pointers=(Pointer("mystery", "loc-3"),), contract=None)
        with self.assertRaises(UnknownRegistration):
            verify(recipe, _RecordingResolver({}), registry)

    def test_operator_pointer_is_never_sent_to_the_resolver(self):
        registry = _make_registry()
        registry.register_comparator(
            "always-true",
            lambda resolved, claim, contract: Comparison(
                match=True, recomputed=resolved[0].value, depth="value_match", detail={}
            ),
        )
        claim = _make_claim("claim-p2")
        evidence_pointer = Pointer("ev", "loc-4")
        operator_pointer = Pointer("op", "loc-5")
        resolver = _RecordingResolver(
            {str(evidence_pointer): Resolved(value=9.0, unit="unit-x", precision=None, meta={})}
        )
        recipe = Recipe(
            claim=claim,
            pointers=(operator_pointer, evidence_pointer),
            contract=Contract(comparator="always-true", params={}),
        )
        verify(recipe, resolver, registry)
        self.assertEqual(resolver.calls, [evidence_pointer])

    def test_unresolved_evidence_pointer_yields_pointer_not_found_with_pointer_text(self):
        registry = _make_registry()
        claim = _make_claim("claim-p3")
        evidence_pointer = Pointer("ev", "loc-6")
        resolver = _RecordingResolver({})  # resolves nothing
        recipe = Recipe(
            claim=claim,
            pointers=(evidence_pointer,),
            contract=Contract(comparator="equals", params={}),
        )
        result = verify(recipe, resolver, registry)
        self.assertEqual(result.state, State.POINTER_NOT_FOUND)
        self.assertEqual(result.reason, "unresolved:ev:loc-6")

    def test_zero_evidence_pointers_yields_no_pointer_reason(self):
        registry = _make_registry()
        claim = _make_claim("claim-p4")
        recipe = Recipe(
            claim=claim,
            pointers=(Pointer("op", "loc-7"),),
            contract=Contract(comparator="equals", params={}),
        )
        result = verify(recipe, _RecordingResolver({}), registry)
        self.assertEqual(result.state, State.POINTER_NOT_FOUND)
        self.assertEqual(result.reason, "no_pointer")

    def test_empty_pointer_tuple_also_yields_no_pointer_reason(self):
        registry = _make_registry()
        claim = _make_claim("claim-p5")
        recipe = Recipe(
            claim=claim, pointers=(), contract=Contract(comparator="equals", params={})
        )
        result = verify(recipe, _RecordingResolver({}), registry)
        self.assertEqual(result.state, State.POINTER_NOT_FOUND)
        self.assertEqual(result.reason, "no_pointer")

    def test_resolver_exception_propagates(self):
        registry = _make_registry()
        claim = _make_claim("claim-p6")

        def _raising_resolver(pointer):
            raise RuntimeError("boom-from-resolver")

        recipe = Recipe(
            claim=claim,
            pointers=(Pointer("ev", "loc-8"),),
            contract=Contract(comparator="equals", params={}),
        )
        with self.assertRaises(RuntimeError):
            verify(recipe, _raising_resolver, registry)


class ContractRequirementTest(unittest.TestCase):
    def test_missing_contract_with_resolved_evidence_raises(self):
        registry = _make_registry()
        claim = _make_claim("claim-c1")
        evidence_pointer = Pointer("ev", "loc-9")
        resolver = _RecordingResolver(
            {str(evidence_pointer): Resolved(value=1.0, unit=None, precision=None, meta={})}
        )
        recipe = Recipe(claim=claim, pointers=(evidence_pointer,), contract=None)
        with self.assertRaises(ValueError):
            verify(recipe, resolver, registry)


class ComparisonOutcomeTest(unittest.TestCase):
    def test_match_true_yields_grounded_with_recomputed_and_depth(self):
        registry = _make_registry()
        registry.register_comparator(
            "cmp-match",
            lambda resolved, claim, contract: Comparison(
                match=True, recomputed=42.0, depth="recount", detail={"note": "d1"}
            ),
        )
        claim = _make_claim("claim-m1")
        evidence_pointer = Pointer("ev", "loc-10")
        resolver = _RecordingResolver(
            {str(evidence_pointer): Resolved(value=1.0, unit=None, precision=None, meta={"src": "m1"})}
        )
        recipe = Recipe(
            claim=claim,
            pointers=(evidence_pointer,),
            contract=Contract(comparator="cmp-match", params={}),
        )
        result = verify(recipe, resolver, registry)
        self.assertEqual(result.state, State.GROUNDED)
        self.assertEqual(result.recomputed, 42.0)
        self.assertEqual(result.achieved_depth, "recount")
        self.assertEqual(result.comparator, "cmp-match")
        self.assertIsNone(result.reason)

    def test_match_false_yields_value_mismatch(self):
        registry = _make_registry()
        registry.register_comparator(
            "cmp-mismatch",
            lambda resolved, claim, contract: Comparison(
                match=False, recomputed=13.0, depth="value_match", detail={}
            ),
        )
        claim = _make_claim("claim-m2")
        evidence_pointer = Pointer("ev", "loc-11")
        resolver = _RecordingResolver(
            {str(evidence_pointer): Resolved(value=1.0, unit=None, precision=None, meta={})}
        )
        recipe = Recipe(
            claim=claim,
            pointers=(evidence_pointer,),
            contract=Contract(comparator="cmp-mismatch", params={}),
        )
        result = verify(recipe, resolver, registry)
        self.assertEqual(result.state, State.VALUE_MISMATCH)
        self.assertEqual(result.recomputed, 13.0)


class ProvenanceTest(unittest.TestCase):
    def test_provenance_carries_claim_provenance_modifiers_meta_and_detail(self):
        registry = _make_registry()
        registry.register_comparator(
            "cmp-prov",
            lambda resolved, claim, contract: Comparison(
                match=True, recomputed=5.0, depth="value_match", detail={"why": "w1"}
            ),
        )
        claim = _make_claim(
            "claim-v1",
            provenance={"origin": "o1"},
            modifiers=Modifiers(population="pop-1", time_range=("t-1", "t-2"), normalization="norm-1"),
        )
        evidence_pointer = Pointer("ev", "loc-12")
        resolver = _RecordingResolver(
            {str(evidence_pointer): Resolved(value=5.0, unit=None, precision=None, meta={"m": "meta-1"})}
        )
        recipe = Recipe(
            claim=claim,
            pointers=(evidence_pointer,),
            contract=Contract(comparator="cmp-prov", params={}),
        )
        result = verify(recipe, resolver, registry)
        self.assertEqual(result.provenance["origin"], "o1")
        self.assertEqual(
            result.provenance["modifiers"],
            {"population": "pop-1", "time_range": ("t-1", "t-2"), "normalization": "norm-1"},
        )
        self.assertEqual(
            result.provenance["resolved_pointers"],
            ({"pointer": "ev:loc-12", "meta": {"m": "meta-1"}},),
        )
        self.assertEqual(result.provenance["comparison"], {"why": "w1"})

    def test_provenance_on_pointer_not_found_still_carries_modifiers(self):
        registry = _make_registry()
        claim = _make_claim(
            "claim-v2",
            provenance={"origin": "o2"},
            modifiers=Modifiers(population="pop-2"),
        )
        recipe = Recipe(
            claim=claim,
            pointers=(Pointer("ev", "loc-13"),),
            contract=Contract(comparator="equals", params={}),
        )
        result = verify(recipe, _RecordingResolver({}), registry)
        self.assertEqual(result.state, State.POINTER_NOT_FOUND)
        self.assertEqual(result.provenance["origin"], "o2")
        self.assertEqual(result.provenance["modifiers"]["population"], "pop-2")


class ResultPointerFieldTest(unittest.TestCase):
    def test_pointers_field_preserves_order_including_operators(self):
        registry = _make_registry()
        registry.register_comparator(
            "cmp-order",
            lambda resolved, claim, contract: Comparison(
                match=True, recomputed=1.0, depth="value_match", detail={}
            ),
        )
        claim = _make_claim("claim-o1")
        p1 = Pointer("op", "first")
        p2 = Pointer("ev", "second")
        p3 = Pointer("op", "third")
        resolver = _RecordingResolver(
            {str(p2): Resolved(value=1.0, unit=None, precision=None, meta={})}
        )
        recipe = Recipe(
            claim=claim, pointers=(p1, p2, p3), contract=Contract(comparator="cmp-order", params={})
        )
        result = verify(recipe, resolver, registry)
        self.assertEqual(result.pointers, ("op:first", "ev:second", "op:third"))


class EqualsComparatorMismatchTest(unittest.TestCase):
    """The Core's own default ``equals`` comparator (Registry.default) must
    actually detect a mismatch, not just pass through pointer-not-found or
    exact-match cases. Exercises the registered comparator directly,
    through ``verify``, with resolved values that differ from the claim.
    """

    def test_equals_comparator_flags_a_clear_mismatch(self):
        registry = Registry.default()
        registry.register_scheme("ev", kind="evidence", trust="high")
        claim = _make_claim("claim-eq1", value=17.0)
        evidence_pointer = Pointer("ev", "loc-30")
        resolver = _RecordingResolver(
            {str(evidence_pointer): Resolved(value=17.5, unit=None, precision=None, meta={})}
        )
        recipe = Recipe(
            claim=claim,
            pointers=(evidence_pointer,),
            contract=Contract(comparator="equals", params={}),
        )
        result = verify(recipe, resolver, registry)
        self.assertEqual(result.state, State.VALUE_MISMATCH)
        self.assertEqual(result.recomputed, 17.5)

    def test_equals_comparator_has_zero_tolerance_even_for_a_tiny_difference(self):
        registry = Registry.default()
        registry.register_scheme("ev", kind="evidence", trust="high")
        claim = _make_claim("claim-eq2", value=23.0)
        evidence_pointer = Pointer("ev", "loc-31")
        resolver = _RecordingResolver(
            {str(evidence_pointer): Resolved(value=23.001, unit=None, precision=None, meta={})}
        )
        recipe = Recipe(
            claim=claim,
            pointers=(evidence_pointer,),
            contract=Contract(comparator="equals", params={}),
        )
        result = verify(recipe, resolver, registry)
        self.assertEqual(result.state, State.VALUE_MISMATCH)


class VerifyAllExceptionPropagationTest(unittest.TestCase):
    def test_verify_all_does_not_swallow_a_resolver_exception(self):
        registry = _make_registry()
        claim_ok = _make_claim("claim-ex1")
        claim_bad = _make_claim("claim-ex2")

        def _raising_resolver(pointer):
            raise RuntimeError("boom-from-verify-all-resolver")

        recipe_ok = Recipe(
            claim=claim_ok,
            pointers=(Pointer("ev", "loc-32"),),
            contract=Contract(comparator="equals", params={}),
        )
        recipe_bad = Recipe(
            claim=claim_bad,
            pointers=(Pointer("ev", "loc-33"),),
            contract=Contract(comparator="equals", params={}),
        )
        with self.assertRaises(RuntimeError):
            verify_all([recipe_ok, recipe_bad], _raising_resolver, registry)


class VerifyAllTest(unittest.TestCase):
    def test_preserves_order_and_maps_each_recipe_to_its_own_result(self):
        registry = _make_registry()
        registry.register_reason("reason-a1", State.UNVERIFIABLE)
        registry.register_reason("reason-a2", State.POINTER_NOT_FOUND)
        claim_a = _make_claim("claim-a1")
        claim_b = _make_claim("claim-a2")
        claim_c = _make_claim("claim-a3")
        recipe_a = Recipe(claim=claim_a, pointers=(), contract=None, unverifiable_reason="reason-a1")
        recipe_b = Recipe(claim=claim_b, pointers=(), contract=None, not_found_reason="reason-a2")
        recipe_c = Recipe(
            claim=claim_c,
            pointers=(Pointer("ev", "loc-20"),),
            contract=Contract(comparator="equals", params={}),
        )
        resolver = _RecordingResolver(
            {"ev:loc-20": Resolved(value=claim_c.value, unit=None, precision=None, meta={})}
        )
        results = verify_all([recipe_a, recipe_b, recipe_c], resolver, registry)
        self.assertEqual([r.claim_id for r in results], ["claim-a1", "claim-a2", "claim-a3"])
        self.assertEqual(results[0].state, State.UNVERIFIABLE)
        self.assertEqual(results[1].state, State.POINTER_NOT_FOUND)
        self.assertEqual(results[2].state, State.GROUNDED)


if __name__ == "__main__":
    unittest.main()
