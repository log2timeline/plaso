# -*- coding: utf-8 -*-
"""Plug-in to collect information about the Windows version."""

import construct

from plaso.events import windows_events
from plaso.lib import timelib
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class WinVerPlugin(interface.KeyPlugin):
  """Plug-in to collect information about the Windows version."""

  NAME = u'windows_version'
  DESCRIPTION = u'Parser for Windows version Registry data.'

  REG_KEYS = [u'\\Microsoft\\Windows NT\\CurrentVersion']
  REG_TYPE = u'SOFTWARE'
  URLS = []

  INT_STRUCT = construct.ULInt32(u'install')

  # TODO: Refactor remove this function in a later CL.
  def GetValueString(self, key, value_name):
    """Retrieves a specific string value from the Registry key.

    Args:
      key: A Windows Registry key (instance of WinRegKey).
      value_name: The name of the value.

    Returns:
      A string value if one is available, otherwise an empty string.
    """
    value = key.GetValue(value_name)

    if not value:
      return u''

    if not value.data or not value.DataIsString():
      return u''
    return value.data

  def GetEntries(
      self, parser_mediator, key=None, registry_type=None, codepage='cp1252',
      **kwargs):
    """Gather minimal information about system install and return an event.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
    """
    text_dict = {}
    text_dict[u'Owner'] = self.GetValueString(key, u'RegisteredOwner')
    text_dict[u'sp'] = self.GetValueString(key, u'CSDBuildNumber')
    text_dict[u'Product name'] = self.GetValueString(key, u'ProductName')
    text_dict[u' Windows Version Information'] = u''

    install_raw = key.GetValue(u'InstallDate').raw_data
    # TODO: move this to a function in utils with a more descriptive name
    # e.g. CopyByteStreamToInt32BigEndian.
    try:
      install = self.INT_STRUCT.parse(install_raw)
    except construct.FieldError:
      install = 0

    event_object = windows_events.WindowsRegistryEvent(
        timelib.Timestamp.FromPosixTime(install), key.path, text_dict,
        usage=u'OS Install Time', offset=key.offset,
        registry_type=registry_type, urls=self.URLS)

    event_object.prodname = text_dict[u'Product name']
    event_object.source_long = u'SOFTWARE WinVersion key'
    if text_dict[u'Owner']:
      event_object.owner = text_dict[u'Owner']
    parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(WinVerPlugin)
