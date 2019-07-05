import re
from urllib.parse import urlparse, parse_qs

import responses

from .base import OscTest, CallbackFactory


def callback(headers, params, request):
    status = 500
    body = ""
    parsed = urlparse(request.url)
    params.update(parse_qs(parsed.query))

    if "project" in parsed.path:
        status = 200
        body = """
<collection matches="2">
    <project name="SUSE:Maintenance:96" kind="maintenance_incident">
      <title/>
      <description/>
      <person userid="krahmer" role="bugowner"/>
      <person userid="oertel" role="maintainer"/>
      <group groupid="maintenance-team" role="maintainer"/>
      <group groupid="autobuild-team" role="reader"/>
      <group groupid="maintenance-team" role="reviewer"/>
      <lock> 
        <enable/>
      </lock>
      <build>
        <disable/>
      </build>
      <publish>
        <disable/>
      </publish>
      <debuginfo>
        <enable/>
      </debuginfo>
      <repository name="SUSE_Updates_SLE-SERVER_12_x86_64">
        <releasetarget project="SUSE:Updates:SLE-SERVER:12:x86_64" 
          repository="update"/>
        <path project="SUSE:Updates:SLE-SERVER:12:x86_64" repository="update"/>
        <arch>x86_64</arch>
      </repository>
      <repository name="SUSE_Updates_SLE-SERVER_12_s390x">
        <releasetarget project="SUSE:Updates:SLE-SERVER:12:s390x" 
          repository="update"/>
        <path project="SUSE:Updates:SLE-SERVER:12:s390x" repository="update"/>
        <arch>s390x</arch>
      </repository>
      <repository name="SUSE_Updates_SLE-SERVER_12_ppc64le">
        <releasetarget project="SUSE:Updates:SLE-SERVER:12:ppc64le" 
          repository="update"/>
        <path project="SUSE:Updates:SLE-SERVER:12:ppc64le" repository="update"/>
        <arch>ppc64le</arch>
      </repository>
      <repository name="SUSE_Updates_SLE-DESKTOP_12_x86_64">
        <releasetarget project="SUSE:Updates:SLE-DESKTOP:12:x86_64" 
          repository="update"/>
        <path project="SUSE:Updates:SLE-DESKTOP:12:x86_64" repository="update"/>
        <arch>x86_64</arch>
      </repository>
      <repository name="SUSE_SLE-12_Update">
        <releasetarget project="SUSE:SLE-12:Update" repository="standard"/>
        <path project="SUSE:SLE-12:Update" repository="standard"/>
        <arch>i586</arch>
        <arch>x86_64</arch>
        <arch>s390</arch>
        <arch>s390x</arch>
        <arch>ppc64le</arch>
        <arch>aarch64</arch>
      </repository>
    </project>
    <project name="SUSE:Maintenance:9691" kind="maintenance_incident">
      <title/>
      <description/>
      <person userid="gboiko" role="bugowner"/>
      <person userid="oertel" role="maintainer"/>
      <group groupid="maintenance-team" role="maintainer"/>
      <group groupid="autobuild-team" role="reviewer"/>
      <group groupid="legal-auto" role="reviewer"/>
      <group groupid="maintenance-team" role="reviewer"/>
      <build>
        <disable/>
      </build>
      <publish>
        <disable/>
      </publish>
      <debuginfo>
        <enable/>
      </debuginfo>
      <repository name="SUSE_Updates_SLE-SERVER_12-SP4_x86_64">
        <releasetarget project="SUSE:Updates:SLE-SERVER:12-SP4:x86_64" 
          repository="update" trigger="maintenance"/>
        <path project="SUSE:Updates:SLE-SERVER:12-SP4:x86_64" 
          repository="update"/>
        <arch>x86_64</arch>
        <arch>i586</arch>
      </repository>
      <repository name="SUSE_Updates_SLE-SERVER_12-SP4_s390x">
        <releasetarget project="SUSE:Updates:SLE-SERVER:12-SP4:s390x" 
          repository="update" trigger="maintenance"/>
        <path project="SUSE:Updates:SLE-SERVER:12-SP4:s390x" 
          repository="update"/>
        <arch>s390x</arch>
        <arch>s390</arch>
      </repository>
      <repository name="SUSE_Updates_SLE-SERVER_12-SP4_ppc64le">
        <releasetarget project="SUSE:Updates:SLE-SERVER:12-SP4:ppc64le" 
          repository="update" trigger="maintenance"/>
        <path project="SUSE:Updates:SLE-SERVER:12-SP4:ppc64le" 
          repository="update"/>
        <arch>ppc64le</arch>
      </repository>
      <repository name="SUSE_Updates_SLE-SERVER_12-SP4_aarch64">
        <releasetarget project="SUSE:Updates:SLE-SERVER:12-SP4:aarch64" 
          repository="update" trigger="maintenance"/>
        <path project="SUSE:Updates:SLE-SERVER:12-SP4:aarch64" 
          repository="update"/>
        <arch>aarch64</arch>
      </repository>
      <repository name="SUSE_Updates_SLE-SDK_12-SP4_x86_64">
        <releasetarget project="SUSE:Updates:SLE-SDK:12-SP4:x86_64" 
          repository="update" trigger="maintenance"/>
        <path project="SUSE:Updates:SLE-SDK:12-SP4:x86_64" repository="update"/>
        <arch>x86_64</arch>
        <arch>i586</arch>
      </repository>
      <repository name="SUSE_Updates_SLE-SDK_12-SP4_s390x">
         <releasetarget project="SUSE:Updates:SLE-SDK:12-SP4:s390x" 
           repository="update" trigger="maintenance"/>
        <path project="SUSE:Updates:SLE-SDK:12-SP4:s390x" repository="update"/>
        <arch>s390x</arch>
        <arch>s390</arch>
      </repository>
      <repository name="SUSE_Updates_SLE-SDK_12-SP4_ppc64le">
        <releasetarget project="SUSE:Updates:SLE-SDK:12-SP4:ppc64le" 
          repository="update" trigger="maintenance"/>
        <path project="SUSE:Updates:SLE-SDK:12-SP4:ppc64le" repository="update"/>
        <arch>ppc64le</arch>
      </repository>
      <repository name="SUSE_Updates_SLE-SDK_12-SP4_aarch64">
        <releasetarget project="SUSE:Updates:SLE-SDK:12-SP4:aarch64" 
          repository="update" trigger="maintenance"/>
        <path project="SUSE:Updates:SLE-SDK:12-SP4:aarch64" repository="update"/>
        <arch>aarch64</arch>
      </repository>
      <repository name="SUSE_Updates_SLE-HA_12-SP4_x86_64">
        <releasetarget project="SUSE:Updates:SLE-HA:12-SP4:x86_64" 
          repository="update" trigger="maintenance"/>
        <path project="SUSE:Updates:SLE-HA:12-SP4:x86_64" repository="update"/>
        <arch>x86_64</arch>
        <arch>i586</arch>
      </repository>
      <repository name="SUSE_Updates_SLE-HA_12-SP4_s390x">
        <releasetarget project="SUSE:Updates:SLE-HA:12-SP4:s390x" 
          repository="update" trigger="maintenance"/>
        <path project="SUSE:Updates:SLE-HA:12-SP4:s390x" repository="update"/>
        <arch>s390x</arch>
        <arch>s390</arch>
      </repository>
      <repository name="SUSE_Updates_SLE-HA_12-SP4_ppc64le">
        <releasetarget project="SUSE:Updates:SLE-HA:12-SP4:ppc64le" 
          repository="update" trigger="maintenance"/>
        <path project="SUSE:Updates:SLE-HA:12-SP4:ppc64le" repository="update"/>
        <arch>ppc64le</arch>
      </repository>
      <repository name="SUSE_Updates_SLE-DESKTOP_12-SP4_x86_64">
        <releasetarget project="SUSE:Updates:SLE-DESKTOP:12-SP4:x86_64" 
          repository="update" trigger="maintenance"/>
        <path project="SUSE:Updates:SLE-DESKTOP:12-SP4:x86_64" 
          repository="update"/>
        <arch>x86_64</arch>
        <arch>i586</arch>
      </repository>
      <repository name="SUSE_SLE-12-SP4_Update">
        <releasetarget project="SUSE:SLE-12-SP4:Update" repository="standard" 
          trigger="maintenance"/>
        <path project="SUSE:SLE-12-SP4:Update" repository="standard"/>
        <arch>i586</arch>
        <arch>x86_64</arch>
        <arch>s390</arch>
        <arch>s390</arch>
        <arch>s390x</arch>
        <arch>ppc64le</arch>
        <arch>aarch64</arch>
      </repository>
    </project>
</collection>
        """
    elif "package" in parsed.path:
        status = 200
        body = """
<collection matches="6">
<package name="python-django" project="SUSE:SLE-11-SP3:GA:Products:Test">
  <title>A high-level Python Web framework</title>
  <description>Django is a high-level Python Web framework that encourages rapid
  development and clean, pragmatic design.</description>
  <person userid="cloud_bugs" role="bugowner"/>
</package>
<package name="python-django" project="Devel:Cloud:1.0">
  <title>The Web framework for perfectionists with deadlines</title>
  <description>Django is a high-level Python Web framework that encourages rapid
  development and clean, pragmatic design.

Developed by a fast-moving online-news operation, Django was designed to handle 
two challenges: the intensive deadlines of a newsroom and the stringent 
requirements of the experienced Web developers who wrote it. It lets you build 
high-performing, elegant Web applications quickly.

Django focuses on automating as much as possible and adhering to the DRY 
principle.</description>
  <url>http://www.djangoproject.com/</url>
</package>
<package name="python-django" project="Devel:Cloud:2.0">
  <title/>
  <description/>
</package>
<package name="python-django" project="SUSE:SLE-11-SP3:Update">
  <title>A high-level Python Web framework</title>
  <description>Django is a high-level Python Web framework that encourages rapid
  development and clean, pragmatic design.</description>
  <url>http://www.djangoproject.com/</url>
</package>
<package name="python-django" project="SUSE:SLE-11-SP2:Update">
  <title>A high-level Python Web framework</title>
  <description>Django is a high-level Python Web framework that encourages rapid
  development and clean, pragmatic design.</description>
  <releasename>python-django</releasename>
  <url>http://www.djangoproject.com/</url>
</package>
<package name="python-django" project="Devel:Cloud:Shared:11-SP3:Update">
  <title/>
  <description/>
</package>
</collection>
        """
    elif "request" in parsed.path:
        status = 200
        body = """
<collection matches="">
  <request id="167315" creator="aaa">
    <action type="submit">
      <source 
        project="home:aaa:branches:SUSE:SLE-12-SP3:Update:Products:SES5:Update" 
        package="python-Django" rev="dbc59e44f0ea89fb37a081328f7d9b95"/>
      <target project="Devel:Storage:5.0" package="python-Django"/>
      <acceptinfo rev="2" srcmd5="9e6269ae5b5933a3593c413e8816ac7b" 
      osrcmd5="015b33968bcb0deb50d5b702826ddf6a"/>
    </action>
    <state name="accepted" who="aaa" when="2018-06-21T11:07:41">
      <comment>Just me fixing up the changelog</comment>
    </state>
    <description>- Prevented spoofing is_safe_url() with basic auth (bsc#967999,
      CVE-2016-2512)</description>
  </request>
  <request id="167473" creator="aaa">
    <action type="submit">
      <source 
      project="home:aaa:branches:SUSE:SLE-12-SP3:Update:Products:SES5:Update" 
      package="python-Django" rev="691eedaf40acd37e4e682a1668123c85"/>
      <target project="Devel:Storage:5.0" package="python-Django"/>
      <acceptinfo rev="3" srcmd5="8918eba54a899896eaa623a3c2ee8452" 
        osrcmd5="9e6269ae5b5933a3593c413e8816ac7b"/>
    </action>
    <state name="accepted" who="bbb" when="2018-06-25T11:21:20">
      <comment/>
    </state>
    <description>- Fixed catastrophic backtracking in urlize and urlizetrunc 
    template filters
    (bsc#1083304, CVE-2018-7536)
    * Added CVE-2018-7536.patch
  - Fixed catastrophic backtracking in django.utils.text.Truncator (bsc#1083305,
    CVE-2018-7537)
    * Added CVE-2018-7537.patch</description>
  </request>
  <request id="167474" creator="aaa">
    <action type="submit">
      <source 
      project="home:aaa:branches:SUSE:SLE-12-SP2:Update:Products:SES4:Update" 
      package="python-Django" rev="f4f53a48efc315e7e339d84b00f8f74e"/>
      <target project="Devel:Storage:4.0" package="python-Django"/>
      <acceptinfo rev="3" srcmd5="8918eba54a899896eaa623a3c2ee8452" 
        osrcmd5="9e6269ae5b5933a3593c413e8816ac7b"/>
    </action>
    <state name="accepted" who="ccc" when="2018-06-25T11:22:10">
      <comment/>
    </state>
    <description>- Fixed catastrophic backtracking in urlize and urlizetrunc 
    template filters
    (bsc#1083304, CVE-2018-7536)
    * Added CVE-2018-7536.patch
  - Fixed catastrophic backtracking in django.utils.text.Truncator (bsc#1083305,
    CVE-2018-7537)
    * Added CVE-2018-7537.patch</description>
  </request>
</collection>

        """

    headers['request-id'] = '728d329e-0e86-11e4-a748-0c84dc037c13'
    return status, headers, body


class TestSearch(OscTest):
    def setUp(self):
        self.mock_request(
            method=responses.GET,
            url=re.compile(self.osc.url + '/search.*'),
            callback=CallbackFactory(callback)
        )

    @responses.activate
    def test_search(self):
        with self.subTest("Project"):
            response = self.osc.search.project(
                "@kind='maintenance_incident' and "
                "starts-with(@name,'SUSE:Maintenance')"
            )
            self.assertEqual(response.tag, "collection")
            self.assertEqual(response.countchildren(), 2)
            self.assertEqual(
                sorted([x.get("name", None) for x in response.getchildren()]),
                sorted(["SUSE:Maintenance:96", "SUSE:Maintenance:9691"])
            )

        with self.subTest("Package"):
            response = self.osc.search.package(
                "@name='python-django'"
            )
            self.assertEqual(response.tag, "collection")
            self.assertEqual(response.countchildren(), 6)
            self.assertEqual(
                sorted([x.get("project", None) for x in response.getchildren()]),
                sorted([
                    'Devel:Cloud:2.0', 'SUSE:SLE-11-SP3:GA:Products:Test',
                    'Devel:Cloud:1.0', 'SUSE:SLE-11-SP3:Update',
                    'SUSE:SLE-11-SP2:Update', 'Devel:Cloud:Shared:11-SP3:Update'
                ])
            )

        with self.subTest("Request"):
            response = self.osc.search.request(
                "target[@package='python-django']"
            )
            self.assertEqual(response.tag, "collection")
            self.assertEqual(response.countchildren(), 3)
            self.assertEqual(
                sorted(
                    [x.get("who", "zzz")
                     for x in response.xpath("request/state")]
                ),
                ["aaa", "bbb", "ccc"]
            )
