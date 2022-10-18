# -*- coding: utf-8 -*-
"""Windows Registry plugin to parse the MRUListEx Registry values.

Also see:
  https://winreg-kb.readthedocs.io/en/latest/sources/explorer-keys/Most-recently-used.html
"""

import abc
import os

from dtfabric.runtime import data_maps as dtfabric_data_maps

from plaso.containers import events
from plaso.lib import errors
from plaso.lib import dtfabric_helper
from plaso.parsers import logger
from plaso.parsers import winreg_parser
from plaso.parsers.shared import shell_items
from plaso.parsers.winreg_plugins import interface


class MRUListExEventData(events.EventData):
  """MRUListEx event data attribute container.

  Attributes:
    entries (str): most recently used (MRU) entries.
    key_path (str): Windows Registry key path.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
  """

  DATA_TYPE = 'windows:registry:mrulistex'

  def __init__(self):
    """Initializes event data."""
    super(MRUListExEventData, self).__init__(data_type=self.DATA_TYPE)
    self.entries = None
    self.key_path = None
    self.last_written_time = None


class MRUListExStringRegistryKeyFilter(
    interface.WindowsRegistryKeyWithValuesFilter):
  """Windows Registry key with values filter."""

  _IGNORE_KEY_PATH_SEGMENTS = frozenset([
      '\\BagMRU\\'.upper(),
      '\\Explorer\\ComDlg32\\OpenSavePidlMRU\\'.upper()])

  _IGNORE_KEY_PATH_SUFFIXES = frozenset([
      '\\BagMRU'.upper(),
      '\\Explorer\\StreamMRU'.upper(),
      '\\Explorer\\ComDlg32\\OpenSavePidlMRU'.upper()])

  _VALUE_NAMES = ['0', 'MRUListEx']

  def __init__(self):
    """Initializes Windows Registry key filter object."""
    super(MRUListExStringRegistryKeyFilter, self).__init__(self._VALUE_NAMES)

  def Match(self, registry_key):
    """Determines if a Windows Registry key matches the filter.

    Args:
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.

    Returns:
      bool: True if the Windows Registry key matches the filter.
    """
    key_path_upper = registry_key.path.upper()
    # Prevent this filter matching non-string MRUListEx values.
    for ignore_key_path_suffix in self._IGNORE_KEY_PATH_SUFFIXES:
      if key_path_upper.endswith(ignore_key_path_suffix):
        return False

    for ignore_key_path_segment in self._IGNORE_KEY_PATH_SEGMENTS:
      if ignore_key_path_segment in key_path_upper:
        return False

    return super(MRUListExStringRegistryKeyFilter, self).Match(registry_key)


class BaseMRUListExWindowsRegistryPlugin(
    interface.WindowsRegistryPlugin, dtfabric_helper.DtFabricHelper):
  """Class for common MRUListEx Windows Registry plugin functionality."""

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'mru.yaml')

  @abc.abstractmethod
  def _ParseMRUListExEntryValue(
      self, parser_mediator, registry_key, entry_index, entry_number, **kwargs):
    """Parses the MRUListEx entry value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key that contains
           the MRUListEx value.
      entry_index (int): MRUListEx entry index.
      entry_number (int): entry number.

    Returns:
      str: MRUList entry value.
    """

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

  def _ParseMRUListExKey(
      self, parser_mediator, registry_key, codepage='cp1252'):
    """Extract event objects from a MRUListEx Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
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

    entries = []
    found_terminator = False
    for entry_index, entry_number in enumerate(mrulistex):
      # The MRU list is terminated with -1 (0xffffffff).
      if entry_number == -1:
        break

      if found_terminator:
        parser_mediator.ProduceExtractionWarning((
            'found additional MRUListEx entries after terminator in key: '
            '{0:s}.').format(registry_key.path))

        # Only create one parser error per terminator.
        found_terminator = False

      value_string = self._ParseMRUListExEntryValue(
          parser_mediator, registry_key, entry_index, entry_number,
          codepage=codepage)

      value_text = 'Index: {0:d} [MRU Value {1:d}]: {2:s}'.format(
          entry_index + 1, entry_number, value_string)

      entries.append(value_text)

    event_data = MRUListExEventData()
    event_data.entries = ' '.join(entries)
    event_data.key_path = registry_key.path
    event_data.last_written_time = registry_key.last_written_time

    parser_mediator.ProduceEventData(event_data)


class MRUListExStringWindowsRegistryPlugin(BaseMRUListExWindowsRegistryPlugin):
  """Windows Registry plugin to parse a string MRUListEx."""

  NAME = 'mrulistex_string'
  DATA_FORMAT = 'Most Recently Used (MRU) Registry data'

  FILTERS = frozenset([MRUListExStringRegistryKeyFilter()])

  # pylint: disable=arguments-differ
  def _ParseMRUListExEntryValue(
      self, parser_mediator, registry_key, entry_index, entry_number, **kwargs):
    """Parses the MRUListEx entry value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key that contains
           the MRUListEx value.
      entry_index (int): MRUListEx entry index.
      entry_number (int): entry number.

    Returns:
      str: MRUList entry value.
    """
    value_string = ''

    value = registry_key.GetValueByName('{0:d}'.format(entry_number))
    if value is None:
      parser_mediator.ProduceExtractionWarning(
          'missing MRUListEx value: {0:d} in key: {1:s}.'.format(
              entry_number, registry_key.path))

    elif value.DataIsString():
      value_string = value.GetDataAsObject()

    elif value.DataIsBinaryData():
      utf16le_string_map = self._GetDataTypeMap('utf16le_string')

      try:
        value_string = self._ReadStructureFromByteStream(
            value.data, 0, utf16le_string_map)
      except (ValueError, errors.ParseError) as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to parse MRUListEx entry value: {0:d} with error: '
            '{1!s}').format(entry_number, exception))

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
    self._ParseMRUListExKey(parser_mediator, registry_key, codepage=codepage)


class MRUListExShellItemListWindowsRegistryPlugin(
    BaseMRUListExWindowsRegistryPlugin):
  """Windows Registry plugin to parse a shell item list MRUListEx."""

  NAME = 'mrulistex_shell_item_list'
  DATA_FORMAT = 'Most Recently Used (MRU) Registry data'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          'Explorer\\ComDlg32\\OpenSavePidlMRU'),
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          'Explorer\\StreamMRU')])

  # pylint: disable=arguments-differ
  def _ParseMRUListExEntryValue(
      self, parser_mediator, registry_key, entry_index, entry_number,
      codepage='cp1252', **kwargs):
    """Parses the MRUListEx entry value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key that contains
           the MRUListEx value.
      entry_index (int): MRUListEx entry index.
      entry_number (int): entry number.
      codepage (Optional[str]): extended ASCII string codepage.

    Returns:
      str: MRUList entry value.
    """
    value_string = ''

    value = registry_key.GetValueByName('{0:d}'.format(entry_number))
    if value is None:
      parser_mediator.ProduceExtractionWarning(
          'missing MRUListEx value: {0:d} in key: {1:s}.'.format(
              entry_number, registry_key.path))

    elif not value.DataIsBinaryData():
      logger.debug((
          '[{0:s}] Non-binary MRUListEx entry value: {1:d} in key: '
          '{2:s}.').format(self.NAME, entry_number, registry_key.path))

    elif value.data:
      shell_items_parser = shell_items.ShellItemsParser(registry_key.path)
      shell_items_parser.ParseByteStream(
          parser_mediator, value.data, codepage=codepage)

      shell_item_path = shell_items_parser.CopyToPath() or 'N/A'
      value_string = 'Shell item path: {0:s}'.format(shell_item_path)

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
    if registry_key.name != 'OpenSavePidlMRU':
      self._ParseMRUListExKey(parser_mediator, registry_key, codepage=codepage)

    if registry_key.name == 'OpenSavePidlMRU':
      # For the OpenSavePidlMRU MRUListEx we also need to parse its subkeys
      # since the Registry key path does not support wildcards yet.
      for subkey in registry_key.GetSubkeys():
        self._ParseMRUListExKey(parser_mediator, subkey, codepage=codepage)


class MRUListExStringAndShellItemWindowsRegistryPlugin(
    BaseMRUListExWindowsRegistryPlugin):
  """Windows Registry plugin to parse a string and shell item MRUListEx."""

  NAME = 'mrulistex_string_and_shell_item'
  DATA_FORMAT = 'Most Recently Used (MRU) Registry data'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          'Explorer\\RecentDocs')])

  # pylint: disable=arguments-differ
  def _ParseMRUListExEntryValue(
      self, parser_mediator, registry_key, entry_index, entry_number,
      codepage='cp1252', **kwargs):
    """Parses the MRUListEx entry value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key that contains
           the MRUListEx value.
      entry_index (int): MRUListEx entry index.
      entry_number (int): entry number.
      codepage (Optional[str]): extended ASCII string codepage.

    Returns:
      str: MRUList entry value.
    """
    value_string = ''

    value = registry_key.GetValueByName('{0:d}'.format(entry_number))
    if value is None:
      parser_mediator.ProduceExtractionWarning(
          'missing MRUListEx value: {0:d} in key: {1:s}.'.format(
              entry_number, registry_key.path))

    elif not value.DataIsBinaryData():
      logger.debug((
          '[{0:s}] Non-binary MRUListEx entry value: {1:d} in key: '
          '{2:s}.').format(self.NAME, entry_number, registry_key.path))

    elif value.data:
      utf16le_string_map = self._GetDataTypeMap('utf16le_string')

      context = dtfabric_data_maps.DataTypeMapContext()

      try:
        path = self._ReadStructureFromByteStream(
            value.data, 0, utf16le_string_map, context=context)
      except (ValueError, errors.ParseError) as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to parse MRUListEx entry value: {0:d} with error: '
            '{1!s}').format(entry_number, exception))
        return value_string

      path = path.rstrip('\x00')

      shell_item_data = value.data[context.byte_size:]

      if not shell_item_data:
        parser_mediator.ProduceExtractionWarning((
            'missing shell item in MRUListEx value: {0:d} in key: '
            '{1:s}.').format(entry_number, registry_key.path))
        value_string = 'Path: {0:s}'.format(path)

      else:
        shell_items_parser = shell_items.ShellItemsParser(registry_key.path)
        shell_items_parser.ParseByteStream(
            parser_mediator, shell_item_data, codepage=codepage)

        shell_item_path = shell_items_parser.CopyToPath() or 'N/A'
        value_string = 'Path: {0:s}, Shell item: [{1:s}]'.format(
            path, shell_item_path)

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
    self._ParseMRUListExKey(parser_mediator, registry_key, codepage=codepage)

    if registry_key.name == 'RecentDocs':
      # For the RecentDocs MRUListEx we also need to parse its subkeys
      # since the Registry key path does not support wildcards yet.
      for subkey in registry_key.GetSubkeys():
        self._ParseMRUListExKey(parser_mediator, subkey, codepage=codepage)


class MRUListExStringAndShellItemListWindowsRegistryPlugin(
    BaseMRUListExWindowsRegistryPlugin):
  """Windows Registry plugin to parse a string and shell item list MRUListEx."""

  NAME = 'mrulistex_string_and_shell_item_list'
  DATA_FORMAT = 'Most Recently Used (MRU) Registry data'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          'Explorer\\ComDlg32\\LastVisitedPidlMRU')])

  # pylint: disable=arguments-differ
  def _ParseMRUListExEntryValue(
      self, parser_mediator, registry_key, entry_index, entry_number,
      codepage='cp1252', **kwargs):
    """Parses the MRUListEx entry value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key that contains
           the MRUListEx value.
      entry_index (int): MRUListEx entry index.
      entry_number (int): entry number.
      codepage (Optional[str]): extended ASCII string codepage.

    Returns:
      str: MRUList entry value.
    """
    value_string = ''

    value = registry_key.GetValueByName('{0:d}'.format(entry_number))
    if value is None:
      parser_mediator.ProduceExtractionWarning(
          'missing MRUListEx value: {0:d} in key: {1:s}.'.format(
              entry_number, registry_key.path))

    elif not value.DataIsBinaryData():
      logger.debug((
          '[{0:s}] Non-binary MRUListEx entry value: {1:d} in key: '
          '{2:s}.').format(self.NAME, entry_number, registry_key.path))

    elif value.data:
      utf16le_string_map = self._GetDataTypeMap('utf16le_string')

      context = dtfabric_data_maps.DataTypeMapContext()

      try:
        path = self._ReadStructureFromByteStream(
            value.data, 0, utf16le_string_map, context=context)
      except (ValueError, errors.ParseError) as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to parse MRUListEx entry value: {0:d} with error: '
            '{1!s}').format(entry_number, exception))
        return value_string

      path = path.rstrip('\x00')

      shell_item_list_data = value.data[context.byte_size:]

      if not shell_item_list_data:
        parser_mediator.ProduceExtractionWarning((
            'missing shell item in MRUListEx value: {0:d} in key: '
            '{1:s}.').format(entry_number, registry_key.path))
        value_string = 'Path: {0:s}'.format(path)

      else:
        shell_items_parser = shell_items.ShellItemsParser(registry_key.path)
        shell_items_parser.ParseByteStream(
            parser_mediator, shell_item_list_data, codepage=codepage)

        shell_item_path = shell_items_parser.CopyToPath() or 'N/A'
        value_string = 'Path: {0:s}, Shell item path: {1:s}'.format(
            path, shell_item_path)

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
    self._ParseMRUListExKey(parser_mediator, registry_key, codepage=codepage)


winreg_parser.WinRegistryParser.RegisterPlugins([
    MRUListExStringWindowsRegistryPlugin,
    MRUListExShellItemListWindowsRegistryPlugin,
    MRUListExStringAndShellItemWindowsRegistryPlugin,
    MRUListExStringAndShellItemListWindowsRegistryPlugin])
