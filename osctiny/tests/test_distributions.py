# -*- coding: utf8 -*-
import re

from requests.exceptions import HTTPError
import responses

from .base import OscTest, CallbackFactory


class TestDistribution(OscTest):
    @responses.activate
    def test_get_list(self):
        def _base(include_remotes):
            response = self.osc.distributions.get_list(include_remotes=include_remotes)
            self.assertEqual({int(d.get("id")) for d in response.distribution},
                             {14495, 14498, 14501})

        def dist_list_callback(headers, params, request):
            status, body = 200, """
            <distributions>
              <distribution vendor="openSUSE" version="Tumbleweed" id="14495">
                <name>openSUSE Tumbleweed</name>
                <project>openSUSE:Factory</project>
                <reponame>openSUSE_Tumbleweed</reponame>
                <repository>snapshot</repository>
                <link>http://www.opensuse.org/</link>
                <architecture>i586</architecture>
                <architecture>x86_64</architecture>
              </distribution>
              <distribution vendor="openSUSE" version="15.2" id="14498">
                <name>openSUSE Leap 15.2</name>
                <project>openSUSE:Leap:15.2</project>
                <reponame>openSUSE_Leap_15.2</reponame>
                <repository>standard</repository>
                <link>http://www.opensuse.org/</link>
                <architecture>x86_64</architecture>
              </distribution>
              <distribution vendor="openSUSE" version="15.1" id="14501">
                <name>openSUSE Leap 15.1</name>
                <project>openSUSE:Leap:15.1</project>
                <reponame>openSUSE_Leap_15.1</reponame>
                <repository>standard</repository>
                <link>http://www.opensuse.org/</link>
                <architecture>x86_64</architecture>
              </distribution>
            </distributions>"""
            return status, headers, body

        self.mock_request(
            method=responses.GET,
            url=re.compile(self.osc.url + r'/distributions(/include_remotes)?/?$'),
            callback=CallbackFactory(dist_list_callback)
        )

        with self.subTest("include remotes"):
            _base(True)

        with self.subTest("do not include remotes"):
            _base(False)

    @responses.activate
    def test_get(self):
        def dist_callback(headers, params, request):
            if re.search("14498/?$", request.url):
                status, body = 200, """<?xml version="1.0" encoding="UTF-8"?>
                <hash>
                  <id type="integer">14498</id>
                  <vendor>openSUSE</vendor>
                  <version>15.2</version>
                  <name>openSUSE Leap 15.2</name>
                  <project>openSUSE:Leap:15.2</project>
                  <reponame>openSUSE_Leap_15.2</reponame>
                  <repository>standard</repository>
                  <link>http://www.opensuse.org/</link>
                  <architectures type="array">
                    <architecture>x86_64</architecture>
                  </architectures>
                </hash>"""
            else:
                status, body = 404, """
                <status code="not_found">
                  <summary>Couldn't find Distribution with 'id'=******</summary>
                </status>"""
            return status, headers, body

        self.mock_request(
            method=responses.GET,
            url=re.compile(self.osc.url + r'/distributions/\d+/?$'),
            callback=CallbackFactory(dist_callback)
        )

        with self.subTest("existing distro"):
            response = self.osc.distributions.get(14498)
            self.assertEqual(response.id, 14498)
            self.assertEqual(response.vendor, "openSUSE")
            self.assertEqual(response.version, 15.2)

        with self.subTest("unknown distro"):
            self.assertRaises(HTTPError, self.osc.distributions.get, 99999)
