"""Text parser plugin for Cisco Adaptive Security Appliance (ASA) log files.

Also see:
  https://www.cisco.com/c/en/us/td/docs/security/asa/syslog/asa-syslog.html
"""

import re

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class CiscoASALogEventData(events.EventData):
    """Cisco Adaptive Security Appliance (ASA) log event data.

    Attributes:
      hostname (str): hostname of the Cisco ASA device.
      message_body (str): message body.
      message_identifier (int): Cisco ASA syslog message identifier, such as
          722037.
      recorded_time (dfdatetime.DateTimeValues): date and time the log entry
          was recorded.
      severity (int): Cisco ASA syslog severity level, which ranges from 0
          (emergencies) to 7 (debugging).
    """

    DATA_TYPE = "cisco:asa:log:entry"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.hostname = None
        self.message_body = None
        self.message_identifier = None
        self.recorded_time = None
        self.severity = None


class CiscoASALogTextPlugin(interface.TextPlugin):
    """Text parser plugin for Cisco Adaptive Security Appliance (ASA) log files."""

    NAME = "cisco_asa"
    DATA_FORMAT = "Cisco Adaptive Security Appliance (ASA) log file"

    ENCODING = "utf-8"

    # Date and time values are formatted as: 2022-01-01T00:01:27+01:00
    _DATE_TIME = (
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})"
    )

    # Log line, for example:
    # 2022-01-01T00:01:27+01:00 asa5540-2 : %ASA-5-722037: Group <DfltGrpPolicy>
    # User <user> IP <192.0.2.1> SVC closing connection: DPD failure.
    _LOG_LINE = pyparsing.Regex(
        rf"^(?P<date_time>{_DATE_TIME}) (?P<hostname>[^\s:]+) : "
        r"%ASA-(?P<severity>[0-7])-(?P<message_identifier>\d{6}):"
        r"[ ]?(?P<message_body>.*)$",
        flags=re.MULTILINE,
    ) + pyparsing.Suppress(pyparsing.LineEnd())

    _LINE_STRUCTURES = [("log_line", _LOG_LINE)]

    VERIFICATION_GRAMMAR = _LOG_LINE

    VERIFICATION_LITERALS = ["%ASA-"]

    def _ParseDateTimeString(self, date_time_string):
        """Parses a date and time string.

        Args:
          date_time_string (str): date and time string in ISO 8601 format.

        Returns:
          dfdatetime.TimeElements: date and time value.

        Raises:
          ParseError: if a valid date and time value cannot be derived from
              the date and time string.
        """
        if "." in date_time_string:
            date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
        else:
            date_time = dfdatetime_time_elements.TimeElements()

        try:
            date_time.CopyFromStringISO8601(date_time_string)
        except (TypeError, ValueError) as exception:
            raise errors.ParseError(
                f"Unable to parse date and time string: {date_time_string!s} with "
                f"error: {exception!s}"
            )

        return date_time

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
        date_time_string = self._GetValueFromStructure(structure, "date_time")

        message_identifier = self._GetValueFromStructure(
            structure, "message_identifier"
        )
        severity = self._GetValueFromStructure(structure, "severity")

        event_data = CiscoASALogEventData()
        event_data.hostname = self._GetValueFromStructure(structure, "hostname")
        event_data.message_body = self._GetStringValueFromStructure(
            structure, "message_body"
        )
        event_data.message_identifier = int(message_identifier, 10)
        event_data.recorded_time = self._ParseDateTimeString(date_time_string)
        event_data.severity = int(severity, 10)

        parser_mediator.ProduceEventData(event_data)

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

        date_time_string = self._GetValueFromStructure(structure, "date_time")

        try:
            self._ParseDateTimeString(date_time_string)
        except errors.ParseError:
            return False

        return True


text_parser.TextLogParser.RegisterPlugin(CiscoASALogTextPlugin)
