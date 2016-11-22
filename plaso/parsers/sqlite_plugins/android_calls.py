# -*- coding: utf-8 -*-
"""This file contains a parser for the Android contacts2 Call History.

Android Call History is stored in SQLite database files named contacts2.db.
"""

from plaso.containers import time_events
from plaso.lib import py2to3
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class AndroidCallEvent(time_events.JavaTimeEvent):
  """Convenience class for an Android Call History event."""

  DATA_TYPE = u'android:event:call'

  def __init__(
      self, java_time, usage, identifier, number, name, duration, call_type):
    """Initializes the event object.

    Args:
      java_time: The Java time value.
      usage: The description of the usage of the time value.
      identifier: The row identifier.
      number: The phone number associated to the remote party.
      duration: The number of seconds the call lasted.
      call_type: Incoming, Outgoing, or Missed.
    """
    super(AndroidCallEvent, self).__init__(java_time, usage)
    self.offset = identifier
    self.number = number
    self.name = name
    self.duration = duration
    self.call_type = call_type


class AndroidCallPlugin(interface.SQLitePlugin):
  """Parse Android contacts2 database."""

  NAME = u'android_calls'
  DESCRIPTION = u'Parser for Android calls SQLite database files.'

  REQUIRED_TABLES = frozenset([u'calls'])

  # Define the needed queries.
  QUERIES = [
      (u'SELECT _id AS id, date, number, name, duration, type FROM calls',
       u'ParseCallsRow')]

  SCHEMAS = [
      {u'_sync_state':
       u'CREATE TABLE _sync_state (_id INTEGER PRIMARY KEY,account_name TEXT '
       u'NOT NULL,account_type TEXT NOT NULL,data TEXT,UNIQUE(account_name, '
       u'account_type))',
       u'_sync_state_metadata':
       u'CREATE TABLE _sync_state_metadata (version INTEGER)',
       u'accounts':
       u'CREATE TABLE accounts (_id INTEGER PRIMARY KEY '
       u'AUTOINCREMENT,account_name TEXT, account_type TEXT, data_set TEXT)',
       u'agg_exceptions':
       u'CREATE TABLE agg_exceptions (_id INTEGER PRIMARY KEY '
       u'AUTOINCREMENT,type INTEGER NOT NULL, raw_contact_id1 INTEGER '
       u'REFERENCES raw_contacts(_id), raw_contact_id2 INTEGER REFERENCES '
       u'raw_contacts(_id))',
       u'android_metadata':
       u'CREATE TABLE android_metadata (locale TEXT)',
       u'calls':
       u'CREATE TABLE calls (_id INTEGER PRIMARY KEY AUTOINCREMENT,number '
       u'TEXT,date INTEGER,duration INTEGER,type INTEGER,new INTEGER,name '
       u'TEXT,numbertype INTEGER,numberlabel TEXT,countryiso '
       u'TEXT,voicemail_uri TEXT,is_read INTEGER,geocoded_location '
       u'TEXT,lookup_uri TEXT,matched_number TEXT,normalized_number '
       u'TEXT,photo_id INTEGER NOT NULL DEFAULT 0,formatted_number '
       u'TEXT,_data TEXT,has_content INTEGER,mime_type TEXT,source_data '
       u'TEXT,source_package TEXT,state INTEGER)',
       u'contacts':
       u'CREATE TABLE contacts (_id INTEGER PRIMARY KEY '
       u'AUTOINCREMENT,name_raw_contact_id INTEGER REFERENCES '
       u'raw_contacts(_id),photo_id INTEGER REFERENCES '
       u'data(_id),photo_file_id INTEGER REFERENCES '
       u'photo_files(_id),custom_ringtone TEXT,send_to_voicemail INTEGER NOT '
       u'NULL DEFAULT 0,times_contacted INTEGER NOT NULL DEFAULT '
       u'0,last_time_contacted INTEGER,starred INTEGER NOT NULL DEFAULT '
       u'0,has_phone_number INTEGER NOT NULL DEFAULT 0,lookup '
       u'TEXT,status_update_id INTEGER REFERENCES data(_id), '
       u'contact_last_updated_timestamp INTEGER)',
       u'data':
       u'CREATE TABLE data (_id INTEGER PRIMARY KEY AUTOINCREMENT,package_id '
       u'INTEGER REFERENCES package(_id),mimetype_id INTEGER REFERENCES '
       u'mimetype(_id) NOT NULL,raw_contact_id INTEGER REFERENCES '
       u'raw_contacts(_id) NOT NULL,is_read_only INTEGER NOT NULL DEFAULT '
       u'0,is_primary INTEGER NOT NULL DEFAULT 0,is_super_primary INTEGER '
       u'NOT NULL DEFAULT 0,data_version INTEGER NOT NULL DEFAULT 0,data1 '
       u'TEXT,data2 TEXT,data3 TEXT,data4 TEXT,data5 TEXT,data6 TEXT,data7 '
       u'TEXT,data8 TEXT,data9 TEXT,data10 TEXT,data11 TEXT,data12 '
       u'TEXT,data13 TEXT,data14 TEXT,data15 TEXT,data_sync1 TEXT, '
       u'data_sync2 TEXT, data_sync3 TEXT, data_sync4 TEXT )',
       u'data_usage_stat':
       u'CREATE TABLE data_usage_stat(stat_id INTEGER PRIMARY KEY '
       u'AUTOINCREMENT, data_id INTEGER NOT NULL, usage_type INTEGER NOT '
       u'NULL DEFAULT 0, times_used INTEGER NOT NULL DEFAULT 0, '
       u'last_time_used INTERGER NOT NULL DEFAULT 0, FOREIGN KEY(data_id) '
       u'REFERENCES data(_id))',
       u'default_directory':
       u'CREATE TABLE default_directory (_id INTEGER PRIMARY KEY)',
       u'deleted_contacts':
       u'CREATE TABLE deleted_contacts (contact_id INTEGER PRIMARY '
       u'KEY,contact_deleted_timestamp INTEGER NOT NULL default 0)',
       u'directories':
       u'CREATE TABLE directories(_id INTEGER PRIMARY KEY '
       u'AUTOINCREMENT,packageName TEXT NOT NULL,authority TEXT NOT '
       u'NULL,typeResourceId INTEGER,typeResourceName TEXT,accountType '
       u'TEXT,accountName TEXT,displayName TEXT, exportSupport INTEGER NOT '
       u'NULL DEFAULT 0,shortcutSupport INTEGER NOT NULL DEFAULT '
       u'0,photoSupport INTEGER NOT NULL DEFAULT 0)',
       u'groups':
       u'CREATE TABLE groups (_id INTEGER PRIMARY KEY '
       u'AUTOINCREMENT,package_id INTEGER REFERENCES '
       u'package(_id),account_name STRING DEFAULT NULL, account_type STRING '
       u'DEFAULT NULL, data_set STRING DEFAULT NULL, sourceid TEXT,version '
       u'INTEGER NOT NULL DEFAULT 1,dirty INTEGER NOT NULL DEFAULT 0,title '
       u'TEXT,title_res INTEGER,notes TEXT,system_id TEXT,deleted INTEGER '
       u'NOT NULL DEFAULT 0,group_visible INTEGER NOT NULL DEFAULT '
       u'0,should_sync INTEGER NOT NULL DEFAULT 1,auto_add INTEGER NOT NULL '
       u'DEFAULT 0,favorites INTEGER NOT NULL DEFAULT 0,group_is_read_only '
       u'INTEGER NOT NULL DEFAULT 0,sync1 TEXT, sync2 TEXT, sync3 TEXT, '
       u'sync4 TEXT , account_id INTEGER REFERENCES accounts(_id))',
       u'mimetypes':
       u'CREATE TABLE mimetypes (_id INTEGER PRIMARY KEY '
       u'AUTOINCREMENT,mimetype TEXT NOT NULL)',
       u'name_lookup':
       u'CREATE TABLE name_lookup (data_id INTEGER REFERENCES data(_id) NOT '
       u'NULL,raw_contact_id INTEGER REFERENCES raw_contacts(_id) NOT '
       u'NULL,normalized_name TEXT NOT NULL,name_type INTEGER NOT '
       u'NULL,PRIMARY KEY (data_id, normalized_name, name_type))',
       u'nickname_lookup':
       u'CREATE TABLE nickname_lookup (name TEXT,cluster TEXT)',
       u'packages':
       u'CREATE TABLE packages (_id INTEGER PRIMARY KEY '
       u'AUTOINCREMENT,package TEXT NOT NULL)',
       u'phone_lookup':
       u'CREATE TABLE phone_lookup (data_id INTEGER REFERENCES data(_id) NOT '
       u'NULL,raw_contact_id INTEGER REFERENCES raw_contacts(_id) NOT '
       u'NULL,normalized_number TEXT NOT NULL,min_match TEXT NOT NULL)',
       u'photo_files':
       u'CREATE TABLE photo_files (_id INTEGER PRIMARY KEY AUTOINCREMENT, '
       u'height INTEGER NOT NULL, width INTEGER NOT NULL, filesize INTEGER '
       u'NOT NULL)',
       u'properties':
       u'CREATE TABLE properties (property_key TEXT PRIMARY KEY, '
       u'property_value TEXT )'}]

  CALL_TYPE = {
      1: u'INCOMING',
      2: u'OUTGOING',
      3: u'MISSED'}

  def ParseCallsRow(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a Call record row.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (sqlite3.Row): row resulting from the query.
      query (Optional[str]): query string.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    call_type = self.CALL_TYPE.get(row['type'], u'UNKNOWN')

    event_object = AndroidCallEvent(
        row['date'], u'Call Started', row['id'], row['number'], row['name'],
        row['duration'], call_type)
    parser_mediator.ProduceEvent(event_object, query=query)

    duration = row['duration']
    if isinstance(duration, py2to3.STRING_TYPES):
      try:
        duration = int(duration, 10)
      except ValueError:
        duration = 0

    if duration:
      # The duration is in seconds and the date value in milliseconds.
      duration *= 1000
      event_object = AndroidCallEvent(
          row['date'] + duration, u'Call Ended', row['id'], row['number'],
          row['name'], row['duration'], call_type)
      parser_mediator.ProduceEvent(event_object, query=query)



sqlite.SQLiteParser.RegisterPlugin(AndroidCallPlugin)
