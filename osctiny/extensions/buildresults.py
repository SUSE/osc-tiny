"""
Build result extension
----------------------
"""
# pylint: disable=too-few-public-methods
from __future__ import unicode_literals
from six.moves.urllib.parse import urljoin

from ..utils.base import ExtensionBase


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
            params=params
        )

        return self.osc.get_objectified_xml(response)

    def get_history(self, project, package, repo, arch="x86_64", **params):
        """
        Get build history

        :param project: Project name
        :param package: Package name
        :param repo: Repository name
        :param arch: Architecture name
        :param params: Additional parameters
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement

        .. versionadded:: 0.5.0
        """

        response = self.osc.request(
            method="GET",
            url=urljoin(self.osc.url, "{}/{}/{}/{}/{}/_history".format(self.base_path,
                                                             project,repo,arch,package)),
            params=params
        )

        return self.osc.get_objectified_xml(response)

    def get_package_list(self, project, repo, arch):
        """
        Get a list of packages for which build results exist

        :param project: Project name
        :param repo: Repository name
        :param arch: Architecture name
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement

        .. versionadded:: 0.2.4
        """
        response = self.osc.request(
            method="GET",
            url=urljoin(self.osc.url, "{}/{}/{}/{}".format(
                self.base_path, project, repo, arch
            ))
        )

        return self.osc.get_objectified_xml(response)

    def get_binary_list(self, project, repo, arch, package, **params):
        """
        Get a list of built RPMs

        :param project: Project name
        :param repo: Repository name
        :param arch: Architecture name
        :param package: Package name
        :param params: Additional parameters
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement

        .. versionadded:: 0.1.3
        """
        response = self.osc.request(
            method="GET",
            url=urljoin(self.osc.url, "{}/{}/{}/{}/{}".format(
                self.base_path, project, repo, arch, package
            )),
            params=params
        )

        return self.osc.get_objectified_xml(response)

    # pylint: disable=too-many-arguments
    def get_binary(self, project, repo, arch, package, filename):
        """
        Get the build binary file

        :param project: Project name
        :param repo: Repository name
        :param arch: Architecture name
        :param package: Package name
        :param filename: File name
        :return: Raw response
        :rtype: str

        .. versionadded:: 0.2.4
        """
        response = self.osc.request(
            method="GET",
            url=urljoin(self.osc.url, "{}/{}/{}/{}/{}/{}".format(
                self.base_path, project, repo, arch, package, filename
            )),
        )

        return response.text

    def cmd(self, project, cmd, **params):
        """
        Execute ``cmd`` for ``project`` and get response

        .. versionadded:: 0.6.2

        :param str project: Project name
        :param str cmd: Command to execute
        :param params: Additional parameters
        """
        allowed_cmds = ["rebuild", "abortbuild", "restartbuild", "unpublish", "sendsysrq",
                        "wipe"]
        if cmd not in allowed_cmds:
            raise ValueError(f"Invalid command: '{cmd}'. Use one of: {', '.join(allowed_cmds)}")

        params["cmd"] = cmd
        response = self.osc.request(
            url=urljoin(self.osc.url, f"{self.base_path}/{project}"),
            method="POST",
            params=params
        )
        return self.osc.get_objectified_xml(response)
