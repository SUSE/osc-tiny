from .. import projects
from .base import OscTest


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
        def _run(attr, expcted):
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
