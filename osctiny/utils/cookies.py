"""
Utilities for cookies
^^^^^^^^^^^^^^^^^^^^^

.. versionadded:: 0.10.2
"""
from http.cookiejar import LWPCookieJar
from io import StringIO
import os
from pathlib import Path

from .conf import _conf


class CookieManager:
    """
    Simplify handling of cookies
    """
    @staticmethod
    def get_cookie_path() -> Path:
        """
        Get path candidates where to expect a cookie file
        """
        if _conf is not None:
            try:
                try:
                    # New OSC config
                    return Path(_conf.config.cookiejar)
                except AttributeError:
                    # Backward compatibility to old OSC config style
                    # pylint: disable=protected-access
                    return Path(_conf._identify_osccookiejar())
            except:  # pylint: disable=broad-except,bare-except
                # If `osc` raises an exception we pretend like it does not exist.
                pass

        path_suffix = Path("osc", "cookiejar")
        return Path(os.getenv("XDG_STATE_HOME", "~/.local/state"))\
            .joinpath(path_suffix).expanduser()

    @classmethod
    def get_jar(cls) -> LWPCookieJar:
        """
        Get cookies from a persistent osc cookiejar, if it exists

        .. versionchanged:: 0.10.2
            Converted from function ``get_cookie_jar``
        """
        path = cls.get_cookie_path()
        if path.is_file():
            jar = LWPCookieJar(filename=str(path))  # compatibility for Python < 3.8
            jar.load()
            return jar

        return LWPCookieJar(filename=str(path))

    @classmethod
    def save_jar(cls, jar: LWPCookieJar) -> None:
        """
        Save cookies to a persistent osc cookiejar
        """
        # compatibility for Python < 3.8
        jar.save(filename=jar.filename or str(cls.get_cookie_path()))

    @staticmethod
    def set_cookie(jar: LWPCookieJar, cookie: str) -> None:
        """
        Read cookie data from string instead of loading from file
        """
        strio = StringIO(cookie)
        strio.seek(0)
        # pylint: disable=protected-access
        jar._really_load(f=strio, filename="", ignore_discard=True, ignore_expires=True)

    @staticmethod
    def get_cookie(jar: LWPCookieJar) -> str:
        """
        Return LWP cookie string with headers
        """
        return f"#LWP-Cookies-2.0\n{jar.as_lwp_str()}"
