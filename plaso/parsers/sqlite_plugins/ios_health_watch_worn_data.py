# -*- coding: utf-8 -*-
"""SQLite parser plugin for iOS Health Watch Worn Data."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IOSHealthWatchWornEventData(events.EventData):
  """iOS Health Watch Worn Data event.

  Attributes:
    date_time (dfdatetime.DateTimeValues): primary timestamp for timeline.
    hours_off_before_next (int): hours the watch was off before the next period.
    hours_worn (int): total hours the watch was worn.
    last_worn_time_str (str): rendered last worn time string.
    start_time_str (str): rendered start time string.
  """

  DATA_TYPE = 'ios:health:watch_worn'

  def __init__(self):
    """Initializes event data."""
    super(IOSHealthWatchWornEventData, self).__init__(data_type=self.DATA_TYPE)
    self.date_time = None
    self.hours_off_before_next = None
    self.hours_worn = None
    self.last_worn_time_str = None
    self.start_time_str = None


class IOSHealthWatchWornPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for iOS Health Watch Worn Data."""

  NAME = 'ios_health_watch_worn_data'
  DATA_FORMAT = 'iOS Health Watch Worn Data from healthdb_secure.sqlite'

  REQUIRED_STRUCTURE = {
      'samples': frozenset(['start_date', 'end_date', 'data_type'])}

  QUERIES = [((
      'WITH TimeData AS (SELECT s.start_date AS start_cocoa, s.end_date AS '
      'end_cocoa, LAG(s.end_date) OVER (ORDER BY s.start_date) AS '
      'prev_end_cocoa FROM samples s WHERE s.data_type IN (70, "70")), '
      'PeriodData AS (SELECT *, (start_cocoa - prev_end_cocoa) AS gap_seconds, '
      'CASE WHEN (start_cocoa - prev_end_cocoa) > 3600 THEN 1 ELSE 0 END AS '
      'new_period FROM TimeData), PeriodGroup AS (SELECT *, SUM(new_period) '
      'OVER (ORDER BY start_cocoa ROWS BETWEEN UNBOUNDED PRECEDING AND '
      'CURRENT ROW) AS period_id FROM PeriodData), Summary AS (SELECT '
      'period_id, MIN(start_cocoa) AS period_start_cocoa, MAX(end_cocoa) AS '
      'period_end_cocoa, CAST((MAX(end_cocoa) - MIN(start_cocoa)) / 3600 AS '
      'INT) AS hours_worn FROM PeriodGroup GROUP BY period_id) SELECT '
      's1.period_start_cocoa AS start_cocoa, s1.hours_worn AS hours_worn, '
      's1.period_end_cocoa AS end_cocoa, CAST((s2.period_start_cocoa - '
      's1.period_end_cocoa) / 3600 AS INT) AS hours_off_before_next FROM '
      'Summary s1 LEFT JOIN Summary s2 ON s1.period_id + 1 = s2.period_id '
      'ORDER BY s1.period_id'),
      'ParseWatchWornRow')]

  SCHEMAS = {
      'samples': (
          'CREATE TABLE samples (data_id INTEGER PRIMARY KEY, start_date '
          'INTEGER, end_date INTEGER, data_type TEXT)')}

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
    except (ValueError, TypeError):
      return None

  def _CopyToRfc3339String(self, dfdt):
    """Returns RFC3339/ISO string from a dfdatetime object.

    Args:
      dfdt (dfdatetime.DateTimeValues): date time value.

    Returns:
      str: formatted date time string or None.
    """
    if dfdt is None:
      return None
    try:
      to_rfc3339 = getattr(dfdt, 'CopyToDateTimeStringRFC3339', None)
      if callable(to_rfc3339):
        return to_rfc3339()
      return dfdt.CopyToDateTimeString()
    except (AttributeError, TypeError, ValueError):
      return None

  def ParseWatchWornRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a Watch Worn summary row (one worn period).

    Args:
      parser_mediator (ParserMediator): mediates interactions.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)
    event_data = IOSHealthWatchWornEventData()

    start_dt = self._GetCocoaDateTime(query_hash, row, 'start_cocoa')
    end_dt = self._GetCocoaDateTime(query_hash, row, 'end_cocoa')

    event_data.date_time = start_dt
    event_data.start_time_str = self._CopyToRfc3339String(start_dt)
    event_data.last_worn_time_str = self._CopyToRfc3339String(end_dt)
    event_data.hours_worn = self._GetRowValue(query_hash, row, 'hours_worn')
    event_data.hours_off_before_next = self._GetRowValue(
        query_hash, row, 'hours_off_before_next')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(IOSHealthWatchWornPlugin)
