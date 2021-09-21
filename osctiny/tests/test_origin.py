import re

import responses

from .base import OscTest, CallbackFactory


class OriginTest(OscTest):
    def test_origin_sort_key(self):
        pattern = self.osc.origins._origin_priority_pattern

        data = (
            # project name, expected
            ('SUSE:SLE-15:Update',
             {"family": "SUSE:SLE", "major": "15", "minor": None, "tail": "Update"}),
            ('SUSE:SLE-15-SP1:Update',
             {"family": "SUSE:SLE", "major": "15", "minor": "1", "tail": "Update"}
             ),
            ('SUSE:SLE-15-SP2:Update',
             {"family": "SUSE:SLE", "major": "15", "minor": "2", "tail": "Update"}
             ),
            ('openSUSE:Leap:15.1',
             {"family": "openSUSE:Leap", "major": "15", "minor": "1", "tail": None}
             ),
            ('openSUSE:Leap:15.1:Update',
             {"family": "openSUSE:Leap", "major": "15", "minor": "1", "tail": "Update"}
             ),
            ('openSUSE:Factory', None),
            ('openSUSE:Leap:15.1:NonFree:Update',
             {"family": "openSUSE:Leap", "major": "15", "minor": "1", "tail": "NonFree:Update"}),
            ('openSUSE:Factory:NonFree', None)
        )

        for project, expected in data:
            with self.subTest(project):
                match = pattern.match(project)
                if expected is None:
                    self.assertIsNone(match)
                else:
                    self.assertEqual(match.groupdict(), expected)

    def test_family_sorter(self):
        data = (
            # input, expected
            (
                ['<devel>', 'openSUSE:Leap:15.2:MicroOS:workarounds',
                 'SUSE:SLE-15-SP2:Update:Products:MicroOS', 'SUSE:SLE-15-SP2:Update',
                 'openSUSE:Leap:15.2:Update', 'openSUSE:Factory'],
                ['<devel>', 'openSUSE:Leap:15.2:MicroOS:workarounds',
                 'SUSE:SLE-15-SP2:Update:Products:MicroOS', 'SUSE:SLE-15-SP2:Update',
                 'openSUSE:Leap:15.2:Update', 'openSUSE:Factory']
            ),
            (
                ['<devel>', 'SUSE:SLE-15:Update', 'SUSE:SLE-15-SP1:Update',
                 'SUSE:SLE-15-SP2:Update', 'openSUSE:Leap:15.1:Update', 'openSUSE:Factory'],
                ['<devel>', 'SUSE:SLE-15-SP2:Update', 'SUSE:SLE-15-SP1:Update',
                 'SUSE:SLE-15:Update', 'openSUSE:Leap:15.1:Update', 'openSUSE:Factory']
            ),
            (
                ['<devel>', 'SUSE:SLE-15-SP2:GA', 'openSUSE:Leap:15.1:Update', 'openSUSE:Leap:15.1',
                 'openSUSE:Factory'],
                ['<devel>', 'SUSE:SLE-15-SP2:GA', 'openSUSE:Leap:15.1:Update', 'openSUSE:Leap:15.1',
                 'openSUSE:Factory']
            ),
            (
                ['<devel>', 'SUSE:SLE-15-SP2:GA', 'openSUSE:Leap:15.1', 'openSUSE:Leap:15.1:Update',
                 'openSUSE:Factory'],
                ['<devel>', 'SUSE:SLE-15-SP2:GA', 'openSUSE:Leap:15.1:Update', 'openSUSE:Leap:15.1',
                 'openSUSE:Factory']
            )
        )

        for unsorted, expected in data:
            with self.subTest():
                now_sorted = list(self.osc.origins.family_sorter(unsorted))
                self.assertTrue(len(now_sorted) == len(unsorted) == len(expected))
                self.assertEqual(expected, now_sorted)

    @responses.activate
    def test_maintained_projects(self):
        def callback(headers, params, request):
            status, body = 500, ""

            if "OBS:MaintenanceProject" in "".join(params.get("match", [])):
                status = 200
                body = """
                <collection matches="1">
                    <project name="openSUSE:Maintenance"/>
                </collection>
                """
            elif "OBS:Maintained" in "".join(params.get("match", [])):
                status = 200
                body = """
                <collection matches="2">
                    <project name="openSUSE:Leap:15.1:Update"/>
                    <project name="openSUSE:Leap:15.2:Update"/>
                </collection>
                """

            return status, headers, body

        self.mock_request(
            method=responses.GET,
            url=re.compile(self.osc.url + "/search/project/id"),
            callback=CallbackFactory(callback)
        )

        with self.subTest("Maintenance Project"):
            maint_project = self.osc.origins.maintenance_project
            self.assertEqual(maint_project, "openSUSE:Maintenance")

        with self.subTest("Maintained Projects"):
            self.assertEqual(self.osc.origins.maintained_projects,
                             ["openSUSE:Leap:15.1:Update", "openSUSE:Leap:15.2:Update"])

    @responses.activate
    def test_get_project_origin_config(self):
        self.mock_request(
            method=responses.GET,
            url=re.compile(self.osc.url + "/source/openSUSE:Leap:15.2:Update/_attribute"),
            body="""
<attributes>
  <attribute name="OriginConfig" namespace="OSRT">
    <value>origins:
- &lt;devel&gt;: {}
- SUSE:SLE-15:Update:
    maintainer_review_initial: false
- SUSE:SLE-15-SP1:Update:
    maintainer_review_initial: false
- SUSE:SLE-15-SP2:Update:
    maintainer_review_initial: false
- openSUSE:Leap:15.1:Update:
    pending_submission_allow: true
- openSUSE:Factory:
    pending_submission_allow: true
- '*~': {}
fallback-group: 'origin-reviewers-maintenance'
    </value>
  </attribute>
  <attribute name="Maintained" namespace="OBS"/>
</attributes>"""
        )

        config = self.osc.origins.get_project_origin_config("openSUSE:Leap:15.2:Update")
        self.assertEqual(config["origins"],
                         [
                             {'<devel>': {}},
                             {'SUSE:SLE-15:Update': {'maintainer_review_initial': False}},
                             {'SUSE:SLE-15-SP1:Update': {'maintainer_review_initial': False}},
                             {'SUSE:SLE-15-SP2:Update': {'maintainer_review_initial': False}},
                             {'openSUSE:Leap:15.1:Update': {'pending_submission_allow': True}},
                             {'openSUSE:Factory': {'pending_submission_allow': True}},
                             {'*~': {}}
                         ])

    @responses.activate
    def test_expanded_origins(self):
        def callback_attr(headers, params, request):
            pattern = re.compile(r"openSUSE:Leap:15\.([12]):Update")
            status, body = 500, ""
            match = pattern.search(request.url)
            if match.group(1) == "2":
                status = 200
                body = """
<attributes>
  <attribute name="OriginConfig" namespace="OSRT">
    <value>origins:
- &lt;devel&gt;: {}
- SUSE:SLE-15:Update:
    maintainer_review_initial: false
- SUSE:SLE-15-SP1:Update:
    maintainer_review_initial: false
- SUSE:SLE-15-SP2:Update:
    maintainer_review_initial: false
- openSUSE:Leap:15.1:Update:
    pending_submission_allow: true
- openSUSE:Factory:
    pending_submission_allow: true
- '*~': {}
fallback-group: 'origin-reviewers-maintenance'
    </value>
  </attribute>
  <attribute name="Maintained" namespace="OBS"/>
</attributes>"""
            elif match.group(1) == "1":
                status = 200
                body = """
<attributes>
  <attribute name="OriginConfig" namespace="OSRT">
    <value>origins:
- &lt;devel&gt;: {}
- SUSE:SLE-15*:
    maintainer_review_initial: false
- openSUSE:Factory:
    pending_submission_allow: true
- '*~': {}
fallback-group: 'origin-reviewers-maintenance'
    </value>
  </attribute>
  <attribute name="Maintained" namespace="OBS"/>
</attributes>"""

            return status, headers, body

        def callback_proj(headers, params, request):
            status, body = 500, ""
            match_string = "".join(params.get("match", []))

            if 'OSRT:OriginConfig' in match_string:
                status = 200
                body = """
                <collection matches="2">
                    <project name="openSUSE:Leap:15.1:Update"/>
                    <project name="openSUSE:Leap:15.2:Update"/>
                </collection>
                """
            elif "starts-with" in match_string:
                status = 200
                body = """
                <collection matches="10">
                  <project name='SUSE:SLE-15-SP1:GA'/>
                  <project name='SUSE:SLE-15-SP1:Update'/>
                  <project name='SUSE:SLE-15-SP2:GA'/>
                  <project name='SUSE:SLE-15-SP2:Update'/>
                  <project name='SUSE:SLE-15-SP2:Update:Products:MicroOS'/>
                  <project name='SUSE:SLE-15-SP2:Update:Products:MicroOS:Update'/>
                  <project name='SUSE:SLE-15-SP3:GA'/>
                  <project name='SUSE:SLE-15-SP3:Update'/>
                  <project name='SUSE:SLE-15:GA'/>
                  <project name='SUSE:SLE-15:Update'/>
                </collection>
                """

            return status, headers, body

        self.mock_request(
            method=responses.GET,
            url=re.compile(self.osc.url + "/search/project/id"),
            callback=CallbackFactory(callback_proj)
        )
        self.mock_request(
            method=responses.GET,
            url=re.compile(self.osc.url + r"/source/openSUSE:Leap:15\.[12]:Update/_attribute"),
            callback=CallbackFactory(callback_attr)
        )

        self.assertEqual(
            dict(self.osc.origins.expanded_origins),
            {
                "openSUSE:Leap:15.1:Update": [
                    "<devel>", "SUSE:SLE-15-SP1:Update", "SUSE:SLE-15-SP1:GA", "SUSE:SLE-15:Update",
                    "SUSE:SLE-15:GA", "openSUSE:Factory"
                ],
                "openSUSE:Leap:15.2:Update": [
                    "<devel>", "SUSE:SLE-15-SP2:Update", "SUSE:SLE-15-SP1:Update",
                    "SUSE:SLE-15:Update", "openSUSE:Leap:15.1:Update", "openSUSE:Factory"
                ]
            }
        )
