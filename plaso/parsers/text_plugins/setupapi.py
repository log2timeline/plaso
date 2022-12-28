# -*- coding: utf-8 -*-
"""Text parser plugin for Windows SetupAPI log files.

Also see:
  https://learn.microsoft.com/en-us/windows-hardware/drivers/install/setupapi-text-logs
"""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class SetupAPILogEventData(events.EventData):
  """SetupAPI log event data.

  Attributes:
    end_time (dfdatetime.DateTimeValues): date and time the end of the log
        entry was added.
    entry_type (str): log entry type, for examaple "Device Install -
        PCI\\VEN_104C&DEV_8019&SUBSYS_8010104C&REV_00\\3&61aaa01&0&38" or
        "Sysprep Respecialize - {804b345a-ffd7-854c-a1b5-ca9598907846}".
    exit_status (str): the exit status of the logged operation.
    start_time (dfdatetime.DateTimeValues): date and time the start of
        the log entry was added.
  """

  DATA_TYPE = 'setupapi:log:line'

  def __init__(self):
    """Initializes event data."""
    super(SetupAPILogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.end_time = None
    self.entry_type = None
    self.exit_status = None
    self.start_time = None


class SetupAPILogTextPlugin(interface.TextPlugin):
  """Text parser plugin for Windows SetupAPI log files."""

  NAME = 'setupapi'
  DATA_FORMAT = 'Windows SetupAPI log file'

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _THREE_DIGITS = pyparsing.Word(pyparsing.nums, exact=3).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  # Date and time values are formatted as: 2015/11/22 17:59:28.110
  _DATE_TIME = (
      _FOUR_DIGITS + pyparsing.Suppress('/') +
      _TWO_DIGITS + pyparsing.Suppress('/') + _TWO_DIGITS +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') + _TWO_DIGITS +
      pyparsing.Word('.,', exact=1).suppress() + _THREE_DIGITS)

  # pylint: disable=line-too-long
  # See https://docs.microsoft.com/en-us/windows-hardware/drivers/install/format-of-a-text-log-header
  # pylint: enable=line-too-long
  _DEVICE_INSTALL_LOG_LINE = (
      pyparsing.Literal('[Device Install Log]') + _END_OF_LINE)

  # Using a regular expression here is faster. Note that pyparsing 2 does not
  # properly handle leading whitespace.
  _HEADER_ENTRY_LINE = pyparsing.Regex(
       r'(Architecture|OS Version|ProductType|Service Pack|Suite) = .*\n')

  _BEGIN_LOG_LINE = pyparsing.Literal('[BeginLog]') + _END_OF_LINE

  # pylint: disable=line-too-long
  # See https://docs.microsoft.com/en-us/windows-hardware/drivers/install/format-of-a-text-log-section-header
  # pylint: enable=line-too-long

  # Using a regular expression here is faster.
  _SECTION_HEADER_LINE = pyparsing.Regex(r'>>>  \[(?P<entry_type>[^\]]+)\]\n')

  # Using a regular expression here is faster.
  _SECTION_START_LINE = pyparsing.Regex(
      r'>>>  Section start (?P<start_time>[0-9]{4}/[0-9]{2}/[0-9]{2} '
      r'[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3})\n')

  # pylint: disable=line-too-long
  # See https://docs.microsoft.com/en-us/windows-hardware/drivers/install/format-of-a-text-log-section-footer
  # pylint: enable=line-too-long

  # Using a regular expression here is faster.
  _SECTION_END_LINE = pyparsing.Regex(
      r'<<<  Section end (?P<end_time>[0-9]{4}/[0-9]{2}/[0-9]{2} '
      r'[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3})\n')

  # Using a regular expression here is faster.
  _EXIT_STATUS_LINE = pyparsing.Regex(
      r'<<<  \[Exit status: (?P<exit_status>[^\]]+)\]\n')

  # pylint: disable=line-too-long
  # See https://learn.microsoft.com/en-us/windows-hardware/drivers/install/format-of-a-text-log-section-body
  # and https://docs.microsoft.com/en-us/windows-hardware/drivers/install/format-of-log-entries-that-are-not-part-of-a-text-log-section
  # pylint: enable=line-too-long

  # Note that undocumented event catagegories have been observed, such as:
  # "cmd:", "idb:" and "pol:".

  # Using a regular expression here is faster. Note that pyparsing 2 does not
  # properly handle leading whitespace.
  _LOG_ENTRY_LINE = pyparsing.Regex(
      r'(|\. |!    |!!!  )[A-Za-z\.]{2,3}: .{0,336}\n')

  # Undocumented observed lines.

  # Using a regular expression here is faster.
  _BOOT_SESSION_LINE = pyparsing.Regex(
      r'[Boot Session: [0-9]{4}/[0-9]{2}/[0-9]{2} '
      r'[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}]\n')

  _HEADER_GRAMMAR = (
      _DEVICE_INSTALL_LOG_LINE +
      pyparsing.OneOrMore(_HEADER_ENTRY_LINE) +
      _BEGIN_LOG_LINE)

  _LINE_STRUCTURES = [
      ('boot_session_line', _BOOT_SESSION_LINE),
      ('exit_status_line', _EXIT_STATUS_LINE),
      ('log_entry_line', _LOG_ENTRY_LINE),
      ('section_end_line', _SECTION_END_LINE),
      ('section_header_line', _SECTION_HEADER_LINE),
      ('section_start_line', _SECTION_START_LINE)]

  VERIFICATION_GRAMMAR = _DEVICE_INSTALL_LOG_LINE

  def __init__(self):
    """Initializes a text parser plugin."""
    super(SetupAPILogTextPlugin, self).__init__()
    self._event_data = None

  def _ParseHeader(self, parser_mediator, text_reader):
    """Parses a text-log file header.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.

    Raises:
      ParseError: when the header cannot be parsed.
    """
    try:
      structure_generator = self._HEADER_GRAMMAR.scanString(
          text_reader.lines, maxMatches=1)
      structure, start, end = next(structure_generator)

    except StopIteration:
      structure = None

    except pyparsing.ParseException as exception:
      raise errors.ParseError(exception)

    if not structure or start != 0:
      raise errors.ParseError('No match found.')

    text_reader.SkipAhead(end)

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
    if key == 'section_header_line':
      self._event_data = SetupAPILogEventData()
      self._event_data.entry_type = self._GetValueFromStructure(
          structure, 'entry_type')

    elif key == 'section_start_line':
      start_time_structure = self._GetValueFromStructure(
          structure, 'start_time')

      try:
        time_elements_structure = self._DATE_TIME.parseString(
            start_time_structure)
      except pyparsing.ParseException as exception:
        raise errors.ParseError(
            'Unable to parse start time with error: {0!s}'.format(exception))

      self._event_data.start_time = self._ParseTimeElements(
          time_elements_structure)

    elif key == 'section_end_line':
      end_time_structure = self._GetValueFromStructure(
          structure, 'end_time')

      try:
        time_elements_structure = self._DATE_TIME.parseString(
            end_time_structure)
      except pyparsing.ParseException as exception:
        raise errors.ParseError(
            'Unable to parse end time with error: {0!s}'.format(exception))

      self._event_data.end_time = self._ParseTimeElements(
          time_elements_structure)

    elif key == 'exit_status_line':
      self._event_data.exit_status = self._GetValueFromStructure(
          structure, 'exit_status')

      parser_mediator.ProduceEventData(self._event_data)

      self._ResetState()

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
      (year, month, day_of_month, hours, minutes, seconds, milliseconds) = (
          time_elements_structure)

      # Ensure time_elements_tuple is not a pyparsing.ParseResults otherwise
      # copy.deepcopy() of the dfDateTime object will fail on Python 3.8 with:
      # "TypeError: 'str' object is not callable" due to pyparsing.ParseResults
      # overriding __getattr__ with a function that returns an empty string
      # when named token does not exist.
      time_elements_tuple = (
          year, month, day_of_month, hours, minutes, seconds, milliseconds)

      date_time = dfdatetime_time_elements.TimeElementsInMilliseconds(
          time_elements_tuple=time_elements_tuple)

      # SetupAPI logs store date and time values in local time.
      date_time.is_local_time = True

      return date_time

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
      self._VerifyString(text_reader.lines)
    except errors.ParseError:
      return False

    self._ResetState()

    return True


text_parser.TextLogParser.RegisterPlugin(SetupAPILogTextPlugin)
