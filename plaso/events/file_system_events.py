# -*- coding: utf-8 -*-
"""This file contains the file system specific event object classes."""

from plaso.events import time_events


class FileStatEvent(time_events.TimestampEvent):
  """File system stat event.

  Attributes:
    file_size: the file size.
    file_system_type: the file system type.
    is_allocated: boolean value to indicate the file is allocated.
    offset: the offset of the stat data.
  """

  DATA_TYPE = u'fs:stat'

  def __init__(
      self, timestamp, timestamp_description, is_allocated, file_size,
      file_system_type):
    """Initializes the event object.

    Args:
      timestamp: the timestamp time value. The timestamp contains the
                 number of microseconds since Jan 1, 1970 00:00:00 UTC
      timestamp_description: a description string for the timestamp value.
      is_allocated: boolean value to indicate the file entry is allocated.
      file_size: an integer containing the file size in bytes.
      file_system_type: a string containing the file system type.
    """
    super(FileStatEvent, self).__init__(timestamp, timestamp_description)

    self.file_size = file_size
    self.file_system_type = file_system_type
    self.is_allocated = is_allocated
    self.offset = 0


class NTFSFileStatEvent(time_events.FiletimeEvent):
  """NTFS file system stat event.

  Attributes:
    attribute_type: the attribute type e.g. 0x00000030 which represents
                    $FILE_NAME.
    file_attribute_flags: the NTFS file attribute flags, set to None
                          if not available.
    file_reference: NTFS file reference.
    file_system_type: the file system type.
    is_allocated: boolean value to indicate the MFT entry is allocated
                 (marked as in use).
    name: string containing the name associated with the stat event, e.g.
          that of a $FILE_NAME attribute, set to None if not available.
    offset: the offset of the stat data.
    parent_file_reference: NTFS file reference of the parent, set to None
                           if not available.
  """

  DATA_TYPE = u'fs:stat:ntfs'

  def __init__(
      self, timestamp, timestamp_description, file_reference, attribute_type,
      file_attribute_flags=None, is_allocated=True, name=None,
      parent_file_reference=None):
    """Initializes the event object.

    Args:
      timestamp: the FILETIME value for the timestamp.
      timestamp_description: the usage string for the timestamp value.
      file_reference: NTFS file reference.
      attribute_type: the attribute type e.g. 0x00000030 which represents
                      $FILE_NAME.
      file_attribute_flags: optional NTFS file attribute flags, set to None
                            if not available.
      is_allocated: optional boolean value to indicate the MFT entry is
                    is allocated (marked as in use).
      name: optional string containing the name associated with the stat event,
            e.g.  that of a $FILE_NAME attribute, set to None if not available.
      parent_file_reference: optional NTFS file reference of the parent, set
                             to None if not available.
    """
    super(NTFSFileStatEvent, self).__init__(timestamp, timestamp_description)

    self.attribute_type = attribute_type
    self.file_reference = file_reference
    self.file_attribute_flags = file_attribute_flags
    self.file_system_type = u'NTFS'
    self.is_allocated = is_allocated
    self.name = name
    self.offset = 0
    self.parent_file_reference = parent_file_reference
