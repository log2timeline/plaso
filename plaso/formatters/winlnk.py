# -*- coding: utf-8 -*-
"""The Windows Shortcut (LNK) event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


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

  SOURCE_LONG = 'Windows Shortcut'
  SOURCE_SHORT = 'LNK'

  def _GetLinkedPath(self, event_data):
    """Determines the linked path.

    Args:
      event_data (EventData): event_data data.

    Returns:
      str: linked path or "Unknown" if not set.
    """
    linked_path = getattr(event_data, 'local_path', None)
    if not linked_path:
      linked_path = getattr(event_data, 'network_path', None)

    if not linked_path:
      linked_path = getattr(event_data, 'relative_path', None)
      if linked_path:
        working_directory = getattr(event_data, 'working_directory', None)
        if working_directory:
          linked_path = '\\'.join([working_directory, linked_path])

    return linked_path or 'Unknown'

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
    if 'description' not in event_values:
      event_values['description'] = 'Empty description'

    event_values['linked_path'] = self._GetLinkedPath(event_data)

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(WinLnkLinkFormatter)
