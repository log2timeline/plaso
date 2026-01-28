# -*- coding: utf-8 -*-
"""Text parser plugin for Atlassian Confluence log files.

This is for the atlassian-confluence.log file, one of multiple log files
produced by a Confluence DC/Server installation.
"""

import re

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class AtlassianConfluenceEventData(events.EventData):
  """Confluence event data.

  Attributes:
    body (str): the freeform body of the log line.
    level (str): the logging level of the event.
    logger_class (str): the Confluence class responsible for logging.
    logger_method (str): name of the method within the class calling the logger.
    thread (str): the Confluence thread from which the log event originated.
    written_time (dfdatetime.DateTimeValues): entry written date and time.
  """

  DATA_TYPE = 'atlassian:confluence:line'

  def __init__(self):
    """Initializes event data."""
    super(AtlassianConfluenceEventData, self).__init__(data_type=self.DATA_TYPE)
    self.body = None
    self.level = None
    self.logger_class = None
    self.logger_method = None
    self.thread = None
    self.written_time = None


class AtlassianConfluenceTextPlugin(interface.TextPlugin):
  """Text parser plugin for Atlassian Confluence log files."""

  NAME = 'atlassian_confluence'
  DATA_FORMAT = 'Atlassian Confluence log file'

  ENCODING = 'utf-8'

  # Confluence log levels
  _CONFLUENCE_LEVELS = [
      'DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL']

  # Date and time format: 2022-07-12 01:08:59,489
  # Format: YYYY-MM-DD HH:MM:SS,mmm (comma-separated milliseconds)
  _DATE_TIME = (
      pyparsing.Word(pyparsing.nums, exact=4).set_results_name('year') +
      pyparsing.Suppress('-') +
      pyparsing.Word(pyparsing.nums, exact=2).set_results_name('month') +
      pyparsing.Suppress('-') +
      pyparsing.Word(pyparsing.nums, exact=2).set_results_name('day_of_month') +
      pyparsing.Word(pyparsing.nums, exact=2).set_results_name('hours') +
      pyparsing.Suppress(':') +
      pyparsing.Word(pyparsing.nums, exact=2).set_results_name('minutes') +
      pyparsing.Suppress(':') +
      pyparsing.Word(pyparsing.nums, exact=2).set_results_name('seconds') +
      pyparsing.Suppress(',') +
      pyparsing.Word(pyparsing.nums, exact=3).set_results_name('milliseconds')
  ).set_results_name('date_time')

  # Log level (DEBUG, INFO, WARN, ERROR, FATAL)
  _LOG_LEVEL = pyparsing.oneOf(_CONFLUENCE_LEVELS).set_results_name('level')

  # Thread name enclosed in brackets: [Catalina-utility-1] or [hz.confluence.event-3]
  # Allows alphanumerics, hyphens, underscores, dots, colons, and spaces
  _CONFLUENCE_THREAD = (
      pyparsing.Suppress('[') +
      pyparsing.Word(
          pyparsing.alphanums + '-_.:' + ' ').set_results_name('thread') +
      pyparsing.Suppress(']'))

  # Logger class name enclosed in brackets
  # [confluence.cluster.hazelcast.HazelcastClusterManager]
  _CONFLUENCE_LOGGER = (
      pyparsing.Suppress('[') +
      pyparsing.SkipTo(']').set_results_name('logger_class') +
      pyparsing.Suppress(']'))

  # Logger method name: startCluster, memberAdded, <init>, lambda$getCompletedStatuses$0
  _CONFLUENCE_LOGGER_METHOD = (
      pyparsing.Word(
          pyparsing.alphanums + '_$<>').set_results_name('logger_method'))

  # Log message body - rest of line
  _CONFLUENCE_LOG_MESSAGE = pyparsing.SkipTo(
      pyparsing.LineEnd()).set_results_name('body')

  # Complete log line structure
  # Format: <timestamp> <level> [<thread>] [<logger_class>] <method> <message>
  _CONFLUENCE_LOG_LINE = (
      _DATE_TIME +
      _LOG_LEVEL +
      _CONFLUENCE_THREAD +
      _CONFLUENCE_LOGGER +
      _CONFLUENCE_LOGGER_METHOD +
      _CONFLUENCE_LOG_MESSAGE)

  _LINE_STRUCTURES = [('log_entry', _CONFLUENCE_LOG_LINE)]

  VERIFICATION_GRAMMAR = _CONFLUENCE_LOG_LINE

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
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    try:
      year = int(self._GetValueFromStructure(time_elements_structure, 'year'))
      month = int(self._GetValueFromStructure(time_elements_structure, 'month'))
      day = int(self._GetValueFromStructure(time_elements_structure, 'day_of_month'))
      hours = int(self._GetValueFromStructure(time_elements_structure, 'hours'))
      minutes = int(self._GetValueFromStructure(time_elements_structure, 'minutes'))
      seconds = int(self._GetValueFromStructure(time_elements_structure, 'seconds'))
      milliseconds = int(self._GetValueFromStructure(
          time_elements_structure, 'milliseconds'))

      date_time = dfdatetime_time_elements.TimeElementsInMilliseconds(
          time_elements_tuple=(
              year, month, day, hours, minutes, seconds, milliseconds))
      # Confluence logs use local server time, not UTC
      date_time.is_local_time = True
    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse time elements with error: {0!s}'.format(exception))

    event_data = AtlassianConfluenceEventData()
    event_data.body = self._GetValueFromStructure(
        structure, 'body', default_value='').strip() or None
    event_data.level = self._GetValueFromStructure(structure, 'level')
    event_data.logger_class = self._GetValueFromStructure(
        structure, 'logger_class')
    event_data.logger_method = self._GetValueFromStructure(
        structure, 'logger_method')
    event_data.thread = self._GetValueFromStructure(structure, 'thread')
    event_data.written_time = date_time

    parser_mediator.ProduceEventData(event_data)

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

    return 'date_time' in structure


text_parser.TextLogParser.RegisterPlugin(AtlassianConfluenceTextPlugin)