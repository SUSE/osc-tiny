from io import StringIO, BytesIO, IOBase
import re
from unittest import skip

import responses

from .base import OscTest, CallbackFactory
from osctiny.errors import OscError


class TestPackage(OscTest):
    @responses.activate
    def test_get_files(self):
        def callback(headers, params, request):
            status = 200
            body = """
                <directory name="python.8549" rev="1" vrev="28.17" 
                    srcmd5="9498d242f91b858372705d1bb4e26e1a">
                  <entry name="CVE-2017-18207.patch" 
                    md5="d1e5e39cfdf5087933cabf7d7b541158" size="900" 
                    mtime="1528391213" />
                  <entry name="Python-2.7.13.tar.xz" 
                    md5="53b43534153bb2a0363f08bae8b9d990" size="12495628"
                    mtime="1484132166" />
                  <entry name="Python-2.7.13.tar.xz.asc" 
                    md5="115f2de1793fa46a382f2a9f4e11b285" size="801" 
                    mtime="1484132166" />
                  <entry name="README.SUSE" 
                    md5="4a5a6c13a5b163d2e763b0d45f64c051" size="735" 
                    mtime="1216853740" />
                  <entry name="python-2.7.13-docs-pdf-a4.tar.bz2" 
                    md5="ccc87ad010f28d926ca09b1d5a55f4b0" size="10712181" 
                    mtime="1484132167" />
                  <entry name="python-base.spec" 
                    md5="af86457b494a667420e971e2e0febfcf" size="18454" 
                    mtime="1537948380" />
                  <entry name="python-doc.changes" 
                    md5="d5b75815a9455e231cc12d0aac045f9c" size="7290" 
                    mtime="1537948380" />
                  <entry name="python-doc.spec" 
                    md5="832b21401d9951d3b6e717e80944bd2b" size="6522" 
                    mtime="1537948381" />
                  <entry name="python.changes" 
                    md5="d479c6cd83559b1eed7d909087cf4785" size="54144" 
                    mtime="1537948381" />
                  <entry name="python.spec" 
                    md5="812c70b56ffd92d060bcf8b02ba479ff" size="20189" 
                    mtime="1537948382" />
                </directory>
            """
            headers['request-id'] = '728d329e-0e86-11e4-a748-0c84dc037c13'
            return status, headers, body

        self.mock_request(
            method=responses.GET,
            url=self.osc.url + '/source/SUSE:SLE-12-SP1:Update/python.8549',
            callback=CallbackFactory(callback)
        )

        response = self.osc.packages.get_files(
            "SUSE:SLE-12-SP1:Update", "python.8549"
        )
        self.assertEqual(response.tag, "directory")
        self.assertEqual(response.countchildren(), 10)

    @responses.activate
    def test_get_list(self):
        def callback(headers, params, request):
            status = 200
            body = """
                <directory count="14">
                  <entry name="SAPHanaSR"/>
                  <entry name="SAPHanaSR.4926"/>
                  <entry name="SAPHanaSR.7820"/>
                  <entry name="SUSEConnect"/>
                  <entry name="SUSEConnect.1732"/>
                  <entry name="SUSEConnect.1892"/>
                  <entry name="SUSEConnect.2196"/>
                  <entry name="SUSEConnect.2374"/>
                  <entry name="SUSEConnect.4293"/>
                  <entry name="SUSEConnect.4515"/>
                  <entry name="SUSEConnect.4773"/>
                  <entry name="SUSEConnect.7260"/>
                  <entry name="SUSEConnect.8868"/>
                  <entry name="SUSEConnect.9195"/>
                </directory>
            """
            headers['request-id'] = '728d329e-0e86-11e4-a748-0c84dc037c13'
            return status, headers, body

        self.mock_request(
            method=responses.GET,
            url=self.osc.url + '/source/SUSE:SLE-12-SP1:Update/python.8549',
            callback=CallbackFactory(callback)
        )

        response = self.osc.packages.get_files(
            "SUSE:SLE-12-SP1:Update", "python.8549"
        )
        self.assertEqual(response.tag, "directory")
        self.assertEqual(response.countchildren(), 14)

    @responses.activate
    def test_get_meta(self):
        def callback(headers, params, request):
            status = 200
            body = """
            <package name="python.8549" project="SUSE:SLE-12-SP1:Update">
              <title>Python Interpreter</title>
              <description>Python is an interpreted, object-oriented programming
              language, and is often compared to Tcl, Perl, Scheme, or Java. You
              can find an overview of Python in the documentation and tutorials
              included in the python-doc (HTML) or python-doc-pdf (PDF) 
              packages.
            
              If you want to install third party modules using distutils, you 
              need to install python-devel package.</description>
              <releasename>python</releasename>
            </package>
            """
            if params.get("view", None) == "blame":
                body = """
   1 (foo__bar     2018-10-29 16:28:55     1) <package name="python.8549" project="SUSE:SLE-12-SP1:Update">
   1 (foo__bar     2018-10-29 16:28:55     2)   <title>Python Interpreter</title>
   1 (foo__bar     2018-10-29 16:28:55     3)   <description>Python is an interpreted, object-oriented programming language, and is
   1 (foo__bar     2018-10-29 16:28:55     4) often compared to Tcl, Perl, Scheme, or Java.  You can find an overview
   1 (foo__bar     2018-10-29 16:28:55     5) of Python in the documentation and tutorials included in the python-doc
   1 (foo__bar     2018-10-29 16:28:55     6) (HTML) or python-doc-pdf (PDF) packages.
   1 (foo__bar     2018-10-29 16:28:55     7) 
   1 (foo__bar     2018-10-29 16:28:55     8) If you want to install third party modules using distutils, you need to
   1 (foo__bar     2018-10-29 16:28:55     9) install python-devel package.</description>
   1 (foo__bar     2018-10-29 16:28:55    10)   <releasename>python</releasename>
   1 (foo__bar     2018-10-29 16:28:55    11) </package>
                """

            return status, headers, body

        self.mock_request(
            method=responses.GET,
            url=self.osc.url + '/source/SUSE:SLE-12-SP1:Update/python.8549/'
                               '_meta',
            callback=CallbackFactory(callback)
        )

        with self.subTest("without blame"):
            response = self.osc.packages.get_meta(
                "SUSE:SLE-12-SP1:Update", "python.8549"
            )
            self.assertEqual(response.tag, "package")
            self.assertEqual(
                response.xpath("./title")[0].text,
                "Python Interpreter"
            )

        with self.subTest("with blame"):
            response = self.osc.packages.get_meta(
                "SUSE:SLE-12-SP1:Update", "python.8549", blame=True
            )
            self.assertTrue(isinstance(response, str))

    @skip("No test data available")
    @responses.activate
    def test_get_attribute(self):
        def callback(headers, params, request):
            status = 200
            body = """</attributes>"""
            headers['request-id'] = '728d329e-0e86-11e4-a748-0c84dc037c13'
            return status, headers, body

        self.mock_request(
            method=responses.GET,
            url=self.osc.url + '/source/SUSE:SLE-12-SP1:Update/python.8549/'
                               '_attribute',
            callback=CallbackFactory(callback)
        )

    @responses.activate
    def test_get_history(self):
        self.mock_request(
            method=responses.GET,
            url=self.osc.url + '/source/SUSE:SLE-12-SP1:Update/python.8549/'
                               '_history',
            body="""
                <revisionlist>
                  <revision rev="1" vrev="1">
                    <srcmd5>b9b258599bb67a2a3d396b1515cabeab</srcmd5>
                    <version>unknown</version>
                    <time>1514367595</time>
                    <user>Fȱȱ Bar</user>
                    <comment>
                      Set link tȱ grub2.5745 via maintenance_release request
                    </comment>
                    <requestid>148865</requestid>
                  </revision>
                  <revision rev="2" vrev="2">
                    <srcmd5>9f5e43584f67e2a301b71b63bdf8e2e1</srcmd5>
                    <version>unknown</version>
                    <time>1520336862</time>
                    <user>HȨllȱ Wȱrld</user>
                    <comment>
                      Set link tȱ grub2.6584 via maintenance_release request
                    </comment>
                    <requestid>154349</requestid>
                  </revision>
                </revisionlist>
            """
        )

        response = self.osc.packages.get_history(
            "SUSE:SLE-12-SP1:Update", "python.8549"
        )
        self.assertEqual(response.tag, "revisionlist")
        self.assertEqual(
            len(response.xpath("./revision")), 2
        )

    @responses.activate
    def test_cmd(self):
        self.mock_request(
            method=responses.POST,
            url=self.osc.url + '/source/SUSE:SLE-12-SP1:Update/python.8549',
            body="""
                +==== //tools/python/2.6.2/src/base/Modules/_ctypes/libffi/src/sparc/ffi.c#1 - /home/build/clifford/gpdb/tools/python/2.6.2/src/base/Modules/_ctypes/libffi/src/sparc/ffi.c ====
                +---
                + Modules/_ctypes/libffi/src/sparc/ffi.c |    5 +++++
                + 1 file changed, 5 insertions(+)
                +
                +--- a/Modules/_ctypes/libffi/src/sparc/ffi.c
                ++++ b/Modules/_ctypes/libffi/src/sparc/ffi.c
                +@@ -652,6 +652,11 @@
                + 	}
                +       else
                + 	{
                ++#if FFI_TYPE_LONGDOUBLE != FFI_TYPE_DOUBLE
                ++         /* SparcV9 long double is 16-byte aligned; skip arg if necessary */
                ++         if (arg_types[i]->type == FFI_TYPE_LONGDOUBLE && (argn & 1))
                ++           argn++;
                ++#endif
                + 	  /* Right-justify.  */
                + 	  argn += ALIGN(arg_types[i]->size, FFI_SIZEOF_ARG) / FFI_SIZEOF_ARG;
                + 
            """
        )

        response = self.osc.packages.cmd(
            "SUSE:SLE-12-SP1:Update", "python.8549", "diff"
        )
        self.assertTrue(isinstance(response, str))
        self.assertIn(
            "++#if FFI_TYPE_LONGDOUBLE != FFI_TYPE_DOUBLE", response
        )

    @responses.activate
    def test_set_meta(self):
        bodies = []

        def callback(headers, params, request):
            bodies.append(request.body)
            status, body = 200, ""

            return status, headers, body

        self.mock_request(
            method=responses.PUT,
            url=re.compile(self.osc.url + '/source/(?P<project>[^/]+)/'
                                          '(?P<package>[^/]+)/_meta'),
            callback=CallbackFactory(callback)
        )

        data = (
            (
                {
                    'project': "test:project",
                    'package': "test.package",
                    'title': "test",
                    'description': "foo"
                },
                b'<package><title>test</title><description>foo</description>'
                b'</package>'
            ),
            (
                {
                    'project': "test:project",
                    'package': "test.package",
                },
                b'<package><title/><description/></package>'
            ),
            (
                {
                    'project': "test:project",
                    'package': "test.package",
                    'meta': """
                    <package name="test.package" project="test:project">
                      <title/>
                      <description/>
                      <build>
                        <enable repository="openSUSE_Leap_15.0"/>
                        <disable arch="i586"/>
                      </build>
                    </package>
                    """
                },
                b'<package name="test.package" project="test:project"><title/>'
                b'<description/><build>'
                b'<enable repository="openSUSE_Leap_15.0"/>'
                b'<disable arch="i586"/></build></package>'
            ),
            (
                {
                    'project': "test:project",
                    'package': "test.package",
                    'title': 'foo',
                    'description': 'bar',
                    'meta': """
                    <package name="test.package" project="test:project">
                      <title/>
                      <description/>
                      <build>
                        <enable repository="openSUSE_Leap_15.0"/>
                        <disable arch="i586"/>
                      </build>
                    </package>
                    """
                },
                b'<package name="test.package" project="test:project">'
                b'<title>foo</title><description>bar</description><build>'
                b'<enable repository="openSUSE_Leap_15.0"/>'
                b'<disable arch="i586"/></build></package>'
            ),
        )

        for params, expected in data:
            with self.subTest():
                self.osc.packages.set_meta(**params)
                self.assertEqual(bodies[-1], expected)

    @responses.activate
    def test_push_file(self):
        content = """
        ლ(ಠ益ಠ)ლ            ლ(ಠ益ಠ)ლ
        Lorem ipsum dolor sit amet,
        consectetur adipiscing elit.
        Vestibulum id enim 
        fermentum, lobortis urna
        quis, convallis justo. 
        ლ(ಠ益ಠ)ლ            ლ(ಠ益ಠ)ლ 
        """
        bodies = []

        def callback(headers, params, request):
            if isinstance(request.body, IOBase):
                request.body.seek(0)
                bodies.append(request.body.read())
            else:
                bodies.append(request.body)
            status, body = 200, ""

            return status, headers, body

        self.mock_request(
            method=responses.PUT,
            url=re.compile(
                self.osc.url + '/source/(?P<project>[^/]+)/'
                               '(?P<package>[^/]+)/(?P<filename>.+)'
            ),
            callback=CallbackFactory(callback)
        )

        with self.subTest("as unicode"):
            self.osc.packages.push_file("prj", "pkg", "readme.txt", content)
            self.assertEqual(bodies[-1], content.encode())

        with self.subTest("as bytes"):
            self.osc.packages.push_file("prj", "pkg", "readme.txt",
                                        content.encode())
            self.assertEqual(bodies[-1], content.encode())

        with self.subTest("as StringIO"):
            self.osc.packages.push_file("prj", "pkg", "readme.txt",
                                        StringIO(content))
            self.assertEqual(bodies[-1], content.encode())

        with self.subTest("as BytesIO"):
            self.osc.packages.push_file("prj", "pkg", "readme.txt",
                                        BytesIO(content.encode()))
            self.assertEqual(bodies[-1], content.encode())

    @responses.activate
    def test_aggregate(self):
        put_called = []

        def exists_callback(headers, params, request):
            status, body = 404, ""
            if "exists" in request.url:
                if "_aggregate" in request.url and "already.agged" not in request.url:
                    status = 404
                else:
                    status = 200
            return status, headers, body

        def put_callback(headers, params, request):
            put_called.append({'request': request, 'params': params})
            status, body = 200, ""
            return status, headers, body

        def meta_callback(headers, params, request):
            status = 200
            body = """<package><title/><description/></package>"""
            return status, headers, body

        self.mock_request(
            method=responses.HEAD,
            url=re.compile(
                self.osc.url + '/source/.*'
            ),
            callback=CallbackFactory(exists_callback)
        )
        self.mock_request(
            method=responses.PUT,
            url=re.compile(
                self.osc.url + '/source/.*'
            ),
            callback=CallbackFactory(put_callback)
        )
        self.mock_request(
            method=responses.GET,
            url=re.compile(
                self.osc.url + '/source/.+/_meta'
            ),
            callback=CallbackFactory(meta_callback)
        )

        with self.subTest("identical package"):
            self.assertRaises(
                OscError,
                self.osc.packages.aggregate,
                "test:project", "test.package",
                "test:project", "test.package",
            )

        with self.subTest("non-existing package"):
            self.assertRaises(
                OscError,
                self.osc.packages.aggregate,
                "test:project", "test.package",
                "test:project:2", "test.package",
            )

        with self.subTest("already existing aggregate"):
            self.assertRaises(
                OscError,
                self.osc.packages.aggregate,
                "test:project:exists", "test.package",
                "test:project2:exists", "already.agged",
            )

        with self.subTest("non-existing target package"):
            old_len = len(put_called)
            self.osc.packages.aggregate(
                "test:project:exists", "test.package",
                "test:project2:foo", "test.pkg",
            )
            self.assertEqual(len(put_called), old_len + 2)

        with self.subTest("existing target package"):
            old_len = len(put_called)
            self.osc.packages.aggregate(
                "test:project:exists", "test.package",
                "test:project2:exists", "test.pkg",
            )
            self.assertEqual(len(put_called), old_len + 1)
