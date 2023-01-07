# -*_ coding: utf-8 -*-
"""Text parser plugin for System Center Configuration Manager (SCCM) logs."""

import re

from dfdatetime import time_elements as dfdatetime_time_elements

import pyparsing

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class SCCMLogEventData(events.EventData):
  """SCCM log event data.

  Attributes:
    component (str): component.
    text (str): text.
    written_time (dfdatetime.DateTimeValues): date and time the entry was
        written.
  """

  DATA_TYPE = 'sccm_log:entry'

  def __init__(self):
    """Initializes event data."""
    super(SCCMLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.component = None
    self.text = None
    self.written_time = None


class SCCMTextPlugin(interface.TextPlugin):
  """Text parser plugin for System Center Configuration Manager (SCCM) logs."""

  NAME = 'sccm'
  DATA_FORMAT = 'System Center Configuration Manager (SCCM) client log file'

  ENCODING = 'utf-8'

  _ONE_OR_TWO_DIGITS = pyparsing.Word(pyparsing.nums, max=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _TWO_OR_THREE_DIGITS = pyparsing.Word(
      pyparsing.nums, min=2, max=3).setParseAction(
          lambda tokens: int(tokens[0], 10))

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      lambda tokens: int(tokens[0], 10))

  # Date formatted as: date="M-D-YYYY"
  _DATE = (pyparsing.Suppress('" date="') + _ONE_OR_TWO_DIGITS +
           pyparsing.Suppress('-') + _ONE_OR_TWO_DIGITS +
           pyparsing.Suppress('-') + _FOUR_DIGITS)

  _TIME_ZONE_OFFSET = pyparsing.Group(
      pyparsing.Word('+-', exact=1) + _TWO_OR_THREE_DIGITS)

  # Time formatted as: time="h:mm:ss.###or time="h:mm:ss.###[+-]##"
  _TIME = (pyparsing.Suppress('time="') + _ONE_OR_TWO_DIGITS +
           pyparsing.Suppress(':') + _TWO_DIGITS + pyparsing.Suppress(':') +
           _TWO_DIGITS + pyparsing.Suppress('.') + pyparsing.Regex(r'\d{3,7}') +
           pyparsing.Optional(_TIME_ZONE_OFFSET))

  _DATE_TIME = (_TIME + _DATE).setResultsName('date_time')

  _LOG_MESSAGE_START = pyparsing.Suppress('<![LOG[')

  # Using a regular expression look ahead here is faster than pyparsing.SkipTo()
  _LOG_MESSAGE_TEXT = pyparsing.Regex(r'.*?(?=(]LOG]!><))', re.DOTALL)

  _LOG_MESSAGE_END = pyparsing.Suppress(']LOG]!><')

  _LOG_MESSAGE = (
      _LOG_MESSAGE_START + _LOG_MESSAGE_TEXT.setResultsName('text') +
      _LOG_MESSAGE_END)

  _COMPONENT = (
      pyparsing.Suppress('" component="') +
      pyparsing.Word(pyparsing.alphanums).setResultsName('component'))

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _LOG_LINE = (
      _LOG_MESSAGE + _DATE_TIME + _COMPONENT +
      pyparsing.Regex(r'.*?(?=(<!\[LOG\[))', re.DOTALL))

  _LAST_LOG_LINE = (
      _LOG_MESSAGE + _DATE_TIME + _COMPONENT +
      pyparsing.restOfLine() + _END_OF_LINE)

  _LINE_STRUCTURES = [
      ('log_line', _LOG_LINE),
      ('last_log_line', _LAST_LOG_LINE)]

  # Because logs files can lead with a partial event, we can't assume that
  # the first character (post-BOM) in the file is the beginning of our match,
  # so we look for match anywhere in lines.

  VERIFICATION_GRAMMAR = (
      pyparsing.Regex(r'.*<!\[LOG\[.*]LOG]!><', re.DOTALL) + _DATE_TIME +
      _COMPONENT)

  VERIFICATION_LITERALS = ['<![LOG[', ']LOG]!><time="']

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

    event_data = SCCMLogEventData()
    event_data.component = self._GetValueFromStructure(structure, 'component')
    event_data.text = self._GetValueFromStructure(structure, 'text')
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
    # Ensure time_elements_tuple is not a pyparsing.ParseResults otherwise
    # copy.deepcopy() of the dfDateTime object will fail on Python 3.8 with:
    # "TypeError: 'str' object is not callable" due to pyparsing.ParseResults
    # overriding __getattr__ with a function that returns an empty string when
    # named token does not exist.

    try:
      if len(time_elements_structure) == 8:
        (hours, minutes, seconds, fraction_of_second, utc_offset_minutes, month,
         day_of_month, year) = time_elements_structure

        time_zone_offset = utc_offset_minutes[1]
        if utc_offset_minutes[0] == '-':
          time_zone_offset *= -1

      else:
        (hours, minutes, seconds, fraction_of_second, month, day_of_month,
         year) = time_elements_structure

        time_zone_offset = None

      if len(fraction_of_second) == 3:
        milliseconds = int(fraction_of_second, 10)
        time_elements_tuple=(
            year, month, day_of_month, hours, minutes, seconds, milliseconds)
        date_time = dfdatetime_time_elements.TimeElementsInMilliseconds(
            time_elements_tuple=time_elements_tuple,
            time_zone_offset=time_zone_offset)

      else:
        # TODO: improve precision support, but for now ignore the 100ns
        # precision.
        microseconds = int(fraction_of_second[:6], 10)
        time_elements_tuple=(
            year, month, day_of_month, hours, minutes, seconds, microseconds)
        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds(
            time_elements_tuple=time_elements_tuple,
            time_zone_offset=time_zone_offset)

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


text_parser.TextLogParser.RegisterPlugin(SCCMTextPlugin)
