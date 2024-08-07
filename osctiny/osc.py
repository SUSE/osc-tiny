"""
Main API access
---------------
"""
from __future__ import unicode_literals

import typing
import errno
from http.cookiejar import CookieJar, LWPCookieJar
from io import BufferedReader, BytesIO, StringIO
import gc
from pathlib import Path
import re
import threading
from urllib.parse import quote, urlparse
import warnings

from lxml.etree import tostring
from lxml.objectify import ObjectifiedElement
from requests import Session, Request, Response
from requests.auth import HTTPBasicAuth
from requests.cookies import RequestsCookieJar, cookiejar_from_dict
from requests.exceptions import ConnectionError as _ConnectionError

from .extensions.attributes import Attribute
from .extensions.buildresults import Build
from .extensions.comments import Comment
from .extensions.distributions import Distribution
from .extensions.issues import Issue
from .extensions.origin import Origin
from .extensions.packages import Package
from .extensions.projects import Project
from .extensions.bs_requests import Request as BsRequest
from .extensions.search import Search
from .extensions.staging import Staging
from .extensions.users import Group, Person
from .models import ParamsType
from .utils.auth import HttpSignatureAuth
from .utils.backports import cached_property
from .utils.conf import BOOLEAN_PARAMS, get_credentials
from .utils.cookies import CookieManager
from .utils.errors import OscError
from .utils.session import generate_session_id, init_session, RetryPolicy
from .utils.xml import get_xml_parser, get_objectified_xml


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
        * - :py:class:`osctiny.extensions.attributes.Attribute`
          - :py:attr:`attributes`
        * - :py:class:`osctiny.extensions.staging.Staging`
          - :py:attr:`staging`

    :param url: API URL of a BuildService instance
    :param username: Username
    :param password: Password; this is either the user password (``ssh_key_file`` is ``None``) or
                     the SSH passphrase, if ``ssh_key_file`` is defined
    :param verify: See `SSL Cert Verification`_ for more details
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

    .. versionchanged:: 0.8.0
        * Removed the ``cache`` parameter
        * Added the ``attributes`` extension

    .. versionchanged:: 0.9.0
        * Added the ``staging`` extension

    .. versionchanged:: 0.10.2
        * Deprecated ``default_connection_retries`` and ``default_retry_timeout``
        * Introduced :py:class:`osctiny.utils.session.RetryPolicy`

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
    retry_policy = RetryPolicy(max_attempts=default_connection_retries,
                               backoff_max=default_retry_timeout)

    def __init__(self, url: typing.Optional[str] = None, username: typing.Optional[str] = None,
                 password: typing.Optional[str] = None, verify: typing.Optional[str] = None,
                 ssh_key_file: typing.Optional[typing.Union[Path, str]] = None):
        # Basic URL and authentication settings
        self.url = url or self.url
        self.username = username or self.username
        self.password = password or self.password
        self.verify = verify
        self.ssh_key = ssh_key_file
        if self.ssh_key is not None and not isinstance(self.ssh_key, Path):
            self.ssh_key = Path(self.ssh_key)

        if not self.username and not self.password and not self.ssh_key:
            try:
                self.username, self.password, self.ssh_key = get_credentials(self.url)
            except (ValueError, RuntimeError, FileNotFoundError) as error:
                raise OscError from error

        # API endpoints
        self.attributes = Attribute(osc_obj=self)
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
        self.staging = Staging(osc_obj=self)
        self.users = Person(osc_obj=self)

    def __del__(self):
        # Just in case ;-)
        gc.collect()

    @property
    def session(self) -> Session:
        """
        Session object
        """
        session_id = generate_session_id(username=self.username, url=self.url)
        session = getattr(THREAD_LOCAL, session_id, None)
        if not session:
            if self.ssh_key is not None:
                auth = HttpSignatureAuth(username=self.username, password=self.password,
                                         ssh_key_file=self.ssh_key)
            else:
                auth = HTTPBasicAuth(self.username, self.password)
            session = init_session(auth=auth, policy=self.retry_policy, verify=self.verify)
            setattr(THREAD_LOCAL, session_id, session)

        return session

    @property
    def cookies(self) -> RequestsCookieJar:
        """
        Access session cookies
        """
        return self.session.cookies

    @cookies.setter
    def cookies(self, value: typing.Union[LWPCookieJar, dict, str]):
        if not isinstance(value, (LWPCookieJar, dict, str)):
            raise TypeError(f"Expected a cookie jar or dict. Got instead: {type(value)}")

        if isinstance(value, CookieJar):
            self.session.cookies = value
        if isinstance(value, str):
            CookieManager.set_cookie(jar=self.session.cookies, cookie=value)
        else:
            self.session.cookies = cookiejar_from_dict(value)

    @property
    def parser(self):
        """
        Explicit parser instance

        .. versionchanged:: 0.8.0
            Content moved to :py:func:`osctiny.utils.xml.get_xml_parser`
        """
        return get_xml_parser()

    def request(self, url: str, method: str = "GET", stream: bool = False,
                data: typing.Optional[ParamsType] = None,
                params: typing.Optional[ParamsType] = None,
                raise_for_status: bool = True, timeout: typing.Optional[int] = None) \
            -> typing.Optional[Response]:
        """
        Perform HTTP(S) request

        ``data`` is URL-encoded and passed on as GET parameters. If ``data`` is
        a dictionary and contains a key ``comment``, this value is passed on as
        a POST parameter.

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

        req = Request(
            method,
            url.replace("#", quote("#")).replace("?", quote("?")),
            data=self.handle_params(url=url, method=method, params=data),
            params=self.handle_params(url=url, method=method, params=params)
        )
        prepped_req = self.session.prepare_request(req)
        prepped_req.headers['Content-Type'] = "application/octet-stream"
        prepped_req.headers['Accept'] = "application/xml"
        settings = self.session.merge_environment_settings(
            prepped_req.url, {}, None, None, None
        )
        settings["stream"] = stream
        if timeout:
            settings["timeout"] = timeout

        try:
            response = self.session.send(prepped_req, **settings)
        except _ConnectionError as error:
            warnings.warn("Problem connecting to server: {}".format(error))
        else:
            if raise_for_status:
                response.raise_for_status()
            return response

        return None

    @cached_property
    def _boolean_param_map(self) -> typing.Dict[typing.Pattern, typing.Dict[str,
                                                                            typing.Tuple[str]]]:
        """
        Return mapping table to identify boolean parameters for a given API endpoint
        """
        return {re.compile(url): data for url, data in BOOLEAN_PARAMS.items()}

    def get_boolean_params(self, url: str, method: str) -> typing.Tuple[str]:
        """
        Get the actual boolean parameter for ``url`` and ``method``

        .. versionadded:: 0.7.3
        """
        parsed_url = urlparse(url)
        for pattern, boolean_params_for_url in self._boolean_param_map.items():
            match = pattern.match(parsed_url.path)
            if match:
                return boolean_params_for_url.get(method, ())

        return ()

    def handle_params(self, url: str, method: str, params: ParamsType) \
            -> bytes:  # pylint: disable=too-many-return-statements
        """
        Translate request parameters to API conform format

        .. note:: The build service does not handle URL-encoded Unicode well.
                  Therefore, parameters are encoded as ``bytes``.

        .. warning:: The build service does not declare its parameters properly and developers do
                     `not intend to fix`_ this server-side. If you want to use _boolean_ parameters,
                     make sure to use ``True`` and ``False``. If you use ``0`` or ``1`` instead, you
                     might receive unexpected results.

                     .. _not intend to fix: https://github.com/openSUSE/open-build-service/issues
                                            /9715

        :param params: Request parameter
        :param url: URL to which the parameters will be sent
        :type url: str
        :param method: HTTP method to send request
        :type method: str
        :return: converted data ready to be used in HTTP request
        :rtype: dict or bytes

        .. versionchanged:: 0.7.3

            Added the ``url`` and ``method`` parameters

        .. versionchanged:: 0.9.0

            Instances of ``ObjectifiedElement`` are accepted for argument ``params``
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

        if isinstance(params, ObjectifiedElement):
            return tostring(params, encoding="utf-8", xml_declaration=True)

        if not isinstance(params, dict):
            return {}

        # The OBS API has a weird expectation regarding boolean parameters and the maintainers have
        # made it clear, that they are not going to clean up the API :(
        # See: https://github.com/openSUSE/open-build-service/issues/9715
        # Also, there are parameters giving the impression that they are boolean, but actually are
        # not.
        boolean_params = self.get_boolean_params(url=url, method=method)
        unexpected_bools = {key for key, value in params.items()
                            if isinstance(value, bool) and key not in boolean_params}
        if unexpected_bools:
            for key in unexpected_bools:
                params[key] = '1' if params[key] else '0'

        return "&".join(
            quote(str(key))
            if key in boolean_params
            else f"{quote(str(key))}={quote(str(value))}"
            for key, value in (
                (key, value)
                for key, value in params.items()
                if not (key in boolean_params and value in [False, "0", 0, None, ""])
            )
            if value is not None
        ).encode()

    def download(self, url: str, destdir: Path, destfile: typing.Optional[str] = None,
                 overwrite: bool = False, **params: ParamsType) -> Path:
        """
        Shortcut for a streaming GET request

        :param str url: Download URL
        :param pathlib.Path destdir: Destination directory
        :param str destfile: Target file name. If not specified, it will be taken from the URL
        :param bool overwrite: switch to overwrite existing downloaded file
        :param params: Additional query params
        :return: absolute path to file or ``None``

        .. versionadded:: 0.7.0
        """
        destdir = destdir if isinstance(destdir, Path) else Path(destdir)
        if not destfile:
            parsed = urlparse(url)
            destfile = Path(parsed.path).name

        if destdir.is_file():
            raise OSError(errno.EEXIST, "Target directory is a file", destdir)

        target = destdir.joinpath(destfile)
        if not overwrite and target.exists():
            raise OSError(errno.EEXIST, "File already exists", target)
        if not destdir.exists():
            destdir.mkdir(parents=True, exist_ok=True)

        response = self.request(url=url, method="GET", stream=True, params=params)

        with target.open("wb") as handle:
            for chunk in response.iter_content(1024):
                handle.write(chunk)

        return target

    def get_objectified_xml(self, response: Response) -> ObjectifiedElement:
        """
        Return API response as an XML object

        .. versionchanged:: 0.1.6

            Allow parsing of "huge" XML inputs

        .. versionchanged:: 0.2.4

            Allow ``response`` to be a string

        .. versionchanged:: 0.8.0

            Content moved to :py:func:`osctiny.utils.xml.get_objectified_xml`
        """
        return get_objectified_xml(response=response)
