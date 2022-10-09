# -*- coding: utf-8 -*-
"""Parser for PostgreSQL application log files."""

import pytz

import pyparsing

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import errors
from plaso.parsers import manager
from plaso.parsers import text_parser


class PostgreSQLEventData(events.EventData):
  """PostgreSQL application log data.

  Attributes:
    log_level (str): logging level of event.
    log_line (str): log message.
    pid (int): process identifier (PID).
    user (str): "user@database" string if present. Records the user account and
        database name that was authenticated or attempting to authenticate.
  """

  DATA_TYPE = 'postgresql:application_log:entry'

  def __init__(self):
    """Initializes event data."""
    super(PostgreSQLEventData, self).__init__(data_type=self.DATA_TYPE)
    self.log_level = None
    self.log_line = None
    self.pid = None
    self.user = None


class PostgreSQLParser(text_parser.PyparsingMultiLineTextParser):
  """Parses events from PostgreSQL application log files.

  This is a multi-line log format that records internal database application
  logs as well as authentication attempts.
  """

  NAME = 'postgresql'
  DATA_FORMAT = 'PostgreSQL application log file'

  _ENCODING = 'utf-8'

  _INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(
      text_parser.PyParseIntCast)

  _TWO_DIGITS = pyparsing.Word(pyparsing.nums, exact=2).setParseAction(
      text_parser.PyParseIntCast)

  _THREE_DIGITS = pyparsing.Word(pyparsing.nums, exact=3).setParseAction(
      text_parser.PyParseIntCast)

  _FOUR_DIGITS = pyparsing.Word(pyparsing.nums, exact=4).setParseAction(
      text_parser.PyParseIntCast)

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

  _LOG_LEVEL = (
      pyparsing.Word(pyparsing.string.ascii_uppercase) +
      pyparsing.Suppress(':')).setResultsName('log_level')

  _LOG_LINE_END = pyparsing.StringEnd() | (_DATE_TIME + _TIME_ZONE)

  _LOG_LINE = (
      _DATE_TIME + _TIME_ZONE + _PID + pyparsing.Optional(_USER_AND_DATABASE) +
      _LOG_LEVEL + pyparsing.SkipTo(_LOG_LINE_END).setResultsName('log_line') +
      pyparsing.ZeroOrMore(pyparsing.lineEnd()))

  LINE_STRUCTURES = [('logline', _LOG_LINE)]

  _SUPPORTED_KEYS = frozenset([key for key, _ in LINE_STRUCTURES])

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

  def _BuildDateTime(self, time_elements_structure):
    """Builds time elements from a PostgreSQL log time stamp.

    Args:
      time_elements_structure (pyparsing.ParseResults): structure of tokens
          derived from a PostgreSQL log time stamp.

    Returns:
      dfdatetime.TimeElements: date and time extracted from the structure or
          None if the structure does not represent a valid string.
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
    except (TypeError, ValueError):
      return None

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a record and produces a PostgreSQL event.

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

    event_data = PostgreSQLEventData()
    event_data.pid = ''.join(
        [str(pid) for pid in self._GetValueFromStructure(structure, 'pid')])

    log_level = self._GetValueFromStructure(structure, 'log_level')
    if log_level and len(log_level) != 1:
      parser_mediator.ProduceExtractionWarning('no log level found')
      return

    event_data.log_level = log_level[0]

    user_and_database = self._GetValueFromStructure(
        structure, 'user_and_database')
    if user_and_database:
      event_data.user = ''.join(user_and_database)

    log_line = self._GetValueFromStructure(structure, 'log_line')
    if log_line:
      event_data.log_line = log_line.lstrip().rstrip()

    time_zone_string = self._GetValueFromStructure(structure, 'time_zone')
    time_zone_string = self._PSQL_TIME_ZONE_MAPPING.get(
        time_zone_string, time_zone_string)

    time_zone = None
    if time_zone_string != 'UTC':
      try:
        time_zone = pytz.timezone(time_zone_string)
      except pytz.UnknownTimeZoneError:
        parser_mediator.ProduceExtractionWarning(
            'unsupported time zone: {0!s}'.format(time_zone_string))
        return

    time_elements_structure = self._GetValueFromStructure(
        structure, 'date_time')

    date_time = self._BuildDateTime(time_elements_structure)
    if time_zone:
      # TODO: set time_zone_offset in date_time instead of using local time.
      date_time.is_local_time = True

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_RECORDED, time_zone=time_zone)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  # pylint: disable=unused-argument
  def VerifyStructure(self, parser_mediator, lines):
    """Verifies that this is a PostgreSQL application log.

    Args:
      parser_mediator (ParserMediator): mediates interactions between
          parsers and other components, such as storage and dfVFS.
      lines (str): one or more lines from the text file.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    try:
      self._LOG_LINE.parseString(lines)
    except pyparsing.ParseException:
      return False

    return True


manager.ParsersManager.RegisterParser(PostgreSQLParser)
