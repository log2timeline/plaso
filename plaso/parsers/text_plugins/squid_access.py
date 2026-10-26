"""Text parser plugin for Squid access log files in the native log format.

Also see:
  https://wiki.squid-cache.org/Features/LogFormat
"""

import pyparsing

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class SquidAccessLogEventData(events.EventData):
    """Squid access log event data.

    Attributes:
      cache_result (str): cache result code, such as "TCP_MISS".
      client_address (str): address of the client that made the request.
      content_type (str): content type of the response.
      elapsed_time (int): number of milliseconds the transaction occupied the
          cache.
      hierarchy_code (str): hierarchy code that describes how the request was
          handled, such as "HIER_DIRECT".
      http_request_method (str): HTTP request method, such as "GET".
      http_response_code (int): HTTP response status code.
      peer_host (str): host or address of the server or peer the request was
          forwarded to.
      recorded_time (dfdatetime.DateTimeValues): date and time the log entry
          was recorded.
      response_size (int): number of bytes delivered to the client.
      url (str): requested URL.
      username (str): name of the user that made the request.
    """

    DATA_TYPE = "squid:access_log:entry"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.cache_result = None
        self.client_address = None
        self.content_type = None
        self.elapsed_time = None
        self.hierarchy_code = None
        self.http_request_method = None
        self.http_response_code = None
        self.peer_host = None
        self.recorded_time = None
        self.response_size = None
        self.url = None
        self.username = None


class SquidAccessLogTextPlugin(interface.TextPlugin):
    """Text parser plugin for Squid access log files in the native log format."""

    NAME = "squid_access"
    DATA_FORMAT = "Squid access log (access.log) file"

    ENCODING = "utf-8"

    _INTEGER = pyparsing.Word(pyparsing.nums).set_parse_action(
        lambda tokens: int(tokens[0], 10)
    )

    # The timestamp is formatted as the number of seconds since
    # 1970-01-01 00:00:00 with millisecond precision, for example:
    # 1759742102.104
    _TIMESTAMP = pyparsing.Regex(r"[0-9]{1,10}\.[0-9]{3}").set_parse_action(
        lambda tokens: int(tokens[0].replace(".", ""), 10)
    )

    _CODE = pyparsing.Word(pyparsing.string.ascii_uppercase + "_")

    _PRINTABLE_WITHOUT_SLASH = pyparsing.Word(pyparsing.printables, exclude_chars="/")

    _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

    # The native log format is defined as:
    # %ts.%03tu %6tr %>a %Ss/%03>Hs %<st %rm %ru %[un %Sh/%<a %mt
    _LOG_LINE = (
        _TIMESTAMP.set_results_name("timestamp")
        + _INTEGER.set_results_name("elapsed_time")
        + pyparsing.Word(pyparsing.printables).set_results_name("client_address")
        + _CODE.set_results_name("cache_result")
        + pyparsing.Suppress("/")
        + _INTEGER.set_results_name("http_response_code")
        + _INTEGER.set_results_name("response_size")
        + _CODE.set_results_name("http_request_method")
        + pyparsing.Word(pyparsing.printables).set_results_name("url")
        + pyparsing.Word(pyparsing.printables).set_results_name("username")
        + _CODE.set_results_name("hierarchy_code")
        + pyparsing.Suppress("/")
        + _PRINTABLE_WITHOUT_SLASH.set_results_name("peer_host")
        + pyparsing.Word(pyparsing.printables).set_results_name("content_type")
        + _END_OF_LINE
    )

    _LINE_STRUCTURES = [("log_line", _LOG_LINE)]

    VERIFICATION_GRAMMAR = _LOG_LINE

    def _GetOptionalStringValueFromStructure(self, structure, name):
        """Retrieves a string value that is "-" when not set from a structure.

        Args:
          structure (pyparsing.ParseResults): tokens from a parsed log line.
          name (str): name of the token.

        Returns:
          str: string value or None if not available.
        """
        value = self._GetValueFromStructure(structure, name)
        if value == "-":
            return None

        return value

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
        timestamp = self._GetValueFromStructure(structure, "timestamp")

        event_data = SquidAccessLogEventData()
        event_data.cache_result = self._GetValueFromStructure(structure, "cache_result")
        event_data.client_address = self._GetValueFromStructure(
            structure, "client_address"
        )
        event_data.content_type = self._GetOptionalStringValueFromStructure(
            structure, "content_type"
        )
        event_data.elapsed_time = self._GetValueFromStructure(structure, "elapsed_time")
        event_data.hierarchy_code = self._GetValueFromStructure(
            structure, "hierarchy_code"
        )
        event_data.http_request_method = self._GetValueFromStructure(
            structure, "http_request_method"
        )
        event_data.http_response_code = self._GetValueFromStructure(
            structure, "http_response_code"
        )
        event_data.peer_host = self._GetOptionalStringValueFromStructure(
            structure, "peer_host"
        )
        event_data.recorded_time = dfdatetime_posix_time.PosixTimeInMilliseconds(
            timestamp=timestamp
        )
        event_data.response_size = self._GetValueFromStructure(
            structure, "response_size"
        )
        event_data.url = self._GetValueFromStructure(structure, "url")
        event_data.username = self._GetOptionalStringValueFromStructure(
            structure, "username"
        )

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
            self._VerifyString(text_reader.lines)
        except errors.ParseError:
            return False

        return True


text_parser.TextLogParser.RegisterPlugin(SquidAccessLogTextPlugin)
