# -*- coding: utf-8 -*-
"""Text parser plugin for Sophos anti-virus logs (SAV.txt) files.

Also see:
  https://support.sophos.com/support/s/article/KB-000033745?language=en_US
"""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class SophosAVLogEventData(events.EventData):
  """Sophos anti-virus log event data.

  Attributes:
    added_time (dfdatetime.DateTimeValues): date and time the log entry
        was added.
    text (str): Sophos anti-virus log message.
  """

  DATA_TYPE = 'sophos:av:log'

  def __init__(self):
    """Initializes event data."""
    super(SophosAVLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.added_time = None
    self.text = None


class SophosAVLogTextPlugin(interface.TextPlugin):
  """Text parser plugin for Sophos anti-virus logs (SAV.txt) files."""

  NAME = 'sophos_av'
  DATA_FORMAT = 'Sophos anti-virus log file (SAV.txt) file'

  ENCODING = 'utf-16-le'

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      lambda tokens: int(tokens[0], 10))

  # Date and time values are formatted as: YYYYMMDD hhmmss
  # For example: 20100720 183814
  _DATE_TIME = pyparsing.Group(
      _FOUR_DIGITS + _TWO_DIGITS + _TWO_DIGITS +
      _TWO_DIGITS + _TWO_DIGITS + _TWO_DIGITS)

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _LOG_LINE = (
      _DATE_TIME.setResultsName('date_time') +
      pyparsing.restOfLine().setResultsName('text') +
      _END_OF_LINE)

  _LINE_STRUCTURES = [('log_line', _LOG_LINE)]

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

    event_data = SophosAVLogEventData()
    event_data.added_time = self._ParseTimeElements(time_elements_structure)
    event_data.text = self._GetStringValueFromStructure(structure, 'text')

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
      # Ensure time_elements_tuple is not a pyparsing.ParseResults otherwise
      # copy.deepcopy() of the dfDateTime object will fail on Python 3.8 with:
      # "TypeError: 'str' object is not callable" due to pyparsing.ParseResults
      # overriding __getattr__ with a function that returns an empty string
      # when named token does not exists.

      year, month, day_of_month, hours, minutes, seconds = (
          time_elements_structure)

      time_elements_tuple = (year, month, day_of_month, hours, minutes, seconds)

      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)

      # TODO: check if date and time values are local time or in UTC.
      date_time.is_local_time = True

      return date_time

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
    except ValueError:
      return False

    return True


text_parser.TextLogParser.RegisterPlugin(SophosAVLogTextPlugin)
