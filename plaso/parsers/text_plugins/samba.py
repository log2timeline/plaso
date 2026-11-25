"""Text parser plugin for Samba log files.

This is a multi-line log format where every log entry starts with a header
line, followed by one or more message lines that are indented.

Also see:
  https://wiki.samba.org/index.php/Setting_up_Audit_Logging
  https://www.samba.org/samba/docs/current/man-html/smb.conf.5.html
"""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class SambaLogEventData(events.EventData):
    """Samba log event data.

    Attributes:
      debug_class (str): debug class of the log entry, such as "auth_audit".
      debug_level (int): debug level of the log entry.
      function_name (str): name of the function that wrote the log entry.
      message_body (str): message body.
      process_identifier (int): process identifier (PID).
      recorded_time (dfdatetime.DateTimeValues): date and time the log entry
          was recorded.
      source_file (str): path of the source file that wrote the log entry.
      source_line (int): line number in the source file that wrote the log entry.
    """

    DATA_TYPE = "samba:log:entry"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.debug_class = None
        self.debug_level = None
        self.function_name = None
        self.message_body = None
        self.process_identifier = None
        self.recorded_time = None
        self.source_file = None
        self.source_line = None


class SambaLogTextPlugin(interface.TextPlugin):
    """Text parser plugin for Samba log files."""

    NAME = "samba"
    DATA_FORMAT = "Samba log file"

    ENCODING = "utf-8"

    _INTEGER = pyparsing.Word(pyparsing.nums).set_parse_action(
        lambda tokens: int(tokens[0], 10)
    )

    _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).set_parse_action(
        lambda tokens: int(tokens[0], 10)
    )

    _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).set_parse_action(
        lambda tokens: int(tokens[0], 10)
    )

    _SIX_DIGITS = pyparsing.Word(pyparsing.nums, exact=6).set_parse_action(
        lambda tokens: int(tokens[0], 10)
    )

    # Date and time values are formatted as: 2017/07/04 21:07:41.410381
    # The fraction of second is only present if "debug hires timestamp" is set.
    _DATE_TIME = pyparsing.Group(
        _FOUR_DIGITS
        + pyparsing.Suppress("/")
        + _TWO_DIGITS
        + pyparsing.Suppress("/")
        + _TWO_DIGITS
        + _TWO_DIGITS
        + pyparsing.Suppress(":")
        + _TWO_DIGITS
        + pyparsing.Suppress(":")
        + _TWO_DIGITS
        + pyparsing.Optional(pyparsing.Suppress(".") + _SIX_DIGITS)
    ).set_results_name("date_time")

    # Process identifier, only present if "debug pid" is set, for example:
    # , pid=21757
    _PROCESS_IDENTIFIER = (
        pyparsing.Suppress(",")
        + pyparsing.Suppress("pid=")
        + _INTEGER.set_results_name("process_identifier")
    )

    # User and group identifiers, only present if "debug uid" is set, for
    # example: , effective(0, 0), real(0, 0)
    _USER_IDENTIFIERS = pyparsing.Suppress(
        pyparsing.Literal(",")
        + pyparsing.Literal("effective(")
        + _INTEGER
        + pyparsing.Literal(",")
        + _INTEGER
        + pyparsing.Literal(")")
        + pyparsing.Literal(",")
        + pyparsing.Literal("real(")
        + _INTEGER
        + pyparsing.Literal(",")
        + _INTEGER
        + pyparsing.Literal(")")
    )

    # Debug class, only present if "debug class" is set, for example:
    # , class=auth_audit
    _DEBUG_CLASS = (
        pyparsing.Suppress(",")
        + pyparsing.Suppress("class=")
        + pyparsing.Word(pyparsing.alphanums + "_").set_results_name("debug_class")
    )

    # The source location is formatted as: ../auth/auth_log.c:848(log_json)
    _SOURCE_LOCATION = pyparsing.Regex(
        r"(?P<source_file>[^\s:]+):(?P<source_line>[0-9]+)"
        r"\((?P<function_name>[^\s()]*)\)"
    )

    _HEADER = (
        pyparsing.LineStart()
        + pyparsing.Suppress("[")
        + _DATE_TIME
        + pyparsing.Suppress(",")
        + _INTEGER.set_results_name("debug_level")
        + pyparsing.Optional(_PROCESS_IDENTIFIER)
        + pyparsing.Optional(_USER_IDENTIFIERS)
        + pyparsing.Optional(_DEBUG_CLASS)
        + pyparsing.Suppress("]")
        + _SOURCE_LOCATION
    )

    # The message lines that follow the header are indented.
    _MESSAGE_LINES = pyparsing.Regex(r"(?:\n[ \t]+[^\n]*)+").leave_whitespace()

    _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

    _LOG_ENTRY = (
        _HEADER
        + pyparsing.Optional(_MESSAGE_LINES.set_results_name("message_lines"))
        + _END_OF_LINE
    )

    _LINE_STRUCTURES = [("log_entry", _LOG_ENTRY)]

    VERIFICATION_GRAMMAR = _HEADER + _END_OF_LINE

    def _ParseRecord(self, parser_mediator, key, structure):
        """Parses a pyparsing structure.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          key (str): name of the parsed structure.
          structure (pyparsing.ParseResults): tokens from a parsed log line.

        Raises:
          ParseError: if the structure cannot be parsed.
        """
        time_elements_structure = self._GetValueFromStructure(structure, "date_time")

        message_lines = self._GetValueFromStructure(
            structure, "message_lines", default_value=""
        )
        message_lines = [line.strip() for line in message_lines.split("\n")]
        message_body = "\n".join([line for line in message_lines if line])

        event_data = SambaLogEventData()
        event_data.debug_class = self._GetValueFromStructure(structure, "debug_class")
        event_data.debug_level = self._GetValueFromStructure(structure, "debug_level")
        event_data.function_name = (
            self._GetValueFromStructure(structure, "function_name") or None
        )
        event_data.message_body = message_body or None
        event_data.process_identifier = self._GetValueFromStructure(
            structure, "process_identifier"
        )
        event_data.recorded_time = self._ParseTimeElements(time_elements_structure)
        event_data.source_file = self._GetValueFromStructure(structure, "source_file")
        event_data.source_line = self._GetDecimalValueFromStructure(
            structure, "source_line"
        )

        parser_mediator.ProduceEventData(event_data)

    def _ParseTimeElements(self, time_elements_structure):
        """Parses date and time elements of a log line.

        Args:
          time_elements_structure (pyparsing.ParseResults): date and time elements
              of a log line.

        Returns:
          dfdatetime.TimeElements: date and time value.

        Raises:
          ParseError: if a valid date and time value cannot be derived from
              the time elements.
        """
        try:
            if len(time_elements_structure) == 6:
                year, month, day_of_month, hours, minutes, seconds = (
                    time_elements_structure
                )
                date_time = dfdatetime_time_elements.TimeElements(
                    time_elements_tuple=(
                        year,
                        month,
                        day_of_month,
                        hours,
                        minutes,
                        seconds,
                    )
                )

            else:
                year, month, day_of_month, hours, minutes, seconds, microseconds = (
                    time_elements_structure
                )
                date_time = dfdatetime_time_elements.TimeElementsInMicroseconds(
                    time_elements_tuple=(
                        year,
                        month,
                        day_of_month,
                        hours,
                        minutes,
                        seconds,
                        microseconds,
                    )
                )

            date_time.is_local_time = True

            return date_time

        except (IndexError, TypeError, ValueError) as exception:
            raise errors.ParseError(
                f"Unable to parse time elements with error: {exception!s}"
            )

    def CheckRequiredFormat(self, parser_mediator, text_reader):
        """Check if the log record has the minimal structure required by the plugin.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          text_reader (EncodedTextReader): text reader.

        Returns:
          bool: True if this is the correct plugin, False otherwise.
        """
        try:
            structure = self._VerifyString(text_reader.lines)
        except errors.ParseError:
            return False

        time_elements_structure = self._GetValueFromStructure(structure, "date_time")

        try:
            self._ParseTimeElements(time_elements_structure)
        except errors.ParseError:
            return False

        return True


text_parser.TextLogParser.RegisterPlugin(SambaLogTextPlugin)
