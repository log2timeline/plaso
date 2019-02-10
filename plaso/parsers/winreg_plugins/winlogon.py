# -*- coding: utf-8 -*-
"""This file contains the Winlogon Registry plugin."""

from __future__ import unicode_literals

from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


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

  def _ParseRegisteredDLLs(self, parser_mediator, registry_key):
    """Parses the registered DLLs that receive event notifications.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    notify_key = registry_key.GetSubkeyByName('Notify')
    if not notify_key:
      return

    for subkey in notify_key.GetSubkeys():
      for trigger in self._TRIGGERS:
        handler_value = subkey.GetValueByName(trigger)
        if not handler_value:
          continue

        values_dict = {
            'Application': subkey.name,
            'Handler': handler_value.GetDataAsObject(),
            'Trigger': trigger}

        command_value = subkey.GetValueByName('DllName')
        if command_value:
          values_dict['Command'] = command_value.GetDataAsObject()

        event_data = windows_events.WindowsRegistryEventData()
        event_data.key_path = subkey.path
        event_data.offset = subkey.offset
        event_data.regvalue = values_dict
        event_data.source_append = ': Winlogon'

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
        continue

      values_dict = {
          'Application': application,
          'Command': command_value.GetDataAsObject(),
          'Trigger': 'Logon'}

      event_data = windows_events.WindowsRegistryEventData()
      event_data.key_path = registry_key.path
      event_data.offset = registry_key.offset
      event_data.regvalue = values_dict
      event_data.source_append = ': Winlogon'

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
    self._ParseRegisteredDLLs(parser_mediator, registry_key)


winreg.WinRegistryParser.RegisterPlugin(WinlogonPlugin)
