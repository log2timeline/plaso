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
import pyfwsi

from plaso.lib import binary
from plaso.lib import event
from plaso.parsers.winreg_plugins import interface
from plaso.winnt import shell_item


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
  def _CopyValueToString(self, value, **kwargs):
    """Returns a string that represents the MRU entry.

    Args:
      value: the Registry value (instance of winreg.WinRegValue) that contains
             the MRUListEx entry.

    Returns:
      An Unicode string representing the MRU entry.
    """

  def _ParseMRUListExValue(self, key):
    """Parses the MRUListEx value in a given Registry key.

    Args:
      key: the Registry key (instance of winreg.WinRegKey) that contains
           the MRUListEx value.

    Yields:
      A MRUListEx value generator, which returns the MRU index number
      and entry value.
    """
    mru_list_value = key.GetValue('MRUListEx')

    try:
      mru_list = self._MRULISTEX_STRUCT.parse(mru_list_value.data)
    except construct.FieldError:
      logging.warning(u'Unable to parse the MRU key: {0:s}'.format(
          key.path))
      return enumerate([])

    return enumerate(mru_list)

  def _ParseMRUListExKey(self, key, codepage='cp1252'):
    """Extract event objects from a MRUListEx Registry key.

    Args:
      key: the Registry key (instance of winreg.WinRegKey).
      codepage: Optional extended ASCII string codepage. The default is cp1252.

    Yields:
      Event objects (instances of EventObject).
    """
    event_timestamp = key.last_written_timestamp

    text_dict = {}
    for index, entry in self._ParseMRUListExValue(key):
      # TODO: detect if list ends prematurely.
      # MRU lists are terminated with 0xffffffff (-1).
      if entry == 0xffffffff:
        break
      value_text = u'Index: {0:d} [MRU Value {1:d}]'.format(index + 1, entry)

      value = key.GetValue(u'{0:d}'.format(entry))
      if value is None:
        logging.debug(u'Missing MRU value: {0:d}.'.format(entry))
        value_string = u''
      else:
        value_string = self._CopyValueToString(value, codepage=codepage)

      text_dict[value_text] = value_string

    yield event.WinRegistryEvent(
        key.path, text_dict, timestamp=event_timestamp,
        source_append=': MRUListEx')


class MRUListExStringPlugin(interface.ValuePlugin, MRUListExPluginMixin):
  """Windows Registry plugin to parse a string MRUListEx."""

  NAME = 'winreg_mrulistex_string'

  REG_TYPE = 'any'
  REG_VALUES = frozenset(['MRUListEx', '0'])

  URLS = [
      u'http://forensicartifacts.com/2011/02/recentdocs/',
      u'https://code.google.com/p/winreg-kb/wiki/MRUKeys']

  _STRING_STRUCT = construct.Struct(
      'string_and_shell_item',
      construct.RepeatUntil(
          lambda obj, ctx: obj == '\x00\x00', construct.Field('string', 2)))

  def _CopyValueToString(self, value, **unused_kwargs):
    """Returns a string that represents the MRU entry.

    Args:
      value: the Registry value (instance of winreg.WinRegValue) that contains
             the MRUListEx entry.

    Returns:
      An Unicode string representing the MRU entry.
    """
    if value.DataIsString():
      return value.data

    if value.DataIsBinaryData():
      logging.debug(u'Non-string MRUListEx parsed as string.')
      return binary.Ut16StreamCopyToString(value.data)

    return u''

  def GetEntries(self, key=None, codepage='cp1252', **unused_kwargs):
    """Extract event objects from a Registry key containing a MRUListEx value.

    Args:
      key: the Registry key (instance of winreg.WinRegKey).
      codepage: Optional extended ASCII string codepage. The default is cp1252.

    Yields:
      Event objects (instances of EventObject).
    """
    for event_object in self._ParseMRUListExKey(key, codepage=codepage):
      yield event_object


class MRUListExShellItemListPlugin(interface.KeyPlugin, MRUListExPluginMixin):
  """Windows Registry plugin to parse a shell item list MRUListEx."""

  NAME = 'winreg_mrulistex_shell_item_list'

  REG_TYPE = 'any'
  REG_KEYS = frozenset([
      # The regular expression indicated a file extension (.jpg) or '*'.
      (u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\ComDlg32\\'
       u'OpenSavePidlMRU'),
      u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\StreamMRU'])

  def _CopyValueToString(self, value, codepage='cp1252', **unused_kwargs):
    """Returns a string that represents the MRU entry.

    Args:
      value: the Registry value (instance of winreg.WinRegValue) that contains
             the MRUListEx entry.
      codepage: Optional extended ASCII string codepage. The default is cp1252.

    Returns:
      An Unicode string representing the MRU entry.
    """
    if value.data_type != value.REG_BINARY:
      return u''

    shell_item_list = pyfwsi.item_list()

    shell_item_list.copy_from_byte_stream(value.data, ascii_codepage=codepage)

    return u'Shell item list: [{0:s}]'.format(
        shell_item.ShellItemListCopyToPath(shell_item_list))

  def GetEntries(self, key=None, codepage='cp1252', **unused_kwargs):
    """Extract event objects from a Registry key containing a MRUListEx value.

    Args:
      key: the Registry key (instance of winreg.WinRegKey).
      codepage: Optional extended ASCII string codepage. The default is cp1252.

    Yields:
      Event objects (instances of EventObject).
    """
    if key.name != u'OpenSavePidlMRU':
      for event_object in self._ParseMRUListExKey(key, codepage=codepage):
        yield event_object

    if key.name == u'OpenSavePidlMRU':
      # For the OpenSavePidlMRU MRUListEx we also need to parse its subkeys
      # since the Registry key path does not support wildcards yet.
      for subkey in key.GetSubkeys():
        for event_object in self._ParseMRUListExKey(subkey, codepage=codepage):
          yield event_object


class MRUListExStringAndShellItemPlugin(
    interface.KeyPlugin, MRUListExPluginMixin):
  """Windows Registry plugin to parse a string and shell item MRUListEx."""

  NAME = 'winreg_mrulistex_string_and_shell_item'

  REG_TYPE = 'any'
  REG_KEYS = frozenset([
      u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\RecentDocs'])

  _STRING_AND_SHELL_ITEM_STRUCT = construct.Struct(
      'string_and_shell_item',
      construct.RepeatUntil(
          lambda obj, ctx: obj == '\x00\x00', construct.Field('string', 2)),
      construct.Anchor('shell_item'))

  def _CopyValueToString(self, value, codepage='cp1252', **unused_kwargs):
    """Returns a string that represents the MRU entry.

    Args:
      value: the Registry value (instance of winreg.WinRegValue) that contains
             the MRUListEx entry.
      codepage: Optional extended ASCII string codepage. The default is cp1252.

    Returns:
      An Unicode string representing the MRU entry.
    """
    if value.data_type != value.REG_BINARY:
      return u''

    value_struct = self._STRING_AND_SHELL_ITEM_STRUCT.parse(value.data)

    try:
      # The struct includes the end-of-string character that we need
      # to strip off.
      path = ''.join(value_struct.string).decode('utf16')[:-1]
    except UnicodeDecodeError as exception:
      logging.warning((
          u'Unable to decode string value in string and shell item '
          u'with error: {0:s}').format(exception))
      path = u''

    # Although we have one shell item here we need the list to parse it.
    shell_item_list = pyfwsi.item_list()

    shell_item_list_data = value.data[value_struct.shell_item:]
    if not shell_item_list_data:
      logging.debug(u'Missing shell item.')
      return u'Path: {0:s}'.format(path)

    shell_item_list.copy_from_byte_stream(
        shell_item_list_data, ascii_codepage=codepage)

    return u'Path: {0:s}, Shell item: [{1:s}]'.format(
        path, shell_item.ShellItemListCopyToPath(shell_item_list))

  def GetEntries(self, key=None, codepage='cp1252', **unused_kwargs):
    """Extract event objects from a Registry key containing a MRUListEx value.

    Args:
      key: the Registry key (instance of winreg.WinRegKey).
      codepage: Optional extended ASCII string codepage. The default is cp1252.

    Yields:
      Event objects (instances of EventObject).
    """
    for event_object in self._ParseMRUListExKey(key, codepage=codepage):
      yield event_object

    if key.name == u'RecentDocs':
      # For the RecentDocs MRUListEx we also need to parse its subkeys
      # since the Registry key path does not support wildcards yet.
      for subkey in key.GetSubkeys():
        for event_object in self._ParseMRUListExKey(subkey, codepage=codepage):
          yield event_object


class MRUListExStringAndShellItemListPlugin(
    interface.KeyPlugin, MRUListExPluginMixin):
  """Windows Registry plugin to parse a string and shell item list MRUListEx."""

  NAME = 'winreg_mrulistex_string_and_shell_item_list'

  REG_TYPE = 'any'
  REG_KEYS = frozenset([
      (u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\ComDlg32\\'
       u'LastVisitedPidlMRU')])

  _STRING_AND_SHELL_ITEM_LIST_STRUCT = construct.Struct(
      'string_and_shell_item',
      construct.RepeatUntil(
          lambda obj, ctx: obj == '\x00\x00', construct.Field('string', 2)),
      construct.Anchor('shell_item_list'))

  def _CopyValueToString(self, value, codepage='cp1252', **unused_kwargs):
    """Returns a string that represents the MRU entry.

    Args:
      value: the Registry value (instance of winreg.WinRegValue) that contains
             the MRUListEx entry.
      codepage: Optional extended ASCII string codepage. The default is cp1252.

    Returns:
      An Unicode string representing the MRU entry.
    """
    if value.data_type != value.REG_BINARY:
      return u''

    value_struct = self._STRING_AND_SHELL_ITEM_LIST_STRUCT.parse(value.data)

    try:
      # The struct includes the end-of-string character that we need
      # to strip off.
      path = ''.join(value_struct.string).decode('utf16')[:-1]
    except UnicodeDecodeError as exception:
      logging.warning((
          u'Unable to decode string value in string and shell item '
          u'with error: {0:s}').format(exception))
      path = u''

    shell_item_list = pyfwsi.item_list()

    shell_item_list_data = value.data[value_struct.shell_item_list:]
    if not shell_item_list_data:
      logging.debug(u'Missing shell item list.')
      return u'Path: {0:s}'.format(path)

    shell_item_list.copy_from_byte_stream(
        shell_item_list_data, ascii_codepage=codepage)

    return u'Path: {0:s}, Shell item list: [{1:s}]'.format(
        path, shell_item.ShellItemListCopyToPath(shell_item_list))

  def GetEntries(self, key=None, codepage='cp1252', **unused_kwargs):
    """Extract event objects from a Registry key containing a MRUListEx value.

    Args:
      key: the Registry key (instance of winreg.WinRegKey).
      codepage: Optional extended ASCII string codepage. The default is cp1252.

    Yields:
      Event objects (instances of EventObject).
    """
    for event_object in self._ParseMRUListExKey(key, codepage=codepage):
      yield event_object
