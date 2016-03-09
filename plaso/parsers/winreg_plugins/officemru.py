# -*- coding: utf-8 -*-
"""This file contains a parser for MS Office MRUs for Plaso."""

import re

from plaso.containers import windows_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'David Nides (david.nides@gmail.com)'


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
    mru_values_dict = {}
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
        parser_mediator.ProduceParseError((
            u'unable to convert filetime string to an integer for '
            u'value: {0:s}.').format(registry_value.name))
        continue

      mru_values_dict[registry_value.name] = value_string

      # TODO: change into a separate event object.
      values_dict = {registry_value.name: value_string}
      event_object = windows_events.WindowsRegistryEvent(
          filetime, registry_key.path, values_dict,
          offset=registry_key.offset, source_append=self._SOURCE_APPEND)
      parser_mediator.ProduceEvent(event_object)

    event_object = windows_events.WindowsRegistryEvent(
        registry_key.last_written_time, registry_key.path, mru_values_dict,
        offset=registry_key.offset, source_append=self._SOURCE_APPEND)
    parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(OfficeMRUPlugin)
