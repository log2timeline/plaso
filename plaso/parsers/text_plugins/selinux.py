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
      account (str): name of the account (acct) that is the subject of a user,
          authentication or account management event, such as the account being
          authenticated or added. Note that this is the account the event acts on,
          where user_identifier is the user identifier of the process that caused
          the event.
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
      file_mode (int): file mode (mode) of the file, which includes the file type
          and the permissions, such as 0o100640 for a regular file that is
          readable and writable by its owner and readable by its group.
      file_path (str): file path (name) referenced by a PATH record.
      group_identifier (str): group identifier (gid) of the process.
      last_written_time (dfdatetime.DateTimeValues): entry last written date and time.
      message_body (str): message body.
      name_type (str): type of the path reference (nametype), such as NORMAL,
          PARENT, CREATE or DELETE.
      operation (str): operation (op) that is audited, such as
          "PAM:authentication", "add_rule" or "LOAD".
      operation_result (str): result (res) of the audited operation, either
          "success" or "failed", or "1" or "0" on record types such as
          CONFIG_CHANGE and LOGIN.
      owner_group_identifier (str): group identifier that owns the file (ogid).
      owner_user_identifier (str): user identifier that owns the file (ouid).
      parent_process_identifier (str): parent process identifier (ppid).
      pid (str): process identifier (PID) that created the SELinux log line.
      process_name (str): name of the process (comm).
      process_title (str): process title (proctitle) of the process, which
          contains the command line with its arguments separated by spaces.
      remote_address (str): source address (addr) of a remote event.
      remote_hostname (str): source hostname (hostname) of a remote event.
      security_context (str): security context (subj) of the process, such as a
          SELinux or AppArmor label.
      success (str): whether the system call succeeded (success).
      system_call (str): system call (syscall).
      terminal (str): controlling terminal (terminal) of the event.
      user_identifier (str): user identifier (uid) of the process.
      working_directory (str): working directory (cwd) of the process at
          execution time.
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
        self.operation_result = None
        self.owner_group_identifier = None
        self.owner_user_identifier = None
        self.parent_process_identifier = None
        self.pid = None
        self.process_name = None
        self.process_title = None
        self.remote_address = None
        self.remote_hostname = None
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

    # Values are deliberately not unquoted when parsed, so that a quoted value,
    # which is a literal, can be distinguished from an unquoted value, which is
    # hex-encoded.
    _KEY_VALUE_GROUP = pyparsing.Group(
        pyparsing.Word(pyparsing.alphanums + "-_")
        + pyparsing.Suppress("=")
        + (
            pyparsing.QuotedString('"', unquote_results=False)
            ^ pyparsing.QuotedString("'", unquote_results=False)
            ^ pyparsing.Word(pyparsing.printables)
        )
    )

    _KEY_VALUE_DICT = pyparsing.Dict(pyparsing.ZeroOrMore(_KEY_VALUE_GROUP))

    _HEX_DIGITS = frozenset("0123456789ABCDEFabcdef")

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
        """Decodes a hex-encoded value, preserving the original bytes.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          hex_value (str): hex-encoded value.

        Returns:
          tuple[str, bool]: decoded value, where bytes that are not valid UTF-8 are
              kept as escaped byte values, and value to indicate the value was
              corrupted. A value that is not validly hex-encoded is returned
              unchanged.
        """
        try:
            decoded_bytes = bytes.fromhex(hex_value)
        except ValueError:
            parser_mediator.ProduceWarning(
                f"unable to decode hex-encoded value: {hex_value:s}"
            )
            return hex_value, True

        try:
            return decoded_bytes.decode("utf-8"), False
        except UnicodeDecodeError:
            parser_mediator.ProduceWarning(
                f"unable to decode UTF-8 in hex-encoded value: {hex_value:s}"
            )
            return decoded_bytes.decode("utf-8", errors="backslashreplace"), True

    def _GetValues(self, body):
        """Retrieves the values of the fields in a message body.

        Audit records store fields such as "acct", "exe" and "res" either at the
        top level of the message body or inside a nested "msg" field, depending on
        the record type. The values of a nested "msg" field are therefore merged
        into the result, where they take precedence.

        Args:
          body (str): message body.

        Returns:
          dict[str, str]: value per field name, where a value of a quoted field is
              kept quoted.
        """
        values = self._KEY_VALUE_DICT.parse_string(body).as_dict()

        nested_body = values.get("msg", None)
        if nested_body and nested_body[0] == "'":
            values.update(
                self._KEY_VALUE_DICT.parse_string(nested_body[1:-1]).as_dict()
            )

        return values

    def _GetValue(self, values, name):
        """Retrieves the value of a field.

        Args:
          values (dict[str, str]): value per field name.
          name (str): field name.

        Returns:
          tuple[str, bool]: value, or None if the field is not present, its value
              is empty or its value is an auditd sentinel such as "?" or "(null)",
              and value to indicate the value was quoted.
        """
        value = values.get(name, None)
        if value is None:
            return None, False

        is_quoted = value[0] == '"'
        if is_quoted:
            value = value[1:-1]

        if not value or value in self._SENTINEL_VALUES:
            return None, False

        return value, is_quoted

    def _GetStringValue(self, values, name):
        """Retrieves the value of a field as a string.

        Args:
          values (dict[str, str]): value per field name.
          name (str): field name.

        Returns:
          str: value, or None if the field has no usable value.
        """
        value, _ = self._GetValue(values, name)
        return value

    def _GetEncodedStringValue(self, parser_mediator, values, name):
        """Retrieves the value of a field that auditd can store hex-encoded.

        auditd stores the value of these fields hex-encoded if it contains
        characters that would otherwise need to be escaped, such as a space, and
        quoted if not.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          values (dict[str, str]): value per field name.
          name (str): field name.

        Returns:
          tuple[str, bool]: value, or None if the field has no usable value, and
              value to indicate the value was corrupted.
        """
        value, is_quoted = self._GetValue(values, name)
        if value is None:
            return None, False

        # A quoted value is a literal, where an unquoted value is hex-encoded.
        if is_quoted or not all(character in self._HEX_DIGITS for character in value):
            return value, False

        return self._DecodeHexValue(parser_mediator, value)

    def _GetArguments(self, parser_mediator, values):
        """Retrieves the command line of an executed program.

        The arguments of an EXECVE record are stored as a number of arguments
        (argc) and the individual arguments (a0 .. aN), which are joined with a
        space, as ausearch does.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          values (dict[str, str]): value per field name.

        Returns:
          tuple[str, bool]: command line, or None if the record has no arguments,
              and value to indicate a value was corrupted.
        """
        number_of_arguments = self._GetStringValue(values, "argc")
        if number_of_arguments is None:
            return None, False

        try:
            number_of_arguments = int(number_of_arguments, 10)
        except ValueError:
            parser_mediator.ProduceWarning(
                f"invalid number of arguments: {number_of_arguments:s}"
            )
            return None, True

        corrupted = False
        arguments = []
        for index in range(number_of_arguments):
            argument, value_corrupted = self._GetEncodedStringValue(
                parser_mediator, values, f"a{index:d}"
            )
            corrupted = corrupted or value_corrupted
            if argument is not None:
                arguments.append(argument)

        return " ".join(arguments) or None, corrupted

    def _GetFileMode(self, parser_mediator, values):
        """Retrieves the file mode of a PATH record.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          values (dict[str, str]): value per field name.

        Returns:
          tuple[int, bool]: file mode, or None if the record has no file mode, and
              value to indicate the value was corrupted.
        """
        file_mode = self._GetStringValue(values, "mode")
        if file_mode is None:
            return None, False

        try:
            return int(file_mode, 8), False
        except ValueError:
            parser_mediator.ProduceWarning(f"invalid file mode: {file_mode:s}")
            return None, True

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

            values = self._GetValues(raw_body)
            enriched_values = self._GetValues(enriched_body)

            corrupted = False

            event_data = SELinuxLogEventData()
            event_data.audit_serial = self._GetValueFromStructure(structure, "serial")
            event_data.audit_type = self._GetValueFromStructure(structure, "type")
            event_data.last_written_time = self._ParseTimeElements(
                time_elements_structure
            )
            event_data.message_body = raw_body or None

            if values:
                event_data.architecture = self._GetStringValue(values, "arch")
                event_data.audit_login_identifier = self._GetStringValue(values, "auid")
                event_data.audit_rule_key, value_corrupted = (
                    self._GetEncodedStringValue(parser_mediator, values, "key")
                )
                corrupted = corrupted or value_corrupted

                event_data.audit_session_identifier = self._GetStringValue(
                    values, "ses"
                )
                event_data.exit_code = self._GetStringValue(values, "exit")
                event_data.group_identifier = self._GetStringValue(values, "gid")
                event_data.name_type = self._GetStringValue(values, "nametype")
                event_data.operation = self._GetStringValue(values, "op")
                event_data.operation_result = self._GetStringValue(values, "res")
                event_data.owner_group_identifier = self._GetStringValue(values, "ogid")
                event_data.owner_user_identifier = self._GetStringValue(values, "ouid")
                event_data.parent_process_identifier = self._GetStringValue(
                    values, "ppid"
                )
                event_data.pid = self._GetStringValue(values, "pid")
                event_data.remote_address = self._GetStringValue(values, "addr")
                event_data.remote_hostname = self._GetStringValue(values, "hostname")
                event_data.security_context = self._GetStringValue(values, "subj")
                event_data.success = self._GetStringValue(values, "success")
                event_data.system_call = self._GetStringValue(values, "syscall")
                event_data.terminal = self._GetStringValue(values, "terminal")
                event_data.user_identifier = self._GetStringValue(values, "uid")

                event_data.file_mode, value_corrupted = self._GetFileMode(
                    parser_mediator, values
                )
                corrupted = corrupted or value_corrupted

                event_data.arguments, value_corrupted = self._GetArguments(
                    parser_mediator, values
                )
                corrupted = corrupted or value_corrupted

                for attribute_name, field_name in (
                    ("account", "acct"),
                    ("executable", "exe"),
                    ("file_path", "name"),
                    ("process_name", "comm"),
                    ("working_directory", "cwd"),
                ):
                    value, value_corrupted = self._GetEncodedStringValue(
                        parser_mediator, values, field_name
                    )
                    setattr(event_data, attribute_name, value)
                    corrupted = corrupted or value_corrupted

                process_title, value_corrupted = self._GetEncodedStringValue(
                    parser_mediator, values, "proctitle"
                )
                corrupted = corrupted or value_corrupted
                if process_title:
                    # The arguments in a process title are separated by a NUL
                    # character.
                    process_title = process_title.replace("\x00", " ")
                event_data.process_title = process_title

            if enriched_values:
                enriched_system_call = self._GetStringValue(enriched_values, "SYSCALL")
                if enriched_system_call:
                    event_data.system_call = enriched_system_call

                enriched_architecture = self._GetStringValue(enriched_values, "ARCH")
                if enriched_architecture:
                    event_data.architecture = enriched_architecture

            parser_mediator.ProduceEventData(event_data, corrupted=corrupted)

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
