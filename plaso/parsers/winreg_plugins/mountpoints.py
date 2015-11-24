# -*- coding: utf-8 -*-
"""This file contains the MountPoints2 plugin."""

from plaso.events import windows_events
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

  def GetEntries(self, parser_mediator, registry_key, **kwargs):
    """Retrieves information from the MountPoints2 registry key.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
    """
    for subkey in registry_key.GetSubkeys():
      name = subkey.name
      if not name:
        continue

      values_dict = {}
      values_dict[u'Volume'] = name

      label_value = subkey.GetValueByName(u'_LabelFromReg')
      if label_value:
        values_dict[u'Label'] = label_value.GetData()

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

      event_object = windows_events.WindowsRegistryEvent(
          subkey.last_written_time, registry_key.path, values_dict,
          offset=subkey.offset, urls=self.URLS)
      parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(MountPoints2Plugin)
