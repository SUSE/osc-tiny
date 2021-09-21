"""
Main API access
---------------
"""
from __future__ import unicode_literals
from io import BufferedReader, BytesIO, StringIO
import gc
import re
from ssl import get_default_verify_paths
import time
import warnings

# pylint: disable=no-name-in-module
from lxml.objectify import fromstring, makeparser
from requests import Session, Request
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError as _ConnectionError

from .extensions.buildresults import Build
from .extensions.comments import Comment
from .extensions.distributions import Distribution
from .extensions.issues import Issue
from .extensions.origin import Origin
from .extensions.packages import Package
from .extensions.projects import Project
from .extensions.bs_requests import Request as BsRequest
from .extensions.search import Search
from .extensions.users import Group, Person
from .utils.conf import get_credentials
from .utils.errors import OscError

try:
    from cachecontrol import CacheControl
except ImportError:
    CacheControl = None


# pylint: disable=too-many-instance-attributes,too-many-arguments
# pylint: disable=too-many-locals
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
        * - :py:class:`osctiny.extensions.packages.Package`
          - :py:attr:`packages`
        * - :py:class:`osctiny.extensions.projects.Project`
          - :py:attr:`projects`
        * - :py:class:`osctiny.extensions.bs_requests.Request`
          - :py:attr:`requests`
        * - :py:class:`osctiny.extensions.search.Search`
          - :py:attr:`search`
        * - :py:class:`osctiny.extensions.users.Group`
          - :py:attr:`groups`
        * - :py:class:`osctiny.extensions.users.Person`
          - :py:attr:`users`
        * - :py:class:`osctiny.extensions.build.Build`
          - :py:attr:`build`
        * - :py:class:`osctiny.extensions.comments.Comment`
          - :py:attr:`comments`
        * - :py:class:`osctiny.extensions.distributions.Distribution`
          - :py:attr:`distributions`
        * - :py:class:`osctiny.extensions.origin.Origin`
          - :py:attr:`origins`

    :param url: API URL of a BuildService instance
    :param username: Credential for login
    :param password: Password for login
    :param verify: See `SSL Cert Verification`_ for more details
    :param cache: Store API responses in a cache
    :raises osctiny.errors.OscError: if no credentials are provided

    .. versionadded:: 0.1.1
        The ``cache`` parameter and the ``build`` extension

    .. versionadded:: 0.1.8
        The ``comments`` extension

    .. versionadded:: 0.2.2
        The ``issues`` extension

    .. versionadded:: 0.2.3
        The ``distributions`` extension

    .. versionadded:: 0.3.0
        The ``origins`` extension

    .. versionchanged:: 0.4.0
        Raises an exception when no credentials are provided

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
    default_connection_retries = 5
    default_retry_timeout = 5

    def __init__(self, url=None, username=None, password=None, verify=None,
                 cache=False):
        # Basic URL and authentication settings
        self.url = url or self.url
        self.username = username or self.username
        self.password = password or self.password

        if not self.username and not self.password:
            try:
                self.username, self.password = get_credentials(self.url)
            except (ValueError, NotImplementedError, FileNotFoundError) as error:
                raise OscError from error

        self._session = Session()
        self._session.verify = verify or get_default_verify_paths().capath
        self.auth = HTTPBasicAuth(self.username, self.password)
        self.parser = makeparser(huge_tree=True)

        # API endpoints
        self.build = Build(osc_obj=self)
        self.comments = Comment(osc_obj=self)
        self.distributions = Distribution(osc_obj=self)
        self.groups = Group(osc_obj=self)
        self.issues = Issue(osc_obj=self)
        self.origins = Origin(osc_obj=self)
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

    def request(self, url, method="GET", stream=False, data=None, params=None,
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

        .. versionchanged:: 0.1.5
            Retry sending the request, if the remote host disconnects

        .. versionadded:: 0.1.7

            * Added parameter `params`

        :param url: Full URL
        :param method: HTTP method
        :param stream: Delayed access, see `Body Content Workflow`_
        :param data: Data to be included as POST parameters in request
        :param params: Additional GET parameters to be included in request
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

        req = Request(
            method,
            url,
            auth=self.auth,
            data=self.handle_params(data),
            params=self.handle_params(params)
        )
        prepped_req = session.prepare_request(req)
        prepped_req.headers['Content-Type'] = "application/octet-stream"
        prepped_req.headers['Accept'] = "application/xml"
        settings = session.merge_environment_settings(
            prepped_req.url, {}, None, None, None
        )
        settings["stream"] = stream
        if timeout:
            settings["timeout"] = timeout

        for i in range(self.default_connection_retries, -1, -1):
            try:
                response = session.send(prepped_req, **settings)
            except _ConnectionError as error:
                warnings.warn("Problem connecting to server: {}".format(error))
                if i < 1:
                    raise
                time.sleep(self.default_retry_timeout)
            else:
                if raise_for_status:
                    response.raise_for_status()
                return response

        return None

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
            return params.encode('utf-8')

        if isinstance(params, StringIO):
            params.seek(0)
            return params.read().encode('utf-8')

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

    def get_objectified_xml(self, response):
        """
        Return API response as an XML object

        .. versionchanged:: 0.1.6

            Allow parsing of "huge" XML inputs

        .. versionchanged:: 0.2.4

            Allow ``response`` to be a string

        :param response: An API response or XML string
        :rtype response: :py:class:`requests.Response`
        :return: :py:class:`lxml.objectify.ObjectifiedElement`
        """
        if isinstance(response, str):
            text = response
        else:
            text = response.text

        try:
            return fromstring(text, self.parser)
        except ValueError:
            # Just in case OBS returns a Unicode string with encoding
            # declaration
            if isinstance(text, str) and \
                    "encoding=" in text:
                return fromstring(
                    re.sub(r'encoding="[^"]+"', "", text)
                )

            # This might be something else
            raise
