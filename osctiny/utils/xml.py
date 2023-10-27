"""
XML parsing
^^^^^^^^^^^

.. versionadded:: 0.8.0
"""
import re
import threading
import typing

from lxml.etree import XMLParser
from lxml.objectify import fromstring, makeparser, ObjectifiedElement
from requests import Response


THREAD_LOCAL = threading.local()


def get_xml_parser() -> XMLParser:
    """
    Get a parser object

    .. versionchanged:: 0.8.0

        Carved out from the ``Osc`` class
    """
    if not hasattr(THREAD_LOCAL, "parser"):
        THREAD_LOCAL.parser = makeparser(huge_tree=True)

    return THREAD_LOCAL.parser


def get_objectified_xml(response: typing.Union[Response, str]) -> ObjectifiedElement:
    """
    Return API response as an XML object

    .. versionchanged:: 0.1.6

        Allow parsing of "huge" XML inputs

    .. versionchanged:: 0.2.4

        Allow ``response`` to be a string

    .. versionchanged:: 0.8.0

        Carved out from ``Osc`` class

    :param response: An API response or XML string
    :rtype response: :py:class:`requests.Response`
    :return: :py:class:`lxml.objectify.ObjectifiedElement`
    """
    if isinstance(response, str):
        text = response
    elif isinstance(response, Response):
        text = response.text
    else:
        raise TypeError(f"Expected a string or response object. Got  {type(response)} instead.")

    parser = get_xml_parser()

    try:
        return fromstring(text, parser)
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
