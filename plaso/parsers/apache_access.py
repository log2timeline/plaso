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
    http_request_referer (str): http request referer header information.
    http_request (str): first line of http request.
    http_request_user_agent (str): http request user agent header information.
    http_response_bytes (int): http response bytes size without headers.
    http_response_code (int): http response code from server.
    ip_address (str): IPv4 or IPv6 addresses.
    port_number (int): canonical port of the server serving the request.
    remote_name (str): remote logname (from identd, if supplied).
    server_name (str): canonical hostname of the server serving the request.
    user_name (str): logged user name.
  """

  DATA_TYPE = 'apache:access'

  def __init__(self):
    """Initializes event data."""
    super(ApacheAccessEventData, self).__init__(data_type=self.DATA_TYPE)
    self.http_request = None
    self.http_request_referer = None
    self.http_request_user_agent = None
    self.http_response_bytes = None
    self.http_response_code = None
    self.ip_address = None
    self.port_number = None
    self.remote_name = None
    self.server_name = None
    self.user_name = None


class ApacheAccessParser(text_parser.PyparsingSingleLineTextParser):
  """Apache access log file parser"""

  NAME = 'apache_access'
  DESCRIPTION = 'Apache access Parser'

  MAX_LINE_LENGTH = 2048

  # Date format [18/Sep/2011:19:18:28 -0400]
  _DATE_TIME = pyparsing.Group(
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

  _HTTP_REQUEST = (
      pyparsing.Suppress('"') +
      pyparsing.SkipTo('"').setResultsName('http_request') +
      pyparsing.Suppress('"'))

  _PORT_NUMBER = text_parser.PyparsingConstants.INTEGER.setResultsName(
      'port_number')

  _REMOTE_NAME = (
      pyparsing.Word(pyparsing.alphanums) |
      pyparsing.Literal('-')).setResultsName('remote_name')

  _RESPONSE_BYTES = (
      pyparsing.Literal('-') |
      text_parser.PyparsingConstants.INTEGER).setResultsName('response_bytes')

  _REFERER = (
      pyparsing.Suppress('"') +
      pyparsing.SkipTo('"').setResultsName('referer') +
      pyparsing.Suppress('"'))

  _SERVER_NAME = (
      pyparsing.Word(pyparsing.alphanums + '-' + '.').setResultsName(
          'server_name'))

  _USER_AGENT = (
      pyparsing.Suppress('"') +
      pyparsing.SkipTo('"').setResultsName('user_agent') +
      pyparsing.Suppress('"'))

  _USER_NAME = (
      pyparsing.Word(pyparsing.alphanums) |
      pyparsing.Literal('-')).setResultsName('user_name')

  # Defined in https://httpd.apache.org/docs/2.4/logs.html
  # format: "%h %l %u %t \"%r\" %>s %b"
  _COMMON_LOG_FORMAT_LINE = (
      text_parser.PyparsingConstants.IP_ADDRESS.setResultsName('ip_address') +
      _REMOTE_NAME +
      _USER_NAME +
      _DATE_TIME +
      _HTTP_REQUEST +
      text_parser.PyparsingConstants.INTEGER.setResultsName('response_code') +
      _RESPONSE_BYTES +
      pyparsing.lineEnd())

  # Defined in https://httpd.apache.org/docs/2.4/logs.html
  # format: "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-agent}i\""
  _COMBINED_LOG_FORMAT_LINE = (
      text_parser.PyparsingConstants.IP_ADDRESS.setResultsName('ip_address') +
      _REMOTE_NAME +
      _USER_NAME +
      _DATE_TIME +
      _HTTP_REQUEST +
      text_parser.PyparsingConstants.INTEGER.setResultsName('response_code') +
      _RESPONSE_BYTES +
      _REFERER +
      _USER_AGENT +
      pyparsing.lineEnd())

  # "vhost_combined" format as used by Debian and related distributions.
  # "%v:%p %h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\""
  _VHOST_COMBINED_LOG_FORMAT = (
      _SERVER_NAME +
      pyparsing.Suppress(':') +
      _PORT_NUMBER +
      text_parser.PyparsingConstants.IP_ADDRESS.setResultsName('ip_address') +
      _REMOTE_NAME +
      _USER_NAME +
      _DATE_TIME +
      _HTTP_REQUEST +
      text_parser.PyparsingConstants.INTEGER.setResultsName('response_code') +
      _RESPONSE_BYTES +
      _REFERER +
      _USER_AGENT +
      pyparsing.lineEnd()
  )

  LINE_STRUCTURES = [
      ('combined_log_format', _COMBINED_LOG_FORMAT_LINE),
      ('common_log_format', _COMMON_LOG_FORMAT_LINE),
      ('vhost_combined_log_format', _VHOST_COMBINED_LOG_FORMAT)]

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
    month = self._GetValueFromStructure(structure, 'month')

    try:
      month = timelib.MONTH_DICT.get(month.lower(), 0)
    except AttributeError as exception:
      raise ValueError('unable to parse month with error: {0!s}.'.format(
          exception))

    time_offset = self._GetValueFromStructure(structure, 'time_offset')

    try:
      time_offset_hours = int(time_offset[1:3], 10)
      time_offset_minutes = int(time_offset[3:5], 10)
    except (IndexError, TypeError, ValueError) as exception:
      raise ValueError(
          'unable to parse time zone offset with error: {0!s}.'.format(
              exception))

    year = self._GetValueFromStructure(structure, 'year')
    day_of_month = self._GetValueFromStructure(structure, 'day')
    hours = self._GetValueFromStructure(structure, 'hours')
    minutes = self._GetValueFromStructure(structure, 'minutes')
    seconds = self._GetValueFromStructure(structure, 'seconds')

    try:
      date_time_string = (
          '{0:04d}-{1:02d}-{2:02d}T{3:02d}:{4:02d}:{5:02d}.000000'
          '{6:s}{7:02d}:{8:02d}').format(
              year, month, day_of_month, hours, minutes, seconds,
              time_offset[0], time_offset_hours, time_offset_minutes)
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

    date_time_string = self._GetValueFromStructure(structure, 'date_time')

    try:
      iso_date_time = self._GetISO8601String(date_time_string)
      date_time.CopyFromStringISO8601(iso_date_time)
    except ValueError:
      parser_mediator.ProduceExtractionWarning(
          'invalid date time value: {0!s}'.format(date_time_string))
      return

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_RECORDED)

    event_data = ApacheAccessEventData()
    event_data.ip_address = self._GetValueFromStructure(structure, 'ip_address')
    event_data.remote_name = self._GetValueFromStructure(
        structure, 'remote_name')
    event_data.user_name = self._GetValueFromStructure(structure, 'user_name')
    event_data.http_request = self._GetValueFromStructure(
        structure, 'http_request')
    event_data.http_response_code = self._GetValueFromStructure(
        structure, 'response_code')
    event_data.http_response_bytes = self._GetValueFromStructure(
        structure, 'response_bytes')

    if key in ('combined_log_format', 'vhost_combined_log_format'):
      event_data.http_request_referer = self._GetValueFromStructure(
          structure, 'referer')
      event_data.http_request_user_agent = self._GetValueFromStructure(
          structure, 'user_agent')

    if key == 'vhost_combined_log_format':
      event_data.server_name = self._GetValueFromStructure(
          structure, 'server_name')
      event_data.port_number = self._GetValueFromStructure(
          structure, 'port_number')

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
