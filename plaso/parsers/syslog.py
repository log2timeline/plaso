# -*- coding: utf-8 -*-
"""Parser for syslog formatted log files"""
import re

import pyparsing

from plaso.containers import text_events
from plaso.lib import errors
from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import text_parser


class SyslogLineEvent(text_events.TextEvent):
  """Convenience class for a syslog line event."""
  DATA_TYPE = u'syslog:line'


class SyslogCommentEvent(text_events.TextEvent):
  """Convenience class for a syslog comment."""
  DATA_TYPE = u'syslog:comment'


class SyslogParser(text_parser.PyparsingMultiLineTextParser):
  """Parses syslog formatted log files"""
  NAME = u'syslog'

  DESCRIPTION = u'Syslog Parser'

  _VERIFICATION_REGEX = re.compile(r'^\w{3}\s+\d{1,2}\s\d{2}:\d{2}:\d{2}\s')

  _plugin_classes = {}

  _PYPARSING_COMPONENTS = {
      u'month': text_parser.PyparsingConstants.MONTH.setResultsName(u'month'),
      u'day': text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName(
          u'day'),
      u'hour': text_parser.PyparsingConstants.TWO_DIGITS.setResultsName(
          u'hour'),
      u'minute': text_parser.PyparsingConstants.TWO_DIGITS.setResultsName(
          u'minute'),
      u'second': text_parser.PyparsingConstants.TWO_DIGITS.setResultsName(
          u'second'),
      u'fractional_seconds': pyparsing.Word(pyparsing.nums).setResultsName(
          u'fractional_seconds'),
      u'hostname': pyparsing.Word(pyparsing.printables).setResultsName(
          u'hostname'),
      u'reporter': pyparsing.Word(pyparsing.alphanums + u'.').setResultsName(
          u'reporter'),
      u'pid': text_parser.PyparsingConstants.PID.setResultsName(u'pid'),
      u'facility': pyparsing.Word(pyparsing.alphanums).setResultsName(
          u'facility'),
      u'body': pyparsing.Regex(
          r'.*?(?=($|\n\w{3}\s+\d{1,2}\s\d{2}:\d{2}:\d{2}))', re.DOTALL).
               setResultsName(u'body'),
      u'comment_body': pyparsing.SkipTo(u' ---').setResultsName(
          u'body')
  }

  _PYPARSING_COMPONENTS[u'date'] = (
      _PYPARSING_COMPONENTS[u'month'] +
      _PYPARSING_COMPONENTS[u'day'] +
      _PYPARSING_COMPONENTS[u'hour'] + pyparsing.Suppress(u':') +
      _PYPARSING_COMPONENTS[u'minute'] + pyparsing.Suppress(u':') +
      _PYPARSING_COMPONENTS[u'second'] + pyparsing.Optional(
          pyparsing.Suppress(u'.') +
          _PYPARSING_COMPONENTS[u'fractional_seconds']))

  _SYSLOG_LINE = (
      _PYPARSING_COMPONENTS[u'date'] +
      _PYPARSING_COMPONENTS[u'hostname'] +
      _PYPARSING_COMPONENTS[u'reporter'] +
      pyparsing.Optional(
          pyparsing.Suppress(u'[') + _PYPARSING_COMPONENTS[u'pid'] +
          pyparsing.Suppress(u']')) +
      pyparsing.Optional(
          pyparsing.Suppress(u'<') + _PYPARSING_COMPONENTS[u'facility'] +
          pyparsing.Suppress(u'>')) +
      pyparsing.Optional(pyparsing.Suppress(u':')) +
      _PYPARSING_COMPONENTS[u'body'] + pyparsing.lineEnd())

  _SYSLOG_COMMENT = (
      _PYPARSING_COMPONENTS[u'date'] + pyparsing.Suppress(u':') +
      pyparsing.Suppress(u'---') + _PYPARSING_COMPONENTS[u'comment_body'] +
      pyparsing.Suppress(u'---') + pyparsing.LineEnd())

  LINE_STRUCTURES = [
      (u'syslog_line', _SYSLOG_LINE),
      (u'syslog_comment', _SYSLOG_COMMENT)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in LINE_STRUCTURES])

  def __init__(self):
    """Initializes a parser object."""
    super(SyslogParser, self).__init__()
    self._last_month = 0
    self._maximum_year = 0
    self._plugin_objects_by_reporter = {}
    self._year_use = 0

  def _UpdateYear(self, parser_mediator, month):
    """Updates the year to use for events, based on last observed month.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      month: an integer containing the month observed by the parser, where
             January is 1.
    """
    if not self._year_use:
      self._year_use = parser_mediator.GetEstimatedYear()
    if not self._maximum_year:
      self._maximum_year = parser_mediator.GetLatestYear()

    if not self._last_month:
      self._last_month = month
      return

    # Some syslog daemons allow out-of-order sequences, so allow some leeway
    # to not cause Apr->May->Apr to cause the year to increment.
    # See http://bugzilla.adiscon.com/show_bug.cgi?id=527
    if self._last_month > (month + 1):
      if self._year_use != self._maximum_year:
        self._year_use += 1
    self._last_month = month

  def EnablePlugins(self, plugin_includes):
    """Enables parser plugins.

    Args:
      plugin_includes: a list of strings containing the names of the plugins
                       to enable, where None or an empty list represents all
                       plugins. Not that the default plugin is handled
                       separately.
    """
    super(SyslogParser, self).EnablePlugins(plugin_includes)

    self._plugin_objects_by_reporter = {}
    for plugin_object in self._plugin_objects:
      self._plugin_objects_by_reporter[plugin_object.REPORTER] = plugin_object

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a matching entry.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      key: a string containing the name of the parsed structure.
      structure: the elements parsed from the file (instance of
                 pyparsing.ParseResults).

    Raises:
      UnableToParseFile: if an unsupported key is provided.
    """
    if key not in self._SUPPORTED_KEYS:
      raise errors.UnableToParseFile(u'Unsupported key: {0:s}'.format(key))

    month = timelib.MONTH_DICT.get(structure.month.lower(), None)
    if not month:
      parser_mediator.ProduceParserError(
          u'Invalid month value: {0:s}'.format(month))
      return

    self._UpdateYear(parser_mediator, month)
    timestamp = timelib.Timestamp.FromTimeParts(
        year=self._year_use, month=month, day=structure.day,
        hour=structure.hour, minutes=structure.minute,
        seconds=structure.second, timezone=parser_mediator.timezone)

    if key == u'syslog_comment':
      comment_attributes = {u'body': structure.body}
      event = SyslogCommentEvent(timestamp, 0, comment_attributes)
      parser_mediator.ProduceEvent(event)
      return

    reporter = structure.reporter
    attributes = {
        u'hostname': structure.hostname,
        u'reporter': reporter,
        u'pid': structure.pid,
        u'body': structure.body}

    plugin_object = self._plugin_objects_by_reporter.get(reporter, None)
    if not plugin_object:
      event_object = SyslogLineEvent(timestamp, 0, attributes)
      parser_mediator.ProduceEvent(event_object)

    else:
      try:
        plugin_object.Process(parser_mediator, timestamp, attributes)

      except errors.WrongPlugin:
        event_object = SyslogLineEvent(timestamp, 0, attributes)
        parser_mediator.ProduceEvent(event_object)

  def VerifyStructure(self, parser_mediator, lines):
    """Verifies that this is a syslog-formatted file.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      lines: a buffer that contains content from the file.

    Returns:
      A boolean value to indicate that passed buffer appears to contain syslog
      content.
    """
    return re.match(self._VERIFICATION_REGEX, lines) is not None


manager.ParsersManager.RegisterParser(SyslogParser)
