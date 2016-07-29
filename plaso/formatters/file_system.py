# -*- coding: utf-8 -*-
"""The file system stat event formatter."""

from dfvfs.lib import definitions as dfvfs_definitions

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class FileStatEventFormatter(interface.ConditionalEventFormatter):
  """The file system stat event formatter."""

  DATA_TYPE = u'fs:stat'

  FORMAT_STRING_PIECES = [
      u'{display_name}',
      u'Type: {file_entry_type}',
      u'({unallocated})']

  FORMAT_STRING_SHORT_PIECES = [
      u'{filename}']

  SOURCE_SHORT = u'FILE'

  _FILE_ENTRY_TYPES = {
      dfvfs_definitions.FILE_ENTRY_TYPE_DEVICE: u'device',
      dfvfs_definitions.FILE_ENTRY_TYPE_DIRECTORY: u'directory',
      dfvfs_definitions.FILE_ENTRY_TYPE_FILE: u'file',
      dfvfs_definitions.FILE_ENTRY_TYPE_LINK: u'link',
      dfvfs_definitions.FILE_ENTRY_TYPE_SOCKET: u'socket',
      dfvfs_definitions.FILE_ENTRY_TYPE_PIPE: u'pipe'}

  def GetMessages(self, unused_formatter_mediator, event):
    """Determines the formatted message strings for an event object.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions between
          formatters and other components, such as storage and Windows EventLog
          resources.
      event (EventObject): event.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event.data_type))

    event_values = event.CopyToDict()

    file_entry_type = event_values.get(u'file_entry_type', None)
    if file_entry_type is not None:
      event_values[u'file_entry_type'] = self._FILE_ENTRY_TYPES.get(
          file_entry_type, u'UNKNOWN')

    # The usage of allocated is deprecated in favor of is_allocated but
    # is kept here to be backwards compatible.
    if (not event_values.get(u'allocated', False) and
        not event_values.get(u'is_allocated', False)):
      event_values[u'unallocated'] = u'unallocated'

    return self._ConditionalFormatMessages(event_values)

  def GetSources(self, event):
    """Determines the the short and long source for an event object.

    Args:
      event (EventObject): event.

    Returns:
      tuple(str, str): short and long source string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event.data_type))

    file_system_type = getattr(event, u'file_system_type', u'UNKNOWN')
    timestamp_desc = getattr(event, u'timestamp_desc', u'Time')
    source_long = u'{0:s} {1:s}'.format(file_system_type, timestamp_desc)

    return self.SOURCE_SHORT, source_long


class NTFSFileStatEventFormatter(FileStatEventFormatter):
  """The NTFS file system stat event formatter."""

  DATA_TYPE = u'fs:stat:ntfs'

  FORMAT_STRING_PIECES = [
      u'{display_name}',
      u'File reference: {file_reference}',
      u'Attribute name: {attribute_name}',
      u'Name: {name}',
      u'Parent file reference: {parent_file_reference}',
      u'({unallocated})']

  FORMAT_STRING_SHORT_PIECES = [
      u'{filename}',
      u'{file_reference}',
      u'{attribute_name}']

  SOURCE_SHORT = u'FILE'

  _ATTRIBUTE_NAMES = {
      0x00000010: u'$STANDARD_INFORMATION',
      0x00000030: u'$FILE_NAME'
  }

  def GetMessages(self, unused_formatter_mediator, event):
    """Determines the formatted message strings for an event object.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions between
          formatters and other components, such as storage and Windows EventLog
          resources.
      event (EventObject): event.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event.data_type))

    event_values = event.CopyToDict()

    attribute_type = event_values.get(u'attribute_type', 0)
    event_values[u'attribute_name'] = self._ATTRIBUTE_NAMES.get(
        attribute_type, u'UNKNOWN')

    file_reference = event_values.get(u'file_reference', None)
    if file_reference:
      event_values[u'file_reference'] = u'{0:d}-{1:d}'.format(
          file_reference & 0xffffffffffff, file_reference >> 48)

    parent_file_reference = event_values.get(u'parent_file_reference', None)
    if parent_file_reference:
      event_values[u'parent_file_reference'] = u'{0:d}-{1:d}'.format(
          parent_file_reference & 0xffffffffffff, parent_file_reference >> 48)

    if not event_values.get(u'is_allocated', False):
      event_values[u'unallocated'] = u'unallocated'

    return self._ConditionalFormatMessages(event_values)


class NTFSUSNChangeEventFormatter(interface.ConditionalEventFormatter):
  """The NTFS USN change event formatter."""

  DATA_TYPE = u'fs:ntfs:usn_change'

  FORMAT_STRING_PIECES = [
      u'{filename}',
      u'File reference: {file_reference}',
      u'Parent file reference: {parent_file_reference}',
      u'Update source: {update_source}',
      u'Update reason: {update_reason}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{filename}',
      u'{file_reference}',
      u'{update_reason}']

  SOURCE_SHORT = u'FILE'

  _USN_REASON_FLAGS = {
      0x00000001: u'USN_REASON_DATA_OVERWRITE',
      0x00000002: u'USN_REASON_DATA_EXTEND',
      0x00000004: u'USN_REASON_DATA_TRUNCATION',
      0x00000010: u'USN_REASON_NAMED_DATA_OVERWRITE',
      0x00000020: u'USN_REASON_NAMED_DATA_EXTEND',
      0x00000040: u'USN_REASON_NAMED_DATA_TRUNCATION',
      0x00000100: u'USN_REASON_FILE_CREATE',
      0x00000200: u'USN_REASON_FILE_DELETE',
      0x00000400: u'USN_REASON_EA_CHANGE',
      0x00000800: u'USN_REASON_SECURITY_CHANGE',
      0x00001000: u'USN_REASON_RENAME_OLD_NAME',
      0x00002000: u'USN_REASON_RENAME_NEW_NAME',
      0x00004000: u'USN_REASON_INDEXABLE_CHANGE',
      0x00008000: u'USN_REASON_BASIC_INFO_CHANGE',
      0x00010000: u'USN_REASON_HARD_LINK_CHANGE',
      0x00020000: u'USN_REASON_COMPRESSION_CHANGE',
      0x00040000: u'USN_REASON_ENCRYPTION_CHANGE',
      0x00080000: u'USN_REASON_OBJECT_ID_CHANGE',
      0x00100000: u'USN_REASON_REPARSE_POINT_CHANGE',
      0x00200000: u'USN_REASON_STREAM_CHANGE',
      0x00400000: u'USN_REASON_TRANSACTED_CHANGE',
      0x80000000: u'USN_REASON_CLOSE'}

  _USN_SOURCE_FLAGS = {
      0x00000001: u'USN_SOURCE_DATA_MANAGEMENT',
      0x00000002: u'USN_SOURCE_AUXILIARY_DATA',
      0x00000004: u'USN_SOURCE_REPLICATION_MANAGEMENT'}

  def GetMessages(self, unused_formatter_mediator, event):
    """Determines the formatted message strings for an event object.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions between
          formatters and other components, such as storage and Windows EventLog
          resources.
      event (EventObject): event.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event.data_type))

    event_values = event.CopyToDict()

    file_reference = event_values.get(u'file_reference', None)
    if file_reference:
      event_values[u'file_reference'] = u'{0:d}-{1:d}'.format(
          file_reference & 0xffffffffffff, file_reference >> 48)

    parent_file_reference = event_values.get(u'parent_file_reference', None)
    if parent_file_reference:
      event_values[u'parent_file_reference'] = u'{0:d}-{1:d}'.format(
          parent_file_reference & 0xffffffffffff, parent_file_reference >> 48)

    update_reason_flags = event_values.get(u'update_reason_flags', 0)
    update_reasons = []
    for bitmask, description in sorted(self._USN_REASON_FLAGS.items()):
      if bitmask & update_reason_flags:
        update_reasons.append(description)

    event_values[u'update_reason'] = u', '.join(update_reasons)

    update_source_flags = event_values.get(u'update_source_flags', 0)
    update_sources = []
    for bitmask, description in sorted(self._USN_SOURCE_FLAGS.items()):
      if bitmask & update_source_flags:
        update_sources.append(description)

    event_values[u'update_source'] = u', '.join(update_sources)

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatters([
    FileStatEventFormatter, NTFSFileStatEventFormatter,
    NTFSUSNChangeEventFormatter])
