"""
Configuration utilities
^^^^^^^^^^^^^^^^^^^^^^^

This module provides a collection of utilities to access the configuration of
`osc <https://github.com/openSUSE/osc>`_ in order to make it easier to create command line tools
with OSC Tiny.

.. versionadded:: 0.4.0
"""
import typing
from base64 import b64decode
from bz2 import decompress
from configparser import ConfigParser, NoSectionError
import os
from pathlib import Path

try:
    from osc import conf as _conf
    from osc.oscerr import ConfigError, ConfigMissingApiurl
except ImportError:
    _conf = None


# Query parameters that are considered to be boolean by the build service
BOOLEAN_PARAMS = {
    "^/source/[^/]+/[^/]+/?$": {
        'GET': ('emptylink', 'expand', 'meta', 'lastworking', 'withlinked', 'deleted', 'parse'),
        'POST': ('ignoredevel', 'add_repositories', 'noaccess', 'update_path_elements',
                 'extend_package_names', 'extend_package_names', 'keeplink', 'repairlink')
    },
    "^/source/[^/]+/?$": {
        'GET': ('expand', 'deleted'),
    },
    "^/source/[^/]+/[^/]+/[^/]+$": {
        'PUT': ('keeplink',)
    },
    "^/build/[^/]+/_result$": {
        'GET': ('lastbuild', 'locallink', 'multibuild')
    },
    "search/published/(binary|repoinfo|pattern)/id$": {
        'GET': ('withdownloadurl',)
    }
}


def get_config_path() -> Path:
    """
    Return path of ``osc`` configuration file

    :return: Path
    :raises FileNotFoundError: if no config file found
    """
    env_path = os.environ.get("OSC_CONFIG", None)
    conf_path = os.environ.get('XDG_CONFIG_HOME', '~/.config')
    if env_path:
        path = Path(env_path)
        if path.is_file():
            return path

    for path in (Path.home().joinpath(".oscrc"),
                 Path(conf_path).joinpath("osc/oscrc").expanduser()):
        if path.is_file():
            return path

    raise FileNotFoundError("No `osc` configuration file found")


def _get_credentials_from_oscrc(url: typing.Optional[str] = None) -> typing.Tuple[str, str, Path]:
    """
    Get credentials for Build Service instance identified by ``url`` from ``osc`` config file

    .. note::

        This function does not perform data validation or sanitation. It is not recommended to call
        this function directly; use :py:fun:`get_credentials` instead.

    :param url: URL of Build Service instance (including schema). If not specified, the value
                from the ``apiurl`` parameter in the config file will be used.
    :return: (username, password, SSH private key path)
    :raises ValueError: if config provides no credentials

    .. versionadded:: 0.6.3
    """
    parser = ConfigParser()
    path = get_config_path()
    parser.read(path)
    try:
        if url is None:
            url = parser["general"].get("apiurl", url)
    except (KeyError, NoSectionError) as error:
        raise ValueError("`osc` config does not provide the default API URL") from error

    if url not in parser.sections():
        raise ValueError("`osc` config has no section for URL {}".format(url))

    username = parser[url].get("user", None)

    password = parser[url].get("pass", None)
    if not password:
        password = parser[url].get("passx", None)
        if password:
            password = decompress(b64decode(password.encode("ascii"))).decode("ascii")

    sshkey = parser[url].get("sshkey", None)
    if sshkey:
        sshkey = Path(sshkey).expanduser()

    return username, password, sshkey


def _get_credentials_from_oscconf(url: typing.Optional[str] = None) -> typing.Tuple[str, str, Path]:
    """
    Get credentials for Build Service instance identified by ``url`` from ``osc``

    .. note::

        This function does not perform data validation or sanitation. It is not recommended to call
        this function directly; use :py:fun:`get_credentials` instead.

    :param url: URL of Build Service instance (including schema). If not specified, the value
                from the ``apiurl`` parameter in the config file will be used.
    :return: (username, password, SSH private key path)
    :raises ValueError: if config provides no credentials
    :raises RuntimeError: if ``osc`` is not installed

    .. versionadded:: 0.6.3
    """
    if _conf is None:
        raise RuntimeError("`osc` is not installed. Use _get_credentials_from_oscrc instead!")
    try:
        _conf.get_config()
        if url is None:
            # get the default api url from osc's config
            url = _conf.config["apiurl"]
        # and now fetch the options for that particular url
        api_config = _conf.get_apiurl_api_host_options(url)
        username = api_config["user"]
        # Note: `osc` can return a wrapper object instead of a plain password:
        # https://github.com/openSUSE/osc/issues/1073
        password = str(api_config["pass"])
        sshkey = Path(api_config["sshkey"]) if api_config.get("sshkey", None) else None
    except (KeyError, ConfigError, ConfigMissingApiurl) as error:
        if isinstance(error, ConfigError):
            raise ValueError("`osc` config was not found.") from error
        # this is the case of ConfigMissingApiurl
        raise ValueError("`osc` config has no options for URL {}".format(url)) from error

    return username, password, sshkey


# pylint: disable=too-many-branches
def get_credentials(url: typing.Optional[str] = None) \
        -> typing.Tuple[str, typing.Optional[str], typing.Optional[Path]]:
    """
    Get credentials for Build Service instance identified by ``url``

    .. important::

        If the ``osc`` package is not installed, this function will only try to extract the username
        and password from the configuration file.

        Any credentials stored on a keyring will not be accessible!

    :param url: URL of Build Service instance (including schema). If not specified, the value
                from the ``apiurl`` parameter in the config file will be used.
    :return: (username, password, SSH private key path)
    :raises ValueError: if config provides no credentials

    .. versionchanged:: 0.6.3

        If an SSH key is configured, this function will return ``None`` instead of a password.
    """
    getter = _get_credentials_from_oscrc if _conf is None else _get_credentials_from_oscconf
    username, password, sshkey = getter(url=url)

    if not username:
        raise ValueError(f"`osc` config provides no username for URL {url}")

    if sshkey is not None:
        if not sshkey.exists():
            # if it is just a key file name, look at the default SSH dir (which is the most
            # common case)
            sshkey = Path.home() / ".ssh" / sshkey
            if not sshkey.exists():
                raise ValueError(f"SSH key from config does not exist: {sshkey}")

    if not password and not sshkey:
        raise ValueError(f"`osc` config provides no password or SSH key for URL {url}")

    return username, password if sshkey is None else None, sshkey
