"""
Projects extension
------------------
"""
from urllib.parse import urljoin

from .base import ExtensionBase


class Project(ExtensionBase):
    """
    Osc extension to interact with projects
    """
    base_path = "/source"

    def get_list(self, deleted=False):
        """
        Get list of projects

        :param deleted: show deleted projects instead of existing
        :type deleted: bool
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        deleted = '1' if deleted else '0'
        response = self.osc.request(
            url=urljoin(self.osc.url, self.base_path),
            method="GET",
            data={'deleted': deleted}
        )

        return self.osc.get_objectified_xml(response)

    def get_meta(self, project):
        """
        Get project metadata

        :param project: name of project
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        response = self.osc.request(
            url=urljoin(
                self.osc.url,
                "{}/{}/_meta".format(self.base_path, project)
            ),
            method="GET"
        )

        return self.osc.get_objectified_xml(response)

    def get_files(self, project, directory="", meta=False, rev=None, **kwargs):
        """
        List project files

        :param project: name of project
        :param directory: directory in project
        :param meta: switch for _meta files
        :type meta: bool
        :param rev: revision
        :type rev: int
        :param kwargs: More keyword arguments for API call
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        if meta:
            kwargs["meta"] = '1'
        if rev:
            kwargs["rev"] = str(rev)
        response = self.osc.request(
            url=urljoin(
                self.osc.url,
                "{}/{}/{}".format(self.base_path, project, directory)
            ),
            method="GET",
            data=kwargs
        )

        return self.osc.get_objectified_xml(response)

    def get_attribute(self, project, attribute=None):
        """
        Get one attribute of a project

        :param project: name of project
        :param attribute: name of attribute
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        url = urljoin(
            self.osc.url,
            "{}/{}/_attribute".format(
                self.base_path, project
            )
        )

        if attribute:
            url = "{}/{}".format(url, attribute)

        response = self.osc.request(url=url, method="GET")

        return self.osc.get_objectified_xml(response)

    def get_comments(self, project):
        """
        Get a list of comments for project

        :param project: name of project
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        response = self.osc.request(
            url=urljoin(self.osc.url,
                        '/comments/project/' + project),
            method="GET",
        )
        return self.osc.get_objectified_xml(response)

    def get_history(self, project, meta=True, rev=None, **kwargs):
        """
        Get history of project

        To get just a particular revision, use the ``rev`` argument.

        :param project: name of package
        :param meta: Switch between meta and non-meta (normally empty) revision
                     history
        :type meta: bool
        :param rev: History revision ID
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        if rev:
            kwargs["rev"] = rev
        kwargs["meta"] = "1" if meta else "0"

        response = self.osc.request(
            url=urljoin(self.osc.url, "/{}/_project/_history".format(project)),
            method="GET",
            data=kwargs
        )

        return self.osc.get_objectified_xml(response)
