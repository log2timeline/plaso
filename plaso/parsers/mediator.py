# -*- coding: utf-8 -*-
"""The parser mediator object."""

import logging
import os

from plaso.containers import errors
from plaso.engine import path_helper
from plaso.lib import py2to3
from plaso.lib import timelib


class ParserMediator(object):
  """Class that implements the parser mediator."""

  def __init__(
      self, storage_writer, knowledge_base, preferred_year=None,
      resolver_context=None, temporary_directory=None):
    """Initializes a parser mediator.

    Args:
      storage_writer (StorageWriter): storage writer.
      knowledge_base (KnowledgeBase): contains information from the source
          data needed for parsing.
      preferred_year (Optional[int]): preferred year.
      resolver_context (Optional[dfvfs.Context]): resolver context.
      temporary_directory (Optional[str]): path of the directory for temporary
          files.
    """
    super(ParserMediator, self).__init__()
    self._abort = False
    self._extra_event_attributes = {}
    self._file_entry = None
    self._knowledge_base = knowledge_base
    self._mount_path = None
    self._number_of_errors = 0
    self._number_of_event_sources = 0
    self._number_of_events = 0
    self._parser_chain_components = []
    self._preferred_year = preferred_year
    self._resolver_context = resolver_context
    self._storage_writer = storage_writer
    self._temporary_directory = temporary_directory
    self._text_prepend = None

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
  def number_of_produced_errors(self):
    """int: number of produced errors."""
    return self._number_of_errors

  @property
  def number_of_produced_event_sources(self):
    """int: number of produced event sources."""
    return self._number_of_event_sources

  @property
  def number_of_produced_events(self):
    """int: number of produced events."""
    return self._number_of_events

  @property
  def platform(self):
    """str: platform."""
    return self._knowledge_base.platform

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
      return

    stat_object = file_entry.GetStat()

    posix_time = getattr(stat_object, u'crtime', None)
    if posix_time is None:
      posix_time = getattr(stat_object, u'ctime', None)

    if posix_time is None:
      logging.warning(
          u'Unable to determine earliest year from file stat information.')
      return

    try:
      year = timelib.GetYearFromPosixTime(
          posix_time, timezone=self._knowledge_base.timezone)
      return year
    except ValueError as exception:
      logging.error((
          u'Unable to determine earliest year from file stat information with '
          u'error: {0:s}').format(exception))
      return

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
      return

    stat_object = file_entry.GetStat()

    posix_time = getattr(stat_object, u'mtime', None)
    if posix_time is None:
      posix_time = getattr(stat_object, u'ctime', None)

    if posix_time is None:
      logging.warning(
          u'Unable to determine modification year from file stat information.')
      return

    try:
      year = timelib.GetYearFromPosixTime(
          posix_time, timezone=self._knowledge_base.timezone)
      return year
    except ValueError as exception:
      logging.error((
          u'Unable to determine creation year from file stat '
          u'information with error: {0:s}').format(exception))
      return

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
      raise KeyError(u'Event attribute {0:s} already set'.format(
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
      raise ValueError(u'Missing file entry')

    path_spec = getattr(file_entry, u'path_spec', None)

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
    * see if the user provided a preferred year;
    * see if knowledge base defines a year e.g. derived from preprocessing;
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
    if year:
      return year

    return timelib.GetCurrentYear()

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
      return

    data_stream = getattr(self._file_entry.path_spec, u'data_stream', None)
    if data_stream:
      return u'{0:s}:{1:s}'.format(self._file_entry.name, data_stream)

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
    return u'/'.join(self._parser_chain_components)

  def PopFromParserChain(self):
    """Removes the last added parser or parser plugin from the parser chain."""
    self._parser_chain_components.pop()

  def ProcessEvent(
      self, event, parser_chain=None, file_entry=None, query=None):
    """Processes an event before it written to the storage.

    Args:
      event (EventObject): event.
      parser_chain (Optional[str]): parsing chain up to this point.
      file_entry (Optional[dfvfs.FileEntry]): file entry, where None will
          use the current file entry set in the mediator.
      query (Optional[str]): query that was used to obtain the event.
    """
    # TODO: rename this to event.parser_chain or equivalent.
    if not getattr(event, u'parser', None) and parser_chain:
      event.parser = parser_chain

    # TODO: deprecate text_prepend in favor of an event tag.
    if not getattr(event, u'text_prepend', None) and self._text_prepend:
      event.text_prepend = self._text_prepend

    if file_entry is None:
      file_entry = self._file_entry

    display_name = None
    if file_entry:
      event.pathspec = file_entry.path_spec

      if not getattr(event, u'filename', None):
        path_spec = getattr(file_entry, u'path_spec', None)
        event.filename = path_helper.PathHelper.GetRelativePathForPathSpec(
            path_spec, mount_path=self._mount_path)

      if not display_name:
        # TODO: dfVFS refactor: move display name to output since the path
        # specification contains the full information.
        display_name = self.GetDisplayName(file_entry)

      stat_object = file_entry.GetStat()
      inode_value = getattr(stat_object, u'ino', None)
      if not hasattr(event, u'inode') and inode_value:
        event.inode = self._GetInode(inode_value)

    if not getattr(event, u'display_name', None) and display_name:
      event.display_name = display_name

    if not getattr(event, u'hostname', None) and self.hostname:
      event.hostname = self.hostname

    if not getattr(event, u'username', None):
      user_sid = getattr(event, u'user_sid', None)
      username = self._knowledge_base.GetUsernameByIdentifier(user_sid)
      if username:
        event.username = username

    if not getattr(event, u'query', None) and query:
      event.query = query

    for attribute, value in iter(self._extra_event_attributes.items()):
      if hasattr(event, attribute):
        raise KeyError(u'Event already has a value for {0:s}'.format(attribute))

      setattr(event, attribute, value)

  def ProduceEvent(self, event, query=None):
    """Produces an event.

    Args:
      event (EventObject): event.
      query (Optional[str]): query that was used to obtain the event.

    Raises:
      RuntimeError: when storage writer is not set.
    """
    if not self._storage_writer:
      raise RuntimeError(u'Storage writer not set.')

    self.ProcessEvent(
        event, parser_chain=self.GetParserChain(),
        file_entry=self._file_entry, query=query)

    self._storage_writer.AddEvent(event)
    self._number_of_events += 1

  def ProduceEvents(self, events, query=None):
    """Produces events.

    Args:
      events (list[EventObject]): event objects.
      query (Optional[str]): query string.
    """
    for event in events:
      self.ProduceEvent(event, query=query)

  def ProduceEventSource(self, event_source):
    """Produces an event source.

    Args:
      event_source (EventSource): an event source.

    Raises:
      RuntimeError: when storage writer is not set.
    """
    if not self._storage_writer:
      raise RuntimeError(u'Storage writer not set.')

    self._storage_writer.AddEventSource(event_source)
    self._number_of_event_sources += 1

  def ProduceEventWithEventData(self, event, event_data):
    """Produces an event.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
    """
    # TODO: store event data and event seperately.
    for attribute_name, attribute_value in event_data.GetAttributes():
      setattr(event, attribute_name, attribute_value)

    self.ProduceEvent(event)

  def ProduceExtractionError(self, message, path_spec=None):
    """Produces an extraction error.

    Args:
      message (str): message of the error.
      path_spec (Optional[dfvfs.PathSpec]): path specification, where None
          will use the path specification of current file entry set in
          the mediator.

    Raises:
      RuntimeError: when storage writer is not set.
    """
    if not self._storage_writer:
      raise RuntimeError(u'Storage writer not set.')

    if not path_spec and self._file_entry:
      path_spec = self._file_entry.path_spec

    parser_chain = self.GetParserChain()
    extraction_error = errors.ExtractionError(
        message=message, parser_chain=parser_chain, path_spec=path_spec)
    self._storage_writer.AddError(extraction_error)
    self._number_of_errors += 1

  def RemoveEventAttribute(self, attribute_name):
    """Removes an attribute from being set on all events produced.

    Args:
      attribute_name (str): name of the attribute to remove.

    Raises:
      KeyError: if the event attribute is not set.
    """
    if attribute_name not in self._extra_event_attributes:
      raise KeyError(u'Event attribute: {0:s} not set'.format(attribute_name))

    del self._extra_event_attributes[attribute_name]

  def ResetFileEntry(self):
    """Resets the active file entry."""
    self._file_entry = None

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

  def SignalAbort(self):
    """Signals the parsers to abort."""
    self._abort = True
