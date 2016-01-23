# -*- coding: utf-8 -*-
"""The default Windows Registry plugin."""

from plaso.events import windows_events
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

  def GetEntries(self, parser_mediator, registry_key, **kwargs):
    """Returns an event object based on a Registry key name and values.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
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

    event_object = windows_events.WindowsRegistryEvent(
        registry_key.last_written_time, registry_key.path, values_dict,
        offset=registry_key.offset)

    parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(DefaultPlugin)
