# -*- coding: utf-8 -*-
"""SQLite parser plugin for iOS Health - All Watch Sleep Data (iOS 17)."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IOSHealthAllWatchSleepLatestEventData(events.EventData):
  """iOS Health - All Watch Sleep (stages) event data.

  Attributes:
    date_time (dfdatetime.DateTimeValues): primary timestamp (Sleep Start).
    end_date (dfdatetime.DateTimeValues): date and time the sleep ended.
    end_date_str (str): end date formatted as 'YYYY-MM-DD HH:MM:SS+00:00'.
    sleep_state_code (int): sleep state code (stages 2-5).
    sleep_state_hms (str): duration of sleep formatted as 'HH:MM:SS'.
    start_date (dfdatetime.DateTimeValues): date and time the sleep started.
    start_date_str (str): start date formatted as 'YYYY-MM-DD HH:MM:SS+00:00'.
  """

  DATA_TYPE = 'ios:health:all_watch_sleep_latest'

  def __init__(self):
    """Initializes event data."""
    super(IOSHealthAllWatchSleepLatestEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.date_time = None
    self.end_date = None
    self.end_date_str = None
    self.sleep_state_code = None
    self.sleep_state_hms = None
    self.start_date = None
    self.start_date_str = None


class IOSHealthAllWatchSleepLatestPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for iOS Health Sleep Stages (iOS 17+)."""

  NAME = 'ios_health_all_watch_sleep_latest'
  DATA_FORMAT = 'iOS Health Sleep Stages from healthdb_secure.sqlite (iOS 17+)'

  REQUIRED_STRUCTURE = {
      'samples': frozenset(['data_id', 'start_date', 'end_date']),
      'category_samples': frozenset(['data_id', 'value'])}

  QUERIES = [(
      'SELECT s.start_date AS start_cocoa, s.end_date AS end_cocoa, '
      'cs.value AS state_code FROM samples s '
      'JOIN category_samples cs ON s.data_id = cs.data_id '
      'ORDER BY s.start_date ASC',
      'ParseSleepRow')]

  def _GetCocoaDateTime(self, qh, row, name):
    """Retrieves a Cocoa Time value from the row.

    Args:
      qh (int): hash of the query.
      row (sqlite3.Row): row.
      name (str): name of the value.

    Returns:
      dfdatetime.CocoaTime: Date and time value or None.
    """
    ts = self._GetRowValue(qh, row, name)
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
    try:
      fn = getattr(dfdt, 'CopyToDateTimeStringRFC3339', None)
      s = fn() if callable(fn) else dfdt.CopyToDateTimeString()
      return s.replace('T', ' ')
    except (AttributeError, TypeError, ValueError):
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

    raw_code = self._GetRowValue(qh, row, 'state_code')
    try:
      code = int(raw_code) if raw_code is not None else None
    except (TypeError, ValueError):
      code = None

    if code not in (2, 3, 4, 5):
      return

    ed = IOSHealthAllWatchSleepLatestEventData()

    start_dt = self._GetCocoaDateTime(qh, row, 'start_cocoa')
    end_dt = self._GetCocoaDateTime(qh, row, 'end_cocoa')

    ed.date_time = start_dt
    ed.start_date = start_dt
    ed.end_date = end_dt
    ed.start_date_str = self._RFC3339Space(start_dt)
    ed.end_date_str = self._RFC3339Space(end_dt)
    ed.sleep_state_code = code

    dur = None
    if start_dt and end_dt:
      try:
        dur = end_dt.timestamp - start_dt.timestamp
      except (AttributeError, TypeError):
        dur = None
    ed.sleep_state_hms = self._SecondsToHMS(dur)

    parser_mediator.ProduceEventData(ed)


sqlite.SQLiteParser.RegisterPlugin(IOSHealthAllWatchSleepLatestPlugin)
