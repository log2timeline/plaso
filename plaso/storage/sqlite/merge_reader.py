# -*- coding: utf-8 -*-
"""Merge reader for SQLite storage files."""

from __future__ import unicode_literals

import os

from plaso.containers import event_sources
from plaso.containers import events
from plaso.containers import manager as containers_manager
from plaso.containers import reports
from plaso.containers import tasks
from plaso.containers import warnings
from plaso.lib import definitions
from plaso.storage import interface
from plaso.storage import logger
from plaso.storage.sqlite import sqlite_file


class SQLiteStorageMergeReader(interface.StorageMergeReader):
  """SQLite-based storage file reader for merging."""

  _ATTRIBUTE_CONTAINERS_MANAGER = (
      containers_manager.AttributeContainersManager)

  _CONTAINER_TYPE_ANALYSIS_REPORT = reports.AnalysisReport.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT = events.EventObject.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_DATA = events.EventData.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_DATA_STREAM = events.EventDataStream.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_SOURCE = event_sources.EventSource.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_TAG = events.EventTag.CONTAINER_TYPE
  _CONTAINER_TYPE_EXTRACTION_WARNING = warnings.ExtractionWarning.CONTAINER_TYPE
  _CONTAINER_TYPE_TASK_COMPLETION = tasks.TaskCompletion.CONTAINER_TYPE
  _CONTAINER_TYPE_TASK_START = tasks.TaskStart.CONTAINER_TYPE

  # Some container types reference other container types, such as event
  # referencing event_data. Container types in this tuple must be ordered after
  # all the container types they reference.
  _CONTAINER_TYPES = (
      _CONTAINER_TYPE_EVENT_SOURCE,
      _CONTAINER_TYPE_EVENT_DATA_STREAM,
      _CONTAINER_TYPE_EVENT_DATA,
      _CONTAINER_TYPE_EVENT,
      _CONTAINER_TYPE_EVENT_TAG,
      _CONTAINER_TYPE_EXTRACTION_WARNING,
      _CONTAINER_TYPE_ANALYSIS_REPORT)

  _ADD_CONTAINER_TYPE_METHODS = {
      _CONTAINER_TYPE_ANALYSIS_REPORT: '_AddAnalysisReport',
      _CONTAINER_TYPE_EVENT: '_AddEvent',
      _CONTAINER_TYPE_EVENT_DATA: '_AddEventData',
      _CONTAINER_TYPE_EVENT_DATA_STREAM: '_AddEventDataStream',
      _CONTAINER_TYPE_EVENT_SOURCE: '_AddEventSource',
      _CONTAINER_TYPE_EVENT_TAG: '_AddEventTag',
      _CONTAINER_TYPE_EXTRACTION_WARNING: '_AddWarning',
  }

  def __init__(self, storage_writer, path):
    """Initializes a storage merge reader.

    Args:
      storage_writer (StorageWriter): storage writer.
      path (str): path to the input file.

    Raises:
      IOError: if the input file cannot be opened.
      RuntimeError: if an add container method is missing.
    """
    super(SQLiteStorageMergeReader, self).__init__(storage_writer)
    self._active_container_generator = None
    self._active_container_type = None
    self._add_active_container_method = None
    self._add_container_type_methods = {}
    self._container_types = None
    self._event_data_identifier_mappings = {}
    self._event_data_stream_identifier_mappings = {}
    self._event_identifier_mappings = {}
    self._path = path
    self._task_storage_file = None

    # Create a runtime lookup table for the add container type method. This
    # prevents having to create a series of if-else checks for container types.
    # The table is generated at runtime as there are no forward function
    # declarations in Python.
    for container_type, method_name in self._ADD_CONTAINER_TYPE_METHODS.items():
      method = getattr(self, method_name, None)
      if not method:
        raise RuntimeError(
            'Add method missing for container type: {0:s}'.format(
                container_type))

      self._add_container_type_methods[container_type] = method

  # pylint: disable=unused-argument

  def _AddAnalysisReport(self, analysis_report, serialized_data=None):
    """Adds an analysis report.

    Args:
      analysis_report (AnalysisReport): analysis report.
      serialized_data (Optional[bytes]): serialized form of the analysis report.
    """
    self._storage_writer.AddAnalysisReport(analysis_report)

  def _AddEvent(self, event, serialized_data=None):
    """Adds an event.

    Args:
      event (EventObject): event.
      serialized_data (Optional[bytes]): serialized form of the event.
    """
    event_data_identifier = event.GetEventDataIdentifier()
    lookup_key = event_data_identifier.CopyToString()

    event_data_identifier = self._event_data_identifier_mappings.get(
        lookup_key, None)

    if not event_data_identifier:
      event_identifier = event.GetIdentifier()
      event_identifier = event_identifier.CopyToString()

      # TODO: store this as an extraction warning so this is preserved
      # in the storage file.
      logger.error((
          'Unable to merge event attribute container: {0:s} since '
          'corresponding event data: {1:s} could not be found.').format(
              event_identifier, lookup_key))
      return

    event.SetEventDataIdentifier(event_data_identifier)

    identifier = event.GetIdentifier()
    lookup_key = identifier.CopyToString()

    self._storage_writer.AddEvent(event)

    identifier = event.GetIdentifier()
    self._event_identifier_mappings[lookup_key] = identifier

  def _AddEventData(self, event_data, serialized_data=None):
    """Adds event data.

    Args:
      event_data (EventData): event data.
      serialized_data (bytes): serialized form of the event data.
    """
    event_data_stream_identifier = event_data.GetEventDataStreamIdentifier()
    if event_data_stream_identifier:
      lookup_key = event_data_stream_identifier.CopyToString()

      event_data_stream_identifier = (
          self._event_data_stream_identifier_mappings.get(lookup_key, None))

      if not event_data_stream_identifier:
        event_data_identifier = event_data.GetIdentifier()
        event_data_identifier = event_data_identifier.CopyToString()

        # TODO: store this as an extraction warning so this is preserved
        # in the storage file.
        logger.error((
            'Unable to merge event data attribute container: {0:s} since '
            'corresponding event data stream: {1:s} could not be '
            'found.').format(event_data_identifier, lookup_key))
        return

      event_data.SetEventDataStreamIdentifier(event_data_stream_identifier)

    identifier = event_data.GetIdentifier()
    lookup_key = identifier.CopyToString()

    self._storage_writer.AddEventData(event_data)

    identifier = event_data.GetIdentifier()
    self._event_data_identifier_mappings[lookup_key] = identifier

  def _AddEventDataStream(self, event_data_stream, serialized_data=None):
    """Adds an event data stream.

    Args:
      event_data_stream (EventDataStream): event data stream.
      serialized_data (bytes): serialized form of the event data stream.
    """
    identifier = event_data_stream.GetIdentifier()
    lookup_key = identifier.CopyToString()

    self._storage_writer.AddEventDataStream(event_data_stream)

    identifier = event_data_stream.GetIdentifier()
    self._event_data_stream_identifier_mappings[lookup_key] = identifier

  def _AddEventSource(self, event_source, serialized_data=None):
    """Adds an event source.

    Args:
      event_source (EventSource): event source.
      serialized_data (Optional[bytes]): serialized form of the event source.
    """
    self._storage_writer.AddEventSource(event_source)

  def _AddEventTag(self, event_tag, serialized_data=None):
    """Adds an event tag.

    Args:
      event_tag (EventTag): event tag.
      serialized_data (Optional[bytes]): serialized form of the event tag.
    """
    event_identifier = event_tag.GetEventIdentifier()
    lookup_key = event_identifier.CopyToString()

    event_identifier = self._event_identifier_mappings.get(lookup_key, None)

    if not event_identifier:
      event_tag_identifier = event_tag.GetIdentifier()
      event_tag_identifier = event_tag_identifier.CopyToString()

      # TODO: store this as an extraction warning so this is preserved
      # in the storage file.
      logger.error((
          'Unable to merge event tag attribute container: {0:s} since '
          'corresponding event: {1:s} could not be found.').format(
              event_tag_identifier, lookup_key))
      return

    event_tag.SetEventDataIdentifier(event_identifier)

    self._storage_writer.AddEventTag(event_tag)

  def _AddWarning(self, warning, serialized_data=None):
    """Adds a warning.

    Args:
      warning (ExtractionWarning): warning.
      serialized_data (Optional[bytes]): serialized form of the warning.
    """
    self._storage_writer.AddWarning(warning)

  def _Close(self):
    """Closes the task storage after reading."""
    self._task_storage_file.Close()
    self._task_storage_file = None

  def _Open(self):
    """Opens the task storage for reading."""
    self._task_storage_file = sqlite_file.SQLiteStorageFile(
        storage_type=definitions.STORAGE_TYPE_TASK)
    self._task_storage_file.Open(self._path)

    table_names = self._task_storage_file.GetTableNames()

    self._container_types = [
        table_name for table_name in self._CONTAINER_TYPES
        if table_name in table_names]

  def MergeAttributeContainers(
      self, callback=None, maximum_number_of_containers=0):
    """Reads attribute containers from a task storage file into the writer.

    Args:
      callback (function[StorageWriter, AttributeContainer]): function to call
          after each attribute container is deserialized.
      maximum_number_of_containers (Optional[int]): maximum number of
          containers to merge, where 0 represent no limit.

    Returns:
      bool: True if the entire task storage file has been merged.

    Raises:
      RuntimeError: if the add method for the active attribute container
          type is missing.
      OSError: if the task storage file cannot be deleted.
      ValueError: if the maximum number of containers is a negative value.
    """
    if maximum_number_of_containers < 0:
      raise ValueError('Invalid maximum number of containers')

    if not self._task_storage_file:
      self._Open()

    number_of_containers = 0
    while self._active_container_generator or self._container_types:
      if not self._active_container_generator:
        self._active_container_type = self._container_types.pop(0)

        self._active_container_generator = (
            self._task_storage_file.GetStoredAttributeContainerGenerator(
                self._active_container_type))

        self._add_active_container_method = (
            self._add_container_type_methods.get(self._active_container_type))

      try:
        attribute_container = next(self._active_container_generator)
      except StopIteration:
        self._active_container_generator = None
        continue

      if callback:
        callback(self._storage_writer, attribute_container)

      self._add_active_container_method(attribute_container)

      number_of_containers += 1

      if (maximum_number_of_containers != 0 and
          number_of_containers >= maximum_number_of_containers):
        return False

    self._Close()

    os.remove(self._path)

    return True
