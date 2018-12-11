import re

import responses

from .base import OscTest, CallbackFactory


def callback(headers, params, request):
    if request.method == "GET" and re.search("request/30902/?$", request.url):
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
    )) or (request.method == "POST" and "cmd" in params):
        status = 200
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
        response = self.osc.requests.cmd(30902, "diff")
        self.assertTrue(isinstance(response, str))
        self.assertIn("changes files:", response)
        self.assertIn("+++ perl-XML-DOM-XPath.changes", response)
