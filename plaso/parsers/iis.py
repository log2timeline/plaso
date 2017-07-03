# -*- coding: utf-8 -*-
"""Parser for Windows IIS Log file.

More documentation on fields can be found here:
http://www.microsoft.com/technet/prodtechnol/WindowsServer2003/Library/
IIS/676400bc-8969-4aa7-851a-9319490a9bbb.mspx?mfr=true
"""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import errors
from plaso.parsers import manager
from plaso.parsers import text_parser


__author__ = 'Ashley Holtz (ashley.a.holtz@gmail.com)'


class IISEventData(events.EventData):
  """IIS log event data.

  Attributes:
  """

  DATA_TYPE = u'iis:log:line'

  def __init__(self):
    """Initializes event data."""
    super(IISEventData, self).__init__(data_type=self.DATA_TYPE)


class WinIISParser(text_parser.PyparsingSingleLineTextParser):
  """Parses a Microsoft IIS log file."""

  NAME = u'winiis'
  DESCRIPTION = u'Parser for Microsoft IIS log files.'

  # Common Fields (6.0: date time s-sitename s-ip cs-method cs-uri-stem
  # cs-uri-query s-port cs-username c-ip cs(User-Agent) sc-status
  # sc-substatus sc-win32-status.
  # Common Fields (7.5): date time s-ip cs-method cs-uri-stem cs-uri-query
  # s-port cs-username c-ip cs(User-Agent) sc-status sc-substatus
  # sc-win32-status time-taken

  BLANK = pyparsing.Literal(u'-')
  WORD = pyparsing.Word(pyparsing.alphanums + u'-') | BLANK

  INTEGER = (
      pyparsing.Word(pyparsing.nums, min=1).setParseAction(
          text_parser.ConvertTokenToInteger) | BLANK)

  IP_ADDRESS = (
      text_parser.PyparsingConstants.IPV4_ADDRESS |
      text_parser.PyparsingConstants.IPV6_ADDRESS | BLANK)

  PORT = (
      pyparsing.Word(pyparsing.nums, min=1, max=6).setParseAction(
          text_parser.ConvertTokenToInteger) | BLANK)

  URI = pyparsing.Word(pyparsing.alphanums + u'/.?&+;_=()-:,%') | BLANK

  DATE_TIME = (
      text_parser.PyparsingConstants.DATE_ELEMENTS +
      text_parser.PyparsingConstants.TIME_ELEMENTS)

  DATE_METADATA = (
      pyparsing.Literal(u'Date:') + DATE_TIME.setResultsName(u'date_time'))

  FIELDS_METADATA = (
      pyparsing.Literal(u'Fields:') +
      pyparsing.SkipTo(pyparsing.LineEnd()).setResultsName(u'fields'))

  COMMENT = pyparsing.Literal(u'#') + (
      DATE_METADATA | FIELDS_METADATA | pyparsing.SkipTo(pyparsing.LineEnd()))

  LOG_LINE_6_0 = (
      DATE_TIME.setResultsName(u'date_time') +
      URI.setResultsName(u's_sitename') +
      IP_ADDRESS.setResultsName(u'dest_ip') +
      WORD.setResultsName(u'http_method') +
      URI.setResultsName(u'cs_uri_stem') +
      URI.setResultsName(u'cs_uri_query') +
      PORT.setResultsName(u'dest_port') +
      WORD.setResultsName(u'cs_username') +
      IP_ADDRESS.setResultsName(u'source_ip') +
      URI.setResultsName(u'user_agent') +
      INTEGER.setResultsName(u'sc_status') +
      INTEGER.setResultsName(u'sc_substatus') +
      INTEGER.setResultsName(u'sc_win32_status'))

  _LOG_LINE_STRUCTURES = {}

  # Common fields. Set results name with underscores, not hyphens because regex
  # will not pick them up.
  _LOG_LINE_STRUCTURES[u'date'] = (
      text_parser.PyparsingConstants.DATE.setResultsName(u'date'))
  _LOG_LINE_STRUCTURES[u'time'] = (
      text_parser.PyparsingConstants.TIME.setResultsName(u'time'))
  _LOG_LINE_STRUCTURES[u's-sitename'] = URI.setResultsName(u's_sitename')
  _LOG_LINE_STRUCTURES[u's-ip'] = IP_ADDRESS.setResultsName(u'dest_ip')
  _LOG_LINE_STRUCTURES[u'cs-method'] = WORD.setResultsName(u'http_method')
  _LOG_LINE_STRUCTURES[u'cs-uri-stem'] = URI.setResultsName(
      u'requested_uri_stem')
  _LOG_LINE_STRUCTURES[u'cs-uri-query'] = URI.setResultsName(u'cs_uri_query')
  _LOG_LINE_STRUCTURES[u's-port'] = PORT.setResultsName(u'dest_port')
  _LOG_LINE_STRUCTURES[u'cs-username'] = WORD.setResultsName(u'cs_username')
  _LOG_LINE_STRUCTURES[u'c-ip'] = IP_ADDRESS.setResultsName(u'source_ip')
  _LOG_LINE_STRUCTURES[u'cs(User-Agent)'] = URI.setResultsName(u'user_agent')
  _LOG_LINE_STRUCTURES[u'sc-status'] = INTEGER.setResultsName(u'http_status')
  _LOG_LINE_STRUCTURES[u'sc-substatus'] = INTEGER.setResultsName(
      u'sc_substatus')
  _LOG_LINE_STRUCTURES[u'sc-win32-status'] = INTEGER.setResultsName(
      u'sc_win32_status')

  # Less common fields.
  _LOG_LINE_STRUCTURES[u's-computername'] = URI.setResultsName(
      u's_computername')
  _LOG_LINE_STRUCTURES[u'sc-bytes'] = INTEGER.setResultsName(u'sent_bytes')
  _LOG_LINE_STRUCTURES[u'cs-bytes'] = INTEGER.setResultsName(u'received_bytes')
  _LOG_LINE_STRUCTURES[u'time-taken'] = INTEGER.setResultsName(u'time_taken')
  _LOG_LINE_STRUCTURES[u'cs-version'] = URI.setResultsName(u'protocol_version')
  _LOG_LINE_STRUCTURES[u'cs-host'] = URI.setResultsName(u'cs_host')
  _LOG_LINE_STRUCTURES[u'cs(Cookie)'] = URI.setResultsName(u'cs_cookie')
  _LOG_LINE_STRUCTURES[u'cs(Referrer)'] = URI.setResultsName(u'cs_referrer')
  _LOG_LINE_STRUCTURES[u'cs(Referer)'] = URI.setResultsName(u'cs_referrer')

  # Define the available log line structures. Default to the IIS v. 6.0
  # common format.
  LINE_STRUCTURES = [
      (u'comment', COMMENT),
      (u'logline', LOG_LINE_6_0)]

  # Define a signature value for the log file.
  _SIGNATURE = b'#Software: Microsoft Internet Information Services'

  def __init__(self):
    """Initializes a parser object."""
    super(WinIISParser, self).__init__()
    self._day_of_month = None
    self._month = None
    self._year = None

  def _ParseComment(self, structure):
    """Parses a comment.

    Args:
      structure (pyparsing.ParseResults): structure parsed from the log file.
    """
    if structure[1] == u'Date:':
      self._year, self._month, self._day_of_month, _, _, _ = structure.date_time
    elif structure[1] == u'Fields:':
      self._ParseFieldsMetadata(structure)

  def _ParseFieldsMetadata(self, structure):
    """Parses the fields metadata.

    Args:
      structure (pyparsing.ParseResults): structure parsed from the log file.
    """
    fields = structure.fields.split(u' ')

    log_line_structure = pyparsing.Empty()
    if fields[0] == u'date' and fields[1] == u'time':
      log_line_structure += self.DATE_TIME.setResultsName(u'date_time')
      fields = fields[2:]

    for member in fields:
      log_line_structure += self._LOG_LINE_STRUCTURES.get(member, self.URI)

    # TODO: self._line_structures is a work-around and this needs
    # a structural fix.
    self._line_structures[1] = (u'logline', log_line_structure)

  def _ParseLogLine(self, parser_mediator, structure):
    """Parse a single log line and produce an event object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      structure (pyparsing.ParseResults): structure parsed from the log file.
    """
    if structure.date_time:
      time_elements_tuple = structure.date_time

    elif structure.date and structure.time:
      year, month, day_of_month = structure.date
      hours, minutes, seconds = structure.time
      time_elements_tuple = (year, month, day_of_month, hours, minutes, seconds)

    elif structure.time:
      hours, minutes, seconds = structure.time
      time_elements_tuple = (
          self._year, self._month, self._day_of_month, hours, minutes, seconds)

    else:
      parser_mediator.ProduceExtractionError(u'missing date and time values')
      return

    try:
      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)
    except ValueError:
      parser_mediator.ProduceExtractionError(
          u'invalid date time value: {0!s}'.format(time_elements_tuple))
      return

    event_data = IISEventData()

    for key, value in iter(structure.items()):
      if key in (u'date', u'date_time', u'time') or value == u'-':
        continue

      if isinstance(value, pyparsing.ParseResults):
        value = u''.join(value)

      setattr(event_data, key, value)

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a log record structure and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): structure parsed from the log file.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in (u'comment', u'logline'):
      raise errors.ParseError(
          u'Unable to parse record, unknown structure: {0:s}'.format(key))

    if key == u'logline':
      self._ParseLogLine(parser_mediator, structure)
    elif key == u'comment':
      self._ParseComment(structure)

  def VerifyStructure(self, unused_parser_mediator, line):
    """Verify that this file is an IIS log file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      line (str): single line from the text file.

    Returns:
      bool: True if the line was successfully parsed.
    """
    # TODO: self._line_structures is a work-around and this needs
    # a structural fix.
    self._line_structures = self.LINE_STRUCTURES

    self._day_of_month = None
    self._month = None
    self._year = None

    # TODO: Examine other versions of the file format and if this parser should
    # support them. For now just checking if it contains the IIS header.
    if self._SIGNATURE in line:
      return True

    return False


manager.ParsersManager.RegisterParser(WinIISParser)
