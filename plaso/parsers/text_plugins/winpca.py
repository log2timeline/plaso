# -*- coding: utf-8 -*-
"""Parser for Windows Program Compatibility Assistant (PCA) Log files."""

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import dsv_parser
from plaso.parsers import manager


class WinPCAEventData(events.EventData):
  """Windows PCA (Program Compatibility Assistant) event data.

  Attributes:
    body (str): message body.
    description (str): description of the executable.
    exit_code (str): final result of the execution.
    last_execution_time (dfdatetime.DateTimeValues): entry last execution
        date and time.
    program_identifier (str): program identifier.
    run_status (str): execution status.
    vendor (str): vendor of executed software.
    version (str): version of executed software.
  """

  DATA_TYPE = 'windows:pca_log:entry'

  def __init__(self):
    """Initializes event data."""
    super(WinPCAEventData, self).__init__(data_type=self.DATA_TYPE)
    self.body = None
    self.description = None
    self.exit_code = None
    self.last_execution_time = None
    self.program_identifier = None
    self.run_status = None
    self.vendor = None
    self.version = None


class WinPCABaseParser(dsv_parser.DSVParser):
  """Common code for parsing Windows PCA Log files."""

  # pylint: disable=abstract-method

  DELIMITER = '|'

  COLUMNS = ()
  _MINIMUM_NUMBER_OF_COLUMNS = None

  def _ParseDateTime(self, date_time_string):
    """Parses date and time elements of a log line.

    Args:
      date_time_string (string): Date time values extracted from the logfile.

    Returns:
      dfdatetime.TimeElements: date and time value.

    Raises:
      ParseError: if a valid date and time value cannot be derived from
          the time elements.
    """
    date_string, time_string = date_time_string.split(' ')
    try:
      year_string, month_string, day_of_month_string = date_string.split('-')
      year = int(year_string, 10)
      month = int(month_string, 10)
      day_of_month = int(day_of_month_string, 10)
    except (AttributeError, ValueError):
      raise errors.ParseError('Unsupported date string: {0:s}'.format(
          date_string))

    try:
      time_value, ms_value = time_string.split('.')
      hours_string, minutes_string, seconds_string = time_value.split(':')
      hours = int(hours_string, 10)
      minutes = int(minutes_string, 10)
      seconds = int(seconds_string, 10)
      milliseconds = int(ms_value, 10)
    except (AttributeError, ValueError):
      raise errors.ParseError('Unsupported time string: {0:s}'.format(
          time_string))

    time_elements_tuple = (
        year, month, day_of_month, hours, minutes, seconds, milliseconds)

    date_time = dfdatetime_time_elements.TimeElementsInMilliseconds(
        time_elements_tuple=time_elements_tuple)
    date_time.is_local_time = False

    return date_time

  def VerifyRow(self, parser_mediator, row):
    """Verifies if a line of the file is in the expected format.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    if len(row) < self._MINIMUM_NUMBER_OF_COLUMNS:
      return False

    try:
      self._ParseDateTime(row['datetime'])
    except (AttributeError, ValueError):
      return False

    return '\\' in row['program']


class WinPCADicParser(WinPCABaseParser):
  """Parses the Windows Program Compatibility Assistant DIC files."""

  NAME = 'winpca_dic'
  DATA_FORMAT = 'Windows PCA log file'

  COLUMNS = ['program', 'datetime']

  _MINIMUM_NUMBER_OF_COLUMNS = 2

  def ParseRow(self, parser_mediator, row_offset, row):
    """Parses a line of the log file and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      row_offset (int): offset of the line from which the row was extracted.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.
    """
    event_data = WinPCAEventData()
    event_data.body = row['program']
    event_data.last_execution_time = self._ParseDateTime(row['datetime'])

    parser_mediator.ProduceEventData(event_data)


class WinPCADB0Parser(WinPCABaseParser):
  """Parses the Windows Program Compatibility Assistant DB0 files."""

  NAME = 'winpca_db0'
  DATA_FORMAT = 'Windows PCA log file'

  COLUMNS = [
      'datetime', 'run_status', 'program', 'description', 'vendor',
      'version', 'program_id', 'exit_code']

  _MINIMUM_NUMBER_OF_COLUMNS = 8

  def ParseRow(self, parser_mediator, row_offset, row):
    """Parses a line of the log file and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      row_offset (int): offset of the line from which the row was extracted.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.
    """
    event_data = WinPCAEventData()
    event_data.body = row['program']
    event_data.last_execution_time = self._ParseDateTime(row['datetime'])

    event_data.run_status = row['run_status']
    event_data.description = row['description']
    event_data.vendor = row['vendor']
    event_data.version = row['version']
    event_data.program_identifier = row['program_id']
    event_data.exit_code = row['exit_code']

    parser_mediator.ProduceEventData(event_data)


manager.ParsersManager.RegisterParsers([WinPCADicParser, WinPCADB0Parser])
