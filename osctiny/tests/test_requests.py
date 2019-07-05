import re
from urllib.parse import urlparse, parse_qs

from lxml.objectify import ObjectifiedElement
from requests.exceptions import HTTPError
import responses

from .base import OscTest, CallbackFactory


def callback(headers, params, request):
    status = 500
    body = ""
    parsed = urlparse(request.url)
    params.update(parse_qs(parsed.query))

    if re.search("comments/request/30902", request.url):
        status = 200
        if request.method == "GET":
            body = """
            <comments request="30902">
              <comment who="apritschet" when="2019-04-18 15:31:19 UTC" 
                       id="1571414">test hello world 2</comment>
              <comment who="apritschet" when="2019-04-18 15:32:42 UTC" 
                       id="1571422">foo bar</comment>
            </comments>"""
        elif request.method == "POST":
            body = """
            <status code="ok" class="mozwebext">
              <summary>Ok</summary>
              <details>Operation successfull.</details>
            </status>
            """
    elif request.method == "GET" and re.search("/request/30902/?", request.url):
        status = 200
        body = """
            <request id="30902" creator="nemo">
          <action type="submit">
            <source project="SUSE:Factory:Head" 
              package="perl-XML-DOM-XPath" rev="3"/>
            <target project="SUSE:SLE-12:GA" 
              package="perl-XML-DOM-XPath"/>
            <acceptinfo rev="1" 
              srcmd5="b3b89e4efa25d04f814bcce615455ac7" 
              osrcmd5="d41d8cd98f00b204e9800998ecf8427e"/>
          </action>
          <state name="accepted" who="foobar" 
            when="2014-01-24T13:11:52">
            <comment>Accepted submit request 30902 from user helloworld
            </comment>
          </state>
          <review state="accepted" when="2014-01-22T17:51:08" 
              who="foobar" by_package="perl-XML-DOM-XPath" 
              by_project="SUSE:Factory:Head">
            <comment>okay</comment>
            <history who="foobar" when="2014-01-23T12:30:39">
              <description>Review got accepted</description>
              <comment>okay</comment>
            </history>
          </review>
          <review state="accepted" when="2014-01-22T17:51:08" 
              who="helloworld" by_group="maintenance-team">
            <comment>Accept manually without review.</comment>
            <history who="helloworld" when="2014-01-22T18:12:29">
              <description>Review got accepted</description>
              <comment>Accept manually without review.</comment>
            </history>
          </review>
          <review state="accepted" when="2014-01-22T17:55:07" 
              who="echo" by_group="legal-team">
            <comment/>
            <history who="echo" when="2014-01-23T19:24:37">
              <description>Review got accepted</description>
            </history>
          </review>
          <description>Required package for FATE#315181 (virt-v2v)
          </description>
        """
        if params.get("withhistory", ['0']) == ['1'] \
                or params.get("withfullhistory", ['0']) == ['1']:
            body += """
                <history who="foo" when="2014-01-22T17:51:08">
                  <description>Request created</description>
                  <comment>Required package for FATE#315181 (virt-v2v)</comment>
                </history>
                <history who="bar" when="2014-01-22T17:55:07">
                  <description>Request got a new review request</description>
                  <comment>{"delegate": "Logic only implemented for SUSE"}
                  </comment>
                </history>
                <history who="bar" when="2014-01-23T19:24:37">
                  <description>Request got reviewed</description>
                </history>
                <history who="hello" when="2014-01-24T13:11:52">
                  <description>Request got accepted</description>
                  <comment>Accepted submit request 30902 from user nemo
                  </comment>
                </history>
            """
        if params.get("withfullhistory", ['0']) == ['1']:
            body += """
                  <history who="acceptor" when="2014-01-23T19:24:37">
                    <description>Review got accepted</description>
                  </history>
            """
        body += "</request>"
    elif re.search("request/?$", request.url):
        status = 200
        body = """
            <directory>
              <entry name="179682"/>
              <entry name="179683"/>
              <entry name="179684"/>
              <entry name="179685"/>
              <entry name="179686"/>
              <entry name="179687"/>
              <entry name="179688"/>
              <entry name="179689"/>
              <entry name="179690"/>
              <entry name="179691"/>
              <entry name="179692"/>
              <entry name="179693"/>
            </directory>
        """
    elif (request.method == "GET" and re.search(
            "request/30902/?cmd=diff$", request.url
    )) or (request.method == "POST" and "diff" in params.get("cmd", [])):
        status = 200
        if "xml" in params.get("view", ["plain"]):
            body = """<request id="30902" actions="0">
  <action type="submit">
  <source project="SUSE:Factory:Head" package="perl-XML-DOM-XPath" rev="3"/>
  <target project="SUSE:SLE-12:GA" package="perl-XML-DOM-XPath"/>
  <acceptinfo rev="1" srcmd5="b3b89e4efa25d04f814bcce615455ac7" osrcmd5="d41d8cd98f00b204e9800998ecf8427e"/>
<sourcediff key="0de9f643081bd0b6e287be4e72c4f388">
  <old project="SUSE:SLE-12:GA" package="perl-XML-DOM-XPath" rev="d41d8cd98f00b204e9800998ecf8427e" srcmd5="d41d8cd98f00b204e9800998ecf8427e"/>
  <new project="SUSE:SLE-12:GA" package="perl-XML-DOM-XPath" rev="b3b89e4efa25d04f814bcce615455ac7" srcmd5="b3b89e4efa25d04f814bcce615455ac7"/>
  <files>
    <file state="added">
      <new name="XML-DOM-XPath-0.14.tar.gz" md5="51a40df96c2f92829e1a4f84782fa75e" size="12410"/>
      <diff binary="1" lines="0"/>
    </file>
    <file state="added">
      <new name="perl-XML-DOM-XPath.changes" md5="350164d3d923003682a645e8b1790edb" size="721"/>
      <diff lines="23">@@ -0,0 +1,22 @@
+-------------------------------------------------------------------
+Tue Aug  6 22:46:18 UTC 2013 - rcurtis@suse.com
+
+- Updated spec file to replace perl_requires macro with preferred SUSE Requires:  perl &gt;= x.x format
+
+-------------------------------------------------------------------
+Mon Aug  5 10:10:37 UTC 2013 - cfarrell@suse.com
+
+- license update: Artistic-1.0 or GPL-1.0+
+  SPDX syntax
+
+-------------------------------------------------------------------
+Wed Dec  1 13:36:09 UTC 2010 - coolo@novell.com
+
+- switch to perl_requires macro
+
+-------------------------------------------------------------------
+Wed Aug  4 12:51:34 UTC 2010 - chris@computersalat.de
+
+- initial package 0.14
+  * created by cpanspec 1.78
+
</diff>
    </file>
    <file state="added">
      <new name="perl-XML-DOM-XPath.spec" md5="584694dc246c40f449d20b9e158fda20" size="2300"/>
      <diff lines="79">@@ -0,0 +1,78 @@
+#
+# spec file for package perl-XML-DOM-XPath
+#
+# Copyright (c) 2013 SUSE LINUX Products GmbH, Nuernberg, Germany.
+#
+# All modifications and additions to the file contributed by third parties
+# remain the property of their copyright owners, unless otherwise agreed
+# upon. The license for this file, and modifications and additions to the
+# file, is the same license as for the pristine package itself (unless the
+# license for the pristine package is not an Open Source License, in which
+# case the license is the MIT License). An "Open Source License" is a
+# license that conforms to the Open Source Definition (Version 1.9)
+# published by the Open Source Initiative.
+
+# Please submit bugfixes or comments via http://bugs.opensuse.org/
+#
+
+
+%bcond_with pod
+
+Name:           perl-XML-DOM-XPath
+%define cpan_name XML-DOM-XPath
+Summary:        Perl extension to add XPath support to XML::DOM, using XML::XPath engine
+License:        Artistic-1.0 or GPL-1.0+
+Group:          Development/Libraries/Perl
+Version:        0.14
+Release:        0
+Url:            http://search.cpan.org/dist/XML-DOM-XPath/
+Source:         http://www.cpan.org/modules/by-module/XML/XML-DOM-XPath-%{version}.tar.gz
+BuildArch:      noarch
+BuildRoot:      %{_tmppath}/%{name}-%{version}-build
+Requires:       perl &gt;= 5.16
+BuildRequires:  perl &gt;= 5.16
+BuildRequires:  perl-macros
+%if %{with pod}
+BuildRequires:  perl(Test::Pod)
+BuildRequires:  perl(Test::Pod::Coverage) &gt;= 1.00
+%endif
+BuildRequires:  perl(XML::DOM)
+BuildRequires:  perl(XML::XPathEngine) &gt;= 0.1
+Requires:       perl(XML::DOM)
+Requires:       perl(XML::XPathEngine) &gt;= 0.1
+
+%description
+XML::DOM::XPath allows you to use XML::XPath methods to query a DOM. This
+is often much easier than relying only on getElementsByTagName.
+
+Authors:
+--------
+    Michel Rodriguez &lt;mirod@cpan.org&gt;
+
+%prep
+%setup -q -n %{cpan_name}-%{version}
+
+%build
+%{__perl} Makefile.PL INSTALLDIRS=vendor
+%{__make} %{?_smp_mflags}
+
+%check
+%{__make} test
+
+%install
+%perl_make_install
+# do not perl_process_packlist (noarch)
+# remove .packlist file
+%{__rm} -rf $RPM_BUILD_ROOT%perl_vendorarch
+# remove perllocal.pod file
+%{__rm} -rf $RPM_BUILD_ROOT%perl_archlib
+%perl_gen_filelist
+
+%clean
+%{__rm} -rf $RPM_BUILD_ROOT
+
+%files -f %{name}.files
+%defattr(-,root,root,-)
+%doc Changes README
+
+%changelog
</diff>
    </file>
  </files>
</sourcediff>
</action>
</request>"""
        else:
            body = """
changes files:
--------------

++++++ new changes file:
--- perl-XML-DOM-XPath.changes
+++ perl-XML-DOM-XPath.changes
@@ -0,0 +1,22 @@
+-------------------------------------------------------------------
+Tue Aug  6 22:46:18 UTC 2013 - rcurtis@suse.com
+
+- Updated spec file to replace perl_requires macro with preferred SUSE Requires:  perl >= x.x format
+
+-------------------------------------------------------------------
+Mon Aug  5 10:10:37 UTC 2013 - cfarrell@suse.com
+
+- license update: Artistic-1.0 or GPL-1.0+
+  SPDX syntax 
+
+-------------------------------------------------------------------
+Wed Dec  1 13:36:09 UTC 2010 - coolo@novell.com
+
+- switch to perl_requires macro
+
+-------------------------------------------------------------------
+Wed Aug  4 12:51:34 UTC 2010 - chris@computersalat.de
+
+- initial package 0.14
+  * created by cpanspec 1.78
+

new:
----
  XML-DOM-XPath-0.14.tar.gz
  perl-XML-DOM-XPath.changes
  perl-XML-DOM-XPath.spec

spec files:
-----------

++++++ new spec file:
--- perl-XML-DOM-XPath.spec
+++ perl-XML-DOM-XPath.spec

        """
    elif (request.method == "POST"
          and "changereviewstate" in params.get("cmd", [])):
        status = 403
        body = "Forbidden for url: http://api.example.com/request/30902"
    else:
        status = 404
        body = """
            <status code="not_found">
              <summary>Couldn't find request with id '3090200000'
              </summary>
            </status>
        """

    headers['request-id'] = '728d329e-0e86-11e4-a748-0c84dc037c13'
    return status, headers, body


class TestRequest(OscTest):
    def setUp(self):
        super().setUp()

        self.mock_request(
            method=responses.GET,
            url=re.compile(self.osc.url + '/request.*'),
            callback=CallbackFactory(callback)
        )
        self.mock_request(
            method=responses.POST,
            url=re.compile(self.osc.url + '/request.*'),
            callback=CallbackFactory(callback)
        )
        self.mock_request(
            method=responses.GET,
            url=re.compile(self.osc.url + r'/comments/request/\d+.*'),
            callback=CallbackFactory(callback)
        )
        self.mock_request(
            method=responses.POST,
            url=re.compile(self.osc.url + r'/comments/request/\d+.*'),
            callback=CallbackFactory(callback)
        )

    @responses.activate
    def test_get_list(self):
        response = self.osc.requests.get_list()
        self.assertEqual(response.tag, "directory")
        self.assertEqual(response.countchildren(), 12)

    @responses.activate
    def test_get(self):
        with self.subTest("no history"):
            response = self.osc.requests.get(30902)
            self.assertEqual(response.tag, "request")
            self.assertEqual(response.get("id"), "30902")
            self.assertEqual(response.get("creator"), "nemo")
            self.assertEqual(len(response.xpath("//request/history")), 0)

        with self.subTest("with history"):
            response = self.osc.requests.get(30902, withhistory=True)
            self.assertEqual(response.tag, "request")
            self.assertEqual(response.get("id"), "30902")
            self.assertEqual(response.get("creator"), "nemo")
            self.assertEqual(len(response.xpath("//request/history")), 4)

        with self.subTest("with full history"):
            response = self.osc.requests.get(30902, withfullhistory=True)
            self.assertEqual(response.tag, "request")
            self.assertEqual(response.get("id"), "30902")
            self.assertEqual(response.get("creator"), "nemo")
            self.assertEqual(len(response.xpath("//request/history")), 5)

    @responses.activate
    def test_cmd(self):
        with self.subTest("plain diff"):
            response = self.osc.requests.cmd(30902, "diff")
            self.assertTrue(isinstance(response, str))
            self.assertIn("changes files:", response)
            self.assertIn("+++ perl-XML-DOM-XPath.changes", response)
        with self.subTest("xml diff"):
            response = self.osc.requests.cmd(30902, "diff", view="xml")
            self.assertTrue(isinstance(response, ObjectifiedElement))
        with self.subTest("changereviewstate"):
            self.assertRaises(
                ValueError,
                self.osc.requests.cmd, 30902, "changereviewstate"
            )

    @responses.activate
    def test_comment(self):
        with self.subTest("get"):
            response = self.osc.requests.get_comments(30902)
            self.assertTrue(isinstance(response, ObjectifiedElement))
            self.assertEqual(len(response.findall("comment")), 2)
        with self.subTest("add"):
            response = self.osc.requests.add_comment(30902, "hello wørld")
            self.assertTrue(response)
