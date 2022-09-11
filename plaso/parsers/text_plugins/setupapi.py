# -*- coding: utf-8 -*-
"""Text parser plugin for Windows SetupAPI log files.

The format is documented at:
https://docs.microsoft.com/en-us/windows-hardware/drivers/install/setupapi-text-logs
"""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class SetupAPILogEventData(events.EventData):
  """SetupAPI log event data.

  Attributes:
    entry_type (str): log entry type, for examaple "Device Install -
        PCI\\VEN_104C&DEV_8019&SUBSYS_8010104C&REV_00\\3&61aaa01&0&38" or
        "Sysprep Respecialize - {804b345a-ffd7-854c-a1b5-ca9598907846}".
    exit_status (str): the exit status of the logged operation.
  """

  DATA_TYPE = 'setupapi:log:line'

  def __init__(self):
    """Initializes event data."""
    super(SetupAPILogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.entry_type = None
    self.exit_status = None


class SetupAPILogTextPlugin(interface.TextPlugin):
  """Text parser plugin for Windows SetupAPI log files."""

  NAME = 'setupapi'
  DATA_FORMAT = 'Windows SetupAPI log file'

  _SLASH = pyparsing.Literal('/').suppress()

  _FOUR_DIGITS = text_parser.PyparsingConstants.FOUR_DIGITS
  _THREE_DIGITS = text_parser.PyparsingConstants.THREE_DIGITS
  _TWO_DIGITS = text_parser.PyparsingConstants.TWO_DIGITS

  _SETUPAPI_DATE_TIME = pyparsing.Group(
      _FOUR_DIGITS + _SLASH +
      _TWO_DIGITS + _SLASH +
      _TWO_DIGITS +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS +
      pyparsing.Word('.,', exact=1).suppress() +
      _THREE_DIGITS)

  # Disable pylint due to long URLs for documenting structures.
  # pylint: disable=line-too-long

  # See https://docs.microsoft.com/en-us/windows-hardware/drivers/install/format-of-a-text-log-header
  _LOG_HEADER_START = (
      pyparsing.Literal('[Device Install Log]') +
      pyparsing.lineEnd())

  # See https://docs.microsoft.com/en-us/windows-hardware/drivers/install/format-of-a-text-log-header
  _LOG_HEADER_END = (
      pyparsing.Literal('[BeginLog]') +
      pyparsing.lineEnd())

  # See https://docs.microsoft.com/en-us/windows-hardware/drivers/install/format-of-a-text-log-section-header
  _SECTION_HEADER = (
      pyparsing.Literal('>>>  [').suppress() +
      pyparsing.CharsNotIn(']').setResultsName('entry_type') +
      pyparsing.Literal(']') +
      pyparsing.lineEnd())

  # See https://docs.microsoft.com/en-us/windows-hardware/drivers/install/format-of-a-text-log-section-header
  _SECTION_HEADER_START = (
      pyparsing.Literal('>>>  Section start').suppress() +
      _SETUPAPI_DATE_TIME.setResultsName('start_time') +
      pyparsing.lineEnd())

  # See https://docs.microsoft.com/en-us/windows-hardware/drivers/install/format-of-a-text-log-section-footer
  _SECTION_END = (
      pyparsing.Literal('<<<  Section end ').suppress() +
      _SETUPAPI_DATE_TIME.setResultsName('end_time') +
      pyparsing.lineEnd())

  # See https://docs.microsoft.com/en-us/windows-hardware/drivers/install/format-of-a-text-log-section-footer
  _SECTION_END_EXIT_STATUS = (
      pyparsing.Literal('<<<  [Exit status: ').suppress() +
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
      _SETUPAPI_DATE_TIME +
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

  def __init__(self):
    """Initializes a text parser plugin."""
    super(SetupAPILogTextPlugin, self).__init__()
    self._last_end_time = None
    self._last_entry_type = None

  def _GetTimeElements(self, time_structure):
    """Builds time elements from a SetupAPI time_stamp field.

    Args:
      time_structure (pyparsing.ParseResults): structure of tokens derived from
          a SetupAPI time_stamp field.

    Returns:
      dfdatetime.TimeElements: date and time extracted from the value or None
          if the structure does not represent a valid date and time value.
    """
    try:
      date_time = dfdatetime_time_elements.TimeElementsInMilliseconds(
          time_elements_tuple=time_structure)
      # SetupAPI logs store date and time values in local time.
      date_time.is_local_time = True
      return date_time

    except ValueError:
      return None

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
    if key == 'ignorable_line':
      return

    if key == 'section_header':
      self._last_entry_type = self._GetValueFromStructure(
          structure, 'entry_type')
      return

    if key == 'section_start':
      time_structure = self._GetValueFromStructure(structure, 'start_time')
      start_time = self._GetTimeElements(time_structure)
      if not start_time:
        parser_mediator.ProduceExtractionWarning(
            'invalid date time value: {0!s}'.format(time_structure))
        return

      event_data = SetupAPILogEventData()
      event_data.entry_type = self._last_entry_type

      event = time_events.DateTimeValuesEvent(
          start_time, definitions.TIME_DESCRIPTION_START,
          time_zone=parser_mediator.timezone)

      # Create event for the start of the SetupAPI section
      parser_mediator.ProduceEventWithEventData(event, event_data)
      return

    if key == 'section_end':
      time_structure = self._GetValueFromStructure(structure, 'end_time')
      end_time = self._GetTimeElements(time_structure)
      if not end_time:
        parser_mediator.ProduceExtractionWarning(
            'invalid date time value: {0!s}'.format(time_structure))
      # Store last end time so that an event with the data from the
      # following exit status section can be created.
      self._last_end_time = end_time
      return

    if key == 'section_end_exit_status':
      exit_status = self._GetValueFromStructure(
          structure, 'exit_status')
      if self._last_end_time:
        event_data = SetupAPILogEventData()
        event_data.entry_type = self._last_entry_type
        event_data.exit_status = exit_status
        event = time_events.DateTimeValuesEvent(
            self._last_end_time, definitions.TIME_DESCRIPTION_END,
            time_zone=parser_mediator.timezone)
        parser_mediator.ProduceEventWithEventData(event, event_data)
        # Reset entry type and status and end time in case a line is missing.
        self._last_entry_type = None
        self._last_end_time = None
        return

    raise errors.ParseError(
        'Unable to parse record, unknown structure: {0:s}'.format(key))

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

    # Reset stored values for parsing a new file.
    self._last_end_time = None
    self._last_entry_type = None

    try:
      parsed_structure = self._LOG_HEADER_START.parseString(line)
    except pyparsing.ParseException:
      parsed_structure = None

    return bool(parsed_structure)


text_parser.SingleLineTextParser.RegisterPlugin(SetupAPILogTextPlugin)
