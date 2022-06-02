# -*- coding: utf-8 -*-
import re
from urllib.parse import unquote_plus

import responses

from ..extensions import projects
from .base import OscTest, CallbackFactory


class BasicTest(OscTest):
    def test_handle_params(self):
        def _run(data, expected):
            handled = self.osc.handle_params(data)
            self.assertEqual(handled, expected)

        data = (
            (None, {}),
            (1, {}),
            ("hello world", b"hello world"),
            ("føø bær", b"f\xc3\xb8\xc3\xb8 b\xc3\xa6r"),
            (
                {"view": "xml", "withissues": 1},
                {b"view": b"xml", b"withissues": b"1"}
            ),
            (
                {"view": "xml", "withissues": True},
                {b"view": b"xml", b"withissues": b"1"}
            ),
            (
                {"view": "xml", "withissues": 0},
                {b"view": b"xml", b"withissues": b"0"}
            ),
            (
                {"view": "xml", "withissues": False},
                {b"view": b"xml", b"withissues": b"0"}
            ),
            (
                {"view": "xml", "withissues": None},
                {b"view": b"xml"}
            ),
        )

        for params, expected in data:
            with self.subTest(params):
                _run(params, expected)

    def test_attrib_regexp(self):
        def _run(attr, expected):
            match = projects.Project.attribute_pattern.match(attr)
            self.assertIsNotNone(match)
            self.assertEqual(match.groupdict(), expected)

        data = (
            ('foo', {'name': 'foo', 'prefix': None}),
            ('foo:bar', {'name': 'bar', 'prefix': 'foo'}),
            ('foo:bar:wørld', {'name': 'bar:wørld', 'prefix': 'foo'}),
        )

        for attr, expected in data:
            with self.subTest(attr):
                _run(attr, expected)

    @responses.activate
    def test_request_url_encode(self):
        pattern = re.compile(self.osc.url + r'file/(?P<filename>.*)')
        special_chars = ('#', '?')
        data = [
            ["Clean URL", "hello_world.txt"],
            ["URL with hashtag", "hełłø#wørłd.txt"],
            ["URL with question mark", "hello?wørłð.txt"],
            ["URL with ampersand", "hełłö&world.txt"]
        ]

        def callback(headers, params, request):
            match = pattern.match(request.url)
            self.assertIsNotNone(match)
            self.assertEqual(unquote_plus(match.group("filename")), filename)
            for special_c in special_chars:
                self.assertNotIn(special_c, match.group("filename"))
            return 200, headers, ""

        self.mock_request(
            method=responses.GET,
            url=pattern,
            callback=CallbackFactory(callback)
        )

        for name, filename in data:
            with self.subTest(name):
                self.osc.request(f"{self.osc.url}file/{filename}")
