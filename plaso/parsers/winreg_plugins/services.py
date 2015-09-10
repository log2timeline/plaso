# -*- coding: utf-8 -*-
"""Plug-in to format the Services and Drivers key with Start and Type values."""

from plaso.events import windows_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class ServicesPlugin(interface.WindowsRegistryPlugin):
  """Plug-in to format the Services and Drivers keys having Type and Start."""

  NAME = u'windows_services'
  DESCRIPTION = u'Parser for services and drivers Registry data.'

  REG_VALUES = frozenset([u'Type', u'Start'])
  REG_TYPE = u'SYSTEM'
  URLS = [u'http://support.microsoft.com/kb/103000']

  def GetServiceDll(self, key):
    """Get the Service DLL for a service, if it exists.

    Checks for a ServiceDLL for in the Parameters subkey of a service key in
    the Registry.

    Args:
      key: A Windows Registry key (instance of dfwinreg.WinRegistryKey).
    """
    parameters_key = key.GetSubkeyByName(u'Parameters')
    if parameters_key:
      service_dll = parameters_key.GetValueByName(u'ServiceDll')
      if service_dll:
        return service_dll.data
    else:
      return None

  def GetEntries(
      self, parser_mediator, registry_key, registry_file_type=None, **kwargs):
    """Create one event for each subkey under Services that has Type and Start.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
      registry_file_type: Optional string containing the Windows Registry file
                          type, e.g. NTUSER, SOFTWARE. The default is None.
    """
    text_dict = {}

    service_type_value = registry_key.GetValueByName(u'Type')
    service_start_value = registry_key.GetValueByName(u'Start')

    # Grab the ServiceDLL value if it exists.
    if service_type_value and service_start_value:
      service_dll = self.GetServiceDll(registry_key)
      if service_dll:
        text_dict[u'ServiceDll'] = service_dll

      # Gather all the other string and integer values and insert as they are.
      for value in registry_key.GetValues():
        if not value.name:
          continue
        if value.name not in text_dict:
          if value.DataIsString() or value.DataIsInteger():
            text_dict[value.name] = value.data
          elif value.DataIsMultiString():
            text_dict[value.name] = u', '.join(value.data)

      # Create a specific service event, so that we can recognize and expand
      # certain values when we're outputting the event.
      event_object = windows_events.WindowsRegistryServiceEvent(
          registry_key.last_written_time, registry_key.path, text_dict,
          offset=registry_key.offset, registry_file_type=registry_file_type,
          urls=self.URLS)
      parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(ServicesPlugin)
