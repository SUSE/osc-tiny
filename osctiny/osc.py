"""
Main API access
---------------
"""
from __future__ import unicode_literals

from base64 import b64encode
import typing
from io import BufferedReader, BytesIO, StringIO
import gc
import logging
from pathlib import Path
import re
from ssl import get_default_verify_paths
import time
import threading
from urllib.parse import quote
import warnings

# pylint: disable=no-name-in-module
from lxml.objectify import fromstring, makeparser
from requests import Session, Request
from requests.auth import HTTPBasicAuth
from requests.cookies import RequestsCookieJar, cookiejar_from_dict
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
from .utils.auth import HttpSignatureAuth
from .utils.conf import get_credentials
from .utils.errors import OscError

try:
    from cachecontrol import CacheControl
except ImportError:
    CacheControl = None

THREAD_LOCAL = threading.local()


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
    :param username: Username
    :param password: Password; this is either the user password (``ssh_key_file`` is ``None``) or
                     the SSH passphrase, if ``ssh_key_file`` is defined
    :param verify: See `SSL Cert Verification`_ for more details
    :param cache: Store API responses in a cache
    :param ssh_key_file: Path to SSH private key file
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

    .. versionchanged:: 0.6.0
        Support for 2FA authentication (i.e. added the ``ssh_key_file`` parameter and changed the
        meaning of the ``password`` parameter

    .. _SSL Cert Verification:
        http://docs.python-requests.org/en/master/user/advanced/
        #ssl-cert-verification
    """
    url = 'https://api.opensuse.org'
    username = ''
    password = ''
    default_timeout = (60, 300)
    default_connection_retries = 5
    default_retry_timeout = 5

    def __init__(self, url: str = None, username: typing.Optional[str] = None,
                 password: typing.Optional[str] = None, verify: typing.Optional[str] = None,
                 cache: bool = False,
                 ssh_key_file: typing.Optional[typing.Union[Path, str]] = None):
        # Basic URL and authentication settings
        self.url = url or self.url
        self.username = username or self.username
        self.password = password or self.password
        self.verify = verify
        self.cache = cache
        self.ssh_key = ssh_key_file
        if self.ssh_key is not None and not isinstance(self.ssh_key, Path):
            self.ssh_key = Path(self.ssh_key)

        if not self.username and not self.password and not self.ssh_key:
            try:
                self.username, self.password, self.ssh_key = get_credentials(self.url)
            except (ValueError, RuntimeError, FileNotFoundError) as error:
                raise OscError from error

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

        hash_value = b64encode(f'{self.username}@{self.url}@{self.ssh_key}'.encode())
        self._session_id = f"session_{hash_value}"

    def __del__(self):
        # Just in case ;-)
        gc.collect()

    @property
    def _session(self) -> Session:
        """
        Session object
        """
        session = getattr(THREAD_LOCAL, self._session_id, None)
        if not session:
            session = Session()
            session.verify = self.verify or get_default_verify_paths().capath

            if self.ssh_key is not None:
                session.auth = HttpSignatureAuth(username=self.username, password=self.password,
                                                 ssh_key_file=self.ssh_key)
            else:
                session.auth = HTTPBasicAuth(self.username, self.password)

            setattr(THREAD_LOCAL, self._session_id, session)

        return session

    @property
    def session(self) -> typing.Union[CacheControl, Session]:
        """
        Session object

        Possibly wrapped in CacheControl, if installed.
        """
        key = f"cached_{self._session_id}"
        session = getattr(THREAD_LOCAL, key, None)
        if not session:
            if self.cache:
                # pylint: disable=broad-except
                try:
                    session = CacheControl(self._session)
                except Exception as error:
                    session = self._session
                    warnings.warn("Cannot use the cache: {}".format(error), RuntimeWarning)
            else:
                session = self._session
            setattr(THREAD_LOCAL, key, session)

        return session

    @property
    def cookies(self) -> RequestsCookieJar:
        """
        Access session cookies
        """
        return self._session.cookies

    @cookies.setter
    def cookies(self, value: RequestsCookieJar):
        if not isinstance(value, (RequestsCookieJar, dict)):
            raise TypeError(f"Expected a cookie jar or dict. Got instead: {type(value)}")

        if isinstance(value, RequestsCookieJar):
            self._session.cookies = value
        else:
            self._session.cookies = cookiejar_from_dict(value)

    @property
    def parser(self):
        """
        Explicit parser instance
        """
        if not hasattr(THREAD_LOCAL, "parser"):
            THREAD_LOCAL.parser = makeparser(huge_tree=True)

        return THREAD_LOCAL.parser

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
            Added parameter `params`

        .. versionchanged:: 0.5.0
            Added logging of request/response

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
            url.replace("#", quote("#")).replace("?", quote("?")),
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

        logger = logging.getLogger("osctiny.request")

        for i in range(self.default_connection_retries, -1, -1):
            logger.info("Requested URL: %s", prepped_req.url)
            logger.debug("Sent data:\n%s\n---",
                         "\n".join(f"{k}: {v}" for k, v in req.data.items())
                         if isinstance(req.data, dict) else req.data)
            logger.debug("Sent parameters:\n%s\n---",
                         "\n".join(f"{k}: {v}" for k, v in req.params.items()))
            try:
                response = session.send(prepped_req, **settings)
            except _ConnectionError as error:
                warnings.warn("Problem connecting to server: {}".format(error))
                log_method = logger.error if i < 1 else logger.warning
                log_method("Request failed: %s", error)
                if i < 1:
                    raise
                logger.debug("Retrying request in %d seconds", self.default_retry_timeout)
                time.sleep(self.default_retry_timeout)
            else:
                logger.info("Server replied with status %d", response.status_code)
                logger.debug("Response headers:\n%s\n---",
                             "\n".join(f"{k}: {v}" for k, v in response.headers.items()))
                logger.debug("Response content:\n%s\n---", response.text)
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
