"""SQLite parser plugin for Windows Search index (Windows.db) database files."""

import struct

from dfdatetime import filetime as dfdatetime_filetime

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class WindowsSearchIndexItemEventData(events.EventData):
    """Windows Search index item event data.

    Attributes:
      access_time (dfdatetime.DateTimeValues): date and time the item was last
          accessed.
      content_type (str): content (MIME) type of the item.
      creation_time (dfdatetime.DateTimeValues): date and time the item was created.
      file_attributes (int): file attribute flags.
      gather_time (dfdatetime.DateTimeValues): date and time the item was last
          processed by the indexer.
      hostname (str): name of the computer the item was indexed on.
      is_folder (bool): True if the item is a folder.
      item_type (str): type of the item, typically the file extension.
      modification_time (dfdatetime.DateTimeValues): date and time the item was
          last modified.
      owner (str): owner of the item.
      path (str): display path of the item.
      size (int): size of the item in bytes.
      summary (str): automatic summary, or content preview, of the item.
      title (str): title of the item.
      work_identifier (int): identifier of the item in the index.
    """

    DATA_TYPE = "windows:search:db_item"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.access_time = None
        self.content_type = None
        self.creation_time = None
        self.file_attributes = None
        self.gather_time = None
        self.hostname = None
        self.is_folder = None
        self.item_type = None
        self.modification_time = None
        self.owner = None
        self.path = None
        self.size = None
        self.summary = None
        self.title = None
        self.work_identifier = None


class WindowsSearchPlugin(interface.SQLitePlugin):
    """SQLite parser plugin for Windows Search index (Windows.db) database files.

    The Windows Search index database of Windows 11 24H2 and later, and Windows
    Server 2025, is typically stored in:
    C:\\ProgramData\\Microsoft\\Search\\Data\\Applications\\Windows\\Windows.db

    The property values of an indexed item are stored in the SystemIndex_1_PropertyStore
    table as one row per item (WorkId) and property (ColumnId). The names of the
    properties are stored in the SystemIndex_1_PropertyStore_Metadata table.
    """

    NAME = "windows_search"
    DATA_FORMAT = "Windows Search index SQLite database (Windows.db) file"

    REQUIRED_STRUCTURE = {
        "SystemIndex_1_PropertyStore": frozenset(["WorkId", "ColumnId", "Value"]),
        "SystemIndex_1_PropertyStore_Metadata": frozenset(["Id", "Name"]),
    }

    # Note that the Value column has a mixed type, text for strings, an integer
    # for 32-bit values and a little-endian 64-bit blob for FILETIME and 64-bit
    # integer values. The column identifiers differ per database, hence the
    # properties are looked up by name.
    QUERIES = [
        (
            (
                "SELECT store.WorkId AS WorkId, "
                "MAX(CASE WHEN metadata.Name = 'System.ItemPathDisplay' "
                "THEN store.Value END) AS ItemPathDisplay, "
                "MAX(CASE WHEN metadata.Name = 'System.Size' "
                "THEN store.Value END) AS Size, "
                "MAX(CASE WHEN metadata.Name = 'System.DateCreated' "
                "THEN store.Value END) AS DateCreated, "
                "MAX(CASE WHEN metadata.Name = 'System.DateModified' "
                "THEN store.Value END) AS DateModified, "
                "MAX(CASE WHEN metadata.Name = 'System.DateAccessed' "
                "THEN store.Value END) AS DateAccessed, "
                "MAX(CASE WHEN metadata.Name = 'System.Search.GatherTime' "
                "THEN store.Value END) AS GatherTime, "
                "MAX(CASE WHEN metadata.Name = 'System.FileOwner' "
                "THEN store.Value END) AS FileOwner, "
                "MAX(CASE WHEN metadata.Name = 'System.ComputerName' "
                "THEN store.Value END) AS ComputerName, "
                "MAX(CASE WHEN metadata.Name = 'System.ItemType' "
                "THEN store.Value END) AS ItemType, "
                "MAX(CASE WHEN metadata.Name = 'System.ContentType' "
                "THEN store.Value END) AS ContentType, "
                "MAX(CASE WHEN metadata.Name = 'System.FileAttributes' "
                "THEN store.Value END) AS FileAttributes, "
                "MAX(CASE WHEN metadata.Name = 'System.IsFolder' "
                "THEN store.Value END) AS IsFolder, "
                "MAX(CASE WHEN metadata.Name = 'System.Title' "
                "THEN store.Value END) AS Title, "
                "MAX(CASE WHEN metadata.Name = 'System.Search.AutoSummary' "
                "THEN store.Value END) AS AutoSummary "
                "FROM SystemIndex_1_PropertyStore AS store "
                "INNER JOIN SystemIndex_1_PropertyStore_Metadata AS metadata "
                "ON store.ColumnId = metadata.Id "
                "WHERE metadata.Name IN ("
                "'System.ItemPathDisplay', 'System.Size', 'System.DateCreated', "
                "'System.DateModified', 'System.DateAccessed', "
                "'System.Search.GatherTime', 'System.FileOwner', "
                "'System.ComputerName', 'System.ItemType', 'System.ContentType', "
                "'System.FileAttributes', 'System.IsFolder', 'System.Title', "
                "'System.Search.AutoSummary') "
                "GROUP BY store.WorkId"
            ),
            "ParseIndexItemRow",
        ),
    ]

    def _GetFiletimeValue(self, query_hash, row, value_name):
        """Retrieves a FILETIME date and time value from the row.

        Args:
          query_hash (int): hash of the query, that uniquely identifies the query
              that produced the row.
          row (sqlite3.Row): row.
          value_name (str): name of the value.

        Returns:
          dfdatetime.Filetime: date and time value or None if not available.
        """
        timestamp = self._GetIntegerValue(query_hash, row, value_name)
        if not timestamp:
            return None

        return dfdatetime_filetime.Filetime(timestamp=timestamp)

    def _GetIntegerValue(self, query_hash, row, value_name):
        """Retrieves an integer value from the row.

        Args:
          query_hash (int): hash of the query, that uniquely identifies the query
              that produced the row.
          row (sqlite3.Row): row.
          value_name (str): name of the value.

        Returns:
          int: value or None if not available.
        """
        value = self._GetRowValue(query_hash, row, value_name)
        if isinstance(value, bytes):
            if len(value) != 8:
                return None

            return struct.unpack("<Q", value)[0]

        if isinstance(value, int):
            return value

        return None

    def _GetStringValue(self, query_hash, row, value_name):
        """Retrieves a string value from the row.

        Args:
          query_hash (int): hash of the query, that uniquely identifies the query
              that produced the row.
          row (sqlite3.Row): row.
          value_name (str): name of the value.

        Returns:
          str: value or None if not available.
        """
        value = self._GetRowValue(query_hash, row, value_name)
        if isinstance(value, str) and value:
            return value

        return None

    def ParseIndexItemRow(self, parser_mediator, query, row, **unused_kwargs):
        """Parses an index item row.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          query (str): query that created the row.
          row (sqlite3.Row): row.
        """
        query_hash = hash(query)

        is_folder = self._GetIntegerValue(query_hash, row, "IsFolder")
        if is_folder is not None:
            is_folder = bool(is_folder)

        event_data = WindowsSearchIndexItemEventData()
        event_data.access_time = self._GetFiletimeValue(query_hash, row, "DateAccessed")
        event_data.content_type = self._GetStringValue(query_hash, row, "ContentType")
        event_data.creation_time = self._GetFiletimeValue(
            query_hash, row, "DateCreated"
        )
        event_data.file_attributes = self._GetIntegerValue(
            query_hash, row, "FileAttributes"
        )
        event_data.gather_time = self._GetFiletimeValue(query_hash, row, "GatherTime")
        event_data.hostname = self._GetStringValue(query_hash, row, "ComputerName")
        event_data.is_folder = is_folder
        event_data.item_type = self._GetStringValue(query_hash, row, "ItemType")
        event_data.modification_time = self._GetFiletimeValue(
            query_hash, row, "DateModified"
        )
        event_data.owner = self._GetStringValue(query_hash, row, "FileOwner")
        event_data.path = self._GetStringValue(query_hash, row, "ItemPathDisplay")
        event_data.size = self._GetIntegerValue(query_hash, row, "Size")
        event_data.summary = self._GetStringValue(query_hash, row, "AutoSummary")
        event_data.title = self._GetStringValue(query_hash, row, "Title")
        event_data.work_identifier = self._GetRowValue(query_hash, row, "WorkId")

        parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(WindowsSearchPlugin)
