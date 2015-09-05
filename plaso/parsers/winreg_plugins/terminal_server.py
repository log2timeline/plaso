# -*- coding: utf-8 -*-
"""This file contains the Terminal Server Registry plugins."""

from plaso.events import windows_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'David Nides (david.nides@gmail.com)'


class TerminalServerClientPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for Terminal Server Client Connection keys."""

  NAME = u'mstsc_rdp'
  DESCRIPTION = u'Parser for Terminal Server Client Connection Registry data.'

  REG_TYPE = u'NTUSER'
  REG_KEYS = [
      u'\\Software\\Microsoft\\Terminal Server Client\\Servers',
      u'\\Software\\Microsoft\\Terminal Server Client\\Default\\AddIns\\RDPDR']

  def GetEntries(
      self, parser_mediator, key=None, registry_file_type=None,
      codepage=u'cp1252', **unused_kwargs):
    """Collect Values in Servers and return event for each one.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_file_type: Optional string containing the Windows Registry file
                          type, e.g. NTUSER, SOFTWARE. The default is None.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    for subkey in key.GetSubkeys():
      username_value = subkey.GetValue(u'UsernameHint')

      if (username_value and username_value.data and
          username_value.DataIsString()):
        username = username_value.data
      else:
        username = u'None'

      text_dict = {}
      text_dict[u'UsernameHint'] = username

      event_object = windows_events.WindowsRegistryEvent(
          key.last_written_timestamp, key.path, text_dict, offset=key.offset,
          registry_file_type=registry_file_type,
          source_append=u': RDP Connection')
      parser_mediator.ProduceEvent(event_object)


class TerminalServerClientMRUPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for Terminal Server Client Connection MRUs keys."""

  NAME = u'mstsc_rdp_mru'
  DESCRIPTION = u'Parser for Terminal Server Client MRU Registry data.'

  REG_TYPE = u'NTUSER'
  REG_KEYS = [
      u'\\Software\\Microsoft\\Terminal Server Client\\Default',
      u'\\Software\\Microsoft\\Terminal Server Client\\LocalDevices']

  def GetEntries(
      self, parser_mediator, key=None, registry_file_type=None,
      codepage=u'cp1252', **unused_kwargs):
    """Collect MRU Values and return event for each one.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_file_type: Optional string containing the Windows Registry file
                          type, e.g. NTUSER, SOFTWARE. The default is None.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    for value in key.GetValues():
      # TODO: add a check for the value naming scheme.
      # Ignore the default value.
      if not value.name:
        continue

      # Ignore any value that is empty or that does not contain a string.
      if not value.data or not value.DataIsString():
        continue

      text_dict = {}
      text_dict[value.name] = value.data

      if value.name == u'MRU0':
        timestamp = key.last_written_timestamp
      else:
        timestamp = 0

      event_object = windows_events.WindowsRegistryEvent(
          timestamp, key.path, text_dict, offset=key.offset,
          registry_file_type=registry_file_type,
          source_append=u': RDP Connection')
      parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugins([
    TerminalServerClientPlugin, TerminalServerClientMRUPlugin])
