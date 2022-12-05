# -*- coding: utf-8 -*-
"""SQLite parser plugin for Mozilla Firefox downloads database files."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class FirefoxDownloadEventData(events.EventData):
  """Firefox download event data.

  Attributes:
    end_time (dfdatetime.DateTimeValues): date and time the download was
        finished.
    full_path (str): full path of the target of the download.
    mime_type (str): mime type of the download.
    name (str): name of the download.
    offset (str): identifier of the row, from which the event data was
        extracted.
    query (str): SQL query that was used to obtain the event data.
    received_bytes (int): number of bytes received.
    referrer (str): referrer URL of the download.
    start_time (dfdatetime.DateTimeValues): date and time the download was
        started.
    temporary_location (str): temporary location of the download.
    total_bytes (int): total number of bytes of the download.
    url (str): source URL of the download.
  """

  DATA_TYPE = 'firefox:downloads:download'

  def __init__(self):
    """Initializes event data."""
    super(FirefoxDownloadEventData, self).__init__(data_type=self.DATA_TYPE)
    self.end_time = None
    self.full_path = None
    self.mime_type = None
    self.name = None
    self.offset = None
    self.query = None
    self.received_bytes = None
    self.referrer = None
    self.start_time = None
    self.temporary_location = None
    self.total_bytes = None
    self.url = None


class FirefoxDownloadsPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Mozilla Firefox downloads database files.

  The Mozilla Firefox downloads database file is typically stored in:
  downloads.sqlite
  """

  NAME = 'firefox_downloads'
  DATA_FORMAT = (
      'Mozilla Firefox downloads SQLite database (downloads.sqlite) file')

  REQUIRED_STRUCTURE = {
      'moz_downloads': frozenset([
          'id', 'name', 'source', 'target', 'tempPath', 'startTime', 'endTime',
          'state', 'referrer', 'currBytes', 'maxBytes', 'mimeType'])}

  QUERIES = [
      (('SELECT moz_downloads.id, moz_downloads.name, moz_downloads.source, '
        'moz_downloads.target, moz_downloads.tempPath, '
        'moz_downloads.startTime, moz_downloads.endTime, moz_downloads.state, '
        'moz_downloads.referrer, moz_downloads.currBytes, '
        'moz_downloads.maxBytes, moz_downloads.mimeType '
        'FROM moz_downloads'),
       'ParseDownloadsRow')]

  SCHEMAS = [
      {'moz_downloads':
       'CREATE TABLE moz_downloads (id INTEGER PRIMARY KEY, name TEXT, '
       'source TEXT, target TEXT, tempPath TEXT, startTime INTEGER, endTime '
       'INTEGER, state INTEGER, referrer TEXT, entityID TEXT, currBytes '
       'INTEGER NOT NULL DEFAULT 0, maxBytes INTEGER NOT NULL DEFAULT -1, '
       'mimeType TEXT, preferredApplication TEXT, preferredAction INTEGER '
       'NOT NULL DEFAULT 0, autoResume INTEGER NOT NULL DEFAULT 0)'}]

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a date and time value from the row.

    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.PosixTimeInMicroseconds: date and time value or None if not
          available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if timestamp is None:
      return None

    return dfdatetime_posix_time.PosixTimeInMicroseconds(timestamp=timestamp)

  def ParseDownloadsRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses a downloads row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = FirefoxDownloadEventData()
    event_data.end_time = self._GetDateTimeRowValue(query_hash, row, 'endTime')
    event_data.full_path = self._GetRowValue(query_hash, row, 'target')
    event_data.mime_type = self._GetRowValue(query_hash, row, 'mimeType')
    event_data.name = self._GetRowValue(query_hash, row, 'name')
    event_data.offset = self._GetRowValue(query_hash, row, 'id')
    event_data.query = query
    event_data.received_bytes = self._GetRowValue(query_hash, row, 'currBytes')
    event_data.referrer = self._GetRowValue(query_hash, row, 'referrer')
    event_data.start_time = self._GetDateTimeRowValue(
        query_hash, row, 'startTime')
    event_data.temporary_location = self._GetRowValue(
        query_hash, row, 'tempPath')
    event_data.total_bytes = self._GetRowValue(query_hash, row, 'maxBytes')
    event_data.url = self._GetRowValue(query_hash, row, 'source')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(FirefoxDownloadsPlugin)
