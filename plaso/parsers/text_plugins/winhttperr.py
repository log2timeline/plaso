"""Text parser plugin for Microsoft HTTP API (HTTP.sys) error log files.

HTTP.sys writes requests it rejects before they reach an application, such as
malformed requests, connection time-outs or queue overflows, to error log files,
which by default are stored in: %SystemRoot%\\System32\\LogFiles\\HTTPERR

Also see:
  https://learn.microsoft.com/en-us/troubleshoot/developer/webapps/aspnet/site-behavior-performance/error-logging-http-apis
"""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class WinHTTPErrEventData(events.EventData):
    """Microsoft HTTP API (HTTP.sys) error log event data.

    Attributes:
      dest_ip (str): IP address of the server.
      dest_port (int): server port number.
      extended_fault_code (str): extended fault code.
      extended_stream_identifier (str): extended stream identifier.
      fault_code (str): fault code.
      http_method (str): HTTP request method, such as GET or POST.
      http_status (int): HTTP status code that was returned by HTTP.sys.
      last_written_time (dfdatetime.DateTimeValues): entry last written date and
          time.
      protocol_version (str): HTTP protocol version that was used.
      queue_name (str): name of the request queue, such as an application pool.
      reason (str): reason HTTP.sys rejected the request, such as "Hostname" or
          "Timer_ConnectionIdle".
      requested_uri (str): URI that was requested.
      site_identifier (int): identifier of the site.
      source_ip (str): IP address of the client that made the request.
      source_port (int): client port number.
      stream_identifier (str): identifier of the HTTP/2 or HTTP/3 stream.
      transport (str): transport protocol, such as TCP or QUIC.
    """

    DATA_TYPE = "windows:httperr_log:entry"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.dest_ip = None
        self.dest_port = None
        self.extended_fault_code = None
        self.extended_stream_identifier = None
        self.fault_code = None
        self.http_method = None
        self.http_status = None
        self.last_written_time = None
        self.protocol_version = None
        self.queue_name = None
        self.reason = None
        self.requested_uri = None
        self.site_identifier = None
        self.source_ip = None
        self.source_port = None
        self.stream_identifier = None
        self.transport = None


class WinHTTPErrTextPlugin(interface.TextPlugin):
    """Text parser plugin for Microsoft HTTP API (HTTP.sys) error log files."""

    NAME = "winhttperr"
    DATA_FORMAT = "Microsoft HTTP API (HTTP.sys) error log file"

    # HTTP.sys writes error log files in UTF-8.
    ENCODING = "utf-8"

    # The values of fields are separated by a single space and an unused or
    # empty value is represented by a hyphen.
    _BLANK = pyparsing.Regex(r"-(?=[ \t\r\n]|$)").suppress()

    # Values such as the requested URI are logged as received from the client and
    # can contain any non-whitespace character, for example characters used in
    # SQL injection attempts. Hence, the values are not restricted to a specific
    # set of characters.
    _STRING_OR_BLANK = _BLANK | pyparsing.Regex(r"[^ \t\r\n]+")

    _INTEGER_OR_BLANK = _BLANK | pyparsing.Word(pyparsing.nums).set_parse_action(
        lambda tokens: int(tokens[0], 10)
    )

    _PORT_NUMBER_OR_BLANK = _BLANK | pyparsing.Word(
        pyparsing.nums, max=5
    ).set_parse_action(lambda tokens: int(tokens[0], 10))

    # An IPv6 address can have a zone index suffix (RFC 4007), such as "%3".
    _IPV6_ZONE_INDEX = pyparsing.Combine(
        pyparsing.Literal("%") + pyparsing.Word(pyparsing.alphanums + ".-_")
    )

    _IP_ADDRESS_OR_BLANK = (
        _BLANK
        | pyparsing.pyparsing_common.ipv4_address
        | pyparsing.Combine(
            pyparsing.pyparsing_common.ipv6_address
            + pyparsing.Optional(_IPV6_ZONE_INDEX)
        )
    )

    _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).set_parse_action(
        lambda tokens: int(tokens[0], 10)
    )

    _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).set_parse_action(
        lambda tokens: int(tokens[0], 10)
    )

    _DATE = pyparsing.Group(
        _FOUR_DIGITS
        + pyparsing.Suppress("-")
        + _TWO_DIGITS
        + pyparsing.Suppress("-")
        + _TWO_DIGITS
    )

    _TIME = pyparsing.Group(
        _TWO_DIGITS
        + pyparsing.Suppress(":")
        + _TWO_DIGITS
        + pyparsing.Suppress(":")
        + _TWO_DIGITS
    )

    _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

    _FIELDS_METADATA = pyparsing.Suppress(
        "Fields:"
    ) + pyparsing.rest_of_line().set_results_name("fields")

    _METADATA = _FIELDS_METADATA | pyparsing.rest_of_line()

    # A comment line starts with "#". HTTP.sys writes a new block of comment
    # lines, including "#Fields:", every time the HTTP service starts writing to
    # a log file, hence comment lines can also occur after the first log line.
    _COMMENT_LOG_LINE = pyparsing.Suppress("#") + _METADATA + _END_OF_LINE

    # Results names use underscores, not hyphens, so that they can be used as
    # attribute names.
    _LOG_LINE_STRUCTURES = {
        "c-ip": _IP_ADDRESS_OR_BLANK.set_results_name("source_ip"),
        "c-port": _PORT_NUMBER_OR_BLANK.set_results_name("source_port"),
        "cs-method": _STRING_OR_BLANK.set_results_name("http_method"),
        "cs-uri": _STRING_OR_BLANK.set_results_name("requested_uri"),
        "cs-version": _STRING_OR_BLANK.set_results_name("protocol_version"),
        "date": _DATE.set_results_name("date"),
        "extended-fault-code": _STRING_OR_BLANK.set_results_name("extended_fault_code"),
        "fault-code": _STRING_OR_BLANK.set_results_name("fault_code"),
        "s-ip": _IP_ADDRESS_OR_BLANK.set_results_name("dest_ip"),
        "s-port": _PORT_NUMBER_OR_BLANK.set_results_name("dest_port"),
        "s-queuename": _STRING_OR_BLANK.set_results_name("queue_name"),
        "s-reason": _STRING_OR_BLANK.set_results_name("reason"),
        "s-siteid": _INTEGER_OR_BLANK.set_results_name("site_identifier"),
        "sc-status": _INTEGER_OR_BLANK.set_results_name("http_status"),
        "streamid": _STRING_OR_BLANK.set_results_name("stream_identifier"),
        "streamid_ex": _STRING_OR_BLANK.set_results_name("extended_stream_identifier"),
        "time": _TIME.set_results_name("time"),
        "transport": _STRING_OR_BLANK.set_results_name("transport"),
    }

    # Fields written by HTTP API 2.0 (Windows Server 2003 and later), used when
    # a log file does not contain a "#Fields:" comment line:
    # date time c-ip c-port s-ip s-port cs-version cs-method cs-uri sc-status
    # s-siteid s-reason s-queuename

    _DEFAULT_LOG_LINE = (
        _DATE.set_results_name("date")
        + _TIME.set_results_name("time")
        + _IP_ADDRESS_OR_BLANK.set_results_name("source_ip")
        + _PORT_NUMBER_OR_BLANK.set_results_name("source_port")
        + _IP_ADDRESS_OR_BLANK.set_results_name("dest_ip")
        + _PORT_NUMBER_OR_BLANK.set_results_name("dest_port")
        + _STRING_OR_BLANK.set_results_name("protocol_version")
        + _STRING_OR_BLANK.set_results_name("http_method")
        + _STRING_OR_BLANK.set_results_name("requested_uri")
        + _INTEGER_OR_BLANK.set_results_name("http_status")
        + _INTEGER_OR_BLANK.set_results_name("site_identifier")
        + _STRING_OR_BLANK.set_results_name("reason")
        + _STRING_OR_BLANK.set_results_name("queue_name")
        + _END_OF_LINE
    )

    _LINE_STRUCTURES = [
        ("comment_line", _COMMENT_LOG_LINE),
        ("log_line", _DEFAULT_LOG_LINE),
    ]

    VERIFICATION_GRAMMAR = (
        pyparsing.ZeroOrMore(
            pyparsing.Regex("#(Date|Fields|Version): .*") + _END_OF_LINE
        )
        + pyparsing.Regex("#Software: Microsoft HTTP API .*")
        + _END_OF_LINE
    )

    VERIFICATION_LITERALS = ["#Software: Microsoft HTTP API "]

    def _GetLogLineStructure(self, fields, parser_mediator=None):
        """Builds a log line structure based on field definitions.

        Args:
          fields (str): field definitions, separated by a space.
          parser_mediator (Optional[ParserMediator]): mediates interactions between
              parsers and other components, such as storage and dfVFS.

        Returns:
          pyparsing.ParserElement: log line structure.
        """
        log_line_structure = pyparsing.Empty()
        for member in fields.split(" "):
            if not member:
                continue

            field_structure = self._LOG_LINE_STRUCTURES.get(member)
            if not field_structure:
                field_structure = self._STRING_OR_BLANK
                if parser_mediator:
                    parser_mediator.ProduceWarning(
                        f"missing definition for field: {member:s} defaulting to "
                        f"STRING_OR_BLANK"
                    )

            log_line_structure += field_structure

        log_line_structure += self._END_OF_LINE

        return log_line_structure

    def _ParseLogLine(self, parser_mediator, structure):
        """Parses a log line.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          structure (pyparsing.ParseResults): tokens from a parsed log line.
        """
        event_data = WinHTTPErrEventData()
        event_data.dest_ip = self._GetValueFromStructure(structure, "dest_ip")
        event_data.dest_port = self._GetValueFromStructure(structure, "dest_port")
        event_data.extended_fault_code = self._GetValueFromStructure(
            structure, "extended_fault_code"
        )
        event_data.extended_stream_identifier = self._GetValueFromStructure(
            structure, "extended_stream_identifier"
        )
        event_data.fault_code = self._GetValueFromStructure(structure, "fault_code")
        event_data.http_method = self._GetValueFromStructure(structure, "http_method")
        event_data.http_status = self._GetValueFromStructure(structure, "http_status")
        event_data.last_written_time = self._ParseTimeElements(structure)
        event_data.protocol_version = self._GetValueFromStructure(
            structure, "protocol_version"
        )
        event_data.queue_name = self._GetValueFromStructure(structure, "queue_name")
        event_data.reason = self._GetValueFromStructure(structure, "reason")
        event_data.requested_uri = self._GetValueFromStructure(
            structure, "requested_uri"
        )
        event_data.site_identifier = self._GetValueFromStructure(
            structure, "site_identifier"
        )
        event_data.source_ip = self._GetValueFromStructure(structure, "source_ip")
        event_data.source_port = self._GetValueFromStructure(structure, "source_port")
        event_data.stream_identifier = self._GetValueFromStructure(
            structure, "stream_identifier"
        )
        event_data.transport = self._GetValueFromStructure(structure, "transport")

        parser_mediator.ProduceEventData(event_data)

    def _ParseRecord(self, parser_mediator, key, structure):
        """Parses a pyparsing structure.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          key (str): name of the parsed structure.
          structure (pyparsing.ParseResults): tokens from a parsed log line.

        Raises:
          ParseError: if the structure cannot be parsed.
        """
        if key == "comment_line":
            fields = self._GetValueFromStructure(structure, "fields", default_value="")
            fields = fields.strip()
            if fields:
                self._SetLogLineStructure(fields, parser_mediator=parser_mediator)

        elif key == "log_line":
            self._ParseLogLine(parser_mediator, structure)

    def _ParseTimeElements(self, structure):
        """Parses date and time elements of a log line.

        Args:
          structure (pyparsing.ParseResults): tokens from a parsed log line.

        Returns:
          dfdatetime.TimeElements: date and time value.

        Raises:
          ParseError: if a valid date and time value cannot be derived from
              the time elements.
        """
        date_elements_structure = self._GetValueFromStructure(structure, "date")
        time_elements_structure = self._GetValueFromStructure(structure, "time")

        try:
            year, month, day_of_month = date_elements_structure
            hours, minutes, seconds = time_elements_structure

            time_elements_tuple = (year, month, day_of_month, hours, minutes, seconds)

            # HTTP.sys error log files are written in UTC.
            return dfdatetime_time_elements.TimeElements(
                time_elements_tuple=time_elements_tuple
            )

        except (TypeError, ValueError) as exception:
            raise errors.ParseError(
                f"Unable to parse time elements with error: {exception!s}"
            )

    def _ResetState(self):
        """Resets stored values."""
        self._SetLineStructures(self._LINE_STRUCTURES)

    def _SetLogLineStructure(self, fields, parser_mediator=None):
        """Sets the line structures based on field definitions.

        Args:
          fields (str): field definitions, separated by a space.
          parser_mediator (Optional[ParserMediator]): mediates interactions between
              parsers and other components, such as storage and dfVFS.
        """
        log_line_structure = self._GetLogLineStructure(
            fields, parser_mediator=parser_mediator
        )
        self._SetLineStructures(
            [
                ("comment_line", self._COMMENT_LOG_LINE),
                ("log_line", log_line_structure),
            ]
        )

    def CheckRequiredFormat(self, parser_mediator, text_reader):
        """Check if the log record has the minimal structure required by the plugin.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          text_reader (EncodedTextReader): text reader.

        Returns:
          bool: True if this is the correct plugin, False otherwise.
        """
        try:
            self._VerifyString(text_reader.lines)
        except errors.ParseError:
            return False

        self._ResetState()

        return True


text_parser.TextLogParser.RegisterPlugin(WinHTTPErrTextPlugin)
