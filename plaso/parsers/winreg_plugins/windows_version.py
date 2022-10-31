# -*- coding: utf-8 -*-
"""Plug-in to collect information about the Windows version."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class WindowsRegistryInstallationEventData(events.EventData):
  """Windows installation event data attribute container.

  Attributes:
    build_number (str): Windows build number.
    installation_time (dfdatetime.DateTimeValues): Windows installation date
        and time.
    key_path (str): Windows Registry key path.
    owner (str): registered owner.
    product_name (str): product name.
    service_pack (str): service pack.
    version (str): Windows version.
  """

  DATA_TYPE = 'windows:registry:installation'

  def __init__(self):
    """Initializes event data."""
    super(WindowsRegistryInstallationEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.build_number = None
    self.installation_time = None
    self.key_path = None
    self.owner = None
    self.product_name = None
    self.service_pack = None
    self.version = None


class WindowsVersionPlugin(interface.WindowsRegistryPlugin):
  """Plug-in to collect information about the Windows version."""

  NAME = 'windows_version'
  DATA_FORMAT = 'Windows version (product) Registry data'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\'
          'CurrentVersion')])

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    # TODO: if not present indicate anomaly of missing InstallDate value.
    registry_value = registry_key.GetValueByName('InstallDate')
    if registry_value:
      event_data = WindowsRegistryInstallationEventData()
      event_data.build_number = self._GetValueFromKey(
          registry_key, 'CurrentBuildNumber')
      event_data.key_path = registry_key.path
      event_data.owner = self._GetValueFromKey(registry_key, 'RegisteredOwner')
      event_data.product_name = self._GetValueFromKey(
          registry_key, 'ProductName')
      event_data.service_pack = self._GetValueFromKey(
          registry_key, 'CSDVersion')
      event_data.version = self._GetValueFromKey(registry_key, 'CurrentVersion')

      installation_time = registry_value.GetDataAsObject()
      if installation_time:
        event_data.installation_time = dfdatetime_posix_time.PosixTime(
            timestamp=installation_time)

      parser_mediator.ProduceEventData(event_data)

    self._ProduceDefaultWindowsRegistryEvent(
        parser_mediator, registry_key, names_to_skip=['InstallDate'])


winreg_parser.WinRegistryParser.RegisterPlugin(WindowsVersionPlugin)
