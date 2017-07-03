# -*- coding: utf-8 -*-
""""Windows Registry plugin for the Microsoft Office MRU."""

import re

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'David Nides (david.nides@gmail.com)'


class OfficeMRUWindowsRegistryEventData(events.EventData):
  """Microsoft Office MRU Windows Registry event data.

  Attributes:
    key_path (str): Windows Registry key path.
    value_string (str): MRU value.
  """
  DATA_TYPE = u'windows:registry:office_mru'

  def __init__(self):
    """Initializes event data."""
    super(OfficeMRUWindowsRegistryEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.key_path = None
    self.value_string = None


class OfficeMRUPlugin(interface.WindowsRegistryPlugin):
  """Plugin that parses Microsoft Office MRU keys."""

  NAME = u'microsoft_office_mru'
  DESCRIPTION = u'Parser for Microsoft Office MRU Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
          u'Access\\File MRU'),
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
          u'Access\\Place MRU'),
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
          u'Excel\\File MRU'),
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
          u'Excel\\Place MRU'),
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
          u'PowerPoint\\File MRU'),
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
          u'PowerPoint\\Place MRU'),
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
          u'Word\\File MRU'),
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\'
          u'Word\\Place MRU')])

  _RE_VALUE_NAME = re.compile(r'^Item [0-9]+$', re.I)

  # The Office 12 item MRU is formatted as:
  # [F00000000][T%FILETIME%]*\\%FILENAME%

  # The Office 14 item MRU is formatted as:
  # [F00000000][T%FILETIME%][O00000000]*%FILENAME%
  _RE_VALUE_DATA = re.compile(r'\[F00000000\]\[T([0-9A-Z]+)\].*\*[\\]?(.*)')

  _SOURCE_APPEND = u': Microsoft Office MRU'

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    # TODO: Test other Office versions to make sure this plugin is applicable.
    values_dict = {}
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
        parser_mediator.ProduceExtractionError((
            u'unable to convert filetime string to an integer for '
            u'value: {0:s}.').format(registry_value.name))
        continue

      event_data = OfficeMRUWindowsRegistryEventData()
      event_data.key_path = registry_key.path
      event_data.offset = registry_value.offset
      # TODO: split value string in individual values.
      event_data.value_string = value_string

      values_dict[registry_value.name] = value_string

      if not timestamp:
        date_time = dfdatetime_semantic_time.SemanticTime(u'Not set')
      else:
        date_time = dfdatetime_filetime.Filetime(timestamp=timestamp)

      # TODO: determine if this should be last written time.
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = registry_key.path
    event_data.offset = registry_key.offset
    event_data.regvalue = values_dict
    event_data.source_append = self._SOURCE_APPEND

    event = time_events.DateTimeValuesEvent(
        registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(OfficeMRUPlugin)
