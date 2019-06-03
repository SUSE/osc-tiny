"""
Projects extension
------------------
"""
import re
from urllib.parse import urljoin

from lxml.etree import tounicode
from lxml.objectify import fromstring

from .base import ExtensionBase


TEMPLATE_CREATE_ATTR = "<attributes><attribute namespace='' name=''>" \
                       "<value></value></attribute></attributes>"


class Project(ExtensionBase):
    """
    Osc extension to interact with projects
    """
    base_path = "/source"
    attribute_pattern = re.compile(r"^((?P<prefix>[^:]+):)?(?P<name>.+)$")

    def get_list(self, deleted=False):
        """
        Get list of projects

        :param deleted: show deleted projects instead of existing
        :type deleted: bool
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
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

        .. note::

            Be aware of namespace prefixes.

            When specifying the ``attribute`` argument make sure to include the
            namespace prefix and separate both by a colon, e.g.
            ``OBS:IncidentPriority``.

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

    def set_attribute(self, project, attribute, value):
        """
        Set or update an attribute of a project

        :param project: project name
        :param attribute: attribute name (can include prefix separated by colon)
        :param value: attribute value
        :return: ``True``, if successful. Otherwise API response
        :rtype: bool or lxml.objectify.ObjectifiedElement
        """
        url = urljoin(
            self.osc.url,
            "{}/{}/_attribute".format(
                self.base_path, project
            )
        )
        match = self.attribute_pattern.match(attribute)
        if match is None:
            raise ValueError("Invalid attribute format: {}".format(attribute))

        attr_xml = fromstring(TEMPLATE_CREATE_ATTR)
        attr_xml.attribute.set('namespace', match.group("prefix"))
        attr_xml.attribute.set('name', match.group("name"))
        # pylint: disable=protected-access
        attr_xml.attribute.value._setText(str(value))

        response = self.osc.request(
            url=url,
            method="POST",
            data=tounicode(attr_xml)
        )

        parsed = self.osc.get_objectified_xml(response)
        if response.status_code == 200 and parsed.get("code") == "ok":
            return True

        return parsed

    def delete_attribute(self, project, attribute):
        """
        Delete an attribute of a project

        :param project: name of project
        :param attribute: name of attribute
        :return: ``True``, if successful. Otherwise API response
        :rtype: bool or lxml.objectify.ObjectifiedElement
        """
        url = urljoin(
            self.osc.url,
            "{}/{}/_attribute/{}".format(
                self.base_path, project, attribute
            )
        )

        response = self.osc.request(
            url=url,
            method="DELETE",
        )
        parsed = self.osc.get_objectified_xml(response)
        if response.status_code == 200 and parsed.get("code") == "ok":
            return True

        return parsed

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

    def add_comment(self, project, comment, parent_id=None):
        """
        Add a comment to a project

        .. versionadded: 0.1.2

        :param project: name of project
        :param comment: Comment to be added
        :param parent_id: ID of parent comment. Default: ``None``
        :return: ``True``, if successful. Otherwise API response
        :rtype: bool or lxml.objectify.ObjectifiedElement
        """
        url = urljoin(self.osc.url, '/comments' + self.base_path + project)
        if parent_id and str(parent_id).isnumeric():
            url += "?parent_id={}".format(parent_id)

        response = self.osc.request(
            url=url,
            method="POST",
            data=comment
        )
        parsed = self.osc.get_objectified_xml(response)
        if response.status_code == 200 and parsed.get("code") == "ok":
            return True

        return parsed

    def get_history(self, project, meta=True, rev=None, **kwargs):
        """
        Get history of project

        To get just a particular revision, use the ``rev`` argument.

        :param project: name of project
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
            url=urljoin(self.osc.url, "{}/{}/_project/_history".format(
                self.base_path, project
            )),
            method="GET",
            data=kwargs
        )

        return self.osc.get_objectified_xml(response)

    def delete(self, project, force=False, comment=None):
        """
        Delete project

        .. versionadded:: 0.1.2

        :param project: Project name
        :param force: Delete project even if subprojects, packages or pending
                      requests for those packages exist
        :param comment: Optional comment
        :return: ``True``, if successful. Otherwise API response
        :rtype: bool or lxml.objectify.ObjectifiedElement
        """
        params = {'force': force, 'comment': comment}

        response = self.osc.request(
            url=urljoin(
                self.osc.url,
                "/".join((self.base_path, project))
            ),
            method="DELETE",
            data=params
        )

        parsed = self.osc.get_objectified_xml(response)
        if response.status_code == 200 and parsed.get("code") == "ok":
            return True

        return parsed

    def exists(self, project):
        """
        Check whether project exists

        .. versionadded:: 0.1.2

        :param project: Project name
        :return: ``True``, if package exists, otherwise ``False``
        """
        response = self.osc.request(
            url=urljoin(
                self.osc.url,
                "/".join((self.base_path, project))
            ),
            method="HEAD",
            raise_for_status=False
        )

        return response.status_code == 200
