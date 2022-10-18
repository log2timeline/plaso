# -*- coding: utf-8 -*-
"""Windows Registry plugin for the Microsoft Office MRU."""

import re

from dfdatetime import filetime as dfdatetime_filetime

from plaso.containers import events
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class OfficeMRUWindowsRegistryEventData(events.EventData):
  """Microsoft Office MRU Windows Registry event data.

  Attributes:
    key_path (str): Windows Registry key path.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
    value_string (str): MRU value.
  """

  DATA_TYPE = 'windows:registry:office_mru'

  def __init__(self):
    """Initializes event data."""
    super(OfficeMRUWindowsRegistryEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.key_path = None
    self.last_written_time = None
    self.value_string = None


class OfficeMRUListWindowsRegistryEventData(events.EventData):
  """Microsoft Office MRU list Windows Registry event data.

  Attributes:
    entries (str): most recently used (MRU) entries.
    key_path (str): Windows Registry key path.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
  """

  DATA_TYPE = 'windows:registry:office_mru_list'

  def __init__(self):
    """Initializes event data."""
    super(OfficeMRUListWindowsRegistryEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.entries = None
    self.key_path = None
    self.last_written_time = None


class OfficeMRUPlugin(interface.WindowsRegistryPlugin):
  """Plugin that parses Microsoft Office MRU keys."""

  NAME = 'microsoft_office_mru'
  DATA_FORMAT = 'Microsoft Office MRU Registry data'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
          'Access\\File MRU'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
          'Access\\Place MRU'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
          'Excel\\File MRU'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
          'Excel\\Place MRU'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
          'PowerPoint\\File MRU'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
          'PowerPoint\\Place MRU'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
          'Word\\File MRU'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
          'Word\\Place MRU')])

  _RE_VALUE_NAME = re.compile(r'^Item [0-9]+$', re.I)

  # The Office 12 item MRU is formatted as:
  # [F00000000][T%FILETIME%]*\\%FILENAME%

  # The Office 14 item MRU is formatted as:
  # [F00000000][T%FILETIME%][O00000000]*%FILENAME%
  _RE_VALUE_DATA = re.compile(r'\[F00000000\]\[T([0-9A-Z]+)\].*\*[\\]?(.*)')

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    # TODO: Test other Office versions to make sure this plugin is applicable.
    entries = []
    for registry_value in registry_key.GetValues():
      # Ignore any value not in the form: 'Item [0-9]+'.
      if not registry_value.name or not self._RE_VALUE_NAME.search(
          registry_value.name):
        continue

      # Ignore any value that is empty or that does not contain a string.
      if not registry_value.data or not registry_value.DataIsString():
        continue

      value_string = registry_value.GetDataAsObject()
      values = self._RE_VALUE_DATA.findall(value_string)

      # Values will contain a list containing a tuple containing 2 values.
      if len(values) != 1 or len(values[0]) != 2:
        continue

      try:
        timestamp = int(values[0][0], 16)
      except ValueError:
        parser_mediator.ProduceExtractionWarning((
            'unable to convert filetime string to an integer for '
            'value: {0:s}.').format(registry_value.name))
        continue

      event_data = OfficeMRUWindowsRegistryEventData()
      event_data.key_path = registry_key.path
      # TODO: split value string in individual values.
      event_data.value_string = value_string

      if timestamp:
        event_data.last_written_time = dfdatetime_filetime.Filetime(
            timestamp=timestamp)

      parser_mediator.ProduceEventData(event_data)

      entries.append('{0:s}: {1:s}'.format(registry_value.name, value_string))

    event_data = OfficeMRUListWindowsRegistryEventData()
    event_data.entries = ' '.join(entries) or None
    event_data.key_path = registry_key.path
    event_data.last_written_time = registry_key.last_written_time

    parser_mediator.ProduceEventData(event_data)


winreg_parser.WinRegistryParser.RegisterPlugin(OfficeMRUPlugin)
