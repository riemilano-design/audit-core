# -*- coding: utf-8 -*-
"""Shared synthetic test material: a small Observation Packet and a small
seat envelope, built by hand (not read from ``scripts/playtest/out/``,
which C-2's tests must not touch -- see the task's instruction and
``test_mutations.py``'s module docstring).

Not a ``test_*`` module, so ``unittest discover`` does not try to run it.
"""


def synthetic_packet():
    """A packet with one aggregate row (fraction) and one facts row, shaped
    like ``docs/golden_master``'s c5 packet (minimal subset: just enough
    for ``aggregates.<id>.numerator|denominator|value`` and
    ``facts.<col>[n].<field>`` to resolve)."""

    return {
        "packetId": "synthetic0000001",
        "customerRef": "zzzz9",
        "aggregates": [
            {"id": "groups.core.games", "value": 20},
            {"id": "side_match.attack", "numerator": 7, "denominator": 20},
        ],
        "facts": {
            "games": [{"gameId": "g1", "result": "win"}, {"gameId": "g2", "result": "loss"}],
            "moves": [{"usi": "7g7f"}, {"usi": "3c3d"}, {"usi": "2g2f"}],
            "recognition": {
                "rows": [{"selfSignature": "ibisha", "names": ["四間飛車"]}],
                "definitions": [{"id": "d1", "name": "四間飛車", "nameKana": "しけんびしゃ"}],
            },
        },
    }


def synthetic_seat_envelope():
    """One hypothesis line with: a GROUNDED-bound observation
    (``aggregates.groups.core.games.value`` == 20), a VALUE_MISMATCH-bound
    observation (``aggregates.side_match.attack.numerator`` claimed as 99,
    packet has 7), a POINTER_NOT_FOUND-bound observation (a row id that is
    not in the packet), one observation with no ``packetRef`` at all (not
    built into any Claim), and one ``counterEvidence`` observation (always
    UNVERIFIABLE)."""

    return {
        "items": [
            {
                "schemaVersion": "0.4",
                "hypothesisId": "H-z1-time-001",
                "kind": "finding",
                "observations": [
                    {
                        "obsId": "o1",
                        "path": "aggregates.groups.core.games.value",
                        "value": 20,
                        "packetRef": {"path": "aggregates.groups.core.games.value"},
                    },
                    {
                        "obsId": "o2",
                        "path": "aggregates.side_match.attack.numerator",
                        "value": 99,
                        "packetRef": {"path": "aggregates.side_match.attack.numerator"},
                    },
                    {
                        "obsId": "o3",
                        "path": "aggregates.no_such_row.value",
                        "value": 1,
                        "packetRef": {"path": "aggregates.no_such_row.value"},
                    },
                    {
                        "obsId": "o4",
                        "path": "no.packet.ref.here",
                        "value": 1,
                    },
                ],
                "counterEvidence": {
                    "attempted": True,
                    "items": [
                        {
                            "kind": "counterexample",
                            "text": "...",
                            "observations": [
                                {"obsId": "ce1", "path": "facts.moves[0].usi", "value": "7g7f"},
                            ],
                        }
                    ],
                },
            }
        ]
    }
