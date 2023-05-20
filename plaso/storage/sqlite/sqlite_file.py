# -*- coding: utf-8 -*-
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

  _FORMAT_VERSION = 20230327

  _APPEND_COMPATIBLE_FORMAT_VERSION = 20230327

  _UPGRADE_COMPATIBLE_FORMAT_VERSION = 20230327

  _READ_COMPATIBLE_FORMAT_VERSION = 20221023

  _READ_INCOMPATIBLE_CONTAINER_TYPES = frozenset([
      'hostname', 'operating_system', 'path', 'source_configuration',
      'time_zone', 'user_account'])

  _CONTAINER_TYPE_EVENT = events.EventObject.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_DATA = events.EventData.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_TAG = events.EventTag.CONTAINER_TYPE

  def __init__(self):
    """Initializes a SQLite-based storage file."""
    super(SQLiteStorageFile, self).__init__()
    self._serializer = json_serializer.JSONAttributeContainerSerializer
    self._serializers_profiler = None

    self.compression_format = definitions.COMPRESSION_FORMAT_ZLIB

  def _CheckStorageMetadata(self, metadata_values, check_readable_only=False):
    """Checks the storage metadata.

    Args:
      metadata_values (dict[str, str]): metadata values per key.
      check_readable_only (Optional[bool]): whether the store should only be
          checked to see if it can be read. If False, the store will be checked
          to see if it can be read and written to.

    Raises:
      IOError: if the format version or the serializer format is not supported.
      OSError: if the format version or the serializer format is not supported.
    """
    super(SQLiteStorageFile, self)._CheckStorageMetadata(
        metadata_values, check_readable_only=check_readable_only)

    compression_format = metadata_values.get('compression_format', None)
    if compression_format not in definitions.COMPRESSION_FORMATS:
      raise IOError('Unsupported compression format: {0!s}'.format(
          compression_format))

  def _CreateAttributeContainerFromRow(
      self, container_type, column_names, row, first_column_index):
    """Creates an attribute container of a row in the database.

    Args:
      container_type (str): attribute container type.
      column_names (list[str]): names of the columns selected.
      row (sqlite.Row): row as a result from a SELECT query.
      first_column_index (int): index of the first column in row.

    Returns:
      AttributeContainer: attribute container.
    """
    if self.format_version > 20221023 or container_type not in (
        self._READ_INCOMPATIBLE_CONTAINER_TYPES):
      schema = self._GetAttributeContainerSchema(container_type)
    else:
      schema = None

    if schema:
      return super(SQLiteStorageFile, self)._CreateAttributeContainerFromRow(
          container_type, column_names, row, first_column_index)

    if self.compression_format == definitions.COMPRESSION_FORMAT_ZLIB:
      compressed_data = row[first_column_index]
      serialized_data = zlib.decompress(compressed_data)
    else:
      compressed_data = b''
      serialized_data = row[first_column_index]

    if self._storage_profiler:
      self._storage_profiler.Sample(
          'read_create', 'read', container_type, len(serialized_data),
          len(compressed_data))

    return self._DeserializeAttributeContainer(container_type, serialized_data)

  def _CreateAttributeContainerTable(self, container_type):
    """Creates a table for a specific attribute container type.

    Args:
      container_type (str): attribute container type.

    Raises:
      IOError: when there is an error querying the storage file or if
          an unsupported attribute container is provided.
      OSError: when there is an error querying the storage file or if
          an unsupported attribute container is provided.
    """
    if self.format_version > 20221023 or container_type not in (
        self._READ_INCOMPATIBLE_CONTAINER_TYPES):
      schema = self._GetAttributeContainerSchema(container_type)
    else:
      schema = None

    if schema:
      super(SQLiteStorageFile, self)._CreateAttributeContainerTable(
          container_type)
    else:
      if self.compression_format == definitions.COMPRESSION_FORMAT_ZLIB:
        data_column_type = 'BLOB'
      else:
        data_column_type = 'TEXT'

      query = (
          'CREATE TABLE {0:s} (_identifier INTEGER PRIMARY KEY AUTOINCREMENT, '
          '_data {1:s});').format(container_type, data_column_type)

      try:
        self._cursor.execute(query)
      except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
        raise IOError('Unable to query storage file with error: {0!s}'.format(
            exception))

    if container_type == self._CONTAINER_TYPE_EVENT_TAG:
      query = ('CREATE INDEX event_tag_per_event '
             'ON event_tag (_event_identifier)')
      try:
        self._cursor.execute(query)
      except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
        raise IOError('Unable to query storage file with error: {0!s}'.format(
            exception))

  def _DeserializeAttributeContainer(self, container_type, serialized_data):
    """Deserializes an attribute container.

    Args:
      container_type (str): attribute container type.
      serialized_data (bytes): serialized attribute container data.

    Returns:
      AttributeContainer: attribute container or None.

    Raises:
      IOError: if the serialized data cannot be decoded.
      OSError: if the serialized data cannot be decoded.
    """
    if not serialized_data:
      return None

    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(container_type)

    try:
      serialized_string = serialized_data.decode('utf-8')
      container = self._serializer.ReadSerialized(serialized_string)

    except UnicodeDecodeError as exception:
      raise IOError('Unable to decode serialized data: {0!s}'.format(exception))

    except (TypeError, ValueError) as exception:
      # TODO: consider re-reading attribute container with error correction.
      raise IOError('Unable to read serialized data: {0!s}'.format(exception))

    finally:
      if self._serializers_profiler:
        self._serializers_profiler.StopTiming(container_type)

    if container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_DATA:
      serialized_identifier = getattr(
          container, '_event_data_stream_identifier', None)
      if serialized_identifier:
        event_data_stream_identifier = (
            containers_interface.AttributeContainerIdentifier())
        event_data_stream_identifier.CopyFromString(serialized_identifier)
        container.SetEventDataStreamIdentifier(event_data_stream_identifier)

    return container

  def _ReadAndCheckStorageMetadata(self, check_readable_only=False):
    """Reads storage metadata and checks that the values are valid.

    Args:
      check_readable_only (Optional[bool]): whether the store should only be
          checked to see if it can be read. If False, the store will be checked
          to see if it can be read and written to.

    Raises:
      IOError: when there is an error querying the attribute container store.
      OSError: when there is an error querying the attribute container store.
    """
    metadata_values = self._ReadMetadata()

    self._CheckStorageMetadata(
        metadata_values, check_readable_only=check_readable_only)

    self.format_version = metadata_values['format_version']
    self.compression_format = metadata_values['compression_format']
    self.serialization_format = metadata_values['serialization_format']

  def _SerializeAttributeContainer(self, container):
    """Serializes an attribute container.

    Args:
      container (AttributeContainer): attribute container.

    Returns:
      bytes: serialized attribute container.

    Raises:
      IOError: if the attribute container cannot be serialized.
      OSError: if the attribute container cannot be serialized.
    """
    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(container.CONTAINER_TYPE)

    try:
      json_dict = self._serializer.WriteSerializedDict(container)

      if container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_DATA:
        event_data_stream_identifier = container.GetEventDataStreamIdentifier()
        if event_data_stream_identifier:
          json_dict['_event_data_stream_identifier'] = (
              event_data_stream_identifier.CopyToString())

      try:
        serialized_string = json.dumps(json_dict)
      except TypeError as exception:
        raise IOError((
            'Unable to serialize attribute container: {0:s} with error: '
            '{1!s}.').format(container.CONTAINER_TYPE, exception))

      if not serialized_string:
        raise IOError('Unable to serialize attribute container: {0:s}.'.format(
            container.CONTAINER_TYPE))

      serialized_string = serialized_string.encode('utf-8')

    finally:
      if self._serializers_profiler:
        self._serializers_profiler.StopTiming(container.CONTAINER_TYPE)

    return serialized_string

  def _WriteExistingAttributeContainer(self, container):
    """Writes an existing attribute container to the store.

    The table for the container type is created if needed.

    Args:
      container (AttributeContainer): attribute container.

    Raises:
      IOError: when there is an error querying the storage file or if
          an unsupported identifier is provided.
      OSError: when there is an error querying the storage file or if
          an unsupported identifier is provided.
    """
    if self.format_version > 20221023 or container.CONTAINER_TYPE not in (
        self._READ_INCOMPATIBLE_CONTAINER_TYPES):
      schema = self._GetAttributeContainerSchema(container.CONTAINER_TYPE)
    else:
      schema = None

    if not schema:
      raise IOError(
          'Unsupported attribute container type: {0:s}'.format(
              container.CONTAINER_TYPE))

    identifier = container.GetIdentifier()

    self._CommitWriteCache(container.CONTAINER_TYPE)

    column_names = []
    values = []
    for name, data_type in sorted(schema.items()):
      attribute_value = getattr(container, name, None)
      if attribute_value is not None:
        if data_type == 'AttributeContainerIdentifier' and isinstance(
            attribute_value, containers_interface.AttributeContainerIdentifier):
          attribute_value = attribute_value.CopyToString()

        elif data_type == 'bool':
          attribute_value = int(attribute_value)

        elif data_type not in self._CONTAINER_SCHEMA_TO_SQLITE_TYPE_MAPPINGS:
          # TODO: add compression support
          attribute_value = self._serializer.WriteSerialized(attribute_value)

      column_names.append('{0:s} = ?'.format(name))
      values.append(attribute_value)

    query = 'UPDATE {0:s} SET {1:s} WHERE _identifier = {2:d}'.format(
        container.CONTAINER_TYPE, ', '.join(column_names),
        identifier.sequence_number)

    if self._storage_profiler:
      self._storage_profiler.StartTiming('write_existing')

    try:
      self._cursor.execute(query, values)

    except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
      raise IOError('Unable to query storage file with error: {0!s}'.format(
          exception))

    finally:
      if self._storage_profiler:
        self._storage_profiler.StopTiming('write_existing')

  def _WriteMetadata(self):
    """Writes metadata.

    Raises:
      IOError: when there is an error querying the attribute container store.
      OSError: when there is an error querying the attribute container store.
    """
    try:
      self._cursor.execute(self._CREATE_METADATA_TABLE_QUERY)
    except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
      raise IOError(
          'Unable to query attribute container store with error: {0!s}'.format(
              exception))

    self._WriteMetadataValue(
        'format_version', '{0:d}'.format(self._FORMAT_VERSION))
    self._WriteMetadataValue('compression_format', self.compression_format)
    self._WriteMetadataValue('serialization_format', self.serialization_format)

  def _WriteNewAttributeContainer(self, container):
    """Writes a new attribute container to the store.

    The table for the container type must exist.

    Args:
      container (AttributeContainer): attribute container.

    Raises:
      IOError: when there is an error querying the storage file.
      OSError: when there is an error querying the storage file.
    """
    if self.format_version > 20221023 or container.CONTAINER_TYPE not in (
        self._READ_INCOMPATIBLE_CONTAINER_TYPES):
      schema = self._GetAttributeContainerSchema(container.CONTAINER_TYPE)
    else:
      schema = None

    if schema:
      super(SQLiteStorageFile, self)._WriteNewAttributeContainer(container)
    else:
      next_sequence_number = self._GetAttributeContainerNextSequenceNumber(
          container.CONTAINER_TYPE)

      if (next_sequence_number == 1 and
          not self._HasTable(container.CONTAINER_TYPE)):
        self._CreateAttributeContainerTable(container.CONTAINER_TYPE)

      identifier = containers_interface.AttributeContainerIdentifier(
          name=container.CONTAINER_TYPE, sequence_number=next_sequence_number)
      container.SetIdentifier(identifier)

      serialized_data = self._SerializeAttributeContainer(container)

      if self.compression_format == definitions.COMPRESSION_FORMAT_ZLIB:
        compressed_data = zlib.compress(serialized_data)
        serialized_data = sqlite3.Binary(compressed_data)
      else:
        compressed_data = ''

      if self._storage_profiler:
        self._storage_profiler.Sample(
            'write_new', 'write', container.CONTAINER_TYPE,
            len(serialized_data), len(compressed_data))

      column_names = ['_data']
      values = [serialized_data]

      self._CacheAttributeContainerForWrite(
          container.CONTAINER_TYPE, column_names, values)

      self._CacheAttributeContainerByIndex(container, next_sequence_number - 1)

  def GetAttributeContainerByIndex(self, container_type, index):
    """Retrieves a specific attribute container.

    Args:
      container_type (str): attribute container type.
      index (int): attribute container index.

    Returns:
      AttributeContainer: attribute container or None if not available.

    Raises:
      IOError: when the store is closed or when there is an error querying
          the storage file.
      OSError: when the store is closed or when there is an error querying
          the storage file.
    """
    if self.format_version > 20221023 or container_type not in (
        self._READ_INCOMPATIBLE_CONTAINER_TYPES):
      schema = self._GetAttributeContainerSchema(container_type)
    else:
      schema = None

    if schema:
      return super(SQLiteStorageFile, self).GetAttributeContainerByIndex(
          container_type, index)

    container = self._GetCachedAttributeContainer(container_type, index)
    if container:
      return container

    self._CommitWriteCache(container_type)

    if not self._attribute_container_sequence_numbers[container_type]:
      return None

    column_names = ['_data']

    row_number = index + 1
    query = 'SELECT {0:s} FROM {1:s} WHERE rowid = {2:d}'.format(
        ', '.join(column_names), container_type, row_number)

    try:
      self._cursor.execute(query)
    except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
      raise IOError('Unable to query storage file with error: {0!s}'.format(
          exception))

    if self._storage_profiler:
      self._storage_profiler.StartTiming('get_container_by_index')

    try:
      row = self._cursor.fetchone()

    finally:
      if self._storage_profiler:
        self._storage_profiler.StopTiming('get_container_by_index')

    if not row:
      return None

    container = self._CreateAttributeContainerFromRow(
        container_type, column_names, row, 0)

    identifier = containers_interface.AttributeContainerIdentifier(
        name=container_type, sequence_number=row_number)
    container.SetIdentifier(identifier)

    self._CacheAttributeContainerByIndex(container, index)
    return container

  def GetAttributeContainers(self, container_type, filter_expression=None):
    """Retrieves a specific type of stored attribute containers.

    Args:
      container_type (str): attribute container type.
      filter_expression (Optional[str]): expression to filter the resulting
          attribute containers by.

    Returns:
      generator(AttributeContainer): attribute container generator.

    Raises:
      IOError: when there is an error querying the storage file.
      OSError: when there is an error querying the storage file.
    """
    if self.format_version > 20221023 or container_type not in (
        self._READ_INCOMPATIBLE_CONTAINER_TYPES):
      schema = self._GetAttributeContainerSchema(container_type)
    else:
      schema = None

    if schema:
      return super(SQLiteStorageFile, self).GetAttributeContainers(
          container_type, filter_expression=filter_expression)

    sql_filter_expression = None
    if filter_expression:
      expression_ast = ast.parse(filter_expression, mode='eval')
      sql_filter_expression = sqlite_store.PythonAST2SQL(expression_ast.body)

    return self._GetAttributeContainersWithFilter(
        container_type, column_names=['_data'],
        filter_expression=sql_filter_expression)

  def GetSortedEvents(self, time_range=None):
    """Retrieves the events in increasing chronological order.

    Args:
      time_range (Optional[TimeRange]): time range used to filter events
          that fall in a specific period.

    Returns:
      generator(EventObject): event generator.
    """
    schema = self._GetAttributeContainerSchema(self._CONTAINER_TYPE_EVENT)
    column_names = sorted(schema.keys())

    filter_expression = None
    if time_range:
      filter_expression = []

      if time_range.start_timestamp:
        filter_expression.append('timestamp >= {0:d}'.format(
            time_range.start_timestamp))

      if time_range.end_timestamp:
        filter_expression.append('timestamp <= {0:d}'.format(
            time_range.end_timestamp))

      filter_expression = ' AND '.join(filter_expression)

    return self._GetAttributeContainersWithFilter(
        self._CONTAINER_TYPE_EVENT, column_names=column_names,
        filter_expression=filter_expression, order_by='timestamp')

  def SetSerializersProfiler(self, serializers_profiler):
    """Sets the serializers profiler.

    Args:
      serializers_profiler (SerializersProfiler): serializers profiler.
    """
    self._serializers_profiler = serializers_profiler
