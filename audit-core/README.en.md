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

## 10-minute reproduction (no API key, 0 USD; no network except the one-time label download)

Right after cloning, one command run inside `audit-core/` lets you see by hand what the engine passes and what it stops when errors are injected (record `fixtures/xbrl/ritual_2026-10-20.json`, result `docs/XBRL_RITUAL_RESULT_2026-10-20.md`).

**Step 0 (once)**: download the two standard-taxonomy label files from EDINET (two curl commands plus a sha256 check, about 8 MB). The steps and sha256 values are in `fixtures/xbrl/TAXONOMY_LABELS_README.md`. They live in `~/.cache/audit-core/edinet-taxonomy/2025-11-01/` (override with the `EDINET_TAXONOMY_DIR` environment variable) and are not in this repository because they carry the Financial Services Agency's copyright notice. Without them the entry point prints instructions and stops (exit code 2).

**Step 1**:

```
python3 measure/ritual_2026-10-20.py --out <output dir>
```

- **Passed 15 / 240 = 6.2%**: each number in the management-discussion text is deliberately changed, one per sentence (the last digit changed / +-1 in the last printed unit), and the count is how many the engine still reports as GROUNDED.
- Stopped 225 / 240 = 93.8% (VALUE_MISMATCH).
- What the 15 passed are: inside the rounding band (+-1 last unit) 14 (rates 12, amounts and others 2); degenerate (`0` becoming `00` before the unit word: the text changes but the value does not) 1; outside the band 0. Whether these are defects is for the reader to decide.
- The default is P22 (the period is pinned; 2026-10-20). Writing a prior-period value as a current-period number now stops: N125, N199, whose injected value matched the prior-period fact under P21 so the reference moved from the current period to the prior period and was still reported as GROUNDED, are stopped (VALUE_MISMATCH) under P22. Passed rows whose reference moved to the prior period: 0.
- Under P21 (2026-10-20, up to `cb4b497`) it was passed 17 / 241, stopped 224 / 241 (record `fixtures/xbrl/ritual_2026-10-20_p21.json`).
- Run time 23.2 seconds (the machine that took the record).
- The input `fixtures/xbrl/ai_prose_instance_2026-10-09.zip` (sha256 `03521437be23c8e2a02d85b4bc29a215646803582e9101fdf185521041174799`, 580,260 bytes) is a public EDINET disclosure document (document ID S100Z4Q1, filer code E36539, DN Holdings Co., Ltd., filed 2026-09-30). **Its management-discussion section was replaced with AI-written text in the 2026-10-09 experiment, so it is not the original text.**
- No key is used. It reads the bundled filing and the two label files under `~/.cache`, nothing else. To run it on your own filings you need an EDINET key and the filings downloaded.

## Check your own filing's text and get a Japanese report (0 USD, no network)

Give it your filing's ZIP (an EDINET securities report) and the text to check (it replaces the management-discussion section). The verdicts are the engine's, unchanged; the report reorders them and rewrites them in Japanese, nothing more (differs, needs a look, out of scope / not judged, matches; seal `docs/XBRL_CUSTOMER_REPORT_SEAL_2026-10-21.md`, result `docs/XBRL_CUSTOMER_REPORT_RESULT_2026-10-21.md`). Without the standard-taxonomy labels (step 0 above) the source column shows element names.

```
python3 -m adapters.xbrl.verify_document --zip <your filing.zip> --text <your text.txt> --out out.json
python3 -m adapters.xbrl.report_customer --in out.json --out report.md --labels ~/.cache/audit-core/edinet-taxonomy/2025-11-01 --zip <your filing.zip>
python3 -m adapters.xbrl.report_customer --in out.json --out report_full.md --labels ~/.cache/audit-core/edinet-taxonomy/2025-11-01 --zip <your filing.zip> --full   # also list the matches
```

With `--zip`, company-specific elements and segments are read in Japanese from the filing's own labels and the title carries the filer's name. Fingerprints are not printed in the report; they go to `report.provenance.json` next to it (machine-readable). The label files it reads are the ones listed in `fixtures/xbrl/taxonomy_labels_sha256.txt`, checked against their sha256.

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

215 test files (counted by the suite-coverage record; the collected-test count changes with every
added test and is kept in that record, not here), including 96
adversarial mutations exercised against the XBRL adapter. The core verification engine
itself is 429 lines (`core/py/audit_core/*.py`): existence and value checks, nothing
else.

## License

Proprietary. Copyright (c) 2026 Yushi Yamanaka. All rights reserved. See `LICENSE`.

## Scope of this file

This is a short excerpt for English-speaking reviewers. The source of truth is the
Japanese documentation and the JSON fixtures it cites; this file adds no capability and
no number that is not already recorded there.
