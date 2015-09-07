# -*- coding: utf-8 -*-
"""This file contains a Windows Registry plugin for WinRAR Registry key."""

import re

from plaso.events import windows_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'David Nides (david.nides@gmail.com)'


class WinRarHistoryPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin for parsing WinRAR History keys."""
  # TODO: Create NTUSER.DAT test file with WinRAR data.

  NAME = u'winrar_mru'
  DESCRIPTION = u'Parser for WinRAR History Registry data.'

  REG_TYPE = u'NTUSER'
  REG_KEYS = [
      u'\\Software\\WinRAR\\DialogEditHistory\\ExtrPath',
      u'\\Software\\WinRAR\\DialogEditHistory\\ArcName',
      u'\\Software\\WinRAR\\ArcHistory']

  _RE_VALUE_NAME = re.compile(r'^[0-9]+$', re.I)

  def GetEntries(
      self, parser_mediator, key=None, registry_file_type=None,
      codepage=u'cp1252', **kwargs):
    """Collect values under WinRAR ArcHistory and return event for each one.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: Optional Registry key (instance of dfwinreg.WinRegistryKey).
           The default is None.
      registry_file_type: Optional string containing the Windows Registry file
                          type, e.g. NTUSER, SOFTWARE. The default is None.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    for value in key.GetValues():
      # Ignore any value not in the form: '[0-9]+'.
      if not value.name or not self._RE_VALUE_NAME.search(value.name):
        continue

      # Ignore any value that is empty or that does not contain a string.
      if not value.data or not value.DataIsString():
        continue

      if value.name == u'0':
        timestamp = key.last_written_timestamp
      else:
        timestamp = 0

      text_dict = {}
      text_dict[value.name] = value.data

      # TODO: shouldn't this behavior be, put all the values
      # into a single event object with the last written time of the key?
      event_object = windows_events.WindowsRegistryEvent(
          timestamp, key.path, text_dict, offset=key.offset,
          registry_file_type=registry_file_type,
          source_append=u': WinRAR History')
      parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(WinRarHistoryPlugin)
