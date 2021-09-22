# -*- coding: utf-8 -*-
from base64 import b64encode
from bz2 import compress
from unittest import TestCase, mock
from datetime import datetime
from io import StringIO
import os
from pathlib import Path
import sys
from tempfile import mkstemp
from types import GeneratorType

from dateutil.parser import parse
from pytz import _UTC, timezone

from ..utils.changelog import ChangeLog, Entry
from ..utils.conf import get_config_path, get_credentials

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

            self.assertEqual(len(omock.mock_calls), 6)
            content = "".join(str(omock.mock_calls[x][1][0])
                              for x in range(2, 5))

            self.assertEqual(
                content,
                "-------------------------------------------------------------------\n"
                "Tue Jan 01 00:00:00 UTC 2019 - Andreas Hasenkopf <ahasenkopf@suse.com>\n\n"
                "Føø Bar\n\n"
                "-------------------------------------------------------------------\n"
                "Mon Jan 01 00:00:00 UTC 2018 - Andreas Pritschet <apritschet@suse.com>\n\n"
                "Hellø Wørld\n\n"
                "-------------------------------------------------------------------\n"
                "Sun Jan 01 00:00:00 UTC 2017 - Andreas Hasenkopf <ahasenkopf@suse.com>\n\n"
                "First enŧry\n\n"
            )

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


@mock.patch("osc.conf", side_effect=ImportError, create=True)
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

        expected_insecure_credentials = ("my-dummy-user", "my-insecure-dummy-password")
        expected_secure_credentials = ('my-dummy-user', 'my-secure-dummy-password')

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
