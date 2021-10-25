# -*- coding: utf-8 -*-
"""Parser for syslog formatted log files.

Also see:
* https://www.rsyslog.com/doc/v8-stable/configuration/templates.html
"""

import re

from dfdatetime import time_elements as dfdatetime_time_elements

import pyparsing

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import logger
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

  DATA_TYPE = 'syslog:line'

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

  DATA_TYPE = 'syslog:comment'

  def __init__(self):
    """Initializes event data."""
    super(SyslogCommentEventData, self).__init__(data_type=self.DATA_TYPE)
    self.body = None


class SyslogParser(text_parser.PyparsingMultiLineTextParser):
  """Parses syslog formatted log files"""

  NAME = 'syslog'
  DATA_FORMAT = 'System log (syslog) file'

  _ENCODING = 'utf-8'

  _plugin_classes = {}

  # The reporter and facility fields can contain any printable character, but
  # to allow for processing of syslog formats that delimit the reporter and
  # facility with printable characters, we remove certain common delimiters
  # from the set of printable characters.
  _REPORTER_CHARACTERS = ''.join(
      [c for c in pyparsing.printables if c not in [':', '[', '<']])
  _FACILITY_CHARACTERS = ''.join(
      [c for c in pyparsing.printables if c not in [':', '>']])

  _SYSLOG_SEVERITY = [
      'EMERG',
      'ALERT',
      'CRIT',
      'ERR',
      'WARNING',
      'NOTICE',
      'INFO',
      'DEBUG']

  # TODO: change pattern to allow only spaces as a field separator.
  _BODY_PATTERN = (
      r'.*?(?=($|\n\w{3}\s+\d{1,2}\s\d{2}:\d{2}:\d{2})|'
      r'($|\n\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}[\+|-]\d{2}:\d{2}\s)|'
      r'($|\n<\d{1,3}>1\s\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}[\+|-]\d{2}'
      r':\d{2}\s))')

  # The rsyslog file format (RSYSLOG_FileFormat) consists of:
  # %TIMESTAMP% %HOSTNAME% %syslogtag%%msg%
  #
  # Where %TIMESTAMP% is in RFC-3339 date time format e.g.
  # 2020-05-31T00:00:45.698463+00:00
  _RSYSLOG_VERIFICATION_PATTERN = (
      r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.'
      r'\d{6}[\+|-]\d{2}:\d{2} ' + _BODY_PATTERN)

  # The rsyslog traditional file format (RSYSLOG_TraditionalFileFormat)
  # consists of:
  # %TIMESTAMP% %HOSTNAME% %syslogtag%%msg%
  #
  # Where %TIMESTAMP% is in yearless ctime date time format e.g.
  # Jan 22 07:54:32
  # TODO: change pattern to allow only spaces as a field separator.
  _RSYSLOG_TRADITIONAL_VERIFICATION_PATTERN = (
      r'^\w{3}\s+\d{1,2}\s\d{2}:\d{2}:\d{2}\s' + _BODY_PATTERN)

  # The Chrome OS syslog messages are of a format beginning with an
  # ISO 8601 combined date and time expression with timezone designator:
  #   2016-10-25T12:37:23.297265-07:00
  #
  # This will then be followed by the SYSLOG Severity which will be one of:
  #   EMERG,ALERT,CRIT,ERR,WARNING,NOTICE,INFO,DEBUG
  #
  # 2016-10-25T12:37:23.297265-07:00 INFO
  _CHROMEOS_VERIFICATION_PATTERN = (
      r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.'
      r'\d{6}[\+|-]\d{2}:\d{2}\s'
      r'(EMERG|ALERT|CRIT|ERR|WARNING|NOTICE|INFO|DEBUG)' + _BODY_PATTERN)

  # The rsyslog protocol 23 format (RSYSLOG_SyslogProtocol23Format)
  # consists of:
  # %PRI%1 %TIMESTAMP% %HOSTNAME% %APP-NAME% %PROCID% %MSGID% %STRUCTURED-DATA%
  #   %msg%
  #
  # Where %TIMESTAMP% is in RFC-3339 date time format e.g.
  # 2020-05-31T00:00:45.698463+00:00
  _RSYSLOG_PROTOCOL_23_VERIFICATION_PATTERN = (
      r'^<\d{1,3}>1\s\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}[\+|-]\d{2}:'
      r'\d{2}\s' + _BODY_PATTERN)

  # Bundle all verification patterns into a single regular expression.
  _VERIFICATION_REGEX = re.compile('({0:s})'.format('|'.join([
      _CHROMEOS_VERIFICATION_PATTERN, _RSYSLOG_VERIFICATION_PATTERN,
      _RSYSLOG_TRADITIONAL_VERIFICATION_PATTERN,
      _RSYSLOG_PROTOCOL_23_VERIFICATION_PATTERN])))

  _PYPARSING_COMPONENTS = {
      'year': text_parser.PyparsingConstants.FOUR_DIGITS.setResultsName(
          'year'),
      'two_digit_month': (
          text_parser.PyparsingConstants.TWO_DIGITS.setResultsName(
              'two_digit_month')),
      'month': text_parser.PyparsingConstants.MONTH.setResultsName('month'),
      'day': text_parser.PyparsingConstants.ONE_OR_TWO_DIGITS.setResultsName(
          'day'),
      'hour': text_parser.PyparsingConstants.TWO_DIGITS.setResultsName(
          'hour'),
      'minute': text_parser.PyparsingConstants.TWO_DIGITS.setResultsName(
          'minute'),
      'second': text_parser.PyparsingConstants.TWO_DIGITS.setResultsName(
          'second'),
      'fractional_seconds': pyparsing.Word(pyparsing.nums).setResultsName(
          'fractional_seconds'),
      'hostname': pyparsing.Word(pyparsing.printables).setResultsName(
          'hostname'),
      'reporter': pyparsing.Word(_REPORTER_CHARACTERS).setResultsName(
          'reporter'),
      'pid': text_parser.PyparsingConstants.PID.setResultsName('pid'),
      'facility': pyparsing.Word(_FACILITY_CHARACTERS).setResultsName(
          'facility'),
      'severity': pyparsing.oneOf(_SYSLOG_SEVERITY).setResultsName('severity'),
      'body': pyparsing.Regex(_BODY_PATTERN, re.DOTALL).setResultsName('body'),
      'comment_body': pyparsing.SkipTo(' ---').setResultsName('body'),
      'priority': (
          text_parser.PyparsingConstants.ONE_TO_THREE_DIGITS.setResultsName(
              'priority')),
      'message_identifier': pyparsing.Word(pyparsing.printables).setResultsName(
          'message_identifier'),
      'structured_data': pyparsing.Word(pyparsing.printables).setResultsName(
          'structured_data'),
  }

  _PYPARSING_COMPONENTS['date'] = (
      _PYPARSING_COMPONENTS['month'] +
      _PYPARSING_COMPONENTS['day'] +
      _PYPARSING_COMPONENTS['hour'] + pyparsing.Suppress(':') +
      _PYPARSING_COMPONENTS['minute'] + pyparsing.Suppress(':') +
      _PYPARSING_COMPONENTS['second'] + pyparsing.Optional(
          pyparsing.Suppress('.') +
          _PYPARSING_COMPONENTS['fractional_seconds']))

  _PYPARSING_COMPONENTS['rfc3339_datetime'] = pyparsing.Combine(
      pyparsing.Word(pyparsing.nums, exact=4) + pyparsing.Literal('-') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal('-') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal('T') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal(':') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal(':') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal('.') +
      pyparsing.Word(pyparsing.nums, exact=6) + pyparsing.oneOf(['-', '+']) +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Optional(
          pyparsing.Literal(':') + pyparsing.Word(pyparsing.nums, exact=2)),
      joinString='', adjacent=True)

  _CHROMEOS_SYSLOG_LINE = (
      _PYPARSING_COMPONENTS['rfc3339_datetime'].setResultsName('datetime') +
      _PYPARSING_COMPONENTS['severity'] +
      _PYPARSING_COMPONENTS['reporter'] +
      pyparsing.Optional(pyparsing.Suppress(':')) +
      pyparsing.Optional(
          pyparsing.Suppress('[') + _PYPARSING_COMPONENTS['pid'] +
          pyparsing.Suppress(']')) +
      pyparsing.Optional(pyparsing.Suppress(':')) +
      _PYPARSING_COMPONENTS['body'] + pyparsing.lineEnd())

  _RSYSLOG_LINE = (
      _PYPARSING_COMPONENTS['rfc3339_datetime'].setResultsName('datetime') +
      _PYPARSING_COMPONENTS['hostname'] +
      _PYPARSING_COMPONENTS['reporter'] +
      pyparsing.Optional(
          pyparsing.Suppress('[') + _PYPARSING_COMPONENTS['pid'] +
          pyparsing.Suppress(']')) +
      pyparsing.Optional(
          pyparsing.Suppress('<') + _PYPARSING_COMPONENTS['facility'] +
          pyparsing.Suppress('>')) +
      pyparsing.Optional(pyparsing.Suppress(':')) +
      _PYPARSING_COMPONENTS['body'] + pyparsing.lineEnd())

  _RSYSLOG_TRADITIONAL_LINE = (
      _PYPARSING_COMPONENTS['date'] +
      _PYPARSING_COMPONENTS['hostname'] +
      _PYPARSING_COMPONENTS['reporter'] +
      pyparsing.Optional(
          pyparsing.Suppress('[') + _PYPARSING_COMPONENTS['pid'] +
          pyparsing.Suppress(']')) +
      pyparsing.Optional(
          pyparsing.Suppress('<') + _PYPARSING_COMPONENTS['facility'] +
          pyparsing.Suppress('>')) +
      pyparsing.Optional(pyparsing.Suppress(':')) +
      _PYPARSING_COMPONENTS['body'] + pyparsing.lineEnd())

  # TODO: Add proper support for %STRUCTURED-DATA%:
  # https://datatracker.ietf.org/doc/html/draft-ietf-syslog-protocol-23#section-6.3
  _RSYSLOG_PROTOCOL_23_LINE = (
      pyparsing.Suppress('<') + _PYPARSING_COMPONENTS['priority'] +
      pyparsing.Suppress('>') + pyparsing.Suppress(
          pyparsing.Word(pyparsing.nums, max=1)) +
      _PYPARSING_COMPONENTS['rfc3339_datetime'].setResultsName('datetime') +
      _PYPARSING_COMPONENTS['hostname'] +
      _PYPARSING_COMPONENTS['reporter'] +
      pyparsing.Or([pyparsing.Suppress('-'), _PYPARSING_COMPONENTS['pid']]) +
      _PYPARSING_COMPONENTS['message_identifier'] +
      _PYPARSING_COMPONENTS['structured_data'] +
      _PYPARSING_COMPONENTS['body'] +
      pyparsing.lineEnd())

  _SYSLOG_COMMENT = (
      _PYPARSING_COMPONENTS['date'] + pyparsing.Suppress(':') +
      pyparsing.Suppress('---') + _PYPARSING_COMPONENTS['comment_body'] +
      pyparsing.Suppress('---') + pyparsing.LineEnd())

  _KERNEL_SYSLOG_LINE = (
      _PYPARSING_COMPONENTS['date'] +
      pyparsing.Literal('kernel').setResultsName('reporter') +
      pyparsing.Suppress(':') + _PYPARSING_COMPONENTS['body'] +
      pyparsing.lineEnd())

  LINE_STRUCTURES = [
      ('chromeos_syslog_line', _CHROMEOS_SYSLOG_LINE),
      ('kernel_syslog_line', _KERNEL_SYSLOG_LINE),
      ('rsyslog_line', _RSYSLOG_LINE),
      ('rsyslog_traditional_line', _RSYSLOG_TRADITIONAL_LINE),
      ('rsyslog_protocol_23_line', _RSYSLOG_PROTOCOL_23_LINE),
      ('syslog_comment', _SYSLOG_COMMENT)]

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
      mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
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

  def _PriorityToSeverity(self, priority):
    """Converts a syslog protocol 23 priority value to severity,
    see https://datatracker.ietf.org/doc/html/draft-ietf-syslog-protocol-23

    Args:
      priority (int): a syslog protocol 23 priority value.

    Returns:
      str: the value from _SYSLOG_SEVERITY corresponding to severity value.
    """
    severity = self._SYSLOG_SEVERITY[priority % 8]
    return severity

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

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a matching entry.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): elements parsed from the file.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in self._SUPPORTED_KEYS:
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    if key in (
        'chromeos_syslog_line', 'rsyslog_line', 'rsyslog_protocol_23_line'):
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
      iso8601_string = self._GetValueFromStructure(structure, 'datetime')

      try:
        date_time.CopyFromStringISO8601(iso8601_string)
      except ValueError:
        parser_mediator.ProduceExtractionWarning(
            'invalid date time value: {0:s}'.format(iso8601_string))
        return

    else:
      # TODO: add support for fractional seconds.

      month = self._GetValueFromStructure(structure, 'month')
      try:
        month = self._MONTH_DICT.get(month.lower(), 0)
      except AttributeError:
        parser_mediator.ProduceExtractionWarning(
            'invalid month value: {0!s}'.format(month))
        return

      if month != 0:
        self._UpdateYear(parser_mediator, month)

      day = self._GetValueFromStructure(structure, 'day')
      hours = self._GetValueFromStructure(structure, 'hour')
      minutes = self._GetValueFromStructure(structure, 'minute')
      seconds = self._GetValueFromStructure(structure, 'second')

      time_elements_tuple = (
          self._year_use, month, day, hours, minutes, seconds)

      try:
        date_time = dfdatetime_time_elements.TimeElements(
            time_elements_tuple=time_elements_tuple)
        date_time.is_local_time = True
      except ValueError:
        parser_mediator.ProduceExtractionWarning(
            'invalid date time value: {0!s}'.format(time_elements_tuple))
        return

    plugin = None
    if key == 'syslog_comment':
      event_data = SyslogCommentEventData()
      event_data.body = self._GetValueFromStructure(structure, 'body')

    else:
      event_data = SyslogLineEventData()
      event_data.body = self._GetValueFromStructure(structure, 'body')
      event_data.hostname = self._GetValueFromStructure(structure, 'hostname')
      event_data.reporter = self._GetValueFromStructure(structure, 'reporter')
      event_data.pid = self._GetValueFromStructure(structure, 'pid')
      event_data.severity = self._GetValueFromStructure(structure, 'severity')

      if key == 'rsyslog_protocol_23_line':
        event_data.severity = self._PriorityToSeverity(
            self._GetValueFromStructure(structure, 'priority'))

      plugin = self._plugin_by_reporter.get(event_data.reporter, None)
      if plugin:
        attributes = {
            'body': event_data.body,
            'hostname': event_data.hostname,
            'pid': event_data.pid,
            'reporter': event_data.reporter,
            'severity': event_data.severity}

        file_entry = parser_mediator.GetFileEntry()
        display_name = parser_mediator.GetDisplayName(file_entry)

        logger.debug('Parsing file: {0:s} with plugin: {1:s}'.format(
            display_name, plugin.NAME))

        try:
          # TODO: pass event_data instead of attributes.
          plugin.Process(parser_mediator, date_time, attributes)

        except errors.WrongPlugin:
          plugin = None

    if not plugin:
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_WRITTEN,
          time_zone=parser_mediator.timezone)
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def VerifyStructure(self, parser_mediator, lines):
    """Verifies that this is a syslog-formatted file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between
          parsers and other components, such as storage and dfvfs.
      lines (str): one or more lines from the text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    return bool(self._VERIFICATION_REGEX.match(lines))


manager.ParsersManager.RegisterParser(SyslogParser)
