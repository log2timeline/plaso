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
"""This file contains a MRUListEx Windows Registry plugin."""

import construct
import logging

from plaso.lib import event
from plaso.parsers.winreg_plugins import interface


class MRUListExPlugin(interface.ValuePlugin):
  """Class that defines a MRUListEx Windows Registry plugin."""

  NAME = 'winreg_mrulistex'

  REG_TYPE = 'any'
  REG_VALUES = frozenset(['MRUListEx', '0'])
  URLS = [u'http://forensicartifacts.com/2011/02/recentdocs/']

  LIST_STRUCT = construct.Range(1, 500, construct.ULInt32('entry_number'))

  def GetText(self, mru_entry):
    """Return a string from a MRU value."""
    value = self._key.GetValue(mru_entry)
    if not value:
      return u''

    # TODO: refactor this into a function of value?
    if value.DataIsString():
      return value.data

    if value.data_type == value.REG_BINARY:
      # TODO: refactor this into an extract text from binary function.
      return value.data.decode('utf_16_le', 'ignore').split('\x00')[0]

    return u''

  def GetEntries(self):
    """Extract EventObjects from a MRU list."""
    mru_list_data = self._key.GetValue('MRUListEx')

    # TODO: there is no need to use raw data refactor to use data.
    raw_data = mru_list_data.raw_data

    try:
      mru_list = self.LIST_STRUCT.parse(raw_data)
    except construct.FieldError:
      logging.warning(u'Unable to parse the MRU key: {0:s}'.format(
          self._key.path))
      return

    event_timestamp = self._key.last_written_timestamp

    text_dict = {}
    for nr, entry in enumerate(mru_list):
      # MRU lists are terminated with 0xFFFFFFFF.
      if entry == 0xFFFFFFFF:
        break
      value_text = u'Index: {} [MRU Value {:d}]'.format(nr + 1, entry)
      text_dict[value_text] = self.GetText(unicode(entry))

    yield event.WinRegistryEvent(
        self._key.path, text_dict, timestamp=event_timestamp,
        source_append=': MRUx List')

  def Process(self, key=None, **kwargs):
    """Determine if we can process this registry key or not."""
    if 'BagMRU' in key.path or 'Explorer\\StreamMRU' in key.path:
      return None

    return super(MRUListExPlugin, self).Process(key=key, **kwargs)
