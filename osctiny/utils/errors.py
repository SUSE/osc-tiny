"""
Exception base classes and utilities
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
"""
import typing
from warnings import warn

from requests import HTTPError, Response

from .xml import get_objectified_xml


def get_http_error_details(error: typing.Union[HTTPError, Response]) -> str:
    """
    Extract user-friendly error message from exception

    .. versionadded:: 0.8.0
    """
    if isinstance(error, HTTPError):
        response = error.response
    elif isinstance(error, Response):
        response = error
    else:
        raise TypeError("Expected a Response of HTTPError instance!")

    try:
        xml_obj = get_objectified_xml(response)
    except Exception as error2:
        warn(message=f"Failed to extract error message due to another error: {error2}",
             category=RuntimeWarning)
    else:
        summary = xml_obj.find("summary")
        if summary is not None:
            return summary.text

    return f"Server replied with: {response.status_code} {response.reason}"


class OscError(Exception):
    """
    Base class for exceptions to be raised by ``osctiny``
    """
