# -*- coding: utf-8 -*-
"""Windows Registry plugin to parse the MRUList Registry values.

Also see:
  https://winreg-kb.readthedocs.io/en/latest/sources/explorer-keys/Most-recently-used.html
"""

import abc
import os

from dtfabric.runtime import data_maps as dtfabric_data_maps

from plaso.containers import events
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.parsers import logger
from plaso.parsers import winreg_parser
from plaso.parsers.shared import shell_items
from plaso.parsers.winreg_plugins import interface


class MRUListEventData(events.EventData):
  """MRUList event data attribute container.

  Attributes:
    entries (list[str]): most recently used (MRU) entries.
    key_path (str): Windows Registry key path.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
  """

  DATA_TYPE = 'windows:registry:mrulist'

  def __init__(self):
    """Initializes event data."""
    super(MRUListEventData, self).__init__(data_type=self.DATA_TYPE)
    self.entries = None
    self.key_path = None
    self.last_written_time = None


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
    interface.WindowsRegistryPlugin, dtfabric_helper.DtFabricHelper):
  """Class for common MRUList Windows Registry plugin functionality."""

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'mru.yaml')

  @abc.abstractmethod
  def _ParseMRUListEntryValue(
      self, parser_mediator, registry_key, entry_index, entry_letter, **kwargs):
    """Parses the MRUList entry value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
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
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      codepage (Optional[str]): extended ASCII string codepage.
    """
    try:
      mrulist = self._ParseMRUListValue(registry_key)
    except (ValueError, errors.ParseError) as exception:
      parser_mediator.ProduceExtractionWarning(
          f'unable to parse MRUList value with error: {exception!s}')
      return

    if not mrulist:
      return

    entries = []
    found_terminator = False
    for entry_index, entry_letter in enumerate(mrulist):
      # The MRU list is terminated with '\0' (0x0000).
      if entry_letter == 0:
        break

      if found_terminator:
        parser_mediator.ProduceExtractionWarning((
            f'found additional MRUList entries after terminator in key: '
            f'{registry_key.path:s}.'))

        # Only create one parser error per terminator.
        found_terminator = False

      entry_letter = chr(entry_letter)

      value_string = self._ParseMRUListEntryValue(
          parser_mediator, registry_key, entry_index, entry_letter,
          codepage=codepage)

      display_entry_index = entry_index + 1
      entries.append((
          f'Index: {display_entry_index:d} [MRU Value {entry_letter:s}]: '
          f'{value_string:s}'))

    event_data = MRUListEventData()
    event_data.entries = entries
    event_data.key_path = registry_key.path
    event_data.last_written_time = registry_key.last_written_time

    parser_mediator.ProduceEventData(event_data)


class MRUListStringWindowsRegistryPlugin(BaseMRUListWindowsRegistryPlugin):
  """Windows Registry plugin to parse a string MRUList."""

  NAME = 'mrulist_string'
  DATA_FORMAT = 'Most Recently Used (MRU) Registry data'

  FILTERS = frozenset([MRUListStringRegistryKeyFilter()])

  def _ParseMRUListEntryValue(
      self, parser_mediator, registry_key, entry_index, entry_letter, **kwargs):
    """Parses the MRUList entry value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key that contains
           the MRUList value.
      entry_index (int): MRUList entry index.
      entry_letter (str): character value representing the entry.

    Returns:
      str: MRUList entry value.
    """
    value_string = ''

    value = registry_key.GetValueByName(entry_letter)
    if value is None:
      parser_mediator.ProduceExtractionWarning((
          f'missing MRUList value: {entry_letter:s} in key: '
          f'{registry_key.path:s}'))

    elif value.DataIsString():
      value_string = value.GetDataAsObject()

    elif value.DataIsBinaryData():
      logger.debug((
          f'[{self.NAME:s}] Non-string MRUList entry value: {entry_letter:s} '
          f'parsed as string in key: {registry_key.path:s}.'))

      utf16le_string_map = self._GetDataTypeMap('utf16le_string')

      try:
        value_string = self._ReadStructureFromByteStream(
            value.data, 0, utf16le_string_map)
      except (ValueError, errors.ParseError) as exception:
        parser_mediator.ProduceExtractionWarning((
            f'unable to parse MRUList entry value: {entry_letter:s} with '
            f'error: {exception!s}'))

      value_string = value_string.rstrip('\x00')

    return value_string

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
    self._ParseMRUListKey(parser_mediator, registry_key, codepage=codepage)


class MRUListShellItemListWindowsRegistryPlugin(
    BaseMRUListWindowsRegistryPlugin):
  """Windows Registry plugin to parse a shell item list MRUList."""

  NAME = 'mrulist_shell_item_list'
  DATA_FORMAT = 'Most Recently Used (MRU) Registry data'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          'Explorer\\DesktopStreamMRU')])

  # pylint: disable=arguments-differ
  def _ParseMRUListEntryValue(
      self, parser_mediator, registry_key, entry_index, entry_letter,
      codepage='cp1252', **kwargs):
    """Parses the MRUList entry value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key that contains
           the MRUList value.
      entry_index (int): MRUList entry index.
      entry_letter (str): character value representing the entry.
      codepage (Optional[str]): extended ASCII string codepage.

    Returns:
      str: MRUList entry value.
    """
    value_string = ''

    value = registry_key.GetValueByName(entry_letter)
    if value is None:
      parser_mediator.ProduceExtractionWarning((
          f'missing MRUList value: {entry_letter:s} in key: '
          f'{registry_key.path:s}'))

    elif not value.DataIsBinaryData():
      parser_mediator.ProduceExtractionWarning((
          f'Non-binary MRUList entry value: {entry_letter:s} in key: '
          f'{registry_key.path:s}'))

    elif value.data:
      shell_items_parser = shell_items.ShellItemsParser(registry_key.path)
      shell_items_parser.ParseByteStream(
          parser_mediator, value.data, codepage=codepage)

      shell_item_path = shell_items_parser.CopyToPath() or 'N/A'
      value_string = f'Shell item path: {shell_item_path:s}'

    return value_string

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
    self._ParseMRUListKey(parser_mediator, registry_key, codepage=codepage)


winreg_parser.WinRegistryParser.RegisterPlugins([
    MRUListStringWindowsRegistryPlugin,
    MRUListShellItemListWindowsRegistryPlugin])
