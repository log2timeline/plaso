# -*- coding: utf-8 -*-
"""SQLite-based storage."""

import os
import sqlite3
import zlib

from plaso.lib import definitions
from plaso.storage import event_heaps
from plaso.storage import file_interface
from plaso.storage import identifiers
from plaso.storage import logger


class SQLiteStorageFile(file_interface.BaseStorageFile):
  """SQLite-based storage file.

  Attributes:
    format_version (int): storage format version.
    serialization_format (str): serialization format.
    storage_type (str): storage type.
  """

  _FORMAT_VERSION = 20210105

  # The earliest format version, stored in-file, that this class
  # is able to append (write).
  _APPEND_COMPATIBLE_FORMAT_VERSION = 20190309

  # The earliest format version, stored in-file, that this class
  # is able to read.
  _READ_COMPATIBLE_FORMAT_VERSION = 20190309

  # Container types that are referenced from other container types.
  _REFERENCED_CONTAINER_TYPES = (
      file_interface.BaseStorageFile._CONTAINER_TYPE_EVENT,
      file_interface.BaseStorageFile._CONTAINER_TYPE_EVENT_DATA,
      file_interface.BaseStorageFile._CONTAINER_TYPE_EVENT_DATA_STREAM,
      file_interface.BaseStorageFile._CONTAINER_TYPE_EVENT_SOURCE)

  _CREATE_METADATA_TABLE_QUERY = (
      'CREATE TABLE metadata (key TEXT, value TEXT);')

  _CREATE_TABLE_QUERY = (
      'CREATE TABLE {0:s} ('
      '_identifier INTEGER PRIMARY KEY AUTOINCREMENT,'
      '_data {1:s});')

  _CREATE_EVENT_TABLE_QUERY = (
      'CREATE TABLE {0:s} ('
      '_identifier INTEGER PRIMARY KEY AUTOINCREMENT,'
      '_timestamp BIGINT,'
      '_data {1:s});')

  _HAS_TABLE_QUERY = (
      'SELECT name FROM sqlite_master '
      'WHERE type = "table" AND name = "{0:s}"')

  # The maximum buffer size of serialized data before triggering
  # a flush to disk (64 MiB).
  _MAXIMUM_BUFFER_SIZE = 64 * 1024 * 1024

  def __init__(
      self, maximum_buffer_size=0,
      storage_type=definitions.STORAGE_TYPE_SESSION):
    """Initializes a store.

    Args:
      maximum_buffer_size (Optional[int]):
          maximum size of a single storage stream. A value of 0 indicates
          the limit is _MAXIMUM_BUFFER_SIZE.
      storage_type (Optional[str]): storage type.

    Raises:
      ValueError: if the maximum buffer size value is out of bounds.
    """
    if (maximum_buffer_size < 0 or
        maximum_buffer_size > self._MAXIMUM_BUFFER_SIZE):
      raise ValueError('Maximum buffer size value out of bounds.')

    if not maximum_buffer_size:
      maximum_buffer_size = self._MAXIMUM_BUFFER_SIZE

    super(SQLiteStorageFile, self).__init__()
    self._connection = None
    self._cursor = None
    self._maximum_buffer_size = maximum_buffer_size
    self._serialized_event_heap = event_heaps.SerializedEventHeap()

    if storage_type == definitions.STORAGE_TYPE_SESSION:
      self.compression_format = definitions.COMPRESSION_FORMAT_ZLIB
    else:
      self.compression_format = definitions.COMPRESSION_FORMAT_NONE

    self.format_version = self._FORMAT_VERSION
    self.serialization_format = definitions.SERIALIZER_FORMAT_JSON
    self.storage_type = storage_type

  def _AddAttributeContainer(
      self, container_type, container, serialized_data=None):
    """Adds an attribute container.

    Args:
      container_type (str): attribute container type.
      container (AttributeContainer): attribute container.
      serialized_data (bytes): serialized form of the container.

    Raises:
      IOError: if the attribute container cannot be serialized.
      OSError: if the attribute container cannot be serialized.
    """
    container_list = self._GetSerializedAttributeContainerList(container_type)

    identifier = identifiers.SQLTableIdentifier(
        container_type, container_list.next_sequence_number + 1)

    # This modifies the container, but the identifier is explicitly not to be
    # serialized, so it's safe to still used the already serialized form of
    # the container.
    container.SetIdentifier(identifier)

    if not serialized_data:
      serialized_data = self._SerializeAttributeContainer(container)

    container_list.PushAttributeContainer(serialized_data)

    if container_list.data_size > self._maximum_buffer_size:
      self._WriteSerializedAttributeContainerList(container_type)

  def _AddSerializedEvent(self, event, serialized_data=None):
    """Adds an serialized event.

    Args:
      event (EventObject): event.
      serialized_data (bytes): serialized form of the event.

    Raises:
      IOError: if the event cannot be serialized.
      OSError: if the event cannot be serialized.
    """
    identifier = identifiers.SQLTableIdentifier(
        self._CONTAINER_TYPE_EVENT,
        self._serialized_event_heap.number_of_events + 1)

    # This modifies the event, but the identifier is explicitly not to be
    # serialized, so it's safe to still used the already serialized form of
    # the container.
    event.SetIdentifier(identifier)

    if not serialized_data:
      serialized_data = self._SerializeAttributeContainer(event)

    self._serialized_event_heap.PushEvent(event.timestamp, serialized_data)

    if self._serialized_event_heap.data_size > self._maximum_buffer_size:
      self._WriteSerializedAttributeContainerList(self._CONTAINER_TYPE_EVENT)

  @classmethod
  def _CheckStorageMetadata(cls, metadata_values, check_readable_only=False):
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
    format_version = metadata_values.get('format_version', None)

    if not format_version:
      raise IOError('Missing format version.')

    try:
      format_version = int(format_version, 10)
    except (TypeError, ValueError):
      raise IOError('Invalid format version: {0!s}.'.format(format_version))

    if (not check_readable_only and
        format_version < cls._APPEND_COMPATIBLE_FORMAT_VERSION):
      raise IOError((
          'Format version: {0:d} is too old and can no longer be '
          'written.').format(format_version))

    if format_version < cls._READ_COMPATIBLE_FORMAT_VERSION:
      raise IOError(
          'Format version: {0:d} is too old and can no longer be read.'.format(
              format_version))

    if format_version > cls._FORMAT_VERSION:
      raise IOError(
          'Format version: {0:d} is too new and not yet supported.'.format(
              format_version))

    metadata_values['format_version'] = format_version

    compression_format = metadata_values.get('compression_format', None)
    if compression_format not in definitions.COMPRESSION_FORMATS:
      raise IOError('Unsupported compression format: {0:s}'.format(
          compression_format))

    serialization_format = metadata_values.get('serialization_format', None)
    if serialization_format != definitions.SERIALIZER_FORMAT_JSON:
      raise IOError('Unsupported serialization format: {0:s}'.format(
          serialization_format))

    storage_type = metadata_values.get('storage_type', None)
    if storage_type not in definitions.STORAGE_TYPES:
      raise IOError('Unsupported storage type: {0:s}'.format(
          storage_type))

  def _CreateAttributeContainerTable(self, container_type):
    """Creates a table for a specific attribute container type.

    Args:
      container_type (str): attribute container type.
    """
    if self.compression_format == definitions.COMPRESSION_FORMAT_ZLIB:
      data_column_type = 'BLOB'
    else:
      data_column_type = 'TEXT'

    if container_type == self._CONTAINER_TYPE_EVENT:
      query = self._CREATE_EVENT_TABLE_QUERY.format(
          container_type, data_column_type)
    else:
      query = self._CREATE_TABLE_QUERY.format(container_type, data_column_type)

    self._cursor.execute(query)

  def _GetNumberOfAttributeContainers(self, container_type):
    """Counts the number of attribute containers of the given type.

    Args:
      container_type (str): attribute container type.

    Returns:
      int: number of attribute containers of the given type.

    Raises:
      ValueError: if an unsupported container_type is provided.
    """
    if not container_type in self._CONTAINER_TYPES:
      raise ValueError('Attribute container type {0:s} is not supported'.format(
          container_type))

    if not self._HasTable(container_type):
      return 0

    # Note that this is SQLite specific, and will give inaccurate results if
    # there are DELETE commands run on the table. The Plaso SQLite storage
    # implementation does not run any DELETE commands.
    query = 'SELECT MAX(_ROWID_) FROM {0:s} LIMIT 1'.format(container_type)
    self._cursor.execute(query)
    row = self._cursor.fetchone()
    if not row:
      return 0

    return row[0] or 0

  def _GetAttributeContainerByIdentifier(self, container_type, identifier):
    """Retrieves the container with a specific identifier.

    Args:
      container_type (str): container type.
      identifier (SQLTableIdentifier): event data identifier.

    Returns:
      AttributeContainer: attribute container or None if not available.

    Raises:
      OSError: if an unsupported identifier is provided.
      IOError: if an unsupported identifier is provided.
    """
    if not isinstance(identifier, identifiers.SQLTableIdentifier):
      raise IOError('Unsupported event data identifier type: {0!s}'.format(
          type(identifier)))

    return self._GetAttributeContainerByIndex(
        container_type, identifier.row_identifier - 1)

  def _GetAttributeContainerByIndex(self, container_type, index):
    """Retrieves a specific attribute container.

    Args:
      container_type (str): attribute container type.
      index (int): attribute container index.

    Returns:
      AttributeContainer: attribute container or None if not available.

    Raises:
      IOError: when there is an error querying the storage file.
      OSError: when there is an error querying the storage file.
    """
    sequence_number = index + 1
    query = 'SELECT _data FROM {0:s} WHERE rowid = {1:d}'.format(
        container_type, sequence_number)

    try:
      self._cursor.execute(query)
    except sqlite3.OperationalError as exception:
      raise IOError('Unable to query storage file with error: {0!s}'.format(
          exception))

    if self._storage_profiler:
      self._storage_profiler.StartTiming('get_container_by_index')

    try:
      row = self._cursor.fetchone()

    finally:
      if self._storage_profiler:
        self._storage_profiler.StopTiming('get_container_by_index')

    if row:
      identifier = identifiers.SQLTableIdentifier(
          container_type, sequence_number)

      if self.compression_format == definitions.COMPRESSION_FORMAT_ZLIB:
        serialized_data = zlib.decompress(row[0])
      else:
        serialized_data = row[0]

      if self._storage_profiler:
        self._storage_profiler.Sample(
            'get_container_by_index', 'read', container_type,
            len(serialized_data), len(row[0]))

      attribute_container = self._DeserializeAttributeContainer(
          container_type, serialized_data)
      attribute_container.SetIdentifier(identifier)
      return attribute_container

    count = self._GetNumberOfAttributeContainers(container_type)
    index -= count

    serialized_data = self._GetSerializedAttributeContainerByIndex(
        container_type, index)
    attribute_container = self._DeserializeAttributeContainer(
        container_type, serialized_data)

    if attribute_container:
      identifier = identifiers.SQLTableIdentifier(
          container_type, sequence_number)
      attribute_container.SetIdentifier(identifier)
    return attribute_container

  # TODO: determine if this method should account for non-stored attribute
  # containers or that it is better to rename the method to
  # _GetStoredAttributeContainers.
  # This method has sqlite-specific arguments for filtering and sorting.
  # pylint: disable=arguments-differ
  def _GetAttributeContainers(
      self, container_type, filter_expression=None, order_by=None):
    """Retrieves a specific type of stored attribute containers.

    Args:
      container_type (str): attribute container type.
      filter_expression (Optional[str]): expression to filter results by.
      order_by (Optional[str]): name of a column to order the results by.

    Yields:
      AttributeContainer: attribute container.

    Raises:
      IOError: when there is an error querying the storage file.
      OSError: when there is an error querying the storage file.
    """
    query = 'SELECT _identifier, _data FROM {0:s}'.format(container_type)
    if filter_expression:
      query = '{0:s} WHERE {1:s}'.format(query, filter_expression)
    if order_by:
      query = '{0:s} ORDER BY {1:s}'.format(query, order_by)

    # Use a local cursor to prevent another query interrupting the generator.
    cursor = self._connection.cursor()

    try:
      cursor.execute(query)
    except sqlite3.OperationalError as exception:
      raise IOError('Unable to query storage file with error: {0!s}'.format(
          exception))

    if self._storage_profiler:
      self._storage_profiler.StartTiming('get_containers')

    try:
      row = cursor.fetchone()

    finally:
      if self._storage_profiler:
        self._storage_profiler.StopTiming('get_containers')

    while row:
      identifier = identifiers.SQLTableIdentifier(container_type, row[0])

      if self.compression_format == definitions.COMPRESSION_FORMAT_ZLIB:
        serialized_data = zlib.decompress(row[1])
      else:
        serialized_data = row[1]

      if self._storage_profiler:
        self._storage_profiler.Sample(
            'get_containers', 'read', container_type, len(serialized_data),
            len(row[1]))

      attribute_container = self._DeserializeAttributeContainer(
          container_type, serialized_data)
      attribute_container.SetIdentifier(identifier)
      yield attribute_container

      row = cursor.fetchone()

  # TODO: determine if this method should account for non-stored attribute
  # containers or that it is better to rename the method to
  # _HasStoredAttributeContainers.
  def _HasAttributeContainers(self, container_type):
    """Determines if store contains a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.

    Returns:
      bool: True if the store contains the specified type of attribute
          containers.
    """
    count = self._GetNumberOfAttributeContainers(container_type)
    return count > 0

  def _HasTable(self, table_name):
    """Determines if a specific table exists.

    Args:
      table_name (str): name of the table.

    Returns:
      bool: True if the table exists, false otherwise.
    """
    query = self._HAS_TABLE_QUERY.format(table_name)

    self._cursor.execute(query)
    return bool(self._cursor.fetchone())

  def _ReadAndCheckStorageMetadata(self, check_readable_only=False):
    """Reads storage metadata and checks that the values are valid.

    Args:
      check_readable_only (Optional[bool]): whether the store should only be
          checked to see if it can be read. If False, the store will be checked
          to see if it can be read and written to.
    """
    query = 'SELECT key, value FROM metadata'
    self._cursor.execute(query)

    metadata_values = {row[0]: row[1] for row in self._cursor.fetchall()}

    self._CheckStorageMetadata(
        metadata_values, check_readable_only=check_readable_only)

    self.format_version = metadata_values['format_version']
    self.compression_format = metadata_values['compression_format']
    self.serialization_format = metadata_values['serialization_format']
    self.storage_type = metadata_values['storage_type']

  def _UpdateEventDataIdentifierAfterDeserialize(self, event):
    """Updates the event data identifier after deserialization.

    Args:
      event (EventObject): event.

    Raises:
      ValueError: if the event data row identifier attribute is missing.
    """
    row_identifier = getattr(event, '_event_data_row_identifier', None)
    if row_identifier is None:
      raise ValueError('Missing event data row identifier attribute')

    event_data_identifier = identifiers.SQLTableIdentifier(
        self._CONTAINER_TYPE_EVENT_DATA, row_identifier)
    event.SetEventDataIdentifier(event_data_identifier)

    delattr(event, '_event_data_row_identifier')

  def _UpdateEventDataIdentifierBeforeSerialize(self, event):
    """Sets the event data row identifier of an event before serialization.

    Args:
      event (EventObject): event.

    Raises:
      IOError: if the event data identifier type is not supported.
      OSError: if the event data identifier type is not supported.
    """
    event_data_identifier = event.GetEventDataIdentifier()

    if not isinstance(event_data_identifier, identifiers.SQLTableIdentifier):
      raise IOError('Unsupported event data identifier type: {0!s}'.format(
          type(event_data_identifier)))

    setattr(event, '_event_data_row_identifier',
            event_data_identifier.row_identifier)

  def _UpdateEventDataStreamIdentifierAfterDeserialize(self, event_data):
    """Updates the event data stream identifier after deserialization.

    Args:
      event_data (EventData): event data.
    """
    row_identifier = getattr(
        event_data, '_event_data_stream_row_identifier', None)
    if row_identifier is None:
      return

    event_data_stream_identifier = identifiers.SQLTableIdentifier(
        self._CONTAINER_TYPE_EVENT_DATA_STREAM, row_identifier)
    event_data.SetEventDataStreamIdentifier(event_data_stream_identifier)

    delattr(event_data, '_event_data_stream_row_identifier')

  def _UpdateEventDataStreamIdentifierBeforeSerialize(self, event_data):
    """Updates the event data stream identifier before serialization.

    Args:
      event_data (EventData): event data.

    Raises:
      IOError: if the event data stream identifier type is not supported.
      OSError: if the event data stream identifier type is not supported.
    """
    event_data_stream_identifier = event_data.GetEventDataStreamIdentifier()
    if event_data_stream_identifier is None:
      return

    if not isinstance(
        event_data_stream_identifier, identifiers.SQLTableIdentifier):
      raise IOError(
          'Unsupported event data stream identifier type: {0!s}'.format(
              type(event_data_stream_identifier)))

    setattr(event_data, '_event_data_stream_row_identifier',
            event_data_stream_identifier.row_identifier)

  def _UpdateEventIdentifierAfterDeserialize(self, event_tag):
    """Updates the event identifier of an event tag after deserialization.

    Args:
      event_tag (EventTag): event tag.

    Raises:
      ValueError: if the event row identifier attribute is missing.
    """
    row_identifier = getattr(event_tag, '_event_row_identifier', None)
    if row_identifier is None:
      raise ValueError('Missing event row identifier attribute')

    event_identifier = identifiers.SQLTableIdentifier(
        self._CONTAINER_TYPE_EVENT, row_identifier)
    event_tag.SetEventIdentifier(event_identifier)

    delattr(event_tag, '_event_row_identifier')

  def _UpdateEventIdentifierBeforeSerialize(self, event_tag):
    """Sets the event row identifier of an event tag before serialization.

    Args:
      event_tag (EventTag): event tag.

    Raises:
      IOError: if the event identifier type is not supported.
      OSError: if the event identifier type is not supported.
    """
    event_identifier = event_tag.GetEventIdentifier()
    if not isinstance(event_identifier, identifiers.SQLTableIdentifier):
      raise IOError('Unsupported event identifier type: {0!s}'.format(
          type(event_identifier)))

    setattr(event_tag, '_event_row_identifier', event_identifier.row_identifier)

  def _WriteAttributeContainer(
      self, attribute_container, serialized_data=None):
    """Writes an attribute container.

    The table for the container type must exist.

    Args:
      attribute_container (AttributeContainer): attribute container.
      serialized_data (Optional[bytes]): serialized form of the attribute
          container.
    """
    if attribute_container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT:
      timestamp, serialized_data = self._serialized_event_heap.PopEvent()
    else:
      if not serialized_data:
        serialized_data = self._SerializeAttributeContainer(
            attribute_container)

    if self.compression_format == definitions.COMPRESSION_FORMAT_ZLIB:
      compressed_data = zlib.compress(serialized_data)
      serialized_data = sqlite3.Binary(compressed_data)
    else:
      compressed_data = ''

    if attribute_container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT:
      query = 'INSERT INTO event (_timestamp, _data) VALUES (?, ?)'
      values = (timestamp, serialized_data)
    else:
      query = 'INSERT INTO {0:s} (_data) VALUES (?)'.format(
          attribute_container.CONTAINER_TYPE)
      values = (serialized_data, )

    if self._storage_profiler:
      self._storage_profiler.StartTiming('write_container')

    try:
      self._cursor.execute(query, values)

    finally:
      if self._storage_profiler:
        self._storage_profiler.StopTiming('write_container')
        self._storage_profiler.Sample(
            'write_container', 'write', attribute_container.CONTAINER_TYPE,
            len(serialized_data), len(compressed_data))

    identifier = identifiers.SQLTableIdentifier(
        attribute_container.CONTAINER_TYPE, self._cursor.lastrowid)
    attribute_container.SetIdentifier(identifier)

  def _WriteSerializedAttributeContainerList(self, container_type):
    """Writes a serialized attribute container list.

    Args:
      container_type (str): attribute container type.
    """
    if container_type == self._CONTAINER_TYPE_EVENT:
      if not self._serialized_event_heap.data_size:
        return

      number_of_attribute_containers = (
          self._serialized_event_heap.number_of_events)

    else:
      container_list = self._GetSerializedAttributeContainerList(container_type)
      if not container_list.data_size:
        return

      number_of_attribute_containers = (
          container_list.number_of_attribute_containers)

    if self._serializers_profiler:
      self._serializers_profiler.StartTiming('write')

    if container_type == self._CONTAINER_TYPE_EVENT:
      query = 'INSERT INTO event (_timestamp, _data) VALUES (?, ?)'
    else:
      query = 'INSERT INTO {0:s} (_data) VALUES (?)'.format(container_type)

    total_compressed_data_size = 0
    total_serialized_data_size = 0

    # TODO: directly use container_list instead of values_tuple_list.
    values_tuple_list = []
    for _ in range(number_of_attribute_containers):
      if container_type == self._CONTAINER_TYPE_EVENT:
        timestamp, serialized_data = self._serialized_event_heap.PopEvent()
      else:
        serialized_data = container_list.PopAttributeContainer()

      if self.compression_format == definitions.COMPRESSION_FORMAT_ZLIB:
        compressed_data = zlib.compress(serialized_data)
        serialized_data = sqlite3.Binary(compressed_data)
      else:
        compressed_data = ''

      if self._storage_profiler:
        total_compressed_data_size += len(compressed_data)
        total_serialized_data_size += len(serialized_data)

      if container_type == self._CONTAINER_TYPE_EVENT:
        values_tuple_list.append((timestamp, serialized_data))
      else:
        values_tuple_list.append((serialized_data, ))

    if self._storage_profiler:
      self._storage_profiler.StartTiming('write_containers_list')

    try:
      self._cursor.executemany(query, values_tuple_list)

    finally:
      if self._storage_profiler:
        self._storage_profiler.StopTiming('write_containers_list')
        self._storage_profiler.Sample(
            'write_containers_list', 'write', container_type,
            total_serialized_data_size, total_compressed_data_size)

    if self._serializers_profiler:
      self._serializers_profiler.StopTiming('write')

    if container_type == self._CONTAINER_TYPE_EVENT:
      self._serialized_event_heap.Empty()
    else:
      container_list.Empty()

  def _WriteStorageMetadata(self):
    """Writes the storage metadata."""
    self._cursor.execute(self._CREATE_METADATA_TABLE_QUERY)

    query = 'INSERT INTO metadata (key, value) VALUES (?, ?)'

    key = 'format_version'
    value = '{0:d}'.format(self._FORMAT_VERSION)
    self._cursor.execute(query, (key, value))

    key = 'compression_format'
    value = self.compression_format
    self._cursor.execute(query, (key, value))

    key = 'serialization_format'
    value = self.serialization_format
    self._cursor.execute(query, (key, value))

    key = 'storage_type'
    value = self.storage_type
    self._cursor.execute(query, (key, value))

  def AddEvent(self, event, serialized_data=None):
    """Adds an event.

    Args:
      event (EventObject): event.
      serialized_data (Optional[bytes]): serialized form of the event.

    Raises:
      IOError: when the storage file is closed or read-only.
      OSError: when the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

    # The serialized data is not used, as this method modifies the attribute
    # container.
    self._UpdateEventDataIdentifierBeforeSerialize(event)
    self._AddSerializedEvent(event)

  def AddEventData(self, event_data, serialized_data=None):
    """Adds event data.

    Args:
      event_data (EventData): event data.
      serialized_data (Optional[bytes]): serialized form of the event data.

    Raises:
      IOError: when the storage file is closed or read-only.
      OSError: when the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

    # The serialized data is not used, as this method modifies the attribute
    # container.
    self._UpdateEventDataStreamIdentifierBeforeSerialize(event_data)
    self._AddAttributeContainer(self._CONTAINER_TYPE_EVENT_DATA, event_data)

  def AddEventTag(self, event_tag, serialized_data=None):
    """Adds an event tag.

    Args:
      event_tag (EventTag): event tag.
      serialized_data (Optional[bytes]): serialized form of the event tag.

    Raises:
      IOError: when the storage file is closed or read-only.
      OSError: when the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

    # The serialized data is not used, as this method modifies the attribute
    # container.
    self._UpdateEventIdentifierBeforeSerialize(event_tag)
    self._AddAttributeContainer(self._CONTAINER_TYPE_EVENT_TAG, event_tag)

  @classmethod
  def CheckSupportedFormat(cls, path, check_readable_only=False):
    """Checks if the storage file format is supported.

    Args:
      path (str): path to the storage file.
      check_readable_only (Optional[bool]): whether the store should only be
          checked to see if it can be read. If False, the store will be checked
          to see if it can be read and written to.

    Returns:
      bool: True if the format is supported.
    """
    try:
      connection = sqlite3.connect(
          path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)

      cursor = connection.cursor()

      query = 'SELECT * FROM metadata'
      cursor.execute(query)

      metadata_values = {row[0]: row[1] for row in cursor.fetchall()}

      cls._CheckStorageMetadata(
          metadata_values, check_readable_only=check_readable_only)

      connection.close()
      result = True

    except (IOError, sqlite3.DatabaseError):
      result = False

    return result

  def Close(self):
    """Closes the file.

    Raises:
      IOError: if the storage file is already closed.
      OSError: if the storage file is already closed.
    """
    if not self._is_open:
      raise IOError('Storage file already closed.')

    if not self._read_only:
      self._WriteSerializedAttributeContainerList(
          self._CONTAINER_TYPE_ANALYSIS_REPORT)
      self._WriteSerializedAttributeContainerList(
          self._CONTAINER_TYPE_EVENT_SOURCE)
      self._WriteSerializedAttributeContainerList(
          self._CONTAINER_TYPE_EVENT_DATA_STREAM)
      self._WriteSerializedAttributeContainerList(
          self._CONTAINER_TYPE_EVENT_DATA)
      self._WriteSerializedAttributeContainerList(self._CONTAINER_TYPE_EVENT)
      self._WriteSerializedAttributeContainerList(
          self._CONTAINER_TYPE_EVENT_TAG)
      self._WriteSerializedAttributeContainerList(
          self._CONTAINER_TYPE_EXTRACTION_WARNING)

    if self._connection:
      # We need to run commit or not all data is stored in the database.
      self._connection.commit()
      self._connection.close()

      self._connection = None
      self._cursor = None

    self._is_open = False

  def GetEventDataByIdentifier(self, identifier):
    """Retrieves specific event data.

    Args:
      identifier (SQLTableIdentifier): event data identifier.

    Returns:
      EventData: event data or None if not available.

    Raises:
      OSError: if an invalid identifier is provided.
      IOError: if an invalid identifier is provided.
    """
    if not isinstance(identifier, identifiers.SQLTableIdentifier):
      raise IOError('Unsupported event data identifier type: {0!s}'.format(
          type(identifier)))

    event_data = self._GetAttributeContainerByIndex(
        self._CONTAINER_TYPE_EVENT_DATA, identifier.row_identifier - 1)
    if event_data:
      self._UpdateEventDataStreamIdentifierAfterDeserialize(event_data)

    return event_data

  def GetEventData(self):
    """Retrieves event data.

    Yields:
      EventData: event data.
    """
    for event_data in self._GetAttributeContainers(
        self._CONTAINER_TYPE_EVENT_DATA):
      self._UpdateEventDataStreamIdentifierAfterDeserialize(event_data)
      yield event_data

  def GetEvents(self):
    """Retrieves the events.

    Yields:
      EventObject: event.
    """
    for event in self._GetAttributeContainers(self._CONTAINER_TYPE_EVENT):
      self._UpdateEventDataIdentifierAfterDeserialize(event)
      yield event

  def GetEventSourceByIndex(self, index):
    """Retrieves a specific event source.

    Args:
      index (int): event source index.

    Returns:
      EventSource: event source or None if not available.
    """
    return self._GetAttributeContainerByIndex(
        self._CONTAINER_TYPE_EVENT_SOURCE, index)

  def GetEventTagByIdentifier(self, identifier):
    """Retrieves a specific event tag.

    Args:
      identifier (SQLTableIdentifier): event tag identifier.

    Returns:
      EventTag: event tag or None if not available.

    Raises:
      OSError: if an invalid identifier is provided.
      IOError: if an invalid identifier is provided.
    """
    if not isinstance(identifier, identifiers.SQLTableIdentifier):
      raise IOError('Unsupported event data identifier type: {0!s}'.format(
          type(identifier)))

    event_tag = self._GetAttributeContainerByIndex(
        self._CONTAINER_TYPE_EVENT_TAG, identifier.row_identifier - 1)
    if event_tag:
      self._UpdateEventIdentifierAfterDeserialize(event_tag)

    return event_tag

  def GetEventTags(self):
    """Retrieves the event tags.

    Yields:
      EventTag: event tag.
    """
    for event_tag in self._GetAttributeContainers(
        self._CONTAINER_TYPE_EVENT_TAG):
      self._UpdateEventIdentifierAfterDeserialize(event_tag)
      yield event_tag

  def GetExtractionWarnings(self):
    """Retrieves the extraction warnings.

    Returns:
      generator(ExtractionWarning): extraction warning generator.
    """
    return self._GetAttributeContainers(self._CONTAINER_TYPE_EXTRACTION_WARNING)

  def GetNumberOfEventSources(self):
    """Retrieves the number event sources.

    Returns:
      int: number of event sources.
    """
    number_of_event_sources = self._GetNumberOfAttributeContainers(
        self._CONTAINER_TYPE_EVENT_SOURCE)

    number_of_event_sources += self._GetNumberOfSerializedAttributeContainers(
        self._CONTAINER_TYPE_EVENT_SOURCE)
    return number_of_event_sources

  def GetSortedEvents(self, time_range=None):
    """Retrieves the events in increasing chronological order.

    Args:
      time_range (Optional[TimeRange]): time range used to filter events
          that fall in a specific period.

    Yield:
      EventObject: event.
    """
    filter_expression = None
    if time_range:
      filter_expression = []

      if time_range.start_timestamp:
        filter_expression.append(
            '_timestamp >= {0:d}'.format(time_range.start_timestamp))

      if time_range.end_timestamp:
        filter_expression.append(
            '_timestamp <= {0:d}'.format(time_range.end_timestamp))

      filter_expression = ' AND '.join(filter_expression)

    event_generator = self._GetAttributeContainers(
        self._CONTAINER_TYPE_EVENT, filter_expression=filter_expression,
        order_by='_timestamp')

    for event in event_generator:
      self._UpdateEventDataIdentifierAfterDeserialize(event)
      yield event

  # pylint: disable=arguments-differ
  def Open(self, path=None, read_only=True, **unused_kwargs):
    """Opens the storage.

    Args:
      path (Optional[str]): path to the storage file.
      read_only (Optional[bool]): True if the file should be opened in
          read-only mode.

    Raises:
      IOError: if the storage file is already opened or if the database
          cannot be connected.
      OSError: if the storage file is already opened or if the database
          cannot be connected.
      ValueError: if path is missing.
    """
    if self._is_open:
      raise IOError('Storage file already opened.')

    if not path:
      raise ValueError('Missing path.')

    path = os.path.abspath(path)

    connection = sqlite3.connect(
        path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)

    cursor = connection.cursor()
    if not cursor:
      return

    self._connection = connection
    self._cursor = cursor
    self._is_open = True
    self._read_only = read_only

    if read_only:
      self._ReadAndCheckStorageMetadata(check_readable_only=True)
    else:
      # self._cursor.execute('PRAGMA journal_mode=MEMORY')

      # Turn off insert transaction integrity since we want to do bulk insert.
      self._cursor.execute('PRAGMA synchronous=OFF')

      if not self._HasTable('metadata'):
        self._WriteStorageMetadata()
      else:
        self._ReadAndCheckStorageMetadata()

      for container_type in self._CONTAINER_TYPES:
        if (self.storage_type == definitions.STORAGE_TYPE_SESSION and
            container_type in self._TASK_STORE_ONLY_CONTAINER_TYPES):
          continue

        if (self.storage_type == definitions.STORAGE_TYPE_TASK and
            container_type in self._SESSION_STORE_ONLY_CONTAINER_TYPES):
          continue

        if not self._HasTable(container_type):
          self._CreateAttributeContainerTable(container_type)

      self._connection.commit()

    last_session_start = self._GetNumberOfAttributeContainers(
        self._CONTAINER_TYPE_SESSION_START)

    last_session_completion = self._GetNumberOfAttributeContainers(
        self._CONTAINER_TYPE_SESSION_COMPLETION)

    # Initialize next_sequence_number based on the file contents so that
    # SQLTableIdentifier points to the correct attribute container.
    for container_type in self._REFERENCED_CONTAINER_TYPES:
      container_list = self._GetSerializedAttributeContainerList(container_type)
      container_list.next_sequence_number = (
          self._GetNumberOfAttributeContainers(container_type))

    # TODO: handle open sessions.
    if last_session_start != last_session_completion:
      logger.warning('Detected unclosed session.')

    self._last_session = last_session_completion
