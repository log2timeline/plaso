# -*- coding: utf-8 -*-
"""File system stat object parser."""

from dfvfs.lib import definitions as dfvfs_definitions

from plaso.containers import time_events
from plaso.lib import timelib
from plaso.parsers import interface
from plaso.parsers import manager


class FileStatEvent(time_events.TimestampEvent):
  """File system stat event.

  Attributes:
    file_entry_type (int): dfVFS file entry type.
    file_size (int): file size in bytes.
    file_system_type (str): file system type.
    is_allocated (bool): True if the file is allocated.
    offset (int): the offset of the stat data in bytes.
  """

  DATA_TYPE = u'fs:stat'

  def __init__(
      self, timestamp, timestamp_description, is_allocated, file_size,
      file_entry_type, file_system_type):
    """Initializes the event object.

    Args:
      timestamp (int): timestamp, which contains the number of microseconds
          since Jan 1, 1970 00:00:00 UTC
      timestamp_description (str): description of the timestamp.
      is_allocated (bool): True if the file entry is allocated.
      file_size (int): file size in bytes.
      file_entry_type (int): dfVFS file entry type.
      file_system_type (str): file system type.
    """
    super(FileStatEvent, self).__init__(timestamp, timestamp_description)
    self.file_entry_type = file_entry_type
    self.file_size = file_size
    self.file_system_type = file_system_type
    self.is_allocated = is_allocated
    self.offset = 0


class FileStatParser(interface.FileEntryParser):
  """Parses file system stat object."""

  NAME = u'filestat'
  DESCRIPTION = u'Parser for file system stat information.'

  _TIME_ATTRIBUTES = frozenset([
      u'atime', u'bkup_time', u'ctime', u'crtime', u'dtime', u'mtime'])

  def _GetFileSystemTypeFromFileEntry(self, file_entry):
    """Return a filesystem type string from a file entry object.

    Args:
      file_entry (dfvfs.FileEntry): a file entry.

    Returns:
      str: file system type.
    """
    if file_entry.type_indicator != dfvfs_definitions.TYPE_INDICATOR_TSK:
      return file_entry.type_indicator

    # TODO: Implement fs_type in dfVFS and remove this implementation
    # once that is in place.
    file_system = file_entry.GetFileSystem()
    fs_info = file_system.GetFsInfo()
    if fs_info.info:
      type_string = u'{0:s}'.format(fs_info.info.ftype)
      if type_string.startswith(u'TSK_FS_TYPE'):
        return type_string[12:]

  def ParseFileEntry(self, parser_mediator, file_entry, **kwargs):
    """Parses a file entry.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_entry (dfvfs.FileEntry): a file entry.
    """
    stat_object = file_entry.GetStat()
    if not stat_object:
      return

    file_system_type = self._GetFileSystemTypeFromFileEntry(file_entry)

    is_allocated = getattr(stat_object, u'allocated', True)
    file_size = getattr(stat_object, u'size', None),

    for time_attribute in self._TIME_ATTRIBUTES:
      posix_time = getattr(stat_object, time_attribute, None)
      if posix_time is None:
        continue

      nano_time_attribute = u'{0:s}_nano'.format(time_attribute)
      nano_time_attribute = getattr(stat_object, nano_time_attribute, None)

      timestamp = timelib.Timestamp.FromPosixTime(posix_time)
      if nano_time_attribute is not None:
        # Note that the _nano values are in intervals of 100th nano seconds.
        micro_time_attribute, _ = divmod(nano_time_attribute, 10)
        timestamp += micro_time_attribute

      # TSK will return 0 if the timestamp is not set.
      if (file_entry.type_indicator == dfvfs_definitions.TYPE_INDICATOR_TSK and
          not timestamp):
        continue

      event_object = FileStatEvent(
          timestamp, time_attribute, is_allocated, file_size, stat_object.type,
          file_system_type)
      parser_mediator.ProduceEvent(event_object)


manager.ParsersManager.RegisterParser(FileStatParser)
