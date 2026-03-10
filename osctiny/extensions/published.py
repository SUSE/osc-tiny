"""
Published binaries extension
-----------------------------
"""

from urllib.parse import urljoin

from ..utils.base import ExtensionBase


class Published(ExtensionBase):
    """
    Osc extension for retrieving published binaries

    .. versionadded:: 0.12.0
    """

    base_path = "/published"

    def get(self, project: str, repo: str, **params):
        """
        Get published repository info

        Returns directory listing or metadata (e.g. ``view=publishedpath``)
        for a given project and repository.

        :param project: Project name
        :param repo: Repository name
        :param params: Additional parameters
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        response = self.osc.request(
            method="GET",
            url=urljoin(self.osc.url, f"{self.base_path}/{project}/{repo}"),
            params=params,
        )

        return self.osc.get_objectified_xml(response)

    def get_binary_list(self, project: str, repo: str, arch: str, **params):
        """
        Get a list of published binaries in a repository

        Returns the directory listing of published packages for a given
        project, repository, and architecture combination.

        :param project: Project name
        :param repo: Repository name
        :param arch: Architecture name
        :param params: Additional parameters
        :return: Objectified XML element containing directory entries
        :rtype: lxml.objectify.ObjectifiedElement
        """
        response = self.osc.request(
            method="GET",
            url=urljoin(self.osc.url, f"{self.base_path}/{project}/{repo}/{arch}"),
            params=params,
        )

        return self.osc.get_objectified_xml(response)
