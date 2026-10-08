# -*- coding: utf-8 -*-
"""C-1d §G (extended by Core 接続 C-1g §1-5 and C-1h §3.4-c, 2026-10-06):
unit tests for ``adapters/xbrl/registry_setup.py``'s ``register_all`` --
the 29 registrations (2 schemes + 9 comparators + 4 normalizations + 14
reasons; C-1d's 21 plus C-1g's 2 P6-only comparators and 1 P6-only
reason, plus C-1h's 1 P7-only comparator and 3 P7-only reasons) and the
two states a duplicate registration must raise in (``builtin`` is
Core's own, already registered by ``Registry.default()``).
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

    def test_nine_comparators_registered_and_callable(self):
        names = (
            "equals_within",
            "equals_within(pure*100)",
            "ratio*100",
            "pct_change(cur,prior)",
            "diff(a-b) equals_within",
            "builtin:sign(cur-prior)==direction",
            "builtin:flow_sign(cur)==direction",
            "diff(a-b)(pure*100)",
            "builtin:sign(|cur|-|prior|)==direction",
        )
        self.assertEqual(len(names), 9)
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
        self.assertIs(
            self.registry.comparator("builtin:flow_sign(cur)==direction"), C.builtin_flow_sign_direction
        )
        self.assertIs(self.registry.comparator("diff(a-b)(pure*100)"), C.diff_ab_pure100)
        self.assertIs(
            self.registry.comparator("builtin:sign(|cur|-|prior|)==direction"),
            C.builtin_sign_abs_diff_direction,
        )

    def test_four_normalizations_registered(self):
        for name in ("round", "truncate", "abs+round", "abs+truncate"):
            self.assertEqual(self.registry.normalization(name), name)

    def test_thirteen_reasons_registered_with_correct_states(self):
        pointer_not_found = (
            "no_element",
            "no_element(unit not in XBRL)",
            "no_element(ratio without fact)",
            "no_prior_member_context",
            "no_element(point without prior phrase)",
            "no_element(text needs money fact)",
            "no_element(no prior for text)",
            # XBRL 直し §1b(2026-10-08、profile P8 のみ)。
            "no_element(no prior2 for prior-year diff)",
        )
        unverifiable = (
            "no_subject",
            "ambiguous(member)",
            "ambiguous(elements)",
            "state_word(no line)",
            "prior is 0",
            "target_or_plan",
        )
        self.assertEqual(len(pointer_not_found) + len(unverifiable), 14)
        for name in pointer_not_found:
            self.assertEqual(self.registry.reason_state(name), core.State.POINTER_NOT_FOUND)
        for name in unverifiable:
            self.assertEqual(self.registry.reason_state(name), core.State.UNVERIFIABLE)

    def test_register_all_registration_counts_from_registry(self):
        """Core 接続 C-1h: 直書きでなく、``register_all`` 後の登録簿そのものを
        数える(RS モジュールの private なタプルの長さと一致することを確認)。
        """

        self.assertEqual(len(RS._COMPARATORS), 9)
        self.assertEqual(len(RS._NORMALIZATIONS), 4)
        self.assertEqual(len(RS._POINTER_NOT_FOUND_REASONS), 8)
        self.assertEqual(len(RS._UNVERIFIABLE_REASONS), 6)
        total = 2 + len(RS._COMPARATORS) + len(RS._NORMALIZATIONS) + len(RS._POINTER_NOT_FOUND_REASONS) + len(RS._UNVERIFIABLE_REASONS)
        self.assertEqual(total, 29)

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
