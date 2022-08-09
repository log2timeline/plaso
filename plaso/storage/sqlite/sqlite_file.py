# -*- coding: utf-8 -*-
"""SQLite-based storage file."""

import ast
import collections
import os
import pathlib
import sqlite3
import zlib

from plaso.containers import event_sources
from plaso.containers import events
from plaso.lib import definitions
from plaso.serializer import json_serializer
from plaso.storage import identifiers
from plaso.storage import interface


def PythonAST2SQL(ast_node):
  """Converts a Python AST to SQL.

  Args:
    ast_node (ast.Node): node of the Python AST.

  Returns:
    str: SQL statement that represents the node.

  Raises:
    TypeError: if the type of node is not supported.
  """
  if isinstance(ast_node, ast.BoolOp):
    if isinstance(ast_node.op, ast.And):
      operand = ' AND '
    elif isinstance(ast_node.op, ast.Or):
      operand = ' OR '
    else:
      raise TypeError(ast_node)

    if len(ast_node.values) != 2:
      raise TypeError(ast_node)

    sql_left = PythonAST2SQL(ast_node.values[0])
    sql_right = PythonAST2SQL(ast_node.values[1])

    return operand.join([sql_left, sql_right])

  if isinstance(ast_node, ast.Compare):
    if len(ast_node.ops) != 1:
      raise TypeError(ast_node)

    if isinstance(ast_node.ops[0], ast.Eq):
      operator = ' = '
    elif isinstance(ast_node.ops[0], ast.NotEq):
      operator = ' <> '
    else:
      raise TypeError(ast_node)

    if len(ast_node.comparators) != 1:
      raise TypeError(ast_node)

    sql_left = PythonAST2SQL(ast_node.left)
    sql_right = PythonAST2SQL(ast_node.comparators[0])

    return operator.join([sql_left, sql_right])

  if isinstance(ast_node, ast.Constant):
    if isinstance(ast_node.value, str):
      return '"{0:s}"'.format(ast_node.value)

    return str(ast_node.value)

  if isinstance(ast_node, ast.Name):
    return ast_node.id

  if isinstance(ast_node, ast.Num):
    return str(ast_node.n)

  if isinstance(ast_node, ast.Str):
    return '"{0:s}"'.format(ast_node.s)

  raise TypeError(ast_node)


class SQLiteStorageFile(interface.BaseStore):
  """SQLite-based storage file.

  Attributes:
    compression_format (str): compression format.
    format_version (int): storage format version.
    serialization_format (str): serialization format.
  """

  _CONTAINER_TYPE_EVENT = events.EventObject.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_DATA = events.EventData.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_DATA_STREAM = events.EventDataStream.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_SOURCE = event_sources.EventSource.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_TAG = events.EventTag.CONTAINER_TYPE

  _FORMAT_VERSION = 20220716

  # The earliest format version with a schema.
  _WITH_SCHEMA_FORMAT_VERSION = 20210621

  # The earliest format version, stored in-file, that this class
  # is able to append (write).
  _APPEND_COMPATIBLE_FORMAT_VERSION = 20211121

  # The earliest format version, stored in-file, that this class
  # is able to upgrade (write new format features).
  _UPGRADE_COMPATIBLE_FORMAT_VERSION = 20211121

  # The earliest format version, stored in-file, that this class
  # is able to read.
  _READ_COMPATIBLE_FORMAT_VERSION = 20211121

  # Container types to not create a table for.
  _NO_CREATE_TABLE_CONTAINER_TYPES = (
      'analyzer_result',
      'hostname',
      'mount_point',
      'operating_system',
      'path',
      'source_configuration')

  # Container types that are referenced from other container types.
  _REFERENCED_CONTAINER_TYPES = (
      _CONTAINER_TYPE_EVENT,
      _CONTAINER_TYPE_EVENT_DATA,
      _CONTAINER_TYPE_EVENT_DATA_STREAM,
      _CONTAINER_TYPE_EVENT_SOURCE)

  # TODO: automatically generate mappings
  _CONTAINER_SCHEMA_IDENTIFIER_MAPPINGS = {
      'event': [(
          'event_data',
          '_event_data_identifier',
          '_event_data_row_identifier')],
      'event_tag': [(
          'event',
          '_event_identifier',
          '_event_row_identifier')],
      'windows_eventlog_message_string': [(
          'windows_eventlog_message_file',
          '_message_file_identifier',
          '_message_file_row_identifier')],
      'windows_wevt_template_event': [(
          'windows_eventlog_message_file',
          '_message_file_identifier',
          '_message_file_row_identifier')],
      # 'windows_eventlog_provider': [(
      #     'system_configuration',
      #     '_system_configuration_identifier',
      #     '_system_configuration_row_identifier')],
  }

  _CONTAINER_SCHEMA_TO_SQLITE_TYPE_MAPPINGS = {
      'AttributeContainerIdentifier': 'INTEGER',
      'bool': 'INTEGER',
      'int': 'INTEGER',
      'str': 'TEXT',
      'timestamp': 'BIGINT'}

  _CREATE_METADATA_TABLE_QUERY = (
      'CREATE TABLE metadata (key TEXT, value TEXT);')

  _HAS_TABLE_QUERY = (
      'SELECT name FROM sqlite_master '
      'WHERE type = "table" AND name = "{0:s}"')

  _INSERT_METADATA_VALUE_QUERY = (
      'INSERT INTO metadata (key, value) VALUES (?, ?)')

  # The maximum number of cached attribute containers
  _MAXIMUM_CACHED_CONTAINERS = 32 * 1024

  def __init__(self):
    """Initializes a SQLite storage file."""
    super(SQLiteStorageFile, self).__init__()
    self._attribute_container_cache = collections.OrderedDict()
    self._connection = None
    self._cursor = None
    self._is_open = False
    self._read_only = True
    self._serializer = json_serializer.JSONAttributeContainerSerializer
    self._use_schema = True

    self.compression_format = definitions.COMPRESSION_FORMAT_ZLIB
    self.format_version = self._FORMAT_VERSION
    self.serialization_format = definitions.SERIALIZER_FORMAT_JSON

  def _CacheAttributeContainerByIndex(self, attribute_container, index):
    """Caches a specific attribute container.

    Args:
      attribute_container (AttributeContainer): attribute container.
      index (int): attribute container index.
    """
    if len(self._attribute_container_cache) >= self._MAXIMUM_CACHED_CONTAINERS:
      self._attribute_container_cache.popitem(last=True)

    lookup_key = '{0:s}.{1:d}'.format(attribute_container.CONTAINER_TYPE, index)
    self._attribute_container_cache[lookup_key] = attribute_container
    self._attribute_container_cache.move_to_end(lookup_key, last=False)

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
      raise IOError('Unsupported compression format: {0!s}'.format(
          compression_format))

    serialization_format = metadata_values.get('serialization_format', None)
    if serialization_format != definitions.SERIALIZER_FORMAT_JSON:
      raise IOError('Unsupported serialization format: {0!s}'.format(
          serialization_format))

  def _CreateAttributeContainerTable(self, container_type):
    """Creates a table for a specific attribute container type.

    Args:
      container_type (str): attribute container type.

    Raises:
      IOError: when there is an error querying the storage file.
      OSError: when there is an error querying the storage file.
    """
    column_definitions = ['_identifier INTEGER PRIMARY KEY AUTOINCREMENT']

    schema = self._GetAttributeContainerSchema(container_type)
    if self._use_schema and schema:
      for name, data_type in sorted(schema.items()):
        data_type = self._CONTAINER_SCHEMA_TO_SQLITE_TYPE_MAPPINGS.get(
              data_type, 'TEXT')
        column_definitions.append('{0:s} {1:s}'.format(name, data_type))

    else:
      if self.compression_format == definitions.COMPRESSION_FORMAT_ZLIB:
        data_column_type = 'BLOB'
      else:
        data_column_type = 'TEXT'

      if container_type == self._CONTAINER_TYPE_EVENT:
        column_definitions.append('_timestamp BIGINT')

      column_definitions.append('_data {0:s}'.format(data_column_type))

    column_definitions = ', '.join(column_definitions)
    query = 'CREATE TABLE {0:s} ({1:s});'.format(
        container_type, column_definitions)

    try:
      self._cursor.execute(query)
    except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
      raise IOError('Unable to query storage file with error: {0!s}'.format(
          exception))

    if container_type == self._CONTAINER_TYPE_EVENT_TAG:
      query = (
          'CREATE INDEX event_tag_per_event '
          'ON event_tag (_event_row_identifier)')
      try:
        self._cursor.execute(query)
      except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
        raise IOError('Unable to query storage file with error: {0!s}'.format(
            exception))

  def _CreatetAttributeContainerFromRow(
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
    schema = self._GetAttributeContainerSchema(container_type)

    if self._use_schema and schema:
      container = self._containers_manager.CreateAttributeContainer(
          container_type)

      for column_index, name in enumerate(column_names):
        attribute_value = row[first_column_index + column_index]
        if attribute_value is None:
          continue

        data_type = schema[name]
        if data_type == 'bool':
          attribute_value = bool(attribute_value)

        elif data_type not in self._CONTAINER_SCHEMA_TO_SQLITE_TYPE_MAPPINGS:
          # TODO: add compression support
          attribute_value = self._serializer.ReadSerialized(attribute_value)

        setattr(container, name, attribute_value)

    else:
      if self.compression_format == definitions.COMPRESSION_FORMAT_ZLIB:
        compressed_data = row[first_column_index]
        serialized_data = zlib.decompress(compressed_data)
      else:
        compressed_data = b''
        serialized_data = row[first_column_index]

      if self._storage_profiler:
        self._storage_profiler.Sample(
            'get_container_by_index', 'read', container_type,
            len(serialized_data), len(compressed_data))

      container = self._DeserializeAttributeContainer(
          container_type, serialized_data)

    return container

  def _GetAttributeContainersWithFilter(
      self, container_type, column_names=None, filter_expression=None,
      order_by=None):
    """Retrieves a specific type of stored attribute containers.

    Args:
      container_type (str): attribute container type.
      column_names (Optional[list[str]]): names of the columns to retrieve.
      filter_expression (Optional[str]): SQL expression to filter results by.
      order_by (Optional[str]): name of a column to order the results by.

    Yields:
      AttributeContainer: attribute container.

    Raises:
      IOError: when there is an error querying the storage file.
      OSError: when there is an error querying the storage file.
    """
    query = 'SELECT _identifier, {0:s} FROM {1:s}'.format(
        ', '.join(column_names), container_type)
    if filter_expression:
      query = ' WHERE '.join([query, filter_expression])
    if order_by:
      query = ' ORDER BY '.join([query, order_by])

    # Use a local cursor to prevent another query interrupting the generator.
    cursor = self._connection.cursor()

    try:
      cursor.execute(query)
    except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
      raise IOError((
          'Unable to query storage file for attribute container: {0:s} with '
          'error: {1!s}').format(container_type, exception))

    if self._storage_profiler:
      self._storage_profiler.StartTiming('get_containers')

    try:
      row = cursor.fetchone()

    finally:
      if self._storage_profiler:
        self._storage_profiler.StopTiming('get_containers')

    while row:
      container = self._CreatetAttributeContainerFromRow(
          container_type, column_names, row, 1)

      identifier = identifiers.SQLTableIdentifier(container_type, row[0])
      container.SetIdentifier(identifier)

      self._UpdateAttributeContainerAfterDeserialize(container)

      yield container

      if self._storage_profiler:
        self._storage_profiler.StartTiming('get_containers')

      try:
        row = cursor.fetchone()

      finally:
        if self._storage_profiler:
          self._storage_profiler.StopTiming('get_containers')

  def _GetCachedAttributeContainer(self, container_type, index):
    """Retrieves a specific cached attribute container.

    Args:
      container_type (str): attribute container type.
      index (int): attribute container index.

    Returns:
      AttributeContainer: attribute container or None if not available.

    Raises:
      IOError: when there is an error querying the storage file.
      OSError: when there is an error querying the storage file.
    """
    lookup_key = '{0:s}.{1:d}'.format(container_type, index)
    attribute_container = self._attribute_container_cache.get(lookup_key, None)
    if attribute_container:
      self._attribute_container_cache.move_to_end(lookup_key, last=False)
    return attribute_container

  def _HasTable(self, table_name):
    """Determines if a specific table exists.

    Args:
      table_name (str): name of the table.

    Returns:
      bool: True if the table exists, false otherwise.

    Raises:
      IOError: when there is an error querying the storage file.
      OSError: when there is an error querying the storage file.
    """
    query = self._HAS_TABLE_QUERY.format(table_name)

    try:
      self._cursor.execute(query)
    except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
      raise IOError('Unable to query storage file with error: {0!s}'.format(
          exception))

    return bool(self._cursor.fetchone())

  def _RaiseIfNotReadable(self):
    """Raises if the storage file is not readable.

     Raises:
      IOError: when the storage file is closed.
      OSError: when the storage file is closed.
    """
    if not self._is_open:
      raise IOError('Unable to read from closed storage file.')

  def _RaiseIfNotWritable(self):
    """Raises if the storage file is not writable.

    Raises:
      IOError: when the storage file is closed or read-only.
      OSError: when the storage file is closed or read-only.
    """
    if not self._is_open:
      raise IOError('Unable to write to closed storage file.')

    if self._read_only:
      raise IOError('Unable to write to read-only storage file.')

  def _ReadAndCheckStorageMetadata(self, check_readable_only=False):
    """Reads storage metadata and checks that the values are valid.

    Args:
      check_readable_only (Optional[bool]): whether the store should only be
          checked to see if it can be read. If False, the store will be checked
          to see if it can be read and written to.

    Raises:
      IOError: when there is an error querying the storage file.
      OSError: when there is an error querying the storage file.
    """
    query = 'SELECT key, value FROM metadata'

    try:
      self._cursor.execute(query)
    except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
      raise IOError('Unable to query storage file with error: {0!s}'.format(
          exception))

    metadata_values = {row[0]: row[1] for row in self._cursor.fetchall()}

    self._CheckStorageMetadata(
        metadata_values, check_readable_only=check_readable_only)

    self.format_version = metadata_values['format_version']
    self.compression_format = metadata_values['compression_format']
    self.serialization_format = metadata_values['serialization_format']

    self._use_schema = bool(
        self.format_version >= self._WITH_SCHEMA_FORMAT_VERSION)

  def _SerializeAttributeContainer(self, attribute_container):
    """Serializes an attribute container.

    Args:
      attribute_container (AttributeContainer): attribute container.

    Returns:
      bytes: serialized attribute container.

    Raises:
      IOError: if the attribute container cannot be serialized.
      OSError: if the attribute container cannot be serialized.
    """
    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(
          attribute_container.CONTAINER_TYPE)

    try:
      attribute_container_data = self._serializer.WriteSerialized(
          attribute_container)
      if not attribute_container_data:
        raise IOError(
            'Unable to serialize attribute container: {0:s}.'.format(
                attribute_container.CONTAINER_TYPE))

      attribute_container_data = attribute_container_data.encode('utf-8')

    finally:
      if self._serializers_profiler:
        self._serializers_profiler.StopTiming(
            attribute_container.CONTAINER_TYPE)

    return attribute_container_data

  def _UpdateAttributeContainerAfterDeserialize(self, container):
    """Updates an attribute container after deserialization.

    Args:
      container (AttributeContainer): attribute container.

    Raises:
      ValueError: if an attribute container identifier is missing.
    """
    identifier_mappings = self._CONTAINER_SCHEMA_IDENTIFIER_MAPPINGS.get(
        container.CONTAINER_TYPE, None)

    if identifier_mappings:
      for (identifier_container_type, attribute_name,
           serialized_attribute_name) in identifier_mappings:
        row_identifier = getattr(container, serialized_attribute_name, None)
        if row_identifier is None:
          raise ValueError('Missing row identifier attribute: {0:s}'.format(
              serialized_attribute_name))

        identifier = identifiers.SQLTableIdentifier(
            identifier_container_type, row_identifier)
        setattr(container, attribute_name, identifier)

        delattr(container, serialized_attribute_name)

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_DATA:
      row_identifier = getattr(
          container, '_event_data_stream_row_identifier', None)
      if row_identifier:
        event_data_stream_identifier = identifiers.SQLTableIdentifier(
            self._CONTAINER_TYPE_EVENT_DATA_STREAM, row_identifier)
        container.SetEventDataStreamIdentifier(event_data_stream_identifier)

        delattr(container, '_event_data_stream_row_identifier')

  def _UpdateAttributeContainerBeforeSerialize(self, container):
    """Updates an attribute container before serialization.

    Args:
      container (AttributeContainer): attribute container.

    Raises:
      IOError: if the attribute container identifier type is not supported.
      OSError: if the attribute container identifier type is not supported.
    """
    identifier_mappings = self._CONTAINER_SCHEMA_IDENTIFIER_MAPPINGS.get(
         container.CONTAINER_TYPE, None)

    if identifier_mappings:
      for _, attribute_name, serialized_attribute_name in identifier_mappings:
        identifier = getattr(container, attribute_name, None)
        if not isinstance(identifier, identifiers.SQLTableIdentifier):
          raise IOError((
              'Unsupported attribute container identifier type: {0!s} for: '
              '{1:s}.{2:s}').format(
                  type(identifier), container.CONTAINER_TYPE, attribute_name))

        setattr(container, serialized_attribute_name,
                identifier.sequence_number)

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_DATA:
      event_data_stream_identifier = container.GetEventDataStreamIdentifier()
      if event_data_stream_identifier:
        if not isinstance(
            event_data_stream_identifier, identifiers.SQLTableIdentifier):
          raise IOError(
              'Unsupported event data stream identifier type: {0!s}'.format(
                  type(event_data_stream_identifier)))

        setattr(container, '_event_data_stream_row_identifier',
                event_data_stream_identifier.sequence_number)

  def _UpdateStorageMetadataFormatVersion(self):
    """Updates the storage metadata format version.

    Raises:
      IOError: when there is an error querying the storage file.
      OSError: when there is an error querying the storage file.
    """
    if self.format_version >= self._UPGRADE_COMPATIBLE_FORMAT_VERSION:
      query = (
          'UPDATE metadata SET value = {0:d} '
          'WHERE key = "format_version"').format(self._FORMAT_VERSION)

      try:
        self._cursor.execute(query)
      except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
        raise IOError('Unable to query storage file with error: {0!s}'.format(
            exception))

  def _WriteExistingAttributeContainer(self, container):
    """Writes an existing attribute container to the store.

    Args:
      container (AttributeContainer): attribute container.

    Raises:
      IOError: when there is an error querying the storage file or if
          an unsupported identifier is provided.
      OSError: when there is an error querying the storage file or if
          an unsupported identifier is provided.
    """
    identifier = container.GetIdentifier()
    if not isinstance(identifier, identifiers.SQLTableIdentifier):
      raise IOError(
          'Unsupported attribute container identifier type: {0!s}'.format(
              type(identifier)))

    schema = self._GetAttributeContainerSchema(container.CONTAINER_TYPE)
    if not schema:
      raise IOError(
          'Unsupported attribute container type: {0:s}'.format(
              container.CONTAINER_TYPE))

    self._UpdateAttributeContainerBeforeSerialize(container)

    column_names = []
    values = []
    for name, data_type in sorted(schema.items()):
      attribute_value = getattr(container, name, None)
      if attribute_value is not None:
        if data_type == 'bool':
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
      IOError: when there is an error querying the storage file.
      OSError: when there is an error querying the storage file.
    """
    try:
      self._cursor.execute(self._CREATE_METADATA_TABLE_QUERY)
    except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
      raise IOError('Unable to query storage file with error: {0!s}'.format(
          exception))

    self._WriteMetadataValue(
        'format_version', '{0:d}'.format(self._FORMAT_VERSION))
    self._WriteMetadataValue('compression_format', self.compression_format)
    self._WriteMetadataValue('serialization_format', self.serialization_format)

  def _WriteMetadataValue(self, key, value):
    """Writes a metadata value.

    Args:
      key (str): key of the storage metadata.
      value (str): value of the storage metadata.

    Raises:
      IOError: when there is an error querying the storage file.
      OSError: when there is an error querying the storage file.
    """
    try:
      self._cursor.execute(self._INSERT_METADATA_VALUE_QUERY, (key, value))
    except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
      raise IOError('Unable to query storage file with error: {0!s}'.format(
          exception))

  def _WriteNewAttributeContainer(self, container):
    """Writes a new attribute container to the store.

    The table for the container type must exist.

    Args:
      container (AttributeContainer): attribute container.

    Raises:
      IOError: when there is an error querying the storage file.
      OSError: when there is an error querying the storage file.
    """
    next_sequence_number = self._GetAttributeContainerNextSequenceNumber(
        container.CONTAINER_TYPE)

    identifier = identifiers.SQLTableIdentifier(
        container.CONTAINER_TYPE, next_sequence_number)
    container.SetIdentifier(identifier)

    schema = self._GetAttributeContainerSchema(container.CONTAINER_TYPE)

    self._UpdateAttributeContainerBeforeSerialize(container)

    if self._use_schema and schema:
      column_names = []
      values = []
      for name, data_type in sorted(schema.items()):
        attribute_value = getattr(container, name, None)
        if attribute_value is not None:
          if data_type == 'bool':
            attribute_value = int(attribute_value)

          elif data_type not in self._CONTAINER_SCHEMA_TO_SQLITE_TYPE_MAPPINGS:
            # TODO: add compression support
            attribute_value = self._serializer.WriteSerialized(attribute_value)

        column_names.append(name)
        values.append(attribute_value)

    else:
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

      if container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT:
        column_names = ['_timestamp', '_data']
        values = [container.timestamp, serialized_data]

      else:
        column_names = ['_data']
        values = [serialized_data]

    query = 'INSERT INTO {0:s} ({1:s}) VALUES ({2:s})'.format(
        container.CONTAINER_TYPE, ', '.join(column_names),
        ','.join(['?'] * len(column_names)))

    if self._storage_profiler:
      self._storage_profiler.StartTiming('write_new')

    try:
      self._cursor.execute(query, values)

    except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
      raise IOError('Unable to query storage file with error: {0!s}'.format(
          exception))

    finally:
      if self._storage_profiler:
        self._storage_profiler.StopTiming('write_new')

    self._CacheAttributeContainerByIndex(container, next_sequence_number - 1)

  @classmethod
  def CheckSupportedFormat(cls, path):
    """Checks if the storage file format is supported.

    Args:
      path (str): path to the storage file.

    Returns:
      bool: True if the format is supported.
    """
    # Check if the path is an existing file, to prevent sqlite3 creating
    # an emtpy database file.
    if not os.path.isfile(path):
      return False

    try:
      connection = sqlite3.connect(
          path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)

      cursor = connection.cursor()

      query = 'SELECT * FROM metadata'
      cursor.execute(query)

      metadata_values = {row[0]: row[1] for row in cursor.fetchall()}

      format_version = metadata_values.get('format_version', None)
      if format_version:
        try:
          format_version = int(format_version, 10)
          result = True
        except (TypeError, ValueError):
          pass

      connection.close()

    except (IOError, TypeError, ValueError, sqlite3.DatabaseError):
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

    if self._connection:
      # We need to run commit or not all data is stored in the database.
      self._connection.commit()
      self._connection.close()

      self._connection = None
      self._cursor = None

    self._is_open = False

  def GetAttributeContainerByIdentifier(self, container_type, identifier):
    """Retrieves a specific type of container with a specific identifier.

    Args:
      container_type (str): container type.
      identifier (SQLTableIdentifier): attribute container identifier.

    Returns:
      AttributeContainer: attribute container or None if not available.

    Raises:
      IOError: when the store is closed or if an unsupported identifier is
          provided.
      OSError: when the store is closed or if an unsupported identifier is
          provided.
    """
    if not isinstance(identifier, identifiers.SQLTableIdentifier):
      raise IOError(
          'Unsupported attribute container identifier type: {0!s}'.format(
              type(identifier)))

    return self.GetAttributeContainerByIndex(
        container_type, identifier.sequence_number - 1)

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
    container = self._GetCachedAttributeContainer(container_type, index)
    if container:
      return container

    schema = self._GetAttributeContainerSchema(container_type)

    if self._use_schema and schema:
      column_names = sorted(schema.keys())
    else:
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

    container = self._CreatetAttributeContainerFromRow(
        container_type, column_names, row, 0)

    identifier = identifiers.SQLTableIdentifier(container_type, row_number)
    container.SetIdentifier(identifier)

    self._UpdateAttributeContainerAfterDeserialize(container)

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
    schema = self._GetAttributeContainerSchema(container_type)

    if self._use_schema and schema:
      column_names = sorted(schema.keys())
    else:
      column_names = ['_data']

    sql_filter_expression = None
    if filter_expression:
      expression_ast = ast.parse(filter_expression, mode='eval')
      sql_filter_expression = PythonAST2SQL(expression_ast.body)

    return self._GetAttributeContainersWithFilter(
        container_type, column_names=column_names,
        filter_expression=sql_filter_expression)

  def GetNumberOfAttributeContainers(self, container_type):
    """Retrieves the number of a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.

    Returns:
      int: the number of containers of a specified type.

    Raises:
      IOError: when there is an error querying the storage file.
      OSError: when there is an error querying the storage file.
    """
    if not self._HasTable(container_type):
      return 0

    # Note that this is SQLite specific, and will give inaccurate results if
    # there are DELETE commands run on the table. The Plaso SQLite storage
    # implementation does not run any DELETE commands.
    query = 'SELECT MAX(_ROWID_) FROM {0:s} LIMIT 1'.format(container_type)

    try:
      self._cursor.execute(query)
    except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
      raise IOError('Unable to query storage file with error: {0!s}'.format(
          exception))

    row = self._cursor.fetchone()
    if not row:
      return 0

    return row[0] or 0

  def GetSortedEvents(self, time_range=None):
    """Retrieves the events in increasing chronological order.

    Args:
      time_range (Optional[TimeRange]): time range used to filter events
          that fall in a specific period.

    Returns:
      generator(EventObject): event generator.
    """
    schema = self._GetAttributeContainerSchema(self._CONTAINER_TYPE_EVENT)
    if self._use_schema and schema:
      filter_column_name = 'timestamp'
      column_names = sorted(schema.keys())
    else:
      filter_column_name = '_timestamp'
      column_names = ['_data']

    filter_expression = None
    if time_range:
      filter_expression = []

      if time_range.start_timestamp:
        filter_expression.append('{0:s} >= {1:d}'.format(
            filter_column_name, time_range.start_timestamp))

      if time_range.end_timestamp:
        filter_expression.append('{0:s} <= {1:d}'.format(
            filter_column_name, time_range.end_timestamp))

      filter_expression = ' AND '.join(filter_expression)

    return self._GetAttributeContainersWithFilter(
        self._CONTAINER_TYPE_EVENT, column_names=column_names,
        filter_expression=filter_expression, order_by=filter_column_name)

  def HasAttributeContainers(self, container_type):
    """Determines if store contains a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.

    Returns:
      bool: True if the store contains the specified type of attribute
          containers.

    Raises:
      IOError: when there is an error querying the storage file.
      OSError: when there is an error querying the storage file.
    """
    count = self.GetNumberOfAttributeContainers(container_type)
    return count > 0

  # pylint: disable=arguments-differ
  def Open(self, path=None, read_only=True, **unused_kwargs):
    """Opens the store.

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

    try:
      path_uri = pathlib.Path(path).as_uri()
      if read_only:
        path_uri = '{0:s}?mode=ro'.format(path_uri)

    except ValueError:
      path_uri = None

    detect_types = sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES

    if path_uri:
      connection = sqlite3.connect(
          path_uri, detect_types=detect_types, uri=True)
    else:
      connection = sqlite3.connect(path, detect_types=detect_types)

    try:
      # Use in-memory journaling mode to reduce IO.
      connection.execute('PRAGMA journal_mode=MEMORY')

      # Turn off insert transaction integrity since we want to do bulk insert.
      connection.execute('PRAGMA synchronous=OFF')

    except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
      raise IOError('Unable to query storage file with error: {0!s}'.format(
          exception))

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
      if not self._HasTable('metadata'):
        self._WriteMetadata()
      else:
        self._ReadAndCheckStorageMetadata()

        # Update the storage metadata format version in case we are adding
        # new format features that are not backwards compatible.
        self._UpdateStorageMetadataFormatVersion()

      for container_type in self._containers_manager.GetContainerTypes():
        if container_type in self._NO_CREATE_TABLE_CONTAINER_TYPES:
          continue

        if not self._HasTable(container_type):
          self._CreateAttributeContainerTable(container_type)

      self._connection.commit()

    # Initialize next_sequence_number based on the file contents so that
    # SQLTableIdentifier points to the correct attribute container.
    for container_type in self._REFERENCED_CONTAINER_TYPES:
      next_sequence_number = self.GetNumberOfAttributeContainers(
          container_type)
      self._SetAttributeContainerNextSequenceNumber(
          container_type, next_sequence_number)
