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

  def _GetLinkedPath(self, event):
    """Determines the linked path.

    Args:
      event (EventObject): event that contains a linked path.

    Returns:
      str: linked path.
    """
    if hasattr(event, 'local_path'):
      return event.local_path

    if hasattr(event, 'network_path'):
      return event.network_path

    if hasattr(event, 'relative_path'):
      paths = []
      if hasattr(event, 'working_directory'):
        paths.append(event.working_directory)
      paths.append(event.relative_path)

      return '\\'.join(paths)

    return 'Unknown'

  # pylint: disable=unused-argument
  def GetMessages(self, formatter_mediator, event):
    """Determines the formatted message strings for an event object.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions
          between formatters and other components, such as storage and Windows
          EventLog resources.
      event (EventObject): event.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event.data_type:
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event.data_type))

    event_values = event.CopyToDict()
    if 'description' not in event_values:
      event_values['description'] = 'Empty description'

    event_values['linked_path'] = self._GetLinkedPath(event)

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(WinLnkLinkFormatter)
