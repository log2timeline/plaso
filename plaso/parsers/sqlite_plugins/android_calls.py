# -*- coding: utf-8 -*-
"""This file contains a parser for the Android contacts2 Call History.

Android Call History is stored in SQLite database files named contacts2.db.
"""

from dfdatetime import java_time as dfdatetime_java_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import py2to3
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class AndroidCallEventData(events.EventData):
  """Android Call event data.

  Attributes:
    call_type (str): type of call, such as: Incoming, Outgoing, or Missed.
    duration (int): number of seconds the call lasted.
    name (str): name associated to the remote party.
    number (str): phone number associated to the remote party.
  """

  DATA_TYPE = u'android:event:call'

  def __init__(self):
    """Initializes event data."""
    super(AndroidCallEventData, self).__init__(data_type=self.DATA_TYPE)
    self.call_type = None
    self.duration = None
    self.name = None
    self.number = None


class AndroidCallPlugin(interface.SQLitePlugin):
  """Parse Android contacts2 database."""

  NAME = u'android_calls'
  DESCRIPTION = u'Parser for Android calls SQLite database files.'

  REQUIRED_TABLES = frozenset([u'calls'])

  # Define the needed queries.
  QUERIES = [
      (u'SELECT _id AS id, date, number, name, duration, type FROM calls',
       u'ParseCallsRow')]

  SCHEMAS = [{
      u'_sync_state': (
          u'CREATE TABLE _sync_state (_id INTEGER PRIMARY KEY, account_name '
          u'TEXT NOT NULL, account_type TEXT NOT NULL, data TEXT, '
          u'UNIQUE(account_name, account_type))'),
      u'_sync_state_metadata': (
          u'CREATE TABLE _sync_state_metadata (version INTEGER)'),
      u'accounts': (
          u'CREATE TABLE accounts (_id INTEGER PRIMARY KEY AUTOINCREMENT, '
          u'account_name TEXT, account_type TEXT, data_set TEXT)'),
      u'agg_exceptions': (
          u'CREATE TABLE agg_exceptions (_id INTEGER PRIMARY KEY '
          u'AUTOINCREMENT, type INTEGER NOT NULL, raw_contact_id1 INTEGER '
          u'REFERENCES raw_contacts(_id), raw_contact_id2 INTEGER REFERENCES '
          u'raw_contacts(_id))'),
      u'android_metadata': (
          u'CREATE TABLE android_metadata (locale TEXT)'),
      u'calls': (
          u'CREATE TABLE calls (_id INTEGER PRIMARY KEY AUTOINCREMENT, number '
          u'TEXT, date INTEGER, duration INTEGER, type INTEGER, new INTEGER, '
          u'name TEXT, numbertype INTEGER, numberlabel TEXT, countryiso TEXT, '
          u'voicemail_uri TEXT, is_read INTEGER, geocoded_location TEXT, '
          u'lookup_uri TEXT, matched_number TEXT, normalized_number TEXT, '
          u'photo_id INTEGER NOT NULL DEFAULT 0, formatted_number TEXT, _data '
          u'TEXT, has_content INTEGER, mime_type TEXT, source_data TEXT, '
          u'source_package TEXT, state INTEGER)'),
      u'contacts': (
          u'CREATE TABLE contacts (_id INTEGER PRIMARY KEY AUTOINCREMENT, '
          u'name_raw_contact_id INTEGER REFERENCES raw_contacts(_id), photo_id '
          u'INTEGER REFERENCES data(_id), photo_file_id INTEGER REFERENCES '
          u'photo_files(_id), custom_ringtone TEXT, send_to_voicemail INTEGER '
          u'NOT NULL DEFAULT 0, times_contacted INTEGER NOT NULL DEFAULT 0, '
          u'last_time_contacted INTEGER, starred INTEGER NOT NULL DEFAULT 0, '
          u'has_phone_number INTEGER NOT NULL DEFAULT 0, lookup TEXT, '
          u'status_update_id INTEGER REFERENCES data(_id), '
          u'contact_last_updated_timestamp INTEGER)'),
      u'data': (
          u'CREATE TABLE data (_id INTEGER PRIMARY KEY AUTOINCREMENT, '
          u'package_id INTEGER REFERENCES package(_id), mimetype_id INTEGER '
          u'REFERENCES mimetype(_id) NOT NULL, raw_contact_id INTEGER '
          u'REFERENCES raw_contacts(_id) NOT NULL, is_read_only INTEGER NOT '
          u'NULL DEFAULT 0, is_primary INTEGER NOT NULL DEFAULT 0, '
          u'is_super_primary INTEGER NOT NULL DEFAULT 0, data_version INTEGER '
          u'NOT NULL DEFAULT 0, data1 TEXT, data2 TEXT, data3 TEXT, data4 '
          u'TEXT, data5 TEXT, data6 TEXT, data7 TEXT, data8 TEXT, data9 TEXT, '
          u'data10 TEXT, data11 TEXT, data12 TEXT, data13 TEXT, data14 TEXT, '
          u'data15 TEXT, data_sync1 TEXT, data_sync2 TEXT, data_sync3 TEXT, '
          u'data_sync4 TEXT )'),
      u'data_usage_stat': (
          u'CREATE TABLE data_usage_stat(stat_id INTEGER PRIMARY KEY '
          u'AUTOINCREMENT, data_id INTEGER NOT NULL, usage_type INTEGER NOT '
          u'NULL DEFAULT 0, times_used INTEGER NOT NULL DEFAULT 0, '
          u'last_time_used INTEGER NOT NULL DEFAULT 0, FOREIGN KEY(data_id) '
          u'REFERENCES data(_id))'),
      u'default_directory': (
          u'CREATE TABLE default_directory (_id INTEGER PRIMARY KEY)'),
      u'deleted_contacts': (
          u'CREATE TABLE deleted_contacts (contact_id INTEGER PRIMARY KEY, '
          u'contact_deleted_timestamp INTEGER NOT NULL default 0)'),
      u'directories': (
          u'CREATE TABLE directories(_id INTEGER PRIMARY KEY AUTOINCREMENT, '
          u'packageName TEXT NOT NULL, authority TEXT NOT NULL, typeResourceId '
          u'INTEGER, typeResourceName TEXT, accountType TEXT, accountName '
          u'TEXT, displayName TEXT, exportSupport INTEGER NOT NULL DEFAULT 0, '
          u'shortcutSupport INTEGER NOT NULL DEFAULT 0, photoSupport INTEGER '
          u'NOT NULL DEFAULT 0)'),
      u'groups': (
          u'CREATE TABLE groups (_id INTEGER PRIMARY KEY AUTOINCREMENT, '
          u'package_id INTEGER REFERENCES package(_id), account_name STRING '
          u'DEFAULT NULL, account_type STRING DEFAULT NULL, data_set STRING '
          u'DEFAULT NULL, sourceid TEXT, version INTEGER NOT NULL DEFAULT 1, '
          u'dirty INTEGER NOT NULL DEFAULT 0, title TEXT, title_res INTEGER, '
          u'notes TEXT, system_id TEXT, deleted INTEGER NOT NULL DEFAULT 0, '
          u'group_visible INTEGER NOT NULL DEFAULT 0, should_sync INTEGER NOT '
          u'NULL DEFAULT 1, auto_add INTEGER NOT NULL DEFAULT 0, favorites '
          u'INTEGER NOT NULL DEFAULT 0, group_is_read_only INTEGER NOT NULL '
          u'DEFAULT 0, sync1 TEXT, sync2 TEXT, sync3 TEXT, sync4 TEXT , '
          u'account_id INTEGER REFERENCES accounts(_id))'),
      u'mimetypes': (
          u'CREATE TABLE mimetypes (_id INTEGER PRIMARY KEY AUTOINCREMENT, '
          u'mimetype TEXT NOT NULL)'),
      u'name_lookup': (
          u'CREATE TABLE name_lookup (data_id INTEGER REFERENCES data(_id) NOT '
          u'NULL, raw_contact_id INTEGER REFERENCES raw_contacts(_id) NOT '
          u'NULL, normalized_name TEXT NOT NULL, name_type INTEGER NOT NULL, '
          u'PRIMARY KEY (data_id, normalized_name, name_type))'),
      u'nickname_lookup': (
          u'CREATE TABLE nickname_lookup (name TEXT, cluster TEXT)'),
      u'packages': (
          u'CREATE TABLE packages (_id INTEGER PRIMARY KEY AUTOINCREMENT, '
          u'package TEXT NOT NULL)'),
      u'phone_lookup': (
          u'CREATE TABLE phone_lookup (data_id INTEGER REFERENCES data(_id) '
          u'NOT NULL, raw_contact_id INTEGER REFERENCES raw_contacts(_id) NOT '
          u'NULL, normalized_number TEXT NOT NULL, min_match TEXT NOT NULL)'),
      u'photo_files': (
          u'CREATE TABLE photo_files (_id INTEGER PRIMARY KEY AUTOINCREMENT, '
          u'height INTEGER NOT NULL, width INTEGER NOT NULL, filesize INTEGER '
          u'NOT NULL)'),
      u'properties': (
          u'CREATE TABLE properties (property_key TEXT PRIMARY KEY, '
          u'property_value TEXT )')}]

  CALL_TYPE = {
      1: u'INCOMING',
      2: u'OUTGOING',
      3: u'MISSED'}

  def ParseCallsRow(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a Call record row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row.
      query (Optional[str]): query.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    call_type = self.CALL_TYPE.get(row['type'], u'UNKNOWN')
    duration = row['duration']
    timestamp = row['date']

    event_data = AndroidCallEventData()
    event_data.call_type = call_type
    event_data.duration = row['duration']
    event_data.name = row['name']
    event_data.number = row['number']
    event_data.offset = row['id']
    event_data.query = query

    date_time = dfdatetime_java_time.JavaTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(date_time, u'Call Started')
    parser_mediator.ProduceEventWithEventData(event, event_data)

    if duration:
      if isinstance(duration, py2to3.STRING_TYPES):
        try:
          duration = int(duration, 10)
        except ValueError:
          duration = 0

      # The duration is in seconds and the date value in milliseconds.
      timestamp += duration * 1000

      date_time = dfdatetime_java_time.JavaTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(date_time, u'Call Ended')
      parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(AndroidCallPlugin)
