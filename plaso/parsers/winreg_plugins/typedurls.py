# -*- coding: utf-8 -*-
"""File containing a Windows Registry plugin to parse the typed URLs key."""

from __future__ import unicode_literals

import re

from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class TypedURLsPlugin(interface.WindowsRegistryPlugin):
  """A Windows Registry plugin for typed URLs history."""

  NAME = 'windows_typed_urls'
  DESCRIPTION = 'Parser for Explorer typed URLs Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Internet Explorer\\'
          'TypedURLs'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          'Explorer\\TypedPaths')])

  _RE_VALUE_NAME = re.compile(r'^url[0-9]+$', re.I)
  _SOURCE_APPEND = ': Typed URLs'

  # pylint 1.9.3 wants a docstring for kwargs, but this is not useful to add.
  # pylint: disable=missing-param-doc
  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    values_dict = {}
    for value in registry_key.GetValues():
      # Ignore any value not in the form: 'url[0-9]+'.
      if not value.name or not self._RE_VALUE_NAME.search(value.name):
        continue

      # Ignore any value that is empty or that does not contain a string.
      if not value.data or not value.DataIsString():
        continue

      values_dict[value.name] = value.GetDataAsObject()

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = registry_key.path
    event_data.offset = registry_key.offset
    event_data.regvalue = values_dict
    event_data.source_append = self._SOURCE_APPEND

    event = time_events.DateTimeValuesEvent(
        registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(TypedURLsPlugin)
