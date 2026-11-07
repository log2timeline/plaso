"""SQLite-based storage file."""

import ast
import json
import sqlite3
import zlib

from acstore import sqlite_store
from acstore.containers import interface as containers_interface

from plaso.containers import events
from plaso.lib import definitions
from plaso.serializer import json_serializer


class SQLiteStorageFile(sqlite_store.SQLiteAttributeContainerStore):
    """SQLite-based storage file.

    Attributes:
      compression_format (str): compression format.
    """

    _FORMAT_VERSION = 20261026

    # The earliest format version, stored in-file, that this class
    # is able to append (write).
    _APPEND_COMPATIBLE_FORMAT_VERSION = 20260516

    # The earliest format version, stored in-file, that this class
    # is able to upgrade (write new format features).
    _UPGRADE_COMPATIBLE_FORMAT_VERSION = 20261026

    # The earliest format version, stored in-file, that this class
    # is able to read.
    _READ_COMPATIBLE_FORMAT_VERSION = 20260516

    # The earliest format version, stored in-file, that stores the event data
    # stream identifier of event data in a separate column, instead of in the
    # serialized data. This allows the serialized data to be copied as-is.
    _EVENT_DATA_STREAM_IDENTIFIER_COLUMN_FORMAT_VERSION = 20261026

    _CONTAINER_TYPE_EVENT = events.EventObject.CONTAINER_TYPE
    _CONTAINER_TYPE_EVENT_DATA = events.EventData.CONTAINER_TYPE
    _CONTAINER_TYPE_EVENT_TAG = events.EventTag.CONTAINER_TYPE

    def __init__(self):
        """Initializes a SQLite-based storage file."""
        super().__init__()
        self._has_event_data_stream_identifier_column = (
            self.format_version
            >= self._EVENT_DATA_STREAM_IDENTIFIER_COLUMN_FORMAT_VERSION
        )
        self._serializer = json_serializer.JSONAttributeContainerSerializer
        self._serializers_profiler = None

        self.compression_format = definitions.COMPRESSION_FORMAT_ZLIB

    def _CheckStorageMetadata(self, metadata_values, check_readable_only=False):
        """Checks the storage metadata.

        Args:
          metadata_values (dict[str, str]): metadata values per key.
          check_readable_only (Optional[bool]): whether the store should only be checked
              to see if it can be read. If False, the store will be checked to see if it
              can be read and written to.

        Raises:
          OSError: if the format version or the serializer format is not supported.
        """
        super()._CheckStorageMetadata(
            metadata_values, check_readable_only=check_readable_only
        )
        compression_format = metadata_values.get("compression_format")
        if compression_format not in definitions.COMPRESSION_FORMATS:
            raise OSError(f"Unsupported compression format: {compression_format!s}")

    def _CreateAttributeContainerFromRow(
        self, container_type, column_names, row, first_column_index
    ):
        """Creates an attribute container of a row in the database.

        Args:
          container_type (str): attribute container type.
          column_names (list[str]): names of the columns selected.
          row (sqlite.Row): row as a result from a SELECT query.
          first_column_index (int): index of the first column in row.

        Returns:
          AttributeContainer: attribute container.
        """
        schema = self._GetAttributeContainerSchema(container_type)
        if schema and container_type != self._CONTAINER_TYPE_EVENT_DATA:
            return super()._CreateAttributeContainerFromRow(
                container_type, column_names, row, first_column_index
            )

        if self.compression_format == definitions.COMPRESSION_FORMAT_ZLIB:
            compressed_data = row[first_column_index]
            serialized_data = zlib.decompress(compressed_data)
        else:
            compressed_data = b""
            serialized_data = row[first_column_index]

        if self._storage_profiler:
            self._storage_profiler.Sample(
                "read_create",
                "read",
                container_type,
                len(serialized_data),
                len(compressed_data),
            )

        container = self._DeserializeAttributeContainer(container_type, serialized_data)

        if (
            container
            and container_type == self._CONTAINER_TYPE_EVENT_DATA
            and self._has_event_data_stream_identifier_column
        ):
            identifier_string = row[first_column_index + 1]
            if identifier_string:
                event_data_stream_identifier = (
                    containers_interface.AttributeContainerIdentifier()
                )
                event_data_stream_identifier.CopyFromString(identifier_string)
                container.SetEventDataStreamIdentifier(event_data_stream_identifier)

        return container

    def _CreateAttributeContainerTable(self, container_type):
        """Creates a table for a specific attribute container type.

        Args:
          container_type (str): attribute container type.

        Raises:
          OSError: when there is an error querying the storage file or if an unsupported
              attribute container is provided.
        """
        schema = self._GetAttributeContainerSchema(container_type)
        if schema and container_type != self._CONTAINER_TYPE_EVENT_DATA:
            super()._CreateAttributeContainerTable(container_type)
        else:
            if self.compression_format == definitions.COMPRESSION_FORMAT_ZLIB:
                data_column_type = "BLOB"
            else:
                data_column_type = "TEXT"

            column_definitions = [
                "_identifier INTEGER PRIMARY KEY AUTOINCREMENT",
                f"_data {data_column_type:s}",
            ]
            if (
                container_type == self._CONTAINER_TYPE_EVENT_DATA
                and self._has_event_data_stream_identifier_column
            ):
                identifier_column_type = self._schema_helper.GetStorageDataType(
                    "AttributeContainerIdentifier"
                )
                column_definitions.append(
                    f"_event_data_stream_identifier {identifier_column_type:s}"
                )

            column_definitions = ", ".join(column_definitions)
            query = f"CREATE TABLE {container_type:s} ({column_definitions:s});"
            try:
                self._cursor.execute(query)
            except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
                raise OSError(f"Unable to query storage file with error: {exception!s}")

        if container_type == self._CONTAINER_TYPE_EVENT_TAG:
            query = "CREATE INDEX event_tag_per_event ON event_tag (_event_identifier)"
            try:
                self._cursor.execute(query)
            except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
                raise OSError(f"Unable to query storage file with error: {exception!s}")

    def _DeserializeAttributeContainer(self, container_type, serialized_data):
        """Deserializes an attribute container.

        Args:
          container_type (str): attribute container type.
          serialized_data (bytes): serialized attribute container data.

        Returns:
          AttributeContainer: attribute container or None.

        Raises:
          OSError: if the serialized data cannot be decoded.
        """
        if not serialized_data:
            return None

        if self._serializers_profiler:
            self._serializers_profiler.StartTiming(container_type)

        try:
            serialized_string = serialized_data.decode("utf-8")
            container = self._serializer.ReadSerialized(serialized_string)

        except UnicodeDecodeError as exception:
            raise OSError(f"Unable to decode serialized data with error: {exception!s}")

        except (TypeError, ValueError) as exception:
            # TODO: consider re-reading attribute container with error correction.
            raise OSError(f"Unable to read serialized data with error: {exception!s}")

        finally:
            if self._serializers_profiler:
                self._serializers_profiler.StopTiming(container_type)

        if container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_DATA:
            serialized_identifier = getattr(
                container, "_event_data_stream_identifier", None
            )
            if serialized_identifier:
                event_data_stream_identifier = (
                    containers_interface.AttributeContainerIdentifier()
                )
                event_data_stream_identifier.CopyFromString(serialized_identifier)
                container.SetEventDataStreamIdentifier(event_data_stream_identifier)

        return container

    def _GetSerializedDataColumnNames(self, container_type):
        """Retrieves the names of the columns of a serialized attribute container.

        Args:
          container_type (str): attribute container type.

        Returns:
          list[str]: names of the columns, where the first column contains the
              serialized data.
        """
        if (
            container_type == self._CONTAINER_TYPE_EVENT_DATA
            and self._has_event_data_stream_identifier_column
        ):
            return ["_data", "_event_data_stream_identifier"]

        return ["_data"]

    def _ReadAndCheckStorageMetadata(self, check_readable_only=False):
        """Reads storage metadata and checks that the values are valid.

        Args:
          check_readable_only (Optional[bool]): whether the store should only be checked
              to see if it can be read. If False, the store will be checked to see if it
              can be read and written to.

        Raises:
          OSError: when there is an error querying the attribute container store.
        """
        metadata_values = self._ReadMetadata()

        self._CheckStorageMetadata(
            metadata_values, check_readable_only=check_readable_only
        )
        self.format_version = metadata_values["format_version"]
        self.compression_format = metadata_values["compression_format"]
        self.serialization_format = metadata_values["serialization_format"]

        self._has_event_data_stream_identifier_column = (
            self.format_version
            >= self._EVENT_DATA_STREAM_IDENTIFIER_COLUMN_FORMAT_VERSION
        )

    def _SerializeAttributeContainer(self, container):
        """Serializes an attribute container.

        Args:
          container (AttributeContainer): attribute container.

        Returns:
          bytes: serialized attribute container.

        Raises:
          OSError: if the attribute container cannot be serialized.
        """
        if self._serializers_profiler:
            self._serializers_profiler.StartTiming(container.CONTAINER_TYPE)

        try:
            json_dict = self._serializer.WriteSerializedDict(container)

            if container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_DATA:
                if self._has_event_data_stream_identifier_column:
                    # The event data stream identifier is stored in a separate column.
                    json_dict.pop("_event_data_stream_identifier", None)
                else:
                    event_data_stream_identifier = (
                        container.GetEventDataStreamIdentifier()
                    )
                    if event_data_stream_identifier:
                        json_dict["_event_data_stream_identifier"] = (
                            event_data_stream_identifier.CopyToString()
                        )

            try:
                serialized_string = json.dumps(json_dict)
            except TypeError as exception:
                raise OSError(
                    f"Unable to serialize attribute container: "
                    f"{container.CONTAINER_TYPE:s} with error: {exception!s}."
                )

            if not serialized_string:
                raise OSError(
                    f"Unable to serialize attribute container: "
                    f"{container.CONTAINER_TYPE:s}"
                )

            serialized_string = serialized_string.encode("utf-8")

        finally:
            if self._serializers_profiler:
                self._serializers_profiler.StopTiming(container.CONTAINER_TYPE)

        return serialized_string

    def _WriteMetadata(self):
        """Writes metadata.

        Raises:
          OSError: when there is an error querying the attribute container store.
        """
        try:
            self._cursor.execute(self._CREATE_METADATA_TABLE_QUERY)
        except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
            raise OSError(
                f"Unable to query attribute container store with error: "
                f"{exception!s}"
            )

        self._WriteMetadataValue("format_version", f"{self._FORMAT_VERSION:d}")
        self._WriteMetadataValue("compression_format", self.compression_format)
        self._WriteMetadataValue("serialization_format", self.serialization_format)

    def _WriteNewAttributeContainer(self, container):
        """Writes a new attribute container to the store.

        The table for the container type must exist.

        Args:
          container (AttributeContainer): attribute container.

        Raises:
          OSError: when there is an error querying the storage file.
        """
        schema = self._GetAttributeContainerSchema(container.CONTAINER_TYPE)
        if schema and container.CONTAINER_TYPE != self._CONTAINER_TYPE_EVENT_DATA:
            super()._WriteNewAttributeContainer(container)
        else:
            serialized_data = self._SerializeAttributeContainer(container)

            if self.compression_format == definitions.COMPRESSION_FORMAT_ZLIB:
                compressed_data = zlib.compress(serialized_data)
                column_value = sqlite3.Binary(compressed_data)
            else:
                compressed_data = b""
                column_value = serialized_data

            if self._storage_profiler:
                self._storage_profiler.Sample(
                    "write_new",
                    "write",
                    container.CONTAINER_TYPE,
                    len(serialized_data),
                    len(compressed_data),
                )

            self._WriteNewSerializedAttributeContainer(container, column_value)

    def _WriteNewSerializedAttributeContainer(self, container, column_value):
        """Writes a new serialized attribute container to the store.

        The table for the container type is created if it does not exist.

        Args:
          container (AttributeContainer): attribute container.
          column_value (bytes|str): serialized, and optionally compressed, data of
              the attribute container, as stored in the _data column.

        Raises:
          OSError: when there is an error querying the storage file.
        """
        next_sequence_number = self._GetAttributeContainerNextSequenceNumber(
            container.CONTAINER_TYPE
        )
        if next_sequence_number == 1 and not self._HasTable(container.CONTAINER_TYPE):
            self._CreateAttributeContainerTable(container.CONTAINER_TYPE)

        identifier = containers_interface.AttributeContainerIdentifier(
            name=container.CONTAINER_TYPE, sequence_number=next_sequence_number
        )
        container.SetIdentifier(identifier)

        column_names = self._GetSerializedDataColumnNames(container.CONTAINER_TYPE)
        values = [column_value]

        if len(column_names) > 1:
            event_data_stream_identifier = container.GetEventDataStreamIdentifier()
            if event_data_stream_identifier:
                event_data_stream_identifier = (
                    event_data_stream_identifier.CopyToString()
                )

            values.append(event_data_stream_identifier)

        self._CacheAttributeContainerForWrite(
            container.CONTAINER_TYPE, column_names, values
        )
        self._CacheAttributeContainerByIndex(container, next_sequence_number - 1)

    def AddAttributeContainerWithStoredData(
        self, container, stored_data, compression_format
    ):
        """Adds a new attribute container with the data as stored in another store.

        The stored data is written as-is, without serializing and compressing the
        attribute container again, if it is compatible with this store. Otherwise
        the attribute container is serialized.

        Args:
          container (AttributeContainer): attribute container.
          stored_data (object): data of the attribute container as returned by
              GetAttributeContainersWithStoredData or None if not available.
          compression_format (str): compression format of the stored data.

        Raises:
          OSError: if the store cannot be written to.
        """
        if (
            stored_data is None
            or container.CONTAINER_TYPE != self._CONTAINER_TYPE_EVENT_DATA
            or compression_format != self.compression_format
            or not self._has_event_data_stream_identifier_column
        ):
            self.AddAttributeContainer(container)
        else:
            self._RaiseIfNotWritable()
            self._WriteNewSerializedAttributeContainer(container, stored_data)

    def GetAttributeContainerByIndex(self, container_type, index):
        """Retrieves a specific attribute container.

        Args:
          container_type (str): attribute container type.
          index (int): attribute container index.

        Returns:
          AttributeContainer: attribute container or None if not available.

        Raises:
          OSError: when the store is closed or when there is an error querying the
              storage file.
        """
        schema = self._GetAttributeContainerSchema(container_type)
        if schema and container_type != self._CONTAINER_TYPE_EVENT_DATA:
            return super().GetAttributeContainerByIndex(container_type, index)

        container = self._GetCachedAttributeContainer(container_type, index)
        if container:
            return container

        self._CommitWriteCache(container_type)

        if not self._attribute_container_sequence_numbers[container_type]:
            return None

        column_names = self._GetSerializedDataColumnNames(container_type)

        row_number = index + 1
        column_names = ", ".join(column_names)
        query = (
            f"SELECT {column_names:s} FROM {container_type:s} "
            f"WHERE rowid = {row_number:d}"
        )
        try:
            self._cursor.execute(query)
        except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
            raise OSError(f"Unable to query storage file with error: {exception!s}")

        if self._storage_profiler:
            self._storage_profiler.StartTiming("get_container_by_index")

        try:
            row = self._cursor.fetchone()

        finally:
            if self._storage_profiler:
                self._storage_profiler.StopTiming("get_container_by_index")

        if not row:
            return None

        container = self._CreateAttributeContainerFromRow(
            container_type, column_names, row, 0
        )
        identifier = containers_interface.AttributeContainerIdentifier(
            name=container_type, sequence_number=row_number
        )
        container.SetIdentifier(identifier)

        self._CacheAttributeContainerByIndex(container, index)
        return container

    def GetAttributeContainers(self, container_type, filter_expression=None):
        """Retrieves a specific type of stored attribute containers.

        Args:
          container_type (str): attribute container type.
          filter_expression (Optional[str]): expression to filter the resulting
              attribute containers by.

        Yields:
          AttributeContainer: attribute container.

        Raises:
          OSError: when there is an error querying the storage file.
        """
        schema = self._GetAttributeContainerSchema(container_type)
        if schema and container_type != self._CONTAINER_TYPE_EVENT_DATA:
            yield from super().GetAttributeContainers(
                container_type, filter_expression=filter_expression
            )
        else:
            sql_filter_expression = None
            if filter_expression:
                expression_ast = ast.parse(filter_expression, mode="eval")
                sql_filter_expression = sqlite_store.PythonAST2SQL(expression_ast.body)

            yield from self._GetAttributeContainersWithFilter(
                container_type,
                column_names=self._GetSerializedDataColumnNames(container_type),
                filter_expression=sql_filter_expression,
            )

    def GetAttributeContainersWithStoredData(self, container_type):
        """Retrieves a specific type of attribute containers and their stored data.

        The stored data is the serialized, and optionally compressed, data of
        the attribute container as stored in the _data column. It is only
        available for event data, if the event data stream identifier is stored
        in a separate column, since then the stored data contains no references
        to other attribute containers and can be copied as-is.

        Args:
          container_type (str): attribute container type.

        Yields:
          tuple[AttributeContainer, bytes|str]: attribute container and its stored
              data or None if not available.

        Raises:
          OSError: when there is an error querying the storage file.
        """
        if (
            container_type != self._CONTAINER_TYPE_EVENT_DATA
            or not self._has_event_data_stream_identifier_column
        ):
            for container in self.GetAttributeContainers(container_type):
                yield container, None

            return

        self._CommitWriteCache(container_type)

        if not self._attribute_container_sequence_numbers[container_type]:
            return

        column_names = self._GetSerializedDataColumnNames(container_type)
        column_names_string = ", ".join(column_names)

        query = f"SELECT _identifier, {column_names_string:s} FROM {container_type:s}"

        # Use a local cursor to prevent another query interrupting the generator.
        cursor = self._connection.cursor()

        try:
            cursor.execute(query)
        except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
            raise OSError(f"Unable to query storage file with error: {exception!s}")

        for row in cursor:
            container = self._CreateAttributeContainerFromRow(
                container_type, column_names, row, 1
            )
            identifier = containers_interface.AttributeContainerIdentifier(
                name=container_type, sequence_number=row[0]
            )
            container.SetIdentifier(identifier)

            yield container, row[1]

    def GetSortedEvents(self, time_range=None):
        """Retrieves the events in increasing chronological order.

        Args:
          time_range (Optional[TimeRange]): time range used to filter events that fall
              in a specific period.

        Returns:
          generator(EventObject): event generator.
        """
        schema = self._GetAttributeContainerSchema(self._CONTAINER_TYPE_EVENT)
        column_names = sorted(schema.keys())

        filter_expression = None
        if time_range:
            filter_expression = []

            if time_range.start_timestamp:
                filter_expression.append(f"timestamp >= {time_range.start_timestamp:d}")

            if time_range.end_timestamp:
                filter_expression.append(f"timestamp <= {time_range.end_timestamp:d}")

            filter_expression = " AND ".join(filter_expression)

        return self._GetAttributeContainersWithFilter(
            self._CONTAINER_TYPE_EVENT,
            column_names=column_names,
            filter_expression=filter_expression,
            order_by="timestamp",
        )

    def SetSerializersProfiler(self, serializers_profiler):
        """Sets the serializers profiler.

        Args:
          serializers_profiler (SerializersProfiler): serializers profiler.
        """
        self._serializers_profiler = serializers_profiler
