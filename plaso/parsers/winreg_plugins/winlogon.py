# -*- coding: utf-8 -*-
"""This file contains the Winlogon Registry plugin."""

from plaso.containers import events
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class WinlogonEventData(events.EventData):
  """Winlogon event data attribute container.

  Attributes:
    application (str): Winlogon application.
    command (str): Winlogon command.
    handler (str): Winlogon handler.
    key_path (str): Windows Registry key path.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
    trigger (str): Winlogon trigger.
  """

  DATA_TYPE = 'windows:registry:winlogon'

  def __init__(self):
    """Initializes event data."""
    super(WinlogonEventData, self).__init__(data_type=self.DATA_TYPE)
    self.application = None
    self.command = None
    self.handler = None
    self.key_path = None
    self.last_written_time = None
    self.trigger = None


class WinlogonPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for parsing the Winlogon key."""

  NAME = 'winlogon'
  DATA_FORMAT = 'Windows log-on Registry data'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion'
          '\\Winlogon')])

  # Sort the value names to ensure event_data is generated in a deterministic
  # manner.
  _LOGON_APPLICATIONS = sorted([
      'Shell', 'Userinit', 'AppSetup', 'GinaDLL', 'System', 'VmApplet',
      'taskman', 'UIHost'])

  _TRIGGER_VALUE_NAMES = sorted([
      'Lock', 'Logoff', 'Logon', 'Shutdown', 'SmartCardLogonNotify',
      'StartScreenSaver', 'StartShell', 'Startup', 'StopScreenSaver',
      'Unlock'])

  def _ParseRegisteredDLLs(self, parser_mediator, notify_subkey):
    """Parses the registered DLLs that receive event notifications.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      notify_subkey (dfwinreg.WinRegistryKey): Notify Windows Registry subkey.
    """
    for subkey in notify_subkey.GetSubkeys():
      for value_name in self._TRIGGER_VALUE_NAMES:
        handler_value = subkey.GetValueByName(value_name)
        if not handler_value:
          # TODO: generate extraction warning.
          continue

        # TODO: check data type handler.

        event_data = WinlogonEventData()
        event_data.application = subkey.name
        event_data.command = self._GetValueFromKey(subkey, 'DllName')
        event_data.handler = handler_value.GetDataAsObject()
        event_data.key_path = subkey.path
        event_data.last_written_time = subkey.last_written_time
        # TODO: refactor make trigger a list of value names.
        event_data.trigger = value_name

        parser_mediator.ProduceEventData(event_data)

  def _ParseLogonApplications(self, parser_mediator, registry_key):
    """Parses the registered logon applications.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    for application in self._LOGON_APPLICATIONS:
      command_value = registry_key.GetValueByName(application)
      if not command_value:
        # TODO: generate extraction warning.
        continue

      event_data = WinlogonEventData()
      event_data.application = application
      # TODO: refactor make command a list of command values.
      event_data.command = command_value.GetDataAsObject()
      event_data.key_path = registry_key.path
      event_data.last_written_time = registry_key.last_written_time
      event_data.trigger = 'Logon'

      parser_mediator.ProduceEventData(event_data)

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    self._ParseLogonApplications(parser_mediator, registry_key)

    notify_subkey = registry_key.GetSubkeyByName('Notify')
    if notify_subkey:
      self._ParseRegisteredDLLs(parser_mediator, notify_subkey)


winreg_parser.WinRegistryParser.RegisterPlugin(WinlogonPlugin)
