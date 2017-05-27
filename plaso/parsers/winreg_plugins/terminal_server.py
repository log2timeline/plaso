# -*- coding: utf-8 -*-
"""This file contains the Terminal Server Registry plugins."""

import re

from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
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

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Terminal Server Client Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    mru_values_dict = {}
    for subkey in registry_key.GetSubkeys():
      username_value = subkey.GetValueByName(u'UsernameHint')

      if (username_value and username_value.data and
          username_value.DataIsString()):
        username = username_value.GetDataAsObject()
      else:
        username = u'N/A'

      mru_values_dict[subkey.name] = username

      event_data = windows_events.WindowsRegistryEventData()
      event_data.key_path = subkey.path
      event_data.offset = subkey.offset
      event_data.regvalue = {u'Username hint': username}
      event_data.source_append = self._SOURCE_APPEND

      event = time_events.DateTimeValuesEvent(
          subkey.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = registry_key.path
    event_data.offset = registry_key.offset
    event_data.regvalue = mru_values_dict
    event_data.source_append = self._SOURCE_APPEND

    event = time_events.DateTimeValuesEvent(
        registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


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

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Terminal Server Client MRU Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    values_dict = {}
    for value in registry_key.GetValues():
      # Ignore the default value.
      if not value.name:
        continue

      # Ignore any value that is empty or that does not contain a string.
      if not value.data or not value.DataIsString():
        continue

      values_dict[value.name] = value.GetDataAsObject()

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = registry_key.path
    event_data.offset = registry_key.offset
    event_data.regvalue = values_dict
    event_data.source_append = self._SOURCE_APPEND

    event = time_events.DateTimeValuesEvent(
        registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugins([
    TerminalServerClientPlugin, TerminalServerClientMRUPlugin])
