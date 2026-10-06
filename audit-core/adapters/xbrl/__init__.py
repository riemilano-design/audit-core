"""XBRL Adapter. Knows about EDINET documents, the XBRL instance format,
Japanese MD&A prose, and how to turn both into Core ``Recipe`` objects.

Nothing in ``audit_core`` (the Core) is imported here or by
``edinet``/``instance``/``extract``/``vocabulary``. Only ``recipes`` and
``run`` import the Core.
"""
