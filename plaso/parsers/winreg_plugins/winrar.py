# -*- coding: utf-8 -*-
"""This file contains a WinRAR history Windows Registry plugin."""

from __future__ import unicode_literals

import re

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class WinRARHistoryEventData(events.EventData):
  """WinRAR history event data attribute container.

  Attributes:
    entries (str): archive history entries.
    key_path (str): Windows Registry key path.
  """

  DATA_TYPE = 'winrar:history'

  def __init__(self):
    """Initializes event data."""
    super(WinRARHistoryEventData, self).__init__(data_type=self.DATA_TYPE)
    self.entries = None
    self.key_path = None


class WinRARHistoryPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for parsing WinRAR History keys."""

  NAME = 'winrar_mru'
  DESCRIPTION = 'Parser for WinRAR History Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\WinRAR\\ArcHistory'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\WinRAR\\DialogEditHistory\\ArcName'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\WinRAR\\DialogEditHistory\\ExtrPath')])

  _RE_VALUE_NAME = re.compile(r'^[0-9]+$', re.I)

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    entries = []
    for registry_value in registry_key.GetValues():
      # Ignore any value not in the form: '[0-9]+'.
      if (not registry_value.name or
          not self._RE_VALUE_NAME.search(registry_value.name)):
        continue

      # Ignore any value that is empty or that does not contain a string.
      if not registry_value.data or not registry_value.DataIsString():
        continue

      value_string = registry_value.GetDataAsObject()
      entries.append('{0:s}: {1:s}'.format(registry_value.name, value_string))

    event_data = WinRARHistoryEventData()
    event_data.entries = ' '.join(entries) or None
    event_data.key_path = registry_key.path

    event = time_events.DateTimeValuesEvent(
        registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(WinRARHistoryPlugin)
