# -*- coding: utf-8 -*-
"""SQLite parser plugin for Mozilla Firefox downloads database files."""

import json

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


class Firefox118DownloadEventData(events.EventData):
  """Firefox download event data.

  Attributes:
    deleted (int): deleted state.
    download_state (int): state of the download.
    end_time (dfdatetime.DateTimeValues): date and time the download was
        finished.
    expiration (int): expiration.
    flags (int): flags associated with this download
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
    type (int): type field.
    url (str): source URL of the download.
  """

  DATA_TYPE = 'firefox:downloads:download'

  def __init__(self):
    """Initializes event data."""
    super(Firefox118DownloadEventData, self).__init__(data_type=self.DATA_TYPE)
    self.deleted = None
    self.download_state = None
    self.end_time = None
    self.expiration = None
    self.flags = None
    self.full_path = None
    self.name = None
    self.query = None
    self.received_bytes = None
    self.start_time = None
    self.total_bytes = None
    self.type = None
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


class Firefox118DownloadsPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for version 118 Firefox downloads database files.

  The version 118 Firefox downloads database file is typically stored in:
  places.sql
  """

  NAME = 'firefox_118_downloads'
  DATA_FORMAT = (
      'Mozilla Firefox 118 downloads SQLite database (downloads.sqlite) file')

  REQUIRED_STRUCTURE = {
      'moz_annos': frozenset([
          'id', 'place_id', 'anno_attribute_id', 'content', 'flags',
          'expiration', 'type', 'dateAdded', 'lastModified']),
      'moz_places': frozenset([
          'id', 'title', 'url', 'last_visit_date'])}

  QUERIES = [
      (('SELECT annos1.content, annos2.flags, annos2.expiration, annos2.type, '
        'annos2.dateAdded, annos2.lastModified, annos2.content as dest_fpath, '
        'places.url, places.title, places.last_visit_date '
        'from moz_annos annos1, moz_annos annos2, moz_places places '
        'WHERE annos1.anno_attribute_id == annos2.anno_attribute_id+1 '
        'AND annos1.place_id == annos2.place_id '
        'AND annos1.place_id == places.id'),
       'ParseDownloadsRow')]

  SCHEMAS = [
      {'moz_annos':
       'CREATE TABLE moz_annos (id INTEGER PRIMARY KEY, '
       'place_id INTEGER NOT NULL, anno_attribute_id INTEGER, '
       'content LONGVARCHAR, flags INTEGER DEFAULT 0, '
       'expiration INTEGER DEFAULT 0, type INTEGER DEFAULT 0, '
       'dateAdded INTEGER DEFAULT 0, lastModified INTEGER DEFAULT 0)'},
      {'moz_places':
       'CREATE TABLE moz_places (id INTEGER PRIMARY KEY, url LONGVARCHAR, '
       'title LONGVARCHAR, rev_host LONGVARCHAR, '
       'visit_count INTEGER DEFAULT 0, hidden INTEGER DEFAULT 0 NOT NULL, '
       'typed INTEGER DEFAULT 0 NOT NULL, '
       'frecency INTEGER DEFAULT -1 NOT NULL, last_visit_date INTEGER, '
       'guid TEXT, foreign_count INTEGER DEFAULT 0 NOT NULL, '
       'url_hash INTEGER DEFAULT 0 NOT NULL , description TEXT, '
       'preview_image_url TEXT, site_name TEXT, '
       'origin_id INTEGER REFERENCES moz_origins(id), '
       'recalc_frecency INTEGER NOT NULL DEFAULT 0, alt_frecency INTEGER, '
       'recalc_alt_frecency INTEGER NOT NULL DEFAULT 0)'}]

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

  def ParseDownloadsRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a downloads row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    content = self._GetRowValue(query_hash, row, 'content')
    content_data = json.loads(content)

    event_data = Firefox118DownloadEventData()

    event_data.deleted = content_data.get('deleted', None)
    event_data.download_state = content_data.get('state', None)
    event_data.end_time = content_data.get('endTime', None)
    event_data.expiration = self._GetRowValue(query_hash, row, 'expiration')
    event_data.flags = self._GetRowValue(query_hash, row, 'flags')
    event_data.full_path = self._GetRowValue(query_hash, row, 'dest_fpath')
    event_data.name = self._GetRowValue(query_hash, row, 'title')
    event_data.query = query
    event_data.received_bytes = content_data.get('fileSize', 0)
    event_data.start_time = self._GetDateTimeRowValue(
        query_hash, row, 'dateAdded')
    event_data.total_bytes = content_data.get('fileSize', 0)
    event_data.type = self._GetRowValue(query_hash, row, 'type')
    event_data.url = self._GetRowValue(query_hash, row, 'url')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugins([
    FirefoxDownloadsPlugin, Firefox118DownloadsPlugin])
