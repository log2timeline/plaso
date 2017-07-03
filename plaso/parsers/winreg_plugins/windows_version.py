# -*- coding: utf-8 -*-
"""Plug-in to collect information about the Windows version."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class WindowsVersionPlugin(interface.WindowsRegistryPlugin):
  """Plug-in to collect information about the Windows version."""

  NAME = u'windows_version'
  DESCRIPTION = u'Parser for Windows version Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\'
          u'CurrentVersion')])

  _STRING_VALUE_NAME_STRINGS = {
      u'CSDVersion': u'service_pack',
      u'CurrentVersion': u'version',
      u'CurrentBuildNumber': u'build_number',
      u'ProductName': u'product_name',
      u'RegisteredOrganization': u'organization',
      u'RegisteredOwner': u'owner',
  }

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    installation_value = None
    string_values = {}
    for registry_value in registry_key.GetValues():
      # Ignore the default value.
      if not registry_value.name:
        continue

      if (registry_value.name == u'InstallDate' and
          registry_value.DataIsInteger()):
        installation_value = registry_value
        continue

      # Ignore any value that is empty or that does not contain a string.
      if not registry_value.data or not registry_value.DataIsString():
        continue

      string_value_name = self._STRING_VALUE_NAME_STRINGS.get(
          registry_value.name, None)
      if not string_value_name:
        continue

      string_values[string_value_name] = registry_value.GetDataAsObject()

    values_dict = {}
    values_dict[u'Owner'] = string_values.get(u'owner', u'')
    values_dict[u'Product name'] = string_values.get(u'product_name', u'')
    values_dict[u'Service pack'] = string_values.get(u'service_pack', u'')
    values_dict[u'Windows Version Information'] = string_values.get(
        u'version', u'')

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = registry_key.path
    event_data.offset = registry_key.offset
    event_data.regvalue = values_dict

    event = time_events.DateTimeValuesEvent(
        registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)

    # TODO: if not present indicate anomaly of missing installation
    # date and time.
    if installation_value:
      event_data = windows_events.WindowsRegistryInstallationEventData()
      event_data.key_path = registry_key.path
      event_data.offset = registry_key.offset
      event_data.owner = string_values.get(u'owner', None)
      event_data.product_name = string_values.get(u'product_name', None)
      event_data.service_pack = string_values.get(u'service_pack', None)
      event_data.version = string_values.get(u'version', None)

      installation_time = installation_value.GetDataAsObject()
      date_time = dfdatetime_posix_time.PosixTime(timestamp=installation_time)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_INSTALLATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(WindowsVersionPlugin)
