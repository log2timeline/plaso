# -*- coding: utf-8 -*-
"""This file contains the MountPoints2 plugin."""

from plaso.events import windows_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class MountPoints2Plugin(interface.KeyPlugin):
  """Windows Registry plugin for parsing the MountPoints2 key."""

  NAME = 'winreg_mountpoints2'
  DESCRIPTION = u'Parser for mount points Registry data.'

  REG_TYPE = 'NTUSER'

  REG_KEYS = [
      (u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\'
       u'MountPoints2')]

  URLS = [u'http://support.microsoft.com/kb/932463']

  def GetEntries(
      self, parser_mediator, key=None, registry_type=None, codepage='cp1252',
      **unused_kwargs):
    """Retrieves information from the MountPoints2 registry key.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
    """
    for subkey in key.GetSubkeys():
      name = subkey.name
      if not name:
        continue

      text_dict = {}
      text_dict[u'Volume'] = name

      # Get the label if it exists.
      label_value = subkey.GetValue('_LabelFromReg')
      if label_value:
        text_dict[u'Label'] = label_value.data

      if name.startswith('{'):
        text_dict[u'Type'] = u'Volume'

      elif name.startswith('#'):
        # The format is: ##Server_Name#Share_Name.
        text_dict[u'Type'] = u'Remote Drive'
        server_name, _, share_name = name[2:].partition('#')
        text_dict[u'Remote_Server'] = server_name
        text_dict[u'Share_Name'] = u'\\{0:s}'.format(
            share_name.replace(u'#', u'\\'))

      else:
        text_dict[u'Type'] = u'Drive'

      event_object = windows_events.WindowsRegistryEvent(
          subkey.last_written_timestamp, key.path, text_dict,
          offset=subkey.offset, registry_type=registry_type, urls=self.URLS)
      parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(MountPoints2Plugin)
