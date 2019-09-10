# -*- coding: utf-8 -*-
"""The parser mediator."""

from __future__ import unicode_literals

import copy
import os
import time

from dfvfs.lib import definitions as dfvfs_definitions

from plaso.containers import warnings
from plaso.engine import path_helper
from plaso.engine import profilers
from plaso.lib import errors
from plaso.lib import py2to3
from plaso.lib import timelib
from plaso.parsers import logger


class ParserMediator(object):
  """Parser mediator.

  Attributes:
    collection_filters_helper (CollectionFiltersHelper): collection filters
        helper.
    last_activity_timestamp (int): timestamp received that indicates the last
        time activity was observed. The last activity timestamp is updated
        when the mediator produces an attribute container, such as an event
        source. This timestamp is used by the multi processing worker process
        to indicate the last time the worker was known to be active. This
        information is then used by the foreman to detect workers that are
        not responding (stalled).
  """
  _INT64_MIN = -1 << 63
  _INT64_MAX = (1 << 63) - 1

  def __init__(
      self, storage_writer, knowledge_base, collection_filters_helper=None,
      preferred_year=None, resolver_context=None, temporary_directory=None):
    """Initializes a parser mediator.

    Args:
      storage_writer (StorageWriter): storage writer.
      knowledge_base (KnowledgeBase): contains information from the source
          data needed for parsing.
      collection_filters_helper (Optional[CollectionFiltersHelper]): collection
          filters helper.
      preferred_year (Optional[int]): preferred year.
      resolver_context (Optional[dfvfs.Context]): resolver context.
      temporary_directory (Optional[str]): path of the directory for temporary
          files.
    """
    super(ParserMediator, self).__init__()
    self._abort = False
    self._cpu_time_profiler = None
    self._extra_event_attributes = {}
    self._file_entry = None
    self._knowledge_base = knowledge_base
    self._last_event_data_hash = None
    self._last_event_data_identifier = None
    self._memory_profiler = None
    self._mount_path = None
    self._number_of_event_sources = 0
    self._number_of_events = 0
    self._number_of_warnings = 0
    self._parser_chain_components = []
    self._preferred_year = preferred_year
    self._process_information = None
    self._resolver_context = resolver_context
    self._storage_writer = storage_writer
    self._temporary_directory = temporary_directory
    self._text_prepend = None

    self.collection_filters_helper = collection_filters_helper
    self.last_activity_timestamp = 0.0

  @property
  def abort(self):
    """bool: True if parsing should be aborted."""
    return self._abort

  @property
  def codepage(self):
    """str: codepage."""
    return self._knowledge_base.codepage

  @property
  def hostname(self):
    """str: hostname."""
    return self._knowledge_base.hostname

  @property
  def knowledge_base(self):
    """KnowledgeBase: knowledge base."""
    return self._knowledge_base

  @property
  def number_of_produced_event_sources(self):
    """int: number of produced event sources."""
    return self._number_of_event_sources

  @property
  def number_of_produced_events(self):
    """int: number of produced events."""
    return self._number_of_events

  @property
  def number_of_produced_warnings(self):
    """int: number of produced warnings."""
    return self._number_of_warnings

  @property
  def operating_system(self):
    """str: operating system or None if not set."""
    return self._knowledge_base.GetValue('operating_system')

  @property
  def resolver_context(self):
    """dfvfs.Context: resolver context."""
    return self._resolver_context

  @property
  def temporary_directory(self):
    """str: path of the directory for temporary files."""
    return self._temporary_directory

  @property
  def timezone(self):
    """datetime.tzinfo: timezone."""
    return self._knowledge_base.timezone

  @property
  def year(self):
    """int: year."""
    return self._knowledge_base.year

  def _GetEarliestYearFromFileEntry(self):
    """Retrieves the year from the file entry date and time values.

    This function uses the creation time if available otherwise the change
    time (metadata last modification time) is used.

    Returns:
      int: year of the file entry or None.
    """
    file_entry = self.GetFileEntry()
    if not file_entry:
      return None

    stat_object = file_entry.GetStat()

    posix_time = getattr(stat_object, 'crtime', None)
    if posix_time is None:
      posix_time = getattr(stat_object, 'ctime', None)

    # Gzip files don't store the creation or metadata modification times,
    # but the modification time stored in the file is a good proxy.
    if file_entry.TYPE_INDICATOR == dfvfs_definitions.TYPE_INDICATOR_GZIP:
      posix_time = getattr(stat_object, 'mtime', None)

    if posix_time is None:
      logger.warning(
          'Unable to determine earliest year from file stat information.')
      return None

    try:
      year = timelib.GetYearFromPosixTime(
          posix_time, timezone=self._knowledge_base.timezone)
      return year
    except ValueError as exception:
      logger.error((
          'Unable to determine earliest year from file stat information with '
          'error: {0!s}').format(exception))
      return None

  def _GetInode(self, inode_value):
    """Retrieves the inode from the inode value.

    Args:
      inode_value (int|str): inode, such as 1 or '27-128-1'.

    Returns:
      int: inode or -1 if the inode value cannot be converted to an integer.
    """
    if isinstance(inode_value, py2to3.INTEGER_TYPES):
      return inode_value

    if isinstance(inode_value, float):
      return int(inode_value)

    if not isinstance(inode_value, py2to3.STRING_TYPES):
      return -1

    if b'-' in inode_value:
      inode_value, _, _ = inode_value.partition(b'-')

    try:
      return int(inode_value, 10)
    except ValueError:
      return -1

  def _GetLatestYearFromFileEntry(self):
    """Retrieves the maximum (highest value) year from the file entry.

    This function uses the modification time if available otherwise the change
    time (metadata last modification time) is used.

    Returns:
      int: year of the file entry or None.
    """
    file_entry = self.GetFileEntry()
    if not file_entry:
      return None

    stat_object = file_entry.GetStat()

    posix_time = getattr(stat_object, 'mtime', None)
    if posix_time is None:
      posix_time = getattr(stat_object, 'ctime', None)

    if posix_time is None:
      logger.warning(
          'Unable to determine modification year from file stat information.')
      return None

    try:
      year = timelib.GetYearFromPosixTime(
          posix_time, timezone=self._knowledge_base.timezone)
      return year
    except ValueError as exception:
      logger.error((
          'Unable to determine creation year from file stat '
          'information with error: {0!s}').format(exception))
      return None

  def AddEventAttribute(self, attribute_name, attribute_value):
    """Adds an attribute that will be set on all events produced.

    Setting attributes using this method will cause events produced via this
    mediator to have an attribute with the provided name set with the
    provided value.

    Args:
      attribute_name (str): name of the attribute to add.
      attribute_value (str): value of the attribute to add.

    Raises:
      KeyError: if the event attribute is already set.
    """
    if attribute_name in self._extra_event_attributes:
      raise KeyError('Event attribute {0:s} already set'.format(
          attribute_name))

    self._extra_event_attributes[attribute_name] = attribute_value

  def AppendToParserChain(self, plugin_or_parser):
    """Adds a parser or parser plugin to the parser chain.

    Args:
      plugin_or_parser (BaseParser): parser or parser plugin.
    """
    self._parser_chain_components.append(plugin_or_parser.NAME)

  def ClearEventAttributes(self):
    """Clears the extra event attributes."""
    self._extra_event_attributes = {}

  def ClearParserChain(self):
    """Clears the parser chain."""
    self._parser_chain_components = []

  def GetDisplayName(self, file_entry=None):
    """Retrieves the display name for a file entry.

    Args:
      file_entry (Optional[dfvfs.FileEntry]): file entry object, where None
          will return the display name of self._file_entry.

    Returns:
      str: human readable string that describes the path to the file entry.

    Raises:
      ValueError: if the file entry is missing.
    """
    if file_entry is None:
      file_entry = self._file_entry

    if file_entry is None:
      raise ValueError('Missing file entry')

    path_spec = getattr(file_entry, 'path_spec', None)

    relative_path = path_helper.PathHelper.GetRelativePathForPathSpec(
        path_spec, mount_path=self._mount_path)
    if not relative_path:
      return file_entry.name

    return self.GetDisplayNameForPathSpec(path_spec)

  def GetDisplayNameForPathSpec(self, path_spec):
    """Retrieves the display name for a path specification.

    Args:
      path_spec (dfvfs.PathSpec): path specification.

    Returns:
      str: human readable version of the path specification.
    """
    return path_helper.PathHelper.GetDisplayNameForPathSpec(
        path_spec, mount_path=self._mount_path, text_prepend=self._text_prepend)

  def GetEstimatedYear(self):
    """Retrieves an estimate of the year.

    This function determines the year in the following manner:
    * determine if the user provided a preferred year;
    * determine if knowledge base defines a year derived from preprocessing;
    * determine the year based on the file entry metadata;
    * default to the current year;

    Returns:
      int: estimated year.
    """
    # TODO: improve this method to get a more reliable estimate.
    # Preserve the year-less date and sort this out in the psort phase.
    if self._preferred_year:
      return self._preferred_year

    if self._knowledge_base.year:
      return self._knowledge_base.year

    # TODO: Find a decent way to actually calculate the correct year
    # instead of relying on stats object.
    year = self._GetEarliestYearFromFileEntry()
    if not year:
      year = self._GetLatestYearFromFileEntry()

    if not year:
      year = timelib.GetCurrentYear()
    return year

  def GetFileEntry(self):
    """Retrieves the active file entry.

    Returns:
      dfvfs.FileEntry: file entry.
    """
    return self._file_entry

  def GetFilename(self):
    """Retrieves the name of the active file entry.

    Returns:
      str: name of the active file entry or None.
    """
    if not self._file_entry:
      return None

    data_stream = getattr(self._file_entry.path_spec, 'data_stream', None)
    if data_stream:
      return '{0:s}:{1:s}'.format(self._file_entry.name, data_stream)

    return self._file_entry.name

  def GetLatestYear(self):
    """Retrieves the latest (newest) year for an event from a file.

    This function tries to determine the year based on the file entry metadata,
    if that fails the current year is used.

    Returns:
      int: year of the file entry or the current year.
    """
    year = self._GetLatestYearFromFileEntry()
    if not year:
      year = timelib.GetCurrentYear()

    return year

  def GetParserChain(self):
    """Retrieves the current parser chain.

    Returns:
      str: parser chain.
    """
    return '/'.join(self._parser_chain_components)

  def PopFromParserChain(self):
    """Removes the last added parser or parser plugin from the parser chain."""
    self._parser_chain_components.pop()

  def ProcessEventData(
      self, event_data, parser_chain=None, file_entry=None, query=None):
    """Processes event data before it written to the storage.

    Args:
      event_data (EventData): event data.
      parser_chain (Optional[str]): parsing chain up to this point.
      file_entry (Optional[dfvfs.FileEntry]): file entry, where None will
          use the current file entry set in the mediator.
      query (Optional[str]): query that was used to obtain the event data.

    Raises:
      KeyError: if there's an attempt to add a duplicate attribute value to the
          event data.
    """
    # TODO: rename this to event_data.parser_chain or equivalent.
    if not getattr(event_data, 'parser', None) and parser_chain:
      event_data.parser = parser_chain

    # TODO: deprecate text_prepend in favor of an event tag.
    if not getattr(event_data, 'text_prepend', None) and self._text_prepend:
      event_data.text_prepend = self._text_prepend

    if file_entry is None:
      file_entry = self._file_entry

    display_name = None
    if file_entry:
      event_data.pathspec = file_entry.path_spec

      if not getattr(event_data, 'filename', None):
        path_spec = getattr(file_entry, 'path_spec', None)
        event_data.filename = path_helper.PathHelper.GetRelativePathForPathSpec(
            path_spec, mount_path=self._mount_path)

      if not display_name:
        # TODO: dfVFS refactor: move display name to output since the path
        # specification contains the full information.
        display_name = self.GetDisplayName(file_entry)

      stat_object = file_entry.GetStat()
      inode_value = getattr(stat_object, 'ino', None)
      if getattr(event_data, 'inode', None) is None and inode_value is not None:
        event_data.inode = self._GetInode(inode_value)

    if not getattr(event_data, 'display_name', None) and display_name:
      event_data.display_name = display_name

    if not getattr(event_data, 'hostname', None) and self.hostname:
      event_data.hostname = self.hostname

    if not getattr(event_data, 'username', None):
      user_sid = getattr(event_data, 'user_sid', None)
      username = self._knowledge_base.GetUsernameByIdentifier(user_sid)
      if username:
        event_data.username = username

    if not getattr(event_data, 'query', None) and query:
      event_data.query = query

    for attribute, value in iter(self._extra_event_attributes.items()):
      if hasattr(event_data, attribute):
        raise KeyError('Event already has a value for {0:s}'.format(attribute))

      setattr(event_data, attribute, value)

  def ProduceEventSource(self, event_source):
    """Produces an event source.

    Args:
      event_source (EventSource): an event source.

    Raises:
      RuntimeError: when storage writer is not set.
    """
    if not self._storage_writer:
      raise RuntimeError('Storage writer not set.')

    self._storage_writer.AddEventSource(event_source)
    self._number_of_event_sources += 1

    self.last_activity_timestamp = time.time()

  def ProduceEventWithEventData(self, event, event_data):
    """Produces an event.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.

    Raises:
      InvalidEvent: if the event timestamp value is not set or out of bounds.
    """
    if event.timestamp is None:
      raise errors.InvalidEvent('Event timestamp value not set.')

    if event.timestamp < self._INT64_MIN or event.timestamp > self._INT64_MAX:
      raise errors.InvalidEvent('Event timestamp value out of bounds.')

    event_data_hash = event_data.GetAttributeValuesHash()
    if event_data_hash != self._last_event_data_hash:
      # Make a copy of the event data before adding additional values.
      event_data = copy.deepcopy(event_data)

      self.ProcessEventData(
          event_data, parser_chain=self.GetParserChain(),
          file_entry=self._file_entry)

      self._storage_writer.AddEventData(event_data)

      self._last_event_data_hash = event_data_hash
      self._last_event_data_identifier = event_data.GetIdentifier()

    if self._last_event_data_identifier:
      event.SetEventDataIdentifier(self._last_event_data_identifier)

    # TODO: remove this after structural fix is in place
    # https://github.com/log2timeline/plaso/issues/1691
    event.parser = self.GetParserChain()

    self._storage_writer.AddEvent(event)
    self._number_of_events += 1

    self.last_activity_timestamp = time.time()

  def ProduceExtractionWarning(self, message, path_spec=None):
    """Produces an extraction warning.

    Args:
      message (str): message of the warning.
      path_spec (Optional[dfvfs.PathSpec]): path specification, where None
          will use the path specification of current file entry set in
          the mediator.

    Raises:
      RuntimeError: when storage writer is not set.
    """
    if not self._storage_writer:
      raise RuntimeError('Storage writer not set.')

    if not path_spec and self._file_entry:
      path_spec = self._file_entry.path_spec

    parser_chain = self.GetParserChain()
    warning = warnings.ExtractionWarning(
        message=message, parser_chain=parser_chain, path_spec=path_spec)
    self._storage_writer.AddWarning(warning)
    self._number_of_warnings += 1

    self.last_activity_timestamp = time.time()

  def RemoveEventAttribute(self, attribute_name):
    """Removes an attribute from being set on all events produced.

    Args:
      attribute_name (str): name of the attribute to remove.

    Raises:
      KeyError: if the event attribute is not set.
    """
    if attribute_name not in self._extra_event_attributes:
      raise KeyError('Event attribute: {0:s} not set'.format(attribute_name))

    del self._extra_event_attributes[attribute_name]

  def ResetFileEntry(self):
    """Resets the active file entry."""
    self._file_entry = None

  def SampleMemoryUsage(self, parser_name):
    """Takes a sample of the memory usage for profiling.

    Args:
      parser_name (str): name of the parser.
    """
    if self._memory_profiler:
      used_memory = self._process_information.GetUsedMemory() or 0
      self._memory_profiler.Sample(parser_name, used_memory)

  def SampleStartTiming(self, parser_name):
    """Starts timing a CPU time sample for profiling.

    Args:
      parser_name (str): name of the parser.
    """
    if self._cpu_time_profiler:
      self._cpu_time_profiler.StartTiming(parser_name)

  def SampleStopTiming(self, parser_name):
    """Stops timing a CPU time sample for profiling.

    Args:
      parser_name (str): name of the parser.
    """
    if self._cpu_time_profiler:
      self._cpu_time_profiler.StopTiming(parser_name)

  def SetEventExtractionConfiguration(self, configuration):
    """Sets the event extraction configuration settings.

    Args:
      configuration (EventExtractionConfiguration): event extraction
          configuration.
    """
    self._text_prepend = configuration.text_prepend

  def SetInputSourceConfiguration(self, configuration):
    """Sets the input source configuration settings.

    Args:
      configuration (InputSourceConfiguration): input source configuration.
    """
    mount_path = configuration.mount_path

    # Remove a trailing path separator from the mount path so the relative
    # paths will start with a path separator.
    if mount_path and mount_path.endswith(os.sep):
      mount_path = mount_path[:-1]

    self._mount_path = mount_path

  def SetFileEntry(self, file_entry):
    """Sets the active file entry.

    Args:
      file_entry (dfvfs.FileEntry): file entry.
    """
    self._file_entry = file_entry

  def SetStorageWriter(self, storage_writer):
    """Sets the storage writer.

    Args:
      storage_writer (StorageWriter): storage writer.
    """
    self._storage_writer = storage_writer

    # Reset the last event data information. Each storage file should
    # contain event data for their events.
    self._last_event_data_hash = None
    self._last_event_data_identifier = None

  def SignalAbort(self):
    """Signals the parsers to abort."""
    self._abort = True

  def StartProfiling(self, configuration, identifier, process_information):
    """Starts profiling.

    Args:
      configuration (ProfilingConfiguration): profiling configuration.
      identifier (str): identifier of the profiling session used to create
          the sample filename.
      process_information (ProcessInfo): process information.
    """
    if not configuration:
      return

    if configuration.HaveProfileParsers():
      identifier = '{0:s}-parsers'.format(identifier)

      self._cpu_time_profiler = profilers.CPUTimeProfiler(
          identifier, configuration)
      self._cpu_time_profiler.Start()

      self._memory_profiler = profilers.MemoryProfiler(
          identifier, configuration)
      self._memory_profiler.Start()

    self._process_information = process_information

  def StopProfiling(self):
    """Stops profiling."""
    if self._cpu_time_profiler:
      self._cpu_time_profiler.Stop()
      self._cpu_time_profiler = None

    if self._memory_profiler:
      self._memory_profiler.Stop()
      self._memory_profiler = None

    self._process_information = None
