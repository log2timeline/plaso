# -*- coding: utf-8 -*-
"""The storage writer."""

import abc
import collections

from plaso.containers import event_sources
from plaso.containers import events
from plaso.containers import reports
from plaso.containers import warnings
from plaso.lib import definitions


class StorageWriter(object):
  """Storage writer interface."""

  _CONTAINER_TYPE_ANALYSIS_REPORT = reports.AnalysisReport.CONTAINER_TYPE
  _CONTAINER_TYPE_ANALYSIS_WARNING = warnings.AnalysisWarning.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT = events.EventObject.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_DATA = events.EventData.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_DATA_STREAM = events.EventDataStream.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_SOURCE = event_sources.EventSource.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_TAG = events.EventTag.CONTAINER_TYPE
  _CONTAINER_TYPE_EXTRACTION_WARNING = warnings.ExtractionWarning.CONTAINER_TYPE
  _CONTAINER_TYPE_PREPROCESSING_WARNING = (
      warnings.PreprocessingWarning.CONTAINER_TYPE)
  _CONTAINER_TYPE_RECOVERY_WARNING = warnings.RecoveryWarning.CONTAINER_TYPE

  def __init__(self, storage_type=definitions.STORAGE_TYPE_SESSION):
    """Initializes a storage writer.

    Args:
      storage_type (Optional[str]): storage type.
    """
    super(StorageWriter, self).__init__()
    self._attribute_containers_counter = collections.Counter()
    self._first_written_event_source_index = 0
    self._serializers_profiler = None
    self._storage_profiler = None
    self._storage_type = storage_type
    self._store = None
    self._written_event_source_index = 0

  @property
  def number_of_analysis_reports(self):
    """int: number of analysis reports warnings written."""
    return self._attribute_containers_counter[
        self._CONTAINER_TYPE_ANALYSIS_REPORT]

  @property
  def number_of_analysis_warnings(self):
    """int: number of analysis warnings written."""
    return self._attribute_containers_counter[
        self._CONTAINER_TYPE_ANALYSIS_WARNING]

  @property
  def number_of_event_sources(self):
    """int: number of event sources written."""
    return self._attribute_containers_counter[self._CONTAINER_TYPE_EVENT_SOURCE]

  @property
  def number_of_event_tags(self):
    """int: number of event tags written."""
    return self._attribute_containers_counter[self._CONTAINER_TYPE_EVENT_TAG]

  @property
  def number_of_events(self):
    """int: number of events written."""
    return self._attribute_containers_counter[self._CONTAINER_TYPE_EVENT]

  @property
  def number_of_extraction_warnings(self):
    """int: number of extraction warnings written."""
    return self._attribute_containers_counter[
        self._CONTAINER_TYPE_EXTRACTION_WARNING]

  @property
  def number_of_preprocessing_warnings(self):
    """int: number of preprocessing warnings written."""
    return self._attribute_containers_counter[
        self._CONTAINER_TYPE_PREPROCESSING_WARNING]

  @property
  def number_of_recovery_warnings(self):
    """int: number of recovery warnings written."""
    return self._attribute_containers_counter[
        self._CONTAINER_TYPE_RECOVERY_WARNING]

  def _RaiseIfNotWritable(self):
    """Raises if the storage writer is not writable.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    if not self._store:
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

    self._store.AddAttributeContainer(container)

    self._attribute_containers_counter[container.CONTAINER_TYPE] += 1

  def AddOrUpdateEventTag(self, event_tag):
    """Adds a new or updates an existing event tag.

    Args:
      event_tag (EventTag): event tag.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    event_identifier = event_tag.GetEventIdentifier()
    existing_event_tag = self._store.GetEventTagByEventIdentifier(
        event_identifier)

    if not existing_event_tag:
      self.AddAttributeContainer(event_tag)

    else:
      if not set(existing_event_tag.labels).issubset(event_tag.labels):
        # No need to update the storage if all the labels are already set.
        existing_event_tag.AddLabels(event_tag.labels)
        self._store.UpdateAttributeContainer(existing_event_tag)

      if self._storage_type == definitions.STORAGE_TYPE_TASK:
        self._attribute_containers_counter[self._CONTAINER_TYPE_EVENT] += 1

  def Close(self):
    """Closes the storage writer.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self._store.Close()
    self._store = None

  def GetAttributeContainerByIdentifier(self, container_type, identifier):
    """Retrieves a specific type of container with a specific identifier.

    Args:
      container_type (str): container type.
      identifier (AttributeContainerIdentifier): attribute container identifier.

    Returns:
      AttributeContainer: attribute container or None if not available.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    return self._store.GetAttributeContainerByIdentifier(
        container_type, identifier)

  def GetAttributeContainerByIndex(self, container_type, index):
    """Retrieves a specific attribute container.

    Args:
      container_type (str): attribute container type.
      index (int): attribute container index.

    Returns:
      AttributeContainer: attribute container or None if not available.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    return self._store.GetAttributeContainerByIndex(container_type, index)

  def GetAttributeContainers(self, container_type):
    """Retrieves a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.

    Returns:
      generator(AttributeContainers): attribute container generator.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    return self._store.GetAttributeContainers(container_type)

  # TODO: remove this helper method, currently only used by parser tests.
  def GetEvents(self):
    """Retrieves the events.

    Returns:
      generator(EventObject): event generator.
    """
    return self.GetAttributeContainers(self._CONTAINER_TYPE_EVENT)

  @abc.abstractmethod
  def GetFirstWrittenEventSource(self):
    """Retrieves the first event source that was written after open.

    Using GetFirstWrittenEventSource and GetNextWrittenEventSource newly
    added event sources can be retrieved in order of addition.

    Returns:
      EventSource: event source or None if there are no newly written ones.
    """

  @abc.abstractmethod
  def GetNextWrittenEventSource(self):
    """Retrieves the next event source that was written after open.

    Returns:
      EventSource: event source or None if there are no newly written ones.
    """

  def GetSessions(self):
    """Retrieves the sessions.

    Returns:
      generator(Session): session generator.
    """
    return self._store.GetSessions()

  def GetSortedEvents(self, time_range=None):
    """Retrieves the events in increasing chronological order.

    This includes all events written to the storage including those pending
    being flushed (written) to the storage.

    Args:
      time_range (Optional[TimeRange]): time range used to filter events
          that fall in a specific period.

    Returns:
      generator(EventObject): event generator.
    """
    return self._store.GetSortedEvents(time_range=time_range)

  def GetSystemConfigurationIdentifier(self):
    """Retrieves the system configuration identifier.

    Returns:
      AttributeContainerIdentifier: system configuration identifier.
    """
    return self._store.GetSystemConfigurationIdentifier()

  @abc.abstractmethod
  def Open(self, **kwargs):
    """Opens the storage writer."""

  def SetSerializersProfiler(self, serializers_profiler):
    """Sets the serializers profiler.

    Args:
      serializers_profiler (SerializersProfiler): serializers profiler.
    """
    self._serializers_profiler = serializers_profiler
    if self._store:
      self._store.SetSerializersProfiler(serializers_profiler)

  def SetStorageProfiler(self, storage_profiler):
    """Sets the storage profiler.

    Args:
      storage_profiler (StorageProfiler): storage profiler.
    """
    self._storage_profiler = storage_profiler
    if self._store:
      self._store.SetStorageProfiler(storage_profiler)

  def UpdateAttributeContainer(self, container):
    """Updates an existing attribute container.

    Args:
      container (AttributeContainer): attribute container.

    Raises:
      IOError: when the storage writer is closed.
      OSError: when the storage writer is closed.
    """
    self._RaiseIfNotWritable()

    self._store.UpdateAttributeContainer(container)

  def WriteSessionCompletion(self, session):
    """Writes session completion information.

    Args:
      session (Session): session the storage changes are part of.

    Raises:
      IOError: when the storage writer is closed or if the storage type is
          not supported.
      OSError: when the storage writer is closed or if the storage type is
          not supported.
    """
    self._RaiseIfNotWritable()

    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Unsupported storage type.')

    session_completion = session.CreateSessionCompletion()
    self._store.AddAttributeContainer(session_completion)

  def WriteSessionConfiguration(self, session):
    """Writes session configuration information.

    Args:
      session (Session): session the storage changes are part of.

    Raises:
      IOError: when the storage writer is closed or if the storage type is
          not supported.
      OSError: when the storage writer is closed or if the storage type is
          not supported.
    """
    self._RaiseIfNotWritable()

    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Unsupported storage type.')

    session_configuration = session.CreateSessionConfiguration()
    self._store.AddAttributeContainer(session_configuration)

  def WriteSessionStart(self, session):
    """Writes session start information.

    Args:
      session (Session): session the storage changes are part of.

    Raises:
      IOError: when the storage writer is closed or if the storage type is
          not supported.
      OSError: when the storage writer is closed or if the storage type is
          not supported.
    """
    self._RaiseIfNotWritable()

    if self._storage_type != definitions.STORAGE_TYPE_SESSION:
      raise IOError('Unsupported storage type.')

    session_start = session.CreateSessionStart()
    self._store.AddAttributeContainer(session_start)
