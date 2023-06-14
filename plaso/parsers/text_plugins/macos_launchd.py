# -*- coding: utf-8 -*-
"""Text parser plugin for MacOS launchd log files."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class MacOSLaunchdEventData(events.EventData):
  """MacOS launchd log event data.

  Attributes:
    body (str): Content of the log event.
    process_name (str): Name of the process that created the record.
    severity (str): severity of the message.
    written_time (dfdatetime.DateTimeValues): date and time the log entry was
        written.
  """

  DATA_TYPE = 'macos:launchd_log:entry'

  def __init__(self):
    """Initializes event data."""
    super(MacOSLaunchdEventData, self).__init__(data_type=self.DATA_TYPE)
    self.body = None
    self.process_name = None
    self.severity = None
    self.written_time = None


class MacOSLaunchdLogTextPlugin(interface.TextPlugin):
  """Text parser plugin for MacOS launchd log files."""

  NAME = 'macos_launchd_log'
  DATA_FORMAT = 'MacOS launchd log file'

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _SIX_DIGITS = pyparsing.Word(pyparsing.nums, exact=6).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _DATE_TIME = (
      _FOUR_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress('.') +
      _SIX_DIGITS)

  _PROCESS_NAME = (
      pyparsing.Suppress('(') +
      pyparsing.OneOrMore(
          pyparsing.Word(pyparsing.printables, excludeChars=')'), stop_on=')') +
      pyparsing.Suppress(')')).setParseAction(' '.join)

  _SEVERITY = pyparsing.Combine(
      pyparsing.Suppress('<') +
      pyparsing.Word(pyparsing.printables, excludeChars='>') +
      pyparsing.Suppress('>'))

  _LOG_LINE = (
    _DATE_TIME.setResultsName('date_time') +
    pyparsing.Optional(_PROCESS_NAME.setResultsName('process_name')) +
    _SEVERITY.setResultsName('severity') +
    pyparsing.Suppress(': ') +

    pyparsing.restOfLine().setResultsName('body') +
    pyparsing.Suppress(pyparsing.LineEnd()))

  _LINE_STRUCTURES = [('log_line', _LOG_LINE)]

  VERIFICATION_GRAMMAR = _LOG_LINE

  def __init__(self):
    """Initializes a text parser plugin."""
    super(MacOSLaunchdLogTextPlugin, self).__init__()
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

    event_data = MacOSLaunchdEventData()
    event_data.body = self._GetValueFromStructure(structure, 'body')
    event_data.process_name = self._GetValueFromStructure(
        structure, 'process_name')
    event_data.severity = self._GetValueFromStructure(structure, 'severity')
    event_data.written_time = (
        dfdatetime_time_elements.TimeElementsInMicroseconds(
            time_elements_tuple=time_elements_structure))

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
      dfdatetime_time_elements.TimeElementsInMicroseconds(
          time_elements_tuple=time_elements_structure)
    except errors.ParseError:
      return False

    self._event_data = None

    return True


text_parser.TextLogParser.RegisterPlugin(MacOSLaunchdLogTextPlugin)
