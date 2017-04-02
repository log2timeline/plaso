# -*- coding: utf-8 -*-
"""This file contains a Windows Registry plugin for WinRAR Registry key."""

import re

from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'David Nides (david.nides@gmail.com)'


class WinRarHistoryPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for parsing WinRAR History keys."""

  NAME = u'winrar_mru'
  DESCRIPTION = u'Parser for WinRAR History Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\WinRAR\\ArcHistory'),
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\WinRAR\\DialogEditHistory\\ArcName'),
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\WinRAR\\DialogEditHistory\\ExtrPath')])

  _RE_VALUE_NAME = re.compile(r'^[0-9]+$', re.I)
  _SOURCE_APPEND = u': WinRAR History'

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    values_dict = {}
    for registry_value in registry_key.GetValues():
      # Ignore any value not in the form: '[0-9]+'.
      if (not registry_value.name or
          not self._RE_VALUE_NAME.search(registry_value.name)):
        continue

      # Ignore any value that is empty or that does not contain a string.
      if not registry_value.data or not registry_value.DataIsString():
        continue

      values_dict[registry_value.name] = registry_value.GetDataAsObject()

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = registry_key.path
    event_data.offset = registry_key.offset
    event_data.regvalue = values_dict
    event_data.source_append = self._SOURCE_APPEND

    event = time_events.DateTimeValuesEvent(
        registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(WinRarHistoryPlugin)
