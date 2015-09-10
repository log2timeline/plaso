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

  REG_TYPE = u'SYSTEM'
  REG_KEYS = [u'\\{current_control_set}\\Control\\TimeZoneInformation']
  URLS = []

  _WIN_TIMEZONE_VALUE_NAMES = frozenset([
      u'ActiveTimeBias', u'Bias', u'DaylightBias', u'DaylightName',
      u'DynamicDaylightTimeDisabled', u'StandardBias', u'StandardName',
      u'TimeZoneKeyName'])

  def _GetValueData(self, value_name, key):
    """Retrieves the value data.

    Given the Registry key and the value_name it returns the data in the value
    or None if value_name does not exist.

    Args:
      value_name: the name of the value.
      key: Registry key (instance of dfwinreg.WinRegistryKey).

    Returns:
      The data inside a Windows Registry value or None.
    """
    value = key.GetValueByName(value_name)
    if value:
      return value.data

  def GetEntries(
      self, parser_mediator, registry_key, registry_file_type=None, **kwargs):
    """Collect values and return an event.

    Args:
      parser_mediator: A parser context object (instance of ParserContext).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
      registry_file_type: Optional string containing the Windows Registry file
                          type, e.g. NTUSER, SOFTWARE. The default is None.
    """
    if registry_key is None:
      return

    text_dict = {}
    for value_name in self._WIN_TIMEZONE_VALUE_NAMES:
      text_dict[value_name] = self._GetValueData(value_name, registry_key)

    event_object = windows_events.WindowsRegistryEvent(
        registry_key.last_written_time, registry_key.path, text_dict,
        offset=registry_key.offset, registry_file_type=registry_file_type)
    parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(WinRegTimezonePlugin)
