# -*- coding: utf-8 -*-
"""The storage interface classes."""

import abc
import collections

from plaso.containers import event_sources
from plaso.containers import events
from plaso.containers import reports
from plaso.containers import tasks
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
  _CONTAINER_TYPE_TASK_COMPLETION = tasks.TaskCompletion.CONTAINER_TYPE
  _CONTAINER_TYPE_TASK_START = tasks.TaskStart.CONTAINER_TYPE

  def __init__(
      self, session, storage_type=definitions.STORAGE_TYPE_SESSION, task=None):
    """Initializes a storage writer.

    Args:
      session (Session): session the storage changes are part of.
      storage_type (Optional[str]): storage type.
      task(Optional[Task]): task.
    """
    super(StorageWriter, self).__init__()
    self._attribute_containers_counter = collections.Counter()
    self._event_data_parser_mappings = {}
    self._first_written_event_source_index = 0
    self._serializers_profiler = None
    self._session = session
    self._storage_profiler = None
    self._storage_type = storage_type
    self._store = None
    self._task = task
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

  def _UpdateAnalysisReportSessionCounter(self, analysis_report):
    """Updates the analysis report session counter.

    Args:
      analysis_report (AnalysisReport): a report.
    """
    if self._storage_type == definitions.STORAGE_TYPE_SESSION:
      report_identifier = analysis_report.plugin_name
      self._session.analysis_reports_counter['total'] += 1
      self._session.analysis_reports_counter[report_identifier] += 1

  def _UpdateEventLabelsSessionCounter(self, event_tag):
    """Updates the event labels session counter.

    Args:
      event_tag (EventTag): an event tag.
    """
    if self._storage_type == definitions.STORAGE_TYPE_SESSION:
      self._session.event_labels_counter['total'] += 1
      for label in event_tag.labels:
        self._session.event_labels_counter[label] += 1

  def _UpdateEventDataParsersMappings(self, event_data):
    """Updates the event data parsers mappings.

    Args:
      event_data (EventData): event data.
    """
    if self._storage_type == definitions.STORAGE_TYPE_SESSION:
      identifier = event_data.GetIdentifier()
      lookup_key = identifier.CopyToString()
      parser_name = event_data.parser.split('/')[-1]
      self._event_data_parser_mappings[lookup_key] = parser_name

  def _UpdateEventParsersSessionCounter(self, event):
    """Updates the event parsers session counter.

    Args:
      event (EventObject): an event.
    """
    if self._storage_type == definitions.STORAGE_TYPE_SESSION:
      event_data_identifier = event.GetEventDataIdentifier()
      lookup_key = event_data_identifier.CopyToString()

      parser_name = self._event_data_parser_mappings.get(lookup_key, 'N/A')
      self._session.parsers_counter[parser_name] += 1
      self._session.parsers_counter['total'] += 1

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

    if container.CONTAINER_TYPE == self._CONTAINER_TYPE_ANALYSIS_REPORT:
      self._UpdateAnalysisReportSessionCounter(container)

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT:
      self._UpdateEventParsersSessionCounter(container)

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_DATA:
      self._UpdateEventDataParsersMappings(container)

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_TAG:
      self._UpdateEventLabelsSessionCounter(container)

    self._attribute_containers_counter[container.CONTAINER_TYPE] += 1

  # TODO: remove after refactoring.
  def AddEventTag(self, event_tag):
    """Adds an event tag.

    Args:
      event_tag (EventTag): an event tag.
    """
    self.AddAttributeContainer(event_tag)

  def Close(self):
    """Closes the storage writer."""
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
    """
    self._RaiseIfNotWritable()

    return self._store.GetAttributeContainerByIdentifier(
        container_type, identifier)

  def GetAttributeContainers(self, container_type):
    """Retrieves a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.

    Returns:
      generator(AttributeContainers): attribute container generator.
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

  @abc.abstractmethod
  def WriteSessionCompletion(self, aborted=False):
    """Writes session completion information.

    Args:
      aborted (Optional[bool]): True if the session was aborted.
    """

  @abc.abstractmethod
  def WriteSessionConfiguration(self):
    """Writes session configuration information."""

  @abc.abstractmethod
  def WriteSessionStart(self):
    """Writes session start information."""

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
    self._store.WriteTaskCompletion(task_completion)

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
    self._store.WriteTaskStart(task_start)
