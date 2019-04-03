"""
Search extension
----------------
"""
from urllib.parse import urljoin

from .base import ExtensionBase


class Search(ExtensionBase):
    """
    Osc extension providing methods for searching
    """
    base_path = "/search/"

    def search(self, path, xpath, **kwargs):
        """
        Search for objects in buildservice

        .. note:: Shortcuts

            There are shortcut method for the object types ``project``,
            ``package`` and ``request``. These only expect the ``xpath``
            argument, e.g.:

            .. code:: python

                Osc.search.request("starts-with(@name,'SUSE:Maintenance')")

        :param path: object type / relative URL
        :param xpath: XPath expression to filter results
        :param kwargs: Additional parameters to be passed to the underlying API
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        kwargs["match"] = xpath
        response = self.osc.request(
            url=urljoin(self.osc.url, self.base_path + path.lstrip("/")),
            data=kwargs,
            method='GET'
        )
        return self.osc.get_objectified_xml(response)

    def __getattr__(self, name):
        allowed = ['project', 'package', 'request']
        if name not in allowed:
            raise AttributeError(
                "No such attribute: '{}'. Use one of: {}".format(
                    name, ", ".join(allowed)
                )
            )

        return lambda *args, **kwargs: self.search(name, *args, **kwargs)
