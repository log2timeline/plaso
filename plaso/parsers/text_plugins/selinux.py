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

import re

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
      account (str): account (acct) targeted by a user or authentication event.
      architecture (str): CPU architecture (arch); the resolved name (e.g.
          "x86_64") when the record is ENRICHED, otherwise the raw value.
      arguments (str): reconstructed command line of an executed program (the
          EXECVE argc/a0..aN arguments), hex-decoded and space-joined.
      audit_login_identifier (str): audit login identifier (auid), the login
          user identifier that is retained across su and sudo.
      audit_rule_key (str): audit rule key (key) identifying the rule that
          triggered the record.
      audit_serial (int): audit serial number, used to correlate the records
          that belong to a single audited event.
      audit_session_identifier (str): audit session identifier (ses).
      audit_type (str): audit type.
      executable (str): path of the executable (exe).
      exit_code (str): exit status of the system call (exit).
      file_mode (str): file mode (mode) of the path in a PATH record.
      file_path (str): file path (name) referenced by a PATH record.
      group_identifier (str): group identifier (gid) of the process.
      last_written_time (dfdatetime.DateTimeValues): entry last written date and time.
      message_body (str): message body.
      name_type (str): type of the path reference (nametype), such as NORMAL,
          PARENT, CREATE or DELETE.
      operation (str): operation (op) performed by a user or auth event.
      owner_group_identifier (str): group identifier that owns the file (ogid).
      owner_user_identifier (str): user identifier that owns the file (ouid).
      parent_process_identifier (str): parent process identifier (ppid).
      pid (str): process identifier (PID) that created the SELinux log line.
      process_name (str): name of the process (comm).
      proctitle (str): process title (proctitle), hex-decoded, with the NUL
          argument separators rendered as spaces.
      remote_address (str): source address (addr) of a remote auth event.
      remote_hostname (str): source hostname (hostname) of a remote auth event.
      result (str): result (res) of a user or auth event, such as success or
          failed.
      security_context (str): security context (subj) of the process, such as a
          SELinux or AppArmor label.
      success (str): whether the system call succeeded (success).
      system_call (str): system call (syscall).
      terminal (str): controlling terminal (terminal) of a user event.
      user_identifier (str): user identifier (uid) of the process.
      working_directory (str): process working directory (cwd) at exec time.
    """

    DATA_TYPE = "selinux:line"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.account = None
        self.architecture = None
        self.arguments = None
        self.audit_login_identifier = None
        self.audit_rule_key = None
        self.audit_serial = None
        self.audit_session_identifier = None
        self.audit_type = None
        self.executable = None
        self.exit_code = None
        self.file_mode = None
        self.file_path = None
        self.group_identifier = None
        self.last_written_time = None
        self.message_body = None
        self.name_type = None
        self.operation = None
        self.owner_group_identifier = None
        self.owner_user_identifier = None
        self.parent_process_identifier = None
        self.pid = None
        self.process_name = None
        self.proctitle = None
        self.remote_address = None
        self.remote_hostname = None
        self.result = None
        self.security_context = None
        self.success = None
        self.system_call = None
        self.terminal = None
        self.user_identifier = None
        self.working_directory = None


class SELinuxTextPlugin(interface.TextPlugin):
    """Text parser plugin for SELinux audit log (audit.log) files."""

    NAME = "selinux"
    DATA_FORMAT = "SELinux audit log (audit.log) file"

    _INTEGER = pyparsing.Word(pyparsing.nums).set_parse_action(
        lambda tokens: int(tokens[0], 10)
    )

    _KEY_VALUE_GROUP = pyparsing.Group(
        pyparsing.Word(pyparsing.alphanums + "-_")
        + pyparsing.Suppress("=")
        + (
            pyparsing.QuotedString('"')
            ^ pyparsing.QuotedString("'")
            ^ pyparsing.Word(pyparsing.printables)
        )
    )

    _KEY_VALUE_DICT = pyparsing.Dict(pyparsing.ZeroOrMore(_KEY_VALUE_GROUP))

    # EXECVE argument count, e.g. "argc=3".
    _ARGC_RE = re.compile(r"\bargc=(\d+)")

    # A hex-capable auditd value is either double-quoted (a literal) or a bare
    # even-length hex string (hex-encoded). Used for EXECVE arguments,
    # proctitle and PATH name, which auditd hex-encodes only when they contain
    # characters that would otherwise need escaping.
    _HEX_CAPABLE_VALUE = r'(?:"([^"]*)"|([0-9A-Fa-f]+))'

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

    # auditd sentinels that stand in for an absent value.
    _SENTINEL_VALUES = frozenset(["?", "(null)", "(none)"])

    def _DecodeHexValue(self, parser_mediator, hex_value):
        """Decodes a hex-encoded auditd value, preserving the original bytes.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          hex_value (str): hex-encoded value.

        Returns:
          str: decoded value; bytes that are not valid UTF-8 are kept as escaped
              byte values. An odd-length (hence not validly hex-encoded) value is
              returned unchanged.
        """
        if len(hex_value) % 2 != 0:
            return hex_value

        decoded_bytes = bytes.fromhex(hex_value)
        try:
            return decoded_bytes.decode("utf-8")
        except UnicodeDecodeError:
            parser_mediator.ProduceExtractionWarning(
                f"unable to decode hex-encoded audit value: {hex_value:s}"
            )
            return decoded_bytes.decode("utf-8", errors="backslashreplace")

    def _GetHexCapableField(self, parser_mediator, body, field_name):
        """Retrieves a hex-capable auditd field (quoted literal or hex-encoded).

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          body (str): raw message body.
          field_name (str): audit field name, such as "proctitle" or "name".

        Returns:
          str: decoded value, or None if the field is not present.
        """
        match = re.search(rf"\b{field_name:s}={self._HEX_CAPABLE_VALUE:s}", body)
        if match is None:
            return None

        literal_value, hex_value = match.groups()
        if literal_value is not None:
            return literal_value

        return self._DecodeHexValue(parser_mediator, hex_value)

    def _GetAuditValue(self, structure, name):
        """Retrieves a structure value, mapping auditd sentinels to None.

        Args:
          structure (pyparsing.ParseResults): parsed key=value structure.
          name (str): field name.

        Returns:
          str: value, or None if absent or an auditd sentinel ("?", "(null)",
              "(none)").
        """
        value = self._GetValueFromStructure(structure, name)
        if value in self._SENTINEL_VALUES:
            return None
        return value

    def _ReconstructArguments(self, parser_mediator, body):
        """Reconstructs the EXECVE command line from argc and a0..aN.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          body (str): raw message body.

        Returns:
          str: space-joined command line, or None if the body has no argc.
        """
        match = self._ARGC_RE.search(body)
        if match is None:
            return None

        arguments = []
        for index in range(int(match.group(1))):
            argument_match = re.search(
                rf"\ba{index:d}={self._HEX_CAPABLE_VALUE:s}", body
            )
            if argument_match is None:
                continue

            literal_value, hex_value = argument_match.groups()
            if literal_value is not None:
                arguments.append(literal_value)
            else:
                arguments.append(self._DecodeHexValue(parser_mediator, hex_value))

        return " ".join(arguments) or None

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
                event_data.architecture = self._GetValueFromStructure(
                    body_structure, "arch"
                )
                event_data.audit_login_identifier = self._GetValueFromStructure(
                    body_structure, "auid"
                )
                event_data.audit_rule_key = self._GetAuditValue(body_structure, "key")
                event_data.audit_session_identifier = self._GetValueFromStructure(
                    body_structure, "ses"
                )
                event_data.executable = self._GetValueFromStructure(
                    body_structure, "exe"
                )
                event_data.exit_code = self._GetValueFromStructure(
                    body_structure, "exit"
                )
                event_data.file_mode = self._GetValueFromStructure(
                    body_structure, "mode"
                )
                event_data.group_identifier = self._GetValueFromStructure(
                    body_structure, "gid"
                )
                event_data.name_type = self._GetValueFromStructure(
                    body_structure, "nametype"
                )
                event_data.owner_group_identifier = self._GetValueFromStructure(
                    body_structure, "ogid"
                )
                event_data.owner_user_identifier = self._GetValueFromStructure(
                    body_structure, "ouid"
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
                event_data.working_directory = self._GetValueFromStructure(
                    body_structure, "cwd"
                )

                event_data.arguments = self._ReconstructArguments(
                    parser_mediator, raw_body
                )
                event_data.file_path = self._GetHexCapableField(
                    parser_mediator, raw_body, "name"
                )

                proctitle = self._GetHexCapableField(
                    parser_mediator, raw_body, "proctitle"
                )
                if proctitle:
                    proctitle = proctitle.replace("\x00", " ")
                event_data.proctitle = proctitle

                message_value = self._GetValueFromStructure(body_structure, "msg")
                if message_value:
                    nested_structure = self._KEY_VALUE_DICT.parse_string(message_value)
                    event_data.account = self._GetValueFromStructure(
                        nested_structure, "acct"
                    )
                    event_data.operation = self._GetValueFromStructure(
                        nested_structure, "op"
                    )
                    event_data.remote_address = self._GetAuditValue(
                        nested_structure, "addr"
                    )
                    event_data.remote_hostname = self._GetAuditValue(
                        nested_structure, "hostname"
                    )
                    event_data.result = self._GetValueFromStructure(
                        nested_structure, "res"
                    )
                    event_data.terminal = self._GetAuditValue(
                        nested_structure, "terminal"
                    )

            if enriched_structure:
                enriched_system_call = self._GetValueFromStructure(
                    enriched_structure, "SYSCALL"
                )
                if enriched_system_call:
                    event_data.system_call = enriched_system_call

                enriched_architecture = self._GetValueFromStructure(
                    enriched_structure, "ARCH"
                )
                if enriched_architecture:
                    event_data.architecture = enriched_architecture

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
