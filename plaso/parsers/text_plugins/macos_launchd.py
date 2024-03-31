# -*- coding: utf-8 -*-
"""Text parser plugin for Mac OS launchd log files."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class MacOSLaunchdEventData(events.EventData):
  """Mac OS launchd log event data.

  Attributes:
    body (str): content of the log event.
    process_name (str): name of the process that created the record.
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
  """Text parser plugin for Mac OS launchd log files."""

  NAME = 'macos_launchd_log'
  DATA_FORMAT = 'Mac OS launchd log file'

  # Date and time values are formatted as:
  # 2023-06-08 14:51:38.987368
  _DATE_TIME = pyparsing.Regex(
      r'(?P<date_time>[0-9]{4}-[0-9]{2}-[0-9]{2} '
      r'[0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{6}) ')

  _PROCESS_NAME = pyparsing.Regex(r'[(](?P<process_name>[^)]+)[)] ')

  _SEVERITY = pyparsing.Regex(r'[<](?P<severity>[^>]+)[>]: ')

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _LOG_LINE = (
      _DATE_TIME + pyparsing.Optional(_PROCESS_NAME) + _SEVERITY +
      pyparsing.restOfLine().set_results_name('body') + _END_OF_LINE)

  _LINE_STRUCTURES = [('log_line', _LOG_LINE)]

  VERIFICATION_GRAMMAR = _LOG_LINE

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
      time_elements_structure = self._GetValueFromStructure(
          structure, 'date_time')

      event_data = MacOSLaunchdEventData()
      event_data.body = self._GetValueFromStructure(structure, 'body')
      event_data.process_name = self._GetValueFromStructure(
          structure, 'process_name')
      event_data.severity = self._GetValueFromStructure(structure, 'severity')
      event_data.written_time = self._ParseTimeElements(time_elements_structure)

      parser_mediator.ProduceEventData(event_data)

  def _ParseTimeElements(self, time_elements_structure):
    """Parses date and time elements.

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
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
      date_time.CopyFromDateTimeString(time_elements_structure)

      return date_time

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          f'Unable to parse time elements with error: {exception!s}')

  def CheckRequiredFormat(self, parser_mediator, text_reader):
    """Check if the log record has the minimal structure required by the parser.

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

    return True


text_parser.TextLogParser.RegisterPlugin(MacOSLaunchdLogTextPlugin)
