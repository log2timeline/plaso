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


# A mixin class is used here to not to have the duplicate functionality
# to parse the MRUList Registry values. However multiple inheritance
# and thus mixins are to be used sparsely in this codebase, hence we need
# to find a better solution in not needing to distinguish between key and
# value plugins.
# TODO: refactor Registry key and value plugin to rid ourselves of the mixin.
class MRUListPluginMixin(object):
  """Class for common MRUList Windows Registry plugin functionality."""

  _MRULIST_STRUCT = construct.Range(1, 500, construct.ULInt16('entry_letter'))

  @abc.abstractmethod
  def _ParseMRUListEntryValue(
      self, parser_mediator, key, entry_index, entry_letter, file_entry=None,
      parser_chain=None, **kwargs):
    """Parses the MRUList entry value.

    Args:
      parser_mediator: A parser context object (instance of ParserContext).
      key: the Registry key (instance of winreg.WinRegKey) that contains
           the MRUList value.
      entry_index: integer value representing the MRUList entry index.
      entry_letter: character value representing the entry.
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
            The default is None.
      parser_chain: Optional string containing the parsing chain up to this
              point. The default is None.

    Returns:
      A string containing the value.
    """

  def _ParseMRUListValue(self, key):
    """Parses the MRUList value in a given Registry key.

    Args:
      key: the Registry key (instance of winreg.WinRegKey) that contains
           the MRUList value.

    Returns:
      A MRUList value generator, which returns the MRU index number
      and entry value.
    """
    mru_list_value = key.GetValue('MRUList')

    # The key exists but does not contain a value named "MRUList".
    if not mru_list_value:
      return enumerate([])

    try:
      mru_list = self._MRULIST_STRUCT.parse(mru_list_value.raw_data)
    except construct.FieldError:
      logging.warning(u'[{0:s}] Unable to parse the MRU key: {1:s}'.format(
          self.NAME, key.path))
      return enumerate([])

    return enumerate(mru_list)

  def _ParseMRUListKey(
      self, parser_mediator, key, registry_type=None, file_entry=None,
      parser_chain=None, codepage='cp1252'):
    """Extract event objects from a MRUList Registry key.

    Args:
      parser_mediator: A parser context object (instance of ParserContext).
      key: the Registry key (instance of winreg.WinRegKey).
      registry_type: Optional Registry type string. The default is None.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
            The default is None.
      parser_chain: Optional string containing the parsing chain up to this
              point. The default is None.
    """
    text_dict = {}
    for entry_index, entry_letter in self._ParseMRUListValue(key):
      # TODO: detect if list ends prematurely.
      # MRU lists are terminated with \0 (0x0000).
      if entry_letter == 0:
        break

      entry_letter = chr(entry_letter)

      value_string = self._ParseMRUListEntryValue(
          parser_mediator, key, entry_index, entry_letter,
          codepage=codepage, file_entry=file_entry, parser_chain=parser_chain)

      value_text = u'Index: {0:d} [MRU Value {1:s}]'.format(
          entry_index + 1, entry_letter)

      text_dict[value_text] = value_string

    event_object = windows_events.WindowsRegistryEvent(
        key.last_written_timestamp, key.path, text_dict,
        offset=key.offset, registry_type=registry_type,
        source_append=': MRU List')
    parser_mediator.ProduceEvent(event_object)


class MRUListStringPlugin(interface.ValuePlugin, MRUListPluginMixin):
  """Windows Registry plugin to parse a string MRUList."""

  NAME = 'winreg_mrulist_string'
  DESCRIPTION = u'Parser for Most Recently Used (MRU) Registry data.'

  REG_TYPE = 'any'
  REG_VALUES = frozenset(['MRUList', 'a'])
  URLS = [u'http://forensicartifacts.com/tag/mru/']

  def _ParseMRUListEntryValue(
      self, parser_mediator, key, entry_index, entry_letter, **unused_kwargs):
    """Parses the MRUList entry value.

    Args:
      parser_mediator: A parser context object (instance of ParserContext).
      key: the Registry key (instance of winreg.WinRegKey) that contains
           the MRUList value.
      entry_index: integer value representing the MRUList entry index.
      entry_letter: character value representing the entry.

    Returns:
      A string containing the value.
    """
    value_string = u''

    value = key.GetValue(u'{0:s}'.format(entry_letter))
    if value is None:
      logging.debug(
          u'[{0:s}] Missing MRUList entry value: {1:s} in key: {2:s}.'.format(
              self.NAME, entry_letter, key.path))

    elif value.DataIsString():
      value_string = value.data

    elif value.DataIsBinaryData():
      logging.debug((
          u'[{0:s}] Non-string MRUList entry value: {1:s} parsed as string '
          u'in key: {2:s}.').format(self.NAME, entry_letter, key.path))
      utf16_stream = binary.ByteStreamCopyToUtf16Stream(value.data)

      try:
        value_string = utf16_stream.decode('utf-16-le')
      except UnicodeDecodeError as exception:
        value_string = binary.HexifyBuffer(utf16_stream)
        logging.warning((
            u'[{0:s}] Unable to decode UTF-16 stream: {1:s} in MRUList entry '
            u'value: {2:s} in key: {3:s} with error: {4:s}').format(
                self.NAME, value_string, entry_letter, key.path, exception))

    return value_string

  def GetEntries(
      self, parser_mediator, key=None, registry_type=None, codepage='cp1252',
      **kwargs):
    """Extracts event objects from a MRU list.

    Args:
      parser_mediator: A parser context object (instance of ParserContext).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    self._ParseMRUListKey(
        parser_mediator, key, registry_type=registry_type, codepage=codepage)

  def Process(
      self, parser_mediator, key=None, registry_type=None, codepage='cp1252',
      **kwargs):
    """Determine if we can process this Registry key or not.

    Args:
      parser_mediator: A parser context object (instance of ParserContext).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    # Prevent this plugin triggering on sub paths of non-string MRUList values.
    if u'Explorer\\DesktopStreamMRU' in key.path:
      return

    super(MRUListStringPlugin, self).Process(
        parser_mediator, key=key, registry_type=registry_type,
        codepage=codepage)



class MRUListShellItemListPlugin(interface.KeyPlugin, MRUListPluginMixin):
  """Windows Registry plugin to parse a shell item list MRUList."""

  NAME = 'winreg_mrulist_shell_item_list'
  DESCRIPTION = u'Parser for Most Recently Used (MRU) Registry data.'

  REG_TYPE = 'any'
  REG_KEYS = frozenset([
      (u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\'
       u'DesktopStreamMRU')])

  URLS = [u'https://github.com/libyal/winreg-kb/wiki/MRU-keys']

  def _ParseMRUListEntryValue(
      self, parser_mediator, key, entry_index, entry_letter, codepage='cp1252',
      file_entry=None, parser_chain=None, **unused_kwargs):
    """Parses the MRUList entry value.

    Args:
      parser_mediator: A parser context object (instance of ParserContext).
      key: the Registry key (instance of winreg.WinRegKey) that contains
           the MRUList value.
      entry_index: integer value representing the MRUList entry index.
      entry_letter: character value representing the entry.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
            The default is None.
      parser_chain: Optional string containing the parsing chain up to this
              point. The default is None.

    Returns:
      A string containing the value.
    """
    value_string = u''

    value = key.GetValue(u'{0:s}'.format(entry_letter))
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
      shell_items_parser.UpdateChainAndParse(
          parser_mediator, value.data, None, codepage=codepage)

      value_string = u'Shell item path: {0:s}'.format(
          shell_items_parser.CopyToPath())

    return value_string

  def GetEntries(
      self, parser_mediator, key=None, registry_type=None, codepage='cp1252',
      **kwargs):
    """Extract event objects from a Registry key containing a MRUList value.

    Args:
      parser_mediator: A parser context object (instance of ParserContext).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    self._ParseMRUListKey(
        parser_mediator, key, registry_type=registry_type, codepage=codepage)


winreg.WinRegistryParser.RegisterPlugins([
    MRUListStringPlugin, MRUListShellItemListPlugin])
