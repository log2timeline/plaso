# -*- coding: utf-8 -*-
"""File system stat object parser."""

import pytsk3

from dfvfs.lib import definitions as dfvfs_definitions

from plaso.containers import events
from plaso.parsers import interface
from plaso.parsers import manager


class FileStatEventData(events.EventData):
  """File system stat event data.

  Attributes:
    access_time (dfdatetime.DateTimeValues): file entry last access date
        and time.
    added_time (dfdatetime.DateTimeValues): file entry added date and time.
    attribute_names ([str]): extended attribute names.
    backup_time (dfdatetime.DateTimeValues): file entry backup date and time.
    change_time (dfdatetime.DateTimeValues): file entry inode change
        (or metadata last modification) date and time.
    creation_time (dfdatetime.DateTimeValues): file entry creation date
        and time.
    deletion_time (dfdatetime.DateTimeValues): file entry deletion date
        and time.
    display_name (str): display name.
    file_entry_type (int): dfVFS file entry type.
    file_size (int): file size in bytes.
    file_system_type (str): file system type.
    filename (str): name of the file.
    group_identifier (int): group identifier (GID), equivalent to st_gid.
    inode (int): inode of the file.
    is_allocated (bool): True if the file is allocated.
    mode (int): access mode, equivalent to st_mode & 0x0fff.
    modification_time (dfdatetime.DateTimeValues): file entry last modification
        date and time.
    number_of_links (int): number of hard links, equivalent to st_nlink.
    owner_identifier (int): user identifier (UID) of the owner, equivalent to
        st_uid.
  """

  DATA_TYPE = 'fs:stat'

  def __init__(self):
    """Initializes event data."""
    super(FileStatEventData, self).__init__(data_type=self.DATA_TYPE)
    self.access_time = None
    self.added_time = None
    self.attribute_names = None
    self.backup_time = None
    self.change_time = None
    self.creation_time = None
    self.deletion_time = None
    self.display_name = None
    self.file_entry_type = None
    self.file_size = None
    self.file_system_type = None
    self.filename = None
    self.group_identifier = None
    self.inode = None
    self.is_allocated = None
    self.mode = None
    self.modification_time = None
    self.number_of_links = None
    self.owner_identifier = None


class FileStatParser(interface.FileEntryParser):
  """Parses file system stat object."""

  NAME = 'filestat'
  DATA_FORMAT = 'file system stat information'

  _TSK_FS_TYPE_MAP = {}

  # Maps SleuthKit file system type enumeration values to a string.
  _TSK_FS_TYPE_MAP = {
      pytsk3.TSK_FS_TYPE_EXFAT: 'exFAT',
      pytsk3.TSK_FS_TYPE_EXT2: 'EXT2',
      pytsk3.TSK_FS_TYPE_EXT3: 'EXT3',
      pytsk3.TSK_FS_TYPE_EXT4: 'EXT4',
      pytsk3.TSK_FS_TYPE_EXT_DETECT: 'EXT',
      pytsk3.TSK_FS_TYPE_FAT12: 'FAT12',
      pytsk3.TSK_FS_TYPE_FAT16: 'FAT16',
      pytsk3.TSK_FS_TYPE_FAT32: 'FAT32',
      pytsk3.TSK_FS_TYPE_FAT_DETECT: 'FAT',
      pytsk3.TSK_FS_TYPE_FFS1B: 'FFS1b',
      pytsk3.TSK_FS_TYPE_FFS1: 'FFS1',
      pytsk3.TSK_FS_TYPE_FFS2: 'FFS2',
      pytsk3.TSK_FS_TYPE_FFS_DETECT: 'FFS',
      pytsk3.TSK_FS_TYPE_HFS: 'HFS',
      pytsk3.TSK_FS_TYPE_HFS_DETECT: 'HFS',
      pytsk3.TSK_FS_TYPE_ISO9660: 'ISO9660',
      pytsk3.TSK_FS_TYPE_ISO9660_DETECT: 'ISO9660',
      pytsk3.TSK_FS_TYPE_NTFS: 'NTFS',
      pytsk3.TSK_FS_TYPE_NTFS_DETECT: 'NTFS',
      pytsk3.TSK_FS_TYPE_YAFFS2: 'YAFFS2',
      pytsk3.TSK_FS_TYPE_YAFFS2_DETECT: 'YAFFS2'}

  def _GetFileSystemTypeFromFileEntry(self, file_entry):
    """Retrieves the file system type indicator of a file entry.

    Args:
      file_entry (dfvfs.FileEntry): a file entry.

    Returns:
      str: file system type.
    """
    if file_entry.type_indicator != dfvfs_definitions.TYPE_INDICATOR_TSK:
      type_string = file_entry.type_indicator
    else:
      file_system = file_entry.GetFileSystem()
      tsk_fs_type = file_system.GetFsType()

      try:
        type_string = self._TSK_FS_TYPE_MAP.get(tsk_fs_type, None)
      except TypeError:
        # Older version of pytsk3 can raise:
        # TypeError: unhashable type: 'pytsk3.TSK_FS_TYPE_ENUM'
        type_string = '{0!s}'.format(tsk_fs_type)
        if type_string.startswith('TSK_FS_TYPE_'):
          type_string = type_string[12:]
        if type_string.endswith('_DETECT'):
          type_string = type_string[:-7]

    if not type_string:
      type_string = 'UNKNOWN'
    return type_string

  def ParseFileEntry(self, parser_mediator, file_entry):
    """Parses a file entry.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_entry (dfvfs.FileEntry): a file entry.
    """
    file_system_type = self._GetFileSystemTypeFromFileEntry(file_entry)

    stat_attribute = file_entry.GetStatAttribute()

    attribute_names = []
    for attribute in file_entry.attributes:
      attribute_name = getattr(attribute, 'name', None)
      if isinstance(attribute_name, bytes):
        attribute_name = attribute_name.decode('utf-8')

      if file_system_type != 'NTFS' and attribute_name:
        attribute_names.append(attribute_name)

    event_data = FileStatEventData()
    event_data.access_time = file_entry.access_time
    event_data.added_time = file_entry.added_time
    event_data.attribute_names = attribute_names or None
    event_data.backup_time = file_entry.backup_time
    event_data.creation_time = file_entry.creation_time
    event_data.change_time = file_entry.change_time
    event_data.deletion_time = file_entry.deletion_time
    event_data.display_name = parser_mediator.GetDisplayNameForPathSpec(
        file_entry.path_spec)
    event_data.file_entry_type = file_entry.entry_type
    event_data.file_size = file_entry.size
    event_data.file_system_type = file_system_type
    event_data.filename = parser_mediator.GetRelativePathForPathSpec(
        file_entry.path_spec)
    event_data.is_allocated = file_entry.IsAllocated()
    event_data.modification_time = file_entry.modification_time

    if stat_attribute:
      event_data.group_identifier = stat_attribute.group_identifier
      event_data.inode = stat_attribute.inode_number
      if stat_attribute.mode is not None:
        event_data.mode = stat_attribute.mode & 0x0fff
      event_data.number_of_links = stat_attribute.number_of_links
      event_data.owner_identifier = stat_attribute.owner_identifier

    parser_mediator.ProduceEventData(event_data)


manager.ParsersManager.RegisterParser(FileStatParser)
