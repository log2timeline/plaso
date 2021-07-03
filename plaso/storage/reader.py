# -*- coding: utf-8 -*-
"""The storage interface classes."""

from plaso.containers import event_sources
from plaso.containers import events
from plaso.containers import reports
from plaso.containers import tasks
from plaso.containers import warnings


class StorageReader(object):
  """Storage reader interface."""

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
  _CONTAINER_TYPE_TASK_COMPLETION = tasks.TaskCompletion.CONTAINER_TYPE
  _CONTAINER_TYPE_TASK_START = tasks.TaskStart.CONTAINER_TYPE

  def __init__(self):
    """Initializes a storage reader."""
    super(StorageReader, self).__init__()
    self._store = None

  def __enter__(self):
    """Make usable with "with" statement."""
    return self

  # pylint: disable=unused-argument
  def __exit__(self, exception_type, value, traceback):
    """Make usable with "with" statement."""
    self.Close()

  def Close(self):
    """Closes the storage reader."""
    self._store.Close()
    self._store = None

  def GetAttributeContainerByIdentifier(self, container_type, identifier):
    """Retrieves a specific type of container with a specific identifier.

    Args:
      container_type (str): container type.
      identifier (AttributeContainerIdentifier): attribute container identifier.

    Returns:
      AttributeContainer: attribute container or None if not available.
    """
    return self._store.GetAttributeContainerByIdentifier(
        container_type, identifier)

  def GetAttributeContainers(self, container_type):
    """Retrieves a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.

    Returns:
      generator(AttributeContainers): attribute container generator.
    """
    return self._store.GetAttributeContainers(container_type)

  def GetNumberOfAnalysisReports(self):
    """Retrieves the number analysis reports.

    Returns:
      int: number of analysis reports.
    """
    return self._store.GetNumberOfAttributeContainers(
        self._CONTAINER_TYPE_ANALYSIS_REPORT)

  def GetNumberOfEventSources(self):
    """Retrieves the number of event sources.

    Returns:
      int: number of event sources.
    """
    return self._store.GetNumberOfAttributeContainers(
        self._CONTAINER_TYPE_EVENT_SOURCE)

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
    return self._store.GetSortedEvents(time_range)

  def HasAttributeContainers(self, container_type):
    """Determines if a store contains a specific type of attribute container.

    Args:
      container_type (str): attribute container type.

    Returns:
      bool: True if the store contains the specified type of attribute
          containers.
    """
    return self._store.HasAttributeContainers(container_type)

  # TODO: remove, this method is kept for backwards compatibility reasons.
  def ReadSystemConfiguration(self, knowledge_base):
    """Reads system configuration information.

    The system configuration contains information about various system specific
    configuration data, for example the user accounts.

    Args:
      knowledge_base (KnowledgeBase): is used to store the system configuration.
    """
    self._store.ReadSystemConfiguration(knowledge_base)

  def SetSerializersProfiler(self, serializers_profiler):
    """Sets the serializers profiler.

    Args:
      serializers_profiler (SerializersProfiler): serializers profiler.
    """
    self._store.SetSerializersProfiler(serializers_profiler)

  def SetStorageProfiler(self, storage_profiler):
    """Sets the storage profiler.

    Args:
      storage_profiler (StorageProfiler): storage profiler.
    """
    self._store.SetStorageProfiler(storage_profiler)
