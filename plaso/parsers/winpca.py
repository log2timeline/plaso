# -*- coding: utf-8 -*-
"""Parser for Windows Program Compatibility Assistant (PCA) log files."""

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import dsv_parser
from plaso.parsers import manager


class WindowsPCAEventData(events.EventData):
  """Windows PCA (Program Compatibility Assistant) event data.

  Attributes:
    description (str): description of the executable.
    executable (str): executable filename.
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
    super(WindowsPCAEventData, self).__init__(data_type=self.DATA_TYPE)
    self.description = None
    self.executable = None
    self.exit_code = None
    self.last_execution_time = None
    self.program_identifier = None
    self.run_status = None
    self.vendor = None
    self.version = None


class WindowsPCABaseParser(dsv_parser.DSVParser):
  """Shared code for parsing Program Compatibility Assistant (PCA) log files."""

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
    if (date_time_string[4] != '-' or date_time_string[7] != '-' or
        date_time_string[10] != ' ' or date_time_string[13] != ':' or
        date_time_string[16] != ':' or date_time_string[19] != '.'):
      raise errors.ParseError('Unsupported date and time string: {0!s}'.format(
          date_time_string))

    try:
      year = int(date_time_string[0:4], 10)
      month = int(date_time_string[5:7], 10)
      day_of_month = int(date_time_string[8:10], 10)
      hours = int(date_time_string[11:13], 10)
      minutes = int(date_time_string[14:16], 10)
      seconds = int(date_time_string[17:19], 10)
      milliseconds = int(date_time_string[20:23], 10)
    except (TypeError, ValueError):
      raise errors.ParseError('Unsupported date and time string: {0!s}'.format(
          date_time_string))

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


class WindowsPCADB0Parser(WindowsPCABaseParser):
  """Parses Windows Program Compatibility Assistant DB0 log files."""

  NAME = 'winpca_db0'
  DATA_FORMAT = 'Windows PCA DB0 log file'

  COLUMNS = [
      'datetime', 'run_status', 'program', 'description', 'vendor',
      'version', 'program_id', 'exit_code']

  _MINIMUM_NUMBER_OF_COLUMNS = 8

  def ParseRow(self, parser_mediator, row_offset, row):  # pylint: disable=unused-argument
    """Parses a line of the log file and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      row_offset (int): offset of the line from which the row was extracted.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.
    """
    event_data = WindowsPCAEventData()
    event_data.description = row['description']
    event_data.executable = row['program']
    event_data.exit_code = row['exit_code']
    event_data.last_execution_time = self._ParseDateTime(row['datetime'])
    event_data.program_identifier = row['program_id']
    event_data.run_status = row['run_status']
    event_data.vendor = row['vendor']
    event_data.version = row['version']

    parser_mediator.ProduceEventData(event_data)


class WindowsPCADicParser(WindowsPCABaseParser):
  """Parses the Windows Program Compatibility Assistant DIC log files."""

  NAME = 'winpca_dic'
  DATA_FORMAT = 'Windows PCA DIC log file'

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
    event_data = WindowsPCAEventData()
    event_data.executable = row['program']
    event_data.last_execution_time = self._ParseDateTime(row['datetime'])

    parser_mediator.ProduceEventData(event_data)


manager.ParsersManager.RegisterParsers([
    WindowsPCADicParser, WindowsPCADB0Parser])
