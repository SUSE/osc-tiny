"""
Configuration utilities
^^^^^^^^^^^^^^^^^^^^^^^

This module provides a collection of utilities to access the configuration of
`osc <https://github.com/openSUSE/osc>`_ in order to make it easier to create command line tools
with OSC Tiny.

.. versionadded:: 0.4.0
"""
from base64 import b64decode
from bz2 import decompress
from configparser import ConfigParser
import os
from pathlib import Path
import warnings

try:
    from osc import conf as _conf
except ImportError:
    _conf = None


def get_config_path():
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


def get_credentials(url=None):
    """
    Get credentials for Build Service instance identified by ``url``

    .. important::

        If the ``osc`` package is not installed, this function will only try to extract the username
        and password from the configuration file.

        Any credentials stored on a keyring will not be accessible!

    :param str url: URL of Build Service instance (including schema). If not specified, the value
                    from the ``apiurl`` parameter in the config file will be used.
    :return: (username, password)
    :raises ValueError: if config provides no credentials
    """
    if _conf is not None:
        # pylint: disable=protected-access
        parser = _conf.get_configParser()
        url = url or parser["general"].get("apiurl", url)
        cred_mgr = _conf._get_credentials_manager(url, parser)
        username = _conf._extract_user_compat(parser, url, cred_mgr)
        if not username:
            raise ValueError("`osc` config provides no username for URL {}".format(url))
        password = cred_mgr.get_password(url, username, defer=False)
        if not password:
            raise ValueError("`osc` config provides no password for URL {}".format(url))
        return username, password

    warnings.warn("`osc` is not installed. Not all configuration backends of `osc` will be "
                  "available.")
    parser = ConfigParser()
    url = url or parser["general"].get("apiurl", url)
    path = get_config_path()
    parser.read((path))

    if url not in parser.sections():
        raise ValueError("`osc` config has no section for URL {}".format(url))

    username = parser[url].get("user", None)
    if not username:
        raise ValueError("`osc` config provides no username for URL {}".format(url))

    password = parser[url].get("pass", None)
    if not password:
        password = parser[url].get("passx", None)
        if password:
            return username, decompress(b64decode(password.encode("ascii"))).decode("ascii")

    raise ValueError("`osc` config provides no password for URL {}".format(url))
