"""Text parser plugin for FreeDesktop.org Trash info files.

Also see:
  https://specifications.freedesktop.org/trash-spec/latest/
"""

from urllib import parse as urllib_parse

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class TrashInfoEventData(events.EventData):
    """FreeDesktop.org Trash info event data.

    Attributes:
      deletion_time (dfdatetime.DateTimeValues): date and time the file or
          directory was moved to the trash.
      original_path (str): original path of the file or directory, before it
          was moved to the trash.
    """

    DATA_TYPE = "linux:trash_info:entry"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.deletion_time = None
        self.original_path = None


class TrashInfoTextPlugin(interface.TextPlugin):
    """Text parser plugin for FreeDesktop.org Trash info files."""

    NAME = "trash_info"
    DATA_FORMAT = "FreeDesktop.org Trash info (.trashinfo) file"

    ENCODING = "utf-8"

    _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).set_parse_action(
        lambda tokens: int(tokens[0], 10)
    )

    _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).set_parse_action(
        lambda tokens: int(tokens[0], 10)
    )

    # Date and time values are formatted as: 2022-08-19T14:05:31
    _DATE_TIME = pyparsing.Group(
        _FOUR_DIGITS
        + pyparsing.Suppress("-")
        + _TWO_DIGITS
        + pyparsing.Suppress("-")
        + _TWO_DIGITS
        + pyparsing.Suppress("T")
        + _TWO_DIGITS
        + pyparsing.Suppress(":")
        + _TWO_DIGITS
        + pyparsing.Suppress(":")
        + _TWO_DIGITS
    ).set_results_name("date_time")

    _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

    _HEADER_LINE = pyparsing.Literal("[Trash Info]") + _END_OF_LINE

    _DELETION_DATE_LINE = (
        pyparsing.Suppress("DeletionDate")
        + pyparsing.Suppress("=")
        + _DATE_TIME
        + _END_OF_LINE
    )

    _PATH_LINE = (
        pyparsing.Suppress("Path")
        + pyparsing.Suppress("=")
        + pyparsing.restOfLine().set_results_name("path")
        + _END_OF_LINE
    )

    _LINE_STRUCTURES = [
        ("deletion_date_line", _DELETION_DATE_LINE),
        ("header_line", _HEADER_LINE),
        ("path_line", _PATH_LINE),
    ]

    # The first line of a Trash info file must be "[Trash Info]".
    VERIFICATION_GRAMMAR = _HEADER_LINE + (_DELETION_DATE_LINE ^ _PATH_LINE)

    VERIFICATION_LITERALS = ["[Trash Info]"]

    def __init__(self):
        """Initializes a text parser plugin."""
        super().__init__()
        self._event_data = None

    def _ParseFinalize(self, parser_mediator):
        """Finalizes parsing.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
        """
        if self._event_data:
            parser_mediator.ProduceEventData(self._event_data)
            self._event_data = None

    def _ParseRecord(self, parser_mediator, key, structure):
        """Parses a pyparsing structure.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          key (str): name of the parsed structure.
          structure (pyparsing.ParseResults): tokens from a parsed line.

        Raises:
          ParseError: if the structure cannot be parsed.
        """
        if key == "header_line":
            if self._event_data:
                raise errors.ParseError("Unsupported additional header line.")

            self._event_data = TrashInfoEventData()

        elif not self._event_data:
            raise errors.ParseError(f"Unsupported {key:s} before header line.")

        elif key == "deletion_date_line":
            time_elements_structure = self._GetValueFromStructure(
                structure, "date_time"
            )
            self._event_data.deletion_time = self._ParseTimeElements(
                time_elements_structure
            )

        elif key == "path_line":
            path = self._GetStringValueFromStructure(structure, "path")
            if path:
                # The path is escaped as in URLs (RFC 2396).
                path = urllib_parse.unquote(path)

            self._event_data.original_path = path

    def _ParseTimeElements(self, time_elements_structure):
        """Parses date and time elements of a line.

        Args:
          time_elements_structure (pyparsing.ParseResults): date and time elements
              of a line.

        Returns:
          dfdatetime.TimeElements: date and time value.

        Raises:
          ParseError: if a valid date and time value cannot be derived from
              the time elements.
        """
        try:
            year, month, day_of_month, hours, minutes, seconds = time_elements_structure

            time_elements_tuple = (year, month, day_of_month, hours, minutes, seconds)
            date_time = dfdatetime_time_elements.TimeElements(
                time_elements_tuple=time_elements_tuple
            )

            # Trash info files store date and time values in local time.
            date_time.is_local_time = True

            return date_time

        except (TypeError, ValueError) as exception:
            raise errors.ParseError(
                f"Unable to parse time elements with error: {exception!s}"
            )

    def _ResetState(self):
        """Resets stored values."""
        self._event_data = None

    def CheckRequiredFormat(self, parser_mediator, text_reader):
        """Check if the log record has the minimal structure required by the plugin.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          text_reader (EncodedTextReader): text reader.

        Returns:
          bool: True if this is the correct plugin, False otherwise.
        """
        if not text_reader.lines.startswith("[Trash Info]\n"):
            return False

        try:
            self._VerifyString(text_reader.lines)
        except errors.ParseError:
            return False

        self._ResetState()

        return True


text_parser.TextLogParser.RegisterPlugin(TrashInfoTextPlugin)
