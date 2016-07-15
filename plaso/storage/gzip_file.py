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
    self._analysis_reports = []
    self._errors = []
    self._event_sources = []
    self._event_tags = []
    self._events = []
    self._gzip_file = None
    self._session_completion = None
    self._session_start = None
    self._task_completion = None
    self._task_start = None

  def _OpenRead(self):
    """Opens the storage file for reading."""
    for line in self._gzip_file.readlines():
      attribute_container = self._DeserializeAttributeContainer(
          line, u'attribute_container')

      if attribute_container.CONTAINER_TYPE == u'analysis_report':
        self._analysis_reports.append(attribute_container)

      elif attribute_container.CONTAINER_TYPE == u'event':
        self._events.append(attribute_container)

      elif attribute_container.CONTAINER_TYPE == u'event_source':
        self._event_sources.append(attribute_container)

      elif attribute_container.CONTAINER_TYPE == u'event_tag':
        self._event_tags.append(attribute_container)

      elif attribute_container.CONTAINER_TYPE == u'extraction_error':
        self._errors.append(attribute_container)

      elif attribute_container.CONTAINER_TYPE == u'task_start':
        self._task_start = attribute_container

      elif attribute_container.CONTAINER_TYPE == u'task_start':
        self._task_start = attribute_container

  def AddAnalysisReport(self, analysis_report):
    """Adds an analysis report.

    Args:
      analysis_report (AnalysisReport): analysis report.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage file.')

    if self._read_only:
      raise IOError(u'Unable to write to read-only storage file.')

    report_data = self._SerializeAttributeContainer(analysis_report)
    self._gzip_file.write(report_data)
    self._gzip_file.write(b'\n')

  def AddError(self, error):
    """Adds an error.

    Args:
      error (ExtractionError): error.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage file.')

    if self._read_only:
      raise IOError(u'Unable to write to read-only storage file.')

    error_data = self._SerializeAttributeContainer(error)
    self._gzip_file.write(error_data)
    self._gzip_file.write(b'\n')

  def AddEvent(self, event):
    """Adds an event.

    Args:
      event (EventObject): event.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage file.')

    if self._read_only:
      raise IOError(u'Unable to write to read-only storage file.')

    event_data = self._SerializeAttributeContainer(event)
    self._gzip_file.write(event_data)
    self._gzip_file.write(b'\n')

  def AddEventSource(self, event_source):
    """Adds an event source.

    Args:
      event_source (EventSource): event source.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage file.')

    if self._read_only:
      raise IOError(u'Unable to write to read-only storage file.')

    event_source_data = self._SerializeAttributeContainer(event_source)
    self._gzip_file.write(event_source_data)
    self._gzip_file.write(b'\n')

  def AddEventTag(self, event_tag):
    """Adds an event tag.

    Args:
      event_tag (EventTag): event tag.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage file.')

    if self._read_only:
      raise IOError(u'Unable to write to read-only storage file.')

    event_tag_data = self._SerializeAttributeContainer(event_tag)
    self._gzip_file.write(event_tag_data)
    self._gzip_file.write(b'\n')

  def Close(self):
    """Closes the storage.

    Raises:
      IOError: if the storage file is already closed.
    """
    if not self._is_open:
      raise IOError(u'Storage file already closed.')

    self._gzip_file.close()
    self._gzip_file = None
    self._is_open = False

  def GetAnalysisReports(self):
    """Retrieves the analysis reports.

    Yields:
      AnalysisReport: analysis report.
    """
    return iter(self._analysis_reports)

  def GetErrors(self):
    """Retrieves the errors.

    Yields:
      ExtractionError: error.
    """
    return iter(self._errors)

  def GetEvents(self, time_range=None):
    """Retrieves the events in increasing chronological order.

    Args:
      time_range (Optional[TimeRange]): time range used to filter events
          that fall in a specific period.

    Returns:
      EventObject: event.
    """
    return iter(self._events)

  def GetEventSources(self):
    """Retrieves the event sources.

    Yields:
      EventSource: event source.
    """
    return iter(self._event_sources)

  def GetEventTags(self):
    """Retrieves the event tags.

    Yields:
      EventTag: event tag.
    """
    return iter(self._event_tags)

  def HasAnalysisReports(self):
    """Determines if a storage contains analysis reports.

    Returns:
      bool: True if the storage contains analysis reports.
    """
    return len(self._analysis_reports) > 0

  def HasErrors(self):
    """Determines if a storage contains extraction errors.

    Returns:
      bool: True if the storage contains extraction errors.
    """
    return len(self._errors) > 0

  def HasEventTags(self):
    """Determines if a storage contains event tags.

    Returns:
      bool: True if the storage contains event tags.
    """
    return len(self._event_tags) > 0

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

    Raises:
      IOError: when the storage file is closed or read-only.
      NotImplementedError: since there is no implementation.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage file.')

    if self._read_only:
      raise IOError(u'Unable to write to read-only storage file.')

    raise NotImplementedError()

  def WriteSessionStart(self, session_start):
    """Writes session start information.

    Args:
      session_start (SessionStart): session start information.

    Raises:
      IOError: when the storage file is closed or read-only.
      NotImplementedError: since there is no implementation.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage file.')

    if self._read_only:
      raise IOError(u'Unable to write to read-only storage file.')

    raise NotImplementedError()

  def WriteTaskCompletion(self, task_completion):
    """Writes task completion information.

    Args:
      task_completion (TaskCompletion): task completion information.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage file.')

    if self._read_only:
      raise IOError(u'Unable to write to read-only storage file.')

    task_completion_data = self._SerializeAttributeContainer(task_completion)
    self._gzip_file.write(task_completion_data)
    self._gzip_file.write(b'\n')

  def WriteTaskStart(self, task_start):
    """Writes task start information.

    Args:
      task_start (TaskStart): task start information.

    Raises:
      IOError: when the storage file is closed or read-only.
    """
    if not self._is_open:
      raise IOError(u'Unable to write to closed storage file.')

    if self._read_only:
      raise IOError(u'Unable to write to read-only storage file.')

    task_start_data = self._SerializeAttributeContainer(task_start)
    self._gzip_file.write(task_start_data)
    self._gzip_file.write(b'\n')


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
