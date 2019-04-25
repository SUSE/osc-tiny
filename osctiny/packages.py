"""
Packages extension
------------------
"""
import errno
import os
from urllib.parse import urljoin

from .base import ExtensionBase, DataDir


class Package(ExtensionBase):
    """
    Osc extension to interact with packages
    """
    base_path = "/source"

    def get_list(self, project):
        """
        Get packages from project

        :param project: name of project
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        response = self.osc.request(
            url=urljoin(self.osc.url, self.base_path + project),
            method="GET"
        )

        return self.osc.get_objectified_xml(response)

    def get_meta(self, project, package):
        """
        Get package metadata

        :param project: name of project
        :param package: name of package
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        response = self.osc.request(
            url=urljoin(
                self.osc.url,
                "{}/{}/{}/_meta".format(self.base_path, project, package)
            ),
            method="GET"
        )

        return self.osc.get_objectified_xml(response)

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
