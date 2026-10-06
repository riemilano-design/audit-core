"""Adapters package root. Holds subject-matter Adapters that connect to the Core.

This package itself knows nothing about any subject matter; it only
exists so that ``adapters.xbrl`` is importable.

Also adds ``<audit-core>/core/py`` to ``sys.path`` (mirroring
``tests/__init__.py``) so that ``recipes.py`` and ``run.py`` can
``import audit_core`` regardless of how this package was reached.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_CORE_PY = os.path.join(os.path.dirname(_HERE), "core", "py")
if _CORE_PY not in sys.path:
    sys.path.insert(0, _CORE_PY)
