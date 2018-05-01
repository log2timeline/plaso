# -*- coding: utf-8 -*-
"""SQLite-based storage."""

from __future__ import unicode_literals

import os
import sqlite3
import zlib

from plaso.containers import artifacts
from plaso.containers import errors
from plaso.containers import event_sources
from plaso.containers import events
from plaso.containers import reports
from plaso.containers import sessions
from plaso.containers import tasks
from plaso.lib import definitions
from plaso.storage import event_heaps
from plaso.storage import identifiers
from plaso.storage import interface
from plaso.storage import logger


class SQLiteStorageFile(interface.BaseStorageFile):
  """SQLite-based storage file.

  Attributes:
    format_version (int): storage format version.
    serialization_format (str): serialization format.
    storage_type (str): storage type.
  """

  _FORMAT_VERSION = 20180101

  # The earliest format version, stored in-file, that this class
  # is able to read.
  _COMPATIBLE_FORMAT_VERSION = 20170707

  _CONTAINER_TYPE_ANALYSIS_REPORT = reports.AnalysisReport.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT = events.EventObject.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_DATA = events.EventData.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_SOURCE = event_sources.EventSource.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_TAG = events.EventTag.CONTAINER_TYPE
  _CONTAINER_TYPE_EXTRACTION_ERROR = errors.ExtractionError.CONTAINER_TYPE
  _CONTAINER_TYPE_SESSION_COMPLETION = sessions.SessionCompletion.CONTAINER_TYPE
  _CONTAINER_TYPE_SESSION_START = sessions.SessionStart.CONTAINER_TYPE
  _CONTAINER_TYPE_SYSTEM_CONFIGURATION = (
      artifacts.SystemConfigurationArtifact.CONTAINER_TYPE)
  _CONTAINER_TYPE_TASK_COMPLETION = tasks.TaskCompletion.CONTAINER_TYPE
  _CONTAINER_TYPE_TASK_START = tasks.TaskStart.CONTAINER_TYPE

  _CONTAINER_TYPES = (
      _CONTAINER_TYPE_ANALYSIS_REPORT,
      _CONTAINER_TYPE_EXTRACTION_ERROR,
      _CONTAINER_TYPE_EVENT,
      _CONTAINER_TYPE_EVENT_DATA,
      _CONTAINER_TYPE_EVENT_SOURCE,
      _CONTAINER_TYPE_EVENT_TAG,
      _CONTAINER_TYPE_SESSION_COMPLETION,
      _CONTAINER_TYPE_SESSION_START,
      _CONTAINER_TYPE_SYSTEM_CONFIGURATION,
      _CONTAINER_TYPE_TASK_COMPLETION,
      _CONTAINER_TYPE_TASK_START)

  # Container types that are referenced from other container types.
  _REFERENCED_CONTAINER_TYPES = (
      _CONTAINER_TYPE_EVENT,
      _CONTAINER_TYPE_EVENT_DATA,
      _CONTAINER_TYPE_EVENT_SOURCE)

  _CREATE_METADATA_TABLE_QUERY = (
      'CREATE TABLE metadata (key TEXT, value TEXT);')

  _CREATE_TABLE_QUERY = (
      'CREATE TABLE {0:s} ('
      '_identifier INTEGER PRIMARY KEY AUTOINCREMENT,'
      '_data {1:s});')

  _CREATE_EVENT_TABLE_QUERY = (
      'CREATE TABLE {0:s} ('
      '_identifier INTEGER PRIMARY KEY AUTOINCREMENT,'
      '_timestamp INTEGER,'
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
    self._last_session = 0
    self._maximum_buffer_size = maximum_buffer_size
    self._serialized_event_heap = event_heaps.SerializedEventHeap()

    if storage_type == definitions.STORAGE_TYPE_SESSION:
      self.compression_format = definitions.COMPRESSION_FORMAT_ZLIB
    else:
      self.compression_format = definitions.COMPRESSION_FORMAT_NONE

    self.format_version = self._FORMAT_VERSION
    self.serialization_format = definitions.SERIALIZER_FORMAT_JSON
    self.storage_type = storage_type

  def _AddAttributeContainer(self, container_type, attribute_container):
    """Adds an attribute container.

    Args:
      container_type (str): attribute container type.
      attribute_container (AttributeContainer): attribute container.

    Raises:
      IOError: if the attribute container cannot be serialized.
    """
    container_list = self._GetSerializedAttributeContainerList(container_type)

    identifier = identifiers.SQLTableIdentifier(
        container_type, container_list.next_sequence_number + 1)
    attribute_container.SetIdentifier(identifier)

    serialized_data = self._SerializeAttributeContainer(attribute_container)

    container_list.PushAttributeContainer(serialized_data)

    if container_list.data_size > self._maximum_buffer_size:
      self._WriteSerializedAttributeContainerList(container_type)

  def _AddSerializedEvent(self, event):
    """Adds an serialized event.

    Args:
      event (EventObject): event.

    Raises:
      IOError: if the event cannot be serialized.
    """
    identifier = identifiers.SQLTableIdentifier(
        self._CONTAINER_TYPE_EVENT,
        self._serialized_event_heap.number_of_events + 1)
    event.SetIdentifier(identifier)

    serialized_data = self._SerializeAttributeContainer(event)

    self._serialized_event_heap.PushEvent(event.timestamp, serialized_data)

    if self._serialized_event_heap.data_size > self._maximum_buffer_size:
      self._WriteSerializedAttributeContainerList(self._CONTAINER_TYPE_EVENT)

  @classmethod
  def _CheckStorageMetadata(cls, metadata_values):
    """Checks the storage metadata.

    Args:
      metadata_values (dict[str, str]): metadata values per key.

    Raises:
      IOError: if the format version or the serializer format is not supported.
    """
    format_version = metadata_values.get('format_version', None)

    if not format_version:
      raise IOError('Missing format version.')

    try:
      format_version = int(format_version, 10)
    except (TypeError, ValueError):
      raise IOError('Invalid format version: {0!s}.'.format(format_version))

    if format_version < cls._COMPATIBLE_FORMAT_VERSION:
      raise IOError(
          'Format version: {0:d} is too old and no longer supported.'.format(
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

  def _GetAttributeContainerByIndex(self, container_type, index):
    """Retrieves a specific attribute container.

    Args:
      container_type (str): attribute container type.
      index (int): attribute container index.

    Returns:
      AttributeContainer: attribute container or None if not available.
    """
    sequence_number = index + 1
    query = 'SELECT _data FROM {0:s} WHERE rowid = {1:d}'.format(
        container_type, sequence_number)
    self._cursor.execute(query)

    row = self._cursor.fetchone()
    if row:
      identifier = identifiers.SQLTableIdentifier(
          container_type, sequence_number)

      if self.compression_format == definitions.COMPRESSION_FORMAT_ZLIB:
        serialized_data = zlib.decompress(row[0])
      else:
        serialized_data = row[0]

      if self._storage_profiler:
        self._storage_profiler.Sample(
            'read', container_type, len(serialized_data), len(row[0]))

      attribute_container = self._DeserializeAttributeContainer(
          container_type, serialized_data)
      attribute_container.SetIdentifier(identifier)
      return attribute_container

    count = self._CountStoredAttributeContainers(container_type)
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

  def _GetAttributeContainers(
      self, container_type, filter_expression=None, order_by=None):
    """Retrieves attribute containers.

    Args:
      container_type (str): attribute container type.
      filter_expression (Optional[str]): expression to filter results by.
      order_by (Optional[str]): name of a column to order the results by.

    Yields:
      AttributeContainer: attribute container.
    """
    query = 'SELECT _identifier, _data FROM {0:s}'.format(container_type)
    if filter_expression:
      query = '{0:s} WHERE {1:s}'.format(query, filter_expression)
    if order_by:
      query = '{0:s} ORDER BY {1:s}'.format(query, order_by)

    # Use a local cursor to prevent another query interrupting the generator.
    cursor = self._connection.cursor()

    cursor.execute(query)

    row = cursor.fetchone()
    while row:
      identifier = identifiers.SQLTableIdentifier(container_type, row[0])

      if self.compression_format == definitions.COMPRESSION_FORMAT_ZLIB:
        serialized_data = zlib.decompress(row[1])
      else:
        serialized_data = row[1]

      if self._storage_profiler:
        self._storage_profiler.Sample(
            'read', container_type, len(serialized_data), len(row[1]))

      attribute_container = self._DeserializeAttributeContainer(
          container_type, serialized_data)
      attribute_container.SetIdentifier(identifier)
      yield attribute_container

      row = cursor.fetchone()

  def _HasAttributeContainers(self, container_type):
    """Determines if a store contains a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.

    Returns:
      bool: True if the store contains the specified type of attribute
          containers.
    """
    count = self._CountStoredAttributeContainers(container_type)
    return count > 0

  def _HasTable(self, table_name):
    """Determines if a specific table exists.

    Args:
      table_name (str): name of the table.

    Returns:
      True if the table exists, false otherwise.
    """
    query = self._HAS_TABLE_QUERY.format(table_name)

    self._cursor.execute(query)
    return bool(self._cursor.fetchone())

  def _ReadStorageMetadata(self):
    """Reads the storage metadata.

    Returns:
      bool: True if the storage metadata was read.
    """
    query = 'SELECT key, value FROM metadata'
    self._cursor.execute(query)

    metadata_values = {row[0]: row[1] for row in self._cursor.fetchall()}

    SQLiteStorageFile._CheckStorageMetadata(metadata_values)

    self.format_version = metadata_values['format_version']
    self.compression_format = metadata_values['compression_format']
    self.serialization_format = metadata_values['serialization_format']
    self.storage_type = metadata_values['storage_type']

  def _WriteAttributeContainer(self, attribute_container):
    """Writes an attribute container.

    The table for the container type must exist.

    Args:
      attribute_container (AttributeContainer): attribute container.
    """
    if attribute_container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT:
      timestamp, serialized_data = self._serialized_event_heap.PopEvent()
    else:
      serialized_data = self._SerializeAttributeContainer(attribute_container)

    if self.compression_format == definitions.COMPRESSION_FORMAT_ZLIB:
      compressed_data = zlib.compress(serialized_data)
      serialized_data = sqlite3.Binary(compressed_data)
    else:
      compressed_data = ''

    if self._storage_profiler:
      self._storage_profiler.Sample(
          'write', attribute_container.CONTAINER_TYPE, len(serialized_data),
          len(compressed_data))

    if attribute_container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT:
      query = 'INSERT INTO event (_timestamp, _data) VALUES (?, ?)'
      self._cursor.execute(query, (timestamp, serialized_data))
    else:
      query = 'INSERT INTO {0:s} (_data) VALUES (?)'.format(
          attribute_container.CONTAINER_TYPE)
      self._cursor.execute(query, (serialized_data, ))

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
        self._storage_profiler.Sample(
            'write', container_type, len(serialized_data), len(compressed_data))

      if container_type == self._CONTAINER_TYPE_EVENT:
        values_tuple_list.append((timestamp, serialized_data))
      else:
        values_tuple_list.append((serialized_data, ))

    self._cursor.executemany(query, values_tuple_list)

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

  def _CountStoredAttributeContainers(self, container_type):
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

    if not self._HasTable(self._CONTAINER_TYPE_ANALYSIS_REPORT):
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

  def AddAnalysisReport(self, analysis_report):
    """Adds an analysis report.

    Args:
      analysis_report (AnalysisReport): analysis report.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

    self._WriteAttributeContainer(analysis_report)

  def AddError(self, error):
    """Adds an error.

    Args:
      error (ExtractionError): error.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

    self._AddAttributeContainer(self._CONTAINER_TYPE_EXTRACTION_ERROR, error)

  def AddEvent(self, event):
    """Adds an event.

    Args:
      event (EventObject): event.

    Raises:
      IOError: when the storage file is closed or read-only or
          if the event data identifier type is not supported.
    """
    self._RaiseIfNotWritable()

    # TODO: change to no longer allow event_data_identifier is None
    # after refactoring every parser to generate event data.
    event_data_identifier = event.GetEventDataIdentifier()
    if event_data_identifier:
      if not isinstance(event_data_identifier, identifiers.SQLTableIdentifier):
        raise IOError('Unsupported event data identifier type: {0:s}'.format(
            type(event_data_identifier)))

      event.event_data_row_identifier = event_data_identifier.row_identifier

    self._AddSerializedEvent(event)

  def AddEventData(self, event_data):
    """Adds event data.

    Args:
      event_data (EventData): event data.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

    self._AddAttributeContainer(self._CONTAINER_TYPE_EVENT_DATA, event_data)

  def AddEventSource(self, event_source):
    """Adds an event source.

    Args:
      event_source (EventSource): event source.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

    self._AddAttributeContainer(
        self._CONTAINER_TYPE_EVENT_SOURCE, event_source)

  def AddEventTag(self, event_tag):
    """Adds an event tag.

    Args:
      event_tag (EventTag): event tag.

    Raises:
      IOError: when the storage file is closed or read-only or
          if the event identifier type is not supported.
    """
    self._RaiseIfNotWritable()

    event_identifier = event_tag.GetEventIdentifier()
    if not isinstance(event_identifier, identifiers.SQLTableIdentifier):
      raise IOError('Unsupported event identifier type: {0:s}'.format(
          type(event_identifier)))

    event_tag.event_row_identifier = event_identifier.row_identifier

    self._AddAttributeContainer(self._CONTAINER_TYPE_EVENT_TAG, event_tag)

  def AddEventTags(self, event_tags):
    """Adds event tags.

    Args:
      event_tags (list[EventTag]): event tags.

    Raises:
      IOError: when the storage file is closed or read-only or
          if the event tags cannot be serialized.
    """
    self._RaiseIfNotWritable()

    for event_tag in event_tags:
      self.AddEventTag(event_tag)

  @classmethod
  def CheckSupportedFormat(cls, path):
    """Checks if the storage file format is supported.

    Args:
      path (str): path to the storage file.

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

      cls._CheckStorageMetadata(metadata_values)

      connection.close()
      result = True

    except (IOError, sqlite3.DatabaseError):
      result = False

    return result

  def Close(self):
    """Closes the storage.

    Raises:
      IOError: if the storage file is already closed.
    """
    if not self._is_open:
      raise IOError('Storage file already closed.')

    if not self._read_only:
      self._WriteSerializedAttributeContainerList(
          self._CONTAINER_TYPE_EVENT_SOURCE)
      self._WriteSerializedAttributeContainerList(
          self._CONTAINER_TYPE_EVENT_DATA)
      self._WriteSerializedAttributeContainerList(self._CONTAINER_TYPE_EVENT)
      self._WriteSerializedAttributeContainerList(
          self._CONTAINER_TYPE_EVENT_TAG)
      self._WriteSerializedAttributeContainerList(
          self._CONTAINER_TYPE_EXTRACTION_ERROR)

    if self._connection:
      # We need to run commit or not all data is stored in the database.
      self._connection.commit()
      self._connection.close()

      self._connection = None
      self._cursor = None

    self._is_open = False

  def GetAnalysisReports(self):
    """Retrieves the analysis reports.

    Returns:
      generator(AnalysisReport): analysis report generator.
    """
    return self._GetAttributeContainers(self._CONTAINER_TYPE_ANALYSIS_REPORT)

  def GetErrors(self):
    """Retrieves the errors.

    Returns:
      generator(ExtractionError): error generator.
    """
    return self._GetAttributeContainers(self._CONTAINER_TYPE_EXTRACTION_ERROR)

  def GetEvents(self):
    """Retrieves the events.

    Yield:
      EventObject: event.
    """
    for event in self._GetAttributeContainers('event'):
      if hasattr(event, 'event_data_row_identifier'):
        event_data_identifier = identifiers.SQLTableIdentifier(
            'event_data', event.event_data_row_identifier)
        event.SetEventDataIdentifier(event_data_identifier)

        del event.event_data_row_identifier

      yield event

  def GetEventData(self):
    """Retrieves the event data.

    Yields:
      generator(EventData): event data generator.
    """
    return self._GetAttributeContainers(self._CONTAINER_TYPE_EVENT_DATA)

  def GetEventDataByIdentifier(self, identifier):
    """Retrieves specific event data.

    Args:
      identifier (SQLTableIdentifier): event data identifier.

    Returns:
      EventData: event data or None if not available.
    """
    return self._GetAttributeContainerByIndex(
        self._CONTAINER_TYPE_EVENT_DATA, identifier.row_identifier - 1)

  def GetEventSourceByIndex(self, index):
    """Retrieves a specific event source.

    Args:
      index (int): event source index.

    Returns:
      EventSource: event source or None if not available.
    """
    return self._GetAttributeContainerByIndex(
        self._CONTAINER_TYPE_EVENT_SOURCE, index)

  def GetEventSources(self):
    """Retrieves the event sources.

    Yields:
      generator(EventSource): event source generator.
    """
    return self._GetAttributeContainers(self._CONTAINER_TYPE_EVENT_SOURCE)

  def GetEventTagByIdentifier(self, identifier):
    """Retrieves a specific event tag.

    Args:
      identifier (SQLTableIdentifier): event tag identifier.

    Returns:
      EventTag: event tag or None if not available.
    """
    event_tag = self._GetAttributeContainerByIndex(
        self._CONTAINER_TYPE_EVENT_TAG, identifier.row_identifier - 1)
    if event_tag:
      event_identifier = identifiers.SQLTableIdentifier(
          self._CONTAINER_TYPE_EVENT, event_tag.event_row_identifier)
      event_tag.SetEventIdentifier(event_identifier)

      del event_tag.event_row_identifier

    return event_tag

  def GetEventTags(self):
    """Retrieves the event tags.

    Yields:
      EventTag: event tag.
    """
    for event_tag in self._GetAttributeContainers(
        self._CONTAINER_TYPE_EVENT_TAG):
      event_identifier = identifiers.SQLTableIdentifier(
          self._CONTAINER_TYPE_EVENT, event_tag.event_row_identifier)
      event_tag.SetEventIdentifier(event_identifier)

      del event_tag.event_row_identifier

      yield event_tag

  def GetNumberOfAnalysisReports(self):
    """Retrieves the number analysis reports.

    Returns:
      int: number of analysis reports.
    """
    return self._CountStoredAttributeContainers(
        self._CONTAINER_TYPE_ANALYSIS_REPORT)

  def GetNumberOfEventSources(self):
    """Retrieves the number event sources.

    Returns:
      int: number of event sources.
    """
    number_of_event_sources = self._CountStoredAttributeContainers(
        self._CONTAINER_TYPE_EVENT_SOURCE)

    number_of_event_sources += self._GetNumberOfSerializedAttributeContainers(
        self._CONTAINER_TYPE_EVENT_SOURCE)
    return number_of_event_sources

  def GetSessions(self):
    """Retrieves the sessions.

    Yields:
      Session: session attribute container.

    Raises:
      IOError: if a stream is missing or there is a mismatch in session
          identifiers between the session start and completion attribute
          containers.
    """
    session_start_generator = self._GetAttributeContainers(
        self._CONTAINER_TYPE_SESSION_START)
    session_completion_generator = self._GetAttributeContainers(
        self._CONTAINER_TYPE_SESSION_COMPLETION)

    for session_index in range(0, self._last_session):
      session_start = next(session_start_generator)
      session_completion = next(session_completion_generator)

      session = sessions.Session()
      session.CopyAttributesFromSessionStart(session_start)
      if session_completion:
        try:
          session.CopyAttributesFromSessionCompletion(session_completion)
        except ValueError:
          raise IOError(
              'Session identifier mismatch for session: {0:d}'.format(
                  session_index))

      yield session

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
      if hasattr(event, 'event_data_row_identifier'):
        event_data_identifier = identifiers.SQLTableIdentifier(
            'event_data', event.event_data_row_identifier)
        event.SetEventDataIdentifier(event_data_identifier)

        del event.event_data_row_identifier

      yield event

  def HasAnalysisReports(self):
    """Determines if a store contains analysis reports.

    Returns:
      bool: True if the store contains analysis reports.
    """
    return self._HasAttributeContainers(self._CONTAINER_TYPE_ANALYSIS_REPORT)

  def HasErrors(self):
    """Determines if a store contains extraction errors.

    Returns:
      bool: True if the store contains extraction errors.
    """
    return self._HasAttributeContainers(self._CONTAINER_TYPE_EXTRACTION_ERROR)

  def HasEventTags(self):
    """Determines if a store contains event tags.

    Returns:
      bool: True if the store contains event tags.
    """
    return self._HasAttributeContainers(self._CONTAINER_TYPE_EVENT_TAG)

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
      self._ReadStorageMetadata()
    else:
      # self._cursor.execute('PRAGMA journal_mode=MEMORY')

      # Turn off insert transaction integrity since we want to do bulk insert.
      self._cursor.execute('PRAGMA synchronous=OFF')

      if not self._HasTable('metadata'):
        self._WriteStorageMetadata()
      else:
        self._ReadStorageMetadata()

      if self.compression_format == definitions.COMPRESSION_FORMAT_ZLIB:
        data_column_type = 'BLOB'
      else:
        data_column_type = 'TEXT'

      for container_type in self._CONTAINER_TYPES:
        if not self._HasTable(container_type):
          if container_type == self._CONTAINER_TYPE_EVENT:
            query = self._CREATE_EVENT_TABLE_QUERY.format(
                container_type, data_column_type)
          else:
            query = self._CREATE_TABLE_QUERY.format(
                container_type, data_column_type)
          self._cursor.execute(query)

      self._connection.commit()

    last_session_start = self._CountStoredAttributeContainers(
        self._CONTAINER_TYPE_SESSION_START)

    last_session_completion = self._CountStoredAttributeContainers(
        self._CONTAINER_TYPE_SESSION_COMPLETION)

    # Initialize next_sequence_number based on the file contents so that
    # SQLTableIdentifier points to the correct attribute container.
    for container_type in self._REFERENCED_CONTAINER_TYPES:
      container_list = self._GetSerializedAttributeContainerList(container_type)
      container_list.next_sequence_number = (
          self._CountStoredAttributeContainers(container_type))

    # TODO: handle open sessions.
    if last_session_start != last_session_completion:
      logger.warning('Detected unclosed session.')

    self._last_session = last_session_completion

  def ReadPreprocessingInformation(self, knowledge_base):
    """Reads preprocessing information.

    The preprocessing information contains the system configuration which
    contains information about various system specific configuration data,
    for example the user accounts.

    Args:
      knowledge_base (KnowledgeBase): is used to store the preprocessing
          information.
    """
    generator = self._GetAttributeContainers(
        self._CONTAINER_TYPE_SYSTEM_CONFIGURATION)
    for stream_number, system_configuration in enumerate(generator):
      # TODO: replace stream_number by session_identifier.
      knowledge_base.ReadSystemConfigurationArtifact(
          system_configuration, session_identifier=stream_number)

  def WritePreprocessingInformation(self, knowledge_base):
    """Writes preprocessing information.

    Args:
      knowledge_base (KnowledgeBase): contains the preprocessing information.

    Raises:
      IOError: if the storage type does not support writing preprocess
          information or the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

    if self.storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Preprocess information not supported by storage type.')

    system_configuration = knowledge_base.GetSystemConfigurationArtifact()

    self._WriteAttributeContainer(system_configuration)

  def WriteSessionCompletion(self, session_completion):
    """Writes session completion information.

    Args:
      session_completion (SessionCompletion): session completion information.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

    self._WriteAttributeContainer(session_completion)

  def WriteSessionStart(self, session_start):
    """Writes session start information.

    Args:
      session_start (SessionStart): session start information.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

    self._WriteAttributeContainer(session_start)

  def WriteTaskCompletion(self, task_completion):
    """Writes task completion information.

    Args:
      task_completion (TaskCompletion): task completion information.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

    self._WriteAttributeContainer(task_completion)

  def WriteTaskStart(self, task_start):
    """Writes task start information.

    Args:
      task_start (TaskStart): task start information.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    self._RaiseIfNotWritable()

    self._WriteAttributeContainer(task_start)
