"""Text parser plugin for vsftpd log files."""

import re

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class VsftpdLogEventData(events.EventData):
    """Vsftpd log event data.

    Attributes:
      added_time (dfdatetime.DateTimeValues): date and time the log entry
          was added.
      process_identifier (int): process identifier (PID).
      text (str): vsftpd log message.
      username (str): name of the user.
    """

    DATA_TYPE = "vsftpd:log"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.added_time = None
        self.process_identifier = None
        self.text = None
        self.username = None


class VsftpdTransferLogEventData(events.EventData):
    """Vsftpd transfer log (xferlog) event data.

    Attributes:
      access_mode (str): access mode of the user, where "a" represents
          anonymous, "g" guest and "r" real.
      added_time (dfdatetime.DateTimeValues): date and time the log entry
          was added.
      authenticated_user_identifier (str): user identifier returned by the
          authentication method, where "*" represents not available.
      authentication_method (str): authentication method, where "0" represents
          none and "1" RFC 931 authentication.
      completion_status (str): completion status of the transfer, where "c"
          represents complete and "i" incomplete.
      direction (str): direction of the transfer, where "i" represents
          incoming, "o" outgoing and "d" deleted.
      file_size (int): size of the transferred file in bytes.
      filename (str): name of the transferred file.
      remote_host (str): remote host name or IP address.
      service_name (str): name of the service.
      special_action_flag (str): special action flag, where "C" represents
          compressed, "U" uncompressed, "T" tar'ed and "_" no action.
      transfer_duration (int): duration of the transfer in seconds.
      transfer_type (str): transfer type, where "a" represents ASCII and "b"
          binary.
      username (str): name of the user, or the password of an anonymous user.
    """

    DATA_TYPE = "vsftpd:xferlog"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.access_mode = None
        self.added_time = None
        self.authenticated_user_identifier = None
        self.authentication_method = None
        self.completion_status = None
        self.direction = None
        self.file_size = None
        self.filename = None
        self.remote_host = None
        self.service_name = None
        self.special_action_flag = None
        self.transfer_duration = None
        self.transfer_type = None
        self.username = None


class VsftpdLogTextPlugin(interface.TextPlugin):
    """Text parser plugin for vsftpd log files."""

    NAME = "vsftpd"
    DATA_FORMAT = "vsftpd log file"

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

    _ONE_OR_TWO_DIGITS = pyparsing.Word(pyparsing.nums, max=2).set_parse_action(
        lambda tokens: int(tokens[0], 10)
    )

    _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).set_parse_action(
        lambda tokens: int(tokens[0], 10)
    )

    _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).set_parse_action(
        lambda tokens: int(tokens[0], 10)
    )

    _THREE_LETTERS = pyparsing.Word(pyparsing.alphas, exact=3)

    # Date and time values are formatted as: Mon Jun  6 18:43:28 2016
    _DATE_TIME = pyparsing.Group(
        _THREE_LETTERS
        + _THREE_LETTERS
        + _ONE_OR_TWO_DIGITS
        + _TWO_DIGITS
        + pyparsing.Suppress(":")
        + _TWO_DIGITS
        + pyparsing.Suppress(":")
        + _TWO_DIGITS
        + _FOUR_DIGITS
    )

    _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

    # Process identifier formatted as: [pid 3]
    _PROCESS_IDENTIFIER = (
        pyparsing.Suppress("[pid")
        + pyparsing.Word(pyparsing.nums)
        .set_parse_action(lambda tokens: int(tokens[0], 10))
        .set_results_name("process_identifier")
        + pyparsing.Suppress("]")
    )

    # Name of the user, when logged in, formatted as: [jean]
    _USERNAME = (
        pyparsing.Suppress("[")
        + pyparsing.CharsNotIn("]\n").set_results_name("username")
        + pyparsing.Suppress("]")
    )

    # Log line formatted as:
    # Mon Jun  6 18:43:32 2016 [pid 1] [jean] OK LOGIN: Client "192.168.1.9"
    _PROCESS_LOG_LINE = (
        _DATE_TIME.set_results_name("date_time")
        + _PROCESS_IDENTIFIER
        + pyparsing.Optional(_USERNAME)
        + pyparsing.restOfLine().set_results_name("text")
        + _END_OF_LINE
    )

    _LOG_LINE = (
        _DATE_TIME.set_results_name("date_time")
        + pyparsing.restOfLine().set_results_name("text")
        + _END_OF_LINE
    )

    # Transfer log line in the xferlog format, as defined by xferlog(5):
    # transfer-time remote-host file-size filename transfer-type
    # special-action-flag direction access-mode username service-name
    # authentication-method authenticated-user-id completion-status
    # The filename is matched up to the trailing fixed fields, so that it can
    # contain spaces.
    _TRANSFER_LOG_VALUES = pyparsing.Regex(
        (
            r"(?P<transfer_duration>[0-9]+) (?P<remote_host>\S+) "
            r"(?P<file_size>[0-9]+) (?P<filename>.+) (?P<transfer_type>[ab]) "
            r"(?P<special_action_flag>[CTU_]+) (?P<direction>[dio]) "
            r"(?P<access_mode>[agr]) (?P<username>\S+) (?P<service_name>\S+) "
            r"(?P<authentication_method>[01]) "
            r"(?P<authenticated_user_identifier>\S+) "
            r"(?P<completion_status>[ci])(?=\r?$)"
        ),
        flags=re.MULTILINE,
    )

    # Transfer log line formatted as:
    # Mon Jun  6 18:43:59 2016 1 192.168.1.9 7664 /home/jean/trains/a.jpg b _ i r
    # jean ftp 0 * c
    _TRANSFER_LOG_LINE = (
        _DATE_TIME.set_results_name("date_time") + _TRANSFER_LOG_VALUES + _END_OF_LINE
    )

    _LINE_STRUCTURES = [
        ("process_log_line", _PROCESS_LOG_LINE),
        ("transfer_log_line", _TRANSFER_LOG_LINE),
        ("log_line", _LOG_LINE),
    ]

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

        if key == "transfer_log_line":
            event_data = VsftpdTransferLogEventData()
            event_data.access_mode = self._GetStringValueFromStructure(
                structure, "access_mode"
            )
            event_data.added_time = self._ParseTimeElements(time_elements_structure)
            event_data.authenticated_user_identifier = (
                self._GetStringValueFromStructure(
                    structure, "authenticated_user_identifier"
                )
            )
            event_data.authentication_method = self._GetStringValueFromStructure(
                structure, "authentication_method"
            )
            event_data.completion_status = self._GetStringValueFromStructure(
                structure, "completion_status"
            )
            event_data.direction = self._GetStringValueFromStructure(
                structure, "direction"
            )
            event_data.file_size = int(
                self._GetStringValueFromStructure(structure, "file_size"), 10
            )
            event_data.filename = self._GetStringValueFromStructure(
                structure, "filename"
            )
            event_data.remote_host = self._GetStringValueFromStructure(
                structure, "remote_host"
            )
            event_data.service_name = self._GetStringValueFromStructure(
                structure, "service_name"
            )
            event_data.special_action_flag = self._GetStringValueFromStructure(
                structure, "special_action_flag"
            )
            event_data.transfer_duration = int(
                self._GetStringValueFromStructure(structure, "transfer_duration"), 10
            )
            event_data.transfer_type = self._GetStringValueFromStructure(
                structure, "transfer_type"
            )
            event_data.username = self._GetStringValueFromStructure(
                structure, "username"
            )

        else:
            event_data = VsftpdLogEventData()
            event_data.added_time = self._ParseTimeElements(time_elements_structure)
            event_data.text = self._GetStringValueFromStructure(structure, "text")

            if key == "process_log_line":
                event_data.process_identifier = self._GetValueFromStructure(
                    structure, "process_identifier"
                )
                event_data.username = self._GetStringValueFromStructure(
                    structure, "username"
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
            _, month_string, day_of_month, hours, minutes, seconds, year = (
                time_elements_structure
            )
            month = self._MONTH_DICT.get(month_string.lower(), 0)

            time_elements_tuple = (year, month, day_of_month, hours, minutes, seconds)
            date_time = dfdatetime_time_elements.TimeElements(
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


text_parser.TextLogParser.RegisterPlugin(VsftpdLogTextPlugin)
