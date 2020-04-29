# -*- coding: utf-8 -*-
"""Merge reader for SQLite storage files."""

from __future__ import unicode_literals

import os
import sqlite3
import zlib

from plaso.containers import event_sources
from plaso.containers import events
from plaso.containers import manager as containers_manager
from plaso.containers import reports
from plaso.containers import tasks
from plaso.containers import warnings
from plaso.lib import definitions
from plaso.storage import interface
from plaso.storage import identifiers
from plaso.storage import logger


class SQLiteStorageMergeReader(interface.StorageMergeReader):
  """SQLite-based storage file reader for merging."""

  _ATTRIBUTE_CONTAINERS_MANAGER = (
      containers_manager.AttributeContainersManager)

  _CONTAINER_TYPE_ANALYSIS_REPORT = reports.AnalysisReport.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT = events.EventObject.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_DATA = events.EventData.CONTAINER_TYPE
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
      _CONTAINER_TYPE_EVENT_DATA,
      _CONTAINER_TYPE_EVENT,
      _CONTAINER_TYPE_EVENT_TAG,
      _CONTAINER_TYPE_EXTRACTION_WARNING,
      _CONTAINER_TYPE_ANALYSIS_REPORT)

  _ADD_CONTAINER_TYPE_METHODS = {
      _CONTAINER_TYPE_ANALYSIS_REPORT: '_AddAnalysisReport',
      _CONTAINER_TYPE_EVENT: '_AddEvent',
      _CONTAINER_TYPE_EVENT_DATA: '_AddEventData',
      _CONTAINER_TYPE_EVENT_SOURCE: '_AddEventSource',
      _CONTAINER_TYPE_EVENT_TAG: '_AddEventTag',
      _CONTAINER_TYPE_EXTRACTION_WARNING: '_AddWarning',
  }

  _TABLE_NAMES_QUERY = (
      'SELECT name FROM sqlite_master WHERE type = "table"')

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
    self._active_container_type = None
    self._active_cursor = None
    self._add_active_container_method = None
    self._add_container_type_methods = {}
    self._compression_format = definitions.COMPRESSION_FORMAT_NONE
    self._connection = None
    self._container_types = None
    self._cursor = None
    self._deserialization_errors = []
    self._event_data_identifier_mappings = {}
    self._path = path

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

  def _AddAnalysisReport(self, analysis_report, serialized_data=None):
    """Adds an analysis report.

    Args:
      analysis_report (AnalysisReport): analysis report.
      serialized_data (Optional[bytes]): serialized form of the analysis report.
    """
    self._storage_writer.AddAnalysisReport(
        analysis_report, serialized_data=serialized_data)

  # The serialized form of the event is not used, as this method modifies the
  # event.
  # pylint: disable=unused-argument
  def _AddEvent(self, event, serialized_data=None):
    """Adds an event.

    Args:
      event (EventObject): event.
      serialized_data (Optional[bytes]): serialized form of the event.
    """
    if hasattr(event, 'event_data_row_identifier'):
      event_data_identifier = identifiers.SQLTableIdentifier(
          self._CONTAINER_TYPE_EVENT_DATA,
          event.event_data_row_identifier)
      lookup_key = event_data_identifier.CopyToString()

      event_data_identifier = self._event_data_identifier_mappings.get(
          lookup_key, None)

      if not event_data_identifier:
        event_identifier = event.GetIdentifier()
        event_identifier = event_identifier.CopyToString()

        if lookup_key in self._deserialization_errors:
          reason = 'deserialized'
        else:
          reason = 'found'

        # TODO: store this as an extraction warning so this is preserved
        # in the storage file.
        logger.error((
            'Unable to merge event attribute container: {0:s} since '
            'corresponding event data: {1:s} could not be {2:s}.').format(
                event_identifier, lookup_key, reason))
        return

      event.SetEventDataIdentifier(event_data_identifier)

    # TODO: add event identifier mappings for event tags.

    self._storage_writer.AddEvent(event)

  def _AddEventData(self, event_data, serialized_data=None):
    """Adds event data.

    Args:
      event_data (EventData): event data.
      serialized_data (bytes): serialized form of the event data.
    """
    identifier = event_data.GetIdentifier()
    lookup_key = identifier.CopyToString()

    self._storage_writer.AddEventData(
        event_data, serialized_data=serialized_data)

    identifier = event_data.GetIdentifier()
    self._event_data_identifier_mappings[lookup_key] = identifier

  def _AddEventSource(self, event_source, serialized_data=None):
    """Adds an event source.

    Args:
      event_source (EventSource): event source.
      serialized_data (Optional[bytes]): serialized form of the event source.
    """
    self._storage_writer.AddEventSource(
        event_source, serialized_data=serialized_data)

  def _AddEventTag(self, event_tag, serialized_data=None):
    """Adds an event tag.

    Args:
      event_tag (EventTag): event tag.
      serialized_data (Optional[bytes]): serialized form of the event tag.
    """
    self._storage_writer.AddEventTag(event_tag, serialized_data=serialized_data)

  def _AddWarning(self, warning, serialized_data=None):
    """Adds a warning.

    Args:
      warning (ExtractionWarning): warning.
      serialized_data (Optional[bytes]): serialized form of the warning.
    """
    self._storage_writer.AddWarning(warning, serialized_data=serialized_data)

  def _Close(self):
    """Closes the task storage after reading."""
    self._connection.close()
    self._connection = None
    self._cursor = None

  def _GetContainerTypes(self):
    """Retrieves the container types to merge.

    Container types not defined in _CONTAINER_TYPES are ignored and not merged.

    Specific container types reference other container types, such
    as event referencing event data. The names are ordered to ensure the
    attribute containers are merged in the correct order.

    Returns:
      list[str]: names of the container types to merge.
    """
    self._cursor.execute(self._TABLE_NAMES_QUERY)
    table_names = [row[0] for row in self._cursor.fetchall()]

    return [
        table_name for table_name in self._CONTAINER_TYPES
        if table_name in table_names]

  def _Open(self):
    """Opens the task storage for reading."""
    self._connection = sqlite3.connect(
        self._path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    self._cursor = self._connection.cursor()

  def _ReadStorageMetadata(self):
    """Reads the task storage metadata."""
    query = 'SELECT key, value FROM metadata'
    self._cursor.execute(query)

    metadata_values = {row[0]: row[1] for row in self._cursor.fetchall()}

    self._compression_format = metadata_values['compression_format']

  def _PrepareForNextContainerType(self):
    """Prepares for the next container type.

    This method prepares the task storage for merging the next container type.
    It sets the active container type, its add method and active cursor
    accordingly.
    """
    self._active_container_type = self._container_types.pop(0)

    self._add_active_container_method = self._add_container_type_methods.get(
        self._active_container_type)

    query = 'SELECT _identifier, _data FROM {0:s}'.format(
        self._active_container_type)
    self._cursor.execute(query)

    self._active_cursor = self._cursor

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

    if not self._cursor:
      self._Open()
      self._ReadStorageMetadata()
      self._container_types = self._GetContainerTypes()

    self._deserialization_errors = []

    number_of_containers = 0
    while self._active_cursor or self._container_types:
      if not self._active_cursor:
        self._PrepareForNextContainerType()

      if maximum_number_of_containers == 0:
        rows = self._active_cursor.fetchall()
      else:
        number_of_rows = maximum_number_of_containers - number_of_containers
        rows = self._active_cursor.fetchmany(size=number_of_rows)

      if not rows:
        self._active_cursor = None
        continue

      for row in rows:
        identifier = identifiers.SQLTableIdentifier(
            self._active_container_type, row[0])

        if self._compression_format == definitions.COMPRESSION_FORMAT_ZLIB:
          serialized_data = zlib.decompress(row[1])
        else:
          serialized_data = row[1]

        try:
          attribute_container = self._DeserializeAttributeContainer(
              self._active_container_type, serialized_data)
        except IOError as exception:
          # TODO: store this as an extraction warning so this is preserved
          # in the storage file.
          logger.error((
              'Unable to deserialize attribute container with error: '
              '{0!s}').format(exception))

          identifier = identifier.CopyToString()
          self._deserialization_errors.append(identifier)
          continue

        attribute_container.SetIdentifier(identifier)

        if self._active_container_type == self._CONTAINER_TYPE_EVENT_TAG:
          event_identifier = identifiers.SQLTableIdentifier(
              self._CONTAINER_TYPE_EVENT,
              attribute_container.event_row_identifier)
          attribute_container.SetEventIdentifier(event_identifier)

          del attribute_container.event_row_identifier

        if callback:
          callback(self._storage_writer, attribute_container)

        self._add_active_container_method(
            attribute_container, serialized_data=serialized_data)

        number_of_containers += 1

      if (maximum_number_of_containers != 0 and
          number_of_containers >= maximum_number_of_containers):
        return False

    self._Close()

    os.remove(self._path)

    return True
