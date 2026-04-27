# -*- coding: utf-8 -*-
"""SQLite parser plugin for iOS Health Weight database."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IOSHealthWeightEventData(events.EventData):
  """iOS Health Weight event data.

  Attributes:
    date_time (dfdatetime.DateTimeValues): primary timestamp.
    weight_kg_str (str): Weight in Kilograms (e.g., '81.64').
    weight_lbs_str (str): Weight in Pounds (e.g., '180.00').
    weight_stone_str (str): Weight in Stone/Pounds (e.g., '12 Stone 12 Pounds').
    weight_value_ts_str (str): ISO string (e.g., "YYYY-MM-DD HH:MM:SS+00:00").
  """

  DATA_TYPE = 'ios:health:weight'

  def __init__(self):
    """Initializes event data."""
    super(IOSHealthWeightEventData, self).__init__(data_type=self.DATA_TYPE)
    self.date_time = None
    self.weight_kg_str = None
    self.weight_lbs_str = None
    self.weight_stone_str = None
    self.weight_value_ts_str = None


class IOSHealthWeightPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for iOS Health Weight database."""

  NAME = 'ios_health_weight'
  DATA_FORMAT = (
      'iOS Health Weight SQLite database file healthdb_secure.sqlite')

  REQUIRED_STRUCTURE = {
      'samples': frozenset(['data_id', 'start_date', 'data_type']),
      'quantity_samples': frozenset(['data_id', 'quantity'])}

  QUERIES = [((
      'SELECT t.start_date AS start_date, t.kg_str AS weight_kg_str, '
      't.stone_int AS stone_int, t.pounds_int AS pounds_int, '
      't.lbs_str AS weight_lbs_str FROM (SELECT s.start_date AS start_date, '
      'substr(qs.quantity, 1, 5) AS kg_str, CAST(qs.quantity / 6.35029317 AS '
      'INT) AS stone_int, CAST((((qs.quantity / 6.35029317) - '
      'CAST(qs.quantity / 6.35029317 AS INT)) * 14) + 0.5 AS INT) AS '
      'pounds_int, substr(qs.quantity * 2.20462262, 1, 6) AS lbs_str FROM '
      'samples s JOIN quantity_samples qs ON s.data_id = qs.data_id WHERE '
      's.data_type IN (3, "3") AND qs.quantity IS NOT NULL) t ORDER BY '
      't.start_date DESC'),
      'ParseWeightRow')]

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a Cocoa DateTime value from the row.

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
    return dfdatetime_cocoa_time.CocoaTime(timestamp=timestamp)

  def _CopyToRfc3339String(self, dfdt):
    """Returns RFC3339/ISO string from a dfdatetime object or None.

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
        s = to_rfc3339()
      else:
        s = dfdt.CopyToDateTimeString()
      return s.replace('T', ' ')
    except (AttributeError, TypeError, ValueError):
      return None

  @staticmethod
  def _FormatStonePounds(stone_int, pounds_int):
    """Formats 'X Stone Y Pounds' with carry handling.

    Args:
      stone_int (int): weight in stone.
      pounds_int (int): weight in pounds.

    Returns:
      str: formatted weight string or None.
    """
    try:
      s = int(stone_int) if stone_int is not None else 0
      p = int(pounds_int) if pounds_int is not None else 0
      if p == 14:
        s += 1
        p = 0
      return f'{s} Stone {p} Pounds'
    except (TypeError, ValueError):
      return None

  def ParseWeightRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a weight row (single timestamp with 3 value fields).

    Args:
      parser_mediator (ParserMediator): mediates interactions.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)
    event_data = IOSHealthWeightEventData()

    event_data.date_time = self._GetDateTimeRowValue(
        query_hash, row, 'start_date')
    event_data.weight_value_ts_str = self._CopyToRfc3339String(
        event_data.date_time)
    event_data.weight_kg_str = self._GetRowValue(
        query_hash, row, 'weight_kg_str')
    event_data.weight_lbs_str = self._GetRowValue(
        query_hash, row, 'weight_lbs_str')

    stone_int = self._GetRowValue(query_hash, row, 'stone_int')
    pounds_int = self._GetRowValue(query_hash, row, 'pounds_int')
    event_data.weight_stone_str = self._FormatStonePounds(stone_int, pounds_int)

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(IOSHealthWeightPlugin)
