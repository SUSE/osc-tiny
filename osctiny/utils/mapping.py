"""
Mapping types
^^^^^^^^^^^^^

This module provides a collection of mapping types with special behavior.

.. versionadded:: 0.3.0
"""
# pylint: disable=too-many-ancestors
from collections.abc import MutableMapping


class Mappable(MutableMapping):
    """
    Basic implementation of a dictionary
    """
    def __init__(self, **kwargs):
        self._data = kwargs.copy()

    def __getitem__(self, item):
        if item not in self._data:
            self.__missing__(item)
        return self._data[item]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __iter__(self):
        return self._data.__iter__()

    def __len__(self):
        return len(self._data)

    def __delitem__(self, key):
        del self._data[key]

    def __contains__(self, item):
        return item in self._data

    def __missing__(self, key):
        raise KeyError(key)

    def __str__(self):
        return str(self._data)

    def __repr__(self):
        return repr(self._data)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()


class LazyOscMappable(Mappable):
    """
    Base class for lazy mappables

    To define custom subclasses override the ``__missing__`` method and set the missing key.

    :param osc_obj: An Osc instance to run queries
    :type osc_obj: :py:class:`osctiny.osc.Osc`
    """
    def __init__(self, osc_obj, **kwargs):
        super().__init__(**kwargs)
        self.osc = osc_obj
