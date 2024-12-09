# -*- coding: utf-8 -*-
"""SQLite parser plugin for 
AirGuard AirTag Tracker on Android database files."""

from dfdatetime import java_time as dfdatetime_java_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class AirTagEventData(events.EventData):
  """AirGuard AirTag Tracker on Android event data.

    Attributes:
        device_address (str): Address of the AirTag device.
        rssi (int): Signal strength indicator.
        latitude (float): Latitude of the AirTag.
        longitude (float): Longitude of the AirTag.
        device_name (str): Name of the device.
        first_discovery (str): First time the device was detected.
        last_seen (str): Last time the device was detected.
  """

  DATA_TYPE = 'android:airtag:event'

  def __init__(self):
    """Initializes event data."""
    super(AirTagEventData, self).__init__(data_type=self.DATA_TYPE)
    self.device_address = None
    self.rssi = None
    self.latitude = None
    self.longitude = None
    self.device_name = None
    self.first_discovery = None
    self.last_seen = None


class AirTagPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for AirGuard AirTag Tracker on Android database files.

  The AirTag database file is typically stored in:
  temp/data/data/de.seemoo.at_tracking_detection.release/databases/attd_db
  """

  NAME = 'android_airtag'
  DATA_FORMAT = 'AirGuard AirTag Tracker on SQLite database files'

  REQUIRED_STRUCTURE = {
      'beacon': frozenset([
        'beaconId', 'receivedAt', 'rssi', 
        'deviceAddress', 'latitude', 'longitude']),
      'device': frozenset([
        'deviceId', 'uniqueId', 'address', 'name', 'firstDiscovery', 'lastSeen', 'deviceType'])}

  QUERIES = [
      ('SELECT device.address, device.name, beacon.rssi, beacon.latitude, '
       'beacon.longitude, device.firstDiscovery, device.lastSeen '
       'FROM device '
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

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a date and time value from the row.

    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.JavaTime: date and time value or None if not available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if timestamp is None:
      return None

    return dfdatetime_java_time.JavaTime(timestamp=timestamp)

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
    event_data.rssi = self._GetRowValue(query_hash, row, 'rssi')
    event_data.latitude = self._GetRowValue(query_hash, row, 'latitude')
    event_data.longitude = self._GetRowValue(query_hash, row, 'longitude')
    event_data.device_name = self._GetRowValue(query_hash, row, 'name')
    event_data.first_discovery = self._GetRowValue(query_hash, row, 
                                                   'firstDiscovery')
    event_data.last_seen = self._GetRowValue(query_hash, row, 'lastSeen')

    parser_mediator.ProduceEventData(event_data)

sqlite.SQLiteParser.RegisterPlugin(AirTagPlugin)
