# -*- coding: utf-8 -*-
"""The parser mediator object."""

import logging
import os

from dfvfs.lib import definitions as dfvfs_definitions

# TODO: disabled as long nothing is listening on the parse error queue.
# from plaso.lib import event
from plaso.lib import utils


class ParserMediator(object):
  """Class that implements the parser mediator."""

  def __init__(
      self, event_queue_producer, parse_error_queue_producer, knowledge_base):
    """Initializes a parser mediator object.

    Args:
      event_queue_producer: the event object queue producer (instance of
                            ItemQueueProducer).
      parse_error_queue_producer: the parse error queue producer (instance of
                                  ItemQueueProducer).
      knowledge_base: A knowledge base object (instance of KnowledgeBase),
                      which contains information from the source data needed
                      for parsing.
    """
    super(ParserMediator, self).__init__()
    self._abort = False
    self._event_queue_producer = event_queue_producer
    self._extra_event_attributes = {}
    self._file_entry = None
    self._filter_object = None
    self._knowledge_base = knowledge_base
    self._mount_path = None
    self._parse_error_queue_producer = parse_error_queue_producer
    self._parser_chain_components = []
    self._text_prepend = None

    self.number_of_events = 0
    self.number_of_parse_errors = 0

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
    """Retrieves the display name for the file entry.

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

    return u'{0:s}:{1:s}'.format(
        file_entry.path_spec.type_indicator, relative_path)

  def GetFileEntry(self):
    """The dfVFS FileEntry object for the file being parsed."""
    return self._file_entry

  def GetFileObject(self, offset=0):
    """Provides a dfVFS FileObject for the file being parsed.

    Args:
      offset: the offset to seek within the file-like object. The offset is
              relative from the start of the data. The default is 0. None
              can be used to ignore setting the offset.

    Returns:
      A file-like object (instance of dfvfs.FileIO).

    Raises:
      ValueError: If no file entry is set in the mediator.
    """
    if not self._file_entry:
      raise ValueError(u'Missing file entry')

    file_object = self._file_entry.GetFileObject()
    if offset is not None:
      file_object.seek(offset, os.SEEK_SET)
    return file_object

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
    """Processes an event before it is emitted to the event queue.

    Args:
      event_object: the event object (instance of EventObject).
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None, which will default to the current
                  file entry set in the mediator.
      query: Optional query string. The default is None.
    """
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
      inode_number = getattr(stat_object, u'ino', None)
      if not hasattr(event_object, u'inode') and inode_number:
        # TODO: clean up the GetInodeValue function.
        event_object.inode = utils.GetInodeValue(inode_number)

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

    for attribute, value in self._extra_event_attributes.iteritems():
      if hasattr(event_object, attribute):
        raise KeyError(u'Event already has a value for {0:s}'.format(attribute))

      setattr(event_object, attribute, value)

  def ProduceEvent(self, event_object, query=None):
    """Produces an event onto the queue.

    Args:
      event_object: the event object (instance of EventObject).
      query: Optional query string. The default is None.
    """
    self.ProcessEvent(
        event_object, parser_chain=self.GetParserChain(),
        file_entry=self._file_entry, query=query)

    if self.MatchesFilter(event_object):
      return

    self._event_queue_producer.ProduceItem(event_object)
    self.number_of_events += 1

  def ProduceEvents(self, event_objects, query=None):
    """Produces events onto the queue.

    Args:
      event_objects: a list or generator of event objects (instances of
                     EventObject).
      query: Optional query string. The default is None.
    """
    for event_object in event_objects:
      self.ProduceEvent(event_object, query=query)

  def ProduceParseError(self, message):
    """Produces a parse error.

    Args:
      message: The message of the error.
    """
    self.number_of_parse_errors += 1
    # TODO: Remove call to logging when parser error queue is fully functional.
    logging.error(u'Error in {0:s} while parsing file {1:s}: {2:s}'.format(
        self.GetParserChain(), self.GetDisplayName(), message))

    # TODO: disabled as long nothing is listening on the parse error queue.
    # if self._parse_error_queue_producer:
    #   path_spec = self._file_entry.path_spec
    #   parser_chain = self.GetParserChain()
    #   parse_error = event.ParseError(
    #       parser_chain, message, path_spec=path_spec)
    #   self._parse_error_queue_producer.ProduceItem(parse_error)
    #   self.number_of_parse_errors += 1

  def ResetCounters(self):
    """Resets the counters."""
    self.number_of_events = 0
    self.number_of_parse_errors = 0

  def ResetFileEntry(self):
    """Resets the file entry."""
    self._file_entry = None

  def SetFileEntry(self, file_entry):
    """Sets the current file entry and clears the parser chain.

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

  def SetTextPrepend(self, text_prepend):
    """Sets the text prepend.

    Args:
      text_prepend: string that contains the text to prepend to every event.
    """
    self._text_prepend = text_prepend

  def SignalAbort(self):
    """Signals the parsers to abort."""
    self._abort = True
