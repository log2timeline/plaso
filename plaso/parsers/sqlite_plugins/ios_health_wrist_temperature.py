# -*- coding: utf-8 -*-
"""SQLite parser plugin for iOS Health Wrist Temperature database."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IOSHealthWristTemperatureEventData(events.EventData):
  """iOS Health Wrist Temperature event data.

  Attributes:
    algorithm_version (float): algorithm version.
    date_added (dfdatetime.DateTimeValues): Cocoa time when record was added.
    date_added_str (str): ISO/RFC3339 from date_added.
    date_time (dfdatetime.DateTimeValues): primary timestamp (start).
    device_manufacturer (str): device manufacturer.
    device_model (str): device model.
    device_name (str): device name.
    end_time (dfdatetime.DateTimeValues): Cocoa time end time.
    end_time_str (str): ISO/RFC3339 from end_time.
    hardware_version (str): hardware version.
    software_version (str): software version.
    start_time (dfdatetime.DateTimeValues): Cocoa time start time.
    start_time_str (str): ISO/RFC3339 from start_time.
    surface_temperature_c (float): skin surface temp (°C).
    surface_temperature_f (float): skin surface temp (°F).
    source (str): source name.
    wrist_temperature_c (float): degrees Celsius.
    wrist_temperature_f (float): degrees Fahrenheit.
  """

  DATA_TYPE = 'ios:health:wrist_temperature'

  def __init__(self):
    """Initializes event data."""
    super(IOSHealthWristTemperatureEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.algorithm_version = None
    self.date_added = None
    self.date_added_str = None
    self.date_time = None
    self.device_manufacturer = None
    self.device_model = None
    self.device_name = None
    self.end_time = None
    self.end_time_str = None
    self.hardware_version = None
    self.software_version = None
    self.start_time = None
    self.start_time_str = None
    self.surface_temperature_c = None
    self.surface_temperature_f = None
    self.source = None
    self.wrist_temperature_c = None
    self.wrist_temperature_f = None


class IOSHealthWristTemperaturePlugin(interface.SQLitePlugin):
  """SQLite parser plugin for iOS Health Wrist Temperature."""

  NAME = 'ios_health_wrist_temperature'
  DATA_FORMAT = (
      'iOS Health Wrist Temperature SQLite database file '
      'healthdb_secure.sqlite')

  REQUIRED_STRUCTURE = {
      'samples': frozenset(['start_date', 'end_date', 'data_type']),
      'quantity_samples': frozenset(['data_id', 'quantity']),
      'objects': frozenset(['data_id', 'creation_date', 'provenance']),
      'data_provenances': frozenset(['ROWID', 'source_id', 'device_id']),
      'sources': frozenset(['ROWID', 'name']),
      'source_devices': frozenset([
          'ROWID', 'name', 'manufacturer', 'model', 'hardware', 'software']),
      'metadata_keys': frozenset(['ROWID', 'key']),
      'metadata_values': frozenset(['object_id', 'key_id', 'numerical_value'])}

  QUERIES = [((
      'WITH surface_temp AS (SELECT mv.object_id, mv.numerical_value FROM '
      'metadata_values AS mv JOIN metadata_keys AS mk ON mv.key_id = mk.ROWID '
      'WHERE mk.key = "_HKPrivateMetadataKeySkinSurfaceTemperature"), '
      'alg_ver AS (SELECT mv.object_id, mv.numerical_value FROM '
      'metadata_values AS mv JOIN metadata_keys AS mk ON mv.key_id = mk.ROWID '
      'WHERE mk.key = "HKAlgorithmVersion") SELECT samples.start_date AS '
      'start_date, samples.end_date AS end_date, objects.creation_date AS '
      'creation_date, quantity_samples.quantity AS wrist_temp_c, '
      '(quantity_samples.quantity * 1.8) + 32 AS wrist_temp_f, sources.name '
      'AS source, alg_ver.numerical_value AS alg_version, '
      'surface_temp.numerical_value AS surf_temp_c, '
      '(surface_temp.numerical_value * 1.8) + 32 AS surf_temp_f, '
      'source_devices.name AS device_name, source_devices.manufacturer AS '
      'device_manufacturer, source_devices.model AS device_model, '
      'source_devices.hardware AS hardware_version, source_devices.software AS '
      'software_version FROM samples LEFT JOIN quantity_samples ON '
      'quantity_samples.data_id = samples.data_id LEFT JOIN objects ON '
      'samples.data_id = objects.data_id LEFT JOIN data_provenances ON '
      'objects.provenance = data_provenances.ROWID LEFT JOIN surface_temp ON '
      'surface_temp.object_id = samples.data_id LEFT JOIN alg_ver ON '
      'alg_ver.object_id = samples.data_id LEFT JOIN sources ON sources.ROWID '
      '= data_provenances.source_id LEFT JOIN source_devices ON '
      'source_devices.ROWID = data_provenances.device_id WHERE '
      'samples.data_type = 70 ORDER BY samples.start_date DESC'),
      'ParseWristTemperatureRow')]

  SCHEMAS = {
      'samples': (
          'CREATE TABLE samples (data_id INTEGER PRIMARY KEY, start_date '
          'REAL, end_date REAL, data_type INTEGER)'),
      'quantity_samples': (
          'CREATE TABLE quantity_samples (data_id INTEGER PRIMARY KEY, '
          'quantity REAL)'),
      'objects': (
          'CREATE TABLE objects (data_id INTEGER PRIMARY KEY, creation_date '
          'REAL, provenance INTEGER)')}

  REQUIRE_SCHEMA_MATCH = False

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

    try:
      ts_float = float(timestamp)
    except (TypeError, ValueError):
      return None

    if ts_float > 1e12:
      ts_float /= 1e9

    if ts_float == 0:
      return None

    return dfdatetime_cocoa_time.CocoaTime(timestamp=ts_float)

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
        return to_rfc3339()
      return dfdt.CopyToDateTimeString()
    except (AttributeError, TypeError, ValueError):
      return None

  def _CleanText(self, value):
    """Cleans common text artifacts (NBSP, mojibake).

    Args:
      value (str): text value to clean.

    Returns:
      str: cleaned text value or None.
    """
    if value is None:
      return None
    text = str(value).replace('\xa0', ' ').strip()
    try:
      fixed = text.encode('latin-1', errors='ignore').decode(
          'utf-8', errors='ignore')
      if fixed and (len(fixed) >= len(text) - 1):
        text = fixed
    except (UnicodeEncodeError, UnicodeDecodeError):
      pass
    return text or None

  def ParseWristTemperatureRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses a wrist temperature row.

    Args:
      parser_mediator (ParserMediator): mediates interactions.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)
    event_data = IOSHealthWristTemperatureEventData()

    event_data.start_time = self._GetDateTimeRowValue(
        query_hash, row, 'start_date')
    event_data.end_time = self._GetDateTimeRowValue(
        query_hash, row, 'end_date')
    event_data.date_added = self._GetDateTimeRowValue(
        query_hash, row, 'creation_date')

    event_data.start_time_str = self._CopyToRfc3339String(event_data.start_time)
    event_data.end_time_str = self._CopyToRfc3339String(event_data.end_time)
    event_data.date_added_str = self._CopyToRfc3339String(event_data.date_added)

    event_data.date_time = event_data.start_time

    event_data.wrist_temperature_c = self._GetRowValue(
        query_hash, row, 'wrist_temp_c')
    event_data.wrist_temperature_f = self._GetRowValue(
        query_hash, row, 'wrist_temp_f')
    event_data.algorithm_version = self._GetRowValue(
        query_hash, row, 'alg_version')
    event_data.surface_temperature_c = self._GetRowValue(
        query_hash, row, 'surf_temp_c')
    event_data.surface_temperature_f = self._GetRowValue(
        query_hash, row, 'surf_temp_f')

    event_data.source = self._CleanText(self._GetRowValue(
        query_hash, row, 'source'))
    event_data.device_name = self._CleanText(self._GetRowValue(
        query_hash, row, 'device_name'))
    event_data.device_manufacturer = self._CleanText(self._GetRowValue(
        query_hash, row, 'device_manufacturer'))
    event_data.device_model = self._CleanText(self._GetRowValue(
        query_hash, row, 'device_model'))
    event_data.hardware_version = self._CleanText(self._GetRowValue(
        query_hash, row, 'hardware_version'))
    event_data.software_version = self._CleanText(self._GetRowValue(
        query_hash, row, 'software_version'))

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(IOSHealthWristTemperaturePlugin)
