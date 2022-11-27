# -*- coding: utf-8 -*-
"""SQLite parser plugin for Android call history database files."""

from dfdatetime import java_time as dfdatetime_java_time

from plaso.containers import events
from plaso.lib import definitions
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class AndroidCallEventData(events.EventData):
  """Android Call event data.

  Attributes:
    call_type (int): type of call, such as: Incoming, Outgoing, or Missed.
    duration (int): number of seconds the call lasted.
    end_time (dfdatetime.DateTimeValues): date and time the call was stopped.
    name (str): name associated to the remote party.
    number (str): phone number associated to the remote party.
    offset (str): identifier of the row, from which the event data was
        extracted.
    query (str): SQL query that was used to obtain the event data.
    start_time (dfdatetime.DateTimeValues): date and time the call was started.
  """

  DATA_TYPE = 'android:event:call'

  def __init__(self):
    """Initializes event data."""
    super(AndroidCallEventData, self).__init__(data_type=self.DATA_TYPE)
    self.call_type = None
    self.duration = None
    self.end_time = None
    self.name = None
    self.number = None
    self.offset = None
    self.query = None
    self.start_time = None


class AndroidCallPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Android call history database files.

  The Android call history database file is typically stored in:
  contacts2.db
  """

  NAME = 'android_calls'
  DATA_FORMAT = 'Android call history SQLite database (contacts2.db) file'

  REQUIRED_STRUCTURE = {
      'calls': frozenset(['_id', 'date', 'number', 'name', 'duration', 'type'])}

  QUERIES = [
      ('SELECT _id AS id, date, number, name, duration, type FROM calls',
       'ParseCallsRow')]

  SCHEMAS = [{
      '_sync_state': (
          'CREATE TABLE _sync_state (_id INTEGER PRIMARY KEY, account_name '
          'TEXT NOT NULL, account_type TEXT NOT NULL, data TEXT, '
          'UNIQUE(account_name, account_type))'),
      '_sync_state_metadata': (
          'CREATE TABLE _sync_state_metadata (version INTEGER)'),
      'accounts': (
          'CREATE TABLE accounts (_id INTEGER PRIMARY KEY AUTOINCREMENT, '
          'account_name TEXT, account_type TEXT, data_set TEXT)'),
      'agg_exceptions': (
          'CREATE TABLE agg_exceptions (_id INTEGER PRIMARY KEY '
          'AUTOINCREMENT, type INTEGER NOT NULL, raw_contact_id1 INTEGER '
          'REFERENCES raw_contacts(_id), raw_contact_id2 INTEGER REFERENCES '
          'raw_contacts(_id))'),
      'android_metadata': (
          'CREATE TABLE android_metadata (locale TEXT)'),
      'calls': (
          'CREATE TABLE calls (_id INTEGER PRIMARY KEY AUTOINCREMENT, number '
          'TEXT, date INTEGER, duration INTEGER, type INTEGER, new INTEGER, '
          'name TEXT, numbertype INTEGER, numberlabel TEXT, countryiso TEXT, '
          'voicemail_uri TEXT, is_read INTEGER, geocoded_location TEXT, '
          'lookup_uri TEXT, matched_number TEXT, normalized_number TEXT, '
          'photo_id INTEGER NOT NULL DEFAULT 0, formatted_number TEXT, _data '
          'TEXT, has_content INTEGER, mime_type TEXT, source_data TEXT, '
          'source_package TEXT, state INTEGER)'),
      'contacts': (
          'CREATE TABLE contacts (_id INTEGER PRIMARY KEY AUTOINCREMENT, '
          'name_raw_contact_id INTEGER REFERENCES raw_contacts(_id), photo_id '
          'INTEGER REFERENCES data(_id), photo_file_id INTEGER REFERENCES '
          'photo_files(_id), custom_ringtone TEXT, send_to_voicemail INTEGER '
          'NOT NULL DEFAULT 0, times_contacted INTEGER NOT NULL DEFAULT 0, '
          'last_time_contacted INTEGER, starred INTEGER NOT NULL DEFAULT 0, '
          'has_phone_number INTEGER NOT NULL DEFAULT 0, lookup TEXT, '
          'status_update_id INTEGER REFERENCES data(_id), '
          'contact_last_updated_timestamp INTEGER)'),
      'data': (
          'CREATE TABLE data (_id INTEGER PRIMARY KEY AUTOINCREMENT, '
          'package_id INTEGER REFERENCES package(_id), mimetype_id INTEGER '
          'REFERENCES mimetype(_id) NOT NULL, raw_contact_id INTEGER '
          'REFERENCES raw_contacts(_id) NOT NULL, is_read_only INTEGER NOT '
          'NULL DEFAULT 0, is_primary INTEGER NOT NULL DEFAULT 0, '
          'is_super_primary INTEGER NOT NULL DEFAULT 0, data_version INTEGER '
          'NOT NULL DEFAULT 0, data1 TEXT, data2 TEXT, data3 TEXT, data4 '
          'TEXT, data5 TEXT, data6 TEXT, data7 TEXT, data8 TEXT, data9 TEXT, '
          'data10 TEXT, data11 TEXT, data12 TEXT, data13 TEXT, data14 TEXT, '
          'data15 TEXT, data_sync1 TEXT, data_sync2 TEXT, data_sync3 TEXT, '
          'data_sync4 TEXT )'),
      'data_usage_stat': (
          'CREATE TABLE data_usage_stat(stat_id INTEGER PRIMARY KEY '
          'AUTOINCREMENT, data_id INTEGER NOT NULL, usage_type INTEGER NOT '
          'NULL DEFAULT 0, times_used INTEGER NOT NULL DEFAULT 0, '
          'last_time_used INTEGER NOT NULL DEFAULT 0, FOREIGN KEY(data_id) '
          'REFERENCES data(_id))'),
      'default_directory': (
          'CREATE TABLE default_directory (_id INTEGER PRIMARY KEY)'),
      'deleted_contacts': (
          'CREATE TABLE deleted_contacts (contact_id INTEGER PRIMARY KEY, '
          'contact_deleted_timestamp INTEGER NOT NULL default 0)'),
      'directories': (
          'CREATE TABLE directories(_id INTEGER PRIMARY KEY AUTOINCREMENT, '
          'packageName TEXT NOT NULL, authority TEXT NOT NULL, typeResourceId '
          'INTEGER, typeResourceName TEXT, accountType TEXT, accountName '
          'TEXT, displayName TEXT, exportSupport INTEGER NOT NULL DEFAULT 0, '
          'shortcutSupport INTEGER NOT NULL DEFAULT 0, photoSupport INTEGER '
          'NOT NULL DEFAULT 0)'),
      'groups': (
          'CREATE TABLE groups (_id INTEGER PRIMARY KEY AUTOINCREMENT, '
          'package_id INTEGER REFERENCES package(_id), account_name STRING '
          'DEFAULT NULL, account_type STRING DEFAULT NULL, data_set STRING '
          'DEFAULT NULL, sourceid TEXT, version INTEGER NOT NULL DEFAULT 1, '
          'dirty INTEGER NOT NULL DEFAULT 0, title TEXT, title_res INTEGER, '
          'notes TEXT, system_id TEXT, deleted INTEGER NOT NULL DEFAULT 0, '
          'group_visible INTEGER NOT NULL DEFAULT 0, should_sync INTEGER NOT '
          'NULL DEFAULT 1, auto_add INTEGER NOT NULL DEFAULT 0, favorites '
          'INTEGER NOT NULL DEFAULT 0, group_is_read_only INTEGER NOT NULL '
          'DEFAULT 0, sync1 TEXT, sync2 TEXT, sync3 TEXT, sync4 TEXT , '
          'account_id INTEGER REFERENCES accounts(_id))'),
      'mimetypes': (
          'CREATE TABLE mimetypes (_id INTEGER PRIMARY KEY AUTOINCREMENT, '
          'mimetype TEXT NOT NULL)'),
      'name_lookup': (
          'CREATE TABLE name_lookup (data_id INTEGER REFERENCES data(_id) NOT '
          'NULL, raw_contact_id INTEGER REFERENCES raw_contacts(_id) NOT '
          'NULL, normalized_name TEXT NOT NULL, name_type INTEGER NOT NULL, '
          'PRIMARY KEY (data_id, normalized_name, name_type))'),
      'nickname_lookup': (
          'CREATE TABLE nickname_lookup (name TEXT, cluster TEXT)'),
      'packages': (
          'CREATE TABLE packages (_id INTEGER PRIMARY KEY AUTOINCREMENT, '
          'package TEXT NOT NULL)'),
      'phone_lookup': (
          'CREATE TABLE phone_lookup (data_id INTEGER REFERENCES data(_id) '
          'NOT NULL, raw_contact_id INTEGER REFERENCES raw_contacts(_id) NOT '
          'NULL, normalized_number TEXT NOT NULL, min_match TEXT NOT NULL)'),
      'photo_files': (
          'CREATE TABLE photo_files (_id INTEGER PRIMARY KEY AUTOINCREMENT, '
          'height INTEGER NOT NULL, width INTEGER NOT NULL, filesize INTEGER '
          'NOT NULL)'),
      'properties': (
          'CREATE TABLE properties (property_key TEXT PRIMARY KEY, '
          'property_value TEXT )')}]

  def ParseCallsRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a Call record row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    duration = self._GetRowValue(query_hash, row, 'duration')
    timestamp = self._GetRowValue(query_hash, row, 'date')

    event_data = AndroidCallEventData()
    event_data.call_type = self._GetRowValue(query_hash, row, 'type')
    event_data.duration = self._GetRowValue(query_hash, row, 'duration')
    event_data.name = self._GetRowValue(query_hash, row, 'name')
    event_data.number = self._GetRowValue(query_hash, row, 'number')
    event_data.offset = self._GetRowValue(query_hash, row, 'id')
    event_data.query = query
    event_data.start_time = dfdatetime_java_time.JavaTime(timestamp=timestamp)

    if duration:
      # The duration is in seconds and the date value in milliseconds.
      timestamp += duration * definitions.MILLISECONDS_PER_SECOND

      event_data.end_time = dfdatetime_java_time.JavaTime(timestamp=timestamp)

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(AndroidCallPlugin)
