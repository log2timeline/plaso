# -*- coding: utf-8 -*-
"""Plug-in to collect the Less Frequently Used (LFU) keys."""

from plaso.containers import events
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class WindowsBootExecuteEventData(events.EventData):
  """Windows Boot Execute event data attribute container.

  Attributes:
    key_path (str): Windows Registry key path.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
    value (str): boot execute value, contains the value obtained from
        the BootExecute Registry value.
  """

  DATA_TYPE = 'windows:registry:boot_execute'

  def __init__(self):
    """Initializes event data."""
    super(WindowsBootExecuteEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.key_path = None
    self.last_written_time = None
    self.value = None


class WindowsBootVerificationEventData(events.EventData):
  """Windows Boot Verification event data attribute container.

  Attributes:
    image_path (str): location of the boot verification executable, contains
        the value obtained from the ImagePath Registry value.
    key_path (str): Windows Registry key path.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
  """

  DATA_TYPE = 'windows:registry:boot_verification'

  def __init__(self):
    """Initializes event data."""
    super(WindowsBootVerificationEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.image_path = None
    self.key_path = None
    self.last_written_time = None


class BootVerificationPlugin(interface.WindowsRegistryPlugin):
  """Plug-in to collect the Boot Verification Key."""

  NAME = 'windows_boot_verify'
  DATA_FORMAT = 'Windows boot verification Registry data'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\'
          'BootVerificationProgram')])

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    image_path = None
    registry_value = registry_key.GetValueByName('ImagePath')
    if registry_value:
      image_path = registry_value.GetDataAsObject()

    if image_path:
      event_data = WindowsBootVerificationEventData()
      event_data.key_path = registry_key.path
      event_data.image_path = image_path
      event_data.last_written_time = registry_key.last_written_time

      parser_mediator.ProduceEventData(event_data)

    self._ProduceDefaultWindowsRegistryEvent(
        parser_mediator, registry_key, names_to_skip=['ImagePath'])


class BootExecutePlugin(interface.WindowsRegistryPlugin):
  """Plug-in to collect the BootExecute Value from the Session Manager key."""

  NAME = 'windows_boot_execute'
  DATA_FORMAT = 'Boot Execution Registry data'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\'
          'Session Manager')])

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    registry_value = registry_key.GetValueByName('BootExecute')
    if registry_value:
      # MSDN: claims that the data type of this value is REG_BINARY
      # although REG_MULTI_SZ is known to be used.
      if registry_value.DataIsString():
        boot_execute = registry_value.GetDataAsObject()
      elif registry_value.DataIsMultiString():
        value_object = registry_value.GetDataAsObject()
        boot_execute = ', '.join(value_object or [])
      else:
        boot_execute = None
        error_string = (
            'Key: {0:s}, value: BootExecute: unsupported value data type: '
            '{1:s}.').format(
                registry_key.path, registry_value.data_type_string)
        parser_mediator.ProduceExtractionWarning(error_string)

      if boot_execute:
        event_data = WindowsBootExecuteEventData()
        event_data.key_path = registry_key.path
        event_data.last_written_time = registry_key.last_written_time
        event_data.value = boot_execute

        parser_mediator.ProduceEventData(event_data)

    self._ProduceDefaultWindowsRegistryEvent(
        parser_mediator, registry_key, names_to_skip=['BootExecute'])


winreg_parser.WinRegistryParser.RegisterPlugins([
    BootVerificationPlugin, BootExecutePlugin])
