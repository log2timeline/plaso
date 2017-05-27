# -*- coding: utf-8 -*-
"""This file contains the Network registry plugin."""

from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class NetworkDrivesPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for parsing the Network key."""

  NAME = u'network_drives'
  DESCRIPTION = u'Parser for Network Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(u'HKEY_CURRENT_USER\\Network')])

  _SOURCE_APPEND = u': Network Drive'

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
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

      event_data = windows_events.WindowsRegistryEventData()
      event_data.key_path = registry_key.path
      event_data.offset = subkey.offset
      event_data.regvalue = values_dict
      event_data.source_append = self._SOURCE_APPEND
      event_data.urls = self.URLS

      event = time_events.DateTimeValuesEvent(
          subkey.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(NetworkDrivesPlugin)
