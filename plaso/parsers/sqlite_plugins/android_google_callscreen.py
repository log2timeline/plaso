# -*- coding: utf-8 -*-
"""SQLite parser plugin for Android Google Call Screen history database files."""

from dfdatetime import java_time as dfdatetime_java_time

from plaso.containers import events
from plaso.lib import definitions
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class GoogleCallScreenEventData(events.EventData):
  """Android Google Call Screen event data.

  Attributes:
    file_path (str): path where the recording file is located.
    timestamp (dfdatetime.DateTimeValues): date and time the log was created.
  """

  DATA_TYPE = 'android:google:callscreen'

  def __init__(self):
    """Initializes event data."""
    super(GoogleCallScreenEventData, self).__init__(data_type=self.DATA_TYPE)
    self.file_path = None
    self.timestamp = None


class GoogleCallScreenPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Android Google Call Screen history database files.

  The Android Google Call Screen history database file is typically stored in:
  callscreenL_transcripts
  """

  NAME = 'google_callscreen'
  DATA_FORMAT = 'Google Call Screen SQLite database (callscreen_transcripts) file'

  REQUIRED_STRUCTURE = {
      'Transcript': frozenset(['lastModifiedMillis', 'audioRecordingFilePath'])}

  QUERIES = [
      ('SELECT lastModifiedMillis, audioRecordingFilePath FROM Transcript',
       'ParseCallScreenRow')]

  SCHEMAS = [{
      'Transcript': (
          'CREATE TABLE `Transcript` (`id` TEXT NOT NULL, `conversation` BLOB, '
          '`audioRecordingFilePath` TEXT, `isRated` INTEGER NOT NULL, `revelioCallType` '
          'INTEGER, `lastModifiedMillis` INTEGER NOT NULL, `callScreenFeedbackData` '
          'BLOB, PRIMARY KEY(`id`))'),
      'android_metadata': (
          'CREATE TABLE android_metadata (locale TEXT)'),
      'room_master_table': (
          'CREATE TABLE room_master_table (id INTEGER PRIMARY KEY, '
          'identity_hash TEXT)')}]

  def ParseCallScreenRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a Google Callscreen record row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)
    
    timestamp = self._GetRowValue(query_hash, row, 'lastModifiedMillis')
    
    event_data = GoogleCallScreenEventData()
    event_data.file_path = self._GetRowValue(query_hash, row, 'audioRecordingFilePath')
    event_data.timestamp = dfdatetime_java_time.JavaTime(timestamp=timestamp)
    
    parser_mediator.ProduceEventData(event_data)
    
sqlite.SQLiteParser.RegisterPlugin(GoogleCallScreenPlugin)
