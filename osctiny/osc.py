"""
Main API access
---------------
"""
from io import BufferedReader, BytesIO, StringIO
import gc
import re
from ssl import get_default_verify_paths
from urllib.parse import urlencode
import warnings

# pylint: disable=no-name-in-module
from lxml.objectify import fromstring
from requests import Session, Request
from requests.auth import HTTPBasicAuth

from .buildresults import Build
from .packages import Package
from .projects import Project
from .bs_requests import Request as BsRequest
from .search import Search
from .users import Group, Person

try:
    from cachecontrol import CacheControl
except ImportError:
    CacheControl = None


# pylint: disable=too-many-instance-attributes,too-many-arguments
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
        * - :py:class:`osctiny.build.Build`
          - :py:attr:`build`

    :param url: API URL of a BuildService instance
    :param username: Credential for login
    :param password: Password for login
    :param verify: See `SSL Cert Verification`_ for more details
    :param cache: Store API responses in a cache

    .. versionadded:: 0.1.1
        The ``cache`` parameter and the ``build`` extension

    .. _SSL Cert Verification:
        http://docs.python-requests.org/en/master/user/advanced/
        #ssl-cert-verification
    """
    url = 'https://api.opensuse.org'
    username = ''
    password = ''
    session = None
    _registered = {}
    default_timeout = (60, 300)

    def __init__(self, url=None, username=None, password=None, verify=None,
                 cache=False):
        # Basic URL and authentication settings
        self.url = url or self.url
        self.username = username or self.username
        self.password = password or self.password
        self._session = Session()
        self._session.verify = verify or get_default_verify_paths().capath
        self.auth = HTTPBasicAuth(self.username, self.password)

        # API endpoints
        self.build = Build(osc_obj=self)
        self.groups = Group(osc_obj=self)
        self.packages = Package(osc_obj=self)
        self.projects = Project(osc_obj=self)
        self.requests = BsRequest(osc_obj=self)
        self.search = Search(osc_obj=self)
        self.users = Person(osc_obj=self)

        # Cache
        if cache:
            # pylint: disable=broad-except
            try:
                self.session = CacheControl(self._session)
            except Exception as error:
                self.session = self._session
                warnings.warn("Cannot use the cache: {}".format(error),
                              RuntimeWarning)
        else:
            self.session = self._session

    def __del__(self):
        # Just in case ;-)
        gc.collect()

    def request(self, url, data=None, method="GET", stream=False,
                raise_for_status=True, timeout=None):
        """
        Perform HTTP(S) request

        ``data`` is URL-encoded and passed on as GET parameters. If ``data`` is
        a dictionary and contains a key ``comment``, this value is passed on as
        a POST parameter.

        If ``stream`` is True, the server response does not get cached because
        the returned file might be large or huge.

        if ``raise_for_status`` is True, the used ``requests`` framework will
        raise an exception for occured errors.

        .. versionchanged:: 0.1.2
            Added parameters `raise_for_status`

        .. versionchanged:: 0.1.3

            * Added parameter `timeout`
            * Transfer data as GET parameters (except for comments and texts)

        :param url: Full URL
        :param data: Data to be included as GET or POST parameters in request
        :param method: HTTP method
        :param stream: Delayed access, see `Body Content Workflow`_
        :param raise_for_status: See `requests.Response.raise_for_status`_
        :param timeout: Request timeout. See `Timeouts`_
        :return: :py:class:`requests.Response`

        .. _Body Content Workflow:
            http://docs.python-requests.org/en/master/user/advanced/
            #body-content-workflow

        .. _requests.Response.raise_for_status:
            https://2.python-requests.org/en/master/api/
            #requests.Response.raise_for_status

        .. _Timeouts:
            https://2.python-requests.org/en/master/user/advanced/#timeouts
        """
        timeout = timeout or self.default_timeout
        if stream:
            session = self._session
        else:
            session = self.session

        if isinstance(data, dict):
            comment = data.pop("comment", {})
            url += "?" + urlencode(self.handle_params(data))
            data = comment

        req = Request(
            method,
            url,
            auth=self.auth,
            data=self.handle_params(data)
        )
        prepped_req = session.prepare_request(req)
        settings = session.merge_environment_settings(
            prepped_req.url, {}, None, None, None
        )
        settings["stream"] = stream
        if timeout:
            settings["timeout"] = timeout

        response = session.send(prepped_req, **settings)
        if raise_for_status:
            response.raise_for_status()
        return response

    @staticmethod
    def handle_params(params):
        """
        Translate request parameters to API conform format

        .. note:: The build service does not handle URL-encoded Unicode well.
                  Therefore parameters are encoded as ``bytes``.

        :param params: Request parameter
        :type params: dict or str or io.BufferedReader
        :return: converted data ready to be used in HTTP request
        :rtype: dict or bytes
        """
        if isinstance(params, bytes):
            return params

        if isinstance(params, str):
            return params.encode()

        if isinstance(params, StringIO):
            params.seek(0)
            return params.read().encode()

        if isinstance(params, (BufferedReader, BytesIO)):
            params.seek(0)
            return params

        if not isinstance(params, dict):
            return {}

        for key in params:
            if isinstance(params[key], bool):
                params[key] = '1' if params[key] else '0'

        return {key.encode(): str(value).encode()
                for key, value in params.items()
                if value is not None}

    @staticmethod
    def get_objectified_xml(response):
        """
        Return API response as an XML object

        :param response: An API response
        :rtype response: :py:class:`requests.Response`
        :return: :py:class:`lxml.objectify.ObjectifiedElement`
        """
        try:
            return fromstring(response.text)
        except ValueError:
            # Just in case OBS returns a Unicode string with encoding
            # declaration
            if isinstance(response.text, str) and "encoding=" in response.text:
                return fromstring(
                    re.sub(r'encoding="[^"]+"', "", response.text)
                )

            # This might be something else
            raise
