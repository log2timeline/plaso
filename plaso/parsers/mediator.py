# -*- coding: utf-8 -*-
"""The parser mediator object."""

import logging
import os

from dfvfs.lib import definitions as dfvfs_definitions

from plaso.containers import errors
from plaso.lib import py2to3
from plaso.lib import timelib


class ParserMediator(object):
  """Class that implements the parser mediator."""

  def __init__(self, storage_writer, knowledge_base):
    """Initializes a parser mediator object.

    Args:
      storage_writer: a storage writer object (instance of StorageWriter).
      knowledge_base: a knowledge base object (instance of KnowledgeBase),
                      which contains information from the source data needed
                      for parsing.
    """
    super(ParserMediator, self).__init__()
    self._abort = False
    self._extra_event_attributes = {}
    self._file_entry = None
    self._filter_object = None
    self._knowledge_base = knowledge_base
    self._mount_path = None
    # TODO: refactor status indication.
    self._number_of_event_sources = 0
    self._number_of_events = 0
    self._parser_chain_components = []
    self._storage_writer = storage_writer
    self._text_prepend = None

  @property
  def abort(self):
    """Read-only value to indicate the parsing should be aborted."""
    return self._abort

  @property
  def codepage(self):
    """The codepage."""
    return self._knowledge_base.codepage

  @property
  def hostname(self):
    """The hostname."""
    return self._knowledge_base.hostname

  @property
  def knowledge_base(self):
    """The knowledge base."""
    return self._knowledge_base

  @property
  def number_of_produced_event_sources(self):
    """The number of produced event sources."""
    return self._number_of_event_sources

  @property
  def number_of_produced_events(self):
    """The number of produced events."""
    return self._number_of_events

  @property
  def platform(self):
    """The platform."""
    return self._knowledge_base.platform

  @property
  def timezone(self):
    """The timezone object."""
    return self._knowledge_base.timezone

  @property
  def year(self):
    """The year."""
    return self._knowledge_base.year

  def _GetEarliestYearFromFileEntry(self):
    """Retrieves the year from the file entry date and time values.

    This function uses the creation time if available otherwise the change
    time (metadata last modification time) is used.

    Returns:
      An integer containing the year of the file entry or None.
    """
    file_entry = self.GetFileEntry()
    stat_object = file_entry.GetStat()

    posix_time = getattr(stat_object, u'crtime', None)
    if posix_time is None:
      posix_time = getattr(stat_object, u'ctime', None)

    if posix_time is None:
      logging.warning(
          u'Unable to determine creation year from file stat information.')
      return

    try:
      year = timelib.GetYearFromPosixTime(
          posix_time, timezone=self._knowledge_base.timezone)
      return year
    except ValueError as exception:
      logging.error((
          u'Unable to determine creation year from file stat information with '
          u'error: {0:s}').format(exception))
      return

  def _GetInode(self, inode_value):
    """Retrieves the inode from the inode value.

    Note that the inode value in TSK can be a string, e.g. '27-128-1'.

    Args:
      inode_value: a string or an integer containing the inode.

    Returns:
      An integer containing the inode or -1 on error if the inode value
      cannot be converted to an integer.
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
      An integer containing the year of the file entry or None.
    """
    file_entry = self.GetFileEntry()
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

  def _GetRelativePath(self, path_spec):
    """Retrieves the relative path.

    Args:
      path_spec: a path specification (instance of dfvfs.PathSpec).

    Returns:
      A string containing the relative path or None.
    """
    if not path_spec:
      return

    # TODO: Solve this differently, quite possibly inside dfVFS using mount
    # path spec.
    location = getattr(path_spec, u'location', None)
    if not location and path_spec.HasParent():
      location = getattr(path_spec.parent, u'location', None)

    if not location:
      return

    data_stream = getattr(path_spec, u'data_stream', None)
    if data_stream:
      location = u'{0:s}:{1:s}'.format(location, data_stream)

    if path_spec.type_indicator != dfvfs_definitions.TYPE_INDICATOR_OS:
      return location

    # If we are parsing a mount point we don't want to include the full
    # path to file's location here, we are only interested in the path
    # relative to the mount point.
    if self._mount_path:
      _, _, location = location.partition(self._mount_path)

    return location

  def AddEventAttribute(self, attribute_name, attribute_value):
    """Add an attribute that will be set on all events produced.

    Setting attributes using this method will cause events produced via this
    mediator to have an attribute with the provided name set with the
    provided value.

    Args:
      attribute_name: The name of the attribute to set.
      attribute_value: The value of the attribute to set.

    Raises:
      KeyError: If an attribute with the given name is already set.
    """
    if hasattr(self._extra_event_attributes, attribute_name):
      raise KeyError(u'Value already set for attribute {0:s}'.format(
          attribute_name))

    self._extra_event_attributes[attribute_name] = attribute_value

  def AppendToParserChain(self, plugin_or_parser):
    """Add a parser or plugin to the chain to the chain."""
    self._parser_chain_components.append(plugin_or_parser.NAME)

  def ClearEventAttributes(self):
    """Clear out attributes that should be added to all events."""
    self._extra_event_attributes = {}

  def ClearParserChain(self):
    """Clears the parser chain."""
    self._parser_chain_components = []

  def GetDisplayName(self, file_entry=None):
    """Retrieves the display name for a file entry.

    Args:
      file_entry: optional file entry object (instance of dfvfs.FileEntry).
                  If none is provided, the display name of self._file_entry
                  will be returned.

    Returns:
      A human readable string that describes the path to the file entry.

    Raises:
      ValueError: if the file entry is missing.
    """
    if file_entry is None:
      file_entry = self._file_entry

    if file_entry is None:
      raise ValueError(u'Missing file entry')

    path_spec = getattr(file_entry, u'path_spec', None)
    relative_path = self._GetRelativePath(path_spec)

    if not relative_path:
      relative_path = file_entry.name

    if not relative_path:
      return file_entry.path_spec.type_indicator

    if self._text_prepend:
      relative_path = u'{0:s}{1:s}'.format(self._text_prepend, relative_path)

    parent_path_spec = path_spec.parent
    if parent_path_spec and path_spec.type_indicator in [
        dfvfs_definitions.TYPE_INDICATOR_BZIP2,
        dfvfs_definitions.TYPE_INDICATOR_GZIP]:
      parent_path_spec = parent_path_spec.parent

    if parent_path_spec and parent_path_spec.type_indicator in [
        dfvfs_definitions.TYPE_INDICATOR_VSHADOW]:
      store_index = getattr(path_spec.parent, u'store_index', None)
      if store_index is not None:
        return u'VSS{0:d}:{1:s}:{2:s}'.format(
            store_index + 1, file_entry.path_spec.type_indicator, relative_path)

    return u'{0:s}:{1:s}'.format(
        file_entry.path_spec.type_indicator, relative_path)

  def GetEstimatedYear(self):
    """Retrieves an estimate of the year.

    This function first looks to see if the knowledge base defines a year, if
    not it tries to determine the year based on the file entry metadata, if
    that fails the current year is used.

    Returns:
      An integer containing the year of the file entry or the current year.
    """
    # TODO: improve this method to get a more reliable estimate.
    # Preserve the year-less date and sort this out in the psort phase.
    year = self._knowledge_base.year

    if not year:
      # TODO: Find a decent way to actually calculate the correct year
      # instead of relying on stats object.
      year = self._GetEarliestYearFromFileEntry()

    if not year:
      year = timelib.GetCurrentYear()

    return year

  def GetFileEntry(self):
    """Retrieves the active file entry.

    Returns:
      A file entry (instance of dfvfs.FileEntry).
    """
    return self._file_entry

  def GetFilename(self):
    """Retrieves the name of the active file entry.

    Returns:
      A string containing the name of the active file entry or None.
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
      An integer containing the year of the file entry or the current year.
    """
    year = self._GetLatestYearFromFileEntry()

    if not year:
      year = timelib.GetCurrentYear()

    return year

  def GetParserChain(self):
    """The parser chain up to this point."""
    return u'/'.join(self._parser_chain_components)

  def MatchesFilter(self, event_object):
    """Checks if the event object matches the filter.

    Args:
      event_object: the event object (instance of EventObject).

    Returns:
      A boolean value indicating if the event object matches the filter.
    """
    return self._filter_object and self._filter_object.Matches(event_object)

  def PopFromParserChain(self):
    """Remove the last added parser or plugin from the chain."""
    self._parser_chain_components.pop()

  def ProcessEvent(
      self, event_object, parser_chain=None, file_entry=None, query=None):
    """Processes an event before it written to the storage.

    Args:
      event_object: the event object (instance of EventObject).
      parser_chain: Optional string containing the parsing chain up to this
                    point.
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None, which will default to the current
                  file entry set in the mediator.
      query: Optional query string.
    """
    # TODO: rename this to event_object.parser_chain or equivalent.
    if not getattr(event_object, u'parser', None) and parser_chain:
      event_object.parser = parser_chain

    # TODO: deprecate text_prepend in favor of an event tag.
    if not getattr(event_object, u'text_prepend', None) and self._text_prepend:
      event_object.text_prepend = self._text_prepend

    if file_entry is None:
      file_entry = self._file_entry

    display_name = None
    if file_entry:
      event_object.pathspec = file_entry.path_spec

      if not getattr(event_object, u'filename', None):
        path_spec = getattr(file_entry, u'path_spec', None)
        event_object.filename = self._GetRelativePath(path_spec)

      if not display_name:
        # TODO: dfVFS refactor: move display name to output since the path
        # specification contains the full information.
        display_name = self.GetDisplayName(file_entry)

      stat_object = file_entry.GetStat()
      inode_value = getattr(stat_object, u'ino', None)
      if not hasattr(event_object, u'inode') and inode_value:
        event_object.inode = self._GetInode(inode_value)

    if not getattr(event_object, u'display_name', None) and display_name:
      event_object.display_name = display_name

    if not getattr(event_object, u'hostname', None) and self.hostname:
      event_object.hostname = self.hostname

    if not getattr(event_object, u'username', None):
      user_sid = getattr(event_object, u'user_sid', None)
      username = self._knowledge_base.GetUsernameByIdentifier(user_sid)
      if username:
        event_object.username = username

    if not getattr(event_object, u'query', None) and query:
      event_object.query = query

    for attribute, value in iter(self._extra_event_attributes.items()):
      if hasattr(event_object, attribute):
        raise KeyError(u'Event already has a value for {0:s}'.format(attribute))

      setattr(event_object, attribute, value)

  def ProduceEvent(self, event_object, query=None):
    """Produces an event.

    Args:
      event_object (EventObject): an event.
      query (Optional[str]): query that was used to obtain the event.

    Raises:
      RuntimeError: when storage writer is not set.
    """
    if not self._storage_writer:
      raise RuntimeError(u'Storage writer not set.')

    self.ProcessEvent(
        event_object, parser_chain=self.GetParserChain(),
        file_entry=self._file_entry, query=query)

    if self.MatchesFilter(event_object):
      return

    self._storage_writer.AddEvent(event_object)
    # TODO: refactor status indication.
    self._number_of_events += 1

  def ProduceEvents(self, event_objects, query=None):
    """Produces events.

    Args:
      event_objects: a list or generator of event objects (instances of
                     EventObject).
      query: Optional query string.
    """
    for event_object in event_objects:
      self.ProduceEvent(event_object, query=query)

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
    # TODO: refactor status indication.
    self._number_of_event_sources += 1

  def ProduceExtractionError(self, message):
    """Produces an extraction error.

    Args:
      message: The message of the error.

    Raises:
      RuntimeError: when storage writer is not set.
    """
    if not self._storage_writer:
      raise RuntimeError(u'Storage writer not set.')

    path_spec = self._file_entry.path_spec
    parser_chain = self.GetParserChain()
    extraction_error = errors.ExtractionError(
        message=message, parser_chain=parser_chain, path_spec=path_spec)
    self._storage_writer.AddError(extraction_error)

  def ResetFileEntry(self):
    """Resets the active file entry."""
    self._file_entry = None

  def SetFileEntry(self, file_entry):
    """Sets the active file entry.

    Args:
      file_entry: the file entry (instance of dfvfs.FileEntry).
    """
    self._file_entry = file_entry

  def SetFilterObject(self, filter_object):
    """Sets the filter object.

    Args:
      filter_object: the filter object (instance of objectfilter.Filter).
    """
    self._filter_object = filter_object

  def SetMountPath(self, mount_path):
    """Sets the mount path.

    Args:
      mount_path: string containing the mount path.
    """
    # Remove a trailing path separator from the mount path so the relative
    # paths will start with a path separator.
    if mount_path and mount_path.endswith(os.sep):
      mount_path = mount_path[:-1]

    self._mount_path = mount_path

  def SetStorageWriter(self, storage_writer):
    """Sets the storage writer.

    Args:
      storage_writer (StorageWriter): storage writer.
    """
    self._storage_writer = storage_writer

  def SetTextPrepend(self, text_prepend):
    """Sets the text prepend.

    Args:
      text_prepend: string that contains the text to prepend to every event.
    """
    self._text_prepend = text_prepend

  def SignalAbort(self):
    """Signals the parsers to abort."""
    self._abort = True
