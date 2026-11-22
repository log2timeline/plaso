"""Text parser plugin for Apache HTTP Server 2.4 error log files.

Also see:
  https://httpd.apache.org/docs/2.4/logs.html#errorlog
  https://httpd.apache.org/docs/2.4/mod/core.html#errorlogformat
"""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class ApacheErrorLogEventData(events.EventData):
    """Apache error log event data.

    Attributes:
      client_address (str): address of the client that made the request, as
          written in the log entry, which can include the port.
      level (str): severity level of the message, such as "error".
      message_body (str): message body.
      module (str): name of the module that produced the message, such as
          "core".
      process_identifier (int): process identifier (PID).
      recorded_time (dfdatetime.DateTimeValues): date and time the log entry
          was recorded.
      thread_identifier (int): thread identifier (TID).
    """

    DATA_TYPE = "apache:error_log:entry"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.client_address = None
        self.level = None
        self.message_body = None
        self.module = None
        self.process_identifier = None
        self.recorded_time = None
        self.thread_identifier = None


class ApacheErrorLogTextPlugin(interface.TextPlugin):
    """Text parser plugin for Apache HTTP Server 2.4 error log files."""

    NAME = "apache_error"
    DATA_FORMAT = "Apache error log (error.log) file"

    ENCODING = "utf-8"

    _MONTH_DICT = {
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    }

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

    _THREE_LETTERS = pyparsing.Word(pyparsing.alphas, exact=3)

    # Date and time values are formatted as: [Fri Sep 09 10:42:29.902022 2011]
    _DATE_TIME = (
        pyparsing.Suppress("[")
        + pyparsing.Group(
            pyparsing.Suppress(_THREE_LETTERS)
            + _THREE_LETTERS
            + _TWO_DIGITS
            + _TWO_DIGITS
            + pyparsing.Suppress(":")
            + _TWO_DIGITS
            + pyparsing.Suppress(":")
            + _TWO_DIGITS
            + pyparsing.Suppress(".")
            + _SIX_DIGITS
            + _FOUR_DIGITS
        ).set_results_name("date_time")
        + pyparsing.Suppress("]")
    )

    _LEVEL = pyparsing.one_of(
        [
            "emerg",
            "alert",
            "crit",
            "error",
            "warn",
            "notice",
            "info",
            "debug",
            "trace1",
            "trace2",
            "trace3",
            "trace4",
            "trace5",
            "trace6",
            "trace7",
            "trace8",
        ]
    )

    # The module and severity level are formatted as: [core:error]
    # The module name can be empty, for example: [:error]
    _MODULE_AND_LEVEL = (
        pyparsing.Suppress("[")
        + pyparsing.Optional(
            pyparsing.Word(pyparsing.alphanums + "_").set_results_name("module")
        )
        + pyparsing.Suppress(":")
        + _LEVEL.set_results_name("level")
        + pyparsing.Suppress("]")
    )

    # The process and thread identifiers are formatted as:
    # [pid 35708:tid 4328636416] or [pid 35708]
    _PROCESS_AND_THREAD_IDENTIFIER = (
        pyparsing.Suppress("[pid")
        + _INTEGER.set_results_name("process_identifier")
        + pyparsing.Optional(
            pyparsing.Suppress(":tid") + _INTEGER.set_results_name("thread_identifier")
        )
        + pyparsing.Suppress("]")
    )

    # The client address is formatted as: [client 192.0.2.1:50432]
    _CLIENT_ADDRESS = (
        pyparsing.Suppress("[client")
        + pyparsing.Word(pyparsing.printables, exclude_chars="]").set_results_name(
            "client_address"
        )
        + pyparsing.Suppress("]")
    )

    _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

    _LOG_LINE = (
        _DATE_TIME
        + _MODULE_AND_LEVEL
        + _PROCESS_AND_THREAD_IDENTIFIER
        + pyparsing.Optional(_CLIENT_ADDRESS)
        + pyparsing.restOfLine().set_results_name("message_body")
        + _END_OF_LINE
    )

    _LINE_STRUCTURES = [("log_line", _LOG_LINE)]

    VERIFICATION_GRAMMAR = _LOG_LINE

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

        event_data = ApacheErrorLogEventData()
        event_data.client_address = self._GetValueFromStructure(
            structure, "client_address"
        )
        event_data.level = self._GetValueFromStructure(structure, "level")
        event_data.message_body = self._GetStringValueFromStructure(
            structure, "message_body"
        )
        event_data.module = self._GetValueFromStructure(structure, "module")
        event_data.process_identifier = self._GetValueFromStructure(
            structure, "process_identifier"
        )
        event_data.recorded_time = self._ParseTimeElements(time_elements_structure)
        event_data.thread_identifier = self._GetValueFromStructure(
            structure, "thread_identifier"
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
            (
                month_string,
                day_of_month,
                hours,
                minutes,
                seconds,
                microseconds,
                year,
            ) = time_elements_structure

            month = self._MONTH_DICT.get(month_string.lower(), 0)

            time_elements_tuple = (
                year,
                month,
                day_of_month,
                hours,
                minutes,
                seconds,
                microseconds,
            )
            date_time = dfdatetime_time_elements.TimeElementsInMicroseconds(
                time_elements_tuple=time_elements_tuple
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


text_parser.TextLogParser.RegisterPlugin(ApacheErrorLogTextPlugin)
