# -*- coding: utf-8 -*-
"""Text parser plugin for iOS sysdiagnose logd files (logd.0.log)."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class IOSSysdiagnoseLogdData(events.EventData):
  """iOS sysdiagnose logd event data.

  Attributes:
    body (str): body of the event line.
    logger (str): name of the process that generated the event.
  """

  DATA_TYPE = 'ios:sysdiagnose:logd:line'

  def __init__(self):
    """Initializes iOS sysdiagnose logd event data."""
    super(IOSSysdiagnoseLogdData, self).__init__(data_type=self.DATA_TYPE)
    self.body = None
    self.logger = None


class IOSSysdiagnoseLogdTextPlugin(interface.TextPlugin):
  """Text parser plugin for iOS sysdiagnose logd files (logd.0.log)."""

  NAME = 'ios_logd'
  DATA_FORMAT = 'iOS sysdiagnose logd file'

  _TIMESTAMP = (
      text_parser.PyparsingConstants.DATE_ELEMENTS +
      text_parser.PyparsingConstants.TIME_ELEMENTS)

  _TIME_DELTA = pyparsing.Word(
      pyparsing.nums + '+' + '-', exact=5).setResultsName('time_delta')

  _LOGGER = (pyparsing.SkipTo(':').setResultsName('logger') +
             pyparsing.Suppress(': '))

  _BODY = pyparsing.SkipTo(pyparsing.LineEnd()).setResultsName('body')

  _LINE_GRAMMAR = _TIMESTAMP + _TIME_DELTA + _LOGGER + _BODY

  _LINE_STRUCTURES = [('log_entry', _LINE_GRAMMAR)]

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

    event_data = IOSSysdiagnoseLogdData()
    event_data.body = self._GetValueFromStructure(structure, 'body')
    event_data.logger = self._GetValueFromStructure(structure, 'logger')

    # dfDateTime takes the time zone offset as number of minutes relative from
    # UTC. So for Easter Standard Time (EST), which is UTC-5:00 the sign needs
    # to be converted, to +300 minutes.
    try:
      time_delta_hours = int(time_delta[:3], 10)
      time_delta_minutes = int(time_delta[3:], 10)
    except (TypeError, ValueError):
      parser_mediator.ProduceExtractionWarning('unsupported time delta value')
      return

    time_zone_offset = (time_delta_hours * -60) + time_delta_minutes

    try:
      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=(year, month, day, hours, minutes, seconds),
          time_zone_offset=time_zone_offset)
    except (TypeError, ValueError):
      parser_mediator.ProduceExtractionWarning('unsupported date time value')
      return

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_MODIFICATION)

    parser_mediator.ProduceEventWithEventData(event, event_data)

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
      parsed_structure = None

    return bool(parsed_structure)


text_parser.SingleLineTextParser.RegisterPlugin(IOSSysdiagnoseLogdTextPlugin)
