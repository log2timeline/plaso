# -*- coding: utf-8 -*-
"""The Windows Shortcut (LNK) event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class WinLnkLinkFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows Shortcut (LNK) link event."""

  DATA_TYPE = 'windows:lnk:link'

  FORMAT_STRING_PIECES = [
      '[{description}]',
      'File size: {file_size}',
      'File attribute flags: 0x{file_attribute_flags:08x}',
      'Drive type: {drive_type}',
      'Drive serial number: 0x{drive_serial_number:08x}',
      'Volume label: {volume_label}',
      'Local path: {local_path}',
      'Network path: {network_path}',
      'cmd arguments: {command_line_arguments}',
      'env location: {env_var_location}',
      'Relative path: {relative_path}',
      'Working dir: {working_directory}',
      'Icon location: {icon_location}',
      'Link target: {link_target}']

  FORMAT_STRING_SHORT_PIECES = [
      '[{description}]',
      '{linked_path}',
      '{command_line_arguments}']

  def _GetLinkedPath(self, event_values):
    """Determines the linked path.

    Args:
      event_values (dict[str, object]): event values.

    Returns:
      str: linked path or "Unknown" if not set.
    """
    linked_path = event_values.get('local_path', None)
    if not linked_path:
      linked_path = event_values.get('network_path', None)

    if not linked_path:
      linked_path = event_values.get('relative_path', None)
      if linked_path:
        working_directory = event_values.get('working_directory', None)
        if working_directory:
          linked_path = '\\'.join([working_directory, linked_path])

    return linked_path or 'Unknown'

  def FormatEventValues(self, event_values):
    """Formats event values using the helpers.

    Args:
      event_values (dict[str, object]): event values.
    """
    if 'description' not in event_values:
      event_values['description'] = 'Empty description'

    event_values['linked_path'] = self._GetLinkedPath(event_values)


manager.FormattersManager.RegisterFormatter(WinLnkLinkFormatter)
