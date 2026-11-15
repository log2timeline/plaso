"""Parser for the Windows Update datastore ESE database (DataStore.edb)."""

import uuid

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import ole_automation_date as dfdatetime_ole_automation_date

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import esedb
from plaso.parsers.esedb_plugins import interface


class WindowsUpdateDatastoreFileEventData(events.EventData):
    """Windows Update datastore tbFiles table event data.

    Attributes:
      digest (str): digest (hash) of the file.
      digest_algorithm (str): algorithm of the digest.
      file_size (int): size of the file.
      identifier (int): local identifier of the file.
      modification_time (dfdatetime.DateTimeValues): file modification date and
          time.
      name (str): name of the file.
      server_identifier (str): identifier (GUID) of the update service the URL
          applies to.
      strong_digest (str): strong digest (hash) of the file.
      strong_digest_algorithm (str): algorithm of the strong digest.
      url (str): URL of the file.
    """

    DATA_TYPE = "windows:update_datastore:file"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.digest = None
        self.digest_algorithm = None
        self.file_size = None
        self.identifier = None
        self.modification_time = None
        self.name = None
        self.server_identifier = None
        self.strong_digest = None
        self.strong_digest_algorithm = None
        self.url = None


class WindowsUpdateDatastoreHistoryEventData(events.EventData):
    """Windows Update datastore tbHistory table event data.

    Attributes:
      categories (str): categories of the update.
      classification (str): identifier (GUID) of the classification of the update.
      client_identifier (str): identifier of the client application that
          processed the update.
      description (str): description of the update.
      identifier (int): identifier of the history entry.
      mapped_result_code (int): mapped result code (HRESULT) of the operation on
          the update.
      more_information_url (str): URL with more information about the update.
      recorded_time (dfdatetime.DateTimeValues): date and time of the operation
          on the update.
      revision_number (int): revision number of the update.
      server_identifier (str): identifier (GUID) of the update service.
      server_selection (int): server selection.
      status (int): status of the operation on the update.
      support_url (str): support URL of the update.
      title (str): title of the update.
      unmapped_result_code (int): unmapped result code of the operation on
          the update.
      update_identifier (str): identifier (GUID) of the update.
    """

    DATA_TYPE = "windows:update_datastore:history"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.categories = None
        self.classification = None
        self.client_identifier = None
        self.description = None
        self.identifier = None
        self.mapped_result_code = None
        self.more_information_url = None
        self.recorded_time = None
        self.revision_number = None
        self.server_identifier = None
        self.server_selection = None
        self.status = None
        self.support_url = None
        self.title = None
        self.unmapped_result_code = None
        self.update_identifier = None


class WindowsUpdateDatastoreUpdateEventData(events.EventData):
    """Windows Update datastore tbUpdates table event data.

    Attributes:
      identifier (int): local identifier of the update.
      kb_article_identifiers (str): identifiers of the knowledge base (KB)
          articles of the update.
      more_information_url (str): URL with more information about the update.
      msrc_severity (str): Microsoft Security Response Center (MSRC) severity
          of the update.
      product_name (str): name of the product the update applies to.
      revision_number (int): revision number of the update.
      server_identifier (str): identifier (GUID) of the update service.
      support_url (str): support URL of the update.
      update_identifier (str): identifier (GUID) of the update.
      update_type (int): type of the update.
    """

    DATA_TYPE = "windows:update_datastore:update"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.identifier = None
        self.kb_article_identifiers = None
        self.more_information_url = None
        self.msrc_severity = None
        self.product_name = None
        self.revision_number = None
        self.server_identifier = None
        self.support_url = None
        self.update_identifier = None
        self.update_type = None


class WindowsUpdateDatastoreESEDBPlugin(interface.ESEDBPlugin):
    """Parses a Windows Update datastore ESE database file."""

    NAME = "windows_update_datastore"
    DATA_FORMAT = "Windows Update datastore ESE database (DataStore.edb) file"

    REQUIRED_TABLES = {
        "tbFiles": "ParseFilesTable",
        "tbHistory": "ParseHistoryTable",
        "tbUpdates": "ParseUpdatesTable",
    }

    _FILES_TABLE_COLUMN_NAMES = frozenset(
        [
            "Digest",
            "DigestAlgorithm",
            "IdFileLocal",
            "Modified",
            "Name",
            "Size",
            "StrongDigest",
            "StrongDigestALgorithm",
            "Urls",
        ]
    )

    _HISTORY_TABLE_COLUMN_NAMES = frozenset(
        [
            "Categories",
            "Classification",
            "ClientId",
            "Date",
            "Description",
            "IdEvent",
            "MappedResult",
            "MoreInfoUrl",
            "ServerId",
            "ServerSelection",
            "Status",
            "SupportUrl",
            "Title",
            "UnmappedResult",
            "UpdateId",
        ]
    )

    _UPDATES_TABLE_COLUMN_NAMES = frozenset(
        [
            "IdLocal",
            "KBArticleIds",
            "MoreInfoUrl",
            "MsrcSeverity",
            "ProductName",
            "RevisionNumber",
            "ServerRef",
            "SupportUrl",
            "UpdateId",
            "UpdateType",
        ]
    )

    _UNSET_FILETIME_VALUES = frozenset([0, 0xFFFFFFFFFFFFFFFF])

    def _GetBinaryDataRecordValue(self, record_values, value_name):
        """Retrieves a binary data record value.

        Args:
          record_values (dict[str,object]): values per column name.
          value_name (str): name of the record value.

        Returns:
          bytes: binary data or None if not set.
        """
        value = record_values.get(value_name)
        if not isinstance(value, bytes):
            return None

        return value

    def _GetColumnValues(
        self, parser_mediator, table_name, record_index, record, column_names
    ):
        """Retrieves the values of specific columns from the record.

        Other columns are not read, since several of them hold multiple values,
        which are currently not supported and would generate a warning for most
        records.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          table_name (str): name of the table.
          record_index (int): ESE record index.
          record (pyesedb.record): ESE record.
          column_names (set[str]): names of the columns to retrieve.

        Returns:
          dict[str,object]: values per column name, where a value that holds
              multiple values is not set.
        """
        record_values = {}

        for value_entry in range(0, record.number_of_values):
            if parser_mediator.abort:
                break

            column_name = record.get_column_name(value_entry)
            if column_name not in column_names or column_name in record_values:
                continue

            if record.is_multi_value(value_entry):
                continue

            try:
                value = self._GetRecordValue(record, value_entry)
            except ValueError as exception:
                value = None
                parser_mediator.ProduceWarning(
                    f"unable to parse value: {column_name:s} in record: "
                    f"{record_index:d} in table: {table_name:s} with error: "
                    f"{exception!s}"
                )

            record_values[column_name] = value

        return record_values

    def _GetFiletimeBinaryDataRecordValue(self, record_values, value_name):
        """Retrieves a FILETIME record value stored as binary data.

        Args:
          record_values (dict[str,object]): values per column name.
          value_name (str): name of the record value.

        Returns:
          dfdatetime.Filetime: date and time or None if not set.

        Raises:
          ParseError: if the FILETIME value cannot be parsed.
        """
        value = self._GetBinaryDataRecordValue(record_values, value_name)
        filetime = self._ConvertValueBinaryDataToULInt64(value)
        if filetime is None or filetime in self._UNSET_FILETIME_VALUES:
            return None

        return dfdatetime_filetime.Filetime(timestamp=filetime)

    def _GetGUIDRecordValue(self, record_values, value_name):
        """Retrieves a GUID record value.

        Args:
          record_values (dict[str,object]): values per column name.
          value_name (str): name of the record value.

        Returns:
          str: string representation of the GUID or None if not set.
        """
        value = record_values.get(value_name)
        if isinstance(value, uuid.UUID):
            return f"{{{value!s}}}"

        if isinstance(value, bytes):
            return self._GetGUIDString(value)

        return None

    def _GetGUIDString(self, value):
        """Retrieves the string representation of a GUID.

        Args:
          value (bytes): binary data that starts with a little-endian GUID.

        Returns:
          str: string representation of the GUID or None if not available.
        """
        if len(value) < 16:
            return None

        guid_value = uuid.UUID(bytes_le=value[:16])
        return f"{{{guid_value!s}}}"

    def _GetHexadecimalRecordValue(self, record_values, value_name):
        """Retrieves a binary data record value as a hexadecimal string.

        Args:
          record_values (dict[str,object]): values per column name.
          value_name (str): name of the record value.

        Returns:
          str: hexadecimal representation of the binary data or None if not set.
        """
        value = self._GetBinaryDataRecordValue(record_values, value_name)
        if not value:
            return None

        return value.hex()

    def _GetOLEAutomationDateRecordValue(self, record_values, value_name):
        """Retrieves an OLE automation date record value.

        The date and time column value is read as an integer, that contains
        the 64-bit floating-point value of the OLE automation date.

        Args:
          record_values (dict[str,object]): values per column name.
          value_name (str): name of the record value.

        Returns:
          dfdatetime.OLEAutomationDate: date and time or None if not set.

        Raises:
          ParseError: if the OLE automation date value cannot be parsed.
        """
        value = record_values.get(value_name)
        if not value:
            return None

        value &= 0xFFFFFFFFFFFFFFFF
        byte_stream = value.to_bytes(8, byteorder="little")
        floating_point_map = self._GetDataTypeMap("float64le")

        try:
            timestamp = self._ReadStructureFromByteStream(
                byte_stream, 0, floating_point_map
            )
        except (ValueError, errors.ParseError) as exception:
            raise errors.ParseError(
                f"Unable to parse OLE automation date with error: {exception!s}"
            )

        return dfdatetime_ole_automation_date.OLEAutomationDate(timestamp=timestamp)

    def _GetUnsignedIntegerRecordValue(self, record_values, value_name):
        """Retrieves a 32-bit integer record value as an unsigned integer.

        Args:
          record_values (dict[str,object]): values per column name.
          value_name (str): name of the record value.

        Returns:
          int: unsigned integer or None if not set.
        """
        value = record_values.get(value_name)
        if value is None:
            return None

        return value & 0xFFFFFFFF

    def ParseFilesTable(
        self, parser_mediator, database=None, table=None, **unused_kwargs
    ):
        """Parses the tbFiles table.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          database (Optional[ESEDatabase]): ESE database.
          table (Optional[pyesedb.table]): table.

        Raises:
          ValueError: if the database or table value is missing.
        """
        if database is None:
            raise ValueError("Missing database value.")

        if table is None:
            raise ValueError("Missing table value.")

        for record_index, esedb_record in enumerate(table.records):
            if parser_mediator.abort:
                break

            record_values = self._GetColumnValues(
                parser_mediator,
                table.name,
                record_index,
                esedb_record,
                self._FILES_TABLE_COLUMN_NAMES,
            )

            event_data = WindowsUpdateDatastoreFileEventData()
            event_data.digest = self._GetHexadecimalRecordValue(record_values, "Digest")
            event_data.digest_algorithm = record_values.get("DigestAlgorithm")
            event_data.file_size = record_values.get("Size")
            event_data.identifier = record_values.get("IdFileLocal")
            event_data.name = record_values.get("Name")
            event_data.strong_digest = self._GetHexadecimalRecordValue(
                record_values, "StrongDigest"
            )
            event_data.strong_digest_algorithm = record_values.get(
                "StrongDigestALgorithm"
            )

            try:
                event_data.modification_time = self._GetFiletimeBinaryDataRecordValue(
                    record_values, "Modified"
                )
            except errors.ParseError as exception:
                parser_mediator.ProduceWarning(
                    f"unable to parse value: Modified in record: {record_index:d} "
                    f"in table: {table.name:s} with error: {exception!s}"
                )

            # The Urls value was observed to consist of the identifier (GUID) of
            # an update service, that corresponds with tbHistory.ServerId and
            # tbUpdates.ServerRef, followed by an UTF-16 little-endian string
            # with end-of-string character and 2 bytes of unknown data.
            urls = self._GetBinaryDataRecordValue(record_values, "Urls")
            if urls and len(urls) > 16:
                url = urls[16:].decode("utf-16-le", errors="backslashreplace")

                event_data.server_identifier = self._GetGUIDString(urls)
                event_data.url = url.split("\x00", maxsplit=1)[0] or None

            parser_mediator.ProduceEventData(event_data)

    def ParseHistoryTable(
        self, parser_mediator, database=None, table=None, **unused_kwargs
    ):
        """Parses the tbHistory table.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          database (Optional[ESEDatabase]): ESE database.
          table (Optional[pyesedb.table]): table.

        Raises:
          ValueError: if the database or table value is missing.
        """
        if database is None:
            raise ValueError("Missing database value.")

        if table is None:
            raise ValueError("Missing table value.")

        for record_index, esedb_record in enumerate(table.records):
            if parser_mediator.abort:
                break

            record_values = self._GetColumnValues(
                parser_mediator,
                table.name,
                record_index,
                esedb_record,
                self._HISTORY_TABLE_COLUMN_NAMES,
            )

            event_data = WindowsUpdateDatastoreHistoryEventData()
            event_data.categories = record_values.get("Categories")
            event_data.classification = self._GetGUIDRecordValue(
                record_values, "Classification"
            )
            event_data.client_identifier = record_values.get("ClientId")
            event_data.description = record_values.get("Description")
            event_data.identifier = record_values.get("IdEvent")
            event_data.mapped_result_code = self._GetUnsignedIntegerRecordValue(
                record_values, "MappedResult"
            )
            event_data.more_information_url = record_values.get("MoreInfoUrl")
            event_data.server_identifier = self._GetGUIDRecordValue(
                record_values, "ServerId"
            )
            event_data.server_selection = record_values.get("ServerSelection")
            event_data.status = record_values.get("Status")
            event_data.support_url = record_values.get("SupportUrl")
            event_data.title = record_values.get("Title")
            event_data.unmapped_result_code = self._GetUnsignedIntegerRecordValue(
                record_values, "UnmappedResult"
            )

            # The Date value was observed to be in UTC.
            try:
                event_data.recorded_time = self._GetOLEAutomationDateRecordValue(
                    record_values, "Date"
                )
            except errors.ParseError as exception:
                parser_mediator.ProduceWarning(
                    f"unable to parse value: Date in record: {record_index:d} "
                    f"in table: {table.name:s} with error: {exception!s}"
                )

            # The UpdateId value consists of the identifier (GUID) of the update
            # followed by a 32-bit little-endian revision number.
            update_identifier = self._GetBinaryDataRecordValue(
                record_values, "UpdateId"
            )
            if update_identifier and len(update_identifier) == 20:
                event_data.revision_number = int.from_bytes(
                    update_identifier[16:], byteorder="little"
                )
                event_data.update_identifier = self._GetGUIDString(update_identifier)

            parser_mediator.ProduceEventData(event_data)

    def ParseUpdatesTable(
        self, parser_mediator, database=None, table=None, **unused_kwargs
    ):
        """Parses the tbUpdates table.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          database (Optional[ESEDatabase]): ESE database.
          table (Optional[pyesedb.table]): table.

        Raises:
          ValueError: if the database or table value is missing.
        """
        if database is None:
            raise ValueError("Missing database value.")

        if table is None:
            raise ValueError("Missing table value.")

        for record_index, esedb_record in enumerate(table.records):
            if parser_mediator.abort:
                break

            record_values = self._GetColumnValues(
                parser_mediator,
                table.name,
                record_index,
                esedb_record,
                self._UPDATES_TABLE_COLUMN_NAMES,
            )

            event_data = WindowsUpdateDatastoreUpdateEventData()
            event_data.identifier = record_values.get("IdLocal")
            event_data.kb_article_identifiers = record_values.get("KBArticleIds")
            event_data.more_information_url = record_values.get("MoreInfoUrl")
            event_data.msrc_severity = record_values.get("MsrcSeverity")
            event_data.product_name = record_values.get("ProductName")
            event_data.revision_number = record_values.get("RevisionNumber")
            event_data.server_identifier = self._GetGUIDRecordValue(
                record_values, "ServerRef"
            )
            event_data.support_url = record_values.get("SupportUrl")
            event_data.update_identifier = self._GetGUIDRecordValue(
                record_values, "UpdateId"
            )
            event_data.update_type = record_values.get("UpdateType")

            parser_mediator.ProduceEventData(event_data)


esedb.ESEDBParser.RegisterPlugin(WindowsUpdateDatastoreESEDBPlugin)
