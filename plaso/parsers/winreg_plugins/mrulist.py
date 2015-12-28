# -*- coding: utf-8 -*-
"""This file contains a MRUList Registry plugin."""

import abc
import logging

import construct

from plaso.events import windows_events
from plaso.lib import binary
from plaso.parsers import winreg
from plaso.parsers.shared import shell_items
from plaso.parsers.winreg_plugins import interface


class MRUListStringRegistryKeyFilter(
    interface.WindowsRegistryKeyWithValuesFilter):
  """Windows Registry key with values filter."""

  _IGNORE_KEY_PATH_SUFFIXES = frozenset([
      u'\\Explorer\\DesktopStreamMRU'.upper()])

  _VALUE_NAMES = [u'a', u'MRUList']

  def __init__(self):
    """Initializes Windows Registry key filter object."""
    super(MRUListStringRegistryKeyFilter, self).__init__(self._VALUE_NAMES)

  def Match(self, registry_key):
    """Determines if a Windows Registry key matches the filter.

    Args:
      registry_key: a Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).

    Returns:
      A boolean value that indicates a match.
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
      self, parser_mediator, key, entry_index, entry_letter, **kwargs):
    """Parses the MRUList entry value.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: the Registry key (instance of dfwinreg.WinRegistryKey) that contains
           the MRUList value.
      entry_index: integer value representing the MRUList entry index.
      entry_letter: character value representing the entry.

    Returns:
      A string containing the value.
    """

  def _ParseMRUListValue(self, key):
    """Parses the MRUList value in a given Registry key.

    Args:
      key: the Registry key (instance of dfwinreg.WinRegistryKey) that contains
           the MRUList value.

    Returns:
      A MRUList value generator, which returns the MRU index number
      and entry value.
    """
    mru_list_value = key.GetValueByName(u'MRUList')

    # The key exists but does not contain a value named "MRUList".
    if not mru_list_value:
      return enumerate([])

    try:
      mru_list = self._MRULIST_STRUCT.parse(mru_list_value.data)
    except construct.FieldError:
      logging.warning(u'[{0:s}] Unable to parse the MRU key: {1:s}'.format(
          self.NAME, key.path))
      return enumerate([])

    return enumerate(mru_list)

  def _ParseMRUListKey(self, parser_mediator, key, codepage=u'cp1252'):
    """Extract event objects from a MRUList Registry key.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: the Registry key (instance of dfwinreg.WinRegistryKey).
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    values_dict = {}
    for entry_index, entry_letter in self._ParseMRUListValue(key):
      # TODO: detect if list ends prematurely.
      # MRU lists are terminated with \0 (0x0000).
      if entry_letter == 0:
        break

      entry_letter = chr(entry_letter)

      value_string = self._ParseMRUListEntryValue(
          parser_mediator, key, entry_index, entry_letter, codepage=codepage)

      value_text = u'Index: {0:d} [MRU Value {1:s}]'.format(
          entry_index + 1, entry_letter)

      values_dict[value_text] = value_string

    event_object = windows_events.WindowsRegistryEvent(
        key.last_written_time, key.path, values_dict,
        offset=key.offset, source_append=self._SOURCE_APPEND)
    parser_mediator.ProduceEvent(event_object)


class MRUListStringPlugin(BaseMRUListPlugin):
  """Windows Registry plugin to parse a string MRUList."""

  NAME = u'mrulist_string'
  DESCRIPTION = u'Parser for Most Recently Used (MRU) Registry data.'

  FILTERS = frozenset([MRUListStringRegistryKeyFilter()])

  URLS = [u'http://forensicartifacts.com/tag/mru/']

  def _ParseMRUListEntryValue(
      self, parser_mediator, key, entry_index, entry_letter, **unused_kwargs):
    """Parses the MRUList entry value.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: the Registry key (instance of dfwinreg.WinRegistryKey) that contains
           the MRUList value.
      entry_index: integer value representing the MRUList entry index.
      entry_letter: character value representing the entry.

    Returns:
      A string containing the value.
    """
    value_string = u''

    value = key.GetValueByName(u'{0:s}'.format(entry_letter))
    if value is None:
      logging.debug(
          u'[{0:s}] Missing MRUList entry value: {1:s} in key: {2:s}.'.format(
              self.NAME, entry_letter, key.path))

    elif value.DataIsString():
      value_string = value.GetDataAsObject()

    elif value.DataIsBinaryData():
      logging.debug((
          u'[{0:s}] Non-string MRUList entry value: {1:s} parsed as string '
          u'in key: {2:s}.').format(self.NAME, entry_letter, key.path))
      utf16_stream = binary.ByteStreamCopyToUTF16Stream(value.data)

      try:
        value_string = utf16_stream.decode(u'utf-16-le')
      except UnicodeDecodeError as exception:
        value_string = binary.HexifyBuffer(utf16_stream)
        logging.warning((
            u'[{0:s}] Unable to decode UTF-16 stream: {1:s} in MRUList entry '
            u'value: {2:s} in key: {3:s} with error: {4:s}').format(
                self.NAME, value_string, entry_letter, key.path, exception))

    return value_string

  def GetEntries(
      self, parser_mediator, registry_key=None, codepage=u'cp1252', **kwargs):
    """Extracts event objects from a MRU list.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
      codepage: Optional extended ASCII string codepage. The default is cp1252.
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
      self, parser_mediator, key, entry_index, entry_letter, codepage=u'cp1252',
      **unused_kwargs):
    """Parses the MRUList entry value.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: the Registry key (instance of dfwinreg.WinRegistryKey) that contains
           the MRUList value.
      entry_index: integer value representing the MRUList entry index.
      entry_letter: character value representing the entry.
      codepage: Optional extended ASCII string codepage. The default is cp1252.

    Returns:
      A string containing the value.
    """
    value_string = u''

    value = key.GetValueByName(u'{0:s}'.format(entry_letter))
    if value is None:
      logging.debug(
          u'[{0:s}] Missing MRUList entry value: {1:s} in key: {2:s}.'.format(
              self.NAME, entry_letter, key.path))

    elif not value.DataIsBinaryData():
      logging.debug((
          u'[{0:s}] Non-binary MRUList entry value: {1:s} in key: '
          u'{2:s}.').format(self.NAME, entry_letter, key.path))

    elif value.data:
      shell_items_parser = shell_items.ShellItemsParser(key.path)
      shell_items_parser.ParseByteStream(
          parser_mediator, value.data, codepage=codepage)

      value_string = u'Shell item path: {0:s}'.format(
          shell_items_parser.CopyToPath())

    return value_string

  def GetEntries(
      self, parser_mediator, registry_key, codepage=u'cp1252', **kwargs):
    """Extract event objects from a Registry key containing a MRUList value.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    self._ParseMRUListKey(parser_mediator, registry_key, codepage=codepage)


winreg.WinRegistryParser.RegisterPlugins([
    MRUListStringPlugin, MRUListShellItemListPlugin])
