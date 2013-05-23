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
"""This file contains a simple UserAssist plugin for Plaso."""
import construct
import logging

from plaso.lib import event
from plaso.lib import timelib
from plaso.lib import win_registry_interface


class XPUserAssistPlugin(win_registry_interface.KeyPlugin):
  """A registry plugin that parses XP UserAssist entries."""

  REG_KEY = ('\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer'
             '\\UserAssist\\{{75048700-EF1F-11D0-9888-006097DEACF9}}\\Count')
  REG_TYPE = 'NTUSER'
  URLS = [u'http://blog.didierstevens.com/programs/userassist/']

  USERASSIST_STRUCT = construct.Struct(
      'userassist_entry', construct.Padding(4), construct.ULInt32('count'),
      construct.ULInt64('timestamp'))

  def GetEntries(self):
    """Retrieves the values in the UserAssist Registry key."""
    for value in self._key.GetValues():
      data = value.GetRawData()
      name_raw = value.name

      if len(data) != 16:
        logging.debug('[UserAssist] Value entry is not of correct length.')
        continue

      try:
        name = name_raw.decode('rot-13')
      except UnicodeEncodeError as e:
        logging.warning(
            (u'Unable to decode UserAssist string in whole (piecewise '
             'decoding instead): {} - [{}]').format(name_raw, e))

        characters = []
        for char in name_raw:
          if ord(char) < 128:
            try:
              characters.append(char.decode('rot-13'))
            except UnicodeEncodeError:
              characters.append(char)
          else:
            characters.append(char)

        name = u''.join(characters)

      data_parsed = self.USERASSIST_STRUCT.parse(data)
      filetime = data_parsed.get('timestamp', 0)
      count = data_parsed.get('count', 0)

      if count > 5:
        count -= 5

      text_dict = {}
      text_dict[name] = u'[Count: {0}]'.format(count)
      yield event.WinRegistryEvent(
          u'', text_dict, timelib.Timestamp.FromFiletime(filetime))
