# -*- coding: utf-8 -*-
"""Parser for the logd.0.log file obtained from iOS Sysdiagnose file dumps."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import manager
from plaso.parsers import text_parser


class LogdEventData(events.EventData):
  """logd event data
  Attributes:
    logger (str): process that submits the log event
    body (str): body of the event line
  """

  DATA_TYPE = "logd:line"

  def __init__(self):
    """Initializes event data."""
    super(LogdEventData, self).__init__(data_type=self.DATA_TYPE)
    self.logger = None
    self.body = None


class LogdParser(text_parser.PyparsingSingleLineTextParser):
  """Parser for the logd.0.log file obtained from iOS Sysdiagnose file dumps."""

  NAME = 'logd.0.log'
  DATA_FORMAT = 'logd log'

  DATE_ELEMENTS = text_parser.PyparsingConstants.DATE_ELEMENTS
  TIME_ELEMENTS = text_parser.PyparsingConstants.TIME_ELEMENTS

  _TIMESTAMP = DATE_ELEMENTS + TIME_ELEMENTS

  _TIME_DELTA = pyparsing.Word(
    pyparsing.nums + '+' + '-', exact=5)('time_delta')

  _LOGGER = pyparsing.SkipTo(':')('logger') + pyparsing.Suppress(': ')

  _BODY = pyparsing.SkipTo(pyparsing.LineEnd())('body')

  _LINE_GRAMMAR = _TIMESTAMP + _TIME_DELTA + _LOGGER + _BODY

  LINE_STRUCTURES = [('log_entry', _LINE_GRAMMAR)]

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a log record structure and produces events.
    This function takes as an input a parsed pyparsing structure
    and produces an EventObject if possible from that structure.
    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
        and other components, such as storage and dfvfs.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): tokens from a parsed log line.
      """

    if key != 'log_entry':
      raise errors.ParseError(
        'Unable to parse record, unknown structure: {0:s}'.format(key))

    year = self._GetValueFromStructure(structure, 'year')
    month = self._GetValueFromStructure(structure, 'month')
    day = self._GetValueFromStructure(structure, 'day_of_month')
    hours = self._GetValueFromStructure(structure, 'hours')
    minutes = self._GetValueFromStructure(structure, 'minutes')
    seconds = self._GetValueFromStructure(structure, 'seconds')

    time_delta = self._GetValueFromStructure(structure, 'time_delta')
    time_deta_hours = time_delta[:3]
    # dfdatetime takes the time zone offset as an int number of minutes but
    # inverts the sign for example Easter Standard Time, which is UTC-5:00 needs
    # to be provided as +300 minutes.
    time_offset = -1 * int(time_deta_hours) * 60 + int(time_delta[3:])

    event_data = LogdEventData()
    event_data.logger = self._GetValueFromStructure(structure, 'logger')
    event_data.body = self._GetValueFromStructure(structure, 'body')

    try:
      date_time = dfdatetime_time_elements.TimeElements(time_elements_tuple=(
        year, month, day, hours, minutes, seconds),
        time_zone_offset=time_offset)
    except (TypeError, ValueError):
      parser_mediator.ProduceExtractionWarning('invalid date time value')
      return

    event = time_events.DateTimeValuesEvent(
      date_time, definitions.TIME_DESCRIPTION_MODIFICATION)

    parser_mediator.ProduceEventWithEventData(event, event_data)

  def VerifyStructure(self, parser_mediator, line):
    """Verifies that this is a mobile installation log file.
    Args:
      parser_mediator (ParserMediator): mediates interactions between
        parsers and other components, such as storage and dfvfs.
      line (str): one line from the text file.
    Returns:
      bool: True if this is the correct parser, False otherwise.
    """

    match_generator = self._LINE_GRAMMAR.scanString(line, maxMatches=1)
    return bool(list(match_generator))


manager.ParsersManager.RegisterParser(LogdParser)
