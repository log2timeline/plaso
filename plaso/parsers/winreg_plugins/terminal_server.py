# -*- coding: utf-8 -*-
"""This file contains the Terminal Server Registry plugins."""

import re

from plaso.events import windows_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'David Nides (david.nides@gmail.com)'


class TerminalServerClientPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for Terminal Server Client Connection keys."""

  NAME = u'mstsc_rdp'
  DESCRIPTION = u'Parser for Terminal Server Client Connection Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Microsoft\\Terminal Server Client\\'
          u'Servers'),
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Microsoft\\Terminal Server Client\\'
          u'Default\\AddIns\\RDPDR')])

  _SOURCE_APPEND = u': RDP Connection'

  def GetEntries(self, parser_mediator, registry_key, **kwargs):
    """Collect Values in Servers and return event for each one.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
    """
    mru_values_dict = {}
    for subkey in registry_key.GetSubkeys():
      username_value = subkey.GetValueByName(u'UsernameHint')

      if (username_value and username_value.data and
          username_value.DataIsString()):
        username = username_value.GetData()
      else:
        username = u'N/A'

      mru_values_dict[subkey.name] = username
      values_dict = {u'Username hint': username}

      event_object = windows_events.WindowsRegistryEvent(
          subkey.last_written_time, subkey.path, values_dict,
          offset=subkey.offset, source_append=self._SOURCE_APPEND)
      parser_mediator.ProduceEvent(event_object)

    event_object = windows_events.WindowsRegistryEvent(
        registry_key.last_written_time, registry_key.path, mru_values_dict,
        offset=registry_key.offset, source_append=self._SOURCE_APPEND)
    parser_mediator.ProduceEvent(event_object)


class TerminalServerClientMRUPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for Terminal Server Client Connection MRUs keys."""

  NAME = u'mstsc_rdp_mru'
  DESCRIPTION = u'Parser for Terminal Server Client MRU Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Microsoft\\Terminal Server Client\\'
          u'Default'),
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Microsoft\\Terminal Server Client\\'
          u'LocalDevices')])

  _RE_VALUE_DATA = re.compile(r'MRU[0-9]+')
  _SOURCE_APPEND = u': RDP Connection'

  def GetEntries(self, parser_mediator, registry_key, **kwargs):
    """Collect MRU Values and return event for each one.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
    """
    values_dict = {}
    for value in registry_key.GetValues():
      # Ignore the default value.
      if not value.name:
        continue

      # Ignore any value that is empty or that does not contain a string.
      if not value.data or not value.DataIsString():
        continue

      values_dict[value.name] = value.GetData()

    event_object = windows_events.WindowsRegistryEvent(
        registry_key.last_written_time, registry_key.path, values_dict,
        offset=registry_key.offset, source_append=self._SOURCE_APPEND)
    parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugins([
    TerminalServerClientPlugin, TerminalServerClientMRUPlugin])
