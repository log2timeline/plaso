# -*- coding: utf-8 -*-
"""The attribute container store interface."""

import abc
import collections

from plaso.containers import artifacts
from plaso.containers import event_sources
from plaso.containers import events
from plaso.containers import manager as containers_manager
from plaso.containers import reports
from plaso.containers import sessions
from plaso.containers import tasks
from plaso.containers import warnings
from plaso.lib import definitions
from plaso.serializer import json_serializer


class BaseStore(object):
  """Attribute container store interface.

  Attributes:
    format_version (int): storage format version.
    serialization_format (str): serialization format.
    storage_type (str): storage type.
  """

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
  _CONTAINER_TYPE_SESSION_COMPLETION = sessions.SessionCompletion.CONTAINER_TYPE
  _CONTAINER_TYPE_SESSION_CONFIGURATION = (
      sessions.SessionConfiguration.CONTAINER_TYPE)
  _CONTAINER_TYPE_SESSION_START = sessions.SessionStart.CONTAINER_TYPE
  _CONTAINER_TYPE_SYSTEM_CONFIGURATION = (
      artifacts.SystemConfigurationArtifact.CONTAINER_TYPE)
  _CONTAINER_TYPE_TASK = tasks.Task.CONTAINER_TYPE

  # Container types that only should be used in a session store.
  _SESSION_STORE_ONLY_CONTAINER_TYPES = (
      _CONTAINER_TYPE_SESSION_COMPLETION,
      _CONTAINER_TYPE_SESSION_CONFIGURATION,
      _CONTAINER_TYPE_SESSION_START,
      _CONTAINER_TYPE_SYSTEM_CONFIGURATION)

  # Container types that only should be used in a task store.
  _TASK_STORE_ONLY_CONTAINER_TYPES = (_CONTAINER_TYPE_TASK,)

  def __init__(self, storage_type=definitions.STORAGE_TYPE_SESSION):
    """Initializes a store.

    Args:
      storage_type (Optional[str]): storage type.
    """
    super(BaseStore, self).__init__()
    self._attribute_container_sequence_numbers = collections.Counter()
    self._containers_manager = containers_manager.AttributeContainersManager
    self._last_session = 0
    self._serializer = json_serializer.JSONAttributeContainerSerializer
    self._serializers_profiler = None
    self._storage_profiler = None

    self.format_version = None
    self.serialization_format = None
    self.storage_type = storage_type

  def _DeserializeAttributeContainer(self, container_type, serialized_data):
    """Deserializes an attribute container.

    Args:
      container_type (str): attribute container type.
      serialized_data (bytes): serialized attribute container data.

    Returns:
      AttributeContainer: attribute container or None.

    Raises:
      IOError: if the serialized data cannot be decoded.
      OSError: if the serialized data cannot be decoded.
    """
    if not serialized_data:
      return None

    if self._serializers_profiler:
      self._serializers_profiler.StartTiming(container_type)

    try:
      serialized_string = serialized_data.decode('utf-8')
      attribute_container = self._serializer.ReadSerialized(serialized_string)

    except UnicodeDecodeError as exception:
      raise IOError('Unable to decode serialized data: {0!s}'.format(exception))

    except (TypeError, ValueError) as exception:
      # TODO: consider re-reading attribute container with error correction.
      raise IOError('Unable to read serialized data: {0!s}'.format(exception))

    finally:
      if self._serializers_profiler:
        self._serializers_profiler.StopTiming(container_type)

    return attribute_container

  def _GetAttributeContainerNextSequenceNumber(self, container_type):
    """Retrieves the next sequence number of an attribute container.

    Args:
      container_type (str): attribute container type.

    Returns:
      int: next sequence number.
    """
    self._attribute_container_sequence_numbers[container_type] += 1
    return self._attribute_container_sequence_numbers[container_type]

  def _GetAttributeContainerSchema(self, container_type):
    """Retrieves the schema of an attribute container.

    Args:
      container_type (str): attribute container type.

    Returns:
      dict[str, str]: attribute container schema or an empty dictionary if
          no schema available.
    """
    try:
      schema = self._containers_manager.GetSchema(container_type)
    except ValueError:
      schema = {}

    return schema

  @abc.abstractmethod
  def _RaiseIfNotReadable(self):
    """Raises if the store is not readable.

     Raises:
       OSError: if the store cannot be read from.
       IOError: if the store cannot be read from.
    """

  @abc.abstractmethod
  def _RaiseIfNotWritable(self):
    """Raises if the store is not writable.

     Raises:
       OSError: if the store cannot be written to.
       IOError: if the store cannot be written to.
    """

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

    finally:
      if self._serializers_profiler:
        self._serializers_profiler.StopTiming(
            attribute_container.CONTAINER_TYPE)

    return attribute_container_data

  def _SetAttributeContainerNextSequenceNumber(
      self, container_type, next_sequence_number):
    """Sets the next sequence number of an attribute container.

    Args:
      container_type (str): attribute container type.
      next_sequence_number (int): next sequence number.
    """
    self._attribute_container_sequence_numbers[
        container_type] = next_sequence_number

  @abc.abstractmethod
  def _WriteNewAttributeContainer(self, container):
    """Writes a new attribute container to the store.

    Args:
      container (AttributeContainer): attribute container.
    """

  @abc.abstractmethod
  def _WriteExistingAttributeContainer(self, container):
    """Writes an existing attribute container to the store.

    Args:
      container (AttributeContainer): attribute container.
    """

  def AddAttributeContainer(self, container):
    """Adds a new attribute container.

    Args:
      container (AttributeContainer): attribute container.

    Raises:
      OSError: if the store cannot be written to.
      IOError: if the store cannot be written to.
    """
    self._RaiseIfNotWritable()
    self._WriteNewAttributeContainer(container)

  @abc.abstractmethod
  def Close(self):
    """Closes the store."""

  @abc.abstractmethod
  def GetAttributeContainerByIdentifier(self, container_type, identifier):
    """Retrieves a specific type of container with a specific identifier.

    Args:
      container_type (str): container type.
      identifier (AttributeContainerIdentifier): attribute container identifier.

    Returns:
      AttributeContainer: attribute container or None if not available.

    Raises:
      IOError: when the store is closed or if an unsupported identifier is
          provided.
      OSError: when the store is closed or if an unsupported identifier is
          provided.
    """

  @abc.abstractmethod
  def GetAttributeContainers(self, container_type, filter_expression=None):
    """Retrieves a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.
      filter_expression (Optional[str]): expression to filter the resulting
          attribute containers by.

    Returns:
      generator(AttributeContainer): attribute container generator.

    Raises:
      IOError: when the store is closed.
      OSError: when the store is closed.
    """

  @abc.abstractmethod
  def GetEventTagByEventIdentifier(self, event_identifier):
    """Retrieves the event tag related to a specific event identifier.

    Args:
      event_identifier (AttributeContainerIdentifier): event.

    Returns:
      EventTag: event tag or None if not available.

    Raises:
      IOError: when the store is closed.
      OSError: when the store is closed.
    """

  @abc.abstractmethod
  def GetNumberOfAttributeContainers(self, container_type):
    """Retrieves the number of a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.

    Returns:
      int: the number of containers of a specified type.
    """

  # TODO: remove the need for seperate SessionStart and SessionCompletion
  # attribute containers.
  def GetSessions(self):
    """Retrieves the sessions.

    Yields:
      Session: session attribute container.

    Raises:
      IOError: if there is a mismatch in session identifiers between the
          session start and completion attribute containers.
      OSError: if there is a mismatch in session identifiers between the
          session start and completion attribute containers.
    """
    session_start_generator = self.GetAttributeContainers(
        self._CONTAINER_TYPE_SESSION_START)
    session_completion_generator = self.GetAttributeContainers(
        self._CONTAINER_TYPE_SESSION_COMPLETION)

    if self.HasAttributeContainers(self._CONTAINER_TYPE_SESSION_CONFIGURATION):
      session_configuration_generator = self.GetAttributeContainers(
          self._CONTAINER_TYPE_SESSION_CONFIGURATION)
    else:
      session_configuration_generator = None

    for session_index in range(1, self._last_session + 1):
      try:
        session_start = next(session_start_generator)
      except StopIteration:
        raise IOError('Missing session start: {0:d}'.format(session_index))

      try:
        session_completion = next(session_completion_generator)
      except StopIteration:
        pass

      session_configuration = None
      if session_configuration_generator:
        try:
          session_configuration = next(session_configuration_generator)
        except StopIteration:
          raise IOError('Missing session configuration: {0:d}'.format(
              session_index))

      session = sessions.Session()
      session.CopyAttributesFromSessionStart(session_start)

      if session_configuration:
        try:
          session.CopyAttributesFromSessionConfiguration(session_configuration)
        except ValueError:
          raise IOError((
              'Session identifier mismatch for session configuration: '
              '{0:d}').format(session_index))

      if session_completion:
        try:
          session.CopyAttributesFromSessionCompletion(session_completion)
        except ValueError:
          raise IOError((
              'Session identifier mismatch for session completion: '
              '{0:d}').format(session_index))

      yield session

  @abc.abstractmethod
  def GetSortedEvents(self, time_range=None):
    """Retrieves the events in increasing chronological order.

    This includes all events written to the store including those pending
    being flushed (written) to the store.

    Args:
      time_range (Optional[TimeRange]): time range used to filter events
          that fall in a specific period.

    Yields:
      EventObject: event.
    """

  @abc.abstractmethod
  def GetSystemConfigurationIdentifier(self):
    """Retrieves the system configuration identifier.

    Returns:
      AttributeContainerIdentifier: system configuration identifier.
    """

  @abc.abstractmethod
  def HasAttributeContainers(self, container_type):
    """Determines if a store contains a specific type of attribute container.

    Args:
      container_type (str): attribute container type.

    Returns:
      bool: True if the store contains the specified type of attribute
          containers.
    """

  @abc.abstractmethod
  def Open(self, **kwargs):
    """Opens the store."""

  def SetSerializersProfiler(self, serializers_profiler):
    """Sets the serializers profiler.

    Args:
      serializers_profiler (SerializersProfiler): serializers profiler.
    """
    self._serializers_profiler = serializers_profiler

  def SetStorageProfiler(self, storage_profiler):
    """Sets the storage profiler.

    Args:
      storage_profiler (StorageProfiler): storage profiler.
    """
    self._storage_profiler = storage_profiler

  def UpdateAttributeContainer(self, container):
    """Updates an existing attribute container.

    Args:
      container (AttributeContainer): attribute container.

    Raises:
      OSError: if the store cannot be written to.
      IOError: if the store cannot be written to.
    """
    self._RaiseIfNotWritable()
    self._WriteExistingAttributeContainer(container)
