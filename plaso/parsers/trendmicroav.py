# -*- coding: utf-8 -*-
"""Parser for Trend Micro Antivirus logs.

Trend Micro uses two log files to track the scans (both manual/scheduled and
real-time) and the web reputation (network scan/filtering).

Currently only the first log is supported.
"""

from dfdatetime import definitions as dfdatetime_definitions
from dfdatetime import posix_time as dfdatetime_posix_time
from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import dsv_parser
from plaso.parsers import manager


class TrendMicroAVEventData(events.EventData):
  """Trend Micro AV Log event data.

  Attributes:
    action (str): action.
    filename (str): filename.
    offset (int): offset of the line relative to the start of the file, from
        which the event data was extracted.
    path (str): path.
    scan_type (str): scan_type.
    threat (str): threat.
    written_time (dfdatetime.DateTimeValues): date and time the log entry was
        written.
  """

  DATA_TYPE = 'av:trendmicro:scan'

  def __init__(self):
    """Initializes event data."""
    super(TrendMicroAVEventData, self).__init__(data_type=self.DATA_TYPE)
    self.action = None
    self.filename = None
    self.offset = None
    self.path = None
    self.scan_type = None
    self.threat = None
    self.written_time = None


class TrendMicroUrlEventData(events.EventData):
  """Trend Micro Web Reputation Log event data.

  Attributes:
    application_name (str): application name.
    block_mode (str): operation mode.
    credibility_rating (int): credibility rating.
    credibility_score (int): credibility score.
    group_code (str): group code.
    group_name (str): group name.
    ip (str): IP address.
    offset (int): offset of the line relative to the start of the file, from
        which the event data was extracted.
    policy_identifier (int): policy identifier.
    threshold (int): threshold value.
    url (str): accessed URL.
    written_time (dfdatetime.DateTimeValues): entry written date and time.
  """

  DATA_TYPE = 'av:trendmicro:webrep'

  def __init__(self):
    """Initializes event data."""
    super(TrendMicroUrlEventData, self).__init__(data_type=self.DATA_TYPE)
    self.application_name = None
    self.block_mode = None
    self.credibility_rating = None
    self.credibility_score = None
    self.group_code = None
    self.group_name = None
    self.ip = None
    self.offset = None
    self.policy_identifier = None
    self.threshold = None
    self.url = None
    self.written_time = None


class TrendMicroBaseParser(dsv_parser.DSVParser):
  """Common code for parsing Trend Micro log files.

  The file format is reminiscent of CSV, but is not quite the same; the
  delimiter is a three-character sequence and there is no provision for
  quoting or escaping.
  """
  # pylint: disable=abstract-method

  DELIMITER = '<;>'

  # Subclasses must define a list of column names.
  COLUMNS = ()

  # Subclasses must define a minimum number of columns value.
  _MINIMUM_NUMBER_OF_COLUMNS = None

  def _CreateDictReader(self, line_reader):
    """Iterates over the log lines and provide a reader for the values.

    Args:
      line_reader (iter): yields each line in the log file.

    Yields:
      dict[str, str]: column values keyed by column header.

    Raises:
      WrongParser: if a log line cannot be parsed.
    """
    for line in line_reader:
      stripped_line = line.strip()
      values = stripped_line.split(self.DELIMITER)
      number_of_values = len(values)
      number_of_columns = len(self.COLUMNS)

      if number_of_values < self._MINIMUM_NUMBER_OF_COLUMNS:
        raise errors.WrongParser(
            'Expected at least {0:d} values, found {1:d}'.format(
                self._MINIMUM_NUMBER_OF_COLUMNS, number_of_values))

      if number_of_values > number_of_columns:
        raise errors.WrongParser(
            'Expected at most {0:d} values, found {1:d}'.format(
                number_of_columns, number_of_values))

      yield dict(zip(self.COLUMNS, values))

  def _ParseTimestamp(self, parser_mediator, row):
    """Provides a timestamp for the given row.

    If the Trend Micro log comes from a version that provides a POSIX timestamp,
    use that directly; it provides the advantages of UTC and of second
    precision. Otherwise fall back onto the local-timezone date and time.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.

    Returns:
      dfdatetime.interface.DateTimeValue: date and time value or None.
    """
    timestamp = row.get('timestamp', None)
    if timestamp is not None:
      try:
        timestamp = int(timestamp, 10)
      except (ValueError, TypeError):
        parser_mediator.ProduceExtractionWarning(
            'Unable to parse timestamp value: {0!s}'.format(timestamp))

      return dfdatetime_posix_time.PosixTime(timestamp=timestamp)

    # The timestamp is not available; parse the local date and time instead.
    try:
      date_time = self._ConvertToTimestamp(row['date'], row['time'])
    except ValueError as exception:
      date_time = None
      parser_mediator.ProduceExtractionWarning((
          'Unable to parse time string: "{0:s} {1:s}" with error: '
          '{2!s}').format(repr(row['date']), repr(row['time']), exception))

    return date_time

  def _ConvertToTimestamp(self, date, time):
    """Converts date and time strings into a timestamp.

    Recent versions of Office Scan write a log field with a Unix timestamp.
    Older versions may not write this field; their logs only provide a date and
    a time expressed in the local time zone. This functions handles the latter
    case.

    Args:
      date (str): date as an 8-character string in the YYYYMMDD format.
      time (str): time as a 3 or 4-character string in the [H]HMM format or a
          6-character string in the HHMMSS format.

    Returns:
      dfdatetime.TimeElements: date and time value.

    Raises:
      ValueError: if the date and time values cannot be parsed.
    """
    if len(date) != 8:
      raise ValueError('Unsupported date string: {0!s}'.format(date))

    # The time consist of a hours and minutes value where the hours value has
    # no leading zero.
    if len(time) not in (3, 4):
      raise ValueError('Unsupported time string: {0!s}'.format(time))

    try:
      year = int(date[:4], 10)
      month = int(date[4:6], 10)
      day = int(date[6:8], 10)
    except (TypeError, ValueError):
      raise ValueError('Unable to parse date string: {0!s}'.format(date))

    try:
      hour = int(time[:-2], 10)
      minutes = int(time[-2:], 10)
    except (TypeError, ValueError):
      raise ValueError('Unable to parse time string: {0!s}'.format(date))

    time_elements_tuple = (year, month, day, hour, minutes, 0)
    date_time = dfdatetime_time_elements.TimeElements(
        precision=dfdatetime_definitions.PRECISION_1_MINUTE,
        time_elements_tuple=time_elements_tuple)
    date_time.is_local_time = True

    return date_time


class OfficeScanVirusDetectionParser(TrendMicroBaseParser):
  """Parses the Trend Micro Office Scan Virus Detection Log."""

  NAME = 'trendmicro_vd'
  DATA_FORMAT = 'Trend Micro Office Scan Virus Detection log file'

  COLUMNS = [
      'date', 'time', 'threat', 'action', 'scan_type', 'unused1',
      'path', 'filename', 'unused2', 'timestamp', 'unused3', 'unused4']

  _MINIMUM_NUMBER_OF_COLUMNS = 8

  _SUPPORTED_SCAN_RESULTS = frozenset([
      0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16, 25])

  def ParseRow(self, parser_mediator, row_offset, row):
    """Parses a line of the log file and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row_offset (int): offset of the line from which the row was extracted.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.
    """
    date_time = self._ParseTimestamp(parser_mediator, row)
    if date_time is None:
      return

    try:
      action = int(row['action'], 10)
    except (ValueError, TypeError):
      action = None

    try:
      scan_type = int(row['scan_type'], 10)
    except (ValueError, TypeError):
      scan_type = None

    event_data = TrendMicroAVEventData()
    event_data.action = action
    event_data.filename = row['filename']
    event_data.offset = row_offset
    event_data.path = row['path']
    event_data.scan_type = scan_type
    event_data.threat = row['threat']
    event_data.written_time = date_time

    parser_mediator.ProduceEventData(event_data)

  def VerifyRow(self, parser_mediator, row):
    """Verifies if a line of the file is in the expected format.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    if len(row) < self._MINIMUM_NUMBER_OF_COLUMNS:
      return False

    # Check the date format!
    # If it doesn't parse, then this isn't a Trend Micro AV log.
    try:
      timestamp = self._ConvertToTimestamp(row['date'], row['time'])
    except (ValueError, TypeError):
      return False

    if timestamp is None:
      return False

    # Check that the action value is plausible.
    try:
      action = int(row['action'], 10)
    except (ValueError, TypeError):
      return False

    return action in self._SUPPORTED_SCAN_RESULTS


class OfficeScanWebReputationParser(TrendMicroBaseParser):
  """Parses the Trend Micro Office Scan Web Reputation detection log."""

  NAME = 'trendmicro_url'
  DATA_FORMAT = 'Trend Micro Office Web Reputation log file'

  COLUMNS = (
      'date', 'time', 'block_mode', 'url', 'group_code', 'group_name',
      'credibility_rating', 'policy_identifier', 'application_name',
      'credibility_score', 'ip', 'threshold', 'timestamp', 'unused')

  _MINIMUM_NUMBER_OF_COLUMNS = 12

  _SUPPORTED_BLOCK_MODES = frozenset([0, 1])

  def ParseRow(self, parser_mediator, row_offset, row):
    """Parses a line of the log file and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row_offset (int): offset of the line from which the row was extracted.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.
    """
    date_time = self._ParseTimestamp(parser_mediator, row)
    if date_time is None:
      return

    event_data = TrendMicroUrlEventData()
    event_data.offset = row_offset
    event_data.written_time = date_time

    # Convert and store integer values.
    for field in (
        'credibility_rating', 'credibility_score', 'policy_identifier',
        'threshold', 'block_mode'):
      try:
        value = int(row[field], 10)
      except (ValueError, TypeError):
        value = None
      setattr(event_data, field, value)

    # Store string values.
    for field in ('url', 'group_name', 'group_code', 'application_name', 'ip'):
      setattr(event_data, field, row[field])

    parser_mediator.ProduceEventData(event_data)

  def VerifyRow(self, parser_mediator, row):
    """Verifies if a line of the file is in the expected format.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    if len(row) < self._MINIMUM_NUMBER_OF_COLUMNS:
      return False

    try:
      timestamp = self._ConvertToTimestamp(row['date'], row['time'])
    except ValueError:
      return False

    if timestamp is None:
      return False

    try:
      block_mode = int(row['block_mode'], 10)
    except (ValueError, TypeError):
      return False

    return block_mode in self._SUPPORTED_BLOCK_MODES


manager.ParsersManager.RegisterParsers([
    OfficeScanVirusDetectionParser, OfficeScanWebReputationParser])
