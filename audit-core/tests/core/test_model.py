import dataclasses
import unittest

from audit_core import Claim, Contract, Form, Modifiers, Pointer, Recipe, State


class PointerParseTest(unittest.TestCase):
    def test_round_trip(self):
        pointer = Pointer.parse("alpha:beta/gamma")
        self.assertEqual(pointer.scheme, "alpha")
        self.assertEqual(pointer.locator, "beta/gamma")
        self.assertEqual(str(pointer), "alpha:beta/gamma")

    def test_round_trip_only_first_colon_splits(self):
        pointer = Pointer.parse("alpha:beta:gamma")
        self.assertEqual(pointer.scheme, "alpha")
        self.assertEqual(pointer.locator, "beta:gamma")
        self.assertEqual(str(pointer), "alpha:beta:gamma")

    def test_missing_colon_raises(self):
        with self.assertRaises(ValueError):
            Pointer.parse("no-colon-here")

    def test_constructed_directly_is_equivalent_to_parsed(self):
        constructed = Pointer(scheme="k", locator="v")
        parsed = Pointer.parse("k:v")
        self.assertEqual(constructed, parsed)


class ModifiersTest(unittest.TestCase):
    def test_defaults(self):
        modifiers = Modifiers()
        self.assertIsNone(modifiers.population)
        self.assertEqual(modifiers.time_range, ())
        self.assertIsNone(modifiers.normalization)

    def test_is_frozen(self):
        modifiers = Modifiers(population="p1", time_range=("t1", "t2"), normalization="n1")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            modifiers.population = "p2"  # type: ignore[misc]


class ClaimTest(unittest.TestCase):
    def test_fields_round_trip(self):
        claim = Claim(
            id="c-9",
            form=Form.DIRECT_VALUE,
            subject="s-9",
            value=12.5,
            unit="u-9",
            modifiers=Modifiers(),
            provenance={"origin": "o-9"},
        )
        self.assertEqual(claim.id, "c-9")
        self.assertIs(claim.form, Form.DIRECT_VALUE)
        self.assertEqual(claim.value, 12.5)
        self.assertEqual(claim.provenance, {"origin": "o-9"})

    def test_is_frozen(self):
        claim = Claim(
            id="c-1",
            form=Form.THRESHOLD,
            subject=None,
            value=None,
            unit=None,
            modifiers=Modifiers(),
            provenance={},
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            claim.id = "c-2"  # type: ignore[misc]


class ContractAndRecipeTest(unittest.TestCase):
    def test_contract_defaults(self):
        contract = Contract(comparator="cmp-7", params={})
        self.assertIsNone(contract.formula)
        self.assertIsNone(contract.reference)

    def test_recipe_optional_reasons_default_to_none(self):
        claim = Claim(
            id="c-3",
            form=Form.AGGREGATE,
            subject="s-3",
            value=3.0,
            unit=None,
            modifiers=Modifiers(),
            provenance={},
        )
        recipe = Recipe(claim=claim, pointers=(), contract=None)
        self.assertIsNone(recipe.unverifiable_reason)
        self.assertIsNone(recipe.not_found_reason)


class StateEnumTest(unittest.TestCase):
    def test_exactly_four_states(self):
        self.assertEqual(
            set(s.value for s in State),
            {"GROUNDED", "VALUE_MISMATCH", "POINTER_NOT_FOUND", "UNVERIFIABLE"},
        )


if __name__ == "__main__":
    unittest.main()
