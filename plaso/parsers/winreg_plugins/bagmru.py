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

from plaso.lib import event
from plaso.parsers.shared import shell_items
from plaso.parsers.winreg_plugins import interface


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

  def _ParseMRUListExEntryValue(
      self, key, entry_index, entry_number, text_dict, value_strings,
      parent_value_string, codepage='cp1252', **unused_kwargs):
    """Parses the MRUListEx entry value.

    Args:
      key: the Registry key (instance of winreg.WinRegKey) that contains
           the MRUListEx value.
      entry_index: integer value representing the MRUListEx entry index.
      entry_number: integer value representing the entry number.
      text_dict: text dictionary object to append textual strings.
      value_string: value string dictionary object to append value strings.
      parent_value_string: string containing the parent value string.

    Yields:
      Event objects (instances of EventObject).
    """
    value = key.GetValue(u'{0:d}'.format(entry_number))
    value_string = u''
    if value is None:
      logging.debug(
          u'[{0:s}] Missing MRUListEx entry value: {1:d} in key: {2:s}.'.format(
              self.name, entry_number, key.path))

    elif not value.DataIsBinaryData():
      logging.debug((
          u'[{0:s}] Non-binary MRUListEx entry value: {1:d} in key: '
          u'{2:s}.').format(self.name, entry_number, key.path))

    elif value.data:
      shell_items_parser = shell_items.ShellItemsParser(key.path)
      for event_object in shell_items_parser.Parse(
          value.data, codepage=codepage):
        yield event_object

      value_string = shell_items_parser.CopyToPath()
      if parent_value_string:
        value_string = u', '.join([parent_value_string, value_string])

      value_strings[entry_number] = value_string

      value_string = u'Shell item list: [{0:s}]'.format(value_string)

    value_text = u'Index: {0:d} [MRU Value {1:d}]'.format(
        entry_index + 1, entry_number)

    text_dict[value_text] = value_string

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
      logging.warning(u'[{0:s}] Unable to parse the MRU key: {1:s}'.format(
          self.name, key.path))
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
    text_dict = {}
    value_strings = {}
    for index, entry_number in self._ParseMRUListExValue(key):
      # TODO: detect if list ends prematurely.
      # MRU lists are terminated with 0xffffffff (-1).
      if entry_number == 0xffffffff:
        break

      for event_object in self._ParseMRUListExEntryValue(
          key, index, entry_number, text_dict, value_strings,
          parent_value_string, codepage=codepage):
        yield event_object

    yield event.WinRegistryEvent(
        key.path, text_dict, timestamp=key.last_written_timestamp,
        source_append=': BagMRU')

    for index, entry_number in self._ParseMRUListExValue(key):
      # TODO: detect if list ends prematurely.
      # MRU lists are terminated with 0xffffffff (-1).
      if entry_number == 0xffffffff:
        break

      sub_key = key.GetSubkey(u'{0:d}'.format(entry_number))
      if not sub_key:
        logging.debug(
            u'[{0:s}] Missing BagMRU sub key: {1:d} in key: {2:s}.'.format(
        self.name, key.path, entry_number))
        continue

      value_string = value_strings.get(entry_number, u'')
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
