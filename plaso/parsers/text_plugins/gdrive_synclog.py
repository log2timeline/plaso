# -*- coding: utf-8 -*-
"""Text parser plugin for Google Drive Sync log files."""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class GoogleDriveSyncLogEventData(events.EventData):
  """Google Drive Sync log event data.

  Attributes:
    added_time (dfdatetime.DateTimeValues): date and time the log entry
        was added.
    level (str): logging level of event such as "DEBUG", "WARN", "INFO" and
        "ERROR".
    message (str): log message.
    process_identifier (int): process identifier of process which logged event.
    source_code (str): filename:line_number of source file which logged event.
    thread (str): colon-separated thread identifier in the form "ID:name"
        which logged event.
  """

  DATA_TYPE = 'google_drive_sync_log:entry'

  def __init__(self):
    """Initializes event data."""
    super(GoogleDriveSyncLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.added_time = None
    self.level = None
    self.message = None
    self.process_identifier = None
    self.source_code = None
    self.thread = None


class GoogleDriveSyncLogTextPlugin(interface.TextPlugin):
  """Text parser plugin for Google Drive Sync log files."""

  NAME = 'gdrive_synclog'
  DATA_FORMAT = 'Google Drive Sync log file'

  ENCODING = 'utf-8'

  _INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _THREE_DIGITS = pyparsing.Word(pyparsing.nums, exact=3).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FRACTION_OF_SECOND = pyparsing.Word('.,', exact=1).suppress() + _THREE_DIGITS

  _TIME_ZONE_OFFSET = pyparsing.Group(
      pyparsing.Word('+-', exact=1) + _TWO_DIGITS + _TWO_DIGITS)

  _DATE_TIME = pyparsing.Group(
      _FOUR_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress('-') + _TWO_DIGITS +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') + _TWO_DIGITS +
      _FRACTION_OF_SECOND + _TIME_ZONE_OFFSET).setResultsName('date_time')

  _PROCESS_IDENTIFIER = (
      pyparsing.Suppress('pid=') +
      _INTEGER.setResultsName('process_identifier'))

  _THREAD = pyparsing.Combine(
      pyparsing.Word(pyparsing.nums) + pyparsing.Literal(':') +
      pyparsing.Word(pyparsing.printables))

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _LOG_LINE_START = (
      _DATE_TIME +
      pyparsing.Word(pyparsing.alphas).setResultsName('level') +
      _PROCESS_IDENTIFIER +
      # TODO: consider stripping thread identifier/cleaning up thread name?
      _THREAD.setResultsName('thread') +
      pyparsing.Word(pyparsing.printables).setResultsName('source_code'))

  _LOG_LINE = (
      _LOG_LINE_START + pyparsing.restOfLine().setResultsName('body') +
      _END_OF_LINE)

  _SUCCESSIVE_LOG_LINE = (
      pyparsing.NotAny(_LOG_LINE_START) +
      pyparsing.restOfLine().setResultsName('body') + _END_OF_LINE)

  _LINE_STRUCTURES = [
      ('log_line', _LOG_LINE),
      ('successive_log_line', _SUCCESSIVE_LOG_LINE)]

  # Using a regular expression here is faster on non-match than the log line
  # grammar.
  VERIFICATION_GRAMMAR = pyparsing.Regex(
      r'(?P<date_time>[0-9]{4}-[0-9]{2}-[0-9]{2} '
      r'[0-9]{2}:[0-9]{2}:[0-9]{2}[,.][0-9]{3} [+-][0-9]{4}) '
      r'[A-Z]+ pid=[0-9]+ [0-9]+:\S+[ ]+\S+:[0-9]+ .*\n')

  VERIFICATION_LITERALS = [' ERROR ', ' FATAL ', ' INFO ', ' pid=', ' WARNING ']

  def __init__(self):
    """Initializes a text parser plugin."""
    super(GoogleDriveSyncLogTextPlugin, self).__init__()
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

    body = self._GetValueFromStructure(structure, 'body', default_value='')
    body = body.strip()

    event_data = GoogleDriveSyncLogEventData()
    event_data.added_time = self._ParseTimeElements(time_elements_structure)
    event_data.level = self._GetValueFromStructure(structure, 'level')
    event_data.process_identifier = self._GetValueFromStructure(
        structure, 'process_identifier')
    event_data.thread = self._GetValueFromStructure(structure, 'thread')
    event_data.source_code = self._GetValueFromStructure(
        structure, 'source_code')
    event_data.message = body

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

      self._event_data.message = ' '.join([self._event_data.message, body])

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
    # Ensure time_elements_tuple is not a pyparsing.ParseResults otherwise
    # copy.deepcopy() of the dfDateTime object will fail on Python 3.8 with:
    # "TypeError: 'str' object is not callable" due to pyparsing.ParseResults
    # overriding __getattr__ with a function that returns an empty string when
    # named token does not exist.
    try:
      (year, month, day_of_month, hours, minutes, seconds, milliseconds,
       time_zone_group) = time_elements_structure

      time_zone_sign, time_zone_hours, time_zone_minutes = time_zone_group

      time_elements_tuple = (
          year, month, day_of_month, hours, minutes, seconds, milliseconds)

      time_zone_offset = (time_zone_hours * 60) + time_zone_minutes
      if time_zone_sign == '-':
        time_zone_offset *= -1

      return dfdatetime_time_elements.TimeElementsInMilliseconds(
          time_elements_tuple=time_elements_tuple,
          time_zone_offset=time_zone_offset)

    except (TypeError, ValueError):
      return None

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

    date_time_structure = self._GetValueFromStructure(structure, 'date_time')

    time_elements_structure = self._DATE_TIME.parseString(date_time_structure)

    try:
      self._ParseTimeElements(time_elements_structure)
    except errors.ParseError:
      return False

    self._event_data = None

    return True


text_parser.TextLogParser.RegisterPlugin(GoogleDriveSyncLogTextPlugin)
