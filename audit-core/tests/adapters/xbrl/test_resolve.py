# -*- coding: utf-8 -*-
"""C-1d §G: unit tests for ``adapters/xbrl/resolve.py``'s ``make_resolver``
on synthetic facts lists (not real material -- the real-material path is
covered end to end by ``tests/golden/test_instrument3.py``).
"""

import unittest

import audit_core as core

from adapters.xbrl import resolve as RV


def _fact(name, context, value, unit="JPY", decimals=None):
    return {"name": name, "context": context, "value": value, "unit": unit, "decimals": decimals}


class MakeResolverTest(unittest.TestCase):
    def test_resolves_known_pointer(self):
        facts = [_fact("jppfs_cor:Assets", "CurrentYearInstant", 42.0, decimals="-6")]
        resolver = RV.make_resolver(facts)
        pointer = core.Pointer.parse("xbrl:jppfs_cor:Assets@CurrentYearInstant")
        resolved = resolver(pointer)
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.value, 42.0)
        self.assertEqual(resolved.unit, "JPY")
        self.assertEqual(resolved.precision, 1e6)
        self.assertEqual(resolved.meta["duplicates"], 1)
        self.assertEqual(resolved.meta["distinct_values"], 1)

    def test_unknown_pointer_resolves_to_none(self):
        facts = [_fact("jppfs_cor:Assets", "CurrentYearInstant", 42.0)]
        resolver = RV.make_resolver(facts)
        pointer = core.Pointer.parse("xbrl:jppfs_cor:Liabilities@CurrentYearInstant")
        self.assertIsNone(resolver(pointer))

    def test_wrong_context_resolves_to_none(self):
        facts = [_fact("jppfs_cor:Assets", "CurrentYearInstant", 42.0)]
        resolver = RV.make_resolver(facts)
        pointer = core.Pointer.parse("xbrl:jppfs_cor:Assets@Prior1YearInstant")
        self.assertIsNone(resolver(pointer))

    def test_duplicates_same_value_is_not_ambiguous(self):
        facts = [
            _fact("jppfs_cor:Assets", "CurrentYearInstant", 7.0),
            _fact("jppfs_cor:Assets", "CurrentYearInstant", 7.0),
        ]
        resolver = RV.make_resolver(facts)
        resolved = resolver(core.Pointer.parse("xbrl:jppfs_cor:Assets@CurrentYearInstant"))
        self.assertEqual(resolved.meta["duplicates"], 2)
        self.assertEqual(resolved.meta["distinct_values"], 1)

    def test_duplicates_different_values_is_ambiguous(self):
        facts = [
            _fact("jppfs_cor:Assets", "CurrentYearInstant", 7.0),
            _fact("jppfs_cor:Assets", "CurrentYearInstant", 9.0),
        ]
        resolver = RV.make_resolver(facts)
        resolved = resolver(core.Pointer.parse("xbrl:jppfs_cor:Assets@CurrentYearInstant"))
        self.assertEqual(resolved.meta["distinct_values"], 2)

    def test_first_in_instance_order_is_chosen(self):
        facts = [
            _fact("jppfs_cor:Assets", "CurrentYearInstant", 7.0),
            _fact("jppfs_cor:Assets", "CurrentYearInstant", 9.0),
        ]
        resolver = RV.make_resolver(facts)
        resolved = resolver(core.Pointer.parse("xbrl:jppfs_cor:Assets@CurrentYearInstant"))
        self.assertEqual(resolved.value, 7.0)

    def test_decimals_inf_gives_no_precision(self):
        facts = [_fact("jppfs_cor:Assets", "CurrentYearInstant", 7.0, decimals="INF")]
        resolver = RV.make_resolver(facts)
        resolved = resolver(core.Pointer.parse("xbrl:jppfs_cor:Assets@CurrentYearInstant"))
        self.assertIsNone(resolved.precision)

    def test_decimals_none_gives_no_precision(self):
        facts = [_fact("jppfs_cor:Assets", "CurrentYearInstant", 7.0, decimals=None)]
        resolver = RV.make_resolver(facts)
        resolved = resolver(core.Pointer.parse("xbrl:jppfs_cor:Assets@CurrentYearInstant"))
        self.assertIsNone(resolved.precision)

    def test_qualified_name_with_colon_round_trips(self):
        # Pointer.parse splits only on the first ':' (the scheme
        # separator), so the element's own namespace colon survives into
        # the locator and must be split on "@" here, not ":".
        facts = [_fact("jpcrp030000-asr_E05055-000:FooMember", "CurrentYearDuration_bar", 1.0)]
        resolver = RV.make_resolver(facts)
        pointer = core.Pointer.parse("xbrl:jpcrp030000-asr_E05055-000:FooMember@CurrentYearDuration_bar")
        resolved = resolver(pointer)
        self.assertEqual(resolved.value, 1.0)


if __name__ == "__main__":
    unittest.main()
