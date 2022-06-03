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
import warnings

try:
    from osc import conf as _conf
    from osc.oscerr import ConfigError, ConfigMissingApiurl
except ImportError:
    _conf = None


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


# pylint: disable=too-many-branches
def get_credentials(url: typing.Optional[str] = None) \
        -> typing.Tuple[str, str, typing.Optional[Path]]:
    """
    Get credentials for Build Service instance identified by ``url``

    .. important::

        If the ``osc`` package is not installed, this function will only try to extract the username
        and password from the configuration file.

        Any credentials stored on a keyring will not be accessible!

    :param str url: URL of Build Service instance (including schema). If not specified, the value
                    from the ``apiurl`` parameter in the config file will be used.
    :return: (username, password, SSH private key path)
    :raises ValueError: if config provides no credentials
    """
    if _conf is not None:
        try:
            _conf.get_config()
            if url is None:
                # get the default api url from osc's config
                url = _conf.config["apiurl"]
            # and now fetch the options for that particular url
            api_config = _conf.get_apiurl_api_host_options(url)
            username = api_config["user"]
            password = api_config["pass"]
            sshkey = Path(api_config["sshkey"]) if api_config["sshkey"] else None
        except (ConfigError, ConfigMissingApiurl) as error:
            if isinstance(error, ConfigError):
                raise ValueError("`osc` config was not found.") from error
            # this is the case of ConfigMissingApiurl
            raise ValueError("`osc` config has no options for URL {}".format(url)) from error

        if not username:
            raise ValueError("`osc` config provides no username for URL {}".format(url))
        if not password:
            raise ValueError("`osc` config provides no password for URL {}".format(url))
        return username, password, sshkey

    warnings.warn("`osc` is not installed. Not all configuration backends of `osc` will be "
                  "available.")
    parser = ConfigParser()
    path = get_config_path()
    parser.read((path))
    try:
        if url is None:
            url = parser["general"].get("apiurl", url)
    except (KeyError, NoSectionError) as error:
        raise ValueError("`osc` config does not provide the default API URL") from error

    if url not in parser.sections():
        raise ValueError("`osc` config has no section for URL {}".format(url))

    username = parser[url].get("user", None)
    if not username:
        raise ValueError("`osc` config provides no username for URL {}".format(url))

    password = parser[url].get("pass", None)
    if not password:
        password = parser[url].get("passx", None)
        if password:
            password = decompress(b64decode(password.encode("ascii"))).decode("ascii")

    if not password:
        raise ValueError("`osc` config provides no password for URL {}".format(url))

    sshkey = parser[url].get("sshkey", None)
    if sshkey:
        sshkey = Path(sshkey)

    return username, password, sshkey
