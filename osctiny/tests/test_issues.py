# -*- coding: utf8 -*-
import re

from lxml.objectify import ObjectifiedElement
from requests.exceptions import HTTPError
import responses

from .base import OscTest, CallbackFactory


class TestIssue(OscTest):
    def setUp(self):
        super(TestIssue, self).setUp()

        def callback(headers, params, request):
            status, body = 200, """
            <issue-trackers>
              <issue-tracker>
                <name>boost</name>
                <kind>trac</kind>
                <description>Boost Trac</description>
                <url>https://svn.boost.org/trac/boost/</url>
                <show-url>https://svn.boost.org/trac/boost/ticket/@@@</show-url>
                <regex>boost#(\d+)</regex>
                <label>boost#@@@</label>
                <enable-fetch>false</enable-fetch>
              </issue-tracker>
              <issue-tracker>
                <name>bco</name>
                <kind>bugzilla</kind>
                <description>Clutter Project Bugzilla</description>
                <url>http://bugzilla.clutter-project.org/</url>
                <show-url>http://bugzilla.clutter-project.org/show_bug.cgi?id=@@@</show-url>
                <regex>bco#(\d+)</regex>
                <label>bco#@@@</label>
                <enable-fetch>false</enable-fetch>
              </issue-tracker>
              <issue-tracker>
                <name>bnc</name>
                <kind>bugzilla</kind>
                <description>SUSE Bugzilla</description>
                <url>https://apibugzilla.novell.com/</url>
                <show-url>https://bugzilla.suse.com/show_bug.cgi?id=@@@</show-url>
                <regex>(?:bnc|BNC|bsc|BSC|boo|BOO)\s*[#:]\s*(\d+)</regex>
                <label>bsc#@@@</label>
                <enable-fetch>true</enable-fetch>
              </issue-tracker>
            </issue-trackers>"""
            return status, headers, body

        self.mock_request(
            method=responses.GET,
            url=re.compile(self.osc.url + '/issue_trackers/?$'),
            callback=CallbackFactory(callback)
        )

    @responses.activate
    def test_get_trackers(self):
        response = self.osc.issues.get_trackers()
        self.assertTrue(isinstance(response, ObjectifiedElement))
        self.assertEqual(response.countchildren(), 3)
        self.assertEqual(
            {x.text for x in response.xpath("issue-tracker/name")},
            {'boost', 'bco', 'bnc'}
        )

    @responses.activate
    def test_get_tracker(self):
        def callback(headers, params, request):
            if re.search("bnc/?$", request.url):
                status, body = 200, """
                <issue-tracker>
                  <name>bnc</name>
                  <kind>bugzilla</kind>
                  <description>SUSE Bugzilla</description>
                  <url>https://apibugzilla.novell.com/</url>
                  <show-url>https://bugzilla.suse.com/show_bug.cgi?id=@@@</show-url>
                  <regex>(?:bnc|BNC|bsc|BSC|boo|BOO)\s*[#:]\s*(\d+)</regex>
                  <label>bsc#@@@</label>
                  <enable-fetch>true</enable-fetch>
                </issue-tracker>"""
            else:
                status, body = 404, """
                <status code="not_found">
                  <summary>Unable to find issue tracker 'bnc2'</summary>
                </status>"""
            return status, headers, body

        self.mock_request(
            method=responses.GET,
            url=re.compile(self.osc.url + r'/issue_trackers/[^/]+/?$'),
            callback=CallbackFactory(callback)
        )

        with self.subTest("Valid tracker"):
            response = self.osc.issues.get_tracker("bnc")
            self.assertEqual(response.name.text, "bnc")

        with self.subTest("Invalid tracker"):
            self.assertRaises(HTTPError, self.osc.issues.get_tracker, "nemo")

    @responses.activate
    def test_get(self):
        def callback(headers, params, request):
            if params.get("force_update", ["0"]) == ["1"]:
                status, body = 200, u"""
                <issue>
                  <created_at>2020-01-04 14:12:00 UTC</created_at>
                  <name>1160086</name>
                  <tracker>bnc</tracker>
                  <label>bsc#1160086</label>
                  <url>https://bugzilla.suse.com/show_bug.cgi?id=1160086</url>
                  <state>OPEN</state>
                  <summary>føø bar</summary>
                  <owner>
                    <login>nemo</login>
                    <email>nemo@suse.com</email>
                    <realname>Caþtæn Nemo</realname>
                  </owner>
                </issue>"""
            else:
                status, body = 200, """
                <issue>
                  <created_at>2020-01-04 14:12:00 UTC</created_at>
                  <name>1160086</name>
                  <tracker>bnc</tracker>
                  <label>bsc#1160086</label>
                  <url>https://bugzilla.suse.com/show_bug.cgi?id=1160086</url>
                </issue>"""
            return status, headers, body

        self.mock_request(
            method=responses.GET,
            url=re.compile(self.osc.url +
                           r'/issue_trackers/bnc/issues/1160086/?.*'),
            callback=CallbackFactory(callback)
        )

        with self.subTest("Manual force update"):
            response = self.osc.issues.get("bnc", 1160086, True)
            self.assertTrue(hasattr(response, "summary"))
            self.assertEqual(len(responses.calls), 2)

        with self.subTest("Manual force update"):
            response = self.osc.issues.get("bnc", 1160086, False)
            self.assertTrue(hasattr(response, "summary"))
            # to whom it may concern: `responses.calls` does not get reset
            # between sub-tests
            self.assertEqual(len(responses.calls), 4)
