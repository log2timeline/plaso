# -*- coding: utf-8 -*-
"""Text parser plugin for Microsoft IIS log files."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class IISEventData(events.EventData):
  """IIS log event data.

  Attributes:
    cs_cookie (str): Content of a sent or received cookie.
    cs_host (str): HTTP host header name.
    cs_referrer (str): Site that referred to the requested site.
    cs_uri_query (str): URI query that was requested.
    cs_username (str): Username of the authenticated user that accessed
        the server, where anonymous users are indicated by a hyphen.
    dest_ip (str): IP address of the server that generated the logged activity.
    dest_port (str): Server port number.
    http_method (str): HTTP request method, such as GET or POST.
    http_status (str): HTTP status code that was returned by the server.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
    protocol_version (str): HTTP protocol version that was used.
    received_bytes (str): Number of bytes received and processed by the server.
    requested_uri_stem (str): File requested, such as index.php or Default.htm
    s_computername (str): Name of the server that generated the logged activity.
    sc_substatus (str):  HTTP substatus error code that was returned by the
        server.
    sc_win32_status (str): Windows status code of the server.
    sent_bytes (str): Number of bytes sent by the server.
    source_ip (str): IP address of the client that made the request.
    s_sitename (str): Service name and instance number that was running on the
        client.
    time_taken (str): Time taken, in milliseconds, to process the request.
    user_agent (str): User agent that was used.
  """

  DATA_TYPE = 'iis:log:line'

  def __init__(self):
    """Initializes event data."""
    super(IISEventData, self).__init__(data_type=self.DATA_TYPE)
    self.cs_cookie = None
    self.cs_host = None
    self.cs_referrer = None
    self.cs_uri_query = None
    self.cs_username = None
    self.dest_ip = None
    self.dest_port = None
    self.http_method = None
    self.http_status = None
    self.last_written_time = None
    self.protocol_version = None
    self.received_bytes = None
    self.requested_uri_stem = None
    self.s_computername = None
    self.sc_substatus = None
    self.sc_win32_status = None
    self.sent_bytes = None
    self.source_ip = None
    self.s_sitename = None
    self.time_taken = None
    self.user_agent = None


class WinIISTextPlugin(interface.TextPlugin):
  """Text parser plugin for Microsoft IIS log files."""

  NAME = 'winiis'
  DATA_FORMAT = 'Microsoft IIS log file'

  # Log file are all extended ASCII encoded unless UTF-8 is explicitly enabled.
  # TODO: fix
  ENCODING = 'utf-8'

  _BLANK = pyparsing.Literal('-')

  _HTTP_METHOD = pyparsing.Word(pyparsing.alphanums + '-_') | _BLANK

  _INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(
      lambda tokens: int(tokens[0], 10)) | _BLANK

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _IP_ADDRESS = (
      pyparsing.pyparsing_common.ipv4_address |
      pyparsing.pyparsing_common.ipv6_address | _BLANK)

  PORT = pyparsing.Word(pyparsing.nums, max=6).setParseAction(
      lambda tokens: int(tokens[0], 10)) | _BLANK

  # Username can consist of: "domain.username", "domain\username",
  # "domain\user$" or "-" for an anonymous user.
  _USERNAME = pyparsing.Word(pyparsing.alphanums + '-.\\$') | _BLANK

  _URI_SAFE_CHARACTERS = '/.?&+;_=()-:,%'

  _URI = pyparsing.Word(pyparsing.alphanums + _URI_SAFE_CHARACTERS) | _BLANK

  _URI_STEM = (pyparsing.Word(
      pyparsing.alphanums + _URI_SAFE_CHARACTERS + '$') | _BLANK)

  # Per https://blogs.iis.net/nazim/use-of-special-characters-like-in-an-iis-url
  # IIS does not require that a query comply with RFC1738 restrictions on valid
  # URI characters
  _QUERY = (pyparsing.Word(
      pyparsing.alphanums + _URI_SAFE_CHARACTERS + '{}|\\^~[]`\'"<>@$') |
           _BLANK)

  _DATE = (
      _FOUR_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress('-') + _TWO_DIGITS)

  _TIME = (
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') + _TWO_DIGITS)

  _DATE_TIME_METADATA = (
      pyparsing.Suppress('Date: ') +
      _DATE.setResultsName('date') +
      _TIME.setResultsName('time'))

  _FIELDS_METADATA = (
      pyparsing.Suppress('Fields: ') +
      pyparsing.restOfLine().setResultsName('fields'))

  _METADATA = (
      _DATE_TIME_METADATA | _FIELDS_METADATA | pyparsing.restOfLine())

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _COMMENT_LOG_LINE = pyparsing.Suppress('#') + _METADATA + _END_OF_LINE

  # IIS 6.x fields: date time s-sitename s-ip cs-method cs-uri-stem
  # cs-uri-query s-port cs-username c-ip cs(User-Agent) sc-status
  # sc-substatus sc-win32-status

  _IIS_6_0_LOG_LINE = (
      _DATE.setResultsName('date') +
      _TIME.setResultsName('time') +
      _URI.setResultsName('s_sitename') +
      _IP_ADDRESS.setResultsName('dest_ip') +
      _HTTP_METHOD.setResultsName('http_method') +
      _URI.setResultsName('cs_uri_stem') +
      _URI.setResultsName('cs_uri_query') +
      PORT.setResultsName('dest_port') +
      _USERNAME.setResultsName('cs_username') +
      _IP_ADDRESS.setResultsName('source_ip') +
      _URI.setResultsName('user_agent') +
      _INTEGER.setResultsName('sc_status') +
      _INTEGER.setResultsName('sc_substatus') +
      _INTEGER.setResultsName('sc_win32_status') +
      _END_OF_LINE)

  # IIS 7.x fields: date time s-ip cs-method cs-uri-stem cs-uri-query
  # s-port cs-username c-ip cs(User-Agent) sc-status sc-substatus
  # sc-win32-status time-taken

  _LOG_LINE_STRUCTURES = {}

  # Common fields. Set results name with underscores, not hyphens because regex
  # will not pick them up.

  _LOG_LINE_STRUCTURES['date'] = _DATE.setResultsName('date')
  _LOG_LINE_STRUCTURES['time'] = _TIME.setResultsName('time')
  _LOG_LINE_STRUCTURES['s-sitename'] = _URI.setResultsName('s_sitename')
  _LOG_LINE_STRUCTURES['s-ip'] = _IP_ADDRESS.setResultsName('dest_ip')
  _LOG_LINE_STRUCTURES['cs-method'] = _HTTP_METHOD.setResultsName('http_method')
  _LOG_LINE_STRUCTURES['cs-uri-stem'] = _URI_STEM.setResultsName(
      'requested_uri_stem')
  _LOG_LINE_STRUCTURES['cs-uri-query'] = _QUERY.setResultsName('cs_uri_query')
  _LOG_LINE_STRUCTURES['s-port'] = PORT.setResultsName('dest_port')
  _LOG_LINE_STRUCTURES['cs-username'] = _USERNAME.setResultsName('cs_username')
  _LOG_LINE_STRUCTURES['c-ip'] = _IP_ADDRESS.setResultsName('source_ip')
  _LOG_LINE_STRUCTURES['cs(User-Agent)'] = _URI.setResultsName('user_agent')
  _LOG_LINE_STRUCTURES['sc-status'] = _INTEGER.setResultsName('http_status')
  _LOG_LINE_STRUCTURES['sc-substatus'] = _INTEGER.setResultsName(
      'sc_substatus')
  _LOG_LINE_STRUCTURES['sc-win32-status'] = _INTEGER.setResultsName(
      'sc_win32_status')

  # Less common fields.

  _LOG_LINE_STRUCTURES['s-computername'] = _URI.setResultsName('s_computername')
  _LOG_LINE_STRUCTURES['sc-bytes'] = _INTEGER.setResultsName('sent_bytes')
  _LOG_LINE_STRUCTURES['cs-bytes'] = _INTEGER.setResultsName('received_bytes')
  _LOG_LINE_STRUCTURES['time-taken'] = _INTEGER.setResultsName('time_taken')
  _LOG_LINE_STRUCTURES['cs-version'] = _URI.setResultsName('protocol_version')
  _LOG_LINE_STRUCTURES['cs-host'] = _URI.setResultsName('cs_host')
  _LOG_LINE_STRUCTURES['cs(Cookie)'] = _URI.setResultsName('cs_cookie')
  _LOG_LINE_STRUCTURES['cs(Referrer)'] = _URI.setResultsName('cs_referrer')
  _LOG_LINE_STRUCTURES['cs(Referer)'] = _URI.setResultsName('cs_referrer')

  # Define the available log line structures. Default to the IIS v. 6.0
  # common format.

  _HEADER_GRAMMAR = pyparsing.OneOrMore(_COMMENT_LOG_LINE)

  _LINE_STRUCTURES = [('log_line', _IIS_6_0_LOG_LINE)]

  _COMMENT_SOFTWARE_LINE = (
      pyparsing.Regex(
          '#Software: Microsoft Internet Information Services [0-9]+.[0-9]+') +
      _END_OF_LINE)

  VERIFICATION_GRAMMAR = (
      pyparsing.ZeroOrMore(
          pyparsing.Regex('#(Date|Fields|Version): .*') + _END_OF_LINE) +
      _COMMENT_SOFTWARE_LINE)

  VERIFICATION_LITERALS = [
      '#Software: Microsoft Internet Information Services ']

  def __init__(self):
    """Initializes a parser."""
    super(WinIISTextPlugin, self).__init__()
    self._day_of_month = None
    self._month = None
    self._year = None

  def _ParseFieldsMetadata(self, parser_mediator, fields):
    """Parses the fields metadata and updates the log line definition to match.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      fields (str): field definitions.
    """
    log_line_structure = pyparsing.Empty()
    for member in fields.split(' '):
      if not member:
        continue

      field_structure = self._LOG_LINE_STRUCTURES.get(member, None)
      if not field_structure:
        field_structure = self._URI
        parser_mediator.ProduceExtractionWarning(
            'missing definition for field: {0:s} defaulting to URI'.format(
                member))

      log_line_structure += field_structure

    log_line_structure += self._END_OF_LINE

    self._SetLineStructures([('log_line', log_line_structure)])

  def _ParseHeader(self, parser_mediator, text_reader):
    """Parses a text-log file header.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.

    Raises:
      ParseError: when the header cannot be parsed.
    """
    try:
      structure_generator = self._HEADER_GRAMMAR.scanString(
          text_reader.lines, maxMatches=1)
      structure, start, end = next(structure_generator)

    except StopIteration:
      structure = None

    except pyparsing.ParseException as exception:
      raise errors.ParseError(exception)

    if not structure or start != 0:
      raise errors.ParseError('No match found.')

    date_elements_tuple = self._GetValueFromStructure(structure, 'date')
    if date_elements_tuple:
      self._year, self._month, self._day_of_month = date_elements_tuple

    fields = self._GetValueFromStructure(structure, 'fields', default_value='')
    fields = fields.strip()
    if fields:
      self._ParseFieldsMetadata(parser_mediator, fields)

    text_reader.SkipAhead(end)

  def _ParseLogLine(self, parser_mediator, structure):
    """Parse a single log line.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      structure (pyparsing.ParseResults): tokens from a parsed log line.
    """
    event_data = IISEventData()
    event_data.cs_cookie = self._GetValueFromStructure(structure, 'cs_cookie')
    event_data.cs_host = self._GetValueFromStructure(structure, 'cs_host')
    event_data.cs_referrer = self._GetValueFromStructure(
        structure, 'cs_referrer')
    event_data.cs_uri_query = self._GetValueFromStructure(
        structure, 'cs_uri_query')
    event_data.cs_username = self._GetValueFromStructure(
        structure, 'cs_username')
    event_data.dest_ip = self._GetValueFromStructure(structure, 'dest_ip')
    event_data.dest_port = self._GetValueFromStructure(structure, 'dest_port')
    event_data.http_method = self._GetValueFromStructure(
        structure, 'http_method')
    event_data.http_status = self._GetValueFromStructure(
        structure, 'http_status')
    event_data.protocol_version = self._GetValueFromStructure(
        structure, 'protocol_version')
    event_data.last_written_time = self._ParseTimeElements(structure)
    event_data.received_bytes = self._GetValueFromStructure(
        structure, 'received_bytes')
    event_data.requested_uri_stem = self._GetValueFromStructure(
        structure, 'requested_uri_stem')
    event_data.s_computername = self._GetValueFromStructure(
        structure, 's_computername')
    event_data.sc_substatus = self._GetValueFromStructure(
        structure, 'sc_substatus')
    event_data.sc_win32_status = self._GetValueFromStructure(
        structure, 'sc_win32_status')
    event_data.sent_bytes = self._GetValueFromStructure(structure, 'sent_bytes')
    event_data.source_ip = self._GetValueFromStructure(structure, 'source_ip')
    event_data.s_sitename = self._GetValueFromStructure(structure, 's_sitename')
    event_data.time_taken = self._GetValueFromStructure(structure, 'time_taken')
    event_data.user_agent = self._GetValueFromStructure(structure, 'user_agent')

    parser_mediator.ProduceEventData(event_data)

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
    try:
      time_elements_structure = self._GetValueFromStructure(structure, 'time')

      hours, minutes, seconds = time_elements_structure

      date_elements_structure = self._GetValueFromStructure(structure, 'date')
      if date_elements_structure:
        year, month, day_of_month = date_elements_structure

        time_elements_tuple = (
            year, month, day_of_month, hours, minutes, seconds)
      else:
        time_elements_tuple = (
             self._year, self._month, self._day_of_month, hours, minutes,
             seconds)

      return dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse time elements with error: {0!s}'.format(exception))

  def _ResetState(self):
    """Resets stored values."""
    self._day_of_month = None
    self._month = None
    self._year = None

    self._SetLineStructures(self._LINE_STRUCTURES)

  def CheckRequiredFormat(self, parser_mediator, text_reader):
    """Check if the log record has the minimal structure required by the plugin.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    try:
      self._VerifyString(text_reader.lines)
    except errors.ParseError:
      return False

    self._ResetState()

    return True


text_parser.TextLogParser.RegisterPlugin(WinIISTextPlugin)
