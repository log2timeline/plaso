"""Text file parser plugin for VMware ESXi log files.

Also see:
  https://knowledge.broadcom.com/external/article/306962
  https://github.com/strozfriedberg/qelp/blob/main/src/qelp/esxi_to_csv.py
"""

import re

from dfdatetime import time_elements

import pyparsing

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class ESXiLogEventData(events.EventData):
    """VMware ESXi log event data.

    Attributes:
      component (str): component that generated the log entry.
      hostname (str): hostname of the ESXi system.
      message_body (str): message body.
      process_identifier (str): process identifier.
      severity (str): severity indicator.
      syslog_priority (str): syslog priority value.
      written_time (dfdatetime.DateTimeValues): date and time the log entry was
          written.
    """

    DATA_TYPE = "vmware:esxi:log:entry"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.component = None
        self.hostname = None
        self.message_body = None
        self.process_identifier = None
        self.severity = None
        self.syslog_priority = None
        self.written_time = None


class ESXiLogTextPlugin(interface.TextPluginWithLineContinuation):
    """Text file parser plugin for VMware ESXi log files."""

    NAME = "esxi_log"
    DATA_FORMAT = "VMware ESXi log file"

    ENCODING = "utf-8"

    _COMPONENTS = "auth|esxcli|hostd|rhttpproxy|shell|syslog|vmauthd|vmkernel|vobd|vpxa"
    _DATE_TIME = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z"
    _SEVERITY = r"\w+(?:\(\d+\))?"

    # Legacy hostd line, for example:
    # [2008-05-07 09:50:04.857 'SOAP' 2260 trivia] Received soap response
    _LEGACY_HOSTD_LINE = pyparsing.Regex(
        r"^\[(?P<date_time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?) "
        r"'(?P<component>[^']+)' (?P<process_identifier>\d+) "
        r"(?P<severity>\w+)\]\s*(?P<message_body>.*)$",
        flags=re.MULTILINE,
    ) + pyparsing.Suppress(pyparsing.LineEnd())

    # Remote syslog line, for example:
    # <166>2019-05-21T19:27:32.479Z esxi.example Hostd: info hostd[123] ...
    _REMOTE_SYSLOG_LINE = pyparsing.Regex(
        rf"^<(?P<syslog_priority>\d+)>(?P<date_time>{_DATE_TIME}) "
        rf"(?P<hostname>\S+) (?P<relay_component>\w+): "
        rf"(?P<severity>{_SEVERITY}) (?P<component>{_COMPONENTS})"
        r"(?:\[(?P<process_identifier>\d+)\])?[ :]\s*(?P<message_body>.*)$",
        flags=re.IGNORECASE | re.MULTILINE,
    ) + pyparsing.Suppress(pyparsing.LineEnd())

    # Userworld line with severity, for example:
    # 2021-01-04T16:02:17.168Z info hostd[123] ...
    _USERWORLD_LINE = pyparsing.Regex(
        rf"^(?P<date_time>{_DATE_TIME}) (?P<severity>{_SEVERITY}) "
        rf"(?P<component>{_COMPONENTS})"
        r"(?:\[(?P<process_identifier>\d+)\])?[ :]\s*(?P<message_body>.*)$",
        flags=re.IGNORECASE | re.MULTILINE,
    ) + pyparsing.Suppress(pyparsing.LineEnd())

    # VMkernel and similar component line, for example:
    # 2024-03-12T07:48:40.079Z In(182) vmkernel: ...
    _KERNEL_LINE = pyparsing.Regex(
        rf"^(?P<date_time>{_DATE_TIME}) (?P<severity>{_SEVERITY}) "
        rf"(?P<component>{_COMPONENTS}):\s*(?P<message_body>.*)$",
        flags=re.IGNORECASE | re.MULTILINE,
    ) + pyparsing.Suppress(pyparsing.LineEnd())

    # Shell line without severity, for example:
    # 2024-12-12T01:44:43.728Z shell[123]: [root]: ls -la
    _SHELL_LINE = pyparsing.Regex(
        rf"^(?P<date_time>{_DATE_TIME}) (?P<component>shell)"
        r"\[(?P<process_identifier>\d+)\]:\s*(?P<message_body>.*)$",
        flags=re.IGNORECASE | re.MULTILINE,
    ) + pyparsing.Suppress(pyparsing.LineEnd())

    _LINE_STRUCTURES = [
        ("legacy_hostd_line", _LEGACY_HOSTD_LINE),
        ("remote_syslog_line", _REMOTE_SYSLOG_LINE),
        ("userworld_line", _USERWORLD_LINE),
        ("kernel_line", _KERNEL_LINE),
        ("shell_line", _SHELL_LINE),
    ]

    VERIFICATION_GRAMMAR = (
        _LEGACY_HOSTD_LINE
        ^ _REMOTE_SYSLOG_LINE
        ^ _USERWORLD_LINE
        ^ _KERNEL_LINE
        ^ _SHELL_LINE
    )

    def __init__(self):
        """Initializes a text parser plugin."""
        super().__init__()
        self._event_data = None
        self._message_body_lines = None

    def _ParseFinalize(self, parser_mediator):
        """Finalizes parsing.

        Args:
          parser_mediator (ParserMediator): parser mediator.
        """
        if self._event_data:
            self._event_data.message_body = "\n".join(self._message_body_lines)
            parser_mediator.ProduceEventData(self._event_data)

        self._event_data = None
        self._message_body_lines = None

    def _ParseRecord(self, parser_mediator, key, structure):
        """Parses a pyparsing structure.

        Args:
          parser_mediator (ParserMediator): parser mediator.
          key (str): name of the parsed structure.
          structure (pyparsing.ParseResults): tokens from a parsed log line.
        """
        if key == "_line_continuation":
            if self._message_body_lines is not None:
                self._message_body_lines.append(structure.strip())
            return

        if self._event_data:
            self._event_data.message_body = "\n".join(self._message_body_lines)
            parser_mediator.ProduceEventData(self._event_data)

        date_time_string = self._GetValueFromStructure(structure, "date_time")
        date_time = time_elements.TimeElementsInMicroseconds()
        if key == "legacy_hostd_line":
            date_time.CopyFromDateTimeString(date_time_string)
            date_time.is_local_time = True
        else:
            date_time.CopyFromStringISO8601(date_time_string)

        event_data = ESXiLogEventData()
        event_data.component = self._GetValueFromStructure(structure, "component")
        event_data.hostname = self._GetValueFromStructure(structure, "hostname")
        event_data.process_identifier = self._GetValueFromStructure(
            structure, "process_identifier"
        )
        event_data.severity = self._GetValueFromStructure(structure, "severity")
        event_data.syslog_priority = self._GetValueFromStructure(
            structure, "syslog_priority"
        )
        event_data.written_time = date_time

        message_body = self._GetValueFromStructure(structure, "message_body")
        self._event_data = event_data
        self._message_body_lines = [message_body]

    def CheckRequiredFormat(self, parser_mediator, text_reader):
        """Checks if the log has the minimal structure required by the plugin.

        Args:
          parser_mediator (ParserMediator): parser mediator.
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
            date_time = time_elements.TimeElementsInMicroseconds()
            if date_time_string.endswith("Z"):
                date_time.CopyFromStringISO8601(date_time_string)
            else:
                date_time.CopyFromDateTimeString(date_time_string)
        except ValueError:
            return False

        return True


text_parser.TextLogParser.RegisterPlugin(ESXiLogTextPlugin)
