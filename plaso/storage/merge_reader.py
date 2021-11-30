# -*- coding: utf-8 -*-
"""The storage merge reader."""

import collections

from plaso.containers import event_sources
from plaso.containers import events
from plaso.containers import warnings
from plaso.storage import logger


class StorageMergeReader(object):
  """Storage reader for merging.

  Attributes:
    number_of_containers (int): number of containers merged in last call to
        MergeAttributeContainers.
    parsers_counter (collections.Counter): number of events per parser or
        parser plugin.
  """

  _CONTAINER_TYPE_EVENT = events.EventObject.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_DATA = events.EventData.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_DATA_STREAM = events.EventDataStream.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_SOURCE = event_sources.EventSource.CONTAINER_TYPE
  _CONTAINER_TYPE_EXTRACTION_WARNING = warnings.ExtractionWarning.CONTAINER_TYPE
  _CONTAINER_TYPE_PREPROCESSING_WARNING = (
      warnings.PreprocessingWarning.CONTAINER_TYPE)
  _CONTAINER_TYPE_RECOVERY_WARNING = warnings.RecoveryWarning.CONTAINER_TYPE

  # Some container types reference other container types, such as event
  # referencing event_data. Container types in this tuple must be ordered after
  # all the container types they reference.
  _CONTAINER_TYPES = (
      _CONTAINER_TYPE_EVENT_SOURCE,
      _CONTAINER_TYPE_EVENT_DATA_STREAM,
      _CONTAINER_TYPE_EVENT_DATA,
      _CONTAINER_TYPE_EVENT,
      _CONTAINER_TYPE_EXTRACTION_WARNING,
      _CONTAINER_TYPE_RECOVERY_WARNING,
      'windows_eventlog_message_file',
      'windows_eventlog_message_string')

  def __init__(self, task_storage_reader, task_identifier):
    """Initializes a storage merge reader.

    Args:
      task_storage_reader (StorageReader): task storage reader.
      task_identifier (str): identifier of the task that is merged.
    """
    super(StorageMergeReader, self).__init__()
    self._active_container_type = None
    self._active_generator = None
    self._container_types = list(self._CONTAINER_TYPES)
    self._event_data_identifier_mappings = {}
    self._event_data_parser_mappings = {}
    self._event_data_stream_identifier_mappings = {}
    self._message_file_identifier_mappings = {}
    self._task_identifier = task_identifier
    self._task_storage_reader = task_storage_reader

    self.number_of_containers = 0
    self.parsers_counter = collections.Counter()

  def _MergeAttributeContainer(self, storage_writer, container):
    """Merges an attribute container from a task store into the storage writer.

    Args:
      storage_writer (StorageWriter): storage writer.
      container (AttributeContainer): attribute container.
    """
    if container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT:
      event_data_identifier = container.GetEventDataIdentifier()
      event_data_lookup_key = event_data_identifier.CopyToString()

      event_data_identifier = self._event_data_identifier_mappings.get(
          event_data_lookup_key, None)

      if event_data_identifier:
        container.SetEventDataIdentifier(event_data_identifier)
      else:
        identifier = container.GetIdentifier()
        identifier_string = identifier.CopyToString()

        # TODO: store this as a merge warning so this is preserved
        # in the storage file.
        logger.error((
            'Unable to merge event attribute container: {0:s} since '
            'corresponding event data: {1:s} could not be found.').format(
                identifier_string, event_data_lookup_key))
        return

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_DATA:
      event_data_stream_identifier = container.GetEventDataStreamIdentifier()
      event_data_stream_lookup_key = None
      if event_data_stream_identifier:
        event_data_stream_lookup_key = (
            event_data_stream_identifier.CopyToString())

        event_data_stream_identifier = (
            self._event_data_stream_identifier_mappings.get(
                event_data_stream_lookup_key, None))

      if event_data_stream_identifier:
        container.SetEventDataStreamIdentifier(event_data_stream_identifier)
      elif event_data_stream_lookup_key:
        identifier = container.GetIdentifier()
        identifier_string = identifier.CopyToString()

        # TODO: store this as a merge warning so this is preserved
        # in the storage file.
        logger.error((
            'Unable to merge event data attribute container: {0:s} since '
            'corresponding event data stream: {1:s} could not be '
            'found.').format(identifier_string, event_data_stream_lookup_key))
        return

    elif container.CONTAINER_TYPE == 'windows_eventlog_message_string':
      message_file_identifier = container.GetMessageFileIdentifier()
      message_file_lookup_key = message_file_identifier.CopyToString()

      message_file_identifier = self._message_file_identifier_mappings.get(
          message_file_lookup_key, None)

      if message_file_identifier:
        container.SetMessageFileIdentifier(message_file_identifier)
      else:
        identifier = container.GetIdentifier()
        identifier_string = identifier.CopyToString()

        # TODO: store this as a merge warning so this is preserved
        # in the storage file.
        logger.error((
            'Unable to merge Windows EventLog message string attribute '
            'container: {0:s} since corresponding Windows EventLog message '
            'file: {1:s} could not be found.').format(
                identifier_string, message_file_lookup_key))
        return

    if container.CONTAINER_TYPE in (
        self._CONTAINER_TYPE_EVENT_DATA,
        self._CONTAINER_TYPE_EVENT_DATA_STREAM,
        'windows_eventlog_message_file'):
      # Preserve the lookup key before adding it to the attribute container
      # store.
      identifier = container.GetIdentifier()
      lookup_key = identifier.CopyToString()

    storage_writer.AddAttributeContainer(container)

    if container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT:
      parser_name = self._event_data_parser_mappings.get(
          event_data_lookup_key, 'N/A')
      self.parsers_counter[parser_name] += 1
      self.parsers_counter['total'] += 1

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_DATA:
      identifier = container.GetIdentifier()
      self._event_data_identifier_mappings[lookup_key] = identifier

      parser_name = container.parser.split('/')[-1]
      self._event_data_parser_mappings[lookup_key] = parser_name

    elif container.CONTAINER_TYPE == self._CONTAINER_TYPE_EVENT_DATA_STREAM:
      identifier = container.GetIdentifier()
      self._event_data_stream_identifier_mappings[lookup_key] = identifier

    elif container.CONTAINER_TYPE == 'windows_eventlog_message_file':
      identifier = container.GetIdentifier()
      self._message_file_identifier_mappings[lookup_key] = identifier

  def Close(self):
    """Closes the merge reader."""
    self._task_storage_reader.Close()
    self._task_storage_reader = None

  def MergeAttributeContainers(
      self, storage_writer, maximum_number_of_containers=0):
    """Reads attribute containers from a task store into the storage writer.

    Args:
      storage_writer (StorageWriter): storage writer.
      maximum_number_of_containers (Optional[int]): maximum number of
          containers to merge, where 0 represent no limit.

    Returns:
      bool: True if the entire task storage file has been merged.
    """
    if not self._active_container_type:
      logger.debug('Starting merge of task: {0:s}'.format(
          self._task_identifier))
    else:
      logger.debug('Continuing merge of: {0:s} of task: {1:s}'.format(
          self._active_container_type, self._task_identifier))

    self.number_of_containers = 0

    while self._active_generator or self._container_types:
      if not self._active_generator:
        self._active_container_type = self._container_types.pop(0)
        self._active_generator = (
            self._task_storage_reader.GetAttributeContainers(
                self._active_container_type))

      try:
        container = next(self._active_generator)
        self.number_of_containers += 1
      except StopIteration:
        container = None
        self._active_generator = None

      if container:
        self._MergeAttributeContainer(storage_writer, container)

      if 0 < maximum_number_of_containers <= self.number_of_containers:
        break

    merge_completed = not self._active_generator and not self._container_types

    logger.debug('Merged {0:d} containers of task: {1:s}'.format(
        self.number_of_containers, self._task_identifier))

    return merge_completed
