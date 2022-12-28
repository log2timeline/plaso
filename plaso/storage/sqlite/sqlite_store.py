# -*- coding: utf-8 -*-
"""SQLite-based attribute container store."""

import ast
import collections
import itertools
import os
import pathlib
import sqlite3

from plaso.containers import interface as containers_interface
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

    return operand.join([
        PythonAST2SQL(ast_node_value) for ast_node_value in ast_node.values])

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


class SQLiteAttributeContainerStore(interface.BaseStore):
  """SQLite-based attribute container store.

  Attributes:
    format_version (int): storage format version.
    serialization_format (str): serialization format.
  """

  # pylint: disable=abstract-method

  _FORMAT_VERSION = 20221023

  # The earliest format version, stored in-file, that this class
  # is able to append (write).
  _APPEND_COMPATIBLE_FORMAT_VERSION = 20221023

  # The earliest format version, stored in-file, that this class
  # is able to upgrade (write new format features).
  _UPGRADE_COMPATIBLE_FORMAT_VERSION = 20221023

  # The earliest format version, stored in-file, that this class
  # is able to read.
  _READ_COMPATIBLE_FORMAT_VERSION = 20221023

  _CONTAINER_SCHEMA_TO_SQLITE_TYPE_MAPPINGS = {
      'AttributeContainerIdentifier': 'TEXT',
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

  _MAXIMUM_WRITE_CACHE_SIZE = 50

  def __init__(self):
    """Initializes a SQLite attribute container store."""
    super(SQLiteAttributeContainerStore, self).__init__()
    self._attribute_container_cache = collections.OrderedDict()
    self._connection = None
    self._cursor = None
    self._is_open = False
    self._read_only = True
    self._write_cache = {}

    self.format_version = self._FORMAT_VERSION

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
    format_version = metadata_values.get('format_version', None)

    if not format_version:
      raise IOError('Missing format version.')

    try:
      format_version = int(format_version, 10)
    except (TypeError, ValueError):
      raise IOError('Invalid format version: {0!s}.'.format(format_version))

    if (not check_readable_only and
        format_version < self._APPEND_COMPATIBLE_FORMAT_VERSION):
      raise IOError((
          'Format version: {0:d} is too old and can no longer be '
          'written.').format(format_version))

    if format_version < self._READ_COMPATIBLE_FORMAT_VERSION:
      raise IOError(
          'Format version: {0:d} is too old and can no longer be read.'.format(
              format_version))

    if format_version > self._FORMAT_VERSION:
      raise IOError(
          'Format version: {0:d} is too new and not yet supported.'.format(
              format_version))

    metadata_values['format_version'] = format_version

  def _CreateAttributeContainerTable(self, container_type):
    """Creates a table for a specific attribute container type.

    Args:
      container_type (str): attribute container type.

    Raises:
      IOError: when there is an error querying the attribute container store
          or if an unsupported attribute container is provided.
      OSError: when there is an error querying the attribute container store
          or if an unsupported attribute container is provided.
    """
    schema = self._GetAttributeContainerSchema(container_type)
    if not schema:
      raise IOError('Unsupported attribute container type: {0:s}'.format(
          container_type))

    column_definitions = ['_identifier INTEGER PRIMARY KEY AUTOINCREMENT']

    schema_to_sqlite_type_mappings = (
          self._CONTAINER_SCHEMA_TO_SQLITE_TYPE_MAPPINGS)
    for name, data_type in sorted(schema.items()):
      data_type = schema_to_sqlite_type_mappings.get(data_type, 'TEXT')
      column_definitions.append('{0:s} {1:s}'.format(name, data_type))

    column_definitions = ', '.join(column_definitions)
    query = 'CREATE TABLE {0:s} ({1:s});'.format(
        container_type, column_definitions)

    try:
      self._cursor.execute(query)
    except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
      raise IOError(
          'Unable to query attribute container store with error: {0!s}'.format(
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

    Raises:
      IOError: when there is an error querying the attribute container store
          or if an unsupported attribute container is provided.
      OSError: when there is an error querying the attribute container store
          or if an unsupported attribute container is provided.
    """
    schema = self._GetAttributeContainerSchema(container_type)
    if not schema:
      raise IOError('Unsupported attribute container type: {0:s}'.format(
          container_type))

    container = self._containers_manager.CreateAttributeContainer(
        container_type)

    for column_index, name in enumerate(column_names):
      attribute_value = row[first_column_index + column_index]
      if attribute_value is None:
        continue

      data_type = schema[name]
      if data_type == 'AttributeContainerIdentifier':
        identifier = containers_interface.AttributeContainerIdentifier()
        identifier.CopyFromString(attribute_value)
        attribute_value = identifier

      elif data_type == 'bool':
        attribute_value = bool(attribute_value)

      elif data_type not in self._CONTAINER_SCHEMA_TO_SQLITE_TYPE_MAPPINGS:
        raise IOError((
            'Unsupported attribute container type: {0:s} attribute: {1:s} '
            'data type: {2:s}').format(container_type, name, data_type))

      setattr(container, name, attribute_value)

    return container

  def _Flush(self):
    """Ensures cached data is written to file.

    Raises:
      IOError: when there is an error querying the attribute container store.
      OSError: when there is an error querying the attribute container store.
    """
    for container_type, write_cache in self._write_cache.items():
      if len(write_cache) > 1:
        self._FlushWriteCache(container_type, write_cache)

    self._write_cache = {}

    # We need to run commit or not all data is stored in the database.
    self._connection.commit()

  def _FlushWriteCache(self, container_type, write_cache):
    """Flushes attribute container values cached for writing.

    Args:
      container_type (str): attribute container type.
      write_cache (list[tuple[str]]): cached attribute container values.

    Raises:
      IOError: when there is an error querying the attribute container store.
      OSError: when there is an error querying the attribute container store.
    """
    column_names = write_cache.pop(0)

    value_statement = '({0:s})'.format(','.join(['?'] * len(column_names)))
    values_statement = ', '.join([value_statement] * len(write_cache))

    query = 'INSERT INTO {0:s} ({1:s}) VALUES {2:s}'.format(
        container_type, ', '.join(column_names), values_statement)

    if self._storage_profiler:
      self._storage_profiler.StartTiming('write_new')

    try:
      values = list(itertools.chain(*write_cache))
      self._cursor.execute(query, values)

    except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
      raise IOError(
          'Unable to query attribute container store with error: {0!s}'.format(
              exception))

    finally:
      if self._storage_profiler:
        self._storage_profiler.StopTiming('write_new')

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
      IOError: when there is an error querying the attribute container store.
      OSError: when there is an error querying the attribute container store.
    """
    write_cache = self._write_cache.get(container_type, [])
    if len(write_cache) > 1:
      self._FlushWriteCache(container_type, write_cache)
      del self._write_cache[container_type]

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
          'Unable to query attribute container store for container: {0:s} with '
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

      identifier = containers_interface.AttributeContainerIdentifier(
          name=container_type, sequence_number=row[0])
      container.SetIdentifier(identifier)

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
      IOError: when there is an error querying the attribute container store.
      OSError: when there is an error querying the attribute container store.
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
      IOError: when there is an error querying the attribute container store.
      OSError: when there is an error querying the attribute container store.
    """
    query = self._HAS_TABLE_QUERY.format(table_name)

    try:
      self._cursor.execute(query)
    except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
      raise IOError(
          'Unable to query attribute container store with error: {0!s}'.format(
              exception))

    return bool(self._cursor.fetchone())

  def _RaiseIfNotReadable(self):
    """Raises if the attribute container store is not readable.

     Raises:
      IOError: when the attribute container store is closed.
      OSError: when the attribute container store is closed.
    """
    if not self._is_open:
      raise IOError('Unable to read from closed attribute container store.')

  def _RaiseIfNotWritable(self):
    """Raises if the attribute container store is not writable.

    Raises:
      IOError: when the attribute container store is closed or read-only.
      OSError: when the attribute container store is closed or read-only.
    """
    if not self._is_open:
      raise IOError('Unable to write to closed attribute container store.')

    if self._read_only:
      raise IOError('Unable to write to read-only attribute container store.')

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

  def _ReadMetadata(self):
    """Reads metadata.

    Returns:
      dict[str, str]: metadata values.

    Raises:
      IOError: when there is an error querying the attribute container store.
      OSError: when there is an error querying the attribute container store.
    """
    query = 'SELECT key, value FROM metadata'

    try:
      self._cursor.execute(query)
    except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
      raise IOError(
          'Unable to query attribute container store with error: {0!s}'.format(
              exception))

    return {row[0]: row[1] for row in self._cursor.fetchall()}

  def _UpdateStorageMetadataFormatVersion(self):
    """Updates the storage metadata format version.

    Raises:
      IOError: when there is an error querying the attribute container store.
      OSError: when there is an error querying the attribute container store.
    """
    if self.format_version >= self._UPGRADE_COMPATIBLE_FORMAT_VERSION:
      query = (
          'UPDATE metadata SET value = {0:d} '
          'WHERE key = "format_version"').format(self._FORMAT_VERSION)

      try:
        self._cursor.execute(query)
      except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
        raise IOError((
            'Unable to query attribute container store with error: '
            '{0!s}').format(exception))

  def _WriteExistingAttributeContainer(self, container):
    """Writes an existing attribute container to the store.

    Args:
      container (AttributeContainer): attribute container.

    Raises:
      IOError: when there is an error querying the attribute container store
          or if an unsupported attribute container is provided.
      OSError: when there is an error querying the attribute container store
          or if an unsupported attribute container is provided.
    """
    identifier = container.GetIdentifier()

    schema = self._GetAttributeContainerSchema(container.CONTAINER_TYPE)
    if not schema:
      raise IOError('Unsupported attribute container type: {0:s}'.format(
          container.CONTAINER_TYPE))

    write_cache = self._write_cache.get(container.CONTAINER_TYPE, [])
    if len(write_cache) > 1:
      self._FlushWriteCache(container.CONTAINER_TYPE, write_cache)
      del self._write_cache[container.CONTAINER_TYPE]

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
          raise IOError((
              'Unsupported attribute container type: {0:s} attribute: {1:s} '
              'data type: {2:s}').format(
                  container.CONTAINER_TYPE, name, data_type))

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
      raise IOError(
          'Unable to query attribute container store with error: {0!s}'.format(
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

  def _WriteMetadataValue(self, key, value):
    """Writes a metadata value.

    Args:
      key (str): key of the storage metadata.
      value (str): value of the storage metadata.

    Raises:
      IOError: when there is an error querying the attribute container store.
      OSError: when there is an error querying the attribute container store.
    """
    try:
      self._cursor.execute(self._INSERT_METADATA_VALUE_QUERY, (key, value))
    except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
      raise IOError(
          'Unable to query attribute container store with error: {0!s}'.format(
              exception))

  def _WriteNewAttributeContainer(self, container):
    """Writes a new attribute container to the store.

    The table for the container type must exist.

    Args:
      container (AttributeContainer): attribute container.

    Raises:
      IOError: when there is an error querying the attribute container store
          or if an unsupported attribute container is provided.
      OSError: when there is an error querying the attribute container store
          or if an unsupported attribute container is provided.
    """
    next_sequence_number = self._GetAttributeContainerNextSequenceNumber(
        container.CONTAINER_TYPE)

    identifier = containers_interface.AttributeContainerIdentifier(
        name=container.CONTAINER_TYPE, sequence_number=next_sequence_number)
    container.SetIdentifier(identifier)

    schema = self._GetAttributeContainerSchema(container.CONTAINER_TYPE)
    if not schema:
      raise IOError('Unsupported attribute container type: {0:s}'.format(
          container.CONTAINER_TYPE))

    column_names = []
    values = []
    for name, data_type in sorted(schema.items()):
      attribute_value = getattr(container, name, None)
      if attribute_value is not None:
        if data_type == 'AttributeContainerIdentifier' and isinstance(
            attribute_value,
            containers_interface.AttributeContainerIdentifier):
          attribute_value = attribute_value.CopyToString()

        elif data_type == 'bool':
          attribute_value = int(attribute_value)

        elif data_type not in self._CONTAINER_SCHEMA_TO_SQLITE_TYPE_MAPPINGS:
          raise IOError((
              'Unsupported attribute container type: {0:s} attribute: {1:s} '
              'data type: {2:s}').format(
                  container.CONTAINER_TYPE, name, data_type))

      column_names.append(name)
      values.append(attribute_value)

    write_cache = self._write_cache.get(
        container.CONTAINER_TYPE, [column_names])
    write_cache.append(values)

    if len(write_cache) >= self._MAXIMUM_WRITE_CACHE_SIZE:
      self._FlushWriteCache(container.CONTAINER_TYPE, write_cache)
      write_cache = [column_names]

    self._write_cache[container.CONTAINER_TYPE] = write_cache

    self._CacheAttributeContainerByIndex(container, next_sequence_number - 1)

  @classmethod
  def CheckSupportedFormat(cls, path):
    """Checks if the attribute container store format is supported.

    Args:
      path (str): path to the attribute container store.

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
      IOError: if the attribute container store is already closed.
      OSError: if the attribute container store is already closed.
    """
    if not self._is_open:
      raise IOError('Storage file already closed.')

    if self._connection:
      self._Flush()

      self._connection.close()

      self._connection = None
      self._cursor = None

    self._is_open = False

  def GetAttributeContainerByIdentifier(self, container_type, identifier):
    """Retrieves a specific type of container with a specific identifier.

    Args:
      container_type (str): container type.
      identifier (AttributeContainerIdentifier): attribute container identifier.

    Returns:
      AttributeContainer: attribute container or None if not available.

    Raises:
      IOError: when the store is closed or if an unsupported attribute
          container is provided.
      OSError: when the store is closed or if an unsupported attribute
          container is provided.
    """
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
      IOError: when there is an error querying the attribute container store
          or if an unsupported attribute container is provided.
      OSError: when there is an error querying the attribute container store
          or if an unsupported attribute container is provided.
    """
    container = self._GetCachedAttributeContainer(container_type, index)
    if container:
      return container

    write_cache = self._write_cache.get(container_type, [])
    if len(write_cache) > 1:
      self._FlushWriteCache(container_type, write_cache)
      del self._write_cache[container_type]

    schema = self._GetAttributeContainerSchema(container_type)
    if not schema:
      raise IOError('Unsupported attribute container type: {0:s}'.format(
          container.CONTAINER_TYPE))

    column_names = sorted(schema.keys())

    row_number = index + 1
    query = 'SELECT {0:s} FROM {1:s} WHERE rowid = {2:d}'.format(
        ', '.join(column_names), container_type, row_number)

    try:
      self._cursor.execute(query)
    except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
      raise IOError(
          'Unable to query attribute container store with error: {0!s}'.format(
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
      IOError: when there is an error querying the attribute container store
          or if an unsupported attribute container is provided.
      OSError: when there is an error querying the attribute container store
          or if an unsupported attribute container is provided.
    """
    schema = self._GetAttributeContainerSchema(container_type)
    if not schema:
      raise IOError('Unsupported attribute container type: {0:s}'.format(
          container_type))

    column_names = sorted(schema.keys())

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
      IOError: when there is an error querying the attribute container store.
      OSError: when there is an error querying the attribute container store.
    """
    if not self._HasTable(container_type):
      return 0

    write_cache = self._write_cache.get(container_type, [])
    if len(write_cache) > 1:
      self._FlushWriteCache(container_type, write_cache)
      del self._write_cache[container_type]

    # Note that this is SQLite specific, and will give inaccurate results if
    # there are DELETE commands run on the table. The Plaso SQLite storage
    # implementation does not run any DELETE commands.
    query = 'SELECT MAX(_ROWID_) FROM {0:s} LIMIT 1'.format(container_type)

    try:
      self._cursor.execute(query)
    except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
      raise IOError(
          'Unable to query attribute container store with error: {0!s}'.format(
              exception))

    row = self._cursor.fetchone()
    if not row:
      return 0

    return row[0] or 0

  def HasAttributeContainers(self, container_type):
    """Determines if store contains a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.

    Returns:
      bool: True if the store contains the specified type of attribute
          containers.

    Raises:
      IOError: when there is an error querying the attribute container store.
      OSError: when there is an error querying the attribute container store.
    """
    count = self.GetNumberOfAttributeContainers(container_type)
    return count > 0

  def Open(self, path=None, read_only=True, **unused_kwargs):  # pylint: disable=arguments-differ
    """Opens the store.

    Args:
      path (Optional[str]): path to the attribute container store.
      read_only (Optional[bool]): True if the file should be opened in
          read-only mode.

    Raises:
      IOError: if the attribute container store is already opened or if
          the database cannot be connected.
      OSError: if the attribute container store is already opened or if
          the database cannot be connected.
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
          path_uri, detect_types=detect_types, isolation_level='DEFERRED',
          uri=True)
    else:
      connection = sqlite3.connect(
          path, detect_types=detect_types, isolation_level='DEFERRED')

    try:
      # Use in-memory journaling mode to reduce IO.
      connection.execute('PRAGMA journal_mode=MEMORY')

      # Turn off insert transaction integrity since we want to do bulk insert.
      connection.execute('PRAGMA synchronous=OFF')

    except (sqlite3.InterfaceError, sqlite3.OperationalError) as exception:
      raise IOError(
          'Unable to query attribute container store with error: {0!s}'.format(
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

      # TODO: create table on demand.
      for container_type in self._containers_manager.GetContainerTypes():
        if not self._HasTable(container_type):
          self._CreateAttributeContainerTable(container_type)

      self._connection.commit()
