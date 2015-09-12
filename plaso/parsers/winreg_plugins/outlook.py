# -*- coding: utf-8 -*-
"""This file contains an Outlook Registry parser."""

from plaso.events import windows_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'David Nides (david.nides@gmail.com)'


class OutlookSearchMRUPlugin(interface.WindowsRegistryPlugin):
  """Windows Registry plugin parsing Outlook Search MRU keys."""

  NAME = u'microsoft_outlook_mru'
  DESCRIPTION = u'Parser for Microsoft Outlook search MRU Registry data.'

  REG_KEYS = [
      u'\\Software\\Microsoft\\Office\\15.0\\Outlook\\Search',
      u'\\Software\\Microsoft\\Office\\14.0\\Outlook\\Search']

  # TODO: The catalog for Office 2013 (15.0) contains binary values not
  # dword values. Check if Office 2007 and 2010 have the same. Re-enable the
  # plug-ins once confirmed and OutlookSearchMRUPlugin has been extended to
  # handle the binary data or create a OutlookSearchCatalogMRUPlugin.
  # Registry keys for:
  #   MS Outlook 2007 Search Catalog:
  #     '\\Software\\Microsoft\\Office\\12.0\\Outlook\\Catalog'
  #   MS Outlook 2010 Search Catalog:
  #     '\\Software\\Microsoft\\Office\\14.0\\Outlook\\Search\\Catalog'
  #   MS Outlook 2013 Search Catalog:
  #     '\\Software\\Microsoft\\Office\\15.0\\Outlook\\Search\\Catalog'

  REG_TYPE = u'NTUSER'

  _SOURCE_APPEND = u': PST Paths'

  def GetEntries(
      self, parser_mediator, registry_key, registry_file_type=None, **kwargs):
    """Collect the values under Outlook and return event for each one.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
      registry_file_type: Optional string containing the Windows Registry file
                          type, e.g. NTUSER, SOFTWARE. The default is None.
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
      values_dict[registry_value.name] = u'0x{0:08x}'.format(
          registry_value.data)

    event_object = windows_events.WindowsRegistryEvent(
        registry_key.last_written_time, registry_key.path, values_dict,
        offset=registry_key.offset, registry_file_type=registry_file_type,
        source_append=self._SOURCE_APPEND)
    parser_mediator.ProduceEvent(event_object)


winreg.WinRegistryParser.RegisterPlugin(OutlookSearchMRUPlugin)
