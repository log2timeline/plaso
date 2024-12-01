# -*- coding: utf-8 -*-
"""SQLite parser plugin for Android Viber call history database files."""

from dfdatetime import java_time as dfdatetime_java_time

from plaso.containers import events
from plaso.lib import definitions
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class AndroidViberCallEventData(events.EventData):
  """Android Viber Call event data.

  Attributes:
    number (str): phone number.
    type (int): type of call, such as: Incoming, or Outgoing.
    viber_call_type (int): type of call in Viber app, such as: Audio Call, or Video Call.
    duration (int): number of seconds the call lasted.
    start_time (dfdatetime.DateTimeValues): date and time the call was started.
    end_time (dfdatetime.DateTimeValues): date and time the call was stopped.
  """

  DATA_TYPE = 'android:viber:call'

  def __init__(self):
    """Initializes event data."""
    super(AndroidViberCallEventData, self).__init__(data_type=self.DATA_TYPE)
    self.number = None
    self.type = None
    self.viber_call_type = None
    self.duration = None
    self.start_time = None
    self.end_time = None


class AndroidViberCallPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Android Viber call history database files.

  The Android Viber call history database file is typically stored in:
  viber_data
  """

  NAME = 'android_viber_call'
  DATA_FORMAT = 'Android Viber call history SQLite database (viber_data) file'

  REQUIRED_STRUCTURE = {
      'calls': frozenset(['_id', 'date', 'number', 'duration', 'type', 'viber_call_type'])}

  QUERIES = [
      ('SELECT _id AS id, date, number, duration, type, viber_call_type FROM calls',
       'ParseViberCallsRow')]

  SCHEMAS = [{
    'blockednumbers': (
        'CREATE TABLE blockednumbers (_id INTEGER PRIMARY KEY AUTOINCREMENT, '
        'canonized_number TEXT NOT NULL, blocked_date LONG DEFAULT 0, '
        'block_reason INTEGER DEFAULT 0, status INTEGER DEFAULT 0, '
        'UNIQUE (canonized_number) ON CONFLICT REPLACE )'),
    'calls': (
        'CREATE TABLE calls (_id INTEGER PRIMARY KEY AUTOINCREMENT, '
        'call_id LONG NOT NULL, aggregate_hash LONG NOT NULL, '
        'number TEXT NOT NULL, canonized_number TEXT NOT NULL, '
        'viber_call BOOLEAN DEFAULT TRUE, viber_call_type INTEGER DEFAULT 1, '
        'date LONG NOT NULL, duration LONG NOT NULL, type INT NOT NULL, '
        'end_reason INT DEFAULT 0, start_reason INT DEFAULT 0, '
        'token LONG DEFAULT 0, looked BOOLEAN DEFAULT TRUE, '
        'conference_info TEXT, group_id LONG DEFAULT 0, '
        'flags INTEGER DEFAULT 0)'),
    'phonebookcontact': (
        'CREATE TABLE phonebookcontact (_id INTEGER PRIMARY KEY NOT NULL, '
        'native_id INTEGER DEFAULT 0, display_name TEXT, phonetic_name TEXT, '
        'phone_label TEXT, low_display_name TEXT, starred BOOLEAN, '
        'viber BOOLEAN, contact_lookup_key TEXT, contact_hash LONG, '
        'version INTEGER DEFAULT 0, has_number BOOLEAN, has_name BOOLEAN, '
        'native_photo_id LONG DEFAULT 0, recently_joined_date LONG DEFAULT 0, '
        'joined_date LONG DEFAULT 0, numbers_name TEXT DEFAULT '', '
        'deleted BOOLEAN, flags INTEGER DEFAULT 0, '
        'UNIQUE (_id) ON CONFLICT REPLACE)'),
    'sqlite_sequence': (
        'CREATE TABLE sqlite_sequence(name,seq)'),
    'sync_data': (
        'CREATE TABLE sync_data (_id INTEGER PRIMARY KEY AUTOINCREMENT, '
        'canonized_phone_number TEXT NOT NULL, display_name TEXT DEFAULT '', '
        'phonetic_name TEXT DEFAULT '',operation INTEGER  DEFAULT 0)'),
    'vibernumbers': (
        'CREATE TABLE vibernumbers (_id INTEGER PRIMARY KEY AUTOINCREMENT, '
        'canonized_number TEXT NOT NULL, photo TEXT DEFAULT '', '
        'viber_name TEXT, clear BOOLEAN, member_id TEXT NOT NULL, '
        'encrypted_member_id TEXT NOT NULL, viber_id TEXT, '
        'date_of_birth TEXT)'),
    'viberpay_data': (
        'CREATE TABLE viberpay_data (_id INTEGER PRIMARY KEY AUTOINCREMENT, '
        'encrypted_member_id TEXT NULL, canonized_phone_number TEXT NULL, '
        'phone_number TEXT NULL, country_code TEXT NULL, '
        'is_country_supported BOOLEAN NOT NULL, '
        'default_currency_code TEXT NULL, is_viberpay_user BOOLEAN NOT NULL, '
        'last_sync_date INTEGER NOT NULL)'),
    'walletlist': (
        'CREATE TABLE walletlist (_id INTEGER PRIMARY KEY AUTOINCREMENT, '
        'country_codes INTEGER NOT NULL)'),
    'walletnumbers': (
        'CREATE TABLE walletnumbers (_id INTEGER PRIMARY KEY AUTOINCREMENT, '
        'canonized_number TEXT NOT NULL, wallet_wu_status INTEGER DEFAULT 0, '
        'UNIQUE (canonized_number) ON CONFLICT REPLACE )'),
    }]

  def ParseViberCallsRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a Viber Call record row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    duration = self._GetRowValue(query_hash, row, 'duration')
    timestamp = self._GetRowValue(query_hash, row, 'date')

    event_data = AndroidViberCallEventData()
    event_data.type = self._GetRowValue(query_hash, row, 'type')
    event_data.duration = duration
    event_data.number = self._GetRowValue(query_hash, row, 'number')
    event_data.viber_call_type = self._GetRowValue(query_hash, row, 'viber_call_type')
    event_data.start_time = dfdatetime_java_time.JavaTime(timestamp=timestamp)

    if duration:
      # The duration is in seconds and the date value in milliseconds.
      timestamp += duration * definitions.MILLISECONDS_PER_SECOND

      event_data.end_time = dfdatetime_java_time.JavaTime(timestamp=timestamp)

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(AndroidViberCallPlugin)
