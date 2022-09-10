# -*- coding: utf-8 -*-
"""Text parser plugin for SkyDrive version 1 log files."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import logger
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class SkyDriveOldLogEventData(events.EventData):
  """SkyDrive version 1 log event data.

  Attributes:
    log_level (str): log level.
    source_code (str): source file and line number that generated the log
        message.
    text (str): log message.
  """

  DATA_TYPE = 'skydrive:log:old:line'

  def __init__(self):
    """Initializes event data."""
    super(SkyDriveOldLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.log_level = None
    self.source_code = None
    self.text = None


class SkyDriveLog1TextPlugin(interface.TextPlugin):
  """Text parser plugin for SkyDrive version 1 log files."""

  NAME = 'skydrive_log_v1'
  DATA_FORMAT = 'OneDrive (or SkyDrive) version 1 log file'

  ENCODING = 'utf-8'

  _FOUR_DIGITS = text_parser.PyparsingConstants.FOUR_DIGITS
  _TWO_DIGITS = text_parser.PyparsingConstants.TWO_DIGITS

  # Common pyparsing objects.
  _COLON = pyparsing.Literal(':')
  _EXCLAMATION = pyparsing.Literal('!')

  # Date and time format used in the header is: DD-MM-YYYY hhmmss.###
  # For example: 08-01-2013 21:22:28.999
  _DATE_TIME = pyparsing.Group(
      _TWO_DIGITS.setResultsName('month') + pyparsing.Suppress('-') +
      _TWO_DIGITS.setResultsName('day_of_month') + pyparsing.Suppress('-') +
      _FOUR_DIGITS.setResultsName('year') +
      text_parser.PyparsingConstants.TIME_MSEC_ELEMENTS).setResultsName(
          'date_time')

  _SOURCE_CODE = pyparsing.Combine(
      pyparsing.CharsNotIn(':') +
      _COLON +
      text_parser.PyparsingConstants.INTEGER +
      _EXCLAMATION +
      pyparsing.Word(pyparsing.printables)).setResultsName('source_code')

  _LOG_LEVEL = (
      pyparsing.Literal('(').suppress() +
      pyparsing.SkipTo(')').setResultsName('log_level') +
      pyparsing.Literal(')').suppress())

  _LINE = (
      _DATE_TIME + _SOURCE_CODE + _LOG_LEVEL +
      _COLON + pyparsing.SkipTo(pyparsing.lineEnd).setResultsName('text'))

  # Sometimes the timestamped log line is followed by an empty line,
  # then by a file name plus other data and finally by another empty
  # line. It could happen that a logline is split in two parts.
  # These lines will not be discarded and an event will be generated
  # ad-hoc (see source), based on the last one if available.
  _NO_HEADER_SINGLE_LINE = (
      pyparsing.NotAny(_DATE_TIME) +
      pyparsing.Optional(pyparsing.Literal('->').suppress()) +
      pyparsing.SkipTo(pyparsing.lineEnd).setResultsName('text'))

  # Define the available log line structures.
  _LINE_STRUCTURES = [
      ('logline', _LINE),
      ('no_header_single_line', _NO_HEADER_SINGLE_LINE)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in _LINE_STRUCTURES])

  def __init__(self):
    """Initializes a parser."""
    super(SkyDriveLog1TextPlugin, self).__init__()
    self._last_date_time = None
    self._last_event_data = None

  def _ParseLogline(self, parser_mediator, structure):
    """Parse a logline and store appropriate attributes.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    time_elements_tuple = self._GetValueFromStructure(structure, 'date_time')
    # TODO: what if time elements tuple is None.
    # TODO: Verify if date and time value is locale dependent.
    month, day_of_month, year, hours, minutes, seconds, milliseconds = (
        time_elements_tuple)

    time_elements_tuple = (
        year, month, day_of_month, hours, minutes, seconds, milliseconds)

    try:
      date_time = dfdatetime_time_elements.TimeElementsInMilliseconds(
          time_elements_tuple=time_elements_tuple)
    except ValueError:
      parser_mediator.ProduceExtractionWarning(
          'invalid date time value: {0!s}'.format(time_elements_tuple))
      return

    event_data = SkyDriveOldLogEventData()
    event_data.log_level = self._GetValueFromStructure(structure, 'log_level')
    event_data.source_code = self._GetValueFromStructure(
        structure, 'source_code')
    event_data.text = self._GetValueFromStructure(structure, 'text')

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_ADDED)
    parser_mediator.ProduceEventWithEventData(event, event_data)

    self._last_date_time = date_time
    self._last_event_data = event_data

  def _ParseNoHeaderSingleLine(self, parser_mediator, structure):
    """Parse an isolated header line and store appropriate attributes.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    if not self._last_event_data:
      logger.debug('SkyDrive, found isolated line with no previous events')
      return

    event_data = SkyDriveOldLogEventData()
    event_data.text = self._GetValueFromStructure(structure, 'text')

    event = time_events.DateTimeValuesEvent(
        self._last_date_time, definitions.TIME_DESCRIPTION_ADDED)
    parser_mediator.ProduceEventWithEventData(event, event_data)

    # TODO think to a possible refactoring for the non-header lines.
    self._last_date_time = None
    self._last_event_data = None

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
    if key not in self._SUPPORTED_KEYS:
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    if key == 'logline':
      self._ParseLogline(parser_mediator, structure)

    elif key == 'no_header_single_line':
      self._ParseNoHeaderSingleLine(parser_mediator, structure)

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
      parsed_structure = self._LINE.parseString(line)
    except pyparsing.ParseException:
      return False

    time_elements_tuple = self._GetValueFromStructure(
        parsed_structure, 'date_time')

    # TODO: what if time elements tuple is None.
    day_of_month, month, year, hours, minutes, seconds, milliseconds = (
        time_elements_tuple)

    time_elements_tuple = (
        year, month, day_of_month, hours, minutes, seconds, milliseconds)

    try:
      dfdatetime_time_elements.TimeElementsInMilliseconds(
          time_elements_tuple=time_elements_tuple)
    except ValueError:
      return False

    return True


text_parser.PyparsingSingleLineTextParser.RegisterPlugin(SkyDriveLog1TextPlugin)
