#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
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
"""File system stat object parser."""

from dfvfs.lib import definitions

from plaso.events import time_events
from plaso.lib import timelib
from plaso.parsers import interface


# TODO: move this function to lib or equiv since it is used from the collector
# as well.
class StatEvents(object):
  """Class that extracts event objects from a stat object."""

  TIME_ATTRIBUTES = frozenset([
      'atime', 'bkup_time', 'ctime', 'crtime', 'dtime', 'mtime'])

  # A copy of the collected file system type.
  _file_system_type = u''

  @classmethod
  def GetFileSystemTypeFromFileEntry(cls, file_entry):
    """Return a filesystem type string from a file entry object.

    Args:
      file_entry: A file entry object (instance of vfs.file_entry.FileEntry).

    Returns:
      A string indicating the file system type.
    """
    if cls._file_system_type:
      return cls._file_system_type

    file_system = file_entry.GetFileSystem()
    file_system_indicator = file_system.type_indicator

    if file_system_indicator == definitions.TYPE_INDICATOR_TSK:
      # TODO: Implement fs_type in dfVFS and remove this implementation
      # once that is in place.
      fs_info = file_system.GetFsInfo()
      if fs_info.info:
        type_string = unicode(fs_info.info.ftype)
        if type_string.startswith('TSK_FS_TYPE'):
          cls._file_system_type = type_string[12:]
          return cls._file_system_type

    cls._file_system_type = file_system_indicator
    return cls._file_system_type

  @classmethod
  def GetEventsFromStat(cls, stat_object, file_system_type):
    """Yield event objects from a file stat object.

    This method takes a stat object and yields an EventObject,
    instance of FileStatEvent, that contains all extracted
    timestamps from the stat object.

    The constraints are that the stat object implements an iterator
    that returns back values all timestamp based values have the
    attribute name 'time' in them. All timestamps also need to be
    stored as a Posix timestamps.

    Args:
      stat_object: A stat object (instance of dfvfs.VFSStat).
      file_system_type: A string that denotes the file system type,
                        eg: OS, NTFS, EXT3, etc.

    Yields:
      An event object for each extracted timestamp contained in the stat
      object.
    """
    time_values = []
    for attribute_name in cls.TIME_ATTRIBUTES:
      if hasattr(stat_object, attribute_name):
        time_values.append(attribute_name)

    if not time_values:
      return

    is_allocated = getattr(stat_object, 'allocated', True)

    file_size = getattr(stat_object, 'size', None),

    for time_value in time_values:
      timestamp = getattr(stat_object, time_value, None)
      if timestamp is None:
        continue

      nano_time_value = u'{0:s}_nano'.format(time_value)
      nano_time_value = getattr(stat_object, nano_time_value, None)

      timestamp = timelib.Timestamp.FromPosixTime(timestamp)
      if nano_time_value is not None:
        timestamp += nano_time_value

      # TODO: this also ignores any timestamp that equals 0.
      # Is this the desired behavior?
      if not timestamp:
        continue

      yield FileStatEvent(
          timestamp, time_value, is_allocated, file_size, file_system_type)


class FileStatEvent(time_events.TimestampEvent):
  """File system stat event."""

  DATA_TYPE = 'fs:stat'

  def __init__(self, timestamp, usage, allocated, size, fs_type):
    """Initializes the event.

    Args:
      timestamp: The timestamp value.
      usage: The usage string describing the timestamp.
      allocated: Boolean value to indicate the file entry is allocated.
      size: The file size in bytes.
      fs_type: The filesystem this timestamp is extracted from.
    """
    super(FileStatEvent, self).__init__(timestamp, usage)

    self.offset = 0
    self.size = size
    self.allocated = allocated
    self.fs_type = fs_type


class FileStatParser(interface.BaseParser):
  """Class that defines a file system stat object parser."""

  NAME = 'filestat'

  def Parse(self, file_entry):
    """Extract data from a file system stat entry.

    Args:
      file_entry: A file entry object.

    Yields:
      An event object (instance of FileStatEvent) that contains the parsed
      attributes.
    """
    stat_object = file_entry.GetStat()

    if stat_object:
      return StatEvents.GetEventsFromStat(
          stat_object, StatEvents.GetFileSystemTypeFromFileEntry(file_entry))
