# -*- coding: utf-8 -*-
"""Parser for Google-formatted log files.

Note that this format is also used by Kubernetes.

Also see:
  https://github.com/google/glog
  https://github.com/kubernetes/klog
"""

import re

from dfdatetime import time_elements as dfdatetime_time_elements

import pyparsing

from plaso.containers import events
from plaso.lib import errors
from plaso.lib import yearless_helper
from plaso.parsers import manager
from plaso.parsers import text_parser


class GoogleLogEventData(events.EventData):
  """Google-formatted log file event data.

  Attributes:
    file_name (str): the name of the source file that logged the message.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
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
    self.last_written_time = None
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
      _TWO_DIGITS + _ONE_OR_TWO_DIGITS +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Optional(
          pyparsing.Suppress('.') + _SIX_DIGITS)).setResultsName('date_time')

  _PRIORITY = pyparsing.oneOf(['E', 'F', 'I', 'W']).setResultsName('priority')

  _LOG_LINE = (
      _PRIORITY + _DATE_TIME +
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
  _LINE_STRUCTURES = [
      ('log_entry', _LOG_LINE),
      ('greeting_start', pyparsing.Literal(_GREETING_START)),
      ('greeting', _GREETING)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in _LINE_STRUCTURES])

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
    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    event_data = GoogleLogEventData()
    event_data.file_name = self._GetValueFromStructure(structure, 'file_name')
    event_data.last_written_time = self._ParseTimeElements(
        time_elements_structure)
    event_data.line_number = self._GetValueFromStructure(
        structure, 'line_number')
    event_data.message = self._GetValueFromStructure(structure, 'message')
    event_data.priority = self._GetValueFromStructure(structure, 'priority')
    event_data.thread_identifier = self._GetValueFromStructure(
        structure, 'thread_identifier')

    parser_mediator.ProduceEventData(event_data)

  def _ParseRecord(self, parser_mediator, key, structure):
    """Parses a pyparsing structure.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): tokens from a parsed log line.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in self._SUPPORTED_KEYS:
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    if key == 'greeting':
      self._ParseGreeting(parser_mediator, structure)

    elif key == 'log_entry':
      try:
        self._ParseLine(parser_mediator, structure)
      except errors.ParseError as exception:
        parser_mediator.ProduceExtractionWarning(
            'unable to parse log line with error: {0!s}'.format(exception))

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
      month, day_of_month, hours, minutes, seconds, microseconds = (
          time_elements_structure)

      self._UpdateYear(month)

      relative_year = self._GetRelativeYear()

      time_elements_tuple = (
          relative_year, month, day_of_month, hours, minutes, seconds,
          microseconds)

      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds(
          is_delta=True, time_elements_tuple=time_elements_tuple)

      date_time.is_local_time = True

      return date_time

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse time elements with error: {0!s}'.format(exception))

  def CheckRequiredFormat(self, parser_mediator, text_reader):
    """Check if the log record has the minimal structure required by the parser.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    if not text_reader.lines.startswith(self._GREETING_START):
      return False

    self._SetEstimatedYear(parser_mediator)

    return True


manager.ParsersManager.RegisterParser(GoogleLogParser)
