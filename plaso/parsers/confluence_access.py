# -*- coding: utf-8 -*-
"""Confluence access log (conf_access_log[DATE].log) file parser.

Per the definitions in
https://confluence.atlassian.com/doc/configure-access-logs-1044780567.html
"""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import manager
from plaso.parsers import text_parser


class ConfluenceAccessEventData(events.EventData):
  """Confluence access event data.

  Attributes:
    forwarded_for (str): request X-FORWARDED-FOR header value.
    http_request_method (str): HTTP request method.
    http_request_referer (str): HTTP request referer header information.
    http_request_uri (str): HTTP request URI.
    http_request_user_agent (str): HTTP request user agent header information.
    http_response_bytes (int): HTTP response bytes size without headers.
    http_response_code (int): HTTP response code from server.
    http_version (str): HTTP request version.
    process_duration (int): time taken to process the request in milliseconds.
    remote_name (str): remote  hostname or IP address
    thread_name (str): name of the thread that handled the request.
    user_name (str): response X-AUSERNAME header value.
  """

  DATA_TYPE = 'confluence:access'

  def __init__(self):
    """Initializes event data."""
    super(ConfluenceAccessEventData, self).__init__(data_type=self.DATA_TYPE)
    self.forwarded_for = None
    self.http_request_method = None
    self.http_request_referer = None
    self.http_request_uri = None
    self.http_request_user_agent = None
    self.http_response_bytes = None
    self.http_response_code = None
    self.http_version = None
    self.process_duration = None
    self.remote_name = None
    self.thread_name = None
    self.user_name = None


class ConfluenceAccessParser(text_parser.PyparsingSingleLineTextParser):
  """Confluence access log (conf_access_log[DATE].log) file parser."""

  NAME = 'confluence_access'
  DATA_FORMAT = 'Confluence access log (access.log) file'

  MAX_LINE_LENGTH = 2048

  # Default pattern is %t %{X-AUSERNAME}o %I %h %r %s %Dms %b %{Referer}i %{
  # User-Agent}i

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

  _RESPONSE_BYTES = (
      pyparsing.Literal('-') |
      text_parser.PyparsingConstants.INTEGER).setResultsName('response_bytes')

  _REFERER = (
      pyparsing.Word(pyparsing.alphanums + "/-_.?=%&:+<>#~[]").setResultsName(
          'referer'))

  _THREAD_NAME = (
      pyparsing.Word(pyparsing.alphanums + '-').setResultsName('thread_name')
  )

  _USER_AGENT = pyparsing.restOfLine.setResultsName('user_agent')

  _USER_NAME = (
      pyparsing.Word(pyparsing.alphanums + '@' + pyparsing.alphanums + '.') |
      pyparsing.Word(pyparsing.alphanums) |
      pyparsing.Literal('-')).setResultsName('user_name')

  _HTTP_METHOD = (
      pyparsing.oneOf(
          ['CONNECT', 'DELETE', 'GET', 'HEAD', 'OPTIONS', 'PATCH', 'POST',
              'PUT', 'TRACE'])).setResultsName('http_method')

  _REMOTE_NAME = (
      (text_parser.PyparsingConstants.IP_ADDRESS | pyparsing.Word(
          pyparsing.alphanums + '-' + '.')).setResultsName('remote_name'))

  _HTTP_VERSION = (
      pyparsing.Word(pyparsing.alphanums + "/.").setResultsName('http_version'))

  _REQUEST_URI = (
      pyparsing.Word(pyparsing.alphanums + "/-_.?=%&:+<>#~[]").setResultsName(
          'request_url'))

  # Defined in
  # https://confluence.atlassian.com/confkb/audit-confluence-using-the-tomcat-valve-component-223216846.html
  # format: "%t %{X-AUSERNAME}o %I %h %r %s %Dms %b %{Referer}i %{User-Agent}i"
  _PRE_711_FORMAT = (
      _DATE_TIME +
      _USER_NAME +
      _THREAD_NAME +
      _REMOTE_NAME +
      _HTTP_METHOD +
      _REQUEST_URI +
      _HTTP_VERSION +
      text_parser.PyparsingConstants.INTEGER.setResultsName('response_code') +
      text_parser.PyparsingConstants.INTEGER.setResultsName(
          'process_duration') +
      pyparsing.Literal('ms') +
      _RESPONSE_BYTES +
      _REFERER +
      _USER_AGENT
  )

  # Post 7.11
  # %t %{X-Forwarded-For}i %{X-AUSERNAME}o %I %h %r %s %Dms %b %{Referer}i %{
  # User-Agent}i
  # Post 7.11
  _POST_711_FORMAT = (
      _DATE_TIME +
      text_parser.PyparsingConstants.IP_ADDRESS.setResultsName(
          'forwarded_for') +
      _USER_NAME +
      _THREAD_NAME +
      _REMOTE_NAME +
      _HTTP_METHOD +
      _REQUEST_URI +
      _HTTP_VERSION +
      text_parser.PyparsingConstants.INTEGER.setResultsName('response_code') +
      text_parser.PyparsingConstants.INTEGER.setResultsName(
          'process_duration') +
      pyparsing.Literal('ms') +
      _RESPONSE_BYTES +
      _REFERER +
      _USER_AGENT
  )

  LINE_STRUCTURES = [
      ('pre_711_format', _PRE_711_FORMAT),
      ('post_711_format', _POST_711_FORMAT)
  ]

  _SUPPORTED_KEYS = frozenset([key for key, _ in LINE_STRUCTURES])

  def _GetDateTime(self, structure):
    """Retrieves the date and time from a date and time values structure.

    The date and time values in Confluence access log files are formatted as:
    "[18/Sep/2011:19:18:28 -0400]".

    Args:
      structure (pyparsing.ParseResults): structure of tokens derived from a
          line of a text file.

    Returns:
      dfdatetime.DateTimeValues: date and time.

    Raises:
      ValueError: if the structure cannot be converted into a date time string.
    """
    year = self._GetValueFromStructure(structure, 'year')
    month = self._GetValueFromStructure(structure, 'month')

    try:
      month = self._MONTH_DICT.get(month.lower(), 0)
    except AttributeError as exception:
      raise ValueError('unable to parse month with error: {0!s}.'.format(
          exception))

    day_of_month = self._GetValueFromStructure(structure, 'day')
    hours = self._GetValueFromStructure(structure, 'hours')
    minutes = self._GetValueFromStructure(structure, 'minutes')
    seconds = self._GetValueFromStructure(structure, 'seconds')
    time_offset = self._GetValueFromStructure(structure, 'time_offset')

    try:
      time_zone_offset = int(time_offset[1:3], 10) * 60
      time_zone_offset += int(time_offset[3:5], 10)
      if time_offset[0] == '-':
        time_zone_offset *= -1

    except (TypeError, ValueError) as exception:
      raise ValueError(
          'unable to parse time zone offset with error: {0!s}.'.format(
              exception))

    time_elements_tuple = (year, month, day_of_month, hours, minutes, seconds)

    return dfdatetime_time_elements.TimeElements(
        time_elements_tuple=time_elements_tuple,
        time_zone_offset=time_zone_offset)

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

    date_time_string = self._GetValueFromStructure(structure, 'date_time')

    try:
      date_time = self._GetDateTime(date_time_string)
    except ValueError as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to parse date time value: {0!s} with error: {1!s}'.format(
              date_time_string, exception))
      return

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_RECORDED)

    event_data = ConfluenceAccessEventData()
    if key == 'post_711_format':
      event_data.forwarded_for = self._GetValueFromStructure(
          structure, 'forwarded_for')

    event_data.remote_name = self._GetValueFromStructure(
        structure, 'remote_name')
    event_data.user_name = self._GetValueFromStructure(
        structure, 'user_name')
    event_data.thread_name = self._GetValueFromStructure(
        structure, 'thread_name')
    event_data.http_request_method = self._GetValueFromStructure(
        structure, 'http_method')
    event_data.http_request_uri = self._GetValueFromStructure(
        structure, 'request_url')
    event_data.http_response_code = self._GetValueFromStructure(
        structure, 'response_code')
    event_data.process_duration = self._GetValueFromStructure(
        structure, 'process_duration')
    event_data.http_response_bytes = self._GetValueFromStructure(
        structure, 'response_bytes')
    event_data.http_request_referer = self._GetValueFromStructure(
        structure, 'referer')
    event_data.http_request_user_agent = self._GetValueFromStructure(
        structure,'user_agent')
    if event_data.http_request_user_agent:
      user_agent = event_data.http_request_user_agent.strip()
      event_data.http_request_user_agent = user_agent

    event_data.http_version = self._GetValueFromStructure(
        structure, 'http_version')

    parser_mediator.ProduceEventWithEventData(event, event_data)

  # pylint: disable=unused-argument
  def VerifyStructure(self, parser_mediator, line):
    """Verifies that this is a confluence access log file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
        and other components, such as storage and dfvfs.
      line (str): line from the text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    return max([parser.matches(line) for _, parser in self.LINE_STRUCTURES])


manager.ParsersManager.RegisterParser(ConfluenceAccessParser)
