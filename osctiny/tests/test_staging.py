import re

from lxml import etree
import responses

from osctiny.models.staging import ExcludedRequest, CheckState, CheckReport

from .base import OscTest


class StagingTest(OscTest):
    @staticmethod
    def _mock_generic_request():
        responses.add(method=responses.GET,
                      url=re.compile("http://api.example.com/(staging|status_reports)/.*"),
                      body="<dummy><foo/><bar>Hello World</bar></dummy>",
                      status=200)

    @responses.activate
    def test_get_backlog(self):
        self._mock_generic_request()
        response = self.osc.staging.get_backlog("Dummy:Project")
        self.assertEqual(response.tag, "dummy")

    @responses.activate
    def test_get_excluded_requests(self):
        self._mock_generic_request()
        response = self.osc.staging.get_excluded_requests("Dummy:Project")
        self.assertEqual(response.tag, "dummy")

    @responses.activate
    def test_set_excluded_requests(self):
        def callback(request):
            element = self.osc.get_objectified_xml(response=request.body)
            self.assertEqual(element.request[0].get("id"), '1')
            self.assertEqual(element.request[0].get("description"), "Foo Bar")
            self.assertEqual(element.request[1].get("id"), '2')
            self.assertEqual(element.request[1].get("description"), "Hello World")
            self.assertEqual(element.request[2].get("id"), '3')
            return 200, {}, "<status code=\"ok\"/>"

        self.mock_request(
            method="POST",
            url="http://api.example.com/staging/Dummy:Project/excluded_requests",
            callback=callback
        )

        result = self.osc.staging.set_excluded_requests("Dummy:Project",
                                                        ExcludedRequest(1, "Foo Bar"),
                                                        ExcludedRequest(2, "Hello World"),
                                                        ExcludedRequest(3))
        self.assertTrue(result)

    @responses.activate
    def test_delete_excluded_requests(self):
        def callback(request):
            element = self.osc.get_objectified_xml(response=request.body)
            self.assertEqual(element.request[0].get("id"), '1')
            return 200, {}, "<status code=\"ok\"/>"

        self.mock_request(
            method="DELETE",
            url="http://api.example.com/staging/Dummy:Project/excluded_requests",
            callback=callback
        )

        result = self.osc.staging.delete_excluded_requests("Dummy:Project", ExcludedRequest(1))
        self.assertTrue(result)

    @responses.activate
    def test_get_staging_projects(self):
        self._mock_generic_request()
        response = self.osc.staging.get_staging_projects("Dummy:Project")
        self.assertEqual(response.tag, "dummy")

    @responses.activate
    def test_get_status(self):
        self._mock_generic_request()
        response = self.osc.staging.get_status("Dummy:Project", "Dummy:Project:Staging:A")
        self.assertEqual(response.tag, "dummy")

    @responses.activate
    def test_accept(self):
        responses.add(method="POST",
                      url="http://api.example.com/staging/Dummy:Project/staging_projects/Dummy:Project:Staging:A/accept",
                      status=200,
                      body="<status code=\"ok\"/>")
        self.assertTrue(self.osc.staging.accept("Dummy:Project", "Dummy:Project:Staging:A"))

    @responses.activate
    def test_get_staged_requests(self):
        self._mock_generic_request()
        response = self.osc.staging.get_staged_requests("Dummy:Project", "Dummy:Project:Staging:A")
        self.assertEqual(response.tag, "dummy")

    @responses.activate
    def test_add_staged_requests(self):
        def callback(request):
            element = self.osc.get_objectified_xml(request.body)
            self.assertEqual(3, len(element.request))
            self.assertEqual(["1", "2", "3"], [elem.get("id") for elem in element.request])
            return 200, {}, "<status code=\"ok\"/>"

        responses.add_callback(method="POST",
                               url="http://api.example.com/staging/Dummy:Project/staging_projects/Dummy:Project:Staging:A/staged_requests",
                               callback=callback)
        result = self.osc.staging.add_staged_requests("Dummy:Project", "Dummy:Project:Staging:A",
                                                      1, 2, 3)
        self.assertTrue(result)

    @responses.activate
    def test_delete_staged_requests(self):
        def callback(request):
            element = self.osc.get_objectified_xml(request.body)
            self.assertEqual(3, len(element.request))
            self.assertEqual(["1", "2", "3"], [elem.get("id") for elem in element.request])
            return 200, {}, "<status code=\"ok\"/>"

        responses.add_callback(method="DELETE",
                               url="http://api.example.com/staging/Dummy:Project/staging_projects/Dummy:Project:Staging:A/staged_requests",
                               callback=callback)
        result = self.osc.staging.delete_staged_requests("Dummy:Project", "Dummy:Project:Staging:A",
                                                         1, 2, 3)
        self.assertTrue(result)

    @responses.activate
    def test_get_required_checks(self):
        responses.add(
            method="GET",
            url="http://api.example.com/status_reports/built_repositories/Dummy:Project/repo/x86_64/required_checks",
            body="<dummyrepoarch/>",
            status=200
        )
        responses.add(
            method="GET",
            url="http://api.example.com/status_reports/repositories/Dummy:Project/repo/required_checks",
            body="<dummyrepo/>",
            status=200
        )
        responses.add(
            method="GET",
            url="http://api.example.com/status_reports/projects/Dummy:Project/required_checks",
            body="<dummyproject/>",
            status=200
        )

        with self.subTest("Repo + Arch"):
            response = self.osc.staging.get_required_checks("Dummy:Project", "repo", "x86_64")
            self.assertEqual(response.tag, "dummyrepoarch")

        with self.subTest("Repo"):
            response = self.osc.staging.get_required_checks("Dummy:Project", "repo")
            self.assertEqual(response.tag, "dummyrepo")

        with self.subTest("Project"):
            response = self.osc.staging.get_required_checks("Dummy:Project")
            self.assertEqual(response.tag, "dummyproject")

    @responses.activate
    def test_set_required_checks(self):
        def callback(request):
            elem = self.osc.get_objectified_xml(request.body)

            if "/projects/" in request.url:
                self.assertTrue(all("project" in child.text for child in elem.name))
            if "/repositories/" in request.url:
                self.assertTrue(all("repo" in child.text for child in elem.name))
            if "/built_repositories/" in request.url:
                self.assertTrue(all("built" in child.text for child in elem.name))

            return 200, {}, "<status code=\"ok\"/>"

        responses.add_callback(
            method="POST",
            url=re.compile("http://api.example.com/status_reports/(projects|repositories|built_repositories)/.*"),
            callback=callback
        )

        with self.subTest("Repo + Arch"):
            result = self.osc.staging.set_required_checks(
                "Dummy:Project", [f"built-{i}" for i in range(1, 3)], "repo", "x86_64"
            )
            self.assertTrue(result)

        with self.subTest("Repo"):
            result = self.osc.staging.set_required_checks(
                "Dummy:Project", [f"repo-{i}" for i in range(1, 3)], "repo"
            )
            self.assertTrue(result)

        with self.subTest("Project"):
            result = self.osc.staging.set_required_checks(
                "Dummy:Project", [f"project-{i}" for i in range(1, 3)]
            )
            self.assertTrue(result)

    @responses.activate
    def test_get_status_report(self):
        responses.add(
            method="GET",
            url="http://api.example.com/status_reports/built/Dummy:Project/repo/x86_64/reports/1",
            body="<dummyarch/>",
            status=200
        )
        responses.add(
            method="GET",
            url="http://api.example.com/status_reports/published/Dummy:Project/repo/reports/1",
            body="<dummyrepo/>",
            status=200
        )

        with self.subTest("Repo + Arch"):
            response = self.osc.staging.get_status_report("Dummy:Project", "repo", "1", "x86_64")
            self.assertEqual(response.tag, "dummyarch")

        with self.subTest("Repo"):
            response = self.osc.staging.get_status_report("Dummy:Project", "repo", "1")
            self.assertEqual(response.tag, "dummyrepo")

    @responses.activate
    def test_set_status_report(self):
        report = CheckReport(
            name="dummy-check",
            required=False,
            state=CheckState.FAILURE,
            short_description="Lorem ipsum dolor sit",
            url="http://example.com/lorem-ipsum"
        )

        def callback(request):
            elem = self.osc.get_objectified_xml(request.body)
            self.assertEqual(report.name, elem.get("name"))
            self.assertEqual("false", elem.get("required"))
            self.assertEqual(elem.state.text, report.state.value)
            self.assertEqual(elem.short_description.text, report.short_description)
            self.assertEqual(elem.url.text, report.url)

            return 200, {}, etree.tostring(report.asxml()).decode()

        responses.add_callback(
            method="POST",
            url=re.compile("http://api.example.com/status_reports/(published|built)"),
            callback=callback
        )

        with self.subTest("Built"):
            result = self.osc.staging.set_status_report("Dummy:Project", "repo", "id-1", report,
                                                        "x86_64")
            self.assertTrue(result)
