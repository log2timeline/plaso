# -*- coding: utf-8 -*-
"""This file contains the Run/RunOnce Key plugins for Plaso."""

from plaso.containers import windows_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class AutoRunsPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for parsing user specific auto runs."""

  NAME = u'windows_run'
  DESCRIPTION = u'Parser for run and run once Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          u'Run'),
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          u'RunOnce'),
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          u'Run'),
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          u'RunOnce'),
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          u'RunOnce\\Setup'),
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          u'RunServices'),
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          u'RunServicesOnce')])

  URLS = [u'http://msdn.microsoft.com/en-us/library/aa376977(v=vs.85).aspx']

  _SOURCE_APPEND = u': Run Key'

  def GetEntries(self, parser_mediator, registry_key, **kwargs):
    """Collect the Values under the Run Key and return an event for each one.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
    """
    for registry_value in registry_key.GetValues():
      # Ignore the default value.
      if not registry_value.name:
        continue

      # Ignore any value that is empty or that does not contain a string.
      if not registry_value.data or not registry_value.DataIsString():
        continue

      values_dict = {registry_value.name: registry_value.GetDataAsObject()}
      event_object = windows_events.WindowsRegistryEvent(
          registry_key.last_written_time, registry_key.path, values_dict,
          offset=registry_key.offset, source_append=self._SOURCE_APPEND,
          urls=self.URLS)
      parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(AutoRunsPlugin)
