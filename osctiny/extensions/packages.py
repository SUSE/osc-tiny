"""
Packages extension
------------------
"""
import os
import typing
from urllib.parse import urljoin

from lxml.etree import tounicode, SubElement, Element
from lxml.objectify import fromstring

from ..utils.base import ExtensionBase
from ..utils.errors import OscError


class Package(ExtensionBase):
    """
    Osc extension to interact with packages
    """
    base_path = "/source"
    new_package_meta_templ = "<package><title/><description/></package>"

    @staticmethod
    def cleanup_params(**params) -> typing.Union[dict, str]:
        """
        Prepare query parameters

        The build service is inconsistent in its validation of parameters. In most cases it does not
        complain about excess parameters, in some it complains about unexpected ones.

        :param params: Query parameters
        :return: The original dictionary of query parameters or a subset of it

        .. versionadded:: 0.7.4

        .. versionchanged:: 0.7.7
            Handle more inconsistencies in the API endpoints
        """
        view = params.get("view", "")
        if view == "info":
            # The 'info' view is strict about parameter validation
            return {key: value for key, value in params.items()
                    if key in ["parse", "arch", "repository", "view"]}
        if "productlist" in view:
            # The "deleted" parameter seems to have precedence over other acceptable parameters
            # (e.g. "view").
            # Product list views now honor the `expand` parameter.
            return f"view={view}&expand={'1' if params.get('expand') else '0'}"
        return params

    def get_list(self, project: str, deleted: typing.Optional[bool] = None, expand: bool = False,
                 **params):
        """
        Get packages from project

        .. versionadded:: 0.1.7
            Parameter ``deleted``

        .. versionadded:: 0.7.0
            Parameter ``expand``

        .. versionadded:: 0.7.4
            Parameter ``params``

        .. versionchanged:: 0.7.6
            Changed default value of ``expand`` to ``False``

        .. versionchanged:: 0.10.7
            Made the ``deleted`` parameter fully optional. It is no longer a boolean flag but really
            a boolean parameter, so ``deleted=0`` is actually added to the API call.

        :param project: name of project
        :param deleted: If true, also shows deleted packages instead of the present ones.
                        If False, then `deleted=0` is appended to the query explicitly.
                        Default is `None`, which implies no parameter addition to the query.
        :param expand: Include inherited packages and their project of origin
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        params.update({"expand": expand})
        if deleted is not None:
            params.update({"deleted": deleted})

        response = self.osc.request(
            url=urljoin(self.osc.url, "{}/{}".format(self.base_path, project)),
            method="GET",
            params=self.cleanup_params(**params)
        )

        return self.osc.get_objectified_xml(response)

    def get_meta(self, project, package, blame=False):
        """
        Get package metadata

        .. note:: When ``blame`` annotations are requested no XML object can be
                  returned!

        .. versionchanged:: 0.1.2
            Added parameter blame

        :param project: name of project
        :param package: name of package
        :param blame: Show metadata with change annotations
        :return: Objectified XML element or str
        :rtype: lxml.objectify.ObjectifiedElement or str
        """
        params = {}
        if blame:
            params["view"] = "blame"

        response = self.osc.request(
            url=urljoin(
                self.osc.url,
                "{}/{}/{}/_meta".format(self.base_path, project, package)
            ),
            method="GET",
            params=params
        )

        if blame:
            return response.text

        return self.osc.get_objectified_xml(response)

    # pylint: disable=too-many-arguments,protected-access
    def set_meta(self, project, package, title=None, description=None,
                 meta=None, comment=None):
        """
        Set package metadata

        .. note:: By setting the meta data ``package`` is created, if it does
                  not exist.

        Specify ``title`` and ``description`` to create an XML file with minimum
        content or provide a complete XML string via ``meta``.

        .. note:: If ``title`` or ``description`` is given in combination with
                  ``meta``, the existing values in ``meta`` will be overwritten.

        .. versionadded:: 0.1.2

        .. versionchanged:: 0.7.8

           Added an optional ``comment`` argument to be used as commit message

        :param project: Project name
        :param package: New package name
        :param title: Title for meta
        :param description: Description for meta
        :param meta: New content for meta
        :type meta: str or lxml.objectify.ObjectifiedElement
        :param comment: Optional comment to use as commit message
        :return:
        """
        if isinstance(meta, (str, bytes)):
            meta = fromstring(meta)

        if meta is not None:
            meta_xml = meta
        else:
            meta_xml = fromstring(self.new_package_meta_templ)

        if title:
            meta_xml.title._setText(title)
        if description:
            meta_xml.description._setText(description)

        self.osc.request(
            url=urljoin(
                self.osc.url,
                "/".join((self.base_path, project, package, "_meta"))
            ),
            data=tounicode(meta_xml),
            params={"comment": comment},
            method="PUT"
        )

    def get_files(self, project, package, **params):
        """
        List package files

        :param project: name of project
        :param package: name of package
        :param params: more optional parameters. See:
                       https://build.opensuse.org/apidocs/index#45
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        response = self.osc.request(
            url=urljoin(
                self.osc.url,
                "{}/{}/{}".format(self.base_path, project, package)
            ),
            method="GET",
            params=self.cleanup_params(**params)
        )

        return self.osc.get_objectified_xml(response)

    # pylint: disable=too-many-arguments
    def get_file(self, project, package, filename, meta=False, rev=None,
                 expand=False):
        """
        Get a source file

        Downloads a specific file from a package and returns a response object
        from which the file contents can be read.

        :param project: name of project
        :param package: name of package
        :param filename: name of file
        :param meta: switch to meta files
        :param rev: Get file from this specific package revision
        :param expand: If the package is linked, it typically only contains a
                       ``_link`` file. In order to allow retrieval of the linked
                       package instead of a 404 error, set this parameter to '1'
        :return: response
        :rtype: requests.Response

        .. versionadded:: 0.1.1
            Parameter rev

        .. versionadded:: 0.1.11
            Parameter expand
        """
        response = self.osc.request(
            url=urljoin(
                self.osc.url,
                "{}/{}/{}/{}".format(self.base_path, project, package, filename)
            ),
            method="GET",
            stream=True,
            params={'meta': meta, 'rev': rev, 'expand': expand}
        )

        return response

    # pylint: disable=too-many-arguments
    def download_file(self, project, package, filename, destdir, meta=False,
                      overwrite=False, rev=None, expand=False):
        """
        Download a file to directory

        :param project: name of project
        :param package: name of package
        :param filename: name of file
        :param destdir: path of directory
        :param meta: switch to meta files
        :param overwrite: switch to overwrite existing downloaded file
        :param rev: Download file from this specific package revision
        :param expand: If ``True`` and the package is a link, download the file from the linked
                       package
        :return: absolute path to file or ``None``
        :raises OSError: if something goes wrong

        .. versionadded:: 0.1.1
            Parameter rev

        .. versionchanged:: 0.3.3
            Added the parameter ``expand``

        .. versionchanged:: 0.7.0
            Moved some logic to :py:meth:`osctiny.osc.Osc.download`
        """
        return self.osc.download(
            url=urljoin(self.osc.url,
                        "{}/{}/{}/{}".format(self.base_path, project, package, filename)),
            destdir=destdir,
            destfile=filename,
            overwrite=overwrite,
            meta=meta,
            rev=rev,
            expand=expand
        )

    def push_file(self, project, package, filename, data, comment=None):
        """
        Upload a file to package

        :param project: Name of project
        :param package: Name of package
        :param filename: Name of file
        :param data: content of file
        :type data: str or open file handle
        :param comment: Optional comment to use as commit message

        .. versionchanged:: 0.5.0

           Added an optional ``comment`` argument to be used as the commit message when writing the
           file.
        """
        path = [self.base_path, project, package, filename]

        self.osc.request(
            url=urljoin(self.osc.url, "/".join(path)),
            method="PUT",
            data=data,
            params={"comment": comment}
        )

    def delete_file(self, project, package, filename, force=False, comment=None):
        """
        Delete package

        .. versionadded:: 0.10.3

        :param project: Project name
        :param package: Package name
        :param filename: Name of file
        :param force: Delete package even if pending requests exist
        :param comment: Optional comment
        :return: ``True``, if successful. Otherwise API response
        :rtype: bool or lxml.objectify.ObjectifiedElement
        """
        params = {'force': force}

        response = self.osc.request(
            url=urljoin(
                self.osc.url,
                "/".join((self.base_path, project, package, filename))
            ),
            method="DELETE",
            params=params,
            data=comment
        )

        parsed = self.osc.get_objectified_xml(response)
        if response.status_code == 200 and parsed.get("code") == "ok":
            return True

        return parsed

    def get_attribute(self, project, package, attribute=None):
        """
        Get one attribute of a package

        :param project: name of project
        :param package: name of package
        :param attribute: name of attribute
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        url = urljoin(
            self.osc.url,
            "{}/{}/{}/_attribute".format(
                self.base_path, project, package
            )
        )
        if attribute:
            url = "{}/{}".format(url, attribute)
        response = self.osc.request(
            url=url,
            method="GET"
        )

        return self.osc.get_objectified_xml(response)

    def get_history(self, project, package, limit = None):
        """
        Get history of package

        :param project: name of project
        :param package: name of package
        :param limit: Optional number of history entries to return. If
                      specified, only the last n entries are returned.
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        params = {"limit": limit} if limit else {}
        response = self.osc.request(
            url=urljoin(
                self.osc.url,
                "{}/{}/{}/_history".format(self.base_path, project, package)
            ),
            method="GET",
            params=params,
        )

        return self.osc.get_objectified_xml(response)

    def cmd(self, project, package, cmd, **params):
        """
        Get the result of the specified command

        Available commands:

        * diff: Shows the diff of all affected packages.
        * showlinked: List all package instances linking to this one.
        * instantiate: Instantiate a package container, which is available via
          project links only so far.
        * release: Releases sources and binaries of that package.
        * unlock: Unlocks a locked package.
        * branch: Create a source link from a package of an existing project.
        * set_flag: Modify or set a defined flag for package
        * createSpecFileTemplate: Create template for RPM SPEC file.
        * commit: Commits package changes to buildservice.
        * collectbuildenv: Creates _buildenv files based on origin package
          builds.
        * importchannel: Import a kiwi channel file for OBS.

        .. note:: Command ``diff``

            The ``diff`` command returns plain text, instead of XML, by default!
            To get XML, pass the ``view='xml'`` param.

        :param project: name of project
        :param package: name of package
        :param cmd: name of command
        :param params: More command specific parameters. See
                       https://build.opensuse.org/apidocs/index
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement or str
        """
        allowed = [
            'diff', 'showlinked', 'instantiate', 'release', 'unlock', 'branch',
            'set_flag', 'createSpecFileTemplate', 'commit', 'collectbuildenv',
            'importchannel'
        ]

        if cmd not in allowed:
            raise ValueError("Invalid command: '{}'. Use one of: {}".format(
                cmd, ", ".join(allowed)
            ))

        params["cmd"] = cmd
        response = self.osc.request(
            url=urljoin(
                self.osc.url,
                "{}/{}/{}".format(self.base_path, project, package)
            ),
            method="POST",
            params=params
        )

        if cmd != "diff" or params.get("view", None) == "xml":
            return self.osc.get_objectified_xml(response)

        return response.text

    def checkout(self, project, package, destdir, rev=None, meta=False, expand=False):
        """
        Checkout all files and directories of package

        :param project: name of project
        :param package: name of package
        :param destdir: target local directory
        :param rev: Package revision to check out
        :param meta: Checkout meta files instead
        :param expand: If ``True`` and the package is a link, download the file from the linked
                       package
        :return: nothing

        .. versionadded:: 0.1.1

        .. versionchanged:: 0.3.3
            Added the parameter ``expand``

        .. versionchanged:: 0.10.3
            The feature to create an ``osc`` compatible ``.osc/`` directory structure was removed.
        """
        if not os.path.exists(destdir):
            if not os.path.isdir(destdir):
                os.makedirs(destdir)
            else:
                raise TypeError("Destination {} is a file!".format(destdir))

        dirlist = self.get_files(project, package, rev=rev, meta=meta, expand=expand)
        for entry in dirlist.findall("entry"):
            self.download_file(
                project=project,
                package=package,
                filename=entry.get("name"),
                destdir=destdir,
                meta=meta,
                overwrite=True,
                rev=rev,
                expand=expand
            )

    def delete(self, project, package, force=False, comment=None):
        """
        Delete package

        .. versionadded:: 0.1.2

        :param project: Project name
        :param package: Package name
        :param force: Delete package even if pending requests exist
        :param comment: Optional comment
        :return: ``True``, if successful. Otherwise API response
        :rtype: bool or lxml.objectify.ObjectifiedElement
        """
        params = {'force': force}

        response = self.osc.request(
            url=urljoin(
                self.osc.url,
                "/".join((self.base_path, project, package))
            ),
            method="DELETE",
            params=params,
            data=comment
        )

        parsed = self.osc.get_objectified_xml(response)
        if response.status_code == 200 and parsed.get("code") == "ok":
            return True

        return parsed

    def exists(self, project, package, filename=None) -> bool:
        """
        Check whether package or file in package exists

        .. versionadded:: 0.1.2

        :param project: Project name
        :param package: Package name
        :param filename: Name of file
        :return: ``True``, if package exists, otherwise ``False``
        """
        path = [self.base_path, project, package]
        if filename:
            path.append(filename)
        response = self.osc.request(
            url=urljoin(
                self.osc.url,
                "/".join(path)
            ),
            method="HEAD",
            raise_for_status=False
        )

        if response.status_code == 404:
            return False

        # 404 is the only acceptable HTTP error code, otherwise raise an exception
        response.raise_for_status()

        return response.status_code == 200

    # pylint: disable=too-many-locals
    def aggregate(self, src_project, src_package, tgt_project, tgt_package,
                  publish=True, repo_map=None, no_sources=False):
        """
        Aggregate a package to another package

        .. versionadded:: 0.1.2

        .. versionchanged:: 0.2.5

            When creating a new aggregate package, the build flag is always enabled.

        :param src_project: Name of source project
        :param src_package: Name of source package
        :param tgt_project: Name of target project
        :param tgt_package: Name of target package
        :param publish: En-/Disable publishing of aggregated package
        :param repo_map: Optional repository mapping
        :type repo_map: None or dict
        :param no_sources: If ``True``, ignore source packages when copying
                           build results to destination project
        :return:
        """
        # Verify no-op
        if src_project == tgt_project and src_package == tgt_package:
            raise OscError("Source and Target are identical!")

        if not self.exists(src_project, src_package):
            raise OscError("Source package does not exist")

        # Check whether target package exists
        if not self.exists(tgt_project, tgt_package):
            meta_xml = self.get_meta(
                project=src_project,
                package=src_package
            )
            meta_xml.set("name", tgt_package)
            meta_xml.set("project", tgt_project)

            build_elem = meta_xml.find("build")
            if build_elem is None:
                build_elem = SubElement(meta_xml, "build")
            build_elem.clear()
            SubElement(build_elem, "enable")

            if not publish:
                pub_elem = meta_xml.find("publish")
                if not pub_elem:
                    pub_elem = SubElement(meta_xml, "publish")
                pub_elem.clear()
                SubElement(pub_elem, "disable")
            self.set_meta(
                project=tgt_project,
                package=tgt_package,
                meta=meta_xml
            )

        # We do not overwrite an existing aggregate
        if self.exists(tgt_project, tgt_package, "_aggregate"):
            raise OscError("Aggregate already exists.")

        repo_map = repo_map or {}

        # Generate aggregate
        agg_xml = Element("aggregatelist")
        agg = SubElement(agg_xml, "aggregate", project=src_project)
        pkg = SubElement(agg, "package")
        pkg.text = src_package

        if no_sources:
            SubElement(agg, "nosources")

        for src, tgt in repo_map.items():
            SubElement(agg, "repository", target=tgt, source=src)

        self.push_file(
            project=tgt_project,
            package=tgt_package,
            data=tounicode(agg_xml),
            filename="_aggregate"
        )

    def get_comments(self, project, package):
        """
        Get a list of comments for package

        .. versionadded:: 0.1.8
            Use internally :py:class:`osctiny.comments.Comment.get`

        :param project: name of project
        :param package: name of package
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        return self.osc.comments.get(
            obj_type="package",
            ids=(project, package)
        )

    def add_comment(self, project, package, comment, parent_id=None):
        """
        Add a comment to a package

        .. versionchanged:: 0.1.8
            Use internally :py:class:`osctiny.comments.Comment.add`

        :param project: name of project
        :param package: name of package
        :param comment: Comment to be added
        :param parent_id: ID of parent comment. Default: ``None``
        :return: ``True``, if successful. Otherwise API response
        :rtype: bool or lxml.objectify.ObjectifiedElement
        """
        return self.osc.comments.add(
            obj_type="package",
            ids=(project, package),
            comment=comment,
            parent_id=parent_id
        )
