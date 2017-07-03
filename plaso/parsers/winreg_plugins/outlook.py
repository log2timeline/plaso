# -*- coding: utf-8 -*-
"""This file contains an Outlook Registry parser."""

from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'David Nides (david.nides@gmail.com)'


class OutlookSearchMRUPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin parsing Outlook Search MRU keys."""

  NAME = u'microsoft_outlook_mru'
  DESCRIPTION = u'Parser for Microsoft Outlook search MRU Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\14.0\\Outlook\\'
          u'Search'),
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\15.0\\Outlook\\'
          u'Search')])

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

  _SOURCE_APPEND = u': PST Paths'

  def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
    """
    values_dict = {}
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
      values_dict[registry_value.name] = u'0x{0:08x}'.format(value_integer)

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = registry_key.path
    event_data.offset = registry_key.offset
    event_data.regvalue = values_dict
    event_data.source_append = self._SOURCE_APPEND

    event = time_events.DateTimeValuesEvent(
        registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


winreg.WinRegistryParser.RegisterPlugin(OutlookSearchMRUPlugin)
