"""SQLite-based storage file."""

import ast
import json
import sqlite3
import zlib

from acstore import sqlite_store
from acstore.containers import interface as containers_interface
from acstore.helpers import schema as schema_helper

from dfdatetime import factory as dfdatetime_factory

from plaso.containers import events
from plaso.lib import definitions
from plaso.serializer import json_serializer


class SQLiteStorageFile(sqlite_store.SQLiteAttributeContainerStore):
    """SQLite-based storage file.

    Attributes:
      compression_format (str): compression format.
    """

    _FORMAT_VERSION = 20261029

    # The earliest format version, stored in-file, that this class
    # is able to append (write).
    _APPEND_COMPATIBLE_FORMAT_VERSION = 20260516

    # The earliest format version, stored in-file, that this class
    # is able to upgrade (write new format features).
    _UPGRADE_COMPATIBLE_FORMAT_VERSION = 20261029

    # The earliest format version, stored in-file, that this class
    # is able to read.
    _READ_COMPATIBLE_FORMAT_VERSION = 20260516

    _CONTAINER_TYPE_EVENT = events.EventObject.CONTAINER_TYPE
    _CONTAINER_TYPE_EVENT_DATA = events.EventData.CONTAINER_TYPE
    _CONTAINER_TYPE_EVENT_TAG = events.EventTag.CONTAINER_TYPE

    # The earliest format version that stores the event data identifier of an event
    # as an integer and the date and time values of an event in a compact form.
    _TYPED_EVENT_COLUMNS_FORMAT_VERSION = 20261029

    # Keys of serialized date and time values that are stored in a compact form.
    _COMPACT_DATE_TIME_KEYS = frozenset(["__class_name__", "__type__", "timestamp"])

    def __init__(self):
        """Initializes a SQLite-based storage file."""
        super().__init__()
        self._date_time_serializer = schema_helper.SchemaHelper.GetAttributeSerializer(
            "dfdatetime.DateTimeValues", "json"
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
        if container_type == self._CONTAINER_TYPE_EVENT:
            return self._CreateEventFromRow(column_names, row, first_column_index)

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

        return self._DeserializeAttributeContainer(container_type, serialized_data)

    def _CreateEventFromRow(self, column_names, row, first_column_index):
        """Creates an event of a row in the database.

        Supports the integer event data identifier and compact date and time values
        of typed event columns, and the string and JSON values of earlier format
        versions.

        Args:
          column_names (list[str]): names of the columns selected.
          row (sqlite.Row): row as a result from a SELECT query.
          first_column_index (int): index of the first column in row.

        Returns:
          EventObject: event.

        Raises:
          OSError: if a column value cannot be deserialized.
        """
        schema = self._GetAttributeContainerSchema(self._CONTAINER_TYPE_EVENT)

        event = events.EventObject()

        for column_index, name in enumerate(column_names, start=first_column_index):
            row_value = row[column_index]
            if row_value is None:
                continue

            if name == "_event_data_identifier" and isinstance(row_value, int):
                attribute_value = containers_interface.AttributeContainerIdentifier(
                    name=self._CONTAINER_TYPE_EVENT_DATA, sequence_number=row_value
                )

            elif name == "date_time" and not row_value.startswith("{"):
                class_name, _, timestamp = row_value.partition(":")
                try:
                    attribute_value = dfdatetime_factory.Factory.NewDateTimeValues(
                        class_name, timestamp=int(timestamp, 10)
                    )
                except (KeyError, TypeError, ValueError) as exception:
                    raise OSError(
                        f"Unable to deserialize date and time values: {row_value:s} "
                        f"with error: {exception!s}"
                    )

            else:
                data_type = schema[name]
                try:
                    attribute_value = self._schema_helper.DeserializeValue(
                        data_type, row_value
                    )
                except OSError:
                    raise OSError(
                        f"Unsupported attribute container type: "
                        f"{self._CONTAINER_TYPE_EVENT:s} attribute: {name:s} data "
                        f"type: {data_type:s}"
                    )

            setattr(event, name, attribute_value)

        return event

    def _CreateAttributeContainerTable(self, container_type):
        """Creates a table for a specific attribute container type.

        Args:
          container_type (str): attribute container type.

        Raises:
          OSError: when there is an error querying the storage file or if an unsupported
              attribute container is provided.
        """
        schema = self._GetAttributeContainerSchema(container_type)
        if (
            container_type == self._CONTAINER_TYPE_EVENT
            and self.format_version >= self._TYPED_EVENT_COLUMNS_FORMAT_VERSION
        ):
            column_definitions = ["_identifier INTEGER PRIMARY KEY AUTOINCREMENT"]
            for name, data_type in sorted(schema.items()):
                if name == "_event_data_identifier":
                    column_type = "INTEGER"
                else:
                    column_type = self._schema_helper.GetStorageDataType(data_type)
                column_definitions.append(f"{name:s} {column_type:s}")

            column_definitions = ", ".join(column_definitions)
            query = f"CREATE TABLE {container_type:s} ({column_definitions:s});"
            try:
                self._cursor.execute(query)
            except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
                raise OSError(f"Unable to query storage file with error: {exception!s}")

        elif schema and container_type != self._CONTAINER_TYPE_EVENT_DATA:
            super()._CreateAttributeContainerTable(container_type)
        else:
            if self.compression_format == definitions.COMPRESSION_FORMAT_ZLIB:
                data_column_type = "BLOB"
            else:
                data_column_type = "TEXT"

            query = (
                f"CREATE TABLE {container_type:s} (_identifier INTEGER PRIMARY KEY "
                f"AUTOINCREMENT, _data {data_column_type:s});"
            )
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
                event_data_stream_identifier = container.GetEventDataStreamIdentifier()
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

    def _SerializeEventColumnValue(self, name, data_type, value):
        """Serializes an event attribute value into a typed event column value.

        Args:
          name (str): name of the attribute.
          data_type (str): schema data type of the attribute.
          value (object): runtime value of the attribute.

        Returns:
          object: column value.

        Raises:
          OSError: if the attribute value cannot be serialized.
        """
        if value is None:
            return None

        if name == "_event_data_identifier":
            if value.name == self._CONTAINER_TYPE_EVENT_DATA:
                return value.sequence_number

        elif name == "date_time":
            json_dict = self._date_time_serializer.SerializeValue(value)
            timestamp = json_dict.get("timestamp")
            if json_dict.keys() == self._COMPACT_DATE_TIME_KEYS and isinstance(
                timestamp, int
            ):
                class_name = json_dict["__class_name__"]
                return f"{class_name:s}:{timestamp:d}"

            return json.dumps(json_dict)

        try:
            return self._schema_helper.SerializeValue(data_type, value)
        except OSError:
            raise OSError(
                f"Unsupported attribute container type: "
                f"{self._CONTAINER_TYPE_EVENT:s} attribute: {name:s} data type: "
                f"{data_type:s}"
            )

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
        if (
            container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT
            and self.format_version >= self._TYPED_EVENT_COLUMNS_FORMAT_VERSION
        ):
            self._WriteNewEvent(container, schema)

        elif schema and container.CONTAINER_TYPE != self._CONTAINER_TYPE_EVENT_DATA:
            super()._WriteNewAttributeContainer(container)
        else:
            next_sequence_number = self._GetAttributeContainerNextSequenceNumber(
                container.CONTAINER_TYPE
            )
            if next_sequence_number == 1 and not self._HasTable(
                container.CONTAINER_TYPE
            ):
                self._CreateAttributeContainerTable(container.CONTAINER_TYPE)

            identifier = containers_interface.AttributeContainerIdentifier(
                name=container.CONTAINER_TYPE, sequence_number=next_sequence_number
            )
            container.SetIdentifier(identifier)

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

            column_names = ["_data"]
            values = [column_value]

            self._CacheAttributeContainerForWrite(
                container.CONTAINER_TYPE, column_names, values
            )
            self._CacheAttributeContainerByIndex(container, next_sequence_number - 1)

    def _WriteNewEvent(self, event, schema):
        """Writes a new event to the store with typed event columns.

        The table for the event container type is created if needed.

        Args:
          event (EventObject): event.
          schema (dict[str, str]): schema of the event container type.

        Raises:
          OSError: when there is an error querying the storage file.
        """
        next_sequence_number = self._GetAttributeContainerNextSequenceNumber(
            event.CONTAINER_TYPE
        )
        if next_sequence_number == 1 and not self._HasTable(event.CONTAINER_TYPE):
            self._CreateAttributeContainerTable(event.CONTAINER_TYPE)

        identifier = containers_interface.AttributeContainerIdentifier(
            name=event.CONTAINER_TYPE, sequence_number=next_sequence_number
        )
        event.SetIdentifier(identifier)

        column_names = []
        values = []
        for name, data_type in sorted(schema.items()):
            attribute_value = getattr(event, name, None)
            column_names.append(name)
            values.append(
                self._SerializeEventColumnValue(name, data_type, attribute_value)
            )

        self._CacheAttributeContainerForWrite(
            event.CONTAINER_TYPE, column_names, values
        )
        self._CacheAttributeContainerByIndex(event, next_sequence_number - 1)

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

        column_names = ["_data"]

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
                column_names=["_data"],
                filter_expression=sql_filter_expression,
            )

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
