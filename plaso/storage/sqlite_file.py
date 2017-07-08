# -*- coding: utf-8 -*-
"""SQLite-based storage."""

import os
import sqlite3

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

  _FORMAT_VERSION = 20170121

  _CONTAINER_TYPES = (
      u'analysis_report', u'extraction_error', u'event', u'event_source',
      u'event_tag', u'session_completion', u'session_start',
      u'task_completion', u'task_start')

  _CREATE_TABLE_QUERY = (
      u'CREATE TABLE {0:s} ('
      u'_identifier INTEGER PRIMARY KEY AUTOINCREMENT,'
      u'_data ATTRIBUTE_CONTAINER);')

  _HAS_TABLE_QUERY = (
      u'SELECT name FROM sqlite_master '
      u'WHERE type = "table" AND name = "{0:s}"')

  def __init__(self, storage_type=definitions.STORAGE_TYPE_SESSION):
    """Initializes a storage.

    Args:
      storage_type (Optional[str]): storage type.
    """
    super(SQLiteStorageFile, self).__init__()
    self._connection = None
    self._cursor = None

    self.format_version = self._FORMAT_VERSION
    self.serialization_format = definitions.SERIALIZER_FORMAT_JSON
    self.storage_type = storage_type

    # Note first argument must be of type str.
    sqlite3.register_converter(
        'ATTRIBUTE_CONTAINER', self._serializer.ReadSerialized)

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

      attribute_container = row[1]
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

    attribute_container_data = self._SerializeAttributeContainer(
        attribute_container)

    query = u'INSERT INTO {0:s} (_data) VALUES (?)'.format(
        attribute_container.CONTAINER_TYPE)
    self._cursor.execute(query, (attribute_container_data, ))

    identifier = identifiers.SQLTableIdentifier(
        attribute_container, self._cursor.lastrowid)
    attribute_container.SetIdentifier(identifier)

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
    self._WriteAttributeContainer(error)

  def AddEvent(self, event):
    """Adds an event.

    Args:
      event (EventObject): event.
    """
    self._WriteAttributeContainer(event)

  def AddEventSource(self, event_source):
    """Adds an event source.

    Args:
      event_source (EventSource): event source.
    """
    self._WriteAttributeContainer(event_source)

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

    self._WriteAttributeContainer(event_tag)

  def Close(self):
    """Closes the storage.

    Raises:
      IOError: if the storage file is already closed.
    """
    if not self._is_open:
      raise IOError(u'Storage file already closed.')

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
    query = u'SELECT _data FROM {0:s} WHERE rowid = {1:d}'.format(
        u'event_source', index + 1)
    self._cursor.execute(query)

    row = self._cursor.fetchone()
    if row:
      return row[0]

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

  def GetNumberOfEventSources(self):
    """Retrieves the number event sources.

    Returns:
      int: number of event sources.
    """
    if not self._HasTable(u'event_source'):
      return 0

    query = u'SELECT COUNT(*) FROM {0:s}'.format(u'event_source')
    self._cursor.execute(query)

    row = self._cursor.fetchone()
    return row[0]

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
    query = u'SELECT COUNT(*) FROM {0:s}'.format(u'analysis_report')
    self._cursor.execute(query)

    row = self._cursor.fetchone()
    return row and row[0] != 0

  def HasErrors(self):
    """Determines if a storage contains extraction errors.

    Returns:
      bool: True if the storage contains extraction errors.
    """
    query = u'SELECT COUNT(*) FROM {0:s}'.format(u'extraction_error')
    self._cursor.execute(query)

    row = self._cursor.fetchone()
    return row and row[0] != 0

  def HasEventTags(self):
    """Determines if a storage contains event tags.

    Returns:
      bool: True if the storage contains event tags.
    """
    query = u'SELECT COUNT(*) FROM {0:s}'.format(u'event_tags')
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
      for container_type in self._CONTAINER_TYPES:
        if not self._HasTable(container_type):
          query = self._CREATE_TABLE_QUERY.format(container_type)
          self._cursor.execute(query)

      self._connection.commit()

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


class SQLiteStorageMergeReader(interface.StorageMergeReader):
  """SQLite-based storage file reader for merging."""

  _CONTAINER_TYPES = (
      u'event_source', u'event', u'extraction_error', u'analysis_report',
      u'event_tag')

  def __init__(self, storage_writer, path):
    """Initializes a storage merge reader.

    Args:
      storage_writer (StorageWriter): storage writer.
      path (str): path to the input file.

    Raises:
      IOError: if the input file cannot be opened.
    """
    super(SQLiteStorageMergeReader, self).__init__(storage_writer)
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
    # TODO: add support for maximum_number_of_containers.
    connection = sqlite3.connect(
        self._path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    cursor = connection.cursor()

    number_of_containers = 0
    for container_type in self._CONTAINER_TYPES:
      if not self._HasTable(container_type):
        continue

      query = u'SELECT _data FROM {0:s}'.format(container_type)
      cursor.execute(query)

      row = cursor.fetchone()
      while row:
        self._AddAttributeContainer(row[0])
        number_of_containers += 1

        # if (maximum_number_of_containers > 0 and
        #     number_of_containers >= maximum_number_of_containers):
        #   return False

        row = cursor.fetchone()

      # pylint: disable=protected-access
      # TODO: fix this hack.
      self._storage_writer._storage_file._connection.commit()

    connection.close()

    connection = None
    cursor = None

    os.remove(self._path)

    return True


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
