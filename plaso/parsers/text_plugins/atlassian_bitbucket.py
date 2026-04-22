# -*- coding: utf-8 -*-
"""Text parser plugin for Atlassian Bitbucket log files.

This is for the atlassian-bitbucket.log file, one of multiple log files
produced by a Bitbucket DC/Server installation.

Also see:
  https://support.atlassian.com/bitbucket-data-center/kb/how-to-read-the-bitbucket-data-center-log-formats/
"""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class AtlassianBitbucketEventData(events.EventData):
  """Bitbucket application log event data.

  Attributes:
    body (str): the freeform body of the log line.
    level (str): the logging level of the event.
    logger_class (str): the Bitbucket class responsible for logging.
    thread (str): the Bitbucket thread from which the log event originated.
    written_time (dfdatetime.DateTimeValues): entry written date and time.
  """

  DATA_TYPE = 'atlassian:bitbucket:line'

  def __init__(self):
    """Initializes event data."""
    super(AtlassianBitbucketEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.body = None
    self.level = None
    self.logger_class = None
    self.thread = None
    self.written_time = None


class AtlassianBitbucketTextPlugin(interface.TextPlugin):
  """Text parser plugin for Atlassian Bitbucket log files."""

  NAME = 'atlassian_bitbucket'
  DATA_FORMAT = 'Atlassian Bitbucket log file'

  ENCODING = 'utf-8'

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).set_parse_action(
      lambda tokens: int(tokens[0], 10))

  _THREE_DIGITS = pyparsing.Word(pyparsing.nums, exact=3).set_parse_action(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).set_parse_action(
      lambda tokens: int(tokens[0], 10))

  # Bitbucket log levels
  _BITBUCKET_LEVELS = ['DEBUG', 'ERROR', 'FATAL', 'INFO', 'TRACE', 'WARN']

  # Date and time format: 2020-09-08 07:53:45,084
  # Format: YYYY-MM-DD HH:MM:SS,mmm (comma-separated milliseconds)
  _DATE_TIME = (
      _FOUR_DIGITS + pyparsing.Suppress('-') + _TWO_DIGITS +
      pyparsing.Suppress('-') + _TWO_DIGITS + _TWO_DIGITS +
      pyparsing.Suppress(':') + _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(',') + _THREE_DIGITS).set_results_name(
          'date_time')

  # Log level (DEBUG, ERROR, FATAL, INFO, TRACE, WARN)
  _LOG_LEVEL = pyparsing.oneOf(_BITBUCKET_LEVELS).set_results_name('level')

  # Thread name enclosed in brackets, e.g. [http-nio-7990-exec-7],
  # [Caesium-1-4], [sshd-SshServer[1aa226b3](port=7999)-nio2-thread-3]
  # Use SkipTo to safely capture everything up to the closing bracket.
  _BITBUCKET_THREAD = (
      pyparsing.Suppress('[') +
      pyparsing.SkipTo(']').set_results_name('thread') +
      pyparsing.Suppress(']'))

  # Logger class name (abbreviated, e.g. c.a.b.i.boot.log.BuildInfoLogger)
  _BITBUCKET_LOGGER = (
      pyparsing.Word(
          pyparsing.alphanums + '._$').set_results_name('logger_class'))

  # Log message body - rest of line
  _BITBUCKET_LOG_MESSAGE = pyparsing.SkipTo(
      pyparsing.LineEnd()).set_results_name('body')

  # Complete log line structure:
  # <timestamp> <level> [<thread>] <logger_class> <message>
  _BITBUCKET_LOG_LINE = (
      _DATE_TIME + _LOG_LEVEL + _BITBUCKET_THREAD + _BITBUCKET_LOGGER +
      _BITBUCKET_LOG_MESSAGE)

  _LINE_STRUCTURES = [('log_entry', _BITBUCKET_LOG_LINE)]

  VERIFICATION_GRAMMAR = _BITBUCKET_LOG_LINE

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
    if key != 'log_entry':
      raise errors.ParseError(
          f'Unable to parse record, unknown structure: {key:s}')

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    event_data = AtlassianBitbucketEventData()
    event_data.body = self._GetValueFromStructure(
        structure, 'body', default_value='').strip() or None
    event_data.level = self._GetValueFromStructure(structure, 'level')
    event_data.logger_class = self._GetValueFromStructure(
        structure, 'logger_class')
    event_data.thread = self._GetValueFromStructure(structure, 'thread')
    event_data.written_time = self._ParseTimeElements(time_elements_structure)

    parser_mediator.ProduceEventData(event_data)

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
      date_time = dfdatetime_time_elements.TimeElementsInMilliseconds(
          time_elements_tuple=time_elements_structure)

      date_time.is_local_time = True

      return date_time

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          f'Unable to parse time elements with error: {exception!s}')

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

    return True


text_parser.TextLogParser.RegisterPlugin(AtlassianBitbucketTextPlugin)
