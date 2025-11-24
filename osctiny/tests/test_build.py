import re
from urllib.parse import urlparse, parse_qs

from requests.exceptions import HTTPError
import responses

from .base import OscTest, CallbackFactory


class BuildTest(OscTest):

    @responses.activate
    def test_get(self):
        def callback(headers, params, request):
            status = 500
            body = ""
            parsed = urlparse(request.url)
            params.update(parse_qs(parsed.query, keep_blank_values=True))

            if not params:
                status = 200
                body = """
                <resultlist state="2c371787daedadb61dfd5fd8411ac6c2">
                  <result project="Some:Project" repository="SLE_15" 
                          arch="x86_64" code="published" state="published">
                    <status package="mypackage" code="disabled" />
                    <status package="anotherpackage" code="disabled" />
                  </result>
                  <result project="Some:Project" repository="SLE_12_SP3" 
                          arch="x86_64" code="published" state="published">
                    <status package="mypackage" code="succeeded" />
                    <status package="anotherpackage" code="disabled" />
                  </result>
                  <result project="Some:Project" repository="SLE_12_SP2" 
                          arch="x86_64" code="published" state="published">
                    <status package="mypackage" code="disabled" />
                    <status package="anotherpackage" code="disabled" />
                  </result>
                </resultlist>
                """
            elif params.get("package", []):
                if params["package"][0] in ["mypackage", "anotherpackage"]:
                    status = 200
                    body = """
                    <resultlist state="110f481609293ee149e28bbaced3b1b9">
                      <result project="Some:Project"  repository="SLE_15" 
                              arch="x86_64" code="published" state="published">
                        <status package="{pkg}" code="disabled" />
                      </result>
                      <result project="Some:Project" repository="SLE_12_SP3" 
                              arch="x86_64" code="published" state="published">
                        <status package="{pkg}" code="succeeded" />
                      </result>
                      <result project="Some:Project" repository="SLE_12_SP2" 
                              arch="x86_64" code="published" state="published">
                        <status package="{pkg}" code="disabled" />
                      </result>
                    </resultlist>
                    """.format(pkg=params["package"][0])
                else:
                    status = 404
                    body = """
                    <status code="404">
                      <summary>unknown package '{pkg}'</summary>
                      <details>404 unknown package '{pkg}'</details>
                    </status>
                    """.format(pkg=params["package"][0])

            return status, headers, body

        project = "Some:Project"
        package = "mypackage"
        self.mock_request(
            method=responses.GET,
            url=re.compile(
                self.osc.url + "/build/{}/_result".format(project)
            ),
            callback=CallbackFactory(callback)
        )

        with self.subTest("all"):
            response = self.osc.build.get(project=project)
            self.assertEqual(len(response.findall("result/status")), 6)

        with self.subTest("package: mypackage"):
            response = self.osc.build.get(project=project, package=package)
            self.assertEqual(len(response.findall("result/status")), 3)

        with self.subTest("package: anotherpackage"):
            response = self.osc.build.get(project=project,
                                          package="anotherpackage")
            self.assertEqual(len(response.findall("result/status")), 3)

        with self.subTest("package: unknown"):
            self.assertRaises(
                HTTPError,
                self.osc.build.get, project=project, package="xyz123"
            )

    @responses.activate
    def test_get_published_list(self):
        project = "openSUSE:Factory"
        repo = "standard"
        arch = "x86_64"

        response_body = """
        <directory>
          <entry name="acme-webserver-1.2.3-1.1.x86_64.rpm"/>
          <entry name="acme-webserver-debuginfo-1.2.3-1.1.x86_64.rpm"/>
          <entry name="acme-webserver-debugsource-1.2.3-1.1.x86_64.rpm"/>
          <entry name="python-foobar-2.0.1-4.2.x86_64.rpm"/>
          <entry name="python-foobar-doc-2.0.1-4.2.x86_64.rpm"/>
          <entry name="libcoolstuff3-0.5.7-2.1.x86_64.rpm"/>
          <entry name="libcoolstuff-devel-0.5.7-2.1.x86_64.rpm"/>
        </directory>
        """

        self.mock_request(
            method=responses.GET,
            url=re.compile(f"{self.osc.url}/published/{project}/{repo}/{arch}"),
            body=response_body,
        )

        response = self.osc.build.get_published_list(
            project=project,
            repo=repo,
            arch=arch
        )

        entries = response.findall("entry")
        self.assertEqual(len(entries), 7)
        self.assertEqual(entries[0].get("name"), "acme-webserver-1.2.3-1.1.x86_64.rpm")
        self.assertEqual(entries[3].get("name"), "python-foobar-2.0.1-4.2.x86_64.rpm")
        self.assertEqual(entries[5].get("name"), "libcoolstuff3-0.5.7-2.1.x86_64.rpm")
