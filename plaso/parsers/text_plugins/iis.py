# -*- coding: utf-8 -*-
"""Text parser plugin for Microsoft IIS log files."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
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

  _MAXIMUM_LINE_LENGTH = 800

  _BLANK = pyparsing.Literal('-')

  _WORD = pyparsing.Word(pyparsing.alphanums + '-') | _BLANK

  _INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(
      text_parser.ConvertTokenToInteger) | _BLANK

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      text_parser.PyParseIntCast)

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      text_parser.PyParseIntCast)

  _IP_ADDRESS = (
      pyparsing.pyparsing_common.ipv4_address |
      pyparsing.pyparsing_common.ipv6_address | _BLANK)

  PORT = pyparsing.Word(pyparsing.nums, max=6).setParseAction(
      text_parser.ConvertTokenToInteger) | _BLANK

  # Username can consist of: domain.username
  USERNAME = pyparsing.Word(pyparsing.alphanums + '.-') | _BLANK

  _URI_SAFE_CHARACTERS = '/.?&+;_=()-:,%'
  _URI_UNSAFE_CHARACTERS = '{}|\\^~[]`\'"<>'

  URI = pyparsing.Word(pyparsing.alphanums + _URI_SAFE_CHARACTERS) | _BLANK

  # Per https://blogs.iis.net/nazim/use-of-special-characters-like-in-an-iis-url
  # IIS does not require that a query comply with RFC1738 restrictions on valid
  # URI characters
  QUERY = (pyparsing.Word(
      pyparsing.alphanums + _URI_SAFE_CHARACTERS + _URI_UNSAFE_CHARACTERS) |
           _BLANK)

  _DATE_TIME = (
      _FOUR_DIGITS.setResultsName('year') + pyparsing.Suppress('-') +
      _TWO_DIGITS.setResultsName('month') + pyparsing.Suppress('-') +
      _TWO_DIGITS.setResultsName('day_of_month') +
      _TWO_DIGITS.setResultsName('hours') + pyparsing.Suppress(':') +
      _TWO_DIGITS.setResultsName('minutes') + pyparsing.Suppress(':') +
      _TWO_DIGITS.setResultsName('seconds')).setResultsName('date_time')

  FIELDS_METADATA = (
      pyparsing.Literal('Fields:') +
      pyparsing.SkipTo(pyparsing.LineEnd()).setResultsName('fields'))

  COMMENT = pyparsing.Literal('#') + (
      pyparsing.Literal('Date:') + _DATE_TIME | FIELDS_METADATA |
      pyparsing.SkipTo(pyparsing.LineEnd()))

  # IIS 6.x fields: date time s-sitename s-ip cs-method cs-uri-stem
  # cs-uri-query s-port cs-username c-ip cs(User-Agent) sc-status
  # sc-substatus sc-win32-status

  LOG_LINE_6_0 = (
      _DATE_TIME +
      URI.setResultsName('s_sitename') +
      _IP_ADDRESS.setResultsName('dest_ip') +
      _WORD.setResultsName('http_method') +
      URI.setResultsName('cs_uri_stem') +
      URI.setResultsName('cs_uri_query') +
      PORT.setResultsName('dest_port') +
      _WORD.setResultsName('cs_username') +
      _IP_ADDRESS.setResultsName('source_ip') +
      URI.setResultsName('user_agent') +
      _INTEGER.setResultsName('sc_status') +
      _INTEGER.setResultsName('sc_substatus') +
      _INTEGER.setResultsName('sc_win32_status'))

  # IIS 7.x fields: date time s-ip cs-method cs-uri-stem cs-uri-query
  # s-port cs-username c-ip cs(User-Agent) sc-status sc-substatus
  # sc-win32-status time-taken

  _LOG_LINE_STRUCTURES = {}

  # Common fields. Set results name with underscores, not hyphens because regex
  # will not pick them up.
  _LOG_LINE_STRUCTURES['date'] = pyparsing.Group(
      _FOUR_DIGITS.setResultsName('year') + pyparsing.Suppress('-') +
      _TWO_DIGITS.setResultsName('month') + pyparsing.Suppress('-') +
      _TWO_DIGITS.setResultsName('day_of_month')).setResultsName('date')

  _LOG_LINE_STRUCTURES['time'] = pyparsing.Group(
      _TWO_DIGITS.setResultsName('hours') + pyparsing.Suppress(':') +
      _TWO_DIGITS.setResultsName('minutes') + pyparsing.Suppress(':') +
      _TWO_DIGITS.setResultsName('seconds')).setResultsName('time')

  _LOG_LINE_STRUCTURES['s-sitename'] = URI.setResultsName('s_sitename')
  _LOG_LINE_STRUCTURES['s-ip'] = _IP_ADDRESS.setResultsName('dest_ip')
  _LOG_LINE_STRUCTURES['cs-method'] = _WORD.setResultsName('http_method')
  _LOG_LINE_STRUCTURES['cs-uri-stem'] = URI.setResultsName(
      'requested_uri_stem')
  _LOG_LINE_STRUCTURES['cs-uri-query'] = QUERY.setResultsName('cs_uri_query')
  _LOG_LINE_STRUCTURES['s-port'] = PORT.setResultsName('dest_port')
  _LOG_LINE_STRUCTURES['cs-username'] = USERNAME.setResultsName('cs_username')
  _LOG_LINE_STRUCTURES['c-ip'] = _IP_ADDRESS.setResultsName('source_ip')
  _LOG_LINE_STRUCTURES['cs(User-Agent)'] = URI.setResultsName('user_agent')
  _LOG_LINE_STRUCTURES['sc-status'] = _INTEGER.setResultsName('http_status')
  _LOG_LINE_STRUCTURES['sc-substatus'] = _INTEGER.setResultsName(
      'sc_substatus')
  _LOG_LINE_STRUCTURES['sc-win32-status'] = _INTEGER.setResultsName(
      'sc_win32_status')

  # Less common fields.
  _LOG_LINE_STRUCTURES['s-computername'] = URI.setResultsName('s_computername')
  _LOG_LINE_STRUCTURES['sc-bytes'] = _INTEGER.setResultsName('sent_bytes')
  _LOG_LINE_STRUCTURES['cs-bytes'] = _INTEGER.setResultsName('received_bytes')
  _LOG_LINE_STRUCTURES['time-taken'] = _INTEGER.setResultsName('time_taken')
  _LOG_LINE_STRUCTURES['cs-version'] = URI.setResultsName('protocol_version')
  _LOG_LINE_STRUCTURES['cs-host'] = URI.setResultsName('cs_host')
  _LOG_LINE_STRUCTURES['cs(Cookie)'] = URI.setResultsName('cs_cookie')
  _LOG_LINE_STRUCTURES['cs(Referrer)'] = URI.setResultsName('cs_referrer')
  _LOG_LINE_STRUCTURES['cs(Referer)'] = URI.setResultsName('cs_referrer')

  # Define the available log line structures. Default to the IIS v. 6.0
  # common format.
  _LINE_STRUCTURES = [
      ('comment', COMMENT),
      ('logline', LOG_LINE_6_0)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in _LINE_STRUCTURES])

  def __init__(self):
    """Initializes a parser."""
    super(WinIISTextPlugin, self).__init__()
    self._day_of_month = None
    self._month = None
    self._year = None

  def _ParseComment(self, parser_mediator, structure):
    """Parses a comment.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      structure (pyparsing.ParseResults): structure parsed from a comment in
          the log file.
    """
    if structure[1] == 'Date:':
      time_elements_tuple = self._GetValueFromStructure(structure, 'date_time')
      self._year, self._month, self._day_of_month, _, _, _ = time_elements_tuple

    elif structure[1] == 'Fields:':
      self._ParseFieldsMetadata(parser_mediator, structure)

  def _ParseFieldsMetadata(self, parser_mediator, structure):
    """Parses the fields metadata and updates the log line definition to match.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      structure (pyparsing.ParseResults): structure parsed from the log file.
    """
    fields = self._GetValueFromStructure(structure, 'fields', default_value='')
    fields = fields.strip()
    fields = fields.split(' ')

    log_line_structure = pyparsing.Empty()
    if fields[0] == 'date' and fields[1] == 'time':
      log_line_structure += self._DATE_TIME
      fields = fields[2:]

    for member in fields:
      if not member:
        continue

      field_structure = self._LOG_LINE_STRUCTURES.get(member, None)
      if not field_structure:
        field_structure = self.URI
        parser_mediator.ProduceExtractionWarning(
            'missing definition for field: {0:s} defaulting to URI'.format(
                member))

      log_line_structure += field_structure

    line_structures = [
      ('comment', self.COMMENT),
      ('logline', log_line_structure)]
    self._SetLineStructures(line_structures)

  def _ParseLogLine(self, parser_mediator, structure):
    """Parse a single log line and produce an event object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      structure (pyparsing.ParseResults): structure parsed from the log file.
    """
    time_elements_structure = structure.get('date_time', None)
    if time_elements_structure:
      # Ensure time_elements_tuple is not a pyparsing.ParseResults otherwise
      # copy.deepcopy() of the dfDateTime object will fail on Python 3.8 with:
      # "TypeError: 'str' object is not callable" due to pyparsing.ParseResults
      # overriding __getattr__ with a function that returns an empty string when
      # named token does not exists.
      year, month, day_of_month, hours, minutes, seconds = (
          time_elements_structure)

      time_elements_tuple = (year, month, day_of_month, hours, minutes, seconds)

    else:
      time_tuple = self._GetValueFromStructure(structure, 'time')
      if not time_tuple:
        parser_mediator.ProduceExtractionWarning('missing time values')
        return

      date_tuple = self._GetValueFromStructure(structure, 'date')
      if not date_tuple:
        time_elements_tuple = (
            self._year, self._month, self._day_of_month, time_tuple[0],
            time_tuple[1], time_tuple[2])

      else:
        time_elements_tuple = (
            date_tuple[0], date_tuple[1], date_tuple[2], time_tuple[0],
            time_tuple[1], time_tuple[2])

    try:
      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)
    except ValueError:
      parser_mediator.ProduceExtractionWarning(
          'invalid date time value: {0!s}'.format(time_elements_tuple))
      return

    event_data = IISEventData()
    event_data.cs_cookie = structure.get('cs_cookie', None)
    event_data.cs_host = structure.get('cs_host', None)
    event_data.cs_referrer = structure.get('cs_referrer', None)
    event_data.cs_uri_query = structure.get('cs_uri_query', None)
    event_data.cs_username = structure.get('cs_username', None)
    event_data.dest_ip = structure.get('dest_ip', None)
    event_data.dest_port = structure.get('dest_port', None)
    event_data.http_method = structure.get('http_method', None)
    event_data.http_status = structure.get('http_status', None)
    event_data.protocol_version = structure.get('protocol_version', None)
    event_data.received_bytes = structure.get('received_bytes', None)
    event_data.requested_uri_stem = structure.get('requested_uri_stem', None)
    event_data.s_computername = structure.get('s_computername', None)
    event_data.sc_substatus = structure.get('sc_substatus', None)
    event_data.sc_win32_status = structure.get('sc_win32_status', None)
    event_data.sent_bytes = structure.get('sent_bytes', None)
    event_data.source_ip = structure.get('source_ip', None)
    event_data.s_sitename = structure.get('s_sitename', None)
    event_data.time_taken = structure.get('time_taken', None)
    event_data.user_agent = structure.get('user_agent', None)

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def _ParseRecord(self, parser_mediator, key, structure):
    """Parses a pyparsing structure.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): tokens from a parsed log line.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in self._SUPPORTED_KEYS:
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    if key == 'logline':
      self._ParseLogLine(parser_mediator, structure)
    elif key == 'comment':
      self._ParseComment(parser_mediator, structure)

  def CheckRequiredFormat(self, parser_mediator, text_file_object):
    """Check if the log record has the minimal structure required by the plugin.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_file_object (dfvfs.TextFile): text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    try:
      line = self._ReadLineOfText(text_file_object)
    except UnicodeDecodeError:
      return False

    found_signature = False
    while line and line[0] == '#':
      if line.startswith('#Software: Microsoft Internet Information Services'):
        found_signature = True
        break

      try:
        line = self._ReadLineOfText(text_file_object)
      except UnicodeDecodeError:
        break

    self._day_of_month = None
    self._month = None
    self._year = None

    self._SetLineStructures(self._LINE_STRUCTURES)

    return found_signature


text_parser.SingleLineTextParser.RegisterPlugin(WinIISTextPlugin)
