#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""This file contains a default registry plugin in Plaso."""
from plaso.lib import event
from plaso.lib import win_registry_interface


class DefaultPlugin(win_registry_interface.KeyPlugin):
  """Basic plugin to extract minimal information from registry keys."""

  REG_TYPE = 'any'
  REG_KEY = '\\'
  # This is a special case, plugins normally never overwrite the priority.
  # However the default plugin should only run when all others plugins have
  # tried and failed.
  WEIGHT = 3

  def Process(self, key):
    """Process the key and return a generator to extract EventObjects."""
    self._key = key
    return self.GetEntries()

  def GetEntries(self):
    """Returns an event object based on a Registry key name and values."""
    text_dict = {}

    for value in self._key.GetValues():
      if not value.name:
        value_name = '(default)'
      else:
        value_name = u'%s' % value.name

      if value.DataIsString():
        text_dict[value_name] = value.data
      elif value.DataIsInteger():
        text_dict[value_name] = u'{0!d}'.format(value.data)
      elif value.data_type == value.REG_MULTI_SZ:
        text_dict[value_name] = u''.join(value.data)
      else:
        text_dict[value_name] = u'[DATA TYPE %s]' % value.GetTypeStr()

    if not text_dict:
      text_dict[u'Value'] = u'No values stored in key.'

    yield event.WinRegistryEvent(
        self._key.path, text_dict, timestamp=self._key.last_written_timestamp,
        offset=self._key.offset)
