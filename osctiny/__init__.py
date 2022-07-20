# pylint: disable=missing-docstring
from .osc import Osc
from .extensions import bs_requests, buildresults, comments, packages, \
    projects, search, users


__all__ = ['Osc', 'bs_requests', 'buildresults', 'comments', 'packages',
           'projects', 'search', 'users']
__version__ = "0.6.5"
