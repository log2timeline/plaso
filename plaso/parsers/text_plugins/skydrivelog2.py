# -*- coding: utf-8 -*-
"""Text parser plugin for SkyDrive version 2 log files."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import logger
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class SkyDriveLog2EventData(events.EventData):
  """SkyDrive version 2 log event data.

  Attributes:
    added_time (dfdatetime.DateTimeValues): date and time the log entry
        was added.
    detail (str): details.
    log_level (str): log level.
    module (str): name of the module that generated the log message.
    source_code (str): source file and line number that generated the log
        message.
  """

  DATA_TYPE = 'skydrive:log:line'

  def __init__(self):
    """Initializes event data."""
    super(SkyDriveLog2EventData, self).__init__(data_type=self.DATA_TYPE)
    self.added_time = None
    self.detail = None
    self.log_level = None
    self.module = None
    self.source_code = None


class SkyDriveLog2TextPlugin(interface.TextPlugin):
  """Text parser plugin for SkyDrive version 2 log files."""

  NAME = 'skydrive_log_v2'
  DATA_FORMAT = 'OneDrive (or SkyDrive) version 2 log file'

  ENCODING = 'utf-8'

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _THREE_DIGITS = pyparsing.Word(pyparsing.nums, exact=3).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      lambda tokens: int(tokens[0], 10))

  IGNORE_FIELD = pyparsing.CharsNotIn(',').suppress()

  # Date and time values are formatted as: YYYY-MM-DD-hhmmss.###
  # For example: 2013-07-25-160323.291
  _HEADER_DATE_TIME = pyparsing.Group(
      _FOUR_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + _TWO_DIGITS + _TWO_DIGITS +
      pyparsing.Suppress('.') + _THREE_DIGITS).setResultsName(
          'header_date_time')

  # Date and time values are formatted as: MM-DD-YY,hh:mm:ss.###
  # For example: 07-25-13,16:06:31.820
  _DATE_TIME = (
      _TWO_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress(',') +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') + _TWO_DIGITS +
      pyparsing.Suppress('.') + _THREE_DIGITS).setResultsName('date_time')

  _SDF_HEADER_START = (
      pyparsing.Literal('######').suppress() +
      pyparsing.Literal('Logging started.').setResultsName('log_start'))

  # Multiline entry end marker, matched from right to left.
  _SDF_ENTRY_END = pyparsing.StringEnd() | _SDF_HEADER_START | _DATE_TIME

  _SDF_LINE = (
      _DATE_TIME + pyparsing.Suppress(',') +
      IGNORE_FIELD + pyparsing.Suppress(',') +
      IGNORE_FIELD + pyparsing.Suppress(',') +
      IGNORE_FIELD + pyparsing.Suppress(',') +
      pyparsing.CharsNotIn(',').setResultsName('module') +
      pyparsing.Suppress(',') +
      pyparsing.CharsNotIn(',').setResultsName('source_code') +
      pyparsing.Suppress(',') +
      IGNORE_FIELD + pyparsing.Suppress(',') +
      IGNORE_FIELD + pyparsing.Suppress(',') +
      pyparsing.CharsNotIn(',').setResultsName('log_level') +
      pyparsing.Suppress(',') +
      pyparsing.SkipTo(_SDF_ENTRY_END).setResultsName('detail') +
      pyparsing.ZeroOrMore(pyparsing.lineEnd()))

  _SDF_HEADER = (
      _SDF_HEADER_START +
      pyparsing.Literal('Version=').setResultsName('version_string') +
      pyparsing.Word(pyparsing.nums + '.').setResultsName('version_number') +
      pyparsing.Literal('StartSystemTime:').suppress() +
      _HEADER_DATE_TIME +
      pyparsing.Literal('StartLocalTime:').setResultsName(
          'local_time_string') +
      pyparsing.SkipTo(pyparsing.lineEnd()).setResultsName('details') +
      pyparsing.lineEnd())

  _LINE_STRUCTURES = [
      ('logline', _SDF_LINE),
      ('header', _SDF_HEADER)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in _LINE_STRUCTURES])

  def _ParseHeader(self, parser_mediator, structure):
    """Parse header lines and store appropriate attributes.

    ['Logging started.', 'Version=', '17.0.2011.0627',
    [2013, 7, 25], 16, 3, 23, 291, 'StartLocalTime', '<details>']

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    time_elements_structure = self._GetValueFromStructure(
        structure, 'header_date_time')

    details = self._GetValueFromStructure(structure, 'details')
    local_time_string = self._GetValueFromStructure(
        structure, 'local_time_string')
    log_start = self._GetValueFromStructure(structure, 'log_start')
    version_number = self._GetValueFromStructure(structure, 'version_number')
    version_string = self._GetValueFromStructure(structure, 'version_string')

    event_data = SkyDriveLog2EventData()
    event_data.added_time = self._ParseHeaderTimeElements(
        time_elements_structure)
    # TODO: refactor detail to individual event data attributes.
    event_data.detail = '{0!s} {1!s} {2!s} {3!s} {4!s}'.format(
        log_start, version_string, version_number, local_time_string, details)

    parser_mediator.ProduceEventData(event_data)

  def _ParseHeaderTimeElements(self, time_elements_structure):
    """Parses date and time elements of a header line.

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

      year, month, day_of_month, hours, minutes, seconds, milliseconds = (
          time_elements_structure)

      time_elements_tuple = (
          year, month, day_of_month, hours, minutes, seconds, milliseconds)

      return dfdatetime_time_elements.TimeElementsInMilliseconds(
          time_elements_tuple=time_elements_tuple)

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse time elements with error: {0!s}'.format(exception))

  def _ParseLine(self, parser_mediator, structure):
    """Parses a logline and store appropriate attributes.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    # Replace newlines with spaces in structure.detail to preserve output.
    # TODO: refactor detail to individual event data attributes.
    detail = self._GetValueFromStructure(structure, 'detail', default_value='')
    detail = detail.replace('\n', ' ').strip(' ')

    event_data = SkyDriveLog2EventData()
    event_data.added_time = self._ParseTimeElements(time_elements_structure)
    event_data.detail = detail or None
    event_data.log_level = self._GetValueFromStructure(structure, 'log_level')
    event_data.module = self._GetValueFromStructure(structure, 'module')
    event_data.source_code = self._GetValueFromStructure(
        structure, 'source_code')

    parser_mediator.ProduceEventData(event_data)

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

    if key == 'logline':
      try:
        self._ParseLine(parser_mediator, structure)
      except errors.ParseError as exception:
        parser_mediator.ProduceExtractionWarning(
            'unable to parse log line with error: {0!s}'.format(exception))

    elif key == 'header':
      try:
        self._ParseHeader(parser_mediator, structure)
      except errors.ParseError as exception:
        parser_mediator.ProduceExtractionWarning(
            'unable to parse header line with error: {0!s}'.format(exception))

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

      year += 2000

      time_elements_tuple = (
          year, month, day_of_month, hours, minutes, seconds, milliseconds)

      return dfdatetime_time_elements.TimeElementsInMilliseconds(
          time_elements_tuple=time_elements_tuple)

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
      structure = self._SDF_HEADER.parseString(text_reader.lines)
    except pyparsing.ParseException:
      logger.debug('Not a SkyDrive log file')
      return False

    time_elements_tuple = self._GetValueFromStructure(
        structure, 'header_date_time')
    try:
      dfdatetime_time_elements.TimeElementsInMilliseconds(
          time_elements_tuple=time_elements_tuple)
    except ValueError:
      logger.debug(
          'Not a SkyDrive log file, invalid date and time: {0!s}'.format(
              time_elements_tuple))
      return False

    return True


text_parser.TextLogParser.RegisterPlugin(SkyDriveLog2TextPlugin)
