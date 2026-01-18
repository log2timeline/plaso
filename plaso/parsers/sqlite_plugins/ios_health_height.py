# -*- coding: utf-8 -*-
"""SQLite parser plugin for iOS Health Height database."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IOSHealthHeightEventData(events.EventData):
  """iOS Health Height event data.

  Attributes:
    date_time (dfdatetime.DateTimeValues): primary timestamp for timeline.
    height_cm (int): height in centimeters (integer).
    height_ft_in (str): height in feet and inches (e.g., 5'10").
    height_m (float): height in meters.
    height_value_ts_str (str): ISO/RFC3339 string derived from date_time.
  """

  DATA_TYPE = 'ios:health:height'

  def __init__(self):
    """Initializes event data."""
    super(IOSHealthHeightEventData, self).__init__(data_type=self.DATA_TYPE)
    self.date_time = None
    self.height_cm = None
    self.height_ft_in = None
    self.height_m = None
    self.height_value_ts_str = None


class IOSHealthHeightPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for iOS Health Height database."""

  NAME = 'ios_health_height'
  DATA_FORMAT = (
      'iOS Health Height SQLite database file healthdb_secure.sqlite')

  REQUIRED_STRUCTURE = {
      'samples': frozenset(['data_id', 'start_date', 'data_type']),
      'quantity_samples': frozenset(['data_id', 'quantity'])}

  QUERIES = [((
      'SELECT samples.start_date AS start_date, quantity_samples.quantity AS '
      'height_meters FROM samples LEFT JOIN quantity_samples ON '
      'samples.data_id = quantity_samples.data_id WHERE samples.data_type = 2 '
      'AND quantity_samples.quantity IS NOT NULL ORDER BY samples.start_date '
      'DESC'),
      'ParseHeightRow')]

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a Cocoa DateTime value from the row.

    Args:
      query_hash (int): hash of the query.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.CocoaTime: Date and time value or None.
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
  def _MetersToCentimetersInt(meters):
    """Converts meters to integer centimeters.

    Args:
      meters (float): height in meters.

    Returns:
      int: height in centimeters or None.
    """
    try:
      return int(meters * 100)
    except (TypeError, ValueError):
      return None

  @staticmethod
  def _MetersToFeetInches(meters):
    """Converts meters to a feet'inches string like 5'10".

    Args:
      meters (float): height in meters.

    Returns:
      str: height in feet'inches or None.
    """
    if meters is None:
      return None
    try:
      feet_float = meters * 3.280839895
      feet = int(feet_float)
      inches = int((feet_float - feet) * 12 + 0.5)
      if inches == 12:
        feet += 1
        inches = 0
      return f"{feet}'{inches}\""
    except (TypeError, ValueError):
      return None

  def ParseHeightRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a height row (single timestamp).

    Args:
      parser_mediator (ParserMediator): mediates interactions.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = IOSHealthHeightEventData()

    event_data.date_time = self._GetDateTimeRowValue(
        query_hash, row, 'start_date')
    event_data.height_value_ts_str = self._CopyToRfc3339String(
        event_data.date_time)
    height_meters = self._GetRowValue(query_hash, row, 'height_meters')
    event_data.height_m = height_meters
    event_data.height_cm = self._MetersToCentimetersInt(height_meters)
    event_data.height_ft_in = self._MetersToFeetInches(height_meters)

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(IOSHealthHeightPlugin)
