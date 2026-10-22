# -*- coding: utf-8 -*-
import unittest

import audit_core as core

from adapters.kokkai import registry_setup as RS


class RegistrySetupTest(unittest.TestCase):
    def setUp(self):
        self.reg = RS.register_all(core.Registry.default())

    def test_scheme_is_evidence(self):
        self.assertEqual(self.reg.scheme("kokkai").kind, "evidence")

    def test_three_comparators(self):
        for name in ("speaker_equals", "quote_in_speech", "number_in_speech"):
            self.assertTrue(callable(self.reg.comparator(name)))

    def test_two_unverifiable_reasons(self):
        self.assertIs(self.reg.reason_state(RS.NO_POINTER_GIVEN), core.State.UNVERIFIABLE)
        self.assertIs(self.reg.reason_state(RS.NO_SPEAKER_GIVEN), core.State.UNVERIFIABLE)

    def test_unknown_name_raises(self):
        with self.assertRaises(core.UnknownRegistration):
            self.reg.comparator("equals_within")

    def test_builtin_equals_is_still_there(self):
        self.assertTrue(callable(self.reg.comparator("equals")))
