#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The parser context object."""

import os

from dfvfs.lib import definitions as dfvfs_definitions

from plaso.lib import event
from plaso.lib import utils


class ParserContext(object):
  """Class that implements the parser context."""

  def __init__(
      self, event_queue_producer, parse_error_queue_producer, knowledge_base):
    """Initializes a parser context object.

    Args:
      event_queue_producer: the event object queue producer (instance of
                            ItemQueueProducer).
      parse_error_queue_producer: the parse error queue producer (instance of
                                  ItemQueueProducer).
      knowledge_base: A knowledge base object (instance of KnowledgeBase),
                      which contains information from the source data needed
                      for parsing.
    """
    super(ParserContext, self).__init__()
    self._abort = False
    self._event_queue_producer = event_queue_producer
    self._filter_object = None
    self._knowledge_base = knowledge_base
    self._mount_path = None
    self._parse_error_queue_producer = parse_error_queue_producer
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

  def GetDisplayName(self, file_entry):
    """Retrieves the display name for the file entry.

    Args:
      file_entry: a file entry object (instance of dfvfs.FileEntry).

    Returns:
      A string containing the display name.
    """
    relative_path = self.GetRelativePath(file_entry)
    if not relative_path:
      return file_entry.name

    return u'{0:s}:{1:s}'.format(
        file_entry.path_spec.type_indicator, relative_path)

  def GetRelativePath(self, file_entry):
    """Retrieves the relative path of the file entry.

    Args:
      file_entry: a file entry object (instance of dfvfs.FileEntry).

    Returns:
      A string containing the relative path or None.
    """
    path_spec = getattr(file_entry, 'path_spec', None)
    if not path_spec:
      return

    # TODO: Solve this differently, quite possibly inside dfVFS using mount
    # path spec.
    file_path = getattr(path_spec, 'location', None)

    if path_spec.type_indicator != dfvfs_definitions.TYPE_INDICATOR_OS:
      return file_path

    # If we are parsing a mount point we don't want to include the full
    # path to file's location here, we are only interested in the relative
    # path to the mount point.
    if self._mount_path:
      _, _, file_path = file_path.partition(self._mount_path)

    return file_path

  def MatchesFilter(self, event_object):
    """Checks if the event object matces the filter.

    Args:
      event_object: the event object (instance of EventObject).

    Returns:
      A boolean value indicating if the event object matches the filter.
    """
    return self._filter_object and self._filter_object.Matches(event_object)

  def ProcessEvent(
      self, event_object, parser_chain=None, file_entry=None, query=None):
    """Processes an event before it is emitted to the event queue.

    Args:
      event_object: the event object (instance of EventObject).
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      query: Optional query string. The default is None.
    """
    if not getattr(event_object, 'parser', None) and parser_chain:
      event_object.parser = parser_chain

    # TODO: deprecate text_prepend in favor of an event tag.
    if not getattr(event_object, 'text_prepend', None) and self._text_prepend:
      event_object.text_prepend = self._text_prepend

    display_name = None
    if file_entry:
      event_object.pathspec = file_entry.path_spec

      if not getattr(event_object, 'filename', None):
        event_object.filename = self.GetRelativePath(file_entry)

      if not display_name:
        # TODO: dfVFS refactor: move display name to output since the path
        # specification contains the full information.
        display_name = self.GetDisplayName(file_entry)

      stat_object = file_entry.GetStat()
      inode_number = getattr(stat_object, 'ino', None)
      if not hasattr(event_object, 'inode') and inode_number:
        # TODO: clean up the GetInodeValue function.
        event_object.inode = utils.GetInodeValue(inode_number)

    if not getattr(event_object, 'display_name', None) and display_name:
      event_object.display_name = display_name

    if not getattr(event_object, 'hostname', None) and self.hostname:
      event_object.hostname = self.hostname

    if not getattr(event_object, 'username', None):
      user_sid = getattr(event_object, 'user_sid', None)
      username = self._knowledge_base.GetUsernameByIdentifier(user_sid)
      if username:
        event_object.username = username

    if not getattr(event_object, 'query', None) and query:
      event_object.query = query

  def ProduceEvent(
      self, event_object, parser_chain=None, file_entry=None, query=None):
    """Produces an event onto the queue.

    Args:
      event_object: the event object (instance of EventObject).
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      query: Optional query string. The default is None.
    """
    self.ProcessEvent(
        event_object, parser_chain=parser_chain, file_entry=file_entry,
        query=query)

    if self.MatchesFilter(event_object):
      return

    self._event_queue_producer.ProduceItem(event_object)
    self.number_of_events += 1

  def ProduceEvents(
      self, event_objects, parser_chain=None, file_entry=None, query=None):
    """Produces events onto the queue.

    Args:
      event_objects: a list or generator of event objects (instances of
                     EventObject).
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      query: Optional query string. The default is None.
    """
    for event_object in event_objects:
      self.ProduceEvent(
          event_object, parser_chain=parser_chain, file_entry=file_entry,
          query=query)

  def ProduceParseError(self, name, description, file_entry=None):
    """Produces a parse error.

    Args:
      name: The parser or plugin name.
      description: The description of the error.
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
    """
    if self._parse_error_queue_producer:
      path_spec = getattr(file_entry, 'path_spec', None)
      parse_error = event.ParseError(name, description, path_spec=path_spec)
      self._parse_error_queue_producer.ProduceItem(parse_error)
      self.number_of_parse_errors += 1

  def ResetCounters(self):
    """Resets the counters."""
    self.number_of_events = 0
    self.number_of_parse_errors = 0

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
