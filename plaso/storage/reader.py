# -*- coding: utf-8 -*-
"""The storage reader."""

from plaso.containers import events
from plaso.containers import sessions
from plaso.storage import logger


class StorageReader(object):
  """Storage reader interface."""

  _CONTAINER_TYPE_SESSION = sessions.Session.CONTAINER_TYPE
  _CONTAINER_TYPE_SESSION_COMPLETION = sessions.SessionCompletion.CONTAINER_TYPE
  _CONTAINER_TYPE_SESSION_CONFIGURATION = (
      sessions.SessionConfiguration.CONTAINER_TYPE)
  _CONTAINER_TYPE_SESSION_START = sessions.SessionStart.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_TAG = events.EventTag.CONTAINER_TYPE

  def __init__(self):
    """Initializes a storage reader."""
    super(StorageReader, self).__init__()
    self._serializers_profiler = None
    self._storage_profiler = None
    self._store = None

  def __enter__(self):
    """Make usable with "with" statement."""
    return self

  # pylint: disable=unused-argument
  def __exit__(self, exception_type, value, traceback):
    """Make usable with "with" statement."""
    self.Close()

  # Kept for backwards compatibility.
  def _GetSessionsOld(self):
    """Retrieves the sessions.

    Yields:
      Session: session attribute container.

    Raises:
      IOError: if there is a mismatch in session identifiers between the
          session start and completion attribute containers.
      OSError: if there is a mismatch in session identifiers between the
          session start and completion attribute containers.
    """
    last_session_start = self._store.GetNumberOfAttributeContainers(
        self._CONTAINER_TYPE_SESSION_START)
    last_session_completion = self._store.GetNumberOfAttributeContainers(
        self._CONTAINER_TYPE_SESSION_COMPLETION)

    # TODO: handle open sessions.
    if last_session_start != last_session_completion:
      logger.warning('Detected unclosed session.')

    session_start_generator = self._store.GetAttributeContainers(
        self._CONTAINER_TYPE_SESSION_START)
    session_completion_generator = self._store.GetAttributeContainers(
        self._CONTAINER_TYPE_SESSION_COMPLETION)

    if self.HasAttributeContainers(self._CONTAINER_TYPE_SESSION_CONFIGURATION):
      session_configuration_generator = self._store.GetAttributeContainers(
          self._CONTAINER_TYPE_SESSION_CONFIGURATION)
    else:
      session_configuration_generator = None

    for session_index in range(1, last_session_completion + 1):
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

  def GetAttributeContainerByIndex(self, container_type, index):
    """Retrieves a specific attribute container.

    Args:
      container_type (str): attribute container type.
      index (int): attribute container index.

    Returns:
      AttributeContainer: attribute container or None if not available.
    """
    return self._store.GetAttributeContainerByIndex(container_type, index)

  def GetAttributeContainers(self, container_type, filter_expression=None):
    """Retrieves a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.
      filter_expression (Optional[str]): expression to filter the resulting
          attribute containers by.

    Returns:
      generator(AttributeContainers): attribute container generator.
    """
    return self._store.GetAttributeContainers(
        container_type, filter_expression=filter_expression)

  def GetEventTagByEventIdentifer(self, event_identifier):
    """Retrieves the event tag of a specific event.

    Args:
      event_identifier (AttributeContainerIdentifier): event attribute
          container identifier.

    Returns:
      EventTag: event tag or None if the event has no event tag.
    """
    lookup_key = event_identifier.CopyToString()
    filter_expression = '_event_identifier == "{0:s}"'.format(lookup_key)

    event_tags = list(self.GetAttributeContainers(
        self._CONTAINER_TYPE_EVENT_TAG, filter_expression=filter_expression))

    if not event_tags:
      return None

    if len(event_tags) > 1:
      logger.warning('More than 1 event tag returned.')

    return event_tags[0]

  def GetFormatVersion(self):
    """Retrieves the format version of the underlying storage file.

    Returns:
      int: the format version.
    """
    return self._store.format_version

  def GetNumberOfAttributeContainers(self, container_type):
    """Retrieves the number of a specific type of attribute containers.

    Args:
      container_type (str): attribute container type.

    Returns:
      int: the number of containers of a specified type.
    """
    return self._store.GetNumberOfAttributeContainers(container_type)

  def GetSerializationFormat(self):
    """Retrieves the serialization format of the underlying storage file.

    Returns:
      str: the serialization format.
    """
    return self._store.serialization_format

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
    if self.HasAttributeContainers(self._CONTAINER_TYPE_SESSION):
      containers = self.GetAttributeContainers(self._CONTAINER_TYPE_SESSION)
    else:
      # Kept for backwards compatibility.
      containers = self._GetSessionsOld()

    yield from containers

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

  def HasAttributeContainers(self, container_type):
    """Determines if a store contains a specific type of attribute container.

    Args:
      container_type (str): attribute container type.

    Returns:
      bool: True if the store contains the specified type of attribute
          containers.
    """
    return self._store.HasAttributeContainers(container_type)

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
