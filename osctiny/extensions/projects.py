"""
Projects extension
------------------
"""
import re
from urllib.parse import urljoin
from warnings import warn

from lxml.etree import tounicode
from lxml.objectify import fromstring, SubElement

from ..utils.base import ExtensionBase


TEMPLATE_CREATE_ATTR = "<attributes><attribute namespace='' name=''></attribute></attributes>"
TEMPLATE_META = "<project name=''><title></title><description></description>" \
                "<build><enable/></build><publish><disable/></publish>" \
                "<debuginfo><enable/></debuginfo></project>"


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
            params={'deleted': deleted}
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

    # pylint: disable=too-many-arguments
    def put_meta(self, project, metafile=None, title=None, description=None,
                 bugowner=None, maintainer=None):
        """
        Edit project meta data or create a new project

        If no ``metafile`` is provided, a default template is used.

        .. versionadded:: 0.1.5

        .. deprecated:: 0.7.2
           Use :meth:`set_meta` instead

        :param project: name of project
        :param metafile: Complete metafile
        :type metafile: str or ElementTree
        :param title: Title for meta file
        :param description: Description for meta file
        :param bugowner: Bugowner for meta file
        :param maintainer: Maintainer for meta file
        :return: ``True``, if successful. Otherwise API response
        :rtype: bool or lxml.objectify.ObjectifiedElement
        """
        warn("Deprecated. Use projects.set_meta instead")

        return self.set_meta(project, metafile, title, description, bugowner,
                             maintainer)

    # pylint: disable=too-many-arguments
    def set_meta(self, project, metafile=None, title=None, description=None,
                 bugowner=None, maintainer=None, comment=None):
        """
        Edit project meta data or create a new project

        If no ``metafile`` is provided, a default template is used.

        .. versionadded:: 0.7.2

        .. versionchanged:: 0.7.8

           Added an optional ``comment`` argument to be used as commit message

        :param project: name of project
        :param metafile: Complete metafile
        :type metafile: str or ElementTree
        :param title: Title for meta file
        :param description: Description for meta file
        :param bugowner: Bugowner for meta file
        :param maintainer: Maintainer for meta file
        :param comment: Optional comment to use as commit message
        :return: ``True``, if successful. Otherwise API response
        :rtype: bool or lxml.objectify.ObjectifiedElement
        """
        if metafile is None:
            metafile = TEMPLATE_META

        if isinstance(metafile, (str, bytes)):
            metafile = fromstring(metafile)

        metafile.set("name", project)

        for required_field, text in (('title', title), ('description', description)):
            elem = metafile.find(required_field)
            if elem is None:
                elem = SubElement(metafile, required_field)

            if text is not None:
                # pylint: disable=protected-access
                elem._setText(text)

        def add_person(role: str, userid: str) -> None:
            person = metafile.xpath(f"person[@role='{role}']")
            if not person:
                person = [SubElement(metafile, 'person', role=role)]
            person[0].set("userid", userid)

        if bugowner:
            add_person("bugowner", bugowner)

        if maintainer:
            add_person("maintainer", maintainer)

        metafile.insert(0, metafile.title)
        metafile.insert(1, metafile.description)

        response = self.osc.request(
            url=urljoin(self.osc.url,
                        "/".join((self.base_path, project, "_meta"))),
            method="PUT",
            data=tounicode(metafile),
            params={"comment": comment}
        )

        parsed = self.osc.get_objectified_xml(response)
        if response.status_code == 200 and parsed.get("code") == "ok":
            return True

        return parsed

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

        .. deprecated:: 0.7.4

            Use :py:meth:`osctiny.extensions.packages.Package.get_files` or
            :py:meth:`osctiny.extensions.packages.Package.get_list` instead.

            The API URL used by this method is (depending on the value of ``directory``) identical
            to the one used by the above two methods.
        """
        if rev:
            kwargs["rev"] = str(rev)

        if not directory:
            return self.osc.packages.get_list(project=project, **kwargs)

        kwargs["meta"] = meta
        return self.osc.packages.get_files(project=project, package=directory, **kwargs)

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
        :param value: attribute value or list of values
        :return: ``True``, if successful. Otherwise API response
        :rtype: bool or lxml.objectify.ObjectifiedElement

        .. versionchanged:: 0.7.0
            Support attributes with multiple values
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

        value = value if isinstance(value, (list, tuple, set)) else [value]
        attr_xml = fromstring(TEMPLATE_CREATE_ATTR)
        attr_xml.attribute.set('namespace', match.group("prefix"))
        attr_xml.attribute.set('name', match.group("name"))
        for val in value:
            elem = SubElement(attr_xml.attribute, "value")
            # pylint: disable=protected-access
            elem._setText(str(val))

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

        .. versionchanged:: 0.1.8
            Use internally :py:class:`osctiny.comments.Comment.get`

        :param project: name of project
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        return self.osc.comments.get(
            obj_type="project",
            ids=(project,)
        )

    def add_comment(self, project, comment, parent_id=None):
        """
        Add a comment to a project

        .. versionadded: 0.1.2

        .. versionchanged:: 0.1.8
            Use internally :py:class:`osctiny.comments.Comment.add`

        :param project: name of project
        :param comment: Comment to be added
        :param parent_id: ID of parent comment. Default: ``None``
        :return: ``True``, if successful. Otherwise API response
        :rtype: bool or lxml.objectify.ObjectifiedElement
        """
        return self.osc.comments.add(
            obj_type="project",
            ids=(project,),
            comment=comment,
            parent_id=parent_id
        )

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

        kwargs["meta"] = meta

        response = self.osc.request(
            url=urljoin(self.osc.url, "{}/{}/_project/_history".format(
                self.base_path, project
            )),
            method="GET",
            params=kwargs
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
        params = {'force': force}

        response = self.osc.request(
            url=urljoin(
                self.osc.url,
                "/".join((self.base_path, project))
            ),
            method="DELETE",
            params=params,
            data=comment
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
        :return: ``True``, if project exists, otherwise ``False``
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

    create = set_meta
