# -*- coding: utf-8 -*-
"""The Windows Shortcut (LNK) event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class WinLnkLinkFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows Shortcut (LNK) link event."""

  DATA_TYPE = u'windows:lnk:link'

  FORMAT_STRING_PIECES = [
      u'[{description}]',
      u'File size: {file_size}',
      u'File attribute flags: 0x{file_attribute_flags:08x}',
      u'Drive type: {drive_type}',
      u'Drive serial number: 0x{drive_serial_number:08x}',
      u'Volume label: {volume_label}',
      u'Local path: {local_path}',
      u'Network path: {network_path}',
      u'cmd arguments: {command_line_arguments}',
      u'env location: {env_var_location}',
      u'Relative path: {relative_path}',
      u'Working dir: {working_directory}',
      u'Icon location: {icon_location}',
      u'Link target: {link_target}']

  FORMAT_STRING_SHORT_PIECES = [
      u'[{description}]',
      u'{linked_path}',
      u'{command_line_arguments}']

  SOURCE_LONG = u'Windows Shortcut'
  SOURCE_SHORT = u'LNK'

  def _GetLinkedPath(self, event_object):
    """Determines the linked path.

    Args:
      event_object: The event object (EventObject) containing the event
                    specific data.

    Returns:
      A string containing the linked path.
    """
    if hasattr(event_object, u'local_path'):
      return event_object.local_path

    if hasattr(event_object, u'network_path'):
      return event_object.network_path

    if hasattr(event_object, u'relative_path'):
      paths = []
      if hasattr(event_object, u'working_directory'):
        paths.append(event_object.working_directory)
      paths.append(event_object.relative_path)

      return u'\\'.join(paths)

    return u'Unknown'

  def GetMessages(self, unused_formatter_mediator, event_object):
    """Determines the formatted message strings for an event object.

    Args:
      formatter_mediator: the formatter mediator object (instance of
                          FormatterMediator).
      event_object: the event object (instance of EventObject).

    Returns:
      A tuple containing the formatted message string and short message string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    event_values = event_object.CopyToDict()
    if u'description' not in event_values:
      event_values[u'description'] = u'Empty description'

    event_values[u'linked_path'] = self._GetLinkedPath(event_object)

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(WinLnkLinkFormatter)
