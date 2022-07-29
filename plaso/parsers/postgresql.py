# -*- coding: utf-8 -*-
"""Parser for PostgreSQL log files."""

import string
import pyparsing

from dateutil import parser

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions, errors
from plaso.parsers import logger
from plaso.parsers import manager
from plaso.parsers import text_parser

class PostgreSQLEventData(events.EventData):
  """PostgreSQL log data.

  Attributes:
    pid (int): process identifier (PID).
    user (str): "user@database" string if present.
    log_level (str): logging level of event
    log_line (str): log message.
  """

  DATA_TYPE = 'postgresql'

  def __init__(self):
    """Initializes event data."""
    super(PostgreSQLEventData, self).__init__(data_type=self.DATA_TYPE)
    self.pid = None
    self.user = None
    self.log_level = None
    self.log_line = None

class PostgreSQLParser(text_parser.PyparsingMultiLineTextParser):
  """Parses events from PostgreSQL log files."""

  NAME = 'postgresql'
  DATA_FORMAT = 'PostgreSQL log file'
  _ENCODING = 'utf-8'

  _DATE_TIME = pyparsing.Group(
    pyparsing.LineStart() +
    text_parser.PyparsingConstants.DATE_ELEMENTS +
    text_parser.PyparsingConstants.TIME.setResultsName('time') +
    pyparsing.Optional(
      pyparsing.Suppress('.') +
      text_parser.PyparsingConstants.INTEGER
    ).setResultsName('microseconds') +
    pyparsing.Word(pyparsing.printables).setResultsName('time_zone')
  ).setResultsName('date_time')

  _PID = pyparsing.Group(
    pyparsing.Suppress('[') +
    pyparsing.OneOrMore(text_parser.PyparsingConstants.INTEGER) +
    pyparsing.Optional(pyparsing.Literal('-')) +
    pyparsing.ZeroOrMore(text_parser.PyparsingConstants.INTEGER) +
    pyparsing.Suppress(']')
  ).setResultsName('pid')

  _USER_AND_DATABASE = pyparsing.Group(
    pyparsing.Word(pyparsing.alphanums) +
    pyparsing.Literal('@') +
    pyparsing.Word(pyparsing.alphanums)
  ).setResultsName('user_and_database')

  _LOG_LEVEL = (
    pyparsing.Word(string.ascii_uppercase) +
    pyparsing.Suppress(':')
  ).setResultsName('log_level')

  _LOG_LINE_END = _BODY_END = pyparsing.StringEnd() | _DATE_TIME

  _LOG_LINE = (
    _DATE_TIME +
    _PID +
    pyparsing.Optional(_USER_AND_DATABASE) +
    _LOG_LEVEL +
    pyparsing.SkipTo(_LOG_LINE_END).setResultsName('log_line') +
    pyparsing.ZeroOrMore(pyparsing.lineEnd())
  )

  LINE_STRUCTURES = [
    ('logline', _LOG_LINE),
  ]

  def _ConvertTimeString(self, structure):
    """Converts the structure to a datetime object.

    The date and time values are formatted as:
    "2022-04-12 00:16:05.526 UTC".

    Args:
      structure (pyparsing.ParseResults): structure of tokens derived from a
          line of a text file, that contains the time elements.

    Returns:
      datetime: datetime object.

    Raises:
      ValueError: if the structure cannot be converted into a datetime.
    """
    try:
      dts = '{0:d}-{1:d}-{2:d} {3:d}:{4:d}:{5:d}.{6:d} {7:s}'.format(
        structure['year'], structure['month'], structure['day_of_month'],
        structure['time']['hours'], structure['time']['minutes'],
        structure['time']['seconds'], structure.get('microseconds', [0])[0],
        structure['time_zone'])
    except (TypeError, ValueError) as exception:
      raise ValueError(
          'unable to format date time string with error: {0!s}.'.format(
              exception))
    return parser.parse(timestr=dts)


  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a record and produces a PostgreSQL event.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): elements parsed from the file.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key != 'logline':
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    event_data = PostgreSQLEventData()
    event_data.pid = ''.join(
      [str(x) for x in self._GetValueFromStructure(structure, 'pid')])

    log_level = self._GetValueFromStructure(structure, 'log_level')
    if log_level and len(log_level) == 1:
      event_data.log_level = log_level[0]
    else:
      parser_mediator.ProduceExtractionWarning('no log level found')
      return

    user_and_database = self._GetValueFromStructure(
      structure, 'user_and_database')
    if user_and_database:
      event_data.user = ''.join(user_and_database)

    log_line = self._GetValueFromStructure(structure, 'log_line')
    if log_line:
      event_data.log_line = log_line.lstrip().rstrip()

    date_time_structure = self._GetValueFromStructure(structure, 'date_time')
    date_time_parsed = self._ConvertTimeString(date_time_structure)
    date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
    date_time.CopyFromDatetime(date_time_parsed)
    event = time_events.DateTimeValuesEvent(
      date_time, definitions.TIME_DESCRIPTION_RECORDED)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  # pylint: disable=unused-argument
  def VerifyStructure(self, parser_mediator, lines):
    """Verifies that this is a bash history file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between
          parsers and other components, such as storage and dfvfs.
      lines (str): one or more lines from the text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    try:
      _ = self._LOG_LINE.parseString(lines)
    except pyparsing.ParseException as exception:
      logger.debug('Not a PostgreSQL log file: {0!s}'.format(exception))
      return False

    return True

manager.ParsersManager.RegisterParser(PostgreSQLParser)
