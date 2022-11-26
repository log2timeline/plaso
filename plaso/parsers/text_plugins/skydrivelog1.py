# -*- coding: utf-8 -*-
"""Text parser plugin for SkyDrive version 1 log files."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import logger
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class SkyDriveOldLogEventData(events.EventData):
  """SkyDrive version 1 log event data.

  Attributes:
    added_time (dfdatetime.DateTimeValues): date and time the log entry
        was added.
    log_level (str): log level.
    source_code (str): source file and line number that generated the log
        message.
    text (str): log message.
  """

  DATA_TYPE = 'skydrive:log:old:line'

  def __init__(self):
    """Initializes event data."""
    super(SkyDriveOldLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.added_time = None
    self.log_level = None
    self.source_code = None
    self.text = None


class SkyDriveLog1TextPlugin(interface.TextPlugin):
  """Text parser plugin for SkyDrive version 1 log files."""

  NAME = 'skydrive_log_v1'
  DATA_FORMAT = 'OneDrive (or SkyDrive) version 1 log file'

  ENCODING = 'utf-8'

  _INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(
      text_parser.PyParseIntCast)

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      text_parser.PyParseIntCast)

  _THREE_DIGITS = pyparsing.Word(pyparsing.nums, exact=3).setParseAction(
      text_parser.PyParseIntCast)

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      text_parser.PyParseIntCast)

  # Date and time values are formatted as: DD-MM-YYYY hhmmss.###
  # For example: 08-01-2013 21:22:28.999
  _DATE_TIME = pyparsing.Group(
      _TWO_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress('-') + _FOUR_DIGITS +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') + _TWO_DIGITS +
      pyparsing.Word('.,', exact=1).suppress() + _THREE_DIGITS).setResultsName(
          'date_time')

  _SOURCE_CODE = pyparsing.Combine(
      pyparsing.CharsNotIn(':') + pyparsing.Literal(':') + _INTEGER +
      pyparsing.Literal('!') +
      pyparsing.Word(pyparsing.printables)).setResultsName('source_code')

  _LOG_LEVEL = (
      pyparsing.Suppress('(') +
      pyparsing.SkipTo(')').setResultsName('log_level') +
      pyparsing.Suppress(')'))

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _LOG_LINE = (
      _DATE_TIME + _SOURCE_CODE + _LOG_LEVEL + pyparsing.Suppress(':') +
      pyparsing.restOfLine().setResultsName('text') +
      _END_OF_LINE)

  # Sometimes the timestamped log line is followed by an empty line,
  # then by a file name plus other data and finally by another empty
  # line. It could happen that a log line is split in two parts.
  # These lines will not be discarded and an event will be generated
  # ad-hoc (see source), based on the last one if available.
  _NO_HEADER_SINGLE_LINE = (
      pyparsing.NotAny(_DATE_TIME) +
      pyparsing.Optional(pyparsing.Suppress('->')) +
      pyparsing.restOfLine().setResultsName('text') +
      _END_OF_LINE)

  # Define the available log line structures.
  _LINE_STRUCTURES = [
      ('log_line', _LOG_LINE),
      ('no_header_single_line', _NO_HEADER_SINGLE_LINE)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in _LINE_STRUCTURES])

  def __init__(self):
    """Initializes a text parser plugin."""
    super(SkyDriveLog1TextPlugin, self).__init__()
    self._event_data = None

  def _ParseLogline(self, parser_mediator, structure):
    """Parse a log line.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    event_data = SkyDriveOldLogEventData()
    event_data.added_time = self._ParseTimeElements(time_elements_structure)
    event_data.log_level = self._GetValueFromStructure(structure, 'log_level')
    event_data.source_code = self._GetValueFromStructure(
        structure, 'source_code')
    event_data.text = self._GetStringValueFromStructure(structure, 'text')

    parser_mediator.ProduceEventData(event_data)

    self._event_data = event_data

  def _ParseNoHeaderSingleLine(self, parser_mediator, structure):
    """Parse an isolated header line and store appropriate attributes.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    if not self._event_data:
      logger.debug('SkyDrive, found isolated line with no previous events')
      return

    event_data = SkyDriveOldLogEventData()
    event_data.added_time = self._event_data.added_time
    event_data.text = self._GetValueFromStructure(structure, 'text')

    parser_mediator.ProduceEventData(event_data)

    self._ResetState()

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

    if key == 'log_line':
      self._ParseLogline(parser_mediator, structure)

    elif key == 'no_header_single_line':
      self._ParseNoHeaderSingleLine(parser_mediator, structure)

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

      month, day_of_month, year, hours, minutes, seconds, milliseconds = (
          time_elements_structure)

      time_elements_tuple = (
          year, month, day_of_month, hours, minutes, seconds, milliseconds)

      # TODO: determine if this should be local time.
      return dfdatetime_time_elements.TimeElementsInMilliseconds(
          time_elements_tuple=time_elements_tuple)

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse time elements with error: {0!s}'.format(exception))

  def _ResetState(self):
    """Resets stored values."""
    self._event_data = None

  def CheckRequiredFormat(self, parser_mediator, text_reader):
    """Check if the log record has the minimal structure required by the plugin.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    line = text_reader.ReadLine()

    try:
      parsed_structure = self._LOG_LINE.parseString(line)
    except pyparsing.ParseException:
      return False

    time_elements_structure = self._GetValueFromStructure(
        parsed_structure, 'date_time')

    try:
      self._ParseTimeElements(time_elements_structure)
    except errors.ParseError:
      return False

    self._ResetState()

    return True


text_parser.TextLogParser.RegisterPlugin(SkyDriveLog1TextPlugin)
