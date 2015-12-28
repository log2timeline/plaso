# -*- coding: utf-8 -*-
"""Plug-in to collect information about the Windows timezone settings."""

from plaso.events import windows_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class WinRegTimezonePlugin(interface.WindowsRegistryPlugin):
  """Plug-in to collect information about the Windows timezone settings."""

  NAME = u'windows_timezone'
  DESCRIPTION = u'Parser for Windows timezone settings.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\'
          u'TimeZoneInformation')])

  URLS = []

  _VALUE_NAMES = frozenset([
      u'ActiveTimeBias', u'Bias', u'DaylightBias', u'DaylightName',
      u'DynamicDaylightTimeDisabled', u'StandardBias', u'StandardName',
      u'TimeZoneKeyName'])

  def _GetValueData(self, registry_key, value_name):
    """Retrieves the value data.

    Given the Registry key and the value_name it returns the data in the value
    or None if value_name does not exist.

    Args:
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
      value_name: the name of the value.

    Returns:
      The data inside a Windows Registry value or None.
    """
    registry_value = registry_key.GetValueByName(value_name)
    if registry_value:
      return registry_value.GetDataAsObject()

  def GetEntries(self, parser_mediator, registry_key, **kwargs):
    """Collect values and return an event.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
    """
    if registry_key is None:
      return

    values_dict = {}
    for value_name in self._VALUE_NAMES:
      value_data = self._GetValueData(registry_key, value_name)
      if value_data is None:
        continue
      values_dict[value_name] = value_data

    event_object = windows_events.WindowsRegistryEvent(
        registry_key.last_written_time, registry_key.path, values_dict,
        offset=registry_key.offset)
    parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(WinRegTimezonePlugin)
