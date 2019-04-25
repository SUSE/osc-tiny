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