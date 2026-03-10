import re
import warnings

import responses

from .base import OscTest


class PublishedTest(OscTest):
    @responses.activate
    def test_get(self):
        project = "openSUSE:Factory"
        repo = "standard"

        response_body = """
        <directory>
          <entry name="x86_64"/>
          <entry name="i586"/>
        </directory>
        """

        self.mock_request(
            method=responses.GET,
            url=re.compile(f"{re.escape(self.osc.url)}/published/{project}/{repo}"),
            body=response_body,
        )

        response = self.osc.published.get(project=project, repo=repo)
        entries = response.findall("entry")
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].get("name"), "x86_64")

    @responses.activate
    def test_get_publishedpath(self):
        project = "SUSE:SLFO:1.1:Staging:I"
        repo = "standard"

        response_body = """<publishedpath project="SUSE:SLFO:1.1:Staging:I" repository="standard">
  <path>SUSE:/SLFO:/1.1:/Staging:/I/standard</path>
  <url>https://download.opensuse.org/obs/SUSE:/SLFO:/1.1:/Staging:/I/standard</url>
</publishedpath>
"""

        self.mock_request(
            method=responses.GET,
            url=re.compile(f"{re.escape(self.osc.url)}/published/{project}/{repo}"),
            body=response_body,
        )

        response = self.osc.published.get(
            project=project, repo=repo, view="publishedpath"
        )
        self.assertIsNotNone(response)
        self.assertEqual(
            response.url,
            "https://download.opensuse.org/obs/SUSE:/SLFO:/1.1:/Staging:/I/standard",
        )

    @responses.activate
    def test_get_binary_list(self):
        project = "openSUSE:Factory"
        repo = "standard"
        arch = "x86_64"

        response_body = """
        <directory>
          <entry name="acme-webserver-1.2.3-1.1.x86_64.rpm"/>
          <entry name="python-foobar-2.0.1-4.2.x86_64.rpm"/>
          <entry name="libcoolstuff3-0.5.7-2.1.x86_64.rpm"/>
        </directory>
        """

        self.mock_request(
            method=responses.GET,
            url=re.compile(
                f"{re.escape(self.osc.url)}/published/{project}/{repo}/{arch}"
            ),
            body=response_body,
        )

        response = self.osc.published.get_binary_list(
            project=project, repo=repo, arch=arch
        )
        entries = response.findall("entry")
        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0].get("name"), "acme-webserver-1.2.3-1.1.x86_64.rpm")
        self.assertEqual(entries[2].get("name"), "libcoolstuff3-0.5.7-2.1.x86_64.rpm")

    @responses.activate
    def test_build_get_published_list_deprecated(self):
        project = "openSUSE:Factory"
        repo = "standard"
        arch = "x86_64"

        response_body = """
        <directory>
          <entry name="acme-webserver-1.2.3-1.1.x86_64.rpm"/>
        </directory>
        """

        self.mock_request(
            method=responses.GET,
            url=re.compile(
                f"{re.escape(self.osc.url)}/published/{project}/{repo}/{arch}"
            ),
            body=response_body,
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            response = self.osc.build.get_published_list(
                project=project, repo=repo, arch=arch
            )
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[0].category, DeprecationWarning))
            self.assertIn("deprecated", str(w[0].message).lower())

        entries = response.findall("entry")
        self.assertEqual(len(entries), 1)
