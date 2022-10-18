# -*- coding: utf-8 -*-
"""This file contains the Terminal Server client Windows Registry plugins."""

import re

from plaso.containers import events
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class TerminalServerClientConnectionEventData(events.EventData):
  """Terminal Server client connection event data attribute container.

  Attributes:
    entries (str): most recently used (MRU) entries.
    key_path (str): Windows Registry key path.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
    username (str): username, provided by the UsernameHint value.
  """

  DATA_TYPE = 'windows:registry:mstsc:connection'

  def __init__(self):
    """Initializes event data."""
    super(TerminalServerClientConnectionEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.entries = None
    self.key_path = None
    self.last_written_time = None
    self.username = None


class TerminalServerClientMRUEventData(events.EventData):
  """Terminal Server client MRU event data attribute container.

  Attributes:
    entries (str): most recently used (MRU) entries.
    key_path (str): Windows Registry key path.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
  """

  DATA_TYPE = 'windows:registry:mstsc:mru'

  def __init__(self):
    """Initializes event data."""
    super(TerminalServerClientMRUEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.entries = None
    self.key_path = None
    self.last_written_time = None


class TerminalServerClientPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for Terminal Server Client Connection keys."""

  NAME = 'mstsc_rdp'
  DATA_FORMAT = 'Terminal Server Client Connection Registry data'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Terminal Server Client\\'
          'Servers'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Terminal Server Client\\'
          'Default\\AddIns\\RDPDR')])

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Terminal Server Client Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    for subkey in registry_key.GetSubkeys():
      username_value = subkey.GetValueByName('UsernameHint')
      if (username_value and username_value.data and
          username_value.DataIsString()):
        username = username_value.GetDataAsObject()
      else:
        username = 'N/A'

      event_data = TerminalServerClientConnectionEventData()
      event_data.key_path = subkey.path
      event_data.last_written_time = subkey.last_written_time
      event_data.username = username

      parser_mediator.ProduceEventData(event_data)

    self._ProduceDefaultWindowsRegistryEvent(parser_mediator, registry_key)


class TerminalServerClientMRUPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for Terminal Server Client Connection MRUs keys."""

  NAME = 'mstsc_rdp_mru'
  DATA_FORMAT = 'Terminal Server Client Most Recently Used (MRU) Registry data'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Terminal Server Client\\'
          'Default'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Terminal Server Client\\'
          'LocalDevices')])

  _RE_VALUE_DATA = re.compile(r'MRU[0-9]+')

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Terminal Server Client MRU Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    entries = []
    for value in registry_key.GetValues():
      # Ignore the default value.
      if not value.name:
        continue

      # Ignore any value that is empty or that does not contain a string.
      if not value.data or not value.DataIsString():
        continue

      value_string = value.GetDataAsObject()
      entries.append('{0:s}: {1:s}'.format(value.name, value_string))

    event_data = TerminalServerClientMRUEventData()
    event_data.entries = ' '.join(entries) or None
    event_data.key_path = registry_key.path
    event_data.last_written_time = registry_key.last_written_time

    parser_mediator.ProduceEventData(event_data)


winreg_parser.WinRegistryParser.RegisterPlugins([
    TerminalServerClientPlugin, TerminalServerClientMRUPlugin])
