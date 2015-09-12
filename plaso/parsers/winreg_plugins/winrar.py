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

  REG_TYPE = u'NTUSER'
  REG_KEYS = [
      u'\\Software\\WinRAR\\DialogEditHistory\\ExtrPath',
      u'\\Software\\WinRAR\\DialogEditHistory\\ArcName',
      u'\\Software\\WinRAR\\ArcHistory']

  _RE_VALUE_NAME = re.compile(r'^[0-9]+$', re.I)
  _SOURCE_APPEND = u': WinRAR History'

  def GetEntries(
      self, parser_mediator, registry_key, registry_file_type=None, **kwargs):
    """Extracts event objects from a WinRAR ArcHistory key.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      registry_key: a Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
      registry_file_type: optional string containing the Windows Registry file
                          type, e.g. NTUSER, SOFTWARE.
    """
    values_dict = {}
    for value in registry_key.GetValues():
      # Ignore any value not in the form: '[0-9]+'.
      if not value.name or not self._RE_VALUE_NAME.search(value.name):
        continue

      # Ignore any value that is empty or that does not contain a string.
      if not value.data or not value.DataIsString():
        continue

      values_dict[value.name] = value.data

    event_object = windows_events.WindowsRegistryEvent(
        registry_key.last_written_time, registry_key.path, values_dict,
        offset=registry_key.offset, registry_file_type=registry_file_type,
        source_append=self._SOURCE_APPEND)
    parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(WinRarHistoryPlugin)
