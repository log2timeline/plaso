# -*- coding: utf-8 -*-
"""File containing a Windows Registry plugin to parse the typed URLs key."""

import re

from plaso.containers import events
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class TypedURLsEventData(events.EventData):
  """Typed URLs event data attribute container.

  Attributes:
    entries (str): typed URLs or paths entries.
    key_path (str): Windows Registry key path.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
  """

  DATA_TYPE = 'windows:registry:typedurls'

  def __init__(self):
    """Initializes event data."""
    super(TypedURLsEventData, self).__init__(data_type=self.DATA_TYPE)
    self.entries = None
    self.key_path = None
    self.last_written_time = None


class TypedURLsPlugin(interface.WindowsRegistryPlugin):
  """A Windows Registry plugin for typed URLs history."""

  NAME = 'windows_typed_urls'
  DATA_FORMAT = 'Windows Explorer typed URLs Registry data'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Internet Explorer\\'
          'TypedURLs'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          'Explorer\\TypedPaths')])

  _RE_VALUE_NAME = re.compile(r'^url[0-9]+$', re.I)

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    entries = []
    for registry_value in registry_key.GetValues():
      value_name = registry_value.name

      # Ignore any value not in the form: 'url[0-9]+'.
      if not value_name or not self._RE_VALUE_NAME.search(value_name):
        continue

      # Ignore any value that is empty or that does not contain a string.
      if not registry_value.data or not registry_value.DataIsString():
        continue

      value_string = registry_value.GetDataAsObject()
      entries.append('{0:s}: {1:s}'.format(value_name, value_string))

    event_data = TypedURLsEventData()
    event_data.entries = ' '.join(entries) or None
    event_data.key_path = registry_key.path
    event_data.last_written_time = registry_key.last_written_time

    parser_mediator.ProduceEventData(event_data)


winreg_parser.WinRegistryParser.RegisterPlugin(TypedURLsPlugin)
