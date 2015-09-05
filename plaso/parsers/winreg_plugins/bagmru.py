# -*- coding: utf-8 -*-
"""This file contains BagMRU Windows Registry plugins (shellbags)."""

import construct

from plaso.events import windows_events
from plaso.parsers.shared import shell_items
from plaso.parsers import winreg
from plaso.parsers.winreg_plugins import interface


class BagMRUPlugin(interface.WindowsRegistryPlugin):
  """Class that defines a BagMRU Windows Registry plugin."""

  NAME = u'bagmru'
  DESCRIPTION = u'Parser for BagMRU Registry data.'

  # TODO: remove REG_TYPE and use HKEY_CURRENT_USER instead.
  REG_TYPE = u'any'

  REG_KEYS = frozenset([
      u'\\Software\\Microsoft\\Windows\\Shell\\BagMRU',
      u'\\Software\\Microsoft\\Windows\\ShellNoRoam\\BagMRU',
      (u'\\Local Settings\\Software\\Microsoft\\Windows\\'
       u'Shell\\BagMRU'),
      (u'\\Local Settings\\Software\\Microsoft\\Windows\\'
       u'ShellNoRoam\\BagMRU'),
      (u'\\Wow6432Node\\Local Settings\\Software\\'
       u'Microsoft\\Windows\\Shell\\BagMRU'),
      (u'\\Wow6432Node\\Local Settings\\Software\\'
       u'Microsoft\\Windows\\ShellNoRoam\\BagMRU')])

  URLS = [u'https://code.google.com/p/winreg-kb/wiki/MRUKeys']

  _MRULISTEX_ENTRY = construct.ULInt32(u'entry_number')

  def _ParseMRUListExEntryValue(
      self, parser_mediator, key, entry_index, entry_number, text_dict,
      value_strings, parent_path_segments, codepage=u'cp1252', **unused_kwargs):
    """Parses the MRUListEx entry value.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: the Registry key (instance of winreg.WinRegKey) that contains
           the MRUListEx value.
      entry_index: integer value representing the MRUListEx entry index.
      entry_number: integer value representing the entry number.
      text_dict: text dictionary object to append textual strings.
      value_strings: value string dictionary object to append value strings.
      parent_path_segments: list containing the parent shell item path segments.
      codepage: Optional extended ASCII string codepage. The default is cp1252.

    Returns:
      The path segment of the shell item.
    """
    value = key.GetValue(u'{0:d}'.format(entry_number))
    path_segment = u'N/A'
    value_string = u''
    if value is None:
      parser_mediator.ProduceParseError(
          u'Missing MRUListEx entry value: {0:d} in key: {1:s}.'.format(
              entry_number, key.path))

    elif not value.DataIsBinaryData():
      parser_mediator.ProduceParseError(
          u'Non-binary MRUListEx entry value: {0:d} in key: {1:s}.'.format(
              entry_number, key.path))

    elif value.data:
      shell_items_parser = shell_items.ShellItemsParser(key.path)
      shell_items_parser.UpdateChainAndParse(
          parser_mediator, value.data, parent_path_segments,
          codepage=codepage)

      path_segment = shell_items_parser.GetUpperPathSegment()
      value_string = shell_items_parser.CopyToPath()

      value_strings[entry_number] = value_string

      value_string = u'Shell item path: {0:s}'.format(value_string)

    value_text = u'Index: {0:d} [MRU Value {1:d}]'.format(
        entry_index + 1, entry_number)

    text_dict[value_text] = value_string

    return path_segment

  def _ParseMRUListExValue(self, parser_mediator, key):
    """Parses the MRUListEx value in a given Registry key.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: the Registry key (instance of winreg.WinRegKey) that contains
           the MRUListEx value.

    Yields:
      A tuple of the MRUListEx index and entry number, where 0 is the first
      index value.
    """
    mru_list_value = key.GetValue(u'MRUListEx')
    if mru_list_value:
      mrulistex_data = mru_list_value.data
      data_size = len(mrulistex_data)
      _, remainder = divmod(data_size, 4)

      if remainder != 0:
        parser_mediator.ProduceParseError((
            u'MRUListEx value data size is not a multitude of 4 '
            u'in MRU key: {0:s}').format(key.path))
        data_size -= remainder

      entry_index = 0
      data_offset = 0
      while data_offset < data_size:
        try:
          entry_number = self._MRULISTEX_ENTRY.parse(
              mrulistex_data[data_offset:])
          yield entry_index, entry_number
        except construct.FieldError:
          parser_mediator.ProduceParseError((
              u'Unable to parse MRUListEx value data at offset: {0:d} '
              u'in MRU key: {1:s}').format(data_offset, key.path))

        entry_index += 1
        data_offset += 4

  def _ParseSubKey(
      self, parser_mediator, key, parent_path_segments, registry_file_type=None,
      codepage=u'cp1252'):
    """Extract event objects from a MRUListEx Registry key.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: the Registry key (instance of winreg.WinRegKey).
      parent_path_segments: list containing the parent shell item path segments.
      registry_file_type: Optional string containing the Windows Registry file
                          type, e.g. NTUSER, SOFTWARE. The default is None.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    entry_numbers = {}
    text_dict = {}
    value_strings = {}

    found_terminator = False
    for index, entry_number in self._ParseMRUListExValue(parser_mediator, key):
      if entry_number == 0xffffffff:
        found_terminator = True
        continue

      if found_terminator:
        parser_mediator.ProduceParseError((
            u'Found additional MRUListEx entries after terminator '
            u'in key: {0:s}.').format(key.path))

        # Only create one parser error per terminator.
        found_terminator = False

      path_segment = self._ParseMRUListExEntryValue(
          parser_mediator, key, index, entry_number, text_dict, value_strings,
          parent_path_segments, codepage=codepage)

      entry_numbers[entry_number] = path_segment

    event_object = windows_events.WindowsRegistryEvent(
        key.last_written_timestamp, key.path, text_dict,
        offset=key.offset, registry_file_type=registry_file_type,
        urls=self.URLS, source_append=u': BagMRU')
    parser_mediator.ProduceEvent(event_object)

    for entry_number, path_segment in entry_numbers.iteritems():
      sub_key = key.GetSubkey(u'{0:d}'.format(entry_number))
      if not sub_key:
        parser_mediator.ProduceParseError(
            u'Missing BagMRU sub key: {0:d} in key: {1:s}.'.format(
                entry_number, key.path))
        continue

      parent_path_segments.append(path_segment)
      self._ParseSubKey(
          parser_mediator, sub_key, parent_path_segments, codepage=codepage)
      _ = parent_path_segments.pop()

  def GetEntries(
      self, parser_mediator, key=None, registry_file_type=None,
      codepage=u'cp1252', **unused_kwargs):
    """Extract event objects from a Registry key containing a MRUListEx value.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_file_type: Optional string containing the Windows Registry file
                          type, e.g. NTUSER, SOFTWARE. The default is None.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    self._ParseSubKey(
        parser_mediator, key, [], registry_file_type=registry_file_type,
        codepage=codepage)


winreg.WinRegistryParser.RegisterPlugin(BagMRUPlugin)
