# -*- coding: utf-8 -*-
# pylint: disable=protected-access
from base64 import b64encode
from bz2 import compress
from http.cookiejar import Cookie, LWPCookieJar
from unittest import TestCase, mock
from datetime import datetime
from io import StringIO
import os
from pathlib import Path
import re
from ssl import get_default_verify_paths
import sys
from tempfile import mkstemp
import time
from types import GeneratorType
import warnings

from dateutil.parser import parse
from pytz import _UTC, timezone
from requests import Response, HTTPError
from requests.auth import HTTPBasicAuth
import responses

from ..osc import Osc, THREAD_LOCAL
from ..utils.auth import HttpSignatureAuth
from ..utils.changelog import ChangeLog, Entry
from ..utils.conf import get_config_path, get_credentials
from ..utils.cookies import CookieManager
from ..utils.mapping import Mappable
from ..utils.errors import get_http_error_details
from ..utils.session import generate_session_id, init_session

sys.path.append(os.path.dirname(__file__))

SAMPLE_CHANGES = """
-------------------------------------------------------------------
Tue Dec  3 10:38:41 UTC 2019 - Andreas Hasenkopf <ahasenkopf@suse.com>

- Version 0.1.10

-------------------------------------------------------------------
Tue Dec  3 10:13:08 UTC 2019 - Andreas Hasenkopf <ahasenkopf@suse.com>

- New package osc-tiny (version 0.1.9)
"""

SAMPLE_CHANGES_2 = """
-------------------------------------------------------------------
Mon Aug  5 06:51:32 CST 2019 - Marco Strigl <marco.strigl@suse.com>

- 0.165.4 (boo#1144211)
   * allow optional fork when creating a maintenance request
   * fix RPMError fallback
   * fix local caching for all package formats
   * fix appname for trusted cert store
   * osc -h does not break anymore when using plugins 

-------------------------------------------------------------------
Wed Jul 24 13:18:01 UTC 2019 - Marco Strigl <marco.strigl@suse.com>

- 0.165.3 (boo#1142662)
    * switch to difflib.diff_bytes and sys.stdout.buffer.write for diffing.
      This will fix all decoding issues with osc diff, osc ci and osc rq -d
    * fix osc ls -lb handling empty size and mtime
    * removed decoding on osc api command.
    * fixed broken TLS certificate handling (boo#1142518, CVE-2019-3685) 

-------------------------------------------------------------------
Fri May 12 00:00:00 CEST 2006 - poeml@suse.de

- don't use --record-rpm option on setup.py, only SUSE has it
- define py_sitelib macro

-------------------------------------------------------------------
Wed May 10 00:00:00 CEST 2006 - poeml@suse.de

- created package (version 0.2)


"""

SAMPLE_CHANGES_3 = """
Tue Dec  3 10:38:41 UTC 2019 - Andreas Hasenkopf <ahasenkopf@suse.com>

- Version 0.1.10

-------------------------------------------------------------------
Tue Dec  3 10:13:08 UTC 2019 - Andreas Hasenkopf <ahasenkopf@suse.com>

- New package osc-tiny (version 0.1.9)
"""


class TestMappable(TestCase):
    def test(self):
        m = Mappable(a="a", b="b")
        m["c"] = "c"

        for key in ('a', 'b', 'c'):
            with self.subTest(f"get {key}"):
                self.assertEqual(key, m.get(key))

        with self.subTest("Default"):
            self.assertEqual("føø", m.get("d", "føø"))


class TestEntry(TestCase):
    def test_timestamp(self):
        cet = timezone("Europe/Berlin")

        with self.subTest("Initialization"):
            entry = Entry(timestamp=datetime(2019, 1, 1, tzinfo=cet))
            self.assertEqual(entry.timestamp.tzinfo, cet)
            self.assertIn("UTC", entry.formatted_timestamp)

        with self.subTest("Assignment"):
            entry = Entry()
            self.assertIsNotNone(entry.timestamp)
            entry.timestamp = datetime(2019, 1, 1, tzinfo=cet)
            self.assertIn("UTC", entry.formatted_timestamp)

        with self.subTest("Naive datetime"):
            self.assertRaises(ValueError, Entry, timestamp=datetime(2019, 1, 1))


class TestChangeLog(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestChangeLog, cls).setUpClass()
        cls.utc = _UTC()

    @staticmethod
    def prep_mock_open(omock):
        """
        Make a mocked file handle iterable

        See:

        * https://stackoverflow.com/a/24779923
        * https://docs.python.org/3.8/library/unittest.mock.html#mock-open
        """
        omock.return_value.__iter__ = lambda self: self
        omock.return_value.__next__ = lambda self: next(iter(self.readline, ''))

    def test_pattern(self):
        headers = [
            "Thu Dec  5 08:57:27 UTC 2019 - Adrian Schröter <adrian@suse.de>",
            "Wed Apr 24 09:37:32 CEST 2019 - schubi@suse.de",
            "Tue Dec  3 10:13:08 UTC 2019 - Andreas Hasenkopf "
            "<ahasenkopf@suse.com>"
        ]

        with self.subTest("Header pattern"):
            for line in headers:
                match = ChangeLog.patterns["header"].match(line)
                self.assertIsNotNone(match)

                timestamp = parse(match.group("timestamp"))
                self.assertIsInstance(timestamp, datetime)

    def test_parse_non_generative(self):
        with mock.patch("osctiny.utils.changelog.open",
                        mock.mock_open(read_data=SAMPLE_CHANGES),
                        create=True) as omock:
            self.prep_mock_open(omock)
            cl = ChangeLog.parse("/who/cares/test.changes", generative=False)

        self.assertIsInstance(cl.entries, list)
        self.assertEqual(len(cl.entries), 2)
        self.assertEqual(cl.entries[0].packager,
                         "Andreas Hasenkopf <ahasenkopf@suse.com>")
        self.assertEqual({x.content for x in cl.entries},
                         {
                             "- New package osc-tiny (version 0.1.9)",
                             "- Version 0.1.10"
                         })

    def test_parse_stringio(self):
        buffer = StringIO(SAMPLE_CHANGES)
        cl = ChangeLog.parse(buffer, generative=False)

        self.assertIsInstance(cl.entries, list)
        self.assertEqual(len(cl.entries), 2)

    def test_parse_path(self):
        _, path = mkstemp()
        with open(path, "w") as handle:
            handle.write(SAMPLE_CHANGES)

        try:
            with self.subTest("generative"):
                cl = ChangeLog.parse(path, generative=True)

                self.assertNotIsInstance(cl.entries, list)
                self.assertEqual(len(list(cl.entries)), 2)

            with self.subTest("non-generative"):
                cl = ChangeLog.parse(path, generative=False)

                self.assertIsInstance(cl.entries, list)
                self.assertEqual(len(cl.entries), 2)
        finally:
            os.remove(path)

    def test_parse_generative(self):
        with mock.patch("osctiny.utils.changelog.open",
                        mock.mock_open(read_data=SAMPLE_CHANGES),
                        create=True) as omock:
            self.prep_mock_open(omock)
            cl = ChangeLog.parse("/who/cares/test.changes", generative=True)

            self.assertIsInstance(cl.entries, GeneratorType)

            counter = 0
            # Notice: This loop must be within the mocked context!
            for _ in cl.entries:
                counter += 1

            self.assertEqual(counter, 2)

    def test_write(self):
        with mock.patch("osctiny.utils.changelog.open",
                        mock.mock_open(read_data=""),
                        create=True) as omock:
            self.prep_mock_open(omock)
            cl = ChangeLog()
            cl.entries = [
                Entry(
                    packager="Andreas Hasenkopf <ahasenkopf@suse.com>",
                    content="Føø Bar",
                    timestamp=datetime(2019, 1, 1, 0, 0, 0, tzinfo=self.utc)
                ),
                Entry(
                    packager="Andreas Pritschet <apritschet@suse.com>",
                    content="Hellø Wørld",
                    timestamp=datetime(2018, 1, 1, 0, 0, 0, tzinfo=self.utc)
                ),
                Entry(
                    packager="Andreas Hasenkopf <ahasenkopf@suse.com>",
                    content="First enŧry",
                    timestamp=datetime(2017, 1, 1, 0, 0, 0, tzinfo=self.utc)
                ),
            ]

            self.assertEqual(len(cl.entries), 3)
            cl.write(path="/who/cares/test.changes")
            calls = [
                mock.call().write(
                    '-------------------------------------------------------------------\n'
                    'Tue Jan 01 00:00:00 UTC 2019 - Andreas Hasenkopf <ahasenkopf@suse.com>'
                    '\n\nFøø Bar\n\n'),
                mock.call().write(
                    '-------------------------------------------------------------------\n'
                    'Mon Jan 01 00:00:00 UTC 2018 - Andreas Pritschet <apritschet@suse.com>'
                    '\n\nHellø Wørld\n\n'),
                mock.call().write(
                    '-------------------------------------------------------------------\n'
                    'Sun Jan 01 00:00:00 UTC 2017 - Andreas Hasenkopf <ahasenkopf@suse.com>'
                    '\n\nFirst enŧry\n\n')]
            omock.assert_has_calls(calls, any_order=True)

    def test_write_stringio(self):
        buffer = StringIO("")
        cl = ChangeLog()
        cl.entries = [Entry(
            packager="Andreas Hasenkopf <ahasenkopf@suse.com>",
            content="Føø Bar",
            timestamp=datetime(2019, 1, 1, 0, 0, 0, tzinfo=self.utc)
        )]

        self.assertEqual(len(cl.entries), 1)
        cl.write(path=buffer)
        buffer.seek(0)
        self.assertEqual(
                buffer.read(),
                "-------------------------------------------------------------------\n"
                "Tue Jan 01 00:00:00 UTC 2019 - Andreas Hasenkopf <ahasenkopf@suse.com>\n\n"
                "Føø Bar\n\n"
            )

    def test_write_append(self):
        with mock.patch("osctiny.utils.changelog.open",
                        mock.mock_open(read_data=SAMPLE_CHANGES_2),
                        create=True) as omock:
            self.prep_mock_open(omock)
            cl = ChangeLog.parse(path="/who/cares/test.changes",
                                 generative=False)

            cl.entries.append(Entry(
                packager="Andreas Hasenkopf <ahasenkopf@suse.com>",
                content="New entry at the top",
                timestamp=datetime(2020, 10, 31, 0, 0, 0, tzinfo=self.utc)
            ))
            cl.write(path="/who/cares/test.changes")

            write_calls = [x for x in omock.mock_calls if x[0] == "().write"]
            self.assertEqual(len(write_calls), 5)
            self.assertEqual(
                str(write_calls[0][1][0]),
                "-------------------------------------------------------------------\n"
                "Sat Oct 31 00:00:00 UTC 2020 - Andreas Hasenkopf <ahasenkopf@suse.com>\n\n"
                "New entry at the top\n\n"
            )

    def test_write_append_stringio(self):
        inbuff = StringIO(SAMPLE_CHANGES_2)
        outbuff = StringIO("")
        cl = ChangeLog.parse(path=inbuff, generative=False)

        cl.entries.append(Entry(
            packager="Andreas Hasenkopf <ahasenkopf@suse.com>",
            content="New entry at the top",
            timestamp=datetime(2020, 10, 31, 0, 0, 0, tzinfo=self.utc)
        ))
        cl.write(path=outbuff)

        outbuff.seek(0)
        self.assertEqual(
            len([x for x in outbuff.readlines() if x.startswith("-" * 67)]),
            5
        )

    def test_parse_missing_sep(self):
        buffer = StringIO(SAMPLE_CHANGES_3)
        cl = ChangeLog.parse(buffer, generative=False)

        self.assertIsInstance(cl.entries, list)
        self.assertEqual(len(cl.entries), 2)

    @mock.patch("warnings.warn")
    def test_parse_invalid_timestamp(self, wmock):
        buffer = StringIO(SAMPLE_CHANGES.replace("10:38:41", "10::41"))
        cl = ChangeLog.parse(buffer, generative=False)

        self.assertIsInstance(cl.entries, list)
        self.assertEqual(len(cl.entries), 2)
        self.assertIsInstance(cl.entries[0].timestamp, str)
        self.assertIsInstance(cl.entries[1].timestamp, datetime)

        self.assertEqual(wmock.call_count, 1)
        self.assertIn("Cannot parse changelog entry", wmock.call_args[0][0])


@mock.patch("osctiny.utils.conf._conf", new_callable=lambda: None, create=True)
@mock.patch("pathlib.Path.is_file", return_value=True)
class TestConfig(TestCase):
    def test_get_config_path(self, *_):
        with self.subTest("No env vars"):
            with mock.patch.dict(os.environ, values={}, clear=True):
                self.assertEqual(Path.home().joinpath(".oscrc"), get_config_path())

        with self.subTest("OSC_CONFIG"):
            osc_config = "/foo/bar/oscrc"
            with mock.patch.dict(os.environ, values={'OSC_CONFIG': osc_config}, clear=True):
                self.assertEqual(Path(osc_config), get_config_path())

    def test_get_credentials(self, *_):
        _, path1 = mkstemp()
        _, path2 = mkstemp()

        expected_insecure_credentials = ("my-dummy-user", "my-insecure-dummy-password", None)
        expected_secure_credentials = ('my-dummy-user', 'my-secure-dummy-password', None)

        with open(path1, "w") as handle:
            handle.write("[http://api.dummy-bs.org]\n")
            handle.write("user={}\npass={}\n".format(*expected_insecure_credentials))

        with open(path2, "w") as handle:
            handle.write("[general]\n")
            handle.write("apiurl=http://api.dummy-bs.org\n")
            handle.write("[http://api.dummy-bs.org]\n")
            handle.write("user={}\n".format(expected_secure_credentials[0]))
            handle.write("passx={}\n".format(b64encode(compress(
                expected_secure_credentials[1].encode("ascii")
            )).decode("ascii")))

        try:
            with self.subTest("No URL, no default"):
                with mock.patch.dict(os.environ, values={'OSC_CONFIG': path1}, clear=True):
                    self.assertRaises(ValueError, get_credentials)

            with self.subTest("Wrong URL"):
                with mock.patch.dict(os.environ, values={'OSC_CONFIG': path1}, clear=True):
                    self.assertRaises(ValueError, get_credentials, "http://google.de")

            with self.subTest("Wrong scheme"):
                with mock.patch.dict(os.environ, values={'OSC_CONFIG': path1}, clear=True):
                    self.assertRaises(ValueError, get_credentials, "https://api.dummy-bs.org")

            with self.subTest("Correct URL"):
                with mock.patch.dict(os.environ, values={'OSC_CONFIG': path1}, clear=True):
                    credentials = get_credentials("http://api.dummy-bs.org")
                self.assertEqual(expected_insecure_credentials, credentials)

            with self.subTest("No URL"):
                with mock.patch.dict(os.environ, values={'OSC_CONFIG': path2}, clear=True):
                    self.assertEqual(expected_secure_credentials, get_credentials())
        finally:
            os.remove(path1)
            os.remove(path2)


@mock.patch("osctiny.utils.auth.time", return_value=123456)
class TestAuth(TestCase):
    def _clear_thread_local(self):
        try:
            delattr(THREAD_LOCAL, generate_session_id(username=self.osc.username, url=self.osc.url))
        except AttributeError:
            pass

    @mock.patch("osctiny.utils.auth.is_ssh_key_readable", return_value=(True, None))
    def setUp(self, *_):
        super().setUp()
        mocked_path = mock.MagicMock(spec=Path)
        mocked_path.configure_mock(**{"is_file.return_value": True})

        self.osc = Osc(url="https://api.example.com",
                       username="nemo",
                       password="password",
                       ssh_key_file=mocked_path)

        self._clear_thread_local()
        self.osc.session.auth.ssh_sign = lambda *args, **kwargs: "Hello World"

    def tearDown(self):
        super().tearDown()
        self._clear_thread_local()

    def setup_response(self, headers: dict):
        responses.reset()
        responses.add(
                responses.GET,
                re.compile("https?://.*"),
                adding_headers=headers,
                body="Bla bla",
                status=401
            )

    def do_assertions(self, response: Response, expected_challenge: bool):
        self.assertEqual(401, response.status_code)
        if expected_challenge:
            self.assertEqual(
                {'realm': 'Use your developer account', 'headers': ['created'], 'created': 123456},
                self.osc.session.auth._thread_local.chal
            )
        else:
            self.assertEqual(0, len(self.osc.session.auth._thread_local.chal))

    @responses.activate
    def test_handle_401(self, *_):
        self.assertIsInstance(self.osc.session.auth, HttpSignatureAuth)

        with self.subTest("No WWW-Authenticate header"):
            self.setup_response({"Foo": "Bar"})
            response = self.osc.session.get("https://api.example.com/hello-world")
            self.do_assertions(response, False)

        with self.subTest("WWW-Authenticate: Only Basic"):
            self.setup_response({"www-authenticate": "Basic realm=\"Use your developer account\""})
            response = self.osc.session.get("https://api.example.com/hello-world")
            self.do_assertions(response, False)

        with self.subTest("WWW-Authenticate: Only Signature"):
            self.setup_response({"www-authenticate":
                                     "Signature realm=\"Use your developer account\","
                                     "headers=\"(created)\""})
            response = self.osc.session.get("https://api.example.com/hello-world")
            self.do_assertions(response, True)

        responses.reset()
        responses.add(
            responses.GET,
            re.compile("https?://.*"),
            adding_headers={"www-authenticate": "Basic realm=\"Use your developer account\", "
                                                "Signature realm=\"Use your developer account\","
                                                "headers=\"(created)\""},
            body="Bla bla",
            status=401
        )

        with self.subTest("WWW-Authenticate: Basic & Signature"):
            self.setup_response({"www-authenticate":
                                     "Basic realm=\"Use your developer account\", "
                                     "Signature realm=\"Use your developer account\","
                                     "headers=\"(created)\""})
            response = self.osc.session.get("https://api.example.com/hello-world")
            self.do_assertions(response, True)

        with self.subTest("WWW-Authenticate: Signature & Basic"):
            self.setup_response({"www-authenticate":
                                     "Signature realm=\"Use your developer account\","
                                     "headers=\"(created)\", "
                                     "Basic realm=\"Use your developer account\", "})
            response = self.osc.session.get("https://api.example.com/hello-world")
            self.do_assertions(response, True)


class TestError(TestCase):
    url = "http://example.com"

    @property
    def osc(self) -> Osc:
        return Osc(url=self.url, username="nemo", password="password")

    @responses.activate
    def test_get_http_error_details(self):
        status = 400
        summary = "Bla Bla Bla"
        rsp_mock = responses.add(
            responses.GET,
            self.url,
            body=f"""<status code="foo"><summary>{summary}</summary></status>""",
            status=status
        )

        response = self.osc.session.get(self.url)

        with self.subTest("Response"):
            self.assertEqual(response.status_code, status)
            self.assertEqual(get_http_error_details(response), summary)

        with self.subTest("Exception"):
            try:
                response.raise_for_status()
            except HTTPError as error:
                self.assertEqual(get_http_error_details(error), summary)
            else:
                self.fail("No exception was raised")

        with self.subTest("Request count"):
            if rsp_mock is not None:
                # In the last version of `responses` supporting Python 3.6, `rsp_mock` is None
                self.assertEqual(1, rsp_mock.call_count)

    @responses.activate
    def test_get_http_error_details__bad_response(self):
        status = 502
        rsp_mock = responses.add(
            responses.GET,
            self.url,
            body=f"""Bad Gateway HTML message""",
            status=status
        )

        response = self.osc.session.get(self.url)

        with self.subTest("Response"):
            self.assertEqual(response.status_code, status)
            with warnings.catch_warnings(record=True) as emitted_warnings:
                self.assertIn("Server replied with:", get_http_error_details(response))
                self.assertEqual(len(emitted_warnings), 1)
                self.assertIn("Start tag expected", str(emitted_warnings[-1].message))

        with self.subTest("Exception"):
            try:
                response.raise_for_status()
            except HTTPError as error:
                with warnings.catch_warnings(record=True) as emitted_warnings:
                    self.assertIn("Server replied with:", get_http_error_details(error))
                    self.assertEqual(len(emitted_warnings), 1)
                    self.assertIn("Start tag expected", str(emitted_warnings[-1].message))
            else:
                self.fail("No exception was raised")

        with self.subTest("Request count"):
            # In the last version of `responses` officially supporting Python 3.6, `rsp_mock` is
            # None.
            # Also, some distros (e.g. openSUSE Leap 15.6) have backported newer versions of
            # `responses` for Python 3.6.
            if rsp_mock is not None and sys.version_info >= (3, 7):
                self.assertEqual(self.osc.retry_policy.max_attempts + 1, rsp_mock.call_count)


@mock.patch("osctiny.utils.cookies._conf", new=None)
class TestCookies(TestCase):
    @property
    def mock_lwp_cookie_str(self) -> str:
        today = datetime.today()
        return '#LWP-Cookies-2.0\n'\
               'Set-Cookie3: openSUSE_session=3f0471fef300491289c3fcf845d445bd; '\
               'path="/"; domain=".suse.de"; path_spec; domain_dot; secure; '\
               f'expires="{today.year + 1}-07-18 14:35:02Z"; HttpOnly=None; version=0\n'

    def test_get_cookie_path(self, *_):
        with self.subTest("XDG_STATE_HOME set"), \
                mock.patch.dict(os.environ, {"XDG_STATE_HOME": "/foo/bar"}):
            self.assertEqual(Path("/foo/bar/osc/cookiejar"), CookieManager.get_cookie_path())

        with self.subTest("XDG_STATE_HOME not set"), mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(Path("~/.local/state/osc/cookiejar").expanduser(),
                             CookieManager.get_cookie_path())

    def test_get_jar(self, *_):
        cookie_path = Path(mkstemp()[1])

        with cookie_path.open("w", encoding="utf-8") as handle:
            handle.write(self.mock_lwp_cookie_str)

        with self.subTest("Existing jar"), mock.patch.object(CookieManager, "get_cookie_path",
                                                             return_value=cookie_path):
            jar = CookieManager.get_jar()
            self.assertEqual(jar.filename, cookie_path.as_posix())
            self.assertIn(".suse.de", jar._cookies)

        does_not_exist = Path("/no/such/path")
        with self.subTest("No jar"), mock.patch.object(CookieManager, "get_cookie_path",
                                                       return_value=does_not_exist):
            self.assertFalse(does_not_exist.is_file())

            jar = CookieManager.get_jar()
            self.assertEqual(jar.filename, does_not_exist.as_posix())
            self.assertEqual(0, len(jar._cookies))

    def test_save_jar(self, *_):
        cookie_path = Path(mkstemp()[1])
        jar = LWPCookieJar(filename=str(cookie_path))
        jar.set_cookie(cookie=Cookie(version=0, name='openSUSE_session',
                                     value='3f0471fef300491289c3fcf845d445bd', port=None,
                                     port_specified=False, domain='.suse.de', domain_specified=True,
                                     domain_initial_dot=True, path='/', path_specified=True,
                                     secure=True, expires=int(time.time()) + 3600, discard=False,
                                     comment=None, comment_url=None, rest={'HttpOnly': 'None'},
                                     rfc2109=False))
        CookieManager.save_jar(jar=jar)

        with cookie_path.open("r", encoding="utf-8") as handle:
            lines = handle.readlines()
            self.assertEqual(2, len(lines))
            self.assertIn("openSUSE_session", lines[1])

    def test_set_cookie(self, *_):
        jar = LWPCookieJar()
        CookieManager.set_cookie(jar=jar, cookie=self.mock_lwp_cookie_str)
        self.assertIn(".suse.de", jar._cookies)

    def test_get_cookie(self, *_):
        cookie_path = Path(mkstemp()[1])
        cookie_str = self.mock_lwp_cookie_str
        with cookie_path.open("w", encoding="utf-8") as handle:
            handle.write(cookie_str)

        jar = LWPCookieJar(filename=str(cookie_path))
        jar.load()
        result = CookieManager.get_cookie(jar=jar)

        # Use regex to handle both quoted and unquoted domain formats
        # Python 3.13.4+ changed how domains are serialized (no quotes)
        expected_pattern = re.escape(cookie_str).replace(
            r'domain="\.suse\.de"', r'domain="?\.suse\.de"?'
        )
        self.assertRegex(result, expected_pattern)


class TestSession(TestCase):
    true_capath = get_default_verify_paths().capath

    def test_verify(self):
        auth = HTTPBasicAuth(username="nemo", password="secret")

        with self.subTest("No verification"):
            session = init_session(auth=auth, verify=False)
            self.assertFalse(session.verify)

        with self.subTest("Specific CA path"):
            capath = "/tmp/no-such-ca.pem"
            session = init_session(auth=auth, verify=capath)
            self.assertEqual(session.verify, capath)

        with self.subTest("None"):
            session = init_session(auth=auth, verify=None)
            self.assertEqual(session.verify, self.true_capath)

        with self.subTest("No value provided"):
            session = init_session(auth=auth)
            self.assertEqual(session.verify, self.true_capath)
