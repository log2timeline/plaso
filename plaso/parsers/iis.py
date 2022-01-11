# -*- coding: utf-8 -*-
"""Parser for Windows IIS Log file."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import errors
from plaso.parsers import manager
from plaso.parsers import text_parser


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


class WinIISParser(text_parser.PyparsingSingleLineTextParser):
  """Parses a Microsoft IIS log file."""

  NAME = 'winiis'
  DATA_FORMAT = 'Microsoft IIS log file'

  MAX_LINE_LENGTH = 800

  BLANK = pyparsing.Literal('-')
  WORD = pyparsing.Word(pyparsing.alphanums + '-') | BLANK

  INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(
      text_parser.ConvertTokenToInteger) | BLANK

  IP_ADDRESS = (
      text_parser.PyparsingConstants.IPV4_ADDRESS |
      text_parser.PyparsingConstants.IPV6_ADDRESS | BLANK)

  PORT = pyparsing.Word(pyparsing.nums, max=6).setParseAction(
      text_parser.ConvertTokenToInteger) | BLANK

  # Username can consist of: domain.username
  USERNAME = pyparsing.Word(pyparsing.alphanums + '.-') | BLANK

  _URI_SAFE_CHARACTERS = '/.?&+;_=()-:,%'
  _URI_UNSAFE_CHARACTERS = '{}|\\^~[]`\'"<>'

  URI = pyparsing.Word(pyparsing.alphanums + _URI_SAFE_CHARACTERS) | BLANK

  # Per https://blogs.iis.net/nazim/use-of-special-characters-like-in-an-iis-url
  # IIS does not require that a query comply with RFC1738 restrictions on valid
  # URI characters
  QUERY = (pyparsing.Word(
      pyparsing.alphanums + _URI_SAFE_CHARACTERS + _URI_UNSAFE_CHARACTERS) |
           BLANK)

  DATE_TIME = (
      text_parser.PyparsingConstants.DATE_ELEMENTS +
      text_parser.PyparsingConstants.TIME_ELEMENTS)

  DATE_METADATA = (
      pyparsing.Literal('Date:') + DATE_TIME.setResultsName('date_time'))

  FIELDS_METADATA = (
      pyparsing.Literal('Fields:') +
      pyparsing.SkipTo(pyparsing.LineEnd()).setResultsName('fields'))

  COMMENT = pyparsing.Literal('#') + (
      DATE_METADATA | FIELDS_METADATA | pyparsing.SkipTo(pyparsing.LineEnd()))

  # IIS 6.x fields: date time s-sitename s-ip cs-method cs-uri-stem
  # cs-uri-query s-port cs-username c-ip cs(User-Agent) sc-status
  # sc-substatus sc-win32-status

  LOG_LINE_6_0 = (
      DATE_TIME.setResultsName('date_time') +
      URI.setResultsName('s_sitename') +
      IP_ADDRESS.setResultsName('dest_ip') +
      WORD.setResultsName('http_method') +
      URI.setResultsName('cs_uri_stem') +
      URI.setResultsName('cs_uri_query') +
      PORT.setResultsName('dest_port') +
      WORD.setResultsName('cs_username') +
      IP_ADDRESS.setResultsName('source_ip') +
      URI.setResultsName('user_agent') +
      INTEGER.setResultsName('sc_status') +
      INTEGER.setResultsName('sc_substatus') +
      INTEGER.setResultsName('sc_win32_status'))

  # IIS 7.x fields: date time s-ip cs-method cs-uri-stem cs-uri-query
  # s-port cs-username c-ip cs(User-Agent) sc-status sc-substatus
  # sc-win32-status time-taken

  _LOG_LINE_STRUCTURES = {}

  # Common fields. Set results name with underscores, not hyphens because regex
  # will not pick them up.
  _LOG_LINE_STRUCTURES['date'] = (
      text_parser.PyparsingConstants.DATE.setResultsName('date'))
  _LOG_LINE_STRUCTURES['time'] = (
      text_parser.PyparsingConstants.TIME.setResultsName('time'))
  _LOG_LINE_STRUCTURES['s-sitename'] = URI.setResultsName('s_sitename')
  _LOG_LINE_STRUCTURES['s-ip'] = IP_ADDRESS.setResultsName('dest_ip')
  _LOG_LINE_STRUCTURES['cs-method'] = WORD.setResultsName('http_method')
  _LOG_LINE_STRUCTURES['cs-uri-stem'] = URI.setResultsName(
      'requested_uri_stem')
  _LOG_LINE_STRUCTURES['cs-uri-query'] = QUERY.setResultsName('cs_uri_query')
  _LOG_LINE_STRUCTURES['s-port'] = PORT.setResultsName('dest_port')
  _LOG_LINE_STRUCTURES['cs-username'] = USERNAME.setResultsName('cs_username')
  _LOG_LINE_STRUCTURES['c-ip'] = IP_ADDRESS.setResultsName('source_ip')
  _LOG_LINE_STRUCTURES['cs(User-Agent)'] = URI.setResultsName('user_agent')
  _LOG_LINE_STRUCTURES['sc-status'] = INTEGER.setResultsName('http_status')
  _LOG_LINE_STRUCTURES['sc-substatus'] = INTEGER.setResultsName(
      'sc_substatus')
  _LOG_LINE_STRUCTURES['sc-win32-status'] = INTEGER.setResultsName(
      'sc_win32_status')

  # Less common fields.
  _LOG_LINE_STRUCTURES['s-computername'] = URI.setResultsName('s_computername')
  _LOG_LINE_STRUCTURES['sc-bytes'] = INTEGER.setResultsName('sent_bytes')
  _LOG_LINE_STRUCTURES['cs-bytes'] = INTEGER.setResultsName('received_bytes')
  _LOG_LINE_STRUCTURES['time-taken'] = INTEGER.setResultsName('time_taken')
  _LOG_LINE_STRUCTURES['cs-version'] = URI.setResultsName('protocol_version')
  _LOG_LINE_STRUCTURES['cs-host'] = URI.setResultsName('cs_host')
  _LOG_LINE_STRUCTURES['cs(Cookie)'] = URI.setResultsName('cs_cookie')
  _LOG_LINE_STRUCTURES['cs(Referrer)'] = URI.setResultsName('cs_referrer')
  _LOG_LINE_STRUCTURES['cs(Referer)'] = URI.setResultsName('cs_referrer')

  # Define the available log line structures. Default to the IIS v. 6.0
  # common format.
  LINE_STRUCTURES = [
      ('comment', COMMENT),
      ('logline', LOG_LINE_6_0)]

  # Define a signature value for the log file.
  _SIGNATURE = '#Software: Microsoft Internet Information Services'

  # Log file are all extended ASCII encoded unless UTF-8 is explicitly enabled.
  _ENCODING = 'utf-8'

  def __init__(self):
    """Initializes a parser."""
    super(WinIISParser, self).__init__()
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
      log_line_structure += self.DATE_TIME.setResultsName('date_time')
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

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a log record structure and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): structure parsed from the log file.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in ('comment', 'logline'):
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    if key == 'logline':
      self._ParseLogLine(parser_mediator, structure)
    elif key == 'comment':
      self._ParseComment(parser_mediator, structure)

  # pylint: disable=unused-argument
  def VerifyStructure(self, parser_mediator, line):
    """Verify that this file is an IIS log file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between
          parsers and other components, such as storage and dfVFS.
      line (str): line from a text file.

    Returns:
      bool: True if the line was successfully parsed.
    """
    self._SetLineStructures(self.LINE_STRUCTURES)

    self._day_of_month = None
    self._month = None
    self._year = None

    # TODO: Examine other versions of the file format and if this parser should
    # support them. For now just checking if it contains the IIS header.
    if self._SIGNATURE in line:
      return True

    return False


manager.ParsersManager.RegisterParser(WinIISParser)
