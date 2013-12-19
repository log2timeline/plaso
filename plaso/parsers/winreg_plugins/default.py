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
from plaso.lib import utils
from plaso.parsers.winreg_plugins import interface


class DefaultPlugin(interface.KeyPlugin):
  """Basic plugin to extract minimal information from registry keys."""

  NAME = 'winreg_default'

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

    if self._key.number_of_values == 0:
      text_dict[u'Value'] = u'No values stored in key.'

    else:
      for value in self._key.GetValues():
        if not value.name:
          value_name = '(default)'
        else:
          value_name = u'{0:s}'.format(value.name)

        if value.data is None:
          value_string = u'[{0:s}] Empty'.format(
              value.data_type_string)
        elif value.DataIsString():
          string_decode = utils.GetUnicodeString(value.data)
          value_string = u'[{0:s}] {1:s}'.format(
              value.data_type_string, string_decode)
        elif value.DataIsInteger():
          value_string = u'[{0:s}] {1:d}'.format(
              value.data_type_string, value.data)
        elif value.DataIsMultiString():
          if type(value.data) not in (list, tuple):
            value_string = u'[{0:s}]'.format(value.data_type_string)
            # TODO: Add a flag or some sort of an anomaly alert.
          else:
            value_string = u'[{0:s}] {1:s}'.format(
                value.data_type_string, u''.join(value.data))
        else:
          value_string = u'[{0:s}]'.format(value.data_type_string)

        text_dict[value_name] = value_string

    yield event.WinRegistryEvent(
        self._key.path, text_dict, timestamp=self._key.last_written_timestamp,
        offset=self._key.offset)
