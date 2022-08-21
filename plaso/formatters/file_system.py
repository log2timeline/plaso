# -*- coding: utf-8 -*-
"""File system custom event formatter helpers."""

from plaso.formatters import interface
from plaso.formatters import manager


class NTFSFileReferenceFormatterHelper(interface.CustomEventFormatterHelper):
  """NTFS file reference formatter helper."""

  IDENTIFIER = 'ntfs_file_reference'

  def FormatEventValues(self, output_mediator, event_values):
    """Formats event values using the helper.

    Args:
      output_mediator (OutputMediator): output mediator.
      event_values (dict[str, object]): event values.
    """
    file_reference = event_values.get('file_reference', None)
    if file_reference:
      event_values['file_reference'] = '{0:d}-{1:d}'.format(
          file_reference & 0xffffffffffff, file_reference >> 48)


class NTFSParentFileReferenceFormatterHelper(
    interface.CustomEventFormatterHelper):
  """NTFS parent file reference formatter helper."""

  IDENTIFIER = 'ntfs_parent_file_reference'

  def FormatEventValues(self, output_mediator, event_values):
    """Formats event values using the helper.

    Args:
      output_mediator (OutputMediator): output mediator.
      event_values (dict[str, object]): event values.
    """
    parent_file_reference = event_values.get('parent_file_reference', None)
    if parent_file_reference:
      event_values['parent_file_reference'] = '{0:d}-{1:d}'.format(
          parent_file_reference & 0xffffffffffff, parent_file_reference >> 48)


class NTFSPathHintsFormatterHelper(interface.CustomEventFormatterHelper):
  """NTFS path hints formatter helper."""

  IDENTIFIER = 'ntfs_path_hints'

  def FormatEventValues(self, output_mediator, event_values):
    """Formats event values using the helper.

    Args:
      output_mediator (OutputMediator): output mediator.
      event_values (dict[str, object]): event values.
    """
    path_hints = event_values.get('path_hints', None)
    if path_hints:
      event_values['path_hints'] = ';'.join(path_hints)


manager.FormattersManager.RegisterEventFormatterHelpers([
    NTFSFileReferenceFormatterHelper, NTFSParentFileReferenceFormatterHelper,
    NTFSPathHintsFormatterHelper])
