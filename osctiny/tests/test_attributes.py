import responses

from .base import OscTest


class TestAttribute(OscTest):
    def setUp(self):
        super().setUp()

        self.mock_request(
            method=responses.GET,
            url=self.osc.url + '/attribute/',
            body="<directory><entry name='Foo'/><entry name='Bar'/></directory>"
        )

        self.mock_request(
            method=responses.GET,
            url=self.osc.url + '/attribute/Foo/_meta',
            body="<namespace name='Foo'><modifiable_by user='A'/></namespace>"
        )

        self.mock_request(
            method=responses.GET,
            url=self.osc.url + '/attribute/Foo',
            body="<directory><entry name='Hello'/><entry name='World'/></directory>"
        )

        self.mock_request(
            method=responses.GET,
            url=self.osc.url + '/attribute/Foo/Hello/_meta',
            body="<definition name='Hello' namespace='Foo'><description>Lorem ipsum</description>"
                 "<count>1</count><modifiable_by role='B'/></definition>"
        )

    @responses.activate
    def test_list_namespace(self):
        self.assertEqual(["Foo", "Bar"], self.osc.attributes.list_namespaces())

    @responses.activate
    def test_get_namespace_meta(self):
        meta = self.osc.attributes.get_namespace_meta("Foo")
        self.assertEqual(meta.get("name"), "Foo")

    @responses.activate
    def test_list_attributes(self):
        self.assertEqual(["Hello", "World"], self.osc.attributes.list_attributes("Foo"))

    @responses.activate
    def test_get_attribute_meta(self):
        meta = self.osc.attributes.get_attribute_meta("Foo", "Hello")
        self.assertEqual(meta.get("name"), "Hello")
        self.assertEqual(meta.get("namespace"), "Foo")
