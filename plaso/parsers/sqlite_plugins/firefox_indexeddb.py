"""SQLite parser plugin for Mozilla Firefox IndexedDB database files."""

import dataclasses
import datetime
import json
import struct

from dfdatetime import posix_time as dfdatetime_posix_time

try:
    from dfindexeddb import errors as dfindexeddb_errors
    from dfindexeddb.indexeddb import types as dfindexeddb_types
    from dfindexeddb.indexeddb.firefox import gecko as dfindexeddb_gecko
except ImportError:
    dfindexeddb_errors = None
    dfindexeddb_gecko = None
    dfindexeddb_types = None

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class FirefoxIndexedDBRecordEventData(events.EventData):
    """Firefox IndexedDB record event data.

    Attributes:
      database_name (str): name of the IndexedDB database.
      javascript_dates (list[dfdatetime.DateTimeValues]): dates and times of
          the JavaScript Date objects stored in the value of the record.
      key (str): key of the record.
      object_store_name (str): name of the object store that contains the
          record.
      origin (str): origin, such as the URL of a web site, that owns the
          IndexedDB database.
      query (str): SQL query that was used to obtain the event data.
      value (str): value of the record.
    """

    DATA_TYPE = "firefox:indexeddb:record"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.database_name = None
        self.javascript_dates = None
        self.key = None
        self.object_store_name = None
        self.origin = None
        self.query = None
        self.value = None


class FirefoxIndexedDBPlugin(interface.SQLitePlugin):
    """SQLite parser plugin for Mozilla Firefox IndexedDB database files.

    The Mozilla Firefox IndexedDB database files are typically stored in:
    storage/default/<origin>/idb/<identifier><name>.sqlite

    The keys and values of the records are decoded with dfindexeddb.
    """

    NAME = "firefox_indexeddb"
    DATA_FORMAT = "Mozilla Firefox IndexedDB SQLite database (idb/*.sqlite) file"

    REQUIRED_STRUCTURE = {
        "database": frozenset(
            ["last_analyze_time", "last_vacuum_time", "name", "origin", "version"]
        ),
        "object_data": frozenset(
            ["data", "file_ids", "index_data_values", "key", "object_store_id"]
        ),
        "object_store": frozenset(["auto_increment", "id", "key_path", "name"]),
    }

    QUERIES = [
        (
            (
                "SELECT database.name AS database_name, database.origin AS origin, "
                "object_store.name AS object_store_name, object_data.key AS key, "
                "object_data.data AS data FROM object_data JOIN object_store ON "
                "object_data.object_store_id = object_store.id JOIN database"
            ),
            "ParseRecordRow",
        )
    ]

    SCHEMAS = [
        {
            "database": (
                "CREATE TABLE database( name TEXT PRIMARY KEY, origin TEXT NOT "
                "NULL, version INTEGER NOT NULL DEFAULT 0, last_vacuum_time INTEGER "
                "NOT NULL DEFAULT 0, last_analyze_time INTEGER NOT NULL DEFAULT 0, "
                "last_vacuum_size INTEGER NOT NULL DEFAULT 0) WITHOUT ROWID"
            ),
            "file": (
                "CREATE TABLE file (id INTEGER PRIMARY KEY, refcount INTEGER NOT "
                "NULL)"
            ),
            "index_data": (
                "CREATE TABLE index_data( index_id INTEGER NOT NULL, value BLOB NOT "
                "NULL, object_data_key BLOB NOT NULL, object_store_id INTEGER NOT "
                "NULL, value_locale BLOB, PRIMARY KEY (index_id, value, "
                "object_data_key), FOREIGN KEY (index_id) REFERENCES "
                "object_store_index(id) , FOREIGN KEY (object_store_id, "
                "object_data_key) REFERENCES object_data(object_store_id, key) ) "
                "WITHOUT ROWID"
            ),
            "object_data": (
                "CREATE TABLE object_data( object_store_id INTEGER NOT NULL, key "
                "BLOB NOT NULL, index_data_values BLOB DEFAULT NULL, file_ids TEXT, "
                "data BLOB NOT NULL, PRIMARY KEY (object_store_id, key), FOREIGN "
                "KEY (object_store_id) REFERENCES object_store(id) ) WITHOUT ROWID"
            ),
            "object_store": (
                "CREATE TABLE object_store( id INTEGER PRIMARY KEY, auto_increment "
                "INTEGER NOT NULL DEFAULT 0, name TEXT NOT NULL, key_path TEXT)"
            ),
            "object_store_index": (
                "CREATE TABLE object_store_index( id INTEGER PRIMARY KEY, "
                "object_store_id INTEGER NOT NULL, name TEXT NOT NULL, key_path "
                "TEXT NOT NULL, unique_index INTEGER NOT NULL, multientry INTEGER "
                "NOT NULL, locale TEXT, is_auto_locale BOOLEAN NOT NULL, FOREIGN "
                "KEY (object_store_id) REFERENCES object_store(id) )"
            ),
            "unique_index_data": (
                "CREATE TABLE unique_index_data( index_id INTEGER NOT NULL, value "
                "BLOB NOT NULL, object_store_id INTEGER NOT NULL, object_data_key "
                "BLOB NOT NULL, value_locale BLOB, PRIMARY KEY (index_id, value), "
                "FOREIGN KEY (index_id) REFERENCES object_store_index(id) , "
                "FOREIGN KEY (object_store_id, object_data_key) REFERENCES "
                "object_data(object_store_id, key) ) WITHOUT ROWID"
            ),
        }
    ]

    # Maximum depth of nested JavaScript values that is formatted.
    _MAXIMUM_DEPTH = 32

    # Maximum number of characters of a formatted key or value.
    _MAXIMUM_STRING_LENGTH = 1024

    _POSIX_EPOCH = datetime.datetime(1970, 1, 1)

    def _FormatJavaScriptValue(self, value, javascript_dates, visited, depth=0):
        """Formats a decoded JavaScript value as a string.

        Objects that are referenced more than once, such as circular references,
        are only formatted the first time they are encountered.

        Args:
          value (object): decoded JavaScript value.
          javascript_dates (list[datetime.datetime]): JavaScript Date values
              found in the value.
          visited (set[int]): identifiers of the objects that have been
              formatted.
          depth (Optional[int]): depth of the value in the nested JavaScript
              values.

        Returns:
          str: formatted JavaScript value.
        """
        if depth > self._MAXIMUM_DEPTH:
            return "..."

        if value is None or isinstance(value, dfindexeddb_types.Null):
            return "null"

        if isinstance(value, dfindexeddb_types.Undefined):
            return "undefined"

        if isinstance(value, bool):
            return "true" if value else "false"

        if isinstance(value, float) and value.is_integer():
            return f"{value:.0f}"

        if isinstance(value, (float, int)):
            return f"{value!s}"

        if isinstance(value, str):
            return json.dumps(value, ensure_ascii=False)

        if isinstance(value, (bytes, bytearray)):
            return f"<{len(value):d} bytes>"

        if isinstance(value, datetime.datetime):
            javascript_dates.append(value)
            return value.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        if isinstance(value, dfindexeddb_gecko.IDBKey):
            return self._FormatJavaScriptValue(
                value.value, javascript_dates, visited, depth
            )

        if id(value) in visited:
            return "<object reference>"

        visited.add(id(value))

        if isinstance(value, (dfindexeddb_types.JSArray, dfindexeddb_types.JSSet)):
            value = value.values

        if isinstance(value, dict):
            formatted_values = []
            for key, element_value in value.items():
                formatted_key = self._FormatJavaScriptValue(
                    key, javascript_dates, visited, depth + 1
                )
                formatted_value = self._FormatJavaScriptValue(
                    element_value, javascript_dates, visited, depth + 1
                )
                formatted_values.append(f"{formatted_key:s}: {formatted_value:s}")

            formatted_values = ", ".join(formatted_values)
            return f"{{{formatted_values:s}}}"

        if isinstance(value, (list, set, tuple)):
            formatted_values = [
                self._FormatJavaScriptValue(
                    element_value, javascript_dates, visited, depth + 1
                )
                for element_value in value
            ]
            if isinstance(value, set):
                formatted_values = sorted(formatted_values)

            formatted_values = ", ".join(formatted_values)
            return f"[{formatted_values:s}]"

        if dataclasses.is_dataclass(value):
            formatted_values = []
            for field in dataclasses.fields(value):
                formatted_value = self._FormatJavaScriptValue(
                    getattr(value, field.name, None),
                    javascript_dates,
                    visited,
                    depth + 1,
                )
                formatted_values.append(f"{field.name:s}: {formatted_value:s}")

            formatted_values = ", ".join(formatted_values)
            return f"{type(value).__name__:s}({formatted_values:s})"

        return f"<{type(value).__name__:s}>"

    def _GetDateTimeValue(self, javascript_date):
        """Retrieves a date and time value from a JavaScript Date value.

        Args:
          javascript_date (datetime.datetime): JavaScript Date value.

        Returns:
          dfdatetime.PosixTimeInMicroseconds: date and time value.
        """
        if javascript_date.tzinfo:
            javascript_date = javascript_date.astimezone(datetime.timezone.utc)
            javascript_date = javascript_date.replace(tzinfo=None)

        timestamp = (javascript_date - self._POSIX_EPOCH) // datetime.timedelta(
            microseconds=1
        )
        return dfdatetime_posix_time.PosixTimeInMicroseconds(timestamp=timestamp)

    def _TruncateString(self, string):
        """Truncates a string to the maximum string length.

        Args:
          string (str): string.

        Returns:
          str: truncated string.
        """
        if len(string) > self._MAXIMUM_STRING_LENGTH:
            string = string[: self._MAXIMUM_STRING_LENGTH - 3] + "..."

        return string

    def ParseRecordRow(self, parser_mediator, query, row, **unused_kwargs):
        """Parses a record row.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          query (str): query that created the row.
          row (sqlite3.Row): row.
        """
        query_hash = hash(query)

        object_store_name = self._GetRowValue(query_hash, row, "object_store_name")

        javascript_dates = []

        encoded_key = self._GetRowValue(query_hash, row, "key")
        if not isinstance(encoded_key, bytes):
            parser_mediator.ProduceWarning(
                f"unsupported key of record in object store: {object_store_name!s}"
            )
            return

        try:
            key = dfindexeddb_gecko.IDBKey.FromBytes(encoded_key)
            key = self._FormatJavaScriptValue(key, javascript_dates, set())

        except (
            dfindexeddb_errors.DecoderError,
            dfindexeddb_errors.ParserError,
            IndexError,
            NotImplementedError,
            OSError,
            OverflowError,
            TypeError,
            ValueError,
            struct.error,
        ) as exception:
            parser_mediator.ProduceWarning(
                f"unable to decode key of record in object store: "
                f"{object_store_name!s} with error: {exception!s}"
            )
            return

        encoded_value = self._GetRowValue(query_hash, row, "data")
        if not isinstance(encoded_value, bytes):
            encoded_value = b""

        try:
            value = dfindexeddb_gecko.JSStructuredCloneDecoder.FromBytes(encoded_value)
            value = self._FormatJavaScriptValue(value, javascript_dates, set())

        except (
            dfindexeddb_errors.DecoderError,
            dfindexeddb_errors.ParserError,
            IndexError,
            NotImplementedError,
            OSError,
            OverflowError,
            TypeError,
            ValueError,
            struct.error,
        ) as exception:
            parser_mediator.ProduceWarning(
                f"unable to decode value of record with key: {key:s} in object "
                f"store: {object_store_name!s} with error: {exception!s}"
            )
            value = None

        event_data = FirefoxIndexedDBRecordEventData()
        event_data.database_name = self._GetRowValue(query_hash, row, "database_name")
        event_data.javascript_dates = [
            self._GetDateTimeValue(javascript_date)
            for javascript_date in javascript_dates
        ] or None
        event_data.key = self._TruncateString(key)
        event_data.object_store_name = object_store_name
        event_data.origin = self._GetRowValue(query_hash, row, "origin")
        event_data.query = query

        if value is not None:
            event_data.value = self._TruncateString(value)

        parser_mediator.ProduceEventData(event_data)


# The plugin is only registered if dfindexeddb is available.
if dfindexeddb_gecko:
    sqlite.SQLiteParser.RegisterPlugin(FirefoxIndexedDBPlugin)
