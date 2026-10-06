"""Test package root.

Adds ``<audit-core>/core/py`` to ``sys.path`` so that ``audit_core`` can
be imported without installing it, when tests are discovered with
``python3 -m unittest discover -s audit-core/tests -t audit-core``.

Also adds ``<audit-core>`` itself to ``sys.path`` so that ``adapters``
(the C-1c XBRL Adapter) can be imported by
``tests/adapters/xbrl/test_*.py`` the same way.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUDIT_CORE = os.path.dirname(_HERE)
_CORE_PY = os.path.join(_AUDIT_CORE, "core", "py")
if _CORE_PY not in sys.path:
    sys.path.insert(0, _CORE_PY)
if _AUDIT_CORE not in sys.path:
    sys.path.insert(0, _AUDIT_CORE)
