"""Text parser plugin for syslog log files.

Also see:
  https://docs.rsyslog.com/doc//configuration/templates.html
"""

import re

from dfdatetime import time_elements as dfdatetime_time_elements

import pyparsing

from plaso.containers import events
from plaso.lib import dateless_helper
from plaso.lib import errors
from plaso.parsers import logger
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class SyslogCommentEventData(events.EventData):
    """Syslog comment event data.

    Attributes:
      last_written_time (dfdatetime.DateTimeValues): entry last written date and time.
      message_body (str): message body.
    """

    DATA_TYPE = "syslog:comment"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.last_written_time = None
        self.message_body = None


class SyslogLineEventData(events.EventData):
    """Syslog line event data.

    Attributes:
      facility (str): facility.
      hostname (str): hostname of the reporter.
      last_written_time (dfdatetime.DateTimeValues): entry last written date and time.
      message_body (str): message body.
      message_identifier (str): message identifier.
      pid (str): process identifier of the reporter.
      reporter (str): reporter.
      severity (str): severity.
    """

    DATA_TYPE = "syslog:line"

    def __init__(self, data_type=DATA_TYPE):
        """Initializes an event data attribute container.

        Args:
          data_type (Optional[str]): event data type indicator.
        """
        super().__init__(data_type=data_type)
        self.facility = None
        self.hostname = None
        self.last_written_time = None
        self.message_body = None
        self.message_identifier = None
        self.pid = None
        self.reporter = None
        self.severity = None


class SyslogCronTaskEventData(SyslogLineEventData):
    """Syslog cron task event data.

    Attributes:
      command (str): command executed.
      last_written_time (dfdatetime.DateTimeValues): entry last written date and time.
      username (str): name of user the command was executed.
    """

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.command = None
        self.last_written_time = None
        self.username = None


class SyslogCronTaskEndEventData(SyslogCronTaskEventData):
    """Syslog cron task end event data."""

    DATA_TYPE = "syslog:cron:task_end"


class SyslogCronTaskRunEventData(SyslogCronTaskEventData):
    """Syslog cron task run event data."""

    DATA_TYPE = "syslog:cron:task_run"


class SyslogSSHEventData(SyslogLineEventData):
    """SSH event data.

    Attributes:
      authentication_method (str): authentication method.
      fingerprint (str): fingerprint.
      ip_address (str): IP address.
      last_written_time (dfdatetime.DateTimeValues): entry last written date and time.
      port (str): port.
      protocol (str): protocol.
      username (str): name of user the command was executed.
    """

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.authentication_method = None
        self.fingerprint = None
        self.ip_address = None
        self.last_written_time = None
        self.port = None
        self.protocol = None
        self.username = None


class SyslogSSHClosedConnectionEventData(SyslogSSHEventData):
    """SSH closed connection event data.

    Attributes:
      is_authenticated (bool): True if sshd wrote the user name as an
          authenticated user, False if as a user that was still authenticating or
          as an invalid user, None if the message does not name a user.
      is_invalid_user (bool): True if sshd wrote the user name as an invalid user,
          which is a name that does not resolve to an account that is allowed to
          log in, None if the message does not name a user.
    """

    DATA_TYPE = "syslog:ssh:closed_connection"

    def __init__(self):
        """Initializes event data."""
        super().__init__()
        self.is_authenticated = None
        self.is_invalid_user = None


# TODO: merge separate SyslogSSHEventData classes.
class SyslogSSHLoginEventData(SyslogSSHEventData):
    """SSH login event data."""

    DATA_TYPE = "syslog:ssh:login"


class SyslogSSHFailedConnectionEventData(SyslogSSHEventData):
    """SSH failed connection event data.

    Attributes:
      is_invalid_user (bool): True if sshd wrote the user name as an invalid user,
          which is a name that does not resolve to an account that is allowed to
          log in.
    """

    DATA_TYPE = "syslog:ssh:failed_connection"

    def __init__(self):
        """Initializes event data."""
        super().__init__()
        self.is_invalid_user = None


class SyslogSSHInvalidUserEventData(SyslogSSHEventData):
    """SSH invalid user event data."""

    DATA_TYPE = "syslog:ssh:invalid_user"


class SyslogSSHOpenedConnectionEventData(SyslogSSHEventData):
    """SSH opened connection event data."""

    DATA_TYPE = "syslog:ssh:opened_connection"


class SyslogSSHReceivedDisconnectEventData(SyslogSSHEventData):
    """SSH received disconnect event data.

    Attributes:
      disconnect_reason (str): disconnect reason as sent by the peer.
      disconnect_reason_code (int): disconnect reason code as sent by the peer,
          see RFC 4253 section 11.1.
    """

    DATA_TYPE = "syslog:ssh:received_disconnect"

    def __init__(self):
        """Initializes event data."""
        super().__init__()
        self.disconnect_reason = None
        self.disconnect_reason_code = None


class SyslogSudoCommandEventData(SyslogLineEventData):
    """Syslog sudo command event data.

    Attributes:
      account (str): name of the account the command was run as, the USER= field.
      command_line (str): command line, the COMMAND= field, as sudo logged it,
          where control characters are written in octal with a leading "#", a
          space in the command path is written as "#040", an argument that
          contains a space is enclosed in single quotes and a single quote or
          backslash in an argument is escaped with a backslash, see sudoers(5).
      group_name (str): name of the group the command was run as, the GROUP=
          field.
      last_written_time (dfdatetime.DateTimeValues): entry last written date and
          time.
      terminal (str): terminal sudo was run from, the TTY= field.
      username (str): name of the user that ran sudo.
      working_directory (str): working directory, the PWD= field.
    """

    DATA_TYPE = "syslog:sudo:command"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.account = None
        self.command_line = None
        self.group_name = None
        self.last_written_time = None
        self.terminal = None
        self.username = None
        self.working_directory = None


class BaseSyslogTextPlugin(interface.TextPlugin):
    """Shared functionality for syslog log file text parser plugins."""

    # pylint: disable=abstract-method

    _CRON_USERNAME = (
        pyparsing.Literal("(")
        + pyparsing.Word(pyparsing.alphanums).set_results_name("username")
        + pyparsing.Literal(")")
    )

    _CRON_COMMAND_END = pyparsing.Literal(")") + pyparsing.StringEnd()

    _CRON_COMMAND = (
        pyparsing.Literal("(")
        + pyparsing.SkipTo(_CRON_COMMAND_END).set_results_name("command")
        + _CRON_COMMAND_END
    )

    _CRON_TASK_END = (
        _CRON_USERNAME
        + pyparsing.Literal("CMDEND")
        + _CRON_COMMAND
        + pyparsing.StringEnd()
    )

    _CRON_TASK_RUN = (
        _CRON_USERNAME
        + pyparsing.Literal("CMD")
        + _CRON_COMMAND
        + pyparsing.StringEnd()
    )

    _CRON_MESSAGE = pyparsing.Group(_CRON_TASK_END).set_results_name(
        "task_end"
    ) ^ pyparsing.Group(_CRON_TASK_RUN).set_results_name("task_run")

    # cronie writes job records under the upper case reporter name, CROND, and
    # the daemon's own messages under the lower case name, crond.
    _CRON_REPORTERS = frozenset(["CRON", "CROND"])

    # OpenSSH 9.8 split the server into a listener binary, sshd, and a per-session
    # binary, sshd-session, which writes the authentication messages.
    _SSHD_REPORTERS = frozenset(["sshd", "sshd-session"])

    _SSHD_AUTHENTICATION_METHOD = pyparsing.Keyword("password") | pyparsing.Keyword(
        "publickey"
    )

    # A key fingerprint consists of the key type followed by the digest, where the
    # digest is either the hash name and a base64 value, such as
    # "ED25519 SHA256:5xyQ+PG1Z3CIiShclJ2iNya5TOdKDgE/HrOXr21IdOo", or the older
    # colon separated hexadecimal form, such as "RSA 00:aa:bb:cc". The default of
    # the sshd_config FingerprintHash option is sha256.
    # Note that the hexadecimal form is matched first, since the hash name and
    # base64 pattern would otherwise match "00:aa" of "00:aa:bb:cc" and leave the
    # remainder of the value unparsed.
    _SSHD_FINGER_PRINT = pyparsing.Regex(
        r"[A-Za-z0-9-]+ "
        r"(?:[0-9a-fA-F]{2}(?::[0-9a-fA-F]{2})+|[A-Za-z0-9]+:[A-Za-z0-9+/=]+)"
    ).set_results_name("fingerprint")

    # A user name is determined by the text that precedes " from " since sshd
    # logs the user name as provided by the client, which is not limited to the
    # characters that useradd would accept.
    _SSH_USERNAME = (
        pyparsing.SkipTo(pyparsing.Literal("from"))
        .set_parse_action(lambda tokens: tokens[0].strip())
        .set_results_name("username")
    )

    # A link-local IPv6 address is logged with its zone identifier, such as
    # "fe80::1%eth0", since sshd determines the address with getnameinfo and
    # NI_NUMERICHOST, see get_peer_ipaddr in OpenSSH canohost.c and RFC 4007
    # section 11.
    _SSH_IP_ADDRESS = pyparsing.Combine(
        (
            pyparsing.pyparsing_common.ipv4_address
            | pyparsing.pyparsing_common.ipv6_address
        )
        + pyparsing.Optional(
            pyparsing.Literal("%") + pyparsing.Word(pyparsing.alphanums + "_.-")
        )
    )

    _SSH_PORT = pyparsing.Word(pyparsing.nums, max=5).set_results_name("port")

    # sshd writes the user name as "user NAME" after a successful
    # authentication, and as "authenticating user NAME" or "invalid user NAME"
    # once an authentication request named a user, see
    # ssh_packet_set_log_preamble in OpenSSH auth2.c. In the connection
    # identifier the name directly precedes the address, see
    # sshpkt_fmt_connection_id in packet.c, hence the name is determined by the
    # text that precedes the address and port.
    _SSH_CONNECTION_USERNAME = (
        pyparsing.SkipTo(_SSH_IP_ADDRESS + pyparsing.Literal("port") + _SSH_PORT)
        .set_parse_action(lambda tokens: tokens[0].strip())
        .set_results_name("username")
    )

    _SSH_CONNECTION_IDENTIFIER = (
        pyparsing.Optional(
            (
                (
                    pyparsing.Keyword("authenticating") + pyparsing.Keyword("user")
                ).set_results_name("authenticating_user")
                | (
                    pyparsing.Keyword("invalid") + pyparsing.Keyword("user")
                ).set_results_name("invalid_user")
                | pyparsing.Keyword("user").set_results_name("authenticated_user")
            )
            + _SSH_CONNECTION_USERNAME
        )
        + _SSH_IP_ADDRESS.set_results_name("ip_address")
        + pyparsing.Literal("port")
        + _SSH_PORT
    )

    # Messages the unprivileged pre-authentication process writes are suffixed
    # with "[preauth]" by the monitor, see monitor.c in OpenSSH.
    _SSHD_PREAUTH_SUFFIX = pyparsing.Optional(pyparsing.Literal("[preauth]"))

    # sshd writes "invalid user" before the user name when the name does not
    # resolve to an account that is allowed to log in, see auth_log in OpenSSH
    # auth.c.
    _SSHD_FAILED_CONNECTION = (
        pyparsing.Literal("Failed")
        + _SSHD_AUTHENTICATION_METHOD.set_results_name("authentication_method")
        + pyparsing.Literal("for")
        + pyparsing.Optional(
            pyparsing.Literal("invalid user").set_results_name("invalid_user")
        )
        + _SSH_USERNAME
        + pyparsing.Literal("from")
        + _SSH_IP_ADDRESS.set_results_name("ip_address")
        + pyparsing.Literal("port")
        + _SSH_PORT
        + pyparsing.Optional(pyparsing.Literal("ssh2").set_results_name("protocol"))
        + pyparsing.StringEnd()
    )

    _SSHD_LOGIN = (
        pyparsing.Literal("Accepted")
        + _SSHD_AUTHENTICATION_METHOD.set_results_name("authentication_method")
        + pyparsing.Literal("for")
        + _SSH_USERNAME
        + pyparsing.Literal("from")
        + _SSH_IP_ADDRESS.set_results_name("ip_address")
        + pyparsing.Literal("port")
        + _SSH_PORT
        + pyparsing.Literal("ssh2").set_results_name("protocol")
        + pyparsing.Optional(pyparsing.Literal(":") + _SSHD_FINGER_PRINT)
        + pyparsing.StringEnd()
    )

    _SSHD_OPENED_CONNECTION = (
        pyparsing.Literal("Connection from")
        + _SSH_IP_ADDRESS.set_results_name("ip_address")
        + pyparsing.Literal("port")
        + _SSH_PORT
        + pyparsing.StringEnd()
    )

    # The end of a connection is written with the connection identifier by
    # sshpkt_vfatal in OpenSSH packet.c, for the peer sending a disconnect
    # message, closing or resetting the TCP connection, and by client_alive_check
    # in serverloop.c, for a client that stops responding.
    _SSHD_CLOSED_CONNECTION = (
        (
            pyparsing.Literal("Connection closed by")
            | pyparsing.Literal("Connection reset by")
            | pyparsing.Literal("Disconnected from")
            | pyparsing.Literal("Timeout, client not responding from")
        )
        + _SSH_CONNECTION_IDENTIFIER
        + _SSHD_PREAUTH_SUFFIX
        + pyparsing.StringEnd()
    )

    # A read error after authentication is written with the address and port
    # and the error message, see process_input in OpenSSH serverloop.c.
    _SSHD_READ_ERROR = (
        pyparsing.Literal("Read error from remote host")
        + _SSH_IP_ADDRESS.set_results_name("ip_address")
        + pyparsing.Literal("port")
        + _SSH_PORT
        + pyparsing.Literal(":")
        + pyparsing.Regex(r".+")
        + pyparsing.StringEnd()
    )

    # The listener writes a connection that did not authenticate within
    # LoginGraceTime with the remote and local addresses, see OpenSSH sshd.c.
    _SSHD_AUTHENTICATION_TIMEOUT = (
        pyparsing.Literal("Timeout before authentication for connection from")
        + _SSH_IP_ADDRESS.set_results_name("ip_address")
        + pyparsing.Literal("to")
        + _SSH_IP_ADDRESS
        + pyparsing.Literal(", pid =")
        + pyparsing.Word(pyparsing.nums)
        + pyparsing.StringEnd()
    )

    # sshd writes the invalid user message once per connection when the user
    # name does not resolve, see getpwnamallow in OpenSSH auth.c.
    _SSHD_INVALID_USER = (
        pyparsing.Literal("Invalid user")
        + _SSH_USERNAME
        + pyparsing.Literal("from")
        + _SSH_IP_ADDRESS.set_results_name("ip_address")
        + pyparsing.Literal("port")
        + _SSH_PORT
        + pyparsing.StringEnd()
    )

    # A disconnect message of the peer is written with its reason code and text,
    # see ssh_packet_read_poll2 in OpenSSH packet.c. A reason other than 11, a
    # normal client exit, is logged at the error level, which OpenSSH prefixes
    # with "error: ", see do_log in log.c.
    _SSHD_RECEIVED_DISCONNECT = (
        pyparsing.Optional(pyparsing.Literal("error:"))
        + pyparsing.Literal("Received disconnect from")
        + _SSH_IP_ADDRESS.set_results_name("ip_address")
        + pyparsing.Literal("port")
        + _SSH_PORT
        + pyparsing.Literal(":")
        + pyparsing.Word(pyparsing.nums)
        .set_parse_action(lambda tokens: int(tokens[0], 10))
        .set_results_name("disconnect_reason_code")
        + pyparsing.Literal(":")
        + pyparsing.SkipTo(_SSHD_PREAUTH_SUFFIX + pyparsing.StringEnd())
        .set_parse_action(lambda tokens: tokens[0].strip())
        .set_results_name("disconnect_reason")
        + _SSHD_PREAUTH_SUFFIX
        + pyparsing.StringEnd()
    )

    _SSHD_MESSAGE = (
        pyparsing.Group(
            _SSHD_CLOSED_CONNECTION | _SSHD_READ_ERROR | _SSHD_AUTHENTICATION_TIMEOUT
        ).set_results_name("closed_connection")
        ^ pyparsing.Group(_SSHD_FAILED_CONNECTION).set_results_name("failed_connection")
        ^ pyparsing.Group(_SSHD_INVALID_USER).set_results_name("invalid_user")
        ^ pyparsing.Group(_SSHD_LOGIN).set_results_name("login")
        ^ pyparsing.Group(_SSHD_OPENED_CONNECTION).set_results_name("opened_connection")
        ^ pyparsing.Group(_SSHD_RECEIVED_DISCONNECT).set_results_name(
            "received_disconnect"
        )
    )

    # sudo writes a command record as "username : [TTY=… ;] PWD=… ; USER=… ;
    # [GROUP=… ;] COMMAND=…", where a field is followed by " ; " and the command
    # line is last, see sudoers(5) section EVENT LOGGING and new_logline in
    # lib/eventlog/eventlog.c. A denied command carries a reason before the
    # fields and is not matched. sudo-rs writes two spaces after the user name
    # where it omits the TTY= field.
    _SUDO_USERNAME = pyparsing.Word(
        pyparsing.printables, exclude_chars=":"
    ).set_results_name("username")

    _SUDO_FIELD_VALUE = pyparsing.Regex(r"[^;]+?(?= ;)")

    _SUDO_COMMAND = (
        _SUDO_USERNAME
        + pyparsing.Literal(":")
        + pyparsing.Optional(
            pyparsing.Literal("TTY=")
            + _SUDO_FIELD_VALUE.set_results_name("terminal")
            + pyparsing.Literal(";")
        )
        + pyparsing.Literal("PWD=")
        + _SUDO_FIELD_VALUE.set_results_name("working_directory")
        + pyparsing.Literal(";")
        + pyparsing.Literal("USER=")
        + _SUDO_FIELD_VALUE.set_results_name("account")
        + pyparsing.Literal(";")
        + pyparsing.Optional(
            pyparsing.Literal("GROUP=")
            + _SUDO_FIELD_VALUE.set_results_name("group_name")
            + pyparsing.Literal(";")
        )
        + pyparsing.Literal("COMMAND=")
        + pyparsing.Regex(r".*").set_results_name("command_line")
        + pyparsing.StringEnd()
    )

    # sudo splits a log message larger than syslog_maxlen, 980 bytes by default,
    # into multiple syslog records, where each additional record contains
    # "(command continued)" after the user name and the remainder of the command
    # line, see sudoers(5) section EVENT LOGGING and do_syslog_sudo in
    # lib/eventlog/eventlog.c.
    _SUDO_COMMAND_CONTINUED = (
        _SUDO_USERNAME
        + pyparsing.Literal(":")
        + pyparsing.Literal("(command continued)")
        + pyparsing.Regex(r".*").set_results_name("command_line")
        + pyparsing.StringEnd()
    )

    def __init__(self):
        """Initializes a text parser plugin."""
        super().__init__()
        self._sudo_command_event_data = None

    def _ParseCronMessageBody(self, message_body):
        """Parses a cron syslog message body.

        Args:
          message_body (str): syslog message body.

        Returns:
          SyslogCronTaskEventData: event data or None if not available.
        """
        try:
            structure = self._CRON_MESSAGE.parse_string(message_body)
        except pyparsing.ParseException as exception:
            logger.debug(f"Unable to parse cron message body with error: {exception!s}")
            return None

        keys = list(structure.keys())
        if len(keys) != 1:
            return None

        key = keys[0]
        structure = structure[0]

        if key == "task_end":
            event_data = SyslogCronTaskEndEventData()
        elif key == "task_run":
            event_data = SyslogCronTaskRunEventData()
        else:
            return None

        event_data.command = structure.get("command")
        event_data.username = structure.get("username")

        return event_data

    def _ParseFinalize(self, parser_mediator):
        """Finalizes parsing.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
        """
        if self._sudo_command_event_data:
            parser_mediator.ProduceEventData(self._sudo_command_event_data)
            self._sudo_command_event_data = None

    def _ParseSshdMessageBody(self, message_body):
        """Parses a sshd syslog message body.

        Args:
          message_body (str): syslog message body.

        Returns:
          SyslogCronTaskRunEventData: event data or None if not available.
        """
        try:
            structure = self._SSHD_MESSAGE.parse_string(message_body)
        except pyparsing.ParseException as exception:
            logger.debug(f"Unable to parse sshd message body with error: {exception!s}")
            return None

        keys = list(structure.keys())
        if len(keys) != 1:
            return None

        key = keys[0]
        structure = structure[0]

        if key == "closed_connection":
            event_data = SyslogSSHClosedConnectionEventData()
            if "username" in structure:
                event_data.is_authenticated = "authenticated_user" in structure
                event_data.is_invalid_user = "invalid_user" in structure
        elif key == "failed_connection":
            event_data = SyslogSSHFailedConnectionEventData()
            event_data.is_invalid_user = structure.get("invalid_user") is not None
        elif key == "invalid_user":
            event_data = SyslogSSHInvalidUserEventData()
        elif key == "login":
            event_data = SyslogSSHLoginEventData()
        elif key == "opened_connection":
            event_data = SyslogSSHOpenedConnectionEventData()
        elif key == "received_disconnect":
            event_data = SyslogSSHReceivedDisconnectEventData()
            event_data.disconnect_reason = structure.get("disconnect_reason")
            event_data.disconnect_reason_code = structure.get("disconnect_reason_code")
        else:
            return None

        event_data.authentication_method = structure.get("authentication_method", None)
        event_data.message_body = structure.get("message_body")
        event_data.fingerprint = structure.get("fingerprint")
        event_data.hostname = structure.get("hostname")
        event_data.ip_address = structure.get("ip_address")
        event_data.pid = structure.get("pid")
        event_data.protocol = structure.get("protocol")
        event_data.port = structure.get("port")
        event_data.reporter = structure.get("reporter")
        event_data.severity = structure.get("severity")
        event_data.username = structure.get("username")

        return event_data

    def _ParseSudoContinuedCommand(self, message_body):
        """Parses a sudo "(command continued)" syslog message body.

        The remainder of the command line is joined to the command line of the
        command record that precedes it.

        Args:
          message_body (str): syslog message body.

        Returns:
          bool: True if the message body continued the preceding command record.
        """
        if not self._sudo_command_event_data:
            return False

        try:
            structure = self._SUDO_COMMAND_CONTINUED.parse_string(message_body)
        except pyparsing.ParseException:
            return False

        if structure.get("username") != self._sudo_command_event_data.username:
            return False

        self._sudo_command_event_data.command_line = " ".join(
            [self._sudo_command_event_data.command_line, structure.get("command_line")]
        )
        return True

    def _ParseSudoMessageBody(self, message_body):
        """Parses a sudo syslog message body.

        Args:
          message_body (str): syslog message body.

        Returns:
          SyslogSudoCommandEventData: event data or None if not available.
        """
        try:
            structure = self._SUDO_COMMAND.parse_string(message_body)
        except pyparsing.ParseException as exception:
            logger.debug(f"Unable to parse sudo message body with error: {exception!s}")
            return None

        event_data = SyslogSudoCommandEventData()
        event_data.account = structure.get("account")
        event_data.command_line = structure.get("command_line")
        event_data.group_name = structure.get("group_name")
        event_data.terminal = structure.get("terminal")
        event_data.username = structure.get("username")
        event_data.working_directory = structure.get("working_directory")

        return event_data

    def _ProduceEventData(self, parser_mediator, event_data):
        """Produces event data.

        A sudo command record is held back until the next record has been parsed,
        since sudo can continue its command line in the next record.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          event_data (SyslogLineEventData): event data.
        """
        if self._sudo_command_event_data:
            parser_mediator.ProduceEventData(self._sudo_command_event_data)
            self._sudo_command_event_data = None

        if isinstance(event_data, SyslogSudoCommandEventData):
            self._sudo_command_event_data = event_data
        else:
            parser_mediator.ProduceEventData(event_data)


class SyslogTextPlugin(BaseSyslogTextPlugin):
    """Text parser plugin for syslog log files."""

    NAME = "syslog"
    DATA_FORMAT = "System log (syslog) file"

    ENCODING = "utf-8"

    # The reporter and facility fields can contain any printable character, but
    # to allow for processing of syslog formats that delimit the reporter and
    # facility with printable characters, we remove certain common delimiters
    # from the set of printable characters.

    _REPORTER_CHARACTERS = "".join(
        [c for c in pyparsing.printables if c not in [":", "[", "<"]]
    )

    _FACILITY_CHARACTERS = "".join(
        [c for c in pyparsing.printables if c not in [":", ">"]]
    )

    # Note that the following values are sorted in-order of their corresponding
    # syslog protocol 23 priority value.
    _SYSLOG_SEVERITY = [
        "EMERG",
        "ALERT",
        "CRIT",
        "ERR",
        "WARNING",
        "NOTICE",
        "INFO",
        "DEBUG",
    ]

    # According to section 6.2.1 of
    # https://datatracker.ietf.org/doc/html/draft-ietf-syslog-protocol-23
    #  0             kernel messages
    #  1             user-level messages
    #  2             mail system
    #  3             system daemons
    #  4             security/authorization messages
    #  5             messages generated internally by syslogd
    #  6             line printer subsystem
    #  7             network news subsystem
    #  8             UUCP subsystem
    #  9             clock daemon
    # 10             security/authorization messages
    # 11             FTP daemon
    # 12             NTP subsystem
    # 13             log audit
    # 14             log alert
    # 15             clock daemon (note 2)
    # 16             local use 0  (local0)
    # 17             local use 1  (local1)
    # 18             local use 2  (local2)
    # 19             local use 3  (local3)
    # 20             local use 4  (local4)
    # 21             local use 5  (local5)
    # 22             local use 6  (local6)
    # 23             local use 7  (local7)
    _SYSLOG_FACILITY = [
        "kernel message",
        "user-level message",
        "mail system",
        "system daemons",
        "security/authorization messages",
        "messages generated internally by syslogd",
        "line printer subsystem",
        "network news subsystem",
        "UUCP subsystem",
        "clock daemon",
        "security/authorization messages",
        "FTP daemon",
        "NTP subsystem",
        "log audit",
        "log alert",
        "clock daemon",
        "local use 0",
        "local use 1",
        "local use 2",
        "local use 3",
        "local use 4",
        "local use 5",
        "local use 6",
        "local use 7",
    ]

    # TODO: change pattern to allow only spaces as a field separator.
    _BODY_PATTERN = (
        r".*?(?=($|\n\w{3}\s+\d{1,2}\s\d{2}:\d{2}:\d{2})|"
        r"($|\n\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}[\+|-]\d{2}:\d{2}\s)|"
        r"($|\n<\d{1,3}>1\s\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}[\+|-]\d{2}"
        r":\d{2}\s))"
    )

    _ONE_OR_TWO_DIGITS = pyparsing.Word(pyparsing.nums, max=2).set_parse_action(
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

    _DATE_TIME_RFC3339 = (
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
        + pyparsing.Suppress(".")
        + _SIX_DIGITS
        + pyparsing.Word("+-", exact=1)
        + _TWO_DIGITS
        + pyparsing.Optional(pyparsing.Suppress(":") + _TWO_DIGITS)
    )

    _PROCESS_IDENTIFIER = pyparsing.Word(pyparsing.nums, max=5).set_parse_action(
        lambda tokens: int(tokens[0], 10)
    )

    _REPORTER = pyparsing.Word(_REPORTER_CHARACTERS)

    _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

    # The ChromeOS syslog messages are of a format beginning with an
    # ISO 8601 combined date and time expression with a time zone offset:
    #   2016-10-25T12:37:23.297265-07:00
    #
    # This will then be followed by the SYSLOG Severity which will be one of:
    #   EMERG,ALERT,CRIT,ERR,WARNING,NOTICE,INFO,DEBUG
    #
    # 2016-10-25T12:37:23.297265-07:00 INFO

    _CHROMEOS_SYSLOG_LINE_BODY = (
        pyparsing.one_of(_SYSLOG_SEVERITY).set_results_name("severity")
        + _REPORTER.set_results_name("reporter")
        + pyparsing.Optional(pyparsing.Suppress(":"))
        + pyparsing.Optional(
            pyparsing.Suppress("[")
            + _PROCESS_IDENTIFIER.set_results_name("pid")
            + pyparsing.Suppress("]")
        )
    )

    # The rsyslog file format (RSYSLOG_FileFormat) consists of:
    # %TIMESTAMP% %HOSTNAME% %syslogtag%%msg%
    #
    # Where %TIMESTAMP% is in RFC-3339 date time format e.g.
    # 2020-05-31T00:00:45.698463+00:00

    _RSYSLOG_LINE_BODY = (
        pyparsing.Word(pyparsing.printables).set_results_name("hostname")
        + _REPORTER.set_results_name("reporter")
        + pyparsing.Optional(
            pyparsing.Suppress("[")
            + _PROCESS_IDENTIFIER.set_results_name("pid")
            + pyparsing.Suppress("]")
        )
        + pyparsing.Optional(
            pyparsing.Suppress("<")
            + pyparsing.Word(_FACILITY_CHARACTERS).set_results_name("facility")
            + pyparsing.Suppress(">")
        )
    )

    _LOG_LINE = (
        _DATE_TIME_RFC3339.set_results_name("date_time")
        + (_CHROMEOS_SYSLOG_LINE_BODY ^ _RSYSLOG_LINE_BODY)
        + pyparsing.Optional(pyparsing.Suppress(":"))
        + pyparsing.Regex(_BODY_PATTERN, re.DOTALL).set_results_name("message_body")
        + _END_OF_LINE
    )

    # The rsyslog protocol 23 format (RSYSLOG_SyslogProtocol23Format)
    # consists of:
    # %PRI%1 %TIMESTAMP% %HOSTNAME% %APP-NAME% %PROCID% %MSGID% %STRUCTURED-DATA%
    #   %msg%
    #
    # Where %TIMESTAMP% is in RFC-3339 date time format e.g.
    # 2020-05-31T00:00:45.698463+00:00

    # TODO: Add proper support for %STRUCTURED-DATA%:
    # https://datatracker.ietf.org/doc/html/draft-ietf-syslog-protocol-23#section-6.3
    _RSYSLOG_PROTOCOL_23_LINE = (
        pyparsing.Suppress("<")
        + _ONE_OR_TWO_DIGITS.set_results_name("priority")
        + pyparsing.Suppress(">")
        + pyparsing.Suppress(pyparsing.Word(pyparsing.nums, max=1))
        + _DATE_TIME_RFC3339.set_results_name("date_time")
        + pyparsing.Word(pyparsing.printables).set_results_name("hostname")
        + _REPORTER.set_results_name("reporter")
        + pyparsing.Or(
            [pyparsing.Suppress("-"), _PROCESS_IDENTIFIER.set_results_name("pid")]
        )
        + pyparsing.Word(pyparsing.printables).set_results_name("message_identifier")
        + pyparsing.Word(pyparsing.printables).set_results_name("structured_data")
        + pyparsing.Regex(_BODY_PATTERN, re.DOTALL).set_results_name("message_body")
        + _END_OF_LINE
    )

    _LINE_STRUCTURES = [
        ("log_line", _LOG_LINE),
        ("rsyslog_protocol_23_line", _RSYSLOG_PROTOCOL_23_LINE),
    ]

    VERIFICATION_GRAMMAR = _LOG_LINE ^ _RSYSLOG_PROTOCOL_23_LINE

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

        message_body = self._GetValueFromStructure(structure, "message_body")
        reporter = self._GetValueFromStructure(structure, "reporter")

        if key == "rsyslog_protocol_23_line":
            priority = self._GetValueFromStructure(structure, "priority")

            facility = self._PriorityToFacility(priority)
            message_identifier = self._GetValueFromStructure(
                structure, "message_identifier"
            )
            severity = self._PriorityToSeverity(priority)
        else:
            facility = None
            message_identifier = None
            severity = self._GetValueFromStructure(structure, "severity")

        event_data = None
        if reporter in self._CRON_REPORTERS:
            event_data = self._ParseCronMessageBody(message_body)
        elif reporter in self._SSHD_REPORTERS:
            event_data = self._ParseSshdMessageBody(message_body)
        elif reporter == "sudo":
            if self._ParseSudoContinuedCommand(message_body):
                return
            event_data = self._ParseSudoMessageBody(message_body)

        if not event_data:
            event_data = SyslogLineEventData()

        event_data.facility = facility
        event_data.hostname = self._GetValueFromStructure(structure, "hostname")
        event_data.last_written_time = self._ParseTimeElements(time_elements_structure)
        event_data.message_body = message_body
        event_data.message_identifier = message_identifier
        event_data.pid = self._GetValueFromStructure(structure, "pid")
        event_data.reporter = reporter
        event_data.severity = severity

        self._ProduceEventData(parser_mediator, event_data)

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
            time_zone_minutes = 0

            if len(time_elements_structure) == 9:
                (
                    year,
                    month,
                    day_of_month,
                    hours,
                    minutes,
                    seconds,
                    microseconds,
                    time_zone_sign,
                    time_zone_hours,
                ) = time_elements_structure

            else:
                (
                    year,
                    month,
                    day_of_month,
                    hours,
                    minutes,
                    seconds,
                    microseconds,
                    time_zone_sign,
                    time_zone_hours,
                    time_zone_minutes,
                ) = time_elements_structure

            time_zone_offset = (time_zone_hours * 60) + time_zone_minutes
            if time_zone_sign == "-":
                time_zone_offset *= -1

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
                time_elements_tuple=time_elements_tuple,
                time_zone_offset=time_zone_offset,
            )

            return date_time

        except (IndexError, TypeError, ValueError) as exception:
            raise errors.ParseError(
                f"Unable to parse time elements with error: {exception!s}"
            )

    def _PriorityToSeverity(self, priority):
        """Converts a syslog protocol 23 priority value to severity.

        Severity is derived from the 3 least significant bits of the priority
        value.

        Args:
          priority (int): a syslog protocol 23 priority value.

        Returns:
          str: the value from _SYSLOG_SEVERITY corresponding to severity value.
        """
        return self._SYSLOG_SEVERITY[priority & 0x07]

    def _PriorityToFacility(self, priority: int) -> str:
        """Converts a syslog protocol 23 or RFC3164 priority to facility.

        Facility is derived from the 5 most significant bits of the priority
        value.

        Args:
          priority (int): a syslog rfc3164 or protocol 23 priority value.

        Returns:
          str: the value from _SYSLOG_FACILITY corresponding to facility value.
        """
        return self._SYSLOG_FACILITY[priority >> 3]

    def CheckRequiredFormat(self, parser_mediator, text_reader):
        """Check if the log record has the minimal structure required by the parser.

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


class TraditionalSyslogTextPlugin(
    BaseSyslogTextPlugin, dateless_helper.DateLessLogFormatHelper
):
    """Text parser plugin for traditional syslog log files."""

    NAME = "syslog_traditional"
    DATA_FORMAT = "Traditional system log (syslog) file"

    ENCODING = "utf-8"

    # The reporter and facility fields can contain any printable character, but
    # to allow for processing of syslog formats that delimit the reporter and
    # facility with printable characters, we remove certain common delimiters
    # from the set of printable characters.

    _REPORTER_CHARACTERS = "".join(
        [c for c in pyparsing.printables if c not in [":", "[", "<"]]
    )

    _FACILITY_CHARACTERS = "".join(
        [c for c in pyparsing.printables if c not in [":", ">"]]
    )

    _SYSLOG_SEVERITY = [
        "ALERT",
        "CRIT",
        "DEBUG",
        "EMERG",
        "ERR",
        "INFO",
        "NOTICE",
        "WARNING",
    ]

    # TODO: change pattern to allow only spaces as a field separator.
    _BODY_PATTERN = (
        r".*?(?=($|\n\w{3}\s+\d{1,2}\s\d{2}:\d{2}:\d{2})|"
        r"($|\n\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}[\+|-]\d{2}:\d{2}\s)|"
        r"($|\n<\d{1,3}>1\s\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}[\+|-]\d{2}"
        r":\d{2}\s))"
    )

    _ONE_OR_TWO_DIGITS = pyparsing.Word(pyparsing.nums, max=2).set_parse_action(
        lambda tokens: int(tokens[0], 10)
    )

    _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).set_parse_action(
        lambda tokens: int(tokens[0], 10)
    )

    _THREE_LETTERS = pyparsing.Word(pyparsing.alphas, exact=3)

    _DATE_TIME = (
        _THREE_LETTERS
        + _ONE_OR_TWO_DIGITS
        + _TWO_DIGITS
        + pyparsing.Suppress(":")
        + _TWO_DIGITS
        + pyparsing.Suppress(":")
        + _TWO_DIGITS
        + pyparsing.Optional(pyparsing.Suppress(".") + pyparsing.Word(pyparsing.nums))
    )

    _PROCESS_IDENTIFIER = pyparsing.Word(pyparsing.nums, max=5).set_parse_action(
        lambda tokens: int(tokens[0], 10)
    )

    _REPORTER = pyparsing.Word(_REPORTER_CHARACTERS)

    _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

    # The rsyslog traditional file format (RSYSLOG_TraditionalFileFormat)
    # consists of:
    # %TIMESTAMP% %HOSTNAME% %syslogtag%%msg%
    #
    # Where %TIMESTAMP% is in year-less ctime date time format e.g.
    # Jan 22 07:54:32

    _RSYSLOG_BODY = (
        pyparsing.Word(pyparsing.printables).set_results_name("hostname")
        + _REPORTER.set_results_name("reporter")
        + pyparsing.Optional(
            pyparsing.Suppress("[")
            + _PROCESS_IDENTIFIER.set_results_name("pid")
            + pyparsing.Suppress("]")
        )
        + pyparsing.Optional(
            pyparsing.Suppress("<")
            + pyparsing.Word(_FACILITY_CHARACTERS).set_results_name("facility")
            + pyparsing.Suppress(">")
        )
        + pyparsing.Optional(pyparsing.Suppress(":"))
        + pyparsing.Regex(_BODY_PATTERN, re.DOTALL).set_results_name("message_body")
    )

    _SYSLOG_COMMENT_END = pyparsing.Suppress("---") + _END_OF_LINE

    _SYSLOG_COMMENT_BODY = (
        pyparsing.Suppress(": ---")
        + pyparsing.SkipTo(_SYSLOG_COMMENT_END).set_results_name("message_body")
        + pyparsing.Suppress("---")
    )

    _KERNEL_SYSLOG_BODY = (
        pyparsing.Literal("kernel").set_results_name("reporter")
        + pyparsing.Suppress(":")
        + pyparsing.Regex(_BODY_PATTERN, re.DOTALL).set_results_name("message_body")
    )

    _LOG_LINE = (
        _DATE_TIME.set_results_name("date_time")
        + (_KERNEL_SYSLOG_BODY ^ _RSYSLOG_BODY ^ _SYSLOG_COMMENT_BODY)
        + _END_OF_LINE
    )

    _LINE_STRUCTURES = [("log_line", _LOG_LINE)]

    # Using a regular expression here is faster on non-match than the log line
    # grammar.
    VERIFICATION_GRAMMAR = pyparsing.Regex(
        r"(?P<date_time>(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) "
        r"( [1-9]|[1-9][0-9]) [0-9]{2}:[0-9]{2}:[0-9]{2}) \S+ .*\n"
    )

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

        message_body = self._GetValueFromStructure(structure, "message_body")
        reporter = self._GetValueFromStructure(structure, "reporter")

        event_data = None
        if reporter in self._CRON_REPORTERS:
            event_data = self._ParseCronMessageBody(message_body)
        elif reporter in self._SSHD_REPORTERS:
            event_data = self._ParseSshdMessageBody(message_body)
        elif reporter == "sudo":
            if self._ParseSudoContinuedCommand(message_body):
                return
            event_data = self._ParseSudoMessageBody(message_body)

        if not event_data:
            event_data = SyslogLineEventData()

        event_data.hostname = self._GetValueFromStructure(structure, "hostname")
        event_data.last_written_time = self._ParseTimeElements(time_elements_structure)
        event_data.message_body = message_body
        event_data.pid = self._GetValueFromStructure(structure, "pid")
        event_data.reporter = reporter
        event_data.severity = self._GetValueFromStructure(structure, "severity")

        self._ProduceEventData(parser_mediator, event_data)

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
            if len(time_elements_structure) == 5:
                month_string, day_of_month, hours, minutes, seconds = (
                    time_elements_structure
                )

            else:
                # TODO: add support for fractional seconds.
                month_string, day_of_month, hours, minutes, seconds, _ = (
                    time_elements_structure
                )

            month = self._GetMonthFromString(month_string)

            self._UpdateYear(month)

            year = self._GetRelativeYear()

            time_elements_tuple = (year, month, day_of_month, hours, minutes, seconds)

            date_time = dfdatetime_time_elements.TimeElements(
                is_delta=True, time_elements_tuple=time_elements_tuple
            )

            date_time.is_local_time = True

            return date_time

        except (IndexError, TypeError, ValueError) as exception:
            raise errors.ParseError(
                f"Unable to parse time elements with error: {exception!s}"
            )

    def CheckRequiredFormat(self, parser_mediator, text_reader):
        """Check if the log record has the minimal structure required by the parser.

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

        date_time_structure = self._GetValueFromStructure(structure, "date_time")

        try:
            time_elements_structure = self._DATE_TIME.parse_string(date_time_structure)
        except pyparsing.ParseException:
            return False

        self._SetEstimatedYear(parser_mediator)

        try:
            self._ParseTimeElements(time_elements_structure)
        except errors.ParseError:
            return False

        return True


text_parser.TextLogParser.RegisterPlugins(
    [SyslogTextPlugin, TraditionalSyslogTextPlugin]
)
