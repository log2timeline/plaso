# -*- coding: utf-8 -*-
"""Windows drivers and services Registry key parser plugin."""

from plaso.containers import events
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class WindowsRegistryServiceEventData(events.EventData):
  """Windows Registry driver or service event data attribute container.

  Attributes:
    error_control (int): error control value of the Windows driver or service
        executable.
    image_path (str): path of the Windows driver or service executable.
    key_path (str): Windows Registry key path.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
    name (str): name of the Windows driver or service.
    object_name (str): Windows service object name.
    service_dll (str): Windows service DLL.
    service_type (int): Windows driver or service type.
    start_type (int): Device or service start type.
    values (str): names and data of additional values in the key.
    values (list[tuple[str, str, str]]): name, data type and data of the
        additional values in the key.
  """

  DATA_TYPE = 'windows:registry:service'

  def __init__(self):
    """Initializes event data."""
    super(WindowsRegistryServiceEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.error_control = None
    self.image_path = None
    self.key_path = None
    self.last_written_time = None
    self.name = None
    self.service_dll = None
    self.object_name = None
    self.service_type = None
    self.start_type = None
    self.values = None


class ServicesPlugin(interface.WindowsRegistryPlugin):
  """Plug-in to format the Services and Drivers keys having Type and Start."""

  NAME = 'windows_services'
  DATA_FORMAT = 'Windows drivers and services Registry data'

  # TODO: use a key path prefix match here. Might be more efficient.
  # HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Services
  FILTERS = frozenset([
      interface.WindowsRegistryKeyWithValuesFilter([
          'Start', 'Type'])])

  def _GetServiceDll(self, registry_key):
    """Retrieves the service DLL value.

    Obtains the service DLL for in the Parameters subkey of a Windows Registry
    service key.

    Args:
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.

    Returns:
      str: path of the service DLL or None.
    """
    parameters_key = registry_key.GetSubkeyByName('Parameters')
    if not parameters_key:
      return None

    return self._GetValueFromKey(parameters_key, 'ServiceDll')

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    service_type = self._GetValueFromKey(registry_key, 'Type')
    start_type = self._GetValueFromKey(registry_key, 'Start')

    if None in (service_type, start_type):
      parser_mediator.ProduceExtractionWarning(
          'missing values: Start and Type.')
      return

    # Create a specific service event, so that we can recognize and expand
    # certain values when we're outputting the event.
    event_data = WindowsRegistryServiceEventData()
    event_data.error_control = self._GetValueFromKey(
        registry_key, 'ErrorControl')
    event_data.image_path = self._GetValueFromKey(
        registry_key, 'ImagePath')
    event_data.key_path = registry_key.path
    event_data.last_written_time = registry_key.last_written_time
    event_data.name = registry_key.name
    event_data.object_name = self._GetValueFromKey(
        registry_key, 'ObjectName')
    event_data.service_type = service_type
    event_data.service_dll = self._GetServiceDll(registry_key)
    event_data.start_type = start_type
    event_data.values = self._GetValuesFromKey(
         parser_mediator, registry_key, names_to_skip=[
            'ErrorControl', 'ImagePath', 'ObjectName', 'Start', 'Type'])

    parser_mediator.ProduceEventData(event_data)


winreg_parser.WinRegistryParser.RegisterPlugin(ServicesPlugin)
