# -*- coding: utf-8 -*-
"""SQLite-based storage."""

import logging
import os
import sqlite3
import zlib

from plaso.containers import sessions
from plaso.lib import definitions
from plaso.storage import identifiers
from plaso.storage import interface


class SQLiteStorageFile(interface.BaseFileStorage):
  """SQLite-based storage file.

  Attributes:
    format_version (int): storage format version.
    serialization_format (str): serialization format.
    storage_type (str): storage type.
  """

  _FORMAT_VERSION = 20170703

  _CONTAINER_TYPES = (
      u'analysis_report', u'extraction_error', u'event', u'event_source',
      u'event_tag', u'session_completion', u'session_start',
      u'task_completion', u'task_start')

  _CREATE_METADATA_TABLE_QUERY = (
      u'CREATE TABLE metadata (key TEXT, value TEXT);')

  _CREATE_TABLE_QUERY = (
      u'CREATE TABLE {0:s} ('
      u'_identifier INTEGER PRIMARY KEY AUTOINCREMENT,'
      u'_data {1:s});')

  _HAS_TABLE_QUERY = (
      u'SELECT name FROM sqlite_master '
      u'WHERE type = "table" AND name = "{0:s}"')

  # The maximum buffer size of serialized data before triggering
  # a flush to disk (64 MiB).
  _MAXIMUM_BUFFER_SIZE = 64 * 1024 * 1024

  def __init__(
      self, maximum_buffer_size=0,
      storage_type=definitions.STORAGE_TYPE_SESSION):
    """Initializes a storage.

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
      raise ValueError(u'Maximum buffer size value out of bounds.')

    if not maximum_buffer_size:
      maximum_buffer_size = self._MAXIMUM_BUFFER_SIZE

    super(SQLiteStorageFile, self).__init__()
    self._connection = None
    self._cursor = None
    self._last_session = 0
    self._maximum_buffer_size = maximum_buffer_size

    if storage_type == definitions.STORAGE_TYPE_SESSION:
      self.compression_format = definitions.COMPRESSION_FORMAT_ZLIB
    else:
      self.compression_format = definitions.COMPRESSION_FORMAT_NONE

    self.format_version = self._FORMAT_VERSION
    self.serialization_format = definitions.SERIALIZER_FORMAT_JSON
    self.storage_type = storage_type

    # TODO: initialize next_sequence_number on read

  def _AddAttributeContainer(self, container_type, attribute_container):
    """Adds an atttibute container.

    Args:
      container_type (str): attribute container type.
      attribute_container (AttributeContainer): attribute container.

    Raises:
      IOError: when the storage file is closed or read-only or
          if the error cannot be serialized.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage file.')

    if self._read_only:
      raise IOError(u'Unable to write to read-only storage file.')

    container_list = self._GetSerializedAttributeContainerList(
        container_type)

    identifier = identifiers.SQLTableIdentifier(
        attribute_container, container_list.next_sequence_number)
    attribute_container.SetIdentifier(identifier)

    serialized_data = self._SerializeAttributeContainer(attribute_container)

    container_list.PushAttributeContainer(serialized_data)

    if container_list.data_size > self._maximum_buffer_size:
      self._WriteSerializedAttributeContainerList(container_type)

  def _GetAttributeContainer(self, container_type):
    """Retrieves an attribute container.

    Args:
      container_type (str): attribute container type.

    Yields:
      AttributeContainer: attribute container.
    """
    query = u'SELECT _identifier, _data FROM {0:s}'.format(container_type)
    self._cursor.execute(query)

    row = self._cursor.fetchone()
    while row:
      identifier = identifiers.SQLTableIdentifier(container_type, row[0])

      if self.compression_format == definitions.COMPRESSION_FORMAT_ZLIB:
        serialized_data = zlib.decompress(row[1])
      else:
        serialized_data = row[1]

      attribute_container = self._DeserializeAttributeContainer(
          container_type, serialized_data)
      attribute_container.SetIdentifier(identifier)
      yield attribute_container

      row = self._cursor.fetchone()

  def _HasTable(self, table_name):
    """Determines if a specific table exists.

    Args:
      table_name: the table name.

    Returns:
      True if the table exists, false otheriwse.
    """
    query = self._HAS_TABLE_QUERY.format(table_name)

    self._cursor.execute(query)
    return bool(self._cursor.fetchone())

  def _ReadStorageMetadata(self):
    """Reads the storage metadata.

    Returns:
      bool: True if the storage metadata was read.

    Raises:
      IOError: if the format version or the serializer format is not supported.
    """
    query = u'SELECT key, value FROM metadata'
    self._cursor.execute(query)

    metadata_values = {}
    for row in self._cursor.fetchone():
      metadata_values[row[0]] = row[1]

    # TODO: check metadata.

    self.format_version = metadata_values.get(
        u'format_version', self.format_version)
    self.compression_format = metadata_values.get(
        u'compression_format', self.compression_format)
    self.serialization_format = metadata_values.get(
        u'serialization_format', self.serialization_format)
    self.storage_type = metadata_values.get(u'storage_type', self.storage_type)

  def _WriteAttributeContainer(self, attribute_container):
    """Writes an attribute container.

    The table for the container type must exist.

    Args:
      attribute_container (AttributeContainer): attribute container.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage file.')

    if self._read_only:
      raise IOError(u'Unable to write to read-only storage file.')

    serialized_data = self._SerializeAttributeContainer(attribute_container)

    if self.compression_format == definitions.COMPRESSION_FORMAT_ZLIB:
      serialized_data = zlib.compress(serialized_data)
      serialized_data = sqlite3.Binary(serialized_data)

    query = u'INSERT INTO {0:s} (_data) VALUES (?)'.format(
        attribute_container.CONTAINER_TYPE)
    self._cursor.execute(query, (serialized_data, ))

    identifier = identifiers.SQLTableIdentifier(
        attribute_container, self._cursor.lastrowid)
    attribute_container.SetIdentifier(identifier)

  def _WriteSerializedAttributeContainerList(self, container_type):
    """Writes a serialized attribute container list.

    Args:
      container_type (str): attribute container type.
    """
    container_list = self._GetSerializedAttributeContainerList(container_type)
    if not container_list.data_size:
      return

    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(u'write')

    query = u'INSERT INTO {0:s} (_data) VALUES (?)'.format(container_type)

    # TODO: directly use container_list.
    values_tuple_list = []
    for _ in range(container_list.number_of_attribute_containers):
      serialized_data = container_list.PopAttributeContainer()

      if self.compression_format == definitions.COMPRESSION_FORMAT_ZLIB:
        serialized_data = zlib.compress(serialized_data)
        serialized_data = sqlite3.Binary(serialized_data)

      values_tuple_list.append((serialized_data, ))

    self._cursor.executemany(query, values_tuple_list)

    if self._serializers_profiler:
      self._serializers_profiler.StopTiming(u'write')

    container_list.Empty()

  def _WriteStorageMetadata(self):
    """Writes the storage metadata."""
    self._cursor.execute(self._CREATE_METADATA_TABLE_QUERY)

    query = u'INSERT INTO metadata (key, value) VALUES (?, ?)'

    key = u'format_version'
    value = u'{0:d}'.format(self._FORMAT_VERSION)
    self._cursor.execute(query, (key, value))

    key = u'compression_format'
    value = self.compression_format
    self._cursor.execute(query, (key, value))

    key = u'serialization_format'
    value = self.serialization_format
    self._cursor.execute(query, (key, value))

    key = u'storage_type'
    value = self.storage_type
    self._cursor.execute(query, (key, value))

  def AddAnalysisReport(self, analysis_report):
    """Adds an analysis report.

    Args:
      analysis_report (AnalysisReport): analysis report.
    """
    self._WriteAttributeContainer(analysis_report)

  def AddError(self, error):
    """Adds an error.

    Args:
      error (ExtractionError): error.
    """
    self._AddAttributeContainer(u'extraction_error', error)

  def AddEvent(self, event):
    """Adds an event.

    Args:
      event (EventObject): event.
    """
    self._AddAttributeContainer(u'event', event)

  def AddEventSource(self, event_source):
    """Adds an event source.

    Args:
      event_source (EventSource): event source.
    """
    self._AddAttributeContainer(u'event_source', event_source)

  def AddEventTag(self, event_tag):
    """Adds an event tag.

    Args:
      event_tag (EventTag): event tag.

    Raises:
      IOError: if the event tag event identifier type is not supported.
    """
    event_identifier = event_tag.GetEventIdentifier()
    if not isinstance(event_identifier, identifiers.SQLTableIdentifier):
      raise IOError(u'Unsupported event identifier type: {0:s}'.format(
          type(event_identifier)))

    event_tag.event_entry_index = event_identifier.row_identifier

    self._AddAttributeContainer(u'event_tag', event_tag)

  @classmethod
  def CheckSupportedFormat(cls, path):
    """Checks is the storage file format is supported.

    Args:
      path (str): path to the storage file.

    Returns:
      bool: True if the format is supported.
    """
    try:
      connection = sqlite3.connect(
          path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)

      cursor = connection.cursor()

      query = u'SELECT * FROM metadata'
      cursor.execute(query)

      # TODO: check metadata.

      connection.close()
      result = True

    except sqlite3.DatabaseError:
      result = False

    return result

  def Close(self):
    """Closes the storage.

    Raises:
      IOError: if the storage file is already closed.
    """
    if not self._is_open:
      raise IOError(u'Storage file already closed.')

    if not self._read_only:
      self._WriteSerializedAttributeContainerList(u'event_source')
      self._WriteSerializedAttributeContainerList(u'event')
      self._WriteSerializedAttributeContainerList(u'event_tag')
      self._WriteSerializedAttributeContainerList(u'extraction_error')

    if self._serializers_profiler:
      self._serializers_profiler.Write()

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
    return self._GetAttributeContainer(u'analysis_report')

  def GetErrors(self):
    """Retrieves the errors.

    Returns:
      generator(ExtractionError): error generator.
    """
    return self._GetAttributeContainer(u'extraction_error')

  def GetEvents(self):
    """Retrieves the events.

    Returns:
      generator(EventObject): event generator.
    """
    return self._GetAttributeContainer(u'event')

  def GetEventSourceByIndex(self, index):
    """Retrieves a specific event source.

    Args:
      index (int): event source index.

    Returns:
      EventSource: event source or None.
    """
    sequence_number = index + 1
    query = u'SELECT _data FROM event_source WHERE rowid = {0:d}'.format(
        sequence_number)
    self._cursor.execute(query)

    row = self._cursor.fetchone()
    if row:
      identifier = identifiers.SQLTableIdentifier(
          u'event_source', sequence_number)

      if self.compression_format == definitions.COMPRESSION_FORMAT_ZLIB:
        serialized_data = zlib.decompress(row[0])
      else:
        serialized_data = row[0]

      event_source = self._DeserializeAttributeContainer(
          u'event_source', serialized_data)
      event_source.SetIdentifier(identifier)
      return event_source

    query = u'SELECT COUNT(*) FROM event_source'
    self._cursor.execute(query)

    row = self._cursor.fetchone()
    index -= row[0]

    serialized_data = self._GetSerializedAttributeContainerByIndex(
        u'event_source', index)
    event_source = self._DeserializeAttributeContainer(
        u'event_source', serialized_data)
    if event_source:
      identifier = identifiers.SQLTableIdentifier(
          u'event_source', sequence_number)
      event_source.SetIdentifier(identifier)
    return event_source

  def GetEventSources(self):
    """Retrieves the event sources.

    Yields:
      generator(EventSource): event source generator.
    """
    return self._GetAttributeContainer(u'event_source')

  def GetEventTags(self):
    """Retrieves the event tags.

    Yields:
      EventTag: event tag.
    """
    for event_tag in self._GetAttributeContainer(u'event_tag'):
      event_identifier = identifiers.SQLTableIdentifier(
          u'event', event_tag.event_entry_index)
      event_tag.SetEventIdentifier(event_identifier)

      yield event_tag

  def GetNumberOfAnalysisReports(self):
    """Retrieves the number analysis reports.

    Returns:
      int: number of analysis reports.
    """
    if not self._HasTable(u'analysis_reports'):
      return 0

    query = u'SELECT COUNT(*) FROM analysis_reports'
    self._cursor.execute(query)

    row = self._cursor.fetchone()
    return row[0]

  def GetNumberOfEventSources(self):
    """Retrieves the number event sources.

    Returns:
      int: number of event sources.
    """
    if not self._HasTable(u'event_source'):
      return 0

    query = u'SELECT COUNT(*) FROM event_source'
    self._cursor.execute(query)

    row = self._cursor.fetchone()
    number_of_event_sources = row[0]

    number_of_event_sources += self._GetNumberOfSerializedAttributeContainers(
        u'event_sources')
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
    session_start_generator = self._GetAttributeContainer(u'session_start')
    session_completion_generator = self._GetAttributeContainer(
        u'session_completion')

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
              u'Session identifier mismatch for session: {0:d}'.format(
                  session_index))

      yield session

  # TODO: time_range is currently not operational, nor that events are
  # returned in chronological order. Fix this.
  def GetSortedEvents(self, time_range=None):
    """Retrieves the events in increasing chronological order.

    Args:
      time_range (Optional[TimeRange]): time range used to filter events
          that fall in a specific period.

    Yields:
      generator(EventObject): event generator.
    """
    return self._GetAttributeContainer(u'event')

  def HasAnalysisReports(self):
    """Determines if a storage contains analysis reports.

    Returns:
      bool: True if the storage contains analysis reports.
    """
    query = u'SELECT COUNT(*) FROM analysis_report'
    self._cursor.execute(query)

    row = self._cursor.fetchone()
    return row and row[0] != 0

  def HasErrors(self):
    """Determines if a storage contains extraction errors.

    Returns:
      bool: True if the storage contains extraction errors.
    """
    query = u'SELECT COUNT(*) FROM extraction_error'
    self._cursor.execute(query)

    row = self._cursor.fetchone()
    return row and row[0] != 0

  def HasEventTags(self):
    """Determines if a storage contains event tags.

    Returns:
      bool: True if the storage contains event tags.
    """
    query = u'SELECT COUNT(*) FROM event_tags'
    self._cursor.execute(query)

    row = self._cursor.fetchone()
    return row and row[0] != 0

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
      raise IOError(u'Storage file already opened.')

    if not path:
      raise ValueError(u'Missing path.')

    connection = sqlite3.connect(
        path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)

    cursor = connection.cursor()
    if not cursor:
      return False

    self._connection = connection
    self._cursor = cursor
    self._is_open = True
    self._read_only = read_only

    if not read_only:
      # self._cursor.execute(u'PRAGMA journal_mode=MEMORY')

      # Turn off insert transaction integrity since we want to do bulk insert.
      self._cursor.execute(u'PRAGMA synchronous=OFF')

      if not self._HasTable(u'metadata'):
        self._WriteStorageMetadata()
      else:
        self._ReadStorageMetadata()

      if self.compression_format == definitions.COMPRESSION_FORMAT_ZLIB:
        data_column_type = u'BLOB'
      else:
        data_column_type = u'TEXT'

      for container_type in self._CONTAINER_TYPES:
        if not self._HasTable(container_type):
          query = self._CREATE_TABLE_QUERY.format(
              container_type, data_column_type)
          self._cursor.execute(query)

      self._connection.commit()

    last_session_start = 0
    if self._HasTable(u'session_start'):
      query = u'SELECT COUNT(*) FROM session_start'
      self._cursor.execute(query)
      row = self._cursor.fetchone()
      last_session_start = row[0]

    last_session_completion = 0
    if self._HasTable(u'session_completion'):
      query = u'SELECT COUNT(*) FROM session_completion'
      self._cursor.execute(query)
      row = self._cursor.fetchone()
      last_session_completion = row[0]

    # TODO: handle open sessions.
    if last_session_start != last_session_completion:
      logging.warning(u'Detected unclosed session.')

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
    # TODO: implement.
    pass

  def WritePreprocessingInformation(self, knowledge_base):
    """Writes preprocessing information.

    Args:
      knowledge_base (KnowledgeBase): contains the preprocessing information.

    Raises:
      IOError: if the storage type does not support writing preprocess
          information or the storage file is closed or read-only or
          if the preprocess information stream already exists.
    """
    # TODO: implement.
    pass

  def WriteSessionCompletion(self, session_completion):
    """Writes session completion information.

    Args:
      session_completion (SessionCompletion): session completion information.
    """
    self._WriteAttributeContainer(session_completion)

  def WriteSessionStart(self, session_start):
    """Writes session start information.

    Args:
      session_start (SessionStart): session start information.
    """
    self._WriteAttributeContainer(session_start)

  def WriteTaskCompletion(self, task_completion):
    """Writes task completion information.

    Args:
      task_completion (TaskCompletion): task completion information.
    """
    self._WriteAttributeContainer(task_completion)

  def WriteTaskStart(self, task_start):
    """Writes task start information.

    Args:
      task_start (TaskStart): task start information.
    """
    self._WriteAttributeContainer(task_start)


class SQLiteStorageMergeReader(interface.FileStorageMergeReader):
  """SQLite-based storage file reader for merging."""

  _CONTAINER_TYPES = (
      u'event_source', u'event', u'extraction_error', u'analysis_report',
      u'event_tag')

  _TABLE_NAMES_QUERY = (
      u'SELECT name FROM sqlite_master WHERE type = "table"')

  def __init__(self, storage_writer, path):
    """Initializes a storage merge reader.

    Args:
      storage_writer (StorageWriter): storage writer.
      path (str): path to the input file.

    Raises:
      IOError: if the input file cannot be opened.
    """
    super(SQLiteStorageMergeReader, self).__init__(storage_writer)
    self._active_container_type = None
    self._active_cursor = None
    self._connection = None
    self._container_types = None
    self._cursor = None
    self._path = path

  def _AddAttributeContainer(self, attribute_container):
    """Adds a single attribute container to the storage writer.

    Args:
      attribute_container (AttributeContainer): container

    Raises:
      RuntimeError: if the attribute container type is not supported.
    """
    container_type = attribute_container.CONTAINER_TYPE
    if container_type == u'event_source':
      self._storage_writer.AddEventSource(attribute_container)

    elif container_type == u'event':
      self._storage_writer.AddEvent(attribute_container)

    elif container_type == u'event_tag':
      event_identifier = identifiers.SerializedStreamIdentifier(
          attribute_container.event_stream_number,
          attribute_container.event_entry_index)
      attribute_container.SetEventIdentifier(event_identifier)

      self._storage_writer.AddEventTag(attribute_container)

    elif container_type == u'extraction_error':
      self._storage_writer.AddError(attribute_container)

    elif container_type == u'analysis_report':
      self._storage_writer.AddAnalysisReport(attribute_container)

    elif container_type not in (u'task_completion', u'task_start'):
      raise RuntimeError(u'Unsupported container type: {0:s}'.format(
          container_type))

  def MergeAttributeContainers(self, maximum_number_of_containers=0):
    """Reads attribute containers from a task storage file into the writer.

    Args:
      maximum_number_of_containers (Optional[int]): maximum number of
          containers to merge, where 0 represent no limit.

    Returns:
      bool: True if the entire task storage file has been merged.

    Raises:
      OSError: if the task storage file cannot be deleted.
    """
    if not self._cursor:
      self._connection = sqlite3.connect(
          self._path,
          detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
      self._cursor = self._connection.cursor()

      self._cursor.execute(self._TABLE_NAMES_QUERY)
      table_names = [row[0] for row in self._cursor.fetchall()]

      # Remove container types not stored in the storage file but keep
      # the container types list in order.
      self._container_types = list(self._CONTAINER_TYPES)
      for name in set(self._CONTAINER_TYPES).difference(table_names):
        self._container_types.remove(name)

    number_of_containers = 0
    while self._active_cursor or self._container_types:
      if not self._active_cursor:
        self._active_container_type = self._container_types.pop(0)

        query = u'SELECT _data FROM {0:s}'.format(self._active_container_type)
        self._cursor.execute(query)

        self._active_cursor = self._cursor

      if maximum_number_of_containers > 0:
        number_of_rows = maximum_number_of_containers - number_of_containers
        rows = self._active_cursor.fetchmany(size=number_of_rows)
      else:
        rows = self._active_cursor.fetchall()

      if not rows:
        self._active_cursor = None
        continue

      for row in rows:
        serialized_data = row[0]

        attribute_container = self._DeserializeAttributeContainer(
            self._active_container_type, serialized_data)
        self._AddAttributeContainer(attribute_container)
        number_of_containers += 1

      if (maximum_number_of_containers > 0 and
          number_of_containers >= maximum_number_of_containers):
        return False

    self._connection.close()
    self._connection = None
    self._cursor = None

    os.remove(self._path)

    return True


class SQLiteStorageFileReader(interface.FileStorageReader):
  """SQLite-based storage file reader."""

  def __init__(self, path):
    """Initializes a storage reader.

    Args:
      path (str): path to the input file.
    """
    super(SQLiteStorageFileReader, self).__init__(path)
    self._storage_file = SQLiteStorageFile()
    self._storage_file.Open(path=path)


class SQLiteStorageFileWriter(interface.FileStorageWriter):
  """SQLite-based storage file writer."""

  def _CreateStorageFile(self):
    """Creates a storage file.

    Returns:
      SQLiteStorageFile: storage file.
    """
    return SQLiteStorageFile(storage_type=self._storage_type)

  def _CreateTaskStorageMergeReader(self, path):
    """Creates a task storage merge reader.

    Args:
      path (str): path to the task storage file that should be merged.

    Returns:
      SQLiteStorageMergeReader: storage merge reader.
    """
    return SQLiteStorageMergeReader(self, path)

  def _CreateTaskStorageWriter(self, path, task):
    """Creates a task storage writer.

    Args:
      path (str): path to the storage file.
      task (Task): task.

    Returns:
      SQLiteStorageFileWriter: storage writer.
    """
    return SQLiteStorageFileWriter(
        self._session, path,
        storage_type=definitions.STORAGE_TYPE_TASK, task=task)
