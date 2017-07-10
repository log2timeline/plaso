# -*- coding: utf-8 -*-
"""Parser for syslog formatted log files"""
import re

import pyparsing

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import text_parser


class SyslogLineEventData(events.EventData):
  """Syslog line event data.

  Attributes:
    body (str): message body.
    hostname (str): hostname of the reporter.
    pid (str): process identifier of the reporter.
    reporter (str): reporter.
    severity (str): severity.
  """

  DATA_TYPE = u'syslog:line'

  def __init__(self, data_type=DATA_TYPE):
    """Initializes an event data attribute container.

    Args:
      data_type (Optional[str]): event data type indicator.
    """
    super(SyslogLineEventData, self).__init__(data_type=data_type)
    self.body = None
    self.hostname = None
    self.pid = None
    self.reporter = None
    self.severity = None


class SyslogCommentEventData(events.EventData):
  """Syslog comment event data.

  Attributes:
    body (str): message body.
  """

  DATA_TYPE = u'syslog:comment'

  def __init__(self):
    """Initializes event data."""
    super(SyslogCommentEventData, self).__init__(data_type=self.DATA_TYPE)
    self.body = None


class SyslogParser(text_parser.PyparsingMultiLineTextParser):
  """Parses syslog formatted log files"""
  NAME = u'syslog'

  DESCRIPTION = u'Syslog Parser'

  _ENCODING = u'utf-8'

  _plugin_classes = {}

  # The reporter and facility fields can contain any printable character, but
  # to allow for processing of syslog formats that delimit the reporter and
  # facility with printable characters, we remove certain common delimiters
  # from the set of printable characters.
  _REPORTER_CHARACTERS = u''.join(
      [c for c in pyparsing.printables if c not in [u':', u'[', u'<']])
  _FACILITY_CHARACTERS = u''.join(
      [c for c in pyparsing.printables if c not in [u':', u'>']])

  _SYSLOG_SEVERITY = [
      u'EMERG',
      u'ALERT',
      u'CRIT',
      u'ERR',
      u'WARNING',
      u'NOTICE',
      u'INFO',
      u'DEBUG']

  _OFFSET_PREFIX = [
      u'-',
      u'+']

  _BODY_CONTENT = (
      r'.*?(?=($|\n\w{3}\s+\d{1,2}\s\d{2}:\d{2}:\d{2})|' \
      r'($|\n\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}' \
      r'[\+|-]\d{2}:\d{2}\s))')

  _VERIFICATION_REGEX = re.compile(
      r'^\w{3}\s+\d{1,2}\s\d{2}:\d{2}:\d{2}\s' + _BODY_CONTENT)

  # The Chrome OS syslog messages are of a format begininng with an
  # ISO 8601 combined date and time expression with timezone designator:
  #   2016-10-25T12:37:23.297265-07:00
  #
  # This will then be followed by the SYSLOG Severity which will be one of:
  #   EMERG,ALERT,CRIT,ERR,WARNING,NOTICE,INFO,DEBUG
  #
  # 2016-10-25T12:37:23.297265-07:00 INFO
  _CHROMEOS_VERIFICATION_REGEX = re.compile(
      r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.'
      r'\d{6}[\+|-]\d{2}:\d{2}\s'
      r'(EMERG|ALERT|CRIT|ERR|WARNING|NOTICE|INFO|DEBUG)' + _BODY_CONTENT)

  _PYPARSING_COMPONENTS = {
      u'year': text_parser.PyparsingConstants.FOUR_DIGITS.setResultsName(
          u'year'),
      u'two_digit_month': (
          text_parser.PyparsingConstants.TWO_DIGITS.setResultsName(
              u'two_digit_month')),
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
      u'severity': pyparsing.oneOf(_SYSLOG_SEVERITY).setResultsName(
          u'severity'),
      u'body': pyparsing.Regex(_BODY_CONTENT, re.DOTALL).setResultsName(
          u'body'),
      u'comment_body': pyparsing.SkipTo(u' ---').setResultsName(
          u'body'),
      u'iso_8601_offset': (
          pyparsing.oneOf(_OFFSET_PREFIX) +
          text_parser.PyparsingConstants.TWO_DIGITS +
          pyparsing.Optional(
              pyparsing.Literal(u':') +
              text_parser.PyparsingConstants.TWO_DIGITS))
  }

  _PYPARSING_COMPONENTS[u'date'] = (
      _PYPARSING_COMPONENTS[u'month'] +
      _PYPARSING_COMPONENTS[u'day'] +
      _PYPARSING_COMPONENTS[u'hour'] + pyparsing.Suppress(u':') +
      _PYPARSING_COMPONENTS[u'minute'] + pyparsing.Suppress(u':') +
      _PYPARSING_COMPONENTS[u'second'] + pyparsing.Optional(
          pyparsing.Suppress(u'.') +
          _PYPARSING_COMPONENTS[u'fractional_seconds']))

  _PYPARSING_COMPONENTS[u'iso_8601_date'] = pyparsing.Combine(
      _PYPARSING_COMPONENTS[u'year'] + pyparsing.Literal(u'-') +
      _PYPARSING_COMPONENTS[u'two_digit_month'] + pyparsing.Literal(u'-') +
      _PYPARSING_COMPONENTS[u'day'] + pyparsing.Literal(u'T') +
      _PYPARSING_COMPONENTS[u'hour'] + pyparsing.Literal(u':') +
      _PYPARSING_COMPONENTS[u'minute'] + pyparsing.Literal(u':') +
      _PYPARSING_COMPONENTS[u'second'] + pyparsing.Literal(u'.') +
      _PYPARSING_COMPONENTS[u'fractional_seconds'] +
      _PYPARSING_COMPONENTS[u'iso_8601_offset'],
      joinString=u'', adjacent=True).setResultsName(u'iso_8601_date')

  _CHROMEOS_SYSLOG_LINE = (
      _PYPARSING_COMPONENTS[u'iso_8601_date'] +
      _PYPARSING_COMPONENTS[u'severity'] +
      _PYPARSING_COMPONENTS[u'reporter'] +
      pyparsing.Optional(pyparsing.Suppress(u':')) +
      pyparsing.Optional(
          pyparsing.Suppress(u'[') + _PYPARSING_COMPONENTS[u'pid'] +
          pyparsing.Suppress(u']')) +
      pyparsing.Optional(pyparsing.Suppress(u':')) +
      _PYPARSING_COMPONENTS[u'body'] + pyparsing.lineEnd())

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
      (u'syslog_comment', _SYSLOG_COMMENT),
      (u'chromeos_syslog_line', _CHROMEOS_SYSLOG_LINE)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in LINE_STRUCTURES])

  def __init__(self):
    """Initializes a parser."""
    super(SyslogParser, self).__init__()
    self._last_month = 0
    self._maximum_year = 0
    self._plugin_by_reporter = {}
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

    self._plugin_by_reporter = {}
    for plugin in self._plugins:
      self._plugin_by_reporter[plugin.REPORTER] = plugin

  def ParseRecord(self, mediator, key, structure):
    """Parses a matching entry.

    Args:
      mediator (ParserMediator): mediates the interactions between
          parsers and other components, such as storage and abort signals.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): elements parsed from the file.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in self._SUPPORTED_KEYS:
      raise errors.ParseError(
          u'Unable to parse record, unknown structure: {0:s}'.format(key))

    if key == u'chromeos_syslog_line':
      timestamp = timelib.Timestamp.FromTimeString(structure.iso_8601_date[0])
    else:
      month = timelib.MONTH_DICT.get(structure.month.lower(), None)
      if not month:
        mediator.ProduceParserError(u'Invalid month value: {0:s}'.format(month))
        return

      self._UpdateYear(mediator, month)
      timestamp = timelib.Timestamp.FromTimeParts(
          year=self._year_use, month=month, day=structure.day,
          hour=structure.hour, minutes=structure.minute,
          seconds=structure.second, timezone=mediator.timezone)

    plugin = None
    if key == u'syslog_comment':
      event_data = SyslogCommentEventData()
      event_data.body = structure.body
      # TODO: pass line number to offset or remove.
      event_data.offset = 0

    else:
      event_data = SyslogLineEventData()
      event_data.body = structure.body
      event_data.hostname = structure.hostname or None
      # TODO: pass line number to offset or remove.
      event_data.offset = 0
      event_data.pid = structure.pid
      event_data.reporter = structure.reporter
      event_data.severity = structure.severity

      plugin = self._plugin_by_reporter.get(structure.reporter, None)
      if plugin:
        attributes = {
            u'hostname': structure.hostname,
            u'severity': structure.severity,
            u'reporter': structure.reporter,
            u'pid': structure.pid,
            u'body': structure.body}

        try:
          # TODO: pass event_data instead of attributes.
          plugin.Process(mediator, timestamp, attributes)

        except errors.WrongPlugin:
          plugin = None

    if not plugin:
      event = time_events.TimestampEvent(
          timestamp, definitions.TIME_DESCRIPTION_WRITTEN)
      mediator.ProduceEventWithEventData(event, event_data)

  def VerifyStructure(self, unused_mediator, line):
    """Verifies that this is a syslog-formatted file.

    Args:
      mediator (ParserMediator): mediates the interactions between
          parsers and other components, such as storage and abort signals.
      line (str): single line from the text file.

    Returns:
      bool: whether the line appears to contain syslog content.
    """
    return (re.match(self._VERIFICATION_REGEX, line) or
            re.match(self._CHROMEOS_VERIFICATION_REGEX, line)) is not None


manager.ParsersManager.RegisterParser(SyslogParser)
