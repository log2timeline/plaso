# -*- coding: utf-8 -*-
"""This file contains the Network registry plugin."""

from plaso.containers import windows_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class NetworkDrivesPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for parsing the Network key."""

  NAME = u'network_drives'
  DESCRIPTION = u'Parser for Network Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(u'HKEY_CURRENT_USER\\Network')])

  def GetEntries(self, parser_mediator, registry_key, **kwargs):
    """Retrieves information from the Network registry key.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
    """
    for subkey in registry_key.GetSubkeys():
      drive_letter = subkey.name
      if not drive_letter:
        continue

      values_dict = {
          u'DriveLetter': drive_letter,
          u'Type': u'Mapped Drive'}

      # Get the remote path if it exists.
      remote_path_value = subkey.GetValueByName(u'RemotePath')
      if remote_path_value:
        remote_path = remote_path_value.GetDataAsObject()

        if remote_path.startswith(u'\\\\'):
          server_name, _, share_name = remote_path[2:].partition(u'\\')
          values_dict[u'RemoteServer'] = server_name
          values_dict[u'ShareName'] = u'\\{0:s}'.format(
              share_name.replace(u'#', u'\\'))

      event_object = windows_events.WindowsRegistryEvent(
          subkey.last_written_time, registry_key.path, values_dict,
          offset=subkey.offset, source_append=u': Network Drive')
      parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(NetworkDrivesPlugin)
