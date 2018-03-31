# -*- coding: utf-8 -*-
"""Merge reader for SQLite storage files."""

from __future__ import unicode_literals

import os
import sqlite3
import zlib

from plaso.containers import errors
from plaso.containers import event_sources
from plaso.containers import events
from plaso.containers import reports
from plaso.containers import tasks
from plaso.lib import definitions
from plaso.storage import identifiers
from plaso.storage import interface


class SQLiteStorageMergeReader(interface.StorageFileMergeReader):
  """SQLite-based storage file reader for merging."""

  _CONTAINER_TYPE_ANALYSIS_REPORT = reports.AnalysisReport.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT = events.EventObject.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_DATA = events.EventData.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_SOURCE = event_sources.EventSource.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_TAG = events.EventTag.CONTAINER_TYPE
  _CONTAINER_TYPE_EXTRACTION_ERROR = errors.ExtractionError.CONTAINER_TYPE
  _CONTAINER_TYPE_TASK_COMPLETION = tasks.TaskCompletion.CONTAINER_TYPE
  _CONTAINER_TYPE_TASK_START = tasks.TaskStart.CONTAINER_TYPE

  _CONTAINER_TYPES = (
      _CONTAINER_TYPE_EVENT_SOURCE,
      _CONTAINER_TYPE_EVENT_DATA,
      _CONTAINER_TYPE_EVENT,
      _CONTAINER_TYPE_EVENT_TAG,
      _CONTAINER_TYPE_EXTRACTION_ERROR,
      _CONTAINER_TYPE_ANALYSIS_REPORT)

  _TABLE_NAMES_QUERY = (
      'SELECT name FROM sqlite_master WHERE type = "table"')

  def __init__(self, storage_writer, path):
    """Initializes a storage merge reader.

    Args:
      storage_writer (StorageWriter): storage writer.
      path (str): path to the input file.

    Raises:
      IOError: if the input file cannot be opened.
    """
    super(SQLiteStorageMergeReader, self).__init__(storage_writer)
    self._active_container_type = None
    self._active_cursor = None
    self._compression_format = definitions.COMPRESSION_FORMAT_NONE
    self._connection = None
    self._container_types = None
    self._cursor = None
    self._event_data_identifier_mappings = {}
    self._path = path

  def _AddAttributeContainer(self, attribute_container):
    """Adds a single attribute container to the storage writer.

    Args:
      attribute_container (AttributeContainer): container

    Raises:
      RuntimeError: if the attribute container type is not supported.
    """
    container_type = attribute_container.CONTAINER_TYPE
    if container_type == self._CONTAINER_TYPE_EVENT_SOURCE:
      self._storage_writer.AddEventSource(attribute_container)

    elif container_type == self._CONTAINER_TYPE_EVENT_DATA:
      identifier = attribute_container.GetIdentifier()
      lookup_key = identifier.CopyToString()

      self._storage_writer.AddEventData(attribute_container)

      identifier = attribute_container.GetIdentifier()
      self._event_data_identifier_mappings[lookup_key] = identifier

    elif container_type == self._CONTAINER_TYPE_EVENT:
      if hasattr(attribute_container, 'event_data_row_identifier'):
        event_data_identifier = identifiers.SQLTableIdentifier(
            self._CONTAINER_TYPE_EVENT_DATA,
            attribute_container.event_data_row_identifier)
        lookup_key = event_data_identifier.CopyToString()

        event_data_identifier = self._event_data_identifier_mappings[lookup_key]
        attribute_container.SetEventDataIdentifier(event_data_identifier)

      # TODO: add event identifier mappings for event tags.

      self._storage_writer.AddEvent(attribute_container)

    elif container_type == self._CONTAINER_TYPE_EVENT_TAG:
      self._storage_writer.AddEventTag(attribute_container)

    elif container_type == self._CONTAINER_TYPE_EXTRACTION_ERROR:
      self._storage_writer.AddError(attribute_container)

    elif container_type == self._CONTAINER_TYPE_ANALYSIS_REPORT:
      self._storage_writer.AddAnalysisReport(attribute_container)

    elif container_type not in (
        self._CONTAINER_TYPE_TASK_COMPLETION, self._CONTAINER_TYPE_TASK_START):
      raise RuntimeError('Unsupported container type: {0:s}'.format(
          container_type))

  def _ReadStorageMetadata(self):
    """Reads the storage metadata.

    Returns:
      bool: True if the storage metadata was read.
    """
    query = 'SELECT key, value FROM metadata'
    self._cursor.execute(query)

    metadata_values = {row[0]: row[1] for row in self._cursor.fetchall()}

    self._compression_format = metadata_values['compression_format']

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
      OSError: if the task storage file cannot be deleted.
    """
    if not self._cursor:
      self._connection = sqlite3.connect(
          self._path,
          detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
      self._cursor = self._connection.cursor()

      self._ReadStorageMetadata()

      self._cursor.execute(self._TABLE_NAMES_QUERY)
      table_names = [row[0] for row in self._cursor.fetchall()]

      # Remove container types not stored in the storage file but keep
      # the container types list in order.
      self._container_types = list(self._CONTAINER_TYPES)
      for name in set(self._CONTAINER_TYPES).difference(table_names):
        self._container_types.remove(name)

    number_of_containers = 0
    while self._active_cursor or self._container_types:
      if not self._active_cursor:
        self._active_container_type = self._container_types.pop(0)

        query = 'SELECT _identifier, _data FROM {0:s}'.format(
            self._active_container_type)
        self._cursor.execute(query)

        self._active_cursor = self._cursor

      if maximum_number_of_containers > 0:
        number_of_rows = maximum_number_of_containers - number_of_containers
        rows = self._active_cursor.fetchmany(size=number_of_rows)
      else:
        rows = self._active_cursor.fetchall()

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

        attribute_container = self._DeserializeAttributeContainer(
            self._active_container_type, serialized_data)
        attribute_container.SetIdentifier(identifier)

        if self._active_container_type == self._CONTAINER_TYPE_EVENT_TAG:
          event_identifier = identifiers.SQLTableIdentifier(
              self._CONTAINER_TYPE_EVENT,
              attribute_container.event_row_identifier)
          attribute_container.SetEventIdentifier(event_identifier)

          del attribute_container.event_row_identifier

        if callback:
          callback(self._storage_writer, attribute_container)

        self._AddAttributeContainer(attribute_container)

        number_of_containers += 1

      if (maximum_number_of_containers > 0 and
          number_of_containers >= maximum_number_of_containers):
        return False

    self._connection.close()
    self._connection = None
    self._cursor = None

    os.remove(self._path)

    return True
