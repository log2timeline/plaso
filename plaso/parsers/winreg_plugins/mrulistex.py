# -*- coding: utf-8 -*-
"""This file contains MRUListEx Windows Registry plugins."""

import abc
import logging

import construct

from plaso.events import windows_events
from plaso.lib import binary
from plaso.parsers import winreg
from plaso.parsers.shared import shell_items
from plaso.parsers.winreg_plugins import interface


class MRUListExStringRegistryKeyFilter(
    interface.WindowsRegistryKeyWithValuesFilter):
  """Windows Registry key with values filter."""

  _IGNORE_KEY_PATH_SEGMENTS = frozenset([
      u'\\BagMRU\\'.upper(),
      u'\\Explorer\\ComDlg32\\OpenSavePidlMRU\\'.upper()])

  _IGNORE_KEY_PATH_SUFFIXES = frozenset([
      u'\\BagMRU'.upper(),
      u'\\Explorer\\StreamMRU'.upper(),
      u'\\Explorer\\ComDlg32\\OpenSavePidlMRU'.upper()])

  _VALUE_NAMES = [u'0', u'MRUListEx']

  def __init__(self):
    """Initializes Windows Registry key filter object."""
    super(MRUListExStringRegistryKeyFilter, self).__init__(self._VALUE_NAMES)

  def Match(self, registry_key):
    """Determines if a Windows Registry key matches the filter.

    Args:
      registry_key: a Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).

    Returns:
      A boolean value that indicates a match.
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
      1, 500, construct.ULInt32(u'entry_number'))

  _SOURCE_APPEND = u': MRUListEx'

  @abc.abstractmethod
  def _ParseMRUListExEntryValue(
      self, parser_mediator, key, entry_index, entry_number, **kwargs):
    """Parses the MRUListEx entry value.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: the Registry key (instance of dfwinreg.WinRegistryKey) that contains
           the MRUListEx value.
      entry_index: integer value representing the MRUListEx entry index.
      entry_number: integer value representing the entry number.

    Returns:
      A string containing the value.
    """

  def _ParseMRUListExValue(self, key):
    """Parses the MRUListEx value in a given Registry key.

    Args:
      key: the Registry key (instance of dfwinreg.WinRegistryKey) that contains
           the MRUListEx value.

    Returns:
      A MRUListEx value generator, which returns the MRU index number
      and entry value.
    """
    mru_list_value = key.GetValueByName(u'MRUListEx')

    # The key exists but does not contain a value named "MRUListEx".
    if not mru_list_value:
      return enumerate([])

    try:
      mru_list = self._MRULISTEX_STRUCT.parse(mru_list_value.data)
    except construct.FieldError:
      logging.warning(u'[{0:s}] Unable to parse the MRU key: {1:s}'.format(
          self.NAME, key.path))
      return enumerate([])

    return enumerate(mru_list)

  def _ParseMRUListExKey(self, parser_mediator, key, codepage=u'cp1252'):
    """Extract event objects from a MRUListEx Registry key.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: the Registry key (instance of dfwinreg.WinRegistryKey).
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    values_dict = {}
    for entry_index, entry_number in self._ParseMRUListExValue(key):
      # TODO: detect if list ends prematurely.
      # MRU lists are terminated with 0xffffffff (-1).
      if entry_number == 0xffffffff:
        break

      value_string = self._ParseMRUListExEntryValue(
          parser_mediator, key, entry_index, entry_number, codepage=codepage)

      value_text = u'Index: {0:d} [MRU Value {1:d}]'.format(
          entry_index + 1, entry_number)

      values_dict[value_text] = value_string

    event_object = windows_events.WindowsRegistryEvent(
        key.last_written_time, key.path, values_dict,
        offset=key.offset, source_append=self._SOURCE_APPEND)
    parser_mediator.ProduceEvent(event_object)


class MRUListExStringPlugin(BaseMRUListExPlugin):
  """Windows Registry plugin to parse a string MRUListEx."""

  NAME = u'mrulistex_string'
  DESCRIPTION = u'Parser for Most Recently Used (MRU) Registry data.'

  FILTERS = frozenset([MRUListExStringRegistryKeyFilter()])

  URLS = [
      u'http://forensicartifacts.com/2011/02/recentdocs/',
      u'https://github.com/libyal/winreg-kb/wiki/MRU-keys']

  _STRING_STRUCT = construct.Struct(
      u'string_and_shell_item',
      construct.RepeatUntil(
          lambda obj, ctx: obj == b'\x00\x00', construct.Field(u'string', 2)))

  def _ParseMRUListExEntryValue(
      self, parser_mediator, key, entry_index, entry_number, **unused_kwargs):
    """Parses the MRUListEx entry value.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: the Registry key (instance of dfwinreg.WinRegistryKey) that contains
           the MRUListEx value.
      entry_index: integer value representing the MRUListEx entry index.
      entry_number: integer value representing the entry number.

    Returns:
      A string containing the value.
    """
    value_string = u''

    value = key.GetValueByName(u'{0:d}'.format(entry_number))
    if value is None:
      logging.debug(
          u'[{0:s}] Missing MRUListEx entry value: {1:d} in key: {2:s}.'.format(
              self.NAME, entry_number, key.path))

    elif value.DataIsString():
      value_string = value.GetData()

    elif value.DataIsBinaryData():
      logging.debug((
          u'[{0:s}] Non-string MRUListEx entry value: {1:d} parsed as string '
          u'in key: {2:s}.').format(self.NAME, entry_number, key.path))
      utf16_stream = binary.ByteStreamCopyToUTF16Stream(value.data)

      try:
        value_string = utf16_stream.decode(u'utf-16-le')
      except UnicodeDecodeError as exception:
        value_string = binary.HexifyBuffer(utf16_stream)
        logging.warning((
            u'[{0:s}] Unable to decode UTF-16 stream: {1:s} in MRUListEx entry '
            u'value: {2:d} in key: {3:s} with error: {4:s}').format(
                self.NAME, value_string, entry_number, key.path, exception))

    return value_string

  def GetEntries(
      self, parser_mediator, registry_key, codepage=u'cp1252', **kwargs):
    """Extract event objects from a Registry key containing a MRUListEx value.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    self._ParseMRUListExKey(parser_mediator, registry_key, codepage=codepage)


class MRUListExShellItemListPlugin(BaseMRUListExPlugin):
  """Windows Registry plugin to parse a shell item list MRUListEx."""

  NAME = u'mrulistex_shell_item_list'
  DESCRIPTION = u'Parser for Most Recently Used (MRU) Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          u'Explorer\\ComDlg32\\OpenSavePidlMRU'),
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          u'Explorer\\StreamMRU')])

  def _ParseMRUListExEntryValue(
      self, parser_mediator, key, entry_index, entry_number, codepage=u'cp1252',
      **unused_kwargs):
    """Parses the MRUListEx entry value.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: the Registry key (instance of dfwinreg.WinRegistryKey) that contains
           the MRUListEx value.
      entry_index: integer value representing the MRUListEx entry index.
      entry_number: integer value representing the entry number.
      codepage: Optional extended ASCII string codepage. The default is cp1252.

    Returns:
      A string containing the value.
    """
    value_string = u''

    value = key.GetValueByName(u'{0:d}'.format(entry_number))
    if value is None:
      logging.debug(
          u'[{0:s}] Missing MRUListEx entry value: {1:d} in key: {2:s}.'.format(
              self.NAME, entry_number, key.path))

    elif not value.DataIsBinaryData():
      logging.debug((
          u'[{0:s}] Non-binary MRUListEx entry value: {1:d} in key: '
          u'{2:s}.').format(self.NAME, entry_number, key.path))

    elif value.data:
      shell_items_parser = shell_items.ShellItemsParser(key.path)
      shell_items_parser.ParseByteStream(
          parser_mediator, value.data, codepage=codepage)

      value_string = u'Shell item path: {0:s}'.format(
          shell_items_parser.CopyToPath())

    return value_string

  def GetEntries(
      self, parser_mediator, registry_key, codepage=u'cp1252', **kwargs):
    """Extract event objects from a Registry key containing a MRUListEx value.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    if registry_key.name != u'OpenSavePidlMRU':
      self._ParseMRUListExKey(parser_mediator, registry_key, codepage=codepage)

    if registry_key.name == u'OpenSavePidlMRU':
      # For the OpenSavePidlMRU MRUListEx we also need to parse its subkeys
      # since the Registry key path does not support wildcards yet.
      for subkey in registry_key.GetSubkeys():
        self._ParseMRUListExKey(parser_mediator, subkey, codepage=codepage)


class MRUListExStringAndShellItemPlugin(BaseMRUListExPlugin):
  """Windows Registry plugin to parse a string and shell item MRUListEx."""

  NAME = u'mrulistex_string_and_shell_item'
  DESCRIPTION = u'Parser for Most Recently Used (MRU) Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          u'Explorer\\RecentDocs')])

  _STRING_AND_SHELL_ITEM_STRUCT = construct.Struct(
      u'string_and_shell_item',
      construct.RepeatUntil(
          lambda obj, ctx: obj == b'\x00\x00', construct.Field(u'string', 2)),
      construct.Anchor(u'shell_item'))

  def _ParseMRUListExEntryValue(
      self, parser_mediator, key, entry_index, entry_number, codepage=u'cp1252',
      **unused_kwargs):
    """Parses the MRUListEx entry value.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: the Registry key (instance of dfwinreg.WinRegistryKey) that contains
           the MRUListEx value.
      entry_index: integer value representing the MRUListEx entry index.
      entry_number: integer value representing the entry number.
      codepage: Optional extended ASCII string codepage. The default is cp1252.

    Returns:
      A string containing the value.
    """
    value_string = u''

    value = key.GetValueByName(u'{0:d}'.format(entry_number))
    if value is None:
      logging.debug(
          u'[{0:s}] Missing MRUListEx entry value: {1:d} in key: {2:s}.'.format(
              self.NAME, entry_number, key.path))

    elif not value.DataIsBinaryData():
      logging.debug((
          u'[{0:s}] Non-binary MRUListEx entry value: {1:d} in key: '
          u'{2:s}.').format(self.NAME, entry_number, key.path))

    elif value.data:
      value_struct = self._STRING_AND_SHELL_ITEM_STRUCT.parse(value.data)

      try:
        # The struct includes the end-of-string character that we need
        # to strip off.
        path = b''.join(value_struct.string).decode(u'utf16')[:-1]
      except UnicodeDecodeError as exception:
        logging.warning((
            u'[{0:s}] Unable to decode string MRUListEx entry value: {1:d} '
            u'in key: {2:s} with error: {3:s}').format(
                self.NAME, entry_number, key.path, exception))
        path = u''

      if path:
        shell_item_list_data = value.data[value_struct.shell_item:]
        if not shell_item_list_data:
          logging.debug((
              u'[{0:s}] Missing shell item in MRUListEx entry value: {1:d}'
              u'in key: {2:s}').format(self.NAME, entry_number, key.path))
          value_string = u'Path: {0:s}'.format(path)

        else:
          shell_items_parser = shell_items.ShellItemsParser(key.path)
          shell_items_parser.ParseByteStream(
              parser_mediator, shell_item_list_data, codepage=codepage)

          value_string = u'Path: {0:s}, Shell item: [{1:s}]'.format(
              path, shell_items_parser.CopyToPath())

    return value_string

  def GetEntries(
      self, parser_mediator, registry_key, codepage=u'cp1252', **kwargs):
    """Extract event objects from a Registry key containing a MRUListEx value.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    self._ParseMRUListExKey(parser_mediator, registry_key, codepage=codepage)

    if registry_key.name == u'RecentDocs':
      # For the RecentDocs MRUListEx we also need to parse its subkeys
      # since the Registry key path does not support wildcards yet.
      for subkey in registry_key.GetSubkeys():
        self._ParseMRUListExKey(parser_mediator, subkey, codepage=codepage)


class MRUListExStringAndShellItemListPlugin(BaseMRUListExPlugin):
  """Windows Registry plugin to parse a string and shell item list MRUListEx."""

  NAME = u'mrulistex_string_and_shell_item_list'
  DESCRIPTION = u'Parser for Most Recently Used (MRU) Registry data.'

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
          u'Explorer\\ComDlg32\\LastVisitedPidlMRU')])

  _STRING_AND_SHELL_ITEM_LIST_STRUCT = construct.Struct(
      u'string_and_shell_item',
      construct.RepeatUntil(
          lambda obj, ctx: obj == b'\x00\x00', construct.Field(u'string', 2)),
      construct.Anchor(u'shell_item_list'))

  def _ParseMRUListExEntryValue(
      self, parser_mediator, key, entry_index, entry_number, codepage=u'cp1252',
      **unused_kwargs):
    """Parses the MRUListEx entry value.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: the Registry key (instance of dfwinreg.WinRegistryKey) that contains
           the MRUListEx value.
      entry_index: integer value representing the MRUListEx entry index.
      entry_number: integer value representing the entry number.
      codepage: Optional extended ASCII string codepage. The default is cp1252.

    Returns:
      A string containing the value.
    """
    value_string = u''

    value = key.GetValueByName(u'{0:d}'.format(entry_number))
    if value is None:
      logging.debug(
          u'[{0:s}] Missing MRUListEx entry value: {1:d} in key: {2:s}.'.format(
              self.NAME, entry_number, key.path))

    elif not value.DataIsBinaryData():
      logging.debug((
          u'[{0:s}] Non-binary MRUListEx entry value: {1:d} in key: '
          u'{2:s}.').format(self.NAME, entry_number, key.path))

    elif value.data:
      value_struct = self._STRING_AND_SHELL_ITEM_LIST_STRUCT.parse(value.data)

      try:
        # The struct includes the end-of-string character that we need
        # to strip off.
        path = b''.join(value_struct.string).decode(u'utf16')[:-1]
      except UnicodeDecodeError as exception:
        logging.warning((
            u'[{0:s}] Unable to decode string MRUListEx entry value: {1:d} '
            u'in key: {2:s} with error: {3:s}').format(
                self.NAME, entry_number, key.path, exception))
        path = u''

      if path:
        shell_item_list_data = value.data[value_struct.shell_item_list:]
        if not shell_item_list_data:
          logging.debug((
              u'[{0:s}] Missing shell item in MRUListEx entry value: {1:d}'
              u'in key: {2:s}').format(self.NAME, entry_number, key.path))
          value_string = u'Path: {0:s}'.format(path)

        else:
          shell_items_parser = shell_items.ShellItemsParser(key.path)
          shell_items_parser.ParseByteStream(
              parser_mediator, shell_item_list_data, codepage=codepage)

          value_string = u'Path: {0:s}, Shell item path: {1:s}'.format(
              path, shell_items_parser.CopyToPath())

    return value_string

  def GetEntries(
      self, parser_mediator, registry_key, codepage=u'cp1252', **kwargs):
    """Extract event objects from a Registry key containing a MRUListEx value.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      registry_key: A Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    self._ParseMRUListExKey(parser_mediator, registry_key, codepage=codepage)


winreg.WinRegistryParser.RegisterPlugins([
    MRUListExStringPlugin, MRUListExShellItemListPlugin,
    MRUListExStringAndShellItemPlugin, MRUListExStringAndShellItemListPlugin])
