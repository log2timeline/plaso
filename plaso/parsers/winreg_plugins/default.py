# -*- coding: utf-8 -*-
"""The default Windows Registry plugin."""

from __future__ import unicode_literals

from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class DefaultPlugin(interface.WindowsRegistryPlugin):
  """Default plugin that extracts minimum information from every registry key.

  The default plugin will parse every registry key that is passed to it and
  extract minimum information, such as a list of available values and if
  possible content of those values. The timestamp used is the timestamp
  when the registry key was last modified.
  """

  NAME = 'winreg_default'
  DESCRIPTION = 'Parser for Registry data.'

  # TODO: merge with interface._GetValuesFromKey and remove the data types.
  def _GetValuesFromKey(self, registry_key):
    """Retrieves the values from a Windows Registry key.

    Args:
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.

    Returns:
      dict[str, object]: names and data of the values in the key. The default
          value is named "(default)".
    """
    values_dict = {}
    for registry_value in registry_key.GetValues():
      value_name = registry_value.name or '(default)'

      value_string = '[{0:s}]'.format(registry_value.data_type_string)
      if registry_value.data is None:
        value_string = '{0:s} Empty'.format(value_string)
      else:
        value_object = registry_value.GetDataAsObject()

        if registry_value.DataIsInteger():
          value_string = '{0:s} {1:d}'.format(value_string, value_object)

        elif registry_value.DataIsString():
          value_string = '{0:s} {1:s}'.format(value_string, value_object)

        elif registry_value.DataIsMultiString():
          if not value_object:
            value_string = '{0:s} []'.format(value_string)
          elif not isinstance(value_object, (list, tuple)):
            value_string = '{0:s} (unknown)'.format(value_string)
            # TODO: Add a flag or some sort of an anomaly alert.
          else:
            value_string = '{0:s} {1:s}'.format(
                value_string, ''.join(value_object))

      values_dict[value_name] = value_string

    return values_dict

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    values_dict = self._GetValuesFromKey(registry_key)

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = registry_key.path
    event_data.values = ' '.join([
        '{0:s}: {1!s}'.format(name, value)
        for name, value in sorted(values_dict.items())]) or None

    event = time_events.DateTimeValuesEvent(
        registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(DefaultPlugin)
