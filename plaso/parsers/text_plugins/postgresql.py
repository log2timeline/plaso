# -*- coding: utf-8 -*-
"""Text parser plugin for PostgreSQL application log files.

This is a multi-line log format that records internal database application
logs as well as authentication attempts.

Also see:
  https://www.postgresql.org/docs/current/runtime-config-logging.html
"""

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class PostgreSQLEventData(events.EventData):
  """PostgreSQL application log data.

  Attributes:
    log_line (str): log message.
    pid (int): process identifier (PID).
    recorded_time (dfdatetime.DateTimeValues): date and time the log entry
        was recorded.
    severity (str): severity.
    user (str): "user@database" string if present. Records the user account and
        database name that was authenticated or attempting to authenticate.
  """

  DATA_TYPE = 'postgresql:application_log:entry'

  def __init__(self):
    """Initializes event data."""
    super(PostgreSQLEventData, self).__init__(data_type=self.DATA_TYPE)
    self.log_line = None
    self.pid = None
    self.recorded_time = None
    self.severity = None
    self.user = None


class PostgreSQLTextPlugin(interface.TextPlugin):
  """Text parser plugin for PostgreSQL application log files."""

  NAME = 'postgresql'
  DATA_FORMAT = 'PostgreSQL application log file'

  ENCODING = 'utf-8'

  _INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _THREE_DIGITS = pyparsing.Word(pyparsing.nums, exact=3).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      lambda tokens: int(tokens[0], 10))

  # Date and time values are formatted as: YYYY-MM-DD hh:mm:ss.### UTC
  # For example: 2022-04-12 00:16:05.526 UTC
  _DATE_TIME = (
      pyparsing.LineStart() +
      _FOUR_DIGITS.setResultsName('year') + pyparsing.Suppress('-') +
      _TWO_DIGITS.setResultsName('month') + pyparsing.Suppress('-') +
      _TWO_DIGITS.setResultsName('day_of_month') +
      _TWO_DIGITS.setResultsName('hours') + pyparsing.Suppress(':') +
      _TWO_DIGITS.setResultsName('minutes') + pyparsing.Suppress(':') +
      _TWO_DIGITS.setResultsName('seconds') +
      pyparsing.Optional(
          pyparsing.Suppress('.') +
          _THREE_DIGITS.setResultsName('milliseconds'))).setResultsName(
              'date_time')

  _TIME_ZONE = pyparsing.Word(pyparsing.printables).setResultsName('time_zone')

  _PID = (
      pyparsing.Suppress('[') + pyparsing.OneOrMore(_INTEGER) +
      pyparsing.Optional(pyparsing.Literal('-')) +
      pyparsing.ZeroOrMore(_INTEGER) +
      pyparsing.Suppress(']')).setResultsName('pid')

  _USER_AND_DATABASE = (
      pyparsing.Word(pyparsing.alphanums) +
      pyparsing.Literal('@') +
      pyparsing.Word(pyparsing.alphanums)).setResultsName('user_and_database')

  _SEVERITY = pyparsing.Word(pyparsing.string.ascii_uppercase)

  _LOG_LINE_END = pyparsing.StringEnd() | (_DATE_TIME + _TIME_ZONE)

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _LOG_LINE = (
      _DATE_TIME + _TIME_ZONE + _PID + pyparsing.Optional(_USER_AND_DATABASE) +
      _SEVERITY.setResultsName('severity') +
      pyparsing.Suppress(':') +
      pyparsing.SkipTo(_LOG_LINE_END).setResultsName('log_line') +
      pyparsing.ZeroOrMore(_END_OF_LINE))

  _LINE_STRUCTURES = [('log_line', _LOG_LINE)]

  VERIFICATION_GRAMMAR = _LOG_LINE

  # TODO: move this into timeliner

  # Extracted from /usr/share/postgresql/13/timezonesets/Default
  # See https://www.postgresql.org/docs/current/datetime-config-files.html
  _PSQL_TIME_ZONE_MAPPING = {
        'ACDT': 'Australia/Adelaide',
        'ACST': 'Australia/Adelaide',
        'ADT': 'America/Glace_Bay',
        'AEDT': 'Australia/Brisbane',
        'AEST': 'Australia/Brisbane',
        'AKDT': 'America/Anchorage',
        'AKST': 'America/Anchorage',
        'AST': 'America/Anguilla',
        'AWST': 'Australia/Perth',
        'BST': 'Europe/London',
        'CDT': 'America/Chicago',
        'CEST': 'Africa/Ceuta',
        'CET': 'Africa/Algiers',
        'CETDST': 'Africa/Ceuta',
        'CST': 'America/Chicago',
        'EAT': 'Africa/Addis_Ababa',
        'EDT': 'America/Detroit',
        'EEST': 'Africa/Cairo',
        'EET': 'Africa/Cairo',
        'EETDST': 'Africa/Cairo',
        'EST': 'America/Cancun',
        'GMT': 'Africa/Abidjan',
        'HKT': 'Asia/Hong_Kong',
        'HST': 'Pacific/Honolulu',
        'IDT': 'Asia/Jerusalem',
        'IST': 'Asia/Jerusalem',
        'JST': 'Asia/Tokyo',
        'KST': 'Asia/Seoul',
        'MDT': 'America/Boise',
        'MSK': 'Europe/Moscow',
        'MST': 'America/Boise',
        'NDT': 'America/St_Johns',
        'NST': 'America/St_Johns',
        'NZDT': 'Antarctica/McMurdo',
        'NZST': 'Antarctica/McMurdo',
        'PDT': 'America/Dawson',
        'PKST': 'Asia/Karachi',
        'PKT': 'Asia/Karachi',
        'PST': 'America/Dawson',
        'SAST': 'Africa/Johannesburg',
        'UCT': 'Etc/UCT',
        'WAT': 'Africa/Bangui',
        'WET': 'Africa/Casablanca',
        'WETDST': 'Atlantic/Canary'}

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
    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    log_line = self._GetValueFromStructure(
        structure, 'log_line', default_value='')
    log_line = log_line.lstrip().rstrip()

    pids = self._GetValueFromStructure(structure, 'pid', default_value=[])

    time_zone_string = self._GetValueFromStructure(structure, 'time_zone')

    user_and_database = self._GetValueFromStructure(
        structure, 'user_and_database', default_value='')
    user_and_database = ''.join(user_and_database)

    # TODO: move this into timeliner
    time_zone_string = self._PSQL_TIME_ZONE_MAPPING.get(
        time_zone_string, time_zone_string)

    date_time = self._ParseTimeElements(time_elements_structure)
    if time_zone_string != 'UTC':
      date_time.is_local_time = True
      date_time.time_zone_hint = time_zone_string

    event_data = PostgreSQLEventData()
    event_data.log_line = log_line or None
    event_data.pid = ''.join([str(pid) for pid in pids])
    event_data.recorded_time = date_time
    event_data.severity = self._GetValueFromStructure(structure, 'severity')
    event_data.user = user_and_database or None

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
    # Ensure time_elements_tuple is not a pyparsing.ParseResults otherwise
    # copy.deepcopy() of the dfDateTime object will fail on Python 3.8 with:
    # "TypeError: 'str' object is not callable" due to pyparsing.ParseResults
    # overriding __getattr__ with a function that returns an empty string when
    # named token does not exist.
    try:
      if len(time_elements_structure) == 6:
        year, month, day_of_month, hours, minutes, seconds = (
            time_elements_structure)

        date_time = dfdatetime_time_elements.TimeElements(time_elements_tuple=(
            year, month, day_of_month, hours, minutes, seconds))

      else:
        year, month, day_of_month, hours, minutes, seconds, milliseconds = (
            time_elements_structure)

        date_time = dfdatetime_time_elements.TimeElementsInMilliseconds(
            time_elements_tuple=(
                year, month, day_of_month, hours, minutes, seconds,
                milliseconds))

      return date_time

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse time elements with error: {0!s}'.format(exception))

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

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    try:
      self._ParseTimeElements(time_elements_structure)
    except errors.ParseError:
      return False

    return True


text_parser.TextLogParser.RegisterPlugin(PostgreSQLTextPlugin)
