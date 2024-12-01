# -*- coding: utf-8 -*-
"""SQLite parser plugin for Android Native Downloads (DownloadManager API) database files."""
import re

from dfdatetime import java_time as dfdatetime_java_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class AndroidNativeDownloadsEventData(events.EventData):
  """Android Native Downloads (DownloadProvider) event data.

  Also see :
  STATUS_* and DESTINATION_* constants: https://android.googlesource.com/platform/frameworks/base/
    +/refs/heads/master/core/java/android/provider/Downloads.java
  ERROR_*, PAUSED_*, and VISIBILITY_* constants: https://android.googlesource.com/platform/frameworks/base/
    +/refs/heads/main/core/java/android/app/DownloadManager.java
  Basis for what columns to extract: https://forensafe.com/blogs/Android_Downloads.html

  Attributes:
    lastmod (dfdatetime.DateTimeValues): Last modified date and time of downloaded file.
    id (int): An identifier for a particular download, unique across the system.
    uri (str): Downloaded URI.
    mimetype (str): Internet Media Type of the downloaded file.
    total_bytes (int): Total size of the download in bytes.
    current_bytes (int): Number of bytes download so far.
    status (int): Holds one of the STATUS_* constants.
        If an error occurred, this holds the HTTP Status Code for an HTTP error (RFC 2616),
        otherwise it holds one of the ERROR_* constants.
        If the download is paused, this holds one of the PAUSED_* constants.
    saved_to (str): Path to the downloaded file on disk.
    deleted (bool): Set to true if this download is deleted. It is completely removed from the database when
        MediaProvider database also deletes the metadata associated with this downloaded file.
    notification_package (str): Package name associated with notification of a running download.
    title (str): Title of the download.
    media_provider_uri (str): The URI to the corresponding entry in MediaProvider for this downloaded entry. It is
        used to delete the entries from MediaProvider database when it is deleted from the
        downloaded list.
    error_msg (str): The column with errorMsg for a failed downloaded. Used only for debugging purposes.
    is_visible_in_downloads_ui (int) :  Whether or not this download should be displayed in the system's Downloads UI.
        Defaults to true.
    destination (int): The name of the column containing the flag that controls the destination of the download.
    See the DESTINATION_* constants for a list of legal values.
    ui_visibility (int): The name of the column containing the flags that controls whether the download is displayed by
        the UI. See the VISIBILITY_* constants for a list of legal values.
    e_tag (str) ETag of this file.
    description (str): The client-supplied description of this download. This will be displayed in system
        notifications. Defaults to the empty string.
  """

  DATA_TYPE = 'android:sqlite:downloads'

  def __init__(self):
    """Initializes event data."""
    super(AndroidNativeDownloadsEventData, self).__init__(data_type=self.DATA_TYPE)
    self.lastmod = None
    self.id = None
    self.uri = None
    self.mimetype = None
    self.total_bytes = None
    self.current_bytes = None
    self.status = None
    self.saved_to = None
    self.deleted = None
    self.notification_package = None
    self.title = None
    self.media_provider_uri = None
    self.error_msg = None
    self.is_visible_in_downloads_ui = None
    self.destination = None
    self.ui_visibility = None
    self.e_tag = None
    self.description = None


class AndroidNativeDownloadsPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Android native downloads database file.

  The Android native downloads database file is typically stored in:
  com.android.providers.downloads/databases/downloads.db
  """

  NAME = 'android_native_downloads'
  DATA_FORMAT = 'Android native downloads SQLite database (downloads.db) file'

  REQUIRED_STRUCTURE = {
      'downloads': frozenset(['_id', 'uri', '_data', 'mimetype', 'destination', 'visibility', 'status', 'lastmod',
                              'notificationpackage', 'total_bytes', 'current_bytes', 'etag', 'title', 'description',
                              'is_visible_in_downloads_ui', 'mediaprovider_uri', 'deleted', 'errorMsg'])}
  QUERIES = [
      ('SELECT _id, uri, _data, mimetype, destination, visibility, status, lastmod, '
          'notificationpackage, total_bytes, current_bytes, etag, title, description, '
          'is_visible_in_downloads_ui, mediaprovider_uri, deleted, errorMsg FROM downloads',
       'ParseDownloadsRow')]

  SCHEMAS = [{
      'android_metadata': (
          'CREATE TABLE android_metadata (locale TEXT) '),
      'downloads': (
          'CREATE TABLE downloads(_id INTEGER PRIMARY KEY AUTOINCREMENT, uri TEXT, method INTEGER, '
          'entity TEXT, no_integrity BOOLEAN, hint TEXT, otaupdate BOOLEAN, _data TEXT, mimetype TEXT, '
          'destination INTEGER, no_system BOOLEAN, visibility INTEGER, control INTEGER, status INTEGER, '
          'numfailed INTEGER, lastmod BIGINT, notificationpackage TEXT, notificationclass TEXT, '
          'notificationextras TEXT, cookiedata TEXT, useragent TEXT, referer TEXT, total_bytes INTEGER, '
          'current_bytes INTEGER, etag TEXT, uid INTEGER, otheruid INTEGER, title TEXT, description TEXT, ' 
          'scanned BOOLEAN, is_public_api INTEGER NOT NULL DEFAULT 0, allow_roaming INTEGER NOT NULL DEFAULT 0, '
          'allowed_network_types INTEGER NOT NULL DEFAULT 0, is_visible_in_downloads_ui INTEGER NOT NULL DEFAULT 1, '
          'bypass_recommended_size_limit INTEGER NOT NULL DEFAULT 0, mediaprovider_uri TEXT, '
          'deleted BOOLEAN NOT NULL DEFAULT 0, errorMsg TEXT, allow_metered INTEGER NOT NULL DEFAULT 1, '
          'allow_write BOOLEAN NOT NULL DEFAULT 0, flags INTEGER NOT NULL DEFAULT 0, mediastore_uri '
          'TEXT DEFAULT NULL)'),
      'request_headers': (
          'CREATE TABLE request_headers(id INTEGER PRIMARY KEY AUTOINCREMENT, download_id INTEGER NOT NULL, '
          'header TEXT NOT NULL,value TEXT NOT NULL)'),
      'sqlite_sequence': (
          'CREATE TABLE sqlite_sequence(name,seq)')}]

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

  def ParseDownloadsRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a download row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = AndroidNativeDownloadsEventData()
    event_data.lastmod = self._GetDateTimeRowValue(query_hash, row, 'lastmod')
    event_data.id = self._GetRowValue(query_hash, row, '_id')
    event_data.uri = self._GetRowValue(query_hash, row, 'uri')
    event_data.mimetype = self._GetRowValue(query_hash, row, 'mimetype')
    event_data.total_bytes = self._GetRowValue(query_hash, row, 'total_bytes')
    event_data.current_bytes = self._GetRowValue(query_hash, row, 'current_bytes')
    event_data.status = self._GetRowValue(query_hash, row, 'status')
    event_data.saved_to = self._GetRowValue(query_hash, row, '_data')
    event_data.deleted = self._GetRowValue(query_hash, row, 'deleted')
    event_data.notification_package = self._GetRowValue(query_hash, row, 'notificationpackage')
    event_data.title = self._GetRowValue(query_hash, row, 'title')
    event_data.error_msg = self._GetRowValue(query_hash, row, 'errorMsg')
    event_data.is_visible_in_downloads_ui = self._GetRowValue(query_hash, row, 'is_visible_in_downloads_ui')
    event_data.media_provider_uri = self._GetRowValue(query_hash, row, 'mediaprovider_uri')
    event_data.destination = self._GetRowValue(query_hash, row, 'destination')
    event_data.ui_visibility = self._GetRowValue(query_hash, row, 'visibility')
    event_data.e_tag = self._GetRowValue(query_hash, row, 'etag')
    event_data.description = self._GetRowValue(query_hash, row, 'description')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(AndroidNativeDownloadsPlugin)
