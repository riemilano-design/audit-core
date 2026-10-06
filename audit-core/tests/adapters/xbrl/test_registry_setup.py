# -*- coding: utf-8 -*-
"""C-1d §G: unit tests for ``adapters/xbrl/registry_setup.py``'s
``register_all`` -- the 21 registrations (2 schemes + 6 comparators + 4
normalizations + 9 reasons) and the two states a duplicate registration
must raise in (``builtin`` is Core's own, already registered by
``Registry.default()``).
"""

import unittest

import audit_core as core

from adapters.xbrl import comparators as C
from adapters.xbrl import registry_setup as RS


class RegisterAllTest(unittest.TestCase):
    def setUp(self):
        self.registry = RS.register_all(core.Registry.default())

    def test_schemes(self):
        xbrl_scheme = self.registry.scheme("xbrl")
        self.assertEqual(xbrl_scheme.kind, "evidence")
        self.assertEqual(xbrl_scheme.trust, "filing")
        formula_scheme = self.registry.scheme("formula")
        self.assertEqual(formula_scheme.kind, "operator")
        self.assertEqual(formula_scheme.trust, "structural")
        # builtin is Core's own default scheme, not registered again here.
        builtin_scheme = self.registry.scheme("builtin")
        self.assertEqual(builtin_scheme.kind, "operator")

    def test_registering_builtin_scheme_again_raises(self):
        with self.assertRaises(ValueError):
            self.registry.register_scheme("builtin", kind="operator", trust="structural")

    def test_six_comparators_registered_and_callable(self):
        names = (
            "equals_within",
            "equals_within(pure*100)",
            "ratio*100",
            "pct_change(cur,prior)",
            "diff(a-b) equals_within",
            "builtin:sign(cur-prior)==direction",
        )
        self.assertEqual(len(names), 6)
        for name in names:
            fn = self.registry.comparator(name)
            self.assertTrue(callable(fn))
        # Core's own default comparator ("equals") is still present too.
        self.assertTrue(callable(self.registry.comparator("equals")))

    def test_comparator_functions_match_module(self):
        self.assertIs(self.registry.comparator("equals_within"), C.equals_within)
        self.assertIs(self.registry.comparator("equals_within(pure*100)"), C.equals_within_pure100)
        self.assertIs(self.registry.comparator("ratio*100"), C.ratio100)
        self.assertIs(self.registry.comparator("pct_change(cur,prior)"), C.pct_change)
        self.assertIs(self.registry.comparator("diff(a-b) equals_within"), C.diff_ab_equals_within)
        self.assertIs(
            self.registry.comparator("builtin:sign(cur-prior)==direction"), C.builtin_sign_direction
        )

    def test_four_normalizations_registered(self):
        for name in ("round", "truncate", "abs+round", "abs+truncate"):
            self.assertEqual(self.registry.normalization(name), name)

    def test_nine_reasons_registered_with_correct_states(self):
        pointer_not_found = (
            "no_element",
            "no_element(unit not in XBRL)",
            "no_element(ratio without fact)",
            "no_prior_member_context",
        )
        unverifiable = (
            "no_subject",
            "ambiguous(member)",
            "ambiguous(elements)",
            "state_word(no line)",
            "prior is 0",
        )
        self.assertEqual(len(pointer_not_found) + len(unverifiable), 9)
        for name in pointer_not_found:
            self.assertEqual(self.registry.reason_state(name), core.State.POINTER_NOT_FOUND)
        for name in unverifiable:
            self.assertEqual(self.registry.reason_state(name), core.State.UNVERIFIABLE)

    def test_registering_a_reason_twice_raises(self):
        with self.assertRaises(ValueError):
            self.registry.register_reason("no_element", core.State.POINTER_NOT_FOUND)

    def test_unregistered_name_raises_unknown_registration(self):
        with self.assertRaises(core.UnknownRegistration):
            self.registry.comparator("no_such_comparator")
        with self.assertRaises(core.UnknownRegistration):
            self.registry.reason_state("no_such_reason")


if __name__ == "__main__":
    unittest.main()
