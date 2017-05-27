# -*- coding: utf-8 -*-
"""This file contains the MountPoints2 plugin."""

from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class MountPoints2Plugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for parsing the MountPoints2 key."""

  NAME = u'explorer_mountpoints2'
  DESCRIPTION = u'Parser for mount points Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          u'Explorer\\MountPoints2')])

  URLS = [u'http://support.microsoft.com/kb/932463']

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    for subkey in registry_key.GetSubkeys():
      name = subkey.name
      if not name:
        continue

      values_dict = {}
      values_dict[u'Volume'] = name

      label_value = subkey.GetValueByName(u'_LabelFromReg')
      if label_value:
        values_dict[u'Label'] = label_value.GetDataAsObject()

      if name.startswith(u'{'):
        values_dict[u'Type'] = u'Volume'

      elif name.startswith(u'#'):
        # The format is: ##Server_Name#Share_Name.
        values_dict[u'Type'] = u'Remote Drive'
        server_name, _, share_name = name[2:].partition(u'#')
        values_dict[u'Remote_Server'] = server_name
        values_dict[u'Share_Name'] = u'\\{0:s}'.format(
            share_name.replace(u'#', u'\\'))

      else:
        values_dict[u'Type'] = u'Drive'

      event_data = windows_events.WindowsRegistryEventData()
      event_data.key_path = registry_key.path
      event_data.offset = subkey.offset
      event_data.regvalue = values_dict
      event_data.urls = self.URLS

      event = time_events.DateTimeValuesEvent(
          subkey.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(MountPoints2Plugin)
