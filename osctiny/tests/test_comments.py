import re

from lxml.objectify import ObjectifiedElement
from requests.exceptions import HTTPError
import responses

from .base import OscTest, CallbackFactory


class TestComment(OscTest):
    @responses.activate
    def test_delete_comment(self):
        def callback(headers, params, request):
            comment_id = -1
            status, body = 404, """
            <status code="not_found">
                <summary>Couldn't find Comment with 'id'=******</summary>
            </status>"""

            match = re.search(r"/(?P<id>\d+/?$)", request.url)
            if match:
                comment_id = int(match.group("id"))

            if comment_id == 666:
                status, body = 200, """<status code="ok"><summary/></status>"""

            return status, headers, body

        self.mock_request(
            method=responses.DELETE,
            url=re.compile(self.osc.url + r'/comment/\d+'),
            callback=CallbackFactory(callback)
        )

        with self.subTest("Existing comment"):
            self.assertTrue(self.osc.comments.delete(666))

        with self.subTest("Non-existing comment"):
            response = self.osc.comments.delete(1)
            self.assertTrue(isinstance(response, ObjectifiedElement))

    @responses.activate
    def test_add_comment(self):
        def callback(headers, params, request):
            status, body = 400, """
            <status code="invalid_record">
              <summary>Body is too long (maximum is 6 characters)</summary>
            </status>
            """
            if len(request.body) <= 6:
                status = 200
                body = '<status code="ok"/>'
            return status, headers, body

        self.mock_request(
            method=responses.POST,
            url=re.compile(self.osc.url + r'/comments/project/.+'),
            callback=CallbackFactory(callback)
        )

        with self.subTest("Good comment"):
            self.assertTrue(self.osc.comments.add("project", ("home:nemo",), "foo"))

        with self.subTest("Bad comment"):
            self.assertRaises(HTTPError, self.osc.comments.add, 'project', ('home:nemo',),
                              'don\'t panic')
