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

  # TODO: remove after refactoring.
  _SINGLE_LINE_MODE = True

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      text_parser.PyParseIntCast)

  _THREE_DIGITS = pyparsing.Word(pyparsing.nums, exact=3).setParseAction(
      text_parser.PyParseIntCast)

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      text_parser.PyParseIntCast)

  # Date and time values are formatted as: 2015/11/22 17:59:28.110
  _DATE_TIME = pyparsing.Group(
      _FOUR_DIGITS + pyparsing.Suppress('/') +
      _TWO_DIGITS + pyparsing.Suppress('/') + _TWO_DIGITS +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') + _TWO_DIGITS +
      pyparsing.Word('.,', exact=1).suppress() + _THREE_DIGITS)

  # Disable pylint due to long URLs for documenting structures.
  # pylint: disable=line-too-long

  # See https://docs.microsoft.com/en-us/windows-hardware/drivers/install/format-of-a-text-log-header
  _LOG_HEADER_START = (
      pyparsing.Literal('[Device Install Log]') + pyparsing.lineEnd())

  # See https://docs.microsoft.com/en-us/windows-hardware/drivers/install/format-of-a-text-log-header
  _LOG_HEADER_END = (
      pyparsing.Literal('[BeginLog]') + pyparsing.lineEnd())

  # See https://docs.microsoft.com/en-us/windows-hardware/drivers/install/format-of-a-text-log-section-header
  _SECTION_HEADER = (
      pyparsing.Suppress('>>>  [') +
      pyparsing.CharsNotIn(']').setResultsName('entry_type') +
      pyparsing.Literal(']') + pyparsing.lineEnd())

  # See https://docs.microsoft.com/en-us/windows-hardware/drivers/install/format-of-a-text-log-section-header
  _SECTION_HEADER_START = (
      pyparsing.Suppress('>>>  Section start') +
      _DATE_TIME.setResultsName('start_time') +
      pyparsing.lineEnd())

  # See https://docs.microsoft.com/en-us/windows-hardware/drivers/install/format-of-a-text-log-section-footer
  _SECTION_END = (
      pyparsing.Suppress('<<<  Section end ') +
      _DATE_TIME.setResultsName('end_time') +
      pyparsing.lineEnd())

  # See https://docs.microsoft.com/en-us/windows-hardware/drivers/install/format-of-a-text-log-section-footer
  _SECTION_END_EXIT_STATUS = (
      pyparsing.Suppress('<<<  [Exit status: ') +
      pyparsing.CharsNotIn(']').setResultsName('exit_status') +
      pyparsing.Literal(']') +
      pyparsing.lineEnd())

  # See https://docs.microsoft.com/en-us/windows-hardware/drivers/install/format-of-log-entries-that-are-not-part-of-a-text-log-section
  _SECTION_BODY_LINE = (
      pyparsing.stringStart +
      pyparsing.MatchFirst([
          pyparsing.Literal('!!!  '),
          pyparsing.Literal('!    '),
          pyparsing.Literal('     ')]) +
      pyparsing.restOfLine).leaveWhitespace()

  # See https://docs.microsoft.com/en-us/windows-hardware/drivers/install/format-of-log-entries-that-are-not-part-of-a-text-log-section
  _NON_SECTION_LINE = (
      pyparsing.stringStart +
      pyparsing.MatchFirst([
          pyparsing.Literal('   . '),
          pyparsing.Literal('!!!  '),
          pyparsing.Literal('!    '),
          pyparsing.Literal('     ')]) +
      pyparsing.restOfLine).leaveWhitespace()

  # These lines do not appear to be documented in the Microsoft documentation.
  _BOOT_SESSION_LINE = (
      pyparsing.Literal('[Boot Session:') +
      _DATE_TIME +
      pyparsing.Literal(']'))

  # pylint: enable=line-too-long

  _LINE_STRUCTURES = [
      ('ignorable_line', _BOOT_SESSION_LINE),
      ('ignorable_line', _LOG_HEADER_END),
      ('ignorable_line', _LOG_HEADER_START),
      ('ignorable_line', _NON_SECTION_LINE),
      ('ignorable_line', _SECTION_BODY_LINE),
      ('section_end', _SECTION_END),
      ('section_end_exit_status', _SECTION_END_EXIT_STATUS),
      ('section_header', _SECTION_HEADER),
      ('section_start', _SECTION_HEADER_START)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in _LINE_STRUCTURES])

  def __init__(self):
    """Initializes a text parser plugin."""
    super(SetupAPILogTextPlugin, self).__init__()
    self._event_data = None

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

    if key == 'ignorable_line':
      return

    if key == 'section_header':
      self._event_data = SetupAPILogEventData()
      self._event_data.entry_type = self._GetValueFromStructure(
          structure, 'entry_type')

    elif key == 'section_start':
      time_elements_structure = self._GetValueFromStructure(
          structure, 'start_time')

      self._event_data.start_time = self._ParseTimeElements(
          time_elements_structure)

    elif key == 'section_end':
      time_elements_structure = self._GetValueFromStructure(
          structure, 'end_time')

      self._event_data.end_time = self._ParseTimeElements(
          time_elements_structure)

    elif key == 'section_end_exit_status':
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
    line = text_reader.ReadLine()

    try:
      parsed_structure = self._LOG_HEADER_START.parseString(line)
    except pyparsing.ParseException:
      return False

    self._ResetState()

    return bool(parsed_structure)


text_parser.SingleLineTextParser.RegisterPlugin(SetupAPILogTextPlugin)
