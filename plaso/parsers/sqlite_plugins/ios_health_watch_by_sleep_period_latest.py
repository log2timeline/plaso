# -*- coding: utf-8 -*-
"""SQLite parser plugin for iOS Health - Watch By Sleep Period Data."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IOSHealthWatchBySleepPeriodLatestEventData(events.EventData):
  """iOS Health - Watch By Sleep Period event data.

  Attributes:
    awake_duration (float): duration spent awake in minutes.
    awake_duration_hms (str): duration spent awake in HH:MM:SS.
    awake_percent (float): percentage of time spent awake.
    core_duration (float): duration spent in core sleep in minutes.
    core_duration_hms (str): duration spent in core sleep in HH:MM:SS.
    core_percent (float): percentage of time spent in core sleep.
    date_time (dfdatetime.DateTimeValues): primary timestamp (start).
    deep_duration (float): duration spent in deep sleep in minutes.
    deep_duration_hms (str): duration spent in deep sleep in HH:MM:SS.
    deep_percent (float): percentage of time spent in deep sleep.
    end_date (dfdatetime.DateTimeValues): date and time sleep ended.
    end_date_str (str): rendered end date string.
    rem_duration (float): duration spent in REM sleep in minutes.
    rem_duration_hms (str): duration spent in REM sleep in HH:MM:SS.
    rem_percent (float): percentage of time spent in REM sleep.
    start_date (dfdatetime.DateTimeValues): date and time sleep started.
    start_date_str (str): rendered start date string.
    total_duration (float): total duration of the sleep period in minutes.
  """

  DATA_TYPE = 'ios:health:watch_by_sleep_period_latest'

  def __init__(self):
    """Initializes event data."""
    super(IOSHealthWatchBySleepPeriodLatestEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.awake_duration = None
    self.awake_duration_hms = None
    self.awake_percent = None
    self.core_duration = None
    self.core_duration_hms = None
    self.core_percent = None
    self.date_time = None
    self.deep_duration = None
    self.deep_duration_hms = None
    self.deep_percent = None
    self.end_date = None
    self.end_date_str = None
    self.rem_duration = None
    self.rem_duration_hms = None
    self.rem_percent = None
    self.start_date = None
    self.start_date_str = None
    self.total_duration = None


class IOSHealthWatchBySleepPeriodLatestPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for iOS Health Watch By Sleep Period (iOS 17+)."""

  NAME = 'ios_health_watch_by_sleep_period_latest'
  DATA_FORMAT = (
      'iOS Health Watch By Sleep Period Data from healthdb_secure.sqlite '
      '(iOS 17+)')

  REQUIRED_STRUCTURE = {
      'samples': frozenset(['data_id', 'start_date', 'end_date']),
      'category_samples': frozenset(['data_id', 'value']),
      'data_provenances': frozenset(['origin_product_type']),
      'objects': frozenset(['data_id'])}

  QUERIES = [((
      'WITH lagged_samples AS (SELECT s.start_date, s.end_date, s.data_id, '
      's.data_type, cs.value, LAG(s.data_id) OVER (ORDER BY s.data_id) AS '
      'prev_data_id, CASE WHEN cs.value = 2 THEN "AWAKE" WHEN cs.value = 3 '
      'THEN "CORE" WHEN cs.value = 4 THEN "DEEP" WHEN cs.value = 5 THEN "REM" '
      'END AS sleep_value FROM samples s LEFT JOIN category_samples cs ON '
      's.data_id = cs.data_id LEFT JOIN objects o ON s.data_id = o.data_id '
      'LEFT JOIN data_provenances dp ON o.provenance = dp.rowid WHERE '
      's.data_type = 63 AND cs.value NOT IN (0, 1) AND dp.origin_product_type '
      'LIKE "%Watch%"), grouped_samples AS (SELECT *, CASE WHEN data_id - '
      'prev_data_id > 1 OR prev_data_id IS NULL THEN 1 ELSE 0 END AS '
      'is_new_group, SUM(CASE WHEN data_id - prev_data_id > 1 OR '
      'prev_data_id IS NULL THEN 1 ELSE 0 END) OVER (ORDER BY data_id) AS '
      'group_number FROM lagged_samples) SELECT MIN(start_date) AS start_date, '
      'MAX(end_date) AS end_date, SUM(CASE WHEN sleep_value IN ("AWAKE", '
      '"REM", "CORE", "DEEP") THEN (end_date - start_date) / 60.0 ELSE 0 END) '
      'AS total_duration, SUM(CASE WHEN sleep_value = "AWAKE" THEN '
      '(end_date - start_date) / 60.0 ELSE 0 END) AS awake_duration, SUM(CASE '
      'WHEN sleep_value = "REM" THEN (end_date - start_date) / 60.0 ELSE 0 '
      'END) AS rem_duration, SUM(CASE WHEN sleep_value = "CORE" THEN '
      '(end_date - start_date) / 60.0 ELSE 0 END) AS core_duration, SUM(CASE '
      'WHEN sleep_value = "DEEP" THEN (end_date - start_date) / 60.0 ELSE 0 '
      'END) AS deep_duration FROM grouped_samples GROUP BY group_number '
      'ORDER BY MIN(start_date) ASC'),
      'ParseSleepRow')]

  SCHEMAS = {
      'samples': (
          'CREATE TABLE samples (data_id INTEGER PRIMARY KEY, start_date '
          'INTEGER, end_date INTEGER, data_type TEXT)'),
      'category_samples': (
          'CREATE TABLE category_samples (data_id INTEGER PRIMARY KEY, value '
          'INTEGER)'),
      'data_provenances': (
          'CREATE TABLE data_provenances (rowid INTEGER PRIMARY KEY, '
          'origin_product_type TEXT)'),
      'objects': (
          'CREATE TABLE objects (data_id INTEGER PRIMARY KEY, provenance '
          'INTEGER)')}

  REQUIRE_SCHEMA_MATCH = False

  def _GetCocoaDateTime(self, query_hash, row, value_name):
    """Returns dfdatetime.CocoaTime from a numeric Cocoa timestamp.

    Args:
      query_hash (int): hash of the query.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.CocoaTime: date and time value or None.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if timestamp is None:
      return None
    try:
      ts_float = float(timestamp)
      if ts_float == 0:
        return None
      return dfdatetime_cocoa_time.CocoaTime(timestamp=ts_float)
    except (TypeError, ValueError):
      return None

  def _CopyToRfc3339String(self, dfdt):
    """Returns RFC3339 string from a dfdatetime object or None.

    Args:
      dfdt (dfdatetime.DateTimeValues): date time value.

    Returns:
      str: formatted date time string or None.
    """
    if dfdt is None:
      return None
    try:
      return getattr(
          dfdt, 'CopyToDateTimeStringRFC3339', dfdt.CopyToDateTimeString)()
    except (AttributeError, TypeError, ValueError):
      return None

  @staticmethod
  def _SecondsToHMS(minutes_value):
    """Convert minutes to HH:MM:SS string.

    Args:
      minutes_value (float): number of minutes.

    Returns:
      str: formatted HH:MM:SS string.
    """
    try:
      total_seconds = int(float(minutes_value) * 60)
    except (TypeError, ValueError):
      return '00:00:00'
    hh = total_seconds // 3600
    mm = (total_seconds % 3600) // 60
    ss = total_seconds % 60
    return f'{hh:02d}:{mm:02d}:{ss:02d}'

  @staticmethod
  def _CalculatePercent(part, total):
    """Calculates percentage.

    Args:
      part (float): part value.
      total (float): total value.

    Returns:
      float: calculated percentage.
    """
    try:
      return round((float(part) / float(total)) * 100, 2) if total else 0.0
    except (TypeError, ValueError):
      return 0.0

  def ParseSleepRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a Watch By Sleep Period row.

    Args:
      parser_mediator (ParserMediator): mediates interactions.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    if not row:
      return

    qh = hash(query)
    event_data = IOSHealthWatchBySleepPeriodLatestEventData()

    start_dt = self._GetCocoaDateTime(qh, row, 'start_date')
    end_dt = self._GetCocoaDateTime(qh, row, 'end_date')
    event_data.start_date = start_dt
    event_data.end_date = end_dt
    event_data.start_date_str = self._CopyToRfc3339String(start_dt)
    event_data.end_date_str = self._CopyToRfc3339String(end_dt)
    event_data.date_time = start_dt

    event_data.total_duration = self._GetRowValue(qh, row, 'total_duration')
    event_data.awake_duration = self._GetRowValue(qh, row, 'awake_duration')
    event_data.rem_duration = self._GetRowValue(qh, row, 'rem_duration')
    event_data.core_duration = self._GetRowValue(qh, row, 'core_duration')
    event_data.deep_duration = self._GetRowValue(qh, row, 'deep_duration')

    event_data.awake_duration_hms = self._SecondsToHMS(
        event_data.awake_duration)
    event_data.rem_duration_hms = self._SecondsToHMS(event_data.rem_duration)
    event_data.core_duration_hms = self._SecondsToHMS(event_data.core_duration)
    event_data.deep_duration_hms = self._SecondsToHMS(event_data.deep_duration)

    total = event_data.total_duration or 1
    event_data.awake_percent = self._CalculatePercent(
        event_data.awake_duration, total)
    event_data.rem_percent = self._CalculatePercent(
        event_data.rem_duration, total)
    event_data.core_percent = self._CalculatePercent(
        event_data.core_duration, total)
    event_data.deep_percent = self._CalculatePercent(
        event_data.deep_duration, total)

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(IOSHealthWatchBySleepPeriodLatestPlugin)
