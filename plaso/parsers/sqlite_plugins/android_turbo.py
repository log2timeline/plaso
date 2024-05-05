# -*- coding: utf-8 -*-
"""SQLite parser plugin for Android turbo database files."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class AndroidTurboBatteryEvent(events.EventData):
  """Android turbo battery event data.

  Attributes:
    battery_level (int): Remaining battery level, expressed as a percentage.
    battery_saver (int): Indicates if battery saver is turn on.
    charge_type (int): Indicates that the device is charging.
    recorded_time (dfdatetime.DateTimeValues): date and time the battery event
        was recorded.
  """

  DATA_TYPE = 'android:event:battery'

  def __init__(self):
    """Initializes event data."""
    super(AndroidTurboBatteryEvent, self).__init__(data_type=self.DATA_TYPE)
    self.battery_level = None
    self.battery_saver = None
    self.charge_type = None
    self.recorded_time = None


class AndroidTurboPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Android's turbo.db database files."""

  NAME = 'android_turbo'
  DATA_FORMAT = 'Android turbo SQLite database (turbo.db) file'

  REQUIRED_STRUCTURE = {
      'battery_event': frozenset([
          'timestamp_millis', 'battery_level', 'charge_type', 'battery_saver'])}

  QUERIES = [
      ('SELECT timestamp_millis, battery_level, charge_type, battery_saver '
       'FROM battery_event',
       'ParseBatteryEventRow')]

  SCHEMAS = [{
      'android_metadata': 'CREATE TABLE android_metadata (locale TEXT)',
      'battery_event':  (
          'CREATE TABLE battery_event(timestamp_millis INTEGER PRIMARY KEY '
          'DESC, battery_level INTEGER, charge_type INTEGER, battery_saver '
          'INTEGER, timezone TEXT, place_key INTEGER, FOREIGN KEY(place_key) '
          'REFERENCES charging_places(_id))'),
      'charging_places': (
          'CREATE TABLE charging_places(_id INTEGER PRIMARY KEY, place_name '
          'TEXT, place_api_id TEXT, UNIQUE(place_api_id) ON CONFLICT IGNORE)')}]

  def ParseBatteryEventRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a row from the battery_event table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = AndroidTurboBatteryEvent()
    event_data.battery_level = self._GetRowValue(
        query_hash, row, 'battery_level')
    event_data.battery_saver = self._GetRowValue(
        query_hash, row, 'battery_saver')
    event_data.charge_type = self._GetRowValue(query_hash, row, 'charge_type')

    timestamp = self._GetRowValue(query_hash, row, 'timestamp_millis')

    event_data.recorded_time = dfdatetime_posix_time.PosixTimeInMilliseconds(
        timestamp=timestamp)

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(AndroidTurboPlugin)
