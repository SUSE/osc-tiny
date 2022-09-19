"""
Backports of handy new features
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. versionadded:: 0.3.0
"""
try:
    # pylint: disable=unused-import
    from functools import lru_cache
except ImportError:
    # Whoever had the grandiose idea to backport this to Python2?
    # pylint: disable=unused-argument
    def lru_cache(*args, **kwargs):
        """Dummy wrapper"""
        def wrapper(fun):
            return fun

        return wrapper


try:
    # pylint: disable=unused-import
    from functools import cached_property
except ImportError:
    # Support for Python3 prior 3.8
    from cached_property import cached_property
