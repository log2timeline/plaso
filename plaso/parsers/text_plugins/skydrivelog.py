# -*- coding: utf-8 -*-
"""Text parser plugins for SkyDrive version 1 and 2 log files."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import logger
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class SkyDriveLogEventData(events.EventData):
  """SkyDrive log event data.

  Attributes:
    added_time (dfdatetime.DateTimeValues): date and time the log entry
        was added.
    detail (str): detail.
    log_level (str): log level.
    module (str): name of the module that generated the log message.
    source_code (str): source file and line number that generated the log
        message.
  """

  DATA_TYPE = 'skydrive:log:entry'

  def __init__(self):
    """Initializes event data."""
    super(SkyDriveLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.added_time = None
    self.detail = None
    self.log_level = None
    self.module = None
    self.source_code = None


class SkyDriveLog1TextPlugin(interface.TextPlugin):
  """Text parser plugin for SkyDrive version 1 log files."""

  NAME = 'skydrive_log_v1'
  DATA_FORMAT = 'OneDrive (or SkyDrive) version 1 log file'

  ENCODING = 'utf-8'

  _INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _THREE_DIGITS = pyparsing.Word(pyparsing.nums, exact=3).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      lambda tokens: int(tokens[0], 10))

  # Format version 1 date and time values are formatted as:
  # DD-MM-YYYY hhmmss.###
  # For example: 08-01-2013 21:22:28.999
  _DATE_TIME_V1 = pyparsing.Group(
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

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _LOG_LINE_V1 = (
      _DATE_TIME_V1 + _SOURCE_CODE +
      pyparsing.QuotedString('(', endQuoteChar=')').setResultsName(
          'log_level') + pyparsing.Suppress(':') +
      pyparsing.restOfLine().setResultsName('detail') + _END_OF_LINE)

  # Sometimes the timestamped log line is followed by an empty line,
  # then by a file name plus other data and finally by another empty
  # line. It could happen that a log line is split in two parts.
  # These lines will not be discarded and an event will be generated
  # ad-hoc (see source), based on the last one if available.
  _NO_HEADER_SINGLE_LINE = (
      pyparsing.NotAny(_DATE_TIME_V1) +
      pyparsing.Optional(pyparsing.Suppress('->')) +
      pyparsing.restOfLine().setResultsName('detail') +
      _END_OF_LINE)

  # Define the available log line structures.
  _LINE_STRUCTURES = [
      ('log_line_v1', _LOG_LINE_V1),
      ('no_header_single_line', _NO_HEADER_SINGLE_LINE)]

  VERIFICATION_GRAMMAR = _LOG_LINE_V1

  def __init__(self):
    """Initializes a text parser plugin."""
    super(SkyDriveLog1TextPlugin, self).__init__()
    self._event_data = None

  def _ParseLoglineVersion1(self, parser_mediator, structure):
    """Parse a version 1 log line.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    event_data = SkyDriveLogEventData()
    event_data.added_time = self._ParseTimeElementsVersion1(
        time_elements_structure)
    event_data.detail = self._GetStringValueFromStructure(structure, 'detail')
    event_data.log_level = self._GetValueFromStructure(structure, 'log_level')
    event_data.source_code = self._GetValueFromStructure(
        structure, 'source_code')

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

    event_data = SkyDriveLogEventData()
    event_data.added_time = self._event_data.added_time
    event_data.detail = self._GetValueFromStructure(structure, 'detail')

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
      ParseError: if the structure cannot be parsed.
    """
    if key == 'log_line_v1':
      self._ParseLoglineVersion1(parser_mediator, structure)

    elif key == 'no_header_single_line':
      self._ParseNoHeaderSingleLine(parser_mediator, structure)

  def _ParseTimeElementsVersion1(self, time_elements_structure):
    """Parses date and time elements of a version 1 log line.

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
    try:
      structure = self._VerifyString(text_reader.lines)
    except errors.ParseError:
      return False

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    try:
      self._ParseTimeElementsVersion1(time_elements_structure)
    except errors.ParseError:
      return False

    self._ResetState()

    return True


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

  # Format version 2 header date and time values are formatted as:
  # YYYY-MM-DD-hhmmss.###
  # For example: 2013-07-25-160323.291
  _HEADER_DATE_TIME_V2 = pyparsing.Group(
      _FOUR_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + _TWO_DIGITS + _TWO_DIGITS +
      pyparsing.Suppress('.') + _THREE_DIGITS).setResultsName(
          'header_date_time')

  # Formate version 2 date and time values are formatted as:
  # MM-DD-YY,hh:mm:ss.###
  # For example: 07-25-13,16:06:31.820
  _DATE_TIME_V2 = (
      _TWO_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress(',') +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') + _TWO_DIGITS +
      pyparsing.Suppress('.') + _THREE_DIGITS).setResultsName('date_time')

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _HEADER_LINE_V2_START = (
      pyparsing.Suppress('######') +
      pyparsing.Literal('Logging started.').setResultsName('log_start') +
      pyparsing.Literal('Version=').setResultsName('version_string') +
      pyparsing.Word(pyparsing.nums + '.').setResultsName('version_number') +
      pyparsing.Suppress('StartSystemTime:') + _HEADER_DATE_TIME_V2 +
      pyparsing.Literal('StartLocalTime:').setResultsName('local_time_string'))

  _HEADER_LINE_V2 = (
      _HEADER_LINE_V2_START + pyparsing.restOfLine.setResultsName('detail') +
      _END_OF_LINE)

  _LOG_LINE_V2_START = (
      _DATE_TIME_V2 + pyparsing.Suppress(',') +
      pyparsing.Word(pyparsing.hexnums) + pyparsing.Suppress(',') +
      pyparsing.Word(pyparsing.hexnums) + pyparsing.Suppress(',') +
      pyparsing.Word(pyparsing.hexnums) + pyparsing.Suppress(',') +
      pyparsing.CharsNotIn(',').setResultsName('module') +
      pyparsing.Suppress(',') +
      pyparsing.CharsNotIn(',').setResultsName('source_code') +
      pyparsing.Suppress(',') +
      pyparsing.Word(pyparsing.hexnums) + pyparsing.Suppress(',') +
      pyparsing.Word(pyparsing.hexnums) + pyparsing.Suppress(',') +
      pyparsing.CharsNotIn(',').setResultsName('log_level') +
      pyparsing.Suppress(','))

  _LOG_LINE_V2 = (
      _LOG_LINE_V2_START + pyparsing.restOfLine.setResultsName('detail') +
      _END_OF_LINE)

  _SUCCESSIVE_LOG_LINE_V2 = (
      pyparsing.NotAny(_HEADER_LINE_V2_START ^ _LOG_LINE_V2_START) +
      pyparsing.restOfLine().setResultsName('detail') + _END_OF_LINE)

  _LINE_STRUCTURES = [
      ('header_line_v2', _HEADER_LINE_V2),
      ('log_line_v2', _LOG_LINE_V2),
      ('successive_log_line_v2', _SUCCESSIVE_LOG_LINE_V2)]

  VERIFICATION_GRAMMAR = _HEADER_LINE_V2

  def __init__(self):
    """Initializes a text parser plugin."""
    super(SkyDriveLog2TextPlugin, self).__init__()
    self._event_data = None

  def _ParseFinalize(self, parser_mediator):
    """Finalizes parsing.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
    """
    if self._event_data:
      parser_mediator.ProduceEventData(self._event_data)
      self._event_data = None

  def _ParseHeaderLine(self, parser_mediator, structure):
    """Parse a header line.

    ['Logging started.', 'Version=', '17.0.2011.0627',
    [2013, 7, 25], 16, 3, 23, 291, 'StartLocalTime', '<detail>']

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    time_elements_structure = self._GetValueFromStructure(
        structure, 'header_date_time')

    detail = self._GetValueFromStructure(structure, 'detail')
    local_time_string = self._GetValueFromStructure(
        structure, 'local_time_string')
    log_start = self._GetValueFromStructure(structure, 'log_start')
    version_number = self._GetValueFromStructure(structure, 'version_number')
    version_string = self._GetValueFromStructure(structure, 'version_string')

    event_data = SkyDriveLogEventData()
    event_data.added_time = self._ParseHeaderTimeElements(
        time_elements_structure)
    # TODO: refactor detail to individual event data attributes.
    event_data.detail = '{0!s} {1!s} {2!s} {3!s} {4!s}'.format(
        log_start, version_string, version_number, local_time_string, detail)

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

  def _ParseLoglineVersion2(self, structure):
    """Parse a version 2 log line.

    Args:
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    detail = self._GetValueFromStructure(structure, 'detail', default_value='')
    detail = detail.strip()

    event_data = SkyDriveLogEventData()
    event_data.added_time = self._ParseTimeElementsVersion2(
        time_elements_structure)
    event_data.detail = detail
    event_data.log_level = self._GetValueFromStructure(structure, 'log_level')
    event_data.module = self._GetValueFromStructure(structure, 'module')
    event_data.source_code = self._GetValueFromStructure(
        structure, 'source_code')

    self._event_data = event_data

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
    if self._event_data and key in ('header_line_v2', 'log_line_v2'):
      parser_mediator.ProduceEventData(self._event_data)
      self._event_data = None

    if key == 'header_line_v2':
      self._ParseHeaderLine(parser_mediator, structure)

    elif key == 'log_line_v2':
      self._ParseLoglineVersion2(structure)

    elif key == 'successive_log_line_v2':
      detail = self._GetValueFromStructure(
          structure, 'detail', default_value='')
      detail = detail.strip()

      self._event_data.detail = ' '.join([self._event_data.detail, detail])

  def _ParseTimeElementsVersion2(self, time_elements_structure):
    """Parses date and time elements of a version 2 log line.

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
      structure = self._VerifyString(text_reader.lines)
    except errors.ParseError:
      return False

    time_elements_tuple = self._GetValueFromStructure(
        structure, 'header_date_time')

    try:
      dfdatetime_time_elements.TimeElementsInMilliseconds(
          time_elements_tuple=time_elements_tuple)
    except ValueError:
      return False

    return True


text_parser.TextLogParser.RegisterPlugins([
    SkyDriveLog1TextPlugin, SkyDriveLog2TextPlugin])
