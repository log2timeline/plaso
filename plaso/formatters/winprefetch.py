"""Windows Prefetch custom event formatter helpers."""

from plaso.formatters import interface
from plaso.formatters import manager


class WindowsPrefetchPathHintsFormatterHelper(
    interface.CustomEventFormatterHelper):
  """Windows Prefetch path hints formatter helper."""

  IDENTIFIER = 'windows_prefetch_path_hints'

  def FormatEventValues(self, output_mediator, event_values):
    """Formats event values using the helper.

    Args:
      output_mediator (OutputMediator): output mediator.
      event_values (dict[str, object]): event values.
    """
    path_hints = event_values.get('path_hints')
    if path_hints:
      event_values['path_hints'] = '; '.join(path_hints)


class WindowsPrefetchVolumesStringFormatterHelper(
    interface.CustomEventFormatterHelper):
  """Windows Prefetch volumes string formatter helper."""

  IDENTIFIER = 'windows_prefetch_volumes_string'

  def FormatEventValues(self, output_mediator, event_values):
    """Formats event values using the helper.

    Args:
      output_mediator (OutputMediator): output mediator.
      event_values (dict[str, object]): event values.
    """
    number_of_volumes = event_values.get('number_of_volumes', 0)
    volume_serial_numbers = event_values.get('volume_serial_numbers')
    volume_device_paths = event_values.get('volume_device_paths')

    volumes_strings = []
    for volume_index in range(0, number_of_volumes):
      if not volume_serial_numbers:
        volume_serial_number = 'UNKNOWN'
      else:
        volume_serial_number = f'0x{volume_serial_numbers[volume_index]:08X}'

      if not volume_device_paths:
        volume_device_path = 'UNKNOWN'
      else:
        volume_device_path = volume_device_paths[volume_index]

      volumes_strings.append((
          f'volume: {volume_index + 1:d} [serial number: '
          f'{volume_serial_number:s}, device path: {volume_device_path:s}]'))

    if volumes_strings:
      event_values['volumes_string'] = ', '.join(volumes_strings)


manager.FormattersManager.RegisterEventFormatterHelpers([
    WindowsPrefetchPathHintsFormatterHelper,
    WindowsPrefetchVolumesStringFormatterHelper])
