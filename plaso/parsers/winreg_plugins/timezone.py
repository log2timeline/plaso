# -*- coding: utf-8 -*-
"""Plug-in to collect information about the Windows timezone settings."""

from __future__ import unicode_literals

from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class WinRegTimezonePlugin(interface.WindowsRegistryPlugin):
  """Plug-in to collect information about the Windows timezone settings."""

  NAME = 'windows_timezone'
  DESCRIPTION = 'Parser for Windows timezone settings.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\'
          'TimeZoneInformation')])

  _VALUE_NAMES = frozenset([
      'ActiveTimeBias', 'Bias', 'DaylightBias', 'DaylightName',
      'DynamicDaylightTimeDisabled', 'StandardBias', 'StandardName',
      'TimeZoneKeyName'])


  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    if registry_key is None:
      return

    values_dict = {}
    for value_name in self._VALUE_NAMES:
      registry_value = registry_key.GetValueByName(value_name)
      if not registry_value:
        continue

      value_data = registry_value.GetDataAsObject()
      if value_data is None:
        continue

      values_dict[value_name] = value_data

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = registry_key.path
    event_data.offset = registry_key.offset
    event_data.regvalue = values_dict

    event = time_events.DateTimeValuesEvent(
        registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(WinRegTimezonePlugin)
