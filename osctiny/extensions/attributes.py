"""
Attributes extension
--------------------

.. versionadded:: 0.8.0
"""
import typing
from urllib.parse import urljoin

from lxml.objectify import ObjectifiedElement

from ..utils.base import ExtensionBase


class Attribute(ExtensionBase):
    """
    Access attribute namespaces and definitions
    """
    base_path = "/attribute"

    def list_namespaces(self) -> typing.List[str]:
        """
        Get a list of all namespaces

        :return: List of namespace names
        """
        response = self.osc.request(
            url=urljoin(self.osc.url, f"{self.base_path}/"),
            method="GET"
        )
        content = self.osc.get_objectified_xml(response)
        return [entry.get("name") for entry in content.findall("entry")]

    def get_namespace_meta(self, namespace: str) -> ObjectifiedElement:
        """
        Get the meta of the namespace

        :param namespace: namespace name
        :return: Objectified XML element
        """
        response = self.osc.request(
            url=urljoin(self.osc.url, f"{self.base_path}/{namespace}/_meta"),
            method="GET"
        )
        return self.osc.get_objectified_xml(response)

    def list_attributes(self, namespace: str) -> typing.List[str]:
        """
        List the attributes available in namespace

        :param namespace: Namespace name
        :return: List of attribute names
        """
        response = self.osc.request(
            url=urljoin(self.osc.url, f"{self.base_path}/{namespace}"),
            method="GET"
        )
        content = self.osc.get_objectified_xml(response)
        return [entry.get("name") for entry in content.findall("entry")]

    def get_attribute_meta(self, namespace: str, name: str) -> ObjectifiedElement:
        """
        Get meta data for attribute

        :param namespace: Namespace name
        :param name: Attribute name
        :return: Objectified XML element
        """
        response = self.osc.request(
            url=urljoin(self.osc.url, f"{self.base_path}/{namespace}/{name}/_meta"),
            method="GET"
        )
        return self.osc.get_objectified_xml(response)
