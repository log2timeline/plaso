# -*- coding: utf-8 -*-
"""Text parser plugin for Google-formatted log files.

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
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


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


class GoogleLogTextPlugin(
    interface.TextPlugin, yearless_helper.YearLessLogFormatHelper):
  """Text parser plugin for Google-formatted log files."""

  NAME = 'googlelog'
  DATA_FORMAT = 'Google-formatted log file'

  MAXIMUM_LINE_LENGTH = 5120

  _ONE_OR_TWO_DIGITS = pyparsing.Word(pyparsing.nums, max=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _SIX_DIGITS = pyparsing.Word(pyparsing.nums, exact=6).setParseAction(
      lambda tokens: int(tokens[0], 10))

  # Date and time values are formatted as: MMDD hh:mm:ss.######
  # For example: 1231 23:59:59.000001
  _DATE_TIME = (
      _TWO_DIGITS + _ONE_OR_TWO_DIGITS +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Optional(
          pyparsing.Suppress('.') + _SIX_DIGITS)).setResultsName('date_time')

  _PRIORITY = pyparsing.oneOf(['E', 'F', 'I', 'W']).setResultsName('priority')

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _LOG_LINE = (
      _PRIORITY + _DATE_TIME +
      pyparsing.Word(pyparsing.nums).setResultsName('thread_identifier') +
      pyparsing.Word(pyparsing.printables.replace(':', '')).setResultsName(
          'file_name') + pyparsing.Suppress(':') +
      pyparsing.Word(pyparsing.nums).setResultsName('line_number') +
      pyparsing.Suppress('] ') +
      pyparsing.Regex('.*?(?=($|\n[IWEF][0-9]{4}))', re.DOTALL).setResultsName(
          'message') + _END_OF_LINE)

  # Header date and time values are formatted as: 2019/07/18 06:07:40
  _HEADER_DATE_TIME = (
      _FOUR_DIGITS + pyparsing.Suppress('/') +
      _TWO_DIGITS + pyparsing.Suppress('/') + _ONE_OR_TWO_DIGITS +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') + _TWO_DIGITS)

  _HEADER_LINE = (
      pyparsing.Suppress('Log file created at:') +
      _HEADER_DATE_TIME.setResultsName('date_time') +
      pyparsing.Regex('.*?(?=($|\n[IWEF][0-9]{4}))', re.DOTALL) +
      _END_OF_LINE)

  _LINE_STRUCTURES = [
      ('header_line', _HEADER_LINE),
      ('log_line', _LOG_LINE)]

  VERIFICATION_GRAMMAR = _HEADER_LINE

  # TODO: change plugin to use _ParseHeader

  def _ParseHeaderLine(self, parser_mediator, structure):
    """Extract useful information from the header line.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      structure (pyparsing.ParseResults): elements parsed from the file.
    """
    # TODO: create log file event data with creation time.

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    year, month, _, _, _, _ = time_elements_structure

    try:
      self._SetMonthAndYear(month, year)
    except (TypeError, ValueError):
      parser_mediator.ProduceExtractionWarning(
          'invalid header date time value.')

  def _ParseHeaderTimeElements(self, time_elements_structure):
    """Parses date and time elements of a header line.

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
      year, month, day_of_month, hours, minutes, seconds = (
          time_elements_structure)

      time_elements_tuple = (year, month, day_of_month, hours, minutes, seconds)

      return dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse time elements with error: {0!s}'.format(exception))

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
      ParseError: if the structure cannot be parsed.
    """
    # TODO: parse log line format from header line.

    if key == 'header_line':
      self._ParseHeaderLine(parser_mediator, structure)

    elif key == 'log_line':
      self._ParseLine(parser_mediator, structure)

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
    try:
      structure, start, _ = self._VerifyString(text_reader.lines)
    except errors.ParseError:
      return False

    if start != 0:
      return False

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    try:
      self._ParseHeaderTimeElements(time_elements_structure)
    except errors.ParseError:
      return False

    self._SetEstimatedYear(parser_mediator)

    return True


text_parser.TextLogParser.RegisterPlugin(GoogleLogTextPlugin)
