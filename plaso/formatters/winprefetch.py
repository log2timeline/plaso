# -*- coding: utf-8 -*-
"""The Windows Prefetch event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class WinPrefetchExecutionFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows Prefetch execution event."""

  DATA_TYPE = 'windows:prefetch:execution'

  FORMAT_STRING_PIECES = [
      'Prefetch',
      '[{executable}] was executed -',
      'run count {run_count}',
      'path: {path}',
      'hash: 0x{prefetch_hash:08X}',
      '{volumes_string}']

  FORMAT_STRING_SHORT_PIECES = [
      '{executable} was run',
      '{run_count} time(s)']

  SOURCE_LONG = 'WinPrefetch'
  SOURCE_SHORT = 'LOG'

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
      raise errors.WrongFormatter(
          'Invalid event object - unsupported data type: {0:s}'.format(
              event.data_type))

    event_values = event.CopyToDict()

    number_of_volumes = event_values.get('number_of_volumes', 0)
    volume_serial_numbers = event_values.get('volume_serial_numbers', None)
    volume_device_paths = event_values.get('volume_device_paths', None)
    volumes_strings = []
    for volume_index in range(0, number_of_volumes):
      if not volume_serial_numbers:
        volume_serial_number = 'UNKNOWN'
      else:
        volume_serial_number = volume_serial_numbers[volume_index]

      if not volume_device_paths:
        volume_device_path = 'UNKNOWN'
      else:
        volume_device_path = volume_device_paths[volume_index]

      volumes_strings.append((
          'volume: {0:d} [serial number: 0x{1:08X}, device path: '
          '{2:s}]').format(
              volume_index + 1, volume_serial_number, volume_device_path))

    if volumes_strings:
      event_values['volumes_string'] = ', '.join(volumes_strings)

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(WinPrefetchExecutionFormatter)
