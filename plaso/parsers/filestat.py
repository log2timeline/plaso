# -*- coding: utf-8 -*-
"""File system stat object parser."""

from __future__ import unicode_literals

from dfdatetime import posix_time as dfdatetime_posix_time
from dfvfs.lib import definitions as dfvfs_definitions

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import interface
from plaso.parsers import manager


class FileStatEventData(events.EventData):
  """File system stat event data.

  Attributes:
    file_entry_type (int): dfVFS file entry type.
    file_size (int): file size in bytes.
    file_system_type (str): file system type.
    inode (int): inode of the file related to the event.
    is_allocated (bool): True if the file is allocated.
  """

  DATA_TYPE = 'fs:stat'

  def __init__(self):
    """Initializes event data."""
    super(FileStatEventData, self).__init__(data_type=self.DATA_TYPE)
    self.file_entry_type = None
    self.file_size = None
    self.file_system_type = None
    self.inode = None
    self.is_allocated = None


class FileStatParser(interface.FileEntryParser):
  """Parses file system stat object."""

  NAME = 'filestat'
  DESCRIPTION = 'Parser for file system stat information.'

  _TIMESTAMP_DESCRIPTIONS = {
      'bkup_time': definitions.TIME_DESCRIPTION_BACKUP,
      'dtime': definitions.TIME_DESCRIPTION_DELETED,
  }

  def _GetFileSystemTypeFromFileEntry(self, file_entry):
    """Retrieves the file system type indicator of a file entry.

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
      type_string = '{0!s}'.format(fs_info.info.ftype)
      if type_string.startswith('TSK_FS_TYPE_'):
        type_string = type_string[12:]
      if type_string.endswith('_DETECT'):
        type_string = type_string[:-7]

    return type_string

  def ParseFileEntry(self, parser_mediator, file_entry):
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

    event_data = FileStatEventData()
    event_data.file_entry_type = stat_object.type
    event_data.file_size = getattr(stat_object, 'size', None)
    event_data.file_system_type = file_system_type
    event_data.is_allocated = file_entry.IsAllocated()

    if file_entry.access_time:
      event = time_events.DateTimeValuesEvent(
          file_entry.access_time, definitions.TIME_DESCRIPTION_LAST_ACCESS)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    if file_entry.creation_time:
      event = time_events.DateTimeValuesEvent(
          file_entry.creation_time, definitions.TIME_DESCRIPTION_CREATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    if file_entry.change_time:
      event = time_events.DateTimeValuesEvent(
          file_entry.change_time, definitions.TIME_DESCRIPTION_CHANGE)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    if file_entry.modification_time:
      event = time_events.DateTimeValuesEvent(
          file_entry.modification_time,
          definitions.TIME_DESCRIPTION_MODIFICATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    for time_attribute, usage in self._TIMESTAMP_DESCRIPTIONS.items():
      posix_time = getattr(stat_object, time_attribute, None)
      if posix_time is None:
        continue

      nano_time_attribute = '{0:s}_nano'.format(time_attribute)
      nano_time_attribute = getattr(stat_object, nano_time_attribute, None)

      timestamp = posix_time * 1000000
      if nano_time_attribute is not None:
        # Note that the _nano values are in intervals of 100th nano seconds.
        micro_time_attribute, _ = divmod(nano_time_attribute, 10)
        timestamp += micro_time_attribute

      # TSK will return 0 if the timestamp is not set.
      if (file_entry.type_indicator == dfvfs_definitions.TYPE_INDICATOR_TSK and
          not timestamp):
        continue

      date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
          timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(date_time, usage)
      parser_mediator.ProduceEventWithEventData(event, event_data)


manager.ParsersManager.RegisterParser(FileStatParser)
