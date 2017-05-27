# -*- coding: utf-8 -*-
"""Plug-in to collect the Less Frequently Used Keys."""

from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class BootVerificationPlugin(interface.WindowsRegistryPlugin):
  """Plug-in to collect the Boot Verification Key."""

  NAME = u'windows_boot_verify'
  DESCRIPTION = u'Parser for Boot Verification Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\'
          u'BootVerificationProgram')])

  URLS = [u'http://technet.microsoft.com/en-us/library/cc782537(v=ws.10).aspx']

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    values_dict = {}
    for registry_value in registry_key.GetValues():
      value_name = registry_value.name or u'(default)'
      values_dict[value_name] = registry_value.GetDataAsObject()

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = registry_key.path
    event_data.offset = registry_key.offset
    event_data.regvalue = values_dict
    event_data.urls = self.URLS

    event = time_events.DateTimeValuesEvent(
        registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


class BootExecutePlugin(interface.WindowsRegistryPlugin):
  """Plug-in to collect the BootExecute Value from the Session Manager key."""

  NAME = u'windows_boot_execute'
  DESCRIPTION = u'Parser for Boot Execution Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\'
          u'Session Manager')])

  URLS = [u'http://technet.microsoft.com/en-us/library/cc963230.aspx']

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = registry_key.path
    event_data.offset = registry_key.offset
    event_data.urls = self.URLS

    values_dict = {}
    for registry_value in registry_key.GetValues():
      value_name = registry_value.name or u'(default)'

      if value_name == u'BootExecute':
        # MSDN: claims that the data type of this value is REG_BINARY
        # although REG_MULTI_SZ is known to be used as well.
        if registry_value.DataIsString():
          value_string = registry_value.GetDataAsObject()

        elif registry_value.DataIsMultiString():
          value_string = u''.join(registry_value.GetDataAsObject())

        elif registry_value.DataIsBinaryData():
          value_string = registry_value.GetDataAsObject()

        else:
          value_string = u''
          error_string = (
              u'Key: {0:s}, value: {1:s}: unsupported value data type: '
              u'{2:s}.').format(
                  registry_key.path, value_name,
                  registry_value.data_type_string)
          parser_mediator.ProduceExtractionError(error_string)

        # TODO: why does this have a separate event object? Remove this.
        event_data.regvalue = {u'BootExecute': value_string}

        event = time_events.DateTimeValuesEvent(
            registry_key.last_written_time,
            definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)

      else:
        values_dict[value_name] = registry_value.GetDataAsObject()

    event_data.regvalue = values_dict

    event = time_events.DateTimeValuesEvent(
        registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugins([
    BootVerificationPlugin, BootExecutePlugin])
