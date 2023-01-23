# -*- coding: utf-8 -*-
"""Text parser plugin for Anydesk Ad Trace log (ad.trace) files.

Parser based on the xxxxx
"""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface
from plaso.multi_process import logger

class AnyDeskAdTraceLogEventData(events.EventData):
  """AnyDesk Ad Trace log event data.

  Attributes:
    http_request_referer (str): http request referer header information.
    http_request (str): first line of http request.
    http_request_user_agent (str): http request user agent header information.
    http_response_bytes (int): http response bytes size without headers.
    http_response_code (int): http response code from server.
    ip_address (str): IPv4 or IPv6 addresses.
    port_number (int): canonical port of the server serving the request.
    recorded_time (dfdatetime.DateTimeValues): date and time the log entry
        was recorded.
    remote_name (str): remote logname (from identd, if supplied).
    server_name (str): canonical hostname of the server serving the request.
    user_name (str): logged user name.
  """

  DATA_TYPE = 'anydesk:adtrace_log:entry'

  def __init__(self):
    """Initializes event data."""
    super(AnyDeskAdTraceLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.loglevel = None
    self.recorded_time = None
    self.appname = None
    self.pid = None
    self.threadid = None
    self.function = None
    self.message = None

class AnyDeskAdTraceLogTextPlugin(interface.TextPlugin):
  """Text parser plugin for AnyDesk Ad Trace log (ad.trace) files."""

  NAME = 'anydesk_adtrace'
  DATA_FORMAT = 'AnyDesk Ad Trace log (ad.trace) file'
  ENCODING = 'utf-8'

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _THREE_DIGITS = pyparsing.Word(pyparsing.nums, exact=3).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _LOGLEVEL = pyparsing.Word(pyparsing.alphas).setResultsName('loglevel')

  # Date and time values are formatted as: 2022-12-29 13:34:22.945
  _DATE_TIME = pyparsing.Group(
      _FOUR_DIGITS +
      pyparsing.Suppress('-') + _TWO_DIGITS +
      pyparsing.Suppress('-') + _TWO_DIGITS +
      _TWO_DIGITS +
      pyparsing.Suppress(':') + _TWO_DIGITS +
      pyparsing.Suppress(':') + _TWO_DIGITS +
      pyparsing.Suppress('.') + _THREE_DIGITS).setResultsName('date_time')

  _APPNAME = pyparsing.Word(pyparsing.alphas).setResultsName('appname')

  _INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FUNCTION_MESSAGE = (
    pyparsing.Word(pyparsing.alphanums + '.' + '_').setResultsName('function') +
    pyparsing.Suppress("-") +
    pyparsing.restOfLine().setResultsName('message')
  )

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _BASIC_LOG_FORMAT_LINE = ( 
    _LOGLEVEL +
    _DATE_TIME +
    _APPNAME +
    _INTEGER.setResultsName('pid') +
    _INTEGER.setResultsName('threadid') +
    _FUNCTION_MESSAGE + 
    _END_OF_LINE
  )

  _SEPARATOR_LINE = pyparsing.Literal("* * * * * * * * * * * * * * * * * *")

  _LINE_STRUCTURES = [
      ('basic_log_format', _BASIC_LOG_FORMAT_LINE),
      ('_separator_line',_SEPARATOR_LINE)
    ]

  VERIFICATION_GRAMMAR = pyparsing.ZeroOrMore(_END_OF_LINE) + _BASIC_LOG_FORMAT_LINE

  VERIFICATION_LITERALS = None

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

    event_data = AnyDeskAdTraceLogEventData()

    loglevel = self._GetValueFromStructure(structure, 'loglevel')

    if not loglevel in ('info', 'warning', 'error'):
      return

    event_data.loglevel = loglevel
    event_data.recorded_time = self._ParseTimeElements(time_elements_structure)
    event_data.appname = self._GetValueFromStructure(structure, 'appname')
    event_data.pid = self._GetValueFromStructure(structure, 'pid')
    event_data.threadid = self._GetValueFromStructure(structure, 'pid')
    event_data.function = self._GetValueFromStructure(structure, 'function')
    event_data.message = self._GetValueFromStructure(structure, 'message')

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
      (year, month, day, hours, minutes, seconds, millisec) = (
          time_elements_structure)

      time_elements_tuple = (year, month, day, hours, minutes, seconds, millisec)
      return dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)

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
    except errors.ParseError as e:
      return False

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    try:
      self._ParseTimeElements(time_elements_structure)
    except errors.ParseError:
      return False
    return True


text_parser.TextLogParser.RegisterPlugin(AnyDeskAdTraceLogTextPlugin)
