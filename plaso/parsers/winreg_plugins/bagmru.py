#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""This file contains BagMRU Windows Registry plugins (shellbags)."""

import logging

import construct
import pyfwsi

from plaso.lib import event
from plaso.parsers.winreg_plugins import interface
from plaso.winnt import shell_item


class BagMRUPlugin(interface.ValuePlugin):
  """Class that defines a BagMRU Windows Registry plugin."""

  NAME = 'winreg_bagmru'

  # TODO: remove REG_TYPE and use HKEY_CURRENT_USER instead.
  REG_TYPE = 'any'

  REG_KEYS = frozenset([
      u'\\Software\\Microsoft\\Windows\\Shell\\BagMRU',
      u'\\Software\\Microsoft\\Windows\\ShellNoRoam\\BagMRU',
      (u'\\Software\\Classes\\Local Settings\\Software\\Microsoft\\Windows\\'
       u'Shell\\BagMRU'),
      (u'\\Software\\Classes\\Local Settings\\Software\\Microsoft\\Windows\\'
       u'ShellNoRoam\\BagMRU'),
      (u'\\Software\\Classes\\Wow6432Node\\Local Settings\\Software\\'
       u'Microsoft\\Windows\\Shell\\BagMRU'),
      (u'\\Software\\Classes\\Wow6432Node\\Local Settings\\Software\\'
       u'Microsoft\\Windows\\ShellNoRoam\\BagMRU')])

  URLS = [u'https://code.google.com/p/winreg-kb/wiki/MRUKeys']

  _MRULISTEX_STRUCT = construct.Range(1, 500, construct.ULInt32('entry_number'))

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

    # Although we have one shell item here we need the list to parse it.
    shell_item_list.copy_from_byte_stream(value.data, ascii_codepage=codepage)

    return shell_item.ShellItemListCopyToPath(shell_item_list)

  def _ParseMRUListExValue(self, key):
    """Parsed the MRUListEx value in a given Registry key.

    Args:
      key: the Registry key (instance of winreg.WinRegKey) that contains
           the MRUListEx value.

    Yields:
      A MRUListEx value generator, which returns the MRU index number
      and entry value.
    """
    mru_list_value = key.GetValue('MRUListEx')
    if not mru_list_value:
      return enumerate([])

    try:
      mru_list = self._MRULISTEX_STRUCT.parse(mru_list_value.data)
    except construct.FieldError:
      logging.warning(u'Unable to parse the MRU key: {0:s}'.format(
          key.path))
      return enumerate([])

    return enumerate(mru_list)

  def _ParseSubKey(self, key, parent_value_string, codepage='cp1252'):
    """Extract event objects from a MRUListEx Registry key.

    Args:
      key: the Registry key (instance of winreg.WinRegKey).
      parent_value_string: string containing the parent value string.
      codepage: Optional extended ASCII string codepage. The default is cp1252.

    Yields:
      Event objects (instances of EventObject).
    """
    event_timestamp = key.last_written_timestamp

    text_dict = {}
    value_strings = {}
    for index, entry in self._ParseMRUListExValue(key):
      # TODO: detect if list ends prematurely.
      # MRU lists are terminated with 0xffffffff (-1).
      if entry == 0xffffffff:
        break
      value_text = u'Index: {0:d} [MRU Value {1:d}]'.format(index + 1, entry)

      value = key.GetValue(u'{0:d}'.format(entry))
      if value is None:
        logging.debug(u'Missing BagMRU value: {0:d}.'.format(entry))
        value_string = u''
      else:
        value_string = self._CopyValueToString(value, codepage=codepage)

        if parent_value_string:
          value_string = u', '.join([parent_value_string, value_string])

      value_strings[entry] = value_string
      if value_string:
        value_string = u'Shell item list: [{0:s}]'.format(value_string)
      text_dict[value_text] = value_string

    yield event.WinRegistryEvent(
        key.path, text_dict, timestamp=event_timestamp,
        source_append=': BagMRU ')

    for index, entry in self._ParseMRUListExValue(key):
      # TODO: detect if list ends prematurely.
      # MRU lists are terminated with 0xffffffff (-1).
      if entry == 0xffffffff:
        break

      sub_key = key.GetSubkey(u'{0:d}'.format(entry))
      if not sub_key:
        logging.debug(u'Missing BagMRU sub key: {0:d}.'.format(entry))
        continue

      value_string = value_strings[entry]
      if parent_value_string:
        value_string = u', '.join([parent_value_string, value_string])

      for event_object in self._ParseSubKey(
          sub_key, value_string, codepage=codepage):
        yield event_object

  def GetEntries(self, key=None, codepage='cp1252', **unused_kwargs):
    """Extract event objects from a Registry key containing a MRUListEx value.

    Args:
      key: the Registry key (instance of winreg.WinRegKey).
      codepage: Optional extended ASCII string codepage. The default is cp1252.

    Yields:
      Event objects (instances of EventObject).
    """
    for event_object in self._ParseSubKey(key, u'', codepage=codepage):
      yield event_object
