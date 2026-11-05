"""Parser for GTK recently used (recently-used.xbel) files.

Also see:
  https://www.freedesktop.org/wiki/Specifications/desktop-bookmark-spec/
"""

import os

from defusedxml import ElementTree

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager


class RecentlyUsedXBELEventData(events.EventData):
    """GTK recently used (recently-used.xbel) event data.

    Attributes:
      added_time (dfdatetime.DateTimeValues): date and time the bookmark was
          added.
      applications (list[str]): names of the applications that registered
          the bookmark.
      last_visited_time (dfdatetime.DateTimeValues): date and time the bookmark
          was last visited.
      mime_type (str): MIME type of the bookmarked resource.
      modification_time (dfdatetime.DateTimeValues): date and time the bookmark
          was last modified.
      uri (str): URI of the bookmarked resource.
    """

    DATA_TYPE = "linux:recently_used:entry"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.added_time = None
        self.applications = None
        self.last_visited_time = None
        self.mime_type = None
        self.modification_time = None
        self.uri = None


class RecentlyUsedXBELParser(interface.FileObjectParser):
    """Parses GTK recently used (recently-used.xbel) files."""

    NAME = "recently_used_xbel"
    DATA_FORMAT = "GTK recently used (recently-used.xbel) file"

    _HEADER_READ_SIZE = 512

    _BOOKMARK_NAMESPACE = "http://www.freedesktop.org/standards/desktop-bookmarks"

    _MIME_NAMESPACE = "http://www.freedesktop.org/standards/shared-mime-info"

    def _ParseDateTimeValue(self, parser_mediator, bookmark_node, name):
        """Parses a date and time value of a bookmark.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          bookmark_node (xml.etree.ElementTree.Element): bookmark XML node.
          name (str): name of the attribute that contains the date and time value.

        Returns:
          dfdatetime.TimeElementsInMicroseconds: date and time value or None if
              not available or not supported.
        """
        date_time_string = bookmark_node.get(name)
        if not date_time_string:
            return None

        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()

        try:
            date_time.CopyFromStringISO8601(date_time_string)
        except ValueError as exception:
            parser_mediator.ProduceWarning(
                f"unable to parse {name:s} date and time value: "
                f"{date_time_string!s} with error: {exception!s}"
            )
            return None

        return date_time

    def ParseFileObject(self, parser_mediator, file_object):
        """Parses a GTK recently used (recently-used.xbel) file-like object.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          file_object (dfvfs.FileIO): file-like object.

        Raises:
          WrongParser: when the file cannot be parsed.
        """
        data = file_object.read(self._HEADER_READ_SIZE)
        if not data.startswith(b"<?xml"):
            raise errors.WrongParser("Not a recently used file [not XML]")

        if b"<xbel" not in data:
            raise errors.WrongParser("Not a recently used file [missing XBEL root]")

        if self._BOOKMARK_NAMESPACE.encode("ascii") not in data:
            raise errors.WrongParser(
                "Not a recently used file [missing desktop bookmarks namespace]"
            )

        # For ElementTree to work we need to work on a file object with its current
        # offset at the start.
        file_object.seek(0, os.SEEK_SET)

        try:
            xml = ElementTree.parse(file_object)
        except (ElementTree.ParseError, ValueError) as exception:
            raise errors.WrongParser(
                f"Unable to parse recently used file with error: {exception!s}"
            )

        root_node = xml.getroot()
        if root_node.tag != "xbel":
            raise errors.WrongParser("Not a recently used file [wrong XML root key]")

        application_tag = f"{{{self._BOOKMARK_NAMESPACE:s}}}application"
        mime_type_tag = f"{{{self._MIME_NAMESPACE:s}}}mime-type"

        for bookmark_node in root_node.iterfind("bookmark"):
            applications = [
                application_node.get("name")
                for application_node in bookmark_node.iter(application_tag)
                if application_node.get("name")
            ]

            mime_type = None
            for mime_type_node in bookmark_node.iter(mime_type_tag):
                mime_type = mime_type_node.get("type")
                break

            event_data = RecentlyUsedXBELEventData()
            event_data.added_time = self._ParseDateTimeValue(
                parser_mediator, bookmark_node, "added"
            )
            event_data.applications = applications or None
            event_data.last_visited_time = self._ParseDateTimeValue(
                parser_mediator, bookmark_node, "visited"
            )
            event_data.mime_type = mime_type
            event_data.modification_time = self._ParseDateTimeValue(
                parser_mediator, bookmark_node, "modified"
            )
            event_data.uri = bookmark_node.get("href")

            parser_mediator.ProduceEventData(event_data)


manager.ParsersManager.RegisterParser(RecentlyUsedXBELParser)
