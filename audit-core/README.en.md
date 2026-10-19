# Audit Core

Audit Core is an XBRL audit verification engine. It checks whether a claim about a
filed financial fact (EDINET, Japan) is grounded in the instance document, and whether
the claimed value matches. It does not judge whether a number is good or bad, and it
does not run a language model.

## Where this currently loses

On a 24-claim gold-confirmed subset (of 35 claims checked against a single spreadsheet),
a general-purpose LLM connected every claim to the correct source cell: **24/24**. Audit
Core connected **12/24**, and held (declined to answer rather than guess) on the other
12, with zero wrong connections. This is a real, measured gap, not a rounding
difference, and it is the headline number in this file, not a footnote.

## What this checks, measured

- Attribute-injection probe (adversarial, not the production path): when unit, period,
  or dimension attributes are tampered with (measured 2026-10-17, before the production
  hold rules described in the next bullet existed), the tamper goes undetected on unit
  **24/24**, period **18/18**, and dimension **24/24** of the lines tried.
- Production path: the same three kinds of tampering are held (declined) **18/18**
  (period), **24/24** (unit), **24/24** (dimension); **192/192** lines reproduce a prior
  measurement stage's states exactly.
- On the gold set, correct references are held (declined) on **0/50** lines -- the hold
  rule does not fire on correct material.
- Error detection (spreadsheet domain, one blinded seat): a general-purpose LLM
  detected **8/8** injected errors; a prior design (the LLM's answers passed
  through an earlier verification layer that overwrote 4 of the LLM's correct
  findings) detected **4/8**; the revised detector detects **8/8**, with 0
  overwrites of the seat's own finding.
- False-pass rate on small transcription errors in the national-parliament-minutes
  domain (a separate dataset): **1/49**.

## What this does not check

Existence and value are the checks above. Unit, period, dimension, and duplicate facts
are not independently verified by this engine's own path (see the Japanese primary
documentation and fixtures referenced below for the full breakdown).

## Install (0 cost, no network required at build time)

```
pip install . --no-build-isolation
```

Two console scripts are installed: `audit-core-verify-document` and
`audit-core-verify-external`. Both depend on nothing beyond the standard library (zero runtime
dependencies), Python >= 3.9.

Editable install (`pip install -e .`) on an older toolchain without PEP 660 support
(setuptools < 61, as measured on this machine: 58.0.4) installs successfully but the
combined import `import audit_core, adapters.xbrl.verify_external` from outside the
project directory fails with `ModuleNotFoundError`; the console scripts and a normal
(non-editable) install both work. See the Japanese result document for the measured
detail.

## Test suite

179 test files, 3413 collected test cases (counted by pytest's collection step), including 96
adversarial mutations exercised against the XBRL adapter. The core verification engine
itself is 429 lines (`core/py/audit_core/*.py`): existence and value checks, nothing
else.

## License

Proprietary. Copyright (c) 2026 Yushi Yamanaka. All rights reserved. See `LICENSE`.

## Scope of this file

This is a short excerpt for English-speaking reviewers. The source of truth is the
Japanese documentation and the JSON fixtures it cites; this file adds no capability and
no number that is not already recorded there.
