"""
Models for Staging
^^^^^^^^^^^^^^^^^^

.. versionadded:: 0.9.0
"""
# pylint: disable=missing-class-docstring,missing-function-docstring
import enum
import typing

from lxml.objectify import ObjectifiedElement

from ..models import E


class ExcludedRequest(typing.NamedTuple):
    id: int
    description: typing.Optional[str] = None

    def asdict(self) -> typing.Dict[str, str]:
        d = {"id": str(self.id)}
        if self.description:
            d["description"] = self.description

        return d

    def asxml(self) -> ObjectifiedElement:
        return E.request(**self.asdict())


class CheckState(enum.Enum):
    PENDING = "pending"
    ERROR = "error"
    FAILURE = "failure"
    SUCCESS = "success"


class CheckReport(typing.NamedTuple):
    name: str
    required: bool
    state: CheckState
    short_description: typing.Optional[str] = None
    url: typing.Optional[str] = None

    @property
    def required_str(self) -> str:
        return "true" if self.required else "false"

    def _optional_fields(self) -> typing.Generator[typing.Tuple[str, str], None, None]:
        for key in ('url', 'short_description'):
            value = getattr(self, key, None)
            if value:
                yield key, str(value)

    def asdict(self) -> typing.Dict[str, str]:
        d = {"name": self.name, "required": self.required_str,
             "state": self.state.value}

        for key, value in self._optional_fields():
            d[key] = value

        return d

    def asxml(self) -> ObjectifiedElement:
        sub_elems = [E.state(self.state.value)]
        for key, value in self._optional_fields():
            _E = getattr(E, key)
            sub_elems.append(_E(value))

        return E.check(*sub_elems, name=self.name, required=self.required_str)
