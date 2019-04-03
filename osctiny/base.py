# pylint: disable=missing-docstring,too-few-public-methods

class ExtensionBase:
    """
    Base class for extensions of the :py:class:`Ocs` entry point.
    """
    def __init__(self, osc_obj):
        self.osc = osc_obj
