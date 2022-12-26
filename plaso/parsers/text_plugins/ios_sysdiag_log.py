# -*- coding: utf-8 -*-
"""Text parser plugin for iOS sysdiag log files."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class IOSSysdiagLogEventData(events.EventData):
  """iOS sysdiagnose log event data.

  Attributes:
    body (str): body of the event line.
    originating_call (str): call that created the entry.
    process_identifier (str): process_identifier.
    severity (str): severity of the message.
    written_time (dfdatetime.DateTimeValues): date and time the log entry was
        written.
  """

  DATA_TYPE = 'ios:sysdiag_log:entry'

  def __init__(self):
    """Initializes event data."""
    super(IOSSysdiagLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.body = None
    self.originating_call = None
    self.process_identifier = None
    self.severity = None
    self.written_time = None


class IOSSysdiagLogTextPlugin(interface.TextPlugin):
  """Text parser plugin for iOS mobile installation log files."""

  NAME = 'ios_sysdiag_log'
  DATA_FORMAT = 'iOS sysdiag log'

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

  _INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _ONE_OR_TWO_DIGITS = pyparsing.Word(pyparsing.nums, max=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _THREE_LETTERS = pyparsing.Word(pyparsing.alphas, exact=3)

  # Date and time values are formatted as: Wed Aug 11 05:51:02 2021
  _DATE_TIME = (
      _THREE_LETTERS.suppress() +
      _THREE_LETTERS +
      _ONE_OR_TWO_DIGITS +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') + _TWO_DIGITS +
      _FOUR_DIGITS)

  _ORIGINATING_CALL = pyparsing.Combine(
      pyparsing.Optional(
          pyparsing.Word('+-', exact=1) + pyparsing.Literal('[') +
          pyparsing.CharsNotIn(']') + pyparsing.Literal(']')) +
      pyparsing.Optional(pyparsing.CharsNotIn(':')))

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _LOG_LINE_START = (
      _DATE_TIME.setResultsName('date_time') +
      pyparsing.Suppress('[') +
      _INTEGER.setResultsName('process_identifier') + pyparsing.Suppress(']') +
      pyparsing.Suppress('<') +
      pyparsing.Word(pyparsing.alphanums).setResultsName('severity') +
      pyparsing.Suppress('>') +
      pyparsing.Suppress('(') +
      pyparsing.Word(pyparsing.alphanums).setResultsName('id') +
      pyparsing.Suppress(')') +
      _ORIGINATING_CALL.setResultsName('originating_call') +
      pyparsing.Suppress(': '))

  _LOG_LINE = (
      _LOG_LINE_START + pyparsing.restOfLine().setResultsName('body') +
      _END_OF_LINE)

  _SUCCESSIVE_LOG_LINE = (
      pyparsing.NotAny(_LOG_LINE_START) +
      pyparsing.restOfLine().setResultsName('body') + _END_OF_LINE)

  _LINE_STRUCTURES = [
      ('log_line', _LOG_LINE),
      ('successive_log_line', _SUCCESSIVE_LOG_LINE)]

  VERIFICATION_GRAMMAR = _LOG_LINE

  def __init__(self):
    """Initializes a text parser plugin."""
    super(IOSSysdiagLogTextPlugin, self).__init__()
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

  def _ParseLogline(self, structure):
    """Parses a log line.

    Args:
      structure (pyparsing.ParseResults): structure of tokens derived from
          a line of a text file.
    """
    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    event_data = IOSSysdiagLogEventData()
    event_data.body = self._GetValueFromStructure(structure, 'body')
    event_data.originating_call = self._GetValueFromStructure(
        structure, 'originating_call')
    event_data.process_identifier = self._GetValueFromStructure(
        structure, 'process_identifier')
    event_data.severity = self._GetValueFromStructure(structure, 'severity')
    event_data.written_time = self._ParseTimeElements(time_elements_structure)

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
    if key == 'log_line':
      if self._event_data:
        parser_mediator.ProduceEventData(self._event_data)
        self._event_data = None

      self._ParseLogline(structure)

    elif key == 'successive_log_line':
      body = self._GetValueFromStructure(structure, 'body', default_value='')
      body = body.strip()

      self._event_data.body = ' '.join([self._event_data.body, body])

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
      month_string, day_of_month, hours, minutes, seconds, year = (
          time_elements_structure)

      month = self._MONTH_DICT.get(month_string.lower(), 0)

      time_elements_tuple = (year, month, day_of_month, hours, minutes, seconds)

      return dfdatetime_time_elements.TimeElements(
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

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    try:
      self._ParseTimeElements(time_elements_structure)
    except errors.ParseError:
      return False

    self._event_data = None

    return True


text_parser.TextLogParser.RegisterPlugin(IOSSysdiagLogTextPlugin)
