import re
from urllib.parse import urlparse, parse_qs

from requests.exceptions import HTTPError
import responses

from .base import OscTest, CallbackFactory


class TestProject(OscTest):
    @responses.activate
    def test_get_list(self):
        def callback(headers, params, request):
            status = 200
            body = """<directory>
                <entry name="Devel:AAC"/>
                <entry name="Devel:ARM"/>
                <entry name="Devel:ARM:Factory"/>
                <entry name="Devel:ARM:Factory:Contrib:ThunderX"/>
                <entry name="Devel:ARM:Factory:Contrib:ThunderX:qemu"/>
                <entry name="Devel:ARM:Factory:ILP32"/>
            </directory>
            """
            parsed = urlparse(request.url)
            params.update(parse_qs(parsed.query))
            if params.get("deleted", ["0"]) == ["1"]:
                status = 403
                body = """<status code="no_permission_for_deleted">
                  <summary>only admins can see deleted projects</summary>
                </status>
                """
            headers['request-id'] = '728d329e-0e86-11e4-a748-0c84dc037c13'
            return status, headers, body

        self.mock_request(
            method=responses.GET,
            url=self.osc.url + '/source',
            callback=CallbackFactory(callback)
        )

        with self.subTest("existing files"):
            response = self.osc.projects.get_list(deleted=False)
            self.assertEqual(response.tag, "directory")
            self.assertEqual(response.countchildren(), 6)

        with self.subTest("deleted files"):
            self.assertRaises(
                HTTPError, self.osc.projects.get_list, deleted=True
            )

    @responses.activate
    def test_get_meta(self):
        def callback(headers, params, request):
            status = 200
            body = """
                <project name="Devel:ARM:Factory">
                  <title>openSUSE Factory built on native ARM Hardware</title>
                  <description>openSUSE Factory built on native ARM Hardware. 
                  It usually builds faster than the external version 
                  openSUSE:Factory:ARM, which builds on qemu in x86_64.
                </description>
                  <link project="openSUSE.org:openSUSE:Factory:ARM"/>
                  <person userid="Foo Bar" role="maintainer"/>
                  <person userid="Hello World" role="maintainer"/>
                  <build>
                    <disable/>
                    <enable arch="aarch64" repository="standard"/>
                  </build>
                  <debuginfo>
                    <enable/>
                  </debuginfo>
                  <repository name="standard" rebuild="local" block="never" 
                      linkedbuild="all">
                    <path project="openSUSE.org:openSUSE:Factory:ARM" 
                      repository="standard"/>
                    <arch>armv7l</arch>
                    <arch>aarch64</arch>
                  </repository>
                  <repository name="images" block="local">
                    <path project="Devel:ARM:Factory" repository="standard"/>
                    <arch>local</arch>
                    <arch>armv7l</arch>
                  </repository>
                </project>
            """
            if not "Devel:ARM:Factory" in request.url:
                status = 404
                body = """
                    <status code="unknown_project">
                      <summary>Devel:ARM:Fbctory</summary>
                    </status>
                """
            headers['request-id'] = '728d329e-0e86-11e4-a748-0c84dc037c13'
            return status, headers, body

        self.mock_request(
            method=responses.GET,
            url=re.compile(self.osc.url + '/source/.*'),
            callback=CallbackFactory(callback)
        )

        with self.subTest("existing project"):
            response = self.osc.projects.get_meta("Devel:ARM:Factory")
            self.assertEqual(response.tag, "project")
            self.assertEqual(response.get("name"), "Devel:ARM:Factory")
            self.assertEqual(len(response.xpath("./person")), 2)

        with self.subTest("non-existing project"):
            self.assertRaises(
                HTTPError, self.osc.projects.get_meta, "Devel:ARM:Fbctory"
            )

    @responses.activate
    def test_get_files(self):
        def callback(headers, params, request):
            status = 200
            body = """
                <directory name="_project" rev="10" vrev="" 
                  srcmd5="4adff519b4e14cf206bcc7bdce40a73c">
                  <entry name="_config" md5="11cfe7fdb2591b55435b312c156e17fe" 
                    size="1818" mtime="1542617696" />
                </directory>
            """
            parsed = urlparse(request.url)
            params.update(parse_qs(parsed.query))

            if params.get("meta", ['0']) == ['1']:
                status = 200
                body = """
                    <directory name="_project" rev="41" vrev="" 
                      srcmd5="f8bf4cb0e1edea467e34462742ca82ae">
                      <entry name="_attribute" 
                        md5="18fbe34f9ab146c9d73f7e5756f74d48" size="4172" 
                        mtime="1543406498" />
                      <entry name="_meta" md5="9392aa5e748eb15087c4db55ac1cb7f3"
                        size="1875" mtime="1542635759" />
                    </directory>
                """
            headers['request-id'] = '728d329e-0e86-11e4-a748-0c84dc037c13'
            return status, headers, body

        self.mock_request(
            method=responses.GET,
            url=re.compile(
                self.osc.url + '/source/SUSE:SLE-15-SP1:GA/_project.*'
            ),
            callback=CallbackFactory(callback)
        )

        with self.subTest("Non-meta files"):
            response = self.osc.projects.get_files("SUSE:SLE-15-SP1:GA",
                                                   "_project")
            self.assertEqual(response.tag, "directory")
            self.assertEqual(len(response.xpath("./entry")), 1)

        with self.subTest("Meta files"):
            response = self.osc.projects.get_files(
                "SUSE:SLE-15-SP1:GA", "_project", meta=True
            )
            self.assertEqual(response.tag, "directory")
            self.assertEqual(len(response.xpath("./entry")), 2)

    @responses.activate
    def test_get_attribute(self):
        def callback(headers, params, request):
            status = 404
            body = """
            <status code="unknown_attribute_type">
              <summary>
                Attribute Type OBS:ApprovedRequestSour does not exist
              </summary>
            </status>
            """
            if request.url.endswith("_attribute"):
                status = 200
                body = """
                <attributes>
                  <attribute name="IgnoredIssues" namespace="OSRT">
                    <value>last_seen: {}</value>
                  </attribute>
                  <attribute name="OpenQAMapping" namespace="OSRT">
                    <value>s/^(SLE-.*)-Installer-(.*)Build/\g&lt;1&gt;
                    -Staging:$LETTER-Installer-\g&lt;2&gt;Build$LETTER./</value>
                  </attribute>
                  <attribute name="ApprovedRequestSource" namespace="OBS"/>
                </attributes>
                """
            if request.url.endswith("OBS:ApprovedRequestSource"):
                status = 200
                body = """
                    <attributes>
                      <attribute name="ApprovedRequestSource" namespace="OBS"/>
                    </attributes>
                """
            headers['request-id'] = '728d329e-0e86-11e4-a748-0c84dc037c13'
            return status, headers, body

        self.mock_request(
            method=responses.GET,
            url=re.compile(
                self.osc.url + '/source/SUSE:SLE-15-SP1:GA/_attribute.*'
            ),
            callback=CallbackFactory(callback)
        )

        with self.subTest("all attributes"):
            response = self.osc.projects.get_attribute("SUSE:SLE-15-SP1:GA")
            self.assertEqual(response.tag, "attributes")
            self.assertEqual(len(response.xpath("./attribute")), 3)

        with self.subTest("one attribute"):
            response = self.osc.projects.get_attribute(
                "SUSE:SLE-15-SP1:GA", "OBS:ApprovedRequestSource"
            )
            self.assertEqual(response.tag, "attributes")
            self.assertEqual(len(response.xpath("./attribute")), 1)

        with self.subTest("wrong attribute"):
            self.assertRaises(
                HTTPError, self.osc.projects.get_attribute,
                "SUSE:SLE-15-SP1:GA", "FOO:Bar"
            )

    @responses.activate
    def test_set_attribute(self):
        def callback(headers, params, request):
            status, body = 200, "<status code='ok'></status>"
            return status, headers, body

        self.mock_request(
            method="POST",
            url=re.compile(
                self.osc.url + '/source/(?P<project>)[^/]+/_attribute/?'
            ),
            callback=CallbackFactory(callback)
        )

        self.assertTrue(
            self.osc.projects.set_attribute(
                project="test:project",
                attribute="namespace:attr",
                value="value"
            )
        )

    @responses.activate
    def test_delete_attribute(self):
        error = False

        def callback(headers, params, request):
            if error:
                status, body = 404, ""
            else:
                status, body = 200, "<status code='ok'></status>"
            return status, headers, body

        self.mock_request(
            method="DELETE",
            url=re.compile(
                self.osc.url + '/source/(?P<project>)[^/]+/_attribute/?'
            ),
            callback=CallbackFactory(callback)
        )

        with self.subTest("existing attr"):
            self.assertTrue(
                self.osc.projects.delete_attribute(
                    project="test:project",
                    attribute="namespace:attr"
                )
            )

        with self.subTest("non-existent attr"):
            error = True
            self.assertRaises(
                HTTPError,
                self.osc.projects.delete_attribute,
                project="test:project",
                attribute="namespace:attr"
            )

    @responses.activate
    def test_delete(self):
        def callback(headers, params, request):
            if "existing" in request.url:
                status, body = 200, """
                <status code="ok">
                  <summary>Ok</summary>
                </status>
                """
            else:
                status, body = 400, """
                    <status code="invalid_project_name">
                      <summary>
                        invalid project name 'home:apritschet:__'
                      </summary>
                    </status>"""
            return status, headers, body

        self.mock_request(
            method="DELETE",
            url=re.compile(
                self.osc.url + '/source/(?P<project>)[^/]+'
            ),
            callback=CallbackFactory(callback)
        )

        with self.subTest("existing"):
            self.assertTrue(self.osc.projects.delete("test_project:existing"))

        with self.subTest("non-existent"):
            self.assertRaises(
                HTTPError,
                self.osc.projects.delete,
                "test:project:non-found"
            )

    @responses.activate
    def test_exists(self):
        def callback(headers, params, request):
            if "existing" in request.url:
                status, body = 200, ""
            else:
                status, body = 404, ""
            return status, headers, body

        self.mock_request(
            method="HEAD",
            url=re.compile(
                self.osc.url + '/source/(?P<project>)[^/]+'
            ),
            callback=CallbackFactory(callback)
        )

        with self.subTest("existing"):
            self.assertTrue(self.osc.projects.exists("home:user:existing"))

        with self.subTest("non-existent"):
            self.assertFalse(self.osc.projects.exists("no:such:project"))
