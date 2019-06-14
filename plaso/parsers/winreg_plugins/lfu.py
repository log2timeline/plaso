# -*- coding: utf-8 -*-
"""Plug-in to collect the Less Frequently Used Keys."""

from __future__ import unicode_literals

from plaso.containers import events
from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class WindowsBootExecuteEventData(events.EventData):
  """Windows Boot Execute event data attribute container.

  Attributes:
    key_path (str): Windows Registry key path.
    value (str): boot execute value, contains the value obtained from
        the BootExecute Registry value.
  """

  DATA_TYPE = 'windows:registry:boot_execute'

  def __init__(self):
    """Initializes event data."""
    super(WindowsBootExecuteEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.key_path = None
    self.value = None


class WindowsBootVerificationEventData(events.EventData):
  """Windows Boot Verification event data attribute container.

  Attributes:
    image_path (str): location of the boot verification executable, contains
        the value obtained from the ImagePath Registry value.
    key_path (str): Windows Registry key path.
  """

  DATA_TYPE = 'windows:registry:boot_verification'

  def __init__(self):
    """Initializes event data."""
    super(WindowsBootVerificationEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.image_path = None
    self.key_path = None


class BootVerificationPlugin(interface.WindowsRegistryPlugin):
  """Plug-in to collect the Boot Verification Key.

  Also see:
    http://technet.microsoft.com/en-us/library/cc782537(v=ws.10).aspx
  """

  NAME = 'windows_boot_verify'
  DESCRIPTION = 'Parser for Boot Verification Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\'
          'BootVerificationProgram')])

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    values_dict = self._GetValuesFromKey(registry_key)
    image_path = None
    for name, value in dict(values_dict).items():
      if name.lower() == 'imagepath':
        image_path = value
        del values_dict[name]

    if image_path:
      event_data = WindowsBootVerificationEventData()
      event_data.key_path = registry_key.path
      event_data.image_path = image_path

      event = time_events.DateTimeValuesEvent(
          registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    if values_dict:
      event_data = windows_events.WindowsRegistryEventData()
      event_data.key_path = registry_key.path
      event_data.values = ' '.join([
          '{0:s}: {1!s}'.format(name, value)
          for name, value in sorted(values_dict.items())])

      event = time_events.DateTimeValuesEvent(
          registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)


class BootExecutePlugin(interface.WindowsRegistryPlugin):
  """Plug-in to collect the BootExecute Value from the Session Manager key.

  Also see:
    http://technet.microsoft.com/en-us/library/cc963230.aspx
  """

  NAME = 'windows_boot_execute'
  DESCRIPTION = 'Parser for Boot Execution Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\'
          'Session Manager')])

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    values_dict = self._GetValuesFromKey(registry_key)
    boot_execute = None
    for name, value in dict(values_dict).items():
      if name.lower() == 'bootexecute':
        boot_execute = value
        del values_dict[name]

    if boot_execute:
      registry_value = registry_key.GetValueByName('BootExecute')

      # MSDN: claims that the data type of this value is REG_BINARY
      # although REG_MULTI_SZ is known to be used as well.
      if (not registry_value.DataIsString() and
          not registry_value.DataIsMultiString() and
          not registry_value.DataIsBinaryData()):
        error_string = (
            'Key: {0:s}, value: BootExecute: unsupported value data type: '
            '{1:s}.').format(
                registry_key.path, registry_value.data_type_string)
        parser_mediator.ProduceExtractionWarning(error_string)

      else:
        event_data = WindowsBootExecuteEventData()
        event_data.key_path = registry_key.path
        event_data.value = boot_execute

        event = time_events.DateTimeValuesEvent(
            registry_key.last_written_time,
            definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)

    if values_dict:
      event_data = windows_events.WindowsRegistryEventData()
      event_data.key_path = registry_key.path
      event_data.values = ' '.join([
          '{0:s}: {1!s}'.format(name, value)
          for name, value in sorted(values_dict.items())])

      event = time_events.DateTimeValuesEvent(
          registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugins([
    BootVerificationPlugin, BootExecutePlugin])
