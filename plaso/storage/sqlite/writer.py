# -*- coding: utf-8 -*-
"""Storage writer for SQLite storage files."""

from plaso.lib import definitions
from plaso.storage import interface
from plaso.storage.sqlite import sqlite_file


class SQLiteStorageFileWriter(interface.StorageWriter):
  """SQLite-based storage file writer."""

  def __init__(
      self, session, output_file,
      storage_type=definitions.STORAGE_TYPE_SESSION, task=None):
    """Initializes a storage writer.

    Args:
      session (Session): session the storage changes are part of.
      output_file (str): path to the output file.
      storage_type (Optional[str]): storage type.
      task(Optional[Task]): task.
    """
    super(SQLiteStorageFileWriter, self).__init__(
        session, storage_type=storage_type, task=task)
    self._output_file = output_file
    self._storage_file = None

  def _CreateStorageFile(self):
    """Creates a storage file.

    Returns:
      SQLiteStorageFile: storage file.
    """
    return sqlite_file.SQLiteStorageFile(storage_type=self._storage_type)

  def _RaiseIfNotWritable(self):
    """Raises if the storage writer is not writable.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    if not self._storage_file:
      raise IOError('Unable to write to closed storage writer.')

  def AddAttributeContainer(self, container):
    """Adds an attribute container.

    Args:
      container (AttributeContainer): attribute container.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self._storage_file.AddAttributeContainer(container)

    if container.CONTAINER_TYPE == self._CONTAINER_TYPE_ANALYSIS_REPORT:
      self._UpdateAnalysisReportSessionCounter(container)

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_ANALYSIS_WARNING:
      self.number_of_analysis_warnings += 1

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT:
      self._UpdateEventParsersSessionCounter(container)

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_DATA:
      self._UpdateEventDataParsersMappings(container)

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_SOURCE:
      self.number_of_event_sources += 1

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_TAG:
      self._UpdateEventLabelsSessionCounter(container)

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EXTRACTION_WARNING:
      self.number_of_extraction_warnings += 1

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_PREPROCESSING_WARNING:
      self.number_of_preprocessing_warnings += 1

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_RECOVERY_WARNING:
      self.number_of_recovery_warnings += 1

  # TODO: remove after refactoring.
  def AddEventTag(self, event_tag):
    """Adds an event tag.

    Args:
      event_tag (EventTag): an event tag.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    # TODO: refactor to use AddOrUpdateAttributeContainer
    self._storage_file.AddEventTag(event_tag)

    self._UpdateEventLabelsSessionCounter(event_tag)

  def Close(self):
    """Closes the storage writer.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self._storage_file.Close()
    self._storage_file = None

  def GetAttributeContainerByIdentifier(self, container_type, identifier):
    """Retrieves a specific type of container with a specific identifier.

    Args:
      container_type (str): container type.
      identifier (AttributeContainerIdentifier): attribute container identifier.

    Returns:
      AttributeContainer: attribute container or None if not available.
    """
    return self._storage_file.GetAttributeContainerByIdentifier(
        container_type, identifier)

  def GetAttributeContainers(self, container_type):
    """Retrieves a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.

    Returns:
      generator(AttributeContainers): attribute container generator.
    """
    return self._storage_file.GetAttributeContainers(container_type)

  def GetFirstWrittenEventSource(self):
    """Retrieves the first event source that was written after open.

    Using GetFirstWrittenEventSource and GetNextWrittenEventSource newly
    added event sources can be retrieved in order of addition.

    Returns:
      EventSource: event source or None if there are no newly written ones.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    if not self._storage_file:
      raise IOError('Unable to read from closed storage writer.')

    event_source = self._storage_file.GetAttributeContainerByIndex(
        self._CONTAINER_TYPE_EVENT_SOURCE,
        self._first_written_event_source_index)

    if event_source:
      self._written_event_source_index = (
          self._first_written_event_source_index + 1)
    return event_source

  def GetNextWrittenEventSource(self):
    """Retrieves the next event source that was written after open.

    Returns:
      EventSource: event source or None if there are no newly written ones.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    if not self._storage_file:
      raise IOError('Unable to read from closed storage writer.')

    event_source = self._storage_file.GetAttributeContainerByIndex(
        self._CONTAINER_TYPE_EVENT_SOURCE, self._written_event_source_index)
    if event_source:
      self._written_event_source_index += 1
    return event_source

  def GetSortedEvents(self, time_range=None):
    """Retrieves the events in increasing chronological order.

    This includes all events written to the storage including those pending
    being flushed (written) to the storage.

    Args:
      time_range (Optional[TimeRange]): time range used to filter events
          that fall in a specific period.

    Returns:
      generator(EventObject): event generator.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    if not self._storage_file:
      raise IOError('Unable to read from closed storage writer.')

    return self._storage_file.GetSortedEvents(time_range=time_range)

  def Open(self, **unused_kwargs):
    """Opens the storage writer.

    Raises:
      IOError: if the storage writer is already opened.
      OSError: if the storage writer is already opened.
    """
    if self._storage_file:
      raise IOError('Storage writer already opened.')

    self._storage_file = self._CreateStorageFile()

    if self._serializers_profiler:
      self._storage_file.SetSerializersProfiler(self._serializers_profiler)

    if self._storage_profiler:
      self._storage_file.SetStorageProfiler(self._storage_profiler)

    self._storage_file.Open(path=self._output_file, read_only=False)

    number_of_event_sources = self._storage_file.GetNumberOfAttributeContainers(
        self._CONTAINER_TYPE_EVENT_SOURCE)
    self._first_written_event_source_index = number_of_event_sources
    self._written_event_source_index = self._first_written_event_source_index

  def SetSerializersProfiler(self, serializers_profiler):
    """Sets the serializers profiler.

    Args:
      serializers_profiler (SerializersProfiler): serializers profiler.
    """
    self._serializers_profiler = serializers_profiler
    if self._storage_file:
      self._storage_file.SetSerializersProfiler(serializers_profiler)

  def SetStorageProfiler(self, storage_profiler):
    """Sets the storage profiler.

    Args:
      storage_profiler (StorageProfiler): storage profiler.
    """
    self._storage_profiler = storage_profiler
    if self._storage_file:
      self._storage_file.SetStorageProfiler(storage_profiler)

  def WriteSessionCompletion(self, aborted=False):
    """Writes session completion information.

    Args:
      aborted (Optional[bool]): True if the session was aborted.

    Raises:
      IOError: if the storage type is not supported or
          when the storage writer is closed.
      OSError: if the storage type is not supported or
          when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Unsupported storage type.')

    # TODO: move self._session out of the SQLiteStorageFileWriter?
    self._session.aborted = aborted
    session_completion = self._session.CreateSessionCompletion()
    self._storage_file.WriteSessionCompletion(session_completion)

  def WriteSessionConfiguration(self):
    """Writes session configuration information.

    Raises:
      IOError: if the storage type does not support writing session
          configuration information or when the storage writer is closed.
      OSError: if the storage type does not support writing session
          configuration information or when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Session configuration not supported by storage type.')

    # TODO: move self._session out of the SQLiteStorageFileWriter?
    session_configuration = self._session.CreateSessionConfiguration()
    self._storage_file.WriteSessionConfiguration(session_configuration)

  def WriteSessionStart(self):
    """Writes session start information.

    Raises:
      IOError: if the storage type is not supported or
          when the storage writer is closed.
      OSError: if the storage type is not supported or
          when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Unsupported storage type.')

    # TODO: move self._session out of the SQLiteStorageFileWriter?
    session_start = self._session.CreateSessionStart()
    self._storage_file.WriteSessionStart(session_start)

  def WriteTaskCompletion(self, aborted=False):
    """Writes task completion information.

    Args:
      aborted (Optional[bool]): True if the session was aborted.

    Raises:
      IOError: if the storage type is not supported or
          when the storage writer is closed.
      OSError: if the storage type is not supported or
          when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    if self._storage_type != definitions.STORAGE_TYPE_TASK:
      raise IOError('Unsupported storage type.')

    self._task.aborted = aborted
    task_completion = self._task.CreateTaskCompletion()
    self._storage_file.WriteTaskCompletion(task_completion)

  def WriteTaskStart(self):
    """Writes task start information.

    Raises:
      IOError: if the storage type is not supported or
          when the storage writer is closed.
      OSError: if the storage type is not supported or
          when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    if self._storage_type != definitions.STORAGE_TYPE_TASK:
      raise IOError('Unsupported storage type.')

    task_start = self._task.CreateTaskStart()
    self._storage_file.WriteTaskStart(task_start)
