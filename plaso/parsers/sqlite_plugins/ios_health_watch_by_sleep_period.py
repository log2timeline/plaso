# -*- coding: utf-8 -*-
"""SQLite parser plugin for iOS Health - Watch By Sleep Period Data."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IOSHealthWatchBySleepPeriodEventData(events.EventData):
  """iOS Health - Watch By Sleep Period event data.

  Attributes:
    asleep_percent (float): percentage of time spent asleep.
    data_type_id (int): internal iOS data type identifier.
    date_time (dfdatetime.DateTimeValues): primary timestamp (start).
    device_name (str): name of the recording device.
    end_date_str (str): rendered end date string.
    in_bed_duration_hms (str): duration spent in bed in HH:MM:SS.
    in_bed_percent (float): percentage of time spent in bed.
    start_date_str (str): rendered start date string.
    time_in_bed_hms (str): total time in bed in HH:MM:SS.
  """

  DATA_TYPE = 'ios:health:watch_by_sleep_period'

  def __init__(self):
    """Initializes event data."""
    super(IOSHealthWatchBySleepPeriodEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.asleep_percent = None
    self.data_type_id = None
    self.date_time = None
    self.device_name = None
    self.end_date_str = None
    self.in_bed_duration_hms = None
    self.in_bed_percent = None
    self.start_date_str = None
    self.time_in_bed_hms = None


class IOSHealthWatchBySleepPeriodPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for iOS Health Watch By Sleep Period Data."""

  NAME = 'ios_health_watch_by_sleep_period'
  DATA_FORMAT = (
      'iOS Health Watch By Sleep Period Data from healthdb_secure.sqlite '
      '(iOS 15-17)')

  REQUIRED_STRUCTURE = {
      'samples': frozenset(['data_id', 'start_date', 'end_date', 'data_type']),
      'category_samples': frozenset(['data_id', 'value']),
      'data_provenances': frozenset(['origin_product_type']),
      'objects': frozenset(['data_id', 'provenance'])}

  QUERIES = [((
      'WITH lagged_samples AS (SELECT s.data_id, s.start_date, s.end_date, '
      '(s.end_date - s.start_date) / 60 AS duration_minutes, s.data_type, '
      'cs.value, dp.origin_product_type, LAG(s.data_id) OVER (ORDER BY '
      's.data_id) AS prev_data_id, CASE cs.value WHEN 0 THEN "IN BED" '
      'WHEN 1 THEN "ASLEEP" END AS sleep_value FROM samples s LEFT JOIN '
      'category_samples cs ON s.data_id = cs.data_id LEFT JOIN objects o '
      'ON s.data_id = o.data_id LEFT JOIN data_provenances dp ON '
      'o.provenance = dp.rowid WHERE s.data_type = 63 AND cs.value IN (0, 1) '
      'AND dp.origin_product_type LIKE "%Watch%"), grouped_samples AS ('
      'SELECT *, CASE WHEN prev_data_id IS NULL OR data_id - prev_data_id > 1 '
      'THEN 1 ELSE 0 END AS is_new_group, SUM(CASE WHEN prev_data_id IS NULL '
      'OR data_id - prev_data_id > 1 THEN 1 ELSE 0 END) OVER (ORDER BY '
      'data_id) AS group_number FROM lagged_samples) SELECT MIN(start_date) '
      'AS start_date, MAX(end_date) AS end_date, MAX(data_type) AS '
      'data_type_id, MAX(origin_product_type) AS device_name, SUM(CASE WHEN '
      'sleep_value IN ("IN BED", "ASLEEP") THEN duration_minutes ELSE 0 END) '
      'AS total_duration, SUM(CASE WHEN sleep_value = "IN BED" THEN '
      'duration_minutes ELSE 0 END) AS in_bed_duration, CASE WHEN '
      'SUM(duration_minutes) > 0 THEN ROUND(SUM(CASE WHEN sleep_value = '
      '"IN BED" THEN duration_minutes ELSE 0 END) * 100.0 / '
      'SUM(duration_minutes), 2) ELSE 0 END AS in_bed_percent, CASE WHEN '
      'SUM(duration_minutes) > 0 THEN ROUND(SUM(CASE WHEN sleep_value = '
      '"ASLEEP" THEN duration_minutes ELSE 0 END) * 100.0 / '
      'SUM(duration_minutes), 2) ELSE 0 END AS asleep_percent FROM '
      'grouped_samples GROUP BY group_number ORDER BY MIN(start_date) ASC'),
      'ParseSleepRowInBed')]

  @staticmethod
  def _MinutesToHMS(minutes_value):
    """Convert minutes to HH:MM:SS string.

    Args:
      minutes_value (float): number of minutes.

    Returns:
      str: formatted HH:MM:SS string.
    """
    if not minutes_value:
      return '00:00:00'
    total_seconds = int(minutes_value * 60)
    hh = total_seconds // 3600
    mm = (total_seconds % 3600) // 60
    ss = total_seconds % 60
    return f'{hh:02d}:{mm:02d}:{ss:02d}'

  def ParseSleepRowInBed(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a single row from the SQL query and produces an event.

    Args:
      parser_mediator (ParserMediator): mediates interactions.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)
    ed = IOSHealthWatchBySleepPeriodEventData()

    start_ts = self._GetRowValue(query_hash, row, 'start_date')
    end_ts = self._GetRowValue(query_hash, row, 'end_date')

    if start_ts:
      ed.date_time = dfdatetime_cocoa_time.CocoaTime(timestamp=start_ts)
      ed.start_date_str = ed.date_time.CopyToDateTimeString()

    if end_ts:
      end_date = dfdatetime_cocoa_time.CocoaTime(timestamp=end_ts)
      ed.end_date_str = end_date.CopyToDateTimeString()

    ed.data_type_id = self._GetRowValue(query_hash, row, 'data_type_id')
    ed.device_name = self._GetRowValue(query_hash, row, 'device_name')

    total_duration = self._GetRowValue(query_hash, row, 'total_duration')
    in_bed_duration = self._GetRowValue(query_hash, row, 'in_bed_duration')

    ed.time_in_bed_hms = self._MinutesToHMS(total_duration)
    ed.in_bed_duration_hms = self._MinutesToHMS(in_bed_duration)
    ed.in_bed_percent = self._GetRowValue(query_hash, row, 'in_bed_percent')
    ed.asleep_percent = self._GetRowValue(query_hash, row, 'asleep_percent')

    parser_mediator.ProduceEventData(ed)


sqlite.SQLiteParser.RegisterPlugin(IOSHealthWatchBySleepPeriodPlugin)
