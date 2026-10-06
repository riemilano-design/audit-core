# -*- coding: utf-8 -*-
"""Unit tests for ``adapters/shogi/registry_setup.py``'s ``register_all``:
8 registrations (1 scheme + 1 comparator + 5 POINTER_NOT_FOUND reasons +
1 UNVERIFIABLE reason; 0 normalizations). ``builtin``/``equals`` are
Core's own, not re-registered here."""

import unittest

import audit_core as core

from adapters.shogi import comparators as C
from adapters.shogi import registry_setup as RS
from adapters.shogi import resolve as RV
from adapters.shogi.recipes import NO_PACKET_REF_REASON


class RegisterAllTest(unittest.TestCase):
    def setUp(self):
        self.registry = RS.register_all(core.Registry.default())

    def test_scheme(self):
        info = self.registry.scheme("packet")
        self.assertEqual(info.kind, "evidence")
        self.assertEqual(info.trust, "tool")
        builtin = self.registry.scheme("builtin")
        self.assertEqual(builtin.kind, "operator")

    def test_registering_builtin_scheme_again_raises(self):
        with self.assertRaises(ValueError):
            self.registry.register_scheme("builtin", kind="operator", trust="structural")

    def test_comparator_registered_and_is_module_function(self):
        self.assertIs(self.registry.comparator("canonical_json_equals"), C.canonical_json_equals)
        self.assertTrue(callable(self.registry.comparator("equals")))

    def test_no_normalizations_registered(self):
        with self.assertRaises(core.UnknownRegistration):
            self.registry.normalization("round")

    def test_five_pointer_not_found_reasons(self):
        for name in (RV.GRAMMAR, RV.NO_ROW, RV.NO_FIELD, RV.INDEX_OUT_OF_RANGE, RV.MISSING_KEY):
            self.assertEqual(self.registry.reason_state(name), core.State.POINTER_NOT_FOUND)

    def test_one_unverifiable_reason(self):
        self.assertEqual(self.registry.reason_state(NO_PACKET_REF_REASON), core.State.UNVERIFIABLE)

    def test_registering_a_reason_twice_raises(self):
        with self.assertRaises(ValueError):
            self.registry.register_reason(RV.GRAMMAR, core.State.POINTER_NOT_FOUND)

    def test_unregistered_name_raises_unknown_registration(self):
        with self.assertRaises(core.UnknownRegistration):
            self.registry.comparator("no_such_comparator")
        with self.assertRaises(core.UnknownRegistration):
            self.registry.reason_state("no_such_reason")

    def test_total_registration_count_is_eight(self):
        # 登録簿から数える(直書きしない) -- 1 scheme + 1 comparator + 6 reasons
        # (builtin の既定 scheme・equals 比較子を除いた、この Adapter 自身の登録数)。
        before = core.Registry.default()
        before_schemes = len(before._schemes)
        before_comparators = len(before._comparators)
        before_reasons = len(before._reasons)
        before_normalizations = len(before._normalizations)
        added_schemes = len(self.registry._schemes) - before_schemes
        added_comparators = len(self.registry._comparators) - before_comparators
        added_reasons = len(self.registry._reasons) - before_reasons
        added_normalizations = len(self.registry._normalizations) - before_normalizations
        self.assertEqual(added_schemes, 1)
        self.assertEqual(added_comparators, 1)
        self.assertEqual(added_reasons, 6)
        self.assertEqual(added_normalizations, 0)
        self.assertEqual(added_schemes + added_comparators + added_reasons + added_normalizations, 8)


if __name__ == "__main__":
    unittest.main()
