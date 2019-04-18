from unittest import skipUnless

from .test_search import TestSearch
from osctiny import Osc

try:
    import cachecontrol
except ImportError:
    with_cache = False
else:
    with_cache = True


@skipUnless(with_cache, "No cache module present, therefore not testing")
class TestSearch(TestSearch):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.osc = Osc(
            url="http://api.example.com",
            username="foobar",
            password="helloworld",
            cache=True
        )
