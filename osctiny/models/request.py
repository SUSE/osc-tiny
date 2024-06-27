"""
Models for requests
^^^^^^^^^^^^^^^^^^^

.. versionadded:: 0.10.0
"""
# pylint: disable=missing-function-docstring,no-member
# Note: The `no-member` rule needs to be disabled due to this bug:
#       https://github.com/pylint-dev/pylint/issues/7891
import enum
import typing

from lxml.objectify import ObjectifiedElement

from . import E


class ActionType(enum.Enum):
    """
    Request action types as defined in OpenBuildService
    """
    ADD_ROLE = "add_role"
    CHANGE_DEVEL = "change_devel"
    DELETE = "delete"
    MAINTENANCE_INCIDENT = "maintenance_incident"
    MAINTENANCE_RELEASE = "maintenance_release"
    RELEASE = "release"
    SET_BUGOWNER = "set_bugowner"
    SUBMIT = "submit"


class Person(typing.NamedTuple):
    """
    Person model for use in actions
    """
    name: str

    def asxml(self) -> ObjectifiedElement:
        return E.person(name=self.name)


class Source(typing.NamedTuple):
    """
    Source for an action
    """
    project: str
    package: str
    rev: typing.Optional[str] = None

    def asxml(self) -> ObjectifiedElement:
        return E.source(**{field: getattr(self, field)
                           for field in self._fields
                           if getattr(self, field, None) is not None})


class Target(typing.NamedTuple):
    """
    Target for an action
    """
    project: str
    package: str
    releaseproject: typing.Optional[str] = None

    def asxml(self) -> ObjectifiedElement:
        return E.target(**{field: getattr(self, field)
                           for field in self._fields
                           if getattr(self, field, None) is not None})


class Action(typing.NamedTuple):
    """
    Request action
    """
    type: ActionType
    target: Target
    person: typing.Optional[Person] = None
    source: typing.Optional[Source] = None

    def asxml(self) -> ObjectifiedElement:
        sub_elems = [self.target.asxml()]
        for field in (self.person, self.source):
            if field is not None:
                sub_elems.append(field.asxml())
        return E.action(*sub_elems, type=self.type.value)


class By(enum.Enum):
    """
    Types by which reviews can be assigned
    """
    USER = "by_user"
    GROUP = "by_group"
    PROJECT = "by_project"
    PACKAGE = "by_package"


class Review(typing.NamedTuple):
    """
    Assign a review
    """
    by: By
    name: str

    def asxml(self) -> ObjectifiedElement:
        return E.review(**{self.by.value: self.name})
