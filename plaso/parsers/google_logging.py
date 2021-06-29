# -*- coding: utf-8 -*-
"""Parser for Google-formatted log files."""

import re

from dfdatetime import time_elements as dfdatetime_time_elements

import pyparsing

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import manager
from plaso.parsers import text_parser


class GoogleLogEventData(events.EventData):
  """Google-formatted log file event data.

  See: https://github.com/google/glog. This format is also used by
  Kubernetes, see https://github.com/kubernetes/klog

  Attributes:
    file_name (str): the name of the source file that logged the message.
    line_number (int): the line number in the source file where the logging
        statement is.
    message (str): the log message.
    priority (str): the priority of the message - I, W, E or F. These values
        represent messages logged at INFO, WARNING, ERROR or FATAL severities,
        respectively.
    thread_identifier (int): the identifier of the thread that recorded the
        message.
  """

  DATA_TYPE = 'googlelog:log'

  def __init__(self, data_type=DATA_TYPE):
    """Initializes event data.

    Args:
      data_type (Optional[str]): event data type indicator.
    """
    super(GoogleLogEventData, self).__init__(data_type=data_type)
    self.file_name = None
    self.line_number = None
    self.message = None
    self.priority = None
    self.thread_identifier = None


class GoogleLogParser(text_parser.PyparsingMultiLineTextParser):
  """Parser for Google-formatted log files."""

  NAME = 'googlelog'
  DATA_FORMAT = 'Google-formatted log file'

  # PyParsing components used to construct grammars for parsing lines.
  _PYPARSING_COMPONENTS = {
      'priority': (
          pyparsing.oneOf(['I', 'W', 'E', 'F']).setResultsName('priority')),
      'year': text_parser.PyparsingConstants.FOUR_DIGITS.setResultsName(
          'year'),
      'month_number': text_parser.PyparsingConstants.TWO_DIGITS.setResultsName(
          'month_number'),
      'day': text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName(
          'day'),
      'hour': text_parser.PyparsingConstants.TWO_DIGITS.setResultsName(
          'hour'),
      'minute': text_parser.PyparsingConstants.TWO_DIGITS.setResultsName(
          'minute'),
      'second': text_parser.PyparsingConstants.TWO_DIGITS.setResultsName(
          'second'),
      'microsecond': pyparsing.Word(pyparsing.nums, exact=6).setParseAction(
          text_parser.PyParseIntCast).setResultsName('microsecond'),
      'thread_identifier': pyparsing.Word(pyparsing.nums).setResultsName(
          'thread_identifier'),
      'file_name':
          (pyparsing.Word(pyparsing.printables.replace(':', '')).setResultsName(
              'file_name')),
      'line_number': (
          pyparsing.Word(pyparsing.nums).setResultsName('line_number')),
      'message': (
          pyparsing.Regex('.*?(?=($|\n[IWEF][0-9]{4}))', re.DOTALL).
          setResultsName('message'))}

  _PYPARSING_COMPONENTS['date'] = (
      _PYPARSING_COMPONENTS['month_number'] +
      _PYPARSING_COMPONENTS['day'] +
      _PYPARSING_COMPONENTS['hour'] + pyparsing.Suppress(':') +
      _PYPARSING_COMPONENTS['minute'] + pyparsing.Suppress(':') +
      _PYPARSING_COMPONENTS['second'] + pyparsing.Optional(
          pyparsing.Suppress('.') +
          _PYPARSING_COMPONENTS['microsecond']))

  # Grammar for individual log event lines.
  _LOG_LINE = (
      _PYPARSING_COMPONENTS['priority'] + _PYPARSING_COMPONENTS['date'] +
      _PYPARSING_COMPONENTS['thread_identifier'] +
      _PYPARSING_COMPONENTS['file_name'] + pyparsing.Suppress(':') +
      _PYPARSING_COMPONENTS['line_number'] + pyparsing.Suppress('] ') +
      _PYPARSING_COMPONENTS['message'] + pyparsing.lineEnd())

  # Grammar for the log file greeting.
  _GREETING = (
      _PYPARSING_COMPONENTS['year'] + pyparsing.Suppress('/') +
      _PYPARSING_COMPONENTS['month_number'] + pyparsing.Suppress('/') +
      _PYPARSING_COMPONENTS['day'] + _PYPARSING_COMPONENTS['hour'] +
      pyparsing.Suppress(':') + _PYPARSING_COMPONENTS['minute'] +
      pyparsing.Suppress(':') + _PYPARSING_COMPONENTS['second'] +
      pyparsing.Regex('.*?(?=($|\n[IWEF][0-9]{4}))', re.DOTALL) +
      pyparsing.lineEnd())

  _GREETING_START = 'Log file created at: '

  # Our initial buffer length is the length of the string we verify with.
  _INITIAL_BUFFER_SIZE = len(_GREETING_START)

  # Once we're sure we're reading a valid file, we'll use a larger read buffer.
  _RUNNING_BUFFER_SIZE = 5120

  # Order is important here, as the structures are checked against each line
  # sequentially, so we put the most common first, and the most expensive
  # last.
  LINE_STRUCTURES = [
      ('log_entry', _LOG_LINE),
      ('greeting_start', pyparsing.Literal(_GREETING_START)),
      ('greeting', _GREETING)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in LINE_STRUCTURES])

  def __init__(self):
    """Initializes a Google log formatted file parser."""
    super(GoogleLogParser, self).__init__()

    # Set the size of the file we need to read to verify it.
    self._buffer_size = self._INITIAL_BUFFER_SIZE
    self._maximum_year = 0
    # The year to use for events. The initial year is stored in the log file
    # greeting.
    self._year = 0
    # The month the last observed event occurred.
    self._last_month = 0

  def _UpdateYear(self, mediator, month):
    """Updates the year to use for events, based on last observed month.

    Args:
      mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      month (int): month observed by the parser, where January is 1.
    """
    if not self._year:
      self._year = mediator.GetEstimatedYear()
    if not self._maximum_year:
      self._maximum_year = mediator.GetLatestYear()

    if not self._last_month:
      self._last_month = month
      return

    # TODO: Check whether out of order events are possible
    if self._last_month > (month + 1):
      if self._year != self._maximum_year:
        self._year += 1
    self._last_month = month

  def _ReadGreeting(self, structure):
    """Extract useful information from the logfile greeting.

    Args:
      structure (pyparsing.ParseResults): elements parsed from the file.
    """
    self._year = self._GetValueFromStructure(structure, 'year')
    self._last_month = self._GetValueFromStructure(structure, 'month_number')

  def _ParseLine(self, parser_mediator, structure):
    """Process a single log line into a GoogleLogEvent.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      structure (pyparsing.ParseResults): elements parsed from the file.
    """
    month = self._GetValueFromStructure(structure, 'month_number')

    if month != 0:
      self._UpdateYear(parser_mediator, month)

    day = self._GetValueFromStructure(structure, 'day')
    hours = self._GetValueFromStructure(structure, 'hour')
    minutes = self._GetValueFromStructure(structure, 'minute')
    seconds = self._GetValueFromStructure(structure, 'second')
    microseconds = self._GetValueFromStructure(structure, 'microsecond')

    time_elements_tuple = (
        self._year, month, day, hours, minutes, seconds, microseconds)

    try:
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds(
          time_elements_tuple=time_elements_tuple)
      date_time.is_local_time = True
    except ValueError:
      parser_mediator.ProduceExtractionWarning(
          'invalid date time value: {0!s}'.format(time_elements_tuple))
      return

    event_data = GoogleLogEventData()
    event_data.priority = self._GetValueFromStructure(structure, 'priority')
    event_data.thread_identifier = self._GetValueFromStructure(
        structure, 'thread_identifier')
    event_data.file_name = self._GetValueFromStructure(structure, 'file_name')
    event_data.line_number = self._GetValueFromStructure(
        structure, 'line_number')
    event_data.message = self._GetValueFromStructure(structure, 'message')

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)

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

    if key == 'greeting':
      self._ReadGreeting(structure)

    elif key == 'log_entry':
      self._ParseLine(parser_mediator, structure)

  def VerifyStructure(self, parser_mediator, lines):
    """Verifies that this is a google log-formatted file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between
          parsers and other components, such as storage and dfvfs.
      lines (str): one or more lines from the text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    if not lines.startswith(self._GREETING_START):
      return False

    # Now that we know this is a valid log, expand the read buffer to the
    # maximum size we expect a log event to be (which is quite large).
    self._buffer_size = self._RUNNING_BUFFER_SIZE
    self._year = parser_mediator.year
    return True


manager.ParsersManager.RegisterParser(GoogleLogParser)
