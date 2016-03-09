# -*- coding: utf-8 -*-
"""Plug-in to collect information about the Windows version."""

from plaso.containers import windows_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class WinVerPlugin(interface.WindowsRegistryPlugin):
  """Plug-in to collect information about the Windows version."""

  NAME = u'windows_version'
  DESCRIPTION = u'Parser for Windows version Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\'
          u'CurrentVersion')])

  URLS = []

  _STRING_VALUE_NAME_STRINGS = {
      u'CSDVersion': u'service_pack',
      u'CurrentVersion': u'version',
      u'CurrentBuildNumber': u'build_number',
      u'ProductName': u'product_name',
      u'RegisteredOrganization': u'organization',
      u'RegisteredOwner': u'owner',
  }

  def GetEntries(self, parser_mediator, registry_key, **kwargs):
    """Gather minimal information about system install and return an event.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
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

    owner = string_values.get(u'owner', u'')
    product_name = string_values.get(u'product_name', u'')
    service_pack = string_values.get(u'service_pack', u'')
    version = string_values.get(u'version', u'')

    values_dict = {}
    values_dict[u'Owner'] = owner
    values_dict[u'Product name'] = product_name
    values_dict[u'Service pack'] = service_pack
    values_dict[u'Windows Version Information'] = version

    event_object = windows_events.WindowsRegistryEvent(
        registry_key.last_written_time, registry_key.path, values_dict,
        offset=registry_key.offset)

    parser_mediator.ProduceEvent(event_object)

    # TODO: if not present indicate anomaly of missing installation
    # date and time.
    if installation_value:
      posix_time = installation_value.GetDataAsObject()
      event_object = windows_events.WindowsRegistryInstallationEvent(
          posix_time, registry_key.path, owner, product_name, service_pack,
          version)
      parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(WinVerPlugin)
