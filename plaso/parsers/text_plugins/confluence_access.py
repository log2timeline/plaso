# -*- coding: utf-8 -*-
"""Text plugin for Confluence access log (conf_access_log[DATE].log) files.

Also see:
  https://confluence.atlassian.com/doc/configure-access-logs-1044780567.html
  https://confluence.atlassian.com/confkb/audit-confluence-using-the-tomcat-valve-component-223216846.html
"""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


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
    recorded_time (dfdatetime.DateTimeValues): date and time the log entry
        was recorded.
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
    self.recorded_time = None
    self.remote_name = None
    self.thread_name = None
    self.user_name = None


class ConfluenceAccessTextPlugin(interface.TextPlugin):
  """Text plugin for Confluence access log (conf_access_log[DATE].log) files."""

  NAME = 'confluence_access'
  DATA_FORMAT = 'Confluence access log (access.log) file'

  _INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _THREE_LETTERS = pyparsing.Word(pyparsing.alphas, exact=3)

  _MONTH_DICT = {
      'jan': 1,
      'feb': 2,
      'mar': 3,
      'apr': 4,
      'may': 5,
      'jun': 6,
      'jul': 7,
      'aug': 8,
      'sep': 9,
      'oct': 10,
      'nov': 11,
      'dec': 12}

  _TIME_ZONE_OFFSET = (
      pyparsing.Word('+-', exact=1) + _TWO_DIGITS + _TWO_DIGITS)

  # Date and time values are formatted as: [18/Sep/2011:19:18:28 -0400]
  _DATE_TIME = pyparsing.Group(
      pyparsing.Suppress('[') + _TWO_DIGITS +
      pyparsing.Suppress('/') + _THREE_LETTERS +
      pyparsing.Suppress('/') + _FOUR_DIGITS +
      pyparsing.Suppress(':') + _TWO_DIGITS +
      pyparsing.Suppress(':') + _TWO_DIGITS +
      pyparsing.Suppress(':') + _TWO_DIGITS +
      _TIME_ZONE_OFFSET + pyparsing.Suppress(']')).setResultsName('date_time')

  _IP_ADDRESS = (
      pyparsing.pyparsing_common.ipv4_address |
      pyparsing.pyparsing_common.ipv6_address)

  _RESPONSE_BYTES = (
      pyparsing.Literal('-') | _INTEGER).setResultsName('response_bytes')

  _REFERER = pyparsing.Word(pyparsing.alphanums + '/-_.?=%&:+<>#~[]')

  _THREAD_NAME = (
      pyparsing.Word(pyparsing.alphanums + '-').setResultsName('thread_name'))

  _USER_AGENT = pyparsing.restOfLine().setResultsName('user_agent')

  _USER_NAME = (
      pyparsing.Word(pyparsing.alphanums + '@' + pyparsing.alphanums + '.') |
      pyparsing.Word(pyparsing.alphanums) |
      pyparsing.Literal('-')).setResultsName('user_name')

  _HTTP_METHOD = pyparsing.oneOf([
      'CONNECT', 'DELETE', 'GET', 'HEAD', 'OPTIONS', 'PATCH', 'POST', 'PUT',
      'TRACE'])

  _REMOTE_NAME = (
      _IP_ADDRESS |
      pyparsing.Word(pyparsing.alphanums + '-' + '.')).setResultsName(
          'remote_name')

  _HTTP_VERSION = (
      pyparsing.Word(pyparsing.alphanums + '/.').setResultsName('http_version'))

  _REQUEST_URI = pyparsing.Word(pyparsing.alphanums + '/-_.?=%&:+<>#~[]')

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  # Default (pre 7.11) format log line:
  # %t %{X-AUSERNAME}o %I %h %r %s %Dms %b %{Referer}i %{User-Agent}i

  _PRE_711_FORMAT_LOG_LINE = (
      _DATE_TIME +
      _USER_NAME +
      _THREAD_NAME +
      _REMOTE_NAME +
      _HTTP_METHOD.setResultsName('http_method') +
      _REQUEST_URI.setResultsName('request_url') +
      _HTTP_VERSION +
      _INTEGER.setResultsName('response_code') +
      _INTEGER.setResultsName('process_duration') +
      pyparsing.Literal('ms') +
      _RESPONSE_BYTES +
      _REFERER.setResultsName('referer') +
      _USER_AGENT +
      _END_OF_LINE)

  # Post 7.11 format log line:
  # %t %{X-Forwarded-For}i %{X-AUSERNAME}o %I %h %r %s %Dms %b %{Referer}i
  # %{User-Agent}i

  _POST_711_FORMAT_LOG_LINE = (
      _DATE_TIME +
      _IP_ADDRESS.setResultsName('forwarded_for') +
      _USER_NAME +
      _THREAD_NAME +
      _REMOTE_NAME +
      _HTTP_METHOD.setResultsName('http_method') +
      _REQUEST_URI.setResultsName('request_url') +
      _HTTP_VERSION +
      _INTEGER.setResultsName('response_code') +
      _INTEGER.setResultsName('process_duration') +
      pyparsing.Literal('ms') +
      _RESPONSE_BYTES +
      _REFERER.setResultsName('referer') +
      _USER_AGENT +
      _END_OF_LINE)

  _LINE_STRUCTURES = [
      ('pre_711_format', _PRE_711_FORMAT_LOG_LINE),
      ('post_711_format', _POST_711_FORMAT_LOG_LINE)]

  VERIFICATION_GRAMMAR = _PRE_711_FORMAT_LOG_LINE ^ _POST_711_FORMAT_LOG_LINE

  VERIFICATION_LITERALS = [
      ' CONNECT ', ' DELETE ', ' GET ', ' HEAD ', ' HTTP/', ' OPTIONS ',
      ' PATCH ', ' POST ', ' PUT ', ' TRACE ']

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
    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    event_data = ConfluenceAccessEventData()
    event_data.http_request_method = self._GetValueFromStructure(
        structure, 'http_method')
    event_data.http_request_referer = self._GetValueFromStructure(
        structure, 'referer')
    event_data.http_request_uri = self._GetValueFromStructure(
        structure, 'request_url')
    event_data.http_request_user_agent = self._GetStringValueFromStructure(
        structure, 'user_agent')
    event_data.http_response_code = self._GetValueFromStructure(
        structure, 'response_code')
    event_data.http_response_bytes = self._GetValueFromStructure(
        structure, 'response_bytes')
    event_data.http_version = self._GetValueFromStructure(
        structure, 'http_version')
    event_data.process_duration = self._GetValueFromStructure(
        structure, 'process_duration')
    event_data.recorded_time = self._ParseTimeElements(time_elements_structure)
    event_data.remote_name = self._GetValueFromStructure(
        structure, 'remote_name')
    event_data.thread_name = self._GetValueFromStructure(
        structure, 'thread_name')
    event_data.user_name = self._GetValueFromStructure(
        structure, 'user_name')

    if key == 'post_711_format':
      event_data.forwarded_for = self._GetValueFromStructure(
          structure, 'forwarded_for')

    parser_mediator.ProduceEventData(event_data)

  def _ParseTimeElements(self, time_elements_structure):
    """Parses date and time elements of a log line.

    Args:
      time_elements_structure (pyparsing.ParseResults): date and time elements
          of a log line.

    Returns:
      dfdatetime.TimeElements: date and time value.

    Raises:
      ParseError: if a valid date and time value cannot be derived from
          the time elements.
    """
    try:
      (day_of_month, month_string, year, hours, minutes, seconds,
       time_zone_sign, time_zone_hours, time_zone_minutes) = (
          time_elements_structure)

      month = self._MONTH_DICT.get(month_string.lower(), 0)

      time_zone_offset = (time_zone_hours * 60) + time_zone_minutes
      if time_zone_sign == '-':
        time_zone_offset *= -1

      time_elements_tuple = (year, month, day_of_month, hours, minutes, seconds)

      return dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple,
          time_zone_offset=time_zone_offset)

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse time elements with error: {0!s}'.format(exception))

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
      structure = self._VerifyString(text_reader.lines)
    except errors.ParseError:
      return False

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    try:
      self._ParseTimeElements(time_elements_structure)
    except errors.ParseError:
      return False

    return True


text_parser.TextLogParser.RegisterPlugin(ConfluenceAccessTextPlugin)
