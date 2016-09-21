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

  _ENCODING = u'utf-8'

  _VERIFICATION_REGEX = re.compile(r'^\w{3}\s+\d{1,2}\s\d{2}:\d{2}:\d{2}\s')

  _plugin_classes = {}

  # The reporter and facility fields can contain any printable character, but
  # to allow for processing of syslog formats that delimit the reporter and
  # facility with printable characters, we remove certain common delimiters
  # from the set of printable characters.
  _REPORTER_CHARACTERS = u''.join(
      [c for c in pyparsing.printables if c not in [u':', u'[', u'<']])
  _FACILITY_CHARACTERS = u''.join(
      [c for c in pyparsing.printables if c not in [u':', u'>']])

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
      u'reporter': pyparsing.Word(_REPORTER_CHARACTERS).setResultsName(
          u'reporter'),
      u'pid': text_parser.PyparsingConstants.PID.setResultsName(u'pid'),
      u'facility': pyparsing.Word(_FACILITY_CHARACTERS).setResultsName(
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

  _KERNEL_SYSLOG_LINE = (
      _PYPARSING_COMPONENTS[u'date'] +
      pyparsing.Literal(u'kernel').setResultsName(u'reporter') +
      pyparsing.Suppress(u':') + _PYPARSING_COMPONENTS[u'body'] +
      pyparsing.lineEnd())

  LINE_STRUCTURES = [
      (u'syslog_line', _SYSLOG_LINE),
      (u'syslog_line', _KERNEL_SYSLOG_LINE),
      (u'syslog_comment', _SYSLOG_COMMENT)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in LINE_STRUCTURES])

  def __init__(self):
    """Initializes a parser object."""
    super(SyslogParser, self).__init__()
    self._last_month = 0
    self._maximum_year = 0
    self._plugin_objects_by_reporter = {}
    self._year_use = 0

  def _UpdateYear(self, mediator, month):
    """Updates the year to use for events, based on last observed month.

    Args:
      mediator (ParserMediator): mediates the interactions between
          parsers and other components, such as storage and abort signals.
      month (int): month observed by the parser, where January is 1.
    """
    if not self._year_use:
      self._year_use = mediator.GetEstimatedYear()
    if not self._maximum_year:
      self._maximum_year = mediator.GetLatestYear()

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
      plugin_includes (list[str]): names of the plugins to enable, where None
          or an empty list represents all plugins. Note that the default plugin
          is handled separately.
    """
    super(SyslogParser, self).EnablePlugins(plugin_includes)

    self._plugin_objects_by_reporter = {}
    for plugin_object in self._plugin_objects:
      self._plugin_objects_by_reporter[plugin_object.REPORTER] = plugin_object

  def ParseRecord(self, mediator, key, structure):
    """Parses a matching entry.

    Args:
      mediator (ParserMediator): mediates the interactions between
          parsers and other components, such as storage and abort signals.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): elements parsed from the file.

    Raises:
      UnableToParseFile: if an unsupported key is provided.
    """
    if key not in self._SUPPORTED_KEYS:
      raise errors.UnableToParseFile(u'Unsupported key: {0:s}'.format(key))

    month = timelib.MONTH_DICT.get(structure.month.lower(), None)
    if not month:
      mediator.ProduceParserError(
          u'Invalid month value: {0:s}'.format(month))
      return

    self._UpdateYear(mediator, month)
    timestamp = timelib.Timestamp.FromTimeParts(
        year=self._year_use, month=month, day=structure.day,
        hour=structure.hour, minutes=structure.minute,
        seconds=structure.second, timezone=mediator.timezone)

    if key == u'syslog_comment':
      comment_attributes = {u'body': structure.body}
      event = SyslogCommentEvent(timestamp, 0, comment_attributes)
      mediator.ProduceEvent(event)
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
      mediator.ProduceEvent(event_object)

    else:
      try:
        plugin_object.Process(mediator, timestamp, attributes)

      except errors.WrongPlugin:
        event_object = SyslogLineEvent(timestamp, 0, attributes)
        mediator.ProduceEvent(event_object)

  def VerifyStructure(self, unused_mediator, line):
    """Verifies that this is a syslog-formatted file.

    Args:
      mediator (ParserMediator): mediates the interactions between
          parsers and other components, such as storage and abort signals.
      line (str): single line from the text file.

    Returns:
      bool: whether the line appears to contain syslog content.
    """
    return re.match(self._VERIFICATION_REGEX, line) is not None


manager.ParsersManager.RegisterParser(SyslogParser)
