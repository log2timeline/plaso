#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains MRUListEx Windows Registry plugins."""

import abc
import logging

import construct

from plaso.events import windows_events
from plaso.lib import binary
from plaso.parsers import winreg
from plaso.parsers.shared import shell_items
from plaso.parsers.winreg_plugins import interface


# A mixin class is used here to not to have the duplicate functionality
# to parse the MRUListEx Registry values. However multiple inheritance
# and thus mixins are to be used sparsely in this codebase, hence we need
# to find a better solution in not needing to distinguish between key and
# value plugins.
# TODO: refactor Registry key and value plugin to rid ourselved of the mixin.
class MRUListExPluginMixin(object):
  """Class for common MRUListEx Windows Registry plugin functionality."""

  _MRULISTEX_STRUCT = construct.Range(1, 500, construct.ULInt32('entry_number'))

  @abc.abstractmethod
  def _ParseMRUListExEntryValue(
      self, parser_context, key, entry_index, entry_number, text_dict,
      **kwargs):
    """Parses the MRUListEx entry value.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      key: the Registry key (instance of winreg.WinRegKey) that contains
           the MRUListEx value.
      entry_index: integer value representing the MRUListEx entry index.
      entry_number: integer value representing the entry number.
      text_dict: text dictionary object to append textual strings.
    """

  def _ParseMRUListExValue(self, key):
    """Parses the MRUListEx value in a given Registry key.

    Args:
      key: the Registry key (instance of winreg.WinRegKey) that contains
           the MRUListEx value.

    Returns:
      A MRUListEx value generator, which returns the MRU index number
      and entry value.
    """
    mru_list_value = key.GetValue('MRUListEx')

    try:
      mru_list = self._MRULISTEX_STRUCT.parse(mru_list_value.data)
    except construct.FieldError:
      logging.warning(u'[{0:s}] Unable to parse the MRU key: {2:s}'.format(
          self.NAME, key.path))
      return enumerate([])

    return enumerate(mru_list)

  def _ParseMRUListExKey(
      self, parser_context, key, registry_type=None, codepage='cp1252'):
    """Extract event objects from a MRUListEx Registry key.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      key: the Registry key (instance of winreg.WinRegKey).
      registry_type: Optional Registry type string. The default is None.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    text_dict = {}
    for index, entry_number in self._ParseMRUListExValue(key):
      # TODO: detect if list ends prematurely.
      # MRU lists are terminated with 0xffffffff (-1).
      if entry_number == 0xffffffff:
        break

      self._ParseMRUListExEntryValue(
          parser_context, key, index, entry_number, text_dict,
          codepage=codepage)

    event_object = windows_events.WindowsRegistryEvent(
        key.last_written_timestamp, key.path, text_dict,
        offset=key.offset, registry_type=registry_type,
        source_append=': MRUListEx')
    parser_context.ProduceEvent(event_object, plugin_name=self.NAME)


class MRUListExStringPlugin(interface.ValuePlugin, MRUListExPluginMixin):
  """Windows Registry plugin to parse a string MRUListEx."""

  NAME = 'winreg_mrulistex_string'
  DESCRIPTION = u'Parser for Most Recently Used (MRU) Registry data.'

  REG_TYPE = 'any'
  REG_VALUES = frozenset(['MRUListEx', '0'])

  URLS = [
      u'http://forensicartifacts.com/2011/02/recentdocs/',
      u'https://code.google.com/p/winreg-kb/wiki/MRUKeys']

  _STRING_STRUCT = construct.Struct(
      'string_and_shell_item',
      construct.RepeatUntil(
          lambda obj, ctx: obj == '\x00\x00', construct.Field('string', 2)))

  def _ParseMRUListExEntryValue(
      self, parser_context, key, entry_index, entry_number, text_dict,
      **unused_kwargs):
    """Parses the MRUListEx entry value.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      key: the Registry key (instance of winreg.WinRegKey) that contains
           the MRUListEx value.
      entry_index: integer value representing the MRUListEx entry index.
      entry_number: integer value representing the entry number.
      text_dict: text dictionary object to append textual strings.
    """
    value_string = u''

    value = key.GetValue(u'{0:d}'.format(entry_number))
    if value is None:
      logging.debug(
          u'[{0:s}] Missing MRUListEx entry value: {1:d} in key: {2:s}.'.format(
              self.NAME, entry_number, key.path))

    elif value.DataIsString():
      value_string = value.data

    elif value.DataIsBinaryData():
      logging.debug((
          u'[{0:s}] Non-string MRUListEx entry value: {1:d} parsed as string '
          u'in key: {2:s}.').format(self.NAME, entry_number, key.path))
      utf16_stream = binary.ByteStreamCopyToUtf16Stream(value.data)

      try:
        value_string = utf16_stream.decode('utf-16-le')
      except UnicodeDecodeError as exception:
        value_string = binary.HexifyBuffer(utf16_stream)
        logging.warning((
            u'[{0:s}] Unable to decode UTF-16 stream: {1:s} in MRUListEx entry '
            u'value: {2:d} in key: {3:s} with error: {4:s}').format(
                self.NAME, value_string, entry_number, key.path, exception))

    value_text = u'Index: {0:d} [MRU Value {1:d}]'.format(
        entry_index + 1, entry_number)

    text_dict[value_text] = value_string

  def GetEntries(
      self, parser_context, key=None, registry_type=None, codepage='cp1252',
      **unused_kwargs):
    """Extract event objects from a Registry key containing a MRUListEx value.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    self._ParseMRUListExKey(
        parser_context, key, registry_type=registry_type, codepage=codepage)

  def Process(self, parser_context, key=None, codepage='cp1252', **kwargs):
    """Determine if we can process this Registry key or not.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      key: A Windows Registry key (instance of WinRegKey).
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    # Prevent this plugin triggering on sub paths of non-string MRUListEx
    # values.
    if (u'BagMRU' in key.path or u'Explorer\\StreamMRU' in key.path or
        u'\\Explorer\\ComDlg32\\OpenSavePidlMRU' in key.path):
      return

    super(MRUListExStringPlugin, self).Process(
        parser_context, key=key, codepage=codepage, **kwargs)


class MRUListExShellItemListPlugin(interface.KeyPlugin, MRUListExPluginMixin):
  """Windows Registry plugin to parse a shell item list MRUListEx."""

  NAME = 'winreg_mrulistex_shell_item_list'
  DESCRIPTION = u'Parser for Most Recently Used (MRU) Registry data.'

  REG_TYPE = 'any'
  REG_KEYS = frozenset([
      # The regular expression indicated a file extension (.jpg) or '*'.
      (u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\ComDlg32\\'
       u'OpenSavePidlMRU'),
      u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\StreamMRU'])

  def _ParseMRUListExEntryValue(
      self, parser_context, key, entry_index, entry_number, text_dict,
      codepage='cp1252', **unused_kwargs):
    """Parses the MRUListEx entry value.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      key: the Registry key (instance of winreg.WinRegKey) that contains
           the MRUListEx value.
      entry_index: integer value representing the MRUListEx entry index.
      entry_number: integer value representing the entry number.
      text_dict: text dictionary object to append textual strings.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    value_string = u''

    value = key.GetValue(u'{0:d}'.format(entry_number))
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
      shell_items_parser.Parse(parser_context, value.data, codepage=codepage)

      value_string = u'Shell item list: [{0:s}]'.format(
          shell_items_parser.CopyToPath())

    value_text = u'Index: {0:d} [MRU Value {1:d}]'.format(
        entry_index + 1, entry_number)

    text_dict[value_text] = value_string

  def GetEntries(
      self, parser_context, key=None, registry_type=None, codepage='cp1252',
      **unused_kwargs):
    """Extract event objects from a Registry key containing a MRUListEx value.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    if key.name != u'OpenSavePidlMRU':
      self._ParseMRUListExKey(
          parser_context, key, registry_type=registry_type, codepage=codepage)

    if key.name == u'OpenSavePidlMRU':
      # For the OpenSavePidlMRU MRUListEx we also need to parse its subkeys
      # since the Registry key path does not support wildcards yet.
      for subkey in key.GetSubkeys():
        self._ParseMRUListExKey(
            parser_context, subkey, registry_type=registry_type,
            codepage=codepage)


class MRUListExStringAndShellItemPlugin(
    interface.KeyPlugin, MRUListExPluginMixin):
  """Windows Registry plugin to parse a string and shell item MRUListEx."""

  NAME = 'winreg_mrulistex_string_and_shell_item'
  DESCRIPTION = u'Parser for Most Recently Used (MRU) Registry data.'

  REG_TYPE = 'any'
  REG_KEYS = frozenset([
      u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\RecentDocs'])

  _STRING_AND_SHELL_ITEM_STRUCT = construct.Struct(
      'string_and_shell_item',
      construct.RepeatUntil(
          lambda obj, ctx: obj == '\x00\x00', construct.Field('string', 2)),
      construct.Anchor('shell_item'))

  def _ParseMRUListExEntryValue(
      self, parser_context, key, entry_index, entry_number, text_dict,
      codepage='cp1252', **unused_kwargs):
    """Parses the MRUListEx entry value.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      key: the Registry key (instance of winreg.WinRegKey) that contains
           the MRUListEx value.
      entry_index: integer value representing the MRUListEx entry index.
      entry_number: integer value representing the entry number.
      text_dict: text dictionary object to append textual strings.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    value_string = u''

    value = key.GetValue(u'{0:d}'.format(entry_number))
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
        path = ''.join(value_struct.string).decode('utf16')[:-1]
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
          shell_items_parser.Parse(
              parser_context, shell_item_list_data, codepage=codepage)

          value_string = u'Path: {0:s}, Shell item: [{1:s}]'.format(
              path, shell_items_parser.CopyToPath())

    value_text = u'Index: {0:d} [MRU Value {1:d}]'.format(
        entry_index + 1, entry_number)

    text_dict[value_text] = value_string

  def GetEntries(
      self, parser_context, key=None, registry_type=None, codepage='cp1252',
      **unused_kwargs):
    """Extract event objects from a Registry key containing a MRUListEx value.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    self._ParseMRUListExKey(
        parser_context, key, registry_type=registry_type, codepage=codepage)

    if key.name == u'RecentDocs':
      # For the RecentDocs MRUListEx we also need to parse its subkeys
      # since the Registry key path does not support wildcards yet.
      for subkey in key.GetSubkeys():
        self._ParseMRUListExKey(
            parser_context, subkey, registry_type=registry_type,
            codepage=codepage)


class MRUListExStringAndShellItemListPlugin(
    interface.KeyPlugin, MRUListExPluginMixin):
  """Windows Registry plugin to parse a string and shell item list MRUListEx."""

  NAME = 'winreg_mrulistex_string_and_shell_item_list'
  DESCRIPTION = u'Parser for Most Recently Used (MRU) Registry data.'

  REG_TYPE = 'any'
  REG_KEYS = frozenset([
      (u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\ComDlg32\\'
       u'LastVisitedPidlMRU')])

  _STRING_AND_SHELL_ITEM_LIST_STRUCT = construct.Struct(
      'string_and_shell_item',
      construct.RepeatUntil(
          lambda obj, ctx: obj == '\x00\x00', construct.Field('string', 2)),
      construct.Anchor('shell_item_list'))

  def _ParseMRUListExEntryValue(
      self, parser_context, key, entry_index, entry_number, text_dict,
      codepage='cp1252', **unused_kwargs):
    """Parses the MRUListEx entry value.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      key: the Registry key (instance of winreg.WinRegKey) that contains
           the MRUListEx value.
      entry_index: integer value representing the MRUListEx entry index.
      entry_number: integer value representing the entry number.
      text_dict: text dictionary object to append textual strings.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    value_string = u''

    value = key.GetValue(u'{0:d}'.format(entry_number))
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
        path = ''.join(value_struct.string).decode('utf16')[:-1]
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
          shell_items_parser.Parse(
              parser_context, shell_item_list_data, codepage=codepage)

          value_string = u'Path: {0:s}, Shell item list: [{1:s}]'.format(
              path, shell_items_parser.CopyToPath())

    value_text = u'Index: {0:d} [MRU Value {1:d}]'.format(
        entry_index + 1, entry_number)

    text_dict[value_text] = value_string

  def GetEntries(
      self, parser_context, key=None, registry_type=None, codepage='cp1252',
      **unused_kwargs):
    """Extract event objects from a Registry key containing a MRUListEx value.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    self._ParseMRUListExKey(
        parser_context, key, registry_type=registry_type, codepage=codepage)


winreg.WinRegistryParser.RegisterPlugins([
    MRUListExStringPlugin, MRUListExShellItemListPlugin,
    MRUListExStringAndShellItemPlugin, MRUListExStringAndShellItemListPlugin])
