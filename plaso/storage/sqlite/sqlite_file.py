# -*- coding: utf-8 -*-
"""SQLite-based storage file."""

import collections
import os
import pathlib
import sqlite3
import zlib

from plaso.containers import manager as containers_manager
from plaso.lib import definitions
from plaso.storage import file_interface
from plaso.storage import identifiers
from plaso.storage import logger


class SQLiteStorageFile(file_interface.BaseStorageFile):
  """SQLite-based storage file.

  Attributes:
    compression_format (str): compression format.
    format_version (int): storage format version.
    serialization_format (str): serialization format.
    storage_type (str): storage type.
  """

  _FORMAT_VERSION = 20210621

  # The earliest format version with a schema.
  _WITH_SCHEMA_FORMAT_VERSION = 20210621

  # The earliest format version, stored in-file, that this class
  # is able to append (write).
  _APPEND_COMPATIBLE_FORMAT_VERSION = 20190309

  # The earliest format version, stored in-file, that this class
  # is able to upgrade (write new format features).
  _UPGRADE_COMPATIBLE_FORMAT_VERSION = 20210621

  # The earliest format version, stored in-file, that this class
  # is able to read.
  _READ_COMPATIBLE_FORMAT_VERSION = 20190309

  # Container types that are referenced from other container types.
  _REFERENCED_CONTAINER_TYPES = (
      file_interface.BaseStorageFile._CONTAINER_TYPE_EVENT,
      file_interface.BaseStorageFile._CONTAINER_TYPE_EVENT_DATA,
      file_interface.BaseStorageFile._CONTAINER_TYPE_EVENT_DATA_STREAM,
      file_interface.BaseStorageFile._CONTAINER_TYPE_EVENT_SOURCE)

  _CONTAINERS_MANAGER = containers_manager.AttributeContainersManager

  _CONTAINER_SCHEMA_VERSION = 20210621

  # TODO: add support for analysis_report, event_data, session_completion,
  # session_configuration, session_start, system_configuration
  _CONTAINER_SCHEMAS = {
      'analysis_warning': {
          'message': 'str',
          'plugin_name': 'str'},

      'event': {
          '_event_data_row_identifier': 'AttributeContainerIdentifier',
          'date_time': 'dfdatetime.DateTimeValues',
          'timestamp': 'int',
          'timestamp_desc': 'str'},

      'event_data_stream': {
          'file_entropy': 'str',
          'md5_hash': 'str',
          'path_spec': 'dfvfs.PathSpec',
          'sha1_hash': 'str',
          'sha256_hash': 'str',
          'yara_match': 'str'},

      'event_source': {
          'data_type': 'str',
          'file_entry_type': 'str',
          'path_spec': 'dfvfs.PathSpec'},

      'event_tag': {
          '_event_row_identifier': 'AttributeContainerIdentifier',
          'labels': 'List[str]'},

      'extraction_warning': {
          'message': 'str',
          'parser_chain': 'str',
          'path_spec': 'dfvfs.PathSpec'},

      'preprocessing_warning': {
          'message': 'str',
          'path_spec': 'dfvfs.PathSpec',
          'plugin_name': 'str'},

      'recovery_warning': {
          'message': 'str',
          'parser_chain': 'str',
          'path_spec': 'dfvfs.PathSpec'},
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

  def __init__(self, storage_type=definitions.STORAGE_TYPE_SESSION):
    """Initializes a store.

    Args:
      storage_type (Optional[str]): storage type.
    """
    if storage_type == definitions.STORAGE_TYPE_SESSION:
      compression_format = definitions.COMPRESSION_FORMAT_ZLIB
    else:
      compression_format = definitions.COMPRESSION_FORMAT_NONE

    super(SQLiteStorageFile, self).__init__()
    self._attribute_container_cache = collections.OrderedDict()
    self._connection = None
    self._cursor = None
    self._use_schema = bool(storage_type == definitions.STORAGE_TYPE_SESSION)

    self.compression_format = compression_format
    self.format_version = self._FORMAT_VERSION
    self.serialization_format = definitions.SERIALIZER_FORMAT_JSON
    self.storage_type = storage_type

  def _CacheAttributeContainerByIndex(self, attribute_container, index):
    """Caches a specific attribute container.

    Args:
      attribute_container (AttributeContainer): attribute container.
      index (int): attribute container index.
    """
    # Do not cache event tags since this causes GetEventTagByIdentifier to fail.
    if (self.format_version < self._WITH_SCHEMA_FORMAT_VERSION and
        attribute_container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_TAG):
      return

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

    storage_type = metadata_values.get('storage_type', None)
    if storage_type not in definitions.STORAGE_TYPES:
      raise IOError('Unsupported storage type: {0!s}'.format(
          storage_type))

  def _CreateAttributeContainerTable(self, container_type):
    """Creates a table for a specific attribute container type.

    Args:
      container_type (str): attribute container type.

    Raises:
      IOError: when there is an error querying the storage file.
      OSError: when there is an error querying the storage file.
    """
    schema = self._CONTAINER_SCHEMAS.get(container_type, {})

    if self._use_schema and schema:
      data_types = {
          name: self._CONTAINER_SCHEMA_TO_SQLITE_TYPE_MAPPINGS.get(
              attribute_type, 'TEXT')
          for name, attribute_type in schema.items()}

      column_definitions = ', '.join([
          '{0:s} {1:s}'.format(name, data_type)
          for name, data_type in sorted(data_types.items())])

    else:
      if self.compression_format == definitions.COMPRESSION_FORMAT_ZLIB:
        data_column_type = 'BLOB'
      else:
        data_column_type = 'TEXT'

      if container_type == self._CONTAINER_TYPE_EVENT:
        column_definitions = (
            '_timestamp BIGINT, '
            '_data {0:s}').format(data_column_type)

      else:
        column_definitions = '_data {0:s}'.format(data_column_type)

    query = (
        'CREATE TABLE {0:s} ('
        '_identifier INTEGER PRIMARY KEY AUTOINCREMENT, '
        '{1:s});').format(container_type, column_definitions)

    try:
      self._cursor.execute(query)
    except sqlite3.OperationalError as exception:
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
    schema = self._CONTAINER_SCHEMAS.get(container_type, {})

    if column_names != ['_data']:
      container = self._CONTAINERS_MANAGER.CreateAttributeContainer(
          container_type)

      for column_index, column_name in enumerate(column_names):
        attribute_type = schema[column_name]
        attribute_value = row[first_column_index + column_index]

        if attribute_value is not None:
          if attribute_type == 'bool':
            attribute_value = bool(attribute_value)

          # TODO: add compression support
          elif attribute_type not in (
              self._CONTAINER_SCHEMA_TO_SQLITE_TYPE_MAPPINGS):
            attribute_value = self._serializer.ReadSerialized(attribute_value)

        setattr(container, column_name, attribute_value)

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
    schema = self._CONTAINER_SCHEMAS.get(container_type, {})

    if self._use_schema and schema:
      column_names = sorted(schema.keys())
    else:
      column_names = ['_data']

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
    except sqlite3.OperationalError as exception:
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
    except sqlite3.OperationalError as exception:
      raise IOError('Unable to query storage file with error: {0!s}'.format(
          exception))

    return bool(self._cursor.fetchone())

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
    except sqlite3.OperationalError as exception:
      raise IOError('Unable to query storage file with error: {0!s}'.format(
          exception))

    metadata_values = {row[0]: row[1] for row in self._cursor.fetchall()}

    self._CheckStorageMetadata(
        metadata_values, check_readable_only=check_readable_only)

    self.format_version = metadata_values['format_version']
    self.compression_format = metadata_values['compression_format']
    self.serialization_format = metadata_values['serialization_format']
    self.storage_type = metadata_values['storage_type']

    self._use_schema = bool(
        self.storage_type == definitions.STORAGE_TYPE_SESSION and
        self.format_version >= self._WITH_SCHEMA_FORMAT_VERSION)

  def _UpdateAttributeContainerAfterDeserialize(self, container):
    """Updates an attribute container after deserialization.

    Args:
      container (AttributeContainer): attribute container.
    """
    if container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT:
      self._UpdateEventAfterDeserialize(container)

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_DATA:
      self._UpdateEventDataAfterDeserialize(container)

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_TAG:
      self._UpdateEventTagAfterDeserialize(container)

  def _UpdateAttributeContainerBeforeSerialize(self, container):
    """Updates an attribute container before serialization.

    Args:
      container (AttributeContainer): attribute container.
    """
    if container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT:
      self._UpdateEventBeforeSerialize(container)

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_DATA:
      self._UpdateEventDataBeforeSerialize(container)

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_TAG:
      self._UpdateEventTagBeforeSerialize(container)

  def _UpdateEventAfterDeserialize(self, event):
    """Updates an event after deserialization.

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

  def _UpdateEventBeforeSerialize(self, event):
    """Updates an event before serialization.

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

  def _UpdateEventDataAfterDeserialize(self, event_data):
    """Updates event data after deserialization.

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

  def _UpdateEventDataBeforeSerialize(self, event_data):
    """Updates event data before serialization.

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

  def _UpdateEventTagAfterDeserialize(self, event_tag):
    """Updates an event tag after deserialization.

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

  def _UpdateEventTagBeforeSerialize(self, event_tag):
    """Updates an event tag before serialization.

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
      except sqlite3.OperationalError as exception:
        raise IOError('Unable to query storage file with error: {0!s}'.format(
            exception))

  def _WriteExistingAttributeContainer(self, container):
    """Writes an existing attribute container to the store.

    Args:
      container (AttributeContainer): attribute container.

    Raises:
      IOError: when there is an error querying the storage file.
      OSError: when there is an error querying the storage file.
    """
    self._UpdateAttributeContainerBeforeSerialize(container)

    schema = self._CONTAINER_SCHEMAS.get(container.CONTAINER_TYPE, {})

    column_names = []
    values = []
    for name, attribute_type in sorted(schema.items()):
      attribute_value = getattr(container, name, None)

      if attribute_value is not None:
        if attribute_type == 'bool':
          attribute_value = int(attribute_value)

        # TODO: add compression support
        elif attribute_type not in (
            self._CONTAINER_SCHEMA_TO_SQLITE_TYPE_MAPPINGS):
          attribute_value = self._serializer.WriteSerialized(attribute_value)

      column_names.append('{0:s} = ?'.format(name))
      values.append(attribute_value)

    identifier = container.GetIdentifier()

    query = 'UPDATE {0:s} SET {1:s} WHERE _identifier = {2:d}'.format(
        container.CONTAINER_TYPE, ', '.join(column_names),
        identifier.row_identifier)

    if self._storage_profiler:
      self._storage_profiler.StartTiming('write_existing')

    try:
      self._cursor.execute(query, values)

    except sqlite3.OperationalError as exception:
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
    except sqlite3.OperationalError as exception:
      raise IOError('Unable to query storage file with error: {0!s}'.format(
          exception))

    self._WriteMetadataValue(
        'format_version', '{0:d}'.format(self._FORMAT_VERSION))
    self._WriteMetadataValue('compression_format', self.compression_format)
    self._WriteMetadataValue('serialization_format', self.serialization_format)
    self._WriteMetadataValue('storage_type', self.storage_type)

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
    except sqlite3.OperationalError as exception:
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

    self._UpdateAttributeContainerBeforeSerialize(container)

    schema = self._CONTAINER_SCHEMAS.get(container.CONTAINER_TYPE, {})

    if self._use_schema and schema:
      column_names = []
      values = []
      for name, attribute_type in sorted(schema.items()):
        attribute_value = getattr(container, name, None)

        if attribute_value is not None:
          if attribute_type == 'bool':
            attribute_value = int(attribute_value)

          # TODO: add compression support
          elif attribute_type not in (
              self._CONTAINER_SCHEMA_TO_SQLITE_TYPE_MAPPINGS):
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

    except sqlite3.OperationalError as exception:
      raise IOError('Unable to query storage file with error: {0!s}'.format(
          exception))

    finally:
      if self._storage_profiler:
        self._storage_profiler.StopTiming('write_new')

    if (self.storage_type == definitions.STORAGE_TYPE_SESSION and
        container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_SOURCE):
      # Cache the event source for a session store since it will be accessed
      # after write.
      self._CacheAttributeContainerByIndex(container, next_sequence_number - 1)

  # TODO: refactor
  def AddEventTag(self, event_tag):
    """Adds an event tag.

    Args:
      event_tag (EventTag): event tag.

    Raises:
      IOError: when the storage file is closed or read-only or when there is
          an error querying the storage file.
      OSError: when the storage file is closed or read-only or when there is
          an error querying the storage file.
    """
    self._RaiseIfNotWritable()

    event_identifier = event_tag.GetEventIdentifier()
    existing_event_tag = self.GetEventTagByEventIdentifier(event_identifier)

    if existing_event_tag:
      existing_event_tag.AddLabels(event_tag.labels)
      self._WriteExistingAttributeContainer(existing_event_tag)

    else:
      self._WriteNewAttributeContainer(event_tag)

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
      raise IOError('Unsupported event data identifier type: {0!s}'.format(
          type(identifier)))

    return self.GetAttributeContainerByIndex(
        container_type, identifier.row_identifier - 1)

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

    schema = self._CONTAINER_SCHEMAS.get(container_type, {})

    if self._use_schema and schema:
      column_names = sorted(schema.keys())
    else:
      column_names = ['_data']

    sequence_number = index + 1
    query = 'SELECT {0:s} FROM {1:s} WHERE rowid = {2:d}'.format(
        ', '.join(column_names), container_type, sequence_number)

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

    if not row:
      return None

    container = self._CreatetAttributeContainerFromRow(
        container_type, column_names, row, 0)

    identifier = identifiers.SQLTableIdentifier(
        container_type, sequence_number)
    container.SetIdentifier(identifier)

    self._UpdateAttributeContainerAfterDeserialize(container)

    self._CacheAttributeContainerByIndex(container, index)
    return container

  def GetAttributeContainers(self, container_type):
    """Retrieves a specific type of stored attribute containers.

    Args:
      container_type (str): attribute container type.

    Returns:
      generator(AttributeContainer): attribute container generator.

    Raises:
      IOError: when there is an error querying the storage file.
      OSError: when there is an error querying the storage file.
    """
    return self._GetAttributeContainersWithFilter(container_type)

  def GetEventTagByEventIdentifier(self, event_identifier):
    """Retrieves the event tag related to a specific event identifier.

    Args:
      event_identifier (SQLTableIdentifier): event.

    Returns:
      EventTag: event tag or None if not available.

    Raises:
      IOError: when the store is closed or when there is an error querying
          the storage file.
      OSError: when the store is closed or when there is an error querying
          the storage file.
    """
    schema = self._CONTAINER_SCHEMAS.get(self._CONTAINER_TYPE_EVENT_TAG, {})
    if self._use_schema and schema:
      return None

    filter_expression = '_event_row_identifier = {0:d}'.format(
        event_identifier.row_identifier)

    generator = self._GetAttributeContainersWithFilter(
        self._CONTAINER_TYPE_EVENT_TAG, filter_expression=filter_expression)
    existing_event_tags = list(generator)

    if len(existing_event_tags) != 1:
      return None

    return existing_event_tags[0]

  def GetNumberOfAttributeContainers(self, container_type):
    """Retrieves the number of a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.

    Returns:
      int: the number of containers of a specified type.

    Raises:
      IOError: when there is an error querying the storage file.
      OSError: when there is an error querying the storage file.
      ValueError: if an unsupported container type is provided.
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

    try:
      self._cursor.execute(query)
    except sqlite3.OperationalError as exception:
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
    schema = self._CONTAINER_SCHEMAS.get(self._CONTAINER_TYPE_EVENT, {})
    if self._use_schema and schema:
      column_name = 'timestamp'
    else:
      column_name = '_timestamp'

    filter_expression = None
    if time_range:
      filter_expression = []

      if time_range.start_timestamp:
        filter_expression.append(
            '{0:s} >= {1:d}'.format(column_name, time_range.start_timestamp))

      if time_range.end_timestamp:
        filter_expression.append(
            '{0:s} <= {1:d}'.format(column_name, time_range.end_timestamp))

      filter_expression = ' AND '.join(filter_expression)

    return self._GetAttributeContainersWithFilter(
        self._CONTAINER_TYPE_EVENT, filter_expression=filter_expression,
        order_by=column_name)

  def HasAttributeContainers(self, container_type):
    """Determines if store contains a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.

    Returns:
      bool: True if the store contains the specified type of attribute
          containers.
    """
    count = self.GetNumberOfAttributeContainers(container_type)
    return count > 0

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

      try:
        # Turn off insert transaction integrity since we want to do bulk insert.
        self._cursor.execute('PRAGMA synchronous=OFF')
      except sqlite3.OperationalError as exception:
        raise IOError('Unable to query storage file with error: {0!s}'.format(
            exception))

      if not self._HasTable('metadata'):
        self._WriteMetadata()
      else:
        self._ReadAndCheckStorageMetadata()

        # Update the storage metadata format version in case we are adding
        # new format features that are not backwards compatible.
        self._UpdateStorageMetadataFormatVersion()

      container_types = set(self._CONTAINER_TYPES)
      if self._use_schema:
        container_types.update(self._CONTAINER_SCHEMAS.keys())

      for container_type in container_types:
        if (self.storage_type == definitions.STORAGE_TYPE_SESSION and
            container_type in self._TASK_STORE_ONLY_CONTAINER_TYPES):
          continue

        if (self.storage_type == definitions.STORAGE_TYPE_TASK and
            container_type in self._SESSION_STORE_ONLY_CONTAINER_TYPES):
          continue

        if not self._HasTable(container_type):
          self._CreateAttributeContainerTable(container_type)

      self._connection.commit()

    last_session_start = self.GetNumberOfAttributeContainers(
        self._CONTAINER_TYPE_SESSION_START)

    last_session_completion = self.GetNumberOfAttributeContainers(
        self._CONTAINER_TYPE_SESSION_COMPLETION)

    # Initialize next_sequence_number based on the file contents so that
    # SQLTableIdentifier points to the correct attribute container.
    for container_type in self._REFERENCED_CONTAINER_TYPES:
      next_sequence_number = self.GetNumberOfAttributeContainers(
          container_type)
      self._SetAttributeContainerNextSequenceNumber(
          container_type, next_sequence_number)

    # TODO: handle open sessions.
    if last_session_start != last_session_completion:
      logger.warning('Detected unclosed session.')

    self._last_session = last_session_completion
