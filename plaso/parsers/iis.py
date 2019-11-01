# -*- coding: utf-8 -*-
"""Parser for Windows IIS Log file.

More documentation on fields can be found here:
https://msdn.microsoft.com/en-us/library/ms525807(v=vs.90).aspx
"""

from __future__ import unicode_literals

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
  """

  DATA_TYPE = 'iis:log:line'

  def __init__(self):
    """Initializes event data."""
    super(IISEventData, self).__init__(data_type=self.DATA_TYPE)


class WinIISParser(text_parser.PyparsingSingleLineTextParser):
  """Parses a Microsoft IIS log file."""

  NAME = 'winiis'
  DESCRIPTION = 'Parser for Microsoft IIS log files.'

  # Common Fields (6.0: date time s-sitename s-ip cs-method cs-uri-stem
  # cs-uri-query s-port cs-username c-ip cs(User-Agent) sc-status
  # sc-substatus sc-win32-status.
  # Common Fields (7.5): date time s-ip cs-method cs-uri-stem cs-uri-query
  # s-port cs-username c-ip cs(User-Agent) sc-status sc-substatus
  # sc-win32-status time-taken

  BLANK = pyparsing.Literal('-')
  WORD = pyparsing.Word(pyparsing.alphanums + '-') | BLANK

  INTEGER = (
      pyparsing.Word(pyparsing.nums, min=1).setParseAction(
          text_parser.ConvertTokenToInteger) | BLANK)

  IP_ADDRESS = (
      text_parser.PyparsingConstants.IPV4_ADDRESS |
      text_parser.PyparsingConstants.IPV6_ADDRESS | BLANK)

  PORT = (
      pyparsing.Word(pyparsing.nums, min=1, max=6).setParseAction(
          text_parser.ConvertTokenToInteger) | BLANK)

  _URI_SAFE_CHARACTERS = '/.?&+;_=()-:,%'
  _URI_UNSAFE_CHARACTERS = '{}|\\^~[]`'

  URI = pyparsing.Word(pyparsing.alphanums + _URI_SAFE_CHARACTERS) | BLANK

  # Per https://blogs.iis.net/nazim/use-of-special-characters-like-in-an-iis-url
  # IIS does not require the a query comply with RFC1738 restrictions on valid
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
  _LOG_LINE_STRUCTURES['cs-username'] = WORD.setResultsName('cs_username')
  _LOG_LINE_STRUCTURES['c-ip'] = IP_ADDRESS.setResultsName('source_ip')
  _LOG_LINE_STRUCTURES['cs(User-Agent)'] = URI.setResultsName('user_agent')
  _LOG_LINE_STRUCTURES['sc-status'] = INTEGER.setResultsName('http_status')
  _LOG_LINE_STRUCTURES['sc-substatus'] = INTEGER.setResultsName(
      'sc_substatus')
  _LOG_LINE_STRUCTURES['sc-win32-status'] = INTEGER.setResultsName(
      'sc_win32_status')

  # Less common fields.
  _LOG_LINE_STRUCTURES['s-computername'] = URI.setResultsName(
      's_computername')
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

  # Per https://msdn.microsoft.com/en-us/library/ms525807(v=vs.90).aspx:
  # "log file format(s) are all ASCII text formats (unless UTF-8 is enabled for
  #  your Web sites)
  _ENCODING = 'utf-8'

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
    # TODO: refactor. Why is this method named _ParseComment when it extracts
    # the date and time?
    if structure[1] == 'Date:':
      time_elements_tuple = self._GetValueFromStructure(structure, 'date_time')
      self._year, self._month, self._day_of_month, _, _, _ = time_elements_tuple
    elif structure[1] == 'Fields:':
      self._ParseFieldsMetadata(structure)

  def _ParseFieldsMetadata(self, structure):
    """Parses the fields metadata and updates the log line definition to match.

    Args:
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
      log_line_structure += self._LOG_LINE_STRUCTURES.get(member, self.URI)

    updated_structures = []
    for line_structure in self._line_structures:
      if line_structure[0] != 'logline':
        updated_structures.append(line_structure)
    updated_structures.append(('logline', log_line_structure))
    # TODO: self._line_structures is a work-around and this needs
    # a structural fix.
    self._line_structures = updated_structures

  def _ParseLogLine(self, parser_mediator, structure):
    """Parse a single log line and produce an event object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      structure (pyparsing.ParseResults): structure parsed from the log file.
    """
    time_elements_tuple = self._GetValueFromStructure(structure, 'date_time')
    if not time_elements_tuple:
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

    for key, value in iter(structure.items()):
      if key in ('date', 'date_time', 'time') or value == '-':
        continue

      if isinstance(value, pyparsing.ParseResults):
        value = ''.join(value)

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
    if key not in ('comment', 'logline'):
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    if key == 'logline':
      self._ParseLogLine(parser_mediator, structure)
    elif key == 'comment':
      self._ParseComment(structure)

  # pylint: disable=unused-argument
  def VerifyStructure(self, parser_mediator, line):
    """Verify that this file is an IIS log file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between
          parsers and other components, such as storage and dfvfs.
      line (str): line from a text file.

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
