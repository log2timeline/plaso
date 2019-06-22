# -*- coding: utf-8 -*-
"""Windows drivers and services Registry key parser plugin."""

from __future__ import unicode_literals

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class WindowsRegistryServiceEventData(events.EventData):
  """Windows Registry driver or service event data attribute container.

  Attributes:
    error_control (int): error control value of the Windows driver or service
        executable.
    image_path (str): path of the Windows driver or service executable.
    key_path (str): Windows Registry key path.
    name (str): name of the Windows driver or service.
    object_name (str): Windows service object name.
    service_dll (str): Windows service DLL.
    service_type (int): Windows driver or service type.
    start_type (int): Device or service start type.
    values (str): names and data of additional values in the key.
  """

  DATA_TYPE = 'windows:registry:service'

  def __init__(self):
    """Initializes event data."""
    super(WindowsRegistryServiceEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.error_control = None
    self.image_path = None
    self.key_path = None
    self.name = None
    self.service_dll = None
    self.object_name = None
    self.service_type = None
    self.start_type = None
    self.values = None


class ServicesPlugin(interface.WindowsRegistryPlugin):
  """Plug-in to format the Services and Drivers keys having Type and Start.

  Also see:
    http://support.microsoft.com/kb/103000
  """

  NAME = 'windows_services'
  DESCRIPTION = 'Parser for services and drivers Registry data.'

  # TODO: use a key path prefix match here. Might be more efficient.
  # HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Services
  FILTERS = frozenset([
      interface.WindowsRegistryKeyWithValuesFilter([
          'Start', 'Type'])])

  def _GetServiceDll(self, key):
    """Retrieves the service DLL value.

    Obtains the service DLL for in the Parameters subkey of a Windows Registry
    service key.

    Args:
      key (dfwinreg.WinRegistryKey): a Windows Registry key.

    Returns:
      str: path of the service DLL or None.
    """
    parameters_key = key.GetSubkeyByName('Parameters')
    if not parameters_key:
      return None

    service_dll = parameters_key.GetValueByName('ServiceDll')
    if not service_dll:
      return None

    return service_dll.GetDataAsObject()

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    service_type = None
    start_type = None

    registry_value = registry_key.GetValueByName('Type')
    if registry_value:
      service_type = registry_value.GetDataAsObject()

    registry_value = registry_key.GetValueByName('Start')
    if registry_value:
      start_type = registry_value.GetDataAsObject()

    if None in (service_type, start_type):
      # TODO: generate extraction warning.
      return

    # Create a specific service event, so that we can recognize and expand
    # certain values when we're outputting the event.
    event_data = WindowsRegistryServiceEventData()
    event_data.key_path = registry_key.path
    event_data.name = registry_key.name
    event_data.service_type = service_type
    event_data.service_dll = self._GetServiceDll(registry_key)
    event_data.start_type = start_type

    registry_value = registry_key.GetValueByName('ErrorControl')
    if registry_value:
      event_data.error_control = registry_value.GetDataAsObject()

    registry_value = registry_key.GetValueByName('ImagePath')
    if registry_value:
      event_data.image_path = registry_value.GetDataAsObject()

    registry_value = registry_key.GetValueByName('ObjectName')
    if registry_value:
      event_data.object_name = registry_value.GetDataAsObject()

    values_dict = self._GetValuesFromKey(registry_key, names_to_skip=[
        'ErrorControl', 'ImagePath', 'ObjectName', 'Start', 'Type'])
    event_data.values = ' '.join([
        '{0:s}: {1!s}'.format(name, value)
        for name, value in sorted(values_dict.items())]) or None

    event = time_events.DateTimeValuesEvent(
        registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(ServicesPlugin)
