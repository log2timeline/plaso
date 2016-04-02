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
  NAME = u'new_syslog'

  DESCRIPTION = u'New Syslog Parser'

  _VERIFICATION_REGEX = re.compile(r'^\w{3}\s\d{2}\s\d{2}:\d{2}:\d{2}\s')

  _plugin_classes = {}
  _plugin_classes_by_reporter = None

  _pyparsing_components = {
    u'month': text_parser.PyparsingConstants.MONTH.setResultsName(u'month'),
    u'day': text_parser.PyparsingConstants.TWO_DIGITS.setResultsName(u'day'),
    u'hour': text_parser.PyparsingConstants.TWO_DIGITS.setResultsName(u'hour'),
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
        r'.*?(?=($|\n\w{3}\s\d{2}\s\d{2}:\d{2}:\d{2}))', re.DOTALL).
        setResultsName(u'body'),
    u'comment_body': pyparsing.SkipTo(u' ---').setResultsName(
        u'body')
  }
  _pyparsing_components[u'date'] = (
      _pyparsing_components[u'month'] +
      _pyparsing_components[u'day'] +
      _pyparsing_components[u'hour'] + pyparsing.Suppress(u':') +
      _pyparsing_components[u'minute'] + pyparsing.Suppress(u':') +
      _pyparsing_components[u'second'] + pyparsing.Optional(
          pyparsing.Suppress(u'.') +
          _pyparsing_components[u'fractional_seconds']))


  LINE_GRAMMAR = (
      _pyparsing_components[u'date'] +
      _pyparsing_components[u'hostname'] +
      _pyparsing_components[u'reporter'] +
      pyparsing.Optional(
          pyparsing.Suppress(u'[') + _pyparsing_components[u'pid'] +
          pyparsing.Suppress(u']')) +
      pyparsing.Optional(
          pyparsing.Suppress(u'<') + _pyparsing_components[u'facility'] +
          pyparsing.Suppress(u'>')) +
      pyparsing.Optional(pyparsing.Suppress(u':')) +
      _pyparsing_components[u'body'] + pyparsing.lineEnd())

  SYSLOG_COMMENT = (
      _pyparsing_components[u'date'] + pyparsing.Suppress(u':') +
      pyparsing.Suppress(u'---') + _pyparsing_components[u'comment_body'] +
      pyparsing.Suppress(u'---') + pyparsing.LineEnd())

  LINE_STRUCTURES = [
      (u'syslog_line', LINE_GRAMMAR),
      (u'syslog_comment', SYSLOG_COMMENT)]

  def __init__(self):
    """Initialize the parser."""
    super(SyslogParser, self).__init__()
    self._year_use = 0
    self._maximum_year = 0
    self._last_month = 0

  def _UpdateYear(self, parser_mediator, month):
    """Updates the year to use for events, based on last observed month.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      month: an integer containing the month observed by the parser.
    """
    if not self._year_use:
      self._year_use = parser_mediator.GetEstimatedYear()
    if not self._maximum_year:
      self._maximum_year = parser_mediator.GetMaximumYear()

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


  def _InitializePlugins(self):
    """ Initializes plugins prior to processing"""
    if not self._plugin_classes_by_reporter:
      self._plugin_classes_by_reporter = {}

    for plugin in self.GetPluginObjects():
      reporter = plugin.REPORTER
      self._plugin_classes_by_reporter[reporter] = plugin

  def VerifyStructure(self, parser_mediator, lines):
    """Verify that this is a syslog file.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      lines: a buffer that contains content from the file.

    Returns:
      True if the passed buffer appears to contain syslog content.
    """
    return re.match(self._VERIFICATION_REGEX, lines)

  def ParseRecord(self, parser_mediator, key, structure):
    """Parse a match.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      key: a string indicating the name of the parsed structure.
      structure: the elements parsed from the file (instance of
                 pyparsing.ParseResults).

    Raises:
      UnableToParseFile: if an unsupported key is provided.
    """
    if key not in [u'syslog_line', u'syslog_comment']:
      raise errors.UnableToParseFile(u'Unsupported key {0:s}'.format(key))

    self._InitializePlugins()
    month = timelib.MONTH_DICT.get(structure.month.lower(), None)
    if not month:
      parser_mediator.ProduceParserError(u'Invalid month value: {0:s}'.format(
        month))
      return
    self._UpdateYear(parser_mediator, month)
    timestamp = timelib.Timestamp.FromTimeParts(
        year= self._year_use, month=month, day=structure.day,
        hour=structure.hour, minutes=structure.minute,
        seconds=structure.second)

    if key == u'syslog_comment':
      comment_attributes = {
          u'hostname': u'',
          u'reporter': u'',
          u'pid': u'',
          u'body': structure.body}
      event = SyslogCommentEvent(timestamp, 0, comment_attributes)
      parser_mediator.ProduceEvent(event)
      return

    attributes = {u'hostname': structure.hostname,
                  u'reporter': structure.reporter,
                  u'pid': structure.pid,
                  u'body': structure.body}

    plugin = self._plugin_classes_by_reporter.get(attributes[u'reporter'], None)
    if plugin:
      try:
        plugin.UpdateChainAndProcess(
            parser_mediator, timestamp=timestamp, syslog_tokens=attributes)
      except errors.WrongPlugin:
        parser_mediator.ProduceEvent(SyslogLineEvent(timestamp, 0, attributes))
    else:
      parser_mediator.ProduceEvent(SyslogLineEvent(timestamp, 0, attributes))

manager.ParsersManager.RegisterParser(SyslogParser)
