"""
Common model/type definitions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
"""
from io import BufferedReader, BytesIO, StringIO
import typing

from lxml.objectify import ElementMaker, ObjectifiedElement

#: XML maker without python type annotations
E = ElementMaker(annotate=False)

#: Acceptable types for HTTP parameters
ParamsType = typing.Union[bytes, str, StringIO, BytesIO, BufferedReader, dict, ObjectifiedElement]

#: Int or string with only numbers
IntOrString = typing.Union[int, str]
