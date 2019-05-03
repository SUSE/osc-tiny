"""
Packages extension
------------------
"""
import errno
import os
from urllib.parse import urljoin

from lxml.etree import tounicode, SubElement, Element
from lxml.objectify import fromstring

from .base import ExtensionBase, DataDir
from .errors import OscError


class Package(ExtensionBase):
    """
    Osc extension to interact with packages
    """
    base_path = "/source"
    new_package_meta_templ = "<package><title/><description/></package>"

    def get_list(self, project):
        """
        Get packages from project

        :param project: name of project
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        response = self.osc.request(
            url=urljoin(self.osc.url, "{}/{}".format(self.base_path, project)),
            method="GET"
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
            data=params
        )

        if blame:
            return response.text

        return self.osc.get_objectified_xml(response)

    # pylint: disable=too-many-arguments,protected-access
    def set_meta(self, project, package, title=None, description=None,
                 meta=None):
        """
        Set package metadata

        .. note:: By setting the meta data ``package`` is created, if it does
                  not exist.

        Specify ``title`` and ``description`` to create an XML file with minimum
        content or provide a complete XML string via ``meta``.

        .. note:: If ``title`` or ``description`` is given in combination with
                  ``meta``, the existing values in ``meta`` will be overwritten.

        .. versionadded:: 0.1.2

        :param project: Project name
        :param package: New package name
        :param title: Title for meta
        :param description: Description for meta
        :param meta: New content for meta
        :type meta: str or lxml.objectify.ObjectifiedElement
        :return:
        """
        if isinstance(meta, str):
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
            data=params
        )

        return self.osc.get_objectified_xml(response)

    # pylint: disable=too-many-arguments
    def get_file(self, project, package, filename, meta=False, rev=None):
        """
        Get a source file

        Downloads a specific file from a package and returns a response object
        from which the file contents can be read.

        :param project: name of project
        :param package: name of package
        :param filename: name of file
        :param meta: switch to meta files
        :param rev: Get file from this specific package revision
        :return: response
        :rtype: requests.Response

        .. versionadded:: 0.1.1
            Parameter rev
        """
        response = self.osc.request(
            url=urljoin(
                self.osc.url,
                "{}/{}/{}/{}".format(self.base_path, project, package, filename)
            ),
            method="GET",
            stream=True,
            data={'meta': meta, 'rev': rev}
        )

        return response

    # pylint: disable=too-many-arguments
    def download_file(self, project, package, filename, destdir, meta=False,
                      overwrite=False, rev=None):
        """
        Download a file to directory

        :param project: name of project
        :param package: name of package
        :param filename: name of file
        :param destdir: path of directory
        :param meta: switch to meta files
        :param overwrite: switch to overwrite existing downloaded file
        :param rev: Download file from this specific package revision
        :return: absolute path to file or ``None``
        :raises OSError: if something goes wrong

        .. versionadded:: 0.1.1
            Parameter rev
        """
        abspath_filename = os.path.abspath(os.path.join(destdir, filename))
        if os.path.isfile(destdir):
            raise OSError(
                errno.EEXIST, "Target directory is a file", destdir
            )
        if not overwrite and os.path.exists(abspath_filename):
            raise OSError(
                errno.EEXIST, "File already exists", abspath_filename
            )
        if not os.path.exists(destdir):
            os.makedirs(destdir)

        response = self.get_file(project, package, filename, meta=meta, rev=rev)

        with open(abspath_filename, "wb") as handle:
            for chunk in response.iter_content(1024):
                handle.write(chunk)

        return abspath_filename

    def push_file(self, project, package, filename, data):
        """
        Upload a file to package

        :param project: Name of project
        :param package: Name of package
        :param filename: Name of file
        :param data: content of file
        :type data: str or open file handle
        """
        path = [self.base_path, project, package, filename]

        self.osc.request(
            url=urljoin(self.osc.url, "/".join(path)),
            method="PUT",
            data=data
        )

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

    def get_history(self, project, package):
        """
        Get history of package

        :param project: name of project
        :param package: name of package
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        response = self.osc.request(
            url=urljoin(
                self.osc.url,
                "{}/{}/{}/_history".format(self.base_path, project, package)
            ),
            method="GET"
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

            The ``diff`` command returns plain text instaed of XML!

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
            data=params
        )

        if cmd != "diff" or params.get("view", None) == "xml":
            return self.osc.get_objectified_xml(response)

        return response.text

    def checkout(self, project, package, destdir, rev=None, meta=False):
        """
        Checkout all files and directories of package

        .. note:: Only by using :py:meth:`checkout` the directory structure is
                  compatible with the ``osc`` command line tool!

        :param project: name of project
        :param package: name of package
        :param destdir: target local directory
        :param rev: Package revision to check out
        :param meta: Checkout meta files instead
        :return: nothing

        .. versionadded:: 0.1.1
        """
        if not os.path.exists(destdir):
            if not os.path.isdir(destdir):
                os.makedirs(destdir)
            else:
                raise TypeError("Destination {} is a file!".format(destdir))

        oscdir = DataDir(osc=self.osc, path=destdir, project=project,
                         package=package)

        dirlist = self.get_files(project, package, rev=rev, meta=meta)
        for entry in dirlist.findall("entry"):
            self.download_file(
                project=project,
                package=package,
                filename=entry.get("name"),
                destdir=destdir,
                meta=meta,
                overwrite=True,
                rev=rev
            )
            os.link(
                os.path.join(destdir, entry.get("name")),
                os.path.join(oscdir.path, entry.get("name"))
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
        params = {'force': force, 'comment': comment}

        response = self.osc.request(
            url=urljoin(
                self.osc.url,
                "/".join((self.base_path, project, package))
            ),
            method="DELETE",
            data=params
        )

        parsed = self.osc.get_objectified_xml(response)
        if response.status_code == 200 and parsed.get("code") == "ok":
            return True

        return parsed

    def exists(self, project, package, filename=None):
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

        return response.status_code == 200

    # pylint: disable=too-many-locals
    def aggregate(self, src_project, src_package, tgt_project, tgt_package,
                  publish=True, repo_map=None, no_sources=False):
        """
        Aggregate a package to another package

        .. versionadded:: 0.1.2

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
