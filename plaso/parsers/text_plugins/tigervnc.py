# -*- coding: utf-8 -*-
"""Text parser plugin for TigerVNC log files."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class TigerVNCLogEventData(events.EventData):
  """TigerVNC log event data.

  Attributes:
    added_time (dfdatetime.DateTimeValues): date and time the log entry
        was added.
    component (str): name of the TigerVNC component.
    text (str): log message text.
  """

  DATA_TYPE = 'tigervnc:log'

  def __init__(self):
    """Initializes event data."""
    super(TigerVNCLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.added_time = None
    self.component = None
    self.text = None


class TigerVNCLogTextPlugin(interface.TextPluginWithLineContinuation):
  """Text parser plugin for TigerVNC log files."""

  NAME = 'tigervnc'
  DATA_FORMAT = 'TigerVNC log file'

  ENCODING = 'utf-8'

  _MONTH_DICT = {
      'jan': 1,
      'feb': 2,
      'mar': 3,
      'apr': 4,
      'may': 5,
      'jun': 6,
      'jul': 7,
      'aug': 8,
      'sep': 9,
      'oct': 10,
      'nov': 11,
      'dec': 12}

  _ONE_OR_TWO_DIGITS = pyparsing.Word(pyparsing.nums, max=2).set_parse_action(
      lambda tokens: int(tokens[0], 10))

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).set_parse_action(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).set_parse_action(
      lambda tokens: int(tokens[0], 10))

  _THREE_LETTERS = pyparsing.Word(pyparsing.alphas, exact=3)

  # Date and time values are formatted as: Sun Oct  2 10:30:45 2023
  # (ctime format)
  _DATE_TIME = pyparsing.Group(
      _THREE_LETTERS + _THREE_LETTERS + _ONE_OR_TWO_DIGITS +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') + _TWO_DIGITS +
      _FOUR_DIGITS)

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  # Timestamp line (just the date/time on its own line)
  _TIMESTAMP_LINE = (
      _DATE_TIME.set_results_name('date_time') +
      _END_OF_LINE)

  # Log entry line format: " component: message"
  _COMPONENT_CHARACTERS = pyparsing.alphanums + '_-'
  _LOG_ENTRY_LINE = (
      pyparsing.White(' ', exact=1) +
      pyparsing.Word(_COMPONENT_CHARACTERS).set_results_name('component') +
      pyparsing.Suppress(':') +
      pyparsing.Optional(pyparsing.White(' ', exact=1)) +
      pyparsing.Regex(r'[^\n]*').set_results_name('text') +
      _END_OF_LINE)

  _LINE_STRUCTURES = [
      ('timestamp_line', _TIMESTAMP_LINE),
      ('log_entry_line', _LOG_ENTRY_LINE)]

  VERIFICATION_GRAMMAR = _TIMESTAMP_LINE

  def __init__(self):
    """Initializes a text parser plugin."""
    super(TigerVNCLogTextPlugin, self).__init__()
    self._current_timestamp = None
    self._event_data = None
    self._text_lines = None

  def _ParseFinalize(self, parser_mediator):
    """Finalizes parsing.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
    """
    if self._event_data:
      self._event_data.text = ' '.join(self._text_lines)
      self._text_lines = []

      parser_mediator.ProduceEventData(self._event_data)
      self._event_data = None

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
    if key == 'timestamp_line':
      # Finalize any previous event before starting a new one
      if self._event_data:
        self._event_data.text = ' '.join(self._text_lines)
        parser_mediator.ProduceEventData(self._event_data)
        self._event_data = None
        self._text_lines = []

      # Store timestamp for the next log entry
      time_elements_structure = self._GetValueFromStructure(
          structure, 'date_time')
      self._current_timestamp = self._ParseTimeElements(
          time_elements_structure)

    elif key == 'log_entry_line':
      # Each log entry line starts a new event, finalize any previous event
      if self._event_data:
        self._event_data.text = ' '.join(self._text_lines)
        parser_mediator.ProduceEventData(self._event_data)

      # Create new event data
      component = self._GetStringValueFromStructure(structure, 'component')
      self._event_data = TigerVNCLogEventData()
      self._event_data.added_time = self._current_timestamp
      self._event_data.component = component
      self._text_lines = []

      # Add text to the current event
      text = self._GetStringValueFromStructure(structure, 'text')
      if text:
        self._text_lines.append(text)

    elif key == '_line_continuation':
      # Handle continuation lines (indented text)
      if self._event_data:
        text = structure.strip()
        if text:
          self._text_lines.append(text)

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
      _, month_string, day_of_month, hours, minutes, seconds, year = (
          time_elements_structure)

      month = self._MONTH_DICT.get(month_string.lower(), 0)

      time_elements_tuple = (year, month, day_of_month, hours, minutes, seconds)
      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)
      date_time.is_local_time = True

      return date_time

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse time elements with error: {0!s}'.format(exception))

  def _ResetState(self):
    """Resets stored values."""
    self._current_timestamp = None
    self._event_data = None
    self._text_lines = []

  def CheckRequiredFormat(self, parser_mediator, text_reader):
    """Check if the log record has the minimal structure required by the plugin.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.

    Returns:
      bool: True if this is the correct plugin, False otherwise.
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

    self._ResetState()

    return True


text_parser.TextLogParser.RegisterPlugin(TigerVNCLogTextPlugin)
