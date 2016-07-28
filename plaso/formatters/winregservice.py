# -*- coding: utf-8 -*-
"""The Windows services event formatter.

The Windows services are derived from Windows Registry files.
"""

from plaso.formatters import manager
from plaso.formatters import winreg
from plaso.winnt import human_readable_service_enums


class WinRegistryServiceFormatter(winreg.WinRegistryGenericFormatter):
  """Formatter for a Windows service event."""

  DATA_TYPE = u'windows:registry:service'

  def GetMessages(self, formatter_mediator, event):
    """Determines the formatted message strings for an event object.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions between
          formatters and other components, such as storage and Windows EventLog
          resources.
      event (EventObject): event.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    regvalue = getattr(event, u'regvalue', {})
    # Loop over all the registry value names in the service key.
    for service_value_name in regvalue.keys():
      # A temporary variable so we can refer to this long name more easily.
      service_enums = human_readable_service_enums.SERVICE_ENUMS
      # Check if we need to can make the value more human readable.
      if service_value_name in service_enums.keys():
        service_enum = service_enums[service_value_name]
        # Find the human readable version of the name and fall back to the
        # raw value if it's not found.
        human_readable_value = service_enum.get(
            regvalue[service_value_name],
            regvalue[service_value_name])
        regvalue[service_value_name] = human_readable_value

    return super(WinRegistryServiceFormatter, self).GetMessages(
        formatter_mediator, event)


manager.FormattersManager.RegisterFormatter(WinRegistryServiceFormatter)
