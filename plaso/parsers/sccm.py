# -*_ coding: utf-8 -*-
"""Parser for SCCM Logs."""

import re

from dfdatetime import time_elements as dfdatetime_time_elements

import pyparsing

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import manager
from plaso.parsers import text_parser


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


class SCCMParser(text_parser.PyparsingMultiLineTextParser):
  """Parser for Windows System Center Configuration Manager (SCCM) logs."""

  NAME = 'sccm'
  DATA_FORMAT = 'System Center Configuration Manager (SCCM) client log file'

  _ENCODING = 'utf-8-sig'

  # Increasing the buffer size as SCCM messages are commonly well larger
  # than the default value.
  BUFFER_SIZE = 16384

  _ONE_OR_TWO_DIGITS = pyparsing.Word(pyparsing.nums, max=2).setParseAction(
      text_parser.PyParseIntCast)

  _TWO_OR_THREE_DIGITS = pyparsing.Word(
      pyparsing.nums, min=2, max=3).setParseAction(text_parser.PyParseIntCast)

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      text_parser.PyParseIntCast)

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      text_parser.PyParseIntCast)

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

  _LOG_MESSAGE = (
      pyparsing.Suppress('<![LOG[') +
      pyparsing.Regex(r'.*?(?=(]LOG]!><))', re.DOTALL).setResultsName('text') +
      pyparsing.Suppress(']LOG]!><'))

  _COMPONENT = (
      pyparsing.Suppress('" component="') +
      pyparsing.Word(pyparsing.alphanums).setResultsName('component'))

  _LOG_ENTRY = (
      _LOG_MESSAGE + _DATE_TIME + _COMPONENT +
      pyparsing.Regex(r'.*?(?=(\<!\[LOG\[))', re.DOTALL))

  _LAST_LOG_ENTRY = (
      _LOG_MESSAGE + _DATE_TIME + _COMPONENT +
      pyparsing.restOfLine + pyparsing.lineEnd)

  _LINE_STRUCTURES = [
      ('log_entry', _LOG_ENTRY),
      ('log_entry_at_end', _LAST_LOG_ENTRY)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in _LINE_STRUCTURES])

  def _BuildDateTime(self, time_elements_structure):
    """Builds time elements from a PostgreSQL log time stamp.

    Args:
      time_elements_structure (pyparsing.ParseResults): structure of tokens
          derived from a SCCM log time stamp.

    Returns:
      dfdatetime.TimeElements: date and time extracted from the structure or
          None if the structure does not represent a valid string.
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
    except (TypeError, ValueError):
      return None

  def CheckRequiredFormat(self, parser_mediator, text_reader):
    """Check if the log record has the minimal structure required by the parser.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    # Because logs files can lead with a partial event,
    # we can't assume that the first character (post-BOM)
    # in the file is the beginning of our match - so we
    # look for match anywhere in lines.
    return pyparsing.Literal('<![LOG[').match in text_reader.lines

  def ParseRecord(self, parser_mediator, key, structure):
    """Parse the record and return an SCCM log event object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in self._SUPPORTED_KEYS:
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    time_elements_structure = self._GetValueFromStructure(
         structure, 'date_time')

    event_data = SCCMLogEventData()
    event_data.component = self._GetValueFromStructure(structure, 'component')
    event_data.text = self._GetValueFromStructure(structure, 'text')
    event_data.written_time = self._BuildDateTime(time_elements_structure)

    parser_mediator.ProduceEventData(event_data)


manager.ParsersManager.RegisterParser(SCCMParser)
