# -*- coding: utf-8 -*-
"""The file system stat event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class NTFSFileStatEventFormatter(interface.ConditionalEventFormatter):
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

  _ATTRIBUTE_NAMES = {
      0x00000010: '$STANDARD_INFORMATION',
      0x00000030: '$FILE_NAME'}

  def FormatEventValues(self, event_values):
    """Formats event values using the helpers.

    Args:
      event_values (dict[str, object]): event values.
    """
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

  def FormatEventValues(self, event_values):
    """Formats event values using the helpers.

    Args:
      event_values (dict[str, object]): event values.
    """
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


manager.FormattersManager.RegisterFormatters([
    NTFSFileStatEventFormatter, NTFSUSNChangeEventFormatter])
