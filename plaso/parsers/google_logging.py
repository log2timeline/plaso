# -*- coding: utf-8 -*-
"""Parser for Google-formatted log files."""

import re

from dfdatetime import time_elements as dfdatetime_time_elements

import pyparsing

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.lib import yearless_helper
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


class GoogleLogParser(
    text_parser.PyparsingMultiLineTextParser,
    yearless_helper.YearLessLogFormatHelper):
  """Parser for Google-formatted log files."""

  NAME = 'googlelog'
  DATA_FORMAT = 'Google-formatted log file'

  BUFFER_SIZE = 5120

  _ONE_OR_TWO_DIGITS = pyparsing.Word(pyparsing.nums, max=2).setParseAction(
      text_parser.PyParseIntCast)

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      text_parser.PyParseIntCast)

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      text_parser.PyParseIntCast)

  _SIX_DIGITS = pyparsing.Word(pyparsing.nums, exact=6).setParseAction(
      text_parser.PyParseIntCast)

  _DATE_TIME = (
      _TWO_DIGITS.setResultsName('month') +
      _ONE_OR_TWO_DIGITS.setResultsName('day_of_month') +
      _TWO_DIGITS.setResultsName('hours') + pyparsing.Suppress(':') +
      _TWO_DIGITS.setResultsName('minutes') + pyparsing.Suppress(':') +
      _TWO_DIGITS.setResultsName('seconds') + pyparsing.Optional(
          pyparsing.Suppress('.') + _SIX_DIGITS.setResultsName('microseconds')))

  _LOG_LINE = (
      pyparsing.oneOf(['I', 'W', 'E', 'F']).setResultsName('priority') +
      _DATE_TIME +
      pyparsing.Word(pyparsing.nums).setResultsName('thread_identifier') +
      pyparsing.Word(pyparsing.printables.replace(':', '')).setResultsName(
          'file_name') + pyparsing.Suppress(':') +
      pyparsing.Word(pyparsing.nums).setResultsName('line_number') +
      pyparsing.Suppress('] ') +
      pyparsing.Regex('.*?(?=($|\n[IWEF][0-9]{4}))', re.DOTALL).setResultsName(
          'message') + pyparsing.lineEnd())

  _GREETING = (
      _FOUR_DIGITS.setResultsName('year') + pyparsing.Suppress('/') +
      _TWO_DIGITS.setResultsName('month') + pyparsing.Suppress('/') +
      _ONE_OR_TWO_DIGITS.setResultsName('day_of_month') +
      _TWO_DIGITS.setResultsName('hours') + pyparsing.Suppress(':') +
      _TWO_DIGITS.setResultsName('minutes') + pyparsing.Suppress(':') +
      _TWO_DIGITS.setResultsName('seconds') +
      pyparsing.Regex('.*?(?=($|\n[IWEF][0-9]{4}))', re.DOTALL) +
      pyparsing.lineEnd())

  _GREETING_START = 'Log file created at: '

  # Order is important here, as the structures are checked against each line
  # sequentially, so we put the most common first, and the most expensive
  # last.
  LINE_STRUCTURES = [
      ('log_entry', _LOG_LINE),
      ('greeting_start', pyparsing.Literal(_GREETING_START)),
      ('greeting', _GREETING)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in LINE_STRUCTURES])

  def _GetTimeElementsTuple(self, structure):
    """Retrieves a time elements tuple from the structure.

    Args:
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.

    Returns:
      tuple: containing:
        year (int): year.
        month (int): month, where 1 represents January.
        day_of_month (int): day of month, where 1 is the first day of the month.
        hours (int): hours.
        minutes (int): minutes.
        seconds (int): seconds.

    Raises:
      ValueError: if month contains an unsupported value.
    """
    month = self._GetValueFromStructure(structure, 'month')
    day_of_month = self._GetValueFromStructure(structure, 'day_of_month')
    hours = self._GetValueFromStructure(structure, 'hours')
    minutes = self._GetValueFromStructure(structure, 'minutes')
    seconds = self._GetValueFromStructure(structure, 'seconds')
    microseconds = self._GetValueFromStructure(structure, 'microseconds')

    self._UpdateYear(month)

    year = self._GetYear()

    return year, month, day_of_month, hours, minutes, seconds, microseconds

  def _ParseGreeting(self, parser_mediator, structure):
    """Extract useful information from the logfile greeting.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      structure (pyparsing.ParseResults): elements parsed from the file.
    """
    year = self._GetValueFromStructure(structure, 'year')
    month = self._GetValueFromStructure(structure, 'month')

    try:
      self._SetMonthAndYear(month, year)
    except (TypeError, ValueError):
      parser_mediator.ProduceExtractionWarning(
          'invalid greeting date time value.')

  def _ParseLine(self, parser_mediator, structure):
    """Process a single log line into a GoogleLogEvent.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      structure (pyparsing.ParseResults): elements parsed from the file.
    """
    try:
      time_elements_tuple = self._GetTimeElementsTuple(structure)
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds(
          time_elements_tuple=time_elements_tuple)
      date_time.is_local_time = True
    except (TypeError, ValueError):
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
          and other components, such as storage and dfVFS.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): elements parsed from the file.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in self._SUPPORTED_KEYS:
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    if key == 'greeting':
      self._ParseGreeting(parser_mediator, structure)

    elif key == 'log_entry':
      self._ParseLine(parser_mediator, structure)

  def VerifyStructure(self, parser_mediator, lines):
    """Verifies that this is a google log-formatted file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between
          parsers and other components, such as storage and dfVFS.
      lines (str): one or more lines from the text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    if not lines.startswith(self._GREETING_START):
      return False

    self._SetEstimatedYear(parser_mediator)

    return True


manager.ParsersManager.RegisterParser(GoogleLogParser)
