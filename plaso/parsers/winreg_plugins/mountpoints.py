# -*- coding: utf-8 -*-
"""This file contains the MountPoints2 plugin."""

from plaso.events import windows_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class MountPoints2Plugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for parsing the MountPoints2 key."""

  NAME = u'explorer_mountpoints2'
  DESCRIPTION = u'Parser for mount points Registry data.'

  REG_TYPE = u'NTUSER'

  REG_KEYS = [
      (u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\'
       u'MountPoints2')]

  URLS = [u'http://support.microsoft.com/kb/932463']

  def GetEntries(
      self, parser_mediator, key=None, registry_file_type=None,
      codepage=u'cp1252', **unused_kwargs):
    """Retrieves information from the MountPoints2 registry key.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_file_type: Optional string containing the Windows Registry file
                          type, e.g. NTUSER, SOFTWARE. The default is None.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    for subkey in key.GetSubkeys():
      name = subkey.name
      if not name:
        continue

      text_dict = {}
      text_dict[u'Volume'] = name

      # Get the label if it exists.
      label_value = subkey.GetValue(u'_LabelFromReg')
      if label_value:
        text_dict[u'Label'] = label_value.data

      if name.startswith(u'{'):
        text_dict[u'Type'] = u'Volume'

      elif name.startswith(u'#'):
        # The format is: ##Server_Name#Share_Name.
        text_dict[u'Type'] = u'Remote Drive'
        server_name, _, share_name = name[2:].partition(u'#')
        text_dict[u'Remote_Server'] = server_name
        text_dict[u'Share_Name'] = u'\\{0:s}'.format(
            share_name.replace(u'#', u'\\'))

      else:
        text_dict[u'Type'] = u'Drive'

      event_object = windows_events.WindowsRegistryEvent(
          subkey.last_written_timestamp, key.path, text_dict,
          offset=subkey.offset, registry_file_type=registry_file_type,
          urls=self.URLS)
      parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(MountPoints2Plugin)
