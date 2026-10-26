"""Parser for group database (/etc/group) files.

Also see:
  https://man7.org/linux/man-pages/man5/group.5.html
"""

from dfvfs.helpers import text_file

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager


class LinuxGroupEventData(events.EventData):
    """Group database (/etc/group) entry event data.

    Attributes:
      group_identifier (int): group identifier (GID).
      group_name (str): name of the group.
      members (list[str]): names of the users that are member of the group.
    """

    DATA_TYPE = "linux:group:entry"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.group_identifier = None
        self.group_name = None
        self.members = None


class LinuxGroupParser(interface.FileObjectParser):
    """Parses group database (/etc/group) files."""

    NAME = "linux_group"
    DATA_FORMAT = "Group database (/etc/group) file"

    FILTERS = frozenset([interface.FileNameFileEntryFilter("group")])

    _MAXIMUM_LINE_SIZE = 65536

    # The maximum number of comment lines before the first entry, for example
    # MacOS stores a description of the file in comment lines.
    _MAXIMUM_NUMBER_OF_LEADING_COMMENT_LINES = 20

    def _ParseEntry(self, line):
        """Parses a group database entry.

        An entry is formatted as: group_name:password:GID:user_list

        Args:
          line (str): line that contains the entry, without end-of-line characters.

        Returns:
          LinuxGroupEventData: event data.

        Raises:
          ParseError: if the entry cannot be parsed.
        """
        values = line.split(":")
        if len(values) != 4:
            raise errors.ParseError(
                f"unsupported number of values: {len(values):d} in entry."
            )

        group_name, _, group_identifier, members = values

        if not group_name:
            raise errors.ParseError("missing group name in entry.")

        if len(line.split()) != 1:
            raise errors.ParseError("unsupported white space in entry.")

        # Note that MacOS uses negative group identifiers, such as -2 for nobody.
        digits = group_identifier.removeprefix("-")
        if not digits.isascii() or not digits.isdigit():
            raise errors.ParseError("unsupported group identifier in entry.")

        event_data = LinuxGroupEventData()
        event_data.group_identifier = int(group_identifier, 10)
        event_data.group_name = group_name
        event_data.members = [member for member in members.split(",") if member] or None

        return event_data

    def ParseFileObject(self, parser_mediator, file_object):
        """Parses a group database (/etc/group) file-like object.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          file_object (dfvfs.FileIO): file-like object.

        Raises:
          WrongParser: when the file cannot be parsed.
        """
        line_reader = text_file.TextFile(
            file_object, encoding="utf-8", end_of_line="\n"
        )
        first_entry = True
        line_number = 1
        number_of_comment_lines = 0

        try:
            line = line_reader.readline(size=self._MAXIMUM_LINE_SIZE)
        except UnicodeDecodeError as exception:
            raise errors.WrongParser(
                f"unable to read line: {line_number:d} with error: {exception!s}"
            )

        while line:
            if parser_mediator.abort:
                break

            line = line.rstrip("\r\n")

            if line.startswith("#"):
                number_of_comment_lines += 1

                if (
                    first_entry
                    and number_of_comment_lines
                    > self._MAXIMUM_NUMBER_OF_LEADING_COMMENT_LINES
                ):
                    raise errors.WrongParser(
                        f"more than {self._MAXIMUM_NUMBER_OF_LEADING_COMMENT_LINES:d} "
                        f"leading comment lines."
                    )

            elif line:
                try:
                    event_data = self._ParseEntry(line)

                except errors.ParseError as exception:
                    if first_entry:
                        raise errors.WrongParser(
                            f"unable to parse line: {line_number:d} with error: "
                            f"{exception!s}"
                        )

                    parser_mediator.ProduceWarning(
                        f"unable to parse line: {line_number:d} with error: "
                        f"{exception!s}"
                    )
                    event_data = None

                if event_data:
                    first_entry = False
                    parser_mediator.ProduceEventData(event_data)

            line_number += 1

            try:
                line = line_reader.readline(size=self._MAXIMUM_LINE_SIZE)
            except UnicodeDecodeError as exception:
                parser_mediator.ProduceWarning(
                    f"unable to read line: {line_number:d} with error: {exception!s}"
                )
                break

        if first_entry:
            raise errors.WrongParser("missing group database entries.")


manager.ParsersManager.RegisterParser(LinuxGroupParser)
