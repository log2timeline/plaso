# -*- coding: utf-8 -*-
"""File system custom event formatter helpers."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class NTFSFileStatEventFormatter(interface.CustomEventFormatterHelper):
  """Custom formatter for NTFS file system stat event values."""

  DATA_TYPE = 'fs:stat:ntfs'

  def FormatEventValues(self, event_values):
    """Formats event values using the helper.

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

    path_hints = event_values.get('path_hints', [])
    if path_hints:
      event_values['path_hints'] = ';'.join(path_hints)


class NTFSUSNChangeEventFormatter(interface.CustomEventFormatterHelper):
  """Custom formatter for NTFS USN change event values."""

  DATA_TYPE = 'fs:ntfs:usn_change'

  def FormatEventValues(self, event_values):
    """Formats event values using the helper.

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


manager.FormattersManager.RegisterEventFormatterHelpers([
    NTFSFileStatEventFormatter, NTFSUSNChangeEventFormatter])
