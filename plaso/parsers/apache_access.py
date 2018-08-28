# -*- coding: utf-8 -*-
"""Apache access log (access.log) parser."""

from __future__ import unicode_literals

import re
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
    TODO: fill
    ip_address :
    remote_name :
    user_name :
    http_request :
    http_response_code :
    http_response_bytes :
    http_request_referer :
    http_request_user_agent :
  """

  DATA_TYPE = 'apache:access'

  def __init__(self):
    """Initializes event data."""
    super(ApacheAccessEventData, self).__init__(data_type=self.DATA_TYPE)
    self.ip_address = None
    self.remote_name = None
    self.user_name = None
    self.http_request  = None
    self.http_response_code = None
    self.http_response_bytes = None
    self.http_request_referer = None
    self.http_request_user_agent = None


class ApacheAccessParser(text_parser.PyparsingSingleLineTextParser):
  """Apache access log file parser"""

  NAME = 'apache_access'
  DESCRIPTION = 'Apache access Parser'

  _VERIFICATION_REGEX = re.compile('TODO: apache format')

  _PYPARSING_COMPONENTS = {
      'ip': text_parser.PyparsingConstants.IP_ADDRESS.setResultsName(
          'ip_address'),
      'remote_name': (pyparsing.Word(pyparsing.alphanums) | pyparsing.Literal('-')),
      'user_name': (pyparsing.Word(pyparsing.alphanums) | pyparsing.Literal('-')),
      'http_request': pyparsing.SkipTo('"').setResultsName('http_request'),
      'response_code': text_parser.PyparsingConstants.INTEGER.setResultsName(
          'response_code'),
      'response_bytes':  text_parser.PyparsingConstants.INTEGER.setResultsName(
          'response_bytes'),
      'referer': pyparsing.SkipTo('"').setResultsName('user_agent'),
      'user_agent': pyparsing.SkipTo('"').setResultsName('user_agent')
  }

  # date = [18/Sep/2011:19:18:28 -0400]
  _PYPARSING_COMPONENTS['date'] = (
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
      (pyparsing.oneOf(['-', '+']) + pyparsing.Word(pyparsing.nums, exact=4)).setResultsName('timezone') +
      pyparsing.Suppress(']')
  )
  _SKIP_SEP = pyparsing.Suppress('"')

  # Defined in https://httpd.apache.org/docs/2.4/logs.html
  # format: "%h %l %u %t \"%r\" %>s %b"
  _COMMON_LOG_FORMAT_LINE = (
      _PYPARSING_COMPONENTS['ip'] +
      _PYPARSING_COMPONENTS['remote_name'].setResultsName('remote_name')+
      _PYPARSING_COMPONENTS['user_name'].setResultsName('user_name') +
      _PYPARSING_COMPONENTS['date'] +
      _SKIP_SEP + _PYPARSING_COMPONENTS['http_request'] + _SKIP_SEP +
      _PYPARSING_COMPONENTS['response_code'] +
      _PYPARSING_COMPONENTS['response_bytes']
  )

  # Defined in https://httpd.apache.org/docs/2.4/logs.html
  # format: "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-agent}i\""
  _COMBINED_LOG_FORMAT_LINE = (
      _COMMON_LOG_FORMAT_LINE +
      _SKIP_SEP + _PYPARSING_COMPONENTS['referer'] + _SKIP_SEP +
      _SKIP_SEP + _PYPARSING_COMPONENTS['user_agent'] + _SKIP_SEP
  )

  LINE_STRUCTURES = [
      ('common_log_format', _COMMON_LOG_FORMAT_LINE),
      ('combined_log_format', _COMBINED_LOG_FORMAT_LINE)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in LINE_STRUCTURES])

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

    month = timelib.MONTH_DICT.get(structure.month.lower(), 0)

    time_elements_tuple = (
      structure.year, month, structure.day, structure.hours,
      structure.minutes, structure.seconds)
    # TODO add timezone offset

    try:
      date_time = dfdatetime_time_elements.TimeElements(
        time_elements_tuple=time_elements_tuple)
      date_time.is_local_time = True # TODO fix

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_ADDED)  # TODO fix

    except ValueError:
      parser_mediator.ProduceExtractionError(
        'invalid date time value: {0!s}'.format(time_elements_tuple))
      return

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
    """Verifies that this is a santa log file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      line (str): line from the text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    # TODO: should we add a file name checking this regexp is not bound to a
    # unique string.
    return True
    # return re.match(self._VERIFICATION_REGEX, line) is not None


manager.ParsersManager.RegisterParser(ApacheAccessParser)
