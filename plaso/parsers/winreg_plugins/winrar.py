# -*- coding: utf-8 -*-
"""This file contains a Windows Registry plugin for WinRAR Registry key."""

import re

from plaso.events import windows_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'David Nides (david.nides@gmail.com)'


class WinRarHistoryPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for parsing WinRAR History keys."""

  NAME = u'winrar_mru'
  DESCRIPTION = u'Parser for WinRAR History Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\WinRAR\\ArcHistory'),
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\WinRAR\\DialogEditHistory\\ArcName'),
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\WinRAR\\DialogEditHistory\\ExtrPath')])

  _RE_VALUE_NAME = re.compile(r'^[0-9]+$', re.I)
  _SOURCE_APPEND = u': WinRAR History'

  def GetEntries(self, parser_mediator, registry_key, **kwargs):
    """Extracts event objects from a WinRAR ArcHistory key.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      registry_key: a Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
    """
    values_dict = {}
    for registry_value in registry_key.GetValues():
      # Ignore any value not in the form: '[0-9]+'.
      if (not registry_value.name or
          not self._RE_VALUE_NAME.search(registry_value.name)):
        continue

      # Ignore any value that is empty or that does not contain a string.
      if not registry_value.data or not registry_value.DataIsString():
        continue

      values_dict[registry_value.name] = registry_value.GetDataAsObject()

    event_object = windows_events.WindowsRegistryEvent(
        registry_key.last_written_time, registry_key.path, values_dict,
        offset=registry_key.offset, source_append=self._SOURCE_APPEND)
    parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(WinRarHistoryPlugin)
