# -*- coding: utf-8 -*-
"""SQLite parser plugin for iOS Health - All Watch Sleep Data."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IOSHealthAllWatchSleepEventData(events.EventData):
  """iOS Health - All Watch Sleep event data (raw code: 0/1).

  Attributes:
    date_time (dfdatetime.DateTimeValues): primary timestamp (Sleep Start).
    end_date (dfdatetime.DateTimeValues): date and time the sleep ended.
    end_date_str (str): end date formatted as 'YYYY-MM-DD HH:MM:SS+00:00'.
    sleep_state_code (int): sleep state code (0 or 1).
    sleep_state_hms (str): duration of sleep formatted as 'HH:MM:SS'.
    start_date (dfdatetime.DateTimeValues): date and time the sleep started.
    start_date_str (str): start date formatted as 'YYYY-MM-DD HH:MM:SS+00:00'.
  """

  DATA_TYPE = 'ios:health:all_watch_sleep'

  def __init__(self):
    """Initializes event data."""
    super(IOSHealthAllWatchSleepEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.date_time = None
    self.end_date = None
    self.end_date_str = None
    self.sleep_state_code = None
    self.sleep_state_hms = None
    self.start_date = None
    self.start_date_str = None


class IOSHealthAllWatchSleepPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for iOS Health - All Watch Sleep Data (iOS 13–16)."""

  NAME = 'ios_health_all_watch_sleep_data'
  DATA_FORMAT = (
      'iOS Health Sleep (Apple Watch) from healthdb_secure.sqlite (iOS 13–16)')

  REQUIRED_STRUCTURE = {
      'samples': frozenset(['data_id', 'start_date', 'end_date', 'data_type']),
      'category_samples': frozenset(['data_id', 'value']),
      'objects': frozenset(['data_id', 'provenance']),
      'data_provenances': frozenset(['origin_product_type'])}

  QUERIES = [(
      'SELECT s.start_date AS start_cocoa, s.end_date AS end_cocoa, '
      'cs.value AS state_code FROM samples s '
      'LEFT JOIN category_samples cs ON s.data_id = cs.data_id '
      'LEFT JOIN objects o ON s.data_id = o.data_id '
      'LEFT JOIN data_provenances dp ON o.provenance = dp.rowid '
      'AND dp.origin_product_type LIKE "%Watch%" '
      'WHERE s.data_type IN (63, "63") AND cs.value IN (0, 1) '
      'ORDER BY s.start_date ASC',
      'ParseSleepRow')]

  def _GetCocoaDateTime(self, query_hash, row, value_name):
    """Retrieves a Cocoa Time value from the row.

    Args:
      query_hash (int): hash of the query.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.CocoaTime: Date and time value or None.
    """
    ts = self._GetRowValue(query_hash, row, value_name)
    if ts is None:
      return None
    return dfdatetime_cocoa_time.CocoaTime(timestamp=ts)

  def _RFC3339Space(self, dfdt):
    """Formats a dfdatetime object to a string with space instead of 'T'.

    Args:
      dfdt (dfdatetime.DateTimeValues): date time value.

    Returns:
      str: formatted date time string or None.
    """
    if dfdt is None:
      return None
    # We catch AttributeError to handle cases where dfdt is not formatted.
    try:
      fn = getattr(dfdt, 'CopyToDateTimeStringRFC3339', None)
      s = fn() if callable(fn) else dfdt.CopyToDateTimeString()
      return s.replace('T', ' ')
    except (AttributeError, ValueError, TypeError):
      return None

  @staticmethod
  def _SecondsToHMS(seconds_value):
    """Converts seconds to HH:MM:SS format.

    Args:
      seconds_value (int|float): total seconds.

    Returns:
      str: formatted string or None.
    """
    try:
      total = int(float(seconds_value))
    except (TypeError, ValueError):
      return None
    hh = total // 3600
    mm = (total % 3600) // 60
    ss = total % 60
    return f'{hh:02d}:{mm:02d}:{ss:02d}'

  def ParseSleepRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a sleep data row.

    Args:
      parser_mediator (ParserMediator): mediates interactions.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    qh = hash(query)
    event_data = IOSHealthAllWatchSleepEventData()

    start_dt = self._GetCocoaDateTime(qh, row, 'start_cocoa')
    end_dt = self._GetCocoaDateTime(qh, row, 'end_cocoa')

    event_data.date_time = start_dt
    event_data.start_date = start_dt
    event_data.end_date = end_dt
    event_data.start_date_str = self._RFC3339Space(start_dt)
    event_data.end_date_str = self._RFC3339Space(end_dt)
    event_data.sleep_state_code = self._GetRowValue(qh, row, 'state_code')

    duration_seconds = None
    if start_dt and end_dt:
      try:
        duration_seconds = end_dt.timestamp - start_dt.timestamp
      except (AttributeError, TypeError):
        duration_seconds = None
    event_data.sleep_state_hms = self._SecondsToHMS(duration_seconds)

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(IOSHealthAllWatchSleepPlugin)
