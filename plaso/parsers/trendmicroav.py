# -*- coding: utf-8 -*-
"""Parser for Trend Micro Antivirus logs.

Trend Micro uses two log files to track the scans (both manual/scheduled and
real-time) and the web reputation (network scan/filtering).

Currently only the first log is supported.
"""

from __future__ import unicode_literals

from dfdatetime import definitions as dfdatetime_definitions
from dfdatetime import posix_time as dfdatetime_posix_time
from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.formatters import trendmicroav as formatter
from plaso.parsers import dsv_parser
from plaso.parsers import manager


class TrendMicroAVEventData(events.EventData):
  """Trend Micro AV Log event data.

  Attributes:
    action (str): action.
    threat (str): threat.
    filename (str): filename.
    scan_type (str): scan_type.
  """

  DATA_TYPE = 'av:trendmicro:scan'

  def __init__(self):
    """Initializes event data."""
    super(TrendMicroAVEventData, self).__init__(data_type=self.DATA_TYPE)
    self.threat = None
    self.action = None
    self.path = None
    self.filename = None
    self.scan_type = None


# pylint: disable=abstract-method
class TrendMicroBaseParser(dsv_parser.DSVParser):
  """Common code for parsing Trend Micro log files.

    The file format is reminiscent of CSV, but is not quite the same; the
    delimiter is a three-character sequence and there is no provision for
    quoting or escaping.
  """

  DELIMITER = '<;>'

  # Subclasses must define an integer MIN_COLUMNS value.
  MIN_COLUMNS = None

  # Subclasses must define a list of field names.
  COLUMNS = ()

  def __init__(self, *args, **kwargs):
    """Initializes the parser.

    The TrendMicro AV writes a text logfile encoded in the CP1252 charset;
    unless otherwise specified, the parser class needs to know this.
    """
    kwargs.setdefault('encoding', 'cp1252')
    super(TrendMicroBaseParser, self).__init__(*args, **kwargs)

  def _CreateDictReader(self, line_reader):
    """Iterates over the log lines and provide a reader for the values.

    Args:
      line_reader (iter): yields each line in the log file.

    Yields:
      A dictionary of column values keyed by column header.
    """
    for line in line_reader:
      try:
        line = line.decode(self._encoding)
      except UnicodeDecodeError as exception:
        raise errors.UnableToParseFile(
            "Unexpected binary content in file: {0:s}".format(exception))
      stripped_line = line.strip()
      values = stripped_line.split(self.DELIMITER)
      if len(values) < self.MIN_COLUMNS:
        raise errors.UnableToParseFile(
            "Expected at least {0:d} values, found {1:d}".format(
                self.MIN_COLUMNS, len(values)))
      if len(values) > len(self.COLUMNS):
        raise errors.UnableToParseFile(
            "Expected at most {0:d} values, found {1:d}".format(
                len(self.COLUMNS), len(values)))
      yield dict(zip(self.COLUMNS, values))

  def _ParseTimestamp(self, parser_mediator, row):
    """Provides a timestamp for the given row.

    If the Trend Micro log comes from a version that provides a Unix timestamp,
    use that directly; it provides the advantages of UTC and of second
    precision. Otherwise fall back onto the local-timezone date and time.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.

    Returns:
      dfdatetime.interface.DateTimeValue: the parsed timestamp.
    """
    if 'timestamp' in row:
      try:
        return dfdatetime_posix_time.PosixTime(timestamp=int(row['timestamp']))
      except ValueError as exception:
        parser_mediator.ProduceExtractionError(
            'Log line has a timestamp field: [{0:s}], but it is invalid: {1:s}'
            .format(repr(row['timestamp']), exception))

    # The Unix timestamp is not available; parse the local date and time.
    try:
      return self._ConvertToTimestamp(row['date'], row['time'])
    except ValueError as exception:
      parser_mediator.ProduceExtractionError(
          'Unable to parse time string: [{0:s} {1:s}] with error {2:s}'
          .format(repr(row['date']), repr(row['time']), exception))


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
      dfdatetime_time_elements.TimestampElements: the parsed timestamp.

    Raises:
      ValueError: if the date/time values cannot be parsed.
    """
    # Check that the strings have the correct length.
    if len(date) != 8:
      raise ValueError('date has wrong length: len({0!s}) != 8'.format(
          repr(date)))
    if len(time) < 3 or len(time) > 4:
      raise ValueError('time has wrong length: len({0!s}) not in (3, 4)'.format(
          repr(time)))

    # Extract the date.
    year = int(date[:4])
    month = int(date[4:6])
    day = int(date[6:8])

    # Extract the time. Note that a single-digit hour value has no leading zero.
    hour = int(time[:-2])
    minutes = int(time[-2:])

    time_elements_tuple = (year, month, day, hour, minutes, 0)
    date_time = dfdatetime_time_elements.TimeElements(
        time_elements_tuple=time_elements_tuple)
    date_time.is_local_time = True
    # TODO: add functionality to dfdatetime to control precision.
    date_time._precision = dfdatetime_definitions.PRECISION_1_MINUTE  # pylint: disable=protected-access

    return date_time


class OfficeScanVirusDetectionParser(TrendMicroBaseParser):
  """Parses the Trend Micro Office Scan Virus Detection Log."""

  NAME = 'trendmicro_vd'
  DESCRIPTION = 'Parser for Trend Micro Office Scan Virus Detection log files.'

  COLUMNS = [
      'date', 'time', 'threat', 'action', 'scan_type', 'unused1',
      'path', 'filename', 'unused2', 'timestamp', 'unused3', 'unused4']
  MIN_COLUMNS = 8

  def ParseRow(self, parser_mediator, row_offset, row):
    """Parses a line of the log file and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row_offset (int): line number of the row.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.
    """

    timestamp = self._ParseTimestamp(parser_mediator, row)

    if timestamp is None:
      return

    event_data = TrendMicroAVEventData()
    event_data.offset = row_offset
    event_data.threat = row['threat']
    event_data.action = int(row['action'])
    event_data.path = row['path']
    event_data.filename = row['filename']
    event_data.scan_type = int(row['scan_type'])

    event = time_events.DateTimeValuesEvent(
        timestamp, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def VerifyRow(self, parser_mediator, row):
    """Verifies if a line of the file is in the expected format.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    if len(row) < self.MIN_COLUMNS:
      return False

    # Check the date format!
    # If it doesn't parse, then this isn't a Trend Micro AV log.
    timestamp = self._ConvertToTimestamp(row['date'], row['time'])

    if timestamp is None:
      return False

    # Check that the action value is plausible
    try:
      action = int(row['action'])
    except ValueError:
      return False
    if action not in formatter.SCAN_RESULTS:
      return False

    # All checks passed.
    return True


class TrendMicroUrlEventData(events.EventData):
  """Trend Micro Web Reputation Log event data.

  Attributes:
    block_mode (str): operation mode.
    url (str): accessed URL.
    group_code (str): group code.
    group_name (str): group name.
    credibility_rating (int): credibility rating.
    credibility_score (int): credibility score.
    policy_identifier (int): policy identifier.
    application_name (str): application name.
    ip (str): IP address.
    threshold (int): threshold value.
  """
  DATA_TYPE = 'av:trendmicro:webrep'

  def __init__(self):
    """Initializes event data."""
    super(TrendMicroUrlEventData, self).__init__(data_type=self.DATA_TYPE)
    self.block_mode = None
    self.url = None
    self.group_code = None
    self.group_name = None
    self.credibility_rating = None
    self.credibility_score = None
    self.policy_identifier = None
    self.application_name = None
    self.ip = None
    self.threshold = None


class OfficeScanWebReputationParser(TrendMicroBaseParser):
  """Parses the Trend Micro Office Scan Web Reputation detection log."""
  NAME = 'trendmicro_url'
  DESCRIPTION = 'Parser for Trend Micro Office Web Reputation log files.'

  COLUMNS = (
      'date', 'time', 'block_mode', 'url', 'group_code', 'group_name',
      'credibility_rating', 'policy_identifier', 'application_name',
      'credibility_score', 'ip', 'threshold', 'timestamp', 'unused')

  MIN_COLUMNS = 12

  def ParseRow(self, parser_mediator, row_offset, row):
    """Parses a line of the log file and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row_offset (int): line number of the row.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.
    """

    timestamp = self._ParseTimestamp(parser_mediator, row)

    if timestamp is None:
      return

    event_data = TrendMicroUrlEventData()
    event_data.offset = row_offset

    # Convert and store integer values.
    for field in (
        'credibility_rating', 'credibility_score', 'policy_identifier',
        'threshold', 'block_mode'):
      setattr(event_data, field, int(row[field]))

    # Store string values.
    for field in ('url', 'group_name', 'group_code', 'application_name', 'ip'):
      setattr(event_data, field, row[field])

    event = time_events.DateTimeValuesEvent(
        timestamp, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def VerifyRow(self, parser_mediator, row):
    """Verifies if a line of the file is in the expected format.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    if len(row) < self.MIN_COLUMNS:
      return False

    # Check the date format!
    # If it doesn't parse, then this isn't a Trend Micro AV log.
    timestamp = self._ConvertToTimestamp(row['date'], row['time'])

    if timestamp is None:
      return False

    try:
      if int(row['block_mode']) not in formatter.BLOCK_MODES:
        return False
    except ValueError:
      return False

    return True


manager.ParsersManager.RegisterParsers([
    OfficeScanVirusDetectionParser,
    OfficeScanWebReputationParser])
