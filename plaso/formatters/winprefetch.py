# -*- coding: utf-8 -*-
"""The Windows Prefetch event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class WinPrefetchExecutionFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows Prefetch execution event."""

  DATA_TYPE = u'windows:prefetch:execution'

  FORMAT_STRING_PIECES = [
      u'Prefetch',
      u'[{executable}] was executed -',
      u'run count {run_count}',
      u'path: {path}',
      u'hash: 0x{prefetch_hash:08X}',
      u'{volumes_string}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{executable} was run',
      u'{run_count} time(s)']

  SOURCE_LONG = u'WinPrefetch'
  SOURCE_SHORT = u'LOG'

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
      raise errors.WrongFormatter(
          u'Invalid event object - unsupported data type: {0:s}'.format(
              event_object.data_type))

    event_values = event_object.CopyToDict()

    number_of_volumes = event_values.get(u'number_of_volumes', 0)
    volume_serial_numbers = event_values.get(u'volume_serial_numbers', None)
    volume_device_paths = event_values.get(u'volume_device_paths', None)
    volumes_strings = []
    for volume_index in range(0, number_of_volumes):
      if not volume_serial_numbers:
        volume_serial_number = u'UNKNOWN'
      else:
        volume_serial_number = volume_serial_numbers[volume_index]

      if not volume_device_paths:
        volume_device_path = u'UNKNOWN'
      else:
        volume_device_path = volume_device_paths[volume_index]

      volumes_strings.append((
          u'volume: {0:d} [serial number: 0x{1:08X}, device path: '
          u'{2:s}]').format(
              volume_index + 1, volume_serial_number, volume_device_path))

    if volumes_strings:
      event_values[u'volumes_string'] = u', '.join(volumes_strings)

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(WinPrefetchExecutionFormatter)
