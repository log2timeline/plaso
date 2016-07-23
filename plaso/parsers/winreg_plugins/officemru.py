# -*- coding: utf-8 -*-
""""Windows Registry plugin for the Microsoft Office MRU."""

import re

from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import eventdata
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'David Nides (david.nides@gmail.com)'


class OfficeMRUWindowsRegistryEvent(time_events.FiletimeEvent):
  """Convenience class for an Microsoft Office MRU Windows Registry event.

  Attributes:
    key_path: a string containing the Windows Registry key path.
    offset: an integer containing the data offset of the Microsoft Office MRU
            Windows Registry value.
    value_string: a string containing the MRU value.
  """
  DATA_TYPE = u'windows:registry:office_mru'

  def __init__(self, filetime, key_path, offset, value_string):
    """Initializes a Windows Registry event.

    Args:
      filetime: an integer containing a FILETIME timestamp.
      key_path: a string containing the Windows Registry key path.
      offset: an integer containing the data offset of the Microsoft Office MRU
              Windows Registry value.
      value_string: a string containing the MRU value.
    """
    # TODO: determine if this should be last written time.
    super(OfficeMRUWindowsRegistryEvent, self).__init__(
        filetime, eventdata.EventTimestamp.WRITTEN_TIME)
    self.key_path = key_path
    self.offset = offset
    self.value_string = value_string


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

  def GetEntries(self, parser_mediator, registry_key, **kwargs):
    """Collect Values under Office 2010 MRUs and return events for each one.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
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
        filetime = int(values[0][0], 16)
      except ValueError:
        parser_mediator.ProduceExtractionError((
            u'unable to convert filetime string to an integer for '
            u'value: {0:s}.').format(registry_value.name))
        continue

      values_dict[registry_value.name] = value_string

      # TODO: split value string in individual values?
      event_object = OfficeMRUWindowsRegistryEvent(
          filetime, registry_key.path, registry_value.offset, value_string)
      parser_mediator.ProduceEvent(event_object)

    event_object = windows_events.WindowsRegistryEvent(
        registry_key.last_written_time, registry_key.path, values_dict,
        offset=registry_key.offset, source_append=self._SOURCE_APPEND)
    parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(OfficeMRUPlugin)
