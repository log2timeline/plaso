# -*- coding: utf-8 -*-
"""Windows Registry plugin to parse the BagMRU (or ShellBags) key."""

import os

from dtfabric.runtime import data_maps as dtfabric_data_maps

from plaso.containers import events
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.parsers.shared import shell_items
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class BagMRUEventData(events.EventData):
  """BagMRU (or ShellBags) event data attribute container.

  Attributes:
    entries (str): most recently used (MRU) entries.
    key_path (str): Windows Registry key path.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
  """

  DATA_TYPE = 'windows:registry:bagmru'

  def __init__(self):
    """Initializes event data."""
    super(BagMRUEventData, self).__init__(data_type=self.DATA_TYPE)
    self.entries = None
    self.key_path = None
    self.last_written_time = None


class BagMRUWindowsRegistryPlugin(
    interface.WindowsRegistryPlugin, dtfabric_helper.DtFabricHelper):
  """Windows Registry plugin to parse the BagMRU (or ShellBags) key."""

  NAME = 'bagmru'
  DATA_FORMAT = 'BagMRU (or ShellBags) Registry data'

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

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'mru.yaml')

  def _ParseMRUListExEntryValue(
      self, parser_mediator, registry_key, entry_number, parent_path_segments,
      codepage='cp1252'):
    """Parses the MRUListEx entry value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key that contains
           the MRUListEx value.
      entry_number (int): entry number.
      parent_path_segments (list[str]): parent shell item path segments.
      codepage (Optional[str]): extended ASCII string codepage.

    Returns:
      tuple[str, str]: path and upper path segment of the shell item or
          None, None if not available.
    """
    value = registry_key.GetValueByName(f'{entry_number:d}')
    if value is None:
      parser_mediator.ProduceExtractionWarning((
          f'Missing MRUListEx entry value: {entry_number:d} in key: '
          f'{registry_key.path:s}'))
      return None, None

    if not value.DataIsBinaryData():
      parser_mediator.ProduceExtractionWarning((
          f'Non-binary MRUListEx entry value: {entry_number:d} in key: '
          f'{registry_key.path:s}'))
      return None, None

    path = None
    upper_path_segment = None

    if value.data:
      shell_items_parser = shell_items.ShellItemsParser(registry_key.path)
      shell_items_parser.ParseByteStream(
          parser_mediator, value.data,
          parent_path_segments=parent_path_segments, codepage=codepage)

      path = shell_items_parser.CopyToPath()
      upper_path_segment = shell_items_parser.GetUpperPathSegment()

    return path, upper_path_segment

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
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      parent_path_segments (list[str]): parent shell item path segments.
      codepage (Optional[str]): extended ASCII string codepage.
    """
    try:
      mrulistex = self._ParseMRUListExValue(registry_key)
    except (ValueError, errors.ParseError) as exception:
      parser_mediator.ProduceExtractionWarning(
          f'unable to parse MRUListEx value with error: {exception!s}')
      return

    if not mrulistex:
      return

    entries = []
    entry_numbers = {}

    found_terminator = False
    for entry_index, entry_number in enumerate(mrulistex):
      # The MRU list is terminated with -1 (0xffffffff).
      if entry_number == -1:
        continue

      if found_terminator:
        parser_mediator.ProduceExtractionWarning((
            f'found additional MRUListEx entries after terminator in key: '
            f'{registry_key.path:s}'))

        # Only create one parser error per terminator.
        found_terminator = False

      path, upper_path_segment = self._ParseMRUListExEntryValue(
          parser_mediator, registry_key, entry_number, parent_path_segments,
          codepage=codepage)

      entry_numbers[entry_number] = upper_path_segment

      display_entry_index = entry_index + 1
      display_path = path or 'N/A'
      entries.append((
          f'Index: {display_entry_index:d} [MRU Value {entry_number:d}]: '
          f'Shell item path: {display_path:s}'))

    event_data = BagMRUEventData()
    event_data.entries = ' '.join(entries) or None
    event_data.key_path = registry_key.path
    event_data.last_written_time = registry_key.last_written_time

    parser_mediator.ProduceEventData(event_data)

    for entry_number, path_segment in entry_numbers.items():
      sub_key = registry_key.GetSubkeyByName(f'{entry_number:d}')
      if not sub_key:
        parser_mediator.ProduceExtractionWarning((
            f'Missing BagMRU sub key: {entry_number:d} in key: '
            f'{registry_key.path:s}'))
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
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      codepage (Optional[str]): extended ASCII string codepage.
    """
    self._ParseSubKey(parser_mediator, registry_key, [], codepage=codepage)


winreg_parser.WinRegistryParser.RegisterPlugin(BagMRUWindowsRegistryPlugin)
