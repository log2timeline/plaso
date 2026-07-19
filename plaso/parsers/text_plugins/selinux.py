"""Text parser plugin for SELinux audit log (audit.log) files.

audit.log log line example:

type=AVC msg=audit(1105758604.519:420): avc: denied { getattr } for pid=5962
comm="httpd" path="/home/auser/public_html" dev=sdb2 ino=921135

Where msg=audit(1105758604.519:420) contains the number of seconds since January 1, 1970
00:00:00 UTC and the number of milliseconds after the dot for example: "seconds:
1105758604, milliseconds: 519".

The number after the timestamp (420 in the example) is a 'serial number' that can be
used to correlate multiple logs generated from the same event.
"""

import pyparsing

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.lib import definitions
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class SELinuxLogEventData(events.EventData):
    """SELinux log event data.

    Attributes:
      audit_login_identifier (str): audit login identifier (auid), the login
          user identifier that is retained across su and sudo.
      audit_serial (int): audit serial number, used to correlate the records
          that belong to a single audited event.
      audit_session_identifier (str): audit session identifier (ses).
      audit_type (str): audit type.
      executable (str): path of the executable (exe).
      exit_code (str): exit status of the system call (exit).
      group_identifier (str): group identifier (gid) of the process.
      last_written_time (dfdatetime.DateTimeValues): entry last written date and time.
      message_body (str): message body.
      parent_process_identifier (str): parent process identifier (ppid).
      pid (str): process identifier (PID) that created the SELinux log line.
      process_name (str): name of the process (comm).
      security_context (str): security context (subj) of the process, such as a
          SELinux or AppArmor label.
      success (str): whether the system call succeeded (success).
      system_call (str): system call (syscall).
      user_identifier (str): user identifier (uid) of the process.
    """

    DATA_TYPE = "selinux:line"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.audit_login_identifier = None
        self.audit_serial = None
        self.audit_session_identifier = None
        self.audit_type = None
        self.executable = None
        self.exit_code = None
        self.group_identifier = None
        self.last_written_time = None
        self.message_body = None
        self.parent_process_identifier = None
        self.pid = None
        self.process_name = None
        self.security_context = None
        self.success = None
        self.system_call = None
        self.user_identifier = None


class SELinuxTextPlugin(interface.TextPlugin):
    """Text parser plugin for SELinux audit log (audit.log) files."""

    NAME = "selinux"
    DATA_FORMAT = "SELinux audit log (audit.log) file"

    _INTEGER = pyparsing.Word(pyparsing.nums).set_parse_action(
        lambda tokens: int(tokens[0], 10)
    )

    _KEY_VALUE_GROUP = pyparsing.Group(
        pyparsing.Word(pyparsing.alphanums)
        + pyparsing.Suppress("=")
        + (pyparsing.QuotedString('"') ^ pyparsing.Word(pyparsing.printables))
    )

    _KEY_VALUE_DICT = pyparsing.Dict(pyparsing.ZeroOrMore(_KEY_VALUE_GROUP))

    _TIMESTAMP = pyparsing.Group(_INTEGER + pyparsing.Suppress(".") + _INTEGER)

    _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

    # A log line is formatted as: type=TYPE msg=audit([0-9]+\.[0-9]+:[0-9]+): .*
    _LOG_LINE = (
        pyparsing.Suppress("type=")
        + (
            pyparsing.Word(pyparsing.srange("[A-Z_]"))
            ^ pyparsing.Regex(r"UNKNOWN\[[0-9]+\]")
        ).set_results_name("type")
        + pyparsing.Suppress("msg=audit(")
        + _TIMESTAMP.set_results_name("timestamp")
        + pyparsing.Suppress(":")
        + _INTEGER.set_results_name("serial")
        + pyparsing.Suppress("):")
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
        if key == "log_line":
            time_elements_structure = self._GetValueFromStructure(
                structure, "timestamp"
            )

            # Try to parse the message body as key value pairs. Note that not all log
            # lines will be properly formatted key value pairs.
            message_body = self._GetValueFromStructure(
                structure, "message_body", default_value=""
            ).strip()

            # ENRICHED audit logs (the modern default on both Fedora/RHEL and Ubuntu)
            # append an interpreted suffix after a 0x1d (group separator) byte, for
            # example "... key=(null)\x1dARCH=x86_64 SYSCALL=execve AUID=...". Split it
            # off: the raw key=value body provides the fields and the raw numeric
            # identifiers are kept for offline soundness; the resolved suffix is used
            # only for the system call name, which is architecture and kernel specific
            # and hard to resolve from an offline image. RAW logs have no suffix.
            raw_body, _, enriched_body = message_body.partition("\x1d")
            raw_body = raw_body.strip()

            body_structure = self._KEY_VALUE_DICT.parse_string(raw_body)
            enriched_structure = self._KEY_VALUE_DICT.parse_string(enriched_body)

            event_data = SELinuxLogEventData()
            event_data.audit_serial = self._GetValueFromStructure(structure, "serial")
            event_data.audit_type = self._GetValueFromStructure(structure, "type")
            event_data.last_written_time = self._ParseTimeElements(
                time_elements_structure
            )
            event_data.message_body = raw_body or None

            if body_structure:
                event_data.audit_login_identifier = self._GetValueFromStructure(
                    body_structure, "auid"
                )
                event_data.audit_session_identifier = self._GetValueFromStructure(
                    body_structure, "ses"
                )
                event_data.executable = self._GetValueFromStructure(
                    body_structure, "exe"
                )
                event_data.exit_code = self._GetValueFromStructure(
                    body_structure, "exit"
                )
                event_data.group_identifier = self._GetValueFromStructure(
                    body_structure, "gid"
                )
                event_data.parent_process_identifier = self._GetValueFromStructure(
                    body_structure, "ppid"
                )
                event_data.pid = self._GetValueFromStructure(body_structure, "pid")
                event_data.process_name = self._GetValueFromStructure(
                    body_structure, "comm"
                )
                event_data.security_context = self._GetValueFromStructure(
                    body_structure, "subj"
                )
                event_data.success = self._GetValueFromStructure(
                    body_structure, "success"
                )
                event_data.system_call = self._GetValueFromStructure(
                    body_structure, "syscall"
                )
                event_data.user_identifier = self._GetValueFromStructure(
                    body_structure, "uid"
                )

            if enriched_structure:
                enriched_system_call = self._GetValueFromStructure(
                    enriched_structure, "SYSCALL"
                )
                if enriched_system_call:
                    event_data.system_call = enriched_system_call

            parser_mediator.ProduceEventData(event_data)

    def _ParseTimeElements(self, time_elements_structure):
        """Parses date and time elements of a log line.

        Args:
          time_elements_structure (pyparsing.ParseResults): date and time elements
              of a log line.

        Returns:
          dfdatetime.PosixTimeInMilliseconds: date and time value.

        Raises:
          ParseError: if a valid date and time value cannot be derived from
              the time elements.
        """
        try:
            seconds, milliseconds = time_elements_structure

            timestamp = (seconds * definitions.MILLISECONDS_PER_SECOND) + milliseconds

            return dfdatetime_posix_time.PosixTimeInMilliseconds(timestamp=timestamp)

        except (TypeError, ValueError) as exception:
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

        time_elements_structure = self._GetValueFromStructure(structure, "timestamp")

        try:
            self._ParseTimeElements(time_elements_structure)
        except errors.ParseError:
            return False

        return True


text_parser.TextLogParser.RegisterPlugin(SELinuxTextPlugin)
