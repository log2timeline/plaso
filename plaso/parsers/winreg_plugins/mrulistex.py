# -*- coding: utf-8 -*-
"""This file contains MRUListEx Windows Registry plugins."""

from __future__ import unicode_literals

import abc
import logging

import construct

from plaso.containers import time_events
from plaso.containers import windows_events
from plaso.lib import definitions
from plaso.lib import binary
from plaso.parsers import winreg
from plaso.parsers.shared import shell_items
from plaso.parsers.winreg_plugins import interface


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


class BaseMRUListExPlugin(interface.WindowsRegistryPlugin):
  """Class for common MRUListEx Windows Registry plugin functionality."""

  _MRULISTEX_STRUCT = construct.Range(
      1, 500, construct.ULInt32('entry_number'))

  _SOURCE_APPEND = ': MRUListEx'

  @abc.abstractmethod
  def _ParseMRUListExEntryValue(
      self, parser_mediator, registry_key, entry_index, entry_number, **kwargs):
    """Parses the MRUListEx entry value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
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
      generator: MRUListEx value generator, which returns the MRU index number
          and entry value.
    """
    mru_list_value = registry_key.GetValueByName('MRUListEx')

    # The key exists but does not contain a value named "MRUListEx".
    if not mru_list_value:
      return enumerate([])

    try:
      mru_list = self._MRULISTEX_STRUCT.parse(mru_list_value.data)
    except construct.FieldError:
      logging.warning('[{0:s}] Unable to parse the MRU key: {1:s}'.format(
          self.NAME, registry_key.path))
      return enumerate([])

    return enumerate(mru_list)

  def _ParseMRUListExKey(
      self, parser_mediator, registry_key, codepage='cp1252'):
    """Extract event objects from a MRUListEx Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      codepage (Optional[str]): extended ASCII string codepage.
    """
    values_dict = {}
    for entry_index, entry_number in self._ParseMRUListExValue(registry_key):
      # TODO: detect if list ends prematurely.
      # MRU lists are terminated with 0xffffffff (-1).
      if entry_number == 0xffffffff:
        break

      value_string = self._ParseMRUListExEntryValue(
          parser_mediator, registry_key, entry_index, entry_number,
          codepage=codepage)

      value_text = 'Index: {0:d} [MRU Value {1:d}]'.format(
          entry_index + 1, entry_number)

      values_dict[value_text] = value_string

    event_data = windows_events.WindowsRegistryEventData()
    event_data.key_path = registry_key.path
    event_data.offset = registry_key.offset
    event_data.regvalue = values_dict
    event_data.source_append = self._SOURCE_APPEND

    event = time_events.DateTimeValuesEvent(
        registry_key.last_written_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)


class MRUListExStringPlugin(BaseMRUListExPlugin):
  """Windows Registry plugin to parse a string MRUListEx."""

  NAME = 'mrulistex_string'
  DESCRIPTION = 'Parser for Most Recently Used (MRU) Registry data.'

  FILTERS = frozenset([MRUListExStringRegistryKeyFilter()])

  URLS = [
      'http://forensicartifacts.com/2011/02/recentdocs/',
      'https://github.com/libyal/winreg-kb/wiki/MRU-keys']

  _STRING_STRUCT = construct.Struct(
      'string_and_shell_item',
      construct.RepeatUntil(
          lambda obj, ctx: obj == b'\x00\x00', construct.Field('string', 2)))

  def _ParseMRUListExEntryValue(
      self, parser_mediator, registry_key, entry_index, entry_number,
      **kwargs):
    """Parses the MRUListEx entry value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
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
      logging.debug(
          '[{0:s}] Missing MRUListEx entry value: {1:d} in key: {2:s}.'.format(
              self.NAME, entry_number, registry_key.path))

    elif value.DataIsString():
      value_string = value.GetDataAsObject()

    elif value.DataIsBinaryData():
      logging.debug((
          '[{0:s}] Non-string MRUListEx entry value: {1:d} parsed as string '
          'in key: {2:s}.').format(self.NAME, entry_number, registry_key.path))
      utf16_stream = binary.ByteStreamCopyToUTF16Stream(value.data)

      try:
        value_string = utf16_stream.decode('utf-16-le')
      except UnicodeDecodeError as exception:
        value_string = binary.HexifyBuffer(utf16_stream)
        logging.warning((
            '[{0:s}] Unable to decode UTF-16 stream: {1:s} in MRUListEx entry '
            'value: {2:d} in key: {3:s} with error: {4!s}').format(
                self.NAME, value_string, entry_number, registry_key.path,
                exception))

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
    self._ParseMRUListExKey(parser_mediator, registry_key, codepage=codepage)


class MRUListExShellItemListPlugin(BaseMRUListExPlugin):
  """Windows Registry plugin to parse a shell item list MRUListEx."""

  NAME = 'mrulistex_shell_item_list'
  DESCRIPTION = 'Parser for Most Recently Used (MRU) Registry data.'

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
          and other components, such as storage and dfvfs.
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
      logging.debug(
          '[{0:s}] Missing MRUListEx entry value: {1:d} in key: {2:s}.'.format(
              self.NAME, entry_number, registry_key.path))

    elif not value.DataIsBinaryData():
      logging.debug((
          '[{0:s}] Non-binary MRUListEx entry value: {1:d} in key: '
          '{2:s}.').format(self.NAME, entry_number, registry_key.path))

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
    if registry_key.name != 'OpenSavePidlMRU':
      self._ParseMRUListExKey(parser_mediator, registry_key, codepage=codepage)

    if registry_key.name == 'OpenSavePidlMRU':
      # For the OpenSavePidlMRU MRUListEx we also need to parse its subkeys
      # since the Registry key path does not support wildcards yet.
      for subkey in registry_key.GetSubkeys():
        self._ParseMRUListExKey(parser_mediator, subkey, codepage=codepage)


class MRUListExStringAndShellItemPlugin(BaseMRUListExPlugin):
  """Windows Registry plugin to parse a string and shell item MRUListEx."""

  NAME = 'mrulistex_string_and_shell_item'
  DESCRIPTION = 'Parser for Most Recently Used (MRU) Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          'Explorer\\RecentDocs')])

  _STRING_AND_SHELL_ITEM_STRUCT = construct.Struct(
      'string_and_shell_item',
      construct.RepeatUntil(
          lambda obj, ctx: obj == b'\x00\x00', construct.Field('string', 2)),
      construct.Anchor('shell_item'))

  # pylint: disable=arguments-differ
  def _ParseMRUListExEntryValue(
      self, parser_mediator, registry_key, entry_index, entry_number,
      codepage='cp1252', **kwargs):
    """Parses the MRUListEx entry value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
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
      logging.debug(
          '[{0:s}] Missing MRUListEx entry value: {1:d} in key: {2:s}.'.format(
              self.NAME, entry_number, registry_key.path))

    elif not value.DataIsBinaryData():
      logging.debug((
          '[{0:s}] Non-binary MRUListEx entry value: {1:d} in key: '
          '{2:s}.').format(self.NAME, entry_number, registry_key.path))

    elif value.data:
      value_struct = self._STRING_AND_SHELL_ITEM_STRUCT.parse(value.data)

      try:
        # The struct includes the end-of-string character that we need
        # to strip off.
        path = b''.join(value_struct.string).decode('utf16')[:-1]
      except UnicodeDecodeError as exception:
        logging.warning((
            '[{0:s}] Unable to decode string MRUListEx entry value: {1:d} '
            'in key: {2:s} with error: {3!s}').format(
                self.NAME, entry_number, registry_key.path, exception))
        path = ''

      if path:
        shell_item_list_data = value.data[value_struct.shell_item:]
        if not shell_item_list_data:
          logging.debug((
              '[{0:s}] Missing shell item in MRUListEx entry value: {1:d}'
              'in key: {2:s}').format(
                  self.NAME, entry_number, registry_key.path))
          value_string = 'Path: {0:s}'.format(path)

        else:
          shell_items_parser = shell_items.ShellItemsParser(registry_key.path)
          shell_items_parser.ParseByteStream(
              parser_mediator, shell_item_list_data, codepage=codepage)

          value_string = 'Path: {0:s}, Shell item: [{1:s}]'.format(
              path, shell_items_parser.CopyToPath())

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
    self._ParseMRUListExKey(parser_mediator, registry_key, codepage=codepage)

    if registry_key.name == 'RecentDocs':
      # For the RecentDocs MRUListEx we also need to parse its subkeys
      # since the Registry key path does not support wildcards yet.
      for subkey in registry_key.GetSubkeys():
        self._ParseMRUListExKey(parser_mediator, subkey, codepage=codepage)


class MRUListExStringAndShellItemListPlugin(BaseMRUListExPlugin):
  """Windows Registry plugin to parse a string and shell item list MRUListEx."""

  NAME = 'mrulistex_string_and_shell_item_list'
  DESCRIPTION = 'Parser for Most Recently Used (MRU) Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          'Explorer\\ComDlg32\\LastVisitedPidlMRU')])

  _STRING_AND_SHELL_ITEM_LIST_STRUCT = construct.Struct(
      'string_and_shell_item',
      construct.RepeatUntil(
          lambda obj, ctx: obj == b'\x00\x00', construct.Field('string', 2)),
      construct.Anchor('shell_item_list'))

  # pylint: disable=arguments-differ
  def _ParseMRUListExEntryValue(
      self, parser_mediator, registry_key, entry_index, entry_number,
      codepage='cp1252', **kwargs):
    """Parses the MRUListEx entry value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
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
      logging.debug(
          '[{0:s}] Missing MRUListEx entry value: {1:d} in key: {2:s}.'.format(
              self.NAME, entry_number, registry_key.path))

    elif not value.DataIsBinaryData():
      logging.debug((
          '[{0:s}] Non-binary MRUListEx entry value: {1:d} in key: '
          '{2:s}.').format(self.NAME, entry_number, registry_key.path))

    elif value.data:
      value_struct = self._STRING_AND_SHELL_ITEM_LIST_STRUCT.parse(value.data)

      try:
        # The struct includes the end-of-string character that we need
        # to strip off.
        path = b''.join(value_struct.string).decode('utf16')[:-1]
      except UnicodeDecodeError as exception:
        logging.warning((
            '[{0:s}] Unable to decode string MRUListEx entry value: {1:d} '
            'in key: {2:s} with error: {3!s}').format(
                self.NAME, entry_number, registry_key.path, exception))
        path = ''

      if path:
        shell_item_list_data = value.data[value_struct.shell_item_list:]
        if not shell_item_list_data:
          logging.debug((
              '[{0:s}] Missing shell item in MRUListEx entry value: {1:d}'
              'in key: {2:s}').format(
                  self.NAME, entry_number, registry_key.path))
          value_string = 'Path: {0:s}'.format(path)

        else:
          shell_items_parser = shell_items.ShellItemsParser(registry_key.path)
          shell_items_parser.ParseByteStream(
              parser_mediator, shell_item_list_data, codepage=codepage)

          value_string = 'Path: {0:s}, Shell item path: {1:s}'.format(
              path, shell_items_parser.CopyToPath())

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
    self._ParseMRUListExKey(parser_mediator, registry_key, codepage=codepage)


winreg.WinRegistryParser.RegisterPlugins([
    MRUListExStringPlugin, MRUListExShellItemListPlugin,
    MRUListExStringAndShellItemPlugin, MRUListExStringAndShellItemListPlugin])
