# -*- coding: utf-8 -*-
import re
from urllib.parse import unquote_plus, parse_qs

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
                b"view=xml&withissues=1"
            ),
            (
                {"view": "xml", "withissues": True},
                b"view=xml&withissues"
            ),
            (
                {"view": "xml", "withissues": 0},
                b"view=xml&withissues=0"
            ),
            (
                {"view": "xml", "withissues": False},
                b"view=xml"
            ),
            (
                {"view": "xml", "withissues": None},
                b"view=xml"
            ),
            (
                {"view": "xml", "withissues": None},
                b"view=xml"
            ),
            (
                {"view": "xml", "deleted": 1},
                b"view=xml&deleted"
            ),
            (
                {"view": "xml", "deleted": 0},
                b"view=xml"
            ),
            (
                {"view": "xml", "deleted": False},
                b"view=xml"
            ),
            (
                {"view": "xml", "deleted": True},
                b"view=xml&deleted"
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

    @responses.activate
    def test_request_boolean_params(self):
        pattern = re.compile(self.osc.url + r'/\?(?P<query>.*)')

        def callback(headers, params, request):
            match = pattern.match(request.url)

            parsed = parse_qs(match.group("query"), keep_blank_values=True)
            self.assertEqual(parsed, expected)
            return 200, headers, ""

        self.mock_request(
            method=responses.GET,
            url=pattern,
            callback=CallbackFactory(callback)
        )

        for path, expected in (
                (b"foo", {"foo": [""]}),
                (b"foo=bar", {"foo": ["bar"]}),
                (b"foo=foo&bar", {"foo": ["foo"], "bar": [""]}),
                (b"foo=foo?bar", {"foo": ["foo?bar"]}),
                (b"foo=foo=bar", {"foo": ["foo=bar"]})
        ):
            with self.subTest(path):
                self.osc.request(self.osc.url, params=path)
