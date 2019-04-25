# pylint: disable=missing-docstring,too-few-public-methods,
import os

from lxml.etree import tounicode


class ExtensionBase:
    """
    Base class for extensions of the :py:class:`Ocs` entry point.
    """
    def __init__(self, osc_obj):
        self.osc = osc_obj


# pylint: disable=too-many-instance-attributes
class DataDir:
    """
    Compatibility layer for the ``.osc`` data directory used by the ``osc`` CLI
    """
    data_dir = ".osc"
    osclib_version_string = "1.0"

    # pylint: disable=too-many-arguments
    def __init__(self, osc, path, project, package=None, overwrite=False):
        self.osc = osc
        self.path = os.path.join(path, self.data_dir)
        self.project = project
        self.package = package
        self._apiurl = os.path.join(self.path, "_apiurl")
        self._project = os.path.join(self.path, "_project")
        self._package = os.path.join(self.path, "_package")
        self._files = os.path.join(self.path, "_files")
        self._osclib_version = os.path.join(self.path, "_osclib_version")
        if not os.path.isdir(self.path):
            os.makedirs(self.path)
            overwrite = True

        if overwrite:
            self.write_dir_contents()

    def write_dir_contents(self):
        with open(self._apiurl, "w") as filehandle:
            filehandle.write(self.osc.url + os.linesep)

        with open(self._osclib_version, "w") as filehandle:
            filehandle.write(self.osclib_version_string + os.linesep)

        with open(self._project, "w") as filehandle:
            filehandle.write(self.project + os.linesep)

        if self.package:
            with open(self._package, "w") as filehandle:
                filehandle.write(self.package + os.linesep)

            with open(self._files, "w") as filehandle:
                filehandle.write(
                    tounicode(self.osc.packages.get_files(self.project,
                                                          self.package))
                )
