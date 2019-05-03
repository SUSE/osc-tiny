from io import IOBase
from unittest import TestCase
from urllib.parse import parse_qs

import responses

from osctiny import Osc


class CallbackFactory:
    """
    Wrapper for callback functions

    Callback functions are expected to accept three parameters and return
    three values:

    :param headers: Predefined headers
    :type headers: dict
    :param params: Parsed querystring
    :param request: Actual request object
    :type: requests.Request
    :type params: dict
    :return: (HTTP status, headers, JSON body)
    :rtype: (int, dict, str)
    """
    def __init__(self, callback):
        if not callable(callback):
            raise TypeError("Callback needs to be callable")
        self.callback = callback

    def __call__(self, request):
        body = request.body
        if isinstance(body, IOBase):
            body.seek(0)
            body = body.read()
        if hasattr(body, "decode"):
            body = body.decode()
        params = parse_qs(body)
        headers = {
            "Cache-Control": "max-age=0, private, must-revalidate",
            "Connection": "Keep-Alive",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Server": "Apache/2.4.33 (Linux/SUSE)",
            "X-Content-Type-Options": "nosniff",
            "X-Download-Options": "noopen",
            "X-Frame-Options": "SAMEORIGIN",
            "X-Request-Id": "6ac6301b-0460-486f-b273-7308ddf673b1",
            "X-XSS-Protection": "1; mode=block"
        }
        return self.callback(headers, params, request)


class OscTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.osc = Osc(
            url="http://api.example.com",
            username="foobar",
            password="helloworld",
        )

    @staticmethod
    def mock_request(**kwargs):
        kwargs.setdefault("content_type", "application/xml")

        if "callback" in kwargs:
            responses.add_callback(**kwargs)
        else:
            responses.add(**kwargs)
