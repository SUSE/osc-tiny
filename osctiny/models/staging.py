"""
Models for Staging
^^^^^^^^^^^^^^^^^^
"""
# pylint: disable=missing-class-docstring,missing-function-docstring
import enum
import typing


class ExcludedRequest(typing.NamedTuple):
    id: int
    description: typing.Optional[str] = None

    def asdict(self) -> typing.Dict[str, str]:
        d = {"id": str(self.id)}
        if self.description:
            d["description"] = self.description

        return d


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
