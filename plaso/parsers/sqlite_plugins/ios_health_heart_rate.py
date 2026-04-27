# -*- coding: utf-8 -*-
"""SQLite parser plugin for iOS Health Heart Rate (pre-iOS 15)."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IOSHealthHeartRateEventData(events.EventData):
  """iOS Health heart rate event data (shared).

  Attributes:
    added_date_str (str): ISO/RFC3339 of creation_date (added to Health).
    bpm (int): heart rate beats per minute.
    context (str): heart rate context (mapped).
    device_name (str): source_devices.name.
    end_date (dfdatetime.DateTimeValues): Cocoa time.
    end_date_str (str): ISO/RFC3339 string derived from end_date.
    hardware (str): source_devices.hardware.
    manufacturer (str): source_devices.manufacturer.
    series_count (int|None): quantity_sample_series.count (iOS 15+ plugin).
    series_key (str|None): quantity_sample_series.hfd_key (iOS 15+ plugin).
    software_version (str): data_provenances.source_version.
    source_name (str): sources.name.
    source_options (str|None): sources.source_options.
    start_date (dfdatetime.DateTimeValues): Cocoa time (sec since 2001-01-01).
    start_date_str (str): ISO/RFC3339 string derived from start_date.
    tz_name (str): data_provenances.tz_name.
  """

  DATA_TYPE = 'ios:health:heart_rate'

  def __init__(self):
    """Initializes event data."""
    super(IOSHealthHeartRateEventData, self).__init__(data_type=self.DATA_TYPE)
    self.added_date_str = None
    self.bpm = None
    self.context = None
    self.device_name = None
    self.end_date = None
    self.end_date_str = None
    self.hardware = None
    self.manufacturer = None
    self.series_count = None
    self.series_key = None
    self.software_version = None
    self.source_name = None
    self.source_options = None
    self.start_date = None
    self.start_date_str = None
    self.tz_name = None


class IOSHealthHeartRatePlugin(interface.SQLitePlugin):
  """SQLite parser plugin for iOS Health Heart Rate (pre-iOS 15)."""

  NAME = 'ios_health_heart_rate'
  DATA_FORMAT = (
      'iOS Health Heart Rate (pre-iOS 15) SQLite database file '
      'healthdb_secure.sqlite')

  REQUIRED_STRUCTURE = {
      'samples': frozenset(['data_id', 'start_date', 'end_date', 'data_type']),
      'quantity_samples': frozenset(['data_id', 'quantity']),
      'metadata_values': frozenset(['object_id', 'numerical_value']),
      'objects': frozenset([
          'data_id', 'provenance', 'creation_date', 'type']),
      'data_provenances': frozenset([
          'ROWID', 'device_id', 'source_id', 'source_version', 'tz_name']),
      'source_devices': frozenset([
          'ROWID', 'name', 'manufacturer', 'hardware']),
      'sources': frozenset(['ROWID', 'name', 'source_options'])}

  QUERIES = [((
      'SELECT s.start_date AS start_date, s.end_date AS end_date, '
      'CAST(ROUND(qs.quantity * 60.0) AS INT) AS bpm, CASE mv.numerical_value '
      'WHEN 1.0 THEN "Background" WHEN 2.0 THEN "Streaming" WHEN 3.0 THEN '
      '"Sedentary" WHEN 4.0 THEN "Walking" WHEN 5.0 THEN "Breathe" WHEN 6.0 '
      'THEN "Workout" WHEN 8.0 THEN "Background" WHEN 9.0 THEN "ECG" '
      'WHEN 10.0 THEN "Blood Oxygen Saturation" ELSE '
      'CAST(mv.numerical_value AS TEXT) END AS context, o.creation_date '
      'AS added_date, CASE sd.name WHEN "__NONE__" THEN "" ELSE sd.name '
      'END AS device_name, sd.manufacturer AS manufacturer, sd.hardware AS '
      'hardware, src.name AS source_name, dp.source_version AS '
      'software_version, dp.tz_name AS tz_name, src.source_options AS '
      'source_options FROM samples s LEFT JOIN quantity_samples qs ON '
      'qs.data_id = s.data_id LEFT JOIN metadata_values mv ON '
      'mv.object_id = s.data_id LEFT JOIN objects o ON o.data_id = s.data_id '
      'LEFT JOIN data_provenances dp ON dp.ROWID = o.provenance LEFT JOIN '
      'source_devices sd ON sd.ROWID = dp.device_id LEFT JOIN sources src '
      'ON src.ROWID = dp.source_id WHERE s.data_type = 5 AND o.type != 2 '
      'ORDER BY s.start_date DESC'),
      'ParseRow')]

  REQUIRE_SCHEMA_MATCH = False

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a date and time value from the row.

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

  def _CopyToRfc3339String(self, dfdt):
    """Returns RFC3339 string from a dfdatetime object.

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

  def _GetRowText(self, query_hash, row, value_name):
    """Retrieves a string value from the row.

    Args:
      query_hash (int): hash of the query.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      str: string value or None.
    """
    v = self._GetRowValue(query_hash, row, value_name)
    return None if v is None else str(v)

  def ParseRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a heart rate row.

    Args:
      parser_mediator (ParserMediator): mediates interactions.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    qh = hash(query)
    ev = IOSHealthHeartRateEventData()

    ev.start_date = self._GetDateTimeRowValue(qh, row, 'start_date')
    ev.end_date = self._GetDateTimeRowValue(qh, row, 'end_date')
    ev.start_date_str = self._CopyToRfc3339String(ev.start_date)
    ev.end_date_str = self._CopyToRfc3339String(ev.end_date)

    ev.bpm = self._GetRowValue(qh, row, 'bpm')
    ev.context = self._GetRowText(qh, row, 'context')

    added = self._GetDateTimeRowValue(qh, row, 'added_date')
    ev.added_date_str = self._CopyToRfc3339String(added)

    ev.device_name = self._GetRowText(qh, row, 'device_name')
    ev.manufacturer = self._GetRowText(qh, row, 'manufacturer')
    ev.hardware = self._GetRowText(qh, row, 'hardware')
    ev.source_name = self._GetRowText(qh, row, 'source_name')
    ev.software_version = self._GetRowText(qh, row, 'software_version')
    ev.tz_name = self._GetRowText(qh, row, 'tz_name')
    ev.source_options = self._GetRowValue(qh, row, 'source_options')

    parser_mediator.ProduceEventData(ev)


sqlite.SQLiteParser.RegisterPlugin(IOSHealthHeartRatePlugin)
