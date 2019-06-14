# -*- coding: utf-8 -*-
"""This file contains the Run/RunOnce key plugins for Plaso."""

from __future__ import unicode_literals

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class RunKeyEventData(events.EventData):
  """Run/RunOnce key event data attribute container.

  Attributes:
    entries (str): Run/RunOnce entries.
    key_path (str): Windows Registry key path.
  """

  DATA_TYPE = 'windows:registry:run'

  def __init__(self):
    """Initializes event data."""
    super(RunKeyEventData, self).__init__(data_type=self.DATA_TYPE)
    self.entries = None
    self.key_path = None


class AutoRunsPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for parsing user specific auto runs.

  Also see:
    http://msdn.microsoft.com/en-us/library/aa376977(v=vs.85).aspx
  """

  NAME = 'windows_run'
  DESCRIPTION = 'Parser for run and run once Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          'Run'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          'RunOnce'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          'Run'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          'RunOnce'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          'RunOnce\\Setup'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          'RunServices'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          'RunServicesOnce')])

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    entries = []
    for registry_value in registry_key.GetValues():
      # Ignore the default value.
      if not registry_value.name:
        continue

      # Ignore any value that is empty or that does not contain a string.
      if not registry_value.data or not registry_value.DataIsString():
        continue

      value_data = registry_value.GetDataAsObject()

      value_string = '{0:s}: {1:s}'.format(registry_value.name, value_data)
      entries.append(value_string)

    event_data = RunKeyEventData()
    event_data.entries = ' '.join(sorted(entries)) or None
    event_data.key_path = registry_key.path

    event = time_events.DateTimeValuesEvent(
        registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(AutoRunsPlugin)
