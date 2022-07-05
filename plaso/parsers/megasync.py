# -*- coding: utf-8 -*-
"""Parser for MEGASync log files.
"""


from dfdatetime import time_elements as dfdatetime_time_elements

import pyparsing

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import logger
from plaso.parsers import manager
from plaso.parsers import text_parser


class MEGASyncEventData(events.EventData):
  """MEGASync log event data.

  Attributes:
    log_level (str): log level.
    message (str): message.
  """

  DATA_TYPE = 'megasync:log:line'

  def __init__(self):
    """Initializes event data."""
    super(MEGASyncEventData, self).__init__(data_type=self.DATA_TYPE)
    self.log_level = None
    self.message = None

class MEGASyncParser(text_parser.PyparsingSingleLineTextParser):
  """Parses MEGASync log files"""

  NAME = 'megasync'
  DATA_FORMAT = 'MEGASync log file'

  # Some types of MEGASync log lines can be very long.
  MAX_LINE_LENGTH = 65536

  _ENCODING = 'utf-8'

  _TWO_DIGITS = text_parser.PyparsingConstants.TWO_DIGITS

  # Timestamp format is: mm/dd-hh:mm:ss.######
  # For example: 03/21-04:13:44.621454
  _TIMESTAMP = pyparsing.Group(
      _TWO_DIGITS.setResultsName('month') + pyparsing.Suppress('/') +
      _TWO_DIGITS.setResultsName('day') + pyparsing.Suppress('-') +
      text_parser.PyparsingConstants.TIME_MSEC_ELEMENTS
  ).setResultsName('timestamp')

  _THREAD_NAME = text_parser.PyparsingConstants.INTEGER.suppress()

  _LOG_LEVEL = (
      pyparsing.Literal('CRIT') |
      pyparsing.Literal('ERR') |
      pyparsing.Literal('WARN') |
      pyparsing.Literal('INFO') |
      pyparsing.Literal('DBG') |
      pyparsing.Literal('DTL')
  ).setResultsName('log_level')

  _MESSAGE = (
      pyparsing.White(ws=' ', min=1, max=2).suppress() +
      pyparsing.restOfLine().setResultsName('message')
  )

  _LOG_LINE = _TIMESTAMP + _THREAD_NAME + _LOG_LEVEL + _MESSAGE

  # Indicates that the last log line was repeated multiple times.
  _REPEAT_LINE = (
      pyparsing.Suppress('[repeated x') +
      text_parser.PyparsingConstants.INTEGER +
      pyparsing.Suppress("]")
  ).setResultsName("repeats")

  LINE_STRUCTURES = [
      ('line', _LOG_LINE),
      ('repeat', _REPEAT_LINE),
  ]

  def __init__(self):
    """Initializes a parser."""
    super(MEGASyncParser, self).__init__()
    self._last_month = 0
    self._maximum_year = 0
    self._year_use = 0

  def _UpdateYear(self, mediator, month):
    """Updates the year to use for events, based on last observed month.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      month (int): month observed by the parser, where January is 1.
    """
    # TODO: use timestamps of the Gzip file, not the file
    # within the Gzip file as the basis of estimation.
    if not self._year_use:
      self._year_use = mediator.GetEstimatedYear()

      # zlib (used by MEGASync to compress rotated-out log files)
      # can generate Gzip files with empty modification timestamp.
      # This shouldn't be used as the estimated year.
      # MEGASync logs can't originate from 1970, so this is safe.
      if self._year_use == 1970:
        self._year_use = mediator.GetCurrentYear()
    if not self._maximum_year:
      self._maximum_year = mediator.GetLatestYear()

    if not self._last_month:
      self._last_month = month
      return

    if self._last_month > month:
      if self._year_use < self._maximum_year:
        self._year_use += 1
    self._last_month = month


  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a structure of tokens derived from a line of a text file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.

    Raises:
      ParseError: when the structure type is unknown.
    """
    # TODO: consider handling repeat lines as well. Repeating lines
    #       are mostly cURL-related debug lines, so likely not of much use.
    if key != "repeat":
      time_elements_tuple = self._GetValueFromStructure(structure, 'timestamp')
      month, day_of_month, hours, minutes, seconds, milliseconds = (
          time_elements_tuple)

      self._UpdateYear(parser_mediator, month)

      time_elements_tuple = (
          self._year_use,
          month, day_of_month, hours, minutes, seconds, milliseconds)

      try:
        timestamp = dfdatetime_time_elements.TimeElements(
            time_elements_tuple=time_elements_tuple)
      except ValueError:
        parser_mediator.ProduceExtractionWarning(
            'invalid timestamp: {0!s}'.format(time_elements_tuple)
        )
        return

      event_data = MEGASyncEventData()
      event_data.message = self._GetValueFromStructure(structure, 'message')
      event_data.log_level = self._GetValueFromStructure(structure, 'log_level')
      event = time_events.DateTimeValuesEvent(
          timestamp, definitions.TIME_DESCRIPTION_RECORDED)
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def VerifyStructure(self, parser_mediator, line):
    """Verifies if a line from a text file is in the expected format.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      line (str): line from a text file.

    Returns:
      bool: True if the line is in the expected format, False if not.
    """

    verified = False
    for _, line_structure in self.LINE_STRUCTURES:
      try:
        _ = line_structure.parseString(line)
      except pyparsing.ParseException:
        continue
      verified = True
      break
    if not verified:
      logger.debug('Not a MEGASync log file')

    return verified


manager.ParsersManager.RegisterParser(MEGASyncParser)
