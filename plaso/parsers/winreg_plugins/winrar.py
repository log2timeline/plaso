# -*- coding: utf-8 -*-
"""This file contains a WinRAR history Windows Registry plugin."""

import re

from plaso.containers import events
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class WinRARHistoryEventData(events.EventData):
  """WinRAR history event data attribute container.

  Attributes:
    entries (str): archive history entries.
    key_path (str): Windows Registry key path.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
  """

  DATA_TYPE = 'winrar:history'

  def __init__(self):
    """Initializes event data."""
    super(WinRARHistoryEventData, self).__init__(data_type=self.DATA_TYPE)
    self.entries = None
    self.key_path = None
    self.last_written_time = None


class WinRARHistoryPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for parsing WinRAR History keys."""

  NAME = 'winrar_mru'
  DATA_FORMAT = 'WinRAR History Registry data'

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
          and other components, such as storage and dfVFS.
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
    event_data.last_written_time = registry_key.last_written_time

    parser_mediator.ProduceEventData(event_data)


winreg_parser.WinRegistryParser.RegisterPlugin(WinRARHistoryPlugin)
