# -*- coding: utf-8 -*-
"""
Changelog
^^^^^^^^^

Parser and generator for SUSE/OpenBuildService style changelog files.

This parser/generator is a reference implementation of the ``vc`` bash script
from the openSUSE:Tools ``build`` package. See:
`<https://build.opensuse.org/package/show/openSUSE:Tools/build>`_

.. versionadded:: 0.1.11
"""
from datetime import datetime
from io import TextIOBase
import re
import warnings

from dateutil.parser import parse
from pytz import _UTC


def is_aware(timestamp):
    """
    Check whether timestamp is timezone aware

    :param timestamp: :py:class:`datetime.datetime`
    :return: ``True``, if timestamp is tz-aware
    """
    return timestamp.tzinfo is not None \
           and timestamp.tzinfo.utcoffset(timestamp) is not None


class Entry:
    """
    Representation of a complete changelog entry

    .. py:attribute:: timestamp

        Timestamp of the entry as a :py:class:`datetime.datetime` object. If no
        value is provided during initialization,
        :py:func:`datetime.datetime.now` is used instead.

    .. py:attribute:: packager

        Email and name of the packager. Valid formats are:

        * ``email@example.com``
        * ``<email@example.com>``
        * ``full name <email@example.com>``

    .. py:attribute:: content

        All lines until the beginning of the next entry; except empty lines at
        the beginning and end
    """
    timestamp = None
    packager = None
    content = ""
    default_tz = _UTC()

    def __init__(self, timestamp=None, packager=None, content=""):
        if not isinstance(timestamp, datetime) and timestamp is not None:
            raise TypeError("`timestamp` needs to be a datetime object!")
        if timestamp and not is_aware(timestamp):
            raise ValueError("`timestamp` is not timezone-aware!")
        self.timestamp = timestamp or self.now()
        self.packager = packager
        self.content = content

    def __bool__(self):
        return bool(self.timestamp and self.packager and self.content)

    def __len__(self):
        return 1 if self.timestamp and self.packager and self.content else 0

    def now(self):
        """
        Return current UTC timestamp

        :return: :py:class:`datetime.datetime`
        """
        return datetime.now(tz=self.default_tz)

    @property
    def formatted_timestamp(self):
        """
        Return properly formatted timestamp

        :return: str
        """
        if not isinstance(self.timestamp, datetime):
            return self.timestamp

        return self.timestamp\
            .astimezone(self.default_tz)\
            .strftime("%a %b %d %H:%M:%S %Z %Y")

    def __str__(self):
        return "{sep}\n{self.formatted_timestamp} - {self.packager}\n\n" \
               "{self.content}\n\n".format(sep="-" * 67, self=self)

    def __unicode__(self):
        return self.__str__()


class ChangeLog:
    """
    Provider of capabilities to parse and write a ``.changes`` file

    Parsing and starting a new ``.changes`` file should be intuitive. In order
    to append or edit entries use this recipe:

    .. code:: python

        cl = ChangeLog.parse(path="/path/to/file", generative=False)
        cl.entries.append(Entry(...))
        cl.write()

    .. py:attribute:: entry_factory

        A class used to store entry data.

        **Example**: :py:class:`Entry` could be extended to provide a read-only
        property to find bug references inside the entry's content.
    """
    additional_tzinfos = {}
    entry_factory = Entry
    entries = None
    patterns = {
        "init": re.compile(r"^-+$"),
        "header": re.compile(
            r"^(?P<timestamp>[A-Za-z]{3,} [A-Za-z]{3,} [0-9: ]+ [A-Z]+ \d{4,}) "
            r"- (?P<packager>.*)\s*$")
    }

    def __init__(self):
        self.entries = []

    def _parse(self, handle):
        """
        Actual method for parsing.

        .. important::

            Please do not call this method directly. Use :py:meth:`parse`
            instead.

        :param handle: An open and iterable (file) handle
        :type handle: Any derived object of :py:class:`io.IOBase`
        """
        # pylint: disable=too-many-branches,consider-using-with
        entry = self.entry_factory()

        if isinstance(handle, TextIOBase):
            handle.seek(0)
        elif isinstance(handle, (str, bytes)):
            handle = open(handle, "r")  # pylint: disable=consider-using-with
        else:
            raise TypeError("Unexpected type for 'path': {}".format(
                type(handle)))

        try:
            for line in handle:
                match = self.patterns["init"].match(line)
                if match:
                    if entry:
                        # We are at the beginning of a new entry. Time to emit
                        # the finished one.
                        yield entry
                    entry = self.entry_factory()
                    continue

                match = self.patterns["header"].match(line)
                if match:
                    try:
                        entry.timestamp = parse(match.group("timestamp"),
                                                ignoretz=False,
                                                tzinfos=self.additional_tzinfos)
                    except ValueError as error:
                        warnings.warn(
                            "Cannot parse changelog entry's timestamp: "
                            "'{}'".format(error))
                        entry.timestamp = match.group("timestamp")
                    else:
                        # Assuming UTC may not be correct, but beats dealing
                        # with a mix of tz-aware and naive datetime objects
                        if not is_aware(entry.timestamp):
                            entry.timestamp = entry.default_tz.localize(
                                parse(match.group("timestamp"), ignoretz=True,)
                            )
                    entry.packager = match.group("packager")
                    continue

                if not line.strip():
                    continue

                if entry.content:
                    entry.content += "\n"

                entry.content += line.rstrip()

            if entry:
                # The last entry of the file is emitted explicitly
                yield entry
        finally:
            handle.close()

    @classmethod
    def parse(cls, path, generative=True):
        """
        Parse a changes file

        The changes file to parse may be specified by it's path or as an already
        open file handle (aka. subclass of :py:class:`io.TextIOBase`).

        Use this method to initialize a new instance of :py:class:`ChangeLog`
        like this:

        .. code:: python

            cl = ChangeLog.parse(path="/path/to/file")
            for entry in cl.entries:
                print(entry)

        :param path: If a path is supplied as a string, the file will be opened
                     for reading. If a subclass of :py:class:`io.TextIOBase` is
                     provided, this method assumes that it is opened for
                     reading.
        :type path: str or open file/stream handle
        :param bool generative: If set to ``True`` (default), changelog entries
                                are parsed on the fly using a generator.
                                Otherwise all entries are parsed immediately and
                                stored in an iterable.
        :return: An instance of ``ChangeLog``
        :raises TypeError: if ``path`` is not a string or a subclass of
                           :py:class:`io.TextIOBase`
        """
        new = cls()

        # pylint: disable=protected-access
        if generative:
            new.entries = new._parse(path)
        else:
            new.entries = list(new._parse(path))

        return new

    def write(self, path):
        """
        Write entries to file/stream

        This method can write to files and any other stream derived from
        :py:class:`io.IOBase`.

        :param path: Path to file or open, writable handle
        :type path: str or  :py:class:`io.IOBase`
        """
        def _wrapped(handle):
            for entry in sorted(self.entries, key=lambda x: x.timestamp,
                                reverse=True):
                handle.write(str(entry))

        if isinstance(path, TextIOBase):
            _wrapped(path)
        elif isinstance(path, (str, bytes)):
            with open(path, "w") as handle:
                _wrapped(handle)
        else:
            raise TypeError("Unexpected type for 'path': {}".format(type(path)))
