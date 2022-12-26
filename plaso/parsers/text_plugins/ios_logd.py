# -*- coding: utf-8 -*-
"""Text parser plugin for iOS sysdiagnose logd files (logd.0.log)."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class IOSSysdiagnoseLogdData(events.EventData):
  """iOS sysdiagnose logd event data.

  Attributes:
    body (str): body of the event line.
    logger (str): name of the process that generated the event.
    written_time (dfdatetime.DateTimeValues): date and time the log entry was
        written.
  """

  DATA_TYPE = 'ios:sysdiagnose:logd:line'

  def __init__(self):
    """Initializes iOS sysdiagnose logd event data."""
    super(IOSSysdiagnoseLogdData, self).__init__(data_type=self.DATA_TYPE)
    self.body = None
    self.logger = None
    self.written_time = None


class IOSSysdiagnoseLogdTextPlugin(interface.TextPlugin):
  """Text parser plugin for iOS sysdiagnose logd files (logd.0.log)."""

  NAME = 'ios_logd'
  DATA_FORMAT = 'iOS sysdiagnose logd file'

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _TIME_ZONE_OFFSET = (
      pyparsing.Word('+-', exact=1) + _TWO_DIGITS + _TWO_DIGITS)

  # Date and time values are formatted as: 2021-08-11 05:50:23-0700
  _DATE_TIME = (
      _FOUR_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress('-') + _TWO_DIGITS +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') + _TWO_DIGITS +
      _TIME_ZONE_OFFSET)

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _LOGGER = pyparsing.Combine(
      pyparsing.Word(pyparsing.alphas + '_') + pyparsing.Literal('[') +
      pyparsing.Word(pyparsing.nums) + pyparsing.Literal(']'))

  _LOG_LINE = (
      _DATE_TIME.setResultsName('date_time') +
      _LOGGER.setResultsName('logger') + pyparsing.Suppress(': ') +
      pyparsing.restOfLine().setResultsName('body') + _END_OF_LINE)

  _LINE_STRUCTURES = [('log_entry', _LOG_LINE)]

  VERIFICATION_GRAMMAR = _LOG_LINE

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

    event_data = IOSSysdiagnoseLogdData()
    event_data.body = self._GetValueFromStructure(
        structure, 'body', default_value='')
    event_data.logger = self._GetValueFromStructure(
        structure, 'logger', default_value='')
    event_data.written_time = self._ParseTimeElements(time_elements_structure)

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
      (year, month, day_of_month, hours, minutes, seconds, time_zone_sign,
       time_zone_hours, time_zone_minutes) = time_elements_structure

      time_zone_offset = (time_zone_hours * 60) + time_zone_minutes
      if time_zone_sign == '-':
        time_zone_offset *= -1

      time_elements_tuple = (year, month, day_of_month, hours, minutes, seconds)

      return dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple,
          time_zone_offset=time_zone_offset)

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
    except errors.ParseError:
      return False

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    try:
      self._ParseTimeElements(time_elements_structure)
    except errors.ParseError:
      return False

    return True


text_parser.TextLogParser.RegisterPlugin(IOSSysdiagnoseLogdTextPlugin)
