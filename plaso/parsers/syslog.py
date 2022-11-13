# -*- coding: utf-8 -*-
"""Parser for syslog formatted log files.

Also see:
* https://www.rsyslog.com/doc/v8-stable/configuration/templates.html
"""

import re

from dfdatetime import time_elements as dfdatetime_time_elements

import pyparsing

from plaso.containers import events
from plaso.lib import errors
from plaso.lib import yearless_helper
from plaso.parsers import logger
from plaso.parsers import manager
from plaso.parsers import text_parser


class SyslogLineEventData(events.EventData):
  """Syslog line event data.

  Attributes:
    body (str): message body.
    hostname (str): hostname of the reporter.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
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
    self.last_written_time = None
    self.pid = None
    self.reporter = None
    self.severity = None


class SyslogCommentEventData(events.EventData):
  """Syslog comment event data.

  Attributes:
    body (str): message body.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
  """

  DATA_TYPE = 'syslog:comment'

  def __init__(self):
    """Initializes event data."""
    super(SyslogCommentEventData, self).__init__(data_type=self.DATA_TYPE)
    self.body = None
    self.last_written_time = None


class SyslogParser(
    text_parser.PyparsingMultiLineTextParser,
    yearless_helper.YearLessLogFormatHelper):
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

  _ONE_OR_TWO_DIGITS = pyparsing.Word(pyparsing.nums, max=2).setParseAction(
      text_parser.PyParseIntCast)

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      text_parser.PyParseIntCast)

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      text_parser.PyParseIntCast)

  _SIX_DIGITS = pyparsing.Word(pyparsing.nums, exact=6).setParseAction(
      text_parser.PyParseIntCast)

  _THREE_LETTERS = pyparsing.Word(pyparsing.alphas, exact=3)

  _DATE_TIME = (
      _THREE_LETTERS + _ONE_OR_TWO_DIGITS +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Optional(
          pyparsing.Suppress('.') +
          pyparsing.Word(pyparsing.nums)))

  _DATE_TIME_RFC3339 = (
      _FOUR_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress('-') +
      _TWO_DIGITS + pyparsing.Suppress('T') +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress(':') +
      _TWO_DIGITS + pyparsing.Suppress('.') +
      _SIX_DIGITS + pyparsing.Word('+-', exact=1) +
      _TWO_DIGITS + pyparsing.Optional(
          pyparsing.Suppress(':') + _TWO_DIGITS))

  _PROCESS_IDENTIFIER = pyparsing.Word(pyparsing.nums, max=5).setParseAction(
      text_parser.PyParseIntCast)

  _REPORTER = pyparsing.Word(_REPORTER_CHARACTERS)

  _CHROMEOS_SYSLOG_LINE = (
      _DATE_TIME_RFC3339.setResultsName('date_time') +
      pyparsing.oneOf(_SYSLOG_SEVERITY).setResultsName('severity') +
      _REPORTER.setResultsName('reporter') +
      pyparsing.Optional(pyparsing.Suppress(':')) +
      pyparsing.Optional(
          pyparsing.Suppress('[') + _PROCESS_IDENTIFIER.setResultsName('pid') +
          pyparsing.Suppress(']')) +
      pyparsing.Optional(pyparsing.Suppress(':')) +
      pyparsing.Regex(_BODY_PATTERN, re.DOTALL).setResultsName('body') +
      pyparsing.lineEnd())

  _RSYSLOG_LINE = (
      _DATE_TIME_RFC3339.setResultsName('date_time') +
      pyparsing.Word(pyparsing.printables).setResultsName('hostname') +
      _REPORTER.setResultsName('reporter') +
      pyparsing.Optional(
          pyparsing.Suppress('[') + _PROCESS_IDENTIFIER.setResultsName('pid') +
          pyparsing.Suppress(']')) +
      pyparsing.Optional(
          pyparsing.Suppress('<') +
          pyparsing.Word(_FACILITY_CHARACTERS).setResultsName('facility') +
          pyparsing.Suppress('>')) +
      pyparsing.Optional(pyparsing.Suppress(':')) +
      pyparsing.Regex(_BODY_PATTERN, re.DOTALL).setResultsName('body') +
      pyparsing.lineEnd())

  _RSYSLOG_TRADITIONAL_LINE = (
      _DATE_TIME.setResultsName('date_time') +
      pyparsing.Word(pyparsing.printables).setResultsName('hostname') +
      _REPORTER.setResultsName('reporter') +
      pyparsing.Optional(
          pyparsing.Suppress('[') + _PROCESS_IDENTIFIER.setResultsName('pid') +
          pyparsing.Suppress(']')) +
      pyparsing.Optional(
          pyparsing.Suppress('<') +
          pyparsing.Word(_FACILITY_CHARACTERS).setResultsName('facility') +
          pyparsing.Suppress('>')) +
      pyparsing.Optional(pyparsing.Suppress(':')) +
      pyparsing.Regex(_BODY_PATTERN, re.DOTALL).setResultsName('body') +
      pyparsing.lineEnd())

  # TODO: Add proper support for %STRUCTURED-DATA%:
  # https://datatracker.ietf.org/doc/html/draft-ietf-syslog-protocol-23#section-6.3
  _RSYSLOG_PROTOCOL_23_LINE = (
      pyparsing.Suppress('<') + _ONE_OR_TWO_DIGITS.setResultsName('priority') +
      pyparsing.Suppress('>') + pyparsing.Suppress(
          pyparsing.Word(pyparsing.nums, max=1)) +
      _DATE_TIME_RFC3339.setResultsName('date_time') +
      pyparsing.Word(pyparsing.printables).setResultsName('hostname') +
      _REPORTER.setResultsName('reporter') +
      pyparsing.Or([
          pyparsing.Suppress('-'), _PROCESS_IDENTIFIER.setResultsName('pid')]) +
      pyparsing.Word(pyparsing.printables).setResultsName(
          'message_identifier') +
      pyparsing.Word(pyparsing.printables).setResultsName('structured_data') +
      pyparsing.Regex(_BODY_PATTERN, re.DOTALL).setResultsName('body') +
      pyparsing.lineEnd())

  _SYSLOG_COMMENT = (
      _DATE_TIME.setResultsName('date_time') + pyparsing.Suppress(':') +
      pyparsing.Suppress('---') +
      pyparsing.SkipTo(' ---').setResultsName('body') +
      pyparsing.Suppress('---') + pyparsing.LineEnd())

  _KERNEL_SYSLOG_LINE = (
      _DATE_TIME.setResultsName('date_time') +
      pyparsing.Literal('kernel').setResultsName('reporter') +
      pyparsing.Suppress(':') +
      pyparsing.Regex(_BODY_PATTERN, re.DOTALL).setResultsName('body') +
      pyparsing.lineEnd())

  _LINE_STRUCTURES = [
      ('chromeos_syslog_line', _CHROMEOS_SYSLOG_LINE),
      ('kernel_syslog_line', _KERNEL_SYSLOG_LINE),
      ('rsyslog_line', _RSYSLOG_LINE),
      ('rsyslog_traditional_line', _RSYSLOG_TRADITIONAL_LINE),
      ('rsyslog_protocol_23_line', _RSYSLOG_PROTOCOL_23_LINE),
      ('syslog_comment', _SYSLOG_COMMENT)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in _LINE_STRUCTURES])

  def __init__(self):
    """Initializes a parser."""
    super(SyslogParser, self).__init__()
    self._plugin_by_reporter = {}

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
      if len(time_elements_structure) >= 9:
        has_year = True
        time_zone_minutes = 0

        if len(time_elements_structure) == 9:
          (year, month, day_of_month, hours, minutes, seconds, microseconds,
           time_zone_sign, time_zone_hours) = time_elements_structure

        else:
          (year, month, day_of_month, hours, minutes, seconds, microseconds,
           time_zone_sign, time_zone_hours, time_zone_minutes) = (
              time_elements_structure)

        time_zone_offset = (time_zone_hours * 60) + time_zone_minutes
        if time_zone_sign == '-':
          time_zone_offset *= -1

      else:
        has_year = False
        microseconds = None
        time_zone_offset = None

        if len(time_elements_structure) == 5:
          month_string, day_of_month, hours, minutes, seconds = (
              time_elements_structure)

        else:
          # TODO: add support for fractional seconds.
          month_string, day_of_month, hours, minutes, seconds, _ = (
              time_elements_structure)

        month = self._GetMonthFromString(month_string)

        self._UpdateYear(month)

        year = self._GetRelativeYear()

      if microseconds is None:
        time_elements_tuple = (
            year, month, day_of_month, hours, minutes, seconds)

        date_time = dfdatetime_time_elements.TimeElements(
            is_delta=(not has_year), time_elements_tuple=time_elements_tuple,
            time_zone_offset=time_zone_offset)

      else:
        time_elements_tuple = (
            year, month, day_of_month, hours, minutes, seconds, microseconds)

        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds(
            is_delta=(not has_year), time_elements_tuple=time_elements_tuple,
            time_zone_offset=time_zone_offset)

      date_time.is_local_time = time_zone_offset is None

      return date_time

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse time elements with error: {0!s}'.format(exception))

  def _PriorityToSeverity(self, priority):
    """Converts a syslog protocol 23 priority value to severity.

    Also see:
      https://datatracker.ietf.org/doc/html/draft-ietf-syslog-protocol-23

    Args:
      priority (int): a syslog protocol 23 priority value.

    Returns:
      str: the value from _SYSLOG_SEVERITY corresponding to severity value.
    """
    severity = self._SYSLOG_SEVERITY[priority % 8]
    return severity

  def CheckRequiredFormat(self, parser_mediator, text_reader):
    """Check if the log record has the minimal structure required by the parser.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    if not bool(self._VERIFICATION_REGEX.match(text_reader.lines)):
      return False

    self._SetEstimatedYear(parser_mediator)

    return True

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
          and other components, such as storage and dfVFS.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): elements parsed from the file.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in self._SUPPORTED_KEYS:
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    date_time = self._ParseTimeElements(time_elements_structure)

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

        except errors.ParseError as exception:
          parser_mediator.ProduceExtractionWarning(
              'unable to parse message: {0:s} with error: {1!s}'.format(
                  event_data.body, exception))

        except errors.WrongPlugin:
          plugin = None

    if not plugin:
      event_data.last_written_time = date_time

      parser_mediator.ProduceEventData(event_data)


manager.ParsersManager.RegisterParser(SyslogParser)
