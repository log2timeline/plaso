# -*- coding: utf-8 -*-
"""Plug-in to collect the Less Frequently Used Keys."""

from plaso.events import windows_events
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

  def GetEntries(self, parser_mediator, registry_key, **kwargs):
    """Gather the BootVerification key values and return one event for all.

    This key is rare, so its presence is suspect.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
    """
    values_dict = {}
    for registry_value in registry_key.GetValues():
      value_name = registry_value.name or u'(default)'
      values_dict[value_name] = registry_value.GetDataAsObject()

    event_object = windows_events.WindowsRegistryEvent(
        registry_key.last_written_time, registry_key.path, values_dict,
        offset=registry_key.offset, urls=self.URLS)
    parser_mediator.ProduceEvent(event_object)


class BootExecutePlugin(interface.WindowsRegistryPlugin):
  """Plug-in to collect the BootExecute Value from the Session Manager key."""

  NAME = u'windows_boot_execute'
  DESCRIPTION = u'Parser for Boot Execution Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\'
          u'Session Manager')])

  URLS = [u'http://technet.microsoft.com/en-us/library/cc963230.aspx']

  def GetEntries(self, parser_mediator, registry_key, **kwargs):
    """Gather the BootExecute Value, compare to default, return event.

    The rest of the values in the Session Manager key are in a separate event.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
    """
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
          parser_mediator.ProduceParseError(error_string)

        # TODO: why does this have a separate event object? Remove this.
        value_dict = {u'BootExecute': value_string}
        event_object = windows_events.WindowsRegistryEvent(
            registry_key.last_written_time, registry_key.path, value_dict,
            offset=registry_key.offset, urls=self.URLS)
        parser_mediator.ProduceEvent(event_object)

      else:
        values_dict[value_name] = registry_value.GetDataAsObject()

    event_object = windows_events.WindowsRegistryEvent(
        registry_key.last_written_time, registry_key.path, values_dict,
        offset=registry_key.offset, urls=self.URLS)
    parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugins([
    BootVerificationPlugin, BootExecutePlugin])
