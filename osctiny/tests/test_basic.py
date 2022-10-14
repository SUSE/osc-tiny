# -*- coding: utf-8 -*-
import pathlib
import re
import tempfile
from urllib.parse import unquote_plus, parse_qs

import responses

from ..extensions import projects
from .base import OscTest, CallbackFactory


class BasicTest(OscTest):
    @responses.activate
    def test_download(self):
        filename = 'test-file.bin'
        url = self.osc.url + '/' + filename
        content = "Lørem îþsum dołor siŧ aµet ..."
        self.mock_request(
            method=responses.GET,
            url=url,
            body=content.encode()
        )

        tmpfile1 = pathlib.Path(tempfile.mkstemp()[1])
        kwargs = {"url": url, "destdir": tmpfile1.parent, "destfile": tmpfile1.name}

        with self.subTest("overwrite=False"):
            self.assertRaises(OSError, self.osc.download, **kwargs)

        with self.subTest("overwrite=True"):
            kwargs2 = kwargs.copy()
            kwargs2["overwrite"] = True
            tmpfile2 = self.osc.download(**kwargs2)
            self.assertEqual(tmpfile1, tmpfile2)
            with tmpfile2.open("r") as handle:
                self.assertEqual(content, handle.read())

        with self.subTest("No destfile"):
            kwargs2 = kwargs.copy()
            del kwargs2["destfile"]
            tmpfile2 = self.osc.download(**kwargs2)
            try:
                self.assertEqual(tmpfile1.parent, tmpfile2.parent)
                self.assertEqual(tmpfile2.name, filename)
                with tmpfile2.open("r") as handle:
                    self.assertEqual(content, handle.read())
            finally:
                tmpfile2.unlink()

    def test_handle_params(self):
        def _run(data, expected, url="https://api.example.com/source/PROJECT/PACKAGE",
                 method="GET"):
            handled = self.osc.handle_params(url=url, method=method, params=data)
            self.assertEqual(handled, expected)

        data = (
            (None, {}),
            (1, {}),
            ("hello world", b"hello world"),
            ("føø bær", b"f\xc3\xb8\xc3\xb8 b\xc3\xa6r"),
            # 'withissues' is not a boolean param in the API
            (
                {"view": "xml", "withissues": 1},
                b"view=xml&withissues=1"
            ),
            (
                {"view": "xml", "withissues": True},
                b"view=xml&withissues=1"
            ),
            (
                {"view": "xml", "withissues": 0},
                b"view=xml&withissues=0"
            ),
            (
                {"view": "xml", "withissues": False},
                b"view=xml&withissues=0"
            ),
            (
                {"view": "xml", "withissues": None},
                b"view=xml"
            ),
            # 'deleted' is a boolean param in the project endpoint
            (
                {"view": "xml", "deleted": 1},
                b"view=xml&deleted"
            ),
            (
                {"view": "xml", "deleted": 0},
                b"view=xml"
            ),
            (
                {"view": "xml", "deleted": "1"},
                b"view=xml&deleted"
            ),
            (
                {"view": "xml", "deleted": "0"},
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
            # 'expand' is a boolean param in the project endpoint
            (
                {"expand": True},
                b"expand",
                "https://api.example.com/source/PROJECT",
            ),
            (
                {"expand": False},
                b"",
                "https://api.example.com/source/PROJECT",
            ),
            # 'deleted' is a boolean param in the project endpoint
            (
                {"deleted": True},
                b"deleted",
                "https://api.example.com/source/PROJECT",
            ),
            (
                {"deleted": False},
                b"",
                "https://api.example.com/source/PROJECT",
            ),

            # 'expand' is a boolean param in the package endpoint
            (
                {"expand": False},
                b"",
                "https://api.example.com/source/PROJECT/PACKAGE",
            ),
            (
                {"expand": True},
                b"expand",
                "https://api.example.com/source/PROJECT/PACKAGE",
            ),
        )

        for dataset in data:
            with self.subTest(dataset[0]):
                _run(*dataset)

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
