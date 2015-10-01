# -*- coding: utf-8 -*-
"""File system stat object parser."""

from dfvfs.lib import definitions as dfvfs_definitions

from plaso.events import file_system_events
from plaso.lib import timelib
from plaso.parsers import interface
from plaso.parsers import manager


class FileStatParser(interface.BaseParser):
  """Class that defines a file system stat object parser."""

  NAME = u'filestat'
  DESCRIPTION = u'Parser for file system stat information.'

  _TIME_ATTRIBUTES = frozenset([
      u'atime', u'bkup_time', u'ctime', u'crtime', u'dtime', u'mtime'])

  def _GetFileSystemTypeFromFileEntry(self, file_entry):
    """Return a filesystem type string from a file entry object.

    Args:
      file_entry: A file entry object (instance of vfs.file_entry.FileEntry).

    Returns:
      A string indicating the file system type.
    """
    file_system = file_entry.GetFileSystem()
    type_indicator = file_system.type_indicator

    if type_indicator != dfvfs_definitions.TYPE_INDICATOR_TSK:
      return type_indicator

    # TODO: Implement fs_type in dfVFS and remove this implementation
    # once that is in place.
    fs_info = file_system.GetFsInfo()
    if fs_info.info:
      type_string = unicode(fs_info.info.ftype)
      if type_string.startswith(u'TSK_FS_TYPE'):
        return type_string[12:]

  def Parse(self, parser_mediator, **kwargs):
    """Extracts event objects from a file system stat entry.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
    """
    file_entry = parser_mediator.GetFileEntry()
    stat_object = file_entry.GetStat()
    if not stat_object:
      return

    file_system_type = self._GetFileSystemTypeFromFileEntry(file_entry)

    is_allocated = getattr(stat_object, u'allocated', True)
    file_size = getattr(stat_object, u'size', None),

    for time_attribute in self._TIME_ATTRIBUTES:
      timestamp = getattr(stat_object, time_attribute, None)
      if timestamp is None:
        continue

      nano_time_attribute = u'{0:s}_nano'.format(time_attribute)
      nano_time_attribute = getattr(stat_object, nano_time_attribute, None)

      timestamp = timelib.Timestamp.FromPosixTime(timestamp)
      if nano_time_attribute is not None:
        # Note that the _nano values are in intervals of 100th nano seconds.
        micro_time_attribute, _ = divmod(nano_time_attribute, 10)
        timestamp += micro_time_attribute

      # TODO: this also ignores any timestamp that equals 0.
      # Is this the desired behavior?
      if not timestamp:
        continue

      event_object = file_system_events.FileStatEvent(
          timestamp, time_attribute, is_allocated, file_size, file_system_type)
      parser_mediator.ProduceEvent(event_object)


manager.ParsersManager.RegisterParser(FileStatParser)
