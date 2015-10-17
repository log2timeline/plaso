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

  FILTERS = frozenset([
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\Shell\\BagMRU'),
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\ShellNoRoam\\'
          u'BagMRU'),
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Classes\\Local Settings\\Software\\'
          u'Microsoft\\Windows\\Shell\\BagMRU'),
      interface.WindowsRegistryKeyPathFilter(
          u'HKEY_CURRENT_USER\\Software\\Classes\\Local Settings\\Software\\'
          u'Microsoft\\Windows\\ShellNoRoam\\BagMRU')])

  URLS = [
      (u'https://github.com/libyal/winreg-kb/blob/master/documentation/'
       u'MRU%20keys.asciidoc#bagmru-key')]

  _MRULISTEX_ENTRY = construct.ULInt32(u'entry_number')

  _SOURCE_APPEND = u': BagMRU'

  def _ParseMRUListExEntryValue(
      self, parser_mediator, key, entry_index, entry_number, values_dict,
      value_strings, parent_path_segments, codepage=u'cp1252', **unused_kwargs):
    """Parses the MRUListEx entry value.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      key: the Registry key (instance of dfwinreg.WinRegistryKey) that contains
           the MRUListEx value.
      entry_index: integer value representing the MRUListEx entry index.
      entry_number: integer value representing the entry number.
      values_dict: dictionary object containing values of the key.
      value_strings: value string dictionary object to append value strings.
      parent_path_segments: list containing the parent shell item path segments.
      codepage: optional extended ASCII string codepage.

    Returns:
      The path segment of the shell item.
    """
    value = key.GetValueByName(u'{0:d}'.format(entry_number))
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
      shell_items_parser.ParseDataStream(
          parser_mediator, value.data,
          parent_path_segments=parent_path_segments, codepage=codepage)

      path_segment = shell_items_parser.GetUpperPathSegment()
      value_string = shell_items_parser.CopyToPath()

      value_strings[entry_number] = value_string

      value_string = u'Shell item path: {0:s}'.format(value_string)

    value_text = u'Index: {0:d} [MRU Value {1:d}]'.format(
        entry_index + 1, entry_number)

    values_dict[value_text] = value_string

    return path_segment

  def _ParseMRUListExValue(self, parser_mediator, key):
    """Parses the MRUListEx value in a given Registry key.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      key: the Registry key (instance of dfwinreg.WinRegistryKey) that contains
           the MRUListEx value.

    Yields:
      A tuple of the MRUListEx index and entry number, where 0 is the first
      index value.
    """
    mru_list_value = key.GetValueByName(u'MRUListEx')
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
      self, parser_mediator, key, parent_path_segments, codepage=u'cp1252'):
    """Extract event objects from a MRUListEx Registry key.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      key: the Registry key (instance of dfwinreg.WinRegistryKey).
      parent_path_segments: list containing the parent shell item path segments.
      codepage: optional extended ASCII string codepage. The default is cp1252.
    """
    entry_numbers = {}
    values_dict = {}
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
          parser_mediator, key, index, entry_number, values_dict,
          value_strings, parent_path_segments, codepage=codepage)

      entry_numbers[entry_number] = path_segment

    event_object = windows_events.WindowsRegistryEvent(
        key.last_written_time, key.path, values_dict,
        offset=key.offset, source_append=self._SOURCE_APPEND, urls=self.URLS)
    parser_mediator.ProduceEvent(event_object)

    for entry_number, path_segment in entry_numbers.iteritems():
      sub_key = key.GetSubkeyByName(u'{0:d}'.format(entry_number))
      if not sub_key:
        parser_mediator.ProduceParseError(
            u'Missing BagMRU sub key: {0:d} in key: {1:s}.'.format(
                entry_number, key.path))
        continue

      parent_path_segments.append(path_segment)
      self._ParseSubKey(
          parser_mediator, sub_key, parent_path_segments, codepage=codepage)
      parent_path_segments.pop()

  def GetEntries(
      self, parser_mediator, registry_key, codepage=u'cp1252', **unused_kwargs):
    """Extract event objects from a Registry key containing a MRUListEx value.

    Args:
      parser_mediator: a parser mediator object (instance of ParserMediator).
      registry_key: a Windows Registry key (instance of
                    dfwinreg.WinRegistryKey).
      codepage: optional extended ASCII string codepage. The default is cp1252.
    """
    self._ParseSubKey(parser_mediator, registry_key, [], codepage=codepage)


winreg.WinRegistryParser.RegisterPlugin(BagMRUPlugin)
