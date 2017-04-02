# -*- coding: utf-8 -*-
"""This file contains a MRUList Registry plugin."""

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


class MRUListStringRegistryKeyFilter(
    interface.WindowsRegistryKeyWithValuesFilter):
  """Windows Registry key with values filter."""

  _IGNORE_KEY_PATH_SUFFIXES = frozenset([
      u'\\Explorer\\DesktopStreamMRU'.upper()])

  _VALUE_NAMES = (u'a', u'MRUList')

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


class BaseMRUListPlugin(interface.WindowsRegistryPlugin):
  """Class for common MRUList Windows Registry plugin functionality."""

  _MRULIST_STRUCT = construct.Range(1, 500, construct.ULInt16(u'entry_letter'))

  _SOURCE_APPEND = u': MRU List'

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
      generator: MRUList value generator, which returns the MRU index number
          and entry value.
    """
    mru_list_value = registry_key.GetValueByName(u'MRUList')

    # The key exists but does not contain a value named "MRUList".
    if not mru_list_value:
      return enumerate([])

    try:
      mru_list = self._MRULIST_STRUCT.parse(mru_list_value.data)
    except construct.FieldError:
      logging.warning(u'[{0:s}] Unable to parse the MRU key: {1:s}'.format(
          self.NAME, registry_key.path))
      return enumerate([])

    return enumerate(mru_list)

  def _ParseMRUListKey(self, parser_mediator, registry_key, codepage=u'cp1252'):
    """Extract event objects from a MRUList Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      codepage (Optional[str]): extended ASCII string codepage.
    """
    values_dict = {}
    for entry_index, entry_letter in self._ParseMRUListValue(registry_key):
      # TODO: detect if list ends prematurely.
      # MRU lists are terminated with \0 (0x0000).
      if entry_letter == 0:
        break

      entry_letter = chr(entry_letter)

      value_string = self._ParseMRUListEntryValue(
          parser_mediator, registry_key, entry_index, entry_letter,
          codepage=codepage)

      value_text = u'Index: {0:d} [MRU Value {1:s}]'.format(
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


class MRUListStringPlugin(BaseMRUListPlugin):
  """Windows Registry plugin to parse a string MRUList."""

  NAME = u'mrulist_string'
  DESCRIPTION = u'Parser for Most Recently Used (MRU) Registry data.'

  FILTERS = frozenset([MRUListStringRegistryKeyFilter()])

  URLS = [u'http://forensicartifacts.com/tag/mru/']

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
    value_string = u''

    value = registry_key.GetValueByName(u'{0:s}'.format(entry_letter))
    if value is None:
      logging.debug(
          u'[{0:s}] Missing MRUList entry value: {1:s} in key: {2:s}.'.format(
              self.NAME, entry_letter, registry_key.path))

    elif value.DataIsString():
      value_string = value.GetDataAsObject()

    elif value.DataIsBinaryData():
      logging.debug((
          u'[{0:s}] Non-string MRUList entry value: {1:s} parsed as string '
          u'in key: {2:s}.').format(self.NAME, entry_letter, registry_key.path))
      utf16_stream = binary.ByteStreamCopyToUTF16Stream(value.data)

      try:
        value_string = utf16_stream.decode(u'utf-16-le')
      except UnicodeDecodeError as exception:
        value_string = binary.HexifyBuffer(utf16_stream)
        logging.warning((
            u'[{0:s}] Unable to decode UTF-16 stream: {1:s} in MRUList entry '
            u'value: {2:s} in key: {3:s} with error: {4:s}').format(
                self.NAME, value_string, entry_letter, registry_key.path,
                exception))

    return value_string

  def ExtractEvents(
      self, parser_mediator, registry_key, codepage=u'cp1252', **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      codepage (Optional[str]): extended ASCII string codepage.
    """
    self._ParseMRUListKey(parser_mediator, registry_key, codepage=codepage)


class MRUListShellItemListPlugin(BaseMRUListPlugin):
  """Windows Registry plugin to parse a shell item list MRUList."""

  NAME = u'mrulist_shell_item_list'
  DESCRIPTION = u'Parser for Most Recently Used (MRU) Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          u'Explorer\\DesktopStreamMRU')])

  URLS = [u'https://github.com/libyal/winreg-kb/wiki/MRU-keys']

  def _ParseMRUListEntryValue(
      self, parser_mediator, registry_key, entry_index, entry_letter,
      codepage=u'cp1252', **kwargs):
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
    value_string = u''

    value = registry_key.GetValueByName(u'{0:s}'.format(entry_letter))
    if value is None:
      logging.debug(
          u'[{0:s}] Missing MRUList entry value: {1:s} in key: {2:s}.'.format(
              self.NAME, entry_letter, registry_key.path))

    elif not value.DataIsBinaryData():
      logging.debug((
          u'[{0:s}] Non-binary MRUList entry value: {1:s} in key: '
          u'{2:s}.').format(self.NAME, entry_letter, registry_key.path))

    elif value.data:
      shell_items_parser = shell_items.ShellItemsParser(registry_key.path)
      shell_items_parser.ParseByteStream(
          parser_mediator, value.data, codepage=codepage)

      value_string = u'Shell item path: {0:s}'.format(
          shell_items_parser.CopyToPath())

    return value_string

  def ExtractEvents(
      self, parser_mediator, registry_key, codepage=u'cp1252', **kwargs):
    """Extracts events from a Windows Registry key.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
      codepage (Optional[str]): extended ASCII string codepage.
    """
    self._ParseMRUListKey(parser_mediator, registry_key, codepage=codepage)


winreg.WinRegistryParser.RegisterPlugins([
    MRUListStringPlugin, MRUListShellItemListPlugin])
