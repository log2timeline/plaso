# -*- coding: utf-8 -*-
"""This file contains the Winlogon Registry plugin."""

from plaso.containers import windows_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class WinlogonPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for parsing the Winlogon key."""

  NAME = u'winlogon'
  DESCRIPTION = u'Parser for winlogon Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion'
          u'\\Winlogon')])

  _TRIGGERS = [
      u'Lock', u'Logoff', u'Logon', u'Shutdown', u'SmartCardLogonNotify',
      u'StartScreenSaver', u'StartShell', u'Startup', u'StopScreenSaver',
      u'Unlock']

  _LOGON_APPLICATIONS = [
      u'Shell', u'Userinit', u'AppSetup', u'GinaDLL', u'System', u'VmApplet',
      u'taskman', u'UIHost']

  def _ParseRegisteredDLLs(self, parser_mediator, registry_key):
    """Parses the registered DLLs that receive event notifications.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
    """
    notify_key = registry_key.GetSubkeyByName(u'Notify')
    if not notify_key:
      return

    for subkey in notify_key.GetSubkeys():
      for trigger in self._TRIGGERS:
        handler_value = subkey.GetValueByName(trigger)
        if handler_value:
          values_dict = {
              u'Application': subkey.name,
              u'Handler': handler_value.GetDataAsObject(),
              u'Trigger': trigger}

          command_value = subkey.GetValueByName(u'DllName')
          if command_value:
            values_dict[u'Command'] = command_value.GetDataAsObject()

          event_object = windows_events.WindowsRegistryEvent(
              subkey.last_written_time, subkey.path, values_dict,
              offset=subkey.offset, source_append=u': Winlogon')
          parser_mediator.ProduceEvent(event_object)

  def _ParseLogonApplications(self, parser_mediator, registry_key):
    """Parses the registered logon applications.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
    """
    for application in self._LOGON_APPLICATIONS:
      command_value = registry_key.GetValueByName(application)
      if command_value:
        values_dict = {
            u'Application': application,
            u'Command': command_value.GetDataAsObject(),
            u'Trigger': u'Logon'}
        event_object = windows_events.WindowsRegistryEvent(
            registry_key.last_written_time, registry_key.path, values_dict,
            offset=registry_key.offset, source_append=u': Winlogon')
        parser_mediator.ProduceEvent(event_object)

  def GetEntries(self, parser_mediator, registry_key, **kwargs):
    """Retrieves information from the Winlogon registry key.

    Args:
        parser_mediator: A parser mediator object (instance of ParserMediator).
        registry_key: A Windows Registry key (instance of
                      dfwinreg.WinRegistryKey).
    """
    self._ParseLogonApplications(parser_mediator, registry_key)
    self._ParseRegisteredDLLs(parser_mediator, registry_key)


winreg.WinRegistryParser.RegisterPlugin(WinlogonPlugin)
