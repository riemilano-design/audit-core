import unittest

from audit_core import Comparison, Registry, State, UnknownRegistration


def _never_called_comparator(resolved, claim, contract):
    raise AssertionError("comparator should not be invoked in this test")


class DefaultRegistryTest(unittest.TestCase):
    def test_default_has_exactly_builtin_scheme_and_equals_comparator(self):
        registry = Registry.default()
        info = registry.scheme("builtin")
        self.assertEqual(info.kind, "operator")
        self.assertEqual(info.trust, "structural")
        self.assertFalse(info.carries_approval)
        self.assertTrue(callable(registry.comparator("equals")))
        with self.assertRaises(UnknownRegistration):
            registry.scheme("anything-else")
        with self.assertRaises(UnknownRegistration):
            registry.comparator("anything-else")

    def test_default_has_no_normalizations_or_reasons(self):
        registry = Registry.default()
        with self.assertRaises(UnknownRegistration):
            registry.normalization("round")
        with self.assertRaises(UnknownRegistration):
            registry.reason_state("no-such-reason")


class UnknownLookupTest(unittest.TestCase):
    def test_unknown_scheme_raises(self):
        registry = Registry()
        with self.assertRaises(UnknownRegistration):
            registry.scheme("never-registered")

    def test_unknown_comparator_raises(self):
        registry = Registry()
        with self.assertRaises(UnknownRegistration):
            registry.comparator("never-registered")

    def test_unknown_reason_raises(self):
        registry = Registry()
        with self.assertRaises(UnknownRegistration):
            registry.reason_state("never-registered")


class DoubleRegistrationTest(unittest.TestCase):
    def test_double_register_scheme_raises(self):
        registry = Registry()
        registry.register_scheme("alpha", kind="evidence", trust="high")
        with self.assertRaises(ValueError):
            registry.register_scheme("alpha", kind="operator", trust="low")

    def test_double_register_comparator_raises(self):
        registry = Registry()
        registry.register_comparator("cmp-a", _never_called_comparator)
        with self.assertRaises(ValueError):
            registry.register_comparator("cmp-a", _never_called_comparator)

    def test_double_register_normalization_raises(self):
        registry = Registry()
        registry.register_normalization("norm-a")
        with self.assertRaises(ValueError):
            registry.register_normalization("norm-a")

    def test_double_register_reason_raises(self):
        registry = Registry()
        registry.register_reason("reason-a", State.UNVERIFIABLE)
        with self.assertRaises(ValueError):
            registry.register_reason("reason-a", State.POINTER_NOT_FOUND)


class ReasonStateRestrictionTest(unittest.TestCase):
    def test_grounded_is_rejected(self):
        registry = Registry()
        with self.assertRaises(ValueError):
            registry.register_reason("reason-g", State.GROUNDED)

    def test_value_mismatch_is_rejected(self):
        registry = Registry()
        with self.assertRaises(ValueError):
            registry.register_reason("reason-v", State.VALUE_MISMATCH)

    def test_unverifiable_and_not_found_are_accepted(self):
        registry = Registry()
        registry.register_reason("reason-u", State.UNVERIFIABLE)
        registry.register_reason("reason-f", State.POINTER_NOT_FOUND)
        self.assertIs(registry.reason_state("reason-u"), State.UNVERIFIABLE)
        self.assertIs(registry.reason_state("reason-f"), State.POINTER_NOT_FOUND)


class SchemeKindValidationTest(unittest.TestCase):
    def test_invalid_kind_raises(self):
        registry = Registry()
        with self.assertRaises(ValueError):
            registry.register_scheme("alpha", kind="not-a-real-kind", trust="high")


if __name__ == "__main__":
    unittest.main()
