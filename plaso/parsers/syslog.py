# -*- coding: utf-8 -*-
"""Parser for syslog formatted log files.

Also see:
  https://www.rsyslog.com/doc/v8-stable/configuration/templates.html
"""

import abc
import codecs
import re

from dfdatetime import time_elements as dfdatetime_time_elements

import pyparsing

from plaso.containers import events
from plaso.lib import errors
from plaso.lib import yearless_helper
from plaso.parsers import interface
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


# TODO: remove after refactor.
class PyparsingLineStructure(object):
  """Line structure.

  Attributes:
    expression (pyparsing.ParserElement): pyparsing expression to parse
        the line structure.
    name (str): name to identify the line structure.
    weight (int): number of times the line structure was successfully used.
  """

  def __init__(self, name, expression):
    """Initializes a line structure.

    Args:
      name (str): name to identify the line structure.
      expression (pyparsing.ParserElement): pyparsing expression to parse
          the line structure.
    """
    super(PyparsingLineStructure, self).__init__()
    self.expression = expression
    self.name = name
    self.weight = 0

  def ParseString(self, string):
    """Parses a string.

    Args:
      string (str): string to parse.

    Returns:
      tuple[pyparsing.ParseResults, int, int]: parsed tokens, start and end
          offset or None if the string could not be parsed.
    """
    try:
      structure_generator = self.expression.scanString(string, maxMatches=1)
      return next(structure_generator, None)

    except pyparsing.ParseException as exception:
      logger.debug('Unable to parse string with error: {0!s}'.format(exception))

    return None


# TODO: remove after refactor.
class PyparsingMultiLineTextParser(interface.FileObjectParser):
  """Multi-line text parser interface based on pyparsing."""

  BUFFER_SIZE = 2048

  # The maximum number of consecutive lines that don't match known line
  # structures to encounter before aborting parsing.
  MAXIMUM_CONSECUTIVE_LINE_FAILURES = 20

  _ENCODING = None

  # The actual structure, this needs to be defined by each parser.
  # This is defined as a list of tuples so that more than a single line
  # structure can be defined. That way the parser can support more than a
  # single type of log entry, despite them all having in common the constraint
  # that each log entry is a single line.
  # The tuple should have two entries, a key and a structure. This is done to
  # keep the structures in an order of priority/preference.
  # The key is a comment or an identification that is passed to the ParseRecord
  # function so that the developer can identify which structure got parsed.
  # The value is the actual pyparsing structure.

  _LINE_STRUCTURES = []

  _MONTH_DICT = {
      'jan': 1,
      'feb': 2,
      'mar': 3,
      'apr': 4,
      'may': 5,
      'jun': 6,
      'jul': 7,
      'aug': 8,
      'sep': 9,
      'oct': 10,
      'nov': 11,
      'dec': 12}

  def __init__(self):
    """Initializes a parser."""
    super(PyparsingMultiLineTextParser, self).__init__()
    self._current_offset = 0
    self._line_structures = []
    self._parser_mediator = None

    codecs.register_error('text_parser_handler', self._EncodingErrorHandler)

    if self._LINE_STRUCTURES:
      self._SetLineStructures(self._LINE_STRUCTURES)

  def _EncodingErrorHandler(self, exception):
    """Encoding error handler.

    Args:
      exception [UnicodeDecodeError]: exception.

    Returns:
      tuple[str, int]: replacement string and a position where encoding should
          continue.

    Raises:
      TypeError: if exception is not of type UnicodeDecodeError.
    """
    if not isinstance(exception, UnicodeDecodeError):
      raise TypeError('Unsupported exception type.')

    if self._parser_mediator:
      self._parser_mediator.ProduceExtractionWarning(
          'error decoding 0x{0:02x} at offset: {1:d}'.format(
              exception.object[exception.start],
              self._current_offset + exception.start))

    escaped = '\\x{0:2x}'.format(exception.object[exception.start])
    return escaped, exception.start + 1

  def _GetMatchingLineStructure(self, string):
    """Retrieves the first matching line structure.

    Args:
      string (str): string.

    Returns:
      tuple: containing:

        int: index of matching line structure in _line_structures;
        PyparsingLineStructure: matching line structure;
        tuple[pyparsing.ParseResults, int, int]: parsed tokens, start and end
            offset.
    """
    for index, line_structure in enumerate(self._line_structures):
      result_tuple = line_structure.ParseString(string)
      if result_tuple:
        # Only want to parse the structure if it starts at the beginning of
        # the string.
        if result_tuple[1] == 0:
          return index, line_structure, result_tuple

    return None, None, None

  def _GetValueFromStructure(self, structure, name, default_value=None):
    """Retrieves a token value from a Pyparsing structure.

    This method ensures the token value is set to the default value when
    the token is not present in the structure. Instead of returning
    the Pyparsing default value of an empty byte stream (b'').

    Args:
      structure (pyparsing.ParseResults): tokens from a parsed log line.
      name (str): name of the token.
      default_value (Optional[object]): default value.

    Returns:
      object: value in the token or default value if the token is not available
          in the structure.
    """
    value = structure.get(name, default_value)
    if isinstance(value, pyparsing.ParseResults) and not value:
      # Ensure the return value is not an empty pyparsing.ParseResults otherwise
      # serialization will fail.
      return None

    return value

  def _ParseLines(self, parser_mediator, text_reader):
    """Parses lines of text using a pyparsing definition.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    # Set the offset to the beginning of the file.
    self._current_offset = 0

    consecutive_line_failures = 0

    # Read every line in the text file.
    while text_reader.lines:
      if parser_mediator.abort:
        break

      # Try to parse the line using all the line structures.
      index, line_structure, result_tuple = self._GetMatchingLineStructure(
          text_reader.lines)

      if result_tuple:
        parsed_structure, _, end = result_tuple

        try:
          self._ParseLineStructure(
              parser_mediator, index, line_structure, parsed_structure)
          consecutive_line_failures = 0

        except errors.ParseError as exception:
          parser_mediator.ProduceExtractionWarning(
              'unable to parse record: {0:s} with error: {1!s}'.format(
                  line_structure.name, exception))

        text_reader.SkipAhead(end)

      else:
        odd_line = text_reader.ReadLine()
        if odd_line:
          if len(odd_line) > 80:
            odd_line = '{0:s}...'.format(odd_line[:77])

          parser_mediator.ProduceExtractionWarning(
              'unable to parse log line: {0:s}'.format(repr(odd_line)))

          consecutive_line_failures += 1
          if (consecutive_line_failures >
              self.MAXIMUM_CONSECUTIVE_LINE_FAILURES):
            raise errors.WrongParser(
                'more than {0:d} consecutive failures to parse lines.'.format(
                    self.MAXIMUM_CONSECUTIVE_LINE_FAILURES))

      try:
        text_reader.ReadLines()
        self._current_offset = text_reader.get_offset()
      except UnicodeDecodeError as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to read and decode log line at offset {0:d} with error: '
            '{1!s}').format(self._current_offset, exception))
        break

  def _ParseLineStructure(
      self, parser_mediator, index, line_structure, parsed_structure):
    """Parses a line structure and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      index (int): index of the line structure in the run-time list of line
          structures.
      line_structure (PyparsingLineStructure): line structure.
      parsed_structure (pyparsing.ParseResults): tokens from a string parsed
          with pyparsing.

    Raises:
      ParseError: if the structure cannot be parsed.
    """
    # TODO: use a callback per line structure name.
    self._ParseRecord(parser_mediator, line_structure.name, parsed_structure)

    line_structure.weight += 1

    while index > 0:
      previous_weight = self._line_structures[index - 1].weight
      if line_structure.weight < previous_weight:
        break

      self._line_structures[index] = self._line_structures[index - 1]
      self._line_structures[index - 1] = line_structure
      index -= 1

  @abc.abstractmethod
  def _ParseRecord(self, parser_mediator, key, structure):
    """Parses a pyparsing structure.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): tokens from a parsed log line.

    Raises:
      ParseError: when the structure type is unknown.
    """

  def _SetLineStructures(self, line_structures):
    """Sets the line structures.

    Args:
      line_structures ([(str, pyparsing.ParserElement)]): tuples of pyparsing
          expressions to parse a line and their names.
    """
    self._line_structures = []
    for key, expression in line_structures:
      # Using parseWithTabs() overrides Pyparsing's default replacement of tabs
      # with spaces to SkipAhead() the correct number of bytes after a match.
      expression.parseWithTabs()

      line_structure = PyparsingLineStructure(key, expression)
      self._line_structures.append(line_structure)

  @abc.abstractmethod
  def CheckRequiredFormat(self, parser_mediator, text_reader):
    """Check if the log record has the minimal structure required by the parser.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a text file-like object using a pyparsing definition.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    if not self._line_structures:
      raise errors.WrongParser('Missing line structures.')

    self._parser_mediator = parser_mediator

    encoding = self._ENCODING or parser_mediator.codepage
    text_reader = text_parser.EncodedTextReader(
        file_object, buffer_size=self.BUFFER_SIZE, encoding=encoding)

    try:
      text_reader.ReadLines()
      self._current_offset = text_reader.get_offset()
    except UnicodeDecodeError as exception:
      raise errors.WrongParser('Not a text file, with error: {0!s}'.format(
          exception))

    if not self.CheckRequiredFormat(parser_mediator, text_reader):
      raise errors.WrongParser('Wrong file structure.')

    try:
      self._ParseLines(parser_mediator, text_reader)
    except Exception as exception:  # pylint: disable=broad-except
      parser_mediator.ProduceExtractionWarning(
          '{0:s} unable to parse text file with error: {1!s}'.format(
              self.NAME, exception))

    if hasattr(self, 'GetYearLessLogHelper'):
      year_less_log_helper = self.GetYearLessLogHelper()
      parser_mediator.AddYearLessLogHelper(year_less_log_helper)


class SyslogParser(
    PyparsingMultiLineTextParser, yearless_helper.YearLessLogFormatHelper):
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

  def _ParseRecord(self, parser_mediator, key, structure):
    """Parses a pyparsing structure.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): tokens from a parsed log line.

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


manager.ParsersManager.RegisterParser(SyslogParser)
