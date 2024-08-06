"""
Common base classes
^^^^^^^^^^^^^^^^^^^
"""
# pylint: disable=too-few-public-methods,


class ExtensionBase:
    """
    Base class for extensions of the :py:class:`Ocs` entry point.
    """
    def __init__(self, osc_obj: "Osc"):
        self.osc = osc_obj
