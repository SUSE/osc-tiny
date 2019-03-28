"""
Persons and groups extension
----------------------------
"""
import errno
import os
from urllib.parse import urljoin

from .base import ExtensionBase


class Group(ExtensionBase):
    """
    The BuildService group API is accessible through this object.
    """
    base_path = "/group/"

    def get_list(self, login=None):
        """
        Get all groups or all groups containing user ``login``

        :param login: Username to filter for
        :rtype: lxml.objectify.ObjectifiedElement
        """
        data = {}
        if login:
            data["login"] = login
        response = self.osc.request(
            url=urljoin(self.osc.url, self.base_path),
            method="GET",
            data=data
        )

        return self.osc.get_objectified_xml(response)

    def get(self, title):
        """
        Get details for group ``title``

        :param title: Title/name of the group
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        response = self.osc.request(
            url=urljoin(self.osc.url, self.base_path + title),
            method="GET",
        )

        return self.osc.get_objectified_xml(response)


class Person(ExtensionBase):
    """
    The BuildService person API is accessible through this object.
    """
    base_path = "/person/"

    def get(self, userid):
        """
        Get details for user ``userid``

        :param userid: Username
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        response = self.osc.request(
            url=urljoin(self.osc.url, self.base_path + userid),
            method="GET",
        )

        return self.osc.get_objectified_xml(response)
