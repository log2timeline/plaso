# -*- coding: utf-8 -*-
"""This file contains the Network drive Registry plugin."""

from __future__ import unicode_literals

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class NetworkDriveEventData(events.EventData):
  """Network drive event data attribute container.

  Attributes:
    drive_letter (str): drive letter assigned to network drive.
    key_path (str): Windows Registry key path.
    server_name (str): name of the server of the network drive.
    share_name (str): name of the share of the network drive.
  """

  DATA_TYPE = 'windows:registry:network_drive'

  def __init__(self):
    """Initializes event data."""
    super(NetworkDriveEventData, self).__init__(data_type=self.DATA_TYPE)
    self.drive_letter = None
    self.key_path = None
    self.server_name = None
    self.share_name = None


class NetworkDrivesPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for parsing the Network key."""

  NAME = 'network_drives'
  DESCRIPTION = 'Parser for Network Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter('HKEY_CURRENT_USER\\Network')])

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

      server_name = None
      share_name = None

      remote_path_value = subkey.GetValueByName('RemotePath')
      if remote_path_value:
        remote_path = remote_path_value.GetDataAsObject()
        if remote_path.startswith('\\\\'):
          server_name, _, share_name = remote_path[2:].partition('\\')
          share_name = '\\{0:s}'.format(share_name.replace('#', '\\'))

      event_data = NetworkDriveEventData()
      event_data.drive_letter = drive_letter
      event_data.key_path = registry_key.path
      event_data.server_name = server_name
      event_data.share_name = share_name

      event = time_events.DateTimeValuesEvent(
          subkey.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(NetworkDrivesPlugin)
