# -*- coding: utf-8 -*-
"""Plug-in to collect information about the Windows version."""

import construct

from plaso.events import windows_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class WinVerPlugin(interface.WindowsRegistryPlugin):
  """Plug-in to collect information about the Windows version."""

  NAME = u'windows_version'
  DESCRIPTION = u'Parser for Windows version Registry data.'

  REG_KEYS = [u'\\Microsoft\\Windows NT\\CurrentVersion']
  REG_TYPE = u'SOFTWARE'
  URLS = []

  INT_STRUCT = construct.ULInt32(u'install')

  # TODO: Refactor remove this function in a later CL.
  def _GetValueString(self, key, value_name):
    """Retrieves a specific string value from the Registry key.

    Args:
      key: A Windows Registry key (instance of dfwinreg.WinRegistryKey).
      value_name: The name of the value.

    Returns:
      A string value if one is available, otherwise an empty string.
    """
    value = key.GetValueByName(value_name)

    if not value:
      return u''

    if not value.data or not value.DataIsString():
      return u''
    return value.data

  def GetEntries(
      self, parser_mediator, registry_key, registry_file_type=None, **kwargs):
    """Gather minimal information about system install and return an event.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
      registry_file_type: Optional string containing the Windows Registry file
                          type, e.g. NTUSER, SOFTWARE. The default is None.
    """
    install_date_value = registry_key.GetValueByName(u'InstallDate')
    if not install_date_value:
      # TODO: does this indicate a parse error?
      return

    install_raw = install_date_value.raw_data

    # TODO: move this to a function in utils with a more descriptive name
    # e.g. CopyByteStreamToInt32BigEndian.
    try:
      filetime = self.INT_STRUCT.parse(install_raw)
    except construct.FieldError:
      filetime = 0

    text_dict = {}
    text_dict[u'Owner'] = self._GetValueString(registry_key, u'RegisteredOwner')
    text_dict[u'sp'] = self._GetValueString(registry_key, u'CSDBuildNumber')
    text_dict[u'Product name'] = self._GetValueString(
        registry_key, u'ProductName')
    text_dict[u' Windows Version Information'] = u''

    event_object = windows_events.WindowsRegistryEvent(
        filetime, registry_key.path, text_dict, offset=registry_key.offset,
        usage=u'OS Install Time', registry_file_type=registry_file_type,
        urls=self.URLS)

    event_object.prodname = text_dict[u'Product name']
    event_object.source_long = u'SOFTWARE WinVersion key'
    if text_dict[u'Owner']:
      event_object.owner = text_dict[u'Owner']
    parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(WinVerPlugin)
