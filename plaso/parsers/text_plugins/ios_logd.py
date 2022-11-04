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
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
    logger (str): name of the process that generated the event.
  """

  DATA_TYPE = 'ios:sysdiagnose:logd:line'

  def __init__(self):
    """Initializes iOS sysdiagnose logd event data."""
    super(IOSSysdiagnoseLogdData, self).__init__(data_type=self.DATA_TYPE)
    self.body = None
    self.last_written_time = None
    self.logger = None


class IOSSysdiagnoseLogdTextPlugin(interface.TextPlugin):
  """Text parser plugin for iOS sysdiagnose logd files (logd.0.log)."""

  NAME = 'ios_logd'
  DATA_FORMAT = 'iOS sysdiagnose logd file'

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      text_parser.PyParseIntCast)

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      text_parser.PyParseIntCast)

  _TIME_ZONE_OFFSET = (
      pyparsing.Word('+-', exact=1) + _TWO_DIGITS + _TWO_DIGITS)

  # Date and time values are formatted as: 2021-08-11 05:50:23-0700
  _DATE_TIME = (
      _FOUR_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress('-') + _TWO_DIGITS +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') + _TWO_DIGITS +
      _TIME_ZONE_OFFSET)

  _LOGGER = (pyparsing.SkipTo(':').setResultsName('logger') +
             pyparsing.Suppress(': '))

  _LINE_GRAMMAR = (
      _DATE_TIME.setResultsName('date_time') +
      _LOGGER +
      pyparsing.SkipTo(pyparsing.LineEnd()).setResultsName('body'))

  _LINE_STRUCTURES = [('log_entry', _LINE_GRAMMAR)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in _LINE_STRUCTURES])

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

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    event_data = IOSSysdiagnoseLogdData()
    event_data.body = self._GetValueFromStructure(structure, 'body')
    event_data.last_written_time = self._ParseTimeElements(
        time_elements_structure)
    event_data.logger = self._GetValueFromStructure(structure, 'logger')

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

    try:
      parsed_structure = self._LINE_GRAMMAR.parseString(line)
    except pyparsing.ParseException:
      return False

    time_elements_structure = self._GetValueFromStructure(
        parsed_structure, 'date_time')

    try:
      self._ParseTimeElements(time_elements_structure)
    except errors.ParseError:
      return False

    return True


text_parser.SingleLineTextParser.RegisterPlugin(IOSSysdiagnoseLogdTextPlugin)
