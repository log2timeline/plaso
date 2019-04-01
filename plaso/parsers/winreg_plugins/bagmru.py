# -*- coding: utf-8 -*-
"""This file contains BagMRU Windows Registry plugins (shellbags)."""

from __future__ import unicode_literals

from dtfabric.runtime import data_maps as dtfabric_data_maps

from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.lib import errors
from plaso.parsers.shared import shell_items
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import dtfabric_plugin
from plaso.parsers.winreg_plugins import interface


class BagMRUWindowsRegistryPlugin(
    dtfabric_plugin.DtFabricBaseWindowsRegistryPlugin):
  """Class that defines a BagMRU Windows Registry plugin."""

  NAME = 'bagmru'
  DESCRIPTION = 'Parser for BagMRU Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\Shell\\BagMRU'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\ShellNoRoam\\'
          'BagMRU'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Classes\\Local Settings\\Software\\'
          'Microsoft\\Windows\\Shell\\BagMRU'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Classes\\Local Settings\\Software\\'
          'Microsoft\\Windows\\ShellNoRoam\\BagMRU'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Local Settings\\Software\\Microsoft\\Windows\\'
          'Shell\\BagMRU'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Local Settings\\Software\\Microsoft\\Windows\\'
          'ShellNoRoam\\BagMRU')])

  URLS = [
      ('https://github.com/libyal/winreg-kb/blob/master/documentation/'
       'MRU%20keys.asciidoc#bagmru-key')]

  _DEFINITION_FILE = 'mru.yaml'

  _SOURCE_APPEND = ': BagMRU'

  def _ParseMRUListExEntryValue(
      self, parser_mediator, registry_key, entry_index, entry_number,
      values_dict, value_strings, parent_path_segments, codepage='cp1252'):
    """Parses the MRUListEx entry value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key that contains
           the MRUListEx value.
      entry_index (int): MRUListEx entry index.
      entry_number (int): entry number.
      values_dict (dict[str, object]): values of the key.
      value_strings (dict[str, str]): value names and strings.
      parent_path_segments (list[str]): parent shell item path segments.
      codepage (Optional[str]): extended ASCII string codepage.

    Returns:
      str: path segment of the shell item.
    """
    value = registry_key.GetValueByName('{0:d}'.format(entry_number))
    path_segment = 'N/A'
    value_string = ''
    if value is None:
      parser_mediator.ProduceExtractionWarning(
          'Missing MRUListEx entry value: {0:d} in key: {1:s}.'.format(
              entry_number, registry_key.path))

    elif not value.DataIsBinaryData():
      parser_mediator.ProduceExtractionWarning(
          'Non-binary MRUListEx entry value: {0:d} in key: {1:s}.'.format(
              entry_number, registry_key.path))

    elif value.data:
      shell_items_parser = shell_items.ShellItemsParser(registry_key.path)
      shell_items_parser.ParseByteStream(
          parser_mediator, value.data,
          parent_path_segments=parent_path_segments, codepage=codepage)

      path_segment = shell_items_parser.GetUpperPathSegment()
      value_string = shell_items_parser.CopyToPath()

      value_strings[entry_number] = value_string

      value_string = 'Shell item path: {0:s}'.format(value_string)

    value_text = 'Index: {0:d} [MRU Value {1:d}]'.format(
        entry_index + 1, entry_number)

    values_dict[value_text] = value_string

    return path_segment

  def _ParseMRUListExValue(self, registry_key):
    """Parses the MRUListEx value in a given Registry key.

    Args:
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key that contains
           the MRUListEx value.

    Returns:
      mrulistex_entries: MRUListEx entries or None if not available.
    """
    mrulistex_value = registry_key.GetValueByName('MRUListEx')

    # The key exists but does not contain a value named "MRUList".
    if not mrulistex_value:
      return None

    mrulistex_entries_map = self._GetDataTypeMap('mrulistex_entries')

    context = dtfabric_data_maps.DataTypeMapContext(values={
        'data_size': len(mrulistex_value.data)})

    return self._ReadStructureFromByteStream(
        mrulistex_value.data, 0, mrulistex_entries_map, context=context)

  def _ParseSubKey(
      self, parser_mediator, registry_key, parent_path_segments,
      codepage='cp1252'):
    """Extract event objects from a MRUListEx Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      parent_path_segments (list[str]): parent shell item path segments.
      codepage (Optional[str]): extended ASCII string codepage.
    """
    try:
      mrulistex = self._ParseMRUListExValue(registry_key)
    except (ValueError, errors.ParseError) as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to parse MRUListEx value with error: {0!s}'.format(exception))
      return

    if not mrulistex:
      return

    entry_numbers = {}
    values_dict = {}
    value_strings = {}

    found_terminator = False
    for index, entry_number in enumerate(mrulistex):
      # The MRU list is terminated with -1 (0xffffffff).
      if entry_number == -1:
        continue

      if found_terminator:
        parser_mediator.ProduceExtractionWarning((
            'found additional MRUListEx entries after terminator in key: '
            '{0:s}.').format(registry_key.path))

        # Only create one parser error per terminator.
        found_terminator = False

      path_segment = self._ParseMRUListExEntryValue(
          parser_mediator, registry_key, index, entry_number, values_dict,
          value_strings, parent_path_segments, codepage=codepage)

      entry_numbers[entry_number] = path_segment

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = registry_key.path
    event_data.offset = registry_key.offset
    event_data.regvalue = values_dict
    event_data.source_append = self._SOURCE_APPEND
    event_data.urls = self.URLS

    event = time_events.DateTimeValuesEvent(
        registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)

    for entry_number, path_segment in iter(entry_numbers.items()):
      sub_key_name = '{0:d}'.format(entry_number)
      sub_key = registry_key.GetSubkeyByName(sub_key_name)
      if not sub_key:
        parser_mediator.ProduceExtractionWarning(
            'Missing BagMRU sub key: {0:d} in key: {1:s}.'.format(
                entry_number, registry_key.path))
        continue

      parent_path_segments.append(path_segment)
      self._ParseSubKey(
          parser_mediator, sub_key, parent_path_segments, codepage=codepage)
      parent_path_segments.pop()

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
    self._ParseSubKey(parser_mediator, registry_key, [], codepage=codepage)


winreg.WinRegistryParser.RegisterPlugin(BagMRUWindowsRegistryPlugin)
