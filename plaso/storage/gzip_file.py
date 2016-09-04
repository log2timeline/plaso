# -*- coding: utf-8 -*-
"""gzip-based storage.

Only supports task storage at the moment.
"""

import gzip

from plaso.lib import definitions
from plaso.storage import interface


class GZIPStorageFile(interface.BaseFileStorage):
  """Class that defines the gzip-based storage file."""

  # pylint: disable=abstract-method

  _COMPRESSION_LEVEL = 9

  _DATA_BUFFER_SIZE = 16 * 1024 * 1024

  def __init__(self, storage_type=definitions.STORAGE_TYPE_TASK):
    """Initializes a storage.

    Args:
      storage_type (Optional[str]): storage type.

    Raises:
      ValueError: if the storage type is not supported.
    """
    if storage_type != definitions.STORAGE_TYPE_TASK:
      raise ValueError(u'Unsupported storage type: {0:s}.'.format(
          storage_type))

    super(GZIPStorageFile, self).__init__()
    self._attribute_containers = {}
    self._gzip_file = None

  def _AddAttributeContainer(self, attribute_container):
    """Adds an attribute container.

    Args:
      attribute_container (AttributeContainer): attribute container.
    """
    container_type = attribute_container.CONTAINER_TYPE
    if container_type not in self._attribute_containers:
      self._attribute_containers[container_type] = []

    self._attribute_containers[container_type].append(attribute_container)

  def _GetAttributeContainerList(self, container_type):
    """Retrieves an attribute container list.

    Args:
      container_type (str): attribute container type.

    Returns:
      list[AttributeContainer]: attribute container list.
    """
    return self._attribute_containers.get(container_type, [])

  def _OpenRead(self):
    """Opens the storage file for reading."""
    data_buffer = self._gzip_file.read(self._DATA_BUFFER_SIZE)
    while data_buffer:
      while b'\n' in data_buffer:
        line, _, data_buffer = data_buffer.partition(b'\n')
        attribute_container = self._DeserializeAttributeContainer(
            line, u'attribute_container')

        self._AddAttributeContainer(attribute_container)

      additional_data_buffer = self._gzip_file.read(self._DATA_BUFFER_SIZE)
      data_buffer = b''.join([data_buffer, additional_data_buffer])

  def _WriteAttributeContainer(self, attribute_container):
    """Writes an attribute container.

    Args:
      attribute_container (AttributeContainer): attribute container.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage file.')

    if self._read_only:
      raise IOError(u'Unable to write to read-only storage file.')

    attribute_container_data = self._SerializeAttributeContainer(
        attribute_container)
    self._gzip_file.write(attribute_container_data)
    self._gzip_file.write(b'\n')

  def AddAnalysisReport(self, analysis_report):
    """Adds an analysis report.

    Args:
      analysis_report (AnalysisReport): analysis report.
    """
    self._WriteAttributeContainer(analysis_report)

  def AddError(self, error):
    """Adds an error.

    Args:
      error (ExtractionError): error.
    """
    self._WriteAttributeContainer(error)

  def AddEvent(self, event):
    """Adds an event.

    Args:
      event (EventObject): event.
    """
    self._WriteAttributeContainer(event)

  def AddEventSource(self, event_source):
    """Adds an event source.

    Args:
      event_source (EventSource): event source.
    """
    self._WriteAttributeContainer(event_source)

  def AddEventTag(self, event_tag):
    """Adds an event tag.

    Args:
      event_tag (EventTag): event tag.
    """
    self._WriteAttributeContainer(event_tag)

  def Close(self):
    """Closes the storage.

    Raises:
      IOError: if the storage file is already closed.
    """
    if not self._is_open:
      raise IOError(u'Storage file already closed.')

    if self._gzip_file:
      self._gzip_file.close()
      self._gzip_file = None
    self._is_open = False

  def GetAnalysisReports(self):
    """Retrieves the analysis reports.

    Returns:
      generator(AnalysisReport): analysis report generator.
    """
    return iter(self._GetAttributeContainerList(u'analysis_report'))

  def GetErrors(self):
    """Retrieves the errors.

    Returns:
      generator(ExtractionError): error generator.
    """
    return iter(self._GetAttributeContainerList(u'extraction_error'))

  # TODO: time_range is currently not operational, nor that events are
  # returned in chronological order. Fix this.
  def GetEvents(self, time_range=None):
    """Retrieves the events in increasing chronological order.

    Args:
      time_range (Optional[TimeRange]): time range used to filter events
          that fall in a specific period.

    Returns:
      generator(EventObject): event generator.
    """
    return iter(self._GetAttributeContainerList(u'event'))

  def GetEventSources(self):
    """Retrieves the event sources.

    Returns:
      generator(EventSource): event source generator.
    """
    return iter(self._GetAttributeContainerList(u'event_source'))

  def GetEventTags(self):
    """Retrieves the event tags.

    Returns:
      generator(EventTag): event tag generator.
    """
    return iter(self._GetAttributeContainerList(u'event_tag'))

  def HasAnalysisReports(self):
    """Determines if a storage contains analysis reports.

    Returns:
      bool: True if the storage contains analysis reports.
    """
    return len(self._GetAttributeContainerList(u'analysis_report')) > 0

  def HasErrors(self):
    """Determines if a storage contains extraction errors.

    Returns:
      bool: True if the storage contains extraction errors.
    """
    return len(self._GetAttributeContainerList(u'extraction_error')) > 0

  def HasEventTags(self):
    """Determines if a storage contains event tags.

    Returns:
      bool: True if the storage contains event tags.
    """
    return len(self._GetAttributeContainerList(u'event_tags')) > 0

  def Open(self, path=None, read_only=True, **unused_kwargs):
    """Opens the storage.

    Args:
      path (Optional[str]): path of the storage file.
      read_only (Optional[bool]): True if the file should be opened in
          read-only mode.

    Raises:
      IOError: if the storage file is already opened.
      ValueError: if path is missing.
    """
    if self._is_open:
      raise IOError(u'Storage file already opened.')

    if not path:
      raise ValueError(u'Missing path.')

    if read_only:
      access_mode = 'rb'
    else:
      access_mode = 'wb'

    self._gzip_file = gzip.open(path, access_mode, self._COMPRESSION_LEVEL)

    if read_only:
      self._OpenRead()

    self._is_open = True
    self._read_only = read_only

  def WriteSessionCompletion(self, session_completion):
    """Writes session completion information.

    Args:
      session_completion (SessionCompletion): session completion information.
    """
    raise NotImplementedError()

  def WriteSessionStart(self, session_start):
    """Writes session start information.

    Args:
      session_start (SessionStart): session start information.
    """
    raise NotImplementedError()

  def WriteTaskCompletion(self, task_completion):
    """Writes task completion information.

    Args:
      task_completion (TaskCompletion): task completion information.
    """
    self._WriteAttributeContainer(task_completion)

  def WriteTaskStart(self, task_start):
    """Writes task start information.

    Args:
      task_start (TaskStart): task start information.
    """
    self._WriteAttributeContainer(task_start)


class GZIPStorageFileReader(interface.FileStorageReader):
  """Class that implements a gzip-based storage file reader."""

  def __init__(self, path):
    """Initializes a storage reader.

    Args:
      path (str): path to the input file.
    """
    super(GZIPStorageFileReader, self).__init__(path)
    self._storage_file = GZIPStorageFile()
    self._storage_file.Open(path=path)
