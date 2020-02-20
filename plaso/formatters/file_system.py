# -*- coding: utf-8 -*-
"""The file system stat event formatter."""

from __future__ import unicode_literals

from dfvfs.lib import definitions as dfvfs_definitions

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class FileStatEventFormatter(interface.ConditionalEventFormatter):
  """The file system stat event formatter."""

  DATA_TYPE = 'fs:stat'

  FORMAT_STRING_PIECES = [
      '{display_name}',
      'Type: {file_entry_type}',
      '({unallocated})']

  FORMAT_STRING_SHORT_PIECES = [
      '{filename}']

  SOURCE_SHORT = 'FILE'

  # The numeric values are for backwards compatibility with plaso files
  # generated with older versions of dfvfs.
  _FILE_ENTRY_TYPES = {
      1: 'device',
      2: 'directory',
      3: 'file',
      4: 'link',
      5: 'socket',
      6: 'pipe',
      dfvfs_definitions.FILE_ENTRY_TYPE_DEVICE: 'device',
      dfvfs_definitions.FILE_ENTRY_TYPE_DIRECTORY: 'directory',
      dfvfs_definitions.FILE_ENTRY_TYPE_FILE: 'file',
      dfvfs_definitions.FILE_ENTRY_TYPE_LINK: 'link',
      dfvfs_definitions.FILE_ENTRY_TYPE_SOCKET: 'socket',
      dfvfs_definitions.FILE_ENTRY_TYPE_PIPE: 'pipe'}

  # pylint: disable=unused-argument
  def GetMessages(self, formatter_mediator, event_data):
    """Determines the formatted message strings for the event data.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions
          between formatters and other components, such as storage and Windows
          EventLog resources.
      event_data (EventData): event data.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event data cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_data.data_type:
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event_data.data_type))

    event_values = event_data.CopyToDict()

    file_entry_type = event_values.get('file_entry_type', None)
    if file_entry_type is not None:
      event_values['file_entry_type'] = self._FILE_ENTRY_TYPES.get(
          file_entry_type, 'UNKNOWN')

    # The usage of allocated is deprecated in favor of is_allocated but
    # is kept here to be backwards compatible.
    if (not event_values.get('allocated', False) and
        not event_values.get('is_allocated', False)):
      event_values['unallocated'] = 'unallocated'

    return self._ConditionalFormatMessages(event_values)

  def GetSources(self, event, event_data):
    """Determines the the short and long source for an event.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.

    Returns:
      tuple(str, str): short and long source string.

    Raises:
      WrongFormatter: if the event data cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_data.data_type:
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event_data.data_type))

    file_system_type = getattr(event_data, 'file_system_type', 'UNKNOWN')
    timestamp_desc = getattr(event, 'timestamp_desc', 'Time')
    source_long = '{0:s} {1:s}'.format(file_system_type, timestamp_desc)

    return self.SOURCE_SHORT, source_long


class NTFSFileStatEventFormatter(FileStatEventFormatter):
  """The NTFS file system stat event formatter."""

  DATA_TYPE = 'fs:stat:ntfs'

  FORMAT_STRING_PIECES = [
      '{display_name}',
      'File reference: {file_reference}',
      'Attribute name: {attribute_name}',
      'Name: {name}',
      'Parent file reference: {parent_file_reference}',
      '({unallocated})',
      'Path hints: {path_hints}']

  FORMAT_STRING_SHORT_PIECES = [
      '{filename}',
      '{file_reference}',
      '{attribute_name}']

  SOURCE_SHORT = 'FILE'

  _ATTRIBUTE_NAMES = {
      0x00000010: '$STANDARD_INFORMATION',
      0x00000030: '$FILE_NAME'
  }

  def GetMessages(self, formatter_mediator, event_data):
    """Determines the formatted message strings for the event data.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions
          between formatters and other components, such as storage and Windows
          EventLog resources.
      event_data (EventData): event data.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event data cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_data.data_type:
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event_data.data_type))

    event_values = event_data.CopyToDict()

    attribute_type = event_values.get('attribute_type', 0)
    event_values['attribute_name'] = self._ATTRIBUTE_NAMES.get(
        attribute_type, 'UNKNOWN')

    file_reference = event_values.get('file_reference', None)
    if file_reference:
      event_values['file_reference'] = '{0:d}-{1:d}'.format(
          file_reference & 0xffffffffffff, file_reference >> 48)

    parent_file_reference = event_values.get('parent_file_reference', None)
    if parent_file_reference:
      event_values['parent_file_reference'] = '{0:d}-{1:d}'.format(
          parent_file_reference & 0xffffffffffff, parent_file_reference >> 48)

    if not event_values.get('is_allocated', False):
      event_values['unallocated'] = 'unallocated'

    path_hints = event_values.get('path_hints', [])
    if path_hints:
      event_values['path_hints'] = ';'.join(path_hints)

    return self._ConditionalFormatMessages(event_values)


class NTFSUSNChangeEventFormatter(interface.ConditionalEventFormatter):
  """The NTFS USN change event formatter."""

  DATA_TYPE = 'fs:ntfs:usn_change'

  FORMAT_STRING_PIECES = [
      '{filename}',
      'File reference: {file_reference}',
      'Parent file reference: {parent_file_reference}',
      'Update source: {update_source}',
      'Update reason: {update_reason}']

  FORMAT_STRING_SHORT_PIECES = [
      '{filename}',
      '{file_reference}',
      '{update_reason}']

  SOURCE_SHORT = 'FILE'

  _USN_REASON_FLAGS = {
      0x00000001: 'USN_REASON_DATA_OVERWRITE',
      0x00000002: 'USN_REASON_DATA_EXTEND',
      0x00000004: 'USN_REASON_DATA_TRUNCATION',
      0x00000010: 'USN_REASON_NAMED_DATA_OVERWRITE',
      0x00000020: 'USN_REASON_NAMED_DATA_EXTEND',
      0x00000040: 'USN_REASON_NAMED_DATA_TRUNCATION',
      0x00000100: 'USN_REASON_FILE_CREATE',
      0x00000200: 'USN_REASON_FILE_DELETE',
      0x00000400: 'USN_REASON_EA_CHANGE',
      0x00000800: 'USN_REASON_SECURITY_CHANGE',
      0x00001000: 'USN_REASON_RENAME_OLD_NAME',
      0x00002000: 'USN_REASON_RENAME_NEW_NAME',
      0x00004000: 'USN_REASON_INDEXABLE_CHANGE',
      0x00008000: 'USN_REASON_BASIC_INFO_CHANGE',
      0x00010000: 'USN_REASON_HARD_LINK_CHANGE',
      0x00020000: 'USN_REASON_COMPRESSION_CHANGE',
      0x00040000: 'USN_REASON_ENCRYPTION_CHANGE',
      0x00080000: 'USN_REASON_OBJECT_ID_CHANGE',
      0x00100000: 'USN_REASON_REPARSE_POINT_CHANGE',
      0x00200000: 'USN_REASON_STREAM_CHANGE',
      0x00400000: 'USN_REASON_TRANSACTED_CHANGE',
      0x80000000: 'USN_REASON_CLOSE'}

  _USN_SOURCE_FLAGS = {
      0x00000001: 'USN_SOURCE_DATA_MANAGEMENT',
      0x00000002: 'USN_SOURCE_AUXILIARY_DATA',
      0x00000004: 'USN_SOURCE_REPLICATION_MANAGEMENT'}

  def GetMessages(self, formatter_mediator, event_data):
    """Determines the formatted message strings for the event data.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions
          between formatters and other components, such as storage and Windows
          EventLog resources.
      event_data (EventData): event data.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event data cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_data.data_type:
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event_data.data_type))

    event_values = event_data.CopyToDict()

    file_reference = event_values.get('file_reference', None)
    if file_reference:
      event_values['file_reference'] = '{0:d}-{1:d}'.format(
          file_reference & 0xffffffffffff, file_reference >> 48)

    parent_file_reference = event_values.get('parent_file_reference', None)
    if parent_file_reference:
      event_values['parent_file_reference'] = '{0:d}-{1:d}'.format(
          parent_file_reference & 0xffffffffffff, parent_file_reference >> 48)

    update_reason_flags = event_values.get('update_reason_flags', 0)
    update_reasons = []
    for bitmask, description in sorted(self._USN_REASON_FLAGS.items()):
      if bitmask & update_reason_flags:
        update_reasons.append(description)

    event_values['update_reason'] = ', '.join(update_reasons)

    update_source_flags = event_values.get('update_source_flags', 0)
    update_sources = []
    for bitmask, description in sorted(self._USN_SOURCE_FLAGS.items()):
      if bitmask & update_source_flags:
        update_sources.append(description)

    event_values['update_source'] = ', '.join(update_sources)

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatters([
    FileStatEventFormatter, NTFSFileStatEventFormatter,
    NTFSUSNChangeEventFormatter])
