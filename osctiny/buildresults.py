"""
Build result extension
----------------------
"""
# pylint: disable=too-few-public-methods
from urllib.parse import urljoin

from .base import ExtensionBase


class Build(ExtensionBase):
    """
    Osc extension for retrieving build results
    """
    base_path = "/build"

    def get(self, project, package=None, repo=None, **params):
        """
        Get build infos

        If no parameters are supplied, a compact list of build states for all
        packages in the project are returned.

        If a ``package`` and/or ``repo`` are supplied, an extended list of build
        results for these particular values is returned.

        :param project: Project name
        :param package: Package name
        :param repo: Repository name
        :param params: Additional parameters
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement

        .. versionadded:: 0.1.1
        """
        params["package"] = package
        params["repository"] = repo
        response = self.osc.request(
            method="GET",
            url=urljoin(self.osc.url, "{}/{}/_result".format(self.base_path,
                                                             project)),
            data=params
        )

        return self.osc.get_objectified_xml(response)
