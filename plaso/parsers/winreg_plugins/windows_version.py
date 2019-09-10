# -*- coding: utf-8 -*-
"""Plug-in to collect information about the Windows version."""

from __future__ import unicode_literals

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class WindowsRegistryInstallationEventData(events.EventData):
  """Windows installation event data attribute container.

  Attributes:
    build_number (str): Windows build number.
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
    self.key_path = None
    self.owner = None
    self.product_name = None
    self.service_pack = None
    self.version = None


class WindowsVersionPlugin(interface.WindowsRegistryPlugin):
  """Plug-in to collect information about the Windows version."""

  NAME = 'windows_version'
  DESCRIPTION = 'Parser for Windows version Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\'
          'CurrentVersion')])

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    values_dict = self._GetValuesFromKey(
        registry_key, names_to_skip=['InstallDate'])

    installation_time = None
    registry_value = registry_key.GetValueByName('InstallDate')
    if registry_value:
      installation_time = registry_value.GetDataAsObject()

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = registry_key.path
    event_data.values = ' '.join([
        '{0:s}: {1!s}'.format(name, value)
        for name, value in sorted(values_dict.items())]) or None

    event = time_events.DateTimeValuesEvent(
        registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)

    # TODO: if not present indicate anomaly of missing installation
    # date and time.
    if installation_time is not None:
      event_data = WindowsRegistryInstallationEventData()
      event_data.key_path = registry_key.path

      registry_value = registry_key.GetValueByName('CurrentBuildNumber')
      if registry_value:
        event_data.build_number = registry_value.GetDataAsObject()

      registry_value = registry_key.GetValueByName('RegisteredOwner')
      if registry_value:
        event_data.owner = registry_value.GetDataAsObject()

      registry_value = registry_key.GetValueByName('ProductName')
      if registry_value:
        event_data.product_name = registry_value.GetDataAsObject()

      registry_value = registry_key.GetValueByName('CSDVersion')
      if registry_value:
        event_data.service_pack = registry_value.GetDataAsObject()

      registry_value = registry_key.GetValueByName('CurrentVersion')
      if registry_value:
        event_data.version = registry_value.GetDataAsObject()

      date_time = dfdatetime_posix_time.PosixTime(timestamp=installation_time)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_INSTALLATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(WindowsVersionPlugin)
