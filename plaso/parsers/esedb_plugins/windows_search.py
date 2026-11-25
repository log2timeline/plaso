"""Parser for the Windows Search ESE database (Windows.edb).

The Windows Search (also known as Windows Desktop Search) database stores
the properties of the items indexed by the Windows Search service. This plugin
supports the Windows 7 format, where the item properties are stored in the
SystemIndex_0A table with one column per property.
"""

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import esedb
from plaso.parsers.esedb_plugins import interface


class WindowsSearchItemEventData(events.EventData):
    """Windows Search indexed item event data.

    Attributes:
      access_time (dfdatetime.DateTimeValues): date and time the item was last
          accessed.
      creation_time (dfdatetime.DateTimeValues): date and time the item was
          created.
      document_identifier (int): Windows Search document identifier.
      file_attribute_flags (int): file attribute flags.
      file_owner (str): owner of the file.
      file_size (int): size of the file.
      gather_time (dfdatetime.DateTimeValues): date and time the item was last
          gathered (indexed) by Windows Search.
      hostname (str): name of the computer that contains the item.
      item_path (str): display path of the item.
      item_url (str): URL of the item.
      modification_time (dfdatetime.DateTimeValues): date and time the item was
          last modified.
    """

    DATA_TYPE = "windows:search:item"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.access_time = None
        self.creation_time = None
        self.document_identifier = None
        self.file_attribute_flags = None
        self.file_owner = None
        self.file_size = None
        self.gather_time = None
        self.hostname = None
        self.item_path = None
        self.item_url = None
        self.modification_time = None


class WindowsSearchESEDBPlugin(interface.ESEDBPlugin):
    """Parses a Windows Search ESE database file."""

    NAME = "windows_search"
    DATA_FORMAT = "Windows 7 Search ESE database (Windows.edb) file"

    REQUIRED_TABLES = {
        "SystemIndex_0A": "ParseSystemIndexTable",
        "SystemIndex_0P": "",
        "SystemIndex_Gthr": "",
    }

    # Columns that contain a 64-bit big-endian integer stored as binary data.
    _BIG_ENDIAN_INTEGER_COLUMNS = frozenset(
        [
            "System_DateAccessed",
            "System_DateCreated",
            "System_DateModified",
            "System_Search_GatherTime",
            "System_Size",
        ]
    )

    # Windows Search fills values that are not set, such as the size of
    # a directory, with "*" (0x2a) bytes.
    _EMPTY_VALUE_BYTE = b"*"

    _SUPPORTED_COLUMNS = frozenset(
        [
            "DocID",
            "System_ComputerName",
            "System_DateAccessed",
            "System_DateCreated",
            "System_DateModified",
            "System_FileAttributes",
            "System_FileOwner",
            "System_ItemPathDisplay",
            "System_ItemUrl",
            "System_Search_GatherTime",
            "System_Size",
        ]
    )

    def _GetSupportedRecordValues(
        self, parser_mediator, table_name, record_index, record, column_indexes
    ):
        """Retrieves the values of the supported columns from the record.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          table_name (str): name of the table.
          record_index (int): ESE record index.
          record (pyesedb.record): ESE record.
          column_indexes (dict[str, int]): value entry per column name.

        Returns:
          dict[str,object]: values per column name, where values that are not
              set are None.
        """
        record_values = {}
        for column_name, value_entry in column_indexes.items():
            try:
                value_data = record.get_value_data(value_entry)
                if value_data and value_data == self._EMPTY_VALUE_BYTE * len(
                    value_data
                ):
                    value = None
                elif column_name in self._BIG_ENDIAN_INTEGER_COLUMNS:
                    value = self._ConvertValueBinaryDataToUBInt64(value_data)
                else:
                    value = self._GetRecordValue(record, value_entry)

            except (IOError, ValueError, errors.ParseError) as exception:
                value = None
                parser_mediator.ProduceWarning(
                    f"unable to parse value: {column_name:s} in record: "
                    f"{record_index:d} in table: {table_name:s} with error: "
                    f"{exception!s}"
                )

            record_values[column_name] = value

        return record_values

    def ParseSystemIndexTable(self, parser_mediator, table=None, **unused_kwargs):
        """Parses the SystemIndex_0A table.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          table (Optional[pyesedb.table]): table.

        Raises:
          ValueError: if the table value is missing.
        """
        if table is None:
            raise ValueError("Missing table value.")

        column_indexes = {}
        for value_entry, column in enumerate(table.columns):
            if column.name in self._SUPPORTED_COLUMNS:
                column_indexes[column.name] = value_entry

        for record_index, esedb_record in enumerate(table.records):
            if parser_mediator.abort:
                break

            record_values = self._GetSupportedRecordValues(
                parser_mediator, table.name, record_index, esedb_record, column_indexes
            )

            event_data = WindowsSearchItemEventData()
            event_data.access_time = self._GetFiletimeRecordValue(
                record_values, "System_DateAccessed"
            )
            event_data.hostname = record_values.get("System_ComputerName")
            event_data.creation_time = self._GetFiletimeRecordValue(
                record_values, "System_DateCreated"
            )
            event_data.document_identifier = record_values.get("DocID")
            event_data.file_attribute_flags = record_values.get("System_FileAttributes")
            event_data.file_owner = record_values.get("System_FileOwner")
            event_data.file_size = record_values.get("System_Size")
            event_data.gather_time = self._GetFiletimeRecordValue(
                record_values, "System_Search_GatherTime"
            )
            event_data.item_path = record_values.get("System_ItemPathDisplay")
            event_data.item_url = record_values.get("System_ItemUrl")
            event_data.modification_time = self._GetFiletimeRecordValue(
                record_values, "System_DateModified"
            )

            parser_mediator.ProduceEventData(event_data)


esedb.ESEDBParser.RegisterPlugin(WindowsSearchESEDBPlugin)
