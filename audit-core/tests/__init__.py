"""Test package root.

Adds ``<audit-core>/core/py`` to ``sys.path`` so that ``audit_core`` can
be imported without installing it, when tests are discovered with
``python3 -m unittest discover -s audit-core/tests -t audit-core``.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_CORE_PY = os.path.join(os.path.dirname(_HERE), "core", "py")
if _CORE_PY not in sys.path:
    sys.path.insert(0, _CORE_PY)
