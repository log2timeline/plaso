"""SQLite parser plugin for Android Native Downloads database files.

The Android native downloads database file is typically stored as:
  com.android.providers.downloads/databases/downloads.db

Also see :
  STATUS_* and DESTINATION_* constants:
    https://android.googlesource.com/platform/frameworks/base/+/refs/heads/master/core/java/android/provider/Downloads.java
  ERROR_*, PAUSED_*, and VISIBILITY_* constants:
    https://android.googlesource.com/platform/frameworks/base/+/HEAD/core/java/android/app/DownloadManager.java
"""

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class AndroidNativeDownloadsEventData(events.EventData):
    """Android Native Downloads (DownloadProvider) event data.

    Attributes:
      current_bytes (int): Number of bytes download so far.
      deleted (bool): Set to true if this download is deleted.
         Also Removed from the database when MediaProvider database
         deletes the metadata associated with this downloaded file.
      description (str): The client-supplied description of this download. This
          will be displayed in system notifications.
      destination (int): Flag that controls download destination. Also see the
          DESTINATION_* constants for a list of supported values.
      error_msg (str): The column with errorMsg for a failed downloaded.
          Used only for debugging purposes.
      e_tag (str): ETag of this file.
      identifier (int): identifier of the download.
      is_visible_in_downloads_ui (int):  Whether or not this download should
          be displayed in the system's Downloads UI. Defaults to true.
      media_provider_uri (str): The URI to corresponding entry in MediaProvider
          for this downloaded entry. If an entry is deleted from downloaded list,
          it is also deleted from MediaProvider DB.
      mime_type (str): Internet Media Type of the downloaded file.
      modification_time (dfdatetime.DateTimeValues): Last content modification
          date and time of downloaded file.
      notification_package (str): Package name associated with notification
          of a running download.
      status (int): Holds one of the STATUS_* constants.
          If an error occurred, this holds the HTTP Status Error Code (RFC 2616),
          otherwise it holds one of the ERROR_* constants.
          If the download is paused, this holds one of the PAUSED_* constants.
      saved_to (str): Path to the downloaded file on disk.
      title (str): Title of the download.
      total_bytes (int): Total size of the download in bytes.
      ui_visibility (int): Flags that control if the download is displayed by the
          UI. Also see VISIBILITY_* constants for a list of supported values.
      uri (str): Downloaded URI.
    """

    DATA_TYPE = "android:sqlite:downloads"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.current_bytes = None
        self.deleted = None
        self.description = None
        self.destination = None
        self.error_msg = None
        self.e_tag = None
        self.identifier = None
        self.is_visible_in_downloads_ui = None
        self.media_provider_uri = None
        self.mime_type = None
        self.modification_time = None
        self.notification_package = None
        self.saved_to = None
        self.status = None
        self.title = None
        self.total_bytes = None
        self.ui_visibility = None
        self.uri = None


class AndroidNativeDownloadsPlugin(interface.SQLitePlugin):
    """SQLite parser plugin for Android native downloads database file."""

    NAME = "android_native_downloads"
    DATA_FORMAT = "Android native downloads SQLite database (downloads.db) file"

    REQUIRED_STRUCTURE = {
        "downloads": frozenset(
            [
                "current_bytes",
                "_data",
                "deleted",
                "description",
                "destination",
                "errorMsg",
                "etag",
                "_id",
                "is_visible_in_downloads_ui",
                "lastmod",
                "mediaprovider_uri",
                "mimetype",
                "notificationpackage",
                "status",
                "title",
                "total_bytes",
                "uri",
                "visibility",
            ]
        )
    }

    QUERIES = [
        (
            (
                "SELECT _id, uri, _data, mimetype, destination, visibility, status, "
                "lastmod, notificationpackage, total_bytes, current_bytes, etag, "
                "title, description, is_visible_in_downloads_ui, mediaprovider_uri, "
                "deleted, errorMsg FROM downloads"
            ),
            "ParseDownloadsRow",
        )
    ]

    SCHEMAS = [
        {
            "android_metadata": ("CREATE TABLE android_metadata (locale TEXT)"),
            "downloads": (
                "CREATE TABLE downloads(_id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "uri TEXT, method INTEGER, entity TEXT, no_integrity BOOLEAN, "
                "hint TEXT, otaupdate BOOLEAN, _data TEXT, mimetype TEXT, "
                "destination INTEGER, no_system BOOLEAN, visibility INTEGER, "
                "control INTEGER, status INTEGER, numfailed INTEGER, "
                "lastmod BIGINT, notificationpackage TEXT, notificationclass TEXT, "
                "notificationextras TEXT, cookiedata TEXT, useragent TEXT, "
                "referer TEXT, total_bytes INTEGER, current_bytes INTEGER, "
                "etag TEXT, uid INTEGER, otheruid INTEGER, title TEXT, "
                "description TEXT, scanned BOOLEAN, "
                "is_public_api INTEGER NOT NULL DEFAULT 0, "
                "allow_roaming INTEGER NOT NULL DEFAULT 0, "
                "allowed_network_types INTEGER NOT NULL DEFAULT 0, "
                "is_visible_in_downloads_ui INTEGER NOT NULL DEFAULT 1, "
                "bypass_recommended_size_limit INTEGER NOT NULL DEFAULT 0, "
                "mediaprovider_uri TEXT, deleted BOOLEAN NOT NULL DEFAULT 0, "
                "errorMsg TEXT, allow_metered INTEGER NOT NULL DEFAULT 1, "
                "allow_write BOOLEAN NOT NULL DEFAULT 0, "
                "flags INTEGER NOT NULL DEFAULT 0, "
                "mediastore_uri TEXT DEFAULT NULL)"
            ),
            "request_headers": (
                "CREATE TABLE request_headers(id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "download_id INTEGER NOT NULL, "
                "header TEXT NOT NULL,value TEXT NOT NULL)"
            ),
            "sqlite_sequence": ("CREATE TABLE sqlite_sequence(name,seq)"),
        }
    ]

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
        event_data.current_bytes = self._GetRowValue(query_hash, row, "current_bytes")
        event_data.deleted = self._GetRowValue(query_hash, row, "deleted")
        # Description defaults to an empty string.
        event_data.description = (
            self._GetRowValue(query_hash, row, "description") or None
        )
        event_data.destination = self._GetRowValue(query_hash, row, "destination")
        event_data.error_msg = self._GetRowValue(query_hash, row, "errorMsg")
        event_data.e_tag = self._GetRowValue(query_hash, row, "etag")
        event_data.identifier = self._GetRowValue(query_hash, row, "_id")
        event_data.is_visible_in_downloads_ui = self._GetRowValue(
            query_hash, row, "is_visible_in_downloads_ui"
        )
        event_data.modification_time = self._GetJavaTimeRowValue(
            query_hash, row, "lastmod"
        )
        event_data.media_provider_uri = self._GetRowValue(
            query_hash, row, "mediaprovider_uri"
        )
        event_data.mime_type = self._GetRowValue(query_hash, row, "mimetype")
        event_data.notification_package = self._GetRowValue(
            query_hash, row, "notificationpackage"
        )
        event_data.saved_to = self._GetRowValue(query_hash, row, "_data")
        event_data.status = self._GetRowValue(query_hash, row, "status")
        event_data.title = self._GetRowValue(query_hash, row, "title")
        event_data.total_bytes = self._GetRowValue(query_hash, row, "total_bytes")
        event_data.ui_visibility = self._GetRowValue(query_hash, row, "visibility")
        event_data.uri = self._GetRowValue(query_hash, row, "uri")

        parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(AndroidNativeDownloadsPlugin)
