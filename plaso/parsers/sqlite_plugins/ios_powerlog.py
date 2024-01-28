# -*- coding: utf-8 -*-
"""SQLite parser plugin for iOS powerlog database files."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IOSPowerlogApplicationUsageEventData(events.EventData):
  """iOS powerlog file application usage event data.

  Attributes:
    background_time (str): Number of seconds that the application ran in the
        background.
    bundle_identifier (str): Name of the application.
    screen_on_time (str): Number of seconds that the application ran in the
        foreground.
    start_time (dfdatetime.DateTimeValues): date and time the start of
        the application.
  """

  DATA_TYPE = 'ios:powerlog:application_usage'

  def __init__(self):
    """Initializes event data."""
    super(IOSPowerlogApplicationUsageEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.background_time = None
    self.bundle_identifier = None
    self.screen_on_time = None
    self.start_time = None


class IOSPowerlogApplicationUsagePlugin(interface.SQLitePlugin):
  """SQLite parser plugin for iOS powerlog database files."""

  NAME = 'ios_powerlog'
  DATA_FORMAT = 'iOS powerlog SQLite database (CurrentPowerlog.PLSQL) file'

  REQUIRED_STRUCTURE = {
      'PLAppTimeService_Aggregate_AppRunTime': frozenset([
          'timestamp', 'BackgroundTime', 'BundleID', 'ScreenOnTime'])}

  QUERIES = [(
      'SELECT timestamp, BackgroundTime, ScreenOnTime, BundleID FROM '
      'PLAppTimeService_Aggregate_AppRunTime', 'ParseApplicationRunTime')]

  SCHEMAS = {
      'PLAppTimeService_Aggregate_AppRunTime': (
          'CREATE TABLE PLAppTimeService_Aggregate_AppRunTime (id INTEGER '
          'PRIMARY KEY AUTOINCREMENT, timestamp REAL, timeInterval REAL, '
          'BackgroundAudioNowPlayingPluggedInTime REAL, '
          'BackgroundAudioNowPlayingTime REAL, BackgroundAudioPlayingTime REAL,'
          ' BackgroundAudioPlayingTimePluggedIn REAL, '
          'BackgroundLocationAudioPluggedInTime REAL, '
          'BackgroundLocationAudioTime REAL, '
          'BackgroundLocationPluggedInTime REAL, BackgroundLocationTime REAL, '
          'BackgroundPluggedInTime REAL, BackgroundTime REAL, BundleID TEXT, '
          'ScreenOnPluggedInTime REAL, ScreenOnTime REAL)')}

  REQUIRES_SCHEMA_MATCH = False

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a date and time value from the row.

    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.PosixTime: date and time value or None if not available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if timestamp is None:
      return None

    return dfdatetime_posix_time.PosixTime(timestamp=timestamp)

  # pylint: disable=unused-argument
  def ParseApplicationRunTime(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses an Application Run Time row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = IOSPowerlogApplicationUsageEventData()
    event_data.background_time = self._GetRowValue(
        query_hash, row, 'BackgroundTime')
    event_data.bundle_identifier = self._GetRowValue(
        query_hash, row, 'BundleID')
    event_data.screen_on_time = self._GetRowValue(
        query_hash, row, 'ScreenOnTime')
    event_data.start_time = self._GetDateTimeRowValue(
        query_hash, row, 'timestamp')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(IOSPowerlogApplicationUsagePlugin)
