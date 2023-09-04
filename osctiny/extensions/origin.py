"""
Origin extension
----------------

This is a runtime optimized implementation of the `Origin Manager`_.

The intention of this implementation is to quickly yield batch results. In doing so a different
logic than in the original OSC plugin is used:

* If a project inherits a package from another project, the origin is checked for the package in the
  original project.
* If the package has received submissions from potential origin projects, only those projects are
  considered.
* The first project from the origin configuration (including above limitations) containing the
  package is considered as origin project.
* If a project was found and if that project inherits the package, the original project is returned.

.. _Origin Manager:
    https://github.com/openSUSE/openSUSE-release-tools/blob/master/docs/origin-manager.md

.. versionadded:: 0.3.0
"""
# pylint: disable=too-many-ancestors,ungrouped-imports
from collections import defaultdict
from functools import lru_cache
import re
from warnings import warn

from yaml import load

from ..utils.backports import cached_property
from ..utils.base import ExtensionBase
from ..utils.mapping import LazyOscMappable

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    # If libyaml installed, we should fall back to the SafeLoader
    from yaml import SafeLoader


class DevelProjects(LazyOscMappable):
    """
    Lazy lookup table for package specific development projects
    """

    def get_devel_projects(self, *projects):
        """
        Find package specific development projects for (maintained) projects

        :param str projects: One or more project names
        :return: Dictionary with development projects per package
        :rtype: dict
        """
        xpath = "state/@name='accepted' and action/@type='change_devel' and ({projects})"
        xpath_projects = ["action/target/@project='{}'".format(project) for project in projects]
        change_devels = self.osc.search.request(
            xpath=xpath.format(projects=" or ".join(xpath_projects))
        )

        data = {}
        for request in sorted(getattr(change_devels, "request", []),
                              key=lambda x: x.state.get("when"), reverse=True):
            key = (request.action.target.get("project"), request.action.target.get("package"))
            if key not in data:
                data[key] = request.action.source.get("project")
                break

        return data

    def __missing__(self, key):
        """
        JIT processing of missing dictionary items

        This method respects the default behavior of dictionary classes.
        """
        self._data[key] = self.get_devel_projects(key)


class PackageMatrix(LazyOscMappable):
    """
    Lazy lookup matrix for package origins

    This matrix collects for every project (provided as key) a dictionary with all allowed origin
    projects and packages therein. If the origin project inherits the package from another project,
    this information is available, too.

    The matrix is not populated at initialization time. When the matrix for a project is requested
    for the first, only the corresponding items are populated. Subsequent access to the same project
    does not trigger new population. Hence "lazy".

    Example:

    .. code-block:: python

        {
            'openSUSE:Leap:15.2:Update': {
                'SUSE:SLE-15-SP2:Update': {
                    # ...
                    'zeromq': ['SUSE:SLE-15:Update'],
                    'zypper': ['SUSE:SLE-15-SP2:Update', 'SUSE:SLE-15-SP2:GA']
                },
                'SUSE:SLE-15-SP1:Update': {
                    'zinnia-tomoe': ['SUSE:SLE-15:GA']
                    # ...
                },
                'openSUSE:Factory': {
                    # ...
                    'zziplib': ['openSUSE:Factory']
                }
            },
            'openSUSE:Leap:15.2': ...
        }

    :param osc_obj: An Osc instance to run queries
    :type osc_obj: :py:class:`osctiny.osc.Osc`
    :param expanded_origins: Lookup dictionary with all possible origin projects
    :type expanded_origins: :py:meth:`Origin.expanded_origins`
    """
    def __init__(self, osc_obj, expanded_origins, **kwargs):
        super().__init__(osc_obj=osc_obj, **kwargs)
        self._expanded_origins = expanded_origins

    def __missing__(self, key):
        """
        JIT processing of missing matrix items

        This method respects the default behavior of dictionary classes.
        """
        def _inherit(proj, o_proj):
            if proj == o_proj:
                return [proj]
            return [proj, o_proj]

        if key in self._expanded_origins:
            self._data[key] = {
                origin_project: {
                    entry.get("name"): _inherit(origin_project, entry.get("originproject"))
                    for entry in getattr(self.osc.projects.get_files(project=origin_project,
                                                                     expand='1'), "entry", [])
                }
                for origin_project in self._expanded_origins[key]
                if origin_project not in ["<devel>", "*", "*~"]
            }
            return
        raise KeyError("'{}' is not an origin project".format(key))


class Origin(ExtensionBase):
    """
    Query tool to find the origin of packages in maintained projects

    .. versionadded:: 0.3.0
    """
    _origin_priority_pattern = re.compile(
        r"^(?P<family>SUSE:[^:-]+|openSUSE:[^:]+)[:-]"
        r"(?P<major>\d+)((\.|-SP)(?P<minor>\d+))?"
        r"(:(?P<tail>.+))?$"
    )

    def __init__(self, osc_obj):
        super().__init__(osc_obj)
        self._devel_projects = None
        self._package_matrix = None

    def family_sort_key(self, key):
        """
        Provides a numeric key for sorting projects of the same family

        :param str key: Project name
        :return: Numeric value representing the version and priority of projects
        :rtype: float
        """
        if isinstance(key, int):
            return key
        if not isinstance(key, str):
            return -1

        match = self._origin_priority_pattern.match(key)
        if not match:
            return 0

        tail_mod = 0.
        if match.group("tail"):
            parts = match.group("tail").split(":")
            if "Update" in parts:
                tail_mod += .0005
            if "workarounds" in parts:
                tail_mod += .0006
            if len(parts) > 1:
                tail_mod += .0001

        value = float(match.group("major") or 0) + .01*float(match.group("minor") or 0) + tail_mod
        return value

    def family_sorter(self, unsorted_list):
        """
        Sort consecutive projects of the same family

        In case the configuration does not list the projects in a meaningful way, they are
        sorted now to avoid the need to check the package histories for every package.

        .. note::

            This sorter is only allowed to change the order of consecutive projects belonging to the
            same family.

            Consider this a workaround for
            `this issue <https://github.com/openSUSE/openSUSE-release-tools/issues/2506>`_.

        :param unsorted_list: List with project names
        :type unsorted_list: list of str
        :return: Generator with sorted list items
        :rtype: generator
        """
        i = 0
        while i < len(unsorted_list):
            match = self._origin_priority_pattern.match(unsorted_list[i])
            if not match:
                yield unsorted_list[i]
                i += 1
                continue

            end_index = -1
            for j in range(i+1, len(unsorted_list)):
                match2 = self._origin_priority_pattern.match(unsorted_list[j])
                if not match2:
                    break
                if match2.group("family") != match.group("family"):
                    break
                end_index = j
            if end_index > i:
                yield from sorted(unsorted_list[i:end_index+1], key=self.family_sort_key,
                                  reverse=True)
                i = end_index+1
            else:
                yield unsorted_list[i]
                i += 1

    @property
    def devel_projects(self):
        """
        Delayed initialization of the package specific development project dictionary

        This dictionary is populated in a lazy/JIT fashion.

        :return: :py:class:`DevelProjects`
        """
        if self._devel_projects is None:
            self._devel_projects = DevelProjects(osc_obj=self.osc)
        return self._devel_projects

    @property
    def package_matrix(self):
        """
        Delayed initialization of the lookup package matrix.

        The matrix is populated in a lazy/JIT fashion.

        :return: :py:class:`PackageMatrix`
        """
        if self._package_matrix is None:
            self._package_matrix = PackageMatrix(osc_obj=self.osc,
                                                 expanded_origins=self.expanded_origins)
        return self._package_matrix

    @cached_property
    def maintenance_project(self):
        """
        Get the maintenance project

        This project is important, because it's meta can provide the list of maintained projects.

        :return: Project name or ``None``
        :rtype: str or None

        .. versionchanged:: 0.4.0

            Return string instead of XML object
        """
        response = self.osc.search.search(path="project/id",
                                          xpath="attribute/@name='OBS:MaintenanceProject'")
        projects = getattr(response, "project", [])
        if len(projects) < 1:
            warn("The build service defines no maintenance projects!")
            return None
        if len(projects) > 1:
            warn("The build service defines multiple maintenance projects!")

        return projects[0].get("name")

    @cached_property
    def maintained_projects(self):
        """
        Get the list of maintained projects

        Maintained projects are identified by the presence of the ``OBS:Maintained`` attribute.

        :return: Project names
        :rtype: List of str

        .. versionchanged:: 0.4.0

            Search maintained projects via the ``OBS:Maintained`` attribute and not via the
            maintenance project.
        """
        response = self.osc.search.search(path="project/id",
                                          xpath="attribute/@name='OBS:Maintained'")
        return [project.get("name") for project in getattr(response, "project", [])]

    @lru_cache(maxsize=16)
    def get_project_origin_config(self, project):
        """
        Get the Origin configuration for ``project``

        This method returns the decoded YAML data, e.g. for "openSUSE:Leap:15.2:Update":

        .. code-block:: json

            {
              "origins": [
                {
                  "<devel>": {}
                },
                {
                  "SUSE:SLE-15:Update": {
                    "maintainer_review_initial": false
                  }
                },
                {
                  "SUSE:SLE-15-SP1:Update": {
                    "maintainer_review_initial": false
                  }
                },
                {
                  "SUSE:SLE-15-SP2:Update": {
                    "maintainer_review_initial": false
                  }
                },
                {
                  "openSUSE:Leap:15.1:Update": {
                    "pending_submission_allow": true
                  }
                },
                {
                  "openSUSE:Factory": {
                    "pending_submission_allow": true
                  }
                },
                {
                  "*~": {}
                }
              ],
              "fallback-group": "origin-reviewers-maintenance"
            }

        :param name project: The project name
        :return: Configuration content
        :rtype: dict
        """
        encoded_attrib = self.osc.projects.get_attribute(project=project,
                                                         attribute="OSRT:OriginConfig")

        return load(encoded_attrib.attribute.value.text, Loader=SafeLoader)

    @cached_property
    def expanded_origins(self):
        """
        Expand the projects from the Origin Configuration

        This property returns all the expanded origin projects for all projects that have the
        ``OSRT:OriginConfig`` attribute set in build service.

        .. note::

            Even if ``OSRT:OriginConfig`` explicitly defines a bogus order of projects, e.g.

            * ``SUSE:SLE-15:Update``
            * ``SUSE:SLE-15-SP1:Update``
            * ``SUSE:SLE-15-SP2:Update``

            this method will rearrange the projects in a meaningful way, e.g. into:

            * ``SUSE:SLE-15-SP2:Update``
            * ``SUSE:SLE-15-SP1:Update``
            * ``SUSE:SLE-15:Update``

            Consider this a workaround for
            `this issue <https://github.com/openSUSE/openSUSE-release-tools/issues/2506>`_.

        :return: Dictionary with lists of origin project names for all projects
        :rtype: dict
        """
        expanded = defaultdict(list)
        projects = [project.get("name")
                    for project in getattr(self.osc.search.search(
                        path="project/id", xpath="attribute/@name='OSRT:OriginConfig'"
                    ), "project", [])]

        for configured_project in projects:
            max_version = self.family_sort_key(configured_project)
            for origin in self.get_project_origin_config(configured_project).get("origins"):
                for _origin in origin:
                    _origin = _origin.rstrip("~")
                    if "*" not in _origin:
                        # no family expansion
                        expanded[configured_project].append(_origin)
                        continue

                    # family expansion
                    parts = _origin.rsplit("*", 1)
                    if parts[0] in ['', "*"]:
                        continue

                    xpath = "starts-with(@name, '{}')".format(parts[0])
                    if parts[1] != "":
                        xpath += " and contains(@name, ':{}')".format(parts[1])

                    family = [proj.get("name")
                              for proj in getattr(self.osc.search.search("project/id", xpath=xpath),
                                                  "project", [])]

                    family.sort(key=self.family_sort_key, reverse=True)
                    expanded[configured_project] += [f
                                                     for f in family
                                                     if self.family_sort_key(f) <= max_version]
            # Note: The order of origins in the config might be not the intended one. Se we sort
            # them the right way.
            expanded[configured_project] = list(self.family_sorter(expanded[configured_project]))

        return expanded

    @lru_cache(maxsize=256)
    def is_linked(self, package, project):
        """
        Guess whether a package is a link source (with incident number as suffix).

        :param package: Package name to check
        :param project: Project name containing the package
        :return: ``True``, if package name seems to have an incident ID as suffix
        """
        without_suffix = re.sub(r"\.\d+$", "", package)
        if without_suffix == package:
            return False

        package_list = {key for pkg in self.package_matrix[project].values() for key in pkg if pkg}
        if without_suffix in package_list:
            return True

        return False

    def get_origin_from_submissions(self, package, project):
        """
        Get potential origin projects from accepted submissions (aka. requests)

        This method returns the source project names from accepted requests.

        :param str package: Target package name
        :param str project: Target project name
        :return: Set of source project names
        :rtype: set or str
        """
        xpath = "action/target/@project='{project}' and action/target/@package='{package}' " \
                "and state/@name='accepted'"
        response = self.osc.search.request(xpath=xpath.format(project=project, package=package))
        sources = response.xpath("request/action/source")
        return {s.get("project") for s in sources}

    def find_package_origin(self, package, project, resolve_inheritance=True):
        """
        Find the origin project for ``package`` in ``project``

        This method will return simply ``None`` for patchinfo packages and packages with an incident
        ID as suffix.

        .. important::

            When you want to check multiple packages by multiple calls to this method, you should
            resolve from where ``project`` inherits the package for all your (package, project)
            pairs in advance and set ``resolve_inheritance`` to ``False`` to speed up the response
            time.

        :param str package: Package name
        :param str project: Project name
        :param bool resolve_inheritance: Trigger to cause this method to replace ``project`` with
                                         the project from which ``package`` is inherited from
        :return: Origin project name or ``None``
        :rtype: str
        """
        if package.startswith("patchinfo") or self.is_linked(package, project):
            # We do not care about patchinfo packages nor packages with incident ID suffixes
            return None

        if resolve_inheritance:
            response = self.osc.packages.get_files(package=package, project=project,
                                                   withlinked=True)
            links = response.xpath("linkinfo/linked")
            if len(links) > 0:
                project = links[-1].get("project")

        if "<devel>" in self.expanded_origins[project] \
                and (project, package) in self.devel_projects[project]:
            return self.devel_projects[project][(project, package)]

        request_origins = self.get_origin_from_submissions(package=package, project=project) \
                          & set(self.expanded_origins[project])
        for candidate in self.expanded_origins[project]:
            if candidate in ["<devel>", "*", "*~"]:
                continue

            matrix = self.package_matrix[project][candidate]
            if package in matrix:
                origin_projects = matrix[package]
                # If the apparent origin project inherits the package, we consider the project from
                # which the package is inherited to be the correct answer.
                for proj in origin_projects[::-1]:
                    if not request_origins or proj in request_origins:
                        return origin_projects[-1]

        return None

    def list(self, project):
        """
        List all packages in a maintained project and their origin projects

        :param str project: Project name
        :return: Generator of pairs: ('pkg', 'origin')
        :rtype: generator
        """
        if project not in self.expanded_origins:
            warn("Project {} has no origin definition".format(project))
            return

        packages = self.osc.projects.get_files(project, expand=True)

        for package in getattr(packages, "entry", []):
            name = package.get("name")
            oproject = package.get("originproject")
            if name.startswith("patchinfo") or self.is_linked(name, oproject):
                # We do not care about patchinfo packages nor packages with incident ID suffixes
                continue
            yield name, self.find_package_origin(package=name, project=oproject,
                                                 resolve_inheritance=False)
