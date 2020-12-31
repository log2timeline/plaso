# -*- coding: utf-8 -*-
"""Windows Prefetch custom event formatter helpers."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class WinPrefetchExecutionFormatter(interface.CustomEventFormatterHelper):
  """Custom formatter for Windows Prefetch execution event values."""

  DATA_TYPE = 'windows:prefetch:execution'

  def FormatEventValues(self, event_values):
    """Formats event values using the helper.

    Args:
      event_values (dict[str, object]): event values.
    """
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

    path_hints = event_values.get('path_hints', [])
    if path_hints:
      event_values['path_hints'] = '; '.join(path_hints)


manager.FormattersManager.RegisterEventFormatterHelper(
    WinPrefetchExecutionFormatter)
