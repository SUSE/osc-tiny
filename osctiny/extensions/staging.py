"""
Staging extension
-----------------

This extension provides access to the staging workflow of OpenBuildService.

.. seealso::

    https://openbuildservice.org/help/manuals/obs-user-guide/cha.obs.stagingworkflow

    https://openbuildservice.org/help/manuals/obs-user-guide/cha.obs.best-practices.webuiusage#staging_how_to

.. versionadded:: 0.9.0
"""
import typing
from urllib.parse import urljoin

from lxml.objectify import ObjectifiedElement, Element, SubElement

from ..models.staging import E, ExcludedRequest, CheckReport
from ..utils.base import ExtensionBase


class Staging(ExtensionBase):
    """
    Osc extension for interacting with staging workflows
    """
    base_path_staging = "/staging"
    base_path_status = "/status_reports"

    def get_backlog(self, project: str) -> ObjectifiedElement:
        """
        List the requests in the staging backlog

        :param project: Project name
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        response = self.osc.request(
            method="GET",
            url=urljoin(self.osc.url, "{}/{}/backlog".format(self.base_path_staging, project))
        )

        return self.osc.get_objectified_xml(response)

    def get_excluded_requests(self, project: str) -> ObjectifiedElement:
        """
        List the requests excluded from a staging workflow

        :param project: Project name
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        response = self.osc.request(
            method="GET",
            url=urljoin(self.osc.url, "{}/{}/excluded_requests".format(self.base_path_staging,
                                                                       project))
        )

        return self.osc.get_objectified_xml(response)

    def set_excluded_requests(self, project: str, *requests: ExcludedRequest) -> bool:
        """
        Exclude requests from the staging workflow.

        :param project: Project name
        :param requests: Requests to exclude with optional reason/description
        :return: ``True``, if successful.
        :raises HTTPError: if comment was not saved correctly. The raised exception contains the
                           full response object and API response.
        """
        response = self.osc.request(
            method="POST",
            url=urljoin(self.osc.url, "{}/{}/excluded_requests".format(self.base_path_staging,
                                                                       project)),
            data=E.excluded_requests(*(request.asxml() for request in requests))
        )
        parsed = self.osc.get_objectified_xml(response)
        if response.status_code == 200 and parsed.get("code") == "ok":
            return True

        return False

    def delete_excluded_requests(self, project: str, *requests: ExcludedRequest) -> bool:
        """
        Remove requests from list of excluded requests

        :param project: Project name
        :param requests: Requests to exclude with optional reason/description
        :return: ``True``, if successful.
        :raises HTTPError: if comment was not saved correctly. The raised exception contains the
                           full response object and API response.
        """
        response = self.osc.request(
            method="DELETE",
            url=urljoin(self.osc.url, "{}/{}/excluded_requests".format(self.base_path_staging,
                                                                       project)),
            data=E.excluded_requests(*(request.asxml() for request in requests))
        )
        parsed = self.osc.get_objectified_xml(response)
        if response.status_code == 200 and parsed.get("code") == "ok":
            return True

        return False

    def get_staging_projects(self, project: str) -> ObjectifiedElement:
        """
        List all the staging projects of a staging workflow.

        :param project: Project name
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        response = self.osc.request(
            method="GET",
            url=urljoin(self.osc.url,
                        "{}/{}/staging_projects".format(self.base_path_staging, project))
        )

        return self.osc.get_objectified_xml(response)

    # pylint: disable=too-many-arguments
    def get_status(self, project: str, staging_project: str, requests: bool = False,
                   status: bool = False, history: bool = False) -> ObjectifiedElement:
        """
        Get the overall state of a staging project

        :param project: Project name
        :param staging_project: Staging project name
        :param requests: Include statistics about staged, untracked and obsolete requests as well as
                         missing reviews
        :param status: Include the overall state
        :param history: Include the history of the staging project
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        response = self.osc.request(
            method="GET",
            url=urljoin(self.osc.url,
                        "{}/{}/staging_projects/{}".format(self.base_path_staging, project,
                                                           staging_project)),
            params={"requests": requests, "status": status, "history": history}
        )

        return self.osc.get_objectified_xml(response)

    def accept(self, project: str, staging_project: str) -> bool:
        """
        This accepts all staged requests and sets the project state back to 'empty'

        :param project: Project name
        :param staging_project: Staging project name
        :return: ``True``, if successful.
        :raises HTTPError: if comment was not saved correctly. The raised exception contains the
                           full response object and API response.
        """
        response = self.osc.request(
            method="POST",
            url=urljoin(self.osc.url, "{}/{}/staging_projects/{}/accept".format(
                self.base_path_staging, project, staging_project))
        )

        parsed = self.osc.get_objectified_xml(response)
        if response.status_code == 200 and parsed.get("code") == "ok":
            return True

        return False

    def get_staged_requests(self, project: str, staging_project: str) ->ObjectifiedElement:
        """
        List all the staged requests of a staging project

        :param project: Project name
        :param staging_project: Staging project name
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        response = self.osc.request(
            method="GET",
            url=urljoin(self.osc.url,
                        "{}/{}/staging_projects/{}/staged_requests".format(
                            self.base_path_staging, project, staging_project)),
        )

        return self.osc.get_objectified_xml(response)

    def add_staged_requests(self, project: str, staging_project: str, *request_ids: int) -> bool:
        """
        Add requests to the staging project.

        :param project: Project name
        :param staging_project: Staging project name
        :param request_ids: Request IDs
        :return: ``True``, if successful.
        :raises HTTPError: if comment was not saved correctly. The raised exception contains the
                           full response object and API response.
        """
        requests = Element("requests")
        for request_id in request_ids:
            SubElement(requests, "request", id=str(request_id))
        response = self.osc.request(
            method="POST",
            url=urljoin(self.osc.url, "{}/{}/staging_projects/{}/staged_requests".format(
                self.base_path_staging, project, staging_project)),
            data=requests
        )
        parsed = self.osc.get_objectified_xml(response)
        if response.status_code == 200 and parsed.get("code") == "ok":
            return True

        return False

    def delete_staged_requests(self, project: str, staging_project: str, *request_ids: int) -> bool:
        """
        Delete requests from the staging project

        :param project: Project name
        :param staging_project: Staging project name
        :param request_ids: Request IDs
        :return: ``True``, if successful.
        :raises HTTPError: if comment was not saved correctly. The raised exception contains the
                           full response object and API response.
        """
        requests = Element("requests")
        for request_id in request_ids:
            SubElement(requests, "request", id=str(request_id))
        response = self.osc.request(
            method="DELETE",
            url=urljoin(self.osc.url, "{}/{}/staging_projects/{}/staged_requests".format(
                self.base_path_staging, project, staging_project)),
            data=requests
        )
        parsed = self.osc.get_objectified_xml(response)
        if response.status_code == 200 and parsed.get("code") == "ok":
            return True

        return False

    def get_required_checks(self, project: str, repo: typing.Optional[str] = None,
                            arch: typing.Optional[str] = None) -> ObjectifiedElement:
        """
        Get list of required checks

        If `repo`` and ``arch`` are specified, required checks from the built repository are
        returned. If only ``repo`` is specified, required checks from the repository are
        returned. Otherwise, required checks from the project are returned

        :param project: (Staging) project name
        :param repo: Repository name (optional)
        :param arch: Architecture name (optional)
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        if repo and arch:
            url_path = "{}/built_repositories/{}/{}/{}/required_checks".format(
                self.base_path_status, project, repo, arch
            )
        elif repo:
            url_path = "{}/repositories/{}/{}/required_checks".format(
                self.base_path_status, project, repo
            )
        else:
            url_path = "{}/projects/{}/required_checks".format(self.base_path_status, project)

        response = self.osc.request(
            method="GET",
            url=urljoin(self.osc.url, url_path),
        )

        return self.osc.get_objectified_xml(response)

    def set_required_checks(self, project: str, checks: typing.List[str],
                            repo: typing.Optional[str] = None,
                            arch: typing.Optional[str] = None) -> bool:
        """
        Submit a new or modified required checks list

        If ``repo`` and ``arch`` are specified, required checks of built repository are
        updated. If only ``repo`` is specified, required checks of the repository are updated.
        Otherwise, required checks of the project are updated.

        :param project: (Staging) project name
        :param checks: List of check names
        :param repo: Repository name (optional)
        :param arch: Architecture name (optional)
        :return: ``True``, if successful.
        :raises HTTPError: if comment was not saved correctly. The raised exception contains the
                           full response object and API response.
        """
        kwargs = {"project": project}
        if repo and arch:
            url_path = "{}/built_repositories/{}/{}/{}/required_checks".format(
                self.base_path_status, project, repo, arch
            )
            kwargs.update({"repository": repo, "architecture": arch})
        elif repo:
            url_path = "{}/repositories/{}/{}/required_checks".format(
                self.base_path_status, project, repo
            )
            kwargs["repository"] = repo
        else:
            url_path = "{}/projects/{}/required_checks".format(self.base_path_status, project)

        response = self.osc.request(
            method="POST",
            url=urljoin(self.osc.url, url_path),
            data=E.required_checks(*(E.name(check) for check in checks))
        )
        parsed = self.osc.get_objectified_xml(response)
        if response.status_code == 200 and parsed.get("code") == "ok":
            return True

        return False

    def get_status_report(self, project: str, repo: str, build_id: str,
                          arch: typing.Optional[str] = None) -> ObjectifiedElement:
        """
        Get list of checks

        If ``arch`` is specified, status report for built project is retrieved. Otherwise, status
        report for published project is retrieved.

        :param project: (Staging) project name
        :param repo: Repository name
        :param build_id: Build ID (Can be obtained via
                         :py:meth:`osctiny.extensions.buildresults.Build.get_status_and_build_id`)
        :param arch: Architecture name
        :return: Objectified XML element
        :rtype: lxml.objectify.ObjectifiedElement
        """
        if arch:
            url_path = "{}/built/{}/{}/{}/reports/{}".format(
                self.base_path_status, project, repo, arch, build_id
            )
        else:
            url_path = "{}/published/{}/{}/reports/{}".format(
                self.base_path_status, project, repo, build_id
            )

        response = self.osc.request(
            method="GET",
            url=urljoin(self.osc.url, url_path)
        )

        return self.osc.get_objectified_xml(response)

    def set_status_report(self, project: str, repo: str, build_id: str, report: CheckReport,
                          arch: typing.Optional[str] = None) -> bool:
        """
        Submit a check to a status report

        If ``arch`` is specified, the status report for built project is set. Otherwise, the status
        report for published project is set.

        :param project: (Staging) project name
        :param repo: Repository name
        :param build_id: Build ID (Can be obtained via
                         :py:meth:`osctiny.extensions.buildresults.Build.get_status_and_build_id`)
        :param report: The status upate
        :param arch: Architecture name
        :return: ``True``, if successful.
        :raises HTTPError: if comment was not saved correctly. The raised exception contains the
                           full response object and API response.
        """
        if arch:
            url_path = "{}/built/{}/{}/{}/reports/{}".format(
                self.base_path_status, project, repo, arch, build_id
            )
        else:
            url_path = "{}/published/{}/{}/reports/{}".format(
                self.base_path_status, project, repo, build_id
            )

        response = self.osc.request(
            method="POST",
            url=urljoin(self.osc.url, url_path),
            data=report.asxml()
        )

        if response.status_code == 200:
            return True

        return False
