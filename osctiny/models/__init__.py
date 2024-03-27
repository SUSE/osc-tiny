"""
Common model/type definitions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
"""
from io import BufferedReader, BytesIO, StringIO
import typing

from lxml.objectify import ObjectifiedElement


ParamsType = typing.Union[bytes, str, StringIO, BytesIO, BufferedReader, dict, ObjectifiedElement]
IntOrString = typing.Union[int, str]
