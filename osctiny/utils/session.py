"""
HTTP Session
^^^^^^^^^^^^

.. versionadded:: 0.10.2
"""
from base64 import b64encode
import os
from ssl import get_default_verify_paths
import threading
import typing

from requests import Session
from requests.adapters import HTTPAdapter
from requests.auth import AuthBase
import urllib3

from .cookies import CookieManager


class RetryPolicy(typing.NamedTuple):
    """
    Parameters for governing request retries
    """
    max_attempts: int = 6
    backoff_factor: float = 0.125
    backoff_max: float = 5.


def generate_session_id(username: str, url: str) -> str:
    """
    Generate a session ID unique to the user, remote host, process and thread.
    """
    session_hash = b64encode(f'{username}@{url}'.encode()).decode()
    return f"session_{session_hash}_{os.getpid()}_{threading.get_ident()}"


def generate_retry_policy(policy: RetryPolicy) -> urllib3.Retry:
    """
    Generate retry policy for HTTP requests
    """
    version = tuple(int(x) for x in urllib3.__version__.split("."))
    kwargs = {
        "connect": policy.max_attempts,
        "read": policy.max_attempts,
        "status": policy.max_attempts,
        "status_forcelist": [500, 502, 503, 504],
        "redirect": False,        # Don't limit redirects.
        "backoff_factor": policy.backoff_factor,
        "raise_on_status": False
    }

    # Older versions of Retry do not understand some parameters:
    if version < (1, 26, 0):
        kwargs.update({
            "method_whitelist": None,
        })
    else:
        new_kwargs = {
            "allowed_methods": None,  # Aka. allow all!
            "other": 0,  # Fail on all other errors.
        }
        if version >= (2, 0, 0):
            new_kwargs["backoff_max"] = policy.backoff_max
        kwargs.update(new_kwargs)

    return urllib3.Retry(**kwargs)


def init_session(auth: AuthBase, policy: typing.Optional[RetryPolicy] = None,
                 verify: typing.Union[str, bool, None] = None) -> Session:
    """
    Factory to initialize a session object.
    """
    session = Session()
    session.auth = auth
    session.cookies = CookieManager.get_jar()
    session.verify = verify if verify is not None else get_default_verify_paths().capath

    if policy:
        retries = generate_retry_policy(policy=policy)
        for proto in ('http://', 'https://'):
            session.mount(proto, HTTPAdapter(max_retries=retries))

    return session
