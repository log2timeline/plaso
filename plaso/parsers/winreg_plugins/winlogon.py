# -*- coding: utf-8 -*-
"""This file contains the Winlogon Registry plugin."""

from __future__ import unicode_literals

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class WinlogonEventData(events.EventData):
  """Winlogon event data attribute container.

  Attributes:
    application (str): Winlogon application.
    command (str): Winlogon command.
    handler (str): Winlogon handler.
    key_path (str): Windows Registry key path.
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
    self.trigger = None


class WinlogonPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for parsing the Winlogon key."""

  NAME = 'winlogon'
  DESCRIPTION = 'Parser for winlogon Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion'
          '\\Winlogon')])

  _LOGON_APPLICATIONS = frozenset([
      'Shell', 'Userinit', 'AppSetup', 'GinaDLL', 'System', 'VmApplet',
      'taskman', 'UIHost'])

  _TRIGGERS = frozenset([
      'Lock', 'Logoff', 'Logon', 'Shutdown', 'SmartCardLogonNotify',
      'StartScreenSaver', 'StartShell', 'Startup', 'StopScreenSaver',
      'Unlock'])

  def _ParseRegisteredDLLs(self, parser_mediator, notify_subkey):
    """Parses the registered DLLs that receive event notifications.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      notify_subkey (dfwinreg.WinRegistryKey): Notify Windows Registry subkey.
    """
    for subkey in notify_subkey.GetSubkeys():
      for trigger in self._TRIGGERS:
        handler_value = subkey.GetValueByName(trigger)
        if not handler_value:
          # TODO: generate extraction warning.
          continue

        # TODO: check data type handler.

        event_data = WinlogonEventData()
        event_data.application = subkey.name
        event_data.handler = handler_value.GetDataAsObject()
        event_data.key_path = subkey.path
        event_data.trigger = trigger

        command_value = subkey.GetValueByName('DllName')
        if command_value:
          event_data.command = command_value.GetDataAsObject()

        event = time_events.DateTimeValuesEvent(
            subkey.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
        parser_mediator.ProduceEventWithEventData(event, event_data)

  def _ParseLogonApplications(self, parser_mediator, registry_key):
    """Parses the registered logon applications.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    for application in self._LOGON_APPLICATIONS:
      command_value = registry_key.GetValueByName(application)
      if not command_value:
        # TODO: generate extraction warning.
        continue

      event_data = WinlogonEventData()
      event_data.application = application
      event_data.command = command_value.GetDataAsObject()
      event_data.key_path = registry_key.path
      event_data.trigger = 'Logon'

      event = time_events.DateTimeValuesEvent(
          registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    self._ParseLogonApplications(parser_mediator, registry_key)

    notify_subkey = registry_key.GetSubkeyByName('Notify')
    if notify_subkey:
      self._ParseRegisteredDLLs(parser_mediator, notify_subkey)


winreg.WinRegistryParser.RegisterPlugin(WinlogonPlugin)
