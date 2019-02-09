# -*- coding: utf-8 -*-
"""This file contains a MRUList Registry plugin."""

from __future__ import unicode_literals

import abc

from dtfabric.runtime import data_maps as dtfabric_data_maps

from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.lib import errors
from plaso.parsers import logger
from plaso.parsers import winreg
from plaso.parsers.shared import shell_items
from plaso.parsers.winreg_plugins import dtfabric_plugin
from plaso.parsers.winreg_plugins import interface


class MRUListStringRegistryKeyFilter(
    interface.WindowsRegistryKeyWithValuesFilter):
  """Windows Registry key with values filter."""

  _IGNORE_KEY_PATH_SUFFIXES = frozenset([
      '\\Explorer\\DesktopStreamMRU'.upper()])

  _VALUE_NAMES = ('a', 'MRUList')

  def __init__(self):
    """Initializes a Windows Registry key filter object."""
    super(MRUListStringRegistryKeyFilter, self).__init__(self._VALUE_NAMES)

  def Match(self, registry_key):
    """Determines if a Windows Registry key matches the filter.

    Args:
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.

    Returns:
      bool: True if the Windows Registry key matches the filter.
    """
    key_path = registry_key.path.upper()
    # Prevent this filter matching non-string MRUList values.
    for ignore_key_path_suffix in self._IGNORE_KEY_PATH_SUFFIXES:
      if key_path.endswith(ignore_key_path_suffix):
        return False

    return super(MRUListStringRegistryKeyFilter, self).Match(registry_key)


class BaseMRUListWindowsRegistryPlugin(
    dtfabric_plugin.DtFabricBaseWindowsRegistryPlugin):
  """Class for common MRUList Windows Registry plugin functionality."""

  _SOURCE_APPEND = ': MRU List'

  _DEFINITION_FILE = 'mru.yaml'

  @abc.abstractmethod
  def _ParseMRUListEntryValue(
      self, parser_mediator, registry_key, entry_index, entry_letter, **kwargs):
    """Parses the MRUList entry value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key that contains
           the MRUList value.
      entry_index (int): MRUList entry index.
      entry_letter (str): character value representing the entry.

    Returns:
      str: MRUList entry value.
    """

  def _ParseMRUListValue(self, registry_key):
    """Parses the MRUList value in a given Registry key.

    Args:
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key that contains
           the MRUList value.

    Returns:
      mrulist_entries: MRUList entries or None if not available.
    """
    mrulist_value = registry_key.GetValueByName('MRUList')

    # The key exists but does not contain a value named "MRUList".
    if not mrulist_value:
      return None

    mrulist_entries_map = self._GetDataTypeMap('mrulist_entries')

    context = dtfabric_data_maps.DataTypeMapContext(values={
        'data_size': len(mrulist_value.data)})

    return self._ReadStructureFromByteStream(
        mrulist_value.data, 0, mrulist_entries_map, context=context)

  def _ParseMRUListKey(self, parser_mediator, registry_key, codepage='cp1252'):
    """Extract event objects from a MRUList Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      codepage (Optional[str]): extended ASCII string codepage.
    """
    try:
      mrulist = self._ParseMRUListValue(registry_key)
    except (ValueError, errors.ParseError) as exception:
      parser_mediator.ProduceExtractionError(
          'unable to parse MRUList value with error: {0!s}'.format(exception))
      return

    if not mrulist:
      return

    values_dict = {}
    found_terminator = False
    for entry_index, entry_letter in enumerate(mrulist):
      # The MRU list is terminated with '\0' (0x0000).
      if entry_letter == 0:
        break

      if found_terminator:
        parser_mediator.ProduceExtractionError((
            'found additional MRUList entries after terminator in key: '
            '{0:s}.').format(registry_key.path))

        # Only create one parser error per terminator.
        found_terminator = False

      entry_letter = chr(entry_letter)

      value_string = self._ParseMRUListEntryValue(
          parser_mediator, registry_key, entry_index, entry_letter,
          codepage=codepage)

      value_text = 'Index: {0:d} [MRU Value {1:s}]'.format(
          entry_index + 1, entry_letter)

      values_dict[value_text] = value_string

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = registry_key.path
    event_data.offset = registry_key.offset
    event_data.regvalue = values_dict
    event_data.source_append = self._SOURCE_APPEND

    event = time_events.DateTimeValuesEvent(
        registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


class MRUListStringWindowsRegistryPlugin(BaseMRUListWindowsRegistryPlugin):
  """Windows Registry plugin to parse a string MRUList."""

  NAME = 'mrulist_string'
  DESCRIPTION = 'Parser for Most Recently Used (MRU) Registry data.'

  FILTERS = frozenset([MRUListStringRegistryKeyFilter()])

  URLS = ['http://forensicartifacts.com/tag/mru/']

  def _ParseMRUListEntryValue(
      self, parser_mediator, registry_key, entry_index, entry_letter, **kwargs):
    """Parses the MRUList entry value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key that contains
           the MRUList value.
      entry_index (int): MRUList entry index.
      entry_letter (str): character value representing the entry.

    Returns:
      str: MRUList entry value.
    """
    value_string = ''

    value = registry_key.GetValueByName('{0:s}'.format(entry_letter))
    if value is None:
      parser_mediator.ProduceExtractionError(
          'missing MRUList value: {0:s} in key: {1:s}.'.format(
              entry_letter, registry_key.path))

    elif value.DataIsString():
      value_string = value.GetDataAsObject()

    elif value.DataIsBinaryData():
      logger.debug((
          '[{0:s}] Non-string MRUList entry value: {1:s} parsed as string '
          'in key: {2:s}.').format(self.NAME, entry_letter, registry_key.path))

      utf16le_string_map = self._GetDataTypeMap('utf16le_string')

      try:
        value_string = self._ReadStructureFromByteStream(
            value.data, 0, utf16le_string_map)
      except (ValueError, errors.ParseError) as exception:
        parser_mediator.ProduceExtractionError((
            'unable to parse MRUList entry value: {0:s} with error: '
            '{1!s}').format(entry_letter, exception))

      value_string = value_string.rstrip('\x00')

    return value_string

  # pylint: disable=arguments-differ
  def ExtractEvents(
      self, parser_mediator, registry_key, codepage='cp1252', **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      codepage (Optional[str]): extended ASCII string codepage.
    """
    self._ParseMRUListKey(parser_mediator, registry_key, codepage=codepage)


class MRUListShellItemListWindowsRegistryPlugin(
    BaseMRUListWindowsRegistryPlugin):
  """Windows Registry plugin to parse a shell item list MRUList."""

  NAME = 'mrulist_shell_item_list'
  DESCRIPTION = 'Parser for Most Recently Used (MRU) Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          'Explorer\\DesktopStreamMRU')])

  URLS = ['https://github.com/libyal/winreg-kb/wiki/MRU-keys']

  # pylint: disable=arguments-differ
  def _ParseMRUListEntryValue(
      self, parser_mediator, registry_key, entry_index, entry_letter,
      codepage='cp1252', **kwargs):
    """Parses the MRUList entry value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key that contains
           the MRUList value.
      entry_index (int): MRUList entry index.
      entry_letter (str): character value representing the entry.
      codepage (Optional[str]): extended ASCII string codepage.

    Returns:
      str: MRUList entry value.
    """
    value_string = ''

    value = registry_key.GetValueByName('{0:s}'.format(entry_letter))
    if value is None:
      parser_mediator.ProduceExtractionError(
          'missing MRUList value: {0:s} in key: {1:s}.'.format(
              entry_letter, registry_key.path))

    elif not value.DataIsBinaryData():
      parser_mediator.ProduceExtractionError(
          'Non-binary MRUList entry value: {1:s} in key: {2:s}.'.format(
              entry_letter, registry_key.path))

    elif value.data:
      shell_items_parser = shell_items.ShellItemsParser(registry_key.path)
      shell_items_parser.ParseByteStream(
          parser_mediator, value.data, codepage=codepage)

      value_string = 'Shell item path: {0:s}'.format(
          shell_items_parser.CopyToPath())

    return value_string

  # pylint: disable=arguments-differ
  def ExtractEvents(
      self, parser_mediator, registry_key, codepage='cp1252', **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      codepage (Optional[str]): extended ASCII string codepage.
    """
    self._ParseMRUListKey(parser_mediator, registry_key, codepage=codepage)


winreg.WinRegistryParser.RegisterPlugins([
    MRUListStringWindowsRegistryPlugin,
    MRUListShellItemListWindowsRegistryPlugin])
