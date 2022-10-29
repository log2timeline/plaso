# -*- coding: utf-8 -*-
"""Text parser plugin for Sophos anti-virus logs (SAV.txt) files.

Also see:
  https://support.sophos.com/support/s/article/KB-000033745?language=en_US
"""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class SophosAVLogEventData(events.EventData):
  """Sophos anti-virus log event data.

  Attributes:
    text (str): Sophos anti-virus log message.
  """

  DATA_TYPE = 'sophos:av:log'

  def __init__(self):
    """Initializes event data."""
    super(SophosAVLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.text = None


class SophosAVLogTextPlugin(interface.TextPlugin):
  """Text parser plugin for Sophos anti-virus logs (SAV.txt) files."""

  NAME = 'sophos_av'
  DATA_FORMAT = 'Sophos anti-virus log file (SAV.txt) file'

  ENCODING = 'utf-16-le'

  _MAXIMUM_LINE_LENGTH = 4096

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      text_parser.PyParseIntCast)

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      text_parser.PyParseIntCast)

  # Note that the whitespace is suppressed by pyparsing.

  _DATE_TIME = pyparsing.Group(
      _FOUR_DIGITS.setResultsName('year') +
      _TWO_DIGITS.setResultsName('month') +
      _TWO_DIGITS.setResultsName('day_of_month') +
      _TWO_DIGITS.setResultsName('hours') +
      _TWO_DIGITS.setResultsName('minutes') +
      _TWO_DIGITS.setResultsName('seconds')).setResultsName('date_time')

  _LOG_LINE = (
      _DATE_TIME + pyparsing.SkipTo(pyparsing.lineEnd).setResultsName('text'))

  _LINE_STRUCTURES = [('logline', _LOG_LINE)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in _LINE_STRUCTURES])

  def _ParseLogLine(self, parser_mediator, structure):
    """Parses a log line.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    # Ensure time_elements_tuple is not a pyparsing.ParseResults otherwise
    # copy.deepcopy() of the dfDateTime object will fail on Python 3.8 with:
    # "TypeError: 'str' object is not callable" due to pyparsing.ParseResults
    # overriding __getattr__ with a function that returns an empty string when
    # named token does not exists.
    time_elements_structure = structure.get('date_time', None)

    try:
      year, month, day_of_month, hours, minutes, seconds = (
          time_elements_structure)

      date_time = dfdatetime_time_elements.TimeElements(time_elements_tuple=(
          year, month, day_of_month, hours, minutes, seconds))
      # TODO: check if date and time values are local time or in UTC.
      date_time.is_local_time = True

    except (TypeError, ValueError):
      parser_mediator.ProduceExtractionWarning(
          'invalid date time value: {0!s}'.format(time_elements_structure))
      return

    event_data = SophosAVLogEventData()
    event_data.text = self._GetValueFromStructure(structure, 'text')

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_ADDED,
        time_zone=parser_mediator.timezone)
    parser_mediator.ProduceEventWithEventData(event, event_data)

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

    # There should be spaces at position 9 and 16.
    if len(line) < 16 or ' ' not in (line[8], line[15]):
      return False

    try:
      parsed_structure = self._LOG_LINE.parseString(line)
    except pyparsing.ParseException:
      parsed_structure = None

    if not parsed_structure:
      return False

    date_time_value = self._GetValueFromStructure(parsed_structure, 'date_time')
    try:
      dfdatetime_time_elements.TimeElements(time_elements_tuple=date_time_value)
    except ValueError:
      return False

    return True


text_parser.SingleLineTextParser.RegisterPlugin(SophosAVLogTextPlugin)
