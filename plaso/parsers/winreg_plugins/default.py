# -*- coding: utf-8 -*-
"""The default Windows Registry plugin."""

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

  NAME = u'winreg_default'
  DESCRIPTION = u'Parser for Registry data.'

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    values_dict = {}

    if registry_key.number_of_values == 0:
      values_dict[u'Value'] = u'No values stored in key.'

    else:
      for registry_value in registry_key.GetValues():
        value_name = registry_value.name or u'(default)'

        if registry_value.data is None:
          value_string = u'[{0:s}] Empty'.format(
              registry_value.data_type_string)

        elif registry_value.DataIsString():
          value_string = registry_value.GetDataAsObject()
          value_string = u'[{0:s}] {1:s}'.format(
              registry_value.data_type_string, value_string)

        elif registry_value.DataIsInteger():
          value_integer = registry_value.GetDataAsObject()
          value_string = u'[{0:s}] {1:d}'.format(
              registry_value.data_type_string, value_integer)

        elif registry_value.DataIsMultiString():
          multi_string = registry_value.GetDataAsObject()
          if not isinstance(multi_string, (list, tuple)):
            value_string = u'[{0:s}]'.format(registry_value.data_type_string)
            # TODO: Add a flag or some sort of an anomaly alert.
          else:
            value_string = u'[{0:s}] {1:s}'.format(
                registry_value.data_type_string, u''.join(multi_string))

        else:
          value_string = u'[{0:s}]'.format(registry_value.data_type_string)

        values_dict[value_name] = value_string

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = registry_key.path
    event_data.offset = registry_key.offset
    event_data.regvalue = values_dict

    event = time_events.DateTimeValuesEvent(
        registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(DefaultPlugin)
