"""
Main API access
---------------
"""
import gc
from ssl import get_default_verify_paths

from lxml.objectify import fromstring
from requests import Session, Request
from requests.auth import HTTPBasicAuth

from .packages import Package
from .projects import Project
from .bs_requests import Request as BsRequest
from .search import Search
from .users import Group, Person


class Osc:
    """
    Build service API client

    An instance of :py:class:`Osc` provides all the extensions and access to the
    API as attributes, e.g. to get a list of groups use:

    .. code-block:: python

        instance = Osc(*args, **kwargs)
        instance.groups.get_list()

    .. list-table:: Extensions
        :header-rows: 1

        * - Extension
          - Accessible through attribute
        * - :py:class:`osctiny.packages.Package`
          - :py:attr:`packages`
        * - :py:class:`osctiny.projects.Project`
          - :py:attr:`projects`
        * - :py:class:`osctiny.bs_requests.Request`
          - :py:attr:`requests`
        * - :py:class:`osctiny.search.Search`
          - :py:attr:`search`
        * - :py:class:`osctiny.users.Group`
          - :py:attr:`groups`
        * - :py:class:`osctiny.users.Person`
          - :py:attr:`users`

    :param url: API URL of a BuildService instance
    :param username: Credential for login
    :param password: Password for login
    :param verify: See `SSL Cert Verification <http://docs.python-requests.org/en/master/user/advanced/#ssl-cert-verification>`_ for more details
    """
    url = 'https://api.opensuse.org'
    username = ''
    password = ''
    session = None
    _registered = {}

    def __init__(self, url=None, username=None, password=None, verify=None):
        # Basic URL and authentication settings
        self.url = url or self.url
        self.username = username or self.username
        self.password = password or self.password
        self.session = Session()
        self.session.verify = verify or get_default_verify_paths().capath
        self.auth = HTTPBasicAuth(self.username, self.password)

        # API endpoints
        self.groups = Group(osc_obj=self)
        self.packages = Package(osc_obj=self)
        self.projects = Project(osc_obj=self)
        self.requests = BsRequest(osc_obj=self)
        self.search = Search(osc_obj=self)
        self.users = Person(osc_obj=self)

    def __del__(self):
        # Just in case ;-)
        gc.collect()

    def request(self, url, data=None, method="GET", stream=False):
        """
        Perform HTTP(S) request

        :param url: Full URL
        :param data: Data to be included as GET or POST parameters in request
        :param method: HTTP method
        :param stream: Delayed access, see `Body Content Workflow <http://docs.python-requests.org/en/master/user/advanced/#body-content-workflow>`_
        :return: :py:class:`requests.Response`
        """
        data = data or {}
        req = Request(method, url, auth=self.auth, data=data)
        prepped_req = self.session.prepare_request(req)
        settings = self.session.merge_environment_settings(
            prepped_req.url, None, None, None, None
        )
        settings["stream"] = stream
        response = self.session.send(prepped_req, **settings)
        response.raise_for_status()
        return response

    @staticmethod
    def get_objectified_xml(response):
        """
        Return API response as an XML object

        :param response: An API response
        :rtype response: :py:class:`requests.Response`
        :return: :py:class:`lxml.objectify.ObjectifiedElement`
        """
        return fromstring(response.text)




