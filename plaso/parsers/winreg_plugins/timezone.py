# -*- coding: utf-8 -*-
"""Plug-in to collect information about the Windows timezone settings."""

from __future__ import unicode_literals

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class WindowsTimezoneSettingsEventData(events.EventData):
  """Timezone settings event data attribute container.

  Attributes:
    configuration (str): timezone configuration.
    key_path (str): Windows Registry key path.
  """

  DATA_TYPE = 'windows:registry:timezone'

  def __init__(self):
    """Initializes event data."""
    super(WindowsTimezoneSettingsEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.configuration = None
    self.key_path = None


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

    configuration = []
    for value_name in self._VALUE_NAMES:
      registry_value = registry_key.GetValueByName(value_name)
      if not registry_value:
        continue

      value = registry_value.GetDataAsObject()
      if value is None:
        continue

      configuration.append('{0:s}: {1!s}'.format(registry_value.name, value))

    event_data = WindowsTimezoneSettingsEventData()
    event_data.configuration = ' '.join(sorted(configuration)) or None
    event_data.key_path = registry_key.path

    event = time_events.DateTimeValuesEvent(
        registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(WinRegTimezonePlugin)
