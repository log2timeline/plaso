# -*- coding: utf-8 -*-
"""SQLite parser plugin for iOS Health Headphone Audio Levels."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IOSHealthHeadphoneAudioEventData(events.EventData):
  """iOS Health Headphone Audio Levels event data.

  Attributes:
    bundle_name (str): app/bundle/source from metadata_values.string_value.
    data_id (int): samples.data_id.
    date_time (dfdatetime.DateTimeValues): primary timestamp for timeline.
    decibels (float): sound level from quantity_samples.quantity.
    device_manufacturer (str): source_devices.manufacturer.
    device_model (str): source_devices.model.
    device_name (str): source_devices.name.
    end_date (dfdatetime.DateTimeValues): Cocoa time end date.
    end_date_str (str): ISO/RFC3339 timestamp string from end_date.
    key (str): metadata_keys.key (if any).
    local_identifier (str): source_devices.localIdentifier.
    start_date (dfdatetime.DateTimeValues): Cocoa time start date.
    start_date_str (str): ISO/RFC3339 timestamp string from start_date.
    total_time_duration (str): 'HH:MM:SS' from (end_date - start_date).
  """

  DATA_TYPE = 'ios:health:headphone_audio_levels'

  def __init__(self):
    """Initializes event data."""
    super(IOSHealthHeadphoneAudioEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.bundle_name = None
    self.data_id = None
    self.date_time = None
    self.decibels = None
    self.device_manufacturer = None
    self.device_model = None
    self.device_name = None
    self.end_date = None
    self.end_date_str = None
    self.key = None
    self.local_identifier = None
    self.start_date = None
    self.start_date_str = None
    self.total_time_duration = None


class IOSHealthHeadphoneAudioPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for iOS Health Headphone Audio Levels."""

  NAME = 'ios_health_headphone_audio_levels'
  DATA_FORMAT = (
      'iOS Health Headphone Audio Levels SQLite database file '
      'healthdb_secure.sqlite')

  REQUIRED_STRUCTURE = {
      'samples': frozenset(['data_id', 'start_date', 'end_date', 'data_type']),
      'quantity_samples': frozenset(['data_id', 'quantity']),
      'metadata_values': frozenset(['object_id', 'string_value', 'key_id']),
      'metadata_keys': frozenset(['ROWID', 'key']),
      'objects': frozenset(['data_id', 'provenance']),
      'data_provenances': frozenset(['ROWID', 'device_id']),
      'source_devices': frozenset([
          'ROWID', 'name', 'manufacturer', 'model', 'localIdentifier'])}

  QUERIES = [((
      'SELECT samples.start_date AS start_date, samples.end_date AS end_date, '
      'strftime("%H:%M:%S", (samples.end_date - samples.start_date), '
      '"unixepoch") AS total_time_duration, quantity_samples.quantity AS '
      'decibels, metadata_values.string_value AS bundle_name, '
      'source_devices.name AS device_name, source_devices.manufacturer AS '
      'device_manufacturer, source_devices.model AS device_model, '
      'source_devices.localIdentifier AS local_identifier, '
      'metadata_keys.key AS key, samples.data_id AS data_id FROM samples '
      'LEFT JOIN quantity_samples ON '
      'quantity_samples.data_id = samples.data_id LEFT JOIN metadata_values '
      'ON metadata_values.object_id = samples.data_id LEFT JOIN metadata_keys '
      'ON metadata_keys.ROWID = metadata_values.key_id LEFT JOIN objects '
      'ON objects.data_id = samples.data_id LEFT JOIN data_provenances '
      'ON data_provenances.ROWID = objects.provenance LEFT JOIN '
      'source_devices ON source_devices.ROWID = data_provenances.device_id '
      'WHERE samples.data_type = 173 AND (metadata_keys.key IS NULL OR '
      'metadata_keys.key != '
      '"_HKPrivateMetadataKeyHeadphoneAudioDataIsTransient") '
      'GROUP BY samples.data_id ORDER BY samples.start_date'),
      'ParseRow')]

  SCHEMAS = {
      'samples': (
          'CREATE TABLE samples (data_id INTEGER PRIMARY KEY, start_date '
          'INTEGER, end_date INTEGER, data_type INTEGER)'),
      'quantity_samples': (
          'CREATE TABLE quantity_samples (data_id INTEGER, quantity REAL)'),
      'metadata_values': (
          'CREATE TABLE metadata_values (object_id INTEGER, key_id INTEGER, '
          'string_value TEXT)'),
      'metadata_keys': (
          'CREATE TABLE metadata_keys (ROWID INTEGER PRIMARY KEY, key TEXT)'),
      'objects': (
          'CREATE TABLE objects (data_id INTEGER, provenance INTEGER)'),
      'data_provenances': (
          'CREATE TABLE data_provenances (ROWID INTEGER PRIMARY KEY, '
          'device_id INTEGER)'),
      'source_devices': (
          'CREATE TABLE source_devices (ROWID INTEGER PRIMARY KEY, name TEXT, '
          'manufacturer TEXT, model TEXT, localIdentifier TEXT)')}

  REQUIRE_SCHEMA_MATCH = False

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
        return to_rfc3339()
      return dfdt.CopyToDateTimeString()
    except (AttributeError, TypeError, ValueError):
      return None

  def ParseRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a headphone audio level row.

    Args:
      parser_mediator (ParserMediator): mediates interactions.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = IOSHealthHeadphoneAudioEventData()
    event_data.start_date = self._GetDateTimeRowValue(
        query_hash, row, 'start_date')
    event_data.end_date = self._GetDateTimeRowValue(
        query_hash, row, 'end_date')
    event_data.start_date_str = self._CopyToRfc3339String(event_data.start_date)
    event_data.end_date_str = self._CopyToRfc3339String(event_data.end_date)
    event_data.date_time = event_data.start_date

    event_data.total_time_duration = self._GetRowValue(
        query_hash, row, 'total_time_duration')
    event_data.decibels = self._GetRowValue(query_hash, row, 'decibels')
    event_data.bundle_name = self._GetRowValue(query_hash, row, 'bundle_name')

    event_data.device_name = self._GetRowValue(
        query_hash, row, 'device_name')
    event_data.device_manufacturer = self._GetRowValue(
        query_hash, row, 'device_manufacturer')
    event_data.device_model = self._GetRowValue(
        query_hash, row, 'device_model')
    event_data.local_identifier = self._GetRowValue(
        query_hash, row, 'local_identifier')

    event_data.key = self._GetRowValue(query_hash, row, 'key')
    event_data.data_id = self._GetRowValue(query_hash, row, 'data_id')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(IOSHealthHeadphoneAudioPlugin)
