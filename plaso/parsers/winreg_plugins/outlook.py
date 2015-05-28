# -*- coding: utf-8 -*-
"""This file contains an Outlook Registry parser."""

from plaso.events import windows_events
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


__author__ = 'David Nides (david.nides@gmail.com)'


class OutlookSearchMRUPlugin(interface.KeyPlugin):
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

  def GetEntries(
      self, parser_mediator, key=None, registry_type=None, codepage=u'cp1252',
      **unused_kwargs):
    """Collect the values under Outlook and return event for each one.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
    """
    value_index = 0
    for value in key.GetValues():
      # Ignore the default value.
      if not value.name:
        continue

      # Ignore any value that is empty or that does not contain an integer.
      if not value.data or not value.DataIsInteger():
        continue

      # TODO: change this 32-bit integer into something meaningful, for now
      # the value name is the most interesting part.
      text_dict = {}
      text_dict[value.name] = u'0x{0:08x}'.format(value.data)

      if value_index == 0:
        timestamp = key.last_written_timestamp
      else:
        timestamp = 0

      event_object = windows_events.WindowsRegistryEvent(
          timestamp, key.path, text_dict, offset=key.offset,
          registry_type=registry_type,
          source_append=u': PST Paths')
      parser_mediator.ProduceEvent(event_object)

      value_index += 1


winreg.WinRegistryParser.RegisterPlugin(OutlookSearchMRUPlugin)
