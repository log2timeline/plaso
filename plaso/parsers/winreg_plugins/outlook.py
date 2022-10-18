# -*- coding: utf-8 -*-
"""This file contains an Outlook search MRU Registry parser."""

from plaso.containers import events
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class OutlookSearchMRUEventData(events.EventData):
  """Outlook search MRU event data attribute container.

  Attributes:
    entries (str): most recently used (MRU) entries.
    key_path (str): Windows Registry key path.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
  """

  DATA_TYPE = 'windows:registry:outlook_search_mru'

  def __init__(self):
    """Initializes event data."""
    super(OutlookSearchMRUEventData, self).__init__(data_type=self.DATA_TYPE)
    self.entries = None
    self.key_path = None
    self.last_written_time = None


class OutlookSearchMRUPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin parsing Outlook Search MRU keys."""

  NAME = 'microsoft_outlook_mru'
  DATA_FORMAT = 'Microsoft Outlook search MRU Registry data'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\Outlook\\'
          'Search'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\15.0\\Outlook\\'
          'Search')])

  # TODO: The catalog for Office 2013 (15.0) contains binary values not
  # dword values. Check if Office 2007 and 2010 have the same. Re-enable the
  # plug-ins once confirmed and OutlookSearchMRUPlugin has been extended to
  # handle the binary data or create a OutlookSearchCatalogMRUPlugin.
  # Registry keys for:
  #   MS Outlook 2007 Search Catalog:
  #     'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\12.0\\Outlook\\'
  #     'Catalog'
  #   MS Outlook 2010 Search Catalog:
  #     'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\Outlook\\'
  #     'Search\\Catalog'
  #   MS Outlook 2013 Search Catalog:
  #     'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\15.0\\Outlook\\'
  #     'Search\\Catalog'

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    entries = []
    for registry_value in registry_key.GetValues():
      # Ignore the default value.
      if not registry_value.name:
        continue

      # Ignore any value that is empty or that does not contain an integer.
      if not registry_value.data or not registry_value.DataIsInteger():
        continue

      # TODO: change this 32-bit integer into something meaningful, for now
      # the value name is the most interesting part.
      value_integer = registry_value.GetDataAsObject()
      value_string = '{0:s}: 0x{1:08x}'.format(
          registry_value.name, value_integer)

      entries.append(value_string)

    event_data = OutlookSearchMRUEventData()
    event_data.entries = ' '.join(entries) or None
    event_data.key_path = registry_key.path
    event_data.last_written_time = registry_key.last_written_time

    parser_mediator.ProduceEventData(event_data)


winreg_parser.WinRegistryParser.RegisterPlugin(OutlookSearchMRUPlugin)
