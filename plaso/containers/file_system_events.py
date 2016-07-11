# -*- coding: utf-8 -*-
"""This file contains the file system specific event object classes."""

from plaso.containers import time_events
from plaso.lib import eventdata


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


class NTFSFileStatEvent(time_events.FiletimeEvent):
  """NTFS file system stat event.

  Attributes:
    attribute_type (int): attribute type e.g. 0x00000030 which represents
        $FILE_NAME.
    file_attribute_flags (int): NTFS file attribute flags.
    file_reference (int): NTFS file reference.
    file_system_type (str): file system type.
    is_allocated (bool): True if the MFT entry is allocated (marked as in use).
    name (str): name associated with the stat event, e.g. that of
        a $FILE_NAME attribute or None if not available.
    offset (int): offset of the stat data in bytes.
    parent_file_reference (int): NTFS file reference of the parent.
  """

  DATA_TYPE = u'fs:stat:ntfs'

  def __init__(
      self, timestamp, timestamp_description, file_reference, attribute_type,
      file_attribute_flags=None, is_allocated=True, name=None,
      parent_file_reference=None):
    """Initializes the event object.

    Args:
      timestamp (int): timestamp, which contains a FILETIME timestamp.
      timestamp_description (str): description of the timestamp.
      file_reference (int): NTFS file reference.
      attribute_type (int): attribute type e.g. 0x00000030 which represents
          $FILE_NAME.
      file_attribute_flags (Optional[int]): NTFS file attribute flags.
      is_allocated (Optional[bool]): True if the MFT entry is is allocated
          (marked as in use).
      name (Optional[str]): name associated with the stat event, e.g. that of
          a $FILE_NAME attribute or None if not available.
      parent_file_reference (Optional[int]): NTFS file reference of the parent.
    """
    super(NTFSFileStatEvent, self).__init__(timestamp, timestamp_description)
    self.attribute_type = attribute_type
    self.file_attribute_flags = file_attribute_flags
    self.file_reference = file_reference
    self.file_system_type = u'NTFS'
    self.is_allocated = is_allocated
    self.name = name
    self.offset = 0
    self.parent_file_reference = parent_file_reference


class NTFSUSNChangeEvent(time_events.FiletimeEvent):
  """NTFS USN change event.

  Attributes:
    file_attribute_flags (int): NTFS file attribute flags.
    file_reference (int): NTFS file reference.
    update_sequence_number (int): update sequence number.
    update_source_flags (int): update source flags.
    update_reason_flags (int): update reason flags.
    filename (str): name of the file associated with the event.
    file_system_type (str): file system type.
    offset (int): offset of the corresponding USN record in bytes.
    parent_file_reference (int): NTFS file reference of the parent.
  """

  DATA_TYPE = u'fs:ntfs:usn_change'

  def __init__(
      self, timestamp, offset, filename, file_reference, update_sequence_number,
      update_source_flags, update_reason_flags, file_attribute_flags=None,
      parent_file_reference=None):
    """Initializes the event object.

    Args:
      timestamp (int): timestamp, which contains a FILETIME timestamp.
      offset (int): offset of the corresponding USN record in bytes.
      filename (str): name of the file associated with the event.
      file_reference (int): NTFS file reference.
      update_sequence_number (int): update sequence number.
      update_source_flags (int): update source flags.
      update_reason_flags (int): update reason flags.
      file_attribute_flags (Optional[int]): NTFS file attribute flags.
      parent_file_reference (Optional[int]): NTFS file reference of the parent.
    """
    super(NTFSUSNChangeEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.ENTRY_MODIFICATION_TIME)
    self.file_attribute_flags = file_attribute_flags
    self.file_reference = file_reference
    self.filename = filename
    self.offset = offset
    self.parent_file_reference = parent_file_reference
    self.update_reason_flags = update_reason_flags
    self.update_sequence_number = update_sequence_number
    self.update_source_flags = update_source_flags
