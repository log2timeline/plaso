# -*- coding: utf-8 -*-
"""The Windows services event formatter.

The Windows services are derived from Windows Registry files.
"""

from __future__ import unicode_literals

from plaso.formatters import manager
from plaso.formatters import interface
from plaso.lib import errors
from plaso.winnt import human_readable_service_enums


class WinRegistryServiceFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows service event."""

  DATA_TYPE = 'windows:registry:service'

  FORMAT_STRING_PIECES = [
      '[{key_path}]',
      'Type: {service_type}',
      'Start: {start_type}',
      'Image path: {image_path}',
      'Error control: {error_control}',
      '{values}']

  FORMAT_STRING_SHORT_PIECES = [
      '[{key_path}]',
      'Type: {service_type}',
      'Start: {start_type}',
      'Image path: {image_path}',
      'Error control: {error_control}',
      '{values}']

  def GetMessages(self, formatter_mediator, event_data):
    """Determines the formatted message strings for the event data.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions between
          formatters and other components, such as storage and Windows EventLog
          resources.
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

    error_control = event_values.get('error_control', None)
    if error_control is not None:
      error_control = (
          human_readable_service_enums.SERVICE_ENUMS['ErrorControl'].get(
              error_control, error_control))
      event_values['error_control'] = error_control

    service_type = event_values.get('service_type', None)
    if service_type is not None:
      service_type = human_readable_service_enums.SERVICE_ENUMS['Type'].get(
          service_type, service_type)
      event_values['service_type'] = service_type

    start_type = event_values.get('start_type', None)
    if start_type is not None:
      start_type = human_readable_service_enums.SERVICE_ENUMS['Start'].get(
          start_type, start_type)
      event_values['start_type'] = start_type

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(WinRegistryServiceFormatter)
