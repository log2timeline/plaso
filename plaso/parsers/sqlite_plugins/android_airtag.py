"""SQLite parser plugin for Android AirGuard AirTag Tracker database files.

The AirTag Tracker database file is typically stored in:
  temp/data/data/de.seemoo.at_tracking_detection.release/databases/attd_db
"""

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class AirTagEventData(events.EventData):
  """AirGuard AirTag Tracker on Android event data.

  Attributes:
    device_address (str): Address of the AirTag device.
    device_name (str): Name of the device.
    first_discovery_time (dfdatetime.DateTimeValues): date and time the device
        was first detected.
    last_seen_time (dfdatetime.DateTimeValues): date and time the device was
        last detected.
    latitude (float): Latitude of the AirTag.
    longitude (float): Longitude of the AirTag.
    rssi (int): Received Signal Strength Indicator (RSSI).
  """

  DATA_TYPE = 'android:airtag:event'

  def __init__(self):
    """Initializes event data."""
    super().__init__(data_type=self.DATA_TYPE)
    self.device_address = None
    self.device_name = None
    self.first_discovery_time = None
    self.last_seen_time = None
    self.latitude = None
    self.longitude = None
    self.rssi = None


class AirTagPlugin(interface.SQLitePlugin):
  """Android AirGuard AirTag Tracker SQLite database file parser."""

  NAME = 'android_airtag'
  DATA_FORMAT = 'AirGuard AirTag Tracker on SQLite database files'

  REQUIRED_STRUCTURE = {
      'beacon': frozenset([
          'beaconId', 'receivedAt', 'rssi', 'deviceAddress', 'latitude',
          'longitude']),
      'device': frozenset([
          'deviceId', 'uniqueId', 'address', 'name', 'firstDiscovery',
          'lastSeen', 'deviceType'])}

  QUERIES = [
      ('SELECT device.address, device.name, beacon.rssi, beacon.latitude, '
       'beacon.longitude, device.firstDiscovery, device.lastSeen FROM device '
       'INNER JOIN beacon ON device.address = beacon.deviceAddress',
       'ParseAirTagRow')]

  SCHEMAS = [{
      'android_metadata': (
          'CREATE TABLE android_metadata (locale TEXT)'),
      'beacon': (
          'CREATE TABLE beacon '
          '(beaconId INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, '
          'receivedAt TEXT NOT NULL, rssi INTEGER NOT NULL, '
          'deviceAddress TEXT NOT NULL, '
          'longitude REAL, latitude REAL, mfg BLOB, serviceUUIDs TEXT)'),
      'device': (
          'CREATE TABLE device '
          '(deviceId INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, '
          'uniqueId TEXT, address TEXT NOT NULL, '
          'name TEXT, ignore INTEGER NOT NULL, '
          'connectable INTEGER DEFAULT 0, payloadData INTEGER, '
          'firstDiscovery TEXT NOT NULL, '
          'lastSeen TEXT NOT NULL, notificationSent INTEGER NOT NULL, '
          'lastNotificationSent TEXT, '
          'deviceType TEXT)'),
      'feedback': (
          'CREATE TABLE feedback '
          '(feedbackId INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, '
          'notificationId INTEGER NOT NULL, location TEXT)'),
      'notification': (
          'CREATE TABLE notification '
          '(notificationId INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, '
          'deviceAddress TEXT NOT NULL, '
          'falseAlarm INTEGER NOT NULL, dismissed INTEGER, '
          'clicked INTEGER, createdAt TEXT NOT NULL)'),
      'room_master_table': (
          'CREATE TABLE room_master_table '
          '(id INTEGER PRIMARY KEY, identity_hash TEXT)'),
      'scan': (
          'CREATE TABLE scan '
          '(scanId INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, '
          'endDate TEXT, noDevicesFound INTEGER, duration INTEGER, '
          'isManual INTEGER NOT NULL, '
          'scanMode INTEGER NOT NULL, startDate TEXT)')}]

  def _GetDateTimeRowValue(self, parser_mediator, query_hash, row, value_name):
    """Retrieves a date and time value from the row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.TimeElementsInMilliseconds: date and time value or None if
          not available.
    """
    iso8601_string = self._GetRowValue(query_hash, row, value_name)
    if iso8601_string is None:
      return None

    try:
      date_time = dfdatetime_time_elements.TimeElementsInMilliseconds()
      date_time.CopyFromStringISO8601(iso8601_string)
    except ValueError as exception:
      parser_mediator.ProduceExtractionWarning(
          f'Unable to parse ${value_name:} date and time string: '
          f'{iso8601_string:s} with error: {exception!s}')
      date_time = None

    return date_time

  def ParseAirTagRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses an AirTag row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = AirTagEventData()
    event_data.device_address = self._GetRowValue(query_hash, row, 'address')
    event_data.device_name = self._GetRowValue(query_hash, row, 'name')
    event_data.first_discovery_time = self._GetDateTimeRowValue(
        parser_mediator, query_hash, row, 'firstDiscovery')
    event_data.last_seen_time = self._GetDateTimeRowValue(
        parser_mediator, query_hash, row, 'lastSeen')
    event_data.latitude = self._GetRowValue(query_hash, row, 'latitude')
    event_data.longitude = self._GetRowValue(query_hash, row, 'longitude')
    event_data.rssi = self._GetRowValue(query_hash, row, 'rssi')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(AirTagPlugin)
