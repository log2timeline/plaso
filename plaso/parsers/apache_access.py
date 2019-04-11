# -*- coding: utf-8 -*-
"""Apache access log (access.log) parser.

Parser based on the two default apache formats, common and combined log format
defined in https://httpd.apache.org/docs/2.4/logs.html
"""

from __future__ import unicode_literals

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements
from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import text_parser


class ApacheAccessEventData(events.EventData):
  """Apache access event data.

  Attributes:
    ip_address (str): IPv4 or IPv6 addresses.
    remote_name (str): remote logname (from identd, if supplied).
    user_name (str): logged user name.
    http_request (str): first line of http request.
    http_response_code (int): http response code from server.
    http_response_bytes (int): http response bytes size without headers.
    http_request_referer (str): http request referer header information.
    http_request_user_agent (str): http request user agent header information.
  """

  DATA_TYPE = 'apache:access'

  def __init__(self):
    """Initializes event data."""
    super(ApacheAccessEventData, self).__init__(data_type=self.DATA_TYPE)
    self.ip_address = None
    self.remote_name = None
    self.user_name = None
    self.http_request = None
    self.http_response_code = None
    self.http_response_bytes = None
    self.http_request_referer = None
    self.http_request_user_agent = None


class ApacheAccessParser(text_parser.PyparsingSingleLineTextParser):
  """Apache access log file parser"""

  NAME = 'apache_access'
  DESCRIPTION = 'Apache access Parser'

  _PYPARSING_COMPONENTS = {
      'ip': text_parser.PyparsingConstants.IP_ADDRESS.setResultsName(
          'ip_address'),
      'remote_name': (pyparsing.Word(pyparsing.alphanums) |
                      pyparsing.Literal('-')).setResultsName('remote_name'),
      'user_name': (pyparsing.Word(pyparsing.alphanums) |
                    pyparsing.Literal('-')).setResultsName('user_name'),
      'http_request': pyparsing.SkipTo('"').setResultsName('http_request'),
      'response_code': text_parser.PyparsingConstants.INTEGER.setResultsName(
          'response_code'),
      'response_bytes':  text_parser.PyparsingConstants.INTEGER.setResultsName(
          'response_bytes'),
      'referer': pyparsing.SkipTo('"').setResultsName('referer'),
      'user_agent': pyparsing.SkipTo('"').setResultsName('user_agent')
  }

  # date format [18/Sep/2011:19:18:28 -0400]
  _PYPARSING_COMPONENTS['date'] = pyparsing.Group(
      pyparsing.Suppress('[') +
      text_parser.PyparsingConstants.TWO_DIGITS.setResultsName('day') +
      pyparsing.Suppress('/') +
      text_parser.PyparsingConstants.THREE_LETTERS.setResultsName('month') +
      pyparsing.Suppress('/') +
      text_parser.PyparsingConstants.FOUR_DIGITS.setResultsName('year') +
      pyparsing.Suppress(':') +
      text_parser.PyparsingConstants.TWO_DIGITS.setResultsName('hours') +
      pyparsing.Suppress(':') +
      text_parser.PyparsingConstants.TWO_DIGITS.setResultsName('minutes') +
      pyparsing.Suppress(':') +
      text_parser.PyparsingConstants.TWO_DIGITS.setResultsName('seconds') +
      pyparsing.Combine(
          pyparsing.oneOf(['-', '+']) +
          pyparsing.Word(
              pyparsing.nums, exact=4)).setResultsName('time_offset') +
      pyparsing.Suppress(']')).setResultsName('date_time')

  _SKIP_SEP = pyparsing.Suppress('"')

  # Defined in https://httpd.apache.org/docs/2.4/logs.html
  # format: "%h %l %u %t \"%r\" %>s %b"
  _COMMON_LOG_FORMAT = (
      _PYPARSING_COMPONENTS['ip'] +
      _PYPARSING_COMPONENTS['remote_name'] +
      _PYPARSING_COMPONENTS['user_name'] +
      _PYPARSING_COMPONENTS['date'] +
      _SKIP_SEP + _PYPARSING_COMPONENTS['http_request'] + _SKIP_SEP +
      _PYPARSING_COMPONENTS['response_code'] +
      _PYPARSING_COMPONENTS['response_bytes']
  )

  # Defined in https://httpd.apache.org/docs/2.4/logs.html
  # format: "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-agent}i\""
  _COMBINED_LOG_FORMAT = (
      _COMMON_LOG_FORMAT +
      _SKIP_SEP + _PYPARSING_COMPONENTS['referer'] + _SKIP_SEP +
      _SKIP_SEP + _PYPARSING_COMPONENTS['user_agent'] + _SKIP_SEP
  )

  _COMMON_LOG_FORMAT_LINE = _COMMON_LOG_FORMAT + pyparsing.lineEnd
  _COMBINED_LOG_FORMAT_LINE = _COMBINED_LOG_FORMAT + pyparsing.lineEnd

  LINE_STRUCTURES = [
      ('combined_log_format', _COMBINED_LOG_FORMAT_LINE),
      ('common_log_format', _COMMON_LOG_FORMAT_LINE)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in LINE_STRUCTURES])

  # TODO: migrate function after dfdatetime issue #47 is fixed.
  def _GetISO8601String(self, structure):
    """Normalize date time parsed format to an ISO 8601 date time string.
    The date and time values in Apache access log files are formatted as:
    "[18/Sep/2011:19:18:28 -0400]".

    Args:
      structure (pyparsing.ParseResults): structure of tokens derived from a
          line of a text file.

    Returns:
      str: ISO 8601 date time string.

    Raises:
      ValueError: if the structure cannot be converted into a date time string.
    """
    time_offset = structure.time_offset
    month = timelib.MONTH_DICT.get(structure.month.lower(), 0)

    try:
      time_offset_hours = int(time_offset[1:3], 10)
      time_offset_minutes = int(time_offset[3:5], 10)
    except (IndexError, TypeError, ValueError) as exception:
      raise ValueError(
          'unable to parse time zone offset with error: {0!s}.'.format(
              exception))

    try:
      date_time_string = (
          '{0:04d}-{1:02d}-{2:02d}T{3:02d}:{4:02d}:{5:02d}.000000'
          '{6:s}{7:02d}:{8:02d}').format(
              structure.year, month, structure.day, structure.hours,
              structure.minutes, structure.seconds, time_offset[0],
              time_offset_hours, time_offset_minutes)
    except ValueError as exception:
      raise ValueError(
          'unable to format date time string with error: {0!s}.'.format(
              exception))

    return date_time_string

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a matching entry.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
        and other components, such as storage and dfvfs.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): elements parsed from the file.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in self._SUPPORTED_KEYS:
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    date_time = dfdatetime_time_elements.TimeElements()

    try:
      iso_date_time = self._GetISO8601String(structure.date_time)
      date_time.CopyFromStringISO8601(iso_date_time)
    except ValueError:
      parser_mediator.ProduceExtractionWarning(
          'invalid date time value: {0!s}'.format(structure.date_time))
      return

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_RECORDED)

    event_data = ApacheAccessEventData()
    event_data.ip_address = structure.ip_address
    event_data.remote_name = structure.remote_name
    event_data.user_name = structure.user_name
    event_data.http_request = structure.http_request
    event_data.http_response_code = structure.response_code
    event_data.http_response_bytes = structure.response_bytes

    if key == 'combined_log_format':
      event_data.http_request_referer = structure.referer
      event_data.http_request_user_agent = structure.user_agent

    parser_mediator.ProduceEventWithEventData(event, event_data)

  # pylint: disable=unused-argument
  def VerifyStructure(self, parser_mediator, line):
    """Verifies that this is an apache access log file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
        and other components, such as storage and dfvfs.
      line (str): line from the text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    return max([parser.matches(line) for _, parser in self.LINE_STRUCTURES])


manager.ParsersManager.RegisterParser(ApacheAccessParser)
