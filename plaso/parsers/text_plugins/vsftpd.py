# -*- coding: utf-8 -*-
"""Text parser pluginf for vsftpd log files."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class VsftpdEventData(events.EventData):
  """vsftpd Log event data.

  Attributes:
    text (str): vsftpd log message.
  """

  DATA_TYPE = 'vsftpd:log'

  def __init__(self):
    """Initializes event data."""
    super(VsftpdEventData, self).__init__(data_type=self.DATA_TYPE)
    self.text = None


class VsftpdLogTextPlugin(interface.TextPlugin):
  """Text parser pluginf for vsftpd log files."""

  NAME = 'vsftpd'
  DATA_FORMAT = 'vsftpd log file'

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

  _DATETIME_ELEMENTS = (
      text_parser.PyparsingConstants.THREE_LETTERS.setResultsName('day') +
      text_parser.PyparsingConstants.THREE_LETTERS.setResultsName('month') +
      text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName(
          'day_of_month') +
      text_parser.PyparsingConstants.TWO_DIGITS.setResultsName('hours') +
      pyparsing.Suppress(':') +
      text_parser.PyparsingConstants.TWO_DIGITS.setResultsName('minutes') +
      pyparsing.Suppress(':') +
      text_parser.PyparsingConstants.TWO_DIGITS.setResultsName('seconds') +
      text_parser.PyparsingConstants.FOUR_DIGITS.setResultsName('year'))

  # Whitespace is suppressed by pyparsing.
  _DATE_TIME = pyparsing.Group(_DATETIME_ELEMENTS)

  _LOG_LINE = (
      _DATE_TIME.setResultsName('date_time') +
      pyparsing.SkipTo(pyparsing.lineEnd).setResultsName('text'))

  _LINE_STRUCTURES = [('logline', _LOG_LINE)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in _LINE_STRUCTURES])

  def _GetTimeElementsTuple(self, structure):
    """Retrieves a time elements tuple from the structure.

    Args:
        structure (pyparsing.ParseResults): structure of tokens derived from
            a line of a vsftp log file.

    Returns:
      tuple: containing:
        year (int): year.
        month (int): month, where 1 represents January.
        day_of_month (int): day of month, where 1 is the first day of the month.
        hours (int): hours.
        minutes (int): minutes.
        seconds (int): seconds.
    """
    time_elements_tuple = self._GetValueFromStructure(structure, 'date_time')
    _, month, day_of_month, hours, minutes, seconds, year = time_elements_tuple
    month = self._MONTH_DICT.get(month.lower(), 0)
    return (year, month, day_of_month, hours, minutes, seconds)

  def _ParseLogLine(self, parser_mediator, structure):
    """Parses a log line.

    Args:
        parser_mediator (ParserMediator): mediates interactions between parsers
            and other components, such as storage and dfVFS.
        structure (pyparsing.ParseResults): structure of tokens derived from
            a line of a text file.
    """
    time_elements_tuple = self._GetTimeElementsTuple(structure)
    try:
      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)
      date_time.is_local_time = True
    except ValueError:
      parser_mediator.ProduceExtractionWarning(
          'invalid date time value: {0!s}'.format(time_elements_tuple))
      return

    event_data = VsftpdEventData()
    event_data.text = self._GetValueFromStructure(structure, 'text')

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_ADDED,
        time_zone=parser_mediator.timezone)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def _ParseRecord(self, parser_mediator, key, structure):
    """Parses a log record structure and produces events.

    This function takes as an input a parsed pyparsing structure
    and produces an EventObject if possible from that structure.

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

    self._ParseLogLine(parser_mediator, structure)

  def CheckRequiredFormat(self, parser_mediator, text_file_object):
    """Check if the log record has the minimal structure required by the plugin.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_file_object (dfvfs.TextFile): text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    try:
      line = self._ReadLineOfText(text_file_object)
    except UnicodeDecodeError:
      return False

    if line and (' [pid ' not in line or ': Client ' not in line):
      return False

    try:
      parsed_structure = self._LOG_LINE.parseString(line)
    except pyparsing.ParseException:
      return False

    time_elements_tuple = self._GetTimeElementsTuple(parsed_structure)

    try:
      dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)
    except ValueError:
      return False

    return True


text_parser.PyparsingSingleLineTextParser.RegisterPlugin(VsftpdLogTextPlugin)
