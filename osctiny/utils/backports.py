"""
Backports of handy new features
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. versionadded:: 0.3.0

.. versionchanged:: 0.8.0

    Removed function ``lru_cache``
"""
try:
    # pylint: disable=unused-import
    from functools import cached_property
except ImportError:
    # Support for Python3 prior 3.8
    from cached_property import cached_property
